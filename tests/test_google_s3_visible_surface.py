from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import stim

from scope_static.google.set1 import DATASET_NAME
from scope_static.google.s3_visible_surface import write_google_s3_visible_surface
from scope_static.mechanism_discovery.artifacts import load_stage3a_frozen_visible_features
from scope_static.mechanism_discovery.discovery_model import run_stage3b1_first_discovery_model
from scope_static.mechanism_discovery.generator_learning import run_stage3c_prototype_generator_learning
from scope_static.experiments.willow_data.s3_visible_adapter import run_google_s3_visible_adapter_from_config


def test_google_s3_visible_adapter_writes_stage3a_real_surface(tmp_path: Path) -> None:
    root = _write_google_fixture(tmp_path)
    output = tmp_path / "S3A_protocol_freeze"

    result = write_google_s3_visible_surface(
        dataset_root=root,
        output_dir=output,
        max_contexts=3,
        windows_per_context=1,
        shotblocks_per_context=2,
        shotblock_size=2,
        min_shotblock_size=2,
        seed=0,
    )

    assert result["decision"] == "google_s3_visible_surface_passed"
    assert result["claim_boundary"]["constructs_counterfactual_teacher_probes"] is False
    assert result["claim_boundary"]["contains_context_path_sample_one_hot_features"] is False
    assert result["assignment_unit"]["j_definition"] == "google_context_window_shotblock_instance"
    assert result["assignment_unit"]["single_shot_j_allowed_first_pass"] is False
    assert result["forbidden_feature_audit"]["passed"] is True
    assert result["split_manifest"]["train_validation_test_splits_non_empty"] is True
    assert result["batch_context_schema"]["primary_protocol"]["mode"] == "google_real_context_window_shotblock_batch"

    matrix, feature_names, manifest = load_stage3a_frozen_visible_features(output)
    assert matrix.shape == (6, len(feature_names))
    assert manifest["loaded_from_stage3a_artifact"] is True
    assert "raw__google_window2__P00" in feature_names
    assert "raw__google_window2__P11" in feature_names
    assert "raw__google_window2__p_comp" in feature_names
    assert "visible_metadata__window_kind_logical_detector_pair" in feature_names
    assert not any("context_id" in name or "sample_id" in name or "path" in name for name in feature_names)

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
        "forbidden_feature_audit.json",
        "assignment_unit.json",
        "summary.md",
    ]:
        assert (output / name).exists()


def test_google_s3_visible_adapter_writes_window_bundle_surface(tmp_path: Path) -> None:
    root = _write_google_fixture(tmp_path)
    output = tmp_path / "S3A_bundle_protocol_freeze"

    result = write_google_s3_visible_surface(
        dataset_root=root,
        output_dir=output,
        max_contexts=3,
        windows_per_context=2,
        window_bundle_size=2,
        shotblocks_per_context=2,
        shotblock_size=2,
        min_shotblock_size=2,
        seed=0,
    )

    matrix, feature_names, _manifest = load_stage3a_frozen_visible_features(output)
    assert result["decision"] == "google_s3_visible_surface_passed"
    assert result["assignment_unit"]["j_definition"] == "google_context_windowbundle_shotblock_instance"
    assert result["assignment_unit"]["expected_categorical_population_group_count_per_row"] == 2
    assert result["batch_context_schema"]["primary_protocol"]["mode"] == "google_real_context_windowbundle_shotblock_batch"
    assert result["probe_schedule_manifest"]["window_bundle_size"] == 2
    assert result["probe_schedule_manifest"]["window_family_profile"] == "mixed_public"
    assert result["visible_feature_schema"]["window_bundle_size"] == 2
    assert matrix.shape == (6, len(feature_names))
    assert "raw__google_window2_bundle_w00__P00" in feature_names
    assert "raw__google_window2_bundle_w01__P11" in feature_names
    assert "visible_metadata__window_bundle_size" in feature_names
    assert "raw__google_window2__P00" not in feature_names


def test_google_s3_visible_adapter_filters_window_family_profile(tmp_path: Path) -> None:
    root = _write_google_fixture(tmp_path)
    output = tmp_path / "S3A_logical_only"

    result = write_google_s3_visible_surface(
        dataset_root=root,
        output_dir=output,
        max_contexts=3,
        windows_per_context=2,
        window_bundle_size=2,
        window_family_profile="logical_detector_pair_only",
        shotblocks_per_context=2,
        shotblock_size=2,
        min_shotblock_size=2,
        seed=0,
    )

    schedule = result["probe_schedule_manifest"]
    assert result["decision"] == "google_s3_visible_surface_passed"
    assert schedule["window_family_profile"] == "logical_detector_pair_only"
    assert schedule["window_kind_counts"] == {"logical_detector_pair": 12}
    assert schedule["window_source_counts"] == {"logical_detector_pair": 12}
    assert all(
        set(row["source_kinds"]) == {"logical_detector_pair"}
        for row in schedule["examples"]
    )


def test_google_s3_visible_adapter_config_wrapper(tmp_path: Path) -> None:
    root = _write_google_fixture(tmp_path)
    output = tmp_path / "configured"
    config = tmp_path / "google_s3.yaml"
    config.write_text(
        "\n".join(
            [
                "google_s3_visible_adapter_v1:",
                f"  dataset_root: {root}",
                f"  output_dir: {output}",
                "  max_contexts: 3",
                "  windows_per_context: 1",
                "  window_family_profile: detector_pair_only",
                "  shotblocks_per_context: 2",
                "  shotblock_size: 2",
                "  min_shotblock_size: 2",
            ]
        )
        + "\n"
    )

    result = run_google_s3_visible_adapter_from_config(config_path=config)

    assert result["decision"] == "google_s3_visible_surface_passed"
    assert result["config"]["window_family_profile"] == "detector_pair_only"
    assert (output / "visible_features.npy").exists()


def test_no_oracle_stage3b1_and_stage3c_consume_google_visible_surface(tmp_path: Path) -> None:
    root = _write_google_fixture(tmp_path)
    s3a = tmp_path / "S3A_protocol_freeze"
    s3b1 = tmp_path / "S3B1"
    s3c = tmp_path / "S3C"
    write_google_s3_visible_surface(
        dataset_root=root,
        output_dir=s3a,
        max_contexts=3,
        windows_per_context=1,
        shotblocks_per_context=2,
        shotblock_size=2,
        min_shotblock_size=2,
        seed=0,
    )

    b1 = run_stage3b1_first_discovery_model(
        stage3a_dir=s3a,
        output_dir=s3b1,
        evaluator_mode="no_oracle_labels",
        k_values=[2],
        max_iter=8,
    )

    assert b1["decision"] == "stage3b1_first_discovery_model_completed"
    assert b1["config"]["evaluator_mode"] == "no_oracle_labels"
    assert b1["claim_boundary"]["oracle_label_metrics_skipped"] is True
    assert b1["evaluator_only_label_metrics"]["selected_model_exact_metrics"]["skipped"] is True
    assert b1["acceptance_audit"]["checks"]["oracle_label_metrics_skipped_in_no_oracle_mode"] is True
    assert np.load(s3b1 / "learned_assignments.npy").shape == (6, 2)

    c = run_stage3c_prototype_generator_learning(
        stage3a_dir=s3a,
        stage3b1_dir=s3b1,
        output_dir=s3c,
        evaluator_mode="no_oracle_labels",
    )

    predicted = c["predicted_assignment_metrics"]["overall"]
    assert c["decision"] == "stage3c_prototype_generator_learning_completed"
    assert c["claim_boundary"]["oracle_assignment_comparator_skipped"] is True
    assert c["oracle_assignment_comparator_metrics"]["skipped"] is True
    assert c["acceptance_audit"]["checks"]["categorical_population_group_count_positive"] is True
    assert predicted["categorical_population_group_count"] > 0
    assert c["prototype_generation_metrics"]["global_null_lift"]["categorical_population_nll_reduction"] > 0.0
    assert c["prototype_generation_metrics"]["mean_only_lift"]["raw_visible_feature_mae_reduction"] > 0.0


def test_stage3b1_learner_input_profile_masks_assignment_but_s3c_scores_full_target(tmp_path: Path) -> None:
    root = _write_google_fixture(tmp_path)
    s3a = tmp_path / "S3A_bundle_protocol_freeze"
    s3b1 = tmp_path / "S3B1_raw_population_only"
    s3c = tmp_path / "S3C_full_target"
    write_google_s3_visible_surface(
        dataset_root=root,
        output_dir=s3a,
        max_contexts=3,
        windows_per_context=2,
        window_bundle_size=2,
        shotblocks_per_context=2,
        shotblock_size=2,
        min_shotblock_size=2,
        seed=0,
    )
    matrix, feature_names, _manifest = load_stage3a_frozen_visible_features(s3a)

    b1 = run_stage3b1_first_discovery_model(
        stage3a_dir=s3a,
        output_dir=s3b1,
        evaluator_mode="no_oracle_labels",
        k_values=[2],
        max_iter=8,
        learner_input_profile="raw_population_only",
    )

    audit = b1["learner_input_mask_audit"]
    assert audit["learner_input_profile"] == "raw_population_only"
    assert audit["training_matrix_for_assignment"] == "masked view of Stage 3A frozen visible_features.npy"
    assert audit["generation_target_matrix"] == "full Stage 3A frozen visible_features.npy"
    assert audit["full_feature_count"] == len(feature_names)
    assert audit["selected_feature_count"] == 10
    assert audit["selected_feature_kind_counts"]["raw_population"] == 10
    assert b1["visible_feature_matrix"]["feature_count"] == matrix.shape[1]
    assert b1["learned_prototypes"]["feature_names"] == audit["selected_feature_names"]
    assert (s3b1 / "learner_input_mask_audit.json").exists()

    c = run_stage3c_prototype_generator_learning(
        stage3a_dir=s3a,
        stage3b1_dir=s3b1,
        output_dir=s3c,
        evaluator_mode="no_oracle_labels",
    )

    assert c["visible_feature_matrix"]["feature_count"] == matrix.shape[1]
    assert c["predicted_assignment_metrics"]["overall"]["categorical_population_group_count"] == 2


def _write_google_fixture(tmp_path: Path) -> Path:
    outer = tmp_path / DATASET_NAME
    root = outer / DATASET_NAME
    for sample in range(3):
        _write_leaf(root / f"sample_{sample:02d}" / "d3_at_q5_5" / "X" / "r13")
    return outer


def _write_leaf(leaf: Path) -> None:
    decoder = leaf / "decoding_results" / "correlated_matching_decoder_with_si1000_prior"
    decoder.mkdir(parents=True, exist_ok=True)
    circuit = stim.Circuit(
        """
        QUBIT_COORDS(0, 0) 0
        QUBIT_COORDS(1, 0) 1
        R 0 1
        TICK
        CX sweep[0] 0
        TICK
        M 0 1
        DETECTOR(0, 0, 0) rec[-2]
        DETECTOR(1, 0, 0) rec[-1]
        OBSERVABLE_INCLUDE(0) rec[-1]
        """
    )
    (leaf / "circuit_ideal.stim").write_text(str(circuit), encoding="utf-8")
    (leaf / "circuit_noisy_si1000.stim").write_text(str(circuit), encoding="utf-8")
    metadata = {
        "basis": "X",
        "distance": 3,
        "rounds": 13,
        "shots": 4,
        "data_qubit_coords": [[0, 0]],
        "meas_qubit_coords": [[1, 0]],
    }
    (leaf / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    _write_b8(leaf / "detection_events.b8", [[0, 0], [0, 1], [1, 0], [1, 1]])
    _write_b8(leaf / "obs_flips_actual.b8", [[0], [0], [1], [1]])
    _write_b8(leaf / "measurements.b8", [[0, 0], [0, 1], [1, 0], [1, 1]])
    _write_b8(leaf / "sweep_bits.b8", [[0], [1], [0], [1]])
    _write_b8(decoder / "obs_flips_predicted.b8", [[0], [0], [1], [1]])
    (decoder / "error_model.dem").write_text("error(0.1) D0 D1\nerror(0.1) D0 L0\nerror(0.1) D1 L0\n", encoding="utf-8")


def _write_b8(path: Path, rows: list[list[int]]) -> None:
    data = np.array(rows, dtype=np.bool_)
    stim.write_shot_data_file(path=str(path), data=data, format="b8", num_measurements=data.shape[1])
