"""Independent physics and fail-closed guards for collective decay steps.

The operator reference is hand-typed from the collective lowering form.  The
remaining tests pin support arity and the finite-step probability-mass preflight,
including the public execution manifest that must expose a blocking diagnosis.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
import torch

import error_coupling_simulator.frontend.axis1_carrier_execution as carrier_execution
import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as execution
from error_coupling_simulator.frontend import (
    Axis1LocalLindbladContextSpec,
    CircuitBuilder,
    axis1_mcwf_mps_state_record_execution_manifest,
    circuit_ir_to_substep_schedule,
)


pytestmark = pytest.mark.skipif(
    not torch.cuda.is_available(),
    reason="collective-decay MCWF operator and preflight checks require CUDA",
)

DEVICE = "cuda"
LOWERING = np.array([[0, 1], [0, 0]], dtype=np.complex128)
IDENTITY = np.eye(2, dtype=np.complex128)


def _collapse_term(family: str, support, coefficient: float) -> dict:
    return {
        "kind": "collapse",
        "operator_family": family,
        "support": list(support),
        "coefficient": float(coefficient),
    }


def _program(substeps: list[dict]) -> dict:
    return {"program": {"num_qubits": 2, "substeps": substeps}}


def _collapse_substep(
    family: str,
    support,
    coefficient: float,
    *,
    dt_ns: float = 20.0,
) -> dict:
    support = tuple(support)
    return {
        "substep_id": "collective_decay_probe",
        "substep_kind": "two_qubit_gate" if len(support) == 2 else "one_qubit_gate",
        "dt_ns": float(dt_ns),
        "terms": [_collapse_term(family, support, coefficient)],
    }


def _collective_operator(coefficient: float) -> np.ndarray:
    return coefficient * (
        np.kron(LOWERING, IDENTITY) + np.kron(IDENTITY, LOWERING)
    )


def test_collective_decay_operator_matches_hand_typed_reference():
    coefficient = math.sqrt(0.05)
    actual = execution._joint_collapse_operator(
        _collapse_term("CORR_RELAX", (0, 1), coefficient),
        (0, 1),
        local_dims=(2, 2),
        device=DEVICE,
    )
    reference = _collective_operator(coefficient)
    assert np.max(np.abs(actual.detach().cpu().numpy() - reference)) <= 1.0e-12


def test_collective_decay_first_order_no_jump_matches_hand_typed_reference():
    coefficient = math.sqrt(0.05)
    dt_ns = 20.0
    actual = execution._joint_nojump_first_order_kraus(
        _collapse_term("CORR_RELAX", (0, 1), coefficient),
        dt_ns,
        (0, 1),
        local_dims=(2, 2),
        device=DEVICE,
    )
    collapse = _collective_operator(coefficient)
    reference = np.eye(4, dtype=np.complex128) - 0.5 * dt_ns * (
        collapse.conj().T @ collapse
    )
    assert np.max(np.abs(actual.detach().cpu().numpy() - reference)) <= 1.0e-12


def test_relative_sign_selects_the_dark_state():
    """Changing the relative sign swaps the symmetric and antisymmetric dark states."""
    coefficient = math.sqrt(0.05)
    plus = execution._joint_collapse_operator(
        _collapse_term("CORR_RELAX", (0, 1), coefficient),
        (0, 1),
        local_dims=(2, 2),
        device=DEVICE,
    ).detach().cpu().numpy()
    minus = coefficient * (
        np.kron(LOWERING, IDENTITY) - np.kron(IDENTITY, LOWERING)
    )

    symmetric = np.zeros(4, dtype=np.complex128)
    symmetric[1] = symmetric[2] = 1.0 / math.sqrt(2.0)
    antisymmetric = np.zeros(4, dtype=np.complex128)
    antisymmetric[1] = 1.0 / math.sqrt(2.0)
    antisymmetric[2] = -1.0 / math.sqrt(2.0)

    assert np.linalg.norm(plus @ antisymmetric) <= 1.0e-12
    assert np.linalg.norm(plus @ symmetric) > 1.0e-6
    assert np.linalg.norm(minus @ symmetric) <= 1.0e-12
    assert np.linalg.norm(minus @ antisymmetric) > 1.0e-6


def test_collective_decay_support_arity_fails_closed():
    blocks = execution._unsupported_substeps(
        _program(
            [_collapse_substep("CORR_RELAX", (0,), math.sqrt(0.05))]
        ),
        local_dims=(2, 2),
    )
    assert blocks
    assert blocks[0]["reason"] == (
        "two_site_collapse_requires_two_site_support:CORR_RELAX"
    )


def test_two_site_collective_decay_passes_support_preflight():
    blocks = execution._unsupported_substeps(
        _program(
            [_collapse_substep("CORR_RELAX", (0, 1), math.sqrt(0.05))]
        ),
        local_dims=(2, 2),
    )
    assert not any(
        block["reason"].startswith("two_site_collapse_requires_two_site_support")
        for block in blocks
    )


def test_mass_residual_preflight_reports_required_microsteps():
    program = _program(
        [_collapse_substep("CORR_RELAX", (0, 1), math.sqrt(0.05), dt_ns=20.0)]
    )
    blocks = execution._first_order_mass_residual_blocks(
        program,
        local_dims=(2, 2),
        microstep_count=1,
        device=DEVICE,
        budget=0.1,
    )
    assert len(blocks) == 1
    assert blocks[0]["reason"].startswith(
        "mcwf_first_order_mass_residual_exceeds_budget"
    )
    assert blocks[0]["first_order_mass_residual_bound"] == pytest.approx(
        1.0, rel=1.0e-6
    )
    assert blocks[0]["required_microstep_count"] == 4

    cleared = execution._first_order_mass_residual_blocks(
        program,
        local_dims=(2, 2),
        microstep_count=4,
        device=DEVICE,
        budget=0.1,
    )
    assert cleared == []


def test_mass_residual_preflight_allows_mild_local_decay():
    blocks = execution._first_order_mass_residual_blocks(
        _program(
            [_collapse_substep("T1", (0,), math.sqrt(1.0 / 75000.0), dt_ns=25.0)]
        ),
        local_dims=(2, 2),
        microstep_count=1,
        device=DEVICE,
        budget=0.1,
    )
    assert blocks == []


def test_mass_residual_preflight_bounds_realized_sequential_nojump_product():
    """The preflight must dominate the sampler's sequential K0 product.

    Two independent T1 terms with ``x = gamma * dt = 0.1`` expose the old
    single-sum formula: it reports ``x**2 = 0.01``, while the realized raw
    candidate mass on ``|11>`` has residual ``0.01450625`` because the sampler
    applies the two no-jump factors sequentially.  A budget between those two
    values must therefore fail closed.
    """

    x = 0.1
    dt_ns = 1.0
    gamma = x / dt_ns
    program = _program(
        [
            {
                "substep_id": "independent_t1_pair",
                "substep_kind": "two_qubit_gate",
                "dt_ns": dt_ns,
                "terms": [
                    _collapse_term("T1", (0,), math.sqrt(gamma)),
                    _collapse_term("T1", (1,), math.sqrt(gamma)),
                ],
            }
        ]
    )

    nojump_mass = (1.0 - x / 2.0) ** 4
    realized_residual = nojump_mass + 2.0 * x - 1.0
    obsolete_single_sum_bound = x**2
    budget = 0.012
    assert obsolete_single_sum_bound < budget < realized_residual

    blocks = execution._first_order_mass_residual_blocks(
        program,
        local_dims=(2, 2),
        microstep_count=1,
        device=DEVICE,
        budget=budget,
    )

    assert len(blocks) == 1
    # For b_i = x/2, u = sum(b_i) and
    # e = product(1 + b_i) - 1 - u, the implementation's true bound is
    # B = u**2 + 2 * (1 + u) * e + e**2.
    u = x
    e = (1.0 + x / 2.0) ** 2 - 1.0 - u
    reference_bound = u**2 + 2.0 * (1.0 + u) * e + e**2
    assert reference_bound == pytest.approx(0.01550625, abs=1.0e-15)
    assert blocks[0]["first_order_mass_residual_bound"] == pytest.approx(
        reference_bound,
        abs=1.0e-15,
    )
    assert blocks[0]["first_order_mass_residual_bound"] >= realized_residual
    assert blocks[0]["required_microstep_count"] == 2


def test_zero_mass_residual_budget_fails_closed_without_division_by_zero():
    program = _program(
        [_collapse_substep("T1", (0,), math.sqrt(1.0 / 75000.0), dt_ns=25.0)]
    )

    blocks = execution._first_order_mass_residual_blocks(
        program,
        local_dims=(2, 2),
        microstep_count=1,
        device=DEVICE,
        budget=0.0,
    )

    assert len(blocks) == 1
    assert blocks[0]["first_order_mass_residual_bound"] > 0.0
    assert blocks[0]["mass_residual_budget"] == 0.0
    assert blocks[0]["required_microstep_count"] is None
    assert blocks[0]["reason"] == (
        "mcwf_first_order_mass_residual_zero_budget_with_active_collapse"
    )


def test_mass_residual_bound_overflow_fails_closed_as_infinity():
    bound = execution._sequential_nojump_mass_residual_bound(
        dt_micro=2.0,
        operator_norms=(1.0e200,),
    )
    assert math.isinf(bound)
    assert bound > 0.0


def test_required_microstep_search_probes_final_supported_interval():
    required = execution._minimum_microstep_count_for_mass_budget(
        dt_substep=1.0,
        operator_norms=(1.0,),
        budget=5.0e-39,
        failing_microstep_count=1,
    )
    assert required is not None
    assert required <= (1 << 63) - 1
    assert execution._sequential_nojump_mass_residual_bound(
        dt_micro=1.0 / required,
        operator_norms=(1.0,),
    ) <= 5.0e-39
    assert execution._sequential_nojump_mass_residual_bound(
        dt_micro=1.0 / (required - 1),
        operator_norms=(1.0,),
    ) > 5.0e-39


def test_public_mcwf_rejects_budget_beyond_recommendation_search():
    with pytest.raises(
        ValueError,
        match=(
            "mass_residual_budget requires required_microstep_count beyond "
            "the signed-64-bit preflight recommendation search"
        ),
    ):
        axis1_mcwf_mps_state_record_execution_manifest(
            _high_decay_schedule(),
            local_dims=[2, 2],
            initial_levels=[1, 1],
            trajectory_count=1,
            rng_seed=11,
            microstep_count=1,
            mass_residual_budget=1.0e-300,
        )


def test_public_mcwf_rejects_zero_mass_residual_budget_before_cuda(
    monkeypatch: pytest.MonkeyPatch,
):
    cuda_calls = []

    def unexpected_cuda(device: str) -> str:
        cuda_calls.append(device)
        raise AssertionError("zero mass-residual budget reached CUDA")

    monkeypatch.setattr(execution, "_require_cuda_device", unexpected_cuda)

    with pytest.raises(
        ValueError,
        match="mass_residual_budget must be positive when provided",
    ):
        axis1_mcwf_mps_state_record_execution_manifest(
            _high_decay_schedule(),
            local_dims=[2, 2],
            initial_levels=[1, 1],
            trajectory_count=1,
            rng_seed=11,
            microstep_count=1,
            mass_residual_budget=0.0,
        )
    assert cuda_calls == []


@pytest.mark.parametrize(
    "backend_contract",
    (
        carrier_execution.AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT,
        carrier_execution.AXIS1_CARRIER_AUTO_BACKEND_CONTRACT,
    ),
    ids=("explicit_mcwf", "auto"),
)
def test_carrier_routes_reject_zero_mass_residual_budget_before_cuda(
    monkeypatch: pytest.MonkeyPatch,
    backend_contract: str,
):
    cuda_calls = []

    def unexpected_cuda(device: str) -> str:
        cuda_calls.append(device)
        raise AssertionError("Carrier zero mass-residual budget reached CUDA")

    monkeypatch.setattr(carrier_execution, "_require_cuda_device", unexpected_cuda)

    with pytest.raises(
        ValueError,
        match="mass_residual_budget must be positive when provided",
    ):
        carrier_execution.axis1_carrier_execution_manifest(
            _high_decay_schedule(),
            execution_backend_contract=backend_contract,
            execution_backend_options={"mass_residual_budget": 0.0},
        )
    assert cuda_calls == []


def _high_decay_schedule():
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.05,
        )
    )
    builder.cz((0, 1))
    builder.measure((0, 1), key=("m0", "m1"))
    return circuit_ir_to_substep_schedule(builder.build())


def _overcap_high_decay_schedule():
    builder = CircuitBuilder(num_qubits=6)
    builder.declare_static_zz_couplings(((0, 5),))
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.05,
        )
    )
    builder.idle(tuple(range(6)), duration_ns=20.0)
    return circuit_ir_to_substep_schedule(builder.build())


def test_execution_manifest_exposes_mass_residual_block():
    manifest = axis1_mcwf_mps_state_record_execution_manifest(
        _high_decay_schedule(),
        local_dims=[2, 2],
        initial_levels=[1, 1],
        trajectory_count=2,
        rng_seed=11,
        microstep_count=1,
    )
    assert manifest["verdict"] == "fail"
    assert manifest["blocked_reason"].startswith(
        "mcwf_first_order_mass_residual_exceeds_budget"
    )
    assert manifest["blocked_substeps"][0]["required_microstep_count"] >= 2


def test_manifest_budget_override_is_explicit():
    manifest = axis1_mcwf_mps_state_record_execution_manifest(
        _high_decay_schedule(),
        local_dims=[2, 2],
        initial_levels=[1, 1],
        trajectory_count=2,
        rng_seed=11,
        microstep_count=1,
        mass_residual_budget=None,
    )
    assert not str(manifest.get("blocked_reason", "")).startswith(
        "mcwf_first_order_mass_residual_exceeds_budget"
    )
    assert manifest["execution_status"] == "completed"
    assert manifest["certification_status"] == "not_evaluated"
    assert manifest["diagnostic_only"] is True
    assert manifest["verdict"] == "fail"
    assert manifest["passed"] is False


def test_mcwf_overcap_none_budget_cannot_pass_restricted_acceptance():
    """MPS-002: record-count normalization cannot hide invalid MCWF branch mass."""

    manifest = axis1_mcwf_mps_state_record_execution_manifest(
        _overcap_high_decay_schedule(),
        local_dims=[2] * 6,
        initial_levels=[1] * 6,
        trajectory_count=1,
        rng_seed=11,
        microstep_count=1,
        mass_residual_budget=None,
    )

    runtime_residual = manifest["mps_execution"]["jump_sampling"][
        "probability_mass_residual_max"
    ]
    # Six T1 jumps each carry unit raw mass. The no-jump candidate has norm
    # squared (1 - gamma*dt/2)^(2*6) = (1/2)^12, so total mass is
    # 6 + 2^-12 and the independently expected residual is 5 + 2^-12.
    assert runtime_residual == pytest.approx(5.0 + 0.5**12, abs=1.0e-9)
    assert manifest["mps_execution"]["total_probability_residual"] == 0.0

    assert manifest["verdict"] == "fail"
    assert manifest["passed"] is False
    assert manifest["execution_status"] == "completed"
    assert manifest["certification_status"] == "not_evaluated"
    assert manifest["diagnostic_only"] is True
    policy = manifest["restricted_acceptance_policy"]
    assert policy["accepted_for_restricted_execution"] is False
    assert policy["certification_status"] == "not_evaluated"
    assert policy["diagnostic_only"] is True
    assert policy["probability"]["runtime_candidate_mass_residual"] == pytest.approx(
        5.0 + 0.5**12,
        abs=1.0e-9,
    )
    assert policy["probability"]["runtime_candidate_mass_residual_budget"] is None
    assert policy["probability"]["runtime_candidate_mass_residual_within_budget"] is None


@pytest.mark.parametrize(
    "budget",
    [math.nan, math.inf, -math.inf],
    ids=["nan", "positive_inf", "negative_inf"],
)
def test_mcwf_rejects_nonfinite_mass_residual_budget_before_execution(
    monkeypatch: pytest.MonkeyPatch,
    budget,
):
    cuda_calls = []

    def unexpected_cuda(device: str) -> str:
        cuda_calls.append(device)
        raise AssertionError("nonfinite budget reached CUDA")

    monkeypatch.setattr(execution, "_require_cuda_device", unexpected_cuda)

    with pytest.raises(ValueError):
        axis1_mcwf_mps_state_record_execution_manifest(
            _overcap_high_decay_schedule(),
            local_dims=[2] * 6,
            initial_levels=[1] * 6,
            trajectory_count=1,
            rng_seed=11,
            microstep_count=1,
            mass_residual_budget=budget,
        )
    assert cuda_calls == []


def test_mcwf_overcap_finite_mass_budget_without_oracle_is_diagnostic_only():
    manifest = axis1_mcwf_mps_state_record_execution_manifest(
        _overcap_high_decay_schedule(),
        local_dims=[2] * 6,
        initial_levels=[1] * 6,
        trajectory_count=1,
        rng_seed=11,
        microstep_count=1,
        # Six sequential no-jump factors have a conservative product-bound
        # above the old single-sum value of 9.  Keep this test focused on the
        # unavailable-oracle policy branch by choosing a budget that clears the
        # corrected preflight.
        mass_residual_budget=200.0,
    )

    policy = manifest["restricted_acceptance_policy"]
    assert manifest["execution_status"] == "completed"
    assert manifest["certification_status"] == "unavailable"
    assert manifest["diagnostic_only"] is True
    assert manifest["verdict"] == "fail"
    assert manifest["passed"] is False
    assert policy["accepted_for_restricted_execution"] is False
    assert policy["accepted_as_restricted_overcap_execution"] is False
    assert policy["probability"]["runtime_candidate_mass_residual_within_budget"] is True
    assert policy["blocked_reason"].startswith("dense_jointL_certification:")
