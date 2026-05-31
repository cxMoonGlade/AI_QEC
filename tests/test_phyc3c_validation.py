from __future__ import annotations

import json
from pathlib import Path

from scope_static.backend.mechanism_catalog import MECHANISM_NAMES
from scope_static.learner import build_batch_protocol, leakage_guardrail_audit_phyc3c
from scope_static.learner import (
    non_leakage_audit,
    protocol_validity_audit,
    run_phyc3c_validation_audit,
)


def test_phyc3c_validation_rejects_single_context_m13_distributional_claim() -> None:
    labels = ["M6", "M13", "M27"] * 6
    groups = [group for group in range(6) for _ in range(3)]
    class_names = ["M6", "M13", "M27"]
    single = build_batch_protocol(labels, groups, class_names, mode="single_realization", batch_size=1)
    multi = build_batch_protocol(labels, groups, class_names, mode="multi_context_batch", batch_size=3)

    audit = protocol_validity_audit(
        labels=labels,
        groups=groups,
        class_names=class_names,
        single_protocol=single,
        multi_protocol=multi,
        required_m13_contexts=3,
    )

    assert audit["single_realization_protocol_valid_for_m13_distributional_claim"] is False
    assert audit["multi_context_protocol_valid_for_m13_distributional_claim"] is True
    assert audit["checks"]["single_realization_rejected_for_distributional_m13_claim"] is True
    assert audit["checks"]["multi_train_test_groups_disjoint"] is True


def test_phyc3c_validation_guardrail_rejects_forbidden_feature_names() -> None:
    audit = leakage_guardrail_audit_phyc3c(["raw__single__prep_0__r_1__meas_Z__P0", "oracle_mechanism_id"])

    assert audit["passed"] is False
    assert audit["checks"]["phyc3c_oracle_absent_from_feature_names"] is False
    assert audit["checks"]["phyc3c_mechanism_absent_from_feature_names"] is False


def test_phyc3c_non_leakage_audit_has_negative_injection_control() -> None:
    schema = {
        "features": [
            {
                "name": "raw__single__prep_0__r_1__meas_Z__P0",
                "kind": "raw_sampled_observation",
                "learner_visible": True,
            }
        ]
    }
    labels = ["M6", "M13"] * 3
    groups = [group for group in range(3) for _ in range(2)]

    audit = non_leakage_audit(
        feature_names=["raw__single__prep_0__r_1__meas_Z__P0"],
        feature_schema=schema,
        labels=labels,
        groups=groups,
        class_names=["M6", "M13"],
    )

    assert audit["passed"] is True
    assert audit["checks"]["forbidden_feature_injection_rejected"] is True
    assert audit["forbidden_feature_injection_probe"]["passed"] is False


def test_phyc3c_validation_writes_acceptance_artifacts(tmp_path: Path) -> None:
    teacher = tmp_path / "S2D_PHYC1_teacher"
    teacher.mkdir()
    records = []
    for group in range(6):
        records.append(_record("M6", group, epsilon=0.035))
        records.append(_record("M13", group, epsilon=0.018 + 0.026 * group / 5.0))
        records.append(_record("M27", group, epsilon=0.026))
    (teacher / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}))

    output = tmp_path / "PHYC3c_validation"
    result = run_phyc3c_validation_audit(
        teacher_dir=teacher,
        output_dir=output,
        shots=1000,
        seeds=(3,),
        sampling_modes=("expected",),
        batch_sizes=(2,),
        shrinkage_alphas=(0.25,),
        max_pca_components_values=(2,),
        primary_min_ba=0.0,
        primary_min_nmi=0.0,
        primary_min_m13_recall=0.0,
        required_m13_contexts=2,
    )

    assert result["stage"] == "PHYC3c_robust_non_leaky_protocol_validation"
    assert result["non_leakage_audit"]["passed"] is True
    assert result["protocol_validity_audit"]["passed"] is True
    assert result["invalid_protocol_negative_control"]["passed"] is True
    assert len(result["robustness_grid"]) == 1
    for name in [
        "metrics.json",
        "summary.md",
        "robustness_grid.json",
        "non_leakage_audit.json",
        "protocol_validity_audit.json",
        "invalid_protocol_negative_control.json",
        "head_stability_audit.json",
        "failure_cases.json",
    ]:
        assert (output / name).exists()


def _record(label: str, group: int, *, epsilon: float) -> dict[str, object]:
    params = {"epsilon": float(epsilon)}
    if label == "M13":
        params = {"axis": "rx", "epsilon": float(epsilon), "epsilon_mean": 0.031, "epsilon_span": 0.026}
    return {
        "oracle_label": label,
        "mechanism_id": label,
        "name": MECHANISM_NAMES[label],
        "num_qubits": 1,
        "parameters": params,
        "instruction": "rx" if label in {"M6", "M13"} else "id",
        "qubits": [0],
        "circuit_id": int(group),
        "location_id": int(group),
        "probe_indices": [],
    }
