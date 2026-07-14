from __future__ import annotations

"""Certification interface — the value types + the ``Anchor`` port (step 1 of ``audit.certify``).

This evaluator-side seam scores a controlled noise process's emitted
records (or the scalable carrier that produces them) against INDEPENDENT GROUND-TRUTH ANCHORS and
returns an epistemic ledger. It graduates into one deep module the carrier↔DM↔closed-form
cross-checks that were re-wired ad hoc across ``outputs/teacher_prereg/`` (the de-facto
``p7e_carrier_cert_common`` + the stim slice in ``twin_xzzx_teacher`` + the closed-form anchors in
``mechanisms``/``hardware``).

DESIGN (locked). A common-caller spine (neutral spelling ``certify_noise_process``;
historical spelling ``certify_teacher``) over an ``Anchor`` capability-descriptor PORT
(this file) — the SAME Protocol shape as
``audit.floor_backend.PathJointEvaluator``: the certify core is BLIND to whether a DM oracle, a stim
Clifford slice, or a closed-form identity answered. The port carries a *capability descriptor* so
OOM-routing is DATA, not branching — an anchor that would OOM reports ``feasible=False`` and the core
routes to the carrier-MCWF for scale, never allocating the infeasible density matrix. Closed-form
identities ride as an analytic SIDECAR (the ``SCALAR_FUNC`` statistic), not as peers in the
distributional comparison — they answer cells the DM/stim anchors cannot, and never compete for the
same cell.

INVARIANTS this interface encodes (the prevent-toy + epistemic discipline, CLAUDE.md):
  * NEGATIVE CONTROLS ARE FIRST-CLASS (the ``Control`` port): a certification with no falsifier is
    rejected; an inert control (one that fails to fire) forces the verdict to FAIL — "a check that
    can't fail is vacuous", made structural.
  * FEASIBILITY IS DATA (``Capability.feasible`` + ``mem_bytes_estimate``): the core checks it
    BEFORE calling an anchor, so the DM-for-anchor / MCWF-for-scale split never OOMs.
  * INDEPENDENCE (``Anchor.independence``): an anchor's route must NOT share the carrier's
    implementation (anti-circular — a check vs the engine's own oracle is not an anchor).
  * EPISTEMIC LEDGER (``LedgerRow.epistemic_class``): every row is class (a) exact / (b) band /
    (c) gate (the METRICS.md ladder); the ledger is the test surface.

Evaluator-only: certification may read known process truth to score validity, but that truth never
enters emitted records. Pure value types + Protocols here — no GPU, no heavy imports; the concrete GPU /
stim / closed-form adapters arrive in later steps.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal, Protocol, runtime_checkable

#: The METRICS.md epistemic ladder, carried on every ledger row + anchor capability.
EpistemicClass = Literal["a", "b", "c"]  # (a) exact | (b) prediction-band | (c) heuristic gate


class Exactness(Enum):
    """How an anchor produces a statistic — sets the comparison band + the default epistemic class."""

    EXACT = "exact"              # enumeration / closed-form identity -> band 0, class (a)
    STATISTICAL = "statistical"  # Monte-Carlo, error ~ C/sqrt(N)     -> MC band, class (b)


class Statistic(Enum):
    """A certifiable quantity of the emitted record surface (seam-folded detectors + logical flip).

    The DM / stim anchors answer the distributional statistics (a process and an anchor compute the
    SAME statistic and are compared); ``SCALAR_FUNC`` is the closed-form analytic SIDECAR (a named
    identity an anchor asserts, with no distributional competitor)."""

    FULL_JOINT = "full_joint"        # P(s, f) over every (record, flip) cell        (R=1 gold GT)
    SYNDROME_DIST = "syndrome_dist"  # P(s) marginal                                 (Pauli-sliceable)
    DETECTOR_MARG = "detector_marg"  # per-(round,stab) detector on-rate + flip rate
    RR_CORR = "rr_corr"              # round-to-round detector correlation           (R>=2 moments)
    SPATIAL_CORR = "spatial_corr"    # same-round cross-detector correlation
    FLOOR = "floor"                  # the Bayes decoding floor F(R)
    SCALAR_FUNC = "scalar_func"      # a named closed-form functional (WG L1/L2/C_L, T-B lambda1, p_ij)


class Verdict(Enum):
    """A ledger row's (or the report's) outcome. PASS requires every (a)-exact row to pass AND every
    negative control to fire; a violated theorem or an inert control is FAIL."""

    PASS = "PASS"
    PASS_PROVISIONAL = "PASS*"   # exact rows pass + statistical rows within band; PROVISIONAL
    FINDING = "FINDING"          # a (b)-prediction missed — reportable, NOT a halt
    FAIL = "FAIL"                # an (a)-exact theorem violated OR a negative control went inert
    UNANCHORED = "UNANCHORED"    # no feasible anchor for this cell — an honest gap, never a crash
    CONTROL = "CONTROL"          # the row records a negative control (its ``value`` = did it fire)


@dataclass(frozen=True)
class Regime:
    """WHAT is certified + the feasibility coordinates that ROUTE anchors.

    ``register`` / ``n_active`` / ``R`` encode the DM feasibility wall the router reads: R=1 full-9q
    marginals feasible; small-register R>=2 feasible; R>=2 full-9q OOM -> the DM anchor reports
    ``feasible=False`` for the full joint and the carrier MCWF carries the scale."""

    R: int
    register: str = "full"               # "full" | "subregister" | an explicit sites tag
    n_active: int = 9                    # qutrits instantiated in the (sub)register (the OOM driver)
    arm: str = "A"                       # measurement-instrument arm (A/C/B1/B2)
    b: float = 1.0                       # leaked-readout bias (a swept nuisance)
    n_stab: int | None = None            # stabilizers per round (emitted width = R * n_stab)
    sites: tuple[int, ...] | None = None  # the active sub-register sites, when register != "full"


@dataclass(frozen=True)
class Feasibility:
    """An anchor's promise about whether it CAN answer a (statistic, regime) without OOM / timeout."""

    ok: bool
    reason: str = ""                       # WHY infeasible (e.g. "R>=2 full-9q: ~100GB copy stack")
    mem_bytes_estimate: int | None = None  # the bound arithmetic (declared, not silent)


@dataclass(frozen=True)
class Capability:
    """An anchor's routing promise for ONE (statistic, regime): feasible? exact-or-statistical?
    epistemic class? the memory bound? The core calls this BEFORE ``answer`` and skips an anchor
    whose ``feasible`` is False — so the OOM-avoidance is data-driven, not a try/except."""

    statistic: Statistic
    exactness: Exactness
    feasible: bool
    reason: str = ""
    epistemic_class: EpistemicClass = "a"
    mem_bytes_estimate: int | None = None


@dataclass(frozen=True)
class AnchorValue:
    """The ground-truth value of ONE statistic an anchor produced, with its honest band + provenance.

    INVARIANT: ``band == 0.0`` iff ``exactness is EXACT`` (an exact anchor has no sampling band; a
    statistical one carries the C/sqrt(N) scale). The core asserts this on ingest."""

    statistic: Statistic
    regime: Regime
    value: Any                     # scalar | {cell -> p} | {(r,j) -> q} | ndarray (per statistic)
    exactness: Exactness
    band: float                    # 0.0 for EXACT; the MC SE scale for STATISTICAL
    epistemic_class: EpistemicClass
    provenance: dict = field(default_factory=dict)  # anchor name, independence, N, prune, dropped_mass


@dataclass(frozen=True)
class LedgerRow:
    """One (anchor, statistic) outcome — the unit of the epistemic ledger (the test surface)."""

    anchor: str | None                # None for an UNANCHORED cell
    statistic: Statistic
    value: float                      # the carrier-vs-anchor distance (TV / worst-z / |Δ|)
    band: tuple[float, float] | None  # the acceptance interval (None for exact zero-tolerance)
    epistemic_class: EpistemicClass
    verdict: Verdict
    detail: dict = field(default_factory=dict)  # per-detector worst, z, dropped_mass, control-fired


@dataclass(frozen=True)
class CertReport:
    """The epistemic ledger + the single headline certification verdict.

    INVARIANTS:
      * ``verdict == PASS`` ⟹ every (a)-exact row passed AND every control fired. A passing report
        with an inert control is impossible — the core's verdict roll-up downgrades it to FAIL.
      * ``routing`` names the anchor actually used per (statistic, regime) + WHY (feasibility), so a
        reader audits the DM-for-anchor / MCWF-for-scale routing without rerunning.
      * ``truth`` is evaluator-only process truth — returned separately, never emitted (isolation)."""

    verdict: Verdict
    rows: tuple[LedgerRow, ...]
    controls: tuple[LedgerRow, ...]
    routing: dict
    truth: dict = field(default_factory=dict)
    provenance: dict = field(default_factory=dict)

    def row(self, anchor: str, statistic: Statistic) -> LedgerRow | None:
        """The ledger row for one (anchor, statistic), or None."""
        for r in self.rows:
            if r.anchor == anchor and r.statistic == statistic:
                return r
        return None

    def summary(self) -> str:
        """A scannable PASS/FAIL table + the verdict line (callers print this as the evidence)."""
        lines = [f"=== certify: {self.verdict.value} ==="]
        for r in (*self.rows, *self.controls):
            band = "" if r.band is None else f" band=({r.band[0]:.4g},{r.band[1]:.4g})"
            lines.append(
                f"  [{r.verdict.value:<11}] {(r.anchor or '-'):<16} {r.statistic.value:<14} "
                f"= {r.value:.5g}{band} ({r.epistemic_class})")
        return "\n".join(lines)

    def assert_pass(self) -> None:
        """Raise unless the verdict is PASS or PASS_PROVISIONAL (the scripted-execution gate)."""
        if self.verdict not in (Verdict.PASS, Verdict.PASS_PROVISIONAL):
            raise AssertionError(f"certify verdict is {self.verdict.value}, not PASS:\n{self.summary()}")


# =========================================================================== #
# The Anchor PORT — the internal seam (mirrors audit.floor_backend.PathJointEvaluator).             #
# Two real adapters minimum (DM oracle + stim Clifford + closed-form sidecar) justify the port      #
# (the two-adapters rule). The certify core talks ONLY to this Protocol — blind to the concrete     #
# ground-truth route.                                                                               #
# =========================================================================== #
@runtime_checkable
class Anchor(Protocol):
    """An INDEPENDENT ground-truth source for record statistics. The certify core asks it (1) what it
    ``answers``, (2) whether it ``capability``-can answer a (statistic, regime) without OOM, and only
    then (3) for the ``answer``. The core never inspects HOW the answer was produced.

    CONTRACT every concrete anchor must satisfy (the FAITHFULNESS rule-I surface):
      * INDEPENDENCE — ``independence`` documents the route (raw ``.stim`` / a closed-form identity /
        a DM enumeration that is a DIFFERENT object than the MPS carrier). A check vs the engine's
        own oracle is NOT an anchor.
      * EXACTNESS DECLARED — every ``AnchorValue`` is EXACT (band 0, class 'a') or STATISTICAL
        (band = the C/sqrt(N) scale, class 'b'); never an undeclared point estimate.
      * FEASIBILITY HONEST — ``capability(stat, regime).feasible`` is True only if ``answer`` will
        return without OOM at that regime; the bound is in ``mem_bytes_estimate``. An anchor that
        would OOM MUST report feasible=False (so the core routes to scale), never attempt-and-crash.
      * STATISTIC-SCOPED — ``answers()`` lists exactly the statistics this anchor can ever produce;
        the core asks nothing else of it.
    """

    name: str
    independence: str

    def answers(self) -> frozenset[Statistic]:
        """The statistics this anchor can EVER produce (regime-independent capability set)."""
        ...

    def capability(self, statistic: Statistic, regime: Regime) -> Capability:
        """The routing promise for (statistic, regime). Called BEFORE ``answer``; the core skips the
        anchor where ``.feasible`` is False. This is how the port says 'I can't answer this regime' —
        as DATA, not an exception."""
        ...

    def answer(self, teacher: ControlledNoiseProcess, statistic: Statistic, regime: Regime,
               *, N: int | None = None, generator: Any | None = None,
               corrupt: dict | None = None) -> AnchorValue:
        """Produce the ground-truth ``statistic`` at ``regime`` for ``teacher``'s known mechanism.
        PRECONDITION: the caller checked ``capability(statistic, regime).feasible`` (the core
        enforces this). Reads ``teacher.sched`` / ``teacher.channels()`` / ``teacher.truth``.

        ``corrupt`` (optional) is a NEGATIVE-CONTROL perturbation a ``Control`` injects so the
        comparison's teeth can be verified — e.g. ``{"stab": j}`` flips stabilizer ``j``'s X<->Z
        support, so the corrupted ground truth must FAIL to match the carrier (the corrupt-stabilizer
        control). An anchor that cannot host a given corruption ignores it (the control then records
        itself inert -> the verdict FAILs, per the genuine-check rule).

        An anchor MAY ALSO expose an OPTIONAL ``emit_kind() -> str`` method declaring which teacher
        VIEW it compares against: ``"full"`` (the real mechanism — the DM anchor) or
        ``"clifford_slice"`` (a Pauli/Clifford slice of the geometry — the stim anchor's
        implementation-independent wiring check). The core reads it via ``hasattr`` and defaults to
        ``"full"``; it is deliberately NOT a required Protocol method so a full-view-only anchor need
        not implement it."""
        ...


@runtime_checkable
class Control(Protocol):
    """A FIRST-CLASS negative control (corrupt-stabilizer, shuffle-label, broken-offset). The core
    runs every control that ``guards`` a statistic BEFORE the positive row, and an ``expect`` that
    does NOT happen forces the verdict to FAIL — the anti-vacuous-check rule, made structural.

    A control is not optional: ``certify_teacher`` with no attachable control for a statistic is a
    configuration error (a certification with no falsifier is rejected by construction)."""

    name: str

    def guards(self, statistic: Statistic) -> bool:
        """Does this control guard ``statistic``? (the core attaches it to those rows)."""
        ...

    def expect(self) -> Literal["must_fail", "must_separate"]:
        """What must happen for the control to FIRE — the positive row is trusted only if it does."""
        ...

    def run(self, ctx: Any, statistic: Statistic, regime: Regime, *, N: int | None = None) -> LedgerRow:
        """Run the control via the core's measurement context ``ctx`` (perturb the anchor or the
        emitted surface, re-measure, assert the ``expect``) -> a CONTROL ledger row recording whether
        it fired. (``ctx`` is the core's measurement façade — defined with the core in step 2.)"""
        ...


@runtime_checkable
class ControlledNoiseProcess(Protocol):
    """What certification needs from a controlled process: a way to emit records, the parsed
    geometry, the per-CZ channel field (for the channel-level anchors), and the evaluator-only known
    truth. Historical fixtures under ``outputs/teacher_prereg`` satisfy this via a thin adapter."""

    @property
    def sched(self) -> Any:
        """The parsed XZZX schedule (geometry + stabilizers + logical + the seam fold + Y-echo)."""
        ...

    @property
    def truth(self) -> dict:
        """The evaluator-only recorded ground truth (theta, gamma, leak params, mechanism Kraus...)."""
        ...

    def emit(self, regime: Regime, *, m: int, N: int, seed: int) -> Any:
        """Emit ``N`` shots at ``regime`` for logical prep ``m`` -> the seam surface (det, obs, packed)."""
        ...

    def channels(self) -> Any:
        """The per-CZ composite CPTP channel field (the minimal-Kraus list) — for channel anchors."""
        ...


@runtime_checkable
class DMReplayable(Protocol):
    """A process the DM-oracle anchor can replay on the density matrix: it builds the per-round
    mechanism callbacks the DM evolves through. A process satisfies BOTH ``ControlledNoiseProcess`` (for
    the carrier-emitted records) AND ``DMReplayable`` (for the DM ground truth) — the two
    representations of the SAME mechanism, which is what makes the DM↔carrier comparison a genuine
    cross-construction check (Gate-4), not a check vs the engine's own oracle."""

    def dm_round_callbacks(self, device: Any) -> tuple:
        """``(round_pre, round_post)`` where ``round_pre(eng, r)`` applies round r's pre-measure
        mechanism (rx + the within-cycle H/X/LEAK stream with the composite leak) on ``eng.rho`` IN
        PLACE, and ``round_post(eng, r)`` the post-M frame (the transversal Y echo; the terminal round
        drops it). Mirrors the carrier's within-cycle schedule EXACTLY (so the DM record == the
        carrier's emitted surface up to sampling)."""
        ...


@runtime_checkable
class CliffordSliceable(Protocol):
    """A process the stim-Clifford anchor can certify: it can emit a PAULI/CLIFFORD slice of its own
    geometry (the mechanism set to ``theta=0, gamma=0`` + a per-round bit-flip ``X_ERROR(p_x)``), which
    stim — a SEPARATE Clifford simulator — reproduces exactly. The comparison certifies the
    geometry→record WIRING (the seam fold + the logical) against an implementation-INDEPENDENT
    reference, catching a shared bug in our own geometry/seam code that both the DM and the carrier
    would otherwise share."""

    def emit_clifford_slice(self, regime: Any, *, p_x: float, m: int, N: int, seed: int) -> dict:
        """Emit ``N`` shots of the Clifford (bit-flip ``X_ERROR(p_x)``) slice -> the seam surface
        ``{"det":..., "obs":...}`` — the SAME geometry + seam fold the full mechanism uses."""
        ...

# Backward-compat alias — "Teacher" retired in error_coupling_simulator; qec_twin keeps it (shim re-exports).
ControlledTeacher = ControlledNoiseProcess
