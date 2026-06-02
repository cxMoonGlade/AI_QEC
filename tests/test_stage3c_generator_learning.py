from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from scope_static.experiments.stage3.generator_learning import run_stage3c_generator_learning_from_config
from scope_static.primitives.mechanism_catalog import MECHANISM_NAMES
from scope_static.mechanism_discovery.protocol_freeze import run_stage3a_dataset_protocol_freeze
from scope_static.mechanism_discovery.observability_ceiling import run_stage3a5_observability_alias_ceiling
from scope_static.mechanism_discovery.artifacts import matrix_digest
from scope_static.mechanism_discovery.discovery_model import EVALUATOR_MODE_NO_ORACLE_LABELS
from scope_static.mechanism_discovery.discovery_model import run_stage3b1_first_discovery_model
from scope_static.mechanism_discovery.generator_learning import run_stage3c_prototype_generator_learning


def test_stage3c_scores_predicted_assignment_generator_against_nulls_and_oracle(tmp_path: Path) -> None:
    _teacher, s3a, s3a5, s3b1 = _prepare_artifacts(
        tmp_path,
        [
            ("M0", "M0"),
            ("M4", "M4"),
            ("M8", "M8"),
        ],
    )
    output = tmp_path / "S3C"

    result = run_stage3c_prototype_generator_learning(stage3a_dir=s3a, stage3a5_dir=s3a5, stage3b1_dir=s3b1, output_dir=output)

    assert result["decision"] == "stage3c_prototype_generator_learning_completed"
    assert result["claim_boundary"]["uses_mechanism_labels_for_predicted_assignment_generator"] is False
    assert result["claim_boundary"]["uses_family_labels_for_predicted_assignment_generator"] is False
    assert result["claim_boundary"]["oracle_assignment_comparator_evaluator_only"] is True
    assert result["claim_boundary"]["soft_family_classification_evaluator_only"] is True
    assert result["claim_boundary"]["soft_family_strength_location_audit_evaluator_only"] is True
    assert result["claim_boundary"]["claims_physical_parameter_recovery"] is False
    assert result["visible_feature_matrix"]["loaded_from_stage3a_artifact"] is True
    assert result["assignment_source_audit"]["row_stochastic"] is True
    assert result["leakage_audit"]["passed"] is True
    assert result["prototype_generation_metrics"]["primary_generation_likelihood_metric"] == "categorical_population_nll"
    assert result["prototype_generation_metrics"]["secondary_continuous_density_diagnostic"] == "gaussian_density_nll"
    assert result["stratified_null_metrics"]["schema"] == "scope_static_stage3c_public_stratified_null_metrics_v1"
    assert result["stratified_null_metrics"]["stratification_audit"]["uses_evaluator_labels"] is False
    assert result["stratified_null_metrics"]["stratification_audit"]["uses_learned_assignments"] is False
    assert result["assignment_shuffle_audit"]["schema"] == "scope_static_stage3c_assignment_shuffle_audit_v1"
    assert result["assignment_shuffle_audit"]["used_for_model_selection"] is False
    assert result["assignment_shuffle_audit"]["seed_count"] == 1
    assert result["assignment_shuffle_audit"]["checks"]["shuffled_assignments_row_stochastic"] is True
    assert result["feature_scramble_audit"]["schema"] == "scope_static_stage3c_feature_scramble_audit_v1"
    assert result["feature_scramble_audit"]["used_for_model_selection"] is False
    assert result["feature_scramble_audit"]["seed_count"] == 1
    assert result["feature_scramble_audit"]["checks"]["feature_marginals_preserved"] is True
    assert result["feature_scramble_audit"]["checks"]["row_order_fold_and_assignments_preserved"] is True
    assert result["acceptance_audit"]["checks"]["heldout_generation_beats_global_null_categorical_population_nll"] is True
    assert result["acceptance_audit"]["checks"]["heldout_generation_beats_mean_only_mae"] is True
    assert result["acceptance_audit"]["checks"]["soft_family_classification_nmi_is_one"] is True
    assert result["acceptance_audit"]["checks"]["soft_family_classification_ari_is_one"] is True
    assert result["acceptance_audit"]["checks"]["soft_family_classification_balanced_accuracy_is_one"] is True
    assert result["acceptance_audit"]["checks"]["soft_family_classification_min_recall_is_one"] is True
    assert result["acceptance_audit"]["checks"]["soft_family_strength_location_audit_evaluator_only_or_skipped"] is True
    assert result["acceptance_audit"]["checks"]["soft_family_strength_location_is_context_relative"] is True
    assert result["acceptance_audit"]["checks"]["soft_family_strength_does_not_claim_physical_parameter_recovery"] is True

    predicted = result["predicted_assignment_metrics"]["overall"]
    global_null = result["global_null_metrics"]["overall"]
    oracle = result["oracle_assignment_comparator_metrics"]["overall"]
    family = result["soft_family_classification_metrics"]
    strength = result["soft_family_strength_location_audit"]
    report = result["prototype_generation_metrics"]["primary_likelihood_report"]
    assert predicted["categorical_population_nll"] >= 0.0
    assert oracle["categorical_population_nll"] >= 0.0
    assert predicted["categorical_population_nll"] < global_null["categorical_population_nll"]
    assert report["predicted_assignment"] == predicted["categorical_population_nll"]
    assert report["oracle_assignment_comparator"] == oracle["categorical_population_nll"]
    assert report["predicted_minus_oracle_gap"] == result["prototype_generation_metrics"]["oracle_comparator_gap"]["categorical_population_nll_gap"]
    assert predicted["gaussian_density_nll"] == predicted["gaussian_nll"]
    assert predicted["gaussian_density_nll"] < global_null["gaussian_density_nll"]
    assert result["assignment_shuffle_audit"]["runs"][0]["overall"]["categorical_population_nll"] is not None
    assert (
        result["assignment_shuffle_audit"]["reference_metrics"]["predicted_assignment"]["categorical_population_nll"]
        == predicted["categorical_population_nll"]
    )
    assert result["feature_scramble_audit"]["runs"][0]["predicted_assignment"]["categorical_population_nll"] is not None
    assert (
        result["feature_scramble_audit"]["reference_metrics"]["predicted_assignment"]["categorical_population_nll"]
        == predicted["categorical_population_nll"]
    )
    assert oracle["raw_visible_feature_mae"] <= predicted["raw_visible_feature_mae"] + 1.0e-12
    assert result["oracle_assignment_comparator_metrics"]["uses_evaluator_labels"] is True
    assert result["oracle_assignment_comparator_metrics"]["used_for_acceptance_model_selection"] is False
    assert family["schema"] == "scope_static_stage3c_soft_family_classification_metrics_v1"
    assert family["evaluator_only"] is True
    assert family["used_for_training"] is False
    assert family["used_for_model_selection"] is False
    assert family["uses_channels_ptms_kraus"] is False
    assert family["normalized_mutual_info"] == 1.0
    assert family["adjusted_rand_index"] == 1.0
    assert family["balanced_accuracy"] == 1.0
    assert family["min_recall"] == 1.0
    assert family["passed"] is True
    assert strength["schema"] == "scope_static_stage3c_soft_family_strength_location_audit_v1"
    assert strength["evaluator_only"] is True
    assert strength["location_reference_frame"] == "context_relative"
    assert strength["claims_physical_parameter_recovery"] is False
    assert "readout_spam" in strength["per_family"]
    readout_strength = strength["per_family"]["readout_spam"]["visible_strength"]
    assert readout_strength["primary_reference_frame"] == "context_relative"
    assert "context_relative_reference" in readout_strength
    assert "global_reference" in readout_strength
    assert (
        strength["per_family"]["readout_spam"]["context_relative_action_locations"]["reference_frame"]
        == "context_relative"
    )
    assert strength["per_family"]["readout_spam"]["absolute_provenance_counts"]["provenance_only"] is True

    for name in [
        "metrics.json",
        "prototype_generation_metrics.json",
        "predicted_assignment_metrics.json",
        "oracle_assignment_comparator_metrics.json",
        "soft_family_classification_metrics.json",
        "soft_family_strength_location_audit.json",
        "global_null_metrics.json",
        "stratified_null_metrics.json",
        "mean_only_baseline_metrics.json",
        "assignment_shuffle_audit.json",
        "feature_scramble_audit.json",
        "leakage_audit.json",
        "acceptance_audit.json",
        "assignment_source_audit.json",
        "heldout_protocol.json",
        "visible_feature_matrix.json",
        "summary.md",
    ]:
        assert (output / name).exists()


def test_stage3c_predicted_generator_uses_frozen_features_not_teacher_record_rebuild(tmp_path: Path) -> None:
    teacher, s3a, s3a5, s3b1 = _prepare_artifacts(
        tmp_path,
        [
            ("M0", "M0"),
            ("M4", "M4"),
            ("M8", "M8"),
        ],
    )
    _poison_teacher_mechanism_definitions_but_keep_labels(teacher)

    result = run_stage3c_prototype_generator_learning(stage3a_dir=s3a, stage3a5_dir=s3a5, stage3b1_dir=s3b1, output_dir=tmp_path / "S3C")

    assert result["decision"] == "stage3c_prototype_generator_learning_completed"
    assert result["visible_feature_matrix"]["loaded_from_stage3a_artifact"] is True
    assert result["leakage_audit"]["checks"]["predicted_generator_rebuilds_features_from_oracle_records"] is False


def test_stage3c_rejects_assignment_row_mismatch(tmp_path: Path) -> None:
    _teacher, s3a, s3a5, s3b1 = _prepare_artifacts(
        tmp_path,
        [
            ("M0", "M0"),
            ("M4", "M4"),
            ("M8", "M8"),
        ],
    )
    np.save(s3b1 / "learned_assignments.npy", np.ones((2, 2), dtype=np.float64) / 2.0)

    try:
        run_stage3c_prototype_generator_learning(stage3a_dir=s3a, stage3a5_dir=s3a5, stage3b1_dir=s3b1, output_dir=tmp_path / "S3C")
    except ValueError as exc:
        assert "row count" in str(exc)
    else:
        raise AssertionError("expected assignment row-count mismatch to fail")


def test_stage3c_config_wrapper_runs_from_yaml(tmp_path: Path) -> None:
    _teacher, s3a, s3a5, s3b1 = _prepare_artifacts(
        tmp_path,
        [
            ("M0", "M0"),
            ("M4", "M4"),
            ("M8", "M8"),
        ],
    )
    output = tmp_path / "configured"
    config = tmp_path / "stage3c.yaml"
    config.write_text(
        "\n".join(
            [
                "stage3c_prototype_generator_learning:",
                f"  stage3a_dir: {s3a}",
                f"  stage3a5_dir: {s3a5}",
                f"  stage3b1_dir: {s3b1}",
                f"  output_dir: {output}",
                "  max_cv_folds: 2",
            ]
        )
        + "\n"
    )

    result = run_stage3c_generator_learning_from_config(config_path=config)

    assert result["decision"] == "stage3c_prototype_generator_learning_completed"
    assert (output / "prototype_generation_metrics.json").exists()


def test_stage3c_no_categorical_surface_uses_gaussian_primary_and_block_lift(tmp_path: Path) -> None:
    s3a = tmp_path / "S3A_v2_like"
    s3b1 = tmp_path / "S3B1"
    s3a.mkdir()
    s3b1.mkdir()
    feature_names = [
        "raw__marginal__detector_rate_mean",
        "raw__spatial_corr__neighbor_cov_mean",
        "raw__logical_coupling__obs_flip_rate_delta",
        "meta__public_geometry__basis_is_z",
    ]
    x = np.asarray(
        [
            [0.10, 0.00, 0.20, 1.00],
            [0.10, 0.00, 0.20, 1.00],
            [0.10, 0.00, 0.20, 1.00],
            [0.90, 0.50, -0.20, 0.00],
            [0.90, 0.50, -0.20, 0.00],
            [0.90, 0.50, -0.20, 0.00],
        ],
        dtype=np.float64,
    )
    np.save(s3a / "visible_features.npy", x)
    (s3a / "visible_feature_schema.json").write_text(
        json.dumps({"features": [{"index": idx, "name": name} for idx, name in enumerate(feature_names)]}, indent=2) + "\n"
    )
    (s3a / "visible_feature_matrix.json").write_text(
        json.dumps(
            {
                "training_matrix_path": "visible_features.npy",
                "feature_schema_path": "visible_feature_schema.json",
                "shape": [int(dim) for dim in x.shape],
                "visible_features_sha256": matrix_digest(x),
            },
            indent=2,
        )
        + "\n"
    )
    (s3a / "metrics.json").write_text(
        json.dumps(
            {
                "acceptance_audit": {"passed": True},
                "split_manifest": {
                    "folds": [
                        {
                            "train_indices": [0, 3],
                            "validation_indices": [1, 4],
                            "test_indices": [2, 5],
                        }
                    ]
                },
            },
            indent=2,
        )
        + "\n"
    )
    responsibilities = np.asarray(
        [
            [1.0, 0.0],
            [1.0, 0.0],
            [1.0, 0.0],
            [0.0, 1.0],
            [0.0, 1.0],
            [0.0, 1.0],
        ],
        dtype=np.float64,
    )
    np.save(s3b1 / "learned_assignments.npy", responsibilities)
    (s3b1 / "metrics.json").write_text(
        json.dumps(
            {
                "acceptance_audit": {"passed": True},
                "claim_boundary": {
                    "trains_from_stage3a_frozen_visible_features": True,
                    "uses_mechanism_labels_for_fit": False,
                    "uses_mechanism_labels_for_model_selection": False,
                },
            },
            indent=2,
        )
        + "\n"
    )

    result = run_stage3c_prototype_generator_learning(
        stage3a_dir=s3a,
        stage3b1_dir=s3b1,
        output_dir=tmp_path / "S3C",
        evaluator_mode=EVALUATOR_MODE_NO_ORACLE_LABELS,
    )

    predicted = result["predicted_assignment_metrics"]["overall"]
    global_null = result["global_null_metrics"]["overall"]
    blocks = result["prototype_generation_metrics"]["feature_block_lift"]["global_null_minus_predicted"]
    profile_report = result["prototype_generation_metrics"]["target_score_profile_report"]["profiles"]
    assert result["decision"] == "stage3c_prototype_generator_learning_completed"
    assert result["soft_family_classification_metrics"]["skipped"] is True
    assert result["soft_family_strength_location_audit"]["skipped"] is True
    assert result["claim_boundary"]["soft_family_classification_skipped"] is True
    assert result["claim_boundary"]["soft_family_strength_location_audit_skipped"] is True
    assert result["acceptance_audit"]["checks"]["soft_family_classification_evaluator_only_or_skipped"] is True
    assert result["acceptance_audit"]["checks"]["soft_family_strength_location_audit_evaluator_only_or_skipped"] is True
    assert result["prototype_generation_metrics"]["primary_generation_likelihood_metric"] == "gaussian_density_nll"
    assert result["assignment_shuffle_audit"]["primary_generation_likelihood_metric"] == "gaussian_density_nll"
    assert result["feature_scramble_audit"]["primary_generation_likelihood_metric"] == "gaussian_density_nll"
    assert result["acceptance_audit"]["primary_generation_likelihood_metric"] == "gaussian_density_nll"
    assert result["stratified_null_metrics"]["stratification_audit"]["public_fields_available"] is False
    assert result["prototype_generation_metrics"]["target_score_profile_report"]["profiles"]["raw_target_only"]["gaussian_density_nll"][
        "stratified_null"
    ] is not None
    assert profile_report["full_target"]["target_feature_count"] == 4
    assert profile_report["raw_target_only"]["target_feature_count"] == 3
    assert profile_report["raw_target_only"]["included_blocks"] == [
        "raw__logical_coupling",
        "raw__marginal",
        "raw__spatial_corr",
    ]
    assert "meta__public_geometry" not in profile_report["raw_target_only"]["included_blocks"]
    assert result["prototype_generation_metrics"]["target_score_profile_report"]["block_profiles"]["blocks"]["raw__marginal"][
        "gaussian_density_nll"
    ]["global_null_minus_predicted_lift"] > 0.0
    assert profile_report["block_normalized"]["target_feature_count"] == 4
    assert result["predicted_assignment_metrics"]["fold_metrics"][0]["target_score_profiles"]["profiles"]["raw_target_only"][
        "target_feature_count"
    ] == 3
    assert result["assignment_shuffle_audit"]["target_score_profile_aggregate"]["profiles"]["raw_target_only"]["run_count"] == 1
    assert (
        result["feature_scramble_audit"]["aggregate"]["target_score_profiles"]["predicted_assignment"]["profiles"]["raw_target_only"]["run_count"]
        == 1
    )
    assert predicted["categorical_population_group_count"] == 0
    assert predicted["gaussian_density_nll"] < global_null["gaussian_density_nll"]
    assert blocks["raw__marginal"]["raw_visible_feature_mae_reduction"] > 0.0
    assert blocks["raw__spatial_corr"]["raw_visible_feature_mae_reduction"] > 0.0
    assert blocks["raw__logical_coupling"]["raw_visible_feature_mae_reduction"] > 0.0


def _prepare_artifacts(tmp_path: Path, label_specs: list[tuple[str, str]]) -> tuple[Path, Path, Path, Path]:
    teacher = tmp_path / "S2D_PHYC1_teacher"
    teacher.mkdir()
    records = []
    for group in range(3):
        for label, mechanism_id in label_specs:
            records.append(_record(label, mechanism_id, group))
    (teacher / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}, indent=2) + "\n")
    s3a = tmp_path / "S3A"
    s3a5 = tmp_path / "S3A5"
    s3b1 = tmp_path / "S3B1"
    run_stage3a_dataset_protocol_freeze(teacher_dir=teacher, output_dir=s3a, shots=1000, batch_size=2)
    run_stage3a5_observability_alias_ceiling(stage3a_dir=s3a, output_dir=s3a5)
    run_stage3b1_first_discovery_model(stage3a_dir=s3a, stage3a5_dir=s3a5, output_dir=s3b1, max_iter=15)
    return teacher, s3a, s3a5, s3b1


def _record(label: str, mechanism_id: str, group: int) -> dict[str, object]:
    two_qubit = mechanism_id in {"M8", "M9", "M10", "M12", "M21", "M22", "M23", "M28", "M29", "M30", "M31", "M32", "M33"}
    return {
        "oracle_label": label,
        "mechanism_id": mechanism_id,
        "name": MECHANISM_NAMES[mechanism_id],
        "num_qubits": 2 if two_qubit else 1,
        "parameters": {},
        "instruction": "rzz" if two_qubit else "id",
        "qubits": [0, 1] if two_qubit else [0],
        "circuit_id": int(group),
        "location_id": int(group),
        "probe_indices": [],
    }


def _poison_teacher_mechanism_definitions_but_keep_labels(teacher: Path) -> None:
    path = teacher / "oracle_mechanisms.json"
    data = json.loads(path.read_text())
    for record in data["mechanisms"]:
        record["mechanism_id"] = "NOT_A_REAL_MECHANISM"
        record["name"] = "poisoned mechanism definition"
        record["num_qubits"] = 999
        record["instruction"] = "not_a_gate"
        record["parameters"] = {"poisoned": True}
    path.write_text(json.dumps(data, indent=2) + "\n")
