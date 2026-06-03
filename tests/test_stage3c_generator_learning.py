from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from scope_static.experiments.stage3.generator_learning import run_stage3c_generator_learning_from_config
from scope_static.learner.zx_visible_probe_suite import build_zx_visible_feature_table
from scope_static.primitives.mechanism_catalog import MECHANISM_LEAF_EXACT_IDS, MECHANISM_NAMES, NON_FLAT_PRIMARY_TARGET_IDS
from scope_static.primitives.mechanism_catalog import mechanism_public_label
from scope_static.mechanism_discovery.protocol_freeze import run_stage3a_dataset_protocol_freeze
from scope_static.mechanism_discovery.observability_ceiling import run_stage3a5_observability_alias_ceiling
from scope_static.mechanism_discovery.artifacts import matrix_digest
from scope_static.mechanism_discovery.discovery_model import EVALUATOR_MODE_CONTROLLED_CATALOG, EVALUATOR_MODE_NO_ORACLE_LABELS
from scope_static.mechanism_discovery.discovery_model import run_stage3b1_first_discovery_model
from scope_static.mechanism_discovery.generator_learning import evaluate_soft_family_strength_location_audit
from scope_static.mechanism_discovery.generator_learning import run_stage3c_prototype_generator_learning
from scope_static.mechanism_discovery.generator_learning import stage3c_claim_gate_audit


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
    assert result["claim_boundary"]["s5_context_relative_mechanism_effect_audit_evaluator_only"] is True
    assert result["claim_boundary"]["claim_gate_allows_assignment_dependent_generator_claim"] is False
    assert result["claim_boundary"]["diagnostic_only_until_s3b1_s5b1_gates_pass"] is True
    assert result["claim_boundary"]["mechanism_taxonomy_contract_audit_reported"] is True
    assert result["claim_boundary"]["mechanism_dimension_recovery_audit_evaluator_only"] is True
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
    assert result["acceptance_audit"]["checks"]["s5_context_relative_effect_audit_evaluator_only_or_skipped"] is True
    assert result["acceptance_audit"]["checks"]["s5_context_relative_effect_uses_context_relative_location"] is True
    assert result["acceptance_audit"]["checks"]["s5_context_relative_effect_uses_context_relative_strength"] is True
    assert result["acceptance_audit"]["checks"]["s5_context_relative_effect_does_not_claim_physical_parameter_recovery"] is True
    assert result["acceptance_audit"]["checks"]["s5_context_relative_effect_recovery_metrics_passed"] is True
    assert result["acceptance_audit"]["checks"]["mechanism_taxonomy_contract_audit_passed"] is True
    assert result["acceptance_audit"]["checks"]["mechanism_dimension_recovery_audit_evaluator_only_or_skipped"] is True
    assert result["acceptance_audit"]["checks"]["mechanism_dimension_recovery_audit_passed"] is True
    assert result["acceptance_audit"]["checks"]["s5_contract_typed_recovery_metrics_passed"] is True
    assert result["claim_gate_audit"]["claim_allowed"] is False
    assert result["claim_gate_audit"]["diagnostic_only"] is True
    assert result["claim_gate_audit"]["checks"]["s3b1_raw_acceptance_passed"] is True

    predicted = result["predicted_assignment_metrics"]["overall"]
    global_null = result["global_null_metrics"]["overall"]
    oracle = result["oracle_assignment_comparator_metrics"]["overall"]
    family = result["soft_family_classification_metrics"]
    strength = result["soft_family_strength_location_audit"]
    s5 = result["s5_context_relative_mechanism_effect_audit"]
    taxonomy = result["mechanism_taxonomy_contract_audit"]
    dimension = result["mechanism_dimension_recovery_audit"]
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
    assert strength["schema"] == "scope_static_s5_context_relative_mechanism_effect_audit_v1"
    assert s5["schema"] == "scope_static_s5_context_relative_mechanism_effect_audit_v1"
    assert s5["stage"] == "S5_context_relative_mechanism_effect_recovery"
    assert s5["contract_typed_recovery_metrics"]["passed"] is True
    assert taxonomy["passed"] is True
    assert taxonomy["schema"] == "scope_static_mechanism_taxonomy_contract_audit_v2"
    assert taxonomy["label_scheme"] == "flat_F_nonflat_M_v1"
    assert taxonomy["legacy_catalog_id_to_public_label"]["M0"] == mechanism_public_label("M0")
    assert taxonomy["legacy_catalog_id_to_public_label"]["M8"] == mechanism_public_label("M8")
    assert dimension["passed"] is True
    assert dimension["classification_target"] == "contract_typed_family_plus_dimension_recovery"
    assert "M0" in dimension["non_flat_primary_target_ids_present"]
    assert mechanism_public_label("M0") in dimension["non_flat_public_labels_present"]
    assert all(target["primary_flat_cluster_target"] is False for target in dimension["targets"])
    assert all(str(target["public_label"]).startswith("M") for target in dimension["targets"])
    assert all(target["label_namespace"] == "non_flat" for target in dimension["targets"])
    assert strength["evaluator_only"] is True
    assert strength["location_reference_frame"] == "context_relative"
    assert strength["location_semantics"] == "context_conditioned_error_likelihood"
    assert "weighted likelihood/support" in strength["context_likelihood_definition"]
    assert strength["claims_physical_parameter_recovery"] is False
    assert strength["effect_recovery_metrics"]["passed"] is True
    assert strength["effect_recovery_metrics"]["max_abs_scalar_error"] == 0.0
    assert "readout_spam" in strength["per_family"]
    assert "M0" in strength["per_exact_mechanism"]
    readout_strength = strength["per_family"]["readout_spam"]["visible_strength"]
    assert readout_strength["primary_reference_frame"] == "context_relative"
    assert "context_relative_reference" in readout_strength
    assert "global_reference" in readout_strength
    assert strength["per_family"]["readout_spam"]["recovery_metrics"]["passed"] is True
    assert strength["per_family"]["readout_spam"]["recovery_metrics"]["max_abs_scalar_error"] == 0.0
    assert strength["per_exact_mechanism"]["M0"]["recovery_metrics"]["passed"] is True
    assert strength["per_exact_mechanism"]["M0"]["recovery_metrics"]["max_abs_scalar_error"] == 0.0
    assert "predicted_effect" in strength["per_family"]["readout_spam"]
    assert "oracle_effect" in strength["per_family"]["readout_spam"]
    assert (
        strength["per_family"]["readout_spam"]["context_relative_action_locations"]["reference_frame"]
        == "context_relative"
    )
    assert (
        strength["per_family"]["readout_spam"]["context_likelihood"]["semantic_role"]
        == "context_conditioned_error_likelihood"
    )
    assert (
        strength["per_family"]["readout_spam"]["recovery_metrics"]["context_likelihood_errors"][
            "top_context_likelihood_cell_match"
        ]
        is True
    )
    assert strength["per_family"]["readout_spam"]["absolute_provenance_counts"]["provenance_only"] is True

    for name in [
        "metrics.json",
        "prototype_generation_metrics.json",
        "predicted_assignment_metrics.json",
        "oracle_assignment_comparator_metrics.json",
        "soft_family_classification_metrics.json",
        "soft_family_strength_location_audit.json",
        "s5_context_relative_mechanism_effect_audit.json",
        "mechanism_taxonomy_contract_audit.json",
        "mechanism_dimension_recovery_audit.json",
        "overlay_contract_audit.json",
        "overlay_recovery_audit.json",
        "global_null_metrics.json",
        "stratified_null_metrics.json",
        "mean_only_baseline_metrics.json",
        "assignment_shuffle_audit.json",
        "feature_scramble_audit.json",
        "leakage_audit.json",
        "claim_gate_audit.json",
        "acceptance_audit.json",
        "assignment_source_audit.json",
        "heldout_protocol.json",
        "visible_feature_matrix.json",
        "summary.md",
    ]:
        assert (output / name).exists()


def test_stage3c_s5_recovers_context_relative_location_and_strength_on_harder_teacher(tmp_path: Path) -> None:
    _teacher, s3a, s3a5, s3b1 = _prepare_harder_context_effect_artifacts(tmp_path)
    output = tmp_path / "S3C_harder_effects"

    result = run_stage3c_prototype_generator_learning(stage3a_dir=s3a, stage3a5_dir=s3a5, stage3b1_dir=s3b1, output_dir=output)

    family = result["soft_family_classification_metrics"]
    s5 = result["s5_context_relative_mechanism_effect_audit"]
    assert family["normalized_mutual_info"] == 1.0
    assert family["adjusted_rand_index"] == 1.0
    assert family["balanced_accuracy"] == 1.0
    assert family["min_recall"] == 1.0
    assert s5["effect_recovery_metrics"]["passed"] is True
    assert s5["effect_recovery_metrics"]["family_count"] == 5
    assert s5["effect_recovery_metrics"]["exact_mechanism_count"] == 5
    assert s5["effect_recovery_metrics"]["max_abs_scalar_error"] == 0.0

    expected_parameter = {
        "M1": "p",
        "M8": "epsilon",
        "M13": "epsilon",
        "M17": "p",
        "M24": "gamma_up",
    }
    for label, parameter_name in expected_parameter.items():
        row = s5["per_exact_mechanism"][label]
        assert row["recovery_metrics"]["passed"] is True
        assert row["recovery_metrics"]["max_abs_scalar_error"] == 0.0
        assert row["recovery_metrics"]["location_errors"]["top_relative_location_cell_match"] is True
        assert row["recovery_metrics"]["strength_errors"]["top_context_relative_strength_block_match"] is True

        location = row["context_relative_action_locations"]["location_fraction_in_context"]
        likelihood = row["context_likelihood"]
        assert location["min"] == 0.0
        assert location["max"] == 1.0
        assert location["signed_mean"] == 0.5
        assert likelihood["semantic_role"] == "context_conditioned_error_likelihood"
        assert likelihood["location_fraction_in_context"] == location
        assert row["recovery_metrics"]["context_likelihood_errors"]["top_context_likelihood_cell_match"] is True

        strength = row["visible_strength"]["context_relative_reference"]
        assert strength["surface_standardized_l2_shift"] > 0.0
        assert strength["surface_mean_abs_standardized_shift"] > 0.0

        parameter = row["oracle_parameter_strength"]["per_parameter"][parameter_name]
        assert parameter["count"] == 5
        assert parameter["min"] < parameter["max"]
        assert row["oracle_parameter_strength"]["records_with_numeric_parameters"] == 5


def test_s5_leaf_effect_audit_covers_current_leaf_mechanisms_with_twenty_context_variants() -> None:
    records = _allm_context_effect_records(variant_count=20)
    table = build_zx_visible_feature_table(records, shots=1000, sampling_mode="expected")
    labels = [str(record["oracle_label"]) for record in records]
    leaf_mechanism_ids = _leaf_exact_mechanism_ids()
    label_to_index = {label: idx for idx, label in enumerate(leaf_mechanism_ids)}
    responsibilities = np.zeros((len(records), len(leaf_mechanism_ids)), dtype=np.float64)
    for row, label in enumerate(labels):
        responsibilities[row, label_to_index[label]] = 1.0

    result = evaluate_soft_family_strength_location_audit(
        table.expected_features,
        responsibilities,
        records,
        feature_names=table.feature_names,
        evaluator_mode=EVALUATOR_MODE_CONTROLLED_CATALOG,
    )

    assert result["family_count"] == 5
    assert result["exact_mechanism_count"] == len(leaf_mechanism_ids)
    assert result["effect_recovery_metrics"]["passed"] is True
    assert result["effect_recovery_metrics"]["max_abs_scalar_error"] == 0.0
    assert result["contract_typed_recovery_metrics"]["passed"] is True
    assert set(result["per_exact_mechanism"]) == set(leaf_mechanism_ids)
    assert "M11" not in result["per_exact_mechanism"]
    dimension = result["mechanism_dimension_recovery_audit"]
    expected_non_flat_leaf_ids = set(NON_FLAT_PRIMARY_TARGET_IDS) & set(leaf_mechanism_ids)
    assert dimension["passed"] is True
    assert set(dimension["non_flat_primary_target_ids_present"]) == expected_non_flat_leaf_ids
    assert "M11" not in dimension["non_flat_primary_target_ids_present"]
    for target in dimension["targets"]:
        assert target["mechanism_id"] in expected_non_flat_leaf_ids
        assert target["primary_flat_cluster_target"] is False
        assert target["dimension_values"]["all_declared_dimensions_have_values"] is True
        assert target["dimension_values"]["strength_dimension_available"] is True
    for mechanism_id in leaf_mechanism_ids:
        row = result["per_exact_mechanism"][mechanism_id]
        parameter_name = _allm_primary_parameter_name(mechanism_id)
        location = row["context_relative_action_locations"]
        location_fraction = location["location_fraction_in_context"]
        likelihood = row["context_likelihood"]
        parameter = row["oracle_parameter_strength"]["per_parameter"][parameter_name]
        strength = row["visible_strength"]["context_relative_reference"]

        assert row["support_count"] == 20
        assert row["recovery_metrics"]["passed"] is True
        assert row["recovery_metrics"]["max_abs_scalar_error"] == 0.0
        assert location["context_count"] == 20
        assert location_fraction["weight_mass"] == 20.0
        assert location_fraction["min"] < location_fraction["max"]
        assert likelihood["semantic_role"] == "context_conditioned_error_likelihood"
        assert likelihood["weight_mass"] == 20.0
        assert likelihood["location_fraction_in_context"] == location_fraction
        assert parameter["count"] == 20
        assert parameter["min"] < parameter["max"]
        assert strength["surface_standardized_l2_shift"] > 0.0


def test_s5_spectator_overlay_family_extracts_base_context_location_axis_and_strength() -> None:
    records = _spectator_overlay_family_records(variant_count=20)
    table = build_zx_visible_feature_table(records, shots=1000, sampling_mode="expected")
    base_mechanisms = ["M1", "M7", "M8", "M17"]
    label_to_index = {label: idx for idx, label in enumerate(base_mechanisms)}
    responsibilities = np.zeros((len(records), len(base_mechanisms)), dtype=np.float64)
    for row, record in enumerate(records):
        responsibilities[row, label_to_index[str(record["oracle_label"])]] = 1.0

    result = evaluate_soft_family_strength_location_audit(
        table.expected_features,
        responsibilities,
        records,
        feature_names=table.feature_names,
        evaluator_mode=EVALUATOR_MODE_CONTROLLED_CATALOG,
    )

    overlay = result["spectator_overlay_audit"]
    overlay_recovery = result["overlay_recovery_audit"]
    overlay_contract = result["overlay_contract_audit"]
    assert overlay["skipped"] is False
    assert overlay["passed"] is True
    assert overlay_contract["passed"] is True
    assert overlay_recovery["passed"] is True
    assert overlay_recovery["recovery_evaluable"] is True
    assert overlay["classification_target"] == "base_mechanism_plus_spectator_overlay_dimensions"
    assert overlay["flat_exact_m11_target"] is False
    assert overlay["claims_physical_parameter_recovery"] is False
    assert overlay["overlay_row_count"] == 80
    assert set(overlay["base_mechanisms"]) == set(base_mechanisms)
    assert set(overlay["coupling_axes"]) == {"RZ", "ZZ", "readout_bias", "reset_bias"}
    assert set(overlay["timing_contexts"]) == {"prev_cycle", "same_cycle", "shot_block_drift"}
    for check in overlay["checks"].values():
        assert check is True
    assert len(overlay["groups"]) == 4
    for group in overlay["groups"]:
        location = group["context_relative_action_locations"]["location_fraction_in_context"]
        likelihood = group["context_relative_action_locations"]["context_likelihood"]
        strength = group["overlay_strength"]
        visible = group["visible_strength"]["context_relative_reference"]
        assert group["support_count"] == 20
        assert group["flat_exact_m11_target"] is False
        assert location["min"] < location["max"]
        assert likelihood["semantic_role"] == "context_conditioned_error_likelihood"
        assert strength["count"] == 20
        assert strength["min"] < strength["max"]
        assert visible["surface_standardized_l2_shift"] > 0.0


def test_overlay_recovery_audit_fields_present() -> None:
    records = _spectator_overlay_family_records(variant_count=3)
    table = build_zx_visible_feature_table(records, shots=1000, sampling_mode="expected")
    base_mechanisms = ["M1", "M7", "M8", "M17"]
    responsibilities = np.zeros((len(records), len(base_mechanisms)), dtype=np.float64)
    label_to_index = {label: idx for idx, label in enumerate(base_mechanisms)}
    for row, record in enumerate(records):
        responsibilities[row, label_to_index[str(record["oracle_label"])]] = 1.0

    result = evaluate_soft_family_strength_location_audit(
        table.expected_features,
        responsibilities,
        records,
        feature_names=table.feature_names,
        evaluator_mode=EVALUATOR_MODE_CONTROLLED_CATALOG,
    )

    overlay = result["overlay_recovery_audit"]
    assert overlay["schema"] == "scope_static_s5_overlay_recovery_audit_v1"
    assert overlay["overlay_family"] == "spectator_crosstalk"
    assert overlay["visible_only_selection"] is True
    assert overlay["uses_oracle_overlay_fields_for_training"] is False
    assert overlay["flat_exact_m11_target"] is False
    assert overlay["base_mechanism_recovery"]
    assert overlay["victim_relative_location_recovery"]["reported_in_groups"] is True
    assert overlay["aggressor_relative_location_recovery"]["reported_in_groups"] is True
    assert overlay["coupling_axis_recovery"]["coupling_axes"]
    assert overlay["timing_context_recovery"]["timing_contexts"]
    assert overlay["joint_overlay_recovery"]["passed"] is True


def test_m11_overlay_not_counted_as_flat_leaf_target() -> None:
    records = [
        _effect_record(
            "M11",
            group=idx,
            slot=idx,
            instruction="rzz",
            parameters={"epsilon": 0.025 + 0.001 * idx, "strength": 0.025 + 0.001 * idx},
            qubits=[idx, idx + 1],
        )
        for idx in range(4)
    ]
    table = build_zx_visible_feature_table(records, shots=1000, sampling_mode="expected")
    responsibilities = np.ones((len(records), 1), dtype=np.float64)

    result = evaluate_soft_family_strength_location_audit(
        table.expected_features,
        responsibilities,
        records,
        feature_names=table.feature_names,
        evaluator_mode=EVALUATOR_MODE_CONTROLLED_CATALOG,
    )

    contract = result["contract_typed_recovery_metrics"]
    dimension = result["mechanism_dimension_recovery_audit"]
    overlay_contract = result["overlay_contract_audit"]
    overlay_recovery = result["overlay_recovery_audit"]
    assert result["passed"] is False
    assert contract["checks"]["atomic_flat_exact_recovery_passed"] is True
    assert contract["checks"]["dimension_recovery_passed"] is True
    assert contract["checks"]["overlay_contract_payload_available_or_no_overlay_records"] is False
    assert contract["overlay_contract_missing_target_ids"] == ["M11"]
    assert "M11_overlay_contract_missing" in contract["overlay_failure_kinds"]
    assert dimension["passed"] is True
    assert dimension["recovery_passed_excluding_not_evaluable"] is True
    assert dimension["not_evaluable_target_ids"] == ["M11"]
    assert dimension["overlay_contract_missing_target_ids"] == ["M11"]
    target = dimension["targets"][0]
    assert target["mechanism_id"] == "M11"
    assert target["not_evaluable"] is True
    assert target["not_evaluable_reason"] == "M11_overlay_contract_missing"
    assert target["recoverable_failure"] is False
    assert overlay_contract["passed"] is False
    assert overlay_contract["num_overlay_records_missing_payload"] == 4
    assert overlay_recovery["recovery_evaluable"] is False
    assert overlay_recovery["failure_kind"] == "M11_overlay_contract_missing"
    assert overlay_recovery["recovery_failure"] is False


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
    assert result["s5_context_relative_mechanism_effect_audit"]["skipped"] is True
    assert result["mechanism_dimension_recovery_audit"]["skipped"] is True
    assert result["claim_boundary"]["soft_family_classification_skipped"] is True
    assert result["claim_boundary"]["soft_family_strength_location_audit_skipped"] is True
    assert result["claim_boundary"]["s5_context_relative_mechanism_effect_audit_skipped"] is True
    assert result["claim_boundary"]["mechanism_dimension_recovery_audit_skipped"] is True
    assert result["acceptance_audit"]["checks"]["soft_family_classification_evaluator_only_or_skipped"] is True
    assert result["acceptance_audit"]["checks"]["soft_family_strength_location_audit_evaluator_only_or_skipped"] is True
    assert result["acceptance_audit"]["checks"]["s5_context_relative_effect_audit_evaluator_only_or_skipped"] is True
    assert result["acceptance_audit"]["checks"]["mechanism_dimension_recovery_audit_evaluator_only_or_skipped"] is True
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


def test_stage3c_claim_gate_keeps_residualized_assignment_diagnostic_only() -> None:
    gate = stage3c_claim_gate_audit(
        s3b1_metrics={"decision": "stage3b1_first_discovery_model_completed", "acceptance_audit": {"passed": True}},
        s3b1_residualized_metrics={
            "decision": "stage3b1_first_discovery_model_completed",
            "acceptance_audit": {"passed": True},
            "visible_transform_audit": {"visible_transform": "public_context_residualized", "claim_allowed": True},
        },
        stage3d4b_metrics=None,
        stage5b1_metrics={
            "decision": "stage5b1_property_recovery_passed",
            "acceptance_audit": {"passed": True},
            "assignment_source_audit": {"assignment_source": "stage3b1"},
        },
    )

    assert gate["claim_allowed"] is True
    assert gate["residualized_s3b1_role"] == "diagnostic_only_shortcut_and_bleed_audit"
    assert gate["checks"]["s3b1_residualized_not_used_as_claim_assignment_source"] is True
    assert gate["claim_assignment_source"] == "stage3b1_raw"


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


def _prepare_harder_context_effect_artifacts(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    teacher = tmp_path / "S2D_PHYC1_harder_effect_teacher"
    teacher.mkdir()
    specs = [
        ("M1", "measure", lambda group: {"p": 0.015 + 0.003 * group}, lambda group: [group % 5]),
        ("M17", "reset", lambda group: {"p": 0.018 + 0.002 * group}, lambda group: [(group + 1) % 5]),
        (
            "M8",
            "rzz",
            lambda group: {"epsilon": 0.035 + 0.006 * group},
            lambda group: [group % 5, (group + 1) % 5],
        ),
        (
            "M13",
            "rx",
            lambda group: {"epsilon": 0.025 + 0.004 * group, "operation_axis": "rx", "error_axis": "rx"},
            lambda group: [(group + 2) % 5],
        ),
        (
            "M24",
            "id",
            lambda group: {"gamma_up": 0.006 + 0.001 * group},
            lambda group: [(group + 3) % 5],
        ),
    ]
    records = []
    for group in range(5):
        rotated = [*specs[group:], *specs[:group]]
        for slot, (label, instruction, parameter_fn, qubit_fn) in enumerate(rotated):
            records.append(_effect_record(label, group, slot, instruction, parameter_fn(group), qubit_fn(group)))
    (teacher / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}, indent=2) + "\n")

    s3a = tmp_path / "S3A_harder_effects"
    s3a5 = tmp_path / "S3A5_harder_effects"
    s3b1 = tmp_path / "S3B1_harder_effects"
    run_stage3a_dataset_protocol_freeze(teacher_dir=teacher, output_dir=s3a, shots=1000, batch_size=5)
    run_stage3a5_observability_alias_ceiling(stage3a_dir=s3a, output_dir=s3a5)
    run_stage3b1_first_discovery_model(stage3a_dir=s3a, stage3a5_dir=s3a5, output_dir=s3b1, max_iter=30)
    return teacher, s3a, s3a5, s3b1


def _allm_context_effect_records(*, variant_count: int) -> list[dict[str, object]]:
    records = []
    mechanism_ids = _leaf_exact_mechanism_ids()
    for variant in range(int(variant_count)):
        for slot, mechanism_id in enumerate(mechanism_ids):
            records.append(
                _effect_record(
                    mechanism_id,
                    variant,
                    (slot + variant) % len(mechanism_ids),
                    _allm_instruction(mechanism_id),
                    _allm_strength_parameters(mechanism_id, variant),
                    _allm_qubits(mechanism_id, variant, slot),
                )
            )
    return records


def _leaf_exact_mechanism_ids() -> list[str]:
    return list(MECHANISM_LEAF_EXACT_IDS)


def _spectator_overlay_family_records(*, variant_count: int) -> list[dict[str, object]]:
    specs = [
        ("M8", "ZZ", "same_cycle", "rzz"),
        ("M7", "RZ", "prev_cycle", "rz"),
        ("M1", "readout_bias", "same_cycle", "measure"),
        ("M17", "reset_bias", "shot_block_drift", "reset"),
    ]
    records = []
    for variant in range(int(variant_count)):
        for slot, (base, axis, timing, instruction) in enumerate(specs):
            strength = 0.002 + 0.0005 * slot + 0.0001 * variant
            parameters = dict(_allm_strength_parameters(base, variant))
            parameters["spectator_strength"] = strength
            records.append(
                _effect_record(
                    base,
                    variant,
                    (slot + variant) % len(specs),
                    instruction,
                    parameters,
                    _allm_qubits(base, variant, slot),
                    spectator_overlay={
                        "present": True,
                        "base_mechanism": base,
                        "victim_relative_location": ["edge", "detector", "qubit_id", "edge"][(slot + variant) % 4],
                        "aggressor_relative_location": ["adjacent_gate", "same_cycle_qubit", "previous_cycle_edge"][
                            (slot + 2 * variant) % 3
                        ],
                        "coupling_axis": axis,
                        "timing_context": timing,
                        "strength": strength,
                    },
                )
            )
    return records


def _allm_strength_parameters(mechanism_id: str, variant: int) -> dict[str, float | str]:
    idx = int(str(mechanism_id)[1:])
    eps = 0.03 + 0.055 * idx + 1.0e-6 * int(variant)
    prob = 0.01 + 0.004 * idx + 1.0e-6 * int(variant)
    readout = min(0.35, 0.02 + 0.006 * idx + 1.0e-6 * int(variant))
    if mechanism_id == "M0":
        return {"p": prob}
    if mechanism_id in {"M1", "M2", "M3", "M16"}:
        return {"p": readout}
    if mechanism_id == "M4":
        return {"gamma": min(0.6, 0.02 + 0.006 * idx + 1.0e-6 * int(variant))}
    if mechanism_id == "M5":
        return {"p": prob}
    if mechanism_id in {
        "M6",
        "M7",
        "M8",
        "M11",
        "M13",
        "M14",
        "M18",
        "M20",
        "M21",
        "M22",
        "M23",
        "M27",
        "M28",
        "M29",
        "M30",
        "M31",
        "M32",
        "M33",
    }:
        params: dict[str, float | str] = {"epsilon": eps}
        if mechanism_id == "M13":
            params.update({"operation_axis": "rx", "error_axis": "rx"})
        if mechanism_id == "M14":
            params.update({"operation_axis": "rx", "error_axis": "rz"})
        return params
    if mechanism_id == "M9":
        return {"p": 0.02 + 0.004 * idx + 1.0e-6 * int(variant)}
    if mechanism_id == "M10":
        return {"epsilon": eps, "epsilon_x": eps, "epsilon_y": 0.7 * eps}
    if mechanism_id == "M12":
        return {"gamma": 0.02 + 0.004 * idx + 1.0e-6 * int(variant)}
    if mechanism_id == "M15":
        return {"eta": 0.02 + 0.004 * idx + 1.0e-6 * int(variant)}
    if mechanism_id == "M17":
        return {"p": 0.02 + 0.004 * idx + 1.0e-6 * int(variant)}
    if mechanism_id == "M19":
        return {"eta": 0.01 + 0.003 * idx + 1.0e-6 * int(variant)}
    if mechanism_id == "M24":
        return {"gamma_up": 0.01 + 0.003 * idx + 1.0e-6 * int(variant)}
    if mechanism_id in {"M25", "M26"}:
        return {"p": 0.02 + 0.004 * idx + 1.0e-6 * int(variant)}
    if mechanism_id == "M34":
        return {"p": 0.01 + 0.003 * idx + 1.0e-6 * int(variant)}
    return {"epsilon": eps}


def _allm_primary_parameter_name(mechanism_id: str) -> str:
    if mechanism_id in {"M4", "M12"}:
        return "gamma"
    if mechanism_id in {"M15", "M19"}:
        return "eta"
    if mechanism_id == "M24":
        return "gamma_up"
    if mechanism_id in {
        "M6",
        "M7",
        "M8",
        "M10",
        "M11",
        "M13",
        "M14",
        "M18",
        "M20",
        "M21",
        "M22",
        "M23",
        "M27",
        "M28",
        "M29",
        "M30",
        "M31",
        "M32",
        "M33",
    }:
        return "epsilon"
    return "p"


def _allm_instruction(mechanism_id: str) -> str:
    if mechanism_id in {"M1", "M2", "M3", "M16"}:
        return "measure"
    if mechanism_id in {"M17", "M18"}:
        return "reset"
    if mechanism_id in {"M8", "M9", "M10", "M11", "M12", "M21", "M22", "M23", "M28", "M29", "M30", "M31", "M32", "M33"}:
        return "rzz"
    if mechanism_id == "M7":
        return "rz"
    if mechanism_id == "M20":
        return "ry"
    if mechanism_id in {"M6", "M13", "M14", "M18", "M27"}:
        return "rx"
    return "id"


def _allm_qubits(mechanism_id: str, variant: int, slot: int) -> list[int]:
    if mechanism_id in {"M8", "M9", "M10", "M11", "M12", "M21", "M22", "M23", "M28", "M29", "M30", "M31", "M32", "M33"}:
        left = (int(variant) + int(slot)) % 17
        return [left, (left + 1) % 17]
    return [(3 * int(variant) + int(slot)) % 17]


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


def _effect_record(
    label: str,
    group: int,
    slot: int,
    instruction: str,
    parameters: dict[str, float | str],
    qubits: list[int],
    spectator_overlay: dict[str, object] | None = None,
) -> dict[str, object]:
    record = {
        "oracle_label": label,
        "mechanism_id": label,
        "name": MECHANISM_NAMES[label],
        "num_qubits": 2 if len(qubits) == 2 else 1,
        "parameters": dict(parameters),
        "instruction": instruction,
        "qubits": [int(qubit) for qubit in qubits],
        "circuit_id": int(group),
        "location_id": int(100 * group + slot),
        "probe_indices": [int(slot), int(slot + 10)],
    }
    if spectator_overlay is not None:
        record["spectator_overlay_present"] = True
        record["spectator_overlay"] = dict(spectator_overlay)
        record["base_mechanism"] = str(spectator_overlay.get("base_mechanism", label))
        record["victim_relative_location"] = str(spectator_overlay.get("victim_relative_location", "unknown"))
        record["aggressor_relative_location"] = str(spectator_overlay.get("aggressor_relative_location", "unknown"))
        record["coupling_axis"] = str(spectator_overlay.get("coupling_axis", "unknown"))
        record["timing_context"] = str(spectator_overlay.get("timing_context", "unknown"))
    return record


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
