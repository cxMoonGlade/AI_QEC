"""M4 decoder-prior composition: DEM skeleton, sub-chain projection, arms (S2/S4/S5/S6/S12).

Pre-registration of record: docs/metric_results.md "M4 PRE-REGISTRATION
(decoder-prior utility; recorded 2026-06-10 BEFORE build/run)"; binding
blueprint docs/.reports/m4_panel/R_reviewer_verdict.md; derivations
docs/.reports/m4_panel/M4B_decoder_mechanics.md (1.1-1.6, 2.2-2.3). This module
is BUILD-side machinery only: it constructs probability columns and projected
DEMs; it never decodes, never fits (S11: ZERO new twin fits -- the frozen M3
cache outputs/m3_fit_cache.pt is a read-only input).

Registered design pins implemented here (epistemic classes per the registration):

* STRUCTURE FREEZE (c, S4): every primary DEM arm shares the shipped-SI1000
  exact-DEM ``(detectors, observable-flags)`` skeleton; arms differ ONLY in the
  probability column. No primary arm carries the mirror-diagonal class; the
  mirror class lives in the claim-flagged ``extended_skeleton`` ablation
  secondary (G6) and is NEVER an input to a primary.
* DECOMPOSED INSTRUCTIONS (FIX ROUND 2026-06-10; measured structure of the
  shipped SI1000 exact DEM, both bases identical): 86,115 error instructions
  of which 2,002 carry a ``^`` decomposition separator (exactly 2 components
  each, max 2); component arity census {1: 6,008, 2: 82,109} over all 88,117
  components -- every component has 1 or 2 detectors. The registration's I-3
  "0 hyperedges" is a COMPONENT-arity fact (no component exceeds 2 detectors),
  NOT "no separators"; ``load_skeleton`` asserts exactly that precondition.
  Contract: the probability slot stays 1:1 with the INSTRUCTION (the STRUCTURE
  FREEZE skeleton is the instruction list; arms differ only in the probability
  column); per-instruction component structure (detector ids + observable
  flags per component, stim order) is stored on ``Skeleton.comps`` and emitted
  byte-faithfully (separators + component order preserved); the S2 projection
  applies COMPONENT-WISE (a component with >= 1 in-grid detector survives,
  one-detector-outside becomes the weight-1 survivor, all components gone =>
  the instruction is dropped; full restriction stays the identity, P1c).
  ARM ASSIGNMENT -- ADJUDICATED (M4 PRE-RUN AMENDMENT 1 ruling 15,
  docs/metric_results.md, recorded 2026-06-10 before the pins stage): the
  conservative reading is ACCEPTED -- a decomposed instruction touches two
  edge sites at once, so it is NEVER twin-owned and never Spitz-estimated
  (the ledgered pairwise estimator does not define a >2-detector mechanism);
  every constructed arm (A2/A3/A3b) carries the shipped SI1000 probability on
  those slots (clamped), IDENTICALLY, so the 2,002 slots cancel out of every
  registered contrast -- including pij-vs-naive -- by construction (measured
  breakdown: all 2,002 are decomposed[w1+w1]). Condition carried (C-1 i): the
  G2 freeze manifest's fill table MUST disclose the decomposed census + this
  passthrough rule (see ``freeze_manifest``).
* DETECTOR COORDINATES (FIX ROUND 2 2026-06-10; reviewer change item B-17):
  two coordinate layers, never conflated. (1) SOURCE (device) coordinates:
  the shipped SI1000 exact DEM annotates every detector with (x, y, t)
  triplets -- measured arity census {3: 28 init, 6: 28,000 bulk, 9: 28
  final}, both bases identical. ``load_skeleton`` CAPTURES them on
  ``Skeleton.coords``; ``with_probabilities`` re-emits them faithfully;
  ``subchain_skeleton`` passes them through UNCHANGED for surviving
  detectors (a sub-DEM detector keeps its device annotation verbatim; only
  the detector index re-densifies). P1c extended: coordinates byte-faithful
  through parse -> serialize -> parse, identity at full restriction.
  (2) CANONICAL decode-facing coordinates: B2's A3c geometry contract
  (``m4_decode.SpaceEdgeGeometry``) requires integral
  ``(chain, ..., layer)`` -- coordinate[0] = dense chain rank,
  coordinate[-1] = dense layer rank. The DEVICE coordinates do NOT satisfy
  it (measured: x in [1, 10], 10 distinct values over 28 chains -- x alone
  does not identify the chain; trailing t is a raw round tag, not the dense
  layer rank). ``with_grid_coordinates(skel, grid)`` therefore replaces the
  annotations with the GLOBAL ``(chain, layer)`` grid ranks; A3c
  window/subchain DEMs must be emitted from that transform (qubit-key
  alignment: data qubit g <-> chain pair (g-1, g), the B-16 adaptor
  convention used by ``two_pass_table`` consumers).
* Sub-chain projection (a, S2/P1c): keep errors with >= 1 detector inside the
  sub-grid; a one-detector-outside error becomes a weight-1 boundary edge at
  the surviving detector with the SAME probability; restriction at the full
  chain is the identity. Sub-observable (M4-B 2.3): leftmost data qubit of the
  sub-chain -- after projection, exactly the left-cut-crossing errors carry L0.
* Twin->DEM composition (S5): SPACE(j, bulk) <- r_hat_j = 2 p01 p10/(p01+p10)
  (the stationary MARGINAL flip probability (a)); TIME(i, bulk) <- q_eff_i
  (gauge-exact (a)); MEDIAN over owning windows (c); ownership filter = data
  qubits at interior window positions 2-4 only (0-based local {1, 2, 3}; the
  edge positions absorb out-of-window mass -- the A2 finding), measure qubits
  at the 4 fully-interior window detectors. ALL unowned cells (chain ends, the
  {15,19} region, boundary measures, layers outside [80, 999], diagonals,
  weight-1 boundaries) take the pij arm's values IDENTICALLY, so the dLER
  contrast is attributable to twin-owned cells BY CONSTRUCTION.
  f_hat = r_hat * R_hat = (p01+p10)/2 is exactly P(flip_{t+1} | flip_t), NOT a
  marginal, and is NEVER assigned to a static edge -- enforced by an explicit
  guard (``assert_marginal_not_conditional``), the registered P7->A2 lesson.
* A2 pij arm (S4): Spitz Eq. 13 EXACT train estimates (hardware/pij.py, the
  ledgered estimator) on the skeleton support; bulk layers [80, 999] are
  layer-POOLED (pooled moments first, M3 convention); layers outside the bulk
  window are LAYER-RESOLVED (the M1-P6 transient keeps its measured profile);
  clamp [1e-6, 1/2 - 1e-6] (c) with clamp-hit counts reported (G9);
  mean-matching boundary half-edges: at every detector site carrying weight-1
  slots, the single is solved so the composed site marginal reproduces the
  measured detection fraction EXACTLY (the M3 construction extended to the
  window graph).
* A3b Spitz-of-the-twin (secondary, claim-separated): the twin model's
  exactly-implied two-point detector statistics -- stationary Markov pair =>
  Cov(F_t, F_{t+dt}) = lambda^{dt-1} (p01 p10 - r^2), lambda = 1 - p01 - p10
  (a, derived in-module) -- pushed through the SAME Spitz Eq. 13 inversion on
  the SAME skeleton support, with twin-implied mean-matching boundaries where
  the twin parameter set covers the site; everything else falls back to the
  pij arm's values identically.
* P1h composition acceptance (b, S5/S6): composed per-site detector marginal
  1 - 2 f_i = prod_{e ni i} (1 - 2 p_e) within +/-0.5% absolute of the train
  detection fraction (``acceptance_check``; AMENDED gating split -- the
  freeze halts on the structural component only, the +/-0.5% band is scored
  per arm as the (b) bet it is: M4 PRE-RUN AMENDMENT 1 ruling 14).
* G2 one-shot composition freeze: ``freeze_manifest`` pins the sha256 of this
  source file + the frozen cache keys used + fill/clamp/support tables BEFORE
  any decode of samples 05+.

Seeds: all NEW M4 randomness uses seed 20260610 (ratified R3); this module is
deterministic and draws no random numbers. Samples 01-99 are never touched
here -- inputs are sample_00 train artifacts and the frozen M3 cache only.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np

from qec_twin.hardware.blocks import CLEAN_INTERIOR_WINDOWS, HOT_WINDOWS
from qec_twin.hardware.pij import PairCounts, _class_moment_planes, spitz_pij_exact
from qec_twin.hardware.stim_artifacts import DetectorGrid
from qec_twin.numerics import NUMERICAL_ZERO

M4_SEED = 20260610  # ratified R3; recorded for the manifest (module draws no randomness)
CLAMP_LO = 1e-6  # registered clamp (c), S4
CLAMP_HI = 0.5 - 1e-6
BULK_LAYER_LO = 80  # the M3 bulk window [80, 999]; outside = layer-resolved unowned
BULK_LAYER_HI = 999
OWNED_DATA_LOCAL = (1, 2, 3)  # 0-based local data positions; = registered "interior positions 2-4"
OWNED_MEASURE_LOCAL = (0, 1, 2, 3)  # all 4 fully-interior window detector columns
FULL_DISTANCE = 29  # d=29 release: data qubits 0..28, measure chains 0..27
HOT_PAIR_CHAINS = (18, 21)  # the M2-located grid-adjacent device pair behind HOT_WINDOWS
ACCEPTANCE_TOL = 5e-3  # P1h: +/-0.5% absolute (b)

PairKey = "tuple[int, int, int]"  # (|di|, |dt|, orientation) -- pij.py convention


# ---------------------------------------------------------------- exact identities (a)


def r_hat(p01: float, p10: float) -> float:
    """Stationary MARGINAL flip probability of the (p01, p10) Markov pair (a):
    ``r = 2 p01 p10 / (p01 + p10)`` -- the S5 space-edge assignment."""

    return 2.0 * float(p01) * float(p10) / max(float(p01) + float(p10), NUMERICAL_ZERO)


def R_hat(p01: float, p10: float) -> float:
    """Bunching ratio (a): ``R = (p01 + p10)^2 / (4 p01 p10)``; iid edges pin R == 1."""

    s = float(p01) + float(p10)
    return s * s / max(4.0 * float(p01) * float(p10), NUMERICAL_ZERO)


def f_hat(p01: float, p10: float) -> float:
    """``f = (p01 + p10)/2 = r * R = P(flip_{t+1} | flip_t)`` exactly (a) -- the
    conditional re-flip probability, NOT a marginal. NEVER a static edge value."""

    return 0.5 * (float(p01) + float(p10))


def markov_flip_cov(p01: float, p10: float, dt: int) -> float:
    """Exact stationary flip autocovariance of the Markov pair (a):

    ``Cov(F_t, F_{t+dt}) = lambda^(dt-1) * (p01 p10 - r^2)``, ``lambda = 1 - p01 - p10``,
    with ``F_t = s_t XOR s_{t-1}`` and ``r = r_hat``. At ``dt = 1`` this is
    ``p01 p10 - r^2 = r^2 (R - 1)`` -- the DEM-expressible bunching shadow.
    (The registration's "geometric (1 - p01 - p10)^dt" labels this family; the
    exact exponent on the covariance prefactor is ``dt - 1``, derived from the
    eigendecomposition of the 2-state transition matrix.)
    """

    if int(dt) < 1:
        raise ValueError("flip autocovariance needs dt >= 1")
    lam = 1.0 - float(p01) - float(p10)
    r = r_hat(p01, p10)
    return lam ** (int(dt) - 1) * (float(p01) * float(p10) - r * r)


def assert_marginal_not_conditional(
    value: float,
    r_hat_median: float,
    f_hat_median: float,
    R_hat_median: float,
    context: str = "",
) -> None:
    """S5 registered prohibition (the P7->A2 coordinate lesson): the value written
    to a static space edge must be the r_hat median and never f_hat = r * R.

    Raises ``AssertionError`` on any violation; ``r <= f`` holds per window by
    AM-HM, so a value above the f_hat median is always mis-wired.
    """

    if not np.isfinite(value):
        raise AssertionError(f"S5 GUARD: non-finite space-edge probability {context}")
    if value > f_hat_median + NUMERICAL_ZERO:
        raise AssertionError(
            f"S5 GUARD: space-edge value {value!r} exceeds the f_hat median "
            f"{f_hat_median!r} {context} -- r_hat <= f_hat is an exact identity; "
            "this assignment is mis-wired"
        )
    if abs(value - r_hat_median) > NUMERICAL_ZERO:
        raise AssertionError(
            f"S5 GUARD: space-edge value {value!r} is not the registered r_hat "
            f"median {r_hat_median!r} {context}"
        )
    if (
        R_hat_median > 1.0 + 1e-9
        and f_hat_median > r_hat_median + NUMERICAL_ZERO
        and abs(value - f_hat_median) <= NUMERICAL_ZERO
    ):
        raise AssertionError(
            f"S5 GUARD: space-edge value equals f_hat = r*R {context} -- the "
            "conditional re-flip probability is never a static edge value"
        )


# ---------------------------------------------------------------- skeleton (S4 structure freeze)


@dataclass(frozen=True)
class Skeleton:
    """The frozen (detectors, observable-flags) DEM skeleton (S4 STRUCTURE FREEZE).

    ``dets``/``obs`` are per-error tuples in instruction order; detector ids are
    GLOBAL (the full-chain numbering) even for projected sub-skeletons --
    ``detector_ids`` lists the (sorted) global ids of this (sub-)grid, and
    emission via ``with_probabilities`` maps them to dense local indices.
    ``p`` is the source probability column (for the shipped SI1000 skeleton:
    the A1 naive arm's values).

    ``comps`` is the per-instruction component structure: a tuple (one entry
    per instruction) of tuples of ``(component_dets, component_obs)`` pairs in
    stim's ``^``-separator order. Single-component instructions (the 84,113
    graphlike majority on the real DEM) have ``len(comps[i]) == 1``;
    ``dets[i]``/``obs[i]`` are always the flattened concatenations across
    components (the instruction's full symptom set -- firing the instruction
    flips EVERY listed detector; the separator is decoder guidance only).
    When ``comps`` is omitted, every instruction is treated as
    single-component (backward-compatible constructor).

    ``coords`` (FIX ROUND 2, B-17) holds the source DEM's ``detector(...)``
    coordinate annotations: one tuple of floats per entry of
    ``detector_ids`` (same order; ``()`` = declared without coordinates), or
    ``None`` when the source DEM carries no annotations at all
    (backward-compatible default -- emission then falls back to the bare
    trailing detector-count pin). Projection passes coordinates through
    UNCHANGED for surviving detectors; ``with_grid_coordinates`` swaps in the
    canonical integral ``(chain, layer)`` annotations that the A3c geometry
    contract requires.

    Interop note (B-18 correction of record): ``Skeleton`` deliberately
    exposes NO ``.dem`` attribute -- emission is always explicit through
    ``with_probabilities`` (which returns the G9 ``ClampReport`` alongside
    the DEM); ``m4_decode.as_dem``'s ``.dem`` duck-type hook does not engage
    on skeleton objects.
    """

    dets: tuple  # tuple[tuple[int, ...], ...] global detector ids, flattened, target order
    obs: tuple  # tuple[tuple[int, ...], ...] logical-observable ids, flattened
    p: np.ndarray  # [E] float64 source probability column
    detector_ids: np.ndarray  # sorted global detector ids of this (sub-)grid
    num_detectors_full: int  # detector count of the full-chain numbering space
    data_lo: int = 0  # left data-qubit index of this (sub-)chain
    data_hi: int | None = None  # right data-qubit index; None = native full skeleton
    source: str = "si1000_exact"
    extended_mask: np.ndarray | None = None  # True on slots added by extended_skeleton
    comps: tuple | None = None  # per-instruction ((dets, obs), ...) components; None => all single
    coords: tuple | None = None  # per-detector_ids coordinate tuples; None => no annotations

    def __post_init__(self):
        if self.comps is None:
            object.__setattr__(
                self, "comps", tuple(((d, o),) for d, o in zip(self.dets, self.obs))
            )
        if self.coords is not None and len(self.coords) != len(self.detector_ids):
            raise ValueError(
                f"coords carries {len(self.coords)} entries for "
                f"{len(self.detector_ids)} detectors -- one annotation tuple per "
                "detector_ids entry (B-17 capture contract)"
            )

    @property
    def num_errors(self) -> int:
        return len(self.dets)

    @property
    def num_decomposed(self) -> int:
        """Instructions carrying >= 1 decomposition separator."""

        return sum(1 for c in self.comps if len(c) > 1)

    def arity_census(self) -> dict:
        """Census over the FLATTENED per-instruction detector count (a
        decomposed instruction counts its full symptom set, 3-4 on the real
        DEM); per-component arities live in ``component_census``."""

        census: dict = {}
        for dets in self.dets:
            census[len(dets)] = census.get(len(dets), 0) + 1
        return census

    def component_census(self) -> dict:
        """Arity census over COMPONENTS -- the true I-3 graphlike object
        (measured on the real DEM: {1: 6,008, 2: 82,109})."""

        census: dict = {}
        for comps in self.comps:
            for comp_dets, _ in comps:
                census[len(comp_dets)] = census.get(len(comp_dets), 0) + 1
        return census


def load_skeleton(dem, *, source: str = "si1000_exact") -> Skeleton:
    """Parse a stim ``DetectorErrorModel`` into the frozen skeleton.

    Asserts the TRUE I-3 precondition: graphlike COMPONENTS -- every
    ``^``-separated component carries exactly 1 or 2 detector targets ("0
    hyperedges" = no component arity > 2; separators themselves are part of
    the shipped structure: 2,002 of the 86,115 SI1000 instructions are
    decomposed into exactly 2 components, measured 2026-06-10, both bases).
    The instruction <-> probability-slot mapping stays 1:1 (STRUCTURE FREEZE);
    component structure (detectors + observable flags per component, stim
    order) is preserved on ``Skeleton.comps`` for byte-faithful emission.
    The shipped recipe is
    ``circuit.detector_error_model(decompose_errors=True, flatten_loops=True)``
    (S4 / M4-B 2.2; measured I-3: 86,115 errors, 0 hyperedges).

    Detector coordinate annotations are CAPTURED on ``Skeleton.coords`` (B-17;
    the shipped SI1000 exact DEM carries device (x, y, t)-triplet coordinates,
    arity census {3: 28, 6: 28,000, 9: 28}); a DEM without any annotation
    yields ``coords=None``.
    """

    dets_list: list = []
    obs_list: list = []
    comps_list: list = []
    probs: list = []
    for index, instruction in enumerate(dem.flattened()):
        if instruction.type != "error":
            continue
        comps: list = [([], [])]
        for target in instruction.targets_copy():
            if target.is_separator():
                comps.append(([], []))
            elif target.is_relative_detector_id():
                comps[-1][0].append(int(target.val))
            elif target.is_logical_observable_id():
                comps[-1][1].append(int(target.val))
        for comp_dets, _ in comps:
            if len(comp_dets) == 0 or len(comp_dets) > 2:
                raise ValueError(
                    f"error #{index} has a component with {len(comp_dets)} detector "
                    "targets -- the M4 skeleton precondition is graphlike COMPONENTS "
                    "(1 or 2 detectors per component; I-3 '0 hyperedges' = no "
                    "component arity > 2)"
                )
        flat_dets = tuple(d for comp_dets, _ in comps for d in comp_dets)
        flat_obs = tuple(o for _, comp_obs in comps for o in comp_obs)
        if len(set(flat_dets)) != len(flat_dets):
            raise ValueError(
                f"error #{index} repeats a detector across decomposition components "
                "-- components must partition the symptom set (precondition; a trip "
                "here on real data is a finding, not a silent merge)"
            )
        dets_list.append(flat_dets)
        obs_list.append(flat_obs)
        comps_list.append(tuple((tuple(cd), tuple(co)) for cd, co in comps))
        probs.append(float(instruction.args_copy()[0]))
    if not dets_list:
        raise ValueError("DEM contains no error instructions")
    num_detectors = int(dem.num_detectors)
    coords_map = dem.get_detector_coordinates()
    coords = tuple(
        tuple(float(v) for v in coords_map.get(d, ())) for d in range(num_detectors)
    )
    return Skeleton(
        dets=tuple(dets_list),
        obs=tuple(obs_list),
        p=np.asarray(probs, dtype=np.float64),
        detector_ids=np.arange(num_detectors, dtype=np.int64),
        num_detectors_full=num_detectors,
        data_lo=0,
        data_hi=None,
        source=source,
        comps=tuple(comps_list),
        coords=coords if any(coords) else None,
    )


@dataclass(frozen=True)
class ClampReport:
    """G9 floor/clamp accounting for one emitted probability column."""

    low_hits: int
    high_hits: int
    total_errors: int
    clamp_lo: float
    clamp_hi: float

    @property
    def total_hits(self) -> int:
        return self.low_hits + self.high_hits


def _fmt_coord(v: float) -> str:
    """One detector-coordinate value: integral floats print as integers (the
    shipped DEM's own style, e.g. ``detector(1, 5, 0) D0``); stim parses both
    forms to the same float, so P1c's parsed-value comparison is unaffected."""

    f = float(v)
    return str(int(f)) if f == int(f) else repr(f)


def with_probabilities(
    skel: Skeleton,
    p: np.ndarray,
    *,
    clamp: bool = True,
    clamp_lo: float = CLAMP_LO,
    clamp_hi: float = CLAMP_HI,
):
    """Emit a stim DEM: SAME instruction order, probability column replaced.

    Returns ``(stim.DetectorErrorModel, ClampReport)`` -- the clamp-hit counts
    are part of the G9 reporting contract, hence returned, not swallowed.
    Detector targets are emitted as dense LOCAL indices (position within
    ``skel.detector_ids``); for the native full skeleton local == global, so
    the parse -> serialize round-trip is the identity (P1c). Decomposed
    instructions are reproduced byte-faithfully: ``^`` separators preserved,
    component order preserved, per-component observable flags preserved
    (within a component, detectors then observables -- stim's canonical
    ``analyze_errors`` order, re-verified by the P1c hardware round-trip).

    Coordinate emission (B-17): when ``skel.coords`` is set, EVERY local
    detector is declared with its annotation verbatim
    (``detector(args) D{local}``; integral values printed as integers --
    stim's parsed-value equality is what P1c pins), which also pins
    ``num_detectors``. Without annotations the legacy bare trailing
    ``detector D{n-1}`` count pin applies when needed.
    """

    import stim

    column = np.asarray(p, dtype=np.float64)
    if column.shape != (skel.num_errors,):
        raise ValueError(f"probability column shape {column.shape} != ({skel.num_errors},)")
    low_hits = int((column < clamp_lo).sum()) if clamp else 0
    high_hits = int((column > clamp_hi).sum()) if clamp else 0
    if clamp:
        column = np.clip(column, clamp_lo, clamp_hi)
    local = {int(g): i for i, g in enumerate(skel.detector_ids)}
    lines: list = []
    max_ref = -1
    for comps, pe in zip(skel.comps, column):
        parts = []
        for comp_dets, comp_obs in comps:
            targets = []
            for d in comp_dets:
                ld = local[int(d)]
                max_ref = max(max_ref, ld)
                targets.append(f"D{ld}")
            targets.extend(f"L{int(o)}" for o in comp_obs)
            parts.append(" ".join(targets))
        lines.append(f"error({float(pe)!r}) " + " ^ ".join(parts))
    num_local = len(skel.detector_ids)
    if skel.coords is not None:
        # B-17: every local detector declared with its annotation verbatim
        # (also pins num_detectors -- the bare trailing pin is subsumed)
        for i, args in enumerate(skel.coords):
            if args:
                lines.append(
                    "detector(" + ", ".join(_fmt_coord(v) for v in args) + f") D{i}"
                )
            else:
                lines.append(f"detector D{i}")
    elif max_ref < num_local - 1:
        # pin num_detectors for downstream decode_batch shape agreement
        lines.append(f"detector D{num_local - 1}")
    dem = stim.DetectorErrorModel("\n".join(lines))
    return dem, ClampReport(
        low_hits=low_hits,
        high_hits=high_hits,
        total_errors=skel.num_errors,
        clamp_lo=clamp_lo,
        clamp_hi=clamp_hi,
    )


def dem_sha256(dem_or_path) -> str:
    """P1f hash: sha256 of a DEM's canonical text (objects) or raw bytes (paths)."""

    if isinstance(dem_or_path, (str, Path)):
        return hashlib.sha256(Path(dem_or_path).read_bytes()).hexdigest()
    return hashlib.sha256(str(dem_or_path).encode("utf-8")).hexdigest()


def roundtrip_report(dem) -> dict:
    """P1c parse -> serialize -> parse fixed point on the error list.

    ``errors_equal`` compares the full component structure verbatim (detector
    ids, observable flags, ``^`` separators and component order -- decomposed
    instructions must survive byte-faithfully); ``coords_equal`` compares the
    captured detector coordinate annotations verbatim (B-17 extension of the
    pin; ``None == None`` for annotation-free DEMs); ``p_bitexact_unclamped``
    compares probabilities bit-exactly on entries the registered clamp does not
    touch; clamp hits are reported (zero expected on physical DEMs).
    """

    skel = load_skeleton(dem)
    emitted, clamp_rep = with_probabilities(skel, skel.p)
    back = load_skeleton(emitted)
    unclamped = (skel.p >= clamp_rep.clamp_lo) & (skel.p <= clamp_rep.clamp_hi)
    return {
        "errors_equal": skel.dets == back.dets
        and skel.obs == back.obs
        and skel.comps == back.comps,
        "coords_equal": skel.coords == back.coords,
        "p_bitexact_unclamped": bool(np.array_equal(skel.p[unclamped], back.p[unclamped])),
        "num_errors": skel.num_errors,
        "clamp_low_hits": clamp_rep.low_hits,
        "clamp_high_hits": clamp_rep.high_hits,
        "num_detectors_preserved": back.num_detectors_full == skel.num_detectors_full,
    }


# ---------------------------------------------------------------- error classification


@dataclass(frozen=True)
class ErrorSite:
    """Grid placement of one skeleton error (global coordinates).

    ``num_components > 1`` marks a decomposed instruction: its instruction-
    level placement is a SENTINEL (``key=None``, ``arity`` = flattened
    detector count, ``row``/``col`` = minima over all detectors, ``di=dt=0``)
    -- consumers MUST branch on ``num_components`` before reading ``key``;
    per-component placements live in ``component_sites``.
    """

    arity: int
    key: tuple | None  # (di, dt, orient) for arity-2; None for weight-1 / decomposed
    row: int  # min layer (pairs) / layer (weight-1)
    col: int  # min chain (pairs) / chain (weight-1)
    di: int
    dt: int
    num_components: int = 1


def _place_component(dets, layer, chain) -> ErrorSite:
    """Placement of one graphlike component (1-2 detectors); orientation per
    the pij.py convention (+1 when the min-layer detector sits at the min
    chain)."""

    if len(dets) == 1:
        d = int(dets[0])
        return ErrorSite(1, None, int(layer[d]), int(chain[d]), 0, 0)
    a, b = int(dets[0]), int(dets[1])
    la, ca = int(layer[a]), int(chain[a])
    lb, cb = int(layer[b]), int(chain[b])
    if (la, ca) > (lb, cb):
        la, ca, lb, cb = lb, cb, la, ca
    dt = lb - la
    di = abs(cb - ca)
    orient = 0 if (di == 0 or dt == 0) else (1 if cb > ca else -1)
    return ErrorSite(2, (di, dt, orient), la, min(ca, cb), di, dt)


def error_sites(skel: Skeleton, grid: DetectorGrid) -> tuple:
    """Per-error ``ErrorSite`` placements (instruction level). Decomposed
    instructions get the documented sentinel (``num_components`` set, ``key``
    None); their per-component classification lives in ``component_sites``."""

    layer = grid.det_to_layer
    chain = grid.det_to_chain
    out: list = []
    for dets, comps in zip(skel.dets, skel.comps):
        if len(comps) == 1:
            out.append(_place_component(comps[0][0], layer, chain))
            continue
        rows = [int(layer[int(d)]) for d in dets]
        cols = [int(chain[int(d)]) for d in dets]
        out.append(ErrorSite(len(dets), None, min(rows), min(cols), 0, 0, len(comps)))
    return tuple(out)


def component_sites(skel: Skeleton, grid: DetectorGrid) -> tuple:
    """Per-instruction tuple of per-COMPONENT ``ErrorSite`` placements (each
    component classified as the standalone graphlike edge it is -- the site
    classifier behind the decomposed-class breakdown in ``support_census``).
    For single-component instructions this is one-element."""

    layer = grid.det_to_layer
    chain = grid.det_to_chain
    return tuple(
        tuple(_place_component(comp_dets, layer, chain) for comp_dets, _ in comps)
        for comps in skel.comps
    )


def _signature_groups(skel: Skeleton) -> dict:
    """Instruction indices grouped by component-structure signature (the
    sorted tuple of per-component (sorted dets, sorted obs) pairs; for
    single-component instructions this is the plain (dets, obs) signature).

    Parallel instructions sharing a signature are written via the merged-edge
    identity ``1 - 2P = (1 - 2p)^k`` (pymatching merges parallel edges
    "independent"); the shipped SI1000 exact DEM fuses identical symptoms, so
    k == 1 everywhere there -- the split rule is defensive and reported.
    """

    groups: dict = {}
    for i, comps in enumerate(skel.comps):
        sig = tuple(
            sorted((tuple(sorted(cd)), tuple(sorted(co))) for cd, co in comps)
        )
        groups.setdefault(sig, []).append(i)
    return groups


def _write_group(probs: np.ndarray, idxs: list, target: float) -> None:
    if len(idxs) == 1:
        probs[idxs[0]] = float(target)
        return
    per = 0.5 * (1.0 - (1.0 - 2.0 * float(target)) ** (1.0 / len(idxs)))
    for i in idxs:
        probs[i] = per


# ---------------------------------------------------------------- S2 sub-chain projection (a)


def subchain_skeleton(skel: Skeleton, grid: DetectorGrid, data_lo: int, data_hi: int) -> Skeleton:
    """EXACT S2 projection onto data qubits ``[data_lo, data_hi]`` (a).

    Sub-grid = detector chains ``[data_lo, data_hi - 1]``, all layers. The
    registered S2 rule applies COMPONENT-WISE (FIX ROUND 2026-06-10): a
    component with >= 1 in-grid detector survives; a two-detector component
    with one detector outside becomes a weight-1 boundary edge at the
    survivor; a component with no in-grid detector is dropped; an instruction
    survives iff >= 1 component survives, with the SAME probability (the slot
    is the instruction). Restriction at the full chain
    (``data_lo == skel.data_lo``, all chains inside) is the identity (P1c).

    Sub-observable (M4-B 2.3(4)): leftmost data qubit ``data_lo`` final readout
    XOR sweep reference. When the left edge moves (``data_lo > skel.data_lo``),
    L0 is carried per-component by exactly the components crossing the left
    cut (one detector at chain < ``data_lo``, one inside) -- on the
    repetition-code matching graph these are precisely the
    data-qubit-``data_lo`` mechanisms; all fully-inside components then carry
    no observable. When the left edge is unchanged, surviving components keep
    their original flags (the observable is the same physical bit); dropping
    an observable-carrying component in that case would silently change the
    observable and raises instead (never expected on the rep-code release --
    L0 mechanisms live at the LEFT boundary, right-side cuts cannot drop them).

    Coordinate convention (B-17): surviving detectors keep their SOURCE
    annotations UNCHANGED (the sub-DEM's ``detector(...)`` line is the device
    annotation verbatim; only the detector index re-densifies at emission).
    Full restriction is therefore the identity on ``coords`` too (P1c).
    Canonical decode-facing ``(chain, layer)`` annotations are a separate,
    explicit transform: ``with_grid_coordinates``.
    """

    data_lo = int(data_lo)
    data_hi = int(data_hi)
    if not 0 <= data_lo < data_hi <= grid.num_chains:
        raise ValueError(
            f"data range [{data_lo}, {data_hi}] invalid for {grid.num_chains} chains "
            f"(data qubits 0..{grid.num_chains})"
        )
    chain_lo, chain_hi = data_lo, data_hi - 1
    chain = grid.det_to_chain
    preserve_obs = data_lo == skel.data_lo
    new_dets: list = []
    new_obs: list = []
    new_comps: list = []
    new_p: list = []
    new_ext: list = []
    ext = skel.extended_mask
    for i in range(skel.num_errors):
        kept_comps: list = []
        for comp_dets, comp_obs in skel.comps[i]:
            inside = tuple(
                d for d in comp_dets if chain_lo <= int(chain[int(d)]) <= chain_hi
            )
            if not inside:
                if preserve_obs and comp_obs:
                    raise ValueError(
                        f"projection [{data_lo}, {data_hi}) drops an observable-"
                        f"carrying component of error #{i} while the left edge is "
                        "unchanged -- the sub-observable would silently change "
                        "(unexpected on the rep-code release; finding, not a merge)"
                    )
                continue
            if preserve_obs:
                comp_obs_new = comp_obs
            else:
                crosses_left = any(int(chain[int(d)]) < chain_lo for d in comp_dets)
                comp_obs_new = (0,) if crosses_left else ()
            kept_comps.append((inside, comp_obs_new))
        if not kept_comps:
            continue
        new_comps.append(tuple(kept_comps))
        new_dets.append(tuple(d for cd, _ in kept_comps for d in cd))
        new_obs.append(tuple(o for _, co in kept_comps for o in co))
        new_p.append(float(skel.p[i]))
        if ext is not None:
            new_ext.append(bool(ext[i]))
    mask = (chain >= chain_lo) & (chain <= chain_hi)
    detector_ids = np.flatnonzero(mask).astype(np.int64)
    new_coords = None
    if skel.coords is not None:
        # B-17 passthrough: each surviving detector keeps its source annotation
        local_of = {int(g): i for i, g in enumerate(skel.detector_ids)}
        new_coords = tuple(skel.coords[local_of[int(d)]] for d in detector_ids)
    return Skeleton(
        dets=tuple(new_dets),
        obs=tuple(new_obs),
        p=np.asarray(new_p, dtype=np.float64),
        detector_ids=detector_ids,
        num_detectors_full=skel.num_detectors_full,
        data_lo=data_lo,
        data_hi=data_hi,
        source=skel.source,
        extended_mask=np.asarray(new_ext, dtype=bool) if ext is not None else None,
        comps=tuple(new_comps),
        coords=new_coords,
    )


def window_skeleton(skel: Skeleton, grid: DetectorGrid, window: int) -> Skeleton:
    """The M2/M3 window ``w`` as a d=5 sub-repetition-code (S2 instrument ii):
    data qubits ``w+1 .. w+5`` => the 4 fully-interior detector columns
    ``w+1 .. w+4``; boundary measure columns dropped."""

    w = int(window)
    return subchain_skeleton(skel, grid, w + 1, w + 5)


def with_grid_coordinates(skel: Skeleton, grid: DetectorGrid) -> Skeleton:
    """Canonical decode-facing coordinate annotations (B-17): replace
    ``coords`` with the GLOBAL integral ``(chain, layer)`` grid rank of each
    detector in ``detector_ids`` order -- coordinate[0] = chain,
    coordinate[-1] = layer, exactly the ``m4_decode.SpaceEdgeGeometry``
    contract (F-B2-4). Required before emitting any A3c window/subchain DEM:
    the DEVICE annotations captured from the shipped DEM do NOT satisfy the
    contract (x is not the chain rank; the trailing t is not the dense layer
    rank -- measured 2026-06-10, see the module docstring). GLOBAL ranks keep
    the A3c qubit keys aligned with ``two_pass_table``'s data-qubit indexing
    via the B-16 adaptor ``g -> (g-1, g)``. Everything except ``coords`` is
    unchanged (the probability column, comps, observables and detector set
    are untouched -- this is an annotation swap, never a structure edit)."""

    coords = tuple(
        (float(grid.det_to_chain[int(d)]), float(grid.det_to_layer[int(d)]))
        for d in skel.detector_ids
    )
    return replace(skel, coords=coords)


def disjoint_partitions(d_prime: int, *, distance: int = FULL_DISTANCE) -> list:
    """MAXIMAL DISJOINT sub-chain partitions of the gate instrument (S2 (i)).

    Left-packed contiguous data ranges ``[k*d', k*d' + d' - 1]`` for
    ``k = 0 .. floor(distance/d') - 1`` (declared offset convention, (c),
    recorded at composition freeze). For ``distance = 29``: d'=5 -> 5
    positions, 7 -> 4, 9 -> 3, 11 -> 2, 13 -> 2, 15..21 -> 1 (the registered
    counts). The hot-region flag lives in ``partition_table``.
    """

    d_prime = int(d_prime)
    if d_prime < 2 or d_prime > int(distance):
        raise ValueError(f"d'={d_prime} outside [2, {distance}]")
    count = int(distance) // d_prime
    return [(k * d_prime, k * d_prime + d_prime - 1) for k in range(count)]


def partition_contains_hot(data_lo: int, data_hi: int) -> bool:
    """True when the sub-chain's measure range ``[data_lo, data_hi - 1]`` touches
    the M2-located hot pair chains (18, 21) (the {15,19}/(18,21) region flag)."""

    return any(int(data_lo) <= c <= int(data_hi) - 1 for c in HOT_PAIR_CHAINS)


def partition_table(d_prime: int, *, distance: int = FULL_DISTANCE) -> list:
    """``disjoint_partitions`` + declared names/offsets + the advance hot flag (S2)."""

    rows = []
    for k, (lo, hi) in enumerate(disjoint_partitions(d_prime, distance=distance)):
        rows.append(
            {
                "name": f"d{int(d_prime)}_pos{k}",
                "data_lo": lo,
                "data_hi": hi,
                "measure_lo": lo,
                "measure_hi": hi - 1,
                "hot": partition_contains_hot(lo, hi),
            }
        )
    return rows


# ---------------------------------------------------------------- frozen-fit access (S11)


def load_frozen_cache(path) -> dict:
    """READ-ONLY loader for the frozen M3 fit cache (zero new fits, S11)."""

    import torch

    from qec_twin.hardware import m3_report  # noqa: F401  (FitRecord unpickling)

    return torch.load(str(path), weights_only=False)


def select_frozen_records(cache: dict, windows, *, basis: str | None = None, split: str = "full"):
    """Per window, the FROZEN record with the lower train cross-entropy (the
    registered M3 seed-selection rule). Returns ``({window: record}, keys_used)``.

    ``cache`` is either the raw m3 fit cache (string keys
    ``"{basis}/{window}/{seed}/{split}"`` -- then ``basis`` is required) or an
    already-selected ``{window: record}`` mapping (passed through verbatim).
    A missing window raises loudly: M4 never fits (S11).
    """

    if cache and all(not isinstance(k, str) for k in cache):
        selected = {}
        for w in windows:
            if int(w) not in cache:
                raise KeyError(f"window {int(w)} missing from the pre-selected record map")
            selected[int(w)] = cache[int(w)]
        return selected, tuple(f"<direct>/{w}" for w in sorted(selected))
    if basis is None:
        raise ValueError("raw m3 fit cache supplied -- basis= is required for key selection")
    selected = {}
    keys_used: list = []
    for w in windows:
        prefix = [str(basis), str(int(w))]
        candidates = [
            (k, r)
            for k, r in cache.items()
            if isinstance(k, str)
            and k.split("/")[:2] == prefix
            and k.split("/")[3] == str(split)
        ]
        if not candidates:
            raise KeyError(
                f"no frozen fit for {basis}/{int(w)}/{split} in the cache -- "
                "ZERO new fits is registration-binding (S11)"
            )
        key, record = min(candidates, key=lambda kr: float(kr[1].ce_per_block))
        selected[int(w)] = record
        keys_used.append(key)
    return selected, tuple(keys_used)


def data_owner_windows(g: int, windows) -> tuple:
    """Windows owning data position ``g`` under the registered interior filter:
    local position ``g - w - 1`` in {1, 2, 3} (0-based; <= 3 owners)."""

    return tuple(int(w) for w in windows if 1 <= int(g) - int(w) - 1 <= 3)


def measure_owner_windows(c: int, windows) -> tuple:
    """Windows owning measure chain ``c``: the 4 fully-interior detector columns
    ``w+1 .. w+4`` (local 0..3; <= 4 owners)."""

    return tuple(int(w) for w in windows if 0 <= int(c) - int(w) - 1 <= 3)


def _twin_parameter_entries(records: dict, windows):
    """Raw per-owner parameter lists: data ``g -> [(w, p01, p10)]``, measure
    ``c -> [(w, q_eff)]`` -- ownership filter applied (S5)."""

    data_entries: dict = {}
    meas_entries: dict = {}
    for w in sorted(int(x) for x in windows):
        record = records[w]
        markov = np.asarray(record.markov, dtype=np.float64)
        q_eff = np.asarray(record.q_eff, dtype=np.float64)
        for k in OWNED_DATA_LOCAL:
            data_entries.setdefault(w + 1 + k, []).append((w, float(markov[k, 0]), float(markov[k, 1])))
        for k in OWNED_MEASURE_LOCAL:
            meas_entries.setdefault(w + 1 + k, []).append((w, float(q_eff[k])))
    return data_entries, meas_entries


def two_pass_table(cache: dict, windows, *, basis: str | None = None, split: str = "full") -> dict:
    """A3c input table: per data qubit ``g -> (r_hat, R_hat)``, each the MEDIAN
    over owning windows of the per-window exact values (S4 A3c; the exact
    identity ``P(flip_{t+1}|flip_t) = p01 p10 / r = r * R`` (a) is consumed by
    B2's two-pass reweight ``r -> min(r*R, 1/2 - eps)``)."""

    records, _ = select_frozen_records(cache, windows, basis=basis, split=split)
    data_entries, _ = _twin_parameter_entries(records, windows)
    table = {}
    for g in sorted(data_entries):
        values = data_entries[g]
        table[g] = (
            float(np.median([r_hat(p01, p10) for _, p01, p10 in values])),
            float(np.median([R_hat(p01, p10) for _, p01, p10 in values])),
        )
    return table


# ---------------------------------------------------------------- arms (S4)


def arm_naive(skel: Skeleton) -> np.ndarray:
    """A1: the skeleton's own shipped-SI1000 probability column (S4)."""

    return skel.p.copy()


def _pooled_or_resolved_entry(
    moments: dict, key, row: int, col: int, layer_lo: int, layer_hi: int
) -> tuple:
    """Spitz-exact entry for one pair class/location: bulk => pooled moments over
    rows ``[layer_lo, layer_hi - dt]`` (M3 convention: pool moments FIRST, then
    invert); outside the bulk window => the layer-resolved per-entry value.
    Returns ``(raw_value, is_bulk)``."""

    mi, mj, mij = moments[key]
    dt = key[1]
    bulk = layer_lo <= row and row + dt <= layer_hi and layer_hi - dt >= layer_lo
    if bulk:
        rows = slice(layer_lo, layer_hi - dt + 1)
        raw = spitz_pij_exact(
            np.float64(mi[rows, col].mean()),
            np.float64(mj[rows, col].mean()),
            np.float64(mij[rows, col].mean()),
        )
    else:
        raw = spitz_pij_exact(
            np.float64(mi[row, col]), np.float64(mj[row, col]), np.float64(mij[row, col])
        )
    return float(raw), bool(bulk)


def detection_fraction_global(counts: PairCounts, grid: DetectorGrid) -> np.ndarray:
    """Measured per-detector firing fraction indexed by GLOBAL detector id
    (the P1h ``train_detection_fraction`` input)."""

    f = np.empty(grid.num_layers * grid.num_chains, dtype=np.float64)
    f[grid.grid.ravel()] = (counts.grid_counts / float(counts.num_shots)).ravel()
    return f


def arm_pij(
    counts: PairCounts,
    grid: DetectorGrid,
    skel: Skeleton,
    *,
    layer_lo: int = BULK_LAYER_LO,
    layer_hi: int = BULK_LAYER_HI,
    clamp_lo: float = CLAMP_LO,
    clamp_hi: float = CLAMP_HI,
    return_report: bool = False,
):
    """A2: Spitz Eq. 13 EXACT train estimates written onto the skeleton support.

    Bulk layers ``[layer_lo, layer_hi]`` are layer-pooled; outside is
    layer-resolved (S5 unowned-fill rule: the M1-P6 transient keeps its
    measured profile). Pair entries clamp to ``[clamp_lo, clamp_hi]`` (c).
    Weight-1 slots: mean-matching half-edges -- at each site carrying slots the
    total single mass solves ``(1 - 2 s) * prod_other (1 - 2 p_e) = 1 - 2 f_site``
    with the measured ``f_site`` (bulk-pooled inside, layer-resolved outside)
    and the product running over EVERY other incident instruction (pairs and
    decomposed instructions alike), distributed over the site's slots via the
    merged-edge identity. Composed site marginals at slot-carrying sites
    therefore reproduce the measured detection fraction EXACTLY (the M3
    construction extended to the graph).

    DECOMPOSED instructions (conservative reading ADJUDICATED ACCEPTED, M4
    PRE-RUN AMENDMENT 1 ruling 15): the pairwise Spitz estimator does not
    define a multi-component mechanism, so those slots carry the shipped
    SI1000 probability (clamped) -- the SAME value every other constructed
    arm carries there, so they cancel out of every registered contrast.
    """

    moments = _class_moment_planes(counts, grid)
    m_grid = counts.grid_counts / float(counts.num_shots)
    sites = error_sites(skel, grid)
    groups = _signature_groups(skel)
    probs = np.empty(skel.num_errors, dtype=np.float64)
    report = {
        "pair_low_clip": 0,
        "pair_high_clip": 0,
        "single_low_clip": 0,
        "single_high_clip": 0,
        "unsupported_class": 0,
        "bulk_pooled_groups": 0,
        "layer_resolved_groups": 0,
        "w1_sites": 0,
        "w1_slots": 0,
        "duplicate_signature_groups": 0,
        "decomposed_passthrough": 0,
    }
    w1_groups: list = []
    for sig, idxs in groups.items():
        if len(idxs) > 1:
            report["duplicate_signature_groups"] += 1
        s = sites[idxs[0]]
        if s.num_components > 1:
            # conservative passthrough (see docstring): shipped SI1000 value,
            # clamped -- identical across every constructed arm by design
            for i in idxs:
                probs[i] = min(max(float(skel.p[i]), clamp_lo), clamp_hi)
            report["decomposed_passthrough"] += len(idxs)
            continue
        if s.arity == 1:
            w1_groups.append((sig, idxs))
            continue
        if s.key not in moments:
            report["unsupported_class"] += 1
            _write_group(probs, idxs, clamp_lo)
            continue
        raw, bulk = _pooled_or_resolved_entry(moments, s.key, s.row, s.col, layer_lo, layer_hi)
        report["bulk_pooled_groups" if bulk else "layer_resolved_groups"] += 1
        value = min(max(raw, clamp_lo), clamp_hi)
        if raw < clamp_lo:
            report["pair_low_clip"] += 1
        elif raw > clamp_hi:
            report["pair_high_clip"] += 1
        _write_group(probs, idxs, value)

    # mean-matching half-edges at weight-1 sites (after every pair is set)
    site_slots: dict = {}
    for sig, idxs in w1_groups:
        s = sites[idxs[0]]
        site_slots.setdefault((s.row, s.col), []).extend(idxs)
    site_prod = {site: 1.0 for site in site_slots}
    layer_of = grid.det_to_layer
    chain_of = grid.det_to_chain
    # the product runs over every incident instruction EXCEPT the singles being
    # solved: pairs AND decomposed passthroughs alike (a decomposed instruction
    # fires every flattened detector, so it factors into each touched site)
    solved = {i for _, idxs in w1_groups for i in idxs}
    for i in range(skel.num_errors):
        if i in solved:
            continue
        for d in skel.dets[i]:
            site = (int(layer_of[int(d)]), int(chain_of[int(d)]))
            if site in site_prod:
                site_prod[site] *= 1.0 - 2.0 * probs[i]
    report["w1_sites"] = len(site_slots)
    for site, idxs in site_slots.items():
        l, c = site
        if layer_lo <= l <= layer_hi:
            f_site = float(m_grid[layer_lo : layer_hi + 1, c].mean())
        else:
            f_site = float(m_grid[l, c])
        prod = max(site_prod[site], NUMERICAL_ZERO)
        raw = 0.5 * (1.0 - (1.0 - 2.0 * f_site) / prod)
        s_total = min(max(raw, clamp_lo), clamp_hi)
        if raw < clamp_lo:
            report["single_low_clip"] += 1
        elif raw > clamp_hi:
            report["single_high_clip"] += 1
        report["w1_slots"] += len(idxs)
        _write_group(probs, idxs, s_total)
    if return_report:
        return probs, report
    return probs


def arm_twin_static(
    cache: dict,
    windows,
    grid: DetectorGrid,
    pij_probs: np.ndarray,
    *,
    skel: Skeleton,
    basis: str | None = None,
    split: str = "full",
    layer_lo: int = BULK_LAYER_LO,
    layer_hi: int = BULK_LAYER_HI,
):
    """A3 twin-static: the S5 composition from FROZEN M3 train fits (verbatim).

    SPACE(j, bulk) <- ``r_hat_j`` (median over owning windows); TIME(i, bulk)
    <- ``q_eff_i`` (median over owning windows); EVERY other cell -- chain
    ends, the {15,19} region, boundary measures, layers outside
    ``[layer_lo, layer_hi]``, diagonals, weight-1 boundaries, decomposed
    instructions (never twin-owned -- conservative ambiguity reading, see the
    module docstring), unsupported classes -- copies ``pij_probs`` IDENTICALLY
    (attribution by construction).
    ``f_hat = r*R`` is never assigned: every space write passes
    ``assert_marginal_not_conditional``.

    Returns ``(probs, ownership_table)``; the table carries owners/medians per
    cell, the unowned-category census, the assigned mask, the guard outcome and
    the frozen cache keys consumed (G2 manifest inputs).
    """

    records, keys_used = select_frozen_records(cache, windows, basis=basis, split=split)
    pij_probs = np.asarray(pij_probs, dtype=np.float64)
    if pij_probs.shape != (skel.num_errors,):
        raise ValueError(f"pij column shape {pij_probs.shape} != ({skel.num_errors},)")
    probs = pij_probs.copy()
    sites = error_sites(skel, grid)
    groups = _signature_groups(skel)

    data_entries, meas_entries = _twin_parameter_entries(records, windows)
    space_cells: dict = {}
    for g, values in data_entries.items():
        space_cells[g] = {
            "owners": tuple(w for w, _, _ in values),
            "r_hat": float(np.median([r_hat(p01, p10) for _, p01, p10 in values])),
            "f_hat": float(np.median([f_hat(p01, p10) for _, p01, p10 in values])),
            "R_hat": float(np.median([R_hat(p01, p10) for _, p01, p10 in values])),
            "num_edges": 0,
        }
    time_cells: dict = {}
    for c, values in meas_entries.items():
        time_cells[c] = {
            "owners": tuple(w for w, _ in values),
            "q_eff": float(np.median([q for _, q in values])),
            "num_edges": 0,
        }

    assigned = np.zeros(skel.num_errors, dtype=bool)
    unowned_census = {
        "weight1": 0,
        "diagonal": 0,
        "decomposed": 0,
        "out_of_bulk_layers": 0,
        "chain_end_or_gap_space": 0,
        "boundary_or_gap_measure": 0,
        "unsupported_by_twin_class": 0,
    }
    guard_checks = 0
    for sig, idxs in groups.items():
        s = sites[idxs[0]]
        if s.num_components > 1:
            # decomposed instructions are NEVER twin-owned (conservative
            # reading ADJUDICATED ACCEPTED, amendment 1 ruling 15): they
            # keep the pij arm's value identically, like every unowned cell
            unowned_census["decomposed"] += len(idxs)
            continue
        if s.arity == 1:
            unowned_census["weight1"] += len(idxs)
            continue
        di, dt, _ = s.key
        if di > 0 and dt > 0:
            unowned_census["diagonal"] += len(idxs)
            continue
        if di == 1 and dt == 0:
            g = s.col + 1
            if not (layer_lo <= s.row <= layer_hi):
                unowned_census["out_of_bulk_layers"] += len(idxs)
                continue
            if g not in space_cells:
                unowned_census["chain_end_or_gap_space"] += len(idxs)
                continue
            cell = space_cells[g]
            assert_marginal_not_conditional(
                cell["r_hat"], cell["r_hat"], cell["f_hat"], cell["R_hat"],
                context=f"(data {g})",
            )
            guard_checks += 1
            _write_group(probs, idxs, cell["r_hat"])
            cell["num_edges"] += len(idxs)
            assigned[idxs] = True
            continue
        if di == 0 and dt == 1:
            c = s.col
            if not (layer_lo <= s.row and s.row + 1 <= layer_hi):
                unowned_census["out_of_bulk_layers"] += len(idxs)
                continue
            if c not in time_cells:
                unowned_census["boundary_or_gap_measure"] += len(idxs)
                continue
            cell = time_cells[c]
            _write_group(probs, idxs, cell["q_eff"])
            cell["num_edges"] += len(idxs)
            assigned[idxs] = True
            continue
        unowned_census["unsupported_by_twin_class"] += len(idxs)

    # {15,19}-region disclosure: cells whose ONLY interior owners would have been
    # the M2-excluded hot windows (S5 lists the region among the unowned fills).
    hot_only_space = tuple(
        g
        for g in range(grid.num_chains + 1)
        if data_owner_windows(g, HOT_WINDOWS) and g not in space_cells
    )
    hot_only_time = tuple(
        c
        for c in range(grid.num_chains)
        if measure_owner_windows(c, HOT_WINDOWS) and c not in time_cells
    )

    ownership_table = {
        "windows": tuple(sorted(int(w) for w in windows)),
        "basis": basis,
        "split": split,
        "cache_keys": keys_used,
        "bulk_layers": (int(layer_lo), int(layer_hi)),
        "space": space_cells,
        "time": time_cells,
        "assigned_mask": assigned,
        "num_assigned": int(assigned.sum()),
        "num_unowned": int((~assigned).sum()),
        "unowned_census": unowned_census,
        "unowned_identical_to_pij": bool(np.array_equal(probs[~assigned], pij_probs[~assigned])),
        "hot_region_disclosure": {
            "hot_windows": tuple(HOT_WINDOWS),
            "hot_pair_chains": HOT_PAIR_CHAINS,
            "space_cells_unowned_only_because_hot_excluded": hot_only_space,
            "time_cells_unowned_only_because_hot_excluded": hot_only_time,
        },
        "guard": {
            "rule": "f_hat = r*R never assigned (S5 registered prohibition)",
            "space_groups_checked": guard_checks,
            "passed": True,  # any violation raises before this table is built
        },
    }
    return probs, ownership_table


# ---------------------------------------------------------------- A3b Spitz-of-the-twin


def _twin_site_char(c: int, r_of, q_of) -> float | None:
    """``E[(-1)^{x}] = (1-2 r_c)(1-2 r_{c+1})(1-2 q_c)^2`` for the detector at
    chain ``c`` (data qubits c, c+1); None when a parameter is uncovered."""

    ra, rb, q = r_of(c), r_of(c + 1), q_of(c)
    if ra is None or rb is None or q is None:
        return None
    return (1.0 - 2.0 * ra) * (1.0 - 2.0 * rb) * (1.0 - 2.0 * q) ** 2


def _twin_pair_value(site_a, site_b, pair_of, q_of) -> float | None:
    """Twin-implied Spitz value for the detector pair ``site_a, site_b`` (a).

    Model: ``x_i(t) = F_i(t) XOR F_{i+1}(t) XOR n_i(t) XOR n_i(t-1)`` with
    independent stationary Markov data-flip chains F and iid record flips n.
    Shared same-layer data flips cancel exactly; shared lagged data flips carry
    ``(1-2r)^2 + 4 Cov(dt)`` with the exact Markov autocovariance; a shared
    record flip (time pairs, dt=1) leaves ``(1-2q)^2``. The exact Eq. 13
    inversion of these moments recovers shared-component probabilities exactly
    (q for dt=1 time pairs, r for space pairs) and otherwise emits the
    DEM-expressible two-point shadow of bunching. Returns None when any needed
    parameter is uncovered.
    """

    (la, ca), (lb, cb) = sorted((tuple(site_a), tuple(site_b)))
    dt = lb - la
    data_a = (ca, ca + 1)
    data_b = (cb, cb + 1)
    needed = sorted(set(data_a) | set(data_b))
    shared = set(data_a) & set(data_b)
    factors = 1.0
    for g in needed:
        pair = pair_of(g)
        if pair is None:
            return None
        p01, p10 = pair
        r = r_hat(p01, p10)
        if g in shared:
            if dt == 0:
                continue  # same-layer shared flip cancels exactly
            factors *= (1.0 - 2.0 * r) ** 2 + 4.0 * markov_flip_cov(p01, p10, dt)
        else:
            factors *= 1.0 - 2.0 * r
    qa, qb = q_of(ca), q_of(cb)
    if qa is None or qb is None:
        return None
    if ca == cb:
        factors *= (1.0 - 2.0 * qa) ** (2 if dt == 1 else 4)
    else:
        factors *= (1.0 - 2.0 * qa) ** 2 * (1.0 - 2.0 * qb) ** 2

    def r_of(g):
        pair = pair_of(g)
        return None if pair is None else r_hat(*pair)

    char_a = _twin_site_char(ca, r_of, q_of)
    char_b = _twin_site_char(cb, r_of, q_of)
    if char_a is None or char_b is None:
        return None
    m_a = 0.5 * (1.0 - char_a)
    m_b = 0.5 * (1.0 - char_b)
    m_ab = 0.25 * (1.0 - char_a - char_b + factors)
    return float(spitz_pij_exact(np.float64(m_a), np.float64(m_b), np.float64(m_ab)))


def arm_spitz_of_twin(
    cache: dict,
    windows,
    grid: DetectorGrid,
    skel: Skeleton,
    *,
    basis: str | None = None,
    split: str = "full",
    pij_probs: np.ndarray | None = None,
    layer_lo: int = BULK_LAYER_LO,
    layer_hi: int = BULK_LAYER_HI,
    clamp_lo: float = CLAMP_LO,
    clamp_hi: float = CLAMP_HI,
    return_report: bool = False,
):
    """A3b secondary (claim-separated, S4): twin-implied two-point detector
    statistics pushed through the SAME Spitz Eq. 13 inversion on the SAME
    skeleton support, with twin-implied mean-matching boundaries.

    Per data qubit the model point is ``(median p01, median p10)`` over owning
    windows (the primitive Markov pair must stay jointly coherent for the
    autocovariance; this differs from A3's median-of-derived r_hat by at most
    median-reordering -- flagged in the build report). Cells whose parameter
    set is not fully owned (or outside the bulk window) copy ``pij_probs``
    identically, mirroring the A3 attribution rule; ``pij_probs`` is therefore
    required whenever such cells exist.
    """

    records, keys_used = select_frozen_records(cache, windows, basis=basis, split=split)
    data_entries, meas_entries = _twin_parameter_entries(records, windows)
    pair_med = {
        g: (
            float(np.median([p01 for _, p01, _ in v])),
            float(np.median([p10 for _, _, p10 in v])),
        )
        for g, v in data_entries.items()
    }
    q_med = {c: float(np.median([q for _, q in v])) for c, v in meas_entries.items()}

    def pair_of(g):
        return pair_med.get(int(g))

    def q_of(c):
        return q_med.get(int(c))

    sites = error_sites(skel, grid)
    groups = _signature_groups(skel)
    layer_of = grid.det_to_layer
    chain_of = grid.det_to_chain
    probs = np.full(skel.num_errors, np.nan, dtype=np.float64)
    report = {
        "twin_implied_groups": 0,
        "fallback_groups": 0,
        "twin_w1_sites": 0,
        "fallback_w1_groups": 0,
        "decomposed_fallback_groups": 0,
        "low_clip": 0,
        "high_clip": 0,
        "cache_keys": keys_used,
    }
    fallback_idxs: list = []
    w1_groups: list = []
    for sig, idxs in groups.items():
        s = sites[idxs[0]]
        if s.num_components > 1:
            # decomposed: never twin-implied (mirrors the A3 attribution rule;
            # the pij arm carries the SI1000 passthrough there, so all arms agree)
            fallback_idxs.extend(idxs)
            report["fallback_groups"] += 1
            report["decomposed_fallback_groups"] += 1
            continue
        if s.arity == 1:
            w1_groups.append((sig, idxs))
            continue
        value = None
        if layer_lo <= s.row and s.row + s.dt <= layer_hi:
            d_a, d_b = (int(d) for d in skel.dets[idxs[0]])
            value = _twin_pair_value(
                (int(layer_of[d_a]), int(chain_of[d_a])),
                (int(layer_of[d_b]), int(chain_of[d_b])),
                pair_of,
                q_of,
            )
        if value is None:
            fallback_idxs.extend(idxs)
            report["fallback_groups"] += 1
            continue
        clipped = min(max(value, clamp_lo), clamp_hi)
        if value < clamp_lo:
            report["low_clip"] += 1
        elif value > clamp_hi:
            report["high_clip"] += 1
        _write_group(probs, idxs, clipped)
        report["twin_implied_groups"] += 1

    # weight-1 slots: twin-implied mean-matching where the site is covered
    site_slots: dict = {}
    for sig, idxs in w1_groups:
        s = sites[idxs[0]]
        site_slots.setdefault((s.row, s.col), []).extend(idxs)
    twin_w1: dict = {}
    for site, idxs in site_slots.items():
        l, c = site
        char = None
        if layer_lo <= l <= layer_hi:
            char = _twin_site_char(
                c, lambda g: (None if pair_of(g) is None else r_hat(*pair_of(g))), q_of
            )
        if char is None:
            fallback_idxs.extend(idxs)
            report["fallback_w1_groups"] += 1
        else:
            twin_w1[site] = (idxs, 0.5 * (1.0 - char))

    if fallback_idxs:
        if pij_probs is None:
            raise ValueError(
                f"A3b: {len(fallback_idxs)} instructions lie outside the twin-covered "
                "set -- pij_probs= is required (unowned cells copy the pij arm "
                "identically, the registered attribution rule)"
            )
        pij_probs = np.asarray(pij_probs, dtype=np.float64)
        if pij_probs.shape != (skel.num_errors,):
            raise ValueError(f"pij column shape {pij_probs.shape} != ({skel.num_errors},)")
        for i in fallback_idxs:
            probs[i] = pij_probs[i]

    if twin_w1:
        site_prod = {site: 1.0 for site in twin_w1}
        # every incident instruction EXCEPT the singles being solved factors in
        # (pairs and decomposed fallbacks alike -- flattened detector incidence)
        solved = {i for idxs, _ in twin_w1.values() for i in idxs}
        for i in range(skel.num_errors):
            if i in solved:
                continue
            for d in skel.dets[i]:
                site = (int(layer_of[int(d)]), int(chain_of[int(d)]))
                if site in site_prod:
                    site_prod[site] *= 1.0 - 2.0 * probs[i]
        for site, (idxs, m_site) in twin_w1.items():
            prod = max(site_prod[site], NUMERICAL_ZERO)
            raw = 0.5 * (1.0 - (1.0 - 2.0 * m_site) / prod)
            s_total = min(max(raw, clamp_lo), clamp_hi)
            if raw < clamp_lo:
                report["low_clip"] += 1
            elif raw > clamp_hi:
                report["high_clip"] += 1
            _write_group(probs, idxs, s_total)
            report["twin_w1_sites"] += 1

    if np.isnan(probs).any():
        raise AssertionError("A3b: unfilled probability slots remain -- build bug")
    if return_report:
        return probs, report
    return probs


# ---------------------------------------------------------------- G6 support extension


def extended_skeleton(skel: Skeleton, grid: DetectorGrid, *, add_classes=None) -> Skeleton:
    """G6 support-extension DIAGNOSTIC constructor -- a SEPARATE, claim-flagged
    secondary. NEVER an input to a primary arm: the registered primaries carry
    the SI1000 skeleton verbatim (S4 STRUCTURE FREEZE, stated verbatim in the
    registration; the mirror class lives here only).

    Default extension = the mirror-diagonal class (the (di=1, dt=1) orientation
    absent from the SI1000 support; the M1 ~970x back-edge finding). Explicit
    ``add_classes`` (``(di, dt, orient)`` keys) cover the wider M1-measured
    device support (time dt 2..5 tails, space di 2..4). Added slots are
    appended AFTER the original instruction list (the original order is a
    prefix), carry no observable flag, probability placeholder 0.0 (arms must
    fill them; emission clamps to the floor), and are marked in
    ``extended_mask``.
    """

    csites = component_sites(skel, grid)
    present_keys = {cs.key for comp in csites for cs in comp if cs.arity == 2}
    if add_classes is None:
        diag_orients = {k[2] for k in present_keys if k[0] == 1 and k[1] == 1}
        add_classes = tuple((1, 1, o) for o in (1, -1) if o not in diag_orients)
    det_set = set(int(d) for d in skel.detector_ids)
    existing_pairs = {
        frozenset(cd) for comps in skel.comps for cd, _ in comps if len(cd) == 2
    }
    new_dets: list = []
    for di, dt, orient in add_classes:
        di, dt = int(di), int(dt)
        if di == 0 and dt == 0:
            raise ValueError("class (0, 0, *) is not a pair class")
        for r in range(grid.num_layers - dt):
            for c in range(grid.num_chains - di):
                if orient < 0:
                    d1 = int(grid.grid[r + dt, c])
                    d2 = int(grid.grid[r, c + di])
                else:
                    d1 = int(grid.grid[r, c])
                    d2 = int(grid.grid[r + dt, c + di])
                if d1 in det_set and d2 in det_set and frozenset((d1, d2)) not in existing_pairs:
                    new_dets.append(tuple(sorted((d1, d2))))
    base_mask = (
        skel.extended_mask
        if skel.extended_mask is not None
        else np.zeros(skel.num_errors, dtype=bool)
    )
    return Skeleton(
        dets=skel.dets + tuple(new_dets),
        obs=skel.obs + ((),) * len(new_dets),
        p=np.concatenate([skel.p, np.zeros(len(new_dets))]),
        detector_ids=skel.detector_ids,
        num_detectors_full=skel.num_detectors_full,
        data_lo=skel.data_lo,
        data_hi=skel.data_hi,
        source=skel.source + "+extended[G6-ablation-secondary]",
        extended_mask=np.concatenate([base_mask, np.ones(len(new_dets), dtype=bool)]),
        comps=skel.comps + tuple(((d, ()),) for d in new_dets),
        coords=skel.coords,  # detector set unchanged => annotations carry through
    )


def _class_label(key) -> str:
    di, dt, orient = key
    if di == 0:
        return f"time(dt={dt})"
    if dt == 0:
        return f"space(di={di})"
    return f"diag(di={di},dt={dt},orient={orient:+d})"


def support_census(arms: dict, *, grid: DetectorGrid | None = None, clamp_lo: float = CLAMP_LO) -> dict:
    """G6 support census table (a) per arm: ``arms`` maps arm name ->
    ``(Skeleton, probability_column)``. With ``grid`` the census is
    class-resolved ((di, dt, orient) labels + weight-1); without, arity-level
    only. Decomposed instructions are labeled
    ``decomposed[<class>+<class>]`` from their per-COMPONENT classification
    (the measured class breakdown of the 2,002 real-DEM decompositions reads
    straight off this census). Extended (G6 ablation) slots are counted
    separately per class."""

    def _label_one(s: ErrorSite) -> str:
        return "w1" if s.arity == 1 else _class_label(s.key)

    table: dict = {}
    for name, (skel, probs) in arms.items():
        probs = np.asarray(probs, dtype=np.float64)
        rows: dict = {}
        if grid is None:
            labels = [
                ("w1" if len(d) == 1 else "pair")
                if len(c) == 1
                else f"decomposed[{len(c)} comps]"
                for d, c in zip(skel.dets, skel.comps)
            ]
        else:
            csites = component_sites(skel, grid)
            labels = [
                _label_one(s)
                if s.num_components == 1
                else "decomposed[" + "+".join(sorted(_label_one(cs) for cs in csites[i])) + "]"
                for i, s in enumerate(error_sites(skel, grid))
            ]
        ext = skel.extended_mask
        for i, label in enumerate(labels):
            row = rows.setdefault(
                label,
                {"count": 0, "extended": 0, "at_floor": 0, "p_sum": 0.0, "p_min": np.inf, "p_max": -np.inf},
            )
            row["count"] += 1
            if ext is not None and ext[i]:
                row["extended"] += 1
            if probs[i] <= clamp_lo:
                row["at_floor"] += 1
            row["p_sum"] += float(probs[i])
            row["p_min"] = min(row["p_min"], float(probs[i]))
            row["p_max"] = max(row["p_max"], float(probs[i]))
        for row in rows.values():
            row["p_mean"] = row["p_sum"] / row["count"]
        table[name] = rows
    return table


# ---------------------------------------------------------------- P1h acceptance


@dataclass(frozen=True)
class AcceptanceResult:
    """P1h verdict; truthy iff passed (every site within ``tol`` absolute)."""

    passed: bool
    tol: float
    max_abs_dev: float
    mean_abs_dev: float
    num_out: int
    num_sites: int

    def __bool__(self) -> bool:  # pragma: no cover - trivial
        return self.passed


def composed_site_marginals(skel: Skeleton, probs: np.ndarray) -> np.ndarray:
    """Per-site composed detector marginal (a):
    ``1 - 2 f_i = prod_{e ni i} (1 - 2 p_e)`` over every incident error
    (weight-1, pair, and decomposed -- a decomposed instruction fires every
    flattened detector it lists); ordered like ``skel.detector_ids``."""

    probs = np.asarray(probs, dtype=np.float64)
    if probs.shape != (skel.num_errors,):
        raise ValueError(f"probability column shape {probs.shape} != ({skel.num_errors},)")
    local = {int(g): i for i, g in enumerate(skel.detector_ids)}
    prod = np.ones(len(skel.detector_ids), dtype=np.float64)
    for i, dets in enumerate(skel.dets):
        for d in dets:
            prod[local[int(d)]] *= 1.0 - 2.0 * probs[i]
    return 0.5 * (1.0 - prod)


def acceptance_check(
    skel: Skeleton,
    probs: np.ndarray,
    train_detection_fraction: np.ndarray,
    *,
    tol: float = ACCEPTANCE_TOL,
):
    """P1h composition acceptance pin (b, S5): composed per-site detector
    marginals within ``tol`` (registered +/-0.5%) ABSOLUTE of the measured
    train detection fraction. ``train_detection_fraction`` is per-detector,
    either in ``skel.detector_ids`` (local) order or indexed by GLOBAL
    detector id (``detection_fraction_global``); returns
    ``(marginals, AcceptanceResult)``.

    AMENDED SEMANTICS (M4 PRE-RUN AMENDMENT 1 ruling 14, recorded before the
    pins stage): the freeze stage HALTS only on the STRUCTURAL component
    (mean-matched sites exact to <= 1e-9; zero negative/NaN marginals;
    interior deviations one-signed positive, max <= 3e-2 tripwire); this
    function's +/-0.5% per-site verdict is the registered (b) BAND,
    scored-and-reported per arm -- its measured miss (A2 sample_00 X:
    6,382/28,056 sites, mean interior surplus +4.5e-3) is a REGISTERED
    FINDING, never a build bug. Silently widening ``ACCEPTANCE_TOL`` is
    FORBIDDEN; the gating split lives in the m4_report freeze stage, not
    here.
    """

    marginals = composed_site_marginals(skel, probs)
    f = np.asarray(train_detection_fraction, dtype=np.float64).ravel()
    if f.size == marginals.size:
        measured = f
    elif f.size == skel.num_detectors_full:
        measured = f[skel.detector_ids]
    else:
        raise ValueError(
            f"train_detection_fraction size {f.size} matches neither the sub-grid "
            f"({marginals.size}) nor the full numbering ({skel.num_detectors_full})"
        )
    dev = np.abs(marginals - measured)
    result = AcceptanceResult(
        passed=bool((dev <= tol).all()),
        tol=float(tol),
        max_abs_dev=float(dev.max()),
        mean_abs_dev=float(dev.mean()),
        num_out=int((dev > tol).sum()),
        num_sites=int(dev.size),
    )
    return marginals, result


# ---------------------------------------------------------------- S12 stitched hybrid


def _seam_rows(skel: Skeleton, grid: DetectorGrid, probs, ownership: dict) -> list:
    """Seam-discontinuity audit rows (G6, confined to the stitched deliverable):
    mean probabilities on the two sides of every ownership seam."""

    sites = error_sites(skel, grid)
    layer_lo, layer_hi = ownership["bulk_layers"]
    space_bulk: dict = {}
    time_bulk: dict = {}
    space_layered: dict = {}
    time_layered: dict = {}
    for i, s in enumerate(sites):
        if s.num_components != 1 or s.arity != 2:
            continue
        di, dt, _ = s.key
        if di == 1 and dt == 0:
            g = s.col + 1
            if layer_lo <= s.row <= layer_hi:
                space_bulk.setdefault(g, []).append(probs[i])
            else:
                space_layered.setdefault((g, s.row), []).append(probs[i])
        elif di == 0 and dt == 1:
            c = s.col
            if layer_lo <= s.row and s.row + 1 <= layer_hi:
                time_bulk.setdefault(c, []).append(probs[i])
            else:
                time_layered.setdefault((c, s.row), []).append(probs[i])

    def mean_of(d, key):
        return float(np.mean(d[key])) if key in d and d[key] else None

    rows: list = []
    owned_space = sorted(ownership["space"])
    owned_time = sorted(ownership["time"])
    for kind, owned, bulk in (("space", owned_space, space_bulk), ("time", owned_time, time_bulk)):
        for cell in owned:
            for nb in (cell - 1, cell + 1):
                if nb in owned or nb not in bulk:
                    continue
                a, b = mean_of(bulk, cell), mean_of(bulk, nb)
                rows.append(
                    {
                        "seam": f"{kind}:owned {cell} | pij-filled {nb} (bulk layers)",
                        "owned_mean_p": a,
                        "filled_mean_p": b,
                        "ratio": (a / b) if (a and b) else None,
                    }
                )
    for kind, owned, bulk, layered in (
        ("space", owned_space, space_bulk, space_layered),
        ("time", owned_time, time_bulk, time_layered),
    ):
        for boundary_layer, label in ((layer_lo - 1, "below-bulk"), (layer_hi + 1, "above-bulk")):
            vals_owned, vals_filled = [], []
            for cell in owned:
                if cell in bulk:
                    vals_owned.extend(bulk[cell])
                if (cell, boundary_layer) in layered:
                    vals_filled.extend(layered[(cell, boundary_layer)])
            if vals_owned and vals_filled:
                a, b = float(np.mean(vals_owned)), float(np.mean(vals_filled))
                rows.append(
                    {
                        "seam": f"{kind}:bulk-owned | layer-resolved fill at layer "
                        f"{boundary_layer} ({label})",
                        "owned_mean_p": a,
                        "filled_mean_p": b,
                        "ratio": a / b if b else None,
                    }
                )
    return rows


def stitched_hybrid(
    cache: dict,
    windows,
    grid: DetectorGrid,
    skel: Skeleton,
    *,
    counts: PairCounts | None = None,
    pij_probs: np.ndarray | None = None,
    basis: str | None = None,
    split: str = "full",
    layer_lo: int = BULK_LAYER_LO,
    layer_hi: int = BULK_LAYER_HI,
):
    """S12 deliverable: the full-chain hybrid DEM -- twin-owned cells from the
    frozen fits, EVERY unowned cell (incl. the {15,19} region) filled from the
    train pij arm, with full disclosure. Returns ``(DetectorErrorModel,
    seam_audit_table)``; the audit carries the fill disclosure, the clamp
    report, the hot-region resolution and the seam-discontinuity rows (G6:
    seam auditing is confined to this deliverable -- primaries decode
    per-subchain DEMs and no seam crosses a primary).
    """

    if pij_probs is None:
        if counts is None:
            raise ValueError("stitched_hybrid needs counts= (to build the pij fill) or pij_probs=")
        pij_probs = arm_pij(counts, grid, skel, layer_lo=layer_lo, layer_hi=layer_hi)
    twin_probs, ownership = arm_twin_static(
        cache,
        windows,
        grid,
        pij_probs,
        skel=skel,
        basis=basis,
        split=split,
        layer_lo=layer_lo,
        layer_hi=layer_hi,
    )
    dem, clamp_rep = with_probabilities(skel, twin_probs)
    seam_audit = {
        "fill_disclosure": {
            "rule": "ALL unowned cells carry the train-pij values IDENTICALLY "
            "(S5; attribution by construction); NOT SI1000 fill",
            "unowned_census": ownership["unowned_census"],
            "num_unowned": ownership["num_unowned"],
            "num_assigned": ownership["num_assigned"],
            "identical_on_unowned": ownership["unowned_identical_to_pij"],
        },
        "hot_region_disclosure": ownership["hot_region_disclosure"],
        "clamp": clamp_rep,
        "cache_keys": ownership["cache_keys"],
        "seam_rows": _seam_rows(skel, grid, twin_probs, ownership),
        "guard": ownership["guard"],
    }
    return dem, seam_audit


# ---------------------------------------------------------------- G2 freeze manifest


def dem_compose_source_sha256() -> str:
    """sha256 of this module's source file -- the G2 composition-code hash."""

    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def freeze_manifest(
    *,
    cache_keys=(),
    fill_table=None,
    clamp_table=None,
    support_table=None,
    extra=None,
) -> dict:
    """G2 one-shot composition freeze record: pinned BEFORE any decode of
    samples 05+; ANY post-hoc edit of the composition voids the run (escrow
    re-registration). Deterministic by construction (no timestamps).

    DISCLOSURE CONTRACT (C-1 condition i, adjudicated in M4 PRE-RUN AMENDMENT
    1 ruling 15): the ``fill_table`` supplied by the freeze stage MUST carry
    the decomposed-instruction census (measured: 2,002 slots, all
    decomposed[w1+w1]) together with the SI1000-passthrough rule for those
    slots (value bit-identical across A1/A2/A3/A3b => contrast-neutral by the
    S5 attribution-by-construction property; a disclosed common bias, never a
    contrast distortion). The hot-region resolution disclosure travels in the
    ownership table (C-3)."""

    return {
        "registration": "M4 PRE-REGISTRATION 2026-06-10 (docs/metric_results.md S5/G2)",
        "dem_compose_sha256": dem_compose_source_sha256(),
        "m4_seed": M4_SEED,
        "clamp": {"lo": CLAMP_LO, "hi": CLAMP_HI},
        "bulk_layers": (BULK_LAYER_LO, BULK_LAYER_HI),
        "ownership_filter": {
            "data_local_positions": OWNED_DATA_LOCAL,
            "measure_local_positions": OWNED_MEASURE_LOCAL,
            "aggregator": "median over owning windows",
        },
        "clean_windows": tuple(CLEAN_INTERIOR_WINDOWS),
        "hot_windows": tuple(HOT_WINDOWS),
        "cache_keys": tuple(sorted(str(k) for k in cache_keys)),
        "fill_table": fill_table,
        "clamp_table": clamp_table,
        "support_table": support_table,
        "extra": extra,
    }


__all__ = [
    "ACCEPTANCE_TOL",
    "AcceptanceResult",
    "BULK_LAYER_HI",
    "BULK_LAYER_LO",
    "CLAMP_HI",
    "CLAMP_LO",
    "ClampReport",
    "ErrorSite",
    "FULL_DISTANCE",
    "HOT_PAIR_CHAINS",
    "M4_SEED",
    "OWNED_DATA_LOCAL",
    "OWNED_MEASURE_LOCAL",
    "R_hat",
    "Skeleton",
    "acceptance_check",
    "arm_naive",
    "arm_pij",
    "arm_spitz_of_twin",
    "arm_twin_static",
    "assert_marginal_not_conditional",
    "component_sites",
    "composed_site_marginals",
    "data_owner_windows",
    "dem_compose_source_sha256",
    "dem_sha256",
    "detection_fraction_global",
    "disjoint_partitions",
    "error_sites",
    "extended_skeleton",
    "f_hat",
    "freeze_manifest",
    "load_frozen_cache",
    "load_skeleton",
    "markov_flip_cov",
    "measure_owner_windows",
    "partition_contains_hot",
    "partition_table",
    "r_hat",
    "roundtrip_report",
    "select_frozen_records",
    "stitched_hybrid",
    "subchain_skeleton",
    "support_census",
    "two_pass_table",
    "window_skeleton",
    "with_grid_coordinates",
    "with_probabilities",
]
