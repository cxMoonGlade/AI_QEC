from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import yaml

from scope_static.experiments.run_s2d_local_inverse_discovery import run_s2d_local_inverse_discovery
from scope_static.physical.local_inverse import build_visible_location_representations
from scope_static.physical.teacher import build_default_oracle_mechanisms


def test_visible_location_representations_ignore_oracle_labels() -> None:
    records = _mechanism_records()
    observations = _observations()

    original = build_visible_location_representations(records, observations, ["z_basis", "x_measure", "y_measure"])
    altered = [dict(record, oracle_label="withheld") for record in records]
    changed = build_visible_location_representations(altered, observations, ["z_basis", "x_measure", "y_measure"])

    assert np.allclose(original["physical_local_inverse_probability"], changed["physical_local_inverse_probability"])
    assert np.allclose(original["physical_local_inverse_probability_v2"], changed["physical_local_inverse_probability_v2"])
    assert np.allclose(original["raw_local_inverse_logits"], changed["raw_local_inverse_logits"])


def test_s2d_local_inverse_discovery_writes_required_artifacts(tmp_path: Path) -> None:
    teacher = tmp_path / "S2D_PHYS1_teacher"
    teacher.mkdir()
    records = _mechanism_records()
    (teacher / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}, indent=2) + "\n")
    np.savez_compressed(
        teacher / "observations.npz",
        observations=_observations(shots=96),
        probe_names=np.asarray(["z_basis", "x_measure", "y_measure"]),
        shots=np.asarray([96], dtype=np.int64),
    )
    config_path = tmp_path / "s2d_local_inverse.yaml"
    output = tmp_path / "S2D_PHYS3_local_inverse"
    config_path.write_text(
        yaml.safe_dump(
            {
                "run": {"output_root": str(tmp_path)},
                "s2d_physical": {"paper_informed_ptm_features": True},
                "s2d_local_inverse": {
                    "teacher_dir": str(teacher),
                    "separability_dir": str(tmp_path / "S2D_PHYS2_oracle_separability"),
                    "output_dir": str(output),
                    "num_clusters": 6,
                    "bootstrap_replicates": 3,
                    "random_baseline_trials": 4,
                    "seed": 11,
                },
            }
        )
    )

    result = run_s2d_local_inverse_discovery(config_path)

    assert result["stage"] == "S2D_PHYS3_local_inverse"
    assert result["predeclared_representation"] == "physical_local_inverse_probability"
    assert result["ari_nmi_used_for_selection"] is False
    assert result["run_selection_audit"]["uses_oracle_labels_for_training"] is False
    assert result["run_selection_audit"]["uses_oracle_labels_for_selection"] is False
    assert result["main_result"]["ari"] == 1.0
    assert result["main_result"]["nmi"] == 1.0
    assert result["s2d3_result"] == "physical_oracle_strong_recovery"
    assert set(result["prediction_metrics"]) == {"local_inverse", "local_inverse_v2", "direct_Salpha", "oracle_fingerprint"}
    assert "heldout_response_nll" in result["prediction_metrics"]["local_inverse"]
    assert "physical_local_inverse_probability_v2_result" in result
    assert "base_rate_null_NLL" in result["nll_difficulty_audit"]
    assert {record["comparison"] for record in result["comparisons"]} >= {
        "random_partition",
        "structural_only_features",
        "raw_observation_probe_summary",
        "direct_S_alpha_assignment",
        "raw_local_inverse_logits",
        "physical_local_inverse_probability",
        "oracle_fingerprint_upper_bound",
    }
    assert (output / "metrics.json").exists()
    assert (output / "summary.md").exists()
    assert (output / "local_inverse_probabilities.npy").exists()
    assert (output / "clusters.json").exists()
    assert (output / "confusion_matrix.json").exists()
    assert (output / "run_selection_audit.json").exists()
    assert np.load(output / "local_inverse_probabilities.npy").shape[0] == len(records)


def _mechanism_records() -> list[dict[str, object]]:
    specs = build_default_oracle_mechanisms({"include_m5": True, "num_qubits": 5})
    return [{"location_id": idx, **spec.audit_dict(), "oracle_label": spec.mechanism_id} for idx, spec in enumerate(specs)]


def _observations(*, shots: int = 64) -> np.ndarray:
    rates = np.array(
        [
            [0.02, 0.03, 0.04, 0.12, 0.22],
            [0.50, 0.52, 0.43, 0.58, 0.35],
            [0.49, 0.47, 0.61, 0.54, 0.70],
        ],
        dtype=np.float64,
    )
    rng = np.random.default_rng(5)
    return (rng.random((3, int(shots), 5)) < rates[:, None, :]).astype(np.uint8)
