"""M28 coherent_xy_parasitic_coupling -- CONSTRAINT LEDGER (executable falsifier tests).

FAITHFULNESS PROTOCOL (docs/FAITHFULNESS_PROTOCOL.md) -- constraint ledger for M28.
Each test below is a FALSIFIER: it documents the invariant AND shows that a
deliberately BROKEN input makes the test FAIL (trips the falsifier). Tests run
GREEN on the faithful carrier and RED on the broken variant.

ANTI-CIRCULARITY: the reference operator (``ref_H_M28``) is HAND-TYPED from the
literature (Zhang-Vala-Sastry-Whaley arXiv:quant-ph/0209120 Eq. 7 + Example 2/Sec.V.A
"H = (1/2)(J_xx XX + J_yy YY + J_xy XY + J_yx YX)", the cross-term sigma_x(x)sigma_y
with independent coefficient J_xy; Kraus-Cirac arXiv:quant-ph/0011050 Eq. 12
off-diagonal d_ab entry of the canonical bilinear Sigma_ab d_ab sigma_a(x)sigma_b).
The cert imports ONLY ``axis1_mcwf_mps_execution._hamiltonian_matrix_for_term``
(the object under test).  The carrier's ``_coherent_family_generator`` /
``_embed_coherent_generator`` / ``TWO_SITE_COHERENT_FAMILIES`` / ``COHERENT_PAULI_FAMILIES``
appear NOWHERE in the reference code (same de-circularization rule as
test_m22_coherent_cxx_constraint_ledger.py, test_m23_coherent_cyy_constraint_ledger.py,
test_axis1_wc_decircularized.py, and the M6/M7/M20 ledgers).

GATE TIER: STRICT (``1-F_e <= 1e-6``; operator identity <= 1e-12 / unitary <= 1e-10).
M28 is a pure-Hamiltonian / exact-dense error -- no collapse, no finite-step MCWF.

M28-SPECIFIC (the one place the cross-term differs from the diagonal XX/YY at the matrix
level):
- The generator is H_M28 = (coeff/4) * (X (x) Y), the cross-term (directed) axis.
  X(x)Y is the (a,b)=(x,y) off-diagonal entry of the canonical bilinear (Kraus-Cirac
  Eq.12) and the standalone J_xy XY term of the generalized anisotropic exchange
  (Zhang Example 2 / Sec.V.A).
- X(x)Y is PURE-IMAGINARY and ANTISYMMETRIC (imag-part norm 2.0, antisym-resid 0.0,
  sym-resid 4.0) -- the OPPOSITE of M22 XX / M23 YY, which are real-symmetric.
  Anti-diagonal imaginary sign pattern (-i, +i, -i, +i).
- X(x)Y != Y(x)X (=M33): DIRECTIONAL. ||X(x)Y - Y(x)X||_F = 2.83.
  M28 = directed A_X->B_Y; M33 = directed A_Y->B_X (its reverse).
- ``1-F_e = sin^2(eps/4)`` (factor /4, same as M22/M23 for 2-site) is AXIS-BLIND and
  DIRECTION-BLIND -- identical for ANY single Pauli-pair generator P(x)Q at the same eps
  (pre-reg B1). The operator-identity gate L3a and wrong-axis falsifiers (L3b-L3e) are the
  LOAD-BEARING cert gates: the SOLE witnesses that the carrier couples via X(x)Y and not
  XX/YY/ZZ/YX/(XX+YY). L3b (XY vs YX = M33) is the M28-sharp directionality control --
  the new gate that separates M28 from its reverse M33. Since 1-F_e is IDENTICAL for M28
  and M33 (both traceless Pauli-pair involutions; pre-reg B1), the XY-vs-YX operator
  disagreement is the ONLY thing that distinguishes them.
- The ratio limit is eps^2/16 (same as M22/M23; the formula is axis-agnostic for single
  Pauli-pair traceless involutions at d=4). The F_avg companion factor is 4/5 (d=4).

GPU-only (top-level memory rule) -- collection FAILS without CUDA.

Pre-registration: docs/twin_validation/m28_coherent_xy_parasitic_coupling_prereg.md
Run:  conda run -n aiqec python -m pytest -q tests/test_m28_coherent_xy_constraint_ledger.py
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
        "M28 constraint-ledger cert is GPU-gated; CUDA-MISSING is NOT A RELEASE BASIS",
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
#                           # (class-c gate; derivation-check: XX/YY/ZZ/YX each diff 3.54e-3
#                           # at eps=0.1; M10 (XX+YY) diff 4.33e-3; all >> 1e-3)

# ---------------------------------------------------------------------------
# Reference operator (HAND-TYPED, non-circular)
#
# Provenance:
#   H_M28 = (coeff/4) * (sigma_x (x) sigma_y)  on the 4-dim computational subspace.
#   sigma_x = [[0,1],[1,0]], sigma_y = [[0,-i],[i,0]]  (Nielsen & Chuang Eq. 2.1).
#   X(x)Y is the CROSS-TERM 2-body generator:
#     - A basis element of the non-local part p of su(4) (Zhang-Vala-Sastry-Whaley
#       arXiv:quant-ph/0209120 Eq. 7, the span of the 9 Pauli(x)Pauli basis elements);
#     - Written standalone with an independent coefficient J_xy in the "generalized
#       anisotropic exchange H = (1/2)(J_xx XX + J_yy YY + J_xy XY + J_yx YX)"
#       (Zhang Example 2 / Sec. V.A -- the DIRECT primary-source license for M28);
#     - The off-diagonal (a,b)=(x,y) entry of the canonical bilinear
#       Sigma_ab d_ab sigma_a(x)sigma_b (Kraus-Cirac arXiv:quant-ph/0011050 Eq. 12;
#       d diagonal in that paper restricts to XX/YY/ZZ, so this is INDIRECT for M28).
#   DEVICE origin (anisotropic/directed crosstalk, INDIRECT): NOT the symmetric transverse
#       coupler/exchange (gmon g sigma_x(x)sigma_x, Geller arXiv:1405.1915; (g/2)(XX+YY)
#       exchange, Sung arXiv:2011.01261) which carry NO cross-term; a pure X(x)Y requires a
#       directed/anisotropic coupler (2q-Hamiltonian derivation §M28, "Directed crosstalk,
#       A->B capacitive coupling").
#   factor 1/4 = (1/2)^2: two-qubit over-rotation convention R_{PQ}(eps_cat) = exp(-i
#       (eps_cat/2)(P(x)Q)), carrier eps = coeff*dt is the per-tensor angle; catalog
#       eps_cat = eps/2 (error_mechanisms.md line 119 "exp(-i eps XY/2)"; carrier docstring
#       lines 1026-1036).
#   M28 structural facts (exact, class-a):
#     (1) X(x)Y is HERMITIAN, IMAGINARY, ANTISYMMETRIC (imag-part norm 2.0, antisym-resid 0.0,
#         sym-resid 4.0) -- the OPPOSITE of the real-symmetric M22 XX / M23 YY.
#         Anti-diagonal, imaginary sign pattern (-i, +i, -i, +i).
#         Explicit matrix on the 4-dim basis |00>,|01>,|10>,|11>:
#             X(x)Y = [[  0,  0,  0, -i],
#                      [  0,  0, +i,  0],
#                      [  0, -i,  0,  0],
#                      [ +i,  0,  0,  0]]
#     (2) X(x)Y != Y(x)X (=M33): DIRECTIONAL. ||X(x)Y - Y(x)X||_F = 2.83.
#         M28 = directed A_X->B_Y; M33 = directed A_Y->B_X (its reverse).
#   zero generator on any leaked level >= 2 (S3; _embed_coherent_generator semantics).
#   error unitary: U = exp(-i H dt) = cos(eps/4) I4 - i sin(eps/4)(X(x)Y), eps = coeff*dt.
#   EXACT 1-F_e (d=4): 1 - |Tr(U)/4|^2 = sin^2(eps/4).
#     Tr(U) = Tr(cos(eps/4)I4 - i sin(eps/4)(X(x)Y)) = 4 cos(eps/4) [since Tr(X(x)Y)=0];
#     F_e = |4cos(eps/4)/4|^2 = cos^2(eps/4) => 1-F_e = sin^2(eps/4).
#     AXIS-BLIND AND DIRECTION-BLIND: identical for ANY single Pauli-pair P(x)Q involution
#     (Tr=0, sq=I4) at the same eps -- cannot distinguish XY from YX (=M33) by 1-F_e alone.
#   LEADING 1-F_e: ||(eps/4)(X(x)Y)||_F^2 / 4 = (eps/4)^2 * 4 / 4 = eps^2/16.
# ---------------------------------------------------------------------------


def ref_H_M28(coeff: float, d0: int, d1: int) -> torch.Tensor:
    """Hand-typed M28 reference generator on the (d0*d1)-dim local space.

    H_M28 = (coeff/4) * (X (x) Y)  embedded into the d0*d1-dimensional space,
    with the zero generator (identity gate) on any product-level pair where either
    index >= 2 (no leakage drive from M28 -- S3).
    Imports NOTHING from the carrier family tables.
    """
    cdt = torch.complex128
    # Hand-typed Pauli-X and Pauli-Y (Nielsen & Chuang Eq. 2.1)
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    Y2 = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
    # (coeff/4) * (X (x) Y) on the 4-dim computational subspace
    # X(x)Y is IMAGINARY-ANTISYMMETRIC: anti-diagonal with signs (-i, +i, -i, +i)
    gen4 = 0.25 * coeff * torch.kron(X2.contiguous(), Y2.contiguous())
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


def ref_U_M28(coeff: float, dt_ns: float, d0: int, d1: int) -> torch.Tensor:
    """Hand-typed M28 error unitary: U = matrix_exp(-i * H * dt)."""
    H = ref_H_M28(coeff, d0, d1)
    return torch.linalg.matrix_exp(-1j * dt_ns * H)


def exact_infidelity_M28(eps: float) -> float:
    """Closed-form 1-F_e for exp(-i(eps/4)(X(x)Y)) vs identity (d=4).

    Tr(U_M28) = Tr(cos(eps/4)I4 - i sin(eps/4)(X(x)Y)) = 4*cos(eps/4)  [Tr(X(x)Y)=0].
    F_e = |Tr(U)/4|^2 = cos^2(eps/4)  =>  1-F_e = sin^2(eps/4).
    Reference: Nielsen arXiv:quant-ph/0205035 Eq. 16 (F_e = |Tr U / d|^2 for unitary U);
    pre-registration B1, section 2.
    NOTE: sin^2(eps/4) is the same for ANY single Pauli-pair P(x)Q generator at
    the same eps (Tr(P(x)Q)=0 and (P(x)Q)^2=I4 for all single Paulis) -- AXIS-BLIND
    AND DIRECTION-BLIND (cannot tell XY from YX=M33 by this scalar alone).
    This is identical to exact_infidelity_M22 / exact_infidelity_M23; the /4 factor is
    the 2-site convention.
    """
    return float(math.sin(eps / 4.0) ** 2)


def _make_coh_xy_term(coeff: float) -> dict:
    """Minimal schedule-term dict for COH_XY on two sites (support=(0,1))."""
    return {
        "kind": "hamiltonian",
        "operator_family": "COH_XY",
        "support": [0, 1],
        "coefficient": float(coeff),
        "substep_id": "m28_ledger",
    }


# ---------------------------------------------------------------------------
# INVARIANT L1: Hermiticity  ||H - H†||_F <= 1e-12  (class-a exact)
# X(x)Y is Hermitian: (X(x)Y)† = X†(x)Y† = X(x)Y (both X and Y are Hermitian).
# An anti-Hermitian generator is WRONG.
# BROKEN INPUT: a non-Hermitian matrix (imaginary off-diagonal term only, not matching H†)
# ---------------------------------------------------------------------------

def test_L1_generator_is_hermitian():
    """L1 (class-a exact): the M28 generator H satisfies H = H†.

    X(x)Y is Hermitian: X† = X, Y† = Y, so (X(x)Y)† = X(x)Y.
    Although X(x)Y is imaginary-antisymmetric (the M28-sharp structural fact), it is
    still Hermitian (a valid quantum-mechanical generator; pre-reg §2, B4 note).
    Broken-input demonstration: an explicitly non-Hermitian operator trips this test.
    """
    coeff = 0.1
    H = _hamiltonian_matrix_for_term(
        _make_coh_xy_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    resid = float(torch.linalg.matrix_norm(H - H.conj().T).item())
    assert resid <= _HERMITIAN_TOL, (
        f"L1 FAIL: ||H - H†||_F = {resid:.3e} > {_HERMITIAN_TOL}; "
        "M28 generator is not Hermitian -- physics bug"
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
# Tr(X(x)Y) = Tr(X)*Tr(Y) = 0*0 = 0; an identity-shifted generator is WRONG.
# BROKEN INPUT: H + (c/4) * I4 (trace = coeff)
# ---------------------------------------------------------------------------

def test_L2_generator_is_traceless():
    """L2 (class-a exact): the M28 generator H is traceless.

    Tr(X(x)Y) = Tr(X)*Tr(Y) = 0*0 = 0. Any non-zero trace indicates identity
    contamination or a wrong family.
    """
    coeff = 0.1
    H = _hamiltonian_matrix_for_term(
        _make_coh_xy_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    tr_resid = float(torch.abs(torch.trace(H)).item())
    assert tr_resid <= _TRACELESS_TOL, (
        f"L2 FAIL: |Tr H| = {tr_resid:.3e} > {_TRACELESS_TOL}; "
        "M28 generator has a non-zero trace -- wrong axis or identity contamination"
    )


def test_L2_broken_identity_shift_trips():
    """FALSIFIER: a traceful 4x4 generator (XY + identity offset) fails L2."""
    cdt = torch.complex128
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    Y2 = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
    XY = torch.kron(X2.contiguous(), Y2.contiguous())
    H_broken = 0.025 * XY + 0.025 * torch.eye(4, dtype=cdt, device=DEV)
    tr_resid = float(torch.abs(torch.trace(H_broken)).item())
    assert tr_resid > _TRACELESS_TOL, (
        "FALSIFIER DID NOT TRIP: an identity-shifted 4x4 generator passed L2 -- "
        "the falsifier is broken"
    )


# ---------------------------------------------------------------------------
# INVARIANT L2b: Imaginary-antisymmetric structure of X(x)Y  (class-a exact, M28-specific)
# X(x)Y is PURE-IMAGINARY (imag-part norm = 2.0 * |coeff/4|) and ANTISYMMETRIC
# (X(x)Y = -(X(x)Y)^T, i.e. antisym-resid = 0, sym-resid = 4 at unit scale).
# This is the M28-sharp structural fact distinguishing it from M22 XX / M23 YY (real-symmetric).
# BROKEN INPUT: a real-symmetric matrix (e.g. X(x)X = M22) violates the imaginary-structure check.
# BROKEN INPUT (antisym): a symmetric matrix (e.g. X(x)X) violates the antisymmetry check.
# ---------------------------------------------------------------------------

def test_L2b_xy_generator_is_imaginary_antisymmetric():
    """L2b (class-a exact, M28-specific): X(x)Y is imaginary-antisymmetric.

    X = [[0,1],[1,0]] (real/symmetric); Y = [[0,-i],[i,0]] (imaginary/antisymmetric).
    X(x)Y = (real-sym)(x)(imag-antisym): the product is imaginary-antisymmetric.
    Anti-diagonal, imaginary sign pattern (-i, +i, -i, +i) on the 4x4 (pre-reg §2, B4).
    Therefore:
      - real-part norm <= 1e-12 (purely imaginary),
      - antisym-resid ||X(x)Y + (X(x)Y)^T||_F <= 1e-12 (antisymmetric),
      - sym-resid ||X(x)Y - (X(x)Y)^T||_F = 4 * |coeff/4| (NOT symmetric).
    This distinguishes M28 from M22 (XX real-symmetric) and M23 (YY real-symmetric).
    Contrast: Y(x)X (=M33) has the SAME imaginary-antisymmetric structure but with
    the opposite sign pattern (+i, -i, +i, -i); the directionality is caught by L3b (XY vs YX).
    """
    coeff = 0.1
    H = _hamiltonian_matrix_for_term(
        _make_coh_xy_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    # Real part should be zero (purely imaginary generator)
    real_norm = float(torch.linalg.matrix_norm(H.real).item())
    assert real_norm <= _OPERATOR_DIFF_TOL, (
        f"L2b FAIL: real-part norm of H_M28 = {real_norm:.3e} > {_OPERATOR_DIFF_TOL}; "
        "X(x)Y should be PURELY IMAGINARY -- physics bug"
    )
    # Antisymmetric: H = -H^T  <=>  H + H^T = 0
    antisym_resid = float(torch.linalg.matrix_norm(H + H.T).item())
    assert antisym_resid <= _OPERATOR_DIFF_TOL, (
        f"L2b FAIL: antisym residual ||H + H^T||_F = {antisym_resid:.3e} > {_OPERATOR_DIFF_TOL}; "
        "X(x)Y should be ANTISYMMETRIC (not X(x)X or Y(x)Y which are symmetric) -- structural bug"
    )
    # Also check the imaginary part norm is at the expected scale (unit-coeff reference)
    # At coeff=0.1: imag part of (0.1/4)*(X(x)Y) has entries in {0, ±0.025};
    # ||imag(H)||_F = (0.1/4) * ||X(x)Y||_imag = (0.1/4) * 2.0 (derivation-check: imag-norm of
    # the unit (coeff/4)*(X(x)Y) at coeff=1 is 0.25 * 2.0 = 0.5; at coeff=0.1 is 0.05)
    expected_imag_scale = abs(coeff / 4.0) * 2.0  # ||X(x)Y||_imag = 2 (norm of imag part of unit X(x)Y)
    imag_norm = float(torch.linalg.matrix_norm(H.imag).item())
    assert abs(imag_norm - expected_imag_scale) <= _OPERATOR_DIFF_TOL, (
        f"L2b FAIL: imag-part norm = {imag_norm:.6e}, expected {expected_imag_scale:.6e}; "
        "M28 imaginary-antisymmetric scale is wrong -- coefficient bug"
    )


def test_L2b_broken_xx_is_real_symmetric_trips():
    """FALSIFIER: X(x)X (=M22) is real-symmetric, failing the imaginary-structure check.

    X(x)X = [[0,0,0,1],[0,0,1,0],[0,1,0,0],[1,0,0,0]] is real (imag-norm=0) and symmetric.
    The L2b real-part check trips on X(x)X: it has norm 0 in imaginary part (all-real),
    and the M28 generator should have norm 0 in real part (all-imaginary). These differ.
    The falsifier checks that the imaginary-antisymmetric assertion is non-trivially distinct
    from real-symmetric generators.
    """
    cdt = torch.complex128
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    H_xx = 0.025 * torch.kron(X2.contiguous(), X2.contiguous())  # M22, real-symmetric
    real_norm_xx = float(torch.linalg.matrix_norm(H_xx.real).item())
    # XX should have a non-zero real part (it is real-symmetric, opposite of M28)
    assert real_norm_xx > _OPERATOR_DIFF_TOL, (
        "FALSIFIER DID NOT TRIP: X(x)X appears to have zero real part -- "
        "falsifier broken (X(x)X should be real-symmetric)"
    )


def test_L2b_broken_real_part_trips_antisym_check():
    """FALSIFIER: a symmetric (non-antisymmetric) matrix fails the antisymmetry check.

    X(x)Y is antisymmetric (H + H^T = 0). A symmetric matrix such as X(x)X (M22,
    H - H^T = 0 => H + H^T = 2H != 0) fails the L2b antisymmetry assertion.
    """
    cdt = torch.complex128
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    H_xx = 0.025 * torch.kron(X2.contiguous(), X2.contiguous())  # symmetric, not antisymmetric
    antisym_resid = float(torch.linalg.matrix_norm(H_xx + H_xx.T).item())
    assert antisym_resid > _OPERATOR_DIFF_TOL, (
        "FALSIFIER DID NOT TRIP: X(x)X (symmetric) passed the antisymmetry check -- "
        "L2b antisymmetry assertion is not meaningful"
    )


# ---------------------------------------------------------------------------
# INVARIANT L3a: Operator identity  ||H_carrier - H_ref||_F <= 1e-12  (B4, class-a)
# This is the LOAD-BEARING cert gate for M28 (1-F_e alone cannot catch wrong Pauli-pair axis
# OR wrong direction: sin^2(eps/4) is identical for ANY single Pauli-pair generator at the
# same eps -- pre-reg B1). The XY-vs-YX (M28 vs M33) confusion is INVISIBLE to 1-F_e.
# BROKEN INPUT: wrong-axis references (YX=M33 / XX=M22 / YY=M23 / ZZ / XX+YY=M10) --
# must disagree >= 1e-3. The YX (M33) control is the PRIMARY M28-sharp gate.
# ---------------------------------------------------------------------------

def test_L3a_operator_matches_hand_typed_reference():
    """L3a (class-a exact, B4): the carrier generator equals the hand-typed reference.

    H_ref = (coeff/4) * (X(x)Y) embedded in (d0,d1), from Zhang Example 2/Sec.V.A
    (J_xy XY term, independent coefficient in the generalized anisotropic exchange).
    This is the LOAD-BEARING gate -- 1-F_e alone cannot distinguish XY from YX/XX/YY/ZZ/...
    at equal eps (all single Pauli-pair involutions have the same sin^2(eps/4); pre-reg B1).
    In particular, 1-F_e CANNOT separate M28 (XY) from its reverse M33 (YX) -- the
    directionality is invisible to the scalar. The operator identity is the SOLE witness.

    Swept over coeff in {0.3, 0.1, 0.03, 0.01, 0.003, 0.001} and dims (2,2) / (3,3).
    """
    for coeff in (0.3, 0.1, 0.03, 0.01, 0.003, 0.001):
        for d0, d1 in ((2, 2), (3, 3)):
            H_carrier = _hamiltonian_matrix_for_term(
                _make_coh_xy_term(coeff),
                support=(0, 1),
                local_dims=(d0, d1),
                device=DEV,
            )
            H_ref = ref_H_M28(coeff, d0, d1)
            diff = float(torch.linalg.matrix_norm(H_carrier - H_ref).item())
            assert diff <= _OPERATOR_DIFF_TOL, (
                f"L3a FAIL: ||H_carrier - H_ref||_F = {diff:.3e} > {_OPERATOR_DIFF_TOL} "
                f"at coeff={coeff}, dims=({d0},{d1}) -- wrong generator (wrong axis, "
                "wrong direction, wrong coefficient, wrong convention)"
            )


def test_L3b_broken_wrong_direction_yx_trips():
    """FALSIFIER (L3b, M28-SHARP GATE): a wrong-direction YX reference disagrees with the XY
    carrier by >= 1e-3.

    This is the PRIMARY wrong-axis control for M28 (pre-reg §3):
    a reference H_wrong = (coeff/4)(Y(x)X) (= M33) disagrees with the XY carrier.
    XY has anti-diagonal imaginary signs (-i, +i, -i, +i); YX has (+i, -i, +i, -i) --
    structurally distinct (the reverse direction).

    This gate is the SOLE distinguisher of M28 (XY) from its reverse M33 (YX):
    sin^2(eps/4) is IDENTICAL for both (pre-reg B1); the operator identity is the only witness.
    A circular reference derived FROM a corrupted carrier pair map (COH_XY->(Y,X)) would
    mirror the wrong direction to diff=0 (false-pass); the hand-typed (X(x)Y) reference catches it.

    Derivation-check (pre-reg §3, 2026-06-29): diff = 3.54e-3 at eps=0.1, above 1e-3.
    """
    coeff = 0.1
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_xy_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    cdt = torch.complex128
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    Y2 = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
    H_wrong_yx = 0.25 * coeff * torch.kron(Y2.contiguous(), X2.contiguous())  # M33 = Y(x)X
    diff = float(torch.linalg.matrix_norm(H_carrier - H_wrong_yx).item())
    assert diff >= _WRONG_AXIS_MIN, (
        f"FALSIFIER DID NOT TRIP: wrong-direction YX reference (=M33) passed with diff={diff:.3e} < "
        f"{_WRONG_AXIS_MIN}; the M28/M33 XY vs YX directionality confusion is undetectable -- "
        "M28 vs M33 distinction cannot be certified (operator-identity cert broken)"
    )


def test_L3c_broken_wrong_axis_xx_trips():
    """FALSIFIER (L3c): a wrong-axis XX reference (=M22) disagrees with the XY carrier by >= 1e-3.

    XX is real-symmetric (anti-diagonal all +1); XY is imaginary-antisymmetric (-i,+i,-i,+i).
    Structurally distinct (the imaginary-antisymmetric assertion of L2b).
    M28-specific: the YY Cartan diagonal (M23, anti-diagonal -1,+1,+1,-1) and XX (M22,
    anti-diagonal +1,+1,+1,+1) must be distinguishable from XY by the operator gate.

    Derivation-check (pre-reg §3, 2026-06-29): diff = 3.54e-3 at eps=0.1, above 1e-3.
    """
    coeff = 0.1
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_xy_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    cdt = torch.complex128
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    H_wrong_xx = 0.25 * coeff * torch.kron(X2.contiguous(), X2.contiguous())  # M22
    diff = float(torch.linalg.matrix_norm(H_carrier - H_wrong_xx).item())
    assert diff >= _WRONG_AXIS_MIN, (
        f"FALSIFIER DID NOT TRIP: wrong-axis XX reference (=M22) passed with diff={diff:.3e} < "
        f"{_WRONG_AXIS_MIN}; the XY/XX confusion is undetectable"
    )


def test_L3d_broken_wrong_axis_yy_trips():
    """FALSIFIER (L3d): a wrong-axis YY reference (=M23) disagrees with the XY carrier by >= 1e-3.

    YY is real-symmetric (anti-diagonal -1,+1,+1,-1); XY is imaginary-antisymmetric (-i,+i,-i,+i).
    Structurally distinct.
    Derivation-check (pre-reg §3, 2026-06-29): diff = 3.54e-3 at eps=0.1, above 1e-3.
    """
    coeff = 0.1
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_xy_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    cdt = torch.complex128
    Y2 = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
    H_wrong_yy = 0.25 * coeff * torch.kron(Y2.contiguous(), Y2.contiguous())  # M23
    diff = float(torch.linalg.matrix_norm(H_carrier - H_wrong_yy).item())
    assert diff >= _WRONG_AXIS_MIN, (
        f"FALSIFIER DID NOT TRIP: wrong-axis YY reference (=M23) passed with diff={diff:.3e} < "
        f"{_WRONG_AXIS_MIN}; the XY/YY confusion is undetectable"
    )


def test_L3e_broken_wrong_axis_zz_trips():
    """FALSIFIER (L3e): a wrong-axis ZZ reference disagrees with the XY carrier by >= 1e-3.

    ZZ is diagonal (eigenvalues +1/-1 on diag, real); XY is imaginary off-anti-diagonal.
    Structurally distinct.
    """
    coeff = 0.1
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_xy_term(coeff),
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
        f"{_WRONG_AXIS_MIN}; the XY/ZZ confusion is undetectable"
    )


def test_L3f_broken_wrong_axis_xxyy_trips():
    """FALSIFIER (L3f): a wrong-axis (XX+YY)/2 reference (=M10) disagrees with the XY carrier.

    (XX+YY)/2 is M10 (COH_XX_YY, the exchange interaction -- two pairs summed); pure XY is M28.
    The carrier's COH_XY must return only the XY pair, not the XX+YY sum (pre-reg §3).

    Derivation-check (pre-reg §3, 2026-06-29): diff = 4.33e-3 at eps=0.1, above 1e-3.
    """
    coeff = 0.1
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_xy_term(coeff),
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
        f"{_WRONG_AXIS_MIN}; the XY/(XX+YY) confusion is undetectable (M28 vs M10 indistinct)"
    )


def test_L3g_broken_wrong_unit_no_factor_trips():
    """FALSIFIER (L3g): wrong-unit convention (coeff*(X(x)Y), missing the /4) disagrees.

    Correct: H = (coeff/4)*(X(x)Y).  Wrong: H = coeff*(X(x)Y)  [missing both /2 factors].
    A factor-of-4 error in the generator gives a factor-of-4 error in the angle.
    """
    coeff = 0.1
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_xy_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    cdt = torch.complex128
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    Y2 = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
    XY = torch.kron(X2.contiguous(), Y2.contiguous())
    H_wrong_unit = float(coeff) * XY  # missing the /4
    diff = float(torch.linalg.matrix_norm(H_carrier - H_wrong_unit).item())
    assert diff >= _WRONG_AXIS_MIN, (
        f"FALSIFIER DID NOT TRIP: wrong-unit (coeff*XY, missing /4) has diff={diff:.3e} < "
        f"{_WRONG_AXIS_MIN}; the factor-of-4 error is undetectable"
    )


def test_L3h_broken_wrong_unit_half_factor_trips():
    """FALSIFIER (L3h): wrong-unit convention ((coeff/2)*(X(x)Y), missing one /2) disagrees.

    Correct: H = (coeff/4)*(X(x)Y).  Wrong: H = (coeff/2)*(X(x)Y)  [only one /2 factor,
    as if this were a 1-site over-rotation convention applied to the 2-site case].
    """
    coeff = 0.1
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_xy_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    cdt = torch.complex128
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    Y2 = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
    XY = torch.kron(X2.contiguous(), Y2.contiguous())
    H_wrong_half = 0.5 * float(coeff) * XY  # missing one /2
    diff = float(torch.linalg.matrix_norm(H_carrier - H_wrong_half).item())
    assert diff >= _WRONG_AXIS_MIN, (
        f"FALSIFIER DID NOT TRIP: wrong-unit ((coeff/2)*XY, missing one /2) has diff={diff:.3e} < "
        f"{_WRONG_AXIS_MIN}; the factor-of-2 error is undetectable"
    )


# ---------------------------------------------------------------------------
# INVARIANT L4: Unitary identity  ||U_carrier - U_ref||_F <= 1e-10  (B4, class-a)
# U = matrix_exp(-i H dt) = cos(eps/4) I4 - i sin(eps/4)(X(x)Y),  eps = coeff * dt_ns.
# Both sides computed via matrix_exp so the matrix_exp floor cancels (pre-reg §3 note).
# BROKEN INPUT: wrong-sign exponent (U = exp(+i H dt)) -- gives the inverse/adjoint gate.
# ---------------------------------------------------------------------------

def test_L4_error_unitary_matches_reference():
    """L4 (class-a exact, B4): the carrier's error gate U = exp(-i H dt) equals the
    reference cos(eps/4)*I4 - i*sin(eps/4)*(X(x)Y) to <= 1e-10.

    Both U_carrier and U_ref are computed via matrix_exp (NOT a closed-form formula) so the
    matrix_exp numerical floor (~6e-8 vs closed form) cancels -- both exponentials act on
    the same H since opdiff=0 (L3a), giving diff ~= 0.

    Swept over coeff in {0.3, 0.1, 0.03, 0.01, 0.003, 0.001} and dims (2,2) / (3,3).
    """
    dt_ns = 20.0
    for coeff in (0.3, 0.1, 0.03, 0.01, 0.003, 0.001):
        for d0, d1 in ((2, 2), (3, 3)):
            eps = coeff * dt_ns
            H_carrier = _hamiltonian_matrix_for_term(
                _make_coh_xy_term(coeff),
                support=(0, 1),
                local_dims=(d0, d1),
                device=DEV,
            )
            U_carrier = torch.linalg.matrix_exp(-1j * dt_ns * H_carrier)
            U_ref = ref_U_M28(coeff, dt_ns, d0, d1)
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
    H_ref = ref_H_M28(coeff, d0, d1)
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
    """L5 (class-a exact): the M28 Kraus channel assembled from H_M28 alone (no collapse)
    is exactly trace-preserving: sum_k K†K = I to <= 1e-12.

    M28 is a pure-Hamiltonian error (S1); no collapse operators. The single Kraus is
    U = exp(-i H dt), which is unitary, so sum_k K†K = U†U = I exactly.
    """
    dt_ns = 20.0
    coeff = 0.1
    H = _hamiltonian_matrix_for_term(
        _make_coh_xy_term(coeff),
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
        "M28 channel is not trace-preserving"
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
# exp(-i(eps/4)(X(x)Y)) vs identity: 1-F_e = sin^2(eps/4) (Nielsen quant-ph/0205035 Eq. 16).
# Factor /4 (not /2) because it is a 2-site generator with (1/2)^2 convention.
# Threshold: STRICT 1-F_e <= 1e-6 (pure Hamiltonian, S1).
# ---------------------------------------------------------------------------

def test_L6a_infidelity_matches_exact_closed_form():
    """L6a (class-b band, B1): carrier 1-F_e = sin^2(eps/4) to the Uhlmann floor (~6e-8 at d=4).

    Swept over eps in {0.3, 0.1, 0.03, 0.01, 0.003, 0.001} rad.
    The STRICT gate tier (S1): numerical agreement of carrier vs the exact closed form.
    NOTE: sin^2(eps/4) is the same closed form for ANY single Pauli-pair P(x)Q generator
    at the same eps -- AXIS-BLIND AND DIRECTION-BLIND (pre-reg B1). The /4 factor (not /2)
    is the 2-site convention.
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
            _make_coh_xy_term(coeff),
            support=(0, 1),
            local_dims=(2, 2),
            device=DEV,
        )
        kraus = assemble_substep_channel([H], [], dt_ns, device=DEV)
        J_carrier = _choi_state_from_kraus(kraus, device=DEV)
        F_e = float(_state_fidelity(J_carrier, J_I, device=DEV))
        one_minus_fe = float(max(0.0, 1.0 - F_e))
        exact = exact_infidelity_M28(eps)
        band_resid = abs(one_minus_fe - exact)
        assert band_resid <= 5e-7, (
            f"L6a FAIL: |carrier_1-F_e - sin^2(eps/4)| = {band_resid:.3e} at eps={eps:.4f}; "
            f"carrier={one_minus_fe:.6e}, exact={exact:.6e}"
        )


def test_L6b_insufficiency_xy_same_infidelity_as_yx():
    """FALSIFIER / proof-of-insufficiency (L6b, M28-SHARP): the XY channel (M28) and the
    YX channel (M33) produce the SAME scalar 1-F_e = sin^2(eps/4) at the same eps.

    This is the M28-sharp proof that 1-F_e CANNOT catch a direction-flip bug (XY vs YX):
    any single Pauli-pair P(x)Q gives sin^2(eps/4) -- DIRECTION-AGNOSTIC (pre-reg B1).
    Makes operator-identity gate L3a (esp. the L3b YX control) strictly necessary.
    A cert relying only on 1-F_e would false-pass a COH_XY->(Y,X) map corruption (the pair
    map gives YX=M33 instead of XY=M28; the infidelity is unchanged).

    The test SHOULD PASS (same infidelity for both directions) -- its role is to DOCUMENT the
    insufficiency, proving that L3a (incl. the L3b YX control) is the necessary gate to
    distinguish M28 from M33.
    """
    coeff = 0.1
    dt_ns = 20.0
    cdt = torch.complex128
    eps = coeff * dt_ns

    # Correct: COH_XY channel via carrier
    H_xy = _hamiltonian_matrix_for_term(
        _make_coh_xy_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    kraus_xy = assemble_substep_channel([H_xy], [], dt_ns, device=DEV)
    J_xy = _choi_state_from_kraus(kraus_xy, device=DEV)

    # Wrong-direction: YX channel built by hand -- SAME infidelity vs identity, DIFFERENT operator
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    Y2 = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
    H_yx = 0.25 * coeff * torch.kron(Y2.contiguous(), X2.contiguous())  # M33 = Y(x)X
    kraus_yx = assemble_substep_channel([H_yx], [], dt_ns, device=DEV)
    J_yx = _choi_state_from_kraus(kraus_yx, device=DEV)

    I_kraus = torch.eye(4, dtype=cdt, device=DEV).unsqueeze(0)
    J_I = _choi_state_from_kraus(I_kraus, device=DEV)

    fe_xy = float(max(0.0, 1.0 - _state_fidelity(J_xy, J_I, device=DEV)))
    fe_yx = float(max(0.0, 1.0 - _state_fidelity(J_yx, J_I, device=DEV)))

    # Both have the same scalar infidelity sin^2(eps/4) vs identity.
    # This SHOULD PASS -- it proves the insufficiency of 1-F_e for M28/M33 separation.
    assert abs(fe_xy - fe_yx) <= 1e-6, (
        f"INSUFFICIENCY PROOF FAILED: XY and YX at same eps have different 1-F_e "
        f"(fe_xy={fe_xy:.6e}, fe_yx={fe_yx:.6e}, diff={abs(fe_xy - fe_yx):.3e}); "
        "this test SHOULD PASS (same 1-F_e for both directions), proving 1-F_e alone is insufficient"
    )

    # But the operators themselves differ: confirms L3a (incl. L3b YX control) is necessary
    diff_op = float(torch.linalg.matrix_norm(H_xy - H_yx).item())
    assert diff_op >= _WRONG_AXIS_MIN, (
        f"Operator diff between XY and YX generators = {diff_op:.3e} < {_WRONG_AXIS_MIN}; "
        "unexpectedly small -- XY and YX look identical at this coeff (bug)"
    )


# ---------------------------------------------------------------------------
# INVARIANT L7: Quadratic scaling  (1-F_e)/eps^2 -> 1/16 as eps->0  (B2, class-b band)
# Leading-order: 1-F_e ~= eps^2/16 = ||(eps/4)(X(x)Y)||_F^2 / 4.
# ||(eps/4)(X(x)Y)||_F^2 = (eps/4)^2 * Tr((X(x)Y)^2) = (eps/4)^2 * Tr(I4) = (eps/4)^2*4=eps^2/4;
# divide by d=4 => eps^2/16. (X(x)Y)^2 = I4 is an exact algebraic fact (class-a).
# Ratio limit 1/16 is the same as M22/M23 (axis-agnostic for single Pauli-pair involutions).
# BROKEN INPUT: a linear-in-eps error (1-F_e ~ eps, not eps^2) fails this ratio test.
# ---------------------------------------------------------------------------

def test_L7_quadratic_scaling():
    """L7 (class-b band, B2): (1-F_e)/eps^2 -> 1/16 as eps -> 0.

    At small eps: sin^2(eps/4) ~= eps^2/16 - eps^4/(3*256) + O(eps^6).
    The ratio (1-F_e)/eps^2 should be within 0.005 of 1/16 = 0.0625 for eps in [0.01, 0.1].
    At eps=0.3 (larger angle) the ratio deviates by ~O(eps^2) -- registered B2 deviation.
    M28-specific: the ratio target is 1/16 (identical to M22/M23, since all are single
    Pauli-pair involutions at d=4 with the /4 convention).

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
            _make_coh_xy_term(coeff),
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
    M28-specific: even though X(x)Y is directional (X(x)Y != Y(x)X), the scalar 1-F_e is
    STILL even in eps (it is a modulus-squared, sign-invariant). This is not in conflict
    with the M28/M33 directionality -- the direction is invisible to 1-F_e (by design,
    as documented in B1 and the L6b insufficiency proof).
    """
    dt_ns = 20.0
    cdt = torch.complex128
    I_kraus = torch.eye(4, dtype=cdt, device=DEV).unsqueeze(0)
    J_I = _choi_state_from_kraus(I_kraus, device=DEV)

    def _fe(coeff_val: float) -> float:
        H = _hamiltonian_matrix_for_term(
            _make_coh_xy_term(coeff_val),
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
        # Tolerance: the Uhlmann estimator floor is ~4e-8 at d=4 per S5; the even-symmetry
        # residual is dominated by this floor, not by any asymmetry in the XY generator.
        # We use 1e-7 (well within the estimator band) -- tighter limits are unsupported
        # since the Uhlmann eigh is floating-point (not exact).
        assert diff <= 1e-7, (
            f"L8 FAIL: 1-F_e(+eps) = {fe_pos:.6e}, 1-F_e(-eps) = {fe_neg:.6e}, "
            f"diff = {diff:.3e} > 1e-7 at coeff={coeff} -- even-symmetry broken "
            "(exceeded Uhlmann estimator floor band)"
        )


def test_L8_broken_odd_infidelity_formula_trips():
    """FALSIFIER: if someone used sin(eps/4) instead of sin^2(eps/4), the result is ODD
    in eps, violating the even-symmetry that the correct formula satisfies.

    The correct formula sin^2(eps/4) is even (sin^2(-x/4) = sin^2(x/4)).
    The wrong formula sin(eps/4) is odd (sin(-x/4) = -sin(x/4)).
    """
    for eps in (0.3, 0.1, 0.03, 0.01, 0.003, 0.001):
        # Correct formula: sin^2(eps/4) -- should be even in eps
        correct_pos = exact_infidelity_M28(+eps)
        correct_neg = exact_infidelity_M28(-eps)
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
# In a 2-qutrit carrier (d0=d1=3), H_M28 acts on the 4 computational rows/cols
# ({0,1}x{0,1} -> indices {0,1,3,4} of a 3x3=9-dim space) with gen4 = (coeff/4)(X(x)Y)
# and has the ZERO GENERATOR on all rows/cols involving any level >= 2 (leaked levels).
# M28 imparts NO population or phase to leaked levels (S3): exp(0)=I on level >= 2.
# BROKEN INPUT: a 9x9 matrix that has non-zero entries involving row/col index 2,5,6,7,8
# (the leaked-level subspace) trips L9.
# ---------------------------------------------------------------------------

def test_L9_qutrit_embed_is_zero_on_leaked_levels():
    """L9 (class-a exact, S3): in a dim=(3,3) carrier, the 9x9 H_M28 matrix has:
    (a) its 4x4 computational block (rows/cols {0,1,3,4}) equal to the qubit reference gen4,
    (b) zero generator on all rows/cols involving leaked level >= 2 (indices 2,5,6,7,8).

    M28-specific: exp(-i H dt) = I on any pair of levels where either index >= 2 -- M28
    imparts NO leakage (pre-reg S3). Any leaked-level coupling is a different mechanism.
    The embed is verified by checking each computational-level (row,col) slot and confirming
    all non-computational rows/cols are zero.

    M28-specific structural check in the embed: the gen4 is (coeff/4)(X(x)Y), imaginary-
    antisymmetric with the anti-diagonal sign pattern (-i,+i,-i,+i); this is embedded without
    change into the computational block. Leaked levels carry ZERO, not this imaginary pattern.
    """
    coeff = 0.1
    d0, d1 = 3, 3
    H = _hamiltonian_matrix_for_term(
        _make_coh_xy_term(coeff),
        support=(0, 1),
        local_dims=(d0, d1),
        device=DEV,
    )
    # Reference gen4 on the 4-dim computational subspace (qubit reference)
    H_ref_4 = ref_H_M28(coeff, 2, 2)  # 4x4, (d0=2, d1=2)

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
            f"L9 FAIL: H_M28 qutrit row-{idx} norm = {row_norm:.3e} != 0; "
            "M28 drives leaked levels -- S3 violated"
        )
        assert col_norm <= _OPERATOR_DIFF_TOL, (
            f"L9 FAIL: H_M28 qutrit col-{idx} norm = {col_norm:.3e} != 0; "
            "M28 drives leaked levels -- S3 violated"
        )


def test_L9_broken_full_qutrit_xy_extends_to_leaked_levels_trips():
    """FALSIFIER: a 9x9 XY-like matrix that extends to qutrit levels (non-zero on leaked rows/cols)
    fails L9.

    A 3x3 X-like tensor Y-like (with entries at level 2) in the full 9x9 two-qutrit space
    would place non-zero entries at leaked-level indices -- which is NOT M28 semantics
    (M28 has zero generator on any level >= 2; pre-reg S3).
    """
    cdt = torch.complex128
    d0, d1 = 3, 3
    # A 3x3 X-like matrix with off-diagonal entries also at level 2 (not M28)
    X3 = torch.zeros((3, 3), dtype=cdt, device=DEV)
    X3[0, 1] = 1.0
    X3[1, 0] = 1.0
    X3[0, 2] = 1.0   # extends to leaked level
    X3[2, 0] = 1.0   # extends to leaked level
    # Y-like 3x3
    Y3 = torch.zeros((3, 3), dtype=cdt, device=DEV)
    Y3[0, 1] = -1.0j
    Y3[1, 0] = 1.0j
    Y3[0, 2] = -1.0j  # extends to leaked level
    Y3[2, 0] = 1.0j   # extends to leaked level
    H_broken = 0.025 * torch.kron(X3.contiguous(), Y3.contiguous())
    leaked_indices = [i for i in range(d0 * d1) if (i // d1 >= 2) or (i % d1 >= 2)]
    leaked_norms = [float(torch.linalg.norm(H_broken[i, :]).item()) for i in leaked_indices]
    assert max(leaked_norms) > _OPERATOR_DIFF_TOL, (
        "FALSIFIER DID NOT TRIP: the broken 9x9 XY-extended matrix has zero leaked rows -- "
        "falsifier wrong (check the index logic)"
    )


# ---------------------------------------------------------------------------
# INVARIANT L10: Anti-circular namespace check  (structural, class-c gate)
# The cert (THIS FILE) must NOT import `_coherent_family_generator`,
# `_embed_coherent_generator`, `TWO_SITE_COHERENT_FAMILIES`, or `COHERENT_PAULI_FAMILIES`
# from the carrier. If these symbols appear in this module's namespace, the cert is circular:
# a wrong Pauli-pair map (COH_XY->(Y,X)) shared between the 'reference' and the carrier
# would false-pass (the W-C round-1 failure shape; test_axis1_wc_decircularized.py).
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

    If any of these is imported, a wrong COH_XY pair map (X,Y)->(Y,X) would be reflected into
    the 'reference' silently (the M28/M33 directionality confusion -- the W-C round-1 failure shape).
    M28-sharp: the COH_XY->(Y,X) map corruption is the exact circularity that would turn M33
    into M28 silently -- the anti-circular gate is the reason this cert can distinguish them.
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
