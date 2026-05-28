from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import yaml

from scope_static.experiments import run_s2d10_generator_space_calibration as runner
from scope_static.physical.generator_space_calibration import (
    GENERATOR_CORE,
    blockwise_decision_metrics,
    effective_rank_metrics,
    grouped_mahalanobis_prototype,
    residualize_by_group,
)


def test_effective_rank_reports_stable_rank_and_angles() -> None:
    jacobian = np.diag([4.0, 2.0, 1.0])
    variants = {"raw_generator_coordinates": np.asarray([[1.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 3.0]])}
    metrics = effective_rank_metrics(jacobian, variants, ["h_XX", "h_YY", "h_ZZ"], ["M10", "M10", "M8"])

    rank = metrics["response_jacobian"]
    assert rank["rank"] == 3
    assert rank["minimum_singular_value"] == 1.0
    assert rank["stable_rank"] == (16.0 + 4.0 + 1.0) / 16.0
    assert "h_XX/h_YY" in rank["column_angles"]


def test_residualize_by_group_removes_group_means() -> None:
    features = np.asarray([[11.0, 0.0], [13.0, 2.0], [-4.0, 6.0], [-2.0, 8.0]])
    residual = residualize_by_group(features, ["a", "a", "b", "b"])

    assert np.allclose(np.mean(residual[:2], axis=0), 0.0)
    assert np.allclose(np.mean(residual[2:], axis=0), 0.0)
    assert np.allclose(residual[0], [-1.0, -1.0])


def test_blockwise_decision_routes_rzz_family_to_physics_blocks() -> None:
    names = list(GENERATOR_CORE)
    rows = np.zeros((4, len(names)), dtype=np.float64)
    labels = ["M8", "M10", "M9", "M12"]
    rows[0, names.index("h_ZZ")] = 2.0
    rows[1, names.index("h_XX")] = 2.0
    rows[2, names.index("gamma_ZZ")] = 2.0
    rows[3, names.index("relaxation_pair")] = 1.0
    rows[3, names.index("nonunital_norm_proxy")] = 1.0

    metrics = blockwise_decision_metrics({"raw_generator_coordinates": rows}, names, labels, [0, 0, 0, 0])
    variant = metrics["variants"]["raw_generator_coordinates"]

    assert variant["stage1_block_accuracy"] == 1.0
    assert variant["stage2_hamiltonian_axis_accuracy"] == 1.0
    assert variant["mechanism_proxy_accuracy"] == 1.0


def test_mahalanobis_prototype_separates_synthetic_generator_signatures() -> None:
    labels = []
    groups = []
    rows = []
    prototypes = {
        "M8": [0.0, 0.0, 4.0, 0.0],
        "M9": [0.0, 0.0, 0.0, 4.0],
        "M10": [4.0, 0.0, 0.0, 0.0],
        "M12": [0.0, 4.0, 0.0, 0.0],
    }
    for group in range(3):
        for label, proto in prototypes.items():
            labels.append(label)
            groups.append(group)
            rows.append(np.asarray(proto, dtype=np.float64) + 0.01 * group)
    metrics = grouped_mahalanobis_prototype(np.asarray(rows), labels, groups)

    assert metrics["available"] is True
    assert metrics["balanced_accuracy"] == 1.0
    assert metrics["per_class_recall"]["M8"] == 1.0


def test_s2d10_runner_writes_required_artifacts_with_fake_s2d9_bundle(tmp_path: Path) -> None:
    source = tmp_path / "S2D.9_local_Pauli_Lindblad_observability"
    source.mkdir()
    (source / "metrics.json").write_text(json.dumps(_fake_s2d9_metrics(), indent=2) + "\n")
    output = tmp_path / "S2D.10_generator_space_calibration_and_nuisance_geometry"
    config = {
        "run": {"output_root": str(tmp_path)},
        "s2d_physical": {"require_gpu": True},
        "s2d10_generator_space_calibration": {
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
    config_path = tmp_path / "s2d10.yaml"
    config_path.write_text(yaml.safe_dump(config))

    result = runner.run_s2d10_generator_space_calibration(config_path)

    assert result["stage"] == "S2D.10_generator_space_calibration_and_nuisance_geometry"
    assert result["source_stage"] == "S2D.9_local_Pauli_Lindblad_observability"
    for name in [
        "metrics.json",
        "summary.md",
        "effective_rank_metrics.json",
        "generator_coordinate_statistics.json",
        "per_mechanism_generator_signatures.json",
        "pairwise_generator_margins.json",
        "circuit_residualization_audit.json",
        "edge_residualization_audit.json",
        "blockwise_decision_metrics.json",
        "mahalanobis_prototype_metrics.json",
        "whitening_ablation_metrics.json",
        "grouped_fold_predictions.json",
        "feature_block_results.json",
        "controls.json",
        "confusion_matrix_by_stage.json",
        "leakage_guardrail_audit.json",
    ]:
        assert (output / name).exists()

    leakage = json.loads((output / "leakage_guardrail_audit.json").read_text())
    assert leakage["runs"]["phys9_multicircuit_setB_balanced"]["passed"] is True


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
            nuisance = 0.2 * float(circuit_id)
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
        values["gamma_ZZ"] = 4.0
    elif label == "M12":
        values["relaxation_pair"] = 2.0
        values["nonunital_norm_proxy"] = 2.0
    return values
