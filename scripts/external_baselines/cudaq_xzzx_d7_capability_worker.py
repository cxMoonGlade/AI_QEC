#!/usr/bin/env python3
"""Run one neutral XZZX d=7 fixture with CUDA-Q's GPU MPS backend.

The worker is intentionally isolated from the ECS package.  It consumes the
neutral JSON emitted by ``emit_xzzx_d7_capability_fixture.py``, translates each
operation to a CUDA-Q builder instruction, and returns shot-level raw
measurements folded through the fixture's detector and logical-observable XOR
rows.

Amplitude damping is inserted once per completed syndrome round, on every data
qubit, after the last ancilla measure/reset and before the next operation.  It
is represented by its two explicit Kraus matrices, not by a Pauli
approximation.  This is an engineering capability probe; a finite MPS bond cap
does not establish record-law faithfulness.
"""

from __future__ import annotations

import argparse
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import resource
import sys
import tempfile
import time
from typing import Any, Mapping


FIXTURE_SCHEMA = "error_coupling_simulator.external_xzzx_d7.fixture.v1"
RESULT_SCHEMA = "error_coupling_simulator.external_cudaq_xzzx_d7.result.v2"
REPO = Path(__file__).resolve().parents[2]
ENVIRONMENT_LOCK = REPO / "baseline-environment-cudaq-qec-linux-64.lock.json"
EXPECTED_RUNTIME_DISTRIBUTIONS = {
    "cudaq": "0.14.2",
    "cuda-quantum-cu13": "0.14.2",
    "cudaq-qec": "0.6.0",
    "cudaq-qec-cu13": "0.6.0",
    "cutensornet-cu13": "2.12.2",
    "cupy-cuda13x": "13.6.0",
}
EXPECTED_CIRCUIT_FINGERPRINTS = {
    2: "193d56d199b45016d91e8d5742f52fdc4e8e3b74d571891c78e28f7ec4eca6bd",
    7: "20a32d1cd1293d4d4d6e74d8af04fe7b1300ddb82dbf734f558fb764ad27c4d7",
}
EXPECTED_CANONICAL_FIXTURE_HASHES = {
    2: "69f4be0f2e4020ba7dc16b58cf2edd1bb501936a984f75f9175168b267e62f13",
    7: "8cc3ff9ec1fbca540775b3e59e54bc97af607fad41c5379562752009532b70d2",
}


def _is_non_pauli_active(strength: float) -> bool:
    return float(strength) != 0.0


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


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_fixture(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("fixture JSON root must be an object")
    if value.get("schema") != FIXTURE_SCHEMA:
        raise ValueError(f"unsupported fixture schema: {value.get('schema')!r}")
    if value.get("distance") != 7:
        raise ValueError("worker accepts only distance-7 fixtures")
    rounds = value.get("rounds")
    if rounds not in {2, 7}:
        raise ValueError("worker accepts only the frozen 2- or 7-round fixtures")
    expected = {
        2: (97, 145, 96, 1),
        7: (97, 385, 336, 1),
    }[rounds]
    observed = tuple(
        value.get(key)
        for key in (
            "num_qubits",
            "num_measurements",
            "num_detectors",
            "num_observables",
        )
    )
    if observed != expected:
        raise ValueError(f"fixture shape mismatch: {observed} != {expected}")
    expected_fingerprint = EXPECTED_CIRCUIT_FINGERPRINTS[rounds]
    if value.get("stim_circuit_sha256") != expected_fingerprint:
        raise ValueError(
            "fixture circuit fingerprint mismatch: "
            f"{value.get('stim_circuit_sha256')!r} != {expected_fingerprint!r}"
        )
    operations = value.get("operations")
    if not isinstance(operations, list) or not operations:
        raise ValueError("fixture operations must be a nonempty list")
    allowed = {"R", "RX", "H", "CX", "M", "MX", "MR"}
    for index, operation in enumerate(operations):
        if not isinstance(operation, dict):
            raise ValueError(f"operation {index} is not an object")
        name = operation.get("op")
        qubits = operation.get("qubits")
        if name not in allowed:
            raise ValueError(f"operation {index} has unsupported op {name!r}")
        arity = 2 if name == "CX" else 1
        if (
            not isinstance(qubits, list)
            or len(qubits) != arity
            or any(
                isinstance(qubit, bool)
                or not isinstance(qubit, int)
                or not 0 <= qubit < value["num_qubits"]
                for qubit in qubits
            )
        ):
            raise ValueError(f"operation {index} has invalid qubits")
    measurement_order = value.get("measurement_order")
    if (
        not isinstance(measurement_order, list)
        or len(measurement_order) != value["num_measurements"]
    ):
        raise ValueError("fixture measurement order has the wrong length")
    expected_measurement_order = []
    for operation in operations:
        name = operation["op"]
        if name not in {"M", "MX", "MR"}:
            continue
        expected_measurement_order.append(
            {
                "column": len(expected_measurement_order),
                "qubit": operation["qubits"][0],
                "basis": "X" if name == "MX" else "Z",
                "reset": name == "MR",
            }
        )
    if measurement_order != expected_measurement_order:
        raise ValueError(
            "fixture measurement order does not match the executable operations"
        )
    for key, count in (
        ("detector_rows", value["num_detectors"]),
        ("observable_rows", value["num_observables"]),
    ):
        rows = value.get(key)
        if not isinstance(rows, list) or len(rows) != count:
            raise ValueError(f"fixture {key} has the wrong length")
        for row_index, row in enumerate(rows):
            if (
                not isinstance(row, list)
                or not row
                or any(
                    isinstance(column, bool)
                    or not isinstance(column, int)
                    or not 0 <= column < value["num_measurements"]
                    for column in row
                )
            ):
                raise ValueError(f"fixture {key}[{row_index}] is invalid")
    data_qubits = value.get("frame", {}).get("data_qubits")
    if (
        not isinstance(data_qubits, list)
        or len(data_qubits) != 49
        or len(set(data_qubits)) != 49
    ):
        raise ValueError("fixture must identify exactly 49 distinct data qubits")
    canonical = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    canonical_hash = hashlib.sha256(canonical).hexdigest()
    expected_canonical_hash = EXPECTED_CANONICAL_FIXTURE_HASHES[rounds]
    if canonical_hash != expected_canonical_hash:
        raise ValueError(
            "fixture canonical fingerprint mismatch: "
            f"{canonical_hash} != {expected_canonical_hash}"
        )
    value["_fixture_file_sha256"] = hashlib.sha256(raw).hexdigest()
    value["_fixture_canonical_sha256"] = canonical_hash
    return value


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (
        json.dumps(payload, allow_nan=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
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


def _fold(bits: list[int], rows: list[list[int]]) -> list[int]:
    return [sum(bits[column] for column in row) & 1 for row in rows]


def _runtime_identity(cudaq: Any) -> dict[str, Any]:
    import cupy

    device = cupy.cuda.runtime.getDeviceProperties(0)
    name = device["name"]
    if isinstance(name, bytes):
        name = name.decode("utf-8")
    installed = {
        name: metadata.version(name)
        for name in EXPECTED_RUNTIME_DISTRIBUTIONS
    }
    _validate_runtime_versions(installed)
    return {
        "python_version": sys.version.split()[0],
        "python_executable": str(Path(sys.executable).resolve()),
        "python_prefix": str(Path(sys.prefix).resolve()),
        "cudaq_version": str(cudaq.__version__),
        "cudaq_distribution_version": metadata.version("cudaq"),
        "cuda_quantum_cu13_version": metadata.version("cuda-quantum-cu13"),
        "cudaq_qec_version": metadata.version("cudaq-qec"),
        "cudaq_qec_cu13_version": metadata.version("cudaq-qec-cu13"),
        "cutensornet_cu13_version": metadata.version("cutensornet-cu13"),
        "cupy_version": cupy.__version__,
        "cuda_runtime_version": cupy.cuda.runtime.runtimeGetVersion(),
        "cuda_driver_version": cupy.cuda.runtime.driverGetVersion(),
        "gpu_count": cupy.cuda.runtime.getDeviceCount(),
        "gpu_name": str(name),
        "gpu_total_memory_bytes": int(device["totalGlobalMem"]),
        "installed_distributions": installed,
    }


def _amplitude_damping_channel(cudaq: Any, probability: float) -> Any:
    import numpy

    k0 = numpy.array(
        [[1.0, 0.0], [0.0, numpy.sqrt(1.0 - probability)]],
        dtype=numpy.complex128,
    )
    k1 = numpy.array(
        [[0.0, numpy.sqrt(probability)], [0.0, 0.0]],
        dtype=numpy.complex128,
    )
    return cudaq.KrausChannel(
        [cudaq.KrausOperator(k0), cudaq.KrausOperator(k1)]
    )


def _build_kernel(
    cudaq: Any,
    fixture: Mapping[str, Any],
    damping_probability: float,
) -> tuple[Any, Any | None, int]:
    kernel = cudaq.make_kernel()
    qubits = kernel.qalloc(fixture["num_qubits"])
    channel = (
        _amplitude_damping_channel(cudaq, damping_probability)
        if _is_non_pauli_active(damping_probability)
        else None
    )
    noise_model = cudaq.NoiseModel() if channel is not None else None
    data_qubits = fixture["frame"]["data_qubits"]
    ancillas_per_round = 48
    measured_and_reset = 0
    damping_applications = 0

    for operation in fixture["operations"]:
        name = operation["op"]
        operands = operation["qubits"]
        if name == "R":
            kernel.reset(qubits[operands[0]])
        elif name == "RX":
            kernel.reset(qubits[operands[0]])
            kernel.h(qubits[operands[0]])
        elif name == "H":
            kernel.h(qubits[operands[0]])
        elif name == "CX":
            kernel.cx(qubits[operands[0]], qubits[operands[1]])
        elif name == "M":
            kernel.mz(qubits[operands[0]])
        elif name == "MX":
            kernel.h(qubits[operands[0]])
            kernel.mz(qubits[operands[0]])
        elif name == "MR":
            kernel.mz(qubits[operands[0]])
            kernel.reset(qubits[operands[0]])
            measured_and_reset += 1
            if measured_and_reset % ancillas_per_round == 0 and channel is not None:
                for data_qubit in data_qubits:
                    kernel.apply_noise(channel, qubits[data_qubit])
                    damping_applications += 1
        else:
            raise AssertionError(f"validated unsupported op: {name}")

    expected_mr = fixture["rounds"] * ancillas_per_round
    if measured_and_reset != expected_mr:
        raise RuntimeError(
            f"round-boundary inference failed: {measured_and_reset} MR != {expected_mr}"
        )
    expected_damping = fixture["rounds"] * len(data_qubits)
    if channel is not None and damping_applications != expected_damping:
        raise RuntimeError(
            f"damping placement drift: {damping_applications} != {expected_damping}"
        )
    return kernel, noise_model, damping_applications


def _counts_to_records(
    counts: Any,
    fixture: Mapping[str, Any],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    total = 0
    for bitstring, frequency in sorted(counts.items()):
        raw = [int(bit) for bit in str(bitstring)]
        if len(raw) != fixture["num_measurements"]:
            raise RuntimeError(
                f"explicit measurement width {len(raw)} != "
                f"{fixture['num_measurements']}"
            )
        frequency = int(frequency)
        if frequency <= 0:
            raise RuntimeError("sample result contains a nonpositive frequency")
        total += frequency
        records.append(
            {
                "frequency": frequency,
                "raw_measurements": raw,
                "detector_bits": _fold(raw, fixture["detector_rows"]),
                "observable_bits": _fold(raw, fixture["observable_rows"]),
            }
        )
    if total <= 0:
        raise RuntimeError("sample result is empty")
    return records


def execute(args: argparse.Namespace) -> dict[str, Any]:
    fixture = _read_fixture(args.fixture)
    print(
        "worker: fixture validated "
        f"d=7 rounds={fixture['rounds']} qubits={fixture['num_qubits']} "
        f"measurements={fixture['num_measurements']}",
        flush=True,
    )

    os.environ["CUDAQ_MPS_MAX_BOND"] = str(args.max_bond)
    import cudaq

    runtime = _runtime_identity(cudaq)
    if not ENVIRONMENT_LOCK.is_file():
        raise RuntimeError(f"missing environment lock: {ENVIRONMENT_LOCK}")
    cudaq.set_random_seed(args.seed)
    cudaq.set_target("tensornet-mps", option=args.precision)
    kernel, noise_model, damping_applications = _build_kernel(
        cudaq,
        fixture,
        args.damping_probability,
    )
    print(
        "worker: kernel built "
        f"operations={len(fixture['operations'])} "
        f"damping_applications={damping_applications} "
        f"max_bond={args.max_bond} precision={args.precision}",
        flush=True,
    )

    start = time.monotonic()
    print("worker: CUDA-Q sample begin", flush=True)
    sample_kwargs = {
        "shots_count": args.shots,
        "explicit_measurements": True,
    }
    if noise_model is not None:
        sample_kwargs["noise_model"] = noise_model
    counts = cudaq.sample(kernel, **sample_kwargs)
    elapsed = time.monotonic() - start
    print(f"worker: CUDA-Q sample end elapsed_seconds={elapsed:.6f}", flush=True)
    records = _counts_to_records(counts, fixture)
    if sum(record["frequency"] for record in records) != args.shots:
        raise RuntimeError("sample frequencies do not sum to requested shots")

    max_rss_kib = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    result = {
        "schema": RESULT_SCHEMA,
        "claim_boundary": (
            "engineering capability only; finite-bond execution is not "
            "record-law or scientific faithfulness evidence"
        ),
        "fixture": {
            "path": str(args.fixture.resolve()),
            "file_sha256": fixture["_fixture_file_sha256"],
            "canonical_sha256": fixture["_fixture_canonical_sha256"],
            "stim_circuit_sha256": fixture["stim_circuit_sha256"],
            "family": fixture["family"],
            "distance": fixture["distance"],
            "rounds": fixture["rounds"],
            "num_qubits": fixture["num_qubits"],
            "num_measurements": fixture["num_measurements"],
            "num_detectors": fixture["num_detectors"],
            "num_observables": fixture["num_observables"],
        },
        "runtime": runtime,
        "environment_lock": {
            "path": str(ENVIRONMENT_LOCK),
            "sha256": _file_sha256(ENVIRONMENT_LOCK),
        },
        "configuration": {
            "target": cudaq.get_target().name,
            "precision": args.precision,
            "shots": args.shots,
            "seed": args.seed,
            "max_bond": args.max_bond,
            "damping_probability": args.damping_probability,
            "is_non_pauli_active": _is_non_pauli_active(
                args.damping_probability
            ),
            "damping_representation": "explicit_two_kraus_amplitude_damping",
            "damping_placement": (
                "after_each_complete_48_ancilla_measure_reset_round_"
                "on_all_49_data_qubits"
            ),
            "damping_applications": damping_applications,
        },
        "elapsed_seconds": elapsed,
        "max_rss_kib": max_rss_kib,
        "record_frequencies": records,
    }
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--shots", type=int, default=1)
    parser.add_argument("--seed", type=int, default=194)
    parser.add_argument("--max-bond", type=int, default=16)
    parser.add_argument("--precision", choices=("fp32", "fp64"), default="fp32")
    parser.add_argument("--damping-probability", type=float, default=0.01)
    args = parser.parse_args()
    if args.shots <= 0:
        parser.error("--shots must be positive")
    if args.seed < 0:
        parser.error("--seed must be nonnegative")
    if args.max_bond <= 0:
        parser.error("--max-bond must be positive")
    if not 0.0 <= args.damping_probability <= 1.0:
        parser.error("--damping-probability must be in [0, 1]")
    return args


def main() -> int:
    args = _parse_args()
    result = execute(args)
    _atomic_write_json(args.output_json, result)
    print(
        "worker: result written "
        f"{args.output_json} max_rss_kib={result['max_rss_kib']}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
