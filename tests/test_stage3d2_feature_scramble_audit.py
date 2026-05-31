from __future__ import annotations

import json
from pathlib import Path

from scope_static.experiments.stage3.feature_scramble_audit import run_stage3d2_feature_scramble_audit_from_config
from scope_static.mechanism_discovery.discovery_model import run_stage3b1_first_discovery_model
from scope_static.mechanism_discovery.feature_scramble_audit import run_stage3d2_feature_scramble_audit
from scope_static.mechanism_discovery.generator_learning import run_stage3c_prototype_generator_learning
from scope_static.mechanism_discovery.observability_ceiling import run_stage3a5_observability_alias_ceiling
from scope_static.mechanism_discovery.protocol_freeze import run_stage3a_dataset_protocol_freeze
from scope_static.primitives.mechanism_catalog import MECHANISM_NAMES


def test_stage3d2_feature_scramble_collapses_generator_toward_null(tmp_path: Path) -> None:
    _teacher, s3a, s3a5, s3b1, s3c = _prepare_artifacts(
        tmp_path,
        [
            ("M0", "M0"),
            ("M4", "M4"),
            ("M8", "M8"),
        ],
    )
    output = tmp_path / "S3D2"

    result = run_stage3d2_feature_scramble_audit(
        stage3a_dir=s3a,
        stage3a5_dir=s3a5,
        stage3b1_dir=s3b1,
        stage3c_dir=s3c,
        output_dir=output,
        seed=7,
        scramble_count=5,
        min_collapse_fraction=0.1,
    )

    assert result["decision"] == "stage3d2_feature_scramble_audit_passed"
    assert result["claim_boundary"]["keeps_discovered_assignments_fixed"] is True
    assert result["claim_boundary"]["scrambles_stage3a_visible_feature_rows"] is True
    assert result["claim_boundary"]["uses_mechanism_labels_for_generator_fit"] is False
    assert result["visible_feature_matrix"]["loaded_from_stage3a_artifact"] is True
    assert result["assignment_source_audit"]["row_stochastic"] is True
    assert result["leakage_audit"]["passed"] is True
    assert result["s3c_consistency_audit"]["passed"] is True

    collapse = result["feature_scramble_metrics"]["primary_collapse_report"]
    assert collapse["scrambled_mean_minus_original_degradation"] > 0.0
    assert collapse["collapse_fraction_toward_global_null"] >= 0.1
    assert collapse["original_assignment"] < collapse["global_null"]
    assert collapse["scrambled_feature_mean"] > collapse["original_assignment"]

    summary = result["scrambled_feature_metrics_summary"]
    assert summary["all_assignments_fixed"] is True
    assert summary["all_feature_row_distributions_preserved"] is True
    assert summary["all_feature_row_alignments_changed"] is True

    for run in result["scramble_runs"]:
        assert run["assignments_fixed"] is True
        assert run["feature_row_distribution_preserved"] is True
        assert run["assignment_matrix_row_stochastic"] is True

    for name in [
        "metrics.json",
        "feature_scramble_metrics.json",
        "original_assignment_metrics.json",
        "scrambled_feature_metrics_summary.json",
        "feature_scramble_runs.json",
        "global_null_metrics.json",
        "mean_only_baseline_metrics.json",
        "s3c_consistency_audit.json",
        "leakage_audit.json",
        "acceptance_audit.json",
        "summary.md",
    ]:
        assert (output / name).exists()


def test_stage3d2_config_wrapper_runs_from_yaml(tmp_path: Path) -> None:
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
    config = tmp_path / "stage3d2.yaml"
    config.write_text(
        "\n".join(
            [
                "stage3d2_feature_scramble_audit:",
                f"  stage3a_dir: {s3a}",
                f"  stage3a5_dir: {s3a5}",
                f"  stage3b1_dir: {s3b1}",
                "  stage3c_dir:",
                f"  output_dir: {output}",
                "  seed: 11",
                "  scramble_count: 3",
                "  max_cv_folds: 2",
                "  min_collapse_fraction: 0.1",
            ]
        )
        + "\n"
    )

    result = run_stage3d2_feature_scramble_audit_from_config(config_path=config)

    assert result["decision"] == "stage3d2_feature_scramble_audit_passed"
    assert (output / "feature_scramble_metrics.json").exists()


def test_stage3d2_rejects_zero_scramble_count(tmp_path: Path) -> None:
    _teacher, s3a, s3a5, s3b1, _s3c = _prepare_artifacts(
        tmp_path,
        [
            ("M0", "M0"),
            ("M4", "M4"),
            ("M8", "M8"),
        ],
        run_s3c=False,
    )

    result = run_stage3d2_feature_scramble_audit(
        stage3a_dir=s3a,
        stage3a5_dir=s3a5,
        stage3b1_dir=s3b1,
        stage3c_dir=None,
        output_dir=tmp_path / "S3D2",
        scramble_count=0,
    )

    assert result["decision"] == "stage3d2_feature_scramble_audit_failed"
    assert result["acceptance_audit"]["checks"]["scramble_count_positive"] is False


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
