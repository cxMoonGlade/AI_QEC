from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pytest
import stim
import torch

from scope_static.google_set1 import (
    DATASET_NAME,
    GoogleScheduleContext,
    build_google_fault_graph,
    build_google_schedule_context,
    find_google_set1_leaf,
    iter_google_set1_leaves,
    load_google_observations,
    normalize_google_set1_root,
    provenance_audit,
    schedule_geometric_orbit_ids,
)
from scope_static.metrics import adjusted_rand_index, normalized_mutual_info, partition_comparison
from scope_static.fault_graph import FaultGraph


def test_root_normalization_accepts_outer_and_nested_and_requires_sample_00(tmp_path: Path):
    outer = tmp_path / DATASET_NAME
    nested = outer / DATASET_NAME
    (nested / "sample_00").mkdir(parents=True)

    assert normalize_google_set1_root(outer) == nested.resolve()
    assert normalize_google_set1_root(nested) == nested.resolve()

    with pytest.raises(ValueError, match="sample_00"):
        normalize_google_set1_root(tmp_path / "missing")


def test_google_leaf_enumeration_and_default_leaf_parsing(tmp_path: Path):
    root = _write_tiny_dataset(tmp_path)
    leaves = iter_google_set1_leaves(root)
    assert len(leaves) == 1

    leaf = find_google_set1_leaf(root)
    assert leaf.sample_id == "sample_00"
    assert leaf.patch_id == "d3_at_q5_5"
    assert leaf.basis == "X"
    assert leaf.rounds == 13


def test_b8_observation_loading_shape_and_dtype(tmp_path: Path):
    root = _write_tiny_dataset(tmp_path)
    observations = load_google_observations(find_google_set1_leaf(root))
    assert observations.shape == (4, 2)
    assert observations.dtype == torch.bool
    assert observations[:, 0].tolist() == [False, True, False, True]


def test_dem_to_fault_graph_construction(tmp_path: Path):
    root = _write_tiny_dataset(tmp_path)
    graph, audit = build_google_fault_graph(find_google_set1_leaf(root), orbit_mode="fault_graph_heuristic")
    assert graph.B == 2
    assert graph.M == 2
    assert audit["M_raw"] == 2
    assert audit["M_effective"] == 2
    assert audit["dem_fault_to_schedule_provenance"]["available"] in {"partial", "false"}


def test_google_schedule_context_coverage_audit_on_tiny_stim_fixture(tmp_path: Path):
    root = _write_tiny_dataset(tmp_path)
    leaf = find_google_set1_leaf(root)
    observations = load_google_observations(leaf)
    context = build_google_schedule_context(leaf, observations=observations)
    audit = context.coverage_audit
    assert audit["num_qubits_parsed"] == 2
    assert audit["num_data_qubits"] == 1
    assert audit["num_measure_qubits"] == 1
    assert audit["num_TICK_layers"] >= 2
    assert audit["num_measurement_operations"] == 1
    assert audit["num_reset_operations"] >= 1
    assert audit["num_detectors_parsed"] == 1
    assert audit["num_logical_observables_parsed"] == 1
    assert audit["detector_count_matches_detection_events_b8_bits_per_shot"] is True
    assert audit["observable_count_matches_obs_flips_actual_b8_bits_per_shot"] is True


def test_provenance_audit_emits_false_partial_and_full_states(tmp_path: Path):
    graph = FaultGraph.from_raw_masks(
        torch.tensor([[1, 0], [0, 1]], dtype=torch.bool),
        num_detectors=2,
        num_observables=0,
        residual_rank=0,
        detector_coordinates=torch.tensor([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]),
    )
    false_audit = provenance_audit(graph)["dem_fault_to_schedule_provenance"]
    assert false_audit["available"] == "false"

    partial_context = _manual_context(center=(0.5, 0.0), qubit_coords=[(0.0, 0.0), (1.0, 0.0)])
    partial_audit = provenance_audit(graph, partial_context)["dem_fault_to_schedule_provenance"]
    assert partial_audit["available"] == "partial"

    full_audit = provenance_audit(
        graph,
        partial_context,
        available_override="full",
        provenance_source_override="circuit annotations",
    )["dem_fault_to_schedule_provenance"]
    assert full_audit["available"] == "full"
    assert full_audit["provenance_source"] == "circuit annotations"


def test_symmetry_validation_emits_nontrivial_identity_only_and_invalid():
    nontrivial_graph = FaultGraph.from_raw_masks(
        torch.tensor([[1, 0], [0, 1]], dtype=torch.bool),
        num_detectors=2,
        num_observables=0,
        residual_rank=0,
        detector_coordinates=torch.tensor([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]),
    )
    nontrivial_context = _manual_context(center=(0.0, 0.0), qubit_coords=[(-1.0, 0.0), (1.0, 0.0)])
    orbit_ids, audit = schedule_geometric_orbit_ids(nontrivial_graph, nontrivial_context)
    assert audit["schedule_symmetry_status"] == "nontrivial"
    assert orbit_ids.tolist() == [0, 0]

    identity_graph = FaultGraph.from_raw_masks(
        torch.tensor([[1, 0], [0, 1]], dtype=torch.bool),
        num_detectors=2,
        num_observables=0,
        residual_rank=0,
        detector_coordinates=torch.tensor([[0.0, 0.0, 0.0], [2.0, 0.0, 0.0]]),
    )
    identity_context = _manual_context(center=(0.0, 0.0), qubit_coords=[(0.0, 0.0), (2.0, 0.0)])
    _, identity_audit = schedule_geometric_orbit_ids(identity_graph, identity_context)
    assert identity_audit["schedule_symmetry_status"] == "identity_only"

    invalid_graph = FaultGraph.from_raw_masks(
        torch.tensor([[1, 0], [0, 1]], dtype=torch.bool),
        num_detectors=2,
        num_observables=0,
        residual_rank=0,
    )
    _, invalid_audit = schedule_geometric_orbit_ids(invalid_graph, identity_context)
    assert invalid_audit["schedule_symmetry_status"] == "invalid"


def test_partition_metrics_on_known_partitions():
    heuristic = [0, 0, 1, 1]
    same = [1, 1, 0, 0]
    refined = [0, 1, 2, 3]
    assert adjusted_rand_index(heuristic, same) == pytest.approx(1.0)
    assert normalized_mutual_info(heuristic, same) == pytest.approx(1.0)
    comparison = partition_comparison(heuristic, refined)
    assert comparison["schedule_refines_heuristic"] is True
    assert comparison["heuristic_refines_schedule"] is False


def test_google_runner_native_gpu_requires_visible_cuda(monkeypatch, tmp_path: Path):
    from scope_static.experiments.run_google_static import main

    root = _write_tiny_dataset(tmp_path)
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)

    with pytest.raises(RuntimeError, match="native GPU"):
        main(
            [
                "--dataset-root",
                str(root),
                "--native-gpu",
                "--train-shots",
                "2",
                "--heldout-shots",
                "1",
                "--max-windows",
                "1",
                "--steps",
                "1",
                "--models",
                "hard_orbit",
                "--orbit-modes",
                "fault_graph_heuristic",
                "--output-dir",
                str(tmp_path / "out"),
            ]
        )


def test_google_runner_is_gpu_first_and_requires_explicit_cpu_fallback(monkeypatch, tmp_path: Path):
    from scope_static.experiments.run_google_static import main

    root = _write_tiny_dataset(tmp_path)
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)

    base_args = [
        "--dataset-root",
        str(root),
        "--train-shots",
        "2",
        "--heldout-shots",
        "1",
        "--max-windows",
        "1",
        "--steps",
        "1",
        "--models",
        "hard_orbit",
        "--orbit-modes",
        "fault_graph_heuristic",
    ]
    with pytest.raises(RuntimeError, match="GPU-first"):
        main([*base_args, "--output-dir", str(tmp_path / "blocked")])

    result = main([*base_args, "--allow-cpu-fallback", "--output-dir", str(tmp_path / "cpu")])
    assert result["run"]["gpu_policy"] == "cpu_fallback_explicit"
    assert result["run"]["device"] == "cpu"


@pytest.mark.skipif(not os.environ.get("SCOPE_GOOGLE_SET1_ROOT"), reason="requires Google Set1 dataset")
def test_google_set1_gated_default_leaf_and_tiny_smoke(tmp_path: Path):
    root = os.environ["SCOPE_GOOGLE_SET1_ROOT"]
    leaves = iter_google_set1_leaves(root)
    assert len(leaves) == 3780

    leaf = find_google_set1_leaf(root)
    observations = load_google_observations(leaf)
    assert tuple(observations.shape) == (50000, 105)

    graph, _ = build_google_fault_graph(leaf, dem_source="decoder_si1000", orbit_mode="fault_graph_heuristic")
    assert graph.B == 105

    from scope_static.experiments.run_google_static import main

    result = main(
        [
            "--dataset-root",
            root,
            "--train-shots",
            "256",
            "--heldout-shots",
            "256",
            "--max-windows",
            "8",
            "--steps",
            "2",
            "--models",
            "hard_orbit",
            "--orbit-modes",
            "fault_graph_heuristic,schedule_geometric",
            "--skip-cross-sample-transfer",
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )
    assert len(result["records"]) == 2


def _write_tiny_dataset(tmp_path: Path) -> Path:
    root = tmp_path / DATASET_NAME / DATASET_NAME
    leaf = root / "sample_00" / "d3_at_q5_5" / "X" / "r13"
    decoder = leaf / "decoding_results" / "correlated_matching_decoder_with_si1000_prior"
    decoder.mkdir(parents=True)
    circuit = stim.Circuit(
        """
        QUBIT_COORDS(0, 0) 0
        QUBIT_COORDS(1, 0) 1
        R 0 1
        TICK
        CX sweep[0] 0
        TICK
        M 0
        DETECTOR(0, 0, 0) rec[-1]
        OBSERVABLE_INCLUDE(0) rec[-1]
        """
    )
    leaf.mkdir(parents=True, exist_ok=True)
    (leaf / "circuit_ideal.stim").write_text(str(circuit), encoding="utf-8")
    (leaf / "circuit_noisy_si1000.stim").write_text(str(circuit), encoding="utf-8")
    metadata = {
        "basis": "X",
        "distance": 3,
        "rounds": 13,
        "shots": 4,
        "data_qubit_coords": [[0, 0]],
        "meas_qubit_coords": [[1, 0]],
    }
    (leaf / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    _write_b8(leaf / "detection_events.b8", [[0], [1], [0], [1]])
    _write_b8(leaf / "obs_flips_actual.b8", [[0], [0], [1], [1]])
    _write_b8(leaf / "measurements.b8", [[0], [1], [1], [0]])
    _write_b8(leaf / "sweep_bits.b8", [[0], [1], [0], [1]])
    _write_b8(decoder / "obs_flips_predicted.b8", [[0], [1], [1], [0]])
    (decoder / "error_model.dem").write_text("error(0.1) D0\nerror(0.2) D0 L0\n", encoding="utf-8")
    return tmp_path / DATASET_NAME


def _write_b8(path: Path, rows: list[list[int]]) -> None:
    data = np.array(rows, dtype=np.bool_)
    stim.write_shot_data_file(path=str(path), data=data, format="b8", num_measurements=data.shape[1])


def _manual_context(center: tuple[float, float], qubit_coords: list[tuple[float, float]]) -> GoogleScheduleContext:
    qubits = [
        {"index": idx, "coords": [x, y], "role": "data", "boundary_role": None}
        for idx, (x, y) in enumerate(qubit_coords)
    ]
    return GoogleScheduleContext(
        h_sched={
            "hardware_layout": {
                "qubits": qubits,
                "patch_center": [center[0], center[1]],
            }
        },
        u={},
        kappa={},
        tau={},
        coverage_audit={},
        claim_boundary={},
    )
