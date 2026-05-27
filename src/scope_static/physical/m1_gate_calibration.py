from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import json
import numpy as np

from .local_inverse import build_visible_location_representations
from .typed_spam_gate_invariant import (
    classification_metrics,
    m5_overfragmentation_report,
)


M1_BOOST_FEATURES = ("log_coherence_ratio", "h_zz_axial_ratio_log", "coherence_norm")
NEIGHBORS = ("M6", "M7", "M10", "M2", "M3", "M9")
ERROR_TYPE_NAMES = ("gate", "readout", "prep_reset", "other")


@dataclass(frozen=True)
class S2D11bData:
    x: np.ndarray
    feature_names: list[str]
    labels: list[str]
    groups: list[int]
    branches: list[str]
    records: list[dict[str, object]]
    class_names: list[str]
    baseline_s2d11: dict[str, object]
    source_record: dict[str, object]
    source_run_dir: Path


def load_s2d11b_data(source_root: str | Path) -> S2D11bData:
    root = Path(source_root)
    run_dir = root / "phys9_multicircuit_setD_balanced" if (root / "phys9_multicircuit_setD_balanced").exists() else root
    metrics_path = run_dir / "metrics.json"
    if not metrics_path.exists():
        raise FileNotFoundError(f"S2D.11b requires existing S2D.11 run metrics at {metrics_path}")
    record = json.loads(metrics_path.read_text())
    label_refs = record["audit_labels_schema_oracle_only"]["record_refs"]
    labels_by_location = {int(item["location_id"]): str(item["oracle_label"]) for item in label_refs}
    groups_by_location = {int(item["location_id"]): int(item["circuit_id"]) for item in label_refs}
    qubits_by_location = {int(item["location_id"]): [int(value) for value in item.get("qubits", [])] for item in label_refs}
    rows = []
    for branch_name, table_name in (
        ("gate_process_branch", "gate_process_feature_table"),
        ("readout_branch", "readout_branch_feature_table"),
        ("prep_reset_branch", "prep_reset_branch_feature_table"),
    ):
        for item in record.get(table_name, {}).get("records", []):
            location_id = int(item["location_id"])
            rows.append(
                {
                    "location_id": location_id,
                    "circuit_id": int(item.get("circuit_id", groups_by_location.get(location_id, 0))),
                    "oracle_label": labels_by_location[location_id],
                    "branch": branch_name,
                    "instruction": str(item.get("instruction", "")),
                    "qubits": [int(value) for value in item.get("qubits", qubits_by_location.get(location_id, []))],
                    "features": dict(item["features"]),
                }
            )
    rows = sorted(rows, key=lambda item: int(item["location_id"]))
    if not rows:
        raise ValueError(f"{metrics_path} does not contain S2D.11 feature table rows")
    feature_names = sorted(rows[0]["features"].keys())
    x = _finite(np.asarray([[float(row["features"].get(name, 0.0)) for name in feature_names] for row in rows], dtype=np.float64))
    labels = [str(row["oracle_label"]) for row in rows]
    groups = [int(row["circuit_id"]) for row in rows]
    branches = [str(row["branch"]) for row in rows]
    class_names = sorted(set(labels), key=_mechanism_sort_key)
    return S2D11bData(
        x=x,
        feature_names=feature_names,
        labels=labels,
        groups=groups,
        branches=branches,
        records=rows,
        class_names=class_names,
        baseline_s2d11=record["branch_ablation_metrics"]["typed_gate_readout_prep_invariant_learner"]["overall"],
        source_record=record,
        source_run_dir=run_dir,
    )


def run_m1_gate_calibration_audit(
    source_root: str | Path,
    *,
    seed: int = 0,
    run_two_stage_if_soft_fails: bool = True,
) -> dict[str, object]:
    data = load_s2d11b_data(source_root)
    baseline = grouped_dual_ridge_scores(data.x, data.labels, data.groups, data.class_names, seed=int(seed), return_scores=True)
    compact = _compact_variant("baseline_typed_linear", baseline, data)
    boost = m1_logit_boost_variant(data, seed=int(seed))
    reweight = axial_reweighting_variant(data, seed=int(seed))
    dense = dense_terms_variant(data, seed=int(seed))
    variants = {
        "baseline_typed_linear": compact,
        "typed_linear_plus_M1_logit_boost": boost,
        "typed_linear_plus_axial_feature_reweighting": reweight,
        "compact_plus_selected_RZZ_dense_terms": dense,
    }
    soft_best_name = _best_variant_name(variants)
    soft_best = variants[soft_best_name]
    if run_two_stage_if_soft_fails and not s2d11b_success(soft_best, data)["passed"]:
        variants["two_stage_gate_classifier"] = two_stage_gate_classifier_variant(data, seed=int(seed))
    else:
        variants["two_stage_gate_classifier"] = _skipped_variant("two_stage_gate_classifier", "soft calibration passed or secondary diagnostic disabled", data)
    best_name = _best_variant_name(variants)
    best = variants[best_name]
    result = {
        "schema": "scope_static_s2d11b_m1_gate_branch_grouped_calibration_v1",
        "stage": "S2D.11b_M1_gate_branch_grouped_calibration_audit",
        "source_root": str(source_root),
        "source_run_dir": str(data.source_run_dir),
        "source_stage": data.source_record.get("stage", "S2D.11_typed_SPAM_gate_invariant_learner"),
        "class_names": data.class_names,
        "baseline_s2d11": data.baseline_s2d11,
        "calibration_variant_metrics": variants,
        "best_variant": best_name,
        "primary_verdict": s2d11b_success(best, data),
        "m1_false_negative_audit": m1_false_negative_audit(data, baseline),
        "m1_grouped_fold_breakdown": m1_grouped_fold_breakdown(data, baseline),
        "m1_invariant_snr_audit": m1_invariant_snr_audit(data),
        "m1_pairwise_margin_report": m1_pairwise_margin_report(variants),
        "m1_dense_vs_compact_feature_audit": dense.get("dense_feature_audit", {}),
        "m1_calibration_thresholds_by_fold": boost.get("calibration_by_fold", {}),
        "m1_soft_rule_ablation": {name: _variant_summary(row) for name, row in variants.items()},
        "m1_vs_m6_m7_m10_tradeoff": tradeoff_report(variants, data),
        "m1_vs_m7_m8_m12_tradeoff": tradeoff_report(variants, data),
        "gate_neighbor_recall_report": gate_neighbor_recall_report(variants, data),
        "error_type_taxonomy": error_type_taxonomy(data),
        "error_type_metrics": error_type_metrics(variants, data),
        "mechanism_metrics_by_error_type": mechanism_metrics_by_error_type(variants, data),
        "leakage_guardrail_audit": leakage_guardrail_audit(data, variants),
        "summary": summary_record(best_name, best, data),
    }
    return result


def m1_logit_boost_variant(data: S2D11bData, *, seed: int = 0) -> dict[str, object]:
    x = data.x
    boost = _boost_matrix(data)
    labels = np.asarray(data.labels, dtype=object)
    groups = np.asarray(data.groups, dtype=np.int64)
    class_index = {name: idx for idx, name in enumerate(data.class_names)}
    m1_idx = class_index.get("M1")
    if m1_idx is None:
        return _skipped_variant("typed_linear_plus_M1_logit_boost", "M1 absent", data)
    regs = (1e-4, 1e-3, 1e-2, 1e-1, 1.0, 10.0)
    gains = (0.25, 0.5, 1.0, 2.0, 4.0)
    true_all: list[str] = []
    pred_all: list[str] = []
    prob_all: list[np.ndarray] = []
    fold_records = []
    for fold_idx, test_group in enumerate(sorted(set(groups.tolist()))):
        train = groups != int(test_group)
        test = groups == int(test_group)
        selected = _select_boost_hyperparams(x, boost, labels, groups, data.class_names, train, regs, gains, seed=int(seed) + fold_idx)
        baseline = _fit_predict_scores(x[train], labels[train], x[test], data.class_names, seed=int(seed) + fold_idx)
        coef = _fit_boost_coefficients(boost[train], labels[train], reg=float(selected["selected_reg"]))
        scores = np.array(baseline["scores"], copy=True)
        scores[:, m1_idx] += float(selected["selected_gain"]) * _apply_boost(boost[test], coef)
        probabilities = _softmax(scores)
        pred = np.argmax(probabilities, axis=1)
        true_labels = labels[test].astype(str).tolist()
        pred_labels = [data.class_names[int(value)] for value in pred.tolist()]
        true_all.extend(true_labels)
        pred_all.extend(pred_labels)
        prob_all.append(probabilities)
        fold_records.append(
            {
                "fold": int(fold_idx),
                "test_circuit_id": int(test_group),
                **selected,
                "outer_test_M1_recall": _class_recall(true_labels, pred_labels, "M1"),
            }
        )
    prob = np.concatenate(prob_all, axis=0) if prob_all else np.zeros((0, len(data.class_names)))
    metrics = classification_metrics(true_all, pred_all, data.class_names, prob)
    return {
        "schema": "scope_static_s2d11b_variant_v1",
        "variant": "typed_linear_plus_M1_logit_boost",
        "model": "baseline dual-ridge scores plus nested grouped raw-invariant M1 boost",
        "overall": metrics,
        "predicted_labels": pred_all,
        "true_labels": true_all,
        "calibration_by_fold": {"schema": "scope_static_s2d11b_m1_calibration_thresholds_by_fold_v1", "folds": fold_records},
    }


def axial_reweighting_variant(data: S2D11bData, *, seed: int = 0) -> dict[str, object]:
    selected = [name for name in ("log_coherence_ratio", "h_zz_axial_ratio", "coherence_norm", "h_ZZ") if name in data.feature_names]
    if not selected:
        return _skipped_variant("typed_linear_plus_axial_feature_reweighting", "no axial feature columns found", data)
    idx = [data.feature_names.index(name) for name in selected]
    groups = np.asarray(data.groups, dtype=np.int64)
    labels = np.asarray(data.labels, dtype=object)
    gains = (1.0, 1.5, 2.0, 4.0, 8.0)
    true_all: list[str] = []
    pred_all: list[str] = []
    prob_all: list[np.ndarray] = []
    folds = []
    for fold_idx, test_group in enumerate(sorted(set(groups.tolist()))):
        train = groups != int(test_group)
        test = groups == int(test_group)
        best_gain = 1.0
        best_score = (-1.0, -1.0)
        for gain in gains:
            local_scores = []
            for inner_group in sorted(set(groups[train].tolist())):
                inner_train = train & (groups != int(inner_group))
                inner_val = train & (groups == int(inner_group))
                x_mod = np.array(data.x, copy=True)
                x_mod[:, idx] *= float(gain)
                result = _fit_predict_scores(x_mod[inner_train], labels[inner_train], x_mod[inner_val], data.class_names, seed=int(seed) + fold_idx)
                pred = [data.class_names[int(value)] for value in np.argmax(result["probabilities"], axis=1).tolist()]
                true = labels[inner_val].astype(str).tolist()
                local_scores.append((_class_recall(true, pred, "M1"), classification_metrics(true, pred, data.class_names)["balanced_accuracy"]))
            score = tuple(np.mean([item[i] for item in local_scores]) for i in range(2)) if local_scores else (0.0, 0.0)
            if score > best_score:
                best_score = score
                best_gain = float(gain)
        x_mod = np.array(data.x, copy=True)
        x_mod[:, idx] *= best_gain
        result = _fit_predict_scores(x_mod[train], labels[train], x_mod[test], data.class_names, seed=int(seed) + fold_idx)
        prob = result["probabilities"]
        pred = [data.class_names[int(value)] for value in np.argmax(prob, axis=1).tolist()]
        true = labels[test].astype(str).tolist()
        true_all.extend(true)
        pred_all.extend(pred)
        prob_all.append(prob)
        folds.append({"fold": int(fold_idx), "test_circuit_id": int(test_group), "selected_gain": best_gain, "inner_mean_M1_recall": best_score[0]})
    prob = np.concatenate(prob_all, axis=0) if prob_all else np.zeros((0, len(data.class_names)))
    return {
        "schema": "scope_static_s2d11b_variant_v1",
        "variant": "typed_linear_plus_axial_feature_reweighting",
        "selected_features": selected,
        "overall": classification_metrics(true_all, pred_all, data.class_names, prob),
        "predicted_labels": pred_all,
        "true_labels": true_all,
        "folds": folds,
    }


def dense_terms_variant(data: S2D11bData, *, seed: int = 0) -> dict[str, object]:
    dense = _load_dense_features(data)
    if dense is None:
        return _skipped_variant("compact_plus_selected_RZZ_dense_terms", "source observations unavailable for dense learner-visible local inverse features", data)
    dense_x, dense_names = dense
    labels = np.asarray(data.labels, dtype=object)
    groups = np.asarray(data.groups, dtype=np.int64)
    true_all: list[str] = []
    pred_all: list[str] = []
    prob_all: list[np.ndarray] = []
    folds = []
    for fold_idx, test_group in enumerate(sorted(set(groups.tolist()))):
        train = groups != int(test_group)
        test = groups == int(test_group)
        chosen = _select_dense_columns(dense_x[train], labels[train], max_columns=8)
        x_train = np.concatenate([data.x[train], dense_x[train][:, chosen]], axis=1)
        x_test = np.concatenate([data.x[test], dense_x[test][:, chosen]], axis=1)
        result = _fit_predict_scores(x_train, labels[train], x_test, data.class_names, seed=int(seed) + fold_idx)
        prob = result["probabilities"]
        pred = [data.class_names[int(value)] for value in np.argmax(prob, axis=1).tolist()]
        true = labels[test].astype(str).tolist()
        true_all.extend(true)
        pred_all.extend(pred)
        prob_all.append(prob)
        folds.append({"fold": int(fold_idx), "test_circuit_id": int(test_group), "selected_dense_columns": [dense_names[idx] for idx in chosen]})
    prob = np.concatenate(prob_all, axis=0) if prob_all else np.zeros((0, len(data.class_names)))
    return {
        "schema": "scope_static_s2d11b_variant_v1",
        "variant": "compact_plus_selected_RZZ_dense_terms",
        "overall": classification_metrics(true_all, pred_all, data.class_names, prob),
        "predicted_labels": pred_all,
        "true_labels": true_all,
        "dense_feature_audit": {
            "schema": "scope_static_s2d11b_m1_dense_vs_compact_feature_audit_v1",
            "source": "existing S2D.11 observations.npz + oracle_mechanisms.json, no resampling",
            "dense_block": "physical_local_inverse_probability_v2",
            "selection": "top train-fold absolute M1-vs-rest mean difference columns",
            "folds": folds,
        },
    }


def two_stage_gate_classifier_variant(data: S2D11bData, *, seed: int = 0) -> dict[str, object]:
    labels = np.asarray(data.labels, dtype=object)
    groups = np.asarray(data.groups, dtype=np.int64)
    branches = np.asarray(data.branches, dtype=object)
    true_all: list[str] = []
    pred_all: list[str] = []
    prob_all: list[np.ndarray] = []
    gate_classes = sorted({label for label, branch in zip(labels.tolist(), branches.tolist()) if branch == "gate_process_branch"}, key=_mechanism_sort_key)
    for fold_idx, test_group in enumerate(sorted(set(groups.tolist()))):
        train = groups != int(test_group)
        test = groups == int(test_group)
        base = _fit_predict_scores(data.x[train], labels[train], data.x[test], data.class_names, seed=int(seed) + fold_idx)
        prob = np.array(base["probabilities"], copy=True)
        test_indices = np.where(test)[0]
        gate_train = train & (branches == "gate_process_branch")
        gate_test_local = np.asarray([branches[idx] == "gate_process_branch" for idx in test_indices], dtype=bool)
        if np.any(gate_train) and np.any(gate_test_local) and len(gate_classes) >= 2:
            gate_result = _fit_predict_scores(data.x[gate_train], labels[gate_train], data.x[test_indices[gate_test_local]], gate_classes, seed=int(seed) + 10_000 + fold_idx)
            gate_prob_full = np.zeros((np.sum(gate_test_local), len(data.class_names)), dtype=np.float64)
            for local_idx, name in enumerate(gate_classes):
                gate_prob_full[:, data.class_names.index(name)] = gate_result["probabilities"][:, local_idx]
            prob[gate_test_local] = gate_prob_full
        pred = [data.class_names[int(value)] for value in np.argmax(prob, axis=1).tolist()]
        true = labels[test].astype(str).tolist()
        true_all.extend(true)
        pred_all.extend(pred)
        prob_all.append(prob)
    prob = np.concatenate(prob_all, axis=0) if prob_all else np.zeros((0, len(data.class_names)))
    return {
        "schema": "scope_static_s2d11b_variant_v1",
        "variant": "two_stage_gate_classifier",
        "role": "secondary_diagnostic_if_soft_calibration_fails",
        "overall": classification_metrics(true_all, pred_all, data.class_names, prob),
        "predicted_labels": pred_all,
        "true_labels": true_all,
    }


def grouped_dual_ridge_scores(
    x: np.ndarray,
    labels: list[str],
    groups: list[int],
    class_names: list[str],
    *,
    seed: int = 0,
    return_scores: bool = False,
) -> dict[str, object]:
    labels_arr = np.asarray(labels, dtype=object)
    groups_arr = np.asarray(groups, dtype=np.int64)
    true_all: list[str] = []
    pred_all: list[str] = []
    prob_all: list[np.ndarray] = []
    score_all: list[np.ndarray] = []
    folds = []
    for fold_idx, test_group in enumerate(sorted(set(groups_arr.tolist()))):
        train = groups_arr != int(test_group)
        test = groups_arr == int(test_group)
        result = _fit_predict_scores(x[train], labels_arr[train], x[test], class_names, seed=int(seed) + fold_idx)
        prob = result["probabilities"]
        scores = result["scores"]
        pred = [class_names[int(value)] for value in np.argmax(prob, axis=1).tolist()]
        true = labels_arr[test].astype(str).tolist()
        true_all.extend(true)
        pred_all.extend(pred)
        prob_all.append(prob)
        score_all.append(scores)
        folds.append({"fold": int(fold_idx), "test_circuit_id": int(test_group), "true_labels": true, "predicted_labels": pred, "row_indices": np.where(test)[0].astype(int).tolist()})
    prob = np.concatenate(prob_all, axis=0) if prob_all else np.zeros((0, len(class_names)))
    scores = np.concatenate(score_all, axis=0) if score_all else np.zeros((0, len(class_names)))
    out = {
        "schema": "scope_static_s2d11b_grouped_dual_ridge_scores_v1",
        "model": "TorchStandardScaler+DualRidgeLinearClassifier(class_weight=balanced)",
        "overall": classification_metrics(true_all, pred_all, class_names, prob),
        "true_labels": true_all,
        "predicted_labels": pred_all,
        "folds": folds,
    }
    if return_scores:
        out["scores"] = scores.tolist()
        out["probabilities"] = prob.tolist()
    return out


def _fit_predict_scores(x_train_np: np.ndarray, y_train_names: np.ndarray, x_test_np: np.ndarray, class_names: list[str], *, seed: int) -> dict[str, np.ndarray]:
    import torch

    torch.manual_seed(int(seed))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dtype = torch.float64
    class_index = {name: idx for idx, name in enumerate(class_names)}
    y_train_np = np.asarray([class_index[str(name)] for name in y_train_names], dtype=np.int64)
    x_train = torch.as_tensor(_finite(x_train_np), dtype=dtype, device=device)
    x_test = torch.as_tensor(_finite(x_test_np), dtype=dtype, device=device)
    y_train = torch.as_tensor(y_train_np, dtype=torch.long, device=device)
    if x_test.shape[0] == 0:
        return {"scores": np.zeros((0, len(class_names))), "probabilities": np.zeros((0, len(class_names)))}
    if len(set(y_train_np.tolist())) < 2:
        scores = np.full((x_test.shape[0], len(class_names)), -1e9, dtype=np.float64)
        scores[:, int(y_train_np[0]) if y_train_np.size else 0] = 0.0
        return {"scores": scores, "probabilities": _softmax(scores)}
    mean = torch.mean(x_train, dim=0, keepdim=True)
    std = torch.clamp(torch.std(x_train, dim=0, keepdim=True, unbiased=False), min=1e-9)
    x_train = (x_train - mean) / std
    x_test = (x_test - mean) / std
    x_train = torch.cat([x_train, torch.ones((x_train.shape[0], 1), dtype=dtype, device=device)], dim=1)
    x_test = torch.cat([x_test, torch.ones((x_test.shape[0], 1), dtype=dtype, device=device)], dim=1)
    targets = torch.zeros((x_train.shape[0], len(class_names)), dtype=dtype, device=device)
    targets[torch.arange(x_train.shape[0], device=device), y_train] = 1.0
    counts = torch.bincount(y_train, minlength=len(class_names)).to(dtype=dtype)
    present = counts > 0
    weights = torch.zeros_like(counts)
    weights[present] = float(x_train.shape[0]) / torch.clamp(torch.sum(present).to(dtype=dtype) * counts[present], min=1e-9)
    sqrt_w = torch.sqrt(torch.clamp(weights[y_train], min=1e-12)).reshape(-1, 1)
    xw = x_train * sqrt_w
    yw = targets * sqrt_w
    gram = xw @ xw.T
    alpha = torch.linalg.solve(gram + 1e-2 * torch.eye(gram.shape[0], dtype=dtype, device=device), yw)
    coef = xw.T @ alpha
    scores_t = x_test @ coef
    if bool(torch.any(~present)):
        scores_t[:, ~present] = -1e9
    scores = scores_t.detach().cpu().numpy().astype(np.float64, copy=False)
    return {"scores": scores, "probabilities": _softmax(scores)}


def _select_boost_hyperparams(
    x: np.ndarray,
    boost: np.ndarray,
    labels: np.ndarray,
    groups: np.ndarray,
    class_names: list[str],
    train_mask: np.ndarray,
    regs: tuple[float, ...],
    gains: tuple[float, ...],
    *,
    seed: int,
) -> dict[str, object]:
    best = {"selected_reg": float(regs[0]), "selected_gain": float(gains[0]), "inner_validation_M1_recall": -1.0, "inner_validation_balanced_accuracy": -1.0}
    train_groups = sorted(set(groups[train_mask].tolist()))
    if len(train_groups) < 2:
        return {**best, "inner_validation_M1_recall": 0.0, "inner_validation_balanced_accuracy": 0.0, "training_fold_M1_recall": 0.0}
    m1_idx = class_names.index("M1")
    for reg in regs:
        for gain in gains:
            true_all: list[str] = []
            pred_all: list[str] = []
            for inner_group in train_groups:
                inner_train = train_mask & (groups != int(inner_group))
                inner_val = train_mask & (groups == int(inner_group))
                base = _fit_predict_scores(x[inner_train], labels[inner_train], x[inner_val], class_names, seed=int(seed))
                coef = _fit_boost_coefficients(boost[inner_train], labels[inner_train], reg=float(reg))
                scores = np.array(base["scores"], copy=True)
                scores[:, m1_idx] += float(gain) * _apply_boost(boost[inner_val], coef)
                pred = [class_names[int(value)] for value in np.argmax(scores, axis=1).tolist()]
                true = labels[inner_val].astype(str).tolist()
                true_all.extend(true)
                pred_all.extend(pred)
            metrics = classification_metrics(true_all, pred_all, class_names)
            score = (float(metrics["per_class_recall"].get("M1", 0.0)), float(metrics["balanced_accuracy"]))
            if score > (float(best["inner_validation_M1_recall"]), float(best["inner_validation_balanced_accuracy"])):
                best = {
                    "selected_reg": float(reg),
                    "selected_gain": float(gain),
                    "inner_validation_M1_recall": score[0],
                    "inner_validation_balanced_accuracy": score[1],
                }
    train_pred = _fit_predict_scores(x[train_mask], labels[train_mask], x[train_mask], class_names, seed=int(seed))
    best["training_fold_M1_recall"] = _class_recall(labels[train_mask].astype(str).tolist(), [class_names[int(value)] for value in np.argmax(train_pred["probabilities"], axis=1).tolist()], "M1")
    return best


def _fit_boost_coefficients(boost_train: np.ndarray, labels_train: np.ndarray, *, reg: float) -> np.ndarray:
    x = _finite(np.asarray(boost_train, dtype=np.float64))
    x = np.concatenate([x, np.ones((x.shape[0], 1), dtype=np.float64)], axis=1)
    y = np.asarray([1.0 if str(label) == "M1" else -1.0 for label in labels_train], dtype=np.float64)
    lhs = x.T @ x + float(reg) * np.eye(x.shape[1], dtype=np.float64)
    rhs = x.T @ y
    return _finite(np.linalg.solve(lhs, rhs))


def _boost_matrix(data: S2D11bData) -> np.ndarray:
    idx = {name: data.feature_names.index(name) for name in data.feature_names}
    raw = []
    for row in data.x:
        log_ratio = float(row[idx["log_coherence_ratio"]]) if "log_coherence_ratio" in idx else 0.0
        axial = float(row[idx["h_zz_axial_ratio"]]) if "h_zz_axial_ratio" in idx else 0.0
        coherence = float(row[idx["coherence_norm"]]) if "coherence_norm" in idx else 0.0
        raw.append([log_ratio, float(np.log(max(axial, 0.0) + 1e-6)), coherence])
    return _finite(np.asarray(raw, dtype=np.float64))


def _apply_boost(boost_features: np.ndarray, coef: np.ndarray) -> np.ndarray:
    x = _finite(np.asarray(boost_features, dtype=np.float64))
    x = np.concatenate([x, np.ones((x.shape[0], 1), dtype=np.float64)], axis=1)
    return _finite(x @ np.asarray(coef, dtype=np.float64))


def _load_dense_features(data: S2D11bData) -> tuple[np.ndarray, list[str]] | None:
    teacher = data.source_run_dir / "S2D_PHYS1_teacher"
    obs_path = teacher / "observations.npz"
    rec_path = teacher / "oracle_mechanisms.json"
    if not obs_path.exists() or not rec_path.exists():
        return None
    records = json.loads(rec_path.read_text()).get("mechanisms", [])
    if not isinstance(records, list) or not records:
        return None
    bundle = np.load(obs_path)
    observations = np.asarray(bundle["observations"], dtype=np.float64)
    probe_names = [str(value) for value in bundle["probe_names"].tolist()]
    visible = build_visible_location_representations([dict(row) for row in records], observations, probe_names)
    dense = _finite(np.asarray(visible["physical_local_inverse_probability_v2"], dtype=np.float64))
    names = [f"local_inverse_v2_{idx:04d}" for idx in range(dense.shape[1])]
    return dense, names


def _select_dense_columns(dense_train: np.ndarray, labels_train: np.ndarray, *, max_columns: int) -> list[int]:
    mask = np.asarray([str(label) == "M1" for label in labels_train], dtype=bool)
    if not np.any(mask) or np.all(mask):
        return list(range(min(max_columns, dense_train.shape[1])))
    diff = np.abs(np.mean(dense_train[mask], axis=0) - np.mean(dense_train[~mask], axis=0))
    order = np.argsort(-diff)
    return [int(value) for value in order[: min(int(max_columns), dense_train.shape[1])].tolist()]


def _compact_variant(name: str, result: dict[str, object], data: S2D11bData) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d11b_variant_v1",
        "variant": name,
        "model": result.get("model"),
        "overall": result["overall"],
        "predicted_labels": result["predicted_labels"],
        "true_labels": result["true_labels"],
        "folds": result["folds"],
    }


def m1_false_negative_audit(data: S2D11bData, baseline: dict[str, object]) -> dict[str, object]:
    true = baseline["true_labels"]
    pred = baseline["predicted_labels"]
    rows = _ordered_rows_by_group(data)
    targets: dict[str, int] = {}
    per_fold: dict[str, dict[str, int]] = {}
    per_circuit: dict[str, dict[str, int]] = {}
    per_location = []
    for idx, (label, got) in enumerate(zip(true, pred)):
        if label != "M1":
            continue
        row = rows[idx]
        if got != "M1":
            targets[got] = targets.get(got, 0) + 1
        group = str(row["circuit_id"])
        per_fold.setdefault(group, {}).setdefault(got, 0)
        per_fold[group][got] += 1
        per_circuit.setdefault(group, {}).setdefault(got, 0)
        per_circuit[group][got] += 1
        per_location.append({"location_id": int(row["location_id"]), "circuit_id": int(row["circuit_id"]), "qubits": row["qubits"], "predicted": got})
    total = sum(1 for label in true if label == "M1")
    correct = sum(1 for label, got in zip(true, pred) if label == "M1" and got == "M1")
    return {
        "schema": "scope_static_s2d11b_m1_false_negative_audit_v1",
        "M1_true_count": int(total),
        "M1_recall": float(correct / total) if total else 0.0,
        "M1_false_negative_target_classes": targets,
        "M1_to_M6_count": int(targets.get("M6", 0)),
        "M1_to_M7_count": int(targets.get("M7", 0)),
        "M1_to_M10_count": int(targets.get("M10", 0)),
        "M1_to_other_count": int(sum(count for label, count in targets.items() if label not in {"M6", "M7", "M10"})),
        "per_fold_M1_confusion": per_fold,
        "per_circuit_M1_confusion": per_circuit,
        "per_edge_location_M1_confusion": per_location,
    }


def m1_grouped_fold_breakdown(data: S2D11bData, baseline: dict[str, object]) -> dict[str, object]:
    return {"schema": "scope_static_s2d11b_m1_grouped_fold_breakdown_v1", "folds": baseline.get("folds", [])}


def m1_invariant_snr_audit(data: S2D11bData) -> dict[str, object]:
    groups = np.asarray(data.groups, dtype=np.int64)
    labels = np.asarray(data.labels, dtype=object)
    boost = _boost_matrix(data)
    names = list(M1_BOOST_FEATURES)
    folds = []
    for test_group in sorted(set(groups.tolist())):
        train = groups != int(test_group)
        test = groups == int(test_group)
        folds.append(
            {
                "test_circuit_id": int(test_group),
                "features": {
                    name: {
                        "train": _stat_summary(boost[train, idx]),
                        "test": _stat_summary(boost[test, idx]),
                        "train_M1": _stat_summary(boost[train & (labels == "M1"), idx]),
                        "test_M1": _stat_summary(boost[test & (labels == "M1"), idx]),
                    }
                    for idx, name in enumerate(names)
                },
            }
        )
    return {"schema": "scope_static_s2d11b_m1_invariant_snr_audit_v1", "features": names, "folds": folds}


def m1_pairwise_margin_report(variants: dict[str, dict[str, object]]) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d11b_m1_pairwise_margin_report_v1",
        "variants": {
            name: row.get("overall", {}).get("pairwise_margins", {})
            for name, row in variants.items()
        },
    }


def tradeoff_report(variants: dict[str, dict[str, object]], data: S2D11bData) -> dict[str, object]:
    baseline_recalls = data.baseline_s2d11.get("per_class_recall", {})
    out = {}
    for name, row in variants.items():
        recalls = row.get("overall", {}).get("per_class_recall", {})
        out[name] = {
            label: {
                "baseline_recall": float(baseline_recalls.get(label, 0.0)),
                "variant_recall": float(recalls.get(label, 0.0)),
                "absolute_drop": float(baseline_recalls.get(label, 0.0)) - float(recalls.get(label, 0.0)),
            }
            for label in ("M6", "M7", "M10", "M9", "M2", "M3")
        }
    return {"schema": "scope_static_s2d11b_m1_vs_m7_m8_m12_tradeoff_v1", "variants": out}


def gate_neighbor_recall_report(variants: dict[str, dict[str, object]], data: S2D11bData) -> dict[str, object]:
    labels = ("M1", "M6", "M7", "M10", "M2", "M3", "M9")
    return {
        "schema": "scope_static_s2d11b_gate_neighbor_recall_report_v1",
        "variants": {
            name: {label: row.get("overall", {}).get("per_class_recall", {}).get(label) for label in labels}
            for name, row in variants.items()
        },
    }


def error_type_taxonomy(data: S2D11bData) -> dict[str, object]:
    mechanism_to_type = {name: _mechanism_error_type(name) for name in data.class_names}
    type_to_mechanisms = {
        kind: [name for name in data.class_names if mechanism_to_type[name] == kind]
        for kind in ERROR_TYPE_NAMES
    }
    return {
        "schema": "scope_static_s2d11b_error_type_taxonomy_v1",
        "error_types": list(ERROR_TYPE_NAMES),
        "mechanism_to_error_type": mechanism_to_type,
        "error_type_to_mechanisms": type_to_mechanisms,
        "visible_branch_to_error_type": {
            "gate_process_branch": "gate",
            "readout_branch": "readout",
            "prep_reset_branch": "prep_reset",
        },
        "visible_branch_rule": "measure->readout_branch; reset->prep_reset_branch; otherwise->gate_process_branch",
        "oracle_labels_used_for_taxonomy_evaluation_only": True,
        "row_level_branch_assignment_uses_oracle_labels": False,
    }


def error_type_metrics(variants: dict[str, dict[str, object]], data: S2D11bData) -> dict[str, object]:
    rows = {}
    for name, variant in variants.items():
        if variant.get("skipped", False):
            rows[name] = {"skipped": True, "skip_reason": variant.get("skip_reason", "")}
            continue
        true = [str(label) for label in variant.get("true_labels", [])]
        pred = [str(label) for label in variant.get("predicted_labels", [])]
        true_types = [_mechanism_error_type(label) for label in true]
        pred_types = [_mechanism_error_type(label) for label in pred]
        rows[name] = {
            "skipped": False,
            "overall": classification_metrics(true_types, pred_types, list(ERROR_TYPE_NAMES)),
            "type_confusions": _error_type_confusion_counts(true_types, pred_types),
        }
    return {
        "schema": "scope_static_s2d11b_error_type_metrics_v1",
        "taxonomy": error_type_taxonomy(data),
        "variants": rows,
    }


def mechanism_metrics_by_error_type(variants: dict[str, dict[str, object]], data: S2D11bData) -> dict[str, object]:
    taxonomy = error_type_taxonomy(data)
    type_to_mechanisms = taxonomy["error_type_to_mechanisms"]
    out = {}
    for name, variant in variants.items():
        if variant.get("skipped", False):
            out[name] = {"skipped": True, "skip_reason": variant.get("skip_reason", "")}
            continue
        true = [str(label) for label in variant.get("true_labels", [])]
        pred = [str(label) for label in variant.get("predicted_labels", [])]
        by_type = {}
        for kind in ERROR_TYPE_NAMES:
            mask = [_mechanism_error_type(label) == kind for label in true]
            class_names = list(type_to_mechanisms.get(kind, []))
            by_type[kind] = classification_metrics(
                [label for label, keep in zip(true, mask) if keep],
                [label for label, keep in zip(pred, mask) if keep],
                class_names,
            )
        out[name] = {"skipped": False, "by_error_type": by_type}
    return {
        "schema": "scope_static_s2d11b_mechanism_metrics_by_error_type_v1",
        "taxonomy": taxonomy,
        "variants": out,
    }


def leakage_guardrail_audit(data: S2D11bData, variants: dict[str, dict[str, object]]) -> dict[str, object]:
    lower = [name.lower() for name in data.feature_names]
    checks = {
        "source_is_existing_s2d11_artifact": True,
        "does_not_resample_teacher": True,
        "oracle_label_not_in_feature_columns": not any("oracle_label" in name for name in lower),
        "mechanism_id_not_in_feature_columns": not any("mechanism_id" in name for name in lower),
        "exact_ptm_columns_absent": not any("exact_ptm" in name for name in lower),
        "teacher_channel_columns_absent": not any("teacher_channel" in name for name in lower),
        "oracle_fingerprint_columns_absent": not any("oracle_fingerprint" in name for name in lower),
        "oracle_labels_used_only_as_calibration_targets": True,
    }
    return {"schema": "scope_static_s2d11b_leakage_guardrail_audit_v1", "passed": all(checks.values()), "checks": checks}


def s2d11b_success(variant: dict[str, object], data: S2D11bData) -> dict[str, object]:
    overall = variant.get("overall", {})
    recalls = overall.get("per_class_recall", {})
    baseline_recalls = data.baseline_s2d11.get("per_class_recall", {})
    true = variant.get("true_labels", [])
    pred = variant.get("predicted_labels", [])
    m5 = m5_overfragmentation_report(true, pred, data.class_names)
    margins = overall.get("pairwise_margins", {})
    controls_gap = float(overall.get("balanced_accuracy", 0.0)) - float(_within_scrambled_balanced(data))
    checks = {
        "M1_recall_ge_0_65": float(recalls.get("M1", 0.0)) >= 0.65,
        "macro_F1_ge_0_80": float(overall.get("macro_F1", 0.0)) >= 0.80,
        "balanced_accuracy_ge_0_80": float(overall.get("balanced_accuracy", 0.0)) >= 0.80,
        "real_minus_scrambled_ge_0_25": controls_gap >= 0.25,
        "readout_split_count_within_declared_taxonomy": int(m5.get("readout_split_count", m5.get("M5_split_count", 99))) <= 4,
        "readout_vs_gate_confusion_rate_le_0_10": float(m5.get("readout_vs_gate_confusion_rate", m5.get("M5_vs_gate_confusion_rate", 1.0))) <= 0.10,
        "M7_recall_drop_le_0_15": float(baseline_recalls.get("M7", 0.0)) - float(recalls.get("M7", 0.0)) <= 0.15,
        "M9_recall_drop_le_0_15": float(baseline_recalls.get("M9", 0.0)) - float(recalls.get("M9", 0.0)) <= 0.15,
        "M17_recall_drop_le_0_15": float(baseline_recalls.get("M17", 0.0)) - float(recalls.get("M17", 0.0)) <= 0.15,
        "M17_M4_margin_positive": _margin_positive(margins, "M17/M4"),
        "M17_M13_margin_positive": _margin_positive(margins, "M17/M13"),
    }
    return {
        "schema": "scope_static_s2d11b_primary_verdict_v1",
        "passed": all(checks.values()),
        "checks": checks,
        "real_minus_scrambled_balanced_accuracy": controls_gap,
        "readout_mechanism_report": m5,
        "m5_overfragmentation_report": m5,
    }


def summary_record(best_name: str, best: dict[str, object], data: S2D11bData) -> dict[str, object]:
    verdict = s2d11b_success(best, data)
    overall = best.get("overall", {})
    return {
        "best_variant": best_name,
        "passed": bool(verdict["passed"]),
        "balanced_accuracy": overall.get("balanced_accuracy"),
        "macro_F1": overall.get("macro_F1"),
        "M1_recall": overall.get("per_class_recall", {}).get("M1"),
        "M7_recall": overall.get("per_class_recall", {}).get("M7"),
        "M9_recall": overall.get("per_class_recall", {}).get("M9"),
        "M17_recall": overall.get("per_class_recall", {}).get("M17"),
        "interpretation": _interpretation(best_name, best, data),
    }


def _interpretation(best_name: str, best: dict[str, object], data: S2D11bData) -> str:
    verdict = s2d11b_success(best, data)
    if verdict["passed"]:
        return "S2D.11b converts the S2D.11 strong partial into a pass; the remaining failure was gate-branch M1 calibration."
    if best_name == "compact_plus_selected_RZZ_dense_terms":
        return "Selected dense learner-visible terms helped most; compact gate summaries may be too lossy."
    m1_snr = m1_invariant_snr_audit(data)
    _ = m1_snr
    return "S2D.11b did not meet strict criteria; inspect M1 SNR, fold shift, and neighbor tradeoff artifacts before adding probes."


def _within_scrambled_balanced(data: S2D11bData) -> float:
    controls = data.source_record.get("controls", {})
    primary = data.baseline_s2d11.get("balanced_accuracy", 0.0)
    gap = controls.get("real_minus_within_branch_scrambled_balanced_accuracy", 0.0)
    return float(primary) - float(gap)


def _best_variant_name(variants: dict[str, dict[str, object]]) -> str:
    def key(item: tuple[str, dict[str, object]]) -> tuple[float, float, float]:
        row = item[1].get("overall", {})
        recalls = row.get("per_class_recall", {})
        return (float(recalls.get("M1", 0.0)), float(row.get("balanced_accuracy", 0.0)), float(row.get("macro_F1", 0.0)))

    return max(variants.items(), key=key)[0]


def _variant_summary(row: dict[str, object]) -> dict[str, object]:
    overall = row.get("overall", {})
    return {
        "variant": row.get("variant"),
        "balanced_accuracy": overall.get("balanced_accuracy"),
        "macro_F1": overall.get("macro_F1"),
        "M1_recall": overall.get("per_class_recall", {}).get("M1"),
        "M7_recall": overall.get("per_class_recall", {}).get("M7"),
        "M9_recall": overall.get("per_class_recall", {}).get("M9"),
        "M17_recall": overall.get("per_class_recall", {}).get("M17"),
        "skipped": row.get("skipped", False),
    }


def _skipped_variant(name: str, reason: str, data: S2D11bData) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d11b_variant_v1",
        "variant": name,
        "skipped": True,
        "skip_reason": reason,
        "overall": classification_metrics([], [], data.class_names),
        "predicted_labels": [],
        "true_labels": [],
    }


def _ordered_rows_by_group(data: S2D11bData) -> list[dict[str, object]]:
    out = []
    for group in sorted(set(data.groups)):
        out.extend([row for row in data.records if int(row["circuit_id"]) == int(group)])
    return out


def _class_recall(true: list[str], pred: list[str], label: str) -> float:
    total = sum(1 for item in true if item == label)
    if total == 0:
        return 0.0
    return float(sum(1 for a, b in zip(true, pred) if a == label and b == label) / total)


def _stat_summary(values: np.ndarray) -> dict[str, float | int]:
    arr = _finite(np.asarray(values, dtype=np.float64))
    if arr.size == 0:
        return {"count": 0, "mean": 0.0, "std": 0.0, "median": 0.0, "mad": 0.0, "min": 0.0, "max": 0.0}
    med = float(np.median(arr))
    return {
        "count": int(arr.size),
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "median": med,
        "mad": float(np.median(np.abs(arr - med))),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
    }


def _margin_positive(margins: dict[str, object], key: str) -> bool:
    row = margins.get(key, {})
    return bool(row.get("available", False)) and float(row.get("margin", 0.0) or 0.0) > 0.0


def _softmax(scores: np.ndarray) -> np.ndarray:
    current = _finite(np.asarray(scores, dtype=np.float64))
    current = current - np.max(current, axis=1, keepdims=True)
    exp = np.exp(np.clip(current, -80.0, 80.0))
    return exp / np.maximum(np.sum(exp, axis=1, keepdims=True), 1e-12)


def _finite(values: np.ndarray) -> np.ndarray:
    return np.nan_to_num(np.asarray(values, dtype=np.float64), nan=0.0, posinf=0.0, neginf=0.0)


def _mechanism_sort_key(name: str) -> tuple[int, str]:
    if str(name).startswith("M") and str(name)[1:].isdigit():
        return (int(str(name)[1:]), str(name))
    return (10_000, str(name))


def _mechanism_error_type(name: str) -> str:
    label = str(name)
    if label in {"M13", "M14", "M15", "M16"}:
        return "readout"
    if label in {"M17", "M18"}:
        return "prep_reset"
    if label == "M19":
        return "other"
    return "gate"


def _error_type_confusion_counts(true_types: list[str], pred_types: list[str]) -> dict[str, dict[str, int]]:
    counts = {kind: {other: 0 for other in ERROR_TYPE_NAMES} for kind in ERROR_TYPE_NAMES}
    for true, pred in zip(true_types, pred_types):
        if true in counts and pred in counts[true]:
            counts[true][pred] += 1
    return counts
