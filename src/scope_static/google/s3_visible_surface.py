from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Iterable

import numpy as np
import yaml

from scope_static.dem.windows import ObservationWindow, make_window
from scope_static.google.inventory import (
    DATASET_SURFACE_SET1,
    GoogleLeaf,
    iter_google_leaves,
    load_google_circuit,
    load_google_observations,
    set1_leaf_from_google_leaf,
)
from scope_static.google.set1 import load_google_dem_data
from scope_static.learner import FORBIDDEN_FEATURE_TOKENS, FORBIDDEN_LEARNER_INPUTS


STAGE_NAME = "Google_S3A_real_visible_surface"
DEFAULT_DATASET_NAME = DATASET_SURFACE_SET1
DEFAULT_DATASET_ROOT = "/home/cx/Document/google_72Q_surface_code_d3_d5_set1"
DEFAULT_OUTPUT_DIR = "outputs/google_static/google_s3_visible_surface_v1/S3A_protocol_freeze"
DEFAULT_ASSIGNMENT_UNIT = "google_context_window_shotblock_instance"
DEFAULT_BUNDLE_ASSIGNMENT_UNIT = "google_context_windowbundle_shotblock_instance"
DEFAULT_SPLIT_POLICY = "grouped_context_leave_one_out_with_cyclic_validation"
WINDOW_FAMILY_PROFILE_MIXED_PUBLIC = "mixed_public"
WINDOW_FAMILY_PROFILE_DETECTOR_PAIR_ONLY = "detector_pair_only"
WINDOW_FAMILY_PROFILE_LOGICAL_DETECTOR_PAIR_ONLY = "logical_detector_pair_only"
WINDOW_FAMILY_PROFILE_DEM_SUPPORT_ONLY = "dem_support_only"
WINDOW_FAMILY_PROFILE_BOUNDARY_HEAVY = "boundary_heavy"
WINDOW_FAMILY_PROFILE_BULK_ONLY = "bulk_only"
WINDOW_FAMILY_PROFILE_MIXED_BALANCED = "mixed_balanced"
DEFAULT_WINDOW_FAMILY_PROFILE = WINDOW_FAMILY_PROFILE_MIXED_PUBLIC
ALLOWED_WINDOW_FAMILY_PROFILES = (
    WINDOW_FAMILY_PROFILE_MIXED_PUBLIC,
    WINDOW_FAMILY_PROFILE_DETECTOR_PAIR_ONLY,
    WINDOW_FAMILY_PROFILE_LOGICAL_DETECTOR_PAIR_ONLY,
    WINDOW_FAMILY_PROFILE_DEM_SUPPORT_ONLY,
    WINDOW_FAMILY_PROFILE_BOUNDARY_HEAVY,
    WINDOW_FAMILY_PROFILE_BULK_ONLY,
    WINDOW_FAMILY_PROFILE_MIXED_BALANCED,
)
WINDOW_FAMILY_PROFILE_ALIASES = {
    "default": WINDOW_FAMILY_PROFILE_MIXED_PUBLIC,
    "all": WINDOW_FAMILY_PROFILE_MIXED_PUBLIC,
    "dem_support_selected_only": WINDOW_FAMILY_PROFILE_DEM_SUPPORT_ONLY,
    "logical_only": WINDOW_FAMILY_PROFILE_LOGICAL_DETECTOR_PAIR_ONLY,
    "detector_only": WINDOW_FAMILY_PROFILE_DETECTOR_PAIR_ONLY,
}

RAW_METRICS = [
    "P00",
    "P01",
    "P10",
    "P11",
    "p_comp",
    "E_left",
    "E_right",
    "E_pair",
    "se_P00",
    "se_P01",
    "se_P10",
    "se_P11",
    "se_p_comp",
    "se_E_left",
    "se_E_right",
    "se_E_pair",
]
RAW_FEATURE_NAMES = [f"raw__google_window2__{metric}" for metric in RAW_METRICS]

METADATA_FEATURE_NAMES = [
    "visible_metadata__shot_count",
    "visible_metadata__basis_is_z",
    "visible_metadata__distance",
    "visible_metadata__rounds",
    "visible_metadata__window_kind_detector_pair",
    "visible_metadata__window_kind_logical_detector_pair",
    "visible_metadata__support_size",
    "visible_metadata__touches_logical",
    "visible_metadata__boundary_touch",
    "visible_metadata__detector_coord_summary_x_mean",
    "visible_metadata__detector_coord_summary_y_mean",
    "visible_metadata__detector_coord_summary_t_mean",
    "visible_metadata__detector_coord_summary_x_span",
    "visible_metadata__detector_coord_summary_y_span",
    "visible_metadata__detector_coord_summary_t_span",
    "visible_metadata__detector_coord_summary_missing_fraction",
    "visible_metadata__shotblock_index_normalized",
]
BUNDLE_METADATA_FEATURE_NAMES = [
    "visible_metadata__window_bundle_size",
    "visible_metadata__window_bundle_index_normalized",
]

FEATURE_NAMES = [*RAW_FEATURE_NAMES, *METADATA_FEATURE_NAMES]
FORBIDDEN_GOOGLE_FEATURE_TOKENS = (
    "context_id",
    "sample_id",
    "path",
    "decoder_correctness",
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
    "family",
    "label",
)


@dataclass(frozen=True)
class GoogleWindow2:
    window: ObservationWindow
    source_kind: str


@dataclass
class GoogleContextPublicMetadata:
    detector_count: int
    coords: dict[int, tuple[float, ...]]
    boundary_detectors: set[int]


@dataclass(frozen=True)
class GoogleDemSupportSurface:
    supports_by_fault: tuple[tuple[int, ...], ...]
    faults_by_observation_bit: tuple[tuple[int, ...], ...]
    num_detectors: int
    num_observables: int


def write_google_s3_visible_surface(
    *,
    dataset_root: str | Path | None = None,
    dataset_name: str = DEFAULT_DATASET_NAME,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    dem_source: str = "decoder_si1000",
    max_contexts: int = 24,
    windows_per_context: int = 64,
    shotblocks_per_context: int = 8,
    shotblock_size: int = 4096,
    min_shotblock_size: int | None = None,
    window_bundle_size: int = 1,
    window_family_profile: str = DEFAULT_WINDOW_FAMILY_PROFILE,
    basis: str | None = None,
    distance: int | None = None,
    rounds: int | None = None,
    seed: int = 0,
    split_policy: str = DEFAULT_SPLIT_POLICY,
) -> dict[str, object]:
    """Write Google real-data window rows in the Stage 3A visible artifact shape.

    The learner matrix contains empirical 2-bit observation distributions and
    allowed public context/window metadata only. It does not fabricate
    counterfactual teacher probes and does not include context/path/sample IDs
    or hidden mechanism labels as learner features.
    """

    if int(max_contexts) <= 0:
        raise ValueError("max_contexts must be positive")
    if int(windows_per_context) <= 0:
        raise ValueError("windows_per_context must be positive")
    if int(shotblocks_per_context) <= 0:
        raise ValueError("shotblocks_per_context must be positive")
    if int(shotblock_size) <= 0:
        raise ValueError("shotblock_size must be positive")
    if int(window_bundle_size) <= 0:
        raise ValueError("window_bundle_size must be positive")
    minimum_block = int(min_shotblock_size) if min_shotblock_size is not None else int(shotblock_size)
    if minimum_block <= 0:
        raise ValueError("min_shotblock_size must be positive")
    bundle_size = int(window_bundle_size)
    family_profile = _normalize_window_family_profile(window_family_profile)
    assignment_unit = _assignment_unit_name(bundle_size)
    feature_names = _feature_names(bundle_size)

    root = Path(dataset_root or os.environ.get("SCOPE_GOOGLE_SET1_ROOT", DEFAULT_DATASET_ROOT))
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    leaves = _select_contexts(
        root,
        dataset_name=str(dataset_name),
        max_contexts=int(max_contexts),
        basis=basis,
        distance=distance,
        rounds=rounds,
    )
    rng = np.random.default_rng(int(seed))
    context_groups = {leaf.context_id: idx for idx, leaf in enumerate(leaves)}

    rows: list[np.ndarray] = []
    assignment_instances: list[dict[str, object]] = []
    window_rows: list[dict[str, object]] = []
    skipped_contexts: list[dict[str, object]] = []
    context_summary_rows: list[dict[str, object]] = []
    row_idx = 0

    for leaf in leaves:
        observations = load_google_observations(leaf)
        selected_windows = _select_window2_for_leaf(
            leaf,
            dem_source=str(dem_source),
            windows_per_context=int(windows_per_context),
            window_family_profile=family_profile,
            rng=rng,
        )
        blocks = _shotblocks(
            shot_count=int(observations.shape[0]),
            shotblock_size=int(shotblock_size),
            shotblocks_per_context=int(shotblocks_per_context),
            min_shotblock_size=minimum_block,
        )
        window_bundles = _window_bundles(selected_windows, bundle_size=bundle_size)
        if not window_bundles or not blocks:
            skipped_contexts.append(
                {
                    "context_group": int(context_groups[leaf.context_id]),
                    "reason": "no_fixed_window2_bundle_or_shotblock",
                    "available_windows": int(len(selected_windows)),
                    "available_window_bundles": int(len(window_bundles)),
                    "available_shots": int(observations.shape[0]),
                    "window_family_profile": family_profile,
                }
            )
            continue
        public_metadata = _context_public_metadata(leaf)
        context_summary_rows.append(
            _context_summary(
                leaf,
                observations=observations,
                windows=selected_windows,
                window_bundles=window_bundles,
                blocks=blocks,
                window_family_profile=family_profile,
            )
        )
        for bundle_idx, bundle in enumerate(window_bundles):
            for block_idx, (start, stop) in enumerate(blocks):
                row = _bundle_row_features(
                    observations,
                    leaf=leaf,
                    window_bundle=bundle,
                    public_metadata=public_metadata,
                    start=start,
                    stop=stop,
                    bundle_idx=bundle_idx,
                    bundle_count=len(window_bundles),
                    block_idx=block_idx,
                    block_count=len(blocks),
                )
                rows.append(row)
                assignment_instances.append(
                    {
                        "j": int(row_idx),
                        "record_index": int(row_idx),
                        "visible_instance_id": f"j{row_idx:06d}",
                        "context_group": int(context_groups[leaf.context_id]),
                        "assignment_unit": assignment_unit,
                        "window_bundle_size": int(bundle_size),
                        "window_bundle_index": int(bundle_idx),
                        "window_kinds": [str(item.window.kind) for item in bundle],
                        "shotblock_index": int(block_idx),
                        "shot_count": int(stop - start),
                    }
                )
                window_rows.append(
                    {
                        "j": int(row_idx),
                        "context_group": int(context_groups[leaf.context_id]),
                        "window_bundle_index_within_context": int(bundle_idx),
                        "window_bundle_size": int(bundle_size),
                        "window_names": [str(item.window.name) for item in bundle],
                        "window_kinds": [str(item.window.kind) for item in bundle],
                        "source_kinds": [str(item.source_kind) for item in bundle],
                        "bits": [[int(bit) for bit in item.window.bits] for item in bundle],
                        "shotblock_start": int(start),
                        "shotblock_stop": int(stop),
                    }
                )
                row_idx += 1

    matrix = _finite(np.asarray(rows, dtype=np.float64)) if rows else np.zeros((0, len(feature_names)), dtype=np.float64)
    sampled_matrix = np.array(matrix, copy=True)
    split_manifest = _split_manifest(
        assignment_instances,
        context_group_count=len(leaves),
        assignment_unit=assignment_unit,
        split_policy=str(split_policy),
    )
    batch_schema = _batch_context_schema(
        context_group_count=len(leaves),
        assignment_unit=assignment_unit,
        split_policy=str(split_policy),
        shotblocks_per_context=int(shotblocks_per_context),
        window_bundle_size=bundle_size,
    )
    feature_schema = _feature_schema(feature_names, window_bundle_size=bundle_size)
    visible_feature_matrix = _visible_feature_matrix_manifest(matrix, sampled_matrix, feature_names=feature_names)
    forbidden_audit = forbidden_feature_audit_google(feature_names)
    assignment = _assignment_unit_manifest(
        record_count=int(matrix.shape[0]),
        context_group_count=len(leaves),
        windows_per_context=int(windows_per_context),
        shotblocks_per_context=int(shotblocks_per_context),
        window_bundle_size=bundle_size,
        assignment_unit=assignment_unit,
    )
    probe_schedule = _probe_schedule_manifest(
        window_rows,
        requested_windows_per_context=int(windows_per_context),
        window_bundle_size=bundle_size,
        window_family_profile=family_profile,
        dem_source=str(dem_source),
    )
    config = {
        "dataset_root": str(root),
        "dataset_name": str(dataset_name),
        "output_dir": str(output),
        "dem_source": str(dem_source),
        "max_contexts": int(max_contexts),
        "windows_per_context": int(windows_per_context),
        "shotblocks_per_context": int(shotblocks_per_context),
        "shotblock_size": int(shotblock_size),
        "min_shotblock_size": int(minimum_block),
        "window_bundle_size": int(bundle_size),
        "window_family_profile": family_profile,
        "basis": basis,
        "distance": None if distance is None else int(distance),
        "rounds": None if rounds is None else int(rounds),
        "seed": int(seed),
        "split_policy": str(split_policy),
        "evaluator_mode": "no_oracle_labels",
    }
    acceptance = _acceptance_audit(
        forbidden_audit=forbidden_audit,
        split_manifest=split_manifest,
        visible_feature_matrix=visible_feature_matrix,
        row_count=int(matrix.shape[0]),
        context_count=len(leaves),
    )
    result = {
        "schema": "scope_static_google_s3a_real_visible_surface_v1",
        "stage": STAGE_NAME,
        "output_dir": str(output),
        "claim_boundary": {
            "constructs_counterfactual_teacher_probes": False,
            "uses_real_google_detection_events": True,
            "uses_real_google_obs_flips_actual": True,
            "learner_visible_surface_kind": (
                "empirical fixed 2-bit observation-window bundles plus public context metadata"
                if bundle_size > 1
                else "empirical fixed 2-bit observation windows plus public context metadata"
            ),
            "evaluator_mode": "no_oracle_labels",
            "contains_true_hidden_mechanism_labels": False,
            "contains_catalog_m_labels": False,
            "contains_context_path_sample_one_hot_features": False,
        },
        "config": config,
        "context_scope": {
            "dataset_name": str(dataset_name),
            "selected_context_count": int(len(leaves)),
            "skipped_context_count": int(len(skipped_contexts)),
            "basis_counts": dict(sorted(Counter(str(leaf.basis) for leaf in leaves).items())),
            "distance_counts": {
                str(key): int(value)
                for key, value in sorted(Counter(leaf.distance for leaf in leaves).items(), key=lambda item: str(item[0]))
            },
            "rounds_counts": {
                str(key): int(value)
                for key, value in sorted(Counter(leaf.rounds for leaf in leaves).items(), key=lambda item: str(item[0]))
            },
            "context_summaries": context_summary_rows,
            "skipped_contexts": skipped_contexts,
        },
        "mechanism_scope": {
            "record_count": int(matrix.shape[0]),
            "class_count_evaluator_only": 0,
            "context_group_count": int(len(leaves)),
            "mechanism_labels_evaluator_only": [],
            "no_oracle_labels": True,
        },
        "visible_feature_schema": feature_schema,
        "visible_feature_matrix": visible_feature_matrix,
        "probe_schedule_manifest": probe_schedule,
        "forbidden_feature_audit": forbidden_audit,
        "split_manifest": split_manifest,
        "batch_context_schema": batch_schema,
        "assignment_unit": assignment,
        "acceptance_audit": acceptance,
        "decision": "google_s3_visible_surface_passed" if acceptance["passed"] else "google_s3_visible_surface_failed",
    }
    _write_outputs(output, result, matrix, sampled_matrix)
    return result


def forbidden_feature_audit_google(feature_names: Iterable[str]) -> dict[str, object]:
    names = [str(name) for name in feature_names]
    tokens = tuple(dict.fromkeys((*FORBIDDEN_FEATURE_TOKENS, *FORBIDDEN_GOOGLE_FEATURE_TOKENS)))
    hits = [
        {"feature_name": name, "token": token}
        for name in names
        for token in tokens
        if token in name.lower()
    ]
    checks = {
        "no_context_id_one_hot_features": not any("context_id" in name.lower() for name in names),
        "no_path_one_hot_features": not any("path" in name.lower() for name in names),
        "no_sample_id_one_hot_features": not any("sample_id" in name.lower() for name in names),
        "no_decoder_correctness_target": not any("decoder_correctness" in name.lower() for name in names),
        "no_catalog_m_label": not any("catalog" in name.lower() or "mechanism" in name.lower() for name in names),
        "no_oracle_channel_fields": not any(token in name.lower() for name in names for token in ("oracle", "channel", "kraus", "ptm")),
        "forbidden_feature_hit_count_is_zero": len(hits) == 0,
    }
    return {
        "schema": "scope_static_google_s3a_forbidden_feature_audit_v1",
        "passed": bool(all(checks.values())),
        "feature_count": int(len(names)),
        "forbidden_feature_count": int(len(hits)),
        "forbidden_feature_hits": hits,
        "checks": checks,
        "allowed_visible_inputs": [
            "empirical fixed 2-bit observation probabilities",
            "empirical expectations",
            "shot count",
            "finite-shot uncertainty estimates",
            "public basis/distance/round metadata",
            "public fixed-window kind metadata",
            "public detector-coordinate summaries",
            "shotblock position within context",
        ],
        "forbidden_learner_inputs": [
            *FORBIDDEN_LEARNER_INPUTS,
            "context_id one-hot",
            "path one-hot",
            "sample_id one-hot",
            "decoder correctness as learner target",
            "catalog M label",
            "true hidden mechanism label",
            "oracle PTM/Kraus/channel",
        ],
    }


def _assignment_unit_name(window_bundle_size: int) -> str:
    return DEFAULT_ASSIGNMENT_UNIT if int(window_bundle_size) <= 1 else DEFAULT_BUNDLE_ASSIGNMENT_UNIT


def _feature_names(window_bundle_size: int) -> list[str]:
    bundle_size = int(window_bundle_size)
    if bundle_size <= 1:
        return [*RAW_FEATURE_NAMES, *METADATA_FEATURE_NAMES]
    raw = [
        f"raw__google_window2_bundle_w{slot:02d}__{metric}"
        for slot in range(bundle_size)
        for metric in RAW_METRICS
    ]
    return [*raw, *METADATA_FEATURE_NAMES, *BUNDLE_METADATA_FEATURE_NAMES]


def _normalize_window_family_profile(value: str) -> str:
    profile = WINDOW_FAMILY_PROFILE_ALIASES.get(str(value), str(value))
    if profile not in ALLOWED_WINDOW_FAMILY_PROFILES:
        raise ValueError(f"window_family_profile must be one of {ALLOWED_WINDOW_FAMILY_PROFILES!r}")
    return profile


def _select_windows_for_family_profile(
    groups: dict[str, list[GoogleWindow2]],
    *,
    detector_count: int,
    boundary_detectors: set[int],
    windows_per_context: int,
    profile: str,
    rng: np.random.Generator,
) -> list[GoogleWindow2]:
    geometry = groups.get("geometry", [])
    dem_support = groups.get("dem_support", [])
    logical = groups.get("logical", [])
    boundary = groups.get("boundary", [])
    all_candidates = [*geometry, *dem_support, *logical, *boundary]
    if profile == WINDOW_FAMILY_PROFILE_MIXED_PUBLIC:
        return _limit_window_count(_dedupe_windows(all_candidates), windows_per_context=windows_per_context, rng=rng)
    if profile == WINDOW_FAMILY_PROFILE_DETECTOR_PAIR_ONLY:
        candidates = [item for item in all_candidates if str(item.window.kind) == "detector_pair"]
        return _limit_window_count(_dedupe_windows(candidates), windows_per_context=windows_per_context, rng=rng)
    if profile == WINDOW_FAMILY_PROFILE_LOGICAL_DETECTOR_PAIR_ONLY:
        candidates = [item for item in logical if str(item.window.kind) == "logical_detector_pair"]
        return _limit_window_count(_dedupe_windows(candidates), windows_per_context=windows_per_context, rng=rng)
    if profile == WINDOW_FAMILY_PROFILE_DEM_SUPPORT_ONLY:
        candidates = [item for item in dem_support if str(item.source_kind) == "dem_support_detector_pair"]
        return _limit_window_count(_dedupe_windows(candidates), windows_per_context=windows_per_context, rng=rng)
    if profile == WINDOW_FAMILY_PROFILE_BOUNDARY_HEAVY:
        deduped = _dedupe_windows(all_candidates)
        ordered = sorted(
            deduped,
            key=lambda item: (
                -_window_boundary_score(item, detector_count=detector_count, boundary_detectors=boundary_detectors),
                _window_source_priority(item.source_kind),
                str(item.window.name),
            ),
        )
        return ordered[: int(windows_per_context)]
    if profile == WINDOW_FAMILY_PROFILE_BULK_ONLY:
        candidates = [
            item
            for item in all_candidates
            if _is_bulk_detector_window(item, detector_count=detector_count, boundary_detectors=boundary_detectors)
        ]
        return _limit_window_count(_dedupe_windows(candidates), windows_per_context=windows_per_context, rng=rng)
    if profile == WINDOW_FAMILY_PROFILE_MIXED_BALANCED:
        group_order = [
            _dedupe_windows(dem_support),
            _dedupe_windows(logical),
            _dedupe_windows(
                [
                    item
                    for item in all_candidates
                    if _window_boundary_score(item, detector_count=detector_count, boundary_detectors=boundary_detectors) > 0
                ]
            ),
            _dedupe_windows(
                [
                    item
                    for item in all_candidates
                    if _is_bulk_detector_window(item, detector_count=detector_count, boundary_detectors=boundary_detectors)
                ]
            ),
        ]
        return _round_robin_window_mix(group_order, windows_per_context=windows_per_context, rng=rng)
    raise ValueError(f"unknown window_family_profile {profile!r}")


def _dedupe_windows(windows: Iterable[GoogleWindow2]) -> list[GoogleWindow2]:
    out: list[GoogleWindow2] = []
    seen: set[tuple[int, ...]] = set()
    for item in windows:
        bits = tuple(int(bit) for bit in item.window.bits)
        if len(bits) != 2 or bits in seen:
            continue
        seen.add(bits)
        out.append(item)
    return out


def _limit_window_count(windows: list[GoogleWindow2], *, windows_per_context: int, rng: np.random.Generator) -> list[GoogleWindow2]:
    if len(windows) <= int(windows_per_context):
        return list(windows)
    order = np.arange(len(windows))
    rng.shuffle(order)
    selected = sorted(order[: int(windows_per_context)].tolist())
    return [windows[idx] for idx in selected]


def _round_robin_window_mix(
    groups: list[list[GoogleWindow2]],
    *,
    windows_per_context: int,
    rng: np.random.Generator,
) -> list[GoogleWindow2]:
    prepared = []
    for group in groups:
        local = list(group)
        if len(local) > 1:
            order = np.arange(len(local))
            rng.shuffle(order)
            local = [local[int(idx)] for idx in order.tolist()]
        prepared.append(local)
    selected: list[GoogleWindow2] = []
    seen: set[tuple[int, ...]] = set()
    positions = [0 for _ in prepared]
    while len(selected) < int(windows_per_context):
        added = False
        for group_idx, group in enumerate(prepared):
            while positions[group_idx] < len(group):
                item = group[positions[group_idx]]
                positions[group_idx] += 1
                bits = tuple(int(bit) for bit in item.window.bits)
                if len(bits) != 2 or bits in seen:
                    continue
                seen.add(bits)
                selected.append(item)
                added = True
                break
            if len(selected) >= int(windows_per_context):
                break
        if not added:
            break
    return selected


def _window_boundary_score(item: GoogleWindow2, *, detector_count: int, boundary_detectors: set[int]) -> int:
    detector_bits = [int(bit) for bit in item.window.bits if int(bit) < int(detector_count)]
    score = sum(1 for bit in detector_bits if bit in boundary_detectors)
    if str(item.source_kind).startswith("boundary_"):
        score += 2
    return int(score)


def _window_source_priority(source_kind: str) -> int:
    order = {
        "boundary_representative_pair": 0,
        "boundary_interior_representative_pair": 1,
        "dem_support_detector_pair": 2,
        "logical_detector_pair": 3,
        "detector_geometry_pair": 4,
    }
    return int(order.get(str(source_kind), 99))


def _is_bulk_detector_window(item: GoogleWindow2, *, detector_count: int, boundary_detectors: set[int]) -> bool:
    bits = [int(bit) for bit in item.window.bits]
    return bool(
        str(item.window.kind) == "detector_pair"
        and bits
        and all(bit < int(detector_count) for bit in bits)
        and all(bit not in boundary_detectors for bit in bits)
    )


def _select_contexts(
    root: Path,
    *,
    dataset_name: str,
    max_contexts: int,
    basis: str | None,
    distance: int | None,
    rounds: int | None,
) -> list[GoogleLeaf]:
    leaves = []
    for leaf in iter_google_leaves(root, dataset_name):
        if basis is not None and str(leaf.basis).upper() != str(basis).upper():
            continue
        if distance is not None and leaf.distance != int(distance):
            continue
        if rounds is not None and leaf.rounds != int(rounds):
            continue
        leaves.append(leaf)
    if not leaves:
        raise ValueError("no Google contexts matched the requested filters")
    return leaves[: int(max_contexts)]


def _select_window2_for_leaf(
    leaf: GoogleLeaf,
    *,
    dem_source: str,
    windows_per_context: int,
    window_family_profile: str,
    rng: np.random.Generator,
) -> list[GoogleWindow2]:
    profile = _normalize_window_family_profile(window_family_profile)
    circuit = load_google_circuit(leaf)
    detector_count = int(circuit.num_detectors)
    observable_count = int(circuit.num_observables)
    geometry = _geometry_detector_pairs(circuit, detector_count)
    dem_support: list[GoogleWindow2] = []
    logical: list[GoogleWindow2] = []
    if leaf.dataset_name == DATASET_SURFACE_SET1:
        try:
            support_surface = _load_dem_support_surface(leaf, dem_source=str(dem_source))
            dem_support.extend(_dem_support_detector_pairs(support_surface))
            logical.extend(_logical_detector_pairs(support_surface))
        except (FileNotFoundError, ValueError):
            logical.extend(_fallback_logical_detector_pairs(detector_count, observable_count))
    else:
        logical.extend(_fallback_logical_detector_pairs(detector_count, observable_count))
    boundary = _boundary_representative_pairs(circuit, detector_count)
    boundary_detectors = _boundary_detectors(_detector_coords(circuit, detector_count))
    groups = {
        "geometry": geometry,
        "dem_support": dem_support,
        "logical": logical,
        "boundary": boundary,
    }
    return _select_windows_for_family_profile(
        groups,
        detector_count=detector_count,
        boundary_detectors=boundary_detectors,
        windows_per_context=int(windows_per_context),
        profile=profile,
        rng=rng,
    )


def _window_bundles(windows: list[GoogleWindow2], *, bundle_size: int) -> list[list[GoogleWindow2]]:
    size = max(1, int(bundle_size))
    return [windows[start : start + size] for start in range(0, len(windows), size) if len(windows[start : start + size]) == size]


def _geometry_detector_pairs(circuit: object, detector_count: int) -> list[GoogleWindow2]:
    coords = _detector_coords(circuit, detector_count)
    if not coords:
        return []
    padded = {idx: _pad_coord(value) for idx, value in coords.items()}
    pairs: set[tuple[int, int]] = set()

    def add_adjacent(indices: Iterable[int], *, key) -> None:
        ordered = sorted((int(idx) for idx in indices), key=key)
        for left, right in zip(ordered, ordered[1:]):
            if left != right:
                pairs.add((min(left, right), max(left, right)))

    add_adjacent(padded, key=lambda idx: (padded[idx][2], padded[idx][0], padded[idx][1], idx))

    by_xy: dict[tuple[float, float], list[int]] = defaultdict(list)
    by_xt: dict[tuple[float, float], list[int]] = defaultdict(list)
    by_yt: dict[tuple[float, float], list[int]] = defaultdict(list)
    by_t: dict[float, list[int]] = defaultdict(list)
    for idx, (x_coord, y_coord, t_coord) in padded.items():
        x_key, y_key, t_key = round(x_coord, 6), round(y_coord, 6), round(t_coord, 6)
        by_xy[(x_key, y_key)].append(int(idx))
        by_xt[(x_key, t_key)].append(int(idx))
        by_yt[(y_key, t_key)].append(int(idx))
        by_t[t_key].append(int(idx))

    for indices in by_xy.values():
        add_adjacent(indices, key=lambda idx: (padded[idx][2], idx))
    for indices in by_xt.values():
        add_adjacent(indices, key=lambda idx: (padded[idx][1], idx))
    for indices in by_yt.values():
        add_adjacent(indices, key=lambda idx: (padded[idx][0], idx))
    for indices in by_t.values():
        add_adjacent(indices, key=lambda idx: (padded[idx][0], padded[idx][1], idx))

    return [
        GoogleWindow2(make_window(f"detector_pair:{left}:{right}", [left, right], "detector_pair"), "detector_geometry_pair")
        for left, right in sorted(pairs, key=lambda item: (_linf_distance(coords[item[0]], coords[item[1]]), item[0], item[1]))
    ]


def _dem_support_detector_pairs(graph: object) -> list[GoogleWindow2]:
    pairs: set[tuple[int, int]] = set()
    detector_count = int(getattr(graph, "num_detectors"))
    for support in getattr(graph, "supports_by_fault"):
        detectors = [int(bit) for bit in support if int(bit) < detector_count]
        for left_idx, left in enumerate(detectors):
            for right in detectors[left_idx + 1 :]:
                pairs.add((min(left, right), max(left, right)))
    return [
        GoogleWindow2(make_window(f"dem_support_detector_pair:{left}:{right}", [left, right], "detector_pair"), "dem_support_detector_pair")
        for left, right in sorted(pairs)
    ]


def _logical_detector_pairs(graph: object) -> list[GoogleWindow2]:
    detector_count = int(getattr(graph, "num_detectors"))
    observable_count = int(getattr(graph, "num_observables"))
    pairs: set[tuple[int, int]] = set()
    for obs in range(observable_count):
        logical_bit = detector_count + obs
        fault_ids = getattr(graph, "faults_by_observation_bit")[logical_bit]
        for fault in fault_ids:
            for bit in getattr(graph, "supports_by_fault")[int(fault)]:
                if int(bit) < detector_count:
                    pairs.add((int(bit), logical_bit))
    return [
        GoogleWindow2(make_window(f"logical_detector_pair:{logical - detector_count}:{detector}", [detector, logical], "logical_detector_pair"), "logical_detector_pair")
        for detector, logical in sorted(pairs)
    ]


def _load_dem_support_surface(leaf: GoogleLeaf, *, dem_source: str) -> GoogleDemSupportSurface:
    dem_data = load_google_dem_data(set1_leaf_from_google_leaf(leaf), dem_source=str(dem_source))
    raw_masks = dem_data.raw_masks
    bit_count = int(raw_masks.shape[0])
    fault_count = int(raw_masks.shape[1])
    supports_by_fault: list[list[int]] = [[] for _ in range(fault_count)]
    faults_by_observation_bit: list[list[int]] = [[] for _ in range(bit_count)]
    bit_ids, fault_ids = raw_masks.nonzero(as_tuple=True)
    for bit, fault in zip(bit_ids.cpu().tolist(), fault_ids.cpu().tolist()):
        bit_int = int(bit)
        fault_int = int(fault)
        supports_by_fault[fault_int].append(bit_int)
        faults_by_observation_bit[bit_int].append(fault_int)
    return GoogleDemSupportSurface(
        supports_by_fault=tuple(tuple(bits) for bits in supports_by_fault),
        faults_by_observation_bit=tuple(tuple(faults) for faults in faults_by_observation_bit),
        num_detectors=int(dem_data.num_detectors),
        num_observables=int(dem_data.num_observables),
    )


def _fallback_logical_detector_pairs(detector_count: int, observable_count: int) -> list[GoogleWindow2]:
    out = []
    if detector_count <= 0 or observable_count <= 0:
        return out
    for obs in range(observable_count):
        logical = detector_count + obs
        for detector in range(detector_count):
            out.append(
                GoogleWindow2(make_window(f"logical_detector_pair:{obs}:{detector}", [detector, logical], "logical_detector_pair"), "logical_detector_pair")
            )
    return out


def _boundary_representative_pairs(circuit: object, detector_count: int) -> list[GoogleWindow2]:
    coords = _detector_coords(circuit, detector_count)
    if detector_count < 2 or not coords:
        return []
    boundary = _boundary_detectors(coords)
    interior = [det for det in sorted(coords) if det not in boundary]
    out = []
    boundary_sorted = sorted(boundary)
    if len(boundary_sorted) >= 2:
        left, right = boundary_sorted[0], boundary_sorted[-1]
        out.append(GoogleWindow2(make_window(f"boundary_detector_pair:{left}:{right}", [left, right], "detector_pair"), "boundary_representative_pair"))
    if boundary_sorted and interior:
        left, right = boundary_sorted[0], interior[0]
        out.append(GoogleWindow2(make_window(f"boundary_interior_detector_pair:{left}:{right}", [left, right], "detector_pair"), "boundary_interior_representative_pair"))
    return out


def _shotblocks(
    *,
    shot_count: int,
    shotblock_size: int,
    shotblocks_per_context: int,
    min_shotblock_size: int,
) -> list[tuple[int, int]]:
    blocks = []
    start = 0
    while start < int(shot_count) and len(blocks) < int(shotblocks_per_context):
        stop = min(int(shot_count), start + int(shotblock_size))
        if stop - start >= int(min_shotblock_size):
            blocks.append((int(start), int(stop)))
        start += int(shotblock_size)
    return blocks


def _bundle_row_features(
    observations: np.ndarray,
    *,
    leaf: GoogleLeaf,
    window_bundle: list[GoogleWindow2],
    public_metadata: GoogleContextPublicMetadata,
    start: int,
    stop: int,
    bundle_idx: int,
    bundle_count: int,
    block_idx: int,
    block_count: int,
) -> np.ndarray:
    raw: list[float] = []
    metadata_rows: list[list[float]] = []
    for item in window_bundle:
        window = item.window
        block = np.asarray(observations[start:stop, list(window.bits)], dtype=np.bool_)
        raw.extend(_window_raw_features(block).tolist())
        metadata_rows.append(
            _metadata_features(
                leaf=leaf,
                window=window,
                public_metadata=public_metadata,
                shot_count=int(block.shape[0]),
                block_idx=int(block_idx),
                block_count=int(block_count),
            )
        )
    if len(window_bundle) == 1:
        metadata = metadata_rows[0]
    else:
        metadata = _bundle_metadata_features(
            metadata_rows,
            bundle_idx=int(bundle_idx),
            bundle_count=int(bundle_count),
            bundle_size=len(window_bundle),
        )
    return np.asarray([*raw, *metadata], dtype=np.float64)


def _window_raw_features(block: np.ndarray) -> np.ndarray:
    if block.ndim != 2 or block.shape[1] != 2 or block.shape[0] == 0:
        raise ValueError("Google S3 visible rows require non-empty fixed 2-bit shotblocks")
    left = block[:, 0].astype(np.int64)
    right = block[:, 1].astype(np.int64)
    state = left * 2 + right
    counts = np.bincount(state, minlength=4).astype(np.float64)
    n = float(block.shape[0])
    probs = counts / n
    p00, p01, p10, p11 = probs.tolist()
    p_comp = float(np.sum(probs))
    e_left = float(p00 + p01 - p10 - p11)
    e_right = float(p00 - p01 + p10 - p11)
    e_pair = float(p00 - p01 - p10 + p11)
    raw = [
        p00,
        p01,
        p10,
        p11,
        p_comp,
        e_left,
        e_right,
        e_pair,
        _proportion_se(p00, n),
        _proportion_se(p01, n),
        _proportion_se(p10, n),
        _proportion_se(p11, n),
        _proportion_se(p_comp, n),
        _expectation_se(e_left, n),
        _expectation_se(e_right, n),
        _expectation_se(e_pair, n),
    ]
    return np.asarray(raw, dtype=np.float64)


def _bundle_metadata_features(
    metadata_rows: list[list[float]],
    *,
    bundle_idx: int,
    bundle_count: int,
    bundle_size: int,
) -> list[float]:
    arr = np.asarray(metadata_rows, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[0] == 0:
        raise ValueError("window bundle metadata requires at least one fixed 2-bit window")
    metadata = np.mean(arr, axis=0).tolist()
    metadata[0] = float(arr[0, 0])
    metadata[-1] = float(arr[0, -1])
    metadata.extend(
        [
            float(bundle_size),
            0.0 if int(bundle_count) <= 1 else float(bundle_idx) / float(int(bundle_count) - 1),
        ]
    )
    return metadata


def _metadata_features(
    *,
    leaf: GoogleLeaf,
    window: ObservationWindow,
    public_metadata: GoogleContextPublicMetadata,
    shot_count: int,
    block_idx: int,
    block_count: int,
) -> list[float]:
    detector_count = int(public_metadata.detector_count)
    coords = public_metadata.coords
    detector_bits = [int(bit) for bit in window.bits if int(bit) < detector_count]
    coord_summary = _coord_summary(coords, detector_bits)
    touches_logical = any(int(bit) >= detector_count for bit in window.bits)
    boundary_touch = any(bit in public_metadata.boundary_detectors for bit in detector_bits) if coords else False
    return [
        float(shot_count),
        1.0 if str(leaf.basis).upper() == "Z" else 0.0,
        float(leaf.distance if leaf.distance is not None else 0),
        float(leaf.rounds if leaf.rounds is not None else 0),
        1.0 if str(window.kind) == "detector_pair" else 0.0,
        1.0 if str(window.kind) == "logical_detector_pair" else 0.0,
        float(len(window.bits)),
        1.0 if touches_logical else 0.0,
        1.0 if boundary_touch else 0.0,
        coord_summary["x_mean"],
        coord_summary["y_mean"],
        coord_summary["t_mean"],
        coord_summary["x_span"],
        coord_summary["y_span"],
        coord_summary["t_span"],
        coord_summary["missing_fraction"],
        0.0 if block_count <= 1 else float(block_idx) / float(block_count - 1),
    ]


def _context_public_metadata(leaf: GoogleLeaf) -> GoogleContextPublicMetadata:
    circuit = load_google_circuit(leaf)
    detector_count = int(circuit.num_detectors)
    coords = _detector_coords(circuit, detector_count)
    return GoogleContextPublicMetadata(
        detector_count=detector_count,
        coords=coords,
        boundary_detectors=_boundary_detectors(coords),
    )


def _feature_schema(feature_names: list[str], *, window_bundle_size: int) -> dict[str, object]:
    names = [str(name) for name in feature_names]
    raw_set = {name for name in names if name.startswith("raw__")}
    metadata_set = {name for name in names if name.startswith("visible_metadata__")}
    bundle_size = int(window_bundle_size)
    features = []
    for idx, name in enumerate(names):
        features.append(
            {
                "index": int(idx),
                "name": str(name),
                "kind": (
                    "raw_google_window2_bundle_empirical_observation"
                    if bundle_size > 1 and name in raw_set
                    else "raw_google_window2_empirical_observation"
                    if name in raw_set
                    else "allowed_google_public_metadata"
                ),
                "learner_visible": True,
                "source": (
                    "Google detection_events.b8 and obs_flips_actual.b8 fixed 2-bit shotblock empirical distribution"
                    if name in raw_set
                    else "public Google context/window metadata, not context/sample/path identity"
                ),
            }
        )
    return {
        "schema": "scope_static_google_s3a_real_visible_feature_schema_v1",
        "stage": STAGE_NAME,
        "claim_boundary": "Real Google data provide empirical fixed-window visible observations, not counterfactual teacher probe responses.",
        "fixed_window_bits": 2,
        "window_bundle_size": int(bundle_size),
        "raw_feature_count": int(len(raw_set)),
        "metadata_feature_count": int(len(metadata_set)),
        "num_features": int(len(names)),
        "features": features,
    }


def _visible_feature_matrix_manifest(matrix: np.ndarray, sampled: np.ndarray, *, feature_names: list[str]) -> dict[str, object]:
    names = [str(name) for name in feature_names]
    matrix_kind = (
        "empirical_google_real_window2_bundle_observation_features"
        if any("raw__google_window2_bundle_" in name for name in names)
        else "empirical_google_real_window2_observation_features"
    )
    return {
        "schema": "scope_static_stage3a_visible_feature_matrix_v1",
        "training_matrix_path": "visible_features.npy",
        "training_matrix_kind": matrix_kind,
        "sampled_matrix_path": "sampled_visible_features.npy",
        "sampled_matrix_kind": f"same_{matrix_kind}",
        "feature_schema_path": "visible_feature_schema.json",
        "feature_count": int(matrix.shape[1]) if matrix.ndim == 2 else 0,
        "record_count": int(matrix.shape[0]) if matrix.ndim == 2 else 0,
        "shape": [int(dim) for dim in matrix.shape],
        "sampled_shape": [int(dim) for dim in sampled.shape],
        "sampling_mode": "real_google_empirical_shotblocks",
        "feature_names_sha256": _text_digest("\n".join(names)),
        "visible_features_sha256": _matrix_digest(matrix),
        "sampled_visible_features_sha256": _matrix_digest(sampled),
        "learner_training_source": "Google S3A-real frozen visible_features.npy",
        "contains_evaluator_labels": False,
        "contains_oracle_fields": False,
        "contains_context_path_sample_one_hot_features": False,
    }


def _split_manifest(
    assignment_instances: list[dict[str, object]],
    *,
    context_group_count: int,
    assignment_unit: str,
    split_policy: str,
) -> dict[str, object]:
    groups = sorted({int(row.get("context_group", -1)) for row in assignment_instances if int(row.get("context_group", -1)) >= 0})
    if not groups and int(context_group_count) > 0:
        groups = list(range(int(context_group_count)))
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
        "group_key": "google_public_context_group",
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


def _batch_context_schema(
    *,
    context_group_count: int,
    assignment_unit: str,
    split_policy: str,
    shotblocks_per_context: int,
    window_bundle_size: int,
) -> dict[str, object]:
    bundle_size = int(window_bundle_size)
    learner_visible_fields = [
        "empirical_google_window2_probabilities",
        "empirical_google_window2_expectations",
        "shot_count",
        "finite_shot_uncertainty_estimates",
        "basis_is_z",
        "distance",
        "rounds",
        "window_kind",
        "support_size",
        "touches_logical",
        "boundary_touch",
        "detector_coordinate_summaries",
        "shotblock_index_normalized",
    ]
    if bundle_size > 1:
        learner_visible_fields.extend(["window_bundle_size", "window_bundle_index_normalized"])
    return {
        "schema": "scope_static_stage3a_batch_context_schema_v1",
        "assignment_unit": str(assignment_unit),
        "split_policy": str(split_policy),
        "primary_protocol": {
            "mode": (
                "google_real_context_windowbundle_shotblock_batch"
                if bundle_size > 1
                else "google_real_context_window_shotblock_batch"
            ),
            "context_group_key": "google_public_context_group",
            "context_group_count": int(context_group_count),
            "shotblocks_per_context": int(shotblocks_per_context),
            "window_bundle_size": int(bundle_size),
        },
        "learner_visible_fields": learner_visible_fields,
        "protocol_only_fields": ["j", "fold", "train_validation_test_split", "context_group"],
        "evaluator_only_fields": [
            "optional_external_proxy_labels",
            "decoder_baseline_outputs",
            "archived_dem_proxy_baseline_metrics",
            "dmle_qec_baseline_metrics",
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


def _assignment_unit_manifest(
    *,
    record_count: int,
    context_group_count: int,
    windows_per_context: int,
    shotblocks_per_context: int,
    window_bundle_size: int,
    assignment_unit: str,
) -> dict[str, object]:
    bundle_size = int(window_bundle_size)
    return {
        "schema": "scope_static_stage3a_assignment_unit_v1",
        "assignment_matrix": "S[j,k] or Pi[j,k]",
        "j_definition": str(assignment_unit),
        "j_description": (
            "Google context-windowbundle-shotblock instance"
            if bundle_size > 1
            else "Google context-window-shotblock instance"
        ),
        "single_shot_j_allowed_first_pass": False,
        "k_definition": "learned latent visible prototype index; no Google oracle mechanism labels are available",
        "record_count": int(record_count),
        "context_group_count": int(context_group_count),
        "requested_windows_per_context": int(windows_per_context),
        "requested_shotblocks_per_context": int(shotblocks_per_context),
        "requested_window_bundle_size": int(bundle_size),
        "requested_window_bundles_per_context": int(int(windows_per_context) // max(1, bundle_size)),
        "expected_categorical_population_group_count_per_row": int(bundle_size),
        "catalog_cardinality_evaluator_only": 0,
        "evaluator_mode": "no_oracle_labels",
    }


def _probe_schedule_manifest(
    window_rows: list[dict[str, object]],
    *,
    requested_windows_per_context: int,
    window_bundle_size: int,
    window_family_profile: str,
    dem_source: str,
) -> dict[str, object]:
    kind_counts = Counter(str(kind) for row in window_rows for kind in row.get("window_kinds", []))
    source_counts = Counter(str(source) for row in window_rows for source in row.get("source_kinds", []))
    window_instance_count = sum(len(list(row.get("window_kinds", []))) for row in window_rows)
    return {
        "schema": "scope_static_google_s3a_window_schedule_manifest_v1",
        "source": "public fixed 2-bit Google detector/logical windows",
        "dem_source_for_public_support_windows": str(dem_source),
        "fixed_window_bits": 2,
        "requested_windows_per_context": int(requested_windows_per_context),
        "window_bundle_size": int(window_bundle_size),
        "window_family_profile": str(window_family_profile),
        "window_bundle_instance_count": int(len(window_rows)),
        "window_instance_count": int(window_instance_count),
        "window_kind_counts": dict(sorted(kind_counts.items())),
        "window_source_counts": dict(sorted(source_counts.items())),
        "selection_policy": [
            f"window family profile: {window_family_profile}",
            "detector-detector local geometry pairs",
            "DEM-support-derived detector pairs",
            "logical-detector pairs",
            "boundary/interior representative detector pairs",
        ],
        "no_logical_fault_support_variable_size_windows": True,
        "examples": window_rows[: min(50, len(window_rows))],
    }


def _acceptance_audit(
    *,
    forbidden_audit: dict[str, object],
    split_manifest: dict[str, object],
    visible_feature_matrix: dict[str, object],
    row_count: int,
    context_count: int,
) -> dict[str, object]:
    checks = {
        "no_forbidden_learner_fields": bool(forbidden_audit.get("passed", False)),
        "split_policy_fixed_before_model_training": bool(split_manifest.get("split_policy_fixed_before_training", False)),
        "train_validation_test_splits_non_empty": bool(split_manifest.get("train_validation_test_splits_non_empty", False)),
        "assignment_unit_declared_before_training": True,
        "single_shot_assignment_not_used_first_pass": True,
        "validation_label_model_selection_disabled": not bool(split_manifest.get("validation_labels_available_to_model_selection", True)),
        "test_label_model_selection_disabled": not bool(split_manifest.get("test_labels_available_to_model_selection", True)),
        "frozen_visible_feature_matrix_declared": bool(visible_feature_matrix.get("training_matrix_path")),
        "frozen_visible_feature_matrix_has_no_labels": not bool(visible_feature_matrix.get("contains_evaluator_labels", True)),
        "frozen_visible_feature_matrix_has_no_oracle_fields": not bool(visible_feature_matrix.get("contains_oracle_fields", True)),
        "frozen_visible_feature_matrix_has_no_context_path_sample_one_hot": not bool(
            visible_feature_matrix.get("contains_context_path_sample_one_hot_features", True)
        ),
        "fixed_window2_rows_exist": int(row_count) > 0,
        "multiple_context_groups_available": int(context_count) >= 3,
        "learner_training_not_run_in_stage3a": True,
        "observability_ceiling_deferred_or_unavailable_without_oracle_labels": True,
    }
    return {
        "schema": "scope_static_google_s3a_acceptance_audit_v1",
        "passed": bool(all(checks.values())),
        "checks": checks,
    }


def _context_summary(
    leaf: GoogleLeaf,
    *,
    observations: np.ndarray,
    windows: list[GoogleWindow2],
    window_bundles: list[list[GoogleWindow2]],
    blocks: list[tuple[int, int]],
    window_family_profile: str,
) -> dict[str, object]:
    return {
        "context_group_summary_only": True,
        "window_family_profile": str(window_family_profile),
        "basis": str(leaf.basis),
        "distance": None if leaf.distance is None else int(leaf.distance),
        "rounds": None if leaf.rounds is None else int(leaf.rounds),
        "shot_count": int(observations.shape[0]),
        "selected_window_count": int(len(windows)),
        "selected_window_bundle_count": int(len(window_bundles)),
        "selected_shotblock_count": int(len(blocks)),
    }


def _coord_summary(coords: dict[int, tuple[float, ...]], detector_bits: list[int]) -> dict[str, float]:
    values = [coords[bit] for bit in detector_bits if bit in coords]
    if not detector_bits:
        missing = 0.0
    else:
        missing = 1.0 - float(len(values)) / float(len(detector_bits))
    if not values:
        return {
            "x_mean": 0.0,
            "y_mean": 0.0,
            "t_mean": 0.0,
            "x_span": 0.0,
            "y_span": 0.0,
            "t_span": 0.0,
            "missing_fraction": float(missing),
        }
    padded = [_pad_coord(value) for value in values]
    arr = np.asarray(padded, dtype=np.float64)
    return {
        "x_mean": float(np.mean(arr[:, 0])),
        "y_mean": float(np.mean(arr[:, 1])),
        "t_mean": float(np.mean(arr[:, 2])),
        "x_span": float(np.max(arr[:, 0]) - np.min(arr[:, 0])),
        "y_span": float(np.max(arr[:, 1]) - np.min(arr[:, 1])),
        "t_span": float(np.max(arr[:, 2]) - np.min(arr[:, 2])),
        "missing_fraction": float(missing),
    }


def _detector_coords(circuit: object, detector_count: int) -> dict[int, tuple[float, ...]]:
    try:
        raw = circuit.get_detector_coordinates()
    except Exception:
        return {}
    coords = {int(key): tuple(float(value) for value in values) for key, values in raw.items()}
    return {idx: coords[idx] for idx in range(int(detector_count)) if idx in coords}


def _boundary_detectors(coords: dict[int, tuple[float, ...]]) -> set[int]:
    if not coords:
        return set()
    padded = {idx: _pad_coord(value) for idx, value in coords.items()}
    xs = [value[0] for value in padded.values()]
    ys = [value[1] for value in padded.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    return {
        int(idx)
        for idx, value in padded.items()
        if math.isclose(value[0], min_x) or math.isclose(value[0], max_x) or math.isclose(value[1], min_y) or math.isclose(value[1], max_y)
    }


def _pad_coord(value: tuple[float, ...]) -> tuple[float, float, float]:
    items = list(float(item) for item in value)
    items.extend([0.0] * (3 - len(items)))
    return float(items[0]), float(items[1]), float(items[2])


def _linf_distance(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    a = _pad_coord(left)
    b = _pad_coord(right)
    return float(max(abs(x - y) for x, y in zip(a, b)))


def _indices_for_groups(assignment_instances: list[dict[str, object]], selected_groups: Iterable[int]) -> list[int]:
    selected = set(int(group) for group in selected_groups)
    return [int(row["record_index"]) for row in assignment_instances if int(row.get("context_group", -1)) in selected]


def _proportion_se(p: float, n: float) -> float:
    return float(math.sqrt(max(0.0, float(p) * (1.0 - float(p))) / max(float(n), 1.0)))


def _expectation_se(expectation: float, n: float) -> float:
    return float(math.sqrt(max(0.0, 1.0 - float(expectation) * float(expectation)) / max(float(n), 1.0)))


def _finite(matrix: np.ndarray) -> np.ndarray:
    return np.nan_to_num(np.asarray(matrix, dtype=np.float64), nan=0.0, posinf=0.0, neginf=0.0)


def _text_digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _matrix_digest(matrix: np.ndarray) -> str:
    arr = np.ascontiguousarray(np.asarray(matrix, dtype=np.float64))
    return hashlib.sha256(arr.tobytes()).hexdigest()


def _json_safe(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return _json_safe(list(value))
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    return value


def _write_outputs(output: Path, result: dict[str, object], visible_features: np.ndarray, sampled_visible_features: np.ndarray) -> None:
    artifacts = {
        "metrics.json": result,
        "visible_feature_schema.json": result["visible_feature_schema"],
        "visible_feature_matrix.json": result["visible_feature_matrix"],
        "forbidden_feature_audit.json": result["forbidden_feature_audit"],
        "split_manifest.json": result["split_manifest"],
        "probe_schedule_manifest.json": result["probe_schedule_manifest"],
        "batch_context_schema.json": result["batch_context_schema"],
        "assignment_unit.json": result["assignment_unit"],
        "acceptance_audit.json": result["acceptance_audit"],
    }
    for name, payload in artifacts.items():
        (output / name).write_text(json.dumps(_json_safe(payload), indent=2, sort_keys=True) + "\n")
    np.save(output / "visible_features.npy", np.asarray(visible_features, dtype=np.float64))
    np.save(output / "sampled_visible_features.npy", np.asarray(sampled_visible_features, dtype=np.float64))
    (output / "config.yaml").write_text(yaml.safe_dump({"google_s3_visible_adapter_v1": result["config"]}, sort_keys=False))
    (output / "summary.md").write_text(format_google_s3_visible_surface_summary(result))


def format_google_s3_visible_surface_summary(result: dict[str, object]) -> str:
    acceptance = dict(result.get("acceptance_audit", {}))
    matrix = dict(result.get("visible_feature_matrix", {}))
    assignment = dict(result.get("assignment_unit", {}))
    scope = dict(result.get("context_scope", {}))
    return "\n".join(
        [
            "# Google S3A-Real Visible Surface",
            "",
            f"- Decision: `{result.get('decision')}`",
            f"- Acceptance passed: `{str(bool(acceptance.get('passed', False))).lower()}`",
            f"- Rows: `{int(matrix.get('record_count', 0))}`",
            f"- Features: `{int(matrix.get('feature_count', 0))}`",
            f"- Contexts: `{int(scope.get('selected_context_count', 0))}`",
            f"- Assignment unit j: `{assignment.get('j_definition')}`",
            "",
            "## Claim Boundary",
            "",
            "This adapter builds empirical fixed 2-bit Google observation-window rows plus public context/window metadata. It does not fabricate counterfactual teacher probes and does not expose context IDs, paths, sample IDs, catalog labels, hidden mechanism labels, or oracle channel objects as learner features.",
            "",
        ]
    )
