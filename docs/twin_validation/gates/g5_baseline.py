#!/usr/bin/env python
from __future__ import annotations

r"""G5 GATE — record-level comparator panel (reporting discipline; NO novelty bar).

Binds to docs/twin_validation/coupled_teacher_round_gates_prereg.md §4 EXACTLY. Records:
shared arm at N* (seed 101), on the round-delta detector stream.

Comparators:
  (a) best-converged Markov-k fit of the per-check delta-bit stream (empirical order-k transition
      probabilities, Laplace alpha=0.5 (c), 50/50 TRAJECTORY split, held-out per-bit NLL in nats
      over interior rounds r > k; k = 0..6). Convergence k* = smallest k with
      ΔNLL(k*->k*+1) < 3*SE(ΔNLL) (paired trajectory bootstrap); none by k=6 => REJECTED => FAIL
      (P-G5-1).
  (b) finite-memory k=0 null (per-round marginal-matched independent bits — reporting-only).
  (c) matched-record surrogate = the markovian_baseline arm records (seed 202) — no tractable
      likelihood; statistic deltas only.
Reported per comparator: held-out NLL ((a),(b)); Spitz p_ij + count-autocovariance at lags 1..4
on comparator records minus the shared-arm values, each with cluster-bootstrap SE + (a/b/c) class.
P-G5-2 (b): converged k* <= 4 (a miss is a FINDING). P-G5-3 (a): NLL(k*) <= NLL(0) + 3*SE.
Printed caveats: "NLL/chi2-in-band != parameter accuracy"; pileup fraction (q_hat/2).

Verdict: PASS <=> (a) converged AND all three comparators declared + reported with classes.
Small/zero deltas are FINDINGS, not failures.

METRIC: held-out per-shot/per-bit NLL (METRICS.md "Held-out syndrome NLL" row, nats).

SCRIPTED-EXECUTION: committed, __main__-guarded; preconditions + printed evidence + flush;
emits g5_baseline.json. GPU-only where the teacher touches cuda.
    conda run -n aiqec python docs/twin_validation/gates/g5_baseline.py --config <path>
"""

import argparse
import math
import sys
from pathlib import Path

import numpy as np

from _gate_common import (  # noqa: E402
    PRIMARY_LAG,
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

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

# g6 statistics reused verbatim (single source of the ledgered Spitz p_ij + autocov).
from g6_ablation import s2_count_autocov, spitz_p_ij  # noqa: E402

GATE = "G5_baseline"
BOOT_B = 200
BOOT_SEED = 777
LAPLACE_ALPHA = 0.5   # (c) Markov-k Laplace smoothing
K_MAX = 6             # (c) Markov order grid 0..6
K_STAR_BAND = 4       # (b) P-G5-2 converged k* <= 4
SPLIT_SEED = 909090   # (c) 50/50 trajectory split seed
NLL_CONV_Z = 3.0      # (c) P-G5-1 convergence: dNLL < 3*SE
EPS = 1e-12           # NUMERICAL_ZERO floor for log-prob


# =========================================================================== #
# Markov-k fit of the per-check delta-bit stream (comparator (a))              #
# =========================================================================== #
def _split_trajectories(n_traj: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Deterministic 50/50 trajectory-level split (train/test cluster indices)."""

    rng = np.random.default_rng(int(seed))
    perm = rng.permutation(int(n_traj))
    half = int(n_traj) // 2
    return np.sort(perm[:half]), np.sort(perm[half:])


def _bits_for_clusters(cube: np.ndarray, clusters: list[np.ndarray], picked: np.ndarray) -> np.ndarray:
    """Concatenate the shot rows of the picked trajectory clusters -> (n_shots, n_delta, n_stab)."""

    idx = np.concatenate([clusters[c] for c in picked]) if len(picked) else np.array([], dtype=int)
    return cube[idx]


def markov_k_heldout_nll(cube: np.ndarray, clusters: list[np.ndarray], k: int,
                         train: np.ndarray, test: np.ndarray) -> float:
    """Held-out per-bit NLL (nats) of an order-k Markov fit of each check's delta-bit stream.

    For each check c, model P(x_{c,r} | x_{c,r-1..r-k}) with empirical order-k transition
    probabilities (Laplace alpha=0.5), fitted on TRAIN trajectories, scored on TEST over interior
    rounds r > k. Averaged over (test shots, checks, interior rounds). k=0 is the marginal per-check
    rate. The bit context is the tuple of the previous k bits (same check). This is a REPORTING
    comparator (no novelty bar), so a simple per-check chain is intentional.
    """

    n, n_delta, n_stab = cube.shape
    train_bits = _bits_for_clusters(cube, clusters, train)
    test_bits = _bits_for_clusters(cube, clusters, test)
    if train_bits.shape[0] == 0 or test_bits.shape[0] == 0:
        return float("nan")
    total_nll = 0.0
    total_terms = 0
    for c in range(n_stab):
        # fit: count (context -> next bit) on train (vectorized over train shots).
        counts: dict[tuple, np.ndarray] = {}
        for r in range(k, n_delta):
            if k == 0:
                key = ()
                nxt = train_bits[:, r, c].astype(int)
                arr = counts.setdefault(key, np.zeros(2, dtype=np.float64))
                arr[1] += float(nxt.sum())
                arr[0] += float((1 - nxt).sum())
            else:
                ctx = train_bits[:, r - k:r, c].astype(int)  # (shots, k)
                nxt = train_bits[:, r, c].astype(int)
                # pack context bits into an int key per shot.
                key_ints = (ctx * (1 << np.arange(k)[::-1])).sum(axis=1)
                for kk in np.unique(key_ints):
                    sel = key_ints == kk
                    arr = counts.setdefault((int(kk),), np.zeros(2, dtype=np.float64))
                    arr[1] += float(nxt[sel].sum())
                    arr[0] += float((1 - nxt[sel]).sum())
        # score on test.
        for r in range(k, n_delta):
            nxt = test_bits[:, r, c].astype(int)
            if k == 0:
                arr = counts.get((), np.zeros(2))
                p1 = (arr[1] + LAPLACE_ALPHA) / (arr.sum() + 2 * LAPLACE_ALPHA)
                p1 = min(max(p1, EPS), 1 - EPS)
                p = np.where(nxt == 1, p1, 1 - p1)
            else:
                ctx = test_bits[:, r - k:r, c].astype(int)
                key_ints = (ctx * (1 << np.arange(k)[::-1])).sum(axis=1)
                p = np.empty(nxt.shape[0], dtype=np.float64)
                for kk in np.unique(key_ints):
                    sel = key_ints == kk
                    arr = counts.get((int(kk),), np.zeros(2))
                    p1 = (arr[1] + LAPLACE_ALPHA) / (arr.sum() + 2 * LAPLACE_ALPHA)
                    p1 = min(max(p1, EPS), 1 - EPS)
                    p[sel] = np.where(nxt[sel] == 1, p1, 1 - p1)
            total_nll += float(-np.log(np.clip(p, EPS, 1.0)).sum())
            total_terms += int(nxt.shape[0])
    return total_nll / total_terms if total_terms else float("nan")


def markov_convergence(cube: np.ndarray, clusters: list[np.ndarray], spt: int) -> dict:
    """Fit k=0..K_MAX, find k* = smallest k with dNLL(k->k+1) < 3*SE(dNLL) (P-G5-1).

    SE(dNLL) via a paired trajectory bootstrap of the (NLL_k - NLL_{k+1}) difference on the SAME
    train/test split resampled at the cluster level. None converged by K_MAX => REJECTED => FAIL.
    """

    n_traj = len(clusters)
    train, test = _split_trajectories(n_traj, SPLIT_SEED)
    nll_by_k = {k: markov_k_heldout_nll(cube, clusters, k, train, test) for k in range(K_MAX + 1)}

    def paired_dnll(k):
        # bootstrap the (NLL_k - NLL_{k+1}) difference by resampling TEST clusters.
        rng = np.random.default_rng(BOOT_SEED + k)
        draws = []
        for _ in range(BOOT_B):
            pick = rng.integers(0, len(test), size=len(test))
            test_b = test[pick]
            a = markov_k_heldout_nll(cube, clusters, k, train, test_b)
            b = markov_k_heldout_nll(cube, clusters, k + 1, train, test_b)
            if np.isfinite(a) and np.isfinite(b):
                draws.append(a - b)
        if len(draws) < 2:
            return float("nan"), float("nan")
        return float(np.mean(draws)), float(np.std(draws, ddof=1))

    conv = []
    k_star = None
    for k in range(K_MAX):
        dnll = nll_by_k[k] - nll_by_k[k + 1]
        _, se = paired_dnll(k)
        converged = np.isfinite(se) and (dnll < NLL_CONV_Z * se)
        conv.append({"k": k, "dNLL_k_to_k1": float(dnll), "se_dNLL": float(se),
                     "converged": bool(converged)})
        if converged and k_star is None:
            k_star = k
    return {"nll_by_k": {str(k): nll_by_k[k] for k in nll_by_k}, "convergence_steps": conv,
            "k_star": k_star, "rejected": bool(k_star is None),
            "k_star_band": K_STAR_BAND, "k_star_in_band": bool(k_star is not None and k_star <= K_STAR_BAND)}


def _nll_kstar_se(cube: np.ndarray, clusters: list[np.ndarray], k_star: int) -> float:
    """SE of NLL(k*) via a TEST-cluster bootstrap on the fixed 50/50 split (P-G5-3)."""

    train, test = _split_trajectories(len(clusters), SPLIT_SEED)
    rng = np.random.default_rng(BOOT_SEED + 99)
    draws = []
    for _ in range(max(20, BOOT_B // 4)):
        pick = rng.integers(0, len(test), size=len(test))
        val = markov_k_heldout_nll(cube, clusters, int(k_star), train, test[pick])
        if np.isfinite(val):
            draws.append(val)
    return float(np.std(np.asarray(draws), ddof=1)) if len(draws) >= 2 else float("nan")


# =========================================================================== #
# statistic deltas per comparator (Spitz p_ij + count autocov, lags 1..n_lags) #
# =========================================================================== #
def statistic_deltas(cube_comp: np.ndarray, cube_shared: np.ndarray, n_lags: int, spt: int) -> dict:
    """Comparator-minus-shared deltas of Spitz p_ij + count autocovariance at lags 1..n_lags,
    each with a cluster-bootstrap SE + z (§4). Comparator sample n = shared N (seeded)."""

    out = {"s1_delta": {}, "s2_delta": {}}
    for lag in range(1, int(n_lags) + 1):
        p_comp = spitz_p_ij(cube_comp, lag)["pooled_p_ij"]
        p_shar = spitz_p_ij(cube_shared, lag)["pooled_p_ij"]
        boot_c = cluster_bootstrap_se(lambda idx, L=lag: spitz_p_ij(cube_comp[idx], L)["pooled_p_ij"],
                                      cube_comp.shape[0], spt, B=BOOT_B, seed=BOOT_SEED)
        d1 = p_comp - p_shar
        out["s1_delta"][f"lag{lag}"] = {"comparator_p_ij": p_comp, "shared_p_ij": p_shar,
                                        "delta": d1, "se": boot_c["se"], "z": zscore(d1, boot_c["se"])}
        c_comp = s2_count_autocov(cube_comp, lag)
        c_shar = s2_count_autocov(cube_shared, lag)
        boot_c2 = cluster_bootstrap_se(lambda idx, L=lag: s2_count_autocov(cube_comp[idx], L),
                                       cube_comp.shape[0], spt, B=BOOT_B, seed=BOOT_SEED)
        d2 = c_comp - c_shar
        out["s2_delta"][f"lag{lag}"] = {"comparator_autocov": c_comp, "shared_autocov": c_shar,
                                        "delta": d2, "se": boot_c2["se"], "z": zscore(d2, boot_c2["se"])}
    return out


def synth_k0_null(cube_shared: np.ndarray) -> np.ndarray:
    """Comparator (b): per-round marginal-matched independent bits (k=0 null; reporting-only)."""

    n, n_delta, n_stab = cube_shared.shape
    marg = cube_shared.mean(axis=0)
    rng = np.random.default_rng(SPLIT_SEED + 7)
    return (rng.random((n, n_delta, n_stab)) < marg[None, :, :]).astype(np.uint8)


# =========================================================================== #
# runner                                                                      #
# =========================================================================== #
def _preconditions(cfg: dict) -> dict:
    import torch

    assert torch.cuda.is_available(), "G5 teacher is GPU-only; cuda must be available"
    n_run = int(cfg["N_star"])
    spt = int(cfg.get("shots_per_trajectory", 1))
    n_traj = precondition_n_traj(n_run, spt)
    print(f"[precond] cuda={torch.cuda.is_available()} device={torch.cuda.get_device_name(0)}",
          flush=True)
    print(f"[precond] fixture={cfg['fixture']} R*={cfg['R_star']} N*={n_run} S={spt} n_traj={n_traj}",
          flush=True)
    return {"n_run": n_run, "shots_per_trajectory": spt}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="G5 record-level comparator panel")
    parser.add_argument("--config", default=None)
    args = parser.parse_args(argv)

    print("=" * 78, flush=True)
    print("G5 GATE — record-level comparator panel (reporting discipline; prereg §4)", flush=True)
    print("=" * 78, flush=True)

    cfg = load_gate_config(args.config)
    pre = _preconditions(cfg)
    n_run, spt = pre["n_run"], pre["shots_per_trajectory"]
    n_lags = int(cfg.get("n_lags", 4))
    m = int(cfg.get("m", 0))
    seeds = cfg.get("seeds", {})

    teacher = construct_teacher(cfg)
    regime = build_regime(cfg, teacher)
    shared = emit_arm(teacher, regime, m=m, N=n_run, seed=int(seeds.get("shared", 101)))
    B = shared["det"].shape[1]
    colmap = detector_column_map(teacher, B)
    n_stab = int(teacher.n_stab)
    # Markov-k over the delta-bit stream needs >= 2 interior delta rounds (R* >= 3).
    require_min_delta_rounds(colmap, n_stab, 2, GATE)
    cube_shared = round_delta_by_round(shared["det"], colmap, n_stab)
    from _gate_common import cluster_blocks
    clusters = cluster_blocks(n_run, spt)

    # comparator (a): Markov-k convergence.
    print("\n[comparator a] Markov-k held-out NLL (k=0..6), convergence k* (P-G5-1)", flush=True)
    markov = markov_convergence(cube_shared, clusters, spt)
    for step in markov["convergence_steps"]:
        print(f"  k={step['k']}->{step['k']+1}: dNLL={step['dNLL_k_to_k1']:.3e} "
              f"se={step['se_dNLL']:.3e} converged={step['converged']}", flush=True)
    print(f"  k*={markov['k_star']} rejected={markov['rejected']} "
          f"(P-G5-2 k*<=4 in_band={markov['k_star_in_band']})", flush=True)
    # P-G5-3 sanity: NLL(k*) <= NLL(0) + 3*SE. SE of NLL(k*) by resampling the TEST trajectory
    # clusters (the same mechanism paired_dnll uses inside markov_convergence).
    nll0 = markov["nll_by_k"]["0"]
    nll_kstar = markov["nll_by_k"][str(markov["k_star"])] if markov["k_star"] is not None else float("nan")
    se_nll = _nll_kstar_se(cube_shared, clusters, markov["k_star"]) if markov["k_star"] is not None \
        else float("nan")
    p_g5_3_ok = bool(np.isfinite(nll_kstar) and np.isfinite(nll0)
                     and nll_kstar <= nll0 + (3.0 * se_nll if np.isfinite(se_nll) else 0.0))
    print(f"  [P-G5-3] NLL(k*)={nll_kstar:.4e} <= NLL(0)={nll0:.4e} + 3SE({se_nll:.2e}) -> "
          f"{'PASS' if p_g5_3_ok else 'FAIL'}", flush=True)

    # comparator (b): k=0 null; comparator (c): markovian_baseline surrogate.
    print("\n[comparator b] k=0 null (marginal-matched i.i.d.) — reporting-only", flush=True)
    cube_k0 = synth_k0_null(cube_shared)
    deltas_k0 = statistic_deltas(cube_k0, cube_shared, n_lags, spt)

    print("[comparator c] matched-record surrogate = markovian_baseline arm (statistic deltas only)",
          flush=True)
    markov_teacher = teacher.markovian_baseline()
    surrogate = emit_arm(markov_teacher, build_regime(cfg, markov_teacher),
                         m=m, N=n_run, seed=int(seeds.get("markovian", 202)))
    cube_surr = round_delta_by_round(surrogate["det"], colmap, n_stab)
    deltas_surr = statistic_deltas(cube_surr, cube_shared, n_lags, spt)

    for name, dd in (("k0_null", deltas_k0), ("markov_surrogate", deltas_surr)):
        s1 = dd["s1_delta"][f"lag{PRIMARY_LAG}"]
        print(f"  {name:<16} S1@lag1 delta={s1['delta']:.3e} z={s1['z']:.2f}", flush=True)

    q_hat = float(cube_shared.mean())
    print(f"\n[caveats] 'NLL/chi2-in-band != parameter accuracy'; pileup fraction q_hat/2="
          f"{q_hat/2.0:.3e}", flush=True)

    # verdict: PASS <=> (a) converged AND all three comparators reported.
    comparator_a_ok = not markov["rejected"]
    verdict = "PASS" if (comparator_a_ok and p_g5_3_ok) else "FAIL"

    findings = []
    if markov["k_star"] is not None and not markov["k_star_in_band"]:
        findings.append(f"P-G5-2 FINDING: converged k*={markov['k_star']} > {K_STAR_BAND}")
    for fnd in findings:
        print(f"   !! {fnd}", flush=True)

    check_class = {
        "comparator_a_markov_k": "GENUINE (held-out NLL; REJECTED->FAIL if no convergence by k=6 "
                                 "— P-G5-1)",
        "P_G5_3_nll_sanity": "GENUINE (a k* fit worse than the k=0 null beyond noise fails)",
        "comparator_b_k0_null": "GENUINE-reported (marginal-matched i.i.d.; reporting-only, never a "
                                "novelty rival — small/zero deltas are FINDINGS)",
        "comparator_c_surrogate": "GENUINE-reported (markovian_baseline; statistic deltas only, no "
                                  "tractable likelihood)",
        "P_G5_2_kstar_band": "GENUINE as a (b) bet (a miss is a FINDING, not pass/fail)",
    }

    evidence = {
        "gate": GATE,
        "verdict": verdict,
        "prereg": "docs/twin_validation/coupled_teacher_round_gates_prereg.md#4",
        "metric": "held-out per-bit NLL (METRICS.md Held-out syndrome NLL, nats)",
        "config": {"path": cfg.get("_config_path"), "sha256": cfg.get("_config_sha256"),
                   "fixture": cfg["fixture"], "R_star": cfg["R_star"], "N_star": n_run,
                   "shots_per_trajectory": spt, "n_lags": n_lags, "seeds": seeds},
        "comparator_a_markov_k": markov,
        "P_G5_3": {"nll_k0": nll0, "nll_kstar": nll_kstar, "se_nll_kstar": se_nll, "pass": p_g5_3_ok},
        "comparator_b_k0_null_deltas": deltas_k0,
        "comparator_c_surrogate_deltas": deltas_surr,
        "diagnostics": {"pileup_fraction_proxy_qhat_over_2": q_hat / 2.0,
                        "caveat": "NLL/chi2-in-band != parameter accuracy"},
        "predictions": {"P_G5_1": {"class": "c", "gate": "Markov-k converges by k=6 else FAIL"},
                        "P_G5_2": {"class": "b", "handling": "k*<=4 else FINDING"},
                        "P_G5_3": {"class": "a", "gate": "NLL(k*) <= NLL(0) + 3SE"}},
        "findings": findings,
        "check_class": check_class,
    }
    out_path, h = write_evidence(GATE, evidence, "g5_baseline.json")
    emit_gate_result(GATE, verdict, h, out_path)
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
