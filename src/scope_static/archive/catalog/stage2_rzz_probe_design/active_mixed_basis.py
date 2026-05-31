from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import torch

from scope_static.identifiability import deterministic_kmeans, evaluate_partition
from scope_static.dem.local_mechanism import split_merge_audit
from scope_static.dem.metrics import adjusted_rand_index, normalized_mutual_info
from scope_static.numerics import NUMERICAL_ZERO

from scope_static.archive.catalog.stage2_learner_limit.targeted_v3 import RZZ_FAMILY, READOUT_LABELS, build_targeted_v3_features, typed_cluster_labels
from scope_static.backend.probe_catalog import EDGE_ORIENTATION_RULE, MIXED_BASIS_ACTIVE_PROBES, build_probe_basis_manifest, probe_basis_by_qubit


MOMENT_NAMES = ("ZZ", "XX", "YY", "XZ", "ZX", "YZ", "ZY", "XY", "YX")
SIGNED_CONTRASTS = ("XZ_minus_ZX", "YZ_minus_ZY", "XY_minus_YX")


@dataclass(frozen=True)
class ActiveMixedBasisBundle:
    feature_spaces: dict[str, np.ndarray]
    feature_names: dict[str, list[str]]
    visible_types: list[str]
    type_budgets: dict[str, int]
    feature_provenance_manifest: dict[str, object]
    active_probe_manifest: dict[str, object]
    visibility_matrix: dict[str, object]
    moment_uncertainty_audit: dict[str, object]


def build_active_mixed_basis_features(
    records: list[dict[str, object]],
    observations: np.ndarray,
    probe_names: Iterable[str],
    *,
    num_clusters: int,
) -> ActiveMixedBasisBundle:
    """Build S2D.7 learner-visible active mixed-basis edge features.

    Inputs are intentionally limited to measured shot bits, probe-basis metadata
    derivable from the visible circuit schedule, and visible record fields such
    as instruction/qubits/probe indices. No exact channels, PTMs, or oracle
    labels are read by this feature builder.
    """

    obs = _validate_observations(observations)
    names = [str(name) for name in probe_names]
    num_qubits = int(obs.shape[2])
    targeted = build_targeted_v3_features(records, obs, names, num_clusters=int(num_clusters))
    from scope_static.mechanism_observability.local_inverse import build_visible_location_representations

    base = build_visible_location_representations(records, obs, names)
    active_v3c = targeted.feature_spaces["physical_local_inverse_probability_v3_typed"]
    structural = base["structural_only_features"]

    probe_manifest = build_probe_basis_manifest(names, num_qubits=num_qubits)
    scrambled_manifest = _scrambled_probe_manifest(probe_manifest)
    moments, moment_names, uncertainty = _edge_moment_matrix(records, obs, names, probe_manifest)
    signed, signed_names = _signed_contrast_matrix(records, moments, moment_names, num_qubits)
    scrambled_moments, scrambled_names, scrambled_uncertainty = _edge_moment_matrix(records, obs, names, scrambled_manifest)
    scrambled_signed, scrambled_signed_names = _signed_contrast_matrix(records, scrambled_moments, scrambled_names, num_qubits)
    marginals, marginal_names = _basis_marginal_matrix(records, obs, names, probe_manifest)

    feature_spaces = {
        "active_probe_only_v3c": active_v3c,
        "active_basis_marginals_only": _finite(np.concatenate([marginals, structural], axis=1)),
        "active_mixed_basis_moments": _finite(np.concatenate([active_v3c, moments], axis=1)),
        "active_mixed_basis_moments_plus_signed_contrasts": _finite(np.concatenate([active_v3c, moments, signed], axis=1)),
        "active_mixed_basis_scrambled": _finite(np.concatenate([active_v3c, scrambled_moments, scrambled_signed], axis=1)),
    }
    feature_names = {
        "active_probe_only_v3c": [f"v3c_{idx}" for idx in range(active_v3c.shape[1])],
        "active_basis_marginals_only": [*marginal_names, *[f"structural_{idx}" for idx in range(structural.shape[1])]],
        "active_mixed_basis_moments": [*[f"v3c_{idx}" for idx in range(active_v3c.shape[1])], *moment_names],
        "active_mixed_basis_moments_plus_signed_contrasts": [
            *[f"v3c_{idx}" for idx in range(active_v3c.shape[1])],
            *moment_names,
            *signed_names,
        ],
        "active_mixed_basis_scrambled": [
            *[f"v3c_{idx}" for idx in range(active_v3c.shape[1])],
            *[f"scrambled_{name}" for name in scrambled_names],
            *[f"scrambled_{name}" for name in scrambled_signed_names],
        ],
    }
    return ActiveMixedBasisBundle(
        feature_spaces=feature_spaces,
        feature_names=feature_names,
        visible_types=targeted.visible_types,
        type_budgets=targeted.type_budgets,
        feature_provenance_manifest=feature_provenance_manifest(feature_names),
        active_probe_manifest=probe_manifest,
        visibility_matrix=visibility_matrix(probe_manifest),
        moment_uncertainty_audit={
            "schema": "scope_static_s2d7_moment_uncertainty_audit_v1",
            "real_basis": uncertainty,
            "scrambled_basis": scrambled_uncertainty,
        },
    )


def evaluate_active_mixed_basis_methods(
    records: list[dict[str, object]],
    observations: np.ndarray,
    probe_names: Iterable[str],
    hidden_labels: torch.Tensor,
    label_names: list[str],
    *,
    comparison_labels: dict[str, list[int]] | None = None,
) -> dict[str, object]:
    bundle = build_active_mixed_basis_features(records, observations, probe_names, num_clusters=len(label_names))
    comparison_labels = comparison_labels or {}
    method_specs = [
        ("active_probe_only_v3c", "active_probe_only_v3c", comparison_labels.get("active_probe_only_v3c")),
        ("active_basis_marginals_only", "active_basis_marginals_only", None),
        ("active_mixed_basis_moments", "active_mixed_basis_moments", None),
        ("active_mixed_basis_moments_plus_signed_contrasts", "active_mixed_basis_moments_plus_signed_contrasts", None),
        ("active_mixed_basis_scrambled", "active_mixed_basis_scrambled", None),
    ]
    rows = []
    labels_by_method: dict[str, list[int]] = {}
    for method, feature_key, precomputed in method_specs:
        features = bundle.feature_spaces[feature_key]
        labels = (
            [int(value) for value in precomputed]
            if precomputed is not None
            else typed_cluster_labels(features, bundle.visible_types, bundle.type_budgets)
        )
        labels_by_method[method] = labels
        rows.append(_method_record(method, feature_key, features, labels, hidden_labels, len(label_names)))

    for method, labels in comparison_labels.items():
        if method in labels_by_method:
            continue
        labels_int = [int(value) for value in labels]
        labels_by_method[method] = labels_int
        rows.append(
            {
                "method": method,
                "feature_space": method,
                "feature_role": "oracle_only_upper_bound" if method == "oracle_fingerprint_upper_bound" else "comparison",
                "uses_oracle_channel_parameters": method == "oracle_fingerprint_upper_bound",
                "uses_oracle_labels": False,
                **_partition_record(labels_int, hidden_labels, len(label_names)),
            }
        )

    return {
        "feature_provenance_manifest": bundle.feature_provenance_manifest,
        "active_probe_manifest": bundle.active_probe_manifest,
        "visibility_matrix": bundle.visibility_matrix,
        "moment_uncertainty_audit": bundle.moment_uncertainty_audit,
        "visible_type_counts": _counts(bundle.visible_types),
        "type_budgets": bundle.type_budgets,
        "methods": rows,
        "labels_by_method": labels_by_method,
        "rzz_family_metrics": rzz_family_metrics(labels_by_method, hidden_labels, label_names),
        "rzz_family_distance_audit": rzz_family_distance_audit(bundle.feature_spaces, hidden_labels, label_names),
        "scrambled_basis_control": _scrambled_basis_control(rows),
        "key_comparison": _key_comparison(rows),
    }


def feature_provenance_manifest(feature_names: dict[str, list[str]]) -> dict[str, object]:
    feature_blocks = {}
    for block, names in feature_names.items():
        feature_blocks[block] = [
            {
                "feature_name": name,
                "source": "learner_counts" if block != "active_probe_only_v3c" else "learner_counts_and_visible_schedule",
                "uses_oracle_label": False,
                "uses_exact_teacher_channel": False,
                "uses_exact_ptm": False,
                "visible_inputs": ["shot_bits", "probe_basis", "edge_index", "circuit_schedule"],
            }
            for name in names
        ]
    return {
        "schema": "scope_static_s2d7_feature_provenance_manifest_v1",
        "edge_orientation_rule": EDGE_ORIENTATION_RULE,
        "learner_visible_rule": (
            "features are learner-visible only when computable from circuit schedule, probe settings, "
            "and measured bit strings without hidden mechanism labels or exact teacher channels"
        ),
        "forbidden_in_phys3": [
            "exact_ptm_entries",
            "exact_rzz_type_1_2_3_4_features",
            "oracle_fingerprints",
            "teacher_channels",
            "oracle_mechanism_labels",
        ],
        "feature_blocks": feature_blocks,
        "audit_only_blocks": {
            "exact_ptm": {"oracle_only": True},
            "rzz_type_features": {"oracle_only": True},
            "oracle_fingerprint_upper_bound": {"oracle_only": True},
        },
    }


def visibility_matrix(probe_manifest: dict[str, object]) -> dict[str, object]:
    records = list(probe_manifest.get("probe_records", []))
    by_pair = {name: 0 for name in MOMENT_NAMES}
    base_by_pair = {name: 0 for name in MOMENT_NAMES}
    active_by_pair = {name: 0 for name in MOMENT_NAMES}
    edge_examples: dict[str, list[dict[str, object]]] = {name: [] for name in MOMENT_NAMES}
    for record in records:
        base_name = str(record.get("base_probe_name", ""))
        is_active = base_name in set(MIXED_BASIS_ACTIVE_PROBES)
        is_base = base_name in {"z_basis", "x_measure", "y_measure"}
        for edge in record.get("measurable_edge_pairs", []):
            if not isinstance(edge, dict):
                continue
            pair = str(edge.get("basis_pair", ""))
            if pair not in by_pair:
                continue
            by_pair[pair] += 1
            if is_base:
                base_by_pair[pair] += 1
            if is_active:
                active_by_pair[pair] += 1
            if len(edge_examples[pair]) < 3:
                edge_examples[pair].append(
                    {
                        "probe_name": record.get("probe_name"),
                        "edge": edge.get("edge"),
                        "basis_pair": pair,
                    }
                )
    return {
        "schema": "scope_static_s2d7_visibility_matrix_v1",
        "edge_orientation_rule": probe_manifest.get("edge_orientation_rule", EDGE_ORIENTATION_RULE),
        "moment_visibility_counts": by_pair,
        "base_probe_visibility_counts": base_by_pair,
        "active_probe_visibility_counts": active_by_pair,
        "base_probes_cannot_expose_mixed_basis": all(base_by_pair[name] == 0 for name in ("XZ", "ZX", "YZ", "ZY", "XY", "YX")),
        "active_probes_expose_mixed_basis": all(active_by_pair[name] > 0 for name in ("XZ", "ZX", "YZ", "ZY", "XY", "YX")),
        "examples": edge_examples,
    }


def rzz_family_metrics(
    labels_by_method: dict[str, list[int]],
    hidden_labels: torch.Tensor,
    label_names: list[str],
) -> dict[str, object]:
    hidden = torch.as_tensor(hidden_labels, dtype=torch.long)
    family_ids = [idx for idx, name in enumerate(label_names) if name in RZZ_FAMILY]
    family_mask = torch.zeros_like(hidden, dtype=torch.bool)
    for idx in family_ids:
        family_mask |= hidden == int(idx)
    readout_labels = [name for name in READOUT_LABELS if name in label_names]
    out = {"family": [label_names[idx] for idx in family_ids], "methods": {}}
    for method, labels in labels_by_method.items():
        pred = torch.as_tensor(labels, dtype=torch.long)
        pred_family = pred[family_mask]
        hidden_family = hidden[family_mask]
        method_metrics = {
            "RZZ_family_ARI": float(adjusted_rand_index(pred_family, hidden_family)) if pred_family.numel() else 0.0,
            "RZZ_family_NMI": float(normalized_mutual_info(pred_family, hidden_family)) if pred_family.numel() else 0.0,
            "M8_M9_merge_count": _pair_merge_count(pred, hidden, label_names, "M8", "M9"),
            "M8_M10_merge_count": _pair_merge_count(pred, hidden, label_names, "M8", "M10"),
            "M8_M12_merge_count": _pair_merge_count(pred, hidden, label_names, "M8", "M12"),
            "M8_split_count": _label_split_count(pred, hidden, label_names, "M8"),
            "readout_split_count": sum(_label_split_count(pred, hidden, label_names, label) for label in readout_labels),
            "M5_split_count": sum(_label_split_count(pred, hidden, label_names, label) for label in readout_labels),
        }
        out["methods"][method] = method_metrics
    return out


def rzz_family_distance_audit(feature_spaces: dict[str, np.ndarray], hidden_labels: torch.Tensor, label_names: list[str]) -> dict[str, object]:
    labels = torch.as_tensor(hidden_labels, dtype=torch.long).numpy()
    family_ids = [idx for idx, name in enumerate(label_names) if name in RZZ_FAMILY]
    out = {"schema": "scope_static_s2d7_rzz_family_distance_audit_v1", "methods": {}}
    for method, features in feature_spaces.items():
        x = _standardize(features)
        centers = {}
        radii = {}
        for idx in family_ids:
            rows = x[labels == idx]
            if rows.size == 0:
                continue
            center = rows.mean(axis=0)
            centers[idx] = center
            radii[idx] = float(np.median(np.linalg.norm(rows - center, axis=1))) if rows.shape[0] > 1 else 0.0
        pairs = {}
        for left_pos, left in enumerate(family_ids):
            for right in family_ids[left_pos + 1 :]:
                if left not in centers or right not in centers:
                    continue
                distance = float(np.linalg.norm(centers[left] - centers[right]))
                pairs[f"{label_names[left]}__{label_names[right]}"] = {
                    "center_distance": distance,
                    "median_radius_left": radii[left],
                    "median_radius_right": radii[right],
                    "margin": float(distance - radii[left] - radii[right]),
                }
        out["methods"][method] = pairs
    return out


def _edge_moment_matrix(
    records: list[dict[str, object]],
    observations: np.ndarray,
    probe_names: list[str],
    probe_manifest: dict[str, object],
) -> tuple[np.ndarray, list[str], dict[str, object]]:
    obs = _validate_observations(observations)
    metadata = _basis_metadata_by_index(probe_manifest)
    names = _moment_feature_names()
    rows = []
    audit_records = []
    for location_idx, record in enumerate(records):
        row = []
        local_audit = {
            "location_id": int(record.get("location_id", location_idx)),
            "instruction": str(record.get("instruction", "")),
            "qubits": _record_qubits(record),
            "moments": {},
        }
        for moment in MOMENT_NAMES:
            stats = _estimate_edge_moment(record, obs, probe_names, metadata, moment)
            row.extend([stats["mean"], stats["connected"], stats["normalized_correlation"], stats["standard_error"], stats["z_score"]])
            local_audit["moments"][moment] = stats
        rows.append(row)
        if str(record.get("instruction")) == "rzz":
            audit_records.append(local_audit)
    return _finite(np.asarray(rows, dtype=np.float64)), names, _moment_uncertainty_summary(audit_records)


def _signed_contrast_matrix(
    records: list[dict[str, object]],
    moment_matrix: np.ndarray,
    moment_names: list[str],
    num_qubits: int,
) -> tuple[np.ndarray, list[str]]:
    name_index = {name: idx for idx, name in enumerate(moment_names)}
    rows = []
    for record, moment_row in zip(records, moment_matrix):
        values = {}
        for moment in MOMENT_NAMES:
            values[moment] = {
                "mean": float(moment_row[name_index[f"{moment}_mean"]]),
                "connected": float(moment_row[name_index[f"{moment}_connected"]]),
                "corr": float(moment_row[name_index[f"{moment}_normalized_correlation"]]),
            }
        signed = []
        for left, right in (("XZ", "ZX"), ("YZ", "ZY"), ("XY", "YX")):
            signed.extend(
                [
                    values[left]["mean"] - values[right]["mean"],
                    values[left]["connected"] - values[right]["connected"],
                    values[left]["corr"] - values[right]["corr"],
                ]
            )
        raw_values = np.asarray([values[name]["mean"] for name in MOMENT_NAMES], dtype=np.float64)
        connected_values = np.asarray([values[name]["connected"] for name in MOMENT_NAMES], dtype=np.float64)
        mixed_raw = np.asarray([values[name]["mean"] for name in ("XZ", "ZX", "YZ", "ZY", "XY", "YX")], dtype=np.float64)
        commuting_raw = np.asarray([values[name]["mean"] for name in ("XY", "YX")], dtype=np.float64)
        qubits = _record_qubits(record)
        left = min(qubits) if qubits else 0
        right = max(qubits) if qubits else left
        max_edge = max(1, int(num_qubits) - 2)
        signed.extend(
            [
                float(np.linalg.norm(mixed_raw)),
                float(np.linalg.norm(commuting_raw)),
                float(np.std(raw_values)),
                float(np.var(connected_values)),
                float(left / max_edge),
                float((left + right) / max(1.0, 2.0 * (int(num_qubits) - 1))),
                float(1.0 if left <= 0 or right >= int(num_qubits) - 1 else 0.0),
            ]
        )
        rows.append(signed)
    names = []
    for contrast in SIGNED_CONTRASTS:
        names.extend([f"{contrast}_mean", f"{contrast}_connected", f"{contrast}_normalized_correlation"])
    names.extend(
        [
            "mixed_basis_norm",
            "commuting_xy_yx_norm",
            "moment_anisotropy",
            "connected_response_variance",
            "edge_position_left",
            "edge_position_center",
            "edge_boundary_flag",
        ]
    )
    return _finite(np.asarray(rows, dtype=np.float64)), names


def _basis_marginal_matrix(
    records: list[dict[str, object]],
    observations: np.ndarray,
    probe_names: list[str],
    probe_manifest: dict[str, object],
) -> tuple[np.ndarray, list[str]]:
    obs = _validate_observations(observations)
    metadata = _basis_metadata_by_index(probe_manifest)
    names = []
    for axis in ("X", "Y", "Z"):
        names.extend([f"{axis}_left_mean", f"{axis}_right_mean", f"{axis}_left_se", f"{axis}_right_se"])
    rows = []
    for record in records:
        qubits = _record_qubits(record)
        left = min(qubits) if qubits else 0
        right = max(qubits) if qubits else left
        probe_indices = _record_probe_indices(record, len(probe_names))
        row = []
        for axis in ("X", "Y", "Z"):
            left_values = []
            right_values = []
            left_ses = []
            right_ses = []
            for probe_idx in probe_indices:
                basis = metadata.get(int(probe_idx), {}).get("basis_by_qubit", probe_basis_by_qubit(probe_names[probe_idx], num_qubits=obs.shape[2]))
                if basis[left] == axis:
                    samples = _pm_one(obs[int(probe_idx), :, left])
                    left_values.append(float(np.mean(samples)))
                    left_ses.append(_standard_error(float(np.mean(samples)), samples.size))
                if basis[right] == axis:
                    samples = _pm_one(obs[int(probe_idx), :, right])
                    right_values.append(float(np.mean(samples)))
                    right_ses.append(_standard_error(float(np.mean(samples)), samples.size))
            row.extend([_mean_or_zero(left_values), _mean_or_zero(right_values), _mean_or_zero(left_ses), _mean_or_zero(right_ses)])
        rows.append(row)
    return _finite(np.asarray(rows, dtype=np.float64)), names


def _estimate_edge_moment(
    record: dict[str, object],
    observations: np.ndarray,
    probe_names: list[str],
    metadata: dict[int, dict[str, object]],
    moment: str,
) -> dict[str, object]:
    qubits = _record_qubits(record)
    if len(qubits) < 2:
        return _empty_moment_stats(moment)
    left = min(qubits)
    right = max(qubits)
    left_axis, right_axis = moment[0], moment[1]
    estimates = []
    for probe_idx in _record_probe_indices(record, len(probe_names)):
        basis = metadata.get(int(probe_idx), {}).get("basis_by_qubit", probe_basis_by_qubit(probe_names[probe_idx], num_qubits=observations.shape[2]))
        if basis[left] != left_axis or basis[right] != right_axis:
            continue
        left_samples = _pm_one(observations[int(probe_idx), :, left])
        right_samples = _pm_one(observations[int(probe_idx), :, right])
        product = left_samples * right_samples
        mean_left = float(np.mean(left_samples))
        mean_right = float(np.mean(right_samples))
        mean = float(np.mean(product))
        connected = float(mean - mean_left * mean_right)
        denom = float(np.sqrt(_nonnegative_variance(1.0 - mean_left * mean_left) * _nonnegative_variance(1.0 - mean_right * mean_right)))
        normalized = float(connected / denom) if denom > NUMERICAL_ZERO else 0.0
        se = _standard_error(mean, int(product.size))
        estimates.append(
            {
                "mean": mean,
                "mean_left": mean_left,
                "mean_right": mean_right,
                "connected": connected,
                "normalized_correlation": normalized,
                "standard_error": se,
                "z_score": float(mean / se) if se > NUMERICAL_ZERO else 0.0,
                "num_shots": int(product.size),
                "probe_index": int(probe_idx),
                "probe_name": probe_names[int(probe_idx)],
            }
        )
    if not estimates:
        return _empty_moment_stats(moment)
    return {
        "moment": moment,
        "available": True,
        "mean": float(np.mean([item["mean"] for item in estimates])),
        "mean_left": float(np.mean([item["mean_left"] for item in estimates])),
        "mean_right": float(np.mean([item["mean_right"] for item in estimates])),
        "connected": float(np.mean([item["connected"] for item in estimates])),
        "normalized_correlation": float(np.mean([item["normalized_correlation"] for item in estimates])),
        "standard_error": float(np.sqrt(np.sum([float(item["standard_error"]) ** 2 for item in estimates])) / len(estimates)),
        "z_score": float(np.mean([item["z_score"] for item in estimates])),
        "num_shots": int(sum(int(item["num_shots"]) for item in estimates)),
        "probes": [{"probe_index": item["probe_index"], "probe_name": item["probe_name"]} for item in estimates],
    }


def _moment_uncertainty_summary(records: list[dict[str, object]]) -> dict[str, object]:
    by_moment = {}
    for moment in MOMENT_NAMES:
        values = []
        ses = []
        shots = []
        for record in records:
            item = record["moments"][moment]
            if not bool(item.get("available", False)):
                continue
            values.append(float(item["mean"]))
            ses.append(float(item["standard_error"]))
            shots.append(int(item["num_shots"]))
        by_moment[moment] = {
            "num_available_locations": len(values),
            "mean": float(np.mean(values)) if values else 0.0,
            "mean_standard_error": float(np.mean(ses)) if ses else 0.0,
            "min_num_shots": int(min(shots)) if shots else 0,
            "max_num_shots": int(max(shots)) if shots else 0,
        }
    return {
        "edge_orientation_rule": EDGE_ORIENTATION_RULE,
        "moment_summary": by_moment,
        "rzz_location_records": records,
    }


def _method_record(
    method: str,
    feature_key: str,
    features: np.ndarray,
    labels: list[int],
    hidden_labels: torch.Tensor,
    num_clusters: int,
) -> dict[str, object]:
    return {
        "method": method,
        "feature_space": feature_key,
        "feature_role": "learner_visible",
        "uses_oracle_channel_parameters": False,
        "uses_oracle_labels": False,
        "uses_exact_ptm": False,
        "feature_shape": [int(features.shape[0]), int(features.shape[1])],
        **_partition_record(labels, hidden_labels, num_clusters),
    }


def _partition_record(labels: list[int], hidden_labels: torch.Tensor, num_clusters: int) -> dict[str, object]:
    labels_t = torch.as_tensor(labels, dtype=torch.long)
    partition = evaluate_partition(labels_t, hidden_labels, num_clusters=int(num_clusters))
    split_merge = split_merge_audit(labels_t, hidden_labels)
    return {
        "ari": float(partition["ari"]),
        "nmi": float(partition["nmi"]),
        "active_clusters": int(partition["active_clusters"]),
        "cluster_masses": partition["cluster_masses"],
        "labels": [int(value) for value in labels_t.tolist()],
        **split_merge,
    }


def _scrambled_basis_control(rows: list[dict[str, object]]) -> dict[str, object]:
    by_method = {str(row["method"]): row for row in rows}
    real = by_method.get("active_mixed_basis_moments_plus_signed_contrasts", {})
    scrambled = by_method.get("active_mixed_basis_scrambled", {})
    return {
        "real_method": "active_mixed_basis_moments_plus_signed_contrasts",
        "scrambled_method": "active_mixed_basis_scrambled",
        "real_ari": real.get("ari"),
        "real_nmi": real.get("nmi"),
        "scrambled_ari": scrambled.get("ari"),
        "scrambled_nmi": scrambled.get("nmi"),
        "real_beats_scrambled": bool(
            float(real.get("ari", 0.0)) > float(scrambled.get("ari", 0.0))
            and float(real.get("nmi", 0.0)) > float(scrambled.get("nmi", 0.0))
        ),
    }


def _key_comparison(rows: list[dict[str, object]]) -> dict[str, object]:
    by_method = {str(row["method"]): row for row in rows}
    active = by_method.get("active_mixed_basis_moments_plus_signed_contrasts", {})
    probe_only = by_method.get("active_probe_only_v3c", {})
    marginals = by_method.get("active_basis_marginals_only", {})
    scrambled = by_method.get("active_mixed_basis_scrambled", {})
    direct = by_method.get("direct_Salpha", {})
    return {
        "primary": "active_mixed_basis_moments_plus_signed_contrasts",
        "active_ari": active.get("ari"),
        "active_nmi": active.get("nmi"),
        "delta_ari_vs_active_probe_only": float(active.get("ari", 0.0)) - float(probe_only.get("ari", 0.0)),
        "delta_nmi_vs_active_probe_only": float(active.get("nmi", 0.0)) - float(probe_only.get("nmi", 0.0)),
        "beats_marginals_only": bool(
            float(active.get("ari", 0.0)) > float(marginals.get("ari", 0.0))
            and float(active.get("nmi", 0.0)) > float(marginals.get("nmi", 0.0))
        ),
        "beats_scrambled": bool(
            float(active.get("ari", 0.0)) > float(scrambled.get("ari", 0.0))
            and float(active.get("nmi", 0.0)) > float(scrambled.get("nmi", 0.0))
        ),
        "beats_direct_Salpha": bool(
            float(active.get("ari", 0.0)) > float(direct.get("ari", 0.0))
            and float(active.get("nmi", 0.0)) > float(direct.get("nmi", 0.0))
        ),
    }


def _scrambled_probe_manifest(probe_manifest: dict[str, object]) -> dict[str, object]:
    records = [dict(record) for record in probe_manifest.get("probe_records", [])]
    active_indices = [idx for idx, record in enumerate(records) if str(record.get("base_probe_name")) in set(MIXED_BASIS_ACTIVE_PROBES)]
    if active_indices:
        shifted = active_indices[1:] + active_indices[:1]
        replacement = [list(records[idx].get("basis_by_qubit", [])) for idx in shifted]
        for idx, basis in zip(active_indices, replacement):
            records[idx]["basis_by_qubit"] = basis
            records[idx]["scrambled_basis_control"] = True
            records[idx]["measurable_edge_pairs"] = [
                {"edge": [int(left), int(left + 1)], "basis_pair": f"{basis[left]}{basis[left + 1]}"}
                for left in range(max(0, len(basis) - 1))
            ]
    return {**probe_manifest, "schema": "scope_static_s2d7_scrambled_active_probe_manifest_v1", "probe_records": records}


def _basis_metadata_by_index(probe_manifest: dict[str, object]) -> dict[int, dict[str, object]]:
    out = {}
    for record in probe_manifest.get("probe_records", []):
        if isinstance(record, dict):
            out[int(record["probe_index"])] = record
    return out


def _moment_feature_names() -> list[str]:
    names = []
    for moment in MOMENT_NAMES:
        names.extend(
            [
                f"{moment}_mean",
                f"{moment}_connected",
                f"{moment}_normalized_correlation",
                f"{moment}_standard_error",
                f"{moment}_z_score",
            ]
        )
    return names


def _empty_moment_stats(moment: str) -> dict[str, object]:
    return {
        "moment": moment,
        "available": False,
        "mean": 0.0,
        "mean_left": 0.0,
        "mean_right": 0.0,
        "connected": 0.0,
        "normalized_correlation": 0.0,
        "standard_error": 0.0,
        "z_score": 0.0,
        "num_shots": 0,
        "probes": [],
    }


def _pair_merge_count(pred: torch.Tensor, hidden: torch.Tensor, label_names: list[str], left_name: str, right_name: str) -> int:
    if left_name not in label_names or right_name not in label_names:
        return 0
    left = label_names.index(left_name)
    right = label_names.index(right_name)
    count = 0
    for cluster in sorted({int(value) for value in pred.tolist()}):
        idx = pred == cluster
        if bool(torch.any(hidden[idx] == left)) and bool(torch.any(hidden[idx] == right)):
            count += 1
    return int(count)


def _label_split_count(pred: torch.Tensor, hidden: torch.Tensor, label_names: list[str], label_name: str) -> int:
    if label_name not in label_names:
        return 0
    label_idx = label_names.index(label_name)
    clusters = sorted({int(value) for value in pred[hidden == label_idx].tolist()})
    return int(max(0, len(clusters) - 1))


def _record_qubits(record: dict[str, object]) -> list[int]:
    raw = record.get("qubits", [])
    return [int(value) for value in raw] if isinstance(raw, list) and raw else [0]


def _record_probe_indices(record: dict[str, object], num_probes: int) -> list[int]:
    raw = record.get("probe_indices", [])
    if isinstance(raw, list) and raw:
        return [int(value) for value in raw]
    return list(range(int(num_probes)))


def _pm_one(bits: np.ndarray) -> np.ndarray:
    return 1.0 - 2.0 * np.asarray(bits, dtype=np.float64)


def _standard_error(mean: float, num_shots: int) -> float:
    if int(num_shots) <= 0:
        return 0.0
    variance = _nonnegative_variance(1.0 - float(mean) * float(mean))
    if variance <= NUMERICAL_ZERO:
        return 0.0
    return float(np.sqrt(variance / int(num_shots)))


def _nonnegative_variance(value: float) -> float:
    return 0.0 if float(value) <= NUMERICAL_ZERO else float(value)


def _mean_or_zero(values: list[float]) -> float:
    return float(np.mean(values)) if values else 0.0


def _counts(values: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[str(value)] = counts.get(str(value), 0) + 1
    return counts


def _validate_observations(observations: np.ndarray) -> np.ndarray:
    obs = np.asarray(observations)
    if obs.ndim != 3:
        raise ValueError("observations must have shape [num_probes, shots, num_qubits]")
    return obs


def _standardize(features: np.ndarray) -> np.ndarray:
    x = _finite(np.asarray(features, dtype=np.float64))
    scale = x.std(axis=0)
    scale[scale < NUMERICAL_ZERO] = 1.0
    return (x - x.mean(axis=0)) / scale


def _finite(values: np.ndarray) -> np.ndarray:
    return np.nan_to_num(np.asarray(values, dtype=np.float64), nan=NUMERICAL_ZERO, posinf=NUMERICAL_ZERO, neginf=-NUMERICAL_ZERO)
