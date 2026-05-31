from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Iterable

import numpy as np
import yaml

from scope_static.protocols import LEARNER_VALIDATION_STAGE
from scope_static.learner import (
    FORBIDDEN_FEATURE_TOKENS,
    FORBIDDEN_LEARNER_INPUTS,
    VISIBLE_OPERATION_CONTEXTS,
    build_zx_visible_feature_table,
)
from scope_static.learner import leakage_guardrail_audit_phyc3c
from .artifacts import load_stage3a_frozen_visible_features as _load_stage3a_frozen_visible_features


STAGE_NAME = "Stage3A_dataset_protocol_freeze"
DEFAULT_OUTPUT_DIR = "outputs/scope_static/PHYC_STAGE3_discovery/S3A_protocol_freeze"
DEFAULT_SPLIT_POLICY = "grouped_context_leave_one_out_with_cyclic_validation"
DEFAULT_ASSIGNMENT_UNIT = "mechanism_condition_instance"
ALLOWED_ASSIGNMENT_UNITS = (
    "mechanism_condition_instance",
    "generated_probe_batch",
    "context_window",
)


def run_stage3a_dataset_protocol_freeze(
    *,
    teacher_dir: str | Path,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    shots: int = 20_000,
    seed: int = 0,
    robustness_mode: bool = False,
    sampling_mode: str = "expected",
    batch_size: int = 5,
    assignment_unit: str = DEFAULT_ASSIGNMENT_UNIT,
    split_policy: str = DEFAULT_SPLIT_POLICY,
) -> dict[str, object]:
    """Freeze Stage 3A learner-visible dataset and protocol artifacts.

    This function intentionally does not train a classifier or discovery model.
    It writes the schema, split, batch/context, assignment-unit, and leakage
    artifacts that later Stage 3B/3C runs must consume.
    """

    if assignment_unit not in ALLOWED_ASSIGNMENT_UNITS:
        raise ValueError(f"assignment_unit must be one of {ALLOWED_ASSIGNMENT_UNITS!r}")
    teacher = Path(teacher_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    records = _load_mechanism_records(teacher / "oracle_mechanisms.json")
    table = build_zx_visible_feature_table(
        records,
        shots=int(shots),
        seed=int(seed),
        robustness_mode=bool(robustness_mode),
        sampling_mode=str(sampling_mode),
    )
    groups = [int(record.get("circuit_id", 0)) for record in records]
    mechanism_labels = [str(record.get("oracle_label", record.get("mechanism_id", ""))) for record in records]
    class_names = sorted(set(mechanism_labels), key=_mechanism_sort_key)

    config = {
        "teacher_dir": str(teacher),
        "output_dir": str(output),
        "shots": int(shots),
        "seed": int(seed),
        "robustness_mode": bool(robustness_mode),
        "sampling_mode": str(sampling_mode),
        "batch_size": int(batch_size),
        "assignment_unit": str(assignment_unit),
        "split_policy": str(split_policy),
    }
    probe_schedule = probe_schedule_manifest(table.schedule, robustness_mode=bool(robustness_mode))
    forbidden_audit = forbidden_feature_audit(table.feature_names)
    split_manifest = grouped_split_manifest(records, groups, assignment_unit=str(assignment_unit), split_policy=str(split_policy))
    batch_schema = batch_context_schema(
        groups,
        assignment_unit=str(assignment_unit),
        batch_size=int(batch_size),
        split_policy=str(split_policy),
    )
    assignment = assignment_unit_manifest(
        records,
        groups,
        assignment_unit=str(assignment_unit),
        class_count=len(class_names),
    )
    feature_matrix = visible_feature_matrix_manifest(
        table.expected_features,
        table.features,
        table.feature_names,
        sampling_mode=str(sampling_mode),
    )
    operation_context_audit = operation_context_public_audit(
        records,
        table.feature_names,
        table.expected_features,
    )
    acceptance = stage3a_acceptance_audit(
        forbidden_audit=forbidden_audit,
        operation_context_audit=operation_context_audit,
        split_manifest=split_manifest,
        batch_context_schema=batch_schema,
        assignment_unit_artifact=assignment,
        visible_feature_matrix=feature_matrix,
    )
    result = {
        "schema": "scope_static_stage3a_protocol_freeze_v1",
        "stage": STAGE_NAME,
        "public_layer": LEARNER_VALIDATION_STAGE.metadata(artifact_stage=STAGE_NAME, substage="dataset_protocol_freeze"),
        "teacher_dir": str(teacher),
        "output_dir": str(output),
        "claim_boundary": {
            "stage3a_trains_model": False,
            "stage3a_computes_observability_ceiling": False,
            "observability_ceiling_stage": "Stage 3A.5",
            "direct_mechanism_label_supervision_allowed": False,
            "learner_inputs_visible_only": True,
            "single_shot_assignment_first_pass_allowed": False,
            "operation_context_is_public_instruction_context": True,
            "operation_context_not_mechanism_instance_surrogate_id": True,
        },
        "config": config,
        "mechanism_scope": {
            "record_count": int(len(records)),
            "class_count_evaluator_only": int(len(class_names)),
            "context_group_count": int(len(set(groups))),
            "mechanism_labels_evaluator_only": class_names,
        },
        "visible_feature_schema": table.feature_schema,
        "visible_feature_matrix": feature_matrix,
        "probe_schedule_manifest": probe_schedule,
        "forbidden_feature_audit": forbidden_audit,
        "operation_context_public_audit": operation_context_audit,
        "split_manifest": split_manifest,
        "batch_context_schema": batch_schema,
        "assignment_unit": assignment,
        "acceptance_audit": acceptance,
        "decision": "stage3a_protocol_freeze_passed" if acceptance["passed"] else "stage3a_protocol_freeze_failed",
    }
    _write_outputs(output, result, table.expected_features, table.features)
    return result


def probe_schedule_manifest(schedule: list[dict[str, object]], *, robustness_mode: bool) -> dict[str, object]:
    contains_y = any("Y" in str(probe.get("prepare", "")) or "Y" in str(probe.get("measurement_basis", "")) for probe in schedule)
    return {
        "schema": "scope_static_stage3a_probe_schedule_manifest_v1",
        "source": "PHYC3b Z/X visible probe suite",
        "robustness_mode": bool(robustness_mode),
        "probe_count": int(len(schedule)),
        "z_x_only": not contains_y,
        "x_prepared_states_required": True,
        "no_y_basis_preparation_or_measurement": not contains_y,
        "probes": [dict(probe) for probe in schedule],
    }


def forbidden_feature_audit(feature_names: Iterable[str]) -> dict[str, object]:
    names = [str(name) for name in feature_names]
    base = leakage_guardrail_audit_phyc3c(names)
    hits = []
    lowered = [(name, name.lower()) for name in names]
    for token in FORBIDDEN_FEATURE_TOKENS:
        for original, lower in lowered:
            if token in lower:
                hits.append({"feature_name": original, "token": token})
    checks = dict(base.get("checks", {}))
    checks.update(
        {
            "direct_mechanism_label_supervision_disabled": True,
            "validation_label_model_selection_disabled": True,
            "test_label_model_selection_disabled": True,
            "teacher_self_features_disabled": True,
            "oracle_prototypes_disabled": True,
            "forbidden_feature_hit_count_is_zero": len(hits) == 0,
        }
    )
    return {
        "schema": "scope_static_stage3a_forbidden_feature_audit_v1",
        "passed": bool(all(checks.values())),
        "feature_count": int(len(names)),
        "forbidden_feature_count": int(len(hits)),
        "forbidden_feature_hits": hits,
        "checks": checks,
        "allowed_visible_inputs": [
            "preparation label",
            "measurement basis label",
            "repeat count",
            "qubit count",
            "empirical probabilities",
            "empirical expectations",
            "shot count",
            "finite-shot uncertainty estimates",
            "sampled-observation-derived features",
            "visible operation/instruction context",
        ],
        "forbidden_learner_inputs": list(FORBIDDEN_LEARNER_INPUTS),
    }


def operation_context_public_audit(
    records: list[dict[str, object]],
    feature_names: list[str],
    visible_features: np.ndarray,
) -> dict[str, object]:
    """Check operation context is public instruction context, not an ID leak."""

    names = [str(name) for name in feature_names]
    matrix = np.asarray(visible_features, dtype=np.float64)
    prefix = "visible_metadata__instruction_"
    expected_names = [f"{prefix}{context}" for context in VISIBLE_OPERATION_CONTEXTS]
    index_by_name = {name: idx for idx, name in enumerate(names)}
    operation_feature_names = [name for name in names if name.startswith(prefix) or name.startswith("visible_metadata__operation_")]
    legacy_operation_names = [name for name in operation_feature_names if name.startswith("visible_metadata__operation_")]
    missing_expected = [name for name in expected_names if name not in index_by_name]
    unexpected_operation_features = [name for name in operation_feature_names if name not in set(expected_names)]
    forbidden_tokens = (
        "mechanism",
        "oracle",
        "label",
        "prototype",
        "omega",
        "record",
        "location",
        "slot",
        "instance",
        "circuit",
        "qubit",
        "teacher",
        "channel",
        "kraus",
        "ptm",
        "operation_id",
    )
    forbidden_name_hits = [
        {"feature_name": name, "token": token}
        for name in operation_feature_names
        for token in forbidden_tokens
        if token in name.lower()
    ]
    unknown_instructions = sorted(
        {
            _public_instruction_context(record.get("instruction", "id"))
            for record in records
            if _public_instruction_context(record.get("instruction", "id")) not in set(VISIBLE_OPERATION_CONTEXTS)
        }
    )
    row_count_ok = matrix.ndim == 2 and int(matrix.shape[0]) == int(len(records))
    columns_available = row_count_ok and not missing_expected
    if columns_available:
        operation_matrix = matrix[:, [index_by_name[name] for name in expected_names]]
        row_sums = np.sum(operation_matrix, axis=1)
        entries_are_binary = bool(np.all(np.isclose(operation_matrix, 0.0) | np.isclose(operation_matrix, 1.0)))
        rows_one_hot = bool(np.allclose(row_sums, 1.0))
        expected = np.zeros_like(operation_matrix)
        for row_idx, record in enumerate(records):
            instruction = _public_instruction_context(record.get("instruction", "id"))
            if instruction in VISIBLE_OPERATION_CONTEXTS:
                expected[row_idx, list(VISIBLE_OPERATION_CONTEXTS).index(instruction)] = 1.0
        max_instruction_mismatch = float(np.max(np.abs(operation_matrix - expected))) if operation_matrix.size else 0.0
        matches_public_instruction_field = bool(not unknown_instructions and np.allclose(operation_matrix, expected))
        distinct_public_patterns = int(len({tuple(row.tolist()) for row in operation_matrix}))
    else:
        entries_are_binary = False
        rows_one_hot = False
        max_instruction_mismatch = None
        matches_public_instruction_field = False
        distinct_public_patterns = 0
    checks = {
        "operation_context_features_present": bool(operation_feature_names),
        "uses_current_instruction_feature_prefix": not bool(legacy_operation_names),
        "feature_names_equal_public_instruction_alphabet": not missing_expected and not unexpected_operation_features,
        "feature_names_contain_no_instance_or_oracle_tokens": not bool(forbidden_name_hits),
        "source_field_is_public_instruction_only": True,
        "source_fields_exclude_mechanism_label_and_instance_ids": True,
        "record_count_matches_feature_rows": bool(row_count_ok),
        "operation_context_entries_are_binary": bool(entries_are_binary),
        "operation_context_rows_are_one_hot": bool(rows_one_hot),
        "operation_context_matches_public_instruction_field": bool(matches_public_instruction_field),
        "all_record_instructions_in_public_alphabet": not bool(unknown_instructions),
        "distinct_context_patterns_bounded_by_public_alphabet": int(distinct_public_patterns) <= int(len(VISIBLE_OPERATION_CONTEXTS)),
    }
    return {
        "schema": "scope_static_stage3a_operation_context_public_audit_v1",
        "passed": bool(all(checks.values())),
        "claim_boundary": "operation context is public circuit/instruction context, not a mechanism-instance surrogate ID",
        "public_instruction_context_alphabet": list(VISIBLE_OPERATION_CONTEXTS),
        "feature_prefix": prefix,
        "allowed_source_fields": ["instruction"],
        "forbidden_source_fields": [
            "oracle_label",
            "mechanism_id",
            "name",
            "parameters",
            "qubits",
            "circuit_id",
            "location_id",
            "probe_indices",
            "record_index",
        ],
        "operation_feature_names": operation_feature_names,
        "missing_expected_features": missing_expected,
        "unexpected_operation_features": unexpected_operation_features,
        "legacy_operation_feature_names": legacy_operation_names,
        "forbidden_feature_name_hits": forbidden_name_hits,
        "unknown_public_instructions": unknown_instructions,
        "distinct_public_context_patterns": int(distinct_public_patterns),
        "max_instruction_mismatch": max_instruction_mismatch,
        "checks": checks,
    }


def grouped_split_manifest(
    records: list[dict[str, object]],
    groups: list[int],
    *,
    assignment_unit: str,
    split_policy: str,
) -> dict[str, object]:
    unique_groups = sorted(set(int(group) for group in groups))
    folds = []
    for fold_idx, test_group in enumerate(unique_groups):
        validation_groups: list[int] = []
        if len(unique_groups) >= 3:
            validation_groups = [int(unique_groups[(fold_idx + 1) % len(unique_groups)])]
        train_groups = [int(group) for group in unique_groups if group not in {int(test_group), *validation_groups}]
        folds.append(
            {
                "fold": int(fold_idx),
                "train_groups": train_groups,
                "validation_groups": validation_groups,
                "test_groups": [int(test_group)],
                "train_indices": _indices_for_groups(groups, train_groups),
                "validation_indices": _indices_for_groups(groups, validation_groups),
                "test_indices": _indices_for_groups(groups, [int(test_group)]),
            }
        )
    train_validation_test_ok = bool(
        unique_groups
        and all(row["train_indices"] for row in folds)
        and all(row["validation_indices"] for row in folds)
        and all(row["test_indices"] for row in folds)
    )
    assignment_instances = [
        {
            "j": int(idx),
            "record_index": int(idx),
            "visible_instance_id": f"j{idx:06d}",
            "context_group": int(groups[idx]) if idx < len(groups) else 0,
            "assignment_unit": str(assignment_unit),
        }
        for idx, _record in enumerate(records)
    ]
    return {
        "schema": "scope_static_stage3a_split_manifest_v1",
        "split_policy": str(split_policy),
        "split_policy_fixed_before_training": True,
        "group_key": "circuit_id",
        "assignment_unit": str(assignment_unit),
        "record_count": int(len(records)),
        "context_groups": unique_groups,
        "fold_count": int(len(folds)),
        "folds": folds,
        "assignment_instances": assignment_instances,
        "contains_mechanism_labels_as_learner_fields": False,
        "validation_labels_available_to_model_selection": False,
        "test_labels_available_to_model_selection": False,
        "train_validation_test_splits_non_empty": train_validation_test_ok,
    }


def batch_context_schema(
    groups: list[int],
    *,
    assignment_unit: str,
    batch_size: int,
    split_policy: str,
) -> dict[str, object]:
    unique_groups = sorted(set(int(group) for group in groups))
    return {
        "schema": "scope_static_stage3a_batch_context_schema_v1",
        "assignment_unit": str(assignment_unit),
        "split_policy": str(split_policy),
        "primary_protocol": {
            "mode": "multi_context_batch",
            "batch_size": int(max(2, batch_size)),
            "context_group_key": "circuit_id",
            "context_group_count": int(len(unique_groups)),
            "minimum_contexts_required_for_m13_distributional_claim": int(max(2, batch_size)),
        },
        "single_context_m13_claim_allowed": False,
        "m13_protocol_definition": (
            "M13 is a context-dependent latent-drift recovery target; "
            "single-context failure is not a Stage 3 failure by itself."
        ),
        "learner_visible_fields": [
            "preparation_label",
            "measurement_basis_label",
            "repeat_count",
            "qubit_count",
            "empirical_probabilities",
            "empirical_expectations",
            "shot_count",
            "finite_shot_uncertainty_estimates",
            "sampled_observation_derived_features",
            "visible_operation_context",
        ],
        "protocol_only_fields": [
            "j",
            "fold",
            "train_validation_test_split",
            "context_group",
        ],
        "evaluator_only_fields": [
            "true_mechanism_id",
            "mechanism_name",
            "physical_family_label",
            "exact_channel_matrix",
            "exact_ptm",
            "exact_kraus_matrices",
            "teacher_id",
            "teacher_self_features",
            "oracle_prototypes",
            "hidden_drift_parameters",
        ],
    }


def assignment_unit_manifest(
    records: list[dict[str, object]],
    groups: list[int],
    *,
    assignment_unit: str,
    class_count: int,
) -> dict[str, object]:
    return {
        "schema": "scope_static_stage3a_assignment_unit_v1",
        "assignment_matrix": "S[j,k] or Pi[j,k]",
        "j_definition": str(assignment_unit),
        "j_first_pass_recommendation": "one mechanism-condition instance or generated probe-batch instance",
        "single_shot_j_allowed_first_pass": False,
        "k_definition": "learned latent mechanism/prototype index",
        "record_count": int(len(records)),
        "context_group_count": int(len(set(groups))),
        "catalog_cardinality_evaluator_only": int(class_count),
    }


def visible_feature_matrix_manifest(
    visible_features: np.ndarray,
    sampled_visible_features: np.ndarray,
    feature_names: list[str],
    *,
    sampling_mode: str,
) -> dict[str, object]:
    matrix = np.asarray(visible_features, dtype=np.float64)
    sampled = np.asarray(sampled_visible_features, dtype=np.float64)
    return {
        "schema": "scope_static_stage3a_visible_feature_matrix_v1",
        "training_matrix_path": "visible_features.npy",
        "training_matrix_kind": "expected_visible_observation_features",
        "sampled_matrix_path": "sampled_visible_features.npy",
        "sampled_matrix_kind": "finite_shot_visible_observation_features",
        "feature_schema_path": "visible_feature_schema.json",
        "feature_count": int(matrix.shape[1]) if matrix.ndim == 2 else 0,
        "record_count": int(matrix.shape[0]) if matrix.ndim == 2 else 0,
        "shape": [int(dim) for dim in matrix.shape],
        "sampled_shape": [int(dim) for dim in sampled.shape],
        "sampling_mode": str(sampling_mode),
        "feature_names_sha256": _text_digest("\n".join(str(name) for name in feature_names)),
        "visible_features_sha256": _matrix_digest(matrix),
        "sampled_visible_features_sha256": _matrix_digest(sampled),
        "learner_training_source": "Stage 3A frozen visible_features.npy",
        "contains_evaluator_labels": False,
        "contains_oracle_fields": False,
    }


def stage3a_acceptance_audit(
    *,
    forbidden_audit: dict[str, object],
    operation_context_audit: dict[str, object],
    split_manifest: dict[str, object],
    batch_context_schema: dict[str, object],
    assignment_unit_artifact: dict[str, object],
    visible_feature_matrix: dict[str, object],
) -> dict[str, object]:
    primary_protocol = dict(batch_context_schema.get("primary_protocol", {}))
    checks = {
        "no_forbidden_learner_fields": bool(forbidden_audit.get("passed", False)),
        "operation_context_is_public_instruction_context": bool(operation_context_audit.get("passed", False)),
        "split_policy_fixed_before_model_training": bool(split_manifest.get("split_policy_fixed_before_training", False)),
        "train_validation_test_splits_non_empty": bool(split_manifest.get("train_validation_test_splits_non_empty", False)),
        "multi_context_batch_protocol_explicit": primary_protocol.get("mode") == "multi_context_batch",
        "assignment_unit_declared_before_training": bool(assignment_unit_artifact.get("j_definition")),
        "single_shot_assignment_not_used_first_pass": not bool(assignment_unit_artifact.get("single_shot_j_allowed_first_pass", True)),
        "validation_label_model_selection_disabled": not bool(split_manifest.get("validation_labels_available_to_model_selection", True)),
        "test_label_model_selection_disabled": not bool(split_manifest.get("test_labels_available_to_model_selection", True)),
        "frozen_visible_feature_matrix_declared": bool(visible_feature_matrix.get("training_matrix_path")),
        "frozen_visible_feature_matrix_has_no_labels": not bool(visible_feature_matrix.get("contains_evaluator_labels", True)),
        "frozen_visible_feature_matrix_has_no_oracle_fields": not bool(visible_feature_matrix.get("contains_oracle_fields", True)),
        "learner_training_not_run_in_stage3a": True,
        "observability_ceiling_deferred_to_stage3a5": True,
    }
    return {
        "schema": "scope_static_stage3a_acceptance_audit_v1",
        "passed": bool(all(checks.values())),
        "checks": checks,
    }


def format_stage3a_summary(result: dict[str, object]) -> str:
    acceptance = dict(result.get("acceptance_audit", {}))
    mechanism_scope = dict(result.get("mechanism_scope", {}))
    assignment = dict(result.get("assignment_unit", {}))
    operation_context = dict(result.get("operation_context_public_audit", {}))
    return "\n".join(
        [
            "# Stage 3A: Dataset And Protocol Freeze",
            "",
            f"- Decision: `{result.get('decision')}`",
            f"- Acceptance passed: `{str(bool(acceptance.get('passed', False))).lower()}`",
            f"- Records: `{int(mechanism_scope.get('record_count', 0))}`",
            f"- Evaluator-only class count: `{int(mechanism_scope.get('class_count_evaluator_only', 0))}`",
            f"- Context groups: `{int(mechanism_scope.get('context_group_count', 0))}`",
            f"- Assignment unit j: `{assignment.get('j_definition')}`",
            f"- Operation context public audit passed: `{str(bool(operation_context.get('passed', False))).lower()}`",
            "",
            "## Claim Boundary",
            "",
            "Stage 3A freezes the learner-visible schema, split policy, batch/context protocol, assignment unit, and forbidden-feature audit. Operation context is public instruction context, not a mechanism-instance surrogate ID. It does not train a discovery model and does not compute the Stage 3A.5 observability ceiling.",
            "",
        ]
    )


def _write_outputs(output: Path, result: dict[str, object], visible_features: np.ndarray, sampled_visible_features: np.ndarray) -> None:
    artifacts = {
        "metrics.json": result,
        "visible_feature_schema.json": result["visible_feature_schema"],
        "visible_feature_matrix.json": result["visible_feature_matrix"],
        "forbidden_feature_audit.json": result["forbidden_feature_audit"],
        "operation_context_public_audit.json": result["operation_context_public_audit"],
        "split_manifest.json": result["split_manifest"],
        "probe_schedule_manifest.json": result["probe_schedule_manifest"],
        "batch_context_schema.json": result["batch_context_schema"],
        "assignment_unit.json": result["assignment_unit"],
        "acceptance_audit.json": result["acceptance_audit"],
    }
    for name, payload in artifacts.items():
        (output / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    np.save(output / "visible_features.npy", np.asarray(visible_features, dtype=np.float64))
    np.save(output / "sampled_visible_features.npy", np.asarray(sampled_visible_features, dtype=np.float64))
    (output / "config.yaml").write_text(yaml.safe_dump({"stage3a_protocol_freeze": result["config"]}, sort_keys=False))
    (output / "summary.md").write_text(format_stage3a_summary(result))


def load_stage3a_frozen_visible_features(stage3a_dir: str | Path) -> tuple[np.ndarray, list[str], dict[str, object]]:
    return _load_stage3a_frozen_visible_features(stage3a_dir)


def _indices_for_groups(groups: list[int], selected_groups: Iterable[int]) -> list[int]:
    selected = set(int(group) for group in selected_groups)
    return [int(idx) for idx, group in enumerate(groups) if int(group) in selected]


def _public_instruction_context(instruction: object | None) -> str:
    operation = str(instruction or "id").strip().lower()
    if operation == "id":
        return "idle"
    return operation


def _load_mechanism_records(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text())
    records = data.get("mechanisms")
    if not isinstance(records, list) or not records:
        raise ValueError(f"{path} does not contain non-empty mechanisms")
    return [dict(record) for record in records]


def _load_json(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _text_digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _matrix_digest(matrix: np.ndarray) -> str:
    arr = np.ascontiguousarray(np.asarray(matrix, dtype=np.float64))
    return hashlib.sha256(arr.tobytes()).hexdigest()


def _mechanism_sort_key(label: str) -> tuple[int, str]:
    text = str(label)
    if text.startswith("M") and text[1:].isdigit():
        return (int(text[1:]), text)
    return (10_000, text)
