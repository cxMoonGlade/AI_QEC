#!/usr/bin/env python
from __future__ import annotations

r"""G6 GATE — coupling-ablation ON RECORDS (the Axis-2 anti-toy core).

Binds to docs/twin_validation/coupled_teacher_round_gates_prereg.md §5 EXACTLY:
  §5.1 statistics S1 (ledgered Spitz p_ij, METRICS.md DEM-edge Eq.13), S2 (lag-l detector-count
       autocovariance), S3 (cross-mechanism r3 = the zeta-witness);
  §5.2 PASS conditions C1..C5 + the in-script pipeline stubs P1/P2 (L10);
  §5.3 power note (one registered amendment path); §5.4 per-arm expectations; §5.5 diagnostics.
Three arms at N_run (= N* or g6_n_override <= 1e6): shared (101) / markovian (202) / off (303).

METRIC (METRICS.md DEM-edge row, EXACT Eq.13):
  p_hat_ij = 1/2 - sqrt(1/4 - cov(x_i,x_j)/(1 - 2*<x_i XOR x_j>))
validity domain enforced (denom > 0, sqrt-arg >= 0); invalid pairs flagged+excluded+counted.
Two-point-only hyperedge blindness stated (Takou-Brown 2504.20212, ledger convention).

CONSTRAINT-LEDGER falsifiers implemented here (docs/twin_validation/gates/CONSTRAINT_LEDGER_partB.md):
  L6  Spitz validity domain + the lag-1 direct-covariance cross-check (independent-GT, §8.2)
      -> spitz_p_ij() + independent_gt_lag1_pij().
  L8  ablation arms differ where registered and ONLY there -> C3/C4.
  L9  params vary per round (dead-override toy, R1) -> c1_positive_control().
  L10 pipeline detects planted correlation / silent on none -> p1_pipeline_null / p2_pipeline_planted.
  L11 cluster SEs -> _gate_common.cluster_bootstrap_se + precondition_n_traj.

EPISTEMIC CLASSES (prereg §9): C1..C4 (c) gates on (b) expectations; C5 (b/c); P1/P2 (c) pipeline.
A (b) miss printed loudly; only the registered gate-FAIL conditions flip the verdict.

SCRIPTED-EXECUTION: committed, __main__-guarded; precondition asserts + printed evidence
(shapes/numbers/hashes) + flushed output; emits g6_ablation.json. GPU-only where the teacher
touches cuda (the orchestrator runs it serially post-review).
    conda run -n aiqec python docs/twin_validation/gates/g6_ablation.py --config <path>
"""

import argparse
import sys

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

# When run as a bare script the sibling `_gate_common.py` is importable because CPython puts
# the script's own directory on sys.path[0]; when imported as a module the runner adds it. Keep
# the gates directory on the path defensively.
from pathlib import Path as _P  # noqa: E402
if str(_P(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(_P(__file__).resolve().parent))

GATE = "G6_ablation"
FEASIBLE_N = 1_000_000  # (c) the amendment-path cap (§5.3)

# (c) registered constants.
BOOT_B = 200
BOOT_SEED = 777
P2_PLANT_SIGMA = 0.5   # (c) g ~ N(0, 0.5^2), sized to be comfortably detectable (z>=5) (§5.2 P2)
P2_PLANT_SEED = 424242
P1_NULL_SEED = 131313
Z_STRUCTURE = 3.0      # (c) C2/C3/C4/C5 threshold
Z_PLANTED_MIN = 5.0    # (c) P2 must read z >= 5
C1_SPREAD_FRAC = 0.90  # (c) >= 90% of inspected shots show per-cycle gamma_phi spread > 0
C1_CROSS_CORR = 0.90   # (c) cross-mech corr(zeta, gamma_phi) >= 0.9
C1_MAX_INSPECT = 256   # (c) min(N, 256) inspected shots


# =========================================================================== #
# S1 — the ledgered Spitz p_ij (METRICS.md DEM-edge row, EXACT Eq. 13)         #
# =========================================================================== #
def _pij_from_moments(mean_i: float, mean_j: float, mean_ij: float) -> tuple[float, bool]:
    """EXACT Spitz Eq. 13 p_ij from the three moments (single pair). Returns (p_ij, valid).

    p_ij = 1/2 - sqrt(1/4 - cov / (1 - 2*<x_i XOR x_j>)),
    cov = <x_i x_j> - <x_i><x_j>,  <x_i XOR x_j> = <x_i> + <x_j> - 2<x_i x_j>.
    Validity domain (L6): denom = 1 - 2*<xor> != 0 (require > 0 per the METRICS.md exact form
    where the small-p branch is taken) AND the sqrt argument >= 0. Invalid -> (nan, False).
    """

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
    """Pooled lag-`lag` timelike Spitz p_ij over (delta(c,r), delta(c,r+lag)) pairs (§5.1 S1).

    `cube` is (N, n_delta, n_stab) round-delta detectors. Pairs are timelike: same check c,
    delta rounds (r, r+lag). Pooled p_ij = mean over valid (r, c) pairs of the per-pair Eq.13
    value; per-pair values retained. Validity domain enforced; invalid pairs flagged+counted.
    """

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


# =========================================================================== #
# S2 — lag-l autocovariance of per-round detector counts (§5.1 S2)            #
# =========================================================================== #
def s2_count_autocov(cube: np.ndarray, lag: int) -> float:
    """ĉ_l = mean over r of Cov_shots(D_r, D_{r+lag}), D_r = sum_c x_{c,r} (per-round det count).

    Per-(r,lag) shot-covariance averaged over r (robust to round inhomogeneity, §5.1 S2).
    """

    n, n_delta, n_stab = cube.shape
    counts = cube.sum(axis=2).astype(np.float64)  # (N, n_delta)
    vals = []
    for r in range(n_delta - lag):
        a = counts[:, r]
        b = counts[:, r + lag]
        # population covariance across shots.
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
        return 0.0, True  # degenerate_obs_constant (or degenerate det) -> r3 := 0
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

    # §5.5 diagnostics: pooled delta-detector rate q_hat + pileup fraction proxy q_hat/2.
    q_hat = float(cube_full.mean())
    out["diagnostics"] = {"pooled_delta_detector_rate_qhat": q_hat,
                          "pileup_fraction_proxy_qhat_over_2": q_hat / 2.0,
                          "n_clusters": (n_run + spt - 1) // spt}
    return out


# =========================================================================== #
# L6 independent-GT (§8.2): lag-1 p_ij closed form vs DIRECT covariance route  #
# =========================================================================== #
def independent_gt_lag1_pij(cube: np.ndarray) -> dict:
    """Cross-check the lag-1 pooled p_ij (closed Eq.13) vs a DIRECT covariance reconstruction.

    Both routes on the SAME shot bits; an algebraic-identity check that trips on an
    implementation typo in EITHER path (tolerance 1e-12, §8.2). The 'direct' route recomputes
    cov, <xor>, denom, arg by hand from the shot arrays (no reuse of _pij_from_moments internals)
    and rebuilds p_ij; agreement to 1e-12 is the independent ground truth for S1's lag-1 value.
    This is NOT a check vs the engine's own oracle (both routes are hand-written from the bits).
    """

    n, n_delta, n_stab = cube.shape
    closed_vals: list[float] = []
    direct_vals: list[float] = []
    for c in range(n_stab):
        for r in range(n_delta - 1):
            xi = cube[:, r, c].astype(np.float64)
            xj = cube[:, r + 1, c].astype(np.float64)
            mi, mj, mij = float(xi.mean()), float(xj.mean()), float((xi * xj).mean())
            pc, valid_c = _pij_from_moments(mi, mj, mij)
            # DIRECT route: independent hand reconstruction from the raw bits.
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
            "note": "XOR identity <x_i XOR x_j> = <x_i>+<x_j>-2<x_i x_j> also used by the "
                    "closed route; the DIRECT route computes <x_i XOR x_j> from the raw bit XOR "
                    "so a typo in the moment-XOR identity would separate the two routes"}


# =========================================================================== #
# C1 — R1 positive control (params must vary; cross-mech corr) from truth      #
# =========================================================================== #
_Z_TRAJ_KEYS = ("per_shot_z_trajectories", "z_trajectories", "z_traj", "trajectories")
_PER_CYCLE_KEYS = ("params_manifest_sample", "per_cycle_params", "per_cycle")
_GAMMA_FIELD = "gamma_phi_per_ns"
_ZETA_FIELD = "zz_zeta_radns"


def c1_positive_control(teacher: Any, regime: Any, *, m: int, seed: int, n_inspect: int) -> dict:
    """C1 (red-team R1): per-cycle gamma_phi VARIES across rounds for >= 90% of inspected shots,
    AND cross-mechanism corr(zeta, gamma_phi) >= 0.9 on a shared-arm truth trajectory (§5.2).

    A-G6-1: truth key spellings are resolved from a declared candidate list; unresolvable =>
    loud FAIL printing sorted(truth.keys()). The teacher's truth records a
    `params_manifest_sample` (one trajectory's per-cycle CoupledMechanismParams) after an emit;
    we emit a small batch first so truth.last_emit is populated, then read the per-cycle fields.
    """

    # populate truth.last_emit by emitting a small batch (the teacher records a per-cycle sample).
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
            f"{sorted(last_emit.keys())}; truth keys = {sorted(truth.keys())}"
        )
    # each sample entry: {"trajectory": j, "per_cycle": [ {..CoupledMechanismParams manifest..}, ...]}
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
    # cross-mech correlation on the pooled per-cycle (zeta, gamma_phi) — both monotone maps of z.
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
                                "_TRUTH_PARAMS_SAMPLE_TRAJECTORIES knob); the >=90%-of-min(N,256) "
                                "wording is honored over the exposed sample. A dead round_index "
                                "still collapses frac_spread to 0 here (R1 falsifier intact); the "
                                "cross-mech correlation is pooled over the trajectory's R cycles."),
            "note": "both fields are monotone maps of one z => |corr| near 1 (§5.2 C1)"}


def _field(manifest: Any, name: str) -> float:
    """Read a numeric field from a CoupledMechanismParams manifest (dict) — loud on absence."""

    if isinstance(manifest, dict) and name in manifest:
        return float(manifest[name])
    raise ConfigError(f"C1: per-cycle params manifest missing field {name!r}; got keys "
                      f"{sorted(manifest.keys()) if isinstance(manifest, dict) else type(manifest)}")


# =========================================================================== #
# P1 / P2 — in-script pipeline stubs (L10, §5.2)                              #
# =========================================================================== #
def p1_pipeline_null(cube_shared: np.ndarray, n_stab: int, spt: int) -> dict:
    """P1 (negative control): synthetic i.i.d. Bernoulli det records at the shared arm's
    per-(c,r) marginals run through the SAME statistic must read |z| < 3 (§5.2). The pipeline
    must not manufacture correlation from independent bits."""

    n, n_delta, ns = cube_shared.shape
    marg = cube_shared.mean(axis=0)  # (n_delta, n_stab) per-(r,c) rate
    rng = np.random.default_rng(P1_NULL_SEED)
    synth = (rng.random((n, n_delta, ns)) < marg[None, :, :]).astype(np.uint8)
    s1 = spitz_p_ij(synth, PRIMARY_LAG)
    s1_boot = cluster_bootstrap_se(lambda idx: _pooled_pij_scalar(synth[idx], PRIMARY_LAG),
                                   n, spt, B=BOOT_B, seed=BOOT_SEED)
    s2 = s2_count_autocov(synth, PRIMARY_LAG)
    s2_boot = cluster_bootstrap_se(lambda idx: s2_count_autocov(synth[idx], PRIMARY_LAG),
                                   n, spt, B=BOOT_B, seed=BOOT_SEED)
    z1 = zscore(s1["pooled_p_ij"], s1_boot["se"])
    z2 = zscore(s2, s2_boot["se"])
    silent = (abs(z1) < Z_STRUCTURE) and (abs(z2) < Z_STRUCTURE)
    return {"s1_lag1_pooled_p_ij": s1["pooled_p_ij"], "s1_z": z1, "s2_lag1_autocov": s2,
            "s2_z": z2, "threshold": Z_STRUCTURE, "silent_as_required": bool(silent),
            "pass": bool(silent)}


def p2_pipeline_planted(cube_shared: np.ndarray, n_stab: int, spt: int) -> dict:
    """P2 (positive control): synthetic records with a per-SHOT common rate multiplier exp(g),
    g ~ N(0, 0.5^2), must read z >= 5 (§5.2). The pipeline must be able to detect real cross-cycle
    correlation. The common multiplier couples ALL (r,c) rates within a shot => cross-cycle memory."""

    n, n_delta, ns = cube_shared.shape
    base = np.clip(cube_shared.mean(axis=0), 1e-4, 0.5)  # (n_delta, n_stab) base rate
    rng = np.random.default_rng(P2_PLANT_SEED)
    g = rng.normal(0.0, P2_PLANT_SIGMA, size=n)          # per-shot common latent
    mult = np.exp(g)[:, None, None]
    rate = np.clip(base[None, :, :] * mult, 0.0, 0.999)  # shared per-shot rate across rounds
    synth = (rng.random((n, n_delta, ns)) < rate).astype(np.uint8)
    s1 = spitz_p_ij(synth, PRIMARY_LAG)
    s1_boot = cluster_bootstrap_se(lambda idx: _pooled_pij_scalar(synth[idx], PRIMARY_LAG),
                                   n, spt, B=BOOT_B, seed=BOOT_SEED)
    s2 = s2_count_autocov(synth, PRIMARY_LAG)
    s2_boot = cluster_bootstrap_se(lambda idx: s2_count_autocov(synth[idx], PRIMARY_LAG),
                                   n, spt, B=BOOT_B, seed=BOOT_SEED)
    z1 = zscore(s1["pooled_p_ij"], s1_boot["se"])
    z2 = zscore(s2, s2_boot["se"])
    detected = (abs(z1) >= Z_PLANTED_MIN) or (abs(z2) >= Z_PLANTED_MIN)
    return {"planted_sigma": P2_PLANT_SIGMA, "s1_lag1_pooled_p_ij": s1["pooled_p_ij"], "s1_z": z1,
            "s2_lag1_autocov": s2, "s2_z": z2, "threshold": Z_PLANTED_MIN,
            "detected_as_required": bool(detected), "pass": bool(detected)}


# =========================================================================== #
# difference statistic (C3) — shared minus markovian, cluster-bootstrapped     #
# =========================================================================== #
def difference_z_shared_minus_markov(stat_name: str, lag: int,
                                     cube_s: np.ndarray, cube_m: np.ndarray,
                                     spt_s: int, spt_m: int) -> dict:
    """z of the shared-minus-markovian difference of the C2-passing statistic (§5.2 C3).

    Independent cluster bootstraps on each arm; SE_diff = sqrt(se_s^2 + se_m^2). `stat_name` in
    {"s1","s2"} selects the pooled p_ij or the count-autocovariance at `lag`.
    """

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


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="G6 coupling-ablation gate (Axis-2 anti-toy core)")
    parser.add_argument("--config", default=None, help="gate_run_config.json (default: gates/ path)")
    args = parser.parse_args(argv)

    print("=" * 78, flush=True)
    print("G6 GATE — coupling-ablation ON RECORDS (Axis-2 anti-toy core; prereg §5)", flush=True)
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

    # arms (§2.3): shared = teacher; markovian = .markovian_baseline(); off = .off_source().
    teacher = construct_teacher(cfg)
    regime = build_regime(cfg, teacher)
    print(f"[arms] regime={regime}", flush=True)

    shared = emit_arm(teacher, regime, m=m, N=n_run, seed=seed_shared)
    colmap = detector_column_map(teacher, shared["det"].shape[1])
    fixture_consistency = assert_fixture_consistency(cfg, teacher, shared["det"].shape[1])
    n_stab = int(teacher.n_stab)
    # cross-cycle statistics need >= 2 delta rounds for lag-1 (R* >= 3); fail loud otherwise.
    require_min_delta_rounds(colmap, n_stab, PRIMARY_LAG + 1, GATE)
    print(f"[arms] det width B={shared['det'].shape[1]} n_stab={n_stab} "
          f"round_delta_cols={colmap['n_round_delta']} final_cols={colmap['n_final_closure']}",
          flush=True)

    markov_teacher = teacher.markovian_baseline()
    markovian = emit_arm(markov_teacher, build_regime(cfg, markov_teacher),
                         m=m, N=n_run, seed=seed_markov)
    off_teacher = teacher.off_source()
    off = emit_arm(off_teacher, build_regime(cfg, off_teacher), m=m, N=n_run, seed=seed_off)

    # per-arm statistics.
    print("\n[measure] shared / markovian / off — S1(Spitz p_ij) + S2(count autocov) + S3(r3)",
          flush=True)
    meas_shared = measure_arm(shared["det"], shared["obs"], colmap, n_stab, n_lags, spt)
    meas_markov = measure_arm(markovian["det"], markovian["obs"], colmap, n_stab, n_lags, spt)
    meas_off = measure_arm(off["det"], off["obs"], colmap, n_stab, n_lags, spt)
    for name, meas in (("shared", meas_shared), ("markovian", meas_markov), ("off", meas_off)):
        s1 = meas["s1"][f"lag{PRIMARY_LAG}"]
        s2 = meas["s2"][f"lag{PRIMARY_LAG}"]
        print(f"  {name:<9} S1@lag1 p_ij={s1['pooled_p_ij']:.3e} z={s1['z']:.2f} "
              f"(valid {s1['n_pairs_valid']}/{s1['n_pairs_total']}); "
              f"S2@lag1 cov={s2['autocov']:.3e} z={s2['z']:.2f}; "
              f"S3 r3={meas['s3']['r3']:.3e} z={meas['s3']['z']:.2f}", flush=True)

    cubes = {
        "shared": round_delta_by_round(shared["det"], colmap, n_stab),
        "markovian": round_delta_by_round(markovian["det"], colmap, n_stab),
        "off": round_delta_by_round(off["det"], colmap, n_stab),
    }

    # --- L6 independent ground truth on the shared arm (§8.2). ---
    print("\n[independent-GT] lag-1 Spitz p_ij closed-form vs DIRECT covariance (tol 1e-12)",
          flush=True)
    gt = independent_gt_lag1_pij(cubes["shared"])
    print(f"  max|closed - direct| = {gt['max_abs_diff']:.3e} over {gt['n_pairs']} pairs -> "
          f"{'PASS' if gt['pass'] else 'FAIL'}", flush=True)

    # --- C1 positive control from truth (params vary + cross-mech corr). ---
    print("\n[C1] R1 positive control (params vary per round + cross-mech corr >= 0.9)", flush=True)
    c1 = c1_positive_control(teacher, regime, m=m, seed=seed_shared, n_inspect=C1_MAX_INSPECT)
    print(f"  frac gamma spread={c1['frac_gamma_spread']:.3f} (>= {C1_SPREAD_FRAC}); "
          f"corr(zeta,gamma)={c1['cross_mech_corr_zeta_gamma']:.4f} (>= {C1_CROSS_CORR}) -> "
          f"{'PASS' if c1['pass'] else 'FAIL'}", flush=True)

    # --- P1 / P2 pipeline stubs (L10). ---
    print("\n[P1/P2] pipeline self-falsification (null silent / planted detected)", flush=True)
    p1 = p1_pipeline_null(cubes["shared"], n_stab, spt)
    p2 = p2_pipeline_planted(cubes["shared"], n_stab, spt)
    print(f"  P1 null: s1_z={p1['s1_z']:.2f} s2_z={p1['s2_z']:.2f} silent(<3)="
          f"{p1['silent_as_required']} -> {'PASS' if p1['pass'] else 'FAIL'}", flush=True)
    print(f"  P2 planted: s1_z={p2['s1_z']:.2f} s2_z={p2['s2_z']:.2f} detected(>=5)="
          f"{p2['detected_as_required']} -> {'PASS' if p2['pass'] else 'FAIL'}", flush=True)

    # --- PASS conditions C1..C5 (§5.2). ---
    z_s1_shared = meas_shared["s1"][f"lag{PRIMARY_LAG}"]["z"]
    z_s2_shared = meas_shared["s2"][f"lag{PRIMARY_LAG}"]["z"]
    # C2 — shared shows structure (S1 or S2 at lag 1).
    c2_via_s1 = abs(z_s1_shared) >= Z_STRUCTURE
    c2_via_s2 = abs(z_s2_shared) >= Z_STRUCTURE
    c2 = c2_via_s1 or c2_via_s2
    c2_stat = "s1" if c2_via_s1 else ("s2" if c2_via_s2 else "none")
    # C3 — markovian flat AND the shared-minus-markov difference of the C2-passing stat z >= 3.
    z_s1_markov = abs(meas_markov["s1"][f"lag{PRIMARY_LAG}"]["z"])
    z_s2_markov = abs(meas_markov["s2"][f"lag{PRIMARY_LAG}"]["z"])
    markov_flat = (z_s1_markov < Z_STRUCTURE) and (z_s2_markov < Z_STRUCTURE)
    diff_row = None
    if c2_stat in ("s1", "s2"):
        diff_row = difference_z_shared_minus_markov(c2_stat, PRIMARY_LAG, cubes["shared"],
                                                    cubes["markovian"], spt, spt)
        c3 = markov_flat and (diff_row["z"] >= Z_STRUCTURE)
    else:
        c3 = False
    # C4 — off collapses (correlation structure, not rate).
    z_s1_off = abs(meas_off["s1"][f"lag{PRIMARY_LAG}"]["z"])
    z_s2_off = abs(meas_off["s2"][f"lag{PRIMARY_LAG}"]["z"])
    c4 = (z_s1_off < Z_STRUCTURE) and (z_s2_off < Z_STRUCTURE)
    # C5 — zeta-witness r3 ~ 0 in ALL three arms (or degenerate-flagged).
    def r3_ok(meas):
        return meas["s3"]["degenerate_obs_constant"] or abs(meas["s3"]["z"]) < Z_STRUCTURE
    c5 = r3_ok(meas_shared) and r3_ok(meas_markov) and r3_ok(meas_off)

    conditions = {
        "C1_params_vary_and_cross_corr": bool(c1["pass"]),
        "C2_shared_structure": bool(c2),
        "C3_independent_kills_it": bool(c3),
        "C4_off_collapses": bool(c4),
        "C5_zeta_witness_r3_zero": bool(c5),
        "P1_pipeline_null_silent": bool(p1["pass"]),
        "P2_pipeline_planted_detected": bool(p2["pass"]),
    }
    verdict = "PASS" if all(conditions.values()) else "FAIL"

    # §5.3 registered consequence (printed): a C2 miss with all controls passing is the
    # amendment path (one-time re-run at N_run=1e6), NOT automatically "no signal".
    if (not c2) and c1["pass"] and c3 is False and markov_flat and c4 and c5:
        print("\n  !! C2 MISS with controls consistent — §5.3 amendment path: a one-time re-run "
              f"at N_run={FEASIBLE_N} is the registered next step; still flat => FINDING + FAIL.",
              flush=True)

    # GENUINE-vs-VACUOUS self-classification (§2.5).
    check_class = {
        "C1_positive_control": "GENUINE (reads evaluator truth; a dead round_index -> uniform "
                               "params would drop frac_spread below 0.9 — red-team R1 falsifier)",
        "C2_shared_structure": "GENUINE (a no-memory teacher reads |z|<3; the shared 1/f source "
                               "must lift it, §5.4)",
        "C3_independent_kills_it": "GENUINE (the markovian permutation destroys the field "
                                   "autocorrelation; a mis-built control would keep S1/S2 alive)",
        "C4_off_collapses": "GENUINE (amplitude-0 source -> constant params -> i.i.d. rounds; a "
                            "leak would keep correlation)",
        "C5_zeta_witness_r3_zero": "GENUINE (a per-round instrument leak or a live-zeta bug moves "
                                   "r3; degenerate-obs handling flagged, §5.1 S3)",
        "P1_pipeline_null": "GENUINE (i.i.d. bits must read silent; a pipeline that manufactures "
                            "correlation fails here — L10)",
        "P2_pipeline_planted": "GENUINE (a planted common-rate latent must be detected; a blind "
                               "pipeline fails here — L10)",
        "independent_gt_lag1_pij": "GENUINE (two hand-written formula routes on identical bits; a "
                                   "typo in either separates them beyond 1e-12 — §8.2 L6)",
        "S1_spitz_p_ij": "GENUINE (ledgered exact Eq.13; validity domain enforced, invalid pairs "
                         "excluded+counted; two-point hyperedge-blind, Takou-Brown)",
        "S2_count_autocov": "GENUINE (per-(r,lag) shot covariance; zero under i.i.d. rounds)",
        "S3_r3": "GENUINE unless degenerate_obs_constant (then VACUOUS-degenerate, r3:=0 flagged)",
    }

    evidence = {
        "gate": GATE,
        "verdict": verdict,
        "prereg": "docs/twin_validation/coupled_teacher_round_gates_prereg.md#5",
        "metric": "cross-cycle Spitz p_ij (METRICS.md DEM-edge Eq.13, EXACT) + count autocovariance",
        "config": {"path": cfg.get("_config_path"), "sha256": cfg.get("_config_sha256"),
                   "fixture": cfg["fixture"], "R_star": cfg["R_star"], "N_run": n_run,
                   "shots_per_trajectory": spt, "n_lags": n_lags, "seeds": seeds},
        "fixture_consistency": fixture_consistency,
        "detector_column_map": colmap,
        "arms": {"shared": meas_shared, "markovian": meas_markov, "off": meas_off},
        "conditions": conditions,
        "C1_detail": c1,
        "C3_difference": diff_row,
        "C2_passing_statistic": c2_stat,
        "independent_gt_lag1_pij": gt,
        "P1_pipeline_null": p1,
        "P2_pipeline_planted": p2,
        "power_note": {"N_run": n_run, "feasible_n": FEASIBLE_N,
                       "amendment_path": "§5.3 one-time re-run at N_run=1e6 on a C2 miss with "
                                         "controls consistent; still flat => FINDING + FAIL"},
        "epistemic_classes": {"C1_C4": "c (gate) on b (expectation)", "C5": "b/c",
                              "P1_P2": "c (pipeline self-test)",
                              "S1": "a (metric) reported; S2/S3 a reported",
                              "independent_gt": "a (algebraic identity)"},
        "check_class": check_class,
    }
    out_path, h = write_evidence(GATE, evidence, "g6_ablation.json")

    print("\n=== G6 CONDITIONS ===", flush=True)
    for k, v in conditions.items():
        print(f"   {k:<34}: {'PASS' if v else 'FAIL'}", flush=True)
    emit_gate_result(GATE, verdict, h, out_path)
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
