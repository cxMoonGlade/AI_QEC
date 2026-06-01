from __future__ import annotations

from collections import Counter
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
from scope_static.google.set1 import build_google_fault_graph
from scope_static.learner import FORBIDDEN_FEATURE_TOKENS, FORBIDDEN_LEARNER_INPUTS


STAGE_NAME = "Google_S3A_real_visible_surface"
DEFAULT_DATASET_NAME = DATASET_SURFACE_SET1
DEFAULT_DATASET_ROOT = "/home/cx/Document/google_72Q_surface_code_d3_d5_set1"
DEFAULT_OUTPUT_DIR = "outputs/google_static/google_s3_visible_surface_v1/S3A_protocol_freeze"
DEFAULT_ASSIGNMENT_UNIT = "google_context_window_shotblock_instance"
DEFAULT_SPLIT_POLICY = "grouped_context_leave_one_out_with_cyclic_validation"

RAW_FEATURE_NAMES = [
    "raw__google_window2__P00",
    "raw__google_window2__P01",
    "raw__google_window2__P10",
    "raw__google_window2__P11",
    "raw__google_window2__p_comp",
    "raw__google_window2__E_left",
    "raw__google_window2__E_right",
    "raw__google_window2__E_pair",
    "raw__google_window2__se_P00",
    "raw__google_window2__se_P01",
    "raw__google_window2__se_P10",
    "raw__google_window2__se_P11",
    "raw__google_window2__se_p_comp",
    "raw__google_window2__se_E_left",
    "raw__google_window2__se_E_right",
    "raw__google_window2__se_E_pair",
]

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
    minimum_block = int(min_shotblock_size) if min_shotblock_size is not None else int(shotblock_size)
    if minimum_block <= 0:
        raise ValueError("min_shotblock_size must be positive")

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
            rng=rng,
        )
        blocks = _shotblocks(
            shot_count=int(observations.shape[0]),
            shotblock_size=int(shotblock_size),
            shotblocks_per_context=int(shotblocks_per_context),
            min_shotblock_size=minimum_block,
        )
        if not selected_windows or not blocks:
            skipped_contexts.append(
                {
                    "context_group": int(context_groups[leaf.context_id]),
                    "reason": "no_fixed_window2_or_shotblock",
                    "available_windows": int(len(selected_windows)),
                    "available_shots": int(observations.shape[0]),
                }
            )
            continue
        context_summary_rows.append(_context_summary(leaf, observations=observations, windows=selected_windows, blocks=blocks))
        for window_idx, google_window in enumerate(selected_windows):
            window = google_window.window
            for block_idx, (start, stop) in enumerate(blocks):
                block = np.asarray(observations[start:stop, list(window.bits)], dtype=np.bool_)
                row = _row_features(
                    block,
                    leaf=leaf,
                    window=window,
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
                        "assignment_unit": DEFAULT_ASSIGNMENT_UNIT,
                        "window_kind": str(window.kind),
                        "shotblock_index": int(block_idx),
                        "shot_count": int(stop - start),
                    }
                )
                window_rows.append(
                    {
                        "j": int(row_idx),
                        "context_group": int(context_groups[leaf.context_id]),
                        "window_index_within_context": int(window_idx),
                        "window_name": str(window.name),
                        "window_kind": str(window.kind),
                        "source_kind": str(google_window.source_kind),
                        "bits": [int(bit) for bit in window.bits],
                        "shotblock_start": int(start),
                        "shotblock_stop": int(stop),
                    }
                )
                row_idx += 1

    matrix = _finite(np.asarray(rows, dtype=np.float64)) if rows else np.zeros((0, len(FEATURE_NAMES)), dtype=np.float64)
    sampled_matrix = np.array(matrix, copy=True)
    split_manifest = _split_manifest(
        assignment_instances,
        context_group_count=len(leaves),
        split_policy=str(split_policy),
    )
    batch_schema = _batch_context_schema(
        context_group_count=len(leaves),
        assignment_unit=DEFAULT_ASSIGNMENT_UNIT,
        split_policy=str(split_policy),
        shotblocks_per_context=int(shotblocks_per_context),
    )
    feature_schema = _feature_schema()
    visible_feature_matrix = _visible_feature_matrix_manifest(matrix, sampled_matrix)
    forbidden_audit = forbidden_feature_audit_google(FEATURE_NAMES)
    assignment = _assignment_unit_manifest(
        record_count=int(matrix.shape[0]),
        context_group_count=len(leaves),
        windows_per_context=int(windows_per_context),
        shotblocks_per_context=int(shotblocks_per_context),
    )
    probe_schedule = _probe_schedule_manifest(
        window_rows,
        requested_windows_per_context=int(windows_per_context),
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
            "learner_visible_surface_kind": "empirical fixed 2-bit observation windows plus public context metadata",
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
    rng: np.random.Generator,
) -> list[GoogleWindow2]:
    circuit = load_google_circuit(leaf)
    detector_count = int(circuit.num_detectors)
    observable_count = int(circuit.num_observables)
    candidates: list[GoogleWindow2] = []
    candidates.extend(_geometry_detector_pairs(circuit, detector_count))
    if leaf.dataset_name == DATASET_SURFACE_SET1:
        try:
            graph, _audit = build_google_fault_graph(set1_leaf_from_google_leaf(leaf), dem_source=str(dem_source))
            candidates.extend(_dem_support_detector_pairs(graph))
            candidates.extend(_logical_detector_pairs(graph))
        except (FileNotFoundError, ValueError):
            candidates.extend(_fallback_logical_detector_pairs(detector_count, observable_count))
    else:
        candidates.extend(_fallback_logical_detector_pairs(detector_count, observable_count))
    candidates.extend(_boundary_representative_pairs(circuit, detector_count))
    deduped: list[GoogleWindow2] = []
    seen: set[tuple[int, ...]] = set()
    for item in candidates:
        bits = tuple(item.window.bits)
        if len(bits) != 2 or bits in seen:
            continue
        seen.add(bits)
        deduped.append(item)
    if len(deduped) <= int(windows_per_context):
        return deduped
    # Keep the selection deterministic but not tied to context path ordering.
    order = np.arange(len(deduped))
    rng.shuffle(order)
    selected = sorted(order[: int(windows_per_context)].tolist())
    return [deduped[idx] for idx in selected]


def _geometry_detector_pairs(circuit: object, detector_count: int) -> list[GoogleWindow2]:
    coords = _detector_coords(circuit, detector_count)
    if not coords:
        return []
    pairs = []
    for left in range(detector_count):
        for right in range(left + 1, detector_count):
            if left not in coords or right not in coords:
                continue
            distance = _linf_distance(coords[left], coords[right])
            pairs.append((distance, left, right))
    windows = []
    for _distance, left, right in sorted(pairs, key=lambda item: (item[0], item[1], item[2])):
        windows.append(GoogleWindow2(make_window(f"detector_pair:{left}:{right}", [left, right], "detector_pair"), "detector_geometry_pair"))
    return windows


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


def _row_features(
    block: np.ndarray,
    *,
    leaf: GoogleLeaf,
    window: ObservationWindow,
    block_idx: int,
    block_count: int,
) -> np.ndarray:
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
    metadata = _metadata_features(leaf=leaf, window=window, shot_count=int(block.shape[0]), block_idx=int(block_idx), block_count=int(block_count))
    return np.asarray([*raw, *metadata], dtype=np.float64)


def _metadata_features(
    *,
    leaf: GoogleLeaf,
    window: ObservationWindow,
    shot_count: int,
    block_idx: int,
    block_count: int,
) -> list[float]:
    circuit = load_google_circuit(leaf)
    detector_count = int(circuit.num_detectors)
    coords = _detector_coords(circuit, detector_count)
    detector_bits = [int(bit) for bit in window.bits if int(bit) < detector_count]
    coord_summary = _coord_summary(coords, detector_bits)
    touches_logical = any(int(bit) >= detector_count for bit in window.bits)
    boundary_touch = any(bit in _boundary_detectors(coords) for bit in detector_bits) if coords else False
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


def _feature_schema() -> dict[str, object]:
    raw_set = set(RAW_FEATURE_NAMES)
    metadata_set = set(METADATA_FEATURE_NAMES)
    features = []
    for idx, name in enumerate(FEATURE_NAMES):
        features.append(
            {
                "index": int(idx),
                "name": str(name),
                "kind": "raw_google_window2_empirical_observation" if name in raw_set else "allowed_google_public_metadata",
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
        "raw_feature_count": int(len(raw_set)),
        "metadata_feature_count": int(len(metadata_set)),
        "num_features": int(len(FEATURE_NAMES)),
        "features": features,
    }


def _visible_feature_matrix_manifest(matrix: np.ndarray, sampled: np.ndarray) -> dict[str, object]:
    return {
        "schema": "scope_static_stage3a_visible_feature_matrix_v1",
        "training_matrix_path": "visible_features.npy",
        "training_matrix_kind": "empirical_google_real_window2_observation_features",
        "sampled_matrix_path": "sampled_visible_features.npy",
        "sampled_matrix_kind": "same_empirical_google_real_window2_observation_features",
        "feature_schema_path": "visible_feature_schema.json",
        "feature_count": int(matrix.shape[1]) if matrix.ndim == 2 else 0,
        "record_count": int(matrix.shape[0]) if matrix.ndim == 2 else 0,
        "shape": [int(dim) for dim in matrix.shape],
        "sampled_shape": [int(dim) for dim in sampled.shape],
        "sampling_mode": "real_google_empirical_shotblocks",
        "feature_names_sha256": _text_digest("\n".join(FEATURE_NAMES)),
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
    split_policy: str,
) -> dict[str, object]:
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
        "assignment_unit": DEFAULT_ASSIGNMENT_UNIT,
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
) -> dict[str, object]:
    return {
        "schema": "scope_static_stage3a_batch_context_schema_v1",
        "assignment_unit": str(assignment_unit),
        "split_policy": str(split_policy),
        "primary_protocol": {
            "mode": "google_real_context_window_shotblock_batch",
            "context_group_key": "google_public_context_group",
            "context_group_count": int(context_group_count),
            "shotblocks_per_context": int(shotblocks_per_context),
        },
        "learner_visible_fields": [
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
        ],
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
) -> dict[str, object]:
    return {
        "schema": "scope_static_stage3a_assignment_unit_v1",
        "assignment_matrix": "S[j,k] or Pi[j,k]",
        "j_definition": DEFAULT_ASSIGNMENT_UNIT,
        "j_description": "Google context-window-shotblock instance",
        "single_shot_j_allowed_first_pass": False,
        "k_definition": "learned latent visible prototype index; no Google oracle mechanism labels are available",
        "record_count": int(record_count),
        "context_group_count": int(context_group_count),
        "requested_windows_per_context": int(windows_per_context),
        "requested_shotblocks_per_context": int(shotblocks_per_context),
        "catalog_cardinality_evaluator_only": 0,
        "evaluator_mode": "no_oracle_labels",
    }


def _probe_schedule_manifest(
    window_rows: list[dict[str, object]],
    *,
    requested_windows_per_context: int,
    dem_source: str,
) -> dict[str, object]:
    kind_counts = Counter(str(row["window_kind"]) for row in window_rows)
    source_counts = Counter(str(row["source_kind"]) for row in window_rows)
    return {
        "schema": "scope_static_google_s3a_window_schedule_manifest_v1",
        "source": "public fixed 2-bit Google detector/logical windows",
        "dem_source_for_public_support_windows": str(dem_source),
        "fixed_window_bits": 2,
        "requested_windows_per_context": int(requested_windows_per_context),
        "window_instance_count": int(len(window_rows)),
        "window_kind_counts": dict(sorted(kind_counts.items())),
        "window_source_counts": dict(sorted(source_counts.items())),
        "selection_policy": [
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
    blocks: list[tuple[int, int]],
) -> dict[str, object]:
    return {
        "context_group_summary_only": True,
        "basis": str(leaf.basis),
        "distance": None if leaf.distance is None else int(leaf.distance),
        "rounds": None if leaf.rounds is None else int(leaf.rounds),
        "shot_count": int(observations.shape[0]),
        "selected_window_count": int(len(windows)),
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
