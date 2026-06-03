from __future__ import annotations

import json
from pathlib import Path

from scope_static.experiments.stage3.k_stress_audit import run_stage3d4_k_stress_audit_from_config
from scope_static.mechanism_discovery.discovery_model import run_stage3b1_first_discovery_model
from scope_static.mechanism_discovery.generator_learning import run_stage3c_prototype_generator_learning
from scope_static.mechanism_discovery.k_stress_audit import run_stage3d4_k_stress_audit
from scope_static.mechanism_discovery.observability_ceiling import run_stage3a5_observability_alias_ceiling
from scope_static.mechanism_discovery.protocol_freeze import run_stage3a_dataset_protocol_freeze
from scope_static.primitives.mechanism_catalog import MECHANISM_NAMES


def test_stage3d4_k_stress_reports_under_exact_overcomplete_runs(tmp_path: Path) -> None:
    _teacher, s3a, s3a5, s3b1, s3c = _prepare_artifacts(
        tmp_path,
        [
            ("M0", "M0"),
            ("M4", "M4"),
            ("M8", "M8"),
        ],
    )
    output = tmp_path / "S3D4"

    result = run_stage3d4_k_stress_audit(
        stage3a_dir=s3a,
        stage3a5_dir=s3a5,
        stage3b1_dir=s3b1,
        stage3c_dir=s3c,
        output_dir=output,
        max_iter=12,
        min_success_nmi=0.5,
        min_success_ari=0.0,
        min_success_ba=0.0,
        min_undercomplete_nmi_gap=0.0,
    )

    assert result["decision"] == "stage3d4_k_stress_audit_passed"
    assert result["claim_boundary"]["uses_mechanism_labels_for_fit"] is False
    assert result["claim_boundary"]["uses_catalog_cardinality_for_k_values_only"] is True
    assert result["claim_boundary"]["uses_stage3b1_assignment_feature_view_for_stress_geometry"] is True
    assert result["visible_feature_matrix"]["loaded_from_stage3a_artifact"] is True
    assert result["assignment_feature_view_audit"]["source"] == "stage3b1_assignment_visible_features"
    assert result["visible_feature_weighting"]["uses_visible_operation_context"] is True
    assert result["feature_schema_match_audit"]["passed"] is True
    assert result["leakage_audit"]["passed"] is True

    families = {row["stress_family"] for row in result["k_stress_results"]}
    assert {"undercomplete", "exact", "overcomplete"}.issubset(families)
    by_family = {row["stress_family"]: row for row in result["k_stress_results"]}
    assert by_family["undercomplete"]["k"] < by_family["exact"]["k"]
    assert by_family["overcomplete"]["k"] > by_family["exact"]["k"]
    assert by_family["exact"]["used_mechanism_labels_for_fit"] is False
    assert by_family["overcomplete"]["used_labels_for_model_selection"] is False

    summary = result["k_stress_summary"]
    assert summary["undercomplete_nmi_gap"] >= 0.0
    assert summary["global_null_categorical_population_nll"] is not None

    for name in [
        "metrics.json",
        "k_stress_plan.json",
        "k_stress_results.json",
        "k_stress_summary.json",
        "model_summaries.json",
        "global_null_metrics.json",
        "mean_only_baseline_metrics.json",
        "leakage_audit.json",
        "s3c_reference_audit.json",
        "acceptance_audit.json",
        "assignment_feature_view_audit.json",
        "visible_feature_weighting.json",
        "learned_assignments_by_k.npz",
        "summary.md",
    ]:
        assert (output / name).exists()


def test_stage3d4_inherits_stage3b1_context_balanced_assignment_family(tmp_path: Path) -> None:
    _teacher, s3a, s3a5, s3b1, _s3c = _prepare_artifacts(
        tmp_path,
        [
            ("M0", "M0"),
            ("M4", "M4"),
            ("M8", "M8"),
        ],
        run_s3c=False,
    )
    metrics_path = s3b1 / "metrics.json"
    metrics = json.loads(metrics_path.read_text())
    metrics.setdefault("candidate_selection", {}).setdefault("selected", {})[
        "model_family"
    ] = "context_balanced_visible_prototype_mixture"
    metrics_path.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n")

    result = run_stage3d4_k_stress_audit(
        stage3a_dir=s3a,
        stage3a5_dir=s3a5,
        stage3b1_dir=s3b1,
        stage3c_dir=None,
        output_dir=tmp_path / "S3D4",
        max_iter=8,
        min_success_nmi=0.0,
        min_success_ari=0.0,
        min_success_ba=0.0,
        min_undercomplete_nmi_gap=0.0,
    )

    by_mode = {row["mode"]: row for row in result["k_stress_results"]}
    assert by_mode["fixed_oracle_count"]["model_family"] == "context_balanced_visible_prototype_mixture"
    assert by_mode["fixed_oracle_count"]["assignment_construction"] == "stage3b1_assignment_replay"
    assert by_mode["fixed_oracle_count"]["used_context_groups_for_fit"] is True
    assert by_mode["overcomplete_2x"]["model_family"] == "s3b1_seeded_visible_overcomplete_split"
    assert by_mode["overcomplete_2x"]["assignment_construction"] == "stage3b1_seeded_visible_only_split"
    assert by_mode["overcomplete_2x"]["used_context_groups_for_fit"] is True


def test_stage3d4_config_wrapper_runs_from_yaml(tmp_path: Path) -> None:
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
    config = tmp_path / "stage3d4.yaml"
    config.write_text(
        "\n".join(
            [
                "stage3d4_k_stress_audit:",
                f"  stage3a_dir: {s3a}",
                f"  stage3a5_dir: {s3a5}",
                f"  stage3b1_dir: {s3b1}",
                "  stage3c_dir:",
                f"  output_dir: {output}",
                "  seed: 11",
                "  max_iter: 8",
                "  max_cv_folds: 2",
                "  min_success_nmi: 0.5",
                "  min_success_ari: 0.0",
                "  min_success_ba: 0.0",
                "  min_undercomplete_nmi_gap: 0.0",
            ]
        )
        + "\n"
    )

    result = run_stage3d4_k_stress_audit_from_config(config_path=config)

    assert result["decision"] == "stage3d4_k_stress_audit_passed"
    assert (output / "k_stress_summary.json").exists()


def test_stage3d4_rejects_impossible_success_threshold(tmp_path: Path) -> None:
    _teacher, s3a, s3a5, s3b1, _s3c = _prepare_artifacts(
        tmp_path,
        [
            ("M0", "M0"),
            ("M4", "M4"),
            ("M8", "M8"),
        ],
        run_s3c=False,
    )

    result = run_stage3d4_k_stress_audit(
        stage3a_dir=s3a,
        stage3a5_dir=s3a5,
        stage3b1_dir=s3b1,
        stage3c_dir=None,
        output_dir=tmp_path / "S3D4",
        max_iter=8,
        min_success_nmi=1.01,
        min_success_ari=0.0,
        min_success_ba=0.0,
        min_undercomplete_nmi_gap=0.0,
    )

    assert result["decision"] == "stage3d4_k_stress_audit_failed"
    assert result["acceptance_audit"]["checks"]["exact_and_overcomplete_recovery_meet_thresholds"] is False


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
