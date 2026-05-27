from __future__ import annotations

import json
from pathlib import Path

import yaml

from scope_static.experiments import run_s2d_difficulty_expansion as mod
from scope_static.physical.teacher import build_default_oracle_mechanisms


def test_difficulty_profiles_and_mechanism_sets_are_configurable() -> None:
    specs = build_default_oracle_mechanisms({"profile": "phys9_chain", "mechanism_set": "set_B"})
    labels = [spec.mechanism_id for spec in specs]

    assert {"M0", "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8"} <= set(labels)
    assert "M9" not in labels
    assert sum(1 for spec in specs if spec.mechanism_id == "M5") == 9
    assert max(max(spec.qubits) for spec in specs if spec.qubits) < 9


def test_difficulty_set_d_has_drifted_m12_strengths() -> None:
    specs = build_default_oracle_mechanisms({"profile": "phys9_chain", "mechanism_set": "set_D"})
    m12 = [spec for spec in specs if spec.mechanism_id == "M12"]

    assert len(m12) >= 2
    assert len({float(spec.parameters["epsilon"]) for spec in m12}) == len(m12)
    assert all(spec.instruction == "rx" for spec in m12)
    assert {"M0", "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9", "M10", "M11", "M12"} <= {
        spec.mechanism_id for spec in specs
    }


def test_balanced_multicircuit_profiles_have_minimum_mechanism_instances() -> None:
    for profile in ["phys9_multicircuit_setB_balanced", "phys9_multicircuit_setC_balanced"]:
        specs = build_default_oracle_mechanisms({"profile": profile})
        counts: dict[str, int] = {}
        for spec in specs:
            counts[spec.mechanism_id] = counts.get(spec.mechanism_id, 0) + 1

        assert min(counts.values()) >= 3
        assert len({spec.circuit_id for spec in specs}) == 3
        assert all(spec.probe_indices for spec in specs)


def test_difficulty_runner_writes_aggregate_artifacts_without_oracle_selection(tmp_path: Path, monkeypatch) -> None:
    config = {
        "run": {"output_root": str(tmp_path)},
        "s2d_physical": {"shots": 32, "paper_informed_ptm_features": True},
        "s2d_difficulty_expansion": {
            "output_dir": str(tmp_path / "S2D_PHYS4_difficulty_expansion"),
            "bootstrap_replicates": 2,
            "random_baseline_trials": 2,
            "runs": [
                {"name": "phys5_setB", "profile": "phys5_chain", "mechanism_set": "set_B"},
                {"name": "phys9_setA", "profile": "phys9_chain", "mechanism_set": "set_A"},
            ],
        },
    }
    config_path = tmp_path / "s2d4.yaml"
    config_path.write_text(yaml.safe_dump(config))

    def fake_teacher(cfg, *, output_dir, preflight_dir):
        out = Path(output_dir)
        out.mkdir(parents=True)
        (out / "noise_application_audit.json").write_text(json.dumps({"records": []}))
        return {"mechanism_counts": {"M0": 1}, "num_qubits": 5 if cfg["profile"] == "phys5_chain" else 9, "output_dir": str(out)}

    def fake_sep(*, teacher_dir, output_dir, paper_informed):
        Path(output_dir).mkdir(parents=True)
        return {
            "ari": 1.0,
            "nmi": 1.0,
            "active_clusters": 3,
            "separability_gate": "identifying",
            "oracle_label_names": ["M0", "M1", "M2"],
            "feature_shape": [3, 5],
        }

    def fake_local(*, teacher_dir, separability_dir, output_dir, config):
        Path(output_dir).mkdir(parents=True)
        return {
            "num_clusters": 3,
            "s2d3_result": "physical_oracle_strong_recovery",
            "main_result": {"ari": 0.9, "nmi": 0.91, "active_clusters": 3, "cluster_masses": [1, 1, 1]},
            "physical_local_inverse_probability_v2_result": {"ari": 0.92, "nmi": 0.93},
            "direct_S_alpha_result": {"ari": 0.2, "nmi": 0.4},
            "oracle_fingerprint_upper_bound": {"ari": 1.0, "nmi": 1.0},
            "prediction_metrics": {
                "local_inverse": {"heldout_response_nll": 0.3, "response_reconstruction_mae": 0.02},
                "direct_Salpha": {"heldout_response_nll": 0.4, "response_reconstruction_mae": 0.03},
                "oracle_fingerprint": {"heldout_response_nll": 0.25, "response_reconstruction_mae": 0.01},
            },
            "nll_difficulty_audit": {
                "response_task_classification": "usable",
                "local_inverse_NLL": 0.3,
                "direct_Salpha_NLL": 0.4,
                "oracle_fingerprint_NLL": 0.25,
            },
            "bootstrap_nmi": {"min_vs_full": 0.95, "labels": [[0, 1, 2]]},
            "key_comparison": {"local_inverse_beats_direct": True},
        }

    monkeypatch.setattr(mod, "generate_physical_teacher_dataset", fake_teacher)
    monkeypatch.setattr(mod, "_run_oracle_separability_audit", fake_sep)
    monkeypatch.setattr(mod, "_run_physical_local_inverse_discovery", fake_local)

    result = mod.run_s2d_difficulty_expansion(config_path)

    assert result["stage"] == "S2D.4_physical_oracle_difficulty_expansion"
    assert result["summary"]["strong_recovery"] == 2
    out = tmp_path / "S2D_PHYS4_difficulty_expansion"
    assert (out / "comparison_table.json").exists()
    assert (out / "comparison_summary.md").exists()
    assert (out / "phys5_setB" / "metrics.json").exists()
    assert (out / "phys5_setB" / "summary.md").exists()
    assert (out / "phys5_setB" / "noise_application_audit.json").exists()
    metrics = json.loads((out / "phys5_setB" / "metrics.json").read_text())
    assert "prediction_metrics" in metrics["PHYS3"]
    assert metrics["num_qubits"] == 5
