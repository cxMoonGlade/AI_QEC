from __future__ import annotations

"""Phase-3 restricted-MPS Record-layout and reset-policy falsifiers.

The expected Record domains and point masses below are hand written.  This file
must not import the production ``_measurement_records`` or ``_xor_records``
helpers: otherwise a shared layout defect could make both execution and oracle
agree for the wrong reason.
"""

import copy

import pytest

try:
    import torch
except Exception as exc:  # pragma: no cover - broken GPU lane only.
    pytest.fail(f"restricted-MPS Phase-3 tests require torch: {exc}", pytrace=False)

if not torch.cuda.is_available():
    pytest.fail(
        "restricted-MPS Phase-3 tests are GPU-gated; CUDA-MISSING is NOT A RELEASE BASIS",
        pytrace=False,
    )

from error_coupling_simulator.frontend import (  # noqa: E402
    Axis1LocalLindbladContextSpec,
    CircuitBuilder,
    axis1_carrier_program_manifest,
    axis1_mcwf_mps_state_record_execution_manifest,
    axis1_qt_mps_restricted_execution_manifest,
    circuit_ir_to_substep_schedule,
)
from error_coupling_simulator.frontend.axis1_mcwf_mps_execution import (  # noqa: E402
    _unsupported_substeps as _mcwf_unsupported_substeps,
)


def _zero_noise_builder(num_qubits: int) -> CircuitBuilder:
    builder = CircuitBuilder(num_qubits=num_qubits)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            gamma_readout_phi_per_ns=0.0,
        )
    )
    return builder


def test_mps004_qt_sampled_uses_all_schedule_measurement_boundaries_for_record_law():
    """Two temporal boundaries define a two-bit Record before trajectories run."""

    builder = _zero_noise_builder(1)
    builder.x(0)
    builder.tick()
    builder.measure(0, key="round0")
    builder.tick()
    builder.x(0)
    builder.tick()
    builder.measure(0, key="round1")
    builder.detector("temporal_flip", xor=("round0", "round1"))
    builder.observable("final_level", xor=("round1",), index=0)
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_qt_mps_restricted_execution_manifest(
        schedule,
        trajectory_count=7,
        rng_seed=404,
    )

    assert manifest["verdict"] == "pass"
    execution = manifest["mps_execution"]

    # Independent hand-written oracle: |0> --X--> |1> --M--> 1 --X--> |0>
    # --M--> 0.  The sampled schema emits only observed empirical outcomes.
    assert execution["measurement_keys"] == ["round0", "round1"]
    assert execution["measurement_targets"] == [0, 0]
    assert execution["measurement_records"] == [[1, 0]]
    assert execution["record_counts"] == [7]
    assert execution["record_probabilities"] == [1.0]

    # These are the literal XOR values for the emitted Record, not values
    # produced by either MPS adapter's private XOR helper.
    assert execution["detector_names"] == ["temporal_flip"]
    assert execution["detector_records"] == [[1]]
    assert execution["logical_observable_names"] == ["final_level"]
    assert execution["logical_observable_records"] == [[0]]


def test_mps004_qt_parses_the_sealed_record_layout_once_before_trajectories(
    monkeypatch: pytest.MonkeyPatch,
):
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    builder = _zero_noise_builder(1)
    builder.measure(0, key="m0")
    schedule = circuit_ir_to_substep_schedule(builder.build())
    real_parser = qt.axis1_record_layout_from_schedule
    calls = 0

    def counted_parser(candidate):
        nonlocal calls
        calls += 1
        return real_parser(candidate)

    monkeypatch.setattr(qt, "axis1_record_layout_from_schedule", counted_parser)
    manifest = qt.axis1_qt_mps_restricted_execution_manifest(
        schedule,
        trajectory_count=5,
        rng_seed=4004,
    )

    assert manifest["verdict"] == "pass"
    assert calls == 1


def test_mps005_mcwf_parses_the_sealed_record_layout_once_before_trajectories(
    monkeypatch: pytest.MonkeyPatch,
):
    import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as mcwf

    builder = _zero_noise_builder(1)
    builder.measure(0, key="m0")
    schedule = circuit_ir_to_substep_schedule(builder.build())
    real_parser = mcwf.axis1_record_layout_from_schedule
    calls = 0

    def counted_parser(candidate):
        nonlocal calls
        calls += 1
        return real_parser(candidate)

    monkeypatch.setattr(mcwf, "axis1_record_layout_from_schedule", counted_parser)
    manifest = mcwf.axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        trajectory_count=5,
        rng_seed=5005,
    )

    assert manifest["verdict"] == "pass"
    assert calls == 1


@pytest.mark.parametrize(
    ("reset_mask", "expected_final_bits"),
    [
        pytest.param((True, True), (0, 0), id="merged-double-mr"),
        pytest.param((True, False), (0, 1), id="merged-mixed-reset-mask"),
    ],
)
def test_mps005_mcwf_merged_measurement_applies_each_operation_reset_mask(
    reset_mask: tuple[bool, bool],
    expected_final_bits: tuple[int, int],
):
    """A grouped boundary applies reset per operation, never all-or-nothing."""

    builder = _zero_noise_builder(2)
    builder.x((0, 1))
    builder.tick()
    builder.measure(0, key="before0", reset=reset_mask[0])
    builder.measure(1, key="before1", reset=reset_mask[1])
    builder.tick()
    builder.measure((0, 1), key=("after0", "after1"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    first_boundary = next(
        substep for substep in schedule.substeps if substep.kind == "measurement"
    )
    # This asserts compiler reachability of the defect: two disjoint public
    # MeasureOps really are merged into one carrier substep.
    assert len(first_boundary.operations) == 2
    assert tuple(op.reset_after_measurement for op in first_boundary.operations) == reset_mask

    manifest = axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        trajectory_count=5,
        rng_seed=505,
    )

    assert manifest["verdict"] == "pass"
    execution = manifest["mps_execution"]
    assert execution["measurement_keys"] == [
        "before0",
        "before1",
        "after0",
        "after1",
    ]
    assert execution["measurement_targets"] == [0, 1, 0, 1]

    # Independent hand-written point-mass oracle.  Both qubits are prepared in
    # |1>; the first two bits must therefore be (1, 1).  Each MR target is then
    # |0>, while each plain-M target remains |1> for the later readout.
    expected_record = (1, 1, *expected_final_bits)
    observed_nonzero_counts = {
        tuple(record): int(count)
        for record, count in zip(
            execution["measurement_records"],
            execution["record_counts"],
            strict=True,
        )
        if int(count) != 0
    }
    assert observed_nonzero_counts == {expected_record: 5}
    evaluator = execution["evaluator_only_diagnostics"]
    assert evaluator["level_records"] == [list(expected_record)]
    assert evaluator["level_record_counts"] == [5]


def test_mps005_mcwf_public_payload_preserves_ordered_xz_basis_and_reset_law():
    """The public Record columns retain X/Z and reset identity in schedule order."""

    builder = _zero_noise_builder(2)
    builder.h(0)
    builder.tick()
    builder.measure(0, key="mx_before", basis="X", reset=True)
    builder.measure(1, key="mz_before", basis="Z", reset=False)
    builder.tick()
    builder.measure(0, key="mx_after", basis="X")
    builder.measure(1, key="mz_after", basis="Z")
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        trajectory_count=5,
        rng_seed=5007,
    )

    assert manifest["schema"] == (
        "error_coupling_simulator.frontend.mcwf_mps_state_record_execution.v7"
    )
    assert manifest["verdict"] == "pass"
    execution = manifest["mps_execution"]
    assert execution["measurement_keys"] == [
        "mx_before",
        "mz_before",
        "mx_after",
        "mz_after",
    ]
    assert execution["measurement_targets"] == [0, 1, 0, 1]
    assert execution["measurement_bases"] == ["X", "Z", "X", "Z"]
    assert execution["reset_after"] == [True, False, False, False]
    assert execution["measurement_basis"] == "mixed_pauli"
    assert execution["measurement_basis_semantics"] == (
        "measurement_bases and reset_after are schedule-ordered one-per-Record-column; "
        "X measurement rotates into Z, projects, then rotates back unless reset prepares |+>"
    )

    # Hand-written law: |+>|0> -> (MX,MZ)=(0,0); X-reset prepares |+>, so the
    # later (MX,MZ) pair is again (0,0). No implementation helper computes it.
    assert execution["measurement_records"] == [[0, 0, 0, 0]]
    assert execution["record_counts"] == [5]
    assert execution["record_probabilities"] == [1.0]
    measurement_policy = execution["multilevel_measurement_policy"]
    assert measurement_policy["name"] == (
        "declared_basis_eigenlabel_sample_then_binary_record"
    )
    assert measurement_policy["bit_mapping"] == (
        "eigenlabel_0_to_bit_0_eigenlabel_1_to_bit_1_"
        "eigenlabel_ge_2_to_bit_1_with_probability_leaked_readout_b"
    )
    evaluator = execution["evaluator_only_diagnostics"]
    assert evaluator["schema"] == (
        "error_coupling_simulator.frontend."
        "mcwf_mps_evaluator_only_diagnostics.v2"
    )
    assert evaluator["level_record_semantics"] == (
        "schedule-ordered local measurement eigenlabel tuples: "
        "X columns use 0=|+>,1=|-> and preserve leaked level labels >=2; "
        "Z columns use computational local levels"
    )
    assert evaluator["level_records"] == [[0, 0, 0, 0]]
    assert evaluator["level_record_counts"] == [5]
    acceptance = manifest["restricted_acceptance_policy"]
    assert acceptance["schema"] == (
        "error_coupling_simulator.frontend."
        "mcwf_mps_restricted_acceptance_policy.v6"
    )
    assert acceptance["dense_jointL_record_certification"][
        "comparison_object"
    ] == "measurement_basis_level_and_emitted_binary_record_populations"


def test_mps012_qt_sampled_reset_row_is_labeled_as_sampled_boundary_only():
    """A sampled reset is not a product-formula dynamics substep."""

    builder = _zero_noise_builder(1)
    builder.x(0)
    builder.tick()
    builder.reset(0)
    builder.tick()
    builder.measure(0, key="after_reset")
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = axis1_qt_mps_restricted_execution_manifest(
        schedule,
        trajectory_count=3,
        rng_seed=12012,
    )

    assert manifest["verdict"] == "pass"
    execution = manifest["mps_execution"]
    assert execution["measurement_records"] == [[0]]
    assert execution["record_counts"] == [3]
    assert execution["record_probabilities"] == [1.0]
    reset_row = next(
        row for row in execution["applied_substeps"] if row["substep_kind"] == "reset"
    )

    expected_reset_metadata = {
        "substep_kind": "reset",
        "finite_step_policy": "boundary_only_no_generator_evolution",
        "reset_boundary_policy": "sampled_pauli_reset_internal_outcome_no_record",
        "sampled_trajectory_count": 3,
    }
    assert {
        key: reset_row.get(key) for key in expected_reset_metadata
    } == expected_reset_metadata
    assert {
        "finite_step_order",
        "microstep_count",
        "sampled_collapse_term_count",
    }.isdisjoint(reset_row)


def _compiler_program_with_gate_reset_and_measurement() -> dict:
    builder = _zero_noise_builder(1)
    builder.x(0)
    builder.tick()
    builder.reset(0)
    builder.tick()
    builder.measure(0, key="m0")
    schedule = circuit_ir_to_substep_schedule(builder.build())
    return axis1_carrier_program_manifest(schedule)


def test_mps013_mcwf_preflight_blocks_reset_substep_with_evolution_terms():
    """Reset control flow must not silently discard a dynamics term."""

    program = _compiler_program_with_gate_reset_and_measurement()
    substeps = program["program"]["substeps"]
    gate = next(row for row in substeps if row["substep_kind"] == "one_qubit_gate")
    reset = next(row for row in substeps if row["substep_kind"] == "reset")
    hamiltonian = next(term for term in gate["terms"] if term["kind"] == "hamiltonian")

    controlled = copy.deepcopy(program)
    controlled_reset = next(
        row
        for row in controlled["program"]["substeps"]
        if row["substep_kind"] == "reset"
    )
    controlled_reset["terms"].insert(0, copy.deepcopy(hamiltonian))
    controlled_reset["dt_ns"] = 25.0

    assert _mcwf_unsupported_substeps(controlled, local_dims=(2,)) == [
        {
            "substep_id": reset["substep_id"],
            "substep_kind": "reset",
            "reason": "mcwf_mps_reset_substep_contains_evolution_terms",
        }
    ]


def test_mps013_mcwf_preflight_blocks_evolution_without_positive_dt():
    """A measurement boundary with dynamics and no dt fails before float(None)."""

    program = _compiler_program_with_gate_reset_and_measurement()
    substeps = program["program"]["substeps"]
    gate = next(row for row in substeps if row["substep_kind"] == "one_qubit_gate")
    measurement = next(row for row in substeps if row["substep_kind"] == "measurement")
    hamiltonian = next(term for term in gate["terms"] if term["kind"] == "hamiltonian")

    controlled = copy.deepcopy(program)
    controlled_measurement = next(
        row
        for row in controlled["program"]["substeps"]
        if row["substep_kind"] == "measurement"
    )
    controlled_measurement["terms"].insert(0, copy.deepcopy(hamiltonian))
    assert controlled_measurement["dt_ns"] is None

    assert _mcwf_unsupported_substeps(controlled, local_dims=(2,)) == [
        {
            "substep_id": measurement["substep_id"],
            "substep_kind": "measurement",
            "reason": "mcwf_mps_evolution_terms_require_positive_dt_ns",
        }
    ]
