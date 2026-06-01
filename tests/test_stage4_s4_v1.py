from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from scope_static.google.s4_bridge_surface import compare_stage4_bridge_contract, write_stage4_synthetic_google_shaped_freeze
from scope_static.mechanism_discovery.google_transfer import run_stage4_google_transfer, run_stage4_transfer_diagnostics
from scope_static.mechanism_discovery.source_ceiling import run_stage4_source_surface_survival_audit
from scope_static.mechanism_discovery.source_pretrain import run_stage4_source_pretrain
from scope_static.mechanism_discovery.stage4_artifacts import (
    load_stage4_source_evaluator_labels,
    load_stage4_visible_matrix,
    validate_stage4_source_label_separation,
)
from scope_static.mechanism_discovery.artifacts import load_stage3a_frozen_visible_features


def test_stage4_synthetic_freeze_is_stage3a_compatible_and_label_separated(tmp_path: Path) -> None:
    teacher = _write_teacher(tmp_path)
    output = tmp_path / "S4_0" / "S3A_protocol_freeze"

    result = write_stage4_synthetic_google_shaped_freeze(teacher_dir=teacher, output_dir=output, shotblock_size=4)

    matrix, feature_names, manifest = load_stage3a_frozen_visible_features(output)
    labels = load_stage4_source_evaluator_labels(output)
    separation = validate_stage4_source_label_separation(output)

    assert result["decision"] == "stage4_synthetic_bridge_freeze_passed"
    assert result["forbidden_feature_audit"]["passed"] is True
    assert result["bridge_contract_audit"]["passed"] is True
    assert matrix.shape[0] == 4
    assert len(feature_names) == matrix.shape[1]
    assert manifest["loaded_from_stage3a_artifact"] is True
    assert labels.exact_labels == ["M0", "M4", "M8", "M12"]
    assert separation["passed"] is True
    assert "exact_mechanism_label" not in "\n".join(feature_names)

    for name in [
        "visible_features.npy",
        "sampled_visible_features.npy",
        "visible_feature_schema.json",
        "visible_feature_matrix.json",
        "split_manifest.json",
        "forbidden_feature_audit.json",
        "adequacy_report.json",
        "acceptance_audit.json",
        "metrics.json",
        "summary.md",
        "source_label_manifest.json",
        "source_evaluator_labels.json",
    ]:
        assert (output / name).exists()


def test_stage4_source_survival_audit_reports_mechanism_survival(tmp_path: Path) -> None:
    source = _write_source_freeze(tmp_path)
    output = tmp_path / "S4_0_5"

    result = run_stage4_source_surface_survival_audit(stage4_source_dir=source, output_dir=output, max_iter=5)

    assert result["decision"] in {
        "bridge_surface_pass",
        "bridge_surface_quotient_only",
        "bridge_surface_projection_aliasing",
    }
    report = result["mechanism_survival_report"]
    assert report["uses_labels_for_training"] is False
    assert report["uses_labels_for_validation_selection"] is False
    assert "source_label_linear_probe_accuracy" in report
    assert "blockwise_mutual_information_with_evaluator_labels" in report
    assert (output / "mechanism_survival_report.json").exists()
    assert (output / "alias_ceiling.json").exists()
    assert (output / "projection_collapse_matrix.json").exists()


def test_stage4_source_pretrain_runs_mlp_and_attention_vq_after_survival_gate(tmp_path: Path) -> None:
    source = _write_source_freeze(tmp_path)
    ceiling = tmp_path / "S4_0_5"
    run_stage4_source_surface_survival_audit(stage4_source_dir=source, output_dir=ceiling, max_iter=5)
    output = tmp_path / "S4_1"

    result = run_stage4_source_pretrain(stage4_source_dir=source, source_ceiling_dir=ceiling, output_dir=output, k=4, code_dim=4, max_iter=5)

    assert result["decision"] == "stage4_source_pretrain_passed"
    assert result["model_selection_audit"]["validation_visible_replay_used_for_selection"] is True
    assert result["model_selection_audit"]["ari_nmi_used_for_selection"] is False
    assert "mlp_continuous" in result["models"]
    assert "attention_vq" in result["models"]
    assert result["codebook_usage"]["active_code_count"] >= 1
    assert (output / "source_codebook.npz").exists()
    assert (output / "codebook_usage.json").exists()
    assert (output / "prototype_cards.json").exists()


def test_stage4_source_pretrain_blocks_failed_surface(tmp_path: Path) -> None:
    source = _write_source_freeze(tmp_path)
    ceiling = tmp_path / "failed_ceiling"
    ceiling.mkdir()
    (ceiling / "mechanism_survival_report.json").write_text(json.dumps({"decision": "bridge_surface_fail"}) + "\n")

    try:
        run_stage4_source_pretrain(stage4_source_dir=source, source_ceiling_dir=ceiling, output_dir=tmp_path / "S4_1")
    except ValueError as exc:
        assert "blocks" in str(exc)
    else:
        raise AssertionError("expected failed source surface to block S4.1")


def test_stage4_google_transfer_and_diagnostics_write_claim_boundary(tmp_path: Path) -> None:
    source = _write_source_freeze(tmp_path)
    ceiling = tmp_path / "S4_0_5"
    run_stage4_source_surface_survival_audit(stage4_source_dir=source, output_dir=ceiling, max_iter=5)
    pretrain = tmp_path / "S4_1"
    run_stage4_source_pretrain(stage4_source_dir=source, source_ceiling_dir=ceiling, output_dir=pretrain, k=4, code_dim=4, max_iter=5)
    transfer_out = tmp_path / "S4_2"

    result = run_stage4_google_transfer(source_pretrain_dir=pretrain, google_stage3a_dir=source, output_dir=transfer_out)

    boundary = result["claim_boundary"]
    assert boundary["claims_true_google_physical_mechanism_recovery"] is False
    assert boundary["claims_google_m_label_recovery"] is False
    assert boundary["claims_visible_syndrome_response_replay"] is True
    assert result["acceptance_audit"]["checks"]["raw_target_beats_random_codebook"] is True
    assert (transfer_out / "claim_boundary.json").exists()

    diagnostics = run_stage4_transfer_diagnostics(source_pretrain_dir=pretrain, google_stage3a_dir=source, output_dir=tmp_path / "S4_3")
    assert diagnostics["does_not_replace_main_claim"] is True
    assert "strict_frozen_transfer" in diagnostics
    assert "frozen_codebook_train_adapter" in diagnostics


def test_stage4_bridge_contract_comparator_detects_mismatch(tmp_path: Path) -> None:
    source = _write_source_freeze(tmp_path)
    other = tmp_path / "other"
    other.mkdir()
    for path in source.iterdir():
        if path.is_file():
            target = other / path.name
            if path.suffix == ".npy":
                np.save(target, np.load(path))
            else:
                target.write_text(path.read_text())
    schema = json.loads((other / "visible_feature_schema.json").read_text())
    schema["features"] = list(reversed(schema["features"]))
    (other / "visible_feature_schema.json").write_text(json.dumps(schema, indent=2) + "\n")

    passed = compare_stage4_bridge_contract(synthetic_dir=source, google_dir=source)
    failed = compare_stage4_bridge_contract(synthetic_dir=source, google_dir=other)

    assert passed["passed"] is True
    assert failed["passed"] is False


def _write_source_freeze(tmp_path: Path) -> Path:
    teacher = _write_teacher(tmp_path)
    output = tmp_path / "S4_0" / "S3A_protocol_freeze"
    write_stage4_synthetic_google_shaped_freeze(teacher_dir=teacher, output_dir=output, shotblock_size=4)
    matrix, _names, _manifest = load_stage4_visible_matrix(output)
    assert matrix.shape[0] == 4
    return output


def _write_teacher(tmp_path: Path) -> Path:
    teacher = tmp_path / "teacher"
    teacher.mkdir(exist_ok=True)
    records = [
        _record("M0", [0, 1], [0]),
        _record("M4", [2, 3], [1]),
        _record("M8", [4, 5], [2]),
        _record("M12", [6, 7], [0, 2]),
    ]
    observations = np.zeros((8, 12, 3), dtype=np.uint8)
    observations[2:4, :, 0] = np.tile([0, 1], 6)
    observations[2:4, :, 1] = 1
    observations[4:6, :, :] = np.asarray([0, 1, 1], dtype=np.uint8)
    observations[6:8, :, 0] = 1
    observations[6:8, :, 2] = np.tile([1, 0], 6)
    np.savez(
        teacher / "observations.npz",
        observations=observations,
        probe_names=np.asarray([f"probe_{idx}" for idx in range(observations.shape[0])], dtype=object),
        shots=np.asarray([observations.shape[1]], dtype=np.int64),
    )
    (teacher / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}, indent=2) + "\n")
    (teacher / "teacher_config.json").write_text(json.dumps({"teacher": "tiny_stage4_fixture"}, indent=2) + "\n")
    return teacher


def _record(label: str, probes: list[int], qubits: list[int]) -> dict[str, object]:
    return {
        "oracle_label": label,
        "mechanism_id": label,
        "name": f"{label}_fixture_mechanism",
        "mechanism_set": "fixture",
        "num_qubits": 3,
        "parameters": {},
        "instruction": "id",
        "qubits": qubits,
        "circuit_id": int(probes[0]),
        "location_id": int(probes[0]),
        "probe_indices": probes,
    }
