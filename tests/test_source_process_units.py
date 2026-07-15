"""Per-unit L0+L1+L2 coverage of
``error_coupling_simulator.source.process`` (33 CPU-pure public units; no GPU, no quimb,
so out_of_scope is empty).

``source/process.py`` owns the Axis-2 explicit cross-cycle SOURCE processes -- evaluator-side
latent timelines (RTN telegraph, log-spaced 1/f RTN sum, gap-engineered phase-burst, two-state
temporal-storm HMM) that persist across QEC cycles and emit payloads consumed downstream by
``source_coupling.Theta``.

L2 DISCIPLINE (the standing lesson: 100% coverage != discrimination). Every load-bearing value is
PINNED against an INDEPENDENT recompute (a from-scratch closed form or a from-scratch RNG replay --
NEVER the module's own helper), and every validation RAISE asserts its EXACT message string via
``str(excinfo.value) == ...`` (mutmut wraps/roundtrips string literals -- a substring ``match=``
still passes them, an exact-equality assert kills them). The RTN telegraph chain and the HMM storm
chain are pinned by a DETERMINISTIC from-scratch reimplementation of the same seeded RNG calls, so
the flip/emission logic is discriminated without any statistical-convergence tolerance (the heavy
sampled-autocovariance falsifiers live in tests/test_source_closed_forms.py, not duplicated here).
``assert_discriminates`` gives each closed-form invariant a demonstrated sabotage variant it rejects.
"""
from __future__ import annotations

import json
import math
import os

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from _support.faithfulness import (
    assert_discriminates,
    assert_pins,
    assert_prob_dist,
    assert_row_stochastic,
)

import error_coupling_simulator.source.process as sp
from error_coupling_simulator.source.process import (
    OneOverFDriftSource,
    PhaseBurstSource,
    RTNSource,
    SourceProcess,
    SourceTimeline,
    TemporalStormSPPSource,
    lag_autocorrelation,
    timeline_to_coupled_params,
    timeline_to_site_coupled_params,
)
from error_coupling_simulator.source.coupling import (
    SourceCouplingConfig,
    default_source_coupling_config,
    independent_baseline_trajectory_to_params,
    trajectory_to_params,
)

_TWO_PI = 2.0 * math.pi
_PAULI_ORDER = ("I", "X", "Y", "Z")


# --------------------------------------------------------------------------- #
# helpers (exact-message raise + INDEPENDENT recomputes, NOT the module's own)  #
# --------------------------------------------------------------------------- #
def _raises_exact(exc, msg, fn):
    """pytest.raises pinning the EXACT message string (kills mutmut's string-literal
    wrap/roundtrip mutations that a substring ``match=`` lets survive)."""
    with pytest.raises(exc) as ei:
        fn()
    assert str(ei.value) == msg, f"message mismatch\n got: {str(ei.value)!r}\n exp: {msg!r}"


def _indep_flip_prob(gamma: float) -> float:
    return 0.5 * (1.0 - math.exp(-2.0 * gamma))


def _indep_autocorr_base(gamma: float) -> float:
    return math.exp(-2.0 * gamma)


def _indep_geomspace(lo: float, hi: float, n: int) -> np.ndarray:
    """Log-linear geometric spacing computed WITHOUT np.geomspace (independent)."""
    if n == 1:
        return np.asarray([float(lo)])
    ll, lh = math.log(lo), math.log(hi)
    return np.asarray([math.exp(ll + (lh - ll) * i / (n - 1)) for i in range(n)])


def _indep_amps(src: OneOverFDriftSource) -> np.ndarray:
    return np.full(int(src.n_fluctuators),
                   float(src.amplitude_radns) / math.sqrt(float(src.n_fluctuators)))


def _indep_psd(src: OneOverFDriftSource, omega) -> np.ndarray:
    g = _indep_geomspace(float(src.gamma_min_per_cycle), float(src.gamma_max_per_cycle),
                         int(src.n_fluctuators))
    a = _indep_amps(src)
    w = np.asarray(omega, dtype=np.float64)
    out = np.zeros_like(w)
    for gi, ai in zip(g, a):
        out += ai * ai * (4.0 * gi) / ((2.0 * gi) ** 2 + w * w)
    return out


def _indep_pearson(a: np.ndarray, b: np.ndarray) -> float:
    am = a - a.mean()
    bm = b - b.mean()
    denom = math.sqrt(float((am * am).sum()) * float((bm * bm).sum()))
    if denom == 0.0:
        return 0.0
    return float((am * bm).sum() / denom)


def _indep_lag(values, lag: int) -> float:
    arr = np.asarray(values, dtype=np.float64)
    if arr.ndim != 1:
        arr = arr.reshape(arr.shape[0], -1).mean(axis=1)
    a = arr[:-lag]
    b = arr[lag:]
    if float(np.std(a)) <= 1e-12 or float(np.std(b)) <= 1e-12:
        return 0.0
    return _indep_pearson(a, b)


def _repro_rtn(seed: int, n: int, gamma: float) -> np.ndarray:
    """From-scratch RNG replay of _sample_rtn_states (same seeded call pattern)."""
    rng = np.random.default_rng(int(seed))
    p = _indep_flip_prob(gamma)
    s = np.empty(n, dtype=np.int8)
    s[0] = 1 if rng.random() < 0.5 else -1
    for t in range(1, n):
        s[t] = -s[t - 1] if rng.random() < p else s[t - 1]
    return s


def _repro_storm_hidden(source: TemporalStormSPPSource, seed: int, n: int, site_count: int):
    """From-scratch RNG replay of the two-state HMM latent chain in
    TemporalStormSPPSource.sample (init from the stationary law, then per-cycle flips)."""
    rng = np.random.default_rng(int(seed))
    a, b = float(source.a), float(source.b)
    pi = np.asarray([b / (a + b), a / (a + b)], dtype=np.float64)   # independent stationary
    shape1 = site_count if source.scope == "per_site" else 1
    hidden = np.empty((n, shape1), dtype=np.int8)
    hidden[0, :] = rng.choice(2, size=shape1, p=pi)
    for t in range(1, n):
        prev = hidden[t - 1]
        flip_up = (prev == 0) & (rng.random(prev.shape) < a)
        flip_down = (prev == 1) & (rng.random(prev.shape) < b)
        cur = np.array(prev, copy=True)
        cur[flip_up] = 1
        cur[flip_down] = 0
        hidden[t] = cur
    return hidden


def _mk_timeline(payload, latent=None, *, seed=0, mode="shared", metadata=None,
                 n=None, cycle_time_ns=1000.0, name="t"):
    p = {k: np.asarray(v) for k, v in payload.items()}
    n = n if n is not None else next(iter(p.values())).shape[0]
    return SourceTimeline(name=name, n_cycles=n, cycle_time_ns=cycle_time_ns,
                          payload=p, latent=dict(latent or {}), metadata=dict(metadata or {}),
                          seed=seed, coupling_mode=mode)


#: a NON-default coupling config (z_scale + gamma_phi sensitivity both differ from the default),
#: so a mutant that swaps ``config`` for None/default in the fan-out diverges on gamma_phi etc.
_CFG = SourceCouplingConfig(z_scale_radns=2.0e-4, gamma_phi_sensitivity=0.5)


# =========================================================================== #
# lag_autocorrelation                                                          #
# =========================================================================== #
def test_L0_lag_autocorrelation_value_and_all_branches():
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 4.0, 3.0, 2.0])
    assert_pins(lag_autocorrelation(x, lag=1), _indep_lag(x, 1), label="lag ac1")
    assert_pins(lag_autocorrelation(x, lag=2), _indep_lag(x, 2), label="lag ac2")
    # ndim != 1 -> row-mean reduction branch
    x2 = np.array([[1.0, 3.0], [2.0, 2.0], [3.0, 1.0], [4.0, 0.0], [5.0, -1.0]])
    assert_pins(lag_autocorrelation(x2, lag=1), _indep_lag(x2, 1), label="lag 2d")
    # constant -> std<=NUMERICAL_ZERO -> 0.0
    assert lag_autocorrelation(np.ones(6), lag=1) == 0.0
    # default lag == 1 (exercises the default arg, not just explicit lags)
    assert_pins(lag_autocorrelation(x), _indep_lag(x, 1), label="default lag")
    # too short: size == lag is still too short (boundary: the guard is <=, not <)
    _raises_exact(ValueError, "not enough samples for requested lag",
                  lambda: lag_autocorrelation(np.array([1.0, 2.0, 3.0]), lag=3))
    _raises_exact(ValueError, "not enough samples for requested lag",
                  lambda: lag_autocorrelation(np.array([1.0, 2.0]), lag=3))
    # lag must be a positive integer
    _raises_exact(ValueError, "lag must be a positive integer, got 0",
                  lambda: lag_autocorrelation(x, lag=0))


def test_KILLER_lag_autocorrelation_discriminates():
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 4.0, 3.0, 2.0])

    def prop(vals):
        assert_pins(lag_autocorrelation(vals, lag=1), _indep_lag(x, 1), label="lag")

    # a lag-2-shifted signal has a genuinely different lag-1 autocorrelation
    assert_discriminates(prop, x, x[::-1] * 2.0 + np.arange(x.size), label="lag autocorr")


@settings(max_examples=150, deadline=None)
@given(vals=st.lists(st.floats(-5.0, 5.0, allow_nan=False, allow_infinity=False),
                     min_size=4, max_size=20), lag=st.integers(1, 3))
def test_L1_lag_autocorrelation_matches_independent_and_in_range(vals, lag):
    arr = np.asarray(vals, dtype=np.float64)
    if arr.size <= lag:
        return
    got = lag_autocorrelation(arr, lag=lag)
    assert -1.0 - 1e-9 <= got <= 1.0 + 1e-9
    assert_pins(got, _indep_lag(arr, lag), label="lag ac")


# =========================================================================== #
# timeline_to_coupled_params                                                   #
# =========================================================================== #
def test_L0_timeline_to_coupled_params_shared_and_independent():
    # NON-default config threaded through -> a mutant that drops/None-s config diverges on gamma_phi.
    src = RTNSource(amplitude_radns=1.0e-4, gamma_per_cycle=0.1)
    timeline = src.sample(seed=31, n_cycles=64)
    # shared branch
    shared = timeline_to_coupled_params(timeline, _CFG)
    ref = trajectory_to_params(timeline.payload_series("z_radns"), _CFG)
    assert {p.coupling_mode for p in shared} == {"shared"}
    assert [p.to_manifest() for p in shared] == [p.to_manifest() for p in ref]
    # the config is load-bearing: the default fan-out differs on gamma_phi_per_ns
    assert (shared[0].gamma_phi_per_ns
            != trajectory_to_params(timeline.payload_series("z_radns"))[0].gamma_phi_per_ns)
    # independent branch, explicit seed
    baseline = timeline.independent_baseline(seed=32)
    z = baseline.payload_series("z_radns")
    indep = timeline_to_coupled_params(baseline, _CFG, independent_seed=77)
    ref_i = independent_baseline_trajectory_to_params(z, _CFG, seed=77)
    assert {p.coupling_mode for p in indep} == {"independent"}
    assert [p.to_manifest() for p in indep] == [p.to_manifest() for p in ref_i]


def test_L0_timeline_to_coupled_params_independent_seed_fallbacks():
    z = np.linspace(-1e-4, 1e-4, 8)
    # (a) seed=None -> metadata['baseline_seed'] wins over timeline.seed (they DIFFER here, so a
    #     mutant that reads the wrong key / drops the fallback resolves the wrong seed).
    t_marker = _mk_timeline({"z_radns": z}, mode="independent", seed=999,
                            metadata={"baseline_seed": 7})
    got = timeline_to_coupled_params(t_marker, _CFG)
    ref = independent_baseline_trajectory_to_params(z, _CFG, seed=7)
    assert [p.to_manifest() for p in got] == [p.to_manifest() for p in ref]
    # and it is NOT the timeline.seed fallback (proves baseline_seed was actually read)
    assert [p.to_manifest() for p in got] != [
        p.to_manifest() for p in independent_baseline_trajectory_to_params(z, _CFG, seed=999)]
    # (b) seed=None, no baseline_seed marker, timeline.seed present -> timeline.seed
    t_seed = _mk_timeline({"z_radns": z}, mode="independent", seed=13)
    got_b = timeline_to_coupled_params(t_seed, _CFG)
    ref_b = independent_baseline_trajectory_to_params(z, _CFG, seed=13)
    assert [p.to_manifest() for p in got_b] == [p.to_manifest() for p in ref_b]
    # (c) seed=None, no baseline_seed, timeline.seed None -> 0
    t_none = _mk_timeline({"z_radns": z}, mode="independent", seed=None)
    got_c = timeline_to_coupled_params(t_none, _CFG)
    ref_c = independent_baseline_trajectory_to_params(z, _CFG, seed=0)
    assert [p.to_manifest() for p in got_c] == [p.to_manifest() for p in ref_c]


def test_L0_timeline_to_coupled_params_rejects_non_1d_payload():
    t2d = _mk_timeline({"z_radns": np.zeros((4, 2))})
    _raises_exact(ValueError, "payload 'z_radns' must be 1-D to feed SourceCouplingConfig",
                  lambda: timeline_to_coupled_params(t2d))


# =========================================================================== #
# timeline_to_site_coupled_params                                             #
# =========================================================================== #
def test_L0_timeline_to_site_coupled_params_shared_and_independent():
    z = np.array([[1e-5, -2e-5, 3e-5], [-1e-5, 2e-5, -3e-5]], dtype=np.float64)  # (cycle, site)
    # shared: each site's full param bundle == the per-site trajectory fan-out at the SAME config
    shared = timeline_to_site_coupled_params(_mk_timeline({"detuning_radns": z}), _CFG)
    assert len(shared) == 2 and len(shared[0]) == 3
    for s_ in range(3):
        ref = trajectory_to_params(z[:, s_], _CFG)
        for c in range(2):
            assert shared[c][s_].to_manifest() == ref[c].to_manifest()
            assert shared[c][s_].coupling_mode == "shared"
    # independent: each site permuted with seed base+site
    tind = _mk_timeline({"detuning_radns": z}, mode="independent", seed=4)
    got = timeline_to_site_coupled_params(tind, _CFG, independent_seed=100)
    for s_ in range(3):
        ref = independent_baseline_trajectory_to_params(z[:, s_], _CFG, seed=100 + s_)
        for c in range(2):
            assert got[c][s_].to_manifest() == ref[c].to_manifest()


def test_L0_timeline_to_site_coupled_params_independent_seed_fallbacks():
    z = np.array([[1e-5, -2e-5], [-1e-5, 2e-5], [3e-5, -3e-5]], dtype=np.float64)
    # (a) baseline_seed marker present -> used as the per-site base seed
    tmark = _mk_timeline({"detuning_radns": z}, mode="independent", seed=None,
                         metadata={"baseline_seed": 21})
    got = timeline_to_site_coupled_params(tmark, _CFG)
    for s_ in range(2):
        ref = independent_baseline_trajectory_to_params(z[:, s_], _CFG, seed=21 + s_)
        for c in range(3):
            assert got[c][s_].to_manifest() == ref[c].to_manifest()
    # (b) no baseline_seed, timeline.seed present -> per-site base = timeline.seed (+site)
    tseed = _mk_timeline({"detuning_radns": z}, mode="independent", seed=5)
    got_b = timeline_to_site_coupled_params(tseed, _CFG)
    for s_ in range(2):
        ref = independent_baseline_trajectory_to_params(z[:, s_], _CFG, seed=5 + s_)
        for c in range(3):
            assert got_b[c][s_].to_manifest() == ref[c].to_manifest()
    # (c) no baseline_seed, timeline.seed None -> per-site base = 0 (+site)
    tnone = _mk_timeline({"detuning_radns": z}, mode="independent", seed=None)
    got_c = timeline_to_site_coupled_params(tnone, _CFG)
    for s_ in range(2):
        ref = independent_baseline_trajectory_to_params(z[:, s_], _CFG, seed=0 + s_)
        for c in range(3):
            assert got_c[c][s_].to_manifest() == ref[c].to_manifest()


def test_L0_timeline_to_site_coupled_params_rejects_non_2d_payload():
    t1d = _mk_timeline({"detuning_radns": np.zeros(4)})
    _raises_exact(ValueError, "payload 'detuning_radns' must be 2-D with shape (cycle, site)",
                  lambda: timeline_to_site_coupled_params(t1d))


# =========================================================================== #
# SourceTimeline.__post_init__ + payload_series/latent_series                  #
# =========================================================================== #
def test_L0_source_timeline_post_init_validation():
    # valid construction coerces payload/latent to copies
    tl = _mk_timeline({"z": np.array([1.0, 2.0])}, latent={"s": np.array([1, 0])})
    assert tl.n_cycles == 2 and tl.cycle_time_ns == 1000.0
    # bad coupling_mode
    _raises_exact(ValueError, "coupling_mode must be 'shared' or 'independent', got 'sideways'",
                  lambda: SourceTimeline(name="t", n_cycles=2, cycle_time_ns=1.0,
                                         payload={"z": np.array([1.0, 2.0])},
                                         coupling_mode="sideways"))
    # non-positive n_cycles (via _require_positive_int)
    _raises_exact(ValueError, "n_cycles must be a positive integer, got 0",
                  lambda: SourceTimeline(name="t", n_cycles=0, cycle_time_ns=1.0, payload={}))
    # non-positive cycle_time_ns
    _raises_exact(ValueError, "cycle_time_ns must be > 0, got 0.0",
                  lambda: SourceTimeline(name="t", n_cycles=1, cycle_time_ns=0.0, payload={}))
    # payload wrong cycle axis
    _raises_exact(ValueError, "payload['z'] must have cycle axis length 2",
                  lambda: SourceTimeline(name="t", n_cycles=2, cycle_time_ns=1.0,
                                         payload={"z": np.array([1.0])}))


def test_L0_payload_and_latent_series_copy_and_missing():
    tl = _mk_timeline({"z": np.array([1.0, 2.0, 3.0])}, latent={"s": np.array([1, -1, 1])})
    z = tl.payload_series("z")
    assert z.tolist() == [1.0, 2.0, 3.0]
    z[0] = 999.0                                  # returned array is a COPY
    assert tl.payload_series("z")[0] == 1.0
    s = tl.latent_series("s")
    assert s.tolist() == [1, -1, 1]
    s[0] = 7
    assert tl.latent_series("s")[0] == 1
    _raises_exact(KeyError, "'nope'", lambda: tl.payload_series("nope"))
    _raises_exact(KeyError, "'nope'", lambda: tl.latent_series("nope"))


def test_KILLER_payload_series_is_a_copy():
    tl = _mk_timeline({"z": np.array([1.0, 2.0, 3.0])})

    def prop(series_fn):
        got = series_fn("z")
        got += 100.0
        assert tl.payload_series("z").tolist() == [1.0, 2.0, 3.0]

    # wrong = an aliasing accessor that hands back the internal array (mutation copy=False)
    class _Aliasing:
        def __call__(self, key):
            return tl.payload[key]

    assert_discriminates(prop, tl.payload_series, _Aliasing(), label="payload_series copy")


# =========================================================================== #
# SourceTimeline.independent_baseline / per_field_independent_ablation         #
# =========================================================================== #
def test_L0_independent_baseline_row_preserving_and_metadata():
    base = _mk_timeline(
        {"a": np.arange(6.0), "b": np.arange(6.0) * 10.0, "c": np.arange(6.0) * 100.0},
        seed=1, metadata={"origin": "x"})
    # permute only a subset of keys; the shared permutation preserves same-cycle alignment
    out = base.independent_baseline(seed=3, payload_keys=("a", "b"))
    perm = np.random.default_rng(3).permutation(6)
    np.testing.assert_array_equal(out.payload_series("a"), np.arange(6.0)[perm])
    np.testing.assert_array_equal(out.payload_series("b"), (np.arange(6.0) * 10.0)[perm])
    np.testing.assert_array_equal(out.payload_series("c"), np.arange(6.0) * 100.0)  # untouched
    # a and b keep their SAME-CYCLE ratio (row-preserving): b == 10*a
    np.testing.assert_allclose(out.payload_series("b"), 10.0 * out.payload_series("a"))
    assert out.coupling_mode == "independent" and out.latent == {}
    md = out.metadata
    assert md["baseline_of"] == "t" and md["baseline_seed"] == 3
    assert md["baseline"] == "matched_marginal_row_preserving_cycle_permutation"
    assert md["permuted_payload_keys"] == ["a", "b"] and md["origin"] == "x"
    assert out.seed == 3
    # default payload_keys=None -> all keys permuted (still one shared permutation)
    out_all = base.independent_baseline(seed=3)
    np.testing.assert_allclose(out_all.payload_series("b"), 10.0 * out_all.payload_series("a"))
    np.testing.assert_allclose(out_all.payload_series("c"), 100.0 * out_all.payload_series("a"))
    # unknown key (KeyError stringifies as repr of its message)
    _raises_exact(KeyError, repr("unknown payload keys for baseline: ['zz']"),
                  lambda: base.independent_baseline(seed=3, payload_keys=("zz",)))


def test_L0_per_field_independent_ablation_breaks_cross_field_alignment():
    base = _mk_timeline({"a": np.arange(8.0), "b": np.arange(8.0) * 10.0}, seed=1)
    out = base.per_field_independent_ablation(seed=4)
    # each field gets its OWN permutation -> marginals preserved, cross-field alignment destroyed
    np.testing.assert_allclose(np.sort(out.payload_series("a")), np.arange(8.0))
    np.testing.assert_allclose(np.sort(out.payload_series("b")), np.arange(8.0) * 10.0)
    # independently reproduce the two per-field permutations from the SAME rng call order
    rng = np.random.default_rng(4)
    pa = np.arange(8.0)[rng.permutation(8)]
    pb = (np.arange(8.0) * 10.0)[rng.permutation(8)]
    np.testing.assert_array_equal(out.payload_series("a"), pa)
    np.testing.assert_array_equal(out.payload_series("b"), pb)
    md = out.metadata
    assert md["ablation_of"] == "t" and md["ablation_seed"] == 4
    assert md["ablation"] == "per_field_independent_cycle_permutation_unphysical"
    assert md["permuted_payload_keys"] == ["a", "b"]
    assert out.coupling_mode == "independent" and out.latent == {}
    # subset ablation: an unpermuted key is untouched
    out_sub = base.per_field_independent_ablation(seed=4, payload_keys=("a",))
    np.testing.assert_array_equal(out_sub.payload_series("b"), np.arange(8.0) * 10.0)
    _raises_exact(KeyError, repr("unknown payload keys for ablation: ['zz']"),
                  lambda: base.per_field_independent_ablation(seed=4, payload_keys=("zz",)))


def test_KILLER_independent_baseline_is_row_preserving():
    base = _mk_timeline({"a": np.arange(200.0), "b": np.arange(200.0) * 3.0}, seed=1)

    def prop(tl):
        # the row-preserving invariant: b == 3*a cycle-by-cycle after permutation
        np.testing.assert_allclose(tl.payload_series("b"), 3.0 * tl.payload_series("a"))

    real = base.independent_baseline(seed=3)
    wrong = base.per_field_independent_ablation(seed=3)   # per-field breaks the alignment
    assert_discriminates(prop, real, wrong, label="row-preserving baseline")


# =========================================================================== #
# SourceTimeline.to_manifest                                                   #
# =========================================================================== #
def test_L0_to_manifest_structure_and_seed_branches():
    tl = _mk_timeline({"z": np.array([1.0, 2.0, 4.0])}, latent={"s": np.array([1, 0, 1])},
                      seed=7, metadata={"k": "v"})
    m = tl.to_manifest()
    assert m["schema"] == "error_coupling_simulator.source.timeline.v1"
    assert m["name"] == "t" and m["n_cycles"] == 3 and m["cycle_time_ns"] == 1000.0
    assert m["seed"] == 7 and m["coupling_mode"] == "shared" and m["metadata"] == {"k": "v"}
    # payload summary carries independently recomputed stats + sha256
    zs = m["payload"]["z"]
    assert zs["shape"] == [3] and zs["dtype"] == "float64"
    assert zs["min"] == 1.0 and zs["max"] == 4.0
    assert zs["mean"] == pytest.approx(7.0 / 3.0) and zs["sha256"] == sp._array_sha256(np.array([1.0, 2.0, 4.0]))
    assert m["latent"]["s"]["shape"] == [3]
    # seed None branch
    assert _mk_timeline({"z": np.array([1.0])}, seed=None).to_manifest()["seed"] is None


def test_source_timeline_rejects_unsupported_schema():
    unsupported_schema = "error_coupling_simulator.source.timeline.v0"
    with pytest.raises(ValueError, match="unsupported source timeline schema"):
        SourceTimeline(
            name="unsupported",
            n_cycles=1,
            cycle_time_ns=1.0,
            payload={"z": np.array([0.0])},
            schema=unsupported_schema,
        )


# =========================================================================== #
# SourceTimeline.save_npz / load_npz  (sha256 round-trip identity)             #
# =========================================================================== #
def test_L0_save_and_load_npz_round_trips_exact(tmp_path):
    tl = RTNSource(amplitude_radns=2e-4, gamma_per_cycle=0.2).sample(seed=22, n_cycles=48)
    path = tl.save_npz(tmp_path / "src.npz")
    loaded = SourceTimeline.load_npz(path)
    np.testing.assert_array_equal(loaded.payload_series("z_radns"), tl.payload_series("z_radns"))
    np.testing.assert_array_equal(loaded.latent_series("rtn_state"), tl.latent_series("rtn_state"))
    assert loaded.seed == tl.seed and loaded.coupling_mode == tl.coupling_mode
    assert (loaded.to_manifest()["payload"]["z_radns"]["sha256"]
            == tl.to_manifest()["payload"]["z_radns"]["sha256"])


def test_L0_load_npz_missing_manifest_raises(tmp_path):
    bad = tmp_path / "nomanifest.npz"
    np.savez_compressed(bad, payload_0=np.array([1.0, 2.0]))
    _raises_exact(ValueError, "source timeline NPZ missing __manifest_json__",
                  lambda: SourceTimeline.load_npz(bad))


def test_L0_load_npz_detects_tampered_array_hash(tmp_path):
    tl = RTNSource(amplitude_radns=2e-4, gamma_per_cycle=0.2).sample(seed=22, n_cycles=32)
    path = tl.save_npz(tmp_path / "src.npz")
    with np.load(path, allow_pickle=False) as data:
        arrays = {k: np.array(data[k], copy=True) for k in data.files}
    arrays["payload_0"][0] *= -1.0
    bad = tmp_path / "bad.npz"
    np.savez_compressed(bad, **arrays)
    with pytest.raises(ValueError, match="hash mismatch"):
        SourceTimeline.load_npz(bad)


def test_L0_load_npz_rejects_unsupported_schema(tmp_path):
    path = RTNSource().sample(seed=1, n_cycles=2).save_npz(tmp_path / "current.npz")
    with np.load(path, allow_pickle=False) as data:
        arrays = {key: np.array(data[key], copy=True) for key in data.files}
    manifest = json.loads(str(arrays["__manifest_json__"].item()))
    manifest["schema"] = "error_coupling_simulator.source.timeline.v0"
    arrays["__manifest_json__"] = np.asarray(json.dumps(manifest, sort_keys=True))
    unsupported = tmp_path / "unsupported.npz"
    np.savez_compressed(unsupported, **arrays)
    with pytest.raises(ValueError, match="unsupported source timeline schema"):
        SourceTimeline.load_npz(unsupported)


# =========================================================================== #
# SourceProcess.sample (abstract; body is a docstring only)                    #
# =========================================================================== #
def test_L0_source_process_sample_is_abstract_and_body_returns_none():
    assert getattr(SourceProcess.sample, "__isabstractmethod__", False) is True
    with pytest.raises(TypeError):
        SourceProcess()   # abstract class -- not instantiable

    class _Concrete(SourceProcess):
        def sample(self, *, seed, n_cycles, layout=None):
            return super().sample(seed=seed, n_cycles=n_cycles, layout=layout)

    assert _Concrete().sample(seed=1, n_cycles=2) is None   # abstract body executes -> None


# =========================================================================== #
# RTNSource -- __post_init__ / flip_probability / autocorr_base / sample        #
# =========================================================================== #
def test_L0_rtn_post_init_validation():
    RTNSource(amplitude_radns=0.0, gamma_per_cycle=0.0, cycle_time_ns=1.0)   # valid boundary
    _raises_exact(ValueError, "amplitude_radns must be >= 0, got -1.0",
                  lambda: RTNSource(amplitude_radns=-1.0))
    _raises_exact(ValueError, "gamma_per_cycle must be >= 0, got -0.5",
                  lambda: RTNSource(gamma_per_cycle=-0.5))
    _raises_exact(ValueError, "cycle_time_ns must be > 0, got 0.0",
                  lambda: RTNSource(cycle_time_ns=0.0))


def test_L0_rtn_flip_probability_and_autocorr_base_pins():
    for g in (0.0, 0.05, 0.25, 1.0):
        src = RTNSource(gamma_per_cycle=g)
        assert_pins(src.flip_probability, _indep_flip_prob(g), label=f"flip@{g}")
        assert_pins(src.autocorr_base, _indep_autocorr_base(g), label=f"ac@{g}")


def test_KILLER_rtn_flip_probability_discriminates():
    src = RTNSource(gamma_per_cycle=0.25)

    def prop(value):
        assert_pins(value, _indep_flip_prob(0.25), label="flip")

    # a wrong-factor variant (the classic exp(-gamma) vs exp(-2 gamma) sabotage)
    assert_discriminates(prop, src.flip_probability, 0.5 * (1.0 - math.exp(-0.25)),
                         label="rtn flip probability")


@settings(max_examples=200, deadline=None)
@given(g=st.floats(0.0, 5.0, allow_nan=False, allow_infinity=False))
def test_L1_rtn_closed_forms(g):
    src = RTNSource(gamma_per_cycle=g)
    assert_pins(src.flip_probability, _indep_flip_prob(g), label="flip")
    assert_pins(src.autocorr_base, _indep_autocorr_base(g), label="ac")


def test_L0_rtn_sample_replayable_and_amplitude_pin():
    A, g = 2.0e-4, 0.25
    src = RTNSource(amplitude_radns=A, gamma_per_cycle=g)
    a = src.sample(seed=7, n_cycles=64)
    b = src.sample(seed=7, n_cycles=64)
    np.testing.assert_array_equal(a.payload_series("z_radns"), b.payload_series("z_radns"))
    states = a.latent_series("rtn_state")
    # INDEPENDENT: the latent telegraph is the seeded replay; z == A * states
    np.testing.assert_array_equal(states, _repro_rtn(7, 64, g))
    np.testing.assert_array_equal(a.payload_series("z_radns"), A * states.astype(np.float64))
    assert set(np.unique(a.payload_series("z_radns"))) <= {-A, A}
    # FULL metadata VALUE-PIN (independent) -- kills every key/value mutation
    md = a.metadata
    assert set(md) == {"source", "value_provenance", "amplitude_radns", "gamma_per_cycle", "flip_probability",
                       "autocorr_base", "layout_site_count"}
    assert md["source"] == "RTNSource"
    assert md["value_provenance"] == {
        "parameter_values": "project-design",
        "claims_hardware_calibration": False,
    }
    assert md["amplitude_radns"] == pytest.approx(A) and md["gamma_per_cycle"] == pytest.approx(g)
    assert md["flip_probability"] == pytest.approx(_indep_flip_prob(g))
    assert md["autocorr_base"] == pytest.approx(_indep_autocorr_base(g))
    assert md["layout_site_count"] == 1
    # layout overrides the default site count in metadata
    assert src.sample(seed=1, n_cycles=4, layout=5).metadata["layout_site_count"] == 5
    # n_cycles must be a positive integer
    _raises_exact(ValueError, "n_cycles must be an integer, got 3.9",
                  lambda: src.sample(seed=1, n_cycles=3.9))


def test_KILLER_rtn_sample_amplitude_map_discriminates():
    A, g = 2.0e-4, 0.25
    a = RTNSource(amplitude_radns=A, gamma_per_cycle=g).sample(seed=7, n_cycles=64)
    states = a.latent_series("rtn_state")

    def prop(z):
        np.testing.assert_array_equal(z, A * states.astype(np.float64))

    assert_discriminates(prop, a.payload_series("z_radns"), states.astype(np.float64) * (A / 2.0),
                         label="rtn amplitude map")


# =========================================================================== #
# OneOverFDriftSource -- __post_init__ / gammas / amplitudes / analytic_psd / sample #
# =========================================================================== #
def test_L0_one_over_f_post_init_validation():
    OneOverFDriftSource(amplitude_radns=0.0)   # valid boundary
    _raises_exact(ValueError, "amplitude_radns must be >= 0, got -1.0",
                  lambda: OneOverFDriftSource(amplitude_radns=-1.0))
    _raises_exact(ValueError, "n_fluctuators must be a positive integer, got 0",
                  lambda: OneOverFDriftSource(n_fluctuators=0))
    _raises_exact(ValueError, "gamma_min_per_cycle must be > 0, got 0.0",
                  lambda: OneOverFDriftSource(gamma_min_per_cycle=0.0))
    _raises_exact(ValueError, "gamma_max_per_cycle must be > 0, got 0.0",
                  lambda: OneOverFDriftSource(gamma_max_per_cycle=0.0))
    _raises_exact(ValueError, "gamma_max_per_cycle must be >= gamma_min_per_cycle",
                  lambda: OneOverFDriftSource(gamma_min_per_cycle=0.5, gamma_max_per_cycle=0.1))
    _raises_exact(ValueError, "cycle_time_ns must be > 0, got 0.0",
                  lambda: OneOverFDriftSource(cycle_time_ns=0.0))


def test_L0_one_over_f_gammas_and_amplitudes_pins():
    src = OneOverFDriftSource(amplitude_radns=3.0e-4, n_fluctuators=6,
                             gamma_min_per_cycle=0.005, gamma_max_per_cycle=0.5)
    assert_pins(src.gammas_per_cycle, _indep_geomspace(0.005, 0.5, 6), rtol=1e-12, atol=1e-15,
                label="gammas")
    assert_pins(src.amplitudes_radns, _indep_amps(src), label="amplitudes")
    # single-fluctuator edge (geomspace of length 1)
    one = OneOverFDriftSource(n_fluctuators=1, gamma_min_per_cycle=0.02, gamma_max_per_cycle=0.02)
    assert_pins(one.gammas_per_cycle, np.array([0.02]), label="gammas n=1")


def test_L0_one_over_f_analytic_psd_value_and_nonfinite_guard():
    src = OneOverFDriftSource(amplitude_radns=3.0e-4, n_fluctuators=6,
                             gamma_min_per_cycle=0.005, gamma_max_per_cycle=0.5)
    omega = np.array([0.01, 0.1, 1.0])
    assert_pins(src.analytic_psd(omega), _indep_psd(src, omega), rtol=1e-10, atol=0.0, label="psd")
    # low-frequency PSD exceeds high-frequency (1/f rolloff)
    psd = src.analytic_psd(omega)
    assert psd[0] > psd[-1] and np.all(psd > 0.0)
    _raises_exact(ValueError, "omega_per_cycle contains non-finite values",
                  lambda: src.analytic_psd(np.array([0.1, np.inf])))


def test_KILLER_one_over_f_analytic_psd_discriminates():
    src = OneOverFDriftSource(amplitude_radns=3.0e-4, n_fluctuators=6,
                             gamma_min_per_cycle=0.005, gamma_max_per_cycle=0.5)
    omega = np.array([0.01, 0.1, 1.0])

    def prop(psd):
        assert_pins(psd, _indep_psd(src, omega), rtol=1e-10, atol=0.0, label="psd")

    # a wrong-exponent Lorentzian (omega instead of omega^2 in the denominator)
    g = _indep_geomspace(0.005, 0.5, 6)
    a = _indep_amps(src)
    wrong = np.zeros_like(omega)
    for gi, ai in zip(g, a):
        wrong += ai * ai * (4.0 * gi) / ((2.0 * gi) ** 2 + omega)
    assert_discriminates(prop, src.analytic_psd(omega), wrong, label="analytic PSD")


def test_L0_one_over_f_sample_shapes_and_matmul_pin():
    src = OneOverFDriftSource(amplitude_radns=3.0e-4, n_fluctuators=4,
                             gamma_min_per_cycle=0.01, gamma_max_per_cycle=0.3)
    tl = src.sample(seed=11, n_cycles=80)
    states = tl.latent_series("rtn_states")
    assert states.shape == (80, 4)
    assert tl.payload_series("z_radns").shape == (80,)
    # INDEPENDENT: z == states @ (A/sqrt(K)) amplitudes
    np.testing.assert_allclose(tl.payload_series("z_radns"),
                               states.astype(np.float64) @ _indep_amps(src))
    # replayability
    np.testing.assert_array_equal(tl.payload_series("z_radns"),
                                  src.sample(seed=11, n_cycles=80).payload_series("z_radns"))
    md = tl.metadata
    assert set(md) == {"source", "value_provenance", "amplitude_radns", "n_fluctuators", "gamma_min_per_cycle",
                       "gamma_max_per_cycle", "gammas_per_cycle", "amplitudes_radns",
                       "layout_site_count"}
    assert md["source"] == "OneOverFDriftSource" and md["n_fluctuators"] == 4
    assert md["value_provenance"] == {
        "parameter_values": "project-design",
        "claims_hardware_calibration": False,
    }
    np.testing.assert_allclose(md["gammas_per_cycle"], _indep_geomspace(0.01, 0.3, 4), rtol=1e-12)
    np.testing.assert_allclose(md["amplitudes_radns"], _indep_amps(src))
    assert md["layout_site_count"] == 1


def test_KILLER_one_over_f_sample_matmul_discriminates():
    src = OneOverFDriftSource(amplitude_radns=3.0e-4, n_fluctuators=4,
                             gamma_min_per_cycle=0.01, gamma_max_per_cycle=0.3)
    tl = src.sample(seed=11, n_cycles=40)
    states = tl.latent_series("rtn_states")

    def prop(z):
        np.testing.assert_allclose(z, states.astype(np.float64) @ _indep_amps(src))

    assert_discriminates(prop, tl.payload_series("z_radns"),
                         states.astype(np.float64) @ (_indep_amps(src) * 2.0),
                         label="one/f matmul")


# =========================================================================== #
# PhaseBurstSource -- __post_init__ / sample                                    #
# =========================================================================== #
def test_L0_phase_burst_post_init_validation():
    PhaseBurstSource(affected_sites=2, site_count=4)   # affected_sites-not-None branch
    _raises_exact(ValueError, "site_count must be a positive integer, got 0",
                  lambda: PhaseBurstSource(site_count=0))
    _raises_exact(ValueError, "peak_shift_mhz must be finite, got inf",
                  lambda: PhaseBurstSource(peak_shift_mhz=float("inf")))
    _raises_exact(ValueError, "peak_jitter_mhz must be >= 0, got -1.0",
                  lambda: PhaseBurstSource(peak_jitter_mhz=-1.0))
    _raises_exact(ValueError, "recovery_time_ns must be > 0, got 0.0",
                  lambda: PhaseBurstSource(recovery_time_ns=0.0))
    _raises_exact(ValueError, "echo_suppression must be in [0, 1]",
                  lambda: PhaseBurstSource(echo_suppression=1.5))
    _raises_exact(ValueError, "footprint must be 'uniform' or 'cluster'",
                  lambda: PhaseBurstSource(footprint="blob"))
    _raises_exact(ValueError, "affected_sites must be a positive integer, got 0",
                  lambda: PhaseBurstSource(affected_sites=0))


def test_L0_phase_burst_sample_closed_form_recovery_and_conversions():
    src = PhaseBurstSource(site_count=2, event_times=(0,), peak_shift_mhz=-2.0,
                           recovery_time_ns=2_000.0, cycle_time_ns=1_000.0,
                           phase_window_ns=1_000.0, echo_suppression=0.1, t1_duration_ns=2_500.0)
    tl = src.sample(seed=1, n_cycles=5)
    delta = tl.payload_series("delta_fq_mhz")
    # INDEPENDENT 1/(1+t/t_rec) recovery closed form
    elapsed = np.arange(5) * 1_000.0
    decay = 1.0 / (1.0 + elapsed / 2_000.0)
    np.testing.assert_allclose(delta[:, 0], -2.0 * decay)
    np.testing.assert_allclose(delta[:, 1], delta[:, 0])
    # MHz -> angular rad/ns; phase = detuning * window; echoed = phase * echo
    detuning = _TWO_PI * delta * 1.0e-3
    np.testing.assert_allclose(tl.payload_series("detuning_radns"), detuning)
    np.testing.assert_allclose(tl.payload_series("phase_rad"), detuning * 1_000.0)
    np.testing.assert_allclose(tl.payload_series("echoed_phase_rad"), detuning * 1_000.0 * 0.1)
    np.testing.assert_allclose(tl.payload_series("z_radns"), np.mean(detuning, axis=1))
    # t1_burst: ceil(2500/1000)=3 rounds hot
    np.testing.assert_allclose(tl.payload_series("t1_burst"),
                               np.array([[1, 1], [1, 1], [1, 1], [0, 0], [0, 0]], dtype=float))
    np.testing.assert_array_equal(tl.latent_series("event_start"),
                                  np.array([1, 0, 0, 0, 0], dtype=np.int8))
    md = tl.metadata
    assert set(md) == {"source", "event_times", "peak_shift_mhz", "peak_jitter_mhz",
                       "recovery_time_ns", "t1_duration_ns", "phase_window_ns",
                       "echo_suppression", "footprint", "site_count"}
    assert md["source"] == "PhaseBurstSource" and md["event_times"] == (0,)
    assert md["site_count"] == 2 and md["footprint"] == "uniform"


def test_L0_phase_burst_sample_branch_arcs():
    # (a) event time outside the horizon -> raise
    _raises_exact(ValueError, "event time 5 outside n_cycles=3",
                  lambda: PhaseBurstSource(event_times=(5,)).sample(seed=1, n_cycles=3))
    # (b) t1_cycles == 0 (t1_duration 0) -> the t1 branch is skipped, burst all zero
    no_t1 = PhaseBurstSource(event_times=(0,), t1_duration_ns=0.0, peak_shift_mhz=-1.0
                             ).sample(seed=1, n_cycles=3)
    np.testing.assert_array_equal(no_t1.payload_series("t1_burst"), np.zeros((3, 1)))
    # (c) t1_cycles > 0 but no site affected (peak 0 -> amp 0) -> np.any(affected) False
    no_aff = PhaseBurstSource(event_times=(0,), peak_shift_mhz=0.0, t1_duration_ns=2_000.0
                              ).sample(seed=1, n_cycles=3)
    np.testing.assert_array_equal(no_aff.payload_series("t1_burst"), np.zeros((3, 1)))
    np.testing.assert_array_equal(no_aff.payload_series("delta_fq_mhz"), np.zeros((3, 1)))
    # (d) a happy multi-event run (t0 > 0 exercised) with two events
    two = PhaseBurstSource(site_count=1, event_times=(0, 2), peak_shift_mhz=-1.0,
                           recovery_time_ns=1_000.0).sample(seed=1, n_cycles=4)
    np.testing.assert_array_equal(two.latent_series("event_start"),
                                  np.array([1, 0, 1, 0], dtype=np.int8))
    # negative event time is rejected by the nonneg-int guard (in _event_times)
    _raises_exact(ValueError, "event_times[0] must be a non-negative integer, got -1",
                  lambda: PhaseBurstSource(event_times=(-1,)).sample(seed=1, n_cycles=4))


def test_L0_phase_burst_cluster_footprint_and_jitter():
    # cluster footprint restricted to affected_sites; jitter>0 exercises the jitter branch
    src = PhaseBurstSource(site_count=8, event_times=(1,), footprint="cluster", affected_sites=3,
                           peak_shift_mhz=-1.0, peak_jitter_mhz=0.2, recovery_time_ns=1_000.0)
    tl = src.sample(seed=5, n_cycles=3)
    delta = tl.payload_series("delta_fq_mhz")
    assert np.count_nonzero(delta[1]) == 3
    assert np.count_nonzero(delta[0]) == 0
    # cluster footprint honours layout coordinates
    layout = {"site_count": 4, "cluster_center": 0,
              "qubit_coords": {"0": [0.0, 0.0], "1": [10.0, 0.0], "2": [0.0, 1.0], "3": [10.0, 1.0]}}
    tl2 = PhaseBurstSource(site_count=4, event_times=(0,), footprint="cluster", affected_sites=2,
                           peak_shift_mhz=-1.0).sample(seed=5, n_cycles=2, layout=layout)
    assert set(np.flatnonzero(tl2.payload_series("delta_fq_mhz")[0])) == {0, 2}
    np.testing.assert_array_equal(tl2.latent_series("event_site_mask")[0],
                                  np.array([1, 0, 1, 0], dtype=np.int8))


def test_KILLER_phase_burst_recovery_discriminates():
    src = PhaseBurstSource(site_count=1, event_times=(0,), peak_shift_mhz=-2.0,
                           recovery_time_ns=2_000.0, cycle_time_ns=1_000.0)
    tl = src.sample(seed=1, n_cycles=5)
    elapsed = np.arange(5) * 1_000.0
    real = tl.payload_series("delta_fq_mhz")[:, 0]

    def prop(d):
        np.testing.assert_allclose(d, -2.0 / (1.0 + elapsed / 2_000.0))

    # exponential recovery (the physically-wrong sabotage the module deliberately avoids)
    wrong = -2.0 * np.exp(-elapsed / 2_000.0)
    assert_discriminates(prop, real, wrong, label="phase-burst recovery law")


# =========================================================================== #
# TemporalStormSPPSource -- __post_init__ + closed-form properties              #
# =========================================================================== #
def test_L0_temporal_storm_post_init_validation():
    TemporalStormSPPSource(scope="cluster", affected_sites=2, site_count=4)  # affected-not-None
    _raises_exact(ValueError, "a + b must be < 1 for positive correlation length",
                  lambda: TemporalStormSPPSource(a=0.6, b=0.5))
    _raises_exact(ValueError, "q_calm must sum to 1, got 0.9",
                  lambda: TemporalStormSPPSource(q_calm=(0.9, 0.0, 0.0, 0.0)))
    _raises_exact(ValueError, "scope must be 'global', 'cluster', or 'per_site'",
                  lambda: TemporalStormSPPSource(scope="galaxy"))
    _raises_exact(ValueError, "site_count must be a positive integer, got 0",
                  lambda: TemporalStormSPPSource(site_count=0))
    _raises_exact(ValueError, "affected_sites must be a positive integer, got 0",
                  lambda: TemporalStormSPPSource(affected_sites=0))
    _raises_exact(ValueError, "cycle_time_ns must be > 0, got 0.0",
                  lambda: TemporalStormSPPSource(cycle_time_ns=0.0))


def test_L0_temporal_storm_transition_and_stationary_and_correlation():
    src = TemporalStormSPPSource(a=0.03, b=0.07)
    P = src.transition_matrix
    assert_pins(P, np.array([[0.97, 0.03], [0.07, 0.93]]), label="transition")
    assert_row_stochastic(P, label="transition")
    pi = src.stationary_distribution
    assert_pins(pi, np.array([0.7, 0.3]), label="stationary")
    # pi is the LEFT eigenvector: pi @ P == pi (independently checked)
    np.testing.assert_allclose(pi @ P, pi)
    assert_pins(src.correlation_length_cycles, -1.0 / math.log(1.0 - 0.03 - 0.07),
                label="corr length")
    # degenerate a=b=0: denom<=0 -> [1,0]; lam2=1 -> inf correlation length
    deg = TemporalStormSPPSource(a=0.0, b=0.0)
    assert_pins(deg.stationary_distribution, np.array([1.0, 0.0]), label="deg stationary")
    assert deg.correlation_length_cycles == math.inf


def test_L0_temporal_storm_marginal_distribution():
    src = TemporalStormSPPSource(a=0.03, b=0.07, q_calm=(0.99, 0.005, 0.003, 0.002),
                                 q_storm=(0.7, 0.1, 0.1, 0.1))
    pi = np.array([0.7, 0.3])
    expected = pi[0] * np.array(src.q_calm) + pi[1] * np.array(src.q_storm)
    assert_pins(src.marginal_distribution, expected, label="marginal")
    assert_prob_dist(src.marginal_distribution, label="marginal")


def test_KILLER_temporal_storm_stationary_discriminates():
    src = TemporalStormSPPSource(a=0.03, b=0.07)
    P = src.transition_matrix

    def prop(pi):
        np.testing.assert_allclose(pi @ P, pi)   # left-eigenvector property

    assert_discriminates(prop, src.stationary_distribution, np.array([0.3, 0.7]),
                         label="stationary left-eigenvector")


@settings(max_examples=150, deadline=None)
@given(a=st.floats(0.0, 0.45, allow_nan=False), b=st.floats(0.0, 0.45, allow_nan=False))
def test_L1_temporal_storm_transition_and_marginal_properties(a, b):
    if a + b >= 1.0:
        return
    src = TemporalStormSPPSource(a=a, b=b)
    assert_row_stochastic(src.transition_matrix, label="P")
    pi = src.stationary_distribution
    np.testing.assert_allclose(pi @ src.transition_matrix, pi, atol=1e-9)
    assert_prob_dist(src.marginal_distribution, label="marginal")


def test_L0_from_fixed_marginal_holds_marginal_and_reconstructs():
    marginal = (0.9, 0.04, 0.03, 0.03)
    q_storm = (0.7, 0.1, 0.1, 0.1)
    pi1, xi = 0.2, 4.0
    src = TemporalStormSPPSource.from_fixed_marginal(
        marginal=marginal, q_storm=q_storm, storm_probability=pi1, correlation_length_cycles=xi)
    # the emitted one-cycle marginal equals the requested marginal
    np.testing.assert_allclose(src.marginal_distribution, marginal)
    # INDEPENDENT reconstruction of the member parameters
    s = 1.0 - math.exp(-1.0 / xi)
    q0 = tuple((p_i - pi1 * q_i) / (1.0 - pi1) for p_i, q_i in zip(marginal, q_storm))
    assert_pins(src.a, pi1 * s, label="a")
    assert_pins(src.b, (1.0 - pi1) * s, label="b")
    assert_pins(np.array(src.q_calm), np.array(q0), label="q_calm")
    assert_pins(np.array(src.q_storm), np.array(q_storm), label="q_storm")
    # a longer correlation length keeps the same marginal but larger memory
    slow = TemporalStormSPPSource.from_fixed_marginal(
        marginal=marginal, q_storm=q_storm, storm_probability=pi1, correlation_length_cycles=20.0)
    np.testing.assert_allclose(slow.marginal_distribution, marginal)
    assert slow.correlation_length_cycles > src.correlation_length_cycles


def test_L0_from_fixed_marginal_storm_probability_ge_one_rejected():
    """storm_probability>=1 is rejected by _validate_probability(allow_zero=False), which requires
    (0, 1) and is now the SOLE owner of that bound -- the previously-redundant downstream
    ``if pi1 >= 1.0`` guard (structurally unreachable given this validator) was removed as dead code."""
    _raises_exact(ValueError, "storm_probability must be in (0, 1), got 1.0",
                  lambda: TemporalStormSPPSource.from_fixed_marginal(
                      marginal=(0.25, 0.25, 0.25, 0.25), q_storm=(0.25, 0.25, 0.25, 0.25),
                      storm_probability=1.0, correlation_length_cycles=5.0))


def test_L0_from_fixed_marginal_rejects_infeasible_implied_calm():
    # marginal below pi1*q_storm on the X channel so the implied q_calm goes negative;
    # values are binary-exact (q0[1] = (0.25 - 0.5*0.75)/0.5 = -0.25) so the repr is clean.
    _raises_exact(ValueError, "implied q_calm[1] must be in [0, 1], got -0.25",
                  lambda: TemporalStormSPPSource.from_fixed_marginal(
                      marginal=(0.5, 0.25, 0.15, 0.1), q_storm=(0.1, 0.75, 0.1, 0.05),
                      storm_probability=0.5, correlation_length_cycles=5.0))


# =========================================================================== #
# TemporalStormSPPSource.sample -- scope arcs + deterministic chain/emission    #
# =========================================================================== #
def test_L0_temporal_storm_sample_global_deterministic_chain():
    # degenerate emissions (calm->I=0, storm->X=1) make emissions == storm indicator exactly,
    # and the seeded chain is reproduced from scratch -> pins init + flip logic + scope=global.
    src = TemporalStormSPPSource(a=0.3, b=0.3, q_calm=(1.0, 0.0, 0.0, 0.0),
                                 q_storm=(0.0, 1.0, 0.0, 0.0), site_count=1, scope="global")
    tl = src.sample(seed=17, n_cycles=40)
    hidden = _repro_storm_hidden(src, 17, 40, 1)
    np.testing.assert_array_equal(tl.latent_series("storm_state"), hidden)
    np.testing.assert_array_equal(tl.payload_series("storm_indicator"), hidden.astype(np.float64))
    np.testing.assert_array_equal(tl.payload_series("pauli_error"), hidden.astype(np.int8))
    np.testing.assert_array_equal(tl.payload_series("cluster_mask"), np.ones((40, 1), dtype=np.int8))
    # replayability
    np.testing.assert_array_equal(tl.payload_series("pauli_error"),
                                  src.sample(seed=17, n_cycles=40).payload_series("pauli_error"))
    # metadata VALUE-PIN
    md = tl.metadata
    assert md["source"] == "TemporalStormSPPSource" and md["scope"] == "global"
    assert md["a"] == pytest.approx(0.3) and md["b"] == pytest.approx(0.3)
    assert md["pauli_order"] == _PAULI_ORDER
    assert md["boundary"] == "reduced_pauli_comparator_not_analog_truth"
    np.testing.assert_allclose(md["transition_matrix"], src.transition_matrix.tolist())
    np.testing.assert_allclose(md["stationary_distribution"], src.stationary_distribution.tolist())


def test_L0_temporal_storm_sample_per_site_and_cluster_scopes():
    # per_site: independent chains per site (hidden shape (n, site_count))
    src = TemporalStormSPPSource(a=0.3, b=0.3, q_calm=(1.0, 0.0, 0.0, 0.0),
                                 q_storm=(0.0, 1.0, 0.0, 0.0), site_count=3, scope="per_site")
    tl = src.sample(seed=23, n_cycles=30)
    hidden = _repro_storm_hidden(src, 23, 30, 3)
    np.testing.assert_array_equal(tl.latent_series("storm_state"), hidden)
    np.testing.assert_array_equal(tl.payload_series("cluster_mask"), np.ones((30, 3), dtype=np.int8))
    # cluster scope: only the layout cluster carries the chain; other sites are 0-masked
    csrc = TemporalStormSPPSource(a=0.02, b=0.02, q_calm=(1.0, 0.0, 0.0, 0.0),
                                  q_storm=(0.0, 1.0, 0.0, 0.0), site_count=4, scope="cluster",
                                  affected_sites=2)
    layout = {"site_count": 4, "cluster_center": 0,
              "qubit_coords": {"0": [0.0, 0.0], "1": [10.0, 0.0], "2": [0.0, 1.0], "3": [10.0, 1.0]}}
    ctl = csrc.sample(seed=23, n_cycles=64, layout=layout)
    np.testing.assert_array_equal(ctl.payload_series("cluster_mask")[0],
                                  np.array([1, 0, 1, 0], dtype=np.int8))
    np.testing.assert_array_equal(ctl.latent_series("storm_state")[:, 1], np.zeros(64, dtype=np.int8))
    _raises_exact(ValueError, "affected_sites=3 exceeds site_count=2",
                  lambda: TemporalStormSPPSource(scope="cluster", site_count=2, affected_sites=3
                                                 ).sample(seed=1, n_cycles=8))


def test_KILLER_temporal_storm_sample_chain_discriminates():
    src = TemporalStormSPPSource(a=0.3, b=0.3, q_calm=(1.0, 0.0, 0.0, 0.0),
                                 q_storm=(0.0, 1.0, 0.0, 0.0), site_count=1, scope="global")
    tl = src.sample(seed=17, n_cycles=40)
    hidden = _repro_storm_hidden(src, 17, 40, 1)

    def prop(states):
        np.testing.assert_array_equal(states, hidden)

    assert_discriminates(prop, tl.latent_series("storm_state"), 1 - hidden, label="storm chain")


# =========================================================================== #
# empirical_transition_matrix / empirical_pauli_distribution / observed_autocorr #
# =========================================================================== #
def _storm_timeline_with_state(storm_state, *, cluster_mask=None, pauli_error=None):
    n = storm_state.shape[0]
    payload = {"storm_indicator": storm_state.astype(np.float64)}
    if cluster_mask is not None:
        payload["cluster_mask"] = cluster_mask
    if pauli_error is not None:
        payload["pauli_error"] = pauli_error
    return _mk_timeline(payload, latent={"storm_state": storm_state}, n=n)


def _indep_transition_counts(states, cluster_mask):
    valid = cluster_mask[:-1].astype(bool) & cluster_mask[1:].astype(bool)
    prev = states[:-1][valid].reshape(-1)
    cur = states[1:][valid].reshape(-1)
    counts = np.zeros((2, 2))
    for p, c in zip(prev, cur):
        counts[int(p), int(c)] += 1.0
    out = np.zeros((2, 2))
    rows = counts.sum(axis=1)
    for i in range(2):
        if rows[i] > 0.0:
            out[i] = counts[i] / rows[i]
    return out


def test_L0_empirical_transition_matrix_value_and_branches():
    src = TemporalStormSPPSource()
    # deterministic hand-built chain (single site); pin the count-based transition matrix
    states = np.array([[0], [0], [1], [1], [0], [1], [1], [1]], dtype=np.int8)
    cmask = np.ones_like(states, dtype=np.int8)
    tl = _storm_timeline_with_state(states, cluster_mask=cmask)
    got = src.empirical_transition_matrix(tl)
    assert_pins(got, _indep_transition_counts(states, cmask), label="empirical P")
    # a chain that NEVER visits state 1 -> rows[1]==0 -> that row stays all-zero
    z0 = np.zeros((5, 1), dtype=np.int8)
    got0 = src.empirical_transition_matrix(_storm_timeline_with_state(z0, cluster_mask=np.ones((5, 1), np.int8)))
    np.testing.assert_array_equal(got0[1], np.array([0.0, 0.0]))
    # no cluster_mask key -> defaults to all-ones (uses the .get fallback)
    tl_nomask = _mk_timeline({"storm_indicator": states.astype(float)},
                             latent={"storm_state": states})
    np.testing.assert_allclose(src.empirical_transition_matrix(tl_nomask),
                               _indep_transition_counts(states, cmask))
    # < 2 cycles
    _raises_exact(ValueError, "need at least two cycles to estimate transitions",
                  lambda: src.empirical_transition_matrix(
                      _storm_timeline_with_state(np.array([[1]], dtype=np.int8),
                                                 cluster_mask=np.ones((1, 1), np.int8))))
    # no consecutively-active site pairs -> prev.size == 0
    dead = np.zeros((4, 1), dtype=np.int8)
    _raises_exact(ValueError, "no active storm sites available for transition estimate",
                  lambda: src.empirical_transition_matrix(
                      _storm_timeline_with_state(dead, cluster_mask=dead)))


def test_L0_empirical_pauli_distribution_value_and_branches():
    src = TemporalStormSPPSource()
    emissions = np.array([[0], [1], [2], [3], [1], [0]], dtype=np.int8)
    tl = _mk_timeline({"pauli_error": emissions, "storm_indicator": np.zeros((6, 1))},
                      latent={"storm_state": np.zeros((6, 1), np.int8)})
    got = src.empirical_pauli_distribution(tl)
    counts = np.bincount(emissions.reshape(-1), minlength=4).astype(float)
    assert_pins(got, counts / counts.sum(), label="empirical pauli")
    assert_prob_dist(got, label="empirical pauli")
    # invalid labels
    bad = _mk_timeline({"pauli_error": np.array([[0], [4]], dtype=np.int8),
                        "storm_indicator": np.zeros((2, 1))},
                       latent={"storm_state": np.zeros((2, 1), np.int8)})
    _raises_exact(ValueError, "pauli_error payload contains labels outside I=0, X=1, Y=2, Z=3",
                  lambda: src.empirical_pauli_distribution(bad))
    # empty (n, 0) payload -> total <= 0
    empty = _mk_timeline({"pauli_error": np.zeros((3, 0), dtype=np.int8),
                          "storm_indicator": np.zeros((3, 0))},
                         latent={"storm_state": np.zeros((3, 0), np.int8)})
    _raises_exact(ValueError, "empty pauli_error payload",
                  lambda: src.empirical_pauli_distribution(empty))


def test_L0_observed_pauli_indicator_autocorrelation_value_and_guard():
    src = TemporalStormSPPSource()
    emissions = np.array([[1], [1], [0], [0], [1], [1], [0], [0]], dtype=np.int8)
    tl = _mk_timeline({"pauli_error": emissions, "storm_indicator": np.zeros((8, 1))},
                      latent={"storm_state": np.zeros((8, 1), np.int8)})
    indicator = (emissions == 1).astype(np.float64)
    assert_pins(src.observed_pauli_indicator_autocorrelation(tl, pauli=1, lag=1),
                _indep_lag(indicator, 1), label="observed autocorr")
    _raises_exact(ValueError, "pauli must be ordered as I=0, X=1, Y=2, Z=3",
                  lambda: src.observed_pauli_indicator_autocorrelation(tl, pauli=4))


def test_KILLER_empirical_pauli_distribution_discriminates():
    src = TemporalStormSPPSource()
    emissions = np.array([[0], [1], [2], [3], [1], [0]], dtype=np.int8)
    tl = _mk_timeline({"pauli_error": emissions, "storm_indicator": np.zeros((6, 1))},
                      latent={"storm_state": np.zeros((6, 1), np.int8)})
    counts = np.bincount(emissions.reshape(-1), minlength=4).astype(float)

    def prop(dist):
        assert_pins(dist, counts / counts.sum(), label="pauli dist")

    assert_discriminates(prop, src.empirical_pauli_distribution(tl),
                         np.array([0.25, 0.25, 0.25, 0.25]), label="empirical pauli dist")


# =========================================================================== #
# PRIVATE HELPERS -- direct value-pins + exact-message raises (mutation teeth)   #
# =========================================================================== #
def test_helper_require_integral_all_branches():
    assert sp._require_integral("x", 4) == 4
    assert sp._require_integral("x", np.int64(5)) == 5
    assert sp._require_integral("x", 4.0) == 4          # float that is integral
    assert sp._require_integral("x", np.float64(6.0)) == 6
    _raises_exact(ValueError, "x must be an integer, got 4.5", lambda: sp._require_integral("x", 4.5))
    _raises_exact(ValueError, "x must be an integer, got True", lambda: sp._require_integral("x", True))
    _raises_exact(ValueError, "x must be an integer, got 'z'", lambda: sp._require_integral("x", "z"))
    _raises_exact(ValueError, "x must be an integer, got inf",
                  lambda: sp._require_integral("x", float("inf")))


def test_helper_require_int_wrappers():
    assert sp._require_positive_int("x", 3) == 3
    _raises_exact(ValueError, "x must be a positive integer, got 0", lambda: sp._require_positive_int("x", 0))
    assert sp._require_nonnegative_int("x", 0) == 0
    _raises_exact(ValueError, "x must be a non-negative integer, got -1",
                  lambda: sp._require_nonnegative_int("x", -1))
    # a non-integral value routes through _require_integral carrying the SAME name (kills name->None)
    _raises_exact(ValueError, "x must be an integer, got 4.5",
                  lambda: sp._require_nonnegative_int("x", 4.5))


def test_helper_require_float_guards():
    assert sp._require_finite("x", 1.5) == 1.5
    _raises_exact(ValueError, "x must be finite, got nan", lambda: sp._require_finite("x", float("nan")))
    assert sp._require_positive("x", 2.0) == 2.0
    _raises_exact(ValueError, "x must be > 0, got 0.0", lambda: sp._require_positive("x", 0.0))
    # non-finite routes through _require_finite with the SAME name (kills the name->None mutant)
    _raises_exact(ValueError, "x must be finite, got inf", lambda: sp._require_positive("x", float("inf")))
    assert sp._require_nonnegative("x", 0.0) == 0.0
    _raises_exact(ValueError, "x must be >= 0, got -0.1", lambda: sp._require_nonnegative("x", -0.1))
    _raises_exact(ValueError, "x must be finite, got nan",
                  lambda: sp._require_nonnegative("x", float("nan")))


def test_helper_validate_probability_and_distribution():
    assert sp._validate_probability("p", 0.0, allow_zero=True) == 0.0
    _raises_exact(ValueError, "p must be in (0, 1), got 0.0",
                  lambda: sp._validate_probability("p", 0.0, allow_zero=False))
    _raises_exact(ValueError, "p must be in [0, 1), got 1.0",
                  lambda: sp._validate_probability("p", 1.0, allow_zero=True))
    # a non-finite value routes through _require_finite carrying the SAME name (kills name->None)
    _raises_exact(ValueError, "p must be finite, got nan",
                  lambda: sp._validate_probability("p", float("nan"), allow_zero=True))
    assert sp._validate_distribution("q", (0.25, 0.25, 0.25, 0.25)) == (0.25, 0.25, 0.25, 0.25)
    _raises_exact(ValueError,
                  "q must have four probabilities ordered as ('I', 'X', 'Y', 'Z')",
                  lambda: sp._validate_distribution("q", (0.5, 0.5)))
    _raises_exact(ValueError, "q[0] must be in [0, 1], got -0.1",
                  lambda: sp._validate_distribution("q", (-0.1, 0.4, 0.4, 0.3)))
    # a value > 1 (but < 2) must still be rejected -> proves the upper bound is 1.0, not 2.0
    _raises_exact(ValueError, "q[0] must be in [0, 1], got 1.5",
                  lambda: sp._validate_distribution("q", (1.5, -0.5, 0.0, 0.0)))
    # a non-finite entry carries the per-index name into _require_finite (kills the name->None mutant)
    _raises_exact(ValueError, "q[0] must be finite, got nan",
                  lambda: sp._validate_distribution("q", (float("nan"), 0.4, 0.3, 0.3)))
    _raises_exact(ValueError, "q must sum to 1, got 0.8",
                  lambda: sp._validate_distribution("q", (0.2, 0.2, 0.2, 0.2)))


def test_helper_layout_site_count_all_branches():
    assert sp._layout_site_count(None, default=3) == 3
    assert sp._layout_site_count(5, default=1) == 5
    assert sp._layout_site_count({"site_count": 7}, default=1) == 7
    assert sp._layout_site_count({"n_qubits": 4}, default=1) == 4
    assert sp._layout_site_count({"num_qubits": 6}, default=1) == 6
    assert sp._layout_site_count({"unrelated": 1}, default=2) == 2   # Mapping, no known key -> default

    class _HasNum:
        num_qubits = 9

    class _HasN:
        n_qubits = 8

    class _Bare:
        pass

    assert sp._layout_site_count(_HasNum(), default=1) == 9
    assert sp._layout_site_count(_HasN(), default=1) == 8
    assert sp._layout_site_count(_Bare(), default=2) == 2

    # Each path forwards a DISTINCT `name` into _require_positive_int; trip each with an invalid
    # (non-positive) value so its exact name surfaces in the message (kills the name-literal mutants).
    _raises_exact(ValueError, "default must be a positive integer, got 0",
                  lambda: sp._layout_site_count(None, default=0))            # layout is None
    _raises_exact(ValueError, "layout must be a positive integer, got 0",
                  lambda: sp._layout_site_count(0, default=1))               # int layout
    _raises_exact(ValueError, "layout['site_count'] must be a positive integer, got 0",
                  lambda: sp._layout_site_count({"site_count": 0}, default=1))
    _raises_exact(ValueError, "layout.num_qubits must be a positive integer, got 0",
                  lambda: sp._layout_site_count(type("Q0", (), {"num_qubits": 0})(), default=1))
    _raises_exact(ValueError, "layout.n_qubits must be a positive integer, got 0",
                  lambda: sp._layout_site_count(type("N0", (), {"n_qubits": 0})(), default=1))
    _raises_exact(ValueError, "default must be a positive integer, got 0",
                  lambda: sp._layout_site_count(type("B0", (), {})(), default=0))  # fallthrough


def test_helper_layout_cluster_center_all_branches():
    assert sp._layout_cluster_center(None) is None
    assert sp._layout_cluster_center({"cluster_center": 2}) == 2
    assert sp._layout_cluster_center({"phase_burst_center": 3}) == 3
    assert sp._layout_cluster_center({"unrelated": 1}) is None

    class _M:
        metadata = {"cluster_center": 4}

    class _PhaseBurstMetadata:
        metadata = {"phase_burst_center": 5}

    class _NoMeta:
        metadata = None

    assert sp._layout_cluster_center(_M()) == 4
    assert sp._layout_cluster_center(_PhaseBurstMetadata()) == 5
    assert sp._layout_cluster_center(_NoMeta()) is None
    # a negative center trips the nonneg-int guard with the path-specific name (kills name mutants)
    _raises_exact(ValueError, "layout['cluster_center'] must be a non-negative integer, got -1",
                  lambda: sp._layout_cluster_center({"cluster_center": -1}))
    _raises_exact(ValueError, "layout.metadata['cluster_center'] must be a non-negative integer, got -1",
                  lambda: sp._layout_cluster_center(type("MM", (), {"metadata": {"cluster_center": -1}})()))


def test_helper_layout_coordinates_all_branches():
    # dict-of-coords via 'qubit_coords' (returns float64 -- the dtype is load-bearing)
    coords = sp._layout_coordinates({"qubit_coords": {0: [0.0, 0.0], 1: [1.0, 2.0]}}, 2)
    np.testing.assert_allclose(coords, [[0.0, 0.0], [1.0, 2.0]])
    assert coords.dtype == np.float64
    # each LAYOUT-dict key alias is honoured distinctly (kills the key-string mutants)
    np.testing.assert_allclose(
        sp._layout_coordinates({"coordinates": [[0.0], [1.0], [2.0]]}, 3), [[0.0], [1.0], [2.0]])
    coords_c = sp._layout_coordinates({"coords": [[3.0], [4.0]]}, 2)
    np.testing.assert_allclose(coords_c, [[3.0], [4.0]])
    assert coords_c.dtype == np.float64

    # metadata-carried coords: each alias key resolves distinctly
    np.testing.assert_allclose(
        sp._layout_coordinates(type("MQ", (), {"metadata": {"qubit_coords": {0: [0.0], 1: [1.0]}}})(), 2),
        [[0.0], [1.0]])
    np.testing.assert_allclose(
        sp._layout_coordinates(type("MC", (), {"metadata": {"coordinates": [[5.0], [6.0]]}})(), 2),
        [[5.0], [6.0]])

    class _M:
        metadata = {"coords": [[0.0, 1.0], [2.0, 3.0]]}

    mc = sp._layout_coordinates(_M(), 2)
    np.testing.assert_allclose(mc, [[0.0, 1.0], [2.0, 3.0]])
    assert mc.dtype == np.float64
    # no coords anywhere -> None
    assert sp._layout_coordinates({"site_count": 4}, 4) is None
    assert sp._layout_coordinates(None, 3) is None
    # missing a site in the dict form
    _raises_exact(ValueError, "layout coordinates missing site 1",
                  lambda: sp._layout_coordinates({"qubit_coords": {0: [0.0]}}, 2))
    # wrong shape
    _raises_exact(ValueError,
                  "layout coordinates must have shape (site_count, coord_dim), got (2, 1) for site_count=3",
                  lambda: sp._layout_coordinates({"qubit_coords": [[0.0], [1.0]]}, 3))
    # non-finite
    _raises_exact(ValueError, "layout coordinates contain non-finite values",
                  lambda: sp._layout_coordinates({"qubit_coords": [[0.0], [float("inf")]]}, 2))


def test_helper_cluster_affected_count_and_indices_and_site_index():
    assert sp._cluster_affected_count(3, 10) == 3
    assert sp._cluster_affected_count(None, 9) == 3     # round(sqrt(9))
    assert sp._cluster_affected_count(None, 1) == 1     # max(1, round(1))
    _raises_exact(ValueError, "affected_sites=5 exceeds site_count=2",
                  lambda: sp._cluster_affected_count(5, 2))
    # indices with layout coords: nearest 2 to center 0 are {0, 2}
    layout = {"cluster_center": 0,
              "qubit_coords": {0: [0.0, 0.0], 1: [10.0, 0.0], 2: [0.0, 1.0], 3: [10.0, 1.0]}}
    idx = sp._cluster_indices(np.random.default_rng(0), 4, affected=2, layout=layout)
    assert set(int(i) for i in idx) == {0, 2}
    # COORDS path, center NOT at origin + UNIQUE squared distances -> exact ordered pin (kills the
    # (coords - center)**2 -> *2 / **3 / +center mutations; ties absent so sort kind is irrelevant).
    coords1d = {"cluster_center": 1, "qubit_coords": {0: [0.0], 1: [10.0], 2: [21.0], 3: [33.0]}}
    off_c = sp._cluster_indices(np.random.default_rng(0), 4, affected=2, layout=coords1d)
    np.testing.assert_array_equal(off_c, [1, 0])   # |x-10|^2 = [100,0,121,529] -> [1,0,...]
    # OFFSETS path with a KNOWN edge center (=3, unique distances) -> kills the arange - center ->
    # arange + center mutation.
    off_e = sp._cluster_indices(np.random.default_rng(0), 4, affected=2, layout={"cluster_center": 3})
    np.testing.assert_array_equal(off_e, [3, 2])   # |arange(4)-3| = [3,2,1,0] -> [3,2,...]
    # OFFSETS path with the RNG-drawn center: seed 11 draws integers(0,4)==0 (a value integers(1,4)
    # can never produce), so the lower bound 0 is load-bearing.
    off_r = sp._cluster_indices(np.random.default_rng(11), 4, affected=2, layout=None)
    np.testing.assert_array_equal(off_r, [0, 1])   # center 0 -> |arange(4)| = [0,1,2,3] -> [0,1,...]
    # out-of-range cluster_center trips _require_site_index with its path name (kills name mutants)
    _raises_exact(ValueError, "cluster_center=9 outside site_count=4",
                  lambda: sp._cluster_indices(np.random.default_rng(0), 4, affected=2,
                                              layout={"cluster_center": 9}))
    assert sp._require_site_index("c", 2, 5) == 2
    _raises_exact(ValueError, "c=5 outside site_count=5", lambda: sp._require_site_index("c", 5, 5))
    _raises_exact(ValueError, "c must be a non-negative integer, got -1",
                  lambda: sp._require_site_index("c", -1, 5))


def test_helper_coerce_array_map_branches():
    out = sp._coerce_array_map("payload", {"a": np.array([1.0, 2.0])}, 2)
    np.testing.assert_array_equal(out["a"], [1.0, 2.0])
    # non-numeric arrays skip the finite check
    out2 = sp._coerce_array_map("payload", {"s": np.array(["a", "b"])}, 2)
    assert out2["s"].tolist() == ["a", "b"]
    _raises_exact(ValueError, "payload['x'] must have cycle axis length 2",
                  lambda: sp._coerce_array_map("payload", {"x": 5}, 2))       # ndim 0
    _raises_exact(ValueError, "payload['x'] must have cycle axis length 2",
                  lambda: sp._coerce_array_map("payload", {"x": np.array([1.0])}, 2))  # wrong len
    _raises_exact(ValueError, "payload['x'] contains non-finite values",
                  lambda: sp._coerce_array_map("payload", {"x": np.array([1.0, np.inf])}, 2))
    # a float32 inf still trips the finite guard: issubdtype(float32, np.number) must stay TRUE
    # (a mutant swapping np.number -> None(=float64) makes issubdtype(float32, float64) False and
    # would wrongly SKIP the finite check).
    _raises_exact(ValueError, "payload['x'] contains non-finite values",
                  lambda: sp._coerce_array_map("payload", {"x": np.array([1.0, np.inf], dtype=np.float32)}, 2))
    # the coerced arrays are COPIES: mutating the caller's input does not alias the stored array
    src_arr = np.array([1.0, 2.0])
    coerced = sp._coerce_array_map("payload", {"a": src_arr}, 2)
    src_arr[0] = 99.0
    assert coerced["a"].tolist() == [1.0, 2.0]


def test_helper_array_summary_numeric_and_non_numeric():
    num = sp._array_summary(np.array([1.0, 2.0, 3.0]))
    assert num["shape"] == [3] and num["dtype"] == "float64"
    assert num["min"] == 1.0 and num["max"] == 3.0 and num["mean"] == 2.0
    assert num["std"] == pytest.approx(np.std([1.0, 2.0, 3.0]))
    assert num["sha256"] == sp._array_sha256(np.array([1.0, 2.0, 3.0]))
    s = sp._array_summary(np.array(["a", "b"]))
    assert s["shape"] == [2] and "sha256" not in s and "min" not in s


def test_helper_array_sha256_is_content_addressed():
    a = np.array([1, 2, 3], dtype=np.int64)
    assert sp._array_sha256(a) == sp._array_sha256(np.array([1, 2, 3], dtype=np.int64))
    assert sp._array_sha256(a) != sp._array_sha256(np.array([1, 2, 4], dtype=np.int64))
    assert sp._array_sha256(a) != sp._array_sha256(a.astype(np.int32))   # dtype is hashed
    # SAME bytes, DIFFERENT dtype -> different hash (proves str(value.dtype) is hashed, not str(None))
    same_bytes = np.array([1, 2, 3, 4], dtype=np.int8)
    assert sp._array_sha256(same_bytes) != sp._array_sha256(same_bytes.view(np.uint8))
    # SAME bytes + dtype, DIFFERENT shape -> different hash (proves the shape is hashed, not None)
    flat = np.arange(6, dtype=np.int8)
    assert sp._array_sha256(flat) != sp._array_sha256(flat.reshape(2, 3))


def test_helper_json_safe_covers_every_type_branch():
    val = {"m": {"k": 1}, "t": (1, 2), "l": [3, 4], "arr": np.array([1, 2]),
           "ni": np.int64(5), "nf": np.float64(2.5), "nb": np.bool_(True), "s": "x"}
    out = sp._json_safe(val)
    assert out == {"m": {"k": 1}, "t": [1, 2], "l": [3, 4], "arr": [1, 2],
                   "ni": 5, "nf": 2.5, "nb": True, "s": "x"}
    assert isinstance(out["ni"], int) and isinstance(out["nf"], float) and isinstance(out["nb"], bool)


def test_helper_load_npz_array_map_branches():
    arr = np.array([1, 2, 3], dtype=np.int64)
    name = "payload_0"
    sha = sp._array_sha256(arr)
    data = {name: arr}
    manifest = {"payload_arrays": {"z": name}, "payload": {"z": {"sha256": sha}}}
    out = sp._load_npz_array_map(data, manifest, arrays_key="payload_arrays", summary_key="payload")
    np.testing.assert_array_equal(out["z"], arr)
    assert out["z"] is not arr   # the loaded array is a COPY (kills the copy=False mutation)
    _raises_exact(ValueError, "source timeline NPZ manifest missing 'payload_arrays'/'payload'",
                  lambda: sp._load_npz_array_map(data, {"payload": {}},
                                                 arrays_key="payload_arrays", summary_key="payload"))
    _raises_exact(ValueError, "source timeline NPZ missing array 'nope' for payload['z']",
                  lambda: sp._load_npz_array_map(
                      {}, {"payload_arrays": {"z": "nope"}, "payload": {"z": {"sha256": sha}}},
                      arrays_key="payload_arrays", summary_key="payload"))
    _raises_exact(ValueError, "source timeline NPZ manifest missing sha256 for payload['z']",
                  lambda: sp._load_npz_array_map(
                      data, {"payload_arrays": {"z": name}, "payload": {"z": {}}},
                      arrays_key="payload_arrays", summary_key="payload"))
    with pytest.raises(ValueError, match="hash mismatch"):
        sp._load_npz_array_map(
            data, {"payload_arrays": {"z": name}, "payload": {"z": {"sha256": "deadbeef"}}},
            arrays_key="payload_arrays", summary_key="payload")


def test_helper_mhz_to_radns_and_rtn_flip_probability():
    assert_pins(sp._mhz_to_radns(np.array([1.0, -2.0])),
                np.array([_TWO_PI * 1.0e-3, -_TWO_PI * 2.0e-3]), label="mhz->radns")
    for g in (0.0, 0.05, 0.5):
        assert_pins(sp._rtn_flip_probability(g), _indep_flip_prob(g), label=f"flip@{g}")
    _raises_exact(ValueError, "gamma_per_cycle must be >= 0, got -0.1",
                  lambda: sp._rtn_flip_probability(-0.1))


def test_helper_sample_rtn_states_matches_independent_replay():
    # seeds 2 and 8 have first rng.random() < 0.5 (states[0] == +1), so the init literal `1` is
    # load-bearing (a mutant setting states[0]=2 diverges from the +-1 replay).
    for seed in (0, 2, 7, 8, 123):
        for gamma in (0.05, 0.3):
            got = sp._sample_rtn_states(np.random.default_rng(seed), 50, gamma)
            np.testing.assert_array_equal(got, _repro_rtn(seed, 50, gamma))
            assert got.dtype == np.int8            # int8 dtype is load-bearing (npz sha256 hashes it)
            assert set(np.unique(got).tolist()) <= {-1, 1}
