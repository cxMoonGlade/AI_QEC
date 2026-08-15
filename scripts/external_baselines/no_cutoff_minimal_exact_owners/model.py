"""Frozen exact algebra and pair/ADD microfixture.

This module owns fixture identity, not target QEC lowering.  Its Pauli labels
use trivial rank-zero cosets and cannot qualify the target RREF/frame builder.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
from typing import Iterable


MICRO_SCOPE = "MICRO_QUALIFICATION_ONLY"
SOLVER_PERMISSION = "CODE_BLOCKED"
TARGET_LOWERING = "UNAVAILABLE"


def canonical_json_bytes(value: object) -> bytes:
    """Return the one frozen canonical-JSON encoding, without a trailing LF."""

    return json.dumps(
        value,
        sort_keys=True,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _fraction_data(value: Fraction) -> list[int]:
    if type(value) is not Fraction:
        raise TypeError("exact coefficients require fractions.Fraction")
    if value.denominator <= 0:
        raise ValueError("fraction denominator must be positive")
    return [value.numerator, value.denominator]


@dataclass(frozen=True, slots=True)
class Qsqrt2i:
    """An element a+b*sqrt(2)+i(c+d*sqrt(2)), stored as four rationals."""

    a: Fraction
    b: Fraction
    c: Fraction
    d: Fraction

    def __post_init__(self) -> None:
        for value in (self.a, self.b, self.c, self.d):
            _fraction_data(value)

    @classmethod
    def rational(cls, numerator: int, denominator: int = 1) -> Qsqrt2i:
        if type(numerator) is not int or type(denominator) is not int:
            raise TypeError("rational components require integers")
        return cls(
            Fraction(numerator, denominator),
            Fraction(0),
            Fraction(0),
            Fraction(0),
        )

    @classmethod
    def sqrt2(cls, coefficient: Fraction = Fraction(1)) -> Qsqrt2i:
        if type(coefficient) is not Fraction:
            raise TypeError("sqrt(2) coefficient must be Fraction")
        return cls(Fraction(0), coefficient, Fraction(0), Fraction(0))

    @classmethod
    def imag(cls, coefficient: Fraction = Fraction(1)) -> Qsqrt2i:
        if type(coefficient) is not Fraction:
            raise TypeError("imaginary coefficient must be Fraction")
        return cls(Fraction(0), Fraction(0), coefficient, Fraction(0))

    def to_data(self) -> list[list[int]]:
        return [_fraction_data(x) for x in (self.a, self.b, self.c, self.d)]

    def __add__(self, other: object) -> Qsqrt2i:
        if not isinstance(other, Qsqrt2i):
            return NotImplemented
        return Qsqrt2i(
            self.a + other.a,
            self.b + other.b,
            self.c + other.c,
            self.d + other.d,
        )

    def __neg__(self) -> Qsqrt2i:
        return Qsqrt2i(-self.a, -self.b, -self.c, -self.d)

    def __sub__(self, other: object) -> Qsqrt2i:
        if not isinstance(other, Qsqrt2i):
            return NotImplemented
        return self + (-other)

    @staticmethod
    def _mul_real_pair(
        left: tuple[Fraction, Fraction],
        right: tuple[Fraction, Fraction],
    ) -> tuple[Fraction, Fraction]:
        a, b = left
        c, d = right
        return a * c + 2 * b * d, a * d + b * c

    def __mul__(self, other: object) -> Qsqrt2i:
        if not isinstance(other, Qsqrt2i):
            return NotImplemented
        real_left = (self.a, self.b)
        imag_left = (self.c, self.d)
        real_right = (other.a, other.b)
        imag_right = (other.c, other.d)
        rr = self._mul_real_pair(real_left, real_right)
        ii = self._mul_real_pair(imag_left, imag_right)
        ri = self._mul_real_pair(real_left, imag_right)
        ir = self._mul_real_pair(imag_left, real_right)
        return Qsqrt2i(rr[0] - ii[0], rr[1] - ii[1], ri[0] + ir[0], ri[1] + ir[1])

    def is_zero(self) -> bool:
        return self == ZERO


ZERO = Qsqrt2i.rational(0)
ONE = Qsqrt2i.rational(1)
I = Qsqrt2i.imag()
SQRT2 = Qsqrt2i.sqrt2()


@dataclass(frozen=True, slots=True)
class PairKey:
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

    @property
    def m_bit(self) -> int:
        return 0 if self.latent_m == -1 else 1

    def to_data(self) -> dict[str, object]:
        return {
            "L": {"x": self.lx, "z": self.lz},
            "R": {"x": self.rx, "z": self.rz},
            "frame": self.frame,
            "latent_m": self.latent_m,
            "record_prefix": list(self.record),
        }


FROZEN_CODEC_0_FIELDS = ("L.x", "L.z", "R.x", "R.z", "m", "frame")
FROZEN_CODEC_2_FIELDS = FROZEN_CODEC_0_FIELDS + ("d0",)


@dataclass(frozen=True, slots=True)
class Codec:
    name: str
    fields: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.name) is not str or not self.name:
            raise ValueError("codec name must be nonempty")
        if type(self.fields) is not tuple or any(type(x) is not str for x in self.fields):
            raise TypeError("codec fields must be a tuple of strings")
        if len(set(self.fields)) != len(self.fields):
            raise ValueError("codec fields must be unique")
        if set(self.fields) not in (set(FROZEN_CODEC_0_FIELDS), set(FROZEN_CODEC_2_FIELDS)):
            raise ValueError("codec has missing or unknown semantic fields")

    @property
    def width(self) -> int:
        return len(self.fields)

    @property
    def record_bits(self) -> int:
        return 1 if "d0" in self.fields else 0

    def encode(self, key: PairKey) -> tuple[int, ...]:
        if len(key.record) != self.record_bits:
            raise ValueError("key Record prefix length disagrees with codec")
        values = {
            "L.x": key.lx,
            "L.z": key.lz,
            "R.x": key.rx,
            "R.z": key.rz,
            "m": key.m_bit,
            "frame": key.frame,
        }
        if self.record_bits:
            values["d0"] = key.record[0]
        return tuple(values[field] for field in self.fields)

    def to_data(self) -> dict[str, object]:
        return {
            "fields": list(self.fields),
            "key_schema": "trivial_coset_pair_latent_frame_record_prefix.v1",
            "name": self.name,
            "record_bits": self.record_bits,
        }

    @property
    def sha256(self) -> str:
        return sha256_json(self.to_data())


@dataclass(frozen=True, slots=True)
class TransitionRow:
    input_key: PairKey
    output_key: PairKey
    weight: Qsqrt2i

    def to_data(self, input_codec: Codec, output_codec: Codec) -> dict[str, object]:
        return {
            "input_bits": list(input_codec.encode(self.input_key)),
            "output_bits": list(output_codec.encode(self.output_key)),
            "weight": self.weight.to_data(),
        }


@dataclass(frozen=True, slots=True)
class Event:
    name: str
    rows: tuple[TransitionRow, ...]

    def to_data(self, input_codec: Codec, output_codec: Codec) -> dict[str, object]:
        rows = [row.to_data(input_codec, output_codec) for row in self.rows]
        rows.sort(key=canonical_json_bytes)
        return {"name": self.name, "rows": rows}


@dataclass(frozen=True, slots=True)
class PairAddProgram:
    codecs: tuple[Codec, ...]
    initial: tuple[tuple[PairKey, Qsqrt2i], ...]
    events: tuple[Event, ...]

    def __post_init__(self) -> None:
        if len(self.codecs) != len(self.events) + 1:
            raise ValueError("program requires one codec per checkpoint")
        for key, _ in self.initial:
            self.codecs[0].encode(key)
        for index, event in enumerate(self.events):
            for row in event.rows:
                self.codecs[index].encode(row.input_key)
                self.codecs[index + 1].encode(row.output_key)

    def to_data(self) -> dict[str, object]:
        initial = [
            {
                "bits": list(self.codecs[0].encode(key)),
                "coefficient": coefficient.to_data(),
            }
            for key, coefficient in self.initial
        ]
        initial.sort(key=canonical_json_bytes)
        return {
            "codecs": [codec.to_data() for codec in self.codecs],
            "events": [
                event.to_data(self.codecs[index], self.codecs[index + 1])
                for index, event in enumerate(self.events)
            ],
            "initial": initial,
            "route": "trivial_coset_exact_pair_add_micro.v1",
            "scope": MICRO_SCOPE,
        }

    @property
    def sha256(self) -> str:
        return sha256_json(self.to_data())


def _a_key(m: int) -> PairKey:
    return PairKey(1, 0, 0, 0, m, 0, ())


def _b_key(m: int) -> PairKey:
    return PairKey(0, 1, 1, 0, m, 1, ())


def _c_key(m: int) -> PairKey:
    return PairKey(1, 1, 0, 1, m, 1, ())


def _d_key(m: int) -> PairKey:
    return PairKey(0, 0, 1, 1, m, 0, ())


def _y_key(m: int) -> PairKey:
    m_bit = 0 if m == -1 else 1
    return PairKey(1, 0, 1, 0, m, 1 - m_bit, (m_bit,))


def _z_key(m: int) -> PairKey:
    m_bit = 0 if m == -1 else 1
    return PairKey(0, 1, 0, 1, m, m_bit, (1 - m_bit,))


def frozen_fixture_keys() -> dict[str, tuple[PairKey, PairKey]]:
    return {
        label: (factory(-1), factory(1))
        for label, factory in (
            ("a", _a_key),
            ("b", _b_key),
            ("c", _c_key),
            ("d", _d_key),
            ("y", _y_key),
            ("z", _z_key),
        )
    }


def frozen_pair_add_program(*, reverse_rows: bool = False) -> PairAddProgram:
    codec0 = Codec("A0", FROZEN_CODEC_0_FIELDS)
    codec1 = Codec("A1", FROZEN_CODEC_0_FIELDS)
    codec2 = Codec("A2", FROZEN_CODEC_2_FIELDS)
    initial = tuple(
        (PairKey(0, 0, 0, 0, m, 0, ()), Qsqrt2i.rational(1, 2))
        for m in (-1, 1)
    )
    e1_rows: list[TransitionRow] = []
    e2_rows: list[TransitionRow] = []
    delta = Qsqrt2i.rational(1, 2**40)
    for m in (-1, 1):
        initial_key = PairKey(0, 0, 0, 0, m, 0, ())
        e1_rows.extend(
            (
                TransitionRow(initial_key, _a_key(m), ONE),
                TransitionRow(initial_key, _b_key(m), Qsqrt2i.sqrt2(Fraction(1, 2))),
                TransitionRow(initial_key, _c_key(m), I),
                TransitionRow(
                    initial_key,
                    _d_key(m),
                    Qsqrt2i(Fraction(0), Fraction(0), Fraction(0), Fraction(-1, 2)),
                ),
            )
        )
        e2_rows.extend(
            (
                TransitionRow(_a_key(m), _y_key(m), ONE),
                TransitionRow(_b_key(m), _y_key(m), -SQRT2 + delta),
                TransitionRow(_c_key(m), _z_key(m), ONE),
                TransitionRow(_d_key(m), _z_key(m), SQRT2),
            )
        )
    if reverse_rows:
        e1_rows.reverse()
        e2_rows.reverse()
    return PairAddProgram(
        codecs=(codec0, codec1, codec2),
        initial=initial,
        events=(
            Event("E1_BRANCH", tuple(e1_rows)),
            Event("E2_INTERFERE_AND_EMIT", tuple(e2_rows)),
        ),
    )


def validate_frozen_pair_add_program(program: PairAddProgram) -> None:
    expected_fields = (
        FROZEN_CODEC_0_FIELDS,
        FROZEN_CODEC_0_FIELDS,
        FROZEN_CODEC_2_FIELDS,
    )
    if tuple(codec.fields for codec in program.codecs) != expected_fields:
        raise ValueError("program does not use the frozen codec order")
    if tuple(event.name for event in program.events) != (
        "E1_BRANCH",
        "E2_INTERFERE_AND_EMIT",
    ):
        raise ValueError("program does not use the frozen event order")
    if program.sha256 != frozen_pair_add_program().sha256:
        raise ValueError("program does not match the frozen fixture identity")


def exact_sum(values: Iterable[Qsqrt2i]) -> Qsqrt2i:
    total = ZERO
    for value in values:
        total = total + value
    return total
