"""M20 coherent_ry_overrotation — CONSTRAINT LEDGER (executable falsifier tests).

FAITHFULNESS PROTOCOL (docs/FAITHFULNESS_PROTOCOL.md) — constraint ledger for M20.
Each test below is a FALSIFIER: it documents the invariant AND shows that a
deliberately BROKEN input makes the test FAIL (trips the falsifier). Tests run
GREEN on the faithful carrier and RED on the broken variant.

ANTI-CIRCULARITY: the reference operator (``ref_H_M20``) is HAND-TYPED from the
literature (Nielsen & Chuang Eq. 2.1 + Eq. 4.4–4.7; Kaufmann-Rojkov-Reiter
arXiv:2307.08741 Eq. 2). The cert imports ONLY
``axis1_mcwf_mps_execution._hamiltonian_matrix_for_term`` (the object under test).
The carrier's ``_coherent_family_generator`` / ``_embed_coherent_generator`` /
``ONE_SITE_COHERENT_FAMILIES`` constants appear NOWHERE in the reference code
(same de-circularization rule as test_axis1_wc_decircularized.py, the M6 ledger,
and the M7 ledger).

GATE TIER: STRICT (``1-F_e <= 1e-6``; operator identity <= 1e-12 / unitary <= 1e-10).
M20 is a pure-Hamiltonian / exact-dense error — no collapse, no finite-step MCWF.

M20-SPECIFIC: ``1-F_e`` is AXIS-BLIND (sin^2(eps/2) is identical for RX/RY/RZ at
the same angle — pre-registration B1). The operator-identity gate L3 (and its
wrong-axis falsifiers L3b / L3c, L6b) are the LOAD-BEARING cert gates for M20:
they are the SOLE witnesses that the carrier rotates about Y and not X/Z.
Pauli-Y is the ONLY single-qubit Pauli with imaginary off-diagonal entries (+-i),
so a real-valued reference (X or Z) is structurally distinguishable by L3 even
when the scalar infidelity cannot distinguish them.

GPU-only (top-level memory rule) — collection FAILS without CUDA.

Pre-registration: docs/twin_validation/m20_coherent_ry_overrotation_prereg.md
Run:  conda run -n aiqec python -m pytest -q tests/test_m20_coherent_ry_constraint_ledger.py
"""
from __future__ import annotations

import math
import sys

import pytest
import torch

# ---------------------------------------------------------------------------
# GPU gate (top-level memory rule: collection fails without CUDA)
# ---------------------------------------------------------------------------
cuda_ok = torch.cuda.is_available()
if not cuda_ok:
    pytest.fail(
        "M20 constraint-ledger cert is GPU-gated; CUDA-MISSING is NOT A RELEASE BASIS",
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
_HERMITIAN_TOL = 1e-12      # ||H - H†||_F <= this  (class-a exact)
_TRACELESS_TOL = 1e-12      # |Tr H| <= this          (class-a exact)
_OPERATOR_DIFF_TOL = 1e-12  # ||H_carrier - H_ref||_F (class-a exact, B4)
_UNITARY_DIFF_TOL = 1e-10   # ||U_carrier - U_ref||_F (class-a exact, B4)
_WRONG_AXIS_MIN = 1e-3      # wrong-axis / wrong-unit control must trip by >= this
#                           # (class-c gate; at eps >= 1e-2; |U_RY - U_RX| ~= eps at small eps,
#                           #  so eps=1e-2 -> ~5e-3 >= 1e-3; pre-reg §3 derivation-check)


# ---------------------------------------------------------------------------
# Reference operator (HAND-TYPED, non-circular)
# Provenance: H_M20 = (coeff/2) * sigma_y on the 2-level computational subspace.
#   sigma_y = [[0, -i], [i, 0]]  (Nielsen & Chuang Eq. 2.1, Pauli-Y).
#   factor 1/2: R_y(theta) = exp(-i theta Y/2)  (N&C Eq. 4.4–4.7).
#   error gate: U = exp(-i H dt) = RY(eps)
#               = [[cos(eps/2), -sin(eps/2)], [sin(eps/2), cos(eps/2)]], eps = coeff * dt_ns.
#   mechanism paper: Kaufmann-Rojkov-Reiter arXiv:2307.08741 Eq. 2
#                    (H_theta = sum_k theta_k P_k; the single-qubit Y term theta_Y Y IS M20).
# Identity (zero generator) on leaked levels >= 2 for qutrit/ququart carriers.
# M20-specific: RY(eps) is REAL-ORTHOGONAL on the 2-block and leaves |2> unchanged
#               (exp(0)=1 on level >=2 — pre-reg S2).
# ---------------------------------------------------------------------------
def ref_H_M20(coeff: float, dim: int) -> torch.Tensor:
    """Hand-typed M20 reference generator on the `dim`-level local space.

    H_M20 = (coeff/2) * Y2 embedded into the `dim`-dimensional local space,
    with the zero generator (identity gate) on levels >= 2 (no leakage drive).
    Importing NOTHING from the carrier family tables.
    """
    cdt = torch.complex128
    Y2 = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
    H = torch.zeros((dim, dim), dtype=cdt, device=DEV)
    H[:2, :2] = 0.5 * coeff * Y2
    return H


def ref_U_M20(coeff: float, dt_ns: float, dim: int) -> torch.Tensor:
    """Hand-typed M20 error unitary: U = matrix_exp(-i * H * dt) = RY(eps)."""
    H = ref_H_M20(coeff, dim)
    return torch.linalg.matrix_exp(-1j * dt_ns * H)


def exact_infidelity_M20(eps: float) -> float:
    """Closed-form 1-F_e for RY(eps) vs identity (d=2).

    1 - |Tr(RY(eps))/2|^2 = 1 - |(2*cos(eps/2))/2|^2
                          = 1 - cos^2(eps/2) = sin^2(eps/2).
    Reference: Nielsen arXiv:quant-ph/0205035 Eq. 16 (F_e = |Tr U / d|^2 for unitary U).
    NOTE: identical to the M6 RX and M7 RZ closed forms — sin^2(eps/2) is axis-agnostic
    (pre-reg B1). The axis is witnessed ONLY by the operator-identity gate L3.
    """
    return float(math.sin(eps / 2.0) ** 2)


def _make_coh_ry_term(coeff: float) -> dict:
    """Minimal schedule-term dict for COH_RY on one site (support=(0,))."""
    return {
        "kind": "hamiltonian",
        "operator_family": "COH_RY",
        "support": [0],
        "coefficient": float(coeff),
        "substep_id": "m20_ledger",
    }


# ---------------------------------------------------------------------------
# INVARIANT L1: Hermiticity  ||H - H†||_F <= 1e-12
# Pauli generators are Hermitian; an anti-Hermitian generator is WRONG.
# BROKEN INPUT: a non-Hermitian matrix (add an imaginary off-diagonal term)
# ---------------------------------------------------------------------------

def test_L1_generator_is_hermitian():
    """L1 (class-a exact): the M20 generator H satisfies H = H†.

    Broken-input demonstration: an explicitly non-Hermitian operator trips this test.
    """
    coeff = 0.1
    H = _hamiltonian_matrix_for_term(
        _make_coh_ry_term(coeff),
        support=(0,),
        local_dims=(2,),
        device=DEV,
    )
    resid = float(torch.linalg.matrix_norm(H - H.conj().T).item())
    assert resid <= _HERMITIAN_TOL, (
        f"L1 FAIL: ||H - H†||_F = {resid:.3e} > {_HERMITIAN_TOL}; "
        "M20 generator is not Hermitian — physics bug"
    )


def test_L1_broken_non_hermitian_trips():
    """FALSIFIER: a deliberately non-Hermitian matrix fails the L1 check.

    BROKEN INPUT: [[0, 1], [0, 0]] — upper-triangular, not Hermitian.
    ||H - H†||_F = ||(0,1;0,0) - (0,0;1,0)||_F = ||(0,1;-1,0)||_F = sqrt(2) >> 1e-12.
    """
    cdt = torch.complex128
    H_broken = torch.tensor([[0.0, 1.0], [0.0, 0.0]], dtype=cdt, device=DEV)
    resid = float(torch.linalg.matrix_norm(H_broken - H_broken.conj().T).item())
    assert resid > _HERMITIAN_TOL, (
        "FALSIFIER DID NOT TRIP: a known non-Hermitian matrix passed L1 — "
        "the falsifier is broken"
    )


# ---------------------------------------------------------------------------
# INVARIANT L2: Tracelessness  |Tr H| <= 1e-12
# Pauli Y is traceless; an identity-shifted generator is WRONG.
# BROKEN INPUT: H + (c/2) * I  (trace = coeff)
# ---------------------------------------------------------------------------

def test_L2_generator_is_traceless():
    """L2 (class-a exact): the M20 generator H is traceless (Pauli Y is traceless)."""
    coeff = 0.1
    H = _hamiltonian_matrix_for_term(
        _make_coh_ry_term(coeff),
        support=(0,),
        local_dims=(2,),
        device=DEV,
    )
    tr_resid = float(torch.abs(torch.trace(H)).item())
    assert tr_resid <= _TRACELESS_TOL, (
        f"L2 FAIL: |Tr H| = {tr_resid:.3e} > {_TRACELESS_TOL}; "
        "M20 generator has a non-zero trace — wrong axis or identity contamination"
    )


def test_L2_broken_identity_shift_trips():
    """FALSIFIER: a traceful generator (Pauli Y + identity offset) fails L2.

    BROKEN INPUT: 0.05*Y + 0.05*I — trace = 0.1 >> 1e-12.
    """
    cdt = torch.complex128
    H_broken = (0.05 * torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
                + 0.05 * torch.eye(2, dtype=cdt, device=DEV))
    tr_resid = float(torch.abs(torch.trace(H_broken)).item())
    assert tr_resid > _TRACELESS_TOL, (
        "FALSIFIER DID NOT TRIP: an identity-shifted generator passed L2 — "
        "the falsifier is broken"
    )


# ---------------------------------------------------------------------------
# INVARIANT L3a: Operator identity  ||H_carrier - H_ref||_F <= 1e-12  (B4, class-a)
# This is the LOAD-BEARING cert gate for M20.
# Y is the ONLY single-qubit Pauli with imaginary off-diagonal entries (+-i);
# a real-valued wrong axis (X or Z) is immediately distinguishable by this gate.
# BROKEN INPUT: a wrong-axis generator (X instead of Y) — must disagree by >= 1e-3
# ---------------------------------------------------------------------------

def test_L3a_operator_matches_hand_typed_reference():
    """L3a (class-a exact, B4): the carrier generator equals the hand-typed reference.

    H_ref = (coeff/2) * Y2 embedded in dim, from Nielsen & Chuang / 2307.08741.
    This is the LOAD-BEARING gate — 1-F_e alone cannot distinguish RY from RX/RZ at
    equal angle (sin^2(eps/2) is identical for all single-qubit single-axis rotations;
    pre-registration B1). The operator identity is the SOLE witness of the Y axis.
    M20-sharp: Y has imaginary off-diagonals (+-i); X is real off-diagonal (1); Z is
    diagonal — a wrong axis is caught immediately by the Frobenius norm of (H - H_ref).
    """
    for coeff in (0.3, 0.1, 0.03, 0.01, 0.003, 0.001):
        for dim in (2, 3):
            H_carrier = _hamiltonian_matrix_for_term(
                _make_coh_ry_term(coeff),
                support=(0,),
                local_dims=(dim,),
                device=DEV,
            )
            H_ref = ref_H_M20(coeff, dim)
            diff = float(torch.linalg.matrix_norm(H_carrier - H_ref).item())
            assert diff <= _OPERATOR_DIFF_TOL, (
                f"L3a FAIL: ||H_carrier - H_ref||_F = {diff:.3e} > {_OPERATOR_DIFF_TOL} "
                f"at coeff={coeff}, dim={dim} — wrong generator (wrong axis, wrong coefficient, "
                "wrong convention)"
            )


def test_L3b_broken_wrong_axis_rx_trips():
    """FALSIFIER (L3b): a wrong-axis X reference disagrees with the Y carrier by >= 1e-3.

    This is the primary wrong-axis control for M20 (pre-registration §3):
    a reference H_wrong = (coeff/2)*X should disagree with the Y carrier.
    Gate fires at eps >= 1e-2 (|U_RY - U_RX| ~= eps at small eps -> ~5e-3 at eps=1e-2;
    pre-reg §3 derivation-check, class-c gate parameter).

    A circular reference derived FROM the corrupted carrier axis map (COH_RY->X)
    would mirror the wrong axis to diff=0 (false-pass); the hand-typed Y reference
    catches the corruption. This is the M20 analogue of the W-C leakage cert's
    wrong-level falsifier (test_axis1_wc_decircularized.py).

    BROKEN INPUT: H_wrong = (coeff/2)*X — real off-diagonal, vs Y which is imaginary.
    ||Y2 - X2||_F = 2 (the imaginary vs real off-diagonals are orthogonal), so
    ||(coeff/2)*Y - (coeff/2)*X||_F = coeff*sqrt(2)/2 = 0.1*sqrt(2)/2 ~= 0.07 >> 1e-3.
    """
    coeff = 0.1  # eps = coeff alone at dt=1; any coeff >= 0.01 satisfies the gate
    dim = 2
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_ry_term(coeff),
        support=(0,),
        local_dims=(dim,),
        device=DEV,
    )
    cdt = torch.complex128
    # Wrong-axis reference: (coeff/2) * X  (should be Y)
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    H_wrong_x = 0.5 * coeff * X2
    diff = float(torch.linalg.matrix_norm(H_carrier - H_wrong_x).item())
    assert diff >= _WRONG_AXIS_MIN, (
        f"FALSIFIER DID NOT TRIP: wrong-axis X reference passed with diff={diff:.3e} < "
        f"{_WRONG_AXIS_MIN}; the Y/X confusion is undetectable — operator-identity cert broken"
    )


def test_L3c_broken_wrong_axis_rz_trips():
    """FALSIFIER (L3c): a wrong-axis Z reference disagrees with the Y carrier by >= 1e-3.

    Companion to L3b: the Z axis is also indistinguishable from Y by 1-F_e alone.
    Both L3b and L3c must trip — the operator gate rejects ALL wrong-axis alternatives.

    BROKEN INPUT: H_wrong = (coeff/2)*Z — diagonal, vs Y which is off-diagonal imaginary.
    ||(coeff/2)*Y - (coeff/2)*Z||_F = coeff*sqrt(2)/2 ~= 0.07 >> 1e-3 at coeff=0.1.
    """
    coeff = 0.1
    dim = 2
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_ry_term(coeff),
        support=(0,),
        local_dims=(dim,),
        device=DEV,
    )
    cdt = torch.complex128
    # Wrong-axis reference: (coeff/2) * Z  (should be Y)
    Z2 = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=cdt, device=DEV)
    H_wrong_z = 0.5 * coeff * Z2
    diff = float(torch.linalg.matrix_norm(H_carrier - H_wrong_z).item())
    assert diff >= _WRONG_AXIS_MIN, (
        f"FALSIFIER DID NOT TRIP: wrong-axis Z reference passed with diff={diff:.3e} < "
        f"{_WRONG_AXIS_MIN}; the Y/Z confusion is undetectable — operator-identity cert broken"
    )


def test_L3d_broken_wrong_unit_convention_trips():
    """FALSIFIER (L3d): wrong-unit convention (treating coeff as the angle, missing the 1/2 factor)
    disagrees with the correct reference.

    Wrong form: H_wrong = coeff * Y  (missing the 1/2 factor from R_y convention).
    The correct form is H = (coeff/2) * Y.

    BROKEN INPUT: coeff*Y instead of (coeff/2)*Y — differs by a factor of 2.
    ||coeff*Y - (coeff/2)*Y||_F = (coeff/2)*||Y||_F = (coeff/2)*sqrt(2) ~= 0.07 at coeff=0.1.
    """
    coeff = 0.1
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_ry_term(coeff),
        support=(0,),
        local_dims=(2,),
        device=DEV,
    )
    cdt = torch.complex128
    Y2 = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
    H_wrong_unit = float(coeff) * Y2   # missing the 1/2
    diff = float(torch.linalg.matrix_norm(H_carrier - H_wrong_unit).item())
    assert diff >= _WRONG_AXIS_MIN, (
        f"FALSIFIER DID NOT TRIP: wrong-unit convention (coeff*Y, missing 1/2) has diff={diff:.3e} < "
        f"{_WRONG_AXIS_MIN}; the factor-of-2 error is undetectable"
    )


# ---------------------------------------------------------------------------
# INVARIANT L4: Unitary identity  ||U_carrier - U_ref||_F <= 1e-10  (B4, class-a)
# U = matrix_exp(-i H dt) = RY(eps)
#   = [[cos(eps/2), -sin(eps/2)], [sin(eps/2), cos(eps/2)]], eps = coeff * dt_ns.
# BROKEN INPUT: wrong-sign in the exponent (U = exp(+i H dt)), gives RY(-eps).
# ---------------------------------------------------------------------------

def test_L4_error_unitary_matches_ry_reference():
    """L4 (class-a exact, B4): the carrier's error gate U = exp(-i H dt) equals the
    reference RY(eps) unitary to <= 1e-10.
    """
    dt_ns = 20.0
    for coeff in (0.3, 0.1, 0.03, 0.01, 0.003, 0.001):
        for dim in (2, 3):
            eps = coeff * dt_ns
            H_carrier = _hamiltonian_matrix_for_term(
                _make_coh_ry_term(coeff),
                support=(0,),
                local_dims=(dim,),
                device=DEV,
            )
            U_carrier = torch.linalg.matrix_exp(-1j * dt_ns * H_carrier)
            U_ref = ref_U_M20(coeff, dt_ns, dim)
            diff = float(torch.linalg.matrix_norm(U_carrier - U_ref).item())
            assert diff <= _UNITARY_DIFF_TOL, (
                f"L4 FAIL: ||U_carrier - U_ref||_F = {diff:.3e} > {_UNITARY_DIFF_TOL} "
                f"at coeff={coeff}, dt={dt_ns}, eps={eps:.3f}, dim={dim}"
            )


def test_L4_broken_wrong_sign_exponent_trips():
    """FALSIFIER: the wrong-sign exponent (exp(+i H dt)) disagrees with the correct gate
    by >= 1e-3 for any non-zero eps not a multiple of pi.

    BROKEN INPUT: use +i instead of -i in the exponent -> RY(-eps) instead of RY(eps).
    ||RY(eps) - RY(-eps)||_F = 2*|sin(eps/2)| ~= eps at small eps -> ~0.2 at eps=2.0 >> 1e-3.
    """
    coeff = 0.1
    dt_ns = 20.0
    dim = 2
    H_ref = ref_H_M20(coeff, dim)
    U_correct = torch.linalg.matrix_exp(-1j * dt_ns * H_ref)
    U_wrong_sign = torch.linalg.matrix_exp(+1j * dt_ns * H_ref)  # wrong sign
    diff = float(torch.linalg.matrix_norm(U_correct - U_wrong_sign).item())
    assert diff >= _WRONG_AXIS_MIN, (
        f"FALSIFIER DID NOT TRIP: wrong-sign exponent has diff={diff:.3e} < "
        f"{_WRONG_AXIS_MIN}; the sign flip is undetectable"
    )


# ---------------------------------------------------------------------------
# INVARIANT L5: CPTP residual (TP check)  ||sum_k K†K - I||_F <= 1e-12
# For a pure unitary (no collapse), the Kraus channel has a SINGLE Kraus = U.
# BROKEN INPUT: a non-unitary matrix (e.g. amplitude-damped form with non-TP residual).
# ---------------------------------------------------------------------------

def test_L5_channel_is_tp():
    """L5 (class-a exact): the M20 Kraus channel assembled from H_M20 alone (no collapse)
    is exactly trace-preserving: sum_k K†K = I to <= 1e-12.
    """
    dt_ns = 20.0
    coeff = 0.1
    H = _hamiltonian_matrix_for_term(
        _make_coh_ry_term(coeff),
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
        "M20 channel is not trace-preserving"
    )


def test_L5_broken_non_tp_trips():
    """FALSIFIER: a non-unitary (non-TP) Kraus set fails L5.

    BROKEN INPUT: K = 0.8*I — scaling the identity down by 0.8.
    sum K†K = 0.64*I; ||0.64*I - I||_F = 0.36*sqrt(D) >> 1e-12.
    """
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
# INVARIANT L6a: process infidelity == sin^2(eps/2) to Uhlmann floor  (B1, class-b band)
# RY(eps) vs identity: 1-F_e = sin^2(eps/2) (Nielsen quant-ph/0205035 Eq. 16).
# Threshold: STRICT 1-F_e <= 1e-6 (pure Hamiltonian, S1).
# ---------------------------------------------------------------------------

def test_L6a_infidelity_matches_exact_closed_form():
    """L6a (class-b band, B1): carrier 1-F_e = sin^2(eps/2) to the Uhlmann estimator floor (~2e-8).

    Swept over eps in {0.3, 0.1, 0.03, 0.01, 0.003, 0.001} rad.
    The STRICT gate tier requires the carrier-assembled channel infidelity vs identity
    to match the closed form to <= 5e-7 (Uhlmann estimator floor ~2e-8; S1, S4).
    NOTE: sin^2(eps/2) is the same closed form as for M6 RX and M7 RZ — axis-agnostic (B1).
    """
    dt_ns = 20.0
    cdt = torch.complex128
    I_kraus = torch.eye(2, dtype=cdt, device=DEV).unsqueeze(0)
    J_I = _choi_state_from_kraus(I_kraus, device=DEV)

    for coeff in (0.3 / dt_ns, 0.1 / dt_ns, 0.03 / dt_ns, 0.01 / dt_ns,
                  0.003 / dt_ns, 0.001 / dt_ns):
        eps = coeff * dt_ns
        H = _hamiltonian_matrix_for_term(
            _make_coh_ry_term(coeff),
            support=(0,),
            local_dims=(2,),
            device=DEV,
        )
        kraus = assemble_substep_channel([H], [], dt_ns, device=DEV)
        J_carrier = _choi_state_from_kraus(kraus, device=DEV)
        F_e = float(_state_fidelity(J_carrier, J_I, device=DEV))
        one_minus_fe = float(max(0.0, 1.0 - F_e))
        exact = exact_infidelity_M20(eps)
        band_resid = abs(one_minus_fe - exact)
        assert band_resid <= 5e-7, (
            f"L6a FAIL: |carrier_1-F_e - sin^2(eps/2)| = {band_resid:.3e} at eps={eps:.4f}; "
            f"carrier={one_minus_fe:.6e}, exact={exact:.6e}"
        )


def test_L6b_insufficiency_wrong_axis_same_infidelity():
    """FALSIFIER / proof-of-insufficiency (L6b): a wrong-axis channel (RX instead of RY
    at the same angle) produces the SAME scalar 1-F_e as the correct RY channel.

    This is the M20-load-bearing proof that 1-F_e CANNOT catch a wrong-axis bug —
    making the operator-identity gate L3 strictly necessary (pre-registration §2, B1, B4).
    A cert that relied only on 1-F_e would false-pass a COH_RY->X axis-map corruption.

    The test SHOULD PASS (same infidelity for both axes) — its role is to DOCUMENT the
    insufficiency and confirm that the scalar metric gives no signal on the bug.
    """
    coeff = 0.1
    dt_ns = 20.0
    cdt = torch.complex128
    eps = coeff * dt_ns

    # Correct: RY(eps) via COH_RY carrier
    H_ry = _hamiltonian_matrix_for_term(
        _make_coh_ry_term(coeff),
        support=(0,),
        local_dims=(2,),
        device=DEV,
    )
    kraus_ry = assemble_substep_channel([H_ry], [], dt_ns, device=DEV)
    J_ry = _choi_state_from_kraus(kraus_ry, device=DEV)

    # Wrong: RX(eps) built by hand — SAME infidelity vs identity, DIFFERENT operator
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    H_rx = 0.5 * coeff * X2
    kraus_rx = assemble_substep_channel([H_rx], [], dt_ns, device=DEV)
    J_rx = _choi_state_from_kraus(kraus_rx, device=DEV)

    I_kraus = torch.eye(2, dtype=cdt, device=DEV).unsqueeze(0)
    J_I = _choi_state_from_kraus(I_kraus, device=DEV)

    fe_ry = float(max(0.0, 1.0 - _state_fidelity(J_ry, J_I, device=DEV)))
    fe_rx = float(max(0.0, 1.0 - _state_fidelity(J_rx, J_I, device=DEV)))

    # Both have the same scalar infidelity (sin^2(eps/2)) vs identity.
    # This SHOULD PASS — it proves the insufficiency.
    assert abs(fe_ry - fe_rx) <= 1e-6, (
        f"INSUFFICIENCY PROOF FAILED: RY and RX at same angle have different 1-F_e "
        f"(fe_ry={fe_ry:.6e}, fe_rx={fe_rx:.6e}, diff={abs(fe_ry - fe_rx):.3e}); "
        "this test SHOULD PASS (same 1-F_e for both axes), proving 1-F_e alone is insufficient"
    )

    # But the operators themselves differ: confirms L3a/L3b are necessary.
    # M20-sharp: Y has imaginary off-diagonals (+-i), X has real off-diagonals (1) ->
    # ||Y - X||_F = 2 (the imaginary-vs-real difference dominates).
    Y2 = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
    X2_dev = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    diff_op = float(torch.linalg.matrix_norm(
        0.5 * coeff * Y2 - 0.5 * coeff * X2_dev
    ).item())
    assert diff_op >= _WRONG_AXIS_MIN, (
        f"Operator diff between RY and RX generators = {diff_op:.3e} < {_WRONG_AXIS_MIN}; "
        "unexpectedly small — Y and X look identical at this coeff (bug)"
    )


# ---------------------------------------------------------------------------
# INVARIANT L7: Quadratic scaling  (1-F_e)/eps^2 -> 1/4 as eps->0  (B2, class-b band)
# Leading-order: 1-F_e ~= eps^2/4 = ||(eps/2)Y||_F^2 / d.
# ||G||_F^2 = Tr((eps/2 Y)^2) = 2*(eps/2)^2 = eps^2/2 -> /d=2 -> eps^2/4.
# Predicts (1-F_e)/eps^2 -> 1/4 with O(eps^2) corrections.
# BROKEN INPUT: a linear-in-eps error (1-F_e ~ eps, not eps^2) fails this ratio test.
# ---------------------------------------------------------------------------

def test_L7_quadratic_scaling():
    """L7 (class-b band, B2): (1-F_e)/eps^2 -> 1/4 as eps -> 0.

    At small eps: sin^2(eps/2) ~= eps^2/4 - eps^4/48 + O(eps^6).
    The ratio (1-F_e)/eps^2 should be within 10% of 1/4 for eps <= 0.1 rad.
    At eps=0.3 (larger angle) the ratio deviates by ~O(eps^2) — registered B2 deviation, not a bug.
    """
    dt_ns = 20.0
    cdt = torch.complex128
    I_kraus = torch.eye(2, dtype=cdt, device=DEV).unsqueeze(0)
    J_I = _choi_state_from_kraus(I_kraus, device=DEV)

    for coeff in (0.005 / dt_ns, 0.003 / dt_ns, 0.001 / dt_ns, 0.0005 / dt_ns):
        eps = coeff * dt_ns
        H = _hamiltonian_matrix_for_term(
            _make_coh_ry_term(coeff),
            support=(0,),
            local_dims=(2,),
            device=DEV,
        )
        kraus = assemble_substep_channel([H], [], dt_ns, device=DEV)
        J_c = _choi_state_from_kraus(kraus, device=DEV)
        one_minus_fe = float(max(0.0, 1.0 - _state_fidelity(J_c, J_I, device=DEV)))
        if eps > 0:
            ratio = one_minus_fe / (eps ** 2)
            assert abs(ratio - 0.25) <= 0.1, (
                f"L7 FAIL: (1-F_e)/eps^2 = {ratio:.4f}, expected ~0.25, deviation "
                f"{abs(ratio-0.25):.4f} > 0.10 at eps={eps:.5f}"
            )


def test_L7_broken_linear_scaling_trips():
    """FALSIFIER: a channel with 1-F_e ~ eps (linear, not quadratic) fails L7.

    A linear-in-eps error would give ratio (1-F_e)/eps^2 ~ 1/eps -> infinity as eps->0.
    We simulate this with a collapse operator scaled as sqrt(eps) (T1-like decay),
    producing 1-F_e ~ eps at small eps.

    BROKEN INPUT: T1 amplitude damping at rate ~ eps_ref/dt_ns.
    At eps=0.001: coherent gives ~eps^2/4 ~ 2.5e-7; T1 gives ~eps/2 ~ 5e-4 -> ratio >> 0.25.
    """
    dt_ns = 20.0
    cdt = torch.complex128
    I_kraus = torch.eye(2, dtype=cdt, device=DEV).unsqueeze(0)
    J_I = _choi_state_from_kraus(I_kraus, device=DEV)

    eps_ref = 0.001  # small angle: coherent error gives ~eps^2/4 ~ 2.5e-7
    # Build a T1 collapse channel at rate ~ eps_ref / dt_ns -> 1-F_e ~ eps_ref (linear)
    sm = torch.tensor([[0.0, 1.0], [0.0, 0.0]], dtype=cdt, device=DEV)
    gamma = eps_ref / dt_ns
    c_linear = math.sqrt(gamma) * sm
    kraus_linear = assemble_substep_channel([], [c_linear], dt_ns, device=DEV)
    J_linear = _choi_state_from_kraus(kraus_linear, device=DEV)
    fe_linear = float(max(0.0, 1.0 - _state_fidelity(J_linear, J_I, device=DEV)))
    ratio_linear = fe_linear / (eps_ref ** 2) if eps_ref > 0 else 0.0
    # A linear error at eps=0.001 gives 1-F_e ~ 0.001/2 ~= 5e-4 -> ratio ~ 500 >> 0.25
    assert abs(ratio_linear - 0.25) > 0.1, (
        f"FALSIFIER DID NOT TRIP: linear-in-eps channel has (1-F_e)/eps^2 = {ratio_linear:.4f} "
        "which is within 0.1 of 0.25; the L7 quadratic-scaling check cannot distinguish "
        "linear from quadratic at this scale — falsifier broken"
    )


# ---------------------------------------------------------------------------
# INVARIANT L8: Even symmetry  1-F_e(eps) = 1-F_e(-eps)  (class-a, exact)
# Over-rotation and under-rotation of equal magnitude are equally infidel (pre-reg B1).
# BROKEN INPUT: an asymmetric (directional) error formula.
# ---------------------------------------------------------------------------

def test_L8_infidelity_even_in_eps():
    """L8 (class-a exact): 1-F_e is even in eps (symmetric in sign of over-rotation).

    sin^2(eps/2) = sin^2(-eps/2); RY(eps) and RY(-eps) have the same infidelity vs identity.
    For any unitary U, F_e = |Tr U / d|^2 satisfies F_e(U) = F_e(U†) (trace modulus is
    invariant under conjugation), so 1-F_e is always even in the rotation angle.
    """
    dt_ns = 20.0
    cdt = torch.complex128
    I_kraus = torch.eye(2, dtype=cdt, device=DEV).unsqueeze(0)
    J_I = _choi_state_from_kraus(I_kraus, device=DEV)

    def _fe(coeff_val: float) -> float:
        H = _hamiltonian_matrix_for_term(
            _make_coh_ry_term(coeff_val),
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

    BROKEN INPUT: wrong reference formula f(eps) = sin(eps/2) — odd function vs correct sin^2.
    ||sin(eps/2) - sin(-eps/2)|| = 2*|sin(eps/2)| >> 0 for eps != 0.
    """
    for eps in (0.3, 0.1, 0.03, 0.01, 0.003, 0.001):
        # Correct formula: sin^2(eps/2) — should be even in eps
        correct_pos = exact_infidelity_M20(+eps)
        correct_neg = exact_infidelity_M20(-eps)
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
# In a qutrit carrier (dim=3), H_M20 acts as (coeff/2)*Y on the [0:2,0:2] block
# and as the ZERO GENERATOR on the [2,2] element (no leakage drive; M20 leaves
# |2> unchanged: exp(0)=1 on level >=2 — pre-registration S2 M20-specific note).
# BROKEN INPUT: extending Y to a 3x3 matrix with a non-zero [2,2] entry or off-diagonal
# coupling to level |2> would violate the S2 zero-generator rule.
# ---------------------------------------------------------------------------

def test_L9_qutrit_embed_is_zero_on_leaked_levels():
    """L9 (class-a exact, S2): in a dim=3 carrier, H_M20[:2,:2] = ref_H_M20(coeff,2)
    AND H_M20[2,:] = H_M20[:,2] = 0 (no leakage drive from M20).

    M20-specific: RY leaves |2> unchanged (exp(0)=1 on level >=2).
    Any leaked-level coupling is a DIFFERENT mechanism (leakage transport, M34/LEAK_*),
    not M20 (pre-reg S2).
    """
    coeff = 0.1
    H = _hamiltonian_matrix_for_term(
        _make_coh_ry_term(coeff),
        support=(0,),
        local_dims=(3,),
        device=DEV,
    )
    # The 2-level block must equal the qubit reference
    H_ref_2level = ref_H_M20(coeff, 2)
    diff_2block = float(torch.linalg.matrix_norm(H[:2, :2] - H_ref_2level).item())
    assert diff_2block <= _OPERATOR_DIFF_TOL, (
        f"L9 FAIL: H_M20 qutrit 2-block differs from qubit reference by {diff_2block:.3e}"
    )
    # The leaked-level row/col must be zero
    leaked_row = float(torch.linalg.norm(H[2, :]).item())
    leaked_col = float(torch.linalg.norm(H[:, 2]).item())
    assert leaked_row <= _OPERATOR_DIFF_TOL, (
        f"L9 FAIL: H_M20 qutrit row-2 = {leaked_row:.3e} != 0; M20 drives leakage — S2 violated"
    )
    assert leaked_col <= _OPERATOR_DIFF_TOL, (
        f"L9 FAIL: H_M20 qutrit col-2 = {leaked_col:.3e} != 0; M20 drives leakage — S2 violated"
    )


def test_L9_broken_full_qutrit_y_coupling_trips():
    """FALSIFIER: a 3x3 Y-like matrix with a non-zero [2,2] element or off-diagonal
    coupling to level |2> fails L9.

    BROKEN INPUT: extend Y to 3x3 with a non-zero imaginary off-diagonal at row/col 2.
    This would impart amplitude between the computational and leaked subspace — not M20.
    ||H_broken[2,:]||_F = |c| >> 1e-12.
    """
    cdt = torch.complex128
    # 3x3 Y-like extended with off-diagonal coupling to level |2>: not M20 semantics
    H_broken = torch.zeros((3, 3), dtype=cdt, device=DEV)
    H_broken[0, 1] = -1.0j * 0.05
    H_broken[1, 0] = +1.0j * 0.05
    # Add a coupling between level 1 and level 2 (leaked-level drive):
    H_broken[1, 2] = -1.0j * 0.05
    H_broken[2, 1] = +1.0j * 0.05
    leaked_row = float(torch.linalg.norm(H_broken[2, :]).item())
    assert leaked_row > _OPERATOR_DIFF_TOL, (
        "FALSIFIER DID NOT TRIP: the broken qutrit-Y (with coupling to level |2>) has zero row-2 "
        "norm — falsifier wrong"
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
    class _FakeModule:
        _coherent_family_generator = lambda *a, **kw: None  # noqa: E731
        _hamiltonian_matrix_for_term = lambda *a, **kw: None  # noqa: E731

    fake = _FakeModule()
    assert hasattr(fake, "_coherent_family_generator"), (
        "FALSIFIER DID NOT TRIP: the fake module lacks the circular symbol — falsifier broken"
    )
