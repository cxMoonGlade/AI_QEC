from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import torch

from scope_static.identifiability import evaluate_partition
from scope_static.local_mechanism import split_merge_audit
from scope_static.metrics import normalized_mutual_info
from scope_static.numerics import NUMERICAL_ZERO

from .active_mixed_basis import rzz_family_distance_audit, rzz_family_metrics
from .mechanism_catalog import RZZ_FAMILY_IDS
from .targeted_v3 import build_targeted_v3_features, typed_cluster_labels
from .teacher import (
    EDGE_ORIENTATION_RULE,
    RZZ_MINIMAL_INTERVENTION_PROBES,
    build_probe_basis_manifest,
    probe_rzz_intervention_edge_parity,
    probe_rzz_intervention_family,
    probe_rzz_intervention_role,
)


STAT_NAMES = ("mean", "connected", "normalized_correlation", "standard_error", "z_score")
BASIS_ROLES = ("x", "y", "xz", "yz")
TWIRL_ROLES = ("twirl_x_left", "twirl_y_left", "twirl_xy")
SIGN_ROLES = ("sign_flip_left", "sign_flip_right")


@dataclass(frozen=True)
class RZZMinimalInterventionBundle:
    feature_spaces: dict[str, np.ndarray]
    feature_names: dict[str, list[str]]
    visible_types: list[str]
    type_budgets: dict[str, int]
    intervention_schema: dict[str, object]
    feature_provenance_manifest: dict[str, object]
    twirl_response_metrics: dict[str, object]
    basis_response_metrics: dict[str, object]
    echo_response_metrics: dict[str, object]


def build_rzz_minimal_intervention_features(
    records: list[dict[str, object]],
    observations: np.ndarray,
    probe_names: Iterable[str],
    *,
    num_clusters: int,
) -> RZZMinimalInterventionBundle:
    obs = _validate_observations(observations)
    names = [str(name) for name in probe_names]
    num_qubits = int(obs.shape[2])
    targeted = build_targeted_v3_features(records, obs, names, num_clusters=int(num_clusters))
    probe_manifest = build_probe_basis_manifest(names, num_qubits=num_qubits)
    scrambled_manifest = _scrambled_intervention_manifest(probe_manifest)

    twirl, twirl_names, twirl_audit = _family_feature_matrix(records, obs, names, probe_manifest, family="pauli_frame_twirl")
    basis, basis_names, basis_audit = _family_feature_matrix(records, obs, names, probe_manifest, family="basis_rotation")
    echo, echo_names, echo_audit = _family_feature_matrix(records, obs, names, probe_manifest, family="sign_flip_echo")
    scrambled_twirl, scrambled_twirl_names, scrambled_twirl_audit = _family_feature_matrix(
        records, obs, names, scrambled_manifest, family="pauli_frame_twirl"
    )
    scrambled_basis, scrambled_basis_names, scrambled_basis_audit = _family_feature_matrix(
        records, obs, names, scrambled_manifest, family="basis_rotation"
    )
    scrambled_echo, scrambled_echo_names, scrambled_echo_audit = _family_feature_matrix(
        records, obs, names, scrambled_manifest, family="sign_flip_echo"
    )

    v3c = targeted.feature_spaces["physical_local_inverse_probability_v3_typed"]
    real_all = _finite(np.concatenate([twirl, basis, echo], axis=1))
    scrambled_all = _finite(np.concatenate([scrambled_twirl, scrambled_basis, scrambled_echo], axis=1))
    real_names = [*[f"twirl_{name}" for name in twirl_names], *[f"basis_{name}" for name in basis_names], *[f"echo_{name}" for name in echo_names]]
    scrambled_names = [
        *[f"twirl_scrambled_{name}" for name in scrambled_twirl_names],
        *[f"basis_scrambled_{name}" for name in scrambled_basis_names],
        *[f"echo_scrambled_{name}" for name in scrambled_echo_names],
    ]
    feature_spaces = {
        "minimal_intervention_probe_only_v3c": v3c,
        "twirl_intervention_features": _finite(np.concatenate([v3c, twirl], axis=1)),
        "basis_intervention_features": _finite(np.concatenate([v3c, basis], axis=1)),
        "echo_sign_intervention_features": _finite(np.concatenate([v3c, echo], axis=1)),
        "minimal_intervention_all": _finite(np.concatenate([v3c, real_all], axis=1)),
        "scrambled_minimal_intervention_control": _finite(np.concatenate([v3c, scrambled_all], axis=1)),
    }
    feature_names = {
        "minimal_intervention_probe_only_v3c": [f"v3c_{idx}" for idx in range(v3c.shape[1])],
        "twirl_intervention_features": [*[f"v3c_{idx}" for idx in range(v3c.shape[1])], *twirl_names],
        "basis_intervention_features": [*[f"v3c_{idx}" for idx in range(v3c.shape[1])], *basis_names],
        "echo_sign_intervention_features": [*[f"v3c_{idx}" for idx in range(v3c.shape[1])], *echo_names],
        "minimal_intervention_all": [*[f"v3c_{idx}" for idx in range(v3c.shape[1])], *real_names],
        "scrambled_minimal_intervention_control": [*[f"v3c_{idx}" for idx in range(v3c.shape[1])], *scrambled_names],
    }
    return RZZMinimalInterventionBundle(
        feature_spaces=feature_spaces,
        feature_names=feature_names,
        visible_types=targeted.visible_types,
        type_budgets=targeted.type_budgets,
        intervention_schema=intervention_schema(probe_manifest),
        feature_provenance_manifest=feature_provenance_manifest(feature_names),
        twirl_response_metrics=_response_metrics("twirl", twirl_names, twirl_audit, scrambled_twirl_audit),
        basis_response_metrics=_response_metrics("basis", basis_names, basis_audit, scrambled_basis_audit),
        echo_response_metrics=_response_metrics("echo", echo_names, echo_audit, scrambled_echo_audit),
    )


def evaluate_rzz_minimal_intervention_methods(
    records: list[dict[str, object]],
    observations: np.ndarray,
    probe_names: Iterable[str],
    hidden_labels: torch.Tensor,
    label_names: list[str],
    *,
    comparison_labels: dict[str, list[int]] | None = None,
    bootstrap_replicates: int = 0,
    seed: int = 0,
) -> dict[str, object]:
    bundle = build_rzz_minimal_intervention_features(records, observations, probe_names, num_clusters=len(label_names))
    comparison_labels = comparison_labels or {}
    method_specs = [
        ("minimal_intervention_probe_only_v3c", "minimal_intervention_probe_only_v3c", comparison_labels.get("minimal_intervention_probe_only_v3c")),
        ("twirl_intervention_features", "twirl_intervention_features", None),
        ("basis_intervention_features", "basis_intervention_features", None),
        ("echo_sign_intervention_features", "echo_sign_intervention_features", None),
        ("minimal_intervention_all", "minimal_intervention_all", None),
        ("scrambled_minimal_intervention_control", "scrambled_minimal_intervention_control", None),
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
        row = _method_record(method, feature_key, features, labels, hidden_labels, len(label_names))
        if method == "minimal_intervention_all":
            row["bootstrap_nmi"] = bootstrap_intervention_nmi(
                records,
                observations,
                probe_names,
                reference_labels=labels,
                num_clusters=len(label_names),
                seed=int(seed),
                replicates=int(bootstrap_replicates),
            )
        rows.append(row)
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
                "uses_exact_ptm": method == "oracle_fingerprint_upper_bound",
                **_partition_record(labels_int, hidden_labels, len(label_names)),
            }
        )
    return {
        "intervention_schema": bundle.intervention_schema,
        "feature_provenance_manifest": bundle.feature_provenance_manifest,
        "twirl_response_metrics": bundle.twirl_response_metrics,
        "basis_response_metrics": bundle.basis_response_metrics,
        "echo_response_metrics": bundle.echo_response_metrics,
        "mechanism_response_table": mechanism_response_table(records, labels_by_method, hidden_labels, label_names, bundle),
        "visible_type_counts": _counts(bundle.visible_types),
        "type_budgets": bundle.type_budgets,
        "methods": rows,
        "labels_by_method": labels_by_method,
        "rzz_family_metrics": rzz_family_metrics(labels_by_method, hidden_labels, label_names),
        "rzz_family_distance_audit": rzz_family_distance_audit(bundle.feature_spaces, hidden_labels, label_names),
        "scrambled_intervention_control": _scrambled_intervention_control(rows),
        "key_comparison": _key_comparison(rows),
    }


def bootstrap_intervention_nmi(
    records: list[dict[str, object]],
    observations: np.ndarray,
    probe_names: Iterable[str],
    *,
    reference_labels: list[int],
    num_clusters: int,
    seed: int,
    replicates: int,
) -> dict[str, object]:
    if int(replicates) <= 0:
        return {"replicates": 0, "mean_vs_full": 1.0, "min_vs_full": 1.0, "labels": []}
    obs = _validate_observations(observations)
    rng = np.random.default_rng(int(seed) + 20_800)
    labels = []
    scores = []
    for _ in range(int(replicates)):
        indices = rng.integers(0, obs.shape[1], size=obs.shape[1])
        boot = obs[:, indices, :]
        bundle = build_rzz_minimal_intervention_features(records, boot, probe_names, num_clusters=int(num_clusters))
        current = typed_cluster_labels(bundle.feature_spaces["minimal_intervention_all"], bundle.visible_types, bundle.type_budgets)
        labels.append(current)
        scores.append(float(normalized_mutual_info(reference_labels, current)))
    return {
        "replicates": int(replicates),
        "mean_vs_full": float(np.mean(scores)) if scores else 1.0,
        "min_vs_full": float(np.min(scores)) if scores else 1.0,
        "labels": labels,
    }


def intervention_schema(probe_manifest: dict[str, object]) -> dict[str, object]:
    records = [
        record
        for record in probe_manifest.get("probe_records", [])
        if isinstance(record, dict) and str(record.get("base_probe_name")) in set(RZZ_MINIMAL_INTERVENTION_PROBES)
    ]
    return {
        "schema": "scope_static_s2d8d_intervention_schema_v1",
        "probe_set": "rzz_minimal_intervention",
        "probe_set_role": "learner_visible_minimal_RZZ_intervention_metadata",
        "edge_orientation_rule": EDGE_ORIENTATION_RULE,
        "edge_coloring_rule": "even_odd_left_edge_index_coloring",
        "families": {
            "baseline": ["rzz_int_no_intervention"],
            "pauli_frame_twirl": ["rzz_int_twirl_x_left_even/odd", "rzz_int_twirl_y_left_even/odd", "rzz_int_twirl_xy_even/odd"],
            "basis_rotation": ["rzz_int_basis_x", "rzz_int_basis_y", "rzz_int_basis_xz", "rzz_int_basis_yz"],
            "sign_flip_echo": ["rzz_int_sign_no_flip", "rzz_int_sign_flip_left_even/odd", "rzz_int_sign_flip_right_even/odd"],
        },
        "learner_visible_inputs": ["shot_bits", "probe_metadata", "edge_index", "circuit_schedule"],
        "forbidden_in_phys3": ["exact_ptm_entries", "rzz_type_features", "oracle_fingerprints", "teacher_channels", "oracle_labels"],
        "probe_records": records,
    }


def feature_provenance_manifest(feature_names: dict[str, list[str]]) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d8d_feature_provenance_manifest_v1",
        "edge_orientation_rule": EDGE_ORIENTATION_RULE,
        "learner_visible_rule": (
            "minimal intervention features are computable from shot bits, intervention probe metadata, "
            "visible edge index, and circuit schedule only"
        ),
        "feature_blocks": {
            block: [
                {
                    "feature_name": name,
                    "source": "learner_counts" if block != "minimal_intervention_probe_only_v3c" else "learner_counts_and_visible_schedule",
                    "uses_oracle_label": False,
                    "uses_exact_teacher_channel": False,
                    "uses_exact_ptm": False,
                    "visible_inputs": ["shot_bits", "probe_intervention_metadata", "edge_index", "circuit_schedule"],
                }
                for name in names
            ]
            for block, names in feature_names.items()
        },
        "audit_only_blocks": {
            "exact_ptm": {"oracle_only": True},
            "rzz_type_features": {"oracle_only": True},
            "oracle_fingerprint_upper_bound": {"oracle_only": True},
        },
    }


def mechanism_response_table(
    records: list[dict[str, object]],
    labels_by_method: dict[str, list[int]],
    hidden_labels: torch.Tensor,
    label_names: list[str],
    bundle: RZZMinimalInterventionBundle,
) -> dict[str, object]:
    labels = torch.as_tensor(hidden_labels, dtype=torch.long).numpy()
    family_ids = [idx for idx, name in enumerate(label_names) if name in set(RZZ_FAMILY_IDS[:4])]
    rows = []
    method_labels = labels_by_method.get("minimal_intervention_all", [])
    features = bundle.feature_spaces["minimal_intervention_all"]
    for label_id in family_ids:
        mask = labels == int(label_id)
        if not np.any(mask):
            continue
        rows.append(
            {
                "oracle_label": label_names[int(label_id)],
                "num_rows": int(np.sum(mask)),
                "mean_feature_norm": float(np.mean(np.linalg.norm(features[mask], axis=1))),
                "predicted_clusters": sorted({int(method_labels[idx]) for idx, keep in enumerate(mask.tolist()) if keep}) if method_labels else [],
                "record_refs": [
                    {
                        "location_id": int(record.get("location_id", idx)),
                        "circuit_id": int(record.get("circuit_id", 0)),
                        "qubits": [int(value) for value in record.get("qubits", [])],
                    }
                    for idx, record in enumerate(records)
                    if bool(mask[idx])
                ],
            }
        )
    return {
        "schema": "scope_static_s2d8d_mechanism_response_table_v1",
        "primary_method": "minimal_intervention_all",
        "rows": rows,
    }


def _family_feature_matrix(
    records: list[dict[str, object]],
    observations: np.ndarray,
    probe_names: list[str],
    probe_manifest: dict[str, object],
    *,
    family: str,
) -> tuple[np.ndarray, list[str], dict[str, object]]:
    by_role = _probe_indices_by_intervention(probe_manifest)
    roles, baseline_role = _family_roles(family)
    rows = []
    audit_records = []
    for idx, record in enumerate(records):
        baseline_family = "baseline" if baseline_role == "no_intervention" else family
        baseline = _estimate_intervention_moment(record, observations, probe_names, by_role, baseline_family, baseline_role)
        role_stats = {role: _estimate_intervention_moment(record, observations, probe_names, by_role, family, role) for role in roles}
        row = []
        row.extend([baseline[name] for name in STAT_NAMES])
        for role in roles:
            row.extend([role_stats[role][name] for name in STAT_NAMES])
        row.extend(_contrast_features(baseline, role_stats, roles))
        rows.append(row)
        if str(record.get("instruction")) == "rzz":
            audit_records.append(
                {
                    "location_id": int(record.get("location_id", idx)),
                    "oracle_label_evaluator_only": str(record.get("oracle_label", "")),
                    "qubits": _record_qubits(record),
                    "family": family,
                    "baseline_role": baseline_role,
                    "baseline_stats": baseline,
                    "role_stats": role_stats,
                    "contrast_features": dict(zip(_contrast_feature_names(roles), _contrast_features(baseline, role_stats, roles))),
                }
            )
    return _finite(np.asarray(rows, dtype=np.float64)), _family_feature_names(family, roles, baseline_role), {"rzz_location_records": audit_records}


def _estimate_intervention_moment(
    record: dict[str, object],
    observations: np.ndarray,
    probe_names: list[str],
    by_role: dict[str, dict[str, dict[str, list[int]]]],
    family: str,
    role: str,
) -> dict[str, object]:
    qubits = _record_qubits(record)
    if len(qubits) < 2:
        return _empty_stats(family, role)
    left = min(qubits)
    right = max(qubits)
    edge_parity = "even" if left % 2 == 0 else "odd"
    role_bucket = by_role.get(family, {}).get(role, {})
    indices = list(role_bucket.get("all", []))
    indices.extend(role_bucket.get(edge_parity, []))
    allowed = set(_record_probe_indices(record, len(probe_names)))
    estimates = []
    for probe_idx in indices:
        if int(probe_idx) not in allowed:
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
        se = _standard_error(mean, product.size)
        estimates.append(
            {
                "mean": mean,
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
        return _empty_stats(family, role)
    return {
        "family": family,
        "role": role,
        "edge_parity": edge_parity,
        "available": True,
        "mean": float(np.mean([item["mean"] for item in estimates])),
        "connected": float(np.mean([item["connected"] for item in estimates])),
        "normalized_correlation": float(np.mean([item["normalized_correlation"] for item in estimates])),
        "standard_error": float(np.sqrt(np.sum([float(item["standard_error"]) ** 2 for item in estimates])) / len(estimates)),
        "z_score": float(np.mean([item["z_score"] for item in estimates])),
        "num_shots": int(sum(int(item["num_shots"]) for item in estimates)),
        "probes": [{"probe_index": item["probe_index"], "probe_name": item["probe_name"]} for item in estimates],
    }


def _contrast_features(baseline: dict[str, object], role_stats: dict[str, dict[str, object]], roles: tuple[str, ...]) -> list[float]:
    values = []
    for role in roles:
        for stat_name in ("mean", "connected", "normalized_correlation"):
            values.append(float(role_stats[role][stat_name]) - float(baseline[stat_name]))
    connected_values = np.asarray([float(role_stats[role]["connected"]) for role in roles], dtype=np.float64)
    mean_values = np.asarray([float(role_stats[role]["mean"]) for role in roles], dtype=np.float64)
    normalized_values = np.asarray([float(role_stats[role]["normalized_correlation"]) for role in roles], dtype=np.float64)
    deltas = connected_values - float(baseline["connected"])
    values.extend(
        [
            float(np.linalg.norm(deltas)),
            float(np.linalg.norm(mean_values - float(baseline["mean"]))),
            float(np.var(connected_values)),
            float(np.var(normalized_values)),
            float(np.max(connected_values) - np.min(connected_values)) if connected_values.size else 0.0,
            float(np.mean(connected_values) / (abs(float(baseline["connected"])) + 1e-6)) if connected_values.size else 0.0,
        ]
    )
    return values


def _family_feature_names(family: str, roles: tuple[str, ...], baseline_role: str) -> list[str]:
    names = [f"{baseline_role}_zz_{name}" for name in STAT_NAMES]
    for role in roles:
        names.extend([f"{role}_zz_{name}" for name in STAT_NAMES])
    names.extend(_contrast_feature_names(roles))
    return [f"{family}_{name}" for name in names]


def _contrast_feature_names(roles: tuple[str, ...]) -> list[str]:
    names = []
    for role in roles:
        for stat_name in ("mean", "connected", "normalized_correlation"):
            names.append(f"{role}_minus_baseline_{stat_name}")
    names.extend(
        [
            "intervention_contrast_norm_connected",
            "intervention_contrast_norm_mean",
            "intervention_response_variance_connected",
            "intervention_response_variance_normalized_correlation",
            "intervention_response_range_connected",
            "mean_intervention_over_baseline_connected",
        ]
    )
    return names


def _probe_indices_by_intervention(probe_manifest: dict[str, object]) -> dict[str, dict[str, dict[str, list[int]]]]:
    out: dict[str, dict[str, dict[str, list[int]]]] = {}
    for record in probe_manifest.get("probe_records", []):
        if not isinstance(record, dict):
            continue
        base_name = str(record.get("base_probe_name", ""))
        family = str(record.get("rzz_intervention_family", probe_rzz_intervention_family(base_name)))
        if family == "none":
            continue
        role = str(record.get("rzz_intervention_role", probe_rzz_intervention_role(base_name)))
        parity = str(record.get("rzz_intervention_edge_parity", probe_rzz_intervention_edge_parity(base_name)))
        out.setdefault(family, {}).setdefault(role, {"all": [], "even": [], "odd": []})
        if parity in out[family][role]:
            out[family][role][parity].append(int(record["probe_index"]))
    return out


def _family_roles(family: str) -> tuple[tuple[str, ...], str]:
    if family == "pauli_frame_twirl":
        return TWIRL_ROLES, "no_intervention"
    if family == "basis_rotation":
        return BASIS_ROLES, "no_intervention"
    if family == "sign_flip_echo":
        return SIGN_ROLES, "sign_no_flip"
    raise ValueError(f"unknown S2D.8d intervention family {family!r}")


def _scrambled_intervention_manifest(probe_manifest: dict[str, object]) -> dict[str, object]:
    records = [dict(record) for record in probe_manifest.get("probe_records", [])]
    role_mapping = {
        "x": "y",
        "y": "xz",
        "xz": "yz",
        "yz": "x",
        "twirl_x_left": "twirl_y_left",
        "twirl_y_left": "twirl_xy",
        "twirl_xy": "twirl_x_left",
        "sign_flip_left": "sign_flip_right",
        "sign_flip_right": "sign_flip_left",
    }
    parity_mapping = {"even": "odd", "odd": "even"}
    for record in records:
        base_name = str(record.get("base_probe_name", ""))
        if base_name not in set(RZZ_MINIMAL_INTERVENTION_PROBES):
            continue
        role = str(record.get("rzz_intervention_role", probe_rzz_intervention_role(base_name)))
        parity = str(record.get("rzz_intervention_edge_parity", probe_rzz_intervention_edge_parity(base_name)))
        record["rzz_intervention_role"] = role_mapping.get(role, role)
        record["rzz_intervention_edge_parity"] = parity_mapping.get(parity, parity)
        record["scrambled_intervention_control"] = role != "no_intervention"
    return {**probe_manifest, "schema": "scope_static_s2d8d_scrambled_intervention_probe_manifest_v1", "probe_records": records}


def _response_metrics(name: str, feature_names: list[str], real_audit: dict[str, object], scrambled_audit: dict[str, object]) -> dict[str, object]:
    return {
        "schema": f"scope_static_s2d8d_{name}_response_metrics_v1",
        "feature_names": feature_names,
        "real_response_audit": real_audit,
        "scrambled_response_audit": scrambled_audit,
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


def _scrambled_intervention_control(rows: list[dict[str, object]]) -> dict[str, object]:
    by_method = {str(row["method"]): row for row in rows}
    real = by_method.get("minimal_intervention_all", {})
    scrambled = by_method.get("scrambled_minimal_intervention_control", {})
    return {
        "real_method": "minimal_intervention_all",
        "scrambled_method": "scrambled_minimal_intervention_control",
        "real_ari": real.get("ari"),
        "real_nmi": real.get("nmi"),
        "scrambled_ari": scrambled.get("ari"),
        "scrambled_nmi": scrambled.get("nmi"),
        "real_beats_scrambled": _beats(real, scrambled),
    }


def _key_comparison(rows: list[dict[str, object]]) -> dict[str, object]:
    by_method = {str(row["method"]): row for row in rows}
    real = by_method.get("minimal_intervention_all", {})
    probe_only = by_method.get("minimal_intervention_probe_only_v3c", {})
    scrambled = by_method.get("scrambled_minimal_intervention_control", {})
    direct = by_method.get("direct_Salpha", {})
    return {
        "primary": "minimal_intervention_all",
        "minimal_intervention_ari": real.get("ari"),
        "minimal_intervention_nmi": real.get("nmi"),
        "delta_ari_vs_probe_only": float(real.get("ari", 0.0)) - float(probe_only.get("ari", 0.0)),
        "delta_nmi_vs_probe_only": float(real.get("nmi", 0.0)) - float(probe_only.get("nmi", 0.0)),
        "beats_scrambled": _beats(real, scrambled),
        "beats_direct_Salpha": _beats(real, direct),
    }


def _beats(left: dict[str, object], right: dict[str, object]) -> bool:
    return float(left.get("ari", 0.0)) > float(right.get("ari", 0.0)) and float(left.get("nmi", 0.0)) > float(right.get("nmi", 0.0))


def _empty_stats(family: str, role: str) -> dict[str, object]:
    return {
        "family": family,
        "role": role,
        "edge_parity": "none",
        "available": False,
        "mean": 0.0,
        "connected": 0.0,
        "normalized_correlation": 0.0,
        "standard_error": 0.0,
        "z_score": 0.0,
        "num_shots": 0,
        "probes": [],
    }


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


def _finite(values: np.ndarray) -> np.ndarray:
    return np.nan_to_num(np.asarray(values, dtype=np.float64), nan=NUMERICAL_ZERO, posinf=NUMERICAL_ZERO, neginf=-NUMERICAL_ZERO)
