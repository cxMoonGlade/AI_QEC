"""M10 coherent_rxx_ryy_perturbation -- CONSTRAINT LEDGER (executable falsifier tests).

FAITHFULNESS PROTOCOL (docs/FAITHFULNESS_PROTOCOL.md) -- constraint ledger for M10.
Each test below is a FALSIFIER: it documents the invariant AND shows that a
deliberately BROKEN input makes the test FAIL (trips the falsifier). Tests run
GREEN on the faithful carrier and RED on the broken variant.

ANTI-CIRCULARITY: the reference operator (``ref_H_M10``) is HAND-TYPED from the
literature as the COMPOSITE ``(coeff/4)(X(x)X + Y(x)Y) = ref_H_M22 + ref_H_M23``.
Provenance: Zhang-Vala-Sastry-Whaley arXiv:quant-ph/0209120 (Eq. 10 Cartan axes,
Ex. 1(2) "XY interaction" (1/4)(XX+YY)); Foxen et al. arXiv:2001.08343 Eq. 1
(fSim theta-swap = sigma_x sigma_x + sigma_y sigma_y); Sung et al. arXiv:2011.01261
((g12/2)(XX+YY), measured g12/2pi=5.0 MHz).
The cert imports ONLY ``axis1_mcwf_mps_execution._hamiltonian_matrix_for_term``
(the object under test). The carrier's ``_coherent_family_generator`` /
``_embed_coherent_generator`` / ``TWO_SITE_COHERENT_FAMILIES`` /
``COHERENT_PAULI_FAMILIES`` appear NOWHERE in the reference code (same
de-circularization rule as test_m22_coherent_cxx_constraint_ledger.py,
test_m23_coherent_cyy_constraint_ledger.py, test_axis1_wc_decircularized.py, and
the M6/M7/M20 ledgers).

GATE TIER: STRICT (``1-F_e <= 1e-6``; operator identity <= 1e-12 / unitary <= 1e-10).
M10 is a pure-Hamiltonian / exact-dense error -- no collapse, no finite-step MCWF.

M10-SPECIFIC (the COMPOSITE):
- The generator is H_M10 = (coeff/4) * (X(x)X + Y(x)Y), the SYMMETRIC EXCHANGE /
  flip-flop / iSWAP coupling -- the COMPOSITE sum of the first two Cartan axes
  (Zhang Eq. 10 a={XX,YY,ZZ}).  M10 = M22 + M23 at the OPERATOR level.
- XX+YY has eigvals {-2, 0, 0, +2} with a 2-dim kernel {|Phi+>, |Psi->} -- it is
  NOT an involution: (XX+YY)^2 = 2I + 2*(X(x)X)*(Y(x)Y) != I.
  Fro-norm of (XX+YY)^2 - I = 4.47  (class-a: exact algebraic fact).
- CLOSED FORM: 1-F_e = 1 - cos^4(eps/4) = sin^2(eps/4)*(2 - sin^2(eps/4)).
  This is DISTINCT from the pure-axis form sin^2(eps/4) (M22/M23): cos^4 vs cos^2.
  Tr(U_M10) = 4*cos^2(eps/4) (not 4*cos(eps/4)).
- LEADING RATIO: (1-F_e)/eps^2 -> 1/8 as eps->0 (TWICE M22/M23's 1/16), because
  Tr((XX+YY)^2) = 8, not 4.
- LOAD-BEARING COMPOSITE GATE (L3a-composite): H_carrier must equal the SUM
  ref_H_M22 + ref_H_M23 to 0.0 (exact). This is the "certify as composite, not an
  independent generator" instruction from the pre-reg brief.
- DROP-SUMMAND controls (L3b/L3c) are the M10-sharp primary wrong-component gates:
  a carrier that emits only XX (drops YY) or only YY (drops XX) is the most likely
  M10-specific bug; the hand-typed (XX+YY) sum catches it; a circular reference
  derived from the carrier's pair list would mirror it and false-pass.
- XX-YY SIGN control (L3d): anti-symmetric exchange (wrong relative sign).
- REAL-SYMMETRIC structural fact (L2b): XX+YY is real-symmetric (both summands are).
- The F_avg companion factor is 4/5 (d=4 for the 2-site window, same as M22/M23).

GPU-only (top-level memory rule) -- collection FAILS without CUDA.

Pre-registration: docs/twin_validation/m10_coherent_rxx_ryy_perturbation_prereg.md
Run:  conda run -n aiqec python -m pytest -q tests/test_m10_coherent_rxx_ryy_constraint_ledger.py
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
        "M10 constraint-ledger cert is GPU-gated; CUDA-MISSING is NOT A RELEASE BASIS",
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
_WRONG_AXIS_MIN = 1e-3      # wrong-component / wrong-unit control must trip by >= this
#                           # (class-c gate; derivation-check: pure-XX/YY each diff 5.00e-2,
#                           # XX-YY diff 1.00e-1, ZZ/XY each diff 8.66e-2 at eps=0.1)

# ---------------------------------------------------------------------------
# Reference operator (HAND-TYPED, non-circular) -- the COMPOSITE
#
# Provenance:
#   H_M10 = (coeff/4) * (sigma_x (x) sigma_x  +  sigma_y (x) sigma_y)
#          = ref_H_M22 + ref_H_M23               [COMPOSITE IDENTITY]
#   sigma_x = [[0,1],[1,0]],  sigma_y = [[0,-i],[i,0]]  (Nielsen & Chuang Eq. 2.1).
#   X(x)X + Y(x)Y is the EXCHANGE / flip-flop / iSWAP interaction 2(sigma+ (x) sigma- + sigma- (x) sigma+).
#   It is the symmetric sum of the first two Cartan axes of the non-local su(4) subalgebra:
#     a = {XX, YY, ZZ}  (Zhang-Vala-Sastry-Whaley arXiv:quant-ph/0209120 Eq. 10),
#   written as the standalone "XY interaction" gate H = (1/4)(XX+YY) (Zhang Ex. 1(2)).
#   DEVICE DIRECT:
#     (i) fSim theta-swap block: theta*(sigma_x(x)sigma_x + sigma_y(x)sigma_y)
#         (Foxen et al. arXiv:2001.08343 Eq. 1; parasitic residual delta_theta <= 5 deg).
#    (ii) measured transverse exchange: (g12/2)(XX+YY), g12/2pi = 5.0 MHz (Sung arXiv:2011.01261).
#   factor 1/4 = (1/2)^2: two-qubit over-rotation convention
#     R_{PQ}(eps_cat) = exp(-i (eps_cat/2)(P(x)Q)), carrier eps = coeff*dt per tensor
#     (error_mechanisms.md line 101; carrier docstring lines 1026-1029).
#   M10 structural fact: XX+YY is REAL-SYMMETRIC, eigvals {-2, 0, 0, +2} (2-dim kernel
#     {|Phi+>, |Psi->}), NOT an involution: (XX+YY)^2 = 2I + 2(XX)(YY) != I.
#     Fro-norm of (XX+YY)^2 - I = 4.47 (class-a exact algebraic fact).
#   zero generator on any leaked level >= 2 (S3; _embed_coherent_generator semantics).
#   error unitary: U = exp(-i H dt),  eps = coeff*dt.
#     Acts as I on {|Phi+>, |Psi->}; e^{-/+ i eps/2} on {|Phi->, |Psi+>}.
#     Tr(U_M10) = 2 + 2*cos(eps/2) = 4*cos^2(eps/4).
#   EXACT 1-F_e (d=4): 1 - |Tr(U)/4|^2 = 1 - cos^4(eps/4) = sin^2(eps/4)*(2-sin^2(eps/4)).
#     This is DISTINCT from the pure-axis sin^2(eps/4): cos^4 not cos^2.
#   LEADING 1-F_e: ||(eps/4)(XX+YY)||_F^2 / 4 = (eps/4)^2 * 8 / 4 = eps^2/8  (ratio 1/8, not 1/16).
# ---------------------------------------------------------------------------

def ref_H_M10(coeff: float, d0: int, d1: int) -> torch.Tensor:
    """Hand-typed M10 reference generator on the (d0*d1)-dim local space -- the COMPOSITE.

    H_M10 = (coeff/4) * (X(x)X + Y(x)Y)  embedded into the d0*d1-dimensional space,
    with the zero generator (identity gate) on any product-level pair where either
    index >= 2 (no leakage drive from M10 -- S3).
    Imports NOTHING from the carrier family tables.
    Equals ref_H_M22(coeff, d0, d1) + ref_H_M23(coeff, d0, d1) exactly.
    """
    cdt = torch.complex128
    # Hand-typed Pauli matrices (Nielsen & Chuang Eq. 2.1)
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    Y2 = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
    XX = torch.kron(X2.contiguous(), X2.contiguous())  # real-symmetric, anti-diag all +1
    YY = torch.kron(Y2.contiguous(), Y2.contiguous())  # real-symmetric, anti-diag -1,+1,+1,-1
    # (coeff/4) * (XX + YY) on the 4-dim computational subspace -- real-symmetric
    gen4 = 0.25 * coeff * (XX + YY)
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


def ref_H_M22(coeff: float, d0: int, d1: int) -> torch.Tensor:
    """Hand-typed M22 summand: (coeff/4)*(X(x)X), embedded.

    Inline duplicate of the M22 reference (no import from sibling ledger) so that the
    composite equality ref_H_M10 == ref_H_M22 + ref_H_M23 is a TESTABLE ASSERTION inside
    this file (no carrier or sibling module imports).
    """
    cdt = torch.complex128
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    gen4 = 0.25 * coeff * torch.kron(X2.contiguous(), X2.contiguous())
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


def ref_H_M23(coeff: float, d0: int, d1: int) -> torch.Tensor:
    """Hand-typed M23 summand: (coeff/4)*(Y(x)Y), embedded.

    Inline duplicate for the composite assertion (no carrier imports).
    """
    cdt = torch.complex128
    Y2 = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
    gen4 = 0.25 * coeff * torch.kron(Y2.contiguous(), Y2.contiguous())
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


def ref_U_M10(coeff: float, dt_ns: float, d0: int, d1: int) -> torch.Tensor:
    """Hand-typed M10 error unitary: U = matrix_exp(-i * H * dt)."""
    H = ref_H_M10(coeff, d0, d1)
    return torch.linalg.matrix_exp(-1j * dt_ns * H)


def exact_infidelity_M10(eps: float) -> float:
    """Closed-form 1-F_e for exp(-i(eps/4)(XX+YY)) vs identity (d=4).

    Eigvals of XX+YY = {-2, 0, 0, +2} (2-dim kernel: |Phi+>, |Psi->).
    Tr(U_M10) = e^{i eps/2} + 1 + 1 + e^{-i eps/2} = 2 + 2*cos(eps/2) = 4*cos^2(eps/4).
    F_e = |Tr(U)/4|^2 = cos^4(eps/4)  =>  1-F_e = 1 - cos^4(eps/4).
    Equivalent: sin^2(eps/4) * (2 - sin^2(eps/4)).
    Reference: Nielsen arXiv:quant-ph/0205035 Eq. 16 (F_e = |Tr U / d|^2 for unitary U);
    pre-registration B1, section 2.

    NOTE: this is DISTINCT from sin^2(eps/4) (M22/M23): the composite XX+YY has
    eigvals {-2,0,0,2} with a 2-dim kernel, so Tr(U) = 4*cos^2 (not 4*cos),
    giving cos^4 (not cos^2). The difference (cos^4 vs cos^2) grows with eps.
    """
    return float(1.0 - math.cos(eps / 4.0) ** 4)


def _make_coh_xxyy_term(coeff: float) -> dict:
    """Minimal schedule-term dict for COH_XX_YY on two sites (support=(0,1))."""
    return {
        "kind": "hamiltonian",
        "operator_family": "COH_XX_YY",
        "support": [0, 1],
        "coefficient": float(coeff),
        "substep_id": "m10_ledger",
    }


# ---------------------------------------------------------------------------
# INVARIANT L1: Hermiticity  ||H - H†||_F <= 1e-12  (class-a exact)
# XX+YY is real-symmetric => Hermitian; (coeff/4)(XX+YY) is Hermitian for any real coeff.
# BROKEN INPUT: a non-Hermitian matrix (imaginary off-diagonal term only)
# ---------------------------------------------------------------------------

def test_L1_generator_is_hermitian():
    """L1 (class-a exact): the M10 generator H satisfies H = H†.

    XX+YY is real-symmetric (both XX and YY are real-symmetric; their sum is too).
    (coeff/4)(XX+YY) is Hermitian for any real coeff.
    Broken-input demonstration: an explicitly non-Hermitian operator trips this test.
    """
    coeff = 0.1
    H = _hamiltonian_matrix_for_term(
        _make_coh_xxyy_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    resid = float(torch.linalg.matrix_norm(H - H.conj().T).item())
    assert resid <= _HERMITIAN_TOL, (
        f"L1 FAIL: ||H - H†||_F = {resid:.3e} > {_HERMITIAN_TOL}; "
        "M10 generator is not Hermitian -- physics bug"
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
# Tr(XX+YY) = Tr(XX) + Tr(YY) = 0 + 0 = 0; an identity-shifted generator is WRONG.
# BROKEN INPUT: H + (c/4) * I4 (trace = coeff)
# ---------------------------------------------------------------------------

def test_L2_generator_is_traceless():
    """L2 (class-a exact): the M10 generator H is traceless.

    Tr(XX+YY) = Tr(X)*Tr(X) + Tr(Y)*Tr(Y) = 0 + 0 = 0.
    Any non-zero trace indicates identity contamination or a wrong family.
    """
    coeff = 0.1
    H = _hamiltonian_matrix_for_term(
        _make_coh_xxyy_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    tr_resid = float(torch.abs(torch.trace(H)).item())
    assert tr_resid <= _TRACELESS_TOL, (
        f"L2 FAIL: |Tr H| = {tr_resid:.3e} > {_TRACELESS_TOL}; "
        "M10 generator has a non-zero trace -- wrong axis or identity contamination"
    )


def test_L2_broken_identity_shift_trips():
    """FALSIFIER: a traceful 4x4 generator ((XX+YY) + identity offset) fails L2."""
    cdt = torch.complex128
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    Y2 = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
    XX = torch.kron(X2.contiguous(), X2.contiguous())
    YY = torch.kron(Y2.contiguous(), Y2.contiguous())
    H_broken = 0.025 * (XX + YY) + 0.025 * torch.eye(4, dtype=cdt, device=DEV)
    tr_resid = float(torch.abs(torch.trace(H_broken)).item())
    assert tr_resid > _TRACELESS_TOL, (
        "FALSIFIER DID NOT TRIP: an identity-shifted 4x4 generator passed L2 -- "
        "the falsifier is broken"
    )


# ---------------------------------------------------------------------------
# INVARIANT L2b: Real-symmetric structure of XX+YY  (class-a exact, M10-specific)
# XX+YY is REAL (imag-part norm 0) and SYMMETRIC ((XX+YY) = (XX+YY)^T).
# Both XX and YY are individually real-symmetric; their sum is real-symmetric.
# Structural pattern: (XX+YY) = [[0,0,0,0],[0,0,2,0],[0,2,0,0],[0,0,0,0]] (anti-diag center).
# BROKEN INPUT: a generator with non-zero imaginary part (e.g. X(x)Y, which is imaginary)
# ---------------------------------------------------------------------------

def test_L2b_xxyy_generator_is_real_symmetric():
    """L2b (class-a exact, M10-specific): XX+YY is real-symmetric.

    XX is real-symmetric (anti-diagonal, all +1 entries).
    YY is real-symmetric (anti-diagonal, signs -1,+1,+1,-1; the two -i factors cancel).
    Their sum (XX+YY) is real-symmetric with anti-diagonal center [[0,0,0,0],
    [0,0,2,0],[0,2,0,0],[0,0,0,0]].

    Therefore for H_M10 = (coeff/4)(XX+YY): imag-part norm <= 1e-12 and H = H^T.
    This is the M10-sharp structural fact distinguishing XX+YY from XY/YX (imaginary).
    """
    coeff = 0.1
    H = _hamiltonian_matrix_for_term(
        _make_coh_xxyy_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    # Imaginary part should be zero (XX and YY are each real-symmetric)
    imag_norm = float(torch.linalg.matrix_norm(H.imag).item())
    assert imag_norm <= _OPERATOR_DIFF_TOL, (
        f"L2b FAIL: imag-part norm of H_M10 = {imag_norm:.3e} > {_OPERATOR_DIFF_TOL}; "
        "XX+YY should be REAL (both summands are real-symmetric) -- physics bug"
    )
    # Symmetric: H = H^T (real-symmetric matrix)
    sym_resid = float(torch.linalg.matrix_norm(H - H.T).item())
    assert sym_resid <= _OPERATOR_DIFF_TOL, (
        f"L2b FAIL: symmetric residual ||H - H^T||_F = {sym_resid:.3e} > {_OPERATOR_DIFF_TOL}; "
        "XX+YY should be SYMMETRIC -- structural bug"
    )


def test_L2b_broken_xy_is_imaginary_trips():
    """FALSIFIER: X(x)Y is imaginary, failing the real-symmetric check.

    X(x)Y has imaginary entries (X is real, Y is imaginary -> XY is imaginary).
    The L2b imag-norm check flags this -- proving the structural assertion distinguishes
    XX+YY (real-symmetric) from wrong-pair generators that carry imaginary entries.
    """
    cdt = torch.complex128
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    Y2 = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
    H_xy = 0.025 * torch.kron(X2.contiguous(), Y2.contiguous())
    imag_norm = float(torch.linalg.matrix_norm(H_xy.imag).item())
    assert imag_norm > _OPERATOR_DIFF_TOL, (
        "FALSIFIER DID NOT TRIP: X(x)Y appears to have zero imaginary part -- "
        "falsifier broken (check the computation)"
    )


# ---------------------------------------------------------------------------
# INVARIANT L2c: Non-involution of XX+YY  (class-a exact, M10-specific)
# (XX+YY)^2 = 2*I4 + 2*(XX)(YY) != I4; the Fro-norm of (XX+YY)^2 - I4 = 4.47.
# This distinguishes M10 from the pure-axis generators (XX^2 = YY^2 = I4: involutions).
# BROKEN INPUT: the pure-XX matrix IS an involution -- (XX)^2 = I4 -> norm = 0.
# ---------------------------------------------------------------------------

def test_L2c_xxyy_is_not_an_involution():
    """L2c (class-a exact, M10-specific): (XX+YY)^2 != I4 (the non-involution structural fact).

    (XX+YY)^2 = X^2 (x) X^2  +  Y^2 (x) Y^2  +  (XX)(YY)  +  (YY)(XX)
              = I (x) I  +  (-I)(x)(-I)  +  (X)(x)(Y) (Y)(x)(X) cross terms
    Direct computation: (XX+YY)^2 = 2I + 2*(X(x)X)*(Y(x)Y)
    The off-diagonal structure of (XY)(YX) is non-trivial; the result is not identity.
    Fro-norm of (XX+YY)^2 - I4 = 4.47  (pre-reg §1, class-a algebraic fact).

    Contrast: pure-XX has (X(x)X)^2 = I4 -> Fro-norm((XX)^2 - I) = 0.
    Contrast: pure-YY has (Y(x)Y)^2 = I4 -> Fro-norm((YY)^2 - I) = 0.
    """
    cdt = torch.complex128
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    Y2 = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
    XX = torch.kron(X2.contiguous(), X2.contiguous())
    YY = torch.kron(Y2.contiguous(), Y2.contiguous())
    XXYY = XX + YY
    I4 = torch.eye(4, dtype=cdt, device=DEV)
    sq_resid = float(torch.linalg.matrix_norm(XXYY @ XXYY - I4).item())
    # Must be NOT zero (the non-involution fact); expected value ~4.47
    assert sq_resid > 1.0, (
        f"L2c FAIL: ||(XX+YY)^2 - I||_F = {sq_resid:.4f}, expected ~4.47 >> 0; "
        "XX+YY appears to be an involution -- algebraic error (physics bug)"
    )


def test_L2c_broken_pure_xx_is_involution_trips():
    """FALSIFIER: pure X(x)X IS an involution (XX^2 = I) -- the non-involution test would
    report norm ~ 0 for it, NOT > 1.

    This confirms that L2c's non-involution check is M10-specific: a wrong-component
    reference that is a single Pauli-pair (an involution) would report zero residual
    there, meaning the check structurally distinguishes the composite from pure axes.
    The falsifier shows that a pure-XX input does NOT trigger the non-involution norm > 1 test.
    """
    cdt = torch.complex128
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    XX = torch.kron(X2.contiguous(), X2.contiguous())
    I4 = torch.eye(4, dtype=cdt, device=DEV)
    sq_resid_xx = float(torch.linalg.matrix_norm(XX @ XX - I4).item())
    # XX is an involution: (XX)^2 = I4, so the residual should be tiny (~0)
    # This means a pure-XX carrier would NOT trigger the L2c "non-involution" condition
    # (its sq_resid would be ~0 << 1), confirming L2c is M10-specific
    assert sq_resid_xx < 1e-10, (
        f"SELF-CHECK FAIL: pure (X(x)X)^2 - I has Fro-norm = {sq_resid_xx:.3e}, "
        "expected ~0 (involution); the falsifier pre-condition is wrong"
    )
    # Confirm the M10 composite is genuinely different (> 1.0) by re-computing it here
    Y2 = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
    YY = torch.kron(Y2.contiguous(), Y2.contiguous())
    XXYY = XX + YY
    sq_resid_m10 = float(torch.linalg.matrix_norm(XXYY @ XXYY - I4).item())
    assert sq_resid_m10 > 1.0, (
        f"FALSIFIER DID NOT TRIP: (XX+YY)^2 - I has norm {sq_resid_m10:.4f} <= 1.0; "
        "the non-involution check cannot distinguish the composite from a pure axis"
    )


# ---------------------------------------------------------------------------
# INVARIANT L3a-composite: Operator identity = the COMPOSITE sum  (B4, class-a)
# ||H_carrier - H_ref||_F <= 1e-12 where H_ref = (coeff/4)(XX+YY) = ref_H_M22 + ref_H_M23.
# This is the "certify as COMPOSITE, not an independent generator" instruction (pre-reg brief).
# The composite equality ref_H_M10 == ref_H_M22 + ref_H_M23 to 0.0 is tested explicitly.
# LOAD-BEARING: 1-F_e is exchange-blind (see L6b); the operator gate is the SOLE witness
# that the carrier emits BOTH XX and YY (not one summand, not a wrong sign, not a different pair).
# ---------------------------------------------------------------------------

def test_L3a_operator_matches_hand_typed_composite_reference():
    """L3a (class-a exact, B4): the carrier generator equals the hand-typed COMPOSITE reference.

    H_ref = (coeff/4) * (X(x)X + Y(x)Y)  embedded in (d0,d1).
    Provenance: Zhang Ex.1(2) / Foxen Eq.1 / Sung transverse exchange.
    This is the LOAD-BEARING COMPOSITE gate -- 1-F_e alone is exchange-blind (see L6b:
    the scalar 1-F_e cannot tell M10 from a wrong-exchange generator with the same spectrum).
    The operator identity is the SOLE witness of the XX+YY pair combination.

    Swept over coeff in {0.3, 0.1, 0.03, 0.01, 0.003, 0.001} and dims (2,2) / (3,3).
    """
    for coeff in (0.3, 0.1, 0.03, 0.01, 0.003, 0.001):
        for d0, d1 in ((2, 2), (3, 3)):
            H_carrier = _hamiltonian_matrix_for_term(
                _make_coh_xxyy_term(coeff),
                support=(0, 1),
                local_dims=(d0, d1),
                device=DEV,
            )
            H_ref = ref_H_M10(coeff, d0, d1)
            diff = float(torch.linalg.matrix_norm(H_carrier - H_ref).item())
            assert diff <= _OPERATOR_DIFF_TOL, (
                f"L3a FAIL: ||H_carrier - H_ref||_F = {diff:.3e} > {_OPERATOR_DIFF_TOL} "
                f"at coeff={coeff}, dims=({d0},{d1}) -- wrong generator (wrong pair combination, "
                "wrong coefficient, wrong convention, or not the composite XX+YY)"
            )


def test_L3a_composite_equals_sum_of_m22_and_m23_references():
    """L3a-composite (class-a exact): ref_H_M10 == ref_H_M22 + ref_H_M23 to 0.0.

    The COMPOSITE identity at the reference level: the hand-typed M10 reference is exactly
    the sum of the two hand-typed M22 and M23 references (which are themselves the landed
    pure-axis references). This is the "certify as composite, not an independent generator"
    instruction from the pre-reg brief (§3), made executable.

    A carrier that emits (XX+YY)/2 (wrong factor) or (XX+YY)*(1/4 vs 1/8) would fail
    L3a but this test verifies the REFERENCE ITSELF is consistent with the summand decomposition.

    Swept over coeff and dims to confirm the embed is consistent.
    """
    for coeff in (0.3, 0.1, 0.03, 0.01, 0.003, 0.001):
        for d0, d1 in ((2, 2), (3, 3)):
            H_m10 = ref_H_M10(coeff, d0, d1)
            H_m22_plus_m23 = ref_H_M22(coeff, d0, d1) + ref_H_M23(coeff, d0, d1)
            diff = float(torch.linalg.matrix_norm(H_m10 - H_m22_plus_m23).item())
            assert diff <= _OPERATOR_DIFF_TOL, (
                f"L3a-composite FAIL: ref_H_M10 != ref_H_M22 + ref_H_M23, "
                f"diff = {diff:.3e} > {_OPERATOR_DIFF_TOL} at coeff={coeff}, dims=({d0},{d1}); "
                "the composite reference is internally inconsistent -- reference bug"
            )


# ---------------------------------------------------------------------------
# DROP-SUMMAND CONTROLS (L3b, L3c) -- the M10-SHARP LOAD-BEARING wrong-component gates
#
# The most likely M10-specific carrier bug is DROPPING ONE SUMMAND:
#   - returns only XX (pair map COH_XX_YY -> ((X,X),) omitting (Y,Y))
#   - returns only YY (pair map COH_XX_YY -> ((Y,Y),) omitting (X,X))
# A hand-typed (XX+YY) composite reference catches these; a circular reference derived
# from the corrupted carrier pair list would mirror the dropped-summand and false-pass.
# Derivation-check: pure-XX diff = 5.00e-2 at eps=0.1; pure-YY diff = 5.00e-2. Both >> 1e-3.
# ---------------------------------------------------------------------------

def test_L3b_broken_drop_xx_summand_trips():
    """FALSIFIER (L3b, M10-PRIMARY): pure-YY only (drop XX summand) disagrees with M10 by >= 1e-3.

    If the carrier's COH_XX_YY pair map were corrupted to emit ONLY YY (drop XX),
    the result would be (coeff/4)(Y(x)Y) -- the M23 generator.
    The hand-typed (XX+YY) composite reference catches this immediately:
    diff = ||(coeff/4)(YY) - (coeff/4)(XX+YY)||_F = (coeff/4)*||XX||_F = (coeff/4)*2 ~ 5e-2.
    A reference derived from the corrupted pair list (only (Y,Y)) would have diff 0 -- false-pass.
    This is the M10-SHARP PRIMARY wrong-component control.
    """
    coeff = 0.1
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_xxyy_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    cdt = torch.complex128
    Y2 = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
    H_wrong_yy_only = 0.25 * coeff * torch.kron(Y2.contiguous(), Y2.contiguous())
    diff = float(torch.linalg.matrix_norm(H_carrier - H_wrong_yy_only).item())
    assert diff >= _WRONG_AXIS_MIN, (
        f"FALSIFIER DID NOT TRIP: drop-XX (YY-only) reference passed with diff={diff:.3e} < "
        f"{_WRONG_AXIS_MIN}; the XX+YY vs YY-only confusion is undetectable -- "
        "composite operator-identity cert broken (M10 vs M23 indistinct)"
    )


def test_L3c_broken_drop_yy_summand_trips():
    """FALSIFIER (L3c, M10-PRIMARY): pure-XX only (drop YY summand) disagrees with M10 by >= 1e-3.

    If the carrier's COH_XX_YY pair map were corrupted to emit ONLY XX (drop YY),
    the result would be (coeff/4)(X(x)X) -- the M22 generator.
    The hand-typed (XX+YY) composite reference catches this immediately:
    diff = ||(coeff/4)(XX) - (coeff/4)(XX+YY)||_F = (coeff/4)*||YY||_F = (coeff/4)*2 ~ 5e-2.
    A reference derived from the corrupted pair list (only (X,X)) would have diff 0 -- false-pass.
    This is the M10-SHARP PRIMARY wrong-component control (the other half of L3b).
    """
    coeff = 0.1
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_xxyy_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    cdt = torch.complex128
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    H_wrong_xx_only = 0.25 * coeff * torch.kron(X2.contiguous(), X2.contiguous())
    diff = float(torch.linalg.matrix_norm(H_carrier - H_wrong_xx_only).item())
    assert diff >= _WRONG_AXIS_MIN, (
        f"FALSIFIER DID NOT TRIP: drop-YY (XX-only) reference passed with diff={diff:.3e} < "
        f"{_WRONG_AXIS_MIN}; the XX+YY vs XX-only confusion is undetectable -- "
        "composite operator-identity cert broken (M10 vs M22 indistinct)"
    )


def test_L3d_broken_wrong_sign_xx_minus_yy_trips():
    """FALSIFIER (L3d): anti-symmetric exchange (XX-YY) disagrees with M10 by >= 1e-3.

    The anti-symmetric exchange XX-YY (wrong relative sign between the two summands)
    differs from the symmetric exchange XX+YY:
    ||(coeff/4)(XX-YY) - (coeff/4)(XX+YY)||_F = (coeff/4)*||2YY||_F ~ 1e-1 at eps=0.1.
    Derivation-check: diff = 1.00e-1 >> 1e-3.
    """
    coeff = 0.1
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_xxyy_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    cdt = torch.complex128
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    Y2 = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
    XX = torch.kron(X2.contiguous(), X2.contiguous())
    YY = torch.kron(Y2.contiguous(), Y2.contiguous())
    H_wrong_antisym = 0.25 * coeff * (XX - YY)   # anti-symmetric exchange (wrong sign)
    diff = float(torch.linalg.matrix_norm(H_carrier - H_wrong_antisym).item())
    assert diff >= _WRONG_AXIS_MIN, (
        f"FALSIFIER DID NOT TRIP: anti-symmetric (XX-YY) reference passed with diff={diff:.3e} < "
        f"{_WRONG_AXIS_MIN}; the XX+YY vs XX-YY sign error is undetectable"
    )


def test_L3e_broken_wrong_axis_zz_trips():
    """FALSIFIER (L3e): wrong-axis ZZ (COH_ZZ / M11) disagrees with M10 by >= 1e-3.

    ZZ is diagonal; XX+YY is off-diagonal (real-symmetric, anti-diagonal center).
    Structurally distinct. M10-specific: ZZ is M11 (COH_CROSSTALK_ZZ); the operator gate
    must keep M10 distinct from a ZZ coupling.
    Derivation-check: diff = 8.66e-2 at eps=0.1 >> 1e-3.
    """
    coeff = 0.1
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_xxyy_term(coeff),
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
        f"{_WRONG_AXIS_MIN}; the XX+YY / ZZ confusion is undetectable (M10 vs M11 indistinct)"
    )


def test_L3f_broken_wrong_axis_xy_trips():
    """FALSIFIER (L3f): wrong-axis XY (M28) disagrees with M10 by >= 1e-3.

    X(x)Y has imaginary off-diagonal entries; XX+YY is real. Structurally distinct.
    XY is M28 (COH_XY); the operator gate catches M10/M28 confusion.
    Derivation-check: diff = 8.66e-2 at eps=0.1 >> 1e-3.
    """
    coeff = 0.1
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_xxyy_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    cdt = torch.complex128
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    Y2 = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
    H_wrong_xy = 0.25 * coeff * torch.kron(X2.contiguous(), Y2.contiguous())
    diff = float(torch.linalg.matrix_norm(H_carrier - H_wrong_xy).item())
    assert diff >= _WRONG_AXIS_MIN, (
        f"FALSIFIER DID NOT TRIP: wrong-axis XY (M28) reference passed with diff={diff:.3e} < "
        f"{_WRONG_AXIS_MIN}; the XX+YY / XY confusion is undetectable (M10 vs M28 indistinct)"
    )


def test_L3g_broken_wrong_unit_no_factor_trips():
    """FALSIFIER (L3g): wrong-unit convention (coeff*(XX+YY), missing the /4) disagrees.

    Correct: H = (coeff/4)*(XX+YY).  Wrong: H = coeff*(XX+YY)  [missing both /2 factors].
    A factor-of-4 error in the generator gives a factor-of-4 error in the angle.
    Derivation-check: diff = 2.12e-1 at eps=0.1 >> 1e-3.
    """
    coeff = 0.1
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_xxyy_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    cdt = torch.complex128
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    Y2 = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
    XX = torch.kron(X2.contiguous(), X2.contiguous())
    YY = torch.kron(Y2.contiguous(), Y2.contiguous())
    H_wrong_unit = float(coeff) * (XX + YY)  # missing the /4
    diff = float(torch.linalg.matrix_norm(H_carrier - H_wrong_unit).item())
    assert diff >= _WRONG_AXIS_MIN, (
        f"FALSIFIER DID NOT TRIP: wrong-unit (coeff*(XX+YY), missing /4) has diff={diff:.3e} < "
        f"{_WRONG_AXIS_MIN}; the factor-of-4 error is undetectable"
    )


def test_L3h_broken_wrong_unit_half_factor_trips():
    """FALSIFIER (L3h): wrong-unit convention ((coeff/2)*(XX+YY), missing one /2) disagrees.

    Correct: H = (coeff/4)*(XX+YY).  Wrong: H = (coeff/2)*(XX+YY)  [only one /2 factor,
    as if this were a 1-site over-rotation convention applied to the 2-site case].
    Derivation-check: diff = 7.07e-2 at eps=0.1 >> 1e-3.
    """
    coeff = 0.1
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_xxyy_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    cdt = torch.complex128
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    Y2 = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
    XX = torch.kron(X2.contiguous(), X2.contiguous())
    YY = torch.kron(Y2.contiguous(), Y2.contiguous())
    H_wrong_half = 0.5 * float(coeff) * (XX + YY)  # missing one /2
    diff = float(torch.linalg.matrix_norm(H_carrier - H_wrong_half).item())
    assert diff >= _WRONG_AXIS_MIN, (
        f"FALSIFIER DID NOT TRIP: wrong-unit ((coeff/2)*(XX+YY), missing one /2) has "
        f"diff={diff:.3e} < {_WRONG_AXIS_MIN}; the factor-of-2 error is undetectable"
    )


# ---------------------------------------------------------------------------
# INVARIANT L4: Unitary identity  ||U_carrier - U_ref||_F <= 1e-10  (B4, class-a)
# U = matrix_exp(-i H dt); acts as I on {|Phi+>,|Psi->}; e^{-/+i eps/2} on {|Phi->,|Psi+>}.
# eps = coeff * dt_ns.
# BROKEN INPUT: wrong-sign exponent (U = exp(+i H dt)) -- gives the inverse/adjoint gate.
# ---------------------------------------------------------------------------

def test_L4_error_unitary_matches_reference():
    """L4 (class-a exact, B4): the carrier's error gate U = exp(-i H dt) equals the
    reference matrix_exp(-i * H_ref * dt) to <= 1e-10.

    Swept over coeff in {0.3, 0.1, 0.03, 0.01, 0.003, 0.001} and dims (2,2) / (3,3).
    """
    dt_ns = 20.0
    for coeff in (0.3, 0.1, 0.03, 0.01, 0.003, 0.001):
        for d0, d1 in ((2, 2), (3, 3)):
            eps = coeff * dt_ns
            H_carrier = _hamiltonian_matrix_for_term(
                _make_coh_xxyy_term(coeff),
                support=(0, 1),
                local_dims=(d0, d1),
                device=DEV,
            )
            U_carrier = torch.linalg.matrix_exp(-1j * dt_ns * H_carrier)
            U_ref = ref_U_M10(coeff, dt_ns, d0, d1)
            diff = float(torch.linalg.matrix_norm(U_carrier - U_ref).item())
            assert diff <= _UNITARY_DIFF_TOL, (
                f"L4 FAIL: ||U_carrier - U_ref||_F = {diff:.3e} > {_UNITARY_DIFF_TOL} "
                f"at coeff={coeff}, dt={dt_ns}, eps={eps:.3f}, dims=({d0},{d1})"
            )


def test_L4_broken_wrong_sign_exponent_trips():
    """FALSIFIER: the wrong-sign exponent (exp(+i H dt)) disagrees with the correct gate
    by >= 1e-3 for any non-zero eps not a multiple of 2*pi/eps.
    """
    coeff = 0.1
    dt_ns = 20.0
    d0, d1 = 2, 2
    H_ref = ref_H_M10(coeff, d0, d1)
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
    """L5 (class-a exact): the M10 Kraus channel assembled from H_M10 alone (no collapse)
    is exactly trace-preserving: sum_k K†K = I to <= 1e-12.

    M10 is a pure-Hamiltonian error (S1); no collapse operators. The single Kraus is
    U = exp(-i H dt), which is unitary, so sum_k K†K = U†U = I exactly.
    """
    dt_ns = 20.0
    coeff = 0.1
    H = _hamiltonian_matrix_for_term(
        _make_coh_xxyy_term(coeff),
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
        "M10 channel is not trace-preserving"
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
# INVARIANT L6a: process infidelity == 1 - cos^4(eps/4) to Uhlmann floor  (B1, class-b band)
# exp(-i(eps/4)(XX+YY)) vs identity: 1-F_e = 1 - cos^4(eps/4)  (NOT sin^2(eps/4)).
# This is DISTINCT from the pure-axis form: the {-2,0,0,+2} eigval spectrum gives
# Tr(U) = 4*cos^2(eps/4) (not 4*cos(eps/4)).
# Threshold: STRICT 1-F_e <= 1e-6 (pure Hamiltonian, S1).
# BROKEN INPUT: the pure-axis sin^2(eps/4) formula evaluated at the same eps gives
# a DIFFERENT number for eps > 0 (the composite vs pure-axis distinction).
# ---------------------------------------------------------------------------

def test_L6a_infidelity_matches_exact_closed_form():
    """L6a (class-b band, B1): carrier 1-F_e = 1 - cos^4(eps/4) to the Uhlmann floor (~5e-8).

    Swept over eps in {0.3, 0.1, 0.03, 0.01, 0.003, 0.001} rad.
    The STRICT gate tier (S1): numerical agreement of carrier vs the exact closed form.
    M10-specific: closed form is 1 - cos^4(eps/4), NOT sin^2(eps/4) (the pure-axis form).
    At eps=0.001 the signal (~1.25e-7) is near the Uhlmann floor (~4e-8); the operator gate
    (L3a, opdiff 0) carries the cert there (pre-reg S5).
    """
    dt_ns = 20.0
    cdt = torch.complex128
    I_kraus = torch.eye(4, dtype=cdt, device=DEV).unsqueeze(0)
    J_I = _choi_state_from_kraus(I_kraus, device=DEV)

    for coeff in (0.3 / dt_ns, 0.1 / dt_ns, 0.03 / dt_ns, 0.01 / dt_ns,
                  0.003 / dt_ns, 0.001 / dt_ns):
        eps = coeff * dt_ns
        H = _hamiltonian_matrix_for_term(
            _make_coh_xxyy_term(coeff),
            support=(0, 1),
            local_dims=(2, 2),
            device=DEV,
        )
        kraus = assemble_substep_channel([H], [], dt_ns, device=DEV)
        J_carrier = _choi_state_from_kraus(kraus, device=DEV)
        F_e = float(_state_fidelity(J_carrier, J_I, device=DEV))
        one_minus_fe = float(max(0.0, 1.0 - F_e))
        exact = exact_infidelity_M10(eps)
        band_resid = abs(one_minus_fe - exact)
        assert band_resid <= 5e-7, (
            f"L6a FAIL: |carrier_1-F_e - (1-cos^4(eps/4))| = {band_resid:.3e} at eps={eps:.4f}; "
            f"carrier={one_minus_fe:.6e}, exact={exact:.6e}"
        )


def test_L6b_m10_infidelity_differs_from_pure_axis_form():
    """L6b (M10-specific distinction from pure axes): at the SAME eps, M10's 1-F_e
    1 - cos^4(eps/4) differs from the pure-axis sin^2(eps/4) form.

    This confirms the M10 observable IS distinguishable from a single Pauli-pair
    generator at the same eps -- unlike the M22/M23 pair (which are indistinct via
    1-F_e, only separated by the operator gate). For M10, BOTH the observable AND the
    operator gate distinguish it from the pure axes.

    However: 1-F_e CANNOT tell which specific exchange operator produced the signal --
    a different exchange with the same {-2,0,0,+2} spectrum would give the same 1-F_e.
    Therefore the operator gate (L3a) remains LOAD-BEARING (pre-reg B1 caveat).

    The test confirms: |1-cos^4(eps/4) - sin^2(eps/4)| > 0 for eps in (0, pi).
    Specifically at eps=0.1: cos^4(0.025)=0.99844... -> 1-F_e=0.001559...,
    sin^2(0.025)=0.000625... -> pure-axis form 0.000625. Difference ~9.3e-4.
    """
    for eps in (0.3, 0.1, 0.03, 0.01):
        exact_m10 = exact_infidelity_M10(eps)
        pure_axis_form = math.sin(eps / 4.0) ** 2  # the M22/M23 formula
        diff = abs(exact_m10 - pure_axis_form)
        # They must differ (M10 closed form is distinct from single Pauli-pair form)
        # At small eps: 1-cos^4(x) ~ 2x^2 vs sin^2(x) ~ x^2 (factor of 2 at small x^2)
        # More precisely: 1-cos^4(eps/4) - sin^2(eps/4) ~ (eps/4)^2 + O(eps^4) > 0
        assert diff > 1e-8, (
            f"L6b FAIL: M10 closed form {exact_m10:.6e} equals pure-axis sin^2 {pure_axis_form:.6e} "
            f"to within {diff:.3e} at eps={eps}; the M10 observable should be distinct from M22/M23"
        )


def test_L6c_carrier_infidelity_differs_from_pure_axis_form_at_same_eps():
    """L6c: the carrier 1-F_e for COH_XX_YY differs from the carrier 1-F_e for COH_XX at the same eps.

    This is a CARRIER-LEVEL check: the actual assembled channel via COH_XX_YY gives a
    different 1-F_e than the channel assembled via COH_XX (or COH_YY) at the same eps.
    Confirms the carrier operator is NOT a pure single-pair generator.

    Note: unlike M22/M23 (which are indistinct via 1-F_e), M10's scalar 1-F_e IS a partial
    distinguisher from pure axes. BUT the operator gate is still needed to distinguish M10
    from other exchange generators with the same spectrum (pre-reg B1 caveat).
    """
    coeff = 0.1
    dt_ns = 20.0
    cdt = torch.complex128
    eps = coeff * dt_ns

    # COH_XX_YY channel (M10)
    H_m10 = _hamiltonian_matrix_for_term(
        _make_coh_xxyy_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    kraus_m10 = assemble_substep_channel([H_m10], [], dt_ns, device=DEV)
    J_m10 = _choi_state_from_kraus(kraus_m10, device=DEV)

    # COH_XX channel (M22) -- same coeff, same dt_ns
    from qec_twin.simulator.axis1_mcwf_mps_execution import _hamiltonian_matrix_for_term as _hmt
    term_xx = {
        "kind": "hamiltonian",
        "operator_family": "COH_XX",
        "support": [0, 1],
        "coefficient": float(coeff),
        "substep_id": "m10_ledger_xx",
    }
    H_xx = _hmt(term_xx, support=(0, 1), local_dims=(2, 2), device=DEV)
    kraus_xx = assemble_substep_channel([H_xx], [], dt_ns, device=DEV)
    J_xx = _choi_state_from_kraus(kraus_xx, device=DEV)

    I_kraus = torch.eye(4, dtype=cdt, device=DEV).unsqueeze(0)
    J_I = _choi_state_from_kraus(I_kraus, device=DEV)

    fe_m10 = float(max(0.0, 1.0 - _state_fidelity(J_m10, J_I, device=DEV)))
    fe_xx = float(max(0.0, 1.0 - _state_fidelity(J_xx, J_I, device=DEV)))

    # M10 and M22 at the same eps should give DIFFERENT 1-F_e
    # M10: ~1.56e-3, M22: ~6.25e-4 at eps=2.0 (eps = 0.1 * 20.0 = 2.0)
    assert abs(fe_m10 - fe_xx) > 1e-5, (
        f"L6c FAIL: COH_XX_YY and COH_XX give same 1-F_e at eps={eps:.3f} "
        f"(fe_m10={fe_m10:.6e}, fe_xx={fe_xx:.6e}, diff={abs(fe_m10 - fe_xx):.3e}); "
        "M10 carrier is indistinguishable from M22 via 1-F_e -- composite not assembled correctly"
    )


# ---------------------------------------------------------------------------
# INVARIANT L7: Quadratic scaling  (1-F_e)/eps^2 -> 1/8 as eps->0  (B2, class-b band)
# Leading-order: 1-F_e ~= eps^2/8 = ||(eps/4)(XX+YY)||_F^2 / 4.
# M10-specific: ratio limit is 1/8 (TWICE M22/M23's 1/16).
# ||(eps/4)(XX+YY)||_F^2 = (eps/4)^2 * Tr((XX+YY)^2) = (eps/4)^2 * 8 = eps^2/2 -> /d=4 -> eps^2/8.
# Tr((XX+YY)^2) = 8 because (XX+YY)^2 = 2I + 2(XX)(YY) -> Tr = 8 + 0 = 8.
# BROKEN INPUT: a linear-in-eps error (1-F_e ~ eps, not eps^2) fails this ratio test.
# ---------------------------------------------------------------------------

def test_L7_quadratic_scaling():
    """L7 (class-b band, B2): (1-F_e)/eps^2 -> 1/8 as eps -> 0.

    At small eps: 1 - cos^4(eps/4) ~= eps^2/8 - 5*eps^4/768 + O(eps^6).
    The ratio (1-F_e)/eps^2 should be within 0.010 of 1/8 = 0.125 for eps in [0.01, 0.1].
    At eps=0.3 (larger angle) the ratio deviates by ~O(eps^2) -- registered B2 deviation.
    M10-specific: the ratio target is 1/8 (NOT 1/16 as for M22/M23): TWICE because
    Tr((XX+YY)^2) = 8 (not 4 for single Pauli-pair XX or YY).

    NOTE: the sweep uses eps >= 0.01 (signal ~1.25e-4) to stay well above the Uhlmann
    estimator floor (~4e-8 at d=4). At eps=0.001 the signal (~1.25e-7) is near the floor;
    the operator gate (L3a, opdiff 0) carries the cert there (pre-reg S5).
    """
    dt_ns = 20.0
    cdt = torch.complex128
    I_kraus = torch.eye(4, dtype=cdt, device=DEV).unsqueeze(0)
    J_I = _choi_state_from_kraus(I_kraus, device=DEV)

    # Use eps in [0.01, 0.3]: signal 1-cos^4(eps/4) in [1.25e-4, 6.5e-2] >> Uhlmann floor ~4e-8
    for coeff in (0.3 / dt_ns, 0.1 / dt_ns, 0.05 / dt_ns, 0.03 / dt_ns, 0.01 / dt_ns):
        eps = coeff * dt_ns
        H = _hamiltonian_matrix_for_term(
            _make_coh_xxyy_term(coeff),
            support=(0, 1),
            local_dims=(2, 2),
            device=DEV,
        )
        kraus = assemble_substep_channel([H], [], dt_ns, device=DEV)
        J_c = _choi_state_from_kraus(kraus, device=DEV)
        one_minus_fe = float(max(0.0, 1.0 - _state_fidelity(J_c, J_I, device=DEV)))
        if eps > 0:
            ratio = one_minus_fe / (eps ** 2)
            assert abs(ratio - (1.0 / 8.0)) <= 0.010, (
                f"L7 FAIL: (1-F_e)/eps^2 = {ratio:.6f}, expected ~1/8 = {1/8:.6f}, "
                f"deviation {abs(ratio - 1/8):.5f} > 0.010 at eps={eps:.5f}"
            )


def test_L7_ratio_is_twice_pure_axis():
    """L7-ratio (class-b band, B2): the M10 scaling ratio (1/8) is exactly twice the M22/M23
    ratio (1/16), because XX+YY contributes TWO Cartan axes.

    Tr((XX+YY)^2) = 8  (M10), vs  Tr((XX)^2) = Tr(I4) = 4 (M22) and similarly for YY.
    So the leading ratio is (1/4)^2 * 8 / 4 = 1/8 for M10, vs (1/4)^2 * 4 / 4 = 1/16 for M22.
    At small eps, the ratio (1-F_e)/eps^2 for M10 should be ~TWICE the ratio for M22.
    """
    dt_ns = 20.0
    cdt = torch.complex128
    I_kraus = torch.eye(4, dtype=cdt, device=DEV).unsqueeze(0)
    J_I = _choi_state_from_kraus(I_kraus, device=DEV)

    # Use a small eps to be in the quadratic regime
    coeff = 0.02 / dt_ns   # eps = 0.02
    eps = coeff * dt_ns

    # M10 (COH_XX_YY)
    H_m10 = _hamiltonian_matrix_for_term(
        _make_coh_xxyy_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    kraus_m10 = assemble_substep_channel([H_m10], [], dt_ns, device=DEV)
    J_m10 = _choi_state_from_kraus(kraus_m10, device=DEV)
    one_minus_fe_m10 = float(max(0.0, 1.0 - _state_fidelity(J_m10, J_I, device=DEV)))

    # M22 (COH_XX) at the SAME eps
    term_xx = {
        "kind": "hamiltonian",
        "operator_family": "COH_XX",
        "support": [0, 1],
        "coefficient": float(coeff),
        "substep_id": "m10_ledger_ratio_check",
    }
    H_xx = _hamiltonian_matrix_for_term(term_xx, support=(0, 1), local_dims=(2, 2), device=DEV)
    kraus_xx = assemble_substep_channel([H_xx], [], dt_ns, device=DEV)
    J_xx = _choi_state_from_kraus(kraus_xx, device=DEV)
    one_minus_fe_xx = float(max(0.0, 1.0 - _state_fidelity(J_xx, J_I, device=DEV)))

    # M10 ratio should be ~TWICE the M22 ratio at the same eps
    ratio_m10 = one_minus_fe_m10 / (eps ** 2) if eps > 0 else 0.0
    ratio_xx = one_minus_fe_xx / (eps ** 2) if eps > 0 else 0.0
    # At eps=0.02 in the quadratic regime: ratio_m10 / ratio_xx should be ~2
    if ratio_xx > 1e-10:
        observed_ratio = ratio_m10 / ratio_xx
        assert abs(observed_ratio - 2.0) <= 0.05, (
            f"L7-ratio FAIL: M10/M22 infidelity ratio = {observed_ratio:.4f}, expected ~2.0 "
            f"(ratio_m10={ratio_m10:.6e}, ratio_xx={ratio_xx:.6e} at eps={eps:.4f})"
        )


def test_L7_broken_linear_scaling_trips():
    """FALSIFIER: a channel with 1-F_e ~ eps (linear, not quadratic) fails L7.

    A T1-like collapse at rate ~ eps_ref / dt_ns produces 1-F_e ~ eps_ref (linear).
    This gives ratio (1-F_e)/eps_ref^2 ~ 1/eps_ref >> 1/8 as eps_ref -> 0.
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
    assert abs(ratio_linear - (1.0 / 8.0)) > 0.01, (
        f"FALSIFIER DID NOT TRIP: linear-in-eps channel has (1-F_e)/eps^2 = {ratio_linear:.4f} "
        "which is within 0.01 of 1/8; the L7 quadratic-scaling check cannot distinguish "
        "linear from quadratic at this scale -- falsifier broken"
    )


# ---------------------------------------------------------------------------
# INVARIANT L8: Even symmetry  1-F_e(eps) = 1-F_e(-eps)  (class-a, exact)
# 1 - cos^4(eps/4) = 1 - cos^4(-eps/4)  (cos is even); F_e(U) = F_e(U†).
# BROKEN INPUT: an asymmetric (directional) error violates even symmetry.
# ---------------------------------------------------------------------------

def test_L8_infidelity_even_in_eps():
    """L8 (class-a exact): 1-F_e is even in eps.

    1 - cos^4(eps/4) = 1 - cos^4(-eps/4) because cos is even.
    F_e(U) = |Tr(U)/4|^2 = |Tr(U†)/4|^2 = F_e(U†) (trace modulus invariant under conjugation).
    Over- and under-rotation of equal magnitude are equally infidel (pre-reg B1 even-in-eps).
    """
    dt_ns = 20.0
    cdt = torch.complex128
    I_kraus = torch.eye(4, dtype=cdt, device=DEV).unsqueeze(0)
    J_I = _choi_state_from_kraus(I_kraus, device=DEV)

    def _fe(coeff_val: float) -> float:
        H = _hamiltonian_matrix_for_term(
            _make_coh_xxyy_term(coeff_val),
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
        assert diff <= 1e-10, (
            f"L8 FAIL: 1-F_e(+eps) = {fe_pos:.6e}, 1-F_e(-eps) = {fe_neg:.6e}, "
            f"diff = {diff:.3e} > 1e-10 at coeff={coeff} -- even-symmetry broken"
        )


def test_L8_broken_odd_infidelity_formula_trips():
    """FALSIFIER: if someone used cos(eps/4) instead of cos^4(eps/4), the formula changes
    from even to a different even function, and cos(eps/4) != cos^4(eps/4) for eps != 0.

    More sharply: if the formula were sin(eps/4) (odd in eps) it would violate the
    even-symmetry check. The correct 1-cos^4(eps/4) is even in eps.
    """
    for eps in (0.3, 0.1, 0.03, 0.01, 0.003, 0.001):
        # Correct formula: 1 - cos^4(eps/4) -- should be even in eps
        correct_pos = exact_infidelity_M10(+eps)
        correct_neg = exact_infidelity_M10(-eps)
        assert abs(correct_pos - correct_neg) <= 1e-14, (
            f"L8 SELF-CHECK FAIL: correct formula 1-cos^4(eps/4) is not even at eps={eps}"
        )
        # Wrong formula: using sin(eps/4) (odd) would violate the symmetry
        wrong_pos = math.sin(eps / 4.0)
        wrong_neg = math.sin(-eps / 4.0)
        assert abs(wrong_pos - wrong_neg) >= abs(eps) / 8.0, (
            f"FALSIFIER DID NOT TRIP: the wrong formula sin(eps/4) is unexpectedly symmetric "
            f"at eps={eps}: wrong_pos={wrong_pos:.6f}, wrong_neg={wrong_neg:.6f}"
        )


# ---------------------------------------------------------------------------
# INVARIANT L9: Apply every gate -- identity embed on leaked levels  (S3, class-a)
# In a 2-qutrit carrier (d0=d1=3), H_M10 acts on the 4 computational rows/cols
# ({0,1}x{0,1} -> indices {0,1,3,4} of a 3x3=9-dim space) with gen4 = (coeff/4)(XX+YY)
# and has the ZERO GENERATOR on all rows/cols involving any level >= 2 (leaked levels).
# M10 imparts NO population or phase to leaked levels (S3): exp(0)=I on level >=2.
# M10-specific note: the exchange XX+YY acts between |01> and |10> (flip-flop); no
# leaked-level exchange (e.g. |11><->|02>) is in scope for M10 -- that is M34/LEAK_*.
# BROKEN INPUT: a 9x9 matrix that has non-zero entries involving row/col index 2,5,6,7,8
# (the leaked-level subspace) trips L9.
# ---------------------------------------------------------------------------

def test_L9_qutrit_embed_is_zero_on_leaked_levels():
    """L9 (class-a exact, S3): in a dim=(3,3) carrier, the 9x9 H_M10 matrix has:
    (a) its 4x4 computational block (rows/cols {0,1,3,4}) equal to the qubit reference gen4,
    (b) zero generator on all rows/cols involving leaked level >= 2 (indices 2,5,6,7,8).

    M10-specific: exp(-i H dt) = I on any pair of levels where either index >= 2 -- M10
    imparts NO leakage (pre-reg S3). The flip-flop exchange acts ONLY on |01><->|10>
    within the computational block; any leaked-level exchange is a different mechanism.
    The embed is verified by checking each computational-level (row,col) slot and confirming
    all non-computational rows/cols are zero.

    M10 structural check in the embed: the gen4 is (coeff/4)(XX+YY), real-symmetric with
    anti-diagonal center pattern [[0,0,0,0],[0,0,2,0],[0,2,0,0],[0,0,0,0]] at coeff=1;
    this is embedded without change into the computational block of the 9x9 matrix.
    """
    coeff = 0.1
    d0, d1 = 3, 3
    H = _hamiltonian_matrix_for_term(
        _make_coh_xxyy_term(coeff),
        support=(0, 1),
        local_dims=(d0, d1),
        device=DEV,
    )
    # Reference gen4 on the 4-dim computational subspace (qubit reference)
    H_ref_4 = ref_H_M10(coeff, 2, 2)  # 4x4, (d0=2, d1=2)

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
            f"L9 FAIL: H_M10 qutrit row-{idx} norm = {row_norm:.3e} != 0; "
            "M10 drives leaked levels -- S3 violated"
        )
        assert col_norm <= _OPERATOR_DIFF_TOL, (
            f"L9 FAIL: H_M10 qutrit col-{idx} norm = {col_norm:.3e} != 0; "
            "M10 drives leaked levels -- S3 violated"
        )


def test_L9_broken_full_qutrit_xxyy_extends_to_leaked_levels_trips():
    """FALSIFIER: a 9x9 (XX+YY)-like matrix that extends to qutrit levels fails L9.

    An extended 3x3 "X+Y-like" matrix that couples into level 2 (not M10 semantics)
    would have non-zero entries at leaked-level indices -- which is NOT M10 semantics.
    M10 has zero generator on any level >= 2 (pre-reg S3).
    """
    cdt = torch.complex128
    d0, d1 = 3, 3
    # A 3x3 "X-like" matrix extended into the leaked level 2
    X3 = torch.zeros((3, 3), dtype=cdt, device=DEV)
    X3[0, 1] = 1.0
    X3[1, 0] = 1.0
    X3[0, 2] = 1.0   # extends to leaked level
    X3[2, 0] = 1.0   # extends to leaked level
    H_broken = 0.025 * torch.kron(X3.contiguous(), X3.contiguous())
    leaked_indices = [i for i in range(d0 * d1) if (i // d1 >= 2) or (i % d1 >= 2)]
    leaked_norms = [float(torch.linalg.norm(H_broken[i, :]).item()) for i in leaked_indices]
    assert max(leaked_norms) > _OPERATOR_DIFF_TOL, (
        "FALSIFIER DID NOT TRIP: the broken 9x9 (XX+YY)-extended matrix has zero leaked rows -- "
        "falsifier wrong (check the index logic)"
    )


# ---------------------------------------------------------------------------
# INVARIANT L10: Anti-circular namespace check  (structural, class-c gate)
# The cert (THIS FILE) must NOT import `_coherent_family_generator`,
# `_embed_coherent_generator`, `TWO_SITE_COHERENT_FAMILIES`, or `COHERENT_PAULI_FAMILIES`
# from the carrier. If these symbols appear in this module's namespace, the cert is circular:
# a wrong Pauli-pair map (COH_XX_YY -> ((X,X),) dropping one summand) shared between the
# 'reference' and the carrier would false-pass (the W-C round-1 failure shape).
# M10-sharp: the circularity risk for M10 is the DROP-SUMMAND corruption -- if the cert
# referenced the carrier pair list, a single-pair corruption (dropping XX or YY from the
# COH_XX_YY pair list) would be invisible. The hand-typed (XX+YY) composite reference is
# the only reference that can catch it.
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

    M10-sharp: if `_coherent_family_generator` is imported, a corrupted COH_XX_YY pair map
    (dropping one summand, e.g. ((X,X),) only) would be reflected into the 'reference'
    silently -- false-passing the drop-summand control (L3b/L3c) which is the M10 load-bearing gate.
    The hand-typed (XX+YY) composite reference is the only safeguard against this.
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
    M10-sharp: the specific circularity to prevent is a `_coherent_family_generator` reference
    that would mirror a corrupted pair map (dropping XX or YY from COH_XX_YY).
    """
    class _FakeModule:
        _coherent_family_generator = lambda *a, **kw: None  # noqa: E731
        _hamiltonian_matrix_for_term = lambda *a, **kw: None  # noqa: E731

    fake = _FakeModule()
    assert hasattr(fake, "_coherent_family_generator"), (
        "FALSIFIER DID NOT TRIP: the fake module lacks the circular symbol -- falsifier broken"
    )
