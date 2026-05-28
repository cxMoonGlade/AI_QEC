from __future__ import annotations

import json
from pathlib import Path

import yaml

from scope_static.experiments import run_s2d11b_m1_gate_branch_grouped_calibration_audit as runner
from scope_static.physical.m1_gate_calibration import load_s2d11b_data, m1_false_negative_audit


def test_s2d11b_runner_reads_existing_s2d11_artifacts_and_writes_bundle(tmp_path: Path) -> None:
    source = tmp_path / "S2D.11_typed_SPAM_gate_invariant_learner"
    _write_fake_s2d11_source(source)
    output = tmp_path / "S2D.11b_M1_gate_branch_grouped_calibration_audit"
    config = {
        "run": {"output_root": str(tmp_path)},
        "s2d11b_m1_gate_branch_grouped_calibration_audit": {
            "source_root": str(source),
            "output_dir": str(output),
            "seed": 0,
            "run_two_stage_if_soft_fails": True,
        },
    }
    path = tmp_path / "s2d11b.yaml"
    path.write_text(yaml.safe_dump(config))

    result = runner.run_s2d11b_m1_gate_branch_grouped_calibration_audit(path)

    assert result["stage"] == "S2D.11b_M1_gate_branch_grouped_calibration_audit"
    assert result["source_run_dir"].endswith("phys9_multicircuit_setD_balanced")
    assert "S2D_PHYS1_teacher" not in result["source_run_dir"]
    for name in [
        "metrics.json",
        "summary.md",
        "m1_false_negative_audit.json",
        "m1_grouped_fold_breakdown.json",
        "m1_invariant_snr_audit.json",
        "m1_calibration_thresholds_by_fold.json",
        "m1_soft_rule_ablation.json",
        "m1_vs_m7_m8_m12_tradeoff.json",
        "gate_neighbor_recall_report.json",
        "error_type_taxonomy.json",
        "error_type_metrics.json",
        "mechanism_metrics_by_error_type.json",
        "calibration_variant_metrics.json",
        "leakage_guardrail_audit.json",
    ]:
        assert (output / name).exists()
    leakage = json.loads((output / "leakage_guardrail_audit.json").read_text())
    assert leakage["passed"] is True
    assert leakage["checks"]["does_not_resample_teacher"] is True
    assert "typed_linear_plus_M1_logit_boost" in result["calibration_variant_metrics"]
    taxonomy = json.loads((output / "error_type_taxonomy.json").read_text())
    assert taxonomy["mechanism_to_error_type"]["M1"] == "readout"
    assert taxonomy["mechanism_to_error_type"]["M17"] == "prep_reset"
    assert taxonomy["mechanism_to_error_type"]["M8"] == "gate"
    type_metrics = json.loads((output / "error_type_metrics.json").read_text())
    best = result["best_variant"]
    assert type_metrics["variants"][best]["overall"]["support"]["readout"] == 12


def test_m1_false_negative_audit_counts_target_classes(tmp_path: Path) -> None:
    source = tmp_path / "S2D.11_typed_SPAM_gate_invariant_learner"
    _write_fake_s2d11_source(source)
    data = load_s2d11b_data(source)
    baseline = {
        "true_labels": ["M8", "M8", "M8", "M9"],
        "predicted_labels": ["M9", "M10", "M12", "M9"],
    }

    audit = m1_false_negative_audit(data, baseline)

    assert audit["M1_true_count"] == 3
    assert audit["M1_recall"] == 0.0
    assert audit["M1_to_M6_count"] == 1
    assert audit["M1_to_M7_count"] == 1
    assert audit["M1_to_M10_count"] == 1
    assert audit["M1_to_other_count"] == 0


def test_s2d11b_fails_clearly_when_source_missing(tmp_path: Path) -> None:
    missing = tmp_path / "missing_s2d11"
    try:
        load_s2d11b_data(missing)
    except FileNotFoundError as exc:
        assert "requires existing S2D.11 run metrics" in str(exc)
    else:
        raise AssertionError("expected FileNotFoundError")


def _write_fake_s2d11_source(root: Path) -> None:
    run = root / "phys9_multicircuit_setD_balanced"
    run.mkdir(parents=True)
    records = []
    tables = {
        "gate_process_feature_table": [],
        "readout_branch_feature_table": [],
        "prep_reset_branch_feature_table": [],
    }
    location_id = 0
    labels = [f"M{idx}" for idx in range(19)]
    for circuit_id in range(3):
        for label in labels:
            branch = _branch(label)
            instruction = {"readout_branch": "measure", "prep_reset_branch": "reset"}.get(branch, "rzz" if label in {"M8", "M9", "M10", "M12"} else "id")
            qubits = [circuit_id % 8, circuit_id % 8 + 1] if instruction == "rzz" else [location_id % 9]
            records.append({"location_id": location_id, "circuit_id": circuit_id, "oracle_label": label, "qubits": qubits})
            row = {
                "location_id": location_id,
                "circuit_id": circuit_id,
                "instruction": instruction,
                "qubits": qubits,
                "features": _features(label, circuit_id),
            }
            tables[_table(branch)].append(row)
            location_id += 1
    metrics = {
        "stage": "S2D.11_typed_SPAM_gate_invariant_learner",
        "audit_labels_schema_oracle_only": {"record_refs": records},
        "gate_process_feature_table": {"records": tables["gate_process_feature_table"]},
        "readout_branch_feature_table": {"records": tables["readout_branch_feature_table"]},
        "prep_reset_branch_feature_table": {"records": tables["prep_reset_branch_feature_table"]},
        "branch_ablation_metrics": {
            "typed_gate_readout_prep_invariant_learner": {
                "overall": {
                    "balanced_accuracy": 0.8,
                    "macro_F1": 0.8,
                    "per_class_recall": {label: 1.0 for label in labels},
                }
            }
        },
        "controls": {"real_minus_within_branch_scrambled_balanced_accuracy": 0.4},
    }
    (run / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")


def _branch(label: str) -> str:
    if label in {"M1", "M2", "M3", "M16"}:
        return "readout_branch"
    if label in {"M17", "M18"}:
        return "prep_reset_branch"
    return "gate_process_branch"


def _table(branch: str) -> str:
    return {
        "gate_process_branch": "gate_process_feature_table",
        "readout_branch": "readout_branch_feature_table",
        "prep_reset_branch": "prep_reset_branch_feature_table",
    }[branch]


def _features(label: str, circuit_id: int) -> dict[str, float]:
    base = {
        "h_XX": 0.0,
        "h_YY": 0.0,
        "h_ZZ": 0.0,
        "gamma_XX": 0.0,
        "gamma_YY": 0.0,
        "gamma_ZZ": 0.0,
        "log_coherence_ratio": 0.0,
        "h_zz_axial_ratio": 0.0,
        "coherence_norm": 0.0,
        "branch_gate": 1.0,
        "branch_readout": 0.0,
        "branch_prep_reset": 0.0,
        "feature_confidence": 1.0,
    }
    if label == "M8":
        base.update({"h_ZZ": 0.08 + 0.01 * circuit_id, "log_coherence_ratio": 4.0, "h_zz_axial_ratio": 100.0, "coherence_norm": 0.08})
    elif label == "M9":
        base.update({"gamma_XX": 0.03, "gamma_YY": 0.03, "gamma_ZZ": 0.03, "log_coherence_ratio": -3.0})
    elif label == "M10":
        base.update({"h_XX": 0.05, "h_YY": 0.04, "log_coherence_ratio": 3.0, "h_zz_axial_ratio": 0.1, "coherence_norm": 0.07})
    elif label == "M12":
        base.update({"coherence_norm": 0.01})
    elif label in {"M1", "M2", "M3", "M16"}:
        base.update({"branch_gate": 0.0, "branch_readout": 1.0})
    elif label in {"M17", "M18"}:
        base.update({"branch_gate": 0.0, "branch_prep_reset": 1.0})
    return base
