#!/usr/bin/env python3
"""Pure plan and timing algebra for the claim-ineligible development sweep.

This module owns no process launch and imports no scientific backend.  The
execution adapter consumes the exact heldout-shaped fixture semantics only as
reusable frozen input.  Every plan and aggregate produced here is explicitly a
``DEVELOPMENT_SWEEP`` diagnostic and is never formal held-out evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping, Sequence


SCHEMA_PREFIX = "error_coupling_simulator.external.gcapeps_finite_memory."
DEVELOPMENT_SWEEP = "DEVELOPMENT_SWEEP"
PLAN_SCHEMA = SCHEMA_PREFIX + "development_sweep_plan.v1"
REPORT_SCHEMA = SCHEMA_PREFIX + "development_sweep.v1"
CHILD_ARTIFACT_SCHEMA = SCHEMA_PREFIX + "development_sweep_child.v1"
FIXTURE_ARTIFACT_SCHEMA = SCHEMA_PREFIX + "development_sweep_fixture.v1"
TIMING_SCHEMA = SCHEMA_PREFIX + "layered_timing.v1"
TRAILER_SCHEMA = SCHEMA_PREFIX + "late_telemetry_trailer.v1"

CALIBRATION_ROUNDS = (4, 6, 8, 10, 12)
SLICE_ORDER = ("width", "rounds", "axis_family", "probability")
HELDOUT_SHAPED_SEED = int.from_bytes(
    hashlib.sha256(b"gcapeps-finite-memory-heldout-v1").digest()[:8],
    "big",
)

DENSE_REFERENCE = "dense_reference"
PLAIN_EVIDENCE = "plain_evidence"
GCAPEPS_EVIDENCE = "gcapeps_evidence"
PLAIN_PERFORMANCE = "plain_performance"
GCAPEPS_PERFORMANCE = "gcapeps_performance"
SDIM_COMPUTATION = "sdim_computation"
TERMINAL_COMPARATOR = "terminal_comparator"

MEASURED_ORDER = (
    ("plain", PLAIN_PERFORMANCE, 0),
    ("gcapeps", GCAPEPS_PERFORMANCE, 0),
    ("gcapeps", GCAPEPS_PERFORMANCE, 1),
    ("plain", PLAIN_PERFORMANCE, 1),
    ("plain", PLAIN_PERFORMANCE, 2),
    ("gcapeps", GCAPEPS_PERFORMANCE, 2),
)


def canonical_json_bytes(value: Mapping[str, Any] | Sequence[Any]) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def projection_sha256(value: Mapping[str, Any]) -> str:
    projection = dict(value)
    projection.pop("result_projection_sha256", None)
    return hashlib.sha256(canonical_json_bytes(projection)).hexdigest()


def _plain_int(
    value: Any,
    *,
    name: str,
    minimum: int = 0,
    maximum: int | None = None,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be a plain integer")
    if value < minimum or (maximum is not None and value > maximum):
        raise ValueError(f"{name} is outside its registered range")
    return value


@dataclass(frozen=True)
class DevelopmentLaunch:
    ordinal: int
    launch_id: str
    role: str
    input_id: int | None = None
    sample_kind: str | None = None
    sample_index: int | None = None

    def as_json(self) -> dict[str, Any]:
        return {
            "ordinal": self.ordinal,
            "launch_id": self.launch_id,
            "role": self.role,
            "input_id": self.input_id,
            "sample_kind": self.sample_kind,
            "sample_index": self.sample_index,
        }


@dataclass(frozen=True)
class DevelopmentCell:
    cell_index: int
    cell: tuple[int, int, int, int, int]
    development_case_id: str
    slice_membership: tuple[str, ...]
    run_blpensemble: bool
    launches: tuple[DevelopmentLaunch, ...]

    def as_json(self) -> dict[str, Any]:
        return {
            "cell_index": self.cell_index,
            "cell": list(self.cell),
            "development_case_id": self.development_case_id,
            "slice_membership": list(self.slice_membership),
            "run_blpensemble": self.run_blpensemble,
            "launches": [row.as_json() for row in self.launches],
        }


def _frozen_cells(
    rounds_star: int,
) -> list[tuple[tuple[int, int, int, int, int], tuple[str, ...]]]:
    rounds_star = _plain_int(rounds_star, name="rounds_star", minimum=1)
    if rounds_star not in CALIBRATION_ROUNDS:
        raise ValueError("rounds_star must be selected from the frozen grid")
    memberships: dict[tuple[int, int, int, int, int], set[str]] = {}

    def add(cell: tuple[int, int, int, int, int], member: str) -> None:
        memberships.setdefault(cell, set()).add(member)

    for width in (3, 5, 7):
        add((width, rounds_star, 3, 3, 4), "width")
    for rounds in (1, 2, 4, rounds_star):
        add((7, rounds, 3, 3, 4), "rounds")
    for axis_family in (1, 2, 3):
        add((7, rounds_star, axis_family, 3, 4), "axis_family")
    for numerator in (0, 1, 2, 3, 4):
        add((7, rounds_star, 3, numerator, 4), "probability")
    rows = [
        (
            cell,
            tuple(
                member
                for member in SLICE_ORDER
                if member in memberships[cell]
            ),
        )
        for cell in sorted(memberships)
    ]
    expected = 11 if rounds_star == 4 else 12
    if len(rows) != expected:
        raise AssertionError("development cell union cardinality drifted")
    return rows


def _build_development_plan_payload(
    *,
    gamma_index: int,
    rounds_star: int,
) -> dict[str, Any]:
    gamma_index = _plain_int(
        gamma_index, name="gamma_index", minimum=0, maximum=3
    )
    cells: list[DevelopmentCell] = []
    ordinal = 0
    for cell_index, (cell, membership) in enumerate(_frozen_cells(rounds_star)):
        prefix = f"dev-c{cell_index:02d}"
        launches: list[DevelopmentLaunch] = []

        def add(
            suffix: str,
            role: str,
            *,
            input_id: int | None = None,
            sample_kind: str | None = None,
            sample_index: int | None = None,
        ) -> None:
            nonlocal ordinal
            launches.append(
                DevelopmentLaunch(
                    ordinal=ordinal,
                    launch_id=f"{prefix}-{suffix}",
                    role=role,
                    input_id=input_id,
                    sample_kind=sample_kind,
                    sample_index=sample_index,
                )
            )
            ordinal += 1

        add("dense", DENSE_REFERENCE)
        add("plain-evidence-i1", PLAIN_EVIDENCE, input_id=1)
        add("plain-evidence-i2", PLAIN_EVIDENCE, input_id=2)
        add("gc-evidence-i1", GCAPEPS_EVIDENCE, input_id=1)
        add("gc-evidence-i2", GCAPEPS_EVIDENCE, input_id=2)
        add(
            "plain-warmup",
            PLAIN_PERFORMANCE,
            input_id=1,
            sample_kind="warmup",
        )
        add(
            "gc-warmup",
            GCAPEPS_PERFORMANCE,
            input_id=1,
            sample_kind="warmup",
        )
        for lane, role, sample_index in MEASURED_ORDER:
            add(
                f"{lane}-measured-{sample_index}",
                role,
                input_id=1,
                sample_kind="measured",
                sample_index=sample_index,
            )
        add("sdim", SDIM_COMPUTATION)
        add("comparator", TERMINAL_COMPARATOR)
        if len(launches) != 15:
            raise AssertionError("development cell workflow cardinality drifted")
        cells.append(
            DevelopmentCell(
                cell_index=cell_index,
                cell=cell,
                development_case_id=f"development-sweep-c{cell_index:02d}",
                slice_membership=membership,
                run_blpensemble="probability" in membership,
                launches=tuple(launches),
            )
        )
    payload: dict[str, Any] = {
        "schema": PLAN_SCHEMA,
        "run_partition": DEVELOPMENT_SWEEP,
        "formal_claim_eligible": False,
        "is_heldout_evidence": False,
        "execution_class": "claim_ineligible_development_diagnostic",
        "heldout_shaped_fixture_reuse_only": True,
        "transport_equivalent_to_B_CAL_or_B_HELD": False,
        "gamma_index": gamma_index,
        "rounds_star": rounds_star,
        "fixture_seed": HELDOUT_SHAPED_SEED,
        "max_bond": 32,
        "cutoff": 0,
        "cells": [cell.as_json() for cell in cells],
        "result_projection_sha256": "",
    }
    payload["result_projection_sha256"] = projection_sha256(payload)
    return payload


def build_development_plan(
    *,
    gamma_index: int,
    rounds_star: int,
) -> dict[str, Any]:
    """Build the exact frozen-cell development graph.

    The 15 launches per cell mirror the formal timing population but carry a
    distinct partition and namespace.  No amendment or formal result is an
    input to this function.
    """

    payload = _build_development_plan_payload(
        gamma_index=gamma_index,
        rounds_star=rounds_star,
    )
    validate_development_plan(payload)
    return payload


def validate_development_plan(plan: Mapping[str, Any]) -> None:
    if set(plan) != {
        "schema",
        "run_partition",
        "formal_claim_eligible",
        "is_heldout_evidence",
        "execution_class",
        "heldout_shaped_fixture_reuse_only",
        "transport_equivalent_to_B_CAL_or_B_HELD",
        "gamma_index",
        "rounds_star",
        "fixture_seed",
        "max_bond",
        "cutoff",
        "cells",
        "result_projection_sha256",
    }:
        raise ValueError("development plan has the wrong exact key set")
    if (
        plan["schema"] != PLAN_SCHEMA
        or plan["run_partition"] != DEVELOPMENT_SWEEP
        or plan["formal_claim_eligible"] is not False
        or plan["is_heldout_evidence"] is not False
        or plan["execution_class"]
        != "claim_ineligible_development_diagnostic"
        or plan["heldout_shaped_fixture_reuse_only"] is not True
        or plan["transport_equivalent_to_B_CAL_or_B_HELD"] is not False
        or plan["fixture_seed"] != HELDOUT_SHAPED_SEED
        or plan["max_bond"] != 32
        or plan["cutoff"] != 0
        or plan["result_projection_sha256"] != projection_sha256(plan)
    ):
        raise ValueError("development plan boundary or identity drifted")
    expected_plan = _build_development_plan_payload(
        gamma_index=plan["gamma_index"],
        rounds_star=plan["rounds_star"],
    )
    if canonical_json_bytes(plan) != canonical_json_bytes(expected_plan):
        raise ValueError("development plan differs from deterministic rebuild")


def validate_worker_trailer(
    trailer: Mapping[str, Any],
    *,
    core_bytes: bytes,
) -> None:
    if set(trailer) != {
        "schema",
        "core_byte_length",
        "core_sha256",
        "ru_maxrss_raw",
        "ru_maxrss_units",
        "sample_scope",
        "timing",
    }:
        raise ValueError("worker trailer has wrong keys")
    if (
        trailer["schema"] != TRAILER_SCHEMA
        or trailer["core_byte_length"] != len(core_bytes)
        or trailer["core_sha256"]
        != hashlib.sha256(core_bytes).hexdigest()
        or trailer["ru_maxrss_units"] != "KiB_on_linux"
        or trailer["sample_scope"] != "post_worker_root_pre_trailer"
    ):
        raise ValueError("worker trailer identity drifted")
    _plain_int(trailer["ru_maxrss_raw"], name="ru_maxrss_raw", minimum=0)
    timing = trailer["timing"]
    if not isinstance(timing, Mapping) or timing.get("schema") != TIMING_SCHEMA:
        raise ValueError("worker timing schema drifted")
