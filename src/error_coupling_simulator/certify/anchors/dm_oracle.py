from __future__ import annotations

"""The DM-oracle anchor — the exact density-matrix ground-truth route.

A THIN adapter over the validated d3 qutrit DM wheel
(``error_coupling_simulator.carrier.exact.qutrit_dm``): it
DELEGATES to ``record_oracle`` / ``project_stabilizer`` / ``logical_distribution`` and reimplements no
physics (the do-not-lose-performance guardrail). It is INDEPENDENT of the MCWF / MPS carrier — a dense
density-matrix enumeration is a DIFFERENT object (the Gate-4 cross-construction), so DM↔carrier is a
genuine check, not a check vs the engine's own oracle (anti-circular).

The capability descriptor encodes the DM feasibility wall as DATA (do-not-OOM — the core checks it
BEFORE ``answer``, so the infeasible density matrix is never allocated):
  * ``DETECTOR_MARG`` at R=1 — per-detector ``P(s_j=1)`` under the carrier's ordered,
    non-selective sequential Lüders instrument (NO full-joint enumeration), followed by the
    same biased-``b`` terminal logical readout. MEMORY ACCOUNTING CORRECTED
    2026-07-06 (residual-② measured the real multiplier): the loop's live set is the held
    ``rho1`` + the working clone + the apply-path output (+ tile temporaries) — ``~3+eps`` DM
    copies AFTER the memory-lean ``apply_channel`` fix (it was ~5 copies before; measured
    k=5.05–5.44 at n=7/8), declared here as a conservative ``_DETECTOR_MARG_COPIES = 4``. At
    full-9q that is ~24.8 GB — INFEASIBLE under the default ``safety=0.5`` budget of a 32 GB
    card, so the router reports the cell UNANCHORED there (an honest gap, not a silent PASS;
    the certify facade's level grid is all full-register DETECTOR_MARG, so on such a card the
    DM leg needs an EXPLICIT caller choice). The true lean peak (~3.3 copies ≈ 20 GB) DOES fit
    the card physically — a caller who accepts the headroom may pass
    ``DMOracleAnchor(safety=0.78)`` (or larger) to enable the cell deliberately.
  * ``FULL_JOINT`` / ``SYNDROME_DIST`` — available only at R=1, where ``record_oracle`` stores the
    enumerated full joint and the capability gate applies its depth-n_stab memory bound. At R≥2 the
    oracle intentionally returns moments only, so these two statistics are semantically infeasible
    regardless of register size or memory budget; capability fails closed before allocation.
  * ``RR_CORR`` / ``SPATIAL_CORR`` (the R≥2 MOMENTS) — ``record_oracle``'s MOMENTS path: the EXACT
    detector first/second moments accumulated over the PRUNED depth-(n_stab·R) branch tree (it stores
    only fixed-size sum1/sum2 + the depth-first live-clone path, NOT the full joint). The conservative
    un-pruned depth bound is DECLARED in the capability's ``mem_bytes_estimate``; infeasible full-register
    cells stay closed while small valid sub-registers may answer. ``dropped_mass`` is reported (the prune
    simplification is bounded and reported, not silent). The (R-1,n_stab) ``rr_corr`` /
    (R,n_stab,n_stab) ``spatial_corr`` are reduced through the SHARED ``core.reduce_rr_corr`` /
    ``reduce_spatial_corr`` so
    the anchor's shape matches ``core.emitted_statistic`` EXACTLY (apples-to-apples). RR_CORR/SPATIAL
    are IDENTICALLY 0 for an independent-bit-flip foil — the statistic keeps its teeth.

Requires the controlled process to be ``DMReplayable``
(``process.dm_round_callbacks(device)``) so the DM replays the specified noise process.
GPU-only model-compute (CLAUDE.md): the DM lives on cuda.
"""

import numpy as np
import torch

from ..core import reduce_rr_corr, reduce_spatial_corr
from ..types import AnchorValue, Capability, Exactness, Regime, Statistic

_CDTYPE = torch.complex128
_ANSWERS = frozenset({Statistic.DETECTOR_MARG, Statistic.FULL_JOINT, Statistic.SYNDROME_DIST,
                      Statistic.RR_CORR, Statistic.SPATIAL_CORR})
#: the R>=2 moments answered via ``record_oracle``'s pruned depth-(n_stab*R) enumeration. The peak
#: LIVE memory is the depth-(n_stab*R) clone stack: the depth-first recursion holds one DM clone PER
#: LEVEL on the active root-to-leaf path (the parent state is kept across the two-outcome loop), so a
#: surviving path materializes the full depth, NOT a single 2-copy path. Pruning skips low-mass BRANCHES
#: (breadth + time) but does NOT shrink the depth, so it does not reduce the peak. ``record_oracle``'s
#: own §7.2 bound confirms ~100 GB at full-9q R>=2 -> INFEASIBLE there; the scale routes to the
#: carrier-MCWF and the DM moments GT lives on a SMALL VALID sub-code (the DM-for-anchor / MCWF-for-scale
#: split). The moments gate uses the same conservative ``depth * copy`` arithmetic as the R=1
#: full-joint branch — the OOM-as-data
#: contract, conservative by design (a capability descriptor must never claim feasible for a cell that
#: might OOM). ``dropped_mass`` is still reported per run so the prune simplification is bounded.
_MOMENTS = frozenset({Statistic.RR_CORR, Statistic.SPATIAL_CORR})
_JOINT_DISTRIBUTIONS = frozenset({Statistic.FULL_JOINT, Statistic.SYNDROME_DIST})
_R2_JOINT_UNAVAILABLE = (
    "R>=2 QutritDM.record_oracle returns moments only; it cannot provide the full joint "
    "required by FULL_JOINT or SYNDROME_DIST"
)
#: DETECTOR_MARG live-copy multiplier (CORRECTED 2026-07-06). The answer loop holds rho1 +
#: the working clone + the apply-path output, plus chunk/tile temporaries from the memory-lean
#: ``apply_channel`` (residual-② measured the PRE-fix path at k=5.05–5.44; the lean path's
#: structural live set is ~3+eps, INCLUDING the X-kind logical readout after the redundant
#: clone in ``logical_distribution`` was removed the same day). Declared conservatively at 4 —
#: a capability descriptor must never claim feasible for a cell that might OOM (the 2*copy
#: value this replaces did exactly that: it declared full-9q feasible at ~12 GB while the true
#: pre-fix peak projected to 31 GB). DECLARED LIMITATION: this bound covers the SINGLE-SITE
#: apply path (all lowering the supported external d3 schedules use). A ``DMReplayable`` process whose
#: ``round_pre`` applies TWO-site channels goes through the still-unchunked
#: ``apply_channel_2site`` (~4.5 copies transient) and is NOT bounded by this descriptor —
#: budget such processes separately (follow-up: chunk the two-site path).
_DETECTOR_MARG_COPIES = 4


class DMOracleAnchor:
    """The exact density-matrix ground-truth anchor (wraps ``forward.exact.qutrit_dm``)."""

    name = "dm_oracle"
    independence = (
        "exact dense density-matrix enumeration; a DIFFERENT object than the MCWF/MPS carrier "
        "(the Gate-4 cross-construction); schedule byte-identical to the raw .stim")

    def __init__(self, *, device: str | torch.device = "cuda", card_bytes: int | None = None,
                 safety: float = 0.5):
        self.device = torch.device(device)
        if card_bytes is None and torch.cuda.is_available():
            card_bytes = int(torch.cuda.get_device_properties(0).total_memory)
        self.card_bytes = int(card_bytes or 0)
        self.safety = float(safety)  # use at most safety * card for the live DM-copy stack

    # ----------------------------------------------------------------- #
    # capability — the OOM-as-data routing contract (PURE; no compute)   #
    # ----------------------------------------------------------------- #
    def answers(self) -> frozenset[Statistic]:
        return _ANSWERS

    @staticmethod
    def _dm_copy_bytes(n_active: int) -> int:
        return (3 ** int(n_active)) ** 2 * 16  # a complex128 density matrix

    def capability(self, statistic: Statistic, regime: Regime) -> Capability:
        if statistic not in _ANSWERS:
            return Capability(statistic, Exactness.EXACT, False, "DM anchor does not answer this", "a")
        if statistic in _JOINT_DISTRIBUTIONS and regime.R >= 2:
            return Capability(
                statistic,
                Exactness.EXACT,
                False,
                _R2_JOINT_UNAVAILABLE,
                "a",
                None,
            )
        copy = self._dm_copy_bytes(regime.n_active)
        budget = int(self.safety * self.card_bytes) if self.card_bytes else 0

        if statistic is Statistic.DETECTOR_MARG:
            if regime.R != 1:
                return Capability(statistic, Exactness.EXACT, False,
                                  "R>=2 detector marginals need the moments path (RR_CORR), not "
                                  "single-stab projection", "a", None)
            need = _DETECTOR_MARG_COPIES * copy  # rho1 + working clone + apply output + tiles
            ok = budget > 0 and need <= budget  # budget==0 (no CUDA / card unknown) => infeasible, not OOM
            reason = "" if ok else (
                "no GPU budget known (card_bytes=0; the DM oracle needs CUDA)" if budget == 0
                else f"~{need/1e9:.0f}GB live > {budget/1e9:.0f}GB budget")
            return Capability(statistic, Exactness.EXACT, ok, reason, "a", need)

        if statistic in _MOMENTS:
            # RR_CORR / SPATIAL_CORR via record_oracle's MOMENTS path (R>=2): the exact detector
            # first/second moments accumulated over the pruned branch tree (it does NOT store the full
            # joint — only fixed-size sum1/sum2). EXACT, class (a). The PEAK live memory is the
            # depth-(n_stab*R) clone stack (one clone per recursion level on the active path; pruning
            # does NOT shrink the depth), so this uses the conservative depth*copy bound: full-9q
            # R>=2 (~100 GB) is INFEASIBLE -> the scale routes to the carrier-MCWF and the DM moments GT
            # lives on a SMALL VALID sub-code (the DM-for-anchor / MCWF-for-scale split, §7.2).
            if regime.R < 2:
                return Capability(statistic, Exactness.EXACT, False,
                                  "the moments (round-to-round / spatial detector correlation) need "
                                  "R>=2; at R=1 there is no round-to-round or realized-distribution "
                                  "second moment", "a", None)
            if regime.n_stab is None:
                return Capability(statistic, Exactness.EXACT, False,
                                  "n_stab unknown for this regime — cannot bound the depth-(n_stab*R) "
                                  "clone stack; refusing (a None n_stab under-counts depth to R and "
                                  "would falsely pass the feasibility gate -> an OOM at answer time)",
                                  "a", None)
            depth = max(1, int(regime.n_stab)) * int(regime.R)
            need = depth * copy  # peak live = the depth-first clone stack (not a 2-copy path)
            ok = budget > 0 and need <= budget  # budget==0 (no CUDA / card unknown) => infeasible
            reason = "" if ok else (
                "no GPU budget known (card_bytes=0; the DM oracle needs CUDA)" if budget == 0
                else f"depth-{depth} x {copy/1e9:.1f}GB ~ {need/1e9:.0f}GB > {budget/1e9:.0f}GB budget "
                     f"(route the scale to the carrier-MCWF; the DM moments GT lives on a small valid "
                     f"sub-code)")
            return Capability(statistic, Exactness.EXACT, ok, reason, "a", need)

        # FULL_JOINT / SYNDROME_DIST at R=1 — the depth-n_stab enumeration copy stack.
        if regime.n_stab is None:
            return Capability(statistic, Exactness.EXACT, False,
                              "n_stab unknown for this regime — cannot bound the depth-(n_stab*R) "
                              "enumeration stack; refusing (a None n_stab under-counts depth and would "
                              "falsely pass the feasibility gate -> an OOM at answer time)", "a", None)
        depth = max(1, int(regime.n_stab)) * int(regime.R)
        need = depth * copy
        ok = budget > 0 and need <= budget  # budget==0 (no CUDA / card unknown) => infeasible, not OOM
        reason = "" if ok else (
            "no GPU budget known (card_bytes=0; the DM oracle needs CUDA)" if budget == 0
            else f"depth-{depth} x {copy/1e9:.1f}GB ~ {need/1e9:.0f}GB > {budget/1e9:.0f}GB budget "
                 f"(route the scale to the carrier-MCWF)")
        return Capability(statistic, Exactness.EXACT, ok, reason, "a", need)

    # ----------------------------------------------------------------- #
    # answer — delegate to the wheel (GPU model-compute)                #
    # ----------------------------------------------------------------- #
    def answer(self, process, statistic: Statistic, regime: Regime, *, N=None, generator=None,
               corrupt=None) -> AnchorValue:
        if statistic in _JOINT_DISTRIBUTIONS and regime.R >= 2:
            raise ValueError(f"DMOracleAnchor contract error: {_R2_JOINT_UNAVAILABLE}")

        from ...carrier.exact.qutrit_dm import QutritDM

        sched = process.sched
        stabs = sched.stab_paulis()
        if corrupt and "stab" in corrupt:
            # the corrupt-stabilizer control: flip stab j's X<->Z. The codestate is no longer its +1
            # eigenvalue eigenstate, so j's marginal goes ~random -> the comparison MUST fail (teeth).
            stabs = list(stabs)
            j = int(corrupt["stab"])
            _fl = {"X": "Z", "Z": "X"}
            stabs[j] = {s: _fl[str(p).upper()] for s, p in stabs[j].items()}
        n_stab = len(stabs)
        m = 0  # the GT is computed at prep m=0 (the batch-1 GT); the facade threads m in step 6
        round_pre, round_post = process.dm_round_callbacks(self.device)

        eng = QutritDM(int(sched.n_data), device=self.device)
        lk = str(sched.logical_kind).upper()
        eng.set_code(stabilizers=stabs,
                     logical_z=dict(sched.logical) if lk == "Z" else None,
                     logical_x=dict(sched.logical) if lk == "X" else None)
        eng.init_logical(m)
        prov = {"anchor": self.name, "independence": self.independence, "m": m}

        if statistic is Statistic.DETECTOR_MARG:
            # Exact carrier semantics at R=1: each reported bit is measured after the
            # previous stabilizers' non-selective Lüders channels.  Isolated projections
            # from one shared rho are only probe quantities and disagree in the leaked
            # sector when adjacent instruments do not commute.
            round_pre(eng, 0)
            marg = np.zeros(n_stab + 1, dtype=np.float64)
            marg[:n_stab] = eng.sequential_stabilizer_marginals(
                stabs, regime.b, regime.arm
            )
            _, p1 = eng.logical_distribution(regime.b)
            marg[n_stab] = float(p1)
            prov["measurement_semantics"] = "sequential_nonselective_lueders"
            prov["terminal_readout"] = "biased_b_product_povm"
            return AnchorValue(statistic, regime, marg, Exactness.EXACT, 0.0, "a", prov)

        if statistic in _MOMENTS:
            # RR_CORR / SPATIAL_CORR via record_oracle's MOMENTS path (R>=2): the EXACT detector
            # first/second moments over the pruned branch tree. Reduce the (R-1, n_stab) rr_corr /
            # (R, n_stab, n_stab) spatial_corr through the SHARED core reductions so the anchor's shape
            # matches emitted_statistic EXACTLY (apples-to-apples). The prune simplification is bounded:
            # dropped_mass is recorded in provenance so pruning remains explicit.
            res = eng.record_oracle(stabs, round_pre, round_post, R=regime.R, b=regime.b, arm=regime.arm)
            if res.get("kind") != "moments":
                raise RuntimeError(
                    f"DM moments anchor expected record_oracle kind='moments' at R={regime.R}, got "
                    f"{res.get('kind')!r} (the moments path needs R>=2)")
            prov["dropped_mass"] = float(res.get("dropped_mass", 0.0))
            prov["total_mass"] = float(res.get("total_mass", 0.0))
            if statistic is Statistic.RR_CORR:
                val = reduce_rr_corr(res["rr_corr"])
            else:
                val = reduce_spatial_corr(res["spatial_corr"])
            return AnchorValue(statistic, regime, val, Exactness.EXACT, 0.0, "a", prov)

        # FULL_JOINT / SYNDROME_DIST via the exact record_oracle (small register / R=1 small).
        res = eng.record_oracle(stabs, round_pre, round_post, R=regime.R, b=regime.b, arm=regime.arm)
        joint = _joint_to_keyed(res, n_stab, regime.R)
        prov["dropped_mass"] = float(res.get("dropped_mass", 0.0))
        if statistic is Statistic.SYNDROME_DIST:
            bits = regime.R * n_stab
            mask = (1 << bits) - 1
            marg: dict = {}
            for key, p in joint.items():
                marg[key & mask] = marg.get(key & mask, 0.0) + p
            joint = marg
        return AnchorValue(statistic, regime, joint, Exactness.EXACT, 0.0, "a", prov)


def _joint_to_keyed(res: dict, n_stab: int, R: int) -> dict:
    """``record_oracle`` R=1 ``joint`` ``{(detector_tuple, flip): p}`` -> ``{key_int: p}`` with the
    SAME packing ``core.emitted_statistic`` uses (det bits LSB-first, flip the top bit)."""
    bits = R * n_stab
    out: dict = {}
    for (s_tuple, f), p in res["joint"].items():
        key = sum(int(b) << i for i, b in enumerate(s_tuple)) + (int(f) << bits)
        out[key] = out.get(key, 0.0) + float(p)
    return out
