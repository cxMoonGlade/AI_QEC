"""Implementation-separated SymPy oracle for the frozen pair/ADD microfixture.

The literal fixture, codecs, recurrence, exact serialization, and hashing in
this module are intentionally repeated without importing any owner module.
This is a micro-qualification oracle only; it neither lowers the target QEC
experiment nor grants permission to implement a solver.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from itertools import product
import json

from sympy import Expr, I, Rational, __version__ as SYMPY_VERSION, expand, simplify, sqrt


ORACLE_SCOPE = "MICRO_QUALIFICATION_ONLY"
TARGET_LOWERING_STATUS = "UNAVAILABLE"
SOLVER_PERMISSION_STATUS = "CODE_BLOCKED"

FIELDS_WITHOUT_RECORD = ("L.x", "L.z", "R.x", "R.z", "m", "frame")
FIELDS_WITH_RECORD = FIELDS_WITHOUT_RECORD + ("d0",)
CHECKPOINT_FIELDS = (
    FIELDS_WITHOUT_RECORD,
    FIELDS_WITHOUT_RECORD,
    FIELDS_WITH_RECORD,
)


@dataclass(frozen=True, slots=True)
class LiteralKey:
    """Oracle-local semantic key; no owner key or codec is reused."""

    lx: int
    lz: int
    rx: int
    rz: int
    latent_m: int
    frame: int
    record: tuple[int, ...]

    def __post_init__(self) -> None:
        for name, value in (
            ("lx", self.lx),
            ("lz", self.lz),
            ("rx", self.rx),
            ("rz", self.rz),
            ("frame", self.frame),
        ):
            if type(value) is not int or value not in (0, 1):
                raise ValueError(f"{name} must be a bit")
        if type(self.latent_m) is not int or self.latent_m not in (-1, 1):
            raise ValueError("latent_m must be -1 or +1")
        if type(self.record) is not tuple or any(
            type(bit) is not int or bit not in (0, 1) for bit in self.record
        ):
            raise ValueError("record must be a tuple of bits")


def _validate_fields(fields: tuple[str, ...]) -> None:
    if type(fields) is not tuple or fields not in (
        FIELDS_WITHOUT_RECORD,
        FIELDS_WITH_RECORD,
    ):
        raise ValueError("oracle codec fields are not one of the two literal codecs")


def encode_literal_key(key: LiteralKey, fields: tuple[str, ...]) -> tuple[int, ...]:
    """Independently encode one semantic oracle key."""

    _validate_fields(fields)
    record_bits = 1 if fields == FIELDS_WITH_RECORD else 0
    if len(key.record) != record_bits:
        raise ValueError("semantic key Record length disagrees with oracle codec")
    values = {
        "L.x": key.lx,
        "L.z": key.lz,
        "R.x": key.rx,
        "R.z": key.rz,
        "m": 0 if key.latent_m == -1 else 1,
        "frame": key.frame,
    }
    if record_bits:
        values["d0"] = key.record[0]
    return tuple(values[field] for field in fields)


def decode_literal_bits(bits: tuple[int, ...], fields: tuple[str, ...]) -> LiteralKey:
    """Independently decode all fields, including latent and Record bits."""

    _validate_fields(fields)
    if type(bits) is not tuple or len(bits) != len(fields) or any(
        type(bit) is not int or bit not in (0, 1) for bit in bits
    ):
        raise ValueError("oracle assignment is not a full bit tuple")
    values = dict(zip(fields, bits, strict=True))
    record = (values["d0"],) if fields == FIELDS_WITH_RECORD else ()
    return LiteralKey(
        lx=values["L.x"],
        lz=values["L.z"],
        rx=values["R.x"],
        rz=values["R.z"],
        latent_m=-1 if values["m"] == 0 else 1,
        frame=values["frame"],
        record=record,
    )


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _local_sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _rational_pair(value: Expr) -> list[int]:
    exact = simplify(value)
    if exact.is_Rational is not True:
        raise ValueError(f"coefficient is outside Q(sqrt(2), i): {exact}")
    numerator, denominator = exact.as_numer_denom()
    return [int(numerator), int(denominator)]


def _expression_data(value: Expr) -> list[list[int]]:
    """Decompose a SymPy expression in the independent 1,sqrt2,i,i*sqrt2 basis."""

    root_two = sqrt(2)
    real_part, imaginary_part = simplify(value).as_real_imag(deep=True)
    real_part = expand(real_part)
    imaginary_part = expand(imaginary_part)
    real_root_two = simplify(real_part.coeff(root_two))
    real_rational = simplify(real_part - real_root_two * root_two)
    imaginary_root_two = simplify(imaginary_part.coeff(root_two))
    imaginary_rational = simplify(imaginary_part - imaginary_root_two * root_two)
    return [
        _rational_pair(real_rational),
        _rational_pair(real_root_two),
        _rational_pair(imaginary_rational),
        _rational_pair(imaginary_root_two),
    ]


def _key_data(key: LiteralKey) -> dict[str, object]:
    return {
        "L": {"x": key.lx, "z": key.lz},
        "R": {"x": key.rx, "z": key.rz},
        "frame": key.frame,
        "latent_m": key.latent_m,
        "record_prefix": list(key.record),
    }


def _zero_key(latent_m: int) -> LiteralKey:
    return LiteralKey(0, 0, 0, 0, latent_m, 0, ())


def _a_key(latent_m: int) -> LiteralKey:
    return LiteralKey(1, 0, 0, 0, latent_m, 0, ())


def _b_key(latent_m: int) -> LiteralKey:
    return LiteralKey(0, 1, 1, 0, latent_m, 1, ())


def _c_key(latent_m: int) -> LiteralKey:
    return LiteralKey(1, 1, 0, 1, latent_m, 1, ())


def _d_key(latent_m: int) -> LiteralKey:
    return LiteralKey(0, 0, 1, 1, latent_m, 0, ())


def _y_key(latent_m: int) -> LiteralKey:
    m_bit = 0 if latent_m == -1 else 1
    return LiteralKey(1, 0, 1, 0, latent_m, 1 - m_bit, (m_bit,))


def _z_key(latent_m: int) -> LiteralKey:
    m_bit = 0 if latent_m == -1 else 1
    return LiteralKey(0, 1, 0, 1, latent_m, m_bit, (1 - m_bit,))


def _literal_fixture() -> tuple[
    tuple[tuple[LiteralKey, Expr], ...],
    tuple[tuple[str, tuple[tuple[LiteralKey, LiteralKey, Expr], ...]], ...],
]:
    """Construct the literal fixture independently from owner data structures."""

    initial = tuple((_zero_key(m), Rational(1, 2)) for m in (-1, 1))
    first_rows: list[tuple[LiteralKey, LiteralKey, Expr]] = []
    second_rows: list[tuple[LiteralKey, LiteralKey, Expr]] = []
    delta = Rational(1, 2**40)
    for m in (-1, 1):
        source = _zero_key(m)
        first_rows.extend(
            (
                (source, _a_key(m), Rational(1)),
                (source, _b_key(m), sqrt(2) / 2),
                (source, _c_key(m), I),
                (source, _d_key(m), -I * sqrt(2) / 2),
            )
        )
        second_rows.extend(
            (
                (_a_key(m), _y_key(m), Rational(1)),
                (_b_key(m), _y_key(m), -sqrt(2) + delta),
                (_c_key(m), _z_key(m), Rational(1)),
                (_d_key(m), _z_key(m), sqrt(2)),
            )
        )
    return initial, (
        ("E1_BRANCH", tuple(first_rows)),
        ("E2_INTERFERE_AND_EMIT", tuple(second_rows)),
    )


def _insert_exact(
    target: dict[LiteralKey, Expr], key: LiteralKey, increment: Expr
) -> None:
    combined = simplify(target.get(key, Rational(0)) + increment)
    if combined == 0:
        target.pop(key, None)
    else:
        target[key] = combined


def _advance_literal_map(
    current: dict[LiteralKey, Expr],
    rows: tuple[tuple[LiteralKey, LiteralKey, Expr], ...],
) -> dict[LiteralKey, Expr]:
    rows_by_input: dict[LiteralKey, list[tuple[LiteralKey, Expr]]] = {}
    for input_key, output_key, weight in rows:
        rows_by_input.setdefault(input_key, []).append((output_key, weight))
    result: dict[LiteralKey, Expr] = {}
    for input_key, coefficient in current.items():
        for output_key, weight in rows_by_input.get(input_key, ()):
            _insert_exact(result, output_key, coefficient * weight)
    return result


def _codec_receipt(label: str, fields: tuple[str, ...]) -> dict[str, object]:
    reencoded: list[list[int]] = []
    for bits in product((0, 1), repeat=len(fields)):
        decoded = decode_literal_bits(bits, fields)
        recovered = encode_literal_key(decoded, fields)
        if recovered != bits:
            raise AssertionError("independent codec failed an exhaustive round trip")
        reencoded.append(list(recovered))
    return {
        "fields": list(fields),
        "label": label,
        "roundtrip_assignment_count": len(reencoded),
        "roundtrip_sha256": _local_sha256(reencoded),
        "width": len(fields),
    }


def _checkpoint_receipt(
    label: str,
    fields: tuple[str, ...],
    coefficient_map: dict[LiteralKey, Expr],
) -> dict[str, object]:
    witnesses = [
        {
            "bits": list(encode_literal_key(key, fields)),
            "coefficient": _expression_data(coefficient),
            "key": _key_data(key),
        }
        for key, coefficient in coefficient_map.items()
    ]
    witnesses.sort(key=lambda entry: tuple(entry["bits"]))

    dense_values: list[list[list[int]]] = []
    roundtrips: list[list[int]] = []
    for bits in product((0, 1), repeat=len(fields)):
        key = decode_literal_bits(bits, fields)
        recovered = encode_literal_key(key, fields)
        if recovered != bits:
            raise AssertionError("checkpoint codec failed an exhaustive round trip")
        roundtrips.append(list(recovered))
        dense_values.append(_expression_data(coefficient_map.get(key, Rational(0))))
    return {
        "dense_values_sha256": _local_sha256(
            {
                "enumeration": "LEXICOGRAPHIC_BINARY_PRODUCT_0_THEN_1",
                "fields": list(fields),
                "values": dense_values,
            }
        ),
        "exhaustive_assignment_count": len(dense_values),
        "fields": list(fields),
        "label": label,
        "nonzero_count": len(witnesses),
        "nonzero_witnesses": witnesses,
        "nonzero_witnesses_sha256": _local_sha256(witnesses),
        "roundtrip_sha256": _local_sha256(roundtrips),
        "support": len(witnesses),
        "width": len(fields),
    }


def _relation_receipt(
    event: str,
    input_fields: tuple[str, ...],
    output_fields: tuple[str, ...],
    rows: tuple[tuple[LiteralKey, LiteralKey, Expr], ...],
) -> dict[str, object]:
    relation: dict[tuple[int, ...], Expr] = {}
    for input_key, output_key, weight in rows:
        combined = encode_literal_key(input_key, input_fields) + encode_literal_key(
            output_key, output_fields
        )
        updated = simplify(relation.get(combined, Rational(0)) + weight)
        if updated == 0:
            relation.pop(combined, None)
        else:
            relation[combined] = updated

    witnesses = []
    for combined, coefficient in relation.items():
        input_bits = combined[: len(input_fields)]
        output_bits = combined[len(input_fields) :]
        witnesses.append(
            {
                "coefficient": _expression_data(coefficient),
                "combined_bits": list(combined),
                "input_bits": list(input_bits),
                "input_key": _key_data(decode_literal_bits(input_bits, input_fields)),
                "output_bits": list(output_bits),
                "output_key": _key_data(decode_literal_bits(output_bits, output_fields)),
            }
        )
    witnesses.sort(key=lambda entry: tuple(entry["combined_bits"]))

    width = len(input_fields) + len(output_fields)
    dense_values: list[list[list[int]]] = []
    roundtrips: list[list[int]] = []
    for combined in product((0, 1), repeat=width):
        input_bits = combined[: len(input_fields)]
        output_bits = combined[len(input_fields) :]
        input_key = decode_literal_bits(input_bits, input_fields)
        output_key = decode_literal_bits(output_bits, output_fields)
        recovered = encode_literal_key(input_key, input_fields) + encode_literal_key(
            output_key, output_fields
        )
        if recovered != combined:
            raise AssertionError("combined input/output codec failed an exhaustive round trip")
        roundtrips.append(list(recovered))
        dense_values.append(_expression_data(relation.get(combined, Rational(0))))

    combined_order = tuple(f"in:{field}" for field in input_fields) + tuple(
        f"out:{field}" for field in output_fields
    )
    return {
        "combined_order": list(combined_order),
        "dense_values_sha256": _local_sha256(
            {
                "enumeration": "LEXICOGRAPHIC_BINARY_PRODUCT_0_THEN_1",
                "order": list(combined_order),
                "values": dense_values,
            }
        ),
        "event": event,
        "exhaustive_assignment_count": len(dense_values),
        "input_fields": list(input_fields),
        "input_width": len(input_fields),
        "nonzero_count": len(witnesses),
        "nonzero_witnesses": witnesses,
        "nonzero_witnesses_sha256": _local_sha256(witnesses),
        "output_fields": list(output_fields),
        "output_width": len(output_fields),
        "roundtrip_assignment_count": len(roundtrips),
        "roundtrip_sha256": _local_sha256(roundtrips),
    }


def run_independent_sympy_pair_add_oracle() -> dict[str, object]:
    """Run the independent exact literal oracle over every represented code."""

    initial, events = _literal_fixture()
    current: dict[LiteralKey, Expr] = {}
    for key, coefficient in initial:
        _insert_exact(current, key, coefficient)
    maps = [current]
    for _event, rows in events:
        current = _advance_literal_map(current, rows)
        maps.append(current)

    checkpoint_labels = ("A0", events[0][0], events[1][0])
    checkpoints = [
        _checkpoint_receipt(label, fields, coefficient_map)
        for label, fields, coefficient_map in zip(
            checkpoint_labels, CHECKPOINT_FIELDS, maps, strict=True
        )
    ]
    relations = [
        _relation_receipt(
            event,
            CHECKPOINT_FIELDS[index],
            CHECKPOINT_FIELDS[index + 1],
            rows,
        )
        for index, (event, rows) in enumerate(events)
    ]

    delta = Rational(1, 2**40)
    tail = simplify(Rational(1, 2) + sqrt(2) / 4 * (-sqrt(2) + delta))
    deleted_zero = simplify(I / 2 + (-I * sqrt(2) / 4) * sqrt(2))
    result: dict[str, object] = {
        "checkpoint_literal_maps": checkpoints,
        "codecs": [
            _codec_receipt(label, fields)
            for label, fields in zip(("A0", "A1", "A2"), CHECKPOINT_FIELDS, strict=True)
        ],
        "interference_evidence": {
            "deleted_zero": _expression_data(deleted_zero),
            "deleted_zero_is_exact": bool(deleted_zero == 0),
            "delta": _expression_data(delta),
            "tail": _expression_data(tail),
            "tail_is_strictly_positive": bool(tail > 0),
            "tail_squared_is_below_1e_minus_24": bool(
                simplify(tail**2) < Rational(1, 10**24)
            ),
        },
        "oracle": "INDEPENDENT_SYMPY_PAIR_ADD_LITERAL_ORACLE",
        "relations": relations,
        "scope": ORACLE_SCOPE,
        "solver_permission": SOLVER_PERMISSION_STATUS,
        "support_history": [len(coefficient_map) for coefficient_map in maps],
        "sympy_version": SYMPY_VERSION,
        "target_lowering": TARGET_LOWERING_STATUS,
    }
    result["oracle_payload_sha256"] = _local_sha256(result)
    return result
