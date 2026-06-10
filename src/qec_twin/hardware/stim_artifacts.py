"""stim-circuit artifacts for the hardware path.

Circuit counts, the detector ``(chain_index, layer)`` grid, measurements→detection
(m2d) conversion with bit-exact parity checking, and evaluator-side DEM
pair-support extraction. ``stim`` is imported lazily (core dep, decoder/ style).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from qec_twin.hardware.b8_io import pack_bits, unpack_bits


def load_circuit(path: Path | str):
    import stim

    return stim.Circuit.from_file(str(path))


@dataclass(frozen=True)
class CircuitCounts:
    num_detectors: int
    num_measurements: int
    num_observables: int
    num_sweep_bits: int
    num_qubits: int


def circuit_counts(circuit) -> CircuitCounts:
    return CircuitCounts(
        num_detectors=int(circuit.num_detectors),
        num_measurements=int(circuit.num_measurements),
        num_observables=int(circuit.num_observables),
        num_sweep_bits=int(circuit.num_sweep_bits),
        num_qubits=int(circuit.num_qubits),
    )


@dataclass(frozen=True)
class DetectorGrid:
    """Detector index -> (layer, chain) map for a quasi-1D repetition-code chain."""

    det_to_layer: np.ndarray  # [D] int32, dense layer rank (0 = init, last = final)
    det_to_chain: np.ndarray  # [D] int32, position along the chain
    grid: np.ndarray  # [num_layers, num_chains] detector index, complete
    num_layers: int
    num_chains: int
    chain_order_source: str  # "metadata_qubit_order" | "dem_path"


def _parse_spatial_entry(entry) -> tuple[float, ...] | None:
    if isinstance(entry, (list, tuple)) and entry and all(isinstance(v, (int, float)) for v in entry):
        return tuple(float(v) for v in entry)
    if isinstance(entry, dict):
        for keys in (("x", "y"), ("row", "col"), ("r", "c")):
            if all(k in entry for k in keys):
                return tuple(float(entry[k]) for k in keys)
    if isinstance(entry, str):
        numbers = re.findall(r"-?\d+(?:\.\d+)?", entry)
        if numbers:
            return tuple(float(v) for v in numbers)
    if isinstance(entry, (int, float)):
        return (float(entry),)
    return None


def _chain_ranks_from_qubit_order(spatial_set: set[tuple[float, ...]], qubit_order) -> dict | None:
    ranks: dict[tuple[float, ...], int] = {}
    for entry in qubit_order:
        parsed = _parse_spatial_entry(entry)
        if parsed in spatial_set and parsed not in ranks:
            ranks[parsed] = len(ranks)
    return ranks if len(ranks) == len(spatial_set) else None


def _dem_detector_sets(circuit):
    try:
        dem = circuit.detector_error_model()
    except Exception:
        dem = circuit.detector_error_model(approximate_disjoint_errors=True)
    detector_sets: list[frozenset[int]] = []
    for instruction in dem.flattened():
        if instruction.type != "error":
            continue
        dets: set[int] = set()
        for target in instruction.targets_copy():
            if target.is_relative_detector_id():
                dets ^= {int(target.val)}
        detector_sets.append(frozenset(dets))
    return detector_sets


def _chain_ranks_from_dem_path(
    dem_circuit,
    det_to_layer: np.ndarray,
    det_spatial: list[tuple[float, ...]],
    spatial_set: set[tuple[float, ...]],
) -> dict:
    """Chain order from the DEM's same-layer (space-like) edges: they form a path."""

    neighbors: dict[tuple[float, ...], set[tuple[float, ...]]] = {s: set() for s in spatial_set}
    for dets in _dem_detector_sets(dem_circuit):
        if len(dets) != 2:
            continue
        a, b = sorted(dets)
        if det_to_layer[a] != det_to_layer[b]:
            continue
        sa, sb = det_spatial[a], det_spatial[b]
        if sa != sb:
            neighbors[sa].add(sb)
            neighbors[sb].add(sa)
    endpoints = sorted(s for s, n in neighbors.items() if len(n) == 1)
    if len(endpoints) != 2:
        raise ValueError(
            f"DEM same-layer adjacency is not a path: {len(endpoints)} endpoints "
            f"(expected 2) over {len(spatial_set)} chain sites"
        )
    order = [endpoints[0]]
    while True:
        nxt = [s for s in neighbors[order[-1]] if len(order) < 2 or s != order[-2]]
        if not nxt:
            break
        order.append(min(nxt))
    if len(order) != len(spatial_set):
        raise ValueError(f"DEM path covers {len(order)} of {len(spatial_set)} chain sites")
    return {s: i for i, s in enumerate(order)}


def detector_grid(circuit, *, dem_circuit=None, qubit_order=None) -> DetectorGrid:
    """Build the (layer, chain) grid from DETECTOR coordinates.

    Chain ordering: metadata ``qubit_order`` when it matches the detector
    spatial coordinates; otherwise the DEM same-layer path order of
    ``dem_circuit`` (the noisy circuit). Layer = dense rank of the trailing
    (time) coordinate.
    """

    coords = circuit.get_detector_coordinates()
    num_detectors = int(circuit.num_detectors)
    if len(coords) != num_detectors or any(len(v) < 3 or len(v) % 3 for v in coords.values()):
        raise ValueError("circuit lacks (x, y, t)-triplet DETECTOR coordinates")

    # Coordinates come in (x, y, t) triplets: init detectors carry 1 triplet, bulk 2
    # (same measure qubit at rounds t and t-1), final 3 (two data qubits at t plus the
    # measure qubit at t-1). The chain site is the measure qubit's (x, y) = the pair of
    # the minimum-t triplet (first triplet for init/bulk; the t-1 triplet for final).
    det_spatial = [()] * num_detectors
    det_time = np.zeros(num_detectors, dtype=np.float64)
    for det, values in coords.items():
        triplets = [
            (float(values[i]), float(values[i + 1]), float(values[i + 2]))
            for i in range(0, len(values), 3)
        ]
        site = min(triplets, key=lambda p: p[2])
        det_spatial[int(det)] = (site[0], site[1])
        det_time[int(det)] = triplets[0][2]

    unique_times = np.unique(det_time)
    det_to_layer = np.searchsorted(unique_times, det_time).astype(np.int32)

    spatial_set = set(det_spatial)
    source = "metadata_qubit_order"
    ranks = _chain_ranks_from_qubit_order(spatial_set, qubit_order) if qubit_order else None
    if ranks is None:
        if dem_circuit is None:
            raise ValueError("qubit_order did not resolve the chain order and no dem_circuit given")
        ranks = _chain_ranks_from_dem_path(dem_circuit, det_to_layer, det_spatial, spatial_set)
        source = "dem_path"
    det_to_chain = np.array([ranks[s] for s in det_spatial], dtype=np.int32)

    num_layers = len(unique_times)
    num_chains = len(spatial_set)
    grid = np.full((num_layers, num_chains), -1, dtype=np.int64)
    grid[det_to_layer, det_to_chain] = np.arange(num_detectors)
    if (grid < 0).any() or num_layers * num_chains != num_detectors:
        raise ValueError(
            f"detector grid is not complete: {num_layers} layers x {num_chains} chains "
            f"vs {num_detectors} detectors"
        )
    return DetectorGrid(
        det_to_layer=det_to_layer,
        det_to_chain=det_to_chain,
        grid=grid,
        num_layers=num_layers,
        num_chains=num_chains,
        chain_order_source=source,
    )


class M2DConverter:
    """measurements (+ sweep) -> detection events / observable flips, packed in+out."""

    def __init__(self, circuit) -> None:
        self._converter = circuit.compile_m2d_converter()
        self.num_measurements = int(circuit.num_measurements)
        self.num_detectors = int(circuit.num_detectors)
        self.num_observables = int(circuit.num_observables)
        self.num_sweep_bits = int(circuit.num_sweep_bits)

    def convert_packed(
        self, measurements_packed: np.ndarray, sweep_packed: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        measurements_packed = np.ascontiguousarray(measurements_packed, dtype=np.uint8)
        sweep_packed = np.ascontiguousarray(sweep_packed, dtype=np.uint8)
        try:
            dets, obs = self._converter.convert(
                measurements=measurements_packed,
                sweep_bits=sweep_packed,
                separate_observables=True,
                bit_packed=True,
            )
            return np.asarray(dets, dtype=np.uint8), np.asarray(obs, dtype=np.uint8)
        except (TypeError, ValueError):
            measurements = unpack_bits(measurements_packed, self.num_measurements)
            sweep = unpack_bits(sweep_packed, self.num_sweep_bits)
            dets, obs = self._converter.convert(
                measurements=measurements,
                sweep_bits=sweep,
                separate_observables=True,
            )
            return pack_bits(np.asarray(dets)), pack_bits(np.asarray(obs))


@dataclass(frozen=True)
class ParityReport:
    total_bytes: int
    mismatched_bytes: int
    first_mismatch_byte: int | None

    @property
    def bit_exact(self) -> bool:
        return self.mismatched_bytes == 0


def bitexact_parity(a: np.ndarray, b: np.ndarray) -> ParityReport:
    a = np.asarray(a, dtype=np.uint8).reshape(-1)
    b = np.asarray(b, dtype=np.uint8).reshape(-1)
    if a.size != b.size:
        raise ValueError(f"byte-count mismatch: {a.size} vs {b.size}")
    diff = np.nonzero(a != b)[0]
    return ParityReport(
        total_bytes=int(a.size),
        mismatched_bytes=int(diff.size),
        first_mismatch_byte=int(diff[0]) if diff.size else None,
    )


def merge_parity_reports(reports: list[ParityReport]) -> ParityReport:
    offset = 0
    first: int | None = None
    mismatched = 0
    for report in reports:
        if first is None and report.first_mismatch_byte is not None:
            first = offset + report.first_mismatch_byte
        mismatched += report.mismatched_bytes
        offset += report.total_bytes
    return ParityReport(total_bytes=offset, mismatched_bytes=mismatched, first_mismatch_byte=first)


@dataclass(frozen=True)
class DemPairSupport:
    """EVALUATOR-SIDE support of the shipped noise model, in pair-class terms.

    Pair-class key: ``(|Δchain|, |Δlayer|, orientation)`` with orientation
    ``sign(Δchain·Δlayer)`` (0 when either delta is 0). Weight-1 errors are the
    boundary edges; weight-3+ are hyperedges (invisible to two-point p_ij).
    """

    pair_classes: frozenset
    pair_class_counts: dict
    single_detector_errors: int
    higher_weight_errors: int


def dem_pair_support(circuit, grid: DetectorGrid) -> DemPairSupport:
    singles = 0
    higher = 0
    pair_counts: dict[tuple[int, int, int], int] = {}
    for dets in _dem_detector_sets(circuit):
        if len(dets) == 1:
            singles += 1
        elif len(dets) == 2:
            a, b = sorted(dets)
            di = int(grid.det_to_chain[a]) - int(grid.det_to_chain[b])
            dt = int(grid.det_to_layer[a]) - int(grid.det_to_layer[b])
            orient = 0 if di == 0 or dt == 0 else (1 if di * dt > 0 else -1)
            key = (abs(di), abs(dt), orient)
            pair_counts[key] = pair_counts.get(key, 0) + 1
        elif len(dets) > 2:
            higher += 1
    return DemPairSupport(
        pair_classes=frozenset(pair_counts),
        pair_class_counts=pair_counts,
        single_detector_errors=singles,
        higher_weight_errors=higher,
    )
