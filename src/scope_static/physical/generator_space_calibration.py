from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from scope_static.numerics import NUMERICAL_ZERO

from .rzz_observability_ceiling import FeatureBlock, evaluate_ceiling_feature_blocks
from .targeted_v3 import RZZ_FAMILY


GENERATOR_CORE = (
    "h_XX",
    "h_YY",
    "h_ZZ",
    "gamma_XX",
    "gamma_YY",
    "gamma_ZZ",
    "relaxation_pair",
    "affine_ZI",
    "affine_IZ",
    "affine_ZZ",
    "nonunital_norm_proxy",
)
HAMILTONIAN = ("h_XX", "h_YY", "h_ZZ")
STOCHASTIC = ("gamma_XX", "gamma_YY", "gamma_ZZ")
AFFINE = ("relaxation_pair", "affine_ZI", "affine_IZ", "affine_ZZ", "nonunital_norm_proxy")
VARIANT_ORDER = (
    "raw_generator_coordinates",
    "edge_residualized_coordinates",
    "circuit_residualized_coordinates",
    "edge_circuit_residualized_coordinates",
    "ideal_schedule_residualized_coordinates",
)
FORBIDDEN_FEATURE_TOKENS = ("oracle_label", "mechanism_id", "exact_ptm", "teacher_channel", "oracle_fingerprint")


@dataclass(frozen=True)
class GeneratorCalibrationBundle:
    effective_rank_metrics: dict[str, object]
    generator_coordinate_statistics: dict[str, object]
    per_mechanism_generator_signatures: dict[str, object]
    pairwise_generator_margins: dict[str, object]
    circuit_residualization_audit: dict[str, object]
    edge_residualization_audit: dict[str, object]
    blockwise_decision_metrics: dict[str, object]
    mahalanobis_prototype_metrics: dict[str, object]
    whitening_ablation_metrics: dict[str, object]
    grouped_fold_predictions: dict[str, object]
    feature_block_results: dict[str, object]
    confusion_matrix_by_stage: dict[str, object]
    controls: dict[str, object]
    leakage_guardrail_audit: dict[str, object]
    decision: str


def build_generator_space_calibration(
    run_record: dict[str, object],
    *,
    seed: int = 0,
    permutation_repeats: int = 128,
) -> GeneratorCalibrationBundle:
    rows = _extract_rows(run_record)
    feature_names = _core_feature_names(rows["feature_names"])
    x = _select_features(rows["features"], rows["feature_names"], feature_names)
    scrambled = _select_features(rows["scrambled_features"], rows["feature_names"], feature_names)
    labels = rows["labels"]
    groups = rows["groups"]
    edge_ids = rows["edge_ids"]
    schedule = rows["schedule_features"]
    variants = {
        "raw_generator_coordinates": x,
        "edge_residualized_coordinates": residualize_by_group(x, edge_ids),
        "circuit_residualized_coordinates": residualize_by_group(x, groups),
        "edge_circuit_residualized_coordinates": residualize_by_design(x, _one_hot_pairs(edge_ids, groups)),
        "ideal_schedule_residualized_coordinates": residualize_by_design(x, schedule),
    }
    scrambled_variants = {
        "raw_generator_coordinates": scrambled,
        "edge_residualized_coordinates": residualize_by_group(scrambled, edge_ids),
        "circuit_residualized_coordinates": residualize_by_group(scrambled, groups),
        "edge_circuit_residualized_coordinates": residualize_by_design(scrambled, _one_hot_pairs(edge_ids, groups)),
        "ideal_schedule_residualized_coordinates": residualize_by_design(scrambled, schedule),
    }
    rzz_labels_set = set(RZZ_FAMILY)
    rzz_mask = np.asarray([label in rzz_labels_set for label in labels], dtype=bool)
    rzz_variants = {name: value[rzz_mask] for name, value in variants.items()}
    rzz_scrambled_variants = {name: value[rzz_mask] for name, value in scrambled_variants.items()}
    rzz_labels = [label for label, keep in zip(labels, rzz_mask.tolist()) if keep]
    rzz_groups = [group for group, keep in zip(groups, rzz_mask.tolist()) if keep]
    jacobian = _response_jacobian(run_record)
    effective = effective_rank_metrics(jacobian, variants, feature_names, labels)
    stats = generator_coordinate_statistics(variants, feature_names, labels, groups, edge_ids)
    signatures = per_mechanism_generator_signatures(variants, feature_names, labels)
    margins = pairwise_generator_margins(variants, feature_names, labels)
    circuit_audit = residualization_audit(x, variants["circuit_residualized_coordinates"], groups, "circuit_id")
    edge_audit = residualization_audit(x, variants["edge_residualized_coordinates"], edge_ids, "edge_id")
    blockwise = blockwise_decision_metrics(rzz_variants, feature_names, rzz_labels, rzz_groups)
    mahalanobis = mahalanobis_prototype_metrics(rzz_variants, rzz_scrambled_variants, feature_names, rzz_labels, rzz_groups)
    whitening = whitening_ablation_metrics(
        rzz_variants,
        rzz_scrambled_variants,
        feature_names,
        rzz_labels,
        rzz_groups,
        seed=seed,
        permutation_repeats=permutation_repeats,
    )
    leakage = leakage_guardrail_audit(feature_names)
    decision = run_decision(whitening, blockwise, signatures)
    return GeneratorCalibrationBundle(
        effective_rank_metrics=effective,
        generator_coordinate_statistics=stats,
        per_mechanism_generator_signatures=signatures,
        pairwise_generator_margins=margins,
        circuit_residualization_audit=circuit_audit,
        edge_residualization_audit=edge_audit,
        blockwise_decision_metrics=blockwise,
        mahalanobis_prototype_metrics=mahalanobis,
        whitening_ablation_metrics=whitening,
        grouped_fold_predictions=whitening["grouped_fold_predictions"],
        feature_block_results=whitening["feature_block_results"],
        confusion_matrix_by_stage=blockwise["confusion_matrix_by_stage"],
        controls=whitening["controls"],
        leakage_guardrail_audit=leakage,
        decision=decision,
    )


def effective_rank_metrics(
    jacobian: np.ndarray,
    variants: dict[str, np.ndarray],
    feature_names: list[str],
    labels: list[str],
) -> dict[str, object]:
    out = {
        "schema": "scope_static_s2d10_effective_rank_metrics_v1",
        "response_jacobian": _matrix_rank_summary(jacobian),
        "feature_spaces": {},
        "pairwise_generator_margins": pairwise_generator_margins(variants, feature_names, labels),
    }
    out["response_jacobian"]["column_angles"] = _column_angles(np.asarray(jacobian, dtype=np.float64), [name for name in GENERATOR_CORE if name in feature_names][: np.asarray(jacobian).shape[1]])
    for name, features in variants.items():
        centered = np.asarray(features, dtype=np.float64) - np.mean(features, axis=0, keepdims=True)
        covariance = centered.T @ centered / max(1, centered.shape[0] - 1)
        out["feature_spaces"][name] = _matrix_rank_summary(covariance)
        out["feature_spaces"][name]["column_angles"] = _column_angles(centered, feature_names)
    return out


def generator_coordinate_statistics(
    variants: dict[str, np.ndarray],
    feature_names: list[str],
    labels: list[str],
    groups: list[int],
    edge_ids: list[str],
) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d10_generator_coordinate_statistics_v1",
        "variants": {
            variant: {
                "feature_names": list(feature_names),
                "coordinates": {
                    coord: _coordinate_stats(np.asarray(features, dtype=np.float64)[:, idx], labels, groups, edge_ids)
                    for idx, coord in enumerate(feature_names)
                },
            }
            for variant, features in variants.items()
        },
    }


def per_mechanism_generator_signatures(
    variants: dict[str, np.ndarray],
    feature_names: list[str],
    labels: list[str],
) -> dict[str, object]:
    out = {"schema": "scope_static_s2d10_per_mechanism_generator_signatures_v1", "variants": {}}
    for variant, features in variants.items():
        x = np.asarray(features, dtype=np.float64)
        by_label = {}
        for label in sorted(set(labels)):
            mask = np.asarray([item == label for item in labels], dtype=bool)
            if not np.any(mask):
                continue
            mean_abs = {name: float(np.mean(np.abs(x[mask, idx]))) for idx, name in enumerate(feature_names)}
            by_label[label] = {
                "num_rows": int(np.sum(mask)),
                "mean": {name: float(np.mean(x[mask, idx])) for idx, name in enumerate(feature_names)},
                "mean_abs": mean_abs,
                "dominant_block": _dominant_block(mean_abs),
                "expected_block": _expected_block(label),
                "expected_block_matched": _dominant_block(mean_abs) == _expected_block(label),
            }
        out["variants"][variant] = by_label
    return out


def pairwise_generator_margins(
    variants: dict[str, np.ndarray],
    feature_names: list[str],
    labels: list[str],
) -> dict[str, object]:
    pairs = ("M1/M6", "M1/M7", "M1/M9", "M6/M7", "M6/M9", "M7/M9")
    out = {"schema": "scope_static_s2d10_pairwise_generator_margins_v1", "variants": {}}
    for variant, features in variants.items():
        x = np.asarray(features, dtype=np.float64)
        variant_rows = {}
        for pair in pairs:
            left, right = pair.split("/")
            left_mask = np.asarray([label == left for label in labels], dtype=bool)
            right_mask = np.asarray([label == right for label in labels], dtype=bool)
            if not np.any(left_mask) or not np.any(right_mask):
                variant_rows[pair] = {"available": False}
                continue
            left_center = np.mean(x[left_mask], axis=0)
            right_center = np.mean(x[right_mask], axis=0)
            pooled = _pooled_std(x[left_mask], x[right_mask])
            diff = left_center - right_center
            z = diff / np.maximum(pooled, NUMERICAL_ZERO)
            variant_rows[pair] = {
                "available": True,
                "euclidean_margin": float(np.linalg.norm(diff)),
                "z_margin": float(np.linalg.norm(z)),
                "top_coordinate": str(feature_names[int(np.argmax(np.abs(z)))]),
                "coordinate_deltas": {name: float(diff[idx]) for idx, name in enumerate(feature_names)},
                "coordinate_z_margins": {name: float(z[idx]) for idx, name in enumerate(feature_names)},
            }
        out["variants"][variant] = variant_rows
    return out


def residualization_audit(raw: np.ndarray, residual: np.ndarray, groups: list[object], group_key: str) -> dict[str, object]:
    raw = np.asarray(raw, dtype=np.float64)
    residual = np.asarray(residual, dtype=np.float64)
    return {
        "schema": "scope_static_s2d10_residualization_audit_v1",
        "group_key": group_key,
        "num_groups": int(len(set(groups))),
        "raw_variance": float(np.mean(np.var(raw, axis=0))) if raw.size else 0.0,
        "residual_variance": float(np.mean(np.var(residual, axis=0))) if residual.size else 0.0,
        "variance_removed_fraction": float(1.0 - (np.mean(np.var(residual, axis=0)) / max(np.mean(np.var(raw, axis=0)), NUMERICAL_ZERO))) if raw.size else 0.0,
        "group_mean_norm_before": _group_mean_norm(raw, groups),
        "group_mean_norm_after": _group_mean_norm(residual, groups),
    }


def blockwise_decision_metrics(
    variants: dict[str, np.ndarray],
    feature_names: list[str],
    labels: list[str],
    groups: list[int],
) -> dict[str, object]:
    out = {
        "schema": "scope_static_s2d10_blockwise_decision_metrics_v1",
        "stage_definitions": {
            "stage1": "Hamiltonian-like vs stochastic-like vs affine/non-unital-like",
            "stage2": "inside Hamiltonian: XX/YY vs ZZ",
            "stage3": "inside stochastic: Pauli-like subtype",
            "stage4": "relaxation/correlated relaxation subtype",
        },
        "variants": {},
        "confusion_matrix_by_stage": {},
    }
    for variant, features in variants.items():
        x = np.asarray(features, dtype=np.float64)
        preds = [_blockwise_predict(row, feature_names) for row in x]
        stage_metrics = _blockwise_stage_metrics(labels, preds)
        out["variants"][variant] = stage_metrics
        out["confusion_matrix_by_stage"][variant] = stage_metrics["confusion_matrix_by_stage"]
    return out


def mahalanobis_prototype_metrics(
    variants: dict[str, np.ndarray],
    scrambled_variants: dict[str, np.ndarray],
    feature_names: list[str],
    labels: list[str],
    groups: list[int],
) -> dict[str, object]:
    out = {"schema": "scope_static_s2d10_mahalanobis_prototype_metrics_v1", "variants": {}}
    for variant, features in variants.items():
        real = grouped_mahalanobis_prototype(features, labels, groups)
        scrambled = grouped_mahalanobis_prototype(scrambled_variants[variant], labels, groups)
        out["variants"][variant] = {
            "real": real,
            "scrambled": scrambled,
            "real_minus_scrambled_balanced_accuracy": float(real["balanced_accuracy"] - scrambled["balanced_accuracy"]),
            "feature_names": feature_names,
        }
    return out


def whitening_ablation_metrics(
    variants: dict[str, np.ndarray],
    scrambled_variants: dict[str, np.ndarray],
    feature_names: list[str],
    labels: list[str],
    groups: list[int],
    *,
    seed: int,
    permutation_repeats: int,
) -> dict[str, object]:
    feature_blocks: dict[str, FeatureBlock] = {}
    for variant, features in variants.items():
        feature_blocks[variant] = FeatureBlock(variant, features, feature_names, ["s2d9_generator_coordinates"], primary=variant == "circuit_residualized_coordinates")
        feature_blocks[f"zscore_{variant}"] = FeatureBlock(
            f"zscore_{variant}",
            zscore_features(features),
            [f"zscore_{name}" for name in feature_names],
            ["s2d9_generator_coordinates_zscore"],
            explanatory=True,
        )
        feature_blocks[f"whitened_{variant}"] = FeatureBlock(
            f"whitened_{variant}",
            whiten_features(features),
            [f"whitened_{name}" for name in feature_names],
            ["s2d9_generator_coordinates_whitened"],
            explanatory=True,
        )
    feature_blocks["scrambled_circuit_residualized_coordinates"] = FeatureBlock(
        "scrambled_circuit_residualized_coordinates",
        scrambled_variants["circuit_residualized_coordinates"],
        [f"scrambled_{name}" for name in feature_names],
        ["s2d9_scrambled_generator_coordinates"],
        control=True,
    )
    if len(set(labels)) < 2 or len(set(groups)) < 2:
        return _skipped_whitening(feature_blocks)
    ceiling = evaluate_ceiling_feature_blocks(
        feature_blocks,
        labels,
        groups,
        primary_block="circuit_residualized_coordinates",
        scrambled_control_block="scrambled_circuit_residualized_coordinates",
        permutation_repeats=int(permutation_repeats),
        seed=int(seed),
    )
    return {
        "schema": "scope_static_s2d10_whitening_ablation_metrics_v1",
        "primary_block": "circuit_residualized_coordinates",
        "feature_block_results": ceiling["feature_block_results"],
        "grouped_fold_predictions": ceiling["grouped_fold_predictions"],
        "controls": ceiling["controls"],
        "run_success": ceiling["run_success"],
    }


def grouped_mahalanobis_prototype(features: np.ndarray, labels: list[str], groups: list[int], *, shrinkage: float = 0.1) -> dict[str, object]:
    x = np.asarray(features, dtype=np.float64)
    y = np.asarray(labels, dtype=object)
    g = np.asarray(groups, dtype=np.int64)
    class_names = [name for name in RZZ_FAMILY if name in set(labels)]
    if len(class_names) < 2 or len(set(groups)) < 2:
        return {"available": False, "balanced_accuracy": 0.0, "macro_F1": 0.0, "confusion_matrix": []}
    true_all = []
    pred_all = []
    for test_group in sorted(set(g.tolist())):
        train = g != int(test_group)
        test = g == int(test_group)
        x_train, x_test = _standardize_train_test(x[train], x[test])
        centers = {}
        for label in class_names:
            mask = y[train] == label
            if np.any(mask):
                centers[label] = np.mean(x_train[mask], axis=0)
        cov = np.cov(x_train.T) if x_train.shape[0] > 1 else np.eye(x_train.shape[1])
        cov = np.asarray(cov, dtype=np.float64)
        diag = np.diag(np.diag(cov))
        cov = (1.0 - float(shrinkage)) * cov + float(shrinkage) * diag + 1e-6 * np.eye(cov.shape[0])
        inv_cov = np.linalg.pinv(cov)
        for row, true in zip(x_test, y[test]):
            distances = {label: float((row - center).T @ inv_cov @ (row - center)) for label, center in centers.items()}
            pred = min(distances, key=distances.get) if distances else class_names[0]
            true_all.append(str(true))
            pred_all.append(str(pred))
    return _label_metrics(true_all, pred_all, class_names)


def run_decision(
    whitening: dict[str, object],
    blockwise: dict[str, object],
    signatures: dict[str, object],
) -> str:
    success = bool(whitening.get("run_success", {}).get("passed", False))
    stage1 = bool(blockwise.get("variants", {}).get("circuit_residualized_coordinates", {}).get("stage1_block_accuracy", 0.0) >= 0.80)
    sig = _rzz_signature_blocks_match(signatures)
    if success and stage1 and sig:
        return "success"
    if stage1 or success:
        return "partial_blockwise_or_geometry"
    return "failure"


def zscore_features(features: np.ndarray) -> np.ndarray:
    x = np.asarray(features, dtype=np.float64)
    return _finite((x - np.mean(x, axis=0, keepdims=True)) / np.maximum(np.std(x, axis=0, keepdims=True), NUMERICAL_ZERO))


def whiten_features(features: np.ndarray, *, ridge: float = 1e-6) -> np.ndarray:
    x = np.asarray(features, dtype=np.float64)
    centered = x - np.mean(x, axis=0, keepdims=True)
    cov = centered.T @ centered / max(1, centered.shape[0] - 1)
    values, vectors = np.linalg.eigh(cov + float(ridge) * np.eye(cov.shape[0]))
    return _finite(centered @ vectors @ np.diag(1.0 / np.sqrt(np.maximum(values, float(ridge)))))


def residualize_by_group(features: np.ndarray, groups: list[object]) -> np.ndarray:
    x = np.asarray(features, dtype=np.float64)
    out = np.array(x, copy=True)
    for group in sorted(set(groups), key=str):
        mask = np.asarray([value == group for value in groups], dtype=bool)
        out[mask] = out[mask] - np.mean(out[mask], axis=0, keepdims=True)
    return _finite(out)


def residualize_by_design(features: np.ndarray, design: np.ndarray, *, ridge: float = 1e-6) -> np.ndarray:
    x = np.asarray(features, dtype=np.float64)
    d = np.asarray(design, dtype=np.float64)
    if d.size == 0:
        return x
    d = np.concatenate([np.ones((d.shape[0], 1), dtype=np.float64), d], axis=1)
    gram = d.T @ d
    penalty = float(ridge) * np.eye(gram.shape[0], dtype=np.float64)
    penalty[0, 0] = 0.0
    coef = np.linalg.pinv(gram + penalty) @ d.T @ x
    return _finite(x - d @ coef)


def leakage_guardrail_audit(feature_names: list[str]) -> dict[str, object]:
    lower = [name.lower() for name in feature_names]
    checks = {
        "oracle_label_not_in_feature_columns": not any("oracle_label" in name for name in lower),
        "mechanism_id_not_in_feature_columns": not any("mechanism_id" in name for name in lower),
        "ptm_columns_absent": not any("ptm" in name for name in lower),
        "teacher_channel_columns_absent": not any("teacher_channel" in name for name in lower),
        "oracle_fingerprint_columns_absent": not any("oracle_fingerprint" in name for name in lower),
        "no_new_teacher_sampling": True,
    }
    return {
        "schema": "scope_static_s2d10_leakage_guardrail_audit_v1",
        "passed": all(bool(value) for value in checks.values()),
        "checks": checks,
        "forbidden_feature_tokens": list(FORBIDDEN_FEATURE_TOKENS),
    }


def _extract_rows(run_record: dict[str, object]) -> dict[str, object]:
    estimates = run_record["generator_coordinate_estimates"]
    feature_names = [str(name) for name in estimates["coordinate_names"]]
    ptm_records = {
        int(item.get("location_id", idx)): item
        for idx, item in enumerate(run_record.get("ptm_block_reconstruction", {}).get("records", []))
        if isinstance(item, dict)
    }
    rows = []
    labels = []
    groups = []
    edge_ids = []
    schedule_features = []
    for record in estimates["records"]:
        location_id = int(record.get("location_id", len(rows)))
        labels.append(str(record.get("oracle_label_evaluator_only", "")))
        groups.append(int(record.get("circuit_id", 0)))
        features = [float(record["features"].get(name, 0.0)) for name in feature_names]
        scrambled = [float(record["scrambled_features"].get(name, 0.0)) for name in feature_names]
        ptm = ptm_records.get(location_id, {})
        qubits = [int(value) for value in ptm.get("qubits", [])] if isinstance(ptm.get("qubits", []), list) else []
        left = min(qubits) if len(qubits) >= 2 else -1
        right = max(qubits) if len(qubits) >= 2 else -1
        parity = "even" if left >= 0 and left % 2 == 0 else "odd" if left >= 0 else "none"
        edge_ids.append(f"{left}-{right}")
        schedule_features.append([float(left), float(right), float(left % 2 == 0 if left >= 0 else 0.0), float(groups[-1])])
        rows.append((features, scrambled))
    return {
        "feature_names": feature_names,
        "features": np.asarray([row[0] for row in rows], dtype=np.float64),
        "scrambled_features": np.asarray([row[1] for row in rows], dtype=np.float64),
        "labels": labels,
        "groups": groups,
        "edge_ids": edge_ids,
        "schedule_features": np.asarray(schedule_features, dtype=np.float64),
    }


def _core_feature_names(feature_names: list[str]) -> list[str]:
    return [name for name in feature_names if name in set(GENERATOR_CORE)]


def _select_features(features: np.ndarray, names: list[str], selected: list[str]) -> np.ndarray:
    indices = [names.index(name) for name in selected]
    return _finite(np.asarray(features, dtype=np.float64)[:, indices])


def _response_jacobian(run_record: dict[str, object]) -> np.ndarray:
    matrix = run_record.get("response_jacobian_json", {}).get("matrix", [])
    return _finite(np.asarray(matrix, dtype=np.float64))


def _matrix_rank_summary(matrix: np.ndarray) -> dict[str, object]:
    values = np.linalg.svd(np.asarray(matrix, dtype=np.float64), compute_uv=False)
    stable_rank = float(np.sum(values * values) / max(values[0] * values[0], NUMERICAL_ZERO)) if values.size else 0.0
    return {
        "singular_values": [float(value) for value in values.tolist()],
        "rank": int(np.linalg.matrix_rank(matrix, tol=NUMERICAL_ZERO)),
        "condition_number": float(values[0] / values[-1]) if values.size and values[-1] > NUMERICAL_ZERO else float("inf"),
        "stable_rank": stable_rank,
        "minimum_singular_value": float(values[-1]) if values.size else 0.0,
    }


def _column_angles(matrix: np.ndarray, names: list[str]) -> dict[str, object]:
    x = np.asarray(matrix, dtype=np.float64)
    if x.ndim != 2:
        return {}
    out = {}
    count = min(x.shape[1], len(names))
    for i in range(count):
        for j in range(i + 1, count):
            a = x[:, i]
            b = x[:, j]
            denom = float(np.linalg.norm(a) * np.linalg.norm(b))
            cosine = NUMERICAL_ZERO if denom <= NUMERICAL_ZERO else float(np.dot(a, b) / denom)
            out[f"{names[i]}/{names[j]}"] = {
                "cosine": cosine,
                "abs_cosine": abs(cosine),
                "angle_degrees": float(np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))),
            }
    return out


def _coordinate_stats(values: np.ndarray, labels: list[str], groups: list[int], edge_ids: list[str]) -> dict[str, object]:
    return {
        "mean_by_mechanism": _mean_by(values, labels),
        "std_by_mechanism": _std_by(values, labels),
        "between_class_over_within_class": _between_within_ratio(values, labels),
        "circuit_residual_variance": float(np.var(residualize_by_group(values[:, None], groups))),
        "edge_residual_variance": float(np.var(residualize_by_group(values[:, None], edge_ids))),
        "shot_noise_proxy": float(np.mean(np.abs(values)) / max(np.sqrt(max(1, len(values))), 1.0)),
    }


def _mean_by(values: np.ndarray, groups: Iterable[object]) -> dict[str, float]:
    return {str(group): float(np.mean(values[np.asarray([item == group for item in groups], dtype=bool)])) for group in sorted(set(groups), key=str)}


def _std_by(values: np.ndarray, groups: Iterable[object]) -> dict[str, float]:
    return {str(group): float(np.std(values[np.asarray([item == group for item in groups], dtype=bool)])) for group in sorted(set(groups), key=str)}


def _between_within_ratio(values: np.ndarray, labels: list[str]) -> float:
    class_means = []
    within = []
    for label in sorted(set(labels)):
        mask = np.asarray([item == label for item in labels], dtype=bool)
        if np.any(mask):
            class_means.append(float(np.mean(values[mask])))
            within.append(float(np.var(values[mask])))
    return float(np.var(class_means) / max(np.mean(within), NUMERICAL_ZERO)) if class_means else 0.0


def _pooled_std(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    return np.sqrt(0.5 * (np.var(left, axis=0) + np.var(right, axis=0)))


def _dominant_block(mean_abs: dict[str, float]) -> str:
    h = float(np.linalg.norm([mean_abs.get(name, 0.0) for name in HAMILTONIAN]))
    s = float(np.linalg.norm([mean_abs.get(name, 0.0) for name in STOCHASTIC]))
    a = float(np.linalg.norm([mean_abs.get(name, 0.0) for name in AFFINE]))
    return max({"hamiltonian": h, "stochastic": s, "affine_nonunital": a}, key={"hamiltonian": h, "stochastic": s, "affine_nonunital": a}.get)


def _expected_block(label: str) -> str:
    if label in {"M1", "M7"}:
        return "hamiltonian"
    if label == "M6":
        return "stochastic"
    if label == "M9":
        return "affine_nonunital"
    return "unknown"


def _blockwise_predict(row: np.ndarray, feature_names: list[str]) -> dict[str, str]:
    values = {name: float(row[idx]) for idx, name in enumerate(feature_names)}
    mean_abs = {name: abs(value) for name, value in values.items()}
    block = _dominant_block(mean_abs)
    h_xx_yy = max(abs(values.get("h_XX", 0.0)), abs(values.get("h_YY", 0.0)))
    h_zz = abs(values.get("h_ZZ", 0.0))
    gamma_values = {name: abs(values.get(name, 0.0)) for name in STOCHASTIC}
    return {
        "stage1_block": block,
        "stage2_hamiltonian_axis": "XX_YY" if h_xx_yy >= h_zz else "ZZ",
        "stage3_stochastic_axis": max(gamma_values, key=gamma_values.get),
        "stage4_relaxation_subtype": "relaxation_affine" if block == "affine_nonunital" else "not_relaxation",
        "mechanism_proxy": _proxy_label(block, h_xx_yy, h_zz),
    }


def _proxy_label(block: str, h_xx_yy: float, h_zz: float) -> str:
    if block == "hamiltonian":
        return "M7" if h_xx_yy >= h_zz else "M1"
    if block == "stochastic":
        return "M6"
    if block == "affine_nonunital":
        return "M9"
    return "unknown"


def _blockwise_stage_metrics(labels: list[str], preds: list[dict[str, str]]) -> dict[str, object]:
    expected_blocks = [_expected_block(label) for label in labels]
    pred_blocks = [item["stage1_block"] for item in preds]
    proxy = [item["mechanism_proxy"] for item in preds]
    h_mask = [label in {"M1", "M7"} for label in labels]
    h_true = ["ZZ" if label == "M1" else "XX_YY" for label, keep in zip(labels, h_mask) if keep]
    h_pred = [item["stage2_hamiltonian_axis"] for item, keep in zip(preds, h_mask) if keep]
    return {
        "stage1_block_accuracy": _accuracy(expected_blocks, pred_blocks),
        "stage2_hamiltonian_axis_accuracy": _accuracy(h_true, h_pred),
        "mechanism_proxy_accuracy": _accuracy(labels, proxy),
        "confusion_matrix_by_stage": {
            "stage1": _confusion(expected_blocks, pred_blocks, ["hamiltonian", "stochastic", "affine_nonunital"]),
            "stage2_hamiltonian": _confusion(h_true, h_pred, ["XX_YY", "ZZ"]),
            "mechanism_proxy": _confusion(labels, proxy, list(RZZ_FAMILY)),
        },
    }


def _rzz_signature_blocks_match(signatures: dict[str, object]) -> bool:
    rows = signatures.get("variants", {}).get("circuit_residualized_coordinates", {})
    if not isinstance(rows, dict):
        return False
    available = [
        row
        for label, row in rows.items()
        if label in set(RZZ_FAMILY)
        and isinstance(row, dict)
        and row.get("expected_block") != "unknown"
    ]
    return bool(available) and all(bool(row.get("expected_block_matched", False)) for row in available)


def _accuracy(true: list[str], pred: list[str]) -> float:
    if not true:
        return 0.0
    return float(np.mean([a == b for a, b in zip(true, pred)]))


def _confusion(true: list[str], pred: list[str], names: list[str]) -> dict[str, object]:
    index = {name: idx for idx, name in enumerate(names)}
    matrix = np.zeros((len(names), len(names)), dtype=int)
    for a, b in zip(true, pred):
        if a in index and b in index:
            matrix[index[a], index[b]] += 1
    return {"labels": names, "matrix": matrix.tolist()}


def _label_metrics(true: list[str], pred: list[str], class_names: list[str]) -> dict[str, object]:
    confusion = _confusion(true, pred, class_names)["matrix"]
    matrix = np.asarray(confusion, dtype=np.int64)
    recalls = []
    f1s = []
    for idx in range(len(class_names)):
        tp = float(matrix[idx, idx])
        fn = float(np.sum(matrix[idx, :]) - matrix[idx, idx])
        fp = float(np.sum(matrix[:, idx]) - matrix[idx, idx])
        rec = tp / (tp + fn) if tp + fn > 0 else 0.0
        prec = tp / (tp + fp) if tp + fp > 0 else 0.0
        f1 = 2.0 * prec * rec / (prec + rec) if prec + rec > 0 else 0.0
        recalls.append(rec)
        f1s.append(f1)
    return {
        "available": True,
        "balanced_accuracy": float(np.mean(recalls)) if recalls else 0.0,
        "macro_F1": float(np.mean(f1s)) if f1s else 0.0,
        "confusion_matrix": matrix.tolist(),
        "confusion_matrix_labels": class_names,
        "per_class_recall": {name: float(recalls[idx]) for idx, name in enumerate(class_names)},
    }


def _standardize_train_test(x_train: np.ndarray, x_test: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mean = np.mean(x_train, axis=0, keepdims=True)
    std = np.maximum(np.std(x_train, axis=0, keepdims=True), NUMERICAL_ZERO)
    return (x_train - mean) / std, (x_test - mean) / std


def _group_mean_norm(features: np.ndarray, groups: list[object]) -> float:
    values = []
    for group in sorted(set(groups), key=str):
        mask = np.asarray([item == group for item in groups], dtype=bool)
        values.append(float(np.linalg.norm(np.mean(features[mask], axis=0))))
    return float(np.mean(values)) if values else 0.0


def _one_hot_pairs(left: list[object], right: list[object]) -> np.ndarray:
    pairs = [f"{a}|{b}" for a, b in zip(left, right)]
    names = sorted(set(pairs))
    index = {name: idx for idx, name in enumerate(names)}
    out = np.zeros((len(pairs), len(names)), dtype=np.float64)
    for row, name in enumerate(pairs):
        out[row, index[name]] = 1.0
    return out


def _skipped_whitening(feature_blocks: dict[str, FeatureBlock]) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d10_whitening_ablation_metrics_v1",
        "skipped": True,
        "feature_block_results": {},
        "grouped_fold_predictions": {},
        "controls": {},
        "run_success": {"passed": False, "checks": {}},
        "feature_blocks": list(feature_blocks),
    }


def _finite(values: np.ndarray) -> np.ndarray:
    return np.nan_to_num(np.asarray(values, dtype=np.float64), nan=NUMERICAL_ZERO, posinf=NUMERICAL_ZERO, neginf=-NUMERICAL_ZERO)
