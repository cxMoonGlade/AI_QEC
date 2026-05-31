from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pytest
import stim
import torch

from scope_static.google.set1 import (
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
from scope_static.dem.metrics import adjusted_rand_index, normalized_mutual_info, partition_comparison
from scope_static.dem.fault_graph import FaultGraph
from scope_static.dem.baselines import baseline_metadata
from scope_static.dem.prepared_graph_store import (
    load_prepared_fault_graph_cache,
    prepared_fault_graph_cache_file,
    prepared_fault_graph_cache_key,
    save_prepared_fault_graph_cache,
)


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


def test_prepared_fault_graph_cache_round_trips_stage1_contract(tmp_path: Path):
    graph = FaultGraph.from_raw_masks(
        torch.tensor([[1, 0, 1], [0, 1, 1], [0, 0, 1]], dtype=torch.bool),
        num_detectors=2,
        num_observables=1,
        residual_rank=1,
        canonicalize_duplicate_masks=True,
    )
    audit = {"preprocessing_mode": "fault_graph_heuristic", "B": graph.B, "M_effective": graph.M}
    key = prepared_fault_graph_cache_key({"case": "tiny", "residual_rank": graph.residual_rank})
    path = prepared_fault_graph_cache_file(tmp_path, key)

    save_prepared_fault_graph_cache(path, key=key, graph=graph, audit=audit, metadata={"case": "tiny"})
    loaded = load_prepared_fault_graph_cache(path, expected_key=key)

    assert loaded.status == "hit"
    assert loaded.audit == audit
    assert loaded.metadata == {"case": "tiny"}
    assert loaded.graph is not None
    assert torch.equal(loaded.graph.A, graph.A)
    assert loaded.graph.supports_by_fault == graph.supports_by_fault
    assert loaded.graph.faults_by_observation_bit == graph.faults_by_observation_bit
    assert torch.equal(loaded.graph.orbit_ids, graph.orbit_ids)
    assert torch.equal(loaded.graph.residual_features, graph.residual_features)
    assert loaded.graph.residual_feature_audit_dict() == graph.residual_feature_audit_dict()
    assert load_prepared_fault_graph_cache(path, expected_key="wrong").status == "key_mismatch"


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
    from scope_static.experiments.willow_data.static import main

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


def test_google_runner_rejects_cpu_fallback(monkeypatch, tmp_path: Path):
    from scope_static.experiments.willow_data.static import main

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

    with pytest.raises(SystemExit):
        main([*base_args, "--allow-cpu-fallback", "--output-dir", str(tmp_path / "cpu")])


def test_google_runner_can_evaluate_discovery_on_real_data_path(monkeypatch, tmp_path: Path, capsys):
    from scope_static.experiments.willow_data.static import main

    if not torch.cuda.is_available():
        pytest.skip("Google workflows require CUDA")
    root = _write_tiny_dataset(tmp_path)

    result = main(
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
            "local,disc_hard",
            "--orbit-modes",
            "fault_graph_heuristic",
            "--discovery-restarts",
            "2",
            "--discovery-prototype-counts",
            "O",
            "--output-dir",
            str(tmp_path / "disc_google"),
        ]
    )
    disc = next(record for record in result["records"] if record["base_model"] == "disc_hard")
    assert result["run"]["stage2b_google_discovery_external_validation"] is True
    assert disc["stage"] == "stage2B_google_external_validation"
    assert disc["google_true_hidden_partition_available"] is False
    assert disc["partition_recovery_claim_allowed"] is False
    assert disc["partition_recovery_ground_truth_available"] is False
    assert disc["prototype_count_K"] == disc["O"]
    assert disc["P_discovery_assignment"] == disc["M_effective"] * (disc["O"] - 1)
    assert disc["compressed_claim_allowed"] is False
    assert disc["discovery_num_restarts"] == 2
    assert len(disc["discovery_restart_outcomes"]) == 2

    output = capsys.readouterr().out
    assert "S2B Google static discovery validation complete" in output
    assert "disc_hard" in output


def test_google_local_mechanism_smoke_uses_proxy_not_true_recovery(monkeypatch, tmp_path: Path):
    from scope_static.experiments.willow_data.local_mechanism import main

    if not torch.cuda.is_available():
        pytest.skip("Google workflows require CUDA")
    root = _write_tiny_dataset(tmp_path)

    result = main(
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
            "--subsample-count",
            "1",
            "--subsample-shots",
            "1",
            "--subsample-steps",
            "1",
            "--nmf-steps",
            "2",
            "--pca-ranks",
            "1",
            "--output-root",
            str(tmp_path / "google_static"),
        ]
    )

    g15 = result["GDISC15_real_local_mechanism_discovery"]
    assert g15["true_hidden_omega_available"] is False
    assert g15["ari_nmi_ground_truth_recovery_claim_allowed"] is False
    assert any(record["model"] == "dmle_qec" for record in g15["records"])
    assert "proxy_support_size" in g15["proxy_partitions"]
    assert (tmp_path / "google_static" / "GDISC13b_real_local_inverse_audit" / "metrics.json").exists()
    assert (tmp_path / "google_static" / "GDISC15_real_local_mechanism_discovery" / "metrics.json").exists()
    assert (tmp_path / "google_static" / "STIM_vs_Google_comparison" / "summary.md").exists()


def test_google_gdisc15b_grid_writes_paired_summary(monkeypatch, tmp_path: Path):
    from scope_static.experiments.willow_data.gdisc15b_grid import main

    if not torch.cuda.is_available():
        pytest.skip("Google workflows require CUDA")
    root = _write_tiny_dataset(tmp_path)

    result = main(
        [
            "--dataset-root",
            str(root),
            "--native-gpu",
            "--samples",
            "sample_00",
            "--patches",
            "d3_at_q5_5",
            "--bases",
            "X",
            "--rounds-labels",
            "r13",
            "--heldout-split-types",
            "shot-heldout",
            "--train-shots",
            "2",
            "--heldout-shots",
            "1",
            "--max-windows",
            "1",
            "--steps",
            "1",
            "--subsample-count",
            "1",
            "--subsample-shots",
            "1",
            "--subsample-steps",
            "1",
            "--nmf-steps",
            "2",
            "--pca-ranks",
            "1",
            "--random-control-ranks",
            "1",
            "--output-dir",
            str(tmp_path / "grid"),
        ]
    )

    assert result["run"]["name"] == "GDISC15b_google_grid_validation"
    assert len(result["grid"]["completed_contexts"]) == 1
    models = {row["model"] for row in result["model_summary"]}
    assert "local_full" in models
    assert "dmle_qec" in models
    assert "global_shared_scalar" in models
    assert any(model.startswith("GDISC15_random_low_rank1") for model in models)
    assert (tmp_path / "grid" / "metrics.json").exists()
    assert (tmp_path / "grid" / "summary.md").read_text().count("wins/total") == 1


def test_google_s3e_external_validation_wraps_grid_acceptance(monkeypatch, tmp_path: Path):
    from scope_static.experiments.willow_data.s3e_external_validation import main

    if not torch.cuda.is_available():
        pytest.skip("Google workflows require CUDA")
    root = _write_tiny_dataset(tmp_path)

    result = main(
        [
            "--dataset-root",
            str(root),
            "--samples",
            "sample_00",
            "--patches",
            "d3_at_q5_5",
            "--bases",
            "X",
            "--rounds-labels",
            "r13",
            "--heldout-split-types",
            "shot-heldout",
            "--train-shots",
            "2",
            "--heldout-shots",
            "1",
            "--max-windows",
            "1",
            "--steps",
            "1",
            "--subsample-count",
            "1",
            "--subsample-shots",
            "1",
            "--subsample-steps",
            "1",
            "--nmf-steps",
            "2",
            "--pca-ranks",
            "1",
            "--random-control-ranks",
            "1",
            "--min-contexts",
            "1",
            "--min-compression-ratio",
            "0.0",
            "--near-local-excess-tolerance",
            "10.0",
            "--min-random-control-margin",
            "-10.0",
            "--output-dir",
            str(tmp_path / "s3e"),
        ]
    )

    assert result["run"]["name"] == "S3E_google_external_validation"
    assert result["acceptance"]["checks"]["true_hidden_omega_claim"]["value"] is False
    assert result["acceptance"]["checks"]["contexts_completed"]["passed"] is True
    assert result["acceptance"]["best_compressed_model"]["model"].startswith("GDISC15_")
    assert (tmp_path / "s3e" / "acceptance.json").exists()
    assert (tmp_path / "s3e" / "GDISC15b_grid" / "metrics.json").exists()


def test_google_xz_scorecard_is_gpu_only_and_writes_label_manifest(monkeypatch, tmp_path: Path):
    from scope_static.experiments.willow_data import xz_scorecard

    def fake_grid_main(argv):
        assert "--native-gpu" in argv
        assert "--allow-cpu-fallback" not in argv
        output = Path(argv[argv.index("--output-dir") + 1])
        contexts = []
        flat_records = []
        for basis in ["X", "Z"]:
            context = {
                "heldout_split_type": "shot-heldout",
                "sample_id": "sample_00",
                "patch_id": "d3_at_q5_5",
                "basis": basis,
                "rounds_label": "r13",
                "output_root": str(output / f"ctx_{basis}"),
            }
            metrics_dir = Path(context["output_root"]) / "GDISC15_real_local_mechanism_discovery"
            metrics_dir.mkdir(parents=True, exist_ok=True)
            (metrics_dir / "metrics.json").write_text(
                json.dumps({"run": {"device": "cuda", "likelihood_backend": "cuda_extension", "cuda_kernel_variant": "dp"}})
            )
            contexts.append(context)
            flat_records.extend(
                [
                    _scorecard_record(context, "local_full", 100, 0.50, 0.010),
                    _scorecard_record(context, "dmle_qec", 100, 0.58, 0.012),
                    _scorecard_record(context, "global_shared_scalar", 1, 0.90, 0.030),
                    _scorecard_record(context, "SI1000_prior_reference", 0, 0.65, 0.020),
                    _scorecard_record(context, "GDISC15_local_logit", 10, 0.51, 0.009),
                    _scorecard_record(context, "GDISC15_random_low_rank1_seed0", 10, 0.75, 0.020),
                ]
            )
        return {
            "grid": {"completed_contexts": contexts, "skipped_contexts": []},
            "flat_records": flat_records,
            "model_summary": [],
        }

    monkeypatch.setattr(xz_scorecard.gdisc15b_grid, "main", fake_grid_main)
    result = xz_scorecard.main(
        [
            "--config",
            str(tmp_path / "missing.yaml"),
            "--dataset-root",
            str(_write_tiny_dataset(tmp_path)),
            "--samples",
            "sample_00",
            "--patches",
            "d3_at_q5_5",
            "--bases",
            "X,Z",
            "--rounds-labels",
            "r13",
            "--min-contexts",
            "2",
            "--output-dir",
            str(tmp_path / "xz"),
        ]
    )

    assert result["run"]["name"] == "Google_XZ_scorecard"
    assert result["scorecard"]["google_xz_scorecard_passed"] is True
    assert {row["basis"] for row in result["scorecard"]["basis_summary"]} == {"X", "Z"}
    assert all(row["best_baseline_model_counts"] == {"dmle_qec": 1} for row in result["scorecard"]["basis_summary"])
    assert all(row["compressed_minus_best_baseline_excess_nll_mean"] < 0 for row in result["scorecard"]["basis_summary"])
    for row in result["scorecard"]["context_scorecard"]:
        assert row["best_baseline"]["baseline_variant"] == "scope_static_dmle_qec_style_independent_dem_mle"
        assert row["best_baseline"]["upstream_dmle_qec_complete_implementation"] is False
    assert result["scorecard"]["label_manifest"]["label_layers"]["forbidden_true_labels"]
    assert (tmp_path / "xz" / "context_scorecard.json").exists()
    assert (tmp_path / "xz" / "label_manifest.json").exists()


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

    from scope_static.experiments.willow_data.static import main

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


def _scorecard_record(context: dict[str, object], model: str, params: int, nll: float, detector_mae: float):
    metadata = baseline_metadata(model) if model == "dmle_qec" else {}
    return {
        **context,
        "model": model,
        "parameter_count": params,
        "compression_ratio": None,
        "heldout_local_window_nll": nll,
        "heldout_local_window_excess_nll": nll,
        "detector_rate_mae": detector_mae,
        "local_correlation_error": detector_mae / 2,
        "logical_flip_rate_calibration": detector_mae / 3,
        **metadata,
    }


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
