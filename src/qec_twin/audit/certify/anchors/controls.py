from __future__ import annotations

"""First-class negative controls — the genuine-check teeth (do-not-fail-to-a-toy).

A control PERTURBS the comparison in a way that, if the carrier were correct, MUST be caught — and the
core's roll-up turns an inert control (one that fails to fire) into a FAIL. ``CorruptStabControl`` is
the canonical QEC control (it tests geometry sensitivity); ``ShuffleControl`` is a cheap generic
second falsifier.
"""

import numpy as np
from dataclasses import replace

from qec_twin.audit.certify.core import compare
from qec_twin.audit.certify.types import LedgerRow, Statistic, Verdict

_GEOM = (Statistic.FULL_JOINT, Statistic.SYNDROME_DIST, Statistic.DETECTOR_MARG)


class CorruptStabControl:
    """The canonical QEC negative control: flip a stabilizer's X<->Z support in the GROUND TRUTH (via
    ``ctx.corrupt_answer({"stab": j})``) → the (correct) emitted surface must FAIL to match (the
    corrupted geometry reads a different syndrome; the codestate is no longer its +1 eigenstate). This
    proves the comparison is SENSITIVE to the geometry — the geometric teeth. An anchor that cannot
    host the corruption returns the same answer → the control does NOT fire → the verdict FAILs (a
    check that can't fail is vacuous)."""

    name = "corrupt_stabilizer"

    def __init__(self, stab: int = 1):
        self._stab = int(stab)

    def guards(self, statistic):
        return statistic in _GEOM

    def expect(self):
        return "must_fail"

    def run(self, ctx, statistic, regime, *, N=None):
        corrupt_av = ctx.corrupt_answer({"stab": self._stab})
        _, _, verdict, _ = compare(statistic, ctx.emitted, corrupt_av, N=ctx.N)
        fired = verdict is Verdict.FAIL
        return LedgerRow(ctx.anchor.name, statistic, 1.0 if fired else 0.0, None, "c",
                         Verdict.CONTROL, {"fired": fired, "name": self.name, "stab": self._stab})


class ShuffleControl:
    """A generic teeth control: shuffle the GROUND-TRUTH value → the emitted must FAIL to match the
    shuffled GT. Weaker than the corrupt-stabilizer control (it does not exercise the geometry), but
    applies to any statistic and is a cheap second falsifier."""

    name = "shuffle"

    def guards(self, statistic):
        return True

    def expect(self):
        return "must_fail"

    def run(self, ctx, statistic, regime, *, N=None):
        shuffled = _shuffle_value(ctx.anchor_value)
        _, _, verdict, _ = compare(statistic, ctx.emitted, shuffled, N=ctx.N)
        fired = verdict is Verdict.FAIL
        return LedgerRow(ctx.anchor.name, statistic, 1.0 if fired else 0.0, None, "c",
                         Verdict.CONTROL, {"fired": fired, "name": self.name})


def _shuffle_value(av):
    """Roll the ground-truth value across its keys/elements (dict dist or array statistic)."""
    val = av.value
    if isinstance(val, dict):
        keys = sorted(val)
        vals = [val[k] for k in keys]
        return replace(av, value={k: vals[(i + 1) % len(vals)] for i, k in enumerate(keys)})
    return replace(av, value=np.roll(np.asarray(val), 1))
