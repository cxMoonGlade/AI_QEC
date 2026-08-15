"""Static exact pair-transition lowering for the frozen neutral program.

The public object describes complete event kernels, signed stabilizer/RREF
checkpoints, and reachability-independent codecs.  It never advances a sparse
coefficient map and never reports support.
"""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
from itertools import product
from typing import Any

from scripts.external_baselines.no_cutoff_minimal_exact_owners.model import (
    I,
    ONE,
    Qsqrt2i,
)

from .model import (
    PAIR_SCHEMA,
    StaticArtifact,
    canonical_json_bytes,
    sha256_json,
    validate_static_envelope,
)


_HALF = Qsqrt2i.rational(1, 2)
_C = Qsqrt2i.rational(9999, 10001)
_S = Qsqrt2i.rational(200, 10001)
_ZERO_COEFFICIENT = [[0, 1], [0, 1], [0, 1], [0, 1]]
_ONE_COEFFICIENT = ONE.to_data()

_PAULI_CONVENTION = {
    "bra_reduction": (
        "left_multiply_signed_rref_stabilizers_and_absorb_phase_into_coefficient"
    ),
    "column_order": [
        "x[q]_for_q_in_declared_qubit_order",
        "z[q]_for_q_in_declared_qubit_order",
    ],
    "formula": "P(x,z)=i^(sum_q_x[q]*z[q])*product_q_X[q]^x[q]*Z[q]^z[q]",
    "ket_reduction": (
        "right_multiply_signed_rref_stabilizers_and_absorb_phase_into_coefficient"
    ),
    "phase_storage": "phase_mod4_on_basis_rows_global_phase_excluded_from_keys",
}


def _q_conjugate(value: Qsqrt2i) -> Qsqrt2i:
    return Qsqrt2i(value.a, value.b, -value.c, -value.d)


def _q_scale(value: Qsqrt2i, scalar: int) -> Qsqrt2i:
    return Qsqrt2i.rational(scalar) * value


def _q_power(value: Qsqrt2i, exponent: int) -> Qsqrt2i:
    if exponent < 0:
        raise ValueError("negative exact powers are unsupported")
    result = ONE
    for _ in range(exponent):
        result = result * value
    return result


def _zero_pauli(n: int) -> dict[str, list[int]]:
    return {"x": [0] * n, "z": [0] * n}


def _signed_row(x: list[int], z: list[int], phase: int = 0) -> dict[str, Any]:
    if len(x) != len(z) or any(bit not in (0, 1) for bit in (*x, *z)):
        raise ValueError("invalid Pauli row bits")
    if phase not in range(4):
        raise ValueError("Pauli phase must be modulo four")
    return {"x": list(x), "z": list(z), "phase_mod4": phase}


def _multiply_rows(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    """Multiply signed Hermitian-convention Pauli rows exactly."""

    lx, lz = left["x"], left["z"]
    rx, rz = right["x"], right["z"]
    if len(lx) != len(rx):
        raise ValueError("Pauli row sizes differ")
    exponent = int(left["phase_mod4"]) + int(right["phase_mod4"])
    out_x: list[int] = []
    out_z: list[int] = []
    for x1, z1, x2, z2 in zip(lx, lz, rx, rz, strict=True):
        xo = x1 ^ x2
        zo = z1 ^ z2
        exponent += x1 * z1 + x2 * z2 + 2 * z1 * x2 - xo * zo
        out_x.append(xo)
        out_z.append(zo)
    return _signed_row(out_x, out_z, exponent % 4)


def _conjugate_h(row: dict[str, Any], q: int) -> dict[str, Any]:
    result = deepcopy(row)
    x, z = result["x"][q], result["z"][q]
    if x and z:
        result["phase_mod4"] = (result["phase_mod4"] + 2) % 4
    result["x"][q], result["z"][q] = z, x
    return result


def _conjugate_cx(row: dict[str, Any], control: int, target: int) -> dict[str, Any]:
    result = deepcopy(row)
    xc = result["x"][control]
    zc = result["z"][control]
    xt = result["x"][target]
    zt = result["z"][target]
    if xc and zt and (xt ^ zc ^ 1):
        result["phase_mod4"] = (result["phase_mod4"] + 2) % 4
    result["x"][target] ^= xc
    result["z"][control] ^= zt
    return result


def _row_bits(row: dict[str, Any]) -> list[int]:
    return list(row["x"]) + list(row["z"])


def _rref(stabilizers: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[int]]:
    rows = deepcopy(stabilizers)
    if not rows:
        return [], []
    width = 2 * len(rows[0]["x"])
    pivot_row = 0
    pivots: list[int] = []
    for column in range(width):
        selected = next(
            (
                index
                for index in range(pivot_row, len(rows))
                if _row_bits(rows[index])[column]
            ),
            None,
        )
        if selected is None:
            continue
        rows[pivot_row], rows[selected] = rows[selected], rows[pivot_row]
        for index in range(len(rows)):
            if index != pivot_row and _row_bits(rows[index])[column]:
                rows[index] = _multiply_rows(rows[index], rows[pivot_row])
        pivots.append(column)
        pivot_row += 1
        if pivot_row == len(rows):
            break
    if pivot_row != len(rows):
        raise ValueError("reference stabilizer rank loss")
    for row in rows:
        if row["phase_mod4"] not in (0, 2):
            raise ValueError("reference stabilizer RREF has a non-Hermitian phase")
    return rows, pivots


def _commutes(left: dict[str, Any], right: dict[str, Any]) -> bool:
    parity = 0
    for lx, lz, rx, rz in zip(
        left["x"], left["z"], right["x"], right["z"], strict=True
    ):
        parity ^= (lx & rz) ^ (lz & rx)
    return parity == 0


def _basis(stabilizers: list[dict[str, Any]]) -> dict[str, Any]:
    if any(
        not _commutes(stabilizers[i], stabilizers[j])
        for i in range(len(stabilizers))
        for j in range(i)
    ):
        raise ValueError("reference stabilizers do not commute")
    rref_rows, pivots = _rref(stabilizers)
    payload = {
        "stabilizers": deepcopy(stabilizers),
        "rref_rows": rref_rows,
        "pivots": pivots,
    }
    return {"basis_id": f"basis-{sha256_json(payload)[:16]}", **payload}


def build_signed_rref_basis(stabilizers: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the public exact signed-RREF witness object."""

    if not isinstance(stabilizers, list) or not stabilizers:
        raise ValueError("stabilizers must be a nonempty list")
    expected_keys = {"x", "z", "phase_mod4"}
    normalized: list[dict[str, Any]] = []
    width: int | None = None
    for row in stabilizers:
        if not isinstance(row, dict) or set(row) != expected_keys:
            raise ValueError("signed stabilizer row schema mismatch")
        candidate = _signed_row(row["x"], row["z"], row["phase_mod4"])
        if width is None:
            width = len(candidate["x"])
        if len(candidate["x"]) != width:
            raise ValueError("signed stabilizer widths differ")
        normalized.append(candidate)
    if width != len(normalized):
        raise ValueError("witness stabilizers must define a full-rank pure state")
    return _basis(normalized)


def canonicalize_pauli_against_basis(
    pauli: dict[str, Any],
    basis: dict[str, Any],
    *,
    side: str,
) -> dict[str, Any]:
    """Reduce one key Pauli, preserving asymmetric ket/bra phases exactly."""

    if side not in {"ket", "bra"}:
        raise ValueError("side must be 'ket' or 'bra'")
    if not isinstance(pauli, dict) or set(pauli) != {"x", "z"}:
        raise ValueError("Pauli key schema mismatch")
    if not isinstance(basis, dict) or not {
        "stabilizers",
        "rref_rows",
        "pivots",
    }.issubset(basis):
        raise ValueError("basis schema mismatch")
    current = _signed_row(pauli["x"], pauli["z"])
    rows = basis["rref_rows"]
    pivots = basis["pivots"]
    if len(rows) != len(pivots):
        raise ValueError("basis row/pivot count mismatch")
    for pivot, stabilizer in zip(pivots, rows, strict=True):
        if _row_bits(current)[pivot]:
            current = (
                _multiply_rows(current, stabilizer)
                if side == "ket"
                else _multiply_rows(stabilizer, current)
            )
    if any(_row_bits(current)[pivot] for pivot in pivots):
        raise AssertionError("Pauli coset reduction left a pivot bit")
    return {
        "representative": {"x": current["x"], "z": current["z"]},
        "coefficient_phase_mod4": current["phase_mod4"],
    }


def _field_for_column(side: str, column: int, qubit_ids: list[int]) -> str:
    n = len(qubit_ids)
    if column < n:
        return f"{side}.x[{qubit_ids[column]}]"
    return f"{side}.z[{qubit_ids[column - n]}]"


def _codec_fields(
    *,
    qubit_ids: list[int],
    observable_live: bool,
    live_raw: list[int],
    record_width: int,
) -> list[str]:
    fields: list[str] = []
    for side in ("L", "R"):
        fields.extend(f"{side}.x[{q}]" for q in qubit_ids)
        fields.extend(f"{side}.z[{q}]" for q in qubit_ids)
    fields.append("latent_m")
    if observable_live:
        fields.append("observable_0_accumulator")
    fields.extend(f"live_raw[{raw}]" for raw in live_raw)
    fields.extend(f"record[{index}]" for index in range(record_width))
    return fields


def _action(opcode: str, qubits: list[int] | None = None, *parameters: str) -> dict[str, Any]:
    return {
        "opcode": opcode,
        "qubits": [] if qubits is None else list(qubits),
        "parameters": list(parameters),
    }


def _classical(
    opcode: str,
    *,
    raw_output: int | None = None,
    rec_operands: list[dict[str, int]] | None = None,
    record_output: dict[str, int] | None = None,
) -> dict[str, Any]:
    return {
        "opcode": opcode,
        "raw_output": raw_output,
        "rec_operands": [] if rec_operands is None else deepcopy(rec_operands),
        "record_output": None if record_output is None else dict(record_output),
    }


def _multipliers(value_by_m: dict[int, Qsqrt2i] | None = None) -> list[dict[str, Any]]:
    values = {-1: ONE, 1: ONE} if value_by_m is None else value_by_m
    return [
        {"latent_m": latent, "coefficient": values[latent].to_data()}
        for latent in (-1, 1)
    ]


def _component_row(
    *,
    branch: list[dict[str, int]] | None = None,
    left_action: dict[str, Any] | None = None,
    right_action: dict[str, Any] | None = None,
    reference_action: dict[str, Any] | None = None,
    classical_action: dict[str, Any] | None = None,
    value_by_m: dict[int, Qsqrt2i] | None = None,
) -> dict[str, Any]:
    return {
        "branch": [] if branch is None else branch,
        "input_predicates": [],
        "left_action": _action("IDENTITY") if left_action is None else left_action,
        "right_action": _action("IDENTITY") if right_action is None else right_action,
        "reference_action": (
            _action("IDENTITY") if reference_action is None else reference_action
        ),
        "classical_action": (
            _classical("IDENTITY") if classical_action is None else classical_action
        ),
        "multiplier_by_latent": _multipliers(value_by_m),
    }


def _coherent_rows(event: dict[str, Any]) -> list[dict[str, Any]]:
    q = event["qubits"][0]["dense_ordinal"]
    rows: list[dict[str, Any]] = []
    for left in (0, 1):
        for right in (0, 1):
            values: dict[int, Qsqrt2i] = {}
            for latent in (-1, 1):
                left_value = ONE if not left else _q_scale(I * _S, -latent)
                right_value = ONE if not right else _q_scale(I * _S, latent)
                values[latent] = (
                    left_value
                    * right_value
                    * _q_power(_C, 2 - left - right)
                )
            rows.append(
                _component_row(
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
                    value_by_m=values,
                )
            )
    return rows


def _instrument_components(kind: str, branch: int) -> list[tuple[str, Qsqrt2i]]:
    if kind == "M":
        return [
            ("I", _HALF),
            ("Z", _HALF if branch == 0 else _q_scale(_HALF, -1)),
        ]
    if branch == 0:
        return [("I", _HALF), ("Z", _HALF)]
    return [("X", _HALF), ("Y", I * _HALF)]


def _instrument_rows(event: dict[str, Any]) -> list[dict[str, Any]]:
    kind = event["kind"]
    q = event["qubits"][0]["dense_ordinal"]
    rows: list[dict[str, Any]] = []
    for branch in (0, 1):
        components = _instrument_components(kind, branch)
        for left_index, (left_pauli, left_value) in enumerate(components):
            for right_index, (right_pauli, right_value) in enumerate(components):
                multiplier = left_value * _q_conjugate(right_value)
                rows.append(
                    _component_row(
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
                        classical_action=_classical(
                            "SUM_KRAUS_BRANCH"
                            if kind == "RESET"
                            else "EMIT_RAW_BRANCH",
                            raw_output=(
                                None if kind == "RESET" else event["raw_output"]
                            ),
                        ),
                        value_by_m={-1: multiplier, 1: multiplier},
                    )
                )
    return rows


def _kernel_rows(event: dict[str, Any]) -> list[dict[str, Any]]:
    kind = event["kind"]
    dense_qubits = [q["dense_ordinal"] for q in event["qubits"]]
    if kind == "COHERENT_Z":
        rows = _coherent_rows(event)
    elif kind in {"RESET", "M", "MR"}:
        rows = _instrument_rows(event)
    elif kind == "H":
        rows = [
            _component_row(
                left_action=_action("CONJUGATE_H", dense_qubits),
                right_action=_action("CONJUGATE_H", dense_qubits),
                reference_action=_action("CONJUGATE_REFERENCE_H", dense_qubits),
            )
        ]
    elif kind == "CX":
        rows = [
            _component_row(
                left_action=_action("CONJUGATE_CX", dense_qubits),
                right_action=_action("CONJUGATE_CX", dense_qubits),
                reference_action=_action("CONJUGATE_REFERENCE_CX", dense_qubits),
            )
        ]
    else:
        opcode = {
            "DETECTOR_APPEND": "APPEND_DETECTOR_XOR",
            "OBSERVABLE_XOR": "ACCUMULATE_OBSERVABLE_XOR",
            "FINALIZE_RECORD": "APPEND_OBSERVABLE",
        }.get(kind, "IDENTITY")
        rows = [
            _component_row(
                classical_action=_classical(
                    opcode,
                    raw_output=event["raw_output"],
                    rec_operands=event["rec_operands"],
                    record_output=event["record_output"],
                )
            )
        ]
    rows.sort(key=canonical_json_bytes)
    return rows


def build_exact_pair_transition_program(neutral: StaticArtifact) -> StaticArtifact:
    """Compile complete static pair semantics without executing a recurrence."""

    if not isinstance(neutral, StaticArtifact):
        raise TypeError("pair lowering requires a neutral static artifact")
    # The pair owner may receive an in-memory StaticArtifact assembled by a
    # caller.  Authenticate the complete neutral semantic payload against the
    # frozen fixture before consuming any event, qubit, or source field.
    from .neutral import validate_declared_error_record_program

    neutral = validate_declared_error_record_program(neutral.to_data())
    neutral_data = neutral.to_data()
    source = neutral_data["semantic"]
    events = source["events"]
    qubit_ids = [entry["stim_id"] for entry in source["qubits"]]
    n = len(qubit_ids)

    stabilizers: list[dict[str, Any]] = []
    for q in range(n):
        x = [0] * n
        z = [0] * n
        z[q] = 1
        stabilizers.append(_signed_row(x, z))

    last_use: dict[int, int] = {}
    producer: dict[int, int] = {}
    for event_index, event in enumerate(events):
        if event["raw_output"] is not None:
            producer[event["raw_output"]] = event_index
        for operand in event["rec_operands"]:
            last_use[operand["absolute_raw_ordinal"]] = event_index

    basis_catalog: list[dict[str, Any]] = []
    basis_by_id: dict[str, dict[str, Any]] = {}
    basis_by_state: dict[tuple[tuple[int, ...], ...], dict[str, Any]] = {}

    def register_basis(rows: list[dict[str, Any]]) -> dict[str, Any]:
        state_key = tuple(
            tuple(row["x"] + row["z"] + [row["phase_mod4"]]) for row in rows
        )
        if state_key in basis_by_state:
            return basis_by_state[state_key]
        basis = _basis(rows)
        existing = basis_by_id.get(basis["basis_id"])
        if existing is not None and canonical_json_bytes(existing) != canonical_json_bytes(
            basis
        ):
            raise ValueError("basis ID collision binds unequal signed-basis payloads")
        if existing is None:
            basis_by_id[basis["basis_id"]] = basis
            basis_catalog.append(basis)
        basis_by_state[state_key] = basis_by_id[basis["basis_id"]]
        return basis_by_state[state_key]

    record_width = 0
    checkpoints: list[dict[str, Any]] = []

    def append_checkpoint(
        *, ordinal: int, after_event_id: str | None, event_index: int
    ) -> None:
        basis = register_basis(stabilizers)
        live_raw = sorted(
            raw
            for raw, produced_at in producer.items()
            if produced_at <= event_index and last_use.get(raw, -1) > event_index
        )
        observable_live = ordinal <= len(events) - 1
        fields = _codec_fields(
            qubit_ids=qubit_ids,
            observable_live=observable_live,
            live_raw=live_raw,
            record_width=record_width,
        )
        pivot_zero_fields = [
            _field_for_column(side, pivot, qubit_ids)
            for side in ("L", "R")
            for pivot in basis["pivots"]
        ]
        checkpoints.append(
            {
                "ordinal": ordinal,
                "after_event_id": after_event_id,
                "basis_id": basis["basis_id"],
                "codec_fields": fields,
                "validity": {
                    "pivot_zero_fields": pivot_zero_fields,
                    "inactive_zero_fields": [],
                    "latent_values": [-1, 1],
                    "record_width": record_width,
                },
                "live_raw": live_raw,
                "record_width": record_width,
            }
        )

    append_checkpoint(ordinal=0, after_event_id=None, event_index=-1)
    for event_index, event in enumerate(events):
        if event["kind"] == "H":
            q = event["qubits"][0]["dense_ordinal"]
            stabilizers = [_conjugate_h(row, q) for row in stabilizers]
        elif event["kind"] == "CX":
            control, target = [
                item["dense_ordinal"] for item in event["qubits"]
            ]
            stabilizers = [
                _conjugate_cx(row, control, target) for row in stabilizers
            ]
        if event["record_output"] is not None:
            record_width += 1
        append_checkpoint(
            ordinal=event_index + 1,
            after_event_id=event["event_id"],
            event_index=event_index,
        )

    kernels: list[dict[str, Any]] = []
    for event_index, event in enumerate(events):
        payload = {
            "event_id": event["event_id"],
            "kind": event["kind"],
            "input_checkpoint": event_index,
            "output_checkpoint": event_index + 1,
            "component_rows": _kernel_rows(event),
        }
        kernels.append({**payload, "semantic_sha256": sha256_json(payload)})

    zero = _zero_pauli(n)
    initial_terms = [
        {
            "coefficient": _HALF.to_data(),
            "latent_m": latent,
            "left": deepcopy(zero),
            "right": deepcopy(zero),
            "observable_accumulator": 0,
            "live_raw": [],
            "record": [],
        }
        for latent in (-1, 1)
    ]
    semantic = {
        "neutral_sha256": neutral.sha256,
        "algebra": {
            "name": "Q(sqrt(2),i)",
            "coefficient_order": "[a,b,c,d]",
            "rational_encoding": "[reduced_numerator,positive_denominator]",
            "zero_policy": "exact_only",
        },
        "pauli_convention": deepcopy(_PAULI_CONVENTION),
        "initial_terms": initial_terms,
        "basis_catalog": basis_catalog,
        "checkpoints": checkpoints,
        "kernels": kernels,
    }
    return StaticArtifact(PAIR_SCHEMA, semantic)


def validate_exact_pair_transition_program(
    data: object, *, neutral: StaticArtifact
) -> StaticArtifact:
    """Strictly reload a pair program against its frozen neutral owner."""

    validate_static_envelope(
        data,
        schema=PAIR_SCHEMA,
        semantic_keys={
            "neutral_sha256",
            "algebra",
            "pauli_convention",
            "initial_terms",
            "basis_catalog",
            "checkpoints",
            "kernels",
        },
    )
    expected = build_exact_pair_transition_program(neutral)
    if canonical_json_bytes(data) != canonical_json_bytes(expected.to_data()):
        raise ValueError("pair artifact does not reproduce frozen semantic identity")
    return expected


def _witness_kernel_rows(
    kind: str, qubits: list[int], *, branch: int | None = None
) -> list[dict[str, Any]]:
    """Reuse the owner kernel semantics without constructing or advancing a state."""

    event = {
        "kind": kind,
        "qubits": [{"dense_ordinal": qubit} for qubit in qubits],
        "raw_output": 0 if kind in {"M", "MR"} else None,
        "rec_operands": [],
        "record_output": None,
    }
    rows = _kernel_rows(event)
    if branch is not None:
        rows = [
            row
            for row in rows
            if row["branch"]
            and row["branch"][0] == {"name": "b", "value": branch}
        ]
    return sorted(deepcopy(rows), key=canonical_json_bytes)


def build_pair_witness_component_catalog(witness_id: str) -> list[dict[str, Any]]:
    """Build the frozen P1/P2 finite component catalogs without a frontier.

    Each entry binds one complete input Pauli pair to the component rows of one
    local owner kernel.  This is deliberately a static truth-table surface: it
    neither canonicalizes an output pair nor accumulates equal output terms.
    """

    paulis = ("I", "X", "Y", "Z")
    if witness_id == "P1":
        operations = (
            ("identity", _witness_kernel_rows("COORD_MARKER", [])),
            ("H", _witness_kernel_rows("H", [0])),
            ("COHERENT_Z", _witness_kernel_rows("COHERENT_Z", [0])),
            ("R", _witness_kernel_rows("RESET", [0])),
            ("M(b=0)", _witness_kernel_rows("M", [0], branch=0)),
            ("M(b=1)", _witness_kernel_rows("M", [0], branch=1)),
            ("MR(b=0)", _witness_kernel_rows("MR", [0], branch=0)),
            ("MR(b=1)", _witness_kernel_rows("MR", [0], branch=1)),
        )
        catalog = [
            {
                "witness_id": witness_id,
                "reference": "0",
                "left_pauli": left,
                "right_pauli": right,
                "latent_m": latent,
                "operation_id": operation_id,
                "component_rows": deepcopy(component_rows),
            }
            for left in paulis
            for right in paulis
            for latent in (-1, 1)
            for operation_id, component_rows in operations
        ]
    elif witness_id == "P2":
        two_qubit_paulis = tuple(
            left + right for left in paulis for right in paulis
        )
        operations = (
            ("H(q=0)", _witness_kernel_rows("H", [0])),
            ("H(q=1)", _witness_kernel_rows("H", [1])),
            ("CX(control=0,target=1)", _witness_kernel_rows("CX", [0, 1])),
            ("CX(control=1,target=0)", _witness_kernel_rows("CX", [1, 0])),
        )
        catalog = [
            {
                "witness_id": witness_id,
                "reference": "00",
                "left_pauli": left,
                "right_pauli": right,
                "operation_id": operation_id,
                "component_rows": deepcopy(component_rows),
            }
            for left in two_qubit_paulis
            for right in two_qubit_paulis
            for operation_id, component_rows in operations
        ]
    else:
        raise ValueError("pair witness id must be exactly 'P1' or 'P2'")

    # This order is part of the frozen witness, not a generic JSON sort:
    # left Pauli, right Pauli, latent codec bit (P1), then listed operation.
    return catalog


def _coset_witness_stabilizers(witness_id: str) -> list[dict[str, Any]]:
    definitions = {
        "C1": [([0], [1])],
        "C2": [([1], [0])],
        "C3": [([1, 1], [0, 0]), ([0, 0], [1, 1])],
        "C4": [
            ([1, 1, 1], [0, 0, 0]),
            ([0, 0, 0], [1, 1, 0]),
            ([0, 0, 0], [0, 1, 1]),
        ],
    }
    try:
        return [_signed_row(x, z) for x, z in definitions[witness_id]]
    except KeyError as exc:
        raise ValueError("coset witness id must be one of C1, C2, C3, C4") from exc


def _reduce_signed_witness_row(
    signed_pauli: dict[str, Any], basis: dict[str, Any], *, side: str
) -> dict[str, Any]:
    current = deepcopy(signed_pauli)
    for pivot, stabilizer in zip(
        basis["pivots"], basis["rref_rows"], strict=True
    ):
        if not _row_bits(current)[pivot]:
            continue
        current = (
            _multiply_rows(current, stabilizer)
            if side == "ket"
            else _multiply_rows(stabilizer, current)
        )
    if any(_row_bits(current)[pivot] for pivot in basis["pivots"]):
        raise AssertionError("coset witness reduction left a pivot bit")
    return {
        "representative": {"x": current["x"], "z": current["z"]},
        "coefficient_phase_mod4": current["phase_mod4"],
    }


def _coset_reference_vector(witness_id: str) -> list[Qsqrt2i]:
    zero = Qsqrt2i.rational(0)
    if witness_id == "C1":
        return [ONE, zero]
    half_sqrt2 = Qsqrt2i.sqrt2(Fraction(1, 2))
    if witness_id == "C2":
        return [half_sqrt2, half_sqrt2]
    if witness_id == "C3":
        return [half_sqrt2, zero, zero, half_sqrt2]
    if witness_id == "C4":
        return [half_sqrt2, zero, zero, zero, zero, zero, zero, half_sqrt2]
    raise ValueError("coset witness id must be one of C1, C2, C3, C4")


def _i_power(exponent: int) -> Qsqrt2i:
    return _q_power(I, exponent % 4)


def _realize_signed_pauli(
    row: dict[str, Any], reference: list[Qsqrt2i], *, side: str
) -> list[list[list[int]]]:
    qubit_count = len(row["x"])
    if len(reference) != 1 << qubit_count:
        raise ValueError("coset reference vector width mismatch")
    local_phase = row["phase_mod4"] + sum(
        x * z for x, z in zip(row["x"], row["z"], strict=True)
    )
    zero = Qsqrt2i.rational(0)
    result = [zero for _ in reference]
    x_mask = sum(
        bit << (qubit_count - qubit - 1)
        for qubit, bit in enumerate(row["x"])
    )
    for input_index in range(1 << qubit_count):
        bits = [
            (input_index >> (qubit_count - qubit - 1)) & 1
            for qubit in range(qubit_count)
        ]
        sign = -1 if sum(
            z * bit for z, bit in zip(row["z"], bits, strict=True)
        ) % 2 else 1
        coefficient = _q_scale(_i_power(local_phase), sign)
        output_index = input_index ^ x_mask
        if side == "ket":
            result[output_index] = result[output_index] + (
                coefficient * reference[input_index]
            )
        else:
            # The frozen reference amplitudes are real.  This computes the
            # complete row covector <psi|P one input column at a time.
            result[input_index] = result[input_index] + (
                reference[output_index] * coefficient
            )
    return [value.to_data() for value in result]


def _pauli_word(row: dict[str, Any]) -> str:
    letters = {(0, 0): "I", (1, 0): "X", (1, 1): "Y", (0, 1): "Z"}
    return "".join(
        letters[(x, z)] for x, z in zip(row["x"], row["z"], strict=True)
    )


def build_coset_witness_rows(
    witness_id: str, *, side: str
) -> list[dict[str, Any]]:
    """Enumerate the complete frozen signed-coset witness catalog."""

    if side not in {"ket", "bra"}:
        raise ValueError("side must be exactly 'ket' or 'bra'")
    stabilizers = _coset_witness_stabilizers(witness_id)
    qubit_count = len(stabilizers)
    basis = _basis(stabilizers)
    reference = _coset_reference_vector(witness_id)
    basis_order = [
        format(index, f"0{qubit_count}b") for index in range(1 << qubit_count)
    ]
    rows: list[dict[str, Any]] = []
    for bits in product((0, 1), repeat=2 * qubit_count):
        physical = _signed_row(
            list(bits[:qubit_count]), list(bits[qubit_count:])
        )
        for raw_mask in product((0, 1), repeat=qubit_count):
            mask = list(raw_mask)
            stabilizer_product = _signed_row(
                [0] * qubit_count, [0] * qubit_count
            )
            for selected, stabilizer in zip(mask, stabilizers, strict=True):
                if selected:
                    stabilizer_product = _multiply_rows(
                        stabilizer_product, stabilizer
                    )
            oriented = (
                _multiply_rows(physical, stabilizer_product)
                if side == "ket"
                else _multiply_rows(stabilizer_product, physical)
            )
            first = _reduce_signed_witness_row(oriented, basis, side=side)
            second_input = _signed_row(
                first["representative"]["x"],
                first["representative"]["z"],
                first["coefficient_phase_mod4"],
            )
            second = _reduce_signed_witness_row(second_input, basis, side=side)
            physical_action = _realize_signed_pauli(
                physical, reference, side=side
            )
            oriented_action = _realize_signed_pauli(
                oriented, reference, side=side
            )
            reduced_action = _realize_signed_pauli(
                second_input, reference, side=side
            )
            if not physical_action == oriented_action == reduced_action:
                raise AssertionError("signed coset witness changed the realized action")
            rows.append(
                {
                    "witness_id": witness_id,
                    "side": side,
                    "physical_pauli": {
                        "x": physical["x"],
                        "z": physical["z"],
                    },
                    "physical_pauli_word": _pauli_word(physical),
                    "stabilizer_mask": mask,
                    "stabilizer_product": stabilizer_product,
                    "oriented_product": oriented,
                    "first_reduction": first,
                    "second_reduction": second,
                    "realized_action": {
                        "kind": (
                            "state_vector" if side == "ket" else "state_covector"
                        ),
                        "basis_order": basis_order,
                        "physical": physical_action,
                        "oriented_product": oriented_action,
                        "reduced": reduced_action,
                    },
                }
            )
    return rows
