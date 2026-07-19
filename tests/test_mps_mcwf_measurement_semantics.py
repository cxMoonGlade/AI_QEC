from __future__ import annotations

"""MCWF/MPS measurement-state and sampled-support regression tests."""

import math
import sys
from types import ModuleType

import numpy as np
import pytest


@pytest.mark.parametrize("seed", [0, 1])
def test_x_measurement_returns_the_conditioned_state_in_the_original_frame(
    seed: int,
) -> None:
    """X readout labels an X eigenstate; later evolution must see that state."""

    import quimb.tensor as qtn
    import torch

    import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as mcwf

    state = qtn.MPS_product_state((np.array([1.0, 0.0], dtype=np.complex128),))
    state.apply_to_arrays(
        lambda value: torch.as_tensor(value, dtype=torch.complex128, device="cpu")
    )
    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed)

    levels, bits, conditioned = mcwf._sample_measurement_multilevel(
        state,
        targets=(0,),
        bases=("X",),
        local_dims=(2,),
        device="cpu",
        generator=generator,
        leaked_readout_b=0.5,
    )

    assert bits == levels
    assert levels[0] in (0, 1)
    sign = 1.0 if levels[0] == 0 else -1.0
    expected = np.array([1.0, sign], dtype=np.complex128) / math.sqrt(2.0)
    observed = conditioned.to_dense().detach().cpu().numpy().reshape(-1)
    np.testing.assert_allclose(observed, expected, rtol=0.0, atol=1.0e-14)


def test_dense_level_oracle_keeps_x_then_z_outcomes_independent() -> None:
    from error_coupling_simulator.certify.axis1_mps import (
        _dense_jointL_level_distribution,
    )
    from error_coupling_simulator.frontend import (
        CircuitBuilder,
        circuit_ir_to_substep_schedule,
    )

    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key="mx", basis="X")
    builder.tick()
    builder.measure(0, key="mz", basis="Z")
    schedule = circuit_ir_to_substep_schedule(builder.build())

    distribution = _dense_jointL_level_distribution(
        schedule,
        {"local_dims": [2], "initial_levels": [0]},
        device="cpu",
    )

    assert distribution == pytest.approx(
        {(0, 0): 0.25, (0, 1): 0.25, (1, 0): 0.25, (1, 1): 0.25},
        abs=1.0e-14,
    )


def test_dense_level_oracle_preserves_probability_below_numerical_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import torch

    import error_coupling_simulator.carrier.joint_lindbladian as joint_lindbladian
    from error_coupling_simulator.certify.axis1_mps import (
        _dense_jointL_level_distribution,
    )
    from error_coupling_simulator.frontend import (
        Axis1LocalLindbladContextSpec,
        CircuitBuilder,
        circuit_ir_to_substep_schedule,
    )
    from error_coupling_simulator.numerics import NUMERICAL_ZERO

    probability = NUMERICAL_ZERO / 4.0
    no_jump = np.diag([math.sqrt(1.0 - probability), 1.0]).astype(np.complex128)
    excitation = np.array(
        [[0.0, 0.0], [math.sqrt(probability), 0.0]],
        dtype=np.complex128,
    )
    completeness = no_jump.conj().T @ no_jump + excitation.conj().T @ excitation
    np.testing.assert_array_equal(completeness, np.eye(2, dtype=np.complex128))

    def hand_typed_excitation_channel(*_args, **_kwargs):
        return [
            torch.as_tensor(no_jump, dtype=torch.complex128, device="cpu"),
            torch.as_tensor(excitation, dtype=torch.complex128, device="cpu"),
        ]

    monkeypatch.setattr(
        joint_lindbladian,
        "assemble_substep_channel",
        hand_typed_excitation_channel,
    )
    builder = CircuitBuilder(num_qubits=1)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            include_thermal_excitation=True,
            gamma_up_per_ns=1.0,
            gamma_1_per_ns=0.0,
            gamma_phi_per_ns=0.0,
        )
    )
    builder.idle(0, duration_ns=1.0)
    builder.measure(0, key="mz")
    schedule = circuit_ir_to_substep_schedule(builder.build())

    distribution = _dense_jointL_level_distribution(
        schedule,
        {"local_dims": [2], "initial_levels": [0]},
        device="cpu",
    )

    assert set(distribution) == {(0,), (1,)}
    assert distribution[(1,)] == pytest.approx(probability, rel=1.0e-12, abs=0.0)
    assert math.fsum(distribution.values()) == pytest.approx(1.0, abs=5.0e-15)


def _scaled_reset_lift(monkeypatch: pytest.MonkeyPatch, *, scale: float) -> None:
    import error_coupling_simulator.certify.axis1_mps as certification

    real_make_lift_fn = certification._make_lift_fn

    def make_scaled_lift_fn(*args, **kwargs):
        lift = real_make_lift_fn(*args, **kwargs)

        def scaled_lift(operator, support):
            lifted = lift(operator, support)
            reset_one_to_zero = np.array(
                [[0.0, 1.0], [0.0, 0.0]],
                dtype=np.complex128,
            )
            if tuple(support) == (0,) and np.array_equal(operator, reset_one_to_zero):
                return scale * lifted
            return lifted

        return scaled_lift

    monkeypatch.setattr(certification, "_make_lift_fn", make_scaled_lift_fn)


def _z_reset_then_measure_schedule():
    from error_coupling_simulator.frontend import (
        CircuitBuilder,
        circuit_ir_to_substep_schedule,
    )

    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key="mz_reset", basis="Z", reset=True)
    builder.tick()
    builder.measure(0, key="mz_after", basis="Z")
    return circuit_ir_to_substep_schedule(builder.build())


def test_dense_level_oracle_normalizes_every_finite_positive_reset_trace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from error_coupling_simulator.certify.axis1_mps import (
        _dense_jointL_level_distribution,
    )
    from error_coupling_simulator.numerics import NUMERICAL_ZERO

    _scaled_reset_lift(monkeypatch, scale=math.sqrt(NUMERICAL_ZERO / 4.0))

    distribution = _dense_jointL_level_distribution(
        _z_reset_then_measure_schedule(),
        {"local_dims": [2], "initial_levels": [1]},
        device="cpu",
    )

    assert distribution == {(1, 0): 1.0}


@pytest.mark.parametrize("scale", [0.0, float("nan")])
def test_dense_level_oracle_rejects_invalid_reset_trace(
    monkeypatch: pytest.MonkeyPatch,
    scale: float,
) -> None:
    from error_coupling_simulator.certify.axis1_mps import (
        _dense_jointL_level_distribution,
    )

    _scaled_reset_lift(monkeypatch, scale=scale)

    with pytest.raises(ValueError, match="reset trace must be finite and greater than zero"):
        _dense_jointL_level_distribution(
            _z_reset_then_measure_schedule(),
            {"local_dims": [2], "initial_levels": [1]},
            device="cpu",
        )


def test_x_measurement_reset_prepares_basis_zero_state() -> None:
    import quimb.tensor as qtn
    import torch

    import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as mcwf
    from error_coupling_simulator.frontend.axis1_record_layout import (
        Axis1MeasurementBoundaryLayout,
    )

    state = qtn.MPS_product_state((np.array([1.0, 0.0], dtype=np.complex128),))
    state.apply_to_arrays(
        lambda value: torch.as_tensor(
            value,
            dtype=torch.complex128,
            device="cpu",
        )
    )
    generator = torch.Generator(device="cpu")
    generator.manual_seed(3)
    levels, _bits, conditioned = mcwf._sample_measurement_multilevel(
        state,
        targets=(0,),
        bases=("X",),
        reset_after=(True,),
        local_dims=(2,),
        device="cpu",
        generator=generator,
        leaked_readout_b=0.5,
    )
    boundary = Axis1MeasurementBoundaryLayout(
        substep_id="mx",
        substep_index=0,
        operations=(),
        keys=("mx",),
        targets=(0,),
        bases=("X",),
        reset_after=(True,),
        global_slice=(0, 1),
    )

    reset = mcwf._apply_measurement_reset_if_requested_multilevel(
        conditioned,
        boundary,
        outcome_levels=levels,
        local_dims=(2,),
        device="cpu",
    )

    expected = np.array([1.0, 1.0], dtype=np.complex128) / math.sqrt(2.0)
    observed = reset.to_dense().detach().cpu().numpy().reshape(-1)
    np.testing.assert_allclose(observed, expected, rtol=0.0, atol=1.0e-14)


def test_x_measurement_rotation_is_identity_on_leaked_levels() -> None:
    import quimb.tensor as qtn
    import torch

    import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as mcwf

    state = qtn.MPS_product_state(
        (np.array([0.0, 0.0, 1.0], dtype=np.complex128),)
    )
    state.apply_to_arrays(
        lambda value: torch.as_tensor(
            value,
            dtype=torch.complex128,
            device="cpu",
        )
    )
    generator = torch.Generator(device="cpu")
    generator.manual_seed(4)

    levels, bits, conditioned = mcwf._sample_measurement_multilevel(
        state,
        targets=(0,),
        bases=("X",),
        reset_after=(False,),
        local_dims=(3,),
        device="cpu",
        generator=generator,
        leaked_readout_b=0.0,
    )

    assert levels == (2,)
    assert bits == (0,)
    observed = conditioned.to_dense().detach().cpu().numpy().reshape(-1)
    np.testing.assert_allclose(
        observed,
        np.array([0.0, 0.0, 1.0], dtype=np.complex128),
        rtol=0.0,
        atol=1.0e-14,
    )


def test_sampled_mcwf_emits_only_sorted_observed_support(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as mcwf
    from error_coupling_simulator.frontend.axis1_record_layout import (
        AXIS1_SCHEDULE_RECORD_LAYOUT_SCHEMA,
        Axis1MeasurementBoundaryLayout,
        Axis1ScheduleRecordLayout,
        Axis1XorLayout,
    )

    width = 20
    keys = tuple(f"m{index}" for index in range(width))
    targets = tuple(range(width))
    boundary = Axis1MeasurementBoundaryLayout(
        substep_id="measurement-0",
        substep_index=0,
        operations=(),
        keys=keys,
        targets=targets,
        bases=("Z",) * width,
        reset_after=(False,) * width,
        global_slice=(0, width),
    )
    layout = Axis1ScheduleRecordLayout(
        schema=AXIS1_SCHEDULE_RECORD_LAYOUT_SCHEMA,
        source_hash="mcwf-sparse-fixture",
        schedule_schema="fixture.v1",
        boundaries=(boundary,),
        measurement_keys=keys,
        measurement_targets=targets,
        measurement_bases=("Z",) * width,
        reset_after=(False,) * width,
        detectors=(
            Axis1XorLayout(
                ordinal=0,
                name="d0",
                keys=("m0",),
                columns=(0,),
            ),
        ),
        observables=(
            Axis1XorLayout(
                ordinal=0,
                name="l0",
                keys=("m19",),
                columns=(19,),
            ),
        ),
    )
    observed_records = iter(
        [
            (tuple([1] * width), tuple([1] * width)),
            (tuple([0] * width), tuple([0] * width)),
            (tuple([1] * width), tuple([1] * width)),
        ]
    )

    class FakeMps:
        def apply_to_arrays(self, _callback) -> None:
            return None

        def copy(self):
            return FakeMps()

    class FakeGenerator:
        def manual_seed(self, _seed):
            return self

    fake_quimb = ModuleType("quimb")
    fake_qtn = ModuleType("quimb.tensor")
    fake_qtn.MPS_product_state = lambda _vectors: FakeMps()
    fake_quimb.tensor = fake_qtn
    monkeypatch.setitem(sys.modules, "quimb", fake_quimb)
    monkeypatch.setitem(sys.modules, "quimb.tensor", fake_qtn)
    monkeypatch.setattr(mcwf.torch, "Generator", lambda *, device: FakeGenerator())
    monkeypatch.setattr(
        mcwf,
        "axis1_carrier_substep_summary",
        lambda _step: {
            "substep_id": "measurement-0",
            "substep_kind": "measurement",
        },
    )
    monkeypatch.setattr(mcwf, "_substep_has_mcwf_terms", lambda _step: False)

    def sample(state, **kwargs):
        assert kwargs["targets"] == targets
        assert kwargs["bases"] == ("Z",) * width
        assert kwargs["reset_after"] == (False,) * width
        levels, bits = next(observed_records)
        return levels, bits, state

    monkeypatch.setattr(mcwf, "_sample_measurement_multilevel", sample)
    monkeypatch.setattr(mcwf, "max_mps_bond", lambda _states: 1)
    monkeypatch.setattr(
        mcwf,
        "aggregate_sampled_truncation_events",
        lambda *_args, **_kwargs: {"context_complete": True},
    )
    monkeypatch.setattr(
        mcwf,
        "build_mps_truncation_ledger",
        lambda **_kwargs: {"discarded_weight_ledger_complete": True},
    )

    def forbidden_full_support(_width: int):
        raise AssertionError(
            "MCWF sampled execution materialized full binary support"
        )

    monkeypatch.setattr(mcwf, "materialize_binary_records", forbidden_full_support)
    execution = mcwf._execute_sampled_mcwf_program(
        {
            "program": {
                "num_qubits": width,
                "substeps": [
                    {
                        "substep_kind": "measurement",
                        "substep_id": "measurement-0",
                    }
                ],
            }
        },
        record_layout=layout,
        device="cuda",
        max_bond=None,
        microstep_count=1,
        finite_step_order="first_order",
        trajectory_count=3,
        rng_seed=11,
        local_dims=(2,) * width,
        initial_levels=(0,) * width,
        leaked_readout_b=0.5,
        dynamics_artifacts=(
            {
                "substep_index": 0,
                "substep_id": "measurement-0",
                "microstep_dt_ns": 0.0,
                "hamiltonian_dt_ns": 0.0,
                "hamiltonian_terms": (),
                "hamiltonian_groups": (),
                "collapse_terms": (),
            },
        ),
    )

    assert execution["measurement_records"] == [
        [0] * width,
        [1] * width,
    ]
    assert execution["record_counts"] == [1, 2]
    assert execution["record_probabilities"] == pytest.approx(
        [1.0 / 3.0, 2.0 / 3.0]
    )
    assert execution["record_count"] == 2
    assert execution["record_count"] <= execution["trajectory_sampling"][
        "trajectory_count"
    ]
    assert all(count > 0 for count in execution["record_counts"])
    assert execution["detector_records"] == [[0], [1]]
    assert execution["logical_observable_records"] == [[0], [1]]
    sampling = execution["trajectory_sampling"]
    assert sampling["measurement_sampling_policy"] == (
        "sequential_conditional_single_site_level_xz_v1"
    )
    assert sampling["record_support_policy"] == (
        "observed_empirical_outcomes_only"
    )
    assert sampling["zero_frequency_records_emitted"] is False


def test_dense_level_oracle_applies_x_measurement_reset_in_original_frame() -> None:
    from error_coupling_simulator.certify.axis1_mps import (
        _dense_jointL_level_distribution,
    )
    from error_coupling_simulator.frontend import (
        CircuitBuilder,
        circuit_ir_to_substep_schedule,
    )

    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key="mx_reset", basis="X", reset=True)
    builder.tick()
    builder.measure(0, key="mx_after", basis="X")
    schedule = circuit_ir_to_substep_schedule(builder.build())

    distribution = _dense_jointL_level_distribution(
        schedule,
        {"local_dims": [2], "initial_levels": [0]},
        device="cpu",
    )

    assert distribution == pytest.approx(
        {(0, 0): 0.5, (1, 0): 0.5},
        abs=1.0e-14,
    )


def test_dense_level_oracle_standalone_rx_prepares_plus_state() -> None:
    """Hand-written RX law: reset prepares |+>, so a later MX bit is zero."""

    import stim

    from error_coupling_simulator.certify.axis1_mps import (
        _dense_jointL_level_distribution,
    )
    from error_coupling_simulator.frontend import stim_circuit_to_substep_schedule

    schedule = stim_circuit_to_substep_schedule(
        stim.Circuit(
            """
            RX 0
            TICK
            MX 0
            """
        )
    )

    distribution = _dense_jointL_level_distribution(
        schedule,
        {"local_dims": [2], "initial_levels": [0]},
        device="cpu",
    )

    assert set(distribution) == {(0,)}
    assert distribution[(0,)] == pytest.approx(1.0, abs=1.0e-14)


def test_sampled_binary_firewall_rejects_zero_frequency_rows_hidden_by_level_route(
) -> None:
    import error_coupling_simulator.certify.axis1_mps as certification

    evaluator = {
        "schema": certification._EVALUATOR_ONLY_DIAGNOSTICS_SCHEMA,
        "visibility": (
            "evaluator_only_not_emitted_record_or_downstream_estimator_input"
        ),
        "level_record_semantics": certification._LEVEL_RECORD_SEMANTICS,
        "level_records": [[0]],
        "level_record_counts": [2],
        "level_record_probabilities": [1.0],
    }
    execution = {
        "measurement_keys": ["m0"],
        "measurement_targets": [0],
        "measurement_bases": ["Z"],
        "reset_after": [False],
        "measurement_basis": "Z",
        "measurement_basis_semantics": (
            "measurement_bases and reset_after are schedule-ordered one-per-Record-column; "
            "X measurement rotates into Z, projects, then rotates back unless reset prepares |+>"
        ),
        "measurement_records": [[0], [1]],
        "record_counts": [2, 0],
        "record_probabilities": [1.0, 0.0],
        "local_dims": [3],
        "evaluator_only_diagnostics": evaluator,
    }
    program = {
        "program": {
            "num_qubits": 1,
            "substeps": [
                {
                    "substep_kind": "measurement",
                    "operation_records": [
                        {"measurement_keys": ["m0"], "targets": [0]}
                    ],
                }
            ],
        }
    }

    with pytest.raises(ValueError, match=r"record_counts\[1\] must be positive"):
        certification._validate_metric_family_execution_payload(
            execution,
            sampled=True,
            trajectory_count=2,
            declared_local_dims=[3],
            program=program,
        )
