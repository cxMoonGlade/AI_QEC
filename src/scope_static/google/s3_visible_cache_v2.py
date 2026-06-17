from __future__ import annotations

from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import time
from typing import Iterable

import numpy as np
import yaml

from scope_static.google.inventory import (
    DATASET_SURFACE_SET1,
    GoogleLeaf,
    load_google_circuit,
    load_google_observations,
)
from scope_static.google.s3_visible_common import (
    DEFAULT_DATASET_NAME,
    DEFAULT_DATASET_ROOT,
    DEFAULT_SPLIT_POLICY,
    _boundary_detectors,
    _detector_coords,
    _json_safe,
    _load_dem_support_surface,
    _pad_coord,
    _select_contexts,
    _shotblocks,
)


CACHE_SCHEMA_VERSION = "scope_static_google_s3a_v2_public_precompute_cache_v1"
DEFAULT_CACHE_DIR = "outputs/google_static/google_s3_visible_surface_v2_cache/precompute_cache"
DEFAULT_ROUND_BANDS = ("early", "mid", "late")
DEFAULT_REGION_FAMILIES = (
    "boundary_adjacent",
    "bulk",
    "logical_support_neighborhood",
    "interior_chain",
    "full_patch",
)
FORBIDDEN_CACHE_LEARNER_TOKENS = (
    "context_id",
    "sample_id",
    "path",
    "decoder_correctness",
    "decoder_success",
    "decoder_failure",
    "catalog",
    "true_hidden",
    "true_mechanism",
    "oracle",
    "mechanism",
    "teacher",
    "channel",
    "kraus",
    "ptm",
    "prototype",
    "omega",
    "label",
)


@dataclass(frozen=True)
class GoogleS3V2CachedContext:
    cache_context_id: str
    dataset_name: str
    dataset_family: str
    basis: str
    distance: int | None
    rounds: int | None
    patch_public_geometry_class: str
    detector_count: int
    observable_count: int
    shot_count: int
    detection_events: np.ndarray
    obs_flips_actual: np.ndarray
    coords: dict[int, tuple[float, ...]]
    boundary_detectors: set[int]
    logical_support_detectors: set[int]
    region_memberships: dict[str, set[int]]
    round_band_memberships: dict[str, set[int]]
    shotblocks: tuple[tuple[int, int], ...]
    dem_public_support_summary: dict[str, object]

    @property
    def observations(self) -> np.ndarray:
        return np.ascontiguousarray(np.concatenate([self.detection_events, self.obs_flips_actual], axis=1))


def write_google_s3_visible_cache_v2(
    *,
    dataset_root: str | Path | None = None,
    dataset_name: str = DEFAULT_DATASET_NAME,
    cache_dir: str | Path = DEFAULT_CACHE_DIR,
    dem_source: str = "decoder_si1000",
    max_contexts: int = 24,
    round_bands: Iterable[str] = DEFAULT_ROUND_BANDS,
    region_families: Iterable[str] = DEFAULT_REGION_FAMILIES,
    shotblocks_per_context: int = 8,
    shotblock_size: int = 4096,
    min_shotblock_size: int | None = None,
    max_shots_per_context: int | None = None,
    basis: str | None = None,
    distance: int | None = None,
    rounds: int | None = None,
    seed: int = 0,
    split_policy: str = DEFAULT_SPLIT_POLICY,
    hash_source_files: bool = True,
    num_workers: int | None = None,
) -> dict[str, object]:
    if int(max_contexts) <= 0:
        raise ValueError("max_contexts must be positive")
    if int(shotblocks_per_context) <= 0:
        raise ValueError("shotblocks_per_context must be positive")
    if int(shotblock_size) <= 0:
        raise ValueError("shotblock_size must be positive")
    minimum_block = int(min_shotblock_size) if min_shotblock_size is not None else int(shotblock_size)
    if minimum_block <= 0:
        raise ValueError("min_shotblock_size must be positive")
    max_signature_shots = None if max_shots_per_context is None else int(max_shots_per_context)
    if max_signature_shots is not None and max_signature_shots <= 0:
        raise ValueError("max_shots_per_context must be positive when provided")

    bands = _normalize_round_bands(round_bands)
    regions = _normalize_region_families(region_families)
    root = Path(dataset_root or os.environ.get("SCOPE_GOOGLE_SET1_ROOT", DEFAULT_DATASET_ROOT))
    output = Path(cache_dir)
    context_dir = output / "contexts"
    context_dir.mkdir(parents=True, exist_ok=True)

    config = {
        "dataset_root": str(root),
        "dataset_name": str(dataset_name),
        "cache_dir": str(output),
        "dem_source": str(dem_source),
        "max_contexts": int(max_contexts),
        "round_bands": list(bands),
        "region_families": list(regions),
        "shotblocks_per_context": int(shotblocks_per_context),
        "shotblock_size": int(shotblock_size),
        "min_shotblock_size": int(minimum_block),
        "max_shots_per_context": max_signature_shots,
        "basis": basis,
        "distance": None if distance is None else int(distance),
        "rounds": None if rounds is None else int(rounds),
        "seed": int(seed),
        "split_policy": str(split_policy),
        "hash_source_files": bool(hash_source_files),
        "num_workers": None if num_workers is None else int(num_workers),
    }
    config_hash = _stable_hash({key: value for key, value in config.items() if key != "cache_dir"})
    leaves = _select_contexts(
        root,
        dataset_name=str(dataset_name),
        max_contexts=int(max_contexts),
        basis=basis,
        distance=distance,
        rounds=rounds,
    )

    contexts: list[dict[str, object]] = []
    source_rows: list[dict[str, object]] = []
    total_shots = 0
    detector_counts: list[int] = []
    observable_counts: list[int] = []
    wallclock_by_block = _zero_cache_wallclock_blocks()
    worker_count = _resolve_cache_worker_count(num_workers, context_count=len(leaves))
    started = time.perf_counter()
    payloads = _compute_cache_context_payloads(
        leaves,
        dem_source=str(dem_source),
        round_bands=bands,
        region_families=regions,
        shotblocks_per_context=int(shotblocks_per_context),
        shotblock_size=int(shotblock_size),
        min_shotblock_size=int(minimum_block),
        max_shots_per_context=max_signature_shots,
        hash_source_files=bool(hash_source_files),
        num_workers=worker_count,
    )
    for payload in payloads:
        cached = payload["cached_context"]
        arrays_name = f"contexts/{cached.cache_context_id}.npz"
        metadata_name = f"contexts/{cached.cache_context_id}.json"
        write_started = time.perf_counter()
        np.savez_compressed(
            output / arrays_name,
            detection_events=np.asarray(cached.detection_events, dtype=np.bool_),
            obs_flips_actual=np.asarray(cached.obs_flips_actual, dtype=np.bool_),
        )
        context_timing = dict(payload["wallclock_by_block_seconds"])
        context_timing["cache_writeout"] = float(time.perf_counter() - write_started)
        metadata = _cached_context_metadata(cached)
        metadata["wallclock_by_block_seconds"] = {key: float(value) for key, value in sorted(context_timing.items())}
        metadata["context_wallclock_seconds"] = float(payload["context_wallclock_seconds"]) + float(context_timing["cache_writeout"])
        metadata["slowest_block"] = _slowest_cache_block(context_timing)
        (output / metadata_name).write_text(
            json.dumps(_json_safe(metadata), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        for key, value in context_timing.items():
            wallclock_by_block[key] = wallclock_by_block.get(key, 0.0) + float(value)
        context_row = {
            "cache_context_id": cached.cache_context_id,
            "arrays_path": arrays_name,
            "metadata_path": metadata_name,
            "dataset_name": cached.dataset_name,
            "dataset_family": cached.dataset_family,
            "basis": cached.basis,
            "distance": cached.distance,
            "rounds": cached.rounds,
            "patch_public_geometry_class": cached.patch_public_geometry_class,
            "shot_count": int(cached.shot_count),
            "detector_count": int(cached.detector_count),
            "observable_count": int(cached.observable_count),
            "region_family_counts": {key: int(len(value)) for key, value in sorted(cached.region_memberships.items())},
            "round_band_counts": {key: int(len(value)) for key, value in sorted(cached.round_band_memberships.items())},
            "shotblock_count": int(len(cached.shotblocks)),
            "context_wallclock_seconds": float(metadata["context_wallclock_seconds"]),
            "slowest_block": metadata["slowest_block"],
        }
        contexts.append(context_row)
        source_rows.append(dict(payload["source_file_row"]))
        total_shots += int(cached.shot_count)
        detector_counts.append(int(cached.detector_count))
        observable_counts.append(int(cached.observable_count))

    total_wallclock = float(time.perf_counter() - started)
    source_manifest = {
        "schema": "scope_static_google_s3a_v2_source_file_manifest_v1",
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "config_hash": config_hash,
        "source_file_rows": source_rows,
        "source_file_count": int(sum(len(row.get("files", [])) for row in source_rows)),
        "hash_source_files": bool(hash_source_files),
    }
    source_manifest_digest = _stable_hash(source_manifest)
    forbidden_audit = forbidden_cache_audit_google_v2()
    manifest = {
        "schema": "scope_static_google_s3a_v2_cache_manifest_v1",
        "schema_version": CACHE_SCHEMA_VERSION,
        "config_hash": config_hash,
        "source_file_manifest_path": "source_file_manifest.json",
        "source_file_manifest_sha256": source_manifest_digest,
        "forbidden_feature_audit_path": "forbidden_feature_audit.json",
        "config": config,
        "context_count": int(len(contexts)),
        "selection_policy": {
            "strategy": "hierarchical_round_robin_by_public_distance_basis_then_rounds",
            "max_contexts": int(max_contexts),
            "filtered_basis": None if basis is None else str(basis),
            "filtered_distance": None if distance is None else int(distance),
            "filtered_rounds": None if rounds is None else int(rounds),
        },
        "basis_counts": dict(sorted(Counter(str(row.get("basis")) for row in contexts).items())),
        "distance_counts": dict(sorted(Counter(str(row.get("distance")) for row in contexts).items())),
        "rounds_counts": dict(sorted(Counter(str(row.get("rounds")) for row in contexts).items())),
        "shot_count": int(total_shots),
        "detector_count": _single_or_range(detector_counts),
        "detector_count_range": _count_range(detector_counts),
        "observable_count": _single_or_range(observable_counts),
        "observable_count_range": _count_range(observable_counts),
        "contexts": contexts,
        "num_workers": int(worker_count),
        "parallelism": {
            "mode": "process_context_precompute" if worker_count > 1 else "serial_context_precompute",
            "num_workers": int(worker_count),
            "deterministic_manifest_order": True,
            "wallclock_by_block_seconds_semantics": "sum_of_per_context_block_wallclock_seconds",
            "note": "With num_workers > 1, summed per-context block wall-clock seconds can exceed total_wallclock_seconds.",
        },
        "wallclock_by_block_seconds": {key: float(value) for key, value in sorted(wallclock_by_block.items())},
        "wallclock_table": [
            {"cache_block": key, "seconds": float(value)}
            for key, value in sorted(wallclock_by_block.items(), key=lambda item: item[0])
        ],
        "slowest_block": _slowest_cache_block(wallclock_by_block),
        "total_wallclock_seconds": total_wallclock,
        "public_precompute_contents": [
            "per-context detection_events slices",
            "per-context obs_flips_actual slices",
            "detector coordinate, round, boundary, and logical-support metadata",
            "DEM-derived public support summaries",
            "region-family membership",
            "round-band membership",
            "shotblock partitions",
        ],
        "forbidden_feature_audit": forbidden_audit,
        "decision": "google_s3_visible_cache_v2_passed" if forbidden_audit["passed"] and contexts else "google_s3_visible_cache_v2_failed",
    }
    (output / "cache_manifest.json").write_text(json.dumps(_json_safe(manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "source_file_manifest.json").write_text(
        json.dumps(_json_safe(source_manifest), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "forbidden_feature_audit.json").write_text(
        json.dumps(_json_safe(forbidden_audit), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "config.yaml").write_text(yaml.safe_dump({"google_s3_visible_cache_v2": config}, sort_keys=False), encoding="utf-8")
    (output / "summary.md").write_text(format_google_s3_visible_cache_v2_summary(manifest), encoding="utf-8")
    return manifest


def load_google_s3_visible_cache_v2(cache_dir: str | Path) -> tuple[list[GoogleS3V2CachedContext], dict[str, object]]:
    root = Path(cache_dir)
    manifest = _load_json(root / "cache_manifest.json")
    if str(manifest.get("schema_version")) != CACHE_SCHEMA_VERSION:
        raise ValueError(f"{root} is not a {CACHE_SCHEMA_VERSION} cache")
    contexts = []
    for row in manifest.get("contexts", []):
        if not isinstance(row, dict):
            continue
        metadata = _load_json(root / str(row.get("metadata_path")))
        arrays = np.load(root / str(row.get("arrays_path")))
        contexts.append(_cached_context_from_payload(metadata, arrays))
    return contexts, manifest


def forbidden_cache_audit_google_v2() -> dict[str, object]:
    learner_visible_cache_fields: list[str] = []
    hits = [
        {"field_name": name, "token": token}
        for name in learner_visible_cache_fields
        for token in FORBIDDEN_CACHE_LEARNER_TOKENS
        if token in name.lower()
    ]
    checks = {
        "cache_is_protocol_precompute_not_learner_feature_matrix": True,
        "source_paths_are_protocol_only_not_learner_visible": True,
        "no_context_sample_path_fields_declared_as_learner_visible": len(hits) == 0,
        "decoder_correctness_not_cached_as_learner_input": True,
        "true_hidden_mechanism_labels_not_cached": True,
        "oracle_channel_objects_not_cached": True,
    }
    return {
        "schema": "scope_static_google_s3a_v2_cache_forbidden_feature_audit_v1",
        "passed": bool(all(checks.values())),
        "learner_visible_cache_field_count": int(len(learner_visible_cache_fields)),
        "forbidden_feature_count": int(len(hits)),
        "forbidden_feature_hits": hits,
        "checks": checks,
        "note": "source_file_manifest.json intentionally records source paths for reproducibility; those paths are protocol metadata and are never emitted as learner-visible visible_features.npy columns.",
    }


def format_google_s3_visible_cache_v2_summary(manifest: dict[str, object]) -> str:
    return "\n".join(
        [
            "# Google S3A V2 Public Precompute Cache",
            "",
            f"- Decision: `{manifest.get('decision')}`",
            f"- Schema version: `{manifest.get('schema_version')}`",
            f"- Config hash: `{manifest.get('config_hash')}`",
            f"- Contexts: `{int(manifest.get('context_count', 0))}`",
            f"- Distance counts: `{manifest.get('distance_counts', {})}`",
            f"- Basis counts: `{manifest.get('basis_counts', {})}`",
            f"- Round counts: `{manifest.get('rounds_counts', {})}`",
            f"- Shots cached: `{int(manifest.get('shot_count', 0))}`",
            f"- Detector count: `{manifest.get('detector_count')}`",
            "",
            "This cache contains public, read-only, reproducible precompute state for the Google S3A V2 public syndrome-response signature builder. It is not a learner feature matrix.",
            "",
        ]
    )


def _zero_cache_wallclock_blocks() -> dict[str, float]:
    return {
        "circuit_load": 0.0,
        "observation_load_slice": 0.0,
        "detector_geometry": 0.0,
        "dem_support": 0.0,
        "public_memberships": 0.0,
        "source_file_manifest_hash": 0.0,
        "cache_writeout": 0.0,
    }


def _slowest_cache_block(timings: dict[str, float]) -> dict[str, object]:
    if not timings:
        return {"cache_block": None, "seconds": 0.0}
    name, seconds = max(timings.items(), key=lambda item: float(item[1]))
    return {"cache_block": str(name), "seconds": float(seconds)}


def _resolve_cache_worker_count(num_workers: int | None, *, context_count: int) -> int:
    if context_count <= 0:
        return 1
    if num_workers is None:
        return 1
    resolved = int(num_workers)
    if resolved <= 0:
        raise ValueError("num_workers must be positive when provided")
    return min(resolved, int(context_count))


def _compute_cache_context_payloads(
    leaves: list[GoogleLeaf],
    *,
    dem_source: str,
    round_bands: tuple[str, ...],
    region_families: tuple[str, ...],
    shotblocks_per_context: int,
    shotblock_size: int,
    min_shotblock_size: int,
    max_shots_per_context: int | None,
    hash_source_files: bool,
    num_workers: int,
) -> list[dict[str, object]]:
    if num_workers <= 1 or len(leaves) <= 1:
        return [
            _cache_context_payload(
                index,
                leaf,
                dem_source=dem_source,
                round_bands=round_bands,
                region_families=region_families,
                shotblocks_per_context=shotblocks_per_context,
                shotblock_size=shotblock_size,
                min_shotblock_size=min_shotblock_size,
                max_shots_per_context=max_shots_per_context,
                hash_source_files=hash_source_files,
            )
            for index, leaf in enumerate(leaves)
        ]
    payloads: list[dict[str, object] | None] = [None] * len(leaves)
    with ProcessPoolExecutor(max_workers=int(num_workers)) as executor:
        futures = {
            executor.submit(
                _cache_context_payload,
                index,
                leaf,
                dem_source=dem_source,
                round_bands=round_bands,
                region_families=region_families,
                shotblocks_per_context=shotblocks_per_context,
                shotblock_size=shotblock_size,
                min_shotblock_size=min_shotblock_size,
                max_shots_per_context=max_shots_per_context,
                hash_source_files=hash_source_files,
            ): index
            for index, leaf in enumerate(leaves)
        }
        for future in as_completed(futures):
            payloads[futures[future]] = future.result()
    return [payload for payload in payloads if payload is not None]


def _cache_context_payload(
    context_index: int,
    leaf: GoogleLeaf,
    *,
    dem_source: str,
    round_bands: tuple[str, ...],
    region_families: tuple[str, ...],
    shotblocks_per_context: int,
    shotblock_size: int,
    min_shotblock_size: int,
    max_shots_per_context: int | None,
    hash_source_files: bool,
) -> dict[str, object]:
    context_started = time.perf_counter()
    cached, timings = _precompute_context_with_timing(
        leaf,
        cache_context_id=f"cache_context_{int(context_index):06d}",
        dem_source=dem_source,
        round_bands=round_bands,
        region_families=region_families,
        shotblocks_per_context=shotblocks_per_context,
        shotblock_size=shotblock_size,
        min_shotblock_size=min_shotblock_size,
        max_shots_per_context=max_shots_per_context,
    )
    source_started = time.perf_counter()
    source_file_row = _source_file_row(leaf, cached.cache_context_id, dem_source=dem_source, hash_files=hash_source_files)
    timings["source_file_manifest_hash"] = float(time.perf_counter() - source_started)
    return {
        "cached_context": cached,
        "source_file_row": source_file_row,
        "wallclock_by_block_seconds": timings,
        "context_wallclock_seconds": float(time.perf_counter() - context_started),
    }


def _precompute_context(
    leaf: GoogleLeaf,
    *,
    cache_context_id: str,
    dem_source: str,
    round_bands: tuple[str, ...],
    region_families: tuple[str, ...],
    shotblocks_per_context: int,
    shotblock_size: int,
    min_shotblock_size: int,
    max_shots_per_context: int | None,
) -> GoogleS3V2CachedContext:
    cached, _timing = _precompute_context_with_timing(
        leaf,
        cache_context_id=cache_context_id,
        dem_source=dem_source,
        round_bands=round_bands,
        region_families=region_families,
        shotblocks_per_context=shotblocks_per_context,
        shotblock_size=shotblock_size,
        min_shotblock_size=min_shotblock_size,
        max_shots_per_context=max_shots_per_context,
    )
    return cached


def _precompute_context_with_timing(
    leaf: GoogleLeaf,
    *,
    cache_context_id: str,
    dem_source: str,
    round_bands: tuple[str, ...],
    region_families: tuple[str, ...],
    shotblocks_per_context: int,
    shotblock_size: int,
    min_shotblock_size: int,
    max_shots_per_context: int | None,
) -> tuple[GoogleS3V2CachedContext, dict[str, float]]:
    timings = _zero_cache_wallclock_blocks()
    started = time.perf_counter()
    circuit = load_google_circuit(leaf)
    timings["circuit_load"] = float(time.perf_counter() - started)
    detector_count = int(circuit.num_detectors)
    observable_count = int(circuit.num_observables)
    started = time.perf_counter()
    observations = load_google_observations(leaf)
    if max_shots_per_context is not None:
        observations = observations[: int(max_shots_per_context)]
    detectors = np.ascontiguousarray(observations[:, :detector_count], dtype=np.bool_)
    observables = np.ascontiguousarray(observations[:, detector_count : detector_count + observable_count], dtype=np.bool_)
    timings["observation_load_slice"] = float(time.perf_counter() - started)
    started = time.perf_counter()
    coords = _detector_coords(circuit, detector_count)
    boundary = _boundary_detectors(coords)
    patch_public_geometry_class = _patch_public_geometry_class(
        leaf,
        coords=coords,
        detector_count=detector_count,
        observable_count=observable_count,
    )
    timings["detector_geometry"] = float(time.perf_counter() - started)
    started = time.perf_counter()
    logical_support, dem_summary = _logical_support_detectors_and_summary(leaf, dem_source=str(dem_source), detector_count=detector_count)
    timings["dem_support"] = float(time.perf_counter() - started)
    started = time.perf_counter()
    region_memberships = {
        region: _detectors_for_region(
            region,
            detector_count=detector_count,
            boundary_detectors=boundary,
            logical_support_detectors=logical_support,
            coords=coords,
        )
        for region in region_families
    }
    round_band_memberships = {
        band: _detectors_for_round_band(coords, detector_count=detector_count, round_band=band)
        for band in round_bands
    }
    shotblocks = tuple(
        _shotblocks(
            shot_count=int(detectors.shape[0]),
            shotblock_size=int(shotblock_size),
            shotblocks_per_context=int(shotblocks_per_context),
            min_shotblock_size=int(min_shotblock_size),
        )
    )
    timings["public_memberships"] = float(time.perf_counter() - started)
    cached = GoogleS3V2CachedContext(
        cache_context_id=str(cache_context_id),
        dataset_name=str(leaf.dataset_name),
        dataset_family=str(leaf.dataset_family),
        basis=str(leaf.basis),
        distance=None if leaf.distance is None else int(leaf.distance),
        rounds=None if leaf.rounds is None else int(leaf.rounds),
        patch_public_geometry_class=patch_public_geometry_class,
        detector_count=detector_count,
        observable_count=observable_count,
        shot_count=int(detectors.shape[0]),
        detection_events=detectors,
        obs_flips_actual=observables,
        coords=coords,
        boundary_detectors=boundary,
        logical_support_detectors=logical_support,
        region_memberships=region_memberships,
        round_band_memberships=round_band_memberships,
        shotblocks=shotblocks,
        dem_public_support_summary=dem_summary,
    )
    return cached, timings


def _cached_context_metadata(cached: GoogleS3V2CachedContext) -> dict[str, object]:
    return {
        "schema": "scope_static_google_s3a_v2_cached_context_v1",
        "cache_context_id": cached.cache_context_id,
        "dataset_name": cached.dataset_name,
        "dataset_family": cached.dataset_family,
        "basis": cached.basis,
        "distance": cached.distance,
        "rounds": cached.rounds,
        "patch_public_geometry_class": cached.patch_public_geometry_class,
        "detector_count": int(cached.detector_count),
        "observable_count": int(cached.observable_count),
        "shot_count": int(cached.shot_count),
        "coords": {str(key): list(value) for key, value in sorted(cached.coords.items())},
        "boundary_detectors": sorted(int(value) for value in cached.boundary_detectors),
        "logical_support_detectors": sorted(int(value) for value in cached.logical_support_detectors),
        "region_memberships": {
            key: sorted(int(value) for value in values)
            for key, values in sorted(cached.region_memberships.items())
        },
        "round_band_memberships": {
            key: sorted(int(value) for value in values)
            for key, values in sorted(cached.round_band_memberships.items())
        },
        "shotblocks": [[int(start), int(stop)] for start, stop in cached.shotblocks],
        "dem_public_support_summary": cached.dem_public_support_summary,
    }


def _cached_context_from_payload(metadata: dict[str, object], arrays: object) -> GoogleS3V2CachedContext:
    coords_payload = dict(metadata.get("coords", {}))
    coords = {int(key): tuple(float(item) for item in value) for key, value in coords_payload.items()}
    return GoogleS3V2CachedContext(
        cache_context_id=str(metadata.get("cache_context_id")),
        dataset_name=str(metadata.get("dataset_name")),
        dataset_family=str(metadata.get("dataset_family")),
        basis=str(metadata.get("basis")),
        distance=None if metadata.get("distance") is None else int(metadata.get("distance")),
        rounds=None if metadata.get("rounds") is None else int(metadata.get("rounds")),
        patch_public_geometry_class=str(metadata.get("patch_public_geometry_class")),
        detector_count=int(metadata.get("detector_count", 0)),
        observable_count=int(metadata.get("observable_count", 0)),
        shot_count=int(metadata.get("shot_count", 0)),
        detection_events=np.ascontiguousarray(arrays["detection_events"], dtype=np.bool_),
        obs_flips_actual=np.ascontiguousarray(arrays["obs_flips_actual"], dtype=np.bool_),
        coords=coords,
        boundary_detectors={int(value) for value in metadata.get("boundary_detectors", [])},
        logical_support_detectors={int(value) for value in metadata.get("logical_support_detectors", [])},
        region_memberships={
            str(key): {int(item) for item in values}
            for key, values in dict(metadata.get("region_memberships", {})).items()
        },
        round_band_memberships={
            str(key): {int(item) for item in values}
            for key, values in dict(metadata.get("round_band_memberships", {})).items()
        },
        shotblocks=tuple((int(start), int(stop)) for start, stop in metadata.get("shotblocks", [])),
        dem_public_support_summary=dict(metadata.get("dem_public_support_summary", {})),
    )


def _source_file_row(leaf: GoogleLeaf, cache_context_id: str, *, dem_source: str, hash_files: bool) -> dict[str, object]:
    files = [
        ("circuit_ideal", leaf.circuit_ideal),
        ("detection_events", leaf.detection_events),
        ("obs_flips_actual", leaf.obs_flips_actual),
        ("metadata", leaf.metadata),
    ]
    try:
        files.append(("decoder_error_model", leaf.decoder_error_model(dem_source)))
    except Exception:
        pass
    return {
        "cache_context_id": str(cache_context_id),
        "files": [_file_record(role, path, hash_file=hash_files) for role, path in files],
    }


def _file_record(role: str, path: Path, *, hash_file: bool) -> dict[str, object]:
    exists = Path(path).is_file()
    return {
        "role": str(role),
        "path": str(path),
        "exists": bool(exists),
        "size_bytes": int(Path(path).stat().st_size) if exists else 0,
        "sha256": _file_sha256(path) if exists and hash_file else None,
    }


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _logical_support_detectors_and_summary(leaf: GoogleLeaf, *, dem_source: str, detector_count: int) -> tuple[set[int], dict[str, object]]:
    if leaf.dataset_name != DATASET_SURFACE_SET1:
        out = set(range(int(detector_count)))
        return out, {"available": False, "reason": "dataset_not_set1", "logical_support_detector_count": int(len(out))}
    try:
        support_surface = _load_dem_support_surface(leaf, dem_source=str(dem_source))
    except (FileNotFoundError, ValueError) as exc:
        out = set(range(int(detector_count)))
        return out, {
            "available": False,
            "reason": type(exc).__name__,
            "logical_support_detector_count": int(len(out)),
        }
    out: set[int] = set()
    logical_fault_count = 0
    observable_bits = range(int(support_surface.num_detectors), int(support_surface.num_detectors + support_surface.num_observables))
    for logical_bit in observable_bits:
        for fault in support_surface.faults_by_observation_bit[int(logical_bit)]:
            logical_fault_count += 1
            for bit in support_surface.supports_by_fault[int(fault)]:
                if int(bit) < int(detector_count):
                    out.add(int(bit))
    if not out:
        out = set(range(int(detector_count)))
    support_sizes = [len(tuple(bits)) for bits in support_surface.supports_by_fault]
    return out, {
        "available": True,
        "dem_source": str(dem_source),
        "fault_count": int(len(support_surface.supports_by_fault)),
        "logical_fault_count": int(logical_fault_count),
        "num_detectors": int(support_surface.num_detectors),
        "num_observables": int(support_surface.num_observables),
        "logical_support_detector_count": int(len(out)),
        "support_size_min": min(support_sizes) if support_sizes else 0,
        "support_size_max": max(support_sizes) if support_sizes else 0,
        "support_size_mean": float(np.mean(support_sizes)) if support_sizes else 0.0,
    }


def _detectors_for_region(
    region_family: str,
    *,
    detector_count: int,
    boundary_detectors: set[int],
    logical_support_detectors: set[int],
    coords: dict[int, tuple[float, ...]],
) -> set[int]:
    all_detectors = set(range(int(detector_count)))
    region = str(region_family)
    if region == "boundary_adjacent":
        return set(boundary_detectors) or set(all_detectors)
    if region == "bulk":
        return set(all_detectors.difference(boundary_detectors))
    if region == "logical_support_neighborhood":
        return set(logical_support_detectors)
    if region == "interior_chain":
        bulk = sorted(all_detectors.difference(boundary_detectors))
        if bulk:
            return set(bulk)
        return set(_middle_detector_chain(coords, detector_count=detector_count))
    if region == "full_patch":
        return set(all_detectors)
    raise ValueError(f"unknown region family {region_family!r}")


def _detectors_for_round_band(coords: dict[int, tuple[float, ...]], *, detector_count: int, round_band: str) -> set[int]:
    if str(round_band) == "all" or not coords:
        return set(range(int(detector_count)))
    padded = {idx: _pad_coord(value) for idx, value in coords.items()}
    if not padded:
        return set(range(int(detector_count)))
    ts = [value[2] for value in padded.values()]
    t_min, t_max = min(ts), max(ts)
    if math.isclose(t_min, t_max):
        return set(range(int(detector_count)))
    out: set[int] = set()
    for idx, value in padded.items():
        frac = (value[2] - t_min) / max(t_max - t_min, 1e-12)
        if str(round_band) == "early" and frac <= 1.0 / 3.0:
            out.add(int(idx))
        elif str(round_band) == "mid" and 1.0 / 3.0 <= frac <= 2.0 / 3.0:
            out.add(int(idx))
        elif str(round_band) == "late" and frac >= 2.0 / 3.0:
            out.add(int(idx))
    return out


def _patch_public_geometry_class(
    leaf: GoogleLeaf,
    *,
    coords: dict[int, tuple[float, ...]],
    detector_count: int,
    observable_count: int,
) -> str:
    spans = _coord_spans(coords)
    digest_text = "|".join(
        [
            str(leaf.dataset_family),
            str(leaf.distance),
            str(detector_count),
            str(observable_count),
            f"{spans['x_span']:.6g}",
            f"{spans['y_span']:.6g}",
            f"{spans['t_span']:.6g}",
        ]
    )
    digest = hashlib.sha256(digest_text.encode("utf-8")).hexdigest()[:10]
    return f"{leaf.dataset_family}_d{leaf.distance}_det{detector_count}_obs{observable_count}_{digest}"


def _middle_detector_chain(coords: dict[int, tuple[float, ...]], *, detector_count: int) -> list[int]:
    if not coords:
        return list(range(int(detector_count)))
    padded = {idx: _pad_coord(value) for idx, value in coords.items()}
    y_values = sorted(value[1] for value in padded.values())
    mid_y = y_values[len(y_values) // 2]
    return [idx for idx, value in padded.items() if math.isclose(value[1], mid_y)]


def _coord_spans(coords: dict[int, tuple[float, ...]]) -> dict[str, float]:
    if not coords:
        return {"x_span": 0.0, "y_span": 0.0, "t_span": 0.0}
    arr = np.asarray([_pad_coord(value) for value in coords.values()], dtype=np.float64)
    return {
        "x_span": float(np.max(arr[:, 0]) - np.min(arr[:, 0])),
        "y_span": float(np.max(arr[:, 1]) - np.min(arr[:, 1])),
        "t_span": float(np.max(arr[:, 2]) - np.min(arr[:, 2])),
    }


def _normalize_round_bands(values: Iterable[str]) -> tuple[str, ...]:
    allowed = {"early", "mid", "late", "all"}
    out = tuple(dict.fromkeys(str(value) for value in values))
    if not out:
        raise ValueError("round_bands must be non-empty")
    bad = [value for value in out if value not in allowed]
    if bad:
        raise ValueError(f"round_bands contains unsupported values: {bad!r}")
    return out


def _normalize_region_families(values: Iterable[str]) -> tuple[str, ...]:
    allowed = set(DEFAULT_REGION_FAMILIES)
    out = tuple(dict.fromkeys(str(value) for value in values))
    if not out:
        raise ValueError("region_families must be non-empty")
    bad = [value for value in out if value not in allowed]
    if bad:
        raise ValueError(f"region_families contains unsupported values: {bad!r}")
    return out


def _single_or_range(values: list[int]) -> int | None:
    if not values:
        return None
    unique = sorted(set(int(value) for value in values))
    return int(unique[0]) if len(unique) == 1 else None


def _count_range(values: list[int]) -> list[int]:
    if not values:
        return []
    return [int(min(values)), int(max(values))]


def _stable_hash(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _load_json(path: Path) -> dict[str, object]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data
