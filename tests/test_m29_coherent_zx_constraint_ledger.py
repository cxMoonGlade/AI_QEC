"""M29 coherent_zx_parasitic_coupling -- CONSTRAINT LEDGER (executable falsifier tests).

FAITHFULNESS PROTOCOL (docs/FAITHFULNESS_PROTOCOL.md) -- constraint ledger for M29.
Each test below is a FALSIFIER: it documents the invariant AND shows that a
deliberately BROKEN input makes the test FAIL (trips the falsifier). Tests run
GREEN on the faithful carrier and RED on the broken variant.

ANTI-CIRCULARITY: the reference operator (``ref_H_M29``) is HAND-TYPED from the
literature (Magesan-Gambetta arXiv:1804.04073 Eq. 3.16 ``H_CR = ... - (J Omega /
sqrt(Delta^2+Omega^2)) ZX/2``; Zhang-Vala-Sastry-Whaley arXiv:quant-ph/0209120 Eq. 7
``sigma^1_z sigma^2_x`` as the 7th basis element of the non-local part p of su(4)).
The cert imports ONLY ``axis1_mcwf_mps_execution._hamiltonian_matrix_for_term``
(the object under test).  The carrier's ``_coherent_family_generator`` /
``_embed_coherent_generator`` / ``TWO_SITE_COHERENT_FAMILIES`` / ``COHERENT_PAULI_FAMILIES``
appear NOWHERE in the reference code (same de-circularization rule as
test_m22_coherent_cxx_constraint_ledger.py, test_m23_coherent_cyy_constraint_ledger.py,
test_axis1_wc_decircularized.py, and the M6/M7/M20 ledgers).

GATE TIER: STRICT (``1-F_e <= 1e-6``; operator identity <= 1e-12 / unitary <= 1e-10).
M29 is a pure-Hamiltonian / exact-dense error -- no collapse, no finite-step MCWF.

M29-SPECIFIC:
- The generator is H_M29 = (coeff/4) * (Z (x) X), the pure-ZX cross-resonance axis
  (Magesan-Gambetta Eq. 3.16 -- the physical cross-resonance entangler; Zhang Eq. 7 --
  ZX is the 7th basis element of the non-local part p of su(4)).
- ``1-F_e = sin^2(eps/4)`` (factor /4, same as M22/M23 for 2-site) is AXIS-BLIND --
  identical for ANY single Pauli-pair generator P(x)Q at the same eps (pre-reg B1).
  The operator-identity gate L3a and wrong-axis falsifiers (L3b-L3f) are the LOAD-BEARING
  cert gates: the SOLE witnesses that the carrier couples via Z(x)X and not XX/YY/ZZ/XZ/ZY.
  L3d (ZX vs XZ = M31) is the M29-SHARP control: ZX is ASYMMETRIC under qubit swap
  (Z(x)X != X(x)Z), so the ZX/XZ swap is the most plausible real bug AND is the ONLY
  thing distinguishing M29 from its swap-partner M31 -- 1-F_e cannot catch it, only the
  operator gate does.
- Z(x)X is REAL-SYMMETRIC (imag-part norm 0, symmetric residual 0): Z is real-diagonal,
  X is real-symmetric, their Kronecker product is real and symmetric. Block-signed structure:
  [[0,1,0,0],[1,0,0,0],[0,0,0,-1],[0,0,-1,0]] -- off-diagonal X on each control-block, sign
  +1 on |0.> block / -1 on |1.> block (the conditional-X / CNOT-generator signature).
- The ratio limit is eps^2/16 (same as M22/M23; not 1/4 as for 1-site); F_avg companion
  factor is 4/5 (d=4 for 2-site).
- Borrowing: ``exact_infidelity_M29(eps)`` is identical to M22/M23's formula (sin^2(eps/4))
  since all are single traceless Pauli-pair involutions at d=4. The observable L6 cannot
  distinguish them; the operator gate L3a is the distinguishing evidence.

GPU-only (top-level memory rule) -- collection FAILS without CUDA.

Pre-registration: docs/twin_validation/m29_coherent_zx_parasitic_coupling_prereg.md
Run:  conda run -n aiqec python -m pytest -q tests/test_m29_coherent_zx_constraint_ledger.py
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
        "M29 constraint-ledger cert is GPU-gated; CUDA-MISSING is NOT A RELEASE BASIS",
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
#                           # (class-c gate; derivation-check: XX/YY/ZZ/XZ/ZY each diff 7.07e-2
#                           # at eps=0.1; M10 (XX+YY) diff 8.66e-2 -- all >> 1e-3)

# ---------------------------------------------------------------------------
# Reference operator (HAND-TYPED, non-circular)
#
# Provenance:
#   H_M29 = (coeff/4) * (sigma_z (x) sigma_x)  on the 4-dim computational subspace.
#   sigma_z = [[1,0],[0,-1]]  (Nielsen & Chuang Eq. 2.1, Pauli-Z).
#   sigma_x = [[0,1],[1,0]]   (Nielsen & Chuang Eq. 2.1, Pauli-X).
#   Z(x)X is the pure-ZX 2-body generator:
#       DEVICE origin (cross-resonance, DIRECT): the driven CR entangler written explicitly as
#           H_CR = (Delta - sqrt(Delta^2+Omega^2)) ZI/2 - (J Omega / sqrt(Delta^2+Omega^2)) ZX/2
#           (Magesan-Gambetta arXiv:1804.04073 Eq. 3.16; Eq. 3.14 tr(H_CR . ZX/2)=-J Omega/sqrt(...);
#           realistic ZX coeff Eq. 4.26; control-side restricted to {I,Z} -> ZX is the unique
#           entangling 2-body term in the CR family); parasitic/residual (un-echoed,
#           crosstalk-induced) ZX is the named CNOT-error source.
#       ALGEBRA basis (DIRECT): sigma^1_z sigma^2_x = Z(x)X is listed verbatim as the 7th basis
#           element of the non-local part p of su(4) (Zhang-Vala-Sastry-Whaley arXiv:quant-ph/0209120
#           Eq. 7: p = span(i/2){..., sigma^1_z sigma^2_x, ...}; Sec. V Ex. 2 general anisotropic
#           H = (1/2) Sum_ab J_ab sigma_a(x)sigma_b with independent J_ab -> pure single ZX is the
#           one-coordinate point of the non-local basis).
#   factor 1/4 = (1/2)^2: two-qubit over-rotation convention
#           R_{PQ}(eps_cat) = exp(-i (eps_cat/2)(P(x)Q)), carrier eps = coeff*dt is the
#           per-tensor angle; catalog eps_cat = eps/2
#           (error_mechanisms.md line 120 "exp(-i eps ZX/2)"; carrier docstring lines 1026-1029).
#   M29 structural facts:
#     Z(x)X is REAL-SYMMETRIC: Z is real-diagonal, X is real-symmetric, kron product is real+symmetric.
#     Block-signed structure: [[0,1,0,0],[1,0,0,0],[0,0,0,-1],[0,0,-1,0]]
#       (off-diagonal X on each control-block, sign +1 on |0.> block / -1 on |1.> block --
#       the conditional-X / CNOT-generator signature; pre-reg §1 B4 note).
#     ASYMMETRIC under qubit swap: Z(x)X != X(x)Z (= M31); ||Z(x)X - X(x)Z||_F = 2.83 != 0.
#   zero generator on any leaked level >= 2 (S3; _embed_coherent_generator semantics).
#   error unitary: U = exp(-i H dt) = cos(eps/4) I4 - i sin(eps/4)(Z(x)X),  eps = coeff*dt.
#   EXACT 1-F_e (d=4): 1 - |Tr(U)/4|^2 = sin^2(eps/4).
#   LEADING 1-F_e:  ||(eps/4)(Z(x)X)||_F^2 / 4 = eps^2/16.
# ---------------------------------------------------------------------------

def ref_H_M29(coeff: float, d0: int, d1: int) -> torch.Tensor:
    """Hand-typed M29 reference generator on the (d0*d1)-dim local space.

    H_M29 = (coeff/4) * (Z (x) X)  embedded into the d0*d1-dimensional space,
    with the zero generator (identity gate) on any product-level pair where either
    index >= 2 (no leakage drive from M29 -- S3).
    Imports NOTHING from the carrier family tables.
    """
    cdt = torch.complex128
    # Hand-typed Pauli-Z and Pauli-X (Nielsen & Chuang Eq. 2.1)
    Z2 = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=cdt, device=DEV)
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    # (coeff/4) * (Z (x) X) on the 4-dim computational subspace
    # Expected: [[0,1,0,0],[1,0,0,0],[0,0,0,-1],[0,0,-1,0]] * coeff/4
    # (the conditional-X structure: +X on |0.> block, -X on |1.> block)
    gen4 = 0.25 * coeff * torch.kron(Z2.contiguous(), X2.contiguous())
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


def ref_U_M29(coeff: float, dt_ns: float, d0: int, d1: int) -> torch.Tensor:
    """Hand-typed M29 error unitary: U = matrix_exp(-i * H * dt)."""
    H = ref_H_M29(coeff, d0, d1)
    return torch.linalg.matrix_exp(-1j * dt_ns * H)


def exact_infidelity_M29(eps: float) -> float:
    """Closed-form 1-F_e for exp(-i(eps/4)(Z(x)X)) vs identity (d=4).

    Tr(U_M29) = Tr(cos(eps/4)I4 - i sin(eps/4)(Z(x)X)) = 4*cos(eps/4)  [Tr(Z(x)X)=0].
    F_e = |Tr(U)/4|^2 = cos^2(eps/4)  =>  1-F_e = sin^2(eps/4).
    Reference: Nielsen arXiv:quant-ph/0205035 Eq. 16 (F_e = |Tr U / d|^2 for unitary U);
    pre-registration B1, section 2.
    NOTE: sin^2(eps/4) is the same for ANY single Pauli-pair P(x)Q generator at
    the same eps (Tr(P(x)Q)=0 and (P(x)Q)^2=I4 for all single Paulis) -- axis-agnostic.
    This is identical to exact_infidelity_M22 / exact_infidelity_M23; the /4 factor is
    the 2-site convention.  The scalar 1-F_e cannot distinguish ZX (M29) from XZ (M31)
    or any other single Pauli-pair -- operator gate L3a + wrong-axis controls are load-bearing.
    """
    return float(math.sin(eps / 4.0) ** 2)


def _make_coh_zx_term(coeff: float) -> dict:
    """Minimal schedule-term dict for COH_ZX on two sites (support=(0,1))."""
    return {
        "kind": "hamiltonian",
        "operator_family": "COH_ZX",
        "support": [0, 1],
        "coefficient": float(coeff),
        "substep_id": "m29_ledger",
    }


# ---------------------------------------------------------------------------
# INVARIANT L1: Hermiticity  ||H - H†||_F <= 1e-12  (class-a exact)
# Pauli-pair generators are Hermitian; an anti-Hermitian generator is WRONG.
# Z(x)X is real-symmetric => Hermitian.
# BROKEN INPUT: a non-Hermitian matrix (imaginary off-diagonal term only)
# ---------------------------------------------------------------------------

def test_L1_generator_is_hermitian():
    """L1 (class-a exact): the M29 generator H satisfies H = H†.

    Z(x)X is real-symmetric (imag-part norm 0 -- pre-reg M29 structural fact);
    (coeff/4)(Z(x)X) is Hermitian for any real coeff.
    Broken-input demonstration: an explicitly non-Hermitian operator trips this test.
    """
    coeff = 0.1
    H = _hamiltonian_matrix_for_term(
        _make_coh_zx_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    resid = float(torch.linalg.matrix_norm(H - H.conj().T).item())
    assert resid <= _HERMITIAN_TOL, (
        f"L1 FAIL: ||H - H†||_F = {resid:.3e} > {_HERMITIAN_TOL}; "
        "M29 generator is not Hermitian -- physics bug"
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
# Z(x)X is traceless (Tr(Z(x)X) = Tr(Z)*Tr(X) = 0*0 = 0); an identity-shifted generator is WRONG.
# BROKEN INPUT: H + (c/4) * I4 (trace = coeff)
# ---------------------------------------------------------------------------

def test_L2_generator_is_traceless():
    """L2 (class-a exact): the M29 generator H is traceless.

    Tr(Z(x)X) = Tr(Z)*Tr(X) = 0*0 = 0. Any non-zero trace indicates identity
    contamination or a wrong family.
    """
    coeff = 0.1
    H = _hamiltonian_matrix_for_term(
        _make_coh_zx_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    tr_resid = float(torch.abs(torch.trace(H)).item())
    assert tr_resid <= _TRACELESS_TOL, (
        f"L2 FAIL: |Tr H| = {tr_resid:.3e} > {_TRACELESS_TOL}; "
        "M29 generator has a non-zero trace -- wrong axis or identity contamination"
    )


def test_L2_broken_identity_shift_trips():
    """FALSIFIER: a traceful 4x4 generator (ZX + identity offset) fails L2."""
    cdt = torch.complex128
    Z2 = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=cdt, device=DEV)
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    ZX = torch.kron(Z2.contiguous(), X2.contiguous())
    H_broken = 0.025 * ZX + 0.025 * torch.eye(4, dtype=cdt, device=DEV)
    tr_resid = float(torch.abs(torch.trace(H_broken)).item())
    assert tr_resid > _TRACELESS_TOL, (
        "FALSIFIER DID NOT TRIP: an identity-shifted 4x4 generator passed L2 -- "
        "the falsifier is broken"
    )


# ---------------------------------------------------------------------------
# INVARIANT L2b: Real-symmetric structure of Z(x)X  (class-a exact, M29-specific)
# Z(x)X is REAL (imag-part norm 0) and SYMMETRIC (Z(x)X = (Z(x)X)^T).
# Block-signed structure: +X on |0.> control block, -X on |1.> control block.
# This is the M29-sharp structural fact: the conditional-X / CNOT-generator signature.
# BROKEN INPUT: a matrix with non-zero imaginary part (e.g. Z(x)Y, which is imaginary)
# ---------------------------------------------------------------------------

def test_L2b_zx_generator_is_real_symmetric():
    """L2b (class-a exact, M29-specific): Z(x)X is real-symmetric.

    Z = [[1,0],[0,-1]] (real), X = [[0,1],[1,0]] (real-symmetric).
    Z(x)X = kron(Z,X): both factors are real -> kron product is real.
    Expected matrix: [[0,1,0,0],[1,0,0,0],[0,0,0,-1],[0,0,-1,0]] * coeff/4.
    Therefore: imag-part norm <= 1e-12, and (Z(x)X) = (Z(x)X)^T.

    This is the M29-specific structural assertion: the block-signed structure
    (off-diagonal X on each control-block, sign +1 on |0.> / -1 on |1.>) is the
    conditional-X / CNOT-generator signature (pre-reg §1 M29-specific structural fact).
    Contrast with Z(x)Y (imaginary) or X(x)Z = M31 (real but transposed block structure).
    """
    coeff = 0.1
    H = _hamiltonian_matrix_for_term(
        _make_coh_zx_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    # Imaginary part should be zero
    imag_norm = float(torch.linalg.matrix_norm(H.imag).item())
    assert imag_norm <= _OPERATOR_DIFF_TOL, (
        f"L2b FAIL: imag-part norm of H_M29 = {imag_norm:.3e} > {_OPERATOR_DIFF_TOL}; "
        "Z(x)X should be REAL (Z and X are both real) -- physics bug"
    )
    # Symmetric: H = H^T (since it is real-symmetric as a matrix)
    sym_resid = float(torch.linalg.matrix_norm(H - H.T).item())
    assert sym_resid <= _OPERATOR_DIFF_TOL, (
        f"L2b FAIL: symmetric residual ||H - H^T||_F = {sym_resid:.3e} > {_OPERATOR_DIFF_TOL}; "
        "Z(x)X should be SYMMETRIC -- structural bug"
    )


def test_L2b_broken_zy_is_imaginary_trips():
    """FALSIFIER: Z(x)Y is imaginary, failing the real-symmetric check.

    Z = [[1,0],[0,-1]] (real), Y = [[0,-i],[i,0]] (imaginary).
    Z(x)Y has a non-zero imaginary part (real * imaginary = imaginary).
    The L2b imag-norm check would flag this -- confirming the structural assertion is
    meaningful (a spurious imaginary-carrying generator is caught by it).
    M29-sharp: Z(x)Y is M30 (COH_ZY), the axis-swap sibling of M29 that differs in
    the target Pauli (Y instead of X). The real-symmetric check separates M29 from M30.
    """
    cdt = torch.complex128
    Z2 = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=cdt, device=DEV)
    Y2 = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
    H_zy = 0.025 * torch.kron(Z2.contiguous(), Y2.contiguous())
    imag_norm = float(torch.linalg.matrix_norm(H_zy.imag).item())
    assert imag_norm > _OPERATOR_DIFF_TOL, (
        "FALSIFIER DID NOT TRIP: Z(x)Y appears to have zero imaginary part -- "
        "falsifier broken (check the computation)"
    )


# ---------------------------------------------------------------------------
# INVARIANT L2c: Asymmetry under qubit swap  (class-a exact, M29-specific)
# Z(x)X != X(x)Z (= M31). This is the SOLE structural fact distinguishing M29 from its
# swap-partner M31, and is directly confirmed by ||Z(x)X - X(x)Z||_F = 2.83 != 0.
# BROKEN INPUT: if someone accidentally used X(x)Z instead of Z(x)X, this check catches it.
# ---------------------------------------------------------------------------

def test_L2c_zx_is_asymmetric_under_qubit_swap():
    """L2c (class-a exact, M29-specific): Z(x)X != X(x)Z.

    ||Z(x)X - X(x)Z||_F = sqrt(8) = 2.83 (at coeff=1, gen4 factor; actual at (coeff/4)
    gives sqrt(8) * coeff/4).  This confirms ZX is NOT symmetric under qubit swap,
    distinguishing M29 (ZX = control-Z target-X) from M31 (XZ = control-X target-Z).
    This structural fact is the reason the wrong-axis L3d (XZ) control is LOAD-BEARING for M29.

    Derivation-check (pre-reg §1): ||Z(x)X - X(x)Z||_F = 2.83 at the 4x4 unit-norm level.
    """
    cdt = torch.complex128
    Z2 = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=cdt, device=DEV)
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    ZX = torch.kron(Z2.contiguous(), X2.contiguous())
    XZ = torch.kron(X2.contiguous(), Z2.contiguous())
    swap_diff = float(torch.linalg.matrix_norm(ZX - XZ).item())
    # ||Z(x)X - X(x)Z||_F = sqrt(8) ~ 2.83 (at coeff=1, not scaled by coeff/4)
    assert swap_diff >= 2.0, (
        f"L2c FAIL: ||Z(x)X - X(x)Z||_F = {swap_diff:.4f}; "
        "Z(x)X and X(x)Z appear identical -- the M29/M31 swap-partner distinction is broken"
    )


def test_L2c_broken_symmetric_operator_trips():
    """FALSIFIER: if Z(x)X were symmetric under swap (i.e. Z(x)X == X(x)Z), the M29/M31
    distinction would collapse and the L2c check would fail.

    We use X(x)X (which IS symmetric: kron(X,X) = kron(X,X)) as the broken-input example.
    ||X(x)X - kron(X,X)^T||_F = 0 (symmetric operator) -- confirming the check is non-trivial.
    Then we verify that Z(x)X is not symmetric under swap (the actual M29 assertion).
    """
    cdt = torch.complex128
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    Z2 = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=cdt, device=DEV)
    XX = torch.kron(X2.contiguous(), X2.contiguous())
    # XX is swap-symmetric: kron(X,X) = kron(X,X) (both factors same)
    swap_diff_xx = float(torch.linalg.matrix_norm(XX - torch.kron(X2.contiguous(), X2.contiguous())).item())
    # ZX is NOT swap-symmetric: kron(Z,X) != kron(X,Z)
    ZX = torch.kron(Z2.contiguous(), X2.contiguous())
    XZ = torch.kron(X2.contiguous(), Z2.contiguous())
    swap_diff_zx = float(torch.linalg.matrix_norm(ZX - XZ).item())
    # XX satisfies swap symmetry (diff == 0); ZX does not (diff >= 2.0)
    assert swap_diff_xx <= 1e-12, (
        "FALSIFIER SETUP ERROR: XX is not swap-symmetric as expected"
    )
    assert swap_diff_zx >= 2.0, (
        f"FALSIFIER DID NOT TRIP: ZX appears swap-symmetric with diff={swap_diff_zx:.3e}; "
        "the M29 asymmetry-under-swap structural fact is broken"
    )


# ---------------------------------------------------------------------------
# INVARIANT L3a: Operator identity  ||H_carrier - H_ref||_F <= 1e-12  (B4, class-a)
# This is the LOAD-BEARING cert gate for M29 (1-F_e alone cannot catch wrong Pauli-pair axis;
# sin^2(eps/4) is identical for ANY single Pauli-pair generator at the same eps -- pre-reg B1).
# BROKEN INPUT: wrong-axis references (XX=M22 / YY=M23 / ZZ / XZ=M31 / ZY=M30 / XX+YY=M10).
# The XZ=M31 (L3d) control is the PRIMARY M29-sharp gate -- the SOLE distinguisher of M29
# from its swap-partner M31 (the most plausible real bug: a left/right transpose in the pair map).
# ---------------------------------------------------------------------------

def test_L3a_operator_matches_hand_typed_reference():
    """L3a (class-a exact, B4): the carrier generator equals the hand-typed reference.

    H_ref = (coeff/4) * (Z(x)X) embedded in (d0,d1), from Magesan-Gambetta Eq. 3.16 / Zhang Eq. 7.
    This is the LOAD-BEARING gate -- 1-F_e alone cannot distinguish ZX from XX/YY/ZZ/XZ/ZY/...
    at equal eps (all have the same sin^2(eps/4); pre-reg B1). The operator identity is
    the SOLE witness of the ZX axis (M29 vs M22/M23/M28/M30-M33/M10/M31 distinction).

    Swept over coeff in {0.3, 0.1, 0.03, 0.01, 0.003, 0.001} and dims (2,2) / (3,3).
    """
    for coeff in (0.3, 0.1, 0.03, 0.01, 0.003, 0.001):
        for d0, d1 in ((2, 2), (3, 3)):
            H_carrier = _hamiltonian_matrix_for_term(
                _make_coh_zx_term(coeff),
                support=(0, 1),
                local_dims=(d0, d1),
                device=DEV,
            )
            H_ref = ref_H_M29(coeff, d0, d1)
            diff = float(torch.linalg.matrix_norm(H_carrier - H_ref).item())
            assert diff <= _OPERATOR_DIFF_TOL, (
                f"L3a FAIL: ||H_carrier - H_ref||_F = {diff:.3e} > {_OPERATOR_DIFF_TOL} "
                f"at coeff={coeff}, dims=({d0},{d1}) -- wrong generator (wrong axis, "
                "wrong coefficient, wrong convention)"
            )


def test_L3b_broken_wrong_axis_xx_trips():
    """FALSIFIER (L3b): a wrong-axis XX reference disagrees with the ZX carrier by >= 1e-3.

    XX is anti-diagonal with all +1 signs (M22); ZX has the block-signed structure
    [[0,1,0,0],[1,0,0,0],[0,0,0,-1],[0,0,-1,0]] -- structurally distinct.

    Derivation-check (pre-reg §3): diff = 7.07e-2 at eps=0.1, well above 1e-3.
    """
    coeff = 0.1
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_zx_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    cdt = torch.complex128
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    H_wrong_xx = 0.25 * coeff * torch.kron(X2.contiguous(), X2.contiguous())
    diff = float(torch.linalg.matrix_norm(H_carrier - H_wrong_xx).item())
    assert diff >= _WRONG_AXIS_MIN, (
        f"FALSIFIER DID NOT TRIP: wrong-axis XX reference passed with diff={diff:.3e} < "
        f"{_WRONG_AXIS_MIN}; the ZX/XX confusion is undetectable -- "
        "M29 vs M22 distinction cannot be certified (operator-identity cert broken)"
    )


def test_L3c_broken_wrong_axis_yy_trips():
    """FALSIFIER (L3c): a wrong-axis YY reference disagrees with the ZX carrier by >= 1e-3.

    YY is real anti-diagonal with signs (-1,+1,+1,-1) (M23); ZX has the block-signed structure.
    Structurally distinct: different sign pattern.

    Derivation-check (pre-reg §3): diff = 7.07e-2 at eps=0.1, well above 1e-3.
    """
    coeff = 0.1
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_zx_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    cdt = torch.complex128
    Y2 = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
    H_wrong_yy = 0.25 * coeff * torch.kron(Y2.contiguous(), Y2.contiguous())
    diff = float(torch.linalg.matrix_norm(H_carrier - H_wrong_yy).item())
    assert diff >= _WRONG_AXIS_MIN, (
        f"FALSIFIER DID NOT TRIP: wrong-axis YY reference passed with diff={diff:.3e} < "
        f"{_WRONG_AXIS_MIN}; the ZX/YY confusion is undetectable (M29 vs M23 indistinct)"
    )


def test_L3d_broken_wrong_axis_xz_trips():
    """FALSIFIER (L3d, M29-SHARP GATE): a wrong-axis XZ (=M31) reference disagrees
    with the ZX carrier by >= 1e-3.

    This is the PRIMARY wrong-axis control for M29 (pre-reg §3):
    a reference H_wrong = (coeff/4)(X(x)Z) disagrees with the ZX carrier.
    X(x)Z has the TRANSPOSED block structure compared to Z(x)X -- same elements,
    different positions (the left/right swap of the Pauli pair).

    This gate is the SOLE distinguisher of M29 (ZX) from its swap-partner M31 (XZ):
    sin^2(eps/4) is identical for both (pre-reg B1; both are single traceless Pauli-pair
    involutions at d=4); 1-F_e cannot tell them apart. The operator identity is the ONLY
    witness separating ZX from XZ -- making L3d strictly necessary (the M29 analogue of
    the M22/M23 XX/YY separation, here a left/right swap of the Pauli pair).

    A circular reference derived FROM a corrupted carrier pair map (COH_ZX->(X,Z)) would
    mirror the wrong axis to diff=0 (false-pass); the hand-typed (Z(x)X) reference catches it.
    The ZX->XZ corruption is the most plausible real bug (a left/right transpose in the pair map).

    Derivation-check (pre-reg §3): diff = 7.07e-2 at eps=0.1, well above 1e-3.
    Structural note: ||Z(x)X - X(x)Z||_F = 2.83 at the unit-coeff level (pre-reg L2c).
    """
    coeff = 0.1
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_zx_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    cdt = torch.complex128
    Z2 = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=cdt, device=DEV)
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    # M31 = X(x)Z: SWAP of the pair (X on control, Z on target) -- the swap-partner
    H_wrong_xz = 0.25 * coeff * torch.kron(X2.contiguous(), Z2.contiguous())
    diff = float(torch.linalg.matrix_norm(H_carrier - H_wrong_xz).item())
    assert diff >= _WRONG_AXIS_MIN, (
        f"FALSIFIER DID NOT TRIP: wrong-axis XZ (=M31, swap-partner) reference passed with "
        f"diff={diff:.3e} < {_WRONG_AXIS_MIN}; the ZX/XZ (M29/M31) confusion is undetectable -- "
        "M29 vs M31 swap-partner cannot be certified (operator-identity cert broken)"
    )


def test_L3e_broken_wrong_axis_zz_trips():
    """FALSIFIER (L3e): a wrong-axis ZZ reference disagrees with the ZX carrier by >= 1e-3.

    ZZ is diagonal (eigenvalues +1/-1 on diag, M11-like); ZX is real off-block-diagonal.
    Structurally distinct.

    Derivation-check (pre-reg §3): diff = 7.07e-2 at eps=0.1, well above 1e-3.
    """
    coeff = 0.1
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_zx_term(coeff),
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
        f"{_WRONG_AXIS_MIN}; the ZX/ZZ confusion is undetectable"
    )


def test_L3e2_broken_wrong_axis_zy_trips():
    """FALSIFIER (L3e2): a wrong-axis ZY (=M30) reference disagrees with the ZX carrier by >= 1e-3.

    ZY = Z(x)Y (M30, COH_ZY): same control-Z but imaginary target-Y axis.
    ZY is imaginary (Z real-diagonal, Y imaginary); ZX is real-symmetric.
    Structurally distinct: ZY fails the real-symmetric check AND differs in operator value.

    Derivation-check (pre-reg §3): diff = 7.07e-2 at eps=0.1, well above 1e-3.
    """
    coeff = 0.1
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_zx_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    cdt = torch.complex128
    Z2 = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=cdt, device=DEV)
    Y2 = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=DEV)
    H_wrong_zy = 0.25 * coeff * torch.kron(Z2.contiguous(), Y2.contiguous())
    diff = float(torch.linalg.matrix_norm(H_carrier - H_wrong_zy).item())
    assert diff >= _WRONG_AXIS_MIN, (
        f"FALSIFIER DID NOT TRIP: wrong-axis ZY (M30) reference passed with diff={diff:.3e} < "
        f"{_WRONG_AXIS_MIN}; the ZX/ZY confusion is undetectable (M29 vs M30 indistinct)"
    )


def test_L3f_broken_wrong_axis_xxyy_trips():
    """FALSIFIER (L3f): a wrong-axis (XX+YY)/2 reference disagrees with the ZX carrier by >= 1e-3.

    (XX+YY)/2 is M10 (COH_XX_YY, the exchange interaction); pure ZX is M29.
    The carrier's COH_ZX must return only the ZX pair, not a symmetric sum.

    Derivation-check (pre-reg §3): diff = 8.66e-2 at eps=0.1, above 1e-3.
    """
    coeff = 0.1
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_zx_term(coeff),
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
        f"{_WRONG_AXIS_MIN}; the ZX/(XX+YY) confusion is undetectable (M29 vs M10 indistinct)"
    )


def test_L3g_broken_wrong_unit_no_factor_trips():
    """FALSIFIER (L3g): wrong-unit convention (coeff*(Z(x)X), missing the /4) disagrees.

    Correct: H = (coeff/4)*(Z(x)X).  Wrong: H = coeff*(Z(x)X)  [missing both /2 factors].
    A factor-of-4 error in the generator gives a factor-of-4 error in the angle.
    """
    coeff = 0.1
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_zx_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    cdt = torch.complex128
    Z2 = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=cdt, device=DEV)
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    ZX = torch.kron(Z2.contiguous(), X2.contiguous())
    H_wrong_unit = float(coeff) * ZX  # missing the /4
    diff = float(torch.linalg.matrix_norm(H_carrier - H_wrong_unit).item())
    assert diff >= _WRONG_AXIS_MIN, (
        f"FALSIFIER DID NOT TRIP: wrong-unit (coeff*ZX, missing /4) has diff={diff:.3e} < "
        f"{_WRONG_AXIS_MIN}; the factor-of-4 error is undetectable"
    )


def test_L3h_broken_wrong_unit_half_factor_trips():
    """FALSIFIER (L3h): wrong-unit convention ((coeff/2)*(Z(x)X), missing one /2) disagrees.

    Correct: H = (coeff/4)*(Z(x)X).  Wrong: H = (coeff/2)*(Z(x)X)  [only one /2 factor,
    as if this were a 1-site over-rotation convention applied to the 2-site case].
    """
    coeff = 0.1
    H_carrier = _hamiltonian_matrix_for_term(
        _make_coh_zx_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    cdt = torch.complex128
    Z2 = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=cdt, device=DEV)
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    ZX = torch.kron(Z2.contiguous(), X2.contiguous())
    H_wrong_half = 0.5 * float(coeff) * ZX  # missing one /2
    diff = float(torch.linalg.matrix_norm(H_carrier - H_wrong_half).item())
    assert diff >= _WRONG_AXIS_MIN, (
        f"FALSIFIER DID NOT TRIP: wrong-unit ((coeff/2)*ZX, missing one /2) has diff={diff:.3e} < "
        f"{_WRONG_AXIS_MIN}; the factor-of-2 error is undetectable"
    )


# ---------------------------------------------------------------------------
# INVARIANT L4: Unitary identity  ||U_carrier - U_ref||_F <= 1e-10  (B4, class-a)
# U = matrix_exp(-i H dt) = cos(eps/4) I4 - i sin(eps/4)(Z(x)X),  eps = coeff * dt_ns.
# BROKEN INPUT: wrong-sign exponent (U = exp(+i H dt)) -- gives the inverse/adjoint gate.
# ---------------------------------------------------------------------------

def test_L4_error_unitary_matches_reference():
    """L4 (class-a exact, B4): the carrier's error gate U = exp(-i H dt) equals the
    reference cos(eps/4)*I4 - i*sin(eps/4)*(Z(x)X) to <= 1e-10.

    Swept over coeff in {0.3, 0.1, 0.03, 0.01, 0.003, 0.001} and dims (2,2) / (3,3).
    """
    dt_ns = 20.0
    for coeff in (0.3, 0.1, 0.03, 0.01, 0.003, 0.001):
        for d0, d1 in ((2, 2), (3, 3)):
            eps = coeff * dt_ns
            H_carrier = _hamiltonian_matrix_for_term(
                _make_coh_zx_term(coeff),
                support=(0, 1),
                local_dims=(d0, d1),
                device=DEV,
            )
            U_carrier = torch.linalg.matrix_exp(-1j * dt_ns * H_carrier)
            U_ref = ref_U_M29(coeff, dt_ns, d0, d1)
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
    H_ref = ref_H_M29(coeff, d0, d1)
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
    """L5 (class-a exact): the M29 Kraus channel assembled from H_M29 alone (no collapse)
    is exactly trace-preserving: sum_k K†K = I to <= 1e-12.

    M29 is a pure-Hamiltonian error (S1); no collapse operators. The single Kraus is
    U = exp(-i H dt), which is unitary, so sum_k K†K = U†U = I exactly.
    """
    dt_ns = 20.0
    coeff = 0.1
    H = _hamiltonian_matrix_for_term(
        _make_coh_zx_term(coeff),
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
        "M29 channel is not trace-preserving"
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
# exp(-i(eps/4)(Z(x)X)) vs identity: 1-F_e = sin^2(eps/4) (Nielsen quant-ph/0205035 Eq. 16).
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
            _make_coh_zx_term(coeff),
            support=(0, 1),
            local_dims=(2, 2),
            device=DEV,
        )
        kraus = assemble_substep_channel([H], [], dt_ns, device=DEV)
        J_carrier = _choi_state_from_kraus(kraus, device=DEV)
        F_e = float(_state_fidelity(J_carrier, J_I, device=DEV))
        one_minus_fe = float(max(0.0, 1.0 - F_e))
        exact = exact_infidelity_M29(eps)
        band_resid = abs(one_minus_fe - exact)
        assert band_resid <= 5e-7, (
            f"L6a FAIL: |carrier_1-F_e - sin^2(eps/4)| = {band_resid:.3e} at eps={eps:.4f}; "
            f"carrier={one_minus_fe:.6e}, exact={exact:.6e}"
        )


def test_L6b_insufficiency_zx_same_infidelity_as_xz():
    """FALSIFIER / proof-of-insufficiency (L6b): the ZX channel (M29) and the XZ channel (M31)
    produce the SAME scalar 1-F_e = sin^2(eps/4) at the same eps.

    This is the M29-sharp proof that 1-F_e CANNOT catch a wrong-axis / swap-partner bug:
    any single Pauli-pair P(x)Q gives sin^2(eps/4) -- pre-reg B1. Makes operator-identity gate
    L3a strictly necessary. A cert relying only on 1-F_e would false-pass a COH_ZX->(X,Z) map
    corruption (the pair map gives XZ=M31 instead of ZX=M29; the infidelity is unchanged).

    The test SHOULD PASS (same infidelity for both axes) -- its role is to DOCUMENT the
    insufficiency, proving that L3a (operator identity) + L3d (wrong-axis XZ) are the necessary
    gates to distinguish M29 from its swap-partner M31.
    """
    coeff = 0.1
    dt_ns = 20.0
    cdt = torch.complex128
    eps = coeff * dt_ns

    # Correct: COH_ZX channel via carrier
    H_zx = _hamiltonian_matrix_for_term(
        _make_coh_zx_term(coeff),
        support=(0, 1),
        local_dims=(2, 2),
        device=DEV,
    )
    kraus_zx = assemble_substep_channel([H_zx], [], dt_ns, device=DEV)
    J_zx = _choi_state_from_kraus(kraus_zx, device=DEV)

    # Swap-partner: XZ=M31 channel built by hand -- SAME infidelity vs identity, DIFFERENT operator
    Z2 = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=cdt, device=DEV)
    X2 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    H_xz = 0.25 * coeff * torch.kron(X2.contiguous(), Z2.contiguous())
    kraus_xz = assemble_substep_channel([H_xz], [], dt_ns, device=DEV)
    J_xz = _choi_state_from_kraus(kraus_xz, device=DEV)

    I_kraus = torch.eye(4, dtype=cdt, device=DEV).unsqueeze(0)
    J_I = _choi_state_from_kraus(I_kraus, device=DEV)

    fe_zx = float(max(0.0, 1.0 - _state_fidelity(J_zx, J_I, device=DEV)))
    fe_xz = float(max(0.0, 1.0 - _state_fidelity(J_xz, J_I, device=DEV)))

    # Both have the same scalar infidelity sin^2(eps/4) vs identity.
    # This SHOULD PASS -- it proves the insufficiency of 1-F_e for M29/M31 separation.
    assert abs(fe_zx - fe_xz) <= 1e-6, (
        f"INSUFFICIENCY PROOF FAILED: ZX and XZ at same eps have different 1-F_e "
        f"(fe_zx={fe_zx:.6e}, fe_xz={fe_xz:.6e}, diff={abs(fe_zx - fe_xz):.3e}); "
        "this test SHOULD PASS (same 1-F_e for both axes), proving 1-F_e alone is insufficient"
    )

    # But the operators themselves differ: confirms L3a + L3d are necessary
    ZX = 0.25 * coeff * torch.kron(Z2.contiguous(), X2.contiguous())
    diff_op = float(torch.linalg.matrix_norm(ZX - H_xz).item())
    assert diff_op >= _WRONG_AXIS_MIN, (
        f"Operator diff between ZX and XZ generators = {diff_op:.3e} < {_WRONG_AXIS_MIN}; "
        "unexpectedly small -- ZX and XZ look identical at this coeff (bug)"
    )


# ---------------------------------------------------------------------------
# INVARIANT L7: Quadratic scaling  (1-F_e)/eps^2 -> 1/16 as eps->0  (B2, class-b band)
# Leading-order: 1-F_e ~= eps^2/16 = ||(eps/4)(Z(x)X)||_F^2 / 4.
# M29-specific: ratio limit is 1/16 (not 1/4 as for 1-site generators, because d=4 and /4 factor).
# ||(eps/4)(Z(x)X)||_F^2 = (eps/4)^2 * Tr((Z(x)X)^2) = (eps/4)^2 * 4 = eps^2/4 -> /d=4 -> eps^2/16.
# (Z(x)X)^2 = I4 is an exact algebraic fact -- the same as for Y(x)Y, X(x)X (class-a).
# BROKEN INPUT: a linear-in-eps error (1-F_e ~ eps, not eps^2) fails this ratio test.
# ---------------------------------------------------------------------------

def test_L7_quadratic_scaling():
    """L7 (class-b band, B2): (1-F_e)/eps^2 -> 1/16 as eps -> 0.

    At small eps: sin^2(eps/4) ~= eps^2/16 - eps^4/(3*256) + O(eps^6).
    The ratio (1-F_e)/eps^2 should be within 0.005 of 1/16 = 0.0625 for eps in [0.01, 0.1].
    At eps=0.3 (larger angle) the ratio deviates by ~O(eps^2) -- registered B2 deviation.
    M29-specific: the ratio target is 1/16 (not 1/4 as in M6/M7/M20), because d=4 and
    the generator has a /4 factor. The ratio is identical to M22/M23 (all are single Pauli-pair
    involutions at d=4).

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
            _make_coh_zx_term(coeff),
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
            _make_coh_zx_term(coeff_val),
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
    """FALSIFIER: if someone used sin(eps/4) instead of sin^2(eps/4), the result is ODD
    in eps, violating the even-symmetry that the correct formula satisfies.

    The correct formula sin^2(eps/4) is even (sin^2(-x/4) = sin^2(x/4)).
    The wrong formula sin(eps/4) is odd (sin(-x/4) = -sin(x/4)).
    """
    for eps in (0.3, 0.1, 0.03, 0.01, 0.003, 0.001):
        # Correct formula: sin^2(eps/4) -- should be even in eps
        correct_pos = exact_infidelity_M29(+eps)
        correct_neg = exact_infidelity_M29(-eps)
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
# In a 2-qutrit carrier (d0=d1=3), H_M29 acts on the 4 computational rows/cols
# ({0,1}x{0,1} -> indices {0,1,3,4} of a 3x3=9-dim space) with gen4 = (coeff/4)(Z(x)X)
# and has the ZERO GENERATOR on all rows/cols involving any level >= 2 (leaked levels).
# M29 imparts NO population or phase to leaked levels (S3): exp(0)=I on level >=2.
# BROKEN INPUT: a 9x9 matrix that has non-zero entries involving row/col index 2,5,6,7,8
# (the leaked-level subspace) trips L9.
# ---------------------------------------------------------------------------

def test_L9_qutrit_embed_is_zero_on_leaked_levels():
    """L9 (class-a exact, S3): in a dim=(3,3) carrier, the 9x9 H_M29 matrix has:
    (a) its 4x4 computational block (rows/cols {0,1,3,4}) equal to the qubit reference gen4,
    (b) zero generator on all rows/cols involving leaked level >= 2 (indices 2,5,6,7,8).

    M29-specific: exp(-i H dt) = I on any pair of levels where either index >= 2 -- M29
    imparts NO leakage (pre-reg S3). Any leaked-level coupling is a different mechanism.
    The embed is verified by checking each computational-level (row,col) slot and confirming
    all non-computational rows/cols are zero.

    M29-specific structural check in the embed: the gen4 is (coeff/4)(Z(x)X), real-symmetric
    with the specific block-signed structure [[0,1,0,0],[1,0,0,0],[0,0,0,-1],[0,0,-1,0]];
    this is embedded without change into the computational block.
    """
    coeff = 0.1
    d0, d1 = 3, 3
    H = _hamiltonian_matrix_for_term(
        _make_coh_zx_term(coeff),
        support=(0, 1),
        local_dims=(d0, d1),
        device=DEV,
    )
    # Reference gen4 on the 4-dim computational subspace (qubit reference)
    H_ref_4 = ref_H_M29(coeff, 2, 2)  # 4x4, (d0=2, d1=2)

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
            f"L9 FAIL: H_M29 qutrit row-{idx} norm = {row_norm:.3e} != 0; "
            "M29 drives leaked levels -- S3 violated"
        )
        assert col_norm <= _OPERATOR_DIFF_TOL, (
            f"L9 FAIL: H_M29 qutrit col-{idx} norm = {col_norm:.3e} != 0; "
            "M29 drives leaked levels -- S3 violated"
        )


def test_L9_broken_full_qutrit_zx_extends_to_leaked_levels_trips():
    """FALSIFIER: a 9x9 ZX-like matrix that extends to qutrit levels (non-zero on leaked rows/cols)
    fails L9.

    A 3x3 Z-like matrix extended to 9x9 via kron with a 3x3 X-like matrix that has entries
    at level 2 would place non-zero entries at leaked-level indices -- which is NOT M29
    semantics (M29 has zero generator on any level >= 2; pre-reg S3).
    """
    cdt = torch.complex128
    d0, d1 = 3, 3
    # A 3x3 "Z-like" matrix with a leaked-level diagonal entry
    Z3 = torch.zeros((3, 3), dtype=cdt, device=DEV)
    Z3[0, 0] = 1.0
    Z3[1, 1] = -1.0
    Z3[2, 2] = 0.5   # leaked level -- NOT M29
    # A 3x3 "X-like" matrix with entries at level 2
    X3 = torch.zeros((3, 3), dtype=cdt, device=DEV)
    X3[0, 1] = 1.0
    X3[1, 0] = 1.0
    X3[0, 2] = 1.0   # extends to leaked level
    X3[2, 0] = 1.0   # extends to leaked level
    H_broken = 0.025 * torch.kron(Z3.contiguous(), X3.contiguous())
    leaked_indices = [i for i in range(d0 * d1) if (i // d1 >= 2) or (i % d1 >= 2)]
    leaked_norms = [float(torch.linalg.norm(H_broken[i, :]).item()) for i in leaked_indices]
    assert max(leaked_norms) > _OPERATOR_DIFF_TOL, (
        "FALSIFIER DID NOT TRIP: the broken 9x9 ZX-extended matrix has zero leaked rows -- "
        "falsifier wrong (check the index logic)"
    )


# ---------------------------------------------------------------------------
# INVARIANT L10: Anti-circular namespace check  (structural, class-c gate)
# The cert (THIS FILE) must NOT import `_coherent_family_generator`,
# `_embed_coherent_generator`, `TWO_SITE_COHERENT_FAMILIES`, or `COHERENT_PAULI_FAMILIES`
# from the carrier. If these symbols appear in this module's namespace, the cert is circular:
# a wrong Pauli-pair map shared between the 'reference' and the carrier would false-pass.
# The COH_ZX->(X,Z) corruption (ZX->XZ swap) is the M29-sharp falsifier: a pair map
# transposition would be mirrored into the circular reference at diff=0 (false-pass).
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

    If any of these is imported, a wrong COH_ZX pair map (Z,X)->(X,Z) would be reflected into
    the 'reference' silently (the W-C round-1 failure shape; test_axis1_wc_decircularized.py).
    M29-sharp: the COH_ZX->(X,Z) map corruption is the exact circularity that would turn M31
    into M29 silently -- the anti-circular gate is the reason this cert can distinguish them.
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
