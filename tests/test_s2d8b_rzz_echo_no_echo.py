from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import yaml

from scope_static.experiments import run_s2d8b_rzz_echo_no_echo as runner
from scope_static.physical.rzz_echo_contrast import build_rzz_echo_contrast_features, evaluate_rzz_echo_contrast_methods
from scope_static.physical.teacher import (
    RZZ_ECHO_CONTRAST_PROBES,
    build_default_oracle_mechanisms,
    build_probe_basis_manifest,
    build_probe_circuits,
)


ECHO_PROBES = ["z_basis", "x_measure", "y_measure", *RZZ_ECHO_CONTRAST_PROBES]
DEPTH_PROBES = ["z_basis", "x_measure", "y_measure", "rzz_depth_1", "rzz_depth_2", "rzz_depth_4", "rzz_depth_8"]
ACTIVE_PROBES = ["z_basis", "x_measure", "y_measure", "alt_xz", "alt_zx", "alt_yz", "alt_zy", "alt_xy", "alt_yx"]


def test_echo_probe_naming_and_colored_repetition_count() -> None:
    circuits, names = build_probe_circuits({"profile": "phys9_chain", "probe_set": "rzz_echo_no_echo"})

    assert names == ECHO_PROBES
    assert [int(circuit.count_ops().get("rzz", 0)) for circuit in circuits] == [8, 8, 8, 16, 16, 16, 16, 16, 16, 16]
    assert [int(circuit.count_ops().get("x", 0)) for circuit in circuits[3:]] == [0, 8, 8, 16, 8, 8, 16]


def test_echo_probe_manifest_has_reproducible_edge_coloring() -> None:
    manifest = build_probe_basis_manifest(ECHO_PROBES, num_qubits=9)
    by_name = {record["base_probe_name"]: record for record in manifest["probe_records"]}

    assert by_name["rzz_no_echo"]["rzz_echo_role"] == "no_echo"
    assert by_name["rzz_no_echo"]["rzz_echo_edge_parity"] == "all"
    assert by_name["rzz_echo_left_even"]["rzz_echo_role"] == "echo_left"
    assert by_name["rzz_echo_left_even"]["rzz_echo_edge_parity"] == "even"
    assert [item["edge"] for item in by_name["rzz_echo_left_even"]["rzz_echo_edge_pairs"]] == [[0, 1], [2, 3], [4, 5], [6, 7]]
    assert [item["edge"] for item in by_name["rzz_echo_right_odd"]["rzz_echo_edge_pairs"]] == [[1, 2], [3, 4], [5, 6], [7, 8]]


def test_echo_contrast_feature_extraction_from_shot_bits() -> None:
    records = [_record("M1", [0, 1])]
    bundle = build_rzz_echo_contrast_features(records, _known_echo_observations(), ECHO_PROBES, num_clusters=1)

    names = bundle.feature_names["rzz_echo_contrast_features"]
    row = bundle.feature_spaces["rzz_echo_contrast_features"][0]

    assert row[names.index("no_echo_zz_mean")] == 1.0
    assert row[names.index("echo_left_zz_mean")] == 0.0
    assert row[names.index("echo_right_zz_mean")] == -1.0
    assert row[names.index("echo_both_zz_mean")] == 0.0
    assert row[names.index("no_echo_minus_echo_right_mean")] == 2.0
    assert np.all(np.isfinite(row))


def test_odd_edge_uses_odd_echo_probe_pairing() -> None:
    records = [_record("M1", [1, 2])]
    observations = _known_echo_observations(num_qubits=3)
    observations[7] = np.asarray([[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]], dtype=np.uint8)
    bundle = build_rzz_echo_contrast_features(records, observations, ECHO_PROBES, num_clusters=1)

    names = bundle.feature_names["rzz_echo_contrast_features"]
    row = bundle.feature_spaces["rzz_echo_contrast_features"][0]

    assert row[names.index("echo_left_zz_mean")] == 1.0


def test_scrambled_echo_control_preserves_shape_and_changes_features() -> None:
    records = [_record("M1", [0, 1])]
    bundle = build_rzz_echo_contrast_features(records, _known_echo_observations(), ECHO_PROBES, num_clusters=1)

    real = bundle.feature_spaces["rzz_echo_contrast_features"]
    scrambled = bundle.feature_spaces["scrambled_echo_control"]
    assert real.shape == scrambled.shape
    assert not np.allclose(real, scrambled)


def test_echo_feature_provenance_is_learner_visible_and_oracle_free() -> None:
    bundle = build_rzz_echo_contrast_features([_record("M1", [0, 1])], _known_echo_observations(), ECHO_PROBES, num_clusters=1)
    manifest = bundle.feature_provenance_manifest

    assert "exact_ptm_entries" in manifest["forbidden_in_phys3"]
    for features in manifest["feature_blocks"].values():
        for spec in features:
            assert spec["uses_oracle_label"] is False
            assert spec["uses_exact_teacher_channel"] is False
            assert spec["uses_exact_ptm"] is False
            assert "shot_bits" in spec["visible_inputs"]
            assert "probe_echo_role" in spec["visible_inputs"]


def test_oracle_label_permutation_leaves_echo_features_unchanged() -> None:
    records_a = [_record("M1", [0, 1])]
    records_b = [_record("M7", [0, 1])]
    obs = _known_echo_observations()

    a = build_rzz_echo_contrast_features(records_a, obs, ECHO_PROBES, num_clusters=1)
    b = build_rzz_echo_contrast_features(records_b, obs, ECHO_PROBES, num_clusters=1)

    assert np.allclose(a.feature_spaces["rzz_echo_contrast_features"], b.feature_spaces["rzz_echo_contrast_features"])


def test_echo_evaluation_reports_bootstrap_and_rzz_metrics() -> None:
    records = [_record("M1", [0, 1]), _record("M7", [0, 1]), _record("M8", [0, 1]), _record("M10", [0, 1])]
    observations = np.concatenate([_known_echo_observations(), _known_echo_observations()], axis=1)
    label_names = sorted({str(record["oracle_label"]) for record in records})
    index = {name: idx for idx, name in enumerate(label_names)}
    hidden = np.asarray([index[str(record["oracle_label"])] for record in records])

    result = evaluate_rzz_echo_contrast_methods(
        records,
        observations,
        ECHO_PROBES,
        hidden_labels_np(hidden),
        label_names,
        bootstrap_replicates=2,
    )

    echo = next(row for row in result["methods"] if row["method"] == "rzz_echo_contrast_features")
    assert echo["bootstrap_nmi"]["replicates"] == 2
    assert "rzz_echo_contrast_features" in result["rzz_family_metrics"]["methods"]
    assert "M1_M7_merge_count" in result["rzz_family_metrics"]["methods"]["rzz_echo_contrast_features"]


def test_s2d8b_runner_writes_required_artifacts_with_fakes(tmp_path: Path, monkeypatch) -> None:
    config = {
        "run": {"output_root": str(tmp_path)},
        "s2d_physical": {"shots": 16, "paper_informed_ptm_features": True},
        "s2d8b_rzz_echo_no_echo": {
            "output_dir": str(tmp_path / "S2D.8_RZZ_dynamical_probe_design" / "S2D.8b_RZZ_echo_no_echo_probe_design"),
            "bootstrap_replicates": 1,
            "random_baseline_trials": 1,
            "runs": [{"name": "phys9_setA", "profile": "phys9_chain", "mechanism_set": "set_A"}],
        },
    }
    config_path = tmp_path / "s2d8b.yaml"
    config_path.write_text(yaml.safe_dump(config))

    def fake_teacher(cfg, *, output_dir, preflight_dir):
        out = Path(output_dir)
        out.mkdir(parents=True)
        specs = build_default_oracle_mechanisms(cfg)
        if cfg.get("probe_set") == "rzz_echo_no_echo":
            probe_names = ECHO_PROBES
        elif cfg.get("probe_set") == "rzz_depth_sweep":
            probe_names = DEPTH_PROBES
        elif cfg.get("probe_set") == "rzz_active_minimal":
            probe_names = ACTIVE_PROBES
        else:
            probe_names = ["z_basis", "x_measure", "y_measure"]
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
        (out / "noise_application_audit.json").write_text(json.dumps({"records": []}))
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

    monkeypatch.setattr(runner, "generate_physical_teacher_dataset", fake_teacher)
    monkeypatch.setattr(runner, "run_oracle_separability_audit", fake_sep)
    monkeypatch.setattr(runner, "run_physical_local_inverse_discovery", fake_local)

    result = runner.run_s2d8b_rzz_echo_no_echo(config_path)

    assert result["stage"] == "S2D.8b_RZZ_echo_no_echo_probe_design"
    out = tmp_path / "S2D.8_RZZ_dynamical_probe_design" / "S2D.8b_RZZ_echo_no_echo_probe_design"
    assert (out / "metrics.json").exists()
    assert (out / "echo_probe_manifest.json").exists()
    assert (out / "echo_response_features.json").exists()
    assert (out / "scrambled_echo_control.json").exists()
    assert (out / "baseline_comparison.json").exists()
    assert (out / "phase_summary.json").exists()


def test_s2d8b_phase_summary_marks_control_matched_negative() -> None:
    summary = runner._phase_summary(
        [
            {
                "name": "phys9_setA",
                "profile": "phys9_chain",
                "decision": "regression_pass",
                "echo_contrast": {"scrambled_echo_control": {"real_ari": 1.0, "scrambled_ari": 1.0, "real_nmi": 1.0, "scrambled_nmi": 1.0}},
            },
            {
                "name": "phys9_multicircuit_setB_balanced",
                "profile": "phys9_multicircuit_setB_balanced",
                "decision": "failure",
                "echo_contrast": {"scrambled_echo_control": {"real_ari": 0.9, "scrambled_ari": 0.9, "real_nmi": 0.8, "scrambled_nmi": 0.8}},
            },
            {
                "name": "phys9_multicircuit_setC_balanced",
                "profile": "phys9_multicircuit_setC_balanced",
                "decision": "failure",
                "echo_contrast": {"scrambled_echo_control": {"real_ari": 0.92, "scrambled_ari": 0.92, "real_nmi": 0.84, "scrambled_nmi": 0.84}},
            },
        ]
    )

    assert summary["phase_label"] == "echo_no_echo_control_matched_negative"
    assert summary["next_recommended_step"] == "S2D.8c_minimal_twirl_style_probes"


def test_s2d8b_phase_summary_marks_mixed_control_limited() -> None:
    summary = runner._phase_summary(
        [
            {
                "name": "phys9_setA",
                "profile": "phys9_chain",
                "decision": "regression_pass",
                "echo_contrast": {"scrambled_echo_control": {"real_beats_scrambled": False, "real_ari": 1.0, "scrambled_ari": 1.0, "real_nmi": 1.0, "scrambled_nmi": 1.0}},
            },
            {
                "name": "phys9_multicircuit_setB_balanced",
                "profile": "phys9_multicircuit_setB_balanced",
                "decision": "failure",
                "echo_contrast": {"scrambled_echo_control": {"real_beats_scrambled": False, "real_ari": 0.9, "scrambled_ari": 0.91, "real_nmi": 0.8, "scrambled_nmi": 0.81}},
            },
            {
                "name": "phys9_multicircuit_setC_balanced",
                "profile": "phys9_multicircuit_setC_balanced",
                "decision": "partial_m1_m7_m10_improved",
                "echo_contrast": {"scrambled_echo_control": {"real_beats_scrambled": False, "real_ari": 0.92, "scrambled_ari": 0.92, "real_nmi": 0.84, "scrambled_nmi": 0.84}},
            },
        ]
    )

    assert summary["phase_label"] == "echo_no_echo_mixed_control_limited"
    assert summary["next_recommended_step"] == "S2D.8c_minimal_twirl_style_probes"


def _record(label: str, qubits: list[int]) -> dict[str, object]:
    return {
        "location_id": 0,
        "oracle_label": label,
        "instruction": "rzz",
        "qubits": qubits,
        "num_qubits": len(qubits),
        "probe_indices": list(range(len(ECHO_PROBES))),
        "parameters": {},
    }


def _known_echo_observations(*, num_qubits: int = 2) -> np.ndarray:
    observations = np.zeros((len(ECHO_PROBES), 4, int(num_qubits)), dtype=np.uint8)
    observations[3, :, :2] = np.asarray([[0, 0], [0, 0], [0, 0], [0, 0]], dtype=np.uint8)
    observations[4, :, :2] = np.asarray([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=np.uint8)
    observations[5, :, :2] = np.asarray([[0, 1], [0, 1], [1, 0], [1, 0]], dtype=np.uint8)
    observations[6, :, :2] = np.asarray([[0, 0], [0, 1], [1, 1], [1, 0]], dtype=np.uint8)
    observations[7, :, :2] = np.asarray([[0, 1], [0, 1], [1, 0], [1, 0]], dtype=np.uint8)
    observations[8, :, :2] = np.asarray([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=np.uint8)
    observations[9, :, :2] = np.asarray([[0, 0], [0, 0], [1, 1], [1, 1]], dtype=np.uint8)
    return observations


def _observations(*, num_probes: int, shots: int, num_qubits: int) -> np.ndarray:
    rng = np.random.default_rng(37)
    rates = np.linspace(0.05, 0.45, int(num_probes) * int(num_qubits), dtype=np.float64).reshape(int(num_probes), int(num_qubits))
    return (rng.random((int(num_probes), int(shots), int(num_qubits))) < rates[:, None, :]).astype(np.uint8)


def hidden_labels_np(values: np.ndarray):
    import torch

    return torch.as_tensor(values, dtype=torch.long)
