#!/usr/bin/env python3
"""Run only the frozen n=8, active-rank-3 GCAPEPS controls.

The default ``collect`` command performs the NumPy-only corruption controls and
grades separately supplied external-control evidence. It never runs either
clean n=8 candidate. The ``orientation`` and ``gc-construction`` commands are
small external-evidence entry points intended for the supervisor's frozen
Quimb environment; the SDIM worker remains a separate process.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from types import ModuleType
from typing import Any, Mapping, Sequence

import numpy as np


CONTROLS_SCHEMA = (
    "error_coupling_simulator.external."
    "gcapeps_n8_r3_controls_only.v1"
)
ORIENTATION_EVIDENCE_SCHEMA = (
    "error_coupling_simulator.external."
    "gcapeps_n8_r3_one_site_orientation_control.v1"
)
GC_CONSTRUCTION_EVIDENCE_SCHEMA = (
    "error_coupling_simulator.external."
    "gcapeps_n8_r3_gc_construction_pytest_controls.v1"
)
EXPECTED_FIXTURE_SHA256 = (
    "a494512a74ed20b28c067734359e9a09ab3df72ad07467160855c3c475ed0b8d"
)
EXPECTED_FORK_COMMIT = "6fbbf74cd36686ed30a4d8865697ce46e47056c1"
EXPECTED_FORK_TREE = "ffdfdf421fbe4d9674c2c88029710042fd18ae14"
EXPECTED_GC_TEST_SOURCE_SHA256 = (
    "d9ce1f4ee556af579eb9e199da8e80a3383910cea42b6383630ad84d9643bb48"
)
EXPECTED_GC_CONFTEST_SOURCE_SHA256 = (
    "f8c4792f1c4ac95f12d60214ee8dc61384e33de03b77cbcffa4c3e7e1c680db4"
)
EXPECTED_MEASURED_LAUNCH_ORDER = (
    "plain",
    "gcapeps",
    "gcapeps",
    "plain",
) * 3
FORBIDDEN_ANCHOR_IMPORT_ROOTS = frozenset(
    {
        "quimb",
        "stim",
        "sdim",
        "gcapeps",
        "emit_gcapeps_n8_r3_fixture",
    }
)
GC_CONSTRUCTION_TEST_FILE = (
    "tests/test_experimental/test_gcapeps_tree_pepo.py"
)
GC_CONSTRUCTION_TEST_IDS = (
    (
        f"{GC_CONSTRUCTION_TEST_FILE}::"
        "test_full_basis_covers_common_routing_factor_and_root_copy"
    ),
    (
        f"{GC_CONSTRUCTION_TEST_FILE}::"
        "test_full_basis_covers_outside_factors_and_single_root"
    ),
    (
        f"{GC_CONSTRUCTION_TEST_FILE}::"
        "test_routed_gauge_fusion_names_old_bond_then_term_label_layout"
    ),
    (
        f"{GC_CONSTRUCTION_TEST_FILE}::"
        "test_lowering_validator_recomputes_construction_formulas[gauge_value]"
    ),
)

_SCRIPT_PATH = Path(__file__).resolve()
_REPO_ROOT = _SCRIPT_PATH.parents[2]
_SCRIPT_DIR = _SCRIPT_PATH.parent
_EMITTER_PATH = _SCRIPT_DIR / "emit_gcapeps_n8_r3_fixture.py"
_ANCHOR_PATH = _SCRIPT_DIR / "gcapeps_n8_r3_dense_anchor.py"
_COMPARATOR_PATH = _SCRIPT_DIR / "compare_gcapeps_n8_r3_differential.py"
_PLAIN_WORKER_PATH = _SCRIPT_DIR / "plain_quimb_n8_r3_worker.py"
_GC_WORKER_PATH = _SCRIPT_DIR / "gcapeps_n8_r3_worker.py"
_SDIM_WORKER_PATH = _SCRIPT_DIR / "gcapeps_n8_r3_sdim_worker.py"


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


def canonical_content_sha256(report: Mapping[str, Any]) -> str:
    """Hash one controls/evidence report without its top-level self-hash."""

    body = dict(report)
    body.pop("content_sha256", None)
    return _canonical_sha256(body)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.resolve(strict=True).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _reject_duplicate_pairs(
    pairs: Sequence[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON token is forbidden: {value}")


def _load_canonical_json(path: Path, *, label: str) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    raw = resolved.read_bytes()
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is not strict UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    if raw != _canonical_json_bytes(value):
        raise ValueError(f"{label} is not exact canonical JSON")
    return value


def _load_script(path: Path, module_name: str) -> ModuleType:
    source = path.resolve(strict=True)
    spec = importlib.util.spec_from_file_location(module_name, source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load script module: {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _parent_source_hashes() -> dict[str, str]:
    paths = {
        "fixture_emitter": _EMITTER_PATH,
        "numpy_anchor": _ANCHOR_PATH,
        "complete_vector_comparator": _COMPARATOR_PATH,
        "plain_quimb_worker": _PLAIN_WORKER_PATH,
        "gcapeps_worker": _GC_WORKER_PATH,
        "sdim_worker": _SDIM_WORKER_PATH,
        "controls_runner": _SCRIPT_PATH,
    }
    return {name: _sha256_file(path) for name, path in paths.items()}


def _load_fixture(
    fixture_path: Path,
    *,
    emitter: ModuleType,
) -> tuple[dict[str, Any], dict[str, Any]]:
    resolved = fixture_path.resolve(strict=True)
    raw = resolved.read_bytes()
    fixture = _load_canonical_json(resolved, label="canonical fixture")
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_FIXTURE_SHA256:
        raise ValueError("controls fixture file hash drifted")
    if emitter.validate_fixture(fixture) != EXPECTED_FIXTURE_SHA256:
        raise ValueError("controls fixture semantic identity drifted")
    return fixture, {
        "path": str(resolved),
        "schema": fixture["schema"],
        "fixture_id": fixture["fixture_id"],
        "sha256": digest,
        "canonical_json": True,
        "n_qubits": 8,
        "active_rank": 3,
    }


def scan_anchor_prohibited_imports(source_path: Path = _ANCHOR_PATH) -> dict[str, Any]:
    """Statically audit the NumPy anchor's import independence."""

    resolved = source_path.resolve(strict=True)
    source = resolved.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(resolved))
    imported: set[str] = set()
    dynamic_literal_imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module)
        elif isinstance(node, ast.Call):
            is_import_call = (
                isinstance(node.func, ast.Name)
                and node.func.id == "__import__"
            ) or (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "import_module"
            )
            if (
                is_import_call
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                dynamic_literal_imports.add(node.args[0].value)

    all_imports = imported | dynamic_literal_imports
    prohibited = sorted(
        name
        for name in all_imports
        if name.split(".", 1)[0] in FORBIDDEN_ANCHOR_IMPORT_ROOTS
        or ".gcapeps" in name
    )
    return {
        "source_relative_path": source_path.resolve(strict=True).relative_to(
            _REPO_ROOT
        ).as_posix(),
        "source_sha256": _sha256_file(resolved),
        "imported_modules": sorted(imported),
        "dynamic_literal_imports": sorted(dynamic_literal_imports),
        "forbidden_imports": prohibited,
        "passed": not prohibited,
    }


def evaluate_fixture_identity(
    *,
    plain_fixture_sha256: str,
    gcapeps_fixture_sha256: str,
    anchor_fixture_sha256: str,
) -> dict[str, Any]:
    """Grade the three fixture bindings before any timing interpretation."""

    values = {
        "plain": plain_fixture_sha256,
        "gcapeps": gcapeps_fixture_sha256,
        "anchor": anchor_fixture_sha256,
    }
    valid_hex = all(
        isinstance(value, str)
        and re.fullmatch(r"[0-9a-f]{64}", value) is not None
        for value in values.values()
    )
    exact_match = valid_hex and all(
        value == EXPECTED_FIXTURE_SHA256 for value in values.values()
    )
    return {
        "fixture_sha256": values,
        "all_are_lowercase_sha256": valid_hex,
        "all_equal_frozen_fixture": exact_match,
        "timing_comparison_eligibility": (
            "ELIGIBLE" if exact_match else "INELIGIBLE"
        ),
    }


def evaluate_timing_and_order(
    *,
    plain_update_ns: Sequence[int],
    gcapeps_update_ns: Sequence[int],
    launch_order: Sequence[str],
) -> dict[str, Any]:
    """Fail closed on nonpositive, unequal-count, or reordered samples."""

    try:
        plain = tuple(plain_update_ns)
        gcapeps = tuple(gcapeps_update_ns)
        order = tuple(launch_order)
    except TypeError:
        return {
            "eligible": False,
            "reasons": ["timing_or_order_is_not_a_sequence"],
        }
    reasons: list[str] = []
    if len(plain) != 6 or len(gcapeps) != 6 or len(plain) != len(gcapeps):
        reasons.append("sample_count_differs_from_six_per_lane")
    for label, values in (("plain", plain), ("gcapeps", gcapeps)):
        if any(
            not isinstance(value, int)
            or isinstance(value, bool)
            or value <= 0
            for value in values
        ):
            reasons.append(f"{label}_timing_contains_nonpositive_or_noninteger")
    if order != EXPECTED_MEASURED_LAUNCH_ORDER:
        reasons.append("launch_order_differs")
    return {
        "eligible": not reasons,
        "reasons": reasons,
        "plain_sample_count": len(plain),
        "gcapeps_sample_count": len(gcapeps),
        "launch_order": list(order),
        "expected_launch_order": list(EXPECTED_MEASURED_LAUNCH_ORDER),
    }


def _comparison_control(
    comparison: Mapping[str, Any],
    *,
    movement_min: float | None = None,
    expected_verdict: str = "MISMATCH",
) -> bool:
    if comparison.get("verdict") != expected_verdict:
        return False
    if movement_min is None:
        return True
    movement = comparison.get("d_inf")
    return (
        isinstance(movement, (int, float))
        and not isinstance(movement, bool)
        and math.isfinite(float(movement))
        and float(movement) > movement_min
    )


def _apply_pauli_product(
    anchor: ModuleType,
    vector: np.ndarray,
    terms: Sequence[Mapping[str, Any]],
) -> np.ndarray:
    result = np.ascontiguousarray(vector.copy(), dtype=np.complex128)
    for term in terms:
        result = np.ascontiguousarray(
            anchor._coefficient(term)
            * anchor._pauli_action(result, str(term["pauli_body"])),
            dtype=np.complex128,
        )
    return result


def _captured_schema_rejection(
    comparator: ModuleType,
    reference: np.ndarray,
    corrupted: np.ndarray,
    *,
    bands: Mapping[str, Any],
) -> dict[str, Any]:
    try:
        comparator.compare_complete_vectors(
            reference,
            corrupted,
            bands=bands,
        )
    except ValueError as exc:
        return {
            "rejected": True,
            "exception_type": type(exc).__name__,
            "message": str(exc),
        }
    return {
        "rejected": False,
        "exception_type": None,
        "message": None,
    }


def run_pure_numpy_controls(
    fixture: Mapping[str, Any],
    *,
    anchor: ModuleType,
    comparator: ModuleType,
) -> dict[str, Any]:
    """Execute every in-process corruption without Quimb/Stim/SDIM."""

    computation = anchor.compute_anchor(fixture)
    vectors = computation["vectors"]
    bands = fixture["metric_bands"]
    movement_min = float(bands["corruption_movement_min"])
    reference_final = vectors["physical_from_signed_terms"]
    reference_prefix = vectors["physical_preparation_after_clifford"]

    preparation_dual = comparator.compare_complete_vectors(
        vectors["closed_form_preparation"],
        vectors["gate_replay_preparation"],
        bands=bands,
    )
    physical_dual = comparator.compare_complete_vectors(
        vectors["physical_from_residual_lift"],
        reference_final,
        bands=bands,
    )
    anchor_formulations = {
        "preparation": preparation_dual,
        "physical_state_action": physical_dual,
        "passed": (
            preparation_dual["verdict"] == "AGREE"
            and physical_dual["verdict"] == "AGREE"
        ),
    }

    shared = reference_final.copy()
    shared[0] += np.complex128(1.0e-6 + 0.0j)
    shared_pair = comparator.compare_complete_vectors(
        shared,
        shared.copy(),
        bands=bands,
    )
    shared_anchor = comparator.compare_complete_vectors(
        reference_final,
        shared,
        bands=bands,
    )
    shared_corruption = {
        "pair": shared_pair,
        "against_anchor": shared_anchor,
        "passed": (
            shared_pair["verdict"] == "AGREE"
            and shared_anchor["verdict"] == "MISMATCH"
        ),
    }

    clifford_gates = [
        (str(row["token"]), tuple(row["logical_targets"]))
        for row in fixture["clifford"]["gates"]
    ]
    omitted_swap_index = 6
    omitted_gate = clifford_gates.pop(omitted_swap_index)
    omitted_prefix = anchor._apply_gate_stream(
        vectors["gate_replay_preparation"],
        clifford_gates,
    )
    omitted_comparison = comparator.compare_complete_vectors(
        reference_prefix,
        omitted_prefix,
        bands=bands,
    )
    omitted_swap = {
        "omitted_index": omitted_swap_index,
        "omitted_gate": [omitted_gate[0], list(omitted_gate[1])],
        "after_clifford_comparison": omitted_comparison,
        "passed": _comparison_control(
            omitted_comparison,
            movement_min=movement_min,
        ),
    }

    product_final = _apply_pauli_product(
        anchor,
        reference_prefix,
        fixture["physical_terms"],
    )
    product_comparison = comparator.compare_complete_vectors(
        reference_final,
        product_final,
        bands=bands,
    )
    sum_to_product = {
        "comparison": product_comparison,
        "passed": _comparison_control(
            product_comparison,
            movement_min=movement_min,
        ),
    }

    flipped_terms = copy.deepcopy(fixture["physical_terms"])
    flipped_terms[0]["word_phase"] *= -1
    flipped_final = anchor._apply_pauli_sum(reference_prefix, flipped_terms)
    flipped_comparison = comparator.compare_complete_vectors(
        reference_final,
        flipped_final,
        bands=bands,
    )
    first_physical_phase = {
        "term_index": 0,
        "comparison": flipped_comparison,
        "passed": _comparison_control(
            flipped_comparison,
            movement_min=movement_min,
        ),
    }

    swapped = np.ascontiguousarray(
        reference_final.reshape((2,) * 8)
        .transpose(7, 1, 2, 3, 4, 5, 6, 0)
        .reshape(256)
    )
    swapped_comparison = comparator.compare_complete_vectors(
        reference_final,
        swapped,
        bands=bands,
    )
    q0_q7_axis_swap = {
        "comparison": swapped_comparison,
        "passed": swapped_comparison["verdict"] == "MISMATCH",
    }

    phase_vector = np.ascontiguousarray(
        np.complex128(1.0j) * reference_final
    )
    phase_comparison = comparator.compare_complete_vectors(
        reference_final,
        phase_vector,
        bands=bands,
    )
    global_phase = {
        "comparison": phase_comparison,
        "passed": (
            phase_comparison["verdict"] == "MISMATCH"
            and phase_comparison["infidelity"] <= bands["infidelity_max"]
            and phase_comparison["d_rel"] > bands["d_rel_max"]
        ),
    }

    scaled_vector = np.ascontiguousarray(
        np.complex128(1.0 + 1.0e-6) * reference_final
    )
    scale_comparison = comparator.compare_complete_vectors(
        reference_final,
        scaled_vector,
        bands=bands,
    )
    scale = {
        "comparison": scale_comparison,
        "passed": (
            scale_comparison["verdict"] == "MISMATCH"
            and scale_comparison["infidelity"] <= bands["infidelity_max"]
            and scale_comparison["d_norm"] > bands["d_norm_max"]
        ),
    }

    element_vector = reference_final.copy()
    element_vector[0] += np.complex128(1.0e-6 + 0.0j)
    element_comparison = comparator.compare_complete_vectors(
        reference_final,
        element_vector,
        bands=bands,
    )
    single_element = {
        "element_index": 0,
        "delta": {"real": 1.0e-6, "imag": 0.0},
        "comparison": element_comparison,
        "copied_structural_metadata_unchanged": True,
        "passed": element_comparison["verdict"] == "MISMATCH",
    }

    invalid_vectors = {
        "wrong_dtype_complex64": reference_final.astype(np.complex64),
        "wrong_shape_255": reference_final[:-1].copy(),
        "nonfinite": np.full(
            256,
            np.complex128(np.nan + 0.0j),
            dtype=np.complex128,
        ),
        "zero_norm": np.zeros(256, dtype=np.complex128),
    }
    invalid_results = {
        name: _captured_schema_rejection(
            comparator,
            reference_final,
            value,
            bands=bands,
        )
        for name, value in invalid_vectors.items()
    }
    invalid_vector_schema = {
        "cases": invalid_results,
        "passed": all(row["rejected"] for row in invalid_results.values()),
    }

    altered_fixture = copy.deepcopy(fixture)
    altered_fixture["active_rank"] = 4
    altered_hash = _canonical_sha256(altered_fixture)
    fixture_mismatch_result = evaluate_fixture_identity(
        plain_fixture_sha256=EXPECTED_FIXTURE_SHA256,
        gcapeps_fixture_sha256=altered_hash,
        anchor_fixture_sha256=EXPECTED_FIXTURE_SHA256,
    )
    fixture_mismatch = {
        "altered_field": "active_rank",
        "altered_fixture_sha256": altered_hash,
        "result": fixture_mismatch_result,
        "passed": (
            fixture_mismatch_result["timing_comparison_eligibility"]
            == "INELIGIBLE"
        ),
    }

    valid_times = (10, 11, 12, 13, 14, 15)
    timing_cases = {
        "valid_baseline": evaluate_timing_and_order(
            plain_update_ns=valid_times,
            gcapeps_update_ns=valid_times,
            launch_order=EXPECTED_MEASURED_LAUNCH_ORDER,
        ),
        "zero": evaluate_timing_and_order(
            plain_update_ns=(10, 11, 12, 13, 14, 0),
            gcapeps_update_ns=valid_times,
            launch_order=EXPECTED_MEASURED_LAUNCH_ORDER,
        ),
        "negative": evaluate_timing_and_order(
            plain_update_ns=valid_times,
            gcapeps_update_ns=(10, 11, 12, 13, 14, -1),
            launch_order=EXPECTED_MEASURED_LAUNCH_ORDER,
        ),
        "sample_count_differs": evaluate_timing_and_order(
            plain_update_ns=valid_times[:-1],
            gcapeps_update_ns=valid_times,
            launch_order=EXPECTED_MEASURED_LAUNCH_ORDER,
        ),
        "launch_order_differs": evaluate_timing_and_order(
            plain_update_ns=valid_times,
            gcapeps_update_ns=valid_times,
            launch_order=(
                "gcapeps",
                "plain",
                *EXPECTED_MEASURED_LAUNCH_ORDER[2:],
            ),
        ),
    }
    timing_and_order = {
        "cases": timing_cases,
        "passed": (
            timing_cases["valid_baseline"]["eligible"] is True
            and all(
                timing_cases[name]["eligible"] is False
                for name in (
                    "zero",
                    "negative",
                    "sample_count_differs",
                    "launch_order_differs",
                )
            )
        ),
    }

    rows = {
        "anchor_dual_formulations": anchor_formulations,
        "shared_candidate_corruption": shared_corruption,
        "omitted_first_routing_swap": omitted_swap,
        "pauli_sum_replaced_by_product": sum_to_product,
        "first_physical_word_phase_flip": first_physical_phase,
        "q0_q7_export_axis_swap": q0_q7_axis_swap,
        "global_phase_1j": global_phase,
        "global_scale_1_plus_1e_minus_6": scale,
        "single_element_plus_1e_minus_6": single_element,
        "invalid_vector_schema": invalid_vector_schema,
        "fixture_hash_mismatch": fixture_mismatch,
        "timing_and_launch_order": timing_and_order,
    }
    return {
        "uses_only_numpy_fixture_anchor_and_comparator": True,
        "clean_n8_candidate_workers_executed": False,
        "controls": rows,
        "all_passed": all(row["passed"] for row in rows.values()),
    }


def run_gc_coherent_term_binding_control(
    fixture: Mapping[str, Any],
    *,
    gc_worker: ModuleType,
) -> dict[str, Any]:
    """Trip the GC event validator when one pulled sign is corrupted."""

    physical_terms: list[str] = []
    pulled_terms: list[str] = []
    for term in fixture["physical_terms"]:
        coefficient = complex(
            float(term["coefficient_real"]),
            float(term["coefficient_imag"]),
        )
        physical_sign = "+" if int(term["word_phase"]) == 1 else "-"
        physical_terms.append(
            f"{coefficient!r}*{physical_sign}{term['pauli_body']}"
        )
        pulled_terms.append(
            f"{coefficient!r}*{term['expected_signed_pullback']}"
        )
    accepted = gc_worker.validate_coherent_event_term_binding(
        physical_terms,
        pulled_terms,
    )
    corrupted = list(pulled_terms)
    first = corrupted[0]
    marker = "*+" if "*+" in first else "*-"
    replacement = "*-" if marker == "*+" else "*+"
    corrupted[0] = first.replace(marker, replacement, 1)
    try:
        gc_worker.validate_coherent_event_term_binding(
            physical_terms,
            corrupted,
        )
    except RuntimeError as exc:
        rejected = True
        rejection = f"{type(exc).__name__}: {exc}"
    else:
        rejected = False
        rejection = None
    return {
        "fixture_derived_physical_terms": physical_terms,
        "fixture_derived_pulled_terms": pulled_terms,
        "accepted_binding": accepted,
        "corrupted_first_pulled_term": corrupted[0],
        "corruption_rejected": rejected,
        "rejection": rejection,
        "clean_n8_candidate_executed": False,
        "passed": bool(
            accepted.get("coefficients_and_signed_words_exactly_bound") is True
            and rejected
        ),
    }


def build_orientation_control_command(
    *,
    python_executable: Path,
    fixture_json: Path,
    fork_checkout: Path,
    output_json: Path,
    controls_script: Path = _SCRIPT_PATH,
) -> list[str]:
    """Construct, but do not run, the isolated one-site Quimb control."""

    return [
        str(python_executable),
        "-I",
        str(controls_script),
        "orientation",
        "--fixture-json",
        str(fixture_json),
        "--fork-checkout",
        str(fork_checkout),
        "--expected-fork-commit",
        EXPECTED_FORK_COMMIT,
        "--expected-fork-tree",
        EXPECTED_FORK_TREE,
        "--output-json",
        str(output_json),
    ]


def build_gc_construction_pytest_command(
    *,
    python_executable: Path,
    fork_checkout: Path,
) -> list[str]:
    """Construct the exact four-test subprocess command."""

    del fork_checkout
    return [
        str(python_executable),
        "-I",
        "-B",
        "-m",
        "pytest",
        "-q",
        "--tb=short",
        "-p",
        "no:cacheprovider",
        *GC_CONSTRUCTION_TEST_IDS,
    ]


def build_gc_construction_control_command(
    *,
    python_executable: Path,
    fork_checkout: Path,
    output_json: Path,
    controls_script: Path = _SCRIPT_PATH,
) -> list[str]:
    """Construct, but do not run, the four-test evidence entry point."""

    return [
        str(python_executable),
        "-I",
        str(controls_script),
        "gc-construction",
        "--fork-checkout",
        str(fork_checkout),
        "--expected-fork-commit",
        EXPECTED_FORK_COMMIT,
        "--expected-fork-tree",
        EXPECTED_FORK_TREE,
        "--output-json",
        str(output_json),
    ]


def build_sdim_worker_command(
    *,
    python_executable: Path,
    fixture_json: Path,
    fork_checkout: Path,
    environment_yaml: Path,
    output_json: Path,
    flip_first_sign_control: bool,
    sdim_worker: Path = _SDIM_WORKER_PATH,
) -> list[str]:
    """Construct, but do not run, one normal or flipped SDIM worker."""

    command = [
        str(python_executable),
        "-I",
        str(sdim_worker),
        "--fixture-json",
        str(fixture_json),
        "--output-json",
        str(output_json),
        "--fork-checkout",
        str(fork_checkout),
        "--expected-fork-commit",
        EXPECTED_FORK_COMMIT,
        "--expected-fork-tree",
        EXPECTED_FORK_TREE,
        "--environment-yaml",
        str(environment_yaml),
    ]
    if flip_first_sign_control:
        command.append("--flip-first-sign-control")
    return command


def _git_scalar(checkout: Path, *arguments: str) -> str:
    process = subprocess.run(
        ["git", "-C", str(checkout), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    value = process.stdout.strip()
    if not value or "\n" in value:
        raise RuntimeError("Git identity command did not return one scalar")
    return value


def _verify_frozen_fork(
    checkout: Path,
    *,
    expected_commit: str,
    expected_tree: str,
) -> dict[str, Any]:
    if expected_commit != EXPECTED_FORK_COMMIT:
        raise ValueError("requested fork commit is not the frozen commit")
    if expected_tree != EXPECTED_FORK_TREE:
        raise ValueError("requested fork tree is not the frozen tree")
    lexical = checkout.absolute()
    resolved = checkout.resolve(strict=True)
    if lexical != resolved or not resolved.is_dir():
        raise RuntimeError("fork checkout must be an absolute nonsymlink directory")
    top = Path(
        _git_scalar(resolved, "rev-parse", "--show-toplevel")
    ).resolve(strict=True)
    commit = _git_scalar(resolved, "rev-parse", "--verify", "HEAD^{commit}")
    tree = _git_scalar(resolved, "rev-parse", "--verify", "HEAD^{tree}")
    if (
        top != resolved
        or commit != EXPECTED_FORK_COMMIT
        or tree != EXPECTED_FORK_TREE
    ):
        raise RuntimeError("fork checkout identity drifted")
    status_process = subprocess.run(
        [
            "git",
            "-C",
            str(resolved),
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--ignored",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    if status_process.stdout != "":
        raise RuntimeError("fork checkout is not ignored-inclusive pristine")
    return {
        "checkout_path": str(resolved),
        "commit": commit,
        "tree": tree,
        "ignored_inclusive_pristine": True,
    }


def _require_content_hash(report: Mapping[str, Any], *, label: str) -> None:
    digest = report.get("content_sha256")
    if (
        not isinstance(digest, str)
        or re.fullmatch(r"[0-9a-f]{64}", digest) is None
        or digest != canonical_content_sha256(report)
    ):
        raise ValueError(f"{label} canonical content hash drifted")


def validate_orientation_evidence(
    report: Mapping[str, Any],
    *,
    expected_source_hashes: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Validate one actual frozen-Quimb one-site evidence report."""

    if not isinstance(report, Mapping):
        raise ValueError("orientation evidence must be an object")
    _require_content_hash(report, label="orientation evidence")
    if report.get("schema") != ORIENTATION_EVIDENCE_SCHEMA:
        raise ValueError("orientation evidence schema drifted")
    if report.get("fixture_sha256") != EXPECTED_FIXTURE_SHA256:
        raise ValueError("orientation fixture identity drifted")
    fork = report.get("fork_identity")
    if (
        not isinstance(fork, Mapping)
        or fork.get("commit") != EXPECTED_FORK_COMMIT
        or fork.get("tree") != EXPECTED_FORK_TREE
        or fork.get("ignored_inclusive_pristine_before") is not True
        or fork.get("ignored_inclusive_pristine_after") is not True
    ):
        raise ValueError("orientation fork identity drifted")
    sources = report.get("source_sha256")
    if not isinstance(sources, Mapping):
        raise ValueError("orientation source identity is unavailable")
    if expected_source_hashes is not None and (
        sources.get("plain_quimb_worker")
        != expected_source_hashes["plain_quimb_worker"]
        or sources.get("controls_runner")
        != expected_source_hashes["controls_runner"]
    ):
        raise ValueError("orientation parent source identity drifted")
    control = report.get("orientation_control")
    passed = (
        isinstance(control, Mapping)
        and control.get("status") == "PASS"
        and control.get("contract")
        == "one_site_nonsymmetric_dense_equals_raw_transpose"
        and control.get("dense_exactly_equals_desired") is True
        and control.get("dense_differs_from_raw") is True
        and isinstance(control.get("action_max_abs_error"), (int, float))
        and isinstance(
            control.get("action_max_abs_error_bound"),
            (int, float),
        )
        and float(control["action_max_abs_error"])
        <= float(control["action_max_abs_error_bound"])
        and isinstance(
            control.get("wrong_orientation_movement"),
            (int, float),
        )
        and float(control["wrong_orientation_movement"]) > 1.0e-6
        and control.get("target_fixture_apply_count") == 0
        and control.get("control_apply_count") == 1
        and report.get("clean_n8_candidates_executed") is False
    )
    if not passed:
        raise ValueError("one-site orientation evidence did not pass")
    return {
        "status": "PASS",
        "content_sha256": report["content_sha256"],
        "fixture_sha256": EXPECTED_FIXTURE_SHA256,
        "target_n8_candidates_executed": False,
    }


def validate_gc_construction_evidence(
    report: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate the exact four frozen-fork construction tests."""

    if not isinstance(report, Mapping):
        raise ValueError("GC construction evidence must be an object")
    _require_content_hash(report, label="GC construction evidence")
    if report.get("schema") != GC_CONSTRUCTION_EVIDENCE_SCHEMA:
        raise ValueError("GC construction evidence schema drifted")
    fork = report.get("fork_identity")
    if (
        not isinstance(fork, Mapping)
        or fork.get("commit") != EXPECTED_FORK_COMMIT
        or fork.get("tree") != EXPECTED_FORK_TREE
        or fork.get("ignored_inclusive_pristine_before") is not True
        or fork.get("ignored_inclusive_pristine_after") is not True
    ):
        raise ValueError("GC construction fork identity drifted")
    sources = report.get("source_sha256")
    if sources != {
        GC_CONSTRUCTION_TEST_FILE: EXPECTED_GC_TEST_SOURCE_SHA256,
        "tests/test_experimental/conftest.py": (
            EXPECTED_GC_CONFTEST_SOURCE_SHA256
        ),
    }:
        raise ValueError("GC construction test source identity drifted")
    command = report.get("pytest_command")
    if (
        not isinstance(command, list)
        or tuple(report.get("selected_test_ids", ()))
        != GC_CONSTRUCTION_TEST_IDS
        or tuple(command[-len(GC_CONSTRUCTION_TEST_IDS) :])
        != GC_CONSTRUCTION_TEST_IDS
        or report.get("returncode") != 0
        or report.get("observed_pass_count") != 4
        or report.get("passed") is not True
        or report.get("clean_n8_candidates_executed") is not False
    ):
        raise ValueError("GC construction pytest evidence did not pass")
    return {
        "status": "PASS",
        "content_sha256": report["content_sha256"],
        "selected_test_ids": list(GC_CONSTRUCTION_TEST_IDS),
        "target_n8_candidates_executed": False,
    }


def validate_sdim_evidence_pair(
    normal_report: Mapping[str, Any],
    flip_report: Mapping[str, Any],
    *,
    sdim_worker: ModuleType,
    expected_source_hashes: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Require normal PASS and the registered first-sign corruption FAIL."""

    sdim_worker.validate_report(normal_report)
    sdim_worker.validate_report(flip_report)
    normal_control = normal_report["control"]
    flip_control = flip_report["control"]
    if (
        normal_report["fixture_identity"]["file_sha256"]
        != EXPECTED_FIXTURE_SHA256
        or flip_report["fixture_identity"]["file_sha256"]
        != EXPECTED_FIXTURE_SHA256
        or normal_report["fork_identity"]["actual_commit"]
        != EXPECTED_FORK_COMMIT
        or flip_report["fork_identity"]["actual_commit"]
        != EXPECTED_FORK_COMMIT
        or normal_report["fork_identity"]["actual_tree"] != EXPECTED_FORK_TREE
        or flip_report["fork_identity"]["actual_tree"] != EXPECTED_FORK_TREE
        or normal_control["enabled"] is not False
        or normal_control["detected"] is not False
        or normal_report["sdim_frame_verdict"] != "PASS"
        or flip_control["enabled"] is not True
        or flip_control["detected"] is not True
        or flip_report["sdim_frame_verdict"] != "FAIL"
    ):
        raise ValueError("normal/flip SDIM evidence pair did not pass")
    normal_worker_hash = normal_report["runtime_identity"]["worker_source"][
        "origin_sha256"
    ]
    flip_worker_hash = flip_report["runtime_identity"]["worker_source"][
        "origin_sha256"
    ]
    if (
        normal_worker_hash != flip_worker_hash
        or (
            expected_source_hashes is not None
            and normal_worker_hash != expected_source_hashes["sdim_worker"]
        )
    ):
        raise ValueError("SDIM worker source identity differs across evidence")
    identity_fields = (
        ("fixture_identity", "canonical_sha256"),
        ("fork_identity", "actual_commit"),
        ("fork_identity", "actual_tree"),
        ("environment_identity", "actual_yaml_sha256"),
    )
    for parent, field in identity_fields:
        if normal_report[parent][field] != flip_report[parent][field]:
            raise ValueError(f"SDIM evidence identity differs at {parent}.{field}")
    return {
        "status": "PASS",
        "normal_content_sha256": normal_report["content_sha256"],
        "flip_content_sha256": flip_report["content_sha256"],
        "normal_verdict": "PASS",
        "flip_control_verdict": "FAIL_DETECTED",
        "enters_timing_or_rss_ratio": False,
    }


def _external_result(
    path: Path | None,
    *,
    label: str,
    validator: Any,
) -> dict[str, Any]:
    if path is None:
        return {
            "status": "MISSING",
            "passed": False,
            "path": None,
            "detail": f"{label} evidence was not supplied",
        }
    try:
        resolved = path.resolve(strict=True)
        report = _load_canonical_json(resolved, label=label)
        validated = validator(report)
    except Exception as exc:
        return {
            "status": "INVALID",
            "passed": False,
            "path": str(path.absolute()),
            "detail": f"{type(exc).__name__}: {exc}",
        }
    return {
        "status": "PASS",
        "passed": True,
        "path": str(resolved),
        "file_sha256": _sha256_file(resolved),
        "validated": validated,
    }


def build_controls_report(
    *,
    fixture_json: Path,
    orientation_evidence_json: Path | None,
    gc_construction_evidence_json: Path | None,
    sdim_normal_evidence_json: Path | None,
    sdim_flip_evidence_json: Path | None,
) -> dict[str, Any]:
    """Build the controls-only report without running external evidence."""

    sources_before = _parent_source_hashes()
    emitter = _load_script(
        _EMITTER_PATH,
        "_gcapeps_controls_fixture_emitter",
    )
    anchor = _load_script(
        _ANCHOR_PATH,
        "_gcapeps_controls_numpy_anchor",
    )
    comparator = _load_script(
        _COMPARATOR_PATH,
        "_gcapeps_controls_comparator",
    )
    gc_worker = _load_script(
        _GC_WORKER_PATH,
        "_gcapeps_controls_gc_worker_validator",
    )
    sdim_worker = _load_script(
        _SDIM_WORKER_PATH,
        "_gcapeps_controls_sdim_validator",
    )
    fixture, fixture_identity = _load_fixture(
        fixture_json,
        emitter=emitter,
    )
    anchor_import_scan = scan_anchor_prohibited_imports()
    synthetic_scan_source = "from quimb.experimental import gcapeps\n"
    synthetic_tree = ast.parse(synthetic_scan_source)
    synthetic_roots = {
        node.module.split(".", 1)[0]
        for node in ast.walk(synthetic_tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    anchor_scan_sensitivity = {
        "synthetic_source": synthetic_scan_source.rstrip("\n"),
        "detected_roots": sorted(
            synthetic_roots & FORBIDDEN_ANCHOR_IMPORT_ROOTS
        ),
        "passed": "quimb" in synthetic_roots,
    }
    pure = run_pure_numpy_controls(
        fixture,
        anchor=anchor,
        comparator=comparator,
    )
    pure["anchor_ast_prohibited_import_scan"] = anchor_import_scan
    pure["anchor_ast_scan_sensitivity"] = anchor_scan_sensitivity
    gc_term_binding = run_gc_coherent_term_binding_control(
        fixture,
        gc_worker=gc_worker,
    )
    pure["gc_coherent_event_term_binding"] = gc_term_binding
    pure["all_passed"] = bool(
        pure["all_passed"]
        and anchor_import_scan["passed"]
        and anchor_scan_sensitivity["passed"]
        and gc_term_binding["passed"]
    )

    orientation = _external_result(
        orientation_evidence_json,
        label="orientation evidence",
        validator=lambda report: validate_orientation_evidence(
            report,
            expected_source_hashes=sources_before,
        ),
    )
    construction = _external_result(
        gc_construction_evidence_json,
        label="GC construction evidence",
        validator=validate_gc_construction_evidence,
    )

    if sdim_normal_evidence_json is None or sdim_flip_evidence_json is None:
        sdim_pair = {
            "status": "MISSING",
            "passed": False,
            "normal_path": (
                None
                if sdim_normal_evidence_json is None
                else str(sdim_normal_evidence_json.absolute())
            ),
            "flip_path": (
                None
                if sdim_flip_evidence_json is None
                else str(sdim_flip_evidence_json.absolute())
            ),
            "detail": "both normal and flipped SDIM evidence are required",
        }
    else:
        try:
            normal_path = sdim_normal_evidence_json.resolve(strict=True)
            flip_path = sdim_flip_evidence_json.resolve(strict=True)
            normal = _load_canonical_json(
                normal_path,
                label="normal SDIM evidence",
            )
            flipped = _load_canonical_json(
                flip_path,
                label="flipped SDIM evidence",
            )
            validated_sdim = validate_sdim_evidence_pair(
                normal,
                flipped,
                sdim_worker=sdim_worker,
                expected_source_hashes=sources_before,
            )
        except Exception as exc:
            sdim_pair = {
                "status": "INVALID",
                "passed": False,
                "normal_path": str(sdim_normal_evidence_json.absolute()),
                "flip_path": str(sdim_flip_evidence_json.absolute()),
                "detail": f"{type(exc).__name__}: {exc}",
            }
        else:
            sdim_pair = {
                "status": "PASS",
                "passed": True,
                "normal_path": str(normal_path),
                "flip_path": str(flip_path),
                "normal_file_sha256": _sha256_file(normal_path),
                "flip_file_sha256": _sha256_file(flip_path),
                "validated": validated_sdim,
            }

    external = {
        "one_site_quimb_orientation": orientation,
        "gc_construction_pytests": construction,
        "sdim_normal_and_first_sign_flip": sdim_pair,
    }
    external_all_passed = all(row["passed"] for row in external.values())
    sources_after = _parent_source_hashes()
    if sources_after != sources_before:
        raise RuntimeError("controls source files changed during report assembly")
    controls_passed = bool(pure["all_passed"] and external_all_passed)
    report: dict[str, Any] = {
        "schema": CONTROLS_SCHEMA,
        "report_role": "supervisor_private_controls_only",
        "fixture_identity": fixture_identity,
        "source_sha256": sources_before,
        "selected_gc_construction_test_ids": list(
            GC_CONSTRUCTION_TEST_IDS
        ),
        "pure_numpy_evidence": pure,
        "external_evidence": external,
        "external_evidence_all_supplied_and_passed": external_all_passed,
        "controls_passed": controls_passed,
        "controls_gate_passed_for_later_preflights": controls_passed,
        "target_execution_authorized_by_this_report_alone": False,
        "execution_scope": {
            "clean_plain_n8_candidate_executed": False,
            "clean_gcapeps_n8_candidate_executed": False,
            "external_evidence_executed_by_collect_process": False,
            "anchor_enters_timing_or_rss": False,
            "sdim_enters_timing_or_rss": False,
            "generic_peps_correctness_claimed": False,
            "physical_ground_truth_claimed": False,
        },
    }
    report["content_sha256"] = canonical_content_sha256(report)
    return report


def write_private_canonical_json_noreplace(
    output_json: Path,
    report: Mapping[str, Any],
) -> Path:
    """Seal one canonical supervisor-private JSON with O_EXCL and fsync."""

    if report.get("content_sha256") != canonical_content_sha256(report):
        raise ValueError("controls report self-hash is invalid")
    encoded = _canonical_json_bytes(report)
    lexical_parent = output_json.absolute().parent
    parent = lexical_parent.resolve(strict=True)
    if lexical_parent != parent or not parent.is_dir():
        raise ValueError("output parent must be an existing nonsymlink directory")
    name = output_json.name
    if name in ("", ".", "..") or "/" in name or os.sep in name:
        raise ValueError("output JSON must name one file in its parent")

    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    directory_flags |= getattr(os, "O_CLOEXEC", 0)
    directory_flags |= getattr(os, "O_NOFOLLOW", 0)
    directory_fd = os.open(parent, directory_flags)
    output_fd: int | None = None
    created = False
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        flags |= getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        output_fd = os.open(name, flags, 0o600, dir_fd=directory_fd)
        created = True
        position = 0
        while position < len(encoded):
            written = os.write(output_fd, encoded[position:])
            if written <= 0:
                raise OSError("short write while sealing controls report")
            position += written
        os.fsync(output_fd)
        metadata = os.fstat(output_fd)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise RuntimeError("controls report is not one private regular file")
        os.close(output_fd)
        output_fd = None

        read_flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
        read_flags |= getattr(os, "O_NOFOLLOW", 0)
        verify_fd = os.open(name, read_flags, dir_fd=directory_fd)
        try:
            chunks: list[bytes] = []
            while True:
                chunk = os.read(verify_fd, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
        finally:
            os.close(verify_fd)
        if b"".join(chunks) != encoded:
            raise RuntimeError("controls report changed after write")
        os.fsync(directory_fd)
        return parent / name
    except Exception:
        if output_fd is not None:
            os.close(output_fd)
        if created:
            try:
                os.unlink(name, dir_fd=directory_fd)
                os.fsync(directory_fd)
            except OSError:
                pass
        raise
    finally:
        os.close(directory_fd)


def _run_orientation_evidence(args: argparse.Namespace) -> int:
    if (
        args.expected_fork_commit != EXPECTED_FORK_COMMIT
        or args.expected_fork_tree != EXPECTED_FORK_TREE
    ):
        raise ValueError("orientation CLI fork binding drifted")
    emitter = _load_script(
        _EMITTER_PATH,
        "_gcapeps_orientation_fixture_emitter",
    )
    plain = _load_script(
        _PLAIN_WORKER_PATH,
        "_gcapeps_orientation_plain_worker",
    )
    _, fixture_identity = _load_fixture(
        args.fixture_json,
        emitter=emitter,
    )
    before = _verify_frozen_fork(
        args.fork_checkout,
        expected_commit=args.expected_fork_commit,
        expected_tree=args.expected_fork_tree,
    )
    qtn, quimb_identity = plain._load_and_verify_quimb(
        args.fork_checkout.resolve(strict=True)
    )
    orientation = plain._one_site_orientation_control(qtn)
    after = _verify_frozen_fork(
        args.fork_checkout,
        expected_commit=args.expected_fork_commit,
        expected_tree=args.expected_fork_tree,
    )
    report: dict[str, Any] = {
        "schema": ORIENTATION_EVIDENCE_SCHEMA,
        "evidence_role": "actual_frozen_quimb_one_site_orientation_only",
        "fixture_sha256": fixture_identity["sha256"],
        "fork_identity": {
            "checkout_path": before["checkout_path"],
            "commit": before["commit"],
            "tree": before["tree"],
            "ignored_inclusive_pristine_before": before[
                "ignored_inclusive_pristine"
            ],
            "ignored_inclusive_pristine_after": after[
                "ignored_inclusive_pristine"
            ],
        },
        "source_sha256": {
            "plain_quimb_worker": _sha256_file(_PLAIN_WORKER_PATH),
            "controls_runner": _sha256_file(_SCRIPT_PATH),
        },
        "quimb_identity": quimb_identity,
        "orientation_control": orientation,
        "clean_n8_candidates_executed": False,
    }
    report["content_sha256"] = canonical_content_sha256(report)
    validate_orientation_evidence(
        report,
        expected_source_hashes=_parent_source_hashes(),
    )
    write_private_canonical_json_noreplace(args.output_json, report)
    return 0


def _run_gc_construction_evidence(args: argparse.Namespace) -> int:
    if (
        args.expected_fork_commit != EXPECTED_FORK_COMMIT
        or args.expected_fork_tree != EXPECTED_FORK_TREE
    ):
        raise ValueError("GC construction CLI fork binding drifted")
    before = _verify_frozen_fork(
        args.fork_checkout,
        expected_commit=args.expected_fork_commit,
        expected_tree=args.expected_fork_tree,
    )
    test_path = args.fork_checkout / GC_CONSTRUCTION_TEST_FILE
    conftest_path = (
        args.fork_checkout / "tests/test_experimental/conftest.py"
    )
    test_hash = _sha256_file(test_path)
    conftest_hash = _sha256_file(conftest_path)
    if (
        test_hash != EXPECTED_GC_TEST_SOURCE_SHA256
        or conftest_hash != EXPECTED_GC_CONFTEST_SOURCE_SHA256
    ):
        raise RuntimeError("frozen GC construction test source drifted")
    command = build_gc_construction_pytest_command(
        python_executable=Path(sys.executable),
        fork_checkout=args.fork_checkout,
    )
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment["PYTHONNOUSERSITE"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    process = subprocess.run(
        command,
        cwd=args.fork_checkout,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    match = re.search(r"(?<!\d)4 passed(?:[,\s]|$)", process.stdout)
    observed_pass_count = 4 if match is not None else 0
    after = _verify_frozen_fork(
        args.fork_checkout,
        expected_commit=args.expected_fork_commit,
        expected_tree=args.expected_fork_tree,
    )
    passed = process.returncode == 0 and observed_pass_count == 4
    report: dict[str, Any] = {
        "schema": GC_CONSTRUCTION_EVIDENCE_SCHEMA,
        "evidence_role": "four_exact_frozen_fork_construction_pytests",
        "fork_identity": {
            "checkout_path": before["checkout_path"],
            "commit": before["commit"],
            "tree": before["tree"],
            "ignored_inclusive_pristine_before": before[
                "ignored_inclusive_pristine"
            ],
            "ignored_inclusive_pristine_after": after[
                "ignored_inclusive_pristine"
            ],
        },
        "source_sha256": {
            GC_CONSTRUCTION_TEST_FILE: test_hash,
            "tests/test_experimental/conftest.py": conftest_hash,
        },
        "selected_test_ids": list(GC_CONSTRUCTION_TEST_IDS),
        "pytest_command": command,
        "returncode": process.returncode,
        "observed_pass_count": observed_pass_count,
        "stdout": process.stdout,
        "stderr": process.stderr,
        "stdout_sha256": hashlib.sha256(process.stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(process.stderr.encode()).hexdigest(),
        "passed": passed,
        "clean_n8_candidates_executed": False,
    }
    report["content_sha256"] = canonical_content_sha256(report)
    if passed:
        validate_gc_construction_evidence(report)
    write_private_canonical_json_noreplace(args.output_json, report)
    return 0 if passed else 1


def _add_fork_binding_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--fork-checkout", type=Path, required=True)
    parser.add_argument("--expected-fork-commit", required=True)
    parser.add_argument("--expected-fork-tree", required=True)
    parser.add_argument("--output-json", type=Path, required=True)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    collect = commands.add_parser(
        "collect",
        help="run pure NumPy controls and grade supplied external evidence",
    )
    collect.add_argument("--fixture-json", type=Path, required=True)
    collect.add_argument("--output-json", type=Path, required=True)
    collect.add_argument(
        "--orientation-evidence-json",
        "--orientation-evidence",
        dest="orientation_evidence_json",
        type=Path,
    )
    collect.add_argument(
        "--gc-construction-evidence-json",
        "--gc-construction-evidence",
        dest="gc_construction_evidence_json",
        type=Path,
    )
    collect.add_argument(
        "--sdim-normal-evidence-json",
        "--sdim-normal-evidence",
        dest="sdim_normal_evidence_json",
        type=Path,
    )
    collect.add_argument(
        "--sdim-flip-evidence-json",
        "--sdim-flip-evidence",
        dest="sdim_flip_evidence_json",
        type=Path,
    )

    orientation = commands.add_parser(
        "orientation",
        help="emit only the actual one-site frozen-Quimb orientation control",
    )
    orientation.add_argument("--fixture-json", type=Path, required=True)
    _add_fork_binding_arguments(orientation)

    construction = commands.add_parser(
        "gc-construction",
        help="emit only the four selected frozen-fork pytest controls",
    )
    _add_fork_binding_arguments(construction)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.command == "orientation":
        return _run_orientation_evidence(args)
    if args.command == "gc-construction":
        return _run_gc_construction_evidence(args)
    if args.command != "collect":
        raise RuntimeError(f"unsupported controls command: {args.command!r}")
    report = build_controls_report(
        fixture_json=args.fixture_json,
        orientation_evidence_json=args.orientation_evidence_json,
        gc_construction_evidence_json=args.gc_construction_evidence_json,
        sdim_normal_evidence_json=args.sdim_normal_evidence_json,
        sdim_flip_evidence_json=args.sdim_flip_evidence_json,
    )
    published = write_private_canonical_json_noreplace(
        args.output_json,
        report,
    )
    print(
        json.dumps(
            {
                "content_sha256": report["content_sha256"],
                "controls_passed": report["controls_passed"],
                "output_json": str(published),
            },
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ),
        flush=True,
    )
    return 0 if report["controls_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
