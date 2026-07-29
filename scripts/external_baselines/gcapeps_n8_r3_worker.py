#!/usr/bin/env python3
"""GCAPEPS/Stim candidate worker for the frozen n=8, rank-three fixture.

Scientific imports are deliberately lazy.  The CLI first authenticates the
neutral fixture, fresh Quimb execution checkout, process envelope, and private
output directory.  It then performs one untruncated state action and writes
three complete complex128 vectors plus one JSON ledger without replacement.

This worker computes no pair verdict and sees no plain-Quimb or NumPy-anchor
output.  Its internal dense checks are same-IR engineering checks and remain
inside the measured carrier-application segment.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, fields, is_dataclass
import hashlib
import importlib.util
from importlib import metadata
import json
import math
import os
from pathlib import Path
import resource
import stat
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence


GCAPEPS_WORKER_SCHEMA = (
    "error_coupling_simulator.external.gcapeps_n8_r3_gcapeps_worker.v1"
)
FIXTURE_SCHEMA = "error_coupling_simulator.external.gcapeps_n8_r3_fixture.v1"
EXPECTED_FIXTURE_SHA256 = (
    "a494512a74ed20b28c067734359e9a09ab3df72ad07467160855c3c475ed0b8d"
)
EXPECTED_FORK_ORIGIN = "https://github.com/cxMoonGlade/quimb.git"
EXPECTED_FORK_COMMIT = "6fbbf74cd36686ed30a4d8865697ce46e47056c1"
EXPECTED_FORK_TREE = "ffdfdf421fbe4d9674c2c88029710042fd18ae14"
EXPECTED_PYPROJECT_SHA256 = (
    "c8b48e06ee8595be41cc5dff6d4f8e768a9064d5a0f84efaec5ff12a7e8aa344"
)
EXPECTED_PIXI_LOCK_SHA256 = (
    "854da99b417c69dbdca4118c2545656470ad4e0f276a606b1b8c3082f795db35"
)
EXPECTED_STIM_VERSION = "1.16.0"
EXPECTED_PREPARATION_STREAM_SHA256 = (
    "e42a195ba2736164700fcf86c1f5949f5a49d39c1932cfd9ee6b8cf6efab3538"
)
EXPECTED_CLIFFORD_STREAM_SHA256 = (
    "aeb75e08b6ac4a592d31199c2eafe9ed0c968465e50d05fa45b7d139a397e50c"
)
EXPECTED_MATRIX_SHA256 = {
    "H": "b8a0541aa80b1a09f1847692e688d8f59e6f7b27904794cb34e3a00547af4cc1",
    "S": "1ea2137ca5d78fbfcef3cfa04052cd34575f5e62ee440b714e6397cc6614322b",
    "S_DAG": (
        "ccdbdd050e820173b78aad0ea053b667a57470bece9c154274926d4192add3a8"
    ),
    "CX": "8147eeddb2b56869f494b2194eb43a7926d1bb5edb4d4f35c6fa9e9633dd4bf8",
    "CZ": "411d2854573bf05718bccb74b2bea00f6180dd0104861c8f112aa0295ea85b45",
    "SWAP": (
        "0fe211d0be6e5908155c70589905d5f91f528440f5a2ddcd39a477b25fd7e70d"
    ),
}
EXPECTED_SITE_ORDER = (
    (0, 0),
    (0, 1),
    (0, 2),
    (0, 3),
    (1, 0),
    (1, 1),
    (1, 2),
    (1, 3),
)
EXPECTED_GRAPH_EDGES = (
    (0, 1),
    (1, 2),
    (2, 3),
    (4, 5),
    (5, 6),
    (6, 7),
    (0, 4),
    (1, 5),
    (2, 6),
    (3, 7),
)
EXPECTED_PREPARATION_BONDS = (2, 2, 2, 2, 2, 2, 1, 2, 1, 1)
EXPECTED_PREPARATION_SITE_ELEMENTS = (4, 16, 8, 4, 4, 16, 8, 4)
PEPS_GATE_SVD_CUTOFF = 1e-12
EXPECTED_ROUTE_ROOT = 0
EXPECTED_ROUTE_VERTICES = (0, 1, 2, 3, 4, 7)
EXPECTED_ROUTE_EDGES = ((0, 1), (0, 4), (1, 2), (2, 3), (3, 7))
EXPECTED_DEPENDENCE_SET = (0, 3, 4, 7)
EXPECTED_RESOURCE_LIMITS = {
    "max_local_operator_elements": 36,
    "max_total_operator_elements": 176,
    "max_local_candidate_tensor_elements": 144,
    "max_total_candidate_tensor_elements": 336,
    "max_predicted_bond_dimension": 6,
    "max_routed_rank_product": 3,
    "max_total_bond_growth_product": 3,
}
EXPECTED_PULLBACKS = (
    "+XXYIZZXZ",
    "+YXYZIZXZ",
    "+ZXYZZZXI",
)
EXPECTED_PHYSICAL_TERMS = (
    (0.0, -0.8, "IXYIZIYZ", -1),
    (0.0, -0.48, "YXYXXIYZ", 1),
    (0.0, -0.36, "YXYXYZYI", 1),
)
THREAD_ENVIRONMENT = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "BLIS_NUM_THREADS",
)
VECTOR_FILENAMES = {
    "residual_preparation": "gcapeps_residual_preparation_vector.npy",
    "after_clifford": "gcapeps_after_clifford_vector.npy",
    "residual_after_update": "gcapeps_residual_after_update_vector.npy",
    "physical_after_update": "gcapeps_physical_after_update_vector.npy",
}
SUMMARY_FILENAME = "gcapeps_worker.json"


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


def _read_strict_json(path: Path) -> tuple[dict[str, Any], str]:
    lexical = path.absolute()
    resolved = lexical.resolve(strict=True)
    if lexical != resolved:
        raise ValueError("fixture path must not traverse a symlink")
    mode = resolved.stat().st_mode
    if not stat.S_ISREG(mode):
        raise ValueError("fixture path must identify a regular file")
    raw = resolved.read_bytes()
    payload = json.loads(
        raw,
        object_pairs_hook=_strict_object,
        parse_constant=_reject_json_constant,
    )
    if not isinstance(payload, dict):
        raise ValueError("fixture must be a JSON object")
    return payload, hashlib.sha256(raw).hexdigest()


def _load_fixture_contract() -> tuple[Any, dict[str, str]]:
    """Load the sibling neutral-fixture contract without relying on sys.path."""

    path = Path(__file__).resolve(strict=True).with_name(
        "emit_gcapeps_n8_r3_fixture.py"
    )
    spec = importlib.util.spec_from_file_location(
        "_gcapeps_n8_r3_fixture_contract",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load the GCAPEPS fixture contract")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, {
        "path": str(path),
        "sha256": _file_sha256(path),
    }


def _run_git(checkout: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(checkout), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def verify_fresh_fork_checkout(checkout: Path) -> dict[str, Any]:
    """Authenticate an ignored-inclusive pristine execution checkout."""

    lexical = checkout.absolute()
    resolved = lexical.resolve(strict=True)
    if lexical != resolved:
        raise RuntimeError("fork checkout path must not traverse a symlink")
    if not resolved.is_dir():
        raise RuntimeError("fork checkout must be a directory")
    head = _run_git(resolved, "rev-parse", "HEAD")
    tree = _run_git(resolved, "rev-parse", "HEAD^{tree}")
    origin = _run_git(resolved, "remote", "get-url", "origin")
    status = _run_git(
        resolved,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--ignored",
    )
    if head != EXPECTED_FORK_COMMIT:
        raise RuntimeError(f"fork commit drifted: {head}")
    if tree != EXPECTED_FORK_TREE:
        raise RuntimeError(f"fork tree drifted: {tree}")
    if origin != EXPECTED_FORK_ORIGIN:
        raise RuntimeError(f"fork origin drifted: {origin!r}")
    if status:
        raise RuntimeError(
            "execution checkout is not ignored-inclusive pristine:\n"
            f"{status}"
        )
    pyproject = resolved / "pyproject.toml"
    pixi_lock = resolved / "pixi.lock"
    if _file_sha256(pyproject) != EXPECTED_PYPROJECT_SHA256:
        raise RuntimeError("fork pyproject.toml hash drifted")
    if _file_sha256(pixi_lock) != EXPECTED_PIXI_LOCK_SHA256:
        raise RuntimeError("fork pixi.lock hash drifted")
    return {
        "path": str(resolved),
        "origin": origin,
        "commit": head,
        "tree": tree,
        "clean_including_ignored": True,
        "pyproject_sha256": EXPECTED_PYPROJECT_SHA256,
        "pixi_lock_sha256": EXPECTED_PIXI_LOCK_SHA256,
    }


def verify_process_envelope() -> dict[str, Any]:
    """Fail before scientific imports if the fresh-worker envelope drifted."""

    if os.environ.get("PYTHONPATH") is not None:
        raise RuntimeError("PYTHONPATH must be absent")
    if sys.platform != "linux":
        raise RuntimeError("GCAPEPS worker requires Linux resource semantics")
    if sys.version_info[:2] != (3, 13):
        raise RuntimeError("GCAPEPS worker requires Python 3.13")
    if not sys.flags.no_user_site:
        raise RuntimeError("user-site imports must be disabled")
    if not sys.dont_write_bytecode:
        raise RuntimeError("bytecode writes must be disabled")
    for name in THREAD_ENVIRONMENT:
        if os.environ.get(name) != "1":
            raise RuntimeError(f"{name} must equal '1'")
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
    numba_cache_raw = os.environ.get("NUMBA_CACHE_DIR")
    if numba_cache_raw is None:
        raise RuntimeError("NUMBA_CACHE_DIR must be set")
    numba_cache_lexical = Path(numba_cache_raw)
    if not numba_cache_lexical.is_absolute():
        raise RuntimeError("NUMBA_CACHE_DIR must be absolute")
    numba_cache = numba_cache_lexical.resolve(strict=True)
    numba_cache_info = numba_cache.stat()
    if not numba_cache.is_dir() or numba_cache_info.st_mode & 0o077:
        raise RuntimeError("NUMBA_CACHE_DIR must be one private directory")
    affinity = sorted(int(cpu) for cpu in os.sched_getaffinity(0))
    if len(affinity) != 1:
        raise RuntimeError("worker must be pinned to exactly one CPU")
    return {
        "python_version": sys.version,
        "python_executable": str(Path(sys.executable).resolve(strict=True)),
        "python_prefix": str(Path(sys.prefix).resolve(strict=True)),
        "cpu_affinity": affinity,
        "thread_environment": {
            name: os.environ[name] for name in THREAD_ENVIRONMENT
        },
        "process_environment": {
            name: os.environ[name] for name in required
        },
        "python_no_user_site": True,
        "python_dont_write_bytecode": True,
        "pythonpath_absent": True,
        "numba_cache_directory": str(numba_cache),
    }


def verify_private_output_directory(path: Path) -> Path:
    """Require a supervisor-owned empty private directory."""

    lexical = path.absolute()
    resolved = lexical.resolve(strict=True)
    if lexical != resolved:
        raise RuntimeError("output directory path must not traverse a symlink")
    info = resolved.stat()
    if not stat.S_ISDIR(info.st_mode):
        raise RuntimeError("output path must be a directory")
    if stat.S_IMODE(info.st_mode) & 0o077:
        raise RuntimeError("output directory must not grant group/other access")
    if any(resolved.iterdir()):
        raise FileExistsError("private output directory must start empty")
    return resolved


def _matrix(token: str):
    """Build a literal C-contiguous little-endian complex128 gate."""

    import numpy as np

    one = np.float64(1.0)
    zero = np.float64(0.0)
    if token == "H":
        scale = one / np.sqrt(np.float64(2.0))
        values = ((scale, scale), (scale, -scale))
    elif token == "S":
        values = ((one, zero), (zero, 1.0j))
    elif token == "S_DAG":
        values = ((one, zero), (zero, -1.0j))
    elif token == "CX":
        values = (
            (one, zero, zero, zero),
            (zero, one, zero, zero),
            (zero, zero, zero, one),
            (zero, zero, one, zero),
        )
    elif token == "CZ":
        values = (
            (one, zero, zero, zero),
            (zero, one, zero, zero),
            (zero, zero, one, zero),
            (zero, zero, zero, -one),
        )
    elif token == "SWAP":
        values = (
            (one, zero, zero, zero),
            (zero, zero, one, zero),
            (zero, one, zero, zero),
            (zero, zero, zero, one),
        )
    else:
        raise ValueError(f"unsupported frozen gate token: {token!r}")
    matrix = np.ascontiguousarray(np.asarray(values, dtype="<c16"))
    digest = hashlib.sha256(matrix.tobytes(order="C")).hexdigest()
    if digest != EXPECTED_MATRIX_SHA256[token]:
        raise RuntimeError(f"{token} matrix hash drifted")
    identity = np.eye(matrix.shape[0], dtype=np.complex128)
    residual = float(np.max(np.abs(matrix.conj().T @ matrix - identity)))
    if (
        not math.isfinite(residual)
        or residual > 8.0 * np.finfo(np.float64).eps
    ):
        raise RuntimeError(f"{token} matrix is not unitary")
    return matrix, digest, residual


def _validated_gate_ledger(
    block: Mapping[str, Any],
    *,
    expected_stream_sha256: str,
) -> tuple[tuple[tuple[str, tuple[int, ...], Any], ...], list[dict[str, Any]]]:
    rows = block.get("gates")
    if not isinstance(rows, list):
        raise ValueError("gate ledger is unavailable")
    parsed = []
    reported = []
    serialized = bytearray()
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping) or row.get("index") != index:
            raise ValueError("gate ledger index drifted")
        token = row.get("token")
        targets = row.get("logical_targets")
        if token not in EXPECTED_MATRIX_SHA256 or not isinstance(targets, list):
            raise ValueError("gate ledger token/targets drifted")
        logical_targets = tuple(targets)
        if (
            any(
                isinstance(target, bool) or not isinstance(target, int)
                for target in logical_targets
            )
            or len(logical_targets) not in (1, 2)
            or len(set(logical_targets)) != len(logical_targets)
            or any(target < 0 or target >= 8 for target in logical_targets)
        ):
            raise ValueError("gate ledger contains invalid targets")
        matrix, digest, residual = _matrix(str(token))
        if row.get("matrix_sha256") != digest:
            raise ValueError("fixture gate matrix binding drifted")
        target_text = ",".join(str(target) for target in logical_targets)
        serialized.extend(
            f"{index:02d}|{token}|{target_text}|{digest}\n".encode("utf-8")
        )
        coordinate_targets = tuple(
            EXPECTED_SITE_ORDER[target] for target in logical_targets
        )
        parsed.append((str(token), logical_targets, matrix))
        reported.append(
            {
                "index": index,
                "token": token,
                "logical_targets": list(logical_targets),
                "coordinate_targets": [list(site) for site in coordinate_targets],
                "matrix_sha256": digest,
                "unitarity_max_abs_residual": residual,
            }
        )
    observed = hashlib.sha256(bytes(serialized)).hexdigest()
    if (
        observed != expected_stream_sha256
        or block.get("gate_stream_sha256") != expected_stream_sha256
    ):
        raise ValueError("gate stream hash drifted")
    return tuple(parsed), reported


def _apply_gate(vector: Any, matrix: Any, targets: Sequence[int]):
    """Apply a literal gate with q0 as the most-significant vector axis."""

    import numpy as np

    state = np.asarray(vector)
    target_tuple = tuple(targets)
    if state.shape != (256,) or state.dtype != np.dtype("complex128"):
        raise ValueError("literal lift input must be length-256 complex128")
    if matrix.shape != (2 ** len(target_tuple),) * 2:
        raise ValueError("literal lift gate shape drifted")
    remaining = tuple(q for q in range(8) if q not in target_tuple)
    permutation = target_tuple + remaining
    permuted = np.transpose(
        state.reshape((2,) * 8),
        permutation,
    ).reshape(2 ** len(target_tuple), -1)
    updated = matrix @ permuted
    inverse = tuple(int(axis) for axis in np.argsort(permutation))
    return np.ascontiguousarray(
        np.transpose(updated.reshape((2,) * 8), inverse).reshape(256),
        dtype=np.complex128,
    )


def _literal_lift(vector: Any, gates: Sequence[tuple[str, tuple[int, ...], Any]]):
    import numpy as np

    state = np.asarray(vector).copy()
    for _token, targets, matrix in gates:
        state = _apply_gate(state, matrix, targets)
    return state


def _vector_sha256(vector: Any) -> str:
    import numpy as np

    array = np.asarray(vector)
    if (
        array.shape != (256,)
        or array.dtype != np.dtype("complex128")
        or not array.flags.c_contiguous
        or not np.all(np.isfinite(array))
    ):
        raise ValueError("complete vector cannot be sealed")
    little = np.ascontiguousarray(array, dtype="<c16")
    return hashlib.sha256(little.tobytes(order="C")).hexdigest()


def _validate_preparation_vector(
    vector: Any,
    fixture: Mapping[str, Any],
) -> None:
    """Enforce the frozen four-amplitude residual preparation invariant."""

    import numpy as np

    state = np.asarray(vector)
    if state.shape != (256,) or state.dtype != np.dtype("complex128"):
        raise ValueError("prepared residual vector contract drifted")
    expected = np.zeros(256, dtype=np.complex128)
    support_rows = fixture["preparation"]["closed_form_support"]
    if not isinstance(support_rows, list) or len(support_rows) != 4:
        raise ValueError("closed-form preparation support drifted")
    for row in support_rows:
        bits = tuple(row["bits"])
        if (
            len(bits) != 8
            or any(bit not in (0, 1) for bit in bits)
            or row["amplitude_real"] != "0.5"
            or row["amplitude_imag"] != "0.0"
        ):
            raise ValueError("closed-form preparation row drifted")
        index = sum(bit << (7 - qubit) for qubit, bit in enumerate(bits))
        if expected[index] != 0.0:
            raise ValueError("closed-form preparation support is duplicated")
        expected[index] = np.complex128(0.5 + 0.0j)
    maximum_error = float(np.max(np.abs(state - expected)))
    if maximum_error > 2.0e-15:
        raise RuntimeError(
            "prepared residual disagrees with four-amplitude invariant: "
            f"{maximum_error}"
        )
    if np.count_nonzero(state) != 4:
        raise RuntimeError("prepared residual must have exactly four nonzeros")
    if abs(float(np.linalg.norm(state)) - 1.0) > 2.0e-15:
        raise RuntimeError("prepared residual norm drifted")
    if abs(float(np.max(np.abs(state))) - 0.5) > 2.0e-15:
        raise RuntimeError("prepared residual infinity norm drifted")


def _positive_elapsed(started: int, *, name: str) -> int:
    elapsed = time.perf_counter_ns() - started
    if elapsed <= 0:
        raise RuntimeError(f"{name} timing must be positive")
    return elapsed


def _coordinate_edges() -> tuple[tuple[tuple[int, int], tuple[int, int]], ...]:
    return tuple(
        (EXPECTED_SITE_ORDER[left], EXPECTED_SITE_ORDER[right])
        for left, right in EXPECTED_GRAPH_EDGES
    )


def _tensor_network_snapshot(circuit: Any) -> dict[str, Any]:
    """Record exact representation sizes without using them as correctness."""

    import numpy as np

    psi, gauges = circuit.get_state(absorb_gauges="return")
    site_rows = []
    for qubit, site in enumerate(EXPECTED_SITE_ORDER):
        tensor = psi[site]
        array = tensor.data
        if not isinstance(array, np.ndarray):
            raise TypeError("GCAPEPS state tensor backend must be NumPy")
        if array.dtype != np.dtype("complex128"):
            raise TypeError("GCAPEPS state tensor dtype must be complex128")
        if not np.all(np.isfinite(array)):
            raise ValueError("GCAPEPS state tensor contains non-finite values")
        site_rows.append(
            {
                "qubit": qubit,
                "site": list(site),
                "shape": list(array.shape),
                "elements": int(array.size),
                "payload_bytes": int(array.nbytes),
                "dtype": str(array.dtype),
                "backend": "numpy",
                "data_sha256": hashlib.sha256(
                    np.ascontiguousarray(array).tobytes(order="C")
                ).hexdigest(),
            }
        )
    edge_rows = []
    for logical_edge, site_edge in zip(
        EXPECTED_GRAPH_EDGES,
        _coordinate_edges(),
        strict=True,
    ):
        bond_index = psi.bond(*site_edge)
        edge_rows.append(
            {
                "logical_edge": list(logical_edge),
                "site_edge": [list(site) for site in site_edge],
                "bond_index": str(bond_index),
                "bond_dimension": int(psi.ind_size(bond_index)),
            }
        )
    gauge_rows = []
    for index, gauge in sorted(gauges.items()):
        array = np.asarray(gauge)
        if array.dtype not in (np.dtype("float64"), np.dtype("complex128")):
            raise TypeError("GCAPEPS gauge dtype must be float64 or complex128")
        if not np.all(np.isfinite(array)):
            raise ValueError("GCAPEPS gauge contains non-finite values")
        gauge_rows.append(
            {
                "bond_index": str(index),
                "shape": list(array.shape),
                "elements": int(array.size),
                "payload_bytes": int(array.nbytes),
                "dtype": str(array.dtype),
                "data_sha256": hashlib.sha256(
                    np.ascontiguousarray(array).tobytes(order="C")
                ).hexdigest(),
            }
        )
    state_elements = sum(row["elements"] for row in site_rows)
    state_bytes = sum(row["payload_bytes"] for row in site_rows)
    gauge_elements = sum(row["elements"] for row in gauge_rows)
    gauge_bytes = sum(row["payload_bytes"] for row in gauge_rows)
    return {
        "tensor_count": len(site_rows),
        "sites": site_rows,
        "edges": edge_rows,
        "state_elements_total": state_elements,
        "state_elements_largest_site": max(row["elements"] for row in site_rows),
        "state_tensor_payload_bytes": state_bytes,
        "gauge_count": len(gauge_rows),
        "gauges": gauge_rows,
        "gauge_elements": gauge_elements,
        "gauge_payload_bytes": gauge_bytes,
        "logical_representation_payload_bytes": state_bytes + gauge_bytes,
        "maximum_bond_dimension": max(
            row["bond_dimension"] for row in edge_rows
        ),
    }


def _phase_fields(phase: complex) -> dict[str, int]:
    if phase == 1.0 + 0.0j:
        return {"real": 1, "imag": 0}
    if phase == -1.0 + 0.0j:
        return {"real": -1, "imag": 0}
    if phase == 0.0 + 1.0j:
        return {"real": 0, "imag": 1}
    if phase == 0.0 - 1.0j:
        return {"real": 0, "imag": -1}
    raise ValueError("Pauli word phase is not exact")


def _dataclass_json(value: Any) -> Any:
    """Convert frozen fork evidence records without hiding field additions."""

    if is_dataclass(value):
        return {
            field.name: _dataclass_json(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_dataclass_json(item) for item in value]
    if isinstance(value, list):
        return [_dataclass_json(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _dataclass_json(item) for key, item in value.items()}
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def _normalize_site(site: Any, inverse_site_map: Mapping[Any, int]) -> int:
    try:
        return inverse_site_map[site]
    except (KeyError, TypeError) as exc:
        raise RuntimeError(f"unknown routed site {site!r}") from exc


def _edge_ledger(update: Any) -> list[dict[str, Any]]:
    inverse = {site: qubit for qubit, site in enumerate(EXPECTED_SITE_ORDER)}
    expected_route_keys = {
        frozenset(edge) for edge in EXPECTED_ROUTE_EDGES
    }
    expected_bonds_before = dict(
        zip(EXPECTED_GRAPH_EDGES, EXPECTED_PREPARATION_BONDS, strict=True)
    )
    rows = []
    seen = set()
    for edge in update.edge_bonds:
        logical_edge = tuple(
            _normalize_site(site, inverse) for site in edge.site_edge
        )
        key = frozenset(logical_edge)
        if key in seen:
            raise RuntimeError("duplicate GCAPEPS edge ledger row")
        seen.add(key)
        matching = next(
            candidate
            for candidate in EXPECTED_GRAPH_EDGES
            if frozenset(candidate) == key
        )
        routed = key in expected_route_keys
        before = expected_bonds_before[matching]
        after = before * (3 if routed else 1)
        expected_values = {
            "routed": routed,
            "state_bond_before": before,
            "operator_bond": 3 if routed else 1,
            "construction_bound": after,
            "predicted_state_bond_after": after,
            "state_bond_after": after,
            "routed_rank_product_before": 1,
            "routed_rank_product_after": 3 if routed else 1,
            "compressed": False,
            "pepo_rank_factor": 3 if routed else 1,
            "refactor_operator_schmidt_factor": 1,
            "refactor_operator_schmidt_product_before": 1,
            "refactor_operator_schmidt_product_after": 1,
            "total_bond_growth_product_before": 1,
            "total_bond_growth_product_after": 3 if routed else 1,
        }
        for name, expected in expected_values.items():
            if getattr(edge, name) != expected:
                raise RuntimeError(
                    f"GCAPEPS edge {matching} field {name} drifted: "
                    f"{getattr(edge, name)!r} != {expected!r}"
                )
        if edge.qubit_edge != matching:
            raise RuntimeError("GCAPEPS qubit-edge order drifted")
        if not edge.gauge_present_before:
            raise RuntimeError("prepared PEPS route lost a Vidal gauge")
        if edge.gauge_size_before != before or edge.gauge_size_after != after:
            raise RuntimeError("GCAPEPS gauge-size edge ledger drifted")
        row = _dataclass_json(edge)
        row["logical_edge_normalized"] = list(matching)
        row["site_edge"] = [list(site) for site in edge.site_edge]
        rows.append(row)
    if seen != {frozenset(edge) for edge in EXPECTED_GRAPH_EDGES}:
        raise RuntimeError("GCAPEPS edge ledger does not cover the graph")
    return rows


def _product_ledger(
    values: Sequence[tuple[tuple[Any, Any], int]],
) -> list[dict[str, Any]]:
    inverse = {site: qubit for qubit, site in enumerate(EXPECTED_SITE_ORDER)}
    rows = []
    for site_edge, value in values:
        logical = tuple(_normalize_site(site, inverse) for site in site_edge)
        rows.append(
            {
                "site_edge": [list(site) for site in site_edge],
                "logical_edge_normalized": list(logical),
                "product": int(value),
            }
        )
    return rows


def _validate_resource_ledger(update: Any) -> dict[str, Any]:
    ledger = update.resource_ledger
    if ledger is None:
        raise RuntimeError("GCAPEPS resource ledger is missing")
    limit_values = asdict(ledger.limits)
    if limit_values != EXPECTED_RESOURCE_LIMITS:
        raise RuntimeError("GCAPEPS resource limits drifted")
    required = {
        "complex128_bytes_per_element": 16,
        "operator_elements_total": 176,
        "operator_elements_largest_site": 36,
        "operator_payload_bytes_total": 2816,
        "operator_payload_bytes_largest_site": 576,
        "state_elements_before_total": 64,
        "state_elements_before_largest_site": 16,
        "state_payload_bytes_before_total": 1024,
        "predicted_state_elements_after_total": 336,
        "predicted_state_elements_after_largest_site": 144,
        "predicted_state_payload_bytes_after_total": 5376,
        "state_elements_after_total": 336,
        "state_elements_after_largest_site": 144,
        "state_payload_bytes_after_total": 5376,
        "epistemic_class": "numerical_only_resource_diagnostic",
    }
    for name, expected in required.items():
        if getattr(ledger, name) != expected:
            raise RuntimeError(
                f"GCAPEPS resource ledger {name} drifted: "
                f"{getattr(ledger, name)!r} != {expected!r}"
            )
    if len(ledger.site_tensors) != 8:
        raise RuntimeError("GCAPEPS resource ledger must cover eight sites")
    for qubit, row in enumerate(ledger.site_tensors):
        if row.qubit != qubit or row.site != EXPECTED_SITE_ORDER[qubit]:
            raise RuntimeError("GCAPEPS site resource order drifted")
        if row.state_elements_before != EXPECTED_PREPARATION_SITE_ELEMENTS[qubit]:
            raise RuntimeError("GCAPEPS site pre-update elements drifted")
        if (
            row.operator_payload_bytes != row.operator_elements * 16
            or row.state_payload_bytes_before
            != row.state_elements_before * 16
            or row.predicted_state_payload_bytes_after
            != row.predicted_state_elements_after * 16
            or row.state_payload_bytes_after != row.state_elements_after * 16
        ):
            raise RuntimeError("GCAPEPS site byte ledger drifted")
        if row.state_elements_after != row.predicted_state_elements_after:
            raise RuntimeError("GCAPEPS realized site size missed prediction")
        if (
            row.state_backend_before != "numpy"
            or row.state_backend_after != "numpy"
            or row.state_dtype_before != "complex128"
            or row.state_dtype_after != "complex128"
        ):
            raise RuntimeError("GCAPEPS site precision/backend drifted")
    return _dataclass_json(ledger)


def _validate_dense_action(update: Any) -> dict[str, Any]:
    evidence = update.dense_operator_action
    if evidence is None:
        raise RuntimeError("GCAPEPS exact-small dense action evidence missing")
    if (
        evidence.max_qubits != 10
        or evidence.qubit_count != 8
        or evidence.checked is not True
        or evidence.status != "passed_exact_small_dense_operator_action"
        or evidence.precision_dtype != "complex128"
        or evidence.independence_class
        != "same_ir_not_an_independent_oracle"
    ):
        raise RuntimeError("GCAPEPS exact-small dense action evidence drifted")
    numeric = (
        evidence.maximum_amplitude_error,
        evidence.state_vector_l2_error,
        evidence.coefficient_l1_norm,
        evidence.maximum_amplitude_backward_scale,
        evidence.state_vector_l2_backward_scale,
        evidence.allowed_maximum_amplitude_error,
        evidence.allowed_state_vector_l2_error,
    )
    if any(value is None or not math.isfinite(float(value)) for value in numeric):
        raise RuntimeError("GCAPEPS dense action evidence is non-finite")
    if (
        evidence.maximum_amplitude_error
        > evidence.allowed_maximum_amplitude_error
        or evidence.state_vector_l2_error
        > evidence.allowed_state_vector_l2_error
    ):
        raise RuntimeError("GCAPEPS dense action evidence exceeds its limits")
    return _dataclass_json(evidence)


def _validate_frame_event(
    event: Any,
    *,
    index: int,
    residual_gate_count: int,
    residual_bond: int,
) -> dict[str, Any]:
    expected = {
        "column": index,
        "round_index": 0,
        "operation": "clifford_frame_update",
        "frame_revision_before": index,
        "frame_revision_after": index + 1,
        "physical_pauli": None,
        "pulled_back_pauli": None,
        "peps_gate_count_before": residual_gate_count,
        "peps_gate_count_after": residual_gate_count,
        "max_bond_before": residual_bond,
        "max_bond_after": residual_bond,
        "residual_update": None,
        "residual_revision_before": 0,
        "residual_revision_after": 0,
        "physical_terms": (),
        "pulled_back_terms": (),
    }
    for name, value in expected.items():
        if getattr(event, name) != value:
            raise RuntimeError(
                f"Clifford frame event {index} field {name} drifted"
            )
    if event.frame_backend != f"stim-{EXPECTED_STIM_VERSION}":
        raise RuntimeError("Clifford frame backend identity drifted")
    if event.residual_backend != "quimb-circuit-peps-simple-update":
        raise RuntimeError("residual backend identity drifted")
    return _dataclass_json(event)


def validate_coherent_event_term_binding(
    physical_terms: Sequence[str],
    pulled_back_terms: Sequence[str],
) -> dict[str, Any]:
    """Bind every coherent-event coefficient and signed word exactly."""

    expected_physical = (
        "-0.8j*-IXYIZIYZ",
        "-0.48j*+YXYXXIYZ",
        "-0.36j*+YXYXYZYI",
    )
    expected_pulled = (
        "-0.8j*+XXYIZZXZ",
        "-0.48j*+YXYZIZXZ",
        "-0.36j*+ZXYZZZXI",
    )
    observed_physical = tuple(physical_terms)
    observed_pulled = tuple(pulled_back_terms)
    if observed_physical != expected_physical:
        raise RuntimeError("GCAPEPS coherent event physical terms drifted")
    if observed_pulled != expected_pulled:
        raise RuntimeError("GCAPEPS coherent event pulled terms drifted")
    return {
        "physical_terms": list(observed_physical),
        "pulled_back_terms": list(observed_pulled),
        "coefficients_and_signed_words_exactly_bound": True,
    }


def _validate_coherent_event(event: Any) -> tuple[dict[str, Any], Any]:
    update = event.residual_update
    if update is None:
        raise RuntimeError("GCAPEPS coherent event has no residual update")
    if (
        event.frame_backend != f"stim-{EXPECTED_STIM_VERSION}"
        or event.residual_backend != "quimb-circuit-peps-simple-update"
        or event.physical_pauli is not None
        or event.pulled_back_pauli is not None
    ):
        raise RuntimeError("GCAPEPS coherent event backend/Pauli fields drifted")
    term_binding = validate_coherent_event_term_binding(
        event.physical_terms,
        event.pulled_back_terms,
    )
    expected_event = {
        "column": 10,
        "round_index": 0,
        "operation": "pulled_coherent_pauli_sum",
        "frame_revision_before": 10,
        "frame_revision_after": 10,
        "peps_gate_count_before": 9,
        "peps_gate_count_after": 9,
        "max_bond_before": 2,
        "max_bond_after": 6,
        "residual_revision_before": 0,
        "residual_revision_after": 1,
    }
    for name, expected in expected_event.items():
        if getattr(event, name) != expected:
            raise RuntimeError(f"coherent event field {name} drifted")
    expected_update = {
        "operation": "coherent_pauli_sum",
        "strategy": "exact_tree_routed_coherent_pepo",
        "support": tuple(range(8)),
        "sites": EXPECTED_SITE_ORDER,
        "max_bond_before": 2,
        "max_bond_after": 6,
        "max_bond_limit": None,
        "cutoff": PEPS_GATE_SVD_CUTOFF,
        "residual_revision_before": 0,
        "residual_revision_after": 1,
        "declared_term_count": 3,
        "active_term_count": 3,
        "dependence_set": EXPECTED_DEPENDENCE_SET,
        "gauge_strategy": "extend_raw_vidal_gauge_over_term_label",
        "truncation_applied": False,
        "nonzero_validation": "full_overlap_exact",
        "contraction_optimize": "greedy",
        "precision_dtype": "complex128",
        "array_backend": "numpy",
        "gauge_certification": "representation_only",
        "gauge_reconditioned": False,
        "gauge_finite": True,
        "gauge_conditioning_status": "not_evaluated_representation_only",
        "compression_applied": False,
        "smudging_applied": False,
        "approximate_contraction_applied": False,
    }
    for name, expected in expected_update.items():
        if getattr(update, name) != expected:
            raise RuntimeError(f"residual update field {name} drifted")
    if (
        update.candidate_norm_squared is None
        or not math.isfinite(update.candidate_norm_squared)
        or update.candidate_norm_squared <= 0.0
    ):
        raise RuntimeError("GCAPEPS candidate norm evidence is invalid")
    inverse = {site: q for q, site in enumerate(EXPECTED_SITE_ORDER)}
    route_root = _normalize_site(update.routing_root, inverse)
    route_vertices = tuple(
        _normalize_site(site, inverse) for site in update.routing_vertices
    )
    route_edges = tuple(
        tuple(_normalize_site(site, inverse) for site in edge)
        for edge in update.routing_tree_edges
    )
    if route_root != EXPECTED_ROUTE_ROOT:
        raise RuntimeError("GCAPEPS route root drifted")
    if route_vertices != EXPECTED_ROUTE_VERTICES:
        raise RuntimeError("GCAPEPS route vertices drifted")
    if route_edges != EXPECTED_ROUTE_EDGES:
        raise RuntimeError("GCAPEPS route edges drifted")
    result = _dataclass_json(event)
    result["coherent_term_binding"] = term_binding
    result["normalized_route"] = {
        "root": route_root,
        "vertices": list(route_vertices),
        "edges": [list(edge) for edge in route_edges],
    }
    return result, update


def _validate_import_origin(path: Path, checkout: Path, *, label: str) -> str:
    lexical = path.absolute()
    resolved = lexical.resolve(strict=True)
    if lexical != resolved:
        raise RuntimeError(f"{label} import origin traverses a symlink")
    if not resolved.is_relative_to(checkout):
        raise RuntimeError(f"{label} import origin escapes frozen fork checkout")
    return str(resolved)


def _runtime_import_identity(checkout: Path) -> tuple[dict[str, Any], Any, Any, Any]:
    """Import scientific dependencies only after preconditions have passed."""

    import numpy as np
    import quimb
    import quimb.tensor as qtn
    import stim
    import quimb.experimental.gcapeps as gcapeps

    if stim.__version__ != EXPECTED_STIM_VERSION:
        raise RuntimeError(f"Stim version drifted: {stim.__version__}")
    quimb_origin = _validate_import_origin(
        Path(quimb.__file__),
        checkout,
        label="Quimb",
    )
    gcapeps_origin = _validate_import_origin(
        Path(gcapeps.__file__),
        checkout,
        label="GCAPEPS",
    )
    return (
        {
            "numpy_version": np.__version__,
            "numpy_import_origin": str(Path(np.__file__).resolve(strict=True)),
            "quimb_version": metadata.version("quimb"),
            "quimb_import_origin": quimb_origin,
            "gcapeps_import_origin": gcapeps_origin,
            "stim_version": stim.__version__,
            "stim_import_origin": str(Path(stim.__file__).resolve(strict=True)),
        },
        np,
        qtn,
        stim,
    )


def _read_cgroup_memory_peak() -> dict[str, Any]:
    try:
        membership = Path("/proc/self/cgroup").read_text(
            encoding="utf-8"
        ).splitlines()
        unified = next(line for line in membership if line.startswith("0::"))
        relative = unified.split("::", 1)[1].lstrip("/")
        path = Path("/sys/fs/cgroup") / relative / "memory.peak"
        raw = path.read_text(encoding="ascii").strip()
        value = int(raw)
        if value < 0:
            raise ValueError("negative memory.peak")
        return {
            "status": "available",
            "bytes": value,
            "source": str(path),
        }
    except (OSError, StopIteration, ValueError) as exc:
        return {
            "status": "unavailable",
            "bytes": None,
            "source": None,
            "reason": f"{type(exc).__name__}: {exc}",
        }


def _resource_usage(started: resource.struct_rusage) -> dict[str, Any]:
    ended = resource.getrusage(resource.RUSAGE_SELF)
    peak_rss_kib = int(ended.ru_maxrss)
    return {
        "ru_maxrss": peak_rss_kib,
        "ru_maxrss_units": "KiB_on_linux",
        "peak_rss_bytes": peak_rss_kib * 1024,
        "platform": sys.platform,
        "process_user_time_ns": int(
            max(0.0, ended.ru_utime - started.ru_utime) * 1_000_000_000
        ),
        "process_system_time_ns": int(
            max(0.0, ended.ru_stime - started.ru_stime) * 1_000_000_000
        ),
        "cgroup_memory_peak": _read_cgroup_memory_peak(),
    }


def compute_gcapeps_candidate(
    fixture: Mapping[str, Any],
    *,
    fixture_sha256: str,
    fork_checkout: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Compute the candidate and return JSON metadata plus four vectors."""

    fixture_contract, fixture_contract_source = _load_fixture_contract()

    if (
        fixture_contract.validate_fixture(fixture)
        != EXPECTED_FIXTURE_SHA256
    ):
        raise ValueError("fixture canonical identity drifted")
    if fixture_sha256 != EXPECTED_FIXTURE_SHA256:
        raise ValueError("worker fixture SHA does not match frozen identity")
    import_identity, np, qtn, stim = _runtime_import_identity(fork_checkout)
    from quimb.experimental.gcapeps import (
        CoherentPauliSum,
        CoherentPauliTerm,
        GCAPEPSResourceLimits,
        GCAPEPSState,
        QubitPauliWord,
        QuimbPEPSCarrier,
        StimCliffordFrame,
    )
    Gate = qtn.Gate

    site_order = tuple(tuple(site) for site in fixture["site_order"])
    graph_edges = tuple(tuple(edge) for edge in fixture["graph_edges"])
    if site_order != EXPECTED_SITE_ORDER or graph_edges != EXPECTED_GRAPH_EDGES:
        raise RuntimeError("fixture geometry drifted")
    coordinate_edges = _coordinate_edges()
    preparation_gates, preparation_ledger = _validated_gate_ledger(
        fixture["preparation"],
        expected_stream_sha256=EXPECTED_PREPARATION_STREAM_SHA256,
    )
    clifford_gates, clifford_ledger = _validated_gate_ledger(
        fixture["clifford"],
        expected_stream_sha256=EXPECTED_CLIFFORD_STREAM_SHA256,
    )
    if len(preparation_gates) != 9 or len(clifford_gates) != 10:
        raise RuntimeError("frozen gate-stream length drifted")

    timings: dict[str, int] = {}
    computation_started = time.perf_counter_ns()
    zero = np.asarray([1.0, 0.0], dtype=np.complex128)
    preparation_started = time.perf_counter_ns()
    psi0 = qtn.PEPS.product_state(
        {site: zero.copy() for site in site_order},
        cyclic=False,
    )
    circuit = qtn.CircuitPEPSSimpleUpdate(
        psi0=psi0,
        edges=coordinate_edges,
        max_bond=None,
        cutoff=PEPS_GATE_SVD_CUTOFF,
        renorm=False,
        gauge_smudge=0.0,
        equilibrate_every=None,
        dtype="complex128",
        to_backend=None,
        convert_eager=True,
    )
    for _token, logical_targets, matrix in preparation_gates:
        coordinate_targets = tuple(
            site_order[target] for target in logical_targets
        )
        circuit.apply_gates(
            (Gate.from_raw(matrix, qubits=coordinate_targets),)
        )
    timings["preparation_ns"] = _positive_elapsed(
        preparation_started,
        name="preparation",
    )
    if circuit.num_gates != 9:
        raise RuntimeError("prepared residual gate count drifted")
    preparation_snapshot = _tensor_network_snapshot(circuit)
    if tuple(
        row["bond_dimension"] for row in preparation_snapshot["edges"]
    ) != EXPECTED_PREPARATION_BONDS:
        raise RuntimeError("prepared PEPS bonds drifted")
    if tuple(
        row["elements"] for row in preparation_snapshot["sites"]
    ) != EXPECTED_PREPARATION_SITE_ELEMENTS:
        raise RuntimeError("prepared PEPS site elements drifted")

    limits = GCAPEPSResourceLimits(**EXPECTED_RESOURCE_LIMITS)
    hybrid_started = time.perf_counter_ns()
    carrier = QuimbPEPSCarrier(
        circuit,
        site_order=site_order,
        contraction_optimize="greedy",
        resource_limits=limits,
    )
    state = GCAPEPSState(StimCliffordFrame(8), carrier)
    timings["hybrid_state_construction_ns"] = _positive_elapsed(
        hybrid_started,
        name="hybrid state construction",
    )
    if state.events or state.frame.revision != 0:
        raise RuntimeError("GCAPEPS state did not begin at revision zero")
    if (
        carrier.residual_revision != 0
        or carrier.num_gates != 9
        or carrier.max_bond_dimension != 2
    ):
        raise RuntimeError("GCAPEPS residual initialization drifted")
    del carrier, circuit, psi0

    frame_events = []
    tableau_started = time.perf_counter_ns()
    for index, (token, targets, _matrix_value) in enumerate(clifford_gates):
        if token == "S_DAG" and index != 5:
            raise RuntimeError("S_DAG row drifted")
        instruction = f"{token} {' '.join(str(q) for q in targets)}"
        one_gate = stim.Circuit(instruction)
        flattened = tuple(one_gate.flattened())
        if len(flattened) != 1 or flattened[0].name != token:
            raise RuntimeError("Stim one-gate instruction drifted")
        event = state.apply_clifford(one_gate)
        frame_events.append(
            _validate_frame_event(
                event,
                index=index,
                residual_gate_count=9,
                residual_bond=2,
            )
        )
    timings["tableau_prefix_ns"] = _positive_elapsed(
        tableau_started,
        name="tableau prefix",
    )
    if len(state.events) != 10:
        raise RuntimeError("Clifford frame event count drifted")
    frame_snapshot = state.frame
    if (
        frame_snapshot.revision != 10
        or frame_snapshot.num_qubits != 8
        or len(frame_snapshot.as_stim_tableau()) != 8
    ):
        raise RuntimeError("final Stim frame dimensions/revision drifted")
    after_frame_carrier = state.carrier
    if (
        after_frame_carrier.residual_revision != 0
        or after_frame_carrier.num_gates != 9
        or after_frame_carrier.max_bond_dimension != 2
    ):
        raise RuntimeError("Clifford routing mutated the residual carrier")
    after_frame_snapshot = _tensor_network_snapshot(
        after_frame_carrier.circuit
    )
    if after_frame_snapshot != preparation_snapshot:
        raise RuntimeError("Clifford routing changed residual representation")

    materialize_before_started = time.perf_counter_ns()
    residual_before = after_frame_carrier.state_vector(max_qubits=8)
    timings["residual_before_state_vector_ns"] = _positive_elapsed(
        materialize_before_started,
        name="residual-before state vector",
    )
    residual_before = np.ascontiguousarray(residual_before)
    if residual_before.dtype != np.dtype("complex128"):
        raise TypeError("residual-before vector dtype drifted")
    _validate_preparation_vector(residual_before, fixture)
    del after_frame_carrier
    lift_before_started = time.perf_counter_ns()
    after_clifford_vector = _literal_lift(residual_before, clifford_gates)
    timings["literal_after_clifford_lift_ns"] = _positive_elapsed(
        lift_before_started,
        name="literal after-Clifford lift",
    )

    ir_started = time.perf_counter_ns()
    physical_terms = []
    physical_term_rows = []
    for index, (term, frozen) in enumerate(
        zip(
            fixture["physical_terms"],
            EXPECTED_PHYSICAL_TERMS,
            strict=True,
        )
    ):
        real = float(term["coefficient_real"])
        imag = float(term["coefficient_imag"])
        body = term["pauli_body"]
        phase = term["word_phase"]
        if (
            term["term_index"] != index
            or (real, imag, body, phase) != frozen
            or term["expected_signed_pullback"] != EXPECTED_PULLBACKS[index]
        ):
            raise RuntimeError("physical signed term drifted")
        coefficient = np.complex128(complex(real, imag))
        word = QubitPauliWord.from_labels(body, phase=complex(phase))
        physical_terms.append(CoherentPauliTerm(coefficient, word))
        physical_term_rows.append(
            {
                "term_index": index,
                "coefficient": {
                    "real": float(coefficient.real),
                    "imag": float(coefficient.imag),
                },
                "physical_body": body,
                "physical_word_phase": _phase_fields(word.phase),
                "physical_signed_word": str(word),
            }
        )
    operator = CoherentPauliSum(tuple(physical_terms))
    timings["coherent_ir_build_ns"] = _positive_elapsed(
        ir_started,
        name="coherent IR build",
    )
    if operator.declared_term_count != 3 or operator.active_term_count != 3:
        raise RuntimeError("physical coherent IR rank drifted")

    carrier_apply_started = time.perf_counter_ns()
    coherent_event = state.apply_coherent_pauli_sum(operator)
    timings["carrier_apply_ns"] = _positive_elapsed(
        carrier_apply_started,
        name="carrier apply",
    )
    if len(state.events) != 11 or state.events[-1] != coherent_event:
        raise RuntimeError("coherent event ledger drifted")
    coherent_event_ledger, update = _validate_coherent_event(coherent_event)
    signed_pullback_audit_started = time.perf_counter_ns()
    structured_pulled_words = tuple(
        frame_snapshot.pullback_pauli(term.word) for term in operator.terms
    )
    timings["structured_signed_pullback_audit_ns"] = _positive_elapsed(
        signed_pullback_audit_started,
        name="structured signed-pullback audit",
    )
    signed_pullback = []
    for row, actual_word, expected in zip(
        physical_term_rows,
        structured_pulled_words,
        EXPECTED_PULLBACKS,
        strict=True,
    ):
        expected_word = QubitPauliWord.from_labels(
            expected[1:],
            phase=1.0 if expected[0] == "+" else -1.0,
        )
        if actual_word != expected_word:
            raise RuntimeError("structured signed pullback drifted")
        signed_pullback.append(
            {
                **row,
                "pulled_back_body": expected[1:],
                "pulled_back_codes": list(actual_word.codes),
                "pulled_back_word_phase": _phase_fields(actual_word.phase),
                "pulled_back_signed_word": str(actual_word),
                "expected_signed_pullback": expected,
            }
        )
    edge_ledger = _edge_ledger(update)
    resource_ledger = _validate_resource_ledger(update)
    dense_action = _validate_dense_action(update)

    final_carrier = state.carrier
    if (
        final_carrier.residual_revision != 1
        or final_carrier.num_gates != 9
        or final_carrier.max_bond_dimension != 6
    ):
        raise RuntimeError("final GCAPEPS residual state drifted")
    final_snapshot = _tensor_network_snapshot(final_carrier.circuit)
    if (
        final_snapshot["state_elements_total"] != 336
        or final_snapshot["state_elements_largest_site"] != 144
        or final_snapshot["maximum_bond_dimension"] != 6
    ):
        raise RuntimeError("final GCAPEPS representation ledger drifted")
    routed_products = _product_ledger(final_carrier.routed_rank_products)
    refactor_products = _product_ledger(
        final_carrier.refactor_operator_schmidt_products
    )
    total_products = _product_ledger(
        final_carrier.total_bond_growth_products
    )
    expected_route_keys = {frozenset(edge) for edge in EXPECTED_ROUTE_EDGES}
    for collection, kind in (
        (routed_products, "routed"),
        (refactor_products, "refactor"),
        (total_products, "total"),
    ):
        if len(collection) != len(EXPECTED_GRAPH_EDGES):
            raise RuntimeError(f"{kind} product ledger width drifted")
        for row in collection:
            key = frozenset(row["logical_edge_normalized"])
            expected = (
                1
                if kind == "refactor"
                else (3 if key in expected_route_keys else 1)
            )
            if row["product"] != expected:
                raise RuntimeError(f"{kind} product ledger value drifted")

    materialize_after_started = time.perf_counter_ns()
    residual_after = final_carrier.state_vector(max_qubits=8)
    timings["residual_after_state_vector_ns"] = _positive_elapsed(
        materialize_after_started,
        name="residual-after state vector",
    )
    residual_after = np.ascontiguousarray(residual_after)
    if residual_after.dtype != np.dtype("complex128"):
        raise TypeError("residual-after vector dtype drifted")
    lift_after_started = time.perf_counter_ns()
    physical_after = _literal_lift(residual_after, clifford_gates)
    timings["literal_physical_after_update_lift_ns"] = _positive_elapsed(
        lift_after_started,
        name="literal physical-after-update lift",
    )
    vectors = {
        "residual_preparation": residual_before,
        "after_clifford": after_clifford_vector,
        "residual_after_update": residual_after,
        "physical_after_update": physical_after,
    }
    vector_hashes = {
        name: _vector_sha256(vector) for name, vector in vectors.items()
    }
    timings["gcapeps_update_ns"] = (
        timings["tableau_prefix_ns"]
        + timings["coherent_ir_build_ns"]
        + timings["carrier_apply_ns"]
    )
    timings["residual_complete_vector_materialization_ns"] = (
        timings["residual_before_state_vector_ns"]
        + timings["residual_after_state_vector_ns"]
    )
    timings["literal_c128_gate_list_lift_ns"] = (
        timings["literal_after_clifford_lift_ns"]
        + timings["literal_physical_after_update_lift_ns"]
    )
    timings["worker_computation_total_ns"] = _positive_elapsed(
        computation_started,
        name="worker computation total",
    )

    payload = {
        "schema": GCAPEPS_WORKER_SCHEMA,
        "status": "completed",
        "lane": "gcapeps_stim_tree_routed_residual_at_frozen_fork_commit",
        "claim_boundary": fixture["claim_boundary"],
        "fixture": {
            "schema": fixture["schema"],
            "canonical_sha256": fixture_sha256,
            "n_qubits": fixture["n_qubits"],
            "active_rank": fixture["active_rank"],
            "dtype": fixture["dtype"],
            "amplitude_convention": fixture["amplitude_convention"],
        },
        "gate_ledgers": {
            "preparation": preparation_ledger,
            "preparation_gate_stream_sha256": (
                EXPECTED_PREPARATION_STREAM_SHA256
            ),
            "clifford": clifford_ledger,
            "clifford_gate_stream_sha256": (
                EXPECTED_CLIFFORD_STREAM_SHA256
            ),
            "literal_c128_lift_used": True,
            "stim_tableau_unitary_matrix_used": False,
        },
        "frame": {
            "backend": frame_snapshot.backend_name,
            "num_qubits": frame_snapshot.num_qubits,
            "revision_before": 0,
            "revision_after": frame_snapshot.revision,
            "one_instruction_apply_calls": 10,
            "clifford_events": frame_events,
        },
        "signed_pullback": signed_pullback,
        "coherent_event": coherent_event_ledger,
        "route": coherent_event_ledger["normalized_route"],
        "edge_ledger": edge_ledger,
        "resource_limits": dict(EXPECTED_RESOURCE_LIMITS),
        "resource_ledger": resource_ledger,
        "dense_operator_action": dense_action,
        "refactor_implemented": False,
        "refactor_bookkeeping": {
            "routed_rank_products": routed_products,
            "refactor_operator_schmidt_products": refactor_products,
            "total_bond_growth_products": total_products,
        },
        "representation": {
            "preparation": preparation_snapshot,
            "after_clifford_frame": after_frame_snapshot,
            "after_rank_three_update": final_snapshot,
            "operator_logical_payload_bytes": 2816,
            "residual_only_bytes_never_labelled_total_gcapeps_memory": True,
            "tableau_memory_not_in_logical_tensor_payload": True,
        },
        "vectors": {
            name: {
                "shape": [256],
                "dtype": "complex128",
                "sha256_c_order_little_endian_c16": vector_hashes[name],
                "l2_norm": float(np.linalg.norm(vectors[name])),
                "maximum_absolute_amplitude": float(
                    np.max(np.abs(vectors[name]))
                ),
                "amplitude_order": "q0_most_significant",
            }
            for name in vectors
        },
        "timing_ns": timings,
        "timing_policy": {
            "gcapeps_update_formula": (
                "tableau_prefix_ns+coherent_ir_build_ns+carrier_apply_ns"
            ),
            "includes_exact_small_internal_dense_and_norm_checks": True,
            "internal_checks_in_segment": "carrier_apply_ns",
            "materialization_excluded_from_update": True,
            "process_launch_and_import_excluded": True,
        },
        "imports": import_identity,
        "fixture_contract_source": fixture_contract_source,
        "no_candidate_or_anchor_output_consumed": True,
        "phase_fit_performed": False,
        "normalization_performed": False,
        "coordinate_permutation_performed": False,
        "compression_applied": False,
        "peps_gate_svd_cutoff": PEPS_GATE_SVD_CUTOFF,
        "peps_gate_svd_cutoff_role": "floating_svd_null_direction_pruning_only",
        "physical_probability_floor_applied": False,
        "truncation_applied": False,
        "approximate_contraction_applied": False,
        "correspondence_status": (
            "SCOPED_ENGINEERING_GREEN__GENERIC_EQUIVALENCE_OPEN"
        ),
    }
    return payload, vectors


def _open_private_dir(path: Path) -> int:
    return os.open(
        path,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | os.O_CLOEXEC,
    )


def _write_bytes_noreplace(
    directory_fd: int,
    filename: str,
    payload: bytes,
) -> None:
    if Path(filename).name != filename:
        raise ValueError("artifact filename must be a basename")
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | os.O_CLOEXEC
        | getattr(os, "O_NOFOLLOW", 0)
    )
    descriptor = os.open(
        filename,
        flags,
        0o600,
        dir_fd=directory_fd,
    )
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _npy_bytes(array: Any) -> bytes:
    import io
    import numpy as np

    stream = io.BytesIO()
    np.save(stream, array, allow_pickle=False)
    return stream.getvalue()


def publish_private_worker_artifacts(
    output_directory: Path,
    payload: dict[str, Any],
    vectors: Mapping[str, Any],
) -> dict[str, Any]:
    """Write fixed artifacts with O_EXCL, fsync, and exact-set verification."""

    directory_fd = _open_private_dir(output_directory)
    try:
        artifacts: dict[str, Any] = {}
        for name, filename in VECTOR_FILENAMES.items():
            encoded = _npy_bytes(vectors[name])
            _write_bytes_noreplace(directory_fd, filename, encoded)
            artifacts[name] = {
                "filename": filename,
                "file_sha256": hashlib.sha256(encoded).hexdigest(),
                "content_sha256_c_order_little_endian_c16": (
                    payload["vectors"][name][
                        "sha256_c_order_little_endian_c16"
                    ]
                ),
            }
        payload["artifacts"] = artifacts
        summary = (
            json.dumps(
                payload,
                allow_nan=False,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
        _write_bytes_noreplace(directory_fd, SUMMARY_FILENAME, summary)
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    expected = set(VECTOR_FILENAMES.values()) | {SUMMARY_FILENAME}
    actual = {entry.name for entry in output_directory.iterdir()}
    if actual != expected:
        raise RuntimeError(
            f"private worker artifact set drifted: {actual!r} != {expected!r}"
        )
    for entry in output_directory.iterdir():
        info = entry.lstat()
        if not stat.S_ISREG(info.st_mode) or entry.is_symlink():
            raise RuntimeError("private worker artifact is not a regular file")
    return payload


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--fork-checkout", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument(
        "--sample-kind",
        choices=("warmup", "measured", "control"),
        required=True,
    )
    parser.add_argument("--sample-index", type=int, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.sample_index < 0:
        raise ValueError("sample-index must be nonnegative")
    process_usage_started = resource.getrusage(resource.RUSAGE_SELF)
    worker_path = Path(__file__).resolve(strict=True)
    worker_sha256_before = _file_sha256(worker_path)
    process_envelope = verify_process_envelope()
    fork_identity = verify_fresh_fork_checkout(args.fork_checkout)
    output_directory = verify_private_output_directory(args.output_directory)
    fixture, fixture_file_sha256 = _read_strict_json(args.fixture)
    if fixture.get("schema") != FIXTURE_SCHEMA:
        raise ValueError("fixture schema drifted")
    if fixture_file_sha256 != EXPECTED_FIXTURE_SHA256:
        raise ValueError("fixture file bytes are not the frozen canonical bytes")
    fixture_contract, _fixture_contract_source = _load_fixture_contract()

    fixture_canonical_sha256 = fixture_contract.validate_fixture(fixture)
    if (
        fixture_canonical_sha256 != EXPECTED_FIXTURE_SHA256
        or fixture_contract.canonical_sha256(fixture)
        != EXPECTED_FIXTURE_SHA256
    ):
        raise ValueError("fixture canonical hash drifted")
    payload, vectors = compute_gcapeps_candidate(
        fixture,
        fixture_sha256=fixture_canonical_sha256,
        fork_checkout=Path(fork_identity["path"]),
    )
    if _file_sha256(worker_path) != worker_sha256_before:
        raise RuntimeError("worker source changed during execution")
    fork_after = verify_fresh_fork_checkout(args.fork_checkout)
    if fork_after != fork_identity:
        raise RuntimeError("fork identity changed during worker execution")
    payload["sample"] = {
        "kind": args.sample_kind,
        "index": args.sample_index,
    }
    payload["fixture"].update(
        {
            "path": str(args.fixture.resolve(strict=True)),
            "file_sha256": fixture_file_sha256,
        }
    )
    payload["fork"] = fork_identity
    payload["process_envelope"] = process_envelope
    payload["resource_usage"] = _resource_usage(process_usage_started)
    payload["provenance"] = {
        "worker_path": str(worker_path),
        "worker_sha256": worker_sha256_before,
        "fork_pristine_before_and_after": True,
        "private_output_directory": str(output_directory),
        "worker_artifacts_written_without_replacement": True,
        "candidate_output_input_paths_accepted": [],
        "anchor_output_input_paths_accepted": [],
    }
    published = publish_private_worker_artifacts(
        output_directory,
        payload,
        vectors,
    )
    print(
        json.dumps(
            {
                "schema": GCAPEPS_WORKER_SCHEMA,
                "status": published["status"],
                "sample": published["sample"],
                "fixture_sha256": fixture_canonical_sha256,
                "summary": str(output_directory / SUMMARY_FILENAME),
            },
            allow_nan=False,
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
