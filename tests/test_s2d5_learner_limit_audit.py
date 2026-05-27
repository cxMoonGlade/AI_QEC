from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import yaml

from scope_static.experiments.run_s2d5_learner_limit_audit import run_s2d5_learner_limit_audit
from scope_static.physical.ptm import channel_fingerprint, probe_response_fingerprint, rzz_type_feature_vector
from scope_static.physical.teacher import build_default_oracle_mechanisms


def test_s2d5_audit_writes_failure_representation_and_nll_artifacts(tmp_path: Path) -> None:
    phys4 = tmp_path / "S2D_PHYS4_difficulty_expansion"
    run_dir = phys4 / "phys9_setB"
    teacher = run_dir / "S2D_PHYS1_teacher"
    sep = run_dir / "S2D_PHYS2_oracle_separability"
    local = run_dir / "S2D_PHYS3_local_inverse"
    teacher.mkdir(parents=True)
    sep.mkdir()
    local.mkdir()

    specs = build_default_oracle_mechanisms({"profile": "phys9_chain", "mechanism_set": "set_B"})[:9]
    records = [{"location_id": idx, **spec.audit_dict(), "oracle_label": spec.mechanism_id} for idx, spec in enumerate(specs)]
    (teacher / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}, indent=2) + "\n")
    np.savez_compressed(
        teacher / "observations.npz",
        observations=_observations(shots=80, num_qubits=9),
        probe_names=np.asarray(["z_basis", "x_measure", "y_measure"]),
        shots=np.asarray([80], dtype=np.int64),
    )
    fingerprints = np.concatenate(
        [
            np.stack([channel_fingerprint(spec, paper_informed=True) for spec in specs], axis=0),
            np.stack([probe_response_fingerprint(spec) for spec in specs], axis=0),
            np.stack([rzz_type_feature_vector(spec) for spec in specs], axis=0),
        ],
        axis=1,
    )
    np.save(sep / "fingerprints.npy", fingerprints)
    labels = [idx % 4 for idx in range(len(records))]
    local_metrics = {
        "main_result": {"ari": 0.2, "nmi": 0.5},
        "comparisons": [
            {"comparison": "physical_local_inverse_probability", "labels": labels},
            {"comparison": "physical_local_inverse_probability_v2", "labels": labels},
            {"comparison": "direct_S_alpha_assignment", "labels": list(reversed(labels))},
            {"comparison": "oracle_fingerprint_upper_bound", "labels": [idx % len({r["oracle_label"] for r in records}) for idx in range(len(records))]},
        ],
    }
    (local / "metrics.json").write_text(json.dumps(local_metrics, indent=2) + "\n")
    config_path = tmp_path / "s2d5.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "s2d5_learner_limit_audit": {
                    "phys4_dir": str(phys4),
                    "output_dir": str(tmp_path / "S2D.5_learner_limit_audit_and_representation_v2"),
                    "runs": ["phys9_setB"],
                }
            }
        )
    )

    result = run_s2d5_learner_limit_audit(config_path)

    assert result["stage"] == "S2D.5_learner_limit_audit_and_representation_v2"
    out = tmp_path / "S2D.5_learner_limit_audit_and_representation_v2"
    assert (out / "phys9_setB" / "failure_pair_audit.json").exists()
    assert (out / "phys9_setB" / "representation_gap_audit.json").exists()
    assert (out / "phys9_setB" / "response_nll_audit.json").exists()
    failure = result["runs"][0]["failure_pair_audit"]
    assert "rx_rz_distinguishable" in failure
    assert "rx_rz_" + "confusion" not in failure
    assert "distinguishable" in failure["rx_rz_distinguishable"]
    assert result["balanced_teacher_profiles"]["phys9_multicircuit_setB_balanced"]["constraint_satisfied"] is True
    rep = result["runs"][0]["representation_gap_audit"]
    assert any(item["feature_space"] == "physical_local_inverse_probability_v2" for item in rep["feature_spaces"])
    assert any(item["feature_space"] == "PHYS3_current_local_inverse_probability_v1" for item in rep["feature_spaces"])
    nll = result["runs"][0]["response_nll_audit"]
    assert "global_mean_NLL" in nll
    assert "calibration_curve" in nll["entries"]["local_inverse"]


def _observations(*, shots: int, num_qubits: int) -> np.ndarray:
    rates = np.array(
        [
            np.linspace(0.02, 0.35, num_qubits),
            np.linspace(0.45, 0.65, num_qubits),
            np.linspace(0.65, 0.35, num_qubits),
        ],
        dtype=np.float64,
    )
    rng = np.random.default_rng(7)
    return (rng.random((3, int(shots), int(num_qubits))) < rates[:, None, :]).astype(np.uint8)
