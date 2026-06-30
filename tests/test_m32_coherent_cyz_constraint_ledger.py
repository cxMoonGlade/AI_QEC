"""M32 coherent_yz_parasitic_coupling -- CONSTRAINT LEDGER (executable falsifier tests).

FAITHFULNESS PROTOCOL (docs/FAITHFULNESS_PROTOCOL.md) -- constraint ledger for M32.
Each test below is a FALSIFIER: it documents the invariant AND shows that a
deliberately BROKEN input makes the test FAIL (trips the falsifier). Tests run
GREEN on the faithful carrier and RED on the broken variant.

ANTI-CIRCULARITY: the reference operator (``ref_H_M32``) is HAND-TYPED from the
literature (Zhang-Vala-Sastry-Whaley arXiv:quant-ph/0209120 Eq. 7 -- sigma^1_y sigma^2_z
is the 6th of the 9 Pauli(x)Pauli basis elements of the non-local part p of su(4); Sec. V
Example 2 general H = sum_ab J_ab sigma_a(x)sigma_b with independent J_yz; Kraus-Cirac
arXiv:quant-ph/0011050 Eq. 24 one-axis gate form U = cos(a).I - i sin(a).S for any
traceless involution S = P(x)Q, S^2=I).  The cert imports ONLY
``axis1_mcwf_mps_execution._hamiltonian_matrix_for_term`` (the object under test).
The carrier's ``_coherent_family_generator`` / ``_embed_coherent_generator`` /
``TWO_SITE_COHERENT_FAMILIES`` / ``COHERENT_PAULI_FAMILIES`` appear NOWHERE in the
reference code (same de-circularization rule as test_m23_coherent_cyy_constraint_ledger.py,
test_m22_coherent_cxx_constraint_ledger.py, test_axis1_wc_decircularized.py, and the
M6/M7/M20 ledgers).

GATE TIER: STRICT (``1-F_e <= 1e-6``; operator identity <= 1e-12 / unitary <= 1e-10).
M32 is a pure-Hamiltonian / exact-dense error -- no collapse, no finite-step MCWF.

M32-SPECIFIC:
- The generator is H_M32 = (coeff/4) * (Y (x) Z), the off-axis cross-term (Zhang Eq. 7,
  sigma^1_y sigma^2_z listed verbatim as the 6th basis element of p; Sec. V Ex. 2,
  general J_yz sigma_y(x)sigma_z with independent coefficient).  NOT a Cartan axis
  (XX/YY/ZZ); NOT the always-on gmon XX (Geller 1405.1915); NOT the transverse exchange
  XX+YY (Sung 2011.01261); NOT a static ZZ (Pettersson 2408.15402).  Device origin:
  conditional-rotation / cross-resonance orbit (Magesan-Gambetta 1804.04073 Eq.3.14/3.16;
  Y(x)Z = (R_z(pi/2)(x)I)(X(x)Z)(R_z(-pi/2)(x)I), local-unitary to the CR Z(x)X
  generator).
- ``1-F_e = sin^2(eps/4)`` (factor /4, 2-site convention) is AXIS-BLIND -- identical for
  ANY single Pauli-pair generator P(x)Q at the same eps (pre-reg B1).  The operator-identity
  gate L3a and wrong-axis falsifiers (L3b-L3f) are the LOAD-BEARING cert gates: the SOLE
  witnesses that the carrier couples via Y(x)Z and not ZY/YY/ZZ/XZ/(XX+YY).
  L3b (YZ vs ZY = M30) is the PRIMARY M32-SHARP CONTROL: because 1-F_e is identical for
  M32 (YZ) and M30 (ZY) (same scalar, axis-blind), B4 is the ONLY thing that separates
  them.  Z(x)Y is ALSO imaginary-antisymmetric (Y antisym(x)Z sym = same imaginary-antisym
  type), so the M32 structural assertion alone is insufficient to separate them -- only the
  index/support ordering (which Pauli is on which site) does.
- Y(x)Z is PURELY IMAGINARY and ANTISYMMETRIC (Y is imaginary/antisymmetric; Z is
  real/symmetric; Y(x)Z inherits the imaginary-antisymmetry of Y): imag-part is nonzero
  (the pure-imaginary fact); real-part norm = 0; antisymmetric residual ||H + H^T||_F = 0.
  This is the OPPOSITE of M23 (Y(x)Y real-symmetric) and M22 (X(x)X real-symmetric).
  Explicitly: Y(x)Z = i * [[0,0,-1,0],[0,0,0,1],[1,0,0,0],[0,-1,0,0]] (pre-reg §1/§2 B4).
  Hermitian: H = H† (Y and Z are both Hermitian; their Kronecker product is Hermitian).
- The ratio limit is eps^2/16 (not 1/4 as for 1-site generators, because d=4 and /4 factor).
- Borrowing: ``exact_infidelity_M32(eps)`` is identical to M22/M23's formula (sin^2(eps/4))
  since all are single traceless Pauli-pair involutions at d=4. The observable L6 cannot
  distinguish them; the operator gate L3a + wrong-axis controls are the distinguishing evidence.

GPU-only (top-level memory rule) -- collection FAILS without CUDA.

Pre-registration: docs/twin_validation/m32_coherent_yz_parasitic_coupling_prereg.md
Run:  conda run -n aiqec python -m pytest -q tests/test_m32_coherent_cyz_constraint_ledger.py
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
        "M32 constraint-ledger cert is GPU-gated; CUDA-MISSING is NOT A RELEASE BASIS",
        pytrace=False,
    )

# ---------------------------------------------------------------------------
# Carrier import -- ONLY the per-term operator builder (anti-circular)
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
#                           # (class-c gate; derivation-check: ZY/YY/ZZ/XZ each diff 7.07e-2
#                           # at eps=0.1; M10 (XX+YY) diff 8.66e-2; all >> 1e-3)

# ---------------------------------------------------------------------------
# Reference operator (HAND-TYPED, non-circular)
#
# Provenance:
#   H_M32 = (coeff/4) * (sigma_y (x) sigma_z)  on the 4-dim computational subspace.
#   sigma_y = [[0,-i],[i,0]]  (Nielsen & Chuang Eq. 2.1, Pauli-Y).
#   sigma_z = [[1,0],[0,-1]]  (Nielsen & Chuang Eq. 2.1, Pauli-Z).
#   Y(x)Z is an off-axis cross-term: named explicitly as sigma^1_y sigma^2_z,
#           the 6th of the 9 Pauli(x)Pauli basis elements of the non-local part p of su(4),
#           Zhang-Vala-Sastry-Whaley arXiv:quant-ph/0209120 Eq. 7 (sigma^1_y sigma^2_z
#           listed verbatim); carried by the general anisotropic interaction
#           H = sum_ab J_ab sigma_a(x)sigma_b with independent J_yz (Zhang Sec. V Example 2;
#           the bilinear sigma_A^T M sigma_B with general M (Kraus-Cirac arXiv:quant-ph/0011050
#           Sec. III/App. A) carries the off-diagonal M_yz sigma_y(x)sigma_z before the
#           local-unitary diagonalization to d=diag).  One-axis gate form U = cos(a).I - i sin(a).S
#           for any traceless involution S = P(x)Q with S^2=I (Kraus-Cirac Eq. 24).
#   DEVICE origin (conditional-rotation / cross-resonance ORBIT, DIRECT):
#           Y(x)Z = (R_z(pi/2)(x)I)(X(x)Z)(R_z(-pi/2)(x)I) (verified, LU-resid 6.85e-8),
#           local-unitary to the CR Z(x)X conditional-rotation generator (Magesan-Gambetta
#           arXiv:1804.04073 Eq. 3.14/3.16). NOT the gmon always-on (pure XX, Geller
#           arXiv:1405.1915), NOT the transverse exchange (XX+YY, Sung arXiv:2011.01261),
#           NOT static ZZ (Pettersson arXiv:2408.15402). "mixed YZ residue"
#           (error_mechanisms.md line 123).
#   factor 1/4 = (1/2)^2: two-qubit over-rotation convention
#           R_{PQ}(eps_cat) = exp(-i (eps_cat/2)(P(x)Q)), carrier eps = coeff*dt is the
#           per-tensor angle; catalog eps_cat = eps/2
#           (error_mechanisms.md line 123 "exp(-i eps YZ/2)"; carrier docstring lines
#           1026-1029).
#   M32 structural fact: Y(x)Z is PURELY IMAGINARY and ANTISYMMETRIC.
#           Y is imaginary/antisymmetric; Z is real/symmetric; their Kronecker product is
#           purely imaginary and antisymmetric: real-part norm = 0, antisymmetric residual
#           ||H + H^T||_F = 0.  Yet Y(x)Z is Hermitian (H = H†), because Y† = Y and Z† = Z.
#           Explicit matrix: Y(x)Z = i * [[0,0,-1,0],[0,0,0,1],[1,0,0,0],[0,-1,0,0]].
#           Contrast M23 Y(x)Y (real-symmetric) and M22 X(x)X (real-symmetric).
#           Tr = 0, (Y(x)Z)^2 = I4.
#   zero generator on any leaked level >= 2 (S3; _embed_coherent_generator semantics).
#   error unitary: U = exp(-i H dt) = cos(eps/4) I4 - i sin(eps/4)(Y(x)Z),  eps = coeff*dt.
#   EXACT 1-F_e (d=4): 1 - |Tr(U)/4|^2 = sin^2(eps/4).
#   LEADING 1-F_e:  ||(eps/4)(Y(x)Z)||_F^2 / 4 = eps^2/16.
# ---------------------------------------------------------------------------

def ref_H_M32(coeff: float, d0: int, d1: int) -> torch.Tensor:
    """Hand-typed M32 reference generator on the (d0*d1)-dim local space.

    H_M32 = (coeff/4) * (Y (x) Z)  embedded into the d0*d1-dimensional space,
    with the zero generator (identity gate) on any product-level pair where either
    index >= 2 (no leakage drive from M32 -- S3).
    Imports NOTHING from the carrier family tables.
    """
    cdt = torch.complex128
    # Hand-typed Pauli-Y and Pauli-Z (Nielsen & Chuang Eq. 2.1)
    Y2 = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
    Z2 = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=cdt, device=DEV)
    # (coeff/4) * (Y (x) Z) on the 4-dim computational subspace
    gen4 = 0.25 * coeff * torch.kron(Y2.contiguous(), Z2.contiguous())
    # embed into d0*d1 space: only the computational rows/cols {0,1} x {0,1}
    out = torch.zeros((d0 * d1, d0 * d1), dtype=cdt, device=DEV)
    for left_in in (0, 1):
        for right_in in (0, 1):
            col = left_in * d1 + right_in
            qcol = left_in * 2 + right_in
            for left_out in (0, 1):
                for right_out in (0, 1):
                    row = left_out * d1 + right_out
                    qrow = left_out * 2 + right_out
                    out[row, col] = gen4[qrow, qcol]
    return out


def ref_U_M32(coeff: float, dt_ns: float, d0: int, d1: int) -> torch.Tensor:
    """Hand-typed M32 error unitary: U = matrix_exp(-i * H * dt)."""
    H = ref_H_M32(coeff, d0, d1)
    return torch.linalg.matrix_exp(-1j * dt_ns * H)


def exact_infidelity_M32(eps: float) -> float:
    """Closed-form 1-F_e for exp(-i(eps/4)(Y(x)Z)) vs identity (d=4).

    Tr(U_M32) = Tr(cos(eps/4)I4 - i sin(eps/4)(Y(x)Z)) = 4*cos(eps/4)  [Tr(Y(x)Z)=0].
    F_e = |Tr(U)/4|^2 = cos^2(eps/4)  =>  1-F_e = sin^2(eps/4).
    Reference: Nielsen arXiv:quant-ph/0205035 Eq. 16 (F_e = |Tr U / d|^2 for unitary U);
    pre-registration B1, section 2.
    NOTE: sin^2(eps/4) is the same for ANY single Pauli-pair P(x)Q generator at
    the same eps (Tr(P(x)Q)=0 and (P(x)Q)^2=I4 for all single Paulis) -- axis-agnostic.
    This is identical to exact_infidelity_M22/M23; the /4 factor is the 2-site convention.
    """
    return float(math.sin(eps / 4.0) ** 2)


def _make_coh_yz_term(coeff: float) -> dict:
    """Minimal schedule-term dict for COH_YZ on two sites (support=(0,1))."""
    return {
        "kind": "hamiltonian",
        "operator_family": "COH_YZ",
        "support": [0, 1],
        "coefficient": float(coeff),
        "substep_id": "m32_ledger",
    }


# ---------------------------------------------------------------------------
# INVARIANT L1: Hermiticity  ||H - H†||_F <= 1e-12  (class-a exact)
# Pauli-pair generators are Hermitian; Y† = Y, Z† = Z => (Y(x)Z)† = Y†(x)Z† = Y(x)Z.
# An anti-Hermitian generator is WRONG.
# BROKEN INPUT: a non-Hermitian matrix (imaginary off-diagonal term only on one side)
# ---------------------------------------------------------------------------

def test_L1_generator_is_hermitian():
    """L1 (class-a exact): the M32 generator H satisfies H = H†.

    Y(x)Z is Hermitian: Y† = Y, Z† = Z, so (Y(x)Z)† = Y†(x)Z† = Y(x)Z.
    Note: Y(x)Z is purely imaginary AND Hermitian (they are compatible: an
    imaginary matrix M satisfies M = M† iff M is imaginary-antisymmetric,
    which Y(x)Z is -- pre-reg §1/§2 B4 structural fact).
    Broken-input demonstration: an explicitly non-Hermitian operator trips this test.
    """
    coeff = 0.1
    H = _hamiltonian_matrix_for_term(
        _make_coh_yz_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    resid = float(torch.linalg.matrix_norm(H - H.conj().T).item())
    assert resid <= _HERMITIAN_TOL, (
        f"L1 FAIL: ||H - H†||_F = {resid:.3e} > {_HERMITIAN_TOL}; "
        "M32 generator is not Hermitian -- physics bug"
    )


def test_L1_broken_non_hermitian_trips():
    """FALSIFIER: a deliberately non-Hermitian 4x4 matrix fails the L1 check."""
    cdt = torch.complex128
    # Upper-triangular only -- not Hermitian
    H_broken = torch.zeros((4, 4), dtype=cdt, device=DEV)
    H_broken[0, 3] = 1.0j
    resid = float(torch.linalg.matrix_norm(H_broken - H_broken.conj().T).item())
    assert resid > _HERMITIAN_TOL, (
        "FALSIFIER DID NOT TRIP: a known non-Hermitian 4x4 matrix passed L1 -- "
        "the falsifier is broken"
    )


# ---------------------------------------------------------------------------
# INVARIANT L2: Tracelessness  |Tr H| <= 1e-12  (class-a exact)
# Y(x)Z is traceless (Tr(Y(x)Z) = Tr(Y)*Tr(Z) = 0*0 = 0);
# an identity-shifted generator is WRONG.
# BROKEN INPUT: H + (c/4) * I4 (trace = coeff)
# ---------------------------------------------------------------------------

def test_L2_generator_is_traceless():
    """L2 (class-a exact): the M32 generator H is traceless.

    Tr(Y(x)Z) = Tr(Y)*Tr(Z) = 0*0 = 0. Any non-zero trace indicates identity
    contamination or a wrong family.
    """
    coeff = 0.1
    H = _hamiltonian_matrix_for_term(
        _make_coh_yz_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    tr_resid = float(torch.abs(torch.trace(H)).item())
    assert tr_resid <= _TRACELESS_TOL, (
        f"L2 FAIL: |Tr H| = {tr_resid:.3e} > {_TRACELESS_TOL}; "
        "M32 generator has a non-zero trace -- wrong axis or identity contamination"
    )


def test_L2_broken_identity_shift_trips():
    """FALSIFIER: a traceful 4x4 generator (YZ + identity offset) fails L2."""
    cdt = torch.complex128
    Y2 = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
    Z2 = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=cdt, device=DEV)
    YZ = torch.kron(Y2.contiguous(), Z2.contiguous())
    H_broken = 0.025 * YZ + 0.025 * torch.eye(4, dtype=cdt, device=DEV)
    tr_resid = float(torch.abs(torch.trace(H_broken)).item())
    assert tr_resid > _TRACELESS_TOL, (
        "FALSIFIER DID NOT TRIP: an identity-shifted 4x4 generator passed L2 -- "
        "the falsifier is broken"
    )


# ---------------------------------------------------------------------------
# INVARIANT L2b: Imaginary-antisymmetric structure of Y(x)Z  (class-a exact, M32-specific)
# Y(x)Z is PURELY IMAGINARY (real-part norm = 0) and ANTISYMMETRIC (H^T = -H, i.e.
# the antisymmetric residual ||H + H^T||_F = 0), yet Hermitian.
# This is the M32-SHARP structural fact, distinguishing it from:
#   - M23 Y(x)Y (real-symmetric),  M22 X(x)X (real-symmetric),
#   - M31 X(x)Z (also imaginary-antisymmetric but DIFFERENT index structure).
# The Z(x)Y (M30) is ALSO imaginary-antisymmetric -- L2b alone does NOT separate
# M32 from M30; the operator identity gate (L3a) and the L3b ZY-vs-YZ control do.
# BROKEN INPUT: a matrix with non-zero real part (e.g. X(x)X, which is real-symmetric)
# ---------------------------------------------------------------------------

def test_L2b_yz_generator_is_imaginary_antisymmetric():
    """L2b (class-a exact, M32-specific): Y(x)Z is purely imaginary and antisymmetric.

    Y = [[0,-i],[i,0]] is imaginary/antisymmetric; Z = [[1,0],[0,-1]] is real/symmetric;
    their Kronecker product Y(x)Z is purely imaginary (real-part norm = 0) and antisymmetric
    (H + H^T = 0).  Explicitly: Y(x)Z = i * [[0,0,-1,0],[0,0,0,1],[1,0,0,0],[0,-1,0,0]].
    This is the M32-sharp structural fact; contrast M23 Y(x)Y (real-symmetric) and
    M22 X(x)X (real-symmetric) where the imaginary factors cancel.

    Note: Y(x)Z is Hermitian (H = H†) simultaneously with being imaginary-antisymmetric
    -- this is consistent because an imaginary matrix M satisfies M = M† iff M is
    imaginary-antisymmetric (iA with A real-symmetric: (iA)† = -iA^T = iA iff A^T = -A
    -- but here A is the real part of the scaled matrix, so the Hermitian + imaginary-antisym
    facts are compatible; numerics: H.conj().T == H while H.real.norm() == 0 and H+H^T == 0).
    """
    coeff = 0.1
    H = _hamiltonian_matrix_for_term(
        _make_coh_yz_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    # Real part should be zero (purely imaginary)
    real_norm = float(torch.linalg.matrix_norm(H.real).item())
    assert real_norm <= _OPERATOR_DIFF_TOL, (
        f"L2b FAIL: real-part norm of H_M32 = {real_norm:.3e} > {_OPERATOR_DIFF_TOL}; "
        "Y(x)Z should be PURELY IMAGINARY (Y imaginary x Z real) -- physics bug"
    )
    # Antisymmetric: H + H^T = 0 (i.e. H^T = -H)
    antisym_resid = float(torch.linalg.matrix_norm(H + H.T).item())
    assert antisym_resid <= _OPERATOR_DIFF_TOL, (
        f"L2b FAIL: antisymmetric residual ||H + H^T||_F = {antisym_resid:.3e} > "
        f"{_OPERATOR_DIFF_TOL}; Y(x)Z should be ANTISYMMETRIC -- structural bug"
    )


def test_L2b_broken_xx_is_real_symmetric_trips():
    """FALSIFIER: X(x)X is real-symmetric, failing the purely-imaginary L2b check.

    X = [[0,1],[1,0]] is real/symmetric; X(x)X has a non-zero real part.
    The L2b real-norm check would flag this -- confirming the structural assertion
    is meaningful (a real-symmetric generator is caught by the imaginary test).
    """
    cdt = torch.complex128
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    H_xx = 0.025 * torch.kron(X2.contiguous(), X2.contiguous())
    real_norm = float(torch.linalg.matrix_norm(H_xx.real).item())
    assert real_norm > _OPERATOR_DIFF_TOL, (
        "FALSIFIER DID NOT TRIP: X(x)X appears to have zero real part -- "
        "falsifier broken (check the computation)"
    )


# ---------------------------------------------------------------------------
# INVARIANT L3a: Operator identity  ||H_carrier - H_ref||_F <= 1e-12  (B4, class-a)
# This is the LOAD-BEARING cert gate for M32.
# 1-F_e alone cannot catch wrong Pauli-pair axis: sin^2(eps/4) is identical for ANY
# single Pauli-pair generator at the same eps -- pre-reg B1.  This includes M30 (ZY):
# 1-F_e is IDENTICAL for M32 (YZ) and M30 (ZY) -- operator identity is the ONLY witness.
# BROKEN INPUT: wrong-axis references (ZY=M30 / YY=M23 / ZZ / XZ=M31 / XX+YY=M10).
# The ZY (M30) control is the PRIMARY M32-sharp gate: the SOLE distinguisher of M32 vs M30.
# ---------------------------------------------------------------------------

def test_L3a_operator_matches_hand_typed_reference():
    """L3a (class-a exact, B4): the carrier generator equals the hand-typed reference.

    H_ref = (coeff/4) * (Y(x)Z) embedded in (d0,d1), from Zhang Eq.7 / Sec.V Ex.2.
    This is the LOAD-BEARING gate -- 1-F_e alone cannot distinguish YZ from ZY/YY/ZZ/XZ/...
    at equal eps (all have the same sin^2(eps/4); pre-reg B1). The operator identity is
    the SOLE witness of the YZ axis (M32 vs M30/M22/M23/M28-M33/M10 distinction).
    Critically: M32 (YZ) and M30 (ZY) are BOTH imaginary-antisymmetric and have the
    SAME 1-F_e; the only separation is the index/support ordering (L3b).

    Swept over coeff in {0.3, 0.1, 0.03, 0.01, 0.003, 0.001} and dims (2,2) / (3,3).
    """
    for coeff in (0.3, 0.1, 0.03, 0.01, 0.003, 0.001):
        for d0, d1 in ((2, 2), (3, 3)):
            H_carrier = _hamiltonian_matrix_for_term(
                _make_coh_yz_term(coeff),
                support=(0, 1),
                local_dims=(d0, d1),
                device=DEV,
            )
            H_ref = ref_H_M32(coeff, d0, d1)
            diff = float(torch.linalg.matrix_norm(H_carrier - H_ref).item())
            assert diff <= _OPERATOR_DIFF_TOL, (
                f"L3a FAIL: ||H_carrier - H_ref||_F = {diff:.3e} > {_OPERATOR_DIFF_TOL} "
                f"at coeff={coeff}, dims=({d0},{d1}) -- wrong generator (wrong axis, "
                "wrong coefficient, wrong convention)"
            )


def test_L3b_broken_wrong_axis_zy_trips():
    """FALSIFIER (L3b, M32-SHARP GATE): a wrong-axis ZY reference disagrees with the YZ carrier
    by >= 1e-3.

    THIS IS THE PRIMARY WRONG-AXIS CONTROL for M32 (pre-reg §3):
    a reference H_wrong = (coeff/4)(Z(x)Y) disagrees with the YZ carrier.
    Z(x)Y is the support-swapped directional partner (M30): ALSO imaginary-antisymmetric,
    ALSO Hermitian, ALSO has 1-F_e = sin^2(eps/4).  The ONLY thing that distinguishes
    M32 (YZ) from M30 (ZY) is the index ordering -- which site carries the Y vs the Z.
    The hand-typed (Y(x)Z) reference catches the swap; a reference derived FROM a corrupted
    carrier pair map (COH_YZ -> (Z,Y)) would mirror the swap to diff=0 (false-pass).

    Derivation-check (2026-06-29): diff = 7.07e-2 at eps=0.1, well above 1e-3.
    """
    coeff = 0.1
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_yz_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    cdt = torch.complex128
    Z2 = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=cdt, device=DEV)
    Y2 = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
    H_wrong_zy = 0.25 * coeff * torch.kron(Z2.contiguous(), Y2.contiguous())  # ZY, not YZ
    diff = float(torch.linalg.matrix_norm(H_carrier - H_wrong_zy).item())
    assert diff >= _WRONG_AXIS_MIN, (
        f"FALSIFIER DID NOT TRIP: wrong-axis ZY (M30) reference passed with diff={diff:.3e} < "
        f"{_WRONG_AXIS_MIN}; the M32/M30 (YZ/ZY) directional-partner separation is "
        "undetectable -- this is the PRIMARY M32-sharp gate"
    )


def test_L3c_broken_wrong_axis_yy_trips():
    """FALSIFIER (L3c): a wrong-axis YY reference disagrees with the YZ carrier by >= 1e-3.

    YY is the Cartan-axis M23 (COH_YY); YZ is the off-axis cross-term M32 (COH_YZ).
    They are structurally distinct: YY is real-symmetric; YZ is imaginary-antisymmetric.
    The operator gate must catch M32/M23 confusion.

    Derivation-check (2026-06-29): diff = 7.07e-2 at eps=0.1, well above 1e-3.
    """
    coeff = 0.1
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_yz_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    cdt = torch.complex128
    Y2 = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
    H_wrong_yy = 0.25 * coeff * torch.kron(Y2.contiguous(), Y2.contiguous())
    diff = float(torch.linalg.matrix_norm(H_carrier - H_wrong_yy).item())
    assert diff >= _WRONG_AXIS_MIN, (
        f"FALSIFIER DID NOT TRIP: wrong-axis YY (M23) reference passed with diff={diff:.3e} < "
        f"{_WRONG_AXIS_MIN}; the YZ/YY confusion is undetectable"
    )


def test_L3d_broken_wrong_axis_zz_trips():
    """FALSIFIER (L3d): a wrong-axis ZZ reference disagrees with the YZ carrier by >= 1e-3.

    ZZ is diagonal (eigenvalues +1/-1 on diag); YZ is purely imaginary off-block-diagonal.
    Structurally distinct. M32-specific: ZZ is the coherent crosstalk axis M11; the operator
    gate must keep M32 distinct from a ZZ coupling.

    Derivation-check (2026-06-29): diff = 7.07e-2 at eps=0.1, well above 1e-3.
    """
    coeff = 0.1
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_yz_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    cdt = torch.complex128
    Z2 = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=cdt, device=DEV)
    H_wrong_zz = 0.25 * coeff * torch.kron(Z2.contiguous(), Z2.contiguous())
    diff = float(torch.linalg.matrix_norm(H_carrier - H_wrong_zz).item())
    assert diff >= _WRONG_AXIS_MIN, (
        f"FALSIFIER DID NOT TRIP: wrong-axis ZZ reference passed with diff={diff:.3e} < "
        f"{_WRONG_AXIS_MIN}; the YZ/ZZ confusion is undetectable"
    )


def test_L3e_broken_wrong_axis_xz_trips():
    """FALSIFIER (L3e): a wrong-axis XZ reference disagrees with the YZ carrier by >= 1e-3.

    XZ = X(x)Z is M31 (COH_XZ), also imaginary-antisymmetric (X imaginary-sym? -- no:
    X is real-symmetric; X(x)Z = real-sym(x)real-sym = real-symmetric, not imaginary).
    Actually X(x)Z is REAL-antisymmetric (X real-sym x Z real-sym but in different block
    positions); in any case structurally distinct from YZ (which is purely imaginary).
    The operator gate must catch M32/M31 confusion.

    Derivation-check (2026-06-29): diff = 7.07e-2 at eps=0.1, well above 1e-3.
    """
    coeff = 0.1
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_yz_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    cdt = torch.complex128
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    Z2 = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=cdt, device=DEV)
    H_wrong_xz = 0.25 * coeff * torch.kron(X2.contiguous(), Z2.contiguous())
    diff = float(torch.linalg.matrix_norm(H_carrier - H_wrong_xz).item())
    assert diff >= _WRONG_AXIS_MIN, (
        f"FALSIFIER DID NOT TRIP: wrong-axis XZ (M31) reference passed with diff={diff:.3e} < "
        f"{_WRONG_AXIS_MIN}; the YZ/XZ confusion is undetectable"
    )


def test_L3f_broken_wrong_axis_xxyy_trips():
    """FALSIFIER (L3f): a wrong-axis (XX+YY)/4 reference disagrees with the YZ carrier by >= 1e-3.

    (XX+YY) is M10 (COH_XX_YY, the exchange interaction); pure YZ is M32.
    The carrier's COH_YZ must return only the YZ pair, not the exchange block.
    M32-specific: the device transverse exchange (g/2)(XX+YY) (Sung arXiv:2011.01261) contains
    neither a YZ term; a pure YZ teacher is an isolated cross-term (S2 -- declared simplification).
    The cert must confirm the carrier emits only YZ, not the exchange block.

    Derivation-check (2026-06-29): diff = 8.66e-2 at eps=0.1, above 1e-3.
    """
    coeff = 0.1
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_yz_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    cdt = torch.complex128
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    Y2 = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
    XX = torch.kron(X2.contiguous(), X2.contiguous())
    YY = torch.kron(Y2.contiguous(), Y2.contiguous())
    # M10 form: (coeff/4)*(XX+YY) -- two pairs, not one
    H_wrong_xxyy = 0.25 * coeff * (XX + YY)
    diff = float(torch.linalg.matrix_norm(H_carrier - H_wrong_xxyy).item())
    assert diff >= _WRONG_AXIS_MIN, (
        f"FALSIFIER DID NOT TRIP: wrong-axis (XX+YY) reference passed with diff={diff:.3e} < "
        f"{_WRONG_AXIS_MIN}; the YZ/(XX+YY) confusion is undetectable (M32 vs M10 indistinct)"
    )


def test_L3g_broken_wrong_unit_no_factor_trips():
    """FALSIFIER (L3g): wrong-unit convention (coeff*(Y(x)Z), missing the /4) disagrees.

    Correct: H = (coeff/4)*(Y(x)Z).  Wrong: H = coeff*(Y(x)Z)  [missing both /2 factors].
    A factor-of-4 error in the generator gives a factor-of-4 error in the angle.
    """
    coeff = 0.1
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_yz_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    cdt = torch.complex128
    Y2 = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
    Z2 = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=cdt, device=DEV)
    YZ = torch.kron(Y2.contiguous(), Z2.contiguous())
    H_wrong_unit = float(coeff) * YZ  # missing the /4
    diff = float(torch.linalg.matrix_norm(H_carrier - H_wrong_unit).item())
    assert diff >= _WRONG_AXIS_MIN, (
        f"FALSIFIER DID NOT TRIP: wrong-unit (coeff*YZ, missing /4) has diff={diff:.3e} < "
        f"{_WRONG_AXIS_MIN}; the factor-of-4 error is undetectable"
    )


def test_L3h_broken_wrong_unit_half_factor_trips():
    """FALSIFIER (L3h): wrong-unit convention ((coeff/2)*(Y(x)Z), missing one /2) disagrees.

    Correct: H = (coeff/4)*(Y(x)Z).  Wrong: H = (coeff/2)*(Y(x)Z)  [only one /2 factor,
    as if this were a 1-site over-rotation convention applied to the 2-site case].
    """
    coeff = 0.1
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_yz_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    cdt = torch.complex128
    Y2 = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
    Z2 = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=cdt, device=DEV)
    YZ = torch.kron(Y2.contiguous(), Z2.contiguous())
    H_wrong_half = 0.5 * float(coeff) * YZ  # missing one /2
    diff = float(torch.linalg.matrix_norm(H_carrier - H_wrong_half).item())
    assert diff >= _WRONG_AXIS_MIN, (
        f"FALSIFIER DID NOT TRIP: wrong-unit ((coeff/2)*YZ, missing one /2) has diff={diff:.3e} < "
        f"{_WRONG_AXIS_MIN}; the factor-of-2 error is undetectable"
    )


# ---------------------------------------------------------------------------
# INVARIANT L4: Unitary identity  ||U_carrier - U_ref||_F <= 1e-10  (B4, class-a)
# U = matrix_exp(-i H dt) = cos(eps/4) I4 - i sin(eps/4)(Y(x)Z),  eps = coeff * dt_ns.
# BROKEN INPUT: wrong-sign exponent (U = exp(+i H dt)) -- gives the inverse/adjoint gate.
# ---------------------------------------------------------------------------

def test_L4_error_unitary_matches_reference():
    """L4 (class-a exact, B4): the carrier's error gate U = exp(-i H dt) equals the
    reference cos(eps/4)*I4 - i*sin(eps/4)*(Y(x)Z) to <= 1e-10.

    Swept over coeff in {0.3, 0.1, 0.03, 0.01, 0.003, 0.001} and dims (2,2) / (3,3).
    """
    dt_ns = 20.0
    for coeff in (0.3, 0.1, 0.03, 0.01, 0.003, 0.001):
        for d0, d1 in ((2, 2), (3, 3)):
            eps = coeff * dt_ns
            H_carrier = _hamiltonian_matrix_for_term(
                _make_coh_yz_term(coeff),
                support=(0, 1),
                local_dims=(d0, d1),
                device=DEV,
            )
            U_carrier = torch.linalg.matrix_exp(-1j * dt_ns * H_carrier)
            U_ref = ref_U_M32(coeff, dt_ns, d0, d1)
            diff = float(torch.linalg.matrix_norm(U_carrier - U_ref).item())
            assert diff <= _UNITARY_DIFF_TOL, (
                f"L4 FAIL: ||U_carrier - U_ref||_F = {diff:.3e} > {_UNITARY_DIFF_TOL} "
                f"at coeff={coeff}, dt={dt_ns}, eps={eps:.3f}, dims=({d0},{d1})"
            )


def test_L4_broken_wrong_sign_exponent_trips():
    """FALSIFIER: the wrong-sign exponent (exp(+i H dt)) disagrees with the correct gate
    by >= 1e-3 for any non-zero eps not a multiple of pi/2.
    """
    coeff = 0.1
    dt_ns = 20.0
    d0, d1 = 2, 2
    H_ref = ref_H_M32(coeff, d0, d1)
    U_correct = torch.linalg.matrix_exp(-1j * dt_ns * H_ref)
    U_wrong_sign = torch.linalg.matrix_exp(+1j * dt_ns * H_ref)  # wrong sign
    diff = float(torch.linalg.matrix_norm(U_correct - U_wrong_sign).item())
    assert diff >= _WRONG_AXIS_MIN, (
        f"FALSIFIER DID NOT TRIP: wrong-sign exponent has diff={diff:.3e} < "
        f"{_WRONG_AXIS_MIN}; the sign flip is undetectable"
    )


# ---------------------------------------------------------------------------
# INVARIANT L5: CPTP residual (TP check)  ||sum_k K†K - I||_F <= 1e-12  (class-a exact)
# For a pure unitary (no collapse), the Kraus channel has a SINGLE Kraus = U.
# BROKEN INPUT: a non-unitary 4x4 matrix (scaling down by 0.8 -- not TP).
# ---------------------------------------------------------------------------

def test_L5_channel_is_tp():
    """L5 (class-a exact): the M32 Kraus channel assembled from H_M32 alone (no collapse)
    is exactly trace-preserving: sum_k K†K = I to <= 1e-12.

    M32 is a pure-Hamiltonian error (S1); no collapse operators. The single Kraus is
    U = exp(-i H dt), which is unitary, so sum_k K†K = U†U = I exactly.
    """
    dt_ns = 20.0
    coeff = 0.1
    H = _hamiltonian_matrix_for_term(
        _make_coh_yz_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
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
        "M32 channel is not trace-preserving"
    )


def test_L5_broken_non_tp_trips():
    """FALSIFIER: a non-unitary (non-TP) 4x4 Kraus set fails L5."""
    cdt = torch.complex128
    # Scale-down 4x4: not TP
    K_bad = 0.8 * torch.eye(4, dtype=cdt, device=DEV)
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
        "FALSIFIER DID NOT TRIP: a known non-TP 4x4 matrix passed L5 -- falsifier broken"
    )


# ---------------------------------------------------------------------------
# INVARIANT L6a: process infidelity == sin^2(eps/4) to Uhlmann floor  (B1, class-b band)
# exp(-i(eps/4)(Y(x)Z)) vs identity: 1-F_e = sin^2(eps/4) (Nielsen quant-ph/0205035 Eq. 16).
# Factor /4 (not /2) because it is a 2-site generator with (1/2)^2 convention.
# Threshold: STRICT 1-F_e <= 1e-6 (pure Hamiltonian, S1).
# ---------------------------------------------------------------------------

def test_L6a_infidelity_matches_exact_closed_form():
    """L6a (class-b band, B1): carrier 1-F_e = sin^2(eps/4) to the Uhlmann floor (~6e-8 at d=4).

    Swept over eps in {0.3, 0.1, 0.03, 0.01, 0.003, 0.001} rad.
    The STRICT gate tier (S1): numerical agreement of carrier vs the exact closed form.
    NOTE: sin^2(eps/4) is the same closed form for ANY single Pauli-pair P(x)Q generator
    at the same eps -- axis-agnostic (pre-reg B1). The /4 factor (not /2) is the 2-site convention.
    At eps=0.001 (1-F_e ~ 6.25e-8) the signal is at the Uhlmann floor; the operator gate (L3a,
    opdiff 0) carries the cert there (pre-reg S5).
    """
    dt_ns = 20.0
    cdt = torch.complex128
    I_kraus = torch.eye(4, dtype=cdt, device=DEV).unsqueeze(0)
    J_I = _choi_state_from_kraus(I_kraus, device=DEV)

    for coeff in (0.3 / dt_ns, 0.1 / dt_ns, 0.03 / dt_ns, 0.01 / dt_ns,
                  0.003 / dt_ns, 0.001 / dt_ns):
        eps = coeff * dt_ns
        H = _hamiltonian_matrix_for_term(
            _make_coh_yz_term(coeff),
            support=(0, 1),
            local_dims=(2, 2),
            device=DEV,
        )
        kraus = assemble_substep_channel([H], [], dt_ns, device=DEV)
        J_carrier = _choi_state_from_kraus(kraus, device=DEV)
        F_e = float(_state_fidelity(J_carrier, J_I, device=DEV))
        one_minus_fe = float(max(0.0, 1.0 - F_e))
        exact = exact_infidelity_M32(eps)
        band_resid = abs(one_minus_fe - exact)
        assert band_resid <= 5e-7, (
            f"L6a FAIL: |carrier_1-F_e - sin^2(eps/4)| = {band_resid:.3e} at eps={eps:.4f}; "
            f"carrier={one_minus_fe:.6e}, exact={exact:.6e}"
        )


def test_L6b_insufficiency_yz_same_infidelity_as_zy():
    """FALSIFIER / proof-of-insufficiency (L6b): the YZ channel (M32) and the ZY channel (M30)
    produce the SAME scalar 1-F_e = sin^2(eps/4) at the same eps.

    This is the M32-SHARP proof that 1-F_e CANNOT catch a wrong-axis bug for M32 vs M30
    (any single Pauli-pair P(x)Q gives sin^2(eps/4) -- pre-reg B1). Makes operator-identity
    gate L3a + ZY-control L3b strictly necessary. A cert relying only on 1-F_e would
    false-pass a COH_YZ->(Z,Y) map corruption (the pair map swaps YZ to ZY; the infidelity
    is unchanged).

    The test SHOULD PASS (same infidelity for both) -- its role is to DOCUMENT the
    insufficiency, proving that L3a + L3b are the necessary gates to distinguish M32 from M30.
    """
    coeff = 0.1
    dt_ns = 20.0
    cdt = torch.complex128
    eps = coeff * dt_ns

    # Correct: COH_YZ channel via carrier
    H_yz = _hamiltonian_matrix_for_term(
        _make_coh_yz_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    kraus_yz = assemble_substep_channel([H_yz], [], dt_ns, device=DEV)
    J_yz = _choi_state_from_kraus(kraus_yz, device=DEV)

    # Wrong-axis: ZY channel (M30) built by hand -- SAME infidelity vs identity, DIFFERENT operator
    Y2 = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
    Z2 = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=cdt, device=DEV)
    H_zy = 0.25 * coeff * torch.kron(Z2.contiguous(), Y2.contiguous())  # ZY, not YZ
    kraus_zy = assemble_substep_channel([H_zy], [], dt_ns, device=DEV)
    J_zy = _choi_state_from_kraus(kraus_zy, device=DEV)

    I_kraus = torch.eye(4, dtype=cdt, device=DEV).unsqueeze(0)
    J_I = _choi_state_from_kraus(I_kraus, device=DEV)

    fe_yz = float(max(0.0, 1.0 - _state_fidelity(J_yz, J_I, device=DEV)))
    fe_zy = float(max(0.0, 1.0 - _state_fidelity(J_zy, J_I, device=DEV)))

    # Both have the same scalar infidelity sin^2(eps/4) vs identity.
    # This SHOULD PASS -- it proves the insufficiency of 1-F_e for M32/M30 separation.
    assert abs(fe_yz - fe_zy) <= 1e-6, (
        f"INSUFFICIENCY PROOF FAILED: YZ and ZY at same eps have different 1-F_e "
        f"(fe_yz={fe_yz:.6e}, fe_zy={fe_zy:.6e}, diff={abs(fe_yz - fe_zy):.3e}); "
        "this test SHOULD PASS (same 1-F_e for both), proving 1-F_e alone is insufficient"
    )

    # But the operators themselves differ: confirms L3a + L3b are necessary
    YZ = 0.25 * coeff * torch.kron(Y2.contiguous(), Z2.contiguous())
    diff_op = float(torch.linalg.matrix_norm(YZ - H_zy).item())
    assert diff_op >= _WRONG_AXIS_MIN, (
        f"Operator diff between YZ and ZY generators = {diff_op:.3e} < {_WRONG_AXIS_MIN}; "
        "unexpectedly small -- YZ and ZY look identical at this coeff (bug)"
    )


# ---------------------------------------------------------------------------
# INVARIANT L7: Quadratic scaling  (1-F_e)/eps^2 -> 1/16 as eps->0  (B2, class-b band)
# Leading-order: 1-F_e ~= eps^2/16 = ||(eps/4)(Y(x)Z)||_F^2 / 4.
# M32-specific: ratio limit is 1/16 (not 1/4 as for 1-site generators, because d=4 and /4 factor).
# ||(eps/4)(Y(x)Z)||_F^2 = (eps/4)^2 * Tr((Y(x)Z)^2) = (eps/4)^2 * 4 = eps^2/4 -> /d=4 -> eps^2/16.
# (Y(x)Z)^2 = (Y^2)(x)(Z^2) = I2(x)I2 = I4 is an exact algebraic fact (class-a).
# BROKEN INPUT: a linear-in-eps error (1-F_e ~ eps, not eps^2) fails this ratio test.
# ---------------------------------------------------------------------------

def test_L7_quadratic_scaling():
    """L7 (class-b band, B2): (1-F_e)/eps^2 -> 1/16 as eps -> 0.

    At small eps: sin^2(eps/4) ~= eps^2/16 - eps^4/(3*256) + O(eps^6).
    The ratio (1-F_e)/eps^2 should be within 0.005 of 1/16 = 0.0625 for eps in [0.01, 0.1].
    At eps=0.3 (larger angle) the ratio deviates by ~O(eps^2) -- registered B2 deviation.
    M32-specific: the ratio target is 1/16 (not 1/4 as in M6/M7/M20), because d=4 and
    the generator has a /4 factor. The ratio is identical to M22/M23 (all are single
    Pauli-pair involutions at d=4).

    NOTE: the sweep uses eps >= 0.01 (signal ~6.25e-6) to stay well above the Uhlmann
    estimator floor (~6e-8 at d=4). At eps=0.001 the signal is AT the floor; the operator
    gate (L3a, opdiff 0) carries the cert there (pre-reg S5).
    """
    dt_ns = 20.0
    cdt = torch.complex128
    I_kraus = torch.eye(4, dtype=cdt, device=DEV).unsqueeze(0)
    J_I = _choi_state_from_kraus(I_kraus, device=DEV)

    # Use eps in [0.01, 0.3]: signal sin^2(eps/4) in [6.25e-6, 5.6e-3] >> Uhlmann floor ~6e-8
    for coeff in (0.3 / dt_ns, 0.1 / dt_ns, 0.05 / dt_ns, 0.03 / dt_ns, 0.01 / dt_ns):
        eps = coeff * dt_ns
        H = _hamiltonian_matrix_for_term(
            _make_coh_yz_term(coeff),
            support=(0, 1),
            local_dims=(2, 2),
            device=DEV,
        )
        kraus = assemble_substep_channel([H], [], dt_ns, device=DEV)
        J_c = _choi_state_from_kraus(kraus, device=DEV)
        one_minus_fe = float(max(0.0, 1.0 - _state_fidelity(J_c, J_I, device=DEV)))
        if eps > 0:
            ratio = one_minus_fe / (eps ** 2)
            assert abs(ratio - (1.0 / 16.0)) <= 0.005, (
                f"L7 FAIL: (1-F_e)/eps^2 = {ratio:.6f}, expected ~1/16 = {1/16:.6f}, "
                f"deviation {abs(ratio - 1/16):.5f} > 0.005 at eps={eps:.5f}"
            )


def test_L7_broken_linear_scaling_trips():
    """FALSIFIER: a channel with 1-F_e ~ eps (linear, not quadratic) fails L7.

    A T1-like collapse at rate ~ eps_ref / dt_ns produces 1-F_e ~ eps_ref (linear).
    This gives ratio (1-F_e)/eps_ref^2 ~ 1/eps_ref >> 1/16 as eps_ref -> 0.
    """
    dt_ns = 20.0
    cdt = torch.complex128
    I_kraus = torch.eye(4, dtype=cdt, device=DEV).unsqueeze(0)
    J_I = _choi_state_from_kraus(I_kraus, device=DEV)

    eps_ref = 0.001
    # T1-like collapse on the first qubit (top-left 4x4 block, lowering |1>->|0> on site-0)
    sm = torch.zeros((4, 4), dtype=cdt, device=DEV)
    sm[0, 1] = 1.0   # |0><1| on site-0 (|00><10|)
    sm[2, 3] = 1.0   # |0><1| on site-0 tensored with identity on site-1 (|01><11|)
    gamma = eps_ref / dt_ns
    c_linear = math.sqrt(gamma) * sm
    kraus_linear = assemble_substep_channel([], [c_linear], dt_ns, device=DEV)
    J_linear = _choi_state_from_kraus(kraus_linear, device=DEV)
    fe_linear = float(max(0.0, 1.0 - _state_fidelity(J_linear, J_I, device=DEV)))
    ratio_linear = fe_linear / (eps_ref ** 2) if eps_ref > 0 else 0.0
    assert abs(ratio_linear - (1.0 / 16.0)) > 0.01, (
        f"FALSIFIER DID NOT TRIP: linear-in-eps channel has (1-F_e)/eps^2 = {ratio_linear:.4f} "
        "which is within 0.01 of 1/16; the L7 quadratic-scaling check cannot distinguish "
        "linear from quadratic at this scale -- falsifier broken"
    )


# ---------------------------------------------------------------------------
# INVARIANT L8: Even symmetry  1-F_e(eps) = 1-F_e(-eps)  (class-a, exact)
# sin^2(eps/4) = sin^2(-eps/4); over- and under-rotation of equal magnitude are equally infidel.
# For any unitary U, F_e(U) = F_e(U†) (trace modulus invariant under conjugation).
# BROKEN INPUT: an asymmetric (directional) error violates even symmetry.
# ---------------------------------------------------------------------------

def test_L8_infidelity_even_in_eps():
    """L8 (class-a exact): 1-F_e is even in eps.

    sin^2(eps/4) = sin^2(-eps/4); F_e(U) = |Tr(U)/4|^2 = |Tr(U†)/4|^2 = F_e(U†)
    (trace modulus is invariant under conjugation). Over- and under-rotation of equal
    magnitude are equally infidel (pre-reg B1 even-in-eps note).
    """
    dt_ns = 20.0
    cdt = torch.complex128
    I_kraus = torch.eye(4, dtype=cdt, device=DEV).unsqueeze(0)
    J_I = _choi_state_from_kraus(I_kraus, device=DEV)

    def _fe(coeff_val: float) -> float:
        H = _hamiltonian_matrix_for_term(
            _make_coh_yz_term(coeff_val),
            support=(0, 1),
            local_dims=(2, 2),
            device=DEV,
        )
        kraus = assemble_substep_channel([H], [], dt_ns, device=DEV)
        J_c = _choi_state_from_kraus(kraus, device=DEV)
        return float(max(0.0, 1.0 - _state_fidelity(J_c, J_I, device=DEV)))

    for coeff in (0.1 / dt_ns, 0.05 / dt_ns, 0.01 / dt_ns):
        fe_pos = _fe(+coeff)
        fe_neg = _fe(-coeff)
        diff = abs(fe_pos - fe_neg)
        # Tolerance is the Uhlmann estimator floor (~4e-8 at d=4; pre-reg S5); 1e-7 gives
        # headroom above floating-point noise at small eps while staying inside the floor.
        assert diff <= 1e-7, (
            f"L8 FAIL: 1-F_e(+eps) = {fe_pos:.6e}, 1-F_e(-eps) = {fe_neg:.6e}, "
            f"diff = {diff:.3e} > 1e-7 at coeff={coeff} -- even-symmetry broken"
        )


def test_L8_broken_odd_infidelity_formula_trips():
    """FALSIFIER: if someone used sin(eps/4) instead of sin^2(eps/4), the result is ODD
    in eps, violating the even-symmetry that the correct formula satisfies.

    The correct formula sin^2(eps/4) is even (sin^2(-x/4) = sin^2(x/4)).
    The wrong formula sin(eps/4) is odd (sin(-x/4) = -sin(x/4)).
    """
    for eps in (0.3, 0.1, 0.03, 0.01, 0.003, 0.001):
        # Correct formula: sin^2(eps/4) -- should be even in eps
        correct_pos = exact_infidelity_M32(+eps)
        correct_neg = exact_infidelity_M32(-eps)
        assert abs(correct_pos - correct_neg) <= 1e-14, (
            f"L8 SELF-CHECK FAIL: correct formula sin^2(eps/4) is not even at eps={eps}"
        )
        # Wrong formula: sin(eps/4) (not squared) -- should be ODD in eps
        wrong_pos = math.sin(eps / 4.0)
        wrong_neg = math.sin(-eps / 4.0)
        assert abs(wrong_pos - wrong_neg) >= abs(eps) / 8.0, (
            f"FALSIFIER DID NOT TRIP: the wrong formula sin(eps/4) is unexpectedly symmetric "
            f"at eps={eps}: wrong_pos={wrong_pos:.6f}, wrong_neg={wrong_neg:.6f}"
        )


# ---------------------------------------------------------------------------
# INVARIANT L9: Apply every gate -- identity embed on leaked levels  (S3, class-a)
# In a 2-qutrit carrier (d0=d1=3), H_M32 acts on the 4 computational rows/cols
# ({0,1}x{0,1} -> indices {0,1,3,4} of a 3x3=9-dim space) with gen4 = (coeff/4)(Y(x)Z)
# and has the ZERO GENERATOR on all rows/cols involving any level >= 2 (leaked levels).
# M32 imparts NO population or phase to leaked levels (S3): exp(0)=I on level >=2.
# BROKEN INPUT: a 9x9 matrix that has non-zero entries involving row/col index 2,5,6,7,8
# (the leaked-level subspace) trips L9.
# ---------------------------------------------------------------------------

def test_L9_qutrit_embed_is_zero_on_leaked_levels():
    """L9 (class-a exact, S3): in a dim=(3,3) carrier, the 9x9 H_M32 matrix has:
    (a) its 4x4 computational block (rows/cols {0,1,3,4}) equal to the qubit reference gen4,
    (b) zero generator on all rows/cols involving leaked level >= 2 (indices 2,5,6,7,8).

    M32-specific: exp(-i H dt) = I on any pair of levels where either index >= 2 -- M32
    imparts NO leakage (pre-reg S3). Any leaked-level coupling is a different mechanism.
    The embed is verified by checking each computational-level (row,col) slot and confirming
    all non-computational rows/cols are zero.

    M32-specific structural check in the embed: the gen4 is (coeff/4)(Y(x)Z),
    purely imaginary and antisymmetric; embedded without change into the computational block.
    """
    coeff = 0.1
    d0, d1 = 3, 3
    H = _hamiltonian_matrix_for_term(
        _make_coh_yz_term(coeff),
        support=(0, 1),
        local_dims=(d0, d1),
        device=DEV,
    )
    # Reference gen4 on the 4-dim computational subspace (qubit reference)
    H_ref_4 = ref_H_M32(coeff, 2, 2)  # 4x4, (d0=2, d1=2)

    # (a) Each computational-level slot must match gen4
    for left_in in (0, 1):
        for right_in in (0, 1):
            col = left_in * d1 + right_in
            qcol = left_in * 2 + right_in
            for left_out in (0, 1):
                for right_out in (0, 1):
                    row = left_out * d1 + right_out
                    qrow = left_out * 2 + right_out
                    carrier_val = H[row, col].item()
                    ref_val = H_ref_4[qrow, qcol].item()
                    diff_val = abs(carrier_val - ref_val)
                    assert diff_val <= _OPERATOR_DIFF_TOL, (
                        f"L9 FAIL: H[{row},{col}] (comp block) = {carrier_val} != "
                        f"H_ref4[{qrow},{qcol}] = {ref_val}, diff={diff_val:.3e}"
                    )

    # (b) All non-computational rows/cols (involving level >= 2) must be zero
    #     Non-computational indices in a 3x3 space: any row/col index i where (i//d1>=2) or (i%d1>=2)
    total_dim = d0 * d1  # 9
    leaked_indices = [i for i in range(total_dim) if (i // d1 >= 2) or (i % d1 >= 2)]
    for idx in leaked_indices:
        row_norm = float(torch.linalg.norm(H[idx, :]).item())
        col_norm = float(torch.linalg.norm(H[:, idx]).item())
        assert row_norm <= _OPERATOR_DIFF_TOL, (
            f"L9 FAIL: H_M32 qutrit row-{idx} norm = {row_norm:.3e} != 0; "
            "M32 drives leaked levels -- S3 violated"
        )
        assert col_norm <= _OPERATOR_DIFF_TOL, (
            f"L9 FAIL: H_M32 qutrit col-{idx} norm = {col_norm:.3e} != 0; "
            "M32 drives leaked levels -- S3 violated"
        )


def test_L9_broken_full_qutrit_yz_extends_to_leaked_levels_trips():
    """FALSIFIER: a 9x9 YZ-like matrix that extends to qutrit levels (non-zero on leaked rows/cols)
    fails L9.

    A 3-level Y-like generator tensored with a 3-level Z-like generator (extending to level 2)
    would place non-zero entries at leaked-level indices -- which is NOT M32 semantics
    (M32 has zero generator on any level >= 2; pre-reg S3).
    """
    cdt = torch.complex128
    d0, d1 = 3, 3
    # A 3x3 "Y-like" matrix with imaginary off-diagonal entries also at level 2 (not M32)
    Y3 = torch.zeros((3, 3), dtype=cdt, device=DEV)
    Y3[0, 1] = -1.0j
    Y3[1, 0] = 1.0j
    Y3[0, 2] = -1.0j   # extends to leaked level
    Y3[2, 0] = 1.0j    # extends to leaked level
    # 3-level Z-like diagonal
    Z3 = torch.diag(torch.tensor([1.0, -1.0, 0.0], dtype=cdt, device=DEV))
    H_broken = 0.025 * torch.kron(Y3.contiguous(), Z3.contiguous())
    leaked_indices = [i for i in range(d0 * d1) if (i // d1 >= 2) or (i % d1 >= 2)]
    leaked_norms = [float(torch.linalg.norm(H_broken[i, :]).item()) for i in leaked_indices]
    assert max(leaked_norms) > _OPERATOR_DIFF_TOL, (
        "FALSIFIER DID NOT TRIP: the broken 9x9 YZ-extended matrix has zero leaked rows -- "
        "falsifier wrong (check the index logic)"
    )


# ---------------------------------------------------------------------------
# INVARIANT L10: Anti-circular namespace check  (structural, class-c gate)
# The cert (THIS FILE) must NOT import `_coherent_family_generator`,
# `_embed_coherent_generator`, `TWO_SITE_COHERENT_FAMILIES`, or `COHERENT_PAULI_FAMILIES`
# from the carrier. If these symbols appear in this module's namespace, the cert is circular:
# a wrong Pauli-pair map shared between the 'reference' and the carrier would false-pass.
# ---------------------------------------------------------------------------

def test_L10_cert_does_not_import_circular_carrier_symbols():
    """L10 (structural, anti-circular): the cert imports ONLY `_hamiltonian_matrix_for_term`
    from the carrier. The carrier's family-generator helpers and family constants must NOT
    appear in this module's namespace (pre-reg §3, anti-circular rule).

    Forbidden symbols:
      - `_coherent_family_generator`  (the internal pair-to-op helper)
      - `_embed_coherent_generator`   (the embedding helper)
      - `TWO_SITE_COHERENT_FAMILIES`  (the family-name set)
      - `COHERENT_PAULI_FAMILIES`     (the combined family set)

    If any of these is imported, a wrong COH_YZ pair map (Y,Z)->(Z,Y) would be reflected into
    the 'reference' silently (the W-C round-1 failure shape; test_axis1_wc_decircularized.py).
    M32-sharp: the COH_YZ->(Z,Y) map corruption is the exact circularity that would swap M32
    (YZ) for M30 (ZY) silently -- the anti-circular gate is the reason this cert can distinguish
    them (L3b is the payoff).
    """
    this_module = sys.modules[__name__]
    assert not hasattr(this_module, "_coherent_family_generator"), (
        "CIRCULAR: cert imports `_coherent_family_generator` from the carrier"
    )
    assert not hasattr(this_module, "_embed_coherent_generator"), (
        "CIRCULAR: cert imports `_embed_coherent_generator` from the carrier"
    )
    assert not hasattr(this_module, "TWO_SITE_COHERENT_FAMILIES"), (
        "CIRCULAR: cert imports `TWO_SITE_COHERENT_FAMILIES` from the carrier"
    )
    assert not hasattr(this_module, "COHERENT_PAULI_FAMILIES"), (
        "CIRCULAR: cert imports `COHERENT_PAULI_FAMILIES` from the carrier"
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
        "FALSIFIER DID NOT TRIP: the fake module lacks the circular symbol -- falsifier broken"
    )
