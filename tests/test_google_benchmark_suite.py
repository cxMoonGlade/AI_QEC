from __future__ import annotations

import json
from pathlib import Path

from scope_static.experiments.willow_data import benchmark_suite
from scope_static.experiments.willow_data.gdisc15b_grid import PRIMARY_METRIC
from scope_static.google.inventory import (
    DATASET_105Q,
    DATASET_REPETITION_D29,
    DATASET_SURFACE_SET1,
    DATASET_SURFACE_SET2,
    EXPECTED_LEAF_COUNTS,
)


def test_google_benchmark_suite_b0_writes_audit_lock(monkeypatch, tmp_path: Path):
    def fake_inventory(*, output_dir, dataset_roots, dataset_names, dem_proxy_mode):
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        context_path = output / "google_context_manifest.jsonl"
        decoder_path = output / "google_decoder_manifest.jsonl"
        label_path = output / "google_label_manifest.json"
        audit_path = output / "google_preprocessing_audit.json"
        context_path.write_text("", encoding="utf-8")
        decoder_path.write_text("", encoding="utf-8")
        label_path.write_text(
            json.dumps(
                {
                    "label_layers": {
                        "context_labels": ["dataset_name"],
                        "strong_shot_labels": ["obs_flips_actual"],
                        "decoder_labels": ["decoder_family"],
                        "dem_proxy_labels": ["support_size"],
                        "forbidden_true_labels": [],
                    }
                }
            ),
            encoding="utf-8",
        )
        audit = {
            "missing_roots": {},
            "datasets": {
                name: {
                    "num_leaves": EXPECTED_LEAF_COUNTS[name],
                    "expected_leaves": EXPECTED_LEAF_COUNTS[name],
                    "leaf_count_matches_observed_inventory": True,
                }
                for name in dataset_names
            },
            "decoder_coverage": {},
        }
        audit_path.write_text(json.dumps(audit), encoding="utf-8")
        return {
            "context_manifest_path": str(context_path),
            "decoder_manifest_path": str(decoder_path),
            "label_manifest_path": str(label_path),
            "audit_path": str(audit_path),
            "num_contexts": sum(EXPECTED_LEAF_COUNTS[name] for name in dataset_names),
            "num_decoder_rows": 0,
            "audit": audit,
        }

    monkeypatch.setattr(benchmark_suite, "write_google_inventory_artifacts", fake_inventory)
    monkeypatch.setattr(
        benchmark_suite,
        "_b0_eval_window_audit",
        lambda _cfg: {
            "available": True,
            "eval_window_audit": {
                "window_plan_mode": "structured_higher_order",
                "max_window_bits": 6,
                "window_family_counts": {"logical_fault_support": 4},
                "window_size_distribution": {"4": 4},
            },
        },
    )
    config = _write_config(
        tmp_path,
        {
            "suite": {"benchmarks": "B0"},
            "inventory": {"datasets": DATASET_SURFACE_SET1, "dem_proxy_mode": "none"},
        },
    )

    result = benchmark_suite.main(["--config", str(config), "--output-dir", str(tmp_path / "suite")])

    b0 = json.loads((tmp_path / "suite" / "B0" / "run_manifest.json").read_text())
    assert result["benchmarks"]["B0"]["result"]["passed"] is True
    assert b0["checks"]["expected_leaf_counts"]["passed"] is True
    assert b0["checks"]["structured_eval_windows"]["passed"] is True
    assert (tmp_path / "suite" / "B0" / "preprocessing_audit.json").exists()
    assert (tmp_path / "suite" / "B0" / "eval_window_audit.json").exists()


def test_google_benchmark_suite_b1_b2_orchestrates_gpu_grid(monkeypatch, tmp_path: Path):
    seen_shots = []

    def fake_grid_main(argv):
        assert "--native-gpu" in argv
        assert argv[argv.index("--eval-window-plan-mode") + 1] == "structured_higher_order"
        train_shots = int(argv[argv.index("--train-shots") + 1])
        seen_shots.append(train_shots)
        output = Path(argv[argv.index("--output-dir") + 1])
        context = _fake_context(output, sample_id="sample_01", basis="X")
        _write_context_metrics(context)
        flat_records = [
            _record(context, "local_full", 0.14 - train_shots * 1e-5, 100),
            _record(context, "dmle_qec", 0.12 - train_shots * 1e-5, 100),
            _record(context, "global_shared_scalar", 0.30, 1),
            _record(context, "GDISC15_local_logit", 0.10 - train_shots * 1e-5, 10),
            _record(context, "GDISC15_random_low_rank1_seed0", 0.25, 10),
        ]
        return {
            "run": {"name": "fake_grid"},
            "grid": {"completed_contexts": [context], "skipped_contexts": []},
            "flat_records": flat_records,
            "model_summary": [{"model": "GDISC15_local_logit", "n": 1}],
        }

    monkeypatch.setattr(benchmark_suite.gdisc15b_grid, "main", fake_grid_main)
    config = _write_config(
        tmp_path,
        {
            "suite": {"benchmarks": "B1,B2"},
            "B1": {"grid": {"samples": "sample_01", "max_contexts": 1}},
            "B2": {"train_shot_grid": "128,4096", "heldout_shots": 4096, "grid": {"samples": "sample_01", "max_contexts": 1}},
        },
    )

    benchmark_suite.main(["--config", str(config), "--output-dir", str(tmp_path / "suite"), "--benchmarks", "B1,B2"])

    assert 4096 in seen_shots
    assert 128 in seen_shots
    assert (tmp_path / "suite" / "B1" / "context_scorecard.json").exists()
    sample_efficiency = json.loads((tmp_path / "suite" / "B2" / "sample_efficiency.json").read_text())
    assert sample_efficiency["primary_metric"] == PRIMARY_METRIC
    assert sample_efficiency["train_shot_grid"] == [128, 4096]
    assert any(row["model"] == "GDISC15_local_logit" for row in sample_efficiency["curves"])


def test_google_benchmark_suite_b3_transfer_and_pending_later_rungs(monkeypatch, tmp_path: Path):
    def fake_static_main(argv):
        assert "--native-gpu" in argv
        output = Path(argv[argv.index("--output-dir") + 1])
        output.mkdir(parents=True, exist_ok=True)
        return {
            "records": [
                {"model": "local", "parameter_count": 100, PRIMARY_METRIC: 0.11, "detector_rate_mae": 0.01},
                {"model": "dmle_qec", "parameter_count": 100, PRIMARY_METRIC: 0.13, "detector_rate_mae": 0.02},
                {"model": "hard_orbit", "parameter_count": 12, PRIMARY_METRIC: 0.10, "detector_rate_mae": 0.01},
            ],
            "cross_sample_transfer_records": [
                {
                    "sample_id": "sample_02",
                    "model": "hard_orbit",
                    "transfer_evaluated": True,
                    PRIMARY_METRIC: 0.12,
                    "detector_rate_mae": 0.01,
                    "logical_flip_rate_calibration": 0.02,
                }
            ],
            "window_audits": [{"eval_window_audit": {"max_window_bits": 6}}],
        }

    monkeypatch.setattr(benchmark_suite.run_google_static, "main", fake_static_main)
    config = _write_config(
        tmp_path,
        {
            "suite": {"benchmarks": "B3,B4"},
            "B3": {
                "transfer": {
                    "source_samples": "sample_00",
                    "target_sample_start": 2,
                    "target_sample_stop": 2,
                    "patches": "d3_at_q5_5",
                    "bases": "X",
                    "rounds_labels": "r13",
                }
            },
        },
    )

    benchmark_suite.main(["--config", str(config), "--output-dir", str(tmp_path / "suite"), "--benchmarks", "B3,B4"])

    transfer = json.loads((tmp_path / "suite" / "B3" / "transfer_scorecard.json").read_text())
    pending = json.loads((tmp_path / "suite" / "B4" / "transfer_scorecard.json").read_text())
    assert transfer["source_fit_transfer_mode"] == "single_source_fit"
    assert transfer["target_fit_dmle_upper_comparator_available"] is False
    assert pending["implemented"] is False
    assert pending["dataset_name"] == DATASET_SURFACE_SET2


def _write_config(tmp_path: Path, overrides: dict[str, object]) -> Path:
    base = {
        "suite": {"benchmarks": "B0"},
        "inventory": {
            "datasets": ",".join((DATASET_REPETITION_D29, DATASET_SURFACE_SET1, DATASET_SURFACE_SET2, DATASET_105Q)),
            "dem_proxy_mode": "none",
        },
        "common_grid": {
            "dataset_root": str(tmp_path / "google_72Q_surface_code_d3_d5_set1"),
            "samples": "sample_01",
            "patches": "d3_at_q5_5",
            "bases": "X",
            "rounds_labels": "r13",
            "heldout_split_types": "shot-heldout",
            "train_shots": 4096,
            "heldout_shots": 4096,
            "steps": 1,
            "max_windows": 8,
            "max_window_bits": 8,
            "detector_pair_window_budget": 4,
            "logical_detector_pair_window_budget": 4,
            "window_plan_mode": "logical_aware",
            "eval_window_plan_mode": "structured_higher_order",
            "eval_max_window_bits": 6,
            "eval_max_windows": 32,
            "eval_radius": 1.0,
            "eval_template_window_budget": 4,
            "eval_orbit_window_budget": 4,
            "pca_ranks": "1",
            "random_control_ranks": "1",
            "random_control_seeds": "0",
            "nmf_steps": 1,
            "kmeans_max_iter": 1,
            "include_upstream_dmle": False,
            "dtype": "float64",
            "likelihood_backend": "auto",
            "cuda_kernel_variant": "dp",
            "spectral_memory_cap_mib": 64,
            "disable_prepared_cache": False,
        },
    }
    _deep_update(base, overrides)
    path = tmp_path / "suite.yaml"
    path.write_text(json.dumps({"google_benchmark_suite_v1": base}), encoding="utf-8")
    return path


def _deep_update(target: dict[str, object], updates: dict[str, object]) -> None:
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_update(target[key], value)  # type: ignore[arg-type]
        else:
            target[key] = value


def _fake_context(output: Path, *, sample_id: str, basis: str) -> dict[str, object]:
    return {
        "dataset_name": DATASET_SURFACE_SET1,
        "dataset_family": "surface",
        "context_id": f"ctx_{sample_id}_{basis}",
        "sample_id": sample_id,
        "sample_index": 1,
        "patch_id": "d3_at_q5_5",
        "basis": basis,
        "rounds": 13,
        "rounds_label": "r13",
        "distance": 3,
        "decoder_pathway": "correlated_matching_decoder_with_si1000_prior",
        "heldout_split_type": "shot-heldout",
        "output_root": str(output / f"ctx_{sample_id}_{basis}"),
    }


def _write_context_metrics(context: dict[str, object]) -> None:
    metrics_dir = Path(str(context["output_root"])) / "GDISC15_real_local_mechanism_discovery"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    (metrics_dir / "metrics.json").write_text(
        json.dumps({"window_audit": {"eval_window_audit": {"window_plan_mode": "structured_higher_order", "max_window_bits": 6}}}),
        encoding="utf-8",
    )


def _record(context: dict[str, object], model: str, nll: float, params: int) -> dict[str, object]:
    return {
        **context,
        "model": model,
        "parameter_count": params,
        "baseline_family": "dmle_qec" if model == "dmle_qec" else None,
        "heldout_eval_window_nll": nll + 0.01,
        "heldout_eval_window_empirical_entropy": 0.01,
        "heldout_eval_window_excess_nll": nll,
        "heldout_local_window_nll": nll + 0.02,
        "heldout_local_window_excess_nll": nll + 0.01,
        "detector_rate_mae": nll / 10,
        "local_correlation_error": nll / 20,
        "logical_flip_rate_calibration": nll / 30,
    }
