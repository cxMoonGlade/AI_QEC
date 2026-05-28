from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import yaml

from scope_static.experiments import run_s2d10b_generator_invariant_calibration as runner
from scope_static.physical.generator_invariant_calibration import (
    INVARIANT_FEATURES,
    generator_invariants_from_coordinates,
    ptm_unitarity,
)
from scope_static.physical.generator_space_calibration import GENERATOR_CORE


def test_generator_invariants_separate_coherent_and_stochastic_signatures() -> None:
    coherent = generator_invariants_from_coordinates({"h_ZZ": 0.05, "gamma_XX": 0.0, "gamma_YY": 0.0, "gamma_ZZ": 0.0}, r_error=np.eye(16), r_est=np.eye(16))
    stochastic = generator_invariants_from_coordinates({"h_ZZ": 0.0, "gamma_XX": 0.01, "gamma_YY": 0.01, "gamma_ZZ": 0.01}, r_error=_scaled_ptm(0.96), r_est=_scaled_ptm(0.96))

    assert coherent["coherence_norm"] > stochastic["coherence_norm"]
    assert coherent["log_coherence_ratio"] > stochastic["log_coherence_ratio"]
    assert stochastic["stochastic_l1"] > coherent["stochastic_l1"]
    assert stochastic["gamma_isotropy_score"] == 0.0
    assert coherent["unitarity_R_error"] == 1.0
    assert stochastic["unitarity_R_error"] < 1.0


def test_generator_invariants_remain_finite_for_near_zero_error() -> None:
    values = generator_invariants_from_coordinates({}, r_error=np.eye(16), r_est=np.eye(16), eps=1e-9)

    assert set(INVARIANT_FEATURES).issubset(values)
    assert all(np.isfinite(float(value)) for value in values.values())
    assert values["coherence_ratio_capped"] == 0.0


def test_ptm_unitarity_uses_nonidentity_block() -> None:
    assert ptm_unitarity(np.eye(16)) == 1.0
    assert np.isclose(ptm_unitarity(_scaled_ptm(0.9)), 0.81)


def test_s2d10b_runner_writes_required_artifacts_with_fake_s2d9_bundle(tmp_path: Path) -> None:
    source = tmp_path / "S2D.9_local_Pauli_Lindblad_observability"
    source.mkdir()
    (source / "metrics.json").write_text(json.dumps(_fake_s2d9_metrics(), indent=2) + "\n")
    output = tmp_path / "S2D.10b_generator_invariant_calibration"
    config = {
        "run": {"output_root": str(tmp_path)},
        "s2d_physical": {"require_gpu": True},
        "s2d10b_generator_invariant_calibration": {
            "source_root": str(source),
            "output_dir": str(output),
            "permutation_repeats": 2,
            "runs": [
                {"name": "phys9_setA"},
                {"name": "phys9_multicircuit_setB_balanced"},
                {"name": "phys9_multicircuit_setC_balanced"},
            ],
        },
    }
    config_path = tmp_path / "s2d10b.yaml"
    config_path.write_text(yaml.safe_dump(config))

    result = runner.run_s2d10b_generator_invariant_calibration(config_path)

    assert result["stage"] == "S2D.10b_generator_invariant_calibration"
    assert result["source_stage"] == "S2D.9_local_Pauli_Lindblad_observability"
    for name in [
        "metrics.json",
        "summary.md",
        "invariant_feature_manifest.json",
        "invariant_feature_table.json",
        "invariant_ablation_metrics.json",
        "feature_block_results.json",
        "controls.json",
        "features_schema_physics_visible.json",
        "audit_labels_schema_oracle_only.json",
        "leakage_guardrail_audit.json",
    ]:
        assert (output / name).exists()

    manifest = json.loads((output / "invariant_feature_manifest.json").read_text())
    first_run = manifest["runs"]["phys9_multicircuit_setB_balanced"]
    assert first_run["no_new_probe_sampling"] is True
    assert all(feature["uses_exact_teacher_channel"] is False for feature in first_run["features"])
    leakage = json.loads((output / "leakage_guardrail_audit.json").read_text())
    assert leakage["runs"]["phys9_multicircuit_setB_balanced"]["passed"] is True


def _scaled_ptm(scale: float) -> np.ndarray:
    matrix = np.eye(16, dtype=np.float64)
    matrix[1:, 1:] *= float(scale)
    return matrix


def _fake_s2d9_metrics() -> dict[str, object]:
    return {
        "stage": "S2D.9_local_Pauli_Lindblad_observability",
        "records": [
            _fake_run_record("phys9_setA", ["M8", "M9", "M10"]),
            _fake_run_record("phys9_multicircuit_setB_balanced", ["M8", "M9", "M10"]),
            _fake_run_record("phys9_multicircuit_setC_balanced", ["M8", "M9", "M10", "M12"]),
        ],
    }


def _fake_run_record(name: str, labels: list[str]) -> dict[str, object]:
    feature_names = [*GENERATOR_CORE, "delta_norm", "logm_delta_norm"]
    records = []
    ptm_records = []
    location_id = 0
    for circuit_id in range(3):
        for label in labels:
            features = _mechanism_features(label)
            nuisance = 0.02 * float(circuit_id)
            features = {key: float(value + nuisance) for key, value in features.items()}
            scrambled = {key: 0.01 * float((idx + circuit_id) % 3) for idx, key in enumerate(feature_names)}
            records.append(
                {
                    "location_id": location_id,
                    "oracle_label_evaluator_only": label,
                    "circuit_id": circuit_id,
                    "features": {key: float(features.get(key, 0.0)) for key in feature_names},
                    "scrambled_features": scrambled,
                }
            )
            ptm_records.append(
                {
                    "location_id": location_id,
                    "qubits": [2 * (location_id % 4), 2 * (location_id % 4) + 1],
                    "circuit_id": circuit_id,
                    "R_error": _ptm_for_label(label).tolist(),
                    "R_est": _ptm_for_label(label).tolist(),
                }
            )
            location_id += 1
    return {
        "name": name,
        "profile": "phys9_chain",
        "mechanism_set": "set_C" if "setC" in name else "set_B",
        "response_jacobian_json": {"matrix": np.eye(len(GENERATOR_CORE)).tolist()},
        "generator_coordinate_estimates": {
            "coordinate_names": feature_names,
            "records": records,
        },
        "ptm_block_reconstruction": {"records": ptm_records},
    }


def _mechanism_features(label: str) -> dict[str, float]:
    values = {key: 0.0 for key in GENERATOR_CORE}
    if label == "M8":
        values["h_ZZ"] = 4.0
    elif label == "M10":
        values["h_XX"] = 3.0
        values["h_YY"] = 2.0
    elif label == "M9":
        values["gamma_XX"] = 1.0
        values["gamma_YY"] = 1.0
        values["gamma_ZZ"] = 1.0
    elif label == "M12":
        values["relaxation_pair"] = 2.0
        values["nonunital_norm_proxy"] = 2.0
    return values


def _ptm_for_label(label: str) -> np.ndarray:
    if label in {"M8", "M10"}:
        return np.eye(16)
    if label == "M9":
        return _scaled_ptm(0.93)
    if label == "M12":
        matrix = _scaled_ptm(0.88)
        matrix[1, 0] = 0.08
        return matrix
    return np.eye(16)
