"""MCWF finite-step X/Z Record-law convergence on the frozen QuTiP fixture.

This file deliberately makes no linear-channel, Choi, CPTP, or global
convergence-order claim.  The deterministic reference is the standard-library
scalar recurrence owned by the neutral QuTiP protocol for this one frozen T1
fixture.  The public GPU test compares sampled Records with that finite-step
law; the continuous-time law comes from the same neutral protocol.
"""

from __future__ import annotations

import importlib.util
import math
from pathlib import Path
from typing import Any

import pytest
import torch

from error_coupling_simulator.frontend import (
    Axis1LocalLindbladContextSpec,
    CircuitBuilder,
    axis1_mcwf_mps_state_record_execution_manifest,
    circuit_ir_to_substep_schedule,
)
from error_coupling_simulator.numerics import NUMERICAL_ZERO


REPO = Path(__file__).resolve().parents[1]
PROTOCOL = REPO / "scripts" / "external_baselines" / "qutip_mcwf_xz_protocol.py"
FIXTURE = (
    REPO
    / "scripts"
    / "external_baselines"
    / "fixtures"
    / "qutip_mcwf_xz_two_qubit_t1.json"
)
MICROSTEP_COUNTS = (10, 20, 40, 80)
EXPECTED_FIXTURE_TV = {
    10: (0.023409825026091874, 0.010275861041313533),
    20: (0.011859662816100847, 0.005088283414417721),
    40: (0.005967971464909766, 0.002531793804892407),
    80: (0.0029934385472444314, 0.0012628170724109378),
}
RATIO_BAND = (1.85, 2.15)
FINAL_JOINT_Z_TV_CAP = 0.0031
FINAL_X_TV_CAP = 0.0013
EXPECTED_JOINT_RADIUS = 0.0640322086265546
EXPECTED_MARGINAL_RADIUS = 0.039518987893233104


def _load_protocol():
    spec = importlib.util.spec_from_file_location(
        "qutip_mcwf_xz_protocol_for_convergence",
        PROTOCOL,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_protocol_owns_the_frozen_finite_step_recurrence():
    protocol = _load_protocol()
    fixture = protocol.load_fixture(FIXTURE)

    law = protocol.finite_step_binary_distribution(fixture, microstep_count=40)
    joint, z_before, x_after = _fixture_tvs(protocol, fixture, law)

    assert math.fsum(law.values()) == pytest.approx(1.0, abs=NUMERICAL_ZERO)
    assert all(row[3] == 0 for row in law)
    assert joint == pytest.approx(EXPECTED_FIXTURE_TV[40][0], abs=NUMERICAL_ZERO)
    assert z_before == pytest.approx(EXPECTED_FIXTURE_TV[40][0], abs=NUMERICAL_ZERO)
    assert x_after == pytest.approx(EXPECTED_FIXTURE_TV[40][1], abs=NUMERICAL_ZERO)


def test_protocol_builds_verdict_driving_convergence_and_corruption_evidence():
    protocol = _load_protocol()
    fixture = protocol.load_fixture(FIXTURE)

    packet = protocol.finite_step_convergence_evidence(fixture)

    assert packet["schema"] == (
        "ai_qec.external_baseline.mcwf_xz_finite_step_convergence.v1"
    )
    assert packet["microstep_counts"] == [10, 20, 40, 80]
    assert packet["ratio_band"] == [1.85, 2.15]
    for row in packet["grid"]:
        count = row["microstep_count"]
        expected_joint_z, expected_x = EXPECTED_FIXTURE_TV[count]
        assert row["observed_tv"] == pytest.approx(
            {
                "joint": expected_joint_z,
                "z_before": expected_joint_z,
                "x_after": expected_x,
            },
            abs=NUMERICAL_ZERO,
        )
        assert row["observed_tv"] == pytest.approx(
            row["expected_tv"], abs=NUMERICAL_ZERO
        )
        assert row["expected_match"] is True
        assert row["post_z_structural_zero"] is True
    assert all(check["passed"] for check in packet["ratio_checks"])
    assert packet["final_grid_gate"]["caps"] == {
        "joint": FINAL_JOINT_Z_TV_CAP,
        "z_before": FINAL_JOINT_Z_TV_CAP,
        "x_after": FINAL_X_TV_CAP,
    }
    assert packet["final_grid_gate"]["passed"] is True
    sample_gate = packet["public_m40_sample_gate_policy"]
    assert sample_gate["sample_count"] == 2048
    assert sample_gate["joint_tv_radius"] == pytest.approx(
        EXPECTED_JOINT_RADIUS, abs=NUMERICAL_ZERO
    )
    assert sample_gate["marginal_tv_radius"] == pytest.approx(
        EXPECTED_MARGINAL_RADIUS, abs=NUMERICAL_ZERO
    )
    assert sample_gate["passed"] is True
    controls = packet["corruption_controls"]
    assert controls["nojump_half_to_one"]["observed_tv_vs_correct_m40"] == (
        pytest.approx(
            {"joint": 0.08111612211053276, "x_after": 0.08111612211053276},
            abs=NUMERICAL_ZERO,
        )
    )
    assert controls["nojump_half_to_one"]["m80_tv_vs_continuous"] == (
        pytest.approx(0.08106347555070871, abs=NUMERICAL_ZERO)
    )
    assert controls["nojump_half_to_one"]["detected"] is True
    assert controls["wrong_dt"]["observed_tv_vs_correct_m40"] == pytest.approx(
        {
            "joint": 0.30909405210692065,
            "z_before": 0.24403202853509015,
            "x_after": 0.24746820619510762,
        },
        abs=NUMERICAL_ZERO,
    )
    assert controls["wrong_dt"]["detected"] is True
    assert packet["all_checks_passed"] is True
    assert packet["content_hash"] == protocol.canonical_content_hash(packet)


def test_protocol_public_m40_sample_gate_is_observed_and_fail_closed():
    protocol = _load_protocol()
    fixture = protocol.load_fixture(FIXTURE)
    finite_step = protocol.finite_step_binary_distribution(fixture, 40)

    healthy = protocol.finite_step_public_sample_evidence(fixture, finite_step)
    corrupted = protocol.finite_step_public_sample_evidence(
        fixture,
        protocol.flip_binary_column(finite_step, column=3),
    )

    assert healthy["schema"] == (
        "ai_qec.external_baseline.mcwf_xz_public_m40_sample_gate.v1"
    )
    assert healthy["observed_tv"] == {"joint": 0.0, "z_before": 0.0, "x_after": 0.0}
    assert healthy["joint_tv_radius"] == pytest.approx(
        EXPECTED_JOINT_RADIUS, abs=NUMERICAL_ZERO
    )
    assert healthy["marginal_tv_radius"] == pytest.approx(
        EXPECTED_MARGINAL_RADIUS, abs=NUMERICAL_ZERO
    )
    assert healthy["post_z_structural_zero"] is True
    assert healthy["passed"] is True
    assert healthy["content_hash"] == protocol.canonical_content_hash(healthy)
    assert corrupted["observed_tv"]["joint"] == 1.0
    assert corrupted["post_z_structural_zero"] is False
    assert corrupted["passed"] is False


def _fixture_tvs(protocol, fixture, finite_step_law):
    continuous_law = protocol.analytic_binary_distribution(fixture)
    joint = protocol.total_variation(finite_step_law, continuous_law)
    z_before = protocol.total_variation(
        protocol.binary_column_marginal(finite_step_law, column=1),
        protocol.binary_column_marginal(continuous_law, column=1),
    )
    x_after = protocol.total_variation(
        protocol.binary_column_marginal(finite_step_law, column=2),
        protocol.binary_column_marginal(continuous_law, column=2),
    )
    return joint, z_before, x_after


def _schedule_from_fixture(fixture: dict[str, Any]):
    builder = CircuitBuilder(num_qubits=int(fixture["num_qubits"]))
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=float(fixture["gamma_phi_per_ns"]),
            gamma_1_per_ns=float(fixture["gamma_1_per_ns"]),
            gamma_readout_phi_per_ns=0.0,
        )
    )
    duration = float(fixture["evolution_duration_ns"])
    builder.idle((0, 1), duration_ns=duration)
    builder.tick()
    builder.measure(0, key="mx_before", basis="X", reset=True)
    builder.measure(1, key="mz_before", basis="Z", reset=True)
    builder.tick()
    builder.idle((0, 1), duration_ns=duration)
    builder.tick()
    builder.measure(0, key="mx_after", basis="X", reset=False)
    builder.measure(1, key="mz_after", basis="Z", reset=False)
    return circuit_ir_to_substep_schedule(builder.build())


def _empirical_law(execution: dict[str, Any]):
    return {
        tuple(int(value) for value in row): float(probability)
        for row, probability in zip(
            execution["measurement_records"],
            execution["record_probabilities"],
            strict=True,
        )
    }


def test_frozen_fixture_record_tv_bias_approximately_halves_on_this_grid():
    protocol = _load_protocol()
    fixture = protocol.load_fixture(FIXTURE)
    observed: dict[int, tuple[float, float, float]] = {}

    for microstep_count in MICROSTEP_COUNTS:
        law = protocol.finite_step_binary_distribution(fixture, microstep_count)
        assert all(row[3] == 0 for row in law)
        joint, z_before, x_after = _fixture_tvs(protocol, fixture, law)
        observed[microstep_count] = (joint, z_before, x_after)
        expected_joint_z, expected_x = EXPECTED_FIXTURE_TV[microstep_count]
        assert joint == pytest.approx(expected_joint_z, abs=NUMERICAL_ZERO)
        assert z_before == pytest.approx(expected_joint_z, abs=NUMERICAL_ZERO)
        assert x_after == pytest.approx(expected_x, abs=NUMERICAL_ZERO)

    joint_values = [observed[m][0] for m in MICROSTEP_COUNTS]
    z_values = [observed[m][1] for m in MICROSTEP_COUNTS]
    x_values = [observed[m][2] for m in MICROSTEP_COUNTS]
    for values in (joint_values, z_values, x_values):
        assert all(current < previous for previous, current in zip(values, values[1:]))
        ratios = [
            previous / current
            for previous, current in zip(values, values[1:])
        ]
        assert all(RATIO_BAND[0] <= ratio <= RATIO_BAND[1] for ratio in ratios)

    assert joint_values[-1] <= FINAL_JOINT_Z_TV_CAP
    assert z_values[-1] <= FINAL_JOINT_Z_TV_CAP
    assert x_values[-1] <= FINAL_X_TV_CAP


def test_corrupted_scalar_recurrences_have_power_on_the_frozen_fixture():
    """Power checks only; the semantic mutation service must kill source mutants."""

    protocol = _load_protocol()
    fixture = protocol.load_fixture(FIXTURE)
    continuous = protocol.analytic_binary_distribution(fixture)

    correct_40 = protocol.finite_step_binary_distribution(fixture, 40)
    doubled_no_jump_40 = protocol.finite_step_binary_distribution(
        fixture,
        40,
        no_jump_linear_factor=1.0,
    )
    joint_half_mutation = protocol.total_variation(
        doubled_no_jump_40,
        correct_40,
    )
    x_half_mutation = protocol.total_variation(
        protocol.binary_column_marginal(doubled_no_jump_40, column=2),
        protocol.binary_column_marginal(correct_40, column=2),
    )
    assert joint_half_mutation == pytest.approx(
        0.08111612211053276,
        abs=NUMERICAL_ZERO,
    )
    assert x_half_mutation == pytest.approx(
        0.08111612211053276,
        abs=NUMERICAL_ZERO,
    )
    assert joint_half_mutation > EXPECTED_JOINT_RADIUS
    assert x_half_mutation > EXPECTED_MARGINAL_RADIUS

    doubled_no_jump_80 = protocol.finite_step_binary_distribution(
        fixture,
        80,
        no_jump_linear_factor=1.0,
    )
    assert protocol.total_variation(
        doubled_no_jump_80,
        continuous,
    ) == pytest.approx(0.08106347555070871, abs=NUMERICAL_ZERO)

    wrong_dt = protocol.finite_step_binary_distribution(
        fixture,
        40,
        divide_duration_by_microsteps=False,
    )
    wrong_dt_joint = protocol.total_variation(wrong_dt, correct_40)
    wrong_dt_z = protocol.total_variation(
        protocol.binary_column_marginal(wrong_dt, column=1),
        protocol.binary_column_marginal(correct_40, column=1),
    )
    wrong_dt_x = protocol.total_variation(
        protocol.binary_column_marginal(wrong_dt, column=2),
        protocol.binary_column_marginal(correct_40, column=2),
    )
    assert wrong_dt_joint == pytest.approx(
        0.30909405210692065,
        abs=NUMERICAL_ZERO,
    )
    assert wrong_dt_z == pytest.approx(
        0.24403202853509015,
        abs=NUMERICAL_ZERO,
    )
    assert wrong_dt_x == pytest.approx(
        0.24746820619510762,
        abs=NUMERICAL_ZERO,
    )


def test_public_gpu_xz_records_match_the_finite_step_fixture_law():
    if not torch.cuda.is_available():
        pytest.fail(
            "MCWF X/Z Record convergence is GPU-gated; CUDA-MISSING is not a release basis",
            pytrace=False,
        )

    protocol = _load_protocol()
    fixture = protocol.load_fixture(FIXTURE)
    microstep_count = int(fixture["microstep_count"])
    trajectory_count = int(fixture["trajectory_count"])
    manifest = axis1_mcwf_mps_state_record_execution_manifest(
        _schedule_from_fixture(fixture),
        device="cuda",
        local_dims=fixture["local_dims"],
        initial_levels=fixture["initial_levels"],
        microstep_count=microstep_count,
        finite_step_order="first_order",
        trajectory_count=trajectory_count,
        rng_seed=int(fixture["project_rng_seed"]),
        mass_residual_budget=0.1,
    )

    assert manifest["execution_status"] == "completed"
    assert manifest["claims_dense_channel_evidence"] is False
    execution = manifest["mps_execution"]
    assert execution["measurement_keys"] == fixture["measurement_keys"]
    assert execution["measurement_targets"] == fixture["measurement_targets"]
    assert execution["measurement_bases"] == fixture["measurement_bases"]
    assert execution["reset_after"] == fixture["reset_after"]
    assert execution["finite_step_policy"]["order"] == "first_order"
    assert all(row[3] == 0 for row in execution["measurement_records"])
    assert sum(execution["record_counts"]) == trajectory_count
    assert math.fsum(execution["record_probabilities"]) == pytest.approx(
        1.0,
        abs=NUMERICAL_ZERO,
    )
    for count, probability in zip(
        execution["record_counts"],
        execution["record_probabilities"],
        strict=True,
    ):
        assert probability == pytest.approx(
            count / trajectory_count,
            abs=NUMERICAL_ZERO,
        )

    empirical = _empirical_law(execution)
    finite_step = protocol.finite_step_binary_distribution(fixture, microstep_count)
    alpha_each = float(fixture["comparison_alpha"]) / 3.0
    joint_radius = protocol.multinomial_tv_radius(
        sample_count=trajectory_count,
        alphabet_size=16,
        alpha=alpha_each,
    )
    marginal_radius = protocol.multinomial_tv_radius(
        sample_count=trajectory_count,
        alphabet_size=2,
        alpha=alpha_each,
    )
    assert joint_radius == pytest.approx(EXPECTED_JOINT_RADIUS, abs=NUMERICAL_ZERO)
    assert marginal_radius == pytest.approx(
        EXPECTED_MARGINAL_RADIUS,
        abs=NUMERICAL_ZERO,
    )

    joint_tv = protocol.total_variation(empirical, finite_step)
    z_tv = protocol.total_variation(
        protocol.binary_column_marginal(empirical, column=1),
        protocol.binary_column_marginal(finite_step, column=1),
    )
    x_tv = protocol.total_variation(
        protocol.binary_column_marginal(empirical, column=2),
        protocol.binary_column_marginal(finite_step, column=2),
    )
    assert joint_tv <= joint_radius
    assert z_tv <= marginal_radius
    assert x_tv <= marginal_radius
