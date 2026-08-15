#!/usr/bin/env python3
"""Fail-closed instrument for the preregistered no-cutoff structure census.

The target d=3/5 Record oracle and three representation owners do not exist.
This module records that debt explicitly while providing a frozen fixture,
compile-only active-coordinate adapters, and exact integer growth adjudication.
It never constructs a simulator state or authorizes solver code.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterator, Mapping
from copy import deepcopy
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any


REPORT_SCHEMA = "error_coupling_simulator.external.no_cutoff_structure_census.v1"
CLIFFT_WORKER_SCHEMA = (
    "error_coupling_simulator.external.no_cutoff_structure_census.clifft_worker.v1"
)
FIXTURE_SCHEMA = (
    "error_coupling_simulator.external.no_cutoff_structure_fixture_identity.v1"
)
GRID = tuple((distance, rounds) for distance in (3, 5) for rounds in (1, 3, 5, 7))
ROUNDS = (1, 3, 5, 7)
ROUTE_KEYS = (
    "clifft_frame",
    "exact_pair",
    "dynamic_add",
    "retained_boundary_tn",
)
METRIC_FAMILIES = {"k_max", "n_pair", "n_dd", "tw", "delta_tv_cert"}
STATUSES = {
    "EXACT",
    "CERTIFIED_INTERVAL",
    "BOUNDS",
    "UNAVAILABLE",
    "CENSORED_RESOURCE",
}

REPO = Path(__file__).resolve().parents[2]
PREREG_PATH = (
    REPO
    / "docs"
    / "simulator_validation"
    / "NO_CUTOFF_STRUCTURE_CENSUS_PREREG_2026-08-03.md"
)
FIXTURE_MANIFEST_PATH = (
    REPO
    / "docs"
    / "simulator_validation"
    / "NO_CUTOFF_STRUCTURE_CENSUS_FIXTURE_MANIFEST_2026-08-03.json"
)
FIXTURE_MANIFEST_SHA256 = (
    "40474ca0beab8341d53bfa41da5438e052744bb83ae6af2632e1bfe273c53c74"
)
CLIFFT_COMMIT = "2c1dfa6029c4f0573c499e938e9a88106a6801b3"
CLIFFT_TREE = "9306ba4fa6d64ec0b9c5835298bf7586916e5b6c"
SYMFT_COMMIT = "bc9a8d2e33b1e03d411c4088f8255299c80a51eb"
SYMFT_TREE = "c24cefb2001cf295fe555637e3be5962d2bf0ffa"
NONZERO_SHADOWS = (
    "primary_plus",
    "primary_minus",
    "tiny_plus",
    "tiny_minus",
)
ALL_SHADOWS = (*NONZERO_SHADOWS, "inert")

_CLIFFT_SOURCE_ANCHORS = (
    "src/clifft/optimizer/statevector_squeeze_pass.cc",
    "src/clifft/optimizer/peephole.cc",
    "src/clifft/backend/compiler_context.h",
    "src/python/bindings.cc",
)
_SYMFT_SOURCE_ANCHORS = (
    "cpp/tools/symft_plan.cpp",
    "cpp/src/sampler/component_plan.cpp",
    "cpp/src/factored/factored_planner.cpp",
    "cpp/src/frontend/stim_parser.cpp",
    "cpp/src/sampler/active_internal.hpp",
    "cpp/CMakeLists.txt",
)

ANGLE_SERIALIZATIONS: dict[str, dict[str, Any]] = {
    "primary": {
        "t_numerator": 1,
        "t_denominator": 100,
        "positive_decimal": "0.012731971059633021",
        "positive_hex": "0x1.a13383a84979bp-7",
    },
    "nonzero_invariance": {
        "t_numerator": 1,
        "t_denominator": 10**20,
        "positive_decimal": "1.2732395447351627e-20",
        "positive_hex": "0x1.e1042c3d96d7fp-67",
    },
    "inert": {
        "t_numerator": 0,
        "t_denominator": 1,
        "positive_decimal": "0",
        "positive_hex": "0x0.0p+0",
    },
}

_STOCHASTIC_GATES = re.compile(
    r"^(?:DEPOLARIZE[12]|[XYZ]_ERROR|PAULI_CHANNEL_[12]|"
    r"CORRELATED_ERROR|ELSE_CORRELATED_ERROR|HERALDED_[A-Z0-9_]+)\b"
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_TRUTH_KEYS = {
    "latent_sign",
    "selected_sign",
    "process_truth",
    "evaluator_truth",
}
_FORBIDDEN_PROXY_KEYS = {
    "probability_node_count",
    "r_max",
    "tw_exact",
    "sampled_tv",
    "state_fidelity",
    "discarded_weight",
    "dem_distance",
}


def canonical_json_bytes(value: Any) -> bytes:
    """Encode the repository's canonical, finite-only pretty JSON."""

    return (
        json.dumps(value, allow_nan=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _negative_decimal(positive: str) -> str:
    return "0" if float(positive) == 0.0 else f"-{positive}"


def verify_angle_serializations() -> dict[str, dict[str, Any]]:
    """Check the frozen decimals against high-precision rounding cells."""

    import mpmath as mp

    observed: dict[str, dict[str, Any]] = {}
    for name, frozen in ANGLE_SERIALIZATIONS.items():
        positive_decimal = str(frozen["positive_decimal"])
        value = float(positive_decimal)
        if value == 0.0:
            value = 0.0
        if value.hex() != frozen["positive_hex"]:
            raise ValueError(f"{name} parser decimal does not reproduce frozen hex")
        if format(value, ".17g") != positive_decimal:
            raise ValueError(f"{name} decimal is not the unique .17g serialization")

        numerator = int(frozen["t_numerator"])
        denominator = int(frozen["t_denominator"])
        if numerator == 0:
            strictly_inside = True
        else:
            with mp.workprec(256):
                exact = 4 * mp.atan(mp.mpf(numerator) / denominator) / mp.pi
                previous = math.nextafter(value, -math.inf)
                following = math.nextafter(value, math.inf)
                lower_midpoint = (mp.mpf(previous) + mp.mpf(value)) / 2
                upper_midpoint = (mp.mpf(value) + mp.mpf(following)) / 2
                strictly_inside = bool(
                    lower_midpoint < exact < upper_midpoint
                )
        if not strictly_inside:
            raise ValueError(f"{name} high-precision value leaves rounding cell")

        negative_decimal = _negative_decimal(positive_decimal)
        negative = float(negative_decimal)
        if negative == 0.0:
            negative = 0.0
        observed[name] = {
            **frozen,
            "negative_decimal": negative_decimal,
            "negative_hex": negative.hex(),
            "strictly_inside_rounding_cell": strictly_inside,
            "mpmath_version": mp.__version__,
        }
    return observed


def _require_stim():
    import stim

    if stim.__version__ != "1.16.0":
        raise RuntimeError(f"fixture requires stim 1.16.0, got {stim.__version__}")
    return stim


def _generated_stim_circuit(distance: int, rounds: int):
    if (distance, rounds) not in GRID:
        raise ValueError(f"cell is outside frozen grid: {(distance, rounds)}")
    stim = _require_stim()
    return stim.Circuit.generated(
        "surface_code:rotated_memory_z",
        distance=distance,
        rounds=rounds,
        after_clifford_depolarization=0.001,
        after_reset_flip_probability=0.0,
        before_measure_flip_probability=0.0,
        before_round_data_depolarization=0.0,
    ).flattened()


def _site_entry(index: int, instruction: Any) -> dict[str, Any]:
    targets: list[int] = []
    for target in instruction.targets_copy():
        if not target.is_qubit_target:
            raise ValueError("scaffold noise target is not a qubit target")
        targets.append(int(target.value))
    return {
        "instruction_index": index,
        "source_args": [
            format(float(argument), ".17g")
            for argument in instruction.gate_args_copy()
        ],
        "source_gate": instruction.name,
        "targets": targets,
    }


def _shadow_text(
    rows: list[tuple[str, Any]],
    *,
    decimal: str | None,
) -> str:
    lines: list[str] = []
    for kind, value in rows:
        if kind == "raw":
            lines.append(value)
        elif decimal is not None:
            lines.append(f"R_Z({decimal}) " + " ".join(map(str, value)))
    return "\n".join(lines).rstrip("\n") + "\n"


def build_shadow_bundle(*, distance: int, rounds: int) -> dict[str, Any]:
    """Build the source scaffold, exact site map, and five structural shadows."""

    circuit = _generated_stim_circuit(distance, rounds)
    source_text = str(circuit).rstrip("\n") + "\n"
    rows: list[tuple[str, Any]] = []
    site_map: list[dict[str, Any]] = []
    for index, instruction in enumerate(circuit):
        if instruction.name in {"DEPOLARIZE1", "DEPOLARIZE2"}:
            entry = _site_entry(index, instruction)
            site_map.append(entry)
            rows.append(("noise", entry["targets"]))
        else:
            rows.append(("raw", str(instruction)))

    angles = verify_angle_serializations()
    shadow_decimals = {
        "primary_plus": angles["primary"]["positive_decimal"],
        "primary_minus": angles["primary"]["negative_decimal"],
        "tiny_plus": angles["nonzero_invariance"]["positive_decimal"],
        "tiny_minus": angles["nonzero_invariance"]["negative_decimal"],
        "inert": None,
    }
    shadows: dict[str, dict[str, str]] = {}
    for name, decimal in shadow_decimals.items():
        text = _shadow_text(rows, decimal=decimal)
        shadows[name] = {"text": text, "sha256": sha256_bytes(text.encode())}

    identity = {
        "distance": distance,
        "inert_shadow_sha256": shadows["inert"]["sha256"],
        "num_detectors": int(circuit.num_detectors),
        "num_observables": int(circuit.num_observables),
        "replacement_rows": len(site_map),
        "replacement_targets": sum(len(row["targets"]) for row in site_map),
        "rounds": rounds,
        "shadow_sha256": {
            name: shadows[name]["sha256"]
            for name in (
                "primary_minus",
                "primary_plus",
                "tiny_minus",
                "tiny_plus",
            )
        },
        "site_map_sha256": sha256_bytes(canonical_json_bytes(site_map)),
        "source_circuit_sha256": sha256_bytes(source_text.encode()),
    }
    return {
        "identity": identity,
        "shadows": shadows,
        "site_map": site_map,
        "source_text": source_text,
    }


def build_fixture_manifest() -> dict[str, Any]:
    cells = [
        build_shadow_bundle(distance=distance, rounds=rounds)["identity"]
        for distance, rounds in GRID
    ]
    return {
        "_schema": FIXTURE_SCHEMA,
        "canonical_json": "json.dumps(allow_nan=False,indent=2,sort_keys=True)+LF",
        "cells": cells,
        "generator": "surface_code:rotated_memory_z",
        "generator_parameters": {
            "after_clifford_depolarization": "0.001",
            "after_reset_flip_probability": "0",
            "before_measure_flip_probability": "0",
            "before_round_data_depolarization": "0",
        },
        "inert_policy": "delete_scaffold_rows",
        "source_text": "str(circuit.flattened()).rstrip(LF)+LF",
        "stim_version": "1.16.0",
    }


def verify_fixture_manifest() -> dict[str, Any]:
    frozen_raw = FIXTURE_MANIFEST_PATH.read_bytes()
    if sha256_bytes(frozen_raw) != FIXTURE_MANIFEST_SHA256:
        raise ValueError("frozen fixture manifest hash mismatch")
    frozen = json.loads(frozen_raw)
    observed = build_fixture_manifest()
    if canonical_json_bytes(observed) != canonical_json_bytes(frozen):
        raise ValueError("Stim fixture no longer reproduces frozen manifest")
    return observed


def contains_stochastic_channel(text: str) -> bool:
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped and _STOCHASTIC_GATES.match(stripped):
            return True
    return False


def structural_shadow_signature(text: str) -> str:
    if contains_stochastic_channel(text):
        raise ValueError("structural shadow retains a stochastic channel")
    normalized = re.sub(r"R_Z\([^)]*\)", "R_Z(<NONZERO>)", text)
    return sha256_bytes(normalized.encode())


def unavailable_metric(reason: str, *, metric: str, route: str) -> dict[str, Any]:
    if not reason:
        raise ValueError("unavailable reason must be nonempty")
    return {
        "identity": {"metric": metric, "route": route},
        "reason": reason,
        "status": "UNAVAILABLE",
    }


def censored_metric(
    reason: str,
    *,
    metric: str,
    route: str,
    resource_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    if not reason or not resource_receipt:
        raise ValueError("censored metric requires reason and resource receipt")
    return {
        "identity": {"metric": metric, "route": route},
        "reason": reason,
        "resource_receipt": dict(resource_receipt),
        "status": "CENSORED_RESOURCE",
    }


def _metric_interval(leaf: Mapping[str, Any]) -> tuple[int, int] | None:
    status = leaf.get("status")
    if status == "EXACT":
        raw = leaf.get("burden", leaf.get("value"))
        if isinstance(raw, bool) or not isinstance(raw, int) or raw <= 0:
            raise ValueError("exact burden must be a positive integer")
        return raw, raw
    if status == "CERTIFIED_INTERVAL":
        lower, upper = leaf.get("lower"), leaf.get("upper")
        if (
            isinstance(lower, bool)
            or isinstance(upper, bool)
            or not isinstance(lower, int)
            or not isinstance(upper, int)
            or lower <= 0
            or lower > upper
        ):
            raise ValueError("certified burden interval is invalid")
        return lower, upper
    if status in {"BOUNDS", "UNAVAILABLE", "CENSORED_RESOURCE"}:
        return None
    raise ValueError(f"unknown metric status: {status!r}")


def adjudicate_burden_series(
    series: Mapping[int, Mapping[str, Any]],
) -> dict[str, Any]:
    """Apply the exact all-three doubling rule without floating regression."""

    if tuple(sorted(series)) != ROUNDS:
        return {
            "indeterminate_reasons": ["MISSING_OR_EXTRA_ROUNDS"],
            "structure_disposition": "INDETERMINATE",
            "transitions": [],
        }
    intervals = {rounds: _metric_interval(series[rounds]) for rounds in ROUNDS}
    transitions: list[dict[str, Any]] = []
    indeterminate: list[str] = []
    for previous, following in zip(ROUNDS[:-1], ROUNDS[1:], strict=True):
        left = intervals[previous]
        right = intervals[following]
        label = f"{previous}->{following}"
        if left is None or right is None:
            classification = "INDETERMINATE"
            indeterminate.append(f"{label}:INELIGIBLE_INPUT")
        elif right[0] >= 2 * left[1]:
            classification = "PROVED_DOUBLING"
        elif right[1] < 2 * left[0]:
            classification = "PROVED_NON_DOUBLING"
        else:
            classification = "INDETERMINATE"
            indeterminate.append(f"{label}:INTERVAL_OVERLAP")
        transitions.append(
            {"classification": classification, "transition": label}
        )

    classifications = [row["classification"] for row in transitions]
    if all(value == "PROVED_DOUBLING" for value in classifications):
        disposition = "KILL_STRUCTURE"
    elif (
        "INDETERMINATE" not in classifications
        and "PROVED_NON_DOUBLING" in classifications
    ):
        disposition = "NOT_KILLED_ON_FROZEN_GRID"
    else:
        disposition = "INDETERMINATE"
    first = next(
        (
            row["transition"]
            for row in transitions
            if row["classification"] == "PROVED_DOUBLING"
        ),
        None,
    )
    result: dict[str, Any] = {
        "indeterminate_reasons": indeterminate,
        "structure_disposition": disposition,
        "transitions": transitions,
    }
    if first is not None:
        result["first_proved_doubling_transition"] = first
    return result


_SYMFT_INTEGER_FIELDS = {
    "qubits",
    "records",
    "detectors",
    "instructions",
    "max_active_qubits",
    "component_count",
    "dense_peak_dimension",
    "component_peak_live_dimension",
    "component_allocated_dimension",
    "pending_operations_before",
    "pending_operations_after",
    "fused_rotations",
    "cancelled_rotations",
    "measurement_left_swaps",
}
_SYMFT_FLOAT_FIELDS = {
    "estimated_dense_vector_work",
    "estimated_component_vector_work",
    "parse_seconds",
    "plan_seconds",
}


def parse_symft_plan_output(text: str) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        pieces = line.split(maxsplit=1)
        if len(pieces) != 2:
            raise ValueError(f"malformed symft_plan line: {line!r}")
        key, raw = pieces
        if key in parsed:
            raise ValueError(f"duplicate symft_plan field: {key}")
        if key in _SYMFT_INTEGER_FIELDS or key == "peak_rss_kib":
            try:
                value = int(raw)
            except ValueError as error:
                raise ValueError(f"non-integer SymFT field {key}") from error
            if value < 0:
                raise ValueError(f"negative SymFT field {key}")
            parsed[key] = value
        elif key in _SYMFT_FLOAT_FIELDS:
            try:
                value = Decimal(raw)
            except InvalidOperation as error:
                raise ValueError(f"invalid SymFT decimal {key}") from error
            if not value.is_finite() or value < 0:
                raise ValueError(f"invalid SymFT decimal {key}")
            parsed[key] = str(value)
        elif key == "active_components":
            if raw not in {"enabled", "dense_fallback"}:
                raise ValueError("invalid active_components value")
            parsed[key] = raw
        else:
            raise ValueError(f"unknown symft_plan field: {key}")

    required = _SYMFT_INTEGER_FIELDS | {"active_components"}
    missing = sorted(required - parsed.keys())
    if missing:
        raise ValueError(f"missing symft_plan fields: {missing}")
    expected_dense = 1 << int(parsed["max_active_qubits"])
    if parsed["dense_peak_dimension"] != expected_dense:
        raise ValueError("SymFT dense dimension disagrees with max_active_qubits")
    return parsed


def normalized_symft_structure(parsed: Mapping[str, Any]) -> dict[str, Any]:
    missing = (_SYMFT_INTEGER_FIELDS | {"active_components"}) - parsed.keys()
    if missing:
        raise ValueError(f"missing SymFT structural fields: {sorted(missing)}")
    normalized = {
        key: parsed[key]
        for key in sorted(_SYMFT_INTEGER_FIELDS | {"active_components"})
    }
    if int(parsed["max_active_qubits"]) < 8:
        component_values = (
            int(parsed["component_count"]),
            int(parsed["component_peak_live_dimension"]),
            int(parsed["component_allocated_dimension"]),
        )
        if component_values != (0, 0, 0):
            raise ValueError("SymFT k<8 early-return component fields are nonzero")
        if parsed["active_components"] != "dense_fallback":
            raise ValueError("SymFT k<8 component plan was unexpectedly selected")
        normalized["active_components"] = "not_constructed"
        normalized["component_plan_status"] = "NOT_CONSTRUCTED_K_LT_8"
    else:
        normalized["component_plan_status"] = (
            "SELECTED" if parsed["active_components"] == "enabled" else "NOT_SELECTED"
        )
    return normalized


def _strict_json_object(raw: bytes) -> dict[str, Any]:
    def pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    try:
        value = json.loads(raw, object_pairs_hook=pairs_hook)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError("invalid JSON") from error
    if not isinstance(value, dict):
        raise ValueError("worker output must be a JSON object")
    if canonical_json_bytes(value) != raw:
        raise ValueError("worker output is not canonical JSON")
    return value


def parse_clifft_worker_output(raw: bytes) -> dict[str, Any]:
    value = _strict_json_object(raw)
    if value.get("_schema") != CLIFFT_WORKER_SCHEMA:
        raise ValueError("wrong Clifft worker schema")
    pass_manifest = value.get("pass_manifest")
    expected_passes = {
        "bytecode_passes": None,
        "hir_passes": ["StatevectorSqueezePass"],
        "normalize_syndromes": False,
    }
    if pass_manifest != expected_passes:
        if isinstance(pass_manifest, dict) and "PeepholeFusionPass" in pass_manifest.get(
            "hir_passes", []
        ):
            raise ValueError("PeepholeFusionPass is cutoff-contaminated")
        raise ValueError("Clifft worker did not use the squeeze-only pass manifest")
    history = value.get("active_k_history")
    count = value.get("num_instructions")
    peak = value.get("peak_rank")
    if (
        not isinstance(history, list)
        or isinstance(count, bool)
        or not isinstance(count, int)
        or len(history) != count
        or any(
            isinstance(item, bool) or not isinstance(item, int) or item < 0
            for item in history
        )
    ):
        raise ValueError("invalid Clifft active_k_history")
    observed_peak = max(history, default=0)
    if peak != observed_peak:
        raise ValueError("Clifft peak_rank disagrees with active history")
    if not isinstance(value.get("extension_sha256"), str) or not _SHA256.fullmatch(
        value["extension_sha256"]
    ):
        raise ValueError("invalid Clifft extension hash")
    result = deepcopy(value)
    result["burden"] = 1 << observed_peak
    result["k_max_clifft_squeeze_no_peephole"] = observed_peak
    return result


def _git_output(source: Path, *arguments: str) -> str:
    process = subprocess.run(
        ["git", "-C", str(source), *arguments],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if process.returncode != 0:
        raise ValueError(
            f"git preflight failed for {source}: {process.stderr.strip()}"
        )
    return process.stdout.strip()


def verify_external_source(
    source: Path,
    *,
    expected_commit: str,
    expected_tree: str,
    anchors: tuple[str, ...],
) -> dict[str, Any]:
    """Require an exact clean external tree and hash the route-defining files."""

    resolved = source.resolve(strict=True)
    commit = _git_output(resolved, "rev-parse", "HEAD")
    tree = _git_output(resolved, "rev-parse", "HEAD^{tree}")
    if (commit, tree) != (expected_commit, expected_tree):
        raise ValueError(
            f"external source identity mismatch: {(commit, tree)}"
        )
    status = _git_output(
        resolved,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    if status:
        raise ValueError(f"external source is not pristine: {resolved}")
    anchor_hashes: dict[str, str] = {}
    for relative in anchors:
        path = resolved / relative
        if not path.is_file():
            raise ValueError(f"missing external source anchor: {relative}")
        anchor_hashes[relative] = sha256_file(path)
    return {
        "anchor_sha256": anchor_hashes,
        "commit": commit,
        "pristine": True,
        "tree": tree,
    }


def _worker_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    return environment


def _run_external_command(
    command: list[str],
    *,
    timeout_seconds: int,
) -> subprocess.CompletedProcess[bytes]:
    if isinstance(timeout_seconds, bool) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be a positive integer")
    return subprocess.run(
        command,
        check=False,
        cwd=REPO,
        env=_worker_environment(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_seconds,
    )


def _resource_receipt(
    *,
    backend: str,
    shadow: str,
    timeout_seconds: int,
    process: subprocess.CompletedProcess[bytes] | None,
) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "backend": backend,
        "shadow": shadow,
        "timeout_seconds": timeout_seconds,
    }
    if process is None:
        receipt["termination"] = "TIMEOUT"
    else:
        receipt.update(
            {
                "returncode": process.returncode,
                "stderr_sha256": sha256_bytes(process.stderr),
                "stdout_sha256": sha256_bytes(process.stdout),
                "termination": "KNOWN_GUARD_OR_SIGNAL",
            }
        )
    return receipt


def _clifft_deterministic_structure(
    parsed: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "active_k_history": list(parsed["active_k_history"]),
        "num_instructions": parsed["num_instructions"],
        "pass_manifest": deepcopy(parsed["pass_manifest"]),
        "peak_rank": parsed["peak_rank"],
    }


def _symft_deterministic_structure(
    parsed: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "estimated_component_vector_work": parsed.get(
            "estimated_component_vector_work"
        ),
        "estimated_dense_vector_work": parsed.get(
            "estimated_dense_vector_work"
        ),
        "structure": normalized_symft_structure(parsed),
    }


def _require_invariant_structures(
    observations: Mapping[str, Mapping[str, Any]],
    *,
    backend: str,
) -> dict[str, Any]:
    if set(observations) != set(NONZERO_SHADOWS):
        raise ValueError(f"{backend} invariance set is incomplete")
    structures = [row["deterministic_structure"] for row in observations.values()]
    frozen = canonical_json_bytes(structures[0])
    if any(canonical_json_bytes(value) != frozen for value in structures[1:]):
        raise ValueError(
            f"{backend} primary/sign/tiny structural invariance failed"
        )
    return deepcopy(structures[0])


def collect_clifft_cell(
    *,
    distance: int,
    rounds: int,
    python_executable: Path,
    timeout_seconds: int,
) -> dict[str, Any]:
    bundle = build_shadow_bundle(distance=distance, rounds=rounds)
    observations: dict[str, dict[str, Any]] = {}
    with tempfile.TemporaryDirectory(prefix="ecs-clifft-cell.") as temporary:
        temporary_root = Path(temporary)
        for shadow in ALL_SHADOWS:
            circuit_path = temporary_root / f"{shadow}.stim"
            circuit_path.write_text(
                bundle["shadows"][shadow]["text"], encoding="utf-8"
            )
            command = [
                str(python_executable),
                str(Path(__file__).resolve(strict=True)),
                "--clifft-worker",
                str(circuit_path),
            ]
            try:
                process = _run_external_command(
                    command, timeout_seconds=timeout_seconds
                )
            except subprocess.TimeoutExpired:
                return censored_metric(
                    "CLIFFT_COMPILE_TIMEOUT",
                    metric="k_max_clifft_squeeze_no_peephole",
                    route="clifft_frame",
                    resource_receipt=_resource_receipt(
                        backend="clifft",
                        shadow=shadow,
                        timeout_seconds=timeout_seconds,
                        process=None,
                    ),
                )
            stderr_text = process.stderr.decode("utf-8", errors="replace")
            known_guard = "peak active rank" in stderr_text and ">= 60" in stderr_text
            if process.returncode != 0:
                if known_guard or process.returncode < 0:
                    return censored_metric(
                        "CLIFFT_PEAK_RANK_GUARD_OR_RESOURCE_SIGNAL",
                        metric="k_max_clifft_squeeze_no_peephole",
                        route="clifft_frame",
                        resource_receipt=_resource_receipt(
                            backend="clifft",
                            shadow=shadow,
                            timeout_seconds=timeout_seconds,
                            process=process,
                        ),
                    )
                raise RuntimeError(
                    "Clifft worker failed before a qualified observation: "
                    + stderr_text[:2000]
                )
            parsed = parse_clifft_worker_output(process.stdout)
            deterministic = _clifft_deterministic_structure(parsed)
            observations[shadow] = {
                "deterministic_structure": deterministic,
                "stderr_sha256": sha256_bytes(process.stderr),
                "stdout_sha256": sha256_bytes(process.stdout),
                "worker": parsed,
            }

    nonzero = {
        shadow: observations[shadow] for shadow in NONZERO_SHADOWS
    }
    deterministic = _require_invariant_structures(
        nonzero, backend="Clifft"
    )
    representative = observations["primary_plus"]["worker"]
    inert = observations["inert"]
    history = list(deterministic["active_k_history"])
    history_sha256 = sha256_bytes(canonical_json_bytes(history))
    return {
        "active_k_history": history,
        "burden": int(representative["burden"]),
        "controls": {
            "inert": {
                "active_k_history": inert["deterministic_structure"][
                    "active_k_history"
                ],
                "circuit_sha256": bundle["shadows"]["inert"]["sha256"],
                "k_max": inert["worker"][
                    "k_max_clifft_squeeze_no_peephole"
                ],
                "num_instructions": inert["worker"]["num_instructions"],
                "pass_manifest": deepcopy(inert["worker"]["pass_manifest"]),
                "stdout_sha256": inert["stdout_sha256"],
                "structural_output_sha256": sha256_bytes(
                    canonical_json_bytes(inert["deterministic_structure"])
                ),
            },
            "nonzero_primary_sign_tiny_invariance": "PASS",
        },
        "identity": {
            "active_k_history_sha256": history_sha256,
            "circuit_sha256": {
                shadow: bundle["shadows"][shadow]["sha256"]
                for shadow in NONZERO_SHADOWS
            },
            "extension_sha256": representative["extension_sha256"],
            "metric": "k_max_clifft_squeeze_no_peephole",
            "num_instructions": representative["num_instructions"],
            "pass_manifest": deepcopy(representative["pass_manifest"]),
            "python_version": representative["python_version"],
            "route": "clifft_frame",
            "structural_output_sha256": sha256_bytes(
                canonical_json_bytes(deterministic)
            ),
            "variant_stdout_sha256": {
                shadow: observations[shadow]["stdout_sha256"]
                for shadow in NONZERO_SHADOWS
            },
            "variant_structural_output_sha256": {
                shadow: sha256_bytes(
                    canonical_json_bytes(
                        observations[shadow]["deterministic_structure"]
                    )
                )
                for shadow in NONZERO_SHADOWS
            },
            "version": representative["version"],
        },
        "status": "EXACT",
        "value": representative["k_max_clifft_squeeze_no_peephole"],
    }


def collect_symft_cell(
    *,
    distance: int,
    rounds: int,
    executable: Path,
    timeout_seconds: int,
) -> dict[str, Any]:
    bundle = build_shadow_bundle(distance=distance, rounds=rounds)
    observations: dict[str, dict[str, Any]] = {}
    with tempfile.TemporaryDirectory(prefix="ecs-symft-cell.") as temporary:
        temporary_root = Path(temporary)
        for shadow in ALL_SHADOWS:
            circuit_path = temporary_root / f"{shadow}.stim"
            circuit_path.write_text(
                bundle["shadows"][shadow]["text"], encoding="utf-8"
            )
            try:
                process = _run_external_command(
                    [str(executable), str(circuit_path)],
                    timeout_seconds=timeout_seconds,
                )
            except subprocess.TimeoutExpired:
                return {
                    **censored_metric(
                        "SYMFT_PLAN_TIMEOUT",
                        metric="k_max_symft",
                        route="symft_diagnostic",
                        resource_receipt=_resource_receipt(
                            backend="symft",
                            shadow=shadow,
                            timeout_seconds=timeout_seconds,
                            process=None,
                        ),
                    ),
                    "headline_eligible": False,
                }
            stderr_text = process.stderr.decode("utf-8", errors="replace")
            known_guard = (
                "active qubit count is too large for machine basis indices"
                in stderr_text
            )
            if process.returncode != 0:
                if known_guard or process.returncode < 0:
                    return {
                        **censored_metric(
                            "SYMFT_MACHINE_INDEX_GUARD_OR_RESOURCE_SIGNAL",
                            metric="k_max_symft",
                            route="symft_diagnostic",
                            resource_receipt=_resource_receipt(
                                backend="symft",
                                shadow=shadow,
                                timeout_seconds=timeout_seconds,
                                process=process,
                            ),
                        ),
                        "headline_eligible": False,
                    }
                raise RuntimeError(
                    "SymFT planner failed before a qualified observation: "
                    + stderr_text[:2000]
                )
            parsed = parse_symft_plan_output(
                process.stdout.decode("utf-8", errors="strict")
            )
            deterministic = _symft_deterministic_structure(parsed)
            observations[shadow] = {
                "deterministic_structure": deterministic,
                "stderr_sha256": sha256_bytes(process.stderr),
                "stdout_sha256": sha256_bytes(process.stdout),
            }

    nonzero = {
        shadow: observations[shadow] for shadow in NONZERO_SHADOWS
    }
    deterministic = _require_invariant_structures(nonzero, backend="SymFT")
    structure = deterministic["structure"]
    inert = observations["inert"]
    k_max = int(structure["max_active_qubits"])
    return {
        "b_frame_symft_monolithic": 1 << k_max,
        "controls": {
            "inert": {
                "circuit_sha256": bundle["shadows"]["inert"]["sha256"],
                "deterministic_structure": inert["deterministic_structure"],
                "stdout_sha256": inert["stdout_sha256"],
                "structural_output_sha256": sha256_bytes(
                    canonical_json_bytes(inert["deterministic_structure"])
                ),
            },
            "nonzero_primary_sign_tiny_invariance": "PASS",
        },
        "deterministic_structure": deterministic,
        "headline_eligible": False,
        "identity": {
            "circuit_sha256": {
                shadow: bundle["shadows"][shadow]["sha256"]
                for shadow in NONZERO_SHADOWS
            },
            "executable_sha256": sha256_file(executable),
            "metric": "k_max_symft",
            "route": "symft_diagnostic",
            "structural_output_sha256": sha256_bytes(
                canonical_json_bytes(deterministic)
            ),
            "variant_stdout_sha256": {
                shadow: observations[shadow]["stdout_sha256"]
                for shadow in NONZERO_SHADOWS
            },
            "variant_structural_output_sha256": {
                shadow: sha256_bytes(
                    canonical_json_bytes(
                        observations[shadow]["deterministic_structure"]
                    )
                )
                for shadow in NONZERO_SHADOWS
            },
        },
        "status": "EXACT",
        "value": k_max,
    }


def instrument_identity() -> dict[str, Any]:
    oracle_path = (
        REPO
        / "scripts"
        / "external_baselines"
        / "no_cutoff_structure_census_exact_oracle.py"
    )
    stim = _require_stim()
    return {
        "angle_serializations": verify_angle_serializations(),
        "canonical_json": "json.dumps(allow_nan=False,indent=2,sort_keys=True)+LF",
        "exact_oracle_sha256": sha256_file(oracle_path),
        "python_version": sys.version.split()[0],
        "serializer_source_sha256": sha256_file(Path(__file__).resolve(strict=True)),
        "stim_version": stim.__version__,
    }


def run_structure_census(
    *,
    clifft_python: Path,
    symft_plan: Path,
    clifft_source: Path,
    symft_source: Path,
    timeout_seconds: int,
) -> dict[str, Any]:
    """Execute only compile/planning structure over the frozen eight cells."""

    clifft_python_resolved = clifft_python.absolute()
    symft_plan_resolved = symft_plan.absolute()
    for label, executable in (
        ("Clifft Python", clifft_python_resolved),
        ("SymFT planner", symft_plan_resolved),
    ):
        if not executable.is_file() or not os.access(executable, os.X_OK):
            raise ValueError(f"{label} is not an executable file: {executable}")
    clifft_preflight = verify_external_source(
        clifft_source,
        expected_commit=CLIFFT_COMMIT,
        expected_tree=CLIFFT_TREE,
        anchors=_CLIFFT_SOURCE_ANCHORS,
    )
    symft_preflight = verify_external_source(
        symft_source,
        expected_commit=SYMFT_COMMIT,
        expected_tree=SYMFT_TREE,
        anchors=_SYMFT_SOURCE_ANCHORS,
    )

    clifft_observations: dict[tuple[int, int], dict[str, Any]] = {}
    symft_observations: dict[tuple[int, int], dict[str, Any]] = {}
    for distance, rounds in GRID:
        clifft_observations[(distance, rounds)] = collect_clifft_cell(
            distance=distance,
            rounds=rounds,
            python_executable=clifft_python_resolved,
            timeout_seconds=timeout_seconds,
        )
        symft_observations[(distance, rounds)] = collect_symft_cell(
            distance=distance,
            rounds=rounds,
            executable=symft_plan_resolved,
            timeout_seconds=timeout_seconds,
        )

    clifft_postflight = verify_external_source(
        clifft_source,
        expected_commit=CLIFFT_COMMIT,
        expected_tree=CLIFFT_TREE,
        anchors=_CLIFFT_SOURCE_ANCHORS,
    )
    symft_postflight = verify_external_source(
        symft_source,
        expected_commit=SYMFT_COMMIT,
        expected_tree=SYMFT_TREE,
        anchors=_SYMFT_SOURCE_ANCHORS,
    )
    if clifft_postflight != clifft_preflight:
        raise ValueError("Clifft source identity changed during census")
    if symft_postflight != symft_preflight:
        raise ValueError("SymFT source identity changed during census")

    external_sources = {
        "clifft": {
            **clifft_preflight,
            "build_dependency_lock_attested": False,
            "python_executable_sha256": sha256_file(clifft_python_resolved),
        },
        "symft": {
            **symft_preflight,
            "build_dependency_lock_attested": False,
            "planner_executable_sha256": sha256_file(symft_plan_resolved),
        },
    }
    return assemble_structure_census_report(
        clifft_observations=clifft_observations,
        symft_observations=symft_observations,
        external_sources=external_sources,
    )


def _clifft_worker(circuit_path: Path) -> int:
    import clifft
    import clifft._clifft_core as clifft_core

    text = circuit_path.read_text(encoding="utf-8")
    if contains_stochastic_channel(text):
        raise ValueError("refusing Clifft input with stochastic channels")
    manager = clifft.HirPassManager()
    manager.add(clifft.StatevectorSqueezePass())
    program = clifft.compile(
        text,
        normalize_syndromes=False,
        hir_passes=manager,
        bytecode_passes=None,
    )
    history = [int(value) for value in program.active_k_history]
    extension = Path(clifft_core.__file__).resolve(strict=True)
    version_value = clifft.version()
    payload = {
        "_schema": CLIFFT_WORKER_SCHEMA,
        "active_k_history": history,
        "extension_sha256": sha256_file(extension),
        "num_instructions": int(program.num_instructions),
        "pass_manifest": {
            "bytecode_passes": None,
            "hir_passes": ["StatevectorSqueezePass"],
            "normalize_syndromes": False,
        },
        "peak_rank": int(program.peak_rank),
        "python_version": sys.version.split()[0],
        "version": str(version_value),
    }
    if len(history) != payload["num_instructions"]:
        raise RuntimeError("Clifft active history length mismatch")
    if max(history, default=0) != payload["peak_rank"]:
        raise RuntimeError("Clifft peak rank mismatch")
    sys.stdout.buffer.write(canonical_json_bytes(payload))
    return 0


def iter_metric_leaves(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        if "status" in value:
            yield value
            return
        for child in value.values():
            yield from iter_metric_leaves(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_metric_leaves(child)


def _unavailable_cell_metrics() -> dict[str, Any]:
    pair = unavailable_metric(
        "NO_EXACT_PAIR_OWNER",
        metric="n_pauli_pair_states_peak",
        route="exact_pair",
    )
    dynamic_add = unavailable_metric(
        "NO_EXACT_DYNAMIC_ADD_OWNER",
        metric="n_exact_pair_add_nodes_peak",
        route="dynamic_add",
    )
    width_reason = "NO_CANONICAL_RETAINED_RECORD_TN_OWNER"
    return {
        "delta_tv_cert": unavailable_metric(
            "UNANCHORED_FULL_RECORD",
            metric="delta_tv_cert",
            route="complete_record",
        ),
        "k_max": {
            "clifft": unavailable_metric(
                "EXTERNAL_ADAPTER_NOT_RUN",
                metric="k_max_clifft_squeeze_no_peephole",
                route="clifft_frame",
            ),
            "symft": {
                **unavailable_metric(
                    "EXTERNAL_ADAPTER_NOT_RUN",
                    metric="k_max_symft",
                    route="symft_diagnostic",
                ),
                "headline_eligible": False,
            },
        },
        "n_dd": dynamic_add,
        "n_pair": pair,
        "tw": {
            "record_boundary_constrained_induced_width": unavailable_metric(
                width_reason,
                metric="record_boundary_constrained_induced_width",
                route="retained_boundary_tn",
            ),
            "terminal_record_representation": "factorized_boundary_factors",
            "tn_record_boundary_peak_dense_entries": unavailable_metric(
                width_reason,
                metric="tn_record_boundary_peak_dense_entries",
                route="retained_boundary_tn",
            ),
            "tn_record_boundary_peak_dense_entries_log2": unavailable_metric(
                width_reason,
                metric="tn_record_boundary_peak_dense_entries_log2",
                route="retained_boundary_tn",
            ),
        },
    }


def _disposition_for_unavailable_route(route: str) -> dict[str, Any]:
    return {
        "aggregate": {
            "burden_identity": route,
            "indeterminate_reasons": ["MISSING_OR_INELIGIBLE_TARGET_METRICS"],
            "structure_disposition": "INDETERMINATE",
        },
        "distance_3": {
            "burden_identity": route,
            **adjudicate_burden_series({}),
        },
        "distance_5": {
            "burden_identity": route,
            **adjudicate_burden_series({}),
        },
    }


def _aggregate_structure_disposition(
    *,
    burden_identity: str,
    distance_3: Mapping[str, Any],
    distance_5: Mapping[str, Any],
) -> dict[str, Any]:
    by_distance = {
        "distance_3": distance_3.get("structure_disposition"),
        "distance_5": distance_5.get("structure_disposition"),
    }
    if "KILL_STRUCTURE" in by_distance.values():
        disposition = "KILL_STRUCTURE"
        reasons: list[str] = []
    elif set(by_distance.values()) == {"NOT_KILLED_ON_FROZEN_GRID"}:
        disposition = "NOT_KILLED_ON_FROZEN_GRID"
        reasons = []
    else:
        disposition = "INDETERMINATE"
        reasons = ["AT_LEAST_ONE_DISTANCE_SLICE_INDETERMINATE"]
    return {
        "burden_identity": burden_identity,
        "distance_dispositions": by_distance,
        "indeterminate_reasons": reasons,
        "structure_disposition": disposition,
    }


def assemble_structure_census_report(
    *,
    clifft_observations: Mapping[tuple[int, int], Mapping[str, Any]],
    symft_observations: Mapping[tuple[int, int], Mapping[str, Any]],
    external_sources: Mapping[str, Any],
) -> dict[str, Any]:
    """Join already-qualified external observations into the frozen report.

    This join cannot populate the absent pair, dynamic-ADD, retained-boundary,
    or full-Record oracle owners.  It therefore always keeps certification
    unanchored and solver permission code-blocked.
    """

    frozen_cells = set(GRID)
    if set(clifft_observations) != frozen_cells:
        raise ValueError("Clifft observations do not cover exactly the frozen grid")
    if set(symft_observations) != frozen_cells:
        raise ValueError("SymFT observations do not cover exactly the frozen grid")

    report = build_fail_closed_report()
    cells_by_key = {
        (int(cell["distance"]), int(cell["rounds"])): cell
        for cell in report["cells"]
    }
    for cell_key in GRID:
        clifft_leaf = deepcopy(dict(clifft_observations[cell_key]))
        symft_leaf = deepcopy(dict(symft_observations[cell_key]))
        _validate_leaf(clifft_leaf)
        _validate_leaf(symft_leaf)
        if clifft_leaf.get("identity", {}).get("route") != "clifft_frame":
            raise ValueError("Clifft observation has the wrong route identity")
        if symft_leaf.get("identity", {}).get("route") != "symft_diagnostic":
            raise ValueError("SymFT observation has the wrong route identity")
        if symft_leaf.get("headline_eligible") is not False:
            raise ValueError("SymFT observation must remain headline-ineligible")
        cells_by_key[cell_key]["metrics"]["k_max"] = {
            "clifft": clifft_leaf,
            "symft": symft_leaf,
        }

    burden_identity = "2**k_max_clifft_squeeze_no_peephole"
    fixed_distance: dict[int, dict[str, Any]] = {}
    for distance in (3, 5):
        series = {
            rounds: clifft_observations[(distance, rounds)]
            for rounds in ROUNDS
        }
        fixed_distance[distance] = {
            "burden_identity": burden_identity,
            **adjudicate_burden_series(series),
        }
    report["structure_dispositions"]["clifft_frame"] = {
        "aggregate": _aggregate_structure_disposition(
            burden_identity=burden_identity,
            distance_3=fixed_distance[3],
            distance_5=fixed_distance[5],
        ),
        "distance_3": fixed_distance[3],
        "distance_5": fixed_distance[5],
    }
    report["external_sources"] = deepcopy(dict(external_sources))
    report["report_status"] = "VALID_BOUNDED_STRUCTURE_CENSUS_CODE_BLOCKED"
    validate_report(report)
    return report


def build_fail_closed_report() -> dict[str, Any]:
    manifest = verify_fixture_manifest()
    prereg_raw = PREREG_PATH.read_bytes()
    prereg_text = prereg_raw.decode("utf-8")
    if "ACTIVE PRE-REGISTRATION, CODE_BLOCKED" not in prereg_text:
        raise ValueError("preregistration is not active and code-blocked")
    cells = [
        {
            "distance": identity["distance"],
            "fixture_identity": identity,
            "metrics": _unavailable_cell_metrics(),
            "rounds": identity["rounds"],
        }
        for identity in manifest["cells"]
    ]
    report = {
        "_schema": REPORT_SCHEMA,
        "cells": cells,
        "certification_verdict": "UNANCHORED",
        "faithfulness_disposition": "UNAVAILABLE",
        "fixture_manifest": {
            "path": str(FIXTURE_MANIFEST_PATH.relative_to(REPO)),
            "sha256": FIXTURE_MANIFEST_SHA256,
        },
        "instrument": instrument_identity(),
        "preregistration": {
            "path": str(PREREG_PATH.relative_to(REPO)),
            "sha256": sha256_bytes(prereg_raw),
            "status": "ACTIVE_PRE_REGISTRATION_CODE_BLOCKED",
        },
        "report_status": "VALID_FAIL_CLOSED",
        "solver_permission": "CODE_BLOCKED",
        "structure_dispositions": {
            route: _disposition_for_unavailable_route(route)
            for route in ROUTE_KEYS
        },
    }
    validate_report(report)
    return report


def _walk_keys(value: Any) -> Iterator[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def _validate_leaf(leaf: Mapping[str, Any]) -> None:
    status = leaf.get("status")
    if status not in STATUSES:
        raise ValueError(f"invalid metric status: {status!r}")
    identity = leaf.get("identity")
    if not isinstance(identity, dict) or not identity.get("metric") or not identity.get(
        "route"
    ):
        raise ValueError("metric leaf lacks route identity")
    if status == "EXACT":
        if "value" not in leaf:
            raise ValueError("exact metric lacks value")
    elif status in {"CERTIFIED_INTERVAL", "BOUNDS"}:
        if "lower" not in leaf or "upper" not in leaf:
            raise ValueError("interval/bounds metric lacks endpoints")
    else:
        forbidden_numeric = {"value", "lower", "upper", "estimate"} & leaf.keys()
        if forbidden_numeric:
            raise ValueError("numeric field is forbidden on unavailable/censored metric")
        if not isinstance(leaf.get("reason"), str) or not leaf["reason"]:
            raise ValueError("unavailable/censored metric lacks reason")
        if status == "CENSORED_RESOURCE" and not isinstance(
            leaf.get("resource_receipt"), dict
        ):
            raise ValueError("censored metric lacks resource receipt")


def _require_nonnegative_int(value: Any, *, name: str, maximum: int) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 0
        or value > maximum
    ):
        raise ValueError(f"{name} must be an integer in [0,{maximum}]")
    return value


def _require_sha256(value: Any, *, name: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a SHA-256 digest")
    return value


def _require_variant_sha256_map(value: Any, *, name: str) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != set(NONZERO_SHADOWS):
        raise ValueError(f"{name} does not cover the four frozen shadows")
    for shadow, digest in value.items():
        _require_sha256(digest, name=f"{name}.{shadow}")
    return value


def _validate_clifft_observation(leaf: Mapping[str, Any]) -> None:
    identity = leaf.get("identity")
    if not isinstance(identity, dict):
        raise ValueError("Clifft observation lacks identity")
    if identity.get("metric") != "k_max_clifft_squeeze_no_peephole":
        raise ValueError("wrong Clifft metric identity")
    if identity.get("route") != "clifft_frame":
        raise ValueError("wrong Clifft route identity")
    if leaf.get("status") != "EXACT":
        return

    k_max = _require_nonnegative_int(
        leaf.get("value"), name="Clifft k_max", maximum=59
    )
    if leaf.get("burden") != 1 << k_max:
        raise ValueError("Clifft burden must equal 2**k_max exactly")
    history = leaf.get("active_k_history")
    if not isinstance(history, list) or any(
        isinstance(value, bool) or not isinstance(value, int) or value < 0
        for value in history
    ):
        raise ValueError("Clifft report lacks an exact active history")
    if max(history, default=0) != k_max:
        raise ValueError("Clifft active history disagrees with k_max")
    instruction_count = identity.get("num_instructions")
    if (
        isinstance(instruction_count, bool)
        or not isinstance(instruction_count, int)
        or instruction_count != len(history)
    ):
        raise ValueError("Clifft active history length mismatch")
    expected_pass_manifest = {
        "bytecode_passes": None,
        "hir_passes": ["StatevectorSqueezePass"],
        "normalize_syndromes": False,
    }
    if identity.get("pass_manifest") != expected_pass_manifest:
        raise ValueError("Clifft pass manifest is not squeeze-only")
    _require_sha256(identity.get("extension_sha256"), name="Clifft extension")
    if identity.get("active_k_history_sha256") != sha256_bytes(
        canonical_json_bytes(history)
    ):
        raise ValueError("Clifft active history hash mismatch")
    deterministic = {
        "active_k_history": history,
        "num_instructions": instruction_count,
        "pass_manifest": expected_pass_manifest,
        "peak_rank": k_max,
    }
    structural_sha256 = sha256_bytes(canonical_json_bytes(deterministic))
    if identity.get("structural_output_sha256") != structural_sha256:
        raise ValueError("Clifft structural output hash mismatch")
    _require_variant_sha256_map(
        identity.get("circuit_sha256"), name="Clifft circuit hashes"
    )
    _require_variant_sha256_map(
        identity.get("variant_stdout_sha256"), name="Clifft worker outputs"
    )
    variant_structures = _require_variant_sha256_map(
        identity.get("variant_structural_output_sha256"),
        name="Clifft variant structures",
    )
    if set(variant_structures.values()) != {structural_sha256}:
        raise ValueError("Clifft four-shadow structural invariance is unproven")
    controls = leaf.get("controls")
    if (
        not isinstance(controls, dict)
        or controls.get("nonzero_primary_sign_tiny_invariance") != "PASS"
        or not isinstance(controls.get("inert"), dict)
    ):
        raise ValueError("Clifft controls are incomplete")
    inert = controls["inert"]
    if _require_nonnegative_int(
        inert.get("k_max"), name="inert Clifft k", maximum=59
    ) != 0:
        raise ValueError("Clifft inert control must have k=0")
    if not isinstance(inert.get("active_k_history"), list) or any(
        value != 0 for value in inert["active_k_history"]
    ):
        raise ValueError("Clifft inert history is missing")
    inert_count = inert.get("num_instructions")
    if (
        isinstance(inert_count, bool)
        or not isinstance(inert_count, int)
        or inert_count != len(inert["active_k_history"])
        or inert.get("pass_manifest") != expected_pass_manifest
    ):
        raise ValueError("Clifft inert structure is inconsistent")
    inert_deterministic = {
        "active_k_history": inert["active_k_history"],
        "num_instructions": inert_count,
        "pass_manifest": expected_pass_manifest,
        "peak_rank": 0,
    }
    for key in ("circuit_sha256", "stdout_sha256"):
        _require_sha256(inert.get(key), name=f"Clifft inert {key}")
    if inert.get("structural_output_sha256") != sha256_bytes(
        canonical_json_bytes(inert_deterministic)
    ):
        raise ValueError("Clifft inert structural output hash mismatch")


def _validate_symft_observation(leaf: Mapping[str, Any]) -> None:
    identity = leaf.get("identity")
    if not isinstance(identity, dict):
        raise ValueError("SymFT observation lacks identity")
    if identity.get("metric") != "k_max_symft":
        raise ValueError("wrong SymFT metric identity")
    if identity.get("route") != "symft_diagnostic":
        raise ValueError("wrong SymFT route identity")
    if leaf.get("headline_eligible") is not False:
        raise ValueError("SymFT must remain headline-ineligible")
    if leaf.get("status") != "EXACT":
        return

    k_max = _require_nonnegative_int(
        leaf.get("value"), name="SymFT k_max", maximum=61
    )
    if leaf.get("b_frame_symft_monolithic") != 1 << k_max:
        raise ValueError("SymFT monolithic burden must equal 2**k_max exactly")
    deterministic = leaf.get("deterministic_structure")
    if not isinstance(deterministic, dict) or not isinstance(
        deterministic.get("structure"), dict
    ):
        raise ValueError("SymFT deterministic structure is missing")
    structure = deterministic["structure"]
    if structure.get("max_active_qubits") != k_max:
        raise ValueError("SymFT structure disagrees with k_max")
    if structure.get("dense_peak_dimension") != 1 << k_max:
        raise ValueError("SymFT dense dimension disagrees with k_max")
    for key in (
        "estimated_dense_vector_work",
        "estimated_component_vector_work",
    ):
        value = deterministic.get(key)
        try:
            decimal_value = Decimal(value)
        except (InvalidOperation, TypeError) as error:
            raise ValueError(f"invalid SymFT work estimate: {key}") from error
        if not decimal_value.is_finite() or decimal_value < 0:
            raise ValueError(f"invalid SymFT work estimate: {key}")
    structural_sha256 = sha256_bytes(canonical_json_bytes(deterministic))
    if identity.get("structural_output_sha256") != structural_sha256:
        raise ValueError("SymFT structural output hash mismatch")
    _require_sha256(identity.get("executable_sha256"), name="SymFT executable")
    _require_variant_sha256_map(
        identity.get("circuit_sha256"), name="SymFT circuit hashes"
    )
    _require_variant_sha256_map(
        identity.get("variant_stdout_sha256"), name="SymFT planner outputs"
    )
    variant_structures = _require_variant_sha256_map(
        identity.get("variant_structural_output_sha256"),
        name="SymFT variant structures",
    )
    if set(variant_structures.values()) != {structural_sha256}:
        raise ValueError("SymFT four-shadow structural invariance is unproven")
    controls = leaf.get("controls")
    if (
        not isinstance(controls, dict)
        or controls.get("nonzero_primary_sign_tiny_invariance") != "PASS"
        or not isinstance(controls.get("inert"), dict)
    ):
        raise ValueError("SymFT controls are incomplete")
    inert = controls["inert"]
    for key in ("circuit_sha256", "stdout_sha256"):
        _require_sha256(inert.get(key), name=f"SymFT inert {key}")
    inert_structure = inert.get("deterministic_structure")
    if not isinstance(inert_structure, dict):
        raise ValueError("SymFT inert structure is missing")
    inert_structural_fields = inert_structure.get("structure")
    if (
        not isinstance(inert_structural_fields, dict)
        or inert_structural_fields.get("max_active_qubits") != 0
        or inert_structural_fields.get("dense_peak_dimension") != 1
    ):
        raise ValueError("SymFT inert control must have k=0 and dense dimension 1")
    if inert.get("structural_output_sha256") != sha256_bytes(
        canonical_json_bytes(inert_structure)
    ):
        raise ValueError("SymFT inert structural output hash mismatch")


def _validate_external_sources(value: Any) -> None:
    if not isinstance(value, dict) or set(value) != {"clifft", "symft"}:
        raise ValueError("observed report lacks both external source identities")
    specifications = {
        "clifft": (
            CLIFFT_COMMIT,
            CLIFFT_TREE,
            _CLIFFT_SOURCE_ANCHORS,
            "python_executable_sha256",
        ),
        "symft": (
            SYMFT_COMMIT,
            SYMFT_TREE,
            _SYMFT_SOURCE_ANCHORS,
            "planner_executable_sha256",
        ),
    }
    for backend, (commit, tree, anchors, executable_key) in specifications.items():
        identity = value[backend]
        if not isinstance(identity, dict):
            raise ValueError(f"invalid {backend} source identity")
        if identity.get("commit") != commit or identity.get("tree") != tree:
            raise ValueError(f"wrong pinned {backend} source identity")
        if identity.get("pristine") is not True:
            raise ValueError(f"{backend} source was not pristine")
        if not isinstance(identity.get("build_dependency_lock_attested"), bool):
            raise ValueError(f"{backend} build lock status is missing")
        anchor_hashes = identity.get("anchor_sha256")
        if not isinstance(anchor_hashes, dict) or set(anchor_hashes) != set(anchors):
            raise ValueError(f"{backend} source anchors are incomplete")
        for relative, digest in anchor_hashes.items():
            _require_sha256(digest, name=f"{backend} source anchor {relative}")
        _require_sha256(identity.get(executable_key), name=f"{backend} executable")


def validate_report(report: Mapping[str, Any]) -> None:
    if report.get("_schema") != REPORT_SCHEMA:
        raise ValueError("wrong census report schema")
    keys = set(_walk_keys(report))
    truth = sorted(keys & _FORBIDDEN_TRUTH_KEYS)
    if truth:
        raise ValueError(f"evaluator truth field is forbidden: {truth}")
    proxy = sorted(keys & _FORBIDDEN_PROXY_KEYS)
    if proxy:
        raise ValueError(f"forbidden proxy field {proxy[0]}")
    cells = report.get("cells")
    if not isinstance(cells, list) or [
        (row.get("distance"), row.get("rounds"))
        for row in cells
        if isinstance(row, dict)
    ] != list(GRID):
        raise ValueError("cells do not match canonical grid order")
    for cell in cells:
        metrics = cell.get("metrics")
        if not isinstance(metrics, dict) or set(metrics) != METRIC_FAMILIES:
            raise ValueError("cell does not contain exactly five metric families")
        k_max = metrics["k_max"]
        if not isinstance(k_max, dict) or set(k_max) != {"clifft", "symft"}:
            raise ValueError("invalid route-qualified k_max family")
        _validate_clifft_observation(k_max["clifft"])
        _validate_symft_observation(k_max["symft"])
        n_dd = metrics["n_dd"]
        if n_dd.get("status") == "EXACT" and n_dd.get("identity", {}).get(
            "metric"
        ) != "n_exact_pair_add_nodes_peak":
            raise ValueError("dynamic ADD headline cannot be populated by final PMF MTBDD")
        tw = metrics["tw"]
        expected_tw = {
            "record_boundary_constrained_induced_width",
            "terminal_record_representation",
            "tn_record_boundary_peak_dense_entries",
            "tn_record_boundary_peak_dense_entries_log2",
        }
        if not isinstance(tw, dict) or set(tw) != expected_tw:
            raise ValueError("invalid retained-boundary tensor family")
        if tw["terminal_record_representation"] != "factorized_boundary_factors":
            raise ValueError("wrong terminal Record representation")
        for leaf in iter_metric_leaves(metrics):
            _validate_leaf(leaf)
    dispositions = report.get("structure_dispositions")
    if not isinstance(dispositions, dict) or set(dispositions) != set(ROUTE_KEYS):
        raise ValueError("wrong structure-disposition route keys")
    for route, value in dispositions.items():
        if not isinstance(value, dict) or set(value) != {
            "distance_3",
            "distance_5",
            "aggregate",
        }:
            raise ValueError(f"wrong disposition shape for {route}")
    if report.get("faithfulness_disposition") != "UNAVAILABLE":
        raise ValueError("current target faithfulness must be unavailable")
    if report.get("certification_verdict") != "UNANCHORED":
        raise ValueError("current target certification must be UNANCHORED")
    if report.get("solver_permission") != "CODE_BLOCKED":
        raise ValueError("solver permission must remain CODE_BLOCKED")
    report_status = report.get("report_status")
    if report_status == "VALID_BOUNDED_STRUCTURE_CENSUS_CODE_BLOCKED":
        _validate_external_sources(report.get("external_sources"))
        cells_by_key = {
            (int(cell["distance"]), int(cell["rounds"])): cell
            for cell in cells
        }
        burden_identity = "2**k_max_clifft_squeeze_no_peephole"
        fixed_distance: dict[int, dict[str, Any]] = {}
        for distance in (3, 5):
            fixed_distance[distance] = {
                "burden_identity": burden_identity,
                **adjudicate_burden_series(
                    {
                        rounds: cells_by_key[(distance, rounds)]["metrics"][
                            "k_max"
                        ]["clifft"]
                        for rounds in ROUNDS
                    }
                ),
            }
        expected_frame = {
            "aggregate": _aggregate_structure_disposition(
                burden_identity=burden_identity,
                distance_3=fixed_distance[3],
                distance_5=fixed_distance[5],
            ),
            "distance_3": fixed_distance[3],
            "distance_5": fixed_distance[5],
        }
        if dispositions["clifft_frame"] != expected_frame:
            raise ValueError("Clifft structure disposition is not recomputable")
    elif report_status != "VALID_FAIL_CLOSED":
        raise ValueError("invalid census report status")
    instrument = report.get("instrument")
    if not isinstance(instrument, dict):
        raise ValueError("report lacks instrument identity")
    for key in ("serializer_source_sha256", "exact_oracle_sha256"):
        if not isinstance(instrument.get(key), str) or not _SHA256.fullmatch(
            instrument[key]
        ):
            raise ValueError(f"invalid instrument identity field: {key}")
    canonical_json_bytes(report)


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
        directory_descriptor = os.open(parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        temporary.unlink(missing_ok=True)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clifft-worker", type=Path)
    parser.add_argument("--emit-fail-closed", type=Path)
    parser.add_argument("--run-structure-census", type=Path)
    parser.add_argument("--verify-fixture", action="store_true")
    parser.add_argument("--clifft-python", type=Path)
    parser.add_argument(
        "--clifft-source", type=Path, default=REPO / "external" / "Clifft"
    )
    parser.add_argument("--symft-plan", type=Path)
    parser.add_argument(
        "--symft-source", type=Path, default=REPO / "external" / "SOFT"
    )
    parser.add_argument("--timeout-seconds", type=int, default=300)
    args = parser.parse_args(argv)
    selected = sum(
        (
            args.clifft_worker is not None,
            args.emit_fail_closed is not None,
            args.run_structure_census is not None,
            args.verify_fixture,
        )
    )
    if selected != 1:
        parser.error("select exactly one execution mode")
    if args.run_structure_census is not None:
        if args.clifft_python is None or args.symft_plan is None:
            parser.error(
                "--run-structure-census requires --clifft-python and --symft-plan"
            )
        if args.timeout_seconds <= 0:
            parser.error("--timeout-seconds must be positive")
    return args


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.clifft_worker is not None:
        return _clifft_worker(args.clifft_worker)
    if args.verify_fixture:
        sys.stdout.buffer.write(canonical_json_bytes(verify_fixture_manifest()))
        return 0
    if args.run_structure_census is not None:
        report = run_structure_census(
            clifft_python=args.clifft_python,
            symft_plan=args.symft_plan,
            clifft_source=args.clifft_source,
            symft_source=args.symft_source,
            timeout_seconds=args.timeout_seconds,
        )
        _atomic_publish_exclusive(
            args.run_structure_census, canonical_json_bytes(report)
        )
        return 0
    report = build_fail_closed_report()
    _atomic_publish_exclusive(args.emit_fail_closed, canonical_json_bytes(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
