from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import yaml

from scope_static.experiments import run_s2d7_rzz_active_probe_design as runner
from scope_static.physical.active_mixed_basis import (
    build_active_mixed_basis_features,
    evaluate_active_mixed_basis_methods,
    visibility_matrix,
)
from scope_static.physical.teacher import (
    EDGE_ORIENTATION_RULE,
    build_default_oracle_mechanisms,
    build_probe_basis_manifest,
    probe_basis_by_qubit,
)


ACTIVE_PROBES = ["z_basis", "x_measure", "y_measure", "alt_xz", "alt_zx", "alt_yz", "alt_zy", "alt_xy", "alt_yx"]


def test_active_probe_basis_metadata_and_edge_orientation_are_reproducible() -> None:
    manifest = build_probe_basis_manifest(["z_basis", "x_measure", "y_measure", "alt_xz", "alt_zx"], num_qubits=4)

    assert manifest["edge_orientation_rule"] == EDGE_ORIENTATION_RULE
    assert probe_basis_by_qubit("alt_xz", num_qubits=4) == ["X", "Z", "X", "Z"]
    assert probe_basis_by_qubit("alt_zx", num_qubits=4) == ["Z", "X", "Z", "X"]
    alt = manifest["probe_records"][3]
    assert alt["base_probe_name"] == "alt_xz"
    assert alt["measurable_edge_pairs"][0] == {"edge": [0, 1], "basis_pair": "XZ"}
    assert alt["measurable_edge_pairs"][1] == {"edge": [1, 2], "basis_pair": "ZX"}


def test_mixed_basis_edge_moments_and_signed_contrasts_from_shot_bits() -> None:
    records = [_record("M1", [0, 1])]
    observations = _known_two_qubit_observations()
    bundle = build_active_mixed_basis_features(records, observations, ACTIVE_PROBES, num_clusters=1)

    moment_names = bundle.feature_names["active_mixed_basis_moments"]
    moment_row = bundle.feature_spaces["active_mixed_basis_moments"][0]
    assert moment_row[moment_names.index("XZ_mean")] == 1.0
    assert moment_row[moment_names.index("ZX_mean")] == -1.0
    assert moment_row[moment_names.index("XZ_standard_error")] == 0.0

    signed_names = bundle.feature_names["active_mixed_basis_moments_plus_signed_contrasts"]
    signed_row = bundle.feature_spaces["active_mixed_basis_moments_plus_signed_contrasts"][0]
    assert signed_row[signed_names.index("XZ_minus_ZX_mean")] == 2.0
    assert np.all(np.isfinite(signed_row))


def test_centered_normalized_moments_handle_zero_variance_safely() -> None:
    records = [_record("M1", [0, 1])]
    observations = np.zeros((len(ACTIVE_PROBES), 8, 2), dtype=np.uint8)
    bundle = build_active_mixed_basis_features(records, observations, ACTIVE_PROBES, num_clusters=1)
    names = bundle.feature_names["active_mixed_basis_moments"]
    row = bundle.feature_spaces["active_mixed_basis_moments"][0]

    assert row[names.index("ZZ_mean")] == 1.0
    assert row[names.index("ZZ_connected")] == 0.0
    assert row[names.index("ZZ_normalized_correlation")] == 0.0
    assert np.all(np.isfinite(row))


def test_feature_provenance_manifest_marks_active_features_learner_visible() -> None:
    bundle = build_active_mixed_basis_features([_record("M1", [0, 1])], _known_two_qubit_observations(), ACTIVE_PROBES, num_clusters=1)
    manifest = bundle.feature_provenance_manifest

    for features in manifest["feature_blocks"].values():
        for spec in features:
            assert spec["uses_oracle_label"] is False
            assert spec["uses_exact_teacher_channel"] is False
            assert spec["uses_exact_ptm"] is False
            assert "shot_bits" in spec["visible_inputs"]
    assert manifest["audit_only_blocks"]["exact_ptm"]["oracle_only"] is True


def test_oracle_label_permutation_leaves_active_features_unchanged() -> None:
    observations = _known_two_qubit_observations()
    left = [_record("M1", [0, 1]), _record("M7", [0, 1])]
    right = [_record("M7", [0, 1]), _record("M1", [0, 1])]

    left_features = build_active_mixed_basis_features(left, observations, ACTIVE_PROBES, num_clusters=2).feature_spaces
    right_features = build_active_mixed_basis_features(right, observations, ACTIVE_PROBES, num_clusters=2).feature_spaces

    for key in left_features:
        np.testing.assert_allclose(left_features[key], right_features[key])


def test_teacher_channel_deletion_still_allows_feature_extraction() -> None:
    record = {"location_id": 0, "instruction": "rzz", "qubits": [0, 1], "num_qubits": 2, "probe_indices": list(range(len(ACTIVE_PROBES)))}

    bundle = build_active_mixed_basis_features([record], _known_two_qubit_observations(), ACTIVE_PROBES, num_clusters=1)

    assert "active_mixed_basis_moments" in bundle.feature_spaces
    assert bundle.feature_spaces["active_mixed_basis_moments"].shape[0] == 1


def test_scrambled_control_preserves_dimensions_and_marginals_exclude_edge_products() -> None:
    bundle = build_active_mixed_basis_features([_record("M1", [0, 1])], _known_two_qubit_observations(), ACTIVE_PROBES, num_clusters=1)

    real = bundle.feature_spaces["active_mixed_basis_moments_plus_signed_contrasts"]
    scrambled = bundle.feature_spaces["active_mixed_basis_scrambled"]
    assert real.shape == scrambled.shape
    assert not np.allclose(real, scrambled)
    assert all("XZ_mean" not in name for name in bundle.feature_names["active_basis_marginals_only"])


def test_visibility_matrix_separates_base_and_active_mixed_basis_visibility() -> None:
    manifest = build_probe_basis_manifest(ACTIVE_PROBES, num_qubits=3)
    matrix = visibility_matrix(manifest)

    assert matrix["base_probes_cannot_expose_mixed_basis"] is True
    assert matrix["active_probes_expose_mixed_basis"] is True
    assert matrix["base_probe_visibility_counts"]["XZ"] == 0
    assert matrix["active_probe_visibility_counts"]["XZ"] > 0


def test_active_evaluation_reports_rzz_family_metrics() -> None:
    records = [_record("M1", [0, 1]), _record("M7", [0, 1]), _record("M8", [0, 1]), _record("M10", [0, 1])]
    observations = np.concatenate([_known_two_qubit_observations(), _known_two_qubit_observations()], axis=1)
    label_names = sorted({str(record["oracle_label"]) for record in records})
    index = {name: idx for idx, name in enumerate(label_names)}
    hidden = np.asarray([index[str(record["oracle_label"])] for record in records])

    result = evaluate_active_mixed_basis_methods(records, observations, ACTIVE_PROBES, hidden_labels_np(hidden), label_names)

    assert "active_mixed_basis_moments_plus_signed_contrasts" in result["labels_by_method"]
    metrics = result["rzz_family_metrics"]["methods"]["active_mixed_basis_moments_plus_signed_contrasts"]
    assert "RZZ_family_ARI" in metrics
    assert "M1_M7_merge_count" in metrics


def test_s2d7_runner_writes_required_artifacts_with_fakes(tmp_path: Path, monkeypatch) -> None:
    config = {
        "run": {"output_root": str(tmp_path)},
        "s2d_physical": {"shots": 16, "paper_informed_ptm_features": True},
        "s2d7_rzz_active_probe_design": {
            "output_dir": str(tmp_path / "S2D.7_RZZ_active_probe_design"),
            "bootstrap_replicates": 1,
            "random_baseline_trials": 1,
            "runs": [{"name": "phys9_setA", "profile": "phys9_chain", "mechanism_set": "set_A"}],
        },
    }
    config_path = tmp_path / "s2d7.yaml"
    config_path.write_text(yaml.safe_dump(config))

    def fake_teacher(cfg, *, output_dir, preflight_dir):
        out = Path(output_dir)
        out.mkdir(parents=True)
        specs = build_default_oracle_mechanisms(cfg)
        records = [{"location_id": idx, **spec.audit_dict(), "oracle_label": spec.mechanism_id} for idx, spec in enumerate(specs)]
        probe_names = ACTIVE_PROBES if cfg.get("probe_set") == "rzz_active_minimal" else ["z_basis", "x_measure", "y_measure"]
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

    result = runner.run_s2d7_rzz_active_probe_design(config_path)

    assert result["stage"] == "S2D.7_RZZ_active_probe_design"
    out = tmp_path / "S2D.7_RZZ_active_probe_design"
    assert (out / "metrics.json").exists()
    assert (out / "active_probe_manifest.json").exists()
    assert (out / "feature_provenance_manifest.json").exists()
    assert (out / "scrambled_basis_control.json").exists()
    assert (out / "freeze_summary.json").exists()
    metrics = json.loads((out / "metrics.json").read_text())
    assert "freeze_summary" in metrics
    assert "active_mixed_basis_moments_plus_signed_contrasts" in metrics["records"][0]["PHYS3"]


def test_s2d7_freeze_summary_marks_balanced_negative_result() -> None:
    summary = runner._freeze_summary(
        [
            {"name": "phys9_setA", "profile": "phys9_chain", "decision": "regression_pass"},
            {"name": "phys9_multicircuit_setB_balanced", "profile": "phys9_multicircuit_setB_balanced", "decision": "failure"},
            {"name": "phys9_multicircuit_setC_balanced", "profile": "phys9_multicircuit_setC_balanced", "decision": "failure"},
        ]
    )

    assert summary["freeze_label"] == "negative_static_mixed_basis_probe_result"
    assert "scrambled_control_matched_real_active_features" in summary["freeze_tags"]
    assert summary["next_recommended_step"] == "S2D.8_RZZ_dynamical_probe_design"


def _record(label: str, qubits: list[int]) -> dict[str, object]:
    return {
        "location_id": 0,
        "oracle_label": label,
        "instruction": "rzz",
        "qubits": qubits,
        "num_qubits": len(qubits),
        "probe_indices": list(range(len(ACTIVE_PROBES))),
        "parameters": {},
    }


def _known_two_qubit_observations() -> np.ndarray:
    observations = np.zeros((len(ACTIVE_PROBES), 4, 2), dtype=np.uint8)
    observations[0] = np.asarray([[0, 0], [0, 0], [0, 0], [0, 0]], dtype=np.uint8)  # ZZ = 1
    observations[1] = np.asarray([[0, 0], [1, 1], [0, 0], [1, 1]], dtype=np.uint8)  # XX = 1
    observations[2] = np.asarray([[0, 1], [0, 1], [1, 0], [1, 0]], dtype=np.uint8)  # YY = -1
    observations[3] = np.asarray([[0, 0], [0, 0], [0, 0], [0, 0]], dtype=np.uint8)  # XZ = 1
    observations[4] = np.asarray([[0, 1], [0, 1], [0, 1], [0, 1]], dtype=np.uint8)  # ZX = -1
    observations[5] = np.asarray([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=np.uint8)  # YZ = 0
    observations[6] = np.asarray([[0, 0], [1, 0], [0, 1], [1, 1]], dtype=np.uint8)  # ZY = 0
    observations[7] = np.asarray([[0, 0], [0, 0], [1, 1], [1, 1]], dtype=np.uint8)  # XY = 1
    observations[8] = np.asarray([[0, 1], [1, 0], [0, 1], [1, 0]], dtype=np.uint8)  # YX = -1
    return observations


def _observations(*, num_probes: int, shots: int, num_qubits: int) -> np.ndarray:
    rng = np.random.default_rng(27)
    rates = np.linspace(0.05, 0.45, int(num_probes) * int(num_qubits), dtype=np.float64).reshape(int(num_probes), int(num_qubits))
    return (rng.random((int(num_probes), int(shots), int(num_qubits))) < rates[:, None, :]).astype(np.uint8)


def hidden_labels_np(values: np.ndarray):
    import torch

    return torch.as_tensor(values, dtype=torch.long)
