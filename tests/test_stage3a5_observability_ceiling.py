from __future__ import annotations

import json
from pathlib import Path

from scope_static.experiments.stage3.observability_ceiling import run_stage3a5_observability_ceiling_from_config
from scope_static.primitives.mechanism_catalog import MECHANISM_NAMES
from scope_static.mechanism_discovery.protocol_freeze import run_stage3a_dataset_protocol_freeze
from scope_static.mechanism_discovery.observability_ceiling import run_stage3a5_observability_alias_ceiling


def test_stage3a5_reports_alias_quotient_when_two_labels_share_visible_distribution(tmp_path: Path) -> None:
    teacher = tmp_path / "S2D_PHYC1_teacher"
    teacher.mkdir()
    records = []
    for group in range(3):
        records.extend([_record("AliasA", "M0", group), _record("AliasB", "M0", group), _record("M4", "M4", group)])
    (teacher / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}, indent=2) + "\n")
    s3a_dir = tmp_path / "S3A"
    run_stage3a_dataset_protocol_freeze(teacher_dir=teacher, output_dir=s3a_dir, shots=1000, batch_size=2)

    result = run_stage3a5_observability_alias_ceiling(stage3a_dir=s3a_dir, output_dir=tmp_path / "S3A5")

    alias = result["oracle_alias_classes"]
    assert result["decision"] == "stage3a5_observability_ceiling_passed"
    assert alias["exact_label_recovery_claim_allowed"] is False
    assert any(set(row["mechanisms"]) == {"AliasA", "AliasB"} for row in alias["alias_classes"])
    assert result["claim_boundary"]["target_if_exact_not_visible"] == "quotient_recovery"
    assert result["claim_boundary"]["uses_stage3a_frozen_visible_features"] is True
    assert result["visible_feature_matrix"]["loaded_from_stage3a_artifact"] is True
    assert result["acceptance_audit"]["checks"]["uses_stage3a_frozen_visible_features"] is True
    exact = result["evaluator_only_label_metrics"]["exact_label_ceiling"]
    quotient = result["evaluator_only_label_metrics"]["quotient_label_ceiling"]
    assert exact["balanced_accuracy"] < 1.0
    assert quotient["balanced_accuracy"] == 1.0
    assert quotient["normalized_mutual_info"] == 1.0

    output = tmp_path / "S3A5"
    for name in [
        "metrics.json",
        "observability_ceiling.json",
        "oracle_alias_classes.json",
        "pairwise_visible_distance_matrix.json",
        "evaluator_only_label_metrics.json",
        "quotient_metrics.json",
        "acceptance_audit.json",
        "feature_schema_match_audit.json",
        "visible_feature_matrix.json",
        "config.yaml",
        "summary.md",
    ]:
        assert (output / name).exists()
    assert not (output / "learned_assignments.npy").exists()


def test_stage3a5_allows_exact_label_claim_when_visible_surface_separates_mechanisms(tmp_path: Path) -> None:
    teacher = tmp_path / "S2D_PHYC1_teacher"
    teacher.mkdir()
    records = []
    for group in range(3):
        records.extend([_record("M0", "M0", group), _record("M4", "M4", group), _record("M8", "M8", group)])
    (teacher / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}, indent=2) + "\n")
    s3a_dir = tmp_path / "S3A"
    run_stage3a_dataset_protocol_freeze(teacher_dir=teacher, output_dir=s3a_dir, shots=1000, batch_size=2)

    result = run_stage3a5_observability_alias_ceiling(stage3a_dir=s3a_dir, output_dir=tmp_path / "S3A5")

    assert result["oracle_alias_classes"]["alias_class_count"] == 0
    assert result["oracle_alias_classes"]["exact_label_recovery_claim_allowed"] is True
    assert result["evaluator_only_label_metrics"]["exact_label_ceiling"]["balanced_accuracy"] == 1.0
    assert result["evaluator_only_label_metrics"]["quotient_label_ceiling"]["balanced_accuracy"] == 1.0


def test_stage3a5_config_wrapper_runs_from_yaml(tmp_path: Path) -> None:
    teacher = tmp_path / "S2D_PHYC1_teacher"
    teacher.mkdir()
    records = []
    for group in range(3):
        records.extend([_record("M0", "M0", group), _record("M4", "M4", group)])
    (teacher / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}, indent=2) + "\n")
    s3a_dir = tmp_path / "S3A"
    run_stage3a_dataset_protocol_freeze(teacher_dir=teacher, output_dir=s3a_dir, shots=1000, batch_size=2)
    output = tmp_path / "configured"
    config = tmp_path / "stage3a5.yaml"
    config.write_text(
        "\n".join(
            [
                "stage3a5_observability_alias_ceiling:",
                f"  stage3a_dir: {s3a_dir}",
                f"  output_dir: {output}",
                "  distance_threshold: 1.0e-9",
                "  signature_decimals: 10",
            ]
        )
        + "\n"
    )

    result = run_stage3a5_observability_ceiling_from_config(config_path=config)

    assert result["decision"] == "stage3a5_observability_ceiling_passed"
    assert (output / "oracle_alias_classes.json").exists()


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
