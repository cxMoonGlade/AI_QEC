from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from scope_static.experiments.stage3.generator_learning import run_stage3c_generator_learning_from_config
from scope_static.primitives.mechanism_catalog import MECHANISM_NAMES
from scope_static.mechanism_discovery.protocol_freeze import run_stage3a_dataset_protocol_freeze
from scope_static.mechanism_discovery.observability_ceiling import run_stage3a5_observability_alias_ceiling
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
    assert result["claim_boundary"]["oracle_assignment_comparator_evaluator_only"] is True
    assert result["visible_feature_matrix"]["loaded_from_stage3a_artifact"] is True
    assert result["assignment_source_audit"]["row_stochastic"] is True
    assert result["leakage_audit"]["passed"] is True
    assert result["prototype_generation_metrics"]["primary_generation_likelihood_metric"] == "categorical_population_nll"
    assert result["prototype_generation_metrics"]["secondary_continuous_density_diagnostic"] == "gaussian_density_nll"
    assert result["acceptance_audit"]["checks"]["heldout_generation_beats_global_null_categorical_population_nll"] is True
    assert result["acceptance_audit"]["checks"]["heldout_generation_beats_mean_only_mae"] is True

    predicted = result["predicted_assignment_metrics"]["overall"]
    global_null = result["global_null_metrics"]["overall"]
    oracle = result["oracle_assignment_comparator_metrics"]["overall"]
    report = result["prototype_generation_metrics"]["primary_likelihood_report"]
    assert predicted["categorical_population_nll"] >= 0.0
    assert oracle["categorical_population_nll"] >= 0.0
    assert predicted["categorical_population_nll"] < global_null["categorical_population_nll"]
    assert report["predicted_assignment"] == predicted["categorical_population_nll"]
    assert report["oracle_assignment_comparator"] == oracle["categorical_population_nll"]
    assert report["predicted_minus_oracle_gap"] == result["prototype_generation_metrics"]["oracle_comparator_gap"]["categorical_population_nll_gap"]
    assert predicted["gaussian_density_nll"] == predicted["gaussian_nll"]
    assert predicted["gaussian_density_nll"] < global_null["gaussian_density_nll"]
    assert oracle["raw_visible_feature_mae"] <= predicted["raw_visible_feature_mae"] + 1.0e-12
    assert result["oracle_assignment_comparator_metrics"]["uses_evaluator_labels"] is True
    assert result["oracle_assignment_comparator_metrics"]["used_for_acceptance_model_selection"] is False

    for name in [
        "metrics.json",
        "prototype_generation_metrics.json",
        "predicted_assignment_metrics.json",
        "oracle_assignment_comparator_metrics.json",
        "global_null_metrics.json",
        "mean_only_baseline_metrics.json",
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
