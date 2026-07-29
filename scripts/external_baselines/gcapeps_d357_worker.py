#!/usr/bin/env python3
"""GCAPEPS lane for the frozen d=3,5,7 unitary-prefix sweep.

The physical H/CX prefix is submitted once to the Stim Clifford frame and one
physical Y rotation is submitted through the certified Pauli-rotation API.
The worker emits representation and performance evidence only: it does not
materialize or contract a complete state and does not implement measurement,
reset, trajectory, detector, observable, or Record semantics.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import fields, is_dataclass
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
    "error_coupling_simulator.external.gcapeps_d357_gcapeps_worker.v2"
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
EXPECTED_STIM_VERSION = "1.16.0"
EXPECTED_DISTANCES = (3, 5, 7)
EXPECTED_SETTINGS = {
    "to_backend": None,
    "convert_eager": True,
    "max_bond": None,
    "cutoff": 1e-12,
    "renorm": False,
    "gauge_smudge": 0.0,
    "equilibrate_every": None,
}
EXPECTED_RESOURCE_LIMITS = {
    3: {
        "max_local_operator_elements": 64,
        "max_total_operator_elements": 144,
        "max_local_candidate_tensor_elements": 32,
        "max_total_candidate_tensor_elements": 72,
        "max_predicted_bond_dimension": 2,
        "max_routed_rank_product": 2,
        "max_total_bond_growth_product": 2,
        "expected_refactor_factor_product": 1,
    },
    5: {
        "max_local_operator_elements": 64,
        "max_total_operator_elements": 272,
        "max_local_candidate_tensor_elements": 32,
        "max_total_candidate_tensor_elements": 136,
        "max_predicted_bond_dimension": 2,
        "max_routed_rank_product": 2,
        "max_total_bond_growth_product": 2,
        "expected_refactor_factor_product": 1,
    },
    7: {
        "max_local_operator_elements": 64,
        "max_total_operator_elements": 464,
        "max_local_candidate_tensor_elements": 32,
        "max_total_candidate_tensor_elements": 232,
        "max_predicted_bond_dimension": 2,
        "max_routed_rank_product": 2,
        "max_total_bond_growth_product": 2,
        "expected_refactor_factor_product": 1,
    },
}
THREAD_ENVIRONMENT = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "BLIS_NUM_THREADS",
)
_FORBIDDEN_CALLS = (
    "state" + "_vector",
    "to" + "_dense",
    "no" + "rm",
    "apply_" + "coherent_pauli_sum",
)


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
        "_gcapeps_d357_fixture_contract_worker",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load the d357 neutral fixture contract")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, {"path": str(path), "sha256": _file_sha256(path)}


def scan_gcapeps_worker_source(source: str) -> dict[str, Any]:
    """Reject complete-state and generic coherent-sum calls by syntax."""

    tree = ast.parse(source)
    prohibited: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Attribute):
            name = node.func.attr
        elif isinstance(node.func, ast.Name):
            name = node.func.id
        else:
            name = ""
        if name in _FORBIDDEN_CALLS:
            prohibited.append(name)
    return {
        "passed": not prohibited,
        "prohibited_calls": sorted(set(prohibited)),
        "forbidden_call_set": list(_FORBIDDEN_CALLS),
    }


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
        or frozen.get("peps_settings") != EXPECTED_SETTINGS
    ):
        raise ValueError("fixture headline/settings contract drifted")
    edges = frozen.get("graph", {}).get("edges")
    gates = frozen.get("prefix", {}).get("gates")
    cells = frozen.get("grid_cells")
    schedule = frozen.get("accumulated_frame_schedule", {}).get("rows")
    locations = frozen.get("error_locations")
    limits = frozen.get("gcapeps_multi_resource_limits")
    if not all(
        isinstance(value, list)
        for value in (edges, gates, cells, schedule, locations)
    ) or not isinstance(limits, dict):
        raise ValueError("fixture grid execution blocks are unavailable")
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
    if len(locations) != 4 or len(schedule) != distance * 4:
        raise ValueError("fixture location/schedule width drifted")
    expected_limits = {
        "max_local_operator_elements": 64,
        "max_total_operator_elements": 64 * n_qubits,
        "max_local_candidate_tensor_elements": 4_194_304,
        "max_total_candidate_tensor_elements": 16_777_216,
        "max_predicted_bond_dimension": 64,
        "max_routed_rank_product": 64,
        "max_total_bond_growth_product": 64,
        "expected_refactor_factor_product": 1,
    }
    if limits != expected_limits:
        raise ValueError("fixture multi-update hard guard drifted")
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
        or abs(math.sin(theta / 2.0) ** 2 - probability)
        > 8.0 * sys.float_info.epsilon
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
) -> tuple[Any, Any, Any, Any, dict[str, Any]]:
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
    qtn_origin = _validate_import_origin(
        Path(qtn.__file__),
        checkout,
        label="Quimb tensor",
    )
    gcapeps_origin = _validate_import_origin(
        Path(gcapeps.__file__),
        checkout,
        label="GCAPEPS",
    )
    return (
        np,
        qtn,
        stim,
        gcapeps,
        {
            "numpy_version": np.__version__,
            "numpy_import_origin": str(Path(np.__file__).resolve(strict=True)),
            "quimb_distribution_version": metadata.version("quimb"),
            "quimb_import_origin": quimb_origin,
            "quimb_tensor_import_origin": qtn_origin,
            "gcapeps_import_origin": gcapeps_origin,
            "stim_version": stim.__version__,
            "stim_import_origin": str(Path(stim.__file__).resolve(strict=True)),
        },
    )


def _json_value(value: Any) -> Any:
    if is_dataclass(value):
        return {
            field.name: _json_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if hasattr(value, "item"):
        try:
            return value.item()
        except (TypeError, ValueError):
            pass
    return value


def _product_representation(
    *,
    n_qubits: int,
    edge_count: int,
) -> dict[str, Any]:
    return {
        "tensor_count": n_qubits,
        "edge_count": edge_count,
        "maximum_bond_dimension": 1,
        "bond_dimensions": [1] * edge_count,
        "total_tensor_elements": 2 * n_qubits,
        "maximum_site_tensor_elements": 2,
        "logical_tensor_bytes": 32 * n_qubits,
        "dtype": "complex128",
        "epistemic_class": "numerical_only_representation_resource",
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


def _validate_rotation_update(
    update: Any,
    *,
    fixture: Mapping[str, Any],
    schedule_row: Mapping[str, Any],
    expected_limits: Mapping[str, int],
    previous_representation: Mapping[str, Any],
    expected_revision_before: int,
    require_tight_first_ledger: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    n_qubits = int(fixture["n_qubits"])
    support = tuple(int(q) for q in schedule_row["support"])
    if (
        update.operation != "pauli_rotation"
        or update.strategy
        != (
            "one_site_coherent_dense"
            if len(support) == 1
            else "exact_tree_routed_coherent_pepo"
        )
        or tuple(update.support) != support
        or tuple(update.dependence_set) != support
        or update.max_bond_before
        != previous_representation["maximum_bond_dimension"]
        or update.max_bond_limit is not None
        or update.cutoff != 1e-12
        or update.residual_revision_before != expected_revision_before
        or update.residual_revision_after != expected_revision_before + 1
        or update.declared_term_count != 2
        or update.active_term_count != 2
        or update.truncation_applied is not False
        or update.compression_applied is not False
        or update.smudging_applied is not False
        or update.approximate_contraction_applied is not False
        or update.nonzero_validation != "unitary_pauli_rotation"
        or update.candidate_norm_squared is not None
    ):
        raise RuntimeError("GCAPEPS residual update contract drifted")
    if len(support) == 1:
        if (
            update.max_bond_after
            != previous_representation["maximum_bond_dimension"]
            or update.routing_root is not None
            or update.routing_vertices
            or update.routing_tree_edges
            or update.edge_bonds
            or update.resource_ledger is not None
            or update.dense_operator_action is not None
            or require_tight_first_ledger
        ):
            raise RuntimeError("GCAPEPS one-site residual evidence drifted")
        representation = dict(previous_representation)
        evidence = {
            "residual_update": _json_value(update),
            "construction_resource_ledger": None,
            "edge_growth_ledger": [],
            "route": None,
            "resource_limits": dict(expected_limits),
            "expected_refactor_factor_product": 1,
            "dense_operator_action": None,
            "tight_first_update_ledger_checked": False,
            "one_site_shape_and_bond_unchanged": True,
        }
        return representation, evidence

    graph_edges = tuple(
        tuple(int(q) for q in edge) for edge in fixture["graph"]["edges"]
    )
    graph_keys = {frozenset(edge) for edge in graph_edges}
    route_keys = {
        frozenset((int(a), int(b))) for a, b in update.routing_tree_edges
    }
    if not route_keys or not route_keys.issubset(graph_keys):
        raise RuntimeError("GCAPEPS route contains a non-graph edge")
    if not set(support).issubset({int(q) for q in update.routing_vertices}):
        raise RuntimeError("GCAPEPS route omits pulled-back support")
    ledger = update.resource_ledger
    if ledger is None:
        raise RuntimeError("GCAPEPS construction resource ledger is missing")
    observed_limits = {
        field.name: getattr(ledger.limits, field.name)
        for field in fields(ledger.limits)
    }
    if observed_limits != dict(expected_limits):
        raise RuntimeError("GCAPEPS runtime resource limits drifted")
    aggregate_limits = {
        "operator_elements_total": expected_limits["max_total_operator_elements"],
        "operator_elements_largest_site": expected_limits[
            "max_local_operator_elements"
        ],
        "state_elements_after_total": expected_limits[
            "max_total_candidate_tensor_elements"
        ],
        "state_elements_after_largest_site": expected_limits[
            "max_local_candidate_tensor_elements"
        ],
    }
    for name, limit in aggregate_limits.items():
        value = int(getattr(ledger, name))
        if value <= 0 or value > limit:
            raise RuntimeError(f"GCAPEPS construction ledger {name} exceeded guard")
    if (
        ledger.state_elements_before_total
        != previous_representation["total_tensor_elements"]
        or ledger.state_elements_before_largest_site
        != previous_representation["maximum_site_tensor_elements"]
        or ledger.state_elements_after_total
        != ledger.predicted_state_elements_after_total
        or ledger.state_elements_after_largest_site
        != ledger.predicted_state_elements_after_largest_site
        or ledger.state_payload_bytes_after_total
        != ledger.state_elements_after_total * 16
        or ledger.complex128_bytes_per_element != 16
        or len(ledger.site_tensors) != n_qubits
    ):
        raise RuntimeError("GCAPEPS state-element construction ledger drifted")
    for qubit, row in enumerate(ledger.site_tensors):
        if (
            row.qubit != qubit
            or row.site != qubit
            or row.state_elements_after != row.predicted_state_elements_after
            or row.state_payload_bytes_after != row.state_elements_after * 16
            or row.state_backend_before != "numpy"
            or row.state_backend_after != "numpy"
            or row.state_dtype_before != "complex128"
            or row.state_dtype_after != "complex128"
        ):
            raise RuntimeError("GCAPEPS per-site construction ledger drifted")
    if require_tight_first_ledger:
        tight = {
            "operator_elements_total": 4 * n_qubits + 76,
            "operator_elements_largest_site": 64,
            "state_elements_before_total": 2 * n_qubits,
            "state_elements_before_largest_site": 2,
            "state_elements_after_total": 2 * n_qubits + 38,
            "state_elements_after_largest_site": 32,
        }
        for name, expected in tight.items():
            if getattr(ledger, name) != expected:
                raise RuntimeError(f"GCAPEPS tight first ledger {name} drifted")
    seen: set[frozenset[int]] = set()
    edge_rows: list[dict[str, Any]] = []
    final_bonds: list[int] = []
    for row in update.edge_bonds:
        edge = tuple(int(q) for q in row.qubit_edge)
        key = frozenset(edge)
        if key in seen or key not in graph_keys:
            raise RuntimeError("GCAPEPS edge ledger coverage drifted")
        seen.add(key)
        routed = key in route_keys
        expected_factor = 2 if routed else 1
        if (
            row.routed is not routed
            or row.operator_bond != expected_factor
            or row.predicted_state_bond_after != row.state_bond_after
            or row.routed_rank_product_after
            != row.routed_rank_product_before * expected_factor
            or row.refactor_operator_schmidt_factor != 1
            or row.refactor_operator_schmidt_product_before != 1
            or row.refactor_operator_schmidt_product_after != 1
            or row.total_bond_growth_product_before
            != row.routed_rank_product_before
            or row.total_bond_growth_product_after
            != row.routed_rank_product_after
            or row.routed_rank_product_after
            > expected_limits["max_routed_rank_product"]
            or row.total_bond_growth_product_after
            > expected_limits["max_total_bond_growth_product"]
            or row.state_bond_after
            > expected_limits["max_predicted_bond_dimension"]
            or row.compressed is not False
        ):
            raise RuntimeError("GCAPEPS per-edge growth ledger drifted")
        final_bonds.append(int(row.state_bond_after))
        edge_rows.append(_json_value(row))
    if seen != graph_keys:
        raise RuntimeError("GCAPEPS edge ledger does not cover the graph")
    maximum_bond = max(final_bonds)
    if update.max_bond_after != maximum_bond:
        raise RuntimeError("GCAPEPS update maximum bond disagrees with edge ledger")
    dense_evidence = update.dense_operator_action
    if (
        dense_evidence is None
        or dense_evidence.qubit_count != n_qubits
        or dense_evidence.max_qubits != 10
        or dense_evidence.checked is not False
        or dense_evidence.status
        != "not_checked_above_exact_small_ceiling"
    ):
        raise RuntimeError("GCAPEPS above-ceiling evidence status drifted")
    representation = {
        "tensor_count": n_qubits,
        "edge_count": len(graph_edges),
        "maximum_bond_dimension": maximum_bond,
        "bond_dimensions": final_bonds,
        "total_tensor_elements": int(ledger.state_elements_after_total),
        "maximum_site_tensor_elements": int(
            ledger.state_elements_after_largest_site
        ),
        "logical_tensor_bytes": int(ledger.state_payload_bytes_after_total),
        "dtype": "complex128",
        "epistemic_class": "numerical_only_representation_resource",
    }
    evidence = {
        "residual_update": _json_value(update),
        "construction_resource_ledger": _json_value(ledger),
        "edge_growth_ledger": edge_rows,
        "route": {
            "root": int(update.routing_root),
            "vertices": [int(q) for q in update.routing_vertices],
            "edges": [[int(a), int(b)] for a, b in update.routing_tree_edges],
        },
        "resource_limits": dict(expected_limits),
        "expected_refactor_factor_product": 1,
        "dense_operator_action": _json_value(dense_evidence),
        "tight_first_update_ledger_checked": require_tight_first_ledger,
    }
    return representation, evidence

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


def compute_gcapeps_candidate(
    fixture: Mapping[str, Any],
    *,
    cell: Mapping[str, Any],
    fixture_sha256: str,
    fork_checkout: Path,
) -> dict[str, Any]:
    np, qtn, stim, gcapeps, imports = _runtime_imports(fork_checkout)
    n_qubits = int(fixture["n_qubits"])
    distance = int(fixture["distance"])
    edges = tuple(tuple(int(q) for q in edge) for edge in fixture["graph"]["edges"])
    prefix_rows = fixture["prefix"]["gates"]
    layers = int(cell["round_layers"])
    complexity = int(cell["noise_complexity"])
    selected_targets = tuple(int(q) for q in cell["selected_targets"])
    operations = tuple(cell["operation_ledger"])
    locations_by_target = {
        int(row["target"]): dict(row) for row in fixture["error_locations"]
    }
    schedule_by_key = {
        (int(row["layer"]), int(row["location_rank"])): dict(row)
        for row in fixture["accumulated_frame_schedule"]["rows"]
    }
    hard_guard = dict(fixture["gcapeps_multi_resource_limits"])
    hard_guard.pop("expected_refactor_factor_product")

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
    initial = _product_representation(
        n_qubits=n_qubits,
        edge_count=len(edges),
    )
    limits = gcapeps.GCAPEPSResourceLimits(**hard_guard)
    carrier = gcapeps.QuimbPEPSCarrier(
        circuit,
        site_order=tuple(range(n_qubits)),
        contraction_optimize="greedy",
        resource_limits=limits,
    )
    state = gcapeps.GCAPEPSState(
        gcapeps.StimCliffordFrame(n_qubits),
        carrier,
    )
    del carrier, circuit
    if state.events or state.frame.revision != 0:
        raise RuntimeError("GCAPEPS state did not begin at frame revision zero")

    prefix_circuit = stim.Circuit()
    for row in prefix_rows:
        prefix_circuit.append(
            str(row["token"]),
            [int(q) for q in row["targets"]],
        )
    prefix_sha256 = _sha256_bytes(str(prefix_circuit).encode("utf-8"))
    if prefix_sha256 != fixture["prefix"]["prefix_stim_sha256"]:
        raise RuntimeError("runtime Stim prefix identity drifted")
    physical_words = {}
    for target in selected_targets:
        labels = "I" * target + "Y" + "I" * (n_qubits - target - 1)
        physical_words[target] = gcapeps.QubitPauliWord.from_labels(
            labels,
            phase=1.0,
        )
    angle = np.float64(cell["theta_radians"])

    prefix_total_ns = 0
    rotation_total_ns = 0
    prefix_batches_completed = 0
    completed_layers = 0
    completed_rotations = 0
    attempted_rotations = 0
    operation_index = 0
    residual_native_gate_count = 0
    current_representation = dict(initial)
    after_prefix = None
    timing_rows: list[dict[str, Any]] = []
    frame_events: list[dict[str, Any]] = []
    construction_updates: list[dict[str, Any]] = []
    censor = None
    for layer in range(1, layers + 1):
        operation = _require_operation(
            operations,
            operation_index,
            layer=layer,
            kind="clifford_prefix",
        )
        if (
            operation.get("prefix_gate_count") != len(prefix_rows)
            or operation.get("prefix_gate_stream_sha256")
            != fixture["prefix"]["gate_stream_sha256"]
        ):
            raise RuntimeError("cell prefix operation binding drifted")
        before_bond = current_representation["maximum_bond_dimension"]
        started = time.perf_counter_ns()
        frame_event = state.apply_clifford(prefix_circuit)
        elapsed = _positive_elapsed(started, name="tableau prefix apply")
        prefix_total_ns += elapsed
        prefix_batches_completed += 1
        if (
            frame_event.operation != "clifford_frame_update"
            or frame_event.frame_revision_before != layer - 1
            or frame_event.frame_revision_after != layer
            or frame_event.peps_gate_count_before
            != residual_native_gate_count
            or frame_event.peps_gate_count_after
            != residual_native_gate_count
            or frame_event.max_bond_before != before_bond
            or frame_event.max_bond_after != before_bond
            or frame_event.residual_update is not None
            or frame_event.residual_revision_before != completed_rotations
            or frame_event.residual_revision_after != completed_rotations
        ):
            raise RuntimeError("batched Clifford frame event drifted")
        frame_events.append(_json_value(frame_event))
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
            after_prefix = dict(current_representation)
        for target in selected_targets:
            operation = _require_operation(
                operations,
                operation_index,
                layer=layer,
                kind="physical_ry",
                target=target,
            )
            if (
                operation.get("theta_radians") != float(angle)
                or operation.get("theta_float64_hex") != float(angle).hex()
            ):
                raise RuntimeError("cell rotation angle binding drifted")
            location_rank = int(locations_by_target[target]["location_rank"])
            schedule = schedule_by_key[(layer, location_rank)]
            if schedule["target"] != target:
                raise RuntimeError("accumulated-frame schedule target drifted")
            native_gate_increment = 1 if len(schedule["support"]) == 1 else 0
            attempted_rotations += 1
            started = time.perf_counter_ns()
            try:
                rotation_event = state.apply_pauli_rotation(
                    physical_words[target],
                    angle,
                )
            except gcapeps.PEPOResourceError as exc:
                if (
                    len(state.events)
                    != prefix_batches_completed + completed_rotations
                    or state.frame.revision != layer
                ):
                    raise RuntimeError(
                        "resource guard failure committed a routing event"
                    ) from exc
                elapsed = _positive_elapsed(
                    started,
                    name="resource-guard-censored tree rotation",
                )
                rotation_total_ns += elapsed
                timing_rows.append(
                    {
                        "operation_index": operation_index,
                        "layer": layer,
                        "kind": "physical_ry",
                        "target": target,
                        "location_rank": location_rank,
                        "elapsed_ns": elapsed,
                        "status": "resource_guard_censored",
                    }
                )
                censor = {
                    "classification": "RESOURCE_GUARD_CENSORED",
                    "error_type": type(exc).__name__,
                    "stage": exc.stage,
                    "metric": exc.metric,
                    "predicted": int(exc.predicted),
                    "limit": int(exc.limit),
                    "message": str(exc),
                    "failed_operation_index": operation_index,
                    "failed_layer": layer,
                    "failed_location_rank": location_rank,
                    "failed_target": target,
                    "failed_routing_event_not_committed": True,
                    "carrier_update_contract": "candidate_then_commit",
                }
                break
            elapsed = _positive_elapsed(started, name="certified tree rotation apply")
            rotation_total_ns += elapsed
            expected_pulled = str(schedule["signed_pullback"]).replace("_", "I")
            if (
                rotation_event.operation != "pulled_pauli_rotation"
                or rotation_event.frame_revision_before != layer
                or rotation_event.frame_revision_after != layer
                or rotation_event.physical_pauli != str(physical_words[target])
                or rotation_event.pulled_back_pauli != expected_pulled
                or rotation_event.peps_gate_count_before
                != residual_native_gate_count
                or rotation_event.peps_gate_count_after
                != residual_native_gate_count + native_gate_increment
                or rotation_event.max_bond_before
                != current_representation["maximum_bond_dimension"]
                or rotation_event.residual_revision_before != completed_rotations
                or rotation_event.residual_revision_after
                != completed_rotations + 1
            ):
                raise RuntimeError("GCAPEPS physical rotation event drifted")
            update = rotation_event.residual_update
            if update is None:
                raise RuntimeError("GCAPEPS rotation has no residual update")
            next_representation, construction = _validate_rotation_update(
                update,
                fixture=fixture,
                schedule_row=schedule,
                expected_limits=hard_guard,
                previous_representation=current_representation,
                expected_revision_before=completed_rotations,
                require_tight_first_ledger=(completed_rotations == 0),
            )
            completed_rotations += 1
            residual_native_gate_count += native_gate_increment
            current_representation = next_representation
            construction_updates.append(
                {
                    "operation_index": operation_index,
                    "layer": layer,
                    "location_rank": location_rank,
                    "target": target,
                    "physical_signed_word": str(physical_words[target]),
                    "observed_signed_pullback": rotation_event.pulled_back_pauli,
                    "expected_signed_pullback": expected_pulled,
                    "expected_support": list(schedule["support"]),
                    **construction,
                }
            )
            timing_rows.append(
                {
                    "operation_index": operation_index,
                    "layer": layer,
                    "kind": "physical_ry",
                    "target": target,
                    "location_rank": location_rank,
                    "elapsed_ns": elapsed,
                    "status": "completed",
                }
            )
            operation_index += 1
        if censor is not None:
            break
        completed_layers = layer
    if censor is None and operation_index != len(operations):
        raise RuntimeError("cell operation ledger has unconsumed rows")
    if after_prefix is None:
        raise RuntimeError("GCAPEPS execution produced no prefix")
    status = "completed" if censor is None else "resource_guard_censored"
    frame_snapshot = state.frame
    result = {
        "schema": WORKER_SCHEMA,
        "status": status,
        "lane": "gcapeps_persistent_live_frame_plus_rank2_tree_residual",
        "claim_boundary": fixture["claim_boundary"],
        "fixture": {
            "schema": fixture["schema"],
            "fixture_id": fixture["fixture_id"],
            "canonical_sha256": fixture_sha256,
            "distance": distance,
            "n_qubits": n_qubits,
            "dtype": fixture["dtype"],
            "prefix_gate_count": len(prefix_rows),
            "prefix_stream_sha256": fixture["prefix"]["gate_stream_sha256"],
            "prefix_stim_sha256": prefix_sha256,
            "graph_edge_count": len(edges),
            "graph_edge_stream_sha256": fixture["graph"]["edge_stream_sha256"],
            "grid_cells_sha256": fixture["grid_cells_sha256"],
            "accumulated_frame_schedule_sha256": fixture[
                "accumulated_frame_schedule"
            ]["schedule_sha256"],
            "cell_id": cell["cell_id"],
            "role": cell["role"],
            "round_layers": layers,
            "noise_complexity": complexity,
            "p_twirl": float(cell["p_twirl"]),
            "p_twirl_float64_hex": cell["p_twirl_float64_hex"],
            "theta_radians": float(angle),
            "theta_float64_hex": cell["theta_float64_hex"],
            "selected_targets": list(selected_targets),
            "expected_rotation_count": int(cell["rotation_count"]),
        },
        "numerical_settings": {
            "dtype": "complex128",
            **EXPECTED_SETTINGS,
        },
        "rotation": {
            "physical_pauli": "Y",
            "selected_targets": list(selected_targets),
            "theta_radians": float(angle),
            "theta_float64_hex": float(angle).hex(),
            "p_twirl": float(cell["p_twirl"]),
            "active_rank_per_rotation": 2,
            "physical_api": "GCAPEPSState.apply_pauli_rotation",
            "pullback_injected_by_fixture": False,
        },
        "progress": {
            "persistent_state_instances": 1,
            "prefix_batches_completed": prefix_batches_completed,
            "completed_layers": completed_layers,
            "completed_rotations": completed_rotations,
            "attempted_rotations": attempted_rotations,
            "expected_layers": layers,
            "expected_rotations": layers * complexity,
            "residual_native_gate_count": residual_native_gate_count,
        },
        "timing_ns": {
            "tableau_prefix_apply_ns": prefix_total_ns,
            "certified_tree_rotation_apply_ns": rotation_total_ns,
            "update_ns": prefix_total_ns + rotation_total_ns,
            "operation_rows": timing_rows,
        },
        "timing_policy": {
            "update_formula": (
                "sum(tableau_prefix_apply_ns)+"
                "sum(certified_tree_rotation_apply_ns_including_guard_attempt)"
            ),
            "prefix_submitted_as_one_stim_circuit_per_layer": True,
            "prefix_circuit_materialization_excluded_from_update": True,
            "initialization_import_fixture_and_snapshots_excluded_from_update": True,
            "worker_total_includes_one_provisional_report_serialization": True,
            "final_atomic_publication_excluded_from_worker_total": True,
        },
        "frame": {
            "backend": frame_snapshot.backend_name,
            "revision": frame_snapshot.revision,
            "batched_apply_calls": prefix_batches_completed,
            "physical_prefix_gate_count_per_batch": len(prefix_rows),
            "events": frame_events,
        },
        "representation": {
            "initial": initial,
            "after_prefix": after_prefix,
            "final_or_partial": current_representation,
            "final": current_representation if censor is None else None,
        },
        "construction": {
            "updates": construction_updates,
            "successful_update_count": len(construction_updates),
            "partial_ledger_complete_through_last_success": True,
            "multi_resource_limits": hard_guard,
            "expected_refactor_factor_product": 1,
        },
        "censor": censor,
        "imports": imports,
        "candidate_semantics": {
            "is_truth": False,
            "complete_state_contraction_performed": False,
            "norm_computed": False,
            "fidelity_computed": False,
            "measurement_reset_or_record_computed": False,
            "generic_coherent_sum_api_used": False,
            "finite_bond_cap": None,
            "tree_lowering_compressed": False,
            "cutoff_role": "floating_svd_null_direction_pruning_only",
            "above_exact_small_ceiling": True,
            "structural_validation_only": True,
            "round_layers_are_complete_qec_rounds": False,
            "p_twirl_is_sampled_frequency": False,
        },
    }
    return result

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
    static_scan = scan_gcapeps_worker_source(
        worker_path.read_text(encoding="utf-8")
    )
    if not static_scan["passed"]:
        raise RuntimeError("GCAPEPS worker forbidden-call scan failed")
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
    result = compute_gcapeps_candidate(
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
        "gcapeps_source_scan": static_scan,
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
