from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from scope_static.experiments.stage4 import google_unit_source_expansion as s4_6_cli
from scope_static.google.s4_bridge_surface import (
    _record_google_shaped_observations,
    compare_stage4_bridge_contract,
    write_stage4_synthetic_google_shaped_freeze,
)
from scope_static.mechanism_discovery import google_unit_source as s4_6_source
from scope_static.mechanism_discovery.google_transfer import run_stage4_google_transfer, run_stage4_transfer_diagnostics
from scope_static.mechanism_discovery.google_unit_source import (
    CONTROL_NAMES,
    _robustness_closeout_report,
    _soft_bucket_weights_for_mode,
    _target_mean_std_only_control_matrix,
    run_stage4_google_unit_source_expansion,
)
from scope_static.mechanism_discovery.assignment_geometry import run_stage4_assignment_geometry_repair
from scope_static.mechanism_discovery.source_ceiling import run_stage4_source_surface_survival_audit
from scope_static.mechanism_discovery.source_pretrain import run_stage4_source_pretrain
from scope_static.mechanism_discovery.support_audit import run_stage4_support_alignment_audit
from scope_static.mechanism_discovery.stage4_artifacts import (
    load_stage4_source_evaluator_labels,
    load_stage4_source_mixture_evaluator_labels,
    load_stage4_visible_matrix,
    validate_stage4_source_label_separation,
)
from scope_static.mechanism_discovery.artifacts import load_stage3a_frozen_visible_features, matrix_digest


def test_stage4_synthetic_freeze_is_stage3a_compatible_and_label_separated(tmp_path: Path) -> None:
    teacher = _write_teacher(tmp_path)
    output = tmp_path / "S4_0" / "S3A_protocol_freeze"

    result = write_stage4_synthetic_google_shaped_freeze(teacher_dir=teacher, output_dir=output, shotblock_size=4)

    matrix, feature_names, manifest = load_stage3a_frozen_visible_features(output)
    labels = load_stage4_source_evaluator_labels(output)
    separation = validate_stage4_source_label_separation(output)

    assert result["decision"] == "stage4_synthetic_bridge_freeze_passed"
    assert result["forbidden_feature_audit"]["passed"] is True
    assert result["bridge_contract_audit"]["passed"] is True
    assert matrix.shape[0] == 4
    assert len(feature_names) == matrix.shape[1]
    assert manifest["loaded_from_stage3a_artifact"] is True
    assert labels.exact_labels == ["M0", "M4", "M8", "M12"]
    assert separation["passed"] is True
    assert "exact_mechanism_label" not in "\n".join(feature_names)

    for name in [
        "visible_features.npy",
        "sampled_visible_features.npy",
        "visible_feature_schema.json",
        "visible_feature_matrix.json",
        "split_manifest.json",
        "forbidden_feature_audit.json",
        "adequacy_report.json",
        "acceptance_audit.json",
        "metrics.json",
        "summary.md",
        "source_label_manifest.json",
        "source_evaluator_labels.json",
    ]:
        assert (output / name).exists()


def test_stage4_source_survival_audit_reports_mechanism_survival(tmp_path: Path) -> None:
    source = _write_source_freeze(tmp_path)
    output = tmp_path / "S4_0_5"

    result = run_stage4_source_surface_survival_audit(stage4_source_dir=source, output_dir=output, max_iter=5)

    assert result["decision"] in {
        "bridge_surface_pass",
        "bridge_surface_quotient_only",
        "bridge_surface_projection_aliasing",
    }
    report = result["mechanism_survival_report"]
    assert report["uses_labels_for_training"] is False
    assert report["uses_labels_for_validation_selection"] is False
    assert "source_label_linear_probe_accuracy" in report
    assert "blockwise_mutual_information_with_evaluator_labels" in report
    assert (output / "mechanism_survival_report.json").exists()
    assert (output / "alias_ceiling.json").exists()
    assert (output / "projection_collapse_matrix.json").exists()


def test_stage4_source_pretrain_runs_mlp_and_attention_vq_after_survival_gate(tmp_path: Path) -> None:
    source = _write_source_freeze(tmp_path)
    ceiling = tmp_path / "S4_0_5"
    run_stage4_source_surface_survival_audit(stage4_source_dir=source, output_dir=ceiling, max_iter=5)
    output = tmp_path / "S4_1"

    result = run_stage4_source_pretrain(stage4_source_dir=source, source_ceiling_dir=ceiling, output_dir=output, k=4, code_dim=4, max_iter=5)

    assert result["decision"] == "stage4_source_pretrain_passed"
    assert result["model_selection_audit"]["validation_visible_replay_used_for_selection"] is True
    assert result["model_selection_audit"]["ari_nmi_used_for_selection"] is False
    assert "mlp_continuous" in result["models"]
    assert "attention_vq" in result["models"]
    assert result["codebook_usage"]["active_code_count"] >= 1
    assert (output / "source_codebook.npz").exists()
    payload = np.load(output / "source_codebook.npz", allow_pickle=True)
    assert "standardization_mean" in payload.files
    assert "standardization_scale" in payload.files
    assert (output / "codebook_usage.json").exists()
    assert (output / "prototype_cards.json").exists()


def test_stage4_source_pretrain_blocks_failed_surface(tmp_path: Path) -> None:
    source = _write_source_freeze(tmp_path)
    ceiling = tmp_path / "failed_ceiling"
    ceiling.mkdir()
    (ceiling / "mechanism_survival_report.json").write_text(json.dumps({"decision": "bridge_surface_fail"}) + "\n")

    try:
        run_stage4_source_pretrain(stage4_source_dir=source, source_ceiling_dir=ceiling, output_dir=tmp_path / "S4_1")
    except ValueError as exc:
        assert "blocks" in str(exc)
    else:
        raise AssertionError("expected failed source surface to block S4.1")


def test_stage4_google_transfer_and_diagnostics_write_claim_boundary(tmp_path: Path) -> None:
    source = _write_source_freeze(tmp_path)
    ceiling = tmp_path / "S4_0_5"
    run_stage4_source_surface_survival_audit(stage4_source_dir=source, output_dir=ceiling, max_iter=5)
    pretrain = tmp_path / "S4_1"
    run_stage4_source_pretrain(stage4_source_dir=source, source_ceiling_dir=ceiling, output_dir=pretrain, k=4, code_dim=4, max_iter=5)
    transfer_out = tmp_path / "S4_2"

    result = run_stage4_google_transfer(source_pretrain_dir=pretrain, google_stage3a_dir=source, output_dir=transfer_out)

    boundary = result["claim_boundary"]
    assert boundary["claims_true_google_physical_mechanism_recovery"] is False
    assert boundary["claims_google_m_label_recovery"] is False
    assert boundary["claims_visible_syndrome_response_replay"] is True
    assert result["acceptance_audit"]["checks"]["raw_target_beats_random_codebook"] is True
    assert (transfer_out / "claim_boundary.json").exists()
    assert (transfer_out / "coordinate_system_audit.json").exists()
    assert (transfer_out / "replay_head_audit.json").exists()
    assert result["coordinate_system_audit"]["source_standardization_loaded"] is True
    assert result["replay_head_audit"]["trains_codebook"] is False

    diagnostics = run_stage4_transfer_diagnostics(source_pretrain_dir=pretrain, google_stage3a_dir=source, output_dir=tmp_path / "S4_3")
    assert diagnostics["does_not_replace_main_claim"] is True
    assert "strict_frozen_transfer" in diagnostics
    assert "frozen_codebook_train_adapter" in diagnostics
    assert (tmp_path / "S4_3" / "domain_shift_report.json").exists()
    assert (tmp_path / "S4_3" / "failure_taxonomy.json").exists()


def test_stage4_support_alignment_audit_reports_source_google_support(tmp_path: Path) -> None:
    source = _write_source_freeze(tmp_path)
    ceiling = tmp_path / "S4_0_5"
    run_stage4_source_surface_survival_audit(stage4_source_dir=source, output_dir=ceiling, max_iter=5)
    pretrain = tmp_path / "S4_1"
    run_stage4_source_pretrain(stage4_source_dir=source, source_ceiling_dir=ceiling, output_dir=pretrain, k=4, code_dim=4, max_iter=5)
    output = tmp_path / "support"

    result = run_stage4_support_alignment_audit(
        stage4_source_dir=source,
        google_stage3a_dir=source,
        source_pretrain_dir=pretrain,
        output_dir=output,
    )

    assert result["decision"] in {
        "source_google_support_overlap",
        "source_google_support_shifted",
        "source_google_support_mismatch",
    }
    assert result["source_google_support_report"]["feature_schema_match"] is True
    assert result["codebook_google_coverage"]["skipped"] is False
    assert (output / "source_google_support_report.json").exists()
    assert (output / "block_shift_ranking.json").exists()
    assert (output / "domain_classifier_audit.json").exists()
    assert (output / "nearest_source_coverage.json").exists()
    assert (output / "codebook_google_coverage.json").exists()


def test_stage4_assignment_geometry_repair_writes_diagnostics(tmp_path: Path) -> None:
    source = _write_source_freeze(tmp_path)
    ceiling = tmp_path / "S4_0_5"
    run_stage4_source_surface_survival_audit(stage4_source_dir=source, output_dir=ceiling, max_iter=5)
    pretrain = tmp_path / "S4_1"
    run_stage4_source_pretrain(stage4_source_dir=source, source_ceiling_dir=ceiling, output_dir=pretrain, k=4, code_dim=4, max_iter=5)
    output = tmp_path / "S4_5"

    result = run_stage4_assignment_geometry_repair(
        stage4_source_dir=source,
        source_pretrain_dir=pretrain,
        google_stage3a_dir=source,
        output_dir=output,
        k=4,
    )

    assert result["decision"] in {"s4_assignment_geometry_repaired", "s4_assignment_geometry_repair_incomplete"}
    assert result["claim_boundary"]["uses_google_ground_truth_mechanism_labels"] is False
    assert "per_code_google_count" in result["assignment_geometry_audit"]
    assert result["frozen_codebook_soft_reassignment"]["trains_code_vectors"] is False
    assert result["google_native_partition_alignment"]["not_ground_truth_mechanism_label"] is True
    assert result["raw_only_codebook_branch"]["excludes_meta_public_geometry_from_assignment"] is True
    assert (output / "assignment_geometry_audit.json").exists()
    assert (output / "frozen_codebook_soft_reassignment.json").exists()
    assert (output / "google_native_partition_alignment.json").exists()
    assert (output / "raw_only_codebook_branch.json").exists()


def test_stage4_google_unit_source_expansion_writes_split_clean_freeze_and_controls(tmp_path: Path) -> None:
    teacher = _write_teacher(tmp_path)
    google = tmp_path / "google_s3a" / "S3A_protocol_freeze"
    write_stage4_synthetic_google_shaped_freeze(teacher_dir=teacher, output_dir=google, shotblock_size=4)
    _force_google_public_geometry_fixture_values(google)
    output = tmp_path / "S4_6"

    result = run_stage4_google_unit_source_expansion(
        teacher_dir=teacher,
        google_stage3a_dir=google,
        output_dir=output,
        seed=7,
        k=4,
        shotblock_size=4,
        mixture_component_count=2,
        bootstrap_replicates=16,
        repeat_seed_count=2,
    )

    freeze = output / "S3A_protocol_freeze"
    matrix, feature_names, manifest = load_stage3a_frozen_visible_features(freeze)
    labels = load_stage4_source_evaluator_labels(freeze)
    mixture = load_stage4_source_mixture_evaluator_labels(freeze)
    separation = validate_stage4_source_label_separation(freeze)
    split = result["mode_design_split_manifest"]
    google_matrix, google_names, _google_manifest = load_stage3a_frozen_visible_features(google)
    meta_indices = [idx for idx, name in enumerate(google_names) if name.startswith("meta__public_geometry")]

    assert matrix.shape[0] == 4
    assert len(feature_names) == matrix.shape[1]
    assert np.allclose(matrix[:, meta_indices], google_matrix[:, meta_indices])
    assert manifest["loaded_from_stage3a_artifact"] is True
    assert labels.records
    assert mixture.records
    assert separation["passed"] is True
    assert result["claim_boundary"]["claims_true_google_physical_mechanism_recovery"] is False
    assert result["claim_boundary"]["claims_cptp_gksl_generation"] is False
    assert split["google_heldout_indices_used_for_missing_mode_selection"] == []
    assert set(split["design"]).isdisjoint(set(split["heldout_eval"]))
    assert result["mode_design_audit"]["used_heldout_eval_rows_for_mode_design"] is False
    assert result["mode_design_audit"]["public_context_mode_index_policy"] == "diagnostic_only_not_used_for_source_row_assignment"
    assert result["mode_design_audit"]["public_context_mode_index_key_count"] > 0
    assert result["visible_surrogate_transform_audit"]["claims_physical_channel_sampling"] is False
    assert result["visible_surrogate_transform_audit"]["claims_cptp_gksl_generation"] is False
    assert result["source_visible_calibration_audit"]["uses_google_heldout_eval_rows"] is False
    assert result["source_visible_calibration_audit"]["public_geometry_features_mirrored_per_row"] is True
    assert result["expanded_transfer_report"]["heldout_eval_only"] is True
    assert result["expanded_transfer_report"]["strict_frozen_transfer"]["scoring_profile"] == "raw_features_only_excludes_meta_public_geometry"
    assert result["expanded_transfer_report"]["strict_frozen_transfer"]["raw_feature_count"] > 0
    assert "full_visible_mae" in result["expanded_transfer_report"]["strict_frozen_transfer"]
    assert set(CONTROL_NAMES).issubset(set(result["controls"]["control_names"]))
    assert result["controls"]["control_construction"]["control_target_mean_std_only"]["uses_source_row_geometry"] is False
    assert result["controls"]["control_construction"]["control_target_mean_std_only"]["preserves_source_standardized_geometry"] is False
    assert "dmle_qec_visible_marginal_mle" in result["controls"]["baseline_names"]
    dmle_metrics = result["expanded_transfer_report"]["controls"]["dmle_qec_visible_marginal_mle"]
    assert dmle_metrics["baseline_family"] == "dmle_qec"
    assert dmle_metrics["uses_dem_parity_map"] is False
    assert dmle_metrics["baseline_metadata"]["baseline_variant"] == "scope_static_dmle_qec_style_independent_dem_mle"
    assert result["paired_bootstrap_report"]["uses_paired_heldout_rows"] is True
    assert result["paired_bootstrap_report"]["heldout_eval_only"] is True
    assert result["seed_split_repeat_report"]["heldout_only"] is True
    assert result["seed_split_repeat_report"]["repeat_seed_count_completed"] == 2
    repeat_rows = result["seed_split_repeat_report"]["repeats"]
    for repeat in repeat_rows:
        checks = repeat["checks"]
        semantic = checks["semantic_source_structure_ablation_comparisons"]
        assert {
            "no_family_structure",
            "no_mode_conditioning",
            "no_mixture_weights",
            "calibration_only",
            "geometry_mirror_only",
        }.issubset(set(semantic))
        assert "raw__marginal" in semantic["no_family_structure"]["raw_block_comparisons"]
        assert "source_ablations_beating_or_tying_strict_raw" in checks
        assert "strict_code_occupancy" in repeat
        assert "per_code_heldout_mass" in repeat["strict_code_occupancy"]
        assert "source_native_alignment" in repeat
        assert "native_mode_coverage_ratio" in repeat["source_native_alignment"]
        assert "source_family_surface_audit" in repeat
        assert "family_surface_separable" in repeat["source_family_surface_audit"]
        assert "family_mapping_audit" in repeat
        assert "mean_max_family_weight" in repeat["family_mapping_audit"]
        assert "low_margin_hard_mapping_mode_count" in repeat["family_mapping_audit"]
        assert repeat["preprocessing_audit"]["calibration_design_indices_match_repeat_design"] is True
        assert repeat["preprocessing_audit"]["uses_google_heldout_eval_rows"] is False
        assert "heldout_eval" in repeat["split_composition"]
        assert "basis" in repeat["split_composition"]["heldout_eval"]["counts"]
    assert repeat_rows[0]["preprocessing_audit"]["source_surface_rebuilt_for_this_split"] is False
    assert repeat_rows[1]["preprocessing_audit"]["source_surface_rebuilt_for_this_split"] is True
    assert result["stronger_statistical_controls_report"]["uses_google_evaluator_labels"] is False
    assert "dmle_qec_visible_marginal_mle" in result["stronger_statistical_controls_report"]["control_families"]["mechanism_mixture_claim_controls"]
    assert set(result["mechanism_source_structure_ablation_report"]["ablation_names"]) == {
        "control_no_visible_transform",
        "control_family_bucket_shuffled",
        "control_shuffled_google_native_mode",
        "control_random_mixture_same_context",
        "control_public_context_only",
    }
    assert result["family_mapping_validation_report"]["diagnosis"] in {
        "hard_family_mapping_brittle",
        "mixed_hard_mapping_and_source_surface_risk",
        "source_family_surface_or_catalog_mechanism_risk",
        "family_structure_ablation_failure_unexplained",
        "no_family_mapping_failure_detected",
    }
    assert result["robustness_closeout_report"]["decision"] in {
        "s4_6_robust_positive",
        "s4_6_robust_source_structure_positive_target_native_dominates",
        "s4_6_current_split_positive_only",
        "s4_6_robustness_inconclusive",
    }
    assert result["acceptance_audit"]["checks"]["freeze_contains_no_downstream_transfer_diagnostics"] is True
    assert (output / "mode_design_split_manifest.json").exists()
    assert (output / "mode_design_audit.json").exists()
    assert (output / "visible_surrogate_transform_audit.json").exists()
    assert (output / "source_visible_calibration_audit.json").exists()
    assert (output / "expanded_transfer_report.json").exists()
    assert (output / "paired_bootstrap_report.json").exists()
    assert (output / "seed_split_repeat_report.json").exists()
    assert (output / "stronger_statistical_controls_report.json").exists()
    assert (output / "mechanism_source_structure_ablation_report.json").exists()
    assert (output / "family_mapping_validation_report.json").exists()
    assert (output / "robustness_closeout_report.json").exists()

    for name in [
        "expanded_transfer_report.json",
        "google_native_mode_coverage.json",
        "source_google_mode_distance.json",
        "mode_design_audit.json",
        "mode_design_split_manifest.json",
        "source_visible_calibration_audit.json",
        "paired_bootstrap_report.json",
        "seed_split_repeat_report.json",
        "stronger_statistical_controls_report.json",
        "mechanism_source_structure_ablation_report.json",
        "family_mapping_validation_report.json",
        "robustness_closeout_report.json",
    ]:
        assert not (freeze / name).exists()
    for name in [
        "visible_features.npy",
        "sampled_visible_features.npy",
        "visible_feature_schema.json",
        "visible_feature_matrix.json",
        "split_manifest.json",
        "forbidden_feature_audit.json",
        "adequacy_report.json",
        "acceptance_audit.json",
        "metrics.json",
        "source_public_signature_manifest.json",
        "source_mixture_label_manifest.json",
        "source_mixture_evaluator_labels.json",
        "source_label_manifest.json",
        "source_evaluator_labels.json",
        "claim_boundary.json",
    ]:
        assert (freeze / name).exists()


def test_stage4_google_unit_source_expansion_samples_records_without_full_materialization(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    teacher = _write_teacher(tmp_path)
    google = tmp_path / "google_s3a" / "S3A_protocol_freeze"
    write_stage4_synthetic_google_shaped_freeze(teacher_dir=teacher, output_dir=google, shotblock_size=4)
    _force_google_public_geometry_fixture_values(google)

    def forbid_full_materialization(*_args: object, **_kwargs: object) -> np.ndarray:
        raise AssertionError("S4.6 mixing must not materialize full per-record observations")

    monkeypatch.setattr(s4_6_source, "_record_google_shaped_observations", forbid_full_materialization)

    result = run_stage4_google_unit_source_expansion(
        teacher_dir=teacher,
        google_stage3a_dir=google,
        output_dir=tmp_path / "S4_6_mem_guard",
        seed=11,
        k=4,
        shotblock_size=4,
        mixture_component_count=2,
        bootstrap_replicates=4,
        repeat_seed_count=1,
    )

    assert result["decision"] in {
        "stage4_google_unit_source_expansion_passed",
        "stage4_google_unit_source_expansion_failed",
    }
    assert result["paired_bootstrap_report"]["bootstrap_replicates"] == 4


def test_stage4_google_unit_direct_sampling_matches_materialized_record_sampling(tmp_path: Path) -> None:
    teacher = _write_teacher(tmp_path)
    observations = np.load(teacher / "observations.npz", allow_pickle=True)["observations"]
    records = json.loads((teacher / "oracle_mechanisms.json").read_text())["mechanisms"]

    for max_source_shots in [None, 5]:
        for sample_count in [1, 9]:
            for seed in [0, 7]:
                for record in records:
                    materialized = _record_google_shaped_observations(
                        record,
                        observations,
                        max_source_shots=max_source_shots,
                    )
                    old_rng = np.random.default_rng(seed)
                    old = materialized[old_rng.integers(0, max(1, materialized.shape[0]), size=max(1, sample_count))]
                    new_rng = np.random.default_rng(seed)
                    new = s4_6_source._sample_record_google_shaped_observations(
                        record,
                        observations,
                        sample_count=sample_count,
                        rng=new_rng,
                        max_source_shots=max_source_shots,
                    )
                    assert np.array_equal(new, old.astype(np.float64))


def test_stage4_google_unit_source_closeout_requires_seed_split_source_ablation_stability() -> None:
    report = _robustness_closeout_report(
        paired_bootstrap={
            "strict_bootstrap_mechanism_controls_passed": True,
            "strict_bootstrap_core_transfer_controls_passed": True,
            "strict_or_adapter_bootstrap_train_on_google_passed": True,
        },
        seed_split_repeat={
            "mechanism_structure_stable_raw": True,
            "mechanism_structure_stable_block": True,
            "source_ablation_stable_raw": False,
            "source_ablation_stable_block": True,
            "core_transfer_controls_stable_raw": True,
            "target_native_train_on_google_stable_raw": True,
        },
        stronger_statistical_controls={
            "mechanism_mixture_controls_passed": True,
            "core_transfer_controls_passed": True,
            "target_native_train_on_google_beaten": True,
        },
        mechanism_source_structure_ablation={"passed": True},
        current_transfer={"passed": True},
    )

    assert report["decision"] == "s4_6_current_split_positive_only"
    assert report["upgrades_current_split_positive_to_robust_positive"] is False
    assert report["mechanism_mixture_stability_passed"] is False


def test_stage4_google_unit_soft_family_weights_are_uncertainty_capped() -> None:
    weights = _soft_bucket_weights_for_mode(
        block_scores={
            "raw__spatial_corr": 10.0,
            "raw__logical_coupling": 0.2,
            "raw__stability": 0.1,
        },
        dominant_bucket="spatial_two_qubit_crosstalk",
        missing=True,
    )

    assert abs(sum(weights.values()) - 1.0) < 1.0e-12
    assert max(weights.values()) <= 0.55 + 1.0e-12
    assert sum(1 for value in weights.values() if value > 0.05) >= 2


def test_stage4_google_unit_source_expansion_cli_requires_explicit_heavy_approval(monkeypatch, tmp_path: Path) -> None:
    config = tmp_path / "stage4_google_unit_source_expansion_v1.yaml"
    config.write_text(
        "\n".join(
            [
                "stage4_google_unit_source_expansion_v1:",
                "  teacher_dir: outputs/scope_static/real_teacher",
                "  google_stage3a_dir: outputs/google_static/real_google/S3A_protocol_freeze",
                "  output_dir: outputs/scope_static/S4_bridge/S4_6_google_unit_source_expansion",
                "  k: 32",
                "  bootstrap_replicates: 256",
                "  repeat_seed_count: 3",
                "",
            ]
        )
    )
    called = False

    def fake_run(**_kwargs: object) -> dict[str, object]:
        nonlocal called
        called = True
        return {"decision": "should_not_run"}

    monkeypatch.setattr(s4_6_cli, "run_stage4_google_unit_source_expansion", fake_run)

    with pytest.raises(RuntimeError, match="--allow-heavy-run"):
        s4_6_cli.run_stage4_google_unit_source_expansion_from_config(config_path=config)

    assert called is False


def test_stage4_google_unit_source_expansion_cli_allows_explicit_smoke_budget(monkeypatch, tmp_path: Path) -> None:
    config = tmp_path / "stage4_google_unit_source_expansion_smoke.yaml"
    config.write_text(
        "\n".join(
            [
                "stage4_google_unit_source_expansion_v1:",
                "  execution_mode: smoke",
                "  teacher_dir: outputs/scope_static/smoke_teacher",
                "  google_stage3a_dir: outputs/google_static/smoke_google/S3A_protocol_freeze",
                "  output_dir: outputs/scope_static/S4_bridge/S4_6_google_unit_source_expansion_smoke",
                "  k: 4",
                "  bootstrap_replicates: 4",
                "  repeat_seed_count: 1",
                "",
            ]
        )
    )
    captured: dict[str, object] = {}

    def fake_run(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {"decision": "smoke_ran", "output_dir": kwargs["output_dir"]}

    monkeypatch.setattr(s4_6_cli, "run_stage4_google_unit_source_expansion", fake_run)

    result = s4_6_cli.run_stage4_google_unit_source_expansion_from_config(config_path=config)

    assert result["decision"] == "smoke_ran"
    assert captured["k"] == 4
    assert captured["bootstrap_replicates"] == 4
    assert captured["repeat_seed_count"] == 1


def test_stage4_target_mean_std_control_does_not_preserve_source_geometry() -> None:
    google = np.asarray(
        [
            [0.1, 0.2, 10.0],
            [0.3, 0.4, 20.0],
            [0.5, 0.6, 30.0],
            [0.7, 0.8, 40.0],
        ],
        dtype=np.float64,
    )
    control = _target_mean_std_only_control_matrix(
        google_raw=google,
        split={"design": [0, 1, 2]},
        row_count=4,
        seed=123,
    )
    affine_preserving = (google - np.mean(google, axis=0, keepdims=True)) / np.std(google, axis=0, keepdims=True)
    control_z = (control - np.mean(control, axis=0, keepdims=True)) / np.std(control, axis=0, keepdims=True)

    assert control.shape == google.shape
    assert not np.allclose(control_z, affine_preserving)


def test_stage4_bridge_contract_comparator_detects_mismatch(tmp_path: Path) -> None:
    source = _write_source_freeze(tmp_path)
    other = tmp_path / "other"
    other.mkdir()
    for path in source.iterdir():
        if path.is_file():
            target = other / path.name
            if path.suffix == ".npy":
                np.save(target, np.load(path))
            else:
                target.write_text(path.read_text())
    schema = json.loads((other / "visible_feature_schema.json").read_text())
    schema["features"] = list(reversed(schema["features"]))
    (other / "visible_feature_schema.json").write_text(json.dumps(schema, indent=2) + "\n")

    passed = compare_stage4_bridge_contract(synthetic_dir=source, google_dir=source)
    failed = compare_stage4_bridge_contract(synthetic_dir=source, google_dir=other)

    assert passed["passed"] is True
    assert failed["passed"] is False


def _write_source_freeze(tmp_path: Path) -> Path:
    teacher = _write_teacher(tmp_path)
    output = tmp_path / "S4_0" / "S3A_protocol_freeze"
    write_stage4_synthetic_google_shaped_freeze(teacher_dir=teacher, output_dir=output, shotblock_size=4)
    matrix, _names, _manifest = load_stage4_visible_matrix(output)
    assert matrix.shape[0] == 4
    return output


def _force_google_public_geometry_fixture_values(stage3a_dir: Path) -> None:
    matrix = np.load(stage3a_dir / "visible_features.npy")
    schema = json.loads((stage3a_dir / "visible_feature_schema.json").read_text())
    names = [str(row["name"]) for row in schema["features"]]
    for name, base in [
        ("meta__public_geometry__detector_count", 1000.0),
        ("meta__public_geometry__coord_t_span", 90.0),
        ("meta__public_geometry__shot_count_total", 32768.0),
    ]:
        idx = names.index(name)
        matrix[:, idx] = base + np.arange(matrix.shape[0], dtype=np.float64)
    np.save(stage3a_dir / "visible_features.npy", matrix)
    manifest = json.loads((stage3a_dir / "visible_feature_matrix.json").read_text())
    manifest["visible_features_sha256"] = matrix_digest(matrix)
    (stage3a_dir / "visible_feature_matrix.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def _write_teacher(tmp_path: Path) -> Path:
    teacher = tmp_path / "teacher"
    teacher.mkdir(exist_ok=True)
    records = [
        _record("M0", [0, 1], [0]),
        _record("M4", [2, 3], [1]),
        _record("M8", [4, 5], [2]),
        _record("M12", [6, 7], [0, 2]),
    ]
    observations = np.zeros((8, 12, 3), dtype=np.uint8)
    observations[2:4, :, 0] = np.tile([0, 1], 6)
    observations[2:4, :, 1] = 1
    observations[4:6, :, :] = np.asarray([0, 1, 1], dtype=np.uint8)
    observations[6:8, :, 0] = 1
    observations[6:8, :, 2] = np.tile([1, 0], 6)
    np.savez(
        teacher / "observations.npz",
        observations=observations,
        probe_names=np.asarray([f"probe_{idx}" for idx in range(observations.shape[0])], dtype=object),
        shots=np.asarray([observations.shape[1]], dtype=np.int64),
    )
    (teacher / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}, indent=2) + "\n")
    (teacher / "teacher_config.json").write_text(json.dumps({"teacher": "tiny_stage4_fixture"}, indent=2) + "\n")
    return teacher


def _record(label: str, probes: list[int], qubits: list[int]) -> dict[str, object]:
    return {
        "oracle_label": label,
        "mechanism_id": label,
        "name": f"{label}_fixture_mechanism",
        "mechanism_set": "fixture",
        "num_qubits": 3,
        "parameters": {},
        "instruction": "id",
        "qubits": qubits,
        "circuit_id": int(probes[0]),
        "location_id": int(probes[0]),
        "probe_indices": probes,
    }
