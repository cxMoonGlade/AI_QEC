from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import stim

from scope_static.google.inventory import (
    DATASET_105Q,
    DATASET_NAMES,
    DATASET_REPETITION_D29,
    DATASET_SURFACE_SET1,
    DATASET_SURFACE_SET2,
    DEFAULT_DATASET_ROOTS,
    EXPECTED_LEAF_COUNTS,
    FORBIDDEN_TRUE_LABELS,
    decoder_pathways_for_leaf,
    extract_dem_proxy_labels,
    iter_google_leaves,
    load_context_manifest,
    load_decoder_manifest,
    observation_shape_audit,
    write_google_inventory_artifacts,
)


def test_unified_inventory_writes_all_four_tiny_dataset_artifacts(tmp_path: Path):
    roots = _write_tiny_google_roots(tmp_path)
    result = write_google_inventory_artifacts(
        output_dir=tmp_path / "inventory",
        dataset_roots=roots,
        dataset_names=DATASET_NAMES,
        dem_proxy_mode="all",
    )

    contexts = load_context_manifest(result["context_manifest_path"])
    decoders = load_decoder_manifest(result["decoder_manifest_path"])
    labels = json.loads(Path(result["label_manifest_path"]).read_text())
    audit = json.loads(Path(result["audit_path"]).read_text())

    assert len(contexts) == 4
    assert {row["dataset_name"] for row in contexts} == set(DATASET_NAMES)
    repetition = next(row for row in contexts if row["dataset_name"] == DATASET_REPETITION_D29)
    surface_105q = next(row for row in contexts if row["dataset_name"] == DATASET_105Q)
    assert repetition["patch_id"] is None
    assert repetition["rounds"] == 1000
    assert repetition["rounds_label"] == "r1000"
    assert surface_105q["sample_id"] is None
    assert surface_105q["sample_index"] is None

    libra = [
        row
        for row in decoders
        if row["dataset_name"] == DATASET_105Q and row["pathway_name"] == "libra_decoder_with_rl_optimized_prior"
    ]
    assert len(libra) == 1
    assert libra[0]["available_dem"] is False
    assert libra[0]["available_predictions"] is False
    assert any(row.get("dem_proxy_labels", {}).get("available") is True for row in decoders)
    assert labels["label_layers"]["forbidden_true_labels"] == list(FORBIDDEN_TRUE_LABELS)
    assert audit["datasets"][DATASET_REPETITION_D29]["num_leaves"] == 1


def test_observation_shape_and_dem_proxy_on_tiny_leaf(tmp_path: Path):
    roots = _write_tiny_google_roots(tmp_path)
    leaf = iter_google_leaves(roots[DATASET_SURFACE_SET1], DATASET_SURFACE_SET1)[0]
    shape = observation_shape_audit(leaf)
    pathway = decoder_pathways_for_leaf(leaf)[0]
    proxy = extract_dem_proxy_labels(
        pathway.error_model_path,
        dataset_name=leaf.dataset_name,
        context_id=leaf.context_id,
        pathway_name=pathway.pathway_name,
    )

    assert shape["shot_count_matches"] is True
    assert shape["detector_count_matches"] is True
    assert shape["observable_count_matches"] is True
    assert proxy["proxy_label_only"] is True
    assert proxy["fault_count"] == 2
    assert proxy["touches_logical_count"] == 1
    assert proxy["forbidden_true_labels_absent"] is True


def test_gdisc15b_manifest_context_selection_records_decoder_skips(tmp_path: Path):
    from scope_static.experiments.willow_data import gdisc15b_grid

    roots = _write_tiny_google_roots(tmp_path)
    inventory = write_google_inventory_artifacts(
        output_dir=tmp_path / "inventory",
        dataset_roots=roots,
        dataset_names=(DATASET_SURFACE_SET1,),
        dem_proxy_mode="none",
    )

    args = gdisc15b_grid._parse_args(
        [
            "--dataset-root",
            str(roots[DATASET_SURFACE_SET1]),
            "--context-manifest",
            inventory["context_manifest_path"],
            "--decoder-manifest",
            inventory["decoder_manifest_path"],
            "--dataset-name",
            DATASET_SURFACE_SET1,
            "--samples",
            "sample_00",
            "--patches",
            "d3_at_q5_5",
            "--bases",
            "X",
            "--rounds-labels",
            "r13",
            "--decoder-pathway",
            "correlated_matching_decoder_with_si1000_prior",
        ]
    )
    contexts = gdisc15b_grid._context_specs(args)
    assert len(contexts) == 1
    assert contexts[0]["dataset_name"] == DATASET_SURFACE_SET1
    assert contexts[0]["decoder_pathway"] == "correlated_matching_decoder_with_si1000_prior"
    assert contexts[0].get("skip_reason") is None

    missing_args = gdisc15b_grid._parse_args(
        [
            "--dataset-root",
            str(roots[DATASET_SURFACE_SET1]),
            "--context-manifest",
            inventory["context_manifest_path"],
            "--decoder-manifest",
            inventory["decoder_manifest_path"],
            "--dataset-name",
            DATASET_SURFACE_SET1,
            "--decoder-pathway",
            "not_a_decoder",
        ]
    )
    skipped = gdisc15b_grid._context_specs(missing_args)
    assert skipped[0]["skip_reason"] == "decoder_pathway_not_in_manifest"


@pytest.mark.skipif(
    not all(root.exists() for root in DEFAULT_DATASET_ROOTS.values()),
    reason="requires local Google datasets under /home/cx/Document",
)
def test_google_inventory_actual_leaf_counts_match_observed_datasets():
    for dataset_name, expected_count in EXPECTED_LEAF_COUNTS.items():
        leaves = iter_google_leaves(DEFAULT_DATASET_ROOTS[dataset_name], dataset_name)
        assert len(leaves) == expected_count
        assert all(all(path.is_file() for path in leaf.required_files().values()) for leaf in leaves)


@pytest.mark.skipif(
    not DEFAULT_DATASET_ROOTS[DATASET_105Q].exists(),
    reason="requires local Google 105Q dataset",
)
def test_google_105q_libra_missing_outputs_are_inventory_missing_data():
    leaves = iter_google_leaves(DEFAULT_DATASET_ROOTS[DATASET_105Q], DATASET_105Q)
    rows = [pathway for leaf in leaves for pathway in decoder_pathways_for_leaf(leaf)]
    libra = [row for row in rows if row.pathway_name == "libra_decoder_with_rl_optimized_prior"]
    assert len(leaves) == 420
    assert len(libra) == 420
    assert sum(1 for row in libra if row.available_predictions) == 364
    assert sum(1 for row in libra if not row.available_predictions) == 56


def _write_tiny_google_roots(tmp_path: Path) -> dict[str, Path]:
    roots = {
        DATASET_REPETITION_D29: tmp_path / DATASET_REPETITION_D29,
        DATASET_SURFACE_SET1: tmp_path / DATASET_SURFACE_SET1 / DATASET_SURFACE_SET1,
        DATASET_SURFACE_SET2: tmp_path / DATASET_SURFACE_SET2 / DATASET_SURFACE_SET2,
        DATASET_105Q: tmp_path / DATASET_105Q / DATASET_105Q,
    }
    _write_leaf(
        roots[DATASET_REPETITION_D29] / "X" / "sample_00",
        metadata={"basis": "X", "distance": 29, "cycles": 1000, "shots": 4},
        decoder_names=("MWPM_decoder_with_RL_optimized_prior",),
    )
    (roots[DATASET_REPETITION_D29] / "Z").mkdir(parents=True, exist_ok=True)
    _write_leaf(
        roots[DATASET_SURFACE_SET1] / "sample_00" / "d3_at_q5_5" / "X" / "r13",
        metadata={"basis": "X", "distance": 3, "rounds": 13, "shots": 4},
        decoder_names=(
            "correlated_matching_decoder_with_si1000_prior",
            "correlated_matching_decoder_with_rl_optimized_prior",
            "harmony_decoder_with_si1000_prior",
            "harmony_decoder_with_rl_optimized_prior",
        ),
    )
    _write_leaf(
        roots[DATASET_SURFACE_SET2] / "sample_00" / "d3_at_q5_5" / "Z" / "r13",
        metadata={"basis": "Z", "distance": 3, "rounds": 13, "shots": 4},
        decoder_names=(
            "belief_matching_decoder_with_prior_from_detector_correlations",
            "belief_matching_decoder_with_rl_optimized_prior",
            "belief_matching_decoder_with_uninformative_prior",
            "correlated_matching_decoder_with_prior_from_detector_correlations",
            "correlated_matching_decoder_with_rl_optimized_prior",
            "correlated_matching_decoder_with_uninformative_prior",
            "harmony_decoder_with_prior_from_detector_correlations",
            "harmony_decoder_with_rl_optimized_prior",
            "harmony_decoder_with_uninformative_prior",
        ),
    )
    _write_leaf(
        roots[DATASET_105Q] / "d3_at_q4_5" / "X" / "r13",
        metadata={"basis": "X", "distance": 3, "rounds": 13, "shots": 4},
        decoder_names=(
            "correlated_matching_decoder_with_si1000_prior",
            "correlated_matching_decoder_with_rl_optimized_prior",
            "harmony_decoder_with_si1000_prior",
            "harmony_decoder_with_rl_optimized_prior",
        ),
    )
    return roots


def _write_leaf(path: Path, *, metadata: dict[str, object], decoder_names: tuple[str, ...]) -> None:
    path.mkdir(parents=True, exist_ok=True)
    circuit = stim.Circuit(
        """
        QUBIT_COORDS(0, 0) 0
        R 0
        TICK
        X_ERROR(0.1) 0
        M 0
        DETECTOR(0, 0, 0) rec[-1]
        OBSERVABLE_INCLUDE(0) rec[-1]
        """
    )
    (path / "circuit_ideal.stim").write_text(str(circuit), encoding="utf-8")
    (path / "circuit_noisy_si1000.stim").write_text(str(circuit), encoding="utf-8")
    (path / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    _write_b8(path / "detection_events.b8", [[0], [1], [0], [1]])
    _write_b8(path / "obs_flips_actual.b8", [[0], [0], [1], [1]])
    _write_b8(path / "measurements.b8", [[0], [1], [1], [0]])
    _write_b8(path / "sweep_bits.b8", [[0], [0], [0], [0]])
    for decoder_name in decoder_names:
        decoder = path / "decoding_results" / decoder_name
        decoder.mkdir(parents=True, exist_ok=True)
        (decoder / "error_model.dem").write_text(
            "error(0.1) D0\nerror(0.2) D0 L0\n",
            encoding="utf-8",
        )
        _write_b8(decoder / "obs_flips_predicted.b8", [[0], [1], [1], [0]])


def _write_b8(path: Path, rows: list[list[int]]) -> None:
    data = np.array(rows, dtype=np.bool_)
    stim.write_shot_data_file(path=str(path), data=data, format="b8", num_measurements=data.shape[1])
