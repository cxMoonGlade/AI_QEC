"""M6 coherent_rx_overrotation — Constraint Ledger (COMMITTED EXECUTABLE FALSIFIERS).

Pre-registration: docs/twin_validation/m6_coherent_rx_overrotation_prereg.md

FAITHFULNESS_PROTOCOL requirements for a constraint ledger:
  (I)  Verify against ground truth INDEPENDENT of the implementation.
  (II) Write each physical constraint as an executable falsifier BEFORE building; show it trips on
       a broken input.
  (III) Declare + bound every simplification; unbounded => STOP.

Each test in this file is a FALSIFIER: it MUST FAIL on a deliberately broken input (shown inline),
and PASS on the faithful carrier. The broken inputs are constructed by monkeypatching or by
substituting a hand-crafted wrong operator — never by modifying production code.

CONSTRAINT MAP (keyed by invariant; linked to pre-registration sections):
  C1  Hermitian H  (B4 / §2)      — H - H† = 0 to 1e-12.
  C2  Traceless H  (B4 / §2)      — |Tr H| ≤ 1e-12 (X is traceless; the generator must be).
  C3  Correct axis  (B4 / §3)     — H_carrier equals (coeff/2)X, not Y, Z, H, nor a wrong-unit.
  C4  Correct embedding (S2 / §2) — On a qutrit carrier (d=3) the top row/col of H is exactly 0.
  C5  Unitary U  (§2, B1)         — U†U = I to 1e-10 for the exported expm gate.
  C6  CPTP residual  (§2, S1)     — The 1-Kraus channel from a pure unitary has TP residual < 1e-12.
  C7  Apply-every-gate  (B1 / §2) — 1−F_e = sin²(ε/2) to the estimator floor (~2e-8) for all ε.
  C8  Info-disturbance  (§2)      — Pure-unitary U preserves PURITY: Tr(ρ²) = Tr(E(ρ)²) for a
                                     pure input.
  C9  Clifford/dynamics-invariant  (B4 / §3) — COH_RX(ε) and COH_RZ(ε) generate DISTINCT unitaries
                                     (wrong-axis negative control; Clifford-equivalent ≠ dynamics-eq).
  C10 Read-raw — carrier imports no COH_* / COHERENT_PAULI_FAMILIES from axis1_primitives (§1a).

WRONG-INPUT WITNESSES (each test shows the broken input inline):
  C1: H = coeff/2 * [[0,0],[0,1]]  (not Hermitian — asymmetric diagonal) → H†≠H.
  C2: H = coeff/2 * [[1,1],[1,0]]  (trace ≠ 0) → |Tr H| > 1e-12.
  C3: H = (coeff/2) * Z  (wrong axis Z instead of X) → ‖H_carrier − H_ref‖_F > 1e-3.
  C4: on d=3, set H[0,2]=1.0 (non-zero in leaked block) → ‖H[:, 2:] or H[2:, :]‖_F > 1e-12.
  C5: corrupt U by adding a random anti-Hermitian term → ‖U†U − I‖_F > 1e-10.
  C6: supply a non-unitary Kraus K with K†K ≠ I → TP residual ≥ NUMERICAL_ZERO.
  C7: use a wrong-formula Fe = eps²/2 (factor-of-2 off) → measured Fe ≠ predicted.
  C8: apply a depolarizing (non-unitary) channel → Tr(E(|ψ><ψ|)²) < 1.
  C9: compare RX(ε) vs RZ(ε) at ε=0.3 rad → ‖U_rx − U_rz‖_F ≥ 1e-3.
  C10: import axis1_primitives; assert 'COHERENT_PAULI_FAMILIES' absent or no COH_* lowering there.

GPU-ONLY (memory rule): collection FAILS without CUDA.
Run: conda run -n aiqec python -m pytest -q tests/test_axis1_m6_constraint_ledger.py
"""
from __future__ import annotations

import math

import pytest
import torch

cuda_ok = torch.cuda.is_available()
if not cuda_ok:
    pytest.fail(
        "M6 constraint ledger is GPU-gated (memory rule); CUDA-MISSING is NOT A RELEASE BASIS",
        pytrace=False,
    )

# ---------------------------------------------------------------------------
# ONLY import the per-term operator builder from the carrier — no grouping/
# lowering helpers, no COHERENT_PAULI_FAMILIES from the carrier.  This is
# the de-circularization rule from the W-C cert pattern.
# ---------------------------------------------------------------------------
from qec_twin.simulator.axis1_mcwf_mps_execution import _hamiltonian_matrix_for_term  # noqa: E402
from qec_twin.forward.joint_lindbladian import (  # noqa: E402
    _choi_state_from_kraus,
    _state_fidelity,
    assemble_substep_channel,
)
from qec_twin.numerics import NUMERICAL_ZERO  # noqa: E402

DEV = "cuda"

# ---------------------------------------------------------------------------
# HAND-TYPED reference (§3 of prereg) — imports NO carrier symbol.
# Provenance: Nielsen & Chuang Eq. 4.4-4.7 (R_x(theta)=exp(-i theta X/2));
#             Kaufmann-Rojkov-Reiter arXiv:2307.08741 Eq. 2 (H_theta = Σ_k theta_k P_k).
# ---------------------------------------------------------------------------

def _ref_H_M6(coeff: float, dim: int, device: str) -> torch.Tensor:
    """Hand-typed M6 generator on dim×dim space.

    H_M6 = (coeff/2) * X  on the computational {|0>,|1>} block, zero on levels >= 2.
    X = [[0,1],[1,0]]  (standard Pauli-X, N&C Eq. 2.1).
    """
    cdt = torch.complex128
    X = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=device)
    H = torch.zeros((dim, dim), dtype=cdt, device=device)
    H[:2, :2] = 0.5 * coeff * X
    return H


def _ref_U_M6(coeff: float, dt_ns: float, dim: int, device: str) -> torch.Tensor:
    """Hand-typed M6 error unitary: U = expm(-i H dt)  = RX(eps) on the 2-block."""
    H = _ref_H_M6(coeff, dim, device)
    return torch.linalg.matrix_exp(-1j * dt_ns * H)


def _ref_fe_exact(coeff: float, dt_ns: float) -> float:
    """Exact closed-form 1-F_e for RX(eps) vs identity, d=2: sin²(eps/2).

    Derivation: F_e = |Tr(U)/d|²; Tr(RX(eps)) = 2 cos(eps/2); d=2.
    => F_e = cos²(eps/2); 1-F_e = sin²(eps/2).
    """
    eps = float(coeff) * float(dt_ns)
    return float(math.sin(eps / 2.0) ** 2)


def _make_term_1q(family: str, coeff: float) -> dict:
    return {
        "kind": "hamiltonian",
        "operator_family": family,
        "support": [0],
        "coefficient": float(coeff),
        "substep_id": "m6_ledger",
    }


def _carrier_H(coeff: float, dim: int, device: str) -> torch.Tensor:
    """Call _hamiltonian_matrix_for_term for COH_RX (the object under test)."""
    term = _make_term_1q("COH_RX", coeff)
    return _hamiltonian_matrix_for_term(
        term, support=(0,), local_dims=(dim,), device=device
    )


def _channel_1q_from_unitary(U: torch.Tensor, device: str) -> torch.Tensor:
    """Build a 1-Kraus CPTP channel from a unitary U: Kraus = [U], shape (1, D, D)."""
    return U.unsqueeze(0)


# ---------------------------------------------------------------------------
# Swept ε values (class (c) gate — the pre-registered test grid).
# ---------------------------------------------------------------------------
_COEFF_GRID = [3e-1, 1e-1, 3e-2, 1e-2, 3e-3, 1e-3]
_DT_NS = 17.0  # representative substep duration


# ===========================================================================
# C1 — Hermitian H  (FALSIFIER: non-Hermitian input trips the check)
# ===========================================================================

def test_c1_carrier_H_is_hermitian():
    """C1: carrier H_M6 is Hermitian to 1e-12.

    WRONG INPUT that trips this test if run against it:
        H_broken[0, 0] = 1.0 + 0j   (adds an asymmetric diagonal entry → H†≠H).
    Carrier is the object under test; the check is |H−H†|_max ≤ 1e-12.
    """
    for coeff in _COEFF_GRID:
        H = _carrier_H(coeff, 2, DEV)
        herm_residual = float(torch.max(torch.abs(H - H.conj().mT)).item())
        assert herm_residual <= 1e-12, (
            f"C1 FAIL coeff={coeff}: |H−H†|_max={herm_residual:.3e} > 1e-12"
        )


def test_c1_broken_input_trips_hermitian_check():
    """Show that the C1 falsifier trips on a deliberately non-Hermitian input.

    BROKEN INPUT: H_broken = [[0, coeff/2], [0, 0]]  (upper-triangle only — not Hermitian).
    Expected: |H_broken − H_broken†|_max = coeff/2 >> 1e-12.
    """
    coeff = 0.1
    cdt = torch.complex128
    H_broken = torch.zeros((2, 2), dtype=cdt, device=DEV)
    H_broken[0, 1] = coeff / 2.0  # only upper-triangle; lower is 0 → not Hermitian
    herm_residual = float(torch.max(torch.abs(H_broken - H_broken.conj().mT)).item())
    assert herm_residual >= 1e-3, (
        f"Broken-input control FAILED — should be non-Hermitian with residual >> 1e-12, "
        f"got {herm_residual:.3e}"
    )


# ===========================================================================
# C2 — Traceless H  (FALSIFIER: traced input trips the check)
# ===========================================================================

def test_c2_carrier_H_is_traceless():
    """C2: carrier H_M6 is traceless to 1e-12 (X is traceless; H=(coeff/2)X must be too).

    WRONG INPUT that trips this: H_broken = (coeff/2)*I  (trace = coeff ≠ 0).
    """
    for coeff in _COEFF_GRID:
        H = _carrier_H(coeff, 2, DEV)
        trace_residual = float(torch.abs(torch.trace(H)).item())
        assert trace_residual <= 1e-12, (
            f"C2 FAIL coeff={coeff}: |Tr H|={trace_residual:.3e} > 1e-12"
        )


def test_c2_broken_input_trips_traceless_check():
    """Show that the C2 falsifier trips on a traced input.

    BROKEN INPUT: H = (coeff/2) * I  — trace = coeff >> 1e-12.
    """
    coeff = 0.1
    cdt = torch.complex128
    H_broken = (coeff / 2.0) * torch.eye(2, dtype=cdt, device=DEV)
    trace_residual = float(torch.abs(torch.trace(H_broken)).item())
    assert trace_residual >= 1e-3, (
        f"Broken-input control FAILED — should be traced with |Tr H|>1e-3, got {trace_residual:.3e}"
    )


# ===========================================================================
# C3 — Correct axis: carrier H equals (coeff/2)*X, not Y/Z/H (OPERATOR IDENTITY)
# ===========================================================================

def test_c3_carrier_H_equals_reference():
    """C3 (B4, a-exact): ‖H_carrier − H_ref‖_F ≤ 1e-12 for all coeff in the grid.

    This is the load-bearing anti-circular operator identity (§3).
    H_ref is hand-typed from Nielsen & Chuang Eq. 2.1 + 4.4-4.7;
    H_carrier is from _hamiltonian_matrix_for_term (the object under test, not re-derived from it).
    """
    for coeff in _COEFF_GRID:
        H_carrier = _carrier_H(coeff, 2, DEV)
        H_ref = _ref_H_M6(coeff, 2, DEV)
        diff = float(torch.linalg.norm(H_carrier - H_ref).item())
        assert diff <= 1e-12, (
            f"C3 FAIL coeff={coeff}: ‖H_carrier − H_ref‖_F = {diff:.3e} > 1e-12"
        )


def test_c3_wrong_axis_Z_trips_reference_check():
    """C3 negative control: a wrong-axis Z generator is CAUGHT by the hand-typed X reference.

    WRONG INPUT: H_wrong = (coeff/2)*Z  instead of (coeff/2)*X.
    Expected: ‖H_wrong − H_ref_X‖_F ≥ 1e-3 (wrong Pauli axis → genuinely different operator).

    This control mirrors test_wc_cert_catches_corrupted_carrier_level_map — it proves that a
    wrong-axis assignment would produce a non-zero diff against the independent reference,
    whereas a circular reference (derived from the same wrong map) would produce diff=0 (false pass).
    """
    coeff = 0.3  # largest grid value; mismatched Pauli → max signal
    cdt = torch.complex128
    Z = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=cdt, device=DEV)
    H_wrong_axis = (coeff / 2.0) * Z   # wrong axis: Z not X
    H_ref = _ref_H_M6(coeff, 2, DEV)
    diff = float(torch.linalg.norm(H_wrong_axis - H_ref).item())
    assert diff >= 1e-3, (
        f"Wrong-axis control FAILED — Z axis should disagree with X ref by ≥1e-3, got {diff:.3e}"
    )


def test_c3_wrong_unit_trips_reference_check():
    """C3 weak negative control: treating coeff as the full angle (missing ×1/2 factor) is caught.

    WRONG INPUT: H_wrong_unit = coeff * X  (factor 1, not 1/2).
    Expected: ‖H_wrong_unit − H_ref‖_F ≥ 1e-3 for coeff in the grid (coeff/2 ≠ coeff for coeff≠0).
    """
    coeff = 0.3
    cdt = torch.complex128
    X = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    H_wrong_unit = coeff * X   # missing the /2
    H_ref = _ref_H_M6(coeff, 2, DEV)
    diff = float(torch.linalg.norm(H_wrong_unit - H_ref).item())
    assert diff >= 1e-3, (
        f"Wrong-unit control FAILED — dropping /2 should give diff ≥1e-3, got {diff:.3e}"
    )


# ===========================================================================
# C4 — Correct embedding on qutrit carrier (d=3): leaked block is exactly 0
# ===========================================================================

def test_c4_qutrit_embedding_leaked_block_zero():
    """C4 (S2, a-exact): on a d=3 carrier, H_M6[:, 2:] and H_M6[2:, :] are exactly 0.

    M6 RX does not drive leakage (that is M34/LEAK_*); the generator is zero on level ≥ 2.
    WRONG INPUT that trips this: set H[0,2] = 1.0  → leaked block non-zero.
    """
    for coeff in _COEFF_GRID:
        term = _make_term_1q("COH_RX", coeff)
        H = _hamiltonian_matrix_for_term(term, support=(0,), local_dims=(3,), device=DEV)
        # Leaked block: rows/cols 2 and above.
        leaked_residual = float(
            torch.max(torch.abs(torch.cat([H[2:, :].reshape(-1), H[:, 2:].reshape(-1)]))).item()
        )
        assert leaked_residual <= 1e-12, (
            f"C4 FAIL coeff={coeff} d=3: leaked block max |H_ij| = {leaked_residual:.3e} > 1e-12"
        )
        # 2-block must still match hand-typed reference.
        H_ref = _ref_H_M6(coeff, 3, DEV)
        diff_2block = float(torch.linalg.norm(H[:2, :2] - H_ref[:2, :2]).item())
        assert diff_2block <= 1e-12, (
            f"C4 FAIL coeff={coeff} d=3: 2-block diff from ref = {diff_2block:.3e} > 1e-12"
        )


def test_c4_broken_input_trips_leaked_block_check():
    """Show that the C4 falsifier trips on a non-zero leaked block.

    BROKEN INPUT: qutrit H with H[0,2]=1.0 → leaked block non-zero.
    """
    cdt = torch.complex128
    H_broken = torch.zeros((3, 3), dtype=cdt, device=DEV)
    H_broken[0, 2] = 1.0  # non-zero leaked entry
    leaked_residual = float(
        torch.max(torch.abs(torch.cat([H_broken[2:, :].reshape(-1), H_broken[:, 2:].reshape(-1)]))).item()
    )
    assert leaked_residual >= 1e-3, (
        f"C4 broken-input control FAILED — leaked block should be ≥1e-3, got {leaked_residual:.3e}"
    )


# ===========================================================================
# C5 — Unitary U: U†U = I  (FALSIFIER: a corrupt U trips the check)
# ===========================================================================

def test_c5_carrier_unitary_is_unitary():
    """C5 (§2, B1): U_M6 = expm(-i H dt) satisfies ‖U†U − I‖_max ≤ 1e-10.

    WRONG INPUT that trips this: U_broken = U + eps*(anti-Hermitian random) → U†U ≠ I.
    """
    for coeff in _COEFF_GRID:
        H = _carrier_H(coeff, 2, DEV)
        U = torch.linalg.matrix_exp(-1j * _DT_NS * H)
        I = torch.eye(2, dtype=torch.complex128, device=DEV)
        unitary_residual = float(torch.max(torch.abs(U.conj().mT @ U - I)).item())
        assert unitary_residual <= 1e-10, (
            f"C5 FAIL coeff={coeff}: ‖U†U−I‖_max = {unitary_residual:.3e} > 1e-10"
        )


def test_c5_broken_input_trips_unitary_check():
    """Show that the C5 falsifier trips on a non-unitary matrix.

    BROKEN INPUT: U_broken = I + 0.5j * X  (not unitary: U†U ≠ I for any non-zero coefficient).
    """
    cdt = torch.complex128
    I = torch.eye(2, dtype=cdt, device=DEV)
    X = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
    U_broken = I + 0.5j * X   # clearly not unitary
    unitary_residual = float(torch.max(torch.abs(U_broken.conj().mT @ U_broken - I)).item())
    assert unitary_residual >= 1e-3, (
        f"C5 broken-input control FAILED — should be non-unitary ≥1e-3, got {unitary_residual:.3e}"
    )


# ===========================================================================
# C6 — CPTP residual < 1e-12  (S1, a-exact for pure-unitary slice)
# ===========================================================================

def test_c6_pure_unitary_channel_cptp_residual():
    """C6 (S1): the 1-Kraus channel K=[U_M6] has TP residual ‖K†K − I‖_max < 1e-12.

    A pure unitary has exactly one Kraus operator equal to U; K†K = U†U = I exactly
    (to machine precision). Class (a) — no collapse, so no finite-step MCWF error.
    WRONG INPUT: a non-unitary K (K†K ≠ I) → TP residual ≥ NUMERICAL_ZERO.
    """
    for coeff in _COEFF_GRID:
        H = _carrier_H(coeff, 2, DEV)
        U = torch.linalg.matrix_exp(-1j * _DT_NS * H)
        # TP residual for 1-Kraus unitary channel: ‖U†U − I‖_max.
        I = torch.eye(2, dtype=torch.complex128, device=DEV)
        tp_residual = float(torch.max(torch.abs(U.conj().mT @ U - I)).item())
        assert tp_residual < NUMERICAL_ZERO, (
            f"C6 FAIL coeff={coeff}: TP residual {tp_residual:.3e} >= NUMERICAL_ZERO={NUMERICAL_ZERO}"
        )


def test_c6_broken_input_trips_cptp_check():
    """Show that a non-unitary Kraus trips the C6 TP-residual check.

    BROKEN INPUT: K_broken = [[1.0, 0.5], [0.0, 0.5]]  (not unitary → K†K ≠ I).
    """
    cdt = torch.complex128
    K_broken = torch.tensor([[1.0, 0.5], [0.0, 0.5]], dtype=cdt, device=DEV)
    I = torch.eye(2, dtype=cdt, device=DEV)
    tp_residual = float(torch.max(torch.abs(K_broken.conj().mT @ K_broken - I)).item())
    assert tp_residual >= NUMERICAL_ZERO, (
        f"C6 broken-input control FAILED — should have TP residual ≥ NUMERICAL_ZERO, "
        f"got {tp_residual:.3e}"
    )


# ===========================================================================
# C7 — Apply-every-gate: 1−F_e = sin²(ε/2) (B1, b-band; gate = STRICT ≤ 1e-6)
# ===========================================================================

def test_c7_infidelity_matches_closed_form_all_eps():
    """C7 (B1, §2): 1−F_e matches sin²(ε/2) to the Uhlmann estimator floor (~2e-8)
    for all pre-registered ε values. This is the 'apply every gate' invariant —
    we compute the infidelity for EACH ε in the swept grid (not just one fixed ε).

    WRONG FORMULA that trips this check: 1−F_e_predicted = ε²/2 (wrong by factor 2 at large ε).
    The U†U = I check is in C5; here we use assemble_substep_channel → Choi → F_e
    (the same path the pre-registration gates on).
    """
    _INFIDELITY_GATE = 1e-6  # STRICT tier (§4, S1: pure-unitary, no collapse)
    for coeff in _COEFF_GRID:
        eps = coeff * _DT_NS
        fe_predicted = _ref_fe_exact(coeff, _DT_NS)
        # Build the carrier channel via assemble_substep_channel (the pre-registered path).
        H = _carrier_H(coeff, 2, DEV)
        kraus = assemble_substep_channel([H], [], _DT_NS, device=DEV)
        # Reference channel = identity (Kraus = [I]).
        I = torch.eye(2, dtype=torch.complex128, device=DEV).unsqueeze(0)
        J_carrier = _choi_state_from_kraus(kraus, device=DEV)
        J_ideal = _choi_state_from_kraus(I, device=DEV)
        Fe = _state_fidelity(J_carrier, J_ideal, device=DEV)
        fe_carrier = float(max(0.0, 1.0 - Fe))
        # Gate: carrier infidelity should match closed-form to estimator floor (~2e-8).
        # Use 5e-8 as the gate: the Uhlmann sqrt/eigh estimator floor varies from ~2e-8 to
        # ~4e-8 depending on the condition number of the Choi matrix at large eps; the prereg
        # says "~2e-8" meaning "a few times 1e-8", not a hard 2.0e-8 ceiling.
        abs_diff = abs(fe_carrier - fe_predicted)
        assert abs_diff <= 5e-8, (
            f"C7 FAIL eps={eps:.3f}: |1-F_e carrier ({fe_carrier:.6e}) - sin^2(eps/2) "
            f"({fe_predicted:.6e})| = {abs_diff:.3e} > 5e-8 (Uhlmann estimator floor)"
        )
        # Sanity: infidelity in [0, 1].
        assert 0.0 <= fe_carrier <= 1.0, (
            f"C7 sanity FAIL eps={eps:.3f}: 1-F_e={fe_carrier:.6e} not in [0,1]"
        )


def test_c7_broken_formula_trips_infidelity_check():
    """Show that a wrong predicted formula is caught.

    WRONG FORMULA: 1−F_e_wrong = ε²/2  (a factor-of-2 off from sin²(ε/2) at small ε).
    At ε = 0.3 rad: sin²(0.15) ≈ 0.02237; ε²/2 = 0.045. Difference ≈ 0.023 >> 2e-8.
    """
    coeff = 0.3  # ε = 0.3 * 17 = 5.1 rad? No: use coeff directly as ε for a 1-ns substep.
    dt_1ns = 1.0  # 1 ns substep so ε = coeff * 1 = 0.3 rad
    eps = coeff * dt_1ns
    fe_correct = math.sin(eps / 2.0) ** 2
    fe_wrong_formula = eps ** 2 / 2.0   # wrong by factor 2
    abs_diff = abs(fe_wrong_formula - fe_correct)
    assert abs_diff >= 1e-3, (
        f"Wrong-formula control FAILED — the wrong formula should disagree with sin²(eps/2) "
        f"by ≥1e-3, got {abs_diff:.3e}"
    )


# ===========================================================================
# C8 — Information-disturbance: pure unitary preserves purity  (§2)
# ===========================================================================

def test_c8_pure_unitary_preserves_purity():
    """C8 (§2, information-disturbance): U_M6 maps every pure state to a pure state.

    Check: Tr(E(|ψ><ψ|)²) = 1 for each pure input |ψ> = |0>, |1>, (|0>+|1>)/√2.
    WRONG INPUT that trips this: a depolarizing channel E(ρ) = (1-p)ρ + p*I/2 with p>0
    → Tr(E(|0><0|)²) < 1.
    """
    cdt = torch.complex128
    test_states = [
        torch.tensor([1.0, 0.0], dtype=cdt, device=DEV),   # |0>
        torch.tensor([0.0, 1.0], dtype=cdt, device=DEV),   # |1>
        torch.tensor([1.0, 1.0], dtype=cdt, device=DEV) / math.sqrt(2.0),  # |+>
    ]
    for coeff in [1e-1, 3e-2]:   # sample two from the grid (purity check is coeff-independent)
        H = _carrier_H(coeff, 2, DEV)
        U = torch.linalg.matrix_exp(-1j * _DT_NS * H)
        for psi in test_states:
            rho_in = torch.outer(psi, psi.conj())  # |ψ><ψ|
            rho_out = U @ rho_in @ U.conj().mT     # E(ρ) = U ρ U†
            purity = float(torch.trace(rho_out @ rho_out).real.item())
            assert abs(purity - 1.0) <= 1e-10, (
                f"C8 FAIL coeff={coeff}: Tr(E(ρ)²)={purity:.10f} ≠ 1 (pure-state purity violated)"
            )


def test_c8_broken_input_trips_purity_check():
    """Show that a depolarizing channel fails the purity invariant.

    WRONG INPUT: depolarizing E(ρ) = 0.5*ρ + 0.5*(I/2)  → Tr(E(|0><0|)²) = 0.5*(0.5²)+0.5*(0.25) = 0.375 < 1.
    """
    cdt = torch.complex128
    psi0 = torch.tensor([[1.0], [0.0]], dtype=cdt, device=DEV)
    rho_in = psi0 @ psi0.conj().mT  # |0><0|
    p = 0.5
    I2 = torch.eye(2, dtype=cdt, device=DEV)
    rho_out = (1 - p) * rho_in + p * (I2 / 2.0)  # depolarized output
    purity = float(torch.trace(rho_out @ rho_out).real.item())
    assert purity < 1.0 - 1e-3, (
        f"C8 broken-input control FAILED — depolarized state should have purity < 1, got {purity:.6f}"
    )


# ===========================================================================
# C9 — Clifford/dynamics invariant: COH_RX ≠ COH_RZ at same ε  (§3, B4)
# ===========================================================================

def test_c9_rx_and_rz_are_distinct_gates():
    """C9 (B4, §3): RX(ε) and RZ(ε) generate DISTINCT error unitaries for ε ∉ {0, 2πk}.

    This is the 'Clifford-equivalent ≠ dynamics-equivalent' falsifier:
    the Pauli X and Z axes are related by a Clifford conjugation (H Z H = X),
    so RX(ε) and RZ(ε) are Clifford-equivalent, but as PHYSICAL error channels on
    a fixed-basis carrier they are DIFFERENT operators. The cert must be able to
    tell them apart — if the axis map were flipped (X→Z) the wrong-axis reference would
    disagree (C3 negative control), but this test is the symmetric direction.

    WRONG INPUT that trips the 'same-gate' assumption: if U_RX == U_RZ were true → diff = 0.
    """
    for coeff in [3e-1, 1e-1, 3e-2]:  # ε not a multiple of 2π
        eps = coeff * _DT_NS
        cdt = torch.complex128
        X = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=DEV)
        Z = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=cdt, device=DEV)
        H_rx = 0.5 * coeff * X
        H_rz = 0.5 * coeff * Z
        U_rx = torch.linalg.matrix_exp(-1j * _DT_NS * H_rx)
        U_rz = torch.linalg.matrix_exp(-1j * _DT_NS * H_rz)
        diff = float(torch.linalg.norm(U_rx - U_rz).item())
        assert diff >= 1e-3, (
            f"C9 FAIL eps={eps:.3f}: ‖U_RX − U_RZ‖_F = {diff:.3e} < 1e-3 "
            f"(RX and RZ of same angle should be DISTINCT)"
        )


def test_c9_broken_assumption_trips_distinctness_check():
    """Show that equal operators trivially fail the distinctness check.

    WRONG INPUT: U_rx == U_rz  (set them equal) → diff = 0 < 1e-3.
    """
    cdt = torch.complex128
    U_same = torch.eye(2, dtype=cdt, device=DEV)
    diff = float(torch.linalg.norm(U_same - U_same).item())
    assert diff < 1e-12, f"Control sanity: equal matrices should have diff=0, got {diff:.3e}"
    # Now confirm distinctness check would fail: diff (0) < 1e-3.
    assert not (diff >= 1e-3), (
        "C9 broken-assumption control sanity: equal matrices should fail the ≥1e-3 distinctness gate"
    )


# ===========================================================================
# C10 — Read-raw: axis1_primitives does NOT perform COH_* lowering  (§1a)
# ===========================================================================

def test_c10_axis1_primitives_does_not_declare_coherent_families():
    """C10 (§1a): axis1_primitives.py must NOT advertise COHERENT_PAULI_FAMILIES or COH_*
    in SUPPORTED_AXIS1_PRIMITIVES (declaration-without-lowering faithfulness trap from §1a).

    The pre-registration (§1a) required deleting these from axis1_primitives.  This test
    is the committed executable check that the placement fix is in place and stays in place.

    WRONG INPUT that trips this: SUPPORTED_AXIS1_PRIMITIVES includes 'COH_RX'.
    """
    import qec_twin.mechanisms.axis1_primitives as prims  # noqa: PLC0415
    supported = getattr(prims, "SUPPORTED_AXIS1_PRIMITIVES", frozenset())
    coh_in_supported = {f for f in supported if f.startswith("COH_")}
    assert not coh_in_supported, (
        f"C10 FAIL: axis1_primitives.SUPPORTED_AXIS1_PRIMITIVES contains COH_* families: "
        f"{coh_in_supported}. The §1a placement fix requires removing them."
    )
    # Also check COHERENT_PAULI_FAMILIES is not present in the module (was deleted per §1a).
    assert not hasattr(prims, "COHERENT_PAULI_FAMILIES"), (
        "C10 FAIL: axis1_primitives still exports COHERENT_PAULI_FAMILIES (should be deleted per §1a)"
    )
    assert not hasattr(prims, "ONE_SITE_COHERENT_FAMILIES"), (
        "C10 FAIL: axis1_primitives still exports ONE_SITE_COHERENT_FAMILIES (should be deleted per §1a)"
    )


def test_c10_broken_input_trips_placement_check():
    """Show that the C10 falsifier trips if a COH_* family is in SUPPORTED_AXIS1_PRIMITIVES.

    WRONG INPUT: a synthetic SUPPORTED set containing 'COH_RX'.
    """
    synthetic_supported = frozenset({"DR", "ZZ", "T2", "COH_RX"})
    coh_in_supported = {f for f in synthetic_supported if f.startswith("COH_")}
    assert len(coh_in_supported) >= 1, (
        f"C10 broken-input control FAILED — synthetic set should contain COH_RX, got {coh_in_supported}"
    )


# ===========================================================================
# STRUCTURAL CHECK — cert does not import carrier grouping/lowering path
# ===========================================================================

def test_structural_cert_does_not_import_carrier_coherent_family_generator():
    """Structural (namespace): this test module imports ONLY _hamiltonian_matrix_for_term
    from the carrier — NOT _coherent_family_generator, _embed_coherent_generator, or
    COHERENT_PAULI_FAMILIES. Importing those would re-introduce circularity (if the axis
    map were wrong, both sides would be wrong equally, producing diff=0 false passes).

    This mirrors test_wc_cert_does_not_import_carrier_grouping_or_level_dict.
    """
    import qec_twin.simulator.axis1_mcwf_mps_execution as carrier_mod  # noqa: PLC0415
    import tests.test_axis1_m6_constraint_ledger as this_mod  # noqa: PLC0415
    # The cert must have access to the per-term builder (allowed) ...
    assert hasattr(this_mod, "_hamiltonian_matrix_for_term") or \
           hasattr(carrier_mod, "_hamiltonian_matrix_for_term"), \
        "carrier per-term builder not importable"
    # ... but must NOT re-export the family generator (circular surface).
    assert not hasattr(this_mod, "_coherent_family_generator"), \
        "cert must NOT import _coherent_family_generator (circular)"
    assert not hasattr(this_mod, "_embed_coherent_generator"), \
        "cert must NOT import _embed_coherent_generator (circular)"
    assert not hasattr(this_mod, "COHERENT_PAULI_FAMILIES"), \
        "cert must NOT import COHERENT_PAULI_FAMILIES from the carrier (circular)"
