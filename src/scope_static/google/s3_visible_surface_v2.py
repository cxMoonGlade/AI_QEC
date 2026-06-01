from __future__ import annotations

from collections import Counter, defaultdict
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
from scope_static.google.s3_visible_cache_v2 import (
    GoogleS3V2CachedContext,
    load_google_s3_visible_cache_v2,
)
from scope_static.google.s3_visible_surface import (
    DEFAULT_DATASET_NAME,
    DEFAULT_DATASET_ROOT,
    DEFAULT_SPLIT_POLICY,
    _boundary_detectors,
    _detector_coords,
    _finite,
    _indices_for_groups,
    _json_safe,
    _load_dem_support_surface,
    _matrix_digest,
    _pad_coord,
    _select_contexts,
    _shotblocks,
    _text_digest,
)


STAGE_NAME = "Google_S3A_real_public_syndrome_response_signature"
AGGREGATE_CACHE_SCHEMA_VERSION = "scope_static_google_s3a_v2_aggregate_cache_v1"
DEFAULT_OUTPUT_DIR = "outputs/google_static/google_s3_visible_surface_v2/S3A_protocol_freeze"
DEFAULT_ASSIGNMENT_UNIT = "google_public_syndrome_response_signature"
DEFAULT_ROUND_BANDS = ("early", "mid", "late")
DEFAULT_REGION_FAMILIES = (
    "boundary_adjacent",
    "bulk",
    "logical_support_neighborhood",
    "interior_chain",
    "full_patch",
)

MARGINAL_FEATURE_NAMES = [
    "raw__marginal__detector_rate_mean",
    "raw__marginal__detector_rate_std",
    "raw__marginal__detector_rate_min",
    "raw__marginal__detector_rate_max",
    "raw__marginal__detector_rate_q25",
    "raw__marginal__detector_rate_q75",
    "raw__marginal__observable_flip_rate_mean",
    "raw__marginal__observable_flip_rate_max",
    "raw__marginal__boundary_detector_rate_mean",
    "raw__marginal__bulk_detector_rate_mean",
    "raw__marginal__round_layer_rate_slope",
    "raw__marginal__detector_rate_entropy_mean",
]

SPATIAL_CORR_FEATURE_NAMES = [
    "raw__spatial_corr__nearest_neighbor_cov_mean",
    "raw__spatial_corr__nearest_neighbor_cov_std",
    "raw__spatial_corr__nearest_neighbor_cov_max_abs",
    "raw__spatial_corr__nearest_neighbor_corr_mean",
    "raw__spatial_corr__nearest_neighbor_corr_std",
    "raw__spatial_corr__boundary_bulk_rate_contrast",
    "raw__spatial_corr__nearest_neighbor_pair_count_norm",
]

TEMPORAL_CORR_FEATURE_NAMES = [
    "raw__temporal_corr__adjacent_round_cov_mean",
    "raw__temporal_corr__adjacent_round_cov_std",
    "raw__temporal_corr__adjacent_round_corr_mean",
    "raw__temporal_corr__adjacent_round_corr_std",
    "raw__temporal_corr__early_mid_rate_delta",
    "raw__temporal_corr__late_mid_rate_delta",
    "raw__temporal_corr__late_early_rate_delta",
    "raw__temporal_corr__adjacent_round_pair_count_norm",
]

LOGICAL_COUPLING_FEATURE_NAMES = [
    "raw__logical_coupling__detector_logical_cov_mean",
    "raw__logical_coupling__detector_logical_cov_std",
    "raw__logical_coupling__detector_logical_cov_max_abs",
    "raw__logical_coupling__detector_logical_corr_mean",
    "raw__logical_coupling__logical_conditioned_rate_diff_mean",
    "raw__logical_coupling__logical_conditioned_rate_diff_std",
    "raw__logical_coupling__logical_conditioned_rate_diff_max_abs",
    "raw__logical_coupling__pair_count_norm",
]

STABILITY_FEATURE_NAMES = [
    "raw__stability__shotblock_detector_rate_variance",
    "raw__stability__shotblock_logical_rate_variance",
    "raw__stability__finite_shot_detector_rate_se",
    "raw__stability__finite_shot_logical_rate_se",
    "raw__stability__bootstrap_detector_rate_se",
    "raw__stability__bootstrap_logical_rate_se",
    "raw__stability__context_repeated_detector_rate_variance",
    "raw__stability__context_repeated_logical_rate_variance",
]

PUBLIC_GEOMETRY_FEATURE_NAMES = [
    "meta__public_geometry__dataset_surface",
    "meta__public_geometry__basis_x",
    "meta__public_geometry__basis_z",
    "meta__public_geometry__distance",
    "meta__public_geometry__rounds",
    "meta__public_geometry__round_band_early",
    "meta__public_geometry__round_band_mid",
    "meta__public_geometry__round_band_late",
    "meta__public_geometry__round_band_all",
    "meta__public_geometry__region_boundary_adjacent",
    "meta__public_geometry__region_bulk",
    "meta__public_geometry__region_logical_support",
    "meta__public_geometry__region_interior_chain",
    "meta__public_geometry__region_full_patch",
    "meta__public_geometry__detector_count",
    "meta__public_geometry__observable_count",
    "meta__public_geometry__selected_detector_fraction",
    "meta__public_geometry__boundary_detector_fraction",
    "meta__public_geometry__logical_support_detector_fraction",
    "meta__public_geometry__coord_x_span",
    "meta__public_geometry__coord_y_span",
    "meta__public_geometry__coord_t_span",
    "meta__public_geometry__shot_count_total",
]

FEATURE_NAMES = [
    *MARGINAL_FEATURE_NAMES,
    *SPATIAL_CORR_FEATURE_NAMES,
    *TEMPORAL_CORR_FEATURE_NAMES,
    *LOGICAL_COUPLING_FEATURE_NAMES,
    *STABILITY_FEATURE_NAMES,
    *PUBLIC_GEOMETRY_FEATURE_NAMES,
]
FEATURE_INDEX = {name: idx for idx, name in enumerate(FEATURE_NAMES)}

FORBIDDEN_GOOGLE_V2_FEATURE_TOKENS = (
    "context_id",
    "sample_id",
    "leaf_id",
    "leaf_path",
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
class _SignatureReplica:
    public_key: tuple[str, ...]
    public_fields: dict[str, object]
    feature_row: np.ndarray
    detector_rate_mean: float
    logical_rate_mean: float
    shot_count: int
    selected_detector_count: int


@dataclass(frozen=True)
class _PublicSignatureContext:
    dataset_name: str
    dataset_family: str
    basis: str
    distance: int | None
    rounds: int | None
    patch_public_geometry_class: str


@dataclass(frozen=True)
class _AggregatePayload:
    replicas: list[_SignatureReplica]
    context_summaries: list[dict[str, object]]
    skipped_units: list[dict[str, object]]
    public_contexts: list[_PublicSignatureContext]
    reference: dict[str, object]


def write_google_s3_visible_surface_v2(
    *,
    dataset_root: str | Path | None = None,
    dataset_name: str = DEFAULT_DATASET_NAME,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    cache_dir: str | Path | None = None,
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
) -> dict[str, object]:
    """Write Google V2 public syndrome-response signatures in Stage 3A shape."""

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
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    cache_manifest: dict[str, object] | None = None
    if cache_dir is None:
        context_sources: list[GoogleLeaf | GoogleS3V2CachedContext] = _select_contexts(
            root,
            dataset_name=str(dataset_name),
            max_contexts=int(max_contexts),
            basis=basis,
            distance=distance,
            rounds=rounds,
        )
    else:
        cached, cache_manifest = load_google_s3_visible_cache_v2(cache_dir)
        context_sources = _filter_cached_contexts(cached, basis=basis, distance=distance, rounds=rounds)[: int(max_contexts)]
        if not context_sources:
            raise ValueError("no cached Google S3A V2 contexts matched the requested filters")
        _validate_cached_memberships(context_sources, round_bands=bands, region_families=regions)
    _ = np.random.default_rng(int(seed))
    replicas_by_key: dict[tuple[str, ...], list[_SignatureReplica]] = defaultdict(list)
    skipped_units: list[dict[str, object]] = []
    context_summaries: list[dict[str, object]] = []
    public_contexts: list[_PublicSignatureContext] = []
    aggregate_payload = (
        _load_aggregate_payload_from_cache(cache_dir, context_sources, round_bands=bands, region_families=regions)
        if cache_dir is not None and all(isinstance(source, GoogleS3V2CachedContext) for source in context_sources)
        else None
    )

    if aggregate_payload is not None:
        skipped_units = list(aggregate_payload.skipped_units)
        context_summaries = list(aggregate_payload.context_summaries)
        public_contexts = list(aggregate_payload.public_contexts)
        for replica in aggregate_payload.replicas:
            replicas_by_key[replica.public_key].append(replica)

    for source in ([] if aggregate_payload is not None else context_sources):
        if isinstance(source, GoogleS3V2CachedContext):
            detector_count = int(source.detector_count)
            observable_count = int(source.observable_count)
            observations = source.observations
            coords = source.coords
            boundary = set(source.boundary_detectors)
            logical_support = set(source.logical_support_detectors)
            geometry_class = str(source.patch_public_geometry_class)
            round_band_memberships = {key: set(value) for key, value in source.round_band_memberships.items()}
            region_memberships = {key: set(value) for key, value in source.region_memberships.items()}
            shotblocks = tuple(source.shotblocks)
            public_context = _PublicSignatureContext(
                dataset_name=str(source.dataset_name),
                dataset_family=str(source.dataset_family),
                basis=str(source.basis),
                distance=source.distance,
                rounds=source.rounds,
                patch_public_geometry_class=geometry_class,
            )
        else:
            leaf = source
            circuit = load_google_circuit(leaf)
            detector_count = int(circuit.num_detectors)
            observable_count = int(circuit.num_observables)
            observations = load_google_observations(leaf)
            if max_signature_shots is not None:
                observations = observations[:max_signature_shots]
            coords = _detector_coords(circuit, detector_count)
            boundary = _boundary_detectors(coords)
            logical_support = _logical_support_detectors(leaf, dem_source=str(dem_source), detector_count=detector_count)
            geometry_class = _patch_public_geometry_class(leaf, coords=coords, detector_count=detector_count, observable_count=observable_count)
            round_band_memberships = {
                band: _detectors_for_round_band(coords, detector_count=detector_count, round_band=band)
                for band in bands
            }
            region_memberships = {
                region: _detectors_for_region(
                    region,
                    detector_count=detector_count,
                    boundary_detectors=boundary,
                    logical_support_detectors=logical_support,
                    coords=coords,
                )
                for region in regions
            }
            shotblocks = tuple(
                _shotblocks(
                    shot_count=int(observations.shape[0]),
                    shotblock_size=int(shotblock_size),
                    shotblocks_per_context=int(shotblocks_per_context),
                    min_shotblock_size=minimum_block,
                )
            )
            public_context = _PublicSignatureContext(
                dataset_name=str(leaf.dataset_name),
                dataset_family=str(leaf.dataset_family),
                basis=str(leaf.basis),
                distance=None if leaf.distance is None else int(leaf.distance),
                rounds=None if leaf.rounds is None else int(leaf.rounds),
                patch_public_geometry_class=geometry_class,
            )
        public_contexts.append(public_context)
        context_unit_count = 0
        for round_band in bands:
            round_detectors = set(round_band_memberships.get(round_band, set()))
            for region in regions:
                region_detectors = set(region_memberships.get(region, set()))
                selected = sorted(set(round_detectors).intersection(region_detectors))
                if not selected:
                    skipped_units.append(
                        {
                            "reason": "empty_public_detector_selection",
                            "dataset_family": str(public_context.dataset_family),
                            "basis": str(public_context.basis),
                            "distance": public_context.distance,
                            "rounds": public_context.rounds,
                            "round_band": str(round_band),
                            "region_family": str(region),
                            "patch_public_geometry_class": geometry_class,
                        }
                    )
                    continue
                public_fields = {
                    "dataset_name": str(public_context.dataset_name),
                    "dataset_family": str(public_context.dataset_family),
                    "distance": public_context.distance,
                    "basis": str(public_context.basis),
                    "rounds": public_context.rounds,
                    "round_band": str(round_band),
                    "region_family": str(region),
                    "patch_public_geometry_class": geometry_class,
                }
                public_key = _public_key(public_fields)
                feature_row, support = _signature_feature_row(
                    observations,
                    context=public_context,
                    coords=coords,
                    boundary_detectors=boundary,
                    logical_support_detectors=logical_support,
                    selected_detectors=selected,
                    detector_count=detector_count,
                    observable_count=observable_count,
                    round_band=str(round_band),
                    region_family=str(region),
                    shotblocks=shotblocks,
                )
                replicas_by_key[public_key].append(
                    _SignatureReplica(
                        public_key=public_key,
                        public_fields=public_fields,
                        feature_row=feature_row,
                        detector_rate_mean=float(support["detector_rate_mean"]),
                        logical_rate_mean=float(support["logical_rate_mean"]),
                        shot_count=int(observations.shape[0]),
                        selected_detector_count=int(len(selected)),
                    )
                )
                context_unit_count += 1
        context_summaries.append(
            {
                "context_group_summary_only": True,
                "dataset_family": str(public_context.dataset_family),
                "basis": str(public_context.basis),
                "distance": public_context.distance,
                "rounds": public_context.rounds,
                "shot_count": int(observations.shape[0]),
                "detector_count": int(detector_count),
                "observable_count": int(observable_count),
                "public_signature_replica_count": int(context_unit_count),
                "source": "google_s3a_v2_cache" if isinstance(source, GoogleS3V2CachedContext) else "google_source_files",
            }
        )

    rows: list[np.ndarray] = []
    assignment_instances: list[dict[str, object]] = []
    signature_rows: list[dict[str, object]] = []
    replicate_rows_by_unit: list[np.ndarray] = []

    for row_idx, key in enumerate(sorted(replicas_by_key)):
        replicas = replicas_by_key[key]
        replica_matrix = np.asarray([replica.feature_row for replica in replicas], dtype=np.float64)
        row = np.mean(replica_matrix, axis=0)
        row[FEATURE_INDEX["raw__stability__context_repeated_detector_rate_variance"]] = _variance(
            [replica.detector_rate_mean for replica in replicas]
        )
        row[FEATURE_INDEX["raw__stability__context_repeated_logical_rate_variance"]] = _variance(
            [replica.logical_rate_mean for replica in replicas]
        )
        public_fields = dict(replicas[0].public_fields)
        rows.append(row)
        replicate_rows_by_unit.append(replica_matrix)
        assignment_instances.append(
            {
                "j": int(row_idx),
                "record_index": int(row_idx),
                "visible_instance_id": f"v2j{row_idx:06d}",
                "context_group": int(row_idx),
                "assignment_unit": DEFAULT_ASSIGNMENT_UNIT,
                "unit_id_internal_only": f"signature_unit_{row_idx:06d}",
                "public_fields": public_fields,
                "source_context_replicate_count": int(len(replicas)),
                "source_shot_count_total": int(sum(replica.shot_count for replica in replicas)),
                "selected_detector_count_mean": float(np.mean([replica.selected_detector_count for replica in replicas])),
            }
        )
        signature_rows.append(
            {
                "j": int(row_idx),
                "public_fields": public_fields,
                "source_context_replicate_count": int(len(replicas)),
                "source_shot_count_total": int(sum(replica.shot_count for replica in replicas)),
            }
        )

    matrix = _finite(np.asarray(rows, dtype=np.float64)) if rows else np.zeros((0, len(FEATURE_NAMES)), dtype=np.float64)
    sampled_matrix = np.array(matrix, copy=True)
    feature_schema = _feature_schema(FEATURE_NAMES)
    visible_feature_matrix = _visible_feature_matrix_manifest(matrix, sampled_matrix, feature_names=FEATURE_NAMES)
    split_manifest = _split_manifest(assignment_instances, assignment_unit=DEFAULT_ASSIGNMENT_UNIT, split_policy=str(split_policy))
    batch_schema = _batch_context_schema(split_policy=str(split_policy), row_count=int(matrix.shape[0]))
    forbidden_audit = forbidden_feature_audit_google_v2(FEATURE_NAMES)
    signature_manifest = _signature_schedule_manifest(
        signature_rows,
        round_bands=bands,
        region_families=regions,
        dem_source=str(dem_source),
    )
    adequacy = _adequacy_report(
        matrix,
        replicate_rows_by_unit=replicate_rows_by_unit,
        feature_names=FEATURE_NAMES,
        assignment_instances=assignment_instances,
        forbidden_audit=forbidden_audit,
    )
    assignment = _assignment_unit_manifest(
        row_count=int(matrix.shape[0]),
        source_context_count=int(len(context_sources)),
        round_bands=bands,
        region_families=regions,
    )
    acceptance = _acceptance_audit(
        forbidden_audit=forbidden_audit,
        split_manifest=split_manifest,
        visible_feature_matrix=visible_feature_matrix,
        adequacy_report=adequacy,
    )
    config = {
        "dataset_root": str(root),
        "dataset_name": str(dataset_name),
        "output_dir": str(output),
        "cache_dir": None if cache_dir is None else str(cache_dir),
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
        "evaluator_mode": "no_oracle_labels",
    }
    result = {
        "schema": "scope_static_google_s3a_public_syndrome_response_signature_v2",
        "stage": STAGE_NAME,
        "output_dir": str(output),
        "claim_boundary": {
            "constructs_counterfactual_teacher_probes": False,
            "uses_real_google_detection_events": True,
            "uses_real_google_obs_flips_actual": True,
            "learner_visible_surface_kind": "public syndrome-response signatures from real Google observation summaries",
            "single_window_row_surface": False,
            "context_window_timeblock_primary_unit": False,
            "contains_decoder_correctness_as_learner_input": False,
            "contains_true_hidden_mechanism_labels": False,
            "contains_catalog_m_labels": False,
            "contains_context_path_sample_one_hot_features": False,
            "evaluator_mode": "no_oracle_labels",
        },
        "config": config,
        "context_scope": {
            "dataset_name": str(dataset_name),
            "selected_context_count": int(len(context_sources)),
            "basis_counts": dict(sorted(Counter(str(context.basis) for context in public_contexts).items())),
            "distance_counts": {
                str(key): int(value)
                for key, value in sorted(Counter(context.distance for context in public_contexts).items(), key=lambda item: str(item[0]))
            },
            "rounds_counts": {
                str(key): int(value)
                for key, value in sorted(Counter(context.rounds for context in public_contexts).items(), key=lambda item: str(item[0]))
            },
            "context_summaries": context_summaries,
            "skipped_public_signature_replicas": skipped_units,
            "cache_used": cache_dir is not None,
            "aggregate_cache_used": aggregate_payload is not None,
        },
        "mechanism_scope": {
            "record_count": int(matrix.shape[0]),
            "class_count_evaluator_only": 0,
            "context_group_count": int(matrix.shape[0]),
            "mechanism_labels_evaluator_only": [],
            "no_oracle_labels": True,
        },
        "visible_feature_schema": feature_schema,
        "visible_feature_matrix": visible_feature_matrix,
        "split_manifest": split_manifest,
        "batch_context_schema": batch_schema,
        "probe_schedule_manifest": signature_manifest,
        "signature_schedule_manifest": signature_manifest,
        "forbidden_feature_audit": forbidden_audit,
        "assignment_unit": assignment,
        "adequacy_report": adequacy,
        "cache_manifest": _cache_manifest_reference(cache_dir, cache_manifest),
        "aggregate_cache_manifest": (
            aggregate_payload.reference
            if aggregate_payload is not None
            else {"aggregate_cache_used": False, "aggregate_dir": None if cache_dir is None else str(Path(cache_dir) / "aggregates")}
        ),
        "acceptance_audit": acceptance,
        "decision": "google_s3_visible_surface_v2_passed" if acceptance["passed"] else "google_s3_visible_surface_v2_failed",
    }
    _write_outputs(output, result, matrix, sampled_matrix)
    return result


def write_google_s3_visible_aggregate_cache_v2(
    *,
    cache_dir: str | Path,
    round_bands: Iterable[str] = DEFAULT_ROUND_BANDS,
    region_families: Iterable[str] = DEFAULT_REGION_FAMILIES,
    max_contexts: int | None = None,
) -> dict[str, object]:
    """Precompute V2 per-context public syndrome-response aggregate rows."""

    bands = _normalize_round_bands(round_bands)
    regions = _normalize_region_families(region_families)
    cached_contexts, cache_manifest = load_google_s3_visible_cache_v2(cache_dir)
    if max_contexts is not None:
        cached_contexts = cached_contexts[: int(max_contexts)]
    _validate_cached_memberships(cached_contexts, round_bands=bands, region_families=regions)
    root = Path(cache_dir)
    aggregate_dir = root / "aggregates"
    aggregate_dir.mkdir(parents=True, exist_ok=True)

    aggregate_contexts: list[dict[str, object]] = []
    wallclock_by_block: dict[str, float] = _zero_wallclock_blocks()
    skipped_units: list[dict[str, object]] = []
    unit_count = 0
    started = time.perf_counter()
    for context in cached_contexts:
        context_started = time.perf_counter()
        rows, unit_rows, detector_means, logical_means, selected_counts, context_timing, context_skipped = _aggregate_context_rows(
            context,
            round_bands=bands,
            region_families=regions,
        )
        for key, value in context_timing.items():
            wallclock_by_block[key] = wallclock_by_block.get(key, 0.0) + float(value)
        skipped_units.extend(context_skipped)
        arrays_name = f"aggregates/aggregate_{context.cache_context_id}.npz"
        metadata_name = f"aggregates/aggregate_{context.cache_context_id}.json"
        np.savez_compressed(
            root / arrays_name,
            feature_rows=np.asarray(rows, dtype=np.float64),
            detector_rate_means=np.asarray(detector_means, dtype=np.float64),
            logical_rate_means=np.asarray(logical_means, dtype=np.float64),
            selected_detector_counts=np.asarray(selected_counts, dtype=np.float64),
        )
        metadata = {
            "schema": "scope_static_google_s3a_v2_aggregate_context_v1",
            "cache_context_id": context.cache_context_id,
            "dataset_name": context.dataset_name,
            "dataset_family": context.dataset_family,
            "basis": context.basis,
            "distance": context.distance,
            "rounds": context.rounds,
            "patch_public_geometry_class": context.patch_public_geometry_class,
            "unit_count": int(len(unit_rows)),
            "unit_rows": unit_rows,
            "wallclock_by_block_seconds": {key: float(value) for key, value in sorted(context_timing.items())},
            "slowest_block": _slowest_block(context_timing),
            "context_wallclock_seconds": float(time.perf_counter() - context_started),
            "skipped_units": context_skipped,
        }
        (root / metadata_name).write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        aggregate_contexts.append(
            {
                "cache_context_id": context.cache_context_id,
                "arrays_path": arrays_name,
                "metadata_path": metadata_name,
                "unit_count": int(len(unit_rows)),
                "context_wallclock_seconds": float(metadata["context_wallclock_seconds"]),
                "slowest_block": metadata["slowest_block"],
            }
        )
        unit_count += int(len(unit_rows))

    wallclock_by_block["metadata_schema_writeout"] = wallclock_by_block.get("metadata_schema_writeout", 0.0)
    total_wallclock = float(time.perf_counter() - started)
    feature_audit = forbidden_feature_audit_google_v2(FEATURE_NAMES)
    manifest = {
        "schema": "scope_static_google_s3a_v2_aggregate_cache_manifest_v1",
        "schema_version": AGGREGATE_CACHE_SCHEMA_VERSION,
        "base_cache_schema_version": str(cache_manifest.get("schema_version")),
        "base_cache_config_hash": str(cache_manifest.get("config_hash")),
        "round_bands": list(bands),
        "region_families": list(regions),
        "feature_names": FEATURE_NAMES,
        "feature_names_sha256": _text_digest("\n".join(FEATURE_NAMES)),
        "context_count": int(len(cached_contexts)),
        "unit_count": int(unit_count),
        "aggregate_contexts": aggregate_contexts,
        "skipped_units": skipped_units,
        "wallclock_by_block_seconds": {key: float(value) for key, value in sorted(wallclock_by_block.items())},
        "wallclock_table": [
            {"feature_block": key, "seconds": float(value)}
            for key, value in sorted(wallclock_by_block.items(), key=lambda item: item[0])
        ],
        "slowest_block": _slowest_block(wallclock_by_block),
        "total_wallclock_seconds": total_wallclock,
        "forbidden_feature_audit": feature_audit,
        "decision": (
            "google_s3_visible_aggregate_cache_v2_passed"
            if bool(feature_audit.get("passed", False)) and unit_count > 0
            else "google_s3_visible_aggregate_cache_v2_failed"
        ),
    }
    (aggregate_dir / "aggregate_manifest.json").write_text(
        json.dumps(_json_safe(manifest), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def forbidden_feature_audit_google_v2(feature_names: Iterable[str]) -> dict[str, object]:
    names = [str(name) for name in feature_names]
    hits = [
        {"feature_name": name, "token": token}
        for name in names
        for token in FORBIDDEN_GOOGLE_V2_FEATURE_TOKENS
        if token in name.lower()
    ]
    checks = {
        "no_context_id_one_hot_features": not any("context_id" in name.lower() for name in names),
        "no_path_one_hot_features": not any("path" in name.lower() for name in names),
        "no_sample_id_one_hot_features": not any("sample_id" in name.lower() for name in names),
        "no_decoder_correctness_target": not any("decoder_correctness" in name.lower() for name in names),
        "no_catalog_or_mechanism_label": not any("catalog" in name.lower() or "mechanism" in name.lower() for name in names),
        "no_oracle_channel_fields": not any(
            token in name.lower() for name in names for token in ("oracle", "channel", "kraus", "ptm")
        ),
        "forbidden_feature_hit_count_is_zero": len(hits) == 0,
    }
    return {
        "schema": "scope_static_google_s3a_forbidden_feature_audit_v2",
        "passed": bool(all(checks.values())),
        "feature_count": int(len(names)),
        "forbidden_feature_count": int(len(hits)),
        "forbidden_feature_hits": hits,
        "checks": checks,
        "allowed_visible_inputs": [
            "empirical detector marginal rates",
            "empirical observable flip rates",
            "public detector geometry summaries",
            "public round band and region indicators",
            "empirical detector-detector covariance summaries",
            "empirical temporal covariance summaries",
            "empirical detector-logical coupling summaries",
            "finite-shot and cross-replicate stability summaries",
        ],
        "forbidden_learner_inputs": [
            "context_id one-hot",
            "path one-hot",
            "sample_id one-hot",
            "decoder correctness as learner target",
            "catalog M label",
            "true hidden mechanism label",
            "oracle PTM/Kraus/channel",
        ],
        "note": "Public dataset/region family names may appear in protocol metadata, but not as surrogate identity features.",
    }


def _aggregate_context_rows(
    context: GoogleS3V2CachedContext,
    *,
    round_bands: tuple[str, ...],
    region_families: tuple[str, ...],
) -> tuple[np.ndarray, list[dict[str, object]], list[float], list[float], list[int], dict[str, float], list[dict[str, object]]]:
    observations = context.observations
    detectors = np.asarray(context.detection_events, dtype=np.float64)
    observables = np.asarray(context.obs_flips_actual, dtype=np.float64)
    detector_rates = np.mean(detectors, axis=0) if detectors.size else np.zeros(0, dtype=np.float64)
    detector_variances = np.mean(detectors * detectors, axis=0) - detector_rates * detector_rates if detectors.size else np.zeros(0, dtype=np.float64)
    public_context = _PublicSignatureContext(
        dataset_name=context.dataset_name,
        dataset_family=context.dataset_family,
        basis=context.basis,
        distance=context.distance,
        rounds=context.rounds,
        patch_public_geometry_class=context.patch_public_geometry_class,
    )
    rows: list[np.ndarray] = []
    unit_rows: list[dict[str, object]] = []
    detector_means: list[float] = []
    logical_means: list[float] = []
    selected_counts: list[int] = []
    timing = _zero_wallclock_blocks()
    skipped: list[dict[str, object]] = []
    for round_band in round_bands:
        round_detectors = set(context.round_band_memberships.get(round_band, set()))
        for region in region_families:
            region_detectors = set(context.region_memberships.get(region, set()))
            selected = sorted(round_detectors.intersection(region_detectors))
            public_fields = {
                "dataset_name": context.dataset_name,
                "dataset_family": context.dataset_family,
                "distance": context.distance,
                "basis": context.basis,
                "rounds": context.rounds,
                "round_band": str(round_band),
                "region_family": str(region),
                "patch_public_geometry_class": context.patch_public_geometry_class,
            }
            if not selected:
                skipped.append(
                    {
                        "reason": "empty_public_detector_selection",
                        "cache_context_id": context.cache_context_id,
                        "public_fields": public_fields,
                    }
                )
                continue
            feature_row, support, local_timing = _signature_feature_row_from_arrays_with_timing(
                observations,
                detectors=detectors,
                observables=observables,
                detector_rates=detector_rates,
                detector_variances=detector_variances,
                context=public_context,
                coords=context.coords,
                boundary_detectors=set(context.boundary_detectors),
                logical_support_detectors=set(context.logical_support_detectors),
                selected_detectors=selected,
                detector_count=int(context.detector_count),
                round_band=str(round_band),
                region_family=str(region),
                shotblocks=tuple(context.shotblocks),
            )
            for key, value in local_timing.items():
                timing[key] = timing.get(key, 0.0) + float(value)
            unit_rows.append(
                {
                    "unit_index": int(len(rows)),
                    "cache_context_id": context.cache_context_id,
                    "public_fields": public_fields,
                    "selected_detector_count": int(len(selected)),
                    "source_shot_count": int(context.shot_count),
                }
            )
            rows.append(feature_row)
            detector_means.append(float(support["detector_rate_mean"]))
            logical_means.append(float(support["logical_rate_mean"]))
            selected_counts.append(int(len(selected)))
    matrix = np.asarray(rows, dtype=np.float64) if rows else np.zeros((0, len(FEATURE_NAMES)), dtype=np.float64)
    return matrix, unit_rows, detector_means, logical_means, selected_counts, timing, skipped


def _load_aggregate_payload_from_cache(
    cache_dir: str | Path,
    context_sources: list[GoogleLeaf | GoogleS3V2CachedContext],
    *,
    round_bands: tuple[str, ...],
    region_families: tuple[str, ...],
) -> _AggregatePayload | None:
    manifest_path = Path(cache_dir) / "aggregates" / "aggregate_manifest.json"
    if not manifest_path.exists():
        return None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if str(manifest.get("schema_version")) != AGGREGATE_CACHE_SCHEMA_VERSION:
        return None
    if str(manifest.get("feature_names_sha256")) != _text_digest("\n".join(FEATURE_NAMES)):
        return None
    selected_contexts = [source for source in context_sources if isinstance(source, GoogleS3V2CachedContext)]
    selected_ids = {context.cache_context_id for context in selected_contexts}
    aggregate_rows = {
        str(row.get("cache_context_id")): row
        for row in manifest.get("aggregate_contexts", [])
        if isinstance(row, dict)
    }
    if not selected_ids.issubset(set(aggregate_rows)):
        return None
    requested_bands = set(str(value) for value in round_bands)
    requested_regions = set(str(value) for value in region_families)
    replicas: list[_SignatureReplica] = []
    context_summaries: list[dict[str, object]] = []
    public_contexts: list[_PublicSignatureContext] = []
    skipped_units: list[dict[str, object]] = []
    root = Path(cache_dir)
    for context in selected_contexts:
        row = aggregate_rows[context.cache_context_id]
        arrays = np.load(root / str(row.get("arrays_path")))
        metadata = json.loads((root / str(row.get("metadata_path"))).read_text(encoding="utf-8"))
        feature_rows = np.asarray(arrays["feature_rows"], dtype=np.float64)
        detector_means = np.asarray(arrays["detector_rate_means"], dtype=np.float64)
        logical_means = np.asarray(arrays["logical_rate_means"], dtype=np.float64)
        selected_counts = np.asarray(arrays["selected_detector_counts"], dtype=np.float64)
        public_context = _PublicSignatureContext(
            dataset_name=str(metadata.get("dataset_name")),
            dataset_family=str(metadata.get("dataset_family")),
            basis=str(metadata.get("basis")),
            distance=None if metadata.get("distance") is None else int(metadata.get("distance")),
            rounds=None if metadata.get("rounds") is None else int(metadata.get("rounds")),
            patch_public_geometry_class=str(metadata.get("patch_public_geometry_class")),
        )
        public_contexts.append(public_context)
        used_unit_count = 0
        for unit in metadata.get("unit_rows", []):
            if not isinstance(unit, dict):
                continue
            public_fields = dict(unit.get("public_fields", {}))
            if str(public_fields.get("round_band")) not in requested_bands:
                continue
            if str(public_fields.get("region_family")) not in requested_regions:
                continue
            unit_idx = int(unit.get("unit_index", -1))
            if unit_idx < 0 or unit_idx >= int(feature_rows.shape[0]):
                continue
            replicas.append(
                _SignatureReplica(
                    public_key=_public_key(public_fields),
                    public_fields=public_fields,
                    feature_row=np.asarray(feature_rows[unit_idx], dtype=np.float64),
                    detector_rate_mean=float(detector_means[unit_idx]),
                    logical_rate_mean=float(logical_means[unit_idx]),
                    shot_count=int(unit.get("source_shot_count", context.shot_count)),
                    selected_detector_count=int(selected_counts[unit_idx]),
                )
            )
            used_unit_count += 1
        skipped_units.extend(
            item for item in metadata.get("skipped_units", []) if isinstance(item, dict)
        )
        context_summaries.append(
            {
                "context_group_summary_only": True,
                "source": "google_s3a_v2_aggregate_cache",
                "dataset_family": context.dataset_family,
                "basis": context.basis,
                "distance": context.distance,
                "rounds": context.rounds,
                "shot_count": int(context.shot_count),
                "detector_count": int(context.detector_count),
                "observable_count": int(context.observable_count),
                "public_signature_replica_count": int(used_unit_count),
                "aggregate_context_wallclock_seconds": float(metadata.get("context_wallclock_seconds", 0.0)),
                "aggregate_slowest_block": metadata.get("slowest_block"),
            }
        )
    if not replicas:
        return None
    return _AggregatePayload(
        replicas=replicas,
        context_summaries=context_summaries,
        skipped_units=skipped_units,
        public_contexts=public_contexts,
        reference=_aggregate_manifest_reference(cache_dir, manifest),
    )


def _filter_cached_contexts(
    contexts: list[GoogleS3V2CachedContext],
    *,
    basis: str | None,
    distance: int | None,
    rounds: int | None,
) -> list[GoogleS3V2CachedContext]:
    out = []
    for context in contexts:
        if basis is not None and str(context.basis).upper() != str(basis).upper():
            continue
        if distance is not None and context.distance != int(distance):
            continue
        if rounds is not None and context.rounds != int(rounds):
            continue
        out.append(context)
    return out


def _validate_cached_memberships(
    contexts: list[GoogleS3V2CachedContext],
    *,
    round_bands: tuple[str, ...],
    region_families: tuple[str, ...],
) -> None:
    missing_bands = sorted(
        {
            band
            for context in contexts
            for band in round_bands
            if band not in context.round_band_memberships
        }
    )
    missing_regions = sorted(
        {
            region
            for context in contexts
            for region in region_families
            if region not in context.region_memberships
        }
    )
    if missing_bands or missing_regions:
        raise ValueError(
            "cached Google S3A V2 precompute is missing requested public memberships: "
            f"round_bands={missing_bands!r}, region_families={missing_regions!r}"
        )


def _cache_manifest_reference(cache_dir: str | Path | None, manifest: dict[str, object] | None) -> dict[str, object]:
    if cache_dir is None or manifest is None:
        return {
            "cache_used": False,
            "cache_dir": None,
        }
    return {
        "cache_used": True,
        "cache_dir": str(cache_dir),
        "schema_version": str(manifest.get("schema_version")),
        "config_hash": str(manifest.get("config_hash")),
        "context_count": int(manifest.get("context_count", 0)),
        "shot_count": int(manifest.get("shot_count", 0)),
        "source_file_manifest_sha256": str(manifest.get("source_file_manifest_sha256", "")),
        "forbidden_feature_audit_passed": bool(dict(manifest.get("forbidden_feature_audit", {})).get("passed", False)),
    }


def _aggregate_manifest_reference(cache_dir: str | Path, manifest: dict[str, object]) -> dict[str, object]:
    return {
        "aggregate_cache_used": True,
        "aggregate_dir": str(Path(cache_dir) / "aggregates"),
        "schema_version": str(manifest.get("schema_version")),
        "base_cache_config_hash": str(manifest.get("base_cache_config_hash", "")),
        "context_count": int(manifest.get("context_count", 0)),
        "unit_count": int(manifest.get("unit_count", 0)),
        "slowest_block": manifest.get("slowest_block"),
        "wallclock_by_block_seconds": dict(manifest.get("wallclock_by_block_seconds", {})),
        "wallclock_table": list(manifest.get("wallclock_table", [])),
        "forbidden_feature_audit_passed": bool(dict(manifest.get("forbidden_feature_audit", {})).get("passed", False)),
    }


def _zero_wallclock_blocks() -> dict[str, float]:
    return {
        "marginal": 0.0,
        "spatial_corr": 0.0,
        "temporal_corr": 0.0,
        "logical_coupling": 0.0,
        "stability": 0.0,
        "metadata_schema_writeout": 0.0,
    }


def _slowest_block(timings: dict[str, float]) -> dict[str, object]:
    if not timings:
        return {"feature_block": None, "seconds": 0.0}
    name, seconds = max(timings.items(), key=lambda item: float(item[1]))
    return {"feature_block": str(name), "seconds": float(seconds)}


def _signature_feature_row(
    observations: np.ndarray,
    *,
    context: _PublicSignatureContext,
    coords: dict[int, tuple[float, ...]],
    boundary_detectors: set[int],
    logical_support_detectors: set[int],
    selected_detectors: list[int],
    detector_count: int,
    observable_count: int,
    round_band: str,
    region_family: str,
    shotblocks: tuple[tuple[int, int], ...],
) -> tuple[np.ndarray, dict[str, float]]:
    row, support, _timing = _signature_feature_row_with_timing(
        observations,
        context=context,
        coords=coords,
        boundary_detectors=boundary_detectors,
        logical_support_detectors=logical_support_detectors,
        selected_detectors=selected_detectors,
        detector_count=detector_count,
        observable_count=observable_count,
        round_band=round_band,
        region_family=region_family,
        shotblocks=shotblocks,
    )
    return row, support


def _signature_feature_row_with_timing(
    observations: np.ndarray,
    *,
    context: _PublicSignatureContext,
    coords: dict[int, tuple[float, ...]],
    boundary_detectors: set[int],
    logical_support_detectors: set[int],
    selected_detectors: list[int],
    detector_count: int,
    observable_count: int,
    round_band: str,
    region_family: str,
    shotblocks: tuple[tuple[int, int], ...],
) -> tuple[np.ndarray, dict[str, float], dict[str, float]]:
    detectors = np.asarray(observations[:, :detector_count], dtype=np.float64)
    observables = np.asarray(observations[:, detector_count : detector_count + observable_count], dtype=np.float64)
    detector_rates = np.mean(detectors, axis=0) if detectors.size else np.zeros(0, dtype=np.float64)
    detector_variances = np.mean(detectors * detectors, axis=0) - detector_rates * detector_rates if detectors.size else np.zeros(0, dtype=np.float64)
    return _signature_feature_row_from_arrays_with_timing(
        observations,
        detectors=detectors,
        observables=observables,
        detector_rates=detector_rates,
        detector_variances=detector_variances,
        context=context,
        coords=coords,
        boundary_detectors=boundary_detectors,
        logical_support_detectors=logical_support_detectors,
        selected_detectors=selected_detectors,
        detector_count=detector_count,
        round_band=round_band,
        region_family=region_family,
        shotblocks=shotblocks,
    )


def _signature_feature_row_from_arrays_with_timing(
    observations: np.ndarray,
    *,
    detectors: np.ndarray,
    observables: np.ndarray,
    detector_rates: np.ndarray,
    detector_variances: np.ndarray,
    context: _PublicSignatureContext,
    coords: dict[int, tuple[float, ...]],
    boundary_detectors: set[int],
    logical_support_detectors: set[int],
    selected_detectors: list[int],
    detector_count: int,
    round_band: str,
    region_family: str,
    shotblocks: tuple[tuple[int, int], ...],
) -> tuple[np.ndarray, dict[str, float], dict[str, float]]:
    selected = [int(idx) for idx in selected_detectors if 0 <= int(idx) < detector_count]
    selected_matrix = detectors[:, selected] if selected else np.zeros((detectors.shape[0], 0), dtype=np.float64)
    logical_per_shot = np.mean(observables, axis=1) if observables.size else np.zeros(detectors.shape[0], dtype=np.float64)

    timings: dict[str, float] = {}
    start = time.perf_counter()
    marginal = _marginal_features(
        detectors,
        observables,
        selected=selected,
        selected_matrix=selected_matrix,
        coords=coords,
        boundary_detectors=boundary_detectors,
    )
    timings["marginal"] = time.perf_counter() - start
    start = time.perf_counter()
    spatial = _spatial_corr_features(
        detectors,
        selected=selected,
        coords=coords,
        boundary_detectors=boundary_detectors,
        detector_rates=detector_rates,
        detector_variances=detector_variances,
    )
    timings["spatial_corr"] = time.perf_counter() - start
    start = time.perf_counter()
    temporal = _temporal_corr_features(
        detectors,
        selected=selected,
        coords=coords,
        detector_rates=detector_rates,
        detector_variances=detector_variances,
    )
    timings["temporal_corr"] = time.perf_counter() - start
    start = time.perf_counter()
    logical = _logical_coupling_features(detectors, observables, selected=selected)
    timings["logical_coupling"] = time.perf_counter() - start
    start = time.perf_counter()
    stability = _stability_features(
        observations,
        detector_count=detector_count,
        selected=selected,
        shotblocks=shotblocks,
    )
    timings["stability"] = time.perf_counter() - start
    start = time.perf_counter()
    public_geometry = _public_geometry_features(
        context=context,
        detector_count=detector_count,
        observable_count=int(observables.shape[1]),
        selected=selected,
        coords=coords,
        boundary_detectors=boundary_detectors,
        logical_support_detectors=logical_support_detectors,
        round_band=str(round_band),
        region_family=str(region_family),
        shot_count=int(observations.shape[0]),
    )
    timings["metadata_schema_writeout"] = time.perf_counter() - start
    row = np.asarray([*marginal, *spatial, *temporal, *logical, *stability, *public_geometry], dtype=np.float64)
    support = {
        "detector_rate_mean": float(np.mean(selected_matrix)) if selected_matrix.size else 0.0,
        "logical_rate_mean": float(np.mean(logical_per_shot)) if logical_per_shot.size else 0.0,
    }
    return row, support, timings


def _marginal_features(
    detectors: np.ndarray,
    observables: np.ndarray,
    *,
    selected: list[int],
    selected_matrix: np.ndarray,
    coords: dict[int, tuple[float, ...]],
    boundary_detectors: set[int],
) -> list[float]:
    rates = np.mean(selected_matrix, axis=0) if selected_matrix.size else np.zeros(0, dtype=np.float64)
    obs_rates = np.mean(observables, axis=0) if observables.size else np.zeros(0, dtype=np.float64)
    boundary_selected = [idx for idx in selected if idx in boundary_detectors]
    bulk_selected = [idx for idx in selected if idx not in boundary_detectors]
    boundary_rate = float(np.mean(detectors[:, boundary_selected])) if boundary_selected else 0.0
    bulk_rate = float(np.mean(detectors[:, bulk_selected])) if bulk_selected else 0.0
    slope = _rate_slope_by_t(rates, selected=selected, coords=coords)
    return [
        _mean(rates),
        _std(rates),
        _min(rates),
        _max(rates),
        _quantile(rates, 0.25),
        _quantile(rates, 0.75),
        _mean(obs_rates),
        _max(obs_rates),
        boundary_rate,
        bulk_rate,
        slope,
        _mean([_binary_entropy(value) for value in rates]),
    ]


def _spatial_corr_features(
    detectors: np.ndarray,
    *,
    selected: list[int],
    coords: dict[int, tuple[float, ...]],
    boundary_detectors: set[int],
    detector_rates: np.ndarray | None = None,
    detector_variances: np.ndarray | None = None,
) -> list[float]:
    pairs = _nearest_neighbor_pairs(selected, coords)
    covs, corrs = _pair_cov_corr(detectors, pairs, detector_rates=detector_rates, detector_variances=detector_variances)
    boundary_selected = [idx for idx in selected if idx in boundary_detectors]
    bulk_selected = [idx for idx in selected if idx not in boundary_detectors]
    boundary_rate = float(np.mean(detectors[:, boundary_selected])) if boundary_selected else 0.0
    bulk_rate = float(np.mean(detectors[:, bulk_selected])) if bulk_selected else 0.0
    return [
        _mean(covs),
        _std(covs),
        _max_abs(covs),
        _mean(corrs),
        _std(corrs),
        boundary_rate - bulk_rate,
        float(len(pairs)) / max(float(len(selected)), 1.0),
    ]


def _temporal_corr_features(
    detectors: np.ndarray,
    *,
    selected: list[int],
    coords: dict[int, tuple[float, ...]],
    detector_rates: np.ndarray | None = None,
    detector_variances: np.ndarray | None = None,
) -> list[float]:
    pairs = _temporal_pairs(selected, coords)
    covs, corrs = _pair_cov_corr(detectors, pairs, detector_rates=detector_rates, detector_variances=detector_variances)
    layer_rates = _layer_rate_summary(detectors, selected=selected, coords=coords)
    early = layer_rates.get("early", 0.0)
    mid = layer_rates.get("mid", 0.0)
    late = layer_rates.get("late", 0.0)
    return [
        _mean(covs),
        _std(covs),
        _mean(corrs),
        _std(corrs),
        mid - early,
        late - mid,
        late - early,
        float(len(pairs)) / max(float(len(selected)), 1.0),
    ]


def _logical_coupling_features(detectors: np.ndarray, observables: np.ndarray, *, selected: list[int]) -> list[float]:
    if not selected or observables.size == 0:
        return [0.0] * len(LOGICAL_COUPLING_FEATURE_NAMES)
    selected_arr = np.asarray(selected, dtype=np.int64)
    x = np.asarray(detectors[:, selected_arr], dtype=np.float64)
    x_rate = np.mean(x, axis=0)
    x_var = np.mean(x * x, axis=0) - x_rate * x_rate
    covs: list[np.ndarray] = []
    corrs: list[np.ndarray] = []
    diffs: list[np.ndarray] = []
    for obs_idx in range(observables.shape[1]):
        y = np.asarray(observables[:, obs_idx], dtype=np.float64)
        y_rate = float(np.mean(y))
        y_var = float(np.mean(y * y) - y_rate * y_rate)
        cov = np.mean(x * y[:, None], axis=0) - x_rate * y_rate
        denom = np.sqrt(np.maximum(x_var * y_var, 0.0))
        corr = np.divide(cov, denom, out=np.zeros_like(cov), where=denom > 0.0)
        mask_one = y >= 0.5
        mask_zero = ~mask_one
        if bool(np.any(mask_one)) and bool(np.any(mask_zero)):
            diff = np.mean(x[mask_one], axis=0) - np.mean(x[mask_zero], axis=0)
        else:
            diff = np.zeros_like(x_rate)
        covs.append(cov)
        corrs.append(corr)
        diffs.append(diff)
    cov_arr = np.concatenate(covs) if covs else np.zeros(0, dtype=np.float64)
    corr_arr = np.concatenate(corrs) if corrs else np.zeros(0, dtype=np.float64)
    diff_arr = np.concatenate(diffs) if diffs else np.zeros(0, dtype=np.float64)
    return [
        _mean(cov_arr),
        _std(cov_arr),
        _max_abs(cov_arr),
        _mean(corr_arr),
        _mean(diff_arr),
        _std(diff_arr),
        _max_abs(diff_arr),
        float(cov_arr.size) / max(float(len(selected)), 1.0),
    ]


def _stability_features(
    observations: np.ndarray,
    *,
    detector_count: int,
    selected: list[int],
    shotblocks: tuple[tuple[int, int], ...],
) -> list[float]:
    if not shotblocks:
        shotblocks = ((0, int(observations.shape[0])),)
    detector_block_rates: list[float] = []
    logical_block_rates: list[float] = []
    selected_arr = np.asarray(selected, dtype=np.int64)
    for start, stop in shotblocks:
        block = np.asarray(observations[start:stop], dtype=np.float64)
        det = block[:, selected_arr] if selected_arr.size else np.zeros((block.shape[0], 0), dtype=np.float64)
        obs = block[:, detector_count:]
        detector_block_rates.append(float(np.mean(det)) if det.size else 0.0)
        logical_block_rates.append(float(np.mean(obs)) if obs.size else 0.0)
    detector_rate = _mean(detector_block_rates)
    logical_rate = _mean(logical_block_rates)
    n = max(float(observations.shape[0]), 1.0)
    return [
        _variance(detector_block_rates),
        _variance(logical_block_rates),
        math.sqrt(max(0.0, detector_rate * (1.0 - detector_rate)) / n),
        math.sqrt(max(0.0, logical_rate * (1.0 - logical_rate)) / n),
        _std(detector_block_rates) / math.sqrt(max(float(len(detector_block_rates)), 1.0)),
        _std(logical_block_rates) / math.sqrt(max(float(len(logical_block_rates)), 1.0)),
        0.0,
        0.0,
    ]


def _public_geometry_features(
    *,
    context: _PublicSignatureContext,
    detector_count: int,
    observable_count: int,
    selected: list[int],
    coords: dict[int, tuple[float, ...]],
    boundary_detectors: set[int],
    logical_support_detectors: set[int],
    round_band: str,
    region_family: str,
    shot_count: int,
) -> list[float]:
    spans = _coord_spans(coords)
    return [
        1.0 if str(context.dataset_family) == "surface" else 0.0,
        1.0 if str(context.basis).upper() == "X" else 0.0,
        1.0 if str(context.basis).upper() == "Z" else 0.0,
        float(context.distance if context.distance is not None else 0),
        float(context.rounds if context.rounds is not None else 0),
        1.0 if round_band == "early" else 0.0,
        1.0 if round_band == "mid" else 0.0,
        1.0 if round_band == "late" else 0.0,
        1.0 if round_band == "all" else 0.0,
        1.0 if region_family == "boundary_adjacent" else 0.0,
        1.0 if region_family == "bulk" else 0.0,
        1.0 if region_family == "logical_support_neighborhood" else 0.0,
        1.0 if region_family == "interior_chain" else 0.0,
        1.0 if region_family == "full_patch" else 0.0,
        float(detector_count),
        float(observable_count),
        float(len(selected)) / max(float(detector_count), 1.0),
        float(len([idx for idx in selected if idx in boundary_detectors])) / max(float(len(selected)), 1.0),
        float(len([idx for idx in selected if idx in logical_support_detectors])) / max(float(len(selected)), 1.0),
        spans["x_span"],
        spans["y_span"],
        spans["t_span"],
        float(shot_count),
    ]


def _logical_support_detectors(leaf: GoogleLeaf, *, dem_source: str, detector_count: int) -> set[int]:
    if leaf.dataset_name != DATASET_SURFACE_SET1:
        return set(range(int(detector_count)))
    try:
        support_surface = _load_dem_support_surface(leaf, dem_source=str(dem_source))
    except (FileNotFoundError, ValueError):
        return set(range(int(detector_count)))
    out: set[int] = set()
    observable_bits = range(int(support_surface.num_detectors), int(support_surface.num_detectors + support_surface.num_observables))
    for logical_bit in observable_bits:
        for fault in support_surface.faults_by_observation_bit[int(logical_bit)]:
            for bit in support_surface.supports_by_fault[int(fault)]:
                if int(bit) < int(detector_count):
                    out.add(int(bit))
    return out or set(range(int(detector_count)))


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


def _public_key(public_fields: dict[str, object]) -> tuple[str, ...]:
    return (
        str(public_fields.get("dataset_name")),
        str(public_fields.get("dataset_family")),
        str(public_fields.get("distance")),
        str(public_fields.get("basis")),
        str(public_fields.get("rounds")),
        str(public_fields.get("patch_public_geometry_class")),
        str(public_fields.get("round_band")),
        str(public_fields.get("region_family")),
    )


def _feature_schema(feature_names: list[str]) -> dict[str, object]:
    features = []
    for idx, name in enumerate(feature_names):
        features.append(
            {
                "index": int(idx),
                "name": str(name),
                "kind": _feature_kind(name),
                "feature_block": _feature_block(name),
                "learner_visible": True,
                "source": _feature_source(name),
            }
        )
    block_counts = Counter(_feature_block(name) for name in feature_names)
    return {
        "schema": "scope_static_google_s3a_public_syndrome_response_feature_schema_v2",
        "stage": STAGE_NAME,
        "claim_boundary": "Real Google data provide public syndrome-response signatures, not counterfactual teacher probe responses.",
        "assignment_unit": DEFAULT_ASSIGNMENT_UNIT,
        "fixed_window_bits": None,
        "raw_feature_count": int(sum(1 for name in feature_names if name.startswith("raw__"))),
        "metadata_feature_count": int(sum(1 for name in feature_names if name.startswith("meta__"))),
        "feature_block_counts": dict(sorted(block_counts.items())),
        "num_features": int(len(feature_names)),
        "features": features,
    }


def _visible_feature_matrix_manifest(matrix: np.ndarray, sampled: np.ndarray, *, feature_names: list[str]) -> dict[str, object]:
    return {
        "schema": "scope_static_stage3a_visible_feature_matrix_v1",
        "training_matrix_path": "visible_features.npy",
        "training_matrix_kind": "empirical_google_public_syndrome_response_signature_features",
        "sampled_matrix_path": "sampled_visible_features.npy",
        "sampled_matrix_kind": "same_empirical_google_public_syndrome_response_signature_features",
        "feature_schema_path": "visible_feature_schema.json",
        "feature_count": int(matrix.shape[1]) if matrix.ndim == 2 else 0,
        "record_count": int(matrix.shape[0]) if matrix.ndim == 2 else 0,
        "shape": [int(dim) for dim in matrix.shape],
        "sampled_shape": [int(dim) for dim in sampled.shape],
        "sampling_mode": "real_google_empirical_public_syndrome_response_signatures",
        "feature_names_sha256": _text_digest("\n".join(feature_names)),
        "visible_features_sha256": _matrix_digest(matrix),
        "sampled_visible_features_sha256": _matrix_digest(sampled),
        "learner_training_source": "Google S3A-real V2 frozen visible_features.npy",
        "contains_evaluator_labels": False,
        "contains_oracle_fields": False,
        "contains_context_path_sample_one_hot_features": False,
    }


def _split_manifest(
    assignment_instances: list[dict[str, object]],
    *,
    assignment_unit: str,
    split_policy: str,
) -> dict[str, object]:
    groups = [int(row.get("context_group", idx)) for idx, row in enumerate(assignment_instances)]
    folds = []
    for fold_idx, test_group in enumerate(groups):
        validation_groups = [int(groups[(fold_idx + 1) % len(groups)])] if len(groups) >= 3 else []
        train_groups = [int(group) for group in groups if group not in {int(test_group), *validation_groups}]
        folds.append(
            {
                "fold": int(fold_idx),
                "train_groups": train_groups,
                "validation_groups": validation_groups,
                "test_groups": [int(test_group)],
                "train_indices": _indices_for_groups(assignment_instances, train_groups),
                "validation_indices": _indices_for_groups(assignment_instances, validation_groups),
                "test_indices": _indices_for_groups(assignment_instances, [int(test_group)]),
            }
        )
    non_empty = bool(
        groups
        and all(row["train_indices"] for row in folds)
        and all(row["validation_indices"] for row in folds)
        and all(row["test_indices"] for row in folds)
    )
    return {
        "schema": "scope_static_stage3a_split_manifest_v1",
        "split_policy": str(split_policy),
        "split_policy_fixed_before_training": True,
        "group_key": "google_public_syndrome_response_signature_group",
        "assignment_unit": str(assignment_unit),
        "record_count": int(len(assignment_instances)),
        "context_groups": groups,
        "fold_count": int(len(folds)),
        "folds": folds,
        "assignment_instances": assignment_instances,
        "contains_mechanism_labels_as_learner_fields": False,
        "validation_labels_available_to_model_selection": False,
        "test_labels_available_to_model_selection": False,
        "train_validation_test_splits_non_empty": non_empty,
    }


def _batch_context_schema(*, split_policy: str, row_count: int) -> dict[str, object]:
    return {
        "schema": "scope_static_stage3a_batch_context_schema_v1",
        "assignment_unit": DEFAULT_ASSIGNMENT_UNIT,
        "split_policy": str(split_policy),
        "primary_protocol": {
            "mode": "google_real_public_syndrome_response_signature_batch",
            "context_group_key": "google_public_syndrome_response_signature_group",
            "context_group_count": int(row_count),
        },
        "learner_visible_fields": [
            "raw__marginal__*",
            "raw__spatial_corr__*",
            "raw__temporal_corr__*",
            "raw__logical_coupling__*",
            "raw__stability__*",
            "meta__public_geometry__*",
        ],
        "protocol_only_fields": ["j", "fold", "train_validation_test_split", "public_fields", "unit_id_internal_only"],
        "evaluator_only_fields": [
            "optional_decoder_facing_proxy_metrics",
            "optional_local_full_baseline_metrics",
            "optional_dmle_qec_baseline_metrics",
        ],
        "forbidden_learner_fields": [
            "context_id",
            "path",
            "sample_id",
            "decoder_correctness",
            "catalog_M_label",
            "true_hidden_mechanism_label",
            "oracle_channel_ptm_kraus",
        ],
    }


def _signature_schedule_manifest(
    signature_rows: list[dict[str, object]],
    *,
    round_bands: tuple[str, ...],
    region_families: tuple[str, ...],
    dem_source: str,
) -> dict[str, object]:
    region_counts = Counter(str(dict(row.get("public_fields", {})).get("region_family")) for row in signature_rows)
    band_counts = Counter(str(dict(row.get("public_fields", {})).get("round_band")) for row in signature_rows)
    return {
        "schema": "scope_static_google_s3a_signature_schedule_manifest_v2",
        "source": "public Google circuit, DEM, geometry, round, and region structure",
        "dem_source_for_public_logical_support_neighborhood": str(dem_source),
        "assignment_unit": DEFAULT_ASSIGNMENT_UNIT,
        "round_bands": list(round_bands),
        "region_families": list(region_families),
        "signature_unit_count": int(len(signature_rows)),
        "round_band_counts": dict(sorted(band_counts.items())),
        "region_family_counts": dict(sorted(region_counts.items())),
        "selection_policy": [
            "group by dataset, distance, basis, public patch geometry class, round band, and region family",
            "aggregate detector/logical response summaries across matching real Google contexts",
            "do not expose context path, sample id, raw sample index, decoder correctness, or mechanism-like labels",
        ],
        "examples": signature_rows[: min(50, len(signature_rows))],
    }


def _assignment_unit_manifest(
    *,
    row_count: int,
    source_context_count: int,
    round_bands: tuple[str, ...],
    region_families: tuple[str, ...],
) -> dict[str, object]:
    return {
        "schema": "scope_static_stage3a_assignment_unit_v1",
        "assignment_matrix": "S[j,k] or Pi[j,k]",
        "j_definition": DEFAULT_ASSIGNMENT_UNIT,
        "j_description": (
            "One public syndrome-response unit keyed by dataset, distance, basis, public patch geometry class, "
            "round band, and region family; not a single shot, context ID, path, or fixed 2-bit window row."
        ),
        "single_shot_j_allowed_first_pass": False,
        "k_definition": "learned latent visible syndrome-response regime; no Google oracle mechanism labels are available",
        "record_count": int(row_count),
        "source_context_count": int(source_context_count),
        "round_bands": list(round_bands),
        "region_families": list(region_families),
        "expected_categorical_population_group_count_per_row": 0,
        "catalog_cardinality_evaluator_only": 0,
        "evaluator_mode": "no_oracle_labels",
    }


def _adequacy_report(
    matrix: np.ndarray,
    *,
    replicate_rows_by_unit: list[np.ndarray],
    feature_names: list[str],
    assignment_instances: list[dict[str, object]],
    forbidden_audit: dict[str, object],
) -> dict[str, object]:
    block_indices = _block_indices(feature_names)
    entropy_by_block = {
        block: _mean([_histogram_entropy(matrix[:, idx]) for idx in indices]) if matrix.size else 0.0
        for block, indices in block_indices.items()
    }
    between_var = {
        block: float(np.mean(np.var(matrix[:, indices], axis=0))) if matrix.shape[0] > 0 and indices else 0.0
        for block, indices in block_indices.items()
    }
    within_var = {}
    for block, indices in block_indices.items():
        values = []
        for replica_matrix in replicate_rows_by_unit:
            if replica_matrix.shape[0] >= 2 and indices:
                values.append(float(np.mean(np.var(replica_matrix[:, indices], axis=0))))
        within_var[block] = _mean(values)
    public_rows = [dict(row.get("public_fields", {})) for row in assignment_instances]
    logical_indices = block_indices.get("raw__logical_coupling", [])
    logical_strength = float(np.mean(np.abs(matrix[:, logical_indices]))) if matrix.shape[0] > 0 and logical_indices else 0.0
    checks = {
        "row_count_positive": int(matrix.shape[0]) > 0,
        "feature_blocks_present": all(block in block_indices for block in _required_raw_blocks()),
        "forbidden_feature_audit_passed": bool(forbidden_audit.get("passed", False)),
        "round_basis_region_coverage_present": bool(public_rows),
    }
    return {
        "schema": "scope_static_google_s3a_signature_adequacy_report_v2",
        "passed": bool(all(checks.values())),
        "checks": checks,
        "row_count": int(matrix.shape[0]),
        "feature_count": int(matrix.shape[1]) if matrix.ndim == 2 else 0,
        "feature_block_counts": {block: int(len(indices)) for block, indices in sorted(block_indices.items())},
        "entropy_per_block": {key: float(value) for key, value in sorted(entropy_by_block.items())},
        "between_unit_variance_per_block": {key: float(value) for key, value in sorted(between_var.items())},
        "within_unit_replicate_variance_per_block": {key: float(value) for key, value in sorted(within_var.items())},
        "logical_coupling_signal_strength_mean_abs": logical_strength,
        "coverage": {
            "basis_counts": dict(sorted(Counter(str(row.get("basis")) for row in public_rows).items())),
            "round_band_counts": dict(sorted(Counter(str(row.get("round_band")) for row in public_rows).items())),
            "region_family_counts": dict(sorted(Counter(str(row.get("region_family")) for row in public_rows).items())),
            "distance_counts": dict(sorted(Counter(str(row.get("distance")) for row in public_rows).items())),
        },
        "claim_boundary": "Adequacy is reported before S3B/S3C training; it is not a learner result.",
    }


def _acceptance_audit(
    *,
    forbidden_audit: dict[str, object],
    split_manifest: dict[str, object],
    visible_feature_matrix: dict[str, object],
    adequacy_report: dict[str, object],
) -> dict[str, object]:
    checks = {
        "no_forbidden_learner_fields": bool(forbidden_audit.get("passed", False)),
        "split_policy_fixed_before_model_training": bool(split_manifest.get("split_policy_fixed_before_training", False)),
        "train_validation_test_splits_non_empty": bool(split_manifest.get("train_validation_test_splits_non_empty", False)),
        "assignment_unit_declared_before_training": True,
        "single_shot_assignment_not_used_first_pass": True,
        "frozen_visible_feature_matrix_declared": bool(visible_feature_matrix.get("training_matrix_path")),
        "frozen_visible_feature_matrix_has_no_labels": not bool(visible_feature_matrix.get("contains_evaluator_labels", True)),
        "frozen_visible_feature_matrix_has_no_oracle_fields": not bool(visible_feature_matrix.get("contains_oracle_fields", True)),
        "frozen_visible_feature_matrix_has_no_context_path_sample_one_hot": not bool(
            visible_feature_matrix.get("contains_context_path_sample_one_hot_features", True)
        ),
        "adequacy_report_passed_before_training": bool(adequacy_report.get("passed", False)),
        "learner_training_not_run_in_stage3a": True,
    }
    return {
        "schema": "scope_static_google_s3a_signature_acceptance_audit_v2",
        "passed": bool(all(checks.values())),
        "checks": checks,
    }


def _feature_kind(name: str) -> str:
    if name.startswith("raw__marginal__"):
        return "raw_google_syndrome_response_marginal"
    if name.startswith("raw__spatial_corr__"):
        return "raw_google_syndrome_response_spatial_correlation"
    if name.startswith("raw__temporal_corr__"):
        return "raw_google_syndrome_response_temporal_correlation"
    if name.startswith("raw__logical_coupling__"):
        return "raw_google_syndrome_response_logical_coupling"
    if name.startswith("raw__stability__"):
        return "raw_google_syndrome_response_stability"
    if name.startswith("meta__public_geometry__"):
        return "allowed_google_public_geometry_metadata"
    return "unknown"


def _feature_source(name: str) -> str:
    if name.startswith("meta__"):
        return "public Google circuit, geometry, basis, distance, round, and region metadata"
    return "Google detection_events.b8 and obs_flips_actual.b8 empirical syndrome-response summaries"


def _feature_block(name: str) -> str:
    parts = str(name).split("__")
    return "__".join(parts[:2]) if len(parts) >= 2 else str(name)


def _block_indices(feature_names: list[str]) -> dict[str, list[int]]:
    out: dict[str, list[int]] = defaultdict(list)
    for idx, name in enumerate(feature_names):
        out[_feature_block(name)].append(int(idx))
    return dict(out)


def _required_raw_blocks() -> tuple[str, ...]:
    return (
        "raw__marginal",
        "raw__spatial_corr",
        "raw__temporal_corr",
        "raw__logical_coupling",
        "raw__stability",
    )


def _nearest_neighbor_pairs(selected: list[int], coords: dict[int, tuple[float, ...]]) -> list[tuple[int, int]]:
    if len(selected) < 2:
        return []
    padded = {idx: _pad_coord(coords[idx]) for idx in selected if idx in coords}
    if len(padded) < 2:
        ordered = sorted(selected)
        return [(left, right) for left, right in zip(ordered, ordered[1:])]
    distances = []
    for left_idx, left in enumerate(sorted(padded)):
        for right in sorted(padded)[left_idx + 1 :]:
            distance = max(abs(a - b) for a, b in zip(padded[left], padded[right]))
            if distance > 0.0:
                distances.append((distance, left, right))
    if not distances:
        return []
    min_distance = min(item[0] for item in distances)
    return [(left, right) for distance, left, right in distances if math.isclose(distance, min_distance) or distance <= min_distance * 1.5]


def _temporal_pairs(selected: list[int], coords: dict[int, tuple[float, ...]]) -> list[tuple[int, int]]:
    by_xy: dict[tuple[float, float], list[tuple[float, int]]] = defaultdict(list)
    for idx in selected:
        if idx not in coords:
            continue
        x_coord, y_coord, t_coord = _pad_coord(coords[idx])
        by_xy[(round(x_coord, 6), round(y_coord, 6))].append((t_coord, int(idx)))
    out = []
    for values in by_xy.values():
        ordered = [idx for _time, idx in sorted(values)]
        out.extend((left, right) for left, right in zip(ordered, ordered[1:]))
    return out


def _pair_cov_corr(
    detectors: np.ndarray,
    pairs: list[tuple[int, int]],
    *,
    detector_rates: np.ndarray | None = None,
    detector_variances: np.ndarray | None = None,
) -> tuple[list[float], list[float]]:
    if not pairs or detectors.size == 0:
        return [], []
    pair_arr = np.asarray(
        [(int(left), int(right)) for left, right in pairs if int(left) < detectors.shape[1] and int(right) < detectors.shape[1]],
        dtype=np.int64,
    )
    if pair_arr.size == 0:
        return [], []
    rates = np.asarray(detector_rates, dtype=np.float64) if detector_rates is not None else np.mean(detectors, axis=0)
    variances = (
        np.asarray(detector_variances, dtype=np.float64)
        if detector_variances is not None
        else np.mean(detectors * detectors, axis=0) - rates * rates
    )
    cov_chunks: list[np.ndarray] = []
    corr_chunks: list[np.ndarray] = []
    for start in range(0, int(pair_arr.shape[0]), 1024):
        chunk = pair_arr[start : start + 1024]
        left = chunk[:, 0]
        right = chunk[:, 1]
        xy_mean = np.mean(detectors[:, left] * detectors[:, right], axis=0)
        cov = xy_mean - rates[left] * rates[right]
        denom = np.sqrt(np.maximum(variances[left] * variances[right], 0.0))
        corr = np.divide(cov, denom, out=np.zeros_like(cov), where=denom > 0.0)
        cov_chunks.append(cov)
        corr_chunks.append(corr)
    covs = np.concatenate(cov_chunks) if cov_chunks else np.zeros(0, dtype=np.float64)
    corrs = np.concatenate(corr_chunks) if corr_chunks else np.zeros(0, dtype=np.float64)
    return covs.tolist(), corrs.tolist()


def _layer_rate_summary(detectors: np.ndarray, *, selected: list[int], coords: dict[int, tuple[float, ...]]) -> dict[str, float]:
    out = {}
    for band in ("early", "mid", "late"):
        band_detectors = sorted(set(selected).intersection(_detectors_for_round_band(coords, detector_count=detectors.shape[1], round_band=band)))
        out[band] = float(np.mean(detectors[:, band_detectors])) if band_detectors else 0.0
    return out


def _rate_slope_by_t(rates: np.ndarray, *, selected: list[int], coords: dict[int, tuple[float, ...]]) -> float:
    if len(selected) != len(rates) or len(selected) < 2:
        return 0.0
    xs = []
    ys = []
    for idx, rate in zip(selected, rates.tolist()):
        if idx not in coords:
            continue
        xs.append(_pad_coord(coords[idx])[2])
        ys.append(float(rate))
    if len(set(round(value, 6) for value in xs)) < 2:
        return 0.0
    coeff = np.polyfit(np.asarray(xs, dtype=np.float64), np.asarray(ys, dtype=np.float64), deg=1)
    return float(coeff[0])


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


def _covariance(x: np.ndarray, y: np.ndarray) -> float:
    if x.size == 0 or y.size == 0:
        return 0.0
    return float(np.mean((x - np.mean(x)) * (y - np.mean(y))))


def _correlation(x: np.ndarray, y: np.ndarray) -> float:
    if x.size == 0 or y.size == 0:
        return 0.0
    sx = float(np.std(x))
    sy = float(np.std(y))
    if sx <= 0.0 or sy <= 0.0:
        return 0.0
    return float(_covariance(x, y) / (sx * sy))


def _binary_entropy(value: float) -> float:
    p = min(max(float(value), 1e-12), 1.0 - 1e-12)
    return float(-(p * math.log(p) + (1.0 - p) * math.log(1.0 - p)))


def _histogram_entropy(values: np.ndarray) -> float:
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0 or float(np.max(arr) - np.min(arr)) <= 0.0:
        return 0.0
    hist, _edges = np.histogram(arr, bins=min(10, max(2, int(arr.size))), density=False)
    probs = hist.astype(np.float64) / max(float(np.sum(hist)), 1.0)
    return float(-np.sum([p * math.log(p) for p in probs if p > 0.0]))


def _mean(values: Iterable[float] | np.ndarray) -> float:
    arr = np.asarray(list(values) if not isinstance(values, np.ndarray) else values, dtype=np.float64)
    return float(np.mean(arr)) if arr.size else 0.0


def _std(values: Iterable[float] | np.ndarray) -> float:
    arr = np.asarray(list(values) if not isinstance(values, np.ndarray) else values, dtype=np.float64)
    return float(np.std(arr)) if arr.size else 0.0


def _variance(values: Iterable[float] | np.ndarray) -> float:
    arr = np.asarray(list(values) if not isinstance(values, np.ndarray) else values, dtype=np.float64)
    return float(np.var(arr)) if arr.size else 0.0


def _min(values: Iterable[float] | np.ndarray) -> float:
    arr = np.asarray(list(values) if not isinstance(values, np.ndarray) else values, dtype=np.float64)
    return float(np.min(arr)) if arr.size else 0.0


def _max(values: Iterable[float] | np.ndarray) -> float:
    arr = np.asarray(list(values) if not isinstance(values, np.ndarray) else values, dtype=np.float64)
    return float(np.max(arr)) if arr.size else 0.0


def _max_abs(values: Iterable[float] | np.ndarray) -> float:
    arr = np.asarray(list(values) if not isinstance(values, np.ndarray) else values, dtype=np.float64)
    return float(np.max(np.abs(arr))) if arr.size else 0.0


def _quantile(values: Iterable[float] | np.ndarray, q: float) -> float:
    arr = np.asarray(list(values) if not isinstance(values, np.ndarray) else values, dtype=np.float64)
    return float(np.quantile(arr, float(q))) if arr.size else 0.0


def _write_outputs(output: Path, result: dict[str, object], visible_features: np.ndarray, sampled_visible_features: np.ndarray) -> None:
    artifacts = {
        "metrics.json": result,
        "visible_feature_schema.json": result["visible_feature_schema"],
        "visible_feature_matrix.json": result["visible_feature_matrix"],
        "forbidden_feature_audit.json": result["forbidden_feature_audit"],
        "split_manifest.json": result["split_manifest"],
        "probe_schedule_manifest.json": result["probe_schedule_manifest"],
        "signature_schedule_manifest.json": result["signature_schedule_manifest"],
        "batch_context_schema.json": result["batch_context_schema"],
        "assignment_unit.json": result["assignment_unit"],
        "adequacy_report.json": result["adequacy_report"],
        "aggregate_cache_manifest.json": result["aggregate_cache_manifest"],
        "acceptance_audit.json": result["acceptance_audit"],
    }
    for name, payload in artifacts.items():
        (output / name).write_text(json.dumps(_json_safe(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    np.save(output / "visible_features.npy", np.asarray(visible_features, dtype=np.float64))
    np.save(output / "sampled_visible_features.npy", np.asarray(sampled_visible_features, dtype=np.float64))
    (output / "config.yaml").write_text(yaml.safe_dump({"google_s3_visible_adapter_v2": result["config"]}, sort_keys=False), encoding="utf-8")
    (output / "summary.md").write_text(format_google_s3_visible_surface_v2_summary(result), encoding="utf-8")


def format_google_s3_visible_surface_v2_summary(result: dict[str, object]) -> str:
    acceptance = dict(result.get("acceptance_audit", {}))
    matrix = dict(result.get("visible_feature_matrix", {}))
    assignment = dict(result.get("assignment_unit", {}))
    adequacy = dict(result.get("adequacy_report", {}))
    return "\n".join(
        [
            "# Google S3A-Real Public Syndrome-Response Signatures",
            "",
            f"- Decision: `{result.get('decision')}`",
            f"- Acceptance passed: `{str(bool(acceptance.get('passed', False))).lower()}`",
            f"- Adequacy passed: `{str(bool(adequacy.get('passed', False))).lower()}`",
            f"- Rows: `{int(matrix.get('record_count', 0))}`",
            f"- Features: `{int(matrix.get('feature_count', 0))}`",
            f"- Assignment unit j: `{assignment.get('j_definition')}`",
            "",
            "## Claim Boundary",
            "",
            "This adapter builds public syndrome-response signatures from real Google detector and observable observations. It does not fabricate counterfactual teacher probes and does not expose context IDs, paths, sample IDs, decoder correctness, catalog labels, hidden mechanism labels, or oracle channel objects as learner features.",
            "",
        ]
    )
