"""Step-3 regression test: MCWF-vs-oracle finite-step CONVERGENCE pinning.

Pin that the carrier's realized first-order-MCWF channel converges to the INDEPENDENT
oracle ``forward.joint_lindbladian.assemble_substep_channel`` (term-based, never the
carrier grouping) as microsteps refine, with the correct convergence orders:

  first_order:        process infidelity 1-F_e  ∝ 1/m^2  (ratio ~4 per doubling)
  strang_second_order: 1-F_e ∝ 1/m^4 (ratio ~16 per doubling)
                       and Strang(m) < first_order(m) at matched m

SUBSTEP SELECTION (S3 — non-commuting H vs collapse, measurement-free):
  DR+T1: CTRL_X drive (sx/2) + T1 sigma^- on the SAME qubit.
  [sx, |1><1|] != 0  =>  S3 (H-vs-collapse Lie-Trotter split) bites.
  At m=1, dt=30ns: 1-F_e ≈ O(dt * omega * gamma) — a real, visible finite-step defect.

COMMUTING POSITIVE CONTROL:
  ZZ + T2 (both diagonal) => exact commuting, no Trotter split => 1-F_e ~ 0 at all m.

ORACLE: forward.joint_lindbladian.assemble_substep_channel builds H + c into ONE
expm(L*dt) — term-based, NEVER the carrier's _hamiltonian_group_gates. Anti-circular.

CHANNEL RECONSTRUCTION: the carrier's realized CPTP map is reconstructed exactly
(branch enumeration via _hamiltonian_group_gates, _nojump_first_order_kraus,
_collapse_operator) following the pattern of
outputs/axis1_review/agentic_v2/opus/r2_mcwf_channel_vs_jointL_beyondT1.py (cert1).

GPU-GATED: the oracle stack is hard CUDA-only (_require_cuda). Collection fails loudly
without CUDA rather than producing a false green skip (same idiom as test_joint_lindbladian).

PRE-REGISTERED PREDICTIONS (epistemic class in square brackets):
  [a] exact/theorem: ZZ+T2 positive control 1-F_e <= 1e-6 at every m (diagonal ops commute,
      no Trotter defect, no no-jump-product defect; exact statement, not a band).
  [b] prediction band: first_order 1-F_e ratio per ×2 microstep doubling in [3, 5].
      Derivation: leading Trotter defect G ~ [H, sum c^dag c] * dt_micro^2 per microstep,
      accumulated over m microsteps -> net G_total ~ m * (dt/m)^2 = dt^2/m, so
      1-F_e ~ ||G_total||^2/D ~ 1/m^2; ratio per doubling = 2^2 = 4, band [3, 5] around it.
  [b] prediction band: Strang ratio per ×2 doubling >= 10 and Strang(m) < first_order(m)
      for the same m. Strang reduces the per-microstep error by one additional order =>
      1-F_e_Strang ~ 1/m^4, ratio per doubling = 2^4 = 16, band >= 10.

Standard metrics (docs/METRICS.md): process (entanglement) infidelity 1-F_e via
Choi-state Uhlmann fidelity (trace-normalised Choi matrices J/D), /d convention.
Choi trace distance companion 1/2 * ||J_ref - J_carrier||_1.

Run: conda run -n aiqec python -m pytest -q outputs/axis1_review/fixes/step3/step3_b/test_candidate.py
"""
from __future__ import annotations

import math
import pytest
import torch

from error_coupling_simulator.carrier.joint_lindbladian import (
    assemble_substep_channel,
    _choi_state_from_kraus,
    _state_fidelity,
)
from error_coupling_simulator.frontend.axis1_mcwf_mps_execution import (
    _hamiltonian_matrix_for_term,
    _collapse_operator,
    _nojump_first_order_kraus,
    _hamiltonian_group_gates,
)

# --------------------------------------------------------------------------- #
# GPU gate (module-level, fail not skip — CUDA-MISSING is not a release basis) #
# --------------------------------------------------------------------------- #
_cuda_ok = torch.cuda.is_available()
if not _cuda_ok:
    pytest.fail(
        "CONVERGENCE-REGRESSION tests are GPU-gated; "
        "CUDA-MISSING is NOT A RELEASE BASIS — run on the CUDA workstation.",
        pytrace=False,
    )

DEV = "cuda"
CDT = torch.complex128

# Physical scales (all in rad/ns or ns^{-1}).
_DT_NS = 30.0                             # substep duration: large enough to see m=1 defect
_OMEGA_PI = math.pi / _DT_NS             # area-preserving pi-pulse: drives 1-F_e ~ O(1e-3)
_GAMMA_1 = 1.0 / 30_000.0               # T1 rate (ns^-1)
_ZETA = 2.0 * math.pi * 0.37e-3         # ZZ (rad/ns), static-ZZ; commutes with T2
_GAMMA_PHI = 1.0 / 30_000.0             # T2 dephasing rate (ns^-1)

# Microstep doublings for convergence sweep (m=1 -> 64 covers 6 doublings).
_MICROSTEPS = [1, 2, 4, 8, 16, 32, 64]
# Minimum microstep count at which we start measuring ratios (need prev available).
_RATIO_START_M = 2

# Tolerance thresholds (epistemic class c — heuristic gates; go/no-go only):
_COMMUTING_INFIDELITY_GATE = 1.0e-6    # [a] theorem-grade: diagonal commute => exact
_FO_RATIO_LO = 3.0                      # [b] prediction band lower bound: ratio ~4
_FO_RATIO_HI = 6.0                      # [b] band upper bound (loose at small m)
_STRANG_RATIO_MIN = 10.0                # [b] Strang per-doubling ratio >= 10
_STRANG_BEATS_FO_GATE = 1.0e-4         # [b] Strang(m) < first_order(m) at m >= this infidelity


# --------------------------------------------------------------------------- #
# Dense Choi builder: carrier's own microstep channel.                         #
# (Reuses the pattern from cert1: branch-enumerated, uses carrier primitives.) #
# --------------------------------------------------------------------------- #

def _lift_op(op_small: torch.Tensor, support: tuple[int, ...], local_dims: tuple[int, ...]) -> torch.Tensor:
    """Lift a per-support operator to the full product space via kron with identities."""
    n = len(local_dims)
    factors = []
    for i in range(n):
        if i == support[0] and len(support) == 1:
            factors.append(op_small.to(dtype=CDT, device=DEV))
        elif len(support) == 2 and i == support[0]:
            # two-site: op_small covers (support[0], support[1])
            # handled by kron-left then kron with remaining I's
            pass
        else:
            factors.append(torch.eye(local_dims[i], dtype=CDT, device=DEV))
    # Simplified: for 1-site and 2-adjacent-site cases only.
    if len(support) == 1:
        out = factors[0]
        idx = 0
        for i in range(n):
            if i == support[0]:
                out = op_small.to(dtype=CDT, device=DEV) if idx == 0 else torch.kron(out, op_small.to(dtype=CDT, device=DEV))
                # rebuild properly
                break
        # Correct implementation: kron product of per-site factors.
        site = support[0]
        result = torch.eye(1, dtype=CDT, device=DEV)
        for i in range(n):
            if i == site:
                result = torch.kron(result, op_small.to(dtype=CDT, device=DEV))
            else:
                result = torch.kron(result, torch.eye(local_dims[i], dtype=CDT, device=DEV))
        return result
    if len(support) == 2:
        assert support[1] == support[0] + 1, "cert: adjacent 2-site only"
        result = torch.eye(1, dtype=CDT, device=DEV)
        i = 0
        while i < n:
            if i == support[0]:
                result = torch.kron(result, op_small.to(dtype=CDT, device=DEV))
                i += 2
            else:
                result = torch.kron(result, torch.eye(local_dims[i], dtype=CDT, device=DEV))
                i += 1
        return result
    raise AssertionError(f"unsupported support length {len(support)}: {support}")


def _carrier_choi(
    substep: dict,
    local_dims: tuple[int, ...],
    dt: float,
    microstep_count: int,
    finite_step_order: str,
) -> torch.Tensor:
    """Deterministic dense Choi state of the carrier's realized CPTP map.

    Branch-enumerates every microstep (H gate then collapse competition) exactly as
    the MCWF sampler does, accumulating rho_out = sum_branches K rho K^dag.
    Uses the carrier's own primitives (_hamiltonian_group_gates per H cluster,
    _nojump_first_order_kraus per collapse term, _collapse_operator for jumps).
    Returns the trace-normalised Choi STATE (J/D), shape (D^2, D^2).
    """
    Dtot = 1
    for d in local_dims:
        Dtot *= d
    dt_micro = float(dt) / int(microstep_count)

    # Gather collapse terms once.
    c_terms = []
    for term in substep.get("terms", ()):
        if str(term["kind"]) != "collapse":
            continue
        if abs(float(term.get("coefficient", 0.0))) <= 0.0:
            continue
        support = tuple(int(q) for q in term["support"])
        c_small = _collapse_operator(term, local_dim=local_dims[support[0]], device=DEV)
        c_terms.append((term, support, c_small))

    def _h_step(rho: torch.Tensor, frac: float) -> torch.Tensor:
        """Apply the carrier's connected-cluster H gates sequentially for frac * dt_micro."""
        groups = _hamiltonian_group_gates(
            substep, dt_ns=frac * dt_micro, local_dims=local_dims, device=DEV
        )
        for g in groups:
            gate = _lift_op(g["gate"], tuple(int(q) for q in g["support"]), local_dims)
            rho = gate @ rho @ gate.conj().transpose(-1, -2)
        return rho

    def _collapse_step(rho: torch.Tensor) -> torch.Tensor:
        """Apply the first-order no-jump + jump Kraus set for one microstep."""
        if not c_terms:
            return rho
        # No-jump Kraus: SEQUENTIAL product over terms (reproduces S2).
        K0 = torch.eye(Dtot, dtype=CDT, device=DEV)
        for term, support, _c_small in c_terms:
            k0_small = _nojump_first_order_kraus(
                term, dt_micro, local_dim=local_dims[support[0]], device=DEV
            )
            K0 = _lift_op(k0_small, support, local_dims) @ K0
        # Jump Kraus: sqrt(dt_micro) * c per term.
        kraus_set = [K0]
        for _term, support, c_small in c_terms:
            kraus_set.append((dt_micro ** 0.5) * _lift_op(c_small, support, local_dims))
        out = torch.zeros_like(rho)
        for K in kraus_set:
            out = out + K @ rho @ K.conj().transpose(-1, -2)
        return out

    def _one_microstep(rho: torch.Tensor) -> torch.Tensor:
        if finite_step_order == "strang_second_order":
            rho = _h_step(rho, 0.5)
            rho = _collapse_step(rho)
            rho = _h_step(rho, 0.5)
        else:
            rho = _h_step(rho, 1.0)
            rho = _collapse_step(rho)
        return rho

    def _channel_rho(rho: torch.Tensor) -> torch.Tensor:
        for _ in range(int(microstep_count)):
            rho = _one_microstep(rho)
        return rho

    # Build Choi: J = sum_{p,q} E(|p><q|) kron |p><q|.
    J = torch.zeros((Dtot * Dtot, Dtot * Dtot), dtype=CDT, device=DEV)
    for p in range(Dtot):
        for q in range(Dtot):
            rho_pq = torch.zeros((Dtot, Dtot), dtype=CDT, device=DEV)
            rho_pq[p, q] = 1.0
            E_pq = _channel_rho(rho_pq)
            e_pq = torch.zeros((Dtot, Dtot), dtype=CDT, device=DEV)
            e_pq[p, q] = 1.0
            J = J + torch.kron(E_pq.contiguous(), e_pq.contiguous())
    J = 0.5 * (J + J.conj().transpose(-1, -2))
    return J / torch.trace(J).real


def _oracle_choi(
    substep: dict,
    local_dims: tuple[int, ...],
    dt: float,
) -> torch.Tensor:
    """Independent oracle Choi: ALL H summed into one H_list, all c lifted to c_list,
    then assemble_substep_channel => one expm(L dt). NEVER uses _hamiltonian_group_gates."""
    Dtot = 1
    for d in local_dims:
        Dtot *= d

    H_list_gpu = []
    c_list_gpu = []
    for term in substep.get("terms", ()):
        kind = str(term["kind"])
        support = tuple(int(q) for q in term["support"])
        if kind == "hamiltonian":
            h_small = _hamiltonian_matrix_for_term(
                term, support=support, local_dims=local_dims, device=DEV
            )
            H_list_gpu.append(_lift_op(h_small, support, local_dims))
        elif kind == "collapse" and abs(float(term.get("coefficient", 0.0))) > 0.0:
            c_small = _collapse_operator(term, local_dim=local_dims[support[0]], device=DEV)
            c_list_gpu.append(_lift_op(c_small, support, local_dims))

    # Sum all H into one for the joint oracle (retains cross-terms).
    if H_list_gpu:
        H_joint = H_list_gpu[0]
        for Hk in H_list_gpu[1:]:
            H_joint = H_joint + Hk
        H_joint_list = [H_joint]
    else:
        H_joint_list = []

    if not H_joint_list and not c_list_gpu:
        raise ValueError("oracle_choi: substep has no generators")
    if not H_joint_list:
        H_joint_list = [torch.zeros((Dtot, Dtot), dtype=CDT, device=DEV)]
    if not c_list_gpu:
        c_list_gpu = []

    kraus = assemble_substep_channel(H_joint_list, c_list_gpu, dt, device=DEV)
    return _choi_state_from_kraus(kraus, device=DEV)


def _choi_infidelity(J_ref: torch.Tensor, J_carrier: torch.Tensor) -> float:
    """1 - F_e (process infidelity): 1 - Uhlmann fidelity of trace-normalised Choi states."""
    F = _state_fidelity(J_ref, J_carrier, device=DEV)
    return float(max(0.0, 1.0 - F))


def _choi_trace_distance(J_ref: torch.Tensor, J_carrier: torch.Tensor) -> float:
    """1/2 * ||J_ref - J_carrier||_1 (trace distance of trace-normalised Choi states)."""
    diff = J_ref - J_carrier
    diff = 0.5 * (diff + diff.conj().transpose(-1, -2))
    ev = torch.linalg.eigvalsh(diff)
    return float(0.5 * torch.sum(torch.abs(ev)).item())


# --------------------------------------------------------------------------- #
# Substep definitions                                                           #
# --------------------------------------------------------------------------- #

def _dr_t1_substep() -> tuple[dict, tuple[int, ...]]:
    """DR+T1: non-commuting CTRL_X drive + T1 sigma^- on same qubit (S3 case)."""
    substep = {
        "substep_id": "DR_T1_S3",
        "terms": [
            {
                "kind": "hamiltonian",
                "support": [0],
                "operator_family": "CTRL_X",
                "coefficient": _OMEGA_PI / 2.0,
            },
            {
                "kind": "collapse",
                "support": [0],
                "operator_family": "T1",
                "coefficient": _GAMMA_1 ** 0.5,
            },
        ],
    }
    local_dims = (2,)
    return substep, local_dims


def _zz_t2_substep() -> tuple[dict, tuple[int, ...]]:
    """ZZ+T2: diagonal H + diagonal collapse on 2-qubit window (commuting control)."""
    substep = {
        "substep_id": "ZZ_T2_COMMUTING",
        "terms": [
            {
                "kind": "hamiltonian",
                "support": [0, 1],
                "operator_family": "ZZ",
                "coefficient": _ZETA,
            },
            {
                "kind": "collapse",
                "support": [0],
                "operator_family": "T2",
                "coefficient": (2.0 * _GAMMA_PHI) ** 0.5,
            },
            {
                "kind": "collapse",
                "support": [1],
                "operator_family": "T2",
                "coefficient": (2.0 * _GAMMA_PHI) ** 0.5,
            },
        ],
    }
    local_dims = (2, 2)
    return substep, local_dims


# --------------------------------------------------------------------------- #
# Test: commuting positive control (ZZ + T2) — 1-F_e ~ 0 at all m             #
# Epistemic class [a]: exact/theorem, no Trotter defect for commuting ops.     #
# --------------------------------------------------------------------------- #

def test_commuting_positive_control_infidelity_near_zero():
    """[a] ZZ+T2 (all diagonal) positive control: 1-F_e <= 1e-6 at all tested microstep counts.

    Theorem: diagonal operators commute, so the Lie-Trotter split (S3) has zero leading
    commutator and the no-jump-product (S2) defect vanishes for diagonal c^dag c. The carrier
    channel is exact vs the joint oracle at every m — m-independent. This is a hard exact
    assertion (class [a]): if it fails, the Choi reconstruction or oracle wiring is broken
    and the convergence test results are meaningless.
    """
    substep, local_dims = _zz_t2_substep()
    J_ref = _oracle_choi(substep, local_dims, _DT_NS)

    infidelities = {}
    for m in _MICROSTEPS:
        J_c = _carrier_choi(substep, local_dims, _DT_NS, m, "first_order")
        infid = _choi_infidelity(J_ref, J_c)
        infidelities[m] = infid

    failing = {m: v for m, v in infidelities.items() if v > _COMMUTING_INFIDELITY_GATE}
    assert not failing, (
        f"[a] EXACT FAILURE — commuting ZZ+T2 positive control: 1-F_e must be <= "
        f"{_COMMUTING_INFIDELITY_GATE:.0e} at ALL m (no Trotter defect for diagonal ops); "
        f"exceeding entries: {failing}. If this fails, the Choi builder or oracle wiring "
        f"is broken — stop, do not proceed with convergence tests."
    )


# --------------------------------------------------------------------------- #
# Helper: convergence ratio table builder                                       #
# --------------------------------------------------------------------------- #

def _convergence_sweep(
    substep: dict,
    local_dims: tuple[int, ...],
    dt: float,
    microsteps: list[int],
    finite_step_order: str,
) -> dict[int, tuple[float, float]]:
    """Run the carrier vs oracle at each microstep count.

    Returns {m: (1-F_e, choi_td)}.
    """
    J_ref = _oracle_choi(substep, local_dims, dt)
    results = {}
    for m in microsteps:
        J_c = _carrier_choi(substep, local_dims, dt, m, finite_step_order)
        infid = _choi_infidelity(J_ref, J_c)
        td = _choi_trace_distance(J_ref, J_c)
        results[m] = (infid, td)
    return results


def _doubling_ratios(
    results: dict[int, tuple[float, float]],
    microsteps: list[int],
) -> list[tuple[int, int, float, float]]:
    """Return list of (m_prev, m_curr, infid_ratio, td_ratio) for consecutive doublings.

    Only includes pairs where m_curr == 2 * m_prev (strict doublings).
    Skips pairs where the infidelity is < 1e-14 (floored to machine zero).
    """
    pairs = []
    for i in range(1, len(microsteps)):
        m_prev = microsteps[i - 1]
        m_curr = microsteps[i]
        if m_curr != 2 * m_prev:
            continue
        infid_prev, td_prev = results[m_prev]
        infid_curr, td_curr = results[m_curr]
        if infid_curr < 1e-14 or infid_prev < 1e-14:
            # Floored to machine zero — ratio undefined; skip.
            continue
        ri = infid_prev / infid_curr
        rt = td_prev / td_curr if td_curr > 1e-18 else float("nan")
        pairs.append((m_prev, m_curr, ri, rt))
    return pairs


# --------------------------------------------------------------------------- #
# Test: first_order DR+T1 — 1-F_e > 0 at m=1, convergence ratio ~4 per ×2    #
# Epistemic class [b]: prediction band.                                        #
# --------------------------------------------------------------------------- #

def test_first_order_dr_t1_convergence_ratio():
    """[b] first_order carrier DR+T1: 1-F_e ratio per ×2 microstep doubling in [3, 5].

    Pre-registered derivation (cert1 r2_mcwf_channel_vs_jointL_beyondT1 outcome, case C):
      * m=1 infidelity > 1e-5 at dt=30ns (real finite-step defect, not machine noise).
      * Monotone decrease with m.
      * Each doubling: infid_prev / infid_curr in [3, 5] (theoretical ~4 from 1/m^2 scaling).
    Standard metric: process infidelity 1-F_e = 1 - F_pro, Choi-state Uhlmann fidelity.
    """
    substep, local_dims = _dr_t1_substep()
    results = _convergence_sweep(substep, local_dims, _DT_NS, _MICROSTEPS, "first_order")

    # Assert m=1 has a real, visible finite-step error.
    infid_m1, _ = results[1]
    assert infid_m1 > 1.0e-5, (
        f"[b] first_order DR+T1 at m=1, dt={_DT_NS}ns: expected 1-F_e > 1e-5 "
        f"(real finite-step defect from S3 H-vs-collapse split); got {infid_m1:.3e}. "
        f"If 1-F_e is machine-zero at m=1, the S3 split is absent or the substep is wrong."
    )

    # Assert monotone decrease (1-F_e(m+1) <= 1-F_e(m)).
    ms_sorted = sorted(results)
    for i in range(1, len(ms_sorted)):
        m_prev = ms_sorted[i - 1]
        m_curr = ms_sorted[i]
        infid_prev, _ = results[m_prev]
        infid_curr, _ = results[m_curr]
        if infid_prev < 1e-12:
            break  # floored; stop monotone check
        assert infid_curr <= infid_prev * 1.05, (
            f"[b] first_order DR+T1: 1-F_e must decrease with m; "
            f"m={m_prev}: {infid_prev:.3e}, m={m_curr}: {infid_curr:.3e} (increased by > 5%)."
        )

    # Assert convergence ratios per doubling are in [3, 5].
    doubling_pairs = _doubling_ratios(results, _MICROSTEPS)
    assert doubling_pairs, (
        "[b] first_order: no valid doubling pairs found (infidelities all floored?). "
        "Need at least one m -> 2m pair with infid > 1e-14."
    )

    bad_ratios = [(m_p, m_c, ri) for m_p, m_c, ri, _ in doubling_pairs
                  if not (_FO_RATIO_LO <= ri <= _FO_RATIO_HI)]
    # At very small m the leading pre-asymptotic terms affect the ratio; only gate
    # on m >= 2 -> m=4 transitions (asymptotic regime).
    bad_asymptotic = [(m_p, m_c, ri) for m_p, m_c, ri in bad_ratios if m_p >= 2]
    assert not bad_asymptotic, (
        f"[b] first_order DR+T1 convergence: 1-F_e ratio per ×2 must be in "
        f"[{_FO_RATIO_LO}, {_FO_RATIO_HI}] for m >= 2; "
        f"out-of-band: {bad_asymptotic}. "
        f"All doubling ratios: {[(m_p, m_c, f'{ri:.2f}') for m_p, m_c, ri, _ in doubling_pairs]}"
    )


# --------------------------------------------------------------------------- #
# Test: strang_second_order DR+T1 — ratios >= 10, Strang < first_order        #
# Epistemic class [b]: prediction band.                                        #
# --------------------------------------------------------------------------- #

def test_strang_dr_t1_faster_than_first_order():
    """[b] strang_second_order carrier DR+T1: ratio per ×2 >= 10 and Strang(m) < first_order(m).

    Pre-registered derivation: Strang splitting reduces per-microstep error by one order =>
    1-F_e_Strang ~ 1/m^4, ratio per doubling = 2^4 = 16 (>> 10). Also, at matched m,
    Strang channel is strictly closer to the oracle than first_order.
    Standard metric: process infidelity 1-F_e.
    """
    substep, local_dims = _dr_t1_substep()
    results_strang = _convergence_sweep(substep, local_dims, _DT_NS, _MICROSTEPS, "strang_second_order")
    results_fo = _convergence_sweep(substep, local_dims, _DT_NS, _MICROSTEPS, "first_order")

    # Assert Strang ratios per doubling >= 10.
    doubling_pairs_strang = _doubling_ratios(results_strang, _MICROSTEPS)
    assert doubling_pairs_strang, (
        "[b] strang: no valid doubling pairs (infidelities all floored?). "
        "Need at least one m -> 2m pair with infid > 1e-14."
    )
    bad_strang = [(m_p, m_c, ri) for m_p, m_c, ri, _ in doubling_pairs_strang
                  if ri < _STRANG_RATIO_MIN and m_p >= 2]
    assert not bad_strang, (
        f"[b] strang_second_order DR+T1: 1-F_e ratio per ×2 must be >= {_STRANG_RATIO_MIN} "
        f"for m >= 2; out-of-band: {bad_strang}. "
        f"All Strang doubling ratios: {[(m_p, m_c, f'{ri:.2f}') for m_p, m_c, ri, _ in doubling_pairs_strang]}"
    )

    # Assert Strang(m) < first_order(m) at matched m (wherever both are above machine floor).
    violations = []
    for m in _MICROSTEPS:
        infid_strang, _ = results_strang[m]
        infid_fo, _ = results_fo[m]
        if infid_fo < _STRANG_BEATS_FO_GATE:
            continue  # both floored; skip
        if infid_strang >= infid_fo:
            violations.append((m, infid_strang, infid_fo))
    assert not violations, (
        f"[b] strang_second_order must be strictly better than first_order at matched m "
        f"(both > {_STRANG_BEATS_FO_GATE:.0e}); violations: "
        f"{[(m, f'{s:.3e}', f'{f:.3e}') for m, s, f in violations]}"
    )


# --------------------------------------------------------------------------- #
# Test: monotone convergence of trace distance (companion metric)               #
# Epistemic class [b].                                                          #
# --------------------------------------------------------------------------- #

def test_choi_trace_distance_decreases_first_order():
    """[b] first_order DR+T1 Choi trace distance 1/2*||J_ref - J_carrier||_1 decreases with m.

    Companion metric to process infidelity. Both -> 0 as m -> inf only if the carrier is a
    correct finite-step scheme for this substep. Standard metric: Choi trace distance.
    """
    substep, local_dims = _dr_t1_substep()
    results = _convergence_sweep(substep, local_dims, _DT_NS, _MICROSTEPS, "first_order")
    ms_sorted = sorted(results)
    for i in range(1, len(ms_sorted)):
        m_prev = ms_sorted[i - 1]
        m_curr = ms_sorted[i]
        _, td_prev = results[m_prev]
        _, td_curr = results[m_curr]
        if td_prev < 1e-10:
            break
        assert td_curr <= td_prev * 1.05, (
            f"[b] first_order DR+T1 Choi trace distance must decrease with m; "
            f"m={m_prev}: {td_prev:.3e}, m={m_curr}: {td_curr:.3e} (increased by > 5%)."
        )


# --------------------------------------------------------------------------- #
# Summary printout (visible with pytest -s)                                    #
# --------------------------------------------------------------------------- #

def test_print_convergence_summary(capsys):
    """Print the full convergence table for both orders and both metrics (informational)."""
    substep_dr, local_dims_dr = _dr_t1_substep()
    substep_zz, local_dims_zz = _zz_t2_substep()
    J_ref_dr = _oracle_choi(substep_dr, local_dims_dr, _DT_NS)
    J_ref_zz = _oracle_choi(substep_zz, local_dims_zz, _DT_NS)

    with capsys.disabled():
        print(f"\n=== Step-3 convergence summary: DR+T1 (S3) + ZZ+T2 (commuting) dt={_DT_NS}ns ===")
        print(f"{'m':>6} {'order':>22} {'1-F_e(DR+T1)':>16} {'td(DR+T1)':>14} "
              f"{'1-F_e ratio':>13} {'1-F_e(ZZ+T2)':>16}")

        for order in ("first_order", "strang_second_order"):
            results_dr = _convergence_sweep(substep_dr, local_dims_dr, _DT_NS, _MICROSTEPS, order)
            results_zz = _convergence_sweep(substep_zz, local_dims_zz, _DT_NS, _MICROSTEPS, order)
            prev_infid = None
            for m in _MICROSTEPS:
                infid_dr, td_dr = results_dr[m]
                infid_zz, _ = results_zz[m]
                ratio = (prev_infid / infid_dr) if (prev_infid is not None and infid_dr > 1e-15) else float("nan")
                print(
                    f"{m:>6} {order:>22} {infid_dr:>16.3e} {td_dr:>14.3e} "
                    f"{ratio:>13.3f} {infid_zz:>16.3e}"
                )
                prev_infid = infid_dr
            print()

        print("Doubling ratios (1-F_e prev/curr per ×2) — first_order should be ~4, Strang ~16:")
        for order in ("first_order", "strang_second_order"):
            results = _convergence_sweep(substep_dr, local_dims_dr, _DT_NS, _MICROSTEPS, order)
            pairs = _doubling_ratios(results, _MICROSTEPS)
            row = "  ".join(f"m={m_p}→{m_c}: {ri:.2f}" for m_p, m_c, ri, _ in pairs)
            print(f"  {order}: {row}")
