#!/usr/bin/env python3
"""Ordinary Quimb PEPO-on-PEPS candidate for the frozen n=8 fixture.

The module deliberately imports Quimb only inside :func:`compute_plain`, so
contract and helper tests can import it from the normal ECS environment. It
does not import the experimental hybrid carrier, Stim, SDIM, or an anchor.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
from importlib import metadata
import json
import math
import os
from pathlib import Path
import platform
import resource
import stat
import subprocess
import sys
import time
from typing import Any, Mapping

import numpy as np


PLAIN_WORKER_SCHEMA = (
    "error_coupling_simulator.external.gcapeps_n8_r3_plain_quimb_worker.v1"
)
FIXTURE_SCHEMA = "error_coupling_simulator.external.gcapeps_n8_r3_fixture.v1"
EXPECTED_FIXTURE_SHA256 = (
    "a494512a74ed20b28c067734359e9a09ab3df72ad07467160855c3c475ed0b8d"
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
EXPECTED_PREPARATION_STREAM_SHA256 = (
    "e42a195ba2736164700fcf86c1f5949f5a49d39c1932cfd9ee6b8cf6efab3538"
)
EXPECTED_CLIFFORD_STREAM_SHA256 = (
    "aeb75e08b6ac4a592d31199c2eafe9ed0c968465e50d05fa45b7d139a397e50c"
)
EXPECTED_GATE_MATRIX_SHA256 = {
    "H": "b8a0541aa80b1a09f1847692e688d8f59e6f7b27904794cb34e3a00547af4cc1",
    "S": "1ea2137ca5d78fbfcef3cfa04052cd34575f5e62ee440b714e6397cc6614322b",
    "S_DAG": ("ccdbdd050e820173b78aad0ea053b667a57470bece9c154274926d4192add3a8"),
    "CX": "8147eeddb2b56869f494b2194eb43a7926d1bb5edb4d4f35c6fa9e9633dd4bf8",
    "CZ": "411d2854573bf05718bccb74b2bea00f6180dd0104861c8f112aa0295ea85b45",
    "SWAP": ("0fe211d0be6e5908155c70589905d5f91f528440f5a2ddcd39a477b25fd7e70d"),
}
EXPECTED_PAULI_DESIRED_SHA256 = {
    "I": "fbfcd8f81e798f2e4e04256375c0766e6166910440ffd3de2b9b37a88ab5aac7",
    "X": "33c11b461fe67e717e37ac34a568cd1c27a89013703bf5b84194f0732a33a26d",
    "Y": "dd9ec1e25765af2c4c067c9cb272c3e394d0044e941c70a6f2c078830a77c373",
    "Z": "c8f478783d65670e5d4823a34aa1be2ec54809ad61ca0d10e4da56195c4778fc",
}
EXPECTED_PAULI_RAW_BRA_KET_SHA256 = {
    "I": "fbfcd8f81e798f2e4e04256375c0766e6166910440ffd3de2b9b37a88ab5aac7",
    "X": "33c11b461fe67e717e37ac34a568cd1c27a89013703bf5b84194f0732a33a26d",
    "Y": "84f1031f8456b7da8f6096a18778bb8974665c5bcbda2270e004f833162deaf6",
    "Z": "c8f478783d65670e5d4823a34aa1be2ec54809ad61ca0d10e4da56195c4778fc",
}
EXPECTED_SITE_ORDER = tuple((q // 4, q % 4) for q in range(8))
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
PLAIN_LANE_NAME = "plain_quimb_direct_sum_pepo_on_peps_at_frozen_fork_commit"
CONTRACTION_OPTIMIZE = "greedy"
THREAD_ENVIRONMENT = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "BLIS_NUM_THREADS",
)
_PROHIBITED_PLAIN_MODULE = ".".join(("quimb", "experimental", "gcapeps"))
_PROHIBITED_REFERENCE_HELPER = "build_" + "global_direct_sum_reference"


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
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _matrix_sha256(matrix: np.ndarray) -> str:
    array = np.asarray(matrix)
    if array.shape not in ((2, 2), (4, 4)):
        raise ValueError("matrix hash input must be 2x2 or 4x4")
    if array.dtype.str != "<c16" or not array.flags.c_contiguous:
        raise ValueError("matrix hash input must be C-contiguous little-endian c128")
    if not np.all(np.isfinite(array)):
        raise ValueError("matrix hash input contains a nonfinite value")
    return _sha256_bytes(array.tobytes(order="C"))


def _vector_sha256(vector: np.ndarray) -> str:
    array = np.asarray(vector)
    if (
        array.shape != (256,)
        or array.dtype.str != "<c16"
        or not array.flags.c_contiguous
        or not np.all(np.isfinite(array))
    ):
        raise ValueError("vector cannot be sealed as little-endian complex128")
    return _sha256_bytes(array.tobytes(order="C"))


def quimb_product_operator_raw_bra_ket(
    desired_output_input: Any,
) -> np.ndarray:
    """Lower semantic ``(output,input)`` axes to Quimb raw ``(bra,ket)``.

    ``PEPO_product_operator`` places the supplied physical axes on
    ``(lower=bra/input, upper=ket/output)``. The explicit transpose is an axis
    adapter. It does not transpose the desired physical operator.
    """

    matrix = np.asarray(desired_output_input)
    if matrix.shape != (2, 2):
        raise ValueError("desired local operator must have shape (2, 2)")
    if matrix.dtype != np.dtype("complex128"):
        raise ValueError("desired local operator must already be complex128")
    if matrix.dtype.str != "<c16":
        raise ValueError("desired local operator must be little-endian complex128")
    if not matrix.flags.c_contiguous:
        raise ValueError("desired local operator must be C-contiguous")
    if not np.all(np.isfinite(matrix)):
        raise ValueError("desired local operator contains a nonfinite value")
    return np.ascontiguousarray(matrix.T)


def scan_plain_worker_source(source: str) -> dict[str, Any]:
    """Statically reject imports/calls that collapse lane independence."""

    if not isinstance(source, str):
        raise TypeError("worker source must be text")
    tree = ast.parse(source)
    prohibited_imports: list[str] = []
    prohibited_calls: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == _PROHIBITED_PLAIN_MODULE or alias.name.startswith(
                    _PROHIBITED_PLAIN_MODULE + "."
                ):
                    prohibited_imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == _PROHIBITED_PLAIN_MODULE or module.startswith(
                _PROHIBITED_PLAIN_MODULE + "."
            ):
                prohibited_imports.append(module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                call_name = node.func.attr
            else:
                call_name = ""
            if call_name == _PROHIBITED_REFERENCE_HELPER:
                prohibited_calls.append(call_name)
    passed = not prohibited_imports and not prohibited_calls
    return {
        "passed": passed,
        "prohibited_imports": sorted(set(prohibited_imports)),
        "prohibited_calls": sorted(set(prohibited_calls)),
    }


def _require_no_runtime_prohibited_imports() -> None:
    loaded = sorted(
        name
        for name in sys.modules
        if (
            name == _PROHIBITED_PLAIN_MODULE
            or name.startswith(_PROHIBITED_PLAIN_MODULE + ".")
        )
    )
    if loaded:
        raise RuntimeError(
            "plain worker process contains prohibited hybrid modules: "
            + ", ".join(loaded)
        )


def _validate_local_axis_contract(value: Any) -> None:
    expected = {
        "semantic_matrix_axes": ["output_ket", "input_bra"],
        "quimb_product_operator_raw_axes": ["bra_input", "ket_output"],
        "lowering": "raw_bra_ket=desired_output_input.T",
        "runtime_control": "one_site_nonsymmetric_dense_equals_raw_transpose",
        "pauli_desired_sha256": EXPECTED_PAULI_DESIRED_SHA256,
        "pauli_raw_bra_ket_sha256": EXPECTED_PAULI_RAW_BRA_KET_SHA256,
    }
    if value != expected:
        raise ValueError("plain PEPO local-axis contract drifted")


def _validated_fixture(
    fixture: Mapping[str, Any],
) -> tuple[dict[str, Any], str]:
    if not isinstance(fixture, Mapping):
        raise TypeError("fixture must be a mapping")
    canonical = _canonical_json_bytes(fixture)
    digest = _sha256_bytes(canonical)
    if digest != EXPECTED_FIXTURE_SHA256:
        raise ValueError(
            "plain worker fixture canonical hash mismatch: "
            f"{digest} != {EXPECTED_FIXTURE_SHA256}"
        )
    frozen = json.loads(canonical)
    if (
        frozen.get("schema") != FIXTURE_SCHEMA
        or frozen.get("n_qubits") != 8
        or frozen.get("active_rank") != 3
        or frozen.get("dtype") != "complex128"
    ):
        raise ValueError("plain worker fixture headline contract drifted")
    if tuple(map(tuple, frozen.get("site_order", ()))) != EXPECTED_SITE_ORDER:
        raise ValueError("plain worker site order drifted")
    if tuple(map(tuple, frozen.get("graph_edges", ()))) != EXPECTED_GRAPH_EDGES:
        raise ValueError("plain worker graph edge order drifted")
    expected_site_map = [
        {"logical_qubit": q, "coordinate": list(EXPECTED_SITE_ORDER[q])}
        for q in range(8)
    ]
    if frozen.get("site_map") != expected_site_map:
        raise ValueError("plain worker logical-to-coordinate site map drifted")
    amplitude = frozen.get("amplitude_convention")
    if amplitude != {
        "local_basis": ["|0>", "|1>"],
        "axes": list(range(8)),
        "q0_axis": 0,
        "q0_bit_significance": "most_significant",
        "flat_index": "sum_q bit(q)*2**(7-q)",
        "matrix_indices": "row_is_output_column_is_input",
        "two_qubit_basis": ["|00>", "|01>", "|10>", "|11>"],
    }:
        raise ValueError("plain worker amplitude convention drifted")
    _validate_local_axis_contract(frozen.get("plain_pepo_local_axis_contract"))
    return frozen, digest


def _git(root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _verify_checkout_identity(root: Path) -> dict[str, Any]:
    if not root.is_absolute():
        raise ValueError("expected Quimb checkout root must be absolute")
    lexical = root.absolute()
    resolved = root.resolve(strict=True)
    if lexical != resolved:
        raise RuntimeError("Quimb checkout root traverses a symlink")
    if not resolved.is_dir():
        raise RuntimeError("Quimb checkout root is not a directory")
    top = Path(_git(resolved, "rev-parse", "--show-toplevel")).resolve(strict=True)
    if top != resolved:
        raise RuntimeError("Quimb checkout root is not the Git top level")
    head = _git(resolved, "rev-parse", "HEAD")
    tree = _git(resolved, "rev-parse", "HEAD^{tree}")
    if head != EXPECTED_FORK_COMMIT or tree != EXPECTED_FORK_TREE:
        raise RuntimeError(
            f"Quimb checkout identity drifted: commit={head}, tree={tree}"
        )
    status = _git(
        resolved,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--ignored",
    )
    if status:
        raise RuntimeError(
            "Quimb execution checkout is not ignored-inclusive pristine:\n" + status
        )
    remotes: dict[str, str] = {}
    for name in _git(resolved, "remote").splitlines():
        if name:
            remotes[name] = _git(resolved, "remote", "get-url", name)
    if remotes.get("origin") != EXPECTED_FORK_ORIGIN:
        raise RuntimeError("Quimb execution checkout origin drifted")
    pyproject = resolved / "pyproject.toml"
    pixi_lock = resolved / "pixi.lock"
    if _file_sha256(pyproject) != EXPECTED_PYPROJECT_SHA256:
        raise RuntimeError("Quimb execution pyproject.toml hash drifted")
    if _file_sha256(pixi_lock) != EXPECTED_PIXI_LOCK_SHA256:
        raise RuntimeError("Quimb execution pixi.lock hash drifted")
    return {
        "root": str(resolved),
        "commit": head,
        "tree": tree,
        "clean_including_ignored": True,
        "remotes": remotes,
        "pyproject_sha256": EXPECTED_PYPROJECT_SHA256,
        "pixi_lock_sha256": EXPECTED_PIXI_LOCK_SHA256,
    }


def verify_process_envelope() -> dict[str, Any]:
    """Fail before Quimb import if the fresh-worker envelope drifted."""

    if os.environ.get("PYTHONPATH") is not None:
        raise RuntimeError("PYTHONPATH must be absent")
    if sys.platform != "linux":
        raise RuntimeError("plain Quimb worker requires Linux resource semantics")
    if sys.version_info[:2] != (3, 13):
        raise RuntimeError("plain Quimb worker requires Python 3.13")
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


def _load_and_verify_quimb(
    expected_quimb_root: Path,
) -> tuple[Any, dict[str, Any]]:
    if os.environ.get("PYTHONPATH") not in (None, ""):
        raise RuntimeError("PYTHONPATH is forbidden for the plain Quimb worker")
    _require_no_runtime_prohibited_imports()
    checkout = _verify_checkout_identity(expected_quimb_root)

    import quimb
    import quimb.tensor as qtn

    _require_no_runtime_prohibited_imports()
    root = Path(checkout["root"])
    quimb_origin_lexical = Path(quimb.__file__).absolute()
    qtn_origin_lexical = Path(qtn.__file__).absolute()
    quimb_origin = quimb_origin_lexical.resolve(strict=True)
    qtn_origin = qtn_origin_lexical.resolve(strict=True)
    expected_quimb_origin = (root / "quimb" / "__init__.py").resolve(strict=True)
    expected_qtn_origin = (root / "quimb" / "tensor" / "__init__.py").resolve(
        strict=True
    )
    if (
        quimb_origin_lexical != quimb_origin
        or qtn_origin_lexical != qtn_origin
        or quimb_origin != expected_quimb_origin
        or qtn_origin != expected_qtn_origin
    ):
        raise RuntimeError(
            "public Quimb imports do not originate at the frozen checkout"
        )
    required_public_api = (
        "PEPS",
        "CircuitPEPSSimpleUpdate",
        "Gate",
        "PEPO_product_operator",
    )
    missing = [name for name in required_public_api if not hasattr(qtn, name)]
    if missing:
        raise RuntimeError(f"frozen public Quimb API is incomplete: {missing}")
    identity = {
        **checkout,
        "quimb_import_origin": str(quimb_origin),
        "quimb_tensor_import_origin": str(qtn_origin),
        "quimb_distribution_version": metadata.version("quimb"),
        "numpy_version": np.__version__,
        "public_api": list(required_public_api),
        "hybrid_imported": False,
    }
    return qtn, identity


def _gate_matrix(token: str) -> np.ndarray:
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
    digest = _matrix_sha256(matrix)
    if digest != EXPECTED_GATE_MATRIX_SHA256[token]:
        raise RuntimeError(f"plain {token} gate matrix hash drifted")
    identity = np.eye(matrix.shape[0], dtype=np.complex128)
    residual = float(np.max(np.abs(matrix.conj().T @ matrix - identity)))
    if not math.isfinite(residual) or residual > 8.0 * np.finfo(np.float64).eps:
        raise RuntimeError(f"plain {token} gate is outside the unitarity band")
    return matrix


def _pauli_matrices(
    axis_contract: Mapping[str, Any],
) -> dict[str, np.ndarray]:
    values = {
        "I": ((1.0, 0.0), (0.0, 1.0)),
        "X": ((0.0, 1.0), (1.0, 0.0)),
        "Y": ((0.0, -1.0j), (1.0j, 0.0)),
        "Z": ((1.0, 0.0), (0.0, -1.0)),
    }
    matrices: dict[str, np.ndarray] = {}
    for symbol, entries in values.items():
        desired = np.ascontiguousarray(np.asarray(entries, dtype="<c16"))
        raw = quimb_product_operator_raw_bra_ket(desired)
        desired_digest = _matrix_sha256(desired)
        raw_digest = _matrix_sha256(raw)
        if (
            desired_digest != EXPECTED_PAULI_DESIRED_SHA256[symbol]
            or raw_digest != EXPECTED_PAULI_RAW_BRA_KET_SHA256[symbol]
            or axis_contract["pauli_desired_sha256"][symbol] != desired_digest
            or axis_contract["pauli_raw_bra_ket_sha256"][symbol] != raw_digest
        ):
            raise RuntimeError(f"plain {symbol} local-axis hash drifted")
        matrices[symbol] = desired
    return matrices


def _apply_gate_block(
    *,
    qtn: Any,
    circuit: Any,
    block: Mapping[str, Any],
    expected_stream_sha256: str,
    site_map: tuple[tuple[int, int], ...],
    graph_edges: tuple[tuple[int, int], ...],
) -> tuple[list[dict[str, Any]], str]:
    rows = block.get("gates")
    if not isinstance(rows, list):
        raise ValueError("plain gate block is unavailable")
    graph_edge_sets = {frozenset(edge) for edge in graph_edges}
    stream = bytearray()
    ledger: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping) or row.get("index") != index:
            raise ValueError("plain gate ledger index drifted")
        token = row.get("token")
        logical_raw = row.get("logical_targets")
        if token not in EXPECTED_GATE_MATRIX_SHA256 or not isinstance(
            logical_raw, list
        ):
            raise ValueError("plain gate ledger token/targets drifted")
        logical_targets = tuple(logical_raw)
        expected_arity = 1 if token in ("H", "S", "S_DAG") else 2
        if (
            len(logical_targets) != expected_arity
            or len(set(logical_targets)) != expected_arity
            or any(
                isinstance(target, bool)
                or not isinstance(target, int)
                or target < 0
                or target >= 8
                for target in logical_targets
            )
        ):
            raise ValueError("plain gate targets are invalid")
        if expected_arity == 2 and frozenset(logical_targets) not in graph_edge_sets:
            raise ValueError("plain two-site gate is not graph-local")
        coordinate_targets = tuple(site_map[q] for q in logical_targets)
        matrix = _gate_matrix(str(token))
        digest = _matrix_sha256(matrix)
        if row.get("matrix_sha256") != digest:
            raise ValueError("plain gate occurrence matrix binding drifted")
        residual = float(
            np.max(
                np.abs(
                    matrix.conj().T @ matrix
                    - np.eye(matrix.shape[0], dtype=np.complex128)
                )
            )
        )
        target_text = ",".join(str(target) for target in logical_targets)
        stream.extend(f"{index:02d}|{token}|{target_text}|{digest}\n".encode("utf-8"))
        raw_gate = qtn.Gate.from_raw(matrix, qubits=coordinate_targets)
        if raw_gate.special or raw_gate.controls:
            raise RuntimeError("plain gate did not remain an uncontrolled raw gate")
        circuit.apply_gates((raw_gate,))
        ledger.append(
            {
                "index": index,
                "canonical_token": token,
                "logical_targets": list(logical_targets),
                "coordinate_targets": [
                    list(coordinate) for coordinate in coordinate_targets
                ],
                "matrix_sha256": digest,
                "unitarity_max_abs_residual": residual,
                "lowering": "Gate.from_raw",
                "named_or_special_gate_used": False,
            }
        )
    observed_stream = _sha256_bytes(bytes(stream))
    if (
        observed_stream != expected_stream_sha256
        or block.get("gate_stream_sha256") != expected_stream_sha256
    ):
        raise ValueError("plain gate stream hash drifted")
    return ledger, observed_stream


def _validate_c128_tensor(array: Any, *, label: str) -> np.ndarray:
    value = np.asarray(array)
    if value.dtype != np.dtype("complex128") or value.dtype.str != "<c16":
        raise RuntimeError(f"{label} is not little-endian complex128")
    if not np.all(np.isfinite(value)):
        raise RuntimeError(f"{label} contains a nonfinite value")
    return value


def _tensor_network_resource_ledger(
    network: Any,
    *,
    site_order: tuple[tuple[int, int], ...],
    graph_edges: tuple[tuple[int, int], ...],
) -> dict[str, Any]:
    if tuple(network.gen_sites_present()) != site_order:
        raise RuntimeError("tensor-network site order drifted")
    if int(network.num_tensors) != len(site_order):
        raise RuntimeError("tensor-network does not have one tensor per site")
    site_rows: list[dict[str, Any]] = []
    total_elements = 0
    total_bytes = 0
    for logical_qubit, coordinate in enumerate(site_order):
        array = _validate_c128_tensor(
            network[coordinate].data,
            label=f"site {coordinate} tensor",
        )
        elements = int(array.size)
        nbytes = int(array.nbytes)
        total_elements += elements
        total_bytes += nbytes
        site_rows.append(
            {
                "logical_qubit": logical_qubit,
                "coordinate": list(coordinate),
                "shape": list(array.shape),
                "elements": elements,
                "logical_bytes": nbytes,
                "dtype": str(array.dtype),
            }
        )
    edge_rows: list[dict[str, Any]] = []
    for logical_a, logical_b in graph_edges:
        coordinate_a = site_order[logical_a]
        coordinate_b = site_order[logical_b]
        bond = int(network.bond_size(coordinate_a, coordinate_b))
        if bond <= 0:
            raise RuntimeError("tensor-network bond dimension is not positive")
        edge_rows.append(
            {
                "logical_edge": [logical_a, logical_b],
                "coordinate_edge": [list(coordinate_a), list(coordinate_b)],
                "bond_dimension": bond,
            }
        )
    if total_bytes != total_elements * np.dtype("complex128").itemsize:
        raise RuntimeError("tensor-network logical byte ledger is inconsistent")
    return {
        "tensor_count": int(network.num_tensors),
        "sites": site_rows,
        "edges": edge_rows,
        "bond_dimensions": [int(row["bond_dimension"]) for row in edge_rows],
        "maximum_bond_dimension": max(int(row["bond_dimension"]) for row in edge_rows),
        "total_tensor_elements": total_elements,
        "maximum_site_tensor_elements": max(int(row["elements"]) for row in site_rows),
        "logical_tensor_bytes": total_bytes,
        "dtype": "complex128",
    }


def _gauge_resource_ledger(
    *,
    gauges: Mapping[str, Any],
    state_snapshot: Any,
    site_order: tuple[tuple[int, int], ...],
    graph_edges: tuple[tuple[int, int], ...],
) -> dict[str, Any]:
    edge_rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    total_elements = 0
    total_bytes = 0
    for logical_a, logical_b in graph_edges:
        coordinate_a = site_order[logical_a]
        coordinate_b = site_order[logical_b]
        bond_index = state_snapshot.bond(coordinate_a, coordinate_b)
        if bond_index not in gauges:
            raise RuntimeError("circuit gauge is missing a graph bond")
        gauge = np.asarray(gauges[bond_index])
        if gauge.dtype not in (np.dtype("float64"), np.dtype("complex128")):
            raise RuntimeError("circuit gauge dtype is outside the frozen lane")
        if gauge.ndim != 1 or not np.all(np.isfinite(gauge)):
            raise RuntimeError("circuit gauge is invalid")
        seen.add(bond_index)
        total_elements += int(gauge.size)
        total_bytes += int(gauge.nbytes)
        edge_rows.append(
            {
                "logical_edge": [logical_a, logical_b],
                "coordinate_edge": [list(coordinate_a), list(coordinate_b)],
                "gauge_elements": int(gauge.size),
                "logical_bytes": int(gauge.nbytes),
                "dtype": str(gauge.dtype),
            }
        )
    if set(gauges) != seen:
        raise RuntimeError("circuit gauge ledger contains non-graph entries")
    return {
        "status": "AVAILABLE_VIDAL_GAUGES",
        "edges": edge_rows,
        "gauge_elements": total_elements,
        "logical_gauge_bytes": total_bytes,
    }


def _materialize_vector(
    state: Any,
    *,
    site_order: tuple[tuple[int, int], ...],
) -> np.ndarray:
    physical_inds = tuple(state.site_ind(site) for site in site_order)
    if len(physical_inds) != 8 or len(set(physical_inds)) != 8:
        raise RuntimeError("plain PEPS physical-index order is invalid")
    dense = state.to_dense(
        physical_inds,
        to_qarray=False,
        to_ket=False,
        optimize=CONTRACTION_OPTIMIZE,
    )
    if not isinstance(dense, np.ndarray):
        raise RuntimeError("plain complete contraction did not return NumPy")
    if dense.dtype != np.dtype("complex128") or dense.dtype.str != "<c16":
        raise RuntimeError(
            "plain complete vector was not already little-endian complex128"
        )
    if dense.size != 256:
        raise RuntimeError("plain complete vector does not have 256 amplitudes")
    vector = dense.reshape((256,))
    if not np.all(np.isfinite(vector)):
        raise RuntimeError("plain complete vector contains a nonfinite value")
    return np.ascontiguousarray(vector)


def _one_site_orientation_control(qtn: Any) -> dict[str, Any]:
    desired = np.ascontiguousarray(
        np.asarray(
            (
                (1.0 + 0.25j, 2.0 - 0.5j),
                (-3.0 + 0.75j, 0.5 - 1.25j),
            ),
            dtype="<c16",
        )
    )
    raw = quimb_product_operator_raw_bra_ket(desired)
    if np.array_equal(desired, raw):
        raise RuntimeError("orientation control matrix is accidentally symmetric")
    operator = qtn.PEPO_product_operator([[raw]], cyclic=False)
    dense = operator.to_dense(
        (operator.upper_ind(0, 0),),
        (operator.lower_ind(0, 0),),
        to_qarray=False,
        optimize=CONTRACTION_OPTIMIZE,
    )
    if (
        not isinstance(dense, np.ndarray)
        or dense.shape != (2, 2)
        or dense.dtype != np.dtype("complex128")
        or not np.all(np.isfinite(dense))
    ):
        raise RuntimeError("orientation control dense operator is invalid")
    if not np.array_equal(dense, desired):
        raise RuntimeError(
            "Quimb one-site dense operator does not equal raw-axis transpose"
        )
    if np.array_equal(dense, raw):
        raise RuntimeError("orientation control cannot distinguish the raw axes")

    input_vector = np.ascontiguousarray(
        np.asarray((0.5 + 0.125j, -0.25 + 0.75j), dtype="<c16")
    )
    state = qtn.PEPS.product_state({(0, 0): input_vector}, cyclic=False)
    output_state = operator.apply(state, contract=True, compress=False)
    output = output_state.to_dense(
        (output_state.site_ind((0, 0)),),
        to_qarray=False,
        to_ket=False,
        optimize=CONTRACTION_OPTIMIZE,
    )
    if (
        not isinstance(output, np.ndarray)
        or output.shape != (2,)
        or output.dtype != np.dtype("complex128")
        or not np.all(np.isfinite(output))
    ):
        raise RuntimeError("orientation control action output is invalid")
    expected = desired @ input_vector
    wrong = raw @ input_vector
    action_error = float(np.max(np.abs(output - expected)))
    wrong_orientation_movement = float(np.max(np.abs(output - wrong)))
    scale = max(1.0, float(np.max(np.abs(expected))))
    bound = float(64.0 * np.finfo(np.float64).eps * scale)
    if action_error > bound or wrong_orientation_movement <= 1.0e-6:
        raise RuntimeError("one-site PEPO action orientation control failed")
    return {
        "status": "PASS",
        "contract": "one_site_nonsymmetric_dense_equals_raw_transpose",
        "semantic_matrix_axes": ["output_ket", "input_bra"],
        "quimb_product_operator_raw_axes": ["bra_input", "ket_output"],
        "lowering": "raw_bra_ket=desired_output_input.T",
        "desired_output_input_sha256": _matrix_sha256(desired),
        "raw_bra_ket_sha256": _matrix_sha256(raw),
        "dense_output_input_sha256": _matrix_sha256(np.ascontiguousarray(dense)),
        "dense_exactly_equals_desired": True,
        "dense_differs_from_raw": True,
        "action_max_abs_error": action_error,
        "action_max_abs_error_bound": bound,
        "wrong_orientation_movement": wrong_orientation_movement,
        "target_fixture_apply_count": 0,
        "control_apply_count": 1,
    }


def _coefficient(term: Mapping[str, Any]) -> np.complex128:
    real_raw = term.get("coefficient_real")
    imag_raw = term.get("coefficient_imag")
    if not isinstance(real_raw, str) or not isinstance(imag_raw, str):
        raise ValueError("plain Pauli coefficient must remain decimal text")
    real = np.float64(real_raw)
    imag = np.float64(imag_raw)
    phase = term.get("word_phase")
    if phase not in (-1, 1) or isinstance(phase, bool):
        raise ValueError("plain Pauli word phase drifted")
    value = np.complex128(complex(real, imag) * int(phase))
    if not np.isfinite(value):
        raise ValueError("plain Pauli coefficient is nonfinite")
    return value


def _build_direct_sum_pepo(
    *,
    qtn: Any,
    terms: Any,
    axis_contract: Mapping[str, Any],
) -> tuple[Any, list[dict[str, Any]]]:
    if not isinstance(terms, list) or len(terms) != 3:
        raise ValueError("plain lane requires exactly three physical terms")
    paulis = _pauli_matrices(axis_contract)
    term_pepos: list[Any] = []
    term_ledger: list[dict[str, Any]] = []
    for index, term in enumerate(terms):
        if not isinstance(term, Mapping) or term.get("term_index") != index:
            raise ValueError("plain physical term order drifted")
        body = term.get("pauli_body")
        if (
            not isinstance(body, str)
            or len(body) != 8
            or any(symbol not in paulis for symbol in body)
        ):
            raise ValueError("plain physical Pauli body drifted")
        scalar = _coefficient(term)
        raw_rows: list[list[np.ndarray]] = [[], []]
        local_rows: list[dict[str, Any]] = []
        for logical_qubit, symbol in enumerate(body):
            desired = paulis[symbol]
            coefficient_applied = logical_qubit == 0
            if coefficient_applied:
                desired = np.ascontiguousarray(scalar * desired)
            raw = quimb_product_operator_raw_bra_ket(desired)
            coordinate = EXPECTED_SITE_ORDER[logical_qubit]
            raw_rows[coordinate[0]].append(raw)
            local_rows.append(
                {
                    "logical_qubit": logical_qubit,
                    "coordinate": list(coordinate),
                    "pauli": symbol,
                    "coefficient_applied_here": coefficient_applied,
                    "desired_output_input_sha256": _matrix_sha256(desired),
                    "raw_bra_ket_sha256": _matrix_sha256(raw),
                }
            )
        if sum(int(row["coefficient_applied_here"]) for row in local_rows) != 1:
            raise RuntimeError("plain term coefficient application count drifted")
        term_pepos.append(qtn.PEPO_product_operator(raw_rows, cyclic=False))
        term_ledger.append(
            {
                "term_index": index,
                "coefficient_real": term["coefficient_real"],
                "coefficient_imag": term["coefficient_imag"],
                "word_phase": term["word_phase"],
                "effective_coefficient_real": float(np.real(scalar)),
                "effective_coefficient_imag": float(np.imag(scalar)),
                "pauli_body": body,
                "coefficient_application_count": 1,
                "coefficient_application_logical_qubit": 0,
                "locals": local_rows,
            }
        )
    pepo01 = term_pepos[0].add_PEPO(term_pepos[1])
    pepo = pepo01.add_PEPO(term_pepos[2])
    return pepo, term_ledger


def _process_environment() -> dict[str, Any]:
    names = (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "BLIS_NUM_THREADS",
        "PYTHONNOUSERSITE",
        "PYTHONDONTWRITEBYTECODE",
        "PYTHONHASHSEED",
        "TZ",
        "CUDA_VISIBLE_DEVICES",
    )
    return {name: os.environ.get(name) for name in names}


def _read_cgroup_memory_peak() -> dict[str, Any]:
    try:
        membership = Path("/proc/self/cgroup").read_text(
            encoding="utf-8"
        ).splitlines()
        unified = next(line for line in membership if line.startswith("0::"))
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


def _resource_usage(start: resource.struct_rusage) -> dict[str, Any]:
    end = resource.getrusage(resource.RUSAGE_SELF)
    peak_rss_kib = int(end.ru_maxrss)
    return {
        "ru_maxrss": peak_rss_kib,
        "ru_maxrss_units": "KiB_on_linux",
        "peak_rss_bytes": peak_rss_kib * 1024,
        "platform": sys.platform,
        "process_user_time_ns": int(
            max(0.0, end.ru_utime - start.ru_utime) * 1_000_000_000
        ),
        "process_system_time_ns": int(
            max(0.0, end.ru_stime - start.ru_stime) * 1_000_000_000
        ),
        "cgroup_memory_peak": _read_cgroup_memory_peak(),
    }


def compute_plain(
    fixture: Mapping[str, Any],
    *,
    expected_quimb_root: str | Path,
) -> dict[str, Any]:
    """Execute the ordinary-Quimb candidate without seeing another lane."""

    frozen, fixture_sha256 = _validated_fixture(fixture)
    source_path = Path(__file__).resolve(strict=True)
    source_sha256_before = _file_sha256(source_path)
    static_policy = scan_plain_worker_source(source_path.read_text(encoding="utf-8"))
    if not static_policy["passed"]:
        raise RuntimeError("plain worker static prohibited-reference scan failed")

    qtn, quimb_identity = _load_and_verify_quimb(Path(expected_quimb_root))
    _require_no_runtime_prohibited_imports()

    site_order = tuple(
        tuple(int(value) for value in coordinate) for coordinate in frozen["site_order"]
    )
    site_map = tuple(
        tuple(int(value) for value in row["coordinate"]) for row in frozen["site_map"]
    )
    graph_edges = tuple(
        tuple(int(value) for value in edge) for edge in frozen["graph_edges"]
    )
    coordinate_edges = tuple((site_map[a], site_map[b]) for a, b in graph_edges)
    zero = np.ascontiguousarray(np.asarray((1.0 + 0.0j, 0.0 + 0.0j), dtype="<c16"))

    usage_start = resource.getrusage(resource.RUSAGE_SELF)
    computation_start_ns = time.perf_counter_ns()

    preparation_start_ns = time.perf_counter_ns()
    psi0 = qtn.PEPS.product_state(
        {coordinate: zero.copy() for coordinate in site_order},
        cyclic=False,
    )
    plain = qtn.CircuitPEPSSimpleUpdate(
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
    preparation_gate_ledger, preparation_stream_sha256 = _apply_gate_block(
        qtn=qtn,
        circuit=plain,
        block=frozen["preparation"],
        expected_stream_sha256=EXPECTED_PREPARATION_STREAM_SHA256,
        site_map=site_map,
        graph_edges=graph_edges,
    )
    preparation_ns = time.perf_counter_ns() - preparation_start_ns

    preparation_raw_state, preparation_gauge_values = plain.get_state(
        absorb_gauges="return"
    )
    preparation_resources = _tensor_network_resource_ledger(
        preparation_raw_state,
        site_order=site_order,
        graph_edges=graph_edges,
    )
    preparation_gauges = _gauge_resource_ledger(
        gauges=preparation_gauge_values,
        state_snapshot=preparation_raw_state,
        site_order=site_order,
        graph_edges=graph_edges,
    )
    if tuple(preparation_resources["bond_dimensions"]) != (EXPECTED_PREPARATION_BONDS):
        raise RuntimeError("plain preparation bond ledger drifted")
    if (
        tuple(int(row["elements"]) for row in preparation_resources["sites"])
        != EXPECTED_PREPARATION_SITE_ELEMENTS
    ):
        raise RuntimeError("plain preparation site-element ledger drifted")
    preparation_state = plain.get_state(absorb_gauges=True)
    preparation_vector_start_ns = time.perf_counter_ns()
    preparation_vector = _materialize_vector(
        preparation_state,
        site_order=site_order,
    )
    preparation_vector_materialization_ns = (
        time.perf_counter_ns() - preparation_vector_start_ns
    )

    physical_clifford_start_ns = time.perf_counter_ns()
    clifford_gate_ledger, clifford_stream_sha256 = _apply_gate_block(
        qtn=qtn,
        circuit=plain,
        block=frozen["clifford"],
        expected_stream_sha256=EXPECTED_CLIFFORD_STREAM_SHA256,
        site_map=site_map,
        graph_edges=graph_edges,
    )
    physical_clifford_ns = time.perf_counter_ns() - physical_clifford_start_ns

    after_clifford_raw_state, after_clifford_gauge_values = plain.get_state(
        absorb_gauges="return"
    )
    after_clifford_resources = _tensor_network_resource_ledger(
        after_clifford_raw_state,
        site_order=site_order,
        graph_edges=graph_edges,
    )
    after_clifford_gauges = _gauge_resource_ledger(
        gauges=after_clifford_gauge_values,
        state_snapshot=after_clifford_raw_state,
        site_order=site_order,
        graph_edges=graph_edges,
    )
    after_clifford_state = plain.get_state(absorb_gauges=True)
    after_clifford_vector_start_ns = time.perf_counter_ns()
    after_clifford_vector = _materialize_vector(
        after_clifford_state,
        site_order=site_order,
    )
    after_clifford_vector_materialization_ns = (
        time.perf_counter_ns() - after_clifford_vector_start_ns
    )

    pepo_build_start_ns = time.perf_counter_ns()
    pepo, physical_term_ledger = _build_direct_sum_pepo(
        qtn=qtn,
        terms=frozen["physical_terms"],
        axis_contract=frozen["plain_pepo_local_axis_contract"],
    )
    pepo_build_ns = time.perf_counter_ns() - pepo_build_start_ns
    operator_resources = _tensor_network_resource_ledger(
        pepo,
        site_order=site_order,
        graph_edges=graph_edges,
    )
    expected_representation = frozen["expected_representation"]
    if (
        operator_resources["bond_dimensions"] != [3] * 10
        or operator_resources["maximum_bond_dimension"]
        != expected_representation["plain_operator_bond_dimension"]
        or operator_resources["total_tensor_elements"]
        != expected_representation["plain_operator_total_elements"]
        or operator_resources["maximum_site_tensor_elements"]
        != expected_representation["plain_operator_max_local_elements"]
    ):
        raise RuntimeError("plain direct-sum PEPO resource prediction failed")

    pepo_apply_start_ns = time.perf_counter_ns()
    final_state = pepo.apply(
        after_clifford_state,
        contract=True,
        compress=False,
    )
    pepo_apply_ns = time.perf_counter_ns() - pepo_apply_start_ns
    final_resources = _tensor_network_resource_ledger(
        final_state,
        site_order=site_order,
        graph_edges=graph_edges,
    )
    final_vector_start_ns = time.perf_counter_ns()
    final_vector = _materialize_vector(final_state, site_order=site_order)
    final_vector_materialization_ns = time.perf_counter_ns() - final_vector_start_ns

    vector_hashes = {
        "preparation": _vector_sha256(preparation_vector),
        "after_clifford": _vector_sha256(after_clifford_vector),
        "final_physical": _vector_sha256(final_vector),
    }
    computation_total_ns = time.perf_counter_ns() - computation_start_ns
    _require_no_runtime_prohibited_imports()
    checkout_after = _verify_checkout_identity(Path(expected_quimb_root))
    if {key: checkout_after[key] for key in ("root", "commit", "tree")} != {
        key: quimb_identity[key] for key in ("root", "commit", "tree")
    }:
        raise RuntimeError("Quimb checkout identity changed during the worker")
    source_sha256_after = _file_sha256(source_path)
    if source_sha256_after != source_sha256_before:
        raise RuntimeError("plain worker source changed during computation")

    timing_ns = {
        "preparation": int(preparation_ns),
        "physical_clifford": int(physical_clifford_ns),
        "pepo_build": int(pepo_build_ns),
        "pepo_apply": int(pepo_apply_ns),
        "preparation_vector_materialization": int(
            preparation_vector_materialization_ns
        ),
        "after_clifford_vector_materialization": int(
            after_clifford_vector_materialization_ns
        ),
        "final_physical_vector_materialization": int(final_vector_materialization_ns),
        "vector_materialization_total": int(
            preparation_vector_materialization_ns
            + after_clifford_vector_materialization_ns
            + final_vector_materialization_ns
        ),
        "plain_update": int(physical_clifford_ns + pepo_build_ns + pepo_apply_ns),
        "worker_computation_total": int(computation_total_ns),
    }
    if any(value <= 0 for value in timing_ns.values()):
        raise RuntimeError("plain worker produced a nonpositive timing segment")

    return {
        "schema": PLAIN_WORKER_SCHEMA,
        "status": "completed",
        "candidate_lane": PLAIN_LANE_NAME,
        "candidate_status": "equal_status_candidate_not_truth",
        "claim_boundary": frozen["claim_boundary"],
        "fixture_sha256": fixture_sha256,
        "fixture_schema": frozen["schema"],
        "vectors": {
            "preparation": preparation_vector,
            "after_clifford": after_clifford_vector,
            "final_physical": final_vector,
        },
        "vector_evidence": {
            name: {
                "sha256_little_endian_c128_c_order": digest,
                "shape": [256],
                "dtype": "complex128",
                "q0_axis": 0,
                "q0_bit_significance": "most_significant",
                "phase_fit_performed": False,
                "normalization_performed": False,
                "coordinate_permutation_performed": False,
                "dtype_cast_performed": False,
            }
            for name, digest in vector_hashes.items()
        },
        "gate_ledgers": {
            "preparation": preparation_gate_ledger,
            "preparation_gate_stream_sha256": preparation_stream_sha256,
            "physical_clifford": clifford_gate_ledger,
            "clifford_gate_stream_sha256": clifford_stream_sha256,
            "logical_to_coordinate_mapping_applied": True,
        },
        "physical_terms": physical_term_ledger,
        "operator_construction": {
            "term_count": 3,
            "term_product_pepo_count": 3,
            "instance_add_PEPO_call_count": 2,
            "module_level_add_PEPO_used": False,
            "sequential_operator_application_used": False,
            "operator_multiplication_used": False,
            "target_pepo_apply_call_count": 1,
            "contract": True,
            "compress": False,
            "coefficient_times_word_phase_applied_once_at_q0": True,
            "local_axis_contract": frozen["plain_pepo_local_axis_contract"],
            "resources": operator_resources,
        },
        "state_resources": {
            "preparation": {
                "state": preparation_resources,
                "gauges": preparation_gauges,
            },
            "after_clifford": {
                "state": after_clifford_resources,
                "gauges": after_clifford_gauges,
            },
            "after_pepo": {
                "state": final_resources,
                "gauges": {
                    "status": "UNAVAILABLE_NATIVE_PEPO_RESULT_NOT_VIDAL_GAUGED",
                    "gauge_elements": None,
                    "old_circuit_gauges_reused": False,
                },
            },
        },
        "orientation_control": {
            "status": "NOT_EXECUTED_IN_TARGET_WORKER",
            "external_pre_target_control_required": True,
            "target_fixture_apply_count": 0,
        },
        "timing_ns": timing_ns,
        "timing_scope": {
            "clock": "time.perf_counter_ns",
            "process_launch_and_import_excluded": True,
            "materialization_excluded_from_plain_update": True,
            "plain_update_formula": "physical_clifford + pepo_build + pepo_apply",
        },
        "resource_usage": _resource_usage(usage_start),
        "settings": {
            "max_bond": None,
            "cutoff": PEPS_GATE_SVD_CUTOFF,
            "cutoff_role": "floating_svd_null_direction_pruning_only",
            "physical_probability_floor": False,
            "renorm": False,
            "gauge_smudge": 0.0,
            "equilibrate_every": None,
            "dtype": "complex128",
            "to_backend": None,
            "convert_eager": True,
            "contraction_optimize": CONTRACTION_OPTIMIZE,
            "compression_used": False,
            "cyclic": False,
        },
        "provenance": {
            "worker_path": str(source_path),
            "worker_sha256": source_sha256_before,
            "fixture_seen_before_other_candidate_or_anchor": True,
            "other_candidate_or_anchor_payload_seen": False,
            "quimb": quimb_identity,
            "checkout_clean_after": checkout_after["clean_including_ignored"],
            "static_prohibited_reference_scan": static_policy,
            "runtime_prohibited_module_scan_passed": True,
            "process_environment": _process_environment(),
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "cpu_affinity": (
                sorted(os.sched_getaffinity(0))
                if hasattr(os, "sched_getaffinity")
                else None
            ),
        },
        "excluded_claims": [
            "ground_truth",
            "registered_ecs_carrier",
            "registered_ecs_record",
            "generic_peps_faithfulness",
            "generic_peps_contraction_certificate",
            "all_input_operator_equality",
            "scaling_evidence",
            "portable_performance",
        ],
    }


def _write_exclusive_bytes(path: Path, payload: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def _write_private_output(
    output_dir: Path,
    computation: Mapping[str, Any],
) -> dict[str, Any]:
    if not output_dir.is_absolute():
        raise ValueError("private output directory must be absolute")
    lexical = output_dir.absolute()
    resolved = lexical.resolve(strict=True)
    if lexical != resolved or not resolved.is_dir():
        raise RuntimeError("private output directory must be a nonsymlink directory")
    info = resolved.stat()
    if not stat.S_ISDIR(info.st_mode) or stat.S_IMODE(info.st_mode) & 0o077:
        raise RuntimeError("private output directory permissions are not private")
    if any(resolved.iterdir()):
        raise FileExistsError("private output directory must start empty")
    output_dir = resolved

    artifacts: dict[str, Any] = {}
    vectors = computation["vectors"]
    for name in ("preparation", "after_clifford", "final_physical"):
        vector = vectors[name]
        path = output_dir / f"{name}.npy"
        with path.open("xb") as stream:
            np.save(stream, vector, allow_pickle=False)
            stream.flush()
            os.fsync(stream.fileno())
        artifacts[name] = {
            "file": path.name,
            "file_sha256": _file_sha256(path),
            "vector_sha256_little_endian_c128_c_order": _vector_sha256(vector),
        }

    summary = {key: value for key, value in computation.items() if key != "vectors"}
    summary["artifacts"] = artifacts
    summary["publication"] = {
        "scope": "private_worker_output_not_final_publication",
        "output_directory": str(output_dir),
        "fresh_directory_created": True,
        "existing_destination_replaced": False,
    }
    encoded = (
        json.dumps(
            summary,
            allow_nan=False,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    _write_exclusive_bytes(output_dir / "plain_worker.json", encoded)
    descriptor = os.open(output_dir, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return summary


def _read_canonical_fixture(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    fixture = json.loads(raw)
    if not isinstance(fixture, dict):
        raise ValueError("fixture file must contain one JSON object")
    canonical = _canonical_json_bytes(fixture)
    if raw != canonical:
        raise ValueError("fixture file bytes are not the canonical JSON bytes")
    _validated_fixture(fixture)
    return fixture


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument(
        "--fork-checkout",
        "--expected-quimb-root",
        dest="fork_checkout",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--output-directory",
        "--output-dir",
        dest="output_directory",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--sample-kind",
        choices=("warmup", "measured", "control"),
        required=True,
    )
    parser.add_argument("--sample-index", type=int, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.sample_index < 0:
        raise ValueError("sample-index must be nonnegative")
    process_usage_started = resource.getrusage(resource.RUSAGE_SELF)
    worker_path = Path(__file__).resolve(strict=True)
    worker_sha256_before = _file_sha256(worker_path)
    process_envelope = verify_process_envelope()
    fork_before = _verify_checkout_identity(args.fork_checkout)
    fixture = _read_canonical_fixture(args.fixture.resolve(strict=True))
    computation = compute_plain(
        fixture,
        expected_quimb_root=args.fork_checkout,
    )
    if _file_sha256(worker_path) != worker_sha256_before:
        raise RuntimeError("plain worker source changed during execution")
    fork_after = _verify_checkout_identity(args.fork_checkout)
    if fork_after != fork_before:
        raise RuntimeError("fork identity changed during plain worker execution")
    computation["sample"] = {
        "kind": args.sample_kind,
        "index": args.sample_index,
    }
    computation["process_envelope"] = process_envelope
    computation["resource_usage"] = _resource_usage(process_usage_started)
    computation["provenance"].update(
        {
            "fork_pristine_before_and_after": True,
            "worker_artifacts_written_without_replacement": True,
            "candidate_output_input_paths_accepted": [],
            "anchor_output_input_paths_accepted": [],
        }
    )
    summary = _write_private_output(
        args.output_directory.absolute(), computation
    )
    print(
        json.dumps(
            {
                "schema": PLAIN_WORKER_SCHEMA,
                "status": summary["status"],
                "sample": summary["sample"],
                "fixture_sha256": summary["fixture_sha256"],
                "summary": str(
                    args.output_directory.resolve(strict=True)
                    / "plain_worker.json"
                ),
            },
            allow_nan=False,
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
