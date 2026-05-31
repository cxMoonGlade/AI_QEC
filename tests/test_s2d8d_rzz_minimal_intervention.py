from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch
import yaml

from scope_static.experiments.qec_noise_catalog import s2d8d_rzz_minimal_intervention as runner
from scope_static.mechanism_observability import build_rzz_minimal_intervention_features
from scope_static.primitives.probe_catalog import (
    RZZ_MINIMAL_INTERVENTION_PROBES,
    build_default_oracle_mechanisms,
    build_probe_basis_manifest,
    build_probe_circuits,
)


INTERVENTION_PROBES = ["z_basis", "x_measure", "y_measure", *RZZ_MINIMAL_INTERVENTION_PROBES]


def test_minimal_intervention_probe_naming_and_counts() -> None:
    circuits, names = build_probe_circuits({"profile": "phys9_chain", "probe_set": "rzz_minimal_intervention"})

    assert names == INTERVENTION_PROBES
    rzz_counts = [int(circuit.count_ops().get("rzz", 0)) for circuit in circuits]
    assert rzz_counts[:14] == [8 for _ in range(14)]
    assert rzz_counts[14:] == [16, 16, 16, 16, 16]
    x_counts = [int(circuit.count_ops().get("x", 0)) for circuit in circuits]
    y_counts = [int(circuit.count_ops().get("y", 0)) for circuit in circuits]
    assert max(x_counts[8:14]) > 0
    assert max(y_counts[8:14]) > 0
    assert max(x_counts[15:]) > 0


def test_minimal_intervention_manifest_has_edge_orientation_and_roles() -> None:
    manifest = build_probe_basis_manifest(INTERVENTION_PROBES, num_qubits=9)
    by_name = {record["base_probe_name"]: record for record in manifest["probe_records"]}

    assert manifest["edge_orientation_rule"] == "lower_qubit_to_higher_qubit"
    assert by_name["rzz_int_no_intervention"]["rzz_intervention_family"] == "baseline"
    assert by_name["rzz_int_twirl_x_left_even"]["rzz_intervention_family"] == "pauli_frame_twirl"
    assert by_name["rzz_int_twirl_x_left_even"]["rzz_intervention_edge_parity"] == "even"
    assert by_name["rzz_int_twirl_x_left_even"]["rzz_intervention_pauli_frame"] == {"left": "X", "right": "I"}
    assert [item["edge"] for item in by_name["rzz_int_sign_flip_right_odd"]["rzz_intervention_edge_pairs"]] == [[1, 2], [3, 4], [5, 6], [7, 8]]


def test_minimal_intervention_features_recover_known_edge_moments() -> None:
    records = [_record("M1", [0, 1])]
    observations = _known_intervention_observations()
    bundle = build_rzz_minimal_intervention_features(records, observations, INTERVENTION_PROBES, num_clusters=1)

    twirl_names = bundle.feature_names["twirl_intervention_features"]
    twirl_row = bundle.feature_spaces["twirl_intervention_features"][0]
    echo_names = bundle.feature_names["echo_sign_intervention_features"]
    echo_row = bundle.feature_spaces["echo_sign_intervention_features"][0]

    assert twirl_row[twirl_names.index("pauli_frame_twirl_no_intervention_zz_mean")] == 1.0
    assert twirl_row[twirl_names.index("pauli_frame_twirl_twirl_x_left_zz_mean")] == -1.0
    assert echo_row[echo_names.index("sign_flip_echo_sign_no_flip_zz_mean")] == 1.0
    assert echo_row[echo_names.index("sign_flip_echo_sign_flip_right_zz_mean")] == -1.0
    assert np.all(np.isfinite(bundle.feature_spaces["minimal_intervention_all"]))


def test_scrambled_minimal_intervention_control_preserves_shape_and_changes_features() -> None:
    bundle = build_rzz_minimal_intervention_features([_record("M1", [0, 1])], _known_intervention_observations(), INTERVENTION_PROBES, num_clusters=1)

    real = bundle.feature_spaces["minimal_intervention_all"]
    scrambled = bundle.feature_spaces["scrambled_minimal_intervention_control"]
    assert real.shape == scrambled.shape
    assert not np.allclose(real, scrambled)


def test_minimal_intervention_provenance_is_learner_visible_and_oracle_free() -> None:
    bundle = build_rzz_minimal_intervention_features([_record("M1", [0, 1])], _known_intervention_observations(), INTERVENTION_PROBES, num_clusters=1)
    manifest = bundle.feature_provenance_manifest

    for features in manifest["feature_blocks"].values():
        for spec in features:
            assert spec["uses_oracle_label"] is False
            assert spec["uses_exact_teacher_channel"] is False
            assert spec["uses_exact_ptm"] is False
            assert "shot_bits" in spec["visible_inputs"]
            assert "probe_intervention_metadata" in spec["visible_inputs"]


def test_oracle_label_permutation_leaves_minimal_intervention_features_unchanged() -> None:
    obs = _known_intervention_observations()
    a = build_rzz_minimal_intervention_features([_record("M1", [0, 1])], obs, INTERVENTION_PROBES, num_clusters=1)
    b = build_rzz_minimal_intervention_features([_record("M7", [0, 1])], obs, INTERVENTION_PROBES, num_clusters=1)

    assert np.allclose(a.feature_spaces["minimal_intervention_all"], b.feature_spaces["minimal_intervention_all"])


def test_s2d8d_runner_writes_required_artifacts_with_fakes(tmp_path: Path, monkeypatch) -> None:
    config = {
        "run": {"output_root": str(tmp_path)},
        "s2d_physical": {"shots": 16, "paper_informed_ptm_features": True},
        "s2d8d_rzz_minimal_intervention": {
            "output_dir": str(tmp_path / "S2D.8_RZZ_dynamical_probe_design" / "S2D.8d_RZZ_minimal_intervention_probe"),
            "bootstrap_replicates": 1,
            "random_baseline_trials": 1,
            "permutation_repeats": 2,
            "runs": [{"name": "phys9_setA", "profile": "phys9_chain", "mechanism_set": "set_A"}],
        },
    }
    config_path = tmp_path / "s2d8d.yaml"
    config_path.write_text(yaml.safe_dump(config))

    def fake_teacher(cfg, *, output_dir, preflight_dir):
        out = Path(output_dir)
        out.mkdir(parents=True)
        specs = build_default_oracle_mechanisms(cfg)
        probe_names = INTERVENTION_PROBES if cfg.get("probe_set") == "rzz_minimal_intervention" else ["z_basis", "x_measure", "y_measure"]
        records = []
        for idx, spec in enumerate(specs):
            record = {"location_id": idx, **spec.audit_dict(), "oracle_label": spec.mechanism_id}
            record["probe_indices"] = list(range(len(probe_names)))
            records.append(record)
        np.savez_compressed(
            out / "observations.npz",
            observations=_observations(num_probes=len(probe_names), shots=16, num_qubits=9),
            probe_names=np.asarray(probe_names),
            shots=np.asarray([16], dtype=np.int64),
        )
        (out / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}, indent=2) + "\n")
        (out / "active_probe_manifest.json").write_text(json.dumps(build_probe_basis_manifest(probe_names, num_qubits=9)))
        return {"mechanism_counts": {"M1": 1}, "num_qubits": 9, "output_dir": str(out)}

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

    def fake_pipeline(cfg, *, output_dir, bootstrap_replicates, random_baseline_trials, run_local_inverse):
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

    monkeypatch.setattr(runner, "run_catalog_pipeline", fake_pipeline)

    result = runner.run_s2d8d_rzz_minimal_intervention(config_path)

    assert result["stage"] == "S2D.8d_RZZ_minimal_intervention_probe"
    out = tmp_path / "S2D.8_RZZ_dynamical_probe_design" / "S2D.8d_RZZ_minimal_intervention_probe"
    assert (out / "metrics.json").exists()
    assert (out / "intervention_schema.json").exists()
    assert (out / "mechanism_response_table.json").exists()
    assert (out / "twirl_response_metrics.json").exists()
    assert (out / "basis_response_metrics.json").exists()
    assert (out / "echo_response_metrics.json").exists()
    assert (out / "grouped_fold_predictions.json").exists()
    assert (out / "leakage_guardrail_audit.json").exists()


def _record(label: str, qubits: list[int]) -> dict[str, object]:
    return {
        "location_id": 0,
        "oracle_label": label,
        "instruction": "rzz",
        "qubits": qubits,
        "circuit_id": 0,
        "probe_indices": list(range(len(INTERVENTION_PROBES))),
    }


def _known_intervention_observations(num_qubits: int = 2) -> np.ndarray:
    observations = np.zeros((len(INTERVENTION_PROBES), 4, num_qubits), dtype=np.uint8)
    by_name = {name: idx for idx, name in enumerate(INTERVENTION_PROBES)}
    observations[by_name["rzz_int_twirl_x_left_even"], :, 1] = 1
    observations[by_name["rzz_int_sign_flip_right_even"], :, 1] = 1
    observations[by_name["rzz_int_basis_x"], :, 0] = np.asarray([0, 0, 1, 1], dtype=np.uint8)
    observations[by_name["rzz_int_basis_x"], :, 1] = np.asarray([0, 1, 0, 1], dtype=np.uint8)
    return observations


def _observations(*, num_probes: int, shots: int, num_qubits: int) -> np.ndarray:
    rng = np.random.default_rng(123)
    return rng.integers(0, 2, size=(int(num_probes), int(shots), int(num_qubits)), dtype=np.uint8)
