from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from pathlib import Path
from typing import Iterable

import numpy as np

from scope_static.google.inventory import (
    DATASET_SURFACE_SET1,
    GoogleLeaf,
    iter_google_leaves,
    set1_leaf_from_google_leaf,
)
from scope_static.google.set1 import load_google_dem_data


DEFAULT_DATASET_NAME = DATASET_SURFACE_SET1
DEFAULT_DATASET_ROOT = "/home/cx/Document/google_72Q_surface_code_d3_d5_set1"
DEFAULT_SPLIT_POLICY = "grouped_context_leave_one_out_with_cyclic_validation"


@dataclass(frozen=True)
class GoogleDemSupportSurface:
    supports_by_fault: tuple[tuple[int, ...], ...]
    faults_by_observation_bit: tuple[tuple[int, ...], ...]
    num_detectors: int
    num_observables: int


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
        if math.isclose(value[0], min_x)
        or math.isclose(value[0], max_x)
        or math.isclose(value[1], min_y)
        or math.isclose(value[1], max_y)
    }


def _pad_coord(value: tuple[float, ...]) -> tuple[float, float, float]:
    items = list(float(item) for item in value)
    items.extend([0.0] * (3 - len(items)))
    return float(items[0]), float(items[1]), float(items[2])


def _indices_for_groups(assignment_instances: list[dict[str, object]], selected_groups: Iterable[int]) -> list[int]:
    selected = set(int(group) for group in selected_groups)
    return [int(row["record_index"]) for row in assignment_instances if int(row.get("context_group", -1)) in selected]


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
