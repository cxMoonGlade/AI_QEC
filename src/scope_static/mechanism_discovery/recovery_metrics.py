from __future__ import annotations

import numpy as np

from scope_static.dem.metrics import adjusted_rand_index, normalized_mutual_info
from scope_static.primitives.channels import M13_DEFAULT_DRIFT_VISIBILITY_SCALE
from scope_static.primitives.channels import M13_DEFAULT_EPSILON_SPAN
from scope_static.primitives.mechanism_catalog import CONTRACT_TYPED_DIMENSION_TARGET_IDS
from scope_static.primitives.mechanism_catalog import CURRENT_VISIBLE_SURFACE_FLAT_EXACT_CLAIM_TARGET_IDS
from scope_static.primitives.mechanism_catalog import NON_FLAT_PRIMARY_TARGET_IDS
from scope_static.primitives.mechanism_catalog import NON_FLAT_PUBLIC_LABELS
from scope_static.primitives.mechanism_catalog import PRIMARY_FLAT_CLUSTER_TARGET_IDS
from scope_static.primitives.mechanism_catalog import PRIMARY_FLAT_PUBLIC_LABELS
from scope_static.primitives.mechanism_catalog import SURFACE_CONDITIONAL_DIMENSION_TARGET_IDS
from scope_static.primitives.mechanism_catalog import mechanism_contract
from scope_static.primitives.mechanism_catalog import mechanism_taxonomy_contract_audit
from scope_static.primitives.overlay_contract import OVERLAY_CONTRACT_MISSING_REASON
from scope_static.primitives.overlay_contract import overlay_contract_audit
from .assignment_matrix import normalize_rows as _normalize_rows
from .assignment_matrix import normalize_rows_with_zeros as _normalize_rows_with_zeros
from .contract_claims import is_one as _is_one
from .discovery_model import EVALUATOR_MODE_NO_ORACLE_LABELS
from .discovery_model import _normalize_evaluator_mode
from .feature_blocks import feature_block_indices as _feature_block_indices
from .mechanism_families import FAMILY_BUCKETS, mechanism_family_bucket

def evaluate_soft_family_classification(
    responsibilities: np.ndarray,
    records: list[dict[str, object]],
    *,
    evaluator_mode: str,
) -> dict[str, object]:
    projection = _soft_family_projection(responsibilities, records)
    resp = projection["responsibilities"]
    family_names = projection["family_names"]
    true_labels = projection["true_family_labels"]
    row_family_prob = projection["row_family_probabilities"]
    cluster_family_mass = projection["cluster_family_mass"]
    cluster_family_prob = projection["cluster_family_probabilities"]
    predicted_ids = np.argmax(row_family_prob, axis=1).astype(np.int64)
    predicted_labels = [family_names[int(idx)] for idx in predicted_ids.tolist()]
    metrics = _classification_metrics(true_labels, predicted_labels, class_names=family_names)
    cluster_decoder = []
    for cluster_idx, row in enumerate(cluster_family_prob.tolist()):
        top_idx = int(np.argmax(row)) if row else 0
        cluster_decoder.append(
            {
                "cluster": f"C{int(cluster_idx):03d}",
                "dominant_family": family_names[top_idx],
                "family_probabilities": {family_names[idx]: float(value) for idx, value in enumerate(row)},
                "family_mass": {family_names[idx]: float(value) for idx, value in enumerate(cluster_family_mass[cluster_idx].tolist())},
            }
        )
    passed = (
        _is_one(metrics["normalized_mutual_info"])
        and _is_one(metrics["adjusted_rand_index"])
        and _is_one(metrics["balanced_accuracy"])
        and _is_one(metrics["min_recall"])
    )
    return {
        "schema": "scope_static_stage3c_soft_family_classification_metrics_v1",
        "description": "Evaluator-only soft family decoder from Stage 3B.1 responsibilities; not used for learner fit or model selection.",
        "evaluator_mode": _normalize_evaluator_mode(evaluator_mode),
        "evaluator_only": True,
        "skipped": False,
        "used_for_training": False,
        "used_for_model_selection": False,
        "uses_evaluator_labels_to_name_family_decoder": True,
        "uses_channels_ptms_kraus": False,
        "row_count": int(resp.shape[0]),
        "prototype_count": int(resp.shape[1]),
        "family_names": family_names,
        "family_count": int(len(family_names)),
        "soft_probability_matrix_shape": [int(resp.shape[0]), int(len(family_names))],
        "cluster_family_decoder": cluster_decoder,
        "confusion_matrix": metrics["confusion_matrix"],
        "support": metrics["support"],
        "per_family_recall": metrics["per_family_recall"],
        "balanced_accuracy": metrics["balanced_accuracy"],
        "min_recall": metrics["min_recall"],
        "adjusted_rand_index": metrics["adjusted_rand_index"],
        "normalized_mutual_info": metrics["normalized_mutual_info"],
        "passed": bool(passed),
    }


def skipped_soft_family_classification() -> dict[str, object]:
    return {
        "schema": "scope_static_stage3c_soft_family_classification_metrics_v1",
        "description": "Skipped because controlled-catalog evaluator family labels are unavailable.",
        "evaluator_mode": EVALUATOR_MODE_NO_ORACLE_LABELS,
        "evaluator_only": False,
        "skipped": True,
        "used_for_training": False,
        "used_for_model_selection": False,
        "uses_evaluator_labels_to_name_family_decoder": False,
        "uses_channels_ptms_kraus": False,
        "passed": True,
        "normalized_mutual_info": None,
        "adjusted_rand_index": None,
        "balanced_accuracy": None,
        "min_recall": None,
    }


def evaluate_soft_family_strength_location_audit(
    x: np.ndarray,
    responsibilities: np.ndarray,
    records: list[dict[str, object]],
    *,
    feature_names: list[str],
    evaluator_mode: str,
) -> dict[str, object]:
    matrix = np.asarray(x, dtype=np.float64)
    if matrix.ndim != 2:
        raise ValueError("visible feature matrix must be 2D")
    if int(matrix.shape[0]) != len(records):
        raise ValueError(f"visible feature row count {matrix.shape[0]} does not match evaluator record count {len(records)}")
    projection = _soft_family_projection(responsibilities, records)
    row_family_prob = projection["row_family_probabilities"]
    family_names = projection["family_names"]
    true_family_labels = projection["true_family_labels"]
    if int(row_family_prob.shape[0]) != int(matrix.shape[0]):
        raise ValueError("soft family probability row count must match visible feature rows")

    relative_records = _records_with_context_relative_location(records)
    overlay_contract = overlay_contract_audit(relative_records, fail_on_missing_overlay_payload=True)
    exact_labels = [str(record.get("oracle_label", record.get("mechanism_id", ""))) for record in records]
    per_family = {}
    for family_idx, family in enumerate(family_names):
        weights = np.asarray(row_family_prob[:, family_idx], dtype=np.float64)
        oracle_weights = np.asarray([1.0 if label == family else 0.0 for label in true_family_labels], dtype=np.float64)
        per_family[family] = _effect_recovery_payload(
            matrix,
            predicted_weights=weights,
            oracle_weights=oracle_weights,
            records=relative_records,
            feature_names=feature_names,
            label=str(family),
        )

    exact_projection = _soft_exact_projection(responsibilities, records, exact_labels=exact_labels)
    row_exact_prob = exact_projection["row_exact_probabilities"]
    exact_names = exact_projection["exact_names"]
    per_exact = {}
    for label_idx, label in enumerate(exact_names):
        weights = np.asarray(row_exact_prob[:, label_idx], dtype=np.float64)
        oracle_weights = np.asarray([1.0 if value == label else 0.0 for value in exact_labels], dtype=np.float64)
        per_exact[label] = _effect_recovery_payload(
            matrix,
            predicted_weights=weights,
            oracle_weights=oracle_weights,
            records=relative_records,
            feature_names=feature_names,
            label=str(label),
        )
    recovery_summary = _effect_recovery_summary(per_family=per_family, per_exact=per_exact)
    spectator_overlay = _spectator_overlay_audit(matrix, relative_records, feature_names=feature_names)
    overlay_recovery = _overlay_recovery_audit(spectator_overlay, overlay_contract)
    dimension_audit = _mechanism_dimension_recovery_audit(
        matrix,
        records=relative_records,
        feature_names=feature_names,
        exact_labels=exact_labels,
        exact_names=exact_names,
        row_exact_prob=row_exact_prob,
        per_exact=per_exact,
        overlay_contract_audit=overlay_contract,
    )
    contract_typed = _contract_typed_recovery_summary(
        per_family=per_family,
        per_exact=per_exact,
        dimension_audit=dimension_audit,
        spectator_overlay=spectator_overlay,
        overlay_contract_audit=overlay_contract,
        overlay_recovery_audit=overlay_recovery,
    )

    return {
        "schema": "scope_static_s5_context_relative_mechanism_effect_audit_v1",
        "compatibility_aliases": ["scope_static_stage3c_soft_family_strength_location_audit_v1"],
        "stage": "S5_context_relative_mechanism_effect_recovery",
        "description": (
            "Evaluator-only audit for recovered mechanism families and exact catalog mechanisms. "
            "S5 location means context-conditioned likelihood/support over context-relative cells, "
            "not absolute physical-coordinate recovery."
        ),
        "evaluator_mode": _normalize_evaluator_mode(evaluator_mode),
        "evaluator_only": True,
        "skipped": False,
        "used_for_training": False,
        "used_for_model_selection": False,
        "uses_stage3b1_responsibilities": True,
        "uses_evaluator_labels_to_name_families": True,
        "uses_oracle_records_for_location_and_parameter_audit": True,
        "uses_channels_ptms_kraus": False,
        "claims_physical_parameter_recovery": False,
        "location_reference_frame": "context_relative",
        "location_semantics": "context_conditioned_error_likelihood",
        "context_likelihood_definition": (
            "For a recovered family/mechanism, location is the weighted likelihood/support that its "
            "visible effect appears in a context-relative cell conditioned on the public/probe context."
        ),
        "absolute_location_ids_are_provenance_only": True,
        "visible_strength_definition": "Primary strength is the weighted shift of frozen learner-visible surface features after subtracting context-local visible means; global-reference strength is reported only as a comparison.",
        "oracle_parameter_strength_definition": "Evaluator-only numeric summary of teacher record parameters; diagnostic only.",
        "row_count": int(matrix.shape[0]),
        "feature_count": int(matrix.shape[1]),
        "family_count": int(len(family_names)),
        "exact_mechanism_count": int(len(set(exact_labels))),
        "effect_recovery_metrics": recovery_summary,
        "contract_typed_recovery_metrics": contract_typed,
        "mechanism_taxonomy_contract_audit": mechanism_taxonomy_contract_audit(),
        "mechanism_dimension_recovery_audit": dimension_audit,
        "overlay_contract_audit": overlay_contract,
        "spectator_overlay_audit": spectator_overlay,
        "overlay_recovery_audit": overlay_recovery,
        "per_family": per_family,
        "per_exact_mechanism": per_exact,
        "passed": bool(contract_typed["passed"]),
    }


def skipped_soft_family_strength_location_audit() -> dict[str, object]:
    return {
        "schema": "scope_static_s5_context_relative_mechanism_effect_audit_v1",
        "compatibility_aliases": ["scope_static_stage3c_soft_family_strength_location_audit_v1"],
        "stage": "S5_context_relative_mechanism_effect_recovery",
        "description": "Skipped because controlled-catalog evaluator records are unavailable.",
        "evaluator_mode": EVALUATOR_MODE_NO_ORACLE_LABELS,
        "evaluator_only": False,
        "skipped": True,
        "used_for_training": False,
        "used_for_model_selection": False,
        "uses_stage3b1_responsibilities": False,
        "uses_evaluator_labels_to_name_families": False,
        "uses_oracle_records_for_location_and_parameter_audit": False,
        "uses_channels_ptms_kraus": False,
        "claims_physical_parameter_recovery": False,
        "location_reference_frame": "context_relative",
        "absolute_location_ids_are_provenance_only": True,
        "effect_recovery_metrics": {
            "schema": "scope_static_s5_effect_recovery_summary_v1",
            "family_count": 0,
            "exact_mechanism_count": 0,
            "max_abs_scalar_error": 0.0,
            "failed_labels": [],
            "passed": True,
        },
        "contract_typed_recovery_metrics": _skipped_contract_typed_recovery_summary("no_oracle_labels"),
        "mechanism_taxonomy_contract_audit": mechanism_taxonomy_contract_audit(),
        "mechanism_dimension_recovery_audit": _skipped_mechanism_dimension_recovery_audit("no_oracle_labels"),
        "overlay_contract_audit": _skipped_overlay_contract_audit("no_oracle_labels"),
        "spectator_overlay_audit": _skipped_spectator_overlay_audit("no_oracle_labels"),
        "overlay_recovery_audit": _skipped_overlay_recovery_audit("no_oracle_labels"),
        "passed": True,
        "per_family": {},
        "per_exact_mechanism": {},
    }


def _soft_family_projection(responsibilities: np.ndarray, records: list[dict[str, object]]) -> dict[str, object]:
    resp = _normalize_rows(responsibilities)
    if int(resp.shape[0]) != len(records):
        raise ValueError(f"assignment row count {resp.shape[0]} does not match evaluator record count {len(records)}")
    true_labels = [mechanism_family_bucket(record) for record in records]
    family_names = [name for name in FAMILY_BUCKETS if name in set(true_labels)]
    family_names.extend(sorted(set(true_labels) - set(family_names)))
    if not family_names:
        family_names = list(FAMILY_BUCKETS)
    family_to_idx = {name: idx for idx, name in enumerate(family_names)}
    true_ids = np.asarray([family_to_idx[label] for label in true_labels], dtype=np.int64)
    true_one_hot = np.zeros((len(true_labels), len(family_names)), dtype=np.float64)
    for row, idx in enumerate(true_ids.tolist()):
        true_one_hot[int(row), int(idx)] = 1.0
    cluster_family_mass = resp.T @ true_one_hot
    cluster_family_prob = _normalize_rows_with_zeros(cluster_family_mass)
    row_family_prob = resp @ cluster_family_prob
    return {
        "responsibilities": resp,
        "family_names": family_names,
        "true_family_labels": true_labels,
        "cluster_family_mass": cluster_family_mass,
        "cluster_family_probabilities": cluster_family_prob,
        "row_family_probabilities": row_family_prob,
    }


def _soft_exact_projection(responsibilities: np.ndarray, records: list[dict[str, object]], *, exact_labels: list[str]) -> dict[str, object]:
    resp = _normalize_rows(responsibilities)
    if int(resp.shape[0]) != len(records) or len(exact_labels) != len(records):
        raise ValueError("assignment, record, and exact-label row counts must match")
    exact_names = sorted(set(exact_labels), key=_mechanism_sort_key)
    label_to_idx = {name: idx for idx, name in enumerate(exact_names)}
    true_one_hot = np.zeros((len(exact_labels), len(exact_names)), dtype=np.float64)
    for row, label in enumerate(exact_labels):
        true_one_hot[int(row), int(label_to_idx[label])] = 1.0
    cluster_exact_mass = resp.T @ true_one_hot
    cluster_exact_prob = _normalize_rows_with_zeros(cluster_exact_mass)
    row_exact_prob = resp @ cluster_exact_prob
    return {
        "responsibilities": resp,
        "exact_names": exact_names,
        "cluster_exact_mass": cluster_exact_mass,
        "cluster_exact_probabilities": cluster_exact_prob,
        "row_exact_probabilities": row_exact_prob,
    }


def _mechanism_dimension_recovery_audit(
    matrix: np.ndarray,
    *,
    records: list[dict[str, object]],
    feature_names: list[str],
    exact_labels: list[str],
    exact_names: list[str],
    row_exact_prob: np.ndarray,
    per_exact: dict[str, object],
    overlay_contract_audit: dict[str, object],
) -> dict[str, object]:
    dimension_targets = set(CONTRACT_TYPED_DIMENSION_TARGET_IDS)
    present_dimension_targets = [label for label in exact_names if label in dimension_targets]
    overlay_contract_missing_labels = set(_overlay_contract_missing_labels(overlay_contract_audit))
    rows = []
    for label in present_dimension_targets:
        contract = mechanism_contract(label)
        indices = [idx for idx, value in enumerate(exact_labels) if value == label]
        label_idx = exact_names.index(label)
        weights = np.asarray(row_exact_prob[:, label_idx], dtype=np.float64)
        local_records = [records[idx] for idx in indices]
        dimensions = _mechanism_dimension_payload(label, contract=contract, records=local_records)
        visible = _weighted_visible_strength(matrix, weights, feature_names=feature_names, records=records)
        effect_metrics = (
            dict(dict(per_exact.get(label, {})).get("recovery_metrics", {}))
            if isinstance(per_exact.get(label, {}), dict)
            else {}
        )
        checks = {
            "contract_is_dimension_recovery_target": str(label) in dimension_targets,
            "dimension_fields_declared": bool(contract.get("dimensions", [])),
            "dimension_values_available": bool(dimensions.get("all_declared_dimensions_have_values", False)),
            "location_dimension_available": bool(dimensions.get("location_dimension_available", False)),
            "strength_dimension_available": bool(dimensions.get("strength_dimension_available", False)),
            "does_not_claim_flat_exact_recovery": True,
        }
        not_evaluable = bool(str(contract.get("contract_role", "")) == "overlay_family" and label in overlay_contract_missing_labels)
        recovery_passed = bool(all(checks.values()))
        rows.append(
            {
                "legacy_catalog_id": str(label),
                "mechanism_id": str(label),
                "public_label": str(contract.get("public_label", label)),
                "label_namespace": str(contract.get("label_namespace", "legacy")),
                "support_count": int(len(indices)),
                "soft_assignment_mass": float(np.sum(weights)),
                "contract_role": str(contract.get("contract_role", "unknown")),
                "base_family": str(contract.get("base_family", "unknown")),
                "primary_flat_cluster_target": bool(contract.get("primary_flat_cluster_target", False)),
                "current_visible_surface_flat_exact_claim_allowed": bool(
                    contract.get("current_visible_surface_flat_exact_claim_allowed", True)
                ),
                "current_visible_surface_claim_target": str(
                    contract.get("current_visible_surface_claim_target", "flat_exact_recovery")
                ),
                "flat_exact_claim_blocker": contract.get("flat_exact_claim_blocker"),
                "targeted_observability_group": list(contract.get("targeted_observability_group", [])),
                "leaf_exact_effect_supported": bool(contract.get("leaf_exact_effect_supported", False)),
                "declared_dimensions": list(contract.get("dimensions", [])),
                "dimension_values": dimensions,
                "visible_strength": visible,
                "effect_recovery_metrics_diagnostic_only": effect_metrics,
                "checks": checks,
                "dimension_recovery_evaluated": not not_evaluable,
                "not_evaluable": not_evaluable,
                "not_evaluable_reason": OVERLAY_CONTRACT_MISSING_REASON if not_evaluable else None,
                "failure_kind": OVERLAY_CONTRACT_MISSING_REASON if not_evaluable else None,
                "recoverable_failure": False if not_evaluable else not recovery_passed,
                "recovery_passed": None if not_evaluable else recovery_passed,
                "passed": True if not_evaluable else recovery_passed,
            }
        )
    evaluable_rows = [row for row in rows if not bool(row.get("not_evaluable", False))]
    not_evaluable_ids = [str(row.get("mechanism_id", "")) for row in rows if bool(row.get("not_evaluable", False))]
    recovery_passed_excluding_not_evaluable = all(bool(row.get("passed", False)) for row in evaluable_rows)
    taxonomy = mechanism_taxonomy_contract_audit()
    checks = {
        "taxonomy_contract_passed": bool(taxonomy.get("passed", False)),
        "evaluator_only": True,
        "not_used_for_training": True,
        "not_used_for_model_selection": True,
        "dimension_recovery_targets_include_surface_conditional_flat_targets": set(SURFACE_CONDITIONAL_DIMENSION_TARGET_IDS).issubset(
            set(CONTRACT_TYPED_DIMENSION_TARGET_IDS)
        ),
        "all_present_contract_dimension_targets_have_dimension_rows": len(rows) == len(present_dimension_targets),
        "present_contract_dimension_rows_pass_excluding_not_evaluable": bool(recovery_passed_excluding_not_evaluable),
        "overlay_contract_missing_targets_are_not_recovery_failures": all(
            not bool(row.get("recoverable_failure", True)) for row in rows if bool(row.get("not_evaluable", False))
        ),
    }
    return {
        "schema": "scope_static_s5_mechanism_dimension_recovery_audit_v1",
        "description": "Evaluator-only dimension audit for non-flat public M* targets and surface-conditional flat F* targets. Legacy M0-M34 IDs are provenance only.",
        "evaluator_only": True,
        "skipped": False,
        "used_for_training": False,
        "used_for_model_selection": False,
        "classification_target": "contract_typed_family_plus_dimension_recovery",
        "claims_physical_parameter_recovery": False,
        "row_count": int(len(records)),
        "feature_count": int(matrix.shape[1]) if matrix.ndim == 2 else 0,
        "non_flat_primary_target_ids_present": [label for label in exact_names if label in set(NON_FLAT_PRIMARY_TARGET_IDS)],
        "surface_conditional_dimension_target_ids_present": [
            label for label in exact_names if label in set(SURFACE_CONDITIONAL_DIMENSION_TARGET_IDS)
        ],
        "contract_typed_dimension_target_ids_present": present_dimension_targets,
        "primary_flat_cluster_target_ids_present": [label for label in exact_names if label in set(PRIMARY_FLAT_CLUSTER_TARGET_IDS)],
        "current_visible_surface_flat_exact_claim_target_ids_present": [
            label for label in exact_names if label in set(CURRENT_VISIBLE_SURFACE_FLAT_EXACT_CLAIM_TARGET_IDS)
        ],
        "non_flat_public_labels_present": [
            str(mechanism_contract(label).get("public_label", label))
            for label in exact_names
            if label in set(NON_FLAT_PRIMARY_TARGET_IDS)
        ],
        "surface_conditional_public_labels_present": [
            str(mechanism_contract(label).get("public_label", label))
            for label in exact_names
            if label in set(SURFACE_CONDITIONAL_DIMENSION_TARGET_IDS)
        ],
        "primary_flat_public_labels_present": [
            str(mechanism_contract(label).get("public_label", label))
            for label in exact_names
            if label in set(PRIMARY_FLAT_CLUSTER_TARGET_IDS)
        ],
        "not_evaluable_target_ids": sorted([label for label in not_evaluable_ids if label]),
        "overlay_contract_missing_target_ids": sorted([label for label in overlay_contract_missing_labels if label in set(present_dimension_targets)]),
        "recovery_passed_excluding_not_evaluable": bool(recovery_passed_excluding_not_evaluable),
        "overlay_contract_payload_complete": bool(overlay_contract_audit.get("passed", False)),
        "checks": checks,
        "targets": rows,
        "passed": bool(all(checks.values())),
    }


def _skipped_mechanism_dimension_recovery_audit(reason: str) -> dict[str, object]:
    return {
        "schema": "scope_static_s5_mechanism_dimension_recovery_audit_v1",
        "description": "Skipped because controlled-catalog evaluator labels are unavailable.",
        "evaluator_only": False,
        "skipped": True,
        "skip_reason": str(reason),
        "used_for_training": False,
        "used_for_model_selection": False,
        "classification_target": "contract_typed_family_plus_dimension_recovery",
        "claims_physical_parameter_recovery": False,
        "row_count": 0,
        "feature_count": 0,
        "non_flat_primary_target_ids_present": [],
        "primary_flat_cluster_target_ids_present": [],
        "non_flat_public_labels_present": [],
        "primary_flat_public_labels_present": [],
        "not_evaluable_target_ids": [],
        "overlay_contract_missing_target_ids": [],
        "recovery_passed_excluding_not_evaluable": True,
        "overlay_contract_payload_complete": True,
        "checks": {"skipped_without_oracle_labels": True},
        "targets": [],
        "passed": True,
    }


def _contract_typed_recovery_summary(
    *,
    per_family: dict[str, object],
    per_exact: dict[str, object],
    dimension_audit: dict[str, object],
    spectator_overlay: dict[str, object],
    overlay_contract_audit: dict[str, object],
    overlay_recovery_audit: dict[str, object],
) -> dict[str, object]:
    family_failed = _failed_effect_labels(per_family)
    primary_flat_failed = _failed_effect_labels(
        {label: payload for label, payload in per_exact.items() if label in set(CURRENT_VISIBLE_SURFACE_FLAT_EXACT_CLAIM_TARGET_IDS)}
    )
    overlay_contract_passed = bool(overlay_contract_audit.get("passed", False))
    overlay_recovery_passed = bool(overlay_recovery_audit.get("passed", False))
    dimension_passed = bool(dimension_audit.get("recovery_passed_excluding_not_evaluable", dimension_audit.get("passed", False)))
    checks = {
        "family_recovery_passed": not family_failed,
        "atomic_flat_exact_recovery_passed": not primary_flat_failed,
        "dimension_recovery_passed": dimension_passed,
        "overlay_contract_payload_available_or_no_overlay_records": overlay_contract_passed,
        "overlay_recovery_evaluable_or_not_required": overlay_recovery_passed,
        "non_flat_exact_labels_not_required_as_primary_flat_targets": True,
    }
    return {
        "schema": "scope_static_s5_contract_typed_recovery_summary_v1",
        "classification_target": "atomic_flat_exact_plus_family_plus_dimension_recovery",
        "description": "S5 acceptance summary: claimable flat IDs use exact recovery, non-flat and surface-conditional flat IDs use family/dimension recovery, and M11 uses overlay recovery when present.",
        "family_failed_labels": family_failed,
        "atomic_flat_exact_failed_labels": primary_flat_failed,
        "dimension_not_evaluable_target_ids": list(dimension_audit.get("not_evaluable_target_ids", [])),
        "overlay_contract_missing_target_ids": list(dimension_audit.get("overlay_contract_missing_target_ids", [])),
        "overlay_failure_kinds": list(overlay_contract_audit.get("failure_kinds", [])),
        "non_flat_primary_target_ids": list(NON_FLAT_PRIMARY_TARGET_IDS),
        "primary_flat_cluster_target_ids": list(PRIMARY_FLAT_CLUSTER_TARGET_IDS),
        "current_visible_surface_flat_exact_claim_target_ids": list(CURRENT_VISIBLE_SURFACE_FLAT_EXACT_CLAIM_TARGET_IDS),
        "surface_conditional_dimension_target_ids": list(SURFACE_CONDITIONAL_DIMENSION_TARGET_IDS),
        "contract_typed_dimension_target_ids": list(CONTRACT_TYPED_DIMENSION_TARGET_IDS),
        "non_flat_public_labels": list(NON_FLAT_PUBLIC_LABELS),
        "primary_flat_public_labels": list(PRIMARY_FLAT_PUBLIC_LABELS),
        "checks": checks,
        "passed": bool(all(checks.values())),
    }


def _skipped_contract_typed_recovery_summary(reason: str) -> dict[str, object]:
    return {
        "schema": "scope_static_s5_contract_typed_recovery_summary_v1",
        "classification_target": "atomic_flat_exact_plus_family_plus_dimension_recovery",
        "description": "Skipped because controlled-catalog evaluator labels are unavailable.",
        "skipped": True,
        "skip_reason": str(reason),
        "family_failed_labels": [],
        "atomic_flat_exact_failed_labels": [],
        "dimension_not_evaluable_target_ids": [],
        "overlay_contract_missing_target_ids": [],
        "overlay_failure_kinds": [],
        "non_flat_primary_target_ids": list(NON_FLAT_PRIMARY_TARGET_IDS),
        "primary_flat_cluster_target_ids": list(PRIMARY_FLAT_CLUSTER_TARGET_IDS),
        "current_visible_surface_flat_exact_claim_target_ids": list(CURRENT_VISIBLE_SURFACE_FLAT_EXACT_CLAIM_TARGET_IDS),
        "surface_conditional_dimension_target_ids": list(SURFACE_CONDITIONAL_DIMENSION_TARGET_IDS),
        "contract_typed_dimension_target_ids": list(CONTRACT_TYPED_DIMENSION_TARGET_IDS),
        "non_flat_public_labels": list(NON_FLAT_PUBLIC_LABELS),
        "primary_flat_public_labels": list(PRIMARY_FLAT_PUBLIC_LABELS),
        "checks": {"skipped_without_oracle_labels": True},
        "passed": True,
    }


def _failed_effect_labels(rows: dict[str, object]) -> list[str]:
    failed = []
    for label, payload in rows.items():
        if not isinstance(payload, dict):
            failed.append(str(label))
            continue
        metrics = payload.get("recovery_metrics", {})
        if not isinstance(metrics, dict) or not bool(metrics.get("passed", False)):
            failed.append(str(label))
    return sorted(failed)


def _mechanism_dimension_payload(label: str, *, contract: dict[str, object], records: list[dict[str, object]]) -> dict[str, object]:
    dimensions = [str(value) for value in list(contract.get("dimensions", []))]
    values: dict[str, object] = {}
    missing: list[str] = []
    for dimension in dimensions:
        extracted = [_mechanism_dimension_value(record, label=label, dimension=dimension, contract=contract) for record in records]
        available = [value for value in extracted if value is not None and str(value) != "unknown"]
        numeric = [_as_finite_float(value) for value in available]
        numeric = [value for value in numeric if value is not None]
        values[dimension] = {
            "available_count": int(len(available)),
            "missing_count": int(max(0, len(records) - len(available))),
            "value_counts": _value_counts(available),
            "numeric_summary": _numeric_summary(np.asarray(numeric, dtype=np.float64)),
            "non_degenerate": bool(len(set(str(value) for value in available)) > 1 or _numeric_values_non_degenerate(numeric)),
        }
        if not available:
            missing.append(dimension)
    strength_values = [_mechanism_strength_value(record, label=label) for record in records]
    strength_values = [value for value in strength_values if value is not None]
    generic_location_dimensions = {"context_relative_location", "context_relative_edge", "relative_location"}
    overlay_location_dimensions = {"victim_relative_location", "aggressor_relative_location"}
    declared_location_dimensions = set(dimensions) & (generic_location_dimensions | overlay_location_dimensions)
    location_dimension_available = (
        all(_mechanism_dimension_has_available_value(values, name) for name in declared_location_dimensions)
        if declared_location_dimensions
        else True
    )
    return {
        "contract_role": str(contract.get("contract_role", "unknown")),
        "base_family": str(contract.get("base_family", "unknown")),
        "declared_dimensions": dimensions,
        "per_dimension": values,
        "missing_dimensions": missing,
        "all_declared_dimensions_have_values": not missing,
        "context_relative_location_available": any(
            _mechanism_dimension_has_available_value(values, name)
            for name in generic_location_dimensions
        ),
        "declared_location_dimensions": sorted(declared_location_dimensions),
        "location_dimension_available": bool(location_dimension_available),
        "strength_dimension_available": bool(strength_values),
        "strength": _numeric_summary(np.asarray(strength_values, dtype=np.float64)),
    }


def _mechanism_dimension_has_available_value(values: dict[str, object], name: str) -> bool:
    row = values.get(name, {})
    return bool(isinstance(row, dict) and int(row.get("available_count", 0) or 0) > 0)


def _mechanism_dimension_value(record: dict[str, object], *, label: str, dimension: str, contract: dict[str, object]) -> object:
    if dimension in {"strength", "drift_strength", "custom_kraus_eta", "eta", "computational_subspace_survival"}:
        return _mechanism_strength_value(record, label=label)
    if dimension == "drift_mixture_span":
        direct = _record_nested_value(record, "drift_strength")
        if direct is not None:
            return direct
        direct = _record_nested_value(record, "effective_epsilon_span")
        if direct is not None:
            return direct
        params = _record_params(record)
        epsilon_span = _as_finite_float(params.get("epsilon_span"))
        scale = _as_finite_float(params.get("drift_visibility_scale"))
        if epsilon_span is None and label == "M13":
            epsilon_span = M13_DEFAULT_EPSILON_SPAN
        if scale is None and label == "M13":
            scale = M13_DEFAULT_DRIFT_VISIBILITY_SCALE
        if epsilon_span is not None:
            return float(abs(epsilon_span) * (scale if scale is not None else 1.0))
        return "unknown"
    if dimension in {"context_relative_location", "context_relative_edge", "relative_location"}:
        location = dict(record.get("_context_relative_location", {})) if isinstance(record.get("_context_relative_location", {}), dict) else {}
        return location.get("location_bucket_in_context", location.get("location_fraction_in_context", "unknown"))
    if dimension == "base_mechanism":
        return _spectator_overlay_base_mechanism(record)
    if dimension in {"victim_relative_location", "aggressor_relative_location", "coupling_axis", "timing_context"}:
        return _spectator_overlay_field(record, dimension, default="unknown")
    if dimension == "pauli_axis_mixture":
        params = _record_params(record)
        axes = [axis for axis in ("x", "y", "z") if _as_finite_float(params.get(f"p_{axis}")) not in {None, 0.0}]
        return "".join(axis.upper() for axis in axes) if axes else "XYZ_mixture"
    if dimension == "assignment_direction":
        if label == "M16":
            return "measurement_context_bias"
        return "direction_unspecified"
    if dimension.startswith("assignment_direction_"):
        return dimension.removeprefix("assignment_direction_")
    if dimension in {"symmetric_assignment", "15_pauli_support_mixture", "correlated_relaxation", "relaxation_down", "excitation_up"}:
        return dimension
    if dimension in {"xx_component", "yy_component"}:
        params = _record_params(record)
        key = "epsilon_x" if dimension == "xx_component" else "epsilon_y"
        return params.get(key, dimension)
    if dimension in {"operation_axis", "error_axis", "drift_index", "measurement_context", "prep_or_reset_axis"}:
        direct = _record_nested_value(record, dimension)
        if direct is not None:
            return direct
        if dimension == "drift_index":
            return record.get("circuit_id", record.get("location_id", "unknown"))
        if dimension == "measurement_context":
            return str(record.get("instruction", "unknown"))
        if dimension == "prep_or_reset_axis":
            return str(record.get("instruction", "unknown"))
    if dimension.startswith("axis_") or dimension.endswith("_axis") or dimension.endswith("_vector"):
        return dimension
    if dimension in {"mixed_ptm_residual", "coherent_asymmetry"}:
        return dimension
    if dimension == "surrogate_type":
        return str(contract.get("base_family", "surrogate"))
    direct = _record_nested_value(record, dimension)
    return "unknown" if direct is None else direct


def _record_nested_value(record: dict[str, object], key: str) -> object | None:
    if record.get(key) is not None:
        return record.get(key)
    drift = record.get("drift_overlay", {})
    if isinstance(drift, dict) and drift.get(key) is not None:
        return drift.get(key)
    overlay = record.get("spectator_overlay", {})
    if isinstance(overlay, dict) and overlay.get(key) is not None:
        return overlay.get(key)
    params = _record_params(record)
    if params.get(key) is not None:
        return params.get(key)
    return None


def _record_params(record: dict[str, object]) -> dict[str, object]:
    params = record.get("parameters", {})
    return dict(params) if isinstance(params, dict) else {}


def _mechanism_strength_value(record: dict[str, object], *, label: str) -> float | None:
    if _spectator_overlay_present(record):
        return _spectator_overlay_strength(record)
    params = _record_params(record)
    keys_by_label = {
        "M4": ("gamma",),
        "M12": ("gamma",),
        "M15": ("eta",),
        "M19": ("eta",),
        "M24": ("gamma_up", "p"),
    }
    keys = keys_by_label.get(label, ("epsilon", "p", "p_z", "gamma", "gamma_up", "eta", "strength"))
    for key in keys:
        value = _as_finite_float(params.get(key, record.get(key)))
        if value is not None:
            return value
    numeric = [value for _key, value in _numeric_leaves(params)]
    if numeric:
        return float(np.linalg.norm(np.asarray(numeric, dtype=np.float64)))
    return _default_mechanism_strength(label)


def _as_finite_float(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if np.isfinite(number) else None


def _default_mechanism_strength(label: str) -> float | None:
    defaults = {
        "M0": 0.002,
        "M1": 0.02,
        "M2": 0.02,
        "M3": 0.02,
        "M4": 0.015,
        "M5": 0.0025,
        "M6": 0.035,
        "M7": 0.035,
        "M8": 0.04,
        "M9": 0.006,
        "M10": 0.025,
        "M11": 0.02,
        "M12": 0.01,
        "M13": 0.03,
        "M14": 0.028,
        "M15": 0.02,
        "M16": 0.02,
        "M17": 0.018,
        "M18": 0.025,
        "M19": 0.006,
        "M20": 0.03,
        "M21": 0.035,
        "M22": 0.022,
        "M23": 0.019,
        "M24": 0.006,
        "M25": 0.006,
        "M26": 0.006,
        "M27": 0.026,
        "M28": 0.015,
        "M29": 0.018,
        "M30": 0.016,
        "M31": 0.017,
        "M32": 0.014,
        "M33": 0.013,
        "M34": 0.004,
    }
    return defaults.get(str(label))


def _numeric_values_non_degenerate(values: list[float]) -> bool:
    return bool(values and min(values) < max(values))


def _overlay_contract_missing_labels(audit: dict[str, object]) -> list[str]:
    labels = set()
    rows = audit.get("rows", [])
    if not isinstance(rows, list):
        return []
    for row in rows:
        if not isinstance(row, dict) or bool(row.get("overlay_payload_complete", False)):
            continue
        label = str(row.get("oracle_label", row.get("mechanism_id", "")))
        if label:
            labels.add(label)
    return sorted(labels)


def _overlay_recovery_audit(spectator_overlay: dict[str, object], overlay_contract: dict[str, object]) -> dict[str, object]:
    missing_labels = _overlay_contract_missing_labels(overlay_contract)
    num_overlay_records = int(overlay_contract.get("num_overlay_records", 0) or 0)
    missing_count = int(overlay_contract.get("num_overlay_records_missing_payload", 0) or 0)
    if missing_count > 0:
        return {
            "schema": "scope_static_s5_overlay_recovery_audit_v1",
            "description": "Evaluator-only S5 audit for non-flat overlay-family recovery; missing overlay payload is a contract failure, not a learner recovery failure.",
            "overlay_family": "spectator_crosstalk",
            "evaluator_only": True,
            "skipped": False,
            "used_for_training": False,
            "used_for_model_selection": False,
            "classification_target": "base_mechanism_plus_spectator_overlay_dimensions",
            "flat_exact_m11_target": False,
            "visible_only_selection": True,
            "uses_oracle_overlay_fields_for_training": False,
            "claims_physical_parameter_recovery": False,
            "num_overlay_records": num_overlay_records,
            "num_overlay_records_missing_payload": missing_count,
            "overlay_contract_payload_complete": False,
            "recovery_evaluable": False,
            "not_evaluable_target_ids": missing_labels,
            "failure_kind": OVERLAY_CONTRACT_MISSING_REASON,
            "recovery_failure": False,
            "base_mechanism_recovery": {},
            "victim_relative_location_recovery": {},
            "aggressor_relative_location_recovery": {},
            "coupling_axis_recovery": {},
            "timing_context_recovery": {},
            "overlay_strength_recovery": {},
            "joint_overlay_recovery": {},
            "checks": {
                "overlay_contract_payload_complete": False,
                "overlay_recovery_evaluable": False,
                "missing_overlay_payload_is_contract_failure_not_recovery_failure": True,
                "does_not_claim_flat_exact_m11_recovery": True,
            },
            "passed": False,
        }
    if bool(spectator_overlay.get("skipped", False)):
        return _skipped_overlay_recovery_audit(str(spectator_overlay.get("skip_reason", "no_spectator_overlay_records")))
    checks = {
        "overlay_contract_payload_complete": bool(overlay_contract.get("passed", False)),
        "overlay_recovery_evaluable": True,
        "spectator_overlay_recovery_passed": bool(spectator_overlay.get("passed", False)),
        "does_not_claim_flat_exact_m11_recovery": not bool(spectator_overlay.get("flat_exact_m11_target", True)),
    }
    return {
        "schema": "scope_static_s5_overlay_recovery_audit_v1",
        "description": "Evaluator-only S5 audit for M11-style spectator crosstalk overlay recovery.",
        "overlay_family": "spectator_crosstalk",
        "evaluator_only": True,
        "skipped": False,
        "used_for_training": False,
        "used_for_model_selection": False,
        "classification_target": "base_mechanism_plus_spectator_overlay_dimensions",
        "flat_exact_m11_target": False,
        "visible_only_selection": True,
        "uses_oracle_overlay_fields_for_training": False,
        "claims_physical_parameter_recovery": False,
        "num_overlay_records": num_overlay_records,
        "num_overlay_records_missing_payload": 0,
        "overlay_contract_payload_complete": bool(overlay_contract.get("passed", False)),
        "recovery_evaluable": True,
        "not_evaluable_target_ids": [],
        "failure_kind": None,
        "recovery_failure": not bool(spectator_overlay.get("passed", False)),
        "base_mechanism_recovery": {"base_mechanisms": spectator_overlay.get("base_mechanisms", [])},
        "victim_relative_location_recovery": {
            "reported_in_groups": all(
                bool(dict(row.get("victim_relative_location_counts", {}))) for row in list(spectator_overlay.get("groups", []))
            )
        },
        "aggressor_relative_location_recovery": {
            "reported_in_groups": all(
                bool(dict(row.get("aggressor_relative_location_counts", {}))) for row in list(spectator_overlay.get("groups", []))
            )
        },
        "coupling_axis_recovery": {"coupling_axes": spectator_overlay.get("coupling_axes", [])},
        "timing_context_recovery": {"timing_contexts": spectator_overlay.get("timing_contexts", [])},
        "overlay_strength_recovery": {
            "non_degenerate": bool(dict(spectator_overlay.get("checks", {})).get("overlay_strength_non_degenerate", False))
        },
        "joint_overlay_recovery": {
            "group_count": int(len(list(spectator_overlay.get("groups", [])))),
            "passed": bool(spectator_overlay.get("passed", False)),
        },
        "checks": checks,
        "passed": bool(all(checks.values())),
    }


def _skipped_overlay_contract_audit(reason: str) -> dict[str, object]:
    return {
        "schema": "scope_static_m11_overlay_contract_audit_v1",
        "skipped": True,
        "skip_reason": str(reason),
        "overlay_mechanism_ids": ["M11"],
        "overlay_family": "spectator_crosstalk",
        "required_fields": [],
        "fail_on_missing_overlay_payload": True,
        "num_overlay_records": 0,
        "num_overlay_records_missing_payload": 0,
        "missing_by_field": {},
        "failure_kinds": [],
        "rows": [],
        "passed": True,
    }


def _skipped_overlay_recovery_audit(reason: str) -> dict[str, object]:
    return {
        "schema": "scope_static_s5_overlay_recovery_audit_v1",
        "description": "Skipped because no evaluator-only overlay records are available.",
        "overlay_family": "spectator_crosstalk",
        "evaluator_only": False,
        "skipped": True,
        "skip_reason": str(reason),
        "used_for_training": False,
        "used_for_model_selection": False,
        "classification_target": "base_mechanism_plus_spectator_overlay_dimensions",
        "flat_exact_m11_target": False,
        "visible_only_selection": True,
        "uses_oracle_overlay_fields_for_training": False,
        "claims_physical_parameter_recovery": False,
        "num_overlay_records": 0,
        "num_overlay_records_missing_payload": 0,
        "overlay_contract_payload_complete": True,
        "recovery_evaluable": False,
        "not_evaluable_target_ids": [],
        "failure_kind": None,
        "recovery_failure": False,
        "base_mechanism_recovery": {},
        "victim_relative_location_recovery": {},
        "aggressor_relative_location_recovery": {},
        "coupling_axis_recovery": {},
        "timing_context_recovery": {},
        "overlay_strength_recovery": {},
        "joint_overlay_recovery": {},
        "checks": {"skipped_without_overlay_records": True},
        "passed": True,
    }


def _spectator_overlay_audit(matrix: np.ndarray, records: list[dict[str, object]], *, feature_names: list[str]) -> dict[str, object]:
    overlay_indices = [idx for idx, record in enumerate(records) if _spectator_overlay_present(record)]
    if not overlay_indices:
        return _skipped_spectator_overlay_audit("no_spectator_overlay_records")

    groups: dict[tuple[str, str], list[int]] = {}
    for idx in overlay_indices:
        record = records[idx]
        key = (_spectator_overlay_base_mechanism(record), _spectator_overlay_field(record, "coupling_axis", default="unknown"))
        groups.setdefault(key, []).append(int(idx))

    group_rows = []
    for (base_mechanism, coupling_axis), indices in sorted(groups.items(), key=lambda item: item[0]):
        weights = np.zeros(len(records), dtype=np.float64)
        weights[np.asarray(indices, dtype=np.int64)] = 1.0
        local_records = [records[idx] for idx in indices]
        group_rows.append(
            {
                "base_mechanism": str(base_mechanism),
                "coupling_axis": str(coupling_axis),
                "support_count": int(len(indices)),
                "classification_target": "base_mechanism_plus_spectator_overlay_dimensions",
                "flat_exact_m11_target": False,
                "timing_context_counts": _value_counts([_spectator_overlay_field(record, "timing_context", default="unknown") for record in local_records]),
                "victim_relative_location_counts": _value_counts(
                    [_spectator_overlay_field(record, "victim_relative_location", default="unknown") for record in local_records]
                ),
                "aggressor_relative_location_counts": _value_counts(
                    [_spectator_overlay_field(record, "aggressor_relative_location", default="unknown") for record in local_records]
                ),
                "overlay_strength": _numeric_summary(np.asarray([_spectator_overlay_strength(record) for record in local_records], dtype=np.float64)),
                "context_relative_action_locations": _context_relative_location_summary(records, weights=weights),
                "visible_strength": _weighted_visible_strength(matrix, weights, feature_names=feature_names, records=records),
                "oracle_parameter_strength": _oracle_parameter_strength(local_records),
            }
        )

    overlay_records = [records[idx] for idx in overlay_indices]
    strengths = np.asarray([_spectator_overlay_strength(record) for record in overlay_records], dtype=np.float64)
    checks = {
        "overlay_is_not_flat_exact_m11_target": True,
        "overlay_rows_have_base_mechanism": all(_spectator_overlay_base_mechanism(record) != "unknown" for record in overlay_records),
        "overlay_rows_have_victim_relative_location": all(
            _spectator_overlay_field(record, "victim_relative_location", default="unknown") != "unknown" for record in overlay_records
        ),
        "overlay_rows_have_aggressor_relative_location": all(
            _spectator_overlay_field(record, "aggressor_relative_location", default="unknown") != "unknown" for record in overlay_records
        ),
        "overlay_rows_have_coupling_axis": all(_spectator_overlay_field(record, "coupling_axis", default="unknown") != "unknown" for record in overlay_records),
        "overlay_rows_have_timing_context": all(_spectator_overlay_field(record, "timing_context", default="unknown") != "unknown" for record in overlay_records),
        "overlay_strength_non_degenerate": bool(strengths.size > 1 and float(np.min(strengths)) < float(np.max(strengths))),
        "overlay_groups_have_visible_strength": all(
            float(dict(dict(row.get("visible_strength", {})).get("context_relative_reference", {})).get("surface_standardized_l2_shift", 0.0) or 0.0)
            > 0.0
            for row in group_rows
        ),
    }
    return {
        "schema": "scope_static_s5_spectator_overlay_audit_v1",
        "description": "Evaluator-only S5 audit for M11-style spectator crosstalk as a context-conditioned overlay family, not a flat exact mechanism.",
        "evaluator_only": True,
        "skipped": False,
        "used_for_training": False,
        "used_for_model_selection": False,
        "classification_target": "base_mechanism_plus_spectator_overlay_dimensions",
        "flat_exact_m11_target": False,
        "claims_physical_parameter_recovery": False,
        "overlay_row_count": int(len(overlay_indices)),
        "base_mechanisms": sorted({_spectator_overlay_base_mechanism(record) for record in overlay_records}),
        "coupling_axes": sorted({_spectator_overlay_field(record, "coupling_axis", default="unknown") for record in overlay_records}),
        "timing_contexts": sorted({_spectator_overlay_field(record, "timing_context", default="unknown") for record in overlay_records}),
        "checks": checks,
        "groups": group_rows,
        "passed": bool(all(checks.values())),
    }


def _skipped_spectator_overlay_audit(reason: str) -> dict[str, object]:
    return {
        "schema": "scope_static_s5_spectator_overlay_audit_v1",
        "description": "Skipped because no evaluator-only spectator overlay records are available.",
        "evaluator_only": False,
        "skipped": True,
        "skip_reason": str(reason),
        "used_for_training": False,
        "used_for_model_selection": False,
        "classification_target": "base_mechanism_plus_spectator_overlay_dimensions",
        "flat_exact_m11_target": False,
        "claims_physical_parameter_recovery": False,
        "overlay_row_count": 0,
        "base_mechanisms": [],
        "coupling_axes": [],
        "timing_contexts": [],
        "checks": {},
        "groups": [],
        "passed": True,
    }


def _spectator_overlay_present(record: dict[str, object]) -> bool:
    if bool(record.get("spectator_overlay_present", False)):
        return True
    overlay = record.get("spectator_overlay", {})
    if isinstance(overlay, dict) and overlay.get("present", False):
        return True
    params = record.get("parameters", {})
    return bool(isinstance(params, dict) and params.get("spectator_overlay_present", False))


def _spectator_overlay_base_mechanism(record: dict[str, object]) -> str:
    return _spectator_overlay_field(record, "base_mechanism", default=str(record.get("oracle_label", record.get("mechanism_id", "unknown"))))


def _spectator_overlay_field(record: dict[str, object], field: str, *, default: str) -> str:
    if record.get(field) is not None:
        return str(record.get(field))
    overlay = record.get("spectator_overlay", {})
    if isinstance(overlay, dict) and overlay.get(field) is not None:
        return str(overlay.get(field))
    params = record.get("parameters", {})
    if isinstance(params, dict) and params.get(field) is not None:
        return str(params.get(field))
    return str(default)


def _spectator_overlay_strength(record: dict[str, object]) -> float:
    for container in (record.get("spectator_overlay", {}), record.get("parameters", {}), record):
        if not isinstance(container, dict):
            continue
        for key in ("strength", "spectator_strength", "coupling_strength"):
            if container.get(key) is None:
                continue
            try:
                value = float(container.get(key))
            except (TypeError, ValueError):
                continue
            if np.isfinite(value):
                return value
    return 0.0


def _effect_recovery_payload(
    matrix: np.ndarray,
    *,
    predicted_weights: np.ndarray,
    oracle_weights: np.ndarray,
    records: list[dict[str, object]],
    feature_names: list[str],
    label: str,
) -> dict[str, object]:
    predicted = _effect_payload(
        matrix,
        predicted_weights,
        records=records,
        feature_names=feature_names,
        label=str(label),
        source="predicted_from_stage3b1_soft_assignment",
    )
    oracle = _effect_payload(
        matrix,
        oracle_weights,
        records=records,
        feature_names=feature_names,
        label=str(label),
        source="oracle_evaluator_only",
    )
    metrics = _effect_recovery_metrics(predicted, oracle)
    return {
        "label": str(label),
        "support_count": int(np.sum(np.asarray(oracle_weights, dtype=np.float64) > 0.0)),
        "soft_assignment_mass": float(np.sum(np.asarray(predicted_weights, dtype=np.float64))),
        "oracle_assignment_mass": float(np.sum(np.asarray(oracle_weights, dtype=np.float64))),
        "predicted_effect": predicted,
        "oracle_effect": oracle,
        "recovery_metrics": metrics,
        "visible_strength": predicted["visible_strength"],
        "context_relative_action_locations": predicted["context_relative_action_locations"],
        "context_likelihood": predicted["context_relative_action_locations"]["context_likelihood"],
        "oracle_visible_strength": oracle["visible_strength"],
        "oracle_context_relative_action_locations": oracle["context_relative_action_locations"],
        "oracle_context_likelihood": oracle["context_relative_action_locations"]["context_likelihood"],
        "absolute_provenance_counts": oracle["absolute_provenance_counts"],
        "oracle_parameter_strength": oracle["oracle_parameter_strength"],
        "passed": bool(metrics["passed"]),
    }


def _effect_payload(
    matrix: np.ndarray,
    weights: np.ndarray,
    *,
    records: list[dict[str, object]],
    feature_names: list[str],
    label: str,
    source: str,
) -> dict[str, object]:
    return {
        "label": str(label),
        "source": str(source),
        "assignment_mass": float(np.sum(np.asarray(weights, dtype=np.float64))),
        "visible_strength": _weighted_visible_strength(matrix, weights, feature_names=feature_names, records=records),
        "context_relative_action_locations": _context_relative_location_summary(records, weights=weights),
        "absolute_provenance_counts": _absolute_provenance_summary(_records_with_positive_weight(records, weights)),
        "oracle_parameter_strength": _oracle_parameter_strength(_records_with_positive_weight(records, weights)),
    }


def _weighted_visible_strength(
    matrix: np.ndarray,
    weights: np.ndarray,
    *,
    feature_names: list[str],
    records: list[dict[str, object]],
) -> dict[str, object]:
    arr = np.asarray(matrix, dtype=np.float64)
    w = np.asarray(weights, dtype=np.float64).reshape(-1)
    if arr.ndim != 2:
        raise ValueError("visible feature matrix must be 2D")
    if int(w.size) != int(arr.shape[0]):
        raise ValueError("weight row count must match visible feature rows")
    if len(records) != int(arr.shape[0]):
        raise ValueError("record count must match visible feature rows")
    names = [str(name) for name in feature_names]
    if len(names) != int(arr.shape[1]):
        names = [f"feature_{idx}" for idx in range(int(arr.shape[1]))]
    surface_mask = np.asarray([not name.startswith(("meta__", "visible_metadata__")) for name in names], dtype=bool)
    raw_mask = np.asarray([name.startswith("raw__") for name in names], dtype=bool)
    if arr.shape[1] == 0 or arr.shape[0] == 0 or float(np.sum(w)) <= 0.0:
        return {
            "weight_mass": float(np.sum(w)),
            "surface_feature_count": int(np.sum(surface_mask)),
            "raw_feature_count": int(np.sum(raw_mask)),
            "primary_reference_frame": "context_relative",
            "context_relative_reference": _empty_strength_reference(),
            "global_reference": _empty_strength_reference(),
        }
    mass = float(np.sum(w))
    global_mean = np.mean(arr, axis=0)
    global_scale = np.std(arr, axis=0)
    global_scale = np.where(global_scale > 1.0e-12, global_scale, 1.0)
    global_shift = (w[:, None] * arr).sum(axis=0) / mass - global_mean
    global_z = global_shift / global_scale
    context_z = _context_relative_weighted_z_shift(arr, w, records)
    context_shift = context_z
    context_count = int(len({_context_key(record) for record in records}))
    return {
        "weight_mass": mass,
        "surface_feature_count": int(np.sum(surface_mask)),
        "raw_feature_count": int(np.sum(raw_mask)),
        "primary_reference_frame": "context_relative",
        "context_count": context_count,
        "context_relative_reference": _strength_reference_payload(names, context_shift, context_z, surface_mask=surface_mask, raw_mask=raw_mask),
        "global_reference": _strength_reference_payload(names, global_shift, global_z, surface_mask=surface_mask, raw_mask=raw_mask),
    }


def _effect_recovery_metrics(predicted: dict[str, object], oracle: dict[str, object]) -> dict[str, object]:
    pred_strength = dict(predicted.get("visible_strength", {}))
    oracle_strength = dict(oracle.get("visible_strength", {}))
    pred_context = dict(pred_strength.get("context_relative_reference", {}))
    oracle_context = dict(oracle_strength.get("context_relative_reference", {}))
    pred_location = dict(predicted.get("context_relative_action_locations", {}))
    oracle_location = dict(oracle.get("context_relative_action_locations", {}))
    strength_errors = {
        "surface_l2_abs_error": _abs_diff(
            pred_context.get("surface_standardized_l2_shift"),
            oracle_context.get("surface_standardized_l2_shift"),
        ),
        "raw_l2_abs_error": _abs_diff(
            pred_context.get("raw_standardized_l2_shift"),
            oracle_context.get("raw_standardized_l2_shift"),
        ),
        "surface_mean_abs_shift_abs_error": _abs_diff(
            pred_context.get("surface_mean_abs_standardized_shift"),
            oracle_context.get("surface_mean_abs_standardized_shift"),
        ),
        "raw_mean_abs_shift_abs_error": _abs_diff(
            pred_context.get("raw_mean_abs_standardized_shift"),
            oracle_context.get("raw_mean_abs_standardized_shift"),
        ),
        "top_context_relative_strength_block_match": _top_strength_block(pred_context) == _top_strength_block(oracle_context),
    }
    location_errors = {
        "location_fraction_mean_abs_error": _summary_mean_abs_error(
            pred_location.get("location_fraction_in_context"),
            oracle_location.get("location_fraction_in_context"),
        ),
        "qubit_center_fraction_mean_abs_error": _summary_mean_abs_error(
            pred_location.get("qubit_center_fraction_in_context"),
            oracle_location.get("qubit_center_fraction_in_context"),
        ),
        "qubit_span_fraction_mean_abs_error": _summary_mean_abs_error(
            pred_location.get("qubit_span_fraction_in_context"),
            oracle_location.get("qubit_span_fraction_in_context"),
        ),
        "top_relative_location_cell_match": _top_count_value(pred_location.get("top_relative_location_cells"))
        == _top_count_value(oracle_location.get("top_relative_location_cells")),
    }
    context_likelihood_errors = {
        "context_likelihood_location_fraction_mean_abs_error": location_errors["location_fraction_mean_abs_error"],
        "context_likelihood_qubit_center_fraction_mean_abs_error": location_errors["qubit_center_fraction_mean_abs_error"],
        "context_likelihood_qubit_span_fraction_mean_abs_error": location_errors["qubit_span_fraction_mean_abs_error"],
        "top_context_likelihood_cell_match": location_errors["top_relative_location_cell_match"],
        "semantic_note": "Alias of location_errors with S5 location interpreted as context-conditioned likelihood/support.",
    }
    scalar_errors = [
        value
        for value in [*strength_errors.values(), *location_errors.values()]
        if isinstance(value, float)
    ]
    passed = (
        all(abs(float(value)) <= 1.0e-12 for value in scalar_errors)
        and bool(strength_errors["top_context_relative_strength_block_match"])
        and bool(location_errors["top_relative_location_cell_match"])
    )
    return {
        "schema": "scope_static_s5_effect_recovery_metrics_v1",
        "metric_role": "predicted_effect_vs_oracle_effect",
        "strength_errors": strength_errors,
        "location_errors": location_errors,
        "context_likelihood_errors": context_likelihood_errors,
        "max_abs_scalar_error": float(max([abs(float(value)) for value in scalar_errors], default=0.0)),
        "passed": bool(passed),
    }


def _effect_recovery_summary(*, per_family: dict[str, object], per_exact: dict[str, object]) -> dict[str, object]:
    rows = [dict(row) for row in [*per_family.values(), *per_exact.values()] if isinstance(row, dict)]
    metrics = [dict(row.get("recovery_metrics", {})) for row in rows if isinstance(row.get("recovery_metrics", {}), dict)]
    max_error = float(max([float(row.get("max_abs_scalar_error", 0.0) or 0.0) for row in metrics], default=0.0))
    failed = [
        str(row.get("label", ""))
        for row in rows
        if isinstance(row.get("recovery_metrics", {}), dict) and not bool(dict(row.get("recovery_metrics", {})).get("passed", False))
    ]
    return {
        "schema": "scope_static_s5_effect_recovery_summary_v1",
        "family_count": int(len(per_family)),
        "exact_mechanism_count": int(len(per_exact)),
        "max_abs_scalar_error": max_error,
        "failed_labels": failed,
        "passed": not failed and max_error <= 1.0e-12,
    }


def _abs_diff(left: object, right: object) -> float:
    if left is None or right is None:
        return 0.0
    return abs(float(left) - float(right))


def _summary_mean_abs_error(left: object, right: object) -> float:
    left_summary = dict(left) if isinstance(left, dict) else {}
    right_summary = dict(right) if isinstance(right, dict) else {}
    return _abs_diff(left_summary.get("signed_mean"), right_summary.get("signed_mean"))


def _top_strength_block(reference: dict[str, object]) -> str:
    blocks = reference.get("block_strengths", {})
    if not isinstance(blocks, dict) or not blocks:
        return ""
    ranked = sorted(
        (
            (float(dict(payload).get("standardized_l2_shift", 0.0) or 0.0), str(name))
            for name, payload in blocks.items()
            if isinstance(payload, dict)
        ),
        key=lambda item: (-item[0], item[1]),
    )
    return ranked[0][1] if ranked else ""


def _top_count_value(value: object) -> str:
    rows = value if isinstance(value, list) else []
    if not rows:
        return ""
    first = dict(rows[0]) if isinstance(rows[0], dict) else {}
    return str(first.get("value", ""))


def _context_relative_weighted_z_shift(arr: np.ndarray, weights: np.ndarray, records: list[dict[str, object]]) -> np.ndarray:
    residual = np.zeros_like(arr, dtype=np.float64)
    by_context: dict[str, list[int]] = {}
    for idx, record in enumerate(records):
        by_context.setdefault(_context_key(record), []).append(int(idx))
    for indices in by_context.values():
        idx = np.asarray(indices, dtype=np.int64)
        context = arr[idx]
        mean = np.mean(context, axis=0)
        scale = np.std(context, axis=0)
        scale = np.where(scale > 1.0e-12, scale, 1.0)
        residual[idx] = (context - mean[None, :]) / scale[None, :]
    mass = float(np.sum(weights))
    if mass <= 0.0:
        return np.zeros(int(arr.shape[1]), dtype=np.float64)
    return (weights[:, None] * residual).sum(axis=0) / mass


def _empty_strength_reference() -> dict[str, object]:
    return {
        "overall_standardized_l2_shift": 0.0,
        "overall_mean_abs_standardized_shift": 0.0,
        "surface_standardized_l2_shift": 0.0,
        "surface_mean_abs_standardized_shift": 0.0,
        "raw_standardized_l2_shift": 0.0,
        "raw_mean_abs_standardized_shift": 0.0,
        "top_feature_shifts": [],
        "top_surface_feature_shifts": [],
        "top_raw_feature_shifts": [],
        "block_strengths": {},
    }


def _strength_reference_payload(
    names: list[str],
    shift: np.ndarray,
    z_shift: np.ndarray,
    *,
    surface_mask: np.ndarray,
    raw_mask: np.ndarray,
) -> dict[str, object]:
    surface_z = z_shift[surface_mask]
    raw_z = z_shift[raw_mask]
    block_strengths = {}
    for block, indices in _feature_block_indices(names).items():
        idx = np.asarray(indices, dtype=np.int64)
        values = z_shift[idx]
        block_strengths[block] = {
            "feature_count": int(idx.size),
            "standardized_l2_shift": float(np.linalg.norm(values)),
            "mean_abs_standardized_shift": float(np.mean(np.abs(values))) if values.size else 0.0,
            "max_abs_standardized_shift": float(np.max(np.abs(values))) if values.size else 0.0,
        }
    return {
        "overall_standardized_l2_shift": float(np.linalg.norm(z_shift)),
        "overall_mean_abs_standardized_shift": float(np.mean(np.abs(z_shift))) if z_shift.size else 0.0,
        "surface_standardized_l2_shift": float(np.linalg.norm(surface_z)) if surface_z.size else 0.0,
        "surface_mean_abs_standardized_shift": float(np.mean(np.abs(surface_z))) if surface_z.size else 0.0,
        "raw_standardized_l2_shift": float(np.linalg.norm(raw_z)) if raw_z.size else 0.0,
        "raw_mean_abs_standardized_shift": float(np.mean(np.abs(raw_z))) if raw_z.size else 0.0,
        "top_feature_shifts": _top_feature_shifts(names, shift, z_shift, limit=8),
        "top_surface_feature_shifts": _top_feature_shifts(names, shift, z_shift, mask=surface_mask, limit=8),
        "top_raw_feature_shifts": _top_feature_shifts(names, shift, z_shift, mask=raw_mask, limit=8),
        "block_strengths": block_strengths,
    }


def _top_feature_shifts(
    feature_names: list[str],
    shift: np.ndarray,
    z_shift: np.ndarray,
    *,
    mask: np.ndarray | None = None,
    limit: int,
) -> list[dict[str, object]]:
    idxs = np.arange(int(len(feature_names)), dtype=np.int64)
    if mask is not None:
        idxs = idxs[np.asarray(mask, dtype=bool)]
    ranked = sorted(idxs.tolist(), key=lambda idx: (-abs(float(z_shift[int(idx)])), str(feature_names[int(idx)])))
    return [
        {
            "feature_name": str(feature_names[int(idx)]),
            "signed_shift": float(shift[int(idx)]),
            "standardized_shift": float(z_shift[int(idx)]),
            "abs_standardized_shift": abs(float(z_shift[int(idx)])),
        }
        for idx in ranked[: max(0, int(limit))]
    ]


def _records_with_context_relative_location(records: list[dict[str, object]]) -> list[dict[str, object]]:
    out = [dict(record) for record in records]
    by_context: dict[str, list[int]] = {}
    for idx, record in enumerate(out):
        by_context.setdefault(_context_key(record), []).append(idx)
    for context_key, indices in by_context.items():
        context_records = [out[idx] for idx in indices]
        unique_locations = sorted({int(record["location_id"]) for record in context_records if _is_int_like(record.get("location_id"))})
        location_rank = {value: idx for idx, value in enumerate(unique_locations)}
        location_den = max(1, len(unique_locations) - 1)
        unique_qubits = sorted({int(value) for record in context_records for value in _list_values(record.get("qubits", [])) if _is_int_like(value)})
        qubit_rank = {value: idx for idx, value in enumerate(unique_qubits)}
        qubit_den = max(1, len(unique_qubits) - 1)
        for idx in indices:
            record = out[idx]
            qubits = [int(value) for value in _list_values(record.get("qubits", [])) if _is_int_like(value)]
            loc = record.get("location_id")
            loc_fraction = None
            loc_rank = None
            if _is_int_like(loc) and int(loc) in location_rank:
                loc_rank = int(location_rank[int(loc)])
                loc_fraction = float(loc_rank / float(location_den))
            qubit_fractions = [float(qubit_rank[q] / float(qubit_den)) for q in qubits if q in qubit_rank]
            center = float(np.mean(qubit_fractions)) if qubit_fractions else None
            span = float(max(qubit_fractions) - min(qubit_fractions)) if qubit_fractions else None
            record["_context_relative_location"] = {
                "context_key": str(context_key),
                "context_record_count": int(len(indices)),
                "context_unique_location_count": int(len(unique_locations)),
                "context_unique_qubit_count": int(len(unique_qubits)),
                "location_rank_in_context": loc_rank,
                "location_fraction_in_context": loc_fraction,
                "location_bucket_in_context": _fraction_bucket(loc_fraction),
                "qubit_center_fraction_in_context": center,
                "qubit_span_fraction_in_context": span,
                "qubit_center_bucket_in_context": _fraction_bucket(center),
                "qubit_arity": int(len(qubits)),
                "instruction": str(record.get("instruction", "unknown")),
            }
    return out


def _context_relative_location_summary(records: list[dict[str, object]], *, weights: np.ndarray | None = None) -> dict[str, object]:
    rows = [dict(record.get("_context_relative_location", {})) for record in records if isinstance(record.get("_context_relative_location", {}), dict)]
    if weights is None:
        row_weights = np.ones(len(rows), dtype=np.float64)
    else:
        raw_weights = np.asarray(weights, dtype=np.float64).reshape(-1)
        row_weights = np.asarray(
            [float(raw_weights[idx]) if idx < int(raw_weights.size) else 0.0 for idx, record in enumerate(records) if isinstance(record.get("_context_relative_location", {}), dict)],
            dtype=np.float64,
        )
    location_pairs = [
        (float(row["location_fraction_in_context"]), float(row_weights[idx]))
        for idx, row in enumerate(rows)
        if row.get("location_fraction_in_context") is not None
    ]
    qubit_center_pairs = [
        (float(row["qubit_center_fraction_in_context"]), float(row_weights[idx]))
        for idx, row in enumerate(rows)
        if row.get("qubit_center_fraction_in_context") is not None
    ]
    qubit_span_pairs = [
        (float(row["qubit_span_fraction_in_context"]), float(row_weights[idx]))
        for idx, row in enumerate(rows)
        if row.get("qubit_span_fraction_in_context") is not None
    ]
    cells = [
        "|".join(
            [
                str(row.get("location_bucket_in_context", "unknown")),
                str(row.get("qubit_center_bucket_in_context", "unknown")),
                f"arity={int(row.get('qubit_arity', 0) or 0)}",
                str(row.get("instruction", "unknown")),
            ]
        )
        for row in rows
    ]
    loc_summary = _weighted_numeric_summary(location_pairs)
    center_summary = _weighted_numeric_summary(qubit_center_pairs)
    span_summary = _weighted_numeric_summary(qubit_span_pairs)
    location_bucket_counts = _weighted_value_counts([row.get("location_bucket_in_context", "unknown") for row in rows], row_weights)
    qubit_center_bucket_counts = _weighted_value_counts([row.get("qubit_center_bucket_in_context", "unknown") for row in rows], row_weights)
    qubit_arity_counts = _weighted_value_counts([row.get("qubit_arity", 0) for row in rows], row_weights)
    instruction_counts = _weighted_value_counts([row.get("instruction", "unknown") for row in rows], row_weights)
    top_cells = _top_weighted_counts(cells, row_weights)
    context_likelihood = {
        "schema": "scope_static_s5_context_conditioned_likelihood_v1",
        "semantic_role": "context_conditioned_error_likelihood",
        "definition": "Weighted likelihood/support that an error effect appears in a context-relative cell conditioned on the public/probe context.",
        "conditioned_on": "context_key",
        "cell_definition": "location_bucket_in_context|qubit_center_bucket_in_context|qubit_arity|instruction",
        "reference_frame": "context_relative",
        "weight_mass": float(np.sum(row_weights)),
        "context_count": int(len(set(str(row.get("context_key", "")) for row in rows))),
        "location_fraction_in_context": loc_summary,
        "qubit_center_fraction_in_context": center_summary,
        "qubit_span_fraction_in_context": span_summary,
        "location_bucket_likelihood_mass": location_bucket_counts,
        "qubit_center_bucket_likelihood_mass": qubit_center_bucket_counts,
        "qubit_arity_likelihood_mass": qubit_arity_counts,
        "instruction_likelihood_mass": instruction_counts,
        "top_context_likelihood_cells": top_cells,
    }
    return {
        "reference_frame": "context_relative",
        "semantic_role": "context_conditioned_error_likelihood",
        "location_semantics": "context-likelihood, not absolute coordinate recovery",
        "record_count": int(len(records)),
        "weight_mass": float(np.sum(row_weights)),
        "context_count": int(len(set(str(row.get("context_key", "")) for row in rows))),
        "location_fraction_in_context": loc_summary,
        "qubit_center_fraction_in_context": center_summary,
        "qubit_span_fraction_in_context": span_summary,
        "location_bucket_counts": location_bucket_counts,
        "qubit_center_bucket_counts": qubit_center_bucket_counts,
        "qubit_arity_counts": qubit_arity_counts,
        "instruction_counts": instruction_counts,
        "top_relative_location_cells": top_cells,
        "context_likelihood": context_likelihood,
    }


def _absolute_provenance_summary(records: list[dict[str, object]]) -> dict[str, object]:
    qubits: list[object] = []
    locations: list[object] = []
    circuits: list[object] = []
    probe_indices: list[object] = []
    for record in records:
        qubits.extend(_list_values(record.get("qubits", [])))
        probe_indices.extend(_list_values(record.get("probe_indices", [])))
        if record.get("location_id") is not None:
            locations.append(record.get("location_id"))
        if record.get("circuit_id") is not None:
            circuits.append(record.get("circuit_id"))
    return {
        "provenance_only": True,
        "record_count": int(len(records)),
        "qubit_counts": _value_counts(qubits),
        "location_id_counts": _value_counts(locations),
        "circuit_id_counts": _value_counts(circuits),
        "probe_index_counts": _value_counts(probe_indices),
    }


def _records_with_positive_weight(records: list[dict[str, object]], weights: np.ndarray) -> list[dict[str, object]]:
    raw_weights = np.asarray(weights, dtype=np.float64).reshape(-1)
    return [record for idx, record in enumerate(records) if idx < int(raw_weights.size) and float(raw_weights[idx]) > 0.0]


def _oracle_parameter_strength(records: list[dict[str, object]]) -> dict[str, object]:
    by_name: dict[str, list[float]] = {}
    all_values: list[float] = []
    records_with_numeric = 0
    for record in records:
        leaves = _numeric_leaves(record.get("parameters", {}))
        if leaves:
            records_with_numeric += 1
        for name, value in leaves:
            by_name.setdefault(name, []).append(float(value))
            all_values.append(float(value))
    values = np.asarray(all_values, dtype=np.float64)
    summary = _numeric_summary(values)
    summary.update(
        {
            "record_count": int(len(records)),
            "records_with_numeric_parameters": int(records_with_numeric),
            "numeric_parameter_count": int(values.size),
            "per_parameter": {name: _numeric_summary(np.asarray(raw, dtype=np.float64)) for name, raw in sorted(by_name.items())},
        }
    )
    return summary


def _numeric_summary(values: np.ndarray) -> dict[str, object]:
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0:
        return {"count": 0, "signed_mean": 0.0, "mean_abs": 0.0, "max_abs": 0.0, "rms": 0.0, "min": 0.0, "max": 0.0}
    return {
        "count": int(arr.size),
        "signed_mean": float(np.mean(arr)),
        "mean_abs": float(np.mean(np.abs(arr))),
        "max_abs": float(np.max(np.abs(arr))),
        "rms": float(np.sqrt(np.mean(arr * arr))),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
    }


def _weighted_numeric_summary(pairs: list[tuple[float, float]]) -> dict[str, object]:
    if not pairs:
        return {"count": 0, "weight_mass": 0.0, "signed_mean": 0.0, "mean_abs": 0.0, "max_abs": 0.0, "rms": 0.0, "min": 0.0, "max": 0.0}
    values = np.asarray([value for value, _weight in pairs], dtype=np.float64)
    weights = np.asarray([max(0.0, weight) for _value, weight in pairs], dtype=np.float64)
    mass = float(np.sum(weights))
    if mass <= 0.0:
        return {"count": int(values.size), "weight_mass": 0.0, "signed_mean": 0.0, "mean_abs": 0.0, "max_abs": 0.0, "rms": 0.0, "min": 0.0, "max": 0.0}
    return {
        "count": int(values.size),
        "weight_mass": mass,
        "signed_mean": float(np.sum(weights * values) / mass),
        "mean_abs": float(np.sum(weights * np.abs(values)) / mass),
        "max_abs": float(np.max(np.abs(values[weights > 0.0]))) if np.any(weights > 0.0) else 0.0,
        "rms": float(np.sqrt(np.sum(weights * values * values) / mass)),
        "min": float(np.min(values[weights > 0.0])) if np.any(weights > 0.0) else 0.0,
        "max": float(np.max(values[weights > 0.0])) if np.any(weights > 0.0) else 0.0,
    }


def _numeric_leaves(value: object, *, prefix: str = "") -> list[tuple[str, float]]:
    if isinstance(value, bool):
        return []
    if isinstance(value, (int, float, np.integer, np.floating)):
        number = float(value)
        return [(prefix or "value", number)] if np.isfinite(number) else []
    if isinstance(value, dict):
        leaves: list[tuple[str, float]] = []
        for key, child in sorted(value.items(), key=lambda item: str(item[0])):
            leaves.extend(_numeric_leaves(child, prefix=f"{prefix}.{key}" if prefix else str(key)))
        return leaves
    if isinstance(value, (list, tuple)):
        leaves = []
        for idx, child in enumerate(value):
            leaves.extend(_numeric_leaves(child, prefix=f"{prefix}.{idx}" if prefix else str(idx)))
        return leaves
    return []


def _list_values(value: object) -> list[object]:
    if isinstance(value, (list, tuple)):
        return list(value)
    if value is None:
        return []
    return [value]


def _value_counts(values: list[object]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        counts[key] = int(counts.get(key, 0)) + 1
    return dict(sorted(counts.items(), key=lambda item: (-int(item[1]), item[0])))


def _weighted_value_counts(values: list[object], weights: np.ndarray) -> dict[str, float]:
    counts: dict[str, float] = {}
    raw_weights = np.asarray(weights, dtype=np.float64).reshape(-1)
    for idx, value in enumerate(values):
        weight = float(raw_weights[idx]) if idx < int(raw_weights.size) else 0.0
        if weight <= 0.0:
            continue
        key = str(value)
        counts[key] = float(counts.get(key, 0.0)) + weight
    return dict(sorted(counts.items(), key=lambda item: (-float(item[1]), item[0])))


def _top_counts(values: list[object], *, limit: int = 8) -> list[dict[str, object]]:
    return [{"value": key, "count": int(count)} for key, count in list(_value_counts(values).items())[: max(0, int(limit))]]


def _top_weighted_counts(values: list[object], weights: np.ndarray, *, limit: int = 8) -> list[dict[str, object]]:
    return [{"value": key, "count": float(count)} for key, count in list(_weighted_value_counts(values, weights).items())[: max(0, int(limit))]]


def _context_key(record: dict[str, object]) -> str:
    if record.get("circuit_id") is not None:
        return f"circuit:{record.get('circuit_id')}"
    if record.get("context_group") is not None:
        return f"context:{record.get('context_group')}"
    return "context:global"


def _fraction_bucket(value: object) -> str:
    if value is None:
        return "unknown"
    number = float(value)
    if number <= 1.0 / 3.0:
        return "leading"
    if number <= 2.0 / 3.0:
        return "middle"
    return "trailing"


def _is_int_like(value: object) -> bool:
    if isinstance(value, bool):
        return False
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return bool(np.isfinite(number) and abs(number - int(number)) <= 1.0e-12)


def _mechanism_sort_key(label: str) -> tuple[int, str]:
    text = str(label)
    if text.startswith("F") and text[1:].isdigit():
        return (int(text[1:]), text)
    if text.startswith("M") and text[1:].isdigit():
        return (10_000 + int(text[1:]), text)
    return (20_000, text)


def _classification_metrics(true_labels: list[str], predicted_labels: list[str], *, class_names: list[str]) -> dict[str, object]:
    if len(true_labels) != len(predicted_labels):
        raise ValueError("true and predicted label counts must match")
    names = [name for name in class_names if name in set(true_labels) or name in set(predicted_labels)]
    names.extend(sorted((set(true_labels) | set(predicted_labels)) - set(names)))
    name_to_idx = {name: idx for idx, name in enumerate(names)}
    confusion = np.zeros((len(names), len(names)), dtype=np.int64)
    support = {name: 0 for name in names}
    correct = {name: 0 for name in names}
    for true, pred in zip(true_labels, predicted_labels):
        if true not in name_to_idx or pred not in name_to_idx:
            continue
        confusion[name_to_idx[true], name_to_idx[pred]] += 1
        support[true] += 1
        if true == pred:
            correct[true] += 1
    recalls = [float(correct[name]) / float(support[name]) if support[name] else 0.0 for name in names]
    true_ids = _encode_with_names(true_labels, names)
    pred_ids = _encode_with_names(predicted_labels, names)
    return {
        "class_names": names,
        "support": {name: int(value) for name, value in support.items()},
        "per_family_recall": {name: float(recall) for name, recall in zip(names, recalls)},
        "balanced_accuracy": float(np.mean(recalls)) if recalls else 1.0,
        "min_recall": float(min(recalls)) if recalls else 1.0,
        "adjusted_rand_index": float(adjusted_rand_index(true_ids, pred_ids)),
        "normalized_mutual_info": float(normalized_mutual_info(true_ids, pred_ids)),
        "confusion_matrix": {
            "rows_true_family": names,
            "columns_predicted_family": names,
            "matrix": [[int(value) for value in row] for row in confusion.tolist()],
        },
    }


def _encode_with_names(labels: list[str], names: list[str]) -> list[int]:
    mapping = {name: idx for idx, name in enumerate(names)}
    return [int(mapping[label]) for label in labels]
