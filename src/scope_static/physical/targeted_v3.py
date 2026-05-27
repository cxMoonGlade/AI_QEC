from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import torch

from scope_static.identifiability import deterministic_kmeans, evaluate_partition
from scope_static.local_mechanism import split_merge_audit
from scope_static.numerics import NUMERICAL_ZERO

from .local_inverse import build_visible_location_representations


RZZ_FAMILY = ("M1", "M6", "M7", "M9")
READOUT_LABELS = ("M13", "M14", "M15", "M16")
READOUT_LABEL = READOUT_LABELS[0]


@dataclass(frozen=True)
class TargetedFeatureBundle:
    feature_spaces: dict[str, np.ndarray]
    visible_types: list[str]
    type_budgets: dict[str, int]
    manifest: dict[str, object]
    readout_before: np.ndarray
    readout_after: np.ndarray


def build_targeted_v3_features(
    records: list[dict[str, object]],
    observations: np.ndarray,
    probe_names: Iterable[str],
    *,
    num_clusters: int,
) -> TargetedFeatureBundle:
    """Build learner-visible typed features for S2D.6.

    The feature blocks use visible operation metadata, observed probe responses,
    and chain location. They do not use oracle labels.
    """

    names = [str(name) for name in probe_names]
    obs = np.asarray(observations, dtype=np.float64)
    num_qubits = int(obs.shape[2])
    visible = [_visible_type(record) for record in records]
    budgets = _typed_cluster_budgets(visible, int(num_clusters))
    base = build_visible_location_representations(records, obs, names)
    v1 = base["physical_local_inverse_probability"]
    v2 = base["physical_local_inverse_probability_v2"]
    direct = base["direct_S_alpha_assignment"]
    structural = base["structural_only_features"]
    raw = base["raw_observation_probe_summary"]

    rzz_rows = []
    readout_rows = []
    readout_before_rows = []
    readout_after_rows = []
    for idx, record in enumerate(records):
        probe_indices = _record_probe_indices(record, len(names))
        local_probe_names = [names[item] for item in probe_indices]
        rzz_rows.append(_rzz_signed_features(record, raw[idx], local_probe_names, num_qubits))
        readout = _readout_normalized_features(raw[idx])
        readout_rows.append(readout)
        if visible[idx] == "readout":
            readout_before_rows.append(raw[idx])
            readout_after_rows.append(readout)

    rzz = _finite(np.stack(rzz_rows, axis=0))
    readout = _finite(np.stack(readout_rows, axis=0))
    feature_spaces = {
        "physical_local_inverse_probability": v1,
        "physical_local_inverse_probability_v2": v2,
        "direct_Salpha": direct,
        "v3a_rzz_signed_only": _finite(np.concatenate([v1, rzz], axis=1)),
        "v3b_readout_normalization_only": _finite(np.concatenate([v1, readout], axis=1)),
        "physical_local_inverse_probability_v3_typed": _finite(np.concatenate([v1, v2, rzz, readout, structural], axis=1)),
    }
    return TargetedFeatureBundle(
        feature_spaces=feature_spaces,
        visible_types=visible,
        type_budgets=budgets,
        manifest=typed_feature_manifest(),
        readout_before=_finite(np.stack(readout_before_rows, axis=0)) if readout_before_rows else np.zeros((0, raw.shape[1])),
        readout_after=_finite(np.stack(readout_after_rows, axis=0)) if readout_after_rows else np.zeros((0, readout.shape[1])),
    )


def evaluate_targeted_v3_methods(
    records: list[dict[str, object]],
    observations: np.ndarray,
    probe_names: Iterable[str],
    hidden_labels: torch.Tensor,
    label_names: list[str],
    *,
    comparison_labels: dict[str, list[int]] | None = None,
) -> dict[str, object]:
    bundle = build_targeted_v3_features(records, observations, probe_names, num_clusters=len(label_names))
    comparison_labels = comparison_labels or {}
    method_specs = [
        ("v1_physical_local_inverse_probability", "physical_local_inverse_probability", comparison_labels.get("physical_local_inverse_probability")),
        ("v2_physical_local_inverse_probability_v2", "physical_local_inverse_probability_v2", comparison_labels.get("physical_local_inverse_probability_v2")),
        ("v3a_rzz_signed_features_only", "v3a_rzz_signed_only", None),
        ("v3b_readout_normalization_only", "v3b_readout_normalization_only", None),
        ("v3c_physical_local_inverse_probability_v3_typed", "physical_local_inverse_probability_v3_typed", None),
        ("direct_Salpha", "direct_Salpha", comparison_labels.get("direct_S_alpha_assignment")),
    ]
    rows = []
    labels_by_method: dict[str, list[int]] = {}
    for method, feature_key, precomputed in method_specs:
        features = bundle.feature_spaces[feature_key]
        if precomputed is None:
            labels = typed_cluster_labels(features, bundle.visible_types, bundle.type_budgets)
        else:
            labels = [int(value) for value in precomputed]
        labels_by_method[method] = labels
        rows.append(_method_record(method, feature_key, features, labels, hidden_labels, len(label_names)))

    if "oracle_fingerprint_upper_bound" in comparison_labels:
        labels = [int(value) for value in comparison_labels["oracle_fingerprint_upper_bound"]]
        labels_by_method["oracle_fingerprint_upper_bound"] = labels
        rows.append(
            {
                "method": "oracle_fingerprint_upper_bound",
                "feature_space": "oracle_PTM_probe_fingerprint",
                "feature_role": "oracle_only_upper_bound",
                "uses_oracle_channel_parameters": True,
                "uses_oracle_labels": False,
                **_partition_record(labels, hidden_labels, len(label_names)),
            }
        )

    return {
        "feature_manifest": bundle.manifest,
        "visible_type_counts": _counts(bundle.visible_types),
        "type_budgets": bundle.type_budgets,
        "methods": rows,
        "labels_by_method": labels_by_method,
        "rzz_family_confusion_audit": rzz_family_confusion_audit(labels_by_method, hidden_labels, label_names),
        "readout_split_audit": readout_split_audit(
            labels_by_method,
            hidden_labels,
            label_names,
            before=bundle.readout_before,
            after=bundle.readout_after,
        ),
        "best_method": max(rows, key=lambda row: (float(row["ari"]), float(row["nmi"]))),
        "key_comparison": _key_comparison(rows),
    }


def typed_cluster_labels(features: np.ndarray, visible_types: list[str], budgets: dict[str, int]) -> list[int]:
    x = np.asarray(features, dtype=np.float64)
    labels = [-1 for _ in visible_types]
    next_label = 0
    for type_name in ("readout", "rzz_edge", "single_qubit", "other"):
        indices = [idx for idx, current in enumerate(visible_types) if current == type_name]
        if not indices:
            continue
        budget = max(1, int(budgets.get(type_name, 1)))
        if budget == 1 or len(indices) == 1:
            for idx in indices:
                labels[idx] = next_label
            next_label += 1
            continue
        local_labels = deterministic_kmeans(torch.as_tensor(x[indices], dtype=torch.float64), budget).labels.tolist()
        for idx, local_label in zip(indices, local_labels):
            labels[idx] = next_label + int(local_label)
        next_label += budget
    if any(label < 0 for label in labels):
        fallback = deterministic_kmeans(torch.as_tensor(x, dtype=torch.float64), max(1, sum(budgets.values()))).labels.tolist()
        labels = [int(fallback[idx]) if label < 0 else int(label) for idx, label in enumerate(labels)]
    return [int(label) for label in labels]


def rzz_family_confusion_audit(
    labels_by_method: dict[str, list[int]],
    hidden_labels: torch.Tensor,
    label_names: list[str],
) -> dict[str, object]:
    out = {}
    true = [int(value) for value in hidden_labels.tolist()]
    family_indices = [idx for idx, name in enumerate(label_names) if name in RZZ_FAMILY]
    for method, labels in labels_by_method.items():
        out[method] = _family_audit(labels, true, label_names, family_indices)
    return out


def readout_split_audit(
    labels_by_method: dict[str, list[int]],
    hidden_labels: torch.Tensor,
    label_names: list[str],
    *,
    before: np.ndarray,
    after: np.ndarray,
) -> dict[str, object]:
    readout_indices = [idx for idx, name in enumerate(label_names) if name in READOUT_LABELS]
    if not readout_indices:
        return {"readout_label_present": False}
    true = np.asarray(hidden_labels.tolist(), dtype=np.int64)
    readout_mask = np.isin(true, np.asarray(readout_indices, dtype=np.int64))
    out = {
        "readout_label_present": True,
        "readout_labels_present": [label_names[idx] for idx in readout_indices],
        "M5_within_class_variance_before_normalization": float(np.mean(np.var(before, axis=0))) if before.size else 0.0,
        "M5_within_class_variance_after_normalization": float(np.mean(np.var(after, axis=0))) if after.size else 0.0,
        "readout_within_class_variance_before_normalization": float(np.mean(np.var(before, axis=0))) if before.size else 0.0,
        "readout_within_class_variance_after_normalization": float(np.mean(np.var(after, axis=0))) if after.size else 0.0,
        "methods": {},
    }
    for method, labels in labels_by_method.items():
        pred = np.asarray(labels, dtype=np.int64)
        clusters = sorted({int(value) for value in pred[readout_mask].tolist()})
        out["methods"][method] = {
            "M5_split_count": len(clusters),
            "M5_clusters": clusters,
            "M5_split_fixed": len(clusters) <= len(readout_indices),
            "readout_split_count": len(clusters),
            "readout_clusters": clusters,
            "readout_split_within_declared_taxonomy": len(clusters) <= len(readout_indices),
        }
    return out


def typed_feature_manifest() -> dict[str, object]:
    return {
        "schema": "scope_static_s2d6_typed_feature_manifest_v1",
        "method": "physical_local_inverse_probability_v3_typed",
        "uses_oracle_labels": False,
        "visible_types": ["rzz_edge", "single_qubit", "readout", "other"],
        "type_budget_rule": {
            "readout": "1 cluster when visible readout locations exist",
            "rzz_edge": "1 cluster for K<9, 3 clusters for 9<=K<11, 4 clusters for K>=11",
            "single_qubit": "remaining clusters after readout/rzz allocation",
            "other": "fallback remaining visible-type budget",
        },
        "feature_blocks": {
            "RZZ locations": [
                "signed probe differences x_measure-z_basis, y_measure-z_basis, x_measure-y_measure",
                "basis response ratios x/z, y/z, x/y",
                "Type2-like diagonal/equal-response preservation contrast",
                "Type3-like off-diagonal/mixing contrast proxy",
                "Type4-like small mixing proxy",
                "signed asymmetry, response slope, response variance across probes",
                "edge-local chain position and neighboring RZZ count",
            ],
            "readout locations": [
                "normalized readout response shape",
                "downweighted readout strength",
                "shape entropy and variance",
            ],
            "single_qubit locations": ["current local inverse probability features"],
        },
        "feature_roles": {
            "v3a_rzz_signed_features_only": "learner_visible",
            "v3b_readout_normalization_only": "learner_visible",
            "physical_local_inverse_probability_v3_typed": "learner_visible",
            "oracle_fingerprint_upper_bound": "oracle_only_upper_bound",
        },
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


def _key_comparison(rows: list[dict[str, object]]) -> dict[str, object]:
    by_method = {str(row["method"]): row for row in rows}
    v3 = by_method.get("v3c_physical_local_inverse_probability_v3_typed", {})
    baselines = [by_method[name] for name in ("v1_physical_local_inverse_probability", "v2_physical_local_inverse_probability_v2") if name in by_method]
    best_baseline = max(baselines, key=lambda row: (float(row["ari"]), float(row["nmi"]))) if baselines else {}
    return {
        "primary": "v3c_vs_v1_v2",
        "v3c_ari": v3.get("ari"),
        "v3c_nmi": v3.get("nmi"),
        "best_v1_v2_method": best_baseline.get("method"),
        "best_v1_v2_ari": best_baseline.get("ari"),
        "best_v1_v2_nmi": best_baseline.get("nmi"),
        "v3c_delta_ari_vs_best_v1_v2": float(v3.get("ari", 0.0)) - float(best_baseline.get("ari", 0.0)) if best_baseline else None,
        "v3c_delta_nmi_vs_best_v1_v2": float(v3.get("nmi", 0.0)) - float(best_baseline.get("nmi", 0.0)) if best_baseline else None,
    }


def _family_audit(labels: list[int], true: list[int], label_names: list[str], family_indices: list[int]) -> dict[str, object]:
    pred = np.asarray(labels, dtype=np.int64)
    actual = np.asarray(true, dtype=np.int64)
    merges = []
    splits = []
    for cluster in sorted({int(value) for value in pred.tolist()}):
        idx = pred == cluster
        present = {
            label_names[label_idx]: int(np.sum(actual[idx] == label_idx))
            for label_idx in family_indices
            if int(np.sum(actual[idx] == label_idx)) > 0
        }
        if len(present) > 1:
            merges.append({"cluster": int(cluster), "mechanisms": present})
    for label_idx in family_indices:
        idx = actual == label_idx
        clusters = sorted({int(value) for value in pred[idx].tolist()})
        if len(clusters) > 1:
            splits.append({"mechanism": label_names[label_idx], "clusters": clusters})
    return {
        "family": [label_names[idx] for idx in family_indices],
        "merge_count": len(merges),
        "split_count": len(splits),
        "merge_clusters": merges,
        "split_mechanisms": splits,
        "distinguishable": len(merges) == 0,
    }


def _rzz_signed_features(record: dict[str, object], local_response: np.ndarray, probe_names: list[str], num_qubits: int) -> np.ndarray:
    probes = _probe_vectors(local_response, probe_names)
    z = _probe_value(probes, "z_basis")
    x = _probe_value(probes, "x_measure", fallback=z)
    y = _probe_value(probes, "y_measure", fallback=z)
    eps = NUMERICAL_ZERO
    qubits = _record_qubits(record)
    left = min(qubits) if qubits else 0
    right = max(qubits) if qubits else left
    max_edge = max(1, int(num_qubits) - 2)
    neighbor_count = 1 if left <= 0 or right >= int(num_qubits) - 1 else 2
    equal_z = _probe_stat(probes, "z_basis", 8)
    equal_x = _probe_stat(probes, "x_measure", 8, fallback=equal_z)
    equal_y = _probe_stat(probes, "y_measure", 8, fallback=equal_z)
    parity_z = _probe_stat(probes, "z_basis", 5)
    parity_x = _probe_stat(probes, "x_measure", 5, fallback=parity_z)
    parity_y = _probe_stat(probes, "y_measure", 5, fallback=parity_z)
    values = np.asarray([z, x, y], dtype=np.float64)
    return np.array(
        [
            float(x - z),
            float(y - z),
            float(x - y),
            float(x / (abs(z) + eps)),
            float(y / (abs(z) + eps)),
            float(x / (abs(y) + eps)),
            float(equal_x - equal_z),
            float(equal_y - equal_z),
            float(abs(parity_x - parity_z) + abs(parity_y - parity_z)),
            float(np.std(local_response) * np.mean(np.abs(local_response - np.mean(local_response)))),
            float((x - z) - (y - z)),
            float(np.polyfit(np.arange(values.size, dtype=np.float64), values, deg=1)[0]),
            float(np.var(values)),
            float(left / max_edge),
            float((left + right) / max(1.0, 2.0 * (int(num_qubits) - 1))),
            float(neighbor_count / 2.0),
            float(1.0 if left <= 0 or right >= int(num_qubits) - 1 else 0.0),
        ],
        dtype=np.float64,
    )


def _readout_normalized_features(local_response: np.ndarray) -> np.ndarray:
    values = _finite(np.asarray(local_response, dtype=np.float64))
    centered = values - float(np.mean(values))
    norm = float(np.linalg.norm(centered))
    shape = centered / max(norm, NUMERICAL_ZERO)
    strength = float(np.linalg.norm(values))
    entropy = _entropy(values)
    return _finite(
        np.concatenate(
            [
                shape,
                np.array(
                    [
                        0.05 * strength,
                        float(np.std(shape)),
                        float(np.max(shape) - np.min(shape)) if shape.size else 0.0,
                        entropy,
                    ],
                    dtype=np.float64,
                ),
            ]
        )
    )


def _typed_cluster_budgets(visible_types: list[str], num_clusters: int) -> dict[str, int]:
    counts = _counts(visible_types)
    readout = min(4, int(counts.get("readout", 0))) if counts.get("readout", 0) else 0
    if counts.get("rzz_edge", 0):
        if int(num_clusters) >= 11:
            rzz = min(4, int(counts["rzz_edge"]))
        elif int(num_clusters) >= 9:
            rzz = min(3, int(counts["rzz_edge"]))
        else:
            rzz = 1
    else:
        rzz = 0
    remaining = max(0, int(num_clusters) - readout - rzz)
    single = min(max(1 if counts.get("single_qubit", 0) else 0, remaining), int(counts.get("single_qubit", 0))) if remaining else 0
    other = max(0, int(num_clusters) - readout - rzz - single) if counts.get("other", 0) else 0
    if counts.get("single_qubit", 0) and readout + rzz + single + other < int(num_clusters):
        single = min(int(counts["single_qubit"]), single + int(num_clusters) - readout - rzz - single - other)
    return {"readout": readout, "rzz_edge": rzz, "single_qubit": single, "other": other}


def _visible_type(record: dict[str, object]) -> str:
    instruction = str(record.get("instruction", "unknown"))
    if instruction == "rzz":
        return "rzz_edge"
    if instruction == "measure":
        return "readout"
    if int(record.get("num_qubits", 1)) == 1:
        return "single_qubit"
    return "other"


def _probe_vectors(local_response: np.ndarray, probe_names: list[str]) -> dict[str, np.ndarray]:
    width = 11
    out = {}
    for idx, name in enumerate(probe_names):
        start = idx * width
        stop = start + width
        if start >= len(local_response):
            continue
        out[_probe_base_name(name)] = _finite(local_response[start:stop])
    return out


def _probe_value(probes: dict[str, np.ndarray], name: str, *, fallback: float = 0.0) -> float:
    if name not in probes:
        return float(fallback)
    return float(np.mean(probes[name]))


def _probe_stat(probes: dict[str, np.ndarray], name: str, index: int, *, fallback: float = 0.0) -> float:
    if name not in probes or int(index) >= len(probes[name]):
        return float(fallback)
    return float(probes[name][int(index)])


def _probe_base_name(name: str) -> str:
    text = str(name)
    return text.split(":", 1)[1] if ":" in text else text


def _record_probe_indices(record: dict[str, object], num_probes: int) -> list[int]:
    raw = record.get("probe_indices", [])
    if isinstance(raw, list) and raw:
        return [int(value) for value in raw]
    return list(range(int(num_probes)))


def _record_qubits(record: dict[str, object]) -> list[int]:
    raw = record.get("qubits", [])
    return [int(value) for value in raw] if isinstance(raw, list) and raw else [0]


def _counts(values: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[str(value)] = counts.get(str(value), 0) + 1
    return counts


def _entropy(values: np.ndarray) -> float:
    probs = np.clip(_finite(values), NUMERICAL_ZERO, 1.0 - NUMERICAL_ZERO)
    entropy = -(probs * np.log(probs) + (1.0 - probs) * np.log(1.0 - probs))
    return float(np.mean(entropy))


def _finite(values: np.ndarray) -> np.ndarray:
    return np.nan_to_num(np.asarray(values, dtype=np.float64), nan=NUMERICAL_ZERO, posinf=NUMERICAL_ZERO, neginf=-NUMERICAL_ZERO)
