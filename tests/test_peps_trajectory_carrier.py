from __future__ import annotations

r"""Single-wire two-dimensional PEPS trajectory invariants and corruption falsifiers.

The suite covers bounded d3 codestate comparisons, per-operation state updates,
structural lossless truncation, stabilizer tensor-train rank bounds, uniform-to-
outcome maps, temporal detector folding, and loop-correlation known answers.
Corruption tests demonstrate that each comparison reacts to the corresponding
wrong formula, orientation, conjugation, or ledger image.

Tests that construct a PEPS state require CUDA. Tests needing the local Google d3
circuit skip when that input is absent; no synthetic circuit replaces it. Exact
qutrit density-matrix and dense algebra calculations are used only as independent
test references and are not imported by the PEPS implementation.
"""

import copy
import math
import re

import numpy as np
import pytest
import torch

from _support.fixtures import require_precondition
from error_coupling_simulator.numerics import NUMERICAL_ZERO

# --------------------------------------------------------------------------- #
# Physical parameters and numerical bars                                      #
# --------------------------------------------------------------------------- #
WG_L1_TARGET = 5.0e-3   # p1c physical test point
G_SEEP = 0.09
G_HEAT = 0.0
B_BIAS = 0.9            # evidence point for the TT rank assertions
ARM = "A"               # arm A only; arm C is unsupported by this trajectory
TOL_EXACT = 1e-12       # unit-gate dense-equality bar
TOL_TRACE = 1e-10       # branch-trace and caps-read bar
FALSIFIER_FLOOR = 1e-6  # a corrupted image must differ by more than this
D3_CAPS_FLOOR = 1e-12   # caps-path read floor at d3 (near-exact contraction)

_CUDA = torch.cuda.is_available()
requires_cuda = pytest.mark.skipif(
    not _CUDA, reason="CUDA unavailable; the PEPS engine is GPU-only")

_N9 = 3 ** 9

# Deliberately wrong stabilizer-sampling direction used only as a falsifier.
_WRONG_SAMPLING_DIRECTION = "outcome = 1 iff u < p1"


# =========================================================================== #
# Runtime adapters for the current PEPS public surface                        #
# =========================================================================== #
_PEPS_PKG = "error_coupling_simulator.carrier.peps"


def _peps_namespaces() -> list:
    """Runtime-only import of the package and all its submodules
    (pkgutil walk — no submodule-name guessing).  Resolution order: package
    namespace (re-exports) first, then submodules sorted by name."""
    import importlib
    import pkgutil

    pkg = importlib.import_module(_PEPS_PKG)
    mods = [pkg]
    for info in sorted(pkgutil.iter_modules(pkg.__path__), key=lambda i: i.name):
        mods.append(importlib.import_module(f"{_PEPS_PKG}.{info.name}"))
    return mods


def _resolve(name: str):
    for mod in _peps_namespaces():
        obj = getattr(mod, name, None)
        if obj is not None:
            return obj
    return None


def _resolve_any(names, what: str):
    for nm in names:
        obj = _resolve(nm)
        if obj is not None:
            return obj
    pytest.fail(
        f"carrier/peps exposes none of {tuple(names)} for {what} — fix this adapter "
        f"(update the runtime adapter for the current spelling)")


def _try_calls(calls, what: str):
    """Run candidate zero-arg lambdas until one succeeds; TypeError (signature
    mismatch) advances to the next candidate; anything else propagates (a real
    engine error must never be silently retried into a different signature)."""
    errs = []
    for c in calls:
        try:
            return c()
        except TypeError as e:
            errs.append(str(e))
    pytest.fail(f"no candidate signature matched for {what} — fix this adapter; "
                f"TypeErrors seen: {errs}")


def _build_codestate(sched, m: int):
    """Build a unit-norm single-wire codestate."""
    fn = _resolve_any(("build_codestate_peps",), "the codestate builder")
    return _try_calls(
        [lambda: fn(sched, int(m), device="cuda"),
         lambda: fn(sched, int(m), "cuda"),
         lambda: fn(sched, int(m))],
        "build_codestate_peps")


def _dense_psi(state) -> torch.Tensor:
    """Bounded d3 dense bridge; engine position 0 is the MSB factor."""
    fn = _resolve("dense_psi")
    if fn is not None:
        return torch.as_tensor(fn(state)).reshape(-1)
    meth = getattr(state, "dense_psi", None)
    if callable(meth):
        return torch.as_tensor(meth()).reshape(-1)
    pytest.fail("carrier/peps exposes no dense_psi; fix this adapter")


def _apply_1site(state, U: torch.Tensor, pos: int) -> None:
    """Apply a one-site bond-inert operator."""
    fn = _resolve_any(("apply_site_op",), "the one-site operator application")
    fn(state, int(pos), U)


def _apply_kraus_forced(state, K: torch.Tensor, pos: int) -> None:
    """Apply ``K_k`` as a plain one-site linear operation, leaving psi
    unnormalized, through the same physical one-site operator API used by gates."""
    _apply_1site(state, K, int(pos))


def _pepo_layout(sched):
    """The exact layout import the PEPS carrier reuses from the retained PEPO package."""
    from error_coupling_simulator.carrier.pepo.layout import PepoLayout
    return PepoLayout.from_sched(sched)


def _stab_tt(paulis: dict, outcome: int, b: float, arm: str, layout):
    """Build the unsquared ``sqrt(e)`` single-wire stabilizer tensor train."""
    fn = _resolve_any(("stab_tt_singlewire",), "the single-wire stab TT builder")
    return _try_calls(
        [lambda: fn(paulis, int(outcome), float(b), str(arm), layout, "cuda"),
         lambda: fn(paulis, int(outcome), float(b), str(arm), layout),
         lambda: fn(paulis, int(outcome), float(b), str(arm), device="cuda"),
         lambda: fn(paulis, int(outcome), float(b), str(arm))],
        "stab_tt_singlewire")


def _apply_stab_branch(state, tt) -> None:
    """Apply an unnormalized ``sqrt(E_s) psi`` branch with no
    truncation inside."""
    fn = _resolve("apply_stab_branch")
    if fn is not None:
        _try_calls([lambda: fn(state, tt)], "apply_stab_branch")
        return
    meth = getattr(state, "apply_stab_branch", None)
    if callable(meth):
        meth(tt)
        return
    pytest.fail("carrier/peps exposes no apply_stab_branch; fix this adapter")


def _tt_ranks(stab_tt) -> tuple[int, ...]:
    """Read the internal TT bond ranks (attr-name adapter — the pepo-anchor shape)."""
    for name in ("ranks", "bond_ranks", "bond_dims", "tt_ranks"):
        r = getattr(stab_tt, name, None)
        if r is not None:
            return tuple(int(x) for x in r)
    for name in ("cores", "tensors", "tt_cores"):
        cores = getattr(stab_tt, name, None)
        if cores is not None and len(cores) >= 2:
            # cores are (D_left, phys, D_right)-shaped; internal bonds = trailing dims
            return tuple(int(np.asarray(c.shape)[-1]) for c in list(cores)[:-1])
    pytest.fail(
        "the single-wire StabTT exposes no recognizable rank attribute (tried ranks/"
        "bond_ranks/bond_dims/tt_ranks/cores/tensors/tt_cores) — fix the _tt_ranks adapter")


def _caps_read(state, caps: dict) -> complex:
    """The production double-layer caps read ``<psi| (x)_q M_q |psi>``;
    absent sites get the identity/norm cap; ``caps = {}`` reads <psi|psi>).
    Convention note: readers of this value in the tests below always form the
    RATIO vs the empty-caps read, so an internally-normalizing seam is also
    accepted without result-steering."""
    names = ("expect_site_caps", "caps_expectation", "expect_caps",
             "double_layer_expect", "expectation_caps")
    errs = []
    for nm in names:
        fn = _resolve(nm)
        cands = []
        if fn is not None:
            cands.append(lambda f=fn: f(state, caps))
        meth = getattr(state, nm, None)
        if callable(meth):
            cands.append(lambda mm=meth: mm(caps))
        for c in cands:
            try:
                return complex(c())
            except TypeError as e:
                errs.append(f"{nm}: {e}")
    pytest.fail(f"no production caps-path read found (tried {names}) — fix this "
                f"adapter; errors: {errs}")


def _obs_prob_seam(state, logical: dict, isx: dict, b: float, m: int) -> float:
    """Distribution-level exact-P(obs) seam. Probabilities carry the
    ``/<psi|psi>`` normalization used by ``mps_forward``:
    ``p1 = <F1>/<psi|psi>``. The seam returns normalized-state ``P(obs = 1)``."""
    fn = _resolve_any(("terminal_readout_obs_prob", "terminal_obs_prob",
                       "obs_prob_exact"), "the exact-P(obs) seam")
    return float(_try_calls(
        [lambda: fn(state, logical, isx, float(b), int(m))],
        "terminal_readout_obs_prob"))


def _edge_key(k):
    if isinstance(k, (tuple, list)) and len(k) == 2:
        a, b = int(k[0]), int(k[1])
        return (a, b) if a < b else (b, a)
    mm = re.match(r"^B(\d+)_(\d+)$", str(k))
    if mm:
        a, b = int(mm.group(1)), int(mm.group(2))
        return (a, b) if a < b else (b, a)
    pytest.fail(f"bond_profile key {k!r} is neither an edge tuple nor 'B{{a}}_{{b}}' "
                f"— fix the _edge_key adapter")


def _bond_profile_norm(state) -> dict:
    """Normalize ``bond_profile(state)`` to ``{(p, q): dim}`` with ``p < q``;
    fall back to reading ``B{a}_{b}`` index sizes from the tensor network."""
    raw = None
    fn = _resolve("bond_profile")
    if fn is not None:
        try:
            raw = fn(state)
        except TypeError:
            raw = None
    if raw is None:
        meth = getattr(state, "bond_profile", None)
        if callable(meth):
            raw = meth()
    if raw is not None:
        return {_edge_key(k): int(v) for k, v in dict(raw).items()}
    tn = getattr(state, "tn", state)
    out = {}
    for ix in tn.ind_map:
        mm = re.match(r"^B(\d+)_(\d+)$", str(ix))
        if mm:
            out[(int(mm.group(1)), int(mm.group(2)))] = int(tn.ind_size(ix))
    return out


def _largest_bond(state) -> tuple[str, int]:
    """The largest virtual bond (an ind shared by exactly two tensors)."""
    tn = getattr(state, "tn", state)
    cands = [(ix, int(tn.ind_size(ix)))
             for ix, tids in tn.ind_map.items() if len(tids) == 2]
    require_precondition(bool(cands), "the state has no 2-tensor virtual bond",
                         remedy="grow the state before truncation tests")
    return max(cands, key=lambda c: c[1])


def _ledger(state) -> list:
    led = getattr(state, "ledger", None)
    return led if isinstance(led, list) else []


def _entry_from(result, state) -> dict:
    """Normalize a truncation call's report: the returned dict, else the last
    dict appended to ``state.ledger``."""
    if isinstance(result, dict):
        return result
    led = [e for e in _ledger(state) if isinstance(e, dict)]
    require_precondition(bool(led), "truncation left no ledger entry to inspect",
                         remedy="fix the _entry_from adapter / the ledger seam")
    return led[-1]


def _truncate_dcap(state, bond, d_cap: int) -> dict:
    """The D_cap truncation arm on one named bond — the MODULE's own
    ``truncate_bond_dcap`` production seam is the PRIMARY candidate (so the
    ledger-image falsifier checks the PEPS ``_policy_cut`` summary, not the
    shared PEPO implementation); the PEPO
    ``ntu_truncate`` spelling is only the last-resort fallback."""
    errs = []
    for nm, calls in (
        ("truncate_bond_dcap", (
            lambda f: f(state, bond, int(d_cap)),)),
        ("truncate_bond_policy", (
            lambda f: f(state, bond, int(d_cap)),
            lambda f: f(state, bond, d_cap=int(d_cap)),
            lambda f: f(state, bond, D_cap=int(d_cap)))),
        ("ntu_truncate", (
            lambda f: f(state, bond, int(d_cap)),)),
    ):
        fn = _resolve(nm)
        if fn is None:
            continue
        for c in calls:
            try:
                return _entry_from(c(fn), state)
            except TypeError as e:
                errs.append(f"{nm}: {e}")
    pytest.fail(f"no D_cap truncation spelling matched — fix this adapter; {errs}")


def _truncate_lossless(state, bond) -> dict:
    """Structural lossless policy: no cut below the exact local rank (the
    sigma > 1e-12*sigma_1 count — the pinned zero-drop convention).  Dedicated
    spellings first; fallback: the D_cap arm at the bond's current dimension
    (kept rank = min(dim, exact local rank) = the exact local rank — structurally
    the same policy)."""
    errs = []
    for nm, calls in (
        ("truncate_bond_lossless", (lambda f: f(state, bond),)),
        ("lossless_truncate", (lambda f: f(state, bond),)),
        ("truncate_bond_policy", (
            lambda f: f(state, bond, policy="lossless"),
            lambda f: f(state, bond, lossless=True))),
    ):
        fn = _resolve(nm)
        if fn is None:
            continue
        for c in calls:
            try:
                return _entry_from(c(fn), state)
            except TypeError as e:
                errs.append(f"{nm}: {e}")
    tn = getattr(state, "tn", state)
    return _truncate_dcap(state, bond, int(tn.ind_size(bond)))


def _truncate_dynamic_forced(state, bond, eps_spike: float, w_max: int):
    """The dynamic-epsilon policy with the precut window forced to bind through
    the window knob. Returns
    ``(entry_or_None, raised_or_None)`` — an orderly-stop raise is a legitimate
    outcome and is handed back for the flag assertion."""
    errs = []
    for nm in ("truncate_bond_policy", "dynamic_truncate", "truncate_bond_dynamic"):
        fn = _resolve(nm)
        if fn is None:
            continue
        for eps_kw in ("eps_spike", "eps", "epsilon"):
            for w_kw in ("w_max", "W_max", "window_max", "window_cap"):
                for extra in ({}, {"policy": "dynamic"}):
                    try:
                        res = fn(state, bond, **{eps_kw: float(eps_spike),
                                                 w_kw: int(w_max)}, **extra)
                        return _entry_from(res, state), None
                    except TypeError as e:
                        errs.append(f"{nm}({eps_kw},{w_kw},{extra}): {e}")
                    except Exception as e:  # noqa: BLE001 — orderly-stop route
                        return None, e
    pytest.fail(f"no dynamic-eps truncation spelling matched (window knob required) "
                f"— fix this adapter; {errs}")


def _has_window_binding(ledger: list) -> bool:
    """True iff the ledger carries a ``window_binding`` flag entry."""
    for e in ledger:
        if isinstance(e, dict) and (
                e.get("kind") == "window_binding"
                or e.get("op") == "window_binding"
                or bool(e.get("window_binding"))):
            return True
    return False


def _map_sbit():
    """Pure decision map ``(u, p0) -> sbit`` with strict ``u < p0``."""
    return _resolve_any(
        ("sbit_from_uniform", "sample_sbit", "sbit_map", "stab_bit_from_uniform",
         "sbit_from_u"),
        "the stabilizer-outcome decision map (expose the pure map "
        "(u, p0) -> sbit so the convention is CPU-testable)")


def _map_terminal_bit():
    """Pure decision map ``(u, p1) -> bit`` with ``bit = 1 iff u < p1``."""
    return _resolve_any(
        ("terminal_bit_from_uniform", "readout_bit_from_uniform",
         "terminal_bit_map", "bit_from_uniform", "terminal_bit_from_u"),
        "the terminal-bit decision map (expose the pure map (u, p1) -> bit)")


def _map_leak_branch():
    """Pure decision map ``(u, [p_k]) -> k``: first k with
    ``u*tot <= cumsum_k``, non-strict ``<=``, fallback ``K-1``."""
    return _resolve_any(
        ("leak_branch_from_uniform", "kraus_branch_from_uniform", "leak_select",
         "select_kraus_branch", "leak_branch_from_u", "leak_tie_break"),
        "the leak tie-break decision map (expose the pure map (u, pk) -> k)")


def _fold_fns():
    """Import the carrier-neutral canonical temporal fold directly."""
    from error_coupling_simulator.carrier.record_fold import det_to_s, s_to_det

    return s_to_det, det_to_s


def _fold_call(fn, rec_flat: np.ndarray, R: int, n_stab: int) -> np.ndarray:
    """Call s_to_det/det_to_s on ONE record; accept flat or (R, n_stab) input."""
    rec_flat = np.asarray(rec_flat, dtype=np.uint8).reshape(-1)
    try:
        out = fn(rec_flat, R, n_stab)
    except (ValueError, TypeError):
        out = fn(rec_flat.reshape(R, n_stab), R, n_stab)
    return np.asarray(out, dtype=np.uint8).reshape(-1)


class _DuckGrid:
    """Minimal d x d grid-geometry duck (the pepo-layout surface subset the eps_l
    instrument may consult) for synthetic known-answer networks.
    Positions p -> (u, v) = (p // d, p % d); edges match the ``B{a}_{b}`` names
    the test's hand-written tensors carry."""

    def __init__(self, d: int):
        self.d = int(d)
        self.n_data = self.d * self.d
        self.grid = {p: (p // self.d, p % self.d) for p in range(self.n_data)}
        self.pos_at = {uv: p for p, uv in self.grid.items()}

    def neighbors(self, pos: int) -> list[int]:
        u, v = self.grid[int(pos)]
        out = [self.pos_at[k] for k in ((u + 1, v), (u - 1, v), (u, v + 1), (u, v - 1))
               if k in self.pos_at]
        return sorted(out)

    def grid_edges(self) -> list[tuple[int, int]]:
        es = set()
        for p in range(self.n_data):
            for q in self.neighbors(p):
                es.add((p, q) if p < q else (q, p))
        return sorted(es)


def _wrap_synthetic_state(tn, d: int):
    """Wrap a hand-built quimb tensor network for the eps_l instrument:
    try the PepsState constructor shapes, else hand back the bare TN with a duck
    layout attached; a bare tensor network is an admissible carrier of the norm
    network for this diagnostic."""
    lay = _DuckGrid(d)
    cls = _resolve("PepsState")
    if cls is not None:
        for call in (lambda: cls(tn=tn, layout=lay, device="cuda", ledger=[]),
                     lambda: cls(tn, lay, "cuda", []),
                     lambda: cls(tn=tn, layout=lay, ledger=[]),
                     lambda: cls(tn, lay)):
            try:
                return call()
            except Exception:  # noqa: BLE001 — constructor validation may reject the duck
                continue
    try:
        tn.layout = lay
    except Exception:  # noqa: BLE001 — a TN subclass may forbid attr injection
        pass
    return tn


def _eps_l_call(obj):
    """Call ``eps_l(state)`` and return its per-loop table."""
    fn = _resolve_any(("eps_l", "eps_l_table", "eps_l_loops", "loop_eps_l"),
                      "the eps_l instrument")
    errs = []
    for target in (obj, getattr(obj, "tn", obj)):
        try:
            return fn(target)
        except TypeError as e:
            errs.append(str(e))
    pytest.fail(f"eps_l accepted neither the wrapped state nor the bare tn — fix "
                f"this adapter; TypeErrors: {errs}")


def _eps_loop_stats(result) -> list[tuple[float, float]]:
    """Normalize the eps_l table to ``[(eps_max, eps_mean)]`` per loop using the
    cut-edge rule: MAX conservative + mean reported)."""
    def from_entry(v):
        if isinstance(v, dict):
            mx = v.get("eps_max", v.get("max", v.get("eps_l")))
            mn = v.get("eps_mean", v.get("mean", mx))
            if mx is not None:
                return (float(mx), float(mn))
            return None
        if isinstance(v, (tuple, list)) and len(v) == 2:
            try:
                return (float(v[0]), float(v[1]))
            except (TypeError, ValueError):
                return None
        try:
            fv = float(v)
            return (fv, fv)
        except (TypeError, ValueError):
            return None

    if isinstance(result, dict) and "per_loop" in result:
        # the module's eps_l returns {per_loop: [{eps_max, eps_mean, ...}], mean,
        # max, n_loops, bp_*}; iterate the per-loop list, not the top-level values.
        entries = [from_entry(v) for v in result["per_loop"]]
    elif isinstance(result, dict):
        entries = [from_entry(v) for v in result.values()]
    elif isinstance(result, (list, tuple)):
        entries = [from_entry(v) for v in result]
    else:
        entries = [from_entry(result)]
    if not entries or any(e is None for e in entries):
        pytest.fail(f"unrecognized eps_l table shape {type(result).__name__}: "
                    f"{result!r} — fix the _eps_loop_stats adapter")
    return entries


# --------------------------------------------------------------------------- #
# Helpers (test-local formulas + memory-lean dense comparisons)                #
# --------------------------------------------------------------------------- #
def _free() -> None:
    if _CUDA:
        torch.cuda.empty_cache()


def _qutrit_mat(name: str, device="cuda") -> torch.Tensor:
    """Test-local single-qutrit operator table from literal formulas using the
    frame-gate convention: computational {0,1} action, |2> inert).  Deliberately
    NOT imported from qutrit_dm or mps_forward: the test drives BOTH engine and
    reference with the same explicit matrix, so no shared gate-table code path can
    hide a convention drift."""
    m = torch.zeros((3, 3), dtype=torch.complex128, device=device)
    nm = str(name).upper()
    if nm == "I":
        return torch.eye(3, dtype=torch.complex128, device=device)
    if nm == "H":
        inv2 = 1.0 / math.sqrt(2.0)
        m[0, 0] = inv2; m[0, 1] = inv2; m[1, 0] = inv2; m[1, 1] = -inv2; m[2, 2] = 1.0
        return m
    if nm == "X":
        m[0, 1] = 1.0; m[1, 0] = 1.0; m[2, 2] = 1.0
        return m
    if nm == "Z":
        m[0, 0] = 1.0; m[1, 1] = -1.0; m[2, 2] = 1.0
        return m
    if nm == "S":
        m[0, 0] = 1.0; m[1, 1] = 1.0j; m[2, 2] = 1.0
        return m
    raise ValueError(f"unsupported test-local qutrit op {name!r}")


def _psi_rho_maxabs(psi: torch.Tensor, rho: torch.Tensor, *, psi_scale: float = 1.0,
                    rho_scale: float = 1.0, block: int = 512) -> float:
    """Chunked max-abs of ``psi_scale * |psi><psi| - rho_scale * rho`` (never a
    full 3^9 x 3^9 temp — the anchor's memory-lean comparison discipline)."""
    psi = psi.reshape(-1)
    assert psi.shape[0] == rho.shape[0] == rho.shape[1], (psi.shape, rho.shape)
    conj_row = psi.conj()[None, :]
    worst = 0.0
    for i0 in range(0, psi.shape[0], block):
        i1 = min(i0 + block, psi.shape[0])
        blk = (psi[i0:i1, None] * conj_row) * psi_scale - rho[i0:i1] * rho_scale
        worst = max(worst, float(blk.abs().max().item()))
        del blk
    return worst


def _pair_maxabs(state, eng) -> float:
    """Unnormalized dense equality of the paired states."""
    return _psi_rho_maxabs(_dense_psi(state), eng.rho)


def _pair_maxabs_normalized(state, eng) -> float:
    """Normalized-image comparison for corruption falsifiers; sensitivity
    must not depend on the prep's absolute norm)."""
    psi = _dense_psi(state)
    n2 = float((psi.conj() * psi).real.sum().item())
    tr = float(torch.diagonal(eng.rho).real.sum().item())
    require_precondition(n2 > 1e-12 and tr > 1e-12,
                         f"degenerate branch (|psi|^2={n2:.3e}, tr={tr:.3e}) — "
                         f"normalized comparison undefined")
    return _psi_rho_maxabs(psi, eng.rho, psi_scale=1.0 / n2, rho_scale=1.0 / tr)


def _site_trits(idx: torch.Tensor, site: int, n: int) -> torch.Tensor:
    """Trit of ``site`` per basis index, with qudit 0 as the most-significant
    factor; recomputed independently here."""
    return (idx // (3 ** (n - 1 - int(site)))) % 3


def _site_rdm(rho: torch.Tensor, site: int, n: int = 9) -> torch.Tensor:
    """One-site reduced density matrix from the dense reference rho (view-based
    diagonals + a small sum — never a 3^18-element temp)."""
    left, right = 3 ** int(site), 3 ** (n - 1 - int(site))
    r6 = rho.reshape(left, 3, right, left, 3, right)
    d1 = r6.diagonal(dim1=0, dim2=3)      # (3, right, 3, right, left)
    d2 = d1.diagonal(dim1=1, dim2=3)      # (3, 3, left, right)
    return d2.sum(dim=(2, 3))             # (3, 3), ket-major


def _leaked_mass_rel(rho: torch.Tensor, sites) -> float:
    """Relative diagonal mass with ANY of ``sites`` in |2> (non-vacuity probe)."""
    n = round(math.log(rho.shape[0]) / math.log(3))
    diag = torch.diagonal(rho).real
    idx = torch.arange(rho.shape[0], device=rho.device)
    any2 = torch.zeros_like(idx, dtype=torch.bool)
    for s in sites:
        any2 |= _site_trits(idx, int(s), n) == 2
    tot = float(diag.sum().item())
    require_precondition(tot > 1e-12, f"vanished trace {tot:.3e} in the leaked-mass "
                                      f"probe")
    return float(diag[any2].sum().item()) / tot


def _obs_prob_dense(rho: torch.Tensor, logical: dict, b: float, m: int, *,
                    swap_b: bool = False) -> float:
    """The observable-law composition, hand-built on the dense reference rho and
    normalized by its trace: H-rotate the X-flagged LOGICAL sites, per-site
    diagonal F1 = |1><1| + b|2><2| / F0 = |0><0| + (1-b)|2><2|, parity over the
    logical support only, XOR m. ``swap_b=True`` builds a deliberately wrong
    coherent double-swap image. Returns ``P(obs = 1)``."""
    n = round(math.log(rho.shape[0]) / math.log(3))
    assert 3 ** n == rho.shape[0]
    h = _qutrit_mat("H", rho.device)

    def _left_mul(work, op, site):
        left, right = 3 ** int(site), 3 ** (n - 1 - int(site))
        return torch.einsum("ab,lbrc->larc", op,
                            work.reshape(left, 3, right, work.shape[0])).reshape(
                                work.shape[0], work.shape[0])

    work = rho
    for s in (s for s, p in logical.items() if str(p).upper() == "X"):
        work = _left_mul(work, h, s)
        work = _left_mul(work.conj().transpose(-1, -2), h, s).conj().transpose(-1, -2)
    diag = torch.diagonal(work).real
    del work
    tr = float(diag.sum().item())
    require_precondition(tr > 1e-12, f"vanished trace {tr:.3e} in the dense obs "
                                     f"composition")
    b1 = (1.0 - float(b)) if swap_b else float(b)
    f1_by_trit = torch.tensor([0.0, 1.0, b1], dtype=torch.float64, device=rho.device)
    idx = torch.arange(rho.shape[0], device=rho.device)
    factor = torch.ones_like(diag)
    for s in logical:
        factor = factor * (1.0 - 2.0 * f1_by_trit[_site_trits(idx, int(s), n)])
    p_odd = float((diag * 0.5 * (1.0 - factor)).sum().item()) / tr
    return p_odd if int(m) == 0 else 1.0 - p_odd


def _isx_map(logical: dict) -> dict:
    """Per-logical-site X flag (the sv_sampler ``log_supp_isx`` convention)."""
    return {int(s): int(str(p).upper() == "X") for s, p in logical.items()}


def _resolve_logical_z(sched) -> dict:
    """Logical operator used by codestate construction, mirrored here for the
    caps identities: ``sched.logical`` for logical kind Z, else ``{0: 'Z'}``."""
    lkind = str(getattr(sched, "logical_kind", "Z")).upper()
    return dict(sched.logical) if (lkind == "Z" and sched.logical) else {0: "Z"}


def _chain_multiplicity_map(sched):
    """Per-edge chain multiplicity computed from actual
    ``PepoLayout.plaquette_path`` outputs before the state is built. Chains are
    the eight stabilizers in schedule order followed by the logical operator;
    an edge traversed by k chains carries raw dim exactly 2^k."""
    lay = _pepo_layout(sched)
    chains = [dict(g) for g in sched.stab_paulis()]
    chains.append(_resolve_logical_z(sched))
    mult: dict[tuple[int, int], int] = {}
    for paulis in chains:
        path = [int(p) for p in lay.plaquette_path(paulis)]
        for a, b in zip(path[:-1], path[1:]):
            e = (a, b) if a < b else (b, a)
            mult[e] = mult.get(e, 0) + 1
    return lay, mult


def _pick_stabs(sched):
    """(weight-4 X-containing, weight-2) supports from the REAL schedule."""
    w4 = next(dict(s.paulis) for s in sched.stabilizers
              if len(s.paulis) == 4
              and any(str(p).upper() == "X" for p in s.paulis.values()))
    w2 = next(dict(s.paulis) for s in sched.stabilizers if len(s.paulis) == 2)
    return w4, w2


# --------------------------------------------------------------------------- #
# Fixtures (real-Google d3 schedule + the p1c within-cycle leak set)           #
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def sched():
    """The real d3_at_q6_7 XZZX schedule and r10 within-cycle streams.

    A textbook stand-in would change paths, multiplicities, and tensor-train
    supports, so absence of the
    local dataset is a SKIP, never a fallback."""
    xp = pytest.importorskip("error_coupling_simulator.frontend.xzzx_parser")
    r01c, r01m = xp.default_r01_paths()
    r10c, r10m = xp.default_r10_paths()
    if not (r01c.is_file() and r01m.is_file() and r10c.is_file() and r10m.is_file()):
        pytest.skip("d3 XZZX r01/r10 real-Google circuits absent under "
                    "DEFAULT_DATASET_ROOT (real patch only, no fallback)")
    s = xp.parse_xzzx_circuit(r01c, r01m, verify=True)
    s = s.with_within_cycle_streams(xp.parse_within_cycle_streams(r10c, r10m))
    assert int(s.n_data) == 9 and len(s.stabilizers) == 8, (s.n_data, len(s.stabilizers))
    return s


@pytest.fixture(scope="session")
def wc(sched):
    """The p1c within-cycle cell: calibrated theta + the CPTP leak Kraus set."""
    if not _CUDA:
        pytest.skip("CUDA unavailable — the within-cycle cell is built on the GPU host")
    from error_coupling_simulator.carrier.within_cycle import (
        FusedWithinCycleSampler,
        RunSpec,
    )
    from error_coupling_simulator.frontend import xzzx_parser as xp
    from error_coupling_simulator.mechanisms.qutrit_leakage import (
        solve_theta_for_wg_l1,
    )

    r01c, r01m = xp.default_r01_paths()
    theta = float(solve_theta_for_wg_l1(WG_L1_TARGET, g_seep=G_SEEP, g_heat=G_HEAT))
    host = FusedWithinCycleSampler(device="cuda")
    spec = RunSpec(circuit_path=r01c, metadata_path=r01m, m=0, theta=theta,
                   g_seep=G_SEEP, g_heat=G_HEAT, arm=ARM, b=B_BIAS,
                   readout_conv="biased_b", N=1, base_seed=0, R=1, dtype="c128")
    leak_t, leak_ev = host.build_within_cycle_leak(spec)
    # Independent Kraus completeness check, also required by leak_sample.
    assert leak_ev["cptp_residual"] < TOL_EXACT, leak_ev
    return {
        "sched": sched,
        "theta": theta,
        "leak_t": leak_t,                                    # (n_kraus, 3, 3) c128 cuda
        "leak_list": [leak_t[k] for k in range(int(leak_t.shape[0]))],
        "stabs": sched.stab_paulis(),
    }


def _fresh_reference(sched):
    """A bare exact density-matrix reference using the real code geometry:
    nine data qutrits, compiled POVM, and no ancilla."""
    from error_coupling_simulator.carrier.exact.qutrit_dm import QutritDM

    logical = dict(sched.logical)
    logical_kind = str(sched.logical_kind).upper()
    engine = QutritDM(int(sched.n_data), device="cuda")
    engine.set_code(
        stabilizers=sched.stab_paulis(),
        logical_z=logical if logical_kind == "Z" else None,
        logical_x=logical if logical_kind == "X" else None,
    )
    return engine


def _pick_jump_k(rdm: torch.Tensor, kraus: list) -> tuple[int, int]:
    """(dominant, jump) Kraus indices from the reference one-site RDM: dominant =
    max branch weight; jump = the branch maximizing |2>-inflow among branches
    with non-degenerate weight (test-side selection only — the SAME forced index
    drives both engine and reference, so the choice is instrumentation, not a
    certified map)."""
    pks, w2s = [], []
    for K in kraus:
        pks.append(float(torch.einsum("ij,ji->", K.conj().T @ K, rdm).real.item()))
        w2s.append(float((K @ rdm @ K.conj().T)[2, 2].real.item()))
    k_dom = int(np.argmax(pks))
    tot = float(sum(pks))
    live = [k for k in range(len(kraus)) if pks[k] > 1e-8 * max(tot, 1e-30)]
    require_precondition(bool(live), "no non-degenerate leak branch to force")
    k_jump = max(live, key=lambda k: w2s[k])
    require_precondition(w2s[k_jump] > 0.0,
                         "no |2>-pumping branch in the leak set — the b-branches "
                         "would be vacuous (scrutinize-vacuous rule)")
    return k_dom, k_jump


def _prep_pair(wc, seed: int, *, n_ops: int = 5, pump_sites: tuple[int, ...] = (),
               m: int = 0, per_op_bar: float | None = None):
    """A paired ``PepsState`` and ``QutritDM`` through the same random H/X/leak
    token program. Every leakage token is a forced-Kraus
    application, unnormalized on both sides (engine ``K_k psi``; reference
    ``apply_channel([K_k])`` = K rho K^dag): random-program LEAKs force the
    DOMINANT branch (norm-preserving to leading order); ``pump_sites`` get a
    JUMP-forced LEAK so |2> mass is live and the b-dependent branches are
    exercised NON-vacuously.  ``per_op_bar`` set => dense equality asserted after
    every operation."""
    state = _build_codestate(wc["sched"], m)
    eng = _fresh_reference(wc["sched"])
    eng.init_logical(m)
    kraus = wc["leak_list"]

    prog: list[tuple[str, int]] = []
    r = np.random.default_rng(seed)
    for _ in range(n_ops):
        prog.append((str(r.choice(["H", "X", "LEAK"])), int(r.integers(0, 9))))
    for s in pump_sites:
        prog.append(("LEAK_JUMP", int(s)))

    for i, (tok, site) in enumerate(prog):
        if tok in ("H", "X"):
            U = _qutrit_mat(tok)
            _apply_1site(state, U, site)
            eng.apply_gate(U, site)
        else:
            k_dom, k_jump = _pick_jump_k(_site_rdm(eng.rho, site), kraus)
            k = k_jump if tok == "LEAK_JUMP" else k_dom
            K = kraus[k]
            _apply_kraus_forced(state, K, site)
            eng.apply_channel([K], site)
        if per_op_bar is not None:
            worst = _pair_maxabs(state, eng)
            assert worst <= per_op_bar, (
                f"per-op equality: op {i} ({tok}@{site}) max-abs {worst:.3e} > "
                f"{per_op_bar:.1e}")
    tr = float(torch.diagonal(eng.rho).real.sum().item())
    require_precondition(tr > 1e-8, f"prep trace collapsed to {tr:.3e} — the "
                                    f"unnormalized comparisons would be vacuous")
    return state, eng


def _grown_engine_state(wc, seed: int):
    """Engine-only state with GROWN bonds for the truncation units: codestate +
    a few 1-site mixers + a jump-forced LEAK (static branch choice: max |2>-inflow
    matrix column — no reference needed), then every weight-four branch (outcome 0)
    UNTRUNCATED so a path bond carries a rich insertion.  Returns
    (state, largest_bond_name, its_dim)."""
    state = _build_codestate(wc["sched"], 0)
    r = np.random.default_rng(seed)
    for _ in range(4):
        _apply_1site(state, _qutrit_mat(str(r.choice(["H", "X"]))), int(r.integers(0, 9)))
    kraus = wc["leak_list"]
    scores = [float((K[2, 0].abs() + K[2, 1].abs()).item()) for K in kraus]
    k_jump = int(np.argmax(scores))
    require_precondition(scores[k_jump] > 0.0,
                         "no |2>-inflow branch in the leak set")
    for site in (0, 4):
        _apply_kraus_forced(state, kraus[k_jump], site)
    lay = _pepo_layout(wc["sched"])
    for s in wc["sched"].stabilizers:
        paulis = dict(s.paulis)
        if len(paulis) != 4:
            continue
        tt = _stab_tt(paulis, 0, B_BIAS, ARM, lay)
        _apply_stab_branch(state, tt)
    bond, dim = _largest_bond(state)
    return state, bond, dim


# =========================================================================== #
# Codestate: dense bridge, structural |2>-mass, caps identities, bond law     #
# per-edge 2^multiplicity bond law                                             #
# =========================================================================== #
@requires_cuda
class TestCodestate:
    @pytest.mark.parametrize("m", [0, 1])
    def test_dense_psi_outer_matches_oracle_rho(self, wc, m):
        # Dense |psi><psi| vs QutritDM.init_logical(m).rho, chunked
        # max-abs <= 1e-12, BOTH m (never a full 5.77-GiB comparison temp).
        state = _build_codestate(wc["sched"], m)
        psi = _dense_psi(state)
        assert psi.shape == (_N9,), psi.shape
        assert psi.dtype == torch.complex128, psi.dtype
        n2 = float((psi.conj() * psi).real.sum().item())
        assert abs(n2 - 1.0) <= TOL_EXACT, (
            f"codestate not unit-norm through the dense bridge: |psi|^2 = {n2!r}")
        eng = _fresh_reference(wc["sched"])
        eng.init_logical(m)
        worst = _psi_rho_maxabs(psi, eng.rho)
        assert worst <= TOL_EXACT, f"m={m}: max-abs {worst:.3e} > 1e-12"
        del state, eng, psi
        _free()

    def test_structural_two_mass_exactly_zero_on_tensors(self, wc):
        # |2>-mass is checked structurally on the tensors: the k=2
        # slice of EVERY site tensor is exactly 0.0 ((a) zero-tolerance; survives
        # any contraction). The representation uses k{pos} dimension 3 and
        # torch CUDA complex128.
        state = _build_codestate(wc["sched"], 0)
        tn = state.tn
        for pos in range(9):
            tag = f"Q{pos}"
            assert tag in tn.tag_map, f"missing site tag {tag}"
            tids = tn.tag_map[tag]
            assert len(tids) == 1, (tag, tids)
            t = tn.tensor_map[next(iter(tids))]
            assert torch.is_tensor(t.data), "site tensor is not a torch tensor"
            assert t.data.dtype == torch.complex128, t.data.dtype
            assert t.data.is_cuda, "site tensor not on CUDA"
            kname = f"k{pos}"
            assert kname in t.inds, (kname, t.inds)
            assert int(tn.ind_size(kname)) == 3, f"single-wire phys leg {kname} dim != 3"
            ax = list(t.inds).index(kname)
            sl = torch.narrow(t.data, ax, 2, 1)
            # structural zero: NOT a float-floor check (never NUMERICAL_ZERO here)
            assert float(sl.abs().max().item()) == 0.0, (
                f"site {pos}: |2> slice of the codestate tensor is not exactly 0.0")
        del state
        _free()

    @pytest.mark.parametrize("m", [0, 1])
    def test_caps_path_stabilizer_and_logical_identities(self, wc, m):
        # <S_g> = +1 for all stabilizers and <Z_L> = (-1)^m through the
        # PRODUCTION CAPS PATH at the d3 floor (<= 1e-12).  The caps path is the
        # instrument under test; the dense bridge (test above) is the cross-check,
        # never the source. Reads are formed as the ratio
        # vs the empty-caps norm read, so both normalized and unnormalized seam
        # conventions are certified without result-steering.
        state = _build_codestate(wc["sched"], m)
        n_read = _caps_read(state, {})
        require_precondition(abs(n_read) > 1e-12,
                             f"empty-caps norm read degenerate: {n_read!r}")
        for g in wc["stabs"]:
            paulis = dict(g)
            caps = {int(s): _qutrit_mat(p) for s, p in paulis.items()}
            q = complex(_caps_read(state, caps)) / complex(n_read)
            assert abs(q - 1.0) <= D3_CAPS_FLOOR, (
                f"caps-path <S_g> != +1 at the d3 floor: stab {paulis} read {q!r}")
        logical = _resolve_logical_z(wc["sched"])
        caps = {int(s): _qutrit_mat(p) for s, p in logical.items()}
        q = complex(_caps_read(state, caps)) / complex(n_read)
        want = float((-1.0) ** int(m))
        assert abs(q - want) <= D3_CAPS_FLOOR, (
            f"caps-path <Z_L> != {want:+.0f} at m={m}: read {q!r}")
        del state
        _free()

    def test_per_edge_dims_equal_two_to_chain_multiplicity(self, wc):
        # Per-edge raw dimension equals 2^(chain multiplicity through
        # that edge).  The multiplicity map is computed from the ACTUAL
        # plaquette_path outputs (eight stabilizers in schedule order followed
        # by the logical operator) before the state is built.
        lay, mult = _chain_multiplicity_map(wc["sched"])
        state = _build_codestate(wc["sched"], 0)
        prof = _bond_profile_norm(state)
        for edge in lay.grid_edges():
            want = 2 ** mult.get(edge, 0)
            got = int(prof.get(edge, 1))     # structurally empty edge has dimension 1
            assert got == want, (
                f"edge {edge}: raw bond dim {got} != 2^multiplicity = {want} "
                f"(multiplicity map: {mult})")
        del state
        _free()


# =========================================================================== #
# Per-operation pair: gates, forced-Kraus leakage, forced outcomes             #
# sqrt(E_s), all UNNORMALIZED at 1e-12                                         #
# =========================================================================== #
@requires_cuda
class TestPerOperationStateUpdates:
    def test_random_token_program_per_op_equality(self, wc):
        # The same random H/X/leak token program runs on both carriers,
        # per-op dense equality <= 1e-12; pump sites make the b-branches live.
        state, eng = _prep_pair(wc, seed=201, n_ops=6, pump_sites=(0,),
                                per_op_bar=TOL_EXACT)
        # leak-pump non-vacuity (scrutinize-vacuous rule): |2> mass live on the pump
        mass2 = _leaked_mass_rel(eng.rho, (0,))
        require_precondition(mass2 > 1e-4,
                             f"pump site carries relative |2> mass {mass2:.3e} <= 1e-4 "
                             f"— b-dependent branches would be vacuous")
        del state, eng
        _free()

    def test_forced_kraus_leak_dominant_and_jump_branches(self, wc):
        # Forced-Kraus leakage compares engine K_k psi unnormalized with the
        # independent apply_channel([K_k]) path for the
        # dominant branch (O(1) weight) AND a jump branch (weight precondition).
        state, eng = _prep_pair(wc, seed=202, n_ops=5, pump_sites=(4,))
        site = 4
        k_dom, k_jump = _pick_jump_k(_site_rdm(eng.rho, site), wc["leak_list"])
        for label, k in (("dominant", k_dom), ("jump", k_jump)):
            st_k = copy.deepcopy(state)
            rho_base = eng.rho.clone()
            K = wc["leak_list"][k]
            _apply_kraus_forced(st_k, K, site)
            eng.apply_channel([K], site)
            tr_branch = float(torch.diagonal(eng.rho).real.sum().item())
            require_precondition(tr_branch > 1e-8,
                                 f"{label} branch k={k} weight {tr_branch:.3e} "
                                 f"degenerate — comparison vacuous")
            worst = _pair_maxabs(st_k, eng)
            assert worst <= TOL_EXACT, (
                f"forced-Kraus LEAK ({label}, k={k}): max-abs {worst:.3e} > 1e-12")
            eng.rho = rho_base
            del st_k
            _free()
        del state, eng
        _free()

    @pytest.mark.parametrize("which", ["w4", "w2"])
    @pytest.mark.parametrize("outcome", [0, 1])
    def test_forced_outcome_sqrt_es_branch_unnormalized(self, wc, which, outcome):
        # Forced-outcome sqrt(E_s) branch for both outcomes, unnormalized:
        # engine tensor train vs independent project_stabilizer, <= 1e-12.
        w4, w2 = _pick_stabs(wc["sched"])
        paulis = w4 if which == "w4" else w2
        pump = tuple(sorted(int(s) for s in paulis))[:1]
        state, eng = _prep_pair(wc, seed=210 + outcome, n_ops=5, pump_sites=pump)
        mass2 = _leaked_mass_rel(eng.rho, sorted(int(s) for s in paulis))
        require_precondition(mass2 > 1e-4,
                             f"support relative |2> mass {mass2:.3e} <= 1e-4 — the "
                             f"b = {B_BIAS} branch would be vacuous")
        require_precondition(float(eng.rho.abs().max().item()) > 1e-6,
                             "prep image too small for a discriminating 1e-12 "
                             "unnormalized comparison")
        tt = _stab_tt(paulis, outcome, B_BIAS, ARM, getattr(state, "layout", None)
                      or _pepo_layout(wc["sched"]))
        _apply_stab_branch(state, tt)                    # engine: unnormalized branch
        eng.project_stabilizer(paulis, outcome, B_BIAS, ARM)  # independent reference
        worst = _pair_maxabs(state, eng)
        assert worst <= TOL_EXACT, (
            f"sqrt(E_s) {which} outcome={outcome}: max-abs {worst:.3e} > 1e-12")
        del state, eng
        _free()


# =========================================================================== #
# Structural lossless truncation                                               #
# =========================================================================== #
@requires_cuda
class TestLosslessPolicy:
    def test_lossless_cut_preserves_state_and_exact_local_rank(self, wc):
        """The lossless policy is structural: no cut may
        reduce rank below the exact local rank (sigma > 1e-12*sigma_1 count, the
        pinned zero-drop convention). On the contracted image, dense psi is
        unchanged at 1e-12
        by a lossless cut on a grown bond; ledger fields
        additionally pin kept rank == exact local rank when reported."""
        state, bond, dim = _grown_engine_state(wc, seed=301)
        require_precondition(dim > 1, f"grown bond {bond!r} has dim {dim} <= 1 — "
                                      f"a lossless cut would be vacuous")
        psi_before = _dense_psi(state).clone()
        entry = _truncate_lossless(state, bond)
        psi_after = _dense_psi(state)
        worst = float((psi_before - psi_after).abs().max().item())
        assert worst <= TOL_EXACT, (
            f"lossless policy on bond {bond!r} moved the contracted state by "
            f"{worst:.3e} > 1e-12 — a cut went below the exact local rank")
        if "exact_rank" in entry and "dim_out" in entry:
            assert int(entry["dim_out"]) == int(entry["exact_rank"]), (
                f"lossless kept rank != exact local rank: {entry}")
        # the module emits total_discarded (precut + ntu, squared-sigma); the pepo
        # fallback emits `discarded`. Read whichever the entry carries.
        disc_key = ("total_discarded" if "total_discarded" in entry
                    else ("discarded" if "discarded" in entry else None))
        if disc_key is not None:
            # zero-drop convention: only sigma <= 1e-12*sigma_1 junk may be cut;
            # its squared relative tail sits far beneath any physical scale.
            assert float(entry[disc_key]) <= 1e-20, (
                f"lossless policy discarded non-junk weight ({disc_key}): {entry}")
        del state, psi_before, psi_after
        _free()


# =========================================================================== #
# Single-wire tensor-train rank bounds at b = 0.9                              #
# =========================================================================== #
@requires_cuda
class TestSingleWireTTRanks:
    def test_tt_ranks_at_physical_evidence_point(self, wc):
        # Bounds are (3,5,3) for weight four and (3,) for weight two. Equality
        # is expected at arm A, b=0.9; a smaller result indicates a porting error.
        w4, w2 = _pick_stabs(wc["sched"])
        lay = _pepo_layout(wc["sched"])
        tt4 = _stab_tt(w4, 0, B_BIAS, ARM, lay)
        r4 = _tt_ranks(tt4)
        assert len(r4) == 3 and all(r <= b for r, b in zip(r4, (3, 5, 3))), (
            f"(a)-bound violation: w=4 single-wire TT ranks {r4} exceed (3,5,3)")
        assert r4 == (3, 5, 3), (
            f"w=4 ranks {r4} != (3,5,3) at b={B_BIAS} arm {ARM}; "
            f"below-bound indicates a porting error")
        tt2 = _stab_tt(w2, 0, B_BIAS, ARM, lay)
        r2 = _tt_ranks(tt2)
        assert len(r2) == 1 and r2[0] <= 3, (
            f"(a)-bound violation: w=2 single-wire TT ranks {r2} exceed (3,)")
        assert r2 == (3,), (
            f"w=2 ranks {r2} != (3,) at b={B_BIAS} arm {ARM}")


# =========================================================================== #
# Sampling-map values on CPU stubs                                            #
# =========================================================================== #
class TestSamplingMaps:
    """The three sampling maps are PURE decision functions; their conventions are
    matched to ``mps_forward``. Reference maps below are written independently,
    so a shared code path cannot hide a wrong comparison direction."""

    def test_stab_map_sbit_zero_iff_u_strictly_below_p0(self):
        smap = _map_sbit()
        # (u, p0, want): boundary u == p0 -> 1 because the comparison is strict.
        cases = [(0.0, 0.5, 0), (0.499, 0.5, 0), (0.5, 0.5, 1), (0.7, 0.5, 1),
                 (0.0, 0.0, 1), (0.0, 1e-9, 0), (0.999, 1.0, 0)]
        for u, p0, want in cases:
            got = int(smap(float(u), float(p0)))
            assert got == want, (
                f"stab map (u={u}, p0={p0}): got {got}, want {want} — the pinned "
                f"convention is sbit = 0 iff u < p0 (STRICT <)")

    def test_terminal_map_bit_one_iff_u_strictly_below_p1(self):
        tmap = _map_terminal_bit()
        cases = [(0.19, 0.2, 1), (0.2, 0.2, 0), (0.21, 0.2, 0),
                 (0.0, 0.0, 0), (0.0, 0.3, 1), (0.999, 1.0, 1)]
        for u, p1, want in cases:
            got = int(tmap(float(u), float(p1)))
            assert got == want, (
                f"terminal map (u={u}, p1={p1}): got {got}, want {want} — the "
                f"pinned convention is bit = 1 iff u < p1")

    def test_leak_tie_break_nonstrict_cumsum_fallback_last(self):
        lmap = _map_leak_branch()
        pk = [0.25, 0.25, 0.5]
        # Boundary u*tot == cumsum_k selects k by the non-strict comparison.
        cases = [(0.0, 0), (0.25, 0), (0.2500000001, 1), (0.5, 1), (0.75, 2), (1.0, 2)]
        for u, want in cases:
            got = int(lmap(float(u), list(pk)))
            assert got == want, (
                f"leak tie-break (u={u}, pk={pk}): got {got}, want {want} — the "
                f"the rule selects the first k with u*tot <= cumsum_k "
                f"(non-strict), fallback K-1")
        # a zero-weight FIRST branch at u = 0 is selected by the non-strict <=
        # (0 <= cumsum_0 = 0).
        assert int(lmap(0.0, [0.0, 1.0])) == 0
        # u = 1.0 lands on the last branch (via non-strict compare or fallback K-1
        # so the compare and fallback are indistinguishable by value.
        assert int(lmap(1.0, [0.3, 0.3])) == 1


# =========================================================================== #
# Sampling and detector-fold corruption falsifiers                            #
# =========================================================================== #
class TestSamplingAndFoldFalsifiers:
    """CPU-stub falsifiers for pure decision maps."""

    def test_sampling_direction_parity_falsifier(self):
        """At u = 0.1 and p1 = 0.2 the current map gives s = 0 while the
        deliberately wrong direction gives s = 1. Non-vacuity requires u outside
        [min(p1,1-p1), max(p1,1-p1)) — the two maps AGREE on that middle band
        that middle band."""
        u, p1 = 0.1, 0.2
        lo, hi = min(p1, 1.0 - p1), max(p1, 1.0 - p1)
        require_precondition(not (lo <= u < hi),
                             f"u = {u} lies in the agreement band [{lo}, {hi}) — "
                             f"the parity falsifier would be vacuous")
        smap = _map_sbit()
        got = int(smap(u, 1.0 - p1))                     # engine map on p0 = 1 - p1
        forbidden = 1 if u < p1 else 0                   # rejected PEPO direction
        assert got == 0, (
            f"engine stab map at (u={u}, p0={1.0 - p1}) returned {got} != 0 — "
            f"the current direction (sbit = 0 iff u < p0) is broken")
        assert forbidden == 1 and abs(got - forbidden) > FALSIFIER_FLOOR, (
            f"direction-parity corrupted image did not separate (got {got}, "
            f"forbidden {forbidden} via the rejected PEPO "
            f"'{_WRONG_SAMPLING_DIRECTION}') — the falsifier has no sensitivity")

    def test_det_s_fold_triple_agreement_and_orientation_falsifier(self):
        """det<->s fold agrees with an independent hand-typed reference,
        det_to_s(s_to_det) == id, and s_to_det(det_to_s) == id; the
        wrong-orientation suffix-XOR fold is
        DEMONSTRATED to differ from the canonical fold."""

        s2d, d2s = _fold_fns()
        R, n_stab, N = 4, 8, 32
        rng = np.random.default_rng(2026)
        s = rng.integers(0, 2, size=(N, R * n_stab)).astype(np.uint8)
        shaped = s.reshape(N, R, n_stab)
        det_ref = np.empty_like(shaped)
        det_ref[:, 0, :] = shaped[:, 0, :]
        det_ref[:, 1:, :] = shaped[:, 1:, :] ^ shaped[:, :-1, :]
        det_ref = det_ref.reshape(N, R * n_stab)
        for i in range(N):
            det_i = _fold_call(s2d, s[i], R, n_stab)
            assert np.array_equal(det_i, det_ref[i]), (
                f"shot {i}: s_to_det != seam fold\n got {det_i}\n exp {det_ref[i]}")
            s_back = _fold_call(d2s, det_i, R, n_stab)
            assert np.array_equal(s_back, s[i]), f"shot {i}: det_to_s(s_to_det) != id"
            det_back = _fold_call(s2d, _fold_call(d2s, det_ref[i], R, n_stab),
                                  R, n_stab)
            assert np.array_equal(det_back, det_ref[i]), (
                f"shot {i}: s_to_det(det_to_s) != id")
        # Corrupted image: the wrong-orientation suffix fold.
        s3 = s.reshape(N, R, n_stab)
        det_sab = np.empty_like(s3)
        det_sab[:, -1, :] = s3[:, -1, :]
        det_sab[:, :-1, :] = s3[:, :-1, :] ^ s3[:, 1:, :]
        det_sab = det_sab.reshape(N, R * n_stab)
        require_precondition(bool(np.any(det_sab != det_ref)),
                             "the random batch never separates the two fold "
                             "orientations — enrich the batch")
        img = float(np.max(np.abs(det_sab.astype(np.int8) - det_ref.astype(np.int8))))
        assert img > FALSIFIER_FLOOR, (
            f"orientation-fold corrupted image {img} <= {FALSIFIER_FLOOR}; the "
            f"comparison has no sensitivity")


@requires_cuda
class TestEngineFalsifiers:
    """Engine-invoking falsifiers on the real patch using CUDA."""

    def test_b_double_swap_obs_seam_engine_invoking(self, wc):
        """The exact-P(obs) seam must match the
        pinned dense composition (<= 1e-10) AND DIFFER from the b <-> (1-b)
        coherent-double-swap composition (> 1e-6) on a state with leaked mass on
        the logical support (non-vacuity preconditions asserted)."""
        logical = dict(wc["sched"].logical)
        isx = _isx_map(logical)
        pump = tuple(sorted(int(s) for s in logical))[:2]
        state, eng = _prep_pair(wc, seed=401, n_ops=4, pump_sites=pump)
        mass2 = _leaked_mass_rel(eng.rho, sorted(int(s) for s in logical))
        require_precondition(mass2 > 1e-4,
                             f"leaked logical mass {mass2:.3e} <= 1e-4 — the b-swap "
                             f"would be numerically invisible; pump more")
        p_ok = _obs_prob_dense(eng.rho, logical, B_BIAS, 0, swap_b=False)
        p_swap = _obs_prob_dense(eng.rho, logical, B_BIAS, 0, swap_b=True)
        require_precondition(abs(p_swap - p_ok) > FALSIFIER_FLOOR,
                             f"b-swap does not move the dense obs probability "
                             f"(|{p_swap:.6e} - {p_ok:.6e}| <= {FALSIFIER_FLOOR}) — "
                             f"no teeth against the double-swap")
        p_eng = _obs_prob_seam(copy.deepcopy(state), logical, isx, B_BIAS, 0)
        assert -1e-9 <= p_eng <= 1.0 + 1e-9, (
            f"obs seam returned {p_eng!r} outside [0, 1] — the normalized-"
            f"probability convention is broken (fix the seam, not this bar)")
        assert abs(p_eng - p_ok) <= TOL_TRACE, (
            f"ENGINE exact obs prob {p_eng:.12e} != unswapped dense {p_ok:.12e} "
            f"(> 1e-10) — the pinned F0/F1 composition is not implemented")
        assert abs(p_eng - p_swap) > FALSIFIER_FLOOR, (
            f"ENGINE exact obs prob {p_eng:.6e} matches the deliberately wrong swapped "
            f"composition {p_swap:.6e} within {FALSIFIER_FLOOR} — the coherent "
            f"double-swap is live in the engine")
        del state, eng
        _free()

    def test_wrong_outcome_sign_breaks_branch_equality(self, wc):
        """A flipped E_s outcome sign in the single-wire tensor train (engine
        outcome 1 vs reference outcome 0) must diverge beyond FALSIFIER_FLOOR on the
        normalized branch images.  Non-vacuity: BOTH outcome branches carry
        weight on the preparation so the corrupted branch is nondegenerate."""
        w4, _ = _pick_stabs(wc["sched"])
        pump = tuple(sorted(int(s) for s in w4))[:1]
        state, eng = _prep_pair(wc, seed=402, n_ops=6, pump_sites=pump)
        parent_tr = float(torch.diagonal(eng.rho).real.sum().item())
        p0w = eng.project_stabilizer(w4, 0, B_BIAS, ARM)   # reference branch stays
        p1w = parent_tr - p0w                               # E_0 + E_1 = I ((a))
        require_precondition(p0w > 1e-4 * parent_tr and p1w > 1e-4 * parent_tr,
                             f"one-sided branch weights (p0w={p0w:.3e}, "
                             f"p1w={p1w:.3e}) — the sign falsifier would be vacuous")
        tt_flipped = _stab_tt(w4, 1, B_BIAS, ARM, getattr(state, "layout", None)
                              or _pepo_layout(wc["sched"]))
        _apply_stab_branch(state, tt_flipped)
        worst = _pair_maxabs_normalized(state, eng)
        assert worst > FALSIFIER_FLOOR, (
            f"outcome-sign corruption did not trip (normalized diff {worst:.3e}); "
            f"the comparison has no sensitivity")
        del state, eng
        _free()

    def test_corrupt_stab_letter_swap_path_preserving(self, wc):
        """Flip one support site's X/Z letter while preserving the support path;
        content, SAME support => same plaquette path, so the TT still builds) —
        the engine branch must diverge from the correct reference update beyond
        FALSIFIER_FLOOR on normalized images."""
        w4, _ = _pick_stabs(wc["sched"])
        sites = sorted(int(s) for s in w4)
        corrupt = dict(w4)
        s0 = sites[0]
        corrupt[s0] = "Z" if str(w4[s0]).upper() == "X" else "X"
        assert corrupt != w4  # corruption sanity
        state, eng = _prep_pair(wc, seed=403, n_ops=6, pump_sites=(s0,))
        tt_bad = _stab_tt(corrupt, 0, B_BIAS, ARM, getattr(state, "layout", None)
                          or _pepo_layout(wc["sched"]))
        _apply_stab_branch(state, tt_bad)
        eng.project_stabilizer(w4, 0, B_BIAS, ARM)          # the TRUE update
        worst = _pair_maxabs_normalized(state, eng)
        assert worst > FALSIFIER_FLOOR, (
            f"CorruptStab did not trip (normalized diff {worst:.3e}); "
            f"the stabilizer-branch comparison has no sensitivity")
        del state, eng
        _free()

    def test_conj_layer_corruption_unconjugated_bra(self, wc):
        """A double-layer caps read built with an unconjugated
        bra copy has the image psi^T M psi (vs the correct psi^dag M psi).  On an
        Im-carrying state (precondition asserted) the two separate; the ENGINE
        caps read must match the correct image and reject the corrupted image."""
        state, eng = _prep_pair(wc, seed=404, n_ops=3)
        for site in (0, 4):
            for tok in ("H", "S", "H"):                  # S phases -> complex psi
                U = _qutrit_mat(tok)
                _apply_1site(state, U, site)
                eng.apply_gate(U, site)
        psi = _dense_psi(state)
        im_rel = float(psi.imag.abs().max().item()) / max(
            float(psi.abs().max().item()), 1e-30)
        require_precondition(im_rel > 1e-6,
                             f"evolved psi is (relatively) real (max|Im|/max|psi| = "
                             f"{im_rel:.3e}) — the conjugation falsifier would be vacuous")
        site = 4
        cap = torch.diag(torch.tensor([1.0, 0.5, 0.25], dtype=torch.complex128,
                                      device=psi.device))
        n = 9
        idx = torch.arange(psi.shape[0], device=psi.device)
        w = torch.tensor([1.0, 0.5, 0.25], dtype=torch.float64,
                         device=psi.device)[_site_trits(idx, site, n)].to(torch.complex128)
        n2 = complex((psi.conj() * psi).sum().item())
        require_precondition(abs(n2) > 1e-12,
                             f"degenerate norm read (n2={n2!r})")
        # Corrupted image: the M-term with the unconjugated bra (psi^T M psi) over
        # the TRUE norm (the unconjugated self-overlap psi^T psi is degenerate ~0
        # for balanced complex codestates — normalizing the M-term difference by
        # the true norm is well-defined and still separates from q_ok whenever psi
        # is complex, the essential conj-LAYER defect).
        q_ok = complex((psi.conj() * w * psi).sum().item()) / n2
        q_sab = complex((psi * w * psi).sum().item()) / n2
        require_precondition(abs(q_sab - q_ok) > FALSIFIER_FLOOR,
                             f"unconjugated-bra image does not separate "
                             f"(|{q_sab!r} - {q_ok!r}| <= {FALSIFIER_FLOOR})")
        n_read = _caps_read(state, {})
        q_eng = complex(_caps_read(state, {site: cap})) / complex(n_read)
        assert abs(q_eng - q_ok) <= TOL_TRACE, (
            f"caps-path read {q_eng!r} != dense psi^dag M psi {q_ok!r} (> 1e-10)")
        assert abs(q_eng - q_sab) > FALSIFIER_FLOOR, (
            f"caps-path read {q_eng!r} matches the unconjugated-bra corrupted image "
            f"{q_sab!r}; the conjugate layer is broken")
        del state, eng, psi
        _free()

    def test_ledger_discard_zero_exactly_when_off(self, wc):
        """A truncation that drops real weight
        (D_cap below the exact local rank) must report ``total_discarded``
        STRICTLY > 0.0; the SAME insertion (deepcopy) with NO cut (D_cap = dim)
        must report ``precut_discarded == 0.0`` AND ``total_discarded == 0.0``
        EXACTLY — the image a deleted/silent discard tracker emits everywhere, so
        the strict > 0.0 assertion is demonstrated to reject that corruption.

        Single-wire d3 exact ranks stay low, so a real-weight precut
        (exact_rank > 4*D_cap) is rarely reachable; the teeth ride the NTU pass's
        real-weight drop (D_cap < exact_rank), which is robustly reachable."""
        d_cap = 2
        state, bond, dim = _grown_engine_state(wc, seed=405)
        require_precondition(dim > d_cap,
                             f"grown bond dim {dim} <= D_cap {d_cap} — nothing to cut")
        mirror = copy.deepcopy(state)
        entry = _truncate_dcap(state, bond, d_cap)
        require_precondition(int(entry["exact_rank"]) > d_cap,
                             f"exact_rank {entry['exact_rank']} <= D_cap {d_cap} on "
                             f"bond {bond!r} (dim {dim}) — the cut drops no real "
                             f"weight; harness construction, not the gate")
        assert float(entry["total_discarded"]) > 0.0, (
            f"in-regime total_discarded not strictly positive: {entry} — the "
            f"discard tracker did not fire (or reports the deleted-tracker image)")
        assert int(entry["dim_out"]) == d_cap, entry
        # OFF: D_cap = dim => neither pass cuts => the deleted-tracker image 0.0
        # EXACTLY (a silent tracker that always reports 0.0 passes this half; the
        # ON case's strict > 0.0 is what gives it teeth).
        entry_off = _truncate_dcap(mirror, bond, int(dim))
        assert int(entry_off["dim_out"]) == int(dim), entry_off  # nothing cut
        assert float(entry_off["precut_discarded"]) == 0.0, (
            f"no-cut entry reports nonzero precut_discarded: {entry_off}")
        assert float(entry_off["total_discarded"]) == 0.0, (
            f"no-cut entry reports nonzero total_discarded: {entry_off} — the "
            f"0.0-when-off ledger image is broken and the strict > 0.0 loses teeth")
        del state, mirror
        _free()

    def test_window_binding_forced_flag(self, wc):
        """Force the defensive window-binding path, normally unreachable below
        ``W_max``, through
        window-bound cut (window cap 1 with a negligible eps budget on a grown
        bond) and asserts the ``window_binding`` ledger flag is EMITTED.  Both
        Both outcomes are legitimate: a clean return after one retry or an
        orderly-stop raise — the flag entry must exist either way.  (eps here is
        a forcing knob for the falsifier, not a numerical-floor claim.)"""
        state, bond, dim = _grown_engine_state(wc, seed=406)
        require_precondition(dim >= 4,
                             f"grown bond dim {dim} < 4 — a window cap of 1 could "
                             f"not discard real weight; grow richer")
        entry, raised = _truncate_dynamic_forced(state, bond, eps_spike=1e-30, w_max=1)
        flagged = _has_window_binding(_ledger(state)) or (
            isinstance(entry, dict) and _has_window_binding([entry]))
        assert flagged, (
            f"forced window-bound cut emitted NO window_binding flag entry "
            f"(returned entry: {entry!r}; raised: {raised!r}; ledger tail: "
            f"{_ledger(state)[-3:]}) — the flag machinery is dead")
        del state
        _free()


# =========================================================================== #
# eps_l known-answer units                                                    #
# =========================================================================== #
def _tn_2x2(site_arrays: dict, device="cuda"):
    """A hand-built 2x2 single-loop tensor network using tags Q{pos},
    phys k{pos} dim 3, bonds B{a}_{b}): positions 0:(0,0) 1:(0,1) 2:(1,0)
    3:(1,1); edges (0,1), (0,2), (1,3), (2,3).  ``site_arrays[pos]`` is a numpy
    (3, D, D) array with axis order (k, first-bond, second-bond) where the bond
    order per site is: 0 -> (B0_1, B0_2); 1 -> (B0_1, B1_3); 2 -> (B0_2, B2_3);
    3 -> (B1_3, B2_3)."""
    import quimb.tensor as qtn

    binds = {0: ("B0_1", "B0_2"), 1: ("B0_1", "B1_3"),
             2: ("B0_2", "B2_3"), 3: ("B1_3", "B2_3")}
    tensors = []
    for pos in range(4):
        data = torch.tensor(np.asarray(site_arrays[pos], dtype=np.complex128),
                            dtype=torch.complex128, device=device)
        tensors.append(qtn.Tensor(data=data,
                                  inds=(f"k{pos}",) + binds[pos],
                                  tags={f"Q{pos}"}))
    return qtn.TensorNetwork(tensors)


def _loop_eps_dense_reference(site_arrays: dict) -> float:
    """INDEPENDENT dense eps_l reference for the single 2x2 loop, written from
    scratch (numpy — no BP code, no message passing): grouped (T, T*) nodes,
    transfer matrix = the ordered product around the loop with one edge cut,
    eps_l = 1 - |lambda_1| / sum_i |lambda_i| (R-T Eq. 4).  For SQUARE per-node
    matrices the spectrum is cyclic-invariant, so every cut edge gives the same
    eps_l — the module's per-edge MAX and mean must both equal this value."""
    def grouped(T):
        # G[x, u, y, v] = sum_k T[k, x, y] * conj(T[k, u, v]); rows (x,u) = the
        # axis-1 (ket, bra) pair, cols (y, v) = the axis-2 pair
        T = np.asarray(T, dtype=np.complex128)
        G = np.einsum("kxy,kuv->xuyv", T, T.conj())
        d1, d2 = T.shape[1], T.shape[2]
        return G.reshape(d1 * d1, d2 * d2)

    transfer_site_0 = grouped(site_arrays[0])  # rows e01-pair, cols e02-pair
    transfer_site_1 = grouped(site_arrays[1])  # rows e01-pair, cols e13-pair
    transfer_site_2 = grouped(site_arrays[2])  # rows e02-pair, cols e23-pair
    transfer_site_3 = grouped(site_arrays[3])  # rows e13-pair, cols e23-pair
    # cut B0_2; walk e02 -> node0 -> e01 -> node1 -> e13 -> node3 -> e23 -> node2
    tm = (
        transfer_site_2
        @ transfer_site_3.T
        @ transfer_site_1.T
        @ transfer_site_0
    )
    ev = np.linalg.eigvals(tm)
    tot = float(np.sum(np.abs(ev)))
    if tot <= 0.0:
        return 0.0
    eps = 1.0 - float(np.max(np.abs(ev))) / tot
    d_e = int(round(math.sqrt(tm.shape[0])))
    assert eps <= 1.0 - 1.0 / (d_e * d_e) + 1e-12, (
        f"reference eps_l {eps} violates the (a) per-edge bound 1 - 1/D_e^2")
    return eps


# Hand-written loop-correlated bond-2 site tensors. The k = 2 slices are zero;
# k in {0, 1} literal values are chosen
# asymmetric + complex so no accidental symmetry can zero the loop correlation)
_EPS_2X2_SITES = {
    0: [[[0.90, 0.10], [-0.20, 0.60]],
        [[0.30 + 0.20j, -0.40], [0.50, 0.10 - 0.30j]],
        [[0.0, 0.0], [0.0, 0.0]]],
    1: [[[0.70, -0.30], [0.20 + 0.10j, 0.80]],
        [[-0.10, 0.60], [0.40 - 0.20j, 0.20]],
        [[0.0, 0.0], [0.0, 0.0]]],
    2: [[[0.50 + 0.30j, 0.20], [-0.60, 0.40]],
        [[0.30, -0.20 + 0.40j], [0.10, 0.70]],
        [[0.0, 0.0], [0.0, 0.0]]],
    3: [[[0.80, -0.10 + 0.20j], [0.30, -0.50]],
        [[0.20, 0.50], [-0.40 + 0.10j, 0.60]],
        [[0.0, 0.0], [0.0, 0.0]]],
}

# product state: all four bonds dim 1 (the transfer matrix is a 1x1 scalar)
_EPS_2X2_PRODUCT = {
    0: [[[0.80]], [[0.60]], [[0.0]]],
    1: [[[0.70]], [[0.50j]], [[0.0]]],
    2: [[[0.90]], [[-0.30]], [[0.0]]],
    3: [[[0.60]], [[0.40 + 0.20j]], [[0.0]]],
}


@requires_cuda
class TestEpsLKnownAnswers:
    def test_eps_l_product_state_smoke_zero(self):
        """Roundoff smoke only: this identity has no discriminating
        power — at bond dim 1 the loop transfer matrix is a scalar, so
        eps_l == 0 for ANY assembly.  Kept as the roundoff sanity leg; the
        discriminating anchor is the bond-2 loop test below."""
        state = _wrap_synthetic_state(_tn_2x2(_EPS_2X2_PRODUCT), d=2)
        stats = _eps_loop_stats(_eps_l_call(state))
        assert len(stats) == 1, f"2x2 grid has exactly one elementary loop: {stats}"
        eps_max, eps_mean = stats[0]
        assert abs(eps_max) <= 1e-12 and abs(eps_mean) <= 1e-12, (
            f"product-state eps_l != 0 to roundoff: max={eps_max!r}, "
            f"mean={eps_mean!r}")

    def test_eps_l_2x2_bond2_loop_matches_independent_dense(self):
        """Discriminating known answer: hand-written
        loop-correlated bond-2 tensors with a NONZERO eps_l, recomputed by an
        INDEPENDENT dense eigendecomposition IN THIS FILE (no shared BP code),
        matched at 1e-10.  A wrong TM assembly / message-gauge error produces a
        nonzero mismatch that the zero branch cannot mask."""
        arrays = {p: np.asarray(a, dtype=np.complex128)
                  for p, a in _EPS_2X2_SITES.items()}
        eps_ref = _loop_eps_dense_reference(arrays)
        require_precondition(eps_ref > 1e-3,
                             f"hand-written loop target degenerate (eps_ref = "
                             f"{eps_ref:.3e} <= 1e-3) — retune the literal tensors")
        state = _wrap_synthetic_state(_tn_2x2(arrays), d=2)
        stats = _eps_loop_stats(_eps_l_call(state))
        assert len(stats) == 1, f"2x2 grid has exactly one elementary loop: {stats}"
        eps_max, eps_mean = stats[0]
        # square per-node matrices => cyclic-invariant spectrum => every cut edge
        # gives the SAME eps_l; MAX and mean must both land on the reference.
        assert abs(eps_max - eps_ref) <= 1e-10, (
            f"eps_l MAX {eps_max!r} != independent dense reference {eps_ref!r} "
            f"(> 1e-10) — TM assembly / cut-edge / message-gauge error")
        assert abs(eps_mean - eps_ref) <= 1e-10, (
            f"eps_l mean {eps_mean!r} != independent dense reference {eps_ref!r} "
            f"(> 1e-10)")


# --------------------------------------------------------------------------- #
# NUMERICAL_ZERO wiring sanity                                                #
# --------------------------------------------------------------------------- #
def test_numerical_zero_is_the_shared_float_floor():
    assert NUMERICAL_ZERO == 1e-12
