"""P1-b sampled-trajectory closed-form falsifiers for Axis-2 source processes.

Promotes faithfulness-table rows 7 (RTNSource) and 8 (OneOverFDriftSource)
(``docs/twin_validation/p1_faithfulness_table.md``) from "partially" toward
"bounded". ``tests/test_source_process.py`` already pins the PARAMETER-level
closed forms (flip probability, autocorr base) and structural PSD properties;
this file closes the remaining gap: SAMPLED trajectories must realize the
declared second-order statistics quantitatively, under a principled tolerance,
with a negative control proving the gate can fail.

Declared closed forms (epistemic class (a) -- exact finite-state Markov
identities, read off the class docstrings/implementation in
``src/error_coupling_simulator/source/process.py``):

* ``RTNSource``: latent telegraph s_t in {-1,+1}, initialized from its
  stationary law (uniform +-1), per-cycle flip probability
  p = (1 - exp(-2*gamma)) / 2, payload z_t = A * s_t ("z_radns").
  Strict stationarity + symmetry give, EXACTLY at every finite t, lag:
      E[z_t] = 0,   C(l) = E[z_t z_{t+l}] = A^2 * (1 - 2p)^l
                          = A^2 * exp(-2*gamma*l).
* ``OneOverFDriftSource``: z_t = sum_k v_k s_k(t) over K INDEPENDENT
  telegraphs, gamma_k log-spaced, v_k = A / sqrt(K). Hence
      C(l) = sum_k v_k^2 exp(-2*gamma_k*l),   C(0) = A^2.
  This is the lag-domain transform of the declared sum-of-Lorentzians
  ``analytic_psd`` (v^2 * 4g / ((2g)^2 + w^2)  <->  v^2 * exp(-2g|tau|)).

Estimator + tolerance derivation (the 5-sigma gate itself is epistemic class
(c) -- a decision rule, per METRICS.md):

* Sample M independent seeded timelines of T cycles via ``source.sample``.
  Per-trajectory KNOWN-MEAN estimator  c_i(l) = mean_t z_t z_{t+l}.
  Because the latent chain starts in its stationary law and the process mean
  is exactly zero by +-1 symmetry, E[c_i(l)] = C(l) exactly at finite T --
  no O(1/T) mean-subtraction bias, so a pooled deviation can only be sampling
  noise or a wrong declared form.
* The c_i are iid across trajectories (independent seeds), so
  SE(l) = std(c_i, ddof=1) / sqrt(M) is a valid standard error of the pooled
  mean REGARDLESS of the within-trajectory correlation structure (the slow-
  fluctuator correlation inflation is absorbed into the across-trajectory
  spread -- important for the gamma_min = 0.005 fluctuator whose correlation
  time ~1/(2*gamma) = 100 cycles is comparable to T).
* Gate: |pooled - analytic| <= 5 * SE. Under the CLT each gate has
  false-positive probability ~5.7e-7; the 13 statistical gates in this file
  union-bound to < 1e-5 total, so a red run is evidence, not noise. (The RTN
  lag-0 variance is NOT a statistical gate: z_t^2 == A^2 structurally, zero
  sampling spread, so it is asserted as an exact identity instead.)
* NEGATIVE control (scrutinize-vacuous-checks rule): the SAME empirical
  statistic is scored against a deliberately wrong closed form (all gammas
  doubled) and must EXCEED the 5-sigma gate at at least one lag in 1..5,
  proving the gate falsifiable at this M, T. Gamma-doubling leaves
  C(0) = A^2 unchanged, so the control lives on lags >= 1 by construction.

CPU-only, numpy-only, fully seeded/deterministic. Runtime is dominated by the
per-cycle Python loop inside ``_sample_rtn_states`` (~M*T*(1+K) draws).
"""

import functools
import math

import numpy as np

from error_coupling_simulator.source.process import OneOverFDriftSource, RTNSource

SEED0 = 20260706
M_TRAJECTORIES = 3000
N_CYCLES = 100
LAGS = (1, 2, 3, 4, 5)
GATE_SIGMA = 5.0


@functools.lru_cache(maxsize=4)
def _sampled_payloads(source) -> np.ndarray:
    """(M, T) matrix of z_radns payloads from M independently seeded timelines.

    Cached per (frozen, hashable) source dataclass so the three tests per
    source share one sampling pass. Treat the returned array as read-only.
    """

    z = np.empty((M_TRAJECTORIES, N_CYCLES), dtype=np.float64)
    for i in range(M_TRAJECTORIES):
        timeline = source.sample(seed=SEED0 + i, n_cycles=N_CYCLES)
        z[i] = timeline.payload_series("z_radns")
    return z


def _per_trajectory_autocov(z: np.ndarray, lag: int) -> np.ndarray:
    """Known-mean lag-l autocovariance estimate per trajectory (row)."""

    if lag == 0:
        prod = z * z
    else:
        prod = z[:, :-lag] * z[:, lag:]
    return prod.mean(axis=1)


def _pooled_z(per_traj: np.ndarray, analytic: float) -> tuple[float, float, float]:
    """Return (z_score, pooled_estimate, standard_error) vs a closed form."""

    m = per_traj.shape[0]
    pooled = float(per_traj.mean())
    se = float(per_traj.std(ddof=1)) / math.sqrt(m)
    return (pooled - analytic) / se, pooled, se


def _rtn_analytic_autocov(source: RTNSource, lag: int, *, gamma_scale: float = 1.0) -> float:
    a = float(source.amplitude_radns)
    return a * a * math.exp(-2.0 * gamma_scale * float(source.gamma_per_cycle) * lag)


def _one_over_f_analytic_autocov(
    source: OneOverFDriftSource, lag: int, *, gamma_scale: float = 1.0
) -> float:
    amps = source.amplitudes_radns
    gammas = gamma_scale * source.gammas_per_cycle
    return float(np.sum(amps * amps * np.exp(-2.0 * gammas * lag)))


def _assert_lags_within_gate(z: np.ndarray, analytic_fn, label: str) -> None:
    rows = []
    for lag in LAGS:
        analytic = analytic_fn(lag)
        zscore, pooled, se = _pooled_z(_per_trajectory_autocov(z, lag), analytic)
        rows.append(f"{label} lag={lag}: pooled={pooled:.6e} analytic={analytic:.6e} se={se:.3e} z={zscore:+.3f}")
    print("\n".join(rows))
    for lag, row in zip(LAGS, rows, strict=True):
        analytic = analytic_fn(lag)
        zscore, _, _ = _pooled_z(_per_trajectory_autocov(z, lag), analytic)
        assert abs(zscore) <= GATE_SIGMA, f"5-sigma gate FAILED: {row}"


def _assert_wrong_form_fails(z: np.ndarray, wrong_fn, label: str) -> None:
    zscores = {}
    for lag in LAGS:
        zscore, pooled, se = _pooled_z(_per_trajectory_autocov(z, lag), wrong_fn(lag))
        zscores[lag] = zscore
        print(
            f"{label} NEGATIVE control lag={lag}: pooled={pooled:.6e} "
            f"wrong_form={wrong_fn(lag):.6e} se={se:.3e} z={zscore:+.3f}"
        )
    worst = max(abs(v) for v in zscores.values())
    assert worst > GATE_SIGMA, (
        f"negative control is VACUOUS for {label}: max |z| over lags {LAGS} is "
        f"{worst:.3f} <= {GATE_SIGMA} -- the gate could not have rejected a "
        f"gamma-doubled misdeclaration at this M, T"
    )


def _assert_variance_and_mean(z: np.ndarray, variance: float, label: str) -> None:
    per0 = _per_trajectory_autocov(z, 0)
    spread0 = float(per0.std(ddof=1))
    if spread0 == 0.0:
        # Structural identity: for the single-telegraph RTNSource,
        # z_t^2 == A^2 for EVERY sample (z_t = +-A), so the lag-0 estimator has
        # exactly zero sampling spread and the 5-sigma SE gate degenerates.
        # The correct check is exactness -- this still verifies the amplitude
        # scaling of the sampled payload against the declared variance.
        pooled0 = float(per0.mean())
        print(
            f"{label} lag-0 variance: pooled={pooled0:.6e} analytic={variance:.6e} "
            "spread=0 (structural identity, exact check rtol=1e-12)"
        )
        np.testing.assert_allclose(pooled0, variance, rtol=1e-12, atol=0.0)
    else:
        z0, pooled0, se0 = _pooled_z(per0, variance)
        print(f"{label} lag-0 variance: pooled={pooled0:.6e} analytic={variance:.6e} se={se0:.3e} z={z0:+.3f}")
        assert abs(z0) <= GATE_SIGMA, (
            f"lag-0 variance gate FAILED for {label}: pooled={pooled0!r} vs analytic={variance!r} (z={z0:+.3f})"
        )
    zm, pooled_m, se_m = _pooled_z(z.mean(axis=1), 0.0)
    print(f"{label} stationary mean: pooled={pooled_m:.3e} analytic=0.0 se={se_m:.3e} z={zm:+.3f}")
    assert abs(zm) <= GATE_SIGMA, (
        f"zero-mean stationarity gate FAILED for {label}: pooled={pooled_m!r} (z={zm:+.3f})"
    )


# ---------------------------------------------------------------------------
# RTNSource (defaults: amplitude_radns=1e-4, gamma_per_cycle=0.05)
# ---------------------------------------------------------------------------


def test_rtn_sampled_autocovariance_matches_declared_closed_form():
    source = RTNSource()
    z = _sampled_payloads(source)
    _assert_lags_within_gate(z, lambda lag: _rtn_analytic_autocov(source, lag), "RTNSource")


def test_rtn_negative_control_gamma_doubled_exceeds_gate():
    source = RTNSource()
    z = _sampled_payloads(source)
    _assert_wrong_form_fails(
        z, lambda lag: _rtn_analytic_autocov(source, lag, gamma_scale=2.0), "RTNSource"
    )


def test_rtn_lag0_variance_and_zero_mean_are_stationary():
    source = RTNSource()
    z = _sampled_payloads(source)
    _assert_variance_and_mean(z, _rtn_analytic_autocov(source, 0), "RTNSource")


# ---------------------------------------------------------------------------
# OneOverFDriftSource (defaults: amplitude_radns=1e-4, n_fluctuators=8,
# gamma geomspace(0.005, 0.5, 8), per-fluctuator weight A/sqrt(8))
# ---------------------------------------------------------------------------


def test_one_over_f_sampled_autocovariance_matches_declared_closed_form():
    source = OneOverFDriftSource()
    z = _sampled_payloads(source)
    _assert_lags_within_gate(
        z, lambda lag: _one_over_f_analytic_autocov(source, lag), "OneOverFDriftSource"
    )


def test_one_over_f_negative_control_gamma_doubled_exceeds_gate():
    source = OneOverFDriftSource()
    z = _sampled_payloads(source)
    _assert_wrong_form_fails(
        z,
        lambda lag: _one_over_f_analytic_autocov(source, lag, gamma_scale=2.0),
        "OneOverFDriftSource",
    )


def test_one_over_f_lag0_variance_and_zero_mean_are_stationary():
    source = OneOverFDriftSource()
    z = _sampled_payloads(source)
    _assert_variance_and_mean(z, _one_over_f_analytic_autocov(source, 0), "OneOverFDriftSource")
