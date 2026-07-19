from __future__ import annotations

import json
import math
import os
from types import SimpleNamespace

import pytest

try:
    import torch
except Exception as exc:  # pragma: no cover - exercised only in a broken GPU lane.
    pytest.fail(f"Axis-1 schedule bridge tests require torch: {exc}", pytrace=False)

if not torch.cuda.is_available():
    pytest.fail(
        "Axis-1 compiler/schedule tests are GPU-gated; CUDA-MISSING is NOT A RELEASE BASIS",
        pytrace=False,
    )

from error_coupling_simulator.frontend import (  # noqa: E402
    ANALOG_SCHEDULE_REPRESENTABILITY,
    AXIS1_FRONTEND_ONE_QUBIT_CONTROL_GATES,
    AXIS1_FRONTEND_TWO_QUBIT_CONTROL_GATES,
    AXIS1_LOCAL_LINDBLAD_CONTEXT_METADATA_KEY,
    AXIS1_STATIC_ZZ_CALIBRATIONS_METADATA_KEY,
    AXIS1_STATIC_ZZ_COUPLINGS_METADATA_KEY,
    AXIS1_CARRIER_MCWF_MPS_BACKEND_CONTRACT,
    AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT,
    AXIS1_CARRIER_MCWF_MPS_EXECUTION_REPRESENTABILITY,
    AXIS1_CARRIER_QUTIP_RESTRICTED_EXECUTION_BACKEND_CONTRACT,
    AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT,
    AXIS1_MCWF_MPS_EXECUTION_BACKEND_CONTRACT,
    AXIS1_QUTRIT_LEAKAGE_CERTIFICATION_REPRESENTABILITY,
    AXIS1_QUTRIT_LEAKAGE_CERTIFICATION_SCHEMA,
    AXIS1_TWO_SITE_LEAKAGE_HAMILTONIAN_CERTIFICATION_REPRESENTABILITY,
    AXIS1_TWO_SITE_LEAKAGE_HAMILTONIAN_CERTIFICATION_SCHEMA,
    JOINT_CHANNEL_DR_ZZ_BAND,
    JOINT_CHANNEL_GAMMA_1_PER_NS,
    JOINT_CHANNEL_GAMMA_PHI_PER_NS,
    JOINT_CHANNEL_NONZERO_COMMUTATOR_MIN,
    JOINT_CHANNEL_NONZERO_SUPEROP_DISTANCE_MIN,
    JOINT_CHANNEL_ZETA_RAD_PER_NS,
    CircuitBuilder,
    CircuitIR,
    CodeQubit,
    CodeSpec,
    GateOp,
    LogicalObservableSpec,
    PauliTerm,
    StabilizerCheck,
    SubstepSchedule,
    JointChannelComparisonRow,
    Axis1LocalLindbladContextSpec,
    Axis1ReadoutResetInstrumentSpec,
    Axis1StaticZZDeviceSpec,
    Axis1SubstepChannelRow,
    axis1_carrier_execution_manifest,
    axis1_carrier_program_manifest,
    axis1_mcwf_mps_state_record_execution_manifest,
    axis1_qutrit_leakage_oracle_certification_manifest,
    axis1_two_site_leakage_hamiltonian_certification_manifest,
    Tick,
    joint_channel_comparison_gate,
    joint_channel_comparison_manifest,
    axis1_measurement_record_evidence_manifest,
    axis1_qutip_cuquantum_probe_manifest,
    axis1_qutip_cuquantum_record_probe_manifest,
    axis1_qutip_cuquantum_state_probe_manifest,
    axis1_qutip_cuquantum_trajectory_probe_manifest,
    axis1_qt_mps_bond_sweep_manifest,
    axis1_qt_mps_restricted_evidence_bundle_manifest,
    axis1_qt_mps_restricted_execution_manifest,
    axis1_qt_mps_resource_probe_manifest,
    axis1_qt_mps_trajectory_seed_sweep_manifest,
    axis1_state_evolution_evidence_manifest,
    axis1_substep_channel_evidence_manifest,
    build_axis1_schedule_selection_plan,
    build_axis1_joint_channel_selection_plan,
    circuit_ir_to_substep_schedule,
    compile_code_spec_to_substep_schedule,
    freeze_axis1_substep_channel_evidence,
    freeze_joint_channel_comparison_evidence,
    freeze_axis1_measurement_record_evidence,
    freeze_axis1_state_evolution_evidence,
    has_valid_compiler_schedule_seal,
    stim_circuit_to_substep_schedule,
    validate_axis1_substep_channel_freeze,
    validate_joint_channel_comparison_freeze,
    validate_axis1_measurement_record_freeze,
    validate_axis1_state_evolution_freeze,
    write_axis1_measurement_record_evidence,
    write_axis1_measurement_record_samples,
    write_axis1_state_evolution_evidence,
    write_joint_channel_comparison_evidence,
    write_axis1_substep_channel_evidence,
)
from error_coupling_simulator.frontend import b8_io  # noqa: E402
from error_coupling_simulator.carrier.joint_lindbladian import (  # noqa: E402
    SUPEROP_EXACTZERO_TOL,
    assemble_substep_channel,
    composed_vs_joint_infidelity,
)
from error_coupling_simulator.mechanisms.axis1_primitives import (  # noqa: E402
    AXIS1_TWO_QUBIT_LOCAL_REGISTRY_ID,
    Axis1PrimitiveParams,
    default_axis1_primitive_registry,
    lower_two_qubit_axis1_primitives,
)
from error_coupling_simulator.numerics import NUMERICAL_ZERO  # noqa: E402
from error_coupling_simulator.frontend.joint_channel_comparison_runner import (  # noqa: E402
    build_joint_channel_comparison_schedule,
    run_joint_channel_comparison_fixture,
)
from error_coupling_simulator.frontend.axis1_codespec_runner import (  # noqa: E402
    build_axis1_codespec_frontend_schedule,
    build_axis1_codespec_frontend_spec,
    run_axis1_codespec_record_fixture,
)
from error_coupling_simulator.frontend.axis1_channel_evidence import (  # noqa: E402
    _assemble_selection_joint_channel,
)
from error_coupling_simulator.frontend.axis1_ideal_controls import (  # noqa: E402
    lower_ideal_controls_for_selection,
)
from error_coupling_simulator.frontend.axis1_mcwf_mps_execution import (  # noqa: E402
    _hamiltonian_group_gates,
)
from error_coupling_simulator.frontend.axis1_selection import Axis1MechanismSelection  # noqa: E402


@pytest.fixture(autouse=True)
def _touch_cuda_lane():
    marker = torch.empty((), device="cuda")
    assert marker.is_cuda


def test_codespec_compiler_generates_axis1_schedule_metadata_without_truth_payloads():
    spec = _make_mixed_frontend_spec(rounds=2)
    schedule = compile_code_spec_to_substep_schedule(spec)
    manifest = schedule.to_manifest()

    assert schedule.source_kind == "code_spec_compiler"
    assert len(schedule.source_hash) == 64
    assert has_valid_compiler_schedule_seal(schedule)
    assert schedule.schedule_template == "repeated_memory_v1"
    assert schedule.representability == ANALOG_SCHEDULE_REPRESENTABILITY
    assert all(substep.generated_by_compiler for substep in schedule.substeps)
    assert manifest["compiler_provenance"]["seal_present"] is True
    assert manifest["compiler_provenance"]["seal_schema"] == (
        "error_coupling_simulator.frontend.compiler_schedule_seal.v1"
    )
    assert "seal_digest" not in manifest["compiler_provenance"]
    assert {substep.kind for substep in schedule.substeps} >= {
        "reset",
        "one_qubit_gate",
        "two_qubit_gate",
        "measurement",
        "barrier",
    }
    assert manifest["duration_policy"]["table_id"] == (
        "error_coupling_simulator.frontend.duration_policy.v1"
    )
    assert manifest["record_layout_ref"]["measurement_keys"][0] == "round0:x0"
    assert manifest["record_layout_ref"]["detector_names"][0] == "delta:x0:round1"
    assert manifest["qubit_roles"]["0"] == "data"
    assert manifest["qubit_roles"]["3"] == "ancilla"

    assert set(manifest) == {
        "schema_version",
        "source_kind",
        "source_hash",
        "schedule_template",
        "num_qubits",
        "qubit_roles",
        "qubit_coords",
        "static_zz_couplings",
        "static_zz_calibrations",
        "record_layout_ref",
        "duration_policy",
        "representability",
        "visibility",
        "compiler_provenance",
        "substeps",
    }
    payload = json.dumps(manifest, sort_keys=True)
    for forbidden in (
        "kraus",
        "ptm",
        "exact_channel",
        "source_timeline",
    ):
        assert forbidden not in payload.lower()


def test_axis1_static_zz_device_spec_is_public_typed_metadata_only():
    device = Axis1StaticZZDeviceSpec(edges=((1, 0), (2, 3)), num_qubits=5)

    assert device.edges == ((0, 1), (2, 3))
    assert device.to_metadata() == {
        AXIS1_STATIC_ZZ_COUPLINGS_METADATA_KEY: [[0, 1], [2, 3]]
    }
    manifest = device.to_manifest()
    assert manifest["visibility"] == "public_schedule_metadata_no_mechanism_truth"
    assert manifest["representability"] == (
        "axis1_static_zz_device_edges_and_public_calibrations_not_operator_truth"
    )
    assert manifest["calibrations"] == []

    assert set(manifest) == {
        "metadata_key",
        "edges",
        "calibrations",
        "num_qubits",
        "visibility",
        "representability",
    }
    payload = json.dumps(manifest, sort_keys=True)
    for forbidden in (
        "kraus",
        "ptm",
        "exact_channel",
        "source_timeline",
    ):
        assert forbidden not in payload.lower()

    calibrated = Axis1StaticZZDeviceSpec(
        edges=((1, 0), (2, 3)),
        num_qubits=5,
        zeta_rad_per_ns_by_edge={
            (1, 0): 1.25e-3,
            "2-3": {"zeta_rad_per_ns": 2.5e-3, "epistemic_class": "b"},
        },
    )
    assert calibrated.zeta_rad_per_ns_by_edge == {
        (0, 1): {"zeta_rad_per_ns": 1.25e-3, "epistemic_class": "c"},
        (2, 3): {"zeta_rad_per_ns": 2.5e-3, "epistemic_class": "b"},
    }
    assert calibrated.to_metadata() == {
        AXIS1_STATIC_ZZ_COUPLINGS_METADATA_KEY: [[0, 1], [2, 3]],
        AXIS1_STATIC_ZZ_CALIBRATIONS_METADATA_KEY: [
            {
                "edge": [0, 1],
                "zeta_rad_per_ns": 1.25e-3,
                "epistemic_class": "c",
            },
            {
                "edge": [2, 3],
                "zeta_rad_per_ns": 2.5e-3,
                "epistemic_class": "b",
            },
        ],
    }

    with pytest.raises(ValueError, match="duplicate"):
        Axis1StaticZZDeviceSpec(edges=((0, 1), (1, 0)), num_qubits=5)
    with pytest.raises(ValueError, match="duplicate endpoint"):
        Axis1StaticZZDeviceSpec(edges=((2, 2),), num_qubits=5)
    with pytest.raises(ValueError, match="outside"):
        Axis1StaticZZDeviceSpec(edges=((0, 5),), num_qubits=5)
    with pytest.raises(ValueError, match="not declared"):
        Axis1StaticZZDeviceSpec(
            edges=((0, 1),),
            num_qubits=5,
            zeta_rad_per_ns_by_edge={(1, 2): 1.0e-3},
        )
    with pytest.raises(ValueError, match="duplicate edge calibration"):
        Axis1StaticZZDeviceSpec(
            edges=((0, 1),),
            num_qubits=5,
            zeta_rad_per_ns_by_edge=[
                {"edge": [0, 1], "zeta_rad_per_ns": 1.0e-3},
                {"edge": [1, 0], "zeta_rad_per_ns": 2.0e-3},
            ],
        )
    with pytest.raises(ValueError, match="finite and non-negative"):
        Axis1StaticZZDeviceSpec(
            edges=((0, 1),),
            num_qubits=5,
            zeta_rad_per_ns_by_edge={(0, 1): -1.0e-3},
        )
    with pytest.raises(ValueError, match="finite and non-negative"):
        Axis1StaticZZDeviceSpec(
            edges=((0, 1),),
            num_qubits=5,
            zeta_rad_per_ns_by_edge={(0, 1): math.nan},
        )
    with pytest.raises(ValueError, match="epistemic_class"):
        Axis1StaticZZDeviceSpec(
            edges=((0, 1),),
            num_qubits=5,
            zeta_rad_per_ns_by_edge={
                (0, 1): {"zeta_rad_per_ns": 1.0e-3, "epistemic_class": "a"}
            },
        )


def test_axis1_local_lindblad_context_spec_is_public_typed_metadata_only():
    context = Axis1LocalLindbladContextSpec(
        include_thermal_excitation=True,
        gamma_up_per_ns=2.0e-4,
        gamma_phi_per_ns=JOINT_CHANNEL_GAMMA_PHI_PER_NS,
        leak_exchange_12_rad_per_ns=1.5e-3,
        leak_seep_21_per_ns=2.5e-3,
        leak_heat_12_per_ns=3.5e-3,
        leak_exchange_11_02_rad_per_ns=4.5e-3,
        leak_mobility_12_21_rad_per_ns=5.5e-3,
        leak_transport_30_12_rad_per_ns=6.5e-3,
        leak_transport_31_22_rad_per_ns=7.5e-3,
        leak_cond_phase_left2_right_z_rad_per_ns=8.5e-3,
        leak_cond_phase_left_z_right2_rad_per_ns=9.5e-3,
    )

    metadata = context.to_metadata()
    assert set(metadata) == {AXIS1_LOCAL_LINDBLAD_CONTEXT_METADATA_KEY}
    manifest = metadata[AXIS1_LOCAL_LINDBLAD_CONTEXT_METADATA_KEY]
    assert manifest["include_thermal_excitation"] is True
    assert manifest["gamma_up_per_ns"] == 2.0e-4
    assert manifest["include_leakage"] is True
    assert manifest["leak_exchange_12_rad_per_ns"] == 1.5e-3
    assert manifest["leak_seep_21_per_ns"] == 2.5e-3
    assert manifest["leak_heat_12_per_ns"] == 3.5e-3
    assert manifest["leak_exchange_11_02_rad_per_ns"] == 4.5e-3
    assert manifest["leak_mobility_12_21_rad_per_ns"] == 5.5e-3
    assert manifest["leak_transport_30_12_rad_per_ns"] == 6.5e-3
    assert manifest["leak_transport_31_22_rad_per_ns"] == 7.5e-3
    assert manifest["leak_cond_phase_left2_right_z_rad_per_ns"] == 8.5e-3
    assert manifest["leak_cond_phase_left_z_right2_rad_per_ns"] == 9.5e-3
    assert manifest["include_fsim_residual"] is False
    assert manifest["fsim_delta_theta_rad"] == 0.0
    assert manifest["fsim_delta_phi_rad"] == 0.0
    assert manifest["contains_operator_payload"] is False
    assert manifest["contains_serialized_channel_payload"] is False
    assert manifest["representability"] == (
        "public_axis1_lindblad_parameter_metadata_no_operator_matrices_no_source"
    )

    assert set(manifest) == {
        "schema",
        "metadata_key",
        "include_thermal_excitation",
        "gamma_up_per_ns",
        "zeta_rad_per_ns",
        "gamma_phi_per_ns",
        "gamma_1_per_ns",
        "gamma_readout_phi_per_ns",
        "include_fsim_residual",
        "fsim_delta_theta_rad",
        "fsim_delta_phi_rad",
        "include_leakage",
        "leak_exchange_12_rad_per_ns",
        "leak_seep_21_per_ns",
        "leak_heat_12_per_ns",
        "leak_exchange_11_02_rad_per_ns",
        "leak_mobility_12_21_rad_per_ns",
        "leak_transport_30_12_rad_per_ns",
        "leak_transport_31_22_rad_per_ns",
        "leak_cond_phase_left2_right_z_rad_per_ns",
        "leak_cond_phase_left_z_right2_rad_per_ns",
        "contains_operator_payload",
        "contains_serialized_channel_payload",
        "visibility",
        "representability",
        "epistemic_class",
        "epistemic_classes",
    }
    assert set(manifest["epistemic_classes"]) == {
        "sigma_plus_collapse_form",
        "fsim_residual_hamiltonian_form",
        "rate_values",
        "thermal_excitation_selection",
        "fsim_residual_angles",
        "leak_exchange_12_rad_per_ns",
        "leak_seep_21_per_ns",
        "leak_heat_12_per_ns",
        "leak_exchange_11_02_rad_per_ns",
        "leak_mobility_12_21_rad_per_ns",
        "leak_transport_30_12_rad_per_ns",
        "leak_transport_31_22_rad_per_ns",
        "leak_cond_phase_left2_right_z_rad_per_ns",
        "leak_cond_phase_left_z_right2_rad_per_ns",
        "leakage_selection",
    }
    payload = json.dumps(manifest, sort_keys=True)
    for forbidden in (
        "kraus",
        "ptm",
        "exact_channel",
        "source_timeline",
    ):
        assert forbidden not in payload.lower()

    assert Axis1LocalLindbladContextSpec().to_metadata() == {}
    with pytest.raises(ValueError, match="gamma_up_per_ns"):
        Axis1LocalLindbladContextSpec(
            include_thermal_excitation=True,
            gamma_up_per_ns=0.0,
        )
    with pytest.raises(ValueError, match="finite and non-negative"):
        Axis1LocalLindbladContextSpec(gamma_up_per_ns=-1.0)
    with pytest.raises(ValueError, match="finite and non-negative"):
        Axis1LocalLindbladContextSpec(leak_seep_21_per_ns=-1.0)
    with pytest.raises(ValueError, match="finite and non-negative"):
        Axis1LocalLindbladContextSpec(leak_exchange_12_rad_per_ns=float("nan"))
    with pytest.raises(ValueError, match="finite and non-negative"):
        Axis1LocalLindbladContextSpec(leak_exchange_11_02_rad_per_ns=-1.0)
    with pytest.raises(ValueError, match="finite and non-negative"):
        Axis1LocalLindbladContextSpec(leak_cond_phase_left2_right_z_rad_per_ns=-1.0)
    with pytest.raises(ValueError, match="nonzero fSim residual angle"):
        Axis1LocalLindbladContextSpec(include_fsim_residual=True)
    with pytest.raises(ValueError, match="fsim_delta_theta_rad must be finite"):
        Axis1LocalLindbladContextSpec(fsim_delta_theta_rad=float("nan"))


def test_public_axis1_fsim_context_selects_two_qubit_residual_from_schedule():
    theta = 1.2e-2
    phi = -7.0e-3
    builder = CircuitBuilder(num_qubits=3)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            include_fsim_residual=True,
            fsim_delta_theta_rad=theta,
            fsim_delta_phi_rad=phi,
        )
    )
    builder.gate("ISWAP", (0, 1))
    builder.measure((0, 1, 2), key=("m0", "m1", "m2"), duration_ns=250.0)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    assert schedule.axis1_local_lindblad_context["include_fsim_residual"] is True
    assert schedule.axis1_local_lindblad_context["fsim_delta_theta_rad"] == theta
    assert schedule.axis1_local_lindblad_context["fsim_delta_phi_rad"] == phi

    plan = build_axis1_schedule_selection_plan(schedule)
    twoq = next(selection for selection in plan.selections if selection.substep_kind == "two_qubit_gate")
    readout = next(selection for selection in plan.selections if selection.substep_kind == "measurement")
    assert twoq.row_kind == "two_qubit_control_cluster_joint_channel"
    assert twoq.primitive_names[-2:] == ("FSIM_SWAP", "FSIM_PHASE")
    assert twoq.context_mechanisms[-2:] == ("FSIM_SWAP", "FSIM_PHASE")
    assert "FSIM_SWAP" not in readout.primitive_names
    assert "FSIM_PHASE" not in readout.primitive_names

    channel = axis1_substep_channel_evidence_manifest(schedule)
    assert channel["axis1_local_lindblad_context"]["include_fsim_residual"] is True
    twoq_row = next(row for row in channel["rows"] if row["substep_kind"] == "two_qubit_gate")
    readout_row = next(row for row in channel["rows"] if row["substep_kind"] == "measurement")
    assert twoq_row["row_kind"] == "two_qubit_control_cluster_joint_channel"
    assert twoq_row["joint_channel"]["dimension"] == 8
    assert twoq_row["ideal_controls"][0]["name"] == "CTRL_ISWAP"
    fsim_records = [
        record
        for record in twoq_row["lowered_mechanisms"]
        if record["name"] in {"FSIM_SWAP", "FSIM_PHASE"}
    ]
    assert [
        (record["name"], record["generator_kind"], record["support"], record["coefficient"])
        for record in fsim_records
    ] == [
        ("FSIM_SWAP", "hamiltonian", [0, 1], pytest.approx(theta / 30.0)),
        ("FSIM_PHASE", "hamiltonian", [0, 1], pytest.approx(phi / 30.0)),
    ]
    assert "FSIM_SWAP" not in readout_row["primitive_names"]
    assert "FSIM_PHASE" not in readout_row["primitive_names"]


def test_codespec_static_zz_metadata_reaches_axis1_schedule_and_channel_evidence():
    spec = _make_mixed_frontend_spec(
        rounds=2,
        metadata=Axis1StaticZZDeviceSpec(edges=((0, 1),), num_qubits=5).to_metadata(),
    )
    schedule = compile_code_spec_to_substep_schedule(spec)

    assert schedule.source_kind == "code_spec_compiler"
    assert schedule.static_zz_couplings == ((0, 1),)
    assert schedule.to_manifest()["static_zz_couplings"] == [[0, 1]]

    plan = build_axis1_schedule_selection_plan(schedule)
    assert plan.static_zz_pairs == ((0, 1),)
    assert any(
        selection.row_kind == "one_qubit_drive_zz_cluster_joint_channel"
        and selection.coupling_edges == ((0, 1),)
        for selection in plan.selections
    )

    channel = axis1_substep_channel_evidence_manifest(schedule)
    assert channel["source_kind"] == "code_spec_compiler"
    static_rows = [
        row
        for row in channel["rows"]
        if row["row_kind"] == "one_qubit_drive_zz_cluster_joint_channel"
        and row["coupling_edges"] == [[0, 1]]
    ]
    assert static_rows
    assert static_rows[0]["source_kind"] == "code_spec_compiler"
    assert static_rows[0]["joint_channel"]["assembly_semantics"] == (
        "single_joint_generator_expm"
    )
    assert static_rows[0]["joint_channel"]["dimension"] == 32


def test_public_axis1_lindblad_context_selects_thermal_up_from_schedule():
    builder = CircuitBuilder(num_qubits=3)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            include_thermal_excitation=True,
            gamma_up_per_ns=2.0e-4,
        )
    )
    builder.idle((0, 1, 2), duration_ns=25.0)
    builder.measure((0, 1, 2), key=("m0", "m1", "m2"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    assert schedule.axis1_local_lindblad_context["include_thermal_excitation"] is True
    assert schedule.to_manifest()["axis1_local_lindblad_context"]["gamma_up_per_ns"] == 2.0e-4

    plan = build_axis1_schedule_selection_plan(schedule)
    assert plan.axis1_local_lindblad_context["include_thermal_excitation"] is True
    assert plan.selections[0].row_kind == "idle_cluster_joint_channel"
    assert plan.selections[0].primitive_names == ("T2", "T1", "T1_UP")

    channel = axis1_substep_channel_evidence_manifest(schedule)
    assert channel["axis1_local_lindblad_context"]["gamma_up_per_ns"] == 2.0e-4
    row = channel["rows"][0]
    assert row["row_kind"] == "idle_cluster_joint_channel"
    assert row["primitive_names"] == ["T2", "T1", "T1_UP"]
    assert [
        (record["name"], record["support"])
        for record in row["lowered_mechanisms"]
        if record["name"] == "T1_UP"
    ] == [("T1_UP", [0]), ("T1_UP", [1]), ("T1_UP", [2])]

    state = axis1_state_evolution_evidence_manifest(schedule)
    applied = state["state_evolution"]["applied_steps"][0]
    assert "T1_UP" in applied["primitive_names"]
    assert any(record["name"] == "T1_UP" for record in applied["lowered_mechanisms"])

    record = axis1_measurement_record_evidence_manifest(schedule)
    assert "T1_UP" in record["record_evidence"]["applied_steps"][0]["primitive_names"]
    assert record["record_evidence"]["record_count"] == 8


def test_public_axis1_lindblad_context_overrides_local_rate_coefficients():
    context = Axis1LocalLindbladContextSpec(
        zeta_rad_per_ns=1.25e-3,
        gamma_phi_per_ns=8.0e-4,
        gamma_1_per_ns=9.0e-4,
        gamma_readout_phi_per_ns=1.25e-3,
    )
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_axis1_local_lindblad_context(context)
    builder.declare_static_zz_couplings(((0, 1),))
    builder.idle((0, 1), duration_ns=25.0)
    builder.measure((0, 1), key=("m0", "m1"), duration_ns=250.0)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    channel = axis1_substep_channel_evidence_manifest(schedule)
    idle_row = next(
        row
        for row in channel["rows"]
        if row["row_kind"] == "idle_zz_cluster_joint_channel"
    )
    readout_row = next(
        row
        for row in channel["rows"]
        if row["row_kind"] == "readout_zz_cluster_joint_channel"
    )

    idle_records = {
        (record["name"], tuple(record["support"])): record["coefficient"]
        for record in idle_row["lowered_mechanisms"]
    }
    assert idle_records[("ZZ", (0, 1))] == pytest.approx(1.25e-3)
    assert idle_records[("T2", (0,))] == pytest.approx((2.0 * 8.0e-4) ** 0.5)
    assert idle_records[("T1", (0,))] == pytest.approx((9.0e-4) ** 0.5)

    rd_coefficients = [
        record["coefficient"]
        for record in readout_row["lowered_mechanisms"]
        if record["name"] == "RD"
    ]
    assert rd_coefficients == pytest.approx(
        [(2.0 * 1.25e-3) ** 0.5, (2.0 * 1.25e-3) ** 0.5]
    )
    assert "T1_UP" not in {
        record["name"] for row in channel["rows"] for record in row["lowered_mechanisms"]
    }


def test_public_static_zz_calibration_overrides_global_zeta_on_single_pair_row():
    context = Axis1LocalLindbladContextSpec(zeta_rad_per_ns=9.0e-4)
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_axis1_local_lindblad_context(context)
    builder.declare_static_zz_couplings(
        ((0, 1),),
        zeta_rad_per_ns_by_edge={(0, 1): 1.75e-3},
    )
    builder.h(0)
    builder.measure((0, 1), key=("m0", "m1"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    assert schedule.static_zz_calibrations == {
        (0, 1): {"zeta_rad_per_ns": 1.75e-3, "epistemic_class": "c"}
    }
    channel = axis1_substep_channel_evidence_manifest(schedule)
    row = next(
        row
        for row in channel["rows"]
        if row["row_kind"] == "one_qubit_drive_zz_joint_channel"
    )
    zz_records = [record for record in row["lowered_mechanisms"] if record["name"] == "ZZ"]
    assert [record["support"] for record in zz_records] == [[0, 1]]
    assert [record["coefficient"] for record in zz_records] == pytest.approx([1.75e-3])

    uncalibrated = CircuitBuilder(num_qubits=2)
    uncalibrated.declare_axis1_local_lindblad_context(context)
    uncalibrated.declare_static_zz_couplings(((0, 1),))
    uncalibrated.h(0)
    uncalibrated.measure((0, 1), key=("m0", "m1"))
    default_schedule = circuit_ir_to_substep_schedule(uncalibrated.build())
    default_channel = axis1_substep_channel_evidence_manifest(default_schedule)
    default_row = next(
        row
        for row in default_channel["rows"]
        if row["row_kind"] == "one_qubit_drive_zz_joint_channel"
    )
    default_zz = [
        record for record in default_row["lowered_mechanisms"] if record["name"] == "ZZ"
    ]
    assert [record["coefficient"] for record in default_zz] == pytest.approx([9.0e-4])


def test_public_static_zz_calibrations_lower_distinct_cluster_coefficients():
    builder = CircuitBuilder(num_qubits=3)
    builder.declare_static_zz_couplings(
        ((0, 1), (0, 2)),
        zeta_rad_per_ns_by_edge={
            (0, 1): 1.25e-3,
            (0, 2): {"zeta_rad_per_ns": 2.5e-3, "epistemic_class": "b"},
        },
    )
    builder.cz((0, 1))
    builder.tick()
    builder.cz((0, 2))
    builder.tick()
    builder.h(0)
    builder.measure((0, 1, 2), key=("m0", "m1", "m2"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    calibration_manifest = [
        {"edge": [0, 1], "zeta_rad_per_ns": 1.25e-3, "epistemic_class": "c"},
        {"edge": [0, 2], "zeta_rad_per_ns": 2.5e-3, "epistemic_class": "b"},
    ]
    assert schedule.to_manifest()["static_zz_calibrations"] == calibration_manifest
    plan = build_axis1_schedule_selection_plan(schedule)
    assert plan.to_manifest()["static_zz_calibrations"] == calibration_manifest

    channel = axis1_substep_channel_evidence_manifest(schedule)
    assert channel["static_zz_calibrations"] == calibration_manifest
    row = next(
        row
        for row in channel["rows"]
        if row["row_kind"] == "one_qubit_drive_zz_cluster_joint_channel"
    )
    zz_records = [record for record in row["lowered_mechanisms"] if record["name"] == "ZZ"]
    assert [record["support"] for record in zz_records] == [[0, 1], [0, 2]]
    assert [record["coefficient"] for record in zz_records] == pytest.approx(
        [1.25e-3, 2.5e-3]
    )

    state = axis1_state_evolution_evidence_manifest(schedule)
    state_row = next(
        step
        for step in state["state_evolution"]["applied_steps"]
        if step["row_kind"] == "one_qubit_drive_zz_cluster_joint_channel"
    )
    state_zz = [
        record for record in state_row["lowered_mechanisms"] if record["name"] == "ZZ"
    ]
    assert [record["coefficient"] for record in state_zz] == pytest.approx(
        [1.25e-3, 2.5e-3]
    )

    record = axis1_measurement_record_evidence_manifest(schedule)
    record_row = next(
        step
        for step in record["record_evidence"]["applied_steps"]
        if step["row_kind"] == "one_qubit_drive_zz_cluster_joint_channel"
    )
    record_zz = [
        item for item in record_row["lowered_mechanisms"] if item["name"] == "ZZ"
    ]
    assert [item["coefficient"] for item in record_zz] == pytest.approx(
        [1.25e-3, 2.5e-3]
    )


def test_codespec_axis1_lindblad_context_metadata_reaches_selector():
    metadata = Axis1LocalLindbladContextSpec(
        include_thermal_excitation=True,
        gamma_up_per_ns=2.0e-4,
    ).to_metadata()
    spec = _make_mixed_frontend_spec(rounds=2, metadata=metadata)
    schedule = compile_code_spec_to_substep_schedule(spec)

    assert schedule.source_kind == "code_spec_compiler"
    assert schedule.axis1_local_lindblad_context["include_thermal_excitation"] is True
    plan = build_axis1_schedule_selection_plan(schedule)
    assert plan.axis1_local_lindblad_context["gamma_up_per_ns"] == 2.0e-4
    assert any("T1_UP" in selection.primitive_names for selection in plan.selections)
    assert any("T1_UP_B" in selection.primitive_names for selection in plan.selections)


def test_codespec_static_zz_calibration_metadata_reaches_schedule():
    metadata = Axis1StaticZZDeviceSpec(
        edges=((0, 1),),
        num_qubits=5,
        zeta_rad_per_ns_by_edge={(0, 1): {"zeta_rad_per_ns": 1.75e-3, "epistemic_class": "b"}},
    ).to_metadata()
    spec = _make_mixed_frontend_spec(rounds=2, metadata=metadata)
    schedule = compile_code_spec_to_substep_schedule(spec)
    manifest = schedule.to_manifest()

    assert schedule.source_kind == "code_spec_compiler"
    assert schedule.static_zz_couplings == ((0, 1),)
    assert schedule.static_zz_calibrations == {
        (0, 1): {"zeta_rad_per_ns": 1.75e-3, "epistemic_class": "b"}
    }
    assert manifest["static_zz_calibrations"] == [
        {"edge": [0, 1], "zeta_rad_per_ns": 1.75e-3, "epistemic_class": "b"}
    ]

    plan = build_axis1_schedule_selection_plan(schedule)
    assert plan.static_zz_calibrations == schedule.static_zz_calibrations
    assert plan.to_manifest()["static_zz_calibrations"] == manifest[
        "static_zz_calibrations"
    ]

    missing_edges = _make_mixed_frontend_spec(
        rounds=2,
        metadata={
            AXIS1_STATIC_ZZ_CALIBRATIONS_METADATA_KEY: [
                {"edge": [0, 1], "zeta_rad_per_ns": 1.0e-3}
            ],
        },
    )
    with pytest.raises(ValueError, match="not declared"):
        compile_code_spec_to_substep_schedule(missing_edges)


def test_codespec_static_zz_metadata_is_validated_by_compiler_seam():
    spec = _make_mixed_frontend_spec(
        rounds=2,
        metadata={AXIS1_STATIC_ZZ_COUPLINGS_METADATA_KEY: ((0, 5),)},
    )

    with pytest.raises(ValueError, match="outside"):
        compile_code_spec_to_substep_schedule(spec)


def test_codespec_compiler_schedule_runs_axis1_record_evidence_with_pauli_measurements():
    spec = build_axis1_codespec_frontend_spec(rounds=2)
    schedule = build_axis1_codespec_frontend_schedule(rounds=2)

    manifest = axis1_measurement_record_evidence_manifest(schedule)
    evidence = manifest["record_evidence"]

    assert manifest["source_kind"] == "code_spec_compiler"
    assert manifest["coverage"]["full_positive_duration_coverage"] is True
    assert manifest["coverage"]["positive_duration_coverage_fraction"] == 1.0
    assert manifest["coverage"]["positive_duration_window_coverage_fraction"] == 1.0
    assert manifest["coverage"]["partial_positive_duration_substeps"] == []
    assert evidence["measurement_basis"] == "mixed_pauli"
    assert evidence["measurement_bases"] == ["X", "Z"]
    assert evidence["applied_channel_count"] == 8
    assert evidence["record_count"] == 128
    assert evidence["detector_records_emitted"] is True
    assert evidence["logical_observables_emitted"] is True
    assert any(
        step["row_kind"] == "two_qubit_control_cluster_joint_channel"
        and step["ideal_controls"][0]["name"] == "CTRL_CX"
        and len(step["participant"]) == 5
        for step in evidence["applied_steps"]
    )
    assert spec.name == "axis1_codespec_mixed_basis_frontend"


def test_circuit_ir_schedule_detects_implicit_and_explicit_idles():
    builder = CircuitBuilder(num_qubits=3)
    builder.h(0)
    builder.tick()
    builder.x(2)
    builder.idle(1)
    builder.tick()
    builder.measure((0, 1, 2), key=("m0", "m1", "m2"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    h_step = next(
        substep
        for substep in schedule.substeps
        if substep.kind == "one_qubit_gate" and substep.operations[0].name == "H"
    )
    assert h_step.active_qubits == (0,)
    assert h_step.idle_qubits == (1, 2)
    assert h_step.dt_ns_nominal == 25.0
    assert h_step.dt_ns_bracket == (20.0, 30.0)

    x_step = next(
        substep
        for substep in schedule.substeps
        if substep.kind == "one_qubit_gate" and substep.operations[0].name == "X"
    )
    assert x_step.active_qubits == (2,)
    assert x_step.idle_qubits == (0, 1)

    explicit_idle = next(substep for substep in schedule.substeps if substep.kind == "idle")
    assert explicit_idle.active_qubits == ()
    assert explicit_idle.idle_qubits == (1,)
    assert explicit_idle.dt_ns_nominal is None
    assert explicit_idle.dt_ns_bracket == (0.0, 300.0)


def test_measurement_and_reset_boundaries_preserve_record_metadata_without_analog_claim():
    builder = CircuitBuilder(num_qubits=1)
    builder.reset(0)
    builder.measure(0, key="m0", reset=True)
    builder.detector("d0", xor=("m0",))
    builder.observable("logical0", xor=("m0",), index=0)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    reset = next(substep for substep in schedule.substeps if substep.kind == "reset")
    assert reset.operations[0].name == "R"
    assert reset.dt_ns_nominal is None
    assert reset.dt_ns_bracket == (100.0, 500.0)
    assert reset.mechanism_slots == ("reset_boundary",)

    measurement = next(substep for substep in schedule.substeps if substep.kind == "measurement")
    assert measurement.operations[0].name == "MR"
    assert measurement.operations[0].basis == "Z"
    assert measurement.operations[0].reset_after_measurement is True
    assert measurement.measurement_keys == ("m0",)
    assert measurement.dt_ns_nominal is None
    assert measurement.mechanism_slots == ("readout_boundary", "reset_boundary")

    assert schedule.record_layout_ref["measurement_keys"] == ["m0"]
    assert schedule.record_layout_ref["detector_names"] == ["d0"]
    assert schedule.record_layout_ref["observable_names"] == ["logical0"]


def test_overlapping_two_qubit_participants_fail_closed():
    circuit = CircuitIR(num_qubits=3, steps=(GateOp("CZ", (0, 1, 1, 2)),))

    with pytest.raises(ValueError, match="overlapping pair participant"):
        circuit_ir_to_substep_schedule(circuit)


def test_noise_and_source_projection_cannot_satisfy_axis1_schedule_contract():
    projected = CircuitIR(
        num_qubits=1,
        steps=(GateOp("I", (0,)),),
        metadata={"noise_projection": {"type": "stim_pauli_source_projection"}},
    )

    with pytest.raises(ValueError, match="not analog joint-L schedule"):
        circuit_ir_to_substep_schedule(projected)

    with pytest.raises(ValueError, match="source_timeline"):
        CircuitIR(
            num_qubits=1,
            steps=(GateOp("I", (0,)),),
            metadata={"source_timeline": {"visibility": "evaluator_only"}},
        )


def test_schedule_source_hash_is_stable_and_changes_with_circuit_body():
    builder = CircuitBuilder(num_qubits=2)
    builder.h(0)
    builder.tick()
    circuit_a = builder.build()

    builder = CircuitBuilder(num_qubits=2)
    builder.h(0)
    builder.tick()
    circuit_b = builder.build()

    builder = CircuitBuilder(num_qubits=2)
    builder.x(0)
    builder.tick()
    circuit_c = builder.build()

    assert circuit_ir_to_substep_schedule(circuit_a).source_hash == (
        circuit_ir_to_substep_schedule(circuit_b).source_hash
    )
    assert circuit_ir_to_substep_schedule(circuit_a).source_hash != (
        circuit_ir_to_substep_schedule(circuit_c).source_hash
    )


def test_public_circuit_ir_extractor_cannot_spoof_reserved_source_kind():
    builder = CircuitBuilder(num_qubits=2)
    builder.h(0)
    builder.tick()
    circuit = builder.build()

    with pytest.raises(ValueError, match="reserved for compiler/importer wrappers"):
        circuit_ir_to_substep_schedule(circuit, source_kind="stim_circuit")
    with pytest.raises(ValueError, match="reserved for compiler/importer wrappers"):
        circuit_ir_to_substep_schedule(circuit, source_kind="code_spec_compiler")


def test_axis1_primitive_registry_lowers_supported_joint_channel_bundle_on_gpu():
    params = Axis1PrimitiveParams(
        zeta_rad_per_ns=JOINT_CHANNEL_ZETA_RAD_PER_NS,
        gamma_phi_per_ns=JOINT_CHANNEL_GAMMA_PHI_PER_NS,
        gamma_1_per_ns=JOINT_CHANNEL_GAMMA_1_PER_NS,
        gamma_up_per_ns=2.0e-4,
    )
    registry = default_axis1_primitive_registry()
    assert registry.registry_id == AXIS1_TWO_QUBIT_LOCAL_REGISTRY_ID
    assert set(registry.supported_primitives) == {
        "DR",
        "ZZ",
        "T2",
        "T1",
        "T1_UP",
        "T2_B",
        "T1_B",
        "T1_UP_B",
        "RD",
        "RD_B",
        "FSIM_SWAP",
        "FSIM_PHASE",
    }
    registry_manifest = registry.to_manifest()
    assert registry_manifest["contains_operator_payload"] is False
    assert registry_manifest["registry_id"] == AXIS1_TWO_QUBIT_LOCAL_REGISTRY_ID

    bundle = registry.lower(
        ("DR", "ZZ", "T2", "T1"),
        dt_ns=25.0,
        params=params,
        device="cuda",
    )

    assert bundle.primitive_names == ("DR", "ZZ", "T2", "T1")
    assert len(bundle.H_list) == 2
    assert len(bundle.c_list) == 2
    assert [record.name for record in bundle.records] == ["DR", "ZZ", "T2", "T1"]
    manifest = bundle.to_manifest()
    assert manifest["representability"] == "two_qubit_axis1_local_window_primitives"
    assert manifest["num_hamiltonian_terms"] == 2
    assert manifest["num_collapse_ops"] == 2
    lo, hi = JOINT_CHANNEL_DR_ZZ_BAND
    one_minus = composed_vs_joint_infidelity(
        bundle.H_list,
        bundle.c_list,
        25.0,
        device="cuda",
    )
    assert lo <= one_minus <= hi

    with pytest.raises(ValueError, match="unsupported Axis-1 primitive"):
        registry.lower(
            ("DR", "LK"),
            dt_ns=25.0,
            params=params,
            device="cuda",
        )

    wrapper_bundle = lower_two_qubit_axis1_primitives(
        ("ZZ", "T2"),
        dt_ns=30.0,
        params=params,
        device="cuda",
    )
    assert wrapper_bundle.primitive_names == ("ZZ", "T2")

    spectator_bundle = registry.lower(
        ("T2_B", "T1_B", "T1_UP_B"),
        dt_ns=25.0,
        params=params,
        device="cuda",
    )
    assert spectator_bundle.primitive_names == ("T2_B", "T1_B", "T1_UP_B")
    assert len(spectator_bundle.H_list) == 0
    assert len(spectator_bundle.c_list) == 3

    readout_bundle = registry.lower(
        ("RD", "RD_B"),
        dt_ns=250.0,
        params=params,
        device="cuda",
    )
    assert readout_bundle.primitive_names == ("RD", "RD_B")
    assert len(readout_bundle.H_list) == 0
    assert len(readout_bundle.c_list) == 2

    thermal_bundle = registry.lower(
        ("T1_UP",),
        dt_ns=25.0,
        params=params,
        device="cuda",
    )
    assert thermal_bundle.primitive_names == ("T1_UP",)
    assert [record.name for record in thermal_bundle.records] == ["T1_UP"]
    kraus = assemble_substep_channel(
        thermal_bundle.H_list,
        thermal_bundle.c_list,
        25.0,
        device="cuda",
    )
    rho = torch.zeros((4, 4), dtype=torch.complex128, device="cuda")
    rho[0, 0] = 1.0
    out = sum(K @ rho @ K.conj().transpose(-1, -2) for K in kraus)
    assert float(out[2, 2].real.item()) > 0.0
    assert abs(float(torch.trace(out).real.item()) - 1.0) <= 1e-8


def test_axis1_fsim_residual_primitives_match_closed_form_unitary_on_gpu():
    dt = 30.0
    for theta, phi in ((1.7e-2, -1.1e-2), (-2.5e-2, 9.0e-3)):
        params = Axis1PrimitiveParams(
            zeta_rad_per_ns=0.0,
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            fsim_delta_theta_rad=theta,
            fsim_delta_phi_rad=phi,
        )

        bundle = lower_two_qubit_axis1_primitives(
            ("FSIM_SWAP", "FSIM_PHASE"),
            dt_ns=dt,
            params=params,
            device="cuda",
        )

        assert bundle.primitive_names == ("FSIM_SWAP", "FSIM_PHASE")
        assert len(bundle.H_list) == 2
        assert len(bundle.c_list) == 0
        assert [
            (record.name, record.generator_kind, record.support, record.coefficient)
            for record in bundle.records
        ] == [
            ("FSIM_SWAP", "hamiltonian", (0, 1), pytest.approx(theta / dt)),
            ("FSIM_PHASE", "hamiltonian", (0, 1), pytest.approx(phi / dt)),
        ]

        expected = torch.eye(4, dtype=torch.complex128, device="cuda")
        expected[1, 1] = math.cos(theta)
        expected[1, 2] = -1j * math.sin(theta)
        expected[2, 1] = -1j * math.sin(theta)
        expected[2, 2] = math.cos(theta)
        expected[3, 3] = complex(math.cos(phi), -math.sin(phi))
        kraus = assemble_substep_channel(bundle.H_list, bundle.c_list, dt, device="cuda")
        _assert_kraus_channel_matches_unitary(kraus, expected)


def test_axis1_fsim_swap_t2_catches_bad_sequential_composition_on_gpu():
    params = Axis1PrimitiveParams(
        zeta_rad_per_ns=0.0,
        gamma_phi_per_ns=5.0e-3,
        gamma_1_per_ns=0.0,
        fsim_delta_theta_rad=8.0e-2,
    )
    bundle = lower_two_qubit_axis1_primitives(
        ("FSIM_SWAP", "T2"),
        dt_ns=30.0,
        params=params,
        device="cuda",
    )

    assert [record.name for record in bundle.records] == ["FSIM_SWAP", "T2"]
    one_minus = composed_vs_joint_infidelity(
        bundle.H_list,
        bundle.c_list,
        30.0,
        device="cuda",
    )
    assert one_minus > 1.0e-10


def test_axis1_cluster_lowering_honors_explicit_thermal_excitation_on_gpu():
    params = Axis1PrimitiveParams(
        zeta_rad_per_ns=JOINT_CHANNEL_ZETA_RAD_PER_NS,
        gamma_phi_per_ns=JOINT_CHANNEL_GAMMA_PHI_PER_NS,
        gamma_1_per_ns=JOINT_CHANNEL_GAMMA_1_PER_NS,
        gamma_up_per_ns=2.0e-4,
    )
    selection = Axis1MechanismSelection(
        selection_id="manual:idle_cluster_with_t1_up:0_1",
        row_kind="idle_cluster_joint_channel",
        substep_id="manual_idle",
        substep_kind="idle",
        participant=(0, 1),
        primitive_names=("T2", "T1", "T1_UP"),
        mechanism_pair=("IDLE", "THERMAL_UP_CLUSTER"),
        context_mechanisms=("T2", "T1", "T1_UP"),
        operation_names=(),
        source_step_indices=(),
        operation_records=(),
        dt_ns_nominal=25.0,
        dt_ns_bracket=(25.0, 25.0),
        dt_source="manual_test_selection",
        mechanism_slots=("idle",),
        reason="test-only explicit thermal-up cluster primitive lowering",
    )

    assembled = _assemble_selection_joint_channel(
        selection,
        dt_ns=25.0,
        params=params,
        device="cuda",
    )
    record_names = [record.name for record in assembled.primitive_bundle.records]
    assert record_names.count("T1_UP") == 2
    assert len(assembled.primitive_bundle.c_list) == 6

    rho = torch.zeros((4, 4), dtype=torch.complex128, device="cuda")
    rho[0, 0] = 1.0
    out = sum(K @ rho @ K.conj().transpose(-1, -2) for K in assembled.kraus)
    assert float((out[1, 1] + out[2, 2]).real.item()) > 0.0
    assert abs(float(torch.trace(out).real.item()) - 1.0) <= 1e-8


def test_joint_channel_selection_plan_is_schedule_derived_and_metadata_only():
    schedule = _joint_channel_schedule()
    plan = build_axis1_joint_channel_selection_plan(schedule)
    manifest = plan.to_manifest()

    assert plan.source_hash == schedule.source_hash
    assert plan.static_zz_pairs == ((0, 1),)
    assert {selection.row_kind for selection in plan.selections} == {
        "zz_t2_exact_zero",
        "dr_zz_prediction_band",
    }
    assert manifest["representability"] == "schedule_derived_axis1_selection_no_h_or_c_payload"
    payload = json.dumps(manifest, sort_keys=True)
    for forbidden in ("hamiltonian", "collapse", "kraus", "ptm", "source_timeline"):
        assert forbidden not in payload.lower()

    exact = plan.require_kind("zz_t2_exact_zero")[0]
    assert exact.primitive_names == ("ZZ", "T2")
    assert exact.source_step_indices == (2,)
    nonzero = plan.require_kind("dr_zz_prediction_band")[0]
    assert nonzero.primitive_names == ("DR", "ZZ", "T2", "T1")
    assert nonzero.mechanism_slots == ("drive", "idle", "spectator")


def test_axis1_generic_selection_plan_covers_non_comparison_drive_substeps():
    builder = CircuitBuilder(num_qubits=2)
    builder.h(0)
    builder.tick()
    builder.x(1)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    plan = build_axis1_schedule_selection_plan(schedule)
    manifest = plan.to_manifest()

    assert plan.selector_id == "axis1_schedule_joint_channel_selector_v1"
    assert plan.static_zz_pairs == ()
    assert [selection.row_kind for selection in plan.selections] == [
        "one_qubit_drive_joint_channel",
        "one_qubit_drive_joint_channel",
    ]
    assert {selection.participant for selection in plan.selections} == {(0, 1), (1, 0)}
    assert all(
        selection.primitive_names == ("T2", "T1", "T2_B", "T1_B")
        for selection in plan.selections
    )
    payload = json.dumps(manifest, sort_keys=True).lower()
    for forbidden in ("hamiltonian", "collapse", "kraus", "ptm", "source_timeline"):
        assert forbidden not in payload

    evidence = axis1_substep_channel_evidence_manifest(schedule)
    assert evidence["selection_plan"]["selector_id"] == "axis1_schedule_joint_channel_selector_v1"
    assert len(evidence["rows"]) == 2
    assert evidence["coverage"]["selected_substep_ids"] == ["s0000", "s0002"]
    assert evidence["coverage"]["full_positive_duration_coverage"] is True
    assert evidence["coverage"]["positive_duration_coverage_fraction"] == 1.0
    assert evidence["coverage"]["omitted_substeps"] == [
        {
            "substep_id": "s0001",
            "kind": "barrier",
            "reason": "structural_or_no_nominal_dt",
            "dt_ns_nominal": None,
            "dt_ns_bracket": [0.0, 0.0],
        }
    ]
    assert all(row["row_kind"] == "one_qubit_drive_joint_channel" for row in evidence["rows"])
    assert {tuple(row["primitive_names"]) for row in evidence["rows"]} == {
        ("T2", "T1", "T2_B", "T1_B")
    }
    assert {row["ideal_controls"][0]["name"] for row in evidence["rows"]} == {
        "CTRL_H",
        "CTRL_X",
    }
    assert all(row["joint_channel"]["contains_ideal_control_hamiltonian"] for row in evidence["rows"])
    assert all(row["joint_channel"]["dimension"] == 4 for row in evidence["rows"])
    assert all(row["passed"] for row in evidence["rows"])


def test_axis1_generic_frontend_controls_cover_supported_one_qubit_gate_names():
    for gate_name in sorted(AXIS1_FRONTEND_ONE_QUBIT_CONTROL_GATES):
        builder = CircuitBuilder(num_qubits=2)
        builder.gate(gate_name, 0)
        builder.measure((0, 1), key=("m0", "m1"))
        schedule = circuit_ir_to_substep_schedule(builder.build())

        plan = build_axis1_schedule_selection_plan(schedule)
        assert [selection.row_kind for selection in plan.selections] == [
            "one_qubit_drive_joint_channel"
        ]

        evidence = axis1_substep_channel_evidence_manifest(schedule)
        assert evidence["coverage"]["full_positive_duration_coverage"] is True
        assert evidence["rows"][0]["ideal_controls"][0]["name"] == f"CTRL_{gate_name}"
        assert evidence["rows"][0]["joint_channel"]["assembly_semantics"] == (
            "single_joint_generator_expm"
        )
        assert evidence["rows"][0]["passed"] is True


def test_axis1_generic_frontend_controls_cover_supported_two_qubit_gate_names():
    for gate_name in sorted(AXIS1_FRONTEND_TWO_QUBIT_CONTROL_GATES):
        builder = CircuitBuilder(num_qubits=2)
        builder.gate(gate_name, (0, 1))
        builder.measure((0, 1), key=("m0", "m1"))
        schedule = circuit_ir_to_substep_schedule(builder.build())

        plan = build_axis1_schedule_selection_plan(schedule)
        assert len(plan.selections) == 1
        expected_row_kind = (
            "two_qubit_zz_joint_channel"
            if gate_name == "CZ"
            else "two_qubit_control_joint_channel"
        )
        assert plan.selections[0].row_kind == expected_row_kind

        evidence = axis1_substep_channel_evidence_manifest(schedule)
        assert evidence["coverage"]["full_positive_duration_coverage"] is True
        assert evidence["rows"][0]["ideal_controls"][0]["name"] == f"CTRL_{gate_name}"
        assert evidence["rows"][0]["joint_channel"]["assembly_semantics"] == (
            "single_joint_generator_expm"
        )
        assert evidence["rows"][0]["joint_channel"]["dimension"] == 4
        assert evidence["rows"][0]["passed"] is True


def test_axis1_ideal_control_lowering_matches_unitary_oracle_on_gpu():
    import stim

    for gate_name in sorted(AXIS1_FRONTEND_ONE_QUBIT_CONTROL_GATES):
        builder = CircuitBuilder(num_qubits=2)
        builder.gate(gate_name, 0)
        schedule = circuit_ir_to_substep_schedule(builder.build())
        selection = build_axis1_schedule_selection_plan(schedule).selections[0]
        expected_1q = torch.as_tensor(
            stim.Circuit(f"{gate_name} 0").to_tableau().to_unitary_matrix(endian="big"),
            dtype=torch.complex128,
            device="cuda",
        )
        _assert_control_channel_matches_unitary(
            selection,
            torch.kron(expected_1q.contiguous(), torch.eye(2, dtype=torch.complex128, device="cuda")),
        )

    for gate_name in sorted(AXIS1_FRONTEND_TWO_QUBIT_CONTROL_GATES):
        builder = CircuitBuilder(num_qubits=2)
        builder.gate(gate_name, (0, 1))
        selection = build_axis1_schedule_selection_plan(
            circuit_ir_to_substep_schedule(builder.build())
        ).selections[0]
        expected_2q = torch.as_tensor(
            stim.Circuit(f"{gate_name} 0 1").to_tableau().to_unitary_matrix(endian="big"),
            dtype=torch.complex128,
            device="cuda",
        )
        _assert_control_channel_matches_unitary(selection, expected_2q)


def test_axis1_explicit_idle_duration_selects_idle_pair_joint_channel():
    builder = CircuitBuilder(num_qubits=2)
    builder.idle((0, 1), duration_ns=75.0)
    builder.measure((0, 1), key=("m0", "m1"))
    builder.detector("d0", xor=("m0", "m1"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    idle = schedule.substeps[0]
    assert idle.kind == "idle"
    assert idle.active_qubits == ()
    assert idle.idle_qubits == (0, 1)
    assert idle.dt_ns_nominal == 75.0
    assert idle.dt_ns_bracket == (75.0, 75.0)
    assert idle.dt_source == "explicit_circuit_idle_duration"

    plan = build_axis1_schedule_selection_plan(schedule)
    assert [selection.row_kind for selection in plan.selections] == [
        "idle_pair_joint_channel"
    ]
    assert plan.selections[0].participant == (0, 1)
    assert plan.selections[0].primitive_names == ("T2", "T1", "T2_B", "T1_B")

    channel = axis1_substep_channel_evidence_manifest(schedule)
    assert channel["coverage"]["selected_substep_ids"] == ["s0000"]
    assert channel["coverage"]["full_positive_duration_coverage"] is True
    assert channel["rows"][0]["row_kind"] == "idle_pair_joint_channel"
    assert channel["rows"][0]["dt_ns"] == 75.0
    assert channel["rows"][0]["joint_channel"]["assembly_semantics"] == (
        "single_joint_generator_expm"
    )

    record = axis1_measurement_record_evidence_manifest(schedule)
    assert record["record_evidence"]["applied_channel_count"] == 1
    assert record["record_evidence"]["applied_steps"][0]["row_kind"] == (
        "idle_pair_joint_channel"
    )
    assert record["record_evidence"]["detector_records_emitted"] is True
    assert record["record_evidence"]["claims_b8_artifact"] is False


def test_axis1_explicit_odd_idle_duration_lowers_union_support_cluster():
    builder = CircuitBuilder(num_qubits=3)
    builder.idle((0, 1, 2), duration_ns=75.0)
    builder.measure((0, 1, 2), key=("m0", "m1", "m2"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    plan = build_axis1_schedule_selection_plan(schedule)
    assert [selection.row_kind for selection in plan.selections] == [
        "idle_cluster_joint_channel"
    ]
    assert plan.selections[0].participant == (0, 1, 2)
    assert plan.selections[0].primitive_names == ("T2", "T1")

    channel = axis1_substep_channel_evidence_manifest(schedule)
    assert channel["coverage"]["full_positive_duration_coverage"] is True
    assert channel["coverage"]["participant_coverage"] == [
        {
            "substep_id": "s0000",
            "kind": "idle",
            "coverage_basis": "explicit_idle_consecutive_pair_partition",
            "dt_ns_nominal": 75.0,
            "expected_participants": [[0, 1]],
            "selected_participants": [[0, 1, 2]],
            "covered_participants": [[0, 1]],
            "missing_participants": [],
            "extra_selected_participants": [],
            "unpaired_qubits": [],
            "covered_unpaired_qubits": [2],
            "full_participant_coverage": True,
            "participant_coverage_fraction": 1.0,
        }
    ]
    row = channel["rows"][0]
    assert row["row_kind"] == "idle_cluster_joint_channel"
    assert row["participant"] == [0, 1, 2]
    assert row["joint_channel"]["dimension"] == 8
    assert row["ideal_controls"] == []
    assert [
        (record["name"], record["support"])
        for record in row["lowered_mechanisms"]
        if record["generator_kind"] == "collapse"
    ] == [
        ("T2", [0]),
        ("T1", [0]),
        ("T2", [1]),
        ("T1", [1]),
        ("T2", [2]),
        ("T1", [2]),
    ]

    record = axis1_measurement_record_evidence_manifest(schedule)
    assert record["record_evidence"]["applied_channel_count"] == 1
    assert record["record_evidence"]["applied_steps"][0]["row_kind"] == (
        "idle_cluster_joint_channel"
    )
    assert record["record_evidence"]["record_count"] == 8


def test_axis1_explicit_idle_static_zz_cluster_embeds_declared_idle_edges():
    builder = CircuitBuilder(num_qubits=3)
    builder.declare_static_zz_couplings(((0, 1),))
    builder.cz((0, 1))
    builder.tick()
    builder.idle((0, 1, 2), duration_ns=75.0)
    builder.measure((0, 1, 2), key=("m0", "m1", "m2"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    plan = build_axis1_schedule_selection_plan(schedule)
    idle_clusters = [
        selection
        for selection in plan.selections
        if selection.row_kind == "idle_zz_cluster_joint_channel"
    ]
    assert len(idle_clusters) == 1
    assert idle_clusters[0].participant == (0, 1, 2)
    assert idle_clusters[0].coupling_edges == ((0, 1),)

    channel = axis1_substep_channel_evidence_manifest(schedule)
    assert channel["coverage"]["selected_substep_ids"] == ["s0000", "s0002"]
    row = next(
        item
        for item in channel["rows"]
        if item["row_kind"] == "idle_zz_cluster_joint_channel"
    )
    assert row["participant"] == [0, 1, 2]
    assert row["coupling_edges"] == [[0, 1]]
    assert row["joint_channel"]["dimension"] == 8
    assert [
        (record["name"], record["support"])
        for record in row["lowered_mechanisms"]
        if record["generator_kind"] == "hamiltonian"
    ] == [("ZZ", [0, 1])]
    assert channel["coverage"]["full_positive_duration_coverage"] is True


def test_axis1_static_zz_requires_explicit_public_metadata_not_cz_history():
    builder = CircuitBuilder(num_qubits=3)
    builder.cz((0, 1))
    builder.tick()
    builder.idle((0, 1, 2), duration_ns=75.0)
    builder.measure((0, 1, 2), key=("m0", "m1", "m2"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    plan = build_axis1_schedule_selection_plan(schedule)
    assert schedule.static_zz_couplings == ()
    assert plan.static_zz_pairs == ()
    assert "idle_zz_cluster_joint_channel" not in {
        selection.row_kind for selection in plan.selections
    }

    channel = axis1_substep_channel_evidence_manifest(schedule)
    idle_row = next(
        row for row in channel["rows"] if row["row_kind"] == "idle_cluster_joint_channel"
    )
    assert idle_row["coupling_edges"] == []


def test_axis1_explicit_measurement_duration_applies_readout_channel_before_records():
    builder = CircuitBuilder(num_qubits=2)
    builder.measure((0, 1), key=("m0", "m1"), duration_ns=250.0)
    builder.detector("d0", xor=("m0", "m1"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    measurement = schedule.substeps[0]
    assert measurement.kind == "measurement"
    assert measurement.active_qubits == (0, 1)
    assert measurement.dt_ns_nominal == 250.0
    assert measurement.dt_ns_bracket == (250.0, 250.0)
    assert measurement.dt_source == "explicit_circuit_measurement_duration"
    assert measurement.operations[0].args == (250.0,)

    plan = build_axis1_schedule_selection_plan(schedule)
    assert [selection.row_kind for selection in plan.selections] == [
        "readout_pair_joint_channel"
    ]
    assert plan.selections[0].primitive_names == (
        "RD",
        "RD_B",
        "T2",
        "T1",
        "T2_B",
        "T1_B",
    )

    channel = axis1_substep_channel_evidence_manifest(schedule)
    assert channel["coverage"]["selected_substep_ids"] == ["s0000"]
    assert channel["coverage"]["full_positive_duration_coverage"] is True
    assert channel["rows"][0]["row_kind"] == "readout_pair_joint_channel"
    assert channel["rows"][0]["dt_ns"] == 250.0
    assert tuple(channel["rows"][0]["primitive_names"]) == (
        "RD",
        "RD_B",
        "T2",
        "T1",
        "T2_B",
        "T1_B",
    )

    record = axis1_measurement_record_evidence_manifest(schedule)
    assert record["record_evidence"]["applied_channel_count"] == 1
    assert record["record_evidence"]["applied_steps"][0]["row_kind"] == (
        "readout_pair_joint_channel"
    )
    assert record["record_evidence"]["measurement_keys"] == ["m0", "m1"]
    assert record["record_evidence"]["detector_records_emitted"] is True
    assert record["record_evidence"]["claims_b8_artifact"] is False


def test_axis1_explicit_odd_readout_duration_lowers_union_support_cluster():
    builder = CircuitBuilder(num_qubits=3)
    builder.measure((0, 1, 2), key=("m0", "m1", "m2"), duration_ns=250.0)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    plan = build_axis1_schedule_selection_plan(schedule)
    assert [selection.row_kind for selection in plan.selections] == [
        "readout_cluster_joint_channel"
    ]
    assert plan.selections[0].participant == (0, 1, 2)
    assert plan.selections[0].primitive_names == ("RD", "T2", "T1")

    channel = axis1_substep_channel_evidence_manifest(schedule)
    assert channel["coverage"]["full_positive_duration_coverage"] is True
    assert channel["rows"][0]["row_kind"] == "readout_cluster_joint_channel"
    assert channel["rows"][0]["participant"] == [0, 1, 2]
    assert channel["rows"][0]["joint_channel"]["dimension"] == 8
    assert [
        (record["name"], record["support"])
        for record in channel["rows"][0]["lowered_mechanisms"]
        if record["generator_kind"] == "collapse"
    ] == [
        ("RD", [0]),
        ("T2", [0]),
        ("T1", [0]),
        ("RD", [1]),
        ("T2", [1]),
        ("T1", [1]),
        ("RD", [2]),
        ("T2", [2]),
        ("T1", [2]),
    ]

    record = axis1_measurement_record_evidence_manifest(schedule)
    assert record["record_evidence"]["applied_channel_count"] == 1
    assert record["record_evidence"]["applied_steps"][0]["row_kind"] == (
        "readout_cluster_joint_channel"
    )
    assert record["record_evidence"]["measurement_keys"] == ["m0", "m1", "m2"]
    assert record["record_evidence"]["record_count"] == 8


def test_axis1_explicit_readout_static_zz_cluster_embeds_declared_edges():
    builder = CircuitBuilder(num_qubits=3)
    builder.declare_static_zz_couplings(((0, 1),))
    builder.cz((0, 1))
    builder.tick()
    builder.measure((0, 1, 2), key=("m0", "m1", "m2"), duration_ns=250.0)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    plan = build_axis1_schedule_selection_plan(schedule)
    readout_clusters = [
        selection
        for selection in plan.selections
        if selection.row_kind == "readout_zz_cluster_joint_channel"
    ]
    assert len(readout_clusters) == 1
    assert readout_clusters[0].participant == (0, 1, 2)
    assert readout_clusters[0].coupling_edges == ((0, 1),)

    channel = axis1_substep_channel_evidence_manifest(schedule)
    row = next(
        item
        for item in channel["rows"]
        if item["row_kind"] == "readout_zz_cluster_joint_channel"
    )
    assert row["participant"] == [0, 1, 2]
    assert row["coupling_edges"] == [[0, 1]]
    assert row["joint_channel"]["dimension"] == 8
    assert [
        (record["name"], record["support"])
        for record in row["lowered_mechanisms"]
        if record["generator_kind"] == "hamiltonian"
    ] == [("ZZ", [0, 1])]
    assert channel["coverage"]["full_positive_duration_coverage"] is True

    record = axis1_measurement_record_evidence_manifest(schedule)
    assert any(
        step["row_kind"] == "readout_zz_cluster_joint_channel"
        for step in record["record_evidence"]["applied_steps"]
    )
    assert record["record_evidence"]["record_count"] == 8


def test_axis1_readout_assignment_instrument_rewrites_reported_records_on_gpu():
    builder = CircuitBuilder(num_qubits=2)
    builder.measure((0, 1), key=("m0", "m1"), duration_ns=250.0)
    builder.detector("d0", xor=("m0", "m1"))
    schedule = circuit_ir_to_substep_schedule(builder.build())
    spec = Axis1ReadoutResetInstrumentSpec(readout_p0_to_1=0.25, readout_p1_to_0=0.0)

    manifest = axis1_measurement_record_evidence_manifest(schedule, instrument_spec=spec)
    evidence = manifest["record_evidence"]
    distribution = {
        tuple(record): probability
        for record, probability in zip(
            evidence["measurement_records"],
            evidence["record_probabilities"],
            strict=True,
        )
    }

    assert manifest["readout_reset_instrument_spec"]["active"] is True
    assert evidence["readout_reset_instrument_spec"]["claims_joint_lindbladian"] is False
    assert len(evidence["readout_assignment_steps"]) == 2
    assert evidence["readout_assignment_steps"][0]["kind"] == "independent_asymmetric_assignment"
    assert evidence["record_count"] == 4
    assert distribution[(0, 0)] == pytest.approx(0.75 * 0.75)
    assert distribution[(1, 0)] == pytest.approx(0.25 * 0.75)
    assert distribution[(0, 1)] == pytest.approx(0.75 * 0.25)
    assert distribution[(1, 1)] == pytest.approx(0.25 * 0.25)
    assert evidence["detector_marginals"] == [pytest.approx(0.375)]


def test_axis1_pair_readout_assignment_instrument_is_nonfactorized():
    builder = CircuitBuilder(num_qubits=2)
    builder.measure((0, 1), key=("m0", "m1"), duration_ns=250.0)
    builder.detector("d0", xor=("m0", "m1"))
    schedule = circuit_ir_to_substep_schedule(builder.build())
    spec = Axis1ReadoutResetInstrumentSpec(readout_pair_flip_probability=0.25)

    manifest = axis1_measurement_record_evidence_manifest(schedule, instrument_spec=spec)
    evidence = manifest["record_evidence"]
    distribution = {
        tuple(record): probability
        for record, probability in zip(
            evidence["measurement_records"],
            evidence["record_probabilities"],
            strict=True,
        )
    }

    assert evidence["readout_assignment_steps"] == [
        {
            "kind": "same_operation_pair_both_flip_assignment",
            "measurement_keys": ["m0", "m1"],
            "columns": [0, 1],
            "probability": 0.25,
            "pairing_policy": "adjacent_keys_within_same_measurement_operation",
            "epistemic_class": "c",
        }
    ]
    assert distribution[(0, 0)] == pytest.approx(0.75)
    assert distribution[(1, 1)] == pytest.approx(0.25)
    assert evidence["record_count"] == len(evidence["measurement_records"])
    assert evidence["detector_marginals"] == [pytest.approx(0.0)]
    assert distribution[(1, 1)] > 0.25 * 0.25


def test_axis1_reset_instrument_changes_later_measurement_without_readout_confusion():
    builder = CircuitBuilder(num_qubits=2)
    builder.measure(0, key="m0", reset=True)
    builder.measure(0, key="m1")
    builder.h(1)
    builder.detector("d0", xor=("m1",))
    schedule = circuit_ir_to_substep_schedule(builder.build())
    spec = Axis1ReadoutResetInstrumentSpec(reset_flip_probability=0.25)

    manifest = axis1_measurement_record_evidence_manifest(schedule, instrument_spec=spec)
    evidence = manifest["record_evidence"]
    distribution = {
        tuple(record): probability
        for record, probability in zip(
            evidence["measurement_records"],
            evidence["record_probabilities"],
            strict=True,
        )
    }

    assert evidence["measurement_steps"][0]["reset_noise"][0]["measurement_key"] == "m0"
    assert evidence["measurement_steps"][0]["reset_noise"][0]["semantics"] == (
        "post_measurement_reset_preparation_flip_before_basis_rotation_back"
    )
    assert distribution[(0, 0)] == pytest.approx(0.75)
    assert distribution[(0, 1)] == pytest.approx(0.25)
    assert evidence["detector_marginals"] == [pytest.approx(0.25)]
    assert evidence["epistemic_classes"]["reset_flip_probability_values"] == "c"


def test_axis1_record_evidence_handles_standalone_reset_boundary_before_readout():
    builder = CircuitBuilder(num_qubits=2)
    builder.reset(0)
    builder.measure((0, 1), key=("m0", "m1"), duration_ns=250.0)
    builder.detector("d0", xor=("m0", "m1"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    assert schedule.substeps[0].kind == "reset"
    assert schedule.substeps[0].operations[0].name == "R"

    record = axis1_measurement_record_evidence_manifest(schedule)
    evidence = record["record_evidence"]
    assert evidence["reset_steps"] == [
        {
            "substep_id": "s0000",
            "operation": {"args": [], "name": "R", "source_step_index": 0, "targets": [0]},
            "reset_semantics": "nonselective_z_reset_to_zero_no_record",
        }
    ]
    assert evidence["applied_steps"][0]["row_kind"] == "readout_pair_joint_channel"
    assert evidence["measurement_keys"] == ["m0", "m1"]
    assert evidence["detector_records_emitted"] is True


def test_axis1_channel_evidence_reports_uncovered_positive_substep_coverage_gap():
    builder = CircuitBuilder(num_qubits=7)
    builder.measure(
        (0, 1, 2, 3, 4, 5, 6),
        key=("m0", "m1", "m2", "m3", "m4", "m5", "m6"),
        duration_ns=250.0,
    )
    schedule = circuit_ir_to_substep_schedule(builder.build())

    evidence = axis1_substep_channel_evidence_manifest(schedule)

    assert evidence["passed"] is False
    assert evidence["verdict"] == "fail"
    assert evidence["selected_rows_passed"] is True
    assert evidence["coverage"]["positive_duration_substeps"] == ["s0000"]
    assert evidence["coverage"]["selected_substep_ids"] == ["s0000"]
    assert evidence["coverage"]["full_positive_duration_coverage"] is False
    assert evidence["coverage"]["positive_duration_coverage_fraction"] == 0.0
    assert evidence["coverage"]["positive_duration_window_coverage_fraction"] == 0.75
    assert [
        item["substep_id"]
        for item in evidence["coverage"]["partial_positive_duration_substeps"]
    ] == ["s0000"]
    assert evidence["coverage"]["partial_positive_duration_substeps"] == [
        {
            "substep_id": "s0000",
            "kind": "measurement",
            "coverage_basis": "explicit_readout_consecutive_pair_partition",
            "dt_ns_nominal": 250.0,
            "expected_participants": [[0, 1], [2, 3], [4, 5]],
            "selected_participants": [[0, 1], [2, 3], [4, 5]],
            "covered_participants": [[0, 1], [2, 3], [4, 5]],
            "missing_participants": [],
            "extra_selected_participants": [],
            "unpaired_qubits": [6],
            "covered_unpaired_qubits": [],
            "full_participant_coverage": False,
            "participant_coverage_fraction": 0.75,
        }
    ]
    state = axis1_state_evolution_evidence_manifest(schedule)
    assert state["passed"] is False
    assert state["verdict"] == "fail"
    assert state["trace_residual_passed"] is True
    assert state["coverage"]["full_positive_duration_coverage"] is False

    record = axis1_measurement_record_evidence_manifest(schedule)
    assert record["passed"] is False
    assert record["verdict"] == "fail"
    assert record["probability_residual_passed"] is True
    assert record["coverage"]["full_positive_duration_coverage"] is False


def test_axis1_one_qubit_drive_over_cap_does_not_claim_full_union_coverage():
    builder = CircuitBuilder(num_qubits=7)
    builder.h(0)
    builder.measure(tuple(range(7)), key=tuple(f"m{i}" for i in range(7)))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    evidence = axis1_substep_channel_evidence_manifest(schedule)

    assert evidence["passed"] is False
    assert evidence["selected_rows_passed"] is True
    assert evidence["coverage"]["full_positive_duration_coverage"] is False
    assert evidence["rows"][0]["row_kind"] == "one_qubit_drive_joint_channel"
    assert evidence["rows"][0]["participant"] == [0, 1]
    assert evidence["rows"][0]["joint_channel"]["dimension"] == 4
    assert not [
        row
        for row in evidence["rows"]
        if row["row_kind"] == "one_qubit_drive_cluster_joint_channel"
    ]


def test_axis1_over_cap_static_idle_refuses_pair_fallback_that_drops_edges():
    builder = CircuitBuilder(num_qubits=6)
    builder.declare_static_zz_couplings(((0, 5),))
    builder.idle(tuple(range(6)), duration_ns=75.0)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    plan = build_axis1_schedule_selection_plan(schedule)
    assert plan.static_zz_pairs == ((0, 5),)
    assert plan.selections == ()
    with pytest.raises(ValueError, match="requires at least one mechanism selection"):
        axis1_substep_channel_evidence_manifest(schedule)


def test_axis1_carrier_program_routes_over_cap_static_idle_without_dropping_edges():
    builder = CircuitBuilder(num_qubits=6)
    builder.declare_static_zz_couplings(
        ((0, 5), (1, 4)),
        zeta_rad_per_ns_by_edge={(0, 5): 1.25e-3},
    )
    builder.idle(tuple(range(6)), duration_ns=75.0)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_carrier_program_manifest(schedule)

    assert manifest["schema"] == "error_coupling_simulator.frontend.carrier_program.v1"
    assert manifest["backend_contract"] == "qt_mps_state_record"
    assert manifest["gpu_required"] is True
    assert manifest["claims_dense_channel_evidence"] is False
    assert manifest["claims_dem_decoder_semantics"] is False
    assert manifest["requires_scalable_backend"] is True
    assert manifest["dense_selection_plan"]["selection_count"] == 0
    assert manifest["coverage"]["full_positive_duration_coverage"] is False
    assert manifest["program"]["num_qubits"] == 6
    assert manifest["program"]["site_order"] == [0, 1, 2, 3, 4, 5]
    book = manifest["program"]["approximation_book"]
    assert book["schema"] == "error_coupling_simulator.frontend.carrier_approximation_book.v1"
    assert book["backend_contract"] == "qt_mps_state_record"
    assert "sequential channel composition is not exact" in book[
        "same_substep_generator_policy"
    ]
    assert book["trajectory_sampling"]["single_trajectory_density_claim"] is False
    assert book["mps_truncation"]["required_ledger"] == (
        "discarded_weight_per_truncating_operation"
    )
    assert book["trotter_split"]["status"] == (
        "none_in_program_ir_backend_must_declare_if_used"
    )
    assert "not replacements for joint_lindbladian" in book["trotter_split"][
        "forbidden_exact_claim"
    ]
    assert book["record_branching"]["public_record_layout_required"] is True
    assert book["record_branching"]["claims_dem_decoder_semantics"] is False
    assert book["dense_oracle_certification"]["within_cap_required"] is True
    assert book["dense_oracle_certification"]["overcap_dense_channel_rows_claimed"] is False
    assert book["dense_oracle_certification"]["comparison_outcome_is_metric"] is False

    assert len(manifest["program"]["substeps"]) == 1
    substep = manifest["program"]["substeps"][0]
    assert substep["route"] == "scalable_required"
    assert substep["route_reason"] == "over_dense_cap_static_zz_union_support"
    assert substep["substep_id"] == "s0000"
    assert substep["substep_kind"] == "idle"
    assert substep["support"] == [0, 1, 2, 3, 4, 5]
    assert substep["dt_ns"] == 75.0
    assert substep["coupling_edges"] == [[0, 5], [1, 4]]
    assert substep["operation_records"][0]["name"] == "I"

    zz_terms = [term for term in substep["terms"] if term["operator_family"] == "ZZ"]
    assert [
        (term["kind"], term["support"], term["coefficient"], term["coefficient_source"])
        for term in zz_terms
    ] == [
        ("hamiltonian", [0, 5], 1.25e-3, "public_static_zz_calibration"),
        ("hamiltonian", [1, 4], JOINT_CHANNEL_ZETA_RAD_PER_NS, "axis1_primitive_default"),
    ]
    assert all(term["provenance"]["metadata_visibility"] == "public" for term in zz_terms)
    local_terms = [
        (term["operator_family"], term["kind"], term["support"])
        for term in substep["terms"]
        if term["operator_family"] in {"T1", "T2"}
    ]
    assert len(local_terms) == 12
    assert ("T2", "collapse", [0]) in local_terms
    assert ("T1", "collapse", [5]) in local_terms


def test_axis1_carrier_program_keeps_dense_feasible_rows_as_oracle_available():
    builder = CircuitBuilder(num_qubits=3)
    builder.declare_static_zz_couplings(
        ((0, 1), (0, 2)),
        zeta_rad_per_ns_by_edge={(0, 2): 2.5e-3},
    )
    builder.h(0)
    builder.measure((0, 1, 2), key=("m0", "m1", "m2"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    dense = axis1_substep_channel_evidence_manifest(schedule)
    carrier = axis1_carrier_program_manifest(schedule)

    assert dense["passed"] is True
    assert carrier["requires_scalable_backend"] is False
    assert carrier["claims_dense_channel_evidence"] is False
    assert carrier["program"]["requires_scalable_backend"] is False
    assert carrier["dense_selection_plan"]["selection_count"] == len(dense["rows"])

    h_step = next(
        step for step in carrier["program"]["substeps"] if step["substep_kind"] == "one_qubit_gate"
    )
    assert h_step["route"] == "dense_oracle_available"
    assert h_step["route_reason"] == "within_dense_axis1_selection_cap"
    assert h_step["support"] == [0, 1, 2]
    assert h_step["coupling_edges"] == [[0, 1], [0, 2]]
    assert h_step["selection_ids"]
    control_terms = [
        term for term in h_step["terms"] if term["operator_family"] == "CTRL_H"
    ]
    assert len(control_terms) == 1
    assert control_terms[0]["kind"] == "hamiltonian"
    assert control_terms[0]["support"] == [0]
    assert control_terms[0]["coefficient_source"] == "axis1_ideal_control"
    assert control_terms[0]["provenance"]["gate_name"] == "H"
    assert control_terms[0]["provenance"]["metadata_visibility"] == (
        "public_frontend_operation"
    )
    assert control_terms[0]["epistemic_class"] == "a"
    assert math.isfinite(control_terms[0]["coefficient"])
    zz_terms = [term for term in h_step["terms"] if term["operator_family"] == "ZZ"]
    assert [
        (term["support"], term["coefficient"], term["coefficient_source"])
        for term in zz_terms
    ] == [
        ([0, 1], JOINT_CHANNEL_ZETA_RAD_PER_NS, "axis1_primitive_default"),
        ([0, 2], 2.5e-3, "public_static_zz_calibration"),
    ]
    assert carrier["coverage"]["full_positive_duration_coverage"] is True


def test_axis1_carrier_program_preserves_reset_and_mr_boundary_only_rows():
    builder = CircuitBuilder(num_qubits=1)
    builder.reset(0)
    builder.measure(0, key="m0", reset=True)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    carrier = axis1_carrier_program_manifest(schedule)

    assert carrier["requires_scalable_backend"] is False
    substeps = carrier["program"]["substeps"]
    assert [substep["substep_kind"] for substep in substeps] == [
        "reset",
        "measurement",
    ]
    assert [substep["route"] for substep in substeps] == [
        "boundary_only",
        "boundary_only",
    ]
    reset_terms = substeps[0]["terms"]
    assert reset_terms == [
        {
            "kind": "instrument",
            "support": [0],
            "operator_family": "RESET_Z",
            "coefficient": None,
            "coefficient_source": "reset_boundary",
            "provenance": {
                "substep_id": "s0000",
                "operation": {
                    "args": [],
                    "name": "R",
                    "source_step_index": 0,
                    "targets": [0],
                },
                "metadata_visibility": "public",
            },
            "epistemic_class": "a",
        }
    ]
    assert substeps[1]["terms"][0]["kind"] == "measurement_boundary"
    assert substeps[1]["operation_records"][0]["reset_after_measurement"] is True


def test_axis1_carrier_program_accepts_mcwf_mps_state_record_contract():
    builder = CircuitBuilder(num_qubits=6)
    builder.declare_static_zz_couplings(((0, 5),))
    builder.idle(tuple(range(6)), duration_ns=75.0)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    carrier = axis1_carrier_program_manifest(
        schedule,
        backend_contract=AXIS1_CARRIER_MCWF_MPS_BACKEND_CONTRACT,
    )

    assert carrier["backend_contract"] == "mcwf_mps_state_record"
    assert carrier["program"]["backend_contract"] == "mcwf_mps_state_record"
    assert carrier["requires_scalable_backend"] is True
    book = carrier["program"]["approximation_book"]
    assert book["backend_contract"] == "mcwf_mps_state_record"
    assert book["state_carrier"]["dimension_polymorphic_local_dims_required"] is True
    assert "MCWF trajectory semantics" in book["state_carrier"]["mcwf_mps_state_record"]
    assert "product-channel trajectories" in book["state_carrier"]["qt_mps_state_record"]
    assert "same-substep unraveling" in book["trajectory_sampling"]["mcwf_status"]
    assert carrier["claims_dense_channel_evidence"] is False
    assert carrier["claims_dem_decoder_semantics"] is False
    assert carrier["claims_axis2_source_timeline"] is False


def test_axis1_mcwf_mps_execution_runs_qubit_fixed_microstep_record_fixture():
    builder = CircuitBuilder(num_qubits=1)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            gamma_readout_phi_per_ns=0.0,
        )
    )
    builder.h(0)
    builder.reset(0)
    builder.measure(0, key="m0")
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        trajectory_count=6,
        rng_seed=123,
        microstep_count=2,
    )

    assert manifest["schema"] == (
        "error_coupling_simulator.frontend.mcwf_mps_state_record_execution.v6"
    )
    assert manifest["backend_contract"] == AXIS1_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
    assert manifest["verdict"] == "pass"
    assert manifest["passed"] is True
    assert manifest["mcwf_mps_backend_executed"] is True
    assert manifest["claims_mcwf_mps_backend_execution"] is True
    assert manifest["claims_exact_joint_lindblad_generator"] is False
    assert manifest["claims_dense_channel_evidence"] is False
    assert manifest["claims_dem_decoder_semantics"] is False
    assert manifest["claims_axis2_source_timeline"] is False
    assert manifest["claims_production_scalable_backend"] is False

    execution = manifest["mps_execution"]
    assert execution["unraveling_policy"] == (
        "fixed_microstep_first_order_quantum_jump_mcwf"
    )
    assert execution["collapse_evolution_policy"] == (
        "joint_first_order_jump_competition_per_microstep"
    )
    assert execution["trajectory_sampling"]["rng_seed_was_explicit"] is True
    assert execution["trajectory_sampling"]["single_trajectory_density_claim"] is False
    assert execution["jump_sampling"]["max_jumps_per_microstep"] == 1
    assert execution["measurement_records"] == [[0]]
    assert execution["record_counts"] == [6]
    assert execution["record_probabilities"] == [1.0]
    assert execution["mps_truncation_ledger"]["accepted_as_exact_bond_representation"] is True


def test_axis1_mcwf_mps_execution_preserves_qutrit_level_record_without_projection():
    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key="m0")
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        local_dims=[3],
        initial_levels=[2],
        leaked_readout_b=1.0,
        trajectory_count=5,
        rng_seed=234,
    )

    assert manifest["schema"] == (
        "error_coupling_simulator.frontend.mcwf_mps_state_record_execution.v6"
    )
    assert manifest["verdict"] == "pass"
    assert manifest["passed"] is True
    assert manifest["mcwf_mps_backend_executed"] is True
    assert manifest["local_hilbert_space"]["local_dims"] == [3]
    assert manifest["claims_exact_joint_lindblad_generator"] is False
    assert manifest["claims_dense_channel_evidence"] is False
    assert manifest["claims_production_scalable_backend"] is False

    execution = manifest["mps_execution"]
    assert execution["local_dims"] == [3]
    assert execution["initial_levels"] == [2]
    assert execution["multilevel_measurement_policy"]["leaked_readout_b"] == 1.0
    assert execution["measurement_records"] == [[1]]
    assert execution["record_counts"] == [5]
    assert execution["record_probabilities"] == [1.0]
    evaluator_diagnostics = execution["evaluator_only_diagnostics"]
    assert evaluator_diagnostics["schema"] == (
        "error_coupling_simulator.frontend.mcwf_mps_evaluator_only_diagnostics.v1"
    )
    assert evaluator_diagnostics["visibility"] == (
        "evaluator_only_not_emitted_record_or_downstream_estimator_input"
    )
    assert evaluator_diagnostics["level_records"] == [[2]]
    assert evaluator_diagnostics["level_record_counts"] == [5]
    assert execution["mps_truncation_ledger"]["local_dims"] == [3]


def test_axis1_mcwf_mps_multilevel_measure_reset_measure_keeps_all_record_keys():
    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key="m0", reset=True)
    builder.measure(0, key="m1")
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        local_dims=[3],
        initial_levels=[2],
        leaked_readout_b=1.0,
        trajectory_count=4,
        rng_seed=901,
    )

    assert manifest["verdict"] == "pass"
    execution = manifest["mps_execution"]
    assert execution["measurement_keys"] == ["m0", "m1"]
    assert execution["measurement_targets"] == [0, 0]
    assert execution["measurement_records"] == [[1, 0]]
    assert execution["record_counts"] == [4]
    assert execution["record_probabilities"] == [1.0]
    evaluator_diagnostics = execution["evaluator_only_diagnostics"]
    assert evaluator_diagnostics["level_records"] == [[2, 0]]
    assert evaluator_diagnostics["level_record_counts"] == [4]
    assert execution["multilevel_measurement_policy"]["leaked_readout_b"] == 1.0


def test_axis1_mcwf_mps_execution_runs_qutrit_exchange_leakage_from_public_context():
    builder = CircuitBuilder(num_qubits=1)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            leak_exchange_12_rad_per_ns=math.pi / 20.0,
        )
    )
    builder.idle(0, duration_ns=10.0)
    builder.measure(0, key="m0")
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        local_dims=[3],
        initial_levels=[1],
        leaked_readout_b=1.0,
        trajectory_count=4,
        rng_seed=567,
    )

    assert manifest["verdict"] == "pass"
    assert manifest["passed"] is True
    assert manifest["mcwf_mps_backend_executed"] is True
    execution = manifest["mps_execution"]
    assert execution["local_dims"] == [3]
    evaluator_diagnostics = execution["evaluator_only_diagnostics"]
    assert evaluator_diagnostics["level_records"] == [[2]]
    assert evaluator_diagnostics["level_record_counts"] == [4]
    assert execution["measurement_records"] == [[1]]
    assert execution["record_counts"] == [4]
    assert execution["applied_substeps"][0]["hamiltonian_term_count"] >= 1
    assert "LEAK_EXCHANGE_12" in execution["applied_substeps"][0][
        "hamiltonian_operator_families"
    ]
    assert execution["exact_joint_generator_claim"] is False
    assert execution["claims_production_scalable_backend"] is False


def test_axis1_mcwf_mps_execution_runs_qutrit_seepage_jump_from_public_context():
    builder = CircuitBuilder(num_qubits=1)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            leak_seep_21_per_ns=1.0,
        )
    )
    builder.idle(0, duration_ns=2.0)
    builder.measure(0, key="m0")
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        local_dims=[3],
        initial_levels=[2],
        leaked_readout_b=1.0,
        trajectory_count=4,
        rng_seed=678,
        # leak_seep_21=1.0/ns over dt=2 ns is an artificially high rate (gamma*dt=2) chosen to FORCE a
        # deterministic seepage jump for this structural (jump-family/level-record) test; the first-order
        # step is intentionally coarse (mass residual ~1.0), so the CPTP mass-residual guardrail is
        # disabled here. Channel fidelity in this regime is covered by cert_m12_phaseB_convergence.py.
        mass_residual_budget=None,
    )

    assert manifest["verdict"] == "fail"
    assert manifest["passed"] is False
    assert manifest["execution_status"] == "completed"
    assert manifest["certification_status"] == "not_evaluated"
    assert manifest["diagnostic_only"] is True
    execution = manifest["mps_execution"]
    evaluator_diagnostics = execution["evaluator_only_diagnostics"]
    assert evaluator_diagnostics["level_records"] == [[1]]
    assert evaluator_diagnostics["level_record_counts"] == [4]
    assert execution["measurement_records"] == [[1]]
    assert execution["record_counts"] == [4]
    assert evaluator_diagnostics["jump_family_counts"] == {"LEAK_SEEP_21": 4}
    assert "LEAK_SEEP_21" in execution["applied_substeps"][0][
        "nonzero_collapse_operator_families"
    ]
    assert execution["collapse_evolution_policy"] == (
        "joint_first_order_jump_competition_per_microstep"
    )


def test_axis1_mcwf_mps_leakage_requires_declared_multilevel_local_dim():
    builder = CircuitBuilder(num_qubits=1)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            leak_exchange_12_rad_per_ns=math.pi / 20.0,
        )
    )
    builder.idle(0, duration_ns=10.0)
    builder.measure(0, key="m0")
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        trajectory_count=2,
        rng_seed=789,
    )

    assert manifest["verdict"] == "fail"
    assert manifest["passed"] is False
    assert manifest["mcwf_mps_backend_executed"] is False
    assert manifest["blocked_reason"] == (
        "mcwf_leakage_requires_local_dim_at_least_3:LEAK_EXCHANGE_12"
    )
    assert manifest["claims_mcwf_mps_backend_execution"] is False
    assert manifest["claims_production_scalable_backend"] is False


def test_axis1_mcwf_mps_same_substep_leakage_static_zz_and_local_collapse_joint_manifest():
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_static_zz_couplings(((0, 1),))
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            zeta_rad_per_ns=1.0e-3,
            gamma_phi_per_ns=2.0e-4,
            gamma_1_per_ns=3.0e-4,
            leak_seep_21_per_ns=1.0,
        )
    )
    builder.idle((0, 1), duration_ns=2.0)
    builder.measure((0, 1), key=("m0", "m1"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        local_dims=[3, 3],
        initial_levels=[2, 0],
        leaked_readout_b=1.0,
        trajectory_count=3,
        rng_seed=890,
        # leak_seep_21=1.0/ns over dt=2 ns (gamma*dt=2) is an artificially high rate to FORCE a
        # deterministic seepage jump for this same-substep structural manifest test; the first-order step
        # is intentionally coarse, so the CPTP mass-residual guardrail is disabled here (a jump-structure
        # test, not a fidelity test — fidelity is covered by cert_m12_phaseB_convergence.py).
        mass_residual_budget=None,
    )

    assert manifest["verdict"] == "fail"
    assert manifest["passed"] is False
    assert manifest["execution_status"] == "completed"
    assert manifest["certification_status"] == "not_evaluated"
    assert manifest["diagnostic_only"] is True
    execution = manifest["mps_execution"]
    first = execution["applied_substeps"][0]
    assert "ZZ" in first["hamiltonian_operator_families"]
    assert "LEAK_SEEP_21" in first["nonzero_collapse_operator_families"]
    assert "T1" in first["nonzero_collapse_operator_families"]
    assert "T2" in first["nonzero_collapse_operator_families"]
    assert execution["collapse_evolution_policy"] == (
        "joint_first_order_jump_competition_per_microstep"
    )
    assert execution["same_substep_generator_policy"] == (
        "Hamiltonian terms and collapse jump candidates are consumed from the "
        "same compiler-generated carrier substep"
    )
    assert execution["evaluator_only_diagnostics"]["jump_family_counts"] == {
        "LEAK_SEEP_21": 3
    }


def test_axis1_carrier_execution_mcwf_mps_backend_runs_qubit_fixture():
    builder = CircuitBuilder(num_qubits=1)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            gamma_readout_phi_per_ns=0.0,
        )
    )
    builder.h(0)
    builder.reset(0)
    builder.measure(0, key="m0")
    schedule = circuit_ir_to_substep_schedule(builder.build())

    execution = axis1_carrier_execution_manifest(
        schedule,
        execution_backend_contract=AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT,
        execution_backend_options={
            "trajectory_count": 6,
            "rng_seed": 123,
            "microstep_count": 2,
        },
    )

    assert execution["schema"] == "error_coupling_simulator.frontend.carrier_execution.v3"
    assert execution["execution_backend_contract"] == "mcwf_mps_state_record"
    assert execution["representability"] == (
        AXIS1_CARRIER_MCWF_MPS_EXECUTION_REPRESENTABILITY
    )
    assert execution["verdict"] == "pass"
    assert execution["passed"] is True
    assert execution["dense_probe_executed"] is False
    assert execution["qt_mps_backend_executed"] is False
    assert execution["mcwf_mps_backend_executed"] is True
    assert execution["qutip_cuquantum_probe_executed"] is False
    assert execution["state_execution"]["executed"] is True
    assert execution["record_execution"]["executed"] is True
    assert execution["record_execution"]["record_counts"] == [6]
    assert execution["record_execution"]["record_probabilities"] == [1.0]
    assert execution["record_execution"]["jump_sampling"]["max_jumps_per_microstep"] == 1
    assert execution["claims_mcwf_mps_backend_execution"] is True
    assert execution["claims_qt_mps_backend_execution"] is False
    assert execution["claims_production_scalable_backend"] is False
    assert execution["claims_dense_channel_evidence"] is False
    assert execution["claims_dem_decoder_semantics"] is False
    assert execution["claims_axis2_source_timeline"] is False


def test_axis1_carrier_execution_mcwf_mps_mixed_local_dims_runs_without_dense_fallback():
    builder = CircuitBuilder(num_qubits=6)
    builder.declare_static_zz_couplings(((0, 5),))
    builder.idle(tuple(range(6)), duration_ns=75.0)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    execution = axis1_carrier_execution_manifest(
        schedule,
        execution_backend_contract=AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT,
        execution_backend_options={
            "local_dims": [2, 3, 4, 2, 3, 4],
            "trajectory_count": 3,
            "rng_seed": 345,
        },
    )

    assert execution["schema"] == "error_coupling_simulator.frontend.carrier_execution.v3"
    assert execution["execution_backend_contract"] == "mcwf_mps_state_record"
    assert execution["representability"] == (
        AXIS1_CARRIER_MCWF_MPS_EXECUTION_REPRESENTABILITY
    )
    assert execution["verdict"] == "fail"
    assert execution["passed"] is False
    assert execution["blocked_reason"].startswith("dense_jointL_certification:")
    assert execution["local_hilbert_space"]["local_dims"] == [2, 3, 4, 2, 3, 4]
    policy = execution["restricted_acceptance_policy"]
    assert policy["certification_status"] == "unavailable"
    assert policy["diagnostic_only"] is True
    assert policy["accepted_for_restricted_execution"] is False
    assert policy["accepted_as_restricted_overcap_execution"] is False
    assert execution["dense_probe_executed"] is False
    assert execution["qt_mps_backend_executed"] is False
    assert execution["mcwf_mps_backend_executed"] is True
    assert execution["qutip_cuquantum_probe_executed"] is False
    assert execution["state_execution"]["executed"] is True
    assert execution["state_execution"]["mps_truncation_ledger"]["local_dims"] == [
        2,
        3,
        4,
        2,
        3,
        4,
    ]
    assert execution["record_execution"]["executed"] is False
    assert execution["claims_mcwf_mps_backend_execution"] is True
    assert execution["claims_qt_mps_backend_execution"] is False
    assert execution["claims_production_scalable_backend"] is False
    assert execution["claims_dense_channel_evidence"] is False
    assert execution["claims_dem_decoder_semantics"] is False
    assert execution["claims_axis2_source_timeline"] is False


def test_axis1_carrier_execution_mcwf_mps_multilevel_finite_bond_fails_closed():
    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key="m0")
    schedule = circuit_ir_to_substep_schedule(builder.build())

    execution = axis1_carrier_execution_manifest(
        schedule,
        execution_backend_contract=AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT,
        execution_backend_options={
            "local_dims": [3],
            "initial_levels": [2],
            "max_bond": 2,
            "trajectory_count": 3,
            "rng_seed": 456,
        },
    )

    assert execution["schema"] == "error_coupling_simulator.frontend.carrier_execution.v3"
    assert execution["execution_backend_contract"] == "mcwf_mps_state_record"
    assert execution["verdict"] == "fail"
    assert execution["passed"] is False
    assert execution["blocked_reason"] == (
        "mcwf_mps_multilevel_finite_bond_ledger_not_implemented"
    )
    assert execution["mcwf_mps_backend_executed"] is False
    assert execution["claims_mcwf_mps_backend_execution"] is False
    assert execution["claims_production_scalable_backend"] is False


def test_axis1_carrier_program_preserves_thermal_excitation_context_terms():
    builder = CircuitBuilder(num_qubits=3)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            include_thermal_excitation=True,
            gamma_up_per_ns=2.0e-4,
        )
    )
    builder.idle((0, 1, 2), duration_ns=25.0)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    carrier = axis1_carrier_program_manifest(schedule)

    idle = carrier["program"]["substeps"][0]
    assert idle["route"] == "dense_oracle_available"
    t1_up_terms = [
        term for term in idle["terms"] if term["operator_family"] == "T1_UP"
    ]
    assert [term["support"] for term in t1_up_terms] == [[0], [1], [2]]
    assert [term["coefficient"] for term in t1_up_terms] == pytest.approx(
        [(2.0e-4) ** 0.5] * 3
    )
    assert all(
        term["coefficient_source"] == "axis1_local_lindblad_context"
        for term in t1_up_terms
    )


def test_axis1_carrier_program_lowers_public_qutrit_leakage_context_terms():
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            leak_exchange_12_rad_per_ns=1.25e-2,
            leak_seep_21_per_ns=2.5e-3,
            leak_heat_12_per_ns=4.0e-3,
        )
    )
    builder.idle((0, 1), duration_ns=50.0)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    carrier = axis1_carrier_program_manifest(
        schedule,
        backend_contract=AXIS1_CARRIER_MCWF_MPS_BACKEND_CONTRACT,
    )

    assert schedule.source_kind == "circuit_ir"
    assert all(substep.generated_by_compiler for substep in schedule.substeps)
    assert carrier["axis1_local_lindblad_context"]["include_leakage"] is True
    idle = carrier["program"]["substeps"][0]
    assert idle["substep_kind"] == "idle"
    leak_terms = [
        (
            term["operator_family"],
            term["kind"],
            term["support"],
            term["coefficient"],
            term["coefficient_source"],
        )
        for term in idle["terms"]
        if term["operator_family"].startswith("LEAK_")
    ]
    assert leak_terms == [
        (
            "LEAK_EXCHANGE_12",
            "hamiltonian",
            [0],
            1.25e-2,
            "axis1_local_lindblad_context",
        ),
        (
            "LEAK_SEEP_21",
            "collapse",
            [0],
            pytest.approx((2.5e-3) ** 0.5),
            "axis1_local_lindblad_context",
        ),
        (
            "LEAK_HEAT_12",
            "collapse",
            [0],
            pytest.approx((4.0e-3) ** 0.5),
            "axis1_local_lindblad_context",
        ),
        (
            "LEAK_EXCHANGE_12",
            "hamiltonian",
            [1],
            1.25e-2,
            "axis1_local_lindblad_context",
        ),
        (
            "LEAK_SEEP_21",
            "collapse",
            [1],
            pytest.approx((2.5e-3) ** 0.5),
            "axis1_local_lindblad_context",
        ),
        (
            "LEAK_HEAT_12",
            "collapse",
            [1],
            pytest.approx((4.0e-3) ** 0.5),
            "axis1_local_lindblad_context",
        ),
    ]
    assert all(
        term["provenance"]["metadata_visibility"]
        == "public_axis1_instantaneous_context_not_axis2_source"
        for term in idle["terms"]
        if term["operator_family"].startswith("LEAK_")
    )


def test_axis1_carrier_program_lowers_two_site_leakage_transport_from_two_qubit_substep():
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            leak_exchange_11_02_rad_per_ns=1.25e-2,
            leak_mobility_12_21_rad_per_ns=2.5e-2,
            leak_transport_30_12_rad_per_ns=3.5e-2,
            leak_transport_31_22_rad_per_ns=4.5e-2,
        )
    )
    builder.cz((0, 1))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    carrier = axis1_carrier_program_manifest(
        schedule,
        backend_contract=AXIS1_CARRIER_MCWF_MPS_BACKEND_CONTRACT,
    )

    assert all(substep.generated_by_compiler for substep in schedule.substeps)
    twoq = carrier["program"]["substeps"][0]
    assert twoq["substep_kind"] == "two_qubit_gate"
    leak_terms = [
        (
            term["operator_family"],
            term["kind"],
            term["support"],
            term["coefficient"],
            term["coefficient_source"],
            term["provenance"]["orientation_policy"],
        )
        for term in twoq["terms"]
        if term["operator_family"] in {
            "LEAK_EXCHANGE_11_02",
            "LEAK_MOBILITY_12_21",
            "LEAK_TRANSPORT_30_12",
            "LEAK_TRANSPORT_31_22",
        }
    ]
    assert leak_terms == [
        (
            "LEAK_EXCHANGE_11_02",
            "hamiltonian",
            [0, 1],
            1.25e-2,
            "axis1_local_lindblad_context",
            "ordered_frontend_two_qubit_operation_targets",
        ),
        (
            "LEAK_MOBILITY_12_21",
            "hamiltonian",
            [0, 1],
            2.5e-2,
            "axis1_local_lindblad_context",
            "ordered_frontend_two_qubit_operation_targets",
        ),
        (
            "LEAK_TRANSPORT_30_12",
            "hamiltonian",
            [0, 1],
            3.5e-2,
            "axis1_local_lindblad_context",
            "ordered_frontend_two_qubit_operation_targets",
        ),
        (
            "LEAK_TRANSPORT_31_22",
            "hamiltonian",
            [0, 1],
            4.5e-2,
            "axis1_local_lindblad_context",
            "ordered_frontend_two_qubit_operation_targets",
        ),
    ]
    assert carrier["claims_dense_channel_evidence"] is False
    assert carrier["claims_axis2_source_timeline"] is False


def test_axis1_mcwf_mps_runs_qutrit_two_site_leakage_exchange_from_public_context():
    dt_ns = _two_qubit_dt_ns()
    theta = 7.7
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            leak_exchange_11_02_rad_per_ns=theta / dt_ns,
        )
    )
    builder.cz((0, 1))
    builder.measure((0, 1), key=("m0", "m1"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        local_dims=[3, 3],
        initial_levels=[1, 1],
        leaked_readout_b=1.0,
        trajectory_count=128,
        rng_seed=901,
    )

    assert manifest["verdict"] == "pass"
    execution = manifest["mps_execution"]
    evaluator_diagnostics = execution["evaluator_only_diagnostics"]
    level_probabilities = {
        tuple(record): probability
        for record, probability in zip(
            evaluator_diagnostics["level_records"],
            evaluator_diagnostics["level_record_probabilities"],
            strict=True,
        )
    }
    assert level_probabilities[(0, 2)] >= 0.85
    assert "LEAK_EXCHANGE_11_02" in execution["applied_substeps"][0][
        "hamiltonian_operator_families"
    ]
    assert execution["hamiltonian_evolution_policy"] == (
        "connected_support_cluster_hamiltonian_sum_matrix_exp"
    )
    assert execution["finite_step_policy"]["name"] == (
        "connected_support_cluster_hamiltonian_sum_first_order_mcwf_split_v2"
    )
    assert execution["finite_step_policy"]["hamiltonian_grouping_policy"] == (
        "connected_support_cluster_terms_are_summed_before_matrix_exp"
    )
    assert execution["claims_dense_channel_evidence"] is False
    assert execution["claims_axis2_source_timeline"] is False


def test_axis1_mcwf_mps_hamiltonian_group_sums_ctrl_cz_and_two_site_transport():
    dt_ns = _two_qubit_dt_ns()
    theta = 0.37
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            leak_exchange_11_02_rad_per_ns=theta / dt_ns,
        )
    )
    builder.cz((0, 1))
    schedule = circuit_ir_to_substep_schedule(builder.build())
    carrier = axis1_carrier_program_manifest(
        schedule,
        backend_contract=AXIS1_CARRIER_MCWF_MPS_BACKEND_CONTRACT,
    )
    substep = carrier["program"]["substeps"][0]

    groups = _hamiltonian_group_gates(
        substep,
        dt_ns=dt_ns,
        local_dims=(3, 3),
        device="cuda",
    )

    assert len(groups) == 1
    group = groups[0]
    assert group["support"] == (0, 1)
    assert group["term"]["operator_family"] == "H_CLUSTER[CTRL_CZ+LEAK_EXCHANGE_11_02]"

    h_ref = torch.zeros((9, 9), dtype=torch.complex128, device="cuda")
    idx_11 = 1 * 3 + 1
    idx_02 = 0 * 3 + 2
    h_ref[idx_11, idx_11] = math.pi / dt_ns
    h_ref[idx_11, idx_02] = theta / dt_ns
    h_ref[idx_02, idx_11] = theta / dt_ns
    expected = torch.linalg.matrix_exp((-1.0j * dt_ns) * h_ref)
    actual = group["gate"]
    assert torch.max(torch.abs(actual - expected)).item() <= 5.0e-12

    ctrl = torch.eye(9, dtype=torch.complex128, device="cuda")
    ctrl[idx_11, idx_11] = -1.0
    leak = torch.eye(9, dtype=torch.complex128, device="cuda")
    c = math.cos(theta)
    s = math.sin(theta)
    leak[idx_11, idx_11] = c
    leak[idx_02, idx_02] = c
    leak[idx_11, idx_02] = -1.0j * s
    leak[idx_02, idx_11] = -1.0j * s
    old_sequential = leak @ ctrl
    assert torch.max(torch.abs(actual - old_sequential)).item() >= 1.0e-2


def test_axis1_mcwf_mps_conditional_leaked_neighbor_phase_lowers_and_groups():
    dt_ns = _two_qubit_dt_ns()
    left_phase = 0.23
    right_phase = 0.41
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            leak_cond_phase_left2_right_z_rad_per_ns=left_phase / dt_ns,
            leak_cond_phase_left_z_right2_rad_per_ns=right_phase / dt_ns,
        )
    )
    builder.cz((0, 1))
    schedule = circuit_ir_to_substep_schedule(builder.build())
    carrier = axis1_carrier_program_manifest(
        schedule,
        backend_contract=AXIS1_CARRIER_MCWF_MPS_BACKEND_CONTRACT,
    )
    substep = carrier["program"]["substeps"][0]

    phase_terms = [
        term for term in substep["terms"]
        if term["operator_family"].startswith("LEAK_COND_PHASE")
    ]
    assert [
        (
            term["operator_family"],
            term["support"],
            term["coefficient"],
            term["provenance"]["orientation_policy"],
        )
        for term in phase_terms
    ] == [
        (
            "LEAK_COND_PHASE_LEFT2_RIGHTZ",
            [0, 1],
            left_phase / dt_ns,
            "ordered_frontend_two_qubit_operation_targets",
        ),
        (
            "LEAK_COND_PHASE_LEFTZ_RIGHT2",
            [0, 1],
            right_phase / dt_ns,
            "ordered_frontend_two_qubit_operation_targets",
        ),
    ]

    groups = _hamiltonian_group_gates(
        substep,
        dt_ns=dt_ns,
        local_dims=(3, 3),
        device="cuda",
    )
    assert len(groups) == 1
    h_ref = torch.zeros((9, 9), dtype=torch.complex128, device="cuda")
    h_ref[1 * 3 + 1, 1 * 3 + 1] = math.pi / dt_ns
    h_ref[2 * 3 + 0, 2 * 3 + 0] = left_phase / dt_ns
    h_ref[2 * 3 + 1, 2 * 3 + 1] = -left_phase / dt_ns
    h_ref[0 * 3 + 2, 0 * 3 + 2] = right_phase / dt_ns
    h_ref[1 * 3 + 2, 1 * 3 + 2] = -right_phase / dt_ns
    expected = torch.linalg.matrix_exp((-1.0j * dt_ns) * h_ref)
    assert torch.max(torch.abs(groups[0]["gate"] - expected)).item() <= 5.0e-12
    assert groups[0]["term"]["operator_family"] == (
        "H_CLUSTER[CTRL_CZ+LEAK_COND_PHASE_LEFT2_RIGHTZ+"
        "LEAK_COND_PHASE_LEFTZ_RIGHT2]"
    )


def test_axis1_mcwf_mps_conditional_phase_requires_declared_leakage_level():
    dt_ns = _two_qubit_dt_ns()
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            leak_cond_phase_left2_right_z_rad_per_ns=0.25 / dt_ns,
        )
    )
    builder.cz((0, 1))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    blocked = axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        local_dims=[2, 3],
        trajectory_count=2,
        rng_seed=905,
    )

    assert blocked["verdict"] == "fail"
    assert blocked["blocked_reason"] == (
        "mcwf_leakage_requires_declared_local_levels:"
        "LEAK_COND_PHASE_LEFT2_RIGHTZ"
    )


def test_axis1_mcwf_mps_two_site_leakage_transport_fails_closed_on_qubit_dims():
    dt_ns = _two_qubit_dt_ns()
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            leak_exchange_11_02_rad_per_ns=math.pi / (2.0 * dt_ns),
        )
    )
    builder.cz((0, 1))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        trajectory_count=2,
        rng_seed=902,
    )

    assert manifest["verdict"] == "fail"
    assert manifest["passed"] is False
    assert manifest["mcwf_mps_backend_executed"] is False
    assert manifest["blocked_reason"] == (
        "mcwf_leakage_requires_declared_local_levels:LEAK_EXCHANGE_11_02"
    )


def test_axis1_mcwf_mps_runs_ququart_transport_only_with_declared_level_three():
    dt_ns = _two_qubit_dt_ns()
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            leak_transport_30_12_rad_per_ns=math.pi / (2.0 * dt_ns),
        )
    )
    builder.cz((0, 1))
    builder.measure((0, 1), key=("m0", "m1"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    blocked = axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        local_dims=[3, 3],
        initial_levels=[1, 2],
        trajectory_count=2,
        rng_seed=903,
    )
    assert blocked["verdict"] == "fail"
    assert blocked["blocked_reason"] == (
        "mcwf_leakage_requires_declared_local_levels:LEAK_TRANSPORT_30_12"
    )

    manifest = axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        local_dims=[4, 3],
        initial_levels=[1, 2],
        leaked_readout_b=1.0,
        trajectory_count=4,
        rng_seed=904,
    )

    assert manifest["verdict"] == "pass"
    execution = manifest["mps_execution"]
    evaluator_diagnostics = execution["evaluator_only_diagnostics"]
    assert evaluator_diagnostics["level_records"] == [[3, 0]]
    assert evaluator_diagnostics["level_record_counts"] == [4]
    assert "LEAK_TRANSPORT_30_12" in execution["applied_substeps"][0][
        "hamiltonian_operator_families"
    ]


def test_dense_axis1_evidence_refuses_to_ignore_public_qutrit_leakage_context(
    monkeypatch: pytest.MonkeyPatch,
):
    from error_coupling_simulator.frontend import (
        axis1_carrier_execution as carrier_execution,
    )

    builder = CircuitBuilder(num_qubits=1)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            leak_exchange_12_rad_per_ns=math.pi / 20.0,
        )
    )
    builder.idle(0, duration_ns=10.0)
    builder.measure(0, key="m0")
    schedule = circuit_ir_to_substep_schedule(builder.build())

    carrier = axis1_carrier_program_manifest(
        schedule,
        backend_contract=AXIS1_CARRIER_MCWF_MPS_BACKEND_CONTRACT,
    )
    assert carrier["axis1_local_lindblad_context"]["include_leakage"] is True
    assert any(
        term["operator_family"] == "LEAK_EXCHANGE_12"
        for step in carrier["program"]["substeps"]
        for term in step["terms"]
    )

    with pytest.raises(ValueError):
        axis1_substep_channel_evidence_manifest(schedule)
    with pytest.raises(ValueError):
        axis1_state_evolution_evidence_manifest(schedule)
    with pytest.raises(ValueError):
        axis1_measurement_record_evidence_manifest(schedule)

    dense_child_calls = []
    monkeypatch.setattr(
        carrier_execution,
        "axis1_state_evolution_evidence_manifest",
        lambda *_args, **_kwargs: dense_child_calls.append("state"),
    )
    monkeypatch.setattr(
        carrier_execution,
        "axis1_measurement_record_evidence_manifest",
        lambda *_args, **_kwargs: dense_child_calls.append("record"),
    )
    with pytest.raises(ValueError):
        axis1_carrier_execution_manifest(schedule)
    assert dense_child_calls == []


def test_axis1_qutrit_leakage_oracle_certification_matches_declared_superop():
    builder = CircuitBuilder(num_qubits=1)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            leak_exchange_12_rad_per_ns=3.1e-2,
            leak_seep_21_per_ns=4.0e-3,
            leak_heat_12_per_ns=2.0e-3,
        )
    )
    builder.idle(0, duration_ns=7.0)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    cert = axis1_qutrit_leakage_oracle_certification_manifest(schedule)

    assert cert["schema"] == AXIS1_QUTRIT_LEAKAGE_CERTIFICATION_SCHEMA
    assert cert["representability"] == (
        AXIS1_QUTRIT_LEAKAGE_CERTIFICATION_REPRESENTABILITY
    )
    assert cert["verdict"] == "pass"
    assert cert["passed"] is True
    assert cert["claims_dense_qutrit_oracle_certification"] is True
    assert cert["claims_dense_channel_payload"] is False
    assert cert["claims_axis1_full_completion"] is False
    assert cert["claims_axis2_source_timeline"] is False
    assert cert["comparison_outcome_is_metric"] is False

    conversion = cert["parameter_conversion"]
    assert conversion["theta"] == pytest.approx(3.1e-2 * 7.0)
    assert conversion["g_seep"] == pytest.approx(4.0e-3 * 7.0)
    assert conversion["g_heat"] == pytest.approx(2.0e-3 * 7.0)
    assert conversion["policy"] == "per_ns_generator_rates_times_dt_ns"
    assert cert["oracle_comparison"]["max_abs_superop_diff"] <= 2.0e-12
    assert cert["oracle_comparison"]["passed"] is True

    control = cert["wrong_unit_negative_control"]
    assert control["role"] == "negative_control_not_metric"
    assert control["wrong_policy"] == "dimensionless_values_without_dt"
    assert control["passed"] is True
    assert control["max_abs_superop_diff"] > 1.0e-3


def test_axis1_qutrit_leakage_oracle_certification_rejects_multi_site_slice():
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            leak_exchange_12_rad_per_ns=3.1e-2,
        )
    )
    builder.idle((0, 1), duration_ns=7.0)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    with pytest.raises(ValueError, match="exactly one leakage-certified site"):
        axis1_qutrit_leakage_oracle_certification_manifest(schedule)


def test_axis1_two_site_leakage_hamiltonian_certification_matches_dense_oracle():
    dt_ns = _two_qubit_dt_ns()
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            leak_exchange_11_02_rad_per_ns=0.37 / dt_ns,
            leak_cond_phase_left2_right_z_rad_per_ns=0.23 / dt_ns,
            leak_cond_phase_left_z_right2_rad_per_ns=0.41 / dt_ns,
        )
    )
    builder.cz((0, 1))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    cert = axis1_two_site_leakage_hamiltonian_certification_manifest(
        schedule,
        local_dims=[3, 3],
    )

    assert cert["schema"] == AXIS1_TWO_SITE_LEAKAGE_HAMILTONIAN_CERTIFICATION_SCHEMA
    assert cert["representability"] == (
        AXIS1_TWO_SITE_LEAKAGE_HAMILTONIAN_CERTIFICATION_REPRESENTABILITY
    )
    assert cert["verdict"] == "pass"
    assert cert["passed"] is True
    assert cert["claims_dense_two_site_leakage_oracle_certification"] is True
    assert cert["claims_dense_channel_payload"] is False
    assert cert["claims_dense_channel_evidence"] is False
    assert cert["claims_axis1_full_completion"] is False
    assert cert["comparison_outcome_is_metric"] is False
    assert cert["certified_substep"]["term_families"] == [
        "CTRL_CZ",
        "LEAK_EXCHANGE_11_02",
        "LEAK_COND_PHASE_LEFT2_RIGHTZ",
        "LEAK_COND_PHASE_LEFTZ_RIGHT2",
    ]
    assert cert["certified_substep"]["lowered_group_family"] == (
        "H_CLUSTER[CTRL_CZ+LEAK_EXCHANGE_11_02+"
        "LEAK_COND_PHASE_LEFT2_RIGHTZ+LEAK_COND_PHASE_LEFTZ_RIGHT2]"
    )
    assert cert["oracle_comparison"]["max_abs_unitary_diff"] <= 2.0e-12
    assert cert["oracle_comparison"]["comparison_outcome_is_metric"] is False
    assert cert["wrong_unit_negative_control"]["passed"] is True
    assert cert["wrong_unit_negative_control"]["max_abs_unitary_diff"] > 1.0e-3


def test_axis1_two_site_leakage_hamiltonian_certification_checks_ququart_levels():
    dt_ns = _two_qubit_dt_ns()
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            leak_transport_30_12_rad_per_ns=0.21 / dt_ns,
        )
    )
    builder.cz((0, 1))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    with pytest.raises(ValueError, match="outside local_dims"):
        axis1_two_site_leakage_hamiltonian_certification_manifest(
            schedule,
            local_dims=[3, 3],
        )

    cert = axis1_two_site_leakage_hamiltonian_certification_manifest(
        schedule,
        local_dims=[4, 3],
    )

    assert cert["verdict"] == "pass"
    assert cert["certified_substep"]["leakage_term_families"] == [
        "LEAK_TRANSPORT_30_12"
    ]
    assert cert["certified_substep"]["local_dims"] == [4, 3]
    assert cert["oracle_comparison"]["max_abs_unitary_diff"] <= 2.0e-12


def test_axis1_carrier_program_preserves_over_cap_thermal_excitation_context_terms():
    builder = CircuitBuilder(num_qubits=6)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            include_thermal_excitation=True,
            gamma_up_per_ns=2.0e-4,
        )
    )
    builder.declare_static_zz_couplings(((0, 5),))
    builder.idle(tuple(range(6)), duration_ns=75.0)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    carrier = axis1_carrier_program_manifest(schedule)

    assert carrier["requires_scalable_backend"] is True
    idle = carrier["program"]["substeps"][0]
    assert idle["route"] == "scalable_required"
    t1_up_terms = [
        term for term in idle["terms"] if term["operator_family"] == "T1_UP"
    ]
    assert [term["support"] for term in t1_up_terms] == [[0], [1], [2], [3], [4], [5]]
    assert [term["coefficient"] for term in t1_up_terms] == pytest.approx(
        [(2.0e-4) ** 0.5] * 6
    )


def test_axis1_over_cap_static_readout_refuses_pair_fallback_that_drops_edges():
    builder = CircuitBuilder(num_qubits=6)
    builder.declare_static_zz_couplings(((0, 5),))
    builder.measure(tuple(range(6)), key=tuple(f"m{i}" for i in range(6)), duration_ns=250.0)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    plan = build_axis1_schedule_selection_plan(schedule)
    assert plan.static_zz_pairs == ((0, 5),)
    assert plan.selections == ()
    with pytest.raises(ValueError, match="requires at least one mechanism selection"):
        axis1_substep_channel_evidence_manifest(schedule)


def test_axis1_carrier_program_routes_over_cap_static_readout_with_record_boundary():
    builder = CircuitBuilder(num_qubits=6)
    builder.declare_static_zz_couplings(((0, 5),))
    builder.measure(tuple(range(6)), key=tuple(f"m{i}" for i in range(6)), duration_ns=250.0)
    builder.detector("d05", xor=("m0", "m5"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_carrier_program_manifest(schedule)

    assert manifest["requires_scalable_backend"] is True
    assert manifest["claims_dem_decoder_semantics"] is False
    readout = manifest["program"]["substeps"][0]
    assert readout["route"] == "scalable_required"
    assert readout["substep_kind"] == "measurement"
    assert readout["support"] == [0, 1, 2, 3, 4, 5]
    assert readout["coupling_edges"] == [[0, 5]]
    assert readout["dt_ns"] == 250.0
    assert readout["operation_records"][0]["measurement_keys"] == [
        "m0",
        "m1",
        "m2",
        "m3",
        "m4",
        "m5",
    ]
    assert manifest["program"]["claims_dem_decoder_semantics"] is False

    boundary_terms = [
        term for term in readout["terms"] if term["kind"] == "measurement_boundary"
    ]
    assert [term["support"] for term in boundary_terms] == [[0], [1], [2], [3], [4], [5]]
    assert all(term["coefficient"] is None for term in boundary_terms)
    assert all(
        term["coefficient_source"] == "projective_record_boundary"
        for term in boundary_terms
    )
    rd_terms = [term for term in readout["terms"] if term["operator_family"] == "RD"]
    assert [term["support"] for term in rd_terms] == [[0], [1], [2], [3], [4], [5]]


def test_axis1_carrier_execution_probe_consumes_program_and_matches_jointL_state_record():
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_static_zz_couplings(((0, 1),))
    builder.h(0)
    builder.tick()
    builder.cz((0, 1))
    builder.tick()
    builder.measure((0, 1), key=("m0", "m1"))
    builder.detector("d0", xor=("m0", "m1"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    program = axis1_carrier_program_manifest(schedule)
    state = axis1_state_evolution_evidence_manifest(schedule)
    record = axis1_measurement_record_evidence_manifest(schedule)
    execution = axis1_carrier_execution_manifest(schedule)

    assert execution["schema"] == "error_coupling_simulator.frontend.carrier_execution.v3"
    assert execution["verdict"] == "pass"
    assert execution["passed"] is True
    assert execution["execution_backend_contract"] == "dense_jointL_probe"
    assert execution["gpu_required"] is True
    assert execution["device"].startswith("cuda")
    assert execution["carrier_program"]["content_hash"] == program["content_hash"]
    assert execution["carrier_program"]["requires_scalable_backend"] is False
    assert execution["carrier_program"]["routes"] == [
        "boundary_only",
        "dense_oracle_available",
    ]
    assert execution["claims_dense_channel_evidence"] is False
    assert execution["claims_dem_decoder_semantics"] is False
    assert execution["claims_axis2_source_timeline"] is False
    assert execution["claims_scalable_backend_completed"] is False

    assert execution["state_execution"]["executed"] is True
    assert execution["state_execution"]["evidence_content_hash"] == state["content_hash"]
    assert execution["state_execution"]["final_z_probabilities"] == (
        state["state_evolution"]["final_z_probabilities"]
    )
    assert execution["state_execution"]["joint_generator_semantics"] == (
        "single_joint_generator_expm"
    )
    assert execution["record_execution"]["executed"] is True
    assert execution["record_execution"]["evidence_content_hash"] == record["content_hash"]
    assert execution["record_execution"]["measurement_records"] == (
        record["record_evidence"]["measurement_records"]
    )
    assert execution["record_execution"]["record_probabilities"] == (
        record["record_evidence"]["record_probabilities"]
    )
    assert execution["record_execution"]["detector_records"] == (
        record["record_evidence"]["detector_records"]
    )
    assert execution["record_execution"]["claims_b8_artifact"] is False
    assert execution["record_execution"]["claims_decoder_integration"] is False
    assert "content_hash" in execution


def test_axis1_carrier_execution_probe_fails_closed_on_over_cap_static_route():
    builder = CircuitBuilder(num_qubits=6)
    builder.declare_static_zz_couplings(((0, 5), (1, 4)))
    builder.idle(tuple(range(6)), duration_ns=1.0e-6)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    execution = axis1_carrier_execution_manifest(schedule)

    assert execution["schema"] == "error_coupling_simulator.frontend.carrier_execution.v3"
    assert execution["verdict"] == "fail"
    assert execution["passed"] is False
    assert execution["execution_backend_contract"] == "dense_jointL_probe"
    assert execution["carrier_program"]["requires_scalable_backend"] is True
    assert execution["blocked_reason"] == "requires_scalable_backend_extension"
    assert execution["dense_probe_executed"] is False
    assert execution["state_execution"] is None
    assert execution["record_execution"] is None
    assert execution["claims_dense_channel_evidence"] is False
    assert execution["claims_dem_decoder_semantics"] is False
    assert execution["claims_axis2_source_timeline"] is False
    assert execution["claims_scalable_backend_completed"] is False


def test_axis1_carrier_execution_qutip_backend_executes_over_cap_static_idle():
    builder = CircuitBuilder(num_qubits=6)
    builder.declare_static_zz_couplings(((0, 5), (1, 4)))
    builder.idle(tuple(range(6)), duration_ns=1.0e-6)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    execution = axis1_carrier_execution_manifest(
        schedule,
        execution_backend_contract=(
            AXIS1_CARRIER_QUTIP_RESTRICTED_EXECUTION_BACKEND_CONTRACT
        ),
    )

    assert execution["schema"] == "error_coupling_simulator.frontend.carrier_execution.v3"
    assert execution["verdict"] == "pass"
    assert execution["passed"] is True
    assert execution["execution_backend_contract"] == (
        "qutip_cuquantum_restricted_state_record_probe"
    )
    assert execution["representability"] == (
        "axis1_carrier_execution_qutip_cuquantum_restricted_no_production_scalable"
    )
    assert execution["carrier_program"]["backend_contract"] == "qutip_cuquantum_probe"
    assert execution["carrier_program"]["requires_scalable_backend"] is True
    assert execution["carrier_program"]["routes"] == ["scalable_required"]
    assert execution["dense_probe_executed"] is False
    assert execution["qutip_cuquantum_probe_executed"] is True
    assert execution["claims_qutip_cuquantum_execution"] is True
    assert execution["claims_qt_mps_backend_execution"] is False
    assert execution["claims_production_scalable_backend"] is False
    assert execution["claims_scalable_backend_completed"] is False
    assert execution["claims_dense_channel_evidence"] is False
    assert execution["claims_dem_decoder_semantics"] is False
    assert execution["claims_axis2_source_timeline"] is False

    state = execution["state_execution"]
    assert state["executed"] is True
    assert state["representability"] == "axis1_qutip_cuquantum_trajectory_probe_no_record_execution"
    assert state["solver"] == "qutip.mcsolve"
    assert state["ntraj"] == 1
    assert state["final_norm"] == pytest.approx(1.0, abs=1.0e-8)
    assert state["final_z_probabilities"][0] >= 1.0 - 1.0e-8
    assert max(state["final_z_probabilities"][1:]) <= 1.0e-8
    assert state["applied_substeps"][0]["route"] == "scalable_required"
    assert state["applied_substeps"][0]["hamiltonian_operator_families"] == [
        "ZZ",
        "ZZ",
    ]
    assert execution["record_execution"] == {
        "executed": False,
        "reason": "schedule_has_no_measurement_substep",
    }
    assert execution["qutip_probe"]["representability"] == (
        "axis1_qutip_cuquantum_trajectory_probe_no_record_execution"
    )


def test_axis1_carrier_execution_qutip_backend_records_over_cap_h_readout():
    builder = CircuitBuilder(num_qubits=6)
    builder.declare_static_zz_couplings(((0, 5),))
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
        )
    )
    builder.h(0)
    builder.tick()
    builder.measure(
        tuple(range(6)),
        key=tuple(f"m{i}" for i in range(6)),
        duration_ns=1.0e-6,
    )
    builder.detector("d05", xor=("m0", "m5"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    execution = axis1_carrier_execution_manifest(
        schedule,
        execution_backend_contract=(
            AXIS1_CARRIER_QUTIP_RESTRICTED_EXECUTION_BACKEND_CONTRACT
        ),
    )

    assert execution["verdict"] == "pass"
    assert execution["passed"] is True
    assert execution["dense_probe_executed"] is False
    assert execution["qutip_cuquantum_probe_executed"] is True
    assert execution["claims_production_scalable_backend"] is False
    assert execution["claims_qt_mps_backend_execution"] is False
    assert execution["claims_dense_channel_evidence"] is False
    assert execution["claims_dem_decoder_semantics"] is False
    assert execution["claims_axis2_source_timeline"] is False

    record = execution["record_execution"]
    assert record["executed"] is True
    assert record["representability"] == (
        "axis1_qutip_cuquantum_record_probe_restricted_no_b8_no_decoder"
    )
    assert record["measurement_keys"] == ["m0", "m1", "m2", "m3", "m4", "m5"]
    p_m0_zero = sum(
        probability
        for bits, probability in zip(
            record["measurement_records"],
            record["record_probabilities"],
            strict=True,
        )
        if bits[0] == 0
    )
    p_m0_one = sum(
        probability
        for bits, probability in zip(
            record["measurement_records"],
            record["record_probabilities"],
            strict=True,
        )
        if bits[0] == 1
    )
    leakage_to_other_readout_bits = sum(
        probability
        for bits, probability in zip(
            record["measurement_records"],
            record["record_probabilities"],
            strict=True,
        )
        if any(bits[index] for index in range(1, 6))
    )
    assert [p_m0_zero, p_m0_one] == pytest.approx([0.5, 0.5], abs=1.0e-8)
    assert leakage_to_other_readout_bits <= 1.0e-8
    assert record["applied_substeps"][0]["hamiltonian_operator_families"] == [
        "CTRL_H",
        "ZZ",
    ]
    assert record["claims_b8_artifact"] is False
    assert record["claims_decoder_integration"] is False
    assert record["claims_dense_channel_evidence"] is False
    assert record["claims_axis2_source_timeline"] is False
    assert record["claims_production_scalable_backend"] is False


def test_axis1_carrier_execution_qt_mps_backend_records_over_cap_h_readout():
    builder = CircuitBuilder(num_qubits=6)
    builder.declare_static_zz_couplings(((0, 5),))
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            gamma_readout_phi_per_ns=0.0,
        )
    )
    builder.h(0)
    builder.tick()
    builder.measure(
        tuple(range(6)),
        key=tuple(f"m{i}" for i in range(6)),
        duration_ns=1.0e-6,
    )
    builder.detector("d05", xor=("m0", "m5"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    execution = axis1_carrier_execution_manifest(
        schedule,
        execution_backend_contract=(
            AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT
        ),
    )

    assert execution["schema"] == "error_coupling_simulator.frontend.carrier_execution.v3"
    assert execution["execution_status"] == "completed"
    assert execution["certification_status"] == "unavailable"
    assert execution["diagnostic_only"] is True
    assert execution["blocked_reason"] == (
        "overcap_independent_record_oracle_unavailable"
    )
    assert execution["verdict"] == "fail"
    assert execution["passed"] is False
    assert execution["execution_backend_contract"] == "qt_mps_state_record"
    assert execution["representability"] == (
        "axis1_carrier_execution_qt_mps_restricted_no_production_scalable"
    )
    assert execution["carrier_program"]["backend_contract"] == "qt_mps_state_record"
    assert execution["carrier_program"]["requires_scalable_backend"] is True
    assert execution["carrier_program"]["routes"] == ["scalable_required"]
    assert execution["dense_probe_executed"] is False
    assert execution["qt_mps_backend_executed"] is True
    assert execution["qutip_cuquantum_probe_executed"] is False
    assert execution["claims_qt_mps_backend_execution"] is True
    assert execution["claims_qutip_cuquantum_execution"] is False
    assert execution["claims_production_scalable_backend"] is False
    assert execution["claims_scalable_backend_completed"] is False
    assert execution["claims_exact_joint_lindblad_generator"] is False
    assert execution["claims_dense_channel_evidence"] is False
    assert execution["claims_dem_decoder_semantics"] is False
    assert execution["claims_axis2_source_timeline"] is False

    qt_mps = execution["qt_mps_execution"]
    assert qt_mps["schema"] == "error_coupling_simulator.frontend.qt_mps_restricted_execution.v6"
    assert qt_mps["execution_status"] == "completed"
    assert qt_mps["certification_status"] == "unavailable"
    assert qt_mps["diagnostic_only"] is True
    assert qt_mps["accepted_for_restricted_execution"] is False
    assert qt_mps["accepted_for_production_scalable_backend"] is False
    assert qt_mps["claims_exact_joint_lindblad_generator"] is False
    assert execution["restricted_acceptance_policy"][
        "accepted_for_production_scalable_backend"
    ] is False
    assert execution["restricted_acceptance_policy"]["overcap"][
        "accepted_as_restricted_overcap_execution"
    ] is False

    record = execution["record_execution"]
    assert record["executed"] is True
    assert record["representability"] == (
        "axis1_qt_mps_restricted_control_hamiltonian_z_record_product_channel"
    )
    assert record["measurement_keys"] == ["m0", "m1", "m2", "m3", "m4", "m5"]
    assert record["claims_b8_artifact"] is False
    assert record["claims_decoder_integration"] is False
    p_m0_zero = sum(
        probability
        for bits, probability in zip(
            record["measurement_records"],
            record["record_probabilities"],
            strict=True,
        )
        if bits[0] == 0
    )
    p_m0_one = sum(
        probability
        for bits, probability in zip(
            record["measurement_records"],
            record["record_probabilities"],
            strict=True,
        )
        if bits[0] == 1
    )
    assert [p_m0_zero, p_m0_one] == pytest.approx([0.5, 0.5], abs=1.0e-8)


def test_axis1_carrier_execution_qt_mps_backend_accepts_declared_options():
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            gamma_readout_phi_per_ns=0.0,
        )
    )
    builder.h((0, 1))
    builder.tick()
    builder.cz((0, 1))
    builder.tick()
    builder.measure((0, 1), key=("m0", "m1"), duration_ns=1.0e-6)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    execution = axis1_carrier_execution_manifest(
        schedule,
        execution_backend_contract=(
            AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT
        ),
        execution_backend_options={
            "max_bond": 2,
            "microstep_count": 2,
            "finite_step_order": "strang_second_order",
        },
    )

    assert execution["verdict"] == "pass"
    assert execution["passed"] is True
    assert execution["execution_backend_options"] == {
        "max_bond": 2,
        "microstep_count": 2,
        "finite_step_order": "strang_second_order",
    }
    state = execution["state_execution"]
    assert state["finite_step_policy"]["order"] == "strang_second_order"
    assert state["finite_step_policy"]["microstep_count"] == 2
    assert state["mps_truncation_ledger"]["max_bond"] == 2
    assert state["mps_truncation_ledger"][
        "accepted_as_exact_bond_representation"
    ] is True
    assert execution["restricted_acceptance_policy"][
        "accepted_for_production_scalable_backend"
    ] is False


def test_axis1_carrier_execution_qt_mps_backend_rejects_unknown_option(
    monkeypatch: pytest.MonkeyPatch,
):
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule = _joint_channel_schedule()
    child_calls = 0

    def unexpected_child(*_args, **_kwargs):
        nonlocal child_calls
        child_calls += 1
        raise AssertionError("invalid options must be rejected before delegation")

    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_restricted_execution_manifest",
        unexpected_child,
    )

    with pytest.raises(ValueError):
        axis1_carrier_execution_manifest(
            schedule,
            execution_backend_contract=(
                AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT
            ),
            execution_backend_options={"silent_metric": 1.0},
        )
    assert child_calls == 0


def test_axis1_carrier_execution_rejects_backend_options_for_dense_probe(
    monkeypatch: pytest.MonkeyPatch,
):
    import error_coupling_simulator.frontend.axis1_carrier_execution as carrier

    schedule = _joint_channel_schedule()
    cuda_calls = 0

    def unexpected_cuda(_device):
        nonlocal cuda_calls
        cuda_calls += 1
        raise AssertionError("invalid options must be rejected before CUDA")

    monkeypatch.setattr(carrier, "_require_cuda_device", unexpected_cuda)

    with pytest.raises(ValueError):
        axis1_carrier_execution_manifest(
            schedule,
            execution_backend_options={"max_bond": 2},
        )
    assert cuda_calls == 0


def test_axis1_qt_mps_restricted_execution_records_over_cap_h_readout_zero_collapse():
    builder = CircuitBuilder(num_qubits=6)
    builder.declare_static_zz_couplings(((0, 5),))
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            gamma_readout_phi_per_ns=0.0,
        )
    )
    builder.h(0)
    builder.tick()
    builder.measure(
        tuple(range(6)),
        key=tuple(f"m{i}" for i in range(6)),
        duration_ns=1.0e-6,
    )
    builder.detector("d05", xor=("m0", "m5"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_qt_mps_restricted_execution_manifest(schedule)

    assert manifest["schema"] == "error_coupling_simulator.frontend.qt_mps_restricted_execution.v6"
    assert manifest["representability"] == (
        "axis1_qt_mps_restricted_control_hamiltonian_z_record_product_channel"
    )
    assert manifest["execution_status"] == "completed"
    assert manifest["certification_status"] == "unavailable"
    assert manifest["diagnostic_only"] is True
    assert manifest["blocked_reason"] == (
        "overcap_independent_record_oracle_unavailable"
    )
    assert manifest["verdict"] == "fail"
    assert manifest["passed"] is False
    assert manifest["qt_mps_backend_executed"] is True
    assert manifest["claims_qt_mps_backend_execution"] is True
    assert manifest["claims_production_scalable_backend"] is False
    assert manifest["claims_exact_joint_lindblad_generator"] is False
    assert manifest["claims_dense_channel_evidence"] is False
    assert manifest["claims_dem_decoder_semantics"] is False
    assert manifest["claims_axis2_source_timeline"] is False
    assert manifest["carrier_program"]["requires_scalable_backend"] is True
    assert manifest["carrier_program"]["routes"] == ["scalable_required"]
    policy = manifest["restricted_acceptance_policy"]
    assert policy["schema"] == (
        "error_coupling_simulator.frontend.qt_mps_restricted_acceptance_policy.v2"
    )
    assert policy["certification_status"] == "unavailable"
    assert policy["diagnostic_only"] is True
    assert policy["blocked_reason"] == (
        "overcap_independent_record_oracle_unavailable"
    )
    assert policy["accepted_for_restricted_execution"] is False
    assert policy["accepted_for_exact_dense_probability_evidence"] is False
    assert policy["accepted_for_sampled_execution_evidence"] is False
    assert policy["accepted_for_production_scalable_backend"] is False
    assert policy["finite_step"]["dense_window_certification_status"] == (
        "skipped_overcap_dense_fallback_forbidden"
    )
    assert policy["finite_step"]["comparison_outcome_is_metric"] is False
    assert policy["overcap"]["requires_scalable_backend"] is True
    assert policy["overcap"]["dense_fallback_forbidden"] is True
    assert policy["overcap"]["accepted_as_restricted_overcap_execution"] is False
    assert policy["overcap"]["accepted_as_production_scalable_backend"] is False
    assert policy["mps_truncation"]["accepted_as_production_error_bound"] is False
    assert policy["comparison_outcome_is_metric"] is False

    execution = manifest["mps_execution"]
    assert execution["mps_library"] == "quimb.tensor.MatrixProductState"
    assert execution["array_backend"] == "torch_cuda_complex128"
    assert execution["exact_joint_generator_claim"] is False
    assert execution["exact_summed_lindbladian_claim"] is False
    ledger = execution["mps_truncation_ledger"]
    assert ledger["explicit_truncation_requested"] is False
    assert ledger["exact_bond_dimension_sufficient"] == 8
    assert ledger["exact_bond_policy"] == "unbounded_no_explicit_cap"
    assert ledger["accepted_as_exact_bond_representation"] is True
    assert ledger["discarded_weight_ledger_complete"] is True
    assert ledger["discarded_weight_sum"] == 0.0
    assert ledger["worst_cut_discarded_weight"] == 0.0
    assert ledger["n_truncating_ops"] == 0
    assert ledger["max_observed_bond"] >= 1
    assert ledger["ledger_scope"] == "no_explicit_mps_truncation_requested"
    assert ledger["epistemic_class"] == "a"
    assert execution["measurement_keys"] == ["m0", "m1", "m2", "m3", "m4", "m5"]
    p_m0_zero = sum(
        probability
        for bits, probability in zip(
            execution["measurement_records"],
            execution["record_probabilities"],
            strict=True,
        )
        if bits[0] == 0
    )
    p_m0_one = sum(
        probability
        for bits, probability in zip(
            execution["measurement_records"],
            execution["record_probabilities"],
            strict=True,
        )
        if bits[0] == 1
    )
    leakage_to_other_readout_bits = sum(
        probability
        for bits, probability in zip(
            execution["measurement_records"],
            execution["record_probabilities"],
            strict=True,
        )
        if any(bits[index] for index in range(1, 6))
    )
    assert [p_m0_zero, p_m0_one] == pytest.approx([0.5, 0.5], abs=1.0e-8)
    assert leakage_to_other_readout_bits <= 1.0e-8
    assert execution["applied_substeps"][0]["hamiltonian_operator_families"] == [
        "CTRL_H",
        "ZZ",
    ]
    assert execution["detector_names"] == ["d05"]
    assert execution["claims_b8_artifact"] is False
    assert execution["claims_decoder_integration"] is False


def test_axis1_qt_mps_restricted_execution_certifies_dense_window_against_jointL_record():
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            gamma_readout_phi_per_ns=0.0,
        )
    )
    builder.h(0)
    builder.tick()
    builder.measure((0, 1), key=("m0", "m1"), duration_ns=1.0e-6)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_qt_mps_restricted_execution_manifest(schedule)

    assert manifest["verdict"] == "pass"
    assert manifest["passed"] is True
    assert manifest["carrier_program"]["requires_scalable_backend"] is False
    assert manifest["carrier_program"]["routes"] == ["dense_oracle_available"]
    certification = manifest["dense_jointL_record_certification"]
    assert certification["executed"] is True
    assert certification["passed"] is True
    assert certification["comparison_object"] == "record_probabilities"
    assert certification["max_abs_probability_difference"] <= 1.0e-8
    assert certification["threshold_epistemic_class"] == "c"
    assert certification["comparison_outcome_is_metric"] is False
    policy = manifest["restricted_acceptance_policy"]
    assert policy["accepted_for_restricted_execution"] is True
    assert policy["accepted_for_exact_dense_probability_evidence"] is True
    assert policy["accepted_for_sampled_execution_evidence"] is False
    assert policy["accepted_for_production_scalable_backend"] is False
    assert policy["finite_step"]["dense_window_certification_status"] == "passed"
    assert policy["finite_step"]["dense_window_certification_passed"] is True
    assert policy["trajectory"]["accepted_as_exact_probability_evidence"] is True
    assert policy["trajectory"]["accepted_as_empirical_record_evidence"] is False
    assert policy["overcap"]["requires_scalable_backend"] is False
    assert policy["overcap"]["dense_fallback_forbidden"] is True
    assert policy["comparison_outcome_is_metric"] is False
    execution = manifest["mps_execution"]
    assert execution["record_probabilities"] == pytest.approx(
        [0.5, 0.5, 0.0, 0.0],
        abs=1.0e-8,
    )
    assert execution["mps_truncation_ledger"]["discarded_weight_ledger_complete"] is True
    assert execution["mps_truncation_ledger"]["discarded_weight_sum"] == 0.0


def test_axis1_qt_mps_restricted_execution_applies_standalone_reset_boundary():
    builder = CircuitBuilder(num_qubits=1)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            gamma_readout_phi_per_ns=0.0,
        )
    )
    builder.h(0)
    builder.reset(0)
    builder.measure(0, key="m0")
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_qt_mps_restricted_execution_manifest(schedule)

    assert manifest["verdict"] == "pass"
    assert manifest["passed"] is True
    assert manifest["carrier_program"]["routes"] == [
        "boundary_only",
        "dense_oracle_available",
    ]
    execution = manifest["mps_execution"]
    assert execution["measurement_records"] == [[0], [1]]
    assert execution["record_probabilities"] == pytest.approx([1.0, 0.0], abs=1.0e-8)
    reset_step = next(
        step for step in execution["applied_substeps"] if step["substep_kind"] == "reset"
    )
    assert reset_step["reset_boundary_policy"] == (
        "nonselective_pauli_reset_internal_branches_no_record"
    )
    assert manifest["dense_jointL_record_certification"]["passed"] is True


def test_axis1_qt_mps_restricted_execution_applies_mr_reset_before_later_readout():
    builder = CircuitBuilder(num_qubits=1)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            gamma_readout_phi_per_ns=0.0,
        )
    )
    builder.measure(0, key="m0", reset=True)
    builder.x(0)
    builder.measure(0, key="m1")
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_qt_mps_restricted_execution_manifest(schedule)

    assert manifest["verdict"] == "pass"
    assert manifest["passed"] is True
    execution = manifest["mps_execution"]
    distribution = {
        tuple(record): probability
        for record, probability in zip(
            execution["measurement_records"],
            execution["record_probabilities"],
            strict=True,
        )
    }
    assert distribution[(0, 1)] == pytest.approx(1.0, abs=1.0e-8)
    assert distribution[(0, 0)] == pytest.approx(0.0, abs=1.0e-8)
    assert distribution[(1, 0)] == pytest.approx(0.0, abs=1.0e-8)
    assert distribution[(1, 1)] == pytest.approx(0.0, abs=1.0e-8)
    assert manifest["dense_jointL_record_certification"]["passed"] is True


def test_axis1_qt_mps_restricted_execution_top_level_pass_requires_acceptance():
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            gamma_readout_phi_per_ns=0.0,
        )
    )
    builder.h(0)
    builder.tick()
    builder.measure((0, 1), key=("m0", "m1"), duration_ns=1.0e-6)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_qt_mps_restricted_execution_manifest(
        schedule,
        dense_oracle_certification=False,
    )

    assert manifest["verdict"] == "fail"
    assert manifest["passed"] is False
    certification = manifest["dense_jointL_record_certification"]
    assert certification == {
        "executed": False,
        "reason": "dense_oracle_certification_not_requested",
        "comparison_outcome_is_metric": False,
    }
    policy = manifest["restricted_acceptance_policy"]
    assert policy["accepted_for_restricted_execution"] is False
    assert policy["finite_step"]["dense_window_certification_status"] == "not_requested"
    assert "dense_window_certification:not_requested" in policy["production_blockers"]
    assert policy["comparison_outcome_is_metric"] is False


def test_axis1_qt_mps_restricted_execution_supports_compiler_two_qubit_control():
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            gamma_readout_phi_per_ns=0.0,
        )
    )
    builder.h((0, 1))
    builder.tick()
    builder.cz((0, 1))
    builder.tick()
    builder.measure((0, 1), key=("m0", "m1"), duration_ns=1.0e-6)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_qt_mps_restricted_execution_manifest(schedule)

    assert manifest["verdict"] == "pass"
    assert manifest["passed"] is True
    assert manifest["carrier_program"]["routes"] == ["dense_oracle_available"]
    execution = manifest["mps_execution"]
    assert [step["substep_kind"] for step in execution["applied_substeps"]] == [
        "one_qubit_gate",
        "two_qubit_gate",
        "measurement",
    ]
    assert execution["applied_substeps"][0]["hamiltonian_operator_families"] == [
        "CTRL_H",
        "CTRL_H",
    ]
    assert execution["applied_substeps"][1]["hamiltonian_operator_families"] == [
        "CTRL_CZ"
    ]
    assert execution["applied_substeps"][1]["max_observed_bond_after_substep"] == 2
    assert execution["record_probabilities"] == pytest.approx(
        [0.25, 0.25, 0.25, 0.25],
        abs=1.0e-8,
    )
    certification = manifest["dense_jointL_record_certification"]
    assert certification["executed"] is True
    assert certification["passed"] is True
    assert certification["comparison_outcome_is_metric"] is False
    assert certification["max_abs_probability_difference"] <= 1.0e-8


def test_axis1_qt_mps_restricted_execution_microsteps_reduce_noncommuting_residual():
    builder = CircuitBuilder(num_qubits=1)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_readout_phi_per_ns=0.0,
        )
    )
    builder.h(0)
    builder.tick()
    builder.measure(0, key="m0", duration_ns=1.0e-6)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifests = [
        axis1_qt_mps_restricted_execution_manifest(schedule, microstep_count=count)
        for count in (1, 2, 4)
    ]
    residuals = [
        manifest["dense_jointL_record_certification"]["max_abs_probability_difference"]
        for manifest in manifests
    ]

    assert residuals[0] > residuals[1] > residuals[2] > 0.0
    assert residuals[0] > 1.0e-4
    assert residuals[2] < 0.25 * residuals[0]
    for count, manifest in zip((1, 2, 4), manifests, strict=True):
        assert manifest["passed"] is False
        assert manifest["claims_exact_joint_lindblad_generator"] is False
        assert manifest["claims_dense_channel_evidence"] is False
        certification = manifest["dense_jointL_record_certification"]
        assert certification["executed"] is True
        assert certification["passed"] is False
        assert certification["comparison_outcome_is_metric"] is False
        acceptance = manifest["restricted_acceptance_policy"]
        assert acceptance["accepted_for_restricted_execution"] is False
        assert acceptance["finite_step"]["dense_window_certification_status"] == "failed"
        assert acceptance["accepted_for_production_scalable_backend"] is False
        policy = manifest["mps_execution"]["finite_step_policy"]
        assert policy["name"] == "operator_family_product_formula_v1"
        assert policy["order"] == "first_order"
        assert policy["microstep_count"] == count
        assert policy["exact_summed_lindbladian_claim"] is False
        assert policy["comparison_outcome_is_metric"] is False


def test_axis1_qt_mps_restricted_execution_strang_reduces_noncommuting_difference():
    builder = CircuitBuilder(num_qubits=1)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_readout_phi_per_ns=0.0,
        )
    )
    builder.h(0)
    builder.tick()
    builder.measure(0, key="m0", duration_ns=1.0e-6)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    first_order = axis1_qt_mps_restricted_execution_manifest(
        schedule,
        microstep_count=1,
    )
    strang = axis1_qt_mps_restricted_execution_manifest(
        schedule,
        microstep_count=1,
        finite_step_order="strang_second_order",
    )
    strang_refined = axis1_qt_mps_restricted_execution_manifest(
        schedule,
        microstep_count=2,
        finite_step_order="strang_second_order",
    )

    first_difference = first_order["dense_jointL_record_certification"][
        "max_abs_probability_difference"
    ]
    strang_difference = strang["dense_jointL_record_certification"][
        "max_abs_probability_difference"
    ]
    refined_difference = strang_refined["dense_jointL_record_certification"][
        "max_abs_probability_difference"
    ]

    assert strang_difference < 0.2 * first_difference
    assert refined_difference < 0.01 * strang_difference
    assert strang["passed"] is False
    assert strang_refined["passed"] is True
    for manifest in (strang, strang_refined):
        policy = manifest["mps_execution"]["finite_step_policy"]
        assert policy["name"] == "strang_hamiltonian_collapse_product_formula_v1"
        assert policy["order"] == "strang_second_order"
        assert policy["exact_summed_lindbladian_claim"] is False
        assert policy["comparison_outcome_is_metric"] is False
        assert manifest["claims_exact_joint_lindblad_generator"] is False
        assert manifest["claims_dense_channel_evidence"] is False
        assert manifest["dense_jointL_record_certification"][
            "comparison_outcome_is_metric"
        ] is False
        assert manifest["approximation_book"]["hamiltonian_product_formula"][
            "epistemic_class"
        ] == "c"
    acceptance = strang_refined["restricted_acceptance_policy"]
    assert acceptance["accepted_for_restricted_execution"] is True
    assert acceptance["accepted_for_exact_dense_probability_evidence"] is True
    assert acceptance["finite_step"]["order"] == "strang_second_order"
    assert acceptance["finite_step"]["dense_window_certification_status"] == "passed"
    assert acceptance["accepted_for_production_scalable_backend"] is False


def test_axis1_qt_mps_restricted_execution_finite_bond_ledger_catches_truncation():
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            gamma_readout_phi_per_ns=0.0,
        )
    )
    builder.h((0, 1))
    builder.tick()
    builder.cz((0, 1))
    builder.tick()
    builder.measure((0, 1), key=("m0", "m1"), duration_ns=1.0e-6)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_qt_mps_restricted_execution_manifest(schedule, max_bond=1)

    assert manifest["qt_mps_backend_executed"] is True
    assert manifest["passed"] is False
    certification = manifest["dense_jointL_record_certification"]
    assert certification["executed"] is True
    assert certification["passed"] is False
    assert certification["comparison_outcome_is_metric"] is False
    assert certification["max_abs_probability_difference"] > 1.0e-3
    assert manifest["mps_execution"]["total_probability"] == pytest.approx(
        1.0, abs=1.0e-8
    )
    assert manifest["mps_execution"]["total_probability_residual"] <= 1.0e-8

    ledger = manifest["mps_execution"]["mps_truncation_ledger"]
    assert ledger["explicit_truncation_requested"] is True
    assert ledger["exact_bond_dimension_sufficient"] == 2
    assert ledger["exact_bond_policy"] == (
        "finite_cap_below_conservative_exact_sufficient_bond"
    )
    assert ledger["accepted_as_exact_bond_representation"] is False
    assert ledger["discarded_weight_ledger_complete"] is True
    assert ledger["ledger_method"] == (
        "quimb_actual_svd_split_per_two_site_unitary_gate"
    )
    assert ledger["discarded_weight_units"] == "fraction_of_pre_split_weight"
    assert ledger["not_a_global_error_bound"] is True
    assert ledger["actual_split_count"] == 1
    assert ledger["actual_discarded_weight_raw_sum"] == pytest.approx(
        0.5, abs=1.0e-8
    )
    assert ledger["discarded_weight_sum"] == pytest.approx(0.5, abs=1.0e-8)
    assert ledger["worst_cut_discarded_weight"] == pytest.approx(0.5, abs=1.0e-8)
    assert ledger["n_truncating_ops"] == 1
    assert ledger["n_tracked_two_site_ops"] == 1
    event = ledger["truncation_events"][0]
    assert event["operator_family"] == "CTRL_CZ"
    assert event["support"] == [0, 1]
    assert event["ledger_method"] == (
        "quimb_actual_svd_split_per_two_site_unitary_gate"
    )
    assert event["discarded_weight_sum"] == pytest.approx(0.5, abs=1.0e-8)
    assert event["split_count"] == 1
    assert event["physical_branch_probability"] is None
    assert event["raw_output_norm_sq"] == pytest.approx(0.5, abs=1.0e-8)
    assert event["restored_output_norm_sq"] == pytest.approx(1.0, abs=1.0e-8)
    assert event["split_records"][0]["path_role"] == "two_site_operator_split"
    assert event["split_records"][0]["actual_kept_bond_dimension"] == 1
    assert event["split_records"][0][
        "actual_discarded_weight_fraction_of_pre_split"
    ] == pytest.approx(0.5, abs=1.0e-8)
    policy = manifest["restricted_acceptance_policy"]
    assert policy["mps_truncation"]["truncation_detected"] is True
    assert policy["mps_truncation"]["accepted_as_restricted_risk_ledger"] is True
    assert policy["mps_truncation"]["accepted_as_production_error_bound"] is False
    assert "finite_bond_error_bound_not_established" in policy["production_blockers"]
    assert "nonzero_mps_truncation_discarded_weight" in policy["production_blockers"]


def test_axis1_qt_mps_restricted_execution_marks_finite_exact_bond_sufficient_cap():
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            gamma_readout_phi_per_ns=0.0,
        )
    )
    builder.h((0, 1))
    builder.tick()
    builder.cz((0, 1))
    builder.tick()
    builder.measure((0, 1), key=("m0", "m1"), duration_ns=1.0e-6)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_qt_mps_restricted_execution_manifest(schedule, max_bond=2)

    assert manifest["verdict"] == "pass"
    ledger = manifest["mps_execution"]["mps_truncation_ledger"]
    assert ledger["explicit_truncation_requested"] is True
    assert ledger["max_bond"] == 2
    assert ledger["exact_bond_dimension_sufficient"] == 2
    assert ledger["exact_bond_policy"] == (
        "finite_cap_at_or_above_conservative_exact_sufficient_bond"
    )
    assert ledger["accepted_as_exact_bond_representation"] is True
    assert ledger["discarded_weight_sum"] == pytest.approx(0.0, abs=1.0e-12)
    assert ledger["worst_cut_discarded_weight"] == pytest.approx(0.0, abs=1.0e-12)
    policy = manifest["restricted_acceptance_policy"]
    assert policy["mps_truncation"]["accepted_as_exact_bond_representation"] is True
    assert policy["mps_truncation"]["accepted_as_production_error_bound"] is False
    assert policy["accepted_for_production_scalable_backend"] is False


def test_axis1_qt_mps_bond_sweep_detects_underbonded_record_difference():
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            gamma_readout_phi_per_ns=0.0,
        )
    )
    builder.h((0, 1))
    builder.tick()
    builder.cz((0, 1))
    builder.tick()
    builder.measure((0, 1), key=("m0", "m1"), duration_ns=1.0e-6)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    sweep = axis1_qt_mps_bond_sweep_manifest(
        schedule,
        bond_values=(1, 2),
        convergence_record_probability_gate=1.0e-3,
    )

    assert sweep["schema"] == "error_coupling_simulator.frontend.qt_mps_bond_sweep.v4"
    assert sweep["verdict"] == "fail"
    assert sweep["passed"] is False
    assert sweep["bond_values"] == [1, 2]
    assert sweep["reference_bond"] == 2
    policy = sweep["convergence_policy"]
    assert policy["accepted_as_restricted_convergence_evidence"] is False
    assert policy["accepted_as_production_error_bound"] is False
    assert policy["accepted_for_production_scalable_backend"] is False
    gate = policy["convergence_gate"]
    assert gate["evaluated"] is True
    assert gate["passed"] is False
    assert gate["comparison_outcome_is_metric"] is False
    assert gate["observed_max_abs_probability_difference"] > 1.0e-3
    assert "record_probability_difference_exceeds_gate" in gate["violations"]
    assert sweep["claims_production_scalable_backend"] is False
    assert sweep["claims_dense_channel_evidence"] is False


def test_axis1_qt_mps_bond_sweep_passes_exact_sufficient_bonds():
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            gamma_readout_phi_per_ns=0.0,
        )
    )
    builder.h((0, 1))
    builder.tick()
    builder.cz((0, 1))
    builder.tick()
    builder.measure((0, 1), key=("m0", "m1"), duration_ns=1.0e-6)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    sweep = axis1_qt_mps_bond_sweep_manifest(
        schedule,
        bond_values=(2, 4),
        convergence_record_probability_gate=1.0e-10,
    )

    assert sweep["verdict"] == "pass"
    assert sweep["passed"] is True
    policy = sweep["convergence_policy"]
    assert policy["accepted_as_restricted_convergence_evidence"] is True
    assert policy["accepted_as_production_error_bound"] is False
    assert policy["accepted_for_production_scalable_backend"] is False
    calibration = policy["reference_dense_calibration"]
    assert calibration["status"] == "passed"
    assert calibration["executed"] is True
    assert calibration["passed"] is True
    assert calibration["accepted_as_dense_calibrated_reference"] is True
    assert calibration["comparison_outcome_is_metric"] is False
    gate = policy["convergence_gate"]
    assert gate["passed"] is True
    assert gate["comparison_outcome_is_metric"] is False
    assert gate["observed_max_abs_probability_difference"] <= 1.0e-10
    assert [run["max_bond"] for run in sweep["run_summaries"]] == [2, 4]
    assert all(
        run["accepted_as_exact_bond_representation"]
        for run in sweep["run_summaries"]
    )
    assert sweep["claims_exact_joint_lindblad_generator"] is False


def test_axis1_qt_mps_bond_sweep_rejects_uncalibrated_finite_step_reference():
    builder = CircuitBuilder(num_qubits=1)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_readout_phi_per_ns=0.0,
        )
    )
    builder.h(0)
    builder.tick()
    builder.measure(0, key="m0", duration_ns=1.0e-6)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    sweep = axis1_qt_mps_bond_sweep_manifest(
        schedule,
        bond_values=(1, 2),
        convergence_record_probability_gate=1.0e-12,
        microstep_count=1,
        finite_step_order="first_order",
    )

    assert sweep["verdict"] == "fail"
    assert sweep["passed"] is False
    policy = sweep["convergence_policy"]
    assert policy["convergence_gate"]["passed"] is True
    calibration = policy["reference_dense_calibration"]
    assert calibration["status"] == "failed"
    assert calibration["executed"] is True
    assert calibration["passed"] is False
    assert calibration["accepted_as_dense_calibrated_reference"] is False
    assert calibration["comparison_outcome_is_metric"] is False
    assert policy["accepted_as_restricted_convergence_evidence"] is False
    assert policy["accepted_as_production_error_bound"] is False
    assert sweep["claims_exact_joint_lindblad_generator"] is False


def test_axis1_qt_mps_trajectory_seed_sweep_passes_dense_calibrated_deterministic_records():
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            gamma_readout_phi_per_ns=0.0,
        )
    )
    builder.measure((0, 1), key=("m0", "m1"), duration_ns=1.0e-6)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    sweep = axis1_qt_mps_trajectory_seed_sweep_manifest(
        schedule,
        trajectory_count=8,
        rng_seeds=(101, 202),
        seed_record_frequency_spread_gate=0.0,
        dense_record_frequency_gate=1.0e-12,
    )

    assert sweep["schema"] == "error_coupling_simulator.frontend.qt_mps_trajectory_seed_sweep.v4"
    assert sweep["verdict"] == "pass"
    assert sweep["passed"] is True
    policy = sweep["seed_sweep_policy"]
    assert policy["all_sampled_runs_accepted"] is True
    assert policy["accepted_as_restricted_seed_sweep_evidence"] is True
    assert policy["accepted_as_dense_calibrated_trajectory_evidence"] is True
    assert policy["accepted_as_production_error_bound"] is False
    assert policy["accepted_for_production_scalable_backend"] is False
    assert policy["comparison_outcome_is_metric"] is False
    assert policy["seed_spread_gate"]["passed"] is True
    assert policy["seed_spread_gate"]["comparison_outcome_is_metric"] is False
    dense = policy["dense_reference_calibration"]
    assert dense["status"] == "passed"
    assert dense["executed"] is True
    assert dense["accepted_as_dense_calibrated_trajectory_evidence"] is True
    assert dense["comparison_outcome_is_metric"] is False
    assert dense["observed_max_abs_frequency_difference"] <= 1.0e-12
    assert [run["rng_seed"] for run in sweep["run_summaries"]] == [101, 202]
    assert all(
        run["accepted_for_sampled_execution_evidence"] for run in sweep["run_summaries"]
    )
    assert sweep["claims_production_scalable_backend"] is False
    assert sweep["claims_dense_channel_evidence"] is False


def test_axis1_qt_mps_trajectory_seed_sweep_rejects_bad_dense_frequency_gate():
    builder = CircuitBuilder(num_qubits=1)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            gamma_readout_phi_per_ns=0.0,
        )
    )
    builder.h(0)
    builder.tick()
    builder.measure(0, key="m0", duration_ns=1.0e-6)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    sweep = axis1_qt_mps_trajectory_seed_sweep_manifest(
        schedule,
        trajectory_count=1,
        rng_seeds=(11, 12),
        seed_record_frequency_spread_gate=1.0,
        dense_record_frequency_gate=0.1,
    )

    assert sweep["verdict"] == "pass"
    assert sweep["passed"] is True
    policy = sweep["seed_sweep_policy"]
    assert policy["accepted_as_restricted_seed_sweep_evidence"] is True
    dense = policy["dense_reference_calibration"]
    assert dense["status"] == "failed"
    assert dense["executed"] is True
    assert dense["accepted_as_dense_calibrated_trajectory_evidence"] is False
    assert "dense_record_frequency_difference_exceeds_gate" in dense["violations"]
    assert dense["comparison_outcome_is_metric"] is False
    assert policy["accepted_for_production_scalable_backend"] is False
    assert sweep["claims_exact_joint_lindblad_generator"] is False


def test_axis1_qt_mps_trajectory_seed_sweep_overcap_is_not_dense_calibrated():
    builder = CircuitBuilder(num_qubits=6)
    builder.declare_static_zz_couplings(((0, 5),))
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            gamma_readout_phi_per_ns=0.0,
        )
    )
    builder.h(0)
    builder.tick()
    builder.measure(
        tuple(range(6)),
        key=tuple(f"m{i}" for i in range(6)),
        duration_ns=1.0e-6,
    )
    schedule = circuit_ir_to_substep_schedule(builder.build())

    sweep = axis1_qt_mps_trajectory_seed_sweep_manifest(
        schedule,
        trajectory_count=8,
        rng_seeds=(321, 654),
        seed_record_frequency_spread_gate=1.0,
        dense_record_frequency_gate=1.0e-8,
    )

    assert sweep["verdict"] == "fail"
    assert sweep["passed"] is False
    policy = sweep["seed_sweep_policy"]
    assert policy["all_sampled_runs_accepted"] is False
    assert policy["seed_spread_gate"]["evaluated"] is True
    assert policy["seed_spread_gate"]["passed"] is True
    assert policy["accepted_as_restricted_seed_sweep_evidence"] is False
    assert policy["accepted_as_dense_calibrated_trajectory_evidence"] is False
    assert policy["dense_reference_calibration"]["status"] == "not_available_overcap"
    assert policy["dense_reference_calibration"]["executed"] is False
    assert policy["accepted_as_production_error_bound"] is False
    assert policy["accepted_for_production_scalable_backend"] is False
    assert sweep["claims_production_scalable_backend"] is False


def test_axis1_qt_mps_trajectory_seed_sweep_requires_explicit_distinct_seeds(
    monkeypatch: pytest.MonkeyPatch,
):
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule = _joint_channel_schedule()
    child_calls = 0

    def unexpected_child(*_args, **_kwargs):
        nonlocal child_calls
        child_calls += 1
        raise AssertionError("invalid seeds must be rejected before delegation")

    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_restricted_execution_manifest",
        unexpected_child,
    )

    with pytest.raises(ValueError):
        axis1_qt_mps_trajectory_seed_sweep_manifest(
            schedule,
            trajectory_count=4,
            rng_seeds=(1,),
        )
    with pytest.raises(ValueError):
        axis1_qt_mps_trajectory_seed_sweep_manifest(
            schedule,
            trajectory_count=4,
            rng_seeds=(1, 1),
        )
    assert child_calls == 0


def test_axis1_qt_mps_restricted_evidence_bundle_passes_deterministic_dense_case():
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            gamma_readout_phi_per_ns=0.0,
        )
    )
    builder.measure((0, 1), key=("m0", "m1"), duration_ns=1.0e-6)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    bundle = axis1_qt_mps_restricted_evidence_bundle_manifest(
        schedule,
        bond_values=(1, 2),
        trajectory_count=8,
        rng_seeds=(101, 202),
        convergence_record_probability_gate=0.0,
        seed_record_frequency_spread_gate=0.0,
        dense_record_frequency_gate=1.0e-12,
    )

    assert bundle["schema"] == (
        "error_coupling_simulator.frontend.qt_mps_restricted_evidence_bundle.v4"
    )
    assert bundle["verdict"] == "pass"
    assert bundle["passed"] is True
    policy = bundle["bundle_policy"]
    assert policy["accepted_as_restricted_bundle_evidence"] is True
    assert policy["accepted_as_dense_calibrated_bundle_evidence"] is True
    assert policy["accepted_as_production_error_bound"] is False
    assert policy["accepted_for_production_scalable_backend"] is False
    assert policy["comparison_outcome_is_metric"] is False
    assert bundle["bond_sweep"]["passed"] is True
    assert bundle["trajectory_seed_sweep"]["passed"] is True
    assert bundle["claims_exact_joint_lindblad_generator"] is False
    assert bundle["claims_dense_channel_evidence"] is False
    assert bundle["claims_production_scalable_backend"] is False


def test_axis1_qt_mps_restricted_evidence_bundle_fails_when_bond_sweep_fails():
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            gamma_readout_phi_per_ns=0.0,
        )
    )
    builder.h((0, 1))
    builder.tick()
    builder.cz((0, 1))
    builder.tick()
    builder.measure((0, 1), key=("m0", "m1"), duration_ns=1.0e-6)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    bundle = axis1_qt_mps_restricted_evidence_bundle_manifest(
        schedule,
        bond_values=(1, 2),
        trajectory_count=8,
        rng_seeds=(101, 202),
        convergence_record_probability_gate=1.0e-3,
        seed_record_frequency_spread_gate=1.0,
        dense_record_frequency_gate=1.0,
    )

    assert bundle["verdict"] == "fail"
    assert bundle["passed"] is False
    assert bundle["bond_sweep"]["passed"] is False
    assert bundle["trajectory_seed_sweep"]["passed"] is True
    policy = bundle["bundle_policy"]
    assert policy["accepted_as_restricted_bundle_evidence"] is False
    assert policy["accepted_as_production_error_bound"] is False
    assert policy["accepted_for_production_scalable_backend"] is False
    assert bundle["claims_production_scalable_backend"] is False


def test_axis1_qt_mps_resource_probe_reports_actual_cuda_memory_without_production_claim():
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            gamma_readout_phi_per_ns=0.0,
        )
    )
    builder.measure((0, 1), key=("m0", "m1"), duration_ns=1.0e-6)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    probe = axis1_qt_mps_resource_probe_manifest(
        schedule,
        bond_values=(1, 2),
        trajectory_count=8,
        rng_seeds=(101, 202),
        convergence_record_probability_gate=0.0,
        seed_record_frequency_spread_gate=0.0,
        dense_record_frequency_gate=1.0e-12,
        min_peak_reserved_gib=0.0,
    )

    assert probe["schema"] == "error_coupling_simulator.frontend.qt_mps_resource_probe.v4"
    assert probe["verdict"] == "pass"
    assert probe["passed"] is True
    assert probe["workload_passed"] is True
    policy = probe["resource_probe_policy"]
    assert policy["memory_pressure_source"] == (
        "actual_restricted_qt_mps_execution_only_no_padding"
    )
    assert policy["peak_reserved_bytes"] >= policy["peak_allocated_bytes"] >= 0
    assert policy["gate_evaluated"] is True
    assert policy["gate_passed"] is True
    assert policy["accepted_as_resource_probe"] is True
    assert policy["accepted_for_production_scalable_backend"] is False
    assert policy["comparison_outcome_is_metric"] is False
    assert probe["claims_production_scalable_backend"] is False
    assert probe["claims_exact_joint_lindblad_generator"] is False


def test_axis1_qt_mps_resource_probe_fails_unreached_memory_gate_without_padding():
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            gamma_readout_phi_per_ns=0.0,
        )
    )
    builder.measure((0, 1), key=("m0", "m1"), duration_ns=1.0e-6)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    probe = axis1_qt_mps_resource_probe_manifest(
        schedule,
        bond_values=(1, 2),
        trajectory_count=8,
        rng_seeds=(101, 202),
        convergence_record_probability_gate=0.0,
        seed_record_frequency_spread_gate=0.0,
        dense_record_frequency_gate=1.0e-12,
        min_peak_reserved_gib=1024.0,
    )

    assert probe["verdict"] == "fail"
    assert probe["passed"] is False
    assert probe["workload_passed"] is True
    policy = probe["resource_probe_policy"]
    assert policy["gate_evaluated"] is True
    assert policy["gate_passed"] is False
    assert policy["accepted_as_resource_probe"] is False
    assert "peak_reserved_gib_below_gate" in policy["violations"]
    assert policy["memory_pressure_source"] == (
        "actual_restricted_qt_mps_execution_only_no_padding"
    )
    assert policy["comparison_outcome_is_metric"] is False
    assert probe["claims_production_scalable_backend"] is False


def test_axis1_qt_mps_restricted_execution_finite_bond_gate_is_policy_not_metric():
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            gamma_readout_phi_per_ns=0.0,
        )
    )
    builder.h((0, 1))
    builder.tick()
    builder.cz((0, 1))
    builder.tick()
    builder.measure((0, 1), key=("m0", "m1"), duration_ns=1.0e-6)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    failed = axis1_qt_mps_restricted_execution_manifest(
        schedule,
        max_bond=1,
        worst_cut_discarded_weight_gate=0.49,
        total_discarded_weight_gate=0.49,
    )
    loose = axis1_qt_mps_restricted_execution_manifest(
        schedule,
        max_bond=1,
        worst_cut_discarded_weight_gate=0.51,
        total_discarded_weight_gate=0.51,
    )

    failed_gate = failed["restricted_acceptance_policy"]["mps_truncation"]["gate"]
    assert failed_gate["evaluated"] is True
    assert failed_gate["passed"] is False
    assert failed_gate["comparison_outcome_is_metric"] is False
    assert failed_gate["epistemic_class"] == "c"
    assert set(failed_gate["violations"]) == {
        "worst_cut_discarded_weight_exceeds_gate",
        "total_discarded_weight_exceeds_gate",
    }
    assert failed["restricted_acceptance_policy"][
        "accepted_for_production_scalable_backend"
    ] is False
    assert "finite_bond_candidate_gate_failed" in failed["restricted_acceptance_policy"][
        "production_blockers"
    ]

    loose_policy = loose["restricted_acceptance_policy"]
    loose_gate = loose_policy["mps_truncation"]["gate"]
    assert loose_gate["evaluated"] is True
    assert loose_gate["passed"] is True
    assert loose_gate["comparison_outcome_is_metric"] is False
    assert loose_policy["mps_truncation"]["accepted_as_finite_bond_candidate"] is True
    assert loose_policy["mps_truncation"]["accepted_as_production_error_bound"] is False
    assert loose_policy["accepted_for_production_scalable_backend"] is False
    assert "finite_bond_error_bound_not_established" in loose_policy[
        "production_blockers"
    ]


def test_axis1_qt_mps_restricted_execution_sampled_trajectories_are_seeded():
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            gamma_readout_phi_per_ns=0.0,
        )
    )
    builder.h((0, 1))
    builder.tick()
    builder.cz((0, 1))
    builder.tick()
    builder.measure((0, 1), key=("m0", "m1"), duration_ns=1.0e-6)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    first = axis1_qt_mps_restricted_execution_manifest(
        schedule,
        trajectory_count=16,
        rng_seed=123,
    )
    second = axis1_qt_mps_restricted_execution_manifest(
        schedule,
        trajectory_count=16,
        rng_seed=123,
    )

    assert first["verdict"] == "pass"
    assert first["passed"] is True
    execution = first["mps_execution"]
    sampling = execution["trajectory_sampling"]
    assert sampling == {
        "mode": "sampled_product_channel_trajectories",
        "trajectory_count": 16,
        "rng_seed": 123,
        "rng_seed_required_for_acceptance": True,
            "rng_seed_was_explicit": True,
            "rng_seed_default_policy": "default_zero_when_not_provided",
            "rng_backend": "torch.Generator(cuda)",
            "measurement_sampling_policy": (
                "sequential_conditional_single_site_z_v1"
            ),
            "record_support_policy": "observed_empirical_outcomes_only",
            "zero_frequency_records_emitted": False,
            "probability_semantics": "empirical_record_frequencies",
            "comparison_outcome_is_metric": False,
        }
    assert execution["record_counts"] == second["mps_execution"]["record_counts"]
    assert sum(execution["record_counts"]) == 16
    assert sum(execution["record_probabilities"]) == pytest.approx(1.0, abs=1.0e-12)
    certification = first["dense_jointL_record_certification"]
    assert certification == {
        "executed": False,
        "reason": "sampled_trajectory_empirical_probabilities_not_exact_dense_certified",
        "comparison_outcome_is_metric": False,
    }
    assert first["claims_production_scalable_backend"] is False
    policy = first["restricted_acceptance_policy"]
    assert policy["accepted_for_restricted_execution"] is True
    assert policy["accepted_for_exact_dense_probability_evidence"] is False
    assert policy["accepted_for_sampled_execution_evidence"] is True
    assert policy["trajectory"]["accepted_as_exact_probability_evidence"] is False
    assert policy["trajectory"]["accepted_as_empirical_record_evidence"] is True
    assert policy["trajectory"]["rng_seed_required_for_acceptance"] is True
    assert policy["trajectory"]["rng_seed_was_explicit"] is True
    assert policy["finite_step"]["dense_window_certification_status"] == (
        "skipped_sampled_trajectory_not_exact_probability_evidence"
    )
    assert policy["accepted_for_production_scalable_backend"] is False


def test_axis1_qt_mps_restricted_execution_requires_explicit_seed_for_sampled_acceptance():
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            gamma_readout_phi_per_ns=0.0,
        )
    )
    builder.h((0, 1))
    builder.tick()
    builder.measure((0, 1), key=("m0", "m1"), duration_ns=1.0e-6)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_qt_mps_restricted_execution_manifest(
        schedule,
        trajectory_count=4,
    )

    sampling = manifest["mps_execution"]["trajectory_sampling"]
    assert manifest["verdict"] == "fail"
    assert manifest["passed"] is False
    assert sampling["rng_seed"] == 0
    assert sampling["rng_seed_was_explicit"] is False
    policy = manifest["restricted_acceptance_policy"]
    assert policy["accepted_for_restricted_execution"] is False
    assert policy["accepted_for_sampled_execution_evidence"] is False
    assert policy["trajectory"]["rng_seed_required_for_acceptance"] is True
    assert policy["trajectory"]["rng_seed_was_explicit"] is False
    assert "sampled_trajectory_rng_seed_not_explicit" in policy["production_blockers"]
    assert policy["accepted_for_production_scalable_backend"] is False


def test_axis1_qt_mps_restricted_execution_runs_over_cap_local_collapse_branches():
    builder = CircuitBuilder(num_qubits=6)
    builder.declare_static_zz_couplings(((0, 5),))
    builder.idle(tuple(range(6)), duration_ns=1.0e-6)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_qt_mps_restricted_execution_manifest(schedule)

    assert manifest["execution_status"] == "completed"
    assert manifest["certification_status"] == "unavailable"
    assert manifest["diagnostic_only"] is True
    assert manifest["blocked_reason"] == (
        "overcap_independent_record_oracle_unavailable"
    )
    assert manifest["verdict"] == "fail"
    assert manifest["passed"] is False
    assert manifest["qt_mps_backend_executed"] is True
    assert manifest["claims_qt_mps_backend_execution"] is True
    assert manifest["claims_production_scalable_backend"] is False
    assert manifest["claims_exact_joint_lindblad_generator"] is False
    policy = manifest["restricted_acceptance_policy"]
    assert policy["accepted_for_restricted_execution"] is False
    assert policy["overcap"][
        "accepted_as_restricted_overcap_execution"
    ] is False

    execution = manifest["mps_execution"]
    assert execution["collapse_evolution_policy"] == "local_product_channel_branching"
    assert execution["record_count"] == 1
    assert execution["measurement_records"] == [[]]
    assert execution["record_probabilities"] == pytest.approx([1.0], abs=1.0e-8)
    assert execution["total_probability_residual"] <= 1.0e-8
    assert execution["applied_substeps"][0]["route"] == "scalable_required"
    assert execution["applied_substeps"][0]["hamiltonian_operator_families"] == ["ZZ"]
    assert execution["applied_substeps"][0]["nonzero_collapse_term_count"] == 12
    assert set(execution["applied_substeps"][0]["nonzero_collapse_operator_families"]) == {
        "T1",
        "T2",
    }


def test_axis1_qt_mps_restricted_execution_samples_over_cap_without_dense_fallback():
    builder = CircuitBuilder(num_qubits=6)
    builder.declare_static_zz_couplings(((0, 5),))
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_readout_phi_per_ns=0.0,
        )
    )
    builder.h(0)
    builder.tick()
    builder.measure(
        tuple(range(6)),
        key=tuple(f"m{i}" for i in range(6)),
        duration_ns=1.0e-6,
    )
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_qt_mps_restricted_execution_manifest(
        schedule,
        trajectory_count=8,
        rng_seed=321,
        finite_step_order="strang_second_order",
    )

    assert manifest["execution_status"] == "completed"
    assert manifest["certification_status"] == "unavailable"
    assert manifest["diagnostic_only"] is True
    assert manifest["blocked_reason"] == (
        "overcap_independent_record_oracle_unavailable"
    )
    assert manifest["verdict"] == "fail"
    assert manifest["passed"] is False
    assert manifest["carrier_program"]["requires_scalable_backend"] is True
    assert manifest["carrier_program"]["routes"] == ["scalable_required"]
    certification = manifest["dense_jointL_record_certification"]
    assert certification == {
        "executed": False,
        "reason": "sampled_trajectory_empirical_probabilities_not_exact_dense_certified",
        "comparison_outcome_is_metric": False,
    }
    execution = manifest["mps_execution"]
    assert execution["trajectory_sampling"]["rng_seed"] == 321
    assert execution["trajectory_sampling"]["rng_seed_was_explicit"] is True
    assert sum(execution["record_counts"]) == 8
    assert sum(execution["record_probabilities"]) == pytest.approx(1.0, abs=1.0e-12)
    policy = manifest["restricted_acceptance_policy"]
    assert policy["accepted_for_restricted_execution"] is False
    assert policy["accepted_for_sampled_execution_evidence"] is False
    assert policy["accepted_for_exact_dense_probability_evidence"] is False
    assert policy["finite_step"]["order"] == "strang_second_order"
    assert policy["finite_step"]["dense_window_certification_status"] == (
        "skipped_sampled_trajectory_not_exact_probability_evidence"
    )
    assert policy["overcap"]["requires_scalable_backend"] is True
    assert policy["overcap"]["dense_fallback_forbidden"] is True
    assert policy["overcap"]["dense_certification_used_for_overcap"] is False
    assert policy["overcap"][
        "accepted_as_restricted_overcap_execution"
    ] is False
    assert policy["accepted_for_production_scalable_backend"] is False
    assert "sampled_probabilities_not_exact_dense_evidence" in policy["production_blockers"]


def test_axis1_qt_mps_restricted_execution_carries_t1_population_decay():
    builder = CircuitBuilder(num_qubits=6)
    builder.declare_static_zz_couplings(((0, 5),))
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_readout_phi_per_ns=0.0,
        )
    )
    builder.h(0)
    builder.tick()
    builder.measure(
        tuple(range(6)),
        key=tuple(f"m{i}" for i in range(6)),
        duration_ns=1.0e-6,
    )
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_qt_mps_restricted_execution_manifest(schedule)

    assert manifest["execution_status"] == "completed"
    assert manifest["certification_status"] == "unavailable"
    assert manifest["diagnostic_only"] is True
    assert manifest["blocked_reason"] == (
        "overcap_independent_record_oracle_unavailable"
    )
    assert manifest["verdict"] == "fail"
    assert manifest["passed"] is False
    policy = manifest["restricted_acceptance_policy"]
    assert policy["accepted_for_restricted_execution"] is False
    assert policy["overcap"][
        "accepted_as_restricted_overcap_execution"
    ] is False
    execution = manifest["mps_execution"]
    p_m0_one = sum(
        probability
        for bits, probability in zip(
            execution["measurement_records"],
            execution["record_probabilities"],
            strict=True,
        )
        if bits[0] == 1
    )
    expected = 0.5 * math.exp(-JOINT_CHANNEL_GAMMA_1_PER_NS * 25.0)
    assert p_m0_one == pytest.approx(expected, abs=1.0e-8)
    assert p_m0_one < 0.5
    assert execution["applied_substeps"][0]["nonzero_collapse_operator_families"].count(
        "T1"
    ) == 6


def test_axis1_qt_mps_restricted_execution_refuses_cpu_device(
    monkeypatch: pytest.MonkeyPatch,
):
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule = _joint_channel_schedule()
    cuda_devices = []
    require_cuda_device = qt._require_cuda_device

    def counted_cuda_guard(device):
        cuda_devices.append(device)
        return require_cuda_device(device)

    monkeypatch.setattr(qt, "_require_cuda_device", counted_cuda_guard)

    with pytest.raises(ValueError):
        axis1_qt_mps_restricted_execution_manifest(schedule, device="cpu")
    assert cuda_devices == ["cpu"]


def test_axis1_qt_mps_restricted_execution_refuses_nonpositive_microstep_count(
    monkeypatch: pytest.MonkeyPatch,
):
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule = _joint_channel_schedule()
    cuda_devices = []
    monkeypatch.setattr(qt, "_require_cuda_device", cuda_devices.append)

    with pytest.raises(ValueError):
        axis1_qt_mps_restricted_execution_manifest(schedule, microstep_count=0)
    assert cuda_devices == []


def test_axis1_qt_mps_restricted_execution_refuses_nonpositive_branch_cap(
    monkeypatch: pytest.MonkeyPatch,
):
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule = _joint_channel_schedule()
    cuda_devices = []
    monkeypatch.setattr(qt, "_require_cuda_device", cuda_devices.append)

    with pytest.raises(ValueError):
        axis1_qt_mps_restricted_execution_manifest(schedule, max_branches=0)
    assert cuda_devices == []


def test_axis1_qt_mps_restricted_execution_refuses_nonpositive_max_bond(
    monkeypatch: pytest.MonkeyPatch,
):
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule = _joint_channel_schedule()
    cuda_devices = []
    monkeypatch.setattr(qt, "_require_cuda_device", cuda_devices.append)

    with pytest.raises(ValueError):
        axis1_qt_mps_restricted_execution_manifest(schedule, max_bond=0)
    assert cuda_devices == []


def test_axis1_qt_mps_restricted_execution_refuses_unknown_finite_step_order(
    monkeypatch: pytest.MonkeyPatch,
):
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule = _joint_channel_schedule()
    cuda_devices = []
    monkeypatch.setattr(qt, "_require_cuda_device", cuda_devices.append)

    with pytest.raises(ValueError):
        axis1_qt_mps_restricted_execution_manifest(
            schedule,
            finite_step_order="exact_joint_lindbladian",
        )
    assert cuda_devices == []


def test_axis1_carrier_execution_probe_refuses_cpu_device(
    monkeypatch: pytest.MonkeyPatch,
):
    import error_coupling_simulator.frontend.axis1_carrier_execution as carrier

    schedule = _joint_channel_schedule()
    cuda_devices = []
    require_cuda_device = carrier._require_cuda_device

    def counted_cuda_guard(device):
        cuda_devices.append(device)
        return require_cuda_device(device)

    monkeypatch.setattr(carrier, "_require_cuda_device", counted_cuda_guard)

    with pytest.raises(ValueError):
        axis1_carrier_execution_manifest(schedule, device="cpu")
    assert cuda_devices == ["cpu"]


def test_axis1_qutip_cuquantum_probe_lowers_over_cap_static_program_symbolically():
    builder = CircuitBuilder(num_qubits=6)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            include_thermal_excitation=True,
            gamma_up_per_ns=2.0e-4,
        )
    )
    builder.declare_static_zz_couplings(
        ((0, 5), (1, 4)),
        zeta_rad_per_ns_by_edge={(0, 5): 1.25e-3},
    )
    builder.idle(tuple(range(6)), duration_ns=75.0)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_qutip_cuquantum_probe_manifest(schedule)

    assert manifest["schema"] == "error_coupling_simulator.frontend.qutip_cuquantum_probe.v1"
    assert manifest["representability"] == (
        "axis1_qutip_cuquantum_symbolic_lowering_probe_no_state_record_execution"
    )
    assert manifest["backend_contract"] == "qutip_cuquantum_probe"
    assert manifest["gpu_required"] is True
    assert manifest["claims_state_execution"] is False
    assert manifest["claims_record_execution"] is False
    assert manifest["claims_dense_channel_evidence"] is False
    assert manifest["claims_dem_decoder_semantics"] is False
    assert manifest["claims_axis2_source_timeline"] is False
    assert manifest["carrier_program"]["requires_scalable_backend"] is True

    lowered = manifest["lowered_substeps"][0]
    assert lowered["substep_id"] == "s0000"
    assert lowered["route"] == "scalable_required"
    assert lowered["support"] == [0, 1, 2, 3, 4, 5]
    assert lowered["hilbert_dims"] == [2, 2, 2, 2, 2, 2]
    assert lowered["combined_hamiltonian"]["data_type"] == "CuOperator"
    assert lowered["combined_hamiltonian"]["shape"] == [64, 64]
    assert lowered["combined_hamiltonian"]["term_count"] >= 1
    assert lowered["contains_dense_operator_payload"] is False

    zz_terms = [
        term for term in lowered["hamiltonian_terms"] if term["operator_family"] == "ZZ"
    ]
    assert [
        (term["support"], term["coefficient"], term["coefficient_source"], term["data_type"])
        for term in zz_terms
    ] == [
        ([0, 5], 1.25e-3, "public_static_zz_calibration", "CuOperator"),
        ([1, 4], JOINT_CHANNEL_ZETA_RAD_PER_NS, "axis1_primitive_default", "CuOperator"),
    ]

    collapse_families = [
        (term["operator_family"], term["support"], term["data_type"])
        for term in lowered["collapse_terms"]
    ]
    assert len(collapse_families) == 18
    assert ("T1_UP", [0], "CuOperator") in collapse_families
    assert ("T2", [5], "CuOperator") in collapse_families
    assert ("T1", [5], "CuOperator") in collapse_families


def test_axis1_qutip_cuquantum_probe_lowers_readout_boundary_without_records():
    builder = CircuitBuilder(num_qubits=6)
    builder.declare_static_zz_couplings(((0, 5),))
    builder.measure(tuple(range(6)), key=tuple(f"m{i}" for i in range(6)), duration_ns=250.0)
    builder.detector("d05", xor=("m0", "m5"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_qutip_cuquantum_probe_manifest(schedule)

    lowered = manifest["lowered_substeps"][0]
    assert lowered["substep_kind"] == "measurement"
    assert [term["support"] for term in lowered["measurement_boundaries"]] == [
        [0],
        [1],
        [2],
        [3],
        [4],
        [5],
    ]
    assert [term["operator_family"] for term in lowered["collapse_terms"]].count("RD") == 6
    assert manifest["claims_record_execution"] is False
    assert manifest["claims_dem_decoder_semantics"] is False


def test_axis1_qutip_cuquantum_probe_refuses_cpu_device():
    schedule = _joint_channel_schedule()

    with pytest.raises(ValueError, match="GPU-only"):
        axis1_qutip_cuquantum_probe_manifest(schedule, device="cpu")


@pytest.mark.skipif(
    os.environ.get("AIQEC_RUN_QUTIP_STATE_PROBE") != "1",
    reason="qutip-cuquantum density state probe is an explicit slow GPU gate",
)
def test_axis1_qutip_cuquantum_state_probe_executes_over_cap_static_idle_zero_state():
    builder = CircuitBuilder(num_qubits=6)
    builder.declare_static_zz_couplings(((0, 5), (1, 4)))
    builder.idle(tuple(range(6)), duration_ns=75.0)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_qutip_cuquantum_state_probe_manifest(schedule)

    assert manifest["schema"] == "error_coupling_simulator.frontend.qutip_cuquantum_state_probe.v1"
    assert manifest["representability"] == (
        "axis1_qutip_cuquantum_state_probe_restricted_no_record_execution"
    )
    assert manifest["verdict"] == "pass"
    assert manifest["passed"] is True
    assert manifest["state_probe_executed"] is True
    assert manifest["execution_backend_contract"] == "qutip_cuquantum_state_probe"
    assert manifest["carrier_program"]["requires_scalable_backend"] is True
    assert manifest["claims_record_execution"] is False
    assert manifest["claims_dense_channel_evidence"] is False
    assert manifest["claims_dem_decoder_semantics"] is False
    assert manifest["claims_axis2_source_timeline"] is False
    assert manifest["claims_production_scalable_backend"] is False

    state = manifest["state_probe"]
    assert state["initial_state"] == "computational_zero_density_matrix"
    assert state["solver"] == "qutip.mesolve"
    assert state["final_state_data_type"] == "CuState"
    assert state["density_matrix_payload_serialized"] is False
    assert state["record_execution"] == "not_requested"
    assert state["trace_residual"] <= 1.0e-8
    assert abs(sum(state["final_z_probabilities"]) - 1.0) <= 1.0e-8
    assert state["final_z_probabilities"][0] >= 1.0 - 1.0e-8
    assert max(state["final_z_probabilities"][1:]) <= 1.0e-8
    assert [step["substep_id"] for step in state["applied_substeps"]] == ["s0000"]
    assert state["applied_substeps"][0]["route"] == "scalable_required"
    assert state["applied_substeps"][0]["hamiltonian_term_count"] == 2
    assert state["applied_substeps"][0]["collapse_term_count"] == 12


def test_axis1_qutip_cuquantum_state_probe_fails_closed_on_measurement_boundary():
    builder = CircuitBuilder(num_qubits=6)
    builder.declare_static_zz_couplings(((0, 5),))
    builder.measure(tuple(range(6)), key=tuple(f"m{i}" for i in range(6)), duration_ns=250.0)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_qutip_cuquantum_state_probe_manifest(schedule)

    assert manifest["schema"] == "error_coupling_simulator.frontend.qutip_cuquantum_state_probe.v1"
    assert manifest["verdict"] == "fail"
    assert manifest["passed"] is False
    assert manifest["state_probe_executed"] is False
    assert manifest["blocked_reason"] == "measurement_boundary_not_supported_by_state_probe"
    assert manifest["claims_record_execution"] is False
    assert manifest["claims_dense_channel_evidence"] is False
    assert manifest["claims_dem_decoder_semantics"] is False


def test_axis1_qutip_cuquantum_state_probe_refuses_cpu_device():
    schedule = _joint_channel_schedule()

    with pytest.raises(ValueError, match="GPU-only"):
        axis1_qutip_cuquantum_state_probe_manifest(schedule, device="cpu")


def test_axis1_qutip_cuquantum_trajectory_probe_executes_over_cap_static_idle_zero_state():
    builder = CircuitBuilder(num_qubits=6)
    builder.declare_static_zz_couplings(((0, 5), (1, 4)))
    builder.idle(tuple(range(6)), duration_ns=1.0e-6)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_qutip_cuquantum_trajectory_probe_manifest(schedule)

    assert manifest["schema"] == "error_coupling_simulator.frontend.qutip_cuquantum_trajectory_probe.v1"
    assert manifest["representability"] == (
        "axis1_qutip_cuquantum_trajectory_probe_no_record_execution"
    )
    assert manifest["verdict"] == "pass"
    assert manifest["passed"] is True
    assert manifest["trajectory_probe_executed"] is True
    assert manifest["execution_backend_contract"] == "qutip_cuquantum_trajectory_probe"
    assert manifest["carrier_program"]["requires_scalable_backend"] is True
    assert manifest["claims_record_execution"] is False
    assert manifest["claims_density_state_evidence"] is False
    assert manifest["claims_dense_channel_evidence"] is False
    assert manifest["claims_dem_decoder_semantics"] is False
    assert manifest["claims_axis2_source_timeline"] is False
    assert manifest["claims_production_scalable_backend"] is False

    traj = manifest["trajectory_probe"]
    assert traj["initial_state"] == "computational_zero_ket"
    assert traj["solver"] == "qutip.mcsolve"
    assert traj["ntraj"] == 1
    assert traj["final_state_data_type"] == "CuState"
    assert traj["statevector_payload_serialized"] is False
    assert traj["record_execution"] == "not_requested"
    assert traj["norm_residual"] <= 1.0e-8
    assert abs(sum(traj["final_z_probabilities"]) - 1.0) <= 1.0e-8
    assert traj["final_z_probabilities"][0] >= 1.0 - 1.0e-8
    assert max(traj["final_z_probabilities"][1:]) <= 1.0e-8
    assert [step["substep_id"] for step in traj["applied_substeps"]] == ["s0000"]


def test_axis1_qutip_cuquantum_trajectory_probe_fails_closed_on_measurement_boundary():
    builder = CircuitBuilder(num_qubits=6)
    builder.declare_static_zz_couplings(((0, 5),))
    builder.measure(tuple(range(6)), key=tuple(f"m{i}" for i in range(6)), duration_ns=250.0)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_qutip_cuquantum_trajectory_probe_manifest(schedule)

    assert manifest["verdict"] == "fail"
    assert manifest["passed"] is False
    assert manifest["trajectory_probe_executed"] is False
    assert manifest["blocked_reason"] == "measurement_boundary_not_supported_by_state_probe"
    assert manifest["claims_record_execution"] is False


def test_axis1_qutip_cuquantum_trajectory_probe_refuses_cpu_device():
    schedule = _joint_channel_schedule()

    with pytest.raises(ValueError, match="GPU-only"):
        axis1_qutip_cuquantum_trajectory_probe_manifest(schedule, device="cpu")


def test_axis1_qutip_cuquantum_record_probe_executes_over_cap_z_readout_boundary():
    builder = CircuitBuilder(num_qubits=6)
    builder.declare_static_zz_couplings(((0, 5),))
    builder.measure(tuple(range(6)), key=tuple(f"m{i}" for i in range(6)), duration_ns=1.0e-6)
    builder.detector("d05", xor=("m0", "m5"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_qutip_cuquantum_record_probe_manifest(schedule)

    assert manifest["schema"] == "error_coupling_simulator.frontend.qutip_cuquantum_record_probe.v1"
    assert manifest["representability"] == (
        "axis1_qutip_cuquantum_record_probe_restricted_no_b8_no_decoder"
    )
    assert manifest["verdict"] == "pass"
    assert manifest["passed"] is True
    assert manifest["record_probe_executed"] is True
    assert manifest["execution_backend_contract"] == "qutip_cuquantum_record_probe"
    assert manifest["carrier_program"]["requires_scalable_backend"] is True
    assert manifest["claims_b8_artifact"] is False
    assert manifest["claims_decoder_integration"] is False
    assert manifest["claims_dense_channel_evidence"] is False
    assert manifest["claims_axis2_source_timeline"] is False
    assert manifest["claims_production_scalable_backend"] is False

    record = manifest["record_probe"]
    assert record["solver"] == "qutip.mcsolve"
    assert record["measurement_basis"] == "Z"
    assert record["measurement_keys"] == ["m0", "m1", "m2", "m3", "m4", "m5"]
    assert record["record_count"] == 64
    assert record["measurement_records"][0] == [0, 0, 0, 0, 0, 0]
    assert record["record_probabilities"][0] >= 1.0 - 1.0e-8
    assert max(record["record_probabilities"][1:]) <= 1.0e-8
    assert abs(sum(record["record_probabilities"]) - 1.0) <= 1.0e-8
    assert record["detector_records_emitted"] is True
    assert record["detector_names"] == ["d05"]
    assert record["detector_records"][0] == [0]
    assert record["logical_observables_emitted"] is False
    assert record["claims_b8_artifact"] is False
    assert record["claims_decoder_integration"] is False


def test_axis1_qutip_cuquantum_record_probe_supports_idle_then_partial_z_readout():
    builder = CircuitBuilder(num_qubits=6)
    builder.declare_static_zz_couplings(((0, 5),))
    builder.idle(tuple(range(6)), duration_ns=1.0e-6)
    builder.tick()
    builder.measure((0, 5), key=("m0", "m5"), duration_ns=1.0e-6)
    builder.detector("d05", xor=("m0", "m5"))
    builder.observable("logical_m5", xor=("m5",), index=0)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_qutip_cuquantum_record_probe_manifest(schedule)

    assert manifest["verdict"] == "pass"
    assert manifest["passed"] is True
    record = manifest["record_probe"]
    assert [step["substep_id"] for step in record["applied_substeps"]] == [
        "s0000",
        "s0002",
    ]
    assert record["measurement_keys"] == ["m0", "m5"]
    assert record["measurement_targets"] == [0, 5]
    assert record["measurement_records"] == [[0, 0], [1, 0], [0, 1], [1, 1]]
    assert record["record_count"] == 4
    assert record["record_probabilities"][0] >= 1.0 - 1.0e-8
    assert max(record["record_probabilities"][1:]) <= 1.0e-8
    assert record["detector_names"] == ["d05"]
    assert record["detector_records"] == [[0], [1], [1], [0]]
    assert record["logical_observable_names"] == ["logical_m5"]
    assert record["logical_observable_records"] == [[0], [0], [1], [1]]
    assert record["claims_b8_artifact"] is False
    assert record["claims_decoder_integration"] is False


def test_axis1_qutip_cuquantum_record_probe_supports_sequential_z_boundaries():
    builder = CircuitBuilder(num_qubits=6)
    builder.declare_static_zz_couplings(((0, 5),))
    builder.idle(tuple(range(6)), duration_ns=1.0e-6)
    builder.tick()
    builder.measure((0,), key=("m0",), duration_ns=1.0e-6)
    builder.tick()
    builder.idle(tuple(range(6)), duration_ns=1.0e-6)
    builder.tick()
    builder.measure((5,), key=("m5",), duration_ns=1.0e-6)
    builder.detector("d05", xor=("m0", "m5"))
    builder.observable("logical_m5", xor=("m5",), index=0)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_qutip_cuquantum_record_probe_manifest(schedule)

    assert manifest["verdict"] == "pass"
    assert manifest["passed"] is True
    record = manifest["record_probe"]
    assert [step["substep_id"] for step in record["applied_substeps"]] == [
        "s0000",
        "s0002",
        "s0004",
        "s0006",
    ]
    assert record["measurement_keys"] == ["m0", "m5"]
    assert record["measurement_targets"] == [0, 5]
    assert record["measurement_boundaries"] == [
        {"substep_id": "s0002", "measurement_keys": ["m0"], "measurement_targets": [0]},
        {"substep_id": "s0006", "measurement_keys": ["m5"], "measurement_targets": [5]},
    ]
    assert record["measurement_records"] == [[0, 0], [1, 0], [0, 1], [1, 1]]
    assert record["record_count"] == 4
    assert record["record_probabilities"][0] >= 1.0 - 1.0e-8
    assert max(record["record_probabilities"][1:]) <= 1.0e-8
    assert record["detector_names"] == ["d05"]
    assert record["detector_records"] == [[0], [1], [1], [0]]
    assert record["logical_observable_names"] == ["logical_m5"]
    assert record["logical_observable_records"] == [[0], [0], [1], [1]]
    assert record["claims_b8_artifact"] is False
    assert record["claims_decoder_integration"] is False
    assert record["claims_production_scalable_backend"] is False


def test_axis1_qutip_cuquantum_record_probe_lowers_frontend_h_before_z_readout():
    builder = CircuitBuilder(num_qubits=6)
    builder.declare_static_zz_couplings(((0, 5),))
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
        )
    )
    builder.h(0)
    builder.tick()
    builder.measure(
        tuple(range(6)),
        key=tuple(f"m{i}" for i in range(6)),
        duration_ns=1.0e-6,
    )
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_qutip_cuquantum_record_probe_manifest(schedule)

    assert manifest["verdict"] == "pass"
    assert manifest["passed"] is True
    assert manifest["record_probe_executed"] is True
    assert manifest["claims_b8_artifact"] is False
    assert manifest["claims_decoder_integration"] is False
    assert manifest["claims_dense_channel_evidence"] is False
    assert manifest["claims_axis2_source_timeline"] is False
    assert manifest["claims_production_scalable_backend"] is False

    record = manifest["record_probe"]
    assert [step["substep_id"] for step in record["applied_substeps"]] == [
        "s0000",
        "s0002",
    ]
    assert record["measurement_keys"] == ["m0", "m1", "m2", "m3", "m4", "m5"]
    assert record["measurement_targets"] == [0, 1, 2, 3, 4, 5]
    p_m0_zero = sum(
        probability
        for bits, probability in zip(
            record["measurement_records"],
            record["record_probabilities"],
            strict=True,
        )
        if bits[0] == 0
    )
    p_m0_one = sum(
        probability
        for bits, probability in zip(
            record["measurement_records"],
            record["record_probabilities"],
            strict=True,
        )
        if bits[0] == 1
    )
    leakage_to_other_readout_bits = sum(
        probability
        for bits, probability in zip(
            record["measurement_records"],
            record["record_probabilities"],
            strict=True,
        )
        if any(bits[index] for index in range(1, 6))
    )
    assert [p_m0_zero, p_m0_one] == pytest.approx([0.5, 0.5], abs=1.0e-8)
    assert leakage_to_other_readout_bits <= 1.0e-8
    assert record["applied_substeps"][0]["substep_kind"] == "one_qubit_gate"
    assert record["applied_substeps"][0]["hamiltonian_term_count"] == 2
    assert record["applied_substeps"][0]["hamiltonian_operator_families"] == [
        "CTRL_H",
        "ZZ",
    ]
    assert record["applied_substeps"][1]["substep_kind"] == "measurement"
    assert record["applied_substeps"][1]["measurement_boundary_count"] == 6


def test_axis1_qutip_cuquantum_record_probe_fails_closed_on_nonmeasurement_program():
    builder = CircuitBuilder(num_qubits=6)
    builder.declare_static_zz_couplings(((0, 5),))
    builder.idle(tuple(range(6)), duration_ns=1.0e-6)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_qutip_cuquantum_record_probe_manifest(schedule)

    assert manifest["verdict"] == "fail"
    assert manifest["passed"] is False
    assert manifest["record_probe_executed"] is False
    assert manifest["blocked_reason"] == "record_probe_requires_at_least_one_measurement_substep"
    assert manifest["claims_b8_artifact"] is False
    assert manifest["claims_decoder_integration"] is False


def test_axis1_qutip_cuquantum_record_probe_refuses_cpu_device():
    schedule = _joint_channel_schedule()

    with pytest.raises(ValueError, match="GPU-only"):
        axis1_qutip_cuquantum_record_probe_manifest(schedule, device="cpu")


def test_axis1_drive_cluster_covers_all_active_idle_participant_windows():
    builder = CircuitBuilder(num_qubits=3)
    builder.h(0)
    builder.measure((0, 1), key=("m0", "m1"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    evidence = axis1_substep_channel_evidence_manifest(schedule)
    coverage = evidence["coverage"]

    assert coverage["selected_positive_duration_substep_ids"] == ["s0000"]
    assert coverage["full_positive_duration_coverage"] is True
    assert coverage["positive_duration_coverage_fraction"] == 1.0
    assert coverage["positive_duration_window_coverage_fraction"] == 1.0
    assert coverage["partial_positive_duration_substeps"] == []
    assert coverage["participant_coverage"] == [
        {
            "substep_id": "s0000",
            "kind": "one_qubit_gate",
            "coverage_basis": "all_active_idle_pairs_visible_in_schedule",
            "dt_ns_nominal": 25.0,
            "expected_participants": [[0, 1], [0, 2]],
            "selected_participants": [[0, 1, 2]],
            "covered_participants": [[0, 1], [0, 2]],
            "missing_participants": [],
            "extra_selected_participants": [],
            "unpaired_qubits": [],
            "covered_unpaired_qubits": [],
            "full_participant_coverage": True,
            "participant_coverage_fraction": 1.0,
        }
    ]
    assert evidence["rows"][0]["row_kind"] == "one_qubit_drive_cluster_joint_channel"
    assert evidence["rows"][0]["participant"] == [0, 1, 2]
    assert evidence["rows"][0]["joint_channel"]["dimension"] == 8


def test_axis1_active_only_one_qubit_gate_lowers_local_joint_channel():
    builder = CircuitBuilder(num_qubits=1)
    builder.h(0)
    builder.measure(0, key="m0")
    schedule = circuit_ir_to_substep_schedule(builder.build())

    evidence = axis1_substep_channel_evidence_manifest(schedule)
    coverage = evidence["coverage"]
    assert coverage["full_positive_duration_coverage"] is True
    assert coverage["participant_coverage"] == [
        {
            "substep_id": "s0000",
            "kind": "one_qubit_gate",
            "coverage_basis": "active_only_one_qubit_controls_visible_in_schedule",
            "dt_ns_nominal": 25.0,
            "expected_participants": [],
            "selected_participants": [[0]],
            "covered_participants": [],
            "missing_participants": [],
            "extra_selected_participants": [],
            "unpaired_qubits": [],
            "covered_unpaired_qubits": [0],
            "full_participant_coverage": True,
            "participant_coverage_fraction": 1.0,
        }
    ]
    row = evidence["rows"][0]
    assert row["row_kind"] == "one_qubit_drive_local_joint_channel"
    assert row["participant"] == [0]
    assert row["primitive_names"] == ["T2", "T1"]
    assert row["joint_channel"]["dimension"] == 2
    assert [control["name"] for control in row["ideal_controls"]] == ["CTRL_H"]
    assert [record["name"] for record in row["lowered_mechanisms"]] == ["T2", "T1"]

    state = axis1_state_evolution_evidence_manifest(schedule)
    assert state["selection_partition"] == evidence["selection_partition"]
    assert state["state_evolution"]["applied_channel_count"] == 1

    record = axis1_measurement_record_evidence_manifest(schedule)
    assert record["selection_partition"] == evidence["selection_partition"]
    assert record["record_evidence"]["applied_channel_count"] == 1
    assert record["record_evidence"]["record_count"] == 2


def test_axis1_active_only_multi_one_qubit_layer_lowers_joint_controls():
    builder = CircuitBuilder(num_qubits=2)
    builder.h((0, 1))
    builder.measure((0, 1), key=("m0", "m1"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    evidence = axis1_substep_channel_evidence_manifest(schedule)
    row = evidence["rows"][0]
    assert row["row_kind"] == "multi_one_qubit_drive_local_joint_channel"
    assert row["participant"] == [0, 1]
    assert row["primitive_names"] == ["T2", "T1"]
    assert row["joint_channel"]["dimension"] == 4
    assert [control["name"] for control in row["ideal_controls"]] == ["CTRL_H", "CTRL_H"]
    assert [control["support"] for control in row["ideal_controls"]] == [[0], [1]]
    assert [
        (record["name"], record["support"])
        for record in row["lowered_mechanisms"]
        if record["generator_kind"] == "collapse"
    ] == [
        ("T2", [0]),
        ("T1", [0]),
        ("T2", [1]),
        ("T1", [1]),
    ]
    assert evidence["coverage"]["participant_coverage"][0]["covered_unpaired_qubits"] == [0, 1]
    assert evidence["coverage"]["full_positive_duration_coverage"] is True


def test_axis1_multi_active_drive_cluster_lowers_all_controls_jointly():
    builder = CircuitBuilder(num_qubits=4)
    builder.h((0, 2))
    builder.measure((0, 1, 2, 3), key=("m0", "m1", "m2", "m3"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    plan = build_axis1_schedule_selection_plan(schedule)
    multi = [
        selection
        for selection in plan.selections
        if selection.row_kind == "multi_one_qubit_drive_cluster_joint_channel"
    ]
    assert len(multi) == 1
    assert multi[0].participant == (0, 2, 1, 3)
    assert multi[0].coupling_edges == ()
    assert multi[0].primitive_names == ("T2", "T1", "T2_B", "T1_B")
    assert multi[0].mechanism_pair == ("CTRL_1Q_LAYER", "T2_T1_CLUSTER")

    evidence = axis1_substep_channel_evidence_manifest(schedule)
    assert evidence["coverage"]["full_positive_duration_coverage"] is True
    assert evidence["coverage"]["participant_coverage"] == [
        {
            "substep_id": "s0000",
            "kind": "one_qubit_gate",
            "coverage_basis": "all_active_idle_pairs_visible_in_schedule",
            "dt_ns_nominal": 25.0,
            "expected_participants": [[0, 1], [0, 3], [2, 1], [2, 3]],
            "selected_participants": [[0, 2, 1, 3]],
            "covered_participants": [[0, 1], [0, 3], [2, 1], [2, 3]],
            "missing_participants": [],
            "extra_selected_participants": [],
            "unpaired_qubits": [],
            "covered_unpaired_qubits": [],
            "full_participant_coverage": True,
            "participant_coverage_fraction": 1.0,
        }
    ]
    assert evidence["selection_partition"]["layers"][0]["window_count"] == 1
    assert evidence["selection_partition"]["layers"][0]["row_kinds"] == [
        "multi_one_qubit_drive_cluster_joint_channel"
    ]
    assert evidence["selection_partition"]["layers"][0]["participants"] == [[0, 2, 1, 3]]

    row = evidence["rows"][0]
    assert row["row_kind"] == "multi_one_qubit_drive_cluster_joint_channel"
    assert row["participant"] == [0, 2, 1, 3]
    assert row["joint_channel"]["dimension"] == 16
    assert [control["name"] for control in row["ideal_controls"]] == ["CTRL_H", "CTRL_H"]
    assert [control["support"] for control in row["ideal_controls"]] == [[0], [1]]
    collapse_records = [
        (record["name"], record["support"])
        for record in row["lowered_mechanisms"]
        if record["generator_kind"] == "collapse"
    ]
    assert collapse_records == [
        ("T2", [0]),
        ("T1", [0]),
        ("T2", [1]),
        ("T1", [1]),
        ("T2_B", [2]),
        ("T1_B", [2]),
        ("T2_B", [3]),
        ("T1_B", [3]),
    ]

    state = axis1_state_evolution_evidence_manifest(schedule)
    assert state["selection_partition"] == evidence["selection_partition"]
    assert state["state_evolution"]["applied_channel_count"] == 1
    assert state["state_evolution"]["applied_layers"][0]["window_count"] == 1
    assert state["state_evolution"]["applied_layers"][0]["same_substep_semantics"] == (
        "parallel_disjoint_local_windows_or_single_union_support"
    )

    record = axis1_measurement_record_evidence_manifest(schedule)
    assert record["selection_partition"] == evidence["selection_partition"]
    assert record["record_evidence"]["application_semantics"] == (
        "schedule_order_selected_joint_channels_with_parallel_disjoint_or_union_support_layers_then_measurements"
    )
    assert record["record_evidence"]["applied_channel_count"] == 1
    assert record["record_evidence"]["applied_layers"][0]["window_count"] == 1
    assert record["record_evidence"]["record_count"] == 16


def test_axis1_two_qubit_cz_with_idle_spectator_lowers_union_support_cluster():
    builder = CircuitBuilder(num_qubits=3)
    builder.declare_static_zz_couplings(((0, 1),))
    builder.cz((0, 1))
    builder.measure((0, 1, 2), key=("m0", "m1", "m2"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    plan = build_axis1_schedule_selection_plan(schedule)
    clusters = [
        selection
        for selection in plan.selections
        if selection.row_kind == "two_qubit_control_zz_cluster_joint_channel"
    ]
    assert len(clusters) == 1
    assert clusters[0].participant == (0, 1, 2)
    assert clusters[0].coupling_edges == ((0, 1),)

    evidence = axis1_substep_channel_evidence_manifest(schedule)
    assert evidence["coverage"]["participant_coverage"] == [
        {
            "substep_id": "s0000",
            "kind": "two_qubit_gate",
            "coverage_basis": "scheduled_two_qubit_gate_participants_plus_idle_qubits",
            "dt_ns_nominal": 30.0,
            "expected_participants": [[0, 1]],
            "selected_participants": [[0, 1, 2]],
            "covered_participants": [[0, 1]],
            "missing_participants": [],
            "extra_selected_participants": [],
            "unpaired_qubits": [],
            "covered_unpaired_qubits": [2],
            "full_participant_coverage": True,
            "participant_coverage_fraction": 1.0,
        }
    ]
    row = evidence["rows"][0]
    assert row["row_kind"] == "two_qubit_control_zz_cluster_joint_channel"
    assert row["participant"] == [0, 1, 2]
    assert row["coupling_edges"] == [[0, 1]]
    assert row["joint_channel"]["dimension"] == 8
    assert [control["name"] for control in row["ideal_controls"]] == ["CTRL_CZ"]
    assert [control["support"] for control in row["ideal_controls"]] == [[0, 1]]
    assert [
        (record["name"], record["support"])
        for record in row["lowered_mechanisms"]
        if record["generator_kind"] == "hamiltonian"
    ] == [("ZZ", [0, 1])]
    assert [
        (record["name"], record["support"])
        for record in row["lowered_mechanisms"]
        if record["generator_kind"] == "collapse"
    ] == [
        ("T2", [0]),
        ("T1", [0]),
        ("T2", [1]),
        ("T1", [1]),
        ("T2_B", [2]),
        ("T1_B", [2]),
    ]

    state = axis1_state_evolution_evidence_manifest(schedule)
    assert state["selection_partition"] == evidence["selection_partition"]
    assert state["state_evolution"]["applied_channel_count"] == 1

    record = axis1_measurement_record_evidence_manifest(schedule)
    assert record["selection_partition"] == evidence["selection_partition"]
    assert record["record_evidence"]["applied_channel_count"] == 1
    assert record["record_evidence"]["record_count"] == 8


def test_axis1_two_qubit_cx_with_idle_spectator_preserves_ordered_cluster_control():
    builder = CircuitBuilder(num_qubits=3)
    builder.cx((1, 0))
    builder.measure((0, 1, 2), key=("m0", "m1", "m2"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    evidence = axis1_substep_channel_evidence_manifest(schedule)
    row = evidence["rows"][0]
    assert row["row_kind"] == "two_qubit_control_cluster_joint_channel"
    assert row["participant"] == [0, 1, 2]
    assert row["coupling_edges"] == []
    assert row["primitive_names"] == ["T2", "T1", "T2_B", "T1_B"]
    assert row["joint_channel"]["dimension"] == 8
    assert [control["name"] for control in row["ideal_controls"]] == ["CTRL_CX"]
    assert [control["support"] for control in row["ideal_controls"]] == [[1, 0]]
    assert evidence["coverage"]["participant_coverage"][0]["covered_participants"] == [[1, 0]]
    assert evidence["coverage"]["participant_coverage"][0]["covered_unpaired_qubits"] == [2]
    assert evidence["coverage"]["full_positive_duration_coverage"] is True


def test_axis1_non_cz_two_qubit_static_zz_active_pair_lowers_one_joint_cluster():
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_static_zz_couplings(((0, 1),))
    builder.gate("SWAP", (0, 1))
    builder.measure((0, 1), key=("m0", "m1"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    plan = build_axis1_schedule_selection_plan(schedule)
    active_rows = [
        selection for selection in plan.selections if selection.substep_id == "s0000"
    ]
    assert len(active_rows) == 1
    assert active_rows[0].row_kind == "two_qubit_control_zz_cluster_joint_channel"
    assert active_rows[0].participant == (0, 1)
    assert active_rows[0].coupling_edges == ((0, 1),)

    evidence = axis1_substep_channel_evidence_manifest(schedule)
    assert evidence["coverage"]["full_positive_duration_coverage"] is True
    row = evidence["rows"][0]
    assert row["row_kind"] == "two_qubit_control_zz_cluster_joint_channel"
    assert row["participant"] == [0, 1]
    assert row["coupling_edges"] == [[0, 1]]
    assert row["primitive_names"] == ["ZZ", "T2", "T1", "T2_B", "T1_B"]
    assert row["joint_channel"]["assembly_semantics"] == "single_joint_generator_expm"
    assert [control["name"] for control in row["ideal_controls"]] == ["CTRL_SWAP"]
    assert [
        (record["name"], record["support"])
        for record in row["lowered_mechanisms"]
        if record["generator_kind"] == "hamiltonian"
    ] == [("ZZ", [0, 1])]

    state = axis1_state_evolution_evidence_manifest(schedule)
    assert state["state_evolution"]["applied_channel_count"] == 1
    record = axis1_measurement_record_evidence_manifest(schedule)
    assert record["record_evidence"]["applied_channel_count"] == 1
    assert record["record_evidence"]["record_count"] == 4

    ordered = CircuitBuilder(num_qubits=2)
    ordered.declare_static_zz_couplings(((0, 1),))
    ordered.cx((1, 0))
    ordered.measure((0, 1), key=("m0", "m1"))
    ordered_row = axis1_substep_channel_evidence_manifest(
        circuit_ir_to_substep_schedule(ordered.build())
    )["rows"][0]
    assert ordered_row["row_kind"] == "two_qubit_control_zz_cluster_joint_channel"
    assert ordered_row["coupling_edges"] == [[0, 1]]
    assert ordered_row["ideal_controls"][0]["name"] == "CTRL_CX"
    assert ordered_row["ideal_controls"][0]["support"] == [1, 0]


def test_axis1_same_substep_non_cz_two_qubit_controls_are_parallel_windows():
    builder = CircuitBuilder(num_qubits=4)
    builder.gate("SWAP", (0, 1, 2, 3))
    builder.measure((0, 1, 2, 3), key=("m0", "m1", "m2", "m3"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    plan = build_axis1_schedule_selection_plan(schedule)
    active_rows = [
        selection for selection in plan.selections if selection.substep_id == "s0000"
    ]
    assert [selection.participant for selection in active_rows] == [(0, 1), (2, 3)]

    evidence = axis1_substep_channel_evidence_manifest(schedule)
    assert evidence["coverage"]["full_positive_duration_coverage"] is True
    assert evidence["selection_partition"]["layers"] == [
        {
            "substep_id": "s0000",
            "order_index": 0,
            "substep_kind": "two_qubit_gate",
            "selection_ids": [
                "s0000:two_qubit_control_joint_channel:0_1",
                "s0000:two_qubit_control_joint_channel:2_3",
            ],
            "row_kinds": [
                "two_qubit_control_joint_channel",
                "two_qubit_control_joint_channel",
            ],
            "participants": [[0, 1], [2, 3]],
            "window_count": 2,
            "same_substep_semantics": (
                "qubit_disjoint_parallel_windows_or_single_union_support"
            ),
        }
    ]
    assert [row["ideal_controls"][0]["name"] for row in evidence["rows"]] == [
        "CTRL_SWAP",
        "CTRL_SWAP",
    ]

    state = axis1_state_evolution_evidence_manifest(schedule)
    assert state["state_evolution"]["applied_layers"][0]["window_count"] == 2
    assert state["state_evolution"]["applied_layers"][0]["same_substep_semantics"] == (
        "parallel_disjoint_local_windows_or_single_union_support"
    )
    record = axis1_measurement_record_evidence_manifest(schedule)
    assert record["record_evidence"]["applied_layers"][0]["window_count"] == 2
    assert record["record_evidence"]["record_count"] == 16


def test_axis1_drive_static_zz_cluster_lowers_shared_active_edges_jointly():
    builder = CircuitBuilder(num_qubits=3)
    builder.declare_static_zz_couplings(((0, 1), (0, 2)))
    builder.cz((0, 1))
    builder.tick()
    builder.cz((0, 2))
    builder.tick()
    builder.h(0)
    builder.measure((0, 1, 2), key=("m0", "m1", "m2"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    plan = build_axis1_schedule_selection_plan(schedule)
    clusters = [
        selection
        for selection in plan.selections
        if selection.row_kind == "one_qubit_drive_zz_cluster_joint_channel"
    ]
    assert len(clusters) == 1
    cluster = clusters[0]
    assert cluster.participant == (0, 1, 2)
    assert cluster.coupling_edges == ((0, 1), (0, 2))
    assert cluster.primitive_names == ("ZZ", "T2", "T1", "T2_B", "T1_B")
    assert not [
        selection
        for selection in plan.selections
        if selection.substep_id == cluster.substep_id
        and selection.row_kind == "one_qubit_drive_zz_joint_channel"
    ]

    evidence = axis1_substep_channel_evidence_manifest(schedule)
    h_layer = next(
        layer
        for layer in evidence["selection_partition"]["layers"]
        if layer["substep_id"] == cluster.substep_id
    )
    assert h_layer["participants"] == [[0, 1, 2]]
    assert h_layer["same_substep_semantics"] == (
        "qubit_disjoint_parallel_windows_or_single_union_support"
    )
    h_coverage = next(
        record
        for record in evidence["coverage"]["participant_coverage"]
        if record["substep_id"] == cluster.substep_id
    )
    assert h_coverage["expected_participants"] == [[0, 1], [0, 2]]
    assert h_coverage["selected_participants"] == [[0, 1, 2]]
    assert h_coverage["covered_participants"] == [[0, 1], [0, 2]]
    assert h_coverage["full_participant_coverage"] is True

    cluster_row = next(
        row
        for row in evidence["rows"]
        if row["row_kind"] == "one_qubit_drive_zz_cluster_joint_channel"
    )
    assert cluster_row["participant"] == [0, 1, 2]
    assert cluster_row["coupling_edges"] == [[0, 1], [0, 2]]
    assert cluster_row["joint_channel"]["dimension"] == 8
    assert cluster_row["joint_channel"]["assembly_semantics"] == "single_joint_generator_expm"
    assert cluster_row["ideal_controls"][0]["name"] == "CTRL_H"
    zz_records = [
        record for record in cluster_row["lowered_mechanisms"] if record["name"] == "ZZ"
    ]
    assert [record["support"] for record in zz_records] == [[0, 1], [0, 2]]
    collapse_records = [
        (record["name"], record["support"])
        for record in cluster_row["lowered_mechanisms"]
        if record["generator_kind"] == "collapse"
    ]
    assert collapse_records == [
        ("T2", [0]),
        ("T1", [0]),
        ("T2_B", [1]),
        ("T1_B", [1]),
        ("T2_B", [2]),
        ("T1_B", [2]),
    ]

    state = axis1_state_evolution_evidence_manifest(schedule)
    assert state["selection_partition"] == evidence["selection_partition"]
    state_cluster = next(
        step
        for step in state["state_evolution"]["applied_steps"]
        if step["row_kind"] == "one_qubit_drive_zz_cluster_joint_channel"
    )
    assert state_cluster["coupling_edges"] == [[0, 1], [0, 2]]
    assert state_cluster["channel_assembly"]["dimension"] == 8

    record = axis1_measurement_record_evidence_manifest(schedule)
    assert record["selection_partition"] == evidence["selection_partition"]
    record_cluster = next(
        step
        for step in record["record_evidence"]["applied_steps"]
        if step["row_kind"] == "one_qubit_drive_zz_cluster_joint_channel"
    )
    assert record_cluster["coupling_edges"] == [[0, 1], [0, 2]]
    assert record_cluster["channel_assembly"]["assembly_semantics"] == (
        "single_joint_generator_expm"
    )
    assert record["record_evidence"]["record_count"] == 8


def test_axis1_static_zz_cluster_handles_mixed_spectators_and_active_orientation():
    builder = CircuitBuilder(num_qubits=4)
    builder.declare_static_zz_couplings(((1, 2),))
    builder.cz((1, 2))
    builder.tick()
    builder.h(2)
    builder.measure((0, 1, 2, 3), key=("m0", "m1", "m2", "m3"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    plan = build_axis1_schedule_selection_plan(schedule)
    cluster = next(
        selection
        for selection in plan.selections
        if selection.row_kind == "one_qubit_drive_zz_cluster_joint_channel"
    )
    assert cluster.participant == (2, 0, 1, 3)
    assert cluster.coupling_edges == ((1, 2),)

    evidence = axis1_substep_channel_evidence_manifest(schedule)
    row = next(
        row
        for row in evidence["rows"]
        if row["row_kind"] == "one_qubit_drive_zz_cluster_joint_channel"
    )
    assert row["participant"] == [2, 0, 1, 3]
    assert row["coupling_edges"] == [[1, 2]]
    assert row["joint_channel"]["dimension"] == 16
    zz_records = [record for record in row["lowered_mechanisms"] if record["name"] == "ZZ"]
    assert [record["support"] for record in zz_records] == [[0, 2]]
    spectator_collapse_supports = [
        record["support"]
        for record in row["lowered_mechanisms"]
        if record["name"] in {"T2_B", "T1_B"}
    ]
    assert spectator_collapse_supports == [[1], [1], [2], [2], [3], [3]]


def test_axis1_static_zz_cluster_includes_idle_idle_edges_in_union_support():
    builder = CircuitBuilder(num_qubits=3)
    builder.declare_static_zz_couplings(((1, 2),))
    builder.cz((1, 2))
    builder.tick()
    builder.h(0)
    builder.measure((0, 1, 2), key=("m0", "m1", "m2"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    plan = build_axis1_schedule_selection_plan(schedule)
    cluster = next(
        selection
        for selection in plan.selections
        if selection.row_kind == "one_qubit_drive_zz_cluster_joint_channel"
    )
    assert cluster.participant == (0, 1, 2)
    assert cluster.coupling_edges == ((1, 2),)

    evidence = axis1_substep_channel_evidence_manifest(schedule)
    row = next(
        row
        for row in evidence["rows"]
        if row["selection_id"] == cluster.selection_id
    )
    assert row["participant"] == [0, 1, 2]
    assert row["coupling_edges"] == [[1, 2]]
    assert row["joint_channel"]["dimension"] == 8
    assert [control["support"] for control in row["ideal_controls"]] == [[0]]
    zz_records = [record for record in row["lowered_mechanisms"] if record["name"] == "ZZ"]
    assert [record["support"] for record in zz_records] == [[1, 2]]
    collapse_records = [
        (record["name"], record["support"])
        for record in row["lowered_mechanisms"]
        if record["generator_kind"] == "collapse"
    ]
    assert collapse_records == [
        ("T2", [0]),
        ("T1", [0]),
        ("T2_B", [1]),
        ("T1_B", [1]),
        ("T2_B", [2]),
        ("T1_B", [2]),
    ]


def test_axis1_multi_active_static_zz_cluster_lowers_shared_spectator_jointly():
    builder = CircuitBuilder(num_qubits=3)
    builder.declare_static_zz_couplings(((0, 1), (1, 2)))
    builder.cz((0, 1))
    builder.tick()
    builder.cz((1, 2))
    builder.tick()
    builder.h((0, 2))
    builder.measure((0, 1, 2), key=("m0", "m1", "m2"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    plan = build_axis1_schedule_selection_plan(schedule)
    clusters = [
        selection
        for selection in plan.selections
        if selection.row_kind == "multi_one_qubit_drive_zz_cluster_joint_channel"
    ]
    assert len(clusters) == 1
    cluster = clusters[0]
    assert cluster.participant == (0, 2, 1)
    assert cluster.coupling_edges == ((0, 1), (1, 2))
    assert cluster.primitive_names == ("ZZ", "T2", "T1", "T2_B", "T1_B")
    assert cluster.mechanism_pair == ("CTRL_1Q_LAYER", "ZZ_CLUSTER")
    assert not [
        selection
        for selection in plan.selections
        if selection.substep_id == cluster.substep_id
        and selection.row_kind == "one_qubit_drive_zz_joint_channel"
    ]

    evidence = axis1_substep_channel_evidence_manifest(schedule)
    h_layer = next(
        layer
        for layer in evidence["selection_partition"]["layers"]
        if layer["substep_id"] == cluster.substep_id
    )
    assert h_layer["window_count"] == 1
    assert h_layer["row_kinds"] == ["multi_one_qubit_drive_zz_cluster_joint_channel"]
    assert h_layer["participants"] == [[0, 2, 1]]
    h_coverage = next(
        record
        for record in evidence["coverage"]["participant_coverage"]
        if record["substep_id"] == cluster.substep_id
    )
    assert h_coverage["expected_participants"] == [[0, 1], [2, 1]]
    assert h_coverage["selected_participants"] == [[0, 2, 1]]
    assert h_coverage["covered_participants"] == [[0, 1], [2, 1]]
    assert h_coverage["full_participant_coverage"] is True

    row = next(row for row in evidence["rows"] if row["selection_id"] == cluster.selection_id)
    assert row["joint_channel"]["dimension"] == 8
    assert row["coupling_edges"] == [[0, 1], [1, 2]]
    assert [control["name"] for control in row["ideal_controls"]] == ["CTRL_H", "CTRL_H"]
    assert [control["support"] for control in row["ideal_controls"]] == [[0], [1]]
    zz_records = [record for record in row["lowered_mechanisms"] if record["name"] == "ZZ"]
    assert [record["support"] for record in zz_records] == [[0, 2], [1, 2]]
    collapse_records = [
        (record["name"], record["support"])
        for record in row["lowered_mechanisms"]
        if record["generator_kind"] == "collapse"
    ]
    assert collapse_records == [
        ("T2", [0]),
        ("T1", [0]),
        ("T2", [1]),
        ("T1", [1]),
        ("T2_B", [2]),
        ("T1_B", [2]),
    ]

    state = axis1_state_evolution_evidence_manifest(schedule)
    assert state["selection_partition"] == evidence["selection_partition"]
    state_cluster = next(
        step
        for step in state["state_evolution"]["applied_steps"]
        if step["selection_id"] == cluster.selection_id
    )
    assert state_cluster["coupling_edges"] == [[0, 1], [1, 2]]

    record = axis1_measurement_record_evidence_manifest(schedule)
    assert record["selection_partition"] == evidence["selection_partition"]
    record_cluster = next(
        step
        for step in record["record_evidence"]["applied_steps"]
        if step["selection_id"] == cluster.selection_id
    )
    assert record_cluster["coupling_edges"] == [[0, 1], [1, 2]]
    assert record["record_evidence"]["record_count"] == 8


def test_axis1_active_only_static_zz_layer_lowers_one_joint_cluster():
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_static_zz_couplings(((0, 1),))
    builder.cz((0, 1))
    builder.tick()
    builder.h((0, 1))
    builder.measure((0, 1), key=("m0", "m1"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    plan = build_axis1_schedule_selection_plan(schedule)
    cluster = next(
        selection
        for selection in plan.selections
        if selection.row_kind == "multi_one_qubit_drive_zz_cluster_joint_channel"
    )
    assert cluster.participant == (0, 1)
    assert cluster.coupling_edges == ((0, 1),)

    evidence = axis1_substep_channel_evidence_manifest(schedule)
    row = next(row for row in evidence["rows"] if row["selection_id"] == cluster.selection_id)
    assert row["joint_channel"]["dimension"] == 4
    assert row["coupling_edges"] == [[0, 1]]
    assert row["primitive_names"] == ["ZZ", "T2", "T1"]
    assert row["context_mechanisms"] == ["T2", "T1"]
    assert [control["name"] for control in row["ideal_controls"]] == ["CTRL_H", "CTRL_H"]
    zz_records = [record for record in row["lowered_mechanisms"] if record["name"] == "ZZ"]
    assert [record["support"] for record in zz_records] == [[0, 1]]
    assert evidence["coverage"]["participant_coverage"][-1]["covered_unpaired_qubits"] == [0, 1]


def test_axis1_coupling_edge_metadata_fails_closed_for_invalid_rows():
    kwargs = dict(
        selection_id="bad",
        substep_id="s0000",
        substep_kind="one_qubit_gate",
        participant=(0, 1, 2),
        primitive_names=("ZZ", "T2"),
        mechanism_pair=("CTRL_1Q", "ZZ_CLUSTER"),
        context_mechanisms=("T2",),
        operation_names=("H",),
        source_step_indices=(0,),
        operation_records=(),
        dt_ns_nominal=25.0,
        dt_ns_bracket=(20.0, 30.0),
        dt_source="test",
        mechanism_slots=("drive", "idle", "spectator"),
        reason="test invalid edge metadata",
    )
    with pytest.raises(ValueError, match="only valid"):
        Axis1MechanismSelection(
            **kwargs,
            row_kind="one_qubit_drive_cluster_joint_channel",
            coupling_edges=((0, 1),),
        )
    with pytest.raises(ValueError, match="requires coupling_edges"):
        Axis1MechanismSelection(
            **kwargs,
            row_kind="one_qubit_drive_zz_cluster_joint_channel",
            coupling_edges=(),
        )
    with pytest.raises(ValueError, match="contained in participant"):
        Axis1MechanismSelection(
            **kwargs,
            row_kind="one_qubit_drive_zz_cluster_joint_channel",
            coupling_edges=((1, 3),),
        )
    with pytest.raises(ValueError, match="requires coupling_edges"):
        Axis1MechanismSelection(
            **kwargs,
            row_kind="multi_one_qubit_drive_zz_cluster_joint_channel",
            coupling_edges=(),
        )
    with pytest.raises(ValueError, match="contained in participant"):
        Axis1MechanismSelection(
            **(
                kwargs
                | {
                    "substep_kind": "two_qubit_gate",
                    "participant": (0, 1),
                    "mechanism_pair": ("CTRL_CZ", "ZZ"),
                    "operation_names": ("CZ",),
                }
            ),
            row_kind="two_qubit_zz_joint_channel",
            coupling_edges=((0, 2),),
        )
    with pytest.raises(ValueError, match="selected participant pair"):
        Axis1MechanismSelection(
            **(
                kwargs
                | {
                    "substep_kind": "two_qubit_gate",
                    "participant": (0, 1, 2),
                    "mechanism_pair": ("CTRL_CZ", "ZZ"),
                    "operation_names": ("CZ",),
                }
            ),
            row_kind="two_qubit_zz_joint_channel",
            coupling_edges=((0, 1),),
        )


def test_joint_channel_comparison_emits_declared_rows_from_compiler_schedule():
    schedule = _joint_channel_schedule()
    rows = joint_channel_comparison_gate(schedule)

    assert len(rows) == 6
    assert all(isinstance(row, JointChannelComparisonRow) for row in rows)
    assert all(row.source_hash == schedule.source_hash for row in rows)
    assert all(row.passed for row in rows), [
        row.to_manifest() for row in rows if not row.passed
    ]
    assert {row.mechanism_pair for row in rows} == {("ZZ", "T2"), ("DR", "ZZ")}

    exact = [row for row in rows if row.mechanism_pair == ("ZZ", "T2")]
    assert [row.dt_ns for row in exact] == [25.0, 30.0, 45.0]
    for row in exact:
        assert row.expected_class == "exact_zero"
        assert row.participant == (0, 1)
        assert row.liouvillian_commutator_norm <= NUMERICAL_ZERO
        assert row.superop_distance <= SUPEROP_EXACTZERO_TOL
        assert row.leading_one_minus_F_e is None
        assert row.context_mechanisms == ()

    nonzero = [row for row in rows if row.mechanism_pair == ("DR", "ZZ")]
    assert [row.dt_ns for row in nonzero] == [20.0, 25.0, 30.0]
    lo, hi = JOINT_CHANNEL_DR_ZZ_BAND
    for row in nonzero:
        assert row.expected_class == "prediction_band_nonzero"
        assert row.participant == (0, 1)
        assert row.liouvillian_commutator_norm > JOINT_CHANNEL_NONZERO_COMMUTATOR_MIN
        assert row.superop_distance > JOINT_CHANNEL_NONZERO_SUPEROP_DISTANCE_MIN
        assert lo <= row.one_minus_F_e <= hi
        assert row.leading_one_minus_F_e is not None
        assert row.leading_one_minus_F_e > 0.0
        assert row.context_mechanisms == ("T2", "T1")

    manifest = joint_channel_comparison_manifest(schedule)
    assert manifest["schema"] == "error_coupling_simulator.frontend.joint_channel_comparison.v1"
    assert manifest["passed"] is True
    assert manifest["source_hash"] == schedule.source_hash
    assert manifest["compiler_provenance"]["schedule_seal_valid"] is True
    assert manifest["compiler_provenance"]["schedule_seal_public"] is False
    assert "seal_digest" not in json.dumps(manifest["compiler_provenance"])
    assert manifest["primitive_registry"]["registry_id"] == AXIS1_TWO_QUBIT_LOCAL_REGISTRY_ID
    assert manifest["primitive_registry"]["contains_operator_payload"] is False
    assert manifest["selection_plan"]["selector_id"] == "axis1_joint_channel_comparison_rows_v1"
    assert len(manifest["selection_plan"]["selections"]) == 2
    assert "row_id" in manifest["rows"][0]
    assert manifest["measured_on"] == "assembled q=2 substep channels from compiler schedule fixture"
    for row in manifest["rows"]:
        assert row["epistemic_class"] in {"a", "b", "c"}
        assert isinstance(row["epistemic_classes"], dict)
        assert row["source_step_indices"]
        assert row["source_operation_ids"]
        assert row["operations"]
        assert row["lowered_mechanisms"]
        assert row["dt_ns_nominal"] in {25.0, 30.0}
    exact_row = next(row for row in manifest["rows"] if row["exact_zero"])
    assert exact_row["value_metric"] == "superop_frobenius_distance_exact_zero_witness"
    assert exact_row["value"] == exact_row["superop_distance"]


def test_joint_channel_manifest_carries_anti_toy_details():
    manifest = joint_channel_comparison_manifest(_joint_channel_schedule())
    details = manifest["details"]

    assert details["schema"] == "error_coupling_simulator.frontend.joint_channel_comparison_anti_toy_details.v1"
    assert details["pass"] is True
    assert details["check1_exact_zero_control"]["pass"] is True
    assert details["check1_exact_zero_control"]["max_superop_frobenius_dist"] <= (
        SUPEROP_EXACTZERO_TOL
    )
    assert details["check2_broken_control_must_fail"]["pass"] is True
    assert details["check2_broken_control_must_fail"]["broken_fails_loudly"] is True

    powerlaws = details["check3_dr_zz_band_powerlaws"]
    assert powerlaws["pass"] is True
    assert powerlaws["physical"]["in_band"] is True
    assert powerlaws["physical"]["slope_ok"] is True
    assert powerlaws["physical"]["gated_powerlaw_scope"] == (
        "coherent_DR_ZZ_component_hamiltonian_only"
    )
    assert "full_substep_context_slope_FINDING" in powerlaws["physical"]
    assert powerlaws["fixed_omega"]["in_band"] is True
    assert powerlaws["fixed_omega"]["smalldt_slope_ok"] is True
    assert powerlaws["zeta_scaling"]["slope_ok"] is True


def test_joint_channel_gate_rejects_cx_as_silent_cz_substitute():
    builder = CircuitBuilder(num_qubits=2)
    builder.h(0)
    builder.tick()
    builder.cx((0, 1))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    with pytest.raises(ValueError, match="CX is not silently relabeled as CZ"):
        joint_channel_comparison_gate(schedule)


def test_joint_channel_gate_rejects_non_drive_one_qubit_gate_as_dr_row():
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_static_zz_couplings(((0, 1),))
    builder.gate("Z", 0)
    builder.tick()
    builder.cz((0, 1))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    with pytest.raises(ValueError, match="dr_zz_prediction_band"):
        joint_channel_comparison_gate(schedule)


def test_joint_channel_gate_does_not_mislabel_mixed_cx_cz_participants():
    circuit = CircuitIR(
        num_qubits=4,
        steps=(
            GateOp("H", (2,)),
            Tick(),
            GateOp("CX", (0, 1)),
            GateOp("CZ", (2, 3)),
        ),
        metadata={AXIS1_STATIC_ZZ_COUPLINGS_METADATA_KEY: [[2, 3]]},
    )
    schedule = circuit_ir_to_substep_schedule(circuit)

    rows = joint_channel_comparison_gate(schedule)
    assert {row.participant for row in rows} == {(2, 3)}


def test_joint_channel_selection_preserves_drive_active_spectator_orientation():
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_static_zz_couplings(((0, 1),))
    builder.h(1)
    builder.tick()
    builder.cz((0, 1))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    plan = build_axis1_joint_channel_selection_plan(schedule)
    exact = plan.require_kind("zz_t2_exact_zero")[0]
    nonzero = plan.require_kind("dr_zz_prediction_band")[0]

    assert plan.static_zz_pairs == ((0, 1),)
    assert exact.participant == (0, 1)
    assert nonzero.participant == (1, 0)


def test_stim_circuit_importer_builds_sealed_axis1_schedule_without_static_zz_inference():
    import stim

    circuit = stim.Circuit(
        """
        QUBIT_COORDS(0, 0) 0
        QUBIT_COORDS(1, 0) 1
        H 0
        TICK
        CZ 0 1
        MR 0
        DETECTOR rec[-1]
        OBSERVABLE_INCLUDE(0) rec[-1]
        """
    )

    schedule = stim_circuit_to_substep_schedule(circuit)
    manifest = schedule.to_manifest()

    assert schedule.source_kind == "stim_circuit"
    assert schedule.num_qubits == 2
    assert schedule.qubit_coords == {0: (0.0, 0.0), 1: (1.0, 0.0)}
    assert schedule.record_layout_ref["measurement_keys"] == ["m0"]
    assert schedule.record_layout_ref["detector_names"] == ["d0"]
    assert schedule.record_layout_ref["observable_names"] == ["logical0"]
    assert manifest["compiler_provenance"]["seal_present"] is True
    assert has_valid_compiler_schedule_seal(schedule)

    plan = build_axis1_joint_channel_selection_plan(schedule)
    assert plan.static_zz_pairs == ()
    assert [selection.row_kind for selection in plan.selections] == ["zz_t2_exact_zero"]
    with pytest.raises(ValueError, match="dr_zz_prediction_band"):
        joint_channel_comparison_gate(schedule)

    with_static_sidecar = stim_circuit_to_substep_schedule(
        circuit,
        static_zz_couplings=Axis1StaticZZDeviceSpec(
            edges=((0, 1),),
            num_qubits=2,
        ).edges,
    )
    assert with_static_sidecar.source_kind == "stim_circuit"
    assert with_static_sidecar.source_hash != schedule.source_hash
    assert with_static_sidecar.static_zz_couplings == ((0, 1),)
    static_plan = build_axis1_joint_channel_selection_plan(with_static_sidecar)
    assert {selection.row_kind for selection in static_plan.selections} == {
        "zz_t2_exact_zero",
        "dr_zz_prediction_band",
    }
    rows = joint_channel_comparison_gate(with_static_sidecar)
    assert {row.mechanism_pair for row in rows} == {("ZZ", "T2"), ("DR", "ZZ")}

    with_static_calibration = stim_circuit_to_substep_schedule(
        circuit,
        static_zz_couplings=((0, 1),),
        static_zz_calibrations=[
            {"edge": [0, 1], "zeta_rad_per_ns": 1.2e-3, "epistemic_class": "b"}
        ],
    )
    with_changed_calibration = stim_circuit_to_substep_schedule(
        circuit,
        static_zz_couplings=((0, 1),),
        static_zz_calibrations=[
            {"edge": [0, 1], "zeta_rad_per_ns": 2.4e-3, "epistemic_class": "b"}
        ],
    )
    assert with_static_calibration.static_zz_couplings == ((0, 1),)
    assert with_static_calibration.static_zz_calibrations == {
        (0, 1): {"zeta_rad_per_ns": 1.2e-3, "epistemic_class": "b"}
    }
    assert with_static_calibration.to_manifest()["static_zz_calibrations"] == [
        {"edge": [0, 1], "zeta_rad_per_ns": 1.2e-3, "epistemic_class": "b"}
    ]
    assert with_static_calibration.source_hash not in {
        schedule.source_hash,
        with_static_sidecar.source_hash,
    }
    assert with_changed_calibration.source_hash != with_static_calibration.source_hash

    with_axis1_context = stim_circuit_to_substep_schedule(
        circuit,
        axis1_local_lindblad_context=Axis1LocalLindbladContextSpec(
            include_thermal_excitation=True,
            gamma_up_per_ns=2.0e-4,
        ),
    )
    assert with_axis1_context.source_hash != schedule.source_hash
    assert with_axis1_context.axis1_local_lindblad_context[
        "include_thermal_excitation"
    ] is True
    context_plan = build_axis1_schedule_selection_plan(with_axis1_context)
    assert any("T1_UP" in selection.primitive_names for selection in context_plan.selections)

    with pytest.raises(ValueError, match="outside"):
        stim_circuit_to_substep_schedule(circuit, static_zz_couplings=((0, 2),))


def test_stim_circuit_importer_accepts_supported_two_qubit_controls_for_joint_channel_comparison():
    import stim

    for gate_name in sorted(AXIS1_FRONTEND_TWO_QUBIT_CONTROL_GATES):
        schedule = stim_circuit_to_substep_schedule(
            stim.Circuit(f"{gate_name} 0 1\nM 0 1")
        )
        assert schedule.source_kind == "stim_circuit"
        assert schedule.substeps[0].kind == "two_qubit_gate"
        assert schedule.substeps[0].operations[0].name == gate_name

        plan = build_axis1_schedule_selection_plan(schedule)
        assert len(plan.selections) == 1
        expected_row_kind = (
            "two_qubit_zz_joint_channel"
            if gate_name == "CZ"
            else "two_qubit_control_joint_channel"
        )
        assert plan.selections[0].row_kind == expected_row_kind

        evidence = axis1_substep_channel_evidence_manifest(schedule)
        assert evidence["source_kind"] == "stim_circuit"
        assert evidence["coverage"]["full_positive_duration_coverage"] is True
        assert evidence["rows"][0]["ideal_controls"][0]["name"] == f"CTRL_{gate_name}"
        assert evidence["rows"][0]["passed"] is True


def test_stim_circuit_importer_rejects_embedded_pauli_noise_as_axis1_schedule():
    import stim

    circuit = stim.Circuit(
        """
        H 0
        X_ERROR(0.1) 0
        """
    )

    with pytest.raises(ValueError, match="source-embedded Stim noise"):
        stim_circuit_to_substep_schedule(circuit)


def test_joint_channel_gate_rejects_handwritten_fake_schedule():
    schedule = _joint_channel_schedule()
    fake_substeps = []
    for substep in schedule.substeps:
        fake_substeps.append(
            type(substep)(
                substep_id=substep.substep_id,
                round_index=substep.round_index,
                tick_index=substep.tick_index,
                order_index=substep.order_index,
                kind=substep.kind,
                operations=substep.operations,
                active_qubits=substep.active_qubits,
                idle_qubits=substep.idle_qubits,
                participants=substep.participants,
                dt_ns_nominal=substep.dt_ns_nominal,
                dt_ns_bracket=substep.dt_ns_bracket,
                dt_source=substep.dt_source,
                mechanism_slots=substep.mechanism_slots,
                measurement_keys=substep.measurement_keys,
                window_support=substep.window_support,
                generated_by_compiler=False,
                epistemic_class=substep.epistemic_class,
            )
        )
    fake = SubstepSchedule(
        source_kind=schedule.source_kind,
        source_hash=schedule.source_hash,
        schedule_template=schedule.schedule_template,
        num_qubits=schedule.num_qubits,
        substeps=tuple(fake_substeps),
        duration_policy=schedule.duration_policy,
        qubit_roles=schedule.qubit_roles,
        qubit_coords=schedule.qubit_coords,
        record_layout_ref=schedule.record_layout_ref,
    )

    with pytest.raises(ValueError, match="compiler-generated substeps"):
        joint_channel_comparison_gate(fake)


def test_joint_channel_gate_rejects_handwritten_schedule_when_compiler_flag_is_omitted():
    schedule = _joint_channel_schedule()
    cloned_substeps = []
    for substep in schedule.substeps:
        cloned_substeps.append(
            type(substep)(
                substep_id=substep.substep_id,
                round_index=substep.round_index,
                tick_index=substep.tick_index,
                order_index=substep.order_index,
                kind=substep.kind,
                operations=substep.operations,
                active_qubits=substep.active_qubits,
                idle_qubits=substep.idle_qubits,
                participants=substep.participants,
                dt_ns_nominal=substep.dt_ns_nominal,
                dt_ns_bracket=substep.dt_ns_bracket,
                dt_source=substep.dt_source,
                mechanism_slots=substep.mechanism_slots,
                measurement_keys=substep.measurement_keys,
                window_support=substep.window_support,
                epistemic_class=substep.epistemic_class,
            )
        )
    fake = SubstepSchedule(
        source_kind=schedule.source_kind,
        source_hash=schedule.source_hash,
        schedule_template=schedule.schedule_template,
        num_qubits=schedule.num_qubits,
        substeps=tuple(cloned_substeps),
        duration_policy=schedule.duration_policy,
        qubit_roles=schedule.qubit_roles,
        qubit_coords=schedule.qubit_coords,
        record_layout_ref=schedule.record_layout_ref,
    )

    with pytest.raises(ValueError, match="compiler-generated substeps"):
        joint_channel_comparison_gate(fake)


def test_joint_channel_gate_rejects_forged_true_compiler_flags_without_builder_seal():
    schedule = _joint_channel_schedule()
    fake = SubstepSchedule(
        source_kind=schedule.source_kind,
        source_hash=schedule.source_hash,
        schedule_template=schedule.schedule_template,
        num_qubits=schedule.num_qubits,
        substeps=schedule.substeps,
        duration_policy=schedule.duration_policy,
        qubit_roles=schedule.qubit_roles,
        qubit_coords=schedule.qubit_coords,
        record_layout_ref=schedule.record_layout_ref,
    )

    assert all(substep.generated_by_compiler for substep in fake.substeps)
    assert not has_valid_compiler_schedule_seal(fake)
    with pytest.raises(ValueError, match="compiler-owned schedule seal"):
        joint_channel_comparison_gate(fake)


def test_joint_channel_gate_rejects_tampered_mechanism_slots():
    schedule = _joint_channel_schedule()
    tampered = []
    for substep in schedule.substeps:
        slots = ("idle", "spectator") if substep.kind == "one_qubit_gate" else substep.mechanism_slots
        tampered.append(
            type(substep)(
                substep_id=substep.substep_id,
                round_index=substep.round_index,
                tick_index=substep.tick_index,
                order_index=substep.order_index,
                kind=substep.kind,
                operations=substep.operations,
                active_qubits=substep.active_qubits,
                idle_qubits=substep.idle_qubits,
                participants=substep.participants,
                dt_ns_nominal=substep.dt_ns_nominal,
                dt_ns_bracket=substep.dt_ns_bracket,
                dt_source=substep.dt_source,
                mechanism_slots=slots,
                measurement_keys=substep.measurement_keys,
                window_support=substep.window_support,
                generated_by_compiler=substep.generated_by_compiler,
                epistemic_class=substep.epistemic_class,
            )
        )
    fake = SubstepSchedule(
        source_kind=schedule.source_kind,
        source_hash=schedule.source_hash,
        schedule_template=schedule.schedule_template,
        num_qubits=schedule.num_qubits,
        substeps=tuple(tampered),
        duration_policy=schedule.duration_policy,
        qubit_roles=schedule.qubit_roles,
        qubit_coords=schedule.qubit_coords,
        record_layout_ref=schedule.record_layout_ref,
    )

    with pytest.raises(ValueError, match="compiler-owned schedule seal"):
        joint_channel_comparison_gate(fake)
    with pytest.raises(ValueError, match="drive mechanism slots"):
        build_axis1_joint_channel_selection_plan(fake)


def test_joint_channel_gate_rejects_unimplemented_source_kind_even_with_valid_shape():
    schedule = _joint_channel_schedule()
    disguised = SubstepSchedule(
        source_kind="stim_pauli_source_projection",
        source_hash=schedule.source_hash,
        schedule_template=schedule.schedule_template,
        num_qubits=schedule.num_qubits,
        substeps=schedule.substeps,
        duration_policy=schedule.duration_policy,
        qubit_roles=schedule.qubit_roles,
        qubit_coords=schedule.qubit_coords,
        record_layout_ref=schedule.record_layout_ref,
    )

    with pytest.raises(ValueError, match="implemented schedule source kinds"):
        joint_channel_comparison_gate(disguised)


def test_joint_channel_evidence_writer_writes_only_comparison_json(tmp_path):
    schedule = _joint_channel_schedule()
    result = write_joint_channel_comparison_evidence(schedule, tmp_path / "comparison")

    assert result.joint_channel_comparison.name == "joint_channel_comparison.json"
    assert sorted(path.name for path in result.out_dir.iterdir()) == ["joint_channel_comparison.json"]
    assert not any(path.suffix in {".stim", ".dem", ".b8", ".npz"} for path in result.out_dir.iterdir())

    manifest = json.loads(result.joint_channel_comparison.read_text())
    assert manifest == result.manifest
    assert manifest["schema"] == "error_coupling_simulator.frontend.joint_channel_comparison.v1"
    assert manifest["verdict"] == "pass"
    assert manifest["passed"] is True
    assert manifest["measured_on"] == "assembled q=2 substep channels from compiler schedule fixture"
    assert manifest["metric"] == "composed-vs-joint channel infidelity"
    assert len(manifest["content_hash"]) == 64
    assert manifest["content_hash"] == result.content_hash
    assert len(manifest["rows"]) == 6

    row = manifest["rows"][0]
    assert {"pair_ij", "substep", "commutator_fro", "witness", "class"} <= set(row)
    assert "SourceTimeline" not in json.dumps(manifest)
    assert "source_timeline" not in json.dumps(manifest)


def test_axis1_substep_channel_evidence_assembles_joint_channels_without_payload(tmp_path):
    schedule = _joint_channel_schedule()
    manifest = axis1_substep_channel_evidence_manifest(schedule)

    assert manifest["schema"] == "error_coupling_simulator.frontend.substep_channel_evidence.v1"
    assert manifest["source_hash"] == schedule.source_hash
    assert manifest["compiler_provenance"]["schedule_seal_valid"] is True
    assert manifest["primitive_registry"]["registry_id"] == AXIS1_TWO_QUBIT_LOCAL_REGISTRY_ID
    assert manifest["representability"] == "axis1_joint_channel_evidence_no_record_emission"
    assert manifest["bridge_scope"] == (
        "joint channel carrier evidence only; no analog record emission, no Axis-2 source timeline, "
        "no leakage/qutrit integration"
    )
    assert len(manifest["rows"]) == 2
    assert manifest["coverage"]["selected_substep_ids"] == ["s0000", "s0002"]
    assert manifest["coverage"]["full_positive_duration_coverage"] is True
    assert manifest["coverage"]["positive_duration_coverage_fraction"] == 1.0
    assert manifest["coverage"]["omitted_substeps"] == [
        {
            "substep_id": "s0001",
            "kind": "barrier",
            "reason": "structural_or_no_nominal_dt",
            "dt_ns_nominal": None,
            "dt_ns_bracket": [0.0, 0.0],
        }
    ]
    assert {row["row_kind"] for row in manifest["rows"]} == {
        "one_qubit_drive_zz_joint_channel",
        "two_qubit_zz_joint_channel",
    }
    assert {tuple(row["mechanism_pair"]) for row in manifest["rows"]} == {
        ("CTRL_1Q", "ZZ"),
        ("CTRL_CZ", "ZZ"),
    }
    cz_row = next(row for row in manifest["rows"] if row["row_kind"] == "two_qubit_zz_joint_channel")
    assert cz_row["coupling_edges"] == [[0, 1]]
    assert [
        record["name"]
        for record in cz_row["lowered_mechanisms"]
        if record["name"] == "ZZ"
    ] == ["ZZ"]
    for row in manifest["rows"]:
        assert row["joint_channel"]["assembly_semantics"] == "single_joint_generator_expm"
        assert row["joint_channel"]["assembled_by"] == (
            "error_coupling_simulator.carrier.joint_lindbladian.assemble_substep_channel"
        )
        assert row["joint_channel"]["contains_serialized_channel_payload"] is False
        assert row["joint_channel"]["dimension"] == 4
        assert row["joint_channel"]["num_kraus"] >= 1
        assert row["joint_channel"]["tp_residual"] <= 1e-8
        assert row["joint_channel"]["contains_ideal_control_hamiltonian"] is True
        assert row["dt_ns"] in {25.0, 30.0}
        assert len(row["ideal_controls"]) == 1
        assert isinstance(row["lowered_mechanisms"], list)
    assert {tuple(row["primitive_names"]) for row in manifest["rows"]} == {
        ("ZZ", "T2", "T1", "T2_B", "T1_B"),
    }
    assert {row["ideal_controls"][0]["name"] for row in manifest["rows"]} == {
        "CTRL_H",
        "CTRL_CZ",
    }

    payload = json.dumps(manifest, sort_keys=True).lower()
    for forbidden in (
        "kraus_stack",
        "kraus_values",
        "choi_matrix",
        "superoperator_matrix",
        "source_timeline",
    ):
        assert forbidden not in payload

    result = write_axis1_substep_channel_evidence(schedule, tmp_path / "channels")
    assert result.channel_evidence.name == "axis1_substep_channels.json"
    assert sorted(path.name for path in result.out_dir.iterdir()) == [
        "axis1_substep_channels.json"
    ]
    assert result.manifest["content_hash"] == manifest["content_hash"]

    freeze = freeze_axis1_substep_channel_evidence(result.channel_evidence)
    assert freeze.freeze_path.name == "axis1_substep_channels.freeze.json"
    validation = validate_axis1_substep_channel_freeze(freeze.freeze_path)
    assert validation["pass"] is True
    assert validation["evidence_content_hash"] == result.content_hash

    bad_freeze = json.loads(freeze.freeze_path.read_text())
    bad_freeze["evidence_file"] = "../axis1_substep_channels.json"
    freeze.freeze_path.write_text(json.dumps(bad_freeze, indent=2, sort_keys=True) + "\n")
    with pytest.raises(ValueError, match="local filename"):
        validate_axis1_substep_channel_freeze(freeze.freeze_path)

    freeze = freeze_axis1_substep_channel_evidence(result.channel_evidence, overwrite=True)

    tampered = json.loads(result.channel_evidence.read_text())
    tampered["verdict"] = "fail"
    result.channel_evidence.write_text(json.dumps(tampered, indent=2, sort_keys=True) + "\n")
    with pytest.raises(ValueError, match="sha256 mismatch"):
        validate_axis1_substep_channel_freeze(freeze.freeze_path)


def test_axis1_substep_channel_evidence_refuses_cpu_device():
    schedule = _joint_channel_schedule()

    with pytest.raises(ValueError, match="GPU-only|joint_lindbladian is GPU-only"):
        axis1_substep_channel_evidence_manifest(schedule, device="cpu")


def test_axis1_substep_channel_evidence_rejects_unsealed_true_flag_schedule():
    schedule = _joint_channel_schedule()
    fake = _unsealed_schedule_clone(schedule)

    assert all(substep.generated_by_compiler for substep in fake.substeps)
    assert not has_valid_compiler_schedule_seal(fake)
    with pytest.raises(ValueError, match="compiler-owned schedule seal"):
        axis1_substep_channel_evidence_manifest(fake)


def test_axis1_state_and_record_evidence_reject_unsealed_true_flag_schedule():
    schedule = _joint_channel_schedule()
    fake = _unsealed_schedule_clone(schedule)

    assert all(substep.generated_by_compiler for substep in fake.substeps)
    assert not has_valid_compiler_schedule_seal(fake)
    with pytest.raises(ValueError, match="compiler-owned schedule seal"):
        axis1_state_evolution_evidence_manifest(fake)
    with pytest.raises(ValueError, match="compiler-owned schedule seal"):
        axis1_measurement_record_evidence_manifest(fake)


def test_axis1_state_evolution_evidence_applies_selected_joint_channels(tmp_path):
    schedule = _joint_channel_schedule()
    manifest = axis1_state_evolution_evidence_manifest(schedule)

    assert manifest["schema"] == "error_coupling_simulator.frontend.state_evolution_evidence.v1"
    assert manifest["representability"] == (
        "axis1_selected_joint_channel_state_evidence_no_record_emission"
    )
    assert manifest["source_hash"] == schedule.source_hash
    assert manifest["selection_plan"]["selector_id"] == "axis1_schedule_joint_channel_selector_v1"
    assert manifest["coverage"]["selected_substep_ids"] == ["s0000", "s0002"]
    assert manifest["state_evolution"]["initial_state"] == "computational_zero_density_matrix"
    assert manifest["state_evolution"]["applied_channel_count"] == 2
    assert manifest["state_evolution"]["application_semantics"] == (
        "schedule_order_selected_joint_channels_with_parallel_disjoint_or_union_support_layers"
    )
    assert manifest["state_evolution"]["claims_logical_gate_semantics"] is False
    assert manifest["state_evolution"]["claims_record_emission"] is False
    assert manifest["state_evolution"]["trace_residual"] <= 1e-8
    probs = manifest["state_evolution"]["final_z_probabilities"]
    assert len(probs) == 4
    assert abs(sum(probs) - 1.0) <= 1e-12
    assert [step["substep_id"] for step in manifest["state_evolution"]["applied_steps"]] == [
        "s0000",
        "s0002",
    ]
    assert [layer["window_count"] for layer in manifest["state_evolution"]["applied_layers"]] == [
        1,
        1,
    ]

    payload = json.dumps(manifest, sort_keys=True).lower()
    for forbidden in ("kraus_stack", "choi_matrix", "superoperator_matrix", "source_timeline"):
        assert forbidden not in payload

    result = write_axis1_state_evolution_evidence(schedule, tmp_path / "state")
    assert result.state_evidence.name == "axis1_state_evolution.json"
    assert sorted(path.name for path in result.out_dir.iterdir()) == [
        "axis1_state_evolution.json"
    ]
    assert result.manifest["content_hash"] == manifest["content_hash"]

    freeze = freeze_axis1_state_evolution_evidence(result.state_evidence)
    assert freeze.freeze_path.name == "axis1_state_evolution.freeze.json"
    validation = validate_axis1_state_evolution_freeze(freeze.freeze_path)
    assert validation["pass"] is True
    assert validation["evidence_content_hash"] == result.content_hash

    bad_freeze = json.loads(freeze.freeze_path.read_text())
    bad_freeze["evidence_file"] = "../axis1_state_evolution.json"
    freeze.freeze_path.write_text(json.dumps(bad_freeze, indent=2, sort_keys=True) + "\n")
    with pytest.raises(ValueError, match="local filename"):
        validate_axis1_state_evolution_freeze(freeze.freeze_path)

    freeze = freeze_axis1_state_evolution_evidence(result.state_evidence, overwrite=True)
    tampered = json.loads(result.state_evidence.read_text())
    tampered["verdict"] = "fail"
    result.state_evidence.write_text(json.dumps(tampered, indent=2, sort_keys=True) + "\n")
    with pytest.raises(ValueError, match="sha256 mismatch"):
        validate_axis1_state_evolution_freeze(freeze.freeze_path)


def test_axis1_evidence_supports_same_substep_parallel_disjoint_windows():
    builder = CircuitBuilder(num_qubits=4)
    builder.cz((0, 1, 2, 3))
    builder.tick()
    builder.measure((0, 1, 2, 3), key=("m0", "m1", "m2", "m3"))
    builder.detector("d01", xor=("m0", "m1"))
    builder.detector("d23", xor=("m2", "m3"))
    builder.observable("logical3", xor=("m3",), index=0)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    state_manifest = axis1_state_evolution_evidence_manifest(schedule)
    assert state_manifest["state_evolution"]["num_qubits"] == 4
    assert state_manifest["state_evolution"]["applied_channel_count"] == 2
    assert [layer["substep_id"] for layer in state_manifest["state_evolution"]["applied_layers"]] == [
        "s0000",
    ]
    assert [layer["window_count"] for layer in state_manifest["state_evolution"]["applied_layers"]] == [
        2,
    ]
    assert [layer["window_count"] for layer in state_manifest["selection_partition"]["layers"]] == [
        2,
    ]
    assert state_manifest["selection_partition"][
        "supports_are_qubit_disjoint_within_each_substep"
    ] is True
    assert len(state_manifest["state_evolution"]["final_z_probabilities"]) == 16
    assert abs(sum(state_manifest["state_evolution"]["final_z_probabilities"]) - 1.0) <= 1e-12

    record_manifest = axis1_measurement_record_evidence_manifest(schedule)
    record = record_manifest["record_evidence"]
    assert record["num_qubits"] == 4
    assert record["applied_channel_count"] == 2
    assert record["record_count"] == 16
    assert record["measurement_keys"] == ["m0", "m1", "m2", "m3"]
    assert record_manifest["selection_partition"] == state_manifest["selection_partition"]
    assert [layer["window_count"] for layer in record["applied_layers"]] == [2]
    assert record["detector_names"] == ["d01", "d23"]
    assert record["logical_observable_names"] == ["logical3"]
    assert record["claims_b8_artifact"] is False
    assert record["claims_overlapping_window_joint_generator"] is False
    expected_detectors = [
        [(row[0] + row[1]) % 2, (row[2] + row[3]) % 2]
        for row in record["measurement_records"]
    ]
    expected_logical = [[row[3]] for row in record["measurement_records"]]
    assert record["detector_records"] == expected_detectors
    assert record["logical_observable_records"] == expected_logical


def test_axis1_same_substep_two_qubit_controls_preserve_cross_window_static_zz_edge():
    builder = CircuitBuilder(num_qubits=4)
    builder.declare_static_zz_couplings(((1, 2),))
    builder.cz((0, 1, 2, 3))
    builder.tick()
    builder.measure((0, 1, 2, 3), key=("m0", "m1", "m2", "m3"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    plan = build_axis1_schedule_selection_plan(schedule)
    active_rows = [
        selection for selection in plan.selections if selection.substep_id == "s0000"
    ]
    assert len(active_rows) == 1
    assert active_rows[0].row_kind == "two_qubit_control_zz_cluster_joint_channel"
    assert active_rows[0].participant == (0, 1, 2, 3)
    assert active_rows[0].coupling_edges == ((1, 2),)

    channel = axis1_substep_channel_evidence_manifest(schedule)
    assert channel["passed"] is True
    assert channel["coverage"]["full_positive_duration_coverage"] is True
    row = channel["rows"][0]
    assert row["row_kind"] == "two_qubit_control_zz_cluster_joint_channel"
    assert row["participant"] == [0, 1, 2, 3]
    assert row["coupling_edges"] == [[1, 2]]
    assert row["joint_channel"]["assembly_semantics"] == "single_joint_generator_expm"
    assert row["joint_channel"]["dimension"] == 16
    assert [control["name"] for control in row["ideal_controls"]] == ["CTRL_CZ", "CTRL_CZ"]
    assert [control["support"] for control in row["ideal_controls"]] == [[0, 1], [2, 3]]

    state = axis1_state_evolution_evidence_manifest(schedule)
    assert state["state_evolution"]["applied_channel_count"] == 1
    assert state["state_evolution"]["applied_layers"][0]["window_count"] == 1
    record = axis1_measurement_record_evidence_manifest(schedule)
    assert record["record_evidence"]["applied_channel_count"] == 1
    assert record["record_evidence"]["applied_layers"][0]["window_count"] == 1


def test_axis1_measurement_record_evidence_branches_z_records_without_b8_or_decoder(tmp_path):
    builder = CircuitBuilder(num_qubits=2)
    builder.h(0)
    builder.tick()
    builder.cz((0, 1))
    builder.tick()
    builder.measure((0, 1), key=("m0", "m1"))
    builder.detector("d0", xor=("m0", "m1"))
    builder.observable("logical0", xor=("m1",), index=0)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_measurement_record_evidence_manifest(schedule)

    assert manifest["schema"] == "error_coupling_simulator.frontend.measurement_record_evidence.v1"
    assert manifest["representability"] == "axis1_selected_joint_channel_record_evidence_no_b8_or_decoder"
    assert manifest["source_hash"] == schedule.source_hash
    assert manifest["selection_plan"]["selector_id"] == "axis1_schedule_joint_channel_selector_v1"
    assert manifest["coverage"]["selected_substep_ids"] == ["s0000", "s0002"]

    evidence = manifest["record_evidence"]
    assert evidence["initial_state"] == "computational_zero_density_matrix"
    assert evidence["applied_channel_count"] == 2
    assert evidence["measurement_basis"] == "Z"
    assert evidence["measurement_keys"] == ["m0", "m1"]
    assert evidence["record_count"] == 4
    assert evidence["total_probability_residual"] <= 1e-8
    assert abs(sum(evidence["record_probabilities"]) - 1.0) <= 1e-12
    assert evidence["measurement_records"] == [[0, 0], [1, 0], [0, 1], [1, 1]]
    assert evidence["detector_records_emitted"] is True
    assert evidence["logical_observables_emitted"] is True
    assert evidence["detector_names"] == ["d0"]
    assert evidence["logical_observable_names"] == ["logical0"]
    assert evidence["detector_records"] == [[0], [1], [1], [0]]
    assert evidence["logical_observable_records"] == [[0], [0], [1], [1]]
    assert evidence["claims_b8_artifact"] is False
    assert evidence["claims_decoder_integration"] is False
    assert evidence["record_layout_ref"]["detector_names"] == ["d0"]
    assert evidence["record_layout_ref"]["observable_names"] == ["logical0"]
    assert evidence["record_layout_ref"]["detectors"] == [
        {"name": "d0", "keys": ["m0", "m1"], "coords": []}
    ]
    assert evidence["record_layout_ref"]["observables"] == [
        {"name": "logical0", "keys": ["m1"], "index": 0}
    ]

    payload = json.dumps(manifest, sort_keys=True).lower()
    for forbidden in ("kraus_stack", "choi_matrix", "superoperator_matrix", "source_timeline"):
        assert forbidden not in payload

    result = write_axis1_measurement_record_evidence(schedule, tmp_path / "records")
    assert result.record_evidence.name == "axis1_measurement_records.json"
    assert sorted(path.name for path in result.out_dir.iterdir()) == [
        "axis1_measurement_records.json"
    ]
    assert result.manifest["content_hash"] == manifest["content_hash"]

    freeze = freeze_axis1_measurement_record_evidence(result.record_evidence)
    assert freeze.freeze_path.name == "axis1_measurement_records.freeze.json"
    validation = validate_axis1_measurement_record_freeze(freeze.freeze_path)
    assert validation["pass"] is True
    assert validation["evidence_content_hash"] == result.content_hash

    tampered = json.loads(result.record_evidence.read_text())
    tampered["verdict"] = "fail"
    result.record_evidence.write_text(json.dumps(tampered, indent=2, sort_keys=True) + "\n")
    with pytest.raises(ValueError, match="sha256 mismatch"):
        validate_axis1_measurement_record_freeze(freeze.freeze_path)


def test_axis1_codespec_record_runner_writes_freeze_and_detects_drift(tmp_path):
    result = run_axis1_codespec_record_fixture(tmp_path / "codespec")

    assert result.schedule.source_kind == "code_spec_compiler"
    assert result.evidence.record_evidence.name == "axis1_measurement_records.json"
    assert result.freeze is not None
    assert result.freeze.freeze_path.name == "axis1_measurement_records.freeze.json"
    assert sorted(path.name for path in result.evidence.out_dir.iterdir()) == [
        "axis1_measurement_records.freeze.json",
        "axis1_measurement_records.json",
    ]

    manifest = json.loads(result.evidence.record_evidence.read_text())
    record = manifest["record_evidence"]
    assert manifest["source_kind"] == "code_spec_compiler"
    assert manifest["coverage"]["full_positive_duration_coverage"] is True
    assert manifest["coverage"]["partial_positive_duration_substeps"] == []
    assert record["measurement_basis"] == "mixed_pauli"
    assert record["record_count"] == 128
    assert record["applied_channel_count"] == 8
    assert record["detector_records_emitted"] is True
    assert record["logical_observables_emitted"] is True

    validation = validate_axis1_measurement_record_freeze(result.freeze.freeze_path)
    assert validation["pass"] is True
    assert validation["evidence_content_hash"] == result.evidence.content_hash

    freeze_manifest = json.loads(result.freeze.freeze_path.read_text())
    freeze_manifest["evidence_sha256"] = "0" * 64
    result.freeze.freeze_path.write_text(
        json.dumps(freeze_manifest, indent=2, sort_keys=True) + "\n"
    )
    with pytest.raises(ValueError, match="sha256 mismatch"):
        freeze_axis1_measurement_record_evidence(result.evidence.record_evidence)


def test_axis1_record_evidence_supports_x_basis_measurement_by_exact_rotation():
    builder = CircuitBuilder(num_qubits=2)
    builder.h(0)
    builder.measure(0, key="mx", basis="X")
    builder.measure(1, key="mz")
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_measurement_record_evidence_manifest(schedule)
    evidence = manifest["record_evidence"]
    assert evidence["measurement_basis"] == "mixed_pauli"
    assert evidence["measurement_bases"] == ["X", "Z"]
    assert evidence["measurement_keys"] == ["mx", "mz"]
    assert evidence["applied_steps"][0]["ideal_controls"][0]["name"] == "CTRL_H"

    p_mx_one = sum(
        probability
        for record, probability in zip(
            evidence["measurement_records"],
            evidence["record_probabilities"],
            strict=True,
        )
        if record[0] == 1
    )
    assert p_mx_one <= 0.1


def test_axis1_record_evidence_lowers_h_frontend_gate_inside_joint_generator():
    builder = CircuitBuilder(num_qubits=2)
    builder.h(0)
    builder.measure((0, 1), key=("m0", "m1"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_measurement_record_evidence_manifest(schedule)
    evidence = manifest["record_evidence"]
    assert evidence["applied_channel_count"] == 1
    step = evidence["applied_steps"][0]
    assert step["row_kind"] == "one_qubit_drive_joint_channel"
    assert step["primitive_names"] == ["T2", "T1", "T2_B", "T1_B"]
    assert step["ideal_controls"][0]["name"] == "CTRL_H"
    assert step["ideal_controls"][0]["epistemic_class"] == "a"
    assert step["channel_assembly"]["assembly_semantics"] == "single_joint_generator_expm"
    assert step["channel_assembly"]["contains_ideal_control_hamiltonian"] is True
    assert step["channel_assembly"]["ideal_control_names"] == ["CTRL_H"]

    p_m0_one = sum(
        probability
        for record, probability in zip(
            evidence["measurement_records"],
            evidence["record_probabilities"],
            strict=True,
        )
        if record[0] == 1
    )
    assert 0.45 <= p_m0_one <= 0.55


def test_axis1_record_evidence_lowers_ordered_cx_frontend_control():
    builder = CircuitBuilder(num_qubits=2)
    builder.x(0)
    builder.tick()
    builder.cx((0, 1))
    builder.tick()
    builder.measure((0, 1), key=("m0", "m1"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    plan = build_axis1_schedule_selection_plan(schedule)
    assert [selection.row_kind for selection in plan.selections] == [
        "one_qubit_drive_joint_channel",
        "two_qubit_control_joint_channel",
    ]
    assert plan.selections[1].participant == (0, 1)
    assert plan.selections[1].primitive_names == ("T2", "T1", "T2_B", "T1_B")

    manifest = axis1_measurement_record_evidence_manifest(schedule)
    evidence = manifest["record_evidence"]
    assert [step["row_kind"] for step in evidence["applied_steps"]] == [
        "one_qubit_drive_joint_channel",
        "two_qubit_control_joint_channel",
    ]
    assert [step["ideal_controls"][0]["name"] for step in evidence["applied_steps"]] == [
        "CTRL_X",
        "CTRL_CX",
    ]
    assert evidence["applied_steps"][1]["mechanism_pair"] == ["CTRL_CX", "T2_T1"]
    assert evidence["applied_steps"][1]["channel_assembly"]["assembly_semantics"] == (
        "single_joint_generator_expm"
    )

    p_11 = sum(
        probability
        for record, probability in zip(
            evidence["measurement_records"],
            evidence["record_probabilities"],
            strict=True,
        )
        if record == [1, 1]
    )
    assert p_11 >= 0.95


def test_axis1_record_sample_writer_writes_b8_without_dem_or_decoder(tmp_path):
    builder = CircuitBuilder(num_qubits=2)
    builder.h(0)
    builder.tick()
    builder.cz((0, 1))
    builder.tick()
    builder.measure((0, 1), key=("m0", "m1"))
    builder.detector("d0", xor=("m0", "m1"))
    builder.observable("logical0", xor=("m1",), index=0)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    result = write_axis1_measurement_record_samples(
        schedule,
        tmp_path / "axis1_samples",
        shots=64,
        seed=123,
    )

    assert sorted(path.name for path in result.out_dir.iterdir()) == [
        "axis1_measurement_records.json",
        "axis1_sample_summary.json",
        "detection_events.b8",
        "obs_flips_actual.b8",
    ]
    assert not (result.out_dir / "detector_error_model.dem").exists()
    assert not (result.out_dir / "decoder_results.json").exists()
    assert result.detection_events is not None
    assert result.obs_flips_actual is not None

    det = b8_io.unpack_bits(b8_io.read_b8(result.detection_events, 1), 1)
    obs = b8_io.unpack_bits(b8_io.read_b8(result.obs_flips_actual, 1), 1)
    assert det.shape == (64, 1)
    assert obs.shape == (64, 1)

    summary = json.loads(result.sample_summary.read_text())
    assert summary["schema"] == "error_coupling_simulator.frontend.record_sample_summary.v1"
    assert summary["representability"] == "axis1_jointL_record_samples_b8_no_dem_no_decoder"
    assert summary["shots"] == 64
    assert summary["seed"] == 123
    assert summary["claims_dem_artifact"] is False
    assert summary["claims_decoder_integration"] is False
    assert summary["claims_stim_pauli_model"] is False
    assert summary["artifacts"]["detector_error_model"] is None
    assert summary["artifacts"]["decoder_results"] is None
    assert summary["artifacts"]["detection_events"]["file"] == "detection_events.b8"
    assert summary["artifacts"]["obs_flips_actual"]["file"] == "obs_flips_actual.b8"
    assert summary["exact_evidence_content_hash"] == result.exact_manifest["content_hash"]


def test_joint_channel_evidence_writer_refuses_stale_simulator_artifact_dir(tmp_path):
    out_dir = tmp_path / "dirty"
    out_dir.mkdir()
    (out_dir / "detector_error_model.DEM").write_text("stale\n")

    with pytest.raises(ValueError, match="simulator-run artifact directories"):
        write_joint_channel_comparison_evidence(_joint_channel_schedule(), out_dir)

    out_dir = tmp_path / "dirty_qutrit"
    out_dir.mkdir()
    (out_dir / "measurement_counts.json").write_text("{}\n")

    with pytest.raises(ValueError, match="simulator-run artifact directories"):
        write_joint_channel_comparison_evidence(_joint_channel_schedule(), out_dir)


def test_axis1_evidence_writers_refuse_forbidden_or_nonlocal_filenames(tmp_path):
    schedule = _joint_channel_schedule()

    with pytest.raises(ValueError, match="forbidden evidence filename"):
        write_joint_channel_comparison_evidence(
            schedule,
            tmp_path / "comparison_forbidden",
            filename="circuit.STIM",
        )
    with pytest.raises(ValueError, match="non-local evidence filename"):
        write_joint_channel_comparison_evidence(
            schedule,
            tmp_path / "comparison_nonlocal",
            filename="../joint_channel_comparison.json",
        )
    with pytest.raises(ValueError, match="forbidden evidence filename"):
        write_axis1_substep_channel_evidence(
            schedule,
            tmp_path / "channel_forbidden",
            filename="detector_error_model.DEM",
        )
    with pytest.raises(ValueError, match="forbidden evidence filename"):
        write_axis1_state_evolution_evidence(
            schedule,
            tmp_path / "state_forbidden",
            filename="STATEVECTOR.JSON",
        )
    with pytest.raises(ValueError, match="forbidden evidence filename"):
        write_axis1_measurement_record_evidence(
            schedule,
            tmp_path / "record_forbidden",
            filename="detection_events.B8",
        )


def test_axis1_record_sampler_refuses_stale_simulator_state_artifact_dir(tmp_path):
    out_dir = tmp_path / "dirty_sample"
    out_dir.mkdir()
    (out_dir / "STATEVECTOR.JSON").write_text("{}\n")

    with pytest.raises(ValueError, match="mixed simulator/decoder artifact directories"):
        write_axis1_measurement_record_samples(
            _joint_channel_schedule(),
            out_dir,
            shots=4,
        )


def test_joint_channel_runner_writes_evidence_freeze_and_detects_drift(tmp_path):
    schedule = build_joint_channel_comparison_schedule()
    assert schedule.source_kind == "circuit_ir"
    assert len(schedule.source_hash) == 64

    result = run_joint_channel_comparison_fixture(tmp_path / "runner")
    assert result.freeze is not None
    assert result.evidence.joint_channel_comparison.name == "joint_channel_comparison.json"
    assert result.freeze.freeze_path.name == "joint_channel_comparison.freeze.json"
    assert sorted(path.name for path in result.evidence.out_dir.iterdir()) == [
        "joint_channel_comparison.freeze.json",
        "joint_channel_comparison.json",
    ]

    validation = validate_joint_channel_comparison_freeze(result.freeze.freeze_path)
    assert validation["pass"] is True
    assert validation["evidence_content_hash"] == result.evidence.content_hash

    freeze_manifest = json.loads(result.freeze.freeze_path.read_text())
    freeze_manifest["evidence_sha256"] = "0" * 64
    result.freeze.freeze_path.write_text(
        json.dumps(freeze_manifest, indent=2, sort_keys=True) + "\n"
    )
    with pytest.raises(ValueError, match="sha256 mismatch"):
        freeze_joint_channel_comparison_evidence(result.evidence.joint_channel_comparison)

    result = run_joint_channel_comparison_fixture(
        tmp_path / "runner",
        refresh_freeze=True,
    )
    manifest = json.loads(result.evidence.joint_channel_comparison.read_text())
    manifest["verdict"] = "fail"
    result.evidence.joint_channel_comparison.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    with pytest.raises(ValueError, match="sha256 mismatch"):
        validate_joint_channel_comparison_freeze(result.freeze.freeze_path)
    with pytest.raises(ValueError, match="mismatch"):
        freeze_joint_channel_comparison_evidence(result.evidence.joint_channel_comparison)


def test_axis1_evidence_runners_return_nonzero_on_failed_verdict(monkeypatch, tmp_path):
    import error_coupling_simulator.frontend.axis1_codespec_runner as codespec_runner_module
    import error_coupling_simulator.frontend.joint_channel_comparison_runner as comparison_runner_module

    comparison_evidence = SimpleNamespace(
        out_dir=tmp_path / "comparison",
        joint_channel_comparison=(
            tmp_path / "comparison" / "joint_channel_comparison.json"
        ),
        content_hash="0" * 64,
        manifest={"verdict": "fail", "passed": False, "rows": []},
    )
    monkeypatch.setattr(
        comparison_runner_module,
        "run_joint_channel_comparison_fixture",
        lambda *args, **kwargs: SimpleNamespace(
            evidence=comparison_evidence,
            freeze=None,
        ),
    )
    assert comparison_runner_module.main(
        ["--out-dir", str(tmp_path / "comparison"), "--no-freeze"]
    ) == 1

    record_manifest = {
        "verdict": "fail",
        "passed": False,
        "source_kind": "code_spec_compiler",
        "source_hash": "1" * 64,
        "coverage": {"full_positive_duration_coverage": False},
        "record_evidence": {
            "record_count": 0,
            "measurement_keys": [],
            "applied_channel_count": 0,
            "measurement_basis": "none",
        },
    }
    record_evidence = SimpleNamespace(
        out_dir=tmp_path / "record",
        record_evidence=tmp_path / "record" / "axis1_measurement_records.json",
        content_hash="1" * 64,
        manifest=record_manifest,
    )
    monkeypatch.setattr(
        codespec_runner_module,
        "run_axis1_codespec_record_fixture",
        lambda *args, **kwargs: SimpleNamespace(
            evidence=record_evidence,
            freeze=None,
        ),
    )
    assert codespec_runner_module.main(["--out-dir", str(tmp_path / "record"), "--no-freeze"]) == 1


def _assert_control_channel_matches_unitary(selection, expected_unitary):
    dt = float(selection.dt_ns_nominal)
    controls = lower_ideal_controls_for_selection(selection, dt_ns=dt, device="cuda")
    assert [record.name for record in controls.records] == [
        f"CTRL_{selection.operation_names[0]}"
    ]
    kraus = assemble_substep_channel(controls.H_list, (), dt, device="cuda")
    assert int(kraus.shape[-1]) == int(expected_unitary.shape[-1])
    _assert_kraus_channel_matches_unitary(kraus, expected_unitary)


def _assert_kraus_channel_matches_unitary(kraus, expected_unitary):
    dim = int(expected_unitary.shape[-1])
    max_residual = 0.0
    for i in range(dim):
        for j in range(dim):
            rho = torch.zeros((dim, dim), dtype=torch.complex128, device="cuda")
            rho[i, j] = 1.0
            actual = sum(K @ rho @ K.conj().transpose(-1, -2) for K in kraus)
            expected = expected_unitary @ rho @ expected_unitary.conj().transpose(-1, -2)
            residual = float(torch.max(torch.abs(actual - expected)).item())
            max_residual = max(max_residual, residual)
    assert max_residual <= 5.0e-8


def _joint_channel_schedule():
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_static_zz_couplings(((0, 1),))
    builder.h(0)
    builder.tick()
    builder.cz((0, 1))
    return circuit_ir_to_substep_schedule(builder.build())


def _two_qubit_dt_ns() -> float:
    builder = CircuitBuilder(num_qubits=2)
    builder.cz((0, 1))
    schedule = circuit_ir_to_substep_schedule(builder.build())
    for substep in schedule.substeps:
        if substep.kind == "two_qubit_gate":
            assert substep.dt_ns_nominal is not None
            return float(substep.dt_ns_nominal)
    raise AssertionError("probe schedule did not produce a two-qubit substep")


def _unsealed_schedule_clone(schedule: SubstepSchedule) -> SubstepSchedule:
    return SubstepSchedule(
        source_kind=schedule.source_kind,
        source_hash=schedule.source_hash,
        schedule_template=schedule.schedule_template,
        num_qubits=schedule.num_qubits,
        substeps=schedule.substeps,
        duration_policy=schedule.duration_policy,
        qubit_roles=schedule.qubit_roles,
        qubit_coords=schedule.qubit_coords,
        record_layout_ref=schedule.record_layout_ref,
        static_zz_couplings=schedule.static_zz_couplings,
        static_zz_calibrations=schedule.static_zz_calibrations,
    )


def _make_mixed_frontend_spec(
    *,
    rounds: int,
    metadata: dict | None = None,
) -> CodeSpec:
    spec_metadata = {"family": "axis1_schedule_test", "encoded_distance_certified": False}
    spec_metadata.update(dict(metadata or {}))
    return CodeSpec(
        name="axis1_schedule_mixed_frontend",
        num_qubits=5,
        data_qubits=(
            CodeQubit(0, "data", (0.0,)),
            CodeQubit(1, "data", (1.0,)),
            CodeQubit(2, "data", (2.0,)),
        ),
        ancilla_qubits=(
            CodeQubit(3, "ancilla", (0.0, 0.5)),
            CodeQubit(4, "ancilla", (1.0, 0.5)),
        ),
        checks=(
            StabilizerCheck("x0", 3, (PauliTerm(0, "X"),), (0.0, 0.5)),
            StabilizerCheck("z1", 4, (PauliTerm(1, "Z"),), (1.0, 0.5)),
        ),
        logical_observables=(
            LogicalObservableSpec("logical_z2", (PauliTerm(2, "Z"),), index=0),
        ),
        rounds=rounds,
        metadata=spec_metadata,
    )
