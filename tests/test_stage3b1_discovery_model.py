from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from scope_static.experiments.stage3.discovery_model import run_stage3b1_discovery_model_from_config
from scope_static.primitives.mechanism_catalog import MECHANISM_NAMES
from scope_static.mechanism_discovery.protocol_freeze import run_stage3a_dataset_protocol_freeze
from scope_static.mechanism_discovery.observability_ceiling import run_stage3a5_observability_alias_ceiling
from scope_static.mechanism_discovery.discovery_model import (
    _context_balanced_hard_assignments,
    _fit_context_balanced_prototype_mixture,
    run_stage3b1_first_discovery_model,
)


def test_stage3b1_trains_visible_only_prototype_mixture_and_reports_quotient_metrics(tmp_path: Path) -> None:
    _teacher, s3a, s3a5 = _prepare_artifacts(
        tmp_path,
        [
            ("AliasA", "M0"),
            ("AliasB", "M0"),
            ("M4", "M4"),
        ],
    )
    output = tmp_path / "S3B1"

    result = run_stage3b1_first_discovery_model(stage3a_dir=s3a, stage3a5_dir=s3a5, output_dir=output, max_iter=15)

    assert result["decision"] == "stage3b1_first_discovery_model_completed"
    assert result["claim_boundary"]["uses_mechanism_labels_for_fit"] is False
    assert result["claim_boundary"]["uses_mechanism_labels_for_model_selection"] is False
    assert result["claim_boundary"]["trains_from_stage3a_frozen_visible_features"] is True
    assert result["claim_boundary"]["rebuilds_visible_features_from_oracle_records_for_fit"] is False
    assert result["visible_feature_matrix"]["loaded_from_stage3a_artifact"] is True
    assert result["model_selection_audit"]["validation_visible_nll_used_for_selection"] is True
    assert result["model_selection_audit"]["validation_ari_used_for_selection"] is False
    assert result["assignment_hardening_audit"]["uses_mechanism_labels_in_hardening"] is False
    assert result["assignment_hardening_audit"]["row_stochastic"] is True
    assert result["label_permutation_audit"]["cluster_label_matching_used_only_for_reporting"] is True
    assert result["learned_assignment_summary"]["row_stochastic"] is True
    assert result["learned_prototypes"]["prototype_count"] == result["learned_assignment_summary"]["selected_k"]
    assert result["acceptance_audit"]["checks"]["selected_model_chosen_by_visible_validation_objective"] is True
    assert result["acceptance_audit"]["checks"]["uses_stage3a_frozen_visible_features_for_fit"] is True

    exact = result["evaluator_only_label_metrics"]["selected_model_exact_metrics"]
    quotient = result["evaluator_only_label_metrics"]["selected_model_quotient_metrics"]
    assert quotient["normalized_mutual_info"] >= exact["normalized_mutual_info"]

    assignments = np.load(output / "learned_assignments.npy")
    assert assignments.shape[0] == 9
    assert np.allclose(assignments.sum(axis=1), 1.0)
    for name in [
        "metrics.json",
        "candidate_selection.json",
        "learned_assignments.npy",
        "learned_covariances.npy",
        "model_parameters.npz",
        "learned_assignment_summary.json",
        "learned_prototypes.json",
        "prototype_generation_metrics.json",
        "assignment_hardening_audit.json",
        "label_permutation_audit.json",
        "model_selection_audit.json",
        "evaluator_only_label_metrics.json",
        "quotient_metrics.json",
        "acceptance_audit.json",
        "feature_schema_match_audit.json",
        "visible_feature_matrix.json",
        "summary.md",
    ]:
        assert (output / name).exists()


def test_stage3b1_exact_separable_fixture_recovers_visible_mechanism_structure(tmp_path: Path) -> None:
    _teacher, s3a, s3a5 = _prepare_artifacts(
        tmp_path,
        [
            ("M0", "M0"),
            ("M4", "M4"),
            ("M8", "M8"),
        ],
    )

    result = run_stage3b1_first_discovery_model(stage3a_dir=s3a, stage3a5_dir=s3a5, output_dir=tmp_path / "S3B1", max_iter=20)

    exact = result["evaluator_only_label_metrics"]["selected_model_exact_metrics"]
    assert exact["normalized_mutual_info"] == 1.0
    assert exact["adjusted_rand_index"] == 1.0
    assert exact["balanced_accuracy_after_label_matching"] == 1.0


def test_stage3b1_fit_uses_frozen_s3a_features_not_teacher_record_rebuild(tmp_path: Path) -> None:
    teacher, s3a, s3a5 = _prepare_artifacts(
        tmp_path,
        [
            ("M0", "M0"),
            ("M4", "M4"),
        ],
    )
    _poison_teacher_mechanism_definitions(teacher)

    result = run_stage3b1_first_discovery_model(stage3a_dir=s3a, stage3a5_dir=s3a5, output_dir=tmp_path / "S3B1", max_iter=5)

    assert result["decision"] == "stage3b1_first_discovery_model_completed"
    assert result["visible_feature_matrix"]["loaded_from_stage3a_artifact"] is True


def test_stage3b1_config_wrapper_runs_from_yaml(tmp_path: Path) -> None:
    _teacher, s3a, s3a5 = _prepare_artifacts(
        tmp_path,
        [
            ("M0", "M0"),
            ("M4", "M4"),
        ],
    )
    output = tmp_path / "configured"
    config = tmp_path / "stage3b1.yaml"
    config.write_text(
        "\n".join(
            [
                "stage3b1_first_discovery_model:",
                f"  stage3a_dir: {s3a}",
                f"  stage3a5_dir: {s3a5}",
                f"  output_dir: {output}",
                "  seed: 3",
                "  max_iter: 12",
            ]
        )
        + "\n"
    )

    result = run_stage3b1_discovery_model_from_config(config_path=config)

    assert result["decision"] == "stage3b1_first_discovery_model_completed"
    assert (output / "learned_prototypes.json").exists()


def test_stage3b1_context_balanced_candidate_tracks_one_instance_per_context() -> None:
    x = np.asarray(
        [
            [0.0, 0.0],
            [5.0, 0.0],
            [0.1, 0.0],
            [5.2, 0.0],
            [-0.1, 0.0],
            [4.8, 0.0],
        ],
        dtype=np.float64,
    )
    groups = np.asarray([0, 0, 1, 1, 2, 2], dtype=np.int64)

    model = _fit_context_balanced_prototype_mixture(x, context_groups=groups, k=2, seed=0, max_iter=5)
    hard = _context_balanced_hard_assignments(x, groups, np.asarray(model["means"], dtype=np.float64))

    assert model["model_family"] == "context_balanced_visible_prototype_mixture"
    for group in sorted(set(groups.tolist())):
        local = hard[groups == group]
        assert sorted(local.tolist()) == [0, 1]


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
