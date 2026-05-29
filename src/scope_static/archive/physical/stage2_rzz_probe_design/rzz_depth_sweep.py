from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import torch

from scope_static.identifiability import evaluate_partition
from scope_static.local_mechanism import split_merge_audit
from scope_static.metrics import normalized_mutual_info
from scope_static.numerics import NUMERICAL_ZERO

from scope_static.physical.active_mixed_basis import rzz_family_distance_audit, rzz_family_metrics
from scope_static.physical.targeted_v3 import build_targeted_v3_features, typed_cluster_labels
from scope_static.physical.teacher import EDGE_ORIENTATION_RULE, RZZ_DEPTH_SWEEP_DEPTHS, build_probe_basis_manifest, probe_rzz_depth


DEPTHS = tuple(int(value) for value in RZZ_DEPTH_SWEEP_DEPTHS)


@dataclass(frozen=True)
class RZZDepthFeatureBundle:
    feature_spaces: dict[str, np.ndarray]
    feature_names: dict[str, list[str]]
    visible_types: list[str]
    type_budgets: dict[str, int]
    depth_probe_manifest: dict[str, object]
    feature_provenance_manifest: dict[str, object]
    depth_response_features: dict[str, object]


def build_rzz_depth_sweep_features(
    records: list[dict[str, object]],
    observations: np.ndarray,
    probe_names: Iterable[str],
    *,
    num_clusters: int,
) -> RZZDepthFeatureBundle:
    obs = _validate_observations(observations)
    names = [str(name) for name in probe_names]
    num_qubits = int(obs.shape[2])
    targeted = build_targeted_v3_features(records, obs, names, num_clusters=int(num_clusters))
    probe_manifest = build_probe_basis_manifest(names, num_qubits=num_qubits)
    scrambled_manifest = _scrambled_depth_manifest(probe_manifest)
    depth_features, depth_names, depth_audit = _depth_feature_matrix(records, obs, names, probe_manifest)
    scrambled_features, scrambled_names, scrambled_audit = _depth_feature_matrix(records, obs, names, scrambled_manifest)
    depth_probe_only = targeted.feature_spaces["physical_local_inverse_probability_v3_typed"]
    feature_spaces = {
        "rzz_depth_probe_only_v3c": depth_probe_only,
        "rzz_depth_features": _finite(np.concatenate([depth_probe_only, depth_features], axis=1)),
        "scrambled_depth_control": _finite(np.concatenate([depth_probe_only, scrambled_features], axis=1)),
    }
    feature_names = {
        "rzz_depth_probe_only_v3c": [f"v3c_{idx}" for idx in range(depth_probe_only.shape[1])],
        "rzz_depth_features": [*[f"v3c_{idx}" for idx in range(depth_probe_only.shape[1])], *depth_names],
        "scrambled_depth_control": [*[f"v3c_{idx}" for idx in range(depth_probe_only.shape[1])], *[f"scrambled_{name}" for name in scrambled_names]],
    }
    return RZZDepthFeatureBundle(
        feature_spaces=feature_spaces,
        feature_names=feature_names,
        visible_types=targeted.visible_types,
        type_budgets=targeted.type_budgets,
        depth_probe_manifest=_depth_probe_manifest(probe_manifest),
        feature_provenance_manifest=feature_provenance_manifest(feature_names),
        depth_response_features={
            "schema": "scope_static_s2d8a_depth_response_features_v1",
            "depths": list(DEPTHS),
            "edge_orientation_rule": EDGE_ORIENTATION_RULE,
            "feature_names": depth_names,
            "real_depth_response_audit": depth_audit,
            "scrambled_depth_response_audit": scrambled_audit,
        },
    )


def evaluate_rzz_depth_sweep_methods(
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
    bundle = build_rzz_depth_sweep_features(records, observations, probe_names, num_clusters=len(label_names))
    comparison_labels = comparison_labels or {}
    method_specs = [
        ("rzz_depth_probe_only_v3c", "rzz_depth_probe_only_v3c", comparison_labels.get("rzz_depth_probe_only_v3c")),
        ("rzz_depth_features", "rzz_depth_features", None),
        ("scrambled_depth_control", "scrambled_depth_control", None),
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
        if method == "rzz_depth_features":
            row["bootstrap_nmi"] = bootstrap_depth_nmi(
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
        "depth_probe_manifest": bundle.depth_probe_manifest,
        "feature_provenance_manifest": bundle.feature_provenance_manifest,
        "depth_response_features": bundle.depth_response_features,
        "visible_type_counts": _counts(bundle.visible_types),
        "type_budgets": bundle.type_budgets,
        "methods": rows,
        "labels_by_method": labels_by_method,
        "rzz_family_metrics": rzz_family_metrics(labels_by_method, hidden_labels, label_names),
        "rzz_family_distance_audit": rzz_family_distance_audit(bundle.feature_spaces, hidden_labels, label_names),
        "scrambled_depth_control": _scrambled_depth_control(rows),
        "key_comparison": _key_comparison(rows),
    }


def bootstrap_depth_nmi(
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
    rng = np.random.default_rng(int(seed) + 20_008)
    labels = []
    scores = []
    for _ in range(int(replicates)):
        indices = rng.integers(0, obs.shape[1], size=obs.shape[1])
        boot = obs[:, indices, :]
        bundle = build_rzz_depth_sweep_features(records, boot, probe_names, num_clusters=int(num_clusters))
        current = typed_cluster_labels(bundle.feature_spaces["rzz_depth_features"], bundle.visible_types, bundle.type_budgets)
        labels.append(current)
        scores.append(float(normalized_mutual_info(reference_labels, current)))
    return {
        "replicates": int(replicates),
        "mean_vs_full": float(np.mean(scores)) if scores else 1.0,
        "min_vs_full": float(np.min(scores)) if scores else 1.0,
        "labels": labels,
    }


def feature_provenance_manifest(feature_names: dict[str, list[str]]) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d8a_depth_feature_provenance_manifest_v1",
        "edge_orientation_rule": EDGE_ORIENTATION_RULE,
        "learner_visible_rule": (
            "depth features are computable from circuit schedule, RZZ depth probe names, "
            "visible edge index, and measured bit strings only"
        ),
        "forbidden_in_phys3": [
            "exact_ptm_entries",
            "exact_rzz_type_1_2_3_4_features",
            "oracle_fingerprints",
            "teacher_channels",
            "oracle_mechanism_labels",
        ],
        "feature_blocks": {
            block: [
                {
                    "feature_name": name,
                    "source": "learner_counts" if block != "rzz_depth_probe_only_v3c" else "learner_counts_and_visible_schedule",
                    "uses_oracle_label": False,
                    "uses_exact_teacher_channel": False,
                    "uses_exact_ptm": False,
                    "visible_inputs": ["shot_bits", "probe_depth", "edge_index", "circuit_schedule"],
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


def _depth_feature_matrix(
    records: list[dict[str, object]],
    observations: np.ndarray,
    probe_names: list[str],
    probe_manifest: dict[str, object],
) -> tuple[np.ndarray, list[str], dict[str, object]]:
    obs = _validate_observations(observations)
    by_depth = _probe_indices_by_depth(probe_manifest)
    rows = []
    audit_records = []
    for idx, record in enumerate(records):
        depth_stats = [_estimate_depth_moment(record, obs, probe_names, by_depth, depth) for depth in DEPTHS]
        curve = np.asarray([float(item["connected"]) for item in depth_stats], dtype=np.float64)
        raw_curve = np.asarray([float(item["mean"]) for item in depth_stats], dtype=np.float64)
        norm_curve = np.asarray([float(item["normalized_correlation"]) for item in depth_stats], dtype=np.float64)
        row = []
        for item in depth_stats:
            row.extend([item["mean"], item["connected"], item["normalized_correlation"], item["standard_error"], item["z_score"]])
        row.extend(_curve_features(curve, raw_curve, norm_curve))
        rows.append(row)
        if str(record.get("instruction")) == "rzz":
            audit_records.append(
                {
                    "location_id": int(record.get("location_id", idx)),
                    "qubits": _record_qubits(record),
                    "depth_stats": depth_stats,
                    "curve_features": _curve_feature_dict(curve, raw_curve, norm_curve),
                }
            )
    names = []
    for depth in DEPTHS:
        names.extend(
            [
                f"depth_{depth}_zz_mean",
                f"depth_{depth}_zz_connected",
                f"depth_{depth}_zz_normalized_correlation",
                f"depth_{depth}_zz_standard_error",
                f"depth_{depth}_zz_z_score",
            ]
        )
    names.extend(_curve_feature_names())
    return _finite(np.asarray(rows, dtype=np.float64)), names, {"rzz_location_records": audit_records}


def _estimate_depth_moment(
    record: dict[str, object],
    observations: np.ndarray,
    probe_names: list[str],
    by_depth: dict[int, list[int]],
    depth: int,
) -> dict[str, object]:
    qubits = _record_qubits(record)
    if len(qubits) < 2:
        return _empty_depth_stats(depth)
    left = min(qubits)
    right = max(qubits)
    estimates = []
    allowed = set(_record_probe_indices(record, len(probe_names)))
    for probe_idx in by_depth.get(int(depth), []):
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
        return _empty_depth_stats(depth)
    return {
        "depth": int(depth),
        "available": True,
        "mean": float(np.mean([item["mean"] for item in estimates])),
        "connected": float(np.mean([item["connected"] for item in estimates])),
        "normalized_correlation": float(np.mean([item["normalized_correlation"] for item in estimates])),
        "standard_error": float(np.sqrt(np.sum([float(item["standard_error"]) ** 2 for item in estimates])) / len(estimates)),
        "z_score": float(np.mean([item["z_score"] for item in estimates])),
        "num_shots": int(sum(int(item["num_shots"]) for item in estimates)),
        "probes": [{"probe_index": item["probe_index"], "probe_name": item["probe_name"]} for item in estimates],
    }


def _curve_features(curve: np.ndarray, raw_curve: np.ndarray, norm_curve: np.ndarray) -> list[float]:
    depth_values = np.asarray(DEPTHS, dtype=np.float64)
    slope = _linear_slope(depth_values, curve)
    curvature = _linear_slope(depth_values[1:], np.diff(curve)) if curve.size > 2 else 0.0
    log_decay = _linear_slope(depth_values, np.log(np.clip(np.abs(raw_curve), NUMERICAL_ZERO, None)))
    odd_even = float(np.mean(curve[[idx for idx, depth in enumerate(DEPTHS) if depth % 2 == 1]]) - np.mean(curve[[idx for idx, depth in enumerate(DEPTHS) if depth % 2 == 0]]))
    return [
        float(slope),
        float(curvature),
        float(log_decay),
        float(odd_even),
        float(np.var(curve)),
        float(np.max(curve) - np.min(curve)),
        float(curve[-1] - curve[0]),
        float(raw_curve[-1] / (abs(raw_curve[0]) + 1e-6)),
        float(np.var(norm_curve)),
    ]


def _curve_feature_dict(curve: np.ndarray, raw_curve: np.ndarray, norm_curve: np.ndarray) -> dict[str, float]:
    return dict(zip(_curve_feature_names(), _curve_features(curve, raw_curve, norm_curve)))


def _curve_feature_names() -> list[str]:
    return [
        "depth_slope",
        "depth_curvature",
        "log_decay_proxy",
        "odd_even_contrast",
        "variance_across_depth",
        "depth_response_range",
        "final_minus_initial_depth_response",
        "final_over_initial_raw_response",
        "normalized_response_variance_across_depth",
    ]


def _probe_indices_by_depth(probe_manifest: dict[str, object]) -> dict[int, list[int]]:
    out = {int(depth): [] for depth in DEPTHS}
    for record in probe_manifest.get("probe_records", []):
        if not isinstance(record, dict):
            continue
        base_name = str(record.get("base_probe_name", ""))
        if not base_name.startswith("rzz_depth_"):
            continue
        depth = int(record.get("rzz_depth", probe_rzz_depth(base_name)))
        if depth in out:
            out[depth].append(int(record["probe_index"]))
    return out


def _depth_probe_manifest(probe_manifest: dict[str, object]) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d8a_depth_probe_manifest_v1",
        "probe_set_role": "learner_visible_rzz_depth_sweep_metadata",
        "edge_orientation_rule": EDGE_ORIENTATION_RULE,
        "depths": list(DEPTHS),
        "probe_records": [
            record
            for record in probe_manifest.get("probe_records", [])
            if isinstance(record, dict) and str(record.get("base_probe_name", "")).startswith("rzz_depth_")
        ],
    }


def _scrambled_depth_manifest(probe_manifest: dict[str, object]) -> dict[str, object]:
    records = [dict(record) for record in probe_manifest.get("probe_records", [])]
    depth_records = [record for record in records if str(record.get("base_probe_name", "")).startswith("rzz_depth_")]
    if depth_records:
        shifted_depths = list(DEPTHS[1:] + DEPTHS[:1])
        mapping = {depth: shifted_depths[idx] for idx, depth in enumerate(DEPTHS)}
        for record in depth_records:
            old_depth = int(record.get("rzz_depth", probe_rzz_depth(str(record.get("base_probe_name")))))
            record["rzz_depth"] = int(mapping.get(old_depth, old_depth))
            record["scrambled_depth_control"] = True
    return {**probe_manifest, "schema": "scope_static_s2d8a_scrambled_depth_probe_manifest_v1", "probe_records": records}


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


def _scrambled_depth_control(rows: list[dict[str, object]]) -> dict[str, object]:
    by_method = {str(row["method"]): row for row in rows}
    real = by_method.get("rzz_depth_features", {})
    scrambled = by_method.get("scrambled_depth_control", {})
    return {
        "real_method": "rzz_depth_features",
        "scrambled_method": "scrambled_depth_control",
        "real_ari": real.get("ari"),
        "real_nmi": real.get("nmi"),
        "scrambled_ari": scrambled.get("ari"),
        "scrambled_nmi": scrambled.get("nmi"),
        "real_beats_scrambled": _beats(real, scrambled),
    }


def _key_comparison(rows: list[dict[str, object]]) -> dict[str, object]:
    by_method = {str(row["method"]): row for row in rows}
    depth = by_method.get("rzz_depth_features", {})
    probe_only = by_method.get("rzz_depth_probe_only_v3c", {})
    scrambled = by_method.get("scrambled_depth_control", {})
    direct = by_method.get("direct_Salpha", {})
    return {
        "primary": "rzz_depth_features",
        "depth_ari": depth.get("ari"),
        "depth_nmi": depth.get("nmi"),
        "delta_ari_vs_depth_probe_only": float(depth.get("ari", 0.0)) - float(probe_only.get("ari", 0.0)),
        "delta_nmi_vs_depth_probe_only": float(depth.get("nmi", 0.0)) - float(probe_only.get("nmi", 0.0)),
        "beats_scrambled": _beats(depth, scrambled),
        "beats_direct_Salpha": _beats(depth, direct),
    }


def _beats(left: dict[str, object], right: dict[str, object]) -> bool:
    return float(left.get("ari", 0.0)) > float(right.get("ari", 0.0)) and float(left.get("nmi", 0.0)) > float(right.get("nmi", 0.0))


def _empty_depth_stats(depth: int) -> dict[str, object]:
    return {
        "depth": int(depth),
        "available": False,
        "mean": 0.0,
        "connected": 0.0,
        "normalized_correlation": 0.0,
        "standard_error": 0.0,
        "z_score": 0.0,
        "num_shots": 0,
        "probes": [],
    }


def _linear_slope(x_values: np.ndarray, y_values: np.ndarray) -> float:
    x = np.asarray(x_values, dtype=np.float64)
    y = np.asarray(y_values, dtype=np.float64)
    if x.size < 2 or y.size < 2 or x.size != y.size:
        return 0.0
    return float(np.polyfit(x, y, deg=1)[0])


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
