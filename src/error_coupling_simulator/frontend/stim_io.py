from __future__ import annotations

"""Stim adapters for the simulator frontend."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .circuit_ir import (
    CircuitIR,
    DetectorDef,
    GateOp,
    MeasureOp,
    ObservableDef,
    Tick,
)


@dataclass(frozen=True)
class StimCounts:
    num_detectors: int
    num_observables: int
    num_measurements: int
    num_qubits: int


def circuit_to_stim(circuit: CircuitIR):
    """Convert key-based :class:`CircuitIR` to a concrete `stim.Circuit`."""

    import stim

    out = stim.Circuit()
    qubit_coords = _qubit_coords_from_metadata(circuit)
    for q in range(int(circuit.num_qubits)):
        out.append("QUBIT_COORDS", [q], qubit_coords.get(q, [float(q)]))
    key_to_measurement_index: dict[str, int] = {}
    measurement_count = 0
    for step in circuit.steps:
        if isinstance(step, Tick):
            out.append("TICK")
        elif isinstance(step, GateOp):
            out.append(step.name, list(step.targets), list(step.args))
        elif isinstance(step, MeasureOp):
            out.append(step.name, list(step.targets))
            for key in step.keys:
                key_to_measurement_index[key] = measurement_count
                measurement_count += 1
        elif isinstance(step, DetectorDef):
            targets = _record_targets(step.keys, key_to_measurement_index, measurement_count, stim)
            out.append("DETECTOR", targets, list(step.coords))
        elif isinstance(step, ObservableDef):
            targets = _record_targets(step.keys, key_to_measurement_index, measurement_count, stim)
            out.append("OBSERVABLE_INCLUDE", targets, float(step.index))
        else:  # pragma: no cover - exhaustive over CircuitStep
            raise TypeError(f"unknown circuit step {type(step)!r}")
    return out


def _record_targets(keys, key_to_measurement_index, measurement_count: int, stim):
    targets = []
    for key in keys:
        if key not in key_to_measurement_index:
            raise ValueError(f"record key {key!r} was not measured before this declaration")
        offset = key_to_measurement_index[key] - measurement_count
        if offset >= 0:
            raise ValueError(f"record key {key!r} is not in the past")
        targets.append(stim.target_rec(offset))
    return targets


def _qubit_coords_from_metadata(circuit: CircuitIR) -> dict[int, list[float]]:
    raw = circuit.metadata.get("qubit_coords", {})
    if not isinstance(raw, dict):
        raise ValueError("CircuitIR.metadata['qubit_coords'] must be a mapping if present")
    out: dict[int, list[float]] = {}
    for raw_key, raw_coords in raw.items():
        q = int(raw_key)
        if q < 0 or q >= int(circuit.num_qubits):
            raise ValueError(f"qubit_coords key {q} outside [0, {circuit.num_qubits})")
        coords = [float(c) for c in raw_coords]
        if not coords:
            raise ValueError(f"qubit_coords for qubit {q} must not be empty")
        out[q] = coords
    return out


def load_stim_circuit(path: str | Path):
    """Load a Stim circuit artifact."""

    import stim

    return stim.Circuit.from_file(str(path))


def write_stim_circuit(circuit, path: str | Path) -> Path:
    path = Path(path)
    path.write_text(str(circuit))
    return path


def write_detector_error_model(dem, path: str | Path) -> Path:
    path = Path(path)
    path.write_text(str(dem))
    return path


def detector_error_model(circuit, *, decompose_errors: bool = True):
    return circuit.detector_error_model(decompose_errors=decompose_errors)


def counts(circuit) -> StimCounts:
    return StimCounts(
        num_detectors=int(circuit.num_detectors),
        num_observables=int(circuit.num_observables),
        num_measurements=int(circuit.num_measurements),
        num_qubits=int(circuit.num_qubits),
    )


def sample_detector_records(
    circuit,
    *,
    shots: int,
    seed: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Sample detector events and observables as unpacked bool arrays."""

    n_det = int(circuit.num_detectors)
    n_obs = int(circuit.num_observables)
    sampler = circuit.compile_detector_sampler(seed=seed)
    samples = sampler.sample(int(shots), append_observables=True)
    samples = np.asarray(samples, dtype=np.bool_)
    det = samples[:, :n_det]
    obs = samples[:, n_det:n_det + n_obs]
    return det, obs
