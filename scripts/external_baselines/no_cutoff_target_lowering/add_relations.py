"""Static dynamic-ADD relation specifications bound to exact pair kernels.

This module deliberately has no ADD root, node table, advance operation,
sparse-state iterator, or target metric.
"""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import hashlib
from itertools import product
from typing import Any, Iterator

from scripts.external_baselines.no_cutoff_minimal_exact_owners.model import (
    I,
    ONE,
    Qsqrt2i,
)

from .model import (
    ADD_SCHEMA,
    StaticArtifact,
    canonical_json_bytes,
    sha256_json,
    validate_static_envelope,
)


CANONICAL_ADD_POLICY = {
    "terminal_interning": "exact_scalar",
    "node_key": "(level,low,high)",
    "equal_child_reduction": True,
    "unique_table": "exact",
    "reachable_gc": "after_each_advance",
    "canonical_renumber": "terminals_then_descending_levels",
    "zero_terminal": "exactly_one",
    "weighted_edges": "forbidden",
    "tolerance": "forbidden",
}


_TINY_ZERO = [[0, 1], [0, 1], [0, 1], [0, 1]]


def _tiny_event(
    operation_id: str,
    kind: str,
    qubits: tuple[int, ...] = (),
    *,
    raw_output: int | None = None,
    rec_operands: tuple[int, ...] = (),
    record_kind: str | None = None,
    fixed_branch: int | None = None,
) -> dict[str, Any]:
    return {
        "operation_id": operation_id,
        "kind": kind,
        "qubits": [{"dense_ordinal": qubit} for qubit in qubits],
        "raw_output": raw_output,
        "rec_operands": [
            {"absolute_raw_ordinal": raw, "operand_ordinal": ordinal}
            for ordinal, raw in enumerate(rec_operands)
        ],
        "record_output": (
            None if record_kind is None else {"kind": record_kind, "ordinal": 0}
        ),
        "fixed_branch": fixed_branch,
    }


def _tiny_witness_definition(
    witness_id: str,
) -> tuple[int, bool, list[dict[str, Any]]]:
    """Return the frozen finite relation witness, never an executable state."""

    if witness_id == "P1":
        return 1, False, [
            _tiny_event("identity", "COORD_MARKER"),
            _tiny_event("H", "H", (0,)),
            _tiny_event("COHERENT_Z", "COHERENT_Z", (0,)),
            _tiny_event("R", "RESET", (0,)),
            _tiny_event("M(b=0)", "M", (0,), raw_output=0, fixed_branch=0),
            _tiny_event("M(b=1)", "M", (0,), raw_output=0, fixed_branch=1),
            _tiny_event("MR(b=0)", "MR", (0,), raw_output=0, fixed_branch=0),
            _tiny_event("MR(b=1)", "MR", (0,), raw_output=0, fixed_branch=1),
        ]
    if witness_id == "P2":
        return 2, False, [
            _tiny_event("H(q=0)", "H", (0,)),
            _tiny_event("H(q=1)", "H", (1,)),
            _tiny_event("CX(control=0,target=1)", "CX", (0, 1)),
            _tiny_event("CX(control=1,target=0)", "CX", (1, 0)),
        ]

    operations: dict[str, tuple[tuple[Any, ...], ...]] = {
        "T1": (
            ("R(0)", "RESET", (0,), None, (), None),
            ("H(0)", "H", (0,), None, (), None),
            ("M(0)", "M", (0,), 0, (), None),
            ("D0(raw0)", "DETECTOR_APPEND", (), None, (0,), "DETECTOR"),
            ("O0(raw0)", "OBSERVABLE_XOR", (), None, (0,), None),
            ("FINALIZE", "FINALIZE_RECORD", (), None, (), "OBSERVABLE"),
        ),
        "T2": (
            ("R(0)", "RESET", (0,), None, (), None),
            ("H(0)", "H", (0,), None, (), None),
            ("MR(0)", "MR", (0,), 0, (), None),
            ("M(0)", "M", (0,), 1, (), None),
            (
                "D0(raw0 xor raw1)",
                "DETECTOR_APPEND",
                (),
                None,
                (0, 1),
                "DETECTOR",
            ),
            ("O0(raw1)", "OBSERVABLE_XOR", (), None, (1,), None),
            ("FINALIZE", "FINALIZE_RECORD", (), None, (), "OBSERVABLE"),
        ),
        "T3": (
            ("R(0)", "RESET", (0,), None, (), None),
            ("H(0)", "H", (0,), None, (), None),
            ("U_m(0)#0", "COHERENT_Z", (0,), None, (), None),
            ("H(0)#1", "H", (0,), None, (), None),
            ("U_m(0)#1", "COHERENT_Z", (0,), None, (), None),
            ("H(0)#2", "H", (0,), None, (), None),
            ("M(0)", "M", (0,), 0, (), None),
            ("D0(raw0)", "DETECTOR_APPEND", (), None, (0,), "DETECTOR"),
            ("O0(raw0)", "OBSERVABLE_XOR", (), None, (0,), None),
            ("FINALIZE", "FINALIZE_RECORD", (), None, (), "OBSERVABLE"),
        ),
        "T4": (
            ("R(0)", "RESET", (0,), None, (), None),
            ("R(1)", "RESET", (1,), None, (), None),
            ("H(0)", "H", (0,), None, (), None),
            ("CX(0,1)", "CX", (0, 1), None, (), None),
            ("M(0)", "M", (0,), 0, (), None),
            ("M(1)", "M", (1,), 1, (), None),
            (
                "D0(raw0 xor raw1)",
                "DETECTOR_APPEND",
                (),
                None,
                (0, 1),
                "DETECTOR",
            ),
            ("O0(raw1)", "OBSERVABLE_XOR", (), None, (1,), None),
            ("FINALIZE", "FINALIZE_RECORD", (), None, (), "OBSERVABLE"),
        ),
    }
    if witness_id not in operations:
        raise ValueError("tiny ADD witness must be one of P1, P2, T1, T2, T3, T4")
    events = [
        _tiny_event(
            operation_id,
            kind,
            qubits,
            raw_output=raw_output,
            rec_operands=rec_operands,
            record_kind=record_kind,
        )
        for operation_id, kind, qubits, raw_output, rec_operands, record_kind in operations[
            witness_id
        ]
    ]
    return (1 if witness_id != "T4" else 2), True, events


def _tiny_q_from_data(data: object) -> Qsqrt2i:
    if not isinstance(data, list) or len(data) != 4:
        raise ValueError("tiny relation coefficient has the wrong exact shape")
    coordinates: list[Fraction] = []
    for coordinate in data:
        if (
            not isinstance(coordinate, list)
            or len(coordinate) != 2
            or any(type(value) is not int for value in coordinate)
        ):
            raise ValueError("tiny relation coefficient coordinate is invalid")
        coordinates.append(Fraction(coordinate[0], coordinate[1]))
    return Qsqrt2i(*coordinates)


def _tiny_i_power(exponent: int) -> Qsqrt2i:
    result = ONE
    for _ in range(exponent % 4):
        result = result * I
    return result


def _tiny_pauli_label(label: str, qubit: int, width: int) -> dict[str, Any]:
    from .pair import _signed_row

    coordinates = {"I": (0, 0), "X": (1, 0), "Y": (1, 1), "Z": (0, 1)}
    if label not in coordinates or not 0 <= qubit < width:
        raise ValueError("tiny relation Pauli action is invalid")
    x = [0] * width
    z = [0] * width
    x[qubit], z[qubit] = coordinates[label]
    return _signed_row(x, z)


def _tiny_apply_owner_action(
    pauli: dict[str, Any], action: dict[str, Any]
) -> dict[str, Any]:
    from .pair import _conjugate_cx, _conjugate_h, _multiply_rows

    opcode = action["opcode"]
    qubits = action["qubits"]
    if opcode == "IDENTITY":
        return deepcopy(pauli)
    if opcode == "CONJUGATE_H":
        return _conjugate_h(pauli, qubits[0])
    if opcode == "CONJUGATE_CX":
        return _conjugate_cx(pauli, qubits[0], qubits[1])
    if opcode in {"LEFT_PREPEND_Z", "LEFT_PREPEND_PAULI"}:
        label = "Z" if opcode == "LEFT_PREPEND_Z" else action["parameters"][0]
        return _multiply_rows(
            _tiny_pauli_label(label, qubits[0], len(pauli["x"])), pauli
        )
    if opcode in {"RIGHT_APPEND_Z", "RIGHT_APPEND_PAULI"}:
        label = "Z" if opcode == "RIGHT_APPEND_Z" else action["parameters"][0]
        return _multiply_rows(
            pauli, _tiny_pauli_label(label, qubits[0], len(pauli["x"]))
        )
    raise ValueError(f"unsupported tiny pair action {opcode!r}")


def _tiny_initial_owner_basis(width: int) -> dict[str, Any]:
    from .pair import build_signed_rref_basis

    stabilizers = []
    for qubit in range(width):
        x = [0] * width
        z = [0] * width
        z[qubit] = 1
        stabilizers.append({"x": x, "z": z, "phase_mod4": 0})
    return build_signed_rref_basis(stabilizers)


def _tiny_advance_owner_basis(
    basis: dict[str, Any], event: dict[str, Any]
) -> dict[str, Any]:
    from .pair import _conjugate_cx, _conjugate_h, build_signed_rref_basis

    stabilizers = deepcopy(basis["stabilizers"])
    dense = [entry["dense_ordinal"] for entry in event["qubits"]]
    if event["kind"] == "H":
        stabilizers = [_conjugate_h(row, dense[0]) for row in stabilizers]
    elif event["kind"] == "CX":
        stabilizers = [
            _conjugate_cx(row, dense[0], dense[1]) for row in stabilizers
        ]
    return build_signed_rref_basis(stabilizers)


def _tiny_codec_fields(
    width: int,
    *,
    observable_live: bool,
    live_raw: list[int],
    record_width: int,
) -> list[str]:
    fields: list[str] = []
    for side in ("L", "R"):
        fields.extend(f"{side}.x[{qubit}]" for qubit in range(width))
        fields.extend(f"{side}.z[{qubit}]" for qubit in range(width))
    fields.append("latent_m")
    if observable_live:
        fields.append("observable_0_accumulator")
    fields.extend(f"live_raw[{raw}]" for raw in live_raw)
    fields.extend(f"record[{ordinal}]" for ordinal in range(record_width))
    return fields


def _tiny_pivot_fields(basis: dict[str, Any], width: int) -> set[str]:
    result: set[str] = set()
    for side in ("L", "R"):
        for pivot in basis["pivots"]:
            axis = "x" if pivot < width else "z"
            qubit = pivot if pivot < width else pivot - width
            result.add(f"{side}.{axis}[{qubit}]")
    return result


def _tiny_assignment(fields: list[str], bits: list[int]) -> dict[str, int]:
    return dict(zip(fields, bits, strict=True))


def _tiny_pair_from_assignment(
    assignment: dict[str, int], side: str, width: int
) -> dict[str, Any]:
    return {
        "x": [assignment[f"{side}.x[{q}]"] for q in range(width)],
        "z": [assignment[f"{side}.z[{q}]"] for q in range(width)],
    }


def _tiny_raw_ordinal(field: str) -> int:
    return int(field.removeprefix("live_raw[").removesuffix("]"))


def _tiny_record_ordinal(field: str) -> int:
    return int(field.removeprefix("record[").removesuffix("]"))


def _tiny_expected_classical_output(
    event: dict[str, Any],
    input_assignment: dict[str, int],
    output_fields: list[str],
    *,
    branch: int | None,
) -> dict[str, int]:
    expected: dict[str, int] = {}
    operands = [
        input_assignment[f"live_raw[{entry['absolute_raw_ordinal']}]" ]
        for entry in event["rec_operands"]
    ]
    parity = sum(operands) % 2
    input_record_width = sum(field.startswith("record[") for field in input_assignment)
    for field in output_fields:
        if field.startswith(("L.", "R.")):
            continue
        if field == "latent_m":
            expected[field] = input_assignment[field]
        elif field == "observable_0_accumulator":
            accumulator = input_assignment["observable_0_accumulator"]
            expected[field] = (
                accumulator ^ parity
                if event["kind"] == "OBSERVABLE_XOR"
                else accumulator
            )
        elif field.startswith("live_raw["):
            raw = _tiny_raw_ordinal(field)
            if raw == event["raw_output"]:
                if branch not in (0, 1):
                    raise ValueError("raw-producing component has no branch")
                expected[field] = branch
            else:
                expected[field] = input_assignment[field]
        elif field.startswith("record["):
            ordinal = _tiny_record_ordinal(field)
            if ordinal < input_record_width:
                expected[field] = input_assignment[field]
            elif event["kind"] == "DETECTOR_APPEND":
                expected[field] = parity
            elif event["kind"] == "FINALIZE_RECORD":
                expected[field] = input_assignment["observable_0_accumulator"]
            else:
                raise ValueError("tiny relation created an unexplained Record bit")
        else:
            raise ValueError(f"unknown tiny codec field {field!r}")
    return expected


def _tiny_owner_transition_map(
    *,
    event: dict[str, Any],
    width: int,
    input_fields: list[str],
    input_bits: list[int],
    output_fields: list[str],
    output_basis: dict[str, Any],
) -> dict[tuple[int, ...], Qsqrt2i]:
    from .pair import _kernel_rows, canonicalize_pauli_against_basis

    input_assignment = _tiny_assignment(input_fields, input_bits)
    latent = -1 if input_assignment["latent_m"] == 0 else 1
    left_input = _tiny_pair_from_assignment(input_assignment, "L", width)
    right_input = _tiny_pair_from_assignment(input_assignment, "R", width)
    rows = _kernel_rows(event)
    fixed_branch = event["fixed_branch"]
    if fixed_branch is not None:
        rows = [
            row
            for row in rows
            if row["branch"]
            and row["branch"][0] == {"name": "b", "value": fixed_branch}
        ]

    result: dict[tuple[int, ...], Qsqrt2i] = {}
    for component in rows:
        left_signed = _tiny_apply_owner_action(
            {**deepcopy(left_input), "phase_mod4": 0}, component["left_action"]
        )
        right_signed = _tiny_apply_owner_action(
            {**deepcopy(right_input), "phase_mod4": 0}, component["right_action"]
        )
        left_reduced = canonicalize_pauli_against_basis(
            {"x": left_signed["x"], "z": left_signed["z"]},
            output_basis,
            side="ket",
        )
        right_reduced = canonicalize_pauli_against_basis(
            {"x": right_signed["x"], "z": right_signed["z"]},
            output_basis,
            side="bra",
        )
        multiplier_data = next(
            item["coefficient"]
            for item in component["multiplier_by_latent"]
            if item["latent_m"] == latent
        )
        phase = (
            left_signed["phase_mod4"]
            + left_reduced["coefficient_phase_mod4"]
            + right_signed["phase_mod4"]
            + right_reduced["coefficient_phase_mod4"]
        )
        coefficient = _tiny_q_from_data(multiplier_data) * _tiny_i_power(phase)
        branch = next(
            (
                item["value"]
                for item in component["branch"]
                if item["name"] == "b"
            ),
            None,
        )
        expected = _tiny_expected_classical_output(
            event, input_assignment, output_fields, branch=branch
        )
        left_rep = left_reduced["representative"]
        right_rep = right_reduced["representative"]
        for side, representative in (("L", left_rep), ("R", right_rep)):
            for qubit in range(width):
                expected[f"{side}.x[{qubit}]"] = representative["x"][qubit]
                expected[f"{side}.z[{qubit}]"] = representative["z"][qubit]
        output = tuple(expected[field] for field in output_fields)
        result[output] = result.get(output, Qsqrt2i.rational(0)) + coefficient
    return result


def _tiny_owner_plans(
    witness_id: str,
) -> tuple[int, list[dict[str, Any]]]:
    width, sequential, events = _tiny_witness_definition(witness_id)
    initial_basis = _tiny_initial_owner_basis(width)
    producer: dict[int, int] = {}
    last_use: dict[int, int] = {}
    for event_index, event in enumerate(events):
        if event["raw_output"] is not None:
            producer[event["raw_output"]] = event_index
        for operand in event["rec_operands"]:
            last_use[operand["absolute_raw_ordinal"]] = event_index

    plans: list[dict[str, Any]] = []
    running_basis = initial_basis
    record_width = 0
    for operation_index, event in enumerate(events):
        input_basis = running_basis if sequential else initial_basis
        output_basis = _tiny_advance_owner_basis(input_basis, event)
        if sequential:
            input_after = operation_index - 1
            input_live_raw = sorted(
                raw
                for raw, produced_at in producer.items()
                if produced_at <= input_after and last_use.get(raw, -1) > input_after
            )
            input_record_width = record_width
            if event["record_output"] is not None:
                record_width += 1
            output_live_raw = sorted(
                raw
                for raw, produced_at in producer.items()
                if produced_at <= operation_index
                and last_use.get(raw, -1) > operation_index
            )
            input_fields = _tiny_codec_fields(
                width,
                observable_live=True,
                live_raw=input_live_raw,
                record_width=input_record_width,
            )
            output_fields = _tiny_codec_fields(
                width,
                observable_live=operation_index < len(events) - 1,
                live_raw=output_live_raw,
                record_width=record_width,
            )
            running_basis = output_basis
        else:
            input_fields = _tiny_codec_fields(
                width, observable_live=True, live_raw=[], record_width=0
            )
            output_fields = list(input_fields)
        plans.append(
            {
                "operation_index": operation_index,
                "event": event,
                "input_basis": input_basis,
                "output_basis": output_basis,
                "input_fields": input_fields,
                "output_fields": output_fields,
                "input_pivots": _tiny_pivot_fields(input_basis, width),
                "output_pivots": _tiny_pivot_fields(output_basis, width),
            }
        )
    return width, plans


def tiny_add_truth_row_count(witness_id: str) -> int:
    """Return the literal size of the frozen input x output truth relation."""

    _, plans = _tiny_owner_plans(witness_id)
    return sum(
        1 << (len(plan["input_fields"]) + len(plan["output_fields"]))
        for plan in plans
    )


def iter_tiny_add_truth_rows(witness_id: str) -> Iterator[dict[str, Any]]:
    """Stream every finite input/output code pair without building an ADD root.

    The iterator is deliberately the full Cartesian product, including pairs
    for which either one-sided codec is invalid.  Such pairs totalize to exact
    structural zero.  Streaming is essential: the frozen T4 witness contains
    44,040,192 rows and must never be accumulated as one Python list.
    """

    width, plans = _tiny_owner_plans(witness_id)
    for plan in plans:
        operation_index = plan["operation_index"]
        event = plan["event"]
        input_fields = plan["input_fields"]
        output_fields = plan["output_fields"]
        input_pivots = plan["input_pivots"]
        output_pivots = plan["output_pivots"]
        output_codes = tuple(product((0, 1), repeat=len(output_fields)))
        output_validity = tuple(
            all(
                bit == 0
                for field, bit in zip(output_fields, bits, strict=True)
                if field in output_pivots
            )
            for bits in output_codes
        )
        for raw_input_bits in product((0, 1), repeat=len(input_fields)):
            input_bits = list(raw_input_bits)
            input_valid = all(
                bit == 0
                for field, bit in zip(input_fields, input_bits, strict=True)
                if field in input_pivots
            )
            transition = (
                _tiny_owner_transition_map(
                    event=event,
                    width=width,
                    input_fields=input_fields,
                    input_bits=input_bits,
                    output_fields=output_fields,
                    output_basis=plan["output_basis"],
                )
                if input_valid
                else {}
            )
            for raw_output_bits, output_valid in zip(
                output_codes, output_validity, strict=True
            ):
                coefficient = (
                    transition.get(raw_output_bits) if output_valid else None
                )
                yield {
                    "operation_index": operation_index,
                    "input_bits": input_bits,
                    "output_bits": list(raw_output_bits),
                    "input_valid": input_valid,
                    "output_valid": output_valid,
                    "totalized_coefficient": (
                        _TINY_ZERO
                        if coefficient is None
                        else coefficient.to_data()
                    ),
                }


def summarize_tiny_add_truth_assertion(
    witness_id: str, *, assertion_id: str, subject: str
) -> dict[str, Any]:
    """Hash the preregistered assertion preimage with bounded working memory."""

    if not assertion_id or not subject:
        raise ValueError("tiny ADD assertion identity must be nonempty")
    digest = hashlib.sha256()
    digest.update(b'{"assertion_id":')
    digest.update(canonical_json_bytes(assertion_id))
    digest.update(b',"rows":[')
    rows_digest = hashlib.sha256(b"[")
    row_count = 0
    for row in iter_tiny_add_truth_rows(witness_id):
        if row_count:
            digest.update(b",")
            rows_digest.update(b",")
        row_bytes = canonical_json_bytes(row)
        digest.update(row_bytes)
        rows_digest.update(row_bytes)
        row_count += 1
    digest.update(b'],"subject":')
    rows_digest.update(b"]")
    digest.update(canonical_json_bytes(subject))
    digest.update(b"}")
    expected_count = tiny_add_truth_row_count(witness_id)
    if row_count != expected_count:
        raise AssertionError("tiny ADD truth stream is not the complete Cartesian product")
    return {
        "row_count": row_count,
        "sha256": digest.hexdigest(),
        "rows_sha256": rows_digest.hexdigest(),
    }


# Kept as a streaming compatibility spelling.  Calling ``list`` on T4 would
# violate the memory-safety requirement; qualification consumes the iterator.
build_tiny_add_truth_rows = iter_tiny_add_truth_rows


def _codec(checkpoint: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint": checkpoint["ordinal"],
        "fields": list(checkpoint["codec_fields"]),
        "validity_sha256": sha256_json(checkpoint["validity"]),
    }


def build_dynamic_add_relation_program(
    pair: StaticArtifact, *, neutral: StaticArtifact
) -> StaticArtifact:
    """Bind an authenticated pair program to root-independent relation maps."""

    # A schema-valid, self-hashed pair envelope is not authority.  Reproduce
    # the complete pair program from the frozen neutral program before reading
    # algebra, checkpoints, or kernels for ADD lowering.
    from .pair import validate_exact_pair_transition_program

    authenticated_pair = validate_exact_pair_transition_program(
        pair.to_data(), neutral=neutral
    )
    pair_data = authenticated_pair.to_data()
    pair_semantic = pair_data["semantic"]
    checkpoints = pair_semantic["checkpoints"]
    kernels = pair_semantic["kernels"]
    if len(checkpoints) != len(kernels) + 1:
        raise ValueError("pair checkpoint/kernel cardinality mismatch")

    events: list[dict[str, Any]] = []
    for index, kernel in enumerate(kernels):
        input_codec = _codec(checkpoints[index])
        output_codec = _codec(checkpoints[index + 1])
        input_fields = input_codec["fields"]
        output_fields = output_codec["fields"]
        events.append(
            {
                "event_id": kernel["event_id"],
                "pair_semantic_sha256": kernel["semantic_sha256"],
                "input_codec": input_codec,
                "output_codec": output_codec,
                "relation_order": [
                    *(f"in.{field}" for field in input_fields),
                    *(f"out.{field}" for field in output_fields),
                ],
                "abstraction": [f"in.{field}" for field in input_fields],
                "rename": [
                    {"from": f"out.{field}", "to": field}
                    for field in output_fields
                ],
            }
        )

    return StaticArtifact(
        ADD_SCHEMA,
        {
            "pair_sha256": authenticated_pair.sha256,
            "canonical_add_policy": dict(CANONICAL_ADD_POLICY),
            "events": events,
        },
    )


def validate_dynamic_add_relation_program(
    data: object, *, pair: StaticArtifact, neutral: StaticArtifact
) -> StaticArtifact:
    """Strictly reload a static ADD relation program against its pair owner."""

    validate_static_envelope(
        data,
        schema=ADD_SCHEMA,
        semantic_keys={"pair_sha256", "canonical_add_policy", "events"},
    )
    expected = build_dynamic_add_relation_program(pair, neutral=neutral)
    if canonical_json_bytes(data) != canonical_json_bytes(expected.to_data()):
        raise ValueError("ADD artifact does not reproduce frozen semantic identity")
    return expected
