from __future__ import annotations

"""The closed-form anchor — the analytic SIDECAR (the ④ honest catch).

The DM and stim anchors compare DISTRIBUTIONS over the same cell and compete to answer it. The
closed-form anchor does NOT: it predicts a named functional from a closed-form THEOREM (no simulator
at all), answering the cell the others can't — the R≥2 round-to-round detector correlation
(``RR_CORR``) of the non-unital channel, which the DM cannot reach at full-9q R≥2 (OOM) and stim
cannot reach (Clifford-only, no leakage/non-Markovian memory).

It WRAPS the existing wheels (``hardware.dem_compose.markov_flip_cov`` — the exact two-state Markov
flip autocovariance; the T-B chain in ``mechanisms.seam_teachers``) and reimplements no physics. The
prediction is class (a) EXACT for a single-qubit two-state Markov record chain (``markov_flip_cov`` is
an (a)-class identity, unit-tested in ``tests/test_carrier_seam_instrument.py``), and an honest
class (b) PREDICTION for the d3 detector correlation — the XZZX geometry + the seam fold perturb the
per-qubit closed form (the wheel-assessment caveat: the T-B closed form is exact on a rep-code / a
single qubit, approximate on the full XZZX). The class is DECLARED, never silently inflated.

It is ``emit_kind() == "nonunital_slice"`` (the teacher emits the amp-damp/non-unital-isolated slice
at R≥2). Pure / host-side (the closed forms are scalar).
"""

import numpy as np

from qec_twin.audit.certify.types import AnchorValue, Capability, Exactness, Regime, Statistic


class ClosedFormAnchor:
    """Predicts the non-unital round-to-round detector correlation via the two-state Markov closed
    form (wraps ``markov_flip_cov``). Configured with the non-unital Markov pair ``(p01, p10)`` (for
    amp-damp(γ): ``(0, γ)``; for the T-B member: the registered pair). ``exact_single_qubit=True`` marks
    the single-qubit chain (class (a) exact); the default is the d3 PREDICTION (class (b))."""

    name = "closed_form_tb"
    independence = (
        "a closed-form theorem (the two-state Markov flip autocovariance / T-B record chain); no "
        "simulator at all — it shares no code path with the DM, the carrier, or stim")

    def __init__(self, *, p01: float, p10: float, exact_single_qubit: bool = False, band_d3: float = 0.02):
        self._p01 = float(p01)
        self._p10 = float(p10)
        self._exact = bool(exact_single_qubit)
        self._band_d3 = float(band_d3)

    def emit_kind(self) -> str:
        return "nonunital_slice"

    def answers(self) -> frozenset[Statistic]:
        return frozenset({Statistic.RR_CORR})

    def capability(self, statistic: Statistic, regime: Regime) -> Capability:
        if statistic is not Statistic.RR_CORR or regime.R < 2:
            return Capability(statistic, Exactness.EXACT, False,
                              "the closed form predicts RR_CORR at R>=2 only", "a", 0)
        exness = Exactness.EXACT if self._exact else Exactness.STATISTICAL
        cls = "a" if self._exact else "b"
        return Capability(statistic, exness, True, "", cls, 0)

    def predict(self) -> float:
        """The closed-form mean |round-to-round detector correlation| for the two-state Markov pair:
        ``corr(d_r, d_{r+1}) = Cov / Var = markov_flip_cov(p01,p10,1) / (r·(1-r))`` with the flip rate
        ``r = 2·p01·p10/(p01+p10)``. (a)-class identity (a single-qubit record chain)."""
        from qec_twin.hardware.dem_compose import markov_flip_cov

        a, b = self._p01, self._p10
        if (a + b) <= 0:
            return 0.0
        r = 2.0 * a * b / (a + b)
        if not (0.0 < r < 1.0):
            return 0.0
        cov = float(markov_flip_cov(a, b, 1))  # the lag-1 flip autocovariance (the wheel)
        return abs(cov / (r * (1.0 - r)))

    def answer(self, teacher, statistic: Statistic, regime: Regime,
               *, N=None, generator=None, corrupt=None) -> AnchorValue:
        corr = self.predict()
        exness = Exactness.EXACT if self._exact else Exactness.STATISTICAL
        cls = "a" if self._exact else "b"
        band = 0.0 if self._exact else self._band_d3  # (b): the d3 geometry perturbs the per-qubit closed form
        return AnchorValue(statistic, regime, np.array([corr]), exness, band, cls,
                           {"anchor": self.name, "p01": self._p01, "p10": self._p10,
                            "exact_single_qubit": self._exact})
