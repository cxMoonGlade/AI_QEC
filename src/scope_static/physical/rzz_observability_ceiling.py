from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from .targeted_v3 import RZZ_FAMILY


PAIR_NAMES = ("M1/M6", "M1/M7", "M1/M9", "M6/M7", "M6/M9", "M7/M9")
FORBIDDEN_FEATURE_TOKENS = ("oracle_label", "mechanism_id", "exact_ptm", "teacher_channel", "oracle_fingerprint")


@dataclass(frozen=True)
class FeatureBlock:
    name: str
    features: np.ndarray
    feature_names: list[str]
    source_blocks: list[str]
    residualize_against: np.ndarray | None = None
    residualize_feature_names: list[str] | None = None
    primary: bool = False
    control: bool = False
    explanatory: bool = False


def evaluate_ceiling_feature_blocks(
    feature_blocks: dict[str, FeatureBlock],
    labels: list[str],
    groups: list[int],
    *,
    primary_block: str = "v3c_plus_active_all",
    scrambled_control_block: str = "v3c_plus_scrambled_active_all",
    permutation_repeats: int = 128,
    seed: int = 0,
) -> dict[str, object]:
    y_names = [str(label) for label in labels]
    class_names = [name for name in RZZ_FAMILY if name in set(y_names)]
    if len(class_names) < 2:
        raise ValueError("S2D.8c requires at least two RZZ-family classes")
    class_index = {name: idx for idx, name in enumerate(class_names)}
    y = np.asarray([class_index[name] for name in y_names], dtype=np.int64)
    group_array = np.asarray(groups, dtype=np.int64)
    _validate_groups(group_array)
    _validate_feature_blocks(feature_blocks, expected_rows=len(y))

    block_results = {}
    fold_predictions = {}
    for name, block in feature_blocks.items():
        result = _evaluate_block(block, y, y_names, group_array, class_names, seed=int(seed))
        block_results[name] = _without_large_predictions(result)
        fold_predictions[name] = result["fold_predictions"]

    primary = block_results[primary_block]
    scrambled = block_results[scrambled_control_block]
    permutation = permutation_label_control(
        feature_blocks[primary_block],
        y,
        y_names,
        group_array,
        class_names,
        repeats=int(permutation_repeats),
        seed=int(seed),
    )
    run_success = _run_success(primary, scrambled, permutation)
    controls = {
        "schema": "scope_static_s2d8c_controls_v1",
        "primary_block": primary_block,
        "scrambled_control_block": scrambled_control_block,
        "real_minus_scrambled_macro_F1": float(primary["overall"]["macro_F1"] - scrambled["overall"]["macro_F1"]),
        "real_minus_scrambled_balanced_accuracy": float(primary["overall"]["balanced_accuracy"] - scrambled["overall"]["balanced_accuracy"]),
        "real_minus_permutation_macro_F1": float(primary["overall"]["macro_F1"] - permutation["macro_F1_mean"]),
        "real_minus_permutation_balanced_accuracy": float(primary["overall"]["balanced_accuracy"] - permutation["balanced_accuracy_mean"]),
        "permutation_label_control": permutation,
        "run_success": run_success,
    }
    secondary = secondary_nonlinear_diagnostics(
        feature_blocks[primary_block],
        y,
        y_names,
        group_array,
        class_names,
        seed=int(seed),
    )
    return {
        "schema": "scope_static_s2d8c_grouped_ceiling_v1",
        "class_names": class_names,
        "num_rows": int(len(y)),
        "groups": sorted({int(value) for value in group_array.tolist()}),
        "primary_block": primary_block,
        "scrambled_control_block": scrambled_control_block,
        "feature_block_results": block_results,
        "grouped_fold_predictions": fold_predictions,
        "controls": controls,
        "run_success": run_success,
        "residualized_active_attribution": residualized_active_attribution(block_results),
        "secondary_nonlinear_diagnostics": secondary,
    }


def permutation_label_control(
    block: FeatureBlock,
    y: np.ndarray,
    y_names: list[str],
    groups: np.ndarray,
    class_names: list[str],
    *,
    repeats: int,
    seed: int,
) -> dict[str, object]:
    rng = np.random.default_rng(int(seed) + 80_300)
    macro_values = []
    bal_values = []
    for _ in range(int(repeats)):
        permuted = rng.permutation(np.asarray(y, dtype=np.int64))
        result = _evaluate_block(block, permuted, [class_names[int(value)] for value in permuted], groups, class_names, seed=int(seed))
        macro_values.append(float(result["overall"]["macro_F1"]))
        bal_values.append(float(result["overall"]["balanced_accuracy"]))
    return {
        "schema": "scope_static_s2d8c_permutation_label_control_v1",
        "repeats": int(repeats),
        "seed": int(seed),
        "labels_permuted_within": "RZZ-family audit rows",
        "grouped_folds_preserved": True,
        "macro_F1_mean": float(np.mean(macro_values)) if macro_values else 0.0,
        "macro_F1_max": float(np.max(macro_values)) if macro_values else 0.0,
        "balanced_accuracy_mean": float(np.mean(bal_values)) if bal_values else 0.0,
        "balanced_accuracy_max": float(np.max(bal_values)) if bal_values else 0.0,
        "macro_F1_ci95": _ci95(macro_values),
        "balanced_accuracy_ci95": _ci95(bal_values),
    }


def residualized_active_attribution(block_results: dict[str, dict[str, object]]) -> dict[str, object]:
    primary = block_results.get("v3c_plus_active_all", {}).get("overall", {})
    residual = block_results.get("active_residualized_against_v3c", {}).get("overall", {})
    scrambled_residual = block_results.get("scrambled_active_residualized_against_v3c", {}).get("overall", {})
    return {
        "schema": "scope_static_s2d8c_residualized_active_attribution_v1",
        "primary_block": "v3c_plus_active_all",
        "residualized_active_block": "active_residualized_against_v3c",
        "scrambled_residualized_active_block": "scrambled_active_residualized_against_v3c",
        "primary_balanced_accuracy": primary.get("balanced_accuracy"),
        "residualized_active_balanced_accuracy": residual.get("balanced_accuracy"),
        "scrambled_residualized_active_balanced_accuracy": scrambled_residual.get("balanced_accuracy"),
        "residualized_minus_scrambled_balanced_accuracy": (
            None
            if not residual or not scrambled_residual
            else float(residual.get("balanced_accuracy", 0.0) - scrambled_residual.get("balanced_accuracy", 0.0))
        ),
        "interpretation": _residualized_interpretation(primary, residual, scrambled_residual),
    }


def secondary_nonlinear_diagnostics(
    block: FeatureBlock,
    y: np.ndarray,
    y_names: list[str],
    groups: np.ndarray,
    class_names: list[str],
    *,
    seed: int,
) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d8c_secondary_nonlinear_diagnostics_v1",
        "role": "secondary_diagnostic_not_used_for_pass_fail",
        "primary_pass_fail_uses": "sklearn.StandardScaler+sklearn.LogisticRegression(class_weight=balanced)",
        "models": {
            "rbf_svm": _evaluate_secondary_model(block, y, groups, class_names, model_name="rbf_svm", seed=int(seed)),
            "gradient_boosting": _evaluate_secondary_model(block, y, groups, class_names, model_name="gradient_boosting", seed=int(seed)),
        },
    }


def features_schema(feature_blocks: dict[str, FeatureBlock], *, source_root: str) -> dict[str, object]:
    blocks = {}
    for name, block in feature_blocks.items():
        blocks[name] = {
            "num_rows": int(block.features.shape[0]),
            "num_features": int(block.features.shape[1]),
            "source_blocks": list(block.source_blocks),
            "feature_names": list(block.feature_names),
            "primary": bool(block.primary),
            "control": bool(block.control),
            "explanatory": bool(block.explanatory),
            "residualized_fold_local": block.residualize_against is not None,
            "uses_oracle_label": False,
            "uses_exact_teacher_channel": False,
            "uses_exact_ptm": False,
            "visible_inputs": ["shot_bits", "probe_metadata", "visible_circuit_schedule", "visible_location_metadata"],
        }
    return {
        "schema": "scope_static_s2d8c_features_schema_physics_visible_v1",
        "source_root": str(source_root),
        "no_new_teacher_sampling": True,
        "feature_blocks": blocks,
        "forbidden_feature_tokens": list(FORBIDDEN_FEATURE_TOKENS),
    }


def audit_labels_schema(labels: list[str], groups: list[int], records: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d8c_audit_labels_schema_oracle_only_v1",
        "labels_role": "audit_only_supervised_targets",
        "forbidden_as_phys3_features": True,
        "oracle_label_names": [str(value) for value in labels],
        "circuit_id_groups": [int(value) for value in groups],
        "record_refs": [
            {
                "location_id": int(record.get("location_id", idx)),
                "oracle_label": str(record.get("oracle_label")),
                "circuit_id": int(record.get("circuit_id", 0)),
                "qubits": [int(value) for value in record.get("qubits", [])],
            }
            for idx, record in enumerate(records)
        ],
    }


def leakage_guardrail_audit(
    feature_blocks: dict[str, FeatureBlock],
    labels_schema: dict[str, object],
    fold_audit: dict[str, object],
) -> dict[str, object]:
    feature_columns = []
    for block in feature_blocks.values():
        feature_columns.extend(block.feature_names)
    lower_columns = [name.lower() for name in feature_columns]
    checks = {
        "oracle_label_not_in_feature_columns": not any("oracle_label" in name for name in lower_columns),
        "mechanism_id_not_in_feature_columns": not any("mechanism_id" in name for name in lower_columns),
        "ptm_columns_absent": not any("ptm" in name for name in lower_columns),
        "teacher_channel_columns_absent": not any("teacher_channel" in name for name in lower_columns),
        "oracle_fingerprint_columns_absent": not any("oracle_fingerprint" in name for name in lower_columns),
        "mechanism_id_not_used_in_clustering": True,
        "transfer_splits_grouped_by_circuit_id": bool(fold_audit.get("all_test_groups_disjoint_from_train", False)),
        "oracle_labels_schema_separate": labels_schema.get("schema") == "scope_static_s2d8c_audit_labels_schema_oracle_only_v1",
    }
    passed = all(bool(value) for value in checks.values())
    return {
        "schema": "scope_static_s2d8c_leakage_guardrail_audit_v1",
        "passed": passed,
        "checks": checks,
        "feature_column_count": int(len(feature_columns)),
    }


def grouped_fold_audit(groups: list[int]) -> dict[str, object]:
    group_array = np.asarray(groups, dtype=np.int64)
    folds = []
    all_disjoint = True
    for test_group in sorted(set(group_array.tolist())):
        train_groups = sorted({int(value) for value in group_array[group_array != test_group].tolist()})
        test_groups = [int(test_group)]
        disjoint = set(train_groups).isdisjoint(test_groups)
        all_disjoint = all_disjoint and disjoint
        folds.append({"test_group": int(test_group), "train_groups": train_groups, "test_groups": test_groups, "disjoint": bool(disjoint)})
    return {
        "schema": "scope_static_s2d8c_grouped_fold_audit_v1",
        "splitter": "LeaveOneGroupOut",
        "group_key": "circuit_id",
        "num_folds": int(len(folds)),
        "folds": folds,
        "all_test_groups_disjoint_from_train": bool(all_disjoint),
    }


def _evaluate_block(
    block: FeatureBlock,
    y: np.ndarray,
    y_names: list[str],
    groups: np.ndarray,
    class_names: list[str],
    *,
    seed: int,
) -> dict[str, object]:
    y = np.asarray(y, dtype=np.int64)
    groups = np.asarray(groups, dtype=np.int64)
    fold_records = []
    all_true = []
    all_pred = []
    all_prob = []
    all_logits = []
    for fold_idx, test_group in enumerate(sorted(set(groups.tolist()))):
        train_mask = groups != int(test_group)
        test_mask = groups == int(test_group)
        x_train, x_test = _fold_features(block, train_mask, test_mask)
        x_train, x_test, scaler = _standardize_train_test(x_train, x_test)
        model = _fit_balanced_logistic(x_train, y[train_mask], num_classes=len(class_names), seed=int(seed) + fold_idx)
        logits, prob = _predict_balanced_logistic(model, x_test, num_classes=len(class_names))
        pred = np.argmax(prob, axis=1)
        fold_metrics = _classification_metrics(y[test_mask], pred, prob, class_names)
        fold_records.append(
            {
                "fold": int(fold_idx),
                "test_circuit_id": int(test_group),
                "train_circuit_ids": sorted({int(value) for value in groups[train_mask].tolist()}),
                "test_indices": [int(value) for value in np.where(test_mask)[0].tolist()],
                "true_labels": [class_names[int(value)] for value in y[test_mask].tolist()],
                "predicted_labels": [class_names[int(value)] for value in pred.tolist()],
                "probabilities": prob.tolist(),
                "metrics": fold_metrics,
                "preprocessing": {
                    "standard_scaler_fit_on_train_only": True,
                    "residualizer_fit_on_train_only": block.residualize_against is not None,
                    "scaler": "sklearn.preprocessing.StandardScaler",
                    "train_feature_mean_shape": [int(value) for value in scaler["mean"].shape],
                },
            }
        )
        all_true.extend([int(value) for value in y[test_mask].tolist()])
        all_pred.extend([int(value) for value in pred.tolist()])
        all_prob.append(prob)
        all_logits.append(logits)
    prob_all = np.concatenate(all_prob, axis=0) if all_prob else np.zeros((0, len(class_names)), dtype=np.float64)
    logits_all = np.concatenate(all_logits, axis=0) if all_logits else np.zeros((0, len(class_names)), dtype=np.float64)
    overall = _classification_metrics(np.asarray(all_true, dtype=np.int64), np.asarray(all_pred, dtype=np.int64), prob_all, class_names)
    fold_macro = [float(record["metrics"]["macro_F1"]) for record in fold_records]
    fold_bal = [float(record["metrics"]["balanced_accuracy"]) for record in fold_records]
    overall["macro_F1_ci95"] = _ci95(fold_macro)
    overall["balanced_accuracy_ci95"] = _ci95(fold_bal)
    overall["ci_method"] = "leave_one_circuit_id_out_t_interval"
    overall["num_folds"] = int(len(fold_records))
    overall["pairwise"] = _pairwise_metrics(np.asarray(all_true, dtype=np.int64), prob_all, class_names)
    overall["pairwise_margins"] = _pairwise_margins(np.asarray(all_true, dtype=np.int64), prob_all, class_names)
    return {
        "block": block.name,
        "model": "sklearn.StandardScaler+sklearn.LogisticRegression(class_weight=balanced)",
        "validation": "LeaveOneGroupOut(circuit_id)",
        "overall": overall,
        "fold_predictions": fold_records,
        "logits": logits_all.tolist(),
    }


def _without_large_predictions(result: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in result.items() if key not in {"fold_predictions", "logits"}}


def _evaluate_secondary_model(
    block: FeatureBlock,
    y: np.ndarray,
    groups: np.ndarray,
    class_names: list[str],
    *,
    model_name: str,
    seed: int,
) -> dict[str, object]:
    y = np.asarray(y, dtype=np.int64)
    groups = np.asarray(groups, dtype=np.int64)
    all_true = []
    all_pred = []
    all_prob = []
    fold_metrics = []
    for fold_idx, test_group in enumerate(sorted(set(groups.tolist()))):
        train_mask = groups != int(test_group)
        test_mask = groups == int(test_group)
        x_train, x_test = _fold_features(block, train_mask, test_mask)
        x_train, x_test, _ = _standardize_train_test(x_train, x_test)
        model = _fit_secondary_model(x_train, y[train_mask], num_classes=len(class_names), model_name=model_name, seed=int(seed) + fold_idx)
        prob = _predict_secondary_model(model, x_test, num_classes=len(class_names))
        pred = np.argmax(prob, axis=1)
        fold_metrics.append(_classification_metrics(y[test_mask], pred, prob, class_names))
        all_true.extend([int(value) for value in y[test_mask].tolist()])
        all_pred.extend([int(value) for value in pred.tolist()])
        all_prob.append(prob)
    prob_all = np.concatenate(all_prob, axis=0) if all_prob else np.zeros((0, len(class_names)), dtype=np.float64)
    overall = _classification_metrics(np.asarray(all_true, dtype=np.int64), np.asarray(all_pred, dtype=np.int64), prob_all, class_names)
    overall["macro_F1_ci95"] = _ci95([float(item["macro_F1"]) for item in fold_metrics])
    overall["balanced_accuracy_ci95"] = _ci95([float(item["balanced_accuracy"]) for item in fold_metrics])
    return {
        "model": model_name,
        "role": "secondary_diagnostic_not_used_for_pass_fail",
        "overall": overall,
    }


def _fit_secondary_model(
    x_train: np.ndarray,
    y_train: np.ndarray,
    *,
    num_classes: int,
    model_name: str,
    seed: int,
) -> dict[str, object]:
    y = np.asarray(y_train, dtype=np.int64)
    present = np.asarray(sorted(set(int(value) for value in y.tolist())), dtype=np.int64)
    if present.size < 2:
        return {"kind": "constant", "class": int(present[0]) if present.size else 0, "num_classes": int(num_classes)}
    if model_name == "rbf_svm":
        clf = SVC(C=1.0, gamma="scale", kernel="rbf", class_weight="balanced", probability=True, random_state=int(seed))
        clf.fit(np.asarray(x_train, dtype=np.float64), y)
        return {"kind": "classifier", "classifier": clf, "classes": np.asarray(clf.classes_, dtype=np.int64)}
    if model_name == "gradient_boosting":
        counts = np.bincount(y, minlength=int(num_classes)).astype(np.float64)
        counts[counts <= 0.0] = 1.0
        sample_weight = float(y.size) / (float(num_classes) * counts[y])
        clf = GradientBoostingClassifier(random_state=int(seed), n_estimators=32, max_depth=2)
        clf.fit(np.asarray(x_train, dtype=np.float64), y, sample_weight=sample_weight)
        return {"kind": "classifier", "classifier": clf, "classes": np.asarray(clf.classes_, dtype=np.int64)}
    raise ValueError(f"unknown secondary model {model_name!r}")


def _predict_secondary_model(model: dict[str, object], x_test: np.ndarray, *, num_classes: int) -> np.ndarray:
    x = np.asarray(x_test, dtype=np.float64)
    if model.get("kind") == "constant":
        prob = np.zeros((x.shape[0], int(num_classes)), dtype=np.float64)
        prob[:, int(model.get("class", 0))] = 1.0
        return prob
    clf = model["classifier"]
    classes = np.asarray(model["classes"], dtype=np.int64)
    local_prob = np.asarray(clf.predict_proba(x), dtype=np.float64)
    prob = np.zeros((x.shape[0], int(num_classes)), dtype=np.float64)
    for local_idx, class_idx in enumerate(classes.tolist()):
        prob[:, int(class_idx)] = local_prob[:, int(local_idx)]
    return prob


def _fold_features(block: FeatureBlock, train_mask: np.ndarray, test_mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    features = np.asarray(block.features, dtype=np.float64)
    if block.residualize_against is None:
        return features[train_mask], features[test_mask]
    base = np.asarray(block.residualize_against, dtype=np.float64)
    train_resid, test_resid = _residualize_train_test(base[train_mask], features[train_mask], base[test_mask], features[test_mask])
    return train_resid, test_resid


def _residualize_train_test(
    base_train: np.ndarray,
    active_train: np.ndarray,
    base_test: np.ndarray,
    active_test: np.ndarray,
    *,
    ridge: float = 1e-6,
) -> tuple[np.ndarray, np.ndarray]:
    design_train = np.concatenate([np.ones((base_train.shape[0], 1), dtype=np.float64), base_train], axis=1)
    design_test = np.concatenate([np.ones((base_test.shape[0], 1), dtype=np.float64), base_test], axis=1)
    gram = design_train.T @ design_train
    penalty = float(ridge) * np.eye(gram.shape[0], dtype=np.float64)
    penalty[0, 0] = 0.0
    coef = np.linalg.pinv(gram + penalty) @ design_train.T @ active_train
    return active_train - design_train @ coef, active_test - design_test @ coef


def _standardize_train_test(x_train: np.ndarray, x_test: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
    scaler = StandardScaler()
    train = scaler.fit_transform(np.asarray(x_train, dtype=np.float64))
    test = scaler.transform(np.asarray(x_test, dtype=np.float64))
    return train, test, {"mean": np.asarray(scaler.mean_, dtype=np.float64), "scale": np.asarray(scaler.scale_, dtype=np.float64)}


def _fit_balanced_logistic(
    x_train: np.ndarray,
    y_train: np.ndarray,
    *,
    num_classes: int,
    seed: int,
    max_iter: int = 1000,
) -> dict[str, object]:
    y = np.asarray(y_train, dtype=np.int64)
    present = np.asarray(sorted(set(int(value) for value in y.tolist())), dtype=np.int64)
    if present.size < 2:
        return {"kind": "constant", "class": int(present[0]) if present.size else 0, "num_classes": int(num_classes)}
    clf = LogisticRegression(class_weight="balanced", max_iter=int(max_iter), solver="lbfgs", C=1.0, random_state=int(seed))
    clf.fit(np.asarray(x_train, dtype=np.float64), y)
    return {"kind": "sklearn_logistic_regression", "classifier": clf, "classes": np.asarray(clf.classes_, dtype=np.int64), "num_classes": int(num_classes)}


def _predict_balanced_logistic(model: dict[str, object], x_test: np.ndarray, *, num_classes: int) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(x_test, dtype=np.float64)
    if model.get("kind") == "constant":
        prob = np.zeros((x.shape[0], int(num_classes)), dtype=np.float64)
        prob[:, int(model.get("class", 0))] = 1.0
        return np.log(np.clip(prob, 1e-12, 1.0)), prob
    clf = model["classifier"]
    classes = np.asarray(model["classes"], dtype=np.int64)
    local_prob = np.asarray(clf.predict_proba(x), dtype=np.float64)
    prob = np.zeros((x.shape[0], int(num_classes)), dtype=np.float64)
    for local_idx, class_idx in enumerate(classes.tolist()):
        prob[:, int(class_idx)] = local_prob[:, int(local_idx)]
    return np.log(np.clip(prob, 1e-12, 1.0)), prob


def _classification_metrics(y_true: np.ndarray, y_pred: np.ndarray, prob: np.ndarray, class_names: list[str]) -> dict[str, object]:
    num_classes = len(class_names)
    confusion = np.zeros((num_classes, num_classes), dtype=np.int64)
    for true, pred in zip(y_true.tolist(), y_pred.tolist()):
        confusion[int(true), int(pred)] += 1
    recalls = {}
    f1_values = []
    recall_values = []
    for idx, name in enumerate(class_names):
        tp = float(confusion[idx, idx])
        fn = float(np.sum(confusion[idx, :]) - confusion[idx, idx])
        fp = float(np.sum(confusion[:, idx]) - confusion[idx, idx])
        support = tp + fn
        recall = tp / support if support > 0.0 else None
        precision = tp / (tp + fp) if tp + fp > 0.0 else 0.0
        f1 = (2.0 * precision * float(recall) / (precision + float(recall))) if recall is not None and precision + float(recall) > 0.0 else 0.0
        recalls[name] = recall
        if support > 0.0:
            recall_values.append(float(recall))
            f1_values.append(float(f1))
    return {
        "macro_F1": float(np.mean(f1_values)) if f1_values else 0.0,
        "balanced_accuracy": float(np.mean(recall_values)) if recall_values else 0.0,
        "confusion_matrix": confusion.tolist(),
        "confusion_matrix_labels": list(class_names),
        "per_class_recall": recalls,
        "min_class_recall": float(min(recall_values)) if recall_values else 0.0,
    }


def _pairwise_metrics(y_true: np.ndarray, prob: np.ndarray, class_names: list[str]) -> dict[str, object]:
    out = {}
    class_index = {name: idx for idx, name in enumerate(class_names)}
    for pair in PAIR_NAMES:
        left, right = pair.split("/")
        if left not in class_index or right not in class_index:
            out[pair] = {"available": False, "auc": None, "accuracy": None}
            continue
        li = class_index[left]
        ri = class_index[right]
        mask = np.logical_or(y_true == li, y_true == ri)
        if int(np.sum(mask)) == 0 or len(set(y_true[mask].tolist())) < 2:
            out[pair] = {"available": False, "auc": None, "accuracy": None}
            continue
        score = prob[mask, li] - prob[mask, ri]
        binary = (y_true[mask] == li).astype(np.int64)
        pred_left = score >= 0.0
        pred = np.where(pred_left, li, ri)
        out[pair] = {
            "available": True,
            "auc": _binary_auc(binary, score),
            "accuracy": float(np.mean(pred == y_true[mask])),
        }
    return out


def _pairwise_margins(y_true: np.ndarray, prob: np.ndarray, class_names: list[str]) -> dict[str, object]:
    out = {}
    class_index = {name: idx for idx, name in enumerate(class_names)}
    for pair in PAIR_NAMES:
        left, right = pair.split("/")
        if left not in class_index or right not in class_index:
            out[pair] = {"available": False, "margin": None}
            continue
        li = class_index[left]
        ri = class_index[right]
        mask = np.logical_or(y_true == li, y_true == ri)
        values = []
        for true, row in zip(y_true[mask].tolist(), prob[mask]):
            if int(true) == li:
                values.append(float(row[li] - row[ri]))
            else:
                values.append(float(row[ri] - row[li]))
        out[pair] = {"available": bool(values), "margin": float(np.mean(values)) if values else None}
    return out


def _binary_auc(binary_true: np.ndarray, score: np.ndarray) -> float | None:
    pos = score[binary_true == 1]
    neg = score[binary_true == 0]
    if pos.size == 0 or neg.size == 0:
        return None
    wins = 0.0
    total = float(pos.size * neg.size)
    for value in pos:
        wins += float(np.sum(value > neg)) + 0.5 * float(np.sum(value == neg))
    return float(wins / total) if total > 0.0 else None


def _run_success(primary: dict[str, object], scrambled: dict[str, object], permutation: dict[str, object]) -> dict[str, object]:
    overall = primary["overall"]
    pairwise_margins = overall.get("pairwise_margins", {})
    available_margins = [
        float(item["margin"])
        for item in pairwise_margins.values()
        if isinstance(item, dict) and bool(item.get("available")) and item.get("margin") is not None
    ]
    real_minus_scrambled_bal = float(overall["balanced_accuracy"] - scrambled["overall"]["balanced_accuracy"])
    real_minus_perm_bal = float(overall["balanced_accuracy"] - permutation["balanced_accuracy_mean"])
    checks = {
        "macro_F1_ge_0_80": float(overall["macro_F1"]) >= 0.80,
        "balanced_accuracy_ge_0_80": float(overall["balanced_accuracy"]) >= 0.80,
        "real_minus_scrambled_balanced_accuracy_ge_0_25": real_minus_scrambled_bal >= 0.25,
        "real_minus_permutation_balanced_accuracy_ge_0_25": real_minus_perm_bal >= 0.25,
        "all_available_pairwise_margins_gt_0": all(value > 0.0 for value in available_margins) if available_margins else False,
        "no_single_class_recall_lt_0_65": float(overall["min_class_recall"]) >= 0.65,
    }
    return {"passed": all(bool(value) for value in checks.values()), "checks": checks}


def _residualized_interpretation(primary: dict[str, object], residual: dict[str, object], scrambled_residual: dict[str, object]) -> str:
    if not primary or not residual:
        return "residualized active attribution unavailable"
    primary_bal = float(primary.get("balanced_accuracy", 0.0))
    residual_bal = float(residual.get("balanced_accuracy", 0.0))
    scrambled_bal = float(scrambled_residual.get("balanced_accuracy", 0.0)) if scrambled_residual else 0.0
    if primary_bal >= 0.80 and residual_bal >= 0.80 and residual_bal - scrambled_bal >= 0.25:
        return "active probes retain RZZ-family signal beyond baseline v3c"
    if primary_bal >= 0.80 and residual_bal < 0.80:
        return "primary signal is mostly baseline v3c/redundant rather than residual active structure"
    return "primary linear ceiling does not show strong transferable signal"


def _softmax(logits: np.ndarray) -> np.ndarray:
    x = np.asarray(logits, dtype=np.float64)
    x = x - np.max(x, axis=1, keepdims=True)
    exp = np.exp(x)
    return exp / np.maximum(np.sum(exp, axis=1, keepdims=True), 1e-12)


def _ci95(values: Iterable[float]) -> dict[str, float | int | None]:
    vals = np.asarray([float(value) for value in values], dtype=np.float64)
    if vals.size == 0:
        return {"n": 0, "mean": None, "low": None, "high": None}
    mean = float(np.mean(vals))
    if vals.size == 1:
        return {"n": 1, "mean": mean, "low": mean, "high": mean}
    tcrit = {2: 4.302652729911275, 3: 3.182446305284263, 4: 2.7764451051977987, 5: 2.570581835636314}.get(
        int(vals.size - 1),
        1.959963984540054,
    )
    half = float(tcrit * np.std(vals, ddof=1) / math.sqrt(vals.size))
    return {"n": int(vals.size), "mean": mean, "low": mean - half, "high": mean + half}


def _validate_groups(groups: np.ndarray) -> None:
    if groups.ndim != 1:
        raise ValueError("groups must be one-dimensional")
    if len(set(groups.tolist())) < 2:
        raise ValueError("grouped validation requires at least two groups")


def _validate_feature_blocks(feature_blocks: dict[str, FeatureBlock], *, expected_rows: int) -> None:
    for name, block in feature_blocks.items():
        if block.features.shape[0] != int(expected_rows):
            raise ValueError(f"feature block {name!r} has wrong row count")
        lowered = [feature.lower() for feature in block.feature_names]
        for token in FORBIDDEN_FEATURE_TOKENS:
            if any(token in feature for feature in lowered):
                raise ValueError(f"feature block {name!r} contains forbidden token {token!r}")
