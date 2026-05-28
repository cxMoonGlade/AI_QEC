from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import yaml

from scope_static.experiments import run_s2d8a_rzz_depth_sweep as runner
from scope_static.physical.rzz_depth_sweep import build_rzz_depth_sweep_features, evaluate_rzz_depth_sweep_methods
from scope_static.physical.teacher import build_default_oracle_mechanisms, build_probe_basis_manifest, build_probe_circuits


DEPTH_PROBES = ["z_basis", "x_measure", "y_measure", "rzz_depth_1", "rzz_depth_2", "rzz_depth_4", "rzz_depth_8"]


def test_depth_probe_naming_and_rzz_repetition_count() -> None:
    circuits, names = build_probe_circuits({"profile": "phys9_chain", "probe_set": "rzz_depth_sweep"})

    assert names == DEPTH_PROBES
    assert [int(circuit.count_ops().get("rzz", 0)) for circuit in circuits] == [8, 8, 8, 8, 16, 32, 64]
    manifest = build_probe_basis_manifest(names, num_qubits=9)
    assert [record["rzz_depth"] for record in manifest["probe_records"]] == [1, 1, 1, 1, 2, 4, 8]


def test_depth_response_feature_extraction_from_shot_bits() -> None:
    records = [_record("M8", [0, 1])]
    observations = _known_depth_observations()
    bundle = build_rzz_depth_sweep_features(records, observations, DEPTH_PROBES, num_clusters=1)

    names = bundle.feature_names["rzz_depth_features"]
    row = bundle.feature_spaces["rzz_depth_features"][0]

    assert row[names.index("depth_1_zz_mean")] == 1.0
    assert row[names.index("depth_2_zz_mean")] == 0.0
    assert row[names.index("depth_4_zz_mean")] == -1.0
    assert row[names.index("depth_8_zz_mean")] == 0.0
    assert np.all(np.isfinite(row))


def test_scrambled_depth_control_preserves_shape() -> None:
    records = [_record("M8", [0, 1])]
    bundle = build_rzz_depth_sweep_features(records, _known_depth_observations(), DEPTH_PROBES, num_clusters=1)

    real = bundle.feature_spaces["rzz_depth_features"]
    scrambled = bundle.feature_spaces["scrambled_depth_control"]
    assert real.shape == scrambled.shape
    assert not np.allclose(real, scrambled)


def test_depth_feature_provenance_is_learner_visible_and_oracle_free() -> None:
    bundle = build_rzz_depth_sweep_features([_record("M8", [0, 1])], _known_depth_observations(), DEPTH_PROBES, num_clusters=1)
    manifest = bundle.feature_provenance_manifest

    assert "exact_ptm_entries" in manifest["forbidden_in_phys3"]
    for features in manifest["feature_blocks"].values():
        for spec in features:
            assert spec["uses_oracle_label"] is False
            assert spec["uses_exact_teacher_channel"] is False
            assert spec["uses_exact_ptm"] is False
            assert "shot_bits" in spec["visible_inputs"]
            assert "probe_depth" in spec["visible_inputs"]


def test_depth_evaluation_reports_bootstrap_and_rzz_metrics() -> None:
    records = [_record("M8", [0, 1]), _record("M9", [0, 1]), _record("M10", [0, 1]), _record("M12", [0, 1])]
    observations = np.concatenate([_known_depth_observations(), _known_depth_observations()], axis=1)
    label_names = sorted({str(record["oracle_label"]) for record in records})
    index = {name: idx for idx, name in enumerate(label_names)}
    hidden = np.asarray([index[str(record["oracle_label"])] for record in records])

    result = evaluate_rzz_depth_sweep_methods(
        records,
        observations,
        DEPTH_PROBES,
        hidden_labels_np(hidden),
        label_names,
        bootstrap_replicates=2,
    )

    depth = next(row for row in result["methods"] if row["method"] == "rzz_depth_features")
    assert depth["bootstrap_nmi"]["replicates"] == 2
    assert "rzz_depth_features" in result["rzz_family_metrics"]["methods"]
    assert "M8_M9_merge_count" in result["rzz_family_metrics"]["methods"]["rzz_depth_features"]


def test_s2d8a_runner_writes_required_artifacts_with_fakes(tmp_path: Path, monkeypatch) -> None:
    config = {
        "run": {"output_root": str(tmp_path)},
        "s2d_physical": {"shots": 16, "paper_informed_ptm_features": True},
        "s2d8a_rzz_depth_sweep": {
            "output_dir": str(tmp_path / "S2D.8_RZZ_dynamical_probe_design"),
            "bootstrap_replicates": 1,
            "random_baseline_trials": 1,
            "runs": [{"name": "phys9_setA", "profile": "phys9_chain", "mechanism_set": "set_A"}],
        },
    }
    config_path = tmp_path / "s2d8a.yaml"
    config_path.write_text(yaml.safe_dump(config))

    def fake_teacher(cfg, *, output_dir, preflight_dir):
        out = Path(output_dir)
        out.mkdir(parents=True)
        specs = build_default_oracle_mechanisms(cfg)
        records = [{"location_id": idx, **spec.audit_dict(), "oracle_label": spec.mechanism_id} for idx, spec in enumerate(specs)]
        if cfg.get("probe_set") == "rzz_depth_sweep":
            probe_names = DEPTH_PROBES
        elif cfg.get("probe_set") == "rzz_active_minimal":
            probe_names = ["z_basis", "x_measure", "y_measure", "alt_xz", "alt_zx", "alt_yz", "alt_zy", "alt_xy", "alt_yx"]
        else:
            probe_names = ["z_basis", "x_measure", "y_measure"]
        np.savez_compressed(
            out / "observations.npz",
            observations=_observations(num_probes=len(probe_names), shots=16, num_qubits=9),
            probe_names=np.asarray(probe_names),
            shots=np.asarray([16], dtype=np.int64),
        )
        (out / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}, indent=2) + "\n")
        (out / "noise_application_audit.json").write_text(json.dumps({"records": []}))
        (out / "active_probe_manifest.json").write_text(json.dumps(build_probe_basis_manifest(probe_names, num_qubits=9)))
        return {"mechanism_counts": {"M8": 1}, "num_qubits": 9, "output_dir": str(out)}

    def fake_sep(*, teacher_dir, output_dir, paper_informed):
        records = json.loads((Path(teacher_dir) / "oracle_mechanisms.json").read_text())["mechanisms"]
        names = sorted({record["oracle_label"] for record in records})
        Path(output_dir).mkdir(parents=True)
        return {
            "ari": 1.0,
            "nmi": 1.0,
            "active_clusters": len(names),
            "separability_gate": "identifying",
            "oracle_label_names": names,
            "feature_shape": [len(records), 10],
            "fingerprint_families": {"ptm": {"oracle_only": True}},
        }

    def fake_local(*, teacher_dir, separability_dir, output_dir, config):
        records = json.loads((Path(teacher_dir) / "oracle_mechanisms.json").read_text())["mechanisms"]
        names = sorted({record["oracle_label"] for record in records})
        index = {name: idx for idx, name in enumerate(names)}
        labels = [index[record["oracle_label"]] for record in records]
        Path(output_dir).mkdir(parents=True)
        return {
            "comparisons": [
                {"comparison": "physical_local_inverse_probability", "labels": labels},
                {"comparison": "physical_local_inverse_probability_v2", "labels": labels},
                {"comparison": "direct_S_alpha_assignment", "labels": [0 for _ in labels]},
                {"comparison": "oracle_fingerprint_upper_bound", "labels": labels},
            ]
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
            "paths": {"teacher_dir": str(teacher_dir), "separability_dir": str(sep_dir), "local_inverse_dir": str(local_dir)},
            "stage_results": {"teacher": teacher, "teacher_self": sep, "learner": local},
        }

    monkeypatch.setattr(runner, "run_physical_oracle_stack", fake_stack)

    result = runner.run_s2d8a_rzz_depth_sweep(config_path)

    assert result["stage"] == "S2D.8a_RZZ_depth_sweep"
    out = tmp_path / "S2D.8_RZZ_dynamical_probe_design"
    assert (out / "metrics.json").exists()
    assert (out / "depth_probe_manifest.json").exists()
    assert (out / "depth_response_features.json").exists()
    assert (out / "scrambled_depth_control.json").exists()
    assert (out / "baseline_comparison.json").exists()
    assert (out / "phase_summary.json").exists()


def test_s2d8a_phase_summary_marks_control_matched_negative() -> None:
    summary = runner._phase_summary(
        [
            {
                "name": "phys9_setA",
                "profile": "phys9_chain",
                "decision": "regression_pass",
                "depth_sweep": {"scrambled_depth_control": {"real_ari": 1.0, "scrambled_ari": 1.0, "real_nmi": 1.0, "scrambled_nmi": 1.0}},
            },
            {
                "name": "phys9_multicircuit_setB_balanced",
                "profile": "phys9_multicircuit_setB_balanced",
                "decision": "failure",
                "depth_sweep": {"scrambled_depth_control": {"real_ari": 0.9, "scrambled_ari": 0.9, "real_nmi": 0.8, "scrambled_nmi": 0.8}},
            },
            {
                "name": "phys9_multicircuit_setC_balanced",
                "profile": "phys9_multicircuit_setC_balanced",
                "decision": "failure",
                "depth_sweep": {"scrambled_depth_control": {"real_ari": 0.92, "scrambled_ari": 0.92, "real_nmi": 0.84, "scrambled_nmi": 0.84}},
            },
        ]
    )

    assert summary["phase_label"] == "depth_sweep_control_matched_negative"
    assert summary["next_recommended_step"] == "S2D.8b_RZZ_echo_no_echo_probe_design"


def _record(label: str, qubits: list[int]) -> dict[str, object]:
    return {
        "location_id": 0,
        "oracle_label": label,
        "instruction": "rzz",
        "qubits": qubits,
        "num_qubits": len(qubits),
        "probe_indices": list(range(len(DEPTH_PROBES))),
        "parameters": {},
    }


def _known_depth_observations() -> np.ndarray:
    observations = np.zeros((len(DEPTH_PROBES), 4, 2), dtype=np.uint8)
    observations[3] = np.asarray([[0, 0], [0, 0], [0, 0], [0, 0]], dtype=np.uint8)
    observations[4] = np.asarray([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=np.uint8)
    observations[5] = np.asarray([[0, 1], [0, 1], [1, 0], [1, 0]], dtype=np.uint8)
    observations[6] = np.asarray([[0, 0], [0, 1], [1, 1], [1, 0]], dtype=np.uint8)
    return observations


def _observations(*, num_probes: int, shots: int, num_qubits: int) -> np.ndarray:
    rng = np.random.default_rng(31)
    rates = np.linspace(0.05, 0.45, int(num_probes) * int(num_qubits), dtype=np.float64).reshape(int(num_probes), int(num_qubits))
    return (rng.random((int(num_probes), int(shots), int(num_qubits))) < rates[:, None, :]).astype(np.uint8)


def hidden_labels_np(values: np.ndarray):
    import torch

    return torch.as_tensor(values, dtype=torch.long)
