from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from scope_static.primitives.mechanism_catalog import CURRENT_VISIBLE_SURFACE_FLAT_EXACT_CLAIM_TARGET_IDS
from .audit_values import optional_float


def is_one(value: object, *, atol: float = 1.0e-12) -> bool:
    if value is None:
        return False
    return bool(abs(float(value) - 1.0) <= float(atol))


def flat_exact_claim_allowed(contract: dict[str, object]) -> bool:
    return bool(contract.get("primary_flat_cluster_target", False)) and bool(
        contract.get("current_visible_surface_flat_exact_claim_allowed", True)
    )


def target_contract_recovery_passed(
    *,
    contract: dict[str, object],
    exact_passed: bool,
    location_strength_passed: bool,
) -> bool:
    if flat_exact_claim_allowed(contract):
        return bool(exact_passed)
    return bool(location_strength_passed)


def claimable_exact_metrics(exact_metrics: dict[str, object]) -> dict[str, object]:
    per_label = (
        dict(exact_metrics.get("per_label_recall_after_label_matching", {}))
        if isinstance(exact_metrics.get("per_label_recall_after_label_matching", {}), dict)
        else {}
    )
    filtered = {
        label: dict(per_label[label])
        for label in CURRENT_VISIBLE_SURFACE_FLAT_EXACT_CLAIM_TARGET_IDS
        if label in per_label and isinstance(per_label.get(label, {}), dict)
    }
    recalls = [float(row.get("recall_after_label_matching", 0.0) or 0.0) for row in filtered.values()]
    if not recalls:
        return {
            "schema": "scope_static_stage5b1_claimable_exact_metrics_v1",
            "claimable_flat_exact_target_ids": list(CURRENT_VISIBLE_SURFACE_FLAT_EXACT_CLAIM_TARGET_IDS),
            "balanced_accuracy_after_label_matching": None,
            "min_recall_after_label_matching": None,
            "per_label_recall_after_label_matching": {},
        }
    return {
        "schema": "scope_static_stage5b1_claimable_exact_metrics_v1",
        "description": "Exact assignment metrics restricted to flat targets whose current visible surface permits flat-exact scientific claims.",
        "claimable_flat_exact_target_ids": list(CURRENT_VISIBLE_SURFACE_FLAT_EXACT_CLAIM_TARGET_IDS),
        "balanced_accuracy_after_label_matching": float(np.mean(recalls)),
        "min_recall_after_label_matching": float(np.min(recalls)),
        "per_label_recall_after_label_matching": filtered,
    }


def claimable_recall_mapping(values: dict[str, object]) -> dict[str, float]:
    recalls: dict[str, float] = {}
    for label, payload in dict(values).items():
        label_text = str(label)
        if label_text not in set(CURRENT_VISIBLE_SURFACE_FLAT_EXACT_CLAIM_TARGET_IDS):
            continue
        if isinstance(payload, dict):
            recalls[label_text] = float(payload.get("self_recall", payload.get("recall_after_label_matching", 0.0)) or 0.0)
        else:
            recalls[label_text] = float(payload)
    return recalls


def stage3d4b_claim_gate_audit(metrics: dict[str, object] | None) -> dict[str, object]:
    if not isinstance(metrics, dict):
        return {
            "schema": "scope_static_stage3d4b_claimable_gate_audit_v1",
            "present": False,
            "passed": False,
        }
    postmerge = dict(metrics.get("postmerge_metrics", {})) if isinstance(metrics.get("postmerge_metrics", {}), dict) else {}
    legacy_acceptance_passed = artifact_acceptance_passed(metrics)
    if not postmerge and legacy_acceptance_passed:
        return {
            "schema": "scope_static_stage3d4b_claimable_gate_audit_v1",
            "description": "D4b claim gate passed by legacy all-exact acceptance, which is stricter than the current claimable-flat subset.",
            "present": True,
            "legacy_acceptance_passed": True,
            "compatibility_fallback": "legacy_all_exact_acceptance",
            "claimable_flat_exact_target_ids": list(CURRENT_VISIBLE_SURFACE_FLAT_EXACT_CLAIM_TARGET_IDS),
            "observed": {
                "claimable_exact_balanced_accuracy": None,
                "claimable_exact_min_recall": None,
                "per_label_recall_after_label_matching": {},
            },
            "checks": {"legacy_all_exact_acceptance_passed": True},
            "passed": True,
        }
    exact = dict(postmerge.get("postmerge_exact_metrics", {})) if isinstance(postmerge.get("postmerge_exact_metrics", {}), dict) else {}
    claimable = claimable_exact_metrics(exact)
    ba = optional_float(claimable.get("balanced_accuracy_after_label_matching"))
    min_recall = optional_float(claimable.get("min_recall_after_label_matching"))
    rows = (
        dict(claimable.get("per_label_recall_after_label_matching", {}))
        if isinstance(claimable.get("per_label_recall_after_label_matching", {}), dict)
        else {}
    )
    checks = {
        "postmerge_metrics_reported": bool(postmerge),
        "claimable_flat_exact_targets_present": len(rows) == len(CURRENT_VISIBLE_SURFACE_FLAT_EXACT_CLAIM_TARGET_IDS),
        "claimable_exact_balanced_accuracy_is_one": is_one(ba, atol=1.0e-9),
        "claimable_exact_min_recall_is_one": is_one(min_recall, atol=1.0e-9),
    }
    return {
        "schema": "scope_static_stage3d4b_claimable_gate_audit_v1",
        "description": "D4b claim gate restricted to flat exact targets whose current visible surface permits flat-exact claims.",
        "present": True,
        "claimable_flat_exact_target_ids": list(CURRENT_VISIBLE_SURFACE_FLAT_EXACT_CLAIM_TARGET_IDS),
        "observed": {
            "claimable_exact_balanced_accuracy": ba,
            "claimable_exact_min_recall": min_recall,
            "per_label_recall_after_label_matching": rows,
        },
        "legacy_acceptance_passed": legacy_acceptance_passed,
        "checks": checks,
        "passed": bool(all(checks.values())),
    }


def stage3d4b_claim_gate_passed(metrics: dict[str, object] | None) -> bool:
    return bool(stage3d4b_claim_gate_audit(metrics).get("passed", False))


def postmerge_assignment_gate(
    assignment_path: Path,
    *,
    min_exact_ba: float,
    min_exact_min_recall: float,
) -> dict[str, object]:
    metrics_path = assignment_path.parent / "metrics.json"
    if not metrics_path.exists():
        return {
            "schema": "scope_static_stage5b1_postmerge_assignment_gate_v1",
            "metrics_path": str(metrics_path),
            "stage3d4b_acceptance_present": False,
            "stage3d4b_acceptance_passed": False,
        }
    try:
        metrics = json.loads(metrics_path.read_text())
    except json.JSONDecodeError:
        return {
            "schema": "scope_static_stage5b1_postmerge_assignment_gate_v1",
            "metrics_path": str(metrics_path),
            "stage3d4b_acceptance_present": True,
            "stage3d4b_acceptance_passed": False,
            "failure_kind": "invalid_stage3d4b_metrics_json",
        }
    acceptance = dict(metrics.get("acceptance_audit", {})) if isinstance(metrics.get("acceptance_audit", {}), dict) else {}
    postmerge = dict(metrics.get("postmerge_metrics", {})) if isinstance(metrics.get("postmerge_metrics", {}), dict) else {}
    exact = dict(postmerge.get("postmerge_exact_metrics", {})) if isinstance(postmerge.get("postmerge_exact_metrics", {}), dict) else {}
    claimable_exact = claimable_exact_metrics(exact)
    per_label = (
        dict(exact.get("per_label_recall_after_label_matching", {}))
        if isinstance(exact.get("per_label_recall_after_label_matching", {}), dict)
        else {}
    )
    targeted_recalls = {
        label: float(dict(per_label.get(label, {})).get("recall_after_label_matching", 0.0) or 0.0)
        for label in ("M6", "M13", "M18", "M27")
        if isinstance(per_label.get(label, {}), dict)
    }
    acceptance_passed = bool(acceptance.get("passed", False))
    claimable_ba = optional_float(claimable_exact.get("balanced_accuracy_after_label_matching"))
    claimable_min_recall = optional_float(claimable_exact.get("min_recall_after_label_matching"))
    claimable_acceptance_passed = bool(
        acceptance_passed
        if not postmerge
        else claimable_ba is not None
        and claimable_min_recall is not None
        and claimable_ba >= float(min_exact_ba)
        and claimable_min_recall >= float(min_exact_min_recall)
    )
    return {
        "schema": "scope_static_stage5b1_postmerge_assignment_gate_v1",
        "metrics_path": str(metrics_path),
        "stage3d4b_acceptance_present": True,
        "stage3d4b_acceptance_passed": acceptance_passed,
        "stage3d4b_claimable_acceptance_passed": claimable_acceptance_passed,
        "stage3d4b_decision": metrics.get("decision"),
        "postmerge_metrics_reported": bool(postmerge),
        "postmerge_exact_balanced_accuracy": optional_float(exact.get("balanced_accuracy_after_label_matching")),
        "postmerge_exact_min_recall": optional_float(exact.get("min_recall_after_label_matching")),
        "postmerge_claimable_exact_balanced_accuracy": claimable_ba,
        "postmerge_claimable_exact_min_recall": claimable_min_recall,
        "claimable_gate_compatibility_fallback": "legacy_all_exact_acceptance" if acceptance_passed and not postmerge else None,
        "claimable_flat_exact_target_ids": list(CURRENT_VISIBLE_SURFACE_FLAT_EXACT_CLAIM_TARGET_IDS),
        "postmerge_targeted_self_recall_by_label": targeted_recalls,
    }


def artifact_acceptance_passed(metrics: dict[str, object] | None) -> bool:
    if not isinstance(metrics, dict):
        return False
    acceptance = metrics.get("acceptance_audit", {})
    if not isinstance(acceptance, dict):
        return False
    return bool(acceptance.get("passed", False))
