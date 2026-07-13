from __future__ import annotations

"""The certify CORE — route → controls-first → score → ledger; blind to concrete anchors.

The core orchestrates the ``Anchor`` / ``Control`` ports: it owns the statistical backbone (total
variation / band / null-subtraction) and the verdict roll-up, and is PURE PYTHON over the anchor /
teacher results. All GPU model-compute lives in the wheels the adapters wrap.

PERFORMANCE (zero-overhead abstraction — do-not-lose-performance):
  * ONE ``teacher.emit`` per (regime, m) — cached — feeds EVERY distributional statistic at that
    regime (the emitted records are computed once, not once per statistic);
  * each anchor is called once per cell; ``capability`` is cheap feasibility arithmetic (no compute);
  * the adapters DELEGATE to the validated wheels (``record_oracle``, the stim oracle, the closed
    forms) and never reimplement physics — the certify path is the wheel's cost + negligible host
    bookkeeping.

GENUINE CHECKS (do-not-fail-to-a-toy — made structural in ``_rollup``):
  * controls run BEFORE the positive row; an inert control (one that fails to FIRE) forces FAIL;
  * a broken carrier FAILs (the comparison has teeth; the core's own positive-control test proves it);
  * an infeasible cell is UNANCHORED, NEVER a silent PASS — the routing downgrade is recorded;
  * roll-up: PASS iff every (a)-exact row passed AND every control fired; any statistical-only row
    gives PASS_PROVISIONAL, never PASS (no inflation of a sampled result to "exact").
"""

import numpy as np

from .types import (
    Anchor,
    AnchorValue,
    CertReport,
    Control,
    ControlledNoiseProcess,
    Exactness,
    LedgerRow,
    Regime,
    Statistic,
    Verdict,
)

_DIST_STATS = (Statistic.FULL_JOINT, Statistic.SYNDROME_DIST)


# --------------------------------------------------------------------------- #
# emitted statistics from records (graduates outputs/.../_dist_from_records)   #
# --------------------------------------------------------------------------- #
def emitted_statistic(records: dict, statistic: Statistic, regime: Regime):
    """One statistic from a teacher's emitted records ``{"det": (N, R*n_stab) uint8, "obs": (N,)
    uint8}`` (the seam-folded surface). Pure host-side; ONE records draw feeds every statistic."""
    det = np.asarray(records["det"])
    obs = np.asarray(records["obs"])
    n = int(det.shape[0])
    if statistic in _DIST_STATS:
        bits = int(det.shape[1])
        weights = 1 << np.arange(bits, dtype=np.int64)
        keys = det.astype(np.int64) @ weights
        if statistic is Statistic.FULL_JOINT:
            keys = keys + (obs.astype(np.int64) << bits)
        u, c = np.unique(keys, return_counts=True)
        return {int(k): float(cnt) / n for k, cnt in zip(u, c)}
    if statistic is Statistic.DETECTOR_MARG:
        return np.concatenate([det.mean(axis=0), [float(obs.mean())]])
    if statistic is Statistic.RR_CORR:
        # the PER-ROUND |connected round-to-round Pearson correlation| corr(det_{r,j}, det_{r+1,j}),
        # averaged over stabs j, as a sequence over r = 0..R-2. The per-round shape (not a single
        # global mean) is what distinguishes a TRANSIENT chain from its stationary limit — the step-5b
        # correction; collapsing to one scalar hid the stationary-vs-transient bug. Still IDENTICALLY 0
        # (every round) for any independent-bit-flip foil (it factorizes across (round, stab)). At R=2
        # the sequence is length 1. Graduates ``twin_xzzx_teacher._mean_rr_corr``.
        # The full SIGNED (R-1, n_stab) Pearson matrix is built here (0 for a zero-variance entry — the
        # SAME convention the DM ``_conn_corr`` uses) and reduced by the SHARED ``reduce_rr_corr`` so
        # the emitted side and the DM anchor cannot drift (apples-to-apples; WS1 prereg §6).
        R = int(regime.R)
        n_stab = int(regime.n_stab or (det.shape[1] // max(R, 1)))
        d = det.reshape(n, R, n_stab).astype(np.float64)
        rr2d = np.zeros((max(R - 1, 1), n_stab), dtype=np.float64)
        for r in range(R - 1):
            for j in range(n_stab):
                rr2d[r, j] = _pearson_bits(d[:, r, j], d[:, r + 1, j])
        return reduce_rr_corr(rr2d) if R > 1 else np.array([0.0], dtype=np.float64)
    if statistic is Statistic.SPATIAL_CORR:
        # the PER-ROUND mean over OFF-DIAGONAL same-round stab pairs of |connected Pearson corr(
        # det_{r,j}, det_{r,j'})|, length R — the spatial mirror of the RR_CORR reduction. The full
        # SIGNED (R, n_stab, n_stab) Pearson matrix is built (diagonal = self-correlation; 0 for a
        # zero-variance entry — the DM convention) and reduced by the SHARED ``reduce_spatial_corr``.
        # IDENTICALLY 0 for any independent-bit-flip foil (it factorizes across (round, stab)).
        R = int(regime.R)
        n_stab = int(regime.n_stab or (det.shape[1] // max(R, 1)))
        d = det.reshape(n, R, n_stab).astype(np.float64)
        sp3d = np.zeros((R, n_stab, n_stab), dtype=np.float64)
        for r in range(R):
            for j in range(n_stab):
                for jp in range(n_stab):
                    sp3d[r, j, jp] = _pearson_bits(d[:, r, j], d[:, r, jp])
        return reduce_spatial_corr(sp3d)
    raise NotImplementedError(f"emitted_statistic for {statistic} arrives with its anchor adapter")


# --------------------------------------------------------------------------- #
# the SHARED moment reductions (one home — emitted side AND the DM anchor call #
# these, so the apples-to-apples shapes/semantics cannot drift; WS1 §6)        #
# --------------------------------------------------------------------------- #
def _pearson_bits(a: np.ndarray, b: np.ndarray) -> float:
    """The connected (Pearson) correlation of two {0,1} sample columns; 0 for a zero-variance column
    (the SAME convention the DM ``record_oracle._conn_corr`` uses, so a from-records reduction and the
    DM moments reduce identically). For {0,1} bits Var = E[d] - E[d]^2."""
    va, vb = float(a.var()), float(b.var())
    if va <= 1e-12 or vb <= 1e-12:
        return 0.0
    return float(np.mean((a - a.mean()) * (b - b.mean())) / np.sqrt(va * vb))


def reduce_rr_corr(rr2d) -> np.ndarray:
    """Reduce a SIGNED round-to-round correlation matrix ``rr2d`` (shape ``(R-1, n_stab)``, the DM
    ``record_oracle`` ``rr_corr`` OR the emitted per-(r,j) Pearson matrix) to the per-round sequence
    ``mean_j |rr2d[r,j]|`` of length ``R-1``. The ONE reduction both the DM anchor and the emitted
    side use (so the compared shapes match exactly). Length-0 (R==1) -> ``[0.0]`` (no round-to-round).
    Discriminating (not a constant collapse): a single nonzero (r,j) moves its round's value; and it is
    IDENTICALLY 0 only when every entry is 0 (the independent-bit-flip foil), preserving the teeth."""
    a = np.abs(np.asarray(rr2d, dtype=np.float64))
    if a.ndim != 2:
        raise ValueError(f"reduce_rr_corr expects a 2-D (R-1, n_stab) matrix, got shape {a.shape}")
    if a.shape[0] == 0:
        return np.array([0.0], dtype=np.float64)
    return a.mean(axis=1)


def reduce_spatial_corr(sp3d) -> np.ndarray:
    """Reduce a SIGNED same-round cross-detector matrix ``sp3d`` (shape ``(R, n_stab, n_stab)``, the DM
    ``record_oracle`` ``spatial_corr`` OR the emitted per-(r,j,j') Pearson matrix) to the per-round
    sequence ``mean_{j != j'} |sp3d[r,j,j']|`` of length ``R`` — the OFF-DIAGONAL mean (the diagonal is
    the trivial self-correlation 1 and is EXCLUDED so the reduction can discriminate; a constant
    diagonal would otherwise dominate). Mirrors ``reduce_rr_corr``. IDENTICALLY 0 for the
    independent-bit-flip foil (all off-diagonal entries 0), preserving the teeth. n_stab<2 -> 0 per
    round (no off-diagonal pair)."""
    a = np.abs(np.asarray(sp3d, dtype=np.float64))
    if a.ndim != 3 or a.shape[1] != a.shape[2]:
        raise ValueError(f"reduce_spatial_corr expects (R, n_stab, n_stab), got shape {a.shape}")
    R, n_stab, _ = a.shape
    if n_stab < 2:
        return np.zeros(R, dtype=np.float64)
    off = ~np.eye(n_stab, dtype=bool)
    return a[:, off].mean(axis=1)


# --------------------------------------------------------------------------- #
# the statistical backbone (pure; operates on statistic VALUES)                #
# --------------------------------------------------------------------------- #
def total_variation(p: dict, q: dict) -> float:
    return 0.5 * sum(abs(p.get(k, 0.0) - q.get(k, 0.0)) for k in set(p) | set(q))


def _dist_band(emitted: dict, anchor: AnchorValue, n: int) -> tuple[float, float]:
    realized = len(set(emitted) | set(anchor.value))
    floor = 0.5 * np.sqrt(realized / n) if n else 0.0
    extra = anchor.band if anchor.exactness is Exactness.STATISTICAL else 0.0
    return (0.0, float(max(6.0 / np.sqrt(n) if n else 0.0, 6.0 * floor) + extra))


def compare(statistic: Statistic, emitted, anchor: AnchorValue, *, N: int,
            null: float | None = None):
    """Score emitted-vs-anchor for one statistic -> (value, band, verdict, detail).

    EXACT anchor -> the band is the EMITTED side's Monte-Carlo floor; STATISTICAL -> + the anchor's
    own band. ``null`` (a second independent emitted draw's TV) is subtracted so the value is the
    GENUINE excess over the sampling floor (the carrier↔DM Gate-4 backbone is this with ``null`` set).
    """
    if statistic in _DIST_STATS:
        tv = total_variation(emitted, anchor.value)
        band = _dist_band(emitted, anchor, N)
        value = tv - (null or 0.0)
        return value, band, (Verdict.PASS if value <= band[1] else Verdict.FAIL), {"tv": tv, "null": null}
    if statistic is Statistic.SCALAR_FUNC:
        value = abs(float(emitted) - float(anchor.value))
        hi = anchor.band if anchor.exactness is Exactness.STATISTICAL else 1e-9
        return value, (0.0, hi), (Verdict.PASS if value <= hi else Verdict.FAIL), {}
    # array statistics (DETECTOR_MARG / RR_CORR / SPATIAL_CORR)
    e = np.asarray(emitted, dtype=float)
    a = np.asarray(anchor.value, dtype=float)
    value = float(np.max(np.abs(e - a))) if e.size else 0.0
    hi = (8.0 / np.sqrt(N) if N else 0.0) + (anchor.band if anchor.exactness is Exactness.STATISTICAL else 0.0)
    return value, (0.0, hi), (Verdict.PASS if value <= hi else Verdict.FAIL), {}


# --------------------------------------------------------------------------- #
# routing (feasible + exact-preferred; the OOM-safe data-driven choice)        #
# --------------------------------------------------------------------------- #
def route(anchors, statistic: Statistic, regime: Regime):
    """The best FEASIBLE anchor for (statistic, regime): exact preferred, then the tightest memory
    bound. None if no anchor is feasible (the cell is then UNANCHORED — an honest gap, not a crash).
    This is the MCWF-for-scale / DM-for-anchor split, expressed as data-driven routing."""
    cands = [a for a in anchors
             if statistic in a.answers() and a.capability(statistic, regime).feasible]
    if not cands:
        return None
    return min(cands, key=lambda a: (
        a.capability(statistic, regime).exactness is not Exactness.EXACT,
        a.capability(statistic, regime).mem_bytes_estimate or 0))


# --------------------------------------------------------------------------- #
# the measurement context a Control uses                                       #
# --------------------------------------------------------------------------- #
class MeasureCtx:
    """The façade a ``Control`` uses to perturb → re-measure → assert-it-fails, without the control
    touching the wheels. Carries the measured emitted statistic + the anchor's answer + the score, and
    (for the corrupt-stabilizer control) a way to RE-ANSWER the anchor with a negative-control
    corruption."""

    def __init__(self, anchor: Anchor, statistic: Statistic, regime: Regime, N: int,
                 emitted, anchor_value: AnchorValue, teacher: ControlledNoiseProcess):
        self.anchor = anchor
        self.statistic = statistic
        self.regime = regime
        self.N = N
        self.emitted = emitted
        self.anchor_value = anchor_value
        self.teacher = teacher

    def score(self, emitted=None, anchor_value=None) -> float:
        """The carrier-vs-anchor distance, optionally on a perturbed emitted / anchor value."""
        v, _, _, _ = compare(
            self.statistic,
            self.emitted if emitted is None else emitted,
            self.anchor_value if anchor_value is None else anchor_value, N=self.N)
        return v

    def corrupt_answer(self, corruption: dict) -> AnchorValue:
        """Re-answer the anchor with a negative-control corruption (e.g. ``{"stab": j}``) — the
        corrupted ground truth the (correct) emitted surface must FAIL to match (the control's teeth).
        Costs one extra ``answer`` (inherent to the control, not overhead on the positive path)."""
        return self.anchor.answer(self.teacher, self.statistic, self.regime, N=self.N, corrupt=corruption)


# --------------------------------------------------------------------------- #
# the engine                                                                   #
# --------------------------------------------------------------------------- #
def certify_cells(teacher: ControlledNoiseProcess, cells, anchors, controls, *, N: int, seed: int = 0,
                  m: int = 0) -> CertReport:
    """Route → controls-first → score → ledger over ``cells`` (a list of (Statistic, Regime)).

    ONE ``emit`` per (regime, m) is cached (perf). Controls run BEFORE the positive row and an inert
    one forces FAIL (``_rollup``). The ``certify_teacher`` facade (step 6) layers the full policy on
    top (auto-routing, the controls-non-optional gate, the level grid)."""
    rows: list[LedgerRow] = []
    control_rows: list[LedgerRow] = []
    routing: dict = {}
    emit_cache: dict = {}

    def _emitted(anchor, statistic, regime):
        kind = anchor.emit_kind() if hasattr(anchor, "emit_kind") else "full"
        key = (_rkey(regime), kind, m)
        if key not in emit_cache:  # ONE emit per (regime, kind) — perf: shared across statistics
            if kind == "clifford_slice":
                # the stim anchor's WIRING check: the teacher's bit-flip Clifford slice
                # (theta=0, gamma=0, X_ERROR(p_x)) — the SAME geometry + seam fold the full mix uses.
                emit_cache[key] = teacher.emit_clifford_slice(regime, p_x=anchor.p_x, m=m, N=N, seed=seed)
            elif kind == "full":
                emit_cache[key] = teacher.emit(regime, m=m, N=N, seed=seed)
            else:
                # an anchor declares an emit_kind the teacher has no source for (e.g. the closed-form
                # anchor's "nonunital_slice"): FAIL LOUD. Silently falling back to teacher.emit() would
                # compare the anchor's isolated-slice prediction against the FULL-mix records (the
                # degenerate-amp-damp footgun the review caught) — a silent toy. Wire the slice or use
                # a standalone check (the closed-form anchor is validated by certify_closed_form_5b.py).
                raise NotImplementedError(
                    f"emit_kind {kind!r} (anchor {anchor.name!r}) has no teacher emit path in "
                    f"certify_cells; wire teacher.emit_{kind}() or run the anchor's standalone check")
        return emitted_statistic(emit_cache[key], statistic, regime)

    for statistic, regime in cells:
        anchor = route(anchors, statistic, regime)
        rk = (statistic.value, _rkey(regime))
        if anchor is None:
            rows.append(LedgerRow(None, statistic, float("nan"), None, "c", Verdict.UNANCHORED,
                                  {"reason": "no feasible anchor for this regime"}))
            routing[rk] = "UNANCHORED (no feasible anchor — honest gap, not PASS)"
            continue
        cap = anchor.capability(statistic, regime)
        routing[rk] = f"{anchor.name} [{cap.exactness.value}]"
        av = anchor.answer(teacher, statistic, regime, N=N)
        _assert_anchor_value(av, anchor)
        emitted = _emitted(anchor, statistic, regime)
        # controls FIRST (the invariant): perturb → re-measure → must fire
        ctx = MeasureCtx(anchor, statistic, regime, N, emitted, av, teacher=teacher)
        cell_controls: list[LedgerRow] = []
        for ctrl in controls:
            if ctrl.guards(statistic):
                cr = ctrl.run(ctx, statistic, regime, N=N)
                control_rows.append(cr)
                cell_controls.append(cr)
        value, band, verdict, detail = compare(statistic, emitted, av, N=N)
        # anti-vacuity, made STRUCTURAL (types.py: "a certification with no falsifier is rejected"):
        # record THIS cell's control coverage so _rollup can reject a teeth-less PASS — a scored row
        # needs >=1 APPLICABLE control that FIRED, else the cell is uncertified (no falsifier).
        n_fired = sum(1 for c in cell_controls
                      if c.detail.get("applicable", True) and c.detail.get("fired", False))
        detail = {**detail, "n_controls": len(cell_controls), "n_controls_fired": n_fired}
        rows.append(LedgerRow(anchor.name, statistic, value, band, av.epistemic_class, verdict, detail))

    return CertReport(_rollup(rows, control_rows), tuple(rows), tuple(control_rows), routing,
                      dict(teacher.truth), {"N": N, "seed": seed, "m": m})


def _assert_anchor_value(av: AnchorValue, anchor: Anchor) -> None:
    """The port's EXACTNESS-DECLARED contract: an EXACT anchor returns band 0 (no undeclared band),
    AND the epistemic class is consistent with the exactness — class 'a' (exact-grade) requires EXACT.
    A class-'a' STATISTICAL value would be rolled up as an EXACT pass (PASS, not PASS_PROVISIONAL) — a
    sampled result inflated to 'exact' (violating the no-inflation invariant); reject it on ingest."""
    if av.exactness is Exactness.EXACT and av.band != 0.0:
        raise ValueError(f"EXACT anchor '{anchor.name}' returned band={av.band} != 0 (undeclared band)")
    if av.epistemic_class == "a" and av.exactness is not Exactness.EXACT:
        raise ValueError(
            f"anchor '{anchor.name}' value is epistemic class 'a' (exact-grade) but exactness="
            f"{av.exactness.value} != EXACT — a statistical result mislabeled 'a' is rolled up as an "
            f"EXACT PASS (inflation). Declare class 'b' for a STATISTICAL value.")


def _rkey(regime: Regime) -> tuple:
    return (regime.R, regime.register, regime.n_active, regime.arm, regime.b)


def _rollup(rows, controls) -> Verdict:
    """The verdict roll-up — the genuine-check teeth made structural."""
    # an APPLICABLE control that RAN but did NOT fire forces FAIL — a vacuous check cannot pass. A
    # control that marked itself INAPPLICABLE (e.g. a shuffle that is identity on a symmetric value)
    # is skipped here: it could not perturb, so it is not a FAILED falsifier — but it also buys no
    # PASS, because the per-cell coverage check below still demands a real, firing control.
    if any(not c.detail.get("fired", False) for c in controls if c.detail.get("applicable", True)):
        return Verdict.FAIL
    if any(r.verdict is Verdict.FAIL for r in rows):
        return Verdict.FAIL
    if any(r.verdict is Verdict.UNANCHORED for r in rows):
        return Verdict.FINDING  # an honest gap (reportable), NOT a PASS
    if not rows:
        return Verdict.FINDING
    # ANTI-VACUITY made STRUCTURAL (the types.py invariant: "a certification with no falsifier is
    # rejected"): a SCORED, anchored, passing row needs >=1 control that FIRED. A passing row with no
    # working falsifier is UNCERTIFIED -> FINDING, never PASS — this closes the `any([]) == False`
    # empty-controls / all-inapplicable hole (a teeth-less PASS was the subsystem's reason-to-exist bug).
    if any(r.detail.get("n_controls_fired", 0) < 1 for r in rows if r.verdict is Verdict.PASS):
        return Verdict.FINDING
    # PASS only if EVERY row is an EXACT pass; any statistical pass -> PASS_PROVISIONAL (no inflation).
    all_exact = all(r.epistemic_class == "a" for r in rows)
    return Verdict.PASS if all_exact else Verdict.PASS_PROVISIONAL
