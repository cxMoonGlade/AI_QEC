from __future__ import annotations

from pathlib import Path

import yaml

from google_s3_fixture import write_tiny_google_s3_dataset
from scope_static.experiments.willow_data.s3_visible_adapter_v2 import run_google_s3_visible_adapter_v2_from_config
from scope_static.google.s3_visible_surface_v2 import write_google_s3_visible_surface_v2
from scope_static.mechanism_discovery.artifacts import load_stage3a_frozen_visible_features
from scope_static.mechanism_discovery.discovery_model import learner_input_mask_audit


def test_google_s3_visible_adapter_v2_writes_public_signature_surface(tmp_path: Path) -> None:
    root = write_tiny_google_s3_dataset(tmp_path, contexts=3)
    output = tmp_path / "S3A_signature_protocol_freeze"

    result = write_google_s3_visible_surface_v2(
        dataset_root=root,
        output_dir=output,
        max_contexts=3,
        round_bands=("early", "mid", "late"),
        region_families=("boundary_adjacent", "logical_support_neighborhood", "interior_chain", "full_patch"),
        shotblocks_per_context=2,
        shotblock_size=2,
        min_shotblock_size=2,
        seed=0,
    )

    matrix, feature_names, manifest = load_stage3a_frozen_visible_features(output)
    assert result["decision"] == "google_s3_visible_surface_v2_passed"
    assert result["claim_boundary"]["single_window_row_surface"] is False
    assert result["claim_boundary"]["context_window_timeblock_primary_unit"] is False
    assert result["assignment_unit"]["j_definition"] == "google_public_syndrome_response_signature"
    assert result["forbidden_feature_audit"]["passed"] is True
    assert result["adequacy_report"]["passed"] is True
    assert result["split_manifest"]["train_validation_test_splits_non_empty"] is True
    assert matrix.shape == (12, len(feature_names))
    assert manifest["training_matrix_kind"] == "empirical_google_public_syndrome_response_signature_features"
    assert "raw__marginal__detector_rate_mean" in feature_names
    assert "raw__spatial_corr__nearest_neighbor_cov_mean" in feature_names
    assert "raw__temporal_corr__adjacent_round_cov_mean" in feature_names
    assert "raw__logical_coupling__detector_logical_cov_mean" in feature_names
    assert "raw__stability__context_repeated_detector_rate_variance" in feature_names
    assert "meta__public_geometry__region_logical_support" in feature_names
    assert "raw__google_window2__P00" not in feature_names
    assert not any("context_id" in name or "sample_id" in name or "path" in name for name in feature_names)
    mask = learner_input_mask_audit(feature_names, learner_input_profile="raw_multiview_only")
    assert mask["selected_feature_count"] == result["visible_feature_schema"]["raw_feature_count"]
    assert all(name.startswith("raw__") for name in mask["selected_feature_names"])

    for name in [
        "metrics.json",
        "config.yaml",
        "visible_features.npy",
        "sampled_visible_features.npy",
        "visible_feature_schema.json",
        "visible_feature_matrix.json",
        "split_manifest.json",
        "batch_context_schema.json",
        "probe_schedule_manifest.json",
        "signature_schedule_manifest.json",
        "forbidden_feature_audit.json",
        "assignment_unit.json",
        "adequacy_report.json",
        "summary.md",
    ]:
        assert (output / name).exists()


def test_google_s3_visible_adapter_v2_config_wrapper(tmp_path: Path) -> None:
    root = write_tiny_google_s3_dataset(tmp_path, contexts=3)
    output = tmp_path / "configured_v2"
    config = tmp_path / "adapter_v2.yaml"
    config.write_text(
        yaml.safe_dump(
            {
                "google_s3_visible_adapter_v2": {
                    "dataset_root": str(root),
                    "output_dir": str(output),
                    "max_contexts": 3,
                    "round_bands": ["early", "mid", "late"],
                    "region_families": ["boundary_adjacent", "logical_support_neighborhood", "full_patch"],
                    "shotblocks_per_context": 2,
                    "shotblock_size": 2,
                    "min_shotblock_size": 2,
                }
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    result = run_google_s3_visible_adapter_v2_from_config(config_path=config)

    assert result["decision"] == "google_s3_visible_surface_v2_passed"
    assert result["config"]["region_families"] == ["boundary_adjacent", "logical_support_neighborhood", "full_patch"]
    assert (output / "adequacy_report.json").exists()
