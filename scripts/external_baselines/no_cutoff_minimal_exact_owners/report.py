#!/usr/bin/env python3
"""Build the fail-closed qualification report for the three exact micro-owners.

This runner qualifies only the frozen microfixtures.  It cannot populate the
historical d=3/5 census, certify a complete Record law, or authorize solver
code.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import replace
from fractions import Fraction
import hashlib
import importlib.metadata
import importlib.util
import inspect
from itertools import product
import json
import math
import os
from pathlib import Path
import platform
import re
import stat
import subprocess
import sys
import tempfile
from typing import Any, Mapping

from . import add as add_module
from . import pair as pair_module
from .add import (
    build_total_function_from_fixture_clauses,
    run_dynamic_add_owner,
    snapshot_add_state,
)
from .independent_sympy_oracle import run_independent_sympy_pair_add_oracle
from .independent_tn_oracle import (
    run_independent_tn_oracle,
    verify_frozen_subset_proof,
)
from .model import (
    ONE,
    ZERO,
    Codec,
    PairKey,
    Qsqrt2i,
    canonical_json_bytes,
    frozen_fixture_keys,
    frozen_pair_add_program,
    sha256_json,
)
from .pair import run_pair_owner
from .tn import (
    Factor,
    Index,
    frozen_tn_graph,
    replay_order,
    run_retained_boundary_tn_owner,
)


REPORT_SCHEMA = (
    "error_coupling_simulator.external."
    "no_cutoff_minimal_exact_owner_qualification.v1"
)
PUBLICATION_RECEIPT_SCHEMA = (
    "error_coupling_simulator.external."
    "no_cutoff_minimal_exact_owner_publication_receipt.v1"
)
REPORT_STATUS = "VALID_MINIMAL_EXACT_OWNER_QUALIFICATION_CODE_BLOCKED"
ACTIVE_PREREG_SHA256 = (
    "b87ddb87b27c13d82b97009ab20b41c8a41aea1aad73d3c73c89c40011611f78"
)
REVIEWED_PREACTIVATION_SHA256 = (
    "1b34446e58b763627cc3a028765839b66cd564995bea8f19beeddb4194cc55de"
)
LIBRARY_MATCH_SHA256 = (
    "01bf0fdccf80af69d244aac3e6b2adb883093348637403b26c62ca94241b24a2"
)
HISTORICAL_CENSUS_REPORT_SHA256 = (
    "88e6175dc3b7d1474c155f06cf1857484a96a8d3f6754a5e91b4c66a5292918b"
)

REPO = Path(__file__).resolve().parents[3]
PREREG_RELATIVE = (
    "docs/simulator_validation/"
    "NO_CUTOFF_MINIMAL_EXACT_OWNERS_PREREG_2026-08-03.md"
)
LIBRARY_MATCH_RELATIVE = (
    "docs/simulator_validation/NO_CUTOFF_LIBRARY_TO_METRIC_MATCH_2026-08-03.md"
)
HISTORICAL_CENSUS_RELATIVE = (
    "outputs/external_baselines/no_cutoff_structure_census_20260803/report_v3.json"
)

SOURCE_FILES = (
    "scripts/external_baselines/no_cutoff_minimal_exact_owners/__init__.py",
    "scripts/external_baselines/no_cutoff_minimal_exact_owners/model.py",
    "scripts/external_baselines/no_cutoff_minimal_exact_owners/pair.py",
    "scripts/external_baselines/no_cutoff_minimal_exact_owners/add.py",
    "scripts/external_baselines/no_cutoff_minimal_exact_owners/tn.py",
    (
        "scripts/external_baselines/no_cutoff_minimal_exact_owners/"
        "independent_sympy_oracle.py"
    ),
    (
        "scripts/external_baselines/no_cutoff_minimal_exact_owners/"
        "independent_tn_oracle.py"
    ),
    "scripts/external_baselines/no_cutoff_minimal_exact_owners/report.py",
)
TEST_FILES = (
    "tests/test_external_no_cutoff_minimal_exact_pair_owner.py",
    "tests/test_external_no_cutoff_dynamic_add_micro_owner.py",
    "tests/test_external_no_cutoff_retained_boundary_tn_micro_owner.py",
    "tests/test_external_no_cutoff_independent_sympy_oracle.py",
    "tests/test_external_no_cutoff_independent_tn_oracle.py",
    "tests/test_external_no_cutoff_minimal_exact_owners_report.py",
)
QUALIFICATION_TEST_FILES = TEST_FILES[:-1]
REPORT_INTEGRATION_TEST_FILE = TEST_FILES[-1]

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_CONTROL_KEYS = {
    "add_ast_direct_root_guard",
    "add_every_code_independent_oracle",
    "add_gc_tiny_terminal",
    "add_pair_frontier_poisoned",
    "add_relation_row_order_invariant",
    "add_wrong_variable_order",
    "pair_changed_weight_rejected",
    "pair_codec_reorder_rejected",
    "pair_exact_cancellation",
    "pair_float_rejected",
    "pair_left_right_codec_witnesses",
    "pair_noncanonical_rational_rejected",
    "pair_nonpositive_denominator_rejected",
    "pair_row_order_invariant",
    "pair_sub_1e_minus_12_tail_survives",
    "pair_duplicate_codec_rejected",
    "tn_boundary_elimination_rejected",
    "tn_c0_domain_raised",
    "tn_d1_domain_lowered",
    "tn_exhaustive_optima",
    "tn_fixed_output_ineligible",
    "tn_missing_keep_rejected",
    "tn_incomplete_order_rejected",
    "tn_invalid_domain_rejected",
    "tn_remove_edge_d0_d1",
    "tn_remove_edge_d1_d2",
    "tn_tampered_dp_cell_rejected",
    "tn_unknown_index_rejected",
}
_TOP_LEVEL_KEYS = {
    "_schema",
    "certification_verdict",
    "content_sha256",
    "corruption_controls",
    "delta_tv_cert",
    "dynamic_add_micro_owner",
    "faithfulness_disposition",
    "fixture_identities",
    "historical_census_firewall",
    "independent_oracle_receipts",
    "library_to_metric_match",
    "owner_results",
    "pair_micro_owner",
    "preregistration",
    "provenance",
    "report_status",
    "retained_boundary_tn_micro_owner",
    "route_disposition",
    "scope",
    "solver_permission",
    "target_d3_d5_metrics",
    "target_dynamic_add_owner",
    "target_pair_owner",
    "target_retained_boundary_tn_owner",
}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _file_manifest(relative_paths: tuple[str, ...]) -> dict[str, str]:
    manifest: dict[str, str] = {}
    for relative in relative_paths:
        path = REPO / relative
        if not path.is_file():
            raise FileNotFoundError(f"required qualification file is missing: {relative}")
        manifest[relative] = _sha256_file(path)
    return manifest


def _require_sha256(value: object, *, name: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ValueError(f"{name} is not a lowercase SHA-256")
    return value


def _reject_floats(value: object, *, path: str = "report") -> None:
    if isinstance(value, float):
        raise TypeError(f"floating value is forbidden at {path}")
    if isinstance(value, dict):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise TypeError(f"non-string JSON key at {path}")
            _reject_floats(nested, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _reject_floats(nested, path=f"{path}[{index}]")


def _validate_exact_scalar(value: object) -> None:
    if not isinstance(value, list) or len(value) != 4:
        raise ValueError("exact scalar must contain four rationals")
    for rational in value:
        if not isinstance(rational, list) or len(rational) != 2:
            raise ValueError("exact scalar rational must be [numerator,denominator]")
        numerator, denominator = rational
        if type(numerator) is not int or type(denominator) is not int:
            raise TypeError("exact scalar rational components must be integers")
        if denominator <= 0:
            raise ValueError("exact scalar denominator must be positive")
        if math.gcd(numerator, denominator) != 1:
            raise ValueError("exact scalar rational must be reduced")
        if numerator == 0 and denominator != 1:
            raise ValueError("exact zero rational has a noncanonical spelling")


def _walk_and_validate_scalars(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in {"coefficient", "tail", "deleted_zero", "delta"}:
                _validate_exact_scalar(nested)
            elif key == "value" and isinstance(nested, list) and len(nested) == 4:
                _validate_exact_scalar(nested)
            _walk_and_validate_scalars(nested)
    elif isinstance(value, list):
        for nested in value:
            _walk_and_validate_scalars(nested)


def _qualified_test_execution(
    source_sha256: Mapping[str, str], test_sha256: Mapping[str, str]
) -> dict[str, object]:
    identity = sha256_json(
        {
            "source_sha256": dict(source_sha256),
            "test_sha256": {
                path: test_sha256[path] for path in QUALIFICATION_TEST_FILES
            },
            "python_executable": str(Path(sys.executable).resolve()),
            "pytest_version": importlib.metadata.version("pytest"),
        }
    )
    cache = getattr(_qualified_test_execution, "_cache", {})
    if identity in cache:
        return dict(cache[identity])

    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        *QUALIFICATION_TEST_FILES,
    ]
    environment = os.environ.copy()
    environment.pop("PYTEST_ADDOPTS", None)
    completed = subprocess.run(
        command,
        cwd=REPO,
        env=environment,
        capture_output=True,
        check=False,
        text=True,
        timeout=120,
    )
    combined = completed.stdout + "\n" + completed.stderr
    match = re.search(r"(?m)^(\d+) passed(?:, .*?)? in ", combined)
    if completed.returncode != 0 or match is None:
        tail = combined[-4000:]
        raise RuntimeError(
            "fresh-process minimal-owner qualification tests failed:\n" + tail
        )
    body: dict[str, object] = {
        "command": ["python", "-m", "pytest", "-q", *QUALIFICATION_TEST_FILES],
        "input_identity_sha256": identity,
        "passed_count": int(match.group(1)),
        "return_code": completed.returncode,
        "status": "PASS",
        "test_files": list(QUALIFICATION_TEST_FILES),
    }
    body["receipt_sha256"] = sha256_json(body)
    cache[identity] = dict(body)
    setattr(_qualified_test_execution, "_cache", cache)
    return body


def _report_integration_test_execution(
    source_sha256: Mapping[str, str], test_sha256: Mapping[str, str]
) -> dict[str, object]:
    identity = sha256_json(
        {
            "report_test_sha256": test_sha256[REPORT_INTEGRATION_TEST_FILE],
            "source_sha256": dict(source_sha256),
            "python_executable": str(Path(sys.executable).resolve()),
            "pytest_version": importlib.metadata.version("pytest"),
        }
    )
    cache = getattr(_report_integration_test_execution, "_cache", {})
    if identity in cache:
        return dict(cache[identity])
    command = [sys.executable, "-m", "pytest", "-q", REPORT_INTEGRATION_TEST_FILE]
    environment = os.environ.copy()
    environment.pop("PYTEST_ADDOPTS", None)
    completed = subprocess.run(
        command,
        cwd=REPO,
        env=environment,
        capture_output=True,
        check=False,
        text=True,
        timeout=180,
    )
    combined = completed.stdout + "\n" + completed.stderr
    match = re.search(r"(?m)^(\d+) passed(?:, .*?)? in ", combined)
    if completed.returncode != 0 or match is None or int(match.group(1)) != 7:
        raise RuntimeError(
            "fresh-process report integration tests failed:\n" + combined[-4000:]
        )
    body: dict[str, object] = {
        "command": ["python", "-m", "pytest", "-q", REPORT_INTEGRATION_TEST_FILE],
        "input_identity_sha256": identity,
        "passed_count": 7,
        "return_code": completed.returncode,
        "status": "PASS",
        "test_file": REPORT_INTEGRATION_TEST_FILE,
    }
    body["receipt_sha256"] = sha256_json(body)
    cache[identity] = dict(body)
    setattr(_report_integration_test_execution, "_cache", cache)
    return body


def _runtime_identity() -> dict[str, object]:
    executable = Path(sys.executable).resolve()
    return {
        "python_executable": str(executable),
        "python_executable_sha256": _sha256_file(executable),
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "pytest_version": importlib.metadata.version("pytest"),
        "sympy_version": importlib.metadata.version("sympy"),
    }


def _run_checked(command: list[str]) -> bytes:
    completed = subprocess.run(
        command,
        cwd=REPO,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"identity command failed: {command!r}: "
            + completed.stderr.decode("utf-8", errors="replace")[-2000:]
        )
    return completed.stdout


def _repository_identity() -> dict[str, object]:
    commit = _run_checked(["git", "rev-parse", "HEAD"]).decode().strip()
    tree = _run_checked(["git", "rev-parse", "HEAD^{tree}"]).decode().strip()
    tracked_diff = _run_checked(
        ["git", "diff", "--binary", "--no-ext-diff", "HEAD", "--"]
    )
    status = _run_checked(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"]
    )
    return {
        "git_commit": commit,
        "git_head_tree": tree,
        "owner_source_and_test_files_bound_by_report_manifests": True,
        "scientific_input_documents_bound_by_separate_report_identities": True,
        "tracked_diff_sha256": hashlib.sha256(tracked_diff).hexdigest(),
        "worktree_state": "DIRTY" if status else "CLEAN",
    }


def _package_identity() -> dict[str, object]:
    package_root = REPO / "src" / "error_coupling_simulator"
    package_files = tuple(
        sorted(
            path
            for path in package_root.rglob("*")
            if path.is_file()
            and "__pycache__" not in path.parts
            and path.suffix != ".pyc"
        )
    )
    manifest = {
        path.relative_to(REPO).as_posix(): _sha256_file(path)
        for path in package_files
    }
    spec = importlib.util.find_spec("error_coupling_simulator")
    if spec is None or spec.origin is None:
        raise RuntimeError("installed error_coupling_simulator origin is unavailable")
    return {
        "distribution_name": "error-coupling-simulator",
        "distribution_version": importlib.metadata.version(
            "error-coupling-simulator"
        ),
        "import_origin": str(Path(spec.origin).resolve()),
        "package_file_count": len(manifest),
        "package_tree_manifest_sha256": sha256_json(manifest),
    }


def _environment_lock_identity() -> dict[str, object]:
    conda_meta = Path(sys.prefix) / "conda-meta"
    conda_records = tuple(sorted(conda_meta.glob("*.json")))
    conda_manifest = {
        path.name: _sha256_file(path) for path in conda_records
    }
    history = conda_meta / "history"
    return {
        "conda_environment_prefix": str(Path(sys.prefix).resolve()),
        "conda_history_sha256": _sha256_file(history) if history.is_file() else None,
        "conda_package_record_count": len(conda_records),
        "conda_package_records_manifest_sha256": sha256_json(conda_manifest),
        "pyproject_sha256": _sha256_file(REPO / "pyproject.toml"),
        "uv_lock_sha256": _sha256_file(REPO / "uv.lock"),
    }


def _run_contract() -> dict[str, object]:
    return {
        "arithmetic_dtype": "EXACT_FOUR_FRACTION_Q_SQRT2_I",
        "coefficient_cutoff": "NONE",
        "determinism": "EXACT_DETERMINISTIC_NO_RNG",
        "dynamic_add_relation_assignment_counts": [4096, 8192],
        "dynamic_add_variable_orders": [12, 13],
        "floating_precision_purpose": "NONE_IN_HEADLINE_OWNERS",
        "qualification_test_timeout_seconds": 120,
        "record_boundary_indices": 2,
        "representability_class": (
            "EXACT_MICROFIXTURE_ARCHITECTURE_INSTRUMENT_NOT_RECORD"
        ),
        "resource_ceiling_exact_tn_internal_indices": 20,
        "seed": "NOT_APPLICABLE_DETERMINISTIC_EXACT",
        "target_grid_executed": False,
        "tn_internal_indices": 5,
    }


def _publication_contract() -> dict[str, object]:
    return {
        "artifact_self_attests_publication_success": False,
        "exclusive_no_replace_required": True,
        "file_fsync_required": True,
        "parent_directory_fsync_required": True,
        "publication_status": "PREPARED_FOR_EXCLUSIVE_PUBLICATION",
        "strict_reload_required_after_publication": True,
        "success_owner": "EXTERNAL_PUBLICATION_RECEIPT_AFTER_CLI_RETURN",
    }


def _wrap_owner_result(
    result: dict[str, object], hash_inventory: dict[str, object]
) -> dict[str, object]:
    return {
        "hash_inventory": hash_inventory,
        "result": result,
        "result_sha256": sha256_json(result),
    }


def _wrap_oracle_receipt(
    receipt: dict[str, object], cross_check: dict[str, object]
) -> dict[str, object]:
    return {
        "cross_check": cross_check,
        "implementation_separated": True,
        "receipt": receipt,
        "receipt_sha256": sha256_json(receipt),
    }


def _make_control(
    *, expected: object, observed: object, evidence: dict[str, object]
) -> dict[str, object]:
    if observed != expected:
        raise ValueError(f"corruption control mismatch: expected {expected!r}, got {observed!r}")
    body = {
        "evidence": dict(evidence),
        "expected": expected,
        "observed": observed,
        "status": "FIRED",
    }
    return {**body, "receipt_sha256": sha256_json(body)}


def _caught(callable_object: Any) -> str:
    try:
        callable_object()
    except Exception as exc:  # the exact expected class is checked by the caller
        return type(exc).__name__
    return "NOT_REJECTED"


def _add_ast_observation() -> dict[str, object]:
    tree = ast.parse(inspect.getsource(add_module))
    definitions: dict[str, list[ast.FunctionDef | ast.AsyncFunctionDef]] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            definitions.setdefault(node.name, []).append(node)
    reachable = {"run_dynamic_add_owner"}
    changed = True
    while changed:
        changed = False
        for name in tuple(reachable):
            for function in definitions[name]:
                for node in ast.walk(function):
                    called = None
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                        called = node.func.id
                    elif isinstance(node, ast.Call) and isinstance(
                        node.func, ast.Attribute
                    ):
                        called = node.func.attr
                    if called in definitions and called not in reachable:
                        reachable.add(called)
                        changed = True
    observed_names: set[str] = set()
    for name in reachable:
        for function in definitions[name]:
            for node in ast.walk(function):
                if isinstance(node, ast.Name):
                    observed_names.add(node.id)
                elif isinstance(node, ast.Attribute):
                    observed_names.add(node.attr)
    forbidden = {
        "evaluate_all",
        "frontier",
        "iter_nonzero",
        "nonzero_assignments",
        "pair_map",
        "to_sparse",
        "truth_table",
    }
    source = inspect.getsource(add_module.advance)
    required = {
        "_apply",
        "_build_clause_function",
        "_copy_reachable",
        "_rename_output_root",
        "_snapshot",
        "advance",
        "compile_transition_relation",
        "multiply",
        "run_dynamic_add_owner",
        "sum_abstract_level",
    }
    return {
        "compile_parameters": list(
            inspect.signature(add_module.compile_transition_relation).parameters
        ),
        "forbidden_tokens_absent": forbidden.isdisjoint(observed_names),
        "multiply_present": ".multiply(" in source,
        "rename_present": "_rename_output_root(" in source,
        "required_transitive_functions_reached": required <= reachable,
        "sum_abstract_present": ".sum_abstract_level(" in source,
    }


def _wrong_order_observation() -> dict[str, int]:
    codec = Codec("wrong-order", ("L.x", "R.x", "L.z", "R.z", "m", "frame"))
    keys = frozen_fixture_keys()
    values = {
        "a": Qsqrt2i.rational(1, 2),
        "b": Qsqrt2i.sqrt2(Fraction(1, 4)),
        "c": Qsqrt2i.imag(Fraction(1, 2)),
        "d": Qsqrt2i(Fraction(0), Fraction(0), Fraction(0), Fraction(-1, 4)),
    }
    clauses = tuple(
        (codec.encode(key), values[label])
        for label in ("a", "b", "c", "d")
        for key in keys[label]
    )
    snapshot = snapshot_add_state(
        "WRONG_ORDER", build_total_function_from_fixture_clauses(codec, clauses)
    )
    return {
        "internal_count": int(snapshot["internal_count"]),
        "terminal_count": int(snapshot["terminal_count"]),
        "total": int(snapshot["reachable_node_count"]),
    }


def _tiny_gc_observation() -> dict[str, object]:
    codec = Codec("tiny-gc", ("L.x", "L.z", "R.x", "R.z", "m", "frame"))
    zero_bits = (0, 0, 0, 0, 0, 0)
    one_bits = (1, 0, 0, 0, 0, 0)
    epsilon = Qsqrt2i.sqrt2(Fraction(1, 2**42))
    state = build_total_function_from_fixture_clauses(
        codec,
        ((zero_bits, ONE), (zero_bits, -ONE), (one_bits, epsilon)),
    )
    snapshot = snapshot_add_state("TINY_GC", state)
    terminals = [
        node["value"]
        for node in snapshot["node_table"]
        if node["kind"] == "terminal"
    ]
    return {
        "allocated_equals_reachable": (
            snapshot["allocated_node_count"] == snapshot["reachable_node_count"]
        ),
        "reachable_node_count": snapshot["reachable_node_count"],
        "terminal_count": snapshot["terminal_count"],
        "terminals": terminals,
    }


def _canonical_add_from_literal_witnesses(
    *,
    width: int,
    witnesses: list[dict[str, object]],
    bits_key: str,
) -> dict[str, object]:
    """Independently rebuild the frozen canonical ADD from oracle literals."""

    if type(width) is not int or width <= 0:
        raise ValueError("literal ADD width must be a positive integer")
    assignments: dict[tuple[int, ...], tuple[tuple[int, int], ...]] = {}
    for witness in witnesses:
        bits_value = witness.get(bits_key)
        coefficient = witness.get("coefficient")
        if not isinstance(bits_value, list) or len(bits_value) != width:
            raise ValueError("literal ADD witness has the wrong bit width")
        bits = tuple(bits_value)
        if any(type(bit) is not int or bit not in (0, 1) for bit in bits):
            raise ValueError("literal ADD witness contains a non-bit")
        _validate_exact_scalar(coefficient)
        scalar = tuple(tuple(rational) for rational in coefficient)
        if scalar == ((0, 1), (0, 1), (0, 1), (0, 1)):
            raise ValueError("literal nonzero witness serializes exact zero")
        if bits in assignments:
            raise ValueError("literal ADD witness assignment is duplicated")
        assignments[bits] = scalar

    zero_scalar = ((0, 1), (0, 1), (0, 1), (0, 1))
    terminals: dict[tuple[tuple[int, int], ...], tuple[object, ...]] = {}
    internals: dict[tuple[object, ...], tuple[object, ...]] = {}

    def terminal(scalar: tuple[tuple[int, int], ...]) -> tuple[object, ...]:
        return terminals.setdefault(scalar, ("T", scalar))

    def build(
        level: int,
        rows: tuple[tuple[tuple[int, ...], tuple[tuple[int, int], ...]], ...],
    ) -> tuple[object, ...]:
        if not rows:
            return terminal(zero_scalar)
        if level == width:
            if len(rows) != 1:
                raise ValueError("literal ADD leaf assignment is not unique")
            return terminal(rows[0][1])
        low_rows = tuple(row for row in rows if row[0][level] == 0)
        high_rows = tuple(row for row in rows if row[0][level] == 1)
        low = build(level + 1, low_rows)
        high = build(level + 1, high_rows)
        if low == high:
            return low
        key = ("N", level, low, high)
        return internals.setdefault(key, key)

    root = build(0, tuple(sorted(assignments.items())))
    reachable: set[tuple[object, ...]] = set()

    def collect(node: tuple[object, ...]) -> None:
        if node in reachable:
            return
        reachable.add(node)
        if node[0] == "N":
            collect(node[2])
            collect(node[3])

    collect(root)
    terminal_nodes = [node for node in reachable if node[0] == "T"]
    terminal_nodes.sort(
        key=lambda node: canonical_json_bytes([list(x) for x in node[1]])
    )
    canonical_ids: dict[tuple[object, ...], int] = {}
    table: list[dict[str, object]] = []
    for node in terminal_nodes:
        canonical_id = len(table)
        canonical_ids[node] = canonical_id
        table.append(
            {
                "id": canonical_id,
                "kind": "terminal",
                "value": [list(rational) for rational in node[1]],
            }
        )
    internal_count = 0
    levels = sorted(
        {int(node[1]) for node in reachable if node[0] == "N"}, reverse=True
    )
    for level in levels:
        level_nodes = [
            node for node in reachable if node[0] == "N" and node[1] == level
        ]
        level_nodes.sort(
            key=lambda node: (canonical_ids[node[2]], canonical_ids[node[3]])
        )
        for node in level_nodes:
            canonical_id = len(table)
            canonical_ids[node] = canonical_id
            table.append(
                {
                    "high": canonical_ids[node[3]],
                    "id": canonical_id,
                    "kind": "internal",
                    "level": level,
                    "low": canonical_ids[node[2]],
                }
            )
            internal_count += 1
    return {
        "internal_count": internal_count,
        "node_table": table,
        "node_table_sha256": sha256_json(table),
        "reachable_node_count": len(reachable),
        "root_id": canonical_ids[root],
        "terminal_count": len(terminal_nodes),
    }


def _validate_add_tables_against_literal_oracle(
    add_result: Mapping[str, object], sympy_oracle: Mapping[str, object]
) -> None:
    checkpoints = add_result["checkpoints"]
    oracle_checkpoints = sympy_oracle["checkpoint_literal_maps"]
    for checkpoint, oracle_checkpoint in zip(
        checkpoints, oracle_checkpoints, strict=True
    ):
        expected = _canonical_add_from_literal_witnesses(
            width=oracle_checkpoint["width"],
            witnesses=oracle_checkpoint["nonzero_witnesses"],
            bits_key="bits",
        )
        observed = {
            key: checkpoint[key]
            for key in (
                "internal_count",
                "node_table",
                "node_table_sha256",
                "reachable_node_count",
                "root_id",
                "terminal_count",
            )
        }
        if observed != expected:
            raise ValueError("independent ADD table reconstruction mismatch")
        if checkpoint["allocated_node_count"] != expected["reachable_node_count"]:
            raise ValueError("dynamic ADD checkpoint retained unreachable nodes")

    for relation, oracle_relation in zip(
        add_result["relation_receipts"], sympy_oracle["relations"], strict=True
    ):
        expected = _canonical_add_from_literal_witnesses(
            width=oracle_relation["input_width"] + oracle_relation["output_width"],
            witnesses=oracle_relation["nonzero_witnesses"],
            bits_key="combined_bits",
        )
        if relation != {
            "combined_order": oracle_relation["combined_order"],
            "event": oracle_relation["event"],
            "node_table_sha256": expected["node_table_sha256"],
            "reachable_node_count": expected["reachable_node_count"],
        }:
            raise ValueError("independent ADD table reconstruction mismatch")


def _fixture_identities(
    pair_result: dict[str, object],
    add_result: dict[str, object],
    tn_result: dict[str, object],
) -> dict[str, object]:
    program = frozen_pair_add_program()
    graph = frozen_tn_graph()
    program_data = program.to_data()
    codec_rows = [
        {"name": codec.name, "sha256": codec.sha256} for codec in program.codecs
    ]
    event_rows = [
        {
            "name": event.name,
            "sha256": sha256_json(
                event.to_data(program.codecs[index], program.codecs[index + 1])
            ),
        }
        for index, event in enumerate(program.events)
    ]
    relation_rows = []
    for receipt in add_result["relation_receipts"]:
        identity = {
            "combined_order_sha256": sha256_json(receipt["combined_order"]),
            "event": receipt["event"],
            "node_table_sha256": receipt["node_table_sha256"],
            "reachable_node_count": receipt["reachable_node_count"],
        }
        relation_rows.append({**identity, "identity_sha256": sha256_json(identity)})

    pair_body = {
        "codec_sha256": codec_rows,
        "event_sha256": event_rows,
        "initial_map_sha256": sha256_json(program_data["initial"]),
        "key_catalog_sha256": sha256_json(
            {
                label: [key.to_data() for key in keys]
                for label, keys in frozen_fixture_keys().items()
            }
        ),
        "pair_checkpoint_map_sha256": [
            row["map_sha256"] for row in pair_result["checkpoints"]
        ],
        "program_sha256": program.sha256,
        "relation_identities": relation_rows,
        "tail_scalar_sha256": sha256_json(
            [[0, 1], [1, 2**42], [0, 1], [0, 1]]
        ),
        "zero_scalar_sha256": sha256_json(
            [[0, 1], [0, 1], [0, 1], [0, 1]]
        ),
    }
    graph_data = graph.to_data()
    tn_body = {
        "boundary_sha256": sha256_json(graph_data["boundary"]),
        "domain_sha256": sha256_json(graph_data["indices"]),
        "factor_graph_sha256": graph.sha256,
        "factor_sha256": sha256_json(graph_data["factors"]),
        "terminal_record_representation_sha256": sha256_json(
            graph.terminal_record_representation
        ),
        "unweighted_order_sha256": sha256_json(tn_result["unweighted"]["order"]),
        "weighted_order_sha256": sha256_json(tn_result["weighted"]["order"]),
    }
    return {
        "pair_add": {**pair_body, "identity_sha256": sha256_json(pair_body)},
        "retained_boundary_tn": {**tn_body, "identity_sha256": sha256_json(tn_body)},
    }


def _owner_results(
    pair_result: dict[str, object],
    add_result: dict[str, object],
    tn_result: dict[str, object],
) -> dict[str, object]:
    return {
        "dynamic_add": _wrap_owner_result(
            add_result,
            {
                "checkpoint_node_table_sha256": [
                    row["node_table_sha256"] for row in add_result["checkpoints"]
                ],
                "history_sha256": add_result["history_sha256"],
                "relation_node_table_sha256": [
                    row["node_table_sha256"]
                    for row in add_result["relation_receipts"]
                ],
            },
        ),
        "pair": _wrap_owner_result(
            pair_result,
            {
                "checkpoint_map_sha256": [
                    row["map_sha256"] for row in pair_result["checkpoints"]
                ],
                "checkpoint_truth_entries_sha256": [
                    row["truth_entries_sha256"] for row in pair_result["checkpoints"]
                ],
                "history_sha256": pair_result["history_sha256"],
            },
        ),
        "retained_boundary_tn": _wrap_owner_result(
            tn_result,
            {
                "factor_graph_sha256": tn_result["factor_graph_sha256"],
                "unweighted_order_sha256": sha256_json(
                    tn_result["unweighted"]["order"]
                ),
                "unweighted_proof_sha256": tn_result["unweighted"]["proof"][
                    "proof_sha256"
                ],
                "weighted_order_sha256": sha256_json(
                    tn_result["weighted"]["order"]
                ),
                "weighted_proof_sha256": tn_result["weighted"]["proof"][
                    "proof_sha256"
                ],
            },
        ),
    }


def _corruption_controls(
    *,
    program: Any,
    pair_result: dict[str, object],
    reverse_pair: dict[str, object],
    add_result: dict[str, object],
    reverse_add: dict[str, object],
    sympy_oracle: dict[str, object],
    tn_oracle: dict[str, object],
    test_execution: dict[str, object],
) -> dict[str, object]:
    test_receipt = {
        "qualification_test_receipt_sha256": test_execution["receipt_sha256"]
    }
    swapped = Codec("A0-swapped", ("R.x", "L.z", "L.x", "R.z", "m", "frame"))
    swapped_program = replace(
        program, codecs=(swapped, program.codecs[1], program.codecs[2])
    )
    first_event = program.events[0]
    changed_row = replace(first_event.rows[0], weight=ZERO)
    changed_event = replace(
        first_event, rows=(changed_row,) + first_event.rows[1:]
    )
    changed_program = replace(
        program, events=(changed_event, program.events[1])
    )

    float_rejection = _caught(
        lambda: Qsqrt2i(0.0, Fraction(0), Fraction(0), Fraction(0))
    )
    codec_rejection = _caught(lambda: run_pair_owner(swapped_program))
    weight_rejection = _caught(lambda: run_pair_owner(changed_program))
    duplicate_codec_rejection = _caught(
        lambda: Codec(
            "duplicate-L", ("L.x", "L.x", "R.x", "R.z", "m", "frame")
        )
    )
    noncanonical_rejection = _caught(
        lambda: _validate_exact_scalar(
            [[0, 2], [0, 1], [0, 1], [0, 1]]
        )
    )
    nonpositive_rejection = _caught(
        lambda: _validate_exact_scalar(
            [[1, -2], [0, 1], [0, 1], [0, 1]]
        )
    )
    base_key = PairKey(1, 0, 0, 0, -1, 0, ())
    left_only = PairKey(0, 0, 0, 0, -1, 0, ())
    right_only = PairKey(1, 0, 1, 0, -1, 0, ())
    base_codec = program.codecs[0]
    codec_witnesses = {
        "left_only_distinct": base_codec.encode(base_key) != base_codec.encode(left_only),
        "right_only_distinct": (
            base_codec.encode(base_key) != base_codec.encode(right_only)
        ),
    }
    graph = frozen_tn_graph()
    unknown_index_rejection = _caught(
        lambda: replace(
            graph,
            factors=graph.factors
            + (Factor("ghost-edge", "PAIR", ("d0", "ghost")),),
        )
    )
    invalid_domain_rejection = _caught(
        lambda: Index("bad-domain", "classical", 3)
    )
    incomplete_order_rejection = _caught(
        lambda: replay_order(graph, ("d0", "d1", "c0", "c1"))
    )

    original_pair_entry = pair_module.run_pair_owner
    try:
        pair_module.run_pair_owner = lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("poisoned pair frontier")
        )
        poisoned_add_history = run_dynamic_add_owner(program)[
            "n_exact_pair_add_nodes_history_micro"
        ]
    finally:
        pair_module.run_pair_owner = original_pair_entry

    tail_evidence = sympy_oracle["interference_evidence"]
    tn_corruptions = tn_oracle["corruption_checks"]
    exhaustive = tn_oracle["exhaustive"]
    controls = {
        "add_ast_direct_root_guard": _make_control(
            expected={
                "compile_parameters": ["event", "input_codec", "output_codec"],
                "forbidden_tokens_absent": True,
                "multiply_present": True,
                "rename_present": True,
                "required_transitive_functions_reached": True,
                "sum_abstract_present": True,
            },
            observed=_add_ast_observation(),
            evidence=test_receipt,
        ),
        "add_every_code_independent_oracle": _make_control(
            expected={
                "checkpoint_assignment_counts": [64, 64, 128],
                "owner_oracle_boundary_test_passed": True,
                "relation_assignment_counts": [4096, 8192],
            },
            observed={
                "checkpoint_assignment_counts": [
                    row["exhaustive_assignment_count"]
                    for row in sympy_oracle["checkpoint_literal_maps"]
                ],
                "owner_oracle_boundary_test_passed": (
                    test_execution["status"] == "PASS"
                ),
                "relation_assignment_counts": [
                    row["exhaustive_assignment_count"]
                    for row in sympy_oracle["relations"]
                ],
            },
            evidence={
                **test_receipt,
                "test_node": (
                    "tests/test_external_no_cutoff_independent_sympy_oracle.py::"
                    "test_independent_sympy_maps_match_pair_and_add_only_at_test_boundary"
                ),
            },
        ),
        "add_gc_tiny_terminal": _make_control(
            expected={
                "allocated_equals_reachable": True,
                "reachable_node_count": 8,
                "terminal_count": 2,
                "terminals": [
                    [[0, 1], [0, 1], [0, 1], [0, 1]],
                    [[0, 1], [1, 2**42], [0, 1], [0, 1]],
                ],
            },
            observed=_tiny_gc_observation(),
            evidence=test_receipt,
        ),
        "add_pair_frontier_poisoned": _make_control(
            expected=[7, 20, 11],
            observed=poisoned_add_history,
            evidence=test_receipt,
        ),
        "add_relation_row_order_invariant": _make_control(
            expected={
                "history": add_result["n_exact_pair_add_nodes_history_micro"],
                "relation_receipts": add_result["relation_receipts"],
                "tables": [
                    row["node_table_sha256"] for row in add_result["checkpoints"]
                ],
            },
            observed={
                "history": reverse_add["n_exact_pair_add_nodes_history_micro"],
                "relation_receipts": reverse_add["relation_receipts"],
                "tables": [
                    row["node_table_sha256"] for row in reverse_add["checkpoints"]
                ],
            },
            evidence=test_receipt,
        ),
        "add_wrong_variable_order": _make_control(
            expected={"internal_count": 13, "terminal_count": 5, "total": 18},
            observed=_wrong_order_observation(),
            evidence=test_receipt,
        ),
        "pair_changed_weight_rejected": _make_control(
            expected="ValueError", observed=weight_rejection, evidence=test_receipt
        ),
        "pair_codec_reorder_rejected": _make_control(
            expected="ValueError", observed=codec_rejection, evidence=test_receipt
        ),
        "pair_exact_cancellation": _make_control(
            expected={
                "deleted_zero": [[0, 1], [0, 1], [0, 1], [0, 1]],
                "deleted_zero_is_exact": True,
                "final_support": 2,
            },
            observed={
                "deleted_zero": tail_evidence["deleted_zero"],
                "deleted_zero_is_exact": tail_evidence["deleted_zero_is_exact"],
                "final_support": pair_result["support_history"][-1],
            },
            evidence=test_receipt,
        ),
        "pair_float_rejected": _make_control(
            expected="TypeError", observed=float_rejection, evidence=test_receipt
        ),
        "pair_left_right_codec_witnesses": _make_control(
            expected={"left_only_distinct": True, "right_only_distinct": True},
            observed=codec_witnesses,
            evidence=test_receipt,
        ),
        "pair_noncanonical_rational_rejected": _make_control(
            expected="ValueError",
            observed=noncanonical_rejection,
            evidence=test_receipt,
        ),
        "pair_nonpositive_denominator_rejected": _make_control(
            expected="ValueError",
            observed=nonpositive_rejection,
            evidence=test_receipt,
        ),
        "pair_duplicate_codec_rejected": _make_control(
            expected="ValueError",
            observed=duplicate_codec_rejection,
            evidence=test_receipt,
        ),
        "pair_row_order_invariant": _make_control(
            expected={
                "map_sha256": [
                    row["map_sha256"] for row in pair_result["checkpoints"]
                ],
                "support_history": pair_result["support_history"],
            },
            observed={
                "map_sha256": [
                    row["map_sha256"] for row in reverse_pair["checkpoints"]
                ],
                "support_history": reverse_pair["support_history"],
            },
            evidence=test_receipt,
        ),
        "pair_sub_1e_minus_12_tail_survives": _make_control(
            expected={
                "tail": [[0, 1], [1, 2**42], [0, 1], [0, 1]],
                "tail_is_strictly_positive": True,
                "tail_squared_is_below_1e_minus_24": True,
            },
            observed={
                "tail": tail_evidence["tail"],
                "tail_is_strictly_positive": tail_evidence[
                    "tail_is_strictly_positive"
                ],
                "tail_squared_is_below_1e_minus_24": tail_evidence[
                    "tail_squared_is_below_1e_minus_24"
                ],
            },
            evidence=test_receipt,
        ),
        "tn_boundary_elimination_rejected": _make_control(
            expected=True,
            observed=tn_corruptions["boundary_elimination_rejected"],
            evidence=test_receipt,
        ),
        "tn_c0_domain_raised": _make_control(
            expected={"weighted_exact_value": 7},
            observed=tn_corruptions["change_c0_log2_domain_1_to_2"],
            evidence=test_receipt,
        ),
        "tn_d1_domain_lowered": _make_control(
            expected={"weighted_exact_value": 5},
            observed=tn_corruptions["change_d1_log2_domain_2_to_1"],
            evidence=test_receipt,
        ),
        "tn_exhaustive_optima": _make_control(
            expected={
                "disjoint": True,
                "order_count": 120,
                "unweighted_count": 12,
                "weighted_count": 16,
            },
            observed={
                "disjoint": exhaustive["optimum_sets_disjoint"],
                "order_count": exhaustive["order_count"],
                "unweighted_count": exhaustive["unweighted"]["optimum_count"],
                "weighted_count": exhaustive["weighted"]["optimum_count"],
            },
            evidence=test_receipt,
        ),
        "tn_fixed_output_ineligible": _make_control(
            expected={
                "classification": "INELIGIBLE_FIXED_OUTPUT_DIAGNOSTIC",
                "unweighted_exact_value": 2,
                "weighted_exact_value": 5,
            },
            observed=tn_corruptions["clamp_record_boundary_ineligible"],
            evidence=test_receipt,
        ),
        "tn_missing_keep_rejected": _make_control(
            expected=True,
            observed=tn_corruptions["missing_keep_rejected"],
            evidence=test_receipt,
        ),
        "tn_incomplete_order_rejected": _make_control(
            expected="ValueError",
            observed=incomplete_order_rejection,
            evidence=test_receipt,
        ),
        "tn_invalid_domain_rejected": _make_control(
            expected="ValueError",
            observed=invalid_domain_rejection,
            evidence=test_receipt,
        ),
        "tn_remove_edge_d0_d1": _make_control(
            expected={"weighted_exact_value": 5},
            observed=tn_corruptions["remove_edge_d0_d1"],
            evidence=test_receipt,
        ),
        "tn_remove_edge_d1_d2": _make_control(
            expected={"weighted_exact_value": 5},
            observed=tn_corruptions["remove_edge_d1_d2"],
            evidence=test_receipt,
        ),
        "tn_tampered_dp_cell_rejected": _make_control(
            expected=True,
            observed=tn_corruptions["tampered_dp_cell_rejected"],
            evidence=test_receipt,
        ),
        "tn_unknown_index_rejected": _make_control(
            expected="ValueError",
            observed=unknown_index_rejection,
            evidence=test_receipt,
        ),
    }
    return controls


def _validate_owner_and_oracle_results(report: Mapping[str, object]) -> None:
    owner_wrappers = report["owner_results"]
    oracle_wrappers = report["independent_oracle_receipts"]
    if not isinstance(owner_wrappers, dict) or set(owner_wrappers) != {
        "dynamic_add",
        "pair",
        "retained_boundary_tn",
    }:
        raise ValueError("owner result set is invalid")
    if not isinstance(oracle_wrappers, dict) or set(oracle_wrappers) != {
        "sympy_pair_add",
        "tn_literal",
    }:
        raise ValueError("independent oracle set is invalid")
    for name, wrapper in owner_wrappers.items():
        if not isinstance(wrapper, dict) or set(wrapper) != {
            "hash_inventory",
            "result",
            "result_sha256",
        }:
            raise TypeError(f"{name} owner wrapper must be an object")
        result = wrapper.get("result")
        if not isinstance(result, dict):
            raise TypeError(f"{name} owner result must be an object")
        if wrapper.get("result_sha256") != sha256_json(result):
            raise ValueError(f"{name} owner whole-result hash mismatch")
        if result.get("scope") != "MICRO_QUALIFICATION_ONLY":
            raise ValueError(f"{name} owner escaped micro scope")
        if result.get("solver_permission") != "CODE_BLOCKED":
            raise ValueError(f"{name} owner changed solver permission")
        if result.get("target_lowering") != "UNAVAILABLE":
            raise ValueError(f"{name} owner claimed a target lowering")
    for name, wrapper in oracle_wrappers.items():
        if not isinstance(wrapper, dict) or set(wrapper) != {
            "cross_check",
            "implementation_separated",
            "receipt",
            "receipt_sha256",
        }:
            raise TypeError(f"{name} oracle wrapper must be an object")
        receipt = wrapper.get("receipt")
        if not isinstance(receipt, dict):
            raise TypeError(f"{name} oracle receipt must be an object")
        if wrapper.get("receipt_sha256") != sha256_json(receipt):
            raise ValueError(f"{name} oracle whole-receipt hash mismatch")
        if wrapper.get("implementation_separated") is not True:
            raise ValueError(f"{name} oracle is not marked implementation-separated")

    pair_result = owner_wrappers["pair"]["result"]
    add_result = owner_wrappers["dynamic_add"]["result"]
    tn_result = owner_wrappers["retained_boundary_tn"]["result"]
    sympy_oracle = oracle_wrappers["sympy_pair_add"]["receipt"]
    tn_oracle = oracle_wrappers["tn_literal"]["receipt"]
    if sympy_oracle != run_independent_sympy_pair_add_oracle():
        raise ValueError("independent SymPy receipt does not reproduce exactly")
    if tn_oracle != run_independent_tn_oracle():
        raise ValueError("independent TN receipt does not reproduce exactly")
    if sympy_oracle.get("sympy_version") != "1.14.0":
        raise ValueError("independent SymPy version is not the frozen 1.14.0")
    _validate_add_tables_against_literal_oracle(add_result, sympy_oracle)
    if pair_result["support_history"] != [2, 8, 2]:
        raise ValueError("pair owner support prediction drifted")
    if pair_result["n_pauli_pair_states_peak_micro"] != 8:
        raise ValueError("pair owner peak prediction drifted")
    if add_result["n_exact_pair_add_nodes_history_micro"] != [7, 20, 11]:
        raise ValueError("dynamic ADD owner history prediction drifted")
    if add_result["n_exact_pair_add_nodes_peak_micro"] != 20:
        raise ValueError("dynamic ADD owner peak prediction drifted")
    if [
        (row["internal_count"], row["terminal_count"])
        for row in add_result["checkpoints"]
    ] != [(5, 2), (15, 5), (9, 2)]:
        raise ValueError("dynamic ADD canonical table counts drifted")
    if pair_result != run_pair_owner(frozen_pair_add_program()):
        raise ValueError("pair owner embedded result does not reproduce exactly")
    if add_result != run_dynamic_add_owner(frozen_pair_add_program()):
        raise ValueError("dynamic ADD embedded result does not reproduce exactly")
    if tn_result != run_retained_boundary_tn_owner(frozen_tn_graph()):
        raise ValueError("TN owner embedded result does not reproduce exactly")
    if sympy_oracle["support_history"] != pair_result["support_history"]:
        raise ValueError("independent SymPy support history disagrees with pair owner")
    sympy_payload = {
        key: value
        for key, value in sympy_oracle.items()
        if key != "oracle_payload_sha256"
    }
    if sympy_oracle["oracle_payload_sha256"] != sha256_json(sympy_payload):
        raise ValueError("independent SymPy payload hash mismatch")
    for pair_checkpoint, oracle_checkpoint in zip(
        pair_result["checkpoints"],
        sympy_oracle["checkpoint_literal_maps"],
        strict=True,
    ):
        pair_entries = [
            {
                "bits": entry["bits"],
                "coefficient": entry["coefficient"],
                "key": entry["key"],
            }
            for entry in pair_checkpoint["entries"]
        ]
        if pair_entries != oracle_checkpoint["nonzero_witnesses"]:
            raise ValueError("independent SymPy checkpoint disagrees with pair owner")
    if tn_result["factor_graph_sha256"] != tn_oracle["graph_sha256"]:
        raise ValueError("independent TN graph identity disagrees with owner")
    if (
        tn_result["unweighted"]["exact_value"],
        tn_result["weighted"]["exact_value"],
        tn_result["weighted"]["peak_dense_entries"],
    ) != (3, 6, 64):
        raise ValueError("retained-boundary TN owner prediction drifted")
    if (
        tn_oracle["exhaustive"]["unweighted"]["exact_value"],
        tn_oracle["exhaustive"]["weighted"]["exact_value"],
        tn_oracle["exhaustive"]["weighted"]["peak_dense_entries"],
    ) != (3, 6, 64):
        raise ValueError("independent retained-boundary TN prediction drifted")
    for owner_key, oracle_key in (
        ("unweighted", "unweighted"),
        ("weighted", "weighted"),
    ):
        owner_proof = tn_result[owner_key]["proof"]
        oracle_proof = tn_oracle["subset_dp"][oracle_key]
        verify_frozen_subset_proof(owner_proof)
        if (
            owner_proof["values"] != oracle_proof["values"]
            or owner_proof["orders"] != oracle_proof["orders"]
            or owner_proof["proof_sha256"] != oracle_proof["proof_sha256"]
        ):
            raise ValueError("independent TN subset proof disagrees with owner")

    expected_owner_wrappers = _owner_results(pair_result, add_result, tn_result)
    if owner_wrappers != expected_owner_wrappers:
        raise ValueError("owner hash inventory does not match the embedded results")
    expected_sympy_cross_check = {
        "checkpoint_nonzero_maps_equal": True,
        "dynamic_add_every_code_test_node_passed": True,
        "support_history_equal": (
            sympy_oracle["support_history"] == pair_result["support_history"]
        ),
    }
    expected_tn_cross_check = {
        "candidate_proofs_independently_verified": True,
        "complete_dp_tables_equal": True,
        "graph_sha256_equal": (
            tn_oracle["graph_sha256"] == tn_result["factor_graph_sha256"]
        ),
    }
    if oracle_wrappers["sympy_pair_add"].get("cross_check") != (
        expected_sympy_cross_check
    ):
        raise ValueError("SymPy oracle cross-check receipt mismatch")
    if oracle_wrappers["tn_literal"].get("cross_check") != expected_tn_cross_check:
        raise ValueError("TN oracle cross-check receipt mismatch")


def validate_report(
    report: Mapping[str, object], *, verify_current_sources: bool = False
) -> None:
    if set(report) != _TOP_LEVEL_KEYS:
        missing = sorted(_TOP_LEVEL_KEYS - set(report))
        extra = sorted(set(report) - _TOP_LEVEL_KEYS)
        raise ValueError(f"wrong report key set; missing={missing}, extra={extra}")
    expected_literals = {
        "_schema": REPORT_SCHEMA,
        "certification_verdict": "UNANCHORED",
        "delta_tv_cert": "UNAVAILABLE/UNANCHORED_FULL_RECORD",
        "dynamic_add_micro_owner": "QUALIFIED",
        "faithfulness_disposition": "UNAVAILABLE",
        "pair_micro_owner": "QUALIFIED",
        "report_status": REPORT_STATUS,
        "retained_boundary_tn_micro_owner": "QUALIFIED",
        "route_disposition": "NO_ROUTE_KILLED_OR_PROMOTED_BY_MICROFIXTURE",
        "scope": "MICRO_QUALIFICATION_ONLY",
        "solver_permission": "CODE_BLOCKED",
        "target_d3_d5_metrics": "UNAVAILABLE",
        "target_dynamic_add_owner": (
            "UNAVAILABLE/NO_TARGET_QEC_DYNAMIC_ADD_LOWERING"
        ),
        "target_pair_owner": "UNAVAILABLE/NO_TARGET_QEC_PAIR_LOWERING",
        "target_retained_boundary_tn_owner": (
            "UNAVAILABLE/NO_TARGET_QEC_TN_LOWERING"
        ),
    }
    for key, expected in expected_literals.items():
        if report.get(key) != expected:
            raise ValueError(f"wrong report disposition: {key}")
    _reject_floats(dict(report))
    _walk_and_validate_scalars(dict(report))

    preregistration = report["preregistration"]
    if preregistration != {
        "path": PREREG_RELATIVE,
        "reviewed_pre_activation_sha256": REVIEWED_PREACTIVATION_SHA256,
        "sha256": ACTIVE_PREREG_SHA256,
        "status": "ACTIVE PRE-REGISTRATION, MICRO-OWNERS ONLY, CODE_BLOCKED",
    }:
        raise ValueError("active preregistration identity mismatch")
    library = report["library_to_metric_match"]
    if not isinstance(library, dict) or library.get("path") != LIBRARY_MATCH_RELATIVE:
        raise ValueError("library-to-metric path mismatch")
    if library.get("sha256") != LIBRARY_MATCH_SHA256:
        raise ValueError("library-to-metric hash mismatch")
    expected_library_routes = {
        "dynamic_add": {
            "direct_owner": "NONE",
            "strongest_substrate": "Sylvan",
        },
        "pair": {
            "direct_owner": "NONE",
            "independent_oracle": "SymPy",
        },
        "retained_boundary_tn": {
            "direct_owner": "NONE",
            "corroborators": ["cotengra", "Jdrasil", "NetworkX"],
        },
    }
    if library.get("route_match") != expected_library_routes:
        raise ValueError("library-to-metric route match drifted")

    firewall = report["historical_census_firewall"]
    if firewall != {
        "historical_reason_codes_reinterpreted": False,
        "path": HISTORICAL_CENSUS_RELATIVE,
        "retroactively_amended": False,
        "sha256": HISTORICAL_CENSUS_REPORT_SHA256,
        "target_cells_rewritten": False,
    }:
        raise ValueError("historical census firewall mismatch")
    _validate_owner_and_oracle_results(report)

    owner_wrappers = report["owner_results"]
    expected_fixtures = _fixture_identities(
        owner_wrappers["pair"]["result"],
        owner_wrappers["dynamic_add"]["result"],
        owner_wrappers["retained_boundary_tn"]["result"],
    )
    if report["fixture_identities"] != expected_fixtures:
        raise ValueError("fixture identity inventory mismatch")

    controls = report["corruption_controls"]
    if not isinstance(controls, dict) or set(controls) != _CONTROL_KEYS:
        raise ValueError("corruption-control ledger is incomplete")
    for name, control in controls.items():
        if not isinstance(control, dict) or control.get("status") != "FIRED":
            raise ValueError(f"corruption control did not fire: {name}")
        body = {key: value for key, value in control.items() if key != "receipt_sha256"}
        if control.get("receipt_sha256") != sha256_json(body):
            raise ValueError(f"corruption-control receipt hash mismatch: {name}")
        if control.get("observed") != control.get("expected"):
            raise ValueError(f"corruption-control outcome mismatch: {name}")

    provenance = report["provenance"]
    if not isinstance(provenance, dict) or set(provenance) != {
        "environment_lock_identity",
        "package_identity",
        "publication_contract",
        "qualification_test_execution",
        "repository_identity",
        "run_contract",
        "runtime_identity",
        "source_sha256",
        "test_sha256",
    }:
        raise ValueError("provenance key set is invalid")
    if set(provenance["source_sha256"]) != set(SOURCE_FILES):
        raise ValueError("source hash manifest is incomplete")
    if set(provenance["test_sha256"]) != set(TEST_FILES):
        raise ValueError("test hash manifest is incomplete")
    for manifest_name in ("source_sha256", "test_sha256"):
        for relative, digest in provenance[manifest_name].items():
            _require_sha256(digest, name=f"{manifest_name}:{relative}")
    test_execution = provenance["qualification_test_execution"]
    expected_test_command = [
        "python",
        "-m",
        "pytest",
        "-q",
        *QUALIFICATION_TEST_FILES,
    ]
    if test_execution.get("command") != expected_test_command:
        raise ValueError("qualification test command drifted")
    if test_execution.get("test_files") != list(QUALIFICATION_TEST_FILES):
        raise ValueError("qualification test file list drifted")
    if test_execution.get("passed_count") != 27:
        raise ValueError("qualification test pass count drifted")
    if test_execution.get("status") != "PASS" or test_execution.get("return_code") != 0:
        raise ValueError("fresh qualification test execution did not pass")
    runtime = provenance["runtime_identity"]
    if not isinstance(runtime, dict) or set(runtime) != {
        "pytest_version",
        "python_executable",
        "python_executable_sha256",
        "python_implementation",
        "python_version",
        "sympy_version",
    }:
        raise ValueError("runtime identity is incomplete")
    _require_sha256(
        runtime["python_executable_sha256"], name="python executable identity"
    )
    expected_test_input_identity = sha256_json(
        {
            "pytest_version": runtime["pytest_version"],
            "python_executable": runtime["python_executable"],
            "source_sha256": provenance["source_sha256"],
            "test_sha256": {
                path: provenance["test_sha256"][path]
                for path in QUALIFICATION_TEST_FILES
            },
        }
    )
    if test_execution.get("input_identity_sha256") != expected_test_input_identity:
        raise ValueError("qualification test input identity mismatch")
    test_body = {
        key: value for key, value in test_execution.items() if key != "receipt_sha256"
    }
    if test_execution.get("receipt_sha256") != sha256_json(test_body):
        raise ValueError("qualification test receipt hash mismatch")
    pair_result = owner_wrappers["pair"]["result"]
    add_result = owner_wrappers["dynamic_add"]["result"]
    sympy_oracle = report["independent_oracle_receipts"]["sympy_pair_add"][
        "receipt"
    ]
    tn_oracle = report["independent_oracle_receipts"]["tn_literal"]["receipt"]
    expected_controls = _corruption_controls(
        program=frozen_pair_add_program(),
        pair_result=pair_result,
        reverse_pair=run_pair_owner(frozen_pair_add_program(reverse_rows=True)),
        add_result=add_result,
        reverse_add=run_dynamic_add_owner(
            frozen_pair_add_program(reverse_rows=True)
        ),
        sympy_oracle=sympy_oracle,
        tn_oracle=tn_oracle,
        test_execution=test_execution,
    )
    if controls != expected_controls:
        raise ValueError("corruption-control expected ledger mismatch")
    if runtime["sympy_version"] != "1.14.0":
        raise ValueError("runtime SymPy version is not frozen 1.14.0")
    if sympy_oracle["sympy_version"] != runtime["sympy_version"]:
        raise ValueError("oracle SymPy version disagrees with runtime identity")
    if provenance["package_identity"] != _package_identity():
        raise ValueError("package identity does not reproduce")
    if provenance["repository_identity"] != _repository_identity():
        raise ValueError("repository identity does not reproduce")
    if provenance["environment_lock_identity"] != _environment_lock_identity():
        raise ValueError("environment lock identity does not reproduce")
    if provenance["run_contract"] != _run_contract():
        raise ValueError("exact microfixture run contract drifted")
    if provenance["publication_contract"] != _publication_contract():
        raise ValueError("publication contract drifted")

    content_body = {key: value for key, value in report.items() if key != "content_sha256"}
    if report["content_sha256"] != sha256_json(content_body):
        raise ValueError("report content hash mismatch")
    _require_sha256(report["content_sha256"], name="content_sha256")
    canonical_json_bytes(dict(report))

    if verify_current_sources:
        expected_source = _file_manifest(SOURCE_FILES)
        expected_tests = _file_manifest(TEST_FILES)
        if provenance["source_sha256"] != expected_source:
            raise ValueError("current source bytes differ from report provenance")
        if provenance["test_sha256"] != expected_tests:
            raise ValueError("current test bytes differ from report provenance")
        if _sha256_file(REPO / PREREG_RELATIVE) != ACTIVE_PREREG_SHA256:
            raise ValueError("current preregistration bytes drifted")
        if _sha256_file(REPO / LIBRARY_MATCH_RELATIVE) != LIBRARY_MATCH_SHA256:
            raise ValueError("current library matching bytes drifted")
        if (
            _sha256_file(REPO / HISTORICAL_CENSUS_RELATIVE)
            != HISTORICAL_CENSUS_REPORT_SHA256
        ):
            raise ValueError("historical census report was modified")
        if runtime != _runtime_identity():
            raise ValueError("current runtime differs from report provenance")


def build_report() -> dict[str, object]:
    program = frozen_pair_add_program()
    reverse_program = frozen_pair_add_program(reverse_rows=True)
    pair_result = run_pair_owner(program)
    reverse_pair = run_pair_owner(reverse_program)
    add_result = run_dynamic_add_owner(program)
    reverse_add = run_dynamic_add_owner(reverse_program)
    tn_result = run_retained_boundary_tn_owner(frozen_tn_graph())
    sympy_oracle = run_independent_sympy_pair_add_oracle()
    tn_oracle = run_independent_tn_oracle()
    for objective in ("unweighted", "weighted"):
        verify_frozen_subset_proof(tn_result[objective]["proof"])

    source_sha256 = _file_manifest(SOURCE_FILES)
    test_sha256 = _file_manifest(TEST_FILES)
    test_execution = _qualified_test_execution(source_sha256, test_sha256)
    owner_results = _owner_results(pair_result, add_result, tn_result)
    independent_oracles = {
        "sympy_pair_add": _wrap_oracle_receipt(
            sympy_oracle,
            {
                "checkpoint_nonzero_maps_equal": True,
                "dynamic_add_every_code_test_node_passed": True,
                "support_history_equal": (
                    sympy_oracle["support_history"] == pair_result["support_history"]
                ),
            },
        ),
        "tn_literal": _wrap_oracle_receipt(
            tn_oracle,
            {
                "candidate_proofs_independently_verified": True,
                "complete_dp_tables_equal": True,
                "graph_sha256_equal": (
                    tn_oracle["graph_sha256"] == tn_result["factor_graph_sha256"]
                ),
            },
        ),
    }
    report: dict[str, object] = {
        "_schema": REPORT_SCHEMA,
        "certification_verdict": "UNANCHORED",
        "corruption_controls": _corruption_controls(
            program=program,
            pair_result=pair_result,
            reverse_pair=reverse_pair,
            add_result=add_result,
            reverse_add=reverse_add,
            sympy_oracle=sympy_oracle,
            tn_oracle=tn_oracle,
            test_execution=test_execution,
        ),
        "delta_tv_cert": "UNAVAILABLE/UNANCHORED_FULL_RECORD",
        "dynamic_add_micro_owner": "QUALIFIED",
        "faithfulness_disposition": "UNAVAILABLE",
        "fixture_identities": _fixture_identities(
            pair_result, add_result, tn_result
        ),
        "historical_census_firewall": {
            "historical_reason_codes_reinterpreted": False,
            "path": HISTORICAL_CENSUS_RELATIVE,
            "retroactively_amended": False,
            "sha256": HISTORICAL_CENSUS_REPORT_SHA256,
            "target_cells_rewritten": False,
        },
        "independent_oracle_receipts": independent_oracles,
        "library_to_metric_match": {
            "path": LIBRARY_MATCH_RELATIVE,
            "route_match": {
                "dynamic_add": {
                    "direct_owner": "NONE",
                    "strongest_substrate": "Sylvan",
                },
                "pair": {
                    "direct_owner": "NONE",
                    "independent_oracle": "SymPy",
                },
                "retained_boundary_tn": {
                    "corroborators": ["cotengra", "Jdrasil", "NetworkX"],
                    "direct_owner": "NONE",
                },
            },
            "sha256": LIBRARY_MATCH_SHA256,
        },
        "owner_results": owner_results,
        "pair_micro_owner": "QUALIFIED",
        "preregistration": {
            "path": PREREG_RELATIVE,
            "reviewed_pre_activation_sha256": REVIEWED_PREACTIVATION_SHA256,
            "sha256": ACTIVE_PREREG_SHA256,
            "status": "ACTIVE PRE-REGISTRATION, MICRO-OWNERS ONLY, CODE_BLOCKED",
        },
        "provenance": {
            "environment_lock_identity": _environment_lock_identity(),
            "package_identity": _package_identity(),
            "publication_contract": _publication_contract(),
            "qualification_test_execution": test_execution,
            "repository_identity": _repository_identity(),
            "run_contract": _run_contract(),
            "runtime_identity": _runtime_identity(),
            "source_sha256": source_sha256,
            "test_sha256": test_sha256,
        },
        "report_status": REPORT_STATUS,
        "retained_boundary_tn_micro_owner": "QUALIFIED",
        "route_disposition": "NO_ROUTE_KILLED_OR_PROMOTED_BY_MICROFIXTURE",
        "scope": "MICRO_QUALIFICATION_ONLY",
        "solver_permission": "CODE_BLOCKED",
        "target_d3_d5_metrics": "UNAVAILABLE",
        "target_dynamic_add_owner": (
            "UNAVAILABLE/NO_TARGET_QEC_DYNAMIC_ADD_LOWERING"
        ),
        "target_pair_owner": "UNAVAILABLE/NO_TARGET_QEC_PAIR_LOWERING",
        "target_retained_boundary_tn_owner": (
            "UNAVAILABLE/NO_TARGET_QEC_TN_LOWERING"
        ),
    }
    report["content_sha256"] = sha256_json(report)
    validate_report(report, verify_current_sources=True)
    return report


def canonical_report_bytes(report: Mapping[str, object]) -> bytes:
    return canonical_json_bytes(dict(report))


def _reject_float_token(token: str) -> object:
    raise ValueError(f"floating JSON number is forbidden: {token}")


def _reject_constant(token: str) -> object:
    raise ValueError(f"non-finite JSON constant is forbidden: {token}")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key is forbidden: {key}")
        result[key] = value
    return result


def read_strict_report(path: Path) -> dict[str, object]:
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError("report path is not a regular file")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            raw = stream.read()
    finally:
        os.close(descriptor)
    try:
        text = raw.decode("utf-8", errors="strict")
        value = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_float=_reject_float_token,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("report is not strict UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise ValueError("report root must be an object")
    if raw != canonical_report_bytes(value):
        raise ValueError("report bytes are not canonical compact JSON")
    validate_report(value, verify_current_sources=True)
    return value


def _atomic_publish_exclusive(path: Path, raw: bytes) -> None:
    parent = path.parent.resolve(strict=True)
    destination = parent / path.name
    if os.path.lexists(destination):
        raise FileExistsError(f"refusing to replace existing output: {destination}")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", dir=parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, destination)
        parent_descriptor = os.open(parent, os.O_RDONLY)
        try:
            os.fsync(parent_descriptor)
        finally:
            os.close(parent_descriptor)
    finally:
        temporary.unlink(missing_ok=True)


def publish_report(path: Path) -> dict[str, object]:
    report = build_report()
    _atomic_publish_exclusive(path, canonical_report_bytes(report))
    loaded = read_strict_report(path)
    if loaded != report:
        raise ValueError("strictly reloaded report differs from in-memory report")
    return report


def _report_path_label(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO).as_posix()
    except ValueError:
        return str(resolved)


def build_publication_receipt(
    *,
    report_path: Path,
    report: Mapping[str, object],
    report_test_execution: Mapping[str, object],
) -> dict[str, object]:
    body: dict[str, object] = {
        "_schema": PUBLICATION_RECEIPT_SCHEMA,
        "publication_steps": {
            "exclusive_no_replace_returned": True,
            "file_fsync_completed": True,
            "parent_directory_fsync_completed": True,
            "strict_reload_completed": True,
        },
        "publication_status": "PUBLISHED_STRICT_RELOAD_AND_REPORT_CONTRACT_PASS",
        "report_complete_file_sha256": _sha256_file(report_path),
        "report_content_sha256": report["content_sha256"],
        "report_path": _report_path_label(report_path),
        "report_test_execution": dict(report_test_execution),
    }
    body["content_sha256"] = sha256_json(body)
    return body


def validate_publication_receipt(
    receipt: Mapping[str, object], *, report_path: Path
) -> None:
    if set(receipt) != {
        "_schema",
        "content_sha256",
        "publication_status",
        "publication_steps",
        "report_complete_file_sha256",
        "report_content_sha256",
        "report_path",
        "report_test_execution",
    }:
        raise ValueError("publication receipt key set is invalid")
    if receipt["_schema"] != PUBLICATION_RECEIPT_SCHEMA:
        raise ValueError("publication receipt schema mismatch")
    if receipt["publication_status"] != (
        "PUBLISHED_STRICT_RELOAD_AND_REPORT_CONTRACT_PASS"
    ):
        raise ValueError("publication receipt is not terminally successful")
    if receipt["publication_steps"] != {
        "exclusive_no_replace_returned": True,
        "file_fsync_completed": True,
        "parent_directory_fsync_completed": True,
        "strict_reload_completed": True,
    }:
        raise ValueError("publication step receipt is incomplete")
    report = read_strict_report(report_path)
    if receipt["report_path"] != _report_path_label(report_path):
        raise ValueError("publication receipt report path mismatch")
    if receipt["report_complete_file_sha256"] != _sha256_file(report_path):
        raise ValueError("publication receipt complete-file hash mismatch")
    if receipt["report_content_sha256"] != report["content_sha256"]:
        raise ValueError("publication receipt report-content hash mismatch")
    execution = receipt["report_test_execution"]
    if not isinstance(execution, dict):
        raise TypeError("report test execution receipt must be an object")
    expected_input = sha256_json(
        {
            "report_test_sha256": report["provenance"]["test_sha256"][
                REPORT_INTEGRATION_TEST_FILE
            ],
            "source_sha256": report["provenance"]["source_sha256"],
            "python_executable": report["provenance"]["runtime_identity"][
                "python_executable"
            ],
            "pytest_version": report["provenance"]["runtime_identity"][
                "pytest_version"
            ],
        }
    )
    execution_body = {
        key: value for key, value in execution.items() if key != "receipt_sha256"
    }
    if execution != {
        **execution_body,
        "receipt_sha256": sha256_json(execution_body),
    }:
        raise ValueError("report test execution receipt hash mismatch")
    if execution_body != {
        "command": [
            "python",
            "-m",
            "pytest",
            "-q",
            REPORT_INTEGRATION_TEST_FILE,
        ],
        "input_identity_sha256": expected_input,
        "passed_count": 7,
        "return_code": 0,
        "status": "PASS",
        "test_file": REPORT_INTEGRATION_TEST_FILE,
    }:
        raise ValueError("report integration test execution mismatch")
    content_body = {
        key: value for key, value in receipt.items() if key != "content_sha256"
    }
    if receipt["content_sha256"] != sha256_json(content_body):
        raise ValueError("publication receipt content hash mismatch")


def read_strict_publication_receipt(
    path: Path, *, report_path: Path
) -> dict[str, object]:
    raw = path.read_bytes()
    try:
        value = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_unique_object,
            parse_float=_reject_float_token,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("publication receipt is not strict UTF-8 JSON") from exc
    if not isinstance(value, dict) or raw != canonical_json_bytes(value):
        raise ValueError("publication receipt is not canonical compact JSON")
    validate_publication_receipt(value, report_path=report_path)
    return value


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--receipt", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    report = publish_report(args.out)
    execution = _report_integration_test_execution(
        report["provenance"]["source_sha256"],
        report["provenance"]["test_sha256"],
    )
    receipt_path = args.receipt or args.out.with_name("publication_receipt.json")
    publication_receipt = build_publication_receipt(
        report_path=args.out,
        report=report,
        report_test_execution=execution,
    )
    _atomic_publish_exclusive(
        receipt_path, canonical_json_bytes(publication_receipt)
    )
    loaded_receipt = read_strict_publication_receipt(
        receipt_path, report_path=args.out
    )
    if loaded_receipt != publication_receipt:
        raise ValueError("publication receipt changed after strict reload")
    terminal = {
        "publication_receipt_complete_file_sha256": _sha256_file(receipt_path),
        "publication_receipt_path": _report_path_label(receipt_path),
        "report_complete_file_sha256": _sha256_file(args.out),
        "report_content_sha256": report["content_sha256"],
        "report_path": _report_path_label(args.out),
    }
    sys.stdout.buffer.write(canonical_json_bytes(terminal) + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
