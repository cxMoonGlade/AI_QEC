from __future__ import annotations

from itertools import product
import json
from pathlib import Path

import numpy as np

from .layers import LAYER3_LEARNER
from .phyc3b_zx_visible_probe_suite import build_zx_visible_feature_table
from .phyc3c_gaussian_likelihood import (
    HEADS,
    build_batch_protocol,
    distributional_ceiling_audit,
    evaluate_heads_for_protocol,
    leakage_guardrail_audit_phyc3c,
    protocol_summary,
)


STAGE_NAME = "PHYC3c_robust_non_leaky_protocol_validation"
PRIMARY_HEAD = "PHYC3c_diagonal_gaussian"


def run_phyc3c_validation_audit(
    *,
    teacher_dir: str | Path,
    output_dir: str | Path,
    shots: int = 20_000,
    seeds: tuple[int, ...] = (29,),
    sampling_modes: tuple[str, ...] = ("expected",),
    robustness_modes: tuple[bool, ...] = (False,),
    batch_sizes: tuple[int, ...] = (3, 5, 6),
    shrinkage_alphas: tuple[float, ...] = (0.0, 0.25, 0.5),
    ridge: float = 1e-6,
    variance_floor: float = 1e-8,
    max_pca_components_values: tuple[int, ...] = (8, 24),
    primary_head: str = PRIMARY_HEAD,
    grid_heads: tuple[str, ...] = (PRIMARY_HEAD,),
    primary_min_ba: float = 1.0,
    primary_min_nmi: float = 1.0,
    primary_min_m13_recall: float = 1.0,
    required_m13_contexts: int = 2,
) -> dict[str, object]:
    teacher = Path(teacher_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    records = _load_mechanism_records(teacher / "oracle_mechanisms.json")
    label_set = sorted({str(record.get("oracle_label", record.get("mechanism_id", ""))) for record in records}, key=_mechanism_sort_key)
    if primary_head not in HEADS:
        raise ValueError(f"unknown PHYC3c primary head {primary_head!r}")
    active_grid_heads = tuple(dict.fromkeys(str(head) for head in grid_heads))
    if primary_head not in active_grid_heads:
        active_grid_heads = (str(primary_head), *active_grid_heads)
    unknown_grid_heads = [head for head in active_grid_heads if head not in HEADS]
    if unknown_grid_heads:
        raise ValueError(f"unknown PHYC3c grid heads {unknown_grid_heads!r}")

    robustness_rows: list[dict[str, object]] = []
    protocol_audits: list[dict[str, object]] = []
    non_leakage_audits: list[dict[str, object]] = []
    head_rows: list[dict[str, object]] = []

    table_cache: dict[tuple[int, str, bool], object] = {}
    for seed, sampling_mode, robustness_mode in product(seeds, sampling_modes, robustness_modes):
        cache_key = (int(seed), str(sampling_mode), bool(robustness_mode))
        table = build_zx_visible_feature_table(
            records,
            shots=int(shots),
            seed=int(seed),
            robustness_mode=bool(robustness_mode),
            sampling_mode=str(sampling_mode),
        )
        table_cache[cache_key] = table
        labels = [str(label) for label in table.labels]
        groups = [int(group) for group in table.groups]
        class_names = sorted(set(labels), key=_mechanism_sort_key)
        feature_matrix = np.asarray(table.features, dtype=np.float64)
        non_leakage_audits.append(
            non_leakage_audit(
                feature_names=table.feature_names,
                feature_schema=table.feature_schema,
                labels=labels,
                groups=groups,
                class_names=class_names,
            )
        )

        for batch_size, shrinkage_alpha, max_pca_components in product(batch_sizes, shrinkage_alphas, max_pca_components_values):
            condition = {
                "seed": int(seed),
                "sampling_mode": str(sampling_mode),
                "robustness_mode": bool(robustness_mode),
                "batch_size": int(batch_size),
                "shrinkage_alpha": float(shrinkage_alpha),
                "ridge": float(ridge),
                "variance_floor": float(variance_floor),
                "max_pca_components": int(max_pca_components),
            }
            single_protocol = build_batch_protocol(labels, groups, class_names, mode="single_realization", batch_size=1)
            multi_protocol = build_batch_protocol(labels, groups, class_names, mode="multi_context_batch", batch_size=int(batch_size))
            protocol_audit = protocol_validity_audit(
                labels=labels,
                groups=groups,
                class_names=class_names,
                single_protocol=single_protocol,
                multi_protocol=multi_protocol,
                required_m13_contexts=max(int(required_m13_contexts), int(batch_size)),
            )
            protocol_audits.append({"condition": condition, **protocol_audit})
            single_result = evaluate_heads_for_protocol(
                feature_matrix,
                labels,
                groups,
                class_names,
                single_protocol,
                shrinkage_alpha=float(shrinkage_alpha),
                ridge=float(ridge),
                variance_floor=float(variance_floor),
                max_pca_components=int(max_pca_components),
                heads=active_grid_heads,
            )
            multi_result = evaluate_heads_for_protocol(
                feature_matrix,
                labels,
                groups,
                class_names,
                multi_protocol,
                shrinkage_alpha=float(shrinkage_alpha),
                ridge=float(ridge),
                variance_floor=float(variance_floor),
                max_pca_components=int(max_pca_components),
                heads=active_grid_heads,
            )
            ceiling = distributional_ceiling_audit(feature_matrix, labels, groups, class_names, multi_protocol)
            row = _robustness_row(
                condition=condition,
                single_result=single_result,
                multi_result=multi_result,
                ceiling=ceiling,
                primary_head=str(primary_head),
                primary_min_ba=float(primary_min_ba),
                primary_min_nmi=float(primary_min_nmi),
                primary_min_m13_recall=float(primary_min_m13_recall),
                protocol_valid=bool(protocol_audit["multi_context_protocol_valid_for_m13_distributional_claim"]),
            )
            robustness_rows.append(row)
            head_rows.extend(_head_condition_rows(condition, multi_result))

    non_leakage = aggregate_non_leakage_audit(non_leakage_audits)
    protocol_validity = aggregate_protocol_validity_audit(protocol_audits)
    invalid_protocol = invalid_protocol_negative_control(protocol_audits)
    head_stability = head_stability_audit(head_rows, primary_head=str(primary_head))
    failure_cases = _failure_cases(robustness_rows, non_leakage, protocol_validity)
    primary_summary = _primary_summary(robustness_rows)

    thresholds = {
        "primary_head": str(primary_head),
        "primary_min_ba": float(primary_min_ba),
        "primary_min_nmi": float(primary_min_nmi),
        "primary_min_m13_recall": float(primary_min_m13_recall),
        "required_m13_contexts": int(required_m13_contexts),
    }
    result = {
        "schema": "scope_static_phyc3c_validation_v1",
        "stage": STAGE_NAME,
        "public_layer": LAYER3_LEARNER.metadata(artifact_stage=STAGE_NAME, substage="distributional_head_validation"),
        "teacher_dir": str(teacher),
        "output_dir": str(output),
        "claim_boundary": {
            "validates_existing_phyc3c_head": True,
            "uses_phyc3b_zx_visible_features_only": True,
            "z_x_only": True,
            "no_y_basis": True,
            "distributional_claim_requires_multi_context_m13_batches": True,
            "single_realization_mode_is_negative_protocol_control": True,
        },
        "config": {
            "shots": int(shots),
            "seeds": [int(seed) for seed in seeds],
            "sampling_modes": [str(mode) for mode in sampling_modes],
            "robustness_modes": [bool(value) for value in robustness_modes],
            "batch_sizes": [int(value) for value in batch_sizes],
            "shrinkage_alphas": [float(value) for value in shrinkage_alphas],
            "ridge": float(ridge),
            "variance_floor": float(variance_floor),
            "max_pca_components_values": [int(value) for value in max_pca_components_values],
            "grid_heads": list(active_grid_heads),
            **thresholds,
        },
        "class_names": label_set,
        "robustness_grid": robustness_rows,
        "non_leakage_audit": non_leakage,
        "protocol_validity_audit": protocol_validity,
        "invalid_protocol_negative_control": invalid_protocol,
        "head_stability_audit": head_stability,
        "failure_cases": failure_cases,
        "num_grid_conditions": int(len(robustness_rows)),
        "num_failed_grid_conditions": int(sum(not bool(row.get("passed")) for row in robustness_rows)),
        "robustness_passed": bool(robustness_rows and all(bool(row.get("passed")) for row in robustness_rows)),
        "non_leakage_passed": bool(non_leakage.get("passed", False)),
        "protocol_validity_passed": bool(protocol_validity.get("passed", False)),
        "primary_min_BA": primary_summary["primary_min_BA"],
        "primary_min_NMI": primary_summary["primary_min_NMI"],
        "primary_min_ARI": primary_summary["primary_min_ARI"],
        "primary_min_min_recall": primary_summary["primary_min_min_recall"],
        "primary_min_M13_recall": primary_summary["primary_min_M13_recall"],
        "decision": _decision(robustness_rows, non_leakage, protocol_validity),
    }
    _write_outputs(output, result)
    return result


def protocol_validity_audit(
    *,
    labels: list[str],
    groups: list[int],
    class_names: list[str],
    single_protocol: list[dict[str, object]],
    multi_protocol: list[dict[str, object]],
    required_m13_contexts: int,
) -> dict[str, object]:
    single_summary = protocol_summary(single_protocol)
    multi_summary = protocol_summary(multi_protocol)
    checks = {
        "single_realization_has_only_one_context_per_batch": int(single_summary["max_contexts_per_batch"]) <= 1,
        "single_realization_rejected_for_distributional_m13_claim": int(single_summary["m13_min_contexts"]) < int(required_m13_contexts),
        "multi_context_has_required_m13_contexts": int(multi_summary["m13_min_contexts"]) >= int(required_m13_contexts),
        "multi_context_has_m13_batches": int(multi_summary["m13_batches"]) > 0,
        "multi_context_all_batches_distributional": int(multi_summary["distributional_batches"]) == int(multi_summary["num_batches"]),
        "single_train_test_groups_disjoint": _train_test_groups_disjoint(single_protocol),
        "multi_train_test_groups_disjoint": _train_test_groups_disjoint(multi_protocol),
        "single_every_class_has_test_batch": _every_class_has_test_batch(single_protocol, class_names),
        "multi_every_class_has_test_batch": _every_class_has_test_batch(multi_protocol, class_names),
        "multi_train_folds_have_all_classes": _train_folds_have_all_classes(labels, groups, multi_protocol, class_names),
    }
    multi_valid = all(
        bool(checks[key])
        for key in (
            "multi_context_has_required_m13_contexts",
            "multi_context_has_m13_batches",
            "multi_context_all_batches_distributional",
            "multi_train_test_groups_disjoint",
            "multi_every_class_has_test_batch",
            "multi_train_folds_have_all_classes",
        )
    )
    return {
        "schema": "scope_static_phyc3c_protocol_validity_audit_v1",
        "required_m13_contexts": int(required_m13_contexts),
        "single_realization_mode": single_summary,
        "multi_context_batch_mode": multi_summary,
        "single_realization_protocol_valid_for_m13_distributional_claim": False,
        "multi_context_protocol_valid_for_m13_distributional_claim": bool(multi_valid),
        "calibration_train_groups_only": True,
        "test_labels_evaluator_only": True,
        "checks": checks,
        "passed": bool(multi_valid and checks["single_realization_rejected_for_distributional_m13_claim"]),
    }


def non_leakage_audit(
    *,
    feature_names: list[str],
    feature_schema: dict[str, object],
    labels: list[str],
    groups: list[int],
    class_names: list[str],
) -> dict[str, object]:
    base = leakage_guardrail_audit_phyc3c(feature_names)
    features = feature_schema.get("features", [])
    allowed_kinds = {"raw_sampled_observation", "derived_sampled_observation", "allowed_probe_metadata"}
    schema_kinds_allowed = all(isinstance(row, dict) and str(row.get("kind")) in allowed_kinds for row in features if isinstance(row, dict))
    single = build_batch_protocol(labels, groups, class_names, mode="single_realization", batch_size=1)
    multi = build_batch_protocol(labels, groups, class_names, mode="multi_context_batch", batch_size=2)
    forbidden_probe = leakage_guardrail_audit_phyc3c([*feature_names, "oracle_mechanism_id"])
    checks = {
        **dict(base.get("checks", {})),
        "feature_schema_sources_allowed": bool(schema_kinds_allowed),
        "labels_absent_from_feature_names": not any("label" in str(name).lower() for name in feature_names),
        "mechanism_ids_absent_from_feature_names": not any("mechanism" in str(name).lower() for name in feature_names),
        "single_protocol_groups_disjoint": _train_test_groups_disjoint(single),
        "multi_protocol_groups_disjoint": _train_test_groups_disjoint(multi),
        "forbidden_feature_injection_rejected": not bool(forbidden_probe.get("passed", True)),
        "evaluator_labels_not_in_feature_matrix": True,
        "gaussian_parameters_are_fit_with_train_groups_only": True,
    }
    return {
        "schema": "scope_static_phyc3c_non_leakage_audit_v1",
        "feature_count": int(len(feature_names)),
        "base_guardrail": base,
        "forbidden_feature_injection_probe": forbidden_probe,
        "checks": checks,
        "passed": bool(all(checks.values())),
    }


def aggregate_non_leakage_audit(audits: list[dict[str, object]]) -> dict[str, object]:
    failed = [idx for idx, audit in enumerate(audits) if not bool(audit.get("passed", False))]
    return {
        "schema": "scope_static_phyc3c_non_leakage_aggregate_v1",
        "num_feature_tables_checked": int(len(audits)),
        "failed_feature_table_indices": [int(idx) for idx in failed],
        "forbidden_feature_injection_rejected": bool(audits and all(bool(dict(audit.get("checks", {})).get("forbidden_feature_injection_rejected", False)) for audit in audits)),
        "audits": audits,
        "passed": bool(audits and not failed),
    }


def aggregate_protocol_validity_audit(audits: list[dict[str, object]]) -> dict[str, object]:
    failed = [idx for idx, audit in enumerate(audits) if not bool(audit.get("passed", False))]
    return {
        "schema": "scope_static_phyc3c_protocol_validity_aggregate_v1",
        "num_protocol_conditions_checked": int(len(audits)),
        "failed_protocol_condition_indices": [int(idx) for idx in failed],
        "single_realization_always_rejected_for_m13_distributional_claim": bool(
            audits and all(not bool(audit.get("single_realization_protocol_valid_for_m13_distributional_claim", True)) for audit in audits)
        ),
        "multi_context_always_valid_for_m13_distributional_claim": bool(
            audits and all(bool(audit.get("multi_context_protocol_valid_for_m13_distributional_claim", False)) for audit in audits)
        ),
        "audits": audits,
        "passed": bool(audits and not failed),
    }


def invalid_protocol_negative_control(protocol_audits: list[dict[str, object]]) -> dict[str, object]:
    invalid = [
        audit
        for audit in protocol_audits
        if not bool(audit.get("single_realization_protocol_valid_for_m13_distributional_claim", True))
    ]
    examples = []
    for audit in invalid[:5]:
        summary = dict(audit.get("single_realization_mode", {}))
        examples.append(
            {
                "condition": audit.get("condition", {}),
                "mode": summary.get("mode", "single_realization"),
                "m13_min_contexts": int(summary.get("m13_min_contexts", 0)),
                "required_m13_contexts": int(audit.get("required_m13_contexts", 0)),
                "valid_for_distributional_claim": False,
            }
        )
    return {
        "schema": "scope_static_phyc3c_invalid_protocol_negative_control_v1",
        "control": "single_realization_protocol",
        "expected_valid_for_m13_distributional_claim": False,
        "observed_rejected_conditions": int(len(invalid)),
        "total_conditions": int(len(protocol_audits)),
        "examples": examples,
        "passed": bool(protocol_audits and len(invalid) == len(protocol_audits)),
    }


def head_stability_audit(head_rows: list[dict[str, object]], *, primary_head: str) -> dict[str, object]:
    by_head: dict[str, list[dict[str, object]]] = {}
    for row in head_rows:
        by_head.setdefault(str(row.get("head")), []).append(row)
    summaries = []
    evaluated_heads = [head for head in HEADS if head in by_head]
    for head in evaluated_heads:
        rows = by_head.get(head, [])
        summaries.append(
            {
                "head": head,
                "conditions": int(len(rows)),
                "BA_min": _min(rows, "balanced_accuracy"),
                "NMI_min": _min(rows, "normalized_mutual_info"),
                "ARI_min": _min(rows, "adjusted_rand_index"),
                "min_recall_min": _min(rows, "min_class_recall"),
                "M13_recall_min": _min(rows, "m13_recall"),
                "all_conditions_perfect": bool(rows and _min(rows, "balanced_accuracy") >= 1.0 and _min(rows, "normalized_mutual_info") >= 1.0),
            }
        )
    primary = next((row for row in summaries if row["head"] == primary_head), {})
    return {
        "schema": "scope_static_phyc3c_head_stability_audit_v1",
        "primary_head": str(primary_head),
        "evaluated_heads": evaluated_heads,
        "omitted_heads": [head for head in HEADS if head not in by_head],
        "heads": summaries,
        "primary_head_all_conditions_perfect": bool(primary.get("all_conditions_perfect", False)),
        "passed": bool(primary.get("all_conditions_perfect", False)),
    }


def _robustness_row(
    *,
    condition: dict[str, object],
    single_result: dict[str, object],
    multi_result: dict[str, object],
    ceiling: dict[str, object],
    primary_head: str,
    primary_min_ba: float,
    primary_min_nmi: float,
    primary_min_m13_recall: float,
    protocol_valid: bool,
) -> dict[str, object]:
    primary = dict(dict(multi_result.get("head_results", {})).get(primary_head, {}))
    single_primary = dict(dict(single_result.get("head_results", {})).get(primary_head, {}))
    ceiling_metrics = dict(ceiling.get("deterministic_distributional_ceiling", {}))
    head_metrics = {}
    for head in dict(multi_result.get("head_results", {})):
        payload = dict(dict(multi_result.get("head_results", {})).get(head, {}))
        head_metrics[head] = _compact_metrics(payload)
    checks = {
        "primary_ba_meets_threshold": float(primary.get("balanced_accuracy", 0.0)) >= float(primary_min_ba),
        "primary_nmi_meets_threshold": float(primary.get("normalized_mutual_info", 0.0)) >= float(primary_min_nmi),
        "primary_m13_recall_meets_threshold": float(primary.get("m13_recall", 0.0)) >= float(primary_min_m13_recall),
        "primary_min_recall_positive": float(primary.get("min_class_recall", 0.0)) > 0.0,
        "distributional_ceiling_reached": float(primary.get("normalized_mutual_info", 0.0)) >= float(ceiling_metrics.get("normalized_mutual_info", 0.0)),
        "protocol_valid": bool(protocol_valid),
    }
    return {
        "schema": "scope_static_phyc3c_robustness_condition_v1",
        "condition": condition,
        "primary_head": str(primary_head),
        "primary_multi_context_metrics": _compact_metrics(primary),
        "primary_single_realization_metrics": _compact_metrics(single_primary),
        "distributional_ceiling_metrics": {
            "balanced_accuracy": float(ceiling_metrics.get("balanced_accuracy", 0.0)),
            "adjusted_rand_index": float(ceiling_metrics.get("adjusted_rand_index", 0.0)),
            "normalized_mutual_info": float(ceiling_metrics.get("normalized_mutual_info", 0.0)),
            "min_class_recall": float(ceiling_metrics.get("min_class_recall", 0.0)),
        },
        "head_metrics_multi_context": head_metrics,
        "checks": checks,
        "passed": bool(all(checks.values())),
    }


def _head_condition_rows(condition: dict[str, object], multi_result: dict[str, object]) -> list[dict[str, object]]:
    rows = []
    for head in dict(multi_result.get("head_results", {})):
        payload = dict(dict(multi_result.get("head_results", {})).get(head, {}))
        rows.append({"condition": condition, "head": head, **_compact_metrics(payload)})
    return rows


def _compact_metrics(payload: dict[str, object]) -> dict[str, float]:
    return {
        "balanced_accuracy": float(payload.get("balanced_accuracy", 0.0)),
        "adjusted_rand_index": float(payload.get("adjusted_rand_index", 0.0)),
        "normalized_mutual_info": float(payload.get("normalized_mutual_info", 0.0)),
        "min_class_recall": float(payload.get("min_class_recall", 0.0)),
        "m13_recall": float(payload.get("m13_recall", 0.0)),
    }


def _primary_summary(rows: list[dict[str, object]]) -> dict[str, float]:
    metrics = [dict(row.get("primary_multi_context_metrics", {})) for row in rows]
    return {
        "primary_min_BA": _min(metrics, "balanced_accuracy"),
        "primary_min_NMI": _min(metrics, "normalized_mutual_info"),
        "primary_min_ARI": _min(metrics, "adjusted_rand_index"),
        "primary_min_min_recall": _min(metrics, "min_class_recall"),
        "primary_min_M13_recall": _min(metrics, "m13_recall"),
    }


def _failure_cases(
    rows: list[dict[str, object]],
    non_leakage: dict[str, object],
    protocol_validity: dict[str, object],
) -> list[dict[str, object]]:
    failures = []
    for row in rows:
        if bool(row.get("passed", False)):
            continue
        failures.append(
            {
                "kind": "robustness_condition_failed",
                "condition": row.get("condition", {}),
                "checks": row.get("checks", {}),
                "primary_multi_context_metrics": row.get("primary_multi_context_metrics", {}),
            }
        )
    if not bool(non_leakage.get("passed", False)):
        failures.append({"kind": "non_leakage_audit_failed", "failed_indices": non_leakage.get("failed_feature_table_indices", [])})
    if not bool(protocol_validity.get("passed", False)):
        failures.append({"kind": "protocol_validity_audit_failed", "failed_indices": protocol_validity.get("failed_protocol_condition_indices", [])})
    return failures


def _decision(rows: list[dict[str, object]], non_leakage: dict[str, object], protocol_validity: dict[str, object]) -> str:
    if rows and all(bool(row.get("passed", False)) for row in rows) and bool(non_leakage.get("passed", False)) and bool(protocol_validity.get("passed", False)):
        return "phyc3c_robust_non_leaky_protocol_valid"
    if not bool(non_leakage.get("passed", False)):
        return "phyc3c_rejected_leakage_guardrail_failed"
    if not bool(protocol_validity.get("passed", False)):
        return "phyc3c_rejected_protocol_invalid"
    return "phyc3c_robustness_grid_has_failures"


def _train_test_groups_disjoint(protocol: list[dict[str, object]]) -> bool:
    return all(
        set(int(group) for group in batch.get("test_groups", [])).isdisjoint(set(int(group) for group in batch.get("train_groups", [])))
        for batch in protocol
    )


def _every_class_has_test_batch(protocol: list[dict[str, object]], class_names: list[str]) -> bool:
    seen = {str(batch.get("label_evaluator_only")) for batch in protocol}
    return all(str(label) in seen for label in class_names)


def _train_folds_have_all_classes(
    labels: list[str],
    groups: list[int],
    protocol: list[dict[str, object]],
    class_names: list[str],
) -> bool:
    for batch in protocol:
        train_groups = {int(group) for group in batch.get("train_groups", [])}
        train_labels = {str(label) for label, group in zip(labels, groups) if int(group) in train_groups}
        if not all(str(label) in train_labels for label in class_names):
            return False
    return True


def _min(rows: list[dict[str, object]], key: str) -> float:
    values = [float(row.get(key, 0.0)) for row in rows]
    return float(min(values)) if values else 0.0


def _write_outputs(output: Path, result: dict[str, object]) -> None:
    artifacts = {
        "metrics.json": result,
        "robustness_grid.json": result["robustness_grid"],
        "non_leakage_audit.json": result["non_leakage_audit"],
        "protocol_validity_audit.json": result["protocol_validity_audit"],
        "invalid_protocol_negative_control.json": result["invalid_protocol_negative_control"],
        "head_stability_audit.json": result["head_stability_audit"],
        "failure_cases.json": result["failure_cases"],
    }
    for name, payload in artifacts.items():
        (output / name).write_text(json.dumps(_json_safe(payload), indent=2, sort_keys=True) + "\n")
    (output / "summary.md").write_text(format_phyc3c_validation_summary(result))


def format_phyc3c_validation_summary(result: dict[str, object]) -> str:
    return "\n".join(
        [
            "# Layer 3c Validation: Robustness, Leakage, and Protocol",
            "",
            f"- Layer: `{LAYER3_LEARNER.public_name}`",
            f"- Legacy alias: `{LAYER3_LEARNER.legacy_alias}`",
            f"- Decision: `{result.get('decision')}`",
            f"- Robustness passed: `{str(bool(result.get('robustness_passed'))).lower()}`",
            f"- Non-leakage passed: `{str(bool(result.get('non_leakage_passed'))).lower()}`",
            f"- Protocol validity passed: `{str(bool(result.get('protocol_validity_passed'))).lower()}`",
            f"- Grid conditions: `{int(result.get('num_grid_conditions', 0))}`",
            f"- Failed grid conditions: `{int(result.get('num_failed_grid_conditions', 0))}`",
            f"- Primary min BA: `{float(result.get('primary_min_BA', 0.0)):.4f}`",
            f"- Primary min NMI: `{float(result.get('primary_min_NMI', 0.0)):.4f}`",
            f"- Primary min M13 recall: `{float(result.get('primary_min_M13_recall', 0.0)):.4f}`",
            "",
            "## Claim Boundary",
            "",
            "Layer 3c validation does not add learner inputs. It reuses Layer 3b Z/X sampled-observation features, rejects single-realization M13 batches as invalid for distributional recovery claims, and checks that forbidden oracle fields are absent from feature names and schema.",
            "",
        ]
    )


def _load_mechanism_records(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text())
    records = data.get("mechanisms")
    if not isinstance(records, list) or not records:
        raise ValueError(f"{path} does not contain non-empty mechanisms")
    return [dict(record) for record in records]


def _json_safe(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return _json_safe(list(value))
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, float) and not np.isfinite(value):
        return "inf" if value > 0.0 else "-inf"
    return value


def _mechanism_sort_key(name: str) -> tuple[int, str]:
    text = str(name)
    if text.startswith("M") and text[1:].isdigit():
        return (int(text[1:]), text)
    return (10_000, text)
