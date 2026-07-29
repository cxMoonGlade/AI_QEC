#!/usr/bin/env python3
"""Run the preregistered GCAPEPS bridge forced-truncation experiment.

This is a claim-bounded exact-small supervisor. It runs lanes A, T, N0, N1,
N2, D1, K0, and K1 only after both repositories are committed at caller-bound
Git identities, both ordinary worktrees are clean, the fork's ignored runtime
inventory is recorded, ``PYTHONPATH`` is absent, and Quimb/GCAPEPS import from
that exact fork.

The output is a complete-vector and local-split evidence packet. Local
discarded singular-value weight is never promoted to a global PEPS, Record,
measurement, reset, accumulated-error, or scaling certificate. No timing
headline is collected.
"""

from __future__ import annotations

import argparse
import ast
import copy
from dataclasses import replace
import hashlib
import importlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from types import ModuleType, SimpleNamespace
from typing import Any, Mapping, Sequence

import numpy as np


REPORT_SCHEMA = "error_coupling_simulator.external.gcapeps_native_forced_truncation.v1"
BASE_FORK_COMMIT = "6fbbf74cd36686ed30a4d8865697ce46e47056c1"
LANE_ORDER = ("A", "T", "N0", "N1", "N2", "D1", "K0", "K1")
EXACT_BAND = 1.0e-12
POSITIVE_TAIL_THRESHOLD = 1.0e-12
_HEX40 = re.compile(r"[0-9a-f]{40}")
_HEX64 = re.compile(r"[0-9a-f]{64}")
_C128 = np.dtype(np.complex128)
_F64 = np.dtype(np.float64)

_SCRIPT_PATH = Path(__file__).resolve()
_REPO_ROOT = _SCRIPT_PATH.parents[2]
_ANCHOR_PATH = (
    _REPO_ROOT
    / "scripts"
    / "external_baselines"
    / "gcapeps_forced_truncation_dense_anchor.py"
)
_PREREG_PATH = (
    _REPO_ROOT
    / "docs"
    / "simulator_validation"
    / "GCAPEPS_NATIVE_FORCED_TRUNCATION_PREREG_2026-07-29.md"
)
_CLOSURE_PATH = (
    _REPO_ROOT
    / "docs"
    / "simulator_validation"
    / "GCAPEPS_NATIVE_FORCED_TRUNCATION_LITERATURE_CLOSURE_2026-07-29.md"
)
_PARENT_RELATIVE_PATHS = (
    "scripts/external_baselines/run_gcapeps_native_forced_truncation.py",
    "scripts/external_baselines/gcapeps_forced_truncation_dense_anchor.py",
    ("docs/simulator_validation/GCAPEPS_NATIVE_FORCED_TRUNCATION_PREREG_2026-07-29.md"),
    (
        "docs/simulator_validation/"
        "GCAPEPS_NATIVE_FORCED_TRUNCATION_LITERATURE_CLOSURE_2026-07-29.md"
    ),
    "tests/test_external_gcapeps_native_forced_truncation.py",
)
_FORK_TRACKED_PATHS = (
    "quimb/experimental/gcapeps/__init__.py",
    "quimb/experimental/gcapeps/carrier.py",
    "quimb/experimental/gcapeps/native.py",
    "quimb/experimental/gcapeps/state.py",
    "tests/test_experimental/test_gcapeps_native.py",
    "tests/test_experimental/test_gcapeps_native_truncation.py",
)
_FORBIDDEN_ANCHOR_IMPORT_ROOTS = frozenset(
    {
        "quimb",
        "stim",
        "sdim",
        "gcapeps",
        "error_coupling_simulator",
    }
)
_METRIC_KEYS = frozenset(
    {
        "reference_norm",
        "candidate_norm",
        "reference_norm_squared",
        "candidate_norm_squared",
        "d_inf",
        "d_2",
        "d_rel",
        "d_norm",
        "fidelity_raw",
        "fidelity_roundoff_correction",
        "fidelity",
        "infidelity",
        "normalized_pure_state_trace_distance",
        "phase_fit_performed",
        "normalization_performed",
        "dtype_cast_performed",
        "coordinate_permutation_performed",
    }
)
_SPLIT_KEYS = frozenset(
    {
        "step_index",
        "gate_role",
        "edge",
        "ordered_sites",
        "configured_max_bond",
        "configured_cutoff",
        "configured_cutoff_mode",
        "full_singular_values",
        "kept_singular_values",
        "full_bond_dimension",
        "kept_bond_dimension",
        "pre_split_weight",
        "discarded_squared_weight",
        "discarded_fraction",
        "keep_by_cutoff",
        "keep_by_cap",
        "actual_keep",
        "cause",
        "dimension_reduced",
        "positive_discarded_weight",
        "positive_discarded_weight_threshold",
        "not_a_global_error_bound",
    }
)


_LEDGER_KEYS = frozenset(
    {
        "compiler_revision",
        "plan_digest_sha256",
        "plan_step_count",
        "two_site_step_count",
        "split_records",
        "positive_discarded_event_count",
        "dimension_reduction_event_count",
        "total_discarded_squared_weight_diagnostic_only",
        "any_smudging_applied",
        "not_a_global_error_bound",
    }
)


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.resolve(strict=True).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _summarize_ignored_status(status: str) -> tuple[dict[str, Any], tuple[str, ...]]:
    first_entries: list[str] = []
    last_entries: list[str] = []
    component_counts: dict[str, int] = {}
    nonignored_entries: list[str] = []
    entry_count = 0
    for line in status.splitlines():
        if not line.startswith("!! "):
            nonignored_entries.append(line)
            continue
        path = line[3:]
        entry_count += 1
        if len(first_entries) < 10:
            first_entries.append(path)
        last_entries.append(path)
        if len(last_entries) > 10:
            last_entries.pop(0)
        component = path.split("/", 1)[0]
        component_counts[component] = component_counts.get(component, 0) + 1
    summary = {
        "entry_count": entry_count,
        "full_status_sha256": hashlib.sha256(status.encode("utf-8")).hexdigest(),
        "counts_by_first_path_component": {
            key: component_counts[key] for key in sorted(component_counts)
        },
        "first_entries": first_entries,
        "last_entries": last_entries,
        "sample_limit_each_end": 10,
        "full_entry_list_emitted": False,
    }
    return summary, tuple(nonignored_entries)


def _require_hex40(value: str, *, label: str) -> str:
    if not isinstance(value, str) or _HEX40.fullmatch(value) is None:
        raise ValueError(f"{label} must be a full lowercase 40-hex Git id")
    return value


def _git_scalar(repo: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    value = completed.stdout.strip()
    if not value or "\n" in value:
        raise RuntimeError("Git scalar command returned an invalid value")
    return value


def _git_status(repo: Path, *, include_ignored: bool) -> str:
    command = [
        "git",
        "-C",
        str(repo),
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    ]
    if include_ignored:
        command.append("--ignored")
    return subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _validate_repo(
    repo: Path,
    *,
    expected_commit: str,
    expected_tree: str,
    include_ignored: bool,
    label: str,
) -> dict[str, Any]:
    expected_commit = _require_hex40(
        expected_commit,
        label=f"expected {label} commit",
    )
    expected_tree = _require_hex40(
        expected_tree,
        label=f"expected {label} tree",
    )
    lexical = repo.absolute()
    resolved = lexical.resolve(strict=True)
    if lexical != resolved or not resolved.is_dir():
        raise RuntimeError(f"{label} repository must be a nonsymlink directory")
    top = Path(_git_scalar(resolved, "rev-parse", "--show-toplevel")).resolve(
        strict=True
    )
    if top != resolved:
        raise RuntimeError(f"{label} path is not its Git top level")
    commit = _git_scalar(resolved, "rev-parse", "--verify", "HEAD^{commit}")
    tree = _git_scalar(resolved, "rev-parse", "--verify", "HEAD^{tree}")
    if commit != expected_commit or tree != expected_tree:
        raise RuntimeError(f"{label} identity drifted: commit={commit}, tree={tree}")
    status = _git_status(resolved, include_ignored=False)
    if status:
        raise RuntimeError(f"{label} repository is not clean:\n{status}")
    ignored_status = (
        _git_status(resolved, include_ignored=True) if include_ignored else ""
    )
    ignored_summary, nonignored_entries = _summarize_ignored_status(ignored_status)
    if nonignored_entries:
        raise RuntimeError(
            f"{label} ignored inventory contains ordinary dirt: "
            f"{nonignored_entries[:10]}"
        )
    result = {
        "path": str(resolved),
        "commit": commit,
        "tree": tree,
        "clean": True,
        "ignored_inventory_recorded": include_ignored,
        "ignored_entry_count": ignored_summary["entry_count"],
        "ignored_status_sha256": ignored_summary["full_status_sha256"],
        "ignored_inventory_summary": ignored_summary,
    }
    return result


def _require_tracked_paths(repo: Path, relative_paths: Sequence[str]) -> None:
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "ls-files",
            "--error-unmatch",
            *relative_paths,
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def _validate_parent_and_fork(
    *,
    parent_repo: Path,
    fork_repo: Path,
    expected_parent_commit: str,
    expected_parent_tree: str,
    expected_fork_commit: str,
    expected_fork_tree: str,
) -> dict[str, Any]:
    parent = _validate_repo(
        parent_repo,
        expected_commit=expected_parent_commit,
        expected_tree=expected_parent_tree,
        include_ignored=False,
        label="parent",
    )
    fork = _validate_repo(
        fork_repo,
        expected_commit=expected_fork_commit,
        expected_tree=expected_fork_tree,
        include_ignored=True,
        label="fork",
    )
    parent_root = Path(parent["path"])
    fork_root = Path(fork["path"])
    for relative in _PARENT_RELATIVE_PATHS:
        (parent_root / relative).resolve(strict=True)
    _require_tracked_paths(parent_root, _PARENT_RELATIVE_PATHS)
    _require_tracked_paths(fork_root, _FORK_TRACKED_PATHS)
    ancestry = subprocess.run(
        [
            "git",
            "-C",
            str(fork_root),
            "merge-base",
            "--is-ancestor",
            BASE_FORK_COMMIT,
            expected_fork_commit,
        ],
        check=False,
    )
    if ancestry.returncode != 0:
        raise RuntimeError("fork target is not a descendant of the frozen base")
    parent["tracked_claim_paths"] = list(_PARENT_RELATIVE_PATHS)
    fork["tracked_claim_paths"] = list(_FORK_TRACKED_PATHS)
    fork["frozen_base_commit"] = BASE_FORK_COMMIT
    fork["descends_from_frozen_base"] = True
    return {"parent": parent, "fork": fork}


def scan_anchor_imports(path: Path = _ANCHOR_PATH) -> dict[str, Any]:
    """Verify that the exact-small anchor has no candidate dependency."""

    resolved = path.resolve(strict=True)
    tree = ast.parse(resolved.read_text(encoding="utf-8"), filename=str(resolved))
    imports: set[str] = set()
    dynamic: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
        elif isinstance(node, ast.Call):
            name = None
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            if (
                name in {"__import__", "import_module"}
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                dynamic.add(node.args[0].value)
    forbidden = sorted(
        name
        for name in imports | dynamic
        if name.split(".", 1)[0] in _FORBIDDEN_ANCHOR_IMPORT_ROOTS or ".gcapeps" in name
    )
    if forbidden:
        raise RuntimeError(f"anchor imports candidate dependencies: {forbidden}")
    return {
        "path": str(resolved),
        "sha256": _sha256_file(resolved),
        "imports": sorted(imports),
        "dynamic_literal_imports": sorted(dynamic),
        "forbidden_imports": [],
        "passed": True,
    }


def _load_module(path: Path, *, name: str) -> ModuleType:
    source = path.resolve(strict=True)
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import module from {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _validate_import_origin(
    module: ModuleType,
    *,
    fork_repo: Path,
    label: str,
) -> dict[str, str]:
    raw = getattr(module, "__file__", None)
    if not isinstance(raw, str):
        raise RuntimeError(f"{label} has no file import origin")
    lexical = Path(raw).absolute()
    resolved = lexical.resolve(strict=True)
    if lexical != resolved or not resolved.is_relative_to(fork_repo):
        raise RuntimeError(f"{label} import origin escapes the frozen fork")
    return {
        "origin": str(resolved),
        "source_sha256": _sha256_file(resolved),
    }


def _load_runtime(fork_repo: Path) -> SimpleNamespace:
    """Import Quimb only after Git and environment preconditions pass."""

    if "PYTHONPATH" in os.environ:
        raise RuntimeError("PYTHONPATH is forbidden for the formal runner")
    quimb = importlib.import_module("quimb")
    qtn = importlib.import_module("quimb.tensor")
    gcapeps = importlib.import_module("quimb.experimental.gcapeps")
    gates = importlib.import_module("quimb.tensor.circuit.gates")
    for label, module in (
        ("quimb", quimb),
        ("quimb.tensor", qtn),
        ("quimb.experimental.gcapeps", gcapeps),
        ("quimb.tensor.circuit.gates", gates),
    ):
        _validate_import_origin(module, fork_repo=fork_repo, label=label)
    return SimpleNamespace(
        quimb=quimb,
        qtn=qtn,
        gcapeps=gcapeps,
        Gate=gates.Gate,
        import_identity={
            "python_version": sys.version,
            "python_executable": str(Path(sys.executable).resolve(strict=True)),
            "numpy_version": np.__version__,
            "numpy_import_origin": str(Path(np.__file__).resolve(strict=True)),
            "numpy_import_sha256": _sha256_file(Path(np.__file__)),
            "quimb": _validate_import_origin(
                quimb,
                fork_repo=fork_repo,
                label="quimb",
            ),
            "quimb_tensor": _validate_import_origin(
                qtn,
                fork_repo=fork_repo,
                label="quimb.tensor",
            ),
            "gcapeps": _validate_import_origin(
                gcapeps,
                fork_repo=fork_repo,
                label="quimb.experimental.gcapeps",
            ),
            "gate_module": _validate_import_origin(
                gates,
                fork_repo=fork_repo,
                label="quimb.tensor.circuit.gates",
            ),
            "pythonpath_absent": True,
        },
    )


def _require_c128_array(
    value: Any,
    *,
    shape: tuple[int, ...],
    label: str,
) -> np.ndarray:
    if not isinstance(value, np.ndarray):
        raise TypeError(f"{label} must already be a NumPy array")
    if (
        value.shape != shape
        or value.dtype != _C128
        or not value.flags.c_contiguous
        or not np.all(np.isfinite(value))
    ):
        raise ValueError(
            f"{label} must be finite C-contiguous complex128 with shape {shape}"
        )
    return value


def _encode_c128(value: np.ndarray, *, label: str) -> dict[str, Any]:
    array = _require_c128_array(value, shape=value.shape, label=label)
    little = np.ascontiguousarray(array, dtype="<c16")
    return {
        "dtype": "complex128",
        "shape": [int(axis) for axis in array.shape],
        "order": "C",
        "values_real_imag": [
            [float(item.real), float(item.imag)] for item in array.reshape(-1)
        ],
        "sha256_little_endian_c_order": hashlib.sha256(
            little.tobytes(order="C")
        ).hexdigest(),
    }


def _raw_gate(runtime: SimpleNamespace, matrix: np.ndarray, sites) -> Any:
    checked = _require_c128_array(
        matrix,
        shape=matrix.shape,
        label="raw gate",
    )
    return runtime.Gate.from_raw(checked, qubits=tuple(sites))


def _build_circuit(
    runtime: SimpleNamespace,
    preparation: np.ndarray,
    *,
    max_bond: int | None,
    cutoff: float,
) -> Any:
    circuit = runtime.qtn.CircuitPEPSSimpleUpdate(
        edges=((0, 1),),
        max_bond=max_bond,
        cutoff=cutoff,
        renorm=False,
        gauge_smudge=0.0,
        equilibrate_every=None,
        gate_opts={"cutoff_mode": "rel", "method": "svd"},
        dtype="complex128",
    )
    circuit.apply_gates((_raw_gate(runtime, preparation, (0,)),))
    return circuit


def _basis_circuit(runtime: SimpleNamespace, basis_index: int) -> Any:
    identity = np.ascontiguousarray(np.eye(2, dtype=np.complex128))
    circuit = _build_circuit(
        runtime,
        identity,
        max_bond=None,
        cutoff=0.0,
    )
    x_gate = np.ascontiguousarray(
        np.asarray(((0.0, 1.0), (1.0, 0.0)), dtype=np.complex128)
    )
    for qubit in range(2):
        if basis_index & (1 << (1 - qubit)):
            circuit.apply_gates((_raw_gate(runtime, x_gate, (qubit,)),))
    return circuit


def _dense_circuit_vector(circuit: Any) -> np.ndarray:
    psi = circuit.psi
    vector = np.asarray(
        psi.to_dense(
            (psi.site_ind(0), psi.site_ind(1)),
            to_qarray=False,
            to_ket=False,
            optimize="greedy",
        )
    ).reshape(-1)
    return _require_c128_array(
        vector,
        shape=(4,),
        label="candidate complete vector",
    )


def _json_site(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, tuple):
        return [_json_site(item) for item in value]
    raise TypeError(f"site value is not JSON-safe: {value!r}")


def _rebuild_native_plan_transcript(plan: Any) -> str:
    site_order = tuple(plan.site_order)
    site_rank = {site: index for index, site in enumerate(site_order)}
    if len(site_rank) != len(site_order):
        raise ValueError("native plan site_order is not unique")

    def encoded_edge(edge):
        left, right = tuple(edge)
        return [site_rank[left], site_rank[right]]

    phase = complex(plan.pauli_phase)
    payload = {
        "schema": "quimb.experimental.gcapeps.native_plan.v1",
        "compiler_revision": str(plan.compiler_revision),
        "pauli_codes": [int(value) for value in plan.pauli_word.codes],
        "pauli_phase": [
            float(phase.real).hex(),
            float(phase.imag).hex(),
        ],
        "site_count": len(site_order),
        "graph_edges": [
            encoded_edge(edge) for edge in plan.graph_edges
        ],
        "angle_radians": float(plan.angle_radians).hex(),
        "signed_angle_radians": float(
            plan.signed_angle_radians
        ).hex(),
        "support": [int(value) for value in plan.support],
        "support_sites": [
            site_rank[site] for site in plan.support_sites
        ],
        "routing_root": site_rank[plan.routing_root],
        "routing_vertices": [
            site_rank[site] for site in plan.routing_vertices
        ],
        "routing_tree_edges": [
            encoded_edge(edge) for edge in plan.routing_tree_edges
        ],
        "steps": [
            {
                "step_index": int(step.step_index),
                "role": str(step.role),
                "gate_kind": str(step.gate_kind),
                "qubits": [int(value) for value in step.qubits],
                "sites": [site_rank[site] for site in step.sites],
                "angle_radians": (
                    None
                    if step.angle_radians is None
                    else float(step.angle_radians).hex()
                ),
                "matrix_sha256": str(step.matrix_sha256),
                "is_two_site": bool(step.is_two_site),
            }
            for step in plan.steps
        ],
        "precision_dtype": str(plan.precision_dtype),
    }
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def serialize_native_plan(plan: Any) -> dict[str, Any]:
    """Serialize a native plan field-by-field, never via ``asdict``."""

    steps = []
    for step in plan.steps:
        steps.append(
            {
                "step_index": int(step.step_index),
                "role": str(step.role),
                "gate_kind": str(step.gate_kind),
                "qubits": [int(value) for value in step.qubits],
                "sites": [_json_site(value) for value in step.sites],
                "angle_radians": (
                    None if step.angle_radians is None else float(step.angle_radians)
                ),
                "matrix_sha256": str(step.matrix_sha256),
                "is_two_site": bool(step.is_two_site),
            }
        )
    phase = complex(plan.pauli_phase)
    payload = {
        "compiler_revision": str(plan.compiler_revision),
        "pauli_word": {
            "num_qubits": int(plan.pauli_word.num_qubits),
            "codes": [int(value) for value in plan.pauli_word.codes],
            "phase_real": float(phase.real),
            "phase_imag": float(phase.imag),
            "is_hermitian": bool(plan.pauli_word.is_hermitian),
        },
        "site_order": [_json_site(value) for value in plan.site_order],
        "graph_edges": [
            [_json_site(left), _json_site(right)] for left, right in plan.graph_edges
        ],
        "angle_radians": float(plan.angle_radians),
        "signed_angle_radians": float(plan.signed_angle_radians),
        "support": [int(value) for value in plan.support],
        "support_sites": [_json_site(value) for value in plan.support_sites],
        "routing_root": _json_site(plan.routing_root),
        "routing_vertices": [_json_site(value) for value in plan.routing_vertices],
        "routing_tree_edges": [
            [_json_site(left), _json_site(right)]
            for left, right in plan.routing_tree_edges
        ],
        "steps": steps,
        "canonical_transcript": str(plan.canonical_transcript),
        "plan_digest_sha256": str(plan.plan_digest_sha256),
        "precision_dtype": str(plan.precision_dtype),
    }
    transcript = payload["canonical_transcript"]
    rebuilt_transcript = _rebuild_native_plan_transcript(plan)
    if transcript != rebuilt_transcript:
        raise ValueError(
            "native canonical transcript disagrees with plan fields"
        )
    digest = payload["plan_digest_sha256"]
    if _HEX64.fullmatch(digest) is None:
        raise ValueError("native plan digest is not lowercase SHA-256")
    if hashlib.sha256(transcript.encode("utf-8")).hexdigest() != digest:
        raise ValueError("native canonical transcript digest is inconsistent")
    try:
        transcript_payload = json.loads(transcript)
    except json.JSONDecodeError as exc:
        raise ValueError("native canonical transcript is not JSON") from exc
    if (
        json.dumps(
            transcript_payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        != transcript
    ):
        raise ValueError("native plan transcript is not canonical JSON")
    _canonical_json_bytes(payload)
    return payload


def serialize_split_record(row: Any) -> dict[str, Any]:
    payload = {
        "step_index": int(row.step_index),
        "gate_role": str(row.gate_role),
        "edge": [_json_site(value) for value in row.edge],
        "ordered_sites": [_json_site(value) for value in row.ordered_sites],
        "configured_max_bond": (
            None if row.configured_max_bond is None else int(row.configured_max_bond)
        ),
        "configured_cutoff": float(row.configured_cutoff),
        "configured_cutoff_mode": str(row.configured_cutoff_mode),
        "full_singular_values": [float(value) for value in row.full_singular_values],
        "kept_singular_values": [float(value) for value in row.kept_singular_values],
        "full_bond_dimension": int(row.full_bond_dimension),
        "kept_bond_dimension": int(row.kept_bond_dimension),
        "pre_split_weight": float(row.pre_split_weight),
        "discarded_squared_weight": float(row.discarded_squared_weight),
        "discarded_fraction": float(row.discarded_fraction),
        "keep_by_cutoff": int(row.keep_by_cutoff),
        "keep_by_cap": int(row.keep_by_cap),
        "actual_keep": int(row.actual_keep),
        "cause": str(row.cause),
        "dimension_reduced": bool(row.dimension_reduced),
        "positive_discarded_weight": bool(row.positive_discarded_weight),
        "positive_discarded_weight_threshold": float(
            row.positive_discarded_weight_threshold
        ),
        "not_a_global_error_bound": bool(row.not_a_global_error_bound),
    }
    validate_serialized_split_record(payload)
    return payload


def validate_serialized_split_record(row: Mapping[str, Any]) -> bool:
    """Independently recompute one serialized cause record."""

    if not isinstance(row, Mapping) or set(row) != _SPLIT_KEYS:
        raise ValueError("split record fields are incomplete or widened")
    full = np.asarray(row["full_singular_values"], dtype=np.float64)
    kept = np.asarray(row["kept_singular_values"], dtype=np.float64)
    if (
        full.ndim != 1
        or kept.ndim != 1
        or full.size == 0
        or kept.size == 0
        or not np.all(np.isfinite(full))
        or not np.all(np.isfinite(kept))
        or np.any(full < 0.0)
        or np.any(kept < 0.0)
        or np.any(full[1:] > full[:-1] + EXACT_BAND)
    ):
        raise ValueError("serialized singular spectrum is invalid")
    if row["full_bond_dimension"] != int(full.size):
        raise ValueError("full dimension disagrees with full spectrum")
    if row["kept_bond_dimension"] != int(kept.size):
        raise ValueError("kept dimension disagrees with kept spectrum")
    max_bond = row["configured_max_bond"]
    if max_bond is not None and (
        isinstance(max_bond, bool) or not isinstance(max_bond, int) or max_bond <= 0
    ):
        raise ValueError("configured max_bond is invalid")
    cutoff = float(row["configured_cutoff"])
    if (
        not math.isfinite(cutoff)
        or cutoff < 0.0
        or row["configured_cutoff_mode"] != "rel"
    ):
        raise ValueError("configured relative cutoff is invalid")
    if cutoff == 0.0:
        keep_cutoff = int(full.size)
    else:
        keep_cutoff = max(1, int(np.count_nonzero(full > cutoff * full[0])))
    keep_cap = int(full.size) if max_bond is None else min(int(full.size), max_bond)
    actual = min(keep_cutoff, keep_cap)
    if (
        row["keep_by_cutoff"] != keep_cutoff
        or row["keep_by_cap"] != keep_cap
        or row["actual_keep"] != actual
        or row["kept_bond_dimension"] != actual
    ):
        raise ValueError("serialized split keep counts are inconsistent")
    if not np.allclose(
        kept,
        full[:actual],
        rtol=EXACT_BAND,
        atol=EXACT_BAND,
    ):
        raise ValueError("serialized kept spectrum is not the leading prefix")
    pre_weight = float(np.sum(full**2))
    discarded = float(np.sum(full[actual:] ** 2))
    fraction = discarded / pre_weight
    expected_cause = "none"
    if actual < full.size:
        cap_reduces = keep_cap < full.size
        cutoff_reduces = keep_cutoff < full.size
        if cap_reduces and cutoff_reduces:
            expected_cause = "both"
        elif cap_reduces:
            expected_cause = "max_bond"
        elif cutoff_reduces:
            expected_cause = "cutoff"
        else:
            raise ValueError("dimension reduction lacks a cause")
    checks = (
        abs(float(row["pre_split_weight"]) - pre_weight),
        abs(float(row["discarded_squared_weight"]) - discarded),
        abs(float(row["discarded_fraction"]) - fraction),
    )
    if not math.isfinite(pre_weight) or pre_weight <= 0.0:
        raise ValueError("serialized pre-split weight is invalid")
    if any(not math.isfinite(value) or value > EXACT_BAND for value in checks):
        raise ValueError("serialized split weights are inconsistent")
    threshold = float(row["positive_discarded_weight_threshold"])
    expected_positive = discarded > threshold
    if (
        threshold != POSITIVE_TAIL_THRESHOLD
        or row["cause"] != expected_cause
        or row["dimension_reduced"] is not (actual < full.size)
        or row["positive_discarded_weight"] is not expected_positive
        or row["not_a_global_error_bound"] is not True
    ):
        raise ValueError("serialized split cause/boolean ledger is inconsistent")
    if len(row["edge"]) != 2 or len(row["ordered_sites"]) != 2:
        raise ValueError("serialized split edge arity drifted")
    return True


def serialize_native_ledger(ledger: Any) -> dict[str, Any]:
    rows = [serialize_split_record(row) for row in ledger.split_records]
    payload = {
        "compiler_revision": str(ledger.compiler_revision),
        "plan_digest_sha256": str(ledger.plan_digest_sha256),
        "plan_step_count": int(ledger.plan_step_count),
        "two_site_step_count": int(ledger.two_site_step_count),
        "split_records": rows,
        "positive_discarded_event_count": int(ledger.positive_discarded_event_count),
        "dimension_reduction_event_count": int(ledger.dimension_reduction_event_count),
        "total_discarded_squared_weight_diagnostic_only": float(
            ledger.total_discarded_squared_weight_diagnostic_only
        ),
        "any_smudging_applied": bool(ledger.any_smudging_applied),
        "not_a_global_error_bound": bool(ledger.not_a_global_error_bound),
    }
    validate_serialized_ledger(payload)
    return payload


def validate_serialized_ledger(ledger: Mapping[str, Any]) -> bool:
    if not isinstance(ledger, Mapping) or set(ledger) != _LEDGER_KEYS:
        raise ValueError("serialized ledger fields are incomplete or widened")
    digest = ledger["plan_digest_sha256"]
    if not isinstance(digest, str) or _HEX64.fullmatch(digest) is None:
        raise ValueError("serialized ledger plan digest is invalid")
    rows = ledger.get("split_records")
    if not isinstance(rows, list):
        raise ValueError("serialized ledger has no split record list")
    for row in rows:
        validate_serialized_split_record(row)
    if ledger.get("two_site_step_count") != len(rows):
        raise ValueError("serialized ledger two-site count drifted")
    if ledger.get("positive_discarded_event_count") != sum(
        bool(row["positive_discarded_weight"]) for row in rows
    ):
        raise ValueError("serialized ledger positive-event count drifted")
    if ledger.get("dimension_reduction_event_count") != sum(
        bool(row["dimension_reduced"]) for row in rows
    ):
        raise ValueError("serialized ledger reduction-event count drifted")
    total = math.fsum(float(row["discarded_squared_weight"]) for row in rows)
    if (
        abs(float(ledger.get("total_discarded_squared_weight_diagnostic_only")) - total)
        > EXACT_BAND
    ):
        raise ValueError("serialized ledger diagnostic total drifted")
    if (
        ledger.get("any_smudging_applied") is not False
        or ledger.get("not_a_global_error_bound") is not True
    ):
        raise ValueError("serialized ledger boundary drifted")
    indices = [int(row["step_index"]) for row in rows]
    if indices != sorted(indices) or len(indices) != len(set(indices)):
        raise ValueError("serialized ledger split order drifted")
    return True


def validate_native_plan_ledger_binding(
    plan: Mapping[str, Any],
    ledger: Mapping[str, Any],
) -> bool:
    validate_serialized_ledger(ledger)
    if plan["compiler_revision"] != ledger["compiler_revision"]:
        raise ValueError("native plan/ledger compiler revisions disagree")
    if plan["plan_digest_sha256"] != ledger["plan_digest_sha256"]:
        raise ValueError("native plan/ledger digests disagree")
    steps = plan.get("steps")
    if not isinstance(steps, list):
        raise ValueError("serialized native plan steps are missing")
    if ledger["plan_step_count"] != len(steps):
        raise ValueError("ledger plan_step_count disagrees with plan")
    two_site_steps = [
        step for step in steps if step.get("is_two_site") is True
    ]
    if ledger["two_site_step_count"] != len(two_site_steps):
        raise ValueError("ledger two_site_step_count disagrees with plan")
    rows = ledger["split_records"]
    if len(rows) != len(two_site_steps):
        raise ValueError("split rows do not cover every two-site plan step")
    for index, (row, step) in enumerate(zip(rows, two_site_steps)):
        if row["step_index"] != step["step_index"]:
            raise ValueError(
                f"split row {index} step_index disagrees with plan"
            )
        if row["gate_role"] != step["role"]:
            raise ValueError(
                f"split row {index} gate_role disagrees with plan"
            )
        if row["ordered_sites"] != step["sites"]:
            raise ValueError(
                f"split row {index} ordered_sites disagree with plan"
            )
    return True


def serialize_native_execution_result(result: Any) -> dict[str, Any]:
    plan = serialize_native_plan(result.plan)
    ledger = serialize_native_ledger(result.ledger)
    digest = str(result.plan_digest_sha256)
    if (
        _HEX64.fullmatch(digest) is None
        or digest != plan["plan_digest_sha256"]
        or digest != ledger["plan_digest_sha256"]
    ):
        raise ValueError("native result/plan/ledger digests disagree")
    validate_native_plan_ledger_binding(plan, ledger)
    circuit = result.circuit
    payload = {
        "plan_digest_sha256": digest,
        "plan": plan,
        "ledger": ledger,
        "circuit": {
            "type": (f"{type(circuit).__module__}.{type(circuit).__qualname__}"),
            "num_gates": int(circuit.num_gates),
            "tensor_elements_serialized": False,
        },
    }
    _canonical_json_bytes(payload)
    return payload


def _serialize_update(update: Any) -> dict[str, Any]:
    plan = (
        None
        if update.native_plan is None
        else serialize_native_plan(update.native_plan)
    )
    ledger = (
        None
        if update.native_truncation_ledger is None
        else serialize_native_ledger(update.native_truncation_ledger)
    )
    if (plan is None) is not (ledger is None):
        raise ValueError("native update plan/ledger presence disagrees")
    if (
        plan is not None
        and plan["plan_digest_sha256"] != ledger["plan_digest_sha256"]
    ):
        raise ValueError("native update plan/ledger digests disagree")
    if plan is not None:
        validate_native_plan_ledger_binding(plan, ledger)
    return {
        "operation": str(update.operation),
        "strategy": str(update.strategy),
        "support": [int(value) for value in update.support],
        "sites": [_json_site(value) for value in update.sites],
        "max_bond_before": int(update.max_bond_before),
        "max_bond_after": int(update.max_bond_after),
        "max_bond_limit": (
            None if update.max_bond_limit is None else int(update.max_bond_limit)
        ),
        "cutoff": float(update.cutoff),
        "residual_revision_before": int(update.residual_revision_before),
        "residual_revision_after": int(update.residual_revision_after),
        "truncation_applied": bool(update.truncation_applied),
        "compression_applied": bool(update.compression_applied),
        "smudging_applied": bool(update.smudging_applied),
        "precision_dtype": str(update.precision_dtype),
        "array_backend": str(update.array_backend),
        "native_plan": plan,
        "native_truncation_ledger": ledger,
        "native_plan_ledger_digest_equal": (None if plan is None else True),
    }


def _validate_metric_payload(metrics: Mapping[str, Any]) -> bool:
    if not isinstance(metrics, Mapping) or set(metrics) != _METRIC_KEYS:
        raise ValueError("metric payload fields are incomplete or widened")
    for key in _METRIC_KEYS - {
        "phase_fit_performed",
        "normalization_performed",
        "dtype_cast_performed",
        "coordinate_permutation_performed",
    }:
        value = metrics[key]
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
        ):
            raise ValueError(f"metric {key} is not a finite scalar")
    for key in (
        "phase_fit_performed",
        "normalization_performed",
        "dtype_cast_performed",
        "coordinate_permutation_performed",
    ):
        if metrics[key] is not False:
            raise ValueError(f"metric transformation firewall failed: {key}")
    if metrics["fidelity_roundoff_correction"] > EXACT_BAND:
        raise ValueError("fidelity roundoff correction exceeds the band")
    if not 0.0 <= metrics["fidelity"] <= 1.0:
        raise ValueError("clipped fidelity lies outside [0,1]")
    return True


def _metrics_match(
    observed: Mapping[str, Any],
    expected: Mapping[str, Any],
    *,
    absolute_band: float = EXACT_BAND,
) -> bool:
    _validate_metric_payload(observed)
    _validate_metric_payload(expected)
    for key in _METRIC_KEYS:
        if isinstance(expected[key], bool):
            if observed[key] is not expected[key]:
                return False
        elif abs(float(observed[key]) - float(expected[key])) > absolute_band:
            return False
    return True


def _lane(
    *,
    lane_id: str,
    role: str,
    vector: np.ndarray,
    reference: np.ndarray,
    expected_vector: np.ndarray,
    anchor: ModuleType,
    configuration: Mapping[str, Any],
    update: Any | None = None,
    direct_split: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    vector = _require_c128_array(vector, shape=(4,), label=f"{lane_id} vector")
    expected_vector = _require_c128_array(
        expected_vector,
        shape=(4,),
        label=f"{lane_id} expected vector",
    )
    metrics = anchor.evaluate_metrics(reference, vector)
    _validate_metric_payload(metrics)
    vector_error = float(np.max(np.abs(vector - expected_vector)))
    return {
        "lane_id": lane_id,
        "role": role,
        "configuration": dict(configuration),
        "complete_vector": _encode_c128(vector, label=f"{lane_id} vector"),
        "metrics_against_exact_anchor": metrics,
        "expected_vector_d_inf": vector_error,
        "expected_vector_passed": vector_error <= EXACT_BAND,
        "update": None if update is None else _serialize_update(update),
        "direct_split_diagnostic": (
            None if direct_split is None else dict(direct_split)
        ),
        "not_a_record_claim": True,
        "not_a_global_error_bound": True,
        "timed": False,
    }


def _native_lane(
    runtime: SimpleNamespace,
    anchor: ModuleType,
    *,
    lane_id: str,
    preparation: np.ndarray,
    exact: np.ndarray,
    expected: np.ndarray,
    angle: float,
    max_bond: int | None,
    cutoff: float,
) -> tuple[dict[str, Any], Any, Any]:
    circuit = _build_circuit(
        runtime,
        preparation,
        max_bond=max_bond,
        cutoff=cutoff,
    )
    carrier = runtime.gcapeps.QuimbPEPSCarrier(
        circuit,
        site_order=(0, 1),
        contraction_optimize="greedy",
        pauli_rotation_strategy="native_simple_update",
    )
    update = carrier.apply_pauli_rotation(
        runtime.gcapeps.QubitPauliWord.from_labels("ZZ"),
        angle,
    )
    vector = carrier.state_vector(max_qubits=2)
    lane = _lane(
        lane_id=lane_id,
        role="quimb_native_compiled_pauli_rotation",
        vector=vector,
        reference=exact,
        expected_vector=expected,
        anchor=anchor,
        configuration={
            "max_bond": max_bond,
            "cutoff": cutoff,
            "cutoff_mode": "rel",
            "renorm": False,
            "gauge_smudge": 0.0,
        },
        update=update,
    )
    return lane, update.native_plan, update.native_truncation_ledger


def _direct_split_diagnostic(
    *,
    full: np.ndarray,
    kept: np.ndarray,
) -> dict[str, Any]:
    full_values = tuple(float(value) for value in full)
    kept_values = tuple(float(value) for value in kept)
    actual = len(kept_values)
    pre_weight = math.fsum(value * value for value in full_values)
    discarded = math.fsum(value * value for value in full_values[actual:])
    payload = {
        "step_index": 0,
        "gate_role": "direct_literal_uzz",
        "edge": [0, 1],
        "ordered_sites": [0, 1],
        "configured_max_bond": 1,
        "configured_cutoff": 0.0,
        "configured_cutoff_mode": "rel",
        "full_singular_values": list(full_values),
        "kept_singular_values": list(kept_values),
        "full_bond_dimension": len(full_values),
        "kept_bond_dimension": actual,
        "pre_split_weight": pre_weight,
        "discarded_squared_weight": discarded,
        "discarded_fraction": discarded / pre_weight,
        "keep_by_cutoff": len(full_values),
        "keep_by_cap": min(len(full_values), 1),
        "actual_keep": min(len(full_values), 1),
        "cause": "max_bond" if len(full_values) > 1 else "none",
        "dimension_reduced": len(full_values) > 1,
        "positive_discarded_weight": discarded > POSITIVE_TAIL_THRESHOLD,
        "positive_discarded_weight_threshold": POSITIVE_TAIL_THRESHOLD,
        "not_a_global_error_bound": True,
    }
    validate_serialized_split_record(payload)
    return payload


def _run_direct_lane(
    runtime: SimpleNamespace,
    anchor: ModuleType,
    *,
    preparation: np.ndarray,
    u_zz: np.ndarray,
    exact: np.ndarray,
) -> dict[str, Any]:
    shadow = _build_circuit(
        runtime,
        preparation,
        max_bond=None,
        cutoff=0.0,
    )
    candidate = _build_circuit(
        runtime,
        preparation,
        max_bond=1,
        cutoff=0.0,
    )
    shadow.apply_gates((_raw_gate(runtime, u_zz.copy(), (0, 1)),))
    candidate.apply_gates((_raw_gate(runtime, u_zz.copy(), (0, 1)),))
    shadow_bond = shadow._psi.bond(0, 1)
    candidate_bond = candidate._psi.bond(0, 1)
    full = np.asarray(shadow.gauges[shadow_bond])
    kept = np.asarray(candidate.gauges[candidate_bond])
    if (
        full.dtype != _F64
        or kept.dtype != _F64
        or not np.all(np.isfinite(full))
        or not np.all(np.isfinite(kept))
    ):
        raise RuntimeError("D1 split gauges are not finite float64")
    diagnostic = _direct_split_diagnostic(full=full, kept=kept)
    return _lane(
        lane_id="D1",
        role="direct_literal_final_uzz_gate_control",
        vector=_dense_circuit_vector(candidate),
        reference=exact,
        expected_vector=exact,
        anchor=anchor,
        configuration={
            "max_bond": 1,
            "cutoff": 0.0,
            "cutoff_mode": "rel",
            "renorm": False,
            "gauge_smudge": 0.0,
        },
        direct_split=diagnostic,
    )


def _operator_from_plan(runtime: SimpleNamespace, plan: Any) -> np.ndarray:
    columns = []
    for basis_index in range(4):
        circuit = _basis_circuit(runtime, basis_index)
        result = runtime.gcapeps.execute_native_pauli_rotation(circuit, plan)
        result_binding = serialize_native_execution_result(result)
        if result_binding["plan_digest_sha256"] != plan.plan_digest_sha256:
            raise ValueError("basis execution result digest disagrees with plan")
        columns.append(_dense_circuit_vector(result.circuit))
    operator = np.ascontiguousarray(np.column_stack(columns))
    return _require_c128_array(
        operator,
        shape=(4, 4),
        label="native full-basis operator",
    )


def _operator_evidence(
    runtime: SimpleNamespace,
    plan: Any,
    expected_operator: np.ndarray,
) -> dict[str, Any]:
    observed = _operator_from_plan(runtime, plan)
    difference = observed - expected_operator
    per_column = [float(np.max(np.abs(difference[:, index]))) for index in range(4)]
    return {
        "all_four_columns_checked": True,
        "candidate_operator": _encode_c128(
            observed,
            label="native full-basis operator",
        ),
        "per_column_d_inf": per_column,
        "all_column_d_inf": max(per_column),
        "frobenius_error": float(np.linalg.norm(difference)),
        "passed": max(per_column) <= EXACT_BAND,
    }


def _positive_rows(ledger: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [row for row in ledger["split_records"] if row["positive_discarded_weight"]]


def _validate_expected_cause(
    ledger: Mapping[str, Any],
    *,
    expected_cause: str | None,
    expected_positive: bool,
) -> bool:
    validate_serialized_ledger(ledger)
    rows = _positive_rows(ledger)
    if expected_positive:
        if expected_cause is None:
            raise ValueError("a positive lane requires an expected cause")
        if len(rows) != 1 or rows[0]["cause"] != expected_cause:
            raise ValueError("required positive split cause was not observed")
    elif rows:
        raise ValueError("a no-loss lane discarded positive weight")
    return True


def _validate_lanes(
    lanes: Mapping[str, Mapping[str, Any]],
    *,
    anchor_payload: Mapping[str, Any],
) -> dict[str, Any]:
    if tuple(lanes) != LANE_ORDER:
        raise ValueError("lane set or order drifted")
    predictions = anchor_payload["exact_predictions"]
    expected_metrics = {
        "A": predictions["exact_self"],
        "T": predictions["exact_self"],
        "N0": predictions["exact_self"],
        "N1": predictions["cap_only"],
        "N2": predictions["exact_self"],
        "D1": predictions["direct_final_gate_control"],
        "K0": predictions["cutoff_inert"],
        "K1": predictions["cutoff_only"],
    }
    metric_rows = {}
    for lane_id, lane in lanes.items():
        observed = lane["metrics_against_exact_anchor"]
        passed = lane["expected_vector_passed"] is True and _metrics_match(
            observed, expected_metrics[lane_id]
        )
        metric_rows[lane_id] = {
            "metrics_match_registered_prediction": passed,
            "expected_vector_d_inf": lane["expected_vector_d_inf"],
        }
        if not passed:
            raise ValueError(f"lane {lane_id} missed its registered prediction")
    native_ledgers = {
        lane_id: lanes[lane_id]["update"]["native_truncation_ledger"]
        for lane_id in ("N0", "N1", "N2", "K0", "K1")
    }
    _validate_expected_cause(
        native_ledgers["N0"],
        expected_cause=None,
        expected_positive=False,
    )
    _validate_expected_cause(
        native_ledgers["N1"],
        expected_cause="max_bond",
        expected_positive=True,
    )
    _validate_expected_cause(
        native_ledgers["N2"],
        expected_cause=None,
        expected_positive=False,
    )
    _validate_expected_cause(
        native_ledgers["K0"],
        expected_cause=None,
        expected_positive=False,
    )
    _validate_expected_cause(
        native_ledgers["K1"],
        expected_cause="cutoff",
        expected_positive=True,
    )
    target_row = _positive_rows(native_ledgers["N1"])[0]
    spectrum = anchor_payload["first_cx_spectrum"]
    if any(
        abs(left - right) > EXACT_BAND
        for left, right in zip(
            target_row["full_singular_values"],
            spectrum["analytic_singular_values"],
        )
    ):
        raise ValueError("N1 positive split spectrum missed the anchor")
    if (
        abs(
            target_row["discarded_squared_weight"]
            - spectrum["discarded_squared_weight"]
        )
        > EXACT_BAND
    ):
        raise ValueError("N1 positive discarded weight missed the anchor")
    direct = lanes["D1"]["direct_split_diagnostic"]
    validate_serialized_split_record(direct)
    if direct["positive_discarded_weight"]:
        raise ValueError("D1 unexpectedly discarded positive weight")
    if (
        lanes["N1"]["complete_vector"]["sha256_little_endian_c_order"]
        != lanes["K1"]["complete_vector"]["sha256_little_endian_c_order"]
    ):
        raise ValueError("N1 and K1 did not reach the predicted equal vector")
    if anchor_payload["final_exact_spectrum"]["fits_bond_one"] is not True:
        raise ValueError("independent final exact state does not fit bond one")
    return {
        "lane_metric_rows": metric_rows,
        "N1_positive_split": target_row,
        "N1_and_K1_equal_output_but_distinct_cause": True,
        "D1_no_positive_loss": True,
        "final_exact_physical_rank": anchor_payload["final_exact_spectrum"][
            "physical_rank_at_absolute_1e_12"
        ],
        "all_lane_gates_passed": True,
    }


def _expect_failure(callback, *, label: str) -> dict[str, Any]:
    try:
        callback()
    except Exception as exc:
        return {
            "label": label,
            "fired": True,
            "exception_type": type(exc).__name__,
            "message": str(exc),
        }
    raise RuntimeError(f"required corruption control was inert: {label}")


def _operator_corruption_control(
    runtime: SimpleNamespace,
    *,
    label: str,
    build_corrupt_plan,
    expected_operator: np.ndarray,
) -> dict[str, Any]:
    try:
        corrupt_plan = build_corrupt_plan()
        observed = _operator_from_plan(runtime, corrupt_plan)
    except Exception as exc:
        return {
            "label": label,
            "fired": True,
            "mechanism": "canonical_plan_or_executor_rejected_corruption",
            "exception_type": type(exc).__name__,
            "message": str(exc),
        }
    d_inf = float(np.max(np.abs(observed - expected_operator)))
    if d_inf <= EXACT_BAND:
        raise RuntimeError(f"required operator corruption was inert: {label}")
    return {
        "label": label,
        "fired": True,
        "mechanism": "full_basis_operator_mismatch",
        "operator_d_inf": d_inf,
    }


def _run_corruption_controls(
    runtime: SimpleNamespace,
    anchor: ModuleType,
    *,
    plan: Any,
    exact: np.ndarray,
    cap_vector: np.ndarray,
    expected_operator: np.ndarray,
    n0_ledger: Mapping[str, Any],
    n1_ledger: Mapping[str, Any],
    k1_ledger: Mapping[str, Any],
) -> dict[str, Any]:
    rows = []
    root_step_index = next(
        index for index, step in enumerate(plan.steps) if step.role == "root_rotation"
    )
    wrong_steps = list(plan.steps)
    wrong_steps[root_step_index] = replace(
        wrong_steps[root_step_index],
        qubits=(0,),
        sites=(0,),
    )
    rows.append(
        _operator_corruption_control(
            runtime,
            label="RZ_on_wrong_site",
            build_corrupt_plan=lambda: replace(
                plan,
                steps=tuple(wrong_steps),
            ),
            expected_operator=expected_operator,
        )
    )

    rows.append(
        _operator_corruption_control(
            runtime,
            label="flipped_signed_angle",
            build_corrupt_plan=lambda: runtime.gcapeps.compile_native_pauli_rotation(
                plan.pauli_word,
                -float(plan.angle_radians),
                site_order=(0, 1),
                graph_edges=((0, 1),),
            ),
            expected_operator=expected_operator,
        )
    )

    rows.append(
        _operator_corruption_control(
            runtime,
            label="omitted_final_CNOT",
            build_corrupt_plan=lambda: replace(
                plan,
                steps=tuple(plan.steps[:-1]),
            ),
            expected_operator=expected_operator,
        )
    )

    rows.append(
        _expect_failure(
            lambda: _validate_expected_cause(
                k1_ledger,
                expected_cause="max_bond",
                expected_positive=True,
            ),
            label="cutoff_lane_mislabeled_as_cap_only",
        )
    )
    rows.append(
        _expect_failure(
            lambda: _validate_expected_cause(
                n0_ledger,
                expected_cause="max_bond",
                expected_positive=True,
            ),
            label="lossless_lane_claimed_positive_cap_loss",
        )
    )
    corrupt_spectrum = copy.deepcopy(n1_ledger)
    positive_index = next(
        index
        for index, row in enumerate(corrupt_spectrum["split_records"])
        if row["positive_discarded_weight"]
    )
    corrupt_spectrum["split_records"][positive_index]["full_singular_values"][-1] *= 0.9
    rows.append(
        _expect_failure(
            lambda: validate_serialized_ledger(corrupt_spectrum),
            label="altered_full_spectrum_without_weight_recomputation",
        )
    )

    global_phase = np.complex128(np.exp(0.37j)) * exact
    global_phase = np.ascontiguousarray(global_phase, dtype=np.complex128)
    phase_metrics = anchor.evaluate_metrics(exact, global_phase)
    if (
        abs(phase_metrics["fidelity"] - 1.0) > EXACT_BAND
        or phase_metrics["d_2"] <= EXACT_BAND
    ):
        raise RuntimeError("global-phase metric discrimination was inert")
    rows.append(
        {
            "label": "global_phase_fidelity_blind_raw_vector_sensitive",
            "fired": True,
        }
    )
    rows.append(
        _expect_failure(
            lambda: _require_c128_array(
                np.asarray(exact, dtype=np.complex64),
                shape=(4,),
                label="corrupted vector",
            ),
            label="complex64_candidate",
        )
    )
    shared = exact.copy()
    shared[0] += np.complex128(0.01)
    pairwise = float(np.linalg.norm(shared - shared))
    if pairwise != 0.0:
        raise RuntimeError("shared-corruption control setup failed")
    shared_metrics = anchor.evaluate_metrics(exact, shared)
    if shared_metrics["d_2"] <= EXACT_BAND:
        raise RuntimeError("independent-anchor shared corruption was inert")
    rows.append(
        {
            "label": "shared_tree_native_corruption",
            "fired": True,
            "pairwise_d2": pairwise,
            "anchor_d2": shared_metrics["d_2"],
        }
    )
    wrong_kept = cap_vector.copy()
    wrong_kept[0] *= np.complex128(0.5)
    wrong_kept = np.ascontiguousarray(wrong_kept)
    if anchor.evaluate_metrics(exact, wrong_kept)["d_2"] <= EXACT_BAND:
        raise RuntimeError("leading-vector corruption was inert")
    rows.append({"label": "wrong_leading_component", "fired": True})

    if len(rows) != 10 or not all(row["fired"] for row in rows):
        raise RuntimeError("corruption-control family is incomplete")
    return {
        "rows": rows,
        "all_controls_fired": True,
        "router_semantics_control": {
            "scope": "required_preexecution_fork_test",
            "test": (
                "tests/test_experimental/test_gcapeps_native.py::"
                "test_remote_signed_rotation_uses_graph_edges_and_"
                "restores_router_sites"
            ),
            "runtime_reexecuted_here": False,
        },
    }


def run_formal_experiment(
    *,
    runtime: SimpleNamespace,
    anchor: ModuleType,
    anchor_payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Execute the frozen formal target. Unit tests must never call this."""

    anchor.validate_anchor_payload(anchor_payload)
    arrays = anchor_payload["arrays"]
    preparation = anchor.decode_complex_array(
        arrays["preparation_gate"],
        label="formal preparation gate",
    )
    exact = anchor.decode_complex_array(
        arrays["exact_vector"],
        label="formal exact vector",
    )
    capped = anchor.decode_complex_array(
        arrays["cap_only_lossy_vector"],
        label="formal capped vector",
    )
    u_zz = anchor.decode_complex_array(
        arrays["u_zz_operator"],
        label="formal U_ZZ",
    )
    theta = float(anchor_payload["fixture"]["theta"])
    lanes: dict[str, dict[str, Any]] = {}
    lanes["A"] = _lane(
        lane_id="A",
        role="numpy_only_independent_dense_anchor",
        vector=exact.copy(),
        reference=exact,
        expected_vector=exact,
        anchor=anchor,
        configuration={"candidate_executed": False, "timed": False},
    )

    tree_circuit = _build_circuit(
        runtime,
        preparation,
        max_bond=None,
        cutoff=0.0,
    )
    tree_carrier = runtime.gcapeps.QuimbPEPSCarrier(
        tree_circuit,
        site_order=(0, 1),
        contraction_optimize="greedy",
        pauli_rotation_strategy="exact_tree",
    )
    tree_update = tree_carrier.apply_pauli_rotation(
        runtime.gcapeps.QubitPauliWord.from_labels("ZZ"),
        theta,
    )
    lanes["T"] = _lane(
        lane_id="T",
        role="exact_tree_pepo",
        vector=tree_carrier.state_vector(max_qubits=2),
        reference=exact,
        expected_vector=exact,
        anchor=anchor,
        configuration={
            "max_bond": None,
            "cutoff": 0.0,
            "compression": False,
            "truncation": False,
        },
        update=tree_update,
    )

    lanes["N0"], plan, n0 = _native_lane(
        runtime,
        anchor,
        lane_id="N0",
        preparation=preparation,
        exact=exact,
        expected=exact,
        angle=theta,
        max_bond=None,
        cutoff=0.0,
    )
    lanes["N1"], n1_plan, n1 = _native_lane(
        runtime,
        anchor,
        lane_id="N1",
        preparation=preparation,
        exact=exact,
        expected=capped,
        angle=theta,
        max_bond=1,
        cutoff=0.0,
    )
    lanes["N2"], n2_plan, n2 = _native_lane(
        runtime,
        anchor,
        lane_id="N2",
        preparation=preparation,
        exact=exact,
        expected=exact,
        angle=theta,
        max_bond=2,
        cutoff=0.0,
    )
    if plan != n1_plan or plan != n2_plan:
        raise RuntimeError("native plan changed across cap-only controls")
    lanes["D1"] = _run_direct_lane(
        runtime,
        anchor,
        preparation=preparation,
        u_zz=u_zz,
        exact=exact,
    )
    lanes["K0"], k0_plan, k0 = _native_lane(
        runtime,
        anchor,
        lane_id="K0",
        preparation=preparation,
        exact=exact,
        expected=exact,
        angle=theta,
        max_bond=None,
        cutoff=float(anchor_payload["cutoff_controls"]["K0"]["relative_cutoff"]),
    )
    lanes["K1"], k1_plan, k1 = _native_lane(
        runtime,
        anchor,
        lane_id="K1",
        preparation=preparation,
        exact=exact,
        expected=capped,
        angle=theta,
        max_bond=None,
        cutoff=float(anchor_payload["cutoff_controls"]["K1"]["relative_cutoff"]),
    )
    if plan != k0_plan or plan != k1_plan:
        raise RuntimeError("native plan changed across cutoff controls")
    operator = _operator_evidence(runtime, plan, u_zz)
    if not operator["passed"]:
        raise RuntimeError("N0 full-basis native operator identity failed")
    validation = _validate_lanes(lanes, anchor_payload=anchor_payload)
    controls = _run_corruption_controls(
        runtime,
        anchor,
        plan=plan,
        exact=exact,
        cap_vector=capped,
        expected_operator=u_zz,
        n0_ledger=serialize_native_ledger(n0),
        n1_ledger=serialize_native_ledger(n1),
        k1_ledger=serialize_native_ledger(k1),
    )
    if not controls["all_controls_fired"]:
        raise RuntimeError("a required corruption control was inert")
    return {
        "lanes": lanes,
        "native_full_operator_identity": operator,
        "validation": validation,
        "corruption_controls": controls,
        "verdict": "PASS_BOUNDED_BRIDGE_TRANSIENT_TRUNCATION",
        "allowed_conclusion_only": (
            "On the frozen two-site bridge, untruncated Quimb-native "
            "compilation agrees with exact tree-PEPO state action, while "
            "per-gate max_bond=1 discards a nonzero transient Schmidt "
            "component and produces the preregistered complete-state error "
            "even though the final exact state fits bond one."
        ),
        "forbidden_promotions": [
            "generic_PEPS_truncation_faithfulness",
            "global_a_posteriori_error_certificate",
            "loopy_local_tail_equals_whole_state_error",
            "accumulated_round_or_Record_correctness",
            "runtime_memory_or_scaling_advantage",
            "qutrit_SDIM_or_leakage_conclusion",
        ],
    }


def _source_identity(parent_repo: Path, fork_repo: Path) -> dict[str, Any]:
    parent_paths = {
        relative: parent_repo / relative for relative in _PARENT_RELATIVE_PATHS
    }
    fork_paths = {relative: fork_repo / relative for relative in _FORK_TRACKED_PATHS}
    return {
        "parent": {name: _sha256_file(path) for name, path in parent_paths.items()},
        "fork": {name: _sha256_file(path) for name, path in fork_paths.items()},
    }


def _claim_bearing_repo_identity(
    identities: Mapping[str, Any],
) -> dict[str, Any]:
    result = {}
    for label in ("parent", "fork"):
        identity = identities[label]
        fields = {
            "path": identity["path"],
            "commit": identity["commit"],
            "tree": identity["tree"],
            "clean": identity["clean"],
            "tracked_claim_paths": identity["tracked_claim_paths"],
        }
        if label == "fork":
            fields["frozen_base_commit"] = identity["frozen_base_commit"]
            fields["descends_from_frozen_base"] = identity[
                "descends_from_frozen_base"
            ]
        result[label] = fields
    return result


def _post_execution_revalidate(
    *,
    parent: Path,
    fork: Path,
    expected_parent_commit: str,
    expected_parent_tree: str,
    expected_fork_commit: str,
    expected_fork_tree: str,
    pre_repositories: Mapping[str, Any],
    pre_source_sha256: Mapping[str, Any],
    pre_import_identity: Mapping[str, Any],
) -> dict[str, Any]:
    post_source_sha256 = _source_identity(parent, fork)
    post_repositories = _validate_parent_and_fork(
        parent_repo=parent,
        fork_repo=fork,
        expected_parent_commit=expected_parent_commit,
        expected_parent_tree=expected_parent_tree,
        expected_fork_commit=expected_fork_commit,
        expected_fork_tree=expected_fork_tree,
    )
    post_runtime = _load_runtime(fork)
    pre_claim_identity = _claim_bearing_repo_identity(pre_repositories)
    post_claim_identity = _claim_bearing_repo_identity(post_repositories)
    if post_claim_identity != pre_claim_identity:
        raise RuntimeError(
            "claim-bearing repository identity changed during experiment"
        )
    if post_source_sha256 != pre_source_sha256:
        raise RuntimeError("claim-bearing source hashes changed during experiment")
    if post_runtime.import_identity != pre_import_identity:
        raise RuntimeError("scientific import identity changed during experiment")
    return {
        "post_repositories": post_repositories,
        "post_source_sha256": post_source_sha256,
        "post_import_identity": post_runtime.import_identity,
        "claim_bearing_repository_identity_equal": True,
        "source_sha256_equal": True,
        "import_identity_equal": True,
        "ignored_inventory_equality_required": False,
        "checkpoint_boundary": (
            "post_experiment_before_report_construction_and_publication"
        ),
        "continuous_immutability_claimed": False,
    }


def _validate_output_path(path: Path) -> Path:
    if not path.is_absolute():
        raise ValueError("--output must be an absolute path under /tmp")
    lexical = path.absolute()
    parent = lexical.parent.resolve(strict=True)
    resolved_candidate = parent / lexical.name
    if not resolved_candidate.is_relative_to(Path("/tmp")):
        raise ValueError("--output must be under /tmp")
    if lexical.exists() or lexical.is_symlink():
        raise FileExistsError("--output must name a fresh path")
    if lexical.name in {"", ".", ".."}:
        raise ValueError("--output filename is invalid")
    return resolved_candidate


def _atomic_write_new(path: Path, payload: Mapping[str, Any]) -> None:
    target = _validate_output_path(path)
    data = _canonical_json_bytes(payload)
    descriptor, raw_stage = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".stage",
        dir=str(target.parent),
    )
    stage = Path(raw_stage)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(stage, target)
        directory_fd = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        try:
            stage.unlink()
        except FileNotFoundError:
            pass


def build_formal_report(
    *,
    parent_repo: Path,
    fork_repo: Path,
    expected_parent_commit: str,
    expected_parent_tree: str,
    expected_fork_commit: str,
    expected_fork_tree: str,
) -> dict[str, Any]:
    """Validate provenance, then and only then execute the formal target."""

    identities = _validate_parent_and_fork(
        parent_repo=parent_repo,
        fork_repo=fork_repo,
        expected_parent_commit=expected_parent_commit,
        expected_parent_tree=expected_parent_tree,
        expected_fork_commit=expected_fork_commit,
        expected_fork_tree=expected_fork_tree,
    )
    if "PYTHONPATH" in os.environ:
        raise RuntimeError("PYTHONPATH is forbidden for the formal runner")
    parent = Path(identities["parent"]["path"])
    fork = Path(identities["fork"]["path"])
    pre_source_sha256 = _source_identity(parent, fork)
    anchor_boundary = scan_anchor_imports(
        parent / _ANCHOR_PATH.relative_to(_REPO_ROOT)
    )
    anchor = _load_module(
        parent / _ANCHOR_PATH.relative_to(_REPO_ROOT),
        name="_gcapeps_forced_truncation_dense_anchor_runtime",
    )
    anchor_payload = anchor.build_anchor_payload()
    anchor.validate_anchor_payload(anchor_payload)
    runtime = _load_runtime(fork)
    pre_import_identity = copy.deepcopy(runtime.import_identity)
    experiment = run_formal_experiment(
        runtime=runtime,
        anchor=anchor,
        anchor_payload=anchor_payload,
    )
    post_execution_revalidation = _post_execution_revalidate(
        parent=parent,
        fork=fork,
        expected_parent_commit=expected_parent_commit,
        expected_parent_tree=expected_parent_tree,
        expected_fork_commit=expected_fork_commit,
        expected_fork_tree=expected_fork_tree,
        pre_repositories=identities,
        pre_source_sha256=pre_source_sha256,
        pre_import_identity=pre_import_identity,
    )
    report: dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "experiment": experiment,
        "anchor": {
            "schema": anchor_payload["schema"],
            "payload_sha256": _canonical_sha256(anchor_payload),
            "source_boundary": anchor_boundary,
            "candidate_or_target_executed_by_anchor": False,
            "enters_timing_or_rss": False,
        },
        "provenance": {
            "repositories": identities,
            "imports": pre_import_identity,
            "source_sha256": pre_source_sha256,
            "post_execution_revalidation": post_execution_revalidation,
            "preregistration": str(_PREREG_PATH.relative_to(_REPO_ROOT)),
            "closure": str(_CLOSURE_PATH.relative_to(_REPO_ROOT)),
            "state_gate_dtype": "complex128",
            "singular_value_dtype": "float64",
            "no_timing_collected": True,
            "output_is_not_a_canonical_carrier_or_Record": True,
        },
        "content_sha256": None,
    }
    report["content_sha256"] = _canonical_sha256(
        {key: value for key, value in report.items() if key != "content_sha256"}
    )
    return report


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the committed, held-out GCAPEPS bridge forced-truncation "
            "experiment and atomically publish canonical JSON under /tmp."
        ),
        epilog=(
            "Preconditions: both ordinary worktrees clean; fork ignored "
            "runtime inventory recorded; "
            "both exact commit/tree identities supplied, PYTHONPATH absent, "
            "and Quimb imported from the supplied fork."
        ),
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--parent-repo", type=Path, required=True)
    parser.add_argument("--fork-repo", type=Path, required=True)
    parser.add_argument("--expected-parent-commit", required=True)
    parser.add_argument("--expected-parent-tree", required=True)
    parser.add_argument("--expected-fork-commit", required=True)
    parser.add_argument("--expected-fork-tree", required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parse_args(argv)
    output = _validate_output_path(arguments.output)
    report = build_formal_report(
        parent_repo=arguments.parent_repo,
        fork_repo=arguments.fork_repo,
        expected_parent_commit=arguments.expected_parent_commit,
        expected_parent_tree=arguments.expected_parent_tree,
        expected_fork_commit=arguments.expected_fork_commit,
        expected_fork_tree=arguments.expected_fork_tree,
    )
    _atomic_write_new(output, report)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
