from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import yaml

from scope_static.protocols import LEARNER_VALIDATION_STAGE
from .artifacts import feature_schema_matches_stage3a as _feature_schema_matches_s3a
from .artifacts import load_json_object as _load_json
from .artifacts import load_stage3_evaluator_labels
from .artifacts import load_stage3a_frozen_visible_features
from .artifacts import resolve_teacher_dir
from .discovery_model import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3B1_DIR
from .discovery_model import _context_groups_from_split_manifest
from .generator_learning import evaluate_soft_family_classification
from .generator_learning import evaluate_soft_family_strength_location_audit
from .observability_ceiling import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A5_DIR
from .protocol_freeze import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A_DIR


STAGE_NAME = "Stage5B1_property_recovery"
DEFAULT_OUTPUT_DIR = "outputs/scope_static/PHYC_STAGE3_discovery/S5B1_property_recovery"
DEFAULT_ASSIGNMENT_SOURCE = "stage3b1"
PROPERTY_HEAD_LINEAR_PROTO = "linear_proto_visible_residual_energy"
PROPERTY_HEAD_CONDITIONAL_VISIBLE_CONTEXT = "conditional_visible_context_property_head"
DEFAULT_PROPERTY_HEAD_MODEL = PROPERTY_HEAD_LINEAR_PROTO
ALLOWED_PROPERTY_HEAD_MODELS = (
    PROPERTY_HEAD_LINEAR_PROTO,
    PROPERTY_HEAD_CONDITIONAL_VISIBLE_CONTEXT,
)


def run_stage5b1_property_recovery(
    *,
    stage3a_dir: str | Path = DEFAULT_STAGE3A_DIR,
    stage3a5_dir: str | Path = DEFAULT_STAGE3A5_DIR,
    stage3b1_dir: str | Path = DEFAULT_STAGE3B1_DIR,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    teacher_dir: str | Path | None = None,
    assignment_source: str = DEFAULT_ASSIGNMENT_SOURCE,
    assignment_path: str | Path | None = None,
    assignment_key: str | None = None,
    property_head_model: str = DEFAULT_PROPERTY_HEAD_MODEL,
) -> dict[str, object]:
    """Recover context-relative mechanism properties from fixed assignments.

    S5B1 fits only a visible Linear/Proto property head from frozen Stage 3A
    features and precomputed S3B1/postmerge responsibilities. Evaluator records
    are loaded after that head is fixed to score location, strength, and
    contract-typed mechanism dimensions.
    """

    s3a = Path(stage3a_dir)
    s3a5 = Path(stage3a5_dir)
    s3b1 = Path(stage3b1_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    s3a_metrics = _load_json(s3a / "metrics.json")
    s3a5_metrics = _load_json(s3a5 / "metrics.json") if (s3a5 / "metrics.json").exists() else {}
    s3b1_metrics = _load_json(s3b1 / "metrics.json") if (s3b1 / "metrics.json").exists() else {}
    teacher = resolve_teacher_dir(s3a_metrics, teacher_dir)
    x, feature_names, feature_matrix = load_stage3a_frozen_visible_features(s3a)
    responsibilities, assignment_audit = load_s5b1_assignment_source(
        stage3b1_dir=s3b1,
        assignment_source=str(assignment_source),
        assignment_path=assignment_path,
        assignment_key=assignment_key,
        record_count=int(x.shape[0]),
    )
    feature_match = _feature_schema_matches_s3a(s3a, feature_names)
    split_manifest = dict(s3a_metrics.get("split_manifest", {})) if isinstance(s3a_metrics.get("split_manifest", {}), dict) else {}
    context_groups = _context_groups_from_split_manifest(split_manifest, record_count=int(x.shape[0]))
    head_model = _normalize_property_head_model(property_head_model)
    if head_model == PROPERTY_HEAD_CONDITIONAL_VISIBLE_CONTEXT:
        property_head = fit_conditional_visible_context_property_head(
            x,
            responsibilities,
            feature_names=feature_names,
            context_groups=context_groups,
        )
    else:
        property_head = fit_linear_proto_property_head(
            x,
            responsibilities,
            feature_names=feature_names,
            context_groups=context_groups,
        )

    evaluator = load_stage3_evaluator_labels(s3a, teacher)
    records = evaluator.records
    if len(records) != int(x.shape[0]):
        raise ValueError(f"Stage 3A frozen feature row count {x.shape[0]} does not match evaluator record count {len(records)}")
    family = evaluate_soft_family_classification(
        responsibilities,
        records,
        evaluator_mode="controlled_catalog",
    )
    s5 = evaluate_soft_family_strength_location_audit(
        x,
        responsibilities,
        records,
        feature_names=feature_names,
        evaluator_mode="controlled_catalog",
    )
    location = context_relative_location_recovery_audit(s5)
    strength = context_normalized_strength_recovery_audit(s5)
    targeted = targeted_property_recovery_audit(s5, targets=("M6", "M13", "M18", "M27"))
    contract_breakdown = stage5b1_contract_breakdown_audit(
        family=family,
        s5=s5,
        location=location,
        strength=strength,
        targeted=targeted,
    )
    acceptance = stage5b1_acceptance_audit(
        s3a_metrics=s3a_metrics,
        s3a5_metrics=s3a5_metrics,
        s3b1_metrics=s3b1_metrics,
        feature_match=feature_match,
        assignment_audit=assignment_audit,
        property_head=property_head,
        family=family,
        s5=s5,
        location=location,
        strength=strength,
        targeted=targeted,
        contract_breakdown=contract_breakdown,
    )
    result = {
        "schema": "scope_static_stage5b1_property_recovery_v1",
        "stage": STAGE_NAME,
        "public_layer": LEARNER_VALIDATION_STAGE.metadata(artifact_stage=STAGE_NAME, substage="property_recovery"),
        "stage3a_dir": str(s3a),
        "stage3a5_dir": str(s3a5),
        "stage3b1_dir": str(s3b1),
        "teacher_dir": str(teacher),
        "output_dir": str(output),
        "claim_boundary": {
            "uses_stage3a_frozen_visible_features": True,
            "uses_fixed_stage3b1_or_postmerge_assignments": True,
            "property_head_model": str(property_head.get("model_name", head_model)),
            "uses_mechanism_labels_for_property_head_fit": False,
            "uses_family_labels_for_property_head_fit": False,
            "uses_oracle_location_or_strength_for_property_head_fit": False,
            "uses_evaluator_records_after_fit_for_scoring": True,
            "claims_physical_parameter_recovery": False,
            "discovers_cptp_gksl_channels": False,
        },
        "config": {
            "stage3a_dir": str(s3a),
            "stage3a5_dir": str(s3a5),
            "stage3b1_dir": str(s3b1),
            "teacher_dir": str(teacher),
            "output_dir": str(output),
            "assignment_source": str(assignment_source),
            "assignment_path": None if assignment_path is None else str(assignment_path),
            "assignment_key": None if assignment_key is None else str(assignment_key),
            "property_head_model": head_model,
        },
        "visible_feature_matrix": feature_matrix,
        "feature_schema_match_audit": feature_match,
        "assignment_source_audit": assignment_audit,
        "s5b1_property_recovery_metrics": property_head,
        "soft_family_classification_metrics": family,
        "s5_context_relative_mechanism_effect_audit": s5,
        "mechanism_dimension_recovery_audit": s5.get("mechanism_dimension_recovery_audit", {}),
        "overlay_contract_audit": s5.get("overlay_contract_audit", {}),
        "overlay_recovery_audit": s5.get("overlay_recovery_audit", {}),
        "context_relative_location_recovery_audit": location,
        "context_normalized_strength_recovery_audit": strength,
        "targeted_m6_m13_m18_m27_property_audit": targeted,
        "s5b1_contract_breakdown_audit": contract_breakdown,
        "acceptance_audit": acceptance,
        "decision": "stage5b1_property_recovery_passed" if acceptance["passed"] else "stage5b1_property_recovery_failed",
    }
    _write_outputs(output, result)
    return result


def load_s5b1_assignment_source(
    *,
    stage3b1_dir: Path,
    assignment_source: str,
    assignment_path: str | Path | None,
    assignment_key: str | None,
    record_count: int,
) -> tuple[np.ndarray, dict[str, object]]:
    source_name = str(assignment_source)
    if assignment_path is None:
        path = stage3b1_dir / "learned_assignments.npy"
    else:
        path = Path(assignment_path)
    if not path.exists():
        raise FileNotFoundError(f"missing S5B1 assignment source: {path}")
    if path.suffix == ".npz":
        with np.load(path) as data:
            key = str(assignment_key or (data.files[0] if data.files else ""))
            if key not in data.files:
                raise KeyError(f"{path} does not contain assignment key {key!r}; available keys: {data.files}")
            matrix = np.asarray(data[key], dtype=np.float64)
    else:
        key = None
        matrix = np.asarray(np.load(path), dtype=np.float64)
    if matrix.ndim != 2:
        raise ValueError("S5B1 assignment source must be a 2D responsibility matrix")
    if int(matrix.shape[0]) != int(record_count):
        raise ValueError(f"S5B1 assignment row count {matrix.shape[0]} does not match Stage 3A rows {record_count}")
    row_sums = np.sum(matrix, axis=1) if matrix.size else np.ones(int(record_count), dtype=np.float64)
    if matrix.size and not np.allclose(row_sums, 1.0):
        matrix = matrix / np.maximum(row_sums[:, None], 1.0e-12)
    audit = {
        "schema": "scope_static_stage5b1_assignment_source_audit_v1",
        "assignment_source": source_name,
        "assignment_path": str(path),
        "assignment_key": key,
        "row_count": int(matrix.shape[0]),
        "prototype_count": int(matrix.shape[1]),
        "row_stochastic": bool(matrix.size == 0 or np.allclose(np.sum(matrix, axis=1), 1.0)),
        "uses_mechanism_labels": False,
        "uses_oracle_location_or_strength": False,
        "passed": True,
    }
    return matrix, audit


def fit_linear_proto_property_head(
    x: np.ndarray,
    responsibilities: np.ndarray,
    *,
    feature_names: list[str],
    context_groups: np.ndarray,
) -> dict[str, object]:
    matrix = np.asarray(x, dtype=np.float64)
    resp = np.asarray(responsibilities, dtype=np.float64)
    residual = _context_residual_matrix(matrix, context_groups)
    energy = np.mean(residual * residual, axis=1) if residual.size else np.zeros(int(matrix.shape[0]), dtype=np.float64)
    magnitude = np.mean(np.abs(residual), axis=1) if residual.size else np.zeros(int(matrix.shape[0]), dtype=np.float64)
    masses = np.sum(resp, axis=0) if resp.size else np.zeros(0, dtype=np.float64)
    prototypes = []
    for idx in range(int(resp.shape[1]) if resp.ndim == 2 else 0):
        weights = resp[:, idx]
        mass = float(np.sum(weights))
        if mass <= 1.0e-12:
            mean = np.zeros(int(matrix.shape[1]), dtype=np.float64)
            proto_energy = 0.0
            proto_magnitude = 0.0
        else:
            mean = (weights[:, None] * residual).sum(axis=0) / mass
            proto_energy = float(np.sum(weights * energy) / mass)
            proto_magnitude = float(np.sum(weights * magnitude) / mass)
        prototypes.append(
            {
                "prototype": f"C{idx:03d}",
                "assignment_mass": mass,
                "context_residual_energy": proto_energy,
                "context_normalized_strength": proto_magnitude,
                "top_residual_features": _top_abs_features(mean, feature_names),
            }
        )
    return {
        "schema": "scope_static_stage5b1_property_recovery_metrics_v1",
        "model_name": "linear_proto_visible_residual_energy",
        "description": "Visible-only property head: fixed assignments summarize context-residual visible energy and magnitude per prototype.",
        "uses_mechanism_labels_for_fit": False,
        "uses_family_labels_for_fit": False,
        "uses_oracle_location_or_strength_for_fit": False,
        "row_count": int(matrix.shape[0]),
        "feature_count": int(matrix.shape[1]) if matrix.ndim == 2 else 0,
        "prototype_count": int(len(prototypes)),
        "context_group_count": int(len(set(np.asarray(context_groups, dtype=np.int64).tolist()))) if len(context_groups) else 0,
        "mean_row_residual_energy": float(np.mean(energy)) if energy.size else 0.0,
        "mean_row_context_normalized_strength": float(np.mean(magnitude)) if magnitude.size else 0.0,
        "prototypes": prototypes,
        "passed": bool(resp.ndim == 2 and int(resp.shape[0]) == int(matrix.shape[0])),
    }


def fit_conditional_visible_context_property_head(
    x: np.ndarray,
    responsibilities: np.ndarray,
    *,
    feature_names: list[str],
    context_groups: np.ndarray,
) -> dict[str, object]:
    matrix = np.asarray(x, dtype=np.float64)
    resp = np.asarray(responsibilities, dtype=np.float64)
    baseline = _context_baseline_matrix(matrix, context_groups)
    residual = matrix - baseline
    row_energy = np.mean(residual * residual, axis=1) if residual.size else np.zeros(int(matrix.shape[0]), dtype=np.float64)
    row_magnitude = np.mean(np.abs(residual), axis=1) if residual.size else np.zeros(int(matrix.shape[0]), dtype=np.float64)
    groups = np.asarray(context_groups, dtype=np.int64)
    context_values = sorted(set(groups.tolist())) if groups.size else []
    prototypes = []
    for idx in range(int(resp.shape[1]) if resp.ndim == 2 else 0):
        weights = resp[:, idx]
        mass = float(np.sum(weights))
        if mass <= 1.0e-12:
            proto_residual = np.zeros(int(matrix.shape[1]), dtype=np.float64)
            proto_energy = 0.0
            proto_strength = 0.0
            context_rows = []
        else:
            proto_residual = (weights[:, None] * residual).sum(axis=0) / mass
            proto_energy = float(np.sum(weights * row_energy) / mass)
            proto_strength = float(np.sum(weights * row_magnitude) / mass)
            context_rows = []
            for group in context_values:
                mask = groups == int(group)
                local_mass = float(np.sum(weights[mask]))
                context_rows.append(
                    {
                        "context_group": int(group),
                        "assignment_mass": local_mass,
                        "strength_score": 0.0 if local_mass <= 1.0e-12 else float(np.sum(weights[mask] * row_magnitude[mask]) / local_mass),
                        "residual_energy_score": 0.0 if local_mass <= 1.0e-12 else float(np.sum(weights[mask] * row_energy[mask]) / local_mass),
                    }
                )
        prototypes.append(
            {
                "prototype": f"C{idx:03d}",
                "assignment_mass": mass,
                "context_conditioned_residual_energy_score": proto_energy,
                "context_normalized_strength_score": proto_strength,
                "location_score_proxy": {
                    "semantic_role": "visible_residual_energy_profile",
                    "top_residual_features": _top_abs_features(proto_residual, feature_names),
                    "uses_oracle_location_for_fit": False,
                },
                "context_scores": context_rows,
            }
        )
    return {
        "schema": "scope_static_stage5b1b_conditional_property_recovery_metrics_v1",
        "model_name": PROPERTY_HEAD_CONDITIONAL_VISIBLE_CONTEXT,
        "description": (
            "Visible-only conditional property head: fit b(context) from public context groups, then summarize "
            "fixed-assignment residual energy as a location proxy and context-normalized magnitude as strength."
        ),
        "structural_model": "visible = public_context_baseline + mechanism_residual + visible_location_proxy + strength_scale_proxy",
        "uses_mechanism_labels_for_fit": False,
        "uses_family_labels_for_fit": False,
        "uses_oracle_location_or_strength_for_fit": False,
        "uses_evaluator_records_for_fit": False,
        "evaluator_records_loaded_after_fit_for_scoring": True,
        "row_count": int(matrix.shape[0]),
        "feature_count": int(matrix.shape[1]) if matrix.ndim == 2 else 0,
        "prototype_count": int(len(prototypes)),
        "context_group_count": int(len(context_values)),
        "mean_row_residual_energy": float(np.mean(row_energy)) if row_energy.size else 0.0,
        "mean_row_context_normalized_strength": float(np.mean(row_magnitude)) if row_magnitude.size else 0.0,
        "prototypes": prototypes,
        "passed": bool(resp.ndim == 2 and int(resp.shape[0]) == int(matrix.shape[0])),
    }


def context_relative_location_recovery_audit(s5: dict[str, object]) -> dict[str, object]:
    rows = _target_payloads(s5)
    failed = [
        str(row.get("label", ""))
        for row in rows
        if not bool(dict(dict(row.get("recovery_metrics", {})).get("location_errors", {})).get("top_relative_location_cell_match", False))
    ]
    return {
        "schema": "scope_static_stage5b1_context_relative_location_recovery_audit_v1",
        "location_reference_frame": str(s5.get("location_reference_frame", "context_relative")),
        "evaluator_only": True,
        "used_for_training": False,
        "used_for_model_selection": False,
        "target_count": int(len(rows)),
        "failed_labels": failed,
        "passed": not failed,
    }


def context_normalized_strength_recovery_audit(s5: dict[str, object]) -> dict[str, object]:
    rows = _target_payloads(s5)
    failed = [
        str(row.get("label", ""))
        for row in rows
        if not bool(dict(dict(row.get("recovery_metrics", {})).get("strength_errors", {})).get("top_context_relative_strength_block_match", False))
    ]
    return {
        "schema": "scope_static_stage5b1_context_normalized_strength_recovery_audit_v1",
        "strength_reference_frame": "context_relative",
        "evaluator_only": True,
        "used_for_training": False,
        "used_for_model_selection": False,
        "target_count": int(len(rows)),
        "failed_labels": failed,
        "passed": not failed,
    }


def targeted_property_recovery_audit(s5: dict[str, object], *, targets: tuple[str, ...]) -> dict[str, object]:
    per_exact = dict(s5.get("per_exact_mechanism", {})) if isinstance(s5.get("per_exact_mechanism", {}), dict) else {}
    rows = {}
    for target in targets:
        payload = dict(per_exact.get(target, {})) if isinstance(per_exact.get(target, {}), dict) else {}
        metrics = dict(payload.get("recovery_metrics", {})) if isinstance(payload.get("recovery_metrics", {}), dict) else {}
        rows[target] = {
            "mechanism_id": str(target),
            "present": bool(payload),
            "support_count": int(payload.get("support_count", 0) or 0),
            "passed": bool(metrics.get("passed", False)) if payload else False,
            "max_abs_scalar_error": float(metrics.get("max_abs_scalar_error", 0.0) or 0.0),
        }
    return {
        "schema": "scope_static_stage5b1_targeted_m6_m13_m18_m27_property_audit_v1",
        "target_mechanism_ids": [str(target) for target in targets],
        "rows": rows,
        "present_target_count": int(sum(1 for row in rows.values() if bool(row.get("present", False)))),
        "passed": all((not bool(row.get("present", False))) or bool(row.get("passed", False)) for row in rows.values()),
    }


def stage5b1_contract_breakdown_audit(
    *,
    family: dict[str, object],
    s5: dict[str, object],
    location: dict[str, object],
    strength: dict[str, object],
    targeted: dict[str, object],
) -> dict[str, object]:
    contract = dict(s5.get("contract_typed_recovery_metrics", {})) if isinstance(s5.get("contract_typed_recovery_metrics", {}), dict) else {}
    dimension = dict(s5.get("mechanism_dimension_recovery_audit", {})) if isinstance(s5.get("mechanism_dimension_recovery_audit", {}), dict) else {}
    effect = dict(s5.get("effect_recovery_metrics", {})) if isinstance(s5.get("effect_recovery_metrics", {}), dict) else {}
    family_failed = [str(value) for value in list(contract.get("family_failed_labels", []))]
    flat_failed = [str(value) for value in list(contract.get("atomic_flat_exact_failed_labels", []))]
    dimension_failed = [
        str(row.get("mechanism_id", row.get("legacy_catalog_id", "")))
        for row in list(dimension.get("targets", []))
        if isinstance(row, dict) and not bool(row.get("not_evaluable", False)) and not bool(row.get("passed", False))
    ]
    overlay_not_evaluable = [
        str(row.get("mechanism_id", row.get("legacy_catalog_id", "")))
        for row in list(dimension.get("targets", []))
        if isinstance(row, dict) and bool(row.get("not_evaluable", False))
    ]
    overlay_contract = dict(s5.get("overlay_contract_audit", {})) if isinstance(s5.get("overlay_contract_audit", {}), dict) else {}
    overlay_recovery = dict(s5.get("overlay_recovery_audit", {})) if isinstance(s5.get("overlay_recovery_audit", {}), dict) else {}
    location_passed = bool(location.get("passed", False))
    strength_passed = bool(strength.get("passed", False))
    dimension_passed = bool(dimension.get("recovery_passed_excluding_not_evaluable", dimension.get("passed", False)))
    overlay_contract_passed = bool(overlay_contract.get("passed", True))
    family_passed = bool(family.get("passed", False)) and not family_failed
    flat_exact_passed = not flat_failed
    targeted_passed = bool(targeted.get("passed", False))
    location_strength_passed = bool(location_passed and strength_passed)
    property_without_dimension_passed = bool(
        family_passed
        and flat_exact_passed
        and location_strength_passed
        and targeted_passed
        and bool(effect.get("passed", False))
    )
    contract_passed = bool(contract.get("passed", False))
    return {
        "schema": "scope_static_stage5b1_contract_breakdown_audit_v1",
        "description": (
            "Breaks S5B1 property recovery into separate location, strength, dimension, and contract gates so "
            "non-flat dimension calibration cannot obscure recovered location/strength diagnostics."
        ),
        "evaluator_only": True,
        "used_for_training": False,
        "used_for_model_selection": False,
        "flat_targets_use_exact_recovery": True,
        "non_flat_targets_use_family_dimension_recovery": True,
        "s5b1_family_passed": family_passed,
        "s5b1_location_passed": location_passed,
        "s5b1_strength_passed": strength_passed,
        "s5b1_location_strength_passed": location_strength_passed,
        "s5b1_flat_exact_passed": flat_exact_passed,
        "s5b1_dimension_passed": dimension_passed,
        "s5b1_overlay_contract_passed": overlay_contract_passed,
        "s5b1_overlay_recovery_evaluable_or_not_required": bool(overlay_recovery.get("passed", True)),
        "s5b1_targeted_m6_m13_m18_m27_passed": targeted_passed,
        "s5b1_property_without_dimension_passed": property_without_dimension_passed,
        "s5b1_contract_passed": contract_passed,
        "family_failed_labels": family_failed,
        "atomic_flat_exact_failed_labels": flat_failed,
        "dimension_failed_labels": sorted([label for label in dimension_failed if label]),
        "overlay_not_evaluable_labels": sorted([label for label in overlay_not_evaluable if label]),
        "overlay_contract_missing_labels": list(contract.get("overlay_contract_missing_target_ids", [])),
        "overlay_failure_kinds": list(contract.get("overlay_failure_kinds", [])),
        "location_failed_labels": list(location.get("failed_labels", [])),
        "strength_failed_labels": list(strength.get("failed_labels", [])),
        "targeted_rows": targeted.get("rows", {}),
        "passed": contract_passed,
    }


def stage5b1_acceptance_audit(
    *,
    s3a_metrics: dict[str, object],
    s3a5_metrics: dict[str, object],
    s3b1_metrics: dict[str, object],
    feature_match: dict[str, object],
    assignment_audit: dict[str, object],
    property_head: dict[str, object],
    family: dict[str, object],
    s5: dict[str, object],
    location: dict[str, object],
    strength: dict[str, object],
    targeted: dict[str, object],
    contract_breakdown: dict[str, object],
) -> dict[str, object]:
    checks = {
        "stage3a_acceptance_passed": bool(dict(s3a_metrics.get("acceptance_audit", {})).get("passed", False)),
        "stage3a5_acceptance_passed": bool(dict(s3a5_metrics.get("acceptance_audit", {})).get("passed", False)) if s3a5_metrics else True,
        "stage3b1_acceptance_passed": bool(dict(s3b1_metrics.get("acceptance_audit", {})).get("passed", False)) if s3b1_metrics else True,
        "feature_schema_matches_stage3a": bool(feature_match.get("passed", False)),
        "assignment_source_row_stochastic": bool(assignment_audit.get("row_stochastic", False)),
        "property_head_fit_uses_no_oracle_fields": not bool(property_head.get("uses_oracle_location_or_strength_for_fit", True)),
        "property_head_passed": bool(property_head.get("passed", False)),
        "soft_family_classification_reported": bool(family.get("passed", False)),
        "s5b1_contract_breakdown_reported": bool(contract_breakdown),
        "s5b1_location_passed": bool(contract_breakdown.get("s5b1_location_passed", False)),
        "s5b1_strength_passed": bool(contract_breakdown.get("s5b1_strength_passed", False)),
        "s5b1_dimension_passed": bool(contract_breakdown.get("s5b1_dimension_passed", False)),
        "s5b1_overlay_contract_passed": bool(contract_breakdown.get("s5b1_overlay_contract_passed", False)),
        "s5b1_contract_passed": bool(contract_breakdown.get("s5b1_contract_passed", False)),
        "contract_typed_property_recovery_passed": bool(contract_breakdown.get("s5b1_contract_passed", False)),
        "context_relative_location_recovery_passed": bool(location.get("passed", False)),
        "context_normalized_strength_recovery_passed": bool(strength.get("passed", False)),
        "targeted_m6_m13_m18_m27_reported": bool(targeted.get("passed", False)),
        "location_strength_reported_separately_from_dimension": True,
        "does_not_claim_physical_parameter_recovery": not bool(s5.get("claims_physical_parameter_recovery", True)),
    }
    return {
        "schema": "scope_static_stage5b1_acceptance_audit_v1",
        "passed": bool(all(checks.values())),
        "checks": checks,
    }


def _context_residual_matrix(matrix: np.ndarray, context_groups: np.ndarray) -> np.ndarray:
    arr = np.asarray(matrix, dtype=np.float64)
    groups = np.asarray(context_groups, dtype=np.int64)
    if arr.ndim != 2 or int(groups.shape[0]) != int(arr.shape[0]):
        return arr - np.mean(arr, axis=0, keepdims=True)
    out = np.zeros_like(arr, dtype=np.float64)
    for group in sorted(set(groups.tolist())):
        mask = groups == int(group)
        out[mask] = arr[mask] - np.mean(arr[mask], axis=0, keepdims=True)
    return out


def _context_baseline_matrix(matrix: np.ndarray, context_groups: np.ndarray) -> np.ndarray:
    arr = np.asarray(matrix, dtype=np.float64)
    groups = np.asarray(context_groups, dtype=np.int64)
    if arr.ndim != 2 or int(groups.shape[0]) != int(arr.shape[0]):
        return np.tile(np.mean(arr, axis=0, keepdims=True), (int(arr.shape[0]), 1))
    out = np.zeros_like(arr, dtype=np.float64)
    for group in sorted(set(groups.tolist())):
        mask = groups == int(group)
        out[mask] = np.mean(arr[mask], axis=0, keepdims=True)
    return out


def _normalize_property_head_model(value: str) -> str:
    model = str(value or DEFAULT_PROPERTY_HEAD_MODEL)
    if model not in ALLOWED_PROPERTY_HEAD_MODELS:
        raise ValueError(f"property_head_model must be one of {ALLOWED_PROPERTY_HEAD_MODELS!r}")
    return model


def _top_abs_features(values: np.ndarray, feature_names: list[str], *, limit: int = 8) -> list[dict[str, object]]:
    rows = sorted(
        (
            (abs(float(value)), float(value), str(feature_names[idx]) if idx < len(feature_names) else f"feature_{idx}")
            for idx, value in enumerate(np.asarray(values, dtype=np.float64).tolist())
        ),
        key=lambda item: (-item[0], item[2]),
    )
    return [{"feature": name, "value": signed, "abs_value": magnitude} for magnitude, signed, name in rows[: max(0, int(limit))]]


def _target_payloads(s5: dict[str, object]) -> list[dict[str, object]]:
    per_family = dict(s5.get("per_family", {})) if isinstance(s5.get("per_family", {}), dict) else {}
    per_exact = dict(s5.get("per_exact_mechanism", {})) if isinstance(s5.get("per_exact_mechanism", {}), dict) else {}
    dimension = dict(s5.get("mechanism_dimension_recovery_audit", {})) if isinstance(s5.get("mechanism_dimension_recovery_audit", {}), dict) else {}
    not_evaluable = {str(label) for label in list(dimension.get("not_evaluable_target_ids", []))}
    rows = [dict(row) for row in per_family.values() if isinstance(row, dict)]
    rows.extend(
        dict(row)
        for label, row in per_exact.items()
        if isinstance(row, dict) and str(label) not in not_evaluable
    )
    return rows


def _write_outputs(output: Path, result: dict[str, object]) -> None:
    artifacts = {
        "metrics.json": result,
        "s5b1_property_recovery_metrics.json": result["s5b1_property_recovery_metrics"],
        "assignment_source_audit.json": result["assignment_source_audit"],
        "soft_family_classification_metrics.json": result["soft_family_classification_metrics"],
        "s5_context_relative_mechanism_effect_audit.json": result["s5_context_relative_mechanism_effect_audit"],
        "mechanism_dimension_recovery_audit.json": result["mechanism_dimension_recovery_audit"],
        "overlay_contract_audit.json": result["overlay_contract_audit"],
        "overlay_recovery_audit.json": result["overlay_recovery_audit"],
        "context_relative_location_recovery_audit.json": result["context_relative_location_recovery_audit"],
        "context_normalized_strength_recovery_audit.json": result["context_normalized_strength_recovery_audit"],
        "targeted_m6_m13_m18_m27_property_audit.json": result["targeted_m6_m13_m18_m27_property_audit"],
        "s5b1_contract_breakdown_audit.json": result["s5b1_contract_breakdown_audit"],
        "acceptance_audit.json": result["acceptance_audit"],
        "feature_schema_match_audit.json": result["feature_schema_match_audit"],
        "visible_feature_matrix.json": result["visible_feature_matrix"],
    }
    for name, payload in artifacts.items():
        (output / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    (output / "config.yaml").write_text(yaml.safe_dump({"stage5b1_property_recovery": result["config"]}, sort_keys=False))
    (output / "summary.md").write_text(format_stage5b1_summary(result))


def format_stage5b1_summary(result: dict[str, object]) -> str:
    acceptance = dict(result.get("acceptance_audit", {}))
    property_head = dict(result.get("s5b1_property_recovery_metrics", {}))
    s5 = dict(result.get("s5_context_relative_mechanism_effect_audit", {}))
    breakdown = dict(result.get("s5b1_contract_breakdown_audit", {}))
    return "\n".join(
        [
            "# Stage 5B1: Property Recovery",
            "",
            f"- Decision: `{result.get('decision')}`",
            f"- Acceptance passed: `{str(bool(acceptance.get('passed', False))).lower()}`",
            f"- Property head: `{property_head.get('model_name')}`",
            f"- Prototype count: `{property_head.get('prototype_count')}`",
            f"- Location / strength / dimension passed: `{str(bool(breakdown.get('s5b1_location_passed', False))).lower()}` / `{str(bool(breakdown.get('s5b1_strength_passed', False))).lower()}` / `{str(bool(breakdown.get('s5b1_dimension_passed', False))).lower()}`",
            f"- Contract-typed recovery passed: `{str(bool(dict(s5.get('contract_typed_recovery_metrics', {})).get('passed', False))).lower()}`",
            "",
            "## Claim Boundary",
            "",
            "S5B1 uses fixed visible assignments and frozen Stage 3A visible features to audit context-relative location and context-normalized strength. Evaluator records are loaded only after the property head is fixed, and physical parameter recovery is not claimed.",
            "",
        ]
    )
