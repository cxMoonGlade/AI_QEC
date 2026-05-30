from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from scope_static.experiments.run_stage3b0_baselines import run_stage3b0_baselines_from_config
from scope_static.physical.mechanism_catalog import MECHANISM_NAMES
from scope_static.physical.stage3a_protocol_freeze import run_stage3a_dataset_protocol_freeze
from scope_static.physical.stage3a5_observability_ceiling import run_stage3a5_observability_alias_ceiling
from scope_static.physical.stage3b0_baselines import run_stage3b0_nonlearned_clustering_baselines


def test_stage3b0_runs_visible_only_baselines_and_prefers_quotient_on_alias_fixture(tmp_path: Path) -> None:
    teacher, s3a, s3a5 = _prepare_artifacts(
        tmp_path,
        [
            ("AliasA", "M0"),
            ("AliasB", "M0"),
            ("M4", "M4"),
        ],
    )

    output = tmp_path / "S3B0"
    result = run_stage3b0_nonlearned_clustering_baselines(stage3a_dir=s3a, stage3a5_dir=s3a5, output_dir=output, max_iter=10)

    assert result["decision"] == "stage3b0_baselines_completed"
    assert result["claim_boundary"]["uses_mechanism_labels_for_fit"] is False
    assert result["claim_boundary"]["trains_from_stage3a_frozen_visible_features"] is True
    assert result["claim_boundary"]["rebuilds_visible_features_from_oracle_records_for_fit"] is False
    assert result["visible_feature_matrix"]["loaded_from_stage3a_artifact"] is True
    assert result["model_selection_audit"]["validation_ari_used_for_selection"] is False
    assert result["model_selection_audit"]["test_nmi_used_for_selection"] is False
    names = {row["baseline_name"] for row in result["baseline_results"]}
    assert {"global_null_control", "mean_only_control", "kmeans_visible", "gaussian_mixture_diagonal", "gaussian_mixture_full"} <= names
    primary = result["learned_assignment_summary"]
    assert primary["row_stochastic"] is True
    assert primary["compressed_claim_allowed"] is False
    assert result["acceptance_audit"]["checks"]["evaluator_metrics_reported_after_fit"] is True
    assert result["acceptance_audit"]["checks"]["uses_stage3a_frozen_visible_features_for_fit"] is True

    kmeans_fixed = _baseline(result, "kmeans_visible", "fixed_oracle_count")
    assert kmeans_fixed["quotient_label_metrics"]["normalized_mutual_info"] >= kmeans_fixed["exact_label_metrics"]["normalized_mutual_info"]

    assignments = np.load(output / "learned_assignments.npy")
    assert assignments.shape[0] == 9
    assert np.allclose(assignments.sum(axis=1), 1.0)
    for name in [
        "metrics.json",
        "baseline_results.json",
        "learned_assignments.npy",
        "baseline_assignments.npz",
        "learned_assignment_summary.json",
        "controls.json",
        "evaluator_only_label_metrics.json",
        "quotient_metrics.json",
        "model_selection_audit.json",
        "acceptance_audit.json",
        "feature_schema_match_audit.json",
        "visible_feature_matrix.json",
        "summary.md",
    ]:
        assert (output / name).exists()


def test_stage3b0_exact_separable_fixture_reaches_perfect_kmeans_metrics(tmp_path: Path) -> None:
    _teacher, s3a, s3a5 = _prepare_artifacts(
        tmp_path,
        [
            ("M0", "M0"),
            ("M4", "M4"),
            ("M8", "M8"),
        ],
    )

    result = run_stage3b0_nonlearned_clustering_baselines(stage3a_dir=s3a, stage3a5_dir=s3a5, output_dir=tmp_path / "S3B0", max_iter=10)

    kmeans_fixed = _baseline(result, "kmeans_visible", "fixed_oracle_count")
    assert kmeans_fixed["exact_label_metrics"]["normalized_mutual_info"] == 1.0
    assert kmeans_fixed["exact_label_metrics"]["adjusted_rand_index"] == 1.0
    assert kmeans_fixed["exact_label_metrics"]["balanced_accuracy_after_label_matching"] == 1.0


def test_stage3b0_fit_uses_frozen_s3a_features_not_teacher_record_rebuild(tmp_path: Path) -> None:
    teacher, s3a, s3a5 = _prepare_artifacts(
        tmp_path,
        [
            ("M0", "M0"),
            ("M4", "M4"),
        ],
    )
    _poison_teacher_mechanism_definitions(teacher)

    result = run_stage3b0_nonlearned_clustering_baselines(stage3a_dir=s3a, stage3a5_dir=s3a5, output_dir=tmp_path / "S3B0", max_iter=5)

    assert result["decision"] == "stage3b0_baselines_completed"
    assert result["visible_feature_matrix"]["loaded_from_stage3a_artifact"] is True


def test_stage3b0_config_wrapper_runs_from_yaml(tmp_path: Path) -> None:
    _teacher, s3a, s3a5 = _prepare_artifacts(
        tmp_path,
        [
            ("M0", "M0"),
            ("M4", "M4"),
        ],
    )
    output = tmp_path / "configured"
    config = tmp_path / "stage3b0.yaml"
    config.write_text(
        "\n".join(
            [
                "stage3b0_nonlearned_clustering_baselines:",
                f"  stage3a_dir: {s3a}",
                f"  stage3a5_dir: {s3a5}",
                f"  output_dir: {output}",
                "  seed: 3",
                "  max_iter: 10",
            ]
        )
        + "\n"
    )

    result = run_stage3b0_baselines_from_config(config_path=config)

    assert result["decision"] == "stage3b0_baselines_completed"
    assert (output / "baseline_results.json").exists()


def _prepare_artifacts(tmp_path: Path, label_specs: list[tuple[str, str]]) -> tuple[Path, Path, Path]:
    teacher = tmp_path / "S2D_PHYC1_teacher"
    teacher.mkdir()
    records = []
    for group in range(3):
        for label, mechanism_id in label_specs:
            records.append(_record(label, mechanism_id, group))
    (teacher / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}, indent=2) + "\n")
    s3a = tmp_path / "S3A"
    s3a5 = tmp_path / "S3A5"
    run_stage3a_dataset_protocol_freeze(teacher_dir=teacher, output_dir=s3a, shots=1000, batch_size=2)
    run_stage3a5_observability_alias_ceiling(stage3a_dir=s3a, output_dir=s3a5)
    return teacher, s3a, s3a5


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


def _poison_teacher_mechanism_definitions(teacher: Path) -> None:
    path = teacher / "oracle_mechanisms.json"
    data = json.loads(path.read_text())
    for record in data["mechanisms"]:
        record["mechanism_id"] = "NOT_A_REAL_MECHANISM"
        record["name"] = "poisoned mechanism definition"
        record["num_qubits"] = 999
        record["instruction"] = "not_a_gate"
        record["parameters"] = {"poisoned": True}
    path.write_text(json.dumps(data, indent=2) + "\n")


def _baseline(result: dict[str, object], baseline_name: str, k_mode: str) -> dict[str, object]:
    for row in result["baseline_results"]:
        if row["baseline_name"] == baseline_name and row["k_mode"] == k_mode:
            return row
    raise AssertionError(f"missing baseline {baseline_name}/{k_mode}")
