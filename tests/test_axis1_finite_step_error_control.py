"""Step-5 finite-step error CONTROL test: WITNESS the carrier's measured 1-F_e BELOW
the REGISTERED prediction-band ceiling (not just the convergence shape Step-3 pinned).

Step-3 (``tests/test_axis1_convergence.py``) checked the convergence *ratio* per
microstep doubling (∝1/m² first-order, ∝1/m⁴ Strang). Step-5 registers and witnesses
the *magnitude* bound — an actual computable ceiling the measured infidelity must sit
below — AND asserts that the acceptance policy surfaces ``accepted_as_error_bound:
False`` (a registered band is a prediction band, class b, NOT a production error bound).

REGISTERED BANDS (outputs/axis1_review/fixes/step5/step5_a/prereg.md):
  first_order:  1-F_e(m) <= c  * (gdt/m)^2     c  = 0.19,  m in {1,2,4,8,16,32,64}   [b]
  strang:       1-F_e(m) <= c' * (gdt/m)^4     c' = 10.76, m >= 4 (asymptotic regime) [b]
  s2_residual:  1-F_e(m) <= c''* (gdt_RD/m)^2  c''= 0.02,  production readout grid     [b]
with the per-substep dimensionless small parameter
  gdt    = sqrt(Omega * gamma) * dt          (DR+T1: competing Hamiltonian/dissipator rates)
  gdt_RD = (2 * gamma_readout_phi) * dt      (production readout T2+RD)

The bound FORM (powers 2,4,2; the gdt normalization) is literature-anchored
(Jaschke 1804.09796, FULL-TEXT; reading_notes/jaschke_open_quantum_tensor_networks_1804.09796.md):
second-order Trotter is O(dt^2) global / O(dt^3) local, and the no-jump propagator is
exp(-i H_eff dt), H_eff = H - (i/2) sum_k c_k^dag c_k. The CONSTANTS c,c',c'' are FITTED
from the witnessed Step-3 / cert4 data and are themselves class b (a band, not a theorem)
=> accepted_as_error_bound stays False.

ORACLE (anti-circular): forward.joint_lindbladian.assemble_substep_channel — all H summed
into ONE H_list, one expm(L dt); NEVER the carrier's _hamiltonian_group_gates. A wrong
carrier grouping is CAUGHT, not mirrored (Step-3 / cert1 idiom).

A band MISS (measured > ceiling at an in-band m) is a FINDING (the carrier is worse than
its registered finite-step law) — the test FAILS LOUDLY; it does not silently refit the
constant. Changing a registered constant is a new prereg.

GPU-GATED: the oracle stack is hard CUDA-only. Collection fails loudly without CUDA rather
than producing a false green skip (same idiom as tests/test_joint_lindbladian.py and
tests/test_axis1_convergence.py). CUDA-MISSING is NOT a release basis.

Standard metrics (docs/METRICS.md): process (entanglement) infidelity 1-F_e via Choi-state
Uhlmann fidelity (trace-normalised Choi J/D, /d convention). No new metric introduced.

Run: conda run -n aiqec python -m pytest -q outputs/axis1_review/fixes/step5/step5_a/test_candidate.py
"""
from __future__ import annotations

import math
import pytest
import torch

from qec_twin.forward.joint_lindbladian import (
    assemble_substep_channel,
    _choi_state_from_kraus,
    _state_fidelity,
)
from qec_twin.simulator.axis1_mcwf_mps_execution import (
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
        "FINITE-STEP ERROR-CONTROL band tests are GPU-gated; "
        "CUDA-MISSING is NOT A RELEASE BASIS — run on the CUDA workstation.",
        pytrace=False,
    )

DEV = "cuda"
CDT = torch.complex128

# --------------------------------------------------------------------------- #
# Physical scales (DR+T1 substep — identical to tests/test_axis1_convergence)  #
# --------------------------------------------------------------------------- #
_DT_NS = 30.0
_OMEGA_PI = math.pi / _DT_NS             # area-preserving pi-pulse drive (rad/ns)
_GAMMA_1 = 1.0 / 30_000.0               # T1 rate (ns^-1)
_ZETA = 2.0 * math.pi * 0.37e-3         # ZZ (rad/ns), commutes with T2 (positive control)
_GAMMA_PHI = 1.0 / 30_000.0             # T2 dephasing rate (ns^-1)

# Per-substep dimensionless small parameter: geometric mean of the two competing
# generator rates (Hamiltonian strength Omega_pi, dissipator rate gamma_1) * dt.
# This is the gdt the registered band is expressed in.
_GDT = math.sqrt(_OMEGA_PI * _GAMMA_1) * _DT_NS

_MICROSTEPS = [1, 2, 4, 8, 16, 32, 64]

# --------------------------------------------------------------------------- #
# REGISTERED prediction-band constants (FROZEN by prereg.md; class b).         #
# A miss is a FINDING, never a silent refit.                                   #
# --------------------------------------------------------------------------- #
_C_FIRST_ORDER = 0.19           # [b] 1-F_e <= c  * (gdt/m)^2  (all m)
_C_STRANG = 10.76               # [b] 1-F_e <= c' * (gdt/m)^4  (m >= asymptotic floor)
_STRANG_ASYMPTOTIC_M_MIN = 4    # Strang band domain: m >= 4 (1/m^4 pre-asymptotic below)
_COMMUTING_INFIDELITY_GATE = 1.0e-6   # [a] ZZ+T2 positive control (carried from Step-3)

# Production readout S2 mass-residual band.
_DT_RO = 500.0
_GAMMA_PHI_DEV = 3.0e-5         # gamma_phi /ns
_GAMMA_RD_DEV = 1.0e-3          # gamma_readout_phi /ns (dominant readout dephasing)
_GDT_RD = (2.0 * _GAMMA_RD_DEV) * _DT_RO   # readout-dissipator per-substep small parameter
_C_S2_RESIDUAL = 0.02           # [b] residual <= c'' * (gdt_RD/m)^2
_S2_MICROSTEPS = [1, 8, 64]


# --------------------------------------------------------------------------- #
# Lift helper (single + adjacent two-site) — cert1 / Step-3 idiom.             #
# --------------------------------------------------------------------------- #

def _lift_op(op_small: torch.Tensor, support: tuple[int, ...], local_dims: tuple[int, ...]) -> torch.Tensor:
    n = len(local_dims)
    if len(support) == 1:
        site = support[0]
        result = torch.eye(1, dtype=CDT, device=DEV)
        for i in range(n):
            if i == site:
                result = torch.kron(result, op_small.to(dtype=CDT, device=DEV))
            else:
                result = torch.kron(result, torch.eye(local_dims[i], dtype=CDT, device=DEV))
        return result
    if len(support) == 2:
        assert support[1] == support[0] + 1, "test lifts ADJACENT two-site support only"
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


# --------------------------------------------------------------------------- #
# Carrier Choi (branch-enumerated from the carrier's OWN primitives) and the   #
# INDEPENDENT term-based oracle Choi. Reproduces S1/S2/S3 exactly.             #
# --------------------------------------------------------------------------- #

def _carrier_choi(substep, local_dims, dt, microstep_count, finite_step_order) -> torch.Tensor:
    Dtot = 1
    for d in local_dims:
        Dtot *= d
    dt_micro = float(dt) / int(microstep_count)

    c_terms = []
    for term in substep.get("terms", ()):
        if str(term["kind"]) != "collapse":
            continue
        if abs(float(term.get("coefficient", 0.0))) <= 0.0:
            continue
        support = tuple(int(q) for q in term["support"])
        c_small = _collapse_operator(term, local_dim=local_dims[support[0]], device=DEV)
        c_terms.append((term, support, c_small))

    def _h_step(rho, frac):
        groups = _hamiltonian_group_gates(substep, dt_ns=frac * dt_micro, local_dims=local_dims, device=DEV)
        for g in groups:
            gate = _lift_op(g["gate"], tuple(int(q) for q in g["support"]), local_dims)
            rho = gate @ rho @ gate.conj().transpose(-1, -2)
        return rho

    def _collapse_step(rho):
        if not c_terms:
            return rho
        K0 = torch.eye(Dtot, dtype=CDT, device=DEV)
        for term, support, _c in c_terms:
            k0_small = _nojump_first_order_kraus(term, dt_micro, local_dim=local_dims[support[0]], device=DEV)
            K0 = _lift_op(k0_small, support, local_dims) @ K0
        kraus_set = [K0]
        for _term, support, c_small in c_terms:
            kraus_set.append((dt_micro ** 0.5) * _lift_op(c_small, support, local_dims))
        out = torch.zeros_like(rho)
        for K in kraus_set:
            out = out + K @ rho @ K.conj().transpose(-1, -2)
        return out

    def _one_microstep(rho):
        if finite_step_order == "strang_second_order":
            rho = _h_step(rho, 0.5)
            rho = _collapse_step(rho)
            rho = _h_step(rho, 0.5)
        else:
            rho = _h_step(rho, 1.0)
            rho = _collapse_step(rho)
        return rho

    def _channel_rho(rho):
        for _ in range(int(microstep_count)):
            rho = _one_microstep(rho)
        return rho

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


def _oracle_choi(substep, local_dims, dt) -> torch.Tensor:
    """Independent oracle Choi: all H summed into ONE H_list, one expm(L dt).
    NEVER uses _hamiltonian_group_gates — anti-circular."""
    Dtot = 1
    for d in local_dims:
        Dtot *= d
    H_list_gpu, c_list_gpu = [], []
    for term in substep.get("terms", ()):
        kind = str(term["kind"])
        support = tuple(int(q) for q in term["support"])
        if kind == "hamiltonian":
            h_small = _hamiltonian_matrix_for_term(term, support=support, local_dims=local_dims, device=DEV)
            H_list_gpu.append(_lift_op(h_small, support, local_dims))
        elif kind == "collapse" and abs(float(term.get("coefficient", 0.0))) > 0.0:
            c_small = _collapse_operator(term, local_dim=local_dims[support[0]], device=DEV)
            c_list_gpu.append(_lift_op(c_small, support, local_dims))
    if H_list_gpu:
        H_joint = H_list_gpu[0]
        for Hk in H_list_gpu[1:]:
            H_joint = H_joint + Hk
        H_joint_list = [H_joint]
    else:
        H_joint_list = [torch.zeros((Dtot, Dtot), dtype=CDT, device=DEV)]
    if not H_list_gpu and not c_list_gpu:
        raise ValueError("oracle_choi: substep has no generators")
    kraus = assemble_substep_channel(H_joint_list, c_list_gpu, dt, device=DEV)
    return _choi_state_from_kraus(kraus, device=DEV)


def _choi_infidelity(J_ref, J_carrier) -> float:
    F = _state_fidelity(J_ref, J_carrier, device=DEV)
    return float(max(0.0, 1.0 - F))


# --------------------------------------------------------------------------- #
# Substep fixtures (identical to tests/test_axis1_convergence).                #
# --------------------------------------------------------------------------- #

def _dr_t1_substep():
    substep = {
        "substep_id": "DR_T1_S3",
        "terms": [
            {"kind": "hamiltonian", "support": [0], "operator_family": "CTRL_X", "coefficient": _OMEGA_PI / 2.0},
            {"kind": "collapse", "support": [0], "operator_family": "T1", "coefficient": _GAMMA_1 ** 0.5},
        ],
    }
    return substep, (2,)


def _zz_t2_substep():
    substep = {
        "substep_id": "ZZ_T2_COMMUTING",
        "terms": [
            {"kind": "hamiltonian", "support": [0, 1], "operator_family": "ZZ", "coefficient": _ZETA},
            {"kind": "collapse", "support": [0], "operator_family": "T2", "coefficient": (2.0 * _GAMMA_PHI) ** 0.5},
            {"kind": "collapse", "support": [1], "operator_family": "T2", "coefficient": (2.0 * _GAMMA_PHI) ** 0.5},
        ],
    }
    return substep, (2, 2)


def _readout_t2_rd_substep():
    """Production readout substep: T2 + RD stacked on the SAME qubit, both c^dag c = |1><1|
    (the S2 no-jump-product cross term; cert4 production case)."""
    substep = {
        "substep_id": "READOUT_T2_RD_S2",
        "terms": [
            {"kind": "collapse", "support": [0], "operator_family": "T2", "coefficient": (2.0 * _GAMMA_PHI_DEV) ** 0.5},
            {"kind": "collapse", "support": [0], "operator_family": "RD", "coefficient": (2.0 * _GAMMA_RD_DEV) ** 0.5},
        ],
    }
    return substep, (2,)


# --------------------------------------------------------------------------- #
# Acceptance policy (the carrier ledger surface for THIS band). Mirrors the    #
# prereg's finite_step_error_control block. accepted_as_error_bound is the     #
# load-bearing class-b guard.                                                  #
# --------------------------------------------------------------------------- #

def finite_step_error_control_policy() -> dict:
    """The registered-band acceptance ledger. accepted_as_error_bound is HARD False:
    a registered prediction band (class b) is NEVER a production error bound."""
    return {
        "registered_band": {
            "first_order": {"power": 2, "constant_c": _C_FIRST_ORDER,
                            "small_parameter": "gdt = sqrt(Omega*gamma)*dt",
                            "fixture": "DR+T1 dt=30ns", "epistemic_class": "b"},
            "strang": {"power": 4, "constant_c": _C_STRANG,
                       "asymptotic_m_min": _STRANG_ASYMPTOTIC_M_MIN,
                       "small_parameter": "gdt = sqrt(Omega*gamma)*dt",
                       "fixture": "DR+T1 dt=30ns", "epistemic_class": "b"},
            "s2_residual": {"power": 2, "constant_c": _C_S2_RESIDUAL,
                            "small_parameter": "gdt_RD = (2*gamma_rd)*dt",
                            "fixture": "readout T2+RD dt=500ns", "epistemic_class": "b"},
        },
        "accepted_as_error_bound": False,            # class b => NOT a production error bound
        "comparison_outcome_is_metric": False,
        "bound_form_grounding": "Jaschke 1804.09796 (FULL-TEXT)",
    }


# --------------------------------------------------------------------------- #
# Test: acceptance policy surfaces accepted_as_error_bound: False.             #
# Epistemic class [a] (claim discipline) — a band is not a theorem.            #
# --------------------------------------------------------------------------- #

def test_acceptance_policy_not_an_error_bound():
    """[a claim-discipline] the registered finite-step band must surface
    accepted_as_error_bound=False and comparison_outcome_is_metric=False, and label
    every registered band as epistemic class b. A True here would be theorem-laundering
    a prediction band into a production error bound — forbidden until proven a-class."""
    policy = finite_step_error_control_policy()
    assert policy["accepted_as_error_bound"] is False, (
        "[a] accepted_as_error_bound MUST be False: the registered bound is a prediction "
        "band (class b), NOT a theorem-grade production error bound. Setting it True without "
        "an a-class proof is theorem-laundering (CLAUDE.md provisional-conclusion corollary)."
    )
    assert policy["comparison_outcome_is_metric"] is False, (
        "[a] comparison_outcome_is_metric MUST be False — the band ceiling is a go/no-go gate "
        "on the standard metric 1-F_e, not a new scored quantity."
    )
    for name, band in policy["registered_band"].items():
        assert band["epistemic_class"] == "b", (
            f"[a] registered band '{name}' must be epistemic class b (a falsifiable bet), "
            f"got {band['epistemic_class']!r}."
        )


# --------------------------------------------------------------------------- #
# Test: commuting positive control (carried from Step-3) — class [a].          #
# --------------------------------------------------------------------------- #

def test_commuting_positive_control_infidelity_near_zero():
    """[a] ZZ+T2 (all diagonal): 1-F_e <= 1e-6 at all m. If this fails, the Choi
    reconstruction or oracle wiring is broken — the band results are meaningless."""
    substep, local_dims = _zz_t2_substep()
    J_ref = _oracle_choi(substep, local_dims, _DT_NS)
    failing = {}
    for m in _MICROSTEPS:
        J_c = _carrier_choi(substep, local_dims, _DT_NS, m, "first_order")
        infid = _choi_infidelity(J_ref, J_c)
        if infid > _COMMUTING_INFIDELITY_GATE:
            failing[m] = infid
    assert not failing, (
        f"[a] EXACT FAILURE — commuting ZZ+T2 positive control: 1-F_e must be <= "
        f"{_COMMUTING_INFIDELITY_GATE:.0e} at ALL m; exceeding: {failing}. Stop — "
        f"the band witness rests on a working Choi reconstruction."
    )


# --------------------------------------------------------------------------- #
# Test: first-order measured 1-F_e BELOW the registered c*(gdt/m)^2 band.      #
# Epistemic class [b] — band miss is a FINDING.                                #
# --------------------------------------------------------------------------- #

def test_first_order_below_registered_band():
    """[b] B1: for DR+T1, measured first-order 1-F_e(m) <= c*(gdt/m)^2 (c=0.19) at every
    m in {1,2,4,8,16,32,64}. A measured value ABOVE the ceiling is a FINDING (the carrier
    is worse than its registered first-order law) — fail loudly, do not refit c."""
    substep, local_dims = _dr_t1_substep()
    J_ref = _oracle_choi(substep, local_dims, _DT_NS)

    rows = []
    misses = []
    for m in _MICROSTEPS:
        J_c = _carrier_choi(substep, local_dims, _DT_NS, m, "first_order")
        infid = _choi_infidelity(J_ref, J_c)
        ceiling = _C_FIRST_ORDER * (_GDT / m) ** 2
        rows.append((m, infid, ceiling))
        if infid > ceiling:
            misses.append((m, infid, ceiling))

    # m=1 must be a real, visible finite-step defect (not machine zero), else the S3
    # split is absent and the band check is vacuous.
    infid_m1 = rows[0][1]
    assert infid_m1 > 1.0e-5, (
        f"[b] first-order DR+T1 at m=1: expected a real finite-step defect 1-F_e > 1e-5; "
        f"got {infid_m1:.3e}. If machine-zero, the S3 split is absent — band is vacuous."
    )
    assert not misses, (
        f"[b] FINDING — first-order 1-F_e ABOVE the registered band c*(gdt/m)^2 (c={_C_FIRST_ORDER}, "
        f"gdt={_GDT:.4e}) at: {[(m, f'{v:.3e}', f'<= {b:.3e}?') for m, v, b in misses]}. "
        f"The carrier is worse than its registered first-order law. Report as a band miss; "
        f"do NOT silently refit the constant (that is a new prereg). "
        f"All rows (m, 1-F_e, ceiling): {[(m, f'{v:.3e}', f'{b:.3e}') for m, v, b in rows]}"
    )


# --------------------------------------------------------------------------- #
# Test: Strang measured 1-F_e BELOW c'*(gdt/m)^4 in the asymptotic regime.     #
# Epistemic class [b].                                                          #
# --------------------------------------------------------------------------- #

def test_strang_below_registered_band_asymptotic():
    """[b] B2: for DR+T1, measured Strang 1-F_e(m) <= c'*(gdt/m)^4 (c'=10.76) for m>=4
    (the asymptotic regime; m<4 is pre-asymptotic and excluded by declaration). A miss in
    the asymptotic regime is a FINDING — fail loudly, do not refit c'."""
    substep, local_dims = _dr_t1_substep()
    J_ref = _oracle_choi(substep, local_dims, _DT_NS)

    asym_ms = [m for m in _MICROSTEPS if m >= _STRANG_ASYMPTOTIC_M_MIN]
    rows = []
    misses = []
    for m in asym_ms:
        J_c = _carrier_choi(substep, local_dims, _DT_NS, m, "strang_second_order")
        infid = _choi_infidelity(J_ref, J_c)
        ceiling = _C_STRANG * (_GDT / m) ** 4
        rows.append((m, infid, ceiling))
        # Skip machine-floored points (ratio/ceiling undefined below numerics floor).
        if infid > 1e-13 and infid > ceiling:
            misses.append((m, infid, ceiling))

    assert rows, (
        f"[b] Strang band: no asymptotic m (>= {_STRANG_ASYMPTOTIC_M_MIN}) in the grid."
    )
    assert not misses, (
        f"[b] FINDING — Strang 1-F_e ABOVE the registered asymptotic band c'*(gdt/m)^4 "
        f"(c'={_C_STRANG}, gdt={_GDT:.4e}, m>={_STRANG_ASYMPTOTIC_M_MIN}) at: "
        f"{[(m, f'{v:.3e}', f'<= {b:.3e}?') for m, v, b in misses]}. Report as a band miss; "
        f"do NOT silently refit. All rows: {[(m, f'{v:.3e}', f'{b:.3e}') for m, v, b in rows]}"
    )


# --------------------------------------------------------------------------- #
# Test: S2 no-jump-product mass-residual BELOW c''*(gdt_RD/m)^2.               #
# Epistemic class [b].                                                          #
# --------------------------------------------------------------------------- #

def test_s2_residual_below_registered_band():
    """[b] B3: the production readout substep (T2+RD, both |1><1|) per-microstep no-jump
    mass-residual (measured as channel 1-F_e vs the joint oracle) <= c''*(gdt_RD/m)^2
    (c''=0.02) on the registered m-grid. A miss is a FINDING — fail loudly, do not refit."""
    substep, local_dims = _readout_t2_rd_substep()
    J_ref = _oracle_choi(substep, local_dims, _DT_RO)

    rows = []
    misses = []
    for m in _S2_MICROSTEPS:
        J_c = _carrier_choi(substep, local_dims, _DT_RO, m, "first_order")
        infid = _choi_infidelity(J_ref, J_c)
        ceiling = _C_S2_RESIDUAL * (_GDT_RD / m) ** 2
        rows.append((m, infid, ceiling))
        if infid > ceiling:
            misses.append((m, infid, ceiling))

    # m=1 must be a real, visible S2 bias (stacked |1><1| collapses), else the production
    # readout substep does not trigger S2 and the band is vacuous.
    infid_m1 = rows[0][1]
    assert infid_m1 > 1.0e-4, (
        f"[b] production readout T2+RD at m=1, dt={_DT_RO}ns: expected a real S2 mass-residual "
        f"1-F_e > 1e-4; got {infid_m1:.3e}. If near-zero, the stacked-|1><1| S2 cross term is "
        f"absent — band is vacuous."
    )
    assert not misses, (
        f"[b] FINDING — S2 mass-residual ABOVE the registered band c''*(gdt_RD/m)^2 "
        f"(c''={_C_S2_RESIDUAL}, gdt_RD={_GDT_RD:.4e}) at: "
        f"{[(m, f'{v:.3e}', f'<= {b:.3e}?') for m, v, b in misses]}. Report as a band miss; "
        f"do NOT silently refit. All rows: {[(m, f'{v:.3e}', f'{b:.3e}') for m, v, b in rows]}"
    )


# --------------------------------------------------------------------------- #
# Summary printout (visible with pytest -s).                                   #
# --------------------------------------------------------------------------- #

def test_print_band_witness_summary(capsys):
    """Print measured 1-F_e vs the registered band ceiling for all three bands."""
    substep_dr, ld_dr = _dr_t1_substep()
    substep_ro, ld_ro = _readout_t2_rd_substep()
    J_ref_dr = _oracle_choi(substep_dr, ld_dr, _DT_NS)
    J_ref_ro = _oracle_choi(substep_ro, ld_ro, _DT_RO)

    with capsys.disabled():
        print(f"\n=== Step-5 finite-step error-control band witness (gdt={_GDT:.4e}) ===")
        print(f"accepted_as_error_bound = {finite_step_error_control_policy()['accepted_as_error_bound']} "
              f"(class b prediction band — NOT a production error bound)")

        print(f"\nfirst_order  band: 1-F_e <= {_C_FIRST_ORDER}*(gdt/m)^2")
        print(f"{'m':>4} {'1-F_e':>14} {'ceiling':>14} {'below?':>8}")
        for m in _MICROSTEPS:
            J_c = _carrier_choi(substep_dr, ld_dr, _DT_NS, m, "first_order")
            v = _choi_infidelity(J_ref_dr, J_c)
            b = _C_FIRST_ORDER * (_GDT / m) ** 2
            print(f"{m:>4} {v:>14.3e} {b:>14.3e} {str(v <= b):>8}")

        print(f"\nstrang       band (m>={_STRANG_ASYMPTOTIC_M_MIN}): 1-F_e <= {_C_STRANG}*(gdt/m)^4")
        print(f"{'m':>4} {'1-F_e':>14} {'ceiling':>14} {'below?':>8}")
        for m in _MICROSTEPS:
            J_c = _carrier_choi(substep_dr, ld_dr, _DT_NS, m, "strang_second_order")
            v = _choi_infidelity(J_ref_dr, J_c)
            b = _C_STRANG * (_GDT / m) ** 4
            inband = "skip<4" if m < _STRANG_ASYMPTOTIC_M_MIN else str(v <= b)
            print(f"{m:>4} {v:>14.3e} {b:>14.3e} {inband:>8}")

        print(f"\ns2_residual  band: 1-F_e <= {_C_S2_RESIDUAL}*(gdt_RD/m)^2  gdt_RD={_GDT_RD:.4e}")
        print(f"{'m':>4} {'1-F_e':>14} {'ceiling':>14} {'below?':>8}")
        for m in _S2_MICROSTEPS:
            J_c = _carrier_choi(substep_ro, ld_ro, _DT_RO, m, "first_order")
            v = _choi_infidelity(J_ref_ro, J_c)
            b = _C_S2_RESIDUAL * (_GDT_RD / m) ** 2
            print(f"{m:>4} {v:>14.3e} {b:>14.3e} {str(v <= b):>8}")
