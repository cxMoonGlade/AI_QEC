"""Independent stdlib reconstruction of facts from frozen Stim source text.

This module intentionally does not import Stim or any target-lowering owner.  It
parses only the preregistered flattened source grammar and reconstructs the
small set of structural facts used to qualify the neutral lowering.
"""

from __future__ import annotations

import re


_ALLOWED_GATES = {
    "QUBIT_COORDS",
    "R",
    "TICK",
    "H",
    "DEPOLARIZE1",
    "CX",
    "DEPOLARIZE2",
    "MR",
    "DETECTOR",
    "M",
    "OBSERVABLE_INCLUDE",
}
_SCALAR_QUBIT_GATES = {"R", "H", "M", "MR"}
_SCAFFOLD_GATES = {"DEPOLARIZE1", "DEPOLARIZE2"}
_EVENT_KIND = {
    "R": "RESET",
    "H": "H",
    "M": "M",
    "MR": "MR",
}
_KERNEL = {
    "COORD_MARKER": "MARKER_IDENTITY",
    "TICK_MARKER": "MARKER_IDENTITY",
    "RESET": "RESET_PAULI_INSTRUMENT",
    "H": "CLIFFORD_H",
    "CX": "CLIFFORD_CX",
    "COHERENT_Z": "PERSISTENT_COHERENT_Z",
    "M": "MEASURE_Z_INSTRUMENT",
    "MR": "MEASURE_RESET_Z_INSTRUMENT",
    "DETECTOR_APPEND": "DETECTOR_XOR_APPEND",
    "OBSERVABLE_XOR": "OBSERVABLE_XOR_ACCUMULATE",
    "FINALIZE_RECORD": "FINALIZE_OBSERVABLE_ZERO",
}
_LINE = re.compile(
    r"^(?P<gate>[A-Z][A-Z0-9_]*)"
    r"(?:\((?P<args>[^()]*)\))?"
    r"(?: (?P<targets>\S(?:.*\S)?))?$"
)
_QUBIT = re.compile(r"(?:0|[1-9][0-9]*)\Z")
_REC = re.compile(r"rec\[(?P<offset>-[1-9][0-9]*)\]\Z")


def _parse_line(line: str, *, line_number: int) -> tuple[str, list[str], list[str]]:
    match = _LINE.fullmatch(line)
    if match is None:
        raise ValueError(f"invalid flattened Stim syntax on line {line_number}")
    gate = match.group("gate")
    if gate not in _ALLOWED_GATES:
        raise ValueError(f"unsupported gate {gate!r} on line {line_number}")

    raw_args = match.group("args")
    if raw_args is None:
        args: list[str] = []
    else:
        args = [part.strip() for part in raw_args.split(",")]
        if not args or any(not part for part in args):
            raise ValueError(f"invalid gate arguments on line {line_number}")
    raw_targets = match.group("targets")
    targets = [] if raw_targets is None else raw_targets.split()
    return gate, args, targets


def _canonical_args(args: list[str], *, line_number: int) -> list[str]:
    result: list[str] = []
    for value in args:
        try:
            canonical = format(float(value), ".17g")
        except ValueError as exc:
            raise ValueError(f"invalid numeric argument on line {line_number}") from exc
        if canonical in {"nan", "inf", "-inf"}:
            raise ValueError(f"non-finite argument on line {line_number}")
        result.append(canonical)
    return result


def _qubit_targets(
    tokens: list[str],
    *,
    gate: str,
    line_number: int,
    declared: set[int],
    require_declared: bool = True,
) -> list[int]:
    if not tokens:
        raise ValueError(f"{gate} has no targets on line {line_number}")
    result: list[int] = []
    for token in tokens:
        if _QUBIT.fullmatch(token) is None:
            raise ValueError(f"{gate} has a non-qubit target on line {line_number}")
        qubit = int(token)
        if require_declared and qubit not in declared:
            raise ValueError(
                f"{gate} targets undeclared qubit {qubit} on line {line_number}"
            )
        result.append(qubit)
    return result


def _resolved_rec_targets(
    tokens: list[str], *, raw_count: int, gate: str, line_number: int
) -> list[int]:
    resolved: list[int] = []
    for token in tokens:
        match = _REC.fullmatch(token)
        if match is None:
            raise ValueError(f"{gate} has a non-rec target on line {line_number}")
        offset = int(match.group("offset"))
        absolute = raw_count + offset
        if not 0 <= absolute < raw_count:
            raise ValueError(f"{gate} has an invalid rec offset on line {line_number}")
        resolved.append(absolute)
    return resolved


def _qubit_ref(qubit: int, dense: dict[int, int]) -> dict[str, int]:
    return {"stim_id": qubit, "dense_ordinal": dense[qubit]}


def _event(
    events: list[dict[str, object]],
    *,
    kind: str,
    source_instruction: int | None,
    source_gate: str,
    source_target_ordinal: int | None = None,
    qubits: list[dict[str, int]] | None = None,
    args: list[str] | None = None,
    raw_output: int | None = None,
    rec_operands: list[dict[str, int]] | None = None,
    record_output: dict[str, object] | None = None,
) -> None:
    events.append(
        {
            "event_id": f"e{len(events):06d}",
            "kind": kind,
            "source_instruction": source_instruction,
            "source_gate": source_gate,
            "source_target_ordinal": source_target_ordinal,
            "source_operand_ordinal": None,
            "qubits": [] if qubits is None else qubits,
            "args": [] if args is None else args,
            "raw_output": raw_output,
            "rec_operands": [] if rec_operands is None else rec_operands,
            "record_output": record_output,
            "kernel_id": _KERNEL[kind],
        }
    )


def reconstruct_site_map(source_text: str) -> list[dict[str, object]]:
    """Reconstruct scaffold-site rows directly from canonical source text."""

    if not isinstance(source_text, str):
        raise TypeError("source_text must be a string")
    if not source_text or not source_text.endswith("\n"):
        raise ValueError("canonical source_text must be nonempty and newline-terminated")

    declared: set[int] = set()
    site_map: list[dict[str, object]] = []
    for line_number, line in enumerate(source_text.splitlines(), start=1):
        if not line:
            raise ValueError(f"blank source line at line {line_number}")
        gate, raw_args, targets = _parse_line(line, line_number=line_number)
        args = _canonical_args(raw_args, line_number=line_number)

        if gate == "QUBIT_COORDS":
            qubits = _qubit_targets(
                targets,
                gate=gate,
                line_number=line_number,
                declared=declared,
                require_declared=False,
            )
            if len(qubits) != 1:
                raise ValueError(
                    f"QUBIT_COORDS must declare one qubit on line {line_number}"
                )
            qubit = qubits[0]
            if qubit in declared:
                raise ValueError(f"duplicate declared qubit {qubit} on line {line_number}")
            declared.add(qubit)
            continue

        if gate not in _SCAFFOLD_GATES:
            continue
        if len(args) != 1:
            raise ValueError(f"{gate} must have one argument on line {line_number}")
        qubits = _qubit_targets(
            targets,
            gate=gate,
            line_number=line_number,
            declared=declared,
        )
        if gate == "DEPOLARIZE2" and len(qubits) % 2:
            raise ValueError(f"DEPOLARIZE2 has an odd target count on line {line_number}")
        site_map.append(
            {
                "instruction_index": line_number - 1,
                "source_gate": gate,
                "source_args": args,
                "targets": qubits,
            }
        )
    return site_map


def reconstruct_source_program(source_text: str) -> dict[str, object]:
    """Reconstruct neutral-style qubit and event rows without owner code."""

    if not isinstance(source_text, str):
        raise TypeError("source_text must be a string")
    if not source_text or not source_text.endswith("\n"):
        raise ValueError("canonical source_text must be nonempty and newline-terminated")

    qubit_rows: list[dict[str, object]] = []
    declared: set[int] = set()
    dense: dict[int, int] = {}
    events: list[dict[str, object]] = []
    raw_count = 0
    detector_count = 0
    observable_count = 0

    for line_number, line in enumerate(source_text.splitlines(), start=1):
        if not line:
            raise ValueError(f"blank source line at line {line_number}")
        source_instruction = line_number - 1
        gate, raw_args, targets = _parse_line(line, line_number=line_number)
        args = _canonical_args(raw_args, line_number=line_number)

        if gate == "QUBIT_COORDS":
            if not args:
                raise ValueError(f"QUBIT_COORDS lacks coordinates on line {line_number}")
            target_qubits = _qubit_targets(
                targets,
                gate=gate,
                line_number=line_number,
                declared=declared,
                require_declared=False,
            )
            if len(target_qubits) != 1:
                raise ValueError(
                    f"QUBIT_COORDS must declare one qubit on line {line_number}"
                )
            qubit = target_qubits[0]
            if qubit in declared:
                raise ValueError(f"duplicate declared qubit {qubit} on line {line_number}")
            declared.add(qubit)
            dense[qubit] = len(qubit_rows)
            qubit_rows.append(
                {
                    "stim_id": qubit,
                    "dense_ordinal": dense[qubit],
                    "coordinates": args,
                }
            )
            _event(
                events,
                kind="COORD_MARKER",
                source_instruction=source_instruction,
                source_gate=gate,
                source_target_ordinal=0,
                qubits=[_qubit_ref(qubit, dense)],
                args=args,
            )
            continue

        if gate == "TICK":
            if args or targets:
                raise ValueError(f"TICK has arguments or targets on line {line_number}")
            _event(
                events,
                kind="TICK_MARKER",
                source_instruction=source_instruction,
                source_gate=gate,
                args=args,
            )
            continue

        if gate in _SCALAR_QUBIT_GATES:
            if args:
                raise ValueError(f"{gate} unexpectedly has arguments on line {line_number}")
            target_qubits = _qubit_targets(
                targets,
                gate=gate,
                line_number=line_number,
                declared=declared,
            )
            for target_ordinal, qubit in enumerate(target_qubits):
                raw_output = raw_count if gate in {"M", "MR"} else None
                _event(
                    events,
                    kind=_EVENT_KIND[gate],
                    source_instruction=source_instruction,
                    source_gate=gate,
                    source_target_ordinal=target_ordinal,
                    qubits=[_qubit_ref(qubit, dense)],
                    args=args,
                    raw_output=raw_output,
                )
                if raw_output is not None:
                    raw_count += 1
            continue

        if gate == "CX":
            if args:
                raise ValueError(f"CX unexpectedly has arguments on line {line_number}")
            target_qubits = _qubit_targets(
                targets,
                gate=gate,
                line_number=line_number,
                declared=declared,
            )
            if len(target_qubits) % 2:
                raise ValueError(f"CX has an odd target count on line {line_number}")
            for target_index in range(0, len(target_qubits), 2):
                _event(
                    events,
                    kind="CX",
                    source_instruction=source_instruction,
                    source_gate=gate,
                    source_target_ordinal=target_index // 2,
                    qubits=[
                        _qubit_ref(target_qubits[target_index], dense),
                        _qubit_ref(target_qubits[target_index + 1], dense),
                    ],
                    args=args,
                )
            continue

        if gate in _SCAFFOLD_GATES:
            if len(args) != 1:
                raise ValueError(f"{gate} must have one argument on line {line_number}")
            target_qubits = _qubit_targets(
                targets,
                gate=gate,
                line_number=line_number,
                declared=declared,
            )
            if gate == "DEPOLARIZE2" and len(target_qubits) % 2:
                raise ValueError(
                    f"DEPOLARIZE2 has an odd target count on line {line_number}"
                )
            for target_ordinal, qubit in enumerate(target_qubits):
                _event(
                    events,
                    kind="COHERENT_Z",
                    source_instruction=source_instruction,
                    source_gate=gate,
                    source_target_ordinal=target_ordinal,
                    qubits=[_qubit_ref(qubit, dense)],
                    args=args,
                )
            continue

        if gate in {"DETECTOR", "OBSERVABLE_INCLUDE"}:
            rec_operands = []
            for operand_ordinal, token in enumerate(targets):
                match = _REC.fullmatch(token)
                if match is None:
                    raise ValueError(
                        f"{gate} has a non-rec target on line {line_number}"
                    )
                negative_offset = int(match.group("offset"))
                absolute = raw_count + negative_offset
                if not 0 <= absolute < raw_count:
                    raise ValueError(
                        f"{gate} has an invalid rec offset on line {line_number}"
                    )
                rec_operands.append(
                    {
                        "negative_offset": negative_offset,
                        "absolute_raw_ordinal": absolute,
                        "operand_ordinal": operand_ordinal,
                    }
                )
            if gate == "DETECTOR":
                _event(
                    events,
                    kind="DETECTOR_APPEND",
                    source_instruction=source_instruction,
                    source_gate=gate,
                    args=args,
                    rec_operands=rec_operands,
                    record_output={"kind": "DETECTOR", "ordinal": detector_count},
                )
                detector_count += 1
            else:
                if args != ["0"]:
                    raise ValueError(
                        "only OBSERVABLE_INCLUDE(0) is permitted "
                        f"on line {line_number}"
                    )
                _event(
                    events,
                    kind="OBSERVABLE_XOR",
                    source_instruction=source_instruction,
                    source_gate=gate,
                    args=args,
                    rec_operands=rec_operands,
                )
                observable_count += 1
            continue

        raise AssertionError(f"unhandled allowed gate {gate}")

    if not qubit_rows:
        raise ValueError("source declares no qubits")
    if observable_count != 1:
        raise ValueError("source must declare observable zero exactly once")

    _event(
        events,
        kind="FINALIZE_RECORD",
        source_instruction=None,
        source_gate="GENERATED",
        record_output={"kind": "OBSERVABLE", "ordinal": 0},
    )
    return {"qubits": qubit_rows, "events": events}


def reconstruct_source_facts(source_text: str) -> dict[str, object]:
    """Reconstruct preregistered neutral-program facts from source bytes alone."""
    program = reconstruct_source_program(source_text)
    qubits = program["qubits"]
    events = program["events"]
    assert isinstance(qubits, list) and isinstance(events, list)
    detector_count = sum(event["kind"] == "DETECTOR_APPEND" for event in events)
    raw_measurements = sum(event["raw_output"] is not None for event in events)
    return {
        "coherent_occurrences": sum(
            event["kind"] == "COHERENT_Z" for event in events
        ),
        "declared_qubits": [qubit["stim_id"] for qubit in qubits],
        "detectors": detector_count,
        "program_events": len(events),
        "raw_measurements": raw_measurements,
        "record_width": detector_count + 1,
        "resolved_record_operands": [
            [operand["absolute_raw_ordinal"] for operand in event["rec_operands"]]
            for event in events
            if event["kind"] in {"DETECTOR_APPEND", "OBSERVABLE_XOR"}
        ],
    }
