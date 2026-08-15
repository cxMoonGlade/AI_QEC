#!/usr/bin/env python3
"""Emit the neutral GCAPEPS finite-memory bond-32 fixture.

This owner is deliberately limited to deterministic experiment input.  It
does not import or execute Quimb, Stim, SDIM, GCAPEPS, or ECS.  Candidate and
reference workers consume the same chronological operation ledger, but remain
responsible for independently constructing and applying its matrices.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from typing import Any, Mapping, Sequence


FIXTURE_SCHEMA = (
    "error_coupling_simulator.external.gcapeps_finite_memory.fixture.v1"
)
SCRIPT_REVISION = "gcapeps-finite-memory-neutral-fixture-v1"
MASK_PAYLOAD_PREFIX = b"gcapeps-finite-memory-mask-v1\x00"
MASK_NAMESPACES = ("CARRIER", "BLPENSEMBLE")
RUN_PARTITIONS = ("CALIBRATION", "HELDOUT")
P_EVENT_DENOMINATOR = 4
ENSEMBLE_PATH_COUNT = 32
MAX_BOND = 32
AXIS_FAMILIES: dict[int, tuple[str, ...]] = {
    1: ("Z",),
    2: ("X", "Y"),
    3: ("X", "Y", "Z"),
}
AXIS_INDEX = {"X": 0, "Y": 1, "Z": 2}
GAMMA_GRID = (
    ("pi/11", "0x1.247426bd47de3p-2"),
    ("pi/9", "0x1.657184ae74487p-2"),
    ("pi/7", "0x1.cb91f3bbba140p-2"),
    ("pi/5", "0x1.41b2f769cf0e0p-1"),
)
CALIBRATION_ROUNDS = (4, 6, 8, 10, 12)
SLICE_ORDER = ("width", "rounds", "axis_family", "probability")
PULLBACK_REQUEST_KEYS = (
    "run_partition",
    "case_id",
    "input_id",
    "input_preparation_transcript_sha256",
    "shared_evolution_transcript_sha256",
    "round_prefix",
    "collision_ordinal",
    "round_index",
    "site_index",
    "axis_index",
    "physical_pauli_body",
)
HELDOUT_SEED = int.from_bytes(
    hashlib.sha256(b"gcapeps-finite-memory-heldout-v1").digest()[:8],
    "big",
)
_UINT64_MAX = (1 << 64) - 1


def canonical_json_bytes(value: Any) -> bytes:
    """Return the protocol's compact, ASCII-only canonical JSON bytes."""

    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    """Hash a value's canonical JSON bytes."""

    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def projection_sha256(value: Mapping[str, Any]) -> str:
    """Hash a result after removing exactly ``result_projection_sha256``."""

    projection = dict(value)
    projection.pop("result_projection_sha256", None)
    return canonical_sha256(projection)


def _with_projection_sha256(value: Mapping[str, Any]) -> dict[str, Any]:
    if "result_projection_sha256" in value:
        raise ValueError("projection input already has result_projection_sha256")
    result = dict(value)
    result["result_projection_sha256"] = canonical_sha256(result)
    return result


def _require_plain_int(
    name: str,
    value: Any,
    *,
    minimum: int = 0,
    maximum: int | None = None,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be a non-boolean integer")
    if value < minimum or (maximum is not None and value > maximum):
        upper = "" if maximum is None else f" and <= {maximum}"
        raise ValueError(f"{name} must be >= {minimum}{upper}")
    return value


def _require_uint64(name: str, value: Any) -> int:
    return _require_plain_int(name, value, maximum=_UINT64_MAX)


def _u64be(value: int) -> bytes:
    return _require_uint64("unsigned 64-bit value", value).to_bytes(8, "big")


def _gamma_metadata(gamma_index: int) -> dict[str, Any]:
    index = _require_plain_int(
        "gamma_index", gamma_index, maximum=len(GAMMA_GRID) - 1
    )
    label, gamma_hex = GAMMA_GRID[index]
    gamma = float.fromhex(gamma_hex)
    if not gamma > 0.0 or gamma.hex() != gamma_hex:
        raise RuntimeError("frozen gamma hex failed exact binary64 reconstruction")
    theta_hex = (-gamma).hex()
    if float.fromhex(theta_hex) != -gamma:
        raise RuntimeError("theta is not the exact binary64 sign flip of gamma")
    return {
        "gamma_index": index,
        "gamma_label": label,
        "gamma_float64_hex": gamma_hex,
        "theta_float64_hex": theta_hex,
    }


def event_payload(
    *,
    namespace: str,
    seed: int,
    mask_index: int,
    width: int,
    round_index: int,
    site_index: int,
) -> bytes:
    """Construct one frozen mask payload."""

    if namespace not in MASK_NAMESPACES:
        raise ValueError(f"unsupported mask namespace: {namespace!r}")
    width = _require_uint64("width", width)
    round_index = _require_plain_int(
        "round_index", round_index, minimum=1, maximum=_UINT64_MAX
    )
    site_index = _require_uint64("site_index", site_index)
    if width == 0 or site_index >= width:
        raise ValueError("site_index must address the nonempty fixture width")
    return b"".join(
        (
            MASK_PAYLOAD_PREFIX,
            namespace.encode("ascii"),
            b"\x00",
            _u64be(seed),
            _u64be(mask_index),
            _u64be(width),
            _u64be(round_index),
            _u64be(site_index),
        )
    )


def event_bit(
    *,
    namespace: str,
    seed: int,
    mask_index: int,
    width: int,
    round_index: int,
    site_index: int,
    p_event_numerator: int,
) -> bool:
    """Evaluate the structural-endpoint, exact-quarter event law."""

    numerator = _require_plain_int(
        "p_event_numerator", p_event_numerator, maximum=P_EVENT_DENOMINATOR
    )
    payload = event_payload(
        namespace=namespace,
        seed=seed,
        mask_index=mask_index,
        width=width,
        round_index=round_index,
        site_index=site_index,
    )
    if numerator == 0:
        return False
    if numerator == P_EVENT_DENOMINATOR:
        return True
    h64 = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
    return h64 < numerator * (1 << 62)


def _event_rows(
    *,
    namespace: str,
    seed: int,
    mask_index: int,
    width: int,
    rounds: int,
    p_event_numerator: int,
) -> tuple[list[dict[str, Any]], list[list[bool]]]:
    rows: list[dict[str, Any]] = []
    full_mask: list[list[bool]] = []
    for round_index in range(1, rounds + 1):
        round_mask: list[bool] = []
        for site_index in range(width):
            payload = event_payload(
                namespace=namespace,
                seed=seed,
                mask_index=mask_index,
                width=width,
                round_index=round_index,
                site_index=site_index,
            )
            digest = hashlib.sha256(payload).digest()
            h64 = int.from_bytes(digest[:8], "big")
            selected = event_bit(
                namespace=namespace,
                seed=seed,
                mask_index=mask_index,
                width=width,
                round_index=round_index,
                site_index=site_index,
                p_event_numerator=p_event_numerator,
            )
            rows.append(
                {
                    "event_row_index": len(rows),
                    "round_index": round_index,
                    "site_index": site_index,
                    "payload_hex": payload.hex(),
                    "payload_sha256": digest.hex(),
                    "h64": h64,
                    "event": selected,
                }
            )
            round_mask.append(selected)
        full_mask.append(round_mask)
    return rows, full_mask


def _matrix_entry(real_hex: str, imag_hex: str = "0x0.0p+0") -> dict[str, str]:
    float.fromhex(real_hex)
    float.fromhex(imag_hex)
    return {
        "real_float64_hex": real_hex,
        "imag_float64_hex": imag_hex,
    }


def _gate_definitions() -> dict[str, Any]:
    zero = _matrix_entry("0x0.0p+0")
    one = _matrix_entry("0x1.0000000000000p+0")
    minus_one = _matrix_entry("-0x1.0000000000000p+0")
    plus_i = _matrix_entry("0x0.0p+0", "0x1.0000000000000p+0")
    minus_i = _matrix_entry("0x0.0p+0", "-0x1.0000000000000p+0")
    half = "0x1.6a09e667f3bccp-1"
    plus_half = _matrix_entry(half)
    minus_half = _matrix_entry(f"-{half}")

    def matrix(
        basis_order: Sequence[str],
        shape: Sequence[int],
        entries: Sequence[Mapping[str, str]],
    ) -> dict[str, Any]:
        return {
            "kind": "explicit_row_major_complex128",
            "basis_order": list(basis_order),
            "shape": list(shape),
            "row_major_entries": [dict(entry) for entry in entries],
        }

    return {
        "H": matrix(
            ("|0>", "|1>"),
            (2, 2),
            (plus_half, plus_half, plus_half, minus_half),
        ),
        "S": matrix(
            ("|0>", "|1>"),
            (2, 2),
            (one, zero, zero, plus_i),
        ),
        "X": matrix(
            ("|0>", "|1>"),
            (2, 2),
            (zero, one, one, zero),
        ),
        "Y": matrix(
            ("|0>", "|1>"),
            (2, 2),
            (zero, minus_i, plus_i, zero),
        ),
        "Z": matrix(
            ("|0>", "|1>"),
            (2, 2),
            (one, zero, zero, minus_one),
        ),
        "CX": matrix(
            ("|00>", "|01>", "|10>", "|11>"),
            (4, 4),
            (
                one,
                zero,
                zero,
                zero,
                zero,
                one,
                zero,
                zero,
                zero,
                zero,
                zero,
                one,
                zero,
                zero,
                one,
                zero,
            ),
        ),
        "PAULI_ROTATION": {
            "kind": "formula",
            "formula": "cos(theta/2)*I-1j*sin(theta/2)*P",
            "theta_source": "operation.theta_float64_hex",
            "pauli_source": "operation.physical_pauli_body",
            "matrix_indices": "row_is_output_column_is_input",
        },
    }


def _clifford_operation(
    *,
    operation_index: int,
    round_index: int,
    layer_index: int,
    within_layer_index: int,
    gate_kind: str,
    targets: Sequence[int],
) -> dict[str, Any]:
    return {
        "operation_class": "clifford",
        "operation_index": operation_index,
        "round_index": round_index,
        "layer_index": layer_index,
        "within_layer_index": within_layer_index,
        "gate_kind": gate_kind,
        "targets": list(targets),
        "matrix_definition": gate_kind,
    }


def _physical_pauli_body(width: int, site_index: int, axis: str) -> str:
    body = ["I"] * (2 * width)
    body[site_index] = axis
    body[width + site_index] = axis
    return "".join(body)


def _collision_operation(
    *,
    operation_index: int,
    collision_ordinal: int,
    event_row_index: int,
    round_index: int,
    layer_index: int,
    within_layer_index: int,
    width: int,
    site_index: int,
    axis: str,
    gamma: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "operation_class": "collision_rotation",
        "operation_index": operation_index,
        "round_index": round_index,
        "layer_index": layer_index,
        "within_layer_index": within_layer_index,
        "gate_kind": "PAULI_ROTATION",
        "targets": [site_index, width + site_index],
        "matrix_definition": "PAULI_ROTATION",
        "collision_ordinal": collision_ordinal,
        "event_row_index": event_row_index,
        "site_index": site_index,
        "axis": axis,
        "axis_index": AXIS_INDEX[axis],
        "physical_pauli_body": _physical_pauli_body(width, site_index, axis),
        "gamma_float64_hex": gamma["gamma_float64_hex"],
        "theta_float64_hex": gamma["theta_float64_hex"],
        "rotation_convention": "exp(-0.5j*theta*P)",
    }


def _round_ledger(
    *,
    width: int,
    rounds: int,
    active_axes: Sequence[str],
    event_rows: Sequence[Mapping[str, Any]],
    gamma: Mapping[str, Any],
) -> list[dict[str, Any]]:
    event_by_locator = {
        (row["round_index"], row["site_index"]): row for row in event_rows
    }
    operation_index = 0
    collision_ordinal = 0
    ledger: list[dict[str, Any]] = []

    for round_index in range(1, rounds + 1):
        layer_specs: list[tuple[str, int | None, list[dict[str, Any]]]] = []

        h_sites = [
            site for site in range(width) if (site + round_index) % 2 == 0
        ]
        h_operations: list[dict[str, Any]] = []
        for within, site in enumerate(h_sites):
            h_operations.append(
                _clifford_operation(
                    operation_index=operation_index,
                    round_index=round_index,
                    layer_index=0,
                    within_layer_index=within,
                    gate_kind="H",
                    targets=(site,),
                )
            )
            operation_index += 1
        layer_specs.append(("system_h", (-round_index) % 2, h_operations))

        s_sites = [
            site for site in range(width) if (site + round_index) % 2 == 1
        ]
        s_operations: list[dict[str, Any]] = []
        for within, site in enumerate(s_sites):
            s_operations.append(
                _clifford_operation(
                    operation_index=operation_index,
                    round_index=round_index,
                    layer_index=1,
                    within_layer_index=within,
                    gate_kind="S",
                    targets=(site,),
                )
            )
            operation_index += 1
        layer_specs.append(("system_s", (1 - round_index) % 2, s_operations))

        first_parity = round_index % 2
        for parity_offset, parity in enumerate(
            (first_parity, 1 - first_parity)
        ):
            operations: list[dict[str, Any]] = []
            bonds = [site for site in range(width - 1) if site % 2 == parity]
            for within, site in enumerate(bonds):
                operations.append(
                    _clifford_operation(
                        operation_index=operation_index,
                        round_index=round_index,
                        layer_index=2 + parity_offset,
                        within_layer_index=within,
                        gate_kind="CX",
                        targets=(site, site + 1),
                    )
                )
                operation_index += 1
            layer_specs.append(
                (f"system_cx_parity_{parity}", parity, operations)
            )

        for parity_offset, parity in enumerate(
            (first_parity, 1 - first_parity)
        ):
            operations = []
            bonds = [site for site in range(width - 1) if site % 2 == parity]
            for within, site in enumerate(bonds):
                operations.append(
                    _clifford_operation(
                        operation_index=operation_index,
                        round_index=round_index,
                        layer_index=4 + parity_offset,
                        within_layer_index=within,
                        gate_kind="CX",
                        targets=(width + site + 1, width + site),
                    )
                )
                operation_index += 1
            layer_specs.append(
                (f"memory_reverse_cx_parity_{parity}", parity, operations)
            )

        collision_operations: list[dict[str, Any]] = []
        for site_index in range(width):
            event_row = event_by_locator[(round_index, site_index)]
            if not event_row["event"]:
                continue
            for axis in active_axes:
                collision_operations.append(
                    _collision_operation(
                        operation_index=operation_index,
                        collision_ordinal=collision_ordinal,
                        event_row_index=event_row["event_row_index"],
                        round_index=round_index,
                        layer_index=6,
                        within_layer_index=len(collision_operations),
                        width=width,
                        site_index=site_index,
                        axis=axis,
                        gamma=gamma,
                    )
                )
                operation_index += 1
                collision_ordinal += 1
        layer_specs.append(("event_conditioned_collisions", None, collision_operations))

        operations = [
            operation
            for _name, _parity, layer_operations in layer_specs
            for operation in layer_operations
        ]
        clifford_operations = [
            operation
            for operation in operations
            if operation["operation_class"] == "clifford"
        ]
        rotations = [
            operation
            for operation in operations
            if operation["operation_class"] == "collision_rotation"
        ]
        ledger.append(
            {
                "round_index": round_index,
                "layers": [
                    {
                        "layer_index": layer_index,
                        "layer_name": name,
                        "parity": parity,
                        "operation_indices": [
                            operation["operation_index"]
                            for operation in layer_operations
                        ],
                    }
                    for layer_index, (name, parity, layer_operations) in enumerate(
                        layer_specs
                    )
                ],
                "operations": operations,
                "clifford_operations": clifford_operations,
                "collision_rotations": rotations,
            }
        )
    return ledger


def _build_path(
    *,
    namespace: str,
    seed: int,
    mask_index: int,
    width: int,
    rounds: int,
    p_event_numerator: int,
    active_axes: Sequence[str],
    gamma: Mapping[str, Any],
    weight_numerator: int,
    weight_denominator: int,
) -> dict[str, Any]:
    event_rows, full_mask = _event_rows(
        namespace=namespace,
        seed=seed,
        mask_index=mask_index,
        width=width,
        rounds=rounds,
        p_event_numerator=p_event_numerator,
    )
    realized = sum(int(value) for row in full_mask for value in row)
    eligible = width * rounds
    round_ledger = _round_ledger(
        width=width,
        rounds=rounds,
        active_axes=active_axes,
        event_rows=event_rows,
        gamma=gamma,
    )
    return {
        "namespace": namespace,
        "mask_index": mask_index,
        "seed": seed,
        "weight_numerator": weight_numerator,
        "weight_denominator": weight_denominator,
        "event_rows": event_rows,
        "event_rows_sha256": canonical_sha256(event_rows),
        "full_mask": full_mask,
        "full_mask_sha256": canonical_sha256(full_mask),
        "eligible_collision_count": eligible,
        "realized_event_count": realized,
        "realized_event_fraction": {
            "numerator": realized,
            "denominator": eligible,
        },
        "active_axis_rotation_count": realized * len(active_axes),
        "mask_multiplicity": 1,
        "distinct_mask_count": 1,
        "round_ledger": round_ledger,
        "shared_evolution_transcript_sha256": canonical_sha256(round_ledger),
    }


def _assign_mask_multiplicity(paths: list[dict[str, Any]]) -> int:
    counts: dict[str, int] = {}
    for path in paths:
        digest = path["full_mask_sha256"]
        counts[digest] = counts.get(digest, 0) + 1
    distinct = len(counts)
    for path in paths:
        path["mask_multiplicity"] = counts[path["full_mask_sha256"]]
        path["distinct_mask_count"] = distinct
    return distinct


def _geometry(width: int) -> dict[str, Any]:
    system = list(range(width))
    memory = list(range(width, 2 * width))
    edges = sorted(
        [(site, site + 1) for site in range(width - 1)]
        + [(width + site, width + site + 1) for site in range(width - 1)]
        + [(site, width + site) for site in range(width)]
    )
    return {
        "rows": 2,
        "width": width,
        "n_qubits": 2 * width,
        "system_sites": system,
        "memory_sites": memory,
        "site_order": [
            {
                "site_id": site,
                "row": "system" if site < width else "memory",
                "row_index": site if site < width else site - width,
            }
            for site in range(2 * width)
        ],
        "graph_edges": [list(edge) for edge in edges],
    }


def _coordinate_convention(width: int) -> dict[str, Any]:
    return {
        "qubit_order": list(range(2 * width)),
        "system_axes": list(range(width)),
        "memory_axes": list(range(width, 2 * width)),
        "q0_bit_significance": "most_significant",
        "tensor_axis_order": "S_0..S_(w-1),M_0..M_(w-1)",
        "flat_index": "sum_q bit(q)*2**(2*w-1-q)",
        "two_qubit_basis": ["|00>", "|01>", "|10>", "|11>"],
        "matrix_indices": "row_is_output_column_is_input",
    }


def _mask_contract() -> dict[str, Any]:
    return {
        "version": "gcapeps-finite-memory-mask-v1",
        "payload_prefix_hex": MASK_PAYLOAD_PREFIX.hex(),
        "namespace_values": list(MASK_NAMESPACES),
        "integer_encoding": "unsigned_u64_big_endian",
        "payload_field_order": [
            "prefix",
            "namespace_ascii",
            "namespace_nul",
            "seed",
            "mask_index",
            "width",
            "round",
            "site",
        ],
        "digest": "SHA256",
        "h64": "uint64_big_endian(digest[0:8])",
        "p_event_denominator": P_EVENT_DENOMINATOR,
        "event_rule": (
            "q=0 structural_false; q=4 structural_true; "
            "otherwise h64 < q*2**62"
        ),
        "round_horizon_in_payload": False,
        "p_event_in_payload": False,
        "carrier_mask_index": 0,
        "blpensemble_mask_indices": list(range(ENSEMBLE_PATH_COUNT)),
        "blpensemble_equal_weight": {
            "numerator": 1,
            "denominator": ENSEMBLE_PATH_COUNT,
        },
    }


def _state_contract() -> dict[str, Any]:
    return {
        "initial_state_kind": "computational_basis_product",
        "joint_state_retained_across_rounds": True,
        "memory_row_policy": "never_discard_reset_or_recreate",
        "candidate_restart_between_rounds": False,
        "physical_round_indexing": "one_based",
        "checkpoint_zero": "initial_state_only",
        "unconditional_cross_row_gate": False,
    }


def _inputs(width: int) -> list[dict[str, Any]]:
    central = width // 2
    rows: list[dict[str, Any]] = []
    for input_id in (1, 2):
        dense_bits = [0] * (2 * width)
        gates: list[dict[str, Any]] = []
        if input_id == 2:
            dense_bits[central] = 1
            gates.append(
                {
                    "operation_index": 0,
                    "gate_kind": "X",
                    "targets": [central],
                    "matrix_definition": "X",
                    "is_physical_round_gate": False,
                }
            )
        transcript = {
            "schema": "gcapeps-finite-memory-input-preparation.v1",
            "input_id": input_id,
            "gates": gates,
        }
        rows.append(
            {
                "input_id": input_id,
                "label": "all_zero" if input_id == 1 else "central_system_x",
                "central_system_site": central,
                "dense_plain_initial_bits": dense_bits,
                "gc_residual_initial_bits": [0] * (2 * width),
                "gc_frame_preparation_gates": gates,
                "preparation_is_physical_round_gate": False,
                "input_preparation_transcript": transcript,
                "input_preparation_transcript_sha256": canonical_sha256(
                    transcript
                ),
            }
        )
    return rows


def fixture_case_id(
    *,
    run_partition: str,
    width: int,
    rounds: int,
    axis_family: int,
    p_event_numerator: int,
    gamma_index: int,
    seed: int,
) -> str:
    """Return the fixture-owned cell or calibration pair/seed id."""

    prefix = run_partition.lower()
    base = (
        f"w{width}-r{rounds}-a{axis_family}-"
        f"p{p_event_numerator}of{P_EVENT_DENOMINATOR}"
    )
    if run_partition == "CALIBRATION":
        return f"{prefix}-g{gamma_index}-s{seed}-{base}"
    return f"{prefix}-{base}"


def _pullback_requests(
    *,
    run_partition: str,
    case_id: str,
    inputs: Sequence[Mapping[str, Any]],
    carrier_path: Mapping[str, Any],
) -> list[dict[str, Any]]:
    shared_hash = carrier_path["shared_evolution_transcript_sha256"]
    requests: list[dict[str, Any]] = []
    for input_row in inputs:
        for round_row in carrier_path["round_ledger"]:
            for rotation in round_row["collision_rotations"]:
                requests.append(
                    {
                        "run_partition": run_partition,
                        "case_id": case_id,
                        "input_id": input_row["input_id"],
                        "input_preparation_transcript_sha256": input_row[
                            "input_preparation_transcript_sha256"
                        ],
                        "shared_evolution_transcript_sha256": shared_hash,
                        "round_prefix": rotation["round_index"],
                        "collision_ordinal": rotation["collision_ordinal"],
                        "round_index": rotation["round_index"],
                        "site_index": rotation["site_index"],
                        "axis_index": rotation["axis_index"],
                        "physical_pauli_body": rotation["physical_pauli_body"],
                    }
                )
    requests.sort(key=lambda row: tuple(row[key] for key in PULLBACK_REQUEST_KEYS))
    if any(set(row) != set(PULLBACK_REQUEST_KEYS) for row in requests):
        raise RuntimeError("pullback request key set drifted")
    keys = [tuple(row[key] for key in PULLBACK_REQUEST_KEYS) for row in requests]
    if len(keys) != len(set(keys)):
        raise RuntimeError("duplicate pullback request key")
    return requests


def _build_fixture_unvalidated(
    *,
    run_partition: str,
    width: int,
    rounds: int,
    axis_family: int,
    p_event_numerator: int,
    seed: int,
    gamma_index: int,
    run_blpensemble: bool,
) -> dict[str, Any]:
    if run_partition not in RUN_PARTITIONS:
        raise ValueError(f"run_partition must be one of {RUN_PARTITIONS}")
    width = _require_plain_int("width", width, minimum=1, maximum=7)
    if width not in (3, 5, 7):
        raise ValueError("width must be one of the frozen values 3, 5, 7")
    rounds = _require_plain_int("rounds", rounds, minimum=1)
    axis_family = _require_plain_int("axis_family", axis_family, minimum=1)
    if axis_family not in AXIS_FAMILIES:
        raise ValueError("axis_family must be one of 1, 2, 3")
    numerator = _require_plain_int(
        "p_event_numerator", p_event_numerator, maximum=P_EVENT_DENOMINATOR
    )
    seed = _require_uint64("seed", seed)
    if not isinstance(run_blpensemble, bool):
        raise TypeError("run_blpensemble must be a bool")
    if run_partition == "CALIBRATION":
        if (
            width != 7
            or rounds not in CALIBRATION_ROUNDS
            or axis_family != 3
            or numerator != 3
            or seed not in range(4)
        ):
            raise ValueError("calibration fixture identity is outside the frozen grid")
        if run_blpensemble:
            raise ValueError("calibration fixtures cannot materialize BLPENSEMBLE")
    else:
        if seed != HELDOUT_SEED:
            raise ValueError("held-out fixture must use the frozen held-out seed")
        if rounds not in {1, 2, *CALIBRATION_ROUNDS}:
            raise ValueError("held-out rounds are outside the frozen union")

    gamma = _gamma_metadata(gamma_index)
    active_axes = AXIS_FAMILIES[axis_family]
    case_id = fixture_case_id(
        run_partition=run_partition,
        width=width,
        rounds=rounds,
        axis_family=axis_family,
        p_event_numerator=numerator,
        gamma_index=gamma_index,
        seed=seed,
    )
    carrier_path = _build_path(
        namespace="CARRIER",
        seed=seed,
        mask_index=0,
        width=width,
        rounds=rounds,
        p_event_numerator=numerator,
        active_axes=active_axes,
        gamma=gamma,
        weight_numerator=1,
        weight_denominator=1,
    )
    inputs = _inputs(width)

    ensemble_paths: list[dict[str, Any]] = []
    if run_blpensemble:
        for mask_index in range(ENSEMBLE_PATH_COUNT):
            ensemble_paths.append(
                _build_path(
                    namespace="BLPENSEMBLE",
                    seed=seed,
                    mask_index=mask_index,
                    width=width,
                    rounds=rounds,
                    p_event_numerator=numerator,
                    active_axes=active_axes,
                    gamma=gamma,
                    weight_numerator=1,
                    weight_denominator=ENSEMBLE_PATH_COUNT,
                )
            )
    ensemble_distinct = _assign_mask_multiplicity(ensemble_paths)

    checkpoints = sorted({0, 1, 2, 4, rounds}.intersection(range(rounds + 1)))
    parameters = {
        "width": width,
        "rounds": rounds,
        "axis_family": axis_family,
        "active_axes": list(active_axes),
        "p_event_numerator": numerator,
        "p_event_denominator": P_EVENT_DENOMINATOR,
        "seed": seed,
        **gamma,
        "max_bond": MAX_BOND,
    }
    result = {
        "schema": FIXTURE_SCHEMA,
        "script_revision": SCRIPT_REVISION,
        "fixture_id": case_id,
        "run_partition": run_partition,
        "case_id": case_id,
        "claim_boundary": (
            "bounded pure-state 2xw persistent-memory unitary carrier fixture; "
            "not a QEC Record, calibrated device model, or generic PEPS claim"
        ),
        "geometry": _geometry(width),
        "coordinate_convention": _coordinate_convention(width),
        "mask_contract": _mask_contract(),
        "state_contract": _state_contract(),
        "gate_definitions": _gate_definitions(),
        "parameters": parameters,
        "inputs": inputs,
        "checkpoints": checkpoints,
        "carrier_path": carrier_path,
        "blpensemble": {
            "enabled": run_blpensemble,
            "registered_path_count": ENSEMBLE_PATH_COUNT,
            "path_count": len(ensemble_paths),
            "weight_numerator": 1,
            "weight_denominator": ENSEMBLE_PATH_COUNT,
            "distinct_mask_count": ensemble_distinct,
            "paths": ensemble_paths,
        },
        "sdim_pullback_requests": _pullback_requests(
            run_partition=run_partition,
            case_id=case_id,
            inputs=inputs,
            carrier_path=carrier_path,
        ),
    }
    return _with_projection_sha256(result)


def build_fixture(
    *,
    run_partition: str,
    width: int,
    rounds: int,
    axis_family: int,
    p_event_numerator: int,
    seed: int,
    gamma_index: int,
    run_blpensemble: bool,
) -> dict[str, Any]:
    """Build one deterministic neutral fixture core."""

    return _build_fixture_unvalidated(
        run_partition=run_partition,
        width=width,
        rounds=rounds,
        axis_family=axis_family,
        p_event_numerator=p_event_numerator,
        seed=seed,
        gamma_index=gamma_index,
        run_blpensemble=run_blpensemble,
    )


def validate_fixture(fixture: Mapping[str, Any]) -> str:
    """Validate the exact schema/content and return its projection hash."""

    if not isinstance(fixture, Mapping):
        raise TypeError("fixture must be a mapping")
    expected_top = {
        "schema",
        "script_revision",
        "fixture_id",
        "run_partition",
        "case_id",
        "claim_boundary",
        "geometry",
        "coordinate_convention",
        "mask_contract",
        "state_contract",
        "gate_definitions",
        "parameters",
        "inputs",
        "checkpoints",
        "carrier_path",
        "blpensemble",
        "sdim_pullback_requests",
        "result_projection_sha256",
    }
    if set(fixture) != expected_top:
        raise ValueError("fixture top-level key set is not exact")
    parameters = fixture.get("parameters")
    ensemble = fixture.get("blpensemble")
    if not isinstance(parameters, Mapping) or not isinstance(ensemble, Mapping):
        raise ValueError("fixture parameters and blpensemble must be mappings")
    try:
        expected = _build_fixture_unvalidated(
            run_partition=fixture["run_partition"],
            width=parameters["width"],
            rounds=parameters["rounds"],
            axis_family=parameters["axis_family"],
            p_event_numerator=parameters["p_event_numerator"],
            seed=parameters["seed"],
            gamma_index=parameters["gamma_index"],
            run_blpensemble=ensemble["enabled"],
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("fixture cannot be reconstructed from its identity") from error
    if canonical_json_bytes(fixture) != canonical_json_bytes(expected):
        raise ValueError("fixture differs from deterministic reconstruction")
    digest = projection_sha256(fixture)
    if fixture["result_projection_sha256"] != digest:
        raise ValueError("fixture result_projection_sha256 mismatch")
    return digest


def build_heldout_cells(rounds_star: int) -> list[dict[str, Any]]:
    """Build the exact-deduplicated, lexicographically sorted held-out union."""

    rounds_star = _require_plain_int("rounds_star", rounds_star, minimum=1)
    if rounds_star not in CALIBRATION_ROUNDS:
        raise ValueError("rounds_star must be selected from the calibration grid")
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

    rows: list[dict[str, Any]] = []
    for cell in sorted(memberships):
        width, rounds, axis_family, numerator, denominator = cell
        ordered_membership = [
            member for member in SLICE_ORDER if member in memberships[cell]
        ]
        rows.append(
            {
                "cell": list(cell),
                "case_id": fixture_case_id(
                    run_partition="HELDOUT",
                    width=width,
                    rounds=rounds,
                    axis_family=axis_family,
                    p_event_numerator=numerator,
                    gamma_index=0,
                    seed=HELDOUT_SEED,
                ),
                "slice_membership": ordered_membership,
                "run_blpensemble": "probability" in ordered_membership,
            }
        )
    expected_count = 11 if rounds_star == 4 else 12
    if len(rows) != expected_count:
        raise RuntimeError("held-out cell union cardinality drifted")
    return rows


def heldout_cell_list_sha256(rounds_star: int) -> str:
    """Hash the complete canonical held-out cell list."""

    return canonical_sha256(build_heldout_cells(rounds_star))


def materialize_heldout_fixtures(
    *,
    rounds_star: int,
    gamma_index: int,
) -> dict[str, Any]:
    """Materialize the amendment-bound held-out list and all neutral cores."""

    cells = build_heldout_cells(rounds_star)
    fixtures = []
    for row in cells:
        width, rounds, axis_family, numerator, denominator = row["cell"]
        if denominator != P_EVENT_DENOMINATOR:
            raise RuntimeError("held-out denominator drifted")
        fixtures.append(
            build_fixture(
                run_partition="HELDOUT",
                width=width,
                rounds=rounds,
                axis_family=axis_family,
                p_event_numerator=numerator,
                seed=HELDOUT_SEED,
                gamma_index=gamma_index,
                run_blpensemble=row["run_blpensemble"],
            )
        )
    materialization = {
        "rounds_star": rounds_star,
        "gamma_index": gamma_index,
        "heldout_seed": HELDOUT_SEED,
        "cell_list": cells,
        "cell_list_sha256": canonical_sha256(cells),
        "fixture_projection_sha256s": [
            fixture["result_projection_sha256"] for fixture in fixtures
        ],
        "fixtures": fixtures,
    }
    materialization["heldout_fixture_sha256"] = canonical_sha256(materialization)
    return materialization


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-partition", choices=RUN_PARTITIONS, required=True)
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--rounds", type=int, required=True)
    parser.add_argument("--axis-family", type=int, choices=tuple(AXIS_FAMILIES), required=True)
    parser.add_argument("--p-event-numerator", type=int, choices=range(5), required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--gamma-index", type=int, choices=range(len(GAMMA_GRID)), required=True)
    parser.add_argument("--run-blpensemble", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Emit exactly one canonical fixture core to stdout, without a newline."""

    args = _parse_args(argv)
    fixture = build_fixture(
        run_partition=args.run_partition,
        width=args.width,
        rounds=args.rounds,
        axis_family=args.axis_family,
        p_event_numerator=args.p_event_numerator,
        seed=args.seed,
        gamma_index=args.gamma_index,
        run_blpensemble=args.run_blpensemble,
    )
    validate_fixture(fixture)
    sys.stdout.buffer.write(canonical_json_bytes(fixture))
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
