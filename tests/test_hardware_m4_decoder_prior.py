"""M4 decoder-prior utility — registered test artifact (S11).

PRE-REGISTRATION: docs/metric_results.md "M4 PRE-REGISTRATION (decoder-prior
utility; recorded 2026-06-10 BEFORE build/run)" S1-S12; reviewer blueprint
docs/.reports/m4_panel/R_reviewer_verdict.md; guards G1-G9 in M4C_adversarial.md.
Build split B3 (this file + qec_twin/hardware/m4_report.py): order-freeze state
machine (S12/G2), S3 pilot rung selection + Lambda-hat ladder, S7 band tables as
data + scoring, S8 statistics (paired shot bootstrap / exact McNemar / G5 partial
Spearman with dual nulls / G7 drift / baseline-only floor check), P10 GPU MC
forecasting, frozen-cache covariates and Tier-0 bands.

Synthetic-data tests need NO hardware data and no B1/B2 modules (dem_compose /
m4_decode are imported lazily by the stage runner only). Hardware-gated tests
skip without QEC_TWIN_HW_DATA / the frozen M3 fit cache and touch sample_00
artifacts ONLY (samples 01-99 are off-limits in every build/debug step). The
P10 sampler tests require CUDA (project rule: model compute never on CPU) and
skip where unavailable.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path

import numpy as np
import pytest
import torch

from qec_twin.hardware import m4_report
from qec_twin.hardware.dataset import resolve_rep29_root
from qec_twin.hardware.m3_report import FitRecord, _cache_key
from qec_twin.hardware.m4_report import (
    M4State,
    OrderFreezeError,
    c_of_s,
    covariation_test,
    eps_inversion,
    floor_check,
    frozen_covariates,
    gate_band_for_rung,
    heldout_samples,
    lambda_ladder,
    mcnemar_exact,
    paired_shot_bootstrap,
    partial_spearman,
    pilot_assert_arms,
    protocol_tuple,
    select_rung,
    spearman,
    tier0_bands,
)

FIT_CACHE = os.environ.get("QEC_TWIN_M3_FIT_CACHE", "outputs/m3_fit_cache.pt")

# ---------------------------------------------------------------- registered constants


def test_registered_design_constants():
    """S1/S3/S7/S8 registration constants are pinned verbatim (ratified R2/R3)."""
    assert m4_report.M4_SEED == 20260610
    assert m4_report.BOOT_REPLICATES == 1000
    assert m4_report.PERM_REPLICATES == 10_000
    assert m4_report.RUNG_TARGET == 0.075
    assert m4_report.RUNG_WINDOW == (0.01, 0.30)
    assert m4_report.RUNG_GRID == (5, 7, 9, 11, 13, 15, 17, 19, 21)
    assert m4_report.EPS_ABSTAIN_P == 0.45
    assert m4_report.TRAIN_SAMPLE == 0
    assert m4_report.PILOT_SAMPLES == (0,)
    assert m4_report.HELDOUT_PRIMARY_SAMPLES == (5, 6, 7, 8, 9)
    assert m4_report.DRIFT_CONTEXT_SAMPLES == (1, 2, 3, 4)
    assert m4_report.EXTENSION_SAMPLES == (10, 11, 12, 13, 14)
    assert m4_report.ESCROW_SAMPLES == (15, 16, 17, 18, 19)
    assert m4_report.PILOT_ARMS == ("naive", "pij")
    assert len(m4_report.CLEAN_WINDOWS) == 19
    assert 15 not in m4_report.CLEAN_WINDOWS and 19 not in m4_report.CLEAN_WINDOWS
    assert m4_report.SPEARMAN_RHO_MIN == 0.4
    assert m4_report.SPEARMAN_ALPHA == 0.01
    # S2 maximal disjoint partitions
    assert m4_report.DISJOINT_POSITIONS == {5: 5, 7: 4, 9: 3, 11: 2, 13: 2, 15: 1, 17: 1, 19: 1, 21: 1}


def test_heldout_sample_sets():
    assert heldout_samples(False) == (5, 6, 7, 8, 9)
    assert heldout_samples(True) == (5, 6, 7, 8, 9, 10, 11, 12, 13, 14)


def test_gate_band_table_lookup():
    assert gate_band_for_rung("X", 7) == {"lo": 2.0, "hi": 30.0, "central": 10.0}
    assert gate_band_for_rung("Z", 5) == {"lo": 1.0, "hi": 25.0, "central": 8.0}
    assert gate_band_for_rung("X", 13) == {"lo": 5.0, "hi": 35.0, "central": 15.0}
    assert gate_band_for_rung("Z", 21) == {"lo": 10.0, "hi": 45.0, "central": 25.0}
    with pytest.raises(ValueError):
        gate_band_for_rung("X", 6)  # off the registered grid
    with pytest.raises(ValueError):
        gate_band_for_rung("Y", 7)


# ---------------------------------------------------------------- c(s) + eps inversion (a)


def test_c_of_s_identity_values():
    """c(2) = 0.31, c(4) = 0.075 to 2 sf (M4-C 0b, exact identity)."""
    assert f"{c_of_s(2.0):.2g}" == "0.31"
    assert f"{c_of_s(4.0):.2g}" == "0.075"
    assert c_of_s(0.0) == 1.0  # exact limit
    grid = np.linspace(0.0, 8.0, 200)
    values = [c_of_s(s) for s in grid]
    assert all(a >= b for a, b in zip(values, values[1:]))  # monotone compression
    with pytest.raises(ValueError):
        c_of_s(-1.0)


def test_eps_inversion_roundtrip_and_abstain():
    eps = 2.0e-4
    p = 0.5 * (1.0 - (1.0 - 2.0 * eps) ** 1000)
    inv = eps_inversion(p, rounds=1000)
    assert not inv["abstain"]
    assert inv["eps"] == pytest.approx(eps, rel=1e-9)
    # registered abstain at p_hat > 0.45 (c)
    high = eps_inversion(0.4501)
    assert high["abstain"] and "0.45" in high["abstain_reason"]
    assert math.isnan(high["eps"])
    # M4-F10 abstain at (1 - 2p) <= 0 (reached only via the p > 0.45 branch first)
    assert eps_inversion(0.5)["abstain"]


def test_protocol_tuple_tags():
    """G1: every %dLER carries (d', T, p_hat, c(s_hat))."""
    tup = protocol_tuple(7, 0.075)
    assert tup["d_prime"] == 7 and tup["T"] == 1000
    assert tup["p_hat"] == 0.075 and not tup["eps_abstain"]
    assert tup["s_hat"] == pytest.approx(2.0 * tup["eps_hat"] * 1000)
    assert 0.0 < tup["c_s_hat"] < 1.0
    assert not tup["unpowered_as_registered"]
    sat = protocol_tuple(5, 0.47)
    assert sat["eps_abstain"] and sat["unpowered_as_registered"]
    assert math.isnan(sat["c_s_hat"])


# ---------------------------------------------------------------- S3 rung selection


def test_select_rung_interior_argmin():
    ladder = {5: 0.40, 7: 0.18, 9: 0.06, 11: 0.02, 13: 0.004}
    out = select_rung(ladder)
    assert out["d_prime_star"] == 9  # |log10 0.06 - log10 0.075| is the smallest in-window
    assert out["flag"] is None
    assert out["target"] == 0.075 and out["window"] == [0.01, 0.30]


def test_select_rung_tie_breaks_to_smaller_d():
    out = select_rung({7: 0.05, 9: 0.05, 11: 0.29})
    assert out["d_prime_star"] == 7  # ties -> smaller d' (verbatim rule)


def test_select_rung_edge_branch_conditioning_limited():
    out = select_rung({5: 0.45, 7: 0.42, 9: 0.35})
    assert out["d_prime_star"] == 9  # smallest-L_bar rung
    assert out["flag"] == "conditioning-limited"


def test_select_rung_edge_branch_power_starved():
    out = select_rung({17: 0.004, 19: 0.0008, 21: 0.0001})
    assert out["d_prime_star"] == 17  # largest-L_bar rung
    assert out["flag"] == "power-starved"


def test_select_rung_window_skipped_completion():
    out = select_rung({5: 0.50, 7: 0.005})
    assert out["flag"] == "window-skipped"
    assert out["d_prime_star"] in (5, 7)
    with pytest.raises(ValueError):
        select_rung({5: 0.0})
    with pytest.raises(ValueError):
        select_rung({})


def test_lambda_ladder_known_ratio_and_abstain():
    """Lambda_hat = eps(d')/eps(d'+2) through the registered inversion."""
    eps = {17: 1.6e-4, 19: 4.0e-5, 21: 1.0e-5}  # exact Lambda = 4 ladder
    ladder = {d: 0.5 * (1.0 - (1.0 - 2.0 * e) ** 1000) for d, e in eps.items()}
    rows = lambda_ladder(ladder)
    assert len(rows) == 2
    for row in rows:
        assert not row["abstain"]
        assert row["lambda_hat"] == pytest.approx(4.0, rel=1e-6)
        assert row["stationarity_caveat"] is True
    # a saturated lower rung abstains and the abstain propagates to its pair
    ladder[15] = 0.49
    rows = lambda_ladder(ladder)
    pair_15_17 = next(r for r in rows if r["d_lo"] == 15)
    assert pair_15_17["abstain"] and math.isnan(pair_15_17["lambda_hat"])


def test_pilot_assert_arms_structural():
    pilot_assert_arms({"naive": object(), "pij": object()})
    with pytest.raises(OrderFreezeError):
        pilot_assert_arms({"naive": 1, "pij": 2, "twin": 3})
    with pytest.raises(OrderFreezeError):
        pilot_assert_arms({"naive": 1, "twin_static": 2})
    with pytest.raises(OrderFreezeError):
        pilot_assert_arms({"naive": 1})  # missing pij is not the registered pilot either


# ---------------------------------------------------------------- S8 statistics


def _paired_synthetic(n=40_000, units=3, base_p=0.10, keep=0.80, seed=1):
    rng = np.random.default_rng(seed)
    baseline = rng.random((n, units)) < base_p
    twin = baseline & (rng.random((n, units)) < keep)
    return twin.astype(np.uint8), baseline.astype(np.uint8)


def test_paired_bootstrap_recovers_known_effect_and_is_deterministic():
    twin, base = _paired_synthetic()
    res = paired_shot_bootstrap(twin, base)
    # constructed truth: twin removes 20% of baseline errors -> %dLER = +20
    assert res["pct_delta"] == pytest.approx(20.0, abs=2.0)
    assert res["pass_one_sided_99"] and res["q01"] > 0.0
    assert res["q01"] < res["pct_delta"] < res["q99"]
    assert res["seed"] == m4_report.M4_SEED and res["replicates"] == 1000
    res2 = paired_shot_bootstrap(twin, base)
    assert res == res2  # seed-deterministic, bit-identical
    with pytest.raises(ValueError):
        paired_shot_bootstrap(twin[:100], base[:200])


def test_paired_bootstrap_design_effect():
    rng = np.random.default_rng(7)
    col_b = (rng.random((20_000, 1)) < 0.2).astype(np.uint8)
    col_a = (col_b.astype(bool) & (rng.random((20_000, 1)) < 0.9)).astype(np.uint8)
    # 4 perfectly-correlated copies of one unit: Kish design effect = 4
    res = paired_shot_bootstrap(np.tile(col_a, 4), np.tile(col_b, 4))
    # exact value 79999/19999 ~ 4.0002 (ddof=1 on cells vs shots)
    assert res["design_effect"] == pytest.approx(4.0, abs=0.01)
    # independent units: design effect ~ 1
    twin, base = _paired_synthetic(seed=11)
    res_iid = paired_shot_bootstrap(twin, base)
    assert res_iid["design_effect"] == pytest.approx(1.0, abs=0.15)


def test_mcnemar_known_effect_counts_and_p():
    twin, base = _paired_synthetic()
    res = mcnemar_exact(twin, base)
    assert res["n01"] == 0  # twin errors are a subset of baseline errors by construction
    n10_expected = 0.10 * 0.20 * twin.size
    assert res["n10"] == pytest.approx(n10_expected, rel=0.1)
    assert res["p_one_sided"] < 1e-9
    assert not res["conditioning_limited"]
    # degenerate: no discordance
    same = np.zeros(100, dtype=np.uint8)
    res0 = mcnemar_exact(same, same)
    assert res0["p_one_sided"] == 1.0 and res0["n01"] == res0["n10"] == 0


def test_mcnemar_conditioning_limited_flag():
    rng = np.random.default_rng(3)
    a = (rng.random(200_000) < 0.05).astype(np.uint8)
    b = (rng.random(200_000) < 0.05).astype(np.uint8)  # independent => delta ~ its bound
    res = mcnemar_exact(a, b)
    assert res["conditioning_limited"]
    # strongly-paired arms sit far from the bound
    twin, base = _paired_synthetic()
    assert not mcnemar_exact(twin, base)["conditioning_limited"]


def test_partial_spearman_kills_pure_r_confound():
    """G5/M4-F5: an effect driven purely by r_hat must be killed by the partial.

    n = 200 here (the statistic is instrument-size-agnostic): with independent
    rank-shuffling noise on y and on R_hat the partial sits within ~0.07 of 0,
    while the unconditional Spearman stays near 1 through the shared r_hat."""
    rng = np.random.default_rng(5)
    n = 200
    r_hat = np.linspace(0.005, 0.020, n)
    y = 100.0 * r_hat + 0.05 * rng.standard_normal(n)  # effect purely via r_hat
    big_r = 1.0 + 50.0 * r_hat + 0.02 * rng.standard_normal(n)  # confounded covariate
    assert spearman(y, big_r) >= 0.8  # unconditional rank correlation is huge
    assert abs(partial_spearman(y, big_r, r_hat)) < 0.35  # the partial kills it
    out = covariation_test(y, big_r, r_hat, permutations=500)
    assert out["verdict"] == "null"
    assert not out["pass_perm"]
    assert out["rho_partial"] < m4_report.SPEARMAN_RHO_MIN


def test_partial_spearman_genuine_effect_survives():
    rng = np.random.default_rng(9)
    r_hat = np.linspace(0.005, 0.020, 19)
    big_r = rng.permutation(np.linspace(1.0, 18.0, 19))  # independent of r_hat
    y = 1.5 * big_r + 0.05 * rng.standard_normal(19)
    out = covariation_test(
        y, big_r, r_hat, permutations=2000, window_labels=list(m4_report.CLEAN_WINDOWS)
    )
    assert out["rho_partial"] >= 0.9
    assert out["pass_perm"] and out["p_perm"] <= m4_report.SPEARMAN_ALPHA
    assert out["cyclic_ok"] and out["leverage_ok"]
    assert out["verdict"] == "pass"
    assert set(out["drops"]) == {"drop_w8", "drop_w20", "drop_w8_w20"}
    assert out["label"] == "registered test of a post-hoc-flagged covariation"


def test_covariation_cyclic_null_sane_and_deterministic():
    rng = np.random.default_rng(13)
    y = rng.standard_normal(19)
    big_r = rng.standard_normal(19)
    r_hat = rng.standard_normal(19)
    out = covariation_test(y, big_r, r_hat, permutations=300)
    n = out["n_windows"]
    assert out["p_cyclic_min_attainable"] == pytest.approx(1.0 / n)
    assert 1.0 / n <= out["p_cyclic"] <= 1.0  # identity shift included
    out2 = covariation_test(y, big_r, r_hat, permutations=300)
    assert out == out2  # pinned-seed determinism
    with pytest.raises(ValueError):
        covariation_test(y[:5], big_r, r_hat)


def test_drift_trend_fields_and_band():
    drift = m4_report.drift_trend({5: 10.0, 6: 14.0, 7: 9.0, 8: 16.0, 9: 12.0})
    assert drift["spread"] == pytest.approx(7.0)
    assert drift["in_band"]  # [2, 40]
    assert drift["samples"] == [5, 6, 7, 8, 9]
    flat = m4_report.drift_trend({5: 10.0, 6: 10.5})
    assert not flat["in_band"]  # spread below the registered 2% floor is a finding


# ---------------------------------------------------------------- floor check (baseline-only)


def test_floor_check_rejects_twin_numbers_by_interface():
    with pytest.raises(ValueError):
        floor_check({"twin": 0.05, "naive": 0.075}, n_heldout_shots=500_000, gate_central_pct=10.0)
    with pytest.raises(ValueError):
        floor_check({"twin_static": 0.05}, n_heldout_shots=500_000, gate_central_pct=10.0)
    with pytest.raises(ValueError):
        floor_check({"pij": 0.07}, n_heldout_shots=500_000, gate_central_pct=10.0)  # naive required


def test_floor_check_trigger_arithmetic():
    res = floor_check({"naive": 0.075, "pij": 0.070}, n_heldout_shots=500_000, gate_central_pct=10.0)
    assert res["delta_hat"] == pytest.approx(0.15)  # min(2 * 0.075, 0.5)
    assert res["floor_pct"] == pytest.approx(1.70, abs=0.02)
    assert not res["extend"]  # 1.7% < 10%/2
    starved = floor_check({"naive": 0.075}, n_heldout_shots=2_000, gate_central_pct=10.0)
    assert starved["floor_pct"] > 5.0 and starved["extend"]
    assert starved["extension_samples"] == [10, 11, 12, 13, 14]
    # measured baseline discordance override (still baseline-only)
    meas = floor_check(
        {"naive": 0.075}, n_heldout_shots=500_000, gate_central_pct=10.0, baseline_discordance=0.01
    )
    assert meas["delta_hat"] == 0.01 and meas["floor_pct"] < res["floor_pct"]
    assert "baseline-only" in meas["delta_source"]


# ---------------------------------------------------------------- order-freeze state machine (S12/G2)


def _advance_to_floor_check(state: M4State) -> dict:
    state.begin("pins")
    state.complete("pins", {"passed": True})
    state.begin("freeze")
    src = {"qec_twin.hardware.dem_compose": "aaa", "qec_twin.hardware.m4_decode": "bbb", "m3_fit_cache": "ccc"}
    state.record_freeze(manifest={"arms": ["naive", "pij", "twin"], "clamp": [1e-6, 0.5 - 1e-6]},
                        source_hashes=src)
    state.complete("freeze", {})
    state.begin("pilot")
    state.complete("pilot", {"table_path": "pilot_table.json"})
    state.begin("select_rung")
    state.complete("select_rung", {"selection": {"d_prime_star": 7}})
    state.begin("p10_forecast")
    state.complete("p10_forecast", {"forecast_path": "p10.json"})
    state.begin("floor_check")
    state.complete("floor_check", {"extend": False})
    return src


def test_order_freeze_refuses_out_of_order(tmp_path):
    state = M4State(tmp_path / "m4_state")
    with pytest.raises(OrderFreezeError, match="prerequisite"):
        state.begin("pilot")
    with pytest.raises(OrderFreezeError, match="prerequisite"):
        state.check_order("heldout")
    state.begin("pins")
    with pytest.raises(OrderFreezeError, match="prerequisite"):
        state.begin("pilot")  # pins started but not COMPLETE
    state.complete("pins", {})
    with pytest.raises(OrderFreezeError, match="prerequisite"):
        state.begin("select_rung")  # freeze/pilot missing
    with pytest.raises(OrderFreezeError):
        state.begin("not_a_stage")


def test_order_freeze_forbids_rerun_after_later_stage_started(tmp_path):
    state = M4State(tmp_path / "m4_state")
    _advance_to_floor_check(state)
    with pytest.raises(OrderFreezeError, match="later stage"):
        state.begin("pilot")  # select_rung and later already ran
    with pytest.raises(OrderFreezeError, match="later stage"):
        state.begin("pins")


def test_heldout_requires_g2_manifest(tmp_path):
    state = M4State(tmp_path / "m4_state")
    state.begin("pins")
    state.complete("pins", {})
    state.begin("freeze")
    # freeze completed WITHOUT record_freeze => no G2 manifest
    state.complete("freeze", {})
    for name, payload in (
        ("pilot", {}),
        ("select_rung", {}),
        ("p10_forecast", {}),
        ("floor_check", {"extend": False}),
    ):
        state.begin(name)
        state.complete(name, payload)
    with pytest.raises(OrderFreezeError, match="manifest"):
        state.begin_heldout(current_source_hashes={}, samples=heldout_samples(False))


def test_heldout_refuses_on_changed_composition_hash_and_runs_once(tmp_path):
    state = M4State(tmp_path / "m4_state")
    src = _advance_to_floor_check(state)
    # source-hash drift => VOID
    drifted = dict(src, **{"qec_twin.hardware.dem_compose": "EDITED"})
    with pytest.raises(OrderFreezeError, match="source hash changed"):
        state.begin_heldout(current_source_hashes=drifted, samples=heldout_samples(False))
    # manifest content edit => VOID
    manifest_path = state.manifest_path
    original = manifest_path.read_text(encoding="utf-8")
    manifest_path.write_text(original + "\n", encoding="utf-8")
    with pytest.raises(OrderFreezeError, match="manifest content changed"):
        state.begin_heldout(current_source_hashes=src, samples=heldout_samples(False))
    manifest_path.write_text(original, encoding="utf-8")
    # missing manifest file => refuse
    manifest_path.unlink()
    with pytest.raises(OrderFreezeError, match="missing"):
        state.begin_heldout(current_source_hashes=src, samples=heldout_samples(False))
    manifest_path.write_text(original, encoding="utf-8")
    # clean entry succeeds and is persisted BEFORE completion
    state.begin_heldout(current_source_hashes=src, samples=heldout_samples(False))
    assert state.stage("heldout")["samples"] == [5, 6, 7, 8, 9]
    # a second attempt refuses even though the first never completed (crash = the one pass)
    with pytest.raises(OrderFreezeError, match="already been attempted"):
        state.begin_heldout(current_source_hashes=src, samples=heldout_samples(False))
    # persistence across reload
    reloaded = M4State(tmp_path / "m4_state")
    with pytest.raises(OrderFreezeError, match="already been attempted"):
        reloaded.begin_heldout(current_source_hashes=src, samples=heldout_samples(False))
    # ... and after completion it still refuses
    reloaded.complete("heldout", {"samples": [5, 6, 7, 8, 9]})
    with pytest.raises(OrderFreezeError, match="already been attempted"):
        reloaded.begin_heldout(current_source_hashes=src, samples=heldout_samples(False))
    # generic begin() may not bypass the G2-checked entry
    fresh = M4State(tmp_path / "other_state")
    with pytest.raises(OrderFreezeError, match="begin_heldout"):
        fresh.begin("heldout")


def test_main_cli_status_and_refusals(tmp_path, capsys):
    state_dir = str(tmp_path / "m4_state")
    assert m4_report.main(["status", "--state-dir", state_dir]) == 0
    out = capsys.readouterr().out
    assert "PENDING" in out and "pins" in out
    # out-of-order stages refuse with exit code 2 BEFORE importing B1/B2 or touching data
    assert m4_report.main(["pilot", "--state-dir", state_dir]) == 2
    assert "ORDER FREEZE refusal" in capsys.readouterr().out
    assert m4_report.main(["heldout", "--state-dir", state_dir]) == 2
    assert m4_report.main(["score", "--state-dir", state_dir]) == 2
    assert m4_report.main(["artifacts", "--state-dir", state_dir]) == 2


# ---------------------------------------------------------------- frozen-cache covariates / Tier-0


def _synthetic_record(basis, window, seed, ce, markov, q_eff):
    return FitRecord(
        basis=basis, window=int(window), seed=int(seed), split="full",
        ce_per_block=float(ce), law=np.zeros(256), q_eff=np.asarray(q_eff, dtype=np.float64),
        markov=np.asarray(markov, dtype=np.float64), fp_residual=1e-10, fp_rounds=40,
    )


def _synthetic_cache(windows, basis="X"):
    cache = {}
    for w in windows:
        good = np.array([[0.010, 0.012]] * 5)
        good[2] = [0.010, 0.020]  # central qubit: r = 0.0133.., R = 1.125
        bad = np.array([[0.030, 0.030]] * 5)
        cache[_cache_key(basis, w, 0, "full")] = _synthetic_record(
            basis, w, 0, 1.0, good, [0.012, 0.015, 0.013, 0.011]
        )
        cache[_cache_key(basis, w, 1, "full")] = _synthetic_record(
            basis, w, 1, 2.0, bad, [0.05, 0.05, 0.05, 0.05]
        )
    return cache


def test_frozen_covariates_lower_ce_selection_and_formulas():
    cache = _synthetic_cache([1, 2])
    cov = frozen_covariates(cache, "X", windows=(1, 2))
    for w in (1, 2):
        assert cov[w]["seed"] == 0  # lower train CE wins (M3 selection rule)
        p01, p10 = 0.010, 0.020
        assert cov[w]["r_hat"] == pytest.approx(2 * p01 * p10 / (p01 + p10))
        assert cov[w]["R_hat"] == pytest.approx((p01 + p10) ** 2 / (4 * p01 * p10))


def test_tier0_bands_ownership_and_abstain():
    cache = _synthetic_cache([1, 2])
    bands = tier0_bands(cache, "X", windows=(1, 2))
    data = bands["data_r_hat"]["sites"]
    # interior ownership filter: data positions w+1+{1,2,3} => {3,4,5} U {4,5,6}
    assert set(data) == {3, 4, 5, 6}
    assert data[4]["n_owners"] == 2 and data[3]["n_owners"] == 1
    assert data[4]["band"][0] <= data[4]["central"] <= data[4]["band"][1]
    assert not data[4]["abstain"]
    assert 0 in bands["data_r_hat"]["abstain_positions"]
    assert 28 in bands["data_r_hat"]["abstain_positions"]
    meas = bands["measure_q_eff"]["sites"]
    assert set(meas) == {2, 3, 4, 5, 6}  # w+1..w+4 for w in {1, 2}
    assert 0 in bands["measure_q_eff"]["abstain_positions"]
    assert 27 in bands["measure_q_eff"]["abstain_positions"]


# ---------------------------------------------------------------- P10 sampler (GPU)

cuda_only = pytest.mark.skipif(not torch.cuda.is_available(), reason="P10 sampler is GPU-only")


def test_p10_sampler_refuses_cpu():
    """Project rule: model compute never falls back to CPU."""
    with pytest.raises(RuntimeError, match="GPU-only"):
        m4_report.sample_window_twin_shots(
            np.full((5, 2), 0.01), np.full(4, 0.01), shots=10, seed=1, device="cpu"
        )
    with pytest.raises(ValueError):
        m4_report.sample_window_twin_shots(
            np.full((4, 2), 0.01), np.full(4, 0.01), shots=10, seed=1, device="cuda"
        )


@cuda_only
def test_p10_sampler_matches_twin_model_statistics():
    """Equivalence pins for the documented M3-model sampler conventions:
    (i) bulk detector marginal obeys 1-2f = (1-2r_k)(1-2r_{k+1})(1-2q_k)^2 (a);
    (ii) observable flip rate = pi_1 (1 - lambda^T) of the two-state chain (a);
    (iii) final layer = readout flips only; (iv) same-site dt=1 Spitz edge ~ q."""
    from qec_twin.hardware.pij import spitz_pij_exact

    markov = np.array(
        [[0.010, 0.012], [0.011, 0.013], [0.012, 0.010], [0.009, 0.014], [0.013, 0.011]]
    )
    q = np.array([0.012, 0.015, 0.013, 0.011])
    shots = 60_000
    dets_flat, obs = m4_report.sample_window_twin_shots(
        markov, q, shots=shots, seed=123, device="cuda", chunk_shots=shots
    )
    layers = m4_report.NUM_ANCILLA_ROUNDS + 1
    assert dets_flat.shape == (shots, layers * 4) and obs.shape == (shots,)
    dets = dets_flat.reshape(shots, layers, 4)

    r = 2.0 * markov[:, 0] * markov[:, 1] / (markov[:, 0] + markov[:, 1])
    f_meas = dets[:, 100:900, :].mean(axis=(0, 1))  # uint8 reduction, no float copy
    f_pred = 0.5 * (1.0 - (1.0 - 2.0 * r[:4]) * (1.0 - 2.0 * r[1:]) * (1.0 - 2.0 * q) ** 2)
    assert np.abs(f_meas - f_pred).max() < 1.0e-3

    p01, p10 = markov[0]
    pi1 = p01 / (p01 + p10)
    lam = 1.0 - p01 - p10
    obs_pred = pi1 * (1.0 - lam ** m4_report.NUM_ANCILLA_ROUNDS)
    assert obs.mean() == pytest.approx(obs_pred, abs=0.012)

    final = dets[:, -1, :].astype(np.float64).mean(axis=0)
    assert np.abs(final - q).max() < 3.0e-3  # final layer carries readout flips only

    for k in range(4):
        ak = dets[:, 100:899, k]
        bk = dets[:, 101:900, k]
        pij_time = float(
            spitz_pij_exact(
                np.float64(ak.mean()),
                np.float64(bk.mean()),
                np.float64((ak & bk).mean()),
            )
        )
        assert abs(pij_time - q[k]) < 1.2e-3  # time edge rate = q_eff (S5 TIME assignment)


@cuda_only
def test_p10_sampler_seed_determinism():
    markov = np.full((5, 2), 0.012)
    q = np.full(4, 0.013)
    d1, o1 = m4_report.sample_window_twin_shots(markov, q, shots=512, seed=7, device="cuda")
    d2, o2 = m4_report.sample_window_twin_shots(markov, q, shots=512, seed=7, device="cuda")
    d3, _ = m4_report.sample_window_twin_shots(markov, q, shots=512, seed=8, device="cuda")
    assert np.array_equal(d1, d2) and np.array_equal(o1, o2)
    assert not np.array_equal(d1, d3)


@cuda_only
def test_p10_forecast_records_before_heldout(tmp_path):
    """p10_forecast produces per-window predictions from the frozen cache with a
    pinned per-(basis, window) seed and the cache-key provenance recorded."""
    cache = _synthetic_cache([1, 2])
    forecast = m4_report.p10_forecast(
        cache,
        dem_for_window=lambda basis, w: None,
        decode_fn=lambda dem, dets: np.zeros(dets.shape[0], dtype=np.uint8),
        bases=("X",),
        windows=(1, 2),
        mc_shots=4000,
        device="cuda",
    )
    rows = forecast["predictions"]["X"]
    assert set(rows) == {1, 2}
    p01, p10 = 0.010, 0.012  # qubit-0 row of the synthetic cache (the observable qubit)
    pi1 = p01 / (p01 + p10)
    for w, row in rows.items():
        # a zero-prediction decoder leaves the raw observable flip rate
        assert row["predicted_ler"] == pytest.approx(pi1, abs=0.05)
        assert row["mc_shots"] == 4000
        assert row["seed"] == m4_report.p10_window_seed("X", w)
        assert row["cache_key"] == _cache_key("X", w, 0, "full")
    assert forecast["ratio_band"] == [0.5, 2.0]
    path = tmp_path / "p10.json"
    text = json.dumps(forecast, default=m4_report._json_default)
    path.write_text(text, encoding="utf-8")
    assert json.loads(path.read_text(encoding="utf-8"))["predictions"]["X"]


def test_p10_window_seed_distinct():
    seeds = {m4_report.p10_window_seed(b, w) for b in ("X", "Z") for w in m4_report.CLEAN_WINDOWS}
    assert len(seeds) == 2 * len(m4_report.CLEAN_WINDOWS)


# ---------------------------------------------------------------- scoring + routing (S7/S10)


def _measured_stub(gate_pass=True, p10_pass=True, headline_pct=1.0, cov="pass", saturated=False):
    return {
        "gate": {"pass_one_sided_99": gate_pass},
        "p10": {"passed": p10_pass},
        "headline": {"pct_delta": headline_pct},
        "covariation": {"verdict": cov},
        "regime": {"saturated_majority": saturated},
    }


def test_route_s10_flags():
    assert m4_report.route_s10({"X": _measured_stub()}) == []
    fork_a = m4_report.route_s10({"X": _measured_stub(gate_pass=False, p10_pass=True)})
    assert [f["code"] for f in fork_a] == ["GATE_FAIL_DEM_FORMAT_BOTTLENECK"]
    fork_b = m4_report.route_s10({"X": _measured_stub(gate_pass=False, p10_pass=False)})
    assert [f["code"] for f in fork_b] == ["GATE_FAIL_CALIBRATION_DIRECTION"]
    neg = m4_report.route_s10({"Z": _measured_stub(headline_pct=-12.0)})
    assert [f["code"] for f in neg] == ["HEADLINE_NEG_AUDIT_COMPOSITION"]
    cov = m4_report.route_s10({"X": _measured_stub(cov="null")})
    assert [f["code"] for f in cov] == ["COVARIATION_NULL_STRUCTURAL"]
    cov_ok = m4_report.route_s10({"X": _measured_stub(cov="null")}, m3_nll_structure_intact=False)
    assert cov_ok == []
    sat = m4_report.route_s10({"X": _measured_stub(saturated=True)})
    assert [f["code"] for f in sat] == ["REGIME_RE_REGISTER"]


def _full_synthetic_basis_results(basis="X", d_prime=7):
    rng = np.random.default_rng(42)
    n = 4000
    windows = list(m4_report.CLEAN_WINDOWS)
    # gate instrument: 4 disjoint subchains at d'=7
    naive_g = (rng.random((n, 4)) < 0.10).astype(np.uint8)
    twin_g = (naive_g.astype(bool) & (rng.random((n, 4)) < 0.85)).astype(np.uint8)
    pij_g = (naive_g.astype(bool) & (rng.random((n, 4)) < 0.95)).astype(np.uint8)
    # window instrument with located structure and an R_hat-tracking effect
    covariates = {}
    r_values = np.linspace(0.008, 0.016, 19)
    big_values = np.linspace(1.5, 14.0, 19)
    rng.shuffle(big_values)
    pij_w = (rng.random((n, 19)) < 0.12).astype(np.uint8)
    naive_w = (pij_w.astype(bool) | (rng.random((n, 19)) < 0.02)).astype(np.uint8)
    twin_w = np.empty_like(pij_w)
    for i, w in enumerate(windows):
        big = 1.0 if w in (20, 21) else float(big_values[i])
        covariates[w] = {"R_hat": big, "r_hat": float(r_values[i])}
        if w in (20, 21):
            twin_w[:, i] = (pij_w[:, i].astype(bool) | (rng.random(n) < 0.01)).astype(np.uint8)
        else:
            keep = 1.0 - 0.02 * big
            twin_w[:, i] = (pij_w[:, i].astype(bool) & (rng.random(n) < keep)).astype(np.uint8)
    a3c_w = twin_w.copy()
    for i, w in enumerate(windows):
        if covariates[w]["R_hat"] >= m4_report.A3C_HIGH_R_MIN and w not in (20, 21):
            a3c_w[:, i] = (twin_w[:, i].astype(bool) & (rng.random(n) < 0.97)).astype(np.uint8)
    p10_predicted = {w: float(twin_w[:, i].mean()) for i, w in enumerate(windows)}
    slices = {s: slice(800 * k, 800 * (k + 1)) for k, s in enumerate((5, 6, 7, 8, 9))}
    return m4_report.compute_basis_results(
        basis=basis,
        d_prime=d_prime,
        gate_errors={"twin": twin_g, "naive": naive_g, "pij": pij_g},
        window_errors={"twin": twin_w, "naive": naive_w, "pij": pij_w},
        window_ids=windows,
        covariates=covariates,
        p10_predicted=p10_predicted,
        per_sample_slices=slices,
        a3c_errors=a3c_w,
        rl_xor_per_1e5=3.0,
    )


def test_compute_basis_results_and_score_s7():
    measured = _full_synthetic_basis_results()
    gate = measured["gate"]
    assert gate["pass_one_sided_99"]
    assert gate["pct_delta"] == pytest.approx(15.0, abs=3.0)
    assert gate["in_band"]  # X, d'=7: [2, 30]
    assert gate["band"] == {"lo": 2.0, "hi": 30.0, "central": 10.0}
    assert gate["protocol"]["d_prime"] == 7 and gate["protocol"]["T"] == 1000
    assert not math.isnan(gate["protocol"]["c_s_hat"])
    assert gate["mcnemar"]["n01"] == 0  # twin errors nested in naive errors
    head = measured["headline"]
    assert head["band"]["central"] == 1.5 and head["band"]["central_branch"] == "gap~0"
    assert head["in_band"]  # ~ +10.5 in [-10, +15]
    assert measured["pij_vs_naive"]["in_band"]  # ~ +5 in [+2, +25]
    assert measured["located"]["all_ok"]
    assert measured["regime"]["passed"] and not measured["regime"]["excluded_saturated"]
    assert measured["p10"]["passed"] and measured["p10"]["fraction_in_band"] == 1.0
    assert measured["drift"] is not None and len(measured["per_sample"]["gate"]) == 5
    controls = measured["a3c"]["controls"]
    assert set(controls) == {20, 21}
    assert measured["covariation"]["verdict"] in ("pass", "confound-consistent", "null")

    scored = m4_report.score_s7({"X": measured})
    items = [row["item"] for row in scored["rows"]]
    assert any("PRIMARY-1 GATE" in i for i in items)
    assert any("PRIMARY-2 HEADLINE" in i for i in items)
    assert any("G5 covariation" in i for i in items)
    assert any("located signs" in i for i in items)
    assert any("regime pin" in i for i in items)
    assert any("P10 predict-before-measure" in i for i in items)
    assert any("drift" in i for i in items)
    assert any("A3c" in i for i in items)
    assert any("dMLE" in i for i in items)
    assert any("reverse trap" in i for i in items)
    assert any("full-code context" in i for i in items)
    assert scored["primaries_per_basis"] == 2
    assert all("class" in row for row in scored["rows"])
    # routing: gate passed, headline in band, regime clean => only a possible
    # covariation flag (synthetic binary noise) may appear
    flags = {f["code"] for f in m4_report.route_s10({"X": measured})}
    assert flags <= {"COVARIATION_NULL_STRUCTURAL"}


def test_per_window_pct_delta_sign_convention():
    a = np.zeros((100, 2), dtype=np.uint8)
    b = np.zeros((100, 2), dtype=np.uint8)
    b[:10, 0] = 1  # B errs 10% on window 8, A errs 0% => A vs B = +100%
    out = m4_report.per_window_pct_delta(a, b, [8, 9])
    assert out[8] == pytest.approx(100.0)
    assert out[9] == pytest.approx(0.0)


# ---------------------------------------------------------------- FIX ROUND (2026-06-10, post-review)


def test_pins_registry_has_no_p1c_and_registered_scopes():
    """Reviewer B-11: B2 ships exactly these runners — pin_p1c DOES NOT exist;
    P1c is routed through B1's round-trip machinery. Pin sample scopes are the
    registered ones (run plan + AMENDMENT 1 ruling 15); the escrow is never
    touched by any pin."""
    assert m4_report.B2_PIN_RUNNERS == ("p1a", "p1b", "p1d", "p1e", "p1f", "p1g")
    assert "p1c" not in m4_report.B2_PIN_RUNNERS
    assert "roundtrip_report" in m4_report.P1C_OWNER and "B1" in m4_report.P1C_OWNER
    assert m4_report.P1A_SAMPLES == (0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14)
    assert not set(m4_report.P1A_SAMPLES) & set(m4_report.ESCROW_SAMPLES)
    assert m4_report.P1E_SAMPLES == (0, 50, 99)
    assert not set(m4_report.P1E_SAMPLES) & set(m4_report.ESCROW_SAMPLES)
    assert m4_report.P1E_HALT_MISMATCH == 1e-3
    # AMENDMENT 1 ruling 14 design constants pinned verbatim
    assert m4_report.P1H_BAND_TOL == 5e-3
    assert m4_report.P1H_MEAN_MATCH_TOL == 1e-9
    assert m4_report.P1H_INTERIOR_MAX_DEV == 3e-2
    assert "ADR-0008-H3" in m4_report.P1H_FINDING_TAG


def test_rr_table_chain_pair_adaptor():
    """Reviewer B-16 (owner B3): B1's two_pass_table keys by DATA QUBIT g; B2's
    rR_table keys by chain pair (g-1, g). Direction: B1 {g} -> B2 {(g-1, g)}."""
    out = m4_report.rr_table_chain_pairs({17: (0.01, 3.0), 1: (0.02, 1.0)})
    assert out == {(16, 17): (0.01, 3.0), (0, 1): (0.02, 1.0)}
    # boundary coincidence: a window's leftmost data qubit w+1 maps to
    # (w, w+1) = B2's (min_chain - 1, min_chain) boundary convention
    w = 7
    assert (w, w + 1) in m4_report.rr_table_chain_pairs({w + 1: (0.01, 2.0)})


def _p1h_arrays(interior_dev=0.0):
    """10-site synthetic field: sites 0 and 9 are mean-matched (targets met
    exactly), sites 1..8 are interior with a uniform deviation."""
    measured = np.full(10, 0.05)
    marginals = measured.copy()
    marginals[1:9] += interior_dev
    mm_idx = np.array([0, 9])
    mm_targets = measured[mm_idx].copy()
    interior_idx = np.arange(1, 9)
    return marginals, measured, mm_idx, mm_targets, interior_idx


def test_p1h_split_structural_passes_while_band_misses():
    """Ruling 14 BOTH SIDES, the measured shape: a one-signed POSITIVE interior
    surplus beyond +/-0.5% (the A2/twin finding) passes the structural gate
    (no halt) while the per-arm band row records the REGISTERED FINDING."""
    marginals, measured, mm_idx, mm_targets, interior_idx = _p1h_arrays(interior_dev=6e-3)
    gate = m4_report.p1h_structural_gate(
        marginals, measured,
        mean_matched_idx=mm_idx, mean_matched_targets=mm_targets, interior_idx=interior_idx,
    )
    assert gate["passed"] and not gate["halt"] and gate["reasons"] == []
    assert gate["interior_max_dev"] == pytest.approx(6e-3)
    assert gate["mean_matched_violations"] == 0
    # component (ii): the band miss is a finding, never a halt
    band = m4_report.p1h_band_row("twin", num_out=8, num_sites=10, max_abs_dev=6e-3, mean_abs_dev=4.8e-3)
    assert not band["in_band"] and band["halts_freeze"] is False
    finding = band["registered_finding"]
    assert "ADR-0008-H3" in finding["tag"]
    assert "never citable as fact" in finding["status"]
    assert "never a halt" in finding["status"]


def test_p1h_structural_gate_halts_on_each_component():
    """Ruling 14(i) halt cases: negative out-of-band deficit (one-signed
    violation), NaN marginal, negative marginal, mean-match violation > 1e-9,
    and the 3e-2 catastrophe tripwire."""
    # (1) interior deficit beyond the band => one-signed-positive violation
    marginals, measured, mm_idx, mm_targets, interior_idx = _p1h_arrays(interior_dev=-6e-3)
    gate = m4_report.p1h_structural_gate(
        marginals, measured, mean_matched_idx=mm_idx, mean_matched_targets=mm_targets,
        interior_idx=interior_idx)
    assert not gate["passed"] and gate["interior_negative_out_of_band"] == 8
    assert any("one-signed" in r for r in gate["reasons"])
    # within-band negative noise does NOT halt (the measured field fluctuates)
    marginals, measured, mm_idx, mm_targets, interior_idx = _p1h_arrays(interior_dev=-2e-3)
    assert m4_report.p1h_structural_gate(
        marginals, measured, mean_matched_idx=mm_idx, mean_matched_targets=mm_targets,
        interior_idx=interior_idx)["passed"]
    # (2) NaN marginal
    marginals, measured, mm_idx, mm_targets, interior_idx = _p1h_arrays(2e-3)
    marginals[4] = np.nan
    gate = m4_report.p1h_structural_gate(
        marginals, measured, mean_matched_idx=mm_idx, mean_matched_targets=mm_targets,
        interior_idx=interior_idx)
    assert not gate["passed"] and gate["nan_marginals"] == 1
    # (3) negative marginal
    marginals, measured, mm_idx, mm_targets, interior_idx = _p1h_arrays(2e-3)
    marginals[2] = -1e-6
    gate = m4_report.p1h_structural_gate(
        marginals, measured, mean_matched_idx=mm_idx, mean_matched_targets=mm_targets,
        interior_idx=interior_idx)
    assert not gate["passed"] and gate["negative_marginals"] == 1
    # (4) mean-matched site off target beyond 1e-9
    marginals, measured, mm_idx, mm_targets, interior_idx = _p1h_arrays(2e-3)
    marginals[0] += 5e-9
    gate = m4_report.p1h_structural_gate(
        marginals, measured, mean_matched_idx=mm_idx, mean_matched_targets=mm_targets,
        interior_idx=interior_idx)
    assert not gate["passed"] and gate["mean_matched_violations"] == 1
    # ... and 1e-10 stays within the structural tolerance
    marginals, measured, mm_idx, mm_targets, interior_idx = _p1h_arrays(2e-3)
    marginals[0] += 1e-10
    assert m4_report.p1h_structural_gate(
        marginals, measured, mean_matched_idx=mm_idx, mean_matched_targets=mm_targets,
        interior_idx=interior_idx)["passed"]
    # (5) catastrophe tripwire: positive surplus above 3e-2
    marginals, measured, mm_idx, mm_targets, interior_idx = _p1h_arrays(3.1e-2)
    gate = m4_report.p1h_structural_gate(
        marginals, measured, mean_matched_idx=mm_idx, mean_matched_targets=mm_targets,
        interior_idx=interior_idx)
    assert not gate["passed"] and any("tripwire" in r for r in gate["reasons"])


def test_p1h_band_row_in_band_has_no_finding():
    row = m4_report.p1h_band_row("pij", num_out=0, num_sites=28_056, max_abs_dev=1e-3, mean_abs_dev=1e-4)
    assert row["in_band"] and "registered_finding" not in row
    assert row["halts_freeze"] is False
    assert row["tol"] == m4_report.P1H_BAND_TOL


def test_sim_round_trip_pass_rule_c5():
    """Reviewer C-5/B-13: the declared (c) completion consumes the REAL
    SimRoundTripResult fields (a NamedTuple, no .get); NaN predicted_ler (the
    non-enumerable run-scale case) passes when sim < raw and sim < 0.45."""
    from collections import namedtuple

    R = namedtuple("R", "sim_ler predicted_ler raw_flip_rate n_shots seed")
    nan = float("nan")
    assert m4_report.sim_round_trip_pass(R(0.10, nan, 0.30, 1000, 1))["passed"]
    assert not m4_report.sim_round_trip_pass(R(nan, nan, 0.30, 1000, 1))["passed"]
    assert not m4_report.sim_round_trip_pass(R(0.46, nan, 0.50, 1000, 1))["passed"]  # >= 0.45
    assert not m4_report.sim_round_trip_pass(R(0.30, nan, 0.30, 1000, 1))["passed"]  # sim >= raw
    out = m4_report.sim_round_trip_pass(R(0.10, 0.101, 0.30, 1000, 7))
    assert out["predicted_ler"] == 0.101 and out["seed"] == 7
    assert "pipeline bug" in out["rule"]


def test_unit_actual_observables_guard_is_loud():
    """Reviewer B-12 / change item 2: error arrays are never fabricated — a
    missing B2 helper raises with the contract spelled out."""

    class _StubB2:
        pass

    with pytest.raises(OrderFreezeError, match="unit_actual_observables"):
        m4_report._require_unit_actual_observables(_StubB2())

    # present helper: _unit_actual forwards (data_lo, data_hi) PAIRS (B2's landed
    # convention) + the explicit allow_heldout flag, and shape-validates
    seen = {}

    class _GoodB2:
        @staticmethod
        def unit_actual_observables(ds, basis, sample, units, *, allow_heldout=False):
            seen["units"] = list(units)
            seen["allow_heldout"] = allow_heldout
            return np.zeros((4, len(units)), dtype=np.uint8)

    out = m4_report._unit_actual(
        _GoodB2(), None, "X", 0, [(0, 28), (8, 12)], 4, allow_heldout=False
    )
    assert out.shape == (4, 2) and out.dtype == np.uint8
    assert seen["units"] == [(0, 28), (8, 12)] and seen["allow_heldout"] is False
    out = m4_report._unit_actual(
        _GoodB2(), None, "X", 7, [(9, 13)], 4, allow_heldout=True
    )
    assert seen["allow_heldout"] is True
    with pytest.raises(ValueError, match="shots, n_units"):
        m4_report._unit_actual(_GoodB2(), None, "X", 0, [(0, 28)], 9, allow_heldout=False)


def test_covariation_restricted_to_primary_samples_under_extension():
    """Reviewer S7/SF fix: even when the extension (10-14) triggered, the G5
    covariation is computed on samples 05-09 ONLY. Constructed so the
    R-tracking effect lives in the primary rows and is corrupted in the
    extension rows — the scored rho must equal the restricted computation."""
    rng = np.random.default_rng(21)
    windows = list(m4_report.CLEAN_WINDOWS)
    n_primary, n_ext = 2000, 2000
    n = n_primary + n_ext
    r_values = np.linspace(0.008, 0.016, 19)
    big_values = rng.permutation(np.linspace(1.5, 14.0, 19))
    covariates = {w: {"R_hat": float(big_values[i]), "r_hat": float(r_values[i])}
                  for i, w in enumerate(windows)}
    pij_w = (rng.random((n, 19)) < 0.12).astype(np.uint8)
    naive_w = (pij_w.astype(bool) | (rng.random((n, 19)) < 0.02)).astype(np.uint8)
    twin_w = np.empty_like(pij_w)
    for i, w in enumerate(windows):
        keep = 1.0 - 0.03 * covariates[w]["R_hat"]
        twin_w[:n_primary, i] = (
            pij_w[:n_primary, i].astype(bool) & (rng.random(n_primary) < keep)
        ).astype(np.uint8)
        extra = 0.004 * covariates[w]["R_hat"]  # extension rows REVERSE the tracking
        twin_w[n_primary:, i] = (
            pij_w[n_primary:, i].astype(bool) | (rng.random(n_ext) < extra)
        ).astype(np.uint8)
    naive_g = (rng.random((n, 3)) < 0.10).astype(np.uint8)
    twin_g = (naive_g.astype(bool) & (rng.random((n, 3)) < 0.85)).astype(np.uint8)
    pij_g = (naive_g.astype(bool) & (rng.random((n, 3)) < 0.95)).astype(np.uint8)
    slices = {s: slice(400 * k, 400 * (k + 1)) for k, s in enumerate(range(5, 15))}
    measured = m4_report.compute_basis_results(
        basis="X", d_prime=7,
        gate_errors={"twin": twin_g, "naive": naive_g, "pij": pij_g},
        window_errors={"twin": twin_w, "naive": naive_w, "pij": pij_w},
        window_ids=windows, covariates=covariates, per_sample_slices=slices,
    )
    cov = measured["covariation"]
    assert cov["covariation_samples"] == [5, 6, 7, 8, 9]
    delta_restricted = m4_report.per_window_pct_delta(
        twin_w[:n_primary], pij_w[:n_primary], windows)
    delta_full = m4_report.per_window_pct_delta(twin_w, pij_w, windows)
    big = [covariates[w]["R_hat"] for w in windows]
    small = [covariates[w]["r_hat"] for w in windows]
    rho_restricted = partial_spearman([delta_restricted[w] for w in windows], big, small)
    rho_full = partial_spearman([delta_full[w] for w in windows], big, small)
    assert abs(rho_restricted - rho_full) > 1e-6  # the restriction is observable
    assert cov["rho_partial"] == pytest.approx(rho_restricted, abs=1e-12)
    assert cov["rho_partial"] != pytest.approx(rho_full, abs=1e-12)
    assert rho_restricted > 0.5  # the primary-rows effect is the clean signal


def test_a3b_drift_context_sliding_and_dmle_rows_in_score_s7():
    """Reviewer change item 6: A3b scored from saved arrays (claim-separated),
    the 01-04 drift-context rows carried context-only, the sliding-window
    secondary recorded dropped-with-documentation, and the dMLE attempt record
    attached to the conditional row."""
    rng = np.random.default_rng(33)
    n = 3000
    windows = list(m4_report.CLEAN_WINDOWS)
    pij_w = (rng.random((n, 19)) < 0.12).astype(np.uint8)
    naive_w = (pij_w.astype(bool) | (rng.random((n, 19)) < 0.02)).astype(np.uint8)
    twin_w = (pij_w.astype(bool) & (rng.random((n, 19)) < 0.9)).astype(np.uint8)
    a3b_w = (pij_w.astype(bool) & (rng.random((n, 19)) < 0.97)).astype(np.uint8)
    naive_g = (rng.random((n, 3)) < 0.10).astype(np.uint8)
    twin_g = (naive_g.astype(bool) & (rng.random((n, 3)) < 0.85)).astype(np.uint8)
    pij_g = (naive_g.astype(bool) & (rng.random((n, 3)) < 0.95)).astype(np.uint8)
    covariates = {w: {"R_hat": 2.0, "r_hat": 0.01} for w in windows}
    context = {
        "samples": [1, 2, 3, 4],
        "gate_pct": {1: 12.0, 2: 14.0, 3: 11.0, 4: 13.0},
        "headline_pct": {1: 2.0, 2: 3.0, 3: 1.0, 4: 2.5},
        "note": "context-only",
    }
    measured = m4_report.compute_basis_results(
        basis="X", d_prime=7,
        gate_errors={"twin": twin_g, "naive": naive_g, "pij": pij_g},
        window_errors={"twin": twin_w, "naive": naive_w, "pij": pij_w},
        window_ids=windows, covariates=covariates,
        a3b_errors=a3b_w, drift_context=context,
    )
    a3b = measured["a3b"]
    assert a3b["vs_pij"]["pct_delta"] > 0  # a3b removes pij errors by construction
    assert "CLAIM-SEPARATED" in a3b["claim_note"]
    assert measured["drift_context"]["samples"] == [1, 2, 3, 4]

    attempt = {"protocol": "run-unmodified-or-drop (ratified R4)", "attempted": True,
               "outcome": "failed-to-run", "reason": "no upstream adaptor"}
    scored = m4_report.score_s7({"X": measured}, dmle_attempt=attempt)
    items = [row["item"] for row in scored["rows"]]
    assert any("A3b Spitz-of-the-twin" in i for i in items)
    assert any("drift context samples 01-04" in i for i in items)
    sliding = next(r for r in scored["rows"] if "sliding-window" in r["item"])
    assert sliding["status"] == "dropped-with-documentation"
    assert "held-out" in sliding["reason"]
    dmle_row = next(r for r in scored["rows"] if r["item"] == "dMLE conditional")
    assert dmle_row["attempt_record"]["outcome"] == "failed-to-run"
    # without a record, the row carries the loud open-obligation flag
    scored_bare = m4_report.score_s7({"X": measured})
    dmle_bare = next(r for r in scored_bare["rows"] if r["item"] == "dMLE conditional")
    assert "ABSENT" in dmle_bare["attempt_record"]


def test_record_dmle_attempt_roundtrip(tmp_path):
    rec = m4_report.record_dmle_attempt(
        tmp_path, attempted=True, outcome="dropped",
        version="DMLE-QEC (vendored pristine, external/baselines)",
        reason="documented drop",
    )
    assert rec["protocol"] == "run-unmodified-or-drop (ratified R4)"
    loaded = m4_report.load_dmle_attempt(tmp_path)
    assert loaded == json.loads(json.dumps(rec))  # JSON round-trip identical
    assert m4_report.load_dmle_attempt(tmp_path / "nowhere") is None


def test_sliding_window_secondary_drop_record():
    rec = m4_report.SLIDING_WINDOW_SECONDARY
    assert rec["status"] == "dropped-with-documentation"
    assert "pre-held-out" in rec["recorded"]
    assert "never silently" in rec["reason"]


# ---------------------------------------------------------------- hardware-gated (sample_00 / frozen cache ONLY)

hw_dataset = pytest.mark.skipif(
    resolve_rep29_root() is None, reason="R2-lite d29 dataset absent (set QEC_TWIN_HW_DATA)"
)
hw_cache = pytest.mark.skipif(
    not Path(FIT_CACHE).exists(), reason="frozen M3 fit cache absent (outputs/m3_fit_cache.pt)"
)


@hw_dataset
def test_hw_train_sample_artifacts_exist():
    """Touches sample_00 paths ONLY (samples 01-99 are off-limits in the build)."""
    from qec_twin.hardware.dataset import RepCodeD29

    ds = RepCodeD29.from_env()
    for basis in ds.bases:
        paths = ds.paths(basis, m4_report.TRAIN_SAMPLE)
        assert paths.detection_events.exists()
        assert paths.circuit_noisy_si1000.exists()


@hw_cache
def test_hw_frozen_covariates_match_m3_findings():
    """Frozen full-split centrals (central qubit, lower-CE seed): R_hat in the
    banked M3 range [1.0, 17.7]; w20 pinned at 1.000 in BOTH bases."""
    cache = torch.load(FIT_CACHE, weights_only=False)
    for basis in ("X", "Z"):
        cov = frozen_covariates(cache, basis)
        assert set(cov) == set(m4_report.CLEAN_WINDOWS)
        for w, row in cov.items():
            assert row["R_hat"] >= 1.0 - 1e-9  # AM-GM floor
            assert row["R_hat"] <= 25.0
            assert 1e-4 < row["r_hat"] < 5e-2
        assert cov[20]["R_hat"] == pytest.approx(1.0, abs=5e-2)


@hw_cache
def test_hw_tier0_bands_from_frozen_cache():
    cache = torch.load(FIT_CACHE, weights_only=False)
    bands = tier0_bands(cache, "X")
    data = bands["data_r_hat"]["sites"]
    meas = bands["measure_q_eff"]["sites"]
    assert all(1 <= row["n_owners"] <= 3 for row in data.values())
    assert all(1 <= row["n_owners"] <= 4 for row in meas.values())
    assert all(row["band"][0] <= row["central"] <= row["band"][1] for row in data.values())
    for pos in (0, 1, 2, 26, 27, 28):
        assert pos in bands["data_r_hat"]["abstain_positions"]
    for pos in (0, 1, 26, 27):
        assert pos in bands["measure_q_eff"]["abstain_positions"]
