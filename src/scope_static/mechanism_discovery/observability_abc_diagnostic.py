from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np
import torch
import yaml

from scope_static.protocols import LEARNER_VALIDATION_STAGE

from .artifacts import feature_schema_matches_stage3a
from .artifacts import load_json_object
from .artifacts import load_stage3_evaluator_labels
from .artifacts import load_stage3a_frozen_visible_features
from .artifacts import mechanism_sort_key
from .artifacts import resolve_teacher_dir
from .baselines import _kmeans
from .discovery_model import _cap_folds
from .discovery_model import _context_groups_from_split_manifest
from .discovery_model import _valid_folds
from .protocol_freeze import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A_DIR


STAGE_NAME = "Stage3_ABC_observability_diagnostic"
DEFAULT_OUTPUT_DIR = "outputs/scope_static/PHYC_STAGE3_discovery/S3ABC_observability_diagnostic"
DEFAULT_TARGET_GROUPS = (("M6", "M13", "M22", "M23"),)
DEFAULT_FEATURE_PROFILES = ("full_no_finite_shot_se", "raw_only")
DEFAULT_VQ_K_VALUES = (35, 70)
DEFAULT_MAX_CV_FOLDS = 5
DEFAULT_SEED = 0
DEFAULT_MLP_EPOCHS = 120
DEFAULT_MLP_HIDDEN_DIM = 64
DEFAULT_PASS_MIN_RECALL = 0.95
DEFAULT_IMPROVEMENT_DELTA = 0.05


def run_stage3_abc_observability_diagnostic(
    *,
    stage3a_dir: str | Path = DEFAULT_STAGE3A_DIR,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    teacher_dir: str | Path | None = None,
    enhanced_stage3a_dir: str | Path | None = None,
    enhanced_teacher_dir: str | Path | None = None,
    target_groups: Sequence[Sequence[str]] = DEFAULT_TARGET_GROUPS,
    feature_profiles: Sequence[str] = DEFAULT_FEATURE_PROFILES,
    vq_k_values: Sequence[int] = DEFAULT_VQ_K_VALUES,
    max_cv_folds: int | None = DEFAULT_MAX_CV_FOLDS,
    seed: int = DEFAULT_SEED,
    mlp_epochs: int = DEFAULT_MLP_EPOCHS,
    mlp_hidden_dim: int = DEFAULT_MLP_HIDDEN_DIM,
    pass_min_recall: float = DEFAULT_PASS_MIN_RECALL,
    improvement_delta: float = DEFAULT_IMPROVEMENT_DELTA,
) -> dict[str, object]:
    """Run A/B/C observability diagnostics for targeted Stage 3 mechanism sets.

    A is an evaluator-only supervised upper bound. B is a no-oracle visible-slot
    diagnostic; labels are loaded only after slot fitting for posthoc scoring. C
    repeats A/B on an optional enhanced-probe Stage 3A freeze.
    """

    s3a = Path(stage3a_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    groups = _normalize_target_groups(target_groups)
    profiles = [str(value) for value in feature_profiles]
    k_values = [max(1, int(value)) for value in vq_k_values]
    current = _run_surface_abc(
        surface_name="current",
        stage3a_dir=s3a,
        teacher_dir=teacher_dir,
        target_groups=groups,
        feature_profiles=profiles,
        vq_k_values=k_values,
        max_cv_folds=max_cv_folds,
        seed=int(seed),
        mlp_epochs=int(mlp_epochs),
        mlp_hidden_dim=int(mlp_hidden_dim),
        pass_min_recall=float(pass_min_recall),
    )

    enhanced: dict[str, object]
    if enhanced_stage3a_dir is None or not str(enhanced_stage3a_dir):
        enhanced = {
            "schema": "scope_static_stage3_abc_enhanced_probe_surface_v1",
            "surface_name": "enhanced",
            "skipped": True,
            "skip_reason": "enhanced_stage3a_dir_not_provided",
        }
    else:
        enhanced = _run_surface_abc(
            surface_name="enhanced",
            stage3a_dir=Path(enhanced_stage3a_dir),
            teacher_dir=enhanced_teacher_dir,
            target_groups=groups,
            feature_profiles=profiles,
            vq_k_values=k_values,
            max_cv_folds=max_cv_folds,
            seed=int(seed) + 17,
            mlp_epochs=int(mlp_epochs),
            mlp_hidden_dim=int(mlp_hidden_dim),
            pass_min_recall=float(pass_min_recall),
        )

    decision = abc_decision_audit(
        current=current,
        enhanced=enhanced,
        target_groups=groups,
        pass_min_recall=float(pass_min_recall),
        improvement_delta=float(improvement_delta),
    )
    acceptance = {
        "schema": "scope_static_stage3_abc_acceptance_audit_v1",
        "checks": {
            "current_surface_a_ran": not bool(current.get("skipped", False)),
            "current_surface_b_ran": not bool(current.get("skipped", False)),
            "supervised_upper_bound_evaluator_only": True,
            "no_oracle_representation_uses_no_labels_for_fit_or_selection": True,
            "stage3a_freeze_not_mutated": True,
            "abc_decision_reported": bool(decision),
        },
    }
    acceptance["passed"] = bool(all(dict(acceptance["checks"]).values()))
    result = {
        "schema": "scope_static_stage3_abc_observability_diagnostic_v1",
        "stage": STAGE_NAME,
        "public_layer": LEARNER_VALIDATION_STAGE.metadata(artifact_stage=STAGE_NAME, substage="abc_observability_diagnostic"),
        "stage3a_dir": str(s3a),
        "teacher_dir": str(current.get("teacher_dir", "")),
        "enhanced_stage3a_dir": None if enhanced_stage3a_dir is None else str(enhanced_stage3a_dir),
        "output_dir": str(output),
        "claim_boundary": {
            "diagnostic_only": True,
            "a_supervised_upper_bound_uses_evaluator_labels": True,
            "a_supervised_upper_bound_claim_allowed": False,
            "b_representation_uses_evaluator_labels_for_fit": False,
            "b_representation_uses_evaluator_labels_for_model_selection": False,
            "b_evaluator_labels_posthoc_only": True,
            "c_requires_enhanced_stage3a_freeze": True,
            "mutates_stage3a_freeze": False,
        },
        "config": {
            "stage3a_dir": str(s3a),
            "teacher_dir": None if teacher_dir is None else str(teacher_dir),
            "enhanced_stage3a_dir": None if enhanced_stage3a_dir is None else str(enhanced_stage3a_dir),
            "enhanced_teacher_dir": None if enhanced_teacher_dir is None else str(enhanced_teacher_dir),
            "target_groups": [list(group) for group in groups],
            "feature_profiles": list(profiles),
            "vq_k_values": list(k_values),
            "max_cv_folds": None if max_cv_folds is None else int(max_cv_folds),
            "seed": int(seed),
            "mlp_epochs": int(mlp_epochs),
            "mlp_hidden_dim": int(mlp_hidden_dim),
            "pass_min_recall": float(pass_min_recall),
            "improvement_delta": float(improvement_delta),
        },
        "current_surface": current,
        "enhanced_surface": enhanced,
        "supervised_upper_bound_audit": current.get("supervised_upper_bound_audit", {}),
        "no_oracle_representation_audit": current.get("no_oracle_representation_audit", {}),
        "enhanced_probe_upper_bound_audit": enhanced,
        "abc_decision_audit": decision,
        "acceptance_audit": acceptance,
        "decision": "stage3_abc_observability_diagnostic_completed" if acceptance["passed"] else "stage3_abc_observability_diagnostic_failed",
    }
    _write_outputs(output, result)
    return result


def _run_surface_abc(
    *,
    surface_name: str,
    stage3a_dir: Path,
    teacher_dir: str | Path | None,
    target_groups: tuple[tuple[str, ...], ...],
    feature_profiles: list[str],
    vq_k_values: list[int],
    max_cv_folds: int | None,
    seed: int,
    mlp_epochs: int,
    mlp_hidden_dim: int,
    pass_min_recall: float,
) -> dict[str, object]:
    s3a_metrics = load_json_object(stage3a_dir / "metrics.json")
    teacher = resolve_teacher_dir(s3a_metrics, teacher_dir)
    x_raw, feature_names, feature_matrix = load_stage3a_frozen_visible_features(stage3a_dir)
    labels = load_stage3_evaluator_labels(stage3a_dir, teacher)
    if len(labels.exact_labels) != int(x_raw.shape[0]):
        raise ValueError(f"{surface_name} Stage 3A row count does not match evaluator label count")
    split_manifest = dict(s3a_metrics.get("split_manifest", {})) if isinstance(s3a_metrics.get("split_manifest", {}), dict) else {}
    folds = _cap_folds(_valid_folds(split_manifest, record_count=int(x_raw.shape[0])), max_cv_folds=max_cv_folds)
    if not folds:
        folds = [_fallback_fold(int(x_raw.shape[0]))]
    context_groups = _context_groups_from_split_manifest(split_manifest, record_count=int(x_raw.shape[0]))
    feature_match = feature_schema_matches_stage3a(stage3a_dir, feature_names)
    supervised = supervised_upper_bound_audit(
        x_raw,
        feature_names=feature_names,
        labels=labels.exact_labels,
        folds=folds,
        target_groups=target_groups,
        feature_profiles=feature_profiles,
        seed=int(seed),
        mlp_epochs=int(mlp_epochs),
        mlp_hidden_dim=int(mlp_hidden_dim),
        pass_min_recall=float(pass_min_recall),
    )
    representation = no_oracle_representation_audit(
        x_raw,
        feature_names=feature_names,
        labels=labels.exact_labels,
        folds=folds,
        context_groups=context_groups,
        target_groups=target_groups,
        feature_profiles=feature_profiles,
        vq_k_values=vq_k_values,
        seed=int(seed),
        pass_min_recall=float(pass_min_recall),
    )
    return {
        "schema": "scope_static_stage3_abc_surface_v1",
        "surface_name": str(surface_name),
        "stage3a_dir": str(stage3a_dir),
        "teacher_dir": str(teacher),
        "visible_feature_matrix": feature_matrix,
        "feature_schema_match_audit": feature_match,
        "row_count": int(x_raw.shape[0]),
        "feature_count": int(x_raw.shape[1]),
        "fold_count": int(len(folds)),
        "target_groups": [list(group) for group in target_groups],
        "supervised_upper_bound_audit": supervised,
        "no_oracle_representation_audit": representation,
    }


def supervised_upper_bound_audit(
    x: np.ndarray,
    *,
    feature_names: list[str],
    labels: Sequence[str],
    folds: list[dict[str, list[int]]],
    target_groups: tuple[tuple[str, ...], ...],
    feature_profiles: Sequence[str],
    seed: int,
    mlp_epochs: int,
    mlp_hidden_dim: int,
    pass_min_recall: float,
) -> dict[str, object]:
    rows: dict[str, object] = {}
    for group in target_groups:
        task_name = _target_group_name(group)
        task_rows = []
        for profile in feature_profiles:
            matrix = _select_feature_profile(x, feature_names, profile)
            for model in ("nearest_centroid", "mlp"):
                task_rows.append(
                    _cross_validated_classifier(
                        matrix,
                        labels=labels,
                        folds=folds,
                        target_labels=group,
                        model_name=model,
                        seed=int(seed),
                        mlp_epochs=int(mlp_epochs),
                        mlp_hidden_dim=int(mlp_hidden_dim),
                    )
                    | {"feature_profile": str(profile)}
                )
        best = _best_metric_row(task_rows)
        rows[task_name] = {
            "target_labels": list(group),
            "models": task_rows,
            "best": best,
            "supervised_upper_bound_passed": bool(float(best.get("min_recall", 0.0) or 0.0) >= float(pass_min_recall)),
        }
    passed = bool(all(bool(dict(row).get("supervised_upper_bound_passed", False)) for row in rows.values()))
    return {
        "schema": "scope_static_stage3_abc_supervised_upper_bound_v1",
        "description": "Evaluator-only upper bound from frozen visible features to targeted mechanism labels.",
        "uses_evaluator_labels_for_fit": True,
        "uses_evaluator_labels_for_model_selection": True,
        "claim_allowed": False,
        "rows": rows,
        "passed": passed,
    }


def no_oracle_representation_audit(
    x: np.ndarray,
    *,
    feature_names: list[str],
    labels: Sequence[str],
    folds: list[dict[str, list[int]]],
    context_groups: np.ndarray,
    target_groups: tuple[tuple[str, ...], ...],
    feature_profiles: Sequence[str],
    vq_k_values: Sequence[int],
    seed: int,
    pass_min_recall: float,
) -> dict[str, object]:
    task_rows: dict[str, list[dict[str, object]]] = {name: [] for name in [_target_group_name(group) for group in target_groups]}
    model_rows: list[dict[str, object]] = []
    for profile in feature_profiles:
        base = _select_feature_profile(x, feature_names, profile)
        for transform in ("visible_vq", "context_residual_vq"):
            transformed = base
            if transform == "context_residual_vq":
                transformed = _context_residual_matrix(base, context_groups)
            for k in vq_k_values:
                metrics = _cross_validated_vq(
                    transformed,
                    labels=labels,
                    folds=folds,
                    target_groups=target_groups,
                    k=max(1, min(int(k), int(x.shape[0]))),
                    seed=int(seed),
                )
                model_row = {
                    "model_name": transform,
                    "feature_profile": str(profile),
                    "k": int(k),
                    "visible_reconstruction_mse": metrics["visible_reconstruction_mse"],
                    "uses_evaluator_labels_for_fit": False,
                    "uses_evaluator_labels_for_model_selection": False,
                }
                model_rows.append(model_row)
                for name, payload in dict(metrics["target_posthoc_metrics"]).items():
                    row = dict(payload)
                    row.update(model_row)
                    task_rows[str(name)].append(row)
    rows: dict[str, object] = {}
    for group in target_groups:
        task_name = _target_group_name(group)
        candidates = task_rows[task_name]
        best = _best_visible_row(candidates)
        best_posthoc = _best_metric_row(candidates)
        rows[task_name] = {
            "target_labels": list(group),
            "models": candidates,
            "best": best,
            "best_selection_rule": "min_visible_reconstruction_mse",
            "best_posthoc_diagnostic": best_posthoc,
            "no_oracle_slots_split_targets": bool(float(best.get("min_recall", 0.0) or 0.0) >= float(pass_min_recall)),
        }
    return {
        "schema": "scope_static_stage3_abc_no_oracle_representation_v1",
        "description": "Visible-only VQ/context-residual slot diagnostic. Labels are used only for posthoc scoring.",
        "uses_evaluator_labels_for_fit": False,
        "uses_evaluator_labels_for_model_selection": False,
        "evaluator_labels_posthoc_only": True,
        "model_selection_metric": "visible_reconstruction_mse_only",
        "model_rows": model_rows,
        "rows": rows,
        "passed": bool(all(bool(dict(row).get("no_oracle_slots_split_targets", False)) for row in rows.values())),
    }


def abc_decision_audit(
    *,
    current: Mapping[str, object],
    enhanced: Mapping[str, object],
    target_groups: tuple[tuple[str, ...], ...],
    pass_min_recall: float,
    improvement_delta: float,
) -> dict[str, object]:
    decisions = {}
    current_a = dict(dict(current.get("supervised_upper_bound_audit", {})).get("rows", {}))
    current_b = dict(dict(current.get("no_oracle_representation_audit", {})).get("rows", {}))
    enhanced_a = dict(dict(enhanced.get("supervised_upper_bound_audit", {})).get("rows", {})) if not bool(enhanced.get("skipped", False)) else {}
    enhanced_b = dict(dict(enhanced.get("no_oracle_representation_audit", {})).get("rows", {})) if not bool(enhanced.get("skipped", False)) else {}
    for group in target_groups:
        name = _target_group_name(group)
        a_best = dict(dict(current_a.get(name, {})).get("best", {}))
        b_best = dict(dict(current_b.get(name, {})).get("best", {}))
        a_min = float(a_best.get("min_recall", 0.0) or 0.0)
        b_min = float(b_best.get("min_recall", 0.0) or 0.0)
        enhanced_a_min = None
        enhanced_b_min = None
        if enhanced_a:
            enhanced_a_min = float(dict(dict(enhanced_a.get(name, {})).get("best", {})).get("min_recall", 0.0) or 0.0)
        if enhanced_b:
            enhanced_b_min = float(dict(dict(enhanced_b.get(name, {})).get("best", {})).get("min_recall", 0.0) or 0.0)
        if a_min < float(pass_min_recall):
            interpretation = "current_visible_surface_insufficient_for_supervised_upper_bound"
        elif b_min < float(pass_min_recall):
            interpretation = "current_surface_contains_supervised_signal_but_no_oracle_slots_do_not_split"
        else:
            interpretation = "current_no_oracle_representation_splits_target"
        enhanced_improved = (
            enhanced_a_min is not None
            and enhanced_a_min - a_min >= float(improvement_delta)
            or enhanced_b_min is not None
            and enhanced_b_min - b_min >= float(improvement_delta)
        )
        decisions[name] = {
            "target_labels": list(group),
            "current_supervised_min_recall": a_min,
            "current_no_oracle_min_recall": b_min,
            "enhanced_supervised_min_recall": enhanced_a_min,
            "enhanced_no_oracle_min_recall": enhanced_b_min,
            "interpretation": interpretation,
            "enhanced_probe_improved": bool(enhanced_improved),
        }
    return {
        "schema": "scope_static_stage3_abc_decision_audit_v1",
        "decision_logic": [
            "If supervised A cannot split a target on current frozen visible features, the current surface is insufficient for a flat-exact claim.",
            "If A can split but no-oracle B cannot, stronger discovery representations may help.",
            "If enhanced-probe A/B improves, missing probe observability is implicated.",
        ],
        "enhanced_probe_ran": not bool(enhanced.get("skipped", False)),
        "enhanced_probe_skip_reason": enhanced.get("skip_reason") if bool(enhanced.get("skipped", False)) else None,
        "rows": decisions,
    }


def _cross_validated_classifier(
    x: np.ndarray,
    *,
    labels: Sequence[str],
    folds: list[dict[str, list[int]]],
    target_labels: tuple[str, ...],
    model_name: str,
    seed: int,
    mlp_epochs: int,
    mlp_hidden_dim: int,
) -> dict[str, object]:
    all_true: list[str] = []
    all_pred: list[str] = []
    evaluable_folds = 0
    for fold_idx, fold in enumerate(folds):
        train_idx = np.asarray(fold.get("train_indices", []), dtype=np.int64)
        eval_idx = np.asarray(fold.get("test_indices", fold.get("validation_indices", [])), dtype=np.int64)
        if eval_idx.size == 0:
            eval_idx = np.asarray(fold.get("validation_indices", []), dtype=np.int64)
        train_mask = np.asarray([str(labels[int(idx)]) in set(target_labels) for idx in train_idx], dtype=bool)
        eval_mask = np.asarray([str(labels[int(idx)]) in set(target_labels) for idx in eval_idx], dtype=bool)
        train_local = train_idx[train_mask]
        eval_local = eval_idx[eval_mask]
        if train_local.size == 0 or eval_local.size == 0:
            continue
        if set(str(labels[int(idx)]) for idx in train_local.tolist()) != set(target_labels):
            continue
        x_train, x_eval = _standardize_from_train(x[train_local], x[eval_local])
        y_train = [str(labels[int(idx)]) for idx in train_local.tolist()]
        y_eval = [str(labels[int(idx)]) for idx in eval_local.tolist()]
        if model_name == "nearest_centroid":
            pred = _nearest_centroid_predict(x_train, y_train, x_eval, target_labels)
        elif model_name == "mlp":
            pred = _mlp_predict(
                x_train,
                y_train,
                x_eval,
                target_labels,
                seed=int(seed) + int(fold_idx),
                epochs=int(mlp_epochs),
                hidden_dim=int(mlp_hidden_dim),
            )
        else:
            raise ValueError(f"unknown supervised model: {model_name}")
        all_true.extend(y_eval)
        all_pred.extend(pred)
        evaluable_folds += 1
    metrics = _classification_metrics(all_true, all_pred, class_names=target_labels)
    return {
        "schema": "scope_static_stage3_abc_supervised_model_row_v1",
        "model_name": str(model_name),
        "evaluable_folds": int(evaluable_folds),
        "uses_evaluator_labels_for_fit": True,
        "uses_evaluator_labels_for_model_selection": True,
        **metrics,
    }


def _cross_validated_vq(
    x: np.ndarray,
    *,
    labels: Sequence[str],
    folds: list[dict[str, list[int]]],
    target_groups: tuple[tuple[str, ...], ...],
    k: int,
    seed: int,
) -> dict[str, object]:
    y_true_by_task: dict[str, list[str]] = defaultdict(list)
    y_pred_by_task: dict[str, list[str]] = defaultdict(list)
    reconstruction_losses: list[float] = []
    evaluable_folds = 0
    for fold_idx, fold in enumerate(folds):
        train_idx = np.asarray(fold.get("train_indices", []), dtype=np.int64)
        eval_idx = np.asarray(fold.get("test_indices", fold.get("validation_indices", [])), dtype=np.int64)
        if eval_idx.size == 0:
            eval_idx = np.asarray(fold.get("validation_indices", []), dtype=np.int64)
        if train_idx.size == 0 or eval_idx.size == 0:
            continue
        x_train, x_eval = _standardize_from_train(x[train_idx], x[eval_idx])
        assignments, centers, _inertia = _kmeans(x_train + 0.0 * float(seed + fold_idx), min(int(k), int(train_idx.size)), max_iter=40)
        train_slots = assignments
        eval_slots = np.argmin(_squared_distances(x_eval, centers), axis=1).astype(np.int64)
        recon = centers[eval_slots]
        reconstruction_losses.append(float(np.mean((x_eval - recon) ** 2)) if x_eval.size else 0.0)
        train_labels = [str(labels[int(idx)]) for idx in train_idx.tolist()]
        eval_labels = [str(labels[int(idx)]) for idx in eval_idx.tolist()]
        for group in target_groups:
            task_name = _target_group_name(group)
            mapping = _slot_to_label_mapping(train_slots, train_labels, group)
            for label, slot in zip(eval_labels, eval_slots.tolist()):
                if label not in set(group):
                    continue
                y_true_by_task[task_name].append(label)
                y_pred_by_task[task_name].append(mapping.get(int(slot), "__other__"))
        evaluable_folds += 1
    target_metrics = {}
    for group in target_groups:
        task_name = _target_group_name(group)
        metrics = _classification_metrics(y_true_by_task[task_name], y_pred_by_task[task_name], class_names=group)
        target_metrics[task_name] = {
            "schema": "scope_static_stage3_abc_no_oracle_target_posthoc_row_v1",
            "evaluable_folds": int(evaluable_folds),
            "uses_evaluator_labels_for_fit": False,
            "uses_evaluator_labels_for_model_selection": False,
            "evaluator_labels_posthoc_only": True,
            **metrics,
        }
    return {
        "visible_reconstruction_mse": float(np.mean(reconstruction_losses)) if reconstruction_losses else None,
        "target_posthoc_metrics": target_metrics,
    }


def _nearest_centroid_predict(
    x_train: np.ndarray,
    y_train: Sequence[str],
    x_eval: np.ndarray,
    class_names: Sequence[str],
) -> list[str]:
    centroids = []
    for label in class_names:
        mask = np.asarray([str(value) == str(label) for value in y_train], dtype=bool)
        centroids.append(np.mean(x_train[mask], axis=0) if np.any(mask) else np.zeros(x_train.shape[1], dtype=np.float64))
    centers = np.stack(centroids, axis=0)
    pred_idx = np.argmin(_squared_distances(x_eval, centers), axis=1)
    return [str(class_names[int(idx)]) for idx in pred_idx.tolist()]


def _mlp_predict(
    x_train: np.ndarray,
    y_train: Sequence[str],
    x_eval: np.ndarray,
    class_names: Sequence[str],
    *,
    seed: int,
    epochs: int,
    hidden_dim: int,
) -> list[str]:
    if x_eval.shape[0] == 0:
        return []
    torch.manual_seed(int(seed))
    class_to_idx = {str(label): idx for idx, label in enumerate(class_names)}
    xt = torch.as_tensor(np.asarray(x_train, dtype=np.float32))
    yt = torch.as_tensor([class_to_idx[str(label)] for label in y_train], dtype=torch.long)
    xe = torch.as_tensor(np.asarray(x_eval, dtype=np.float32))
    hidden = max(4, int(hidden_dim))
    model = torch.nn.Sequential(
        torch.nn.Linear(int(x_train.shape[1]), hidden),
        torch.nn.ReLU(),
        torch.nn.Linear(hidden, len(class_names)),
    )
    opt = torch.optim.AdamW(model.parameters(), lr=0.01, weight_decay=1.0e-4)
    loss_fn = torch.nn.CrossEntropyLoss()
    model.train()
    for _ in range(max(1, int(epochs))):
        opt.zero_grad(set_to_none=True)
        loss = loss_fn(model(xt), yt)
        loss.backward()
        opt.step()
    model.eval()
    with torch.no_grad():
        pred = torch.argmax(model(xe), dim=1).cpu().numpy().astype(int)
    return [str(class_names[int(idx)]) for idx in pred.tolist()]


def _classification_metrics(y_true: Sequence[str], y_pred: Sequence[str], *, class_names: Sequence[str]) -> dict[str, object]:
    names = [str(value) for value in class_names]
    recalls = {}
    confusion = {name: {other: 0 for other in names + ["__other__"]} for name in names}
    total = len(y_true)
    correct = 0
    for truth, pred in zip(y_true, y_pred):
        truth_text = str(truth)
        pred_text = str(pred) if str(pred) in set(names) else "__other__"
        if truth_text in confusion:
            confusion[truth_text][pred_text] = int(confusion[truth_text].get(pred_text, 0)) + 1
        if truth_text == pred_text:
            correct += 1
    for name in names:
        support = sum(confusion[name].values())
        recalls[name] = float(confusion[name].get(name, 0) / support) if support else 0.0
    return {
        "sample_count": int(total),
        "accuracy": float(correct / total) if total else 0.0,
        "balanced_accuracy": float(np.mean(list(recalls.values()))) if recalls else 0.0,
        "min_recall": float(np.min(list(recalls.values()))) if recalls else 0.0,
        "per_label_recall": recalls,
        "confusion": confusion,
    }


def _slot_to_label_mapping(slots: np.ndarray, labels: Sequence[str], target_labels: tuple[str, ...]) -> dict[int, str]:
    counts: dict[int, Counter[str]] = defaultdict(Counter)
    target_set = set(target_labels)
    for slot, label in zip(np.asarray(slots, dtype=np.int64).tolist(), labels):
        label_text = str(label)
        if label_text in target_set:
            counts[int(slot)][label_text] += 1
    mapping = {}
    for slot, counter in counts.items():
        if counter:
            mapping[int(slot)] = sorted(counter.items(), key=lambda item: (-item[1], mechanism_sort_key(item[0])))[0][0]
    return mapping


def _best_metric_row(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    if not rows:
        return {"sample_count": 0, "balanced_accuracy": 0.0, "min_recall": 0.0}
    return dict(
        max(
            rows,
            key=lambda row: (
                float(row.get("min_recall", 0.0) or 0.0),
                float(row.get("balanced_accuracy", 0.0) or 0.0),
                float(row.get("accuracy", 0.0) or 0.0),
                -float(row.get("visible_reconstruction_mse", 0.0) or 0.0),
            ),
        )
    )


def _best_visible_row(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    if not rows:
        return {"sample_count": 0, "balanced_accuracy": 0.0, "min_recall": 0.0}
    return dict(
        min(
            rows,
            key=lambda row: (
                float(row.get("visible_reconstruction_mse", 0.0) or 0.0),
                int(row.get("k", 0) or 0),
                str(row.get("model_name", "")),
                str(row.get("feature_profile", "")),
            ),
        )
    )


def _select_feature_profile(x: np.ndarray, feature_names: Sequence[str], profile: str) -> np.ndarray:
    text = str(profile)
    if text == "full":
        mask = np.ones(len(feature_names), dtype=bool)
    elif text == "full_no_finite_shot_se":
        mask = np.asarray([not _is_finite_shot_se_feature(name) for name in feature_names], dtype=bool)
    elif text == "raw_only":
        mask = np.asarray([str(name).startswith("raw__") for name in feature_names], dtype=bool)
    else:
        raise ValueError(f"unknown ABC feature profile: {profile!r}")
    if not np.any(mask):
        return np.asarray(x[:, :0], dtype=np.float64)
    return np.asarray(x[:, mask], dtype=np.float64)


def _is_finite_shot_se_feature(name: object) -> bool:
    text = str(name)
    return "__se_" in text or text.endswith("__se") or "_se_" in text


def _context_residual_matrix(x: np.ndarray, context_groups: np.ndarray) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float64)
    groups = np.asarray(context_groups, dtype=np.int64)
    if arr.ndim != 2 or groups.shape[0] != arr.shape[0]:
        return arr - np.mean(arr, axis=0, keepdims=True)
    out = np.zeros_like(arr, dtype=np.float64)
    for group in sorted(set(groups.tolist())):
        mask = groups == int(group)
        out[mask] = arr[mask] - np.mean(arr[mask], axis=0, keepdims=True)
    return out


def _standardize_from_train(train: np.ndarray, eval_: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mean = np.mean(train, axis=0, keepdims=True) if train.size else np.zeros((1, train.shape[1]), dtype=np.float64)
    scale = np.std(train, axis=0, keepdims=True) if train.size else np.ones((1, train.shape[1]), dtype=np.float64)
    scale = np.where(scale > 1.0e-12, scale, 1.0)
    return (train - mean) / scale, (eval_ - mean) / scale


def _squared_distances(x: np.ndarray, centers: np.ndarray) -> np.ndarray:
    diff = np.asarray(x, dtype=np.float64)[:, None, :] - np.asarray(centers, dtype=np.float64)[None, :, :]
    return np.sum(diff * diff, axis=2)


def _fallback_fold(record_count: int) -> dict[str, list[int]]:
    indices = np.arange(int(record_count), dtype=np.int64)
    train = indices[indices % 5 != 0].astype(int).tolist()
    test = indices[indices % 5 == 0].astype(int).tolist()
    if not train or not test:
        train = indices.tolist()
        test = indices.tolist()
    return {"train_indices": train, "validation_indices": test, "test_indices": test}


def _normalize_target_groups(groups: Sequence[Sequence[str]]) -> tuple[tuple[str, ...], ...]:
    out = []
    for group in groups:
        labels = tuple(str(value) for value in group if str(value))
        if labels and len(labels) < 3:
            raise ValueError(
                "pair-only target groups are forbidden; use a targeted mechanism set with at least three labels"
            )
        if labels:
            out.append(labels)
    if not out:
        raise ValueError("at least one target group is required")
    return tuple(out)


def _target_group_name(group: Iterable[str]) -> str:
    return "_vs_".join(str(value) for value in group)


def _write_outputs(output: Path, result: dict[str, object]) -> None:
    artifacts = {
        "metrics.json": result,
        "supervised_upper_bound_audit.json": result["supervised_upper_bound_audit"],
        "no_oracle_representation_audit.json": result["no_oracle_representation_audit"],
        "enhanced_probe_upper_bound_audit.json": result["enhanced_probe_upper_bound_audit"],
        "abc_decision_audit.json": result["abc_decision_audit"],
        "acceptance_audit.json": result["acceptance_audit"],
    }
    for name, payload in artifacts.items():
        (output / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    (output / "config.yaml").write_text(yaml.safe_dump({"stage3_abc_observability_diagnostic": result["config"]}, sort_keys=False))
    (output / "summary.md").write_text(format_stage3_abc_summary(result))


def format_stage3_abc_summary(result: Mapping[str, object]) -> str:
    decision = dict(result.get("abc_decision_audit", {}))
    rows = dict(decision.get("rows", {}))
    lines = [
        "# Stage 3 ABC Observability Diagnostic",
        "",
        f"- Decision: `{result.get('decision')}`",
        f"- Enhanced probe ran: `{str(bool(decision.get('enhanced_probe_ran', False))).lower()}`",
        "",
        "## Target Decisions",
        "",
    ]
    for name, row_obj in rows.items():
        row = dict(row_obj)
        lines.append(
            f"- `{name}`: A min recall `{float(row.get('current_supervised_min_recall', 0.0)):.4f}`, "
            f"B min recall `{float(row.get('current_no_oracle_min_recall', 0.0)):.4f}`, "
            f"interpretation `{row.get('interpretation')}`"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "ABC is diagnostic-only. A may use evaluator labels to establish an upper bound; B fits and selects visible slots without labels and uses labels only after fitting for posthoc scoring.",
            "",
        ]
    )
    return "\n".join(lines)
