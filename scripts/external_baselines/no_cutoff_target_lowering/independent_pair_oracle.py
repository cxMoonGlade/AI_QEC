"""Independent source/RREF and finite-matrix oracle for static pair rows.

This module deliberately does not import the target lowering, its model, or
the earlier micro-owner.  It reconstructs receipt rows directly from canonical
Stim text, and checks nontrivial local expansions against literal SymPy
matrices before returning their frozen normal form.
"""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from typing import Any

import sympy as sp


# Elements are a + b*sqrt(2) + i*(c + d*sqrt(2)).  Keeping this tiny field
# implementation here makes the oracle independent of both exact owners.
_Q = tuple[Fraction, Fraction, Fraction, Fraction]

_ZERO: _Q = (Fraction(0),) * 4
_ONE: _Q = (Fraction(1), Fraction(0), Fraction(0), Fraction(0))
_I: _Q = (Fraction(0), Fraction(0), Fraction(1), Fraction(0))
_HALF: _Q = (Fraction(1, 2), Fraction(0), Fraction(0), Fraction(0))
_C: _Q = (Fraction(9999, 10001), Fraction(0), Fraction(0), Fraction(0))
_S: _Q = (Fraction(200, 10001), Fraction(0), Fraction(0), Fraction(0))

_IDENTITY_2 = sp.eye(2)
_X = sp.Matrix([[0, 1], [1, 0]])
_Y = sp.Matrix([[0, -sp.I], [sp.I, 0]])
_Z = sp.diag(1, -1)
_H = sp.Matrix([[1, 1], [1, -1]]) / sp.sqrt(2)
_CX = sp.Matrix(
    [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0],
    ]
)
_PAULI = {"I": _IDENTITY_2, "X": _X, "Y": _Y, "Z": _Z}
_MATRIX_CHECKED: set[str] = set()


def _q_add(left: _Q, right: _Q) -> _Q:
    return tuple(a + b for a, b in zip(left, right, strict=True))  # type: ignore[return-value]


def _q_mul(left: _Q, right: _Q) -> _Q:
    a, b, c, d = left
    e, f, g, h = right
    # (a+b*r)(e+f*r) - (c+d*r)(g+h*r)
    real_a = a * e + 2 * b * f - c * g - 2 * d * h
    real_b = a * f + b * e - c * h - d * g
    # (a+b*r)(g+h*r) + (c+d*r)(e+f*r)
    imag_a = a * g + 2 * b * h + c * e + 2 * d * f
    imag_b = a * h + b * g + c * f + d * e
    return (real_a, real_b, imag_a, imag_b)


def _q_scale(value: _Q, scalar: int) -> _Q:
    return tuple(scalar * item for item in value)  # type: ignore[return-value]


def _q_conjugate(value: _Q) -> _Q:
    a, b, c, d = value
    return (a, b, -c, -d)


def _q_power(value: _Q, exponent: int) -> _Q:
    if exponent < 0:
        raise ValueError("negative exact power")
    result = _ONE
    for _ in range(exponent):
        result = _q_mul(result, value)
    return result


def _q_data(value: _Q) -> list[list[int]]:
    return [[part.numerator, part.denominator] for part in value]


def _q_from_data(value: object) -> _Q:
    if not isinstance(value, list) or len(value) != 4:
        raise AssertionError("oracle coefficient is not a four-coordinate field value")
    coordinates: list[Fraction] = []
    for pair in value:
        if (
            not isinstance(pair, list)
            or len(pair) != 2
            or type(pair[0]) is not int
            or type(pair[1]) is not int
            or pair[1] <= 0
        ):
            raise AssertionError("oracle coefficient has an invalid rational encoding")
        item = Fraction(pair[0], pair[1])
        if [item.numerator, item.denominator] != pair:
            raise AssertionError("oracle coefficient is not reduced canonically")
        coordinates.append(item)
    return tuple(coordinates)  # type: ignore[return-value]


def _q_sympy(value: _Q) -> sp.Expr:
    a, b, c, d = value
    rational = lambda item: sp.Rational(item.numerator, item.denominator)
    return (
        rational(a)
        + rational(b) * sp.sqrt(2)
        + sp.I * (rational(c) + rational(d) * sp.sqrt(2))
    )


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _action(
    opcode: str, qubits: list[int] | None = None, *parameters: str
) -> dict[str, Any]:
    return {
        "opcode": opcode,
        "qubits": [] if qubits is None else list(qubits),
        "parameters": list(parameters),
    }


def _classical_action(
    opcode: str,
    *,
    raw_output: int | None = None,
    rec_operands: list[dict[str, int]] | None = None,
    record_output: dict[str, int] | None = None,
) -> dict[str, Any]:
    return {
        "opcode": opcode,
        "raw_output": raw_output,
        "rec_operands": [] if rec_operands is None else [dict(x) for x in rec_operands],
        "record_output": None if record_output is None else dict(record_output),
    }


def _multipliers(values: dict[int, _Q] | None = None) -> list[dict[str, Any]]:
    selected = {-1: _ONE, 1: _ONE} if values is None else values
    if set(selected) != {-1, 1}:
        raise AssertionError("oracle latent multiplier domain changed")
    return [
        {"latent_m": latent, "coefficient": _q_data(selected[latent])}
        for latent in (-1, 1)
    ]


def _row(
    *,
    branch: list[dict[str, int]] | None = None,
    left_action: dict[str, Any] | None = None,
    right_action: dict[str, Any] | None = None,
    reference_action: dict[str, Any] | None = None,
    classical_action: dict[str, Any] | None = None,
    multipliers: dict[int, _Q] | None = None,
) -> dict[str, Any]:
    return {
        "branch": [] if branch is None else [dict(choice) for choice in branch],
        "input_predicates": [],
        "left_action": _action("IDENTITY") if left_action is None else left_action,
        "right_action": _action("IDENTITY") if right_action is None else right_action,
        "reference_action": (
            _action("IDENTITY") if reference_action is None else reference_action
        ),
        "classical_action": (
            _classical_action("IDENTITY")
            if classical_action is None
            else classical_action
        ),
        "multiplier_by_latent": _multipliers(multipliers),
    }


def _dense_qubits(event: dict[str, Any]) -> list[int]:
    qubits = event.get("qubits")
    if not isinstance(qubits, list):
        raise TypeError("neutral event qubits must be a list")
    result: list[int] = []
    for qubit in qubits:
        if not isinstance(qubit, dict) or type(qubit.get("dense_ordinal")) is not int:
            raise TypeError("neutral event has an invalid dense qubit reference")
        result.append(qubit["dense_ordinal"])
    return result


def _coherent_rows(event: dict[str, Any], q: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for left in (0, 1):
        for right in (0, 1):
            values: dict[int, _Q] = {}
            for latent in (-1, 1):
                left_coefficient = (
                    _ONE if left == 0 else _q_scale(_q_mul(_I, _S), -latent)
                )
                right_coefficient = (
                    _ONE if right == 0 else _q_scale(_q_mul(_I, _S), latent)
                )
                values[latent] = _q_mul(
                    _q_mul(left_coefficient, right_coefficient),
                    _q_power(_C, 2 - left - right),
                )
            rows.append(
                _row(
                    branch=[
                        {"name": "left_Z", "value": left},
                        {"name": "right_Z", "value": right},
                    ],
                    left_action=(
                        _action("LEFT_PREPEND_Z", [q])
                        if left
                        else _action("IDENTITY")
                    ),
                    right_action=(
                        _action("RIGHT_APPEND_Z", [q])
                        if right
                        else _action("IDENTITY")
                    ),
                    multipliers=values,
                )
            )
    if "COHERENT_Z" not in _MATRIX_CHECKED:
        _check_coherent_matrices(rows)
        _MATRIX_CHECKED.add("COHERENT_Z")
    return rows


def _instrument_components(kind: str, branch: int) -> list[tuple[str, _Q]]:
    if kind == "M":
        return [
            ("I", _HALF),
            ("Z", _HALF if branch == 0 else _q_scale(_HALF, -1)),
        ]
    if branch == 0:
        return [("I", _HALF), ("Z", _HALF)]
    return [("X", _HALF), ("Y", _q_mul(_I, _HALF))]


def _instrument_rows(event: dict[str, Any], kind: str, q: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    raw_output = event.get("raw_output")
    if kind == "RESET" and raw_output is not None:
        raise ValueError("RESET must not expose a raw branch")
    if kind in {"M", "MR"} and type(raw_output) is not int:
        raise ValueError(f"{kind} must expose one integer raw branch")
    for branch in (0, 1):
        components = _instrument_components(kind, branch)
        for left_index, (left_pauli, left_value) in enumerate(components):
            for right_index, (right_pauli, right_value) in enumerate(components):
                coefficient = _q_mul(left_value, _q_conjugate(right_value))
                rows.append(
                    _row(
                        branch=[
                            {"name": "b", "value": branch},
                            {"name": "left_component", "value": left_index},
                            {"name": "right_component", "value": right_index},
                        ],
                        left_action=_action(
                            "LEFT_PREPEND_PAULI", [q], left_pauli
                        ),
                        right_action=_action(
                            "RIGHT_APPEND_PAULI", [q], right_pauli
                        ),
                        classical_action=_classical_action(
                            "SUM_KRAUS_BRANCH"
                            if kind == "RESET"
                            else "EMIT_RAW_BRANCH",
                            raw_output=None if kind == "RESET" else raw_output,
                        ),
                        multipliers={-1: coefficient, 1: coefficient},
                    )
                )
    if kind not in _MATRIX_CHECKED:
        _check_instrument_matrices(kind, rows)
        _MATRIX_CHECKED.add(kind)
    return rows


def _matrix_for_action(action: dict[str, Any], *, side: str) -> sp.Matrix:
    opcode = action["opcode"]
    if opcode == "IDENTITY":
        return _IDENTITY_2
    expected = "LEFT_PREPEND_PAULI" if side == "left" else "RIGHT_APPEND_PAULI"
    if opcode != expected or len(action["parameters"]) != 1:
        raise AssertionError("oracle row has an unexpected Pauli action")
    return _PAULI[action["parameters"][0]]


def _coefficient_for_latent(row: dict[str, Any], latent: int) -> sp.Expr:
    matches = [
        item for item in row["multiplier_by_latent"] if item["latent_m"] == latent
    ]
    if len(matches) != 1:
        raise AssertionError("oracle row lost the persistent-sign coordinate")
    return _q_sympy(_q_from_data(matches[0]["coefficient"]))


def _assert_zero_matrix(value: sp.Matrix, *, label: str) -> None:
    if any(sp.simplify(entry) != 0 for entry in value):
        raise AssertionError(f"independent finite-matrix check failed for {label}")


def _generic_density() -> sp.Matrix:
    rho00, rho01, rho10, rho11 = sp.symbols("rho00 rho01 rho10 rho11")
    return sp.Matrix([[rho00, rho01], [rho10, rho11]])


def _check_coherent_matrices(rows: list[dict[str, Any]]) -> None:
    rho = _generic_density()
    c = sp.Rational(9999, 10001)
    s = sp.Rational(200, 10001)
    for latent in (-1, 1):
        observed = sp.zeros(2)
        for row in rows:
            left = _Z if row["branch"][0]["value"] else _IDENTITY_2
            right = _Z if row["branch"][1]["value"] else _IDENTITY_2
            observed += _coefficient_for_latent(row, latent) * left * rho * right
        unitary = c * _IDENTITY_2 - sp.I * latent * s * _Z
        expected = unitary * rho * unitary.conjugate().T
        _assert_zero_matrix(observed - expected, label=f"COHERENT_Z(m={latent})")


def _check_instrument_matrices(kind: str, rows: list[dict[str, Any]]) -> None:
    rho = _generic_density()
    for branch in (0, 1):
        observed = sp.zeros(2)
        for row in rows:
            if row["branch"][0] != {"name": "b", "value": branch}:
                continue
            coefficient = _coefficient_for_latent(row, -1)
            if coefficient != _coefficient_for_latent(row, 1):
                raise AssertionError("instrument coefficient depends on latent sign")
            left = _matrix_for_action(row["left_action"], side="left")
            right = _matrix_for_action(row["right_action"], side="right")
            observed += coefficient * left * rho * right
        if kind == "M":
            kraus = (_IDENTITY_2 + (-1) ** branch * _Z) / 2
        elif branch == 0:
            kraus = (_IDENTITY_2 + _Z) / 2
        else:
            kraus = (_X + sp.I * _Y) / 2
        expected = kraus * rho * kraus.conjugate().T
        _assert_zero_matrix(observed - expected, label=f"{kind}(b={branch})")


def _check_clifford_literals() -> None:
    """Make the action labels answer to independent literal matrices."""

    if "CLIFFORD" in _MATRIX_CHECKED:
        return

    _assert_zero_matrix(_H * _X * _H.conjugate().T - _Z, label="H:X->Z")
    _assert_zero_matrix(_H * _Z * _H.conjugate().T - _X, label="H:Z->X")
    ix = sp.kronecker_product(_IDENTITY_2, _X)
    xx = sp.kronecker_product(_X, _X)
    zi = sp.kronecker_product(_Z, _IDENTITY_2)
    zz = sp.kronecker_product(_Z, _Z)
    _assert_zero_matrix(_CX * ix * _CX.T - ix, label="CX:IX->IX")
    _assert_zero_matrix(_CX * xx * _CX.T - sp.kronecker_product(_X, _IDENTITY_2), label="CX:XX->XI")
    _assert_zero_matrix(_CX * zi * _CX.T - zi, label="CX:ZI->ZI")
    _assert_zero_matrix(_CX * zz * _CX.T - sp.kronecker_product(_IDENTITY_2, _Z), label="CX:ZZ->IZ")
    _MATRIX_CHECKED.add("CLIFFORD")


def reconstruct_component_rows(neutral_event: object) -> list[dict[str, Any]]:
    """Independently reconstruct one neutral event's canonical component rows."""

    if not isinstance(neutral_event, dict):
        raise TypeError("neutral_event must be a dictionary")
    kind = neutral_event.get("kind")
    if not isinstance(kind, str):
        raise TypeError("neutral event kind must be a string")
    qubits = _dense_qubits(neutral_event)

    if kind == "COHERENT_Z":
        if len(qubits) != 1:
            raise ValueError("COHERENT_Z requires one dense qubit")
        rows = _coherent_rows(neutral_event, qubits[0])
    elif kind in {"RESET", "M", "MR"}:
        if len(qubits) != 1:
            raise ValueError(f"{kind} requires one dense qubit")
        rows = _instrument_rows(neutral_event, kind, qubits[0])
    elif kind == "H":
        if len(qubits) != 1:
            raise ValueError("H requires one dense qubit")
        _check_clifford_literals()
        rows = [
            _row(
                left_action=_action("CONJUGATE_H", qubits),
                right_action=_action("CONJUGATE_H", qubits),
                reference_action=_action("CONJUGATE_REFERENCE_H", qubits),
            )
        ]
    elif kind == "CX":
        if len(qubits) != 2:
            raise ValueError("CX requires control and target dense qubits")
        _check_clifford_literals()
        rows = [
            _row(
                left_action=_action("CONJUGATE_CX", qubits),
                right_action=_action("CONJUGATE_CX", qubits),
                reference_action=_action("CONJUGATE_REFERENCE_CX", qubits),
            )
        ]
    elif kind in {
        "COORD_MARKER",
        "TICK_MARKER",
        "DETECTOR_APPEND",
        "OBSERVABLE_XOR",
        "FINALIZE_RECORD",
    }:
        opcode = {
            "DETECTOR_APPEND": "APPEND_DETECTOR_XOR",
            "OBSERVABLE_XOR": "ACCUMULATE_OBSERVABLE_XOR",
            "FINALIZE_RECORD": "APPEND_OBSERVABLE",
        }.get(kind, "IDENTITY")
        rec_operands = neutral_event.get("rec_operands")
        if not isinstance(rec_operands, list):
            raise TypeError("neutral event rec_operands must be a list")
        record_output = neutral_event.get("record_output")
        if record_output is not None and not isinstance(record_output, dict):
            raise TypeError("neutral event record_output must be a dictionary or null")
        raw_output = neutral_event.get("raw_output")
        if raw_output is not None and type(raw_output) is not int:
            raise TypeError("neutral event raw_output must be an integer or null")
        rows = [
            _row(
                classical_action=_classical_action(
                    opcode,
                    raw_output=raw_output,
                    rec_operands=rec_operands,
                    record_output=record_output,
                )
            )
        ]
    else:
        raise ValueError(f"unsupported neutral event kind {kind!r}")

    # This ordering is the preregistered normal form.  Hash ordering is not an
    # alternate spelling, even when all rows contain the same mathematical sum.
    return sorted(rows, key=_canonical_bytes)


_PAIR_EVENT_KIND = {"R": "RESET", "H": "H", "M": "M", "MR": "MR"}
_PAIR_ALLOWED_SOURCE_GATES = {
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
_PAIR_LOCAL_PRODUCT_PHASE = {
    ((0, 0), (0, 0)): 0,
    ((0, 0), (1, 0)): 0,
    ((0, 0), (1, 1)): 0,
    ((0, 0), (0, 1)): 0,
    ((1, 0), (0, 0)): 0,
    ((1, 0), (1, 0)): 0,
    ((1, 0), (1, 1)): 1,
    ((1, 0), (0, 1)): 3,
    ((1, 1), (0, 0)): 0,
    ((1, 1), (1, 0)): 3,
    ((1, 1), (1, 1)): 0,
    ((1, 1), (0, 1)): 1,
    ((0, 1), (0, 0)): 0,
    ((0, 1), (1, 0)): 1,
    ((0, 1), (1, 1)): 3,
    ((0, 1), (0, 1)): 0,
}
_PAIR_CX_PHASE_CACHE: dict[tuple[int, int, int, int], int] = {}


def _pair_source_event(
    events: list[dict[str, Any]],
    *,
    kind: str,
    qubits: list[dict[str, int]] | None = None,
    raw_output: int | None = None,
    rec_operands: list[dict[str, int]] | None = None,
    record_output: dict[str, int] | None = None,
) -> None:
    events.append(
        {
            "event_id": f"e{len(events):06d}",
            "kind": kind,
            "qubits": [] if qubits is None else qubits,
            "raw_output": raw_output,
            "rec_operands": [] if rec_operands is None else rec_operands,
            "record_output": record_output,
        }
    )


def _reconstruct_pair_source_program(source_text: str) -> dict[str, Any]:
    """Parse the frozen text through Stim without neutral/source-owner helpers."""

    if not isinstance(source_text, str):
        raise TypeError("pair receipt source_text must be a string")
    if not source_text or not source_text.endswith("\n"):
        raise ValueError("pair receipt source_text must be newline terminated")
    import stim

    circuit = stim.Circuit(source_text).flattened()
    canonical_text = str(circuit).rstrip("\n") + "\n"
    if canonical_text != source_text:
        raise ValueError("pair receipt source_text is not canonical flattened Stim")

    qubit_ids: list[int] = []
    dense: dict[int, int] = {}
    for instruction in circuit:
        if instruction.name not in _PAIR_ALLOWED_SOURCE_GATES:
            raise ValueError(
                f"pair receipt source contains unsupported gate {instruction.name!r}"
            )
        if instruction.name != "QUBIT_COORDS":
            continue
        targets = instruction.targets_copy()
        if len(targets) != 1 or not targets[0].is_qubit_target:
            raise ValueError("pair receipt QUBIT_COORDS must declare one qubit")
        qubit = int(targets[0].value)
        if qubit in dense:
            raise ValueError("pair receipt source duplicates a declared qubit")
        dense[qubit] = len(qubit_ids)
        qubit_ids.append(qubit)
    if not qubit_ids:
        raise ValueError("pair receipt source declares no qubits")

    def qubit_ref(target: Any) -> dict[str, int]:
        if not target.is_qubit_target:
            raise ValueError("pair receipt quantum operation has a non-qubit target")
        qubit = int(target.value)
        if qubit not in dense:
            raise ValueError("pair receipt operation targets an undeclared qubit")
        return {"stim_id": qubit, "dense_ordinal": dense[qubit]}

    events: list[dict[str, Any]] = []
    raw_count = 0
    detector_count = 0
    observable_count = 0
    for instruction in circuit:
        name = instruction.name
        targets = instruction.targets_copy()
        if name == "QUBIT_COORDS":
            for target in targets:
                _pair_source_event(
                    events, kind="COORD_MARKER", qubits=[qubit_ref(target)]
                )
        elif name in _PAIR_EVENT_KIND:
            for target in targets:
                raw_output = raw_count if name in {"M", "MR"} else None
                _pair_source_event(
                    events,
                    kind=_PAIR_EVENT_KIND[name],
                    qubits=[qubit_ref(target)],
                    raw_output=raw_output,
                )
                raw_count += int(raw_output is not None)
        elif name == "CX":
            if len(targets) % 2:
                raise ValueError("pair receipt CX target list is odd")
            for target_index in range(0, len(targets), 2):
                _pair_source_event(
                    events,
                    kind="CX",
                    qubits=[
                        qubit_ref(targets[target_index]),
                        qubit_ref(targets[target_index + 1]),
                    ],
                )
        elif name in {"DEPOLARIZE1", "DEPOLARIZE2"}:
            if len(instruction.gate_args_copy()) != 1:
                raise ValueError("pair receipt scaffold gate must have one argument")
            if name == "DEPOLARIZE2" and len(targets) % 2:
                raise ValueError("pair receipt DEPOLARIZE2 target list is odd")
            for target in targets:
                _pair_source_event(
                    events, kind="COHERENT_Z", qubits=[qubit_ref(target)]
                )
        elif name == "TICK":
            if targets or instruction.gate_args_copy():
                raise ValueError("pair receipt TICK carries operands")
            _pair_source_event(events, kind="TICK_MARKER")
        elif name in {"DETECTOR", "OBSERVABLE_INCLUDE"}:
            rec_operands: list[dict[str, int]] = []
            for operand_ordinal, target in enumerate(targets):
                if not target.is_measurement_record_target:
                    raise ValueError("pair receipt Record declaration has a non-rec target")
                negative_offset = int(target.value)
                absolute = raw_count + negative_offset
                if negative_offset >= 0 or not 0 <= absolute < raw_count:
                    raise ValueError("pair receipt Record declaration has an invalid rec")
                rec_operands.append(
                    {
                        "negative_offset": negative_offset,
                        "absolute_raw_ordinal": absolute,
                        "operand_ordinal": operand_ordinal,
                    }
                )
            if name == "DETECTOR":
                _pair_source_event(
                    events,
                    kind="DETECTOR_APPEND",
                    rec_operands=rec_operands,
                    record_output={"kind": "DETECTOR", "ordinal": detector_count},
                )
                detector_count += 1
            else:
                args = instruction.gate_args_copy()
                if args != [0.0]:
                    raise ValueError("pair receipt permits only observable zero")
                observable_count += 1
                _pair_source_event(
                    events, kind="OBSERVABLE_XOR", rec_operands=rec_operands
                )
        else:
            raise AssertionError(f"unhandled pair receipt source gate {name!r}")
    if observable_count != 1:
        raise ValueError("pair receipt source must declare observable zero once")
    _pair_source_event(
        events,
        kind="FINALIZE_RECORD",
        record_output={"kind": "OBSERVABLE", "ordinal": 0},
    )
    return {"qubit_ids": qubit_ids, "events": events}


def _pair_signed_row(
    x: list[int], z: list[int], phase_mod4: int = 0
) -> dict[str, Any]:
    if len(x) != len(z) or any(bit not in (0, 1) for bit in (*x, *z)):
        raise ValueError("pair receipt Pauli row is invalid")
    if phase_mod4 not in range(4):
        raise ValueError("pair receipt Pauli phase is invalid")
    return {"x": list(x), "z": list(z), "phase_mod4": phase_mod4}


def _pair_row_bits(row: dict[str, Any]) -> list[int]:
    return list(row["x"]) + list(row["z"])


def _pair_multiply_rows(
    left: dict[str, Any], right: dict[str, Any]
) -> dict[str, Any]:
    if not (
        len(left["x"])
        == len(left["z"])
        == len(right["x"])
        == len(right["z"])
    ):
        raise ValueError("pair receipt Pauli widths differ")
    phase = int(left["phase_mod4"]) + int(right["phase_mod4"])
    out_x: list[int] = []
    out_z: list[int] = []
    for lx, lz, rx, rz in zip(
        left["x"], left["z"], right["x"], right["z"], strict=True
    ):
        phase += _PAIR_LOCAL_PRODUCT_PHASE[((lx, lz), (rx, rz))]
        out_x.append(lx ^ rx)
        out_z.append(lz ^ rz)
    return _pair_signed_row(out_x, out_z, phase % 4)


def _pair_commutes(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return (
        sum(
            lx * rz + lz * rx
            for lx, lz, rx, rz in zip(
                left["x"], left["z"], right["x"], right["z"], strict=True
            )
        )
        % 2
        == 0
    )


def _pair_rref(stabilizers: list[dict[str, Any]]) -> dict[str, Any]:
    if not stabilizers:
        raise ValueError("pair receipt stabilizer basis is empty")
    qubit_count = len(stabilizers)
    if any(
        len(row["x"]) != qubit_count
        or len(row["z"]) != qubit_count
        or row["phase_mod4"] not in (0, 2)
        for row in stabilizers
    ):
        raise ValueError("pair receipt stabilizer basis is not a pure-state basis")
    if any(
        not _pair_commutes(stabilizers[left], stabilizers[right])
        for left in range(qubit_count)
        for right in range(left)
    ):
        raise ValueError("pair receipt stabilizers do not commute")
    rows = deepcopy(stabilizers)
    pivots: list[int] = []
    pivot_row = 0
    for column in range(2 * qubit_count):
        selected = next(
            (
                row
                for row in range(pivot_row, qubit_count)
                if _pair_row_bits(rows[row])[column]
            ),
            None,
        )
        if selected is None:
            continue
        rows[pivot_row], rows[selected] = rows[selected], rows[pivot_row]
        for row in range(qubit_count):
            if row != pivot_row and _pair_row_bits(rows[row])[column]:
                rows[row] = _pair_multiply_rows(rows[pivot_row], rows[row])
        pivots.append(column)
        pivot_row += 1
        if pivot_row == qubit_count:
            break
    if pivot_row != qubit_count:
        raise ValueError("pair receipt reference stabilizer lost rank")
    return {
        "stabilizers": deepcopy(stabilizers),
        "rref_rows": rows,
        "pivots": pivots,
    }


def _pair_conjugate_h(row: dict[str, Any], qubit: int) -> dict[str, Any]:
    result = deepcopy(row)
    x, z = result["x"][qubit], result["z"][qubit]
    result["x"][qubit], result["z"][qubit] = z, x
    if x and z:
        result["phase_mod4"] = (result["phase_mod4"] + 2) % 4
    return result


def _pair_conjugate_cx(
    row: dict[str, Any], control: int, target: int
) -> dict[str, Any]:
    result = deepcopy(row)
    xc = result["x"][control]
    zc = result["z"][control]
    xt = result["x"][target]
    zt = result["z"][target]
    local_key = (xc, zc, xt, zt)
    phase_delta = _PAIR_CX_PHASE_CACHE.get(local_key)
    if phase_delta is None:
        labels = {(0, 0): "I", (1, 0): "X", (1, 1): "Y", (0, 1): "Z"}
        input_matrix = sp.kronecker_product(
            _PAULI[labels[(xc, zc)]], _PAULI[labels[(xt, zt)]]
        )
        output_bits = (xc, zc ^ zt, xt ^ xc, zt)
        output_matrix = sp.kronecker_product(
            _PAULI[labels[output_bits[:2]]], _PAULI[labels[output_bits[2:]]]
        )
        conjugated = _CX * input_matrix * _CX.T
        if conjugated == output_matrix:
            phase_delta = 0
        elif conjugated == -output_matrix:
            phase_delta = 2
        else:
            raise AssertionError("literal CX did not map a Pauli to a signed Pauli")
        _PAIR_CX_PHASE_CACHE[local_key] = phase_delta
    result["phase_mod4"] = (result["phase_mod4"] + phase_delta) % 4
    result["x"][target] ^= xc
    result["z"][control] ^= zt
    return result


def _pair_checkpoint_bases(
    events: list[dict[str, Any]], qubit_count: int
) -> list[dict[str, Any]]:
    stabilizers: list[dict[str, Any]] = []
    for qubit in range(qubit_count):
        x = [0] * qubit_count
        z = [0] * qubit_count
        z[qubit] = 1
        stabilizers.append(_pair_signed_row(x, z))
    cache: dict[tuple[tuple[int, ...], ...], dict[str, Any]] = {}

    def checkpoint() -> dict[str, Any]:
        key = tuple(
            tuple(row["x"] + row["z"] + [row["phase_mod4"]])
            for row in stabilizers
        )
        if key not in cache:
            cache[key] = _pair_rref(stabilizers)
        return deepcopy(cache[key])

    history = [checkpoint()]
    for event in events:
        dense_qubits = [qubit["dense_ordinal"] for qubit in event["qubits"]]
        if event["kind"] == "H":
            if len(dense_qubits) != 1:
                raise ValueError("pair receipt H event has wrong arity")
            stabilizers = [
                _pair_conjugate_h(row, dense_qubits[0]) for row in stabilizers
            ]
        elif event["kind"] == "CX":
            if len(dense_qubits) != 2:
                raise ValueError("pair receipt CX event has wrong arity")
            stabilizers = [
                _pair_conjugate_cx(row, dense_qubits[0], dense_qubits[1])
                for row in stabilizers
            ]
        history.append(checkpoint())
    return history


def _pair_codec_fields(
    qubit_ids: list[int],
    *,
    observable_live: bool,
    live_raw: list[int],
    record_width: int,
) -> list[str]:
    fields = [
        field
        for side in ("L", "R")
        for axis in ("x", "z")
        for field in (f"{side}.{axis}[{qubit}]" for qubit in qubit_ids)
    ]
    fields.append("latent_m")
    if observable_live:
        fields.append("observable_0_accumulator")
    fields.extend(f"live_raw[{raw}]" for raw in live_raw)
    fields.extend(f"record[{record}]" for record in range(record_width))
    return fields


def _pair_pivot_field(side: str, pivot: int, qubit_ids: list[int]) -> str:
    qubit_count = len(qubit_ids)
    axis = "x" if pivot < qubit_count else "z"
    qubit = qubit_ids[pivot if pivot < qubit_count else pivot - qubit_count]
    return f"{side}.{axis}[{qubit}]"


def _pair_checkpoint_codecs(
    events: list[dict[str, Any]],
    qubit_ids: list[int],
    bases: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    producer: dict[int, int] = {}
    last_use: dict[int, int] = {}
    for event_index, event in enumerate(events):
        raw_output = event["raw_output"]
        if raw_output is not None:
            if raw_output in producer:
                raise ValueError("pair receipt source duplicates a raw output")
            producer[raw_output] = event_index
        for operand in event["rec_operands"]:
            raw = operand["absolute_raw_ordinal"]
            if raw not in producer:
                raise ValueError("pair receipt rec operand has no prior producer")
            last_use[raw] = event_index
    record_widths = [0]
    for event in events:
        record_widths.append(
            record_widths[-1] + int(event["record_output"] is not None)
        )
    codecs: list[dict[str, Any]] = []
    for checkpoint, basis in enumerate(bases):
        after_event = checkpoint - 1
        live_raw = sorted(
            raw
            for raw, produced_at in producer.items()
            if produced_at <= after_event and last_use.get(raw, -1) > after_event
        )
        validity = {
            "pivot_zero_fields": [
                _pair_pivot_field(side, pivot, qubit_ids)
                for side in ("L", "R")
                for pivot in basis["pivots"]
            ],
            "inactive_zero_fields": [],
            "latent_values": [-1, 1],
            "record_width": record_widths[checkpoint],
        }
        codecs.append(
            {
                "checkpoint": checkpoint,
                "fields": _pair_codec_fields(
                    qubit_ids,
                    observable_live=checkpoint < len(events),
                    live_raw=live_raw,
                    record_width=record_widths[checkpoint],
                ),
                "validity_sha256": hashlib.sha256(
                    _canonical_bytes(validity)
                ).hexdigest(),
            }
        )
    return codecs


def reconstruct_pair_receipt_rows(source_text: str) -> dict[str, list[dict[str, Any]]]:
    """Reconstruct every expected ``pair:*`` receipt row in one source owner.

    This function imports no target-lowering owner, neutral parser, source
    oracle, or target/RREF oracle.  The returned lists retain chronological or
    frozen enumeration order; callers must not replace it with hash sorting.
    """

    source = _reconstruct_pair_source_program(source_text)
    qubit_ids = source["qubit_ids"]
    events = source["events"]
    bases = _pair_checkpoint_bases(events, len(qubit_ids))
    zero_pauli = {"x": [0] * len(qubit_ids), "z": [0] * len(qubit_ids)}
    initial_terms = [
        {
            "coefficient": [[1, 2], [0, 1], [0, 1], [0, 1]],
            "latent_m": latent,
            "left": deepcopy(zero_pauli),
            "right": deepcopy(zero_pauli),
            "observable_accumulator": 0,
            "live_raw": [],
            "record": [],
        }
        for latent in (-1, 1)
    ]
    return {
        "initial_terms": initial_terms,
        "basis_catalog": bases,
        "checkpoint_codecs": _pair_checkpoint_codecs(
            events, qubit_ids, bases
        ),
        "kernel_normal_forms": [
            {
                "event_id": event["event_id"],
                "rows": reconstruct_component_rows(event),
            }
            for event in events
        ],
    }


def _pauli_word_matrix(word: str) -> sp.Matrix:
    if not word or any(letter not in _PAULI for letter in word):
        raise AssertionError("pair witness has an invalid Pauli word")
    result = _PAULI[word[0]]
    for letter in word[1:]:
        result = sp.kronecker_product(result, _PAULI[letter])
    return result


def _single_qubit_gate(gate: sp.Matrix, qubit: int, qubit_count: int) -> sp.Matrix:
    if type(qubit) is not int or qubit not in range(qubit_count):
        raise AssertionError("pair witness action has an invalid qubit")
    factors = [gate if index == qubit else _IDENTITY_2 for index in range(qubit_count)]
    result = factors[0]
    for factor in factors[1:]:
        result = sp.kronecker_product(result, factor)
    return result


def _literal_cx(control: int, target: int, qubit_count: int) -> sp.Matrix:
    if (
        type(control) is not int
        or type(target) is not int
        or control not in range(qubit_count)
        or target not in range(qubit_count)
        or control == target
    ):
        raise AssertionError("pair witness CX action has invalid endpoints")
    dimension = 1 << qubit_count
    matrix = sp.zeros(dimension)
    for column in range(dimension):
        bits = [
            (column >> (qubit_count - index - 1)) & 1
            for index in range(qubit_count)
        ]
        if bits[control]:
            bits[target] ^= 1
        row = sum(bit << (qubit_count - index - 1) for index, bit in enumerate(bits))
        matrix[row, column] = 1
    return matrix


def _validate_witness_action(action: object) -> tuple[str, list[int], list[str]]:
    if not isinstance(action, dict) or set(action) != {
        "opcode",
        "qubits",
        "parameters",
    }:
        raise AssertionError("pair witness component action schema mismatch")
    opcode = action["opcode"]
    qubits = action["qubits"]
    parameters = action["parameters"]
    if not isinstance(opcode, str):
        raise AssertionError("pair witness component opcode is not a string")
    if not isinstance(qubits, list) or any(type(q) is not int for q in qubits):
        raise AssertionError("pair witness component qubits are invalid")
    if not isinstance(parameters, list) or any(
        not isinstance(parameter, str) for parameter in parameters
    ):
        raise AssertionError("pair witness component parameters are invalid")
    return opcode, qubits, parameters


def _conjugation_gate(
    opcode: str, qubits: list[int], parameters: list[str], qubit_count: int
) -> sp.Matrix:
    if parameters:
        raise AssertionError("Clifford witness action has unexpected parameters")
    if opcode.endswith("_H") and len(qubits) == 1:
        return _single_qubit_gate(_H, qubits[0], qubit_count)
    if opcode.endswith("_CX") and len(qubits) == 2:
        return _literal_cx(qubits[0], qubits[1], qubit_count)
    raise AssertionError("pair witness has an unsupported Clifford action")


def _apply_witness_left(
    action: object, matrix: sp.Matrix, qubit_count: int
) -> sp.Matrix:
    opcode, qubits, parameters = _validate_witness_action(action)
    if opcode == "IDENTITY":
        if qubits or parameters:
            raise AssertionError("identity action carries operands")
        return matrix
    if opcode in {"LEFT_PREPEND_Z", "LEFT_PREPEND_PAULI"}:
        if len(qubits) != 1:
            raise AssertionError("left prepend action must name one qubit")
        if opcode == "LEFT_PREPEND_Z":
            if parameters:
                raise AssertionError("LEFT_PREPEND_Z carries parameters")
            pauli = _Z
        else:
            if len(parameters) != 1 or parameters[0] not in _PAULI:
                raise AssertionError("left Pauli action has an invalid parameter")
            pauli = _PAULI[parameters[0]]
        return _single_qubit_gate(pauli, qubits[0], qubit_count) * matrix
    if opcode in {"CONJUGATE_H", "CONJUGATE_CX"}:
        gate = _conjugation_gate(opcode, qubits, parameters, qubit_count)
        return gate * matrix * gate.conjugate().T
    raise AssertionError(f"unsupported left witness action {opcode!r}")


def _apply_witness_right(
    action: object, matrix: sp.Matrix, qubit_count: int
) -> sp.Matrix:
    opcode, qubits, parameters = _validate_witness_action(action)
    if opcode == "IDENTITY":
        if qubits or parameters:
            raise AssertionError("identity action carries operands")
        return matrix
    if opcode in {"RIGHT_APPEND_Z", "RIGHT_APPEND_PAULI"}:
        if len(qubits) != 1:
            raise AssertionError("right append action must name one qubit")
        if opcode == "RIGHT_APPEND_Z":
            if parameters:
                raise AssertionError("RIGHT_APPEND_Z carries parameters")
            pauli = _Z
        else:
            if len(parameters) != 1 or parameters[0] not in _PAULI:
                raise AssertionError("right Pauli action has an invalid parameter")
            pauli = _PAULI[parameters[0]]
        return matrix * _single_qubit_gate(pauli, qubits[0], qubit_count)
    if opcode in {"CONJUGATE_H", "CONJUGATE_CX"}:
        gate = _conjugation_gate(opcode, qubits, parameters, qubit_count)
        return gate * matrix * gate.conjugate().T
    raise AssertionError(f"unsupported right witness action {opcode!r}")


def _apply_witness_reference(
    action: object, matrix: sp.Matrix, qubit_count: int
) -> sp.Matrix:
    opcode, qubits, parameters = _validate_witness_action(action)
    if opcode == "IDENTITY":
        if qubits or parameters:
            raise AssertionError("identity action carries operands")
        return matrix
    if opcode in {"CONJUGATE_REFERENCE_H", "CONJUGATE_REFERENCE_CX"}:
        gate = _conjugation_gate(opcode, qubits, parameters, qubit_count)
        return gate * matrix * gate.conjugate().T
    raise AssertionError(f"unsupported reference witness action {opcode!r}")


def _validate_witness_component_row(row: object) -> dict[str, Any]:
    required = {
        "branch",
        "input_predicates",
        "left_action",
        "right_action",
        "reference_action",
        "classical_action",
        "multiplier_by_latent",
    }
    if not isinstance(row, dict) or set(row) != required:
        raise AssertionError("pair witness component-row schema mismatch")
    if not isinstance(row["branch"], list) or not isinstance(
        row["input_predicates"], list
    ):
        raise AssertionError("pair witness component branch schema mismatch")
    if row["input_predicates"]:
        raise AssertionError("pair witness component has unexpected predicates")
    classical = row["classical_action"]
    if not isinstance(classical, dict) or set(classical) != {
        "opcode",
        "raw_output",
        "rec_operands",
        "record_output",
    }:
        raise AssertionError("pair witness classical-action schema mismatch")
    _validate_witness_action(row["left_action"])
    _validate_witness_action(row["right_action"])
    _validate_witness_action(row["reference_action"])
    multipliers = row["multiplier_by_latent"]
    if not isinstance(multipliers, list) or len(multipliers) != 2:
        raise AssertionError("pair witness latent multiplier catalog mismatch")
    if [item.get("latent_m") for item in multipliers if isinstance(item, dict)] != [
        -1,
        1,
    ]:
        raise AssertionError("pair witness latent multiplier ordering mismatch")
    for item in multipliers:
        if not isinstance(item, dict) or set(item) != {"latent_m", "coefficient"}:
            raise AssertionError("pair witness multiplier schema mismatch")
        _q_from_data(item["coefficient"])
    return row


def _summed_component_matrix(
    entry: dict[str, Any], reference: sp.Matrix, qubit_count: int, latent: int
) -> sp.Matrix:
    rows = entry["component_rows"]
    if not isinstance(rows, list) or not rows:
        raise AssertionError("pair witness entry has no component rows")
    if rows != sorted(rows, key=_canonical_bytes):
        raise AssertionError("pair witness component rows are not canonical")
    observed = sp.zeros(1 << qubit_count)
    left_input = _pauli_word_matrix(entry["left_pauli"])
    right_input = _pauli_word_matrix(entry["right_pauli"])
    for raw_row in rows:
        row = _validate_witness_component_row(raw_row)
        left = _apply_witness_left(row["left_action"], left_input, qubit_count)
        right = _apply_witness_right(row["right_action"], right_input, qubit_count)
        local_reference = _apply_witness_reference(
            row["reference_action"], reference, qubit_count
        )
        observed += _coefficient_for_latent(row, latent) * left * local_reference * right
    return observed


def _literal_witness_matrix(
    entry: dict[str, Any], reference: sp.Matrix, qubit_count: int, latent: int
) -> sp.Matrix:
    density = (
        _pauli_word_matrix(entry["left_pauli"])
        * reference
        * _pauli_word_matrix(entry["right_pauli"])
    )
    operation = entry["operation_id"]
    identity = sp.eye(1 << qubit_count)
    if operation == "identity":
        return density
    if operation == "H":
        gate = _single_qubit_gate(_H, 0, qubit_count)
        return gate * density * gate.conjugate().T
    if operation == "COHERENT_Z":
        z = _single_qubit_gate(_Z, 0, qubit_count)
        c = sp.Rational(9999, 10001)
        s = sp.Rational(200, 10001)
        gate = c * identity - sp.I * latent * s * z
        return gate * density * gate.conjugate().T
    if operation == "R":
        p0 = (_IDENTITY_2 + _Z) / 2
        reset_one = (_X + sp.I * _Y) / 2
        return p0 * density * p0.conjugate().T + reset_one * density * reset_one.conjugate().T
    if operation in {"M(b=0)", "M(b=1)"}:
        branch = 0 if operation == "M(b=0)" else 1
        kraus = (_IDENTITY_2 + (-1) ** branch * _Z) / 2
        return kraus * density * kraus.conjugate().T
    if operation in {"MR(b=0)", "MR(b=1)"}:
        kraus = (
            (_IDENTITY_2 + _Z) / 2
            if operation == "MR(b=0)"
            else (_X + sp.I * _Y) / 2
        )
        return kraus * density * kraus.conjugate().T
    if operation in {"H(q=0)", "H(q=1)"}:
        qubit = 0 if operation == "H(q=0)" else 1
        gate = _single_qubit_gate(_H, qubit, qubit_count)
        return gate * density * gate.conjugate().T
    if operation in {
        "CX(control=0,target=1)",
        "CX(control=1,target=0)",
    }:
        control, target = (
            (0, 1)
            if operation == "CX(control=0,target=1)"
            else (1, 0)
        )
        gate = _literal_cx(control, target, qubit_count)
        return gate * density * gate.conjugate().T
    raise AssertionError(f"unknown pair witness operation {operation!r}")


def _expected_witness_keys(witness_id: str) -> tuple[list[tuple[Any, ...]], int]:
    paulis = ("I", "X", "Y", "Z")
    if witness_id == "P1":
        operations = (
            "identity",
            "H",
            "COHERENT_Z",
            "R",
            "M(b=0)",
            "M(b=1)",
            "MR(b=0)",
            "MR(b=1)",
        )
        return [
            (left, right, latent, operation)
            for left in paulis
            for right in paulis
            for latent in (-1, 1)
            for operation in operations
        ], 1
    if witness_id == "P2":
        words = tuple(left + right for left in paulis for right in paulis)
        operations = (
            "H(q=0)",
            "H(q=1)",
            "CX(control=0,target=1)",
            "CX(control=1,target=0)",
        )
        return [
            (left, right, operation)
            for left in words
            for right in words
            for operation in operations
        ], 2
    raise ValueError("pair witness id must be exactly 'P1' or 'P2'")


def verify_pair_witness_component_matrices(
    witness_id: str, catalog: object
) -> list[dict[str, Any]]:
    """Exhaustively compare P1/P2 owner sums with literal SymPy actions."""

    expected_keys, qubit_count = _expected_witness_keys(witness_id)
    expected_key_set = set(expected_keys)
    if not isinstance(catalog, list):
        raise TypeError("pair witness component catalog must be a list")
    reference_vector = sp.zeros(1 << qubit_count, 1)
    reference_vector[0, 0] = 1
    reference = reference_vector * reference_vector.conjugate().T
    required_fields = {
        "witness_id",
        "reference",
        "left_pauli",
        "right_pauli",
        "operation_id",
        "component_rows",
    }
    if witness_id == "P1":
        required_fields.add("latent_m")

    by_key: dict[tuple[Any, ...], dict[str, Any]] = {}
    encountered_keys: list[tuple[Any, ...]] = []
    for raw_entry in catalog:
        if not isinstance(raw_entry, dict) or set(raw_entry) != required_fields:
            raise AssertionError("pair witness catalog entry schema mismatch")
        if raw_entry["witness_id"] != witness_id:
            raise AssertionError("pair witness catalog id mismatch")
        if raw_entry["reference"] != "0" * qubit_count:
            raise AssertionError("pair witness reference mismatch")
        if witness_id == "P1":
            key = (
                raw_entry["left_pauli"],
                raw_entry["right_pauli"],
                raw_entry["latent_m"],
                raw_entry["operation_id"],
            )
        else:
            key = (
                raw_entry["left_pauli"],
                raw_entry["right_pauli"],
                raw_entry["operation_id"],
            )
        if key in by_key:
            raise AssertionError("pair witness catalog contains a duplicate entry")
        by_key[key] = raw_entry
        encountered_keys.append(key)
    if set(by_key) != expected_key_set:
        missing = sorted(expected_key_set - set(by_key), key=repr)
        extra = sorted(set(by_key) - expected_key_set, key=repr)
        raise AssertionError(
            f"pair witness catalog coverage mismatch: missing={missing[:1]!r}, extra={extra[:1]!r}"
        )
    if encountered_keys != expected_keys:
        raise AssertionError(
            "pair witness catalog is not in frozen Pauli/bit/operation order"
        )

    verified: list[dict[str, Any]] = []
    for key in expected_keys:
        entry = by_key[key]
        latent = entry["latent_m"] if witness_id == "P1" else -1
        if type(latent) is not int or latent not in (-1, 1):
            raise AssertionError("pair witness latent sign is invalid")
        observed = _summed_component_matrix(entry, reference, qubit_count, latent)
        expected = _literal_witness_matrix(entry, reference, qubit_count, latent)
        for row_index in range(expected.rows):
            for column_index in range(expected.cols):
                difference = sp.simplify(
                    observed[row_index, column_index]
                    - expected[row_index, column_index]
                )
                if difference != 0:
                    raise AssertionError(
                        "pair witness component matrix mismatch at "
                        f"{witness_id}:{key!r}[{row_index},{column_index}]: {difference!s}"
                    )
        result = {
            "witness_id": witness_id,
            "reference": entry["reference"],
            "left_pauli": entry["left_pauli"],
            "right_pauli": entry["right_pauli"],
            "operation_id": entry["operation_id"],
            "component_row_count": len(entry["component_rows"]),
            "expected_matrix": [
                [str(sp.simplify(expected[row, column])) for column in range(expected.cols)]
                for row in range(expected.rows)
            ],
            "observed_matrix": [
                [str(sp.simplify(observed[row, column])) for column in range(observed.cols)]
                for row in range(observed.rows)
            ],
            "status": "PASS",
        }
        if witness_id == "P1":
            result["latent_m"] = latent
        verified.append(result)
    return verified
