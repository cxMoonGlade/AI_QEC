from __future__ import annotations

"""The DM-oracle anchor — the exact density-matrix ground-truth route.

A THIN adapter over the validated d3 qutrit DM wheel (``qec_twin.forward.exact.qutrit_dm``): it
DELEGATES to ``record_oracle`` / ``project_stabilizer`` / ``logical_distribution`` and reimplements no
physics (the do-not-lose-performance guardrail). It is INDEPENDENT of the MCWF / MPS carrier — a dense
density-matrix enumeration is a DIFFERENT object (the Gate-4 cross-construction), so DM↔carrier is a
genuine check, not a check vs the engine's own oracle (anti-circular).

The capability descriptor encodes the DM feasibility wall as DATA (do-not-OOM — the core checks it
BEFORE ``answer``, so the infeasible density matrix is never allocated):
  * ``DETECTOR_MARG`` at R=1 — per-detector ``P(s_j=1)`` via a SINGLE-stabilizer projection of the
    one-round-evolved rho (the reviewer-validated full-9q approach; ~2 DM copies, NO enumeration) +
    the logical-flip rate. Feasible at full-9q R=1 (~12 GB) on a 32 GB card.
  * ``FULL_JOINT`` / ``SYNDROME_DIST`` — ``record_oracle``'s depth-(n_stab·R) enumeration: feasible at
    a small register or R=1 small; INFEASIBLE (``feasible=False``) at R=1 full-9q (~50 GB) and R≥2
    full-9q (~100 GB) — the core then routes the scale to the carrier-MCWF.

Requires the teacher to be ``DMReplayable`` (``teacher.dm_round_callbacks(device)``) so the DM replays
the teacher's EXACT mechanism. GPU-only model-compute (CLAUDE.md): the DM lives on cuda.
"""

import numpy as np
import torch

from qec_twin.audit.certify.types import AnchorValue, Capability, Exactness, Regime, Statistic

_CDTYPE = torch.complex128
_ANSWERS = frozenset({Statistic.DETECTOR_MARG, Statistic.FULL_JOINT, Statistic.SYNDROME_DIST})


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
        copy = self._dm_copy_bytes(regime.n_active)
        budget = int(self.safety * self.card_bytes) if self.card_bytes else 0

        if statistic is Statistic.DETECTOR_MARG:
            if regime.R != 1:
                return Capability(statistic, Exactness.EXACT, False,
                                  "R>=2 detector marginals need the moments path (RR_CORR), not "
                                  "single-stab projection", "a", None)
            need = 2 * copy  # rho1 + the projected clone
            ok = budget == 0 or need <= budget
            reason = "" if ok else f"~{need/1e9:.0f}GB live > {budget/1e9:.0f}GB budget"
            return Capability(statistic, Exactness.EXACT, ok, reason, "a", need)

        # FULL_JOINT / SYNDROME_DIST — the depth-(n_stab*R) enumeration copy stack
        depth = max(1, int(regime.n_stab or 0)) * int(regime.R)
        need = depth * copy
        ok = budget == 0 or need <= budget
        reason = "" if ok else (f"depth-{depth} x {copy/1e9:.1f}GB ~ {need/1e9:.0f}GB > "
                                f"{budget/1e9:.0f}GB budget (route the scale to the carrier-MCWF)")
        return Capability(statistic, Exactness.EXACT, ok, reason, "a", need)

    # ----------------------------------------------------------------- #
    # answer — delegate to the wheel (GPU model-compute)                #
    # ----------------------------------------------------------------- #
    def answer(self, teacher, statistic: Statistic, regime: Regime, *, N=None, generator=None,
               corrupt=None) -> AnchorValue:
        from qec_twin.forward.exact.qutrit_dm import QutritDM

        sched = teacher.sched
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
        round_pre, round_post = teacher.dm_round_callbacks(self.device)

        eng = QutritDM(int(sched.n_data), device=self.device)
        lk = str(sched.logical_kind).upper()
        eng.set_code(stabilizers=stabs,
                     logical_z=dict(sched.logical) if lk == "Z" else None,
                     logical_x=dict(sched.logical) if lk == "X" else None)
        eng.init_logical(m)
        prov = {"anchor": self.name, "independence": self.independence, "m": m}

        if statistic is Statistic.DETECTOR_MARG:
            # the reviewer-validated full-9q R=1 path: single-stab projection of the evolved rho.
            round_pre(eng, 0)
            rho1 = eng.rho.clone()
            marg = np.zeros(n_stab + 1, dtype=np.float64)
            for j, stab in enumerate(stabs):
                eng.rho = rho1.clone()
                marg[j] = eng.project_stabilizer(stab, 1, regime.b, regime.arm)
            eng.rho = rho1.clone()
            _, p1 = eng.logical_distribution()
            marg[n_stab] = float(p1)  # the logical-flip rate (last entry; matches emitted DETECTOR_MARG)
            eng.rho = rho1
            return AnchorValue(statistic, regime, marg, Exactness.EXACT, 0.0, "a", prov)

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
