from __future__ import annotations

import json
from pathlib import Path

from scope_static.experiments.stage3.context_shuffle_audit import run_stage3d3_context_shuffle_audit_from_config
from scope_static.mechanism_discovery.context_shuffle_audit import run_stage3d3_context_shuffle_audit
from scope_static.mechanism_discovery.discovery_model import run_stage3b1_first_discovery_model
from scope_static.mechanism_discovery.generator_learning import run_stage3c_prototype_generator_learning
from scope_static.mechanism_discovery.observability_ceiling import run_stage3a5_observability_alias_ceiling
from scope_static.mechanism_discovery.protocol_freeze import run_stage3a_dataset_protocol_freeze
from scope_static.primitives.mechanism_catalog import MECHANISM_NAMES


def test_stage3d3_context_shuffle_audits_protocol_only_context_groups(tmp_path: Path) -> None:
    _teacher, s3a, s3a5, s3b1, s3c = _prepare_artifacts(
        tmp_path,
        [
            ("M0", "M0"),
            ("M4", "M4"),
            ("M8", "M8"),
        ],
    )
    output = tmp_path / "S3D3"

    result = run_stage3d3_context_shuffle_audit(
        stage3a_dir=s3a,
        stage3a5_dir=s3a5,
        stage3b1_dir=s3b1,
        stage3c_dir=s3c,
        output_dir=output,
        seed=7,
        shuffle_count=5,
        max_original_advantage_over_context_shuffle=10.0,
    )

    assert result["decision"] == "stage3d3_context_shuffle_audit_passed"
    assert result["claim_boundary"]["keeps_visible_features_fixed"] is True
    assert result["claim_boundary"]["keeps_discovered_assignments_fixed"] is True
    assert result["claim_boundary"]["scrambles_protocol_only_context_groups"] is True
    assert result["claim_boundary"]["uses_mechanism_labels_for_generator_fit"] is False
    assert result["visible_feature_matrix"]["loaded_from_stage3a_artifact"] is True
    assert result["assignment_source_audit"]["row_stochastic"] is True
    assert result["context_protocol_audit"]["passed"] is True
    assert result["leakage_audit"]["passed"] is True
    assert result["s3c_consistency_audit"]["passed"] is True
    assert "selected_model_uses_context_groups" in result["selected_context_usage_audit"]

    report = result["context_shuffle_metrics"]["primary_context_report"]
    assert report["original_assignment"] is not None
    assert report["context_shuffled_assignment_mean"] is not None
    assert report["original_global_null_minus_original_lift"] > 0.0

    summary = result["context_shuffled_metrics_summary"]
    assert summary["all_visible_features_fixed"] is True
    assert summary["all_assignments_fixed"] is True
    assert summary["all_context_group_multisets_preserved"] is True
    assert summary["all_context_alignments_changed"] is True
    assert summary["all_fold_indices_changed"] is True

    for run in result["context_shuffle_runs"]:
        assert run["visible_features_fixed"] is True
        assert run["assignments_fixed"] is True
        assert run["context_group_multiset_preserved"] is True
        assert run["fold_indices_changed"] is True
        assert run["assignment_matrix_row_stochastic"] is True

    for name in [
        "metrics.json",
        "context_shuffle_metrics.json",
        "original_assignment_metrics.json",
        "original_global_null_metrics.json",
        "original_mean_only_baseline_metrics.json",
        "context_shuffled_metrics_summary.json",
        "context_shuffle_runs.json",
        "context_protocol_audit.json",
        "selected_context_usage_audit.json",
        "s3c_consistency_audit.json",
        "leakage_audit.json",
        "acceptance_audit.json",
        "summary.md",
    ]:
        assert (output / name).exists()


def test_stage3d3_config_wrapper_runs_from_yaml(tmp_path: Path) -> None:
    _teacher, s3a, s3a5, s3b1, _s3c = _prepare_artifacts(
        tmp_path,
        [
            ("M0", "M0"),
            ("M4", "M4"),
            ("M8", "M8"),
        ],
        run_s3c=False,
    )
    output = tmp_path / "configured"
    config = tmp_path / "stage3d3.yaml"
    config.write_text(
        "\n".join(
            [
                "stage3d3_context_shuffle_audit:",
                f"  stage3a_dir: {s3a}",
                f"  stage3a5_dir: {s3a5}",
                f"  stage3b1_dir: {s3b1}",
                "  stage3c_dir:",
                f"  output_dir: {output}",
                "  seed: 11",
                "  shuffle_count: 3",
                "  max_cv_folds: 2",
                "  max_original_advantage_over_context_shuffle: 10.0",
            ]
        )
        + "\n"
    )

    result = run_stage3d3_context_shuffle_audit_from_config(config_path=config)

    assert result["decision"] == "stage3d3_context_shuffle_audit_passed"
    assert (output / "context_shuffle_metrics.json").exists()


def test_stage3d3_rejects_zero_shuffle_count(tmp_path: Path) -> None:
    _teacher, s3a, s3a5, s3b1, _s3c = _prepare_artifacts(
        tmp_path,
        [
            ("M0", "M0"),
            ("M4", "M4"),
            ("M8", "M8"),
        ],
        run_s3c=False,
    )

    result = run_stage3d3_context_shuffle_audit(
        stage3a_dir=s3a,
        stage3a5_dir=s3a5,
        stage3b1_dir=s3b1,
        stage3c_dir=None,
        output_dir=tmp_path / "S3D3",
        shuffle_count=0,
        max_original_advantage_over_context_shuffle=10.0,
    )

    assert result["decision"] == "stage3d3_context_shuffle_audit_failed"
    assert result["acceptance_audit"]["checks"]["shuffle_count_positive"] is False


def _prepare_artifacts(
    tmp_path: Path,
    label_specs: list[tuple[str, str]],
    *,
    run_s3c: bool = True,
) -> tuple[Path, Path, Path, Path, Path | None]:
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
    s3c = tmp_path / "S3C"
    run_stage3a_dataset_protocol_freeze(teacher_dir=teacher, output_dir=s3a, shots=1000, batch_size=2)
    run_stage3a5_observability_alias_ceiling(stage3a_dir=s3a, output_dir=s3a5)
    run_stage3b1_first_discovery_model(stage3a_dir=s3a, stage3a5_dir=s3a5, output_dir=s3b1, max_iter=15)
    if run_s3c:
        run_stage3c_prototype_generator_learning(stage3a_dir=s3a, stage3a5_dir=s3a5, stage3b1_dir=s3b1, output_dir=s3c)
        return teacher, s3a, s3a5, s3b1, s3c
    return teacher, s3a, s3a5, s3b1, None


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
