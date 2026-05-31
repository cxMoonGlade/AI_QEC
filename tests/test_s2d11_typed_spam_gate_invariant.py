from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import yaml

from scope_static.experiments.qec_noise_catalog import s2d11_typed_spam_gate_invariant_learner as runner
from scope_static.mechanism_observability import INVARIANT_FEATURES
from scope_static.mechanism_observability import GENERATOR_CORE
from scope_static.mechanism_observability import (
    build_typed_spam_gate_features,
    branch_budget_audit,
    classification_metrics,
    m5_overfragmentation_report,
    visible_branch,
)


def test_branch_assignment_uses_visible_instruction_only() -> None:
    assert visible_branch({"instruction": "measure", "oracle_label": "M1"}) == "readout_branch"
    assert visible_branch({"instruction": "reset", "oracle_label": "M17"}) == "prep_reset_branch"
    assert visible_branch({"instruction": "rzz", "oracle_label": "M8"}) == "gate_process_branch"


def test_branch_budget_audit_declares_visible_run_config_source() -> None:
    audit = branch_budget_audit(["M0", "M1", "M17"], ["gate_process_branch", "readout_branch", "prep_reset_branch"])

    assert audit["budget_source"] == "visible_run_config"
    assert audit["row_oracle_labels_used"] is False
    assert audit["mechanism_id_used_per_row"] is False
    assert audit["branch_assignment_source"] == "visible_instruction_type"
    assert audit["budgets"]["readout_branch"] == 1
    assert audit["budgets"]["prep_reset_branch"] == 1


def test_m5_split_count_uses_tau_threshold() -> None:
    no_split = m5_overfragmentation_report(["M1"] * 10, ["M1"] * 10, ["M1", "M8"], tau=0.10)
    split = m5_overfragmentation_report(["M1"] * 10, ["M1"] * 9 + ["M8"], ["M1", "M8"], tau=0.10)

    assert no_split["readout_split_count"] == 1
    assert no_split["readout_split_fixed"] is True
    assert split["readout_split_count"] == 2
    assert split["readout_vs_gate_confusion_rate"] == 0.1


def test_classification_metrics_report_evaluator_only_partition_scores() -> None:
    metrics = classification_metrics(["M0", "M1", "M2"], ["M0", "M1", "M2"], ["M0", "M1", "M2"])

    assert metrics["adjusted_rand_index"] == 1.0
    assert metrics["normalized_mutual_info"] == 1.0


def test_typed_features_are_oracle_label_permutation_invariant_and_include_confidence_fields() -> None:
    records = _fake_records(["M8", "M1", "M17"])
    observations, probe_names = _fake_observations(num_qubits=9)
    local_record = _fake_local_record(records)

    first = build_typed_spam_gate_features(records, observations, probe_names, local_record, enabled_mechanisms=["M8", "M1", "M17"])
    permuted = [dict(record, oracle_label=f"X{idx}") for idx, record in enumerate(records)]
    second = build_typed_spam_gate_features(permuted, observations, probe_names, local_record, enabled_mechanisms=["M8", "M1", "M17"])

    np.testing.assert_allclose(first.feature_spaces["typed_gate_readout_prep_invariant_learner"], second.feature_spaces["typed_gate_readout_prep_invariant_learner"])
    assert first.leakage_guardrail_audit["passed"] is True
    feature_names = first.feature_names["typed_gate_readout_prep_invariant_learner"]
    assert {"feature_confidence", "feature_snr", "fit_residual_or_reconstruction_error", "low_confidence_flag"} <= set(feature_names)
    assert any(name.startswith("sampled_tomo_left_mean_") for name in feature_names)
    assert any(name.startswith("sampled_tomo_pair_centered_corr_") for name in feature_names)
    assert "shot_ptm_delta_XX_YY" in feature_names
    assert "per_probe_sampled_response_vector" in first.typed_branch_feature_manifest["visible_inputs"]
    readout_row = first.readout_branch_feature_table["records"][0]
    assert "feature_confidence" in readout_row
    assert "feature_snr" in readout_row
    assert "fit_residual_or_reconstruction_error" in readout_row
    assert "low_confidence_flag" in readout_row


def test_runner_writes_full_audit_bundle_with_fake_setD(tmp_path: Path, monkeypatch) -> None:
    records = _fake_records([f"M{idx}" for idx in range(35)])
    observations, probe_names = _fake_observations(num_qubits=9)
    local_record = _fake_local_record(records)

    def fake_teacher(config, output_dir, preflight_dir):
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        preflight = Path(preflight_dir)
        preflight.mkdir(parents=True, exist_ok=True)
        (output / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}, indent=2) + "\n")
        np.savez(output / "observations.npz", observations=observations, probe_names=np.asarray(probe_names, dtype="<U64"))
        counts = {}
        for record in records:
            counts[str(record["oracle_label"])] = counts.get(str(record["oracle_label"]), 0) + 1
        return {"num_qubits": 9, "mechanism_counts": counts, "num_circuit_batches": 3, "balanced_min_instances_per_mechanism": 3, "num_probes": len(probe_names)}

    def fake_local(*_args, **_kwargs):
        return SimpleNamespace(
            generator_coordinate_estimates=local_record["generator_coordinate_estimates"],
            ptm_block_reconstruction=local_record["ptm_block_reconstruction"],
            response_jacobian_json={"matrix": np.eye(2).tolist()},
        )

    monkeypatch.setattr(runner, "generate_controlled_catalog_teacher_dataset", fake_teacher)
    monkeypatch.setattr(runner, "build_local_pauli_lindblad_observability", fake_local)

    output = tmp_path / "S2D.11_typed_SPAM_gate_invariant_learner"
    config = {
        "run": {"output_root": str(tmp_path)},
        "s2d_physical": {"require_gpu": True, "shots": 8},
        "s2d11_typed_spam_gate_invariant_learner": {
            "output_dir": str(output),
            "run_secondary_allM_if_primary_passes": False,
            "runs": [
                {"name": "phys9_multicircuit_setD_balanced", "profile": "phys9_multicircuit_setD_balanced", "mechanism_set": "set_D"}
            ],
        },
    }
    path = tmp_path / "s2d11.yaml"
    path.write_text(yaml.safe_dump(config))

    result = runner.run_s2d11_typed_spam_gate_invariant_learner(path)

    assert result["stage"] == "S2D.11_typed_SPAM_gate_invariant_learner"
    assert result["preferred_precise_name"] == "S2D.11_typed_gate_readout_prep_invariant_learner"
    for name in [
        "metrics.json",
        "summary.md",
        "typed_branch_feature_manifest.json",
        "branch_budget_audit.json",
        "grouped_fold_coverage_audit.json",
        "typed_metric_head_report.json",
        "m5_overfragmentation_report.json",
        "m11_prep_observability_preflight.json",
        "prep_reconstruction_assumption_audit.json",
        "grouped_fold_predictions.csv",
    ]:
        assert (output / name).exists()
    metrics = json.loads((output / "metrics.json").read_text())
    record = metrics["records"][0]
    assert "supervised_grouped_ceiling" in record
    assert "typed_heads" in record
    assert "branch_ablations" in record
    assert "controls" in record
    assert "oracle_upper_bound" in record
    assert record["branch_budget_audit"]["budget_source"] == "visible_run_config"


def _fake_records(labels: list[str]) -> list[dict[str, object]]:
    records = []
    location_id = 0
    for circuit_id in range(3):
        for label in labels:
            instruction = _instruction_for_label(label)
            qubits = [int((location_id + circuit_id) % 9)]
            if instruction == "rzz":
                left = int((location_id + circuit_id) % 8)
                qubits = [left, left + 1]
            records.append(
                {
                    "location_id": location_id,
                    "oracle_label": label,
                    "instruction": instruction,
                    "qubits": qubits,
                    "circuit_id": circuit_id,
                    "probe_indices": list(range(6)),
                }
            )
            location_id += 1
    return records


def _fake_local_record(records: list[dict[str, object]]) -> dict[str, object]:
    coordinate_names = [*GENERATOR_CORE, "nonunital_norm_proxy", "delta_norm", "logm_delta_norm"]
    estimates = []
    ptm_records = []
    for record in records:
        features = _features_for_label(str(record["oracle_label"]))
        estimates.append(
            {
                "location_id": int(record["location_id"]),
                "oracle_label_evaluator_only": str(record["oracle_label"]),
                "circuit_id": int(record["circuit_id"]),
                "features": {name: float(features.get(name, 0.0)) for name in coordinate_names},
                "scrambled_features": {name: 0.0 for name in coordinate_names},
            }
        )
        ptm_records.append(
            {
                "location_id": int(record["location_id"]),
                "R_error": np.eye(16).tolist(),
                "R_est": np.eye(16).tolist(),
            }
        )
    return {
        "generator_coordinate_estimates": {"coordinate_names": coordinate_names, "records": estimates},
        "ptm_block_reconstruction": {"records": ptm_records},
    }


def _fake_observations(num_qubits: int) -> tuple[np.ndarray, list[str]]:
    probe_names = [
        "rzz_tomo_pZpZp_mZZ_even",
        "rzz_tomo_pZmZm_mZZ_even",
        "rzz_tomo_pXpXp_mXX_even",
        "rzz_tomo_pYpYp_mYY_even",
        "x_measure",
        "y_measure",
    ]
    observations = np.zeros((len(probe_names), 8, num_qubits), dtype=np.float64)
    for probe_idx in range(len(probe_names)):
        for q in range(num_qubits):
            value = 1.0 if (probe_idx + q) % 3 == 0 else 0.0
            observations[probe_idx, :, q] = value
    observations[0, :, :] = 1.0
    observations[1, :, :] = 0.0
    return observations, probe_names


def _instruction_for_label(label: str) -> str:
    return {
        "M8": "rzz",
        "M9": "rzz",
        "M10": "rzz",
        "M12": "rzz",
        "M21": "rzz",
        "M22": "rzz",
        "M23": "rzz",
        "M28": "rzz",
        "M29": "rzz",
        "M30": "rzz",
        "M31": "rzz",
        "M32": "rzz",
        "M33": "rzz",
        "M6": "rx",
        "M7": "rz",
        "M13": "rx",
        "M14": "rx",
        "M20": "ry",
        "M1": "measure",
        "M2": "measure",
        "M3": "measure",
        "M16": "measure",
        "M17": "reset",
        "M18": "reset",
    }.get(label, "id")


def _features_for_label(label: str) -> dict[str, float]:
    values = {name: 0.0 for name in [*GENERATOR_CORE, "nonunital_norm_proxy", "delta_norm", "logm_delta_norm", *INVARIANT_FEATURES]}
    if label == "M8":
        values["h_ZZ"] = 0.12
    elif label == "M9":
        values["gamma_XX"] = values["gamma_YY"] = values["gamma_ZZ"] = 0.05
    elif label == "M10":
        values["h_XX"] = 0.09
        values["h_YY"] = 0.06
    elif label in {"M4", "M12"}:
        values["relaxation_pair"] = 0.08
        values["nonunital_norm_proxy"] = 0.08
    elif label == "M6":
        values["h_XX"] = 0.04
    elif label in {"M7", "M13", "M14"}:
        values["h_ZZ"] = 0.04
    elif label in {"M5", "M15"}:
        values["h_XX"] = 0.02
        values["gamma_ZZ"] = 0.04
    elif label == "M11":
        values["h_ZZ"] = 0.02
    elif label == "M19":
        values["gamma_XX"] = 0.006
    values["delta_norm"] = max(0.02, sum(abs(values.get(name, 0.0)) for name in GENERATOR_CORE))
    return values
