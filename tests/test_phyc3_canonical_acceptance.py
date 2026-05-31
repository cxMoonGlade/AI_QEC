from __future__ import annotations

import json
import math
from pathlib import Path

from scope_static.learner import run_phyc3_canonical_acceptance
from scope_static.experiments.qec_noise_catalog.learner_acceptance import run_learner_acceptance_from_config


def test_phyc3_canonical_acceptance_selects_phyc3c_and_writes_quality(tmp_path: Path) -> None:
    paths = _write_acceptance_fixture(tmp_path)

    result = run_phyc3_canonical_acceptance(**paths, output_dir=tmp_path / "PHYC3_canonical")

    assert result["stage"] == "PHYC3_canonical_quality_acceptance"
    assert result["public_layer"]["stage_name"] == "Learner Classification and Noise Generation (Learner)"
    assert result["public_layer"]["legacy_alias"] == "PHYC3"
    assert [row["stage_index"] for row in result["public_layer_stack"]] == [1, 2, 3]
    assert result["contract_passed"] is True
    assert result["decision"] == "phyc3_canonical_quality_accepted"
    assert result["canonical_prediction_source"]["source_name"] == "phyc3c_distributional_gaussian_likelihood_head"
    assert result["canonical_quality_metrics"]["passed"] is True
    assert result["canonical_quality_metrics"]["classification_accuracy"] == 1.0
    assert result["canonical_quality_metrics"]["incompatible_prediction_count"] == 0
    generation = result["learner_generation_quality_metrics"]
    assert generation["prediction_source"] == "phyc3c_distributional_gaussian_likelihood_head"
    assert generation["no_leakage_audit"]["generation_uses_predicted_label_not_true_label"] is True
    assert generation["num_batches"] == 4
    assert math.isfinite(generation["visible_gaussian_nll_nats_per_feature"]["mean"])
    assert math.isfinite(generation["visible_raw_feature_mae"]["mean"])
    assert result["phyc3a_baseline_audit"]["passed"] is True
    assert all(not row["accepted_as_canonical"] for row in result["rejected_sources"]["sources"])
    for name in [
        "metrics.json",
        "summary.md",
        "provenance_audit.json",
        "acceptance_checks.json",
        "canonical_quality_metrics.json",
        "learner_generation_quality.json",
        "rejected_sources.json",
        "canonical_prediction_source.json",
    ]:
        assert (tmp_path / "PHYC3_canonical" / name).exists()


def test_phyc3_canonical_acceptance_rejects_phyc2_that_emits_learner_predictions(tmp_path: Path) -> None:
    paths = _write_acceptance_fixture(tmp_path)
    phyc2_metrics = json.loads((paths["phyc2_dir"] / "metrics.json").read_text())
    phyc2_metrics["phyc2_emits_learner_grouped_predictions"] = True
    phyc2_metrics["sampled_observation_learner_diagnostic"] = {"legacy": True}
    (paths["phyc2_dir"] / "metrics.json").write_text(json.dumps(phyc2_metrics))

    result = run_phyc3_canonical_acceptance(**paths, output_dir=tmp_path / "PHYC3_canonical_bad")

    assert result["contract_passed"] is False
    assert result["phyc2_teacher_self_audit"]["checks"]["phyc2_emits_no_learner_predictions"] is False
    assert result["phyc2_teacher_self_audit"]["checks"]["phyc2_has_no_legacy_learner_diagnostic"] is False


def test_phyc3_canonical_acceptance_requires_phyc3c_multi_context_protocol(tmp_path: Path) -> None:
    paths = _write_acceptance_fixture(tmp_path)
    phyc3c_metrics = json.loads((paths["phyc3c_dir"] / "metrics.json").read_text())
    phyc3c_metrics["primary_mode"] = "single_realization"
    (paths["phyc3c_dir"] / "metrics.json").write_text(json.dumps(phyc3c_metrics))

    result = run_phyc3_canonical_acceptance(**paths, output_dir=tmp_path / "PHYC3_canonical_single")

    assert result["contract_passed"] is False
    assert result["phyc3c_accepted_learner_audit"]["checks"]["primary_mode_is_multi_context"] is False


def test_layer3_canonical_acceptance_config_alias(tmp_path: Path) -> None:
    paths = _write_acceptance_fixture(tmp_path)
    config = {
        "layer3_canonical_acceptance": {
            "teacher_dir": str(paths["teacher_dir"]),
            "phyc2_dir": str(paths["phyc2_dir"]),
            "phyc3a_dir": str(paths["phyc3a_dir"]),
            "phyc3b_dir": str(paths["phyc3b_dir"]),
            "phyc3c_dir": str(paths["phyc3c_dir"]),
            "phyc3c_validation_dir": str(paths["phyc3c_validation_dir"]),
            "output_dir": str(tmp_path / "Learner_canonical"),
        }
    }
    config_path = tmp_path / "layer3.yaml"
    config_path.write_text(json.dumps(config))

    result = run_learner_acceptance_from_config(config_path=config_path)

    assert result["contract_passed"] is True
    assert result["public_layer"]["layer_short_name"] == "Learner"


def _write_acceptance_fixture(tmp_path: Path) -> dict[str, Path]:
    teacher = tmp_path / "teacher"
    phyc2 = tmp_path / "PHYC2_teacher_self_only_v4"
    phyc3a = tmp_path / "PHYC3a_old_surface"
    phyc3b = tmp_path / "PHYC3b"
    phyc3c = tmp_path / "PHYC3c"
    validation = tmp_path / "PHYC3c_validation"
    for path in [teacher, phyc2, phyc3a, phyc3b, phyc3c, validation]:
        path.mkdir()
    records = [
        _record(0, "M0", "local_stochastic_pauli_gate_error", "id", {"p_x": 0.001, "p_y": 0.001, "p_z": 0.001}),
        _record(0, "M6", "coherent_rx_overrotation", "rx", {"epsilon": 0.025}),
        _record(1, "M0", "local_stochastic_pauli_gate_error", "id", {"p_x": 0.001, "p_y": 0.001, "p_z": 0.001}),
        _record(1, "M6", "coherent_rx_overrotation", "rx", {"epsilon": 0.025}),
    ]
    _write_json(teacher / "oracle_mechanisms.json", {"mechanisms": records})
    _write_json(
        phyc2 / "metrics.json",
        {
            "stage": "PHYC2_sampled_observation_separability",
            "contract_passed": True,
            "balanced_accuracy": 1.0,
            "adjusted_rand_index": 1.0,
            "normalized_mutual_info": 1.0,
            "min_class_recall": 1.0,
            "phyc2_emits_learner_grouped_predictions": False,
        },
    )
    _write_json(
        phyc3a / "metrics.json",
        {
            "stage": "PHYC3_no_leakage_learner_recovery",
            "decision": "no_leakage_learner_recovery_failed",
            "contract_passed": False,
            "balanced_accuracy": 0.5,
            "adjusted_rand_index": 0.0,
            "normalized_mutual_info": 0.0,
            "teacher_self_predictions_allowed": False,
        },
    )
    _write_json(
        phyc3b / "metrics.json",
        {
            "stage": "PHYC3b_ZX_visible_alias_breaking_probe_suite",
            "visible_signature_conflicts_after": 0,
            "deterministic_ceiling_BA_after": 1.0,
            "deterministic_ceiling_ARI_after": 1.0,
            "deterministic_ceiling_NMI_after": 1.0,
            "leakage_guardrail_audit": {"passed": True},
        },
    )
    _write_json(
        phyc3c / "metrics.json",
        _phyc3c_metrics(str(teacher)),
    )
    _write_json(
        validation / "metrics.json",
        {
            "stage": "PHYC3c_robust_non_leaky_protocol_validation",
            "decision": "phyc3c_robust_non_leaky_protocol_valid",
            "robustness_passed": True,
            "non_leakage_passed": True,
            "protocol_validity_passed": True,
        },
    )
    return {
        "teacher_dir": teacher,
        "phyc2_dir": phyc2,
        "phyc3a_dir": phyc3a,
        "phyc3b_dir": phyc3b,
        "phyc3c_dir": phyc3c,
        "phyc3c_validation_dir": validation,
    }


def _phyc3c_metrics(teacher_dir: str) -> dict[str, object]:
    folds = [
        {
            "fold": 0,
            "train_groups": [1],
            "test_groups": [0],
            "true_labels": ["M0", "M6"],
            "predicted_labels": ["M0", "M6"],
            "batches": [
                {"true_label_evaluator_only": "M0", "predicted_label": "M0", "test_groups": [0], "num_contexts": 1},
                {"true_label_evaluator_only": "M6", "predicted_label": "M6", "test_groups": [0], "num_contexts": 1},
            ],
        },
        {
            "fold": 1,
            "train_groups": [0],
            "test_groups": [1],
            "true_labels": ["M0", "M6"],
            "predicted_labels": ["M0", "M6"],
            "batches": [
                {"true_label_evaluator_only": "M0", "predicted_label": "M0", "test_groups": [1], "num_contexts": 1},
                {"true_label_evaluator_only": "M6", "predicted_label": "M6", "test_groups": [1], "num_contexts": 1},
            ],
        },
    ]
    return {
        "stage": "PHYC3c_distributional_gaussian_likelihood_head",
        "teacher_dir": teacher_dir,
        "primary_mode": "multi_context_batch",
        "primary_head": "PHYC3c_diagonal_gaussian",
        "learner_BA": 1.0,
        "learner_ARI": 1.0,
        "learner_NMI": 1.0,
        "min_recall": 1.0,
        "m13_recall": 1.0,
        "leakage_guardrail_audit": {"passed": True},
        "multi_context_batch_mode": {
            "head_results": {
                "PHYC3c_diagonal_gaussian": {
                    "balanced_accuracy": 1.0,
                    "adjusted_rand_index": 1.0,
                    "normalized_mutual_info": 1.0,
                    "min_class_recall": 1.0,
                    "m13_recall": 1.0,
                    "grouped_fold_predictions": folds,
                }
            }
        },
    }


def _record(group: int, mechanism_id: str, name: str, instruction: str, parameters: dict[str, float]) -> dict[str, object]:
    return {
        "oracle_label": mechanism_id,
        "mechanism_id": mechanism_id,
        "name": name,
        "num_qubits": 1,
        "parameters": parameters,
        "instruction": instruction,
        "qubits": [0],
        "circuit_id": int(group),
        "location_id": int(group),
        "probe_indices": [],
    }


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
