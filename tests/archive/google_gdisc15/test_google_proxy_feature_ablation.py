from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.skip(reason="archived Google GDISC15 diagnostic stack")

from scope_static.archive.experiments.google_gdisc15 import proxy_feature_ablation
from scope_static.archive.experiments.google_gdisc15.gdisc15b_grid import PRIMARY_METRIC


def test_google_proxy_feature_ablation_writes_requested_artifacts(monkeypatch, tmp_path: Path):
    seen = []

    def fake_grid_main(argv):
        assert "--native-gpu" in argv
        assert argv[argv.index("--candidate-family") + 1] == "proxy_profiles"
        assert argv[argv.index("--context-workers") + 1] == "2"
        assert argv[argv.index("--torch-num-threads") + 1] == "3"
        assert argv[argv.index("--prepared-cache-dir") + 1].endswith("prepared_cache")
        assert "--skip-reference-priors" in argv
        assert "--skip-local-correlation-metrics" in argv
        feature_profiles = [
            item.strip()
            for item in argv[argv.index("--proxy-feature-profiles") + 1].split(",")
            if item.strip()
        ]
        window_profile = argv[argv.index("--eval-window-plan-mode") + 1]
        output = Path(argv[argv.index("--output-dir") + 1])
        context = {
            "dataset_name": "google_72Q_surface_code_d3_d5_set1",
            "dataset_family": "surface",
            "context_id": f"ctx_{window_profile}",
            "sample_id": "sample_01",
            "patch_id": "d3_at_q5_5",
            "basis": "X",
            "rounds_label": "r13",
            "output_root": str(output / "ctx"),
        }
        metrics_dir = Path(context["output_root"]) / "GDISC15_real_local_mechanism_discovery"
        metrics_dir.mkdir(parents=True, exist_ok=True)
        (metrics_dir / "metrics.json").write_text(
            json.dumps(
                {
                    "preprocessing_feature_audit": {
                        "profiles": {
                            profile: {
                                "feature_count": 3 + (1 if profile == "fg_only" else 3),
                                "nonzero_feature_count": 2 + (1 if profile == "fg_only" else 3),
                                "constant_feature_count": 1,
                                "feature_rank": 1 if profile == "fg_only" else 3,
                                "missing_feature_count": 0,
                                "forbidden_label_audit": {"passed": True, "hits": []},
                            }
                            for profile in feature_profiles
                        }
                    },
                    "window_audit": {
                        "eval_window_audit": {
                            "window_plan_mode": window_profile,
                            "num_windows": 8,
                            "mean_window_bits": 2.5,
                            "max_window_bits": 4,
                            "window_family_counts": {"single_detector": 2, "logical_fault_support": 2},
                            "detector_logical_bit_coverage": {"fraction_bits_covered": 0.5},
                            "num_windows_containing_logical": 2,
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        base = 0.10
        window_gain = -0.01 if window_profile == "balanced_structured" else 0.0
        records = [
            _record(context, "local_full", 0.11),
            _record(context, "dmle_qec", 0.12),
        ]
        for feature_profile in feature_profiles:
            rank = 1 if feature_profile == "fg_only" else 3
            profile_gain = -0.02 if feature_profile != "fg_only" else 0.0
            score = base + profile_gain + window_gain
            records.append(
                _record(
                    context,
                    f"GDISC15_proxy_{feature_profile}",
                    score,
                    {
                        "proxy_feature_profile": feature_profile,
                        "proxy_feature_device": "cuda:0",
                        "proxy_feature_count": 3 + rank,
                        "proxy_feature_rank": rank,
                        "proxy_constant_feature_count": 1,
                        "proxy_missing_feature_count": 0,
                    },
                )
            )
        seen.append((window_profile, tuple(feature_profiles)))
        return {
            "grid": {"completed_contexts": [context], "skipped_contexts": []},
            "flat_records": records,
            "model_summary": [],
        }

    monkeypatch.setattr(proxy_feature_ablation.gdisc15b_grid, "main", fake_grid_main)

    result = proxy_feature_ablation.main(
        [
            "--config",
            str(tmp_path / "missing.yaml"),
            "--proxy-feature-profiles",
            "fg_only,fg_support",
            "--window-profiles",
            "current_structured,balanced_structured",
            "--max-contexts",
            "1",
            "--context-workers",
            "2",
            "--torch-num-threads",
            "3",
            "--output-dir",
            str(tmp_path / "ablation"),
        ]
    )

    assert len(seen) == 2
    assert seen == [
        ("current_structured", ("fg_only", "fg_support")),
        ("balanced_structured", ("fg_only", "fg_support")),
    ]
    assert result["run"]["name"] == "Google_proxy_feature_ablation"
    for name in [
        "preprocessing_feature_ablation.csv",
        "preprocessing_feature_audit.json",
        "window_profile_audit.json",
        "paired_structure_lift.csv",
        "proxy_feature_leaderboard.md",
        "claim_summary.md",
    ]:
        assert (tmp_path / "ablation" / name).exists()
    paired = (tmp_path / "ablation" / "paired_structure_lift.csv").read_text(encoding="utf-8")
    assert "delta_vs_fg_only" in paired
    assert "fg_support" in paired
    claim = (tmp_path / "ablation" / "claim_summary.md").read_text(encoding="utf-8")
    assert "Forbidden-label audit passed" in claim


def _record(context: dict[str, object], model: str, nll: float, extra: dict[str, object] | None = None) -> dict[str, object]:
    return {
        **context,
        "model": model,
        "parameter_count": 10,
        PRIMARY_METRIC: nll,
        "heldout_local_window_excess_nll": nll + 0.01,
        "detector_rate_mae": nll / 10,
        "local_correlation_error": nll / 20,
        "logical_flip_rate_calibration": nll / 30,
        **(extra or {}),
    }
