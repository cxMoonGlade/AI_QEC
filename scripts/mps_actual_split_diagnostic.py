#!/usr/bin/env python3
"""Audit the actual Quimb split path used by the restricted qubit MPS routes.

This is an implementation diagnostic, not a production error bound and not a
record-faithfulness certificate.  It deliberately lives outside ``src/**`` and
does not import any external comparison runtime.  Other MPS libraries can read
the neutral fixture JSON in their own fresh process and emit the same neutral
result schema.

The Quimb runner calls the same public operation used by the current restricted
executors::

    mps.gate_(gate, where=support, contract="auto-mps",
              max_bond=max_bond, cutoff=0.0)

While that call is active, the runner observes each rank-revealing
``Tensor.split`` without changing its arguments or return value.  The dense
oracle is separately formulated with an explicit axis permutation and matrix
multiplication.
"""

from __future__ import annotations

import argparse
import ast
from contextlib import contextmanager, nullcontext
import hashlib
import importlib.metadata
import importlib.util
import inspect
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from typing import Any, Iterator, Sequence

import numpy as np


FIXTURE_SCHEMA = "error_coupling_simulator.diagnostics.mps_split_fixture.v1"
RESULT_SCHEMA = "error_coupling_simulator.diagnostics.mps_split_result.v1"
DTYPE = "complex128"
EXPECTED_QUIMB_VERSION = "1.14.0"
EXPECTED_TORCH_VERSION = "2.12.0"
FIDELITY_TOL = 1.0e-10
DISCARD_FRACTION_TOL = 1.0e-10
DEFAULT_RESULT = Path(
    "outputs/simulator_validation/diagnostics/mps_actual_split/result.json"
)
DEFAULT_FIXTURES = Path(
    "outputs/simulator_validation/diagnostics/mps_actual_split/fixtures.json"
)
CLAIM_BOUNDARY = {
    "status": "IMPLEMENTATION_DIAGNOSTIC_ONLY",
    "production_error_bound": False,
    "record_faithfulness": False,
    "external_library_equivalence": False,
    "notes": (
        "Per-split discarded weights and final-state fidelity describe only the "
        "declared 4-6-qubit fixtures. They do not bound a multi-operation or "
        "multi-round record law."
    ),
}
REPO_BINDINGS = (
    Path("scripts/mps_actual_split_diagnostic.py"),
    Path("tests/test_mps_actual_split_diagnostic.py"),
    Path("src/error_coupling_simulator/frontend/axis1_qt_mps_execution.py"),
    Path("src/error_coupling_simulator/frontend/axis1_mcwf_mps_execution.py"),
    Path("tests/harness/proc.py"),
    Path("tests/harness/gpu_pool.py"),
    Path("pyproject.toml"),
    Path("core-environment-cu130.lock"),
    Path("uv.lock"),
)
_HARNESS_MODULES: dict[str, Any] = {}


def canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _complex_array_payload(array: np.ndarray | Sequence[complex]) -> dict[str, Any]:
    values = np.asarray(array, dtype=np.complex128)
    flat = values.reshape(-1)
    return {
        "dtype": DTYPE,
        "shape": list(values.shape),
        "real": [float(value) for value in flat.real],
        "imag": [float(value) for value in flat.imag],
    }


def _complex_array_from_payload(
    payload: dict[str, Any], *, field: str
) -> np.ndarray:
    if not isinstance(payload, dict):
        raise ValueError(f"{field} must be an object")
    if payload.get("dtype") != DTYPE:
        raise ValueError(f"{field}.dtype must be {DTYPE!r}")
    shape_raw = payload.get("shape")
    if (
        not isinstance(shape_raw, list)
        or not shape_raw
        or any(not isinstance(dim, int) or isinstance(dim, bool) or dim <= 0 for dim in shape_raw)
    ):
        raise ValueError(f"{field}.shape must contain positive integer dimensions")
    size = math.prod(shape_raw)
    real = payload.get("real")
    imag = payload.get("imag")
    if not isinstance(real, list) or not isinstance(imag, list):
        raise ValueError(f"{field}.real and .imag must be lists")
    if len(real) != size or len(imag) != size:
        raise ValueError(f"{field} payload length does not match shape")
    try:
        values = np.asarray(real, dtype=np.float64) + 1j * np.asarray(
            imag, dtype=np.float64
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} contains non-numeric data") from exc
    if not np.all(np.isfinite(values.real)) or not np.all(np.isfinite(values.imag)):
        raise ValueError(f"{field} contains non-finite data")
    return values.astype(np.complex128, copy=False).reshape(tuple(shape_raw))


def _canonical_hash(payload: dict[str, Any], *, hash_field: str) -> str:
    unhashed = {key: value for key, value in payload.items() if key != hash_field}
    return sha256_bytes(canonical_json_bytes(unhashed))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git_output(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ("git", *args),
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def execution_provenance(*, require_committed_script: bool = True) -> dict[str, Any]:
    """Bind a run to the committed diagnostic, owners, and environment locks."""

    script_path = Path(__file__).resolve()
    repo_root = Path(_git_output(script_path.parent, "rev-parse", "--show-toplevel"))
    try:
        relative_script = script_path.relative_to(repo_root)
    except ValueError as exc:
        raise RuntimeError("diagnostic script is outside the Git repository") from exc
    if relative_script != REPO_BINDINGS[0]:
        raise RuntimeError(
            f"diagnostic import origin is {relative_script}, expected {REPO_BINDINGS[0]}"
        )
    missing = [path.as_posix() for path in REPO_BINDINGS if not (repo_root / path).is_file()]
    if missing:
        raise RuntimeError(f"missing diagnostic binding files: {missing}")
    binding_status = _git_output(
        repo_root,
        "status",
        "--short",
        "--untracked-files=all",
        "--",
        *(path.as_posix() for path in REPO_BINDINGS),
    )
    if require_committed_script and binding_status:
        raise RuntimeError(
            "nontrivial diagnostic requires committed clean binding files; "
            f"git status is {binding_status!r}"
        )
    tracked: dict[str, bool] = {}
    for path in REPO_BINDINGS:
        try:
            _git_output(repo_root, "ls-files", "--error-unmatch", path.as_posix())
            tracked[path.as_posix()] = True
        except subprocess.CalledProcessError:
            tracked[path.as_posix()] = False
    if require_committed_script and not all(tracked.values()):
        raise RuntimeError("one or more diagnostic binding files are not tracked by Git")
    return {
        "git_commit": _git_output(repo_root, "rev-parse", "HEAD"),
        "binding_files_tracked": tracked,
        "binding_files_git_status": binding_status,
        "binding_file_sha256": {
            path.as_posix(): _sha256_file(repo_root / path) for path in REPO_BINDINGS
        },
        "full_git_status_porcelain": _git_output(
            repo_root, "status", "--short", "--untracked-files=all"
        ).splitlines(),
    }


def mcwf_corr_relax_bypass_witness(repo_root: Path | None = None) -> dict[str, Any]:
    """Statically bind the current CORR_RELAX path's explicit cap bypass.

    This does not claim that a capped CORR_RELAX operation ran.  It proves the
    opposite current implementation fact: both two-site no-jump and jump
    candidate applications in ``_sample_joint_jump_or_nojump`` explicitly pass
    ``max_bond=None``.
    """

    root = (
        Path(repo_root).resolve()
        if repo_root is not None
        else Path(__file__).resolve().parents[1]
    )
    relative = Path(
        "src/error_coupling_simulator/frontend/axis1_mcwf_mps_execution.py"
    )
    source_path = root / relative
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=relative.as_posix())

    families_include_corr_relax = False
    target_function: ast.FunctionDef | None = None
    joint_operator_has_corr_relax = False
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(
                isinstance(target, ast.Name)
                and target.id == "TWO_SITE_COLLAPSE_FAMILIES"
                for target in targets
            ):
                families_include_corr_relax = "CORR_RELAX" in ast.unparse(node)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == "_sample_joint_jump_or_nojump":
                target_function = node
            elif node.name == "_joint_collapse_operator":
                joint_operator_has_corr_relax = "CORR_RELAX" in ast.unparse(node)
    if target_function is None:
        raise RuntimeError("MCWF source has no _sample_joint_jump_or_nojump function")

    call_sites: list[dict[str, Any]] = []
    for node in ast.walk(target_function):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "gate_":
            continue
        keywords = {keyword.arg: keyword.value for keyword in node.keywords if keyword.arg}
        max_bond = keywords.get("max_bond")
        contract = keywords.get("contract")
        if (
            isinstance(max_bond, ast.Constant)
            and max_bond.value is None
            and isinstance(contract, ast.Constant)
            and contract.value == "auto-mps"
        ):
            call_sites.append(
                {
                    "line": int(node.lineno),
                    "contract": "auto-mps",
                    "max_bond": None,
                }
            )
    call_sites.sort(key=lambda item: item["line"])
    passed = (
        families_include_corr_relax
        and joint_operator_has_corr_relax
        and len(call_sites) == 2
    )
    if not passed:
        raise RuntimeError(
            "current MCWF CORR_RELAX cap-bypass witness did not match the expected "
            "two explicit max_bond=None auto-mps call sites"
        )
    return {
        "status": "OBSERVED_CURRENT_PRODUCTION_BYPASS",
        "operator_family": "CORR_RELAX",
        "source_path": relative.as_posix(),
        "source_sha256": _sha256_file(source_path),
        "function": "_sample_joint_jump_or_nojump",
        "two_site_family_registry_contains_corr_relax": True,
        "joint_operator_branch_contains_corr_relax": True,
        "call_sites": call_sites,
        "current_max_bond_forwarding": None,
        "capped_fixture_relation": "HYPOTHETICAL_COUNTERFACTUAL_ONLY",
    }


def _product_dense(local_factors: Sequence[np.ndarray]) -> np.ndarray:
    out = np.asarray([1.0 + 0.0j], dtype=np.complex128)
    for factor in local_factors:
        out = np.kron(out, np.asarray(factor, dtype=np.complex128))
    return out


def _cnot() -> np.ndarray:
    return np.asarray(
        [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]],
        dtype=np.complex128,
    )


def _corr_relax_jump() -> np.ndarray:
    sigma_minus = np.asarray([[0, 1], [0, 0]], dtype=np.complex128)
    identity = np.eye(2, dtype=np.complex128)
    return np.kron(sigma_minus, identity) + np.kron(identity, sigma_minus)


def _fixture(
    *,
    fixture_id: str,
    local_factors: Sequence[np.ndarray],
    operator: np.ndarray,
    support: tuple[int, int],
    max_bond: int,
    operation_semantics: str,
    expected_split_path: str,
    route_relation: str,
) -> dict[str, Any]:
    initial = _product_dense(local_factors)
    distance = abs(int(support[1]) - int(support[0]))
    expected_split_count = 2 * max(0, distance - 1) + 1
    capped = int(max_bond) == 1
    return {
        "fixture_id": fixture_id,
        "num_sites": len(local_factors),
        "local_dimension": 2,
        "qubit_order": "site_0_most_significant_big_endian",
        "operation_semantics": operation_semantics,
        "route_relation": route_relation,
        "expected_split_path": expected_split_path,
        "support": list(support),
        "max_bond": int(max_bond),
        "cutoff": 0.0,
        "cutoff_mode": "rsum2",
        "cutoff_mode_source": "quimb_open_boundary_default_made_explicit",
        "initial_product_factors": [
            _complex_array_payload(np.asarray(factor, dtype=np.complex128))
            for factor in local_factors
        ],
        "initial_dense_state": _complex_array_payload(initial),
        "two_site_operator": _complex_array_payload(operator),
        "expected_runtime_acceptance": {
            "actual_split_count": expected_split_count,
            "normalized_state_fidelity": 0.5 if capped else 1.0,
            "normalized_state_fidelity_abs_tolerance": FIDELITY_TOL,
            "worst_discarded_weight_fraction": 0.5 if capped else 0.0,
            "worst_discarded_weight_fraction_abs_tolerance": DISCARD_FRACTION_TOL,
            "requires_positive_discard": capped,
        },
        "value_provenance": "project-design",
    }


def build_default_fixture_manifest() -> dict[str, Any]:
    """Build deterministic adjacent, nonadjacent, and collapse-jump fixtures."""

    zero = np.asarray([1.0, 0.0], dtype=np.complex128)
    one = np.asarray([0.0, 1.0], dtype=np.complex128)
    plus = np.asarray([1.0, 1.0], dtype=np.complex128) / math.sqrt(2.0)

    adjacent_factors = (zero, plus, zero, zero)
    nonadjacent_factors = (plus, zero, zero, zero, zero)
    jump_factors = (zero, zero, one, one, zero, zero)

    fixtures: list[dict[str, Any]] = []
    for suffix, cap in (("cap1", 1), ("exact_cap", 8)):
        fixtures.append(
            _fixture(
                fixture_id=f"adjacent_cnot_4q_{suffix}",
                local_factors=adjacent_factors,
                operator=_cnot(),
                support=(1, 2),
                max_bond=cap,
                operation_semantics="adjacent_two_site_unitary_gate",
                expected_split_path="one_gate_split",
                route_relation="DIRECT_QUBIT_AUTO_MPS_CAP_DIAGNOSTIC",
            )
        )
        fixtures.append(
            _fixture(
                fixture_id=f"nonadjacent_cnot_5q_{suffix}",
                local_factors=nonadjacent_factors,
                operator=_cnot(),
                support=(0, 4),
                max_bond=cap,
                operation_semantics="nonadjacent_two_site_unitary_gate",
                expected_split_path="forward_swaps_gate_split_reverse_swaps",
                route_relation="DIRECT_QUBIT_AUTO_MPS_CAP_DIAGNOSTIC",
            )
        )
        fixtures.append(
            _fixture(
                fixture_id=f"corr_relax_bell_jump_6q_{suffix}",
                local_factors=jump_factors,
                operator=_corr_relax_jump(),
                support=(2, 3),
                max_bond=cap,
                operation_semantics=(
                    "hypothetical_capped_corr_relax_jump_candidate_"
                    "c_equals_smI_plus_Ism"
                ),
                expected_split_path="one_gate_split",
                route_relation="HYPOTHETICAL_COUNTERFACTUAL_CURRENT_MCWF_BYPASSES_CAP",
            )
        )

    manifest: dict[str, Any] = {
        "schema": FIXTURE_SCHEMA,
        "dtype": DTYPE,
        "fixture_count": len(fixtures),
        "fixtures": fixtures,
        "neutral_exchange_contract": {
            "consumer_process": "fresh_process_per_library_runtime",
            "required_result_schema": RESULT_SCHEMA,
            "array_encoding": "row_major_flat_real_imag_with_explicit_shape",
            "runtime_co_loading": False,
            "strict_join_required_before_cross_library_claim": True,
        },
        "production_route_witness_contract": {
            "CORR_RELAX": (
                "source-bound current MCWF bypass witness; capped fixtures are "
                "hypothetical counterfactual probes"
            )
        },
        "claim_boundary": CLAIM_BOUNDARY,
    }
    manifest["content_hash_sha256"] = _canonical_hash(
        manifest, hash_field="content_hash_sha256"
    )
    validate_fixture_manifest(manifest)
    return manifest


def validate_fixture_manifest(manifest: dict[str, Any]) -> None:
    if not isinstance(manifest, dict) or manifest.get("schema") != FIXTURE_SCHEMA:
        raise ValueError(f"fixture schema must be {FIXTURE_SCHEMA!r}")
    if manifest.get("dtype") != DTYPE:
        raise ValueError(f"fixture dtype must be {DTYPE!r}")
    if manifest.get("claim_boundary") != CLAIM_BOUNDARY:
        raise ValueError("fixture manifest claim boundary must remain implementation-only")
    exchange = manifest.get("neutral_exchange_contract")
    if not isinstance(exchange, dict) or exchange.get("runtime_co_loading") is not False:
        raise ValueError("fixture exchange contract must forbid runtime co-loading")
    if exchange.get("strict_join_required_before_cross_library_claim") is not True:
        raise ValueError("fixture exchange contract must require strict result joining")
    if exchange.get("consumer_process") != "fresh_process_per_library_runtime":
        raise ValueError("fixture exchange contract must require a fresh library process")
    if exchange.get("required_result_schema") != RESULT_SCHEMA:
        raise ValueError("fixture exchange contract names the wrong result schema")
    witness_contract = manifest.get("production_route_witness_contract")
    if not isinstance(witness_contract, dict) or "hypothetical" not in str(
        witness_contract.get("CORR_RELAX", "")
    ):
        raise ValueError("fixture manifest lacks the CORR_RELAX bypass contract")
    fixtures = manifest.get("fixtures")
    if not isinstance(fixtures, list) or not fixtures:
        raise ValueError("fixtures must be a nonempty list")
    if manifest.get("fixture_count") != len(fixtures):
        raise ValueError("fixture_count does not match fixtures")
    identifiers: set[str] = set()
    for index, fixture in enumerate(fixtures):
        field = f"fixtures[{index}]"
        if not isinstance(fixture, dict):
            raise ValueError(f"{field} must be an object")
        fixture_id = fixture.get("fixture_id")
        if not isinstance(fixture_id, str) or not fixture_id:
            raise ValueError(f"{field}.fixture_id must be a nonempty string")
        if fixture_id in identifiers:
            raise ValueError(f"duplicate fixture_id {fixture_id!r}")
        identifiers.add(fixture_id)
        n = fixture.get("num_sites")
        if not isinstance(n, int) or isinstance(n, bool) or not 4 <= n <= 6:
            raise ValueError(f"{field}.num_sites must be an integer in [4, 6]")
        if fixture.get("local_dimension") != 2:
            raise ValueError(f"{field}.local_dimension must be 2")
        support = fixture.get("support")
        if (
            not isinstance(support, list)
            or len(support) != 2
            or any(not isinstance(q, int) or isinstance(q, bool) for q in support)
            or support[0] == support[1]
            or any(q < 0 or q >= n for q in support)
        ):
            raise ValueError(f"{field}.support must name two distinct valid sites")
        max_bond = fixture.get("max_bond")
        if max_bond not in (1, 8) or isinstance(max_bond, bool):
            raise ValueError(f"{field}.max_bond must be the cap-1 or exact-cap-8 probe")
        expected_suffix = "cap1" if max_bond == 1 else "exact_cap"
        if not fixture_id.endswith(expected_suffix):
            raise ValueError(f"{field}.fixture_id does not match its cap class")
        if fixture.get("cutoff") != 0.0:
            raise ValueError(f"{field}.cutoff must be the current explicit 0.0")
        if fixture.get("cutoff_mode") != "rsum2":
            raise ValueError(
                f"{field}.cutoff_mode must make Quimb's open-boundary rsum2 default explicit"
            )
        if fixture.get("cutoff_mode_source") != (
            "quimb_open_boundary_default_made_explicit"
        ):
            raise ValueError(f"{field}.cutoff_mode_source is not the frozen contract")
        route_relation = fixture.get("route_relation")
        if not isinstance(route_relation, str) or not route_relation:
            raise ValueError(f"{field}.route_relation must be explicit")
        is_corr_relax = "corr_relax" in str(fixture.get("operation_semantics", ""))
        if is_corr_relax and route_relation != (
            "HYPOTHETICAL_COUNTERFACTUAL_CURRENT_MCWF_BYPASSES_CAP"
        ):
            raise ValueError(f"{field} CORR_RELAX cap fixture must be labelled hypothetical")
        if not is_corr_relax and route_relation != "DIRECT_QUBIT_AUTO_MPS_CAP_DIAGNOSTIC":
            raise ValueError(f"{field} direct MPS fixture relation is invalid")
        if fixture.get("value_provenance") != "project-design":
            raise ValueError(f"{field}.value_provenance must be project-design")
        expected = fixture.get("expected_runtime_acceptance")
        expected_count = 2 * max(0, abs(int(support[1]) - int(support[0])) - 1) + 1
        if not isinstance(expected, dict) or expected.get("actual_split_count") != expected_count:
            raise ValueError(f"{field}.expected_runtime_acceptance split count is wrong")
        expected_fidelity = 0.5 if max_bond == 1 else 1.0
        expected_fraction = 0.5 if max_bond == 1 else 0.0
        if expected.get("normalized_state_fidelity") != expected_fidelity:
            raise ValueError(f"{field} expected fidelity does not match its cap class")
        if expected.get("worst_discarded_weight_fraction") != expected_fraction:
            raise ValueError(f"{field} expected discarded fraction does not match its cap class")
        if expected.get("requires_positive_discard") is not (max_bond == 1):
            raise ValueError(f"{field} positive-discard expectation does not match its cap class")
        if expected.get("normalized_state_fidelity_abs_tolerance") != FIDELITY_TOL:
            raise ValueError(f"{field} fidelity tolerance does not match the frozen gate")
        if (
            expected.get("worst_discarded_weight_fraction_abs_tolerance")
            != DISCARD_FRACTION_TOL
        ):
            raise ValueError(f"{field} discarded-fraction tolerance does not match the frozen gate")
        factors_raw = fixture.get("initial_product_factors")
        if not isinstance(factors_raw, list) or len(factors_raw) != n:
            raise ValueError(f"{field}.initial_product_factors must have num_sites entries")
        factors = [
            _complex_array_from_payload(value, field=f"{field}.initial_product_factors")
            for value in factors_raw
        ]
        if any(value.shape != (2,) for value in factors):
            raise ValueError(f"{field}.initial product factors must each have shape [2]")
        initial = _complex_array_from_payload(
            fixture.get("initial_dense_state"), field=f"{field}.initial_dense_state"
        )
        if initial.shape != (2**n,):
            raise ValueError(f"{field}.initial_dense_state has wrong shape")
        if not np.array_equal(initial, _product_dense(factors)):
            raise ValueError(f"{field}.initial dense state does not match product factors")
        if not math.isclose(float(np.vdot(initial, initial).real), 1.0, abs_tol=1.0e-14):
            raise ValueError(f"{field}.initial state must be normalized")
        operator = _complex_array_from_payload(
            fixture.get("two_site_operator"), field=f"{field}.two_site_operator"
        )
        if operator.shape != (4, 4):
            raise ValueError(f"{field}.two_site_operator must have shape [4, 4]")
    expected_hash = _canonical_hash(manifest, hash_field="content_hash_sha256")
    if manifest.get("content_hash_sha256") != expected_hash:
        raise ValueError("fixture manifest content hash mismatch")


def load_fixture_manifest(path: Path) -> dict[str, Any]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"could not read fixture manifest {path}") from exc
    validate_fixture_manifest(manifest)
    return manifest


def apply_two_site_dense(
    state: np.ndarray,
    operator: np.ndarray,
    *,
    support: tuple[int, int],
    num_sites: int,
) -> np.ndarray:
    """Independent big-endian dense application for an ordered two-site support."""

    state = np.asarray(state, dtype=np.complex128)
    operator = np.asarray(operator, dtype=np.complex128)
    if state.shape != (2**num_sites,) or operator.shape != (4, 4):
        raise ValueError("state or operator shape does not match the declared qubit fixture")
    if len(set(support)) != 2 or any(q < 0 or q >= num_sites for q in support):
        raise ValueError("support must name two distinct valid sites")
    rest = tuple(q for q in range(num_sites) if q not in support)
    permutation = tuple(support) + rest
    inverse = np.argsort(permutation)
    front = np.transpose(state.reshape((2,) * num_sites), permutation).reshape(4, -1)
    acted = (operator @ front).reshape((2, 2) + (2,) * len(rest))
    return np.transpose(acted, inverse).reshape(-1)


def _normalized(array: np.ndarray) -> tuple[np.ndarray, float]:
    values = np.asarray(array, dtype=np.complex128).reshape(-1)
    norm = float(np.linalg.norm(values))
    if not math.isfinite(norm) or norm <= 0.0:
        raise ValueError("state has non-positive or non-finite norm")
    return values / norm, norm


def _state_metrics(reference: np.ndarray, candidate: np.ndarray) -> dict[str, float]:
    ref, ref_norm = _normalized(reference)
    got, got_norm = _normalized(candidate)
    overlap = np.vdot(ref, got)
    fidelity = min(1.0, max(0.0, float(abs(overlap) ** 2)))
    phase = overlap / abs(overlap) if abs(overlap) > 0.0 else 1.0 + 0.0j
    phase_aligned = float(np.linalg.norm(ref - np.conjugate(phase) * got))
    return {
        "reference_raw_norm": ref_norm,
        "candidate_raw_norm": got_norm,
        "normalized_state_fidelity": fidelity,
        "pure_state_trace_distance": math.sqrt(max(0.0, 1.0 - fidelity)),
        "phase_aligned_l2": phase_aligned,
    }


def _schmidt_records(state: np.ndarray, *, num_sites: int, max_bond: int) -> list[dict[str, Any]]:
    normalized, _ = _normalized(state)
    records: list[dict[str, Any]] = []
    for cut in range(1, num_sites):
        singular_values = np.linalg.svd(
            normalized.reshape(2**cut, 2 ** (num_sites - cut)),
            compute_uv=False,
        )
        weights = np.square(np.abs(singular_values))
        kept = min(int(max_bond), int(singular_values.size))
        records.append(
            {
                "cut_index": cut,
                "pre_truncation_rank": int(np.count_nonzero(singular_values > 1.0e-14)),
                "svd_vector_length": int(singular_values.size),
                "kept_rank_cap": kept,
                "discarded_weight_fraction_at_cap": float(np.sum(weights[kept:])),
                "total_schmidt_weight": float(np.sum(weights)),
                "singular_values": [float(value) for value in singular_values],
            }
        )
    return records


def _shared_bond_dimension(split_output: Any) -> int | None:
    if not isinstance(split_output, tuple) or len(split_output) != 2:
        return None
    left, right = split_output
    common = [index for index in left.inds if index in set(right.inds)]
    if len(common) != 1:
        return None
    return int(left.ind_size(common[0]))


@contextmanager
def _observe_actual_quimb_splits() -> Iterator[list[dict[str, Any]]]:
    """Observe actual ``Tensor.split`` calls while preserving their semantics."""

    import quimb.tensor as qtn

    records: list[dict[str, Any]] = []
    original = qtn.Tensor.split

    def observed(tensor, left_inds, *args, **kwargs):
        max_bond = kwargs.get("max_bond")
        singular_values: np.ndarray | None = None
        if max_bond is not None:
            right_inds = kwargs.get("right_inds")
            values = original(
                tensor,
                left_inds,
                right_inds=right_inds,
                method="svd",
                get="values",
            )
            singular_values = np.asarray(
                values.detach().cpu().numpy() if hasattr(values, "detach") else values,
                dtype=np.float64,
            ).reshape(-1)

        output = original(tensor, left_inds, *args, **kwargs)
        if singular_values is not None:
            kept_rank = _shared_bond_dimension(output)
            if kept_rank is None:
                kept_rank = min(int(max_bond), int(singular_values.size))
            weights = np.square(np.abs(singular_values))
            discarded = float(np.sum(weights[kept_rank:]))
            total = float(np.sum(weights))
            records.append(
                {
                    "sequence_index": len(records),
                    "requested_method": str(kwargs.get("method", "auto")),
                    "requested_absorb": str(kwargs.get("absorb", "auto")),
                    "requested_max_bond": int(max_bond),
                    "requested_cutoff": float(kwargs.get("cutoff", 1.0e-10)),
                    "requested_cutoff_mode": str(kwargs.get("cutoff_mode", "rel")),
                    "requested_renorm": kwargs.get("renorm"),
                    "pre_split_singular_values": [float(value) for value in singular_values],
                    "pre_split_total_weight": total,
                    "actual_kept_rank": int(kept_rank),
                    "actual_discarded_weight_raw": discarded,
                    "actual_discarded_weight_fraction_of_pre_split": (
                        discarded / total if total > 0.0 else 0.0
                    ),
                }
            )
        return output

    qtn.Tensor.split = observed
    try:
        yield records
    finally:
        qtn.Tensor.split = original


def _label_split_roles(
    records: list[dict[str, Any]], *, support: tuple[int, int]
) -> None:
    distance = abs(int(support[1]) - int(support[0]))
    expected = 2 * max(0, distance - 1) + 1
    for index, record in enumerate(records):
        if len(records) != expected:
            role = "unclassified_runtime_path"
        elif index < distance - 1:
            role = "forward_swap_split"
        elif index == distance - 1:
            role = "two_site_operator_split"
        else:
            role = "reverse_swap_split"
        record["inferred_path_role"] = role


def _as_numpy(array: Any) -> np.ndarray:
    if hasattr(array, "detach"):
        array = array.detach().cpu().numpy()
    return np.asarray(array, dtype=np.complex128)


def _runtime_identity(*, device: str) -> dict[str, Any]:
    import quimb
    import quimb.tensor as qtn
    import torch

    quimb_version = importlib.metadata.version("quimb")
    torch_version = importlib.metadata.version("torch")
    gate_source = Path(inspect.getsourcefile(qtn.MatrixProductState.gate_with_auto_swap) or "")
    if not gate_source.is_file():
        raise RuntimeError("could not bind Quimb gate_with_auto_swap source file")
    requested = torch.device(device)
    if requested.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA diagnostic requested but torch.cuda.is_available() is false")
    if quimb_version != EXPECTED_QUIMB_VERSION or torch_version != EXPECTED_TORCH_VERSION:
        raise RuntimeError(
            "runtime pin mismatch: "
            f"quimb={quimb_version!r} torch={torch_version!r}, expected "
            f"{EXPECTED_QUIMB_VERSION!r}/{EXPECTED_TORCH_VERSION!r}"
        )
    identity: dict[str, Any] = {
        "quimb_version": quimb_version,
        "quimb_import_origin": str(Path(quimb.__file__).resolve()),
        "quimb_gate_source": str(gate_source.resolve()),
        "quimb_gate_source_sha256": _sha256_file(gate_source),
        "torch_version": torch_version,
        "torch_cuda_runtime": str(torch.version.cuda),
        "requested_device": str(requested),
        "python": platform.python_version(),
        "python_executable": str(Path(sys.executable).resolve()),
        "python_prefix": str(Path(sys.prefix).resolve()),
        "process_id": os.getpid(),
        "parent_process_id": os.getppid(),
        "ECS_GPU_SLOT": os.environ.get("ECS_GPU_SLOT"),
        "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES"),
    }
    if requested.type == "cuda":
        if os.environ.get("ECS_GPU_SLOT") is None:
            raise RuntimeError("CUDA worker has no inherited ECS GPU lease marker")
        identity.update(
            {
                "cuda_device_name": torch.cuda.get_device_name(requested),
                "cuda_device_capability": list(torch.cuda.get_device_capability(requested)),
                "canonical_current_route_runtime": True,
            }
        )
    else:
        identity["canonical_current_route_runtime"] = False
    return identity


def _case_runtime_acceptance(
    fixture: dict[str, Any],
    *,
    metrics: dict[str, float],
    split_records: list[dict[str, Any]],
    tensor_runtime_ok: bool,
) -> dict[str, Any]:
    expected = fixture["expected_runtime_acceptance"]
    fractions = [
        float(record["actual_discarded_weight_fraction_of_pre_split"])
        for record in split_records
    ]
    worst_fraction = max(fractions, default=0.0)
    fidelity = float(metrics["normalized_state_fidelity"])
    checks = {
        "nonzero_split_ledger": len(split_records) > 0,
        "expected_split_count": len(split_records) == int(expected["actual_split_count"]),
        "explicit_rsum2_cutoff_mode": bool(split_records)
        and all(record["requested_cutoff_mode"] == "rsum2" for record in split_records),
        "torch_complex128_requested_device": bool(tensor_runtime_ok),
        "expected_normalized_state_fidelity": abs(
            fidelity - float(expected["normalized_state_fidelity"])
        )
        <= float(expected["normalized_state_fidelity_abs_tolerance"]),
        "expected_worst_discarded_weight_fraction": abs(
            worst_fraction - float(expected["worst_discarded_weight_fraction"])
        )
        <= float(expected["worst_discarded_weight_fraction_abs_tolerance"]),
        "positive_discard_requirement": (
            worst_fraction > DISCARD_FRACTION_TOL
            if bool(expected["requires_positive_discard"])
            else worst_fraction <= DISCARD_FRACTION_TOL
        ),
    }
    return {
        "passed": all(checks.values()),
        "verdict": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "observed_normalized_state_fidelity": fidelity,
        "observed_worst_discarded_weight_fraction": worst_fraction,
        "expected": expected,
    }


def run_quimb_fixture(fixture: dict[str, Any], *, device: str) -> dict[str, Any]:
    """Execute one fixture through Quimb's actual auto-swap/split path."""

    import quimb.tensor as qtn
    import torch

    n = int(fixture["num_sites"])
    support = tuple(int(q) for q in fixture["support"])
    max_bond = int(fixture["max_bond"])
    factors_np = [
        _complex_array_from_payload(value, field="initial_product_factors")
        for value in fixture["initial_product_factors"]
    ]
    initial = _complex_array_from_payload(
        fixture["initial_dense_state"], field="initial_dense_state"
    ).reshape(-1)
    operator = _complex_array_from_payload(
        fixture["two_site_operator"], field="two_site_operator"
    )
    dense_target = apply_two_site_dense(
        initial, operator, support=support, num_sites=n
    )

    factors = [
        torch.as_tensor(value, dtype=torch.complex128, device=device)
        for value in factors_np
    ]
    gate = torch.as_tensor(operator, dtype=torch.complex128, device=device)
    mps = qtn.MPS_product_state(factors)
    info: dict[str, Any] = {"cur_orthog": "calc"}
    with _observe_actual_quimb_splits() as split_records:
        mps.gate_(
            gate,
            where=support,
            contract="auto-mps",
            info=info,
            max_bond=max_bond,
            cutoff=0.0,
            cutoff_mode=str(fixture["cutoff_mode"]),
        )
    _label_split_roles(split_records, support=support)

    actual_dense = _as_numpy(mps.to_dense()).reshape(-1)
    exact_schmidt = _schmidt_records(
        dense_target, num_sites=n, max_bond=max_bond
    )
    actual_schmidt = _schmidt_records(
        actual_dense, num_sites=n, max_bond=max_bond
    )
    left, right = sorted(support)
    shadow_scope = [
        record for record in exact_schmidt if left < int(record["cut_index"]) <= right
    ]
    actual_discarded_raw = [
        float(record["actual_discarded_weight_raw"]) for record in split_records
    ]
    actual_discarded_fractions = [
        float(record["actual_discarded_weight_fraction_of_pre_split"])
        for record in split_records
    ]

    tensors_complex128 = all(
        getattr(tensor.data, "dtype", None) == torch.complex128
        for tensor in mps.tensors
    )
    tensors_requested_device = all(
        getattr(tensor.data, "device", torch.device("cpu")).type
        == torch.device(device).type
        for tensor in mps.tensors
    )
    tensor_runtime_ok = bool(tensors_complex128 and tensors_requested_device)
    metrics = _state_metrics(dense_target, actual_dense)
    runtime_acceptance = _case_runtime_acceptance(
        fixture,
        metrics=metrics,
        split_records=split_records,
        tensor_runtime_ok=tensor_runtime_ok,
    )

    try:
        calculated_center = mps.calc_current_orthog_center()
    except Exception as exc:  # diagnostic field only; state evidence remains available
        calculated_center = f"unavailable:{type(exc).__name__}"

    return {
        "fixture_id": fixture["fixture_id"],
        "num_sites": n,
        "support": list(support),
        "max_bond": max_bond,
        "operation_semantics": fixture["operation_semantics"],
        "route_relation": fixture["route_relation"],
        "fixture_sha256": sha256_bytes(canonical_json_bytes(fixture)),
        "dense_reference": {
            "method": "explicit_big_endian_axis_permutation_and_matrix_multiply",
            "normalized_target_state": _complex_array_payload(_normalized(dense_target)[0]),
            "schmidt_records": exact_schmidt,
        },
        "candidate_output": {
            "normalized_state": _complex_array_payload(_normalized(actual_dense)[0]),
            "state_metrics": metrics,
            "bond_dimensions": [
                int(mps.bond_size(site, site + 1)) for site in range(n - 1)
            ],
            "max_observed_bond": int(mps.max_bond()),
            "actual_schmidt_records": actual_schmidt,
            "tensor_runtime": {
                "all_tensors_complex128": bool(tensors_complex128),
                "all_tensors_requested_device": bool(tensors_requested_device),
            },
        },
        "actual_quimb_split_ledger": {
            "method": "runtime_observation_of_actual_tensor_split_inputs_and_outputs",
            "actual_split_count": len(split_records),
            "expected_auto_swap_split_count": 2 * max(0, right - left - 1) + 1,
            "split_records": split_records,
            "actual_discarded_weight_raw_sum": float(sum(actual_discarded_raw)),
            "worst_actual_split_discarded_weight_raw": float(
                max(actual_discarded_raw, default=0.0)
            ),
            "actual_discarded_weight_fraction_sum": float(
                sum(actual_discarded_fractions)
            ),
            "worst_actual_split_discarded_weight_fraction": float(
                max(actual_discarded_fractions, default=0.0)
            ),
            "not_a_global_error_bound": True,
        },
        "shadow_target_cut_diagnostic": {
            "method": "exact_post_operator_dense_state_schmidt_tail",
            "cut_records": shadow_scope,
            "discarded_weight_fraction_sum": float(
                sum(
                    float(record["discarded_weight_fraction_at_cap"])
                    for record in shadow_scope
                )
            ),
            "same_object_as_actual_split_ledger": False,
            "not_a_global_error_bound": True,
        },
        "canonicalization_observation": {
            "gate_info_cur_orthog": _jsonable_center(info.get("cur_orthog")),
            "calculated_current_orthog_center": _jsonable_center(calculated_center),
            "count_canonized": [int(value) for value in mps.count_canonized()],
        },
        "runtime_acceptance": runtime_acceptance,
    }


def _jsonable_center(value: Any) -> Any:
    if isinstance(value, (tuple, list)):
        return [int(item) for item in value]
    if isinstance(value, (int, np.integer)):
        return int(value)
    return str(value)


def _fresh_process_execution_verified(result: dict[str, Any]) -> bool:
    """Return whether parent-side process and GPU-lease evidence closes the run."""

    fresh = result.get("fresh_process_execution")
    runtime = result.get("runtime_identity")
    producer = result.get("producer")
    if not all(isinstance(value, dict) for value in (fresh, runtime, producer)):
        return False
    try:
        process_ok = (
            int(fresh["returncode"]) == 0
            and fresh["timed_out"] is False
            and fresh["process_group_cleanup_verified"] is True
            and int(runtime["process_id"]) == int(fresh["process_group_id"])
        )
    except (KeyError, TypeError, ValueError):
        return False
    if not process_ok:
        return False
    requested = str(runtime.get("requested_device", ""))
    if requested.startswith("cuda"):
        runtime_slot = runtime.get("ECS_GPU_SLOT")
        visible = runtime.get("CUDA_VISIBLE_DEVICES")
        lease_slot = fresh.get("gpu_lease_slot")
        if runtime_slot is None or visible is None or lease_slot is None:
            return False
        if str(runtime_slot) != str(lease_slot) or str(visible) != str(lease_slot):
            return False
    else:
        if fresh.get("gpu_lease_slot") is not None:
            return False
    command = fresh.get("command")
    return bool(
        isinstance(command, list)
        and "--worker" in command
        and producer.get("device") == requested
    )


def _diagnostic_acceptance(
    *, case_checks_passed: bool, canonical_runtime: bool, fresh_process_verified: bool
) -> dict[str, Any]:
    passed = bool(case_checks_passed and canonical_runtime and fresh_process_verified)
    return {
        "case_checks_passed": bool(case_checks_passed),
        "canonical_current_route_runtime": bool(canonical_runtime),
        "fresh_process_execution_verified": bool(fresh_process_verified),
        "passed": passed,
        "verdict": "PASS" if passed else "NOT_ACCEPTED",
    }


def build_quimb_result(
    fixture_manifest: dict[str, Any],
    *,
    device: str,
    fixture_ids: set[str] | None = None,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    validate_fixture_manifest(fixture_manifest)
    selected = [
        fixture
        for fixture in fixture_manifest["fixtures"]
        if fixture_ids is None or fixture["fixture_id"] in fixture_ids
    ]
    if not selected:
        raise ValueError("fixture selection is empty")
    if fixture_ids is not None:
        found = {fixture["fixture_id"] for fixture in selected}
        missing = sorted(fixture_ids - found)
        if missing:
            raise ValueError(f"unknown fixture ids: {missing}")

    runtime_identity = _runtime_identity(device=device)
    cases = [run_quimb_fixture(fixture, device=device) for fixture in selected]
    case_checks_passed = all(case["runtime_acceptance"]["passed"] for case in cases)
    canonical_runtime = bool(runtime_identity["canonical_current_route_runtime"])
    result: dict[str, Any] = {
        "schema": RESULT_SCHEMA,
        "fixture_manifest_sha256": fixture_manifest["content_hash_sha256"],
        "producer": {
            "library": "quimb",
            "library_version": importlib.metadata.version("quimb"),
            "array_backend": "torch",
            "device": str(device),
            "dtype": DTYPE,
            "python": platform.python_version(),
            "execution_class": (
                "canonical_gpu_diagnostic"
                if str(device).startswith("cuda")
                else "noncanonical_cpu_smoke"
            ),
        },
        "runtime_identity": runtime_identity,
        "execution_provenance": provenance,
        "production_route_witness": mcwf_corr_relax_bypass_witness(),
        "selected_fixture_ids": [fixture["fixture_id"] for fixture in selected],
        "case_count": len(cases),
        "cases": cases,
        "aggregate": {
            "minimum_normalized_state_fidelity": float(
                min(
                    case["candidate_output"]["state_metrics"][
                        "normalized_state_fidelity"
                    ]
                    for case in cases
                )
            ),
            "maximum_actual_split_discarded_weight_raw": float(
                max(
                    case["actual_quimb_split_ledger"][
                        "worst_actual_split_discarded_weight_raw"
                    ]
                    for case in cases
                )
            ),
            "maximum_actual_split_discarded_weight_fraction": float(
                max(
                    case["actual_quimb_split_ledger"][
                        "worst_actual_split_discarded_weight_fraction"
                    ]
                    for case in cases
                )
            ),
            "maximum_actual_split_discarded_weight_fraction_sum": float(
                max(
                    case["actual_quimb_split_ledger"][
                        "actual_discarded_weight_fraction_sum"
                    ]
                    for case in cases
                )
            ),
        },
        "diagnostic_acceptance": _diagnostic_acceptance(
            case_checks_passed=case_checks_passed,
            canonical_runtime=canonical_runtime,
            fresh_process_verified=False,
        ),
        "claim_boundary": CLAIM_BOUNDARY,
    }
    result["content_hash_sha256"] = _canonical_hash(
        result, hash_field="content_hash_sha256"
    )
    validate_result_manifest(result, fixture_manifest=fixture_manifest)
    return result


def validate_result_manifest(
    result: dict[str, Any], *, fixture_manifest: dict[str, Any] | None = None
) -> None:
    """Validate a result and, when supplied, strictly join it to its fixtures."""

    if not isinstance(result, dict) or result.get("schema") != RESULT_SCHEMA:
        raise ValueError(f"result schema must be {RESULT_SCHEMA!r}")
    if result.get("claim_boundary") != CLAIM_BOUNDARY:
        raise ValueError("result claim boundary must remain implementation-only")
    fixture_hash = result.get("fixture_manifest_sha256")
    if not isinstance(fixture_hash, str) or len(fixture_hash) != 64:
        raise ValueError("result fixture_manifest_sha256 must be a sha256 hex string")
    try:
        int(fixture_hash, 16)
    except ValueError as exc:
        raise ValueError("result fixture_manifest_sha256 is not hexadecimal") from exc
    producer = result.get("producer")
    if not isinstance(producer, dict) or not isinstance(producer.get("library"), str):
        raise ValueError("result producer.library is required")
    if producer.get("dtype") != DTYPE:
        raise ValueError(f"result producer.dtype must be {DTYPE!r}")
    cases = result.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("result cases must be a nonempty list")
    if result.get("case_count") != len(cases):
        raise ValueError("result case_count does not match cases")
    identifiers: set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"result cases[{index}] must be an object")
        fixture_id = case.get("fixture_id")
        if not isinstance(fixture_id, str) or fixture_id in identifiers:
            raise ValueError("result fixture ids must be nonempty and unique")
        identifiers.add(fixture_id)
        candidate = case.get("candidate_output")
        if not isinstance(candidate, dict):
            raise ValueError("result candidate_output is required")
        normalized = _complex_array_from_payload(
            candidate.get("normalized_state"), field="candidate_output.normalized_state"
        )
        if normalized.shape != (2 ** int(case["num_sites"]),):
            raise ValueError("result candidate normalized state has wrong shape")
        if not math.isclose(float(np.vdot(normalized, normalized).real), 1.0, abs_tol=1.0e-10):
            raise ValueError("result candidate normalized state is not normalized")

    if fixture_manifest is not None:
        validate_fixture_manifest(fixture_manifest)
        if fixture_hash != fixture_manifest["content_hash_sha256"]:
            raise ValueError("result does not join to the supplied fixture manifest hash")
        selected_ids = result.get("selected_fixture_ids")
        if (
            not isinstance(selected_ids, list)
            or not selected_ids
            or len(set(selected_ids)) != len(selected_ids)
        ):
            raise ValueError("strict fixture join requires unique selected_fixture_ids")
        if selected_ids != [case["fixture_id"] for case in cases]:
            raise ValueError("result case order does not match selected_fixture_ids")
        fixture_by_id = {
            fixture["fixture_id"]: fixture for fixture in fixture_manifest["fixtures"]
        }
        unknown = sorted(set(selected_ids) - set(fixture_by_id))
        if unknown:
            raise ValueError(f"result names unknown fixture ids: {unknown}")
        for case in cases:
            fixture = fixture_by_id[case["fixture_id"]]
            expected_case_fields = {
                "num_sites": fixture["num_sites"],
                "support": fixture["support"],
                "max_bond": fixture["max_bond"],
                "operation_semantics": fixture["operation_semantics"],
                "route_relation": fixture["route_relation"],
                "fixture_sha256": sha256_bytes(canonical_json_bytes(fixture)),
            }
            for name, expected in expected_case_fields.items():
                if case.get(name) != expected:
                    raise ValueError(
                        f"result case {case['fixture_id']!r} field {name!r} "
                        "does not join to its fixture"
                    )

        if producer.get("library") == "quimb":
            _validate_quimb_result_extension(result, fixture_by_id)
    expected_hash = _canonical_hash(result, hash_field="content_hash_sha256")
    if result.get("content_hash_sha256") != expected_hash:
        raise ValueError("result content hash mismatch")


def _is_sha256_hex(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _validate_quimb_execution_provenance(result: dict[str, Any]) -> None:
    provenance = result.get("execution_provenance")
    if not isinstance(provenance, dict):
        raise ValueError("Quimb result requires committed execution provenance")
    tracked = provenance.get("binding_files_tracked")
    hashes = provenance.get("binding_file_sha256")
    if not isinstance(tracked, dict) or not isinstance(hashes, dict):
        raise ValueError("Quimb result provenance lacks binding maps")
    required = {path.as_posix() for path in REPO_BINDINGS}
    if not required.issubset(tracked) or not required.issubset(hashes):
        raise ValueError("Quimb result provenance omits required binding files")
    if any(tracked[path] is not True for path in required):
        raise ValueError("Quimb result provenance contains untracked binding files")
    if any(not _is_sha256_hex(hashes[path]) for path in required):
        raise ValueError("Quimb result provenance contains invalid binding hashes")
    if provenance.get("binding_files_git_status") != "":
        raise ValueError("Quimb result binding files were not clean at execution")
    git_commit = provenance.get("git_commit")
    if not isinstance(git_commit, str) or len(git_commit) not in (40, 64):
        raise ValueError("Quimb result provenance has no valid Git commit")
    try:
        int(git_commit, 16)
    except ValueError as exc:
        raise ValueError("Quimb result provenance Git commit is not hexadecimal") from exc


def _validate_quimb_result_extension(
    result: dict[str, Any], fixture_by_id: dict[str, dict[str, Any]]
) -> None:
    _validate_quimb_execution_provenance(result)
    case_passes: list[bool] = []
    for case in result["cases"]:
        fixture = fixture_by_id[case["fixture_id"]]
        ledger = case.get("actual_quimb_split_ledger")
        acceptance = case.get("runtime_acceptance")
        if not isinstance(ledger, dict) or not isinstance(acceptance, dict):
            raise ValueError("Quimb result requires split ledger and runtime acceptance")
        records = ledger.get("split_records")
        if not isinstance(records, list) or not records:
            raise ValueError("Quimb result split ledger must be nonempty")
        if ledger.get("actual_split_count") != len(records):
            raise ValueError("Quimb result split count does not match its records")
        if len(records) != fixture["expected_runtime_acceptance"]["actual_split_count"]:
            raise ValueError("Quimb result split count does not match fixture expectation")
        raw = [float(record["actual_discarded_weight_raw"]) for record in records]
        fractions = [
            float(record["actual_discarded_weight_fraction_of_pre_split"])
            for record in records
        ]
        if any(
            not math.isfinite(value) or value < 0.0
            for value in (*raw, *fractions)
        ):
            raise ValueError("Quimb result contains invalid discarded weights")
        if any(value > 1.0 + DISCARD_FRACTION_TOL for value in fractions):
            raise ValueError("Quimb result discarded fraction exceeds one")
        aggregate_pairs = (
            ("actual_discarded_weight_raw_sum", sum(raw)),
            ("worst_actual_split_discarded_weight_raw", max(raw)),
            ("actual_discarded_weight_fraction_sum", sum(fractions)),
            ("worst_actual_split_discarded_weight_fraction", max(fractions)),
        )
        for name, expected in aggregate_pairs:
            if not math.isclose(
                float(ledger.get(name)), float(expected), rel_tol=0.0, abs_tol=1.0e-14
            ):
                raise ValueError(f"Quimb split ledger aggregate {name!r} is inconsistent")
        candidate = case["candidate_output"]
        tensor_runtime = candidate.get("tensor_runtime")
        if not isinstance(tensor_runtime, dict):
            raise ValueError("Quimb candidate output lacks tensor runtime evidence")
        recomputed_acceptance = _case_runtime_acceptance(
            fixture,
            metrics=candidate["state_metrics"],
            split_records=records,
            tensor_runtime_ok=bool(
                tensor_runtime.get("all_tensors_complex128")
                and tensor_runtime.get("all_tensors_requested_device")
            ),
        )
        if acceptance != recomputed_acceptance:
            raise ValueError("Quimb runtime acceptance does not match recomputed evidence")
        checks = acceptance.get("checks")
        if not isinstance(checks, dict) or not checks or not all(
            isinstance(value, bool) for value in checks.values()
        ):
            raise ValueError("Quimb runtime acceptance checks must be explicit booleans")
        passed = all(checks.values())
        if acceptance.get("passed") is not passed:
            raise ValueError("Quimb runtime acceptance summary is inconsistent")
        if acceptance.get("verdict") != ("PASS" if passed else "FAIL"):
            raise ValueError("Quimb runtime acceptance verdict is inconsistent")
        case_passes.append(passed)
    aggregate = result.get("aggregate")
    if not isinstance(aggregate, dict):
        raise ValueError("Quimb result lacks aggregate evidence")
    expected_aggregate = {
        "minimum_normalized_state_fidelity": min(
            float(case["candidate_output"]["state_metrics"]["normalized_state_fidelity"])
            for case in result["cases"]
        ),
        "maximum_actual_split_discarded_weight_raw": max(
            float(
                case["actual_quimb_split_ledger"][
                    "worst_actual_split_discarded_weight_raw"
                ]
            )
            for case in result["cases"]
        ),
        "maximum_actual_split_discarded_weight_fraction": max(
            float(
                case["actual_quimb_split_ledger"][
                    "worst_actual_split_discarded_weight_fraction"
                ]
            )
            for case in result["cases"]
        ),
        "maximum_actual_split_discarded_weight_fraction_sum": max(
            float(
                case["actual_quimb_split_ledger"][
                    "actual_discarded_weight_fraction_sum"
                ]
            )
            for case in result["cases"]
        ),
    }
    for name, expected in expected_aggregate.items():
        try:
            observed = float(aggregate[name])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Quimb aggregate field {name!r} is invalid") from exc
        if not math.isclose(observed, expected, rel_tol=0.0, abs_tol=1.0e-14):
            raise ValueError(f"Quimb aggregate field {name!r} is inconsistent")
    diagnostic = result.get("diagnostic_acceptance")
    runtime = result.get("runtime_identity")
    if not isinstance(diagnostic, dict) or not isinstance(runtime, dict):
        raise ValueError("Quimb result requires diagnostic acceptance and runtime identity")
    canonical = bool(runtime.get("canonical_current_route_runtime"))
    fresh_verified = _fresh_process_execution_verified(result)
    expected_diagnostic = _diagnostic_acceptance(
        case_checks_passed=all(case_passes),
        canonical_runtime=canonical,
        fresh_process_verified=fresh_verified,
    )
    if diagnostic != expected_diagnostic:
        raise ValueError("Quimb diagnostic acceptance is inconsistent")
    if runtime.get("quimb_version") != EXPECTED_QUIMB_VERSION:
        raise ValueError("Quimb result runtime version does not match the repository pin")
    if runtime.get("torch_version") != EXPECTED_TORCH_VERSION:
        raise ValueError("Quimb result Torch version does not match the repository pin")
    producer = result["producer"]
    if producer.get("library_version") != runtime.get("quimb_version"):
        raise ValueError("Quimb producer and runtime library versions disagree")
    if producer.get("array_backend") != "torch":
        raise ValueError("Quimb diagnostic requires the pinned Torch array backend")
    requested_device = str(runtime.get("requested_device", ""))
    if producer.get("device") != requested_device:
        raise ValueError("Quimb producer and runtime device identities disagree")
    if canonical != requested_device.startswith("cuda"):
        raise ValueError("Quimb canonical runtime flag disagrees with the requested device")
    expected_execution_class = (
        "canonical_gpu_diagnostic"
        if requested_device.startswith("cuda")
        else "noncanonical_cpu_smoke"
    )
    if producer.get("execution_class") != expected_execution_class:
        raise ValueError("Quimb producer execution class disagrees with its device")
    if not isinstance(runtime.get("quimb_import_origin"), str) or not Path(
        runtime["quimb_import_origin"]
    ).is_absolute():
        raise ValueError("Quimb runtime import origin is not absolute")
    if not isinstance(runtime.get("quimb_gate_source"), str) or not Path(
        runtime["quimb_gate_source"]
    ).is_absolute():
        raise ValueError("Quimb gate source origin is not absolute")
    if not _is_sha256_hex(runtime.get("quimb_gate_source_sha256")):
        raise ValueError("Quimb gate source hash is invalid")
    if requested_device.startswith("cuda") and (
        not isinstance(runtime.get("cuda_device_name"), str)
        or not isinstance(runtime.get("cuda_device_capability"), list)
        or runtime.get("ECS_GPU_SLOT") is None
        or runtime.get("CUDA_VISIBLE_DEVICES") is None
    ):
        raise ValueError("Quimb CUDA runtime lacks device and lease identity")
    witness = result.get("production_route_witness")
    call_sites = witness.get("call_sites") if isinstance(witness, dict) else None
    if (
        not isinstance(witness, dict)
        or witness.get("status") != "OBSERVED_CURRENT_PRODUCTION_BYPASS"
        or witness.get("current_max_bond_forwarding", "missing") is not None
        or witness.get("capped_fixture_relation") != "HYPOTHETICAL_COUNTERFACTUAL_ONLY"
        or witness.get("source_path")
        != "src/error_coupling_simulator/frontend/axis1_mcwf_mps_execution.py"
        or not isinstance(call_sites, list)
        or len(call_sites) != 2
        or any(
            not isinstance(site, dict)
            or site.get("contract") != "auto-mps"
            or site.get("max_bond", "missing") is not None
            for site in call_sites
        )
    ):
        raise ValueError("Quimb result lacks the current MCWF CORR_RELAX bypass witness")
    provenance_hashes = result["execution_provenance"]["binding_file_sha256"]
    if witness.get("source_sha256") != provenance_hashes[witness["source_path"]]:
        raise ValueError("MCWF bypass witness is not bound to execution provenance")
    corr_cases = [
        case for case in result["cases"] if "corr_relax" in case["operation_semantics"]
    ]
    if any(
        case["route_relation"]
        != "HYPOTHETICAL_COUNTERFACTUAL_CURRENT_MCWF_BYPASSES_CAP"
        for case in corr_cases
    ):
        raise ValueError("Quimb CORR_RELAX cap cases are not labelled hypothetical")
    fresh = result.get("fresh_process_execution")
    if fresh is not None and not fresh_verified:
        raise ValueError("Quimb fresh-process or GPU-lease evidence is invalid")


def join_result_to_fixtures(
    fixture_manifest: dict[str, Any],
    result: dict[str, Any],
    *,
    require_accepted: bool = True,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Return strictly joined rows; reject unaccepted cross-library evidence."""

    validate_result_manifest(result, fixture_manifest=fixture_manifest)
    if require_accepted and not bool(
        result.get("diagnostic_acceptance", {}).get("passed", False)
    ):
        raise ValueError("result is not accepted for a cross-library claim")
    fixture_by_id = {
        fixture["fixture_id"]: fixture for fixture in fixture_manifest["fixtures"]
    }
    return [
        (fixture_by_id[case["fixture_id"]], case) for case in result["cases"]
    ]


def load_result_manifest(
    path: Path, *, fixture_manifest: dict[str, Any] | None = None
) -> dict[str, Any]:
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"could not read result manifest {path}") from exc
    validate_result_manifest(result, fixture_manifest=fixture_manifest)
    return result


def write_json_atomic(path: Path, payload: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n").encode(
        "utf-8"
    )
    with tempfile.NamedTemporaryFile(
        mode="wb", prefix=f".{path.name}.", dir=path.parent, delete=False
    ) as handle:
        temporary = Path(handle.name)
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return hashlib.sha256(encoded).hexdigest()


def _load_harness_module(name: str):
    if name in _HARNESS_MODULES:
        return _HARNESS_MODULES[name]
    path = Path(__file__).resolve().parents[1] / "tests" / "harness" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"mps_split_{name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load harness module {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _HARNESS_MODULES[name] = module
    return module


def _run_fresh_worker(
    *,
    fixtures_path: Path,
    result_path: Path,
    device: str,
    timeout: float,
    fixture_ids: Sequence[str] | None = None,
) -> dict[str, Any]:
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker",
        "--fixtures-in",
        str(fixtures_path),
        "--result-out",
        str(result_path),
        "--device",
        str(device),
    ]
    for fixture_id in fixture_ids or ():
        command.extend(("--fixture-id", str(fixture_id)))
    proc = _load_harness_module("proc")
    log_path = result_path.with_suffix(result_path.suffix + ".worker.log")
    lease_slot: int | None = None
    inherited_slot = os.environ.get("ECS_GPU_SLOT")
    if device == "cuda":
        if inherited_slot is not None and os.environ.get("CUDA_VISIBLE_DEVICES") is None:
            raise RuntimeError(
                "inherited ECS_GPU_SLOT requires CUDA_VISIBLE_DEVICES for a pinned worker"
            )
        gpu_pool = _load_harness_module("gpu_pool")
        lease_context = (
            nullcontext(None)
            if inherited_slot is not None
            else gpu_pool.acquire_gpu_slot()
        )
    else:
        lease_context = nullcontext(None)
    with lease_context as lease:
        if lease is None:
            child_env = dict(os.environ)
            if device == "cuda":
                lease_slot = int(inherited_slot) if inherited_slot is not None else None
        else:
            lease_slot = int(lease.slot)
            child_env = lease.child_env(dict(os.environ))
        ran = proc.run(
            command,
            cwd=str(Path(__file__).resolve().parents[1]),
            env=child_env,
            timeout=float(timeout),
            log_path=str(log_path),
        )
    execution = {
        "command": command,
        "returncode": int(ran.returncode),
        "timed_out": bool(ran.timed_out),
        "process_group_id": int(ran.pgid),
        "process_group_cleanup_verified": bool(ran.group_cleanup_verified),
        "gpu_lease_slot": lease_slot,
        "inherited_gpu_lease": inherited_slot is not None,
        "log_path": str(log_path),
    }
    if not ran.ok:
        log = log_path.read_text(errors="replace") if log_path.is_file() else ""
        raise RuntimeError(
            f"MPS split worker failed: {execution!r}\n--- worker log ---\n{log[-12000:]}"
        )
    return execution


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="cuda", choices=("cuda", "cpu"))
    parser.add_argument("--fixtures-in", type=Path)
    parser.add_argument("--fixtures-out", type=Path, default=DEFAULT_FIXTURES)
    parser.add_argument("--result-out", type=Path, default=DEFAULT_RESULT)
    parser.add_argument("--timeout", type=float, default=1800.0)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--fixture-id",
        action="append",
        dest="fixture_ids",
        help="Run only this fixture id; may be supplied more than once.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    provenance = execution_provenance(require_committed_script=True)
    if args.worker:
        if args.fixtures_in is None:
            raise RuntimeError("worker mode requires --fixtures-in")
        fixtures = load_fixture_manifest(args.fixtures_in)
        result = build_quimb_result(
            fixtures,
            device=args.device,
            fixture_ids=set(args.fixture_ids) if args.fixture_ids else None,
            provenance=provenance,
        )
        write_json_atomic(args.result_out, result)
        return 0

    fixtures = (
        load_fixture_manifest(args.fixtures_in)
        if args.fixtures_in is not None
        else build_default_fixture_manifest()
    )
    print(f"fixture_schema={FIXTURE_SCHEMA}", flush=True)
    print(f"fixture_manifest_sha256={fixtures['content_hash_sha256']}", flush=True)
    print(f"git_commit={provenance['git_commit']}", flush=True)
    print(f"device={args.device} dtype={DTYPE}", flush=True)
    fixture_bytes_sha = write_json_atomic(args.fixtures_out, fixtures)
    execution = _run_fresh_worker(
        fixtures_path=args.fixtures_out,
        result_path=args.result_out,
        device=args.device,
        timeout=float(args.timeout),
        fixture_ids=args.fixture_ids,
    )
    result = load_result_manifest(args.result_out, fixture_manifest=fixtures)
    result["fresh_process_execution"] = execution
    result["diagnostic_acceptance"] = _diagnostic_acceptance(
        case_checks_passed=all(
            bool(case["runtime_acceptance"]["passed"])
            for case in result["cases"]
        ),
        canonical_runtime=bool(
            result["runtime_identity"]["canonical_current_route_runtime"]
        ),
        fresh_process_verified=_fresh_process_execution_verified(result),
    )
    result["content_hash_sha256"] = _canonical_hash(
        result, hash_field="content_hash_sha256"
    )
    validate_result_manifest(result, fixture_manifest=fixtures)
    result_bytes_sha = write_json_atomic(args.result_out, result)
    print(f"fixtures_out={args.fixtures_out} bytes_sha256={fixture_bytes_sha}", flush=True)
    print(f"result_out={args.result_out} bytes_sha256={result_bytes_sha}", flush=True)
    print(
        "minimum_normalized_state_fidelity="
        f"{result['aggregate']['minimum_normalized_state_fidelity']:.17g}",
        flush=True,
    )
    print(
        f"diagnostic_acceptance={result['diagnostic_acceptance']['verdict']} "
        f"worker_cleanup={execution['process_group_cleanup_verified']}",
        flush=True,
    )
    return 0 if result["diagnostic_acceptance"]["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
