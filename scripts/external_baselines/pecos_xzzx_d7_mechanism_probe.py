#!/usr/bin/env python3
"""Which non-Pauli mechanisms can PECOS's scalable MPS actually carry at XZZX d7?

`pecos_xzzx_d7_capability_worker.py` established that PECOS executes an XZZX d=7
multi-round Record with a coherent error injected, but it injects exactly one thing:
a single-qubit, single-axis ``RY(theta)`` layer after each complete round. That is the
weakest available reading of "non-Pauli", and it is the case the literature already
solves exactly: a uniform single-axis rotation is Gaussian, which is why Marton &
Asboth (Quantum 7, 1116 (2023)) reach a full 2D d=19 patch with exact fermionic
linear optics. Demonstrating capability on that mechanism demonstrates the least.

The MPS bindings expose 86 gates, and among them are the mechanisms that are NOT
free-fermion reducible:

  * ``RZZ`` -- two-qubit coherent rotation. Residual ZZ crosstalk is the physically
    dominant coherent error on superconducting hardware and is the model Harper,
    Nakhl, Sevior & Usman (arXiv:2605.29514v1) use for their d=9 result. Applied
    after every entangling gate on the same pair, following that paper.
  * ``T``/``Tdg`` -- maximally non-Clifford single-qubit gate.
  * ``R1XY`` -- two-angle rotation, so the error is not confined to one axis and the
    X- and Z-type check families both respond.

This probe runs the same frozen native construction as the capability worker and
swaps only the injected mechanism, so the comparison is like-for-like.

CLAIM BOUNDARY. One shot per mechanism establishes EXECUTION CAPABILITY only: that the
scalable MPS carries the mechanism through a d7 multi-round circuit and still emits a
folded Record. It is not a distribution, a logical error rate, a faithfulness claim, or
a bond-dimension convergence result. `chi` is fixed and no truncation certificate is
computed.

WHAT PECOS STILL CANNOT DO, verified separately and not by this script: its MPS gate
bindings contain no channel or Kraus entry at all, so no dissipative mechanism is
reachable on the scalable path; and its ``leak``/``unleak`` bindings are aliases for
state re-initialization (``bindings.py``: ``"leak": init_zero``), with leakage tracked
as a classical qubit set in the machine layer, so there is no third level in the state.

Preconditions
-------------
* the `ecs-baseline-pecos` environment;
* `LD_LIBRARY_PATH` containing that environment's `nvidia/cu13/lib`, which the
  capability worker's precondition check also demands.
"""

from __future__ import annotations

import argparse
from collections import Counter
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time
from typing import Any

REPO = Path(__file__).resolve().parents[2]

MECHANISMS = ("none", "ry_layer", "t_layer", "r1xy_layer", "rzz_per_2q")


def emit(line: str = "") -> None:
    print(line, flush=True)


def _gate_name(gate: Any) -> str:
    return str(gate.gate_type.name)


def _check_library_path() -> None:
    prefix = Path(sys.prefix).resolve()
    required = (
        prefix
        / "lib"
        / f"python{sys.version_info.major}.{sys.version_info.minor}"
        / "site-packages"
        / "nvidia"
        / "cu13"
        / "lib"
    ).resolve()
    configured = {
        Path(value).resolve()
        for value in os.environ.get("LD_LIBRARY_PATH", "").split(":")
        if value
    }
    if required not in configured:
        raise RuntimeError(
            f"LD_LIBRARY_PATH must contain the environment-local CUDA runtime: {required}"
        )


def run_shot(
    circuit: Any,
    *,
    mechanism: str,
    angle: float,
    chi: int,
    seed: int,
) -> tuple[list[int], dict[str, Any]]:
    from pecos.simulators.mps_pytket import MPS

    simulator = MPS(num_qubits=97, chi=chi, seed=seed)
    measurements: dict[int, int] = {}
    injections = 0
    layers = 0
    complete_rounds = 0
    started = time.monotonic()

    for tick_index in range(int(circuit.num_ticks())):
        tick = circuit.get_tick(tick_index)
        measure_free_count = 0
        for gate in tick.gate_batches():
            name = _gate_name(gate)
            qubits = [int(q) for q in gate.qubits]
            angles = tuple(float(a) for a in gate.angles)
            meas_ids = [int(m) for m in gate.meas_ids]

            if name == "QAlloc":
                for qubit in qubits:
                    simulator.run_gate("Init", {qubit})
                continue

            if name in {"MeasureFree", "MZ"}:
                for qubit, mid in zip(qubits, meas_ids, strict=True):
                    # Call the binding directly: run_gate tests the return value by
                    # truthiness and therefore drops a scalar zero outcome.
                    bit = int(simulator.bindings["Measure"](simulator, qubit))
                    if bit not in {0, 1}:
                        raise RuntimeError(f"non-bit measurement result {bit!r}")
                    if mid in measurements:
                        raise RuntimeError(f"duplicate measurement id {mid}")
                    measurements[mid] = bit
                if name == "MeasureFree":
                    measure_free_count += len(qubits)
                continue

            if name not in simulator.bindings:
                raise RuntimeError(f"PECOS MPS has no binding for {name!r}")
            locations: Any = {qubits[0]} if len(qubits) == 1 else {tuple(qubits)}
            parameters: dict[str, Any] = {"angles": angles} if angles else {}
            simulator.run_gate(name, locations, **parameters)

            # Harper-class residual ZZ crosstalk: an unwanted coherent ZZ rotation on
            # exactly the pair that was just entangled, injected per gate rather than
            # per round.
            if mechanism == "rzz_per_2q" and len(qubits) == 2 and angle:
                simulator.run_gate("RZZ", {tuple(qubits)}, angles=(angle,))
                injections += 1

        if measure_free_count == 48:
            complete_rounds += 1
            if angle and mechanism in {"ry_layer", "t_layer", "r1xy_layer"}:
                for data_qubit in range(49):
                    if mechanism == "ry_layer":
                        simulator.run_gate("RY", {data_qubit}, angles=(angle,))
                    elif mechanism == "t_layer":
                        simulator.run_gate("T", {data_qubit})
                    else:
                        simulator.run_gate(
                            "R1XY", {data_qubit}, angles=(angle, angle * 0.5)
                        )
                    injections += 1
                layers += 1

        if tick_index % 16 == 0 or tick_index + 1 == int(circuit.num_ticks()):
            emit(
                f"    tick={tick_index + 1}/{circuit.num_ticks()} "
                f"meas={len(measurements)} injections={injections}"
            )

    elapsed = time.monotonic() - started
    if sorted(measurements) != list(range(len(measurements))):
        raise RuntimeError("measurement ids are not a dense 0..n-1 range")
    raw = [measurements[i] for i in range(len(measurements))]
    return raw, {
        "elapsed_seconds": elapsed,
        "injections": injections,
        "injection_layers": layers,
        "complete_syndrome_layers": complete_rounds,
    }


def probe(*, mechanism: str, rounds: int, angle: float, chi: int, seed: int) -> dict[str, Any]:
    import numpy
    from pecos.qec.surface import (
        build_memory_circuit,
        extract_detection_events_and_observables,
    )

    circuit = build_memory_circuit(
        distance=7,
        rounds=rounds,
        basis="Z",
        interaction_basis="szz",
        clifford_frame_policy="checkerboard_xzzx",
    )
    counts: Counter[str] = Counter()
    for tick_index in range(int(circuit.num_ticks())):
        for gate in circuit.get_tick(tick_index).gate_batches():
            counts[_gate_name(gate)] += 1

    emit(f"  mechanism={mechanism} angle={angle} chi={chi} rounds={rounds}")
    raw, execution = run_shot(
        circuit, mechanism=mechanism, angle=angle, chi=chi, seed=seed
    )
    fired, flipped = extract_detection_events_and_observables(
        circuit, numpy.asarray([raw], dtype=numpy.uint8)
    )
    detectors = json.loads(circuit.get_meta("detectors") or "[]")
    observables = json.loads(circuit.get_meta("observables") or "[]")
    # The extractor returns per-shot lists of FIRED DETECTOR INDICES, not bit rows.
    # Summing them adds up indices; the count is the length.
    fired_count = len(fired[0])
    payload = {
        "mechanism": mechanism,
        "angle": angle,
        "chi": chi,
        "rounds": rounds,
        "raw_width": len(raw),
        "num_detectors": len(detectors),
        "num_observables": len(observables),
        "detector_events": fired_count,
        "observable_flips": len(flipped[0]),
        "two_qubit_gate_batches": int(counts.get("SZZ", 0) + counts.get("SZZdg", 0)),
        **execution,
    }
    emit(
        f"  -> raw={payload['raw_width']} detectors={payload['num_detectors']} "
        f"events={fired_count} obs_flips={payload['observable_flips']} "
        f"injections={payload['injections']} in {execution['elapsed_seconds']:.1f}s"
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mechanism",
        action="append",
        choices=MECHANISMS,
        help="repeatable; defaults to the full sweep",
    )
    parser.add_argument("--rounds", type=int, choices=(2, 7), default=7)
    parser.add_argument("--angle", type=float, default=0.02)
    parser.add_argument("--chi", type=int, default=16)
    parser.add_argument("--seed", type=int, default=314159)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    _check_library_path()
    versions = {
        name: importlib.metadata.version(name)
        for name in ("quantum-pecos", "pytket", "cupy-cuda13x")
        if _installed(name)
    }
    emit("PECOS non-Pauli mechanism probe at XZZX d7")
    emit(f"runtime {versions}")
    emit("one shot per mechanism: execution capability only, no distribution claim")
    emit()

    mechanisms = args.mechanism or list(MECHANISMS)
    results: list[dict[str, Any]] = []
    status = 0
    for mechanism in mechanisms:
        try:
            results.append(
                probe(
                    mechanism=mechanism,
                    rounds=args.rounds,
                    angle=0.0 if mechanism == "none" else args.angle,
                    chi=args.chi,
                    seed=args.seed,
                )
            )
        except Exception as exc:  # noqa: BLE001 - the failure IS the result here
            emit(f"  -> FAILED {type(exc).__name__}: {exc}")
            results.append({"mechanism": mechanism, "error": f"{type(exc).__name__}: {exc}"})
            status = 1
        emit()

    emit("summary")
    emit(f"  {'mechanism':<14s} {'raw':>4s} {'det':>4s} {'events':>7s} {'inj':>5s} {'secs':>7s}")
    for row in results:
        if "error" in row:
            emit(f"  {row['mechanism']:<14s} {row['error']}")
            continue
        emit(
            f"  {row['mechanism']:<14s} {row['raw_width']:>4d} {row['num_detectors']:>4d} "
            f"{row['detector_events']:>7d} {row['injections']:>5d} "
            f"{row['elapsed_seconds']:>7.1f}"
        )
    if args.output:
        args.output.write_text(json.dumps({"results": results}, indent=2), encoding="utf-8")
        emit(f"wrote {args.output}")
    return status


def _installed(name: str) -> bool:
    try:
        importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return False
    return True


if __name__ == "__main__":
    sys.exit(main())
