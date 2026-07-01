"""M12 Phase-B (2-site joint-collapse trajectory seam) — executable spec.

Puts the genuinely-new carrier code of the M12 Phase-B seam into the test suite (5-model review
finding #6: the seam was cert-only under outputs/). Covers the load-bearing operator physics
(anti-circular, vs a hand-typed Lindblad operator — NOT the carrier's own oracle) and the two carrier
fixes the panel required:

  fix #2  first-order MCWF mass-residual preflight guardrail (`_first_order_mass_residual_blocks` +
          `mass_residual_budget`): the no-jump Kraus K0 = I - 1/2 c^dag c dt is grossly non-CPTP at
          gamma*dt ~ 1 with too few microsteps (|11> probability mass -> 2.0); the manifest now
          fail-closes before execution and reports the required microstep_count.
  fix #3  two-site-collapse support-arity preflight (`_unsupported_substeps`): a CORR_RELAX request
          with non-two-site support fails closed in the manifest, not at the operator builder.
  fix #4  wrong-relative-sign falsifier: the relative sign of the collective jump is load-bearing
          (it swaps which Bell state is dark), so the seam's discriminating power is tested.

GPU-only (memory rule; CPU is not a release basis) — collection FAILS without CUDA.

Run:  conda run -n aiqec python -m pytest -q tests/test_m12_phaseB_seam.py
"""
from __future__ import annotations

import math

import numpy as np
import pytest
import torch

cuda_ok = torch.cuda.is_available()
if not cuda_ok:
    pytest.fail(
        "M12 Phase-B seam cert is GPU-gated; CUDA-MISSING is NOT A RELEASE BASIS",
        pytrace=False,
    )

import qec_twin.simulator.axis1_mcwf_mps_execution as execmod  # noqa: E402
from qec_twin.simulator import (  # noqa: E402
    CircuitBuilder,
    Axis1LocalLindbladContextSpec,
    axis1_mcwf_mps_state_record_execution_manifest,
    circuit_ir_to_substep_schedule,
)

DEV = "cuda"
SM = np.array([[0, 1], [0, 0]], dtype=complex)  # sigma^- = |0><1|
I2 = np.eye(2, dtype=complex)


def _cterm(family, support, coeff):
    return {
        "kind": "collapse",
        "operator_family": family,
        "support": list(support),
        "coefficient": float(coeff),
    }


def _prog(substeps):
    return {"program": {"num_qubits": 2, "substeps": substeps}}


def _collapse_substep(family, support, coeff, dt=20.0, substep_id="s0"):
    kind = "two_qubit_gate" if len(support) == 2 else "one_qubit_gate"
    return {
        "substep_id": substep_id,
        "substep_kind": kind,
        "dt_ns": float(dt),
        "terms": [_cterm(family, support, coeff)],
    }


# ---------------------------------------------------------------------------
# operator physics (anti-circular: hand-typed Lindblad operator, not the carrier oracle)
# ---------------------------------------------------------------------------
def test_joint_collapse_operator_is_hand_typed_collective_dicke():
    g = 0.05
    coeff = math.sqrt(g)
    c = execmod._joint_collapse_operator(
        _cterm("CORR_RELAX", (0, 1), coeff), (0, 1), local_dims=(2, 2), device=DEV
    )
    ref = coeff * (np.kron(SM, I2) + np.kron(I2, SM))  # hand-typed collective L
    assert float((c.detach().cpu().numpy() - ref).__abs__().max()) <= 1e-12


def test_joint_nojump_first_order_kraus():
    g = 0.05
    coeff = math.sqrt(g)
    dt = 20.0
    k0 = execmod._joint_nojump_first_order_kraus(
        _cterm("CORR_RELAX", (0, 1), coeff), dt, (0, 1), local_dims=(2, 2), device=DEV
    )
    ref_c = coeff * (np.kron(SM, I2) + np.kron(I2, SM))
    ref = np.eye(4, dtype=complex) - 0.5 * dt * (ref_c.conj().T @ ref_c)
    assert float((k0.detach().cpu().numpy() - ref).__abs__().max()) <= 1e-12


def test_wrong_relative_sign_swaps_the_dark_state():
    """fix #4: the relative sign is load-bearing. The CORRECT (+) collective op makes the
    ANTISYMMETRIC Bell state dark (subradiant) and the SYMMETRIC one bright (superradiant); the
    wrong (-) sign inverts this. A seam that lost the sign would be physically wrong."""
    g = 0.05
    coeff = math.sqrt(g)
    c_plus = execmod._joint_collapse_operator(
        _cterm("CORR_RELAX", (0, 1), coeff), (0, 1), local_dims=(2, 2), device=DEV
    ).detach().cpu().numpy()
    c_minus = coeff * (np.kron(SM, I2) - np.kron(I2, SM))  # the wrong-sign falsifier
    # |01>=index1, |10>=index2 in qubit-0-major order
    sym = np.zeros(4, complex); sym[1] = sym[2] = 1 / math.sqrt(2)
    anti = np.zeros(4, complex); anti[1] = 1 / math.sqrt(2); anti[2] = -1 / math.sqrt(2)
    # correct (+): antisym dark, sym bright
    assert np.linalg.norm(c_plus @ anti) <= 1e-12
    assert np.linalg.norm(c_plus @ sym) > 1e-6
    # wrong (-): sym dark, antisym bright (the inversion the falsifier exposes)
    assert np.linalg.norm(c_minus @ sym) <= 1e-12
    assert np.linalg.norm(c_minus @ anti) > 1e-6


# ---------------------------------------------------------------------------
# fix #3 — two-site-collapse support-arity preflight
# ---------------------------------------------------------------------------
def test_support_preflight_rejects_one_site_corr_relax():
    blocks = execmod._unsupported_substeps(
        _prog([_collapse_substep("CORR_RELAX", (0,), math.sqrt(0.05))]), local_dims=(2, 2)
    )
    assert blocks, "1-site CORR_RELAX must fail closed in the manifest preflight"
    assert blocks[0]["reason"] == "two_site_collapse_requires_two_site_support:CORR_RELAX"


def test_support_preflight_accepts_two_site_corr_relax():
    blocks = execmod._unsupported_substeps(
        _prog([_collapse_substep("CORR_RELAX", (0, 1), math.sqrt(0.05))]), local_dims=(2, 2)
    )
    reasons = [b["reason"] for b in blocks]
    assert not any(r.startswith("two_site_collapse_requires_two_site_support") for r in reasons)


# ---------------------------------------------------------------------------
# fix #2 — first-order MCWF mass-residual preflight guardrail
# ---------------------------------------------------------------------------
def test_mass_residual_guardrail_fail_closes_catastrophic_regime():
    """g=0.05, dt=20 => ||c^dag c||_op = 2g = 0.1; at m=1 the worst-case bound is
    1/4 dt^2 (0.1)^2 = 1.0 (|11>-mass 2.0). Required m = ceil(20*0.1/(2*sqrt(0.1))) = 4."""
    blocks = execmod._first_order_mass_residual_blocks(
        _prog([_collapse_substep("CORR_RELAX", (0, 1), math.sqrt(0.05), dt=20.0)]),
        local_dims=(2, 2), microstep_count=1, device=DEV, budget=0.1,
    )
    assert len(blocks) == 1
    assert blocks[0]["reason"].startswith("mcwf_first_order_mass_residual_exceeds_budget")
    assert blocks[0]["first_order_mass_residual_bound"] == pytest.approx(1.0, rel=1e-6)
    assert blocks[0]["required_microstep_count"] == 4


def test_mass_residual_guardrail_clears_at_required_microsteps():
    blocks = execmod._first_order_mass_residual_blocks(
        _prog([_collapse_substep("CORR_RELAX", (0, 1), math.sqrt(0.05), dt=20.0)]),
        local_dims=(2, 2), microstep_count=4, device=DEV, budget=0.1,
    )
    assert blocks == []


def test_mass_residual_guardrail_mild_regime_passes_at_m1():
    blocks = execmod._first_order_mass_residual_blocks(
        _prog([_collapse_substep("CORR_RELAX", (0, 1), math.sqrt(0.005), dt=20.0)]),
        local_dims=(2, 2), microstep_count=1, device=DEV, budget=0.1,
    )
    assert blocks == []


def test_mass_residual_guardrail_does_not_false_positive_on_physical_t1():
    """A physical T1 (gamma_1 ~ 1/75000 per ns) over a ~25 ns substep has a vanishing residual
    bound; the guardrail must not fire on ordinary use."""
    coeff = math.sqrt(1.0 / 75000.0)
    blocks = execmod._first_order_mass_residual_blocks(
        _prog([_collapse_substep("T1", (0,), coeff, dt=25.0)]),
        local_dims=(2, 2), microstep_count=1, device=DEV, budget=0.1,
    )
    assert blocks == []


# ---------------------------------------------------------------------------
# fix #2 — end-to-end: the manifest fail-closes (and budget=None overrides)
# ---------------------------------------------------------------------------
def _high_t1_schedule():
    """A single CZ substep with a catastrophically high T1 (gamma_1 = 0.05 per ns) — used only to
    drive the first-order step into the grossly-non-CPTP regime for the guardrail test."""
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(gamma_phi_per_ns=0.0, gamma_1_per_ns=0.05)
    )
    builder.cz((0, 1))
    builder.measure((0, 1), key=("m0", "m1"))
    return circuit_ir_to_substep_schedule(builder.build())


def test_manifest_fail_closes_on_catastrophic_first_order_step():
    manifest = axis1_mcwf_mps_state_record_execution_manifest(
        _high_t1_schedule(), local_dims=[2, 2], initial_levels=[1, 1],
        trajectory_count=2, rng_seed=11, microstep_count=1,
    )
    assert manifest["verdict"] == "fail"
    assert manifest["blocked_reason"].startswith("mcwf_first_order_mass_residual_exceeds_budget")
    assert manifest["blocked_substeps"][0]["required_microstep_count"] >= 2


def test_manifest_budget_none_disables_the_guardrail():
    """With the guardrail disabled, the same schedule is NOT rejected for the residual reason
    (a deliberate convergence study is the only sanctioned use of the coarse regime)."""
    manifest = axis1_mcwf_mps_state_record_execution_manifest(
        _high_t1_schedule(), local_dims=[2, 2], initial_levels=[1, 1],
        trajectory_count=2, rng_seed=11, microstep_count=1, mass_residual_budget=None,
    )
    reason = str(manifest.get("blocked_reason", ""))
    assert not reason.startswith("mcwf_first_order_mass_residual_exceeds_budget")
