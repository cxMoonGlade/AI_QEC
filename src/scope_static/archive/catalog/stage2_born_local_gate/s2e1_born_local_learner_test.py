from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from scope_static.primitives.born_local import BORN_LOCAL_SUPPORTED_MECHANISMS
from scope_static.primitives.mechanism_catalog import IMPLEMENTED_MECHANISM_IDS


S2E1_REQUIRED_MECHANISMS = tuple(BORN_LOCAL_SUPPORTED_MECHANISMS)
S2E1_NON_BORN_ALLM_CONTROL_MECHANISMS = tuple(IMPLEMENTED_MECHANISM_IDS)


def run_s2e1_born_local_learner_test(
    *,
    teacher_dir: str | Path,
    phyc2_dir: str | Path,
    output_dir: str | Path,
    contract_variant: str = "balanced",
    require_full_scope: bool = True,
    expected_response_model: str = "born_local",
) -> dict[str, object]:
    """S2E.1 learner gate using an existing PHYC2 metrics artifact.

    The audit intentionally does not regenerate PHYC2. It checks whether an
    already-materialized PHYC2 learner result is valid evidence for the
    Stage 2E.1 Born-local task.
    """

    teacher = Path(teacher_dir)
    phyc2 = Path(phyc2_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    teacher_summary = _read_json_optional(teacher / "summary.json")
    teacher_config = _read_json_optional(teacher / "teacher_config.json")
    sampling_audit = _read_json_optional(teacher / "sampling_audit.json")
    phyc2_metrics = _read_json_required(phyc2 / "metrics.json")

    response_model = _first_string(
        teacher_summary.get("local_observable_response_model"),
        teacher_config.get("local_observable_response_model"),
        sampling_audit.get("local_observable_response_model"),
    )
    class_names = _class_names(phyc2_metrics)
    expected_model = _normalize_response_model(expected_response_model)
    scope = _scope_audit(
        class_names,
        require_full_scope=bool(require_full_scope),
        expected_response_model=expected_model,
    )
    sampling = _sampling_gate_audit(sampling_audit)
    expected_variant = _normalize_contract_variant(contract_variant)
    actual_variant = _normalize_contract_variant(str(phyc2_metrics.get("contract_variant", expected_variant)))

    gates = [
        _gate("existing_phyc2_metrics_present", bool(phyc2_metrics), f"read {phyc2 / 'metrics.json'}"),
        _gate(
            "phyc2_teacher_dir_matches",
            _teacher_dir_matches(phyc2_metrics.get("teacher_dir"), teacher),
            "PHYC2 metrics point at the teacher artifact under test",
        ),
        _gate(
            "phyc2_contract_variant",
            actual_variant == expected_variant,
            f"expected {expected_variant}, got {actual_variant}",
        ),
        _gate("phyc2_contract_passed", bool(phyc2_metrics.get("contract_passed")), "existing PHYC2 learner contract passed"),
        _gate(
            "phyc2_coverage_evaluable",
            bool(dict(phyc2_metrics.get("coverage", {})).get("contract_evaluable", False)),
            "existing PHYC2 coverage was grouped-fold evaluable",
        ),
        _gate(
            "source_artifact_matches_expected_model",
            response_model == expected_model,
            f"expected {expected_model!r}, got local_observable_response_model={response_model!r}",
        ),
        *_sampling_gates_for_model(sampling, expected_response_model=expected_model),
        _gate(
            "full_s2e1_mechanism_scope",
            bool(scope["passed"]),
            _scope_reason(scope),
        ),
    ]
    passed = all(bool(item["passed"]) for item in gates)
    result = {
        "schema": "scope_static_s2e1_born_local_learner_test_v1",
        "stage": "S2E.1_PHYC2_Born_local_learner_test",
        "question": "Are existing PHYC2 sampled observations valid learner evidence for the Stage 2E.1 Born-local task?",
        "teacher_dir": str(teacher),
        "phyc2_dir": str(phyc2),
        "output_dir": str(output),
        "data_reuse": {
            "source": "existing_PHYC2_metrics_json",
            "reran_phyc2": False,
            "reran_teacher": False,
        },
        "contract_variant": expected_variant,
        "require_full_scope": bool(require_full_scope),
        "expected_response_model": expected_model,
        "evidence_role": "born_local_stage2e_gate" if expected_model == "born_local" else "non_born_existing_phyc2_control",
        "source_artifact": {
            "local_observable_response_model": response_model,
            "teacher_summary_present": bool(teacher_summary),
            "teacher_config_present": bool(teacher_config),
            "sampling_audit_present": bool(sampling_audit),
        },
        "mechanism_scope": scope,
        "sampling_gate": sampling,
        "phyc2_metrics": {
            "contract_passed": bool(phyc2_metrics.get("contract_passed")),
            "decision": phyc2_metrics.get("decision"),
            "balanced_accuracy": float(phyc2_metrics.get("balanced_accuracy", 0.0)),
            "min_class_recall": float(phyc2_metrics.get("min_class_recall", 0.0)),
            "prevalence_weighted_accuracy": float(phyc2_metrics.get("prevalence_weighted_accuracy", 0.0)),
            "rare_class_recall_min": float(phyc2_metrics.get("rare_class_recall_min", 0.0)),
            "real_minus_within_branch_scrambled_balanced_accuracy": float(
                phyc2_metrics.get("real_minus_within_branch_scrambled_balanced_accuracy", 0.0)
            ),
        },
        "gates": gates,
        "contract_passed": bool(passed),
        "decision": "s2e1_born_local_learner_test_passed" if passed else "s2e1_born_local_learner_test_failed",
    }
    _write_outputs(output, result)
    return result


def format_s2e1_born_local_learner_test_summary(result: dict[str, object]) -> str:
    lines = [
        "# S2E.1 Born-Local Learner Test",
        "",
        f"- Decision: `{result.get('decision')}`",
        f"- Contract passed: `{str(bool(result.get('contract_passed'))).lower()}`",
        f"- Teacher: `{result.get('teacher_dir')}`",
        f"- Existing PHYC2: `{result.get('phyc2_dir')}`",
        f"- Reran PHYC2: `{str(bool(dict(result.get('data_reuse', {})).get('reran_phyc2', False))).lower()}`",
        "",
        "| gate | passed | detail |",
        "| --- | --- | --- |",
    ]
    for gate in result.get("gates", []):
        if not isinstance(gate, dict):
            continue
        lines.append(f"| {gate.get('name')} | {str(bool(gate.get('passed'))).lower()} | {gate.get('detail')} |")
    lines.append("")
    return "\n".join(lines)


def _scope_audit(
    class_names: Iterable[str],
    *,
    require_full_scope: bool,
    expected_response_model: str,
) -> dict[str, object]:
    observed = sorted({str(name) for name in class_names if str(name)}, key=_mechanism_sort_key)
    required = list(_required_mechanisms(expected_response_model))
    missing = [name for name in required if name not in set(observed)]
    unsupported = [name for name in observed if name not in set(required)]
    passed = not unsupported and (not require_full_scope or not missing)
    return {
        "required_mechanisms": required,
        "observed_mechanisms": observed,
        "missing_required_mechanisms": missing,
        "unsupported_mechanisms_present": unsupported,
        "num_required": int(len(required)),
        "num_observed": int(len(observed)),
        "require_full_scope": bool(require_full_scope),
        "passed": bool(passed),
    }


def _required_mechanisms(expected_response_model: str) -> tuple[str, ...]:
    if _normalize_response_model(expected_response_model) == "born_local":
        return S2E1_REQUIRED_MECHANISMS
    return S2E1_NON_BORN_ALLM_CONTROL_MECHANISMS


def _scope_reason(scope: dict[str, object]) -> str:
    missing = list(scope.get("missing_required_mechanisms", []))
    unsupported = list(scope.get("unsupported_mechanisms_present", []))
    if unsupported:
        return f"unsupported mechanisms present: {unsupported}"
    if bool(scope.get("require_full_scope", False)) and missing:
        return f"missing required mechanisms: {missing}"
    return "observed mechanisms match the requested S2E.1 Born-local scope"


def _sampling_gate_audit(sampling_audit: dict[str, object]) -> dict[str, object]:
    overlay = sampling_audit.get("pair_correlation_overlay", {})
    if not isinstance(overlay, dict):
        overlay = {}
    joint = sampling_audit.get("born_local_joint_sampling", {})
    if not isinstance(joint, dict):
        joint = {}
    overlay_disabled = bool(overlay) and not bool(overlay.get("enabled", True))
    return {
        "pair_correlation_overlay_disabled": bool(overlay_disabled),
        "pair_correlation_overlay_reason": overlay.get("reason", "pair_correlation_overlay audit missing"),
        "born_local_joint_sampling_enabled": bool(joint.get("enabled", False)),
        "born_local_joint_sampling_num_entries": int(joint.get("num_entries", 0) or 0),
    }


def _sampling_gates_for_model(sampling: dict[str, object], *, expected_response_model: str) -> list[dict[str, object]]:
    if _normalize_response_model(expected_response_model) != "born_local":
        return [
            _gate(
                "non_born_sampling_path_allowed",
                True,
                "non-Born existing-PHYC2 control does not require Born-local joint POVM sampling",
            )
        ]
    return [
        _gate(
            "no_pair_correlation_overlay",
            bool(sampling["pair_correlation_overlay_disabled"]),
            str(sampling["pair_correlation_overlay_reason"]),
        ),
        _gate(
            "born_local_joint_sampling_path",
            bool(sampling["born_local_joint_sampling_enabled"]),
            "sampling audit reports Born-local joint POVM sampling path",
        ),
    ]


def _class_names(phyc2_metrics: dict[str, object]) -> list[str]:
    names = phyc2_metrics.get("class_names")
    if isinstance(names, list) and names:
        return [str(name) for name in names]
    coverage = phyc2_metrics.get("coverage", {})
    if isinstance(coverage, dict) and isinstance(coverage.get("class_support"), dict):
        return [str(name) for name in coverage["class_support"]]
    return []


def _teacher_dir_matches(recorded: object, teacher: Path) -> bool:
    if recorded in (None, ""):
        return False
    recorded_path = Path(str(recorded))
    try:
        return recorded_path.resolve() == teacher.resolve()
    except FileNotFoundError:
        return recorded_path == teacher


def _first_string(*values: object) -> str | None:
    for value in values:
        if value is not None and str(value):
            return str(value)
    return None


def _gate(name: str, passed: bool, detail: str) -> dict[str, object]:
    return {"name": str(name), "passed": bool(passed), "detail": str(detail)}


def _read_json_required(path: Path) -> dict[str, object]:
    return json.loads(path.read_text())


def _read_json_optional(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    return data if isinstance(data, dict) else {}


def _normalize_contract_variant(value: str) -> str:
    text = str(value).strip().lower().replace("-", "_")
    aliases = {
        "": "balanced",
        "balanced": "balanced",
        "phyc2_balanced": "balanced",
        "weighted": "weighted",
        "schedule_weighted": "weighted",
        "phyc2_weighted": "weighted",
    }
    if text not in aliases:
        raise ValueError("contract_variant must be 'balanced' or 'weighted'")
    return aliases[text]


def _normalize_response_model(value: str) -> str:
    text = str(value).strip().lower().replace("-", "_")
    aliases = {
        "": "born_local",
        "born": "born_local",
        "born_local": "born_local",
        "phyc2_born_local": "born_local",
        "separability_v2": "separability_v2",
        "non_born": "separability_v2",
        "non_born_control": "separability_v2",
    }
    return aliases.get(text, text)


def _write_outputs(output: Path, result: dict[str, object]) -> None:
    (output / "metrics.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (output / "summary.md").write_text(format_s2e1_born_local_learner_test_summary(result))


def _mechanism_sort_key(name: str) -> tuple[int, str]:
    if str(name).startswith("M") and str(name)[1:].isdigit():
        return (int(str(name)[1:]), str(name))
    return (10_000, str(name))
