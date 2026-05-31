from __future__ import annotations

import json
from pathlib import Path

import pytest

from scope_static.primitives.born_local import BORN_LOCAL_SUPPORTED_MECHANISMS
from scope_static.teacher.born_local_learner_test import run_s2e1_born_local_learner_test


def test_s2e1_learner_test_passes_full_born_local_phyc2_artifact(tmp_path: Path) -> None:
    teacher = _write_teacher_artifact(tmp_path, response_model="born_local")
    phyc2 = _write_phyc2_artifact(tmp_path, teacher_dir=teacher, class_names=list(BORN_LOCAL_SUPPORTED_MECHANISMS))

    result = run_s2e1_born_local_learner_test(
        teacher_dir=teacher,
        phyc2_dir=phyc2,
        output_dir=tmp_path / "S2E1",
    )

    assert result["schema"] == "scope_static_s2e1_born_local_learner_test_v1"
    assert result["stage"] == "S2E.1_PHYC2_Born_local_learner_test"
    assert result["data_reuse"]["reran_phyc2"] is False
    assert result["contract_passed"] is True
    assert result["decision"] == "s2e1_born_local_learner_test_passed"
    assert (tmp_path / "S2E1" / "metrics.json").exists()
    assert (tmp_path / "S2E1" / "summary.md").exists()


def test_s2e1_learner_test_rejects_existing_separability_v2_phyc2_as_born_local_pass(tmp_path: Path) -> None:
    teacher = _write_teacher_artifact(tmp_path, response_model="separability_v2")
    phyc2 = _write_phyc2_artifact(tmp_path, teacher_dir=teacher, class_names=[*BORN_LOCAL_SUPPORTED_MECHANISMS, "M11"])

    result = run_s2e1_born_local_learner_test(
        teacher_dir=teacher,
        phyc2_dir=phyc2,
        output_dir=tmp_path / "S2E1",
    )

    gates = {str(item["name"]): bool(item["passed"]) for item in result["gates"]}
    assert result["contract_passed"] is False
    assert gates["phyc2_contract_passed"] is True
    assert gates["source_artifact_matches_expected_model"] is False
    assert gates["full_s2e1_mechanism_scope"] is False
    assert result["mechanism_scope"]["unsupported_mechanisms_present"] == ["M11"]


def test_s2e1_learner_test_consumes_existing_phyc2_output_when_present(tmp_path: Path) -> None:
    root = Path("outputs/scope_static/local_observable_gpu_allM_30q_depth30_weighted_v2_slot_remap")
    teacher = root / "S2D_PHYS1_teacher"
    phyc2 = root / "PHYC2_weighted_slot_only_control"
    if not (teacher / "teacher_config.json").exists() or not (phyc2 / "metrics.json").exists():
        pytest.skip("existing PHYC2 artifact is not present in this checkout")

    result = run_s2e1_born_local_learner_test(
        teacher_dir=teacher,
        phyc2_dir=phyc2,
        output_dir=tmp_path / "S2E1_existing_phyc2",
        contract_variant="weighted",
        expected_response_model="separability_v2",
        require_full_scope=False,
    )

    assert result["data_reuse"]["reran_phyc2"] is False
    assert result["phyc2_metrics"]["contract_passed"] is True
    assert result["contract_passed"] is True
    assert result["evidence_role"] == "non_born_existing_phyc2_control"
    assert result["source_artifact"]["local_observable_response_model"] == "separability_v2"


def _write_teacher_artifact(tmp_path: Path, *, response_model: str) -> Path:
    teacher = tmp_path / "S2D_PHYS1_teacher"
    teacher.mkdir(parents=True)
    source = {"local_observable_response_model": response_model}
    (teacher / "summary.json").write_text(json.dumps(source) + "\n")
    (teacher / "teacher_config.json").write_text(json.dumps(source) + "\n")
    (teacher / "sampling_audit.json").write_text(
        json.dumps(
            {
                "local_observable_response_model": response_model,
                "pair_correlation_overlay": {
                    "enabled": False,
                    "reason": "born_local samples exact local joint POVMs directly",
                },
                "born_local_joint_sampling": {"enabled": True, "num_entries": 4},
            }
        )
        + "\n"
    )
    return teacher


def _write_phyc2_artifact(tmp_path: Path, *, teacher_dir: Path, class_names: list[str]) -> Path:
    phyc2 = tmp_path / "PHYC2"
    phyc2.mkdir(parents=True)
    support = {name: 2 for name in class_names}
    (phyc2 / "metrics.json").write_text(
        json.dumps(
            {
                "schema": "scope_static_phyc2_sampled_observation_separability_v1",
                "stage": "PHYC2_sampled_observation_separability",
                "teacher_dir": str(teacher_dir),
                "contract_variant": "balanced",
                "contract_passed": True,
                "decision": "balanced_sampled_observations_learner_separable",
                "coverage": {
                    "contract_evaluable": True,
                    "class_support": support,
                },
                "class_names": class_names,
                "balanced_accuracy": 1.0,
                "min_class_recall": 1.0,
                "prevalence_weighted_accuracy": 1.0,
                "rare_class_recall_min": 1.0,
                "real_minus_within_branch_scrambled_balanced_accuracy": 0.5,
            }
        )
        + "\n"
    )
    return phyc2
