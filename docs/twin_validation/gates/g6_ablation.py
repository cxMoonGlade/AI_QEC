#!/usr/bin/env python
from __future__ import annotations

r"""G6 GATE — record-level coupling FAITHFULNESS REPORT (Axis-2; re-registered 2026-07-03).

Binds to docs/twin_validation/coupled_teacher_round_gates_prereg.md §5 (revised) EXACTLY, and to
docs/twin_validation/g6_null_model_rederivation_2026-07-03.md (the derivation) +
outputs/twin_validation/g6_null_feasibility_from_constants.py (committed-constant evidence).

WHY THIS GATE CHANGED (amendment G6-A1, prereg §10; done BEFORE any G6 run — predict-before-measure):
the round-delta detector D_{c,r} = m_{c,r-1} XOR m_{c,r} shares the measured bit m_{c,r} with
D_{c,r+1} (record_layout.py:110-135), so the delta stream is MA(1). On a CORRECT teacher the off arm
reads Spitz p_ij(lag1) = mu = p_ro + p_rs - 2 p_ro p_rs = 0.0149 (NOT 0), and lag>=2 = 0 exactly; a
permutation-invariant trajectory-mean-instrument common-mode (~8.7e-5) sits at all lags in shared AND
markovian; the genuine shared-vs-markovian MEMORY signal is second-order (gamma_phi only varies per
round; zeta record-dead; readout/reset at trajectory mean) with N_detect >= ~2.4e8 >> 1e6. The old
pass/fail C2/C3/C4 were therefore unsatisfiable. G6 is re-registered as a FAITHFULNESS REPORT.

WHAT IS GATED (all feasible at N<=1e6):
  R-G6-A (a-exact) off-arm MA(1) closed form: p_ij(lag1) == rate-implied mu within 3 SE per check,
         AND off S1/S2(lag>=2) consistent with 0.   [replaces the broken C4]
  R-G6-B (a-exact) MA(1) 1-dependence: off S2(lag1) |z|>=3 AND off S2(lag2) |z|<3.
  C1     (kept) params vary per round + cross-mech corr >= 0.9 (from truth).
  C5     (kept) zeta-witness r3 ~ 0 in all arms.
  P1     (FIXED) pipeline null on i.i.d. MEASURED bits XORed into deltas reproduces the MA(1) floor
         and does not manufacture correlation above it.   [old P1 drew i.i.d. DELTA bits = wrong null]
  P2     (RELABELED) common-mode sensitivity: a planted per-shot common-rate latent is detected.
  P3     (NEW) planted-MEMORY positive control: an inflated AR(1) memory is caught by the
         shared-minus-permuted difference statistic (validates the difference machinery).
  R-G6-C (b, CONDITIONAL) common-mode equality: IF the common-mode is detected in shared (S2 lag2
         |z|>=3) THEN shared and markovian agree at lag2 (|z_diff|<3). Vacuous-power => reported.

WHAT IS REPORTED (never gates):
  R-G6-D the shared-minus-markovian memory difference (S2 lag>=2) + the derived N_detect bracket —
         the honest sub-detectability finding (mild-1/f record imprint is a FAITHFUL sub-floor).
  Full S1/S2/S3 per-arm tables at lags 1..n_lags; common-mode estimates; independent-GT lag-1 xcheck.

METRIC (METRICS.md DEM-edge row, EXACT Eq.13):
  p_hat_ij = 1/2 - sqrt(1/4 - cov(x_i,x_j)/(1 - 2*<x_i XOR x_j>))
validity domain enforced (denom>0, sqrt-arg>=0); invalid pairs flagged+excluded+counted.
Two-point-only hyperedge blindness stated (Takou-Brown 2504.20212, ledger convention).

SCRIPTED-EXECUTION: committed, __main__-guarded; precondition asserts + printed evidence
(shapes/numbers/hashes) + flushed output; emits g6_ablation.json. GPU-only where the teacher touches
cuda (the orchestrator runs it serially post-review, at the Track-A/Track-B join).
    conda run -n aiqec python docs/twin_validation/gates/g6_ablation.py --config <path>
"""

import argparse
import math
import sys
from typing import Any

import numpy as np

# repo-root sys.path shim lives in _gate_common (imported first).
from _gate_common import (  # noqa: E402  (bare-script sibling import; see below)
    PRIMARY_LAG,
    ConfigError,
    assert_fixture_consistency,
    build_regime,
    cluster_bootstrap_se,
    construct_teacher,
    detector_column_map,
    emit_arm,
    emit_gate_result,
    load_gate_config,
    precondition_n_traj,
    require_min_delta_rounds,
    round_delta_by_round,
    write_evidence,
    zscore,
)

from pathlib import Path as _P  # noqa: E402
if str(_P(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(_P(__file__).resolve().parent))

GATE = "G6_ablation"
FEASIBLE_N = 1_000_000  # (c) the feasibility cap (§5.3)

# (c) registered constants.
BOOT_B = 200
BOOT_SEED = 777
Z_STRUCTURE = 3.0        # (c) structural / equality threshold
Z_PLANTED_MIN = 5.0      # (c) P2/P3 planted-control detection floor
C1_SPREAD_FRAC = 0.90    # (c) >= 90% of inspected shots show per-cycle gamma_phi spread > 0
C1_CROSS_CORR = 0.90     # (c) cross-mech corr(zeta, gamma_phi) >= 0.9
C1_MAX_INSPECT = 256     # (c) min(N, 256) inspected shots
SECONDARY_LAG = 2        # (c) lag>=2 vanishes exactly under MA(1) (the 1-dependence witness)
# P2 (common-mode) planted latent + P3 (memory) planted latent — both sized comfortably detectable.
P2_PLANT_SIGMA = 0.5     # (c) g ~ N(0, 0.5^2) per-shot common-rate multiplier
P2_PLANT_SEED = 424242
P1_NULL_SEED = 131313
P3_PLANT_SEED = 565656
P3_AR1_PHI = 0.85        # (c) AR(1) memory correlation across delta rounds
P3_AR1_LOGIT_GAIN = 2.0  # (c) logit-space gain of the AR(1) latent (inflated => clearly detectable)
P3_BASE_RATE = 0.05      # (c) base delta rate for the planted stream
#: the derived N_detect bracket (conservative single-stat .. optimistic pooled), reported for R-G6-D.
DERIVED_N_DETECT = {"conservative_min": 1.1e10, "conservative_max": 1.2e15,
                    "optimistic_pooled_min": 2.4e8, "derivation":
                    "docs/twin_validation/g6_null_model_rederivation_2026-07-03.md §6"}
DERIVED_COMMON_MODE = 8.7e-5  # (b) per-check common-mode covariance from the committed constants


# =========================================================================== #
# S1 — the ledgered Spitz p_ij (METRICS.md DEM-edge row, EXACT Eq. 13)         #
# =========================================================================== #
def _pij_from_moments(mean_i: float, mean_j: float, mean_ij: float) -> tuple[float, bool]:
    """EXACT Spitz Eq. 13 p_ij from the three moments (single pair). Returns (p_ij, valid)."""

    cov = mean_ij - mean_i * mean_j
    xor = mean_i + mean_j - 2.0 * mean_ij
    denom = 1.0 - 2.0 * xor
    if not (denom > 0.0):
        return float("nan"), False
    arg = 0.25 - cov / denom
    if not (arg >= 0.0):
        return float("nan"), False
    return 0.5 - float(np.sqrt(arg)), True


def spitz_p_ij(cube: np.ndarray, lag: int) -> dict:
    """Pooled lag-`lag` timelike Spitz p_ij over (delta(c,r), delta(c,r+lag)) pairs (§5.1 S1)."""

    n, n_delta, n_stab = cube.shape
    per_pair: list[float] = []
    invalid = 0
    total = 0
    for c in range(n_stab):
        for r in range(n_delta - lag):
            xi = cube[:, r, c].astype(np.float64)
            xj = cube[:, r + lag, c].astype(np.float64)
            total += 1
            pij, valid = _pij_from_moments(float(xi.mean()), float(xj.mean()),
                                           float((xi * xj).mean()))
            if valid:
                per_pair.append(pij)
            else:
                invalid += 1
    pooled = float(np.mean(per_pair)) if per_pair else float("nan")
    return {"pooled_p_ij": pooled, "n_pairs_total": total, "n_pairs_valid": len(per_pair),
            "n_pairs_invalid": invalid, "per_pair": per_pair, "lag": int(lag)}


def _pooled_pij_scalar(cube: np.ndarray, lag: int) -> float:
    """Pooled lag-`lag` p_ij as a bootstrap-statistic scalar (nan if no valid pair)."""

    return spitz_p_ij(cube, lag)["pooled_p_ij"]


def per_check_pij_lag1(cube: np.ndarray, check: int) -> float:
    """Pooled lag-1 Spitz p_ij for ONE check (mean over r of the per-pair Eq.13 value)."""

    n, n_delta, n_stab = cube.shape
    vals: list[float] = []
    for r in range(n_delta - 1):
        xi = cube[:, r, check].astype(np.float64)
        xj = cube[:, r + 1, check].astype(np.float64)
        pij, valid = _pij_from_moments(float(xi.mean()), float(xj.mean()), float((xi * xj).mean()))
        if valid:
            vals.append(pij)
    return float(np.mean(vals)) if vals else float("nan")


def per_check_rate_implied_mu(cube: np.ndarray, check: int) -> float:
    """Rate-implied per-measured-bit flip mu from the check's mean delta rate: mu=(1-sqrt(1-2q))/2.

    (a-exact for an MA(1) delta stream: <D>=2mu(1-mu) => mu=(1-sqrt(1-2<D>))/2.)
    """

    q = float(cube[:, :, check].mean())
    arg = 1.0 - 2.0 * q
    if arg < 0.0:
        return float("nan")
    return 0.5 * (1.0 - math.sqrt(arg))


# =========================================================================== #
# S2 — lag-l autocovariance of per-round detector counts (§5.1 S2)            #
# =========================================================================== #
def s2_count_autocov(cube: np.ndarray, lag: int) -> float:
    """c_l = mean over r of Cov_shots(D_r, D_{r+lag}), D_r = sum_c x_{c,r} (per-round det count)."""

    n, n_delta, n_stab = cube.shape
    counts = cube.sum(axis=2).astype(np.float64)  # (N, n_delta)
    vals = []
    for r in range(n_delta - lag):
        a = counts[:, r]
        b = counts[:, r + lag]
        vals.append(float(np.mean((a - a.mean()) * (b - b.mean()))))
    return float(np.mean(vals)) if vals else float("nan")


# =========================================================================== #
# S3 — cross-mechanism r3 = Pearson(sum_r D_r, obs)  (§5.1 S3, the zeta-witness)#
# =========================================================================== #
def s3_r3(cube: np.ndarray, obs: np.ndarray) -> tuple[float, bool]:
    """r3 = Pearson_shots(sum_r D_r, obs). Degenerate: Var(obs)==0 => r3:=0 + flag."""

    total_counts = cube.sum(axis=(1, 2)).astype(np.float64)  # (N,)
    o = obs.astype(np.float64)
    if o.std() == 0.0 or total_counts.std() == 0.0:
        return 0.0, True
    r = float(np.corrcoef(total_counts, o)[0, 1])
    return (r if np.isfinite(r) else 0.0), False


# =========================================================================== #
# per-arm measurement bundle (S1/S2 at all lags + S3) with cluster SEs         #
# =========================================================================== #
def measure_arm(det: np.ndarray, obs: np.ndarray, colmap: dict, n_stab: int, n_lags: int,
                spt: int) -> dict:
    """S1/S2 at lags 1..n_lags + S3, each with a trajectory-cluster bootstrap SE (§2.4)."""

    cube_full = round_delta_by_round(det, colmap, n_stab)  # (N, n_delta, n_stab)
    n_run = det.shape[0]
    out: dict = {"n_run": int(n_run), "shots_per_trajectory": int(spt),
                 "n_delta": int(cube_full.shape[1]), "n_stab": int(n_stab), "s1": {}, "s2": {}}

    for lag in range(1, int(n_lags) + 1):
        s1_point = spitz_p_ij(cube_full, lag)
        s1_boot = cluster_bootstrap_se(
            lambda idx, L=lag: _pooled_pij_scalar(cube_full[idx], L), n_run, spt,
            B=BOOT_B, seed=BOOT_SEED)
        out["s1"][f"lag{lag}"] = {
            "pooled_p_ij": s1_point["pooled_p_ij"], "se": s1_boot["se"],
            "z": zscore(s1_point["pooled_p_ij"], s1_boot["se"]),
            "n_pairs_valid": s1_point["n_pairs_valid"], "n_pairs_invalid": s1_point["n_pairs_invalid"],
            "n_pairs_total": s1_point["n_pairs_total"], "B_effective": s1_boot["B_effective"]}
        s2_point = s2_count_autocov(cube_full, lag)
        s2_boot = cluster_bootstrap_se(
            lambda idx, L=lag: s2_count_autocov(cube_full[idx], L), n_run, spt,
            B=BOOT_B, seed=BOOT_SEED)
        out["s2"][f"lag{lag}"] = {"autocov": s2_point, "se": s2_boot["se"],
                                  "z": zscore(s2_point, s2_boot["se"]),
                                  "B_effective": s2_boot["B_effective"]}

    r3_point, degenerate = s3_r3(cube_full, obs)
    r3_boot = cluster_bootstrap_se(
        lambda idx: s3_r3(cube_full[idx], obs[idx])[0], n_run, spt, B=BOOT_B, seed=BOOT_SEED)
    out["s3"] = {"r3": r3_point, "se": r3_boot["se"], "z": zscore(r3_point, r3_boot["se"]),
                 "degenerate_obs_constant": bool(degenerate), "B_effective": r3_boot["B_effective"]}

    q_hat = float(cube_full.mean())
    out["diagnostics"] = {"pooled_delta_detector_rate_qhat": q_hat,
                          "pileup_fraction_proxy_qhat_over_2": q_hat / 2.0,
                          "n_clusters": (n_run + spt - 1) // spt}
    return out


# =========================================================================== #
# R-G6-A — off-arm MA(1) closed form (a-exact; replaces the broken C4)         #
# =========================================================================== #
def off_arm_ma1_closed_form(cube_off: np.ndarray, spt: int, p_instr_cfg: float,
                            s1_lag2_z: float, s2_lag2_z: float) -> dict:
    """R-G6-A: per-check off-arm p_ij(lag1) == rate-implied mu within 3 SE, AND lag>=2 ~ 0.

    a-EXACT identity (derivation §2): for an MA(1) delta stream, p_ij(lag1)=mu and <D>=2mu(1-mu),
    so p_ij(lag1) == (1-sqrt(1-2<D>))/2. We bootstrap the difference [p_ij(lag1) - rate-implied mu]
    per check (both recomputed on the resample) => z_A; gate |z_A| < 3. The config p_instr is the
    REPORTED anchor (the Z-check equals it; the X-check carries a small extra physical-dephasing
    term). lag>=2 zero is read from the pooled S1/S2 lag-2 z-scores (passed in).
    """

    n, n_delta, n_stab = cube_off.shape
    per_check: list[dict] = []
    all_lag1_ok = True
    for c in range(n_stab):
        def diff_stat(idx, cc=c):
            sub = cube_off[idx]
            return per_check_pij_lag1(sub, cc) - per_check_rate_implied_mu(sub, cc)
        boot = cluster_bootstrap_se(diff_stat, n, spt, B=BOOT_B, seed=BOOT_SEED)
        pij1 = per_check_pij_lag1(cube_off, c)
        mu_rate = per_check_rate_implied_mu(cube_off, c)
        z_a = zscore(boot["point"], boot["se"])
        ok = bool(abs(z_a) < Z_STRUCTURE) if np.isfinite(z_a) else False
        all_lag1_ok = all_lag1_ok and ok
        per_check.append({"check": c, "pij_lag1": pij1, "rate_implied_mu": mu_rate,
                          "p_instr_cfg": p_instr_cfg, "diff": boot["point"], "se": boot["se"],
                          "z_identity": z_a, "identity_holds": ok})
    lag2_zero = bool(abs(s1_lag2_z) < Z_STRUCTURE and abs(s2_lag2_z) < Z_STRUCTURE)
    passed = bool(all_lag1_ok and lag2_zero)
    return {"per_check": per_check, "all_lag1_identity_holds": bool(all_lag1_ok),
            "lag2_consistent_zero": lag2_zero, "s1_lag2_z": s1_lag2_z, "s2_lag2_z": s2_lag2_z,
            "pass": passed,
            "note": "a-exact MA(1): p_ij(lag1)=(1-sqrt(1-2<D>))/2; the Z-check anchor is "
                    f"p_instr={p_instr_cfg:.6f}; a wiring bug (wrong fold/non-i.i.d. rounds) breaks it"}


# =========================================================================== #
# L6 independent-GT (§8.2): lag-1 p_ij closed form vs DIRECT covariance route  #
# =========================================================================== #
def independent_gt_lag1_pij(cube: np.ndarray) -> dict:
    """Cross-check the lag-1 pooled p_ij (closed Eq.13) vs a DIRECT covariance reconstruction."""

    n, n_delta, n_stab = cube.shape
    closed_vals: list[float] = []
    direct_vals: list[float] = []
    for c in range(n_stab):
        for r in range(n_delta - 1):
            xi = cube[:, r, c].astype(np.float64)
            xj = cube[:, r + 1, c].astype(np.float64)
            mi, mj, mij = float(xi.mean()), float(xj.mean()), float((xi * xj).mean())
            pc, valid_c = _pij_from_moments(mi, mj, mij)
            cov_direct = float(np.mean(xi * xj) - np.mean(xi) * np.mean(xj))
            xor_direct = float(np.mean((xi.astype(int) ^ xj.astype(int)).astype(np.float64)))
            denom_direct = 1.0 - 2.0 * xor_direct
            valid_d = denom_direct > 0.0 and (0.25 - cov_direct / denom_direct) >= 0.0
            if valid_c and valid_d:
                pd = 0.5 - float(np.sqrt(0.25 - cov_direct / denom_direct))
                closed_vals.append(pc)
                direct_vals.append(pd)
    if not closed_vals:
        return {"max_abs_diff": float("nan"), "n_pairs": 0, "tol": 1e-12, "pass": False,
                "note": "no valid lag-1 pair for the cross-check"}
    diffs = np.abs(np.asarray(closed_vals) - np.asarray(direct_vals))
    max_diff = float(diffs.max())
    return {"max_abs_diff": max_diff, "n_pairs": len(closed_vals), "tol": 1e-12,
            "pass": bool(max_diff <= 1e-12),
            "note": "two hand-written formula routes on identical bits; a typo in either separates "
                    "them beyond 1e-12 (§8.2 L6)"}


# =========================================================================== #
# C1 — R1 positive control (params must vary; cross-mech corr) from truth      #
# =========================================================================== #
_PER_CYCLE_KEYS = ("params_manifest_sample", "per_cycle_params", "per_cycle")
_GAMMA_FIELD = "gamma_phi_per_ns"
_ZETA_FIELD = "zz_zeta_radns"


def c1_positive_control(teacher: Any, regime: Any, *, m: int, seed: int, n_inspect: int) -> dict:
    """C1 (red-team R1): per-cycle gamma_phi VARIES across rounds for >= 90% of inspected shots,
    AND cross-mechanism corr(zeta, gamma_phi) >= 0.9 on a shared-arm truth trajectory (§5.2)."""

    n_batch = max(1, min(int(n_inspect), C1_MAX_INSPECT))
    _ = emit_arm(teacher, regime, m=int(m), N=n_batch, seed=int(seed))
    truth = teacher.truth
    last_emit = truth.get("last_emit") or {}
    samples = None
    for key in _PER_CYCLE_KEYS:
        if key in last_emit:
            samples = last_emit[key]
            break
    if not samples:
        raise ConfigError(
            "C1 could not resolve the per-cycle params sample from truth.last_emit "
            f"(tried {_PER_CYCLE_KEYS}); truth.last_emit keys = "
            f"{sorted(last_emit.keys())}; truth keys = {sorted(truth.keys())}")
    gamma_spread_ok = 0
    zeta_series: list[float] = []
    gamma_series: list[float] = []
    inspected = 0
    for entry in samples:
        per_cycle = entry.get("per_cycle") if isinstance(entry, dict) else None
        if not per_cycle:
            continue
        gammas = [float(_field(pc, _GAMMA_FIELD)) for pc in per_cycle]
        zetas = [float(_field(pc, _ZETA_FIELD)) for pc in per_cycle]
        if len(set(np.round(gammas, 18))) >= 2:
            gamma_spread_ok += 1
        zeta_series.extend(zetas)
        gamma_series.extend(gammas)
        inspected += 1
    if inspected == 0:
        raise ConfigError("C1: no per-cycle entries carried a 'per_cycle' list")
    frac_spread = gamma_spread_ok / inspected
    if len(zeta_series) >= 2 and np.std(zeta_series) > 0 and np.std(gamma_series) > 0:
        cross_corr = float(abs(np.corrcoef(zeta_series, gamma_series)[0, 1]))
    else:
        cross_corr = float("nan")
    passed = (frac_spread >= C1_SPREAD_FRAC) and (np.isfinite(cross_corr) and cross_corr >= C1_CROSS_CORR)
    return {"inspected_shots": inspected, "frac_gamma_spread": frac_spread,
            "frac_spread_threshold": C1_SPREAD_FRAC, "cross_mech_corr_zeta_gamma": cross_corr,
            "cross_corr_threshold": C1_CROSS_CORR, "pass": bool(passed),
            "interface_limit": ("the teacher truth surfaces only "
                                f"{inspected} trajectory param-sample(s) (its "
                                "_TRUTH_PARAMS_SAMPLE_TRAJECTORIES knob, widened by F4); a dead "
                                "round_index still collapses frac_spread to 0 (R1 falsifier intact)"),
            "note": "both fields are monotone maps of one z => |corr| near 1 (§5.2 C1)"}


def _field(manifest: Any, name: str) -> float:
    if isinstance(manifest, dict) and name in manifest:
        return float(manifest[name])
    raise ConfigError(f"C1: per-cycle params manifest missing field {name!r}; got keys "
                      f"{sorted(manifest.keys()) if isinstance(manifest, dict) else type(manifest)}")


# =========================================================================== #
# P1 (FIXED) / P2 (relabeled) / P3 (new) — pipeline self-falsification (L10)   #
# =========================================================================== #
def _synth_deltas_from_measured_bits(rates_meas: np.ndarray, n: int, n_stab: int,
                                     seed: int) -> np.ndarray:
    """Draw i.i.d. MEASURED bits at per-(round,check) rates then XOR consecutive -> MA(1) deltas.

    rates_meas: (R, n_stab) per-round measured-bit rate. Returns (n, R-1, n_stab) uint8 deltas.
    """

    R = rates_meas.shape[0]
    rng = np.random.default_rng(int(seed))
    m = (rng.random((n, R, n_stab)) < rates_meas[None, :, :]).astype(np.uint8)  # measured bits
    return (m[:, :-1, :] ^ m[:, 1:, :]).astype(np.uint8)                        # deltas (MA(1))


def p1_pipeline_null_fixed(cube_shared: np.ndarray, cube_off: np.ndarray, spt: int) -> dict:
    """P1 (FIXED): i.i.d. MEASURED bits at the off-arm's implied bit rate, XORed into deltas, must
    reproduce the MA(1) floor (p_ij(lag1) ~ off rate-implied mu) and NOT manufacture lag>=2
    correlation. The OLD P1 drew i.i.d. DELTA bits (the wrong null) and missed the MA(1) structure.
    """

    n, n_delta, n_stab = cube_shared.shape
    R = n_delta + 1
    # per-check implied measured-bit rate from the off arm's delta rate: mu=(1-sqrt(1-2q))/2.
    rates = np.empty((R, n_stab), dtype=np.float64)
    for c in range(n_stab):
        mu_c = per_check_rate_implied_mu(cube_off, c)
        rates[:, c] = np.clip(mu_c if np.isfinite(mu_c) else 0.015, 1e-6, 0.5)
    synth = _synth_deltas_from_measured_bits(rates, n, n_stab, P1_NULL_SEED)
    # the synthetic MA(1) floor value per check.
    mu_expected = float(np.mean([per_check_rate_implied_mu(cube_off, c) for c in range(n_stab)]))
    s1_lag1 = spitz_p_ij(synth, 1)["pooled_p_ij"]
    # lag1 must MATCH the MA(1) floor (not be silent); lag>=2 must be silent (no manufactured corr).
    s2_lag2 = s2_count_autocov(synth, SECONDARY_LAG)
    s2_lag2_boot = cluster_bootstrap_se(
        lambda idx: s2_count_autocov(synth[idx], SECONDARY_LAG), n, spt, B=BOOT_B, seed=BOOT_SEED)
    z_lag2 = zscore(s2_lag2, s2_lag2_boot["se"])
    lag1_matches_floor = bool(abs(s1_lag1 - mu_expected) < 0.05 * max(mu_expected, 1e-3) + 3.0
                              * math.sqrt(max(mu_expected, 1e-6) * (1 - mu_expected) / n))
    lag2_silent = bool(abs(z_lag2) < Z_STRUCTURE)
    return {"synth_p_ij_lag1": s1_lag1, "ma1_floor_mu": mu_expected,
            "lag1_matches_ma1_floor": lag1_matches_floor, "s2_lag2_autocov": s2_lag2,
            "s2_lag2_z": z_lag2, "lag2_silent": lag2_silent,
            "pass": bool(lag1_matches_floor and lag2_silent),
            "note": "i.i.d. MEASURED bits -> deltas reproduce the MA(1) floor (lag1) with NO "
                    "manufactured lag>=2 correlation (fixes the old i.i.d.-delta-bit null, F1)"}


def p2_pipeline_common_mode(cube_shared: np.ndarray, spt: int) -> dict:
    """P2 (RELABELED): a planted per-SHOT common-rate multiplier exp(g), g~N(0,0.5^2), IS a
    common-mode; the pipeline must DETECT it (|z|>=5). This validates common-mode sensitivity —
    NOT memory discrimination (the common-mode is permutation-invariant; §5.2)."""

    n, n_delta, ns = cube_shared.shape
    base = np.clip(cube_shared.mean(axis=0), 1e-4, 0.5)
    rng = np.random.default_rng(P2_PLANT_SEED)
    g = rng.normal(0.0, P2_PLANT_SIGMA, size=n)
    rate = np.clip(base[None, :, :] * np.exp(g)[:, None, None], 0.0, 0.999)
    synth = (rng.random((n, n_delta, ns)) < rate).astype(np.uint8)
    s1 = spitz_p_ij(synth, PRIMARY_LAG)["pooled_p_ij"]
    s1_boot = cluster_bootstrap_se(lambda idx: _pooled_pij_scalar(synth[idx], PRIMARY_LAG),
                                   n, spt, B=BOOT_B, seed=BOOT_SEED)
    s2 = s2_count_autocov(synth, SECONDARY_LAG)   # common-mode is at ALL lags incl. lag>=2
    s2_boot = cluster_bootstrap_se(lambda idx: s2_count_autocov(synth[idx], SECONDARY_LAG),
                                   n, spt, B=BOOT_B, seed=BOOT_SEED)
    z1 = zscore(s1, s1_boot["se"])
    z2 = zscore(s2, s2_boot["se"])
    detected = (abs(z1) >= Z_PLANTED_MIN) or (abs(z2) >= Z_PLANTED_MIN)
    return {"planted_sigma": P2_PLANT_SIGMA, "s1_lag1_z": z1, "s2_lag2_z": z2,
            "threshold": Z_PLANTED_MIN, "detected_as_required": bool(detected),
            "pass": bool(detected),
            "note": "common-mode sensitivity control (permutation-INVARIANT latent); NOT a memory "
                    "discrimination test"}


def _ar1_latent(n: int, n_rounds: int, n_stab: int, phi: float, rng: np.random.Generator) -> np.ndarray:
    """Stationary unit-variance AR(1) latent (n, n_rounds, n_stab), corr phi across rounds."""

    a = np.empty((n, n_rounds, n_stab), dtype=np.float64)
    a[:, 0, :] = rng.normal(size=(n, n_stab))
    noise_scale = math.sqrt(1.0 - phi ** 2)
    for r in range(1, n_rounds):
        a[:, r, :] = phi * a[:, r - 1, :] + noise_scale * rng.normal(size=(n, n_stab))
    return a


def p3_pipeline_planted_memory(n: int, n_delta: int, n_stab: int, spt: int) -> dict:
    """P3 (NEW): an INFLATED AR(1) memory planted DIRECTLY in the delta rate (no structural MA(1)
    masking), caught by the shared-minus-permuted difference statistic (|z|>=5). Validates that the
    difference machinery CAN detect memory when the amplitude is large; the real teacher's amplitude
    is sub-floor and second-order (§5.3), which is exactly why it is NOT gated.

    NOTE: the memory is planted at the DELTA level (deltas drawn as Bernoulli(sigmoid(logit(base) +
    gain*a_r))), NOT via measured-bit XOR — routing through measured bits would reproduce the very
    second-order dilution the derivation identifies, which is the wrong thing for a positive control.
    """

    rng = np.random.default_rng(P3_PLANT_SEED)
    logit_base = math.log(P3_BASE_RATE / (1.0 - P3_BASE_RATE))
    a = _ar1_latent(n, n_delta, n_stab, P3_AR1_PHI, rng)
    p_mem = 1.0 / (1.0 + np.exp(-(logit_base + P3_AR1_LOGIT_GAIN * a)))
    d_mem = (rng.random((n, n_delta, n_stab)) < p_mem).astype(np.uint8)
    # permuted (memory destroyed, per-round marginal set preserved): shuffle the latent rounds.
    a_perm = np.empty_like(a)
    for c in range(n_stab):
        for s in range(n):
            a_perm[s, :, c] = a[s, rng.permutation(n_delta), c]
    p_perm = 1.0 / (1.0 + np.exp(-(logit_base + P3_AR1_LOGIT_GAIN * a_perm)))
    d_perm = (rng.random((n, n_delta, n_stab)) < p_perm).astype(np.uint8)
    diff = difference_z_shared_minus_markov("s2", PRIMARY_LAG, d_mem, d_perm, spt, spt)
    detected = abs(diff["z"]) >= Z_PLANTED_MIN
    return {"ar1_phi": P3_AR1_PHI, "ar1_logit_gain": P3_AR1_LOGIT_GAIN, "difference_z": diff["z"],
            "shared_point": diff["shared_point"], "markovian_point": diff["markovian_point"],
            "threshold": Z_PLANTED_MIN, "detected_as_required": bool(detected),
            "pass": bool(detected),
            "note": "planted-MEMORY positive control: an AR(1) memory (planted directly in the delta "
                    "rate, inflated) is caught by the shared-minus-permuted difference statistic; "
                    "validates the difference machinery. The real teacher's amplitude is sub-floor "
                    "and second-order (§5.3), which is why the memory discriminator is NOT gated."}


# =========================================================================== #
# difference statistic — shared minus markovian, cluster-bootstrapped          #
# =========================================================================== #
def difference_z_shared_minus_markov(stat_name: str, lag: int,
                                     cube_s: np.ndarray, cube_m: np.ndarray,
                                     spt_s: int, spt_m: int) -> dict:
    """z of the shared-minus-markovian difference of a statistic (S1 p_ij or S2 count-autocov)."""

    def stat(cube, arm_stat=stat_name, L=lag):
        return _pooled_pij_scalar(cube, L) if arm_stat == "s1" else s2_count_autocov(cube, L)

    boot_s = cluster_bootstrap_se(lambda idx: stat(cube_s[idx]), cube_s.shape[0], spt_s,
                                  B=BOOT_B, seed=BOOT_SEED)
    boot_m = cluster_bootstrap_se(lambda idx: stat(cube_m[idx]), cube_m.shape[0], spt_m,
                                  B=BOOT_B, seed=BOOT_SEED + 1)
    diff = float(boot_s["point"] - boot_m["point"])
    se_diff = float(np.sqrt(np.nan_to_num(boot_s["se"], nan=0.0) ** 2
                            + np.nan_to_num(boot_m["se"], nan=0.0) ** 2))
    return {"statistic": stat_name, "lag": int(lag), "shared_point": boot_s["point"],
            "markovian_point": boot_m["point"], "difference": diff, "se_diff": se_diff,
            "z": zscore(diff, se_diff)}


# =========================================================================== #
# preconditions + runner                                                      #
# =========================================================================== #
def _preconditions(cfg: dict) -> dict:
    import torch

    assert torch.cuda.is_available(), "G6 teacher is GPU-only; cuda must be available"
    n_run = int(cfg.get("g6_n_override") or cfg["N_star"])
    if n_run > FEASIBLE_N:
        raise ConfigError(f"g6 N_run={n_run} exceeds FEASIBLE_N={FEASIBLE_N} (§5.3)")
    spt = int(cfg.get("shots_per_trajectory", 1))
    n_traj = precondition_n_traj(n_run, spt)
    print(f"[precond] cuda={torch.cuda.is_available()} device={torch.cuda.get_device_name(0)}",
          flush=True)
    from _gate_common import MIN_N_TRAJ
    print(f"[precond] fixture={cfg['fixture']} R*={cfg['R_star']} N_run={n_run} S={spt} "
          f"n_traj(clusters)={n_traj} (floor {MIN_N_TRAJ})", flush=True)
    return {"n_run": n_run, "shots_per_trajectory": spt, "n_traj": n_traj}


def _p_instr_from_truth(teacher: Any) -> float:
    """The committed instrument floor mu = p_ro + p_rs - 2 p_ro p_rs from teacher truth config."""

    cfgm = teacher.truth.get("config", {})
    p_ro = float(cfgm.get("readout_flip_base_p", 1e-2))
    p_rs = float(cfgm.get("reset_flip_base_p", 5e-3))
    return p_ro + p_rs - 2.0 * p_ro * p_rs


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="G6 record-level coupling faithfulness report")
    parser.add_argument("--config", default=None, help="gate_run_config.json (default: gates/ path)")
    args = parser.parse_args(argv)

    print("=" * 78, flush=True)
    print("G6 GATE — record-level coupling FAITHFULNESS REPORT (Axis-2; prereg §5 revised)", flush=True)
    print("=" * 78, flush=True)

    cfg = load_gate_config(args.config)
    pre = _preconditions(cfg)
    n_run, spt = pre["n_run"], pre["shots_per_trajectory"]
    n_lags = int(cfg.get("n_lags", 4))
    m = int(cfg.get("m", 0))
    seeds = cfg.get("seeds", {})
    seed_shared = int(seeds.get("shared", 101))
    seed_markov = int(seeds.get("markovian", 202))
    seed_off = int(seeds.get("off", 303))

    teacher = construct_teacher(cfg)
    regime = build_regime(cfg, teacher)
    p_instr_cfg = _p_instr_from_truth(teacher)
    print(f"[arms] regime={regime}  committed p_instr(mu)={p_instr_cfg:.6f}", flush=True)

    shared = emit_arm(teacher, regime, m=m, N=n_run, seed=seed_shared)
    colmap = detector_column_map(teacher, shared["det"].shape[1])
    fixture_consistency = assert_fixture_consistency(cfg, teacher, shared["det"].shape[1])
    n_stab = int(teacher.n_stab)
    # lag-2 (the MA(1) 1-dependence witness) needs >= 3 delta rounds => R* >= 4.
    require_min_delta_rounds(colmap, n_stab, SECONDARY_LAG + 1, GATE)
    print(f"[arms] det width B={shared['det'].shape[1]} n_stab={n_stab} "
          f"round_delta_cols={colmap['n_round_delta']} final_cols={colmap['n_final_closure']}",
          flush=True)

    markov_teacher = teacher.markovian_baseline()
    markovian = emit_arm(markov_teacher, build_regime(cfg, markov_teacher),
                         m=m, N=n_run, seed=seed_markov)
    off_teacher = teacher.off_source()
    off = emit_arm(off_teacher, build_regime(cfg, off_teacher), m=m, N=n_run, seed=seed_off)

    print("\n[measure] shared / markovian / off — S1(Spitz p_ij) + S2(count autocov) + S3(r3)",
          flush=True)
    meas_shared = measure_arm(shared["det"], shared["obs"], colmap, n_stab, n_lags, spt)
    meas_markov = measure_arm(markovian["det"], markovian["obs"], colmap, n_stab, n_lags, spt)
    meas_off = measure_arm(off["det"], off["obs"], colmap, n_stab, n_lags, spt)
    for name, meas in (("shared", meas_shared), ("markovian", meas_markov), ("off", meas_off)):
        s1_1 = meas["s1"]["lag1"]; s2_1 = meas["s2"]["lag1"]; s2_2 = meas["s2"][f"lag{SECONDARY_LAG}"]
        print(f"  {name:<9} S1@1 p_ij={s1_1['pooled_p_ij']:.4e} z={s1_1['z']:.2f}; "
              f"S2@1 cov={s2_1['autocov']:.3e} z={s2_1['z']:.2f}; "
              f"S2@2 cov={s2_2['autocov']:.3e} z={s2_2['z']:.2f}; "
              f"S3 r3={meas['s3']['r3']:.3e} z={meas['s3']['z']:.2f}", flush=True)

    cubes = {"shared": round_delta_by_round(shared["det"], colmap, n_stab),
             "markovian": round_delta_by_round(markovian["det"], colmap, n_stab),
             "off": round_delta_by_round(off["det"], colmap, n_stab)}
    n_shots = cubes["shared"].shape[0]
    n_delta = cubes["shared"].shape[1]

    # --- L6 independent ground truth on the shared arm (§8.2). ---
    gt = independent_gt_lag1_pij(cubes["shared"])
    print(f"\n[independent-GT] lag-1 Spitz p_ij closed vs DIRECT cov: max|diff|={gt['max_abs_diff']:.3e}"
          f" over {gt['n_pairs']} pairs -> {'PASS' if gt['pass'] else 'FAIL'}", flush=True)

    # --- R-G6-A: off-arm MA(1) closed form (a-exact; replaces C4). ---
    print("\n[R-G6-A] off-arm MA(1) closed form (p_ij(lag1)==rate-implied mu; lag>=2 ~ 0)", flush=True)
    rga = off_arm_ma1_closed_form(
        cubes["off"], spt, p_instr_cfg,
        meas_off["s1"][f"lag{SECONDARY_LAG}"]["z"], meas_off["s2"][f"lag{SECONDARY_LAG}"]["z"])
    for pc in rga["per_check"]:
        print(f"    check {pc['check']}: p_ij(1)={pc['pij_lag1']:.5f} mu_implied={pc['rate_implied_mu']:.5f}"
              f" (cfg {pc['p_instr_cfg']:.5f}) identity z={pc['z_identity']:.2f} -> "
              f"{'ok' if pc['identity_holds'] else 'FAIL'}", flush=True)
    print(f"    lag>=2 consistent 0: {rga['lag2_consistent_zero']} -> "
          f"{'PASS' if rga['pass'] else 'FAIL'}", flush=True)

    # --- R-G6-B: MA(1) 1-dependence via S2 (off lag1 nonzero, lag2 zero). ---
    off_s2_lag1_z = meas_off["s2"]["lag1"]["z"]
    off_s2_lag2_z = meas_off["s2"][f"lag{SECONDARY_LAG}"]["z"]
    rgb_pass = bool(abs(off_s2_lag1_z) >= Z_STRUCTURE and abs(off_s2_lag2_z) < Z_STRUCTURE)
    print(f"\n[R-G6-B] MA(1) 1-dependence: off S2@1 z={off_s2_lag1_z:.2f} (>=3) & "
          f"S2@2 z={off_s2_lag2_z:.2f} (<3) -> {'PASS' if rgb_pass else 'FAIL'}", flush=True)

    # --- R-G6-C (conditional): common-mode equality shared ~ markovian at lag2. ---
    shared_s2_lag2_z = meas_shared["s2"][f"lag{SECONDARY_LAG}"]["z"]
    diff_lag2 = difference_z_shared_minus_markov("s2", SECONDARY_LAG, cubes["shared"],
                                                 cubes["markovian"], spt, spt)
    common_mode_detected = bool(abs(shared_s2_lag2_z) >= Z_STRUCTURE)
    if common_mode_detected:
        rgc_pass = bool(abs(diff_lag2["z"]) < Z_STRUCTURE)
        rgc_class = "GENUINE (common-mode detected in shared; markovian must reproduce it)"
    else:
        rgc_pass = True  # vacuous-power: not counted against PASS, reported.
        rgc_class = "VACUOUS-power (common-mode sub-detected at this N; reported, not gated)"
    print(f"\n[R-G6-C] common-mode equality: shared S2@2 z={shared_s2_lag2_z:.2f} "
          f"(detected={common_mode_detected}); shared-markov diff z={diff_lag2['z']:.2f} -> "
          f"{'PASS' if rgc_pass else 'FAIL'} [{rgc_class}]", flush=True)

    # --- R-G6-D (REPORTED): memory difference + derived N. ---
    diff_lag2_memory = diff_lag2  # the shared-markov lag2 difference IS the memory residue proxy
    print(f"\n[R-G6-D REPORTED] shared-markov memory difference (S2@2) z={diff_lag2_memory['z']:.2f}"
          f" (expected <3: sub-floor); derived N_detect >= {DERIVED_N_DETECT['optimistic_pooled_min']:.1e}"
          f" (optimistic) .. {DERIVED_N_DETECT['conservative_min']:.1e} (conservative) >> {FEASIBLE_N}",
          flush=True)

    # --- C1 positive control from truth. ---
    print("\n[C1] R1 positive control (params vary per round + cross-mech corr >= 0.9)", flush=True)
    c1 = c1_positive_control(teacher, regime, m=m, seed=seed_shared, n_inspect=C1_MAX_INSPECT)
    print(f"  frac gamma spread={c1['frac_gamma_spread']:.3f}; corr(zeta,gamma)="
          f"{c1['cross_mech_corr_zeta_gamma']:.4f} -> {'PASS' if c1['pass'] else 'FAIL'}", flush=True)

    # --- C5 zeta-witness r3 ~ 0 in ALL three arms. ---
    def r3_ok(meas):
        return meas["s3"]["degenerate_obs_constant"] or abs(meas["s3"]["z"]) < Z_STRUCTURE
    c5 = bool(r3_ok(meas_shared) and r3_ok(meas_markov) and r3_ok(meas_off))
    print(f"\n[C5] zeta-witness r3 ~ 0 all arms -> {'PASS' if c5 else 'FAIL'}", flush=True)

    # --- P1 / P2 / P3 pipeline self-falsification. ---
    print("\n[P1/P2/P3] pipeline self-falsification", flush=True)
    p1 = p1_pipeline_null_fixed(cubes["shared"], cubes["off"], spt)
    p2 = p2_pipeline_common_mode(cubes["shared"], spt)
    p3 = p3_pipeline_planted_memory(n_shots, n_delta, n_stab, spt)
    print(f"  P1 null: p_ij(1)={p1['synth_p_ij_lag1']:.5f} (floor {p1['ma1_floor_mu']:.5f}, "
          f"match={p1['lag1_matches_ma1_floor']}) lag2 z={p1['s2_lag2_z']:.2f} "
          f"-> {'PASS' if p1['pass'] else 'FAIL'}", flush=True)
    print(f"  P2 common-mode: s1_z={p2['s1_lag1_z']:.2f} s2@2_z={p2['s2_lag2_z']:.2f} detected(>=5)="
          f"{p2['detected_as_required']} -> {'PASS' if p2['pass'] else 'FAIL'}", flush=True)
    print(f"  P3 planted-memory: diff_z={p3['difference_z']:.2f} detected(>=5)="
          f"{p3['detected_as_required']} -> {'PASS' if p3['pass'] else 'FAIL'}", flush=True)

    conditions = {
        "R_G6_A_off_ma1_closed_form": bool(rga["pass"]),
        "R_G6_B_ma1_one_dependence": bool(rgb_pass),
        "R_G6_C_common_mode_equality": bool(rgc_pass),
        "C1_params_vary_and_cross_corr": bool(c1["pass"]),
        "C5_zeta_witness_r3_zero": bool(c5),
        "P1_pipeline_null_ma1_floor": bool(p1["pass"]),
        "P2_common_mode_detected": bool(p2["pass"]),
        "P3_planted_memory_detected": bool(p3["pass"]),
        "independent_gt_lag1_pij": bool(gt["pass"]),
    }
    verdict = "PASS" if all(conditions.values()) else "FAIL"

    check_class = {
        "R_G6_A_off_ma1_closed_form": "GENUINE (a-exact MA(1) identity p_ij(lag1)=(1-sqrt(1-2<D>))/2; "
                                      "a wiring bug / non-i.i.d. off rounds breaks it)",
        "R_G6_B_ma1_one_dependence": "GENUINE (off S2 nonzero at lag1, exactly 0 at lag>=2 — the "
                                     "moving-average signature)",
        "R_G6_C_common_mode_equality": rgc_class,
        "C1_params_vary_and_cross_corr": "GENUINE (reads evaluator truth; a dead round_index -> "
                                         "uniform params drops frac_spread below 0.9 — red-team R1)",
        "C5_zeta_witness_r3_zero": "GENUINE (a per-round instrument leak or a live-zeta bug moves r3; "
                                   "degenerate-obs flagged)",
        "P1_pipeline_null_ma1_floor": "GENUINE (i.i.d. MEASURED bits reproduce the MA(1) floor with no "
                                      "manufactured lag>=2 correlation — the CORRECT null, F1-fixed)",
        "P2_common_mode_detected": "GENUINE (a planted common-mode latent must be detected; common-mode "
                                   "sensitivity control — NOT memory discrimination)",
        "P3_planted_memory_detected": "GENUINE (an inflated AR(1) memory must be caught by the "
                                      "shared-minus-permuted difference statistic)",
        "independent_gt_lag1_pij": "GENUINE (two hand-written formula routes on identical bits; §8.2 L6)",
        "R_G6_D_memory_subfloor": "REPORTED, never gates (the honest sub-detectability finding; the "
                                  "memory lives at the channel level (G2) + in truth, sub-floor on records)",
        "S1_spitz_p_ij": "GENUINE (ledgered exact Eq.13; validity domain enforced)",
        "S2_count_autocov": "GENUINE (per-(r,lag) shot covariance; off lag>=2 exactly 0 under MA(1))",
        "S3_r3": "GENUINE unless degenerate_obs_constant (then VACUOUS-degenerate, r3:=0 flagged)",
    }

    evidence = {
        "gate": GATE,
        "verdict": verdict,
        "prereg": "docs/twin_validation/coupled_teacher_round_gates_prereg.md#5 (revised 2026-07-03, G6-A1)",
        "derivation": "docs/twin_validation/g6_null_model_rederivation_2026-07-03.md",
        "metric": "cross-cycle Spitz p_ij (METRICS.md DEM-edge Eq.13, EXACT) + count autocovariance",
        "config": {"path": cfg.get("_config_path"), "sha256": cfg.get("_config_sha256"),
                   "fixture": cfg["fixture"], "R_star": cfg["R_star"], "N_run": n_run,
                   "shots_per_trajectory": spt, "n_lags": n_lags, "seeds": seeds,
                   "committed_p_instr_mu": p_instr_cfg},
        "fixture_consistency": fixture_consistency,
        "detector_column_map": colmap,
        "arms": {"shared": meas_shared, "markovian": meas_markov, "off": meas_off},
        "conditions": conditions,
        "R_G6_A_off_ma1": rga,
        "R_G6_B_one_dependence": {"off_s2_lag1_z": off_s2_lag1_z, "off_s2_lag2_z": off_s2_lag2_z,
                                  "pass": rgb_pass},
        "R_G6_C_common_mode_equality": {"shared_s2_lag2_z": shared_s2_lag2_z,
                                        "common_mode_detected": common_mode_detected,
                                        "difference": diff_lag2, "pass": rgc_pass, "class": rgc_class,
                                        "derived_common_mode_per_check": DERIVED_COMMON_MODE},
        "R_G6_D_memory_subfloor_REPORTED": {"difference_S2_lag2": diff_lag2_memory,
                                            "derived_N_detect": DERIVED_N_DETECT,
                                            "expectation": "|z|<3 at N<=1e6 (faithful sub-floor); a "
                                                           "surprise |z|>=3 is a FINDING not a fail"},
        "C1_detail": c1,
        "C5_zeta_witness": {"shared": meas_shared["s3"], "markovian": meas_markov["s3"],
                            "off": meas_off["s3"], "pass": c5},
        "independent_gt_lag1_pij": gt,
        "P1_pipeline_null": p1,
        "P2_common_mode": p2,
        "P3_planted_memory": p3,
        "epistemic_classes": {"R_G6_A_B": "a (exact) reported+gated", "R_G6_C": "b (conditional gate)",
                              "R_G6_D": "b REPORTED never gates", "C1_C5": "c gate on b expectation",
                              "P1_P2_P3": "c pipeline self-test", "independent_gt": "a algebraic identity"},
        "check_class": check_class,
    }
    out_path, h = write_evidence(GATE, evidence, "g6_ablation.json")

    print("\n=== G6 CONDITIONS (faithfulness report) ===", flush=True)
    for k, v in conditions.items():
        print(f"   {k:<34}: {'PASS' if v else 'FAIL'}", flush=True)
    emit_gate_result(GATE, verdict, h, out_path)
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
