"""Independent signed-stabilizer checkpoint reconstruction.

This oracle intentionally depends only on the Python standard library.  In
particular, it does not reuse the target owner, neutral lowering, coefficient
model, or the earlier micro-owner implementation.
"""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import hashlib
from itertools import product
import json
from typing import Any, Iterator, Mapping, Sequence


# If ``P(x, z) = i**(x*z) X**x Z**z`` on one qubit, this table gives the
# additional power of i in ``P(left) P(right)`` relative to
# ``P(left xor right)``.  Keeping the finite multiplication table here makes
# this reconstruction algebraically independent of the owner's bit formula.
_LOCAL_PRODUCT_PHASE = {
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


def _row(
    x: Sequence[int], z: Sequence[int], phase_mod4: int = 0
) -> dict[str, Any]:
    if len(x) != len(z):
        raise ValueError("Pauli x/z widths differ")
    if any(type(bit) is not int or bit not in (0, 1) for bit in (*x, *z)):
        raise ValueError("Pauli coordinates must be bits")
    if type(phase_mod4) is not int or phase_mod4 not in range(4):
        raise ValueError("Pauli phase must be an integer modulo four")
    return {
        "x": list(x),
        "z": list(z),
        "phase_mod4": phase_mod4,
    }


def _multiply(left: Mapping[str, Any], right: Mapping[str, Any]) -> dict[str, Any]:
    """Multiply two signed Pauli rows using the finite one-qubit table."""

    lx = list(left["x"])
    lz = list(left["z"])
    rx = list(right["x"])
    rz = list(right["z"])
    if not (len(lx) == len(lz) == len(rx) == len(rz)):
        raise ValueError("Pauli row widths differ")

    phase = int(left["phase_mod4"]) + int(right["phase_mod4"])
    out_x: list[int] = []
    out_z: list[int] = []
    for left_x, left_z, right_x, right_z in zip(
        lx, lz, rx, rz, strict=True
    ):
        phase += _LOCAL_PRODUCT_PHASE[
            ((left_x, left_z), (right_x, right_z))
        ]
        out_x.append(left_x ^ right_x)
        out_z.append(left_z ^ right_z)
    return _row(out_x, out_z, phase % 4)


def _commutes(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    lx = list(left["x"])
    lz = list(left["z"])
    rx = list(right["x"])
    rz = list(right["z"])
    if not (len(lx) == len(lz) == len(rx) == len(rz)):
        raise ValueError("Pauli row widths differ")
    symplectic_inner_product = sum(
        (left_x * right_z) + (left_z * right_x)
        for left_x, left_z, right_x, right_z in zip(
            lx, lz, rx, rz, strict=True
        )
    )
    return symplectic_inner_product % 2 == 0


def _multiply_commuting(
    left: Mapping[str, Any], right: Mapping[str, Any]
) -> dict[str, Any]:
    if not _commutes(left, right):
        raise ValueError("RREF row multiplication requires commuting Paulis")
    return _multiply(left, right)


def _conjugate_h(row: Mapping[str, Any], qubit: int) -> dict[str, Any]:
    result = deepcopy(dict(row))
    x = result["x"][qubit]
    z = result["z"][qubit]
    # H Y H = -Y, while H swaps X and Z without a sign.
    if (x, z) == (1, 1):
        result["phase_mod4"] = (result["phase_mod4"] + 2) % 4
    result["x"][qubit], result["z"][qubit] = z, x
    return result


def _generator_image(
    width: int, *, x_qubits: Sequence[int] = (), z_qubits: Sequence[int] = ()
) -> dict[str, Any]:
    x = [0] * width
    z = [0] * width
    for qubit in x_qubits:
        x[qubit] ^= 1
    for qubit in z_qubits:
        z[qubit] ^= 1
    return _row(x, z)


def _conjugate_control_first_cx(
    row: Mapping[str, Any], control: int, target: int
) -> dict[str, Any]:
    """Conjugate via the four CNOT generator images, control first.

    Rather than reuse a tableau phase formula, this expands the two affected
    canonical Pauli factors in operator order and maps
    ``Xc -> Xc Xt``, ``Zc -> Zc``, ``Xt -> Xt``, and
    ``Zt -> Zc Zt``.
    """

    if control == target:
        raise ValueError("CX control and target must differ")
    width = len(row["x"])
    control_x = int(row["x"][control])
    control_z = int(row["z"][control])
    target_x = int(row["x"][target])
    target_z = int(row["z"][target])

    local = _row(
        [0] * width,
        [0] * width,
        (control_x * control_z + target_x * target_z) % 4,
    )
    if control_x:
        local = _multiply(
            local,
            _generator_image(width, x_qubits=(control, target)),
        )
    if control_z:
        local = _multiply(
            local,
            _generator_image(width, z_qubits=(control,)),
        )
    if target_x:
        local = _multiply(
            local,
            _generator_image(width, x_qubits=(target,)),
        )
    if target_z:
        local = _multiply(
            local,
            _generator_image(width, z_qubits=(control, target)),
        )

    result = deepcopy(dict(row))
    result["x"][control] = local["x"][control]
    result["z"][control] = local["z"][control]
    result["x"][target] = local["x"][target]
    result["z"][target] = local["z"][target]
    result["phase_mod4"] = (
        int(row["phase_mod4"]) + int(local["phase_mod4"])
    ) % 4
    return result


def _bits(row: Mapping[str, Any]) -> list[int]:
    return list(row["x"]) + list(row["z"])


def _assert_commuting_full_width(
    stabilizers: Sequence[Mapping[str, Any]], qubit_count: int
) -> None:
    if len(stabilizers) != qubit_count:
        raise ValueError("reference stabilizer count differs from qubit count")
    for index, stabilizer in enumerate(stabilizers):
        if len(stabilizer["x"]) != qubit_count or len(stabilizer["z"]) != qubit_count:
            raise ValueError(f"reference stabilizer {index} has the wrong width")
        if stabilizer["phase_mod4"] not in (0, 2):
            raise ValueError(f"reference stabilizer {index} is not Hermitian")
        for earlier in stabilizers[:index]:
            if not _commutes(stabilizer, earlier):
                raise ValueError("reference stabilizers do not commute")


def _full_rref(
    stabilizers: Sequence[Mapping[str, Any]], qubit_count: int
) -> tuple[list[dict[str, Any]], list[int]]:
    """Return deterministic full GF(2) RREF with signed row products."""

    _assert_commuting_full_width(stabilizers, qubit_count)
    rows = [deepcopy(dict(row)) for row in stabilizers]
    pivots: list[int] = []
    next_pivot_row = 0

    for column in range(2 * qubit_count):
        selected = None
        for candidate in range(next_pivot_row, len(rows)):
            if _bits(rows[candidate])[column] == 1:
                selected = candidate
                break
        if selected is None:
            continue

        rows[next_pivot_row], rows[selected] = (
            rows[selected],
            rows[next_pivot_row],
        )
        pivot = rows[next_pivot_row]
        for row_index in range(len(rows)):
            if row_index == next_pivot_row:
                continue
            if _bits(rows[row_index])[column] == 1:
                # Stabilizer rows commute, so using pivot * row is exact and
                # deliberately differs in implementation order from the owner.
                rows[row_index] = _multiply_commuting(pivot, rows[row_index])

        pivots.append(column)
        next_pivot_row += 1
        if next_pivot_row == qubit_count:
            break

    if len(pivots) != qubit_count:
        raise ValueError("reference stabilizer matrix lost rank")
    _assert_commuting_full_width(rows, qubit_count)
    return rows, pivots


def _checkpoint(
    stabilizers: Sequence[Mapping[str, Any]], qubit_count: int
) -> dict[str, Any]:
    rref_rows, pivots = _full_rref(stabilizers, qubit_count)
    return {
        "stabilizers": [deepcopy(dict(row)) for row in stabilizers],
        "rref_rows": rref_rows,
        "pivots": pivots,
    }


def independent_signed_rref_basis(
    stabilizers: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build an independently checked signed stabilizer RREF basis."""

    if isinstance(stabilizers, (str, bytes)) or not isinstance(
        stabilizers, Sequence
    ):
        raise TypeError("stabilizers must be a sequence of signed Pauli rows")
    if not stabilizers:
        raise ValueError("a signed stabilizer basis must be nonempty")

    normalized: list[dict[str, Any]] = []
    for stabilizer in stabilizers:
        if not isinstance(stabilizer, Mapping):
            raise TypeError("each stabilizer must be an object")
        try:
            normalized.append(
                _row(
                    stabilizer["x"],
                    stabilizer["z"],
                    stabilizer["phase_mod4"],
                )
            )
        except KeyError as exc:
            raise ValueError("a stabilizer row is missing x, z, or phase_mod4") from exc

    qubit_count = len(normalized[0]["x"])
    if qubit_count <= 0:
        raise ValueError("a signed stabilizer basis must have positive width")
    return _checkpoint(normalized, qubit_count)


def canonicalize_pauli_independently(
    pauli: Mapping[str, Any],
    basis: Mapping[str, Any],
    *,
    side: str,
) -> dict[str, Any]:
    """Reduce a Pauli coset and return the exact absorbed phase.

    Ket representatives eliminate each pivot by right multiplication
    ``P * S``.  Bra representatives use left multiplication ``S * P``.
    The returned phase is the power of ``i`` multiplying the resulting
    phase-free representative.
    """

    if side not in {"ket", "bra"}:
        raise ValueError("side must be exactly 'ket' or 'bra'")
    if not isinstance(pauli, Mapping):
        raise TypeError("pauli must be an object")
    if not isinstance(basis, Mapping):
        raise TypeError("basis must be an object")

    try:
        current = _row(pauli["x"], pauli["z"])
        supplied_stabilizers = basis["stabilizers"]
        supplied_rref_rows = basis["rref_rows"]
        supplied_pivots = basis["pivots"]
    except KeyError as exc:
        raise ValueError("pauli or basis is missing a required field") from exc

    reconstructed = independent_signed_rref_basis(supplied_stabilizers)
    supplied_payload = {
        "stabilizers": supplied_stabilizers,
        "rref_rows": supplied_rref_rows,
        "pivots": supplied_pivots,
    }
    if supplied_payload != reconstructed:
        raise ValueError("basis does not match independent signed RREF")
    if len(current["x"]) != len(reconstructed["stabilizers"]):
        raise ValueError("Pauli width differs from the stabilizer basis")

    for pivot, stabilizer in zip(
        reconstructed["pivots"], reconstructed["rref_rows"], strict=True
    ):
        if _bits(current)[pivot] == 0:
            continue
        if side == "ket":
            current = _multiply(current, stabilizer)
        else:
            current = _multiply(stabilizer, current)

    if any(_bits(current)[pivot] for pivot in reconstructed["pivots"]):
        raise ValueError("coset reduction failed to clear every pivot")
    return {
        "representative": {
            "x": list(current["x"]),
            "z": list(current["z"]),
        },
        "coefficient_phase_mod4": int(current["phase_mod4"]),
    }


def _coset_stabilizers(witness_id: str) -> list[dict[str, Any]]:
    definitions = {
        "C1": [((0,), (1,))],
        "C2": [((1,), (0,))],
        "C3": [((1, 1), (0, 0)), ((0, 0), (1, 1))],
        "C4": [
            ((1, 1, 1), (0, 0, 0)),
            ((0, 0, 0), (1, 1, 0)),
            ((0, 0, 0), (0, 1, 1)),
        ],
    }
    if witness_id not in definitions:
        raise ValueError("coset witness id must be one of C1, C2, C3, C4")
    return [_row(x, z) for x, z in definitions[witness_id]]


def _reduce_signed_coset_row(
    signed_pauli: Mapping[str, Any], basis: Mapping[str, Any], *, side: str
) -> dict[str, Any]:
    if side not in {"ket", "bra"}:
        raise ValueError("side must be exactly 'ket' or 'bra'")
    current = _row(
        signed_pauli["x"],
        signed_pauli["z"],
        signed_pauli["phase_mod4"],
    )
    for pivot, stabilizer in zip(
        basis["pivots"], basis["rref_rows"], strict=True
    ):
        if not _bits(current)[pivot]:
            continue
        current = (
            _multiply(current, stabilizer)
            if side == "ket"
            else _multiply(stabilizer, current)
        )
    if any(_bits(current)[pivot] for pivot in basis["pivots"]):
        raise AssertionError("independent coset reduction left a pivot bit")
    return {
        "representative": {
            "x": list(current["x"]),
            "z": list(current["z"]),
        },
        "coefficient_phase_mod4": current["phase_mod4"],
    }


_ExactAmplitude = tuple[Fraction, Fraction, Fraction, Fraction]
_AMP_ZERO: _ExactAmplitude = (Fraction(0),) * 4
_AMP_ONE: _ExactAmplitude = (
    Fraction(1),
    Fraction(0),
    Fraction(0),
    Fraction(0),
)
_AMP_I: _ExactAmplitude = (
    Fraction(0),
    Fraction(0),
    Fraction(1),
    Fraction(0),
)
_AMP_SQRT2_HALF: _ExactAmplitude = (
    Fraction(0),
    Fraction(1, 2),
    Fraction(0),
    Fraction(0),
)


def _amp_add(left: _ExactAmplitude, right: _ExactAmplitude) -> _ExactAmplitude:
    return tuple(
        left_value + right_value
        for left_value, right_value in zip(left, right, strict=True)
    )  # type: ignore[return-value]


def _amp_mul(left: _ExactAmplitude, right: _ExactAmplitude) -> _ExactAmplitude:
    a, b, c, d = left
    e, f, g, h = right
    return (
        a * e + 2 * b * f - c * g - 2 * d * h,
        a * f + b * e - c * h - d * g,
        a * g + 2 * b * h + c * e + 2 * d * f,
        a * h + b * g + c * f + d * e,
    )


def _amp_i_power(exponent: int) -> _ExactAmplitude:
    result = _AMP_ONE
    for _ in range(exponent % 4):
        result = _amp_mul(result, _AMP_I)
    return result


def _amp_data(value: _ExactAmplitude) -> list[list[int]]:
    return [
        [coordinate.numerator, coordinate.denominator] for coordinate in value
    ]


def _coset_reference_amplitudes(witness_id: str) -> list[_ExactAmplitude]:
    if witness_id == "C1":
        return [_AMP_ONE, _AMP_ZERO]
    if witness_id == "C2":
        return [_AMP_SQRT2_HALF, _AMP_SQRT2_HALF]
    if witness_id == "C3":
        return [
            _AMP_SQRT2_HALF,
            _AMP_ZERO,
            _AMP_ZERO,
            _AMP_SQRT2_HALF,
        ]
    if witness_id == "C4":
        return [
            _AMP_SQRT2_HALF,
            _AMP_ZERO,
            _AMP_ZERO,
            _AMP_ZERO,
            _AMP_ZERO,
            _AMP_ZERO,
            _AMP_ZERO,
            _AMP_SQRT2_HALF,
        ]
    raise ValueError("coset witness id must be one of C1, C2, C3, C4")


def _local_pauli_transition(x: int, z: int, input_bit: int) -> tuple[int, int]:
    """Return output bit and phase exponent from a literal four-Pauli table."""

    table = {
        (0, 0, 0): (0, 0),
        (0, 0, 1): (1, 0),
        (1, 0, 0): (1, 0),
        (1, 0, 1): (0, 0),
        (1, 1, 0): (1, 1),
        (1, 1, 1): (0, 3),
        (0, 1, 0): (0, 0),
        (0, 1, 1): (1, 2),
    }
    return table[(x, z, input_bit)]


def _realize_coset_operator(
    row: Mapping[str, Any],
    reference: Sequence[_ExactAmplitude],
    *,
    side: str,
) -> list[list[list[int]]]:
    qubit_count = len(row["x"])
    if len(reference) != 1 << qubit_count:
        raise ValueError("independent coset reference width mismatch")
    result = [_AMP_ZERO for _ in reference]
    for input_index in range(1 << qubit_count):
        input_bits = [
            (input_index >> (qubit_count - qubit - 1)) & 1
            for qubit in range(qubit_count)
        ]
        output_bits: list[int] = []
        phase = int(row["phase_mod4"])
        for x, z, input_bit in zip(
            row["x"], row["z"], input_bits, strict=True
        ):
            output_bit, local_phase = _local_pauli_transition(x, z, input_bit)
            output_bits.append(output_bit)
            phase += local_phase
        output_index = sum(
            bit << (qubit_count - qubit - 1)
            for qubit, bit in enumerate(output_bits)
        )
        coefficient = _amp_i_power(phase)
        if side == "ket":
            result[output_index] = _amp_add(
                result[output_index],
                _amp_mul(coefficient, reference[input_index]),
            )
        else:
            result[input_index] = _amp_add(
                result[input_index],
                _amp_mul(reference[output_index], coefficient),
            )
    return [_amp_data(value) for value in result]


def _coset_pauli_word(row: Mapping[str, Any]) -> str:
    labels = {(0, 0): "I", (1, 0): "X", (1, 1): "Y", (0, 1): "Z"}
    return "".join(
        labels[(x, z)] for x, z in zip(row["x"], row["z"], strict=True)
    )


def reconstruct_coset_witness_rows(
    witness_id: str, *, side: str
) -> list[dict[str, Any]]:
    """Independently enumerate all physical-Pauli/stabilizer-mask products."""

    if side not in {"ket", "bra"}:
        raise ValueError("side must be exactly 'ket' or 'bra'")
    stabilizers = _coset_stabilizers(witness_id)
    qubit_count = len(stabilizers)
    basis = independent_signed_rref_basis(stabilizers)
    reference = _coset_reference_amplitudes(witness_id)
    basis_order = [
        format(index, f"0{qubit_count}b") for index in range(1 << qubit_count)
    ]
    rows: list[dict[str, Any]] = []
    for bits in product((0, 1), repeat=2 * qubit_count):
        physical = _row(bits[:qubit_count], bits[qubit_count:])
        for raw_mask in product((0, 1), repeat=qubit_count):
            mask = list(raw_mask)
            stabilizer_product = _row(
                [0] * qubit_count, [0] * qubit_count
            )
            for selected, stabilizer in zip(mask, stabilizers, strict=True):
                if selected:
                    stabilizer_product = _multiply(
                        stabilizer_product, stabilizer
                    )
            oriented = (
                _multiply(physical, stabilizer_product)
                if side == "ket"
                else _multiply(stabilizer_product, physical)
            )
            first = _reduce_signed_coset_row(oriented, basis, side=side)
            second_input = _row(
                first["representative"]["x"],
                first["representative"]["z"],
                first["coefficient_phase_mod4"],
            )
            second = _reduce_signed_coset_row(second_input, basis, side=side)
            physical_action = _realize_coset_operator(
                physical, reference, side=side
            )
            oriented_action = _realize_coset_operator(
                oriented, reference, side=side
            )
            reduced_action = _realize_coset_operator(
                second_input, reference, side=side
            )
            if not physical_action == oriented_action == reduced_action:
                raise AssertionError(
                    "independent signed coset changed the realized action"
                )
            rows.append(
                {
                    "witness_id": witness_id,
                    "side": side,
                    "physical_pauli": {
                        "x": physical["x"],
                        "z": physical["z"],
                    },
                    "physical_pauli_word": _coset_pauli_word(physical),
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


def _dense_qubits(event: Mapping[str, Any]) -> list[int]:
    qubits = event.get("qubits")
    if not isinstance(qubits, list):
        raise ValueError("event qubits must be a list")
    dense: list[int] = []
    for qubit in qubits:
        if not isinstance(qubit, Mapping):
            raise ValueError("event qubit must be an object")
        ordinal = qubit.get("dense_ordinal")
        if type(ordinal) is not int:
            raise ValueError("event dense qubit ordinal must be an integer")
        dense.append(ordinal)
    return dense


def reconstruct_checkpoint_bases(
    events: Sequence[Mapping[str, Any]], qubit_count: int
) -> list[dict[str, Any]]:
    """Reconstruct checkpoint bases at time zero and after every event.

    The reference starts in ``|0>**qubit_count``.  Only ``H`` and control-first
    ``CX`` events conjugate that reference; instruments, coherent errors,
    classical Record operations, and markers leave it unchanged.
    """

    if type(qubit_count) is not int or qubit_count <= 0:
        raise ValueError("qubit_count must be a positive integer")
    if isinstance(events, (str, bytes)) or not isinstance(events, Sequence):
        raise TypeError("events must be a sequence of event objects")

    stabilizers: list[dict[str, Any]] = []
    for qubit in range(qubit_count):
        x = [0] * qubit_count
        z = [0] * qubit_count
        z[qubit] = 1
        stabilizers.append(_row(x, z))

    checkpoint_cache: dict[
        tuple[tuple[int, ...], ...], dict[str, Any]
    ] = {}

    def current_checkpoint() -> dict[str, Any]:
        key = tuple(
            tuple(row["x"] + row["z"] + [row["phase_mod4"]])
            for row in stabilizers
        )
        if key not in checkpoint_cache:
            checkpoint_cache[key] = _checkpoint(stabilizers, qubit_count)
        return deepcopy(checkpoint_cache[key])

    history = [current_checkpoint()]
    for event in events:
        if not isinstance(event, Mapping):
            raise TypeError("each event must be an object")
        kind = event.get("kind")
        if kind == "H":
            dense = _dense_qubits(event)
            if len(dense) != 1 or not 0 <= dense[0] < qubit_count:
                raise ValueError("H must name one in-range dense qubit")
            stabilizers = [_conjugate_h(row, dense[0]) for row in stabilizers]
        elif kind == "CX":
            dense = _dense_qubits(event)
            if len(dense) != 2 or any(
                not 0 <= qubit < qubit_count for qubit in dense
            ):
                raise ValueError("CX must name two in-range dense qubits")
            stabilizers = [
                _conjugate_control_first_cx(row, dense[0], dense[1])
                for row in stabilizers
            ]
        history.append(current_checkpoint())

    return history


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _codec_field_for_pivot(
    side: str, pivot: int, qubit_ids: Sequence[int]
) -> str:
    qubit_count = len(qubit_ids)
    if not 0 <= pivot < 2 * qubit_count:
        raise ValueError("signed-RREF pivot lies outside the Pauli codec")
    if pivot < qubit_count:
        return f"{side}.x[{qubit_ids[pivot]}]"
    return f"{side}.z[{qubit_ids[pivot - qubit_count]}]"


def _checkpoint_codec_fields(
    *,
    qubit_ids: Sequence[int],
    observable_live: bool,
    live_raw: Sequence[int],
    record_width: int,
) -> list[str]:
    fields: list[str] = []
    for side in ("L", "R"):
        fields.extend(f"{side}.x[{qubit}]" for qubit in qubit_ids)
        fields.extend(f"{side}.z[{qubit}]" for qubit in qubit_ids)
    fields.append("latent_m")
    if observable_live:
        fields.append("observable_0_accumulator")
    fields.extend(f"live_raw[{raw}]" for raw in live_raw)
    fields.extend(f"record[{ordinal}]" for ordinal in range(record_width))
    return fields


def _source_qubit_ids(qubits: object) -> list[int]:
    if not isinstance(qubits, list) or not qubits:
        raise ValueError("independent source program has no qubit list")
    qubit_ids: list[int] = []
    for expected_dense, qubit in enumerate(qubits):
        if not isinstance(qubit, Mapping):
            raise ValueError("independent source qubit must be an object")
        stim_id = qubit.get("stim_id")
        dense = qubit.get("dense_ordinal")
        if type(stim_id) is not int or type(dense) is not int:
            raise ValueError("independent source qubit identity is invalid")
        if dense != expected_dense:
            raise ValueError("independent source dense qubit order is not canonical")
        qubit_ids.append(stim_id)
    if len(set(qubit_ids)) != len(qubit_ids):
        raise ValueError("independent source qubit IDs are not unique")
    return qubit_ids


def _event_liveness(
    events: Sequence[Mapping[str, Any]],
) -> tuple[dict[int, int], dict[int, int]]:
    producer: dict[int, int] = {}
    last_use: dict[int, int] = {}
    for event_index, event in enumerate(events):
        raw_output = event.get("raw_output")
        if raw_output is not None:
            if type(raw_output) is not int or raw_output in producer:
                raise ValueError(
                    "independent source raw output is invalid or duplicated"
                )
            producer[raw_output] = event_index
        rec_operands = event.get("rec_operands")
        if not isinstance(rec_operands, list):
            raise ValueError("independent source rec operands must be a list")
        for operand in rec_operands:
            if not isinstance(operand, Mapping):
                raise ValueError("independent source rec operand must be an object")
            raw = operand.get("absolute_raw_ordinal")
            if type(raw) is not int or raw not in producer:
                raise ValueError("independent source rec operand has no prior producer")
            last_use[raw] = event_index
    return producer, last_use


def reconstruct_add_relation_events(source_text: str) -> list[dict[str, Any]]:
    """Reconstruct every static ADD relation row from source text alone.

    The only project-level dependencies are the two independent oracles: one
    parses the frozen flattened source and the other derives finite local pair
    rows.  Target owner/model/neutral/ADD and micro-owner code are never used.
    """

    # Local imports keep the signed-RREF and coset APIs independently usable
    # even in an environment that does not install the finite-matrix oracle.
    from .independent_pair_oracle import reconstruct_component_rows
    from .independent_source_oracle import reconstruct_source_program

    source_program = reconstruct_source_program(source_text)
    if not isinstance(source_program, Mapping):
        raise TypeError("independent source program must be an object")
    qubit_ids = _source_qubit_ids(source_program.get("qubits"))
    raw_events = source_program.get("events")
    if not isinstance(raw_events, list) or any(
        not isinstance(event, Mapping) for event in raw_events
    ):
        raise ValueError("independent source events must be a list of objects")
    events: list[Mapping[str, Any]] = list(raw_events)

    basis_history = reconstruct_checkpoint_bases(events, len(qubit_ids))
    if len(basis_history) != len(events) + 1:
        raise AssertionError("independent checkpoint history has wrong cardinality")
    producer, last_use = _event_liveness(events)

    record_widths = [0]
    for event in events:
        record_output = event.get("record_output")
        if record_output is not None and not isinstance(record_output, Mapping):
            raise ValueError(
                "independent source Record output must be an object or null"
            )
        record_widths.append(record_widths[-1] + int(record_output is not None))

    codecs: list[dict[str, Any]] = []
    for checkpoint, basis in enumerate(basis_history):
        after_event_index = checkpoint - 1
        live_raw = sorted(
            raw
            for raw, produced_at in producer.items()
            if produced_at <= after_event_index
            and last_use.get(raw, -1) > after_event_index
        )
        fields = _checkpoint_codec_fields(
            qubit_ids=qubit_ids,
            observable_live=checkpoint < len(events),
            live_raw=live_raw,
            record_width=record_widths[checkpoint],
        )
        pivots = basis.get("pivots")
        if not isinstance(pivots, list):
            raise AssertionError("independent basis has no pivot list")
        validity = {
            "pivot_zero_fields": [
                _codec_field_for_pivot(side, pivot, qubit_ids)
                for side in ("L", "R")
                for pivot in pivots
            ],
            "inactive_zero_fields": [],
            "latent_values": [-1, 1],
            "record_width": record_widths[checkpoint],
        }
        codecs.append(
            {
                "checkpoint": checkpoint,
                "fields": fields,
                "validity_sha256": _sha256_json(validity),
            }
        )

    relations: list[dict[str, Any]] = []
    for event_index, event in enumerate(events):
        event_id = event.get("event_id")
        kind = event.get("kind")
        if not isinstance(event_id, str) or not isinstance(kind, str):
            raise ValueError("independent source event identity is invalid")
        kernel_payload = {
            "event_id": event_id,
            "kind": kind,
            "input_checkpoint": event_index,
            "output_checkpoint": event_index + 1,
            "component_rows": reconstruct_component_rows(dict(event)),
        }
        input_codec = codecs[event_index]
        output_codec = codecs[event_index + 1]
        input_fields = input_codec["fields"]
        output_fields = output_codec["fields"]
        relations.append(
            {
                "event_id": event_id,
                "pair_semantic_sha256": _sha256_json(kernel_payload),
                "input_codec": deepcopy(input_codec),
                "output_codec": deepcopy(output_codec),
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
    return relations


def _binary_rank(rows: Sequence[Mapping[str, Any]]) -> int:
    """Compute GF(2) rank without trusting a supplied RREF or pivot list."""

    packed: list[int] = []
    width: int | None = None
    for row in rows:
        bits = _bits(row)
        if width is None:
            width = len(bits)
        elif len(bits) != width:
            raise ValueError("GF(2) rank rows have inconsistent widths")
        value = 0
        for bit in bits:
            if bit not in (0, 1):
                raise ValueError("GF(2) rank input is not binary")
            value = (value << 1) | bit
        packed.append(value)
    if width is None:
        return 0

    rank = 0
    for column in range(width):
        mask = 1 << (width - column - 1)
        selected = next(
            (
                candidate
                for candidate in range(rank, len(packed))
                if packed[candidate] & mask
            ),
            None,
        )
        if selected is None:
            continue
        packed[rank], packed[selected] = packed[selected], packed[rank]
        for row_index in range(len(packed)):
            if row_index != rank and packed[row_index] & mask:
                packed[row_index] ^= packed[rank]
        rank += 1
        if rank == len(packed):
            break
    return rank


def _signed_row_signature(row: Mapping[str, Any]) -> str:
    """Compactly retain every bit and the signed global phase in a receipt."""

    x = "".join(str(bit) for bit in row["x"])
    z = "".join(str(bit) for bit in row["z"])
    return f"{int(row['phase_mod4'])}:{x}:{z}"


def _pairwise_commutation_bits(rows: Sequence[Mapping[str, Any]]) -> str:
    """Encode all unique pairs in ``i``-then-``j`` upper-triangle order."""

    return "".join(
        "1" if _commutes(rows[left], rows[right]) else "0"
        for left in range(len(rows))
        for right in range(left + 1, len(rows))
    )


def _leading_columns(rows: Sequence[Mapping[str, Any]]) -> list[int]:
    columns: list[int] = []
    for row in rows:
        try:
            columns.append(_bits(row).index(1))
        except ValueError as exc:
            raise ValueError("signed RREF contains an identity row") from exc
    return columns


def _normalize_history_basis(
    basis: Mapping[str, Any], *, qubit_count: int
) -> dict[str, Any]:
    required = {"stabilizers", "rref_rows", "pivots"}
    if not required.issubset(basis):
        raise ValueError("checkpoint basis is missing a required field")

    def normalize_rows(value: object, *, label: str) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            raise ValueError(f"checkpoint {label} must be a list")
        normalized: list[dict[str, Any]] = []
        for row in value:
            if not isinstance(row, Mapping):
                raise ValueError(f"checkpoint {label} row must be an object")
            try:
                normalized.append(
                    _row(row["x"], row["z"], row["phase_mod4"])
                )
            except KeyError as exc:
                raise ValueError(
                    f"checkpoint {label} row is missing signed-Pauli data"
                ) from exc
        if len(normalized) != qubit_count:
            raise ValueError(f"checkpoint {label} has the wrong row count")
        return normalized

    stabilizers = normalize_rows(basis["stabilizers"], label="stabilizers")
    rref_rows = normalize_rows(basis["rref_rows"], label="rref_rows")
    raw_pivots = basis["pivots"]
    if not isinstance(raw_pivots, list) or any(
        type(pivot) is not int for pivot in raw_pivots
    ):
        raise ValueError("checkpoint pivots must be a list of integers")
    pivots = list(raw_pivots)
    if len(pivots) != qubit_count or any(
        not 0 <= pivot < 2 * qubit_count for pivot in pivots
    ):
        raise ValueError("checkpoint pivot count or range is invalid")
    return {
        "stabilizers": stabilizers,
        "rref_rows": rref_rows,
        "pivots": pivots,
    }


def _basis_audit_summary(
    basis: Mapping[str, Any], *, qubit_count: int
) -> dict[str, dict[str, Any]]:
    normalized = _normalize_history_basis(basis, qubit_count=qubit_count)
    stabilizers = normalized["stabilizers"]
    supplied_rref = normalized["rref_rows"]
    supplied_pivots = normalized["pivots"]

    source_rref, source_pivots = _full_rref(stabilizers, qubit_count)
    second_rref, second_pivots = _full_rref(supplied_rref, qubit_count)
    stabilizer_signatures = [
        _signed_row_signature(row) for row in stabilizers
    ]
    supplied_signatures = [
        _signed_row_signature(row) for row in supplied_rref
    ]
    source_signatures = [_signed_row_signature(row) for row in source_rref]
    second_signatures = [_signed_row_signature(row) for row in second_rref]
    pair_count = qubit_count * (qubit_count - 1) // 2

    return {
        "rank": {
            "required_rank": qubit_count,
            "stabilizer_rank": _binary_rank(stabilizers),
            "rref_rank": _binary_rank(supplied_rref),
        },
        "commutation": {
            "pair_order": "(i,j)_for_i=0..n-1_then_j=i+1..n-1",
            "pair_count": pair_count,
            "stabilizer_pair_results": _pairwise_commutation_bits(stabilizers),
            "rref_pair_results": _pairwise_commutation_bits(supplied_rref),
        },
        "leftmost_pivots": {
            "declared_pivots": supplied_pivots,
            "rref_leading_columns": _leading_columns(supplied_rref),
            "independent_source_pivots": source_pivots,
        },
        "signed_phases": {
            "stabilizer_phases_mod4": [
                row["phase_mod4"] for row in stabilizers
            ],
            "rref_phases_mod4": [
                row["phase_mod4"] for row in supplied_rref
            ],
            "all_rows_hermitian": all(
                row["phase_mod4"] in (0, 2)
                for row in (*stabilizers, *supplied_rref)
            ),
        },
        "idempotence": {
            "source_stabilizer_rows": stabilizer_signatures,
            "source_reduction_rows": source_signatures,
            "first_reduction_rows": supplied_signatures,
            "second_reduction_rows": second_signatures,
            "source_reduction_pivots": source_pivots,
            "first_reduction_pivots": supplied_pivots,
            "second_reduction_pivots": second_pivots,
            "source_equals_first": (
                source_signatures == supplied_signatures
                and source_pivots == supplied_pivots
            ),
            "first_equals_second": (
                supplied_signatures == second_signatures
                and supplied_pivots == second_pivots
            ),
        },
    }


def audit_target_rref_receipt_rows(
    events: Sequence[Mapping[str, Any]],
    qubit_count: int,
    owner_history: Sequence[Mapping[str, Any]],
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    """Build complete expected/observed RREF receipt rows per checkpoint.

    Expected bases are reconstructed from the event stream by this independent
    oracle.  Observed rows are separately derived from the supplied owner
    history; no owner/model/report helper participates in either path.
    """

    if type(qubit_count) is not int or qubit_count <= 0:
        raise ValueError("qubit_count must be a positive integer")
    if isinstance(owner_history, (str, bytes)) or not isinstance(
        owner_history, Sequence
    ):
        raise TypeError("owner_history must be a sequence of checkpoint bases")

    expected_history = reconstruct_checkpoint_bases(events, qubit_count)
    if len(owner_history) != len(expected_history):
        raise ValueError("owner checkpoint history has the wrong cardinality")

    assertion_ids = (
        "rank",
        "commutation",
        "leftmost_pivots",
        "signed_phases",
        "idempotence",
    )
    receipt: dict[str, dict[str, list[dict[str, Any]]]] = {
        assertion_id: {"expected_rows": [], "observed_rows": []}
        for assertion_id in assertion_ids
    }
    summary_cache: dict[
        tuple[tuple[str, ...], tuple[str, ...], tuple[int, ...]],
        dict[str, dict[str, Any]],
    ] = {}

    def summary(basis: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
        normalized = _normalize_history_basis(basis, qubit_count=qubit_count)
        key = (
            tuple(_signed_row_signature(row) for row in normalized["stabilizers"]),
            tuple(_signed_row_signature(row) for row in normalized["rref_rows"]),
            tuple(normalized["pivots"]),
        )
        if key not in summary_cache:
            summary_cache[key] = _basis_audit_summary(
                normalized, qubit_count=qubit_count
            )
        return summary_cache[key]

    for checkpoint, (expected_basis, observed_basis) in enumerate(
        zip(expected_history, owner_history, strict=True)
    ):
        if not isinstance(observed_basis, Mapping):
            raise TypeError("owner checkpoint basis must be an object")
        expected_summary = summary(expected_basis)
        observed_summary = summary(observed_basis)
        for assertion_id in assertion_ids:
            receipt[assertion_id]["expected_rows"].append(
                {"checkpoint": checkpoint, **deepcopy(expected_summary[assertion_id])}
            )
            receipt[assertion_id]["observed_rows"].append(
                {"checkpoint": checkpoint, **deepcopy(observed_summary[assertion_id])}
            )

    return receipt


# The finite ADD truth witness below is deliberately self-contained.  It does
# not import the ADD/pair/TN owners (or their coefficient model), and it never
# constructs a decision diagram, a reachable state, or an advance operation.
_TRUTH_ZERO_DATA = [[0, 1], [0, 1], [0, 1], [0, 1]]


def _truth_event(
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
        "qubits": list(qubits),
        "raw_output": raw_output,
        "rec_operands": list(rec_operands),
        "record_output": record_kind,
        "fixed_branch": fixed_branch,
    }


def _truth_definition(
    witness_id: str,
) -> tuple[int, bool, list[dict[str, Any]]]:
    if witness_id == "P1":
        return 1, False, [
            _truth_event("identity", "COORD_MARKER"),
            _truth_event("H", "H", (0,)),
            _truth_event("COHERENT_Z", "COHERENT_Z", (0,)),
            _truth_event("R", "RESET", (0,)),
            _truth_event("M(b=0)", "M", (0,), raw_output=0, fixed_branch=0),
            _truth_event("M(b=1)", "M", (0,), raw_output=0, fixed_branch=1),
            _truth_event("MR(b=0)", "MR", (0,), raw_output=0, fixed_branch=0),
            _truth_event("MR(b=1)", "MR", (0,), raw_output=0, fixed_branch=1),
        ]
    if witness_id == "P2":
        return 2, False, [
            _truth_event("H(q=0)", "H", (0,)),
            _truth_event("H(q=1)", "H", (1,)),
            _truth_event("CX(control=0,target=1)", "CX", (0, 1)),
            _truth_event("CX(control=1,target=0)", "CX", (1, 0)),
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
        _truth_event(
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


def _truth_amp_rational(numerator: int, denominator: int = 1) -> _ExactAmplitude:
    return (
        Fraction(numerator, denominator),
        Fraction(0),
        Fraction(0),
        Fraction(0),
    )


def _truth_amp_scale(value: _ExactAmplitude, scalar: int) -> _ExactAmplitude:
    return tuple(scalar * coordinate for coordinate in value)  # type: ignore[return-value]


def _truth_amp_conjugate(value: _ExactAmplitude) -> _ExactAmplitude:
    a, b, c, d = value
    return a, b, -c, -d


def _truth_amp_power(value: _ExactAmplitude, exponent: int) -> _ExactAmplitude:
    if exponent < 0:
        raise ValueError("negative tiny truth powers are invalid")
    result = _AMP_ONE
    for _ in range(exponent):
        result = _amp_mul(result, value)
    return result


def _truth_initial_basis(width: int) -> dict[str, Any]:
    stabilizers = []
    for qubit in range(width):
        x = [0] * width
        z = [0] * width
        z[qubit] = 1
        stabilizers.append(_row(x, z))
    return independent_signed_rref_basis(stabilizers)


def _truth_advance_basis(
    basis: Mapping[str, Any], event: Mapping[str, Any]
) -> dict[str, Any]:
    stabilizers = [deepcopy(dict(row)) for row in basis["stabilizers"]]
    qubits = event["qubits"]
    if event["kind"] == "H":
        stabilizers = [_conjugate_h(row, qubits[0]) for row in stabilizers]
    elif event["kind"] == "CX":
        stabilizers = [
            _conjugate_control_first_cx(row, qubits[0], qubits[1])
            for row in stabilizers
        ]
    return independent_signed_rref_basis(stabilizers)


def _truth_codec_fields(
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


def _truth_pivot_fields(basis: Mapping[str, Any], width: int) -> set[str]:
    result: set[str] = set()
    for side in ("L", "R"):
        for pivot in basis["pivots"]:
            axis = "x" if pivot < width else "z"
            qubit = pivot if pivot < width else pivot - width
            result.add(f"{side}.{axis}[{qubit}]")
    return result


def _truth_assignment(fields: list[str], bits: list[int]) -> dict[str, int]:
    return dict(zip(fields, bits, strict=True))


def _truth_pair_from_assignment(
    assignment: Mapping[str, int], side: str, width: int
) -> dict[str, Any]:
    return _row(
        [assignment[f"{side}.x[{qubit}]"] for qubit in range(width)],
        [assignment[f"{side}.z[{qubit}]"] for qubit in range(width)],
    )


def _truth_pauli_label(label: str, qubit: int, width: int) -> dict[str, Any]:
    coordinates = {"I": (0, 0), "X": (1, 0), "Y": (1, 1), "Z": (0, 1)}
    if label not in coordinates or not 0 <= qubit < width:
        raise ValueError("independent tiny Pauli action is invalid")
    x = [0] * width
    z = [0] * width
    x[qubit], z[qubit] = coordinates[label]
    return _row(x, z)


def _truth_instrument_components(
    kind: str, branch: int
) -> list[tuple[str, _ExactAmplitude]]:
    half = _truth_amp_rational(1, 2)
    if kind == "M":
        return [
            ("I", half),
            ("Z", half if branch == 0 else _truth_amp_scale(half, -1)),
        ]
    if branch == 0:
        return [("I", half), ("Z", half)]
    return [("X", half), ("Y", _amp_mul(_AMP_I, half))]


def _truth_literal_terms(event: Mapping[str, Any]) -> list[dict[str, Any]]:
    kind = event["kind"]
    terms: list[dict[str, Any]] = []
    if kind == "COHERENT_Z":
        c = _truth_amp_rational(9999, 10001)
        s = _truth_amp_rational(200, 10001)
        for left in (0, 1):
            for right in (0, 1):
                values: dict[int, _ExactAmplitude] = {}
                for latent in (-1, 1):
                    left_value = (
                        _AMP_ONE
                        if not left
                        else _truth_amp_scale(_amp_mul(_AMP_I, s), -latent)
                    )
                    right_value = (
                        _AMP_ONE
                        if not right
                        else _truth_amp_scale(_amp_mul(_AMP_I, s), latent)
                    )
                    values[latent] = _amp_mul(
                        _amp_mul(left_value, right_value),
                        _truth_amp_power(c, 2 - left - right),
                    )
                terms.append(
                    {
                        "transform": None,
                        "left_label": "Z" if left else None,
                        "right_label": "Z" if right else None,
                        "branch": None,
                        "coefficient_by_latent": values,
                    }
                )
        return terms
    if kind in {"RESET", "M", "MR"}:
        instrument_kind = "MR" if kind == "RESET" else kind
        for branch in (0, 1):
            if event["fixed_branch"] is not None and branch != event["fixed_branch"]:
                continue
            components = _truth_instrument_components(instrument_kind, branch)
            for left_label, left_value in components:
                for right_label, right_value in components:
                    coefficient = _amp_mul(
                        left_value, _truth_amp_conjugate(right_value)
                    )
                    terms.append(
                        {
                            "transform": None,
                            "left_label": left_label,
                            "right_label": right_label,
                            "branch": branch,
                            "coefficient_by_latent": {
                                -1: coefficient,
                                1: coefficient,
                            },
                        }
                    )
        return terms
    transform = kind if kind in {"H", "CX"} else None
    return [
        {
            "transform": transform,
            "left_label": None,
            "right_label": None,
            "branch": None,
            "coefficient_by_latent": {-1: _AMP_ONE, 1: _AMP_ONE},
        }
    ]


def _truth_apply_term_side(
    pauli: Mapping[str, Any],
    term: Mapping[str, Any],
    event: Mapping[str, Any],
    *,
    side: str,
) -> dict[str, Any]:
    current = deepcopy(dict(pauli))
    transform = term["transform"]
    qubits = event["qubits"]
    if transform == "H":
        return _conjugate_h(current, qubits[0])
    if transform == "CX":
        return _conjugate_control_first_cx(current, qubits[0], qubits[1])
    label = term["left_label"] if side == "ket" else term["right_label"]
    if label is None:
        return current
    local = _truth_pauli_label(label, qubits[0], len(current["x"]))
    return _multiply(local, current) if side == "ket" else _multiply(current, local)


def _truth_raw_ordinal(field: str) -> int:
    return int(field.removeprefix("live_raw[").removesuffix("]"))


def _truth_record_ordinal(field: str) -> int:
    return int(field.removeprefix("record[").removesuffix("]"))


def _truth_expected_classical_output(
    event: Mapping[str, Any],
    input_assignment: Mapping[str, int],
    output_fields: list[str],
    *,
    branch: int | None,
) -> dict[str, int]:
    expected: dict[str, int] = {}
    operands = [
        input_assignment[f"live_raw[{raw}]"] for raw in event["rec_operands"]
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
            raw = _truth_raw_ordinal(field)
            if raw == event["raw_output"]:
                if branch not in (0, 1):
                    raise ValueError("independent raw-producing term has no branch")
                expected[field] = branch
            else:
                expected[field] = input_assignment[field]
        elif field.startswith("record["):
            ordinal = _truth_record_ordinal(field)
            if ordinal < input_record_width:
                expected[field] = input_assignment[field]
            elif event["kind"] == "DETECTOR_APPEND":
                expected[field] = parity
            elif event["kind"] == "FINALIZE_RECORD":
                expected[field] = input_assignment["observable_0_accumulator"]
            else:
                raise ValueError("independent tiny relation created an unknown Record bit")
        else:
            raise ValueError(f"unknown independent tiny codec field {field!r}")
    return expected


def _truth_transition_map(
    *,
    event: Mapping[str, Any],
    width: int,
    input_fields: list[str],
    input_bits: list[int],
    output_fields: list[str],
    output_basis: Mapping[str, Any],
) -> dict[tuple[int, ...], _ExactAmplitude]:
    input_assignment = _truth_assignment(input_fields, input_bits)
    latent = -1 if input_assignment["latent_m"] == 0 else 1
    left_input = _truth_pair_from_assignment(input_assignment, "L", width)
    right_input = _truth_pair_from_assignment(input_assignment, "R", width)
    result: dict[tuple[int, ...], _ExactAmplitude] = {}
    for term in _truth_literal_terms(event):
        left_signed = _truth_apply_term_side(
            left_input, term, event, side="ket"
        )
        right_signed = _truth_apply_term_side(
            right_input, term, event, side="bra"
        )
        left_reduced = _reduce_signed_coset_row(
            left_signed, output_basis, side="ket"
        )
        right_reduced = _reduce_signed_coset_row(
            right_signed, output_basis, side="bra"
        )
        phase = (
            left_reduced["coefficient_phase_mod4"]
            + right_reduced["coefficient_phase_mod4"]
        )
        coefficient = _amp_mul(
            term["coefficient_by_latent"][latent], _amp_i_power(phase)
        )
        expected = _truth_expected_classical_output(
            event,
            input_assignment,
            output_fields,
            branch=term["branch"],
        )
        for side, reduction in (("L", left_reduced), ("R", right_reduced)):
            representative = reduction["representative"]
            for qubit in range(width):
                expected[f"{side}.x[{qubit}]"] = representative["x"][qubit]
                expected[f"{side}.z[{qubit}]"] = representative["z"][qubit]
        output = tuple(expected[field] for field in output_fields)
        result[output] = _amp_add(result.get(output, _AMP_ZERO), coefficient)
    return result


def _truth_plans(witness_id: str) -> tuple[int, list[dict[str, Any]]]:
    width, sequential, events = _truth_definition(witness_id)
    initial_basis = _truth_initial_basis(width)
    producer: dict[int, int] = {}
    last_use: dict[int, int] = {}
    for event_index, event in enumerate(events):
        if event["raw_output"] is not None:
            producer[event["raw_output"]] = event_index
        for raw in event["rec_operands"]:
            last_use[raw] = event_index

    plans: list[dict[str, Any]] = []
    running_basis = initial_basis
    record_width = 0
    for operation_index, event in enumerate(events):
        input_basis = running_basis if sequential else initial_basis
        output_basis = _truth_advance_basis(input_basis, event)
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
            input_fields = _truth_codec_fields(
                width,
                observable_live=True,
                live_raw=input_live_raw,
                record_width=input_record_width,
            )
            output_fields = _truth_codec_fields(
                width,
                observable_live=operation_index < len(events) - 1,
                live_raw=output_live_raw,
                record_width=record_width,
            )
            running_basis = output_basis
        else:
            input_fields = _truth_codec_fields(
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
                "input_pivots": _truth_pivot_fields(input_basis, width),
                "output_pivots": _truth_pivot_fields(output_basis, width),
            }
        )
    return width, plans


def reconstructed_tiny_add_truth_row_count(witness_id: str) -> int:
    """Independently count the full frozen input x output relation."""

    _, plans = _truth_plans(witness_id)
    return sum(
        1 << (len(plan["input_fields"]) + len(plan["output_fields"]))
        for plan in plans
    )


def iter_reconstructed_tiny_add_truth_rows(
    witness_id: str,
) -> Iterator[dict[str, Any]]:
    """Independently stream every valid and invalid input/output code pair."""

    width, plans = _truth_plans(witness_id)
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
                _truth_transition_map(
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
                    transition.get(raw_output_bits, _AMP_ZERO)
                    if output_valid
                    else _AMP_ZERO
                )
                yield {
                    "operation_index": operation_index,
                    "input_bits": input_bits,
                    "output_bits": list(raw_output_bits),
                    "input_valid": input_valid,
                    "output_valid": output_valid,
                    "totalized_coefficient": (
                        _TRUTH_ZERO_DATA
                        if coefficient == _AMP_ZERO
                        else _amp_data(coefficient)
                    ),
                }


def summarize_reconstructed_tiny_add_truth_assertion(
    witness_id: str, *, assertion_id: str, subject: str
) -> dict[str, Any]:
    """Independently hash the assertion preimage with bounded memory."""

    if not assertion_id or not subject:
        raise ValueError("independent tiny ADD assertion identity must be nonempty")
    digest = hashlib.sha256()
    digest.update(b'{"assertion_id":')
    digest.update(_canonical_json_bytes(assertion_id))
    digest.update(b',"rows":[')
    rows_digest = hashlib.sha256(b"[")
    row_count = 0
    for row in iter_reconstructed_tiny_add_truth_rows(witness_id):
        if row_count:
            digest.update(b",")
            rows_digest.update(b",")
        row_bytes = _canonical_json_bytes(row)
        digest.update(row_bytes)
        rows_digest.update(row_bytes)
        row_count += 1
    digest.update(b'],"subject":')
    rows_digest.update(b"]")
    digest.update(_canonical_json_bytes(subject))
    digest.update(b"}")
    expected_count = reconstructed_tiny_add_truth_row_count(witness_id)
    if row_count != expected_count:
        raise AssertionError(
            "independent tiny ADD stream is not the complete Cartesian product"
        )
    return {
        "row_count": row_count,
        "sha256": digest.hexdigest(),
        "rows_sha256": rows_digest.hexdigest(),
    }


# Historical spelling retained as a lazy iterator, never a materialized T4 list.
reconstruct_tiny_add_truth_rows = iter_reconstructed_tiny_add_truth_rows


_PERSISTENT_LATENT_DECLARATION = {
    "name": "m",
    "domain": [-1, 1],
    "codec": [
        {"bit": 0, "value": -1},
        {"bit": 1, "value": 1},
    ],
    "prior": [[1, 2], [1, 2]],
    "transition": "identity_across_coherent_occurrences",
}


def _audit_object(value: object, *, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be a mapping")
    return value


def _audit_list(value: object, *, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise TypeError(f"{label} must be a list")
    return value


def _audit_persistent_neutral_declaration(
    neutral_semantic: Mapping[str, Any],
) -> None:
    process = _audit_object(
        neutral_semantic.get("process"), label="neutral process"
    )
    if process.get("name") != "persistent_coherent_declared_error":
        raise ValueError("persistent neutral process declaration mismatch")
    if process.get("axis") != "Z":
        raise ValueError("persistent neutral process axis mismatch")
    latent = _audit_object(process.get("latent"), label="neutral latent")
    if dict(latent) != _PERSISTENT_LATENT_DECLARATION:
        raise ValueError("persistent neutral latent declaration mismatch")


def _audit_neutral_coherent_occurrences(
    neutral_semantic: Mapping[str, Any],
) -> list[tuple[int, str]]:
    events = _audit_list(neutral_semantic.get("events"), label="neutral events")
    coherent: list[tuple[int, str]] = []
    seen_event_ids: set[str] = set()
    for event_ordinal, raw_event in enumerate(events):
        event = _audit_object(
            raw_event, label=f"neutral event {event_ordinal}"
        )
        event_id = event.get("event_id")
        if not isinstance(event_id, str) or not event_id:
            raise ValueError("neutral event has an invalid event_id")
        if event_id in seen_event_ids:
            raise ValueError("neutral event_id is duplicated")
        seen_event_ids.add(event_id)
        if event.get("kind") == "COHERENT_Z":
            if event.get("kernel_id") != "PERSISTENT_COHERENT_Z":
                raise ValueError("neutral coherent event lost persistent semantics")
            coherent.append((event_ordinal, event_id))
    if not coherent:
        raise ValueError("persistent neutral process has no coherent occurrence")
    return coherent


def _audit_pair_latent_binding(
    pair_semantic: Mapping[str, Any],
    neutral_semantic: Mapping[str, Any],
    coherent: Sequence[tuple[int, str]],
) -> dict[str, Mapping[str, Any]]:
    initial_terms = _audit_list(
        pair_semantic.get("initial_terms"), label="pair initial_terms"
    )
    if [
        _audit_object(term, label="pair initial term").get("latent_m")
        for term in initial_terms
    ] != [-1, 1]:
        raise ValueError("pair initial terms do not own the persistent latent_m prior")
    expected_initial_coefficient = [[1, 2], [0, 1], [0, 1], [0, 1]]
    if any(
        _audit_object(term, label="pair initial term").get("coefficient")
        != expected_initial_coefficient
        for term in initial_terms
    ):
        raise ValueError("pair initial terms do not reproduce the neutral sign prior")

    events = _audit_list(neutral_semantic.get("events"), label="neutral events")
    kernels = _audit_list(pair_semantic.get("kernels"), label="pair kernels")
    if len(kernels) != len(events):
        raise ValueError("pair kernel stream does not span every neutral event")
    kernels_by_event: dict[str, Mapping[str, Any]] = {}
    for event_ordinal, (raw_event, raw_kernel) in enumerate(
        zip(events, kernels, strict=True)
    ):
        event = _audit_object(raw_event, label=f"neutral event {event_ordinal}")
        kernel = _audit_object(raw_kernel, label=f"pair kernel {event_ordinal}")
        if (
            kernel.get("event_id") != event.get("event_id")
            or kernel.get("kind") != event.get("kind")
            or kernel.get("input_checkpoint") != event_ordinal
            or kernel.get("output_checkpoint") != event_ordinal + 1
        ):
            raise ValueError("pair kernel chronology differs from the neutral process")
        event_id = str(event["event_id"])
        if event_id in kernels_by_event:
            raise ValueError("pair kernel event_id is duplicated")
        kernels_by_event[event_id] = kernel
        component_rows = _audit_list(
            kernel.get("component_rows"),
            label=f"pair kernel {event_id} component_rows",
        )
        if not component_rows:
            raise ValueError("pair kernel has no complete component row")
        for row_ordinal, raw_row in enumerate(component_rows):
            row = _audit_object(
                raw_row,
                label=f"pair kernel {event_id} component {row_ordinal}",
            )
            multipliers = _audit_list(
                row.get("multiplier_by_latent"),
                label=f"pair kernel {event_id} latent multipliers",
            )
            if [
                _audit_object(item, label="pair latent multiplier").get("latent_m")
                for item in multipliers
            ] != [-1, 1]:
                raise ValueError(
                    "pair kernel component does not bind both persistent latent_m values"
                )
            if any(
                set(_audit_object(item, label="pair latent multiplier"))
                != {"latent_m", "coefficient"}
                for item in multipliers
            ):
                raise ValueError("pair latent multiplier schema is not exact")

    checkpoints = _audit_list(
        pair_semantic.get("checkpoints"), label="pair checkpoints"
    )
    if len(checkpoints) != len(events) + 1:
        raise ValueError("pair checkpoint stream does not bound every neutral event")
    for checkpoint_ordinal, raw_checkpoint in enumerate(checkpoints):
        checkpoint = _audit_object(
            raw_checkpoint, label=f"pair checkpoint {checkpoint_ordinal}"
        )
        expected_after = (
            None if checkpoint_ordinal == 0 else events[checkpoint_ordinal - 1]["event_id"]
        )
        if (
            checkpoint.get("ordinal") != checkpoint_ordinal
            or checkpoint.get("after_event_id") != expected_after
        ):
            raise ValueError("pair checkpoint chronology differs from the neutral process")
        codec_fields = _audit_list(
            checkpoint.get("codec_fields"), label="pair checkpoint codec_fields"
        )
        if codec_fields.count("latent_m") != 1 or any(
            isinstance(field, str)
            and field.startswith("latent_m")
            and field != "latent_m"
            for field in codec_fields
        ):
            raise ValueError("pair checkpoint codec does not own exactly one latent_m")
        validity = _audit_object(
            checkpoint.get("validity"), label="pair checkpoint validity"
        )
        if validity.get("latent_values") != [-1, 1]:
            raise ValueError("pair checkpoint codec changed the persistent latent domain")

    coherent_ids = [event_id for _, event_id in coherent]
    if [
        event_id
        for event_id in coherent_ids
        if kernels_by_event[event_id].get("kind") == "COHERENT_Z"
    ] != coherent_ids:
        raise ValueError("pair coherent kernels do not span the neutral occurrences")
    return kernels_by_event


def _audit_tn_sign_chain(
    tn_semantic: Mapping[str, Any],
    coherent: Sequence[tuple[int, str]],
    pair_kernels: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    index_catalog = _audit_list(
        tn_semantic.get("index_catalog"), label="TN index_catalog"
    )
    indices: dict[str, Mapping[str, Any]] = {}
    for raw_index in index_catalog:
        index = _audit_object(raw_index, label="TN index")
        index_id = index.get("index_id")
        if not isinstance(index_id, str) or not index_id:
            raise ValueError("TN index has an invalid index_id")
        if index_id in indices:
            raise ValueError("TN index_id is duplicated")
        indices[index_id] = index

    factors_raw = _audit_list(tn_semantic.get("factors"), label="TN factors")
    factors: dict[str, Mapping[str, Any]] = {}
    for raw_factor in factors_raw:
        factor = _audit_object(raw_factor, label="TN factor")
        factor_id = factor.get("factor_id")
        if not isinstance(factor_id, str) or not factor_id:
            raise ValueError("TN factor has an invalid factor_id")
        if factor_id in factors:
            raise ValueError("TN factor_id is duplicated")
        factors[factor_id] = factor

    half_factors = [
        factor for factor in factors.values() if factor.get("template_id") == "HALF"
    ]
    if len(half_factors) != 1:
        raise ValueError("TN persistent sign chain must own exactly one HALF prior")
    prior = half_factors[0]
    prior_provenance = _audit_object(
        prior.get("provenance"), label="TN sign prior provenance"
    )
    prior_scope = _audit_list(prior.get("scope"), label="TN sign prior scope")
    if (
        prior.get("shape") != [2]
        or len(prior_scope) != 1
        or prior_provenance.get("role") != "SIGN_PRIOR"
        or prior_provenance.get("event_id") is not None
        or prior_provenance.get("ordinal") != 0
    ):
        raise ValueError("TN persistent sign prior is malformed")
    prior_sign = prior_scope[0]

    ledgers = _audit_list(
        tn_semantic.get("sign_occurrence_ledger"),
        label="TN sign_occurrence_ledger",
    )
    if len(ledgers) != len(coherent):
        raise ValueError("TN sign ledger does not span every coherent occurrence")
    sign_eq_factors = {
        factor_id
        for factor_id, factor in factors.items()
        if factor.get("template_id") == "SIGN_EQ"
    }
    coherent_factors = {
        factor_id
        for factor_id, factor in factors.items()
        if factor.get("template_id") == "COHERENT_Z"
    }
    if len(sign_eq_factors) != len(coherent):
        raise ValueError("TN persistent sign chain must have one SIGN_EQ per occurrence")
    if len(coherent_factors) != len(coherent):
        raise ValueError("TN controlled channels do not span every coherent occurrence")

    occurrences: list[dict[str, Any]] = []
    used_chain_factors: set[str] = set()
    used_channel_factors: set[str] = set()
    expected_sign_indices: set[str] = {str(prior_sign)}
    previous_sign = prior_sign
    for occurrence, ((event_ordinal, event_id), raw_ledger) in enumerate(
        zip(coherent, ledgers, strict=True)
    ):
        ledger = _audit_object(raw_ledger, label=f"TN sign ledger {occurrence}")
        if set(ledger) != {
            "occurrence",
            "event_id",
            "previous_sign",
            "mu",
            "next_sign",
            "chain_factor",
            "channel_factor",
        }:
            raise ValueError("TN sign ledger schema is not exact")
        if (
            ledger.get("occurrence") != occurrence
            or ledger.get("event_id") != event_id
            or ledger.get("previous_sign") != previous_sign
        ):
            raise ValueError("TN sign ledger is not one ordered persistent chain")
        mu = ledger.get("mu")
        next_sign = ledger.get("next_sign")
        chain_factor_id = ledger.get("chain_factor")
        channel_factor_id = ledger.get("channel_factor")
        if not all(
            isinstance(value, str) and value
            for value in (mu, next_sign, chain_factor_id, channel_factor_id)
        ):
            raise ValueError("TN sign ledger contains an invalid identifier")
        if mu in expected_sign_indices or next_sign in expected_sign_indices or mu == next_sign:
            raise ValueError("TN sign ledger reuses an occurrence or chain-output index")

        try:
            chain_factor = factors[str(chain_factor_id)]
            channel_factor = factors[str(channel_factor_id)]
        except KeyError as exc:
            raise ValueError("TN sign ledger references an unknown factor") from exc
        chain_provenance = _audit_object(
            chain_factor.get("provenance"), label="TN SIGN_EQ provenance"
        )
        channel_provenance = _audit_object(
            channel_factor.get("provenance"), label="TN controlled-channel provenance"
        )
        if (
            chain_factor.get("template_id") != "SIGN_EQ"
            or chain_factor.get("shape") != [2, 2, 2]
            or chain_factor.get("scope") != [previous_sign, mu, next_sign]
            or chain_provenance.get("role") != "SIGN_CHAIN"
            or chain_provenance.get("event_id") != event_id
            or chain_provenance.get("ordinal") != occurrence
        ):
            raise ValueError("TN SIGN_EQ factor does not match its ordered ledger row")
        channel_scope = _audit_list(
            channel_factor.get("scope"), label="TN controlled-channel scope"
        )
        if (
            channel_factor.get("template_id") != "COHERENT_Z"
            or channel_factor.get("shape") != [4, 4, 2]
            or len(channel_scope) != 3
            or channel_scope[2] != mu
            or channel_provenance.get("role") != "CONTROLLED_CHANNEL"
            or channel_provenance.get("event_id") != event_id
            or channel_provenance.get("ordinal") != occurrence
        ):
            raise ValueError("TN controlled channel does not use its ledgered sign")
        if pair_kernels[event_id].get("kind") != "COHERENT_Z":
            raise ValueError("pair/TN coherent occurrence kinds disagree")

        for index_id, role, index_ordinal in (
            (mu, "SIGN_OCCURRENCE", occurrence),
            (next_sign, "SIGN_CHAIN_OUTPUT", occurrence + 1),
        ):
            index = indices.get(str(index_id))
            if index is None:
                raise ValueError("TN sign ledger references an unknown sign index")
            provenance = _audit_object(
                index.get("provenance"), label="TN sign-index provenance"
            )
            if (
                index.get("kind") != "SIGN"
                or index.get("domain") != 2
                or provenance.get("event_id") != event_id
                or provenance.get("role") != role
                or provenance.get("ordinal") != index_ordinal
            ):
                raise ValueError("TN sign index does not match its ordered ledger role")

        used_chain_factors.add(str(chain_factor_id))
        used_channel_factors.add(str(channel_factor_id))
        expected_sign_indices.update((str(mu), str(next_sign)))
        occurrences.append(
            {
                "occurrence": occurrence,
                "neutral_event_ordinal": event_ordinal,
                "event_id": event_id,
                "pair_input_checkpoint": pair_kernels[event_id]["input_checkpoint"],
                "pair_output_checkpoint": pair_kernels[event_id]["output_checkpoint"],
                "previous_sign": previous_sign,
                "mu": mu,
                "next_sign": next_sign,
                "chain_factor": chain_factor_id,
                "channel_factor": channel_factor_id,
            }
        )
        previous_sign = next_sign

    if used_chain_factors != sign_eq_factors:
        raise ValueError("TN owns an unledgered SIGN_EQ factor")
    if used_channel_factors != coherent_factors:
        raise ValueError("TN owns an unledgered coherent channel factor")

    sign_indices = {
        index_id
        for index_id, index in indices.items()
        if index.get("kind") == "SIGN"
    }
    if sign_indices != expected_sign_indices:
        raise ValueError("TN owns an unledgered or missing persistent-sign index")
    prior_index = indices.get(str(prior_sign))
    if prior_index is None:
        raise ValueError("TN sign prior references an unknown sign index")
    prior_index_provenance = _audit_object(
        prior_index.get("provenance"), label="TN sign-prior index provenance"
    )
    if (
        prior_index.get("kind") != "SIGN"
        or prior_index.get("domain") != 2
        or prior_index_provenance.get("event_id") is not None
        or prior_index_provenance.get("role") != "SIGN_PRIOR"
        or prior_index_provenance.get("ordinal") != 0
    ):
        raise ValueError("TN sign-prior index is malformed")

    terminals = [
        factor
        for factor in factors.values()
        if _audit_object(
            factor.get("provenance"), label="TN factor provenance"
        ).get("role")
        == "SIGN_TERMINAL"
    ]
    if len(terminals) != 1:
        raise ValueError("TN persistent sign chain must own one terminal")
    terminal = terminals[0]
    if (
        terminal.get("template_id") != "ONE"
        or terminal.get("shape") != [2]
        or terminal.get("scope") != [previous_sign]
    ):
        raise ValueError("TN sign terminal does not close the persistent chain")
    return occurrences


class PersistentSignLoweringAuditError(ValueError):
    """Fail-closed aggregate from all independently runnable subchecks."""

    def __init__(
        self,
        failures: Sequence[Mapping[str, str]],
        *,
        subchecks: Mapping[str, str],
    ) -> None:
        self.failures = tuple(dict(failure) for failure in failures)
        self.subchecks = dict(subchecks)
        summary = "; ".join(
            f"{failure['subcheck']}: {failure['message']}"
            for failure in self.failures
        )
        super().__init__(f"persistent sign lowering audit failed: {summary}")


def audit_persistent_sign_lowering(
    neutral_semantic: Mapping[str, Any],
    pair_semantic: Mapping[str, Any],
    tn_semantic: Mapping[str, Any],
) -> dict[str, Any]:
    """Audit one persistent sign from process declaration through both targets.

    The audit consumes only public semantic mappings.  It reconstructs no
    target object and imports no neutral, pair, TN, report, or micro-owner
    implementation.  A passing receipt establishes static latent/incidence
    consistency only; it does not run a frontier, contract a network, or make
    a Record-law claim.
    """

    neutral = _audit_object(neutral_semantic, label="neutral semantic")
    pair = _audit_object(pair_semantic, label="pair semantic")
    tn = _audit_object(tn_semantic, label="TN semantic")
    failures: list[dict[str, str]] = []
    subchecks = {
        "neutral_process": "PASS",
        "pair_latent": "BLOCKED",
        "tn_sign_chain": "BLOCKED",
    }
    try:
        _audit_persistent_neutral_declaration(neutral)
    except (TypeError, ValueError) as exc:
        subchecks["neutral_process"] = "FAIL"
        failures.append(
            {"subcheck": "neutral_process", "message": str(exc)}
        )

    coherent: list[tuple[int, str]] | None = None
    try:
        coherent = _audit_neutral_coherent_occurrences(neutral)
    except (TypeError, ValueError) as exc:
        subchecks["neutral_process"] = "FAIL"
        failures.append(
            {"subcheck": "neutral_process", "message": str(exc)}
        )

    pair_kernels: dict[str, Mapping[str, Any]] | None = None
    if coherent is not None:
        try:
            pair_kernels = _audit_pair_latent_binding(
                pair, neutral, coherent
            )
            subchecks["pair_latent"] = "PASS"
        except (TypeError, ValueError) as exc:
            subchecks["pair_latent"] = "FAIL"
            failures.append(
                {"subcheck": "pair_latent", "message": str(exc)}
            )

    occurrences: list[dict[str, Any]] | None = None
    if coherent is not None and pair_kernels is not None:
        try:
            occurrences = _audit_tn_sign_chain(
                tn, coherent, pair_kernels
            )
            subchecks["tn_sign_chain"] = "PASS"
        except (TypeError, ValueError) as exc:
            subchecks["tn_sign_chain"] = "FAIL"
            failures.append(
                {"subcheck": "tn_sign_chain", "message": str(exc)}
            )

    if failures:
        raise PersistentSignLoweringAuditError(
            failures, subchecks=subchecks
        )
    if coherent is None or occurrences is None:
        raise AssertionError("persistent sign audit reached an incomplete clean state")
    receipt: dict[str, Any] = {
        "status": "PASS",
        "scope": "STATIC_PERSISTENT_SIGN_LOWERING_ONLY",
        "subchecks": subchecks,
        "coherent_occurrence_count": len(coherent),
        "occurrences": occurrences,
    }
    receipt["receipt_sha256"] = _sha256_json(receipt)
    return receipt
