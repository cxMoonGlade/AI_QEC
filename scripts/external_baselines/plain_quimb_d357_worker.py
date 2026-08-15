#!/usr/bin/env python3
"""Ordinary-Quimb lane for the frozen d=3,5,7 unitary-prefix sweep.

This worker consumes one neutral fixture and emits one resource/performance
JSON file.  It deliberately has no GCAPEPS import and computes no complete
state, norm, probability, fidelity, measurement, reset, or Record quantity.
"""

from __future__ import annotations

import argparse
import ast
import errno
import hashlib
import importlib.util
from importlib import metadata
import json
import math
import os
from pathlib import Path
import resource
import secrets
import stat
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence


WORKER_SCHEMA = (
    "error_coupling_simulator.external.gcapeps_d357_plain_quimb_worker.v2"
)
EXPECTED_FORK_COMMIT = "6fbbf74cd36686ed30a4d8865697ce46e47056c1"
EXPECTED_FORK_TREE = "ffdfdf421fbe4d9674c2c88029710042fd18ae14"
EXPECTED_FORK_ORIGIN = "https://github.com/cxMoonGlade/quimb.git"
EXPECTED_PYPROJECT_SHA256 = (
    "c8b48e06ee8595be41cc5dff6d4f8e768a9064d5a0f84efaec5ff12a7e8aa344"
)
EXPECTED_PIXI_LOCK_SHA256 = (
    "854da99b417c69dbdca4118c2545656470ad4e0f276a606b1b8c3082f795db35"
)
EXPECTED_DISTANCES = (3, 5, 7)
EXPECTED_PEPS_SETTINGS = {
    "to_backend": None,
    "convert_eager": True,
    "max_bond": None,
    "cutoff": 1e-12,
    "renorm": False,
    "gauge_smudge": 0.0,
    "equilibrate_every": None,
}
EXPECTED_GATE_SHA256 = {
    "H": "b8a0541aa80b1a09f1847692e688d8f59e6f7b27904794cb34e3a00547af4cc1",
    "CX": "8147eeddb2b56869f494b2194eb43a7926d1bb5edb4d4f35c6fa9e9633dd4bf8",
}
THREAD_ENVIRONMENT = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "BLIS_NUM_THREADS",
)
_PROHIBITED_MODULE = ".".join(("quimb", "experimental", "gcapeps"))


def _canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise ValueError(f"duplicate JSON key: {key!r}")
        output[key] = value
    return output


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def _read_strict_json(path: Path) -> tuple[dict[str, Any], bytes]:
    lexical = path.absolute()
    resolved = lexical.resolve(strict=True)
    if lexical != resolved or not resolved.is_file():
        raise ValueError("fixture must be a nonsymlink regular file")
    if not stat.S_ISREG(resolved.stat().st_mode):
        raise ValueError("fixture must be a regular file")
    raw = resolved.read_bytes()
    payload = json.loads(
        raw,
        object_pairs_hook=_strict_object,
        parse_constant=_reject_json_constant,
    )
    if not isinstance(payload, dict):
        raise ValueError("fixture must contain one JSON object")
    return payload, raw


def _load_fixture_contract() -> tuple[Any, dict[str, str]]:
    path = Path(__file__).resolve(strict=True).with_name(
        "emit_gcapeps_d357_unitary_prefix_fixture.py"
    )
    spec = importlib.util.spec_from_file_location(
        "_gcapeps_d357_fixture_contract_plain",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load the d357 neutral fixture contract")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, {"path": str(path), "sha256": _file_sha256(path)}


def scan_plain_worker_source(source: str) -> dict[str, Any]:
    """Reject imports of the hybrid implementation in the plain lane."""

    tree = ast.parse(source)
    prohibited: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            prohibited.extend(
                alias.name
                for alias in node.names
                if alias.name == _PROHIBITED_MODULE
                or alias.name.startswith(_PROHIBITED_MODULE + ".")
            )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == _PROHIBITED_MODULE or module.startswith(
                _PROHIBITED_MODULE + "."
            ):
                prohibited.append(module)
    return {
        "passed": not prohibited,
        "prohibited_imports": sorted(set(prohibited)),
    }


def _require_no_hybrid_imports() -> None:
    loaded = sorted(
        name
        for name in sys.modules
        if name == _PROHIBITED_MODULE
        or name.startswith(_PROHIBITED_MODULE + ".")
    )
    if loaded:
        raise RuntimeError(
            "plain worker loaded prohibited hybrid modules: "
            + ", ".join(loaded)
        )


def _git(checkout: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(checkout), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def verify_fork_checkout(checkout: Path) -> dict[str, Any]:
    lexical = checkout.absolute()
    resolved = lexical.resolve(strict=True)
    if lexical != resolved or not resolved.is_dir():
        raise RuntimeError("fork checkout must be a nonsymlink directory")
    top = Path(_git(resolved, "rev-parse", "--show-toplevel")).resolve(
        strict=True
    )
    if top != resolved:
        raise RuntimeError("fork checkout is not its Git top level")
    commit = _git(resolved, "rev-parse", "HEAD")
    tree = _git(resolved, "rev-parse", "HEAD^{tree}")
    origin = _git(resolved, "remote", "get-url", "origin")
    dirty = _git(
        resolved,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--ignored",
    )
    if commit != EXPECTED_FORK_COMMIT or tree != EXPECTED_FORK_TREE:
        raise RuntimeError(
            f"fork identity drifted: commit={commit}, tree={tree}"
        )
    if origin != EXPECTED_FORK_ORIGIN:
        raise RuntimeError(f"fork origin drifted: {origin!r}")
    if dirty:
        raise RuntimeError(
            "fork checkout is not ignored-inclusive pristine:\n" + dirty
        )
    pyproject = resolved / "pyproject.toml"
    pixi_lock = resolved / "pixi.lock"
    if _file_sha256(pyproject) != EXPECTED_PYPROJECT_SHA256:
        raise RuntimeError("fork pyproject.toml hash drifted")
    if _file_sha256(pixi_lock) != EXPECTED_PIXI_LOCK_SHA256:
        raise RuntimeError("fork pixi.lock hash drifted")
    return {
        "path": str(resolved),
        "commit": commit,
        "tree": tree,
        "origin": origin,
        "clean_including_ignored": True,
        "pyproject_sha256": EXPECTED_PYPROJECT_SHA256,
        "pixi_lock_sha256": EXPECTED_PIXI_LOCK_SHA256,
    }


def verify_process_envelope() -> dict[str, Any]:
    if os.environ.get("PYTHONPATH") is not None:
        raise RuntimeError("PYTHONPATH must be absent")
    if sys.platform != "linux":
        raise RuntimeError("worker requires Linux resource semantics")
    if sys.version_info[:2] != (3, 13):
        raise RuntimeError("worker requires Python 3.13")
    if not sys.flags.no_user_site or not sys.dont_write_bytecode:
        raise RuntimeError("worker requires isolated imports and no bytecode")
    required = {
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "TZ": "UTC",
        "CUDA_VISIBLE_DEVICES": "",
    }
    for name, expected in required.items():
        if os.environ.get(name) != expected:
            raise RuntimeError(f"{name} must equal {expected!r}")
    for name in THREAD_ENVIRONMENT:
        if os.environ.get(name) != "1":
            raise RuntimeError(f"{name} must equal '1'")
    cache_raw = os.environ.get("NUMBA_CACHE_DIR")
    if cache_raw is None or not Path(cache_raw).is_absolute():
        raise RuntimeError("NUMBA_CACHE_DIR must be an absolute path")
    cache = Path(cache_raw).resolve(strict=True)
    if not cache.is_dir() or stat.S_IMODE(cache.stat().st_mode) & 0o077:
        raise RuntimeError("NUMBA_CACHE_DIR must be one private directory")
    affinity = sorted(int(cpu) for cpu in os.sched_getaffinity(0))
    if len(affinity) != 1:
        raise RuntimeError("worker must be pinned to exactly one CPU")
    return {
        "python_version": sys.version,
        "python_executable": str(Path(sys.executable).resolve(strict=True)),
        "python_prefix": str(Path(sys.prefix).resolve(strict=True)),
        "python_no_user_site": True,
        "python_dont_write_bytecode": True,
        "pythonpath_absent": True,
        "cpu_affinity": affinity,
        "thread_environment": {
            name: os.environ[name] for name in THREAD_ENVIRONMENT
        },
        "process_environment": {
            name: os.environ[name] for name in required
        },
        "numba_cache_directory": str(cache),
    }


def _validated_output_path(path: Path) -> tuple[Path, Path]:
    if not path.is_absolute():
        raise ValueError("--output must be absolute")
    lexical = path.absolute()
    if lexical.name in ("", ".", ".."):
        raise ValueError("--output must name one file")
    parent_lexical = lexical.parent
    parent = parent_lexical.resolve(strict=True)
    if parent_lexical != parent or not parent.is_dir():
        raise RuntimeError("output parent must be a nonsymlink directory")
    if stat.S_IMODE(parent.stat().st_mode) & 0o077:
        raise RuntimeError("output parent must not grant group/other access")
    if lexical.exists() or lexical.is_symlink():
        raise FileExistsError("output already exists")
    return lexical, parent


def _validate_fixture(
    fixture: Mapping[str, Any],
    raw: bytes,
    contract: Any,
) -> tuple[dict[str, Any], str]:
    if fixture.get("schema") != contract.FIXTURE_SCHEMA:
        raise ValueError("fixture schema drifted")
    canonical = contract.canonical_json_bytes(fixture)
    if raw != canonical:
        raise ValueError("fixture file is not frozen canonical JSON bytes")
    digest = contract.canonical_json_sha256(fixture)
    validated = contract.validate_fixture(fixture)
    if validated != digest:
        raise ValueError("fixture validator returned a different identity")
    frozen = json.loads(canonical)
    distance = frozen.get("distance")
    n_qubits = frozen.get("n_qubits")
    if (
        distance not in EXPECTED_DISTANCES
        or n_qubits != 2 * distance * distance - 1
        or frozen.get("dtype") != "complex128"
        or frozen.get("peps_settings") != EXPECTED_PEPS_SETTINGS
    ):
        raise ValueError("fixture headline/settings contract drifted")
    edges = frozen.get("graph", {}).get("edges")
    gates = frozen.get("prefix", {}).get("gates")
    cells = frozen.get("grid_cells")
    schedule = frozen.get("accumulated_frame_schedule", {}).get("rows")
    if not all(isinstance(value, list) for value in (edges, gates, cells, schedule)):
        raise ValueError("fixture graph/prefix/grid/schedule is unavailable")
    expected_sites = set(range(n_qubits))
    seen_sites: set[int] = set()
    edge_keys: set[frozenset[int]] = set()
    for edge in edges:
        if (
            not isinstance(edge, list)
            or len(edge) != 2
            or any(isinstance(q, bool) or not isinstance(q, int) for q in edge)
            or edge[0] >= edge[1]
            or any(q not in expected_sites for q in edge)
        ):
            raise ValueError("fixture graph edge is invalid")
        key = frozenset(edge)
        if key in edge_keys:
            raise ValueError("fixture graph contains a duplicate edge")
        edge_keys.add(key)
        seen_sites.update(edge)
    if seen_sites != expected_sites:
        raise ValueError("fixture graph does not cover every compact site")
    for index, row in enumerate(gates):
        if not isinstance(row, dict) or row.get("index") != index:
            raise ValueError("fixture prefix row index drifted")
        token = row.get("token")
        targets = row.get("targets")
        arity = 1 if token == "H" else 2 if token == "CX" else 0
        if (
            arity == 0
            or not isinstance(targets, list)
            or len(targets) != arity
            or len(set(targets)) != arity
            or any(
                isinstance(q, bool)
                or not isinstance(q, int)
                or q not in expected_sites
                for q in targets
            )
        ):
            raise ValueError("fixture prefix gate is invalid")
        if arity == 2 and frozenset(targets) not in edge_keys:
            raise ValueError("fixture CX is outside the compact graph")
    cell_ids = [row.get("cell_id") for row in cells if isinstance(row, dict)]
    if len(cell_ids) != 8 or len(set(cell_ids)) != 8:
        raise ValueError("fixture must contain eight unique grid cells")
    if len(schedule) != distance * 4:
        raise ValueError("fixture accumulated-frame schedule width drifted")
    return frozen, digest


def _select_cell(
    fixture: Mapping[str, Any],
    cell_id: str,
) -> dict[str, Any]:
    if not isinstance(cell_id, str) or not cell_id:
        raise ValueError("cell-id must be nonempty text")
    matches = [
        row for row in fixture["grid_cells"] if row.get("cell_id") == cell_id
    ]
    if len(matches) != 1:
        raise ValueError(f"unknown or duplicate grid cell: {cell_id!r}")
    cell = dict(matches[0])
    distance = int(fixture["distance"])
    layers = cell.get("round_layers")
    complexity = cell.get("noise_complexity")
    targets = cell.get("selected_targets")
    operations = cell.get("operation_ledger")
    if (
        isinstance(layers, bool)
        or not isinstance(layers, int)
        or layers < 1
        or layers > distance
        or complexity not in (1, 2, 4)
        or not isinstance(targets, list)
        or len(targets) != complexity
        or not isinstance(operations, list)
        or len(operations) != layers * (complexity + 1)
        or cell.get("prefix_application_count") != layers
        or cell.get("rotation_count") != layers * complexity
    ):
        raise ValueError("grid cell execution dimensions drifted")
    theta = cell.get("theta_radians")
    probability = cell.get("p_twirl")
    if (
        not isinstance(theta, float)
        or not isinstance(probability, float)
        or theta.hex() != cell.get("theta_float64_hex")
        or probability.hex() != cell.get("p_twirl_float64_hex")
        or not math.isclose(
            math.sin(theta / 2.0) ** 2,
            probability,
            rel_tol=0.0,
            abs_tol=8.0 * sys.float_info.epsilon,
        )
    ):
        raise ValueError("grid cell probability/angle mapping drifted")
    return cell

def _validate_import_origin(path: Path, checkout: Path, *, label: str) -> str:
    lexical = path.absolute()
    resolved = lexical.resolve(strict=True)
    if lexical != resolved or not resolved.is_relative_to(checkout):
        raise RuntimeError(f"{label} import origin escapes the frozen fork")
    return str(resolved)


def _runtime_imports(
    checkout: Path,
) -> tuple[Any, Any, dict[str, Any]]:
    _require_no_hybrid_imports()
    import numpy as np
    import quimb
    import quimb.tensor as qtn

    _require_no_hybrid_imports()
    quimb_origin = _validate_import_origin(
        Path(quimb.__file__),
        checkout,
        label="Quimb",
    )
    tensor_origin = _validate_import_origin(
        Path(qtn.__file__),
        checkout,
        label="Quimb tensor",
    )
    return (
        np,
        qtn,
        {
            "numpy_version": np.__version__,
            "numpy_import_origin": str(Path(np.__file__).resolve(strict=True)),
            "quimb_distribution_version": metadata.version("quimb"),
            "quimb_import_origin": quimb_origin,
            "quimb_tensor_import_origin": tensor_origin,
            "hybrid_imported": False,
        },
    )


def _matrix(np: Any, token: str) -> Any:
    if token == "H":
        scale = np.float64(1.0) / np.sqrt(np.float64(2.0))
        values = ((scale, scale), (scale, -scale))
    elif token == "CX":
        values = (
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 1.0, 0.0, 0.0),
            (0.0, 0.0, 0.0, 1.0),
            (0.0, 0.0, 1.0, 0.0),
        )
    else:
        raise ValueError(f"unsupported gate token: {token!r}")
    matrix = np.ascontiguousarray(np.asarray(values, dtype="<c16"))
    digest = _sha256_bytes(matrix.tobytes(order="C"))
    if digest != EXPECTED_GATE_SHA256[token]:
        raise RuntimeError(f"{token} matrix identity drifted")
    identity = np.eye(matrix.shape[0], dtype=np.complex128)
    residual = float(np.max(np.abs(matrix.conj().T @ matrix - identity)))
    if not math.isfinite(residual) or residual > 8 * np.finfo(np.float64).eps:
        raise RuntimeError(f"{token} matrix is outside the unitarity band")
    return matrix


def _local_ry(np: Any, angle: float) -> Any:
    half = np.float64(angle) / np.float64(2.0)
    identity = np.eye(2, dtype="<c16")
    y = np.asarray(((0.0, -1.0j), (1.0j, 0.0)), dtype="<c16")
    matrix = np.ascontiguousarray(
        np.cos(half) * identity - 1.0j * np.sin(half) * y
    )
    if matrix.dtype.str != "<c16" or not np.all(np.isfinite(matrix)):
        raise RuntimeError("local RY matrix left the c128 lane")
    residual = float(
        np.max(np.abs(matrix.conj().T @ matrix - np.eye(2, dtype="<c16")))
    )
    if residual > 8 * np.finfo(np.float64).eps:
        raise RuntimeError("local RY matrix is outside the unitarity band")
    return matrix


def _representation_snapshot(
    circuit: Any,
    *,
    np: Any,
    n_qubits: int,
    edges: tuple[tuple[int, int], ...],
) -> dict[str, Any]:
    psi = circuit._psi
    if int(psi.num_tensors) != n_qubits:
        raise RuntimeError("PEPS does not contain one tensor per compact site")
    total_elements = 0
    maximum_site_elements = 0
    for site in range(n_qubits):
        array = np.asarray(psi[site].data)
        if (
            array.dtype != np.dtype("complex128")
            or array.dtype.str != "<c16"
            or not np.all(np.isfinite(array))
        ):
            raise RuntimeError("PEPS tensor left the finite little-endian c128 lane")
        elements = int(array.size)
        total_elements += elements
        maximum_site_elements = max(maximum_site_elements, elements)
    bond_dimensions: list[int] = []
    for left, right in edges:
        bond = psi.bond(left, right)
        dimension = int(psi.ind_size(bond))
        if dimension <= 0:
            raise RuntimeError("PEPS bond dimension is nonpositive")
        bond_dimensions.append(dimension)
    gauges = circuit.gauges
    gauge_elements = 0
    gauge_bytes = 0
    for value in gauges.values():
        array = np.asarray(value)
        if array.dtype not in (np.dtype("float64"), np.dtype("complex128")):
            raise RuntimeError("Vidal gauge dtype drifted")
        if array.ndim != 1 or not np.all(np.isfinite(array)):
            raise RuntimeError("Vidal gauge is invalid")
        gauge_elements += int(array.size)
        gauge_bytes += int(array.nbytes)
    return {
        "tensor_count": n_qubits,
        "edge_count": len(edges),
        "maximum_bond_dimension": max(bond_dimensions),
        "bond_dimensions": bond_dimensions,
        "total_tensor_elements": total_elements,
        "maximum_site_tensor_elements": maximum_site_elements,
        "logical_tensor_bytes": total_elements * 16,
        "gauge_elements": gauge_elements,
        "logical_gauge_bytes": gauge_bytes,
        "dtype": "complex128",
        "epistemic_class": "numerical_only_representation_resource",
    }


def _positive_elapsed(started: int, *, name: str) -> int:
    elapsed = time.perf_counter_ns() - started
    if elapsed <= 0:
        raise RuntimeError(f"{name} timing is not positive")
    return elapsed


def _read_cgroup_memory_peak() -> dict[str, Any]:
    try:
        lines = Path("/proc/self/cgroup").read_text(encoding="utf-8").splitlines()
        unified = next(line for line in lines if line.startswith("0::"))
        relative = unified.split("::", 1)[1].lstrip("/")
        path = Path("/sys/fs/cgroup") / relative / "memory.peak"
        value = int(path.read_text(encoding="ascii").strip())
        if value < 0:
            raise ValueError("negative memory.peak")
        return {"status": "available", "bytes": value, "source": str(path)}
    except (OSError, StopIteration, ValueError) as exc:
        return {
            "status": "unavailable",
            "bytes": None,
            "source": None,
            "reason": f"{type(exc).__name__}: {exc}",
        }


def _resource_usage(started: resource.struct_rusage) -> dict[str, Any]:
    ended = resource.getrusage(resource.RUSAGE_SELF)
    peak_kib = int(ended.ru_maxrss)
    return {
        "ru_maxrss": peak_kib,
        "ru_maxrss_units": "KiB_on_linux",
        "peak_rss_bytes": peak_kib * 1024,
        "process_user_time_ns": int(
            max(0.0, ended.ru_utime - started.ru_utime) * 1_000_000_000
        ),
        "process_system_time_ns": int(
            max(0.0, ended.ru_stime - started.ru_stime) * 1_000_000_000
        ),
        "cgroup_memory_peak": _read_cgroup_memory_peak(),
    }


def _require_operation(
    operations: Sequence[Mapping[str, Any]],
    index: int,
    *,
    layer: int,
    kind: str,
    target: int | None = None,
) -> Mapping[str, Any]:
    try:
        row = operations[index]
    except IndexError as exc:
        raise RuntimeError("cell operation ledger ended early") from exc
    if (
        row.get("operation_index") != index
        or row.get("layer") != layer
        or row.get("kind") != kind
        or (target is not None and row.get("target") != target)
    ):
        raise RuntimeError("cell operation ledger order drifted")
    return row


def compute_plain_candidate(
    fixture: Mapping[str, Any],
    *,
    cell: Mapping[str, Any],
    fixture_sha256: str,
    fork_checkout: Path,
) -> dict[str, Any]:
    np, qtn, imports = _runtime_imports(fork_checkout)
    n_qubits = int(fixture["n_qubits"])
    distance = int(fixture["distance"])
    edges = tuple(tuple(int(q) for q in edge) for edge in fixture["graph"]["edges"])
    rows = fixture["prefix"]["gates"]
    layers = int(cell["round_layers"])
    complexity = int(cell["noise_complexity"])
    selected_targets = tuple(int(q) for q in cell["selected_targets"])
    operations = tuple(cell["operation_ledger"])

    circuit = qtn.CircuitPEPSSimpleUpdate(
        psi0=None,
        edges=edges,
        max_bond=None,
        cutoff=1e-12,
        renorm=False,
        gauge_smudge=0.0,
        equilibrate_every=None,
        dtype="complex128",
        to_backend=None,
        convert_eager=True,
    )
    initial = _representation_snapshot(
        circuit,
        np=np,
        n_qubits=n_qubits,
        edges=edges,
    )
    if initial["maximum_bond_dimension"] != 1:
        raise RuntimeError("plain PEPS did not begin as a product state")

    raw_prefix = []
    for row in rows:
        token = str(row["token"])
        matrix = _matrix(np, token)
        digest = _sha256_bytes(matrix.tobytes(order="C"))
        if row["matrix_sha256"] != digest:
            raise RuntimeError("fixture gate matrix binding drifted")
        raw_prefix.append(
            qtn.Gate.from_raw(matrix, qubits=tuple(int(q) for q in row["targets"]))
        )
    raw_prefix_tuple = tuple(raw_prefix)
    theta = float(cell["theta_radians"])
    ry = _local_ry(np, theta)
    ry_sha256 = _sha256_bytes(ry.tobytes(order="C"))
    raw_rotations = {
        target: qtn.Gate.from_raw(ry, qubits=(target,))
        for target in selected_targets
    }

    prefix_total_ns = 0
    rotation_total_ns = 0
    prefix_batches_completed = 0
    completed_layers = 0
    completed_rotations = 0
    operation_index = 0
    timing_rows: list[dict[str, Any]] = []
    after_prefix = None
    for layer in range(1, layers + 1):
        operation = _require_operation(
            operations,
            operation_index,
            layer=layer,
            kind="clifford_prefix",
        )
        if (
            operation.get("prefix_gate_count") != len(rows)
            or operation.get("prefix_gate_stream_sha256")
            != fixture["prefix"]["gate_stream_sha256"]
        ):
            raise RuntimeError("cell prefix operation binding drifted")
        started = time.perf_counter_ns()
        circuit.apply_gates(raw_prefix_tuple)
        elapsed = _positive_elapsed(started, name="physical prefix apply")
        prefix_total_ns += elapsed
        prefix_batches_completed += 1
        timing_rows.append(
            {
                "operation_index": operation_index,
                "layer": layer,
                "kind": "clifford_prefix",
                "target": None,
                "elapsed_ns": elapsed,
                "status": "completed",
            }
        )
        operation_index += 1
        if after_prefix is None:
            after_prefix = _representation_snapshot(
                circuit,
                np=np,
                n_qubits=n_qubits,
                edges=edges,
            )
        for target in selected_targets:
            operation = _require_operation(
                operations,
                operation_index,
                layer=layer,
                kind="physical_ry",
                target=target,
            )
            if (
                operation.get("theta_radians") != theta
                or operation.get("theta_float64_hex") != theta.hex()
            ):
                raise RuntimeError("cell rotation angle binding drifted")
            started = time.perf_counter_ns()
            circuit.apply_gates((raw_rotations[target],))
            elapsed = _positive_elapsed(started, name="physical local RY apply")
            rotation_total_ns += elapsed
            completed_rotations += 1
            timing_rows.append(
                {
                    "operation_index": operation_index,
                    "layer": layer,
                    "kind": "physical_ry",
                    "target": target,
                    "elapsed_ns": elapsed,
                    "status": "completed",
                }
            )
            operation_index += 1
        completed_layers = layer
    if operation_index != len(operations):
        raise RuntimeError("cell operation ledger has unconsumed rows")
    expected_gate_count = layers * len(rows) + layers * complexity
    if circuit.num_gates != expected_gate_count:
        raise RuntimeError("plain persistent-state gate count drifted")
    final = _representation_snapshot(
        circuit,
        np=np,
        n_qubits=n_qubits,
        edges=edges,
    )
    if after_prefix is None:
        raise RuntimeError("plain execution produced no prefix snapshot")
    _require_no_hybrid_imports()
    return {
        "schema": WORKER_SCHEMA,
        "status": "completed",
        "lane": "plain_quimb_persistent_physical_layers_plus_local_ry",
        "claim_boundary": fixture["claim_boundary"],
        "fixture": {
            "schema": fixture["schema"],
            "fixture_id": fixture["fixture_id"],
            "canonical_sha256": fixture_sha256,
            "distance": distance,
            "n_qubits": n_qubits,
            "dtype": fixture["dtype"],
            "prefix_gate_count": len(rows),
            "prefix_stream_sha256": fixture["prefix"]["gate_stream_sha256"],
            "graph_edge_count": len(edges),
            "graph_edge_stream_sha256": fixture["graph"]["edge_stream_sha256"],
            "grid_cells_sha256": fixture["grid_cells_sha256"],
            "cell_id": cell["cell_id"],
            "role": cell["role"],
            "round_layers": layers,
            "noise_complexity": complexity,
            "p_twirl": float(cell["p_twirl"]),
            "p_twirl_float64_hex": cell["p_twirl_float64_hex"],
            "theta_radians": theta,
            "theta_float64_hex": cell["theta_float64_hex"],
            "selected_targets": list(selected_targets),
            "expected_rotation_count": int(cell["rotation_count"]),
        },
        "numerical_settings": {
            "dtype": "complex128",
            **EXPECTED_PEPS_SETTINGS,
        },
        "rotation": {
            "physical_pauli": "Y",
            "selected_targets": list(selected_targets),
            "theta_radians": theta,
            "theta_float64_hex": theta.hex(),
            "p_twirl": float(cell["p_twirl"]),
            "active_rank_per_rotation": 2,
            "matrix_sha256_c_order_little_endian_c128": ry_sha256,
            "construction": "cos(theta/2)*I-i*sin(theta/2)*Y",
            "raw_gate": True,
        },
        "progress": {
            "persistent_state_instances": 1,
            "prefix_batches_completed": prefix_batches_completed,
            "completed_layers": completed_layers,
            "completed_rotations": completed_rotations,
            "attempted_rotations": completed_rotations,
            "expected_layers": layers,
            "expected_rotations": layers * complexity,
        },
        "timing_ns": {
            "physical_prefix_apply_ns": prefix_total_ns,
            "physical_local_ry_apply_ns": rotation_total_ns,
            "update_ns": prefix_total_ns + rotation_total_ns,
            "operation_rows": timing_rows,
        },
        "timing_policy": {
            "update_formula": (
                "sum(physical_prefix_apply_ns)+sum(physical_local_ry_apply_ns)"
            ),
            "prefix_submitted_as_one_raw_gate_tuple_per_layer": True,
            "gate_materialization_excluded_from_update": True,
            "initialization_import_fixture_and_snapshots_excluded_from_update": True,
            "worker_total_includes_one_provisional_report_serialization": True,
            "final_atomic_publication_excluded_from_worker_total": True,
        },
        "representation": {
            "initial": initial,
            "after_prefix": after_prefix,
            "final": final,
        },
        "imports": imports,
        "candidate_semantics": {
            "is_truth": False,
            "complete_state_contraction_performed": False,
            "norm_computed": False,
            "fidelity_computed": False,
            "measurement_reset_or_record_computed": False,
            "finite_bond_cap": None,
            "cutoff_role": "floating_svd_null_direction_pruning_only",
            "round_layers_are_complete_qec_rounds": False,
            "p_twirl_is_sampled_frequency": False,
        },
    }

def _atomic_publish_noreplace(path: Path, payload: bytes) -> str:
    path, parent = _validated_output_path(path)
    directory_fd = os.open(
        parent,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | os.O_CLOEXEC,
    )
    stage = f".{path.name}.stage-{os.getpid()}-{secrets.token_hex(8)}"
    descriptor = -1
    staged = False
    try:
        descriptor = os.open(
            stage,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC,
            0o600,
            dir_fd=directory_fd,
        )
        staged = True
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        try:
            os.link(
                stage,
                path.name,
                src_dir_fd=directory_fd,
                dst_dir_fd=directory_fd,
                follow_symlinks=False,
            )
        except OSError as exc:
            if exc.errno == errno.EEXIST:
                raise FileExistsError("output appeared before publication") from exc
            raise
        os.unlink(stage, dir_fd=directory_fd)
        staged = False
        os.fsync(directory_fd)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if staged:
            try:
                os.unlink(stage, dir_fd=directory_fd)
            except FileNotFoundError:
                pass
        os.close(directory_fd)
    resolved = path.resolve(strict=True)
    if resolved != path or not stat.S_ISREG(resolved.stat().st_mode):
        raise RuntimeError("published output is not the sealed regular file")
    digest = _file_sha256(resolved)
    if digest != _sha256_bytes(payload):
        raise RuntimeError("published output bytes changed")
    return digest


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--fork-checkout", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cell-id", required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    worker_started = time.perf_counter_ns()
    usage_started = resource.getrusage(resource.RUSAGE_SELF)
    args = _parse_args(argv)
    worker_path = Path(__file__).resolve(strict=True)
    worker_sha256 = _file_sha256(worker_path)
    static_scan = scan_plain_worker_source(worker_path.read_text(encoding="utf-8"))
    if not static_scan["passed"]:
        raise RuntimeError("plain worker prohibited-import scan failed")
    process_envelope = verify_process_envelope()
    output_path, _ = _validated_output_path(args.output)
    fork_before = verify_fork_checkout(args.fork_checkout)
    contract, contract_source = _load_fixture_contract()
    fixture, raw_fixture = _read_strict_json(args.fixture)
    frozen, fixture_sha256 = _validate_fixture(
        fixture,
        raw_fixture,
        contract,
    )
    cell = _select_cell(frozen, args.cell_id)
    result = compute_plain_candidate(
        frozen,
        cell=cell,
        fixture_sha256=fixture_sha256,
        fork_checkout=Path(fork_before["path"]),
    )
    if _file_sha256(worker_path) != worker_sha256:
        raise RuntimeError("worker source changed during execution")
    fork_after = verify_fork_checkout(args.fork_checkout)
    if fork_after != fork_before:
        raise RuntimeError("fork identity changed during execution")
    result["fork"] = fork_before
    result["process_envelope"] = process_envelope
    result["resource_usage"] = _resource_usage(usage_started)
    result["provenance"] = {
        "worker_path": str(worker_path),
        "worker_sha256": worker_sha256,
        "fixture_path": str(args.fixture.resolve(strict=True)),
        "fixture_file_sha256": _sha256_bytes(raw_fixture),
        "fixture_contract_source": contract_source,
        "plain_source_scan": static_scan,
        "fork_pristine_before_and_after": True,
        "candidate_or_reference_output_inputs": [],
        "atomic_no_replace_output": True,
        "output_path": str(output_path),
    }
    json.dumps(result, allow_nan=False, ensure_ascii=False, sort_keys=True)
    result["timing_ns"]["worker_total_ns"] = _positive_elapsed(
        worker_started,
        name="worker total",
    )
    encoded = (
        json.dumps(
            result,
            allow_nan=False,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    output_sha256 = _atomic_publish_noreplace(output_path, encoded)
    print(
        json.dumps(
            {
                "schema": WORKER_SCHEMA,
                "status": result["status"],
                "distance": result["fixture"]["distance"],
                "output": str(output_path),
                "output_sha256": output_sha256,
            },
            allow_nan=False,
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
