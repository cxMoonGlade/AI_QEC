#!/usr/bin/env python3
"""Run one PECOS XZZX d=7 MPS capability shot.

This worker deliberately stays outside the product package.  It executes
PECOS's native ``checkerboard_xzzx`` surface-memory circuit through the public
MPS gate bindings, preserves PECOS measurement ids as a raw per-shot Record,
and independently asks PECOS to fold that Record into detectors and the
logical observable.

The injected ``RY`` layer is a coherent non-Pauli control error.  It is useful
for answering the narrow execution-capability question, but it is neither an
amplitude-damping channel nor a leakage model.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import tempfile
import time
from typing import Any


SCHEMA = "error_coupling_simulator.external_pecos_xzzx_d7_capability.v1"
REPO = Path(__file__).resolve().parents[2]
ENVIRONMENT_LOCK = REPO / "baseline-environment-pecos-linux-64.lock.json"
EXPECTED_RUNTIME_DISTRIBUTIONS = {
    "quantum-pecos": "0.9.0.dev2",
    "pecos-rslib": "0.9.0.dev2",
    "pytket-cutensornet": "0.12.1",
    "cupy-cuda13x": "14.1.1",
    "cutensornet-cu13": "2.13.0",
}


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _is_non_pauli_active(strength: float) -> bool:
    return float(strength) != 0.0


def _native_round_semantics(rounds: int) -> dict[str, int]:
    if rounds not in {2, 7}:
        raise ValueError(f"unsupported PECOS capability rounds: {rounds}")
    return {
        "pecos_complete_rounds": rounds,
        "initial_partial_measurement_count": 24,
        "complete_round_measurement_count": 48,
        "syndrome_measurement_layer_count": rounds + 1,
        "expected_num_measurements": 24 + rounds * 48 + 49,
        "expected_num_detectors": 24 + rounds * 48,
        "expected_non_pauli_layers": rounds,
    }


def _validate_runtime_versions(installed: dict[str, str]) -> None:
    for name, expected in EXPECTED_RUNTIME_DISTRIBUTIONS.items():
        observed = installed.get(name)
        if observed != expected:
            raise RuntimeError(
                f"{name} version {observed!r}, expected {expected!r}"
            )
    extras = set(installed) - set(EXPECTED_RUNTIME_DISTRIBUTIONS)
    if extras:
        raise RuntimeError(f"unexpected runtime version keys: {sorted(extras)}")


def _gate_name(gate: Any) -> str:
    return str(gate.gate_type.name)


def _run_shot(
    circuit: Any,
    *,
    coherent_angle: float,
    chi: int,
    seed: int,
) -> tuple[list[int], dict[str, Any]]:
    import cupy
    from pecos.simulators import MPS

    qubits = sorted(int(qubit) for qubit in circuit.all_qubits())
    if qubits != list(range(97)):
        raise RuntimeError(f"unexpected PECOS d=7 qubits: {qubits!r}")

    simulator = MPS(
        num_qubits=97,
        chi=chi,
        seed=seed,
    )
    measurements: dict[int, int] = {}
    coherent_layers = 0
    coherent_applications = 0
    initialization_measurement_layers = 0
    complete_syndrome_layers = 0
    started = time.monotonic()

    for tick_index in range(int(circuit.num_ticks())):
        tick = circuit.get_tick(tick_index)
        measure_free_count = 0
        for gate in tick.gate_batches():
            name = _gate_name(gate)
            gate_qubits = [int(qubit) for qubit in gate.qubits]
            angles = tuple(float(angle) for angle in gate.angles)
            measurement_ids = [int(measurement) for measurement in gate.meas_ids]

            if name == "QAlloc":
                for qubit in gate_qubits:
                    simulator.run_gate("Init", {qubit})
                continue

            if name in {"MeasureFree", "MZ"}:
                if len(gate_qubits) != len(measurement_ids):
                    raise RuntimeError(
                        f"{name} qubit/measurement mismatch at tick {tick_index}"
                    )
                for qubit, measurement_id in zip(
                    gate_qubits,
                    measurement_ids,
                    strict=True,
                ):
                    # DefaultSimulator.run_gate drops a scalar zero because it
                    # tests the gate return by truthiness before populating its
                    # output dictionary.  Call the public binding directly so
                    # both measurement outcomes remain observable.
                    result = simulator.bindings["Measure"](simulator, qubit)
                    bit = int(result)
                    if bit not in {0, 1}:
                        raise RuntimeError(f"non-bit measurement result: {result!r}")
                    if measurement_id in measurements:
                        raise RuntimeError(
                            f"duplicate measurement id {measurement_id}"
                        )
                    measurements[measurement_id] = bit
                if name == "MeasureFree":
                    measure_free_count += len(gate_qubits)
                continue

            if name not in simulator.bindings:
                raise RuntimeError(
                    f"PECOS MPS has no binding for native gate {name!r}"
                )
            if len(gate_qubits) == 1:
                locations: set[int] | set[tuple[int, ...]] = {gate_qubits[0]}
            elif len(gate_qubits) == 2:
                locations = {tuple(gate_qubits)}
            else:
                raise RuntimeError(
                    f"unsupported native gate arity for {name}: {gate_qubits}"
                )
            parameters: dict[str, Any] = {}
            if angles:
                parameters["angles"] = angles
            simulator.run_gate(name, locations, **parameters)

        if measure_free_count == 24:
            initialization_measurement_layers += 1
        elif measure_free_count == 48:
            complete_syndrome_layers += 1
        elif measure_free_count:
            raise RuntimeError(
                f"unexpected MeasureFree layer width {measure_free_count}"
            )

        # The native PECOS circuit starts with one 24-check initialization
        # layer, then has ``rounds`` complete 48-check syndrome layers.  Match
        # the CUDA-Q fixture placement by injecting only after complete rounds.
        if measure_free_count == 48 and _is_non_pauli_active(coherent_angle):
            for data_qubit in range(49):
                simulator.run_gate(
                    "RY",
                    {data_qubit},
                    angles=(coherent_angle,),
                )
                coherent_applications += 1
            coherent_layers += 1

        if tick_index % 8 == 0 or tick_index + 1 == circuit.num_ticks():
            print(
                f"tick={tick_index + 1}/{circuit.num_ticks()} "
                f"measurements={len(measurements)} "
                f"coherent_layers={coherent_layers}",
                flush=True,
            )

    expected_ids = list(range(len(measurements)))
    observed_ids = sorted(measurements)
    if observed_ids != expected_ids:
        raise RuntimeError(
            "measurement ids are not a dense zero-based Record: "
            f"{observed_ids[:8]}...{observed_ids[-8:]}"
        )
    raw = [measurements[index] for index in expected_ids]
    if initialization_measurement_layers != 1:
        raise RuntimeError(
            "PECOS native circuit must have one 24-check initialization layer"
        )
    expected_rounds = int(circuit.get_meta("rounds") or 0)
    if expected_rounds and complete_syndrome_layers != expected_rounds:
        raise RuntimeError(
            f"complete syndrome layers {complete_syndrome_layers} "
            f"!= metadata rounds {expected_rounds}"
        )
    elapsed = time.monotonic() - started
    memory_pool = cupy.get_default_memory_pool()
    diagnostics = {
        "elapsed_seconds": elapsed,
        "coherent_layers": coherent_layers,
        "coherent_applications": coherent_applications,
        "initialization_measurement_layers": initialization_measurement_layers,
        "complete_syndrome_layers": complete_syndrome_layers,
        "cupy_memory_used_bytes": int(memory_pool.used_bytes()),
        "cupy_memory_total_bytes": int(memory_pool.total_bytes()),
    }
    return raw, diagnostics


def run(*, rounds: int, coherent_angle: float, chi: int, seed: int) -> dict[str, Any]:
    import cupy
    import numpy
    from pecos.qec.surface import (
        build_memory_circuit,
        extract_detection_events_and_observables,
    )

    installed = {
        name: importlib.metadata.version(name)
        for name in EXPECTED_RUNTIME_DISTRIBUTIONS
    }
    _validate_runtime_versions(installed)
    if not ENVIRONMENT_LOCK.is_file():
        raise RuntimeError(f"missing environment lock: {ENVIRONMENT_LOCK}")
    executable = Path(os.sys.executable).resolve()
    prefix = Path(os.sys.prefix).resolve()
    try:
        executable.relative_to(prefix)
    except ValueError as error:
        raise RuntimeError("Python executable escapes its environment") from error
    required_library_path = (
        prefix / "lib" / f"python{os.sys.version_info.major}.{os.sys.version_info.minor}"
        / "site-packages" / "nvidia" / "cu13" / "lib"
    ).resolve()
    configured_library_paths = {
        Path(value).resolve()
        for value in os.environ.get("LD_LIBRARY_PATH", "").split(":")
        if value
    }
    if required_library_path not in configured_library_paths:
        raise RuntimeError(
            "LD_LIBRARY_PATH does not include the environment-local CUDA "
            f"runtime directory: {required_library_path}"
        )

    built_at = time.monotonic()
    circuit = build_memory_circuit(
        distance=7,
        rounds=rounds,
        basis="Z",
        interaction_basis="szz",
        clifford_frame_policy="checkerboard_xzzx",
    )
    round_semantics = _native_round_semantics(rounds)
    build_seconds = time.monotonic() - built_at
    gate_counts: Counter[str] = Counter()
    gate_batches = 0
    measurement_ids: list[int] = []
    for tick_index in range(int(circuit.num_ticks())):
        for gate in circuit.get_tick(tick_index).gate_batches():
            name = _gate_name(gate)
            gate_counts[name] += 1
            gate_batches += 1
            measurement_ids.extend(int(value) for value in gate.meas_ids)

    raw, execution = _run_shot(
        circuit,
        coherent_angle=coherent_angle,
        chi=chi,
        seed=seed,
    )
    if execution["complete_syndrome_layers"] != rounds:
        raise RuntimeError(
            f"native complete syndrome layers "
            f"{execution['complete_syndrome_layers']} != requested rounds {rounds}"
        )
    expected_coherent_layers = (
        round_semantics["expected_non_pauli_layers"]
        if _is_non_pauli_active(coherent_angle)
        else 0
    )
    if execution["coherent_layers"] != expected_coherent_layers:
        raise RuntimeError(
            f"coherent layers {execution['coherent_layers']} "
            f"!= expected {expected_coherent_layers}"
        )
    raw_array = numpy.asarray([raw], dtype=numpy.uint8)
    fired_detectors, flipped_observables = extract_detection_events_and_observables(
        circuit,
        raw_array,
    )
    detector_definitions = json.loads(circuit.get_meta("detectors") or "[]")
    observable_definitions = json.loads(circuit.get_meta("observables") or "[]")
    if len(raw) != round_semantics["expected_num_measurements"]:
        raise RuntimeError(
            f"native Record width {len(raw)} "
            f"!= {round_semantics['expected_num_measurements']}"
        )
    if len(detector_definitions) != round_semantics["expected_num_detectors"]:
        raise RuntimeError(
            f"native detector width {len(detector_definitions)} "
            f"!= {round_semantics['expected_num_detectors']}"
        )
    fired_detector_indices = [int(value) for value in fired_detectors[0]]
    flipped_observable_indices = [
        int(value) for value in flipped_observables[0]
    ]
    detector_bits = [0] * len(detector_definitions)
    observable_bits = [0] * len(observable_definitions)
    for index in fired_detector_indices:
        detector_bits[index] = 1
    for index in flipped_observable_indices:
        observable_bits[index] = 1
    raw_bytes = bytes(raw)

    return {
        "schema": SCHEMA,
        "claim_boundary": (
            "external execution capability only; coherent RY is not a "
            "dissipative channel or leakage, and finite-chi output is not a "
            "faithfulness certificate"
        ),
        "runtime": {
            "python_version": os.sys.version.split()[0],
            "python_executable": str(executable),
            "python_prefix": str(prefix),
            "installed_distributions": installed,
            "cupy": cupy.__version__,
            "cuda_runtime_version": int(cupy.cuda.runtime.runtimeGetVersion()),
            "compute_capability": cupy.cuda.Device().compute_capability,
            "environment_lock": str(ENVIRONMENT_LOCK),
            "environment_lock_sha256": _file_sha256(ENVIRONMENT_LOCK),
            "required_cuda_library_path": str(required_library_path),
        },
        "circuit": {
            "family": "pecos_native_surface_memory_checkerboard_xzzx",
            "distance": 7,
            "rounds": rounds,
            "basis": "Z",
            "interaction_basis": "szz",
            "clifford_frame_policy": "checkerboard_xzzx",
            "num_qubits": len(circuit.all_qubits()),
            "num_ticks": int(circuit.num_ticks()),
            "num_gate_batches": gate_batches,
            "gate_counts": dict(sorted(gate_counts.items())),
            "num_measurements": len(measurement_ids),
            "measurement_ids_dense": sorted(measurement_ids)
            == list(range(len(measurement_ids))),
            "initialization_measurement_layer_checks": 24,
            "complete_syndrome_layers": rounds,
            "record_width_note": (
                "PECOS includes one 24-check initialization layer before the "
                "requested complete rounds; its raw/detector widths therefore "
                "differ from the neutral Stim fixture by 24"
            ),
            **round_semantics,
            "build_seconds": build_seconds,
        },
        "non_pauli": {
            "mechanism": "coherent_ry_overrotation",
            "angle_radians": coherent_angle,
            "placement": (
                "all 49 data qubits after each complete 48-check MeasureFree "
                "syndrome layer; not after the 24-check initialization layer "
                "or terminal data MZ"
            ),
            "is_non_pauli_active": _is_non_pauli_active(coherent_angle),
            "is_dissipative_kraus": False,
            "is_leakage": False,
        },
        "mps": {
            "maximum_bond_dimension": chi,
            "precision": "float64",
            "seed": seed,
        },
        "record": {
            "raw_bits": "".join(str(bit) for bit in raw),
            "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "raw_ones": sum(raw),
            "num_raw_measurements": len(raw),
            "detector_bits": "".join(str(bit) for bit in detector_bits),
            "detector_events": sum(detector_bits),
            "num_detectors": len(detector_bits),
            "fired_detector_indices": fired_detector_indices,
            "observable_bits": observable_bits,
            "flipped_observable_indices": flipped_observable_indices,
        },
        "execution": execution,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rounds", type=int, choices=(2, 7), required=True)
    parser.add_argument("--coherent-angle", type=float, default=0.02)
    parser.add_argument("--chi", type=int, default=16)
    parser.add_argument("--seed", type=int, default=314159)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.chi < 1:
        raise SystemExit("--chi must be positive")
    payload = run(
        rounds=args.rounds,
        coherent_angle=args.coherent_angle,
        chi=args.chi,
        seed=args.seed,
    )
    _atomic_json(args.output, payload)
    print(
        f"PECOS XZZX d=7 r={args.rounds}: "
        f"raw={payload['record']['num_raw_measurements']} "
        f"detectors={payload['record']['num_detectors']} "
        f"events={payload['record']['detector_events']} "
        f"elapsed={payload['execution']['elapsed_seconds']:.3f}s",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
