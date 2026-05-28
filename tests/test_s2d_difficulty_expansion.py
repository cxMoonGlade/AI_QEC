from __future__ import annotations

import json
from pathlib import Path

import yaml

from scope_static.experiments import run_s2d_difficulty_expansion as mod
from scope_static.physical.teacher import build_default_oracle_mechanisms, build_probe_basis_manifest, build_probe_circuits


def test_difficulty_profiles_and_mechanism_sets_are_configurable() -> None:
    specs = build_default_oracle_mechanisms({"profile": "phys9_chain", "mechanism_set": "set_B"})
    labels = [spec.mechanism_id for spec in specs]

    assert {f"M{idx}" for idx in range(15)} <= set(labels)
    assert "M15" not in labels
    assert sum(1 for spec in specs if spec.mechanism_id in {"M1", "M2", "M3", "M16"}) == 3
    assert max(max(spec.qubits) for spec in specs if spec.qubits) < 9


def test_difficulty_set_d_has_drifted_m13_strengths() -> None:
    specs = build_default_oracle_mechanisms({"mechanism_set": "set_D", "num_qubits": 40})
    m13 = [spec for spec in specs if spec.mechanism_id == "M13"]

    assert len(m13) >= 2
    assert len({float(spec.parameters["epsilon"]) for spec in m13}) == len(m13)
    assert all(spec.instruction == "rx" for spec in m13)
    assert {f"M{idx}" for idx in range(35)} <= {
        spec.mechanism_id for spec in specs
    }


def test_balanced_multicircuit_profiles_have_minimum_mechanism_instances() -> None:
    for profile in ["phys9_multicircuit_setB_balanced", "phys9_multicircuit_setC_balanced", "phys15_multicircuit_allM_balanced"]:
        specs = build_default_oracle_mechanisms({"profile": profile})
        counts: dict[str, int] = {}
        for spec in specs:
            counts[spec.mechanism_id] = counts.get(spec.mechanism_id, 0) + 1

        assert min(counts.values()) >= 3
        assert len({spec.circuit_id for spec in specs}) == 3
        assert all(spec.probe_indices for spec in specs)
    assert {f"M{idx}" for idx in range(35)} == set(counts)


def test_circuit_depth_is_visible_probe_metadata() -> None:
    manifest = build_probe_basis_manifest(["z_basis"], num_qubits=3, circuit_depth=50)
    circuits, _ = build_probe_circuits({"profile": "phys9_chain", "probe_set": "base", "depth": 3})
    ops = circuits[0].count_ops()

    assert manifest["circuit_depth"] == 50
    assert manifest["probe_records"][0]["circuit_depth"] == 50
    assert ops["rzz"] == 3 * (9 - 1)


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

    def fake_stack(cfg, *, output_dir, bootstrap_replicates, random_baseline_trials, run_local_inverse):
        root = Path(output_dir)
        teacher_dir = root / "S2D_PHYS1_teacher"
        sep_dir = root / "S2D_PHYS2_oracle_separability"
        local_dir = root / "S2D_PHYS3_local_inverse"
        teacher = fake_teacher(cfg, output_dir=teacher_dir, preflight_dir=root / "S2D_PHYS0_preflight")
        sep = fake_sep(teacher_dir=teacher_dir, output_dir=sep_dir, paper_informed=True)
        local = fake_local(teacher_dir=teacher_dir, separability_dir=sep_dir, output_dir=local_dir, config=cfg)
        return {
            "output_dir": str(root),
            "paths": {"teacher_dir": str(teacher_dir), "separability_dir": str(sep_dir), "local_inverse_dir": str(local_dir)},
            "teacher": {"mechanism_counts": teacher["mechanism_counts"], "num_qubits": teacher["num_qubits"]},
            "metrics": {
                "teacher_self": {
                    "ari": sep["ari"],
                    "nmi": sep["nmi"],
                    "active_clusters": sep["active_clusters"],
                    "separability_gate": sep["separability_gate"],
                    "oracle_label_names": sep["oracle_label_names"],
                    "feature_shape": sep["feature_shape"],
                },
                "learner": {
                    "s2d3_result": local["s2d3_result"],
                    "main_result": local["main_result"],
                    "physical_local_inverse_probability_v2_result": local["physical_local_inverse_probability_v2_result"],
                    "direct_S_alpha_result": local["direct_S_alpha_result"],
                    "oracle_fingerprint_upper_bound": local["oracle_fingerprint_upper_bound"],
                    "prediction_metrics": local["prediction_metrics"],
                    "nll_difficulty_audit": local["nll_difficulty_audit"],
                    "bootstrap_nmi": local["bootstrap_nmi"],
                    "key_comparison": local["key_comparison"],
                },
            },
            "verdicts": {"overall_diagnosis": "strong_recovery"},
            "timings_seconds": {"total": 0.0},
            "stage_results": {"teacher": teacher, "teacher_self": sep, "learner": local},
        }

    monkeypatch.setattr(mod, "run_physical_oracle_stack", fake_stack)

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
