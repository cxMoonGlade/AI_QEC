from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import torch

from scope_static.identifiability import evaluate_partition
from scope_static.dem.local_mechanism import split_merge_audit
from scope_static.dem.metrics import normalized_mutual_info
from scope_static.numerics import NUMERICAL_ZERO

from scope_static.archive.catalog.stage2_rzz_probe_design.active_mixed_basis import rzz_family_distance_audit, rzz_family_metrics
from scope_static.archive.catalog.stage2_learner_limit.targeted_v3 import build_targeted_v3_features, typed_cluster_labels
from scope_static.primitives.probe_catalog import (
    EDGE_ORIENTATION_RULE,
    RZZ_ECHO_CONTRAST_PROBES,
    build_probe_basis_manifest,
    probe_rzz_echo_edge_parity,
    probe_rzz_echo_role,
)


ECHO_ROLES = ("no_echo", "echo_left", "echo_right", "echo_both")
ECHO_STAT_NAMES = ("mean", "connected", "normalized_correlation", "standard_error", "z_score")
ECHO_DELTA_PAIRS = (
    ("no_echo", "echo_left"),
    ("no_echo", "echo_right"),
    ("no_echo", "echo_both"),
    ("echo_left", "echo_right"),
    ("echo_both", "no_echo"),
)


@dataclass(frozen=True)
class RZZEchoFeatureBundle:
    feature_spaces: dict[str, np.ndarray]
    feature_names: dict[str, list[str]]
    visible_types: list[str]
    type_budgets: dict[str, int]
    echo_probe_manifest: dict[str, object]
    feature_provenance_manifest: dict[str, object]
    echo_response_features: dict[str, object]


def build_rzz_echo_contrast_features(
    records: list[dict[str, object]],
    observations: np.ndarray,
    probe_names: Iterable[str],
    *,
    num_clusters: int,
) -> RZZEchoFeatureBundle:
    obs = _validate_observations(observations)
    names = [str(name) for name in probe_names]
    num_qubits = int(obs.shape[2])
    targeted = build_targeted_v3_features(records, obs, names, num_clusters=int(num_clusters))
    probe_manifest = build_probe_basis_manifest(names, num_qubits=num_qubits)
    scrambled_manifest = _scrambled_echo_manifest(probe_manifest)
    echo_features, echo_names, echo_audit = _echo_feature_matrix(records, obs, names, probe_manifest)
    scrambled_features, scrambled_names, scrambled_audit = _echo_feature_matrix(records, obs, names, scrambled_manifest)
    echo_probe_only = targeted.feature_spaces["physical_local_inverse_probability_v3_typed"]
    feature_spaces = {
        "rzz_echo_probe_only_v3c": echo_probe_only,
        "rzz_echo_contrast_features": _finite(np.concatenate([echo_probe_only, echo_features], axis=1)),
        "scrambled_echo_control": _finite(np.concatenate([echo_probe_only, scrambled_features], axis=1)),
    }
    feature_names = {
        "rzz_echo_probe_only_v3c": [f"v3c_{idx}" for idx in range(echo_probe_only.shape[1])],
        "rzz_echo_contrast_features": [*[f"v3c_{idx}" for idx in range(echo_probe_only.shape[1])], *echo_names],
        "scrambled_echo_control": [*[f"v3c_{idx}" for idx in range(echo_probe_only.shape[1])], *[f"scrambled_{name}" for name in scrambled_names]],
    }
    return RZZEchoFeatureBundle(
        feature_spaces=feature_spaces,
        feature_names=feature_names,
        visible_types=targeted.visible_types,
        type_budgets=targeted.type_budgets,
        echo_probe_manifest=_echo_probe_manifest(probe_manifest),
        feature_provenance_manifest=feature_provenance_manifest(feature_names),
        echo_response_features={
            "schema": "scope_static_s2d8b_echo_response_features_v1",
            "echo_roles": list(ECHO_ROLES),
            "edge_orientation_rule": EDGE_ORIENTATION_RULE,
            "edge_coloring_rule": "even_odd_left_edge_index_coloring",
            "feature_names": echo_names,
            "real_echo_response_audit": echo_audit,
            "scrambled_echo_response_audit": scrambled_audit,
        },
    )


def evaluate_rzz_echo_contrast_methods(
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
    bundle = build_rzz_echo_contrast_features(records, observations, probe_names, num_clusters=len(label_names))
    comparison_labels = comparison_labels or {}
    method_specs = [
        ("rzz_echo_probe_only_v3c", "rzz_echo_probe_only_v3c", comparison_labels.get("rzz_echo_probe_only_v3c")),
        ("rzz_echo_contrast_features", "rzz_echo_contrast_features", None),
        ("scrambled_echo_control", "scrambled_echo_control", None),
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
        if method == "rzz_echo_contrast_features":
            row["bootstrap_nmi"] = bootstrap_echo_nmi(
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
        "echo_probe_manifest": bundle.echo_probe_manifest,
        "feature_provenance_manifest": bundle.feature_provenance_manifest,
        "echo_response_features": bundle.echo_response_features,
        "visible_type_counts": _counts(bundle.visible_types),
        "type_budgets": bundle.type_budgets,
        "methods": rows,
        "labels_by_method": labels_by_method,
        "rzz_family_metrics": rzz_family_metrics(labels_by_method, hidden_labels, label_names),
        "rzz_family_distance_audit": rzz_family_distance_audit(bundle.feature_spaces, hidden_labels, label_names),
        "scrambled_echo_control": _scrambled_echo_control(rows),
        "key_comparison": _key_comparison(rows),
    }


def bootstrap_echo_nmi(
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
    rng = np.random.default_rng(int(seed) + 20_080)
    labels = []
    scores = []
    for _ in range(int(replicates)):
        indices = rng.integers(0, obs.shape[1], size=obs.shape[1])
        boot = obs[:, indices, :]
        bundle = build_rzz_echo_contrast_features(records, boot, probe_names, num_clusters=int(num_clusters))
        current = typed_cluster_labels(bundle.feature_spaces["rzz_echo_contrast_features"], bundle.visible_types, bundle.type_budgets)
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
        "schema": "scope_static_s2d8b_echo_feature_provenance_manifest_v1",
        "edge_orientation_rule": EDGE_ORIENTATION_RULE,
        "edge_coloring_rule": "even_odd_left_edge_index_coloring",
        "learner_visible_rule": (
            "echo contrast features are computable from circuit schedule, echo/no-echo probe names, "
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
                    "source": "learner_counts" if block != "rzz_echo_probe_only_v3c" else "learner_counts_and_visible_schedule",
                    "uses_oracle_label": False,
                    "uses_exact_teacher_channel": False,
                    "uses_exact_ptm": False,
                    "visible_inputs": ["shot_bits", "probe_echo_role", "probe_echo_edge_parity", "edge_index", "circuit_schedule"],
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


def _echo_feature_matrix(
    records: list[dict[str, object]],
    observations: np.ndarray,
    probe_names: list[str],
    probe_manifest: dict[str, object],
) -> tuple[np.ndarray, list[str], dict[str, object]]:
    obs = _validate_observations(observations)
    by_echo = _probe_indices_by_echo(probe_manifest)
    rows = []
    audit_records = []
    for idx, record in enumerate(records):
        role_stats = {role: _estimate_echo_moment(record, obs, probe_names, by_echo, role) for role in ECHO_ROLES}
        row = []
        for role in ECHO_ROLES:
            row.extend([role_stats[role][name] for name in ECHO_STAT_NAMES])
        row.extend(_contrast_features(role_stats))
        rows.append(row)
        if str(record.get("instruction")) == "rzz":
            audit_records.append(
                {
                    "location_id": int(record.get("location_id", idx)),
                    "qubits": _record_qubits(record),
                    "edge_parity": _record_edge_parity(record),
                    "role_stats": role_stats,
                    "contrast_features": _contrast_feature_dict(role_stats),
                }
            )
    return _finite(np.asarray(rows, dtype=np.float64)), _echo_feature_names(), {"rzz_location_records": audit_records}


def _estimate_echo_moment(
    record: dict[str, object],
    observations: np.ndarray,
    probe_names: list[str],
    by_echo: dict[str, dict[str, list[int]]],
    role: str,
) -> dict[str, object]:
    qubits = _record_qubits(record)
    if len(qubits) < 2:
        return _empty_echo_stats(role)
    left = min(qubits)
    right = max(qubits)
    edge_parity = "even" if left % 2 == 0 else "odd"
    indices = by_echo.get(role, {}).get("all" if role == "no_echo" else edge_parity, [])
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
        return _empty_echo_stats(role)
    return {
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


def _contrast_features(role_stats: dict[str, dict[str, object]]) -> list[float]:
    values = []
    for left, right in ECHO_DELTA_PAIRS:
        for stat_name in ("mean", "connected", "normalized_correlation"):
            values.append(float(role_stats[left][stat_name]) - float(role_stats[right][stat_name]))
    connected_deltas = np.asarray(
        [float(role_stats["no_echo"]["connected"]) - float(role_stats[role]["connected"]) for role in ("echo_left", "echo_right", "echo_both")],
        dtype=np.float64,
    )
    mean_deltas = np.asarray(
        [float(role_stats["no_echo"]["mean"]) - float(role_stats[role]["mean"]) for role in ("echo_left", "echo_right", "echo_both")],
        dtype=np.float64,
    )
    norm_values = np.asarray([float(role_stats[role]["normalized_correlation"]) for role in ECHO_ROLES], dtype=np.float64)
    connected_values = np.asarray([float(role_stats[role]["connected"]) for role in ECHO_ROLES], dtype=np.float64)
    values.extend(
        [
            float(np.linalg.norm(connected_deltas)),
            float(np.linalg.norm(mean_deltas)),
            float(np.var(connected_values)),
            float(np.var(norm_values)),
            float(role_stats["echo_left"]["connected"]) - float(role_stats["echo_right"]["connected"]),
            float(role_stats["no_echo"]["connected"]) / (abs(float(role_stats["echo_both"]["connected"])) + 1e-6),
        ]
    )
    return values


def _contrast_feature_dict(role_stats: dict[str, dict[str, object]]) -> dict[str, float]:
    return dict(zip(_contrast_feature_names(), _contrast_features(role_stats)))


def _echo_feature_names() -> list[str]:
    names = []
    for role in ECHO_ROLES:
        names.extend([f"{role}_zz_{name}" for name in ECHO_STAT_NAMES])
    names.extend(_contrast_feature_names())
    return names


def _contrast_feature_names() -> list[str]:
    names = []
    for left, right in ECHO_DELTA_PAIRS:
        for stat_name in ("mean", "connected", "normalized_correlation"):
            names.append(f"{left}_minus_{right}_{stat_name}")
    names.extend(
        [
            "echo_contrast_norm_connected",
            "echo_contrast_norm_mean",
            "echo_response_variance_connected",
            "echo_response_variance_normalized_correlation",
            "echo_signed_left_right_asymmetry_connected",
            "no_echo_over_echo_both_connected",
        ]
    )
    return names


def _probe_indices_by_echo(probe_manifest: dict[str, object]) -> dict[str, dict[str, list[int]]]:
    out = {role: {"all": [], "even": [], "odd": []} for role in ECHO_ROLES}
    for record in probe_manifest.get("probe_records", []):
        if not isinstance(record, dict):
            continue
        base_name = str(record.get("base_probe_name", ""))
        if base_name not in set(RZZ_ECHO_CONTRAST_PROBES):
            continue
        role = str(record.get("rzz_echo_role", probe_rzz_echo_role(base_name)))
        parity = str(record.get("rzz_echo_edge_parity", probe_rzz_echo_edge_parity(base_name)))
        if role in out and parity in out[role]:
            out[role][parity].append(int(record["probe_index"]))
    return out


def _echo_probe_manifest(probe_manifest: dict[str, object]) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d8b_echo_probe_manifest_v1",
        "probe_set_role": "learner_visible_rzz_echo_no_echo_metadata",
        "edge_orientation_rule": EDGE_ORIENTATION_RULE,
        "edge_coloring_rule": "even_odd_left_edge_index_coloring",
        "echo_roles": list(ECHO_ROLES),
        "probe_records": [
            record
            for record in probe_manifest.get("probe_records", [])
            if isinstance(record, dict) and str(record.get("base_probe_name", "")) in set(RZZ_ECHO_CONTRAST_PROBES)
        ],
    }


def _scrambled_echo_manifest(probe_manifest: dict[str, object]) -> dict[str, object]:
    records = [dict(record) for record in probe_manifest.get("probe_records", [])]
    role_mapping = {"echo_left": "echo_right", "echo_right": "echo_both", "echo_both": "echo_left"}
    parity_mapping = {"even": "odd", "odd": "even"}
    for record in records:
        base_name = str(record.get("base_probe_name", ""))
        if base_name not in set(RZZ_ECHO_CONTRAST_PROBES):
            continue
        role = str(record.get("rzz_echo_role", probe_rzz_echo_role(base_name)))
        parity = str(record.get("rzz_echo_edge_parity", probe_rzz_echo_edge_parity(base_name)))
        record["rzz_echo_role"] = role_mapping.get(role, role)
        record["rzz_echo_edge_parity"] = parity_mapping.get(parity, parity)
        record["scrambled_echo_control"] = role != "no_echo"
    return {**probe_manifest, "schema": "scope_static_s2d8b_scrambled_echo_probe_manifest_v1", "probe_records": records}


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


def _scrambled_echo_control(rows: list[dict[str, object]]) -> dict[str, object]:
    by_method = {str(row["method"]): row for row in rows}
    real = by_method.get("rzz_echo_contrast_features", {})
    scrambled = by_method.get("scrambled_echo_control", {})
    return {
        "real_method": "rzz_echo_contrast_features",
        "scrambled_method": "scrambled_echo_control",
        "real_ari": real.get("ari"),
        "real_nmi": real.get("nmi"),
        "scrambled_ari": scrambled.get("ari"),
        "scrambled_nmi": scrambled.get("nmi"),
        "real_beats_scrambled": _beats(real, scrambled),
    }


def _key_comparison(rows: list[dict[str, object]]) -> dict[str, object]:
    by_method = {str(row["method"]): row for row in rows}
    echo = by_method.get("rzz_echo_contrast_features", {})
    probe_only = by_method.get("rzz_echo_probe_only_v3c", {})
    scrambled = by_method.get("scrambled_echo_control", {})
    direct = by_method.get("direct_Salpha", {})
    return {
        "primary": "rzz_echo_contrast_features",
        "echo_ari": echo.get("ari"),
        "echo_nmi": echo.get("nmi"),
        "delta_ari_vs_echo_probe_only": float(echo.get("ari", 0.0)) - float(probe_only.get("ari", 0.0)),
        "delta_nmi_vs_echo_probe_only": float(echo.get("nmi", 0.0)) - float(probe_only.get("nmi", 0.0)),
        "beats_scrambled": _beats(echo, scrambled),
        "beats_direct_Salpha": _beats(echo, direct),
    }


def _beats(left: dict[str, object], right: dict[str, object]) -> bool:
    return float(left.get("ari", 0.0)) > float(right.get("ari", 0.0)) and float(left.get("nmi", 0.0)) > float(right.get("nmi", 0.0))


def _empty_echo_stats(role: str) -> dict[str, object]:
    return {
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


def _record_edge_parity(record: dict[str, object]) -> str:
    qubits = _record_qubits(record)
    left = min(qubits) if qubits else 0
    return "even" if left % 2 == 0 else "odd"


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
