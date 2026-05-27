from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from scope_static.numerics import NUMERICAL_ZERO

from .generator_invariant_calibration import INVARIANT_FEATURES, generator_invariants_from_coordinates, ptm_unitarity
from .generator_space_calibration import GENERATOR_CORE, grouped_mahalanobis_prototype, residualize_by_design
from .local_pauli_lindblad import PAULI_LABELS
from .rzz_observability_ceiling import FeatureBlock, audit_labels_schema, features_schema, grouped_fold_audit
from .targeted_v3 import RZZ_FAMILY


BRANCH_NAMES = ("gate_process_branch", "readout_branch", "prep_reset_branch")
FORBIDDEN_FEATURE_TOKENS = ("oracle_label", "mechanism_id", "exact_ptm", "teacher_channel", "oracle_fingerprint")
M5_TAU = 0.10
READOUT_MECHANISM_IDS = ("M13", "M14", "M15", "M16")
PREP_RESET_MECHANISM_IDS = ("M17", "M18")
RZZ_FAMILY_IDS = ("M1", "M6", "M7", "M9")
LOCATION_FEATURES = ("location_qubit_mean", "location_span", "chain_position", "neighbor_rzz_count", "branch_gate", "branch_readout", "branch_prep_reset")
READOUT_FEATURES = (
    "readout_shape_norm",
    "readout_strength",
    "assignment_asymmetry_proxy",
    "readout_entropy",
    "readout_variance",
    "readout_x_minus_z",
    "readout_y_minus_z",
)
PREP_RESET_FEATURES = (
    "prep_fidelity_proxy",
    "prep_axis_bias_x",
    "prep_axis_bias_y",
    "prep_axis_bias_z",
    "initial_state_affine_shift",
    "reset_prep_asymmetry",
    "prep_confidence_proxy",
)
CONFIDENCE_FEATURES = ("feature_confidence", "feature_snr", "fit_residual_or_reconstruction_error", "low_confidence_flag")
INSTRUCTION_FEATURES = ("instruction_id", "instruction_rx", "instruction_rz", "instruction_rzz", "instruction_measure", "instruction_reset", "instruction_other")
SINGLE_QUBIT_RESPONSE_FEATURES = (
    "sq_response_mean",
    "sq_response_std",
    "sq_response_min",
    "sq_response_max",
    "sq_response_entropy",
    "sq_z_mean",
    "sq_x_mean",
    "sq_y_mean",
    "sq_x_minus_z",
    "sq_y_minus_z",
    "sq_x_minus_y",
    "sq_phase_visibility",
    "sq_population_visibility",
    "sq_basis_anisotropy",
)


@dataclass(frozen=True)
class TypedSpamGateBundle:
    feature_spaces: dict[str, np.ndarray]
    feature_names: dict[str, list[str]]
    labels: list[str]
    groups: list[int]
    records: list[dict[str, object]]
    branch_names: list[str]
    branch_assignment_audit: dict[str, object]
    branch_budget_audit: dict[str, object]
    grouped_fold_coverage_audit: dict[str, object]
    typed_branch_feature_manifest: dict[str, object]
    typed_branch_feature_schema_physics_visible: dict[str, object]
    audit_labels_schema_oracle_only: dict[str, object]
    gate_process_feature_table: dict[str, object]
    readout_branch_feature_table: dict[str, object]
    prep_reset_branch_feature_table: dict[str, object]
    single_qubit_invariant_reconstruction_audit: dict[str, object]
    m11_prep_observability_preflight: dict[str, object]
    m11_prep_feature_snr: dict[str, object]
    m11_vs_m4_preflight_margin: dict[str, object]
    prep_reconstruction_assumption_audit: dict[str, object]
    leakage_guardrail_audit: dict[str, object]


def build_typed_spam_gate_features(
    records: list[dict[str, object]],
    observations: np.ndarray,
    probe_names: Iterable[str],
    local_record: dict[str, object],
    *,
    enabled_mechanisms: list[str],
    seed: int = 0,
) -> TypedSpamGateBundle:
    obs = np.asarray(observations, dtype=np.float64)
    names = [str(name) for name in probe_names]
    labels = [str(record.get("oracle_label", "")) for record in records]
    groups = [int(record.get("circuit_id", 0)) for record in records]
    branches = [visible_branch(record) for record in records]
    local_rows = _local_rows(local_record)
    static_names = [
        *GENERATOR_CORE,
        *INVARIANT_FEATURES,
        *LOCATION_FEATURES,
        *INSTRUCTION_FEATURES,
        *SINGLE_QUBIT_RESPONSE_FEATURES,
        *READOUT_FEATURES,
        *PREP_RESET_FEATURES,
        *CONFIDENCE_FEATURES,
    ]
    base_names = list(static_names)
    real_rows = []
    within_rows = []
    cross_rows = []
    raw_rows = []
    invariant_rows = []
    gate_rows = []
    readout_rows = []
    prep_rows = []
    rng = np.random.default_rng(int(seed) + 111_000)
    branch_permutation = rng.permutation(np.arange(len(records))) if records else np.asarray([], dtype=int)
    for idx, record in enumerate(records):
        location_id = int(record.get("location_id", idx))
        local = local_rows.get(location_id, {})
        features = _record_features(record, obs, names, local)
        real = np.asarray([features.get(name, 0.0) for name in base_names], dtype=np.float64)
        raw = np.concatenate(
            [
                np.asarray([features.get(name, 0.0) for name in GENERATOR_CORE], dtype=np.float64),
                np.asarray([features.get(name, 0.0) for name in [*INSTRUCTION_FEATURES, *SINGLE_QUBIT_RESPONSE_FEATURES]], dtype=np.float64),
            ]
        )
        invariants = np.asarray([features.get(name, 0.0) for name in INVARIANT_FEATURES], dtype=np.float64)
        real_rows.append(real)
        raw_rows.append(raw)
        invariant_rows.append(invariants)
        if branches[idx] == "gate_process_branch":
            gate_rows.append(_feature_table_row(record, base_names, real))
        elif branches[idx] == "readout_branch":
            readout_rows.append(_feature_table_row(record, base_names, real))
        else:
            prep_rows.append(_feature_table_row(record, base_names, real))
    real_matrix = _finite(np.asarray(real_rows, dtype=np.float64))
    raw_matrix = _finite(np.asarray(raw_rows, dtype=np.float64))
    invariant_matrix = _finite(np.asarray(invariant_rows, dtype=np.float64))
    within_rows = [None for _ in records]
    for branch in BRANCH_NAMES:
        branch_indices = [idx for idx, current in enumerate(branches) if current == branch]
        if not branch_indices:
            continue
        local = np.array(real_matrix[branch_indices], copy=True)
        for col in range(local.shape[1]):
            rng.shuffle(local[:, col])
        for row_idx, original_idx in enumerate(branch_indices):
            within_rows[original_idx] = local[row_idx]
    for idx in range(len(records)):
        if within_rows[idx] is None:
            within_rows[idx] = real_matrix[idx]
        cross_source = int(branch_permutation[idx]) if idx < branch_permutation.size else idx
        cross_rows.append(real_matrix[cross_source])
    within_matrix = _finite(np.asarray(within_rows, dtype=np.float64))
    cross_matrix = _finite(np.asarray(cross_rows, dtype=np.float64))
    no_readout = _zero_branch(real_matrix, branches, "readout_branch")
    no_prep = _zero_branch(real_matrix, branches, "prep_reset_branch")
    flat_raw_plus_invariants = _finite(np.concatenate([raw_matrix, invariant_matrix], axis=1))
    feature_spaces = {
        "flat_raw_generator_or_local_inverse": raw_matrix,
        "flat_invariants_only": invariant_matrix,
        "flat_raw_plus_invariants": flat_raw_plus_invariants,
        "typed_gate_readout_prep_invariant_learner": real_matrix,
        "typed_without_readout_branch": no_readout,
        "typed_without_prep_branch": no_prep,
        "within_branch_scrambled_control": within_matrix,
        "cross_branch_scrambled_control": cross_matrix,
    }
    feature_names = {
        "flat_raw_generator_or_local_inverse": [*GENERATOR_CORE, *INSTRUCTION_FEATURES, *SINGLE_QUBIT_RESPONSE_FEATURES],
        "flat_invariants_only": list(INVARIANT_FEATURES),
        "flat_raw_plus_invariants": [*GENERATOR_CORE, *INSTRUCTION_FEATURES, *SINGLE_QUBIT_RESPONSE_FEATURES, *INVARIANT_FEATURES],
        "typed_gate_readout_prep_invariant_learner": base_names,
        "typed_without_readout_branch": base_names,
        "typed_without_prep_branch": base_names,
        "within_branch_scrambled_control": [f"within_scrambled_{name}" for name in base_names],
        "cross_branch_scrambled_control": [f"cross_scrambled_{name}" for name in base_names],
    }
    feature_blocks = {
        name: FeatureBlock(
            name,
            features,
            feature_names[name],
            ["s2d11_typed_spam_gate_invariant_features"],
            primary=name == "typed_gate_readout_prep_invariant_learner",
            control=name.endswith("_control"),
            explanatory=name not in {"typed_gate_readout_prep_invariant_learner", "within_branch_scrambled_control", "cross_branch_scrambled_control"},
        )
        for name, features in feature_spaces.items()
    }
    feature_schema = features_schema(feature_blocks, source_root="S2D.11_typed_SPAM_gate_invariant_learner")
    labels_schema = audit_labels_schema(labels, groups, records)
    return TypedSpamGateBundle(
        feature_spaces=feature_spaces,
        feature_names=feature_names,
        labels=labels,
        groups=groups,
        records=[dict(record) for record in records],
        branch_names=branches,
        branch_assignment_audit=branch_assignment_audit(records, branches),
        branch_budget_audit=branch_budget_audit(enabled_mechanisms, branches),
        grouped_fold_coverage_audit=grouped_fold_coverage_audit(records, labels, groups, branches),
        typed_branch_feature_manifest=typed_branch_feature_manifest(feature_names["typed_gate_readout_prep_invariant_learner"]),
        typed_branch_feature_schema_physics_visible=feature_schema,
        audit_labels_schema_oracle_only=labels_schema,
        gate_process_feature_table={"schema": "scope_static_s2d11_gate_process_feature_table_v1", "records": gate_rows},
        readout_branch_feature_table={"schema": "scope_static_s2d11_readout_branch_feature_table_v1", "records": readout_rows},
        prep_reset_branch_feature_table={"schema": "scope_static_s2d11_prep_reset_branch_feature_table_v1", "records": prep_rows},
        single_qubit_invariant_reconstruction_audit=single_qubit_invariant_reconstruction_audit(records, labels, feature_spaces["typed_gate_readout_prep_invariant_learner"], feature_names["typed_gate_readout_prep_invariant_learner"]),
        m11_prep_observability_preflight=m11_prep_observability_preflight(labels, feature_spaces["typed_gate_readout_prep_invariant_learner"], feature_names["typed_gate_readout_prep_invariant_learner"]),
        m11_prep_feature_snr=m11_prep_feature_snr(labels, feature_spaces["typed_gate_readout_prep_invariant_learner"], feature_names["typed_gate_readout_prep_invariant_learner"]),
        m11_vs_m4_preflight_margin=m11_vs_m4_preflight_margin(labels, feature_spaces["typed_gate_readout_prep_invariant_learner"], feature_names["typed_gate_readout_prep_invariant_learner"]),
        prep_reconstruction_assumption_audit=prep_reconstruction_assumption_audit(names),
        leakage_guardrail_audit=leakage_guardrail_audit(feature_schema),
    )


def evaluate_typed_spam_gate_learner(
    bundle: TypedSpamGateBundle,
    *,
    seed: int = 0,
    m5_tau: float = M5_TAU,
    include_m13: bool = False,
    include_m19: bool | None = None,
) -> dict[str, object]:
    labels = list(bundle.labels)
    groups = list(bundle.groups)
    class_names = sorted(set(labels), key=_mechanism_sort_key)
    branch_ablation = {}
    predictions = {}
    all_predictions = {}
    for name, features in bundle.feature_spaces.items():
        result = grouped_linear_head(features, labels, groups, class_names, seed=int(seed))
        branch_ablation[name] = _compact_head_result(result)
        predictions[name] = result["fold_predictions"]
        all_predictions[name] = result["all"]
    primary = branch_ablation["typed_gate_readout_prep_invariant_learner"]["overall"]
    within = branch_ablation["within_branch_scrambled_control"]["overall"]
    cross = branch_ablation["cross_branch_scrambled_control"]["overall"]
    heads = {
        "typed_linear_head": branch_ablation["typed_gate_readout_prep_invariant_learner"],
        "typed_prototype_head": grouped_prototype_head(bundle.feature_spaces["typed_gate_readout_prep_invariant_learner"], labels, groups, class_names),
        "typed_mahalanobis_prototype_head": grouped_mahalanobis_head(bundle.feature_spaces["typed_gate_readout_prep_invariant_learner"], labels, groups, class_names),
    }
    primary_pred = all_predictions["typed_gate_readout_prep_invariant_learner"]
    m5_report = m5_overfragmentation_report(labels, primary_pred["predicted_labels"], class_names, tau=float(m5_tau))
    m11_report = m11_readout_confound_audit(bundle, labels, groups, class_names, seed=int(seed))
    pairwise = pairwise_margin_report(primary.get("pairwise_margins", {}), heads)
    gate_audit = gate_family_audit(labels, primary_pred["predicted_labels"], class_names)
    controls = {
        "schema": "scope_static_s2d11_controls_v1",
        "real_minus_within_branch_scrambled_balanced_accuracy": float(primary["balanced_accuracy"] - within["balanced_accuracy"]),
        "real_minus_cross_branch_scrambled_balanced_accuracy": float(primary["balanced_accuracy"] - cross["balanced_accuracy"]),
        "primary_threshold_real_minus_within_branch_scrambled_ge_0_25": float(primary["balanced_accuracy"] - within["balanced_accuracy"]) >= 0.25,
    }
    success = s2d11_success(
        branch_ablation=branch_ablation,
        heads=heads,
        controls=controls,
        m5_report=m5_report,
        m11_report=m11_report,
        gate_audit=gate_audit,
        coverage=bundle.grouped_fold_coverage_audit,
    )
    supervised_grouped_ceiling = {
        "primary_feature_block": "typed_gate_readout_prep_invariant_learner",
        "primary_head": "typed_linear_head",
        "overall": primary,
        "grouped_fold_predictions": predictions["typed_gate_readout_prep_invariant_learner"],
    }
    run_m19_stress = bool(include_m13 if include_m19 is None else include_m19)
    m19_audit = m19_confidence_audit(bundle, labels, primary_pred["predicted_labels"], class_names) if run_m19_stress else {}
    secondary_stress = {
        "includes_M19_other_mechanism": run_m19_stress,
        "m19_confidence_audit": m19_audit,
        "includes_M13": False,
        "m13_confidence_audit": m19_audit,
    }
    return {
        "schema": "scope_static_s2d11_typed_spam_gate_evaluation_v1",
        "class_names": class_names,
        "supervised_grouped_ceiling": supervised_grouped_ceiling,
        "typed_heads": heads,
        "unsupervised_clustering": {"status": "not_run", "reason": "S2D.11 primary is grouped supervised ceiling plus typed prototype heads"},
        "branch_ablations": branch_ablation,
        "oracle_upper_bound": oracle_upper_bound_metrics(labels, class_names),
        "primary_verdict": success,
        "secondary_stress": secondary_stress,
        "branch_ablation_metrics": branch_ablation,
        "typed_metric_head_report": heads,
        "grouped_fold_predictions": predictions,
        "pairwise_margin_report": pairwise,
        "confusion_matrix_by_branch": confusion_matrix_by_branch(labels, primary_pred["predicted_labels"], bundle.branch_names, class_names),
        "readout_mechanism_audit": m5_report,
        "m5_readout_audit": m5_report,
        "m5_overfragmentation_report": m5_report,
        "m11_prep_reset_audit": m11_report,
        "m11_readout_confound_audit": m11_report,
        "single_qubit_invariant_reconstruction_audit": bundle.single_qubit_invariant_reconstruction_audit,
        "gate_family_audit": gate_audit,
        "oracle_upper_bound_metrics": oracle_upper_bound_metrics(labels, class_names),
        "scrambled_branch_control_audit": scrambled_branch_control_audit(branch_ablation, controls),
        "controls": controls,
        "run_success": success,
        "m13_confidence_audit": secondary_stress["m13_confidence_audit"],
        "m19_confidence_audit": secondary_stress["m19_confidence_audit"],
    }


def visible_branch(record: dict[str, object]) -> str:
    instruction = str(record.get("instruction", "")).lower()
    if instruction == "measure":
        return "readout_branch"
    if instruction == "reset":
        return "prep_reset_branch"
    return "gate_process_branch"


def branch_assignment_audit(records: list[dict[str, object]], branches: list[str]) -> dict[str, object]:
    rows = []
    for idx, (record, branch) in enumerate(zip(records, branches)):
        rows.append(
            {
                "location_id": int(record.get("location_id", idx)),
                "instruction": str(record.get("instruction", "")),
                "branch": str(branch),
                "uses_oracle_label": False,
                "rule": "measure->readout_branch; reset->prep_reset_branch; otherwise->gate_process_branch",
            }
        )
    return {"schema": "scope_static_s2d11_branch_assignment_audit_v1", "records": rows, "branch_counts": _counts(branches)}


def branch_budget_audit(enabled_mechanisms: list[str], branches: list[str]) -> dict[str, object]:
    enabled = [str(item) for item in enabled_mechanisms]
    readout_budget = sum(1 for item in enabled if item in READOUT_MECHANISM_IDS)
    prep_budget = sum(1 for item in enabled if item in PREP_RESET_MECHANISM_IDS)
    total = len(enabled)
    gate_budget = max(1, total - readout_budget - prep_budget)
    return {
        "schema": "scope_static_s2d11_branch_budget_audit_v1",
        "total_K": int(total),
        "enabled_visible_branches": sorted(set(branches)),
        "readout_budget_rule": "number of enabled readout mechanisms in M13/M14/M15/M16",
        "prep_reset_budget_rule": "number of enabled prep/reset mechanisms in M17/M18",
        "gate_budget_rule": "K - readout_budget - prep_reset_budget",
        "budget_source": "visible_run_config",
        "row_oracle_labels_used": False,
        "mechanism_id_used_per_row": False,
        "branch_assignment_source": "visible_instruction_type",
        "budgets": {"gate_process_branch": gate_budget, "readout_branch": readout_budget, "prep_reset_branch": prep_budget},
        "row_level_oracle_labels_used_for_branch_assignment": False,
        "row_level_oracle_labels_used_for_branch_budgeting": False,
    }


def grouped_fold_coverage_audit(records: list[dict[str, object]], labels: list[str], groups: list[int], branches: list[str]) -> dict[str, object]:
    mechanism_count_by_circuit = {}
    mechanism_count_by_pair = {}
    mechanism_count_by_branch = {}
    for idx, (record, label, group, branch) in enumerate(zip(records, labels, groups, branches)):
        mechanism_count_by_circuit.setdefault(str(label), {}).setdefault(str(group), 0)
        mechanism_count_by_circuit[str(label)][str(group)] += 1
        qubits = tuple(int(value) for value in record.get("qubits", []))
        pair = "-".join(str(value) for value in qubits) if qubits else "none"
        mechanism_count_by_pair.setdefault(str(label), {}).setdefault(pair, 0)
        mechanism_count_by_pair[str(label)][pair] += 1
        mechanism_count_by_branch.setdefault(str(label), {}).setdefault(str(branch), 0)
        mechanism_count_by_branch[str(label)][str(branch)] += 1
    fold_coverage = []
    for test_group in sorted(set(groups)):
        train_labels = sorted({label for label, group in zip(labels, groups) if int(group) != int(test_group)}, key=_mechanism_sort_key)
        test_labels = sorted({label for label, group in zip(labels, groups) if int(group) == int(test_group)}, key=_mechanism_sort_key)
        fold_coverage.append({"test_circuit_id": int(test_group), "train_mechanisms": train_labels, "test_mechanisms": test_labels})
    distinct_circuits = {label: len(counts) for label, counts in mechanism_count_by_circuit.items()}
    distinct_locations = {label: len(counts) for label, counts in mechanism_count_by_pair.items()}
    valid = bool(distinct_circuits) and min(distinct_circuits.values()) >= 2
    return {
        "schema": "scope_static_s2d11_grouped_fold_coverage_audit_v1",
        "mechanism_count_by_circuit_id": mechanism_count_by_circuit,
        "mechanism_count_by_qubit_pair": mechanism_count_by_pair,
        "mechanism_count_by_branch": mechanism_count_by_branch,
        "fold_train_test_mechanism_coverage": fold_coverage,
        "min_distinct_circuits_per_mechanism": int(min(distinct_circuits.values())) if distinct_circuits else 0,
        "min_distinct_locations_per_mechanism": int(min(distinct_locations.values())) if distinct_locations else 0,
        "valid_grouped_generalization": bool(valid),
        "hard_rule": "each primary mechanism must appear in at least 2 distinct circuit_id groups; prefer >=3",
    }


def grouped_linear_head(features: np.ndarray, labels: list[str], groups: list[int], class_names: list[str], *, seed: int = 0) -> dict[str, object]:
    import torch

    x = _finite(np.asarray(features, dtype=np.float64))
    y_names = np.asarray(labels, dtype=object)
    g = np.asarray(groups, dtype=np.int64)
    class_index = {name: idx for idx, name in enumerate(class_names)}
    y = np.asarray([class_index[str(name)] for name in y_names], dtype=np.int64)
    if len(class_names) < 2 or len(set(groups)) < 2:
        return _skipped_head("typed_linear_head", class_names)
    true_all = []
    pred_all = []
    prob_all = []
    folds = []
    for fold_idx, test_group in enumerate(sorted(set(g.tolist()))):
        train = g != int(test_group)
        test = g == int(test_group)
        present = sorted(set(int(value) for value in y[train].tolist()))
        if len(present) < 2:
            pred = np.full(np.sum(test), present[0] if present else 0, dtype=np.int64)
            prob = np.zeros((np.sum(test), len(class_names)), dtype=np.float64)
            prob[:, int(pred[0]) if pred.size else 0] = 1.0
        else:
            prob = _gpu_dual_ridge_probabilities(
                x[train],
                y[train],
                x[test],
                num_classes=len(class_names),
                seed=int(seed) + fold_idx,
            )
            pred = np.argmax(prob, axis=1)
        true_labels = [class_names[int(value)] for value in y[test].tolist()]
        pred_labels = [class_names[int(value)] for value in pred.tolist()]
        folds.append(
            {
                "fold": int(fold_idx),
                "test_circuit_id": int(test_group),
                "true_labels": true_labels,
                "predicted_labels": pred_labels,
                "probabilities": prob.tolist(),
            }
        )
        true_all.extend(true_labels)
        pred_all.extend(pred_labels)
        prob_all.append(prob)
    prob_matrix = np.concatenate(prob_all, axis=0) if prob_all else np.zeros((0, len(class_names)), dtype=np.float64)
    overall = classification_metrics(true_all, pred_all, class_names, prob_matrix)
    return {
        "model": "TorchStandardScaler+DualRidgeLinearClassifier(class_weight=balanced)",
        "linear_head_note": "GPU-friendly fold-local dual ridge solve used for few-row/high-dimensional PHYS3 feature tables.",
        "overall": overall,
        "fold_predictions": folds,
        "all": {"true_labels": true_all, "predicted_labels": pred_all},
    }


def grouped_prototype_head(features: np.ndarray, labels: list[str], groups: list[int], class_names: list[str]) -> dict[str, object]:
    return _grouped_distance_head(features, labels, groups, class_names, mahalanobis=False)


def grouped_mahalanobis_head(features: np.ndarray, labels: list[str], groups: list[int], class_names: list[str]) -> dict[str, object]:
    return _grouped_distance_head(features, labels, groups, class_names, mahalanobis=True)


def classification_metrics(true: list[str], pred: list[str], class_names: list[str], probabilities: np.ndarray | None = None) -> dict[str, object]:
    matrix = np.zeros((len(class_names), len(class_names)), dtype=np.int64)
    index = {name: idx for idx, name in enumerate(class_names)}
    support = {name: 0 for name in class_names}
    for a, b in zip(true, pred):
        if a in support:
            support[a] += 1
        if a in index and b in index:
            matrix[index[a], index[b]] += 1
    recalls = []
    f1s = []
    per_recall = {}
    for idx, name in enumerate(class_names):
        tp = float(matrix[idx, idx])
        fn = float(support[name] - matrix[idx, idx])
        fp = float(np.sum(matrix[:, idx]) - matrix[idx, idx])
        recall = tp / (tp + fn) if tp + fn > 0.0 else 0.0
        precision = tp / (tp + fp) if tp + fp > 0.0 else 0.0
        f1 = 2.0 * precision * recall / (precision + recall) if precision + recall > 0.0 else 0.0
        recalls.append(recall)
        f1s.append(f1)
        per_recall[name] = recall
    return {
        "balanced_accuracy": float(np.mean(recalls)) if recalls else 0.0,
        "macro_F1": float(np.mean(f1s)) if f1s else 0.0,
        "min_class_recall": float(min(recalls)) if recalls else 0.0,
        "per_class_recall": per_recall,
        "confusion_matrix": matrix.tolist(),
        "confusion_matrix_labels": class_names,
        "support": {name: int(value) for name, value in support.items()},
        "pairwise_margins": pairwise_probability_margins(true, probabilities, class_names) if probabilities is not None else {},
    }


def m5_overfragmentation_report(true_labels: list[str], pred_labels: list[str], class_names: list[str], *, tau: float = M5_TAU) -> dict[str, object]:
    m5_indices = [idx for idx, label in enumerate(true_labels) if label in READOUT_MECHANISM_IDS]
    counts = {}
    for idx in m5_indices:
        counts[pred_labels[idx]] = counts.get(pred_labels[idx], 0) + 1
    total = max(1, len(m5_indices))
    significant = {label: count for label, count in counts.items() if count / total >= float(tau)}
    readout_mass = sum(count for label, count in counts.items() if label in READOUT_MECHANISM_IDS)
    gate_confusion = sum(count for label, count in counts.items() if label not in READOUT_MECHANISM_IDS)
    return {
        "schema": "scope_static_s2d11_readout_mechanism_report_v2",
        "tau": float(tau),
        "readout_true_mechanisms": list(READOUT_MECHANISM_IDS),
        "readout_split_count": int(len(significant)),
        "readout_mass_by_predicted_class": counts,
        "readout_cluster_purity": float(readout_mass / total),
        "readout_overfragmentation_index": float(max(0, len(significant) - len(READOUT_MECHANISM_IDS))),
        "readout_vs_gate_confusion_rate": float(gate_confusion / total),
        "readout_split_fixed": len(significant) <= len(READOUT_MECHANISM_IDS),
        "M5_split_count": int(len(significant)),
        "M5_mass_by_predicted_class": counts,
        "M5_cluster_purity": float(readout_mass / total),
        "M5_overfragmentation_index": float(max(0, len(significant) - len(READOUT_MECHANISM_IDS))),
        "M5_vs_gate_confusion_rate": float(gate_confusion / total),
        "M5_split_fixed": len(significant) <= len(READOUT_MECHANISM_IDS),
    }


def m11_readout_confound_audit(bundle: TypedSpamGateBundle, labels: list[str], groups: list[int], class_names: list[str], *, seed: int) -> dict[str, object]:
    features = bundle.feature_spaces["typed_gate_readout_prep_invariant_learner"]
    names = bundle.feature_names["typed_gate_readout_prep_invariant_learner"]
    prep_columns = [idx for idx, name in enumerate(names) if name.startswith("prep_") or name in {"initial_state_affine_shift", "reset_prep_asymmetry"}]
    readout_columns = [idx for idx, name in enumerate(names) if name.startswith("readout_") or name.startswith("assignment_")]
    raw = features[:, prep_columns] if prep_columns else np.zeros((features.shape[0], 1))
    base = features[:, readout_columns] if readout_columns else np.zeros((features.shape[0], 1))
    residualized = residualize_by_design(raw, base)
    raw_result = grouped_linear_head(raw, labels, groups, class_names, seed=int(seed))
    resid_result = grouped_linear_head(residualized, labels, groups, class_names, seed=int(seed))
    prep_label = _primary_prep_reset_label(labels)
    readout_label = _primary_readout_label(labels)
    return {
        "schema": "scope_static_s2d11_m11_readout_confound_audit_v1",
        "raw_prep_reset_features": _compact_head_result(raw_result),
        "readout_residualized_prep_reset_features": _compact_head_result(resid_result),
        "prep_reset_primary_label": prep_label,
        "readout_primary_label": readout_label,
        "M11_recall_before_readout_residualization": raw_result["overall"]["per_class_recall"].get(prep_label),
        "M11_recall_after_readout_residualization": resid_result["overall"]["per_class_recall"].get(prep_label),
        "M11_M4_pairwise_margin": _pair_margin_from_result(resid_result, f"{prep_label}/M4"),
        "M11_M5_pairwise_margin": _pair_margin_from_result(resid_result, f"{prep_label}/{readout_label}"),
        "M11_vs_readout_branch_confusion": _m11_readout_confusion(resid_result),
    }


def single_qubit_invariant_reconstruction_audit(records: list[dict[str, object]], labels: list[str], features: np.ndarray, feature_names: list[str]) -> dict[str, object]:
    pairs = {
        "RX/RZ pairwise margin": ("M2", "M3"),
        "coherent-vs-stochastic 1Q margin": ("M2", "M0"),
        "nonunital detection score": ("M4", "M0"),
    }
    margins = {}
    for name, (left, right) in pairs.items():
        margins[name] = _feature_margin(labels, features, feature_names, left, right)
    fit_resid_idx = feature_names.index("generator_total") if "generator_total" in feature_names else 0
    values = features[:, fit_resid_idx] if features.size else np.asarray([])
    return {
        "schema": "scope_static_s2d11_single_qubit_invariant_reconstruction_audit_v1",
        "RX_RZ_pairwise_margin": margins["RX/RZ pairwise margin"],
        "coherent_vs_stochastic_1Q_margin": margins["coherent-vs-stochastic 1Q margin"],
        "nonunital_detection_score": margins["nonunital detection score"],
        "PTM_generator_fit_residual_distribution": _distribution(values),
        "invariant_SNR_by_feature": {
            name: _snr(features[:, idx]) for idx, name in enumerate(feature_names)
        },
        "low_SNR_1Q_failure_examples": [],
    }


def m11_prep_observability_preflight(labels: list[str], features: np.ndarray, feature_names: list[str]) -> dict[str, object]:
    prep_label = _primary_prep_reset_label(labels)
    readout_label = _primary_readout_label(labels)
    margin_m4 = _feature_margin(labels, features, feature_names, prep_label, "M4")
    margin_m5 = _feature_margin(labels, features, feature_names, prep_label, readout_label)
    passed = bool(margin_m4.get("available")) and bool(margin_m5.get("available")) and float(margin_m4.get("z_margin", 0.0)) > 0.0 and float(margin_m5.get("z_margin", 0.0)) > 0.0
    return {
        "schema": "scope_static_s2d11a_m11_prep_observability_preflight_v1",
        "passed": passed,
        "M11_vs_M4_margin": margin_m4,
        "M11_vs_M5_margin": margin_m5,
        "interpretation": (
            "Prep/reset features separate M17/M18 from gate and readout mechanisms above chance"
            if passed
            else "Prep/reset observability is weak under current no-new-probe data"
        ),
    }


def m11_prep_feature_snr(labels: list[str], features: np.ndarray, feature_names: list[str]) -> dict[str, object]:
    prep_label = _primary_prep_reset_label(labels)
    mask = np.asarray([label == prep_label for label in labels], dtype=bool)
    return {
        "schema": "scope_static_s2d11_m11_prep_feature_snr_v1",
        "features": {
            name: _snr(features[mask, idx]) if np.any(mask) else 0.0
            for idx, name in enumerate(feature_names)
            if name.startswith("prep_") or name in {"initial_state_affine_shift", "reset_prep_asymmetry"}
        },
    }


def m11_vs_m4_preflight_margin(labels: list[str], features: np.ndarray, feature_names: list[str]) -> dict[str, object]:
    prep_label = _primary_prep_reset_label(labels)
    return {
        "schema": "scope_static_s2d11_m11_vs_m4_preflight_margin_v1",
        "prep_reset_primary_label": prep_label,
        "margin": _feature_margin(labels, features, feature_names, prep_label, "M4"),
    }


def prep_reconstruction_assumption_audit(probe_names: list[str]) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d11_prep_reconstruction_assumption_audit_v1",
        "uses_existing_rzz_local_tomography": True,
        "no_new_probe_family": True,
        "prep_metadata_present": any("rzz_tomo_p" in name for name in probe_names),
        "assumption": "prep/reset features are shot-derived response proxies, not full GST/SPAM tomography",
    }


def gate_family_audit(labels: list[str], pred: list[str], class_names: list[str]) -> dict[str, object]:
    subset = [name for name in RZZ_FAMILY_IDS if name in class_names]
    mask = [label in subset for label in labels]
    true = [label for label, keep in zip(labels, mask) if keep]
    got = [label for label, keep in zip(pred, mask) if keep]
    return {"schema": "scope_static_s2d11_gate_family_audit_v1", "rzz_family": subset, **classification_metrics(true, got, subset)}


def oracle_upper_bound_metrics(labels: list[str], class_names: list[str]) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d11_oracle_upper_bound_metrics_v1",
        "role": "audit_only_forbidden_information_upper_bound",
        "uses_oracle_labels_as_predictions": True,
        "not_a_valid_learner": True,
        **classification_metrics(labels, labels, class_names),
    }


def scrambled_branch_control_audit(branch_ablation: dict[str, object], controls: dict[str, object]) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d11_scrambled_branch_control_audit_v1",
        "within_branch_scrambled_control": {
            "scramble_mode": "shuffle feature columns within each branch",
            "branch_assignment_preserved": True,
            "dimensions_preserved": True,
            "performance_drop_vs_real_balanced_accuracy": controls["real_minus_within_branch_scrambled_balanced_accuracy"],
        },
        "cross_branch_scrambled_control": {
            "scramble_mode": "permute complete feature rows across branches",
            "branch_assignment_preserved": False,
            "dimensions_preserved": True,
            "performance_drop_vs_real_balanced_accuracy": controls["real_minus_cross_branch_scrambled_balanced_accuracy"],
            "diagnostic_not_primary_threshold": True,
        },
    }


def m19_confidence_audit(bundle: TypedSpamGateBundle, labels: list[str], pred: list[str], class_names: list[str]) -> dict[str, object]:
    features = bundle.feature_spaces["typed_gate_readout_prep_invariant_learner"]
    names = bundle.feature_names["typed_gate_readout_prep_invariant_learner"]
    mask = np.asarray([label == "M19" for label in labels], dtype=bool)
    indices = [names.index(name) for name in names if name in {"unitarity_loss_R_error", "gamma_isotropy_score", "generator_total"}]
    confidence = np.linalg.norm(features[:, indices], axis=1) if indices else np.zeros(features.shape[0])
    true_m13 = [label for label, keep in zip(labels, mask.tolist()) if keep]
    pred_m13 = [label for label, keep in zip(pred, mask.tolist()) if keep]
    recall = classification_metrics(true_m13, pred_m13, ["M19"])["per_class_recall"].get("M19", 0.0) if true_m13 else None
    return {
        "schema": "scope_static_s2d11_m19_confidence_audit_v1",
        "secondary_stress_only": True,
        "M19_recall": recall,
        "M19_confidence_histogram": np.histogram(confidence[mask], bins=5)[0].astype(int).tolist() if np.any(mask) else [],
        "M19_invariant_SNR": {names[idx]: _snr(features[mask, idx]) for idx in indices} if np.any(mask) else {},
        "M19_false_negative_examples": [int(idx) for idx, (label, got) in enumerate(zip(labels, pred)) if label == "M19" and got != "M19"],
        "M13_recall": None,
        "M13_confidence_histogram": [],
        "M13_invariant_SNR": {},
        "M13_false_negative_examples": [],
        "unitarity_proxy_distribution": _distribution(features[mask, names.index("unitarity_loss_R_error")]) if np.any(mask) and "unitarity_loss_R_error" in names else {},
        "PTM_mixing_proxy_distribution": _distribution(confidence[mask]) if np.any(mask) else {},
    }


def m13_confidence_audit(bundle: TypedSpamGateBundle, labels: list[str], pred: list[str], class_names: list[str]) -> dict[str, object]:
    """Backward-compatible alias for historical artifact names; current other mechanism is M19."""

    return m19_confidence_audit(bundle, labels, pred, class_names)


def leakage_guardrail_audit(feature_schema: dict[str, object]) -> dict[str, object]:
    columns = []
    for block in feature_schema.get("feature_blocks", {}).values():
        columns.extend(str(name).lower() for name in block.get("feature_names", []))
    checks = {
        "oracle_label_not_in_feature_columns": not any("oracle_label" in name for name in columns),
        "mechanism_id_not_in_feature_columns": not any("mechanism_id" in name for name in columns),
        "exact_ptm_columns_absent": not any("exact_ptm" in name for name in columns),
        "teacher_channel_columns_absent": not any("teacher_channel" in name for name in columns),
        "oracle_fingerprint_columns_absent": not any("oracle_fingerprint" in name for name in columns),
        "visible_instruction_type_allowed": True,
        "no_new_probe_family": True,
    }
    return {"schema": "scope_static_s2d11_leakage_guardrail_audit_v1", "passed": all(checks.values()), "checks": checks}


def typed_branch_feature_manifest(feature_names: list[str]) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d11_typed_branch_feature_manifest_v1",
        "branches": list(BRANCH_NAMES),
        "feature_names": list(feature_names),
        "uses_oracle_labels": False,
        "uses_exact_teacher_channel": False,
        "uses_exact_ptm": False,
        "visible_inputs": ["shot_bits", "probe_metadata", "visible_instruction_type", "visible_qubits", "shot_reconstructed_local_ptm"],
    }


def s2d11_success(
    *,
    branch_ablation: dict[str, object],
    heads: dict[str, object],
    controls: dict[str, object],
    m5_report: dict[str, object],
    m11_report: dict[str, object],
    gate_audit: dict[str, object],
    coverage: dict[str, object],
) -> dict[str, object]:
    primary = branch_ablation["typed_gate_readout_prep_invariant_learner"]["overall"]
    flat_inv = branch_ablation["flat_invariants_only"]["overall"]
    flat_plus = branch_ablation["flat_raw_plus_invariants"]["overall"]
    no_readout = branch_ablation["typed_without_readout_branch"]["overall"]
    no_prep = branch_ablation["typed_without_prep_branch"]["overall"]
    maha = heads["typed_mahalanobis_prototype_head"]["overall"]
    linear = heads["typed_linear_head"]["overall"]
    checks = {
        "macro_F1_ge_0_80": float(primary["macro_F1"]) >= 0.80,
        "balanced_accuracy_ge_0_80": float(primary["balanced_accuracy"]) >= 0.80,
        "no_primary_class_recall_lt_0_65": float(primary["min_class_recall"]) >= 0.65,
        "beats_within_branch_scrambled_by_0_25": bool(controls["primary_threshold_real_minus_within_branch_scrambled_ge_0_25"]),
        "beats_flat_invariants": float(primary["balanced_accuracy"]) > float(flat_inv["balanced_accuracy"]),
        "beats_flat_raw_plus_invariants": float(primary["balanced_accuracy"]) > float(flat_plus["balanced_accuracy"]),
        "beats_without_readout_branch": float(primary["balanced_accuracy"]) > float(no_readout["balanced_accuracy"]),
        "beats_without_prep_branch": float(primary["balanced_accuracy"]) > float(no_prep["balanced_accuracy"]),
        "mahalanobis_not_under_linear": float(maha["balanced_accuracy"]) >= float(linear["balanced_accuracy"]),
        "readout_split_fixed": bool(m5_report.get("readout_split_fixed", False)),
        "gate_family_balanced_accuracy_ge_0_80": float(gate_audit.get("balanced_accuracy", 0.0)) >= 0.80,
        "grouped_fold_coverage_valid": bool(coverage.get("valid_grouped_generalization", False)),
    }
    return {"passed": all(checks.values()), "checks": checks}


def pairwise_probability_margins(true: list[str], probabilities: np.ndarray, class_names: list[str]) -> dict[str, object]:
    pairs = ("M1/M6", "M1/M7", "M6/M7", "M9/M1", "M9/M6", "M9/M7", "M17/M4", "M17/M13")
    out = {
        "definition": (
            "For classifier/prototype score heads, pairwise_margin(a,b) is the mean over true a rows of "
            "score_a(x)-score_b(x), plus true b rows of score_b(x)-score_a(x). Positive means the model "
            "prefers the correct class."
        )
    }
    index = {name: idx for idx, name in enumerate(class_names)}
    for pair in pairs:
        left, right = pair.split("/")
        if left not in index or right not in index:
            out[pair] = {"available": False, "margin": None}
            continue
        values = []
        for label, row in zip(true, probabilities):
            if label == left:
                values.append(float(row[index[left]] - row[index[right]]))
            elif label == right:
                values.append(float(row[index[right]] - row[index[left]]))
        out[pair] = {"available": bool(values), "margin": float(np.mean(values)) if values else None}
    return out


def distance_pairwise_margins(true: list[str], distances: np.ndarray, class_names: list[str]) -> dict[str, object]:
    pairs = ("M1/M6", "M1/M7", "M6/M7", "M9/M1", "M9/M6", "M9/M7", "M17/M4", "M17/M13")
    out = {
        "definition": (
            "For distance heads, pairwise_margin(a,b) is the mean over true a rows of distance_to_b(x)-distance_to_a(x), "
            "plus true b rows of distance_to_a(x)-distance_to_b(x). Positive means the correct prototype is closer."
        )
    }
    index = {name: idx for idx, name in enumerate(class_names)}
    dist = np.nan_to_num(np.asarray(distances, dtype=np.float64), nan=np.inf, posinf=np.inf, neginf=np.inf)
    for pair in pairs:
        left, right = pair.split("/")
        if left not in index or right not in index:
            out[pair] = {"available": False, "margin": None}
            continue
        values = []
        for label, row in zip(true, dist):
            left_d = float(row[index[left]])
            right_d = float(row[index[right]])
            if not np.isfinite(left_d) or not np.isfinite(right_d):
                continue
            if label == left:
                values.append(right_d - left_d)
            elif label == right:
                values.append(left_d - right_d)
        out[pair] = {"available": bool(values), "margin": float(np.mean(values)) if values else None}
    return out


def pairwise_margin_report(primary_margins: dict[str, object], heads: dict[str, object]) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d11_pairwise_margin_report_v1",
        "score_margin_definition": (
            "pairwise_margin(a,b) = mean over true class a rows of score_a(x)-score_b(x), "
            "and true class b rows of score_b(x)-score_a(x). Positive means the head prefers "
            "the correct class."
        ),
        "distance_margin_definition": (
            "For distance heads, pairwise_margin(a,b) = mean over true class a rows of "
            "distance_to_b(x)-distance_to_a(x), and true class b rows of distance_to_a(x)-distance_to_b(x). "
            "Positive means the nearest prototype is closer to the correct class."
        ),
        "primary_linear_pairwise_margins": primary_margins,
        "head_summaries": {name: row.get("overall", {}) for name, row in heads.items()},
    }


def confusion_matrix_by_branch(labels: list[str], pred: list[str], branches: list[str], class_names: list[str]) -> dict[str, object]:
    out = {"schema": "scope_static_s2d11_confusion_matrix_by_branch_v1", "branches": {}}
    for branch in BRANCH_NAMES:
        mask = [current == branch for current in branches]
        out["branches"][branch] = classification_metrics([label for label, keep in zip(labels, mask) if keep], [label for label, keep in zip(pred, mask) if keep], class_names)
    return out


def _record_features(record: dict[str, object], observations: np.ndarray, probe_names: list[str], local: dict[str, object]) -> dict[str, float]:
    features = {name: float(local.get("features", {}).get(name, 0.0)) for name in GENERATOR_CORE}
    ptm = local.get("ptm", {})
    invariants = generator_invariants_from_coordinates(
        {**features, "nonunital_norm_proxy": float(local.get("features", {}).get("nonunital_norm_proxy", 0.0))},
        r_error=_matrix_or_none(ptm.get("R_error")),
        r_est=_matrix_or_none(ptm.get("R_est")),
    )
    features.update(invariants)
    error = abs(float(features.get("delta_norm", 0.0)))
    total = abs(float(features.get("generator_total", 0.0)))
    snr = total / max(NUMERICAL_ZERO, error)
    features.update(
        {
            "fit_residual_or_reconstruction_error": error,
            "feature_snr": snr,
            "feature_confidence": float(snr / (1.0 + snr)),
            "low_confidence_flag": float(total < NUMERICAL_ZERO or snr < 0.05),
        }
    )
    qubits = [int(value) for value in record.get("qubits", [])]
    num_qubits = int(observations.shape[2]) if observations.ndim == 3 else 1
    branch = visible_branch(record)
    features.update(_location_features(qubits, num_qubits, branch))
    features.update(_instruction_features(record))
    features.update(_single_qubit_response_features(record, observations, probe_names, qubits))
    features.update(_readout_features(record, observations, probe_names, qubits))
    features.update(_prep_features(record, observations, probe_names, qubits))
    return features


def _instruction_features(record: dict[str, object]) -> dict[str, float]:
    instruction = str(record.get("instruction", "")).lower()
    known = {"id", "rx", "rz", "rzz", "measure", "reset"}
    return {
        "instruction_id": float(instruction == "id"),
        "instruction_rx": float(instruction == "rx"),
        "instruction_rz": float(instruction == "rz"),
        "instruction_rzz": float(instruction == "rzz"),
        "instruction_measure": float(instruction == "measure"),
        "instruction_reset": float(instruction == "reset"),
        "instruction_other": float(instruction not in known),
    }


def _single_qubit_response_features(record: dict[str, object], observations: np.ndarray, probe_names: list[str], qubits: list[int]) -> dict[str, float]:
    q = qubits[0] if qubits else 0
    q = min(max(q, 0), observations.shape[2] - 1)
    indices = _record_probe_indices(record, len(probe_names))
    if not indices:
        return {name: 0.0 for name in SINGLE_QUBIT_RESPONSE_FEATURES}
    means = np.asarray([float(np.mean(observations[idx, :, q])) for idx in indices], dtype=np.float64)
    z = _probe_mean(probe_names, observations, indices, q, "z")
    x = _probe_mean(probe_names, observations, indices, q, "x")
    y = _probe_mean(probe_names, observations, indices, q, "y")
    p = np.clip(means, NUMERICAL_ZERO, 1.0 - NUMERICAL_ZERO)
    entropy = float(np.mean(-(p * np.log(p) + (1.0 - p) * np.log(1.0 - p))))
    return {
        "sq_response_mean": float(np.mean(means)),
        "sq_response_std": float(np.std(means)),
        "sq_response_min": float(np.min(means)),
        "sq_response_max": float(np.max(means)),
        "sq_response_entropy": entropy,
        "sq_z_mean": float(z),
        "sq_x_mean": float(x),
        "sq_y_mean": float(y),
        "sq_x_minus_z": float(x - z),
        "sq_y_minus_z": float(y - z),
        "sq_x_minus_y": float(x - y),
        "sq_phase_visibility": float(np.linalg.norm([x - z, y - z])),
        "sq_population_visibility": float(abs(z - 0.5)),
        "sq_basis_anisotropy": float(np.std([x, y, z])),
    }


def _readout_features(record: dict[str, object], observations: np.ndarray, probe_names: list[str], qubits: list[int]) -> dict[str, float]:
    q = qubits[0] if qubits else 0
    q = min(max(q, 0), observations.shape[2] - 1)
    indices = _record_probe_indices(record, len(probe_names))
    if not indices:
        return _empty_readout_features()
    means = np.asarray([float(np.mean(observations[idx, :, q])) for idx in indices], dtype=np.float64)
    centered = means - float(np.mean(means))
    z = _probe_mean(probe_names, observations, indices, q, "z")
    x = _probe_mean(probe_names, observations, indices, q, "x")
    y = _probe_mean(probe_names, observations, indices, q, "y")
    strength = float(np.linalg.norm(means))
    p = np.clip(means, NUMERICAL_ZERO, 1.0 - NUMERICAL_ZERO)
    entropy = float(np.mean(-(p * np.log(p) + (1.0 - p) * np.log(1.0 - p))))
    return {
        "readout_shape_norm": float(np.linalg.norm(centered)),
        "readout_strength": strength,
        "assignment_asymmetry_proxy": float(z - (1.0 - z)),
        "readout_entropy": entropy,
        "readout_variance": float(np.var(means)),
        "readout_x_minus_z": float(x - z),
        "readout_y_minus_z": float(y - z),
    }


def _prep_features(record: dict[str, object], observations: np.ndarray, probe_names: list[str], qubits: list[int]) -> dict[str, float]:
    q = qubits[0] if qubits else 0
    q = min(max(q, 0), observations.shape[2] - 1)
    indices = _record_probe_indices(record, len(probe_names))
    z_plus = _probe_mean(probe_names, observations, indices, q, "pzp")
    z_minus = _probe_mean(probe_names, observations, indices, q, "pzm")
    x_plus = _probe_mean(probe_names, observations, indices, q, "pxp")
    y_plus = _probe_mean(probe_names, observations, indices, q, "pyp")
    prep_axis = np.asarray([x_plus - 0.5, y_plus - 0.5, z_plus - z_minus], dtype=np.float64)
    return {
        "prep_fidelity_proxy": float(abs(z_plus - z_minus) + abs(x_plus - 0.5) + abs(y_plus - 0.5)),
        "prep_axis_bias_x": float(prep_axis[0]),
        "prep_axis_bias_y": float(prep_axis[1]),
        "prep_axis_bias_z": float(prep_axis[2]),
        "initial_state_affine_shift": float(np.linalg.norm(prep_axis)),
        "reset_prep_asymmetry": float(z_plus - (1.0 - z_minus)),
        "prep_confidence_proxy": float(np.linalg.norm(prep_axis) / max(NUMERICAL_ZERO, np.std(prep_axis) + NUMERICAL_ZERO)),
    }


def _location_features(qubits: list[int], num_qubits: int, branch: str) -> dict[str, float]:
    if qubits:
        mean_q = float(np.mean(qubits))
        span = float(max(qubits) - min(qubits)) if len(qubits) > 1 else 0.0
    else:
        mean_q = 0.0
        span = 0.0
    return {
        "location_qubit_mean": mean_q,
        "location_span": span,
        "chain_position": float(mean_q / max(1, int(num_qubits) - 1)),
        "neighbor_rzz_count": float(2 if 0 < mean_q < int(num_qubits) - 1 else 1),
        "branch_gate": float(branch == "gate_process_branch"),
        "branch_readout": float(branch == "readout_branch"),
        "branch_prep_reset": float(branch == "prep_reset_branch"),
    }


def _local_rows(local_record: dict[str, object]) -> dict[int, dict[str, object]]:
    estimates = local_record.get("generator_coordinate_estimates", {})
    ptm_records = {
        int(item.get("location_id", idx)): item
        for idx, item in enumerate(local_record.get("ptm_block_reconstruction", {}).get("records", []))
        if isinstance(item, dict)
    }
    out = {}
    for idx, row in enumerate(estimates.get("records", [])):
        location_id = int(row.get("location_id", idx))
        out[location_id] = {"features": dict(row.get("features", {})), "ptm": ptm_records.get(location_id, {})}
    return out


def _grouped_distance_head(features: np.ndarray, labels: list[str], groups: list[int], class_names: list[str], *, mahalanobis: bool) -> dict[str, object]:
    import torch

    x = _finite(np.asarray(features, dtype=np.float64))
    y = np.asarray(labels, dtype=object)
    g = np.asarray(groups, dtype=np.int64)
    if len(class_names) < 2 or len(set(groups)) < 2:
        return _skipped_head("typed_mahalanobis_prototype_head" if mahalanobis else "typed_prototype_head", class_names)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dtype = torch.float64
    true_all = []
    pred_all = []
    folds = []
    dist_all = []
    for test_group in sorted(set(g.tolist())):
        train = g != int(test_group)
        test = g == int(test_group)
        x_train = torch.as_tensor(x[train], dtype=dtype, device=device)
        x_test = torch.as_tensor(x[test], dtype=dtype, device=device)
        mean = torch.mean(x_train, dim=0, keepdim=True)
        std = torch.clamp(torch.std(x_train, dim=0, keepdim=True, unbiased=False), min=1e-9)
        x_train = (x_train - mean) / std
        x_test = (x_test - mean) / std
        centers = []
        present = []
        for name in class_names:
            mask = np.asarray(y[train] == name, dtype=bool)
            present.append(bool(np.any(mask)))
            if np.any(mask):
                centers.append(torch.mean(x_train[torch.as_tensor(mask, dtype=torch.bool, device=device)], dim=0))
            else:
                centers.append(torch.zeros(x_train.shape[1], dtype=dtype, device=device))
        center_matrix = torch.stack(centers, dim=0)
        diff = x_test[:, None, :] - center_matrix[None, :, :]
        if mahalanobis:
            pooled_terms = []
            for class_idx, name in enumerate(class_names):
                mask = np.asarray(y[train] == name, dtype=bool)
                if np.any(mask):
                    local = x_train[torch.as_tensor(mask, dtype=torch.bool, device=device)] - center_matrix[class_idx]
                    pooled_terms.append(local * local)
            pooled = torch.cat(pooled_terms, dim=0) if pooled_terms else x_train * 0.0 + 1.0
            var = torch.clamp(torch.mean(pooled, dim=0), min=1e-6)
            denom = 0.9 * var + 0.1
            distances = torch.sum((diff * diff) / denom[None, None, :], dim=2)
        else:
            distances = torch.linalg.norm(diff, dim=2)
        if not all(present):
            absent = torch.as_tensor([not item for item in present], dtype=torch.bool, device=device)
            distances[:, absent] = float("inf")
        pred_indices = torch.argmin(distances, dim=1).detach().cpu().numpy().astype(np.int64)
        dist_np = distances.detach().cpu().numpy().astype(np.float64, copy=False)
        for row_idx, true in enumerate(y[test]):
            true_all.append(str(true))
            pred_all.append(str(class_names[int(pred_indices[row_idx])]))
            dist_all.append(dist_np[row_idx])
        folds.append({"test_circuit_id": int(test_group), "backend": str(device), "diagonal_shrinkage": bool(mahalanobis)})
    overall = classification_metrics(true_all, pred_all, class_names)
    dist_matrix = np.stack(dist_all, axis=0) if dist_all else np.zeros((0, len(class_names)), dtype=np.float64)
    overall["pairwise_margins"] = distance_pairwise_margins(true_all, dist_matrix, class_names)
    model = "TorchDiagonalShrinkageMahalanobisPrototype" if mahalanobis else "TorchNearestPrototype"
    return {"model": model, "backend": str(device), "overall": overall, "fold_predictions": folds}


def _gpu_dual_ridge_probabilities(
    x_train_np: np.ndarray,
    y_train_np: np.ndarray,
    x_test_np: np.ndarray,
    *,
    num_classes: int,
    seed: int,
    ridge: float = 1e-2,
) -> np.ndarray:
    import torch

    torch.manual_seed(int(seed))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dtype = torch.float64
    x_train = torch.as_tensor(_finite(np.asarray(x_train_np, dtype=np.float64)), dtype=dtype, device=device)
    x_test = torch.as_tensor(_finite(np.asarray(x_test_np, dtype=np.float64)), dtype=dtype, device=device)
    y_train = torch.as_tensor(np.asarray(y_train_np, dtype=np.int64), dtype=torch.long, device=device)
    if x_train.numel() == 0 or x_test.numel() == 0:
        return np.zeros((int(x_test_np.shape[0]), int(num_classes)), dtype=np.float64)
    mean = torch.mean(x_train, dim=0, keepdim=True)
    std = torch.clamp(torch.std(x_train, dim=0, keepdim=True, unbiased=False), min=1e-9)
    x_train = (x_train - mean) / std
    x_test = (x_test - mean) / std
    ones_train = torch.ones((x_train.shape[0], 1), dtype=dtype, device=device)
    ones_test = torch.ones((x_test.shape[0], 1), dtype=dtype, device=device)
    x_train = torch.cat([x_train, ones_train], dim=1)
    x_test = torch.cat([x_test, ones_test], dim=1)

    targets = torch.zeros((x_train.shape[0], int(num_classes)), dtype=dtype, device=device)
    targets[torch.arange(x_train.shape[0], device=device), y_train] = 1.0
    counts = torch.bincount(y_train, minlength=int(num_classes)).to(dtype=dtype)
    weights_by_class = torch.zeros_like(counts)
    present = counts > 0
    weights_by_class[present] = float(x_train.shape[0]) / torch.clamp(torch.sum(present).to(dtype=dtype) * counts[present], min=1e-9)
    sample_weights = weights_by_class[y_train]
    sqrt_w = torch.sqrt(torch.clamp(sample_weights, min=1e-12)).reshape(-1, 1)
    x_weighted = x_train * sqrt_w
    y_weighted = targets * sqrt_w

    gram = x_weighted @ x_weighted.T
    eye = torch.eye(gram.shape[0], dtype=dtype, device=device)
    alpha = torch.linalg.solve(gram + float(ridge) * eye, y_weighted)
    coef = x_weighted.T @ alpha
    scores = x_test @ coef
    absent = counts <= 0
    if bool(torch.any(absent)):
        scores[:, absent] = -1e9
    prob = torch.softmax(scores, dim=1)
    return prob.detach().cpu().numpy().astype(np.float64, copy=False)


def _compact_head_result(result: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in result.items() if key != "fold_predictions"}


def _pair_margin_from_result(result: dict[str, object], pair: str) -> object:
    return result.get("overall", {}).get("pairwise_margins", {}).get(pair, {}).get("margin")


def _m11_readout_confusion(result: dict[str, object]) -> float:
    all_rows = result.get("all", {})
    true = all_rows.get("true_labels", [])
    pred = all_rows.get("predicted_labels", [])
    m11 = [got for label, got in zip(true, pred) if label in PREP_RESET_MECHANISM_IDS]
    if not m11:
        return 0.0
    return float(sum(1 for got in m11 if got in READOUT_MECHANISM_IDS) / len(m11))


def _primary_prep_reset_label(labels: list[str]) -> str:
    for label in PREP_RESET_MECHANISM_IDS:
        if label in labels:
            return label
    return PREP_RESET_MECHANISM_IDS[0]


def _primary_readout_label(labels: list[str]) -> str:
    for label in READOUT_MECHANISM_IDS:
        if label in labels:
            return label
    return READOUT_MECHANISM_IDS[0]


def _feature_margin(labels: list[str], features: np.ndarray, feature_names: list[str], left: str, right: str) -> dict[str, object]:
    left_mask = np.asarray([label == left for label in labels], dtype=bool)
    right_mask = np.asarray([label == right for label in labels], dtype=bool)
    if not np.any(left_mask) or not np.any(right_mask):
        return {"available": False}
    diff = np.mean(features[left_mask], axis=0) - np.mean(features[right_mask], axis=0)
    pooled = np.sqrt(0.5 * (np.var(features[left_mask], axis=0) + np.var(features[right_mask], axis=0)))
    z = diff / np.maximum(pooled, NUMERICAL_ZERO)
    return {"available": True, "z_margin": float(np.linalg.norm(z)), "top_feature": str(feature_names[int(np.argmax(np.abs(z)))])}


def _probe_mean(probe_names: list[str], observations: np.ndarray, indices: list[int], q: int, token: str) -> float:
    matches = [idx for idx in indices if token in probe_names[idx].lower()]
    if not matches:
        matches = indices
    return float(np.mean([np.mean(observations[idx, :, q]) for idx in matches])) if matches else 0.0


def _record_probe_indices(record: dict[str, object], num_probes: int) -> list[int]:
    raw = record.get("probe_indices", [])
    if isinstance(raw, list) and raw:
        return [int(value) for value in raw]
    return list(range(int(num_probes)))


def _zero_branch(features: np.ndarray, branches: list[str], branch: str) -> np.ndarray:
    out = np.array(features, copy=True)
    mask = np.asarray([current == branch for current in branches], dtype=bool)
    out[mask] = 0.0
    return out


def _feature_table_row(record: dict[str, object], names: list[str], values: np.ndarray) -> dict[str, object]:
    by_name = {name: float(values[idx]) for idx, name in enumerate(names)}
    return {
        "location_id": int(record.get("location_id", 0)),
        "circuit_id": int(record.get("circuit_id", 0)),
        "instruction": str(record.get("instruction", "")),
        "qubits": [int(value) for value in record.get("qubits", [])],
        "feature_confidence": float(by_name.get("feature_confidence", 0.0)),
        "feature_snr": float(by_name.get("feature_snr", 0.0)),
        "fit_residual_or_reconstruction_error": float(by_name.get("fit_residual_or_reconstruction_error", 0.0)),
        "low_confidence_flag": bool(by_name.get("low_confidence_flag", 1.0) >= 0.5),
        "features": by_name,
    }


def _empty_readout_features() -> dict[str, float]:
    return {
        "readout_shape_norm": 0.0,
        "readout_strength": 0.0,
        "assignment_asymmetry_proxy": 0.0,
        "readout_entropy": 0.0,
        "readout_variance": 0.0,
        "readout_x_minus_z": 0.0,
        "readout_y_minus_z": 0.0,
    }


def _skipped_head(model: str, class_names: list[str]) -> dict[str, object]:
    return {"model": model, "overall": classification_metrics([], [], class_names), "fold_predictions": [], "all": {"true_labels": [], "predicted_labels": []}}


def _standardize_train_test(x_train: np.ndarray, x_test: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mean = np.mean(x_train, axis=0, keepdims=True)
    std = np.maximum(np.std(x_train, axis=0, keepdims=True), NUMERICAL_ZERO)
    return (x_train - mean) / std, (x_test - mean) / std


def _matrix_or_none(value: object) -> np.ndarray | None:
    if value is None:
        return None
    arr = np.asarray(value, dtype=np.float64)
    return _finite(arr) if arr.ndim == 2 else None


def _distribution(values: np.ndarray) -> dict[str, float | int]:
    arr = _finite(np.asarray(values, dtype=np.float64))
    return {
        "count": int(arr.size),
        "mean": float(np.mean(arr)) if arr.size else 0.0,
        "std": float(np.std(arr)) if arr.size else 0.0,
        "min": float(np.min(arr)) if arr.size else 0.0,
        "max": float(np.max(arr)) if arr.size else 0.0,
    }


def _snr(values: np.ndarray) -> float:
    arr = _finite(np.asarray(values, dtype=np.float64))
    return float(abs(np.mean(arr)) / max(np.std(arr), NUMERICAL_ZERO)) if arr.size else 0.0


def _counts(values: Iterable[object]) -> dict[str, int]:
    out: dict[str, int] = {}
    for value in values:
        out[str(value)] = out.get(str(value), 0) + 1
    return out


def _mechanism_sort_key(name: str) -> tuple[int, str]:
    if str(name).startswith("M") and str(name)[1:].isdigit():
        return (int(str(name)[1:]), str(name))
    return (10_000, str(name))


def _finite(values: np.ndarray) -> np.ndarray:
    return np.nan_to_num(np.asarray(values, dtype=np.float64), nan=NUMERICAL_ZERO, posinf=NUMERICAL_ZERO, neginf=-NUMERICAL_ZERO)
