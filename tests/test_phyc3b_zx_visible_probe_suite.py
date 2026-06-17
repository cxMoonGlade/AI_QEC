from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from scope_static.primitives.mechanism_catalog import MECHANISM_NAMES
from scope_static.learner import (
    ALIAS_PAIRS,
    audit_m34_implementation,
    build_zx_visible_feature_table,
    build_zx_visible_probe_schedule,
    run_phyc3b_zx_visible_alias_breaking_probe_suite,
)


def test_phyc3b_probe_schedule_is_zx_only_and_has_required_preparations() -> None:
    schedule = build_zx_visible_probe_schedule()

    assert {probe["prepare"] for probe in schedule if probe["qubit_count"] == 1} == {"|0>", "|1>", "|+>"}
    assert {probe["prepare"] for probe in schedule if probe["qubit_count"] == 2} == {"|00>", "|01>", "|10>", "|++>"}
    assert {probe["measurement_basis"] for probe in schedule if probe["qubit_count"] == 2} == {"ZZ", "ZX", "XZ", "XX"}
    assert all("Y" not in str(probe["prepare"]) for probe in schedule)
    assert all("Y" not in str(probe["measurement_basis"]) for probe in schedule)
    assert all(set(probe["measurement_axes"]) <= {"Z", "X"} for probe in schedule)


def test_phyc3b_feature_schema_contains_raw_observations_and_no_forbidden_feature_fields() -> None:
    table = build_zx_visible_feature_table([_record("M8", 0), _record("M30", 0)], shots=1000)
    names = [feature["name"] for feature in table.feature_schema["features"]]
    forbidden = ("oracle", "mechanism", "teacher", "channel", "kraus", "ptm", "prototype", "omega", "family", "label")

    assert any(name.endswith("__E_Z") for name in names)
    assert any(name.endswith("__E_X") for name in names)
    assert "raw__two__prep_00__r_1__meas_ZZ__P00" in names
    assert "raw__two__prep_00__r_1__meas_ZZ__P11" in names
    assert "derived__computational_subspace_survival_proxy" in names
    assert "visible_metadata__instruction_rzz" in names
    assert "visible_metadata__operation_id" not in names
    assert not any(token in name.lower() for token in forbidden for name in names)


def test_phyc3b_ceiling_audit_runs_before_learner_training_and_writes_artifacts(tmp_path: Path) -> None:
    teacher = tmp_path / "S2D_PHYC1_teacher"
    teacher.mkdir()
    records = []
    for group in range(2):
        records.extend([_record(label, group) for pair in ALIAS_PAIRS[:3] for label in pair])
    (teacher / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}))
    output = tmp_path / "PHYC3b"

    result = run_phyc3b_zx_visible_alias_breaking_probe_suite(teacher_dir=teacher, output_dir=output, shots=1000, seed=0)

    assert result["execution_order"].index("visible_ceiling_before") < result["execution_order"].index("learner_training")
    assert result["ceiling_audit_precedes_learner_training"] is True
    for name in [
        "metrics.json",
        "summary.md",
        "feature_schema_zx_visible.json",
        "probe_schedule_zx_visible.json",
        "visible_signature_conflicts_before.json",
        "visible_signature_conflicts_after.json",
        "deterministic_ceiling_metrics_before.json",
        "deterministic_ceiling_metrics_after.json",
        "alias_pair_confusion_after.json",
        "quotient_alias_classes_after.json",
        "leakage_guardrail_audit.json",
        "learner_metrics.json",
        "learner_confusion_matrix.json",
        "incompatible_predictions.json",
        "m34_implementation_audit.json",
    ]:
        assert (output / name).exists()


def test_phyc3b_m34_audit_identifies_current_cptp_surrogate() -> None:
    table = build_zx_visible_feature_table([_record("M15", 0), _record("M34", 0)], shots=1000)
    audit = audit_m34_implementation([_record("M34", 0)], table=table)

    assert audit["schema"] == "scope_static_phyc3b_m34_implementation_audit_v1"
    assert audit["implementation_class"] == "B_CPTP_computational_subspace_surrogate"
    assert audit["p_comp_m15_m34_separator_claim_allowed"] is False


def test_phyc3b_alias_support_patterns_are_visible_under_zx_probes() -> None:
    records = [_record(label, 0) for pair in ALIAS_PAIRS for label in pair]
    table = build_zx_visible_feature_table(records, shots=1000)
    means = {label: _mean_map(table, label) for label in {record["oracle_label"] for record in records}}

    assert means["M30"]["raw__two__prep_00__r_1__meas_ZZ__P01"] > means["M8"]["raw__two__prep_00__r_1__meas_ZZ__P01"]
    assert means["M10"]["raw__two__prep_00__r_1__meas_ZZ__P11"] > means["M32"]["raw__two__prep_00__r_1__meas_ZZ__P11"]
    assert means["M32"]["raw__two__prep_00__r_1__meas_ZZ__P10"] > means["M10"]["raw__two__prep_00__r_1__meas_ZZ__P10"]
    assert means["M33"]["raw__two__prep_00__r_1__meas_ZZ__P11"] > means["M12"]["raw__two__prep_00__r_1__meas_ZZ__P11"]
    assert means["M24"]["derived__single_non_unitality_proxy"] > means["M0"]["derived__single_non_unitality_proxy"]
    assert means["M4"]["derived__single_prep_1_z_relaxation_proxy"] > means["M27"]["derived__single_prep_1_z_relaxation_proxy"]


def test_m13_drift_overlay_has_row_level_visible_geometry_beyond_m6_rx_strength() -> None:
    records = [
        _record(
            "M6",
            0,
            parameters={"epsilon": 0.035},
            instruction="rx",
        ),
        _record(
            "M13",
            0,
            parameters={"operation_axis": "rx", "epsilon": 0.035, "epsilon_mean": 0.035, "epsilon_span": 0.018},
            instruction="rx",
        ),
    ]

    table = build_zx_visible_feature_table(records, shots=1000)
    distance = float(np.linalg.norm(table.expected_features[0] - table.expected_features[1]))
    forbidden = ("oracle", "mechanism", "teacher", "channel", "kraus", "ptm", "prototype", "omega", "family", "label")

    assert distance > 1.0e-4
    assert not any(token in name.lower() for token in forbidden for name in table.feature_names)


def test_m22_m23_axis_quadrature_proxy_is_visible_under_zx_probes() -> None:
    records = [
        _record("M22", 0, parameters={"epsilon": 0.022}, instruction="rzz"),
        _record("M23", 0, parameters={"epsilon": 0.019}, instruction="rzz"),
    ]

    table = build_zx_visible_feature_table(records, shots=1000)
    means = {label: _mean_map(table, label) for label in ("M22", "M23")}
    forbidden = ("oracle", "mechanism", "teacher", "channel", "kraus", "ptm", "prototype", "omega", "family", "label")
    feature = "derived__two_axis_quadrature_plus_xx_pair_transfer_proxy"

    assert feature in table.feature_names
    assert abs(means["M23"][feature] - means["M22"][feature]) > 1.0e-4
    assert means["M22"]["derived__two_axis_quadrature_plus_any_transfer_flag"] == 0.0
    assert means["M23"]["derived__two_axis_quadrature_plus_any_transfer_flag"] == 1.0
    assert means["M23"]["derived__two_axis_quadrature_plus_support_pattern"] > means["M22"][
        "derived__two_axis_quadrature_plus_support_pattern"
    ]
    assert means["M23"]["derived__two_axis_quadrature_plus_zx_xz_single_axis_loss_proxy"] > means["M22"][
        "derived__two_axis_quadrature_plus_zx_xz_single_axis_loss_proxy"
    ]
    assert not any(token in name.lower() for token in forbidden for name in table.feature_names)


def _record(
    label: str,
    group: int,
    *,
    parameters: dict[str, object] | None = None,
    instruction: str | None = None,
) -> dict[str, object]:
    two_qubit = label in {"M8", "M9", "M10", "M12", "M21", "M22", "M23", "M28", "M29", "M30", "M31", "M32", "M33"}
    return {
        "oracle_label": label,
        "mechanism_id": label,
        "name": MECHANISM_NAMES[label],
        "num_qubits": 2 if two_qubit else 1,
        "parameters": dict(parameters or {}),
        "instruction": instruction if instruction is not None else ("rzz" if two_qubit else "id"),
        "qubits": [0, 1] if two_qubit else [0],
        "circuit_id": int(group),
        "location_id": int(group),
        "probe_indices": [],
    }


def _mean_map(table: object, label: str) -> dict[str, float]:
    rows = [idx for idx, current in enumerate(table.labels) if current == label]
    assert rows
    values = table.expected_features[rows].mean(axis=0)
    return {name: float(values[idx]) for idx, name in enumerate(table.feature_names)}
