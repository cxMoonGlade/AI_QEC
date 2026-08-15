"""Fail-closed assembly and publication for static target-lowering objects.

Only deterministic static programs and qualification evidence live here.  The
module has no target recurrence, ADD root, TN contraction, metric execution,
Record probability, or route-selection entry point.
"""

from __future__ import annotations

import argparse
import ctypes
import errno
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import secrets
import shutil
import stat
import subprocess
import sys
from copy import deepcopy
from functools import lru_cache
from itertools import product
from pathlib import Path
from typing import Any, Mapping

from .add_relations import (
    build_dynamic_add_relation_program,
    validate_dynamic_add_relation_program,
)
from .independent_pair_oracle import reconstruct_pair_receipt_rows
from .independent_source_oracle import (
    reconstruct_site_map,
    reconstruct_source_facts,
    reconstruct_source_program,
)
from .independent_target_oracle import (
    PersistentSignLoweringAuditError,
    audit_persistent_sign_lowering,
    reconstruct_add_relation_events,
)
from .independent_tn_oracle import (
    reconstruct_network_incidence,
    reconstruct_table_catalog,
)
from .model import canonical_json_bytes, reject_floats, sha256_json
from .model import ADD_SCHEMA, NEUTRAL_SCHEMA, PAIR_SCHEMA, STATIC_SCOPE, TN_SCHEMA
from .neutral import (
    lower_frozen_declared_error_record,
    validate_declared_error_record_program,
)
from .pair import (
    build_exact_pair_transition_program,
    validate_exact_pair_transition_program,
)
from .tn import (
    build_retained_boundary_factor_network,
    validate_retained_boundary_factor_network,
)


REPO = Path(__file__).resolve().parents[3]
GRID = tuple(
    (distance, rounds)
    for distance in (3, 5)
    for rounds in (1, 3, 5, 7)
)
PROGRAM_NAMES = ("neutral", "pair", "add_relations", "tn")
REPORT_SCHEMA = (
    "error_coupling_simulator.external."
    "no_cutoff_target_lowering_qualification.v1"
)
PUBLICATION_RECEIPT_SCHEMA = (
    "error_coupling_simulator.external."
    "no_cutoff_target_lowering_publication_receipt.v1"
)
REPORT_STATUS = "VALID_STATIC_TARGET_LOWERING_QUALIFICATION_CODE_BLOCKED"
ACTIVE_PREREG_SHA256 = (
    "48e4f6b5e2f1024cdf569fc367bca3a2101c3bcfc61c0c6f2b672ebd88679d69"
)
REVIEWED_PREACTIVATION_SHA256 = (
    "4aed3c844447aa0a8bdaba31e0ae41071c4ca03ebe4c9a90fd24f6fc4c53af63"
)
REVIEW_RECEIPT_SHA256 = (
    "ff62206dd026958efa4b8c79092f8aafb7cf1bf227c2ec681c68de161f2f4a82"
)
LITERATURE_CLOSURE_SHA256 = (
    "366e8d3088e287d0d8ad9042f9e0d893f7ecbae5a4266615d28eb31e92f0e0c6"
)
FIXTURE_MANIFEST_SHA256 = (
    "40474ca0beab8341d53bfa41da5438e052744bb83ae6af2632e1bfe273c53c74"
)
FIXTURE_MANIFEST_SCHEMA = (
    "error_coupling_simulator.external.no_cutoff_structure_fixture_identity.v1"
)
PREREG_RELATIVE = (
    "docs/simulator_validation/NO_CUTOFF_TARGET_LOWERING_PREREG_2026-08-03.md"
)
REVIEW_RELATIVE = (
    "docs/simulator_validation/NO_CUTOFF_TARGET_LOWERING_PREREG_REVIEW_2026-08-03.md"
)
LITERATURE_CLOSURE_RELATIVE = (
    "docs/simulator_validation/"
    "NO_CUTOFF_TARGET_LOWERING_LITERATURE_CLOSURE_2026-08-03.md"
)
FIXTURE_MANIFEST_RELATIVE = (
    "docs/simulator_validation/"
    "NO_CUTOFF_STRUCTURE_CENSUS_FIXTURE_MANIFEST_2026-08-03.json"
)
SOURCE_FILES = (
    "scripts/external_baselines/no_cutoff_target_lowering/__init__.py",
    "scripts/external_baselines/no_cutoff_target_lowering/model.py",
    "scripts/external_baselines/no_cutoff_target_lowering/neutral.py",
    "scripts/external_baselines/no_cutoff_target_lowering/pair.py",
    "scripts/external_baselines/no_cutoff_target_lowering/add_relations.py",
    "scripts/external_baselines/no_cutoff_target_lowering/tn.py",
    (
        "scripts/external_baselines/no_cutoff_target_lowering/"
        "independent_source_oracle.py"
    ),
    (
        "scripts/external_baselines/no_cutoff_target_lowering/"
        "independent_pair_oracle.py"
    ),
    (
        "scripts/external_baselines/no_cutoff_target_lowering/"
        "independent_target_oracle.py"
    ),
    (
        "scripts/external_baselines/no_cutoff_target_lowering/"
        "independent_tn_oracle.py"
    ),
    "scripts/external_baselines/no_cutoff_target_lowering/report.py",
)
TEST_FILES = (
    "tests/test_external_no_cutoff_target_neutral.py",
    "tests/test_external_no_cutoff_target_pair_program.py",
    "tests/test_external_no_cutoff_target_add_relations.py",
    "tests/test_external_no_cutoff_target_tn_network.py",
    "tests/test_external_no_cutoff_target_independent_oracles.py",
    "tests/test_external_no_cutoff_target_lowering_report.py",
)
PRODUCTION_OUTPUT_RELATIVE = (
    "outputs/external_baselines/no_cutoff_target_lowering_20260803"
)
CORRUPTION_CONTROL_IDS = (
    "source_target_changed",
    "site_map_ordinal_changed",
    "dense_range_qubits",
    "cx_pair_swapped",
    "coherent_target_swapped",
    "rec_resolved_against_final",
    "record_raw_exposed",
    "record_latent_exposed",
    "iid_sign_resampling",
    "float_coefficient",
    "structural_zero_pruned",
    "coherent_right_sign_flipped",
    "reset_k1_omitted",
    "measurement_postselected",
    "left_right_exchanged",
    "rref_phase_dropped",
    "rref_rightmost_pivot",
    "codec_latent_omitted",
    "codec_accumulator_omitted",
    "codec_live_raw_omitted",
    "raw_dropped_early",
    "add_coefficient_changed",
    "add_current_root_field",
    "tn_density_transposed",
    "tn_table_sparsified",
    "tn_measurement_dephased",
    "tn_reset_trace_omitted",
    "tn_copy_removed",
    "tn_keep_removed",
    "tn_iid_signs",
    "tn_sign_codec_swapped",
    "numeric_metric_injected",
    "historical_artifact_changed",
)

STRUCTURE_REPORT_RELATIVE = (
    "outputs/external_baselines/no_cutoff_structure_census_20260803/report_v3.json"
)
MINIMAL_REPORT_RELATIVE = (
    "outputs/external_baselines/no_cutoff_minimal_exact_owners_20260803/report.json"
)
MINIMAL_RECEIPT_RELATIVE = (
    "outputs/external_baselines/no_cutoff_minimal_exact_owners_20260803/"
    "publication_receipt.json"
)
STRUCTURE_REPORT_SHA256 = (
    "88e6175dc3b7d1474c155f06cf1857484a96a8d3f6754a5e91b4c66a5292918b"
)
MINIMAL_REPORT_SHA256 = (
    "fb645bb886c4b35c8efd2977956c50df9afca88c9c9be58716307d9dc6baf777"
)
MINIMAL_RECEIPT_SHA256 = (
    "ce6a332e16f2839d50839ee86ad54a269d3bc192ee65ba0795e7a83ecaae29b8"
)
MINIMAL_REPORT_CONTENT_SHA256 = (
    "5fd753b7e5de415a3063dd65a0322f22f3baef42ce09a054ab5c400f822ab395"
)
_CENSUS_SOURCE_ANCHORS = {
    "scripts/external_baselines/no_cutoff_structure_census.py": (
        "382cf0145b92cdda021f5534657ddc357dd439733e79bfd41a848e829b0a6bf9"
    ),
    "scripts/external_baselines/no_cutoff_structure_census_exact_oracle.py": (
        "0cbb222a716f9e4717b6661a2fb1a2f70559d99c6b83a244776d499df50a735f"
    ),
}


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _open_directory_no_symlinks(path: Path) -> int:
    """Open an absolute directory by walking every component with NOFOLLOW."""

    absolute = Path(os.path.abspath(path))
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open("/", flags)
    try:
        for component in absolute.parts[1:]:
            try:
                child = os.open(component, flags, dir_fd=descriptor)
            except OSError as exc:
                if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
                    raise ValueError(
                        f"directory path contains a symlink or non-directory: {path}"
                    ) from exc
                raise
            os.close(descriptor)
            descriptor = child
        metadata = os.fstat(descriptor)
        if not stat.S_ISDIR(metadata.st_mode):
            raise ValueError(f"path is not a directory: {path}")
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def _read_regular_file_no_symlinks(path: Path) -> bytes:
    """Read one regular file from held parent/file descriptors exactly once."""

    parent = _open_directory_no_symlinks(path.parent)
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        try:
            descriptor = os.open(path.name, flags, dir_fd=parent)
        except OSError as exc:
            if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
                raise ValueError(f"file path is a symlink: {path}") from exc
            raise
        try:
            before = os.fstat(descriptor)
            if not stat.S_ISREG(before.st_mode):
                raise ValueError(f"path is not a regular file: {path}")
            chunks: list[bytes] = []
            while True:
                block = os.read(descriptor, 1024 * 1024)
                if not block:
                    break
                chunks.append(block)
            after = os.fstat(descriptor)
            if (
                before.st_dev,
                before.st_ino,
                before.st_size,
                before.st_mtime_ns,
            ) != (
                after.st_dev,
                after.st_ino,
                after.st_size,
                after.st_mtime_ns,
            ):
                raise ValueError(f"file changed while being read: {path}")
            return b"".join(chunks)
        finally:
            os.close(descriptor)
    finally:
        os.close(parent)


def _secure_file_sha256(path: Path) -> str:
    return _sha256_bytes(_read_regular_file_no_symlinks(path))


_IMPORTED_SOURCE_MANIFEST = {
    relative: _secure_file_sha256(REPO / relative) for relative in SOURCE_FILES
}


def _assert_qualification_sources_unchanged_since_import() -> str:
    """Reject same-process authority drift before any cache can be reused."""

    current = {
        relative: _secure_file_sha256(REPO / relative) for relative in SOURCE_FILES
    }
    if current != _IMPORTED_SOURCE_MANIFEST:
        changed = sorted(
            relative
            for relative in SOURCE_FILES
            if current[relative] != _IMPORTED_SOURCE_MANIFEST[relative]
        )
        raise ValueError(
            "qualification source changed after module import: " + ", ".join(changed)
        )
    return sha256_json(current)


def _strict_json_bytes(raw: bytes, *, subject: str) -> dict[str, Any]:
    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in rows:
            if key in result:
                raise ValueError(f"{subject} contains duplicate JSON key {key!r}")
            result[key] = value
        return result

    def reject_float(token: str) -> None:
        raise ValueError(f"{subject} contains forbidden floating token {token}")

    try:
        value = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=pairs,
            parse_float=reject_float,
            parse_constant=reject_float,
        )
    except UnicodeDecodeError as exc:
        raise ValueError(f"{subject} is not strict UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{subject} is not strict JSON") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{subject} must be a JSON object")
    return value


def _program_path(distance: int, rounds: int, name: str) -> str:
    return f"programs/d{distance}_r{rounds}/{name}.json"


@lru_cache(maxsize=1)
def _cached_program_artifacts() -> tuple[tuple[str, bytes], ...]:
    programs: list[tuple[str, bytes]] = []
    for distance, rounds in GRID:
        neutral = lower_frozen_declared_error_record(
            distance=distance, rounds=rounds
        )
        pair = build_exact_pair_transition_program(neutral)
        add = build_dynamic_add_relation_program(pair, neutral=neutral)
        tn = build_retained_boundary_factor_network(neutral)
        for name, artifact in (
            ("neutral", neutral),
            ("pair", pair),
            ("add_relations", add),
            ("tn", tn),
        ):
            programs.append(
                (
                    _program_path(distance, rounds, name),
                    canonical_json_bytes(artifact.to_data()),
                )
            )
    return tuple(programs)


def build_program_artifacts() -> dict[str, bytes]:
    """Build the fixed 32 canonical program files entirely in memory."""

    source_identity = _assert_qualification_sources_unchanged_since_import()
    result = dict(_cached_program_artifacts())
    if _assert_qualification_sources_unchanged_since_import() != source_identity:
        raise ValueError("qualification source changed while building programs")
    return result


_VALIDATED_PROGRAM_MANIFESTS: set[str] = set()


def validate_program_artifacts(programs: Mapping[str, bytes]) -> None:
    """Strictly parse and deterministically reproduce all 32 program bytes."""

    source_identity = _assert_qualification_sources_unchanged_since_import()
    expected_paths = {
        _program_path(distance, rounds, name)
        for distance, rounds in GRID
        for name in PROGRAM_NAMES
    }
    if set(programs) != expected_paths:
        raise ValueError("program artifact manifest is not the fixed 32-file layout")
    manifest_identity = sha256_json(
        {
            "qualification_source_identity": source_identity,
            "programs": {
            path: _sha256_bytes(raw) if type(raw) is bytes else "NOT_BYTES"
            for path, raw in programs.items()
            },
        }
    )
    if manifest_identity in _VALIDATED_PROGRAM_MANIFESTS:
        return
    for distance, rounds in GRID:
        parsed: dict[str, dict[str, Any]] = {}
        for name in PROGRAM_NAMES:
            path = _program_path(distance, rounds, name)
            raw = programs[path]
            if type(raw) is not bytes:
                raise TypeError(f"program artifact {path} must be bytes")
            value = _strict_json_bytes(raw, subject=path)
            if raw != canonical_json_bytes(value):
                raise ValueError(f"program artifact {path} is not canonical JSON")
            parsed[name] = value

        neutral = validate_declared_error_record_program(parsed["neutral"])
        pair = validate_exact_pair_transition_program(
            parsed["pair"], neutral=neutral
        )
        validate_dynamic_add_relation_program(
            parsed["add_relations"], pair=pair, neutral=neutral
        )
        validate_retained_boundary_factor_network(
            parsed["tn"], neutral=neutral
        )
    if _assert_qualification_sources_unchanged_since_import() != source_identity:
        raise ValueError("qualification source changed while validating programs")
    _VALIDATED_PROGRAM_MANIFESTS.add(manifest_identity)


def _assertion(
    assertion_id: str,
    *,
    subject: str,
    expected_rows: list[Any],
    observed_rows: list[Any],
) -> dict[str, Any]:
    expected_preimage = {
        "assertion_id": assertion_id,
        "subject": subject,
        "rows": expected_rows,
    }
    observed_preimage = {
        "assertion_id": assertion_id,
        "subject": subject,
        "rows": observed_rows,
    }
    expected_sha256 = sha256_json(expected_preimage)
    observed_sha256 = sha256_json(observed_preimage)
    status = (
        "PASS"
        if len(expected_rows) == len(observed_rows)
        and expected_sha256 == observed_sha256
        else "FAILED"
    )
    return {
        "assertion_id": assertion_id,
        "status": status,
        "row_count": len(expected_rows),
        "expected_sha256": expected_sha256,
        "observed_sha256": observed_sha256,
    }


def _oracle_receipt(
    *,
    oracle_id: str,
    subject: str,
    subject_sha256: str,
    oracle_source: str,
    assertions: list[dict[str, Any]],
) -> dict[str, Any]:
    if any(assertion["status"] != "PASS" for assertion in assertions):
        failed = [
            assertion["assertion_id"]
            for assertion in assertions
            if assertion["status"] != "PASS"
        ]
        raise ValueError(f"independent oracle mismatch for {oracle_id}: {failed}")
    body = {
        "oracle_id": oracle_id,
        "subject": subject,
        "subject_sha256": subject_sha256,
        "oracle_source_sha256": _secure_file_sha256(REPO / oracle_source),
        "assertions": assertions,
    }
    return {**body, "receipt_sha256": sha256_json(body)}


def _record_schema_from_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    raw_count = sum(event["raw_output"] is not None for event in events)
    detector_count = sum(event["kind"] == "DETECTOR_APPEND" for event in events)
    outputs = [
        {
            **event["record_output"],
            "producer_event_id": event["event_id"],
        }
        for event in events
        if event["record_output"] is not None
    ]
    return {
        "raw_measurement_count": raw_count,
        "detector_count": detector_count,
        "observable_indices": [0],
        "outputs": outputs,
        "record_width": detector_count + 1,
    }


def _source_receipt(
    *,
    distance: int,
    rounds: int,
    neutral_data: dict[str, Any],
    raw: bytes,
) -> dict[str, Any]:
    semantic = neutral_data["semantic"]
    source_text = semantic["source"]["source_text"]
    independent = reconstruct_source_program(source_text)
    owner_events = semantic["events"]
    observed_events = independent["events"]
    owner_rec = [
        {"event_id": event["event_id"], "rec_operands": event["rec_operands"]}
        for event in owner_events
        if event["rec_operands"]
    ]
    observed_rec = [
        {"event_id": event["event_id"], "rec_operands": event["rec_operands"]}
        for event in observed_events
        if event["rec_operands"]
    ]
    owner_counts = {
        "coherent_occurrences": sum(
            event["kind"] == "COHERENT_Z" for event in owner_events
        ),
        "declared_qubits": [row["stim_id"] for row in semantic["qubits"]],
        "detectors": semantic["record_schema"]["detector_count"],
        "program_events": len(owner_events),
        "raw_measurements": semantic["record_schema"]["raw_measurement_count"],
        "record_width": semantic["record_schema"]["record_width"],
        "resolved_record_operands": [
            [operand["absolute_raw_ordinal"] for operand in event["rec_operands"]]
            for event in owner_events
            if event["kind"] in {"DETECTOR_APPEND", "OBSERVABLE_XOR"}
        ],
    }
    subject = f"d{distance}_r{rounds}/neutral"
    assertions = [
        _assertion(
            "source_text_sha256",
            subject=subject,
            expected_rows=[
                {"sha256": semantic["fixture"]["cell_identity"]["source_circuit_sha256"]}
            ],
            observed_rows=[{"sha256": _sha256_bytes(source_text.encode("utf-8"))}],
        ),
        _assertion(
            "site_map_sha256",
            subject=subject,
            expected_rows=semantic["site_map"],
            observed_rows=reconstruct_site_map(source_text),
        ),
        _assertion(
            "declared_qubits",
            subject=subject,
            expected_rows=semantic["qubits"],
            observed_rows=independent["qubits"],
        ),
        _assertion(
            "event_stream",
            subject=subject,
            expected_rows=owner_events,
            observed_rows=observed_events,
        ),
        _assertion(
            "rec_resolution",
            subject=subject,
            expected_rows=owner_rec,
            observed_rows=observed_rec,
        ),
        _assertion(
            "record_schema",
            subject=subject,
            expected_rows=[semantic["record_schema"]],
            observed_rows=[_record_schema_from_events(observed_events)],
        ),
        _assertion(
            "structural_counts",
            subject=subject,
            expected_rows=[owner_counts],
            observed_rows=[reconstruct_source_facts(source_text)],
        ),
    ]
    return _oracle_receipt(
        oracle_id=f"source:d{distance}:r{rounds}",
        subject=subject,
        subject_sha256=_sha256_bytes(raw),
        oracle_source=(
            "scripts/external_baselines/no_cutoff_target_lowering/"
            "independent_source_oracle.py"
        ),
        assertions=assertions,
    )


def _owner_basis_history(pair_semantic: dict[str, Any]) -> list[dict[str, Any]]:
    catalog = {
        row["basis_id"]: {
            "pivots": row["pivots"],
            "rref_rows": row["rref_rows"],
            "stabilizers": row["stabilizers"],
        }
        for row in pair_semantic["basis_catalog"]
    }
    return [catalog[row["basis_id"]] for row in pair_semantic["checkpoints"]]


def _owner_checkpoint_codecs(pair_semantic: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "checkpoint": checkpoint["ordinal"],
            "fields": checkpoint["codec_fields"],
            "validity_sha256": sha256_json(checkpoint["validity"]),
        }
        for checkpoint in pair_semantic["checkpoints"]
    ]


def _pair_and_rref_receipts(
    *,
    distance: int,
    rounds: int,
    neutral_data: dict[str, Any],
    pair_data: dict[str, Any],
    pair_raw: bytes,
) -> tuple[dict[str, Any], dict[str, Any]]:
    from .independent_target_oracle import audit_target_rref_receipt_rows

    neutral_semantic = neutral_data["semantic"]
    pair_semantic = pair_data["semantic"]
    events = neutral_semantic["events"]
    qubit_count = len(neutral_semantic["qubits"])
    owner_bases = _owner_basis_history(pair_semantic)
    independent = reconstruct_pair_receipt_rows(
        neutral_semantic["source"]["source_text"]
    )
    owner_kernel_rows = [
        {"event_id": kernel["event_id"], "rows": kernel["component_rows"]}
        for kernel in pair_semantic["kernels"]
    ]
    subject = f"d{distance}_r{rounds}/pair"
    pair_assertions = [
        _assertion(
            "initial_terms",
            subject=subject,
            expected_rows=independent["initial_terms"],
            observed_rows=pair_semantic["initial_terms"],
        ),
        _assertion(
            "basis_catalog",
            subject=subject,
            expected_rows=independent["basis_catalog"],
            observed_rows=owner_bases,
        ),
        _assertion(
            "checkpoint_codecs",
            subject=subject,
            expected_rows=independent["checkpoint_codecs"],
            observed_rows=_owner_checkpoint_codecs(pair_semantic),
        ),
        _assertion(
            "kernel_normal_forms",
            subject=subject,
            expected_rows=independent["kernel_normal_forms"],
            observed_rows=owner_kernel_rows,
        ),
    ]
    pair_receipt = _oracle_receipt(
        oracle_id=f"pair:d{distance}:r{rounds}",
        subject=subject,
        subject_sha256=_sha256_bytes(pair_raw),
        oracle_source=(
            "scripts/external_baselines/no_cutoff_target_lowering/"
            "independent_pair_oracle.py"
        ),
        assertions=pair_assertions,
    )

    rref_subject = f"d{distance}_r{rounds}/signed-rref"
    rref_rows = audit_target_rref_receipt_rows(
        events, qubit_count, owner_bases
    )
    rref_assertions = [
        _assertion(
            assertion_id,
            subject=rref_subject,
            expected_rows=rref_rows[assertion_id]["expected_rows"],
            observed_rows=rref_rows[assertion_id]["observed_rows"],
        )
        for assertion_id in (
            "rank",
            "commutation",
            "leftmost_pivots",
            "signed_phases",
            "idempotence",
        )
    ]
    rref_receipt = _oracle_receipt(
        oracle_id=f"rref:d{distance}:r{rounds}",
        subject=rref_subject,
        subject_sha256=_sha256_bytes(pair_raw),
        oracle_source=(
            "scripts/external_baselines/no_cutoff_target_lowering/"
            "independent_target_oracle.py"
        ),
        assertions=rref_assertions,
    )
    return pair_receipt, rref_receipt


def _add_receipt(
    *,
    distance: int,
    rounds: int,
    neutral_data: dict[str, Any],
    add_data: dict[str, Any],
    raw: bytes,
) -> dict[str, Any]:
    owner = add_data["semantic"]["events"]
    independent = reconstruct_add_relation_events(
        neutral_data["semantic"]["source"]["source_text"]
    )
    subject = f"d{distance}_r{rounds}/add-relations"

    def select(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> list[dict[str, Any]]:
        return [
            {"event_id": row["event_id"], **{field: row[field] for field in fields}}
            for row in rows
        ]

    forbidden = {
        "current_root",
        "root",
        "node_table",
        "frontier",
        "support",
        "pair_state",
    }

    def forbidden_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for row in rows:
            found: set[str] = set()
            stack: list[object] = [row]
            while stack:
                value = stack.pop()
                if isinstance(value, dict):
                    found.update(forbidden & set(value))
                    stack.extend(value.values())
                elif isinstance(value, list):
                    stack.extend(value)
            result.append({"event_id": row["event_id"], "forbidden_fields": sorted(found)})
        return result

    assertions = [
        _assertion(
            "all_event_normal_forms",
            subject=subject,
            expected_rows=select(
                independent, ("pair_semantic_sha256", "relation_order")
            ),
            observed_rows=select(
                owner, ("pair_semantic_sha256", "relation_order")
            ),
        ),
        _assertion(
            "all_checkpoint_codecs",
            subject=subject,
            expected_rows=select(independent, ("input_codec", "output_codec")),
            observed_rows=select(owner, ("input_codec", "output_codec")),
        ),
        _assertion(
            "abstraction_maps",
            subject=subject,
            expected_rows=select(independent, ("abstraction",)),
            observed_rows=select(owner, ("abstraction",)),
        ),
        _assertion(
            "rename_maps",
            subject=subject,
            expected_rows=select(independent, ("rename",)),
            observed_rows=select(owner, ("rename",)),
        ),
        _assertion(
            "forbidden_payload_absence",
            subject=subject,
            expected_rows=forbidden_rows(independent),
            observed_rows=forbidden_rows(owner),
        ),
    ]
    return _oracle_receipt(
        oracle_id=f"add:d{distance}:r{rounds}",
        subject=subject,
        subject_sha256=_sha256_bytes(raw),
        oracle_source=(
            "scripts/external_baselines/no_cutoff_target_lowering/"
            "independent_target_oracle.py"
        ),
        assertions=assertions,
    )


def _tn_receipt(
    *,
    distance: int,
    rounds: int,
    neutral_data: dict[str, Any],
    tn_data: dict[str, Any],
    raw: bytes,
) -> dict[str, Any]:
    owner = tn_data["semantic"]
    source_text = neutral_data["semantic"]["source"]["source_text"]
    incidence = reconstruct_network_incidence(source_text)
    subject = f"d{distance}_r{rounds}/tn"

    def tagged_indices(value: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            *({"row_kind": "index", **row} for row in value["index_catalog"]),
            *({"row_kind": "factor", **row} for row in value["factors"]),
            *({"row_kind": "marker", **row} for row in value["marker_ledger"]),
        ]

    assertions = [
        _assertion(
            "table_catalog",
            subject=subject,
            expected_rows=reconstruct_table_catalog(),
            observed_rows=owner["table_catalog"],
        ),
        _assertion(
            "index_incidence",
            subject=subject,
            expected_rows=tagged_indices(incidence),
            observed_rows=tagged_indices(owner),
        ),
        _assertion(
            "raw_consumers",
            subject=subject,
            expected_rows=incidence["raw_consumer_ledger"],
            observed_rows=owner["raw_consumer_ledger"],
        ),
        _assertion(
            "sign_chain",
            subject=subject,
            expected_rows=incidence["sign_occurrence_ledger"],
            observed_rows=owner["sign_occurrence_ledger"],
        ),
        _assertion(
            "record_boundary",
            subject=subject,
            expected_rows=[
                {"ordinal": index, "index_id": value}
                for index, value in enumerate(incidence["boundary"])
            ],
            observed_rows=[
                {"ordinal": index, "index_id": value}
                for index, value in enumerate(owner["boundary"])
            ],
        ),
    ]
    return _oracle_receipt(
        oracle_id=f"tn:d{distance}:r{rounds}",
        subject=subject,
        subject_sha256=_sha256_bytes(raw),
        oracle_source=(
            "scripts/external_baselines/no_cutoff_target_lowering/"
            "independent_tn_oracle.py"
        ),
        assertions=assertions,
    )


_CELL_RECEIPT_CACHE: dict[str, list[dict[str, Any]]] = {}


def build_cell_oracle_receipts(
    programs: Mapping[str, bytes],
) -> list[dict[str, Any]]:
    """Build the five independent target receipts for each frozen cell."""

    source_identity = _assert_qualification_sources_unchanged_since_import()
    identity = sha256_json(
        {
            "qualification_source_identity": source_identity,
            "programs": {
                path: _sha256_bytes(raw) if type(raw) is bytes else "NOT_BYTES"
                for path, raw in programs.items()
            },
        }
    )
    cached = _CELL_RECEIPT_CACHE.get(identity)
    if cached is not None:
        return deepcopy(cached)
    validate_program_artifacts(programs)
    receipts: list[dict[str, Any]] = []
    for distance, rounds in GRID:
        parsed = {
            name: _strict_json_bytes(
                programs[_program_path(distance, rounds, name)],
                subject=_program_path(distance, rounds, name),
            )
            for name in PROGRAM_NAMES
        }
        receipts.append(
            _source_receipt(
                distance=distance,
                rounds=rounds,
                neutral_data=parsed["neutral"],
                raw=programs[_program_path(distance, rounds, "neutral")],
            )
        )
        pair_receipt, rref_receipt = _pair_and_rref_receipts(
            distance=distance,
            rounds=rounds,
            neutral_data=parsed["neutral"],
            pair_data=parsed["pair"],
            pair_raw=programs[_program_path(distance, rounds, "pair")],
        )
        receipts.extend((pair_receipt, rref_receipt))
        receipts.append(
            _add_receipt(
                distance=distance,
                rounds=rounds,
                neutral_data=parsed["neutral"],
                add_data=parsed["add_relations"],
                raw=programs[_program_path(distance, rounds, "add_relations")],
            )
        )
        receipts.append(
            _tn_receipt(
                distance=distance,
                rounds=rounds,
                neutral_data=parsed["neutral"],
                tn_data=parsed["tn"],
                raw=programs[_program_path(distance, rounds, "tn")],
            )
        )
    receipts.sort(key=lambda receipt: receipt["oracle_id"])
    if _assert_qualification_sources_unchanged_since_import() != source_identity:
        raise ValueError("qualification source changed while building cell receipts")
    _CELL_RECEIPT_CACHE[identity] = deepcopy(receipts)
    return receipts


def _pair_witness_receipts() -> list[dict[str, Any]]:
    from .independent_pair_oracle import verify_pair_witness_component_matrices
    from .pair import build_pair_witness_component_catalog

    receipts: list[dict[str, Any]] = []
    for witness_id in ("P1", "P2"):
        catalog = build_pair_witness_component_catalog(witness_id)
        comparisons = verify_pair_witness_component_matrices(witness_id, catalog)

        def side_rows(matrix_field: str) -> list[dict[str, Any]]:
            rows: list[dict[str, Any]] = []
            for comparison in comparisons:
                row = {
                    key: deepcopy(value)
                    for key, value in comparison.items()
                    if key not in {"expected_matrix", "observed_matrix", "status"}
                }
                row["matrix"] = deepcopy(comparison[matrix_field])
                rows.append(row)
            return rows

        expected = side_rows("expected_matrix")
        observed = side_rows("observed_matrix")
        subject = f"{witness_id}/complete-pair-component-matrix"
        receipts.append(
            _oracle_receipt(
                oracle_id=f"pair-witness:{witness_id}",
                subject=subject,
                subject_sha256=sha256_json(catalog),
                oracle_source=(
                    "scripts/external_baselines/no_cutoff_target_lowering/"
                    "independent_pair_oracle.py"
                ),
                assertions=[
                    _assertion(
                        "complete_component_matrix",
                        subject=subject,
                        expected_rows=expected,
                        observed_rows=observed,
                    )
                ],
            )
        )
    return receipts


def _coset_witness_receipts() -> list[dict[str, Any]]:
    from .independent_target_oracle import reconstruct_coset_witness_rows
    from .pair import build_coset_witness_rows

    receipts: list[dict[str, Any]] = []
    for witness_id in ("C1", "C2", "C3", "C4"):
        owner_by_side = {
            side: build_coset_witness_rows(witness_id, side=side)
            for side in ("ket", "bra")
        }
        expected_by_side = {
            side: reconstruct_coset_witness_rows(witness_id, side=side)
            for side in ("ket", "bra")
        }
        subject = f"{witness_id}/signed-stabilizer-cosets"
        expected_idempotence = [
            {
                "side": side,
                "physical_pauli": row["physical_pauli"],
                "stabilizer_mask": row["stabilizer_mask"],
                "first_reduction": row["first_reduction"],
                "second_reduction": row["second_reduction"],
            }
            for side in ("ket", "bra")
            for row in expected_by_side[side]
        ]
        observed_idempotence = [
            {
                "side": side,
                "physical_pauli": row["physical_pauli"],
                "stabilizer_mask": row["stabilizer_mask"],
                "first_reduction": row["first_reduction"],
                "second_reduction": row["second_reduction"],
            }
            for side in ("ket", "bra")
            for row in owner_by_side[side]
        ]
        assertions = [
            _assertion(
                "ket_all_paulis_products",
                subject=subject,
                expected_rows=expected_by_side["ket"],
                observed_rows=owner_by_side["ket"],
            ),
            _assertion(
                "bra_all_paulis_products",
                subject=subject,
                expected_rows=expected_by_side["bra"],
                observed_rows=owner_by_side["bra"],
            ),
            _assertion(
                "idempotence",
                subject=subject,
                expected_rows=expected_idempotence,
                observed_rows=observed_idempotence,
            ),
        ]
        receipts.append(
            _oracle_receipt(
                oracle_id=f"coset-witness:{witness_id}",
                subject=subject,
                subject_sha256=sha256_json(owner_by_side),
                oracle_source=(
                    "scripts/external_baselines/no_cutoff_target_lowering/"
                    "independent_target_oracle.py"
                ),
                assertions=assertions,
            )
        )
    return receipts


def _subtract_exact_data(left: list[list[int]], right: list[list[int]]) -> list[list[int]]:
    from fractions import Fraction

    if len(left) != 4 or len(right) != 4:
        raise ValueError("exact witness scalar width changed")
    return [
        [difference.numerator, difference.denominator]
        for difference in (
            Fraction(a[0], a[1]) - Fraction(b[0], b[1])
            for a, b in zip(left, right, strict=True)
        )
    ]


def _tn_witness_receipts() -> list[dict[str, Any]]:
    from .independent_tn_oracle import reconstruct_tiny_retained_tensor
    from .tn import contract_tiny_retained_tensor

    receipts: list[dict[str, Any]] = []
    for witness_id in ("T1", "T2", "T3", "T4"):
        observed = contract_tiny_retained_tensor(witness_id)
        expected = reconstruct_tiny_retained_tensor(witness_id)
        subject = f"{witness_id}/complete-retained-tensor"
        assertions = [
            _assertion(
                "complete_retained_tensor",
                subject=subject,
                expected_rows=expected,
                observed_rows=observed,
            )
        ]
        if witness_id == "T3":
            owner_iid = contract_tiny_retained_tensor("T3", sign_process="iid")
            expected_iid = reconstruct_tiny_retained_tensor(
                "T3", sign_process="iid"
            )
            observed_delta = [
                {
                    "record": row["record"],
                    "delta": _subtract_exact_data(row["value"], iid["value"]),
                }
                for row, iid in zip(observed, owner_iid, strict=True)
            ]
            expected_delta = [
                {
                    "record": row["record"],
                    "delta": _subtract_exact_data(row["value"], iid["value"]),
                }
                for row, iid in zip(expected, expected_iid, strict=True)
            ]
            assertions.append(
                _assertion(
                    "persistent_iid_difference",
                    subject=subject,
                    expected_rows=expected_delta,
                    observed_rows=observed_delta,
                )
            )
        receipts.append(
            _oracle_receipt(
                oracle_id=f"tn-witness:{witness_id}",
                subject=subject,
                subject_sha256=sha256_json(observed),
                oracle_source=(
                    "scripts/external_baselines/no_cutoff_target_lowering/"
                    "independent_tn_oracle.py"
                ),
                assertions=assertions,
            )
        )
    return receipts


def build_non_add_witness_oracle_receipts() -> list[dict[str, Any]]:
    """Build complete P/C/T witness receipts, excluding ADD truth tables."""

    receipts = [
        *_pair_witness_receipts(),
        *_coset_witness_receipts(),
        *_tn_witness_receipts(),
    ]
    receipts.sort(key=lambda receipt: receipt["oracle_id"])
    return receipts


def metric_unavailable_objects() -> dict[str, dict[str, Any]]:
    static = {
        "status": "UNAVAILABLE/NOT_EXECUTED_STATIC_LOWERING_STAGE",
        "reason": "STATIC_TARGET_LOWERING_ONLY_NO_ROUTE_EXECUTION",
        "headline_eligible": False,
    }
    return {
        "n_pauli_pair_states_peak": dict(static),
        "n_exact_pair_add_nodes_peak": dict(static),
        "record_boundary_constrained_induced_width": dict(static),
        "tn_record_boundary_peak_dense_entries": dict(static),
        "delta_tv_cert": {
            "status": "UNAVAILABLE/UNANCHORED_FULL_RECORD",
            "reason": "NO_INDEPENDENT_COMPLETE_TARGET_RECORD_LAW",
            "headline_eligible": False,
        },
    }


def _validate_metric_unavailable_objects(value: object) -> None:
    if value != metric_unavailable_objects():
        raise ValueError("metric unavailable object was replaced or numerically injected")


@lru_cache(maxsize=1)
def _clean_corruption_artifacts() -> tuple[Any, Any, Any, Any]:
    neutral = lower_frozen_declared_error_record(distance=3, rounds=1)
    pair = build_exact_pair_transition_program(neutral)
    add = build_dynamic_add_relation_program(pair, neutral=neutral)
    tn = build_retained_boundary_factor_network(neutral)
    return neutral, pair, add, tn


def _rehash_envelope(data: dict[str, Any]) -> None:
    data["semantic_sha256"] = sha256_json(data["semantic"])


def _rehash_kernel_and_envelope(
    data: dict[str, Any], kernel: dict[str, Any]
) -> None:
    kernel["semantic_sha256"] = sha256_json(
        {key: value for key, value in kernel.items() if key != "semantic_sha256"}
    )
    _rehash_envelope(data)


def _require_changed(candidate: object, expected: object, message: str) -> None:
    if candidate != expected:
        raise ValueError(message)


def _corruption_case(
    control_id: str,
) -> tuple[str, str, type[BaseException], str, Any]:
    _assert_qualification_sources_unchanged_since_import()
    neutral, pair, add, tn = _clean_corruption_artifacts()
    neutral_sha = neutral.sha256
    pair_sha = pair.sha256
    add_sha = add.sha256
    tn_sha = tn.sha256

    if control_id == "iid_sign_resampling":
        changed = deepcopy(neutral.to_data()["semantic"])
        changed["process"]["latent"]["transition"] = (
            "resample_independently_at_each_occurrence"
        )

        def validate_iid_neutral_corruption() -> None:
            try:
                audit_persistent_sign_lowering(
                    changed,
                    pair.to_data()["semantic"],
                    tn.to_data()["semantic"],
                )
            except PersistentSignLoweringAuditError as exc:
                if exc.subchecks != {
                    "neutral_process": "FAIL",
                    "pair_latent": "PASS",
                    "tn_sign_chain": "PASS",
                }:
                    raise AssertionError(
                        "IID neutral corruption did not traverse pair and TN checks"
                    ) from exc
                raise ValueError(
                    "persistent-sign corruption detected by joint neutral/pair/TN audit"
                ) from exc
            raise AssertionError("IID neutral corruption escaped joint sign audit")

        return (
            neutral_sha,
            "replace the declared persistent latent by per-occurrence resampling",
            ValueError,
            "joint neutral/pair/TN audit",
            validate_iid_neutral_corruption,
        )

    if control_id in {
        "source_target_changed",
        "site_map_ordinal_changed",
        "dense_range_qubits",
        "cx_pair_swapped",
        "coherent_target_swapped",
        "rec_resolved_against_final",
        "record_raw_exposed",
        "record_latent_exposed",
    }:
        data = deepcopy(neutral.to_data())
        semantic = data["semantic"]
        mutation = control_id.replace("_", " ")
        if control_id == "source_target_changed":
            lines = semantic["source"]["source_text"].splitlines()
            row = next(index for index, line in enumerate(lines) if line.startswith("R "))
            tokens = lines[row].split()
            tokens[1], tokens[2] = tokens[2], tokens[1]
            lines[row] = " ".join(tokens)
            semantic["source"]["source_text"] = "\n".join(lines) + "\n"
            semantic["source"]["source_text_sha256"] = _sha256_bytes(
                semantic["source"]["source_text"].encode("utf-8")
            )
        elif control_id == "site_map_ordinal_changed":
            semantic["site_map"][0]["instruction_index"] += 1
        elif control_id == "dense_range_qubits":
            semantic["qubits"][0]["stim_id"] = 0
        elif control_id == "cx_pair_swapped":
            event = next(event for event in semantic["events"] if event["kind"] == "CX")
            event["qubits"].reverse()
        elif control_id == "coherent_target_swapped":
            events = [
                event for event in semantic["events"] if event["kind"] == "COHERENT_Z"
            ]
            events[0]["qubits"], events[1]["qubits"] = (
                events[1]["qubits"],
                events[0]["qubits"],
            )
        elif control_id == "rec_resolved_against_final":
            event = next(event for event in semantic["events"] if event["rec_operands"])
            event["rec_operands"][0]["absolute_raw_ordinal"] = (
                semantic["record_schema"]["raw_measurement_count"] - 1
            )
        elif control_id == "record_raw_exposed":
            semantic["record_schema"]["outputs"].append(
                {"kind": "RAW", "ordinal": 0, "producer_event_id": "e000000"}
            )
            semantic["record_schema"]["record_width"] += 1
        elif control_id == "record_latent_exposed":
            semantic["record_schema"]["outputs"].append(
                {"kind": "LATENT", "ordinal": 0, "producer_event_id": "e000000"}
            )
            semantic["record_schema"]["record_width"] += 1
        _rehash_envelope(data)
        if control_id in {
            "dense_range_qubits",
            "cx_pair_swapped",
            "coherent_target_swapped",
            "rec_resolved_against_final",
        }:
            independent = reconstruct_source_program(
                semantic["source"]["source_text"]
            )
            field = "qubits" if control_id == "dense_range_qubits" else "events"
            return (
                neutral_sha,
                mutation,
                ValueError,
                "independent source oracle",
                lambda: _require_changed(
                    semantic[field],
                    independent[field],
                    "corruption detected by independent source oracle",
                ),
            )
        return (
            neutral_sha,
            mutation,
            ValueError,
            (
                "Record schema"
                if control_id in {"record_raw_exposed", "record_latent_exposed"}
                else "frozen semantic identity"
            ),
            lambda: validate_declared_error_record_program(data),
        )

    if control_id in {
        "coherent_right_sign_flipped",
        "reset_k1_omitted",
        "measurement_postselected",
        "left_right_exchanged",
    }:
        from .independent_pair_oracle import (
            verify_pair_witness_component_matrices,
        )
        from .pair import build_pair_witness_component_catalog

        clean = build_pair_witness_component_catalog("P1")
        subject_sha = sha256_json(clean)
        changed = deepcopy(clean)
        mutation = {
            "coherent_right_sign_flipped": (
                "flip the right +i*m*s coefficient in one complete P1 kernel"
            ),
            "reset_k1_omitted": "omit every K1 reset component in one P1 row",
            "measurement_postselected": "remove the complete P1 M(b=1) branch",
            "left_right_exchanged": (
                "exchange noncommuting left/right actions in one P1 component"
            ),
        }[control_id]
        if control_id == "measurement_postselected":
            changed = [
                row
                for row in changed
                if row["operation_id"] != "M(b=1)"
            ]
        else:
            operation = "R" if control_id == "reset_k1_omitted" else "COHERENT_Z"
            if control_id == "reset_k1_omitted":
                for entry in changed:
                    if entry["operation_id"] == "R":
                        entry["component_rows"] = [
                            row
                            for row in entry["component_rows"]
                            if row["branch"][0] != {"name": "b", "value": 1}
                        ]
            else:
                entry = next(
                    row
                    for row in changed
                    if row["left_pauli"] == "I"
                    and row["right_pauli"] == "I"
                    and row["latent_m"] == -1
                    and row["operation_id"] == operation
                )
                component = next(
                    row
                    for row in entry["component_rows"]
                    if row["left_action"] != row["right_action"]
                )
                if control_id == "coherent_right_sign_flipped":
                    coefficient = component["multiplier_by_latent"][0][
                        "coefficient"
                    ][2]
                    coefficient[0] = -coefficient[0]
                else:
                    component["left_action"], component["right_action"] = (
                        component["right_action"],
                        component["left_action"],
                    )
        return (
            subject_sha,
            mutation,
            AssertionError,
            "witness",
            lambda: verify_pair_witness_component_matrices("P1", changed),
        )

    if control_id in {
        "codec_latent_omitted",
        "codec_accumulator_omitted",
        "codec_live_raw_omitted",
        "raw_dropped_early",
    }:
        independent = reconstruct_pair_receipt_rows(
            neutral.to_data()["semantic"]["source"]["source_text"]
        )
        changed = deepcopy(pair.to_data()["semantic"])
        mutation = control_id.replace("_", " ")
        if control_id in {"codec_latent_omitted", "codec_accumulator_omitted"}:
            field = (
                "latent_m"
                if control_id == "codec_latent_omitted"
                else "observable_0_accumulator"
            )
            changed["checkpoints"][0]["codec_fields"].remove(field)
            observed = _owner_checkpoint_codecs(changed)
            expected = independent["checkpoint_codecs"]
            message = "codec corruption detected by independent field-difference oracle"
        elif control_id == "codec_live_raw_omitted":
            checkpoint = next(row for row in changed["checkpoints"] if row["live_raw"])
            checkpoint["codec_fields"].remove(f"live_raw[{checkpoint['live_raw'][0]}]")
            observed = _owner_checkpoint_codecs(changed)
            expected = independent["checkpoint_codecs"]
            message = "codec corruption detected by independent field-difference oracle"
        else:
            checkpoint = next(row for row in changed["checkpoints"] if row["live_raw"])
            checkpoint["live_raw"].pop(0)
            observed = [row["live_raw"] for row in changed["checkpoints"]]
            expected = [
                [
                    int(field.removeprefix("live_raw[").removesuffix("]"))
                    for field in codec["fields"]
                    if field.startswith("live_raw[")
                ]
                for codec in independent["checkpoint_codecs"]
            ]
            message = "liveness corruption detected by independent codec oracle"
        return (
            pair_sha,
            mutation,
            ValueError,
            "codec corruption|liveness corruption",
            lambda: _require_changed(observed, expected, message),
        )

    if control_id in {
        "float_coefficient",
    }:
        data = deepcopy(pair.to_data())
        semantic = data["semantic"]
        mutation = control_id.replace("_", " ")
        if control_id == "float_coefficient":
            semantic["initial_terms"][0]["coefficient"][0] = 0.5
            _rehash_envelope(data)
            return (
                pair_sha,
                mutation,
                TypeError,
                "floating value",
                lambda: validate_exact_pair_transition_program(data, neutral=neutral),
            )
        if control_id == "coherent_right_sign_flipped":
            kernel = next(
                row for row in semantic["kernels"] if row["kind"] == "COHERENT_Z"
            )
            component = next(
                row
                for row in kernel["component_rows"]
                if row["branch"][1] == {"name": "right_Z", "value": 1}
            )
            rational = component["multiplier_by_latent"][0]["coefficient"][2]
            rational[0] = -rational[0]
            _rehash_kernel_and_envelope(data, kernel)
        elif control_id == "reset_k1_omitted":
            kernel = next(row for row in semantic["kernels"] if row["kind"] == "RESET")
            kernel["component_rows"] = [
                row
                for row in kernel["component_rows"]
                if row["branch"][0] != {"name": "b", "value": 1}
            ]
            _rehash_kernel_and_envelope(data, kernel)
        elif control_id == "measurement_postselected":
            kernel = next(row for row in semantic["kernels"] if row["kind"] == "M")
            kernel["component_rows"] = [
                row
                for row in kernel["component_rows"]
                if row["branch"][0] == {"name": "b", "value": 0}
            ]
            _rehash_kernel_and_envelope(data, kernel)
        elif control_id == "left_right_exchanged":
            kernel = next(
                row for row in semantic["kernels"] if row["kind"] == "COHERENT_Z"
            )
            component = next(
                row
                for row in kernel["component_rows"]
                if row["left_action"]["opcode"] != row["right_action"]["opcode"]
            )
            component["left_action"], component["right_action"] = (
                component["right_action"],
                component["left_action"],
            )
            _rehash_kernel_and_envelope(data, kernel)
        return (
            pair_sha,
            mutation,
            ValueError,
            "frozen semantic identity",
            lambda: validate_exact_pair_transition_program(data, neutral=neutral),
        )

    if control_id == "rref_phase_dropped":
        from .independent_target_oracle import reconstruct_coset_witness_rows
        from .pair import build_coset_witness_rows

        clean = build_coset_witness_rows("C4", side="ket")
        changed = deepcopy(clean)
        row = next(
            row
            for row in changed
            if row["first_reduction"]["coefficient_phase_mod4"] != 0
        )
        row["first_reduction"]["coefficient_phase_mod4"] = 0
        return (
            sha256_json(clean),
            "drop one nonzero signed-RREF reduction phase",
            ValueError,
            "rref phase corruption",
            lambda: _require_changed(
                changed,
                reconstruct_coset_witness_rows("C4", side="ket"),
                "rref phase corruption detected by independent coset oracle",
            ),
        )

    if control_id == "rref_rightmost_pivot":
        from .independent_target_oracle import reconstruct_coset_witness_rows
        from .pair import build_coset_witness_rows

        clean = build_coset_witness_rows("C4", side="ket")
        changed = deepcopy(clean)
        row = next(
            row
            for row in changed
            if row["physical_pauli"] != row["first_reduction"]["representative"]
        )
        row["first_reduction"]["representative"] = deepcopy(
            row["physical_pauli"]
        )
        return (
            sha256_json(clean),
            "replace one leftmost-pivot reduction by a rightmost-style remainder",
            ValueError,
            "rightmost pivot corruption",
            lambda: _require_changed(
                changed,
                reconstruct_coset_witness_rows("C4", side="ket"),
                "rightmost pivot corruption detected by independent coset oracle",
            ),
        )

    if control_id in {"add_coefficient_changed", "add_current_root_field"}:
        data = deepcopy(add.to_data())
        mutation = control_id.replace("_", " ")
        if control_id == "add_coefficient_changed":
            corrupted_pair = deepcopy(pair.to_data())
            kernel = next(
                row
                for row in corrupted_pair["semantic"]["kernels"]
                if row["component_rows"]
            )
            coefficient = kernel["component_rows"][0]["multiplier_by_latent"][0][
                "coefficient"
            ][0]
            coefficient[0] = -coefficient[0]
            _rehash_kernel_and_envelope(corrupted_pair, kernel)
            data["semantic"]["events"][0]["pair_semantic_sha256"] = kernel[
                "semantic_sha256"
            ]
            independent = reconstruct_add_relation_events(
                neutral.to_data()["semantic"]["source"]["source_text"]
            )
            observed = data["semantic"]["events"]
            return (
                add_sha,
                "flip one pair coefficient and bind its changed event hash",
                ValueError,
                "independent ADD relation",
                lambda: _require_changed(
                    observed,
                    independent,
                    "coefficient corruption detected by independent ADD relation",
                ),
            )
        else:
            data["semantic"]["current_root"] = 0
            pattern = "semantic schema"
        _rehash_envelope(data)
        return (
            add_sha,
            mutation,
            ValueError,
            pattern,
            lambda: validate_dynamic_add_relation_program(
                data, pair=pair, neutral=neutral
            ),
        )

    if control_id == "tn_iid_signs":
        from .independent_tn_oracle import reconstruct_tiny_retained_tensor
        from .tn import contract_tiny_retained_tensor

        changed = deepcopy(tn.to_data()["semantic"])
        sign_eq_count = 0
        for factor in changed["factors"]:
            if factor["template_id"] != "SIGN_EQ":
                continue
            sign_eq_count += 1
            factor["template_id"] = "HALF"
            factor["shape"] = [2]
            factor["scope"] = [factor["scope"][1]]
        persistent = reconstruct_tiny_retained_tensor("T3")
        iid = contract_tiny_retained_tensor("T3", sign_process="iid")

        def validate_tn_iid_corruption() -> None:
            audit_error: PersistentSignLoweringAuditError | None = None
            try:
                audit_persistent_sign_lowering(
                    neutral.to_data()["semantic"],
                    pair.to_data()["semantic"],
                    changed,
                )
            except PersistentSignLoweringAuditError as exc:
                audit_error = exc
            if audit_error is None:
                raise AssertionError("IID TN corruption escaped joint sign audit")
            if sign_eq_count == 0 or audit_error.subchecks != {
                "neutral_process": "PASS",
                "pair_latent": "PASS",
                "tn_sign_chain": "FAIL",
            }:
                raise AssertionError(
                    "IID TN corruption did not isolate the TN sign-chain check"
                ) from audit_error
            if iid == persistent:
                raise AssertionError(
                    "IID TN corruption escaped tiny direct-density oracle"
                ) from audit_error
            raise ValueError(
                "persistent-sign corruption detected by joint lowering audit "
                "and tiny direct-density oracle"
            ) from audit_error

        return (
            sha256_json(persistent),
            (
                "replace every SIGN_EQ incidence and the T3 sign process by "
                "per-occurrence IID signs"
            ),
            ValueError,
            "joint lowering audit and tiny direct-density oracle",
            validate_tn_iid_corruption,
        )

    if control_id in {"tn_measurement_dephased", "tn_reset_trace_omitted"}:
        from .independent_tn_oracle import reconstruct_tiny_retained_tensor
        from .tn import (
            build_tiny_corrupted_table_catalog,
            contract_tiny_retained_tensor,
        )

        witness_id = "T1" if control_id == "tn_measurement_dephased" else "T2"
        expected = reconstruct_tiny_retained_tensor(witness_id)
        observed = contract_tiny_retained_tensor(
            witness_id,
            table_catalog=build_tiny_corrupted_table_catalog(control_id),
        )
        return (
            sha256_json(expected),
            (
                "replace M by nonselective dephasing with clamped raw output"
                if control_id == "tn_measurement_dephased"
                else "omit the MR K1 reset branch"
            ),
            ValueError,
            "direct-density corruption",
            lambda: _require_changed(
                observed,
                expected,
                "direct-density corruption detected by complete tiny tensor",
            ),
        )

    if control_id in {
        "structural_zero_pruned",
        "tn_density_transposed",
        "tn_table_sparsified",
        "tn_copy_removed",
        "tn_keep_removed",
        "tn_sign_codec_swapped",
    }:
        data = deepcopy(tn.to_data())
        semantic = data["semantic"]
        mutation = control_id.replace("_", " ")
        templates = {
            row["template_id"]: row for row in semantic["table_catalog"]
        }
        zero = [[0, 1], [0, 1], [0, 1], [0, 1]]
        if control_id == "structural_zero_pruned":
            templates["INIT0"]["table"].pop()
        elif control_id == "tn_density_transposed":
            table = templates["COHERENT_Z"]["table"]
            original = deepcopy(table)
            digit_swap = (0, 2, 1, 3)
            for q_in, q_out, sign in product(range(4), range(4), range(2)):
                target = (q_in * 4 + q_out) * 2 + sign
                source = (
                    (digit_swap[q_in] * 4 + digit_swap[q_out]) * 2 + sign
                )
                table[target] = original[source]
        elif control_id == "tn_table_sparsified":
            table = templates["COHERENT_Z"]["table"]
            table.pop(table.index(zero))
        elif control_id == "tn_measurement_dephased":
            table = templates["M"]["table"]
            table[0], table[1] = table[1], table[0]
        elif control_id == "tn_reset_trace_omitted":
            templates["R"]["table"][0] = zero
        elif control_id == "tn_copy_removed":
            index = next(
                index
                for index, factor in enumerate(semantic["factors"])
                if factor["template_id"] == "COPY"
            )
            semantic["factors"].pop(index)
        elif control_id == "tn_keep_removed":
            index = next(
                index
                for index, factor in enumerate(semantic["factors"])
                if factor["template_id"] == "KEEP"
            )
            semantic["factors"].pop(index)
        elif control_id == "tn_iid_signs":
            factor = next(
                row for row in semantic["factors"] if row["template_id"] == "SIGN_EQ"
            )
            factor["template_id"] = "HALF"
            factor["shape"] = [2]
            factor["scope"] = [factor["scope"][1]]
        else:
            table = templates["COHERENT_Z"]["table"]
            for offset in range(0, len(table), 2):
                table[offset], table[offset + 1] = table[offset + 1], table[offset]
        _rehash_envelope(data)
        if control_id in {
            "structural_zero_pruned",
            "tn_density_transposed",
            "tn_table_sparsified",
            "tn_sign_codec_swapped",
        }:
            from .independent_tn_oracle import validate_table_catalog

            return (
                tn_sha,
                mutation,
                ValueError,
                "template|differs",
                lambda: validate_table_catalog(semantic["table_catalog"]),
            )
        if control_id in {"tn_copy_removed", "tn_keep_removed"}:
            incidence = reconstruct_network_incidence(
                neutral.to_data()["semantic"]["source"]["source_text"]
            )
            observed = {key: semantic[key] for key in incidence}
            if control_id == "tn_keep_removed":
                from .independent_tn_oracle import (
                    validate_retained_boundary_keep_coverage,
                )

                def validate_keep_corruption() -> None:
                    if observed == incidence:
                        raise AssertionError(
                            "KEEP corruption escaped independent incidence"
                        )
                    try:
                        validate_retained_boundary_keep_coverage(semantic)
                    except ValueError as exc:
                        raise ValueError(
                            "incidence corruption and retained boundary KEEP coverage"
                        ) from exc
                    raise AssertionError(
                        "KEEP corruption escaped retained-boundary structure"
                    )

                return (
                    tn_sha,
                    mutation,
                    ValueError,
                    "incidence corruption and retained boundary KEEP coverage",
                    validate_keep_corruption,
                )
            return (
                tn_sha,
                mutation,
                ValueError,
                "incidence corruption",
                lambda: _require_changed(
                    observed,
                    incidence,
                    "incidence corruption detected by independent TN oracle",
                ),
            )
        return (
            tn_sha,
            mutation,
            ValueError,
            "frozen semantic identity",
            lambda: validate_retained_boundary_factor_network(data, neutral=neutral),
        )

    if control_id == "numeric_metric_injected":
        metrics = metric_unavailable_objects()
        subject_sha = sha256_json(metrics)
        metrics["n_pauli_pair_states_peak"] = 1  # type: ignore[assignment]
        return (
            subject_sha,
            "replace unavailable pair metric with numeric one",
            ValueError,
            "metric unavailable object",
            lambda: _validate_metric_unavailable_objects(metrics),
        )

    if control_id == "historical_artifact_changed":
        raw = (REPO / STRUCTURE_REPORT_RELATIVE).read_bytes()
        changed = raw + b" "

        def validate_changed_history() -> None:
            if _sha256_bytes(changed) != STRUCTURE_REPORT_SHA256:
                raise ValueError("historical artifact changed")

        return (
            STRUCTURE_REPORT_SHA256,
            "append one byte to the historical census report in memory",
            ValueError,
            "historical artifact changed",
            validate_changed_history,
        )

    raise ValueError(f"unknown corruption control {control_id!r}")


def run_corruption_control(control_id: str) -> dict[str, Any]:
    """Apply one registered mutation and require its real validator to trip."""

    if control_id not in CORRUPTION_CONTROL_IDS:
        raise ValueError("corruption control id is not registered")
    subject_sha256, mutation, exception_type, pattern, action = _corruption_case(
        control_id
    )
    try:
        action()
    except Exception as exc:
        if type(exc) is not exception_type or re.search(pattern, str(exc)) is None:
            raise AssertionError(
                f"{control_id} tripped the wrong exception: {type(exc).__name__}: {exc}"
            ) from exc
        observed_descriptor = {
            "type": type(exc).__name__,
            "message_pattern": pattern,
        }
    else:
        raise AssertionError(f"{control_id} mutation was not rejected")
    descriptor = {"type": exception_type.__name__, "message_pattern": pattern}
    body = {
        "control_id": control_id,
        "subject_sha256": subject_sha256,
        "mutation": mutation,
        "expected_exception": descriptor,
        "observed_exception": observed_descriptor,
        "test_nodeid": (
            "tests/test_external_no_cutoff_target_independent_oracles.py::"
            f"test_registered_corruption_control_trips[{control_id}]"
        ),
        "status": "TRIPPED",
    }
    return {**body, "receipt_sha256": sha256_json(body)}


def build_corruption_control_receipts() -> list[dict[str, Any]]:
    return [run_corruption_control(control_id) for control_id in CORRUPTION_CONTROL_IDS]


def verify_historical_firewall() -> dict[str, Any]:
    """Rehash prior publications and their recorded owner/test manifests."""

    fixed = {
        STRUCTURE_REPORT_RELATIVE: STRUCTURE_REPORT_SHA256,
        MINIMAL_REPORT_RELATIVE: MINIMAL_REPORT_SHA256,
        MINIMAL_RECEIPT_RELATIVE: MINIMAL_RECEIPT_SHA256,
    }
    fixed_raw: dict[str, bytes] = {}
    for relative, expected in fixed.items():
        try:
            raw = _read_regular_file_no_symlinks(REPO / relative)
        except (FileNotFoundError, ValueError) as exc:
            raise ValueError(f"historical artifact changed: {relative}") from exc
        if _sha256_bytes(raw) != expected:
            raise ValueError(f"historical artifact changed: {relative}")
        fixed_raw[relative] = raw

    minimal_report = _strict_json_bytes(
        fixed_raw[MINIMAL_REPORT_RELATIVE],
        subject="historical minimal report",
    )
    provenance = minimal_report.get("provenance")
    if not isinstance(provenance, dict):
        raise ValueError("historical minimal report lacks provenance")
    manifests: dict[str, str] = {}
    for key in ("source_sha256", "test_sha256"):
        values = provenance.get(key)
        if not isinstance(values, dict) or not values:
            raise ValueError(f"historical minimal report lacks {key}")
        for relative, expected in values.items():
            if not isinstance(relative, str) or not isinstance(expected, str):
                raise ValueError(f"historical {key} has an invalid row")
            manifests[relative] = expected
    manifests.update(_CENSUS_SOURCE_ANCHORS)
    for relative, expected in manifests.items():
        try:
            observed = _secure_file_sha256(REPO / relative)
        except (FileNotFoundError, ValueError) as exc:
            raise ValueError(
                f"historical source/test manifest changed: {relative}"
            ) from exc
        if observed != expected:
            raise ValueError(f"historical source/test manifest changed: {relative}")

    minimal_receipt = _strict_json_bytes(
        fixed_raw[MINIMAL_RECEIPT_RELATIVE],
        subject="historical minimal receipt",
    )
    if (
        minimal_receipt.get("report_complete_file_sha256")
        != MINIMAL_REPORT_SHA256
        or minimal_receipt.get("report_content_sha256")
        != MINIMAL_REPORT_CONTENT_SHA256
    ):
        raise ValueError("historical minimal receipt/report binding changed")
    receipt_body = {
        key: value
        for key, value in minimal_receipt.items()
        if key != "content_sha256"
    }
    if minimal_receipt.get("content_sha256") != _sha256_bytes(
        canonical_json_bytes(receipt_body)
    ):
        raise ValueError("historical minimal receipt content hash mismatch")

    return {
        "structure_report": STRUCTURE_REPORT_SHA256,
        "minimal_report": MINIMAL_REPORT_SHA256,
        "minimal_receipt": MINIMAL_RECEIPT_SHA256,
        "source_test_manifests_match": True,
    }


def qualification_test_command() -> list[str]:
    """Return the one argv permitted to mint qualification evidence."""

    return [sys.executable, "-m", "pytest", "-q", *TEST_FILES]


def collect_qualification_nodeids() -> list[str]:
    """Collect the exact six-file qualification surface without executing it."""

    command = [
        sys.executable,
        "-m",
        "pytest",
        "--collect-only",
        "-q",
        *TEST_FILES,
    ]
    completed = subprocess.run(
        command,
        cwd=REPO,
        capture_output=True,
        check=False,
        text=True,
        timeout=120,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "qualification node-id collection failed:\n"
            + (completed.stdout + completed.stderr)[-4000:]
        )
    nodeids = sorted(
        line.strip()
        for line in completed.stdout.splitlines()
        if line.startswith("tests/") and "::" in line
    )
    if not nodeids or len(nodeids) != len(set(nodeids)):
        raise ValueError("qualification node-id collection is empty or duplicated")
    return nodeids


def _make_observed_test_run_receipt(
    *, command: list[str], nodeids: list[str], passed: int, failed: int
) -> dict[str, Any]:
    """Mint the frozen receipt shape after ``run_qualification_tests`` observes it."""

    body = {
        "command": list(command),
        "nodeids": sorted(nodeids),
        "passed": passed,
        "failed": failed,
    }
    receipt = {**body, "receipt_sha256": sha256_json(body)}
    _validate_test_run_receipt(receipt)
    return receipt


def _observed_pass_count(completed: subprocess.CompletedProcess[str]) -> int:
    combined = completed.stdout + "\n" + completed.stderr
    forbidden = re.compile(
        r"\b(?:failed|error|errors|skipped|xfailed|xpassed|deselected)\b",
        flags=re.IGNORECASE,
    )
    matches = re.findall(
        r"(?m)(\d+) passed(?:, \d+ warnings?)? in [^\r\n]+$",
        combined,
    )
    if completed.returncode != 0 or len(matches) != 1 or forbidden.search(combined):
        raise RuntimeError(
            "fresh-process qualification tests did not produce one all-pass outcome:\n"
            + combined[-4000:]
        )
    return int(matches[0])


_OBSERVED_TEST_RUN_TOKEN = object()


class _ObservedTestRun:
    """Opaque same-process authority minted only after an observed pytest run."""

    __slots__ = ("_receipt", "_token")

    def __init__(self, receipt: dict[str, Any], token: object) -> None:
        if token is not _OBSERVED_TEST_RUN_TOKEN:
            raise TypeError("observed test-run capability is not mintable by callers")
        self._receipt = deepcopy(receipt)
        self._token = token

    def _validated_receipt(self) -> dict[str, Any]:
        if self._token is not _OBSERVED_TEST_RUN_TOKEN:
            raise TypeError("observed test-run capability is invalid")
        _validate_test_run_receipt(self._receipt)
        return deepcopy(self._receipt)


def run_qualification_tests() -> _ObservedTestRun:
    """Execute the exact frozen test surface and mint an opaque capability."""

    source_identity = _assert_qualification_sources_unchanged_since_import()
    nodeids = collect_qualification_nodeids()
    command = qualification_test_command()
    environment = os.environ.copy()
    environment.pop("PYTEST_ADDOPTS", None)
    environment.pop("PYTEST_PLUGINS", None)
    completed = subprocess.run(
        command,
        cwd=REPO,
        env=environment,
        capture_output=True,
        check=False,
        text=True,
        timeout=900,
    )
    passed = _observed_pass_count(completed)
    if passed != len(nodeids):
        raise RuntimeError(
            f"qualification execution passed {passed} tests; collected {len(nodeids)}"
        )
    if _assert_qualification_sources_unchanged_since_import() != source_identity:
        raise ValueError("qualification source changed during test execution")
    receipt = _make_observed_test_run_receipt(
        command=command, nodeids=nodeids, passed=passed, failed=0
    )
    return _ObservedTestRun(receipt, _OBSERVED_TEST_RUN_TOKEN)


def _validate_test_run_receipt(value: object) -> None:
    if not isinstance(value, dict) or set(value) != {
        "command",
        "nodeids",
        "passed",
        "failed",
        "receipt_sha256",
    }:
        raise ValueError("test run receipt schema mismatch")
    body = {key: item for key, item in value.items() if key != "receipt_sha256"}
    if value["receipt_sha256"] != sha256_json(body):
        raise ValueError("test run receipt hash mismatch")
    command = value["command"]
    nodeids = value["nodeids"]
    if (
        not isinstance(command, list)
        or not command
        or any(not isinstance(item, str) or not item for item in command)
    ):
        raise ValueError("test run command is not an exact argv list")
    if command != qualification_test_command():
        raise ValueError("test run command drift")
    if (
        not isinstance(nodeids, list)
        or any(not isinstance(item, str) for item in nodeids)
        or nodeids != sorted(set(nodeids))
    ):
        raise ValueError("test run nodeids are not unique and sorted")
    if type(value["passed"]) is not int or type(value["failed"]) is not int:
        raise TypeError("test run counts must be integers")
    if value["passed"] != len(nodeids) or value["failed"] != 0:
        raise ValueError("test run is not an all-pass execution of every nodeid")
    expected_nodeids = collect_qualification_nodeids()
    if nodeids != expected_nodeids:
        raise ValueError("test run node-id set drift")
    required_controls = {
        (
            "tests/test_external_no_cutoff_target_independent_oracles.py::"
            f"test_registered_corruption_control_trips[{control_id}]"
        )
        for control_id in CORRUPTION_CONTROL_IDS
    }
    if not required_controls <= set(nodeids):
        raise ValueError("test run omits registered corruption-control nodeids")


def _file_manifest(paths: tuple[str, ...]) -> dict[str, str]:
    result: dict[str, str] = {}
    for relative in paths:
        path = REPO / relative
        try:
            result[relative] = _secure_file_sha256(path)
        except (FileNotFoundError, ValueError) as exc:
            raise FileNotFoundError(
                f"qualification source is missing or unsafe: {relative}"
            ) from exc
    return result


def _artifact_descriptor(path: str, raw: bytes) -> dict[str, str]:
    data = _strict_json_bytes(raw, subject=path)
    return {
        "path": path,
        "schema": data["_schema"],
        "sha256": _sha256_bytes(raw),
        "semantic_sha256": data["semantic_sha256"],
    }


def _add_truth_oracle_receipts() -> list[dict[str, Any]]:
    from .add_relations import summarize_tiny_add_truth_assertion
    from .independent_target_oracle import (
        summarize_reconstructed_tiny_add_truth_assertion,
    )

    receipts: list[dict[str, Any]] = []
    for witness_id in ("P1", "P2", "T1", "T2", "T3", "T4"):
        subject = f"{witness_id}/complete-static-add-truth"
        assertion_id = "every_valid_and_invalid_code"
        observed = summarize_tiny_add_truth_assertion(
            witness_id, assertion_id=assertion_id, subject=subject
        )
        expected = summarize_reconstructed_tiny_add_truth_assertion(
            witness_id, assertion_id=assertion_id, subject=subject
        )
        status = (
            "PASS"
            if expected["row_count"] == observed["row_count"]
            and expected["sha256"] == observed["sha256"]
            else "FAILED"
        )
        receipts.append(
            _oracle_receipt(
                oracle_id=f"add-truth:{witness_id}",
                subject=subject,
                subject_sha256=observed["rows_sha256"],
                oracle_source=(
                    "scripts/external_baselines/no_cutoff_target_lowering/"
                    "independent_target_oracle.py"
                ),
                assertions=[
                    {
                        "assertion_id": assertion_id,
                        "status": status,
                        "row_count": expected["row_count"],
                        "expected_sha256": expected["sha256"],
                        "observed_sha256": observed["sha256"],
                    }
                ],
            )
        )
    return receipts


_ALL_ORACLE_CACHE: dict[str, list[dict[str, Any]]] = {}


def build_all_oracle_receipts(
    programs: Mapping[str, bytes],
) -> list[dict[str, Any]]:
    source_identity = _assert_qualification_sources_unchanged_since_import()
    identity = sha256_json(
        {
            "qualification_source_identity": source_identity,
            "programs": {
                path: _sha256_bytes(raw) if type(raw) is bytes else "NOT_BYTES"
                for path, raw in programs.items()
            },
        }
    )
    cached = _ALL_ORACLE_CACHE.get(identity)
    if cached is not None:
        return deepcopy(cached)
    receipts = [
        *build_cell_oracle_receipts(programs),
        *build_non_add_witness_oracle_receipts(),
        *_add_truth_oracle_receipts(),
    ]
    receipts.sort(key=lambda receipt: receipt["oracle_id"])
    if len(receipts) != 56 or len({row["oracle_id"] for row in receipts}) != 56:
        raise ValueError("oracle receipt catalog is incomplete or duplicated")
    if _assert_qualification_sources_unchanged_since_import() != source_identity:
        raise ValueError("qualification source changed while building oracle receipts")
    _ALL_ORACLE_CACHE[identity] = deepcopy(receipts)
    return receipts


def _schema_manifest() -> dict[str, str]:
    return {
        "neutral": NEUTRAL_SCHEMA,
        "pair": PAIR_SCHEMA,
        "add_relations": ADD_SCHEMA,
        "tn": TN_SCHEMA,
        "report": REPORT_SCHEMA,
        "receipt": PUBLICATION_RECEIPT_SCHEMA,
    }


def _assemble_qualification_report_from_receipt(
    programs: Mapping[str, bytes], *, test_run: Mapping[str, Any]
) -> dict[str, Any]:
    """Internal deterministic assembly from a structurally validated receipt."""

    source_identity = _assert_qualification_sources_unchanged_since_import()
    validate_program_artifacts(programs)
    test_run_data = deepcopy(dict(test_run))
    _validate_test_run_receipt(test_run_data)
    for relative, expected in (
        (PREREG_RELATIVE, ACTIVE_PREREG_SHA256),
        (REVIEW_RELATIVE, REVIEW_RECEIPT_SHA256),
        (LITERATURE_CLOSURE_RELATIVE, LITERATURE_CLOSURE_SHA256),
        (FIXTURE_MANIFEST_RELATIVE, FIXTURE_MANIFEST_SHA256),
    ):
        if _secure_file_sha256(REPO / relative) != expected:
            raise ValueError(f"qualification authority changed: {relative}")

    artifact_manifest = {
        path: _sha256_bytes(programs[path]) for path in sorted(programs)
    }
    oracle_receipts = build_all_oracle_receipts(programs)
    receipts_by_id = {row["oracle_id"]: row for row in oracle_receipts}
    cells: list[dict[str, Any]] = []
    qualified = "QUALIFIED_STATIC_TARGET_LOWERING"
    for distance, rounds in GRID:
        artifacts = {
            name: _artifact_descriptor(
                _program_path(distance, rounds, name),
                programs[_program_path(distance, rounds, name)],
            )
            for name in PROGRAM_NAMES
        }
        oracle_ids = [
            f"{prefix}:d{distance}:r{rounds}"
            for prefix in ("source", "pair", "rref", "add", "tn")
        ]
        if any(oracle_id not in receipts_by_id for oracle_id in oracle_ids):
            raise ValueError("cell oracle receipt is missing")
        cells.append(
            {
                "distance": distance,
                "rounds": rounds,
                "artifacts": artifacts,
                "oracle_receipt_ids": oracle_ids,
                "statuses": {
                    "neutral": qualified,
                    "pair": qualified,
                    "add_relations": qualified,
                    "tn": qualified,
                },
            }
        )

    controls = build_corruption_control_receipts()
    source_files = _file_manifest(SOURCE_FILES)
    test_files = _file_manifest(TEST_FILES)
    body: dict[str, Any] = {
        "_schema": REPORT_SCHEMA,
        "report_status": REPORT_STATUS,
        "scope": STATIC_SCOPE,
        "preregistration": {
            "path": PREREG_RELATIVE,
            "active_sha256": ACTIVE_PREREG_SHA256,
            "reviewed_preactivation_sha256": REVIEWED_PREACTIVATION_SHA256,
            "review_receipt_sha256": REVIEW_RECEIPT_SHA256,
        },
        "literature_closure": {
            "path": LITERATURE_CLOSURE_RELATIVE,
            "sha256": LITERATURE_CLOSURE_SHA256,
            "status": "CLOSED_FOR_STATIC_TARGET_LOWERING",
        },
        "fixture_manifest": {
            "path": FIXTURE_MANIFEST_RELATIVE,
            "sha256": FIXTURE_MANIFEST_SHA256,
            "schema": FIXTURE_MANIFEST_SCHEMA,
        },
        "historical_firewall": verify_historical_firewall(),
        "artifact_manifest": artifact_manifest,
        "cells": cells,
        "independent_oracle_receipts": oracle_receipts,
        "corruption_controls": controls,
        "metrics": metric_unavailable_objects(),
        "route_disposition": "NONE/STATIC_LOWERING_ONLY",
        "solver_permission": "CODE_BLOCKED",
        "provenance": {
            "python": {
                "name": platform.python_implementation(),
                "version": platform.python_version(),
            },
            "stim": {
                "name": "stim",
                "version": importlib.metadata.version("stim"),
            },
            "sympy": {
                "name": "sympy",
                "version": importlib.metadata.version("sympy"),
            },
            "dependencies": [
                {
                    "name": "pytest",
                    "version": importlib.metadata.version("pytest"),
                }
            ],
            "source_files": source_files,
            "test_files": test_files,
            "test_run": test_run_data,
            "schemas": _schema_manifest(),
        },
    }
    result = {**body, "content_sha256": sha256_json(body)}
    if _assert_qualification_sources_unchanged_since_import() != source_identity:
        raise ValueError("qualification source changed while assembling report")
    return result


def assemble_qualification_report(
    programs: Mapping[str, bytes], *, observed_test_run: _ObservedTestRun
) -> dict[str, Any]:
    """Production assembly requiring same-process evidence from the runner."""

    if type(observed_test_run) is not _ObservedTestRun:
        raise TypeError(
            "production report assembly requires run_qualification_tests() evidence"
        )
    return _assemble_qualification_report_from_receipt(
        programs,
        test_run=observed_test_run._validated_receipt(),
    )


def validate_qualification_report(
    report: object,
    *,
    programs: Mapping[str, bytes],
    verify_current_sources: bool = True,
) -> None:
    if not isinstance(report, dict):
        raise TypeError("qualification report must be a JSON object")
    reject_floats(report)
    required_keys = {
        "_schema",
        "report_status",
        "scope",
        "preregistration",
        "literature_closure",
        "fixture_manifest",
        "historical_firewall",
        "artifact_manifest",
        "cells",
        "independent_oracle_receipts",
        "corruption_controls",
        "metrics",
        "route_disposition",
        "solver_permission",
        "provenance",
        "content_sha256",
    }
    if set(report) != required_keys:
        raise ValueError("qualification report top-level schema mismatch")
    body = {key: value for key, value in report.items() if key != "content_sha256"}
    if report["content_sha256"] != sha256_json(body):
        raise ValueError("qualification report content hash mismatch")
    provenance = report.get("provenance")
    if not isinstance(provenance, dict):
        raise ValueError("qualification report provenance schema mismatch")
    _validate_test_run_receipt(provenance.get("test_run"))
    _validate_metric_unavailable_objects(report.get("metrics"))
    expected = _assemble_qualification_report_from_receipt(
        programs, test_run=provenance["test_run"]
    )
    if canonical_json_bytes(report) != canonical_json_bytes(expected):
        if verify_current_sources:
            raise ValueError(
                "qualification report does not reproduce current frozen evidence"
            )
        raise ValueError("qualification report semantic identity mismatch")


def _relative_parts(relative: str) -> tuple[str, ...]:
    parts = Path(relative).parts
    if not parts or Path(relative).is_absolute() or any(
        part in {"", ".", ".."} for part in parts
    ):
        raise ValueError(f"publication path is not a safe relative path: {relative}")
    return parts


def _directory_open_flags() -> int:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    return flags


def _open_relative_parent(
    root_descriptor: int, relative: str, *, create: bool
) -> tuple[int, str]:
    parts = _relative_parts(relative)
    descriptor = os.dup(root_descriptor)
    try:
        for component in parts[:-1]:
            created = False
            if create:
                try:
                    os.mkdir(component, mode=0o755, dir_fd=descriptor)
                    created = True
                except FileExistsError:
                    pass
            try:
                child = os.open(
                    component, _directory_open_flags(), dir_fd=descriptor
                )
            except OSError as exc:
                if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
                    raise ValueError(
                        f"publication parent is a symlink or non-directory: {relative}"
                    ) from exc
                raise
            if created:
                os.fsync(descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor, parts[-1]
    except Exception:
        os.close(descriptor)
        raise


def _exclusive_write_at(root_descriptor: int, relative: str, raw: bytes) -> None:
    parent, name = _open_relative_parent(root_descriptor, relative, create=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(name, flags, 0o644, dir_fd=parent)
        try:
            view = memoryview(raw)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    raise OSError("exclusive publication write made no progress")
                view = view[written:]
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.fsync(parent)
    finally:
        os.close(parent)


def _read_regular_at(root_descriptor: int, relative: str) -> bytes:
    parent, name = _open_relative_parent(root_descriptor, relative, create=False)
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        try:
            descriptor = os.open(name, flags, dir_fd=parent)
        except OSError as exc:
            if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
                raise ValueError(f"published file is a symlink: {relative}") from exc
            raise
        try:
            before = os.fstat(descriptor)
            if not stat.S_ISREG(before.st_mode):
                raise ValueError(f"published path is not a regular file: {relative}")
            chunks: list[bytes] = []
            while True:
                block = os.read(descriptor, 1024 * 1024)
                if not block:
                    break
                chunks.append(block)
            after = os.fstat(descriptor)
            if (
                before.st_dev,
                before.st_ino,
                before.st_size,
                before.st_mtime_ns,
            ) != (
                after.st_dev,
                after.st_ino,
                after.st_size,
                after.st_mtime_ns,
            ):
                raise ValueError(f"published file changed while read: {relative}")
            return b"".join(chunks)
        finally:
            os.close(descriptor)
    finally:
        os.close(parent)


def _scan_publication_tree(
    root_descriptor: int, prefix: str = ""
) -> tuple[set[str], set[str]]:
    files: set[str] = set()
    directories: set[str] = set()
    for name in sorted(os.listdir(root_descriptor)):
        relative = f"{prefix}/{name}" if prefix else name
        metadata = os.stat(name, dir_fd=root_descriptor, follow_symlinks=False)
        if stat.S_ISLNK(metadata.st_mode):
            raise ValueError(f"publication tree contains symlink: {relative}")
        if stat.S_ISREG(metadata.st_mode):
            files.add(relative)
            continue
        if not stat.S_ISDIR(metadata.st_mode):
            raise ValueError(f"publication tree contains special file: {relative}")
        directories.add(relative)
        child = os.open(name, _directory_open_flags(), dir_fd=root_descriptor)
        try:
            child_files, child_directories = _scan_publication_tree(child, relative)
        finally:
            os.close(child)
        files.update(child_files)
        directories.update(child_directories)
    return files, directories


def _expected_program_paths() -> set[str]:
    return {
        _program_path(distance, rounds, name)
        for distance, rounds in GRID
        for name in PROGRAM_NAMES
    }


def _expected_publication_directories() -> set[str]:
    return {
        "programs",
        *(f"programs/d{distance}_r{rounds}" for distance, rounds in GRID),
    }


def _renameat2_noreplace(
    parent_descriptor: int, source: str, destination: str
) -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        raise RuntimeError("atomic no-replace directory rename is unavailable")
    renameat2.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    renameat2.restype = ctypes.c_int
    result = renameat2(
        parent_descriptor,
        os.fsencode(source),
        parent_descriptor,
        os.fsencode(destination),
        1,
    )
    if result == 0:
        return
    error = ctypes.get_errno()
    if error == errno.EEXIST:
        raise FileExistsError(
            f"publication refuses to overwrite existing output: {destination}"
        )
    raise OSError(error, os.strerror(error), destination)


def _strict_report_bytes(
    raw: bytes, *, programs: Mapping[str, bytes]
) -> dict[str, Any]:
    report = _strict_json_bytes(raw, subject="qualification_report.json")
    if raw != canonical_json_bytes(report):
        raise ValueError("qualification report is not canonical JSON")
    validate_qualification_report(report, programs=programs)
    return report


def build_publication_receipt(
    *,
    report: Mapping[str, Any],
    artifact_manifest: Mapping[str, str],
) -> dict[str, Any]:
    if set(artifact_manifest) != {
        *_expected_program_paths(),
        "qualification_report.json",
    }:
        raise ValueError("publication receipt artifact manifest layout mismatch")
    manifest = dict(artifact_manifest)
    report_program_manifest = report.get("artifact_manifest")
    observed_program_manifest = {
        path: manifest[path] for path in sorted(_expected_program_paths())
    }
    if (
        not isinstance(report_program_manifest, dict)
        or observed_program_manifest != report_program_manifest
    ):
        raise ValueError("publication receipt program/report manifest mismatch")
    report_sha256 = _sha256_bytes(canonical_json_bytes(dict(report)))
    if manifest["qualification_report.json"] != report_sha256:
        raise ValueError("publication receipt report hash mismatch")
    body = {
        "_schema": PUBLICATION_RECEIPT_SCHEMA,
        "preregistration_sha256": ACTIVE_PREREG_SHA256,
        "report_path": "qualification_report.json",
        "report_sha256": report_sha256,
        "artifact_manifest": manifest,
        "artifact_manifest_sha256": sha256_json(manifest),
    }
    return {**body, "content_sha256": sha256_json(body)}


def _validate_publication_receipt_at(
    receipt: Mapping[str, Any],
    *,
    root_descriptor: int,
    report: Mapping[str, Any],
) -> None:
    """Validate an exact bundle through one already-sealed directory FD."""

    files, directories = _scan_publication_tree(root_descriptor)
    expected_files = {
        *_expected_program_paths(),
        "qualification_report.json",
        "publication_receipt.json",
    }
    if files != expected_files or directories != _expected_publication_directories():
        raise ValueError("publication tree layout mismatch")

    raw_receipt = _read_regular_at(root_descriptor, "publication_receipt.json")
    disk_receipt = _strict_json_bytes(raw_receipt, subject="publication_receipt.json")
    if raw_receipt != canonical_json_bytes(disk_receipt):
        raise ValueError("publication receipt is not canonical JSON")
    if canonical_json_bytes(dict(receipt)) != raw_receipt:
        raise ValueError("supplied publication receipt differs from disk")

    programs = {
        relative: _read_regular_at(root_descriptor, relative)
        for relative in sorted(_expected_program_paths())
    }
    validate_program_artifacts(programs)
    report_raw = _read_regular_at(root_descriptor, "qualification_report.json")
    disk_report = _strict_report_bytes(report_raw, programs=programs)
    if canonical_json_bytes(dict(report)) != report_raw:
        raise ValueError("supplied qualification report differs from disk")

    artifact_manifest = {
        relative: _sha256_bytes(programs[relative]) for relative in sorted(programs)
    }
    artifact_manifest["qualification_report.json"] = _sha256_bytes(report_raw)
    expected_receipt = build_publication_receipt(
        report=disk_report,
        artifact_manifest=artifact_manifest,
    )
    if disk_receipt != expected_receipt:
        raise ValueError("publication receipt semantic identity mismatch")


def validate_publication_receipt(
    receipt: object,
    *,
    output_dir: Path,
    report: Mapping[str, Any],
) -> None:
    if not isinstance(receipt, dict) or set(receipt) != {
        "_schema",
        "preregistration_sha256",
        "report_path",
        "report_sha256",
        "artifact_manifest",
        "artifact_manifest_sha256",
        "content_sha256",
    }:
        raise ValueError("publication receipt schema mismatch")
    reject_floats(receipt)
    body = {key: value for key, value in receipt.items() if key != "content_sha256"}
    if receipt["content_sha256"] != sha256_json(body):
        raise ValueError("publication receipt content hash mismatch")
    if (
        receipt["_schema"] != PUBLICATION_RECEIPT_SCHEMA
        or receipt["preregistration_sha256"] != ACTIVE_PREREG_SHA256
        or receipt["report_path"] != "qualification_report.json"
    ):
        raise ValueError("publication receipt authority mismatch")
    manifest = receipt["artifact_manifest"]
    if not isinstance(manifest, dict) or receipt[
        "artifact_manifest_sha256"
    ] != sha256_json(manifest):
        raise ValueError("publication receipt manifest hash mismatch")
    expected_paths = {
        *_expected_program_paths(),
        "qualification_report.json",
    }
    if set(manifest) != expected_paths:
        raise ValueError("publication receipt manifest layout mismatch")
    root = _open_directory_no_symlinks(output_dir)
    try:
        _validate_publication_receipt_at(
            receipt, root_descriptor=root, report=report
        )
    finally:
        os.close(root)


def _publish_validated_bundle(
    output_dir: Path,
    *,
    programs: Mapping[str, bytes],
    report: Mapping[str, Any],
    observed_test_run: _ObservedTestRun,
) -> dict[str, Any]:
    """Stage, validate, and atomically no-replace one qualified bundle."""

    if type(observed_test_run) is not _ObservedTestRun:
        raise TypeError(
            "publication requires run_qualification_tests() evidence"
        )
    observed_receipt = observed_test_run._validated_receipt()
    provenance = report.get("provenance")
    if (
        not isinstance(provenance, Mapping)
        or provenance.get("test_run") != observed_receipt
    ):
        raise ValueError("publication report/test-run capability mismatch")

    output_absolute = Path(os.path.abspath(output_dir))
    if output_absolute.name in {"", ".", ".."}:
        raise ValueError("publication output must name one new child directory")
    parent_descriptor = _open_directory_no_symlinks(output_absolute.parent)
    target_name = output_absolute.name
    try:
        try:
            existing = os.stat(
                target_name, dir_fd=parent_descriptor, follow_symlinks=False
            )
        except FileNotFoundError:
            existing = None
        if existing is not None:
            if stat.S_ISLNK(existing.st_mode):
                raise ValueError("publication output root is a symlink")
            raise FileExistsError(
                f"publication refuses to overwrite existing output: {output_absolute}"
            )

        validate_program_artifacts(programs)
        validate_qualification_report(report, programs=programs)
        report_raw = canonical_json_bytes(report)
        stage_name = f".{target_name}.stage.{secrets.token_hex(16)}"
        os.mkdir(stage_name, mode=0o700, dir_fd=parent_descriptor)
        os.fsync(parent_descriptor)
        stage_descriptor = os.open(
            stage_name, _directory_open_flags(), dir_fd=parent_descriptor
        )
        stage_identity = os.fstat(stage_descriptor)
        renamed = False
        try:
            for relative in sorted(programs):
                _exclusive_write_at(stage_descriptor, relative, programs[relative])
            reloaded_programs = {
                relative: _read_regular_at(stage_descriptor, relative)
                for relative in sorted(programs)
            }
            validate_program_artifacts(reloaded_programs)

            _exclusive_write_at(
                stage_descriptor, "qualification_report.json", report_raw
            )
            reloaded_report = _strict_report_bytes(
                _read_regular_at(stage_descriptor, "qualification_report.json"),
                programs=reloaded_programs,
            )
            artifact_manifest = {
                relative: _sha256_bytes(reloaded_programs[relative])
                for relative in sorted(reloaded_programs)
            }
            artifact_manifest["qualification_report.json"] = _sha256_bytes(
                report_raw
            )
            receipt = build_publication_receipt(
                report=reloaded_report,
                artifact_manifest=artifact_manifest,
            )
            _exclusive_write_at(
                stage_descriptor,
                "publication_receipt.json",
                canonical_json_bytes(receipt),
            )
            os.fsync(stage_descriptor)

            _validate_publication_receipt_at(
                receipt,
                root_descriptor=stage_descriptor,
                report=reloaded_report,
            )
            _renameat2_noreplace(parent_descriptor, stage_name, target_name)
            renamed = True
            os.fsync(parent_descriptor)
            final_descriptor = os.open(
                target_name, _directory_open_flags(), dir_fd=parent_descriptor
            )
            try:
                final_identity = os.fstat(final_descriptor)
                if (final_identity.st_dev, final_identity.st_ino) != (
                    stage_identity.st_dev,
                    stage_identity.st_ino,
                ):
                    raise ValueError("publication root inode changed during rename")
                _validate_publication_receipt_at(
                    receipt,
                    root_descriptor=final_descriptor,
                    report=reloaded_report,
                )
            finally:
                os.close(final_descriptor)
            return receipt
        finally:
            os.close(stage_descriptor)
            if not renamed:
                stage_path = output_absolute.parent / stage_name
                try:
                    metadata = os.stat(
                        stage_name,
                        dir_fd=parent_descriptor,
                        follow_symlinks=False,
                    )
                except FileNotFoundError:
                    metadata = None
                if (
                    metadata is not None
                    and stat.S_ISDIR(metadata.st_mode)
                    and (metadata.st_dev, metadata.st_ino)
                    == (stage_identity.st_dev, stage_identity.st_ino)
                ):
                    shutil.rmtree(stage_path)
                    os.fsync(parent_descriptor)
    finally:
        os.close(parent_descriptor)


def publish_qualification_bundle(output_dir: Path) -> dict[str, Any]:
    """Official boundary: execute the frozen tests, build, then publish."""

    expected_output = REPO / PRODUCTION_OUTPUT_RELATIVE
    if Path(os.path.abspath(output_dir)) != expected_output:
        raise ValueError(
            f"official publication path must be {PRODUCTION_OUTPUT_RELATIVE}"
        )
    observed_test_run = run_qualification_tests()
    programs = build_program_artifacts()
    report = assemble_qualification_report(
        programs, observed_test_run=observed_test_run
    )
    return _publish_validated_bundle(
        output_dir,
        programs=programs,
        report=report,
        observed_test_run=observed_test_run,
    )


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="new final bundle directory; it must not already exist",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    receipt = publish_qualification_bundle(args.output_dir)
    print(canonical_json_bytes(receipt).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
