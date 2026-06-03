from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from scope_static.experiments.stage3.overcomplete_merge_prune_audit import (
    run_stage3d4b_overcomplete_merge_prune_audit_from_config,
)
from scope_static.mechanism_discovery.observability_ceiling import run_stage3a5_observability_alias_ceiling
from scope_static.mechanism_discovery.overcomplete_merge_prune_audit import (
    microcluster_merge_map,
    run_stage3d4b_overcomplete_merge_prune_audit,
)
from scope_static.mechanism_discovery.protocol_freeze import run_stage3a_dataset_protocol_freeze
from scope_static.primitives.mechanism_catalog import MECHANISM_NAMES


def test_stage3d4b_merges_overcomplete_microclusters_without_labels(tmp_path: Path) -> None:
    teacher, s3a, s3a5 = _prepare_stage3a_artifacts(tmp_path)
    d4 = _write_fake_d4_overcomplete_artifact(tmp_path, record_count=9)
    output = tmp_path / "S3D4b"

    result = run_stage3d4b_overcomplete_merge_prune_audit(
        stage3a_dir=s3a,
        stage3a5_dir=s3a5,
        stage3d4_dir=d4,
        output_dir=output,
        teacher_dir=teacher,
        max_microcluster_support=1,
        max_microcluster_fraction=0.2,
        min_postmerge_nmi=0.9,
        min_postmerge_ari=0.9,
        min_postmerge_ba=0.9,
        min_postmerge_min_recall=0.9,
    )

    assert result["decision"] == "stage3d4b_overcomplete_merge_prune_audit_passed"
    assert result["claim_decision"] in {
        "stage3d4b_postmerge_claim_gate_passed",
        "stage3d4b_postmerge_claim_gate_failed",
    }
    assert result["claim_gate_audit"]["present"] is True
    assert result["claim_boundary"]["uses_mechanism_labels_for_merge_rule"] is False
    assert result["assignment_feature_view_audit"]["source"] == "stage3a_full_visible_fallback"
    assert result["merge_prune_plan"]["uses_mechanism_labels_for_merge_rule"] is False
    assert result["leakage_audit"]["passed"] is True
    assert result["merge_map"]["active_cluster_count"] == 5
    assert result["merge_map"]["postmerge_family_count"] == 3
    assert result["merge_map"]["microcluster_count"] == 3
    assert result["merge_map"]["microcluster_merge_applied"] is True
    assert result["merge_map"]["uses_context_normalized_residual_profile_veto"] is True
    assert result["merge_map"]["residual_profile_veto_audit"]["uses_mechanism_labels"] is False

    raw = result["postmerge_metrics"]["raw_overcomplete_exact_metrics"]
    post = result["postmerge_metrics"]["postmerge_exact_metrics"]
    assert raw["min_recall_after_label_matching"] < 1.0
    assert post["normalized_mutual_info"] == 1.0
    assert post["adjusted_rand_index"] == 1.0
    assert post["balanced_accuracy_after_label_matching"] == 1.0
    assert post["min_recall_after_label_matching"] == 1.0

    for name in [
        "metrics.json",
        "merge_prune_plan.json",
        "overcomplete_cluster_summary.json",
        "merge_map.json",
        "residual_profile_veto_audit.json",
        "postmerge_metrics.json",
        "postmerge_assignments.npy",
        "leakage_audit.json",
        "acceptance_audit.json",
        "claim_gate_audit.json",
        "assignment_feature_view_audit.json",
        "assignment_feature_weighting.json",
        "summary.md",
    ]:
        assert (output / name).exists()


def test_stage3d4b_config_wrapper_runs_from_yaml(tmp_path: Path) -> None:
    teacher, s3a, s3a5 = _prepare_stage3a_artifacts(tmp_path)
    d4 = _write_fake_d4_overcomplete_artifact(tmp_path, record_count=9)
    output = tmp_path / "configured"
    config = tmp_path / "stage3d4b.yaml"
    config.write_text(
        "\n".join(
            [
                "stage3d4b_overcomplete_merge_prune_audit:",
                f"  stage3a_dir: {s3a}",
                f"  stage3a5_dir: {s3a5}",
                f"  stage3d4_dir: {d4}",
                f"  teacher_dir: {teacher}",
                f"  output_dir: {output}",
                "  max_microcluster_support: 1",
                "  max_microcluster_fraction: 0.2",
                "  min_postmerge_nmi: 0.9",
                "  min_postmerge_ari: 0.9",
                "  min_postmerge_ba: 0.9",
                "  min_postmerge_min_recall: 0.9",
            ]
        )
        + "\n"
    )

    result = run_stage3d4b_overcomplete_merge_prune_audit_from_config(config_path=config)

    assert result["decision"] == "stage3d4b_overcomplete_merge_prune_audit_passed"
    assert (output / "postmerge_metrics.json").exists()


def test_stage3d4b_rejects_when_no_microcluster_merge_applies(tmp_path: Path) -> None:
    teacher, s3a, s3a5 = _prepare_stage3a_artifacts(tmp_path)
    d4 = _write_fake_d4_overcomplete_artifact(tmp_path, record_count=9)

    result = run_stage3d4b_overcomplete_merge_prune_audit(
        stage3a_dir=s3a,
        stage3a5_dir=s3a5,
        stage3d4_dir=d4,
        output_dir=tmp_path / "S3D4b",
        teacher_dir=teacher,
        max_microcluster_support=0,
        max_microcluster_fraction=0.2,
        min_postmerge_nmi=0.9,
        min_postmerge_ari=0.9,
        min_postmerge_ba=0.9,
        min_postmerge_min_recall=0.9,
    )

    assert result["decision"] == "stage3d4b_overcomplete_merge_prune_audit_failed"
    assert result["acceptance_audit"]["checks"]["microcluster_merge_applied"] is False


def test_stage3d4b_residual_profile_veto_prevents_visible_distinct_microcluster_merge() -> None:
    summary = {
        "clusters": [
            {
                "cluster": "C000",
                "support": 1,
                "support_fraction": 0.1,
                "context_residual_profile": [0.0, 0.0],
                "context_residual_profile_l2_norm": 0.0,
            },
            {
                "cluster": "C001",
                "support": 1,
                "support_fraction": 0.1,
                "context_residual_profile": [0.02, 0.0],
                "context_residual_profile_l2_norm": 0.02,
            },
            {
                "cluster": "C002",
                "support": 1,
                "support_fraction": 0.1,
                "context_residual_profile": [3.0, 0.0],
                "context_residual_profile_l2_norm": 3.0,
            },
            {
                "cluster": "C003",
                "support": 7,
                "support_fraction": 0.7,
                "context_residual_profile": [0.0, 1.0],
                "context_residual_profile_l2_norm": 1.0,
            },
        ]
    }

    merge = microcluster_merge_map(
        summary,
        record_count=10,
        max_microcluster_support=1,
        max_microcluster_fraction=0.2,
        min_microcluster_family_count=2,
        context_residual_profile_veto_threshold=0.1,
    )

    families = merge["families"]
    merged_sources = [set(row["source_clusters"]) for row in families if row["merge_type"] == "microcluster_tail_family"]
    assert {"C000", "C001"} in merged_sources
    assert all("C002" not in sources for sources in merged_sources)
    assert merge["residual_profile_veto_audit"]["veto_applied"] is True
    assert merge["residual_profile_veto_audit"]["uses_mechanism_labels"] is False
    assert merge["cluster_to_family"]["C002"] != merge["cluster_to_family"]["C000"]


def test_stage3d4b_merges_visible_compatible_split_parent_siblings() -> None:
    summary = {
        "clusters": [
            {
                "cluster": "C000",
                "split_parent": 0,
                "support": 5,
                "support_fraction": 0.25,
                "context_residual_profile": [0.0, 0.0],
                "context_residual_profile_l2_norm": 0.0,
            },
            {
                "cluster": "C001",
                "split_parent": 0,
                "support": 5,
                "support_fraction": 0.25,
                "context_residual_profile": [0.01, 0.0],
                "context_residual_profile_l2_norm": 0.01,
            },
            {
                "cluster": "C002",
                "split_parent": 1,
                "support": 5,
                "support_fraction": 0.25,
                "context_residual_profile": [0.0, 0.0],
                "context_residual_profile_l2_norm": 0.0,
            },
            {
                "cluster": "C003",
                "split_parent": 1,
                "support": 5,
                "support_fraction": 0.25,
                "context_residual_profile": [2.0, 0.0],
                "context_residual_profile_l2_norm": 2.0,
            },
        ]
    }

    merge = microcluster_merge_map(
        summary,
        record_count=20,
        max_microcluster_support=1,
        max_microcluster_fraction=0.01,
        min_microcluster_family_count=2,
        context_residual_profile_veto_threshold=0.1,
    )

    assert merge["microcluster_merge_applied"] is False
    assert merge["split_parent_merge_applied"] is True
    assert merge["visible_merge_applied"] is True
    assert merge["cluster_to_family"]["C000"] == merge["cluster_to_family"]["C001"]
    assert merge["cluster_to_family"]["C002"] != merge["cluster_to_family"]["C003"]
    assert merge["uses_labels_for_merge_rule"] is False
    assert merge["residual_profile_veto_audit"]["veto_applied"] is True


def _prepare_stage3a_artifacts(tmp_path: Path) -> tuple[Path, Path, Path]:
    teacher = tmp_path / "S2D_PHYC1_teacher"
    teacher.mkdir()
    records = []
    for group in range(3):
        records.extend(
            [
                _record("M0", "M0", group),
                _record("M4", "M4", group),
                _record("M8", "M8", group),
            ]
        )
    (teacher / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}, indent=2) + "\n")
    s3a = tmp_path / "S3A"
    s3a5 = tmp_path / "S3A5"
    run_stage3a_dataset_protocol_freeze(teacher_dir=teacher, output_dir=s3a, shots=1000, batch_size=2)
    run_stage3a5_observability_alias_ceiling(stage3a_dir=s3a, output_dir=s3a5)
    return teacher, s3a, s3a5


def _write_fake_d4_overcomplete_artifact(tmp_path: Path, *, record_count: int) -> Path:
    d4 = tmp_path / "S3D4"
    d4.mkdir()
    responsibilities = np.zeros((int(record_count), 6), dtype=np.float64)
    # Rows are [M0, M4, M8] repeated by context. M8 is deliberately split into
    # one-row overcomplete microclusters.
    assignments = [0, 1, 2, 0, 1, 3, 0, 1, 4]
    responsibilities[np.arange(int(record_count)), np.asarray(assignments, dtype=np.int64)] = 1.0
    np.savez(d4 / "learned_assignments_by_k.npz", overcomplete_2x=responsibilities)
    metrics = {
        "schema": "scope_static_stage3d4_k_stress_audit_v1",
        "decision": "stage3d4_k_stress_audit_passed",
        "claim_boundary": {
            "uses_mechanism_labels_for_fit": False,
            "uses_mechanism_labels_for_model_selection": False,
        },
        "acceptance_audit": {"passed": True},
    }
    (d4 / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n")
    return d4


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
