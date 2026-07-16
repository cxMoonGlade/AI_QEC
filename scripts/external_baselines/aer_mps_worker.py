#!/usr/bin/env python3
"""Execute one neutral circuit with Qiskit Aer MPS in an isolated process.

The repo-owned orchestrator starts this worker with ``conda run -n
ecs-baseline-aer``.  One invocation handles exactly one circuit and one bond
policy so Aer's process-global MPS log cannot leak across comparison rows.
"""

from __future__ import annotations

import argparse
import hashlib
from importlib import metadata
import json
from pathlib import Path
import sys
from typing import Any, Mapping

from aer_mps_protocol import (
    RESULT_SCHEMA,
    atomic_write_json,
    canonical_json_sha256,
    encode_complex_vector,
    parse_mps_log,
    read_json_object,
    validate_request,
    vector_norm_squared,
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _is_within(path: Path, directory: Path) -> bool:
    try:
        path.resolve().relative_to(directory.resolve())
        return True
    except ValueError:
        return False


def _runtime_identity(qiskit: Any, qiskit_aer: Any) -> dict[str, Any]:
    distribution = metadata.distribution("qiskit-aer")
    direct_url_text = distribution.read_text("direct_url.json")
    direct_url = json.loads(direct_url_text) if direct_url_text else None
    installer = (distribution.read_text("INSTALLER") or "").strip()
    distribution_root = Path(distribution.locate_file("")).resolve()
    distribution_files = list(distribution.files or ())
    record_files = [path for path in distribution_files if path.name == "RECORD"]
    if len(record_files) != 1:
        raise RuntimeError(
            f"expected exactly one qiskit-aer RECORD, found {len(record_files)}"
        )
    record_path = Path(distribution.locate_file(record_files[0])).resolve()
    package_hashes: dict[str, str] = {}
    selected_exact_paths = {
        "qiskit_aer/__init__.py",
        "qiskit_aer/backends/aer_simulator.py",
    }
    for relative in distribution_files:
        relative_text = str(relative)
        selected = (
            relative_text in selected_exact_paths
            or (
                "controller_wrappers" in relative_text
                and relative_text.endswith((".so", ".pyd", ".dylib"))
            )
        )
        if selected:
            installed_path = Path(distribution.locate_file(relative)).resolve()
            package_hashes[relative_text] = _sha256_file(installed_path)
    missing_exact_paths = selected_exact_paths - package_hashes.keys()
    if missing_exact_paths:
        raise RuntimeError(
            f"qiskit-aer distribution lacks selected files: {sorted(missing_exact_paths)}"
        )
    if not any("controller_wrappers" in path for path in package_hashes):
        raise RuntimeError("qiskit-aer distribution lacks a controller_wrappers binary")
    imported_module = Path(qiskit_aer.__file__).resolve()
    distribution_module = Path(
        distribution.locate_file("qiskit_aer/__init__.py")
    ).resolve()
    import_matches_distribution = imported_module == distribution_module
    if not import_matches_distribution:
        raise RuntimeError(
            "imported qiskit_aer module does not match metadata.distribution('qiskit-aer')"
        )
    executable = Path(sys.executable).resolve()
    prefix = Path(sys.prefix).resolve()
    executable_within_prefix = _is_within(executable, prefix)
    if not executable_within_prefix:
        raise RuntimeError("worker Python executable is outside sys.prefix")
    if direct_url is None and installer == "pip":
        installation_source = "pip_distribution_without_direct_url"
    elif direct_url is not None:
        installation_source = "distribution_with_direct_url"
    else:
        installation_source = "distribution_source_unclassified"
    return {
        "python_version": sys.version.split()[0],
        "python_executable": str(executable),
        "python_prefix": str(prefix),
        "python_executable_within_prefix": executable_within_prefix,
        "qiskit_version": qiskit.__version__,
        "qiskit_aer_version": qiskit_aer.__version__,
        "qiskit_aer_module_file": str(imported_module),
        "qiskit_aer_direct_url": direct_url,
        "qiskit_aer_installation_source": installation_source,
        "qiskit_aer_import_matches_distribution": import_matches_distribution,
        "qiskit_aer_distribution": {
            "name": distribution.metadata["Name"],
            "version": distribution.version,
            "installer": installer,
            "root": str(distribution_root),
            "record_path": str(record_path),
            "record_sha256": _sha256_file(record_path),
            "selected_package_sha256": package_hashes,
        },
    }


def _append_gate(circuit: Any, gate: Mapping[str, Any]) -> None:
    name = gate["name"]
    qubits = gate["qubits"]
    parameters = gate["parameters"]
    if name == "h":
        circuit.h(qubits[0])
    elif name == "x":
        circuit.x(qubits[0])
    elif name == "ry":
        circuit.ry(parameters[0], qubits[0])
    elif name == "rz":
        circuit.rz(parameters[0], qubits[0])
    elif name == "cx":
        circuit.cx(qubits[0], qubits[1])
    elif name == "cz":
        circuit.cz(qubits[0], qubits[1])
    elif name == "swap":
        circuit.swap(qubits[0], qubits[1])
    else:  # validate_request rejects this before Qiskit is imported.
        raise ValueError(f"unsupported gate: {name!r}")


def _saved_mps_summary(saved_mps: object) -> dict[str, Any]:
    import numpy as np

    if not isinstance(saved_mps, (tuple, list)) or len(saved_mps) != 2:
        raise RuntimeError("Aer save_matrix_product_state returned an unexpected container")
    site_tensors, schmidt_vectors = saved_mps
    site_shapes: list[list[list[int]]] = []
    for site_index, site in enumerate(site_tensors):
        if not isinstance(site, (tuple, list)) or len(site) != 2:
            raise RuntimeError(f"Aer MPS site {site_index} is not a two-matrix tensor")
        site_shapes.append(
            [
                [int(dimension) for dimension in np.asarray(matrix).shape]
                for matrix in site
            ]
        )
    schmidt_values = [
        [float(value) for value in np.asarray(vector, dtype=float).reshape(-1)]
        for vector in schmidt_vectors
    ]
    return {
        "num_sites": len(site_shapes),
        "site_tensor_shapes": site_shapes,
        "bond_dimensions": [len(values) for values in schmidt_values],
        "schmidt_values": schmidt_values,
    }


def _selected_metadata(raw_metadata: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "method",
        "device",
        "matrix_product_state_truncation_threshold",
        "matrix_product_state_max_bond_dimension",
        "matrix_product_state_sample_measure_algorithm",
        "matrix_product_state_lapack",
    )
    selected: dict[str, Any] = {}
    missing = [key for key in keys if key not in raw_metadata]
    if missing:
        raise RuntimeError(f"Aer result metadata lacks required MPS fields: {missing}")
    for key in keys:
        value = raw_metadata[key]
        if isinstance(value, (str, int, float, bool)) or value is None:
            selected[key] = value
        else:
            selected[key] = str(value)
    return selected


def execute(request: Mapping[str, Any]) -> dict[str, Any]:
    """Run one validated request and return a JSON-safe result."""

    request = validate_request(request)
    circuit_spec = request["circuit"]
    print(
        f"worker: validated {request['execution_id']} "
        f"({circuit_spec['num_qubits']} qubits, {len(circuit_spec['gates'])} gates)",
        flush=True,
    )

    # These imports happen only inside the dedicated external-runtime process.
    import numpy as np
    import qiskit
    from qiskit import QuantumCircuit
    import qiskit_aer
    from qiskit_aer import AerSimulator

    runtime = _runtime_identity(qiskit, qiskit_aer)
    print(
        "worker: runtime "
        f"qiskit={runtime['qiskit_version']} "
        f"qiskit-aer={runtime['qiskit_aer_version']}",
        flush=True,
    )

    circuit = QuantumCircuit(circuit_spec["num_qubits"], name=circuit_spec["id"])
    for gate in circuit_spec["gates"]:
        _append_gate(circuit, gate)
    # Saving the statevector first leaves save_mps last, allowing Aer to move the
    # final MPS container without invalidating the statevector snapshot.
    circuit.save_statevector(label="statevector")
    circuit.save_matrix_product_state(label="mps")

    configuration = {
        "method": "matrix_product_state",
        "device": "CPU",
        "seed_simulator": request["seed"],
        "truncation_threshold": request["truncation_threshold"],
        "max_bond_dimension": request["max_bond_dimension"],
        "mps_log_data": True,
        "mps_swap_direction": "mps_swap_left",
        "mps_lapack": False,
        "sample_measure_algorithm": "mps_apply_measure",
        # Aer uses this threshold to decide whether a positive discarded value
        # is printed.  Zero preserves every positive value in MPS_log_data.
        "chop_threshold": 0.0,
        "shots": 1,
    }
    simulator_options = {
        "method": configuration["method"],
        "device": configuration["device"],
        "matrix_product_state_truncation_threshold": configuration[
            "truncation_threshold"
        ],
        "mps_log_data": configuration["mps_log_data"],
        "mps_swap_direction": configuration["mps_swap_direction"],
        "mps_lapack": configuration["mps_lapack"],
        "mps_sample_measure_algorithm": configuration["sample_measure_algorithm"],
        "chop_threshold": configuration["chop_threshold"],
        "mps_omp_threads": 1,
        "max_parallel_threads": 1,
    }
    if configuration["max_bond_dimension"] is not None:
        simulator_options["matrix_product_state_max_bond_dimension"] = configuration[
            "max_bond_dimension"
        ]

    print(
        "worker: executing with "
        f"max_bond_dimension={configuration['max_bond_dimension']!r} "
        f"truncation_threshold={configuration['truncation_threshold']}",
        flush=True,
    )
    simulator = AerSimulator(**simulator_options)
    job = simulator.run(
        circuit,
        shots=configuration["shots"],
        seed_simulator=configuration["seed_simulator"],
    )
    aer_result = job.result()
    if not aer_result.success:
        raise RuntimeError(f"Aer execution failed: {aer_result.status}")
    data = aer_result.data(0)
    state = [complex(value) for value in np.asarray(data["statevector"]).reshape(-1)]
    raw_metadata = aer_result.results[0].metadata
    if "MPS_log_data" not in raw_metadata:
        raise RuntimeError("Aer result metadata lacks MPS_log_data")
    raw_log = raw_metadata["MPS_log_data"]
    if not isinstance(raw_log, str):
        raise RuntimeError("Aer result MPS_log_data is not a string")

    result = {
        "schema": RESULT_SCHEMA,
        "request_sha256": canonical_json_sha256(request),
        "execution_id": request["execution_id"],
        "circuit_id": circuit_spec["id"],
        "runtime": runtime,
        "configuration": configuration,
        "statevector": encode_complex_vector(state),
        "statevector_norm_squared": vector_norm_squared(state),
        "mps": _saved_mps_summary(data["mps"]),
        "mps_log": parse_mps_log(raw_log),
        "simulator_metadata": _selected_metadata(raw_metadata),
    }
    print(
        "worker: captured "
        f"bonds={result['mps']['bond_dimensions']} "
        f"discarded_values={result['mps_log']['discarded_value_count']}",
        flush=True,
    )
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="neutral request JSON")
    parser.add_argument("--output", type=Path, required=True, help="neutral result JSON")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    request = read_json_object(args.input)
    result = execute(request)
    output_hash = atomic_write_json(args.output, result)
    print(f"worker: wrote {args.output.name} sha256={output_hash}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
