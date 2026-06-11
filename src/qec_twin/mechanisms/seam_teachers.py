from __future__ import annotations

"""ADR 0008 C3 seam-test teachers (registration item 2; EVALUATOR-ONLY).

The controlled-teacher arms of the frozen SEAM-TEST pre-registration
(``docs/metric_results.md`` "ADR 0008 SEAM-TEST PRE-REGISTRATION", 2026-06-10;
skeleton: ``docs/.reports/adr0008_panel/R2_c3prep_verdict.md`` item 2; member
table: ``D_package_derivations.md`` D5). All results are
controlled-teacher-scoped -- no hardware claim of any kind issues from this
line.

Geometry (SEAM-TEST PRE-RUN AMENDMENT 1, ruling 1): the instrument is the
DISJOINT two-window strip -- the windows share the seam DATA pair across the
seam (one qubit each side) and NO check is measured on that pair. Every edge
teacher below acts on the unchecked seam data pair through the oracle's
declared edge slot (``SeamStrip.oracle_law`` passes
``edges=(strip.seam_pair,)``); nothing in this module depends on a seam check
existing, and the registered constants are unchanged by the amendment.

Isolation contract (``docs/teacher_learner.md``): every object here is
evaluator-side counterfactual ground truth. The teacher's channels, parameters
(``SeamTeacher.params``) and labels are used ONLY to *score* the carrier
(by S3, against the ``forward/exact`` oracle); they are never fed to the
learner/carrier, which consumes observations alone.

The arms (registration item 2 + the control variants):

(i)   :func:`coherent_seam_teacher` -- the M3-scale backdrop plus the coherent
      seam edge ``U_phi = exp(-i phi Z(x)Z)`` ON the strip's (unchecked) seam
      data pair at the H2
      placement (``[ (prod_i E_i) ; U_phi ]^repeats`` then extraction);
      ``phi_ref = 0.1``, regime ``[0.05, 0.15]``. Control:
      :func:`bias_injected_coherent_teacher` (checklist item 35: inject a known
      delta into phi; the scored functional must move by the predicted amount).
(ii)  :func:`tb_bunching_teacher` -- D5's explicit T-B member at
      ``r = 1.27e-2, R = 5``: a per-data-qubit time-constant non-unital CPTP
      channel whose Z record under per-round non-selective extraction is the
      two-state Markov flip chain ``(p01, p10) = (6.7039e-3, 1.20296e-1)``,
      ``lambda1 = 1 - p01 - p10 = 0.873``. Valid here per the R-MECH amendment
      scope: D5's T-B table holds for rep-code instruments and controlled-teacher
      seam tests (surface-window instruments need the T-C/asymmetric-q hooks).
(iii) :func:`backdrop_teacher` -- the M3-scale local backdrop: small iid local
      noise at ~1e-2 rates with declared constants. Declared composition:
      ``BitFlip(1e-2) . RX(0.2)`` per data qubit (coherent twirl rate
      ``sin^2(0.1) ~ 1e-2``). The coherent component is REQUIRED for the
      registered seam functionals to be non-degenerate: with a purely diagonal
      (Pauli-Z-basis) backdrop the state is diagonal at every pre_rotation=0
      context and both the coherent edge and its twirl act trivially on
      diagonals, so the registered phi^2 sandwich channel (P-c) would be
      exactly zero by construction.
(iv)  :func:`twirled_seam_teacher` -- the Pauli-twirled control of the seam
      edge: correlated dephasing ``{cos(phi) I4, sin(phi) Z(x)Z}`` at rate
      ``sin^2(phi)`` (P-b: the rate is visible, phi-sign/coherence exactly not).
(v)   :func:`pauli_ablation_teacher` -- the T-A ablation for the structural
      pins: the R = 1 member of the SAME T-B family at the matched record flip
      rate (``p01 = p10 = r`` => iid record flips, ``R_k == 1`` for every k,
      exactly).

Equal treatment (D8 / checklist item 7): every factory returns a
:class:`SeamTeacher`, which exposes the single observation surface
(``name`` / ``channel_field`` / ``edge_field``) consumed by
``SeamStrip.oracle_law`` -- all arms induce the identical declared block family.

Epistemic classes: the chain identities in :func:`tb_record_chain_stats` and
:func:`tb_member_from_rate_and_ratio` are (a)-class (D5 closed forms, verified
as unit-test identities in ``tests/test_carrier_seam_instrument.py``); the
declared constants below are (c)-class registered design values.
"""

import math
from dataclasses import dataclass, field
from typing import Any, Callable

import torch

from qec_twin.forward.cptp_channel import CDTYPE
from qec_twin.mechanisms.teachers import (
    coherent_overrotation_kraus,
    correlated_dephasing_kraus,
    zz_coupling_kraus,
)

# ----------------------------------------------------------------------------- #
# Registered constants ((c)-class design values, frozen with the registration)   #
# ----------------------------------------------------------------------------- #
#: Coherent seam edge reference angle and regime endpoints (registration item 2).
SEAM_PHI_REF = 0.1
SEAM_PHI_REGIME = (0.05, 0.15)

#: M3-scale iid local backdrop: per-data-qubit ``BitFlip(p) . RX(theta)``.
#: Both effective rates ~1e-2 (stochastic p; coherent twirl rate sin^2(theta/2)).
BACKDROP_FLIP_RATE = 1.0e-2
BACKDROP_ROTATION = 0.2

#: D5 T-B bunching member at r = 1.27e-2, R = 5 (the registered family rate /
#: bunching ratio / record-chain decay; (p01, p10) realize them to print
#: precision -- verified as (a)-class identities in the unit tests).
TB_P01 = 6.7039e-3
TB_P10 = 1.20296e-1
TB_FLIP_RATE = 1.27e-2
TB_BUNCHING_RATIO = 5.0
TB_LAMBDA1 = 0.873


# ----------------------------------------------------------------------------- #
# T-B member channel + (a)-class record-chain identities (D5)                     #
# ----------------------------------------------------------------------------- #
def tb_markov_kraus(p01: float, p10: float) -> torch.Tensor:
    """D5's explicit T-B member as a ``(3, 2, 2)`` Kraus stack.

    ``K0 = diag(sqrt(1-p01), sqrt(1-p10))``, ``K1 = sqrt(p01) |1><0|``,
    ``K2 = sqrt(p10) |0><1|`` -- a time-constant, NON-UNITAL single-qubit CPTP
    channel. On Z-basis populations it acts exactly as the two-state Markov
    transition ``0 -> 1`` w.p. ``p01``, ``1 -> 0`` w.p. ``p10``, so under
    per-round non-selective extraction the per-qubit Z record is the stationary
    two-state Markov flip chain with ``R_k = 1 + (R - 1) lambda1^{k-1}``,
    ``lambda1 = 1 - p01 - p10`` (D5 T-B theorem, (a)-class).
    """
    q01, q10 = float(p01), float(p10)
    k0 = torch.tensor(
        [[math.sqrt(1.0 - q01), 0.0], [0.0, math.sqrt(1.0 - q10)]], dtype=CDTYPE
    )
    k1 = torch.tensor([[0.0, 0.0], [math.sqrt(q01), 0.0]], dtype=CDTYPE)
    k2 = torch.tensor([[0.0, math.sqrt(q10)], [0.0, 0.0]], dtype=CDTYPE)
    return torch.stack([k0, k1, k2])


def tb_record_chain_stats(p01: float, p10: float) -> dict[str, float]:
    """(a)-class closed-form stationary record-chain functionals (D5 identities).

    ``r = 2 p01 p10 / (p01 + p10)`` (stationary flip rate),
    ``R = (p01 + p10)^2 / (4 p01 p10)`` (lag-1 bunching ratio ``P(FF)/r^2``),
    ``lambda1 = 1 - p01 - p10`` (record-chain decay; the T-B-pinned rate),
    ``T3 = R`` (the consecutive-triple pin: T-B predicts ``P(FFF)/r^3 = R``
    exactly -- renewal after two flips).
    """
    q01, q10 = float(p01), float(p10)
    s = q01 + q10
    r = 2.0 * q01 * q10 / s
    ratio = s * s / (4.0 * q01 * q10)
    return {"r": r, "R": ratio, "lambda1": 1.0 - s, "T3": ratio}


def tb_member_from_rate_and_ratio(r: float, ratio: float) -> tuple[float, float]:
    """D5 inversion ``{p01, p10} = r R (1 +/- sqrt(1 - 1/R))`` (unordered, Z2 gauge).

    Returns the pair sorted ascending (the unordered-fiber convention: which
    member is ``p01`` is the registered Z2 gauge).
    """
    rr = float(r) * float(ratio)
    root = math.sqrt(1.0 - 1.0 / float(ratio)) if float(ratio) > 1.0 else 0.0
    return (rr * (1.0 - root), rr * (1.0 + root))


# ----------------------------------------------------------------------------- #
# The equal-treatment teacher object (D8)                                         #
# ----------------------------------------------------------------------------- #
@dataclass(frozen=True)
class SeamTeacher:
    """One evaluator-only teacher arm exposing the D8 observation surface.

    ``channel_field`` is ``(t, i) -> (k, 2, 2) Kraus | None`` (per-data-location
    storage mechanism); ``edge_field`` is ``None`` or
    ``(t, (i, j)) -> (k, 4, 4) Kraus | None`` evaluated on the strip's declared
    seam pair at the H2 placement. ``params`` records the declared ground-truth
    constants -- EVALUATOR/AUDIT-SIDE ONLY (isolation contract): they are never
    a learner/carrier input; an undeclared crossing voids the affected fits
    (checklist item 28).
    """

    name: str
    channel_field: Callable
    edge_field: Callable | None
    params: dict[str, Any] = field(default_factory=dict)


def _const_field(kraus: torch.Tensor) -> Callable:
    return lambda t, i: kraus


def _edge_on(pair, kraus: torch.Tensor) -> Callable:
    target = tuple(pair)
    return lambda t, e: kraus if tuple(e) == target else None


def backdrop_kraus() -> torch.Tensor:
    """The declared M3-scale backdrop channel ``BitFlip(1e-2) . RX(0.2)``."""
    return coherent_overrotation_kraus(BACKDROP_FLIP_RATE, BACKDROP_ROTATION)


def _backdrop_params() -> dict[str, Any]:
    return {
        "backdrop_flip_rate": BACKDROP_FLIP_RATE,
        "backdrop_rotation": BACKDROP_ROTATION,
        "backdrop_coherent_rate": math.sin(BACKDROP_ROTATION / 2.0) ** 2,
    }


# ----------------------------------------------------------------------------- #
# Teacher factories (registration item 2 arms)                                    #
# ----------------------------------------------------------------------------- #
def backdrop_teacher(strip) -> SeamTeacher:
    """(iii) M3-scale local backdrop: iid ``BitFlip(1e-2) . RX(0.2)``, no edge."""
    return SeamTeacher(
        name="seam-backdrop",
        channel_field=_const_field(backdrop_kraus()),
        edge_field=None,
        params={**_backdrop_params(), "seam_pair": tuple(strip.seam_pair)},
    )


def coherent_seam_teacher(strip, phi: float = SEAM_PHI_REF) -> SeamTeacher:
    """(i) Backdrop + coherent seam edge ``exp(-i phi Z(x)Z)`` on the seam pair.

    H2 placement: the edge applies once per repeat AFTER that pass's location
    channels (``[ (prod_i E_i) ; U_phi ]^repeats`` then extraction) -- the
    placement is realized by ``forward/exact`` and declared, never commuted.
    """
    return SeamTeacher(
        name=f"seam-coherent(phi={float(phi):+.6g})",
        channel_field=_const_field(backdrop_kraus()),
        edge_field=_edge_on(strip.seam_pair, zz_coupling_kraus(float(phi))),
        params={
            **_backdrop_params(),
            "phi": float(phi),
            "phi_ref": SEAM_PHI_REF,
            "phi_regime": SEAM_PHI_REGIME,
            "seam_pair": tuple(strip.seam_pair),
        },
    )


def bias_injected_coherent_teacher(strip, *, delta: float, phi: float = SEAM_PHI_REF) -> SeamTeacher:
    """(i-control) Bias-injection control for the coherent teacher.

    Checklist item 35 pattern: inject a KNOWN declared delta into the coherent
    parameter (``phi -> phi + delta``); the evaluator then checks the scored
    functional (B_LER) moves by the amount predicted from the oracle. ``delta``
    is required and recorded -- its run value is the scorer's (S3) declared
    choice, not a constant of this module.
    """
    injected = float(phi) + float(delta)
    return SeamTeacher(
        name=f"seam-coherent-bias(phi={float(phi):+.6g},delta={float(delta):+.6g})",
        channel_field=_const_field(backdrop_kraus()),
        edge_field=_edge_on(strip.seam_pair, zz_coupling_kraus(injected)),
        params={
            **_backdrop_params(),
            "phi": float(phi),
            "delta": float(delta),
            "phi_injected": injected,
            "seam_pair": tuple(strip.seam_pair),
        },
    )


def twirled_seam_teacher(strip, phi: float = SEAM_PHI_REF) -> SeamTeacher:
    """(iv) The Pauli-twirled control of the seam edge (P-b).

    Backdrop + correlated dephasing ``{cos(phi) I4, sin(phi) Z(x)Z}`` -- the
    exact two-qubit Pauli twirl of ``U_phi`` at correlated rate ``sin^2(phi)``.
    Its law must show the rate but exactly NO phi-sign/coherence sensitivity
    (the channel is even in phi by construction).
    """
    return SeamTeacher(
        name=f"seam-twirled(phi={float(phi):+.6g})",
        channel_field=_const_field(backdrop_kraus()),
        edge_field=_edge_on(strip.seam_pair, correlated_dephasing_kraus(float(phi))),
        params={
            **_backdrop_params(),
            "phi": float(phi),
            "twirl_rate": math.sin(float(phi)) ** 2,
            "seam_pair": tuple(strip.seam_pair),
        },
    )


def tb_bunching_teacher(strip) -> SeamTeacher:
    """(ii) The D5 T-B bunching member at ``r = 1.27e-2, R = 5`` on every data qubit.

    Time-constant per-data-qubit non-unital CPTP field; no edge. The carrier's
    recovered ``(r, R)`` (P-d) and the no-fit two-block ``R_det`` pin
    (registration item 6) are scored against the registered chain values.
    """
    stats = tb_record_chain_stats(TB_P01, TB_P10)
    return SeamTeacher(
        name="seam-bunching-TB(R=5)",
        channel_field=_const_field(tb_markov_kraus(TB_P01, TB_P10)),
        edge_field=None,
        params={
            "p01": TB_P01,
            "p10": TB_P10,
            "r": stats["r"],
            "R": stats["R"],
            "lambda1": stats["lambda1"],
            "T3": stats["T3"],
            "registered": {
                "r": TB_FLIP_RATE,
                "R": TB_BUNCHING_RATIO,
                "lambda1": TB_LAMBDA1,
            },
        },
    )


def pauli_ablation_teacher(strip) -> SeamTeacher:
    """(v) The T-A Pauli-ablation variant for the structural pins (R = 1).

    The R = 1 member of the SAME T-B family at the matched registered record
    flip rate: ``p01 = p10 = r`` makes the per-step flip probability
    state-independent, so the record is exactly iid (``R_k == 1`` for every k,
    ``P(FF) = r^2`` -- T-A in-family; checklist item 22's teacher side).
    """
    q = TB_FLIP_RATE
    stats = tb_record_chain_stats(q, q)
    return SeamTeacher(
        name="seam-pauli-ablation-TA(R=1)",
        channel_field=_const_field(tb_markov_kraus(q, q)),
        edge_field=None,
        params={"p01": q, "p10": q, "r": stats["r"], "R": stats["R"], "lambda1": stats["lambda1"]},
    )


def seam_teacher_arms(
    strip,
    *,
    phi: float = SEAM_PHI_REF,
    bias_delta: float | None = None,
) -> dict[str, SeamTeacher]:
    """The full equal-treatment roster (D8): every registered arm, one surface.

    Returns the five item-2 arms (backdrop, coherent, twirled control, T-B
    bunching, T-A ablation); the bias-injection control is included when
    ``bias_delta`` is declared.
    """
    arms = {
        "backdrop": backdrop_teacher(strip),
        "coherent": coherent_seam_teacher(strip, phi=phi),
        "twirled": twirled_seam_teacher(strip, phi=phi),
        "bunching": tb_bunching_teacher(strip),
        "ablation": pauli_ablation_teacher(strip),
    }
    if bias_delta is not None:
        arms["bias"] = bias_injected_coherent_teacher(strip, delta=bias_delta, phi=phi)
    return arms
