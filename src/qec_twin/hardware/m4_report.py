"""M4 decoder-prior utility driver (R2-lite, ADR 0007; registration of record:
docs/metric_results.md "M4 PRE-REGISTRATION (decoder-prior utility; recorded
2026-06-10 BEFORE build/run)", S1-S12; reviewer blueprint
docs/.reports/m4_panel/R_reviewer_verdict.md; guards G1-G9 in M4C_adversarial.md).

This module owns (build split B3): the S12 ORDER FREEZE as an explicit staged
state machine, the S3 pilot + mechanical rung selection + Lambda-hat ladder, the
S7 prediction/band tables AS DATA + scoring, the S8 statistics, P10
predict-before-measure forecasting (GPU MC sampler of the frozen M3 window twin
model), G2 manifest enforcement, G5 covariation, G7 drift, artifacts writing and
``main()``. Composition/arms live in ``dem_compose`` (B1); decoding + machinery
pins live in ``m4_decode`` (B2). Both are imported lazily so the registered
synthetic-data tests (tests/test_hardware_m4_decoder_prior.py) run standalone.

Run (console entry registered by the build, ratified R4)::

    QEC_TWIN_HW_DATA=<parent dir> python -m qec_twin.hardware.m4_report <stage>

Stages (S12, frozen order; each stage REFUSES to run out of order)::

    pins -> freeze -> pilot -> select-rung -> p10-forecast -> floor-check
         -> heldout (ONE pass) -> score -> artifacts

Committed adjudication notes (recorded with the build, BEFORE any run; every
item below is a conservative faithful reading of a registration ambiguity, never
a redesign — all flagged in docs/.reports/m4_panel/build_B3_report.md):

- RUNG-SELECTION LADDER: S3 writes "L_bar_pij,train(d')" without a basis tag
  while %dLER claims are never pooled across bases. Read: rung selection is a
  DESIGN rule, not a claim — d'* is selected once on the count-weighted
  pooled-over-bases pij ladder; per-basis ladders and per-basis argmins are
  reported alongside and a disagreement is flagged.
- EDGE-BRANCH COMPLETION: the two declared S3 edge branches cover
  "all > 0.30" and "all < 0.01". If the ladder straddles the window without
  entering it (possible only when L_bar skips [0.01, 0.30] between adjacent
  rungs), the selection falls back to the same argmin objective over all rungs,
  flagged "window-skipped" (conservative completion, reported, never silent).
- "EXACT PERMUTATION" NULL (G5): 19! permutations cannot be enumerated; the
  registered B = 1e4 (seed 20260610) Monte-Carlo draw from the permutation null
  is used and labeled as such. The cyclic-shift null IS exactly enumerable (the
  full n-element cyclic group, identity included), so it is enumerated; its
  attainable minimum p is 1/n (= 1/19 > alpha = 0.01), hence the cyclic null is
  a registered ROBUSTNESS REPORT, not the alpha-gate; "significance vanishing
  under the cyclic null" is operationalized as cyclic rank worse than top-2
  (p_cyclic > 2/n) — declared (c).
- McNEMAR "discordance near its saturation bound": operationalized as
  delta >= 0.9 * min(p_A + p_B, 2 - p_A - p_B) — declared (c).
- FLOOR CHECK (S8): baseline-only BY INTERFACE — ``floor_check`` accepts a
  mapping whose keys must be the named baseline arms; any twin-tagged key
  raises. The discordance proxy is the measured pilot A1<->A2 discordance when
  supplied (baseline-only by construction), else the conservative bound
  min(2 * L_naive, 0.5); the effective N is the SHOT count (no unit-pooling
  gain credited — conservative: a larger floor can only trigger the
  pre-registered extension, never skip it).
- DESIGN EFFECT: Kish-style, deff = (SE_shot-bootstrap / SE_iid-cell)^2 on the
  paired per-shot difference.
- P10 SAMPLER CONVENTIONS (model = the FROZEN M3 window twin, zero new fits):
  the M3 flip channel (m3_report.flip_channel_kraus: K0 diagonal, K1
  antidiagonal) acts on a computational-basis state as a CLASSICAL two-state
  Markov chain on the qubit value with transitions P(0->1) = p01,
  P(1->0) = p10; q^eff is the gauge-exact per-ancilla-round record flip ("MR
  resets clean", m3 P1g folding identity). Sampler conventions: v(0) = 0 (the
  transient layers are S5 UNOWNED cells; the M3 bulk block law is the
  stationary law this chain mixes to — M1-P6 transient ~70 rounds << the
  registered bulk cut at 80); detector layer 0 = first syndrome record; final
  layer carries readout flips only (the twin class has no final-data-readout
  DOF — unowned); observable = leftmost window data qubit final readout in the
  error frame (the sweep-reference XOR is the identity there, S2/P1b). The P10
  band is x/2 either way (b) — these conventions are recorded, not tuned.
- HELD-OUT ONCE-ONLY: ``begin_heldout`` persists the attempt BEFORE any decode;
  a crashed attempt still counts as the one pass (re-entry after a partial look
  is a look — G2: void => re-register on the escrow samples 15-19).
- DRIFT CONTEXT: samples 01-04 are context-only (design-contaminated); they are
  decoded in the SCORING stage, strictly after the one held-out pass, and never
  enter primaries.
- BURST-SHOT MAD FLAG (M4-F10): operationalized on the per-shot error count
  across units of the BASELINE arm (the only always-present per-shot burst
  proxy at decode level); with/without both reported — declared (c).
- A3c SCORING: "high-R windows" = frozen R_hat_W >= 2 (the M3 split-stable
  threshold); "~0 on w20/w21" scored as the 95% bootstrap CI containing 0 —
  declared (c) operationalizations.
- PROTOCOL TUPLE: the p_hat in (d', T, p_hat, c(s_hat)) is the comparison
  DENOMINATOR (baseline) arm's per-shot LER — the conditioning operating point.

FIX ROUND (2026-06-10, post-review; binding: docs/.reports/m4_panel/
build_R_m4_review.md SB/SD/SF + docs/metric_results.md "M4 PRE-RUN AMENDMENT 1"
rulings 14-15). Stage glue reconciled to the REAL B1/B2 APIs (B-1..B-16):

- PINS: B2 ships exactly pin_{p1a,p1b,p1d,p1e,p1f,p1g} — there is NO pin_p1c;
  P1c is B1's machinery (roundtrip_report + the full-restriction identity) and
  is wired through B1 in the pins stage. P1a byte-parity scope {00, 05-14}
  (escrow 15-19 NEVER opened); P1e/P1f scope {00, 50, 99} (ruling 15: shipped
  model vs shipped predictions — NOT held-out contamination).
- FREEZE GATE (ruling 14): the amended P1h runs on the TWIN column with A2
  reported alongside; the freeze HALTS ONLY on the STRUCTURAL component
  (mean-matched sites reproduce their target to <= 1e-9; zero negative/NaN
  marginals; interior deviation one-signed positive with max <= 3e-2 (c)
  tripwire). The registered +/-0.5% per-site band is scored-and-reported per
  arm; a miss is the REGISTERED FINDING (M3/ADR-0008-H3 back-edge tag) — never
  a halt, never a tolerance edit. "One-signed positive" is operationalized
  (declared (c)) as: no interior site composes BELOW measured by more than the
  band (an out-of-band NEGATIVE deficit contradicts the verified
  over-composition structure => build bug).
- ERROR ARRAYS: every statistic consumes XOR(decoder prediction, per-unit
  ACTUAL observable); the actual bits come from B2's fix-round helper
  ``unit_actual_observables(ds, basis, sample, units)`` with units =
  ``(data_lo, data_hi)`` INCLUSIVE data-qubit pairs (B2's landed convention:
  window w => (w+1, w+5); a d' partition => its (lo, hi); only data_lo selects
  the observable — that qubit's final readout XOR its sweep reference, S2/P1b;
  the full chain reproduces P1b bit-exactly). Samples 01-99 need B2's explicit
  ``allow_heldout=True`` — set by THIS runner only inside the held-out stage
  and the post-held-out scoring-stage 01-04 context decode (the registered
  design; module note 8). A missing helper raises loudly.
- A3c KEYS (B-16, owner B3): B1's two_pass_table keys by DATA QUBIT g; B2's
  rR_table keys by CHAIN PAIR — adapted here as {g} -> {(g-1, g)} (data qubit
  g sits between detector chains g-1 and g; boundary keys then coincide with
  B2's (min_chain-1, min_chain) convention).
- SUBCHAIN CONVENTION: B1's subchain_skeleton(skel, grid, data_lo, data_hi)
  takes data_hi INCLUSIVE (pinned by window_skeleton == subchain(w+1, w+5) and
  the full-restriction identity subchain(0, num_chains)); partition rows feed
  (data_lo, data_hi) verbatim. (The review text's literal 'hi+1' is an
  off-by-one under that convention — documented in the fix-round report.)
- SCORING (SF/change 6): the covariation is restricted to samples 05-09 even
  under the extension; drift-context samples 01-04 are decoded in the scoring
  stage as CONTEXT ONLY; the corpus RL XOR context count is wired from the
  pins-stage P1e measurement; A3b (spitz_of_twin) is scored from the saved
  held-out arrays (claim-separated secondary); the S2 sliding-window secondary
  is recorded dropped-with-documentation BEFORE held-out (it cannot be added
  afterwards); the A4 dMLE conditional carries the run-unmodified-or-drop
  attempt protocol via ``record_dmle_attempt`` (documentation hook read by the
  scoring stage; absence is a loudly-flagged open obligation, not a blocker).
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as _dt
import hashlib
import importlib.util
import json
import math
import os
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np
import torch

from qec_twin.hardware import blocks
from qec_twin.hardware.m3_report import FIT_SEEDS, _cache_key
from qec_twin.numerics import NUMERICAL_ZERO

# ---------------------------------------------------------------- S1-S3 design constants

M4_SEED = 20260610  # ratified R3: ALL new M4 randomness (frozen M3 fits keep 20260609)
BOOT_REPLICATES = 1000  # S7/S8 paired shot bootstrap
PERM_REPLICATES = 10_000  # G5 permutation null
T_ROUNDS = 1000  # S1 estimand: fixed T = 1000
NUM_DETECTOR_LAYERS = 1002  # 1 init + 1000 bulk + 1 final (dataset.py)
NUM_ANCILLA_ROUNDS = 1001

TRAIN_SAMPLE = 0
PILOT_SAMPLES = (TRAIN_SAMPLE,)  # S3: TRAIN-ONLY pilot, sample_00 ONLY
HELDOUT_PRIMARY_SAMPLES = (5, 6, 7, 8, 9)  # S1 splits: ONE pass, no re-entry
DRIFT_CONTEXT_SAMPLES = (1, 2, 3, 4)  # context only (design-contaminated)
EXTENSION_SAMPLES = (10, 11, 12, 13, 14)  # at most once, baseline-only trigger
ESCROW_SAMPLES = (15, 16, 17, 18, 19)  # G2 void-and-rerun reserve

RUNG_GRID = (5, 7, 9, 11, 13, 15, 17, 19, 21)  # S3 full pilot grid
RUNG_TARGET = 0.075  # ratified R2
RUNG_WINDOW = (0.01, 0.30)  # ratified R2
# S2 maximal disjoint partitions (positions per rung; B1 owns the named offsets)
DISJOINT_POSITIONS = {5: 5, 7: 4, 9: 3, 11: 2, 13: 2, 15: 1, 17: 1, 19: 1, 21: 1}

EPS_ABSTAIN_P = 0.45  # S1 (c): registered abstain on eps-hat when p_hat > 0.45
Z_ONE_SIDED_99 = 2.3263478740408408  # (c) one-sided 99% normal quantile

CLEAN_WINDOWS = blocks.CLEAN_INTERIOR_WINDOWS  # 19 windows = 1..21 minus {15, 19}
PILOT_ARMS = ("naive", "pij")  # S3: arms A1+A2 ONLY — the twin arm is never piloted

P10_MC_SHOTS = 100_000  # S11: 3.8e6 decode-equivalent = 19 windows x 2 bases x 1e5
P10_SEED_STRIDE = 7919  # (c) per-(basis, window) seed derivation constant

SPEARMAN_RHO_MIN = 0.4  # G5 effect floor
SPEARMAN_ALPHA = 0.01  # G5 one-sided alpha
COVARIATION_DROP_WINDOWS = (8, 20)  # G5 leverage points
A3C_HIGH_R_MIN = 2.0  # (c) "high-R windows" operationalization (M3 split-stable)
MCNEMAR_SATURATION_FRACTION = 0.9  # (c) conditioning-limited flag threshold
CYCLIC_TOP_RANK = 2  # (c) cyclic-null "significance vanishing" operationalization

# -- pins-stage registry (FIX ROUND, reviewer B-11): B2 ships exactly these
# runners; there is NO pin_p1c — P1c is B1's round-trip machinery, wired in
# _stage_pins through P1C_OWNER.
B2_PIN_RUNNERS = ("p1a", "p1b", "p1d", "p1e", "p1f", "p1g")
P1C_OWNER = "dem_compose.roundtrip_report + full-restriction identity (B1)"
P1A_SAMPLES = (TRAIN_SAMPLE,) + HELDOUT_PRIMARY_SAMPLES + EXTENSION_SAMPLES  # byte parity ONLY; escrow excluded
P1E_SAMPLES = (TRAIN_SAMPLE, 50, 99)  # registered far-corpus probes (AMENDMENT 1 ruling 15)
P1E_HALT_MISMATCH = 1e-3  # registered outer bound: mismatch > 1e-3 => HALT + degeneracy audit
P1D_PROBE_SHOTS = 2_000  # sample_00 dets slice for the P1d determinism pin (c)
GUARD_SIM_SHOTS = 20_000  # G4 sim-round-trip shots per probe arm (c)
GUARD_JITTER_SHOTS = 20_000  # G4 jitter-control sample_00 dets slice (c)

# -- AMENDMENT 1 ruling 14: the P1h split (docs/metric_results.md, recorded
# BEFORE the pins stage). Component (i) STRUCTURAL gates the freeze; component
# (ii) is the registered per-site band, scored-and-reported per arm.
P1H_BAND_TOL = 5e-3  # the registered +/-0.5% per-site band (b) — NEVER a halt
P1H_MEAN_MATCH_TOL = 1e-9  # structural (i): mean-matched sites reproduce their target
P1H_INTERIOR_MAX_DEV = 3e-2  # structural (i): catastrophe tripwire (c)
P1H_FINDING_TAG = (
    "structural composed-marginal surplus of the independent-edges format "
    "(M3 / ADR-0008-H3 back-edge)"
)

# ---------------------------------------------------------------- S7 prediction/band tables AS DATA

# PRIMARY 1 (the ADR M4 GATE) per-rung band TABLE (b)+(c), declared BEFORE the
# pilot: {basis: ((d_lo, d_hi), (band_lo_pct, band_hi_pct, central_pct))}.
GATE_RUNG_BANDS = {
    "X": (((5, 9), (2.0, 30.0, 10.0)), ((11, 15), (5.0, 35.0, 15.0)), ((17, 21), (10.0, 45.0, 25.0))),
    "Z": (((5, 9), (1.0, 25.0, 8.0)), ((11, 15), (5.0, 35.0, 15.0)), ((17, 21), (10.0, 45.0, 25.0))),
}
# PRIMARY 2 (the HEADLINE) two-sided bands (b); central +1.5% per the P1i
# gap~0 branch (RUN 2026-06-10, both bases — the +4% branch did NOT fire).
HEADLINE_BAND = {"X": (-10.0, 15.0), "Z": (-10.0, 12.0)}
HEADLINE_CENTRAL = 1.5
P1I_BRANCH = {
    "branch": "gap~0",
    "measured_gap": {"X": 5.2e-4, "Z": 1.7e-4},
    "predicted_2Rr2": {"X": 2.07e-3, "Z": 1.64e-3},
    "recorded": "2026-06-10 pre-decode (S6 P1i / I-6)",
}
LOCATED_POSITIVE_WINDOWS = (8, 9, 16, 17)  # (b) twin-vs-pij > 0
LOCATED_NONPOSITIVE_WINDOWS = (20, 21)  # (b) twin-vs-pij <= 0
PIJ_VS_NAIVE_BAND = (2.0, 25.0)  # (b) percent
DMLE_TWIN_BAND = (-10.0, 10.0)  # (b) two-sided, central 0 — the ONLY licensed head-to-head
A3C_HIGH_R_BAND = (0.0, 8.0)  # (b) percent, two-pass vs static on high-R windows
A3C_CONTROL_WINDOWS = (20, 21)  # built-in negative control: ~0
REGIME_PIN_BAND = (0.005, 0.45)  # (c) per-window pij-arm held-out LER
REGIME_PIN_MIN_WINDOWS = 16  # of 19
P10_RATIO_BAND = (0.5, 2.0)  # (b) measured/predicted
P10_MIN_FRACTION = 0.75
DRIFT_SPREAD_BAND = (2.0, 40.0)  # (b) percent, per-sample %dLER spread
FULL_CODE_RL_XOR_BAND = (0.0, 10.0)  # context (NOT a %d claim), per 1e5 shots

REVERSE_TRAP_NOTE = (
    "Pre-registered (b): a small twin-vs-naive %dLER despite the +56/+44-nat NLL "
    "blowout is NOT a failure — MWPM depends mostly on weight ratios; NLL does not "
    "map to LER and no derivation exists (S7)."
)

# G4 sim-round-trip pass rule for NON-ENUMERABLE DEMs (declared (c) completion,
# reviewer C-5 / F-B2-3; recorded in the freeze manifest extra; B2 may export
# SIM_ROUND_TRIP_PASS_RULE, which then takes precedence): a tripwire, never a band.
SIM_ROUND_TRIP_PASS_RULE = (
    "G4 sim round-trip pass rule (c, C-5): pass iff the decode completed with "
    "correct shapes AND sim_ler < raw_flip_rate AND sim_ler < 0.45; any "
    "NaN/shape/exception = pipeline bug, nothing downstream."
)

# S2 sliding-window position set (registered secondary): recorded
# dropped-with-documentation BEFORE the one held-out pass (reviewer A/S2 + change
# item 6: it must either be implemented before held-out or recorded dropped — it
# can never be added afterwards). Carried in the freeze manifest extra and the
# scored table.
SLIDING_WINDOW_SECONDARY = {
    "item": "S2 sliding-window position set (registered secondary, design-effect disclosure)",
    "status": "dropped-with-documentation",
    "recorded": "pre-held-out (FIX ROUND 2026-06-10)",
    "reason": (
        "not implemented before the ONE held-out pass; per the review it cannot be "
        "added after held-out — dropped, never silently; the maximal-disjoint "
        "primaries and the 19-window instrument are unaffected"
    ),
}

# A4 dMLE conditional protocol (ratified R4; reviewer change item 6): the
# documentation hook for the run-unmodified-or-drop attempt, written BEFORE the
# scoring stage consumes the dMLE row.
DMLE_PROTOCOL_NOTE = (
    "A4 dMLE conditional (run-unmodified-or-drop, ratified R4): the upstream "
    "DMLE-QEC baseline is ATTEMPTED at its own recommended/default settings, code "
    "unmodified (baseline discipline; version/commit declared with the numbers). "
    "Outcome 'ran' wires the dmle error arrays into the only licensed head-to-head; "
    "any other outcome documents the drop. Cross-protocol claims stay forbidden (G9)."
)

STATE_DIR_DEFAULT = "outputs/m4_state"
ARTIFACTS_DIR_DEFAULT = "outputs/m4_artifacts"
FIT_CACHE_DEFAULT = os.environ.get("QEC_TWIN_M3_FIT_CACHE", "outputs/m3_fit_cache.pt")


def _utc_stamp() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _json_default(obj):
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)  # e.g. B1 ClampReport / AcceptanceResult
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"not JSON-serializable: {type(obj)}")


def _dump_json(payload, path: Path) -> str:
    """Atomic canonical-JSON write; returns the content sha256."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, sort_keys=True, default=_json_default)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def module_source_hash(module_name: str) -> str:
    """sha256 of a module's source file (G2 composition-code hash input)."""
    spec = importlib.util.find_spec(module_name)
    if spec is None or spec.origin is None:
        raise FileNotFoundError(f"module not importable for hashing: {module_name}")
    return file_sha256(spec.origin)


def composition_source_hashes(fit_cache_path: str | Path) -> dict[str, str]:
    """G2 pin inputs: composition code hash + the frozen M3 cache bytes."""
    return {
        "qec_twin.hardware.dem_compose": module_source_hash("qec_twin.hardware.dem_compose"),
        "qec_twin.hardware.m4_decode": module_source_hash("qec_twin.hardware.m4_decode"),
        "m3_fit_cache": file_sha256(fit_cache_path),
    }


# ---------------------------------------------------------------- exact conventions (S1)


def c_of_s(s: float) -> float:
    """Compression identity c(s) = s e^{-s} / (1 - e^{-s}) (a); s = 2 eps T."""
    s = float(s)
    if math.isnan(s):
        return float("nan")
    if s < 0.0:
        raise ValueError("s = 2*eps*T must be nonnegative")
    if s < NUMERICAL_ZERO:
        return 1.0  # exact limit
    return s * math.exp(-s) / (1.0 - math.exp(-s))


def eps_inversion(p_shot: float, *, rounds: int = T_ROUNDS) -> dict:
    """Secondary per-round inversion eps = (1 - (1 - 2p)^(1/T)) / 2 (a) with the
    registered abstains: p_hat > 0.45 (c, S1) and (1 - 2p) <= 0 (M4-F10)."""
    p = float(p_shot)
    out = {
        "p_shot": p,
        "rounds": int(rounds),
        "eps": float("nan"),
        "abstain": False,
        "abstain_reason": None,
        "stationarity_caveat": True,
    }
    if p > EPS_ABSTAIN_P:
        out.update(abstain=True, abstain_reason=f"p_hat {p:.6g} > {EPS_ABSTAIN_P}")
        return out
    base = 1.0 - 2.0 * p
    if base <= 0.0:
        out.update(abstain=True, abstain_reason="1 - 2*p_hat <= 0")
        return out
    out["eps"] = 0.5 * (1.0 - base ** (1.0 / float(rounds)))
    return out


def protocol_tuple(d_prime: int, p_hat: float, *, rounds: int = T_ROUNDS) -> dict:
    """G1: every %dLER carries (d', T, p_hat, c(s_hat)); p_hat = the comparison
    denominator (baseline) arm per-shot LER (module note)."""
    inv = eps_inversion(p_hat, rounds=rounds)
    s_hat = float("nan") if inv["abstain"] else 2.0 * inv["eps"] * rounds
    return {
        "d_prime": int(d_prime),
        "T": int(rounds),
        "p_hat": float(p_hat),
        "eps_hat": inv["eps"],
        "eps_abstain": inv["abstain"],
        "eps_abstain_reason": inv["abstain_reason"],
        "s_hat": s_hat,
        "c_s_hat": c_of_s(s_hat),
        "unpowered_as_registered": bool(float(p_hat) > EPS_ABSTAIN_P),  # G1 falsifier
    }


# ---------------------------------------------------------------- S3 rung selection + Lambda ladder


def select_rung(pilot_ladder: Mapping[int, float]) -> dict:
    """S3 mechanical rule, verbatim (c, constants ratified R2):

    d'* = argmin_d' |log10 L_bar_pij,train(d') - log10 0.075| s.t.
    L_bar in [0.01, 0.30]; ties -> smaller d'. Edge branches declared: all
    rungs > 0.30 => smallest-L_bar rung, flagged conditioning-limited;
    all < 0.01 => largest-L_bar rung, flagged power-starved. Mixed straddle
    without an in-window rung => argmin objective, flagged window-skipped
    (conservative completion — module note)."""
    if not pilot_ladder:
        raise ValueError("empty pilot ladder")
    target = math.log10(RUNG_TARGET)
    rows = []
    for d in sorted(int(k) for k in pilot_ladder):
        l_bar = float(pilot_ladder[d])
        if l_bar < 0.0:
            raise ValueError(f"pilot L_bar must be non-negative, got {l_bar} at d'={d}")
        # MEASURED-ZERO cells (mechanical-fix note, 2026-06-11: the real pilot
        # measured L_bar == 0 at d' >= 17 — zero decoded errors in 1e5 shots;
        # the device beats the panel's analytic anchors, which is exactly why
        # the rule is pilot-driven). A zero cell is INELIGIBLE by the registered
        # rule (outside [0.01, 0.30]; argmin objective = +inf — it can never be
        # selected) and sorts as the smallest L_bar in the edge branches. The
        # registered rule text is untouched; raising here was a glue bug.
        rows.append(
            {
                "d_prime": d,
                "L_bar": l_bar,
                "objective": (abs(math.log10(l_bar) - target)
                              if l_bar > 0.0 else float("inf")),
                "in_window": RUNG_WINDOW[0] <= l_bar <= RUNG_WINDOW[1],
            }
        )
    if all(r["L_bar"] == 0.0 for r in rows):
        raise ValueError("every pilot rung measured zero errors — no rung is scoreable")
    feasible = [r for r in rows if r["in_window"]]
    if feasible:
        pick = min(feasible, key=lambda r: (r["objective"], r["d_prime"]))
        flag = None
    elif all(r["L_bar"] > RUNG_WINDOW[1] for r in rows):
        pick = min(rows, key=lambda r: (r["L_bar"], r["d_prime"]))
        flag = "conditioning-limited"
    elif all(r["L_bar"] < RUNG_WINDOW[0] for r in rows):
        pick = max(rows, key=lambda r: (r["L_bar"], -r["d_prime"]))
        flag = "power-starved"
    else:
        pick = min(rows, key=lambda r: (r["objective"], r["d_prime"]))
        flag = "window-skipped"
    return {
        "d_prime_star": pick["d_prime"],
        "L_bar_selected": pick["L_bar"],
        "flag": flag,
        "target": RUNG_TARGET,
        "window": list(RUNG_WINDOW),
        "table": rows,
    }


def lambda_ladder(pilot_ladder: Mapping[int, float], *, rounds: int = T_ROUNDS) -> list[dict]:
    """The free S3 deliverable: Lambda_hat(d') = eps_hat(d') / eps_hat(d'+2) per
    adjacent rung pair, via the registered inversion; abstains propagate.
    Ledgered with the stationarity caveat — never an extrapolation license."""
    rows = []
    rungs = sorted(int(k) for k in pilot_ladder)
    for d in rungs:
        if d + 2 not in pilot_ladder:
            continue
        lo = eps_inversion(float(pilot_ladder[d]), rounds=rounds)
        hi = eps_inversion(float(pilot_ladder[d + 2]), rounds=rounds)
        abstain = bool(lo["abstain"] or hi["abstain"])
        lam = float("nan")
        if not abstain and hi["eps"] > NUMERICAL_ZERO:
            lam = lo["eps"] / hi["eps"]
        rows.append(
            {
                "d_lo": d,
                "d_hi": d + 2,
                "eps_lo": lo["eps"],
                "eps_hi": hi["eps"],
                "lambda_hat": lam,
                "abstain": abstain,
                "abstain_reason": lo["abstain_reason"] or hi["abstain_reason"],
                "stationarity_caveat": True,
            }
        )
    return rows


def pilot_assert_arms(arm_names: Sequence[str]) -> None:
    """S3 structural assertion: the pilot decodes arms A1+A2 ONLY."""
    names = tuple(str(n) for n in arm_names)
    if any("twin" in n.lower() for n in names) or set(names) != set(PILOT_ARMS):
        raise OrderFreezeError(
            f"S3 violation: pilot arms must be exactly {PILOT_ARMS} (the twin arm is "
            f"never decoded in the pilot); got {names}"
        )


# ---------------------------------------------------------------- S8 statistics


def pct_delta_lers(l_a: float, l_b: float) -> float:
    """S1 estimand convention: %dLER(A vs B) = 100 * (L_B - L_A) / L_B."""
    return 100.0 * (float(l_b) - float(l_a)) / max(float(l_b), NUMERICAL_ZERO)


def paired_shot_bootstrap(
    errors_a, errors_b, *, replicates: int = BOOT_REPLICATES, seed: int = M4_SEED
) -> dict:
    """%dLER(A vs B) with the paired SHOT bootstrap (S8/G3): the shot is the iid
    resampling unit — whole per-shot vectors are resampled so subchains/windows
    within a shot stay together; the Kish design effect is reported."""
    a = np.asarray(errors_a, dtype=np.float64)
    b = np.asarray(errors_b, dtype=np.float64)
    if a.ndim == 1:
        a = a[:, None]
    if b.ndim == 1:
        b = b[:, None]
    if a.shape != b.shape:
        raise ValueError(f"paired arrays must share shape, got {a.shape} vs {b.shape}")
    n, units = a.shape
    a_shot = a.mean(axis=1)
    b_shot = b.mean(axis=1)
    l_a = float(a_shot.mean())
    l_b = float(b_shot.mean())
    pct = pct_delta_lers(l_a, l_b)
    rng = np.random.default_rng(int(seed))
    reps = np.empty(int(replicates), dtype=np.float64)
    for i in range(int(replicates)):
        idx = rng.integers(0, n, size=n)
        reps[i] = pct_delta_lers(a_shot[idx].mean(), b_shot[idx].mean())
    d_shot = b_shot - a_shot
    se_shot = float(d_shot.std(ddof=1) / math.sqrt(n)) if n > 1 else float("nan")
    d_cells = (b - a).ravel()
    se_iid = (
        float(d_cells.std(ddof=1) / math.sqrt(d_cells.size)) if d_cells.size > 1 else float("nan")
    )
    deff = (se_shot / se_iid) ** 2 if se_iid and se_iid > NUMERICAL_ZERO else float("nan")
    q01, q025, q975, q99 = (float(np.quantile(reps, q)) for q in (0.01, 0.025, 0.975, 0.99))
    return {
        "pct_delta": pct,
        "l_a": l_a,
        "l_b": l_b,
        "boot_se": float(reps.std(ddof=1)),
        "q01": q01,
        "q025": q025,
        "q975": q975,
        "q99": q99,
        "pass_one_sided_99": bool(q01 > 0.0),
        "design_effect": float(deff),
        "n_shots": int(n),
        "n_units": int(units),
        "replicates": int(replicates),
        "seed": int(seed),
    }


def _binom_sf_half(k: int, n: int) -> float:
    """P(X >= k) for X ~ Binomial(n, 1/2), exact terms in log space (torch lgamma)."""
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    i = torch.arange(int(k), int(n) + 1, dtype=torch.float64)
    n_t = torch.tensor(float(n), dtype=torch.float64)
    log_terms = (
        torch.lgamma(n_t + 1.0)
        - torch.lgamma(i + 1.0)
        - torch.lgamma(n_t - i + 1.0)
        - n_t * math.log(2.0)
    )
    return float(min(1.0, torch.exp(log_terms).sum().item()))


def mcnemar_exact(errors_a, errors_b) -> dict:
    """Exact McNemar cross-check (G3): discordant counts (n01, n10) reported per
    pair; discordance near its saturation bound => flagged conditioning-limited
    regardless of p (threshold = 0.9 x bound; declared (c), module note).
    Convention: n01 = cells where A errs and B is correct; n10 = the converse;
    one-sided p tests "A better" (n10 dominant)."""
    a = np.asarray(errors_a).astype(bool).ravel()
    b = np.asarray(errors_b).astype(bool).ravel()
    if a.shape != b.shape:
        raise ValueError("paired arrays must share shape")
    n = int(a.size)
    n01 = int(np.count_nonzero(a & ~b))
    n10 = int(np.count_nonzero(~a & b))
    m = n01 + n10
    p_a = float(a.mean()) if n else float("nan")
    p_b = float(b.mean()) if n else float("nan")
    if m == 0:
        p_one = p_two = 1.0
    else:
        p_one = _binom_sf_half(n10, m)
        p_two = min(1.0, 2.0 * _binom_sf_half(max(n01, n10), m))
    delta = m / max(n, 1)
    bound = min(p_a + p_b, 2.0 - (p_a + p_b))
    conditioning_limited = bool(bound > NUMERICAL_ZERO and delta >= MCNEMAR_SATURATION_FRACTION * bound)
    return {
        "n": n,
        "n01": n01,
        "n10": n10,
        "discordance": float(delta),
        "discordance_bound": float(bound),
        "conditioning_limited": conditioning_limited,
        "p_one_sided": float(p_one),
        "p_two_sided": float(p_two),
        "p_a": p_a,
        "p_b": p_b,
    }


def rankdata(values) -> np.ndarray:
    """Average-tie ranks (1-based), mergesort-stable."""
    x = np.asarray(values, dtype=np.float64)
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(x.size, dtype=np.float64)
    sorted_x = x[order]
    i = 0
    while i < x.size:
        j = i
        while j + 1 < x.size and sorted_x[j + 1] == sorted_x[i]:
            j += 1
        ranks[order[i : j + 1]] = 0.5 * (i + j) + 1.0
        i = j + 1
    return ranks


def spearman(y, x) -> float:
    ry, rx = rankdata(y), rankdata(x)
    ry = ry - ry.mean()
    rx = rx - rx.mean()
    denom = math.sqrt(float(ry @ ry) * float(rx @ rx))
    if denom < NUMERICAL_ZERO:
        return 0.0
    return float(ry @ rx) / denom


def partial_spearman(y, x, z) -> float:
    """Partial Spearman rho(y, x | z): rank-transform, residualize y and x on z
    (least squares with intercept), Pearson of the residuals."""
    ry, rx, rz = rankdata(y), rankdata(x), rankdata(z)
    design = np.stack([np.ones_like(rz), rz], axis=1)

    def _residual(v: np.ndarray) -> np.ndarray:
        coef, *_ = np.linalg.lstsq(design, v, rcond=None)
        return v - design @ coef

    ey, ex = _residual(ry), _residual(rx)
    denom = math.sqrt(float(ey @ ey) * float(ex @ ex))
    if denom < NUMERICAL_ZERO:
        return 0.0
    return float(ey @ ex) / denom


def covariation_test(
    pct_delta_w,
    r_big_w,
    r_small_w,
    *,
    window_labels: Sequence[int] | None = None,
    rho_min: float = SPEARMAN_RHO_MIN,
    alpha: float = SPEARMAN_ALPHA,
    permutations: int = PERM_REPLICATES,
    seed: int = M4_SEED,
    drop_windows: Sequence[int] = COVARIATION_DROP_WINDOWS,
) -> dict:
    """G5: partial Spearman rho(%dLER_W(twin vs pij), R_hat_W | r_hat_W), one-sided
    positive, registered test of a post-hoc-flagged covariation (NEVER
    "independent confirmation"); no mechanism attribution. Both nulls reported:
    Monte-Carlo permutation (B, seed — module note on "exact") and the fully
    enumerated cyclic-shift null; {w8, w20} drop-sensitivity."""
    y = np.asarray(pct_delta_w, dtype=np.float64)
    big = np.asarray(r_big_w, dtype=np.float64)
    small = np.asarray(r_small_w, dtype=np.float64)
    if not (y.shape == big.shape == small.shape) or y.ndim != 1:
        raise ValueError("covariation inputs must be equal-length 1-d arrays")
    n = y.size
    labels = list(window_labels) if window_labels is not None else list(range(n))
    if len(labels) != n:
        raise ValueError("window_labels length mismatch")

    def _perm_p(yv, bv, sv, rho_obs, rng):
        worse = 0
        for _ in range(int(permutations)):
            rho_p = partial_spearman(yv[rng.permutation(yv.size)], bv, sv)
            if rho_p >= rho_obs:
                worse += 1
        return (1.0 + worse) / (float(permutations) + 1.0)

    rho = partial_spearman(y, big, small)
    rng = np.random.default_rng(int(seed))
    p_perm = _perm_p(y, big, small, rho, rng)
    rho_shifts = [partial_spearman(np.roll(y, k), big, small) for k in range(n)]
    p_cyclic = float(np.mean([r >= rho for r in rho_shifts]))  # identity included => >= 1/n
    cyclic_ok = bool(p_cyclic <= CYCLIC_TOP_RANK / n)

    drops = {}
    drop_sets = [(w,) for w in drop_windows if w in labels]
    present = tuple(w for w in drop_windows if w in labels)
    if len(present) > 1:
        drop_sets.append(present)
    for drop in drop_sets:
        keep = np.array([lab not in drop for lab in labels], dtype=bool)
        yd, bd, sd = y[keep], big[keep], small[keep]
        rho_d = partial_spearman(yd, bd, sd)
        p_d = _perm_p(yd, bd, sd, rho_d, np.random.default_rng(int(seed)))
        drops["drop_" + "_".join(f"w{w}" for w in drop)] = {
            "rho": rho_d,
            "p_perm": p_d,
            "significant": bool(rho_d >= rho_min and p_d <= alpha),
        }
    pass_perm = bool(rho >= rho_min and p_perm <= alpha)
    leverage_ok = all(d["significant"] for d in drops.values()) if drops else True
    if pass_perm and cyclic_ok and leverage_ok:
        verdict = "pass"
    elif pass_perm:
        verdict = "confound-consistent"  # G5: vanishing under cyclic null / leverage drop
    else:
        verdict = "null"
    return {
        "rho_partial": rho,
        "p_perm": p_perm,
        "p_cyclic": p_cyclic,
        "p_cyclic_min_attainable": 1.0 / n,
        "cyclic_ok": cyclic_ok,
        "pass_perm": pass_perm,
        "leverage_ok": leverage_ok,
        "drops": drops,
        "verdict": verdict,
        "n_windows": n,
        "rho_min": rho_min,
        "alpha": alpha,
        "permutations": int(permutations),
        "seed": int(seed),
        "label": "registered test of a post-hoc-flagged covariation",
    }


def drift_trend(per_sample_pct: Mapping[int, float]) -> dict:
    """G7: per-sample %dLER + trend check; spread band (b) [2%, 40%]."""
    samples = sorted(int(s) for s in per_sample_pct)
    values = np.array([float(per_sample_pct[s]) for s in samples], dtype=np.float64)
    spread = float(values.max() - values.min()) if values.size else float("nan")
    slope = float(np.polyfit(np.array(samples, dtype=np.float64), values, 1)[0]) if values.size > 1 else float("nan")
    rank_rho = spearman(values, np.array(samples, dtype=np.float64)) if values.size > 1 else float("nan")
    return {
        "samples": samples,
        "pct_delta": values.tolist(),
        "spread": spread,
        "band": list(DRIFT_SPREAD_BAND),
        "in_band": bool(DRIFT_SPREAD_BAND[0] <= spread <= DRIFT_SPREAD_BAND[1]),
        "ols_slope_per_sample": slope,
        "rank_trend_rho": rank_rho,
    }


BASELINE_ARMS = ("naive", "pij")


def floor_check(
    baseline_lers: Mapping[str, float],
    *,
    n_heldout_shots: int,
    gate_central_pct: float,
    baseline_discordance: float | None = None,
) -> dict:
    """S8 pre-registered conditional extension trigger (anti-optional-stopping, c).

    BASELINE-ONLY BY INTERFACE: accepts only the named baseline arms — any other
    key (in particular anything twin-tagged) raises. Trigger: the baseline-only
    aggregate resolution floor (one-sided 99%, McNemar variance bound
    Var(dp) <= delta / N) exceeding half the registered gate central => held-out
    extends ONCE to samples 10-14. Conservative conventions per module note."""
    for key in baseline_lers:
        if key not in BASELINE_ARMS:
            raise ValueError(
                f"floor_check is baseline-only by interface: accepts {BASELINE_ARMS}, got {key!r}"
            )
    if "naive" not in baseline_lers:
        raise ValueError("floor_check requires the 'naive' baseline LER")
    l_naive = float(baseline_lers["naive"])
    if baseline_discordance is not None:
        delta_hat = float(baseline_discordance)
        delta_source = "measured pilot A1<->A2 discordance (baseline-only)"
    else:
        delta_hat = min(2.0 * l_naive, 0.5)
        delta_source = "conservative bound min(2*L_naive, 0.5)"
    n = max(int(n_heldout_shots), 1)
    floor_abs = Z_ONE_SIDED_99 * math.sqrt(delta_hat / n)
    floor_pct = 100.0 * floor_abs / max(l_naive, NUMERICAL_ZERO)
    extend = bool(floor_pct > float(gate_central_pct) / 2.0)
    return {
        "baseline_lers": {k: float(v) for k, v in baseline_lers.items()},
        "delta_hat": delta_hat,
        "delta_source": delta_source,
        "n_heldout_shots": n,
        "z_one_sided_99": Z_ONE_SIDED_99,
        "floor_abs": floor_abs,
        "floor_pct": floor_pct,
        "gate_central_pct": float(gate_central_pct),
        "extend": extend,
        "extension_samples": list(EXTENSION_SAMPLES),
    }


def heldout_samples(extend: bool) -> tuple[int, ...]:
    """The ONE held-out pass covers 05-09, plus 10-14 iff the baseline-only
    floor check triggered the pre-registered extension (decided BEFORE the pass)."""
    return HELDOUT_PRIMARY_SAMPLES + (EXTENSION_SAMPLES if extend else ())


def mad_burst_mask(per_shot_counts) -> np.ndarray:
    """M4-F10 burst-shot MAD flag (m3 P8 rule on the per-shot error count across
    units of the baseline arm — module note): |c - median| > 5 * 1.4826 * MAD."""
    v = np.asarray(per_shot_counts, dtype=np.float64)
    median = float(np.median(v))
    scale = 1.4826 * float(np.median(np.abs(v - median)))
    if scale <= 0.0:
        return np.zeros(v.size, dtype=bool)
    return np.abs(v - median) > 5.0 * scale


# ---------------------------------------------------------------- P1h amended split (ruling 14) + fix-round glue


def p1h_structural_gate(
    marginals,
    measured,
    *,
    mean_matched_idx,
    mean_matched_targets,
    interior_idx,
    band_tol: float = P1H_BAND_TOL,
    mean_match_tol: float = P1H_MEAN_MATCH_TOL,
    interior_max: float = P1H_INTERIOR_MAX_DEV,
) -> dict:
    """AMENDMENT 1 ruling 14, component (i) — the ONLY P1h component the freeze
    may halt on:

    1. mean-matched (weight-1-carrying) sites reproduce their registered target
       fraction to <= ``mean_match_tol`` (1e-9);
    2. zero negative/NaN composed marginals;
    3. the interior-site deviation field is one-signed POSITIVE — operationalized
       (declared (c), module docstring): no interior site composes BELOW measured
       by more than the +/-0.5% band — with max deviation <= ``interior_max``
       (3e-2 catastrophe tripwire, (c)).

    The +/-0.5% per-site band itself is component (ii): scored-and-reported per
    arm via :func:`p1h_band_row`, NEVER a halt.
    """
    marginals = np.asarray(marginals, dtype=np.float64)
    measured = np.asarray(measured, dtype=np.float64)
    if marginals.shape != measured.shape or marginals.ndim != 1:
        raise ValueError("marginals/measured must be equal-length 1-d arrays")
    nan_count = int(np.isnan(marginals).sum())
    neg_count = int((marginals < 0.0).sum())  # NaN < 0 is False: counts are disjoint
    mm_idx = np.asarray(mean_matched_idx, dtype=np.int64)
    mm_targets = np.asarray(mean_matched_targets, dtype=np.float64)
    if mm_idx.shape != mm_targets.shape:
        raise ValueError("mean_matched_idx/targets length mismatch")
    mm_dev = np.abs(marginals[mm_idx] - mm_targets) if mm_idx.size else np.zeros(0)
    mm_max = float(mm_dev.max()) if mm_dev.size else 0.0
    mm_violations = int((mm_dev > mean_match_tol).sum())
    ii = np.asarray(interior_idx, dtype=np.int64)
    dev = marginals[ii] - measured[ii] if ii.size else np.zeros(0)
    negative_out_of_band = int((dev < -band_tol).sum())
    max_interior_dev = float(dev.max()) if dev.size else 0.0
    min_interior_dev = float(dev.min()) if dev.size else 0.0
    tripwire = bool(max_interior_dev > interior_max)
    reasons = []
    if nan_count:
        reasons.append(f"{nan_count} NaN composed marginals")
    if neg_count:
        reasons.append(f"{neg_count} negative composed marginals")
    if mm_violations:
        reasons.append(
            f"{mm_violations} mean-matched sites off target by > {mean_match_tol:g} "
            f"(max {mm_max:.3g})"
        )
    if negative_out_of_band:
        reasons.append(
            f"{negative_out_of_band} interior sites compose BELOW measured beyond the "
            f"+/-{band_tol:g} band (one-signed-positive violation)"
        )
    if tripwire:
        reasons.append(
            f"max interior deviation {max_interior_dev:.3g} > {interior_max:g} "
            "(catastrophe tripwire)"
        )
    passed = not reasons
    return {
        "rule": "AMENDMENT 1 ruling 14(i): the freeze HALTS only on this structural component",
        "epistemic_class": "(c) structural build-bug gate",
        "passed": passed,
        "halt": not passed,
        "reasons": reasons,
        "nan_marginals": nan_count,
        "negative_marginals": neg_count,
        "mean_matched_sites": int(mm_idx.size),
        "mean_matched_max_dev": mm_max,
        "mean_matched_violations": mm_violations,
        "mean_match_tol": float(mean_match_tol),
        "interior_sites": int(ii.size),
        "interior_negative_out_of_band": negative_out_of_band,
        "interior_max_dev": max_interior_dev,
        "interior_min_dev": min_interior_dev,
        "interior_max_allowed": float(interior_max),
        "band_tol": float(band_tol),
    }


def p1h_band_row(
    arm: str,
    *,
    num_out: int,
    num_sites: int,
    max_abs_dev: float,
    mean_abs_dev: float,
    tol: float = P1H_BAND_TOL,
) -> dict:
    """AMENDMENT 1 ruling 14, component (ii): the registered +/-0.5% per-site
    band, scored-and-reported per arm as the (b) bet it is. A miss is recorded
    as the REGISTERED FINDING (M3/ADR-0008-H3 back-edge tag) — never a halt,
    never citable as fact, no band re-derivation, no composition edit (G2)."""
    in_band = int(num_out) == 0
    row = {
        "arm": str(arm),
        "epistemic_class": "(b) registered per-site band (AMENDMENT 1 ruling 14(ii))",
        "tol": float(tol),
        "num_out": int(num_out),
        "num_sites": int(num_sites),
        "max_abs_dev": float(max_abs_dev),
        "mean_abs_dev": float(mean_abs_dev),
        "in_band": in_band,
        "halts_freeze": False,
    }
    if not in_band:
        row["registered_finding"] = {
            "tag": P1H_FINDING_TAG,
            "status": (
                "REGISTERED FINDING: band miss recorded as the (b) bet's outcome; "
                "never citable as fact; no band re-derivation; no composition edit "
                "(G2); never a halt"
            ),
        }
    return row


def sim_round_trip_pass(result) -> dict:
    """The declared (c) G4 pass rule for run-scale (non-enumerable) DEMs
    (reviewer C-5 / F-B2-3; recorded in the freeze manifest extra): pass iff the
    decode completed (correct shapes — an exception never reaches here) AND
    sim_ler < raw_flip_rate AND sim_ler < 0.45. Consumes the REAL
    ``SimRoundTripResult`` fields (reviewer B-13: it is a NamedTuple, not a dict
    with a 'passed' key); the exact enumerable-DEM check stays pinned in B2's
    own toy suite."""
    sim = float(result.sim_ler)
    raw = float(result.raw_flip_rate)
    predicted = float(result.predicted_ler)
    passed = bool(math.isfinite(sim) and math.isfinite(raw) and sim < raw and sim < 0.45)
    return {
        "sim_ler": sim,
        "predicted_ler": predicted,
        "raw_flip_rate": raw,
        "n_shots": int(result.n_shots),
        "seed": int(result.seed),
        "passed": passed,
        "rule": SIM_ROUND_TRIP_PASS_RULE,
    }


def rr_table_chain_pairs(per_qubit: Mapping) -> dict:
    """B-16 key adaptor (owner B3; direction documented): B1's ``two_pass_table``
    is keyed by DATA QUBIT index ``g``; B2's ``SpaceEdgeGeometry``/
    ``two_pass_decode`` rR_table is keyed by CHAIN PAIRS. Data qubit ``g`` sits
    between detector chains ``g-1`` and ``g``, so the map is
    ``{g} -> {(g-1, g)}``; the boundary qubit keys then coincide with B2's
    ``(min_chain-1, min_chain)`` / ``(max_chain, max_chain+1)`` convention."""
    return {
        (int(g) - 1, int(g)): (float(v[0]), float(v[1])) for g, v in per_qubit.items()
    }


def record_dmle_attempt(
    state_dir,
    *,
    attempted: bool,
    outcome: str,
    version: str | None = None,
    settings: str | None = None,
    reason: str | None = None,
) -> dict:
    """A4 dMLE attempt documentation hook (run-unmodified-or-drop, ratified R4;
    reviewer change item 6): written BEFORE the scoring stage consumes the dMLE
    row. ``outcome``: 'ran' | 'failed-to-run' | 'dropped'."""
    record = {
        "protocol": "run-unmodified-or-drop (ratified R4)",
        "note": DMLE_PROTOCOL_NOTE,
        "attempted": bool(attempted),
        "outcome": str(outcome),
        "version": version,
        "settings": settings,
        "reason": reason,
        "recorded_utc": _utc_stamp(),
    }
    _dump_json(record, Path(state_dir) / "dmle_attempt.json")
    return record


def load_dmle_attempt(state_dir) -> dict | None:
    path = Path(state_dir) / "dmle_attempt.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _require_unit_actual_observables(b2):
    """The per-unit ACTUAL-observable helper is B2's fix-round deliverable
    (reviewer B-12 / change item 2): ``unit_actual_observables(ds, basis,
    sample, units) -> uint8 [shots, len(units)]`` with units = ``(data_lo,
    data_hi)`` inclusive pairs (only data_lo selects the observable). Guarded
    lookup with a LOUD error — error arrays are never fabricated."""
    fn = getattr(b2, "unit_actual_observables", None)
    if fn is None:
        raise OrderFreezeError(
            "m4_decode.unit_actual_observables(ds, basis, sample, units) is MISSING "
            "(B2 fix-round deliverable, reviewer B-12): the per-unit actual "
            "observable — final readout of the unit's leftmost data qubit XOR its "
            "sweep reference — is the error-array source for every statistic; "
            "refusing to proceed without it"
        )
    return fn


# ---------------------------------------------------------------- gate band lookup / scoring helpers


def gate_band_for_rung(basis: str, d_prime: int) -> dict:
    """S7 PRIMARY-1 per-rung band TABLE lookup (declared BEFORE the pilot)."""
    if basis not in GATE_RUNG_BANDS:
        raise ValueError(f"unknown basis {basis!r}")
    d = int(d_prime)
    if d not in RUNG_GRID:
        raise ValueError(f"d'={d} not on the registered rung grid {RUNG_GRID}")
    for (lo, hi), (band_lo, band_hi, central) in GATE_RUNG_BANDS[basis]:
        if lo <= d <= hi:
            return {"lo": band_lo, "hi": band_hi, "central": central}
    raise ValueError(f"d'={d} not covered by the registered band table")


def regime_pin(window_pij_lers: Mapping[int, float]) -> dict:
    """S7 window regime pin (c): per-window pij-arm held-out LER in [0.005, 0.45]
    for >= 16/19; windows with L >= 0.45 are excluded-and-flagged from %d
    aggregates and the covariation; the count is reported."""
    rows = {}
    excluded = []
    for w, ler in window_pij_lers.items():
        ler = float(ler)
        in_band = REGIME_PIN_BAND[0] <= ler <= REGIME_PIN_BAND[1]
        saturated = ler >= REGIME_PIN_BAND[1]
        rows[int(w)] = {"ler": ler, "in_band": bool(in_band), "saturated": bool(saturated)}
        if saturated:
            excluded.append(int(w))
    n_in = sum(1 for r in rows.values() if r["in_band"])
    return {
        "per_window": rows,
        "n_in_band": n_in,
        "n_windows": len(rows),
        "min_required": REGIME_PIN_MIN_WINDOWS,
        "passed": bool(n_in >= REGIME_PIN_MIN_WINDOWS),
        "excluded_saturated": excluded,
        "saturated_majority": bool(len(excluded) > len(rows) / 2.0),
    }


def located_signs(per_window_pct: Mapping[int, float]) -> dict:
    """S7 located signs (b): twin-vs-pij > 0 on {8, 9, 16, 17}; <= 0 on {20, 21}."""
    rows = {}
    for w in LOCATED_POSITIVE_WINDOWS:
        if w in per_window_pct:
            rows[w] = {"pct": float(per_window_pct[w]), "expected": ">0",
                       "ok": bool(per_window_pct[w] > 0.0)}
    for w in LOCATED_NONPOSITIVE_WINDOWS:
        if w in per_window_pct:
            rows[w] = {"pct": float(per_window_pct[w]), "expected": "<=0",
                       "ok": bool(per_window_pct[w] <= 0.0)}
    n_ok = sum(1 for r in rows.values() if r["ok"])
    return {"per_window": rows, "n_ok": n_ok, "n_total": len(rows), "all_ok": n_ok == len(rows)}


def p10_score(measured_lers: Mapping[int, float], predicted_lers: Mapping[int, float]) -> dict:
    """S7 P10 (b): measured/predicted in [0.5, 2] for >= 75% of windows."""
    rows = {}
    for w, pred in predicted_lers.items():
        w = int(w)
        if w not in measured_lers:
            continue
        pred = float(pred)
        meas = float(measured_lers[w])
        ratio = meas / max(pred, NUMERICAL_ZERO)
        rows[w] = {
            "predicted": pred,
            "measured": meas,
            "ratio": ratio,
            "in_band": bool(P10_RATIO_BAND[0] <= ratio <= P10_RATIO_BAND[1]),
        }
    n = len(rows)
    frac = (sum(1 for r in rows.values() if r["in_band"]) / n) if n else float("nan")
    return {
        "per_window": rows,
        "fraction_in_band": float(frac),
        "min_fraction": P10_MIN_FRACTION,
        "passed": bool(n > 0 and frac >= P10_MIN_FRACTION),
        "ratio_band": list(P10_RATIO_BAND),
    }


# ---------------------------------------------------------------- frozen covariates + Tier-0 bands


def _selected_record(cache: Mapping, basis: str, window: int, split: str = "full"):
    """The M3 selection rule on the FROZEN cache: per window, the seed with the
    lower TRAIN cross-entropy (same selection as outputs/m4_i6_tb_check.py)."""
    records = [cache[_cache_key(basis, int(window), int(seed), split)] for seed in FIT_SEEDS]
    return min(records, key=lambda r: r.ce_per_block)


def frozen_covariates(cache: Mapping, basis: str, windows=CLEAN_WINDOWS) -> dict[int, dict]:
    """G5 covariates FROZEN at the M3 full-split centrals (central qubit, lower-CE
    seed): r_hat = 2 p01 p10 / (p01 + p10), R_hat = (p01 + p10)^2 / (4 p01 p10)."""
    out = {}
    for w in windows:
        rec = _selected_record(cache, basis, w)
        p01, p10 = (float(x) for x in rec.markov[2])  # central qubit
        out[int(w)] = {
            "r_hat": 2.0 * p01 * p10 / max(p01 + p10, NUMERICAL_ZERO),
            "R_hat": (p01 + p10) ** 2 / max(4.0 * p01 * p10, NUMERICAL_ZERO),
            "p01": p01,
            "p10": p10,
            "seed": int(rec.seed),
        }
    return out


def tier0_bands(cache: Mapping, basis: str, windows=CLEAN_WINDOWS) -> dict:
    """S12 deliverable: per-edge Tier-0 bands + abstain flags from the FROZEN
    cache. Ownership filter (S5): data qubits at interior window positions 2-4
    only; measure qubits at interior detectors only. Central = MEDIAN over
    owners (S5 aggregator); band = [min, max] replicate spread
    (systematics-dominated, M3 P7). Unowned cells => abstain (train-pij fill in
    the composition; no twin band is claimed there)."""
    data_owned: dict[int, list[float]] = {}
    meas_owned: dict[int, list[float]] = {}
    for w in windows:
        rec = _selected_record(cache, basis, w)
        for qubit in (1, 2, 3):  # interior positions 2-4 (1-indexed) of the 5
            p01, p10 = (float(x) for x in rec.markov[qubit])
            r_hat = 2.0 * p01 * p10 / max(p01 + p10, NUMERICAL_ZERO)
            data_owned.setdefault(int(w) + 1 + qubit, []).append(r_hat)
        for k in range(4):  # all 4 in-window measure columns are interior detectors
            meas_owned.setdefault(int(w) + 1 + k, []).append(float(rec.q_eff[k]))

    def _bands(owned: dict[int, list[float]], positions: range) -> dict:
        rows = {}
        abstain = []
        for pos in positions:
            if pos in owned:
                vals = np.array(owned[pos], dtype=np.float64)
                rows[pos] = {
                    "central": float(np.median(vals)),
                    "band": [float(vals.min()), float(vals.max())],
                    "n_owners": int(vals.size),
                    "abstain": False,
                }
            else:
                abstain.append(pos)
        return {"sites": rows, "abstain_positions": abstain}

    return {
        "basis": basis,
        "aggregator": "median over owners (S5)",
        "band_convention": "replicate [min, max] over owning windows (systematics-dominated, M3 P7)",
        "data_r_hat": _bands(data_owned, range(0, 29)),
        "measure_q_eff": _bands(meas_owned, range(0, 28)),
    }


# ---------------------------------------------------------------- P10 GPU sampler + forecast


def sample_window_twin_shots(
    markov_pairs,
    q_eff,
    *,
    shots: int,
    seed: int,
    device: str = "cuda",
    ancilla_rounds: int = NUM_ANCILLA_ROUNDS,
    chunk_shots: int = 25_000,
) -> tuple[np.ndarray, np.ndarray]:
    """GPU MC sampler of the FROZEN M3 window twin model (P10, S7/S11).

    Model equivalence (m3_report.flip_channel_kraus): K0 = diag(sqrt(1-p01),
    sqrt(1-p10)), K1 = antidiag(sqrt(p10), sqrt(p01)) acts on a
    computational-basis state as the classical two-state Markov chain on the
    qubit VALUE with P(0->1) = p01, P(1->0) = p10 (strictly
    diagonal/antidiagonal Kraus: zero coherence is generated, so the diagonal
    of the density matrix evolves exactly by this chain); q_eff is the
    gauge-exact per-round record flip (m3 P1g folding identity; "MR resets
    clean"). The bulk detector-pair law of this sampler therefore converges to
    the M3 steady block law (m3 P1a pins the same law against stim at d=5).

    Conventions (module docstring; recorded with the build): v(0) = 0; per round
    t = 1..R the chain steps then the 4 interior measure columns record
    M_k(t) = v_k(t) XOR v_{k+1}(t) XOR u_k(t), u ~ Bern(q_eff_k) iid; detector
    layers: layer 0 = M(1); layer t in 1..R-1 = M(t+1) XOR M(t); layer R
    (final) = u(R) (no final-data-readout DOF in the twin class — S5 unowned).
    Observable flip = v_leftmost(R) (error frame; S2/P1b).

    Returns ``(detectors [shots, (R+1)*4] uint8 layer-major (t*4 + k),
    obs_flips [shots] uint8)`` on CPU. Determinism: fixed (seed, chunk_shots)
    defines the stream. GPU-only by project rule — raises off-CUDA.
    """
    if not str(device).startswith("cuda"):
        raise RuntimeError("P10 model sampling is GPU-only (project rule); got device=" + str(device))
    markov = np.asarray(markov_pairs, dtype=np.float64)
    q = np.asarray(q_eff, dtype=np.float64)
    if markov.shape != (5, 2) or q.shape != (4,):
        raise ValueError(f"expected markov_pairs (5, 2) and q_eff (4,), got {markov.shape}, {q.shape}")
    rounds = int(ancilla_rounds)
    shots = int(shots)
    p01 = torch.as_tensor(markov[:, 0], dtype=torch.float64, device=device)
    p10 = torch.as_tensor(markov[:, 1], dtype=torch.float64, device=device)
    q_t = torch.as_tensor(q, dtype=torch.float64, device=device)
    gen = torch.Generator(device=device)
    gen.manual_seed(int(seed))
    det_chunks: list[np.ndarray] = []
    obs_chunks: list[np.ndarray] = []
    done = 0
    while done < shots:
        n = min(int(chunk_shots), shots - done)
        v = torch.zeros((n, 5), dtype=torch.bool, device=device)
        dets = torch.zeros((n, rounds + 1, 4), dtype=torch.bool, device=device)
        m_prev = torch.zeros((n, 4), dtype=torch.bool, device=device)
        u = torch.zeros((n, 4), dtype=torch.bool, device=device)
        for t in range(1, rounds + 1):
            flip_p = torch.where(v, p10.expand(n, 5), p01.expand(n, 5))
            v = v ^ (torch.rand((n, 5), dtype=torch.float64, device=device, generator=gen) < flip_p)
            u = torch.rand((n, 4), dtype=torch.float64, device=device, generator=gen) < q_t
            m_now = v[:, :4] ^ v[:, 1:] ^ u
            if t == 1:
                dets[:, 0] = m_now
            else:
                dets[:, t - 1] = m_now ^ m_prev
            m_prev = m_now
        dets[:, rounds] = u  # final layer: readout flips only (convention above)
        det_chunks.append(dets.reshape(n, -1).to(torch.uint8).cpu().numpy())
        obs_chunks.append(v[:, 0].to(torch.uint8).cpu().numpy())
        done += n
    return np.concatenate(det_chunks, axis=0), np.concatenate(obs_chunks, axis=0)


def p10_window_seed(basis: str, window: int, *, seed: int = M4_SEED) -> int:
    """(c) per-(basis, window) seed derivation — declared design constant."""
    return int(seed) + P10_SEED_STRIDE * int(window) + (1 if basis == "Z" else 0)


def p10_forecast(
    cache: Mapping,
    *,
    dem_for_window,
    decode_fn,
    bases=("X", "Z"),
    windows=CLEAN_WINDOWS,
    mc_shots: int = P10_MC_SHOTS,
    device: str = "cuda",
    seed: int = M4_SEED,
) -> dict:
    """P10 predict-before-measure (b): per-window twin-arm held-out LER predicted
    by GPU MC from the FROZEN train-fitted twin model, recorded BEFORE the
    held-out pass. ``dem_for_window(basis, window)`` supplies the twin-arm
    window DEM (B1); ``decode_fn(dem, detectors)`` returns per-shot observable
    predictions (B2; CPU decoding is evaluator-side, ratified R1)."""
    rows: dict[str, dict] = {}
    for basis in bases:
        rows[basis] = {}
        for w in windows:
            rec = _selected_record(cache, basis, w)
            dets, obs = sample_window_twin_shots(
                rec.markov,
                rec.q_eff,
                shots=mc_shots,
                seed=p10_window_seed(basis, w, seed=seed),
                device=device,
            )
            predictions = np.asarray(decode_fn(dem_for_window(basis, w), dets)).astype(np.uint8).ravel()
            errors = predictions ^ obs
            ler = float(errors.mean())
            rows[basis][int(w)] = {
                "predicted_ler": ler,
                "mc_se": math.sqrt(max(ler * (1.0 - ler), NUMERICAL_ZERO) / mc_shots),
                "mc_shots": int(mc_shots),
                "seed": p10_window_seed(basis, w, seed=seed),
                "cache_key": _cache_key(basis, int(w), int(rec.seed), "full"),
            }
    return {
        "recorded_utc": _utc_stamp(),
        "seed": int(seed),
        "device": device,
        "ratio_band": list(P10_RATIO_BAND),
        "min_fraction": P10_MIN_FRACTION,
        "conventions": "see m4_report.sample_window_twin_shots docstring",
        "predictions": rows,
    }


# ---------------------------------------------------------------- order-freeze state machine (S12/G2)

STAGES = (
    "pins",
    "freeze",
    "pilot",
    "select_rung",
    "p10_forecast",
    "floor_check",
    "heldout",
    "scoring",
    "artifacts",
)


class OrderFreezeError(RuntimeError):
    """A stage refused to run: out of order, G2 manifest violation, or held-out
    re-entry. Per S12/G2 the remedy is NEVER to bypass — a voided run
    re-registers on the escrow samples 15-19."""


class M4State:
    """The S12 ORDER FREEZE as an explicit staged state machine with a JSON
    manifest under the state directory. Refusal semantics:

    - a stage refuses unless every earlier stage is COMPLETE;
    - a stage refuses if any later stage has already STARTED (no reordering,
      no silent re-runs after downstream stages began);
    - the held-out stage additionally refuses if the G2 freeze manifest is
      missing/edited or the composition source hashes changed, and it refuses
      to start TWICE — the attempt is persisted before any decode, so a crashed
      pass still counts as the one pass.
    """

    REGISTRATION = "docs/metric_results.md — M4 PRE-REGISTRATION (recorded 2026-06-10)"

    def __init__(self, state_dir: str | Path):
        self.dir = Path(state_dir)
        self.path = self.dir / "state.json"
        if self.path.exists():
            self._state = json.loads(self.path.read_text(encoding="utf-8"))
        else:
            self._state = {"registration": self.REGISTRATION, "seed": M4_SEED, "stages": {}}

    # -- persistence
    def _save(self) -> None:
        _dump_json(self._state, self.path)

    @property
    def manifest_path(self) -> Path:
        return self.dir / "freeze_manifest.json"

    # -- queries
    def stage(self, name: str) -> dict | None:
        return self._state["stages"].get(name)

    def completed(self, name: str) -> bool:
        entry = self.stage(name)
        return bool(entry and entry.get("completed"))

    def payload(self, name: str) -> dict:
        entry = self.stage(name)
        if not entry or not entry.get("completed"):
            raise OrderFreezeError(f"stage '{name}' has no completed payload")
        return entry.get("payload", {})

    # -- order enforcement
    def check_order(self, name: str) -> None:
        if name not in STAGES:
            raise OrderFreezeError(f"unknown stage '{name}' (frozen order: {STAGES})")
        index = STAGES.index(name)
        missing = [s for s in STAGES[:index] if not self.completed(s)]
        if missing:
            raise OrderFreezeError(
                f"stage '{name}' refused: prerequisite stage(s) {missing} not complete "
                "(S12 ORDER FREEZE — no step reorders)"
            )
        started_later = [s for s in STAGES[index + 1 :] if self.stage(s) is not None]
        if started_later:
            raise OrderFreezeError(
                f"stage '{name}' refused: later stage(s) {started_later} already started — "
                "the order freeze forbids reordering/re-entry"
            )
        if name == "heldout" and self.stage("heldout") is not None:
            raise OrderFreezeError(
                "the ONE held-out pass (S12) has already been attempted; re-entry voids the "
                f"run — re-register on the escrow samples {list(ESCROW_SAMPLES)} (G2)"
            )

    def begin(self, name: str) -> None:
        if name == "heldout":
            raise OrderFreezeError("the held-out stage must be entered via begin_heldout (G2 checks)")
        self.check_order(name)
        self._state["stages"][name] = {"started": _utc_stamp(), "completed": None, "payload": None}
        self._save()

    def complete(self, name: str, payload: dict | None = None) -> None:
        entry = self.stage(name)
        if entry is None:
            raise OrderFreezeError(f"stage '{name}' was never started")
        entry["completed"] = _utc_stamp()
        entry["payload"] = payload or {}
        self._save()

    # -- G2 composition freeze
    def record_freeze(self, *, manifest: dict, source_hashes: Mapping[str, str], extra: dict | None = None) -> dict:
        """Write the B1 freeze manifest to disk and pin its sha256 + the
        composition source hashes (G2: pinned BEFORE any decode of samples 05+)."""
        entry = self.stage("freeze")
        if entry is None or entry.get("completed"):
            raise OrderFreezeError("record_freeze must be called inside the freeze stage (after begin)")
        sha = _dump_json(manifest, self.manifest_path)
        self._state["freeze"] = {
            "manifest_path": str(self.manifest_path),
            "manifest_sha256": sha,
            "source_hashes": dict(source_hashes),
            "recorded": _utc_stamp(),
            "extra": extra or {},
        }
        self._save()
        return self._state["freeze"]

    def begin_heldout(self, *, current_source_hashes: Mapping[str, str], samples: Sequence[int]) -> None:
        self.check_order("heldout")
        freeze = self._state.get("freeze")
        if not freeze:
            raise OrderFreezeError(
                "held-out refused: no G2 composition-freeze manifest recorded (G2: hashes "
                "pinned BEFORE any decode of samples 05+)"
            )
        manifest_path = Path(freeze["manifest_path"])
        if not manifest_path.exists():
            raise OrderFreezeError("held-out refused: the G2 freeze manifest file is missing")
        current_manifest_sha = hashlib.sha256(manifest_path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
        if current_manifest_sha != freeze["manifest_sha256"]:
            raise OrderFreezeError(
                "held-out refused: the G2 freeze manifest content changed since the freeze — "
                f"the run is VOID; re-register on the escrow samples {list(ESCROW_SAMPLES)}"
            )
        pinned = freeze["source_hashes"]
        current = dict(current_source_hashes)
        changed = sorted(
            k for k in set(pinned) | set(current) if pinned.get(k) != current.get(k)
        )
        if changed:
            raise OrderFreezeError(
                f"held-out refused: composition source hash changed for {changed} since the "
                "G2 freeze (ANY post-hoc edit voids the run, including 'fixing an obvious "
                f"bug') — re-register on the escrow samples {list(ESCROW_SAMPLES)}"
            )
        self._state["stages"]["heldout"] = {
            "started": _utc_stamp(),
            "completed": None,
            "payload": None,
            "samples": [int(s) for s in samples],
        }
        self._save()  # persisted BEFORE any decode: a crashed attempt still counts


# ---------------------------------------------------------------- per-basis result assembly (scoring core)


def per_window_pct_delta(errors_a: np.ndarray, errors_b: np.ndarray, window_ids) -> dict[int, float]:
    """Per-window %dLER(A vs B) on [shots, n_windows] paired error arrays."""
    a = np.asarray(errors_a, dtype=np.float64)
    b = np.asarray(errors_b, dtype=np.float64)
    return {
        int(w): pct_delta_lers(float(a[:, i].mean()), float(b[:, i].mean()))
        for i, w in enumerate(window_ids)
    }


def compute_basis_results(
    *,
    basis: str,
    d_prime: int,
    gate_errors: Mapping[str, np.ndarray],
    window_errors: Mapping[str, np.ndarray],
    window_ids: Sequence[int],
    covariates: Mapping[int, Mapping[str, float]],
    p10_predicted: Mapping[int, float] | None = None,
    per_sample_slices: Mapping[int, slice] | None = None,
    a3c_errors: np.ndarray | None = None,
    a3b_errors: np.ndarray | None = None,
    dmle_errors: np.ndarray | None = None,
    rl_xor_per_1e5: float | None = None,
    drift_context: Mapping | None = None,
    covariation_samples: Sequence[int] = HELDOUT_PRIMARY_SAMPLES,
    seed: int = M4_SEED,
) -> dict:
    """All registered per-basis statistics from per-shot error arrays.

    ``gate_errors``: {arm: [shots, n_subchains]} at the selected rung d'*;
    ``window_errors``: {arm: [shots, 19]} on the window instrument; arms must
    include 'twin', 'naive', 'pij'. ``a3c_errors``/``a3b_errors``/
    ``dmle_errors`` are optional [shots, 19] arrays for the secondary arms.
    ``per_sample_slices`` maps held-out sample id -> shot-axis slice (G7).
    FIX ROUND: the G5 covariation is computed on ``covariation_samples``
    (default 05-09) ONLY — the registration restricts it to the primaries even
    when the extension (10-14) triggered (reviewer S7/SF item). ``drift_context``
    carries the samples-01-04 context-only rows (scoring stage; never primaries)."""
    window_ids = [int(w) for w in window_ids]
    twin_g, naive_g, pij_g = (np.asarray(gate_errors[a]) for a in ("twin", "naive", "pij"))
    twin_w, naive_w, pij_w = (np.asarray(window_errors[a]) for a in ("twin", "naive", "pij"))

    # PRIMARY 1 — the ADR M4 GATE (twin vs naive at d'*)
    gate = paired_shot_bootstrap(twin_g, naive_g, seed=seed)
    gate["mcnemar"] = mcnemar_exact(twin_g, naive_g)
    gate["protocol"] = protocol_tuple(d_prime, gate["l_b"])
    gate["band"] = gate_band_for_rung(basis, d_prime)
    gate["in_band"] = bool(gate["band"]["lo"] <= gate["pct_delta"] <= gate["band"]["hi"])
    burst = mad_burst_mask(naive_g.sum(axis=1))
    if burst.any():
        keep = ~burst
        gate["without_burst_shots"] = {
            "n_flagged": int(burst.sum()),
            "pct_delta": pct_delta_lers(float(twin_g[keep].mean()), float(naive_g[keep].mean())),
        }
    else:
        gate["without_burst_shots"] = {"n_flagged": 0, "pct_delta": gate["pct_delta"]}

    # PRIMARY 2 — the HEADLINE (twin vs pij at d'*)
    headline = paired_shot_bootstrap(twin_g, pij_g, seed=seed)
    headline["mcnemar"] = mcnemar_exact(twin_g, pij_g)
    headline["protocol"] = protocol_tuple(d_prime, headline["l_b"])
    headline["band"] = {"lo": HEADLINE_BAND[basis][0], "hi": HEADLINE_BAND[basis][1],
                        "central": HEADLINE_CENTRAL, "central_branch": P1I_BRANCH["branch"]}
    headline["in_band"] = bool(
        HEADLINE_BAND[basis][0] <= headline["pct_delta"] <= HEADLINE_BAND[basis][1]
    )

    # pij vs naive (reported band)
    pij_vs_naive = paired_shot_bootstrap(pij_g, naive_g, seed=seed)
    pij_vs_naive["protocol"] = protocol_tuple(d_prime, pij_vs_naive["l_b"])
    pij_vs_naive["band"] = list(PIJ_VS_NAIVE_BAND)
    pij_vs_naive["in_band"] = bool(
        PIJ_VS_NAIVE_BAND[0] <= pij_vs_naive["pct_delta"] <= PIJ_VS_NAIVE_BAND[1]
    )

    # window instrument: regime pin -> exclusions -> located/covariation
    window_pij_lers = {w: float(pij_w[:, i].mean()) for i, w in enumerate(window_ids)}
    regime = regime_pin(window_pij_lers)
    excluded = set(regime["excluded_saturated"])
    delta_w = per_window_pct_delta(twin_w, pij_w, window_ids)
    located = located_signs(delta_w)
    included = [w for w in window_ids if w not in excluded]
    # G5 covariation on the PRIMARY samples (05-09) ONLY, even under the
    # extension (registration restriction; reviewer S7/SF fix item). Without
    # per-sample slices every row is a primary row by construction.
    cov_scope = None
    delta_w_cov = delta_w
    if per_sample_slices:
        wanted = {int(s) for s in covariation_samples}
        sel = sorted(int(s) for s in per_sample_slices if int(s) in wanted)
        mask = np.zeros(twin_w.shape[0], dtype=bool)
        for s in sel:
            mask[per_sample_slices[s]] = True
        if not mask.any():
            raise ValueError(
                f"covariation restriction to samples {sorted(wanted)} selects zero "
                "shots — per_sample_slices does not cover the primaries"
            )
        delta_w_cov = per_window_pct_delta(twin_w[mask], pij_w[mask], window_ids)
        cov_scope = sel
    cov = covariation_test(
        [delta_w_cov[w] for w in included],
        [covariates[w]["R_hat"] for w in included],
        [covariates[w]["r_hat"] for w in included],
        window_labels=included,
        seed=seed,
    )
    cov["covariation_samples"] = cov_scope  # None => single-population arrays

    # P10 predict-before-measure scoring (measured twin window LERs vs forecast)
    p10 = None
    if p10_predicted is not None:
        measured = {w: float(twin_w[:, i].mean()) for i, w in enumerate(window_ids)}
        p10 = p10_score(measured, p10_predicted)

    # G7 drift: per-sample gate %dLER (twin vs naive); headline reported alongside
    drift = None
    per_sample = {}
    if per_sample_slices:
        gate_by_sample = {}
        headline_by_sample = {}
        for sample, sl in sorted(per_sample_slices.items()):
            gate_by_sample[int(sample)] = pct_delta_lers(
                float(twin_g[sl].mean()), float(naive_g[sl].mean())
            )
            headline_by_sample[int(sample)] = pct_delta_lers(
                float(twin_g[sl].mean()), float(pij_g[sl].mean())
            )
        drift = drift_trend(gate_by_sample)
        per_sample = {"gate": gate_by_sample, "headline": headline_by_sample}

    # A3c two-pass vs static (window instrument only; never the gate)
    a3c = None
    if a3c_errors is not None:
        a3c_arr = np.asarray(a3c_errors)
        high_r = [w for w in included if covariates[w]["R_hat"] >= A3C_HIGH_R_MIN]
        idx = {w: i for i, w in enumerate(window_ids)}
        a3c = {"high_R_windows": high_r, "high_R_min": A3C_HIGH_R_MIN}
        if high_r:
            cols = [idx[w] for w in high_r]
            boot = paired_shot_bootstrap(a3c_arr[:, cols], twin_w[:, cols], seed=seed)
            boot["band"] = list(A3C_HIGH_R_BAND)
            boot["in_band"] = bool(A3C_HIGH_R_BAND[0] <= boot["pct_delta"] <= A3C_HIGH_R_BAND[1])
            a3c["high_R"] = boot
        controls = {}
        for w in A3C_CONTROL_WINDOWS:
            if w in idx:
                ctrl = paired_shot_bootstrap(a3c_arr[:, [idx[w]]], twin_w[:, [idx[w]]], seed=seed)
                ctrl["near_zero"] = bool(ctrl["q025"] <= 0.0 <= ctrl["q975"])  # (c) module note
                controls[w] = ctrl
        a3c["controls"] = controls

    # A3b Spitz-of-the-twin (claim-separated secondary, S4): scored from the
    # saved held-out arrays (reviewer change item 6); registered WITHOUT its own
    # band — reported with CIs, never a primary.
    a3b = None
    if a3b_errors is not None:
        a3b_arr = np.asarray(a3b_errors)
        a3b = {
            "vs_pij": paired_shot_bootstrap(a3b_arr, pij_w, seed=seed),
            "twin_vs_a3b": paired_shot_bootstrap(twin_w, a3b_arr, seed=seed),
            "per_window_vs_pij": per_window_pct_delta(a3b_arr, pij_w, window_ids),
            "claim_note": (
                "A3b is CLAIM-SEPARATED (S4): twin-implied two-point statistics "
                "through the same Spitz inversion — a secondary, never pooled with "
                "the twin arm's claims"
            ),
        }

    # A4 dMLE conditional (run-unmodified-or-drop, ratified R4)
    dmle = None
    if dmle_errors is not None:
        dmle_arr = np.asarray(dmle_errors)
        dmle_vs_pij = paired_shot_bootstrap(dmle_arr, pij_w, seed=seed)
        twin_vs_dmle = paired_shot_bootstrap(twin_w, dmle_arr, seed=seed)
        twin_vs_dmle["band"] = list(DMLE_TWIN_BAND)
        twin_vs_dmle["in_band"] = bool(
            DMLE_TWIN_BAND[0] <= twin_vs_dmle["pct_delta"] <= DMLE_TWIN_BAND[1]
        )
        dmle = {
            "dmle_vs_pij": dmle_vs_pij,
            "twin_vs_dmle": twin_vs_dmle,
            "claim_note": "the ONLY licensed twin-dMLE head-to-head; the published 30.6% is a "
            "protocol-tagged context bar only; 'matched/beat dMLE' forbidden cross-protocol (G9)",
        }

    return {
        "basis": basis,
        "d_prime": int(d_prime),
        "gate": gate,
        "headline": headline,
        "pij_vs_naive": pij_vs_naive,
        "per_window_twin_vs_pij": delta_w,
        "located": located,
        "covariation": cov,
        "regime": regime,
        "p10": p10,
        "drift": drift,
        "per_sample": per_sample,
        "a3c": a3c,
        "a3b": a3b,
        "dmle": dmle,
        "rl_xor_per_1e5": rl_xor_per_1e5,
        "drift_context": dict(drift_context) if drift_context is not None else None,
    }


# ---------------------------------------------------------------- S7 scoring + S10 routing


def score_s7(measured_by_basis: Mapping[str, dict], *, dmle_attempt: Mapping | None = None) -> dict:
    """Score the FULL S7 prediction/band table (encoded above as data) against
    measured results. Exactly TWO primaries per basis (G8); everything else is
    reported-with-bands. Rows carry their epistemic class. ``dmle_attempt`` is
    the run-unmodified-or-drop documentation record (``record_dmle_attempt``)."""
    rows = []
    for basis, m in sorted(measured_by_basis.items()):
        gate = m["gate"]
        rows.append(
            {
                "item": "PRIMARY-1 GATE %dLER(twin vs naive)",
                "basis": basis,
                "class": "(c) gate rule + (b) per-rung band",
                "measured_pct": gate["pct_delta"],
                "ci99": [gate["q01"], gate["q99"]],
                "pass_gate": gate["pass_one_sided_99"],
                "band": gate["band"],
                "in_band": gate["in_band"],
                "mcnemar": {k: gate["mcnemar"][k] for k in ("n01", "n10", "p_one_sided", "conditioning_limited")},
                "protocol": gate["protocol"],
                "design_effect": gate["design_effect"],
                "without_burst_shots": gate["without_burst_shots"],
            }
        )
        head = m["headline"]
        rows.append(
            {
                "item": "PRIMARY-2 HEADLINE %dLER(twin vs pij)",
                "basis": basis,
                "class": "(b) two-sided band",
                "measured_pct": head["pct_delta"],
                "ci95": [head["q025"], head["q975"]],
                "band": head["band"],
                "in_band": head["in_band"],
                "mcnemar": {k: head["mcnemar"][k] for k in ("n01", "n10", "p_two_sided", "conditioning_limited")},
                "protocol": head["protocol"],
                "note": "the DEM bottleneck may compress the bunching advantage toward 0 — "
                "the compression is itself the measurement",
            }
        )
        cov = m["covariation"]
        rows.append(
            {
                "item": "G5 covariation partial Spearman rho(%dLER_W, R_hat_W | r_hat_W)",
                "basis": basis,
                "class": "(c) registered test of a post-hoc-flagged covariation",
                "rho": cov["rho_partial"],
                "p_perm": cov["p_perm"],
                "p_cyclic": cov["p_cyclic"],
                "verdict": cov["verdict"],
                "drops": cov["drops"],
            }
        )
        rows.append(
            {
                "item": "located signs twin-vs-pij {8,9,16,17}>0, {20,21}<=0",
                "basis": basis,
                "class": "(b)",
                "per_window": m["located"]["per_window"],
                "n_ok": m["located"]["n_ok"],
                "n_total": m["located"]["n_total"],
                "all_ok": m["located"]["all_ok"],
            }
        )
        pvn = m["pij_vs_naive"]
        rows.append(
            {
                "item": "pij vs naive",
                "basis": basis,
                "class": "(b)",
                "measured_pct": pvn["pct_delta"],
                "band": pvn["band"],
                "in_band": pvn["in_band"],
                "protocol": pvn["protocol"],
            }
        )
        reg = m["regime"]
        rows.append(
            {
                "item": "window regime pin: pij LER in [0.005, 0.45] for >= 16/19",
                "basis": basis,
                "class": "(c)",
                "n_in_band": reg["n_in_band"],
                "n_windows": reg["n_windows"],
                "passed": reg["passed"],
                "excluded_saturated": reg["excluded_saturated"],
            }
        )
        if m.get("p10") is not None:
            p10 = m["p10"]
            rows.append(
                {
                    "item": "P10 predict-before-measure: measured/predicted in [0.5, 2] for >= 75%",
                    "basis": basis,
                    "class": "(b)",
                    "fraction_in_band": p10["fraction_in_band"],
                    "passed": p10["passed"],
                }
            )
        if m.get("drift") is not None:
            drift = m["drift"]
            rows.append(
                {
                    "item": "drift: per-sample %dLER spread in [2%, 40%] (M5 feed)",
                    "basis": basis,
                    "class": "(b)",
                    "spread": drift["spread"],
                    "in_band": drift["in_band"],
                    "ols_slope_per_sample": drift["ols_slope_per_sample"],
                    "rank_trend_rho": drift["rank_trend_rho"],
                }
            )
        if m.get("a3c") is not None:
            a3c = m["a3c"]
            rows.append(
                {
                    "item": "A3c two-pass vs static: +[0, 8]% on high-R windows; ~0 on w20/w21",
                    "basis": basis,
                    "class": "(b) + (c) operationalizations",
                    "high_R": a3c.get("high_R"),
                    "controls": {
                        w: {"pct": c["pct_delta"], "near_zero": c["near_zero"]}
                        for w, c in a3c.get("controls", {}).items()
                    },
                }
            )
        if m.get("a3b") is not None:
            a3b = m["a3b"]
            rows.append(
                {
                    "item": "A3b Spitz-of-the-twin (claim-separated secondary, S4)",
                    "basis": basis,
                    "class": "(b) secondary, claim-separated — no registered band; CIs reported",
                    "a3b_vs_pij_pct": a3b["vs_pij"]["pct_delta"],
                    "a3b_vs_pij_ci95": [a3b["vs_pij"]["q025"], a3b["vs_pij"]["q975"]],
                    "twin_vs_a3b_pct": a3b["twin_vs_a3b"]["pct_delta"],
                    "twin_vs_a3b_ci95": [a3b["twin_vs_a3b"]["q025"], a3b["twin_vs_a3b"]["q975"]],
                    "note": a3b["claim_note"],
                }
            )
        if m.get("drift_context"):
            ctx = m["drift_context"]
            rows.append(
                {
                    "item": "drift context samples 01-04 (context-only, design-contaminated)",
                    "basis": basis,
                    "class": "(b) context — decoded in scoring strictly AFTER the held-out pass; never a primary",
                    "samples": ctx.get("samples"),
                    "gate_pct": ctx.get("gate_pct"),
                    "headline_pct": ctx.get("headline_pct"),
                    "note": ctx.get("note"),
                }
            )
        if m.get("dmle") is not None:
            dmle = m["dmle"]
            rows.append(
                {
                    "item": "dMLE conditional: dMLE vs pij > 0; twin vs dMLE in [-10, +10] central 0",
                    "basis": basis,
                    "class": "(b) conditional (ratified R4)",
                    "dmle_vs_pij_pct": dmle["dmle_vs_pij"]["pct_delta"],
                    "dmle_vs_pij_positive": bool(dmle["dmle_vs_pij"]["pct_delta"] > 0.0),
                    "twin_vs_dmle_pct": dmle["twin_vs_dmle"]["pct_delta"],
                    "twin_vs_dmle_in_band": dmle["twin_vs_dmle"]["in_band"],
                    "note": dmle["claim_note"],
                    "attempt_record": dict(dmle_attempt) if dmle_attempt else None,
                }
            )
        else:
            rows.append(
                {
                    "item": "dMLE conditional",
                    "basis": basis,
                    "class": "(b) conditional (ratified R4)",
                    "status": "no dmle error arrays — disposition per the attempt record (run-unmodified-or-drop)",
                    "attempt_record": dict(dmle_attempt)
                    if dmle_attempt
                    else "ABSENT — open obligation: record via m4_report.record_dmle_attempt "
                    "BEFORE relying on this row (reviewer change item 6)",
                }
            )
        if m.get("rl_xor_per_1e5") is not None:
            rows.append(
                {
                    "item": "full-code context: corpus RL XOR count per 1e5 shots (NOT a %d claim)",
                    "basis": basis,
                    "class": "(b) context",
                    "measured": m["rl_xor_per_1e5"],
                    "band": list(FULL_CODE_RL_XOR_BAND),
                    "in_band": bool(
                        FULL_CODE_RL_XOR_BAND[0] <= m["rl_xor_per_1e5"] <= FULL_CODE_RL_XOR_BAND[1]
                    ),
                }
            )
    rows.append({"item": "reverse trap (pre-registered)", "class": "(b)", "note": REVERSE_TRAP_NOTE})
    rows.append({"class": "(c) recorded design decision", **SLIDING_WINDOW_SECONDARY})
    return {"rows": rows, "primaries_per_basis": 2, "registration": M4State.REGISTRATION}


def route_s10(measured_by_basis: Mapping[str, dict], *, m3_nll_structure_intact: bool = True) -> list[dict]:
    """S10 routing flags from measured results. Routing only — no rescue fitting
    is licensed on any branch."""
    flags = []
    for basis, m in sorted(measured_by_basis.items()):
        gate = m["gate"]
        if not gate["pass_one_sided_99"]:
            p10 = m.get("p10")
            if p10 is not None and p10["passed"]:
                flags.append(
                    {
                        "basis": basis,
                        "code": "GATE_FAIL_DEM_FORMAT_BOTTLENECK",
                        "text": "GATE fail with P10 in band: verify pins/splits first; if genuine, "
                        "the independent-edges DEM-prior format is the bottleneck — back-edge to "
                        "ADR 0008 / H3 (structural). ADR fallback: publish the negative + the "
                        "deliverables. No rescue fitting.",
                    }
                )
            elif p10 is not None:
                flags.append(
                    {
                        "basis": basis,
                        "code": "GATE_FAIL_CALIBRATION_DIRECTION",
                        "text": "GATE fail with P10 miss: 'calibration wrong' direction — verify "
                        "pins/splits; no rescue fitting either way.",
                    }
                )
            else:
                flags.append(
                    {
                        "basis": basis,
                        "code": "GATE_FAIL_UNDIAGNOSED",
                        "text": "GATE fail; P10 unavailable — verify pins/splits; diagnosis fork "
                        "requires the P10 forecast comparison.",
                    }
                )
        if m["headline"]["pct_delta"] < HEADLINE_BAND[basis][0]:
            flags.append(
                {
                    "basis": basis,
                    "code": "HEADLINE_NEG_AUDIT_COMPOSITION",
                    "text": "headline < -10%: audit the composition first; if sound, model-implied "
                    "statistics decode worse than empirical — re-derive, re-register.",
                }
            )
        if m["covariation"]["verdict"] != "pass" and m3_nll_structure_intact:
            flags.append(
                {
                    "basis": basis,
                    "code": "COVARIATION_NULL_STRUCTURAL",
                    "text": "covariation null/confound-consistent with the M3 NLL structure intact: "
                    "structural finding to ADR 0008 / H3 (bunching does not transfer through "
                    "independent edges even via dt-tails).",
                }
            )
        if m["regime"]["saturated_majority"]:
            flags.append(
                {
                    "basis": basis,
                    "code": "REGIME_RE_REGISTER",
                    "text": "> 1/2 of windows saturated: re-register on wider sub-codes "
                    "(d' = 9/11 unions) — NEW registration.",
                }
            )
    return flags


# ---------------------------------------------------------------- stage implementations


def _b1():
    """B1 composition module (lazy: built concurrently; synthetic tests run without it)."""
    from qec_twin.hardware import dem_compose

    return dem_compose


def _b2():
    """B2 decode module (lazy: built concurrently; synthetic tests run without it)."""
    from qec_twin.hardware import m4_decode

    return m4_decode


def _dataset():
    from qec_twin.hardware.dataset import RepCodeD29

    return RepCodeD29.from_env()


def _load_fit_cache(path: str | Path) -> dict:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"frozen M3 fit cache not found: {path} (M4 consumes the frozen cache; "
            "zero new twin fits ever)"
        )
    return torch.load(path, weights_only=False)


def _unit_key(kind: str, *parts) -> str:
    return ":".join([kind, *[str(p) for p in parts]])


# -- fix-round glue against the REAL B1/B2 APIs (reviewer SB, B-1..B-16) --------


def _skeleton_context(b1, ds, basis: str):
    """The canonical B1 construction (reviewer B-1; mirrors B1's hardware tests):
    grid via ``m1_report.build_grid``; skeleton parsed from the sample_00
    noisy-SI1000 circuit's exact DEM (``decompose_errors=True,
    flatten_loops=True`` — the shipped S4 recipe). Returns (skel, grid, dem)."""
    from qec_twin.hardware import m1_report, stim_artifacts

    grid = m1_report.build_grid(ds, basis, sample=TRAIN_SAMPLE)
    circuit = stim_artifacts.load_circuit(ds.paths(basis, TRAIN_SAMPLE).circuit_noisy_si1000)
    dem = circuit.detector_error_model(decompose_errors=True, flatten_loops=True)
    return b1.load_skeleton(dem), grid, dem


def _train_counts(ds, basis: str, grid, *, chunk_shots: int):
    """ONE sample_00 pair-count accumulation per basis feeds every unit's A2
    column (reviewer B-5)."""
    from qec_twin.hardware.pij import accumulate_pair_counts

    return accumulate_pair_counts(
        ds.paths(basis, TRAIN_SAMPLE).detection_events, grid, chunk_shots=int(chunk_shots)
    )


def _gate_units(b1, skel, grid, d_prime: int):
    """Maximal-disjoint gate units at d' (reviewer B-2/B-3): partition_table
    supplies names/offsets/hot flags; projection via subchain_skeleton with
    B1's INCLUSIVE data_hi convention (module docstring FIX ROUND note).
    Yields (unit_key, sub_skeleton, partition_row)."""
    units = []
    for row in b1.partition_table(int(d_prime)):
        sub = b1.subchain_skeleton(skel, grid, int(row["data_lo"]), int(row["data_hi"]))
        units.append((_unit_key("rung", int(d_prime), row["name"]), sub, row))
    return units


def _arm_dems(b1, sub, columns: Mapping[str, np.ndarray]):
    """Probability columns -> decodable DEMs (reviewer B-4): every arm builder
    returns a COLUMN; ``with_probabilities`` returns the (dem, ClampReport)
    2-tuple — unpacked here, clamp counts flowing to G9 accounting."""
    dems: dict = {}
    clamps: dict = {}
    for arm, column in columns.items():
        dem, rep = b1.with_probabilities(sub, column)
        dems[arm] = dem
        clamps[arm] = {
            "low_hits": int(rep.low_hits),
            "high_hits": int(rep.high_hits),
            "total_errors": int(rep.total_errors),
        }
    return dems, clamps


def _packed_events(ds, basis: str, sample: int, bits_per_shot: int) -> np.ndarray:
    """Read-only memmap of one full-width detection_events b8 file,
    [shots, ceil(bits/8)] uint8."""
    path = ds.paths(basis, int(sample)).detection_events
    bytes_per_shot = (int(bits_per_shot) + 7) // 8
    raw = np.memmap(path, dtype=np.uint8, mode="r")
    if raw.size % bytes_per_shot:
        raise ValueError(
            f"{path}: {raw.size} bytes is not a whole number of {bytes_per_shot}-byte shots"
        )
    return raw.reshape(-1, bytes_per_shot)


def _unit_bits(packed: np.ndarray, det_ids) -> np.ndarray:
    """bool [shots, n_local] columns of the listed GLOBAL detector ids out of a
    packed full-width b8 array (little bit order — the b8/_bit_column
    convention), in det_ids order (= the emitted DEM's local detector order)."""
    det_ids = np.asarray(det_ids, dtype=np.int64)
    out = np.empty((packed.shape[0], det_ids.size), dtype=np.bool_)
    for j, d in enumerate(det_ids):
        out[:, j] = (packed[:, d >> 3] >> (d & 7)) & 1
    return out


def _unit_actual(
    b2, ds, basis: str, sample: int, unit_pairs, n_shots: int, *, allow_heldout: bool
) -> np.ndarray:
    """Per-unit ACTUAL observable bits via B2's fix-round helper (reviewer
    change item 2); units = (data_lo, data_hi) inclusive pairs (B2's landed
    convention); shape-validated [shots, n_units]. ``allow_heldout`` is set by
    the staged runner ONLY for the held-out stage and the post-held-out 01-04
    context decode (B2's held-out access contract)."""
    fn = _require_unit_actual_observables(b2)
    pairs = [(int(lo), int(hi)) for lo, hi in unit_pairs]
    actual = np.asarray(fn(ds, basis, int(sample), pairs, allow_heldout=bool(allow_heldout)))
    if actual.ndim != 2 or actual.shape != (int(n_shots), len(pairs)):
        raise ValueError(
            f"unit_actual_observables returned shape {actual.shape}, expected "
            f"({int(n_shots)}, {len(pairs)}) — the B2 helper contract is "
            "[shots, n_units] (reviewer B-12)"
        )
    return actual.astype(np.uint8)


def _decode_sample_errors(
    b2,
    ds,
    basis: str,
    sample: int,
    units,
    unit_dems: Mapping[str, Mapping],
    *,
    bits_per_shot: int,
    n_workers: int,
    chunk_shots: int,
    two_pass_rr: Mapping | None = None,
    allow_heldout: bool = False,
    max_batch_columns: int = 24_000,
) -> dict:
    """One (basis, sample) decode of every unit x arm against the REAL B2 fleet
    API (reviewer B-12): stream the packed full-width detection events ONCE
    (memmap), slice each unit's detector columns, build ``DecodeJob``s, run
    ``decode_fleet(jobs) -> [FleetResult]`` (order-aligned, job_id verified),
    and XOR the [shots, 1] PREDICTIONS against the per-unit ACTUAL observable —
    the error arrays every statistic consumes. ``units`` is a list of
    ``(unit_key, det_ids, (data_lo, data_hi))``. With ``two_pass_rr``
    (chain-pair keyed — apply :func:`rr_table_chain_pairs` first, B-16) each
    window unit also runs the A3c two-pass job (mode="two_pass") on its twin
    DEM (B-15)."""
    from qec_twin.hardware import b8_io

    units = [
        (str(k), np.asarray(d, dtype=np.int64), (int(pair[0]), int(pair[1])))
        for k, d, pair in units
    ]
    packed = _packed_events(ds, basis, sample, bits_per_shot)
    n_shots = int(packed.shape[0])
    actual = _unit_actual(
        b2, ds, basis, sample, [pair for _, _, pair in units], n_shots,
        allow_heldout=allow_heldout,
    )
    errors: dict = {}

    def _flush(batch) -> None:
        jobs: list = []
        meta: list = []
        for key, det_ids, col in batch:
            bits = _unit_bits(packed, det_ids)
            packed_unit = b8_io.pack_bits(bits)
            del bits
            for arm, dem in unit_dems[key].items():
                jobs.append(
                    b2.DecodeJob(
                        job_id=f"{key}|{arm}",
                        dem_text=str(dem),
                        dets=packed_unit,
                        chunk_shots=int(chunk_shots),
                    )
                )
                meta.append((key, arm, col))
            if two_pass_rr is not None and key.startswith("window:"):
                jobs.append(
                    b2.DecodeJob(
                        job_id=f"{key}|two_pass",
                        dem_text=str(unit_dems[key]["twin"]),
                        dets=packed_unit,
                        chunk_shots=int(chunk_shots),
                        mode="two_pass",
                        rR_table=dict(two_pass_rr),
                    )
                )
                meta.append((key, "two_pass", col))
        results = b2.decode_fleet(jobs, n_workers=int(n_workers))
        for job, (key, arm, col), res in zip(jobs, meta, results):
            if res.job_id != job.job_id:
                raise RuntimeError("decode_fleet results misaligned with job order")
            preds = np.asarray(res.preds, dtype=np.uint8).reshape(n_shots, -1)[:, 0]
            errors.setdefault(key, {})[arm] = (preds ^ actual[:, col]).astype(np.uint8)

    batch: list = []
    cols = 0
    for i, (key, det_ids, _g) in enumerate(units):
        if batch and cols + det_ids.size > int(max_batch_columns):
            _flush(batch)
            batch, cols = [], 0
        batch.append((key, det_ids, i))
        cols += int(det_ids.size)
    if batch:
        _flush(batch)
    return errors


def _mean_matched_sites(skel, grid, counts, *, bulk_layers) -> tuple[np.ndarray, np.ndarray]:
    """Local detector indices + registered targets of every weight-1-carrying
    (mean-matched) site — ruling 14(i) input: the A2 construction solves the
    singles so the composed site marginal reproduces the measured detection
    fraction EXACTLY (bulk-pooled inside ``bulk_layers``, layer-resolved
    outside)."""
    lo, hi = int(bulk_layers[0]), int(bulk_layers[1])
    m_grid = counts.grid_counts / float(counts.num_shots)
    layer_of = grid.det_to_layer
    chain_of = grid.det_to_chain
    local = {int(g): i for i, g in enumerate(skel.detector_ids)}
    dets = sorted(
        {
            int(skel.dets[i][0])
            for i in range(skel.num_errors)
            if len(skel.comps[i]) == 1 and len(skel.dets[i]) == 1
        }
    )
    idx: list = []
    targets: list = []
    for d in dets:
        layer, chain = int(layer_of[d]), int(chain_of[d])
        if lo <= layer <= hi:
            target = float(m_grid[lo : hi + 1, chain].mean())
        else:
            target = float(m_grid[layer, chain])
        idx.append(local[d])
        targets.append(target)
    return np.asarray(idx, dtype=np.int64), np.asarray(targets, dtype=np.float64)


def _stage_status(args, state: M4State) -> int:
    print(f"M4 order-freeze state ({state.path})")
    print(f"registration: {state.REGISTRATION}; seed {M4_SEED}")
    for name in STAGES:
        entry = state.stage(name)
        if entry is None:
            print(f"  {name:13s} PENDING")
        elif entry.get("completed"):
            print(f"  {name:13s} complete  ({entry['completed']})")
        else:
            print(f"  {name:13s} STARTED-NOT-COMPLETE ({entry['started']})")
    if state._state.get("freeze"):
        print(f"  G2 manifest: {state._state['freeze']['manifest_sha256'][:16]}…")
    return 0


def _stage_pins(args, state: M4State) -> int:
    """S6 machinery pins with the REAL B2 runner signatures (reviewer B-11 —
    B2 ships exactly ``B2_PIN_RUNNERS``; there is NO pin_p1c), P1c through B1's
    round-trip machinery (``P1C_OWNER``), the recorded P1i datum. P1h runs
    inside the freeze stage under the AMENDMENT-1 split. Sample contact per the
    reviewer's run plan: P1a {00, 05-14} byte parity only (escrow 15-19 never
    opened); P1e/P1f {00, 50, 99} (ruling 15); everything else sample_00 or no
    shot data. The corpus RL XOR context count (S1 wiring gap) is measured here
    from P1e's shipped-vs-actual context numbers and consumed by scoring."""
    state.begin("pins")
    b1, b2 = _b1(), _b2()
    ds = _dataset()
    from qec_twin.hardware import b8_io
    from qec_twin.hardware import dataset as hw_dataset

    summary: dict = {}
    rl_xor: dict = {}

    # P1a — m2d byte parity (M1 construction reused verbatim; no decoding)
    per_basis = {}
    for basis in args.bases:
        r = b2.pin_p1a(ds, P1A_SAMPLES, basis, chunk_shots=args.chunk_shots)
        per_basis[basis] = {"samples": [int(s) for s in r["samples"]], "passed": bool(r["passed"])}
    summary["p1a"] = {
        "passed": all(v["passed"] for v in per_basis.values()),
        "per_basis": per_basis,
        "scope_note": "byte parity only; escrow 15-19 NEVER opened (run-plan adjudication)",
    }

    # P1b — observable construction bit-exact at window == full chain
    per_basis = {}
    for basis in args.bases:
        r = b2.pin_p1b(ds, basis, sample=TRAIN_SAMPLE, chunk_shots=args.chunk_shots)
        per_basis[basis] = {
            "circuit_used": r["circuit_used"],
            "total_shots": int(r["total_shots"]),
            "mismatched_shots": int(r["mismatched_shots"]),
            "passed": bool(r["passed"]),
        }
    summary["p1b"] = {"passed": all(v["passed"] for v in per_basis.values()), "per_basis": per_basis}

    # P1c — B1's machinery (reviewer B-11: the phantom pin_p1c call is GONE):
    # parse -> serialize -> parse round-trip on the real SI1000 exact DEM + the
    # full-restriction identity subchain(0, num_chains) == skeleton, per basis.
    per_basis = {}
    for basis in args.bases:
        skel, grid, dem = _skeleton_context(b1, ds, basis)
        rt = b1.roundtrip_report(dem)
        full = b1.subchain_skeleton(skel, grid, 0, grid.num_chains)
        identity = bool(
            full.dets == skel.dets
            and full.obs == skel.obs
            and full.comps == skel.comps
            and np.array_equal(full.p, skel.p)
            and np.array_equal(full.detector_ids, skel.detector_ids)
        )
        passed = bool(
            rt["errors_equal"]
            and rt["p_bitexact_unclamped"]
            and rt["num_detectors_preserved"]
            and identity
        )
        per_basis[basis] = {
            "roundtrip": {
                k: rt[k]
                for k in (
                    "errors_equal",
                    "p_bitexact_unclamped",
                    "num_errors",
                    "clamp_low_hits",
                    "clamp_high_hits",
                    "num_detectors_preserved",
                )
            },
            "full_restriction_identity": identity,
            "passed": passed,
        }
    summary["p1c"] = {
        "owner": P1C_OWNER,
        "passed": all(v["passed"] for v in per_basis.values()),
        "per_basis": per_basis,
    }

    # P1d — decoder determinism on the shipped RL DEM + a sample_00 dets slice
    per_basis = {}
    for basis in args.bases:
        art = ds.evaluator_decoding_artifacts(basis, TRAIN_SAMPLE)
        dets = b8_io.read_b8(
            ds.paths(basis, TRAIN_SAMPLE).detection_events,
            hw_dataset.NUM_DETECTORS,
            (0, P1D_PROBE_SHOTS),
        )
        r = b2.pin_p1d(b2.as_dem(art.error_model_dem), dets)
        per_basis[basis] = {"n_shots": int(r["n_shots"]), "passed": bool(r["passed"])}
    summary["p1d"] = {"passed": all(v["passed"] for v in per_basis.values()), "per_basis": per_basis}

    # P1e — shipped-prediction reproduction on {00, 50, 99} (ruling 15); the
    # registered halt rule is mismatch > 1e-3; the bit-exact branch is recorded.
    per_basis = {}
    for basis in args.bases:
        r = b2.pin_p1e(ds, P1E_SAMPLES, basis, chunk_shots=max(int(args.chunk_shots) // 5, 1))
        rows = [
            {
                "sample": int(s.sample),
                "n_shots": int(s.n_shots),
                "n_mismatch": int(s.n_mismatch),
                "mismatch_fraction": float(s.mismatch_fraction),
                "shipped_vs_actual_flips": int(s.shipped_vs_actual_flips),
                "ours_vs_actual_flips": int(s.ours_vs_actual_flips),
            }
            for s in r["results"]
        ]
        total_flips = sum(row["shipped_vs_actual_flips"] for row in rows)
        total_shots = sum(row["n_shots"] for row in rows)
        rl_xor[basis] = 1e5 * total_flips / total_shots if total_shots else float("nan")
        per_basis[basis] = {
            "samples": [int(s) for s in r["samples"]],
            "max_mismatch_fraction": float(r["max_mismatch_fraction"]),
            "bit_exact": float(r["max_mismatch_fraction"]) == 0.0,
            "passed": bool(float(r["max_mismatch_fraction"]) <= P1E_HALT_MISMATCH),
            "per_sample": rows,
        }
    summary["p1e"] = {
        "passed": all(v["passed"] for v in per_basis.values()),
        "halt_rule": f"mismatch > {P1E_HALT_MISMATCH:g} => HALT + degeneracy audit (registered)",
        "per_basis": per_basis,
    }

    # P1f — hash audit over {00, 50, 99} (report-only, no gate)
    r = b2.pin_p1f(ds, P1E_SAMPLES, bases=tuple(args.bases))
    summary["p1f"] = {
        "passed": True,
        "report_only": True,
        "num_distinct": int(r["num_distinct"]),
        "groups": {digest: [list(k) for k in keys] for digest, keys in r["groups"].items()},
    }

    # P1g — exact minimum-weight reference (no data)
    r = b2.pin_p1g()
    summary["p1g"] = {
        "passed": bool(r["passed"]),
        "toys": [
            {k: t[k] for k in ("toy", "num_ties", "num_disagreements", "passed")}
            for t in r["results"]
        ],
    }

    summary["p1i"] = {"recorded": True, **P1I_BRANCH}

    for name in ("p1a", "p1b", "p1c", "p1d", "p1e", "p1f", "p1g"):
        print(f"  P1{name[-1]}: {'ok' if summary[name].get('passed', True) else 'FAIL'}", flush=True)
    passed = all(entry.get("passed", True) for entry in summary.values())
    if not passed:
        print("P1 pin failure => build bug; nothing downstream (S10).")
        return 1
    state.complete("pins", {"results": summary, "rl_xor_per_1e5": rl_xor})
    return 0


def _stage_freeze(args, state: M4State) -> int:
    """G2 composition freeze under AMENDMENT 1 ruling 14: the amended P1h runs
    on the TWIN composition column (the arm actually being frozen) with A2 (pij)
    reported alongside; the freeze HALTS ONLY on the STRUCTURAL component; the
    registered +/-0.5% per-site band is scored-and-reported per arm — a miss is
    the REGISTERED FINDING (M3/ADR-0008-H3 back-edge tag), never a halt, never
    a tolerance edit. Manifest per the run plan (reviewer F stage 2): cache keys
    from the ownership tables; fill table incl. the decomposed-passthrough
    census (C-1 condition i); clamp tables; support census; partition offsets;
    the sim-round-trip pass rule (C-5); the sliding-window drop record."""
    state.begin("freeze")
    b1, b2 = _b1(), _b2()
    ds = _dataset()
    cache = _load_fit_cache(args.fit_cache)
    p1h: dict = {}
    fill_table: dict = {}
    clamp_table: dict = {}
    support_table: dict = {}
    cache_keys: set = set()
    structural_ok = True
    for basis in args.bases:
        skel, grid, _dem = _skeleton_context(b1, ds, basis)
        counts = _train_counts(ds, basis, grid, chunk_shots=args.chunk_shots)
        pij_col, pij_report = b1.arm_pij(counts, grid, skel, return_report=True)
        twin_col, ownership = b1.arm_twin_static(
            cache, CLEAN_WINDOWS, grid, pij_col, skel=skel, basis=basis
        )
        cache_keys.update(str(k) for k in ownership["cache_keys"])
        f_global = b1.detection_fraction_global(counts, grid)

        # amended P1h: band scored per arm (TWIN + A2); structural gate on TWIN
        rows: dict = {"arms": {}}
        twin_marginals = None
        for arm, column in (("twin", twin_col), ("pij", pij_col)):
            marginals, res = b1.acceptance_check(skel, column, f_global)
            rows["arms"][arm] = p1h_band_row(
                arm,
                num_out=res.num_out,
                num_sites=res.num_sites,
                max_abs_dev=res.max_abs_dev,
                mean_abs_dev=res.mean_abs_dev,
                tol=res.tol,
            )
            if arm == "twin":
                twin_marginals = marginals
        measured = np.asarray(f_global, dtype=np.float64)[skel.detector_ids]
        mm_idx, mm_targets = _mean_matched_sites(
            skel, grid, counts, bulk_layers=(b1.BULK_LAYER_LO, b1.BULK_LAYER_HI)
        )
        chains = grid.det_to_chain[skel.detector_ids]
        interior_idx = np.flatnonzero((chains > 0) & (chains < grid.num_chains - 1))
        rows["structural"] = p1h_structural_gate(
            twin_marginals,
            measured,
            mean_matched_idx=mm_idx,
            mean_matched_targets=mm_targets,
            interior_idx=interior_idx,
        )
        structural_ok = structural_ok and rows["structural"]["passed"]
        p1h[basis] = rows

        fill_table[basis] = {
            "rule": (
                "ALL unowned cells carry the train-pij values IDENTICALLY (S5; "
                "attribution by construction); decomposed instructions carry the "
                "shipped SI1000 value (clamped) in EVERY constructed arm — the C-1 "
                "accepted passthrough, contrast-neutral by construction"
            ),
            "unowned_census": ownership["unowned_census"],
            "num_assigned": int(ownership["num_assigned"]),
            "num_unowned": int(ownership["num_unowned"]),
            "unowned_identical_to_pij": bool(ownership["unowned_identical_to_pij"]),
            "hot_region_disclosure": ownership["hot_region_disclosure"],
            "decomposed_passthrough_slots": int(ownership["unowned_census"]["decomposed"]),
        }
        clamp_table[basis] = {"pij_estimator_report": dict(pij_report)}
        support_table[basis] = b1.support_census(
            {
                "naive": (skel, b1.arm_naive(skel)),
                "pij": (skel, pij_col),
                "twin": (skel, twin_col),
            },
            grid=grid,
        )

    if not structural_ok:
        print(
            "P1h STRUCTURAL component FAILED => build bug (S10); freeze NOT recorded. "
            "(The +/-0.5% per-site band never halts — AMENDMENT 1 ruling 14(ii) scores "
            "it per arm.)"
        )
        for basis, rows in p1h.items():
            for reason in rows["structural"]["reasons"]:
                print(f"  {basis}: {reason}")
        return 1
    manifest = b1.freeze_manifest(
        cache_keys=sorted(cache_keys),
        fill_table=fill_table,
        clamp_table=clamp_table,
        support_table=support_table,
        extra={
            "p1h_amended": p1h,
            "sim_round_trip_pass_rule": getattr(
                b2, "SIM_ROUND_TRIP_RULE",
                getattr(b2, "SIM_ROUND_TRIP_PASS_RULE", SIM_ROUND_TRIP_PASS_RULE),
            ),
            "partition_offsets": {str(d): b1.partition_table(d) for d in RUNG_GRID},
            "sliding_window_secondary": SLIDING_WINDOW_SECONDARY,
        },
    )
    record = state.record_freeze(
        manifest=manifest,
        source_hashes=composition_source_hashes(args.fit_cache),
        extra={"p1h": p1h},
    )
    state.complete(
        "freeze",
        {
            "manifest_sha256": record["manifest_sha256"],
            "p1h_structural_passed": True,
            "p1h_band_in_band": {
                basis: {arm: row["in_band"] for arm, row in rows["arms"].items()}
                for basis, rows in p1h.items()
            },
        },
    )
    print(f"composition frozen: manifest sha256 {record['manifest_sha256']}")
    for basis, rows in p1h.items():
        for arm, row in rows["arms"].items():
            verdict = (
                "in band"
                if row["in_band"]
                else "BAND MISS -> REGISTERED FINDING (ruling 14(ii); never a halt)"
            )
            print(f"  P1h band {basis}/{arm}: {row['num_out']}/{row['num_sites']} out — {verdict}")
    return 0


def _stage_pilot(args, state: M4State) -> int:
    """S3 TRAIN-ONLY pilot: sample_00 ONLY, arms A1+A2 ONLY, full grid + 19
    windows. Fix round: columns -> DEMs via with_probabilities (B-4), units via
    partition_table/subchain_skeleton + window_skeleton (B-2/B-3), one pair-count
    accumulation per basis (B-5), decode through the real fleet with per-unit
    actual observables (B-12)."""
    state.begin("pilot")
    b1, b2 = _b1(), _b2()
    ds = _dataset()
    table: dict = {
        "seed": M4_SEED,
        "samples": list(PILOT_SAMPLES),
        "arms": list(PILOT_ARMS),
        "bases": {},
        "clamp_counts": {},  # G9
    }
    pooled_cells: dict[int, list[float]] = {d: [0.0, 0.0] for d in RUNG_GRID}  # [errors, cells]
    for basis in args.bases:
        skel, grid, _dem = _skeleton_context(b1, ds, basis)
        counts = _train_counts(ds, basis, grid, chunk_shots=args.chunk_shots)
        units: list = []  # (key, det_ids, (data_lo, data_hi))
        unit_dems: dict = {}
        hot_by_key: dict = {}
        clamp_total = {
            arm: {"low_hits": 0, "high_hits": 0, "total_errors": 0} for arm in PILOT_ARMS
        }

        def _add_unit(key: str, sub, unit_pair, hot: bool) -> None:
            columns = {"naive": b1.arm_naive(sub), "pij": b1.arm_pij(counts, grid, sub)}
            pilot_assert_arms(columns)  # S3: the twin arm is never decoded in the pilot
            dems, clamps = _arm_dems(b1, sub, columns)
            unit_dems[key] = dems
            for arm, rep in clamps.items():
                for field, value in rep.items():
                    clamp_total[arm][field] += value
            hot_by_key[key] = bool(hot)
            units.append((key, sub.detector_ids, unit_pair))

        for d in RUNG_GRID:
            for key, sub, row in _gate_units(b1, skel, grid, d):
                _add_unit(key, sub, (int(row["data_lo"]), int(row["data_hi"])), bool(row["hot"]))
        for w in CLEAN_WINDOWS:
            _add_unit(
                _unit_key("window", w),
                b1.window_skeleton(skel, grid, w),
                (int(w) + 1, int(w) + 5),
                False,
            )

        errors = _decode_sample_errors(
            b2,
            ds,
            basis,
            TRAIN_SAMPLE,
            units,
            unit_dems,
            bits_per_shot=grid.num_layers * grid.num_chains,
            n_workers=args.workers,
            chunk_shots=args.chunk_shots,
        )
        basis_rows: dict = {"rungs": {}, "windows": {}}
        for d in RUNG_GRID:
            keys = sorted(k for k in errors if k.startswith(f"rung:{d}:"))
            naive = np.stack([errors[k]["naive"] for k in keys], axis=1)
            pij = np.stack([errors[k]["pij"] for k in keys], axis=1)
            disc = float((naive.astype(bool) ^ pij.astype(bool)).mean())
            basis_rows["rungs"][str(d)] = {
                "positions": {
                    k.split(":", 2)[2]: {
                        "naive": float(errors[k]["naive"].mean()),
                        "pij": float(errors[k]["pij"].mean()),
                        "hot": hot_by_key[k],
                    }
                    for k in keys
                },
                "pooled": {"naive": float(naive.mean()), "pij": float(pij.mean())},
                "n_cells": int(naive.size),
                "discordance_naive_pij": disc,
            }
            pooled_cells[d][0] += float(pij.sum())
            pooled_cells[d][1] += float(pij.size)
        for w in CLEAN_WINDOWS:
            row = errors[_unit_key("window", w)]
            basis_rows["windows"][str(w)] = {
                "naive": float(row["naive"].mean()),
                "pij": float(row["pij"].mean()),
            }
        table["bases"][basis] = basis_rows
        table["clamp_counts"][basis] = clamp_total
    table["pooled_over_bases_pij_ladder"] = {
        str(d): (cells[0] / cells[1] if cells[1] else float("nan")) for d, cells in pooled_cells.items()
    }
    table["note"] = (
        "Pilot LERs are DESIGN INPUTS, in-sample, never quoted as performance numbers (S3)."
    )
    path = state.dir / "pilot_table.json"
    sha = _dump_json(table, path)
    state.complete("pilot", {"table_path": str(path), "sha256": sha})
    print(f"pilot table written: {path}")
    return 0


def _stage_select_rung(args, state: M4State) -> int:
    """S3 mechanical rung selection on the pilot table + the Lambda-hat ladder."""
    state.begin("select_rung")
    table = json.loads(Path(state.payload("pilot")["table_path"]).read_text(encoding="utf-8"))
    pooled = {int(d): float(v) for d, v in table["pooled_over_bases_pij_ladder"].items()}
    selection = select_rung(pooled)
    per_basis = {}
    for basis, rows in table["bases"].items():
        ladder = {int(d): float(r["pooled"]["pij"]) for d, r in rows["rungs"].items()}
        per_basis[basis] = {
            "selection": select_rung(ladder),
            "lambda_ladder_pij": lambda_ladder(ladder),
            "lambda_ladder_naive": lambda_ladder(
                {int(d): float(r["pooled"]["naive"]) for d, r in rows["rungs"].items()}
            ),
        }
    disagreement = len({pb["selection"]["d_prime_star"] for pb in per_basis.values()}) > 1
    payload = {
        "selection": selection,
        "per_basis": per_basis,
        "per_basis_disagreement_flag": disagreement,
        "ladder_pooling_note": "d'* selected once on the count-weighted pooled-over-bases pij "
        "ladder (design rule, not a claim — module adjudication note)",
    }
    state.complete("select_rung", payload)
    print(f"d'* = {selection['d_prime_star']} (flag: {selection['flag']}); "
          f"per-basis disagreement: {disagreement}")
    return 0


def _stage_p10_forecast(args, state: M4State) -> int:
    """P10 forecasts recorded to a timestamped file BEFORE the held-out pass.
    Model sampling on GPU (project rule); decoding CPU (ratified R1)."""
    state.begin("p10_forecast")
    if not torch.cuda.is_available():
        raise OrderFreezeError(
            "P10 model sampling is GPU-only (project rule: model compute never falls "
            "back to CPU); no CUDA device available"
        )
    b1, b2 = _b1(), _b2()
    ds = _dataset()
    cache = _load_fit_cache(args.fit_cache)
    contexts = {}
    for basis in args.bases:
        skel, grid, _dem = _skeleton_context(b1, ds, basis)
        counts = _train_counts(ds, basis, grid, chunk_shots=args.chunk_shots)
        contexts[basis] = (skel, grid, counts)

    def dem_for_window(basis: str, window: int):
        """The twin-arm window DEM (fix round B-3/B-6): window_skeleton + pij
        fill on the window support + the S5 composition (global clean-window
        ownership) + with_probabilities (tuple unpacked)."""
        skel, grid, counts = contexts[basis]
        sub = b1.window_skeleton(skel, grid, window)
        # the GPU sampler emits layer-major (t*4 + k) detector columns; the
        # emitted DEM's local order is sorted-global — assert they coincide
        ids = np.asarray(sub.detector_ids, dtype=np.int64)
        lex = grid.det_to_layer[ids].astype(np.int64) * grid.num_chains + grid.det_to_chain[ids]
        if not np.all(np.diff(lex) > 0):
            raise RuntimeError(
                "window detector ids are not (layer, chain)-lexicographic — the P10 "
                "sampler column order would be wrong (build bug, nothing downstream)"
            )
        pij_col = b1.arm_pij(counts, grid, sub)
        twin_col, _ownership = b1.arm_twin_static(
            cache, CLEAN_WINDOWS, grid, pij_col, skel=sub, basis=basis
        )
        dem, _clamp = b1.with_probabilities(sub, twin_col)
        return dem

    forecast = p10_forecast(
        cache,
        dem_for_window=dem_for_window,
        decode_fn=b2.decode_dem,
        bases=tuple(args.bases),
        windows=CLEAN_WINDOWS,
        mc_shots=args.mc_shots,
        device="cuda",
        seed=M4_SEED,
    )
    path = state.dir / f"p10_forecast_{_utc_stamp()}.json"
    sha = _dump_json(forecast, path)
    state.complete("p10_forecast", {"forecast_path": str(path), "sha256": sha})
    print(f"P10 forecast recorded BEFORE the held-out pass: {path}")
    return 0


def _stage_floor_check(args, state: M4State) -> int:
    """S8 baseline-only floor check: reads ONLY baseline-arm numbers from the
    pilot table (the pilot contains no twin arm by construction)."""
    state.begin("floor_check")
    table = json.loads(Path(state.payload("pilot")["table_path"]).read_text(encoding="utf-8"))
    d_star = state.payload("select_rung")["selection"]["d_prime_star"]
    n_heldout = len(HELDOUT_PRIMARY_SAMPLES) * 100_000  # 5e5 shots/basis (S1)
    rows = {}
    extend = False
    for basis, basis_rows in table["bases"].items():
        rung = basis_rows["rungs"][str(d_star)]
        central = gate_band_for_rung(basis, d_star)["central"]
        rows[basis] = floor_check(
            {"naive": rung["pooled"]["naive"], "pij": rung["pooled"]["pij"]},
            n_heldout_shots=n_heldout,
            gate_central_pct=central,
            baseline_discordance=rung.get("discordance_naive_pij"),
        )
        extend = extend or rows[basis]["extend"]
    payload = {"per_basis": rows, "extend": extend, "heldout_samples": list(heldout_samples(extend))}
    state.complete("floor_check", payload)
    print(f"baseline-only floor check: extend = {extend}; held-out samples {payload['heldout_samples']}")
    return 0


def _stage_heldout(args, state: M4State) -> int:
    """The ONE held-out pass (S12): G2-checked entry, attempt persisted before
    any decode; decodes the registered held-out samples only. Fix round: real
    arm constructors (columns -> with_probabilities DEMs, B-4..B-7), G4 guards
    on the REAL signatures (sim_round_trip(dem, n_shots) consumed through the
    declared C-5 pass rule; jitter_control(dem, dets, eps=) on a sample_00
    train slice — B-13/B-14), the A3c two-pass through the fleet with the
    chain-pair rR table (B-15/B-16), per-shot ERRORS via the per-unit actual
    observable (B-12)."""
    state.check_order("heldout")  # refuse early, before touching B1/B2 or data
    extend = bool(state.payload("floor_check")["extend"])
    samples = heldout_samples(extend)
    src = composition_source_hashes(args.fit_cache)
    state.begin_heldout(current_source_hashes=src, samples=samples)
    b1, b2 = _b1(), _b2()
    ds = _dataset()
    cache = _load_fit_cache(args.fit_cache)
    d_star = int(state.payload("select_rung")["selection"]["d_prime_star"])
    saved = []
    for basis in args.bases:
        skel, grid, _dem = _skeleton_context(b1, ds, basis)
        counts = _train_counts(ds, basis, grid, chunk_shots=args.chunk_shots)
        bits_per_shot = grid.num_layers * grid.num_chains
        units: list = []  # (key, det_ids, (data_lo, data_hi))
        unit_dems: dict = {}
        clamp_rows: dict = {}
        subs: dict = {}

        def _add_unit(key: str, sub, unit_pair, columns: dict) -> None:
            dems, clamps = _arm_dems(b1, sub, columns)
            unit_dems[key] = dems
            clamp_rows[key] = clamps
            subs[key] = sub
            units.append((key, sub.detector_ids, unit_pair))

        for key, sub, row in _gate_units(b1, skel, grid, d_star):
            pij_col = b1.arm_pij(counts, grid, sub)
            twin_col, _own = b1.arm_twin_static(
                cache, CLEAN_WINDOWS, grid, pij_col, skel=sub, basis=basis
            )
            _add_unit(
                key, sub, (int(row["data_lo"]), int(row["data_hi"])),
                {"naive": b1.arm_naive(sub), "pij": pij_col, "twin": twin_col},
            )
        for w in CLEAN_WINDOWS:
            sub = b1.window_skeleton(skel, grid, w)
            pij_col = b1.arm_pij(counts, grid, sub)
            twin_col, _own = b1.arm_twin_static(
                cache, CLEAN_WINDOWS, grid, pij_col, skel=sub, basis=basis
            )
            a3b_col = b1.arm_spitz_of_twin(
                cache, CLEAN_WINDOWS, grid, sub, basis=basis, pij_probs=pij_col
            )
            _add_unit(
                _unit_key("window", w), sub, (int(w) + 1, int(w) + 5),
                {
                    "naive": b1.arm_naive(sub),
                    "pij": pij_col,
                    "twin": twin_col,
                    "spitz_of_twin": a3b_col,
                },
            )

        # A3c rR table: B1 keys by data qubit g -> B2 chain pairs (B-16 adaptor)
        rr = rr_table_chain_pairs(b1.two_pass_table(cache, CLEAN_WINDOWS, basis=basis))

        # G4 guards on the probe unit, per arm: sim round-trip consumed through
        # the declared (c) pass rule (C-5; SimRoundTripResult is a NamedTuple,
        # B-13) + the +/-1e-9 weight-jitter flip rate on a sample_00 TRAIN dets
        # slice (no extra held-out exposure; the guard probes machinery, B-14).
        probe_key = _unit_key("window", CLEAN_WINDOWS[0])
        train_packed = _packed_events(ds, basis, TRAIN_SAMPLE, bits_per_shot)
        probe_bits = _unit_bits(train_packed[:GUARD_JITTER_SHOTS], subs[probe_key].detector_ids)
        # B2's fix round ships the declared rule itself (sim_round_trip_check /
        # SIM_ROUND_TRIP_RULE) — preferred; the local C-5 wrapper is the fallback.
        checker = getattr(b2, "sim_round_trip_check", None)
        guards: dict = {
            "rule": getattr(
                b2, "SIM_ROUND_TRIP_RULE",
                getattr(b2, "SIM_ROUND_TRIP_PASS_RULE", SIM_ROUND_TRIP_PASS_RULE),
            ),
            "sim_round_trip": {},
            "jitter_flip_rate": {},
        }
        for arm, dem in unit_dems[probe_key].items():
            if checker is not None:
                guards["sim_round_trip"][arm] = dict(
                    checker(dem, n_shots=GUARD_SIM_SHOTS, seed=M4_SEED)._asdict()
                )
            else:
                guards["sim_round_trip"][arm] = sim_round_trip_pass(
                    b2.sim_round_trip(dem, n_shots=GUARD_SIM_SHOTS, seed=M4_SEED)
                )
            guards["jitter_flip_rate"][arm] = float(
                b2.jitter_control(dem, probe_bits, eps=1e-9, seed=M4_SEED)
            )
        _dump_json(guards, state.dir / f"heldout_guards_{basis}.json")
        _dump_json(clamp_rows, state.dir / f"heldout_clamps_{basis}.json")  # G9
        if not all(g["passed"] for g in guards["sim_round_trip"].values()):
            print("G4 sim round-trip miss => pipeline bug, nothing downstream.")
            return 1

        for sample in samples:
            errors = _decode_sample_errors(
                b2,
                ds,
                basis,
                sample,
                units,
                unit_dems,
                bits_per_shot=bits_per_shot,
                n_workers=args.workers,
                chunk_shots=args.chunk_shots,
                two_pass_rr=rr,  # A3c rides the window units only (never the gate)
                allow_heldout=True,  # B2's held-out access contract: the ONE staged pass
            )
            arrays = {
                f"{key}|{arm}": err for key, arms in errors.items() for arm, err in arms.items()
            }
            out = state.dir / f"heldout_{basis}_s{int(sample):02d}.npz"
            np.savez_compressed(out, **arrays)
            saved.append(str(out))
    state.complete(
        "heldout", {"samples": [int(s) for s in samples], "files": saved, "d_prime_star": d_star}
    )
    print(f"held-out pass complete: {len(saved)} files")
    return 0


def _load_heldout_arrays(state: M4State, basis: str, samples) -> tuple[dict, dict, dict]:
    """Reassemble {arm: [shots, units]} gate/window arrays + per-sample slices."""
    gate: dict[str, list[np.ndarray]] = {}
    window: dict[str, list[np.ndarray]] = {}
    slices: dict[int, slice] = {}
    offset = 0
    for sample in samples:
        data = np.load(state.dir / f"heldout_{basis}_s{int(sample):02d}.npz")
        rung_keys = sorted({k.split("|")[0] for k in data.files if k.startswith("rung:")})
        window_keys = [f"window:{w}" for w in CLEAN_WINDOWS]
        arms_g = sorted({k.split("|")[1] for k in data.files if k.startswith("rung:")})
        arms_w = sorted({k.split("|")[1] for k in data.files if k.startswith("window:")})
        n = data[f"{rung_keys[0]}|{arms_g[0]}"].size
        for arm in arms_g:
            gate.setdefault(arm, []).append(
                np.stack([data[f"{k}|{arm}"] for k in rung_keys], axis=1)
            )
        for arm in arms_w:
            window.setdefault(arm, []).append(
                np.stack([data[f"{k}|{arm}"] for k in window_keys], axis=1)
            )
        slices[int(sample)] = slice(offset, offset + n)
        offset += n
    return (
        {a: np.concatenate(v, axis=0) for a, v in gate.items()},
        {a: np.concatenate(v, axis=0) for a, v in window.items()},
        slices,
    )


def _decode_drift_context(args, state: M4State, d_star: int) -> dict:
    """Samples 01-04, CONTEXT ONLY (S1: design-contaminated; module note 8;
    reviewer change item 6): decoded HERE in the scoring stage, strictly AFTER
    the one held-out pass, at the gate instrument (d'*) — per-sample %dLER rows
    only, NEVER primaries. Arrays persisted for audit."""
    b1, b2 = _b1(), _b2()
    ds = _dataset()
    cache = _load_fit_cache(args.fit_cache)
    out: dict = {}
    for basis in args.bases:
        skel, grid, _dem = _skeleton_context(b1, ds, basis)
        counts = _train_counts(ds, basis, grid, chunk_shots=args.chunk_shots)
        units: list = []
        unit_dems: dict = {}
        for key, sub, row in _gate_units(b1, skel, grid, d_star):
            pij_col = b1.arm_pij(counts, grid, sub)
            twin_col, _own = b1.arm_twin_static(
                cache, CLEAN_WINDOWS, grid, pij_col, skel=sub, basis=basis
            )
            dems, _clamps = _arm_dems(
                b1, sub, {"naive": b1.arm_naive(sub), "pij": pij_col, "twin": twin_col}
            )
            unit_dems[key] = dems
            units.append((key, sub.detector_ids, (int(row["data_lo"]), int(row["data_hi"]))))
        gate_rows: dict = {}
        headline_rows: dict = {}
        for sample in DRIFT_CONTEXT_SAMPLES:
            errors = _decode_sample_errors(
                b2,
                ds,
                basis,
                sample,
                units,
                unit_dems,
                bits_per_shot=grid.num_layers * grid.num_chains,
                n_workers=args.workers,
                chunk_shots=args.chunk_shots,
                # samples 01-04 are design-contaminated CONTEXT (S1) decoded
                # strictly after the one held-out pass (module note 8) — the
                # registered post-held-out exception to B2's held-out contract
                allow_heldout=True,
            )
            arrays = {
                f"{key}|{arm}": err for key, arms in errors.items() for arm, err in arms.items()
            }
            np.savez_compressed(state.dir / f"context_{basis}_s{int(sample):02d}.npz", **arrays)
            keys = sorted(errors)
            twin = np.stack([errors[k]["twin"] for k in keys], axis=1)
            naive = np.stack([errors[k]["naive"] for k in keys], axis=1)
            pij = np.stack([errors[k]["pij"] for k in keys], axis=1)
            gate_rows[int(sample)] = pct_delta_lers(float(twin.mean()), float(naive.mean()))
            headline_rows[int(sample)] = pct_delta_lers(float(twin.mean()), float(pij.mean()))
        out[basis] = {
            "samples": [int(s) for s in DRIFT_CONTEXT_SAMPLES],
            "gate_pct": gate_rows,
            "headline_pct": headline_rows,
            "note": (
                "context-only (design-contaminated, S1); decoded in the scoring stage "
                "strictly after the one held-out pass; never a primary"
            ),
        }
    return out


def _stage_score(args, state: M4State) -> int:
    """S7 scoring + S8 statistics + S10 routing on the one held-out pass.
    Fix-round items (reviewer SF / change item 6): covariation restricted to
    samples 05-09 even under the extension; drift-context 01-04 decoded here
    (context-only); the corpus RL XOR context count wired from the pins stage;
    A3b scored from the saved spitz_of_twin arrays; the dMLE attempt record
    (run-unmodified-or-drop) attached; the sliding-window drop record carried
    into the scored table. Scoring code is not hash-frozen (legal post-freeze),
    but the COMPOSITION still is — the pinned source hashes are re-verified."""
    state.begin("scoring")
    cache = _load_fit_cache(args.fit_cache)
    freeze = state._state.get("freeze") or {}
    pinned = freeze.get("source_hashes", {})
    current = composition_source_hashes(args.fit_cache)
    changed = sorted(k for k in pinned if pinned[k] != current.get(k))
    if changed:
        raise OrderFreezeError(
            f"scoring refused: composition source hash changed for {changed} after the "
            "G2 freeze — the run is VOID; re-register on the escrow samples "
            f"{list(ESCROW_SAMPLES)}"
        )
    d_star = int(state.payload("heldout")["d_prime_star"])
    samples = [int(s) for s in state.payload("heldout")["samples"]]
    forecast = json.loads(
        Path(state.payload("p10_forecast")["forecast_path"]).read_text(encoding="utf-8")
    )
    rl_xor = state.payload("pins").get("rl_xor_per_1e5", {})
    dmle_attempt = load_dmle_attempt(state.dir)
    if dmle_attempt is None:
        print(
            "A4 dMLE attempt record ABSENT — open obligation (run-unmodified-or-drop, "
            "ratified R4): record via m4_report.record_dmle_attempt; the scored row "
            "carries the obligation flag."
        )
    context = _decode_drift_context(args, state, d_star)
    measured = {}
    for basis in args.bases:
        gate_arr, window_arr, slices = _load_heldout_arrays(state, basis, samples)
        measured[basis] = compute_basis_results(
            basis=basis,
            d_prime=d_star,
            gate_errors=gate_arr,
            window_errors=window_arr,
            window_ids=CLEAN_WINDOWS,
            covariates=frozen_covariates(cache, basis),
            p10_predicted={
                int(w): row["predicted_ler"]
                for w, row in forecast["predictions"][basis].items()
            },
            per_sample_slices=slices,
            a3c_errors=window_arr.get("two_pass"),
            a3b_errors=window_arr.get("spitz_of_twin"),
            dmle_errors=window_arr.get("dmle"),
            rl_xor_per_1e5=rl_xor.get(basis),
            drift_context=context.get(basis),
            covariation_samples=HELDOUT_PRIMARY_SAMPLES,
            seed=M4_SEED,
        )
    scored = score_s7(measured, dmle_attempt=dmle_attempt)
    flags = route_s10(measured)
    payload_path = state.dir / "scored_table.json"
    sha = _dump_json({"scored": scored, "routing_flags": flags}, payload_path)
    state.complete("scoring", {"scored_path": str(payload_path), "sha256": sha})
    for row in scored["rows"]:
        print(json.dumps(row, default=_json_default))
    for flag in flags:
        print(f"ROUTING {flag.get('basis', '-')}: {flag['code']}")
    return 0


def _stage_artifacts(args, state: M4State) -> int:
    """S12 deliverables: per-window + per-rung twin .dem, Tier-0 bands + abstain
    flags from the FROZEN cache, the stitched hybrid + seam audit, the
    Lambda-hat ladder row."""
    state.begin("artifacts")
    b1 = _b1()
    ds = _dataset()
    cache = _load_fit_cache(args.fit_cache)
    out = Path(args.artifacts_dir)
    out.mkdir(parents=True, exist_ok=True)
    d_star = int(state.payload("heldout")["d_prime_star"])
    written = []
    for basis in args.bases:
        skel, grid, _dem = _skeleton_context(b1, ds, basis)
        counts = _train_counts(ds, basis, grid, chunk_shots=args.chunk_shots)

        def _twin_dem(sub):
            """Fix round B-6: a REAL emitted DEM (never the (probs, table) tuple repr)."""
            pij_col = b1.arm_pij(counts, grid, sub)
            twin_col, _own = b1.arm_twin_static(
                cache, CLEAN_WINDOWS, grid, pij_col, skel=sub, basis=basis
            )
            dem, _clamp = b1.with_probabilities(sub, twin_col)
            return dem

        for w in CLEAN_WINDOWS:
            dem = _twin_dem(b1.window_skeleton(skel, grid, w))
            path = out / f"twin_{basis}_window_{w:02d}.dem"
            path.write_text(str(dem), encoding="utf-8")
            written.append(str(path))
        for _key, sub, row in _gate_units(b1, skel, grid, d_star):
            dem = _twin_dem(sub)
            path = out / f"twin_{basis}_rung_{d_star}_{row['name']}.dem"
            path.write_text(str(dem), encoding="utf-8")
            written.append(str(path))
        _dump_json(tier0_bands(cache, basis), out / f"tier0_bands_{basis}.json")
        written.append(str(out / f"tier0_bands_{basis}.json"))
        pij_full = b1.arm_pij(counts, grid, skel)
        stitched, seam_audit = b1.stitched_hybrid(
            cache, CLEAN_WINDOWS, grid, skel, pij_probs=pij_full, basis=basis
        )
        (out / f"stitched_hybrid_{basis}.dem").write_text(str(stitched), encoding="utf-8")
        _dump_json(seam_audit, out / f"seam_audit_{basis}.json")
        written += [str(out / f"stitched_hybrid_{basis}.dem"), str(out / f"seam_audit_{basis}.json")]
    ladder_row = {
        "ledger_row": "Lambda-hat ladder (S3 free deliverable; stationarity caveat carried)",
        "selection": state.payload("select_rung"),
        "i1_datum": "ZERO logical errors in 1e7 shots per basis (S1 I-1, ledgered)",
    }
    _dump_json(ladder_row, out / "lambda_ladder_row.json")
    written.append(str(out / "lambda_ladder_row.json"))
    state.complete("artifacts", {"files": written})
    print(f"artifacts written: {len(written)} files under {out}")
    return 0


# ---------------------------------------------------------------- main

_STAGE_DISPATCH = {
    "status": _stage_status,
    "pins": _stage_pins,
    "freeze": _stage_freeze,
    "pilot": _stage_pilot,
    "select-rung": _stage_select_rung,
    "p10-forecast": _stage_p10_forecast,
    "floor-check": _stage_floor_check,
    "heldout": _stage_heldout,
    "score": _stage_score,
    "artifacts": _stage_artifacts,
}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="m4-report",
        description=__doc__.splitlines()[0],
    )
    parser.add_argument("stage", choices=sorted(_STAGE_DISPATCH))
    parser.add_argument("--state-dir", default=STATE_DIR_DEFAULT)
    parser.add_argument("--artifacts-dir", default=ARTIFACTS_DIR_DEFAULT)
    parser.add_argument("--fit-cache", default=FIT_CACHE_DEFAULT)
    parser.add_argument("--bases", nargs="+", default=["X", "Z"])
    parser.add_argument("--mc-shots", type=int, default=P10_MC_SHOTS)
    parser.add_argument("--chunk-shots", type=int, default=10_000)
    parser.add_argument("--workers", type=int, default=16)  # CPU decode fleet (ratified R1)
    args = parser.parse_args(argv)
    state = M4State(args.state_dir)
    try:
        return int(_STAGE_DISPATCH[args.stage](args, state))
    except OrderFreezeError as err:
        print(f"ORDER FREEZE refusal: {err}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
