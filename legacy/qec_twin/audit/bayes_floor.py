from __future__ import annotations

"""Estimable Bayes decoding floor at large R — the unbiased, exact-per-sample Monte-Carlo
floor (the ⑦ floor-artifact fix + core scoring infrastructure).

Authority: ``docs/nonpauli_teacher/p7b_estimable_floor.md`` (the build spec). This module
GRADUATES the floor machinery from the gitignored ``outputs/`` one-off scripts into tracked
``src/`` core scoring infra — the gap-to-Bayes denominator every axis (binary AND soft) needs.

BACKEND SEAM (ADR 0010 §"Integration", item 8b). The floor LOGIC here — the MC averaging of
``min(P(s,0),P(s,1))/P(s)``, the ``[plugin, crossfit]`` bracket, the standard error, the L6
sanity arithmetic, the no-drift report, the ``_joint_sf_from_conditionals`` (s,f)-joint algebra
and the ``FloorProblem`` instance — is BACKEND-AGNOSTIC. The per-record syndrome-conditioned
(s, L) sector weights it averages come from a ``PathJointEvaluator`` (``audit/floor_backend.py``).
The certified d3 density-matrix backend is ``DMPathEvaluator`` (the current oracle; its
faithfulness is established COMPONENT-WISE by the #11 L1 independent lane vs the raw ``.stim``
+ a from-scratch oracle — schedule byte-identical to the ``.stim``, leak dynamics |2⟩(R) to
1.4e-15, WG slice exp(L/4) to 1.75e-13, ⟨S⟩/logical/detectors vs stim; the ``1.5e-18`` is the
PARSING/geometry cert, not a DM-output-distribution residual — see ``floor_backend.py``); the
upcoming quimb LPDO carrier (the scalable >d3 floor backend, ADR 0010
§Decision-2) implements the same Protocol and plugs in as ``evaluator=`` WITHOUT touching this
file. Every public floor function takes ``evaluator: PathJointEvaluator = DMPathEvaluator()``
(the default is backward-compatible — the d3 oracle). The DM bodies (the ``_*_batched`` helpers,
the ``QutritDM`` codestate / enumeration) were RELOCATED into ``DMPathEvaluator`` by a pure,
behavior-preserving move — ``tests/test_bayes_floor.py`` L1/L2/L3/L6 are the bit-identical guard.

    # NOTE (ADR 0010): the calibration/knobs `ForwardLaw` seam + the `ShotSet` sampler are a
    # SEPARATE, larger interface-extraction phase — NOT done here. This file extracts ONLY the
    # floor's `PathJointEvaluator`. `ForwardLaw` will be defined alongside the forward backend
    # (RepCodeForward / the quimb MCWF-MPS forward), not in the audit package.

WHAT THE BAYES FLOOR IS (spec §0). For the logical decision from the syndrome history the
Bayes (optimal-decoder) floor is

    F(R) = Σ_s min( P(s, f=0), P(s, f=1) )  =  E_{s∼P(s)}[ min(P(0|s), P(1|s)) ]  =  P(f ≠ f*(s)),

s ∈ {0,1}^(8R) the detector record, f the LOGICAL FLIP observable (f = parity(terminal data)
XOR m — the seam's isolation-respecting label, NOT the raw syndrome parity), f*(s)=argmax_f
P(f|s) the Bayes decoder. F is the smallest achievable LER; ``gap = LER_decoder − F ≥ 0`` is
the decoding headroom. NOTE the observable is the FLIP f, not m: the syndrome-only
½(1−TV(P(s|0),P(s|1))) is ≈0.5 (the stabilizer syndromes COMMUTE with the logical) and is the
WRONG object — see ``flip_aligned_floor`` in ``outputs/teacher_prereg/p7_decision.py``.

THE ARTIFACT THIS FIXES (red-team af7c9b, FAITHFULNESS_PROTOCOL standing-ledger item 7). The
prior build estimated F by the IN-SAMPLE PLUG-IN ``F̂_in = Σ_s min(n(s,0),n(s,1))/N``. In the
under-sampled regime ``2^(8R) ≫ N`` (R=5: 2^40 ≫ N, high collision rate) most records are
singletons ⇒ ``min(n(s,0),n(s,1)) = 0`` ⇒ ``F̂_in`` UNDER-counts the overlap ⇒ it is
DOWN-BIASED and RISES with N. A floor that is too low INFLATES ``gap = LER − F`` ⇒ a FALSE
NOT-CAPPED. "A down-biased floor makes the verdict conservative" is BACKWARDS for not-capped.

THE FIX — exact-per-sample Monte-Carlo (spec §2, UNBIASED). The plug-in's bias is entirely
from estimating ``P(f|s)`` by COUNTING (singletons → 0/1). We remove it by evaluating
``P(f|s)`` EXACTLY per sample from the certified oracle (the DM is the EXACT evolution under
the #11 L1 independently-verified components — schedule byte-identical to the raw ``.stim``,
leak dynamics / WG slice vs a from-scratch oracle, ⟨S⟩/logical/detectors vs stim — so it is
the exact teacher distribution; the leakage is INJECTED by our WG model, hence no external
circuit-leakage distribution to certify against). Draw ``s_i ∼ P(s)`` (Born-branch down a random measurement path via
``evaluator.sample_paths``), keep the UNNORMALIZED conditional handle ``ρ_{s_i}``
(``tr ρ_{s_i} = P(s_i)``), then read ``P(s_i,f) = tr(Π_f ρ_{s_i})`` via the logical-sector
traces, and

    F̂_mc = (1/N) Σ_i  min(P(s_i,0), P(s_i,1)) / tr(ρ_{s_i})  =  (1/N) Σ_i min(P(0|s_i), P(1|s_i)).

UNBIASEDNESS (spec §2 proof): ``E_{s∼P}[min(P(0|s),P(1|s))] = Σ_s P(s) min(·) = Σ_s
min(P(s,0),P(s,1)) = F``. Each summand is computed EXACTLY (path-propagation), so the only
error is MC variance ``Var ≤ Var_s[min(·)]/N ≤ 0.0625/N`` (min ∈ [0,½]; usually ≪ that since
most records are decisive). NO singleton/sparsity down-bias — an UNBIASED estimator, not a
less-biased plug-in.

THE (s, f) JOINT, EXACTLY (the load-bearing construction; the backend supplies the conditionals).
The teacher prepares ``|m⟩_L``. Within-cycle evolution + R rounds of (per-CZ leak slices,
syndrome projection, post-M Y) gives, for a syndrome path s, the UNNORMALIZED conditional
``ρ_{s|m}`` (``tr = P(s|m)``). The terminal logical-operator parity sector L is read by
``Π_{L=ℓ}``; the flip is ``f = L ⊕ m``. Under the UNIFORM logical prior the (s,f) joint is

    P(s, f) = ½ P(s, L=f | m=0)  +  ½ P(s, L=f⊕1 | m=1),     P(s, L=ℓ | m) = tr(Π_{L=ℓ} ρ_{s|m}).

So an exact-per-sample term needs BOTH m-conditionals at the SAME sampled s: we Born-branch one
m (sampling s) and KEEP its handle ``ρ_{s|m}`` (``evaluator.sample_paths``), then
DETERMINISTICALLY re-evolve the OTHER m onto the same s (``evaluator.reevolve_onto_records``).
Verified: ``Σ_{s,f} P(s,f) = 1`` and the exact (s,f) floor matches a from-scratch enumerator at
R=1 (test L1).

GPU-ONLY (binding): the model-compute lives on ``device='cuda'`` (no CPU fallback, no
"cuda if available else cpu"); only host-side bookkeeping (the floor scalars, metadata,
the plug-in/cross-fit counting) is CPU. complex128 throughout for the DM backend.

PLACEMENT (spec §3). ``audit/`` already owns gating / bands / validity; the floor is a validity
capability (the model-free Bayes-error denominator). The one-off analysis/decision harness
(``outputs/teacher_prereg/p7b_*.py``) consumes THIS module across R + leakage/realistic arms.

Public API:
  - ``mc_floor(...)``            — the exact-per-sample Monte-Carlo floor (UNBIASED) + MC SE.
  - ``enumerate_floor(...)``     — exact floor by full 2^(8R) enumeration (the R=1 anchor).
  - ``plugin_floor(...)``        — in-sample plug-in (down-biased; the artifact) — bracket LOWER.
  - ``crossfit_floor(...)``      — held-out / cross-fit (up-biased) — bracket UPPER.
  - ``floor_convergence_report(...)`` — fit F̂(N); the no-drift tripwire (plug-in rises, mc not).
Every return carries F̂, the MC SE, the ``[plugin, crossfit]`` bracket, the convergence flag, and
metadata (R, arm, observable). The ``PathJointEvaluator`` backend is in ``audit/floor_backend.py``.
"""

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import torch

from qec_twin.audit.floor_backend import (
    DMPathEvaluator,
    PathJointEvaluator,
    _n_from_dim,  # noqa: F401  (re-export kept available for harness callers)
    _require_cuda,
)
# Re-export the backend symbols the ledger (``tests/test_bayes_floor.py``) imports directly
# from this module — the floor's public surface is unchanged by the relocation.
from qec_twin.audit.floor_backend import (  # noqa: F401
    _logical_sector_traces_batched,
    _site_superop,
    cptp_residual,
)
from qec_twin.numerics import NUMERICAL_ZERO  # noqa: F401

CDTYPE = torch.complex128
RDTYPE = torch.float64


# =========================================================================== #
# Result containers                                                            #
# =========================================================================== #
@dataclass(frozen=True)
class FloorResult:
    """One Bayes-floor estimate with its honest band + provenance.

    ``F_hat`` is the floor estimate; ``mc_se`` the Monte-Carlo standard error (0 for the
    exact ``enumerate_floor``); ``bracket`` the ``(plugin, crossfit)`` valid bracket
    (``E[plugin] ≤ F ≤ E[crossfit]``; ``None`` if not requested); ``convergence_ok`` the
    no-drift flag (``None`` unless a convergence report set it); ``meta`` the metadata
    (R, arm, observable, register, N, the leg results, the DPI/coarsening declaration).
    """

    F_hat: float
    mc_se: float
    method: str
    bracket: tuple[float, float] | None = None
    convergence_ok: bool | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {"F_hat": float(self.F_hat), "mc_se": float(self.mc_se), "method": self.method,
                "bracket": (None if self.bracket is None else [float(self.bracket[0]),
                                                               float(self.bracket[1])]),
                "convergence_ok": self.convergence_ok, "meta": dict(self.meta)}


@dataclass(frozen=True)
class FloorProblem:
    """The Bayes-floor problem instance on a (sub-)register: the within-cycle geometry + leak.

    All fields are the engine-native description the floor enumerates over — IDENTICAL to the
    objects ``QutritDM`` / ``p7_floor_rgt1.dm_floor_history`` consume (no re-derivation):

    ``n``               number of qutrits in the register (3^n DM).
    ``streams``         ``{pos -> ordered pre-M token list}`` (H / X / LEAK), the within-cycle
                        interior stream per qutrit (the post-M Y is applied by the evolution on
                        every site each interior round). Sourced from the r10 interior round.
    ``stabs``           the ordered stabilizer ``paulis`` dicts (``{pos -> 'X'|'Z'}``).
    ``logical``         the logical-operator support ``{pos -> 'X'|'Z'}`` — the OBSERVABLE the
                        flip f is read from (asserted == the teacher's logical m at build time).
    ``leak_kraus``      the per-CZ leak slice ``exp(L/4)`` as a list of ``(3,3)`` torch CUDA
                        Kraus (one LEAK token applies it; an n_cz-CZ qutrit gets exp(L·n_cz/4)).
    ``b``               the swept leaked-readout bias (registration §2.2).
    ``arm``             the measurement-instrument arm ('A' default; 'C'/'B1'/'B2').
    ``R``               the number of rounds.
    ``register_kind``   'full' or 'subregister' (provenance + the DPI declaration).
    """

    n: int
    streams: dict[int, list[str]]
    stabs: list[dict[int, str]]
    logical: dict[int, str]
    leak_kraus: list[torch.Tensor]
    b: float
    arm: str
    R: int
    register_kind: str = "subregister"

    @property
    def n_stab(self) -> int:
        return len(self.stabs)


# =========================================================================== #
# The (s, f) joint algebra (backend-free)                                       #
# =========================================================================== #
def _joint_sf_from_conditionals(P_s_L_m0: tuple[torch.Tensor, torch.Tensor],
                                P_s_L_m1: tuple[torch.Tensor, torch.Tensor]
                                ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """``(P(s,f=0), P(s,f=1), P(s))`` from the per-m logical sector traces (the uniform-prior
    (s,f) joint). ``f = L ⊕ m`` ⇒ ``P(s,f=0)=½[P(s,L=0|m0)+P(s,L=1|m1)]``,
    ``P(s,f=1)=½[P(s,L=1|m0)+P(s,L=0|m1)]``, ``P(s)=P(s,f=0)+P(s,f=1)``. Backend-free: it takes
    the sector traces the ``PathJointEvaluator`` returns and forms the joint."""
    P_s_f0 = 0.5 * (P_s_L_m0[0] + P_s_L_m1[1])
    P_s_f1 = 0.5 * (P_s_L_m0[1] + P_s_L_m1[0])
    return P_s_f0, P_s_f1, P_s_f0 + P_s_f1


# =========================================================================== #
# The exact-per-sample MC floor (the core, UNBIASED)                            #
# =========================================================================== #
def mc_floor(prob: "FloorProblem", *, N: int, device: torch.device, seed: int = 0,
             batch: int = 2048, with_bracket: bool = False,
             crossfit_seed: int = 99, sanity: bool = True,
             evaluator: PathJointEvaluator = DMPathEvaluator()) -> FloorResult:
    """The EXACT-PER-SAMPLE Monte-Carlo Bayes floor ``F̂_mc`` (spec §2; UNBIASED) + the MC SE.

    Draw ``s_i ∼ P(s)`` (sample ``m ∼ Uniform{0,1}`` then Born-branch via
    ``evaluator.sample_paths`` — so s is marginal over the uniform logical prior), keep the
    UNNORMALIZED conditional handle ``ρ_{s_i|m}``, deterministically re-evolve the OTHER m onto
    the same record (``evaluator.reevolve_onto_records``), read the four logical-sector traces
    (``evaluator.logical_sector_traces``), and accumulate ``min(P(s_i,0),P(s_i,1)) / P(s_i)`` =
    ``min(P(0|s_i),P(1|s_i))``. The mean is ``F̂_mc``; the SE is ``sqrt(Var(terms)/N)``. NO
    counting of syndromes ⇒ NO singleton down-bias (the whole point).

    Runs B paths per GPU pass (``batch``); for the full 3^9 register ``batch=1`` (5.77 GiB/DM).
    GPU-only model compute. ``evaluator`` is the backend (default = the certified d3
    ``DMPathEvaluator``; the quimb LPDO carrier plugs in here without changing this logic).
    ``with_bracket`` additionally computes the ``[plugin, crossfit]`` band from the SAME N drawn
    records (a convenience; for an independent bracket draw a fresh sample via
    ``sample_teacher_records`` and call ``plugin_floor`` / ``crossfit_floor``).
    ``sanity`` runs the L6 probability checks per pass (``0 ≤ P(s,f)``, ``P(s,0)+P(s,1)=P(s)``,
    CPTP residual via the per-path trace conservation).

    Returns a :class:`FloorResult` with ``F_hat``, ``mc_se``, ``method='mc'``, the bracket (if
    requested), and metadata (R, arm, observable, register, N, the empirical variance, the per-pass
    sanity residuals, the leaked-logical mass).
    """
    _require_cuda(device)
    if N <= 0:
        raise ValueError("mc_floor needs N > 0")
    gen = torch.Generator(device=device); gen.manual_seed(int(seed))

    terms = torch.empty(N, dtype=RDTYPE, device=device)
    # for the optional plug-in / cross-fit bracket we ALSO retain (record, f) draws.
    keep_records = with_bracket
    rec_list: list[torch.Tensor] = []
    f_list: list[torch.Tensor] = []
    worst_norm = 0.0      # max |P(s,0)+P(s,1) - P(s)| (L6: == 0 by construction)
    worst_neg = 0.0       # max(0, -min P(s,f)) (L6: no negative joint)
    worst_trace = 0.0     # max |sum_paths-weighted P(s) drift| proxy (per-pass)
    done = 0
    while done < N:
        B = min(int(batch), N - done)
        m_draw = torch.randint(0, 2, (B,), generator=gen, device=device)
        # Born-branch B paths for m_draw; KEEP the conditional handle ρ_{s|m_draw} + the records.
        handle_kept, records = evaluator.sample_paths(prob, m_draw, B, gen)
        # the OTHER m (= 1 - m_draw), deterministically re-evolved onto the SAME records
        other_m = 1 - m_draw
        handle_other = evaluator.reevolve_onto_records(prob, other_m, records)
        # logical sectors for the kept (m_draw) and the other (1-m_draw)
        Lk0, Lk1 = evaluator.logical_sector_traces(handle_kept, prob.logical)
        Lo0, Lo1 = evaluator.logical_sector_traces(handle_other, prob.logical)
        # arrange into (s,L|m=0), (s,L|m=1) per path (depends which m was kept)
        kept0 = (m_draw == 0)
        P_s_L_m0_0 = torch.where(kept0, Lk0, Lo0)
        P_s_L_m0_1 = torch.where(kept0, Lk1, Lo1)
        P_s_L_m1_0 = torch.where(kept0, Lo0, Lk0)
        P_s_L_m1_1 = torch.where(kept0, Lo1, Lk1)
        P_s_f0, P_s_f1, P_s = _joint_sf_from_conditionals(
            (P_s_L_m0_0, P_s_L_m0_1), (P_s_L_m1_0, P_s_L_m1_1))
        mn = torch.minimum(P_s_f0, P_s_f1)
        cond = torch.where(P_s > 0, mn / P_s.clamp_min(1e-300), torch.zeros_like(P_s))
        terms[done:done + B] = cond
        if sanity:
            worst_norm = max(worst_norm, float(((P_s_f0 + P_s_f1) - P_s).abs().max()))
            worst_neg = max(worst_neg, float((-torch.minimum(P_s_f0, P_s_f1)).clamp_min(0).max()))
            # trace conservation proxy: the kept path's P(s|m) must equal the handle trace
            tr_kept = evaluator.path_trace(handle_kept)
            worst_trace = max(worst_trace, float(((Lk0 + Lk1) - tr_kept).abs().max()))
        if keep_records:
            # draw the logical flip f for this path (the realized label, for the plug-in/cross-fit):
            # f is determined by the kept m and the sampled terminal parity. We realize it by
            # sampling L ~ (P(s,L|m_draw)/P(s|m_draw)) then f = L ^ m_draw — an honest shot label.
            tr_kept = (Lk0 + Lk1).clamp_min(1e-300)
            pL1 = (Lk1 / tr_kept)
            uL = torch.rand(B, generator=gen, device=device, dtype=RDTYPE)
            Lsamp = (uL < pL1).to(torch.uint8)
            f = (Lsamp ^ m_draw.to(torch.uint8))
            rec_list.append(records.detach().to("cpu"))
            f_list.append(f.detach().to("cpu"))
        done += B

    F_hat = float(terms.mean().item())
    var = float(terms.var(unbiased=True).item()) if N > 1 else 0.0
    se = math.sqrt(var / N) if N > 0 else float("nan")

    meta: dict[str, Any] = {
        "R": prob.R, "arm": prob.arm, "observable": "logical_flip_f",
        "register_kind": prob.register_kind, "n": prob.n, "n_stab": prob.n_stab,
        "N": int(N), "b": float(prob.b), "empirical_var": var, "var_bound": 0.0625,
        "batch": int(batch),
    }
    if sanity:
        meta.update(sanity_norm_residual=worst_norm, sanity_neg_residual=worst_neg,
                    sanity_trace_residual=worst_trace,
                    cptp_residual=evaluator.cptp_residual(prob))
    bracket = None
    if with_bracket and rec_list:
        det = torch.cat(rec_list).numpy().astype(np.uint8)
        flip = torch.cat(f_list).numpy().astype(np.uint8)
        pl = _plugin_floor_from_records(det, flip)
        cf = _crossfit_floor_from_records(det, flip, seed=crossfit_seed)
        bracket = (pl, cf)
        meta.update(plugin_floor=pl, crossfit_floor=cf,
                    plugin_le_mc=bool(pl <= F_hat + se), mc_le_crossfit=bool(F_hat - se <= cf))
    return FloorResult(F_hat=F_hat, mc_se=se, method="mc", bracket=bracket, meta=meta)


# =========================================================================== #
# Exact enumeration floor (the L1 ground-truth anchor)                          #
# =========================================================================== #
def enumerate_floor(prob: "FloorProblem", *, device: torch.device, prune: float = 1e-15,
                    evaluator: PathJointEvaluator = DMPathEvaluator()) -> FloorResult:
    """The EXACT Bayes floor by FULL enumeration of all ``2^(R*n_stab)`` syndrome histories (the
    independent ground-truth anchor; spec §4 L1). For each ``m∈{0,1}`` ask the backend for the
    full within-cycle history map ``{path -> (P(s,L=0|m), P(s,L=1|m))}`` (``evaluator.enumerate_history``),
    then form the exact (s,f) joint and ``F = Σ_s min(P(s,0),P(s,1))``. Exact-by-enumeration (no
    Monte-Carlo, no bias) — for the DM backend the projection ``Tr[E_s ρ]`` equals the full
    Kraus-branch integral and ``E_0+E_1=I`` keeps the recursion's branch traces summing to the parent.

    Feasible on a sub-register at small R. ``evaluator`` defaults to the certified ``DMPathEvaluator``;
    ``prune`` is the DM backend's small-weight drop (default 1e-15 == the prior inline value, so the
    default path is bit-identical). For a ``DMPathEvaluator`` whose own ``_prune`` differs from the
    requested ``prune`` (e.g. the default singleton with a non-default ``prune=`` here) a fresh
    DM evaluator carrying ``prune`` is used (no shared-state mutation); non-DM backends ignore
    ``prune``. Returns ``method='enumerate'``, ``mc_se=0``, and the per-class history sums (each
    must be 1), the cell count, and the leaked-logical mass in ``meta``.

    EXACT-GRADE BACKENDS ONLY — DO NOT pass a TRUNCATED ``TNPathEvaluator`` (LPDO at ``chi`` below
    exact-grade): exactness here RELIES on ``E_0 + E_1 = I`` (the partition of unity) so the
    recursion's per-branch traces sum to the parent. A truncated LPDO breaks that identity on the
    truncated state, so the per-class history sums drift below 1 and this function RAISES the
    ``per-class history sums not 1`` ``AssertionError`` (verified tripping in
    ``outputs/teacher_prereg/p7h_positive_controls.py`` control 3b — it correctly REFUSES a
    truncated LPDO rather than returning a corrupted floor). For a truncated carrier use ``mc_floor``
    instead: it is per-PATH normalized (it divides by ``P(s)`` per sampled path), so it needs no
    partition-of-unity and stays a valid floor estimate under truncation (the truncation error is then
    the carrier's χ-convergence book, certified vs the DM oracle — see ``p7h_carrier_cert_HONEST.md``).
    """
    _require_cuda(device)
    if isinstance(evaluator, DMPathEvaluator) and evaluator._prune != float(prune):
        evaluator = DMPathEvaluator(prune=float(prune))
    h0 = evaluator.enumerate_history(prob, 0)
    h1 = evaluator.enumerate_history(prob, 1)
    keys = set(h0) | set(h1)
    F = 0.0
    sum_ps = 0.0
    sum0 = sum(v[0] + v[1] for v in h0.values())
    sum1 = sum(v[0] + v[1] for v in h1.values())
    for s in keys:
        a0, a1 = h0.get(s, (0.0, 0.0))   # (P(s,L=0|m0), P(s,L=1|m0))
        b0, b1 = h1.get(s, (0.0, 0.0))   # (P(s,L=0|m1), P(s,L=1|m1))
        P_s_f0 = 0.5 * (a0 + b1)
        P_s_f1 = 0.5 * (a1 + b0)
        F += min(P_s_f0, P_s_f1)
        sum_ps += P_s_f0 + P_s_f1
    meta = {"R": prob.R, "arm": prob.arm, "observable": "logical_flip_f",
            "register_kind": prob.register_kind, "n": prob.n, "n_stab": prob.n_stab,
            "n_cells": len(keys), "sum_P0": float(sum0), "sum_P1": float(sum1),
            "sum_Psf": float(sum_ps)}
    if not (abs(sum0 - 1.0) < 1e-6 and abs(sum1 - 1.0) < 1e-6):
        raise AssertionError(f"enumerate_floor: per-class history sums not 1 (P0={sum0}, P1={sum1})")
    if not (abs(sum_ps - 1.0) < 1e-6):
        raise AssertionError(f"enumerate_floor: (s,f) joint does not sum to 1 (got {sum_ps})")
    if not (-1e-9 <= F <= 0.5 + 1e-9):
        raise AssertionError(f"enumerate_floor: F={F} out of [0,0.5]")
    return FloorResult(F_hat=float(F), mc_se=0.0, method="enumerate", meta=meta)


# =========================================================================== #
# Bracket arms: in-sample plug-in (down-biased) + cross-fit (up-biased)         #
# =========================================================================== #
def _plugin_floor_from_records(det: np.ndarray, flip: np.ndarray) -> float:
    """In-sample plug-in ``Σ_s min(n(s,0),n(s,1))/N`` — DOWN-biased (the artifact). Vectorized
    (pack → unique → bincount), identical to ``p7_decision.flip_aligned_floor``."""
    N = int(det.shape[0])
    if N == 0:
        return 0.0
    packed = np.packbits(det.astype(np.uint8), axis=1) if det.ndim == 2 else det
    uniq, gid = np.unique(packed, axis=0, return_inverse=True)
    gid = gid.reshape(-1)
    K = int(gid.max()) + 1
    n1 = np.bincount(gid, weights=flip.astype(np.float64), minlength=K)
    ntot = np.bincount(gid, minlength=K).astype(np.float64)
    return float(np.minimum(ntot - n1, n1).sum() / N)


def _crossfit_floor_from_records(det: np.ndarray, flip: np.ndarray, *, seed: int = 0) -> float:
    """Held-out / cross-fit floor — UP-biased. Fit the per-record majority class ``f̂*(s)`` on a
    TRAIN split, score the disjoint TEST split's error against it; symmetrize over the 2-fold swap.
    Test records UNSEEN in train default to the global-majority guess (still a valid suboptimal
    decoder ⇒ its risk ≥ F). ``E[F̂_cv] ≥ F`` (the fitted decoder is suboptimal at finite train).

    Records are mapped to integer ids by a SINGLE global ``np.unique`` over all packed rows (a robust
    shared id space — no fragile structured-view), so a train/test split is a fast ``bincount`` per
    fold on the shared ids."""
    N = int(det.shape[0])
    if N < 2:
        return float("nan")
    rng = np.random.default_rng(seed)
    perm = rng.permutation(N)
    packed = np.packbits(det.astype(np.uint8), axis=1) if det.ndim == 2 else det
    # one shared id space across ALL rows (train+test see the SAME record-id for the same record)
    _uniq, ids = np.unique(packed, axis=0, return_inverse=True)
    ids = ids.reshape(-1).astype(np.int64)
    K = int(ids.max()) + 1
    flip_u8 = flip.astype(np.uint8)
    half = N // 2
    errs = []
    for tr_idx, te_idx in ((perm[:half], perm[half:]), (perm[half:], perm[:half])):
        tr_ids = ids[tr_idx]
        n1 = np.bincount(tr_ids, weights=flip_u8[tr_idx].astype(np.float64), minlength=K)
        ntot = np.bincount(tr_ids, minlength=K).astype(np.float64)
        maj = (n1 > (ntot - n1)).astype(np.uint8)          # per-record majority f on train
        seen = ntot > 0                                    # records the train split observed
        global_maj = np.uint8(flip_u8[tr_idx].mean() >= 0.5)
        te_ids = ids[te_idx]
        pred = np.where(seen[te_ids], maj[te_ids], global_maj)
        errs.append(float((pred.astype(np.uint8) ^ flip_u8[te_idx]).mean()))
    return float(np.mean(errs))


def plugin_floor(det: np.ndarray, flip: np.ndarray) -> FloorResult:
    """The IN-SAMPLE plug-in Bayes floor (the bracket LOWER; DOWN-biased — the ⑦ artifact).

    ``det`` is the ``(N, R*n_stab)`` detector-event record array (bool/uint8) and ``flip`` the
    ``(N,)`` logical-flip labels — the SAME ``(detection_events, obs_flips)`` convention the seam
    (``outputs/teacher_prereg/p7_seam.teacher_shots_to_events``) emits and ``decode_dem`` consumes
    (first-round-raw + interior round-to-round XOR). ``E[plugin] ≤ F``; it RISES with N in the
    under-sampled regime — the convergence tripwire's positive control. ``mc_se`` is the binomial
    shot SE on the floor. Host-side counting (no GPU)."""
    N = int(det.shape[0])
    pl = _plugin_floor_from_records(det, flip)
    se = math.sqrt(max(pl * (1.0 - pl), 1e-12) / N) if N > 0 else float("nan")
    # collision diagnostics (the under-sampling signature)
    packed = np.packbits(det.astype(np.uint8), axis=1) if det.ndim == 2 else det
    uniq, gid = np.unique(packed, axis=0, return_inverse=True)
    gid = gid.reshape(-1); K = int(gid.max()) + 1 if N else 0
    n1 = np.bincount(gid, weights=flip.astype(np.float64), minlength=K)
    ntot = np.bincount(gid, minlength=K).astype(np.float64)
    n_coll = int((((ntot - n1) > 0) & (n1 > 0)).sum())
    meta = {"N": N, "n_distinct": int(K), "n_collision": n_coll,
            "collision_frac": float(2 * n_coll / max(K, 1)), "observable": "logical_flip_f",
            "bias": "down (in-sample plug-in; rises with N)"}
    return FloorResult(F_hat=float(pl), mc_se=se, method="plugin", meta=meta)


def crossfit_floor(det: np.ndarray, flip: np.ndarray, *, seed: int = 0) -> FloorResult:
    """The HELD-OUT / cross-fit Bayes floor (the bracket UPPER; UP-biased). The fitted decoder is
    suboptimal at finite train ⇒ ``E[crossfit] ≥ F``. With ``plugin_floor`` it gives the valid
    bracket ``E[plugin] ≤ F ≤ E[crossfit]`` (spec §1). Host-side."""
    N = int(det.shape[0])
    cf = _crossfit_floor_from_records(det, flip, seed=seed)
    se = math.sqrt(max(cf * (1.0 - cf), 1e-12) / N) if N > 0 else float("nan")
    meta = {"N": N, "observable": "logical_flip_f", "bias": "up (held-out cross-fit)", "seed": seed}
    return FloorResult(F_hat=float(cf), mc_se=se, method="crossfit", meta=meta)


def bracket_floor(det: np.ndarray, flip: np.ndarray, *, seed: int = 0) -> tuple[float, float]:
    """The valid ``(plugin, crossfit)`` bracket from a record/flip sample: ``[E[plugin], E[crossfit]]``
    contains F (spec §1, a sample-splitting identity; the only premise = i.i.d. shots)."""
    return (_plugin_floor_from_records(det, flip), _crossfit_floor_from_records(det, flip, seed=seed))


# =========================================================================== #
# Convergence report (the no-drift tripwire)                                    #
# =========================================================================== #
def floor_convergence_report(prob: "FloorProblem", *, device: torch.device,
                             N_sweep: tuple[int, ...] = (2000, 8000, 32000),
                             seed: int = 0, batch: int = 2048,
                             plugin_sample_N: int | None = None,
                             evaluator: PathJointEvaluator = DMPathEvaluator()) -> dict[str, Any]:
    """Fit ``F̂(N)`` over an N-sweep and emit the NO-DRIFT TRIPWIRE (spec §4 L2): the UNBIASED
    ``mc_floor`` must NOT drift with N (slope ≈ 0 within SE), while the in-sample PLUG-IN must RISE
    (slope > 0 — the positive control that the tripwire fires). For each N: run ``mc_floor`` (its
    SE) AND draw a fresh ``plugin_sample_N`` (default N) record sample to estimate the plug-in.

    The plug-in record sample is drawn by Born-sampling the teacher (the SAME within-cycle path via
    ``sample_teacher_records``), realizing per-shot ``(detector record, logical flip)`` — exactly the
    under-sampled-regime object the plug-in is biased on. ``evaluator`` is forwarded to both
    ``mc_floor`` and ``sample_teacher_records``. Returns the per-N rows, the OLS slopes (mc, plugin)
    with their SEs, and ``convergence_ok`` (mc slope consistent with 0 AND plug-in slope > 0). GPU
    model compute.
    """
    _require_cuda(device)
    rows = []
    mc_vals, mc_ses, pl_vals = [], [], []
    Ns = [int(n) for n in N_sweep]
    for i, N in enumerate(Ns):
        mc_res = mc_floor(prob, N=N, device=device, seed=seed + i, batch=batch, sanity=False,
                          evaluator=evaluator)
        pN = int(plugin_sample_N or N)
        det, flip = sample_teacher_records(prob, N=pN, device=device, seed=seed + 1000 + i,
                                           batch=batch, evaluator=evaluator)
        pl = _plugin_floor_from_records(det, flip)
        mc_vals.append(mc_res.F_hat); mc_ses.append(mc_res.mc_se); pl_vals.append(pl)
        rows.append({"N": N, "mc": mc_res.F_hat, "mc_se": mc_res.mc_se, "plugin": pl,
                     "var": mc_res.meta.get("empirical_var")})

    def _ols_slope(xs, ys):
        x = np.array([math.log10(max(v, 1)) for v in xs], dtype=float)  # slope per decade of N
        y = np.array(ys, dtype=float)
        A = np.vstack([x, np.ones_like(x)]).T
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        slope = float(coef[0])
        resid = y - A @ coef
        dof = max(len(x) - 2, 1)
        s2 = float((resid @ resid) / dof)
        sxx = float(((x - x.mean()) ** 2).sum())
        slope_se = math.sqrt(s2 / sxx) if sxx > 0 else float("inf")
        return slope, slope_se

    mc_slope, mc_slope_se = _ols_slope(Ns, mc_vals)
    pl_slope, pl_slope_se = _ols_slope(Ns, pl_vals)
    mc_flat = abs(mc_slope) <= 3.0 * max(mc_slope_se, max(mc_ses) if mc_ses else 0.0)
    plugin_rises = pl_slope > 0.0  # the artifact's signature
    convergence_ok = bool(mc_flat)
    return {"rows": rows, "mc_slope_per_decade": mc_slope, "mc_slope_se": mc_slope_se,
            "plugin_slope_per_decade": pl_slope, "plugin_slope_se": pl_slope_se,
            "mc_flat": bool(mc_flat), "plugin_rises": bool(plugin_rises),
            "convergence_ok": convergence_ok,
            "meta": {"R": prob.R, "arm": prob.arm, "observable": "logical_flip_f",
                     "register_kind": prob.register_kind, "N_sweep": Ns}}


# =========================================================================== #
# Teacher record sampler (for plug-in / cross-fit / convergence)               #
# =========================================================================== #
def sample_teacher_records(prob: "FloorProblem", *, N: int, device: torch.device, seed: int = 0,
                           batch: int = 2048,
                           evaluator: PathJointEvaluator = DMPathEvaluator()
                           ) -> tuple[np.ndarray, np.ndarray]:
    """Born-sample ``N`` teacher shots → ``(det[N, R*n_stab], flip[N])`` in the seam convention
    (raw per-round syndrome → first-round-raw + interior round-to-round XOR; flip = L ⊕ m).

    Samples ``m ∼ Uniform{0,1}`` then Born-branches the within-cycle state (via
    ``evaluator.sample_paths`` — so the marginal record law is ``P(s)`` and the flip law is the true
    ``P(f|s)``) — the SAME draw ``mc_floor`` uses, but here we EMIT the (record, flip) pair (the
    object the plug-in / cross-fit / decoder consume). The raw per-round syndrome is folded to
    detectors exactly as ``p7_seam.teacher_shots_to_events``: ``det[:,0,:]=s[:,0,:]``;
    ``det[:,r,:]=s[:,r,:]^s[:,r-1,:]`` for r≥1. GPU model compute; the folding is host-side uint8.
    Used by ``plugin_floor`` / ``crossfit_floor`` / the convergence report; NOT itself a floor."""
    _require_cuda(device)
    if N <= 0:
        raise ValueError("sample_teacher_records needs N > 0")
    gen = torch.Generator(device=device); gen.manual_seed(int(seed))
    R, n_stab = prob.R, prob.n_stab
    syn = np.empty((N, R * n_stab), dtype=np.uint8)
    flip = np.empty(N, dtype=np.uint8)
    done = 0
    while done < N:
        B = min(int(batch), N - done)
        m_draw = torch.randint(0, 2, (B,), generator=gen, device=device)
        handle_kept, records = evaluator.sample_paths(prob, m_draw, B, gen)
        L0, L1 = evaluator.logical_sector_traces(handle_kept, prob.logical)
        tr = (L0 + L1).clamp_min(1e-300)
        uL = torch.rand(B, generator=gen, device=device, dtype=RDTYPE)
        Lsamp = (uL < (L1 / tr)).to(torch.uint8)
        f = (Lsamp ^ m_draw.to(torch.uint8))
        syn[done:done + B] = records.detach().to("cpu").numpy().astype(np.uint8)
        flip[done:done + B] = f.detach().to("cpu").numpy().astype(np.uint8)
        done += B
    # fold raw per-round syndromes → detectors (first-round raw + interior round-to-round XOR)
    s = syn.reshape(N, R, n_stab)
    det = np.empty((N, R, n_stab), dtype=np.uint8)
    det[:, 0, :] = s[:, 0, :]
    if R > 1:
        det[:, 1:, :] = s[:, 1:, :] ^ s[:, :-1, :]
    return det.reshape(N, R * n_stab), flip


# =========================================================================== #
# Problem builders (from the parsed schedule)                                  #
# =========================================================================== #
def build_full_problem(schedule, interior_streams: dict[int, tuple], leak_kraus: list[torch.Tensor],
                       *, R: int, b: float, arm: str = "A") -> FloorProblem:
    """Build the FULL 3^9 within-cycle :class:`FloorProblem` from the parsed r01 schedule + the r10
    interior streams (the within-cycle source split, P4a model §1). The pre-M token list per qutrit
    is the interior stream with the post-M Y stripped (the evolution applies Y on every site each
    interior round). The logical OBSERVABLE is the schedule's logical (asserted == the teacher's m).
    """
    streams = {}
    for p in range(schedule.n_data):
        toks = interior_streams[p]
        streams[p] = [t for t in toks if t in ("H", "X", "LEAK")]
    return FloorProblem(n=schedule.n_data, streams=streams, stabs=schedule.stab_paulis(),
                        logical=dict(schedule.logical), leak_kraus=leak_kraus, b=float(b),
                        arm=str(arm), R=int(R), register_kind="full")
