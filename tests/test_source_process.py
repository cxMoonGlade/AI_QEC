from __future__ import annotations

import math

import numpy as np
import pytest

from qec_twin.mechanisms import (
    OneOverFDriftSource,
    PhaseBurstSource,
    RTNSource,
    SourceCouplingConfig,
    SourceTimeline,
    TemporalStormSPPSource,
    cross_mechanism_correlation,
    lag_autocorrelation,
    timeline_to_coupled_params,
    timeline_to_site_coupled_params,
)


def test_rtn_source_is_replayable_and_uses_exact_discrete_flip_probability():
    source = RTNSource(amplitude_radns=2.0e-4, gamma_per_cycle=0.25)
    a = source.sample(seed=7, n_cycles=128)
    b = source.sample(seed=7, n_cycles=128)

    assert source.flip_probability == pytest.approx(0.5 * (1.0 - math.exp(-0.5)))
    assert source.autocorr_base == pytest.approx(math.exp(-0.5))
    np.testing.assert_array_equal(a.payload_series("z_radns"), b.payload_series("z_radns"))
    assert set(np.unique(a.payload_series("z_radns"))) <= {-2.0e-4, 2.0e-4}
    assert a.to_manifest()["metadata"]["source"] == "RTNSource"


def test_source_timeline_exact_npz_replay_round_trips_payloads_and_latents(tmp_path):
    timeline = OneOverFDriftSource(
        amplitude_radns=3.0e-4,
        n_fluctuators=4,
        gamma_min_per_cycle=0.01,
        gamma_max_per_cycle=0.3,
    ).sample(seed=21, n_cycles=128)
    path = timeline.save_npz(tmp_path / "source_timeline.npz")
    loaded = SourceTimeline.load_npz(path)

    assert loaded.to_manifest()["payload"]["z_radns"]["sha256"] == timeline.to_manifest()["payload"]["z_radns"]["sha256"]
    np.testing.assert_array_equal(loaded.payload_series("z_radns"), timeline.payload_series("z_radns"))
    np.testing.assert_array_equal(loaded.latent_series("rtn_states"), timeline.latent_series("rtn_states"))
    assert loaded.seed == timeline.seed


def test_source_timeline_npz_replay_validates_internal_array_hashes(tmp_path):
    timeline = RTNSource(amplitude_radns=2.0e-4, gamma_per_cycle=0.2).sample(seed=22, n_cycles=32)
    path = timeline.save_npz(tmp_path / "source_timeline.npz")
    with np.load(path, allow_pickle=False) as data:
        arrays = {key: np.array(data[key], copy=True) for key in data.files}
    arrays["payload_0"] = np.array(arrays["payload_0"], copy=True)
    arrays["payload_0"][0] *= -1.0
    bad_path = tmp_path / "source_timeline_bad.npz"
    np.savez_compressed(bad_path, **arrays)

    with pytest.raises(ValueError, match="hash mismatch"):
        SourceTimeline.load_npz(bad_path)


def test_one_over_f_source_has_log_spaced_rtns_and_positive_lorentzian_psd():
    source = OneOverFDriftSource(
        amplitude_radns=3.0e-4,
        n_fluctuators=6,
        gamma_min_per_cycle=0.005,
        gamma_max_per_cycle=0.5,
    )
    timeline = source.sample(seed=11, n_cycles=256)
    gammas = source.gammas_per_cycle
    psd = source.analytic_psd(np.asarray([0.01, 0.1, 1.0]))

    assert timeline.payload_series("z_radns").shape == (256,)
    assert timeline.latent_series("rtn_states").shape == (256, 6)
    np.testing.assert_allclose(np.diff(np.log(gammas)), np.full(5, np.diff(np.log(gammas))[0]))
    assert np.all(psd > 0.0)
    assert psd[0] > psd[-1]


def test_timeline_independent_baseline_preserves_marginal_but_breaks_alignment():
    source = RTNSource(amplitude_radns=1.0e-4, gamma_per_cycle=0.02)
    timeline = source.sample(seed=3, n_cycles=2000)
    baseline = timeline.independent_baseline(seed=4)

    np.testing.assert_allclose(
        np.sort(timeline.payload_series("z_radns")),
        np.sort(baseline.payload_series("z_radns")),
        rtol=0,
        atol=0,
    )
    assert baseline.coupling_mode == "independent"
    assert baseline.latent == {}


def test_independent_timeline_feeds_independent_theta_fanout():
    timeline = RTNSource(amplitude_radns=1.0e-4, gamma_per_cycle=0.1).sample(seed=31, n_cycles=3000)
    baseline = timeline.independent_baseline(seed=32)
    params = timeline_to_coupled_params(baseline, SourceCouplingConfig(z_scale_radns=1.0e-4))

    assert {p.coupling_mode for p in params} == {"independent"}
    shared = timeline_to_coupled_params(timeline, SourceCouplingConfig(z_scale_radns=1.0e-4))
    assert cross_mechanism_correlation(shared, "detuning_radns", "drive_omega_radns") > 0.9
    assert abs(cross_mechanism_correlation(params, "detuning_radns", "drive_omega_radns")) < 0.25


def test_phase_burst_source_uses_non_exponential_recovery_and_echo_hook():
    source = PhaseBurstSource(
        site_count=2,
        event_times=(0,),
        peak_shift_mhz=-2.0,
        recovery_time_ns=2_000.0,
        cycle_time_ns=1_000.0,
        phase_window_ns=1_000.0,
        echo_suppression=0.1,
        t1_duration_ns=2_500.0,
    )
    timeline = source.sample(seed=1, n_cycles=5)
    delta = timeline.payload_series("delta_fq_mhz")
    phase = timeline.payload_series("phase_rad")
    echoed = timeline.payload_series("echoed_phase_rad")

    assert delta[:, 0].tolist() == pytest.approx([-2.0, -2.0 / 1.5, -1.0, -0.8, -2.0 / 3.0])
    assert delta[:, 1].tolist() == pytest.approx(delta[:, 0].tolist())
    assert phase[0, 0] == pytest.approx(-4.0 * math.pi)
    assert echoed[0, 0] == pytest.approx(0.1 * phase[0, 0])
    np.testing.assert_allclose(
        timeline.payload_series("t1_burst"),
        np.asarray([[1.0, 1.0], [1.0, 1.0], [1.0, 1.0], [0.0, 0.0], [0.0, 0.0]]),
    )
    assert timeline.to_manifest()["metadata"]["source"] == "PhaseBurstSource"


def test_phase_burst_row_preserving_baseline_keeps_payload_algebra():
    source = PhaseBurstSource(
        site_count=3,
        event_times=(0, 4),
        peak_shift_mhz=-2.0,
        recovery_time_ns=2_000.0,
        cycle_time_ns=1_000.0,
        phase_window_ns=250.0,
        echo_suppression=0.2,
    )
    baseline = source.sample(seed=2, n_cycles=8).independent_baseline(seed=3)

    detuning = baseline.payload_series("detuning_radns")
    np.testing.assert_allclose(baseline.payload_series("phase_rad"), detuning * 250.0)
    np.testing.assert_allclose(baseline.payload_series("echoed_phase_rad"), detuning * 250.0 * 0.2)


def test_phase_burst_cluster_footprint_is_not_forced_chip_wide():
    source = PhaseBurstSource(
        site_count=8,
        event_times=(1,),
        footprint="cluster",
        affected_sites=3,
        peak_shift_mhz=-1.0,
        recovery_time_ns=1_000.0,
    )
    timeline = source.sample(seed=5, n_cycles=3)
    delta = timeline.payload_series("delta_fq_mhz")

    assert np.count_nonzero(delta[1]) == 3
    assert np.count_nonzero(delta[0]) == 0
    assert np.count_nonzero(delta[2]) == 3


def test_phase_burst_cluster_can_use_layout_coordinates():
    source = PhaseBurstSource(
        site_count=4,
        event_times=(0,),
        footprint="cluster",
        affected_sites=2,
        peak_shift_mhz=-1.0,
    )
    layout = {
        "site_count": 4,
        "cluster_center": 0,
        "qubit_coords": {"0": [0.0, 0.0], "1": [10.0, 0.0], "2": [0.0, 1.0], "3": [10.0, 1.0]},
    }
    timeline = source.sample(seed=5, n_cycles=2, layout=layout)
    affected = set(np.flatnonzero(timeline.payload_series("delta_fq_mhz")[0]))

    assert affected == {0, 2}
    np.testing.assert_array_equal(timeline.latent_series("event_site_mask")[0], np.asarray([1, 0, 1, 0], dtype=np.int8))


def test_phase_burst_rejects_bad_event_times_layouts_and_footprints():
    with pytest.raises(ValueError, match="integer"):
        PhaseBurstSource(event_times=(1.9,)).sample(seed=1, n_cycles=4)
    with pytest.raises(ValueError, match="affected_sites"):
        PhaseBurstSource(site_count=2, event_times=(0,), footprint="cluster", affected_sites=3).sample(seed=1, n_cycles=2)
    with pytest.raises(ValueError, match="missing site"):
        PhaseBurstSource(site_count=3, event_times=(0,), footprint="cluster", affected_sites=2).sample(
            seed=1,
            n_cycles=2,
            layout={"site_count": 3, "qubit_coords": {"0": [0.0], "1": [1.0]}},
        )
    with pytest.raises(ValueError, match="shape"):
        PhaseBurstSource(site_count=3, event_times=(0,), footprint="cluster", affected_sites=2).sample(
            seed=1,
            n_cycles=2,
            layout={"site_count": 3, "qubit_coords": [[0.0], [1.0]]},
        )


def test_phase_burst_per_site_payload_feeds_site_local_theta_without_averaging():
    timeline = PhaseBurstSource(
        site_count=3,
        event_times=(0,),
        peak_shift_mhz=-1.0,
        recovery_time_ns=1_000.0,
    ).sample(seed=9, n_cycles=3)

    params = timeline_to_site_coupled_params(timeline, payload_key="detuning_radns")
    assert len(params) == 3
    assert len(params[0]) == 3
    for cycle in range(3):
        for site in range(3):
            assert params[cycle][site].source_draw_for("detuning") == pytest.approx(
                timeline.payload_series("detuning_radns")[cycle, site]
            )


def test_temporal_storm_spp_exact_marginal_and_correlation_length_metadata():
    source = TemporalStormSPPSource(
        a=0.03,
        b=0.07,
        q_calm=(0.99, 0.005, 0.003, 0.002),
        q_storm=(0.7, 0.1, 0.1, 0.1),
        site_count=3,
        scope="global",
    )
    timeline = source.sample(seed=13, n_cycles=8000)
    marginal = source.marginal_distribution

    np.testing.assert_allclose(source.transition_matrix, np.asarray([[0.97, 0.03], [0.07, 0.93]]))
    assert source.stationary_distribution.tolist() == pytest.approx([0.7, 0.3])
    assert source.correlation_length_cycles == pytest.approx(-1.0 / math.log(0.9))
    assert marginal.tolist() == pytest.approx(0.7 * np.asarray(source.q_calm) + 0.3 * np.asarray(source.q_storm))

    emissions = timeline.payload_series("pauli_error")
    empirical_non_i = np.mean(emissions != 0)
    expected_non_i = 1.0 - marginal[0]
    assert empirical_non_i == pytest.approx(expected_non_i, abs=0.03)
    np.testing.assert_allclose(source.empirical_pauli_distribution(timeline), marginal, atol=0.02)
    np.testing.assert_allclose(source.empirical_transition_matrix(timeline), source.transition_matrix, atol=0.03)
    assert timeline.to_manifest()["metadata"]["boundary"] == "reduced_pauli_comparator_not_analog_truth"


def test_temporal_storm_fixed_marginal_family_changes_memory_not_one_cycle_distribution():
    marginal = (0.9, 0.04, 0.03, 0.03)
    q_storm = (0.7, 0.1, 0.1, 0.1)
    fast = TemporalStormSPPSource.from_fixed_marginal(
        marginal=marginal,
        q_storm=q_storm,
        storm_probability=0.2,
        correlation_length_cycles=4.0,
    )
    slow = TemporalStormSPPSource.from_fixed_marginal(
        marginal=marginal,
        q_storm=q_storm,
        storm_probability=0.2,
        correlation_length_cycles=20.0,
    )

    np.testing.assert_allclose(fast.marginal_distribution, marginal)
    np.testing.assert_allclose(slow.marginal_distribution, marginal)
    assert slow.correlation_length_cycles > fast.correlation_length_cycles


def test_temporal_storm_cluster_scope_marks_layout_cluster_only():
    source = TemporalStormSPPSource(
        a=0.02,
        b=0.02,
        q_calm=(1.0, 0.0, 0.0, 0.0),
        q_storm=(0.0, 1.0, 0.0, 0.0),
        site_count=4,
        scope="cluster",
        affected_sites=2,
    )
    layout = {
        "site_count": 4,
        "cluster_center": 0,
        "qubit_coords": {"0": [0.0, 0.0], "1": [10.0, 0.0], "2": [0.0, 1.0], "3": [10.0, 1.0]},
    }
    timeline = source.sample(seed=23, n_cycles=128, layout=layout)

    np.testing.assert_array_equal(timeline.payload_series("cluster_mask")[0], np.asarray([1, 0, 1, 0], dtype=np.int8))
    np.testing.assert_array_equal(timeline.latent_series("storm_state")[:, 1], np.zeros(128, dtype=np.int8))
    np.testing.assert_array_equal(timeline.latent_series("storm_state")[:, 3], np.zeros(128, dtype=np.int8))


def test_temporal_storm_rejects_cluster_footprint_larger_than_layout():
    source = TemporalStormSPPSource(scope="cluster", site_count=2, affected_sites=3)
    with pytest.raises(ValueError, match="affected_sites"):
        source.sample(seed=1, n_cycles=8)


def test_temporal_storm_empirical_pauli_distribution_rejects_invalid_labels():
    source = TemporalStormSPPSource()
    timeline = SourceTimeline(
        name="bad_pauli",
        n_cycles=2,
        cycle_time_ns=1_000.0,
        payload={"pauli_error": np.asarray([[0], [4]], dtype=np.int8), "storm_indicator": np.zeros((2, 1))},
        latent={"storm_state": np.zeros((2, 1), dtype=np.int8)},
    )
    with pytest.raises(ValueError, match="outside"):
        source.empirical_pauli_distribution(timeline)


def test_temporal_storm_baseline_breaks_lag_correlation_without_changing_marginal():
    source = TemporalStormSPPSource(a=0.02, b=0.02, q_calm=(1.0, 0.0, 0.0, 0.0), q_storm=(0.0, 1.0, 0.0, 0.0))
    timeline = source.sample(seed=17, n_cycles=6000)
    baseline = timeline.independent_baseline(seed=18, payload_keys=("storm_indicator", "pauli_error"))

    storm = timeline.payload_series("storm_indicator")[:, 0]
    storm_baseline = baseline.payload_series("storm_indicator")[:, 0]
    assert lag_autocorrelation(storm, lag=1) > 0.85
    assert abs(lag_autocorrelation(storm_baseline, lag=1)) < 0.08
    assert np.mean(storm_baseline) == pytest.approx(np.mean(storm))
    np.testing.assert_array_equal(
        np.sort(timeline.payload_series("pauli_error")[:, 0]),
        np.sort(baseline.payload_series("pauli_error")[:, 0]),
    )


def test_source_process_rejects_non_integral_integer_fields():
    with pytest.raises(ValueError, match="integer"):
        RTNSource().sample(seed=1, n_cycles=3.9)
    with pytest.raises(ValueError, match="integer"):
        PhaseBurstSource(site_count=3.1)


def test_source_timeline_can_feed_existing_theta_fanout():
    source = RTNSource(amplitude_radns=1.0e-5, gamma_per_cycle=0.0)
    timeline = source.sample(seed=19, n_cycles=4)
    params = timeline_to_coupled_params(timeline, SourceCouplingConfig(z_scale_radns=1.0e-4))

    assert len(params) == 4
    assert {p.coupling_mode for p in params} == {"shared"}
    assert {p.source_draw_for("detuning") for p in params} <= {-1.0e-5, 1.0e-5}
