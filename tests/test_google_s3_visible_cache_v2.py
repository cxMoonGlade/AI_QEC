from __future__ import annotations

from pathlib import Path

import numpy as np
import yaml

from google_s3_fixture import write_tiny_google_s3_dataset
from scope_static.experiments.willow_data.s3_visible_cache_v2 import run_google_s3_visible_cache_v2_from_config
from scope_static.experiments.willow_data.s3_visible_aggregate_v2 import run_google_s3_visible_aggregate_v2_from_config
from scope_static.google.s3_visible_cache_v2 import (
    load_google_s3_visible_cache_v2,
    write_google_s3_visible_cache_v2,
)
from scope_static.google.s3_visible_surface_v2 import (
    write_google_s3_visible_aggregate_cache_v2,
    write_google_s3_visible_surface_v2,
)
from scope_static.mechanism_discovery.artifacts import load_stage3a_frozen_visible_features


def test_google_s3_visible_cache_v2_writes_public_precompute_artifacts(tmp_path: Path) -> None:
    root = write_tiny_google_s3_dataset(tmp_path, contexts=3)
    cache = tmp_path / "cache_v2"

    manifest = write_google_s3_visible_cache_v2(
        dataset_root=root,
        cache_dir=cache,
        max_contexts=3,
        round_bands=("early", "mid", "late"),
        region_families=("boundary_adjacent", "logical_support_neighborhood", "full_patch"),
        shotblocks_per_context=2,
        shotblock_size=2,
        min_shotblock_size=2,
        hash_source_files=False,
    )
    contexts, loaded = load_google_s3_visible_cache_v2(cache)

    assert manifest["decision"] == "google_s3_visible_cache_v2_passed"
    assert manifest["schema_version"] == "scope_static_google_s3a_v2_public_precompute_cache_v1"
    assert manifest["context_count"] == 3
    assert manifest["shot_count"] == 12
    assert manifest["detector_count"] == 1
    assert manifest["num_workers"] == 1
    assert manifest["parallelism"]["mode"] == "serial_context_precompute"
    assert manifest["total_wallclock_seconds"] >= 0.0
    assert manifest["wallclock_table"]
    assert manifest["forbidden_feature_audit"]["passed"] is True
    assert loaded["config_hash"] == manifest["config_hash"]
    assert len(contexts) == 3
    assert contexts[0].detection_events.shape == (4, 1)
    assert contexts[0].obs_flips_actual.shape == (4, 1)
    assert contexts[0].round_band_memberships
    assert contexts[0].region_memberships
    assert loaded["contexts"][0]["slowest_block"]["cache_block"] in {
        "cache_writeout",
        "circuit_load",
        "dem_support",
        "detector_geometry",
        "observation_load_slice",
        "public_memberships",
        "source_file_manifest_hash",
    }

    for name in [
        "cache_manifest.json",
        "source_file_manifest.json",
        "forbidden_feature_audit.json",
        "config.yaml",
        "summary.md",
    ]:
        assert (cache / name).exists()


def test_google_s3_visible_cache_v2_parallel_matches_serial(tmp_path: Path) -> None:
    root = write_tiny_google_s3_dataset(tmp_path, contexts=4)
    serial_cache = tmp_path / "cache_v2_serial"
    parallel_cache = tmp_path / "cache_v2_parallel"
    kwargs = {
        "max_contexts": 4,
        "round_bands": ("early", "mid", "late"),
        "region_families": ("boundary_adjacent", "logical_support_neighborhood", "full_patch"),
        "shotblocks_per_context": 2,
        "shotblock_size": 2,
        "min_shotblock_size": 2,
        "hash_source_files": False,
    }

    serial = write_google_s3_visible_cache_v2(
        dataset_root=root,
        cache_dir=serial_cache,
        num_workers=1,
        **kwargs,
    )
    parallel = write_google_s3_visible_cache_v2(
        dataset_root=root,
        cache_dir=parallel_cache,
        num_workers=2,
        **kwargs,
    )
    serial_contexts, _serial_manifest = load_google_s3_visible_cache_v2(serial_cache)
    parallel_contexts, _parallel_manifest = load_google_s3_visible_cache_v2(parallel_cache)

    assert parallel["decision"] == "google_s3_visible_cache_v2_passed"
    assert parallel["num_workers"] == 2
    assert parallel["parallelism"]["mode"] == "process_context_precompute"
    assert [row["cache_context_id"] for row in serial["contexts"]] == [
        row["cache_context_id"] for row in parallel["contexts"]
    ]
    assert len(serial_contexts) == len(parallel_contexts)
    for left, right in zip(serial_contexts, parallel_contexts):
        assert left.cache_context_id == right.cache_context_id
        assert np.array_equal(left.detection_events, right.detection_events)
        assert np.array_equal(left.obs_flips_actual, right.obs_flips_actual)
        assert left.region_memberships == right.region_memberships
        assert left.round_band_memberships == right.round_band_memberships


def test_google_s3_visible_surface_v2_consumes_cache_without_source_root(tmp_path: Path) -> None:
    root = write_tiny_google_s3_dataset(tmp_path, contexts=3)
    cache = tmp_path / "cache_v2"
    direct = tmp_path / "direct_s3a"
    cached = tmp_path / "cached_s3a"
    kwargs = {
        "max_contexts": 3,
        "round_bands": ("early", "mid", "late"),
        "region_families": ("boundary_adjacent", "logical_support_neighborhood", "full_patch"),
        "shotblocks_per_context": 2,
        "shotblock_size": 2,
        "min_shotblock_size": 2,
    }
    write_google_s3_visible_cache_v2(
        dataset_root=root,
        cache_dir=cache,
        hash_source_files=False,
        **kwargs,
    )
    write_google_s3_visible_surface_v2(dataset_root=root, output_dir=direct, **kwargs)
    result = write_google_s3_visible_surface_v2(
        dataset_root=tmp_path / "missing_source_root",
        cache_dir=cache,
        output_dir=cached,
        **kwargs,
    )

    direct_matrix, direct_features, _direct_manifest = load_stage3a_frozen_visible_features(direct)
    cached_matrix, cached_features, _cached_manifest = load_stage3a_frozen_visible_features(cached)
    assert result["decision"] == "google_s3_visible_surface_v2_passed"
    assert result["context_scope"]["cache_used"] is True
    assert result["cache_manifest"]["cache_used"] is True
    assert direct_features == cached_features
    assert np.allclose(direct_matrix, cached_matrix)


def test_google_s3_visible_surface_v2_consumes_aggregate_cache(tmp_path: Path) -> None:
    root = write_tiny_google_s3_dataset(tmp_path, contexts=3)
    cache = tmp_path / "cache_v2"
    direct = tmp_path / "direct_s3a"
    aggregate = tmp_path / "aggregate_s3a"
    kwargs = {
        "max_contexts": 3,
        "round_bands": ("early", "mid", "late"),
        "region_families": ("boundary_adjacent", "logical_support_neighborhood", "full_patch"),
        "shotblocks_per_context": 2,
        "shotblock_size": 2,
        "min_shotblock_size": 2,
    }
    write_google_s3_visible_cache_v2(
        dataset_root=root,
        cache_dir=cache,
        hash_source_files=False,
        **kwargs,
    )
    aggregate_manifest = write_google_s3_visible_aggregate_cache_v2(
        cache_dir=cache,
        round_bands=kwargs["round_bands"],
        region_families=kwargs["region_families"],
    )
    write_google_s3_visible_surface_v2(dataset_root=root, output_dir=direct, **kwargs)
    result = write_google_s3_visible_surface_v2(
        dataset_root=tmp_path / "missing_source_root",
        cache_dir=cache,
        output_dir=aggregate,
        **kwargs,
    )

    direct_matrix, direct_features, _direct_manifest = load_stage3a_frozen_visible_features(direct)
    aggregate_matrix, aggregate_features, _aggregate_manifest = load_stage3a_frozen_visible_features(aggregate)
    assert aggregate_manifest["decision"] == "google_s3_visible_aggregate_cache_v2_passed"
    assert aggregate_manifest["wallclock_table"]
    assert aggregate_manifest["slowest_block"]["feature_block"] in {
        "marginal",
        "spatial_corr",
        "temporal_corr",
        "logical_coupling",
        "stability",
        "metadata_schema_writeout",
    }
    assert result["context_scope"]["aggregate_cache_used"] is True
    assert result["aggregate_cache_manifest"]["aggregate_cache_used"] is True
    assert (aggregate / "aggregate_cache_manifest.json").exists()
    assert direct_features == aggregate_features
    assert np.allclose(direct_matrix, aggregate_matrix)


def test_google_s3_visible_aggregate_v2_parallel_matches_serial(tmp_path: Path) -> None:
    root = write_tiny_google_s3_dataset(tmp_path, contexts=4)
    cache = tmp_path / "cache_v2"
    kwargs = {
        "max_contexts": 4,
        "round_bands": ("early", "mid", "late"),
        "region_families": ("boundary_adjacent", "logical_support_neighborhood", "full_patch"),
        "shotblocks_per_context": 2,
        "shotblock_size": 2,
        "min_shotblock_size": 2,
    }
    write_google_s3_visible_cache_v2(
        dataset_root=root,
        cache_dir=cache,
        hash_source_files=False,
        **kwargs,
    )

    serial = write_google_s3_visible_aggregate_cache_v2(
        cache_dir=cache,
        round_bands=kwargs["round_bands"],
        region_families=kwargs["region_families"],
        num_workers=1,
    )
    serial_rows = {
        str(row["cache_context_id"]): np.load(cache / str(row["arrays_path"]))["feature_rows"].copy()
        for row in serial["aggregate_contexts"]
    }
    parallel = write_google_s3_visible_aggregate_cache_v2(
        cache_dir=cache,
        round_bands=kwargs["round_bands"],
        region_families=kwargs["region_families"],
        num_workers=2,
    )

    assert parallel["decision"] == "google_s3_visible_aggregate_cache_v2_passed"
    assert parallel["num_workers"] == 2
    assert parallel["parallelism"]["mode"] == "threaded_context_aggregation"
    assert [row["cache_context_id"] for row in serial["aggregate_contexts"]] == [
        row["cache_context_id"] for row in parallel["aggregate_contexts"]
    ]
    for row in parallel["aggregate_contexts"]:
        context_id = str(row["cache_context_id"])
        parallel_rows = np.load(cache / str(row["arrays_path"]))["feature_rows"]
        assert np.allclose(serial_rows[context_id], parallel_rows, rtol=1e-12, atol=1e-12)


def test_google_s3_visible_cache_v2_config_wrapper(tmp_path: Path) -> None:
    root = write_tiny_google_s3_dataset(tmp_path, contexts=3)
    cache = tmp_path / "configured_cache_v2"
    config = tmp_path / "cache_v2.yaml"
    config.write_text(
        yaml.safe_dump(
            {
                "google_s3_visible_cache_v2": {
                    "dataset_root": str(root),
                    "cache_dir": str(cache),
                    "max_contexts": 3,
                    "round_bands": ["early", "mid", "late"],
                    "region_families": ["boundary_adjacent", "logical_support_neighborhood", "full_patch"],
                    "shotblocks_per_context": 2,
                    "shotblock_size": 2,
                    "min_shotblock_size": 2,
                    "hash_source_files": False,
                    "num_workers": 2,
                }
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    result = run_google_s3_visible_cache_v2_from_config(config_path=config)

    assert result["decision"] == "google_s3_visible_cache_v2_passed"
    assert result["num_workers"] == 2
    assert (cache / "cache_manifest.json").exists()


def test_google_s3_visible_aggregate_v2_config_wrapper(tmp_path: Path) -> None:
    root = write_tiny_google_s3_dataset(tmp_path, contexts=3)
    cache = tmp_path / "configured_cache_v2"
    cache_config = tmp_path / "cache_v2.yaml"
    cache_config.write_text(
        yaml.safe_dump(
            {
                "google_s3_visible_cache_v2": {
                    "dataset_root": str(root),
                    "cache_dir": str(cache),
                    "max_contexts": 3,
                    "round_bands": ["early", "mid", "late"],
                    "region_families": ["boundary_adjacent", "logical_support_neighborhood", "full_patch"],
                    "shotblocks_per_context": 2,
                    "shotblock_size": 2,
                    "min_shotblock_size": 2,
                    "hash_source_files": False,
                }
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    run_google_s3_visible_cache_v2_from_config(config_path=cache_config)
    aggregate_config = tmp_path / "aggregate_v2.yaml"
    aggregate_config.write_text(
        yaml.safe_dump(
            {
                "google_s3_visible_aggregate_v2": {
                    "cache_dir": str(cache),
                    "round_bands": ["early", "mid", "late"],
                    "region_families": ["boundary_adjacent", "logical_support_neighborhood", "full_patch"],
                    "num_workers": 2,
                }
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    result = run_google_s3_visible_aggregate_v2_from_config(config_path=aggregate_config)

    assert result["decision"] == "google_s3_visible_aggregate_cache_v2_passed"
    assert result["num_workers"] == 2
    assert (cache / "aggregates" / "aggregate_manifest.json").exists()
