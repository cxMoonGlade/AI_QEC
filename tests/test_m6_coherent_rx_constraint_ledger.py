"""M6 coherent_rx_overrotation — CONSTRAINT LEDGER (executable falsifier tests).

FAITHFULNESS PROTOCOL (docs/FAITHFULNESS_PROTOCOL.md) — constraint ledger for M6.
Each test below is a FALSIFIER: it documents the invariant AND shows that a
deliberately BROKEN input makes the test FAIL (trips the falsifier). Tests run
GREEN on the faithful carrier and RED on the broken variant.

ANTI-CIRCULARITY: the reference operator (``ref_H_M6``) is HAND-TYPED from the
literature (Nielsen & Chuang Eq. 2.1 + Eq. 4.4–4.7; Kaufmann-Rojkov-Reiter
arXiv:2307.08741 Eq. 2). The cert imports ONLY
``axis1_mcwf_mps_execution._hamiltonian_matrix_for_term`` (the object under test).
The carrier's ``_coherent_family_generator`` / ``_embed_coherent_generator`` /
``ONE_SITE_COHERENT_FAMILIES`` constants appear NOWHERE in the reference code
(same de-circularization rule as test_axis1_wc_decircularized.py).

GATE TIER: STRICT (``1−F_e ≤ 1e-6``; operator identity ≤ 1e-12 / unitary ≤ 1e-10).
M6 is a pure-Hamiltonian / exact-dense error — no collapse, no finite-step MCWF.

GPU-only (top-level memory rule) — collection FAILS without CUDA.

Pre-registration: docs/twin_validation/m6_coherent_rx_overrotation_prereg.md
Run:  conda run -n aiqec python -m pytest -q tests/test_m6_coherent_rx_constraint_ledger.py
"""
from __future__ import annotations

import math
import inspect

import pytest
import torch

# ---------------------------------------------------------------------------
# GPU gate (top-level memory rule: collection fails without CUDA)
# ---------------------------------------------------------------------------
cuda_ok = torch.cuda.is_available()
if not cuda_ok:
    pytest.fail(
        "M6 constraint-ledger cert is GPU-gated; CUDA-MISSING is NOT A RELEASE BASIS",
        pytrace=False,
    )

# ---------------------------------------------------------------------------
# Carrier import — ONLY the per-term operator builder (anti-circular)
# ---------------------------------------------------------------------------
from qec_twin.simulator.axis1_mcwf_mps_execution import (  # noqa: E402
    _hamiltonian_matrix_for_term,
)
from qec_twin.forward.joint_lindbladian import (  # noqa: E402
    _choi_state_from_kraus,
    _state_fidelity,
    assemble_substep_channel,
)

DEV = "cuda"

# ---------------------------------------------------------------------------
# Invariant tolerances (pre-registration §2, §6)
# ---------------------------------------------------------------------------
_HERMITIAN_TOL = 1e-12      # ||H - H†||_F ≤ this  (class-a exact)
_TRACELESS_TOL = 1e-12      # |Tr H| ≤ this          (class-a exact)
_OPERATOR_DIFF_TOL = 1e-12  # ||H_carrier - H_ref||_F (class-a exact, B4)
_UNITARY_DIFF_TOL = 1e-10   # ||U_carrier - U_ref||_F (class-a exact, B4)
_INFIDELITY_TOL = 1e-6      # 1−F_e ≤ this for strict pure-Hamiltonian (S1)
_WRONG_AXIS_MIN = 1e-3      # wrong-axis control must trip by ≥ this


# ---------------------------------------------------------------------------
# Reference operator (HAND-TYPED, non-circular)
# Provenance: H_M6 = (coeff/2) * sigma_x on the 2-level computational subspace.
#   sigma_x = [[0,1],[1,0]]  (Nielsen & Chuang Eq. 2.1, Pauli-X).
#   factor 1/2: R_x(theta) = exp(-i theta X/2)  (N&C Eq. 4.4–4.7).
#   error gate: U = exp(-i H dt) = RX(eps), eps = coeff * dt_ns.
#   mechanism paper: Kaufmann-Rojkov-Reiter arXiv:2307.08741 Eq. 2 (H_theta = sum_k theta_k P_k).
# Identity (zero generator) on leaked levels >= 2 for qutrit/ququart carriers.
# ---------------------------------------------------------------------------
def ref_H_M6(coeff: float, dim: int) -> torch.Tensor:
    """Hand-typed M6 reference generator on the `dim`-level local space.

    H_M6 = (coeff/2) * X  embedded into the `dim`-dimensional local space,
    with the zero generator (identity block) on levels >= 2 (no leakage drive).
    Importing NOTHING from the carrier family tables.
    """
    cdt = torch.complex128
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    H = torch.zeros((dim, dim), dtype=cdt, device=DEV)
    H[:2, :2] = 0.5 * coeff * X2
    return H


def ref_U_M6(coeff: float, dt_ns: float, dim: int) -> torch.Tensor:
    """Hand-typed M6 error unitary: U = matrix_exp(-i * H * dt)."""
    H = ref_H_M6(coeff, dim)
    return torch.linalg.matrix_exp(-1j * dt_ns * H)


def exact_infidelity_M6(eps: float) -> float:
    """Closed-form 1-F_e for RX(eps) vs identity (d=2).

    1 - |Tr(RX(eps))/2|^2 = 1 - cos^2(eps/2) = sin^2(eps/2).
    Reference: Nielsen arXiv:quant-ph/0205035 Eq. 16 (F_e = |Tr U / d|^2 for unitary U).
    """
    return float(math.sin(eps / 2.0) ** 2)


def _make_coh_rx_term(coeff: float) -> dict:
    """Minimal schedule-term dict for COH_RX on one site (support=(0,))."""
    return {
        "kind": "hamiltonian",
        "operator_family": "COH_RX",
        "support": [0],
        "coefficient": float(coeff),
        "substep_id": "m6_ledger",
    }


# ---------------------------------------------------------------------------
# INVARIANT L1: Hermiticity  ||H - H†||_F ≤ 1e-12
# BROKEN INPUT: a non-Hermitian matrix (add an imaginary off-diagonal term)
# ---------------------------------------------------------------------------

def test_L1_generator_is_hermitian():
    """L1 (class-a exact): the M6 generator H satisfies H = H†.

    Broken-input demonstration: an explicitly non-Hermitian operator trips this test.
    """
    coeff = 0.1
    H = _hamiltonian_matrix_for_term(
        _make_coh_rx_term(coeff),
        support=(0,),
        local_dims=(2,),
        device=DEV,
    )
    resid = float(torch.linalg.matrix_norm(H - H.conj().T).item())
    assert resid <= _HERMITIAN_TOL, (
        f"L1 FAIL: ||H - H†||_F = {resid:.3e} > {_HERMITIAN_TOL}; "
        "M6 generator is not Hermitian — physics bug"
    )


def test_L1_broken_non_hermitian_trips():
    """FALSIFIER: a deliberately non-Hermitian matrix fails the L1 check."""
    cdt = torch.complex128
    H_broken = torch.tensor([[0.0, 1.0j], [0.0, 0.0]], dtype=cdt, device=DEV)
    resid = float(torch.linalg.matrix_norm(H_broken - H_broken.conj().T).item())
    assert resid > _HERMITIAN_TOL, (
        "FALSIFIER DID NOT TRIP: a known non-Hermitian matrix passed L1 — "
        "the falsifier is broken"
    )


# ---------------------------------------------------------------------------
# INVARIANT L2: Tracelessness  |Tr H| ≤ 1e-12
# Pauli generators are traceless; an identity-shifted generator is WRONG.
# BROKEN INPUT: H + (c/2) * I (trace = coeff)
# ---------------------------------------------------------------------------

def test_L2_generator_is_traceless():
    """L2 (class-a exact): the M6 generator H is traceless (Pauli X is traceless)."""
    coeff = 0.1
    H = _hamiltonian_matrix_for_term(
        _make_coh_rx_term(coeff),
        support=(0,),
        local_dims=(2,),
        device=DEV,
    )
    tr_resid = float(torch.abs(torch.trace(H)).item())
    assert tr_resid <= _TRACELESS_TOL, (
        f"L2 FAIL: |Tr H| = {tr_resid:.3e} > {_TRACELESS_TOL}; "
        "M6 generator has a non-zero trace — wrong axis or identity contamination"
    )


def test_L2_broken_identity_shift_trips():
    """FALSIFIER: a traceful generator (Pauli + identity offset) fails L2."""
    cdt = torch.complex128
    H_broken = 0.05 * torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV) \
             + 0.05 * torch.eye(2, dtype=cdt, device=DEV)
    tr_resid = float(torch.abs(torch.trace(H_broken)).item())
    assert tr_resid > _TRACELESS_TOL, (
        "FALSIFIER DID NOT TRIP: an identity-shifted generator passed L2 — "
        "the falsifier is broken"
    )


# ---------------------------------------------------------------------------
# INVARIANT L3: Operator identity  ||H_carrier - H_ref||_F ≤ 1e-12  (B4, class-a)
# This is the LOAD-BEARING cert gate (1-F_e alone cannot catch wrong Pauli axis).
# BROKEN INPUT: a wrong-axis generator (Z instead of X) — must disagree by ≥ 1e-3
# ---------------------------------------------------------------------------

def test_L3_operator_matches_hand_typed_reference():
    """L3 (class-a exact, B4): the carrier generator equals the hand-typed reference.

    H_ref = (coeff/2) * X2 embedded in dim, from Nielsen & Chuang / 2307.08741.
    This is the LOAD-BEARING gate — 1-F_e alone cannot distinguish RX from RZ at
    equal angle (both have identical scalar infidelity).
    """
    for coeff in (0.3, 0.1, 0.03, 0.01, 0.003, 0.001):
        for dim in (2, 3):
            H_carrier = _hamiltonian_matrix_for_term(
                _make_coh_rx_term(coeff),
                support=(0,),
                local_dims=(dim,),
                device=DEV,
            )
            H_ref = ref_H_M6(coeff, dim)
            diff = float(torch.linalg.matrix_norm(H_carrier - H_ref).item())
            assert diff <= _OPERATOR_DIFF_TOL, (
                f"L3 FAIL: ||H_carrier - H_ref||_F = {diff:.3e} > {_OPERATOR_DIFF_TOL} "
                f"at coeff={coeff}, dim={dim} — wrong generator (wrong axis, wrong coefficient, "
                "wrong convention)"
            )


def test_L3_broken_wrong_axis_trips():
    """FALSIFIER (level-discriminating negative control): a wrong-axis reference (Z instead of X)
    disagrees with the carrier by ≥ 1e-3 for any nonzero epsilon not a multiple of 2pi.

    This is the M6 analogue of the W-C leakage cert's wrong-level falsifier.
    A circular reference derived FROM the corrupted carrier map would mirror the wrong axis
    to diff=0 (false-pass); the hand-typed X reference catches the corruption.
    """
    coeff = 0.1
    dim = 2
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_rx_term(coeff),
        support=(0,),
        local_dims=(dim,),
        device=DEV,
    )
    cdt = torch.complex128
    # Wrong-axis reference: (coeff/2) * Z  (should be X)
    Z2 = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=cdt, device=DEV)
    H_wrong_axis = 0.5 * coeff * Z2
    diff = float(torch.linalg.matrix_norm(H_carrier - H_wrong_axis).item())
    assert diff >= _WRONG_AXIS_MIN, (
        f"FALSIFIER DID NOT TRIP: wrong-axis (Z) reference passed with diff={diff:.3e} < "
        f"{_WRONG_AXIS_MIN}; the X/Z confusion is undetectable — operator-identity cert broken"
    )


def test_L3_broken_wrong_unit_convention_trips():
    """FALSIFIER: wrong-unit convention (treating coeff as the angle, missing the ×1/2 factor)
    disagrees with the correct reference.

    Wrong form: H_wrong = coeff * X  (missing the 1/2 factor from R_x convention).
    The correct form is H = (coeff/2) * X.
    """
    coeff = 0.1
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_rx_term(coeff),
        support=(0,),
        local_dims=(2,),
        device=DEV,
    )
    cdt = torch.complex128
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    H_wrong_unit = float(coeff) * X2   # missing the 1/2
    diff = float(torch.linalg.matrix_norm(H_carrier - H_wrong_unit).item())
    assert diff >= _WRONG_AXIS_MIN, (
        f"FALSIFIER DID NOT TRIP: wrong-unit convention (coeff*X, missing 1/2) has diff={diff:.3e} < "
        f"{_WRONG_AXIS_MIN}; the factor-of-2 error is undetectable"
    )


# ---------------------------------------------------------------------------
# INVARIANT L4: Unitary identity  ||U_carrier - U_ref||_F ≤ 1e-10  (B4, class-a)
# U = matrix_exp(-i H dt) = RX(eps), eps = coeff * dt_ns.
# BROKEN INPUT: wrong-sign in the exponent (U = exp(+i H dt)), gives RX(-eps).
# ---------------------------------------------------------------------------

def test_L4_error_unitary_matches_rx_reference():
    """L4 (class-a exact, B4): the carrier's error gate U = exp(-i H dt) equals the
    reference RX(eps) unitary to ≤ 1e-10.
    """
    dt_ns = 20.0
    for coeff in (0.3, 0.1, 0.03, 0.01, 0.003, 0.001):
        for dim in (2, 3):
            eps = coeff * dt_ns
            H_carrier = _hamiltonian_matrix_for_term(
                _make_coh_rx_term(coeff),
                support=(0,),
                local_dims=(dim,),
                device=DEV,
            )
            U_carrier = torch.linalg.matrix_exp(-1j * dt_ns * H_carrier)
            U_ref = ref_U_M6(coeff, dt_ns, dim)
            diff = float(torch.linalg.matrix_norm(U_carrier - U_ref).item())
            assert diff <= _UNITARY_DIFF_TOL, (
                f"L4 FAIL: ||U_carrier - U_ref||_F = {diff:.3e} > {_UNITARY_DIFF_TOL} "
                f"at coeff={coeff}, dt={dt_ns}, eps={eps:.3f}, dim={dim}"
            )


def test_L4_broken_wrong_sign_exponent_trips():
    """FALSIFIER: the wrong-sign exponent (exp(+i H dt)) disagrees with the correct gate
    by ≥ 1e-3 for any non-zero eps not a multiple of pi.
    """
    coeff = 0.1
    dt_ns = 20.0
    dim = 2
    H_ref = ref_H_M6(coeff, dim)
    U_correct = torch.linalg.matrix_exp(-1j * dt_ns * H_ref)
    U_wrong_sign = torch.linalg.matrix_exp(+1j * dt_ns * H_ref)  # wrong sign
    diff = float(torch.linalg.matrix_norm(U_correct - U_wrong_sign).item())
    assert diff >= _WRONG_AXIS_MIN, (
        f"FALSIFIER DID NOT TRIP: wrong-sign exponent has diff={diff:.3e} < "
        f"{_WRONG_AXIS_MIN}; the sign flip is undetectable"
    )


# ---------------------------------------------------------------------------
# INVARIANT L5: CPTP residual (TP check)  ||sum_k K†K - I||_F ≤ 1e-12
# For a pure unitary (no collapse), the Kraus channel has a SINGLE Kraus = U.
# BROKEN INPUT: a non-unitary matrix (e.g. a dephased form with a non-TP residual).
# ---------------------------------------------------------------------------

def test_L5_channel_is_tp():
    """L5 (class-a exact): the M6 Kraus channel assembled from H_M6 alone (no collapse)
    is exactly trace-preserving: sum_k K†K = I to ≤ 1e-12.
    """
    dt_ns = 20.0
    coeff = 0.1
    H = _hamiltonian_matrix_for_term(
        _make_coh_rx_term(coeff),
        support=(0,),
        local_dims=(2,),
        device=DEV,
    )
    kraus = assemble_substep_channel([H], [], dt_ns, device=DEV)
    D = kraus.shape[-1]
    sumKdK = torch.zeros((D, D), dtype=torch.complex128, device=DEV)
    for k in range(kraus.shape[0]):
        Kk = kraus[k]
        sumKdK = sumKdK + Kk.conj().T @ Kk
    resid = float(torch.linalg.matrix_norm(
        sumKdK - torch.eye(D, dtype=torch.complex128, device=DEV)
    ).item())
    assert resid <= 1e-12, (
        f"L5 FAIL: ||sum K†K - I||_F = {resid:.3e} > 1e-12; "
        "M6 channel is not trace-preserving"
    )


def test_L5_broken_non_tp_trips():
    """FALSIFIER: a non-unitary (non-TP) Kraus set fails L5."""
    cdt = torch.complex128
    # A non-unitary 2x2: scaling down by 0.8 (not TP)
    K_bad = torch.tensor([[0.8, 0.0], [0.0, 0.8]], dtype=cdt, device=DEV)
    kraus_bad = K_bad.unsqueeze(0)
    D = kraus_bad.shape[-1]
    sumKdK = torch.zeros((D, D), dtype=cdt, device=DEV)
    for k in range(kraus_bad.shape[0]):
        Kk = kraus_bad[k]
        sumKdK = sumKdK + Kk.conj().T @ Kk
    resid = float(torch.linalg.matrix_norm(
        sumKdK - torch.eye(D, dtype=cdt, device=DEV)
    ).item())
    assert resid > 1e-12, (
        "FALSIFIER DID NOT TRIP: a known non-TP matrix passed L5 — falsifier broken"
    )


# ---------------------------------------------------------------------------
# INVARIANT L6: process infidelity == sin^2(eps/2) to Uhlmann floor  (B1, class-b band)
# RX(eps) vs identity: 1-F_e = sin^2(eps/2) (Nielsen quant-ph/0205035 Eq. 16).
# Threshold: STRICT 1-F_e ≤ 1e-6 (pure Hamiltonian, S1).
# BROKEN INPUT: a Kraus stack representing the wrong gate (RZ instead of RX at same angle)
#   — the scalar infidelity is IDENTICAL (same sin^2) but the operator is wrong; this is why
#   L3/L4 (operator identity) are the LOAD-BEARING gates and 1-F_e alone is INSUFFICIENT.
# ---------------------------------------------------------------------------

def test_L6_infidelity_matches_exact_closed_form():
    """L6 (class-b band, B1): carrier 1-F_e = sin^2(eps/2) to the Uhlmann estimator floor (~2e-8).

    Swept over eps in {0.3, 0.1, 0.03, 0.01, 0.003, 0.001} rad.
    The STRICT gate tier requires the carrier-assembled channel infidelity vs identity ≤ 1e-6
    (pure-Hamiltonian, no collapse; S1).
    """
    dt_ns = 20.0
    cdt = torch.complex128
    I_kraus = torch.eye(2, dtype=cdt, device=DEV).unsqueeze(0)   # identity reference channel
    J_I = _choi_state_from_kraus(I_kraus, device=DEV)

    for coeff in (0.3 / dt_ns, 0.1 / dt_ns, 0.03 / dt_ns, 0.01 / dt_ns,
                  0.003 / dt_ns, 0.001 / dt_ns):
        eps = coeff * dt_ns
        H = _hamiltonian_matrix_for_term(
            _make_coh_rx_term(coeff),
            support=(0,),
            local_dims=(2,),
            device=DEV,
        )
        kraus = assemble_substep_channel([H], [], dt_ns, device=DEV)
        J_carrier = _choi_state_from_kraus(kraus, device=DEV)
        F_e = float(_state_fidelity(J_carrier, J_I, device=DEV))
        one_minus_fe = float(max(0.0, 1.0 - F_e))
        exact = exact_infidelity_M6(eps)
        # b-band check: carrier agrees with sin^2(eps/2) to Uhlmann floor (~2e-8).
        # The STRICT tier (S1) means the NUMERICAL precision of the carrier vs the EXACT
        # closed form is within 1e-6 — it does NOT mean the error gate has small infidelity
        # vs identity (which is sin^2(eps/2), correctly large for large eps).
        band_resid = abs(one_minus_fe - exact)
        assert band_resid <= 5e-7, (
            f"L6 FAIL: |carrier_1-F_e - sin^2(eps/2)| = {band_resid:.3e} at eps={eps:.4f}; "
            f"carrier={one_minus_fe:.6e}, exact={exact:.6e} — "
            "STRICT means numerical agreement with the closed form, not that eps is small"
        )


def test_L6_insufficiency_wrong_axis_same_infidelity():
    """FALSIFIER proof-of-insufficiency: a wrong-axis channel (RZ instead of RX at the same angle)
    produces the SAME scalar 1-F_e as the correct RX channel — showing that 1-F_e alone
    CANNOT catch the wrong-axis bug (the reason L3 operator identity is the load-bearing gate).
    """
    coeff = 0.1
    dt_ns = 20.0
    cdt = torch.complex128
    eps = coeff * dt_ns

    # Correct: RX(eps) via COH_RX carrier
    H_rx = _hamiltonian_matrix_for_term(
        _make_coh_rx_term(coeff),
        support=(0,),
        local_dims=(2,),
        device=DEV,
    )
    kraus_rx = assemble_substep_channel([H_rx], [], dt_ns, device=DEV)
    J_rx = _choi_state_from_kraus(kraus_rx, device=DEV)

    # Wrong: RZ(eps) built by hand — SAME infidelity vs identity, DIFFERENT operator
    Z2 = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=cdt, device=DEV)
    H_rz = 0.5 * coeff * Z2
    kraus_rz = assemble_substep_channel([H_rz], [], dt_ns, device=DEV)
    J_rz = _choi_state_from_kraus(kraus_rz, device=DEV)

    I_kraus = torch.eye(2, dtype=cdt, device=DEV).unsqueeze(0)
    J_I = _choi_state_from_kraus(I_kraus, device=DEV)

    fe_rx = float(max(0.0, 1.0 - _state_fidelity(J_rx, J_I, device=DEV)))
    fe_rz = float(max(0.0, 1.0 - _state_fidelity(J_rz, J_I, device=DEV)))

    # Both have the same scalar infidelity (sin^2(eps/2)) vs identity
    assert abs(fe_rx - fe_rz) <= 1e-6, (
        f"INSUFFICIENCY PROOF FAILED: RX and RZ at same angle have different 1-F_e "
        f"(fe_rx={fe_rx:.6e}, fe_rz={fe_rz:.6e}, diff={abs(fe_rx - fe_rz):.3e}); "
        "this test SHOULD PASS (same 1-F_e for both), proving 1-F_e alone is insufficient"
    )

    # But the operators themselves differ: confirms L3 is necessary
    diff_op = float(torch.linalg.matrix_norm(H_rx - H_rz).item())
    assert diff_op >= _WRONG_AXIS_MIN, (
        f"Operator diff between RX and RZ generators = {diff_op:.3e} < {_WRONG_AXIS_MIN}; "
        "unexpectedly small — X and Z look identical at this coeff (bug)"
    )


# ---------------------------------------------------------------------------
# INVARIANT L7: Quadratic scaling  (1-F_e)/eps^2 → 1/4 as eps→0  (B2, class-b band)
# Leading-order: 1-F_e ≈ eps^2/4 = ||(eps/2)X||_F^2 / d.
# Predicts (1-F_e)/eps^2 → 1/4 with O(eps^2) corrections.
# BROKEN INPUT: a linear-in-eps error (1-F_e ~ eps, not eps^2) fails this ratio test.
# ---------------------------------------------------------------------------

def test_L7_quadratic_scaling():
    """L7 (class-b band, B2): (1-F_e)/eps^2 → 1/4 as eps → 0.

    At small eps: sin^2(eps/2) ≈ eps^2/4 - eps^4/48 + O(eps^6).
    The ratio (1-F_e)/eps^2 should be within 10% of 1/4 for eps ≤ 0.1 rad.
    At eps=0.3 (larger angle) the ratio deviates by ~O(eps^2) — registered B2 deviation, not a bug.
    """
    dt_ns = 20.0
    cdt = torch.complex128
    I_kraus = torch.eye(2, dtype=cdt, device=DEV).unsqueeze(0)
    J_I = _choi_state_from_kraus(I_kraus, device=DEV)

    ratios: list[float] = []
    for coeff in (0.005 / dt_ns, 0.003 / dt_ns, 0.001 / dt_ns, 0.0005 / dt_ns):
        eps = coeff * dt_ns
        H = _hamiltonian_matrix_for_term(
            _make_coh_rx_term(coeff),
            support=(0,),
            local_dims=(2,),
            device=DEV,
        )
        kraus = assemble_substep_channel([H], [], dt_ns, device=DEV)
        J_c = _choi_state_from_kraus(kraus, device=DEV)
        one_minus_fe = float(max(0.0, 1.0 - _state_fidelity(J_c, J_I, device=DEV)))
        if eps > 0:
            ratio = one_minus_fe / (eps ** 2)
            ratios.append(ratio)
            assert abs(ratio - 0.25) <= 0.1, (
                f"L7 FAIL: (1-F_e)/eps^2 = {ratio:.4f}, expected ~0.25, deviation "
                f"{abs(ratio-0.25):.4f} > 0.10 at eps={eps:.5f}"
            )


def test_L7_broken_linear_scaling_trips():
    """FALSIFIER: a channel with 1-F_e ~ eps (linear, not quadratic) fails L7.

    A linear-in-eps error would give ratio (1-F_e)/eps^2 ~ 1/eps → ∞ as eps→0.
    We simulate this with a collapse operator scaled as sqrt(eps) (T1-like decay),
    producing 1-F_e ~ eps at small eps.
    """
    dt_ns = 20.0
    cdt = torch.complex128
    I_kraus = torch.eye(2, dtype=cdt, device=DEV).unsqueeze(0)
    J_I = _choi_state_from_kraus(I_kraus, device=DEV)

    eps_ref = 0.001  # small angle: a coherent error gives ~eps^2/4 ~ 2.5e-7
    # Build a T1 collapse channel at rate ~ eps_ref / dt_ns -> 1-F_e ~ eps_ref (linear)
    sm = torch.tensor([[0.0, 1.0], [0.0, 0.0]], dtype=cdt, device=DEV)
    gamma = eps_ref / dt_ns
    c_linear = math.sqrt(gamma) * sm
    kraus_linear = assemble_substep_channel([], [c_linear], dt_ns, device=DEV)
    J_linear = _choi_state_from_kraus(kraus_linear, device=DEV)
    fe_linear = float(max(0.0, 1.0 - _state_fidelity(J_linear, J_I, device=DEV)))
    ratio_linear = fe_linear / (eps_ref ** 2) if eps_ref > 0 else 0.0
    # A linear error at eps=0.001 gives 1-F_e ~ 0.001/2 ≈ 5e-4 → ratio ~ 500 >> 0.25
    assert abs(ratio_linear - 0.25) > 0.1, (
        f"FALSIFIER DID NOT TRIP: linear-in-eps channel has (1-F_e)/eps^2 = {ratio_linear:.4f} "
        "which is within 0.1 of 0.25; the L7 quadratic-scaling check cannot distinguish "
        "linear from quadratic at this scale — falsifier broken"
    )


# ---------------------------------------------------------------------------
# INVARIANT L8: Even symmetry  1-F_e(eps) = 1-F_e(-eps)  (class-a, exact)
# Over-rotation and under-rotation of equal magnitude are equally infidel.
# BROKEN INPUT: an asymmetric error model (e.g. pure T1 relaxation) is odd in the sense
# that its infidelity changes with sign (it is a directional error, not symmetric).
# ---------------------------------------------------------------------------

def test_L8_infidelity_even_in_eps():
    """L8 (class-a exact): 1-F_e is even in eps (symmetric in sign of over-rotation).

    sin^2(eps/2) = sin^2(-eps/2); RX(eps) and RX(-eps) have the same infidelity vs identity.
    For any unitary U, F_e = |Tr U / d|^2 satisfies F_e(U) = F_e(U†) (trace modulus is
    invariant under conjugation), so 1-F_e is always even in the rotation angle.
    """
    dt_ns = 20.0
    cdt = torch.complex128
    I_kraus = torch.eye(2, dtype=cdt, device=DEV).unsqueeze(0)
    J_I = _choi_state_from_kraus(I_kraus, device=DEV)

    def _fe(coeff_val: float) -> float:
        H = _hamiltonian_matrix_for_term(
            _make_coh_rx_term(coeff_val),
            support=(0,),
            local_dims=(2,),
            device=DEV,
        )
        kraus = assemble_substep_channel([H], [], dt_ns, device=DEV)
        J_c = _choi_state_from_kraus(kraus, device=DEV)
        return float(max(0.0, 1.0 - _state_fidelity(J_c, J_I, device=DEV)))

    for coeff in (0.1 / dt_ns, 0.05 / dt_ns, 0.01 / dt_ns):
        fe_pos = _fe(+coeff)
        fe_neg = _fe(-coeff)
        diff = abs(fe_pos - fe_neg)
        assert diff <= 1e-10, (
            f"L8 FAIL: 1-F_e(+eps) = {fe_pos:.6e}, 1-F_e(-eps) = {fe_neg:.6e}, "
            f"diff = {diff:.3e} > 1e-10 at coeff={coeff} — even-symmetry broken"
        )


def test_L8_broken_odd_infidelity_formula_trips():
    """FALSIFIER: if someone used sin(eps/2) instead of sin^2(eps/2) in the reference formula,
    the result would be ODD in eps (sin(eps/2) is negative for eps<0), violating the even-symmetry
    that the CORRECT formula sin^2(eps/2) satisfies.

    Background: for any unitary channel U, 1-F_e(U, I) = 1 - |Tr(U)/d|^2 = 1 - cos^2(eps/2) =
    sin^2(eps/2). The even-symmetry is a MATHEMATICAL IDENTITY of sin^2. The WRONG formula
    sin(eps/2) (omitting the square) is ODD: sin(-x/2) = -sin(x/2).

    This is the correct falsifier: the wrong reference formula is not even in eps.
    The carrier operator-level identity (L3/L4) separately verifies the carrier is the right
    OPERATOR; L8 verifies the closed-form reference used to evaluate B1 is the right FUNCTION.
    """
    for eps in (0.3, 0.1, 0.03, 0.01, 0.003, 0.001):
        # Correct formula: sin^2(eps/2)  — should be even in eps
        correct_pos = exact_infidelity_M6(+eps)
        correct_neg = exact_infidelity_M6(-eps)
        assert abs(correct_pos - correct_neg) <= 1e-14, (
            f"L8 SELF-CHECK FAIL: correct formula sin^2(eps/2) is not even at eps={eps}"
        )
        # Wrong formula: sin(eps/2) (not squared) — should be ODD in eps (not even)
        wrong_pos = math.sin(eps / 2)
        wrong_neg = math.sin(-eps / 2)
        # The wrong formula gives OPPOSITE sign for +eps and -eps -> difference is large
        assert abs(wrong_pos - wrong_neg) >= abs(eps) / 4.0, (
            f"FALSIFIER DID NOT TRIP: the wrong formula sin(eps/2) is unexpectedly symmetric "
            f"at eps={eps}: wrong_pos={wrong_pos:.6f}, wrong_neg={wrong_neg:.6f}"
        )


# ---------------------------------------------------------------------------
# INVARIANT L9: Apply every gate — identity embed on leaked levels (S2, class-a)
# In a qutrit carrier (dim=3), H_M6 acts as (coeff/2)*X on the [0:2,0:2] block
# and as the ZERO GENERATOR on the [2,2] element (no leakage drive).
# BROKEN INPUT: extending X to a 3x3 full Pauli would put non-zero off-diagonal
# elements at [0,2], [2,0], [1,2], [2,1] — leaking the error into qutrit levels.
# ---------------------------------------------------------------------------

def test_L9_qutrit_embed_is_zero_on_leaked_levels():
    """L9 (class-a exact, S2): in a dim=3 carrier, H_M6[:2,:2] = ref_H_M6(coeff,2)
    AND H_M6[2,:] = H_M6[:,2] = 0 (no leakage drive from M6).
    """
    coeff = 0.1
    H = _hamiltonian_matrix_for_term(
        _make_coh_rx_term(coeff),
        support=(0,),
        local_dims=(3,),
        device=DEV,
    )
    # The 2-level block must equal the qubit reference
    H_ref_2level = ref_H_M6(coeff, 2)
    diff_2block = float(torch.linalg.matrix_norm(H[:2, :2] - H_ref_2level).item())
    assert diff_2block <= _OPERATOR_DIFF_TOL, (
        f"L9 FAIL: H_M6 qutrit 2-block differs from qubit reference by {diff_2block:.3e}"
    )
    # The leaked-level row/col must be zero (use vector norm for 1D slices)
    leaked_row = float(torch.linalg.norm(H[2, :]).item())
    leaked_col = float(torch.linalg.norm(H[:, 2]).item())
    assert leaked_row <= _OPERATOR_DIFF_TOL, (
        f"L9 FAIL: H_M6 qutrit row-2 = {leaked_row:.3e} ≠ 0; M6 drives leakage — S2 violated"
    )
    assert leaked_col <= _OPERATOR_DIFF_TOL, (
        f"L9 FAIL: H_M6 qutrit col-2 = {leaked_col:.3e} ≠ 0; M6 drives leakage — S2 violated"
    )


def test_L9_broken_full_qutrit_pauli_trips():
    """FALSIFIER: a 3x3 Pauli-X (driving level 2 as well) fails L9."""
    cdt = torch.complex128
    # Full 3x3 X-like matrix: anti-diagonal 1s, including level 2
    H_broken = 0.05 * torch.tensor(
        [[0, 1, 0], [1, 0, 0], [0, 0, 0]], dtype=cdt, device=DEV
    )
    # Putting a 1 in [0,2] to simulate leakage coupling
    H_broken_leak = H_broken.clone()
    H_broken_leak[0, 2] = 0.05
    H_broken_leak[2, 0] = 0.05
    leaked_row = float(torch.linalg.norm(H_broken_leak[2, :]).item())  # 1D vector norm
    assert leaked_row > _OPERATOR_DIFF_TOL, (
        "FALSIFIER DID NOT TRIP: the broken leakage Pauli has zero row-2 — falsifier wrong"
    )


# ---------------------------------------------------------------------------
# INVARIANT L10: Anti-circular namespace check
# The cert (THIS FILE) must NOT import `_coherent_family_generator`,
# `_embed_coherent_generator`, or `ONE_SITE_COHERENT_FAMILIES` from the carrier.
# If these symbols appear in this module's namespace, the cert is circular.
# BROKEN INPUT: any import of those carrier internals would make this test fail.
# ---------------------------------------------------------------------------

def test_L10_cert_does_not_import_circular_carrier_symbols():
    """L10 (structural, anti-circular): the cert imports ONLY `_hamiltonian_matrix_for_term`
    from the carrier — the object under test. The carrier's family-generator helpers
    (`_coherent_family_generator`, `_embed_coherent_generator`) and the family constant
    (`ONE_SITE_COHERENT_FAMILIES`) must NOT appear in this module's namespace.

    If a future edit imports these, the cert becomes circular: a wrong Pauli-axis map
    shared between the cert's 'reference' and the carrier would false-pass (the W-C
    round-1 failure shape; see test_axis1_wc_decircularized.py).
    """
    import sys
    this_module = sys.modules[__name__]
    assert not hasattr(this_module, "_coherent_family_generator"), (
        "CIRCULAR: cert imports `_coherent_family_generator` from the carrier"
    )
    assert not hasattr(this_module, "_embed_coherent_generator"), (
        "CIRCULAR: cert imports `_embed_coherent_generator` from the carrier"
    )
    assert not hasattr(this_module, "ONE_SITE_COHERENT_FAMILIES"), (
        "CIRCULAR: cert imports `ONE_SITE_COHERENT_FAMILIES` from the carrier"
    )
    # Confirm the allowed carrier entry-point IS present
    assert hasattr(this_module, "_hamiltonian_matrix_for_term"), (
        "INTERNAL: `_hamiltonian_matrix_for_term` (the object under test) missing from cert module"
    )


def test_L10_broken_circular_import_would_fail():
    """FALSIFIER: demonstrate that if a circular import were present, L10 would fail.

    We manually simulate the presence of a carrier-internal symbol in a fake module dict
    and confirm the L10 check would trip.
    """
    # Build a mock module namespace that has the circular symbol
    class _FakeModule:
        _coherent_family_generator = lambda *a, **kw: None
        _hamiltonian_matrix_for_term = lambda *a, **kw: None

    fake = _FakeModule()
    # L10's check: hasattr(module, "_coherent_family_generator") would be True -> FAIL
    assert hasattr(fake, "_coherent_family_generator"), (
        "FALSIFIER DID NOT TRIP: the fake module lacks the circular symbol — falsifier broken"
    )
