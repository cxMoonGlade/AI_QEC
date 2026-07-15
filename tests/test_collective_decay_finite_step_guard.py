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
