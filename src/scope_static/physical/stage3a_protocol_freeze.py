from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Iterable

import numpy as np
import yaml

from .layers import LAYER3_LEARNER
from .phyc3b_zx_visible_probe_suite import (
    FORBIDDEN_FEATURE_TOKENS,
    FORBIDDEN_LEARNER_INPUTS,
    build_zx_visible_feature_table,
)
from .phyc3c_gaussian_likelihood import leakage_guardrail_audit_phyc3c


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
    acceptance = stage3a_acceptance_audit(
        forbidden_audit=forbidden_audit,
        split_manifest=split_manifest,
        batch_context_schema=batch_schema,
        assignment_unit_artifact=assignment,
        visible_feature_matrix=feature_matrix,
    )
    result = {
        "schema": "scope_static_stage3a_protocol_freeze_v1",
        "stage": STAGE_NAME,
        "public_layer": LAYER3_LEARNER.metadata(artifact_stage=STAGE_NAME, substage="dataset_protocol_freeze"),
        "teacher_dir": str(teacher),
        "output_dir": str(output),
        "claim_boundary": {
            "stage3a_trains_model": False,
            "stage3a_computes_observability_ceiling": False,
            "observability_ceiling_stage": "Stage 3A.5",
            "direct_mechanism_label_supervision_allowed": False,
            "learner_inputs_visible_only": True,
            "single_shot_assignment_first_pass_allowed": False,
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
        ],
        "forbidden_learner_inputs": list(FORBIDDEN_LEARNER_INPUTS),
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
    split_manifest: dict[str, object],
    batch_context_schema: dict[str, object],
    assignment_unit_artifact: dict[str, object],
    visible_feature_matrix: dict[str, object],
) -> dict[str, object]:
    primary_protocol = dict(batch_context_schema.get("primary_protocol", {}))
    checks = {
        "no_forbidden_learner_fields": bool(forbidden_audit.get("passed", False)),
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
            "",
            "## Claim Boundary",
            "",
            "Stage 3A freezes the learner-visible schema, split policy, batch/context protocol, assignment unit, and forbidden-feature audit. It does not train a discovery model and does not compute the Stage 3A.5 observability ceiling.",
            "",
        ]
    )


def _write_outputs(output: Path, result: dict[str, object], visible_features: np.ndarray, sampled_visible_features: np.ndarray) -> None:
    artifacts = {
        "metrics.json": result,
        "visible_feature_schema.json": result["visible_feature_schema"],
        "visible_feature_matrix.json": result["visible_feature_matrix"],
        "forbidden_feature_audit.json": result["forbidden_feature_audit"],
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
    s3a = Path(stage3a_dir)
    manifest_path = s3a / "visible_feature_matrix.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"missing frozen Stage 3A visible feature matrix manifest: {manifest_path}")
    manifest = _load_json(manifest_path)
    matrix_path = s3a / str(manifest.get("training_matrix_path", "visible_features.npy"))
    if not matrix_path.exists():
        raise FileNotFoundError(f"missing frozen Stage 3A visible feature matrix: {matrix_path}")
    matrix = np.asarray(np.load(matrix_path), dtype=np.float64)
    schema = _load_json(s3a / str(manifest.get("feature_schema_path", "visible_feature_schema.json")))
    feature_names = [str(item.get("name", "")) for item in schema.get("features", []) if isinstance(item, dict)]
    if matrix.ndim != 2:
        raise ValueError(f"{matrix_path} must be a 2D visible feature matrix")
    if len(feature_names) != int(matrix.shape[1]):
        raise ValueError(f"{matrix_path} has {matrix.shape[1]} columns but schema has {len(feature_names)} features")
    expected_shape = [int(dim) for dim in manifest.get("shape", [])] if isinstance(manifest.get("shape", []), list) else []
    if expected_shape and expected_shape != [int(dim) for dim in matrix.shape]:
        raise ValueError(f"{matrix_path} shape {matrix.shape} does not match manifest shape {expected_shape}")
    expected_digest = str(manifest.get("visible_features_sha256", ""))
    if expected_digest and _matrix_digest(matrix) != expected_digest:
        raise ValueError(f"{matrix_path} digest does not match Stage 3A manifest")
    out_manifest = dict(manifest)
    out_manifest.update(
        {
            "loaded_from_stage3a_artifact": True,
            "resolved_training_matrix_path": str(matrix_path),
            "resolved_feature_schema_path": str(s3a / str(manifest.get("feature_schema_path", "visible_feature_schema.json"))),
        }
    )
    return matrix, feature_names, out_manifest


def _indices_for_groups(groups: list[int], selected_groups: Iterable[int]) -> list[int]:
    selected = set(int(group) for group in selected_groups)
    return [int(idx) for idx, group in enumerate(groups) if int(group) in selected]


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
