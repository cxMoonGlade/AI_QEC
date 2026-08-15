#!/usr/bin/env python3
"""Signed Stim--SDIM frame differential for the frozen n=8 fixture.

This worker deliberately has no PEPS, state-vector, fidelity, or timing
surface.  SDIM is exercised through the fork's public dimension-two
``SdimCliffordFrame`` bridge and is corroboration only, never ground truth.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import inspect
import json
import os
from pathlib import Path
import platform
import re
import stat
import subprocess
import sys
from typing import Any, Mapping, Sequence


WORKER_SCHEMA = (
    "error_coupling_simulator.external."
    "gcapeps_n8_r3_sdim_frame_worker.v1"
)
FIXTURE_SCHEMA = "error_coupling_simulator.external.gcapeps_n8_r3_fixture.v1"
EXPECTED_FIXTURE_SHA256 = (
    "a494512a74ed20b28c067734359e9a09ab3df72ad07467160855c3c475ed0b8d"
)
EXPECTED_CLIFFORD_STREAM_SHA256 = (
    "aeb75e08b6ac4a592d31199c2eafe9ed0c968465e50d05fa45b7d139a397e50c"
)
EXPECTED_FORK_COMMIT = "6fbbf74cd36686ed30a4d8865697ce46e47056c1"
EXPECTED_FORK_TREE = "ffdfdf421fbe4d9674c2c88029710042fd18ae14"
EXPECTED_ENVIRONMENT_YAML_SHA256 = (
    "64236e0cb6dc87a90f116dbebb8ee8a73882dc41d00619af8b7d3ccc35de3431"
)
EXPECTED_PYTHON_VERSION = "3.12.13"
EXPECTED_STIM_VERSION = "1.16.0"
EXPECTED_SDIM_VERSION = "1.3.3"
EXPECTED_SDIM_INSPECTED_COMMIT = (
    "115c495b23ade35ef0f68b7299afef463129bf51"
)
EXPECTED_GCAPEPS_SOURCE_SHA256 = {
    "__init__.py": (
        "853df7503d3697bb7c78182c4bdbbe58e700e47657fde07e7664bdcf240052e1"
    ),
    "frame.py": (
        "63eff4ff2a534c3007c4441cb53bf4fdf901e881ce1f2d71d386b39713b40105"
    ),
    "pauli.py": (
        "71c7c0f68ddc215b6a59998a7ca560fc822792a9a672fbef6a30c072b367310b"
    ),
}
EXPECTED_CLIFFORD_GATES = (
    ("H", (0,)),
    ("S", (1,)),
    ("CX", (0, 4)),
    ("H", (3,)),
    ("CZ", (2, 6)),
    ("S_DAG", (7,)),
    ("SWAP", (5, 6)),
    ("CX", (6, 7)),
    ("SWAP", (5, 6)),
    ("SWAP", (1, 2)),
)
EXPECTED_PHYSICAL_TERMS = (
    (0, "IXYIZIYZ", -1, "+XXYIZZXZ"),
    (1, "YXYXXIYZ", 1, "+YXYZIZXZ"),
    (2, "YXYXYZYI", 1, "+ZXYZZZXI"),
)

TOP_LEVEL_KEYS = frozenset(
    {
        "schema",
        "worker_role",
        "fixture_identity",
        "fork_identity",
        "environment_identity",
        "runtime_identity",
        "scope",
        "initial_frame",
        "prefix_ledger",
        "term_pullbacks",
        "control",
        "sdim_frame_verdict",
        "content_sha256",
    }
)
FIXTURE_IDENTITY_KEYS = frozenset(
    {
        "path",
        "schema",
        "file_sha256",
        "canonical_sha256",
        "file_is_canonical_json",
        "n_qubits",
        "active_rank",
        "clifford_gate_stream_sha256",
        "physical_term_count",
    }
)
FORK_IDENTITY_KEYS = frozenset(
    {
        "checkout_path",
        "frozen_commit",
        "frozen_tree",
        "expected_commit_from_cli",
        "expected_tree_from_cli",
        "actual_commit",
        "actual_tree",
        "identity_verified",
        "quimb_origin_within_checkout",
    }
)
ENVIRONMENT_IDENTITY_KEYS = frozenset(
    {
        "yaml_path",
        "expected_yaml_sha256",
        "actual_yaml_sha256",
        "yaml_identity_verified",
        "bootstrap_only",
        "transitive_lock_attested",
        "wheel_bytes_attested",
        "installed_distributions",
    }
)
INSTALLED_DISTRIBUTIONS_KEYS = frozenset(
    {"record_count", "records", "canonical_sha256"}
)
DISTRIBUTION_RECORD_KEYS = frozenset(
    {"name", "normalized_name", "version", "location", "direct_url"}
)
RUNTIME_IDENTITY_KEYS = frozenset(
    {
        "python",
        "stim",
        "sdim",
        "quimb",
        "gcapeps_public_api",
        "gcapeps_frame_source",
        "gcapeps_pauli_source",
        "worker_source",
        "sdim_backend_status",
    }
)
PYTHON_IDENTITY_KEYS = frozenset(
    {
        "implementation",
        "version",
        "version_info",
        "executable",
        "resolved_executable",
        "resolved_executable_sha256",
    }
)
MODULE_IDENTITY_KEYS = frozenset(
    {
        "distribution_name",
        "distribution_version",
        "module_version",
        "origin",
        "origin_sha256",
    }
)
SOURCE_IDENTITY_KEYS = frozenset({"origin", "origin_sha256"})
SDIM_STATUS_KEYS = frozenset(
    {"name", "available", "version", "detail", "inspected_commit"}
)
SCOPE_KEYS = frozenset(
    {
        "dimension",
        "qubit_only",
        "uses_stim_bridge",
        "receives_peps",
        "emits_peps",
        "receives_state_vector",
        "emits_state_vector",
        "enters_timing_or_rss_ratio",
        "qutrit_evidence",
        "ground_truth",
        "state_action_verdict_authority",
    }
)
FRAME_SNAPSHOT_KEYS = frozenset(
    {"x_outputs", "z_outputs", "canonical_sha256"}
)
INITIAL_FRAME_KEYS = frozenset(
    {
        "stim_revision",
        "sdim_revision",
        "stim_tableau",
        "sdim_tableau",
        "tableau_exact_match",
        "revision_exact_match",
    }
)
PREFIX_ROW_KEYS = frozenset(
    {
        "index",
        "token",
        "logical_targets",
        "stim_instruction",
        "stim_revision_before",
        "stim_revision_after",
        "sdim_revision_before",
        "sdim_revision_after",
        "expected_revision_after",
        "stim_tableau",
        "sdim_tableau",
        "tableau_exact_match",
        "revision_exact_match",
    }
)
TERM_ROW_KEYS = frozenset(
    {
        "term_index",
        "physical_body",
        "input_word_phase",
        "input_signed_word",
        "expected_signed_pullback",
        "stim_signed_pullback",
        "sdim_backend_signed_pullback",
        "sdim_compared_signed_pullback",
        "flip_control_applied",
        "expected_equals_stim",
        "expected_equals_sdim",
        "stim_equals_sdim",
        "backend_stim_equals_sdim",
        "strict_match",
    }
)
CONTROL_KEYS = frozenset(
    {
        "name",
        "enabled",
        "term_index",
        "comparison_sign_flipped",
        "detected",
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


def canonical_content_sha256(report: Mapping[str, Any]) -> str:
    """Hash a report excluding its top-level self-hash."""

    body = dict(report)
    body.pop("content_sha256", None)
    return _canonical_sha256(body)


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
    raise ValueError(f"non-finite JSON constant is forbidden: {value}")


def _load_canonical_fixture(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    fixture_path = path.resolve(strict=True)
    raw = fixture_path.read_bytes()
    try:
        fixture = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("fixture is not strict UTF-8 JSON") from exc
    if not isinstance(fixture, dict):
        raise ValueError("fixture must be a JSON object")
    canonical = _canonical_json_bytes(fixture)
    digest = hashlib.sha256(canonical).hexdigest()
    file_digest = hashlib.sha256(raw).hexdigest()
    if raw != canonical:
        raise ValueError("fixture file is not exact canonical JSON")
    if digest != EXPECTED_FIXTURE_SHA256 or file_digest != digest:
        raise ValueError("fixture literal identity drifted")
    if (
        fixture.get("schema") != FIXTURE_SCHEMA
        or fixture.get("n_qubits") != 8
        or fixture.get("active_rank") != 3
    ):
        raise ValueError("fixture n=8 r=3 identity drifted")

    clifford = fixture.get("clifford")
    if not isinstance(clifford, dict):
        raise ValueError("fixture Clifford block is unavailable")
    if clifford.get("gate_stream_sha256") != EXPECTED_CLIFFORD_STREAM_SHA256:
        raise ValueError("fixture Clifford stream hash drifted")
    rows = clifford.get("gates")
    if not isinstance(rows, list) or len(rows) != len(EXPECTED_CLIFFORD_GATES):
        raise ValueError("fixture Clifford gate count drifted")
    for index, ((token, targets), row) in enumerate(
        zip(EXPECTED_CLIFFORD_GATES, rows, strict=True)
    ):
        if (
            not isinstance(row, dict)
            or row.get("index") != index
            or row.get("token") != token
            or row.get("logical_targets") != list(targets)
        ):
            raise ValueError(f"fixture Clifford row {index} drifted")

    terms = fixture.get("physical_terms")
    if not isinstance(terms, list) or len(terms) != len(
        EXPECTED_PHYSICAL_TERMS
    ):
        raise ValueError("fixture physical term count drifted")
    for expected, term in zip(EXPECTED_PHYSICAL_TERMS, terms, strict=True):
        index, body, phase, pullback = expected
        if (
            not isinstance(term, dict)
            or term.get("term_index") != index
            or term.get("pauli_body") != body
            or term.get("word_phase") != phase
            or term.get("expected_signed_pullback") != pullback
        ):
            raise ValueError(f"fixture physical term {index} drifted")

    identity = {
        "path": str(fixture_path),
        "schema": FIXTURE_SCHEMA,
        "file_sha256": file_digest,
        "canonical_sha256": digest,
        "file_is_canonical_json": True,
        "n_qubits": 8,
        "active_rank": 3,
        "clifford_gate_stream_sha256": EXPECTED_CLIFFORD_STREAM_SHA256,
        "physical_term_count": 3,
    }
    return fixture, identity


def _sha256_file(path: Path) -> str:
    resolved = path.resolve(strict=True)
    if not resolved.is_file():
        raise ValueError(f"identity origin is not a regular file: {resolved}")
    digest = hashlib.sha256()
    with resolved.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_value(checkout: Path, *arguments: str) -> str:
    process = subprocess.run(
        ["git", "-C", str(checkout), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    value = process.stdout.strip()
    if "\n" in value or not value:
        raise RuntimeError("Git identity command returned a non-scalar value")
    return value


def _verify_fork_identity(
    checkout: Path,
    *,
    expected_commit: str,
    expected_tree: str,
) -> tuple[Path, dict[str, Any]]:
    if expected_commit != EXPECTED_FORK_COMMIT:
        raise ValueError("CLI fork commit does not equal the frozen commit")
    if expected_tree != EXPECTED_FORK_TREE:
        raise ValueError("CLI fork tree does not equal the frozen tree")
    fork = checkout.resolve(strict=True)
    if not fork.is_dir():
        raise ValueError("fork checkout must be a directory")
    actual_commit = _git_value(fork, "rev-parse", "--verify", "HEAD^{commit}")
    actual_tree = _git_value(fork, "rev-parse", "--verify", "HEAD^{tree}")
    if actual_commit != expected_commit or actual_tree != expected_tree:
        raise ValueError("fork checkout identity does not match the CLI binding")
    return fork, {
        "checkout_path": str(fork),
        "frozen_commit": EXPECTED_FORK_COMMIT,
        "frozen_tree": EXPECTED_FORK_TREE,
        "expected_commit_from_cli": expected_commit,
        "expected_tree_from_cli": expected_tree,
        "actual_commit": actual_commit,
        "actual_tree": actual_tree,
        "identity_verified": True,
        "quimb_origin_within_checkout": True,
    }


def _read_direct_url(distribution: importlib.metadata.Distribution) -> Any:
    text = distribution.read_text("direct_url.json")
    if text is None:
        return None
    try:
        return json.loads(
            text,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_json_constant,
        )
    except json.JSONDecodeError as exc:
        raise ValueError("installed direct_url.json is invalid") from exc


def _normalized_distribution_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _installed_distributions() -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for distribution in importlib.metadata.distributions():
        name = distribution.metadata.get("Name")
        version = distribution.version
        if not isinstance(name, str) or not name or not version:
            raise ValueError("installed distribution lacks name or version")
        records.append(
            {
                "name": name,
                "normalized_name": _normalized_distribution_name(name),
                "version": str(version),
                "location": str(Path(distribution.locate_file("")).resolve()),
                "direct_url": _read_direct_url(distribution),
            }
        )
    records.sort(
        key=lambda row: (
            row["normalized_name"],
            row["version"],
            row["location"],
            _canonical_json_bytes(row["direct_url"]),
        )
    )
    return {
        "record_count": len(records),
        "records": records,
        "canonical_sha256": _canonical_sha256(records),
    }


def _module_identity(
    module: Any,
    *,
    distribution_name: str,
) -> dict[str, Any]:
    origin_value = getattr(module, "__file__", None)
    if not isinstance(origin_value, str) or not origin_value:
        raise ValueError(f"{distribution_name} has no import origin")
    origin = Path(origin_value).resolve(strict=True)
    return {
        "distribution_name": distribution_name,
        "distribution_version": importlib.metadata.version(distribution_name),
        "module_version": getattr(module, "__version__", None),
        "origin": str(origin),
        "origin_sha256": _sha256_file(origin),
    }


def _source_identity(value: Any) -> dict[str, Any]:
    source_value = inspect.getsourcefile(value)
    if not isinstance(source_value, str) or not source_value:
        raise ValueError("public API source origin is unavailable")
    source = Path(source_value).resolve(strict=True)
    return {"origin": str(source), "origin_sha256": _sha256_file(source)}


def _is_relative_to(path: Path, directory: Path) -> bool:
    try:
        path.relative_to(directory)
    except ValueError:
        return False
    return True


def _verify_environment_and_runtime(
    fork: Path,
    *,
    environment_yaml: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if platform.python_version() != EXPECTED_PYTHON_VERSION:
        raise RuntimeError(
            "SDIM worker requires Python "
            f"{EXPECTED_PYTHON_VERSION}, got {platform.python_version()}"
        )

    import quimb
    import quimb.experimental.gcapeps as gcapeps
    import sdim
    import stim
    from quimb.experimental.gcapeps import (
        QubitPauliWord,
        SdimCliffordFrame,
        StimCliffordFrame,
        sdim_backend_status,
    )

    del QubitPauliWord, SdimCliffordFrame, StimCliffordFrame

    if importlib.metadata.version("stim") != EXPECTED_STIM_VERSION:
        raise RuntimeError("Stim distribution version drifted")
    if getattr(stim, "__version__", None) != EXPECTED_STIM_VERSION:
        raise RuntimeError("Stim module version drifted")
    if importlib.metadata.version("sdim") != EXPECTED_SDIM_VERSION:
        raise RuntimeError("SDIM distribution version drifted")
    if not hasattr(sdim, "ExtendedTableau"):
        raise RuntimeError("SDIM ExtendedTableau is unavailable")
    if gcapeps.SDIM_SUPPORTED_VERSION != EXPECTED_SDIM_VERSION:
        raise RuntimeError("fork SDIM version pin drifted")
    if gcapeps.SDIM_INSPECTED_COMMIT != EXPECTED_SDIM_INSPECTED_COMMIT:
        raise RuntimeError("fork SDIM inspected commit drifted")

    status = sdim_backend_status()
    if (
        not status.available
        or status.name != "sdim"
        or status.version != EXPECTED_SDIM_VERSION
    ):
        raise RuntimeError(f"SDIM backend is unavailable: {status.detail}")

    expected_yaml = (
        fork / "environment-gcapeps-sdim.yml"
    ).resolve(strict=True)
    observed_yaml = environment_yaml.resolve(strict=True)
    if observed_yaml != expected_yaml:
        raise ValueError("environment YAML is not the frozen fork YAML")
    yaml_digest = _sha256_file(observed_yaml)
    if yaml_digest != EXPECTED_ENVIRONMENT_YAML_SHA256:
        raise ValueError("environment YAML hash drifted")

    quimb_identity = _module_identity(quimb, distribution_name="quimb")
    quimb_origin = Path(quimb_identity["origin"])
    if not _is_relative_to(quimb_origin, fork):
        raise RuntimeError("imported Quimb does not resolve inside the frozen fork")

    public_api_identity = _module_identity(
        gcapeps,
        distribution_name="quimb",
    )
    frame_identity = _source_identity(gcapeps.StimCliffordFrame)
    pauli_identity = _source_identity(gcapeps.QubitPauliWord)
    expected_sources = {
        "__init__.py": public_api_identity,
        "frame.py": frame_identity,
        "pauli.py": pauli_identity,
    }
    for filename, identity in expected_sources.items():
        origin = Path(identity["origin"])
        if not _is_relative_to(origin, fork):
            raise RuntimeError(f"{filename} does not resolve inside the fork")
        if identity["origin_sha256"] != EXPECTED_GCAPEPS_SOURCE_SHA256[filename]:
            raise RuntimeError(f"{filename} source hash drifted")

    python_executable = Path(sys.executable)
    resolved_python = python_executable.resolve(strict=True)
    runtime_identity = {
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
            "version_info": list(sys.version_info[:5]),
            "executable": str(python_executable),
            "resolved_executable": str(resolved_python),
            "resolved_executable_sha256": _sha256_file(resolved_python),
        },
        "stim": _module_identity(stim, distribution_name="stim"),
        "sdim": _module_identity(sdim, distribution_name="sdim"),
        "quimb": quimb_identity,
        "gcapeps_public_api": public_api_identity,
        "gcapeps_frame_source": frame_identity,
        "gcapeps_pauli_source": pauli_identity,
        "worker_source": _source_identity(_verify_environment_and_runtime),
        "sdim_backend_status": {
            "name": status.name,
            "available": status.available,
            "version": status.version,
            "detail": status.detail,
            "inspected_commit": EXPECTED_SDIM_INSPECTED_COMMIT,
        },
    }
    environment_identity = {
        "yaml_path": str(observed_yaml),
        "expected_yaml_sha256": EXPECTED_ENVIRONMENT_YAML_SHA256,
        "actual_yaml_sha256": yaml_digest,
        "yaml_identity_verified": True,
        "bootstrap_only": True,
        "transitive_lock_attested": False,
        "wheel_bytes_attested": False,
        "installed_distributions": _installed_distributions(),
    }
    return environment_identity, runtime_identity


def _frame_snapshot(tableau: Any, *, num_qubits: int) -> dict[str, Any]:
    body = {
        "x_outputs": [str(tableau.x_output(q)) for q in range(num_qubits)],
        "z_outputs": [str(tableau.z_output(q)) for q in range(num_qubits)],
    }
    return {**body, "canonical_sha256": _canonical_sha256(body)}


def _signed_word(text: str, QubitPauliWord: Any) -> Any:
    if (
        not isinstance(text, str)
        or len(text) != 9
        or text[0] not in "+-"
        or any(label not in "IXYZ" for label in text[1:])
    ):
        raise ValueError(f"invalid frozen signed Pauli word: {text!r}")
    phase = 1.0 + 0.0j if text[0] == "+" else -1.0 + 0.0j
    return QubitPauliWord.from_labels(text[1:], phase=phase)


def _execute_frame_differential(
    fixture: Mapping[str, Any],
    *,
    flip_first_sign_control: bool,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    import stim
    from quimb.experimental.gcapeps import (
        QubitPauliWord,
        SdimCliffordFrame,
        StimCliffordFrame,
    )

    stim_frame = StimCliffordFrame(8)
    sdim_frame = SdimCliffordFrame(8)
    if (
        stim_frame.backend_name != f"stim-{EXPECTED_STIM_VERSION}"
        or sdim_frame.backend_name
        != f"sdim-{EXPECTED_SDIM_VERSION}-qubit-bridge"
    ):
        raise RuntimeError("frame backend name drifted")

    initial_stim_tableau = stim_frame.as_stim_tableau()
    initial_sdim_tableau = sdim_frame.as_stim_tableau()
    initial_stim_snapshot = _frame_snapshot(
        initial_stim_tableau,
        num_qubits=8,
    )
    initial_sdim_snapshot = _frame_snapshot(
        initial_sdim_tableau,
        num_qubits=8,
    )
    initial = {
        "stim_revision": stim_frame.revision,
        "sdim_revision": sdim_frame.revision,
        "stim_tableau": initial_stim_snapshot,
        "sdim_tableau": initial_sdim_snapshot,
        "tableau_exact_match": bool(
            initial_stim_tableau == initial_sdim_tableau
            and initial_stim_snapshot == initial_sdim_snapshot
        ),
        "revision_exact_match": bool(
            stim_frame.revision == sdim_frame.revision == 0
        ),
    }

    clifford = fixture["clifford"]
    prefix_rows: list[dict[str, Any]] = []
    for index, row in enumerate(clifford["gates"]):
        token = row["token"]
        targets = tuple(row["logical_targets"])
        instruction = f"{token} {' '.join(str(q) for q in targets)}"
        operation = stim.Circuit(instruction)
        stim_before = stim_frame.revision
        sdim_before = sdim_frame.revision
        stim_frame.apply_clifford(operation)
        sdim_frame.apply_clifford(operation)
        stim_tableau = stim_frame.as_stim_tableau()
        sdim_tableau = sdim_frame.as_stim_tableau()
        stim_snapshot = _frame_snapshot(stim_tableau, num_qubits=8)
        sdim_snapshot = _frame_snapshot(sdim_tableau, num_qubits=8)
        expected_revision = index + 1
        prefix_rows.append(
            {
                "index": index,
                "token": token,
                "logical_targets": list(targets),
                "stim_instruction": instruction,
                "stim_revision_before": stim_before,
                "stim_revision_after": stim_frame.revision,
                "sdim_revision_before": sdim_before,
                "sdim_revision_after": sdim_frame.revision,
                "expected_revision_after": expected_revision,
                "stim_tableau": stim_snapshot,
                "sdim_tableau": sdim_snapshot,
                "tableau_exact_match": bool(
                    stim_tableau == sdim_tableau
                    and stim_snapshot == sdim_snapshot
                ),
                "revision_exact_match": bool(
                    stim_before == sdim_before == index
                    and stim_frame.revision
                    == sdim_frame.revision
                    == expected_revision
                ),
            }
        )

    term_rows: list[dict[str, Any]] = []
    for index, term in enumerate(fixture["physical_terms"]):
        input_word = QubitPauliWord.from_labels(
            term["pauli_body"],
            phase=complex(term["word_phase"]),
        )
        expected_word = _signed_word(
            term["expected_signed_pullback"],
            QubitPauliWord,
        )
        stim_pulled = stim_frame.pullback_pauli(input_word)
        sdim_backend_pulled = sdim_frame.pullback_pauli(input_word)
        flip_applied = bool(flip_first_sign_control and index == 0)
        sdim_compared = (
            sdim_backend_pulled.with_phase(-sdim_backend_pulled.phase)
            if flip_applied
            else sdim_backend_pulled
        )
        expected_equals_stim = expected_word == stim_pulled
        expected_equals_sdim = expected_word == sdim_compared
        stim_equals_sdim = stim_pulled == sdim_compared
        backend_match = stim_pulled == sdim_backend_pulled
        term_rows.append(
            {
                "term_index": index,
                "physical_body": term["pauli_body"],
                "input_word_phase": term["word_phase"],
                "input_signed_word": str(input_word),
                "expected_signed_pullback": str(expected_word),
                "stim_signed_pullback": str(stim_pulled),
                "sdim_backend_signed_pullback": str(sdim_backend_pulled),
                "sdim_compared_signed_pullback": str(sdim_compared),
                "flip_control_applied": flip_applied,
                "expected_equals_stim": expected_equals_stim,
                "expected_equals_sdim": expected_equals_sdim,
                "stim_equals_sdim": stim_equals_sdim,
                "backend_stim_equals_sdim": backend_match,
                "strict_match": bool(
                    expected_equals_stim
                    and expected_equals_sdim
                    and stim_equals_sdim
                ),
            }
        )
    return initial, prefix_rows, term_rows


def build_report(
    *,
    fixture_json: Path,
    fork_checkout: Path,
    expected_fork_commit: str,
    expected_fork_tree: str,
    environment_yaml: Path,
    flip_first_sign_control: bool = False,
) -> dict[str, Any]:
    """Build and self-validate one isolated signed-frame report."""

    fixture, fixture_identity = _load_canonical_fixture(fixture_json)
    fork, fork_identity = _verify_fork_identity(
        fork_checkout,
        expected_commit=expected_fork_commit,
        expected_tree=expected_fork_tree,
    )
    environment_identity, runtime_identity = _verify_environment_and_runtime(
        fork,
        environment_yaml=environment_yaml,
    )
    quimb_origin = Path(runtime_identity["quimb"]["origin"])
    if not _is_relative_to(quimb_origin, fork):
        raise RuntimeError("Quimb origin escaped the verified fork")
    fork_identity["quimb_origin_within_checkout"] = True

    initial, prefixes, terms = _execute_frame_differential(
        fixture,
        flip_first_sign_control=flip_first_sign_control,
    )
    prefix_pass = bool(
        initial["tableau_exact_match"]
        and initial["revision_exact_match"]
        and all(
            row["tableau_exact_match"] and row["revision_exact_match"]
            for row in prefixes
        )
    )
    term_pass = all(row["strict_match"] for row in terms)
    verdict = "PASS" if prefix_pass and term_pass else "FAIL"
    control_detected = bool(
        flip_first_sign_control
        and terms[0]["flip_control_applied"]
        and terms[0]["backend_stim_equals_sdim"]
        and not terms[0]["strict_match"]
        and verdict == "FAIL"
    )
    report: dict[str, Any] = {
        "schema": WORKER_SCHEMA,
        "worker_role": "signed_dimension_two_stim_sdim_frame_corroboration",
        "fixture_identity": fixture_identity,
        "fork_identity": fork_identity,
        "environment_identity": environment_identity,
        "runtime_identity": runtime_identity,
        "scope": {
            "dimension": 2,
            "qubit_only": True,
            "uses_stim_bridge": True,
            "receives_peps": False,
            "emits_peps": False,
            "receives_state_vector": False,
            "emits_state_vector": False,
            "enters_timing_or_rss_ratio": False,
            "qutrit_evidence": False,
            "ground_truth": False,
            "state_action_verdict_authority": False,
        },
        "initial_frame": initial,
        "prefix_ledger": prefixes,
        "term_pullbacks": terms,
        "control": {
            "name": "flip_first_sdim_pullback_sign",
            "enabled": flip_first_sign_control,
            "term_index": 0,
            "comparison_sign_flipped": flip_first_sign_control,
            "detected": control_detected,
        },
        "sdim_frame_verdict": verdict,
    }
    report["content_sha256"] = canonical_content_sha256(report)
    validate_report(report)
    return report


def _require_exact_keys(
    value: Any,
    expected: frozenset[str],
    *,
    label: str,
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    observed = frozenset(value)
    if observed != expected:
        missing = sorted(expected - observed)
        extra = sorted(observed - expected)
        raise ValueError(
            f"{label} keys drifted: missing={missing}, extra={extra}"
        )
    return value


def _validate_tableau_snapshot(value: Any, *, label: str) -> None:
    snapshot = _require_exact_keys(value, FRAME_SNAPSHOT_KEYS, label=label)
    if (
        not isinstance(snapshot["x_outputs"], list)
        or not isinstance(snapshot["z_outputs"], list)
        or len(snapshot["x_outputs"]) != 8
        or len(snapshot["z_outputs"]) != 8
        or not all(
            isinstance(item, str)
            for item in snapshot["x_outputs"] + snapshot["z_outputs"]
        )
    ):
        raise ValueError(f"{label} generator list drifted")
    body = {
        "x_outputs": snapshot["x_outputs"],
        "z_outputs": snapshot["z_outputs"],
    }
    if snapshot["canonical_sha256"] != _canonical_sha256(body):
        raise ValueError(f"{label} hash drifted")


def _flipped_signed_word_text(value: str) -> str:
    if not isinstance(value, str) or not value or value[0] not in "+-":
        raise ValueError("signed Pauli text must start with + or -")
    return ("-" if value[0] == "+" else "+") + value[1:]


def validate_report(report: Mapping[str, Any]) -> None:
    """Reject every unsupported key, identity drift, or verdict inconsistency."""

    root = _require_exact_keys(report, TOP_LEVEL_KEYS, label="report")
    if root["schema"] != WORKER_SCHEMA:
        raise ValueError("SDIM worker schema drifted")
    if (
        root["worker_role"]
        != "signed_dimension_two_stim_sdim_frame_corroboration"
    ):
        raise ValueError("SDIM worker role drifted")

    fixture = _require_exact_keys(
        root["fixture_identity"],
        FIXTURE_IDENTITY_KEYS,
        label="fixture_identity",
    )
    if (
        fixture["schema"] != FIXTURE_SCHEMA
        or fixture["file_sha256"] != EXPECTED_FIXTURE_SHA256
        or fixture["canonical_sha256"] != EXPECTED_FIXTURE_SHA256
        or fixture["file_is_canonical_json"] is not True
        or fixture["n_qubits"] != 8
        or fixture["active_rank"] != 3
        or fixture["clifford_gate_stream_sha256"]
        != EXPECTED_CLIFFORD_STREAM_SHA256
        or fixture["physical_term_count"] != 3
    ):
        raise ValueError("fixture identity fields drifted")

    fork = _require_exact_keys(
        root["fork_identity"],
        FORK_IDENTITY_KEYS,
        label="fork_identity",
    )
    if (
        fork["frozen_commit"] != EXPECTED_FORK_COMMIT
        or fork["expected_commit_from_cli"] != EXPECTED_FORK_COMMIT
        or fork["actual_commit"] != EXPECTED_FORK_COMMIT
        or fork["frozen_tree"] != EXPECTED_FORK_TREE
        or fork["expected_tree_from_cli"] != EXPECTED_FORK_TREE
        or fork["actual_tree"] != EXPECTED_FORK_TREE
        or fork["identity_verified"] is not True
        or fork["quimb_origin_within_checkout"] is not True
    ):
        raise ValueError("fork identity fields drifted")

    environment = _require_exact_keys(
        root["environment_identity"],
        ENVIRONMENT_IDENTITY_KEYS,
        label="environment_identity",
    )
    if (
        environment["expected_yaml_sha256"]
        != EXPECTED_ENVIRONMENT_YAML_SHA256
        or environment["actual_yaml_sha256"]
        != EXPECTED_ENVIRONMENT_YAML_SHA256
        or environment["yaml_identity_verified"] is not True
        or environment["bootstrap_only"] is not True
        or environment["transitive_lock_attested"] is not False
        or environment["wheel_bytes_attested"] is not False
    ):
        raise ValueError("environment identity fields drifted")
    distributions = _require_exact_keys(
        environment["installed_distributions"],
        INSTALLED_DISTRIBUTIONS_KEYS,
        label="installed_distributions",
    )
    records = distributions["records"]
    if (
        not isinstance(records, list)
        or distributions["record_count"] != len(records)
        or distributions["canonical_sha256"] != _canonical_sha256(records)
    ):
        raise ValueError("installed distribution ledger drifted")
    for index, record in enumerate(records):
        _require_exact_keys(
            record,
            DISTRIBUTION_RECORD_KEYS,
            label=f"installed_distributions.records[{index}]",
        )

    runtime = _require_exact_keys(
        root["runtime_identity"],
        RUNTIME_IDENTITY_KEYS,
        label="runtime_identity",
    )
    python = _require_exact_keys(
        runtime["python"],
        PYTHON_IDENTITY_KEYS,
        label="runtime_identity.python",
    )
    if python["version"] != EXPECTED_PYTHON_VERSION:
        raise ValueError("runtime Python version drifted")
    for name in ("stim", "sdim", "quimb", "gcapeps_public_api"):
        identity = _require_exact_keys(
            runtime[name],
            MODULE_IDENTITY_KEYS,
            label=f"runtime_identity.{name}",
        )
        if not isinstance(identity["origin_sha256"], str):
            raise ValueError(f"runtime identity {name} hash drifted")
    if (
        runtime["stim"]["distribution_version"] != EXPECTED_STIM_VERSION
        or runtime["stim"]["module_version"] != EXPECTED_STIM_VERSION
        or runtime["sdim"]["distribution_version"] != EXPECTED_SDIM_VERSION
    ):
        raise ValueError("Stim or SDIM runtime version drifted")
    for name, filename in (
        ("gcapeps_public_api", "__init__.py"),
        ("gcapeps_frame_source", "frame.py"),
        ("gcapeps_pauli_source", "pauli.py"),
    ):
        expected_keys = (
            MODULE_IDENTITY_KEYS
            if name == "gcapeps_public_api"
            else SOURCE_IDENTITY_KEYS
        )
        identity = _require_exact_keys(
            runtime[name],
            expected_keys,
            label=f"runtime_identity.{name}",
        )
        if identity["origin_sha256"] != EXPECTED_GCAPEPS_SOURCE_SHA256[filename]:
            raise ValueError(f"{name} source identity drifted")
    _require_exact_keys(
        runtime["worker_source"],
        SOURCE_IDENTITY_KEYS,
        label="runtime_identity.worker_source",
    )
    status = _require_exact_keys(
        runtime["sdim_backend_status"],
        SDIM_STATUS_KEYS,
        label="runtime_identity.sdim_backend_status",
    )
    if (
        status["name"] != "sdim"
        or status["available"] is not True
        or status["version"] != EXPECTED_SDIM_VERSION
        or status["inspected_commit"] != EXPECTED_SDIM_INSPECTED_COMMIT
    ):
        raise ValueError("SDIM backend status drifted")

    scope = _require_exact_keys(root["scope"], SCOPE_KEYS, label="scope")
    expected_scope = {
        "dimension": 2,
        "qubit_only": True,
        "uses_stim_bridge": True,
        "receives_peps": False,
        "emits_peps": False,
        "receives_state_vector": False,
        "emits_state_vector": False,
        "enters_timing_or_rss_ratio": False,
        "qutrit_evidence": False,
        "ground_truth": False,
        "state_action_verdict_authority": False,
    }
    if dict(scope) != expected_scope:
        raise ValueError("SDIM worker scope drifted")

    initial = _require_exact_keys(
        root["initial_frame"],
        INITIAL_FRAME_KEYS,
        label="initial_frame",
    )
    _validate_tableau_snapshot(
        initial["stim_tableau"],
        label="initial_frame.stim_tableau",
    )
    _validate_tableau_snapshot(
        initial["sdim_tableau"],
        label="initial_frame.sdim_tableau",
    )
    initial_tableau_match = (
        initial["stim_tableau"] == initial["sdim_tableau"]
    )
    if (
        initial["stim_revision"] != 0
        or initial["sdim_revision"] != 0
        or initial["tableau_exact_match"] is not initial_tableau_match
        or initial_tableau_match is not True
        or initial["revision_exact_match"] is not True
    ):
        raise ValueError("initial frame differential drifted")

    prefixes = root["prefix_ledger"]
    if not isinstance(prefixes, list) or len(prefixes) != 10:
        raise ValueError("prefix ledger count drifted")
    for index, (row, expected_gate) in enumerate(
        zip(prefixes, EXPECTED_CLIFFORD_GATES, strict=True)
    ):
        prefix = _require_exact_keys(
            row,
            PREFIX_ROW_KEYS,
            label=f"prefix_ledger[{index}]",
        )
        token, targets = expected_gate
        if (
            prefix["index"] != index
            or prefix["token"] != token
            or prefix["logical_targets"] != list(targets)
            or prefix["stim_instruction"]
            != f"{token} {' '.join(str(q) for q in targets)}"
            or prefix["stim_revision_before"] != index
            or prefix["sdim_revision_before"] != index
            or prefix["stim_revision_after"] != index + 1
            or prefix["sdim_revision_after"] != index + 1
            or prefix["expected_revision_after"] != index + 1
        ):
            raise ValueError(f"prefix ledger row {index} drifted")
        _validate_tableau_snapshot(
            prefix["stim_tableau"],
            label=f"prefix_ledger[{index}].stim_tableau",
        )
        _validate_tableau_snapshot(
            prefix["sdim_tableau"],
            label=f"prefix_ledger[{index}].sdim_tableau",
        )
        tableau_match = prefix["stim_tableau"] == prefix["sdim_tableau"]
        if (
            prefix["tableau_exact_match"] is not tableau_match
            or prefix["revision_exact_match"] is not True
        ):
            raise ValueError(f"prefix ledger row {index} verdict drifted")

    terms = root["term_pullbacks"]
    if not isinstance(terms, list) or len(terms) != 3:
        raise ValueError("term pullback count drifted")
    for index, (term, expected) in enumerate(
        zip(terms, EXPECTED_PHYSICAL_TERMS, strict=True)
    ):
        row = _require_exact_keys(
            term,
            TERM_ROW_KEYS,
            label=f"term_pullbacks[{index}]",
        )
        expected_index, body, phase, pullback = expected
        if (
            row["term_index"] != expected_index
            or row["physical_body"] != body
            or row["input_word_phase"] != phase
            or row["expected_signed_pullback"] != pullback
        ):
            raise ValueError(f"term pullback row {index} drifted")

    control = _require_exact_keys(
        root["control"],
        CONTROL_KEYS,
        label="control",
    )
    enabled = control["enabled"]
    if not isinstance(enabled, bool):
        raise ValueError("control enabled flag must be boolean")
    if (
        control["name"] != "flip_first_sdim_pullback_sign"
        or control["term_index"] != 0
        or control["comparison_sign_flipped"] is not enabled
        or terms[0]["flip_control_applied"] is not enabled
        or any(row["flip_control_applied"] for row in terms[1:])
    ):
        raise ValueError("sign-flip control ledger drifted")

    for index, (row, expected) in enumerate(
        zip(terms, EXPECTED_PHYSICAL_TERMS, strict=True)
    ):
        _, body, phase, pullback = expected
        input_signed = ("+" if phase == 1 else "-") + body
        flip_applied = bool(enabled and index == 0)
        compared_sdim = (
            _flipped_signed_word_text(pullback)
            if flip_applied
            else pullback
        )
        expected_equals_sdim = not flip_applied
        if (
            row["input_signed_word"] != input_signed
            or row["stim_signed_pullback"] != pullback
            or row["sdim_backend_signed_pullback"] != pullback
            or row["sdim_compared_signed_pullback"] != compared_sdim
            or row["expected_equals_stim"] is not True
            or row["expected_equals_sdim"] is not expected_equals_sdim
            or row["stim_equals_sdim"] is not expected_equals_sdim
            or row["backend_stim_equals_sdim"] is not True
            or row["strict_match"] is not expected_equals_sdim
        ):
            raise ValueError(f"term pullback row {index} comparison drifted")

    prefix_pass = all(
        row["tableau_exact_match"] is True
        and row["revision_exact_match"] is True
        for row in prefixes
    )
    term_pass = all(row["strict_match"] is True for row in terms)
    expected_verdict = (
        "PASS"
        if initial["tableau_exact_match"]
        and initial["revision_exact_match"]
        and prefix_pass
        and term_pass
        else "FAIL"
    )
    if root["sdim_frame_verdict"] != expected_verdict:
        raise ValueError("SDIM frame verdict is inconsistent")
    expected_control_detected = bool(
        enabled
        and terms[0]["backend_stim_equals_sdim"] is True
        and terms[0]["strict_match"] is False
        and expected_verdict == "FAIL"
    )
    if control["detected"] is not expected_control_detected:
        raise ValueError("sign-flip control detection drifted")
    if enabled and expected_verdict != "FAIL":
        raise ValueError("sign-flip corruption did not fail the differential")
    if not enabled and expected_verdict != "PASS":
        raise ValueError("uncorrupted SDIM frame differential did not pass")

    content_hash = root["content_sha256"]
    if (
        not isinstance(content_hash, str)
        or not re.fullmatch(r"[0-9a-f]{64}", content_hash)
        or content_hash != canonical_content_sha256(root)
    ):
        raise ValueError("SDIM worker canonical content hash drifted")


def write_private_report_no_replace(
    output_json: Path,
    report: Mapping[str, Any],
) -> Path:
    """Create one supervisor-private canonical JSON file without replacement."""

    validate_report(report)
    encoded = _canonical_json_bytes(report)
    parent = output_json.parent.resolve(strict=True)
    if not parent.is_dir():
        raise ValueError("output parent must be an existing directory")
    name = output_json.name
    if name in ("", ".", "..") or "/" in name or os.sep in name:
        raise ValueError("output JSON must name one file in its parent")

    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
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
                raise OSError("short write while sealing SDIM worker report")
            position += written
        os.fsync(output_fd)
        metadata = os.fstat(output_fd)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise RuntimeError("private SDIM report is not one regular file")
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
            raise RuntimeError("private SDIM report changed after write")
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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--fork-checkout", type=Path, required=True)
    parser.add_argument("--expected-fork-commit", required=True)
    parser.add_argument("--expected-fork-tree", required=True)
    parser.add_argument("--environment-yaml", type=Path, required=True)
    parser.add_argument("--flip-first-sign-control", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    fixture_path = args.fixture_json.resolve(strict=True)
    output_parent = args.output_json.parent.resolve(strict=True)
    output_path = output_parent / args.output_json.name
    if output_path == fixture_path:
        raise ValueError("output JSON must be distinct from the fixture")
    report = build_report(
        fixture_json=fixture_path,
        fork_checkout=args.fork_checkout,
        expected_fork_commit=args.expected_fork_commit,
        expected_fork_tree=args.expected_fork_tree,
        environment_yaml=args.environment_yaml,
        flip_first_sign_control=args.flip_first_sign_control,
    )
    published = write_private_report_no_replace(output_path, report)
    print(
        json.dumps(
            {
                "content_sha256": report["content_sha256"],
                "output_json": str(published),
                "sdim_frame_verdict": report["sdim_frame_verdict"],
            },
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
