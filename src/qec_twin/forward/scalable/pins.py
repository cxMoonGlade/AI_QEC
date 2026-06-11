from __future__ import annotations

"""Carrier-side structural pins + error accounting (seam-test registration items
3, 7 and 8 -- the carrier-facing slice).

Every pin here is a cheap CALLABLE check labeled per the registration's
STRUCTURAL/EMERGENT split: a STRUCTURAL pin sits at a numerical floor and its
violation is a build bug; the seam residual is the EMERGENT side and lives in
:class:`CarrierErrorAccounting` as tier-3, functional-indexed ``B_carrier`` --
a measurement, never an assertion, and NEVER folded into ``eps_log``. S3 wires
these pins into the theorem-pin suite and scores the ledger; this module only
provides the machinery.

Pins provided (carrier side of registration item 7):
  * normalization + zero negative mass  (STRUCTURAL, float64 floor)
  * fixed point <= 1e-9 where registered  (STRUCTURAL; M3 machinery reused)
  * seam-reduction trace preservation  (STRUCTURAL; the composition rule's CPTP
    kernel is TP by construction -- the pin verifies the implementation)
  * T-A Pauli-ablation => R_k == 1  (STRUCTURAL: the Pauli twirl of any local
    field is unital-diagonal, the sharp T-B boundary pins its record chain)
  * unital-diagonal pin => R_k == 1  (STRUCTURAL; scope: unital-DIAGONAL fields
    -- the sharp boundary is about diagonal-record dynamics, a unital but
    non-diagonal (coherent) field is NOT covered and is not claimed)
  * zero-seam exactness  (STRUCTURAL, the build's load-bearing pin: with zero
    seam mass the composed law must equal the whole-strip forward/exact oracle
    to <= 1e-10 -- composition exact when there is nothing to approximate)
"""

from dataclasses import dataclass, field as dataclass_field

import torch

from qec_twin.forward.cptp_channel import tp_residual
from qec_twin.forward.exact.steady_state import (
    DEFAULT_BURN_IN,
    DEFAULT_FP_TOL,
    DEFAULT_MAX_BURN_IN,
    diagonal_markov_pair,
    fixed_point_residual,
)
from qec_twin.forward.scalable.composed import (
    StripLaw,
    StripObservations,
    seam_conditional_reduction,
    strip_law_total_variation,
)
from qec_twin.forward.scalable.marginals import r_det_lag

# Pure channel utility (the exact Pauli twirl of a Kraus stack); imports no
# teacher state/parameters -- isolation contract intact.
from qec_twin.mechanisms.teachers import pauli_twirl_kraus


# --------------------------------------------------------------------------- #
# STRUCTURAL pins                                                               #
# --------------------------------------------------------------------------- #
def normalization_pin(law: StripLaw, *, tol: float = 1e-12) -> dict[str, object]:
    """STRUCTURAL: each window law sums to 1 within float64 round-off."""
    defect_l, defect_r = law.normalization_defect()
    return {
        "defect_left": defect_l,
        "defect_right": defect_r,
        "tol": float(tol),
        "ok": defect_l <= tol and defect_r <= tol,
    }


def nonpositive_pin(law: StripLaw, *, tol: float = 1e-12) -> dict[str, object]:
    """STRUCTURAL: zero negative probability mass beyond float64 round-off.

    Exact structural zeros (unreachable records) are legal law entries; the pin
    counts entries below ``-tol`` (build bug) and reports the minimum entry."""
    min_l = float(law.left.probs.min())
    min_r = float(law.right.probs.min())
    num_negative = int((law.left.probs < -tol).sum()) + int((law.right.probs < -tol).sum())
    return {
        "min_left": min_l,
        "min_right": min_r,
        "num_negative": num_negative,
        "tol": float(tol),
        "ok": num_negative == 0,
    }


def fixed_point_pin(
    channel_field,
    *,
    distance: int,
    tol: float = DEFAULT_FP_TOL,
    burn_in: int = DEFAULT_BURN_IN,
    max_burn_in: int = DEFAULT_MAX_BURN_IN,
    device: str | torch.device = "cpu",
) -> dict[str, object]:
    """STRUCTURAL (where registered): window stationary state reaches
    ``||rho_B - Phi(rho_B)||_1 <= 1e-9`` under the registered doubling schedule
    (the M3 machinery, reused verbatim)."""
    residual, rounds_used = fixed_point_residual(
        channel_field, distance=distance, burn_in=burn_in, max_burn_in=max_burn_in, tol=tol, device=device
    )
    return {"residual": residual, "rounds_used": rounds_used, "tol": float(tol), "ok": residual <= tol}


def seam_reduction_tp_pin(
    seam_kraus: torch.Tensor, partner_sigma: torch.Tensor, *, tol: float = 1e-12
) -> dict[str, object]:
    """STRUCTURAL: both conditional reductions of the seam slot are trace
    preserving (the composition rule's CPTP-by-construction kernel)."""
    res_l = float(tp_residual(seam_conditional_reduction(seam_kraus, partner_sigma, side="left")))
    res_r = float(tp_residual(seam_conditional_reduction(seam_kraus, partner_sigma, side="right")))
    return {
        "tp_residual_left": res_l,
        "tp_residual_right": res_r,
        "tol": float(tol),
        "ok": res_l <= tol and res_r <= tol,
    }


def pauli_ablation_pin(
    channel_field,
    *,
    distance: int,
    check: int = 0,
    lags: tuple[int, ...] = (1, 2, 3),
    tol: float = 1e-9,
    device: str | torch.device = "cpu",
) -> dict[str, object]:
    """STRUCTURAL (T-A in-carrier, checklist item 22): the Pauli-restricted
    ablation of the carrier's local field pins ``R_k == 1`` at every lag.

    The ablation is channel-level (each location's Kraus stack replaced by its
    exact Pauli twirl), never a parameter edit."""
    n = int(distance)
    twirled = [
        pauli_twirl_kraus(channel_field(0, i)) if channel_field(0, i) is not None else None
        for i in range(n)
    ]
    ablated = lambda t, i: twirled[i]  # noqa: E731
    r_by_lag = {
        int(k): r_det_lag(ablated, distance=n, check=check, lag=int(k), device=device)["R_k"]
        for k in lags
    }
    max_dev = max(abs(v - 1.0) for v in r_by_lag.values())
    return {"R_k": r_by_lag, "max_abs_deviation": max_dev, "tol": float(tol), "ok": max_dev <= tol}


def unital_diagonal_pin(
    channel_field,
    *,
    distance: int,
    check: int = 0,
    lags: tuple[int, ...] = (1, 2, 3),
    tol: float = 1e-9,
    class_tol: float = 1e-12,
    device: str | torch.device = "cpu",
) -> dict[str, object]:
    """STRUCTURAL (sharp T-B boundary): a unital-DIAGONAL local field has
    ``p01 == p10`` per location, and its record chain pins ``R_k == 1``.

    First verifies the field is in scope (``|p01 - p10| <= class_tol`` at every
    location -- the pin is NOT claimed for unital non-diagonal/coherent fields),
    then checks the carrier-law ``R_k``."""
    n = int(distance)
    asym = 0.0
    for i in range(n):
        kraus = channel_field(0, i)
        if kraus is None:
            continue
        p01, p10 = diagonal_markov_pair(kraus)
        asym = max(asym, abs(float(p01) - float(p10)))
    in_scope = asym <= class_tol
    r_by_lag = {
        int(k): r_det_lag(channel_field, distance=n, check=check, lag=int(k), device=device)["R_k"]
        for k in lags
    }
    max_dev = max(abs(v - 1.0) for v in r_by_lag.values())
    return {
        "markov_asymmetry": asym,
        "in_scope": in_scope,
        "R_k": r_by_lag,
        "max_abs_deviation": max_dev,
        "tol": float(tol),
        "ok": in_scope and max_dev <= tol,
    }


def zero_seam_exactness_pin(
    law: StripLaw, oracle_observations: StripObservations, *, tol: float = 1e-10
) -> dict[str, object]:
    """STRUCTURAL (the load-bearing pin): with zero seam mass, the composed law
    equals the whole-strip ``forward/exact`` oracle joint cell-by-cell.

    ``oracle_observations`` is the evaluator-side exact strip joint (grouped by
    the declared per-window codes); the pin scores max-abs cell gap and TV, both
    required ``<= tol``."""
    gap = strip_law_total_variation(law, oracle_observations)
    return {**gap, "tol": float(tol), "ok": gap["max_abs"] <= tol and gap["tv"] <= tol}


# --------------------------------------------------------------------------- #
# Error accounting: eps_log (tier 2) vs B_carrier (tier 3) -- never merged      #
# --------------------------------------------------------------------------- #
@dataclass
class SeamResidualRecord:
    """One functional-indexed ``B_carrier`` entry (tier-3 ``B_misspec``).

    ``functional`` names the registered functional (fiber-constant discipline is
    the registration's, carried by name); ``value`` is the measured carrier-vs-
    oracle residual on it; ``note`` carries scope (context, phi, basis)."""

    functional: str
    context_label: str
    value: float
    note: str = ""
    tier: str = "B_misspec(tier-3, functional-indexed)"


@dataclass
class EpsLogRecord:
    """One ``eps_log`` entry: float64 round-off ONLY (tier-2 evaluator error).

    The carrier's declared evaluator class is exact-enumeration float64, so the
    only legal entries are measured round-off proxies (normalization defect,
    TP residual)."""

    name: str
    context_label: str
    value: float


@dataclass
class CarrierErrorAccounting:
    """The carrier arm's error ledger (registration items 3 and 8).

    Two SEPARATE books with no combining operation anywhere in this class (by
    construction): ``eps_log`` records are float64 round-off only; ``b_carrier``
    records are the measured seam residuals -- tier-3 model-class
    misspecification, functional-indexed, priced or abstained by S3's scoring,
    NEVER convertible into an ``eps_log``."""

    eps_log: list[EpsLogRecord] = dataclass_field(default_factory=list)
    b_carrier: list[SeamResidualRecord] = dataclass_field(default_factory=list)

    def record_eps_log(self, name: str, context_label: str, value: float) -> EpsLogRecord:
        rec = EpsLogRecord(name=name, context_label=context_label, value=float(value))
        self.eps_log.append(rec)
        return rec

    def record_law_round_off(self, law: StripLaw) -> None:
        """Convenience: log a strip law's measured normalization defects."""
        defect_l, defect_r = law.normalization_defect()
        self.record_eps_log("normalization_defect_left", law.context.label, defect_l)
        self.record_eps_log("normalization_defect_right", law.context.label, defect_r)

    def record_seam_residual(
        self, functional: str, context_label: str, value: float, *, note: str = ""
    ) -> SeamResidualRecord:
        rec = SeamResidualRecord(
            functional=str(functional), context_label=str(context_label), value=float(value), note=str(note)
        )
        self.b_carrier.append(rec)
        return rec

    def report(self) -> dict[str, object]:
        """The two books, under separate keys -- the only export shape."""
        return {
            "eps_log": [vars(r) for r in self.eps_log],
            "B_carrier": [vars(r) for r in self.b_carrier],
            "convention": "eps_log = float64 round-off only; B_carrier = tier-3 "
            "functional-indexed seam residual; never folded together",
        }
