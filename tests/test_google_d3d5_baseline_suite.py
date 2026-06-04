from __future__ import annotations

from pathlib import Path

from scope_static.experiments.willow_data.d3d5_baselines import _config_from_mapping
from scope_static.google.baseline_suite import (
    ALLOWED_BASELINE_KEYS,
    BASELINE_KEYS,
    DECODER_BASELINES,
    EXTERNAL_ADAPTER_REQUIRED_BASELINES,
    BaselineSuiteConfig,
    _aggregate_leaf_results,
    _empty_metric_record,
    _external_adapter_missing_record,
    _metric_definitions,
    _run_scope_teacher_learner_latent_replay,
    _select_leaves,
)
from scope_static.google.inventory import GoogleLeaf


def test_google_d3d5_suite_covers_documented_baseline_families() -> None:
    assert set(DECODER_BASELINES) == {
        "dem_physics_prior_matching_si1000",
        "rl_optimized_prior_matching",
        "harmony_si1000",
        "harmony_rl_optimized",
    }
    assert {
        "independent_detector",
        "pairwise_ising",
        "factor_graph_crf",
        "graphical_lasso",
        "bayesian_hierarchical",
        "bernoulli_mixture_em",
        "sparse_coding_dictionary",
        "causal_discovery_structure",
        "vae",
        "gan",
        "ebm_rbm_crbm",
        "autoregressive_generative",
    } <= set(BASELINE_KEYS)
    assert "scope_teacher_learner_latent_replay" not in set(BASELINE_KEYS)
    assert "scope_teacher_learner_latent_replay" in set(ALLOWED_BASELINE_KEYS)
    assert "pairwise_ising" in EXTERNAL_ADAPTER_REQUIRED_BASELINES


def test_google_d3d5_metric_definitions_include_no_label_metrics() -> None:
    definitions = _metric_definitions()

    assert "logical_p_L" in definitions
    assert "syndrome_first_moment_mae" in definitions
    assert "two_sample_auc" in definitions
    assert "dem_f1" in definitions
    assert "strength_spearman" in definitions
    assert "external_baseline_policy" in definitions


def test_external_baseline_records_do_not_use_native_proxy() -> None:
    record = _external_adapter_missing_record("pairwise_ising")

    assert record["baseline_key"] == "pairwise_ising"
    assert record["implementation_status"] == "not_run_external_adapter_missing"
    assert record["runner_policy"] == "official_or_cloned_upstream_only_no_native_proxy"
    assert record["syndrome_nll_per_shot"] is None
    assert record["external_repositories"]
    assert "native" not in record["implementation_status"]


def test_google_d3d5_aggregate_marks_google_no_label_metrics_not_applicable() -> None:
    baselines = {}
    for key in BASELINE_KEYS:
        record = _empty_metric_record(key, implementation_status="test")
        record["logical_p_L"] = 0.1
        baselines[key] = record
    result = _aggregate_leaf_results(
        [
            {
                "rounds": 1,
                "actual_logical_rate_test": 0.2,
                "baselines": baselines,
            }
        ]
    )

    for key in BASELINE_KEYS:
        metrics = result[key]["metrics"]
        assert metrics["dem_f1"]["status"] == "not_applicable_google_no_ground_truth_mechanism_labels"
        assert metrics["strength_spearman"]["status"] == "not_applicable_google_no_ground_truth_strength_labels"
        assert metrics["cross_decoding_delta_p_L_vs_matching_si1000"]["status"].startswith("not_run")


def test_google_d3d5_config_loader_parses_yaml_shape() -> None:
    cfg = _config_from_mapping(
        {
            "dataset_root": "/tmp/google",
            "dataset_name": "google_72Q_surface_code_d3_d5_set1",
            "output_dir": "outputs/test",
            "distances": [3, 5],
            "bases": ["X", "Z"],
            "rounds": [1, 10],
            "max_leaves_per_distance_basis": 1,
            "max_shots_per_leaf": 128,
            "detector_limit": 8,
        }
    )

    assert isinstance(cfg, BaselineSuiteConfig)
    assert cfg.dataset_root == Path("/tmp/google")
    assert cfg.distances == (3, 5)
    assert cfg.bases == ("X", "Z")
    assert cfg.rounds == (1, 10)
    assert cfg.max_shots_per_leaf == 128


def test_scope_teacher_learner_adapter_reports_comparable_google_metrics() -> None:
    metrics = _run_scope_teacher_learner_latent_replay(
        x_train=[
            [0, 0, 1],
            [0, 1, 1],
            [1, 0, 0],
            [1, 1, 0],
        ],
        y_train=[0, 0, 1, 1],
        x_test=[
            [0, 1, 1],
            [1, 0, 0],
        ],
        y_test=[0, 1],
        context={},
        cfg=BaselineSuiteConfig(mixture_components=2, max_iter=5),
        seed=0,
        baseline_params={"prototype_count": 2, "max_iter": 5},
    )

    assert metrics["baseline_key"] == "scope_teacher_learner_latent_replay"
    assert metrics["implementation_status"] == "native_scope_teacher_learner_adapter"
    assert metrics["syndrome_nll_per_shot"] is not None
    assert metrics["syndrome_first_moment_mae"] is not None
    assert metrics["two_sample_auc"] is not None
    assert metrics["logical_p_L"] is None
    assert metrics["structural_summary"]["uses_google_true_mechanism_labels"] is False
    assert metrics["structural_summary"]["uses_observable_flips_for_detector_prototypes"] is False
    assert metrics["structural_summary"]["logical_p_l_status"] == "not_reported_not_a_decoder"


def test_google_d3d5_leaf_selection_covers_each_configured_round(monkeypatch) -> None:
    leaves = [
        _fake_leaf(distance=3, basis="X", rounds=1, index=0),
        _fake_leaf(distance=3, basis="X", rounds=1, index=1),
        _fake_leaf(distance=3, basis="X", rounds=10, index=0),
        _fake_leaf(distance=3, basis="X", rounds=10, index=1),
    ]
    monkeypatch.setattr("scope_static.google.baseline_suite.iter_google_leaves", lambda *_args, **_kwargs: leaves)

    selected = _select_leaves(
        BaselineSuiteConfig(
            dataset_root=Path("/tmp/google"),
            distances=(3,),
            bases=("X",),
            rounds=(1, 10),
            max_leaves_per_distance_basis=2,
        )
    )

    assert [leaf.rounds for leaf in selected] == [1, 10]


def _fake_leaf(*, distance: int, basis: str, rounds: int, index: int) -> GoogleLeaf:
    path = Path(f"/tmp/{distance}/{basis}/{rounds}/{index}")
    return GoogleLeaf(
        dataset_name="google_72Q_surface_code_d3_d5_set1",
        dataset_family="surface_code",
        root=Path("/tmp/google"),
        path=path,
        context_id=f"d{distance}_{basis}_r{rounds}_{index}",
        sample_id=f"sample_{index:02d}",
        sample_index=index,
        patch_id="patch",
        basis=basis,
        distance=distance,
        rounds=rounds,
        rounds_label=f"r{rounds:02d}",
        shots=100,
        circuit_ideal=path / "circuit_ideal.stim",
        circuit_noisy_si1000=path / "circuit_noisy_si1000.stim",
        measurements=path / "measurements.b8",
        sweep_bits=path / "sweep_bits.b8",
        detection_events=path / "detection_events.b8",
        obs_flips_actual=path / "obs_flips_actual.b8",
        metadata=path / "metadata.json",
    )
