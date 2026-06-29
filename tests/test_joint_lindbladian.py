"""Independent-oracle unit tests for the Axis-1 joint-Lindbladian assembler.

Validates ``src/qec_twin/forward/joint_lindbladian.py`` against INDEPENDENT references
(QuTiP ``liouvillian``/``expm`` AND a hand-written from-scratch scipy column-stacking
Liouvillian) — NEVER the module's own superop/Choi code (anti-circular, the faithfulness
protocol's rule I). Formalizes the adversarial reviewer's checks as the conventional
``tests/`` home (the ``docs/twin_validation/gates/g2_jointL.py`` gate is the integration
harness; this is the unit oracle).

The module is GPU-only (``_require_cuda`` refuses CPU, no fallback — the memory rule), so
collection FAILS without CUDA instead of producing a skip-green release signal. QuTiP/scipy
are independent-oracle dependencies and also fail collection if unavailable.

Run:  conda run -n aiqec python -m pytest -q tests/test_joint_lindbladian.py
"""
from __future__ import annotations

import pytest
import torch

cuda_ok = torch.cuda.is_available()
if not cuda_ok:
    pytest.fail(
        "joint_lindbladian oracle tests are GPU-gated; CUDA-MISSING is NOT A RELEASE BASIS",
        pytrace=False,
    )
try:
    import qutip as qt  # noqa: F401
    import numpy as np
    from scipy.linalg import expm as _scipy_expm
except Exception as exc:  # pragma: no cover - environment guard
    pytest.fail(
        "ORACLE-DEPS-MISSING (NOT A RELEASE BASIS): install qutip + scipy "
        "(pip install -e '.[test]') to run the independent-oracle joint_lindbladian tests; "
        f"import error={type(exc).__name__}: {exc}",
        pytrace=False,
    )

from qec_twin.numerics import NUMERICAL_ZERO  # noqa: E402
from qec_twin.forward.joint_lindbladian import (  # noqa: E402
    assemble_substep_channel,
    composed_substep_channel,
    composed_vs_joint_infidelity,
    composed_vs_joint_choi_distance,
    composed_vs_joint_infidelity_leading,
    liouvillian_superop,
    liouvillian_commutator_norm,
    composed_vs_joint_superop_distance,
    SUPEROP_EXACTZERO_TOL,
    _joint_superop,
)
from qec_twin.forward.cptp_channel import apply_kraus  # noqa: E402

DEVICE = "cuda"
CDT = torch.complex128


# --------------------------------------------------------------------------- #
# D=4 two-qubit-window generators (built independently of the module).         #
# --------------------------------------------------------------------------- #
def _ops_numpy():
    """The D=4 operators as numpy arrays (independent of the module's torch builder)."""
    import numpy as np

    eye = np.eye(2, dtype=complex)
    sx = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
    n = np.array([[0.0, 0.0], [0.0, 1.0]], dtype=complex)   # |1><1|
    sm = np.array([[0.0, 1.0], [0.0, 0.0]], dtype=complex)   # |0><1| = sigma_minus
    return {
        "sx_a": np.kron(sx, eye),
        "n_n": np.kron(n, n),
        "n_a": np.kron(n, eye),
        "sm_a": np.kron(sm, eye),
    }


# physically-motivated scales (rad/ns; 1 us = 1000 ns) — same as the G2 gate.
ZETA = 2.0 * np.pi * 0.37e-3   # ZZ
GAMMA_PHI = 1.0 / 30000.0                           # T2
GAMMA_1 = 1.0 / 30000.0                             # T1


def _np_to_cuda(a):
    return torch.as_tensor(a, dtype=CDT, device=DEVICE)


def _drxzz_t1t2_generators(omega):
    """A NON-commuting, non-unital generator set: H_DR + H_ZZ Hamiltonians, c_T2 + c_T1
    collapses. Returns (H_list_np, c_list_np) as numpy arrays."""
    ops = _ops_numpy()
    H_DR = (omega / 2.0) * ops["sx_a"]
    H_ZZ = ZETA * ops["n_n"]
    c_T2 = np.sqrt(2.0 * GAMMA_PHI) * ops["n_a"]
    c_T1 = np.sqrt(GAMMA_1) * ops["sm_a"]
    return [H_DR, H_ZZ], [c_T2, c_T1]


# --------------------------------------------------------------------------- #
# INDEPENDENT oracles                                                          #
# --------------------------------------------------------------------------- #
def _scipy_liouvillian(H_list_np, c_list_np):
    """From-scratch column-stacking Liouvillian (numpy/scipy ONLY — independent of the module
    AND of qutip). vec(rho)[j*D+i] = rho[i,j]; vec(A rho B) = (B^T (x) A) vec(rho):
        L = -i(I(x)H - H^T(x)I) + sum_k [ conj(c)(x)c - 1/2(I(x)c^dag c + (c^dag c)^T(x)I) ].
    """
    import numpy as np

    H = sum(H_list_np) if H_list_np else np.zeros_like(c_list_np[0])
    D = H.shape[0]
    I = np.eye(D, dtype=complex)
    L = -1j * (np.kron(I, H) - np.kron(H.T, I))
    for c in c_list_np:
        cc = c.conj().T @ c
        L = L + np.kron(c.conj(), c) - 0.5 * np.kron(I, cc) - 0.5 * np.kron(cc.T, I)
    return L


def _qutip_superop(H_list_np, c_list_np, dt):
    """INDEPENDENT QuTiP superoperator S = (liouvillian(H, c_ops) * dt).expm(), returned as a
    dense (D^2, D^2) numpy array in QuTiP's column-stacking 'super' convention."""
    S = (qt.liouvillian(_qutip_H(H_list_np), [qt.Qobj(c) for c in c_list_np]) * float(dt)).expm()
    return S.full()


def _qutip_H(H_list_np):
    """Build the QuTiP Hamiltonian Qobj for the D=4 channel, handling an EMPTY H_list
    (pure-dissipator / T1-only channels): ``sum([])`` is the scalar ``0``, and ``qt.Qobj(0)`` is a
    (1,1) operator whose dims don't match the (16,16) collapse Liouvillian -> ValueError. So an
    empty list maps to a ZERO (4,4) operator. Flat default dims [[4],[4]] are used consistently for
    H and the c_ops (qt.liouvillian only requires H and c_ops to SHARE dims; the 2-qubit tensor
    structure is irrelevant to the Liouvillian, so flat dims are simplest and guaranteed-matched)."""
    import numpy as np

    if not H_list_np:
        return qt.Qobj(np.zeros((4, 4), dtype=complex))
    return qt.Qobj(sum(H_list_np))


def _qutip_apply(H_list_np, c_list_np, dt, rho_np):
    """Propagate a density matrix rho_np by dt through the QuTiP channel (operator_to_vector ->
    superop -> vector_to_operator). Fully independent of the module."""
    S = (qt.liouvillian(_qutip_H(H_list_np), [qt.Qobj(c) for c in c_list_np]) * float(dt)).expm()
    out = qt.vector_to_operator(S * qt.operator_to_vector(qt.Qobj(rho_np)))
    return out.full()


def _rand_rho_numpy(D, *, seed):
    """Deterministic random density matrix (PSD, trace 1) as numpy."""
    import numpy as np

    g = np.random.default_rng(seed)
    A = g.standard_normal((D, D)) + 1j * g.standard_normal((D, D))
    rho = A @ A.conj().T
    return rho / np.trace(rho).real


def _scipy_composed_superop(H_list_np, c_list_np, dt):
    """INDEPENDENT composed superoperator: each generator's OWN expm(L_i dt) applied SEQUENTIALLY
    (canonical order: H_list then c_list; first listed applied first => S = S_last @ ... @ S_1),
    built from scipy expm of the from-scratch Liouvillians. Independent of the module's composition."""
    superops = [_scipy_expm(_scipy_liouvillian([H], []) * dt) for H in H_list_np]
    superops += [_scipy_expm(_scipy_liouvillian([], [c]) * dt) for c in c_list_np]
    S = superops[0]
    for S_next in superops[1:]:
        S = S_next @ S
    return S


def _choi_state_from_superop(S):
    """INDEPENDENT trace-normalised Choi STATE J/Tr(J) from a column-stacked superop S:
    J = sum_{p,q} E(|p><q|) (x) |p><q|, E(|p><q|) = column-major unvec of S @ vec(|p><q|).
    numpy-only — does NOT call the module's _choi_state_from_kraus."""
    import numpy as np

    D = int(round(S.shape[0] ** 0.5))
    J = np.zeros((D * D, D * D), dtype=complex)
    for p in range(D):
        for q in range(D):
            dyad = np.zeros((D, D), dtype=complex)
            dyad[p, q] = 1.0
            Epq = (S @ dyad.reshape(-1, order="F")).reshape(D, D, order="F")
            e = np.zeros((D, D), dtype=complex)
            e[p, q] = 1.0
            J = J + np.kron(Epq, e)
    J = 0.5 * (J + J.conj().T)
    return J / np.trace(J).real


def _uhlmann_fidelity(A, B):
    """INDEPENDENT Uhlmann state fidelity F(A,B) = (Tr sqrt(sqrt(A) B sqrt(A)))^2 (numpy eigh).
    Does NOT call the module's _state_fidelity."""
    import numpy as np

    wa, Va = np.linalg.eigh(0.5 * (A + A.conj().T))
    wa = np.clip(wa.real, 0.0, None)
    sa = (Va * np.sqrt(wa)) @ Va.conj().T
    M = sa @ B @ sa
    M = 0.5 * (M + M.conj().T)
    wm = np.clip(np.linalg.eigvalsh(M).real, 0.0, None)
    return float(np.sum(np.sqrt(wm)) ** 2)


# --------------------------------------------------------------------------- #
# 1. joint superop == independent QuTiP + scipy Liouvillian (vec/sign/dissipator) #
# --------------------------------------------------------------------------- #
def test_joint_superop_matches_qutip_scipy():
    """For a NON-commuting pair (DR + ZZ + T1 + T2 on D=4), the module's JOINT superoperator
    equals BOTH (a) the from-scratch scipy column-stacking Liouvillian expm and (b) QuTiP's
    liouvillian(...).expm() to ~1e-13. Pins the column-stacking vec convention, the -i[H,.]
    commutator sign, and the dissipator form — all against code that is NOT the module's."""
    dt = 25.0
    H_list_np, c_list_np = _drxzz_t1t2_generators(omega=np.pi / dt)

    # module superop (the object under test).
    H_list = [_np_to_cuda(H) for H in H_list_np]
    c_list = [_np_to_cuda(c) for c in c_list_np]
    S_mod = _joint_superop(H_list, c_list, dt, device=DEVICE).cpu().numpy()

    # oracle (a): from-scratch scipy column-stacking Liouvillian, then scipy expm.
    L_scipy = _scipy_liouvillian(H_list_np, c_list_np)
    S_scipy = _scipy_expm(L_scipy * dt)

    # oracle (b): QuTiP liouvillian.expm().
    S_qt = _qutip_superop(H_list_np, c_list_np, dt)

    # also pin the bare Liouvillian (no expm) against scipy, exact to ~1e-14.
    L_mod = liouvillian_superop(H_list, c_list, device=DEVICE).cpu().numpy()
    assert np.max(np.abs(L_mod - L_scipy)) < 1e-12, np.max(np.abs(L_mod - L_scipy))

    assert np.max(np.abs(S_mod - S_scipy)) < 1e-13, np.max(np.abs(S_mod - S_scipy))
    assert np.max(np.abs(S_mod - S_qt)) < 1e-13, np.max(np.abs(S_mod - S_qt))


# --------------------------------------------------------------------------- #
# 2. Choi->Kraus is CPTP + lossless vs the independent QuTiP channel           #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "label,H_list_np_factory,c_keys",
    [
        # non-commuting, non-unital (DR+ZZ Hamiltonians, T1+T2 collapses) — device-realistic.
        ("dr_zz_t1t2", lambda: _drxzz_t1t2_generators(np.pi / 25.0)[0], ["c_T2", "c_T1"]),
        # NON-UNITAL T1-ONLY amplitude damping (P_relax ~ 0.71 over dt; the commuting-pair check
        # never exercises non-unitality — this does).
        ("t1_only_nonunital", lambda: [], ["c_T1_relax"]),
        # NEAR-TOTAL relaxation (gamma*dt = 5, P_relax ~ 0.99) -> heavily exercises the identity-sink
        # completion of the leaked trace-preservation defect.
        ("t1_neartotal_sink", lambda: [], ["c_T1_neartotal"]),
    ],
)
def test_choi_to_kraus_cptp_lossless(label, H_list_np_factory, c_keys):
    """`assemble_substep_channel`'s Kraus (a) are trace-preserving (||sum K^dag K - I|| <= 1e-12)
    and (b) reproduce the INDEPENDENT QuTiP channel on random density matrices to ~1e-13.
    Covers a non-unital T1-only channel and a near-total-relaxation identity-sink case."""
    dt = 25.0
    ops = _ops_numpy()
    H_list_np = H_list_np_factory()
    c_map = {
        "c_T2": np.sqrt(2.0 * GAMMA_PHI) * ops["n_a"],
        "c_T1": np.sqrt(GAMMA_1) * ops["sm_a"],
        "c_T1_relax": np.sqrt(0.05) * ops["sm_a"],       # gamma*dt = 1.25, P_relax ~ 0.71 (non-unital)
        "c_T1_neartotal": np.sqrt(0.2) * ops["sm_a"],    # gamma*dt = 5, P_relax ~ 0.99 (identity-sink)
    }
    c_list_np = [c_map[k] for k in c_keys]

    H_list = [_np_to_cuda(H) for H in H_list_np]
    c_list = [_np_to_cuda(c) for c in c_list_np]
    kraus = assemble_substep_channel(H_list, c_list, dt, device=DEVICE)

    # (a) trace preservation.
    D = kraus.shape[-1]
    eye = torch.eye(D, dtype=CDT, device=DEVICE)
    SKK = torch.einsum("kij,kil->jl", kraus.conj(), kraus)
    tp_resid = float(torch.max(torch.abs(SKK - eye)))
    assert tp_resid <= NUMERICAL_ZERO, f"{label}: ||sum K^dag K - I|| = {tp_resid}"

    # (b) action matches the independent QuTiP channel on random density matrices.
    for seed in range(4):
        rho_np = _rand_rho_numpy(D, seed=seed)
        out_qt = _qutip_apply(H_list_np, c_list_np, dt, rho_np)
        rho_t = torch.as_tensor(rho_np, dtype=CDT, device=DEVICE)
        out_mod = apply_kraus(rho_t, kraus).cpu().numpy()
        err = np.max(np.abs(out_mod - out_qt))
        assert err < 1e-13, f"{label} seed={seed}: channel-action err {err}"


# --------------------------------------------------------------------------- #
# 3. exact-zero commuting pair: BOTH witnesses (structural + channel-level)     #
# --------------------------------------------------------------------------- #
def test_composed_vs_joint_exact_zero_commuting():
    """ZZ x T2 (both diagonal in n) commute => composed == joint. Structural witness
    ||[L_ZZ, L_T2]|| <= 1e-12 (expm-free, tight) AND channel superop distance <=
    SUPEROP_EXACTZERO_TOL (1e-10, the declared torch matrix_exp floor), dt-independent."""
    ops = _ops_numpy()
    H_ZZ = _np_to_cuda(ZETA * ops["n_n"])
    c_T2 = _np_to_cuda(np.sqrt(2.0 * GAMMA_PHI) * ops["n_a"])

    # (A) structural Liouvillian-commutator witness (expm-free).
    comm = liouvillian_commutator_norm({"H": H_ZZ}, {"c": c_T2}, device=DEVICE)
    assert comm <= NUMERICAL_ZERO, f"||[L_ZZ, L_T2]|| = {comm} (should be ~0, commuting)"

    # (B) channel-level superop distance witness (matrix_exp instrument floor), dt-independent.
    for dt in (20.0, 25.0, 30.0):
        d = composed_vs_joint_superop_distance([H_ZZ], [c_T2], dt, device=DEVICE)
        assert d <= SUPEROP_EXACTZERO_TOL, f"dt={dt}: superop dist {d} > {SUPEROP_EXACTZERO_TOL}"


# --------------------------------------------------------------------------- #
# 4. non-commuting pair: both witnesses clearly NONZERO (the control can fail)  #
# --------------------------------------------------------------------------- #
def test_composed_vs_joint_nonzero_noncommuting():
    """DR x ZZ does NOT commute => composed != joint. The structural Liouvillian-commutator is
    clearly > 1e-6 and the channel superop distance > 1e-3 — proving the exact-zero controls
    are NOT vacuous (they can fail when the pair genuinely couples)."""
    dt = 25.0
    ops = _ops_numpy()
    H_DR = _np_to_cuda((np.pi / dt / 2.0) * ops["sx_a"])
    H_ZZ = _np_to_cuda(ZETA * ops["n_n"])

    comm = liouvillian_commutator_norm({"H": H_DR}, {"H": H_ZZ}, device=DEVICE)
    assert comm > 1e-6, f"||[L_DR, L_ZZ]|| = {comm} (should be clearly nonzero)"

    d = composed_vs_joint_superop_distance([H_DR, H_ZZ], [], dt, device=DEVICE)
    assert d > 1e-3, f"DR x ZZ channel superop distance {d} (should be clearly nonzero)"


# --------------------------------------------------------------------------- #
# 5. GPU-only: refuses a CPU device (no fallback)                              #
# --------------------------------------------------------------------------- #
def test_requires_cuda():
    """The module is GPU-only (memory rule); passing a CPU device must raise ValueError, never
    silently fall back to CPU."""
    ops = _ops_numpy()
    H_ZZ = torch.as_tensor(ZETA * ops["n_n"], dtype=CDT, device=DEVICE)
    c_T2 = torch.as_tensor(np.sqrt(2.0 * GAMMA_PHI) * ops["n_a"], dtype=CDT, device=DEVICE)
    with pytest.raises(ValueError):
        liouvillian_superop([H_ZZ], [c_T2], device="cpu")
    with pytest.raises(ValueError):
        assemble_substep_channel([H_ZZ], [c_T2], 25.0, device="cpu")


# --------------------------------------------------------------------------- #
# 6. HEADLINE API: composed_vs_joint_infidelity == independent Choi-Uhlmann 1-F_e #
# --------------------------------------------------------------------------- #
def test_composed_vs_joint_infidelity_matches_independent():
    """The registered metric `composed_vs_joint_infidelity` (1-F_e) equals an INDEPENDENT
    Choi-state Uhlmann fidelity built from scipy/numpy superops (the joint and the composed
    channels' Choi STATES, then Uhlmann F) — NOT the module's _choi_state/_state_fidelity.
    DR x ZZ + T1 + T2 (non-commuting); ~1e-4 relative (the Uhlmann sqrt/eigh round-off)."""
    dt = 25.0
    H_list_np, c_list_np = _drxzz_t1t2_generators(omega=np.pi / dt)
    H_list = [_np_to_cuda(H) for H in H_list_np]
    c_list = [_np_to_cuda(c) for c in c_list_np]

    mod = composed_vs_joint_infidelity(H_list, c_list, dt, device=DEVICE)

    # INDEPENDENT oracle: scipy joint + composed superops -> Choi states -> Uhlmann fidelity.
    S_joint = _scipy_expm(_scipy_liouvillian(H_list_np, c_list_np) * dt)
    S_comp = _scipy_composed_superop(H_list_np, c_list_np, dt)
    J_joint = _choi_state_from_superop(S_joint)
    J_comp = _choi_state_from_superop(S_comp)
    oracle = 1.0 - _uhlmann_fidelity(J_joint, J_comp)

    assert oracle > 1e-4, f"sanity: oracle 1-F_e {oracle} should be clearly nonzero for DRxZZ"
    rel = abs(mod - oracle) / oracle
    assert rel < 2e-3, f"module 1-F_e {mod} vs independent {oracle} (rel {rel})"


# --------------------------------------------------------------------------- #
# 7. HEADLINE API: composed_substep_channel == independent sequential composition #
# --------------------------------------------------------------------------- #
def test_composed_substep_channel_matches_independent():
    """`composed_substep_channel`'s CPTP Kraus reproduce an INDEPENDENT sequential composition
    (each per-generator scipy expm channel applied in canonical order) on random density matrices
    to ~1e-13. Pins the composition ORDER + the per-generator channel build."""
    dt = 25.0
    H_list_np, c_list_np = _drxzz_t1t2_generators(omega=np.pi / dt)
    H_list = [_np_to_cuda(H) for H in H_list_np]
    c_list = [_np_to_cuda(c) for c in c_list_np]

    kraus = composed_substep_channel(H_list, c_list, dt, device=DEVICE)
    D = kraus.shape[-1]
    S_comp = _scipy_composed_superop(H_list_np, c_list_np, dt)  # independent composed superop

    for seed in range(4):
        rho_np = _rand_rho_numpy(D, seed=seed)
        # independent reference: apply the scipy composed superop (column-stacking) to rho.
        out_ref = (S_comp @ rho_np.reshape(-1, order="F")).reshape(D, D, order="F")
        out_mod = apply_kraus(torch.as_tensor(rho_np, dtype=CDT, device=DEVICE), kraus).cpu().numpy()
        err = np.max(np.abs(out_mod - out_ref))
        assert err < 1e-13, f"composed channel action err {err} (seed {seed})"


# --------------------------------------------------------------------------- #
# 8. HEADLINE API: composed_vs_joint_choi_distance exact-zero machine-precision  #
# --------------------------------------------------------------------------- #
def test_composed_vs_joint_choi_distance_exact_zero_companion():
    """`composed_vs_joint_choi_distance` (the exact-zero machine-precision companion) is ~0 for the
    commuting ZZ x T2 pair (the Kraus-roundtrip reconstruction floor, well under 1e-9) and clearly
    NONZERO for the non-commuting DR x ZZ pair (> 1e-3) — so it discriminates correctly."""
    ops = _ops_numpy()
    H_ZZ = _np_to_cuda(ZETA * ops["n_n"])
    c_T2 = _np_to_cuda(np.sqrt(2.0 * GAMMA_PHI) * ops["n_a"])
    H_DR = _np_to_cuda((np.pi / 25.0 / 2.0) * ops["sx_a"])

    for dt in (20.0, 25.0, 30.0):
        d0 = composed_vs_joint_choi_distance([H_ZZ], [c_T2], dt, device=DEVICE)
        assert d0 < 1e-9, f"commuting ZZxT2 Choi distance {d0} at dt={dt} (should be ~0)"

    d_nz = composed_vs_joint_choi_distance([H_DR, H_ZZ], [], 25.0, device=DEVICE)
    assert d_nz > 1e-3, f"non-commuting DRxZZ Choi distance {d_nz} (should be clearly nonzero)"


# --------------------------------------------------------------------------- #
# 9. HEADLINE API: leading-order ||G||^2/d matches the exact 1-F_e at small dt   #
# --------------------------------------------------------------------------- #
def test_composed_vs_joint_infidelity_leading_matches_exact_smalldt():
    """`composed_vs_joint_infidelity_leading` (the analytic ||G||_F^2/d leading-order law, G =
    (i/2)[H_0,H_1]dt^2, the field-standard /d factor) matches the EXACT
    `composed_vs_joint_infidelity` at SMALL dt (where higher-order BCH is negligible), to a few %,
    AND equals an INDEPENDENT numpy computation of ||(i/2)[H_0,H_1]dt^2||_F^2 / d. Fixed-Omega so
    the leading term is clean (Hamiltonian-only pair)."""
    ops = _ops_numpy()
    omega = np.pi / 25.0   # fixed Omega
    H_DR_np = (omega / 2.0) * ops["sx_a"]
    H_ZZ_np = ZETA * ops["n_n"]
    H_DR = _np_to_cuda(H_DR_np)
    H_ZZ = _np_to_cuda(H_ZZ_np)
    D = 4

    for dt in (4.0, 6.0, 8.0):
        leading_mod = composed_vs_joint_infidelity_leading([H_DR, H_ZZ], dt, device=DEVICE)
        exact = composed_vs_joint_infidelity([H_DR, H_ZZ], [], dt, device=DEVICE)

        # INDEPENDENT analytic leading-order: ||(i/2)[H_0,H_1]dt^2||_F^2 / d (the /d factor).
        G = 0.5j * (H_DR_np @ H_ZZ_np - H_ZZ_np @ H_DR_np) * dt ** 2
        oracle_leading = float(np.linalg.norm(G, "fro") ** 2 / D)

        # (a) module leading-order == independent analytic leading-order (machine precision).
        rel_lead = abs(leading_mod - oracle_leading) / oracle_leading
        assert rel_lead < 1e-6, f"dt={dt}: module leading {leading_mod} vs analytic {oracle_leading} (rel {rel_lead})"
        # (b) leading-order ~ exact 1-F_e at small dt (a few %; the /d law, NOT /d^2).
        rel_exact = abs(leading_mod - exact) / exact
        assert rel_exact < 0.10, f"dt={dt}: leading {leading_mod} vs exact 1-F_e {exact} (rel {rel_exact})"
