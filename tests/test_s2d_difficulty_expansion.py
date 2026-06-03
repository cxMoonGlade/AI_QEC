from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import yaml

from scope_static.experiments.qec_noise_catalog import s2d_difficulty_expansion as mod
from scope_static.primitives.overlay_contract import overlay_contract_audit
from scope_static.primitives.probe_catalog import build_default_oracle_mechanisms, build_probe_basis_manifest, build_probe_circuits


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
    m11 = [spec for spec in specs if spec.mechanism_id == "M11"]

    assert len(m13) >= 2
    assert len({float(spec.parameters["epsilon"]) for spec in m13}) == len(m13)
    assert all(spec.instruction == "rx" for spec in m13)
    assert m11
    assert all(bool(spec.parameters["spectator_overlay_present"]) for spec in m11)
    assert all(spec.parameters["base_mechanism"] for spec in m11)
    assert all(spec.parameters["victim_relative_location"] for spec in m11)
    assert all(spec.parameters["aggressor_relative_location"] for spec in m11)
    assert all(spec.parameters["coupling_axis"] for spec in m11)
    assert all(spec.parameters["timing_context"] for spec in m11)
    assert all(spec.parameters["claims_standalone_flat_mechanism"] is False for spec in m11)
    assert {f"M{idx}" for idx in range(35)} <= {
        spec.mechanism_id for spec in specs
    }
    for spec in specs:
        audit = spec.audit_dict()
        assert audit["legacy_catalog_id"] == spec.mechanism_id
        assert audit["mechanism_id"] == spec.mechanism_id
        assert str(audit["public_label"]).startswith("F" if audit["label_namespace"] == "flat" else "M")
        assert audit["label_namespace"] in {"flat", "non_flat"}


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


def test_balanced_strength_variants_cover_every_mechanism() -> None:
    specs = build_default_oracle_mechanisms(
        {
            "num_qubits": 20,
            "mechanism_set": "allM",
            "balanced_min_instances_per_mechanism": 20,
            "multicircuit_teacher_batch": True,
            "balanced_strength_variants": True,
            "balanced_strength_min_scale": 0.65,
            "balanced_strength_max_scale": 1.35,
        }
    )

    by_mechanism: dict[str, list[float]] = {}
    for spec in specs:
        by_mechanism.setdefault(spec.mechanism_id, []).append(_primary_strength(spec.parameters))

    assert set(by_mechanism) == {f"M{idx}" for idx in range(35)}
    for mechanism_id, values in by_mechanism.items():
        assert len(values) == 20, mechanism_id
        assert len({round(value, 12) for value in values}) == 20, mechanism_id


def test_balanced_teacher_serializes_m11_overlay_payload_in_records() -> None:
    specs = build_default_oracle_mechanisms(
        {
            "num_qubits": 20,
            "mechanism_set": "allM",
            "balanced_min_instances_per_mechanism": 4,
            "multicircuit_teacher_batch": True,
            "balanced_strength_variants": True,
        }
    )
    records = [{"location_id": idx, **spec.audit_dict(), "oracle_label": spec.mechanism_id} for idx, spec in enumerate(specs)]
    m11 = [record for record in records if record["mechanism_id"] == "M11"]

    assert len(m11) == 4
    audit = overlay_contract_audit(m11)
    assert audit["passed"] is True
    assert audit["num_overlay_records"] == 4
    assert audit["num_overlay_records_missing_payload"] == 0
    for record in m11:
        assert record["spectator_overlay_present"] is True
        assert record["contract_role"] == "overlay_family"
        assert record["overlay_family"] == "spectator_crosstalk"
        assert record["public_effect_family"] == "spectator_overlay"
        assert str(record["public_overlay_class"]).endswith("_overlay")
        assert str(record["nonflat_public_label"]).startswith("spectator_overlay_")
        assert record["base_mechanism"] in {"M8", "M7", "M1", "M17"}
        assert record["victim_relative_location"] in {"edge", "qubit_id", "detector"}
        assert record["aggressor_relative_location"] in {"adjacent_gate", "previous_cycle_edge", "same_cycle_qubit", "shot_block"}
        assert record["coupling_axis"] in {"ZZ", "RZ", "readout_bias", "reset_bias"}
        assert record["timing_context"] in {"same_cycle", "prev_cycle", "shot_block_drift"}
        assert float(record["spectator_strength"]) > 0.0
        assert record["spectator_overlay"]["present"] is True
        assert record["spectator_overlay"]["base_mechanism"] == record["base_mechanism"]


def test_balanced_strength_variants_can_decouple_context_and_strength() -> None:
    specs = build_default_oracle_mechanisms(
        {
            "num_qubits": 20,
            "mechanism_set": "allM",
            "balanced_min_instances_per_mechanism": 20,
            "multicircuit_teacher_batch": True,
            "balanced_strength_variants": True,
            "balanced_strength_variant_strategy": "decorrelated_latin",
            "balanced_strength_min_scale": 0.65,
            "balanced_strength_max_scale": 1.35,
        }
    )

    by_mechanism: dict[str, list[tuple[int, int, float]]] = {}
    for spec in specs:
        by_mechanism.setdefault(spec.mechanism_id, []).append(
            (int(spec.circuit_id or 0), int(spec.qubits[0] if spec.qubits else 0), _primary_strength(spec.parameters))
        )

    for mechanism_id, rows in by_mechanism.items():
        strengths = [row[2] for row in rows]
        assert len(rows) == 20, mechanism_id
        assert len({round(value, 12) for value in strengths}) == 20, mechanism_id

    for mechanism_id in ("M6", "M13", "M18"):
        rows = sorted(by_mechanism[mechanism_id])
        circuit_ids = np.asarray([row[0] for row in rows], dtype=float)
        relative_locations = np.asarray([row[1] for row in rows], dtype=float)
        strengths = np.asarray([row[2] for row in rows], dtype=float)
        assert abs(float(np.corrcoef(circuit_ids, strengths)[0, 1])) < 0.1, mechanism_id
        assert abs(float(np.corrcoef(relative_locations, strengths)[0, 1])) < 0.1, mechanism_id


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
            "s2d3_result": "catalog_validation_strong_recovery",
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

    def fake_pipeline(cfg, *, output_dir, bootstrap_replicates, random_baseline_trials, run_local_inverse):
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

    monkeypatch.setattr(mod, "run_catalog_pipeline", fake_pipeline)

    result = mod.run_s2d_difficulty_expansion(config_path)

    assert result["stage"] == "S2D.4_catalog_validation_difficulty_expansion"
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


def _primary_strength(parameters: dict[str, object]) -> float:
    for key in ("epsilon", "p", "p_z", "gamma", "gamma_up", "eta", "strength", "epsilon_x", "epsilon_y", "p_x"):
        if key in parameters:
            return float(parameters[key])
    raise AssertionError(f"record has no primary strength parameter: {parameters}")
