from __future__ import annotations

"""The closed-form anchor — the analytic SIDECAR (the ④ honest catch).

The DM and stim anchors compare DISTRIBUTIONS over the same cell and compete to answer it. The
closed-form anchor does NOT: it predicts a named functional from EXACT classical propagation (no
simulator at all), answering the cell the others can't — the R≥2 round-to-round detector correlation
(``RR_CORR``) of the non-unital channel, which the DM cannot reach at full-9q R≥2 (OOM) and stim
cannot reach (Clifford-only, no leakage/non-Markovian memory).

TRANSIENT, NOT STATIONARY (the step-5b correction). The record chain is PREPARED in ``|0>`` and the
channel acts each round, so the measured two-state chain ``s_0, s_1, …`` is TRANSIENT — its occupation
relaxes ``a_r → a_∞`` only as ``r → ∞``, which the finite-R engine never reaches. The earlier anchor
wrapped ``markov_flip_cov`` — documented as the *stationary* flip autocovariance — so it predicted the
``r → ∞`` limit and DISAGREED with the engine's transient. This anchor instead propagates the chain
EXACTLY from the prepared state. (The transient's per-round SHAPE is regime-dependent: for a low-rate
member like ``(0.08, 0.20)`` ``|corr|`` relaxes monotonically toward — and stays above — the stationary
value, but for other ``(p01, p10)`` the SIGNED correlation can change sign and ``|corr|`` is
non-monotone / can dip below stationary; do not read the monotone case as general.)

Two independent computations live here, and their agreement (in ``tests/test_certify.py`` and
``outputs/teacher_prereg/certify_closed_form_5b.py``) is a non-circular cross-check:
  * ``answer`` / ``_exact_rr_corr`` — the GROUND TRUTH: EXACT classical propagation of the two-state
    chain (the (u, v, w) triple-joint, enumerated; NO sampling, NO stationarity, NO flip-flip algebra).
    Handles the raw first detector ``d_0 = s_0`` uniformly via ``s_{-1} ≡ 0``;
  * ``predict_sequence`` — the analytic THEOREM (the flip-flip identity ``E[d_r d_{r+1}] = p01 p10``
    EXACTLY, the transient cancelling; ``E[d_r] = p01 + a_{r-1}(p10 - p01)``), for ``r ≥ 1``.
The two are computed DIFFERENTLY (brute-force joint vs the analytic identity); their match validates
the identity, and BOTH are independent of the quantum engine the 5b check validates.

The prediction is class (a) EXACT for a single-qubit two-state Markov record chain (the embedded
classical channel keeps the density matrix diagonal, so the quantum engine reproduces the classical
chain to machine precision), and an honest class (b) PREDICTION for the d3 detector correlation — the
XZZX geometry + the seam fold perturb the per-qubit form. The class is DECLARED, never inflated.

It is ``emit_kind() == "nonunital_slice"`` (the teacher emits the amp-damp/non-unital-isolated slice
at R≥2). Pure / host-side (a 3×3 stochastic propagation).
"""

import numpy as np

from ..types import AnchorValue, Capability, Exactness, Regime, Statistic


class ClosedFormAnchor:
    """Predicts the non-unital round-to-round detector correlation by EXACT classical propagation of
    the two-state Markov chain (TRANSIENT, prepared in ``|0>``). Configured with the non-unital Markov
    pair ``(p01, p10)`` (for amp-damp(γ): ``(0, γ)`` — the degenerate absorbing member, predicting ~0;
    for the T-B member: the registered pair). ``a0`` is the occupation ``P(s_0 = 1)`` AFTER the first
    channel on the prepared ``|0>`` — ``p01`` by the engine's channel-before-first-measurement
    convention. ``exact_single_qubit=True`` marks the single-qubit chain (class (a) exact); the default
    is the d3 PREDICTION (class (b))."""

    name = "closed_form_tb"
    independence = (
        "EXACT classical propagation of the two-state Markov chain (the transient prepared-state "
        "occupation + the detector triple-joint); no simulator at all — it shares no code path with "
        "the DM, the carrier, or stim")

    def __init__(self, *, p01: float, p10: float, exact_single_qubit: bool = False,
                 band_d3: float = 0.02, a0: float | None = None):
        self._p01 = float(p01)
        self._p10 = float(p10)
        self._exact = bool(exact_single_qubit)
        self._band_d3 = float(band_d3)
        # P(s_0 = 1) after the first channel on the prepared |0>; the engine applies the channel before
        # the first measurement, so a0 = p01 (TRANSIENT initial condition, not the stationary a_∞).
        self._a0 = float(self._p01 if a0 is None else a0)

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

    # ----------------------------------------------------------------------- #
    # the chain (transient, prepared-state)                                   #
    # ----------------------------------------------------------------------- #
    def _occupations(self, R: int) -> np.ndarray:
        """Transient occupation ``a_r = P(s_r = 1)``, ``r = 0..R-1``, from the prepared ``|0>``:
        ``a_0`` given, ``a_{r+1} = p01 + a_r (1 - p01 - p10)``. Relaxes to ``a_∞ = p01/(p01+p10)``."""
        a = np.empty(int(R), dtype=np.float64)
        a[0] = self._a0
        q = 1.0 - self._p01 - self._p10
        for r in range(1, int(R)):
            a[r] = self._p01 + a[r - 1] * q
        return a

    def _exact_rr_corr(self, R: int) -> np.ndarray:
        """EXACT per-round detector correlation ``|Corr(d_r, d_{r+1})|``, ``r = 0..R-2``, by exact
        classical propagation of the two-state chain (NO sampling, NO stationarity, NO flip-flip
        algebra). ``d_r = s_{r-1} XOR s_r`` with ``s_{-1} = 0`` (the prepared ``|0>`` -> ``d_0 = s_0``).
        The GROUND TRUTH the quantum engine is certified against."""
        R = int(R)
        p01, p10 = self._p01, self._p10
        T = np.array([[1.0 - p01, p01], [p10, 1.0 - p10]])  # T[from, to]
        # pi_ext[k] = marginal of s_{k-1}; pi_ext[0] = P(s_{-1}) = (1, 0) (the prepared |0>).
        pi_ext = [np.array([1.0, 0.0])]
        for _ in range(R):
            pi_ext.append(pi_ext[-1] @ T)
        out = []
        for r in range(R - 1):
            pm = pi_ext[r]  # marginal of s_{r-1}
            e_dr = e_dr1 = e_both = 0.0
            for u in (0, 1):          # s_{r-1}
                for v in (0, 1):      # s_r
                    for w in (0, 1):  # s_{r+1}
                        p = pm[u] * T[u, v] * T[v, w]
                        dr, dr1 = u ^ v, v ^ w
                        e_dr += p * dr
                        e_dr1 += p * dr1
                        e_both += p * dr * dr1
            var_r, var_r1 = e_dr * (1.0 - e_dr), e_dr1 * (1.0 - e_dr1)
            if var_r > 1e-12 and var_r1 > 1e-12:
                out.append(abs((e_both - e_dr * e_dr1) / np.sqrt(var_r * var_r1)))
            else:
                out.append(0.0)
        return np.array(out, dtype=np.float64)

    def predict_sequence(self, R: int) -> np.ndarray:
        """The analytic THEOREM, ``r = 1..R-2`` (the flip-flip rounds): ``E[d_r d_{r+1}] = p01 p10``
        EXACTLY (the transient cancels under the Markov conditional independence ``s_{r-1} ⟂ s_{r+1} |
        s_r``), ``E[d_r] = p01 + a_{r-1}(p10 - p01)``. Computed DIFFERENTLY from ``_exact_rr_corr``
        (the closed-form identity vs the brute-force joint); their match validates the identity."""
        R = int(R)
        p01, p10 = self._p01, self._p10
        a = self._occupations(R)  # a[r] = P(s_r = 1)
        out = []
        for r in range(1, R - 1):
            e_dr = p01 + a[r - 1] * (p10 - p01)
            e_dr1 = p01 + a[r] * (p10 - p01)
            var_r, var_r1 = e_dr * (1.0 - e_dr), e_dr1 * (1.0 - e_dr1)
            if var_r > 1e-12 and var_r1 > 1e-12:
                out.append(abs((p01 * p10 - e_dr * e_dr1) / np.sqrt(var_r * var_r1)))
            else:
                out.append(0.0)
        return np.array(out, dtype=np.float64)

    def answer(self, teacher, statistic: Statistic, regime: Regime,
               *, N=None, generator=None, corrupt=None) -> AnchorValue:
        seq = self._exact_rr_corr(regime.R)  # per-round, r=0..R-2 (EXACT, transient)
        exness = Exactness.EXACT if self._exact else Exactness.STATISTICAL
        cls = "a" if self._exact else "b"
        band = 0.0 if self._exact else self._band_d3  # (b): the d3 geometry perturbs the per-qubit form
        return AnchorValue(statistic, regime, seq, exness, band, cls,
                           {"anchor": self.name, "p01": self._p01, "p10": self._p10, "a0": self._a0,
                            "exact_single_qubit": self._exact, "transient": True})
