from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from scope_static.mechanism_discovery.artifacts import matrix_digest
from scope_static.mechanism_discovery.observability_abc_diagnostic import run_stage3_abc_observability_diagnostic


def test_stage3_abc_runs_current_surface_and_keeps_no_oracle_boundary(tmp_path: Path) -> None:
    labels = ["M6", "M13", "M22", "M23"] * 4
    matrix = _separable_matrix(labels)
    teacher, s3a = _write_stage3a_fixture(tmp_path / "current", labels=labels, matrix=matrix)

    result = run_stage3_abc_observability_diagnostic(
        stage3a_dir=s3a,
        teacher_dir=teacher,
        output_dir=tmp_path / "ABC",
        target_groups=(("M6", "M13", "M22", "M23"),),
        feature_profiles=("raw_only",),
        vq_k_values=(4,),
        max_cv_folds=1,
        seed=0,
        mlp_epochs=5,
        mlp_hidden_dim=8,
        pass_min_recall=0.9,
    )

    assert result["decision"] == "stage3_abc_observability_diagnostic_completed"
    assert result["claim_boundary"]["diagnostic_only"] is True
    assert result["claim_boundary"]["b_representation_uses_evaluator_labels_for_fit"] is False
    assert result["abc_decision_audit"]["enhanced_probe_ran"] is False
    assert result["abc_decision_audit"]["enhanced_probe_skip_reason"] == "enhanced_stage3a_dir_not_provided"
    row_name = "M6_vs_M13_vs_M22_vs_M23"
    supervised = result["supervised_upper_bound_audit"]["rows"][row_name]["best"]
    no_oracle = result["no_oracle_representation_audit"]["rows"][row_name]["best"]
    no_oracle_row = result["no_oracle_representation_audit"]["rows"][row_name]
    assert supervised["min_recall"] >= 0.9
    assert no_oracle_row["best_selection_rule"] == "min_visible_reconstruction_mse"
    assert "best_posthoc_diagnostic" in no_oracle_row
    assert no_oracle["uses_evaluator_labels_for_fit"] is False
    assert no_oracle["uses_evaluator_labels_for_model_selection"] is False
    assert no_oracle["min_recall"] >= 0.9

    output = tmp_path / "ABC"
    for name in [
        "metrics.json",
        "supervised_upper_bound_audit.json",
        "no_oracle_representation_audit.json",
        "enhanced_probe_upper_bound_audit.json",
        "abc_decision_audit.json",
        "summary.md",
    ]:
        assert (output / name).exists()


def test_stage3_abc_enhanced_probe_records_improvement(tmp_path: Path) -> None:
    labels = ["M6", "M13", "M22", "M23"] * 3
    current = np.zeros((len(labels), 3), dtype=np.float64)
    current[:, 2] = np.linspace(0.0, 1.0, len(labels))
    enhanced = _separable_matrix(labels)
    current_teacher, current_s3a = _write_stage3a_fixture(tmp_path / "current", labels=labels, matrix=current)
    enhanced_teacher, enhanced_s3a = _write_stage3a_fixture(tmp_path / "enhanced", labels=labels, matrix=enhanced)

    result = run_stage3_abc_observability_diagnostic(
        stage3a_dir=current_s3a,
        teacher_dir=current_teacher,
        enhanced_stage3a_dir=enhanced_s3a,
        enhanced_teacher_dir=enhanced_teacher,
        output_dir=tmp_path / "ABC",
        target_groups=(("M6", "M13", "M22", "M23"),),
        feature_profiles=("raw_only",),
        vq_k_values=(4,),
        max_cv_folds=1,
        seed=1,
        mlp_epochs=5,
        mlp_hidden_dim=8,
        pass_min_recall=0.9,
    )

    row = result["abc_decision_audit"]["rows"]["M6_vs_M13_vs_M22_vs_M23"]
    assert result["abc_decision_audit"]["enhanced_probe_ran"] is True
    assert row["current_supervised_min_recall"] < 0.9
    assert row["enhanced_supervised_min_recall"] >= 0.9
    assert row["enhanced_probe_improved"] is True
    assert row["interpretation"] == "current_visible_surface_insufficient_for_supervised_upper_bound"


def test_stage3_abc_enhanced_probe_requires_actual_improvement(tmp_path: Path) -> None:
    labels = ["M6", "M13", "M22", "M23"] * 3
    matrix = _separable_matrix(labels)
    current_teacher, current_s3a = _write_stage3a_fixture(tmp_path / "current", labels=labels, matrix=matrix)
    enhanced_teacher, enhanced_s3a = _write_stage3a_fixture(tmp_path / "enhanced", labels=labels, matrix=matrix)

    result = run_stage3_abc_observability_diagnostic(
        stage3a_dir=current_s3a,
        teacher_dir=current_teacher,
        enhanced_stage3a_dir=enhanced_s3a,
        enhanced_teacher_dir=enhanced_teacher,
        output_dir=tmp_path / "ABC",
        target_groups=(("M6", "M13", "M22", "M23"),),
        feature_profiles=("raw_only",),
        vq_k_values=(4,),
        max_cv_folds=1,
        seed=1,
        mlp_epochs=5,
        mlp_hidden_dim=8,
        pass_min_recall=0.9,
    )

    row = result["abc_decision_audit"]["rows"]["M6_vs_M13_vs_M22_vs_M23"]
    assert row["current_supervised_min_recall"] >= 0.9
    assert row["enhanced_supervised_min_recall"] == row["current_supervised_min_recall"]
    assert row["enhanced_probe_improved"] is False


def test_stage3_abc_rejects_pair_only_target_groups(tmp_path: Path) -> None:
    labels = ["M6", "M13", "M22", "M23"] * 3
    matrix = _separable_matrix(labels)
    teacher, s3a = _write_stage3a_fixture(tmp_path / "current", labels=labels, matrix=matrix)

    with pytest.raises(ValueError, match="pair-only target groups are forbidden"):
        run_stage3_abc_observability_diagnostic(
            stage3a_dir=s3a,
            teacher_dir=teacher,
            output_dir=tmp_path / "ABC",
            target_groups=(("M22", "M23"),),
            feature_profiles=("raw_only",),
            vq_k_values=(4,),
            max_cv_folds=1,
            seed=0,
            mlp_epochs=5,
            mlp_hidden_dim=8,
            pass_min_recall=0.9,
        )


def _write_stage3a_fixture(root: Path, *, labels: list[str], matrix: np.ndarray) -> tuple[Path, Path]:
    root.mkdir(parents=True)
    teacher = root / "S2D_PHYS1_teacher"
    teacher.mkdir()
    records = [{"oracle_label": label, "mechanism_id": label} for label in labels]
    (teacher / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}, indent=2, sort_keys=True) + "\n")
    s3a = root / "S3A_protocol_freeze"
    s3a.mkdir()
    np.save(s3a / "visible_features.npy", np.asarray(matrix, dtype=np.float64))
    feature_names = [f"raw__f{idx}" for idx in range(int(matrix.shape[1]))]
    (s3a / "visible_feature_schema.json").write_text(
        json.dumps({"features": [{"name": name} for name in feature_names]}, indent=2, sort_keys=True) + "\n"
    )
    (s3a / "visible_feature_matrix.json").write_text(
        json.dumps(
            {
                "training_matrix_path": "visible_features.npy",
                "feature_schema_path": "visible_feature_schema.json",
                "shape": [int(matrix.shape[0]), int(matrix.shape[1])],
                "visible_features_sha256": matrix_digest(np.asarray(matrix, dtype=np.float64)),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    occurrence: dict[str, int] = {}
    test_indices = []
    train_indices = []
    for idx, label in enumerate(labels):
        count = occurrence.get(label, 0)
        occurrence[label] = count + 1
        if count == 0:
            test_indices.append(idx)
        else:
            train_indices.append(idx)
    split_manifest = {
        "assignment_instances": [
            {"record_index": idx, "context_group": idx % 4, "visible_instance_id": f"j{idx:06d}"}
            for idx in range(len(labels))
        ],
        "folds": [
            {
                "train_indices": train_indices,
                "validation_indices": test_indices,
                "test_indices": test_indices,
            }
        ],
    }
    (s3a / "metrics.json").write_text(
        json.dumps(
            {
                "config": {"teacher_dir": str(teacher)},
                "split_manifest": split_manifest,
                "acceptance_audit": {"passed": True},
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return teacher, s3a


def _separable_matrix(labels: list[str]) -> np.ndarray:
    prototypes = {
        "M6": np.asarray([1.0, 0.0, 0.0], dtype=np.float64),
        "M13": np.asarray([0.0, 1.0, 0.0], dtype=np.float64),
        "M22": np.asarray([0.0, 0.0, 1.0], dtype=np.float64),
        "M23": np.asarray([1.0, 1.0, 1.0], dtype=np.float64),
    }
    rows = []
    for idx, label in enumerate(labels):
        rows.append(prototypes[label] + 0.01 * float(idx % 3))
    return np.stack(rows, axis=0)
