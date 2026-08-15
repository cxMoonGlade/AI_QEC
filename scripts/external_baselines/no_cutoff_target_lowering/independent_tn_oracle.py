"""Independent exact-table oracle for the retained-boundary TN lowering.

This module deliberately owns its exact scalar algebra and literal gate
matrices.  It does not import the target lowering, its shared model, or the
earlier micro-owner package, so agreement checks do not share table-building
code with the owner under test.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class _Exact:
    """A literal element of Q(sqrt(2), i).

    Components are ordered as ``a + b*sqrt(2) + i*(c + d*sqrt(2))``.
    """

    a: Fraction = Fraction(0)
    b: Fraction = Fraction(0)
    c: Fraction = Fraction(0)
    d: Fraction = Fraction(0)

    def __add__(self, other: _Exact) -> _Exact:
        return _Exact(
            self.a + other.a,
            self.b + other.b,
            self.c + other.c,
            self.d + other.d,
        )

    def __neg__(self) -> _Exact:
        return _Exact(-self.a, -self.b, -self.c, -self.d)

    def __sub__(self, other: _Exact) -> _Exact:
        return self + (-other)

    def __mul__(self, other: _Exact) -> _Exact:
        # (a+b*r)(e+f*r) with r**2=2, applied to real/imaginary pairs.
        rr_a = self.a * other.a + 2 * self.b * other.b
        rr_b = self.a * other.b + self.b * other.a
        ii_a = self.c * other.c + 2 * self.d * other.d
        ii_b = self.c * other.d + self.d * other.c
        ri_a = self.a * other.c + 2 * self.b * other.d
        ri_b = self.a * other.d + self.b * other.c
        ir_a = self.c * other.a + 2 * self.d * other.b
        ir_b = self.c * other.b + self.d * other.a
        return _Exact(rr_a - ii_a, rr_b - ii_b, ri_a + ir_a, ri_b + ir_b)

    def conjugate(self) -> _Exact:
        return _Exact(self.a, self.b, -self.c, -self.d)

    def to_data(self) -> list[list[int]]:
        return [
            [part.numerator, part.denominator]
            for part in (self.a, self.b, self.c, self.d)
        ]


_ZERO = _Exact()
_ONE = _Exact(Fraction(1))
_HALF = _Exact(Fraction(1, 2))
_C = _Exact(Fraction(9999, 10001))
_IS = _Exact(c=Fraction(200, 10001))
_INV_SQRT2 = _Exact(b=Fraction(1, 2))


def _indicator(condition: bool) -> _Exact:
    return _ONE if condition else _ZERO


def _density_pair(code: int) -> tuple[int, int]:
    """Decode the frozen density codec ``code = 2*ket + bra``."""

    if type(code) is not int or code < 0 or code > 3:
        raise ValueError("density code must be one of 0, 1, 2, 3")
    return code // 2, code % 2


def _one_qubit_density_table(
    unitary: tuple[tuple[_Exact, _Exact], tuple[_Exact, _Exact]],
) -> list[_Exact]:
    values: list[_Exact] = []
    # Scope order is (q_in, q_out), with the last index varying fastest.
    for q_in, q_out in product(range(4), repeat=2):
        in_ket, in_bra = _density_pair(q_in)
        out_ket, out_bra = _density_pair(q_out)
        values.append(
            unitary[out_ket][in_ket]
            * unitary[out_bra][in_bra].conjugate()
        )
    return values


def _two_qubit_density_table(
    unitary: tuple[
        tuple[_Exact, _Exact, _Exact, _Exact],
        tuple[_Exact, _Exact, _Exact, _Exact],
        tuple[_Exact, _Exact, _Exact, _Exact],
        tuple[_Exact, _Exact, _Exact, _Exact],
    ],
) -> list[_Exact]:
    values: list[_Exact] = []
    # Scope order is control-in, target-in, control-out, target-out.
    for c_in, t_in, c_out, t_out in product(range(4), repeat=4):
        ci_ket, ci_bra = _density_pair(c_in)
        ti_ket, ti_bra = _density_pair(t_in)
        co_ket, co_bra = _density_pair(c_out)
        to_ket, to_bra = _density_pair(t_out)
        ket_in = 2 * ci_ket + ti_ket
        bra_in = 2 * ci_bra + ti_bra
        ket_out = 2 * co_ket + to_ket
        bra_out = 2 * co_bra + to_bra
        values.append(
            unitary[ket_out][ket_in] * unitary[bra_out][bra_in].conjugate()
        )
    return values


def _template(
    template_id: str,
    scope_kinds: list[str],
    shape: list[int],
    table: list[_Exact],
) -> dict[str, Any]:
    entries = 1
    for extent in shape:
        entries *= extent
    if len(table) != entries:
        raise AssertionError(f"{template_id}: literal table/shape mismatch")
    return {
        "template_id": template_id,
        "scope_kinds": scope_kinds,
        "shape": shape,
        "table": [value.to_data() for value in table],
    }


def reconstruct_table_catalog() -> list[dict[str, Any]]:
    """Reconstruct all fifteen preregistered tables from literal definitions."""

    h = (
        (_INV_SQRT2, _INV_SQRT2),
        (_INV_SQRT2, -_INV_SQRT2),
    )
    # Computational-basis order |00>, |01>, |10>, |11>; control first.
    cx = (
        (_ONE, _ZERO, _ZERO, _ZERO),
        (_ZERO, _ONE, _ZERO, _ZERO),
        (_ZERO, _ZERO, _ZERO, _ONE),
        (_ZERO, _ZERO, _ONE, _ZERO),
    )

    coherent: list[_Exact] = []
    for q_in, q_out, mu_bit in product(range(4), range(4), range(2)):
        # Frozen sign codec: 0 -> -1, 1 -> +1.
        mu = -1 if mu_bit == 0 else 1
        phase = _IS if mu == 1 else -_IS
        u_mu = (
            (_C - phase, _ZERO),
            (_ZERO, _C + phase),
        )
        coherent.append(_one_qubit_density_table(u_mu)[4 * q_in + q_out])

    reset = [
        _indicator(_density_pair(q_in)[0] == _density_pair(q_in)[1] and q_out == 0)
        for q_in, q_out in product(range(4), repeat=2)
    ]
    measure = [
        _indicator(q_in == 3 * raw and q_out == 3 * raw)
        for q_in, raw, q_out in product(range(4), range(2), range(4))
    ]
    measure_reset = [
        _indicator(q_in == 3 * raw and q_out == 0)
        for q_in, raw, q_out in product(range(4), range(2), range(4))
    ]
    sign_eq = [
        _indicator(previous == occurrence == following)
        for previous, occurrence, following in product(range(2), repeat=3)
    ]
    copy = [
        _indicator(source == consumer == terminal)
        for source, consumer, terminal in product(range(2), repeat=3)
    ]
    xor = [
        _indicator(output == (accumulator ^ raw))
        for accumulator, raw, output in product(range(2), repeat=3)
    ]

    # Canonical catalog order and every structural zero are explicit here.
    return [
        _template(
            "INIT0",
            ["DENSITY"],
            [4],
            [_ONE, _ZERO, _ZERO, _ZERO],
        ),
        _template(
            "TRACE",
            ["DENSITY"],
            [4],
            [_ONE, _ZERO, _ZERO, _ONE],
        ),
        _template(
            "H",
            ["DENSITY", "DENSITY"],
            [4, 4],
            _one_qubit_density_table(h),
        ),
        _template(
            "CX",
            ["DENSITY", "DENSITY", "DENSITY", "DENSITY"],
            [4, 4, 4, 4],
            _two_qubit_density_table(cx),
        ),
        _template(
            "COHERENT_Z",
            ["DENSITY", "DENSITY", "SIGN"],
            [4, 4, 2],
            coherent,
        ),
        _template("R", ["DENSITY", "DENSITY"], [4, 4], reset),
        _template(
            "M",
            ["DENSITY", "RAW", "DENSITY"],
            [4, 2, 4],
            measure,
        ),
        _template(
            "MR",
            ["DENSITY", "RAW", "DENSITY"],
            [4, 2, 4],
            measure_reset,
        ),
        _template("HALF", ["SIGN"], [2], [_HALF, _HALF]),
        _template(
            "SIGN_EQ",
            ["SIGN", "SIGN", "SIGN"],
            [2, 2, 2],
            sign_eq,
        ),
        _template("ONE", ["CLASSICAL"], [2], [_ONE, _ONE]),
        _template(
            "COPY",
            ["RAW", "CONSUMER", "RAW"],
            [2, 2, 2],
            copy,
        ),
        _template("ZERO", ["PARITY"], [2], [_ONE, _ZERO]),
        _template(
            "XOR",
            ["PARITY", "CONSUMER", "PARITY"],
            [2, 2, 2],
            xor,
        ),
        _template("KEEP", ["RECORD"], [2], [_ONE, _ONE]),
    ]


def validate_table_catalog(candidate: object) -> None:
    """Raise at the first template that differs from the independent catalog."""

    expected = reconstruct_table_catalog()
    if not isinstance(candidate, list):
        raise ValueError("INIT0: table catalog must be a list")

    for index, expected_template in enumerate(expected):
        name = expected_template["template_id"]
        if index >= len(candidate):
            raise ValueError(f"{name}: template is missing")
        actual = candidate[index]
        if not isinstance(actual, Mapping):
            raise ValueError(f"{name}: template row is not a mapping")
        if actual.get("template_id") != name:
            raise ValueError(f"{name}: template identity or order differs")
        for field in ("scope_kinds", "shape", "table"):
            if actual.get(field) != expected_template[field]:
                raise ValueError(f"{name}: {field} differs")
        if set(actual) != set(expected_template):
            raise ValueError(f"{name}: template fields differ")

    if len(candidate) > len(expected):
        extra = candidate[len(expected)]
        name = (
            extra.get("template_id", "<extra>")
            if isinstance(extra, Mapping)
            else "<extra>"
        )
        raise ValueError(f"{name}: unexpected extra template")


_INDEX_DOMAINS = {
    "DENSITY": 4,
    "SIGN": 2,
    "RAW": 2,
    "CONSUMER": 2,
    "PARITY": 2,
    "RECORD": 2,
}


def _scope_kind_accepts(
    template_id: str,
    slot: int,
    expected: str,
    actual: str,
) -> bool:
    """Independently interpret the two preregistered wire supertypes.

    ``ONE`` is the all-ones terminal for a persistent SIGN endpoint or a RAW
    COPY-chain endpoint, hence its catalog kind ``CLASSICAL`` denotes exactly
    those two terminal wire kinds.  A retained RECORD wire is the open-boundary
    subtype of a PARITY value, so it may occupy the output slot of the final
    XOR (and the input of the zero-output construction).
    """

    if expected == "CLASSICAL":
        return actual in {"SIGN", "RAW"}
    if expected == "PARITY" and actual == "RECORD":
        return (template_id, slot) in {("XOR", 2), ("ZERO", 0)}
    return actual == expected


def _validate_network_type_rows(
    index_catalog: object,
    factors: object,
    templates: object,
) -> None:
    if not isinstance(index_catalog, list):
        raise ValueError("TN index catalog must be a list")
    if not isinstance(factors, list):
        raise ValueError("TN factor catalog must be a list")
    if not isinstance(templates, list):
        raise ValueError("TN template catalog must be a list")

    kinds_by_id: dict[str, str] = {}
    domains_by_id: dict[str, int] = {}
    for row in index_catalog:
        if not isinstance(row, Mapping):
            raise ValueError("TN index row must be a mapping")
        index_id, kind, domain = row.get("index_id"), row.get("kind"), row.get("domain")
        if not isinstance(index_id, str) or not index_id:
            raise ValueError("TN index identity must be a nonempty string")
        if index_id in kinds_by_id:
            raise ValueError(f"duplicate TN index identity {index_id}")
        if not isinstance(kind, str) or kind not in _INDEX_DOMAINS:
            raise ValueError(f"{index_id}: unknown TN index kind {kind!r}")
        expected_domain = _INDEX_DOMAINS[kind]
        if type(domain) is not int or domain != expected_domain:
            raise ValueError(
                f"{index_id}: TN index domain {domain!r} does not match {kind}"
            )
        kinds_by_id[index_id] = kind
        domains_by_id[index_id] = domain

    templates_by_id: dict[str, Mapping[str, Any]] = {}
    for row in templates:
        if not isinstance(row, Mapping):
            raise ValueError("TN template row must be a mapping")
        template_id = row.get("template_id")
        if not isinstance(template_id, str) or template_id in templates_by_id:
            raise ValueError("TN template identities must be unique strings")
        templates_by_id[template_id] = row

    factor_ids: set[str] = set()
    for factor in factors:
        if not isinstance(factor, Mapping):
            raise ValueError("TN factor row must be a mapping")
        factor_id = factor.get("factor_id")
        template_id = factor.get("template_id")
        scope = factor.get("scope")
        shape = factor.get("shape")
        if not isinstance(factor_id, str) or factor_id in factor_ids:
            raise ValueError("TN factor identities must be unique strings")
        factor_ids.add(factor_id)
        if not isinstance(template_id, str) or template_id not in templates_by_id:
            raise ValueError(f"{factor_id}: unknown TN template {template_id!r}")
        template = templates_by_id[template_id]
        expected_kinds = template.get("scope_kinds")
        expected_shape = template.get("shape")
        if not isinstance(scope, list) or not isinstance(expected_kinds, list):
            raise ValueError(f"{factor_id}: TN factor scope typing is malformed")
        if shape != expected_shape or len(scope) != len(expected_kinds):
            raise ValueError(f"{factor_id}: TN factor scope/shape mismatch")
        for slot, (index_id, expected_kind, extent) in enumerate(
            zip(scope, expected_kinds, expected_shape, strict=True)
        ):
            if not isinstance(index_id, str) or index_id not in kinds_by_id:
                raise ValueError(
                    f"{factor_id}: TN factor slot {slot} references an unknown index"
                )
            if not isinstance(expected_kind, str) or type(extent) is not int:
                raise ValueError(f"{factor_id}: TN template slot {slot} is malformed")
            actual_kind = kinds_by_id[index_id]
            if not _scope_kind_accepts(
                template_id, slot, expected_kind, actual_kind
            ):
                raise ValueError(
                    f"{factor_id}: TN factor slot {slot} expects {expected_kind}, "
                    f"got {actual_kind}"
                )
            if domains_by_id[index_id] != extent:
                raise ValueError(
                    f"{factor_id}: TN factor slot {slot} domain/shape mismatch"
                )


def validate_network_types(candidate: object) -> None:
    """Independently reject an ill-typed retained-boundary TN semantic body."""

    if not isinstance(candidate, Mapping):
        raise ValueError("TN semantic body must be a mapping")
    table_catalog = candidate.get("table_catalog")
    validate_table_catalog(table_catalog)
    _validate_network_type_rows(
        candidate.get("index_catalog"),
        candidate.get("factors"),
        table_catalog,
    )


def validate_retained_boundary_keep_coverage(candidate: object) -> None:
    """Require exactly one KEEP factor on every and only retained boundary."""

    validate_network_types(candidate)
    if not isinstance(candidate, Mapping):  # pragma: no cover - validated above.
        raise AssertionError("validated TN semantic body is not a mapping")
    boundary = candidate.get("boundary")
    index_catalog = candidate.get("index_catalog")
    factors = candidate.get("factors")
    if (
        not isinstance(boundary, list)
        or any(not isinstance(index_id, str) for index_id in boundary)
        or len(set(boundary)) != len(boundary)
        or not isinstance(index_catalog, list)
        or not isinstance(factors, list)
    ):
        raise ValueError("retained boundary KEEP coverage has malformed inputs")

    kinds = {
        row["index_id"]: row["kind"]
        for row in index_catalog
        if isinstance(row, Mapping)
    }
    if any(kinds.get(index_id) != "RECORD" for index_id in boundary):
        raise ValueError("retained boundary KEEP coverage includes a non-Record index")

    counts = {index_id: 0 for index_id in boundary}
    for factor in factors:
        if not isinstance(factor, Mapping) or factor.get("template_id") != "KEEP":
            continue
        scope = factor.get("scope")
        if not isinstance(scope, list) or len(scope) != 1 or scope[0] not in counts:
            raise ValueError("retained boundary KEEP coverage has an extra factor")
        counts[scope[0]] += 1
    if any(count != 1 for count in counts.values()):
        raise ValueError("retained boundary KEEP coverage is not exactly one per output")


_TEMPLATE_SHAPES = {
    "INIT0": [4],
    "TRACE": [4],
    "H": [4, 4],
    "CX": [4, 4, 4, 4],
    "COHERENT_Z": [4, 4, 2],
    "R": [4, 4],
    "M": [4, 2, 4],
    "MR": [4, 2, 4],
    "HALF": [2],
    "SIGN_EQ": [2, 2, 2],
    "ONE": [2],
    "COPY": [2, 2, 2],
    "ZERO": [2],
    "XOR": [2, 2, 2],
    "KEEP": [2],
}

_TEMPLATE_SCOPE_KINDS = {
    "INIT0": ["DENSITY"],
    "TRACE": ["DENSITY"],
    "H": ["DENSITY", "DENSITY"],
    "CX": ["DENSITY", "DENSITY", "DENSITY", "DENSITY"],
    "COHERENT_Z": ["DENSITY", "DENSITY", "SIGN"],
    "R": ["DENSITY", "DENSITY"],
    "M": ["DENSITY", "RAW", "DENSITY"],
    "MR": ["DENSITY", "RAW", "DENSITY"],
    "HALF": ["SIGN"],
    "SIGN_EQ": ["SIGN", "SIGN", "SIGN"],
    "ONE": ["CLASSICAL"],
    "COPY": ["RAW", "CONSUMER", "RAW"],
    "ZERO": ["PARITY"],
    "XOR": ["PARITY", "CONSUMER", "PARITY"],
    "KEEP": ["RECORD"],
}


class _IncidenceBuilder:
    """Independent stable-ID builder for labelled factor incidence only."""

    def __init__(self) -> None:
        self.indices: list[dict[str, Any]] = []
        self.factors: list[dict[str, Any]] = []
        self._known_indices: set[str] = set()
        self._known_kinds: dict[str, str] = {}
        self._known_domains: dict[str, int] = {}

    @staticmethod
    def _provenance(
        event_id: str | None, role: str, ordinal: int | None
    ) -> dict[str, Any]:
        return {"event_id": event_id, "role": role, "ordinal": ordinal}

    def index(
        self,
        index_id: str,
        kind: str,
        *,
        event_id: str | None,
        role: str,
        ordinal: int | None,
    ) -> str:
        if index_id in self._known_indices:
            raise ValueError(f"duplicate independently reconstructed index {index_id}")
        if kind not in _INDEX_DOMAINS:
            raise ValueError(f"unknown independently reconstructed index kind {kind!r}")
        self._known_indices.add(index_id)
        self._known_kinds[index_id] = kind
        self._known_domains[index_id] = _INDEX_DOMAINS[kind]
        self.indices.append(
            {
                "index_id": index_id,
                "kind": kind,
                "domain": _INDEX_DOMAINS[kind],
                "provenance": self._provenance(event_id, role, ordinal),
            }
        )
        return index_id

    def factor(
        self,
        template_id: str,
        scope: list[str],
        *,
        event_id: str | None,
        role: str,
        ordinal: int | None,
    ) -> str:
        if template_id not in _TEMPLATE_SHAPES:
            raise ValueError(
                f"unknown independently reconstructed template {template_id}"
            )
        if any(index not in self._known_indices for index in scope):
            raise ValueError(f"{template_id} factor references an unknown index")
        shape = _TEMPLATE_SHAPES[template_id]
        expected_kinds = _TEMPLATE_SCOPE_KINDS[template_id]
        if len(scope) != len(shape) or len(scope) != len(expected_kinds):
            raise ValueError(f"{template_id} factor scope has the wrong arity")
        for slot, (index_id, expected_kind, extent) in enumerate(
            zip(scope, expected_kinds, shape, strict=True)
        ):
            actual_kind = self._known_kinds[index_id]
            if not _scope_kind_accepts(
                template_id, slot, expected_kind, actual_kind
            ):
                raise ValueError(
                    f"{template_id} factor slot {slot} expects {expected_kind}, "
                    f"got {actual_kind}"
                )
            if self._known_domains[index_id] != extent:
                raise ValueError(
                    f"{template_id} factor slot {slot} domain/shape mismatch"
                )
        factor_id = f"f{len(self.factors):06d}"
        self.factors.append(
            {
                "factor_id": factor_id,
                "template_id": template_id,
                "scope": list(scope),
                "shape": list(shape),
                "provenance": self._provenance(event_id, role, ordinal),
            }
        )
        return factor_id


def reconstruct_network_incidence(source_text: str) -> dict[str, Any]:
    """Rebuild complete TN incidence from independently parsed Stim source.

    The source parser is the only project import.  No neutral, TN, pair, ADD,
    shared-model, or micro-owner representation participates in this oracle.
    """

    from .independent_source_oracle import reconstruct_source_program

    source_program = reconstruct_source_program(source_text)
    qubits = source_program["qubits"]
    events = source_program["events"]
    if not isinstance(qubits, list) or not isinstance(events, list):
        raise ValueError("independent source reconstruction has invalid containers")

    builder = _IncidenceBuilder()
    current_wire: dict[int, str] = {}
    wire_count: dict[int, int] = {}

    for qubit in qubits:
        if not isinstance(qubit, Mapping):
            raise ValueError("independent qubit row is malformed")
        stim_id = qubit["stim_id"]
        dense_ordinal = qubit["dense_ordinal"]
        if type(stim_id) is not int or type(dense_ordinal) is not int:
            raise ValueError("independent qubit identity is malformed")
        wire_count[stim_id] = 0
        initial = builder.index(
            f"q{stim_id}:w0",
            "DENSITY",
            event_id=None,
            role="INITIAL_DENSITY",
            ordinal=dense_ordinal,
        )
        current_wire[stim_id] = initial
        builder.factor(
            "INIT0",
            [initial],
            event_id=None,
            role="INITIAL_STATE",
            ordinal=dense_ordinal,
        )

    sign_previous = builder.index(
        "sign:z:0",
        "SIGN",
        event_id=None,
        role="SIGN_PRIOR",
        ordinal=0,
    )
    builder.factor(
        "HALF",
        [sign_previous],
        event_id=None,
        role="SIGN_PRIOR",
        ordinal=0,
    )

    marker_ledger: list[dict[str, str]] = []
    sign_ledger: list[dict[str, Any]] = []
    raw_producers: dict[int, str] = {}

    def next_wire(stim_id: int, event_id: str, role: str) -> str:
        if stim_id not in wire_count:
            raise ValueError(f"event references undeclared qubit {stim_id}")
        wire_count[stim_id] += 1
        return builder.index(
            f"q{stim_id}:w{wire_count[stim_id]}",
            "DENSITY",
            event_id=event_id,
            role=role,
            ordinal=wire_count[stim_id],
        )

    for event in events:
        if not isinstance(event, Mapping):
            raise ValueError("independent event row is malformed")
        event_id = event["event_id"]
        kind = event["kind"]
        if not isinstance(event_id, str) or not isinstance(kind, str):
            raise ValueError("independent event identity is malformed")

        if kind in {"COORD_MARKER", "TICK_MARKER"}:
            marker_ledger.append({"event_id": event_id, "kind": kind})
            continue
        if kind in {"DETECTOR_APPEND", "OBSERVABLE_XOR", "FINALIZE_RECORD"}:
            continue

        if kind in {"RESET", "H", "M", "MR", "COHERENT_Z"}:
            event_qubits = event["qubits"]
            if not isinstance(event_qubits, list) or len(event_qubits) != 1:
                raise ValueError(f"{event_id}: single-qubit event is malformed")
            qubit = event_qubits[0]
            if not isinstance(qubit, Mapping) or type(qubit.get("stim_id")) is not int:
                raise ValueError(f"{event_id}: qubit reference is malformed")
            stim_id = qubit["stim_id"]
            q_in = current_wire[stim_id]
            q_out = next_wire(stim_id, event_id, f"{kind}_OUTPUT")

            if kind == "COHERENT_Z":
                occurrence = len(sign_ledger)
                mu = builder.index(
                    f"sign:mu:{occurrence}",
                    "SIGN",
                    event_id=event_id,
                    role="SIGN_OCCURRENCE",
                    ordinal=occurrence,
                )
                sign_next = builder.index(
                    f"sign:z:{occurrence + 1}",
                    "SIGN",
                    event_id=event_id,
                    role="SIGN_CHAIN_OUTPUT",
                    ordinal=occurrence + 1,
                )
                chain_factor = builder.factor(
                    "SIGN_EQ",
                    [sign_previous, mu, sign_next],
                    event_id=event_id,
                    role="SIGN_CHAIN",
                    ordinal=occurrence,
                )
                channel_factor = builder.factor(
                    "COHERENT_Z",
                    [q_in, q_out, mu],
                    event_id=event_id,
                    role="CONTROLLED_CHANNEL",
                    ordinal=occurrence,
                )
                sign_ledger.append(
                    {
                        "occurrence": occurrence,
                        "event_id": event_id,
                        "previous_sign": sign_previous,
                        "mu": mu,
                        "next_sign": sign_next,
                        "chain_factor": chain_factor,
                        "channel_factor": channel_factor,
                    }
                )
                sign_previous = sign_next
            elif kind in {"M", "MR"}:
                raw = event["raw_output"]
                if type(raw) is not int or raw in raw_producers:
                    raise ValueError(
                        f"{event_id}: raw output is malformed or duplicated"
                    )
                raw_index = builder.index(
                    f"raw:{raw}:producer",
                    "RAW",
                    event_id=event_id,
                    role="RAW_MEASUREMENT",
                    ordinal=raw,
                )
                raw_producers[raw] = raw_index
                builder.factor(
                    kind,
                    [q_in, raw_index, q_out],
                    event_id=event_id,
                    role=f"{kind}_INSTRUMENT",
                    ordinal=raw,
                )
            else:
                source_target_ordinal = event["source_target_ordinal"]
                if type(source_target_ordinal) is not int:
                    raise ValueError(f"{event_id}: source target ordinal is malformed")
                builder.factor(
                    "R" if kind == "RESET" else "H",
                    [q_in, q_out],
                    event_id=event_id,
                    role=f"{kind}_CHANNEL",
                    ordinal=source_target_ordinal,
                )
            current_wire[stim_id] = q_out
            continue

        if kind == "CX":
            event_qubits = event["qubits"]
            if not isinstance(event_qubits, list) or len(event_qubits) != 2:
                raise ValueError(f"{event_id}: CX qubits are malformed")
            control, target = event_qubits
            if not isinstance(control, Mapping) or not isinstance(target, Mapping):
                raise ValueError(f"{event_id}: CX qubit references are malformed")
            control_id, target_id = control.get("stim_id"), target.get("stim_id")
            if type(control_id) is not int or type(target_id) is not int:
                raise ValueError(f"{event_id}: CX qubit identities are malformed")
            c_in, t_in = current_wire[control_id], current_wire[target_id]
            c_out = next_wire(control_id, event_id, "CX_CONTROL_OUTPUT")
            t_out = next_wire(target_id, event_id, "CX_TARGET_OUTPUT")
            source_target_ordinal = event["source_target_ordinal"]
            if type(source_target_ordinal) is not int:
                raise ValueError(f"{event_id}: source target ordinal is malformed")
            builder.factor(
                "CX",
                [c_in, t_in, c_out, t_out],
                event_id=event_id,
                role="CX_CHANNEL",
                ordinal=source_target_ordinal,
            )
            current_wire[control_id] = c_out
            current_wire[target_id] = t_out
            continue

        raise ValueError(f"{event_id}: unsupported independently parsed event {kind}")

    builder.factor(
        "ONE",
        [sign_previous],
        event_id=None,
        role="SIGN_TERMINAL",
        ordinal=len(sign_ledger),
    )
    for qubit in qubits:
        assert isinstance(qubit, Mapping)
        stim_id = qubit["stim_id"]
        dense_ordinal = qubit["dense_ordinal"]
        assert type(stim_id) is int and type(dense_ordinal) is int
        builder.factor(
            "TRACE",
            [current_wire[stim_id]],
            event_id=None,
            role="FINAL_TRACE",
            ordinal=dense_ordinal,
        )

    detector_events = [event for event in events if event["kind"] == "DETECTOR_APPEND"]
    observable_events = [event for event in events if event["kind"] == "OBSERVABLE_XOR"]
    if not events or events[-1]["kind"] != "FINALIZE_RECORD":
        raise ValueError("independent source program lacks Record finalization")
    final_event = events[-1]

    record_inputs: list[
        tuple[
            int,
            str,
            list[tuple[Mapping[str, Any], Mapping[str, Any], int]],
        ]
    ] = []
    for event in detector_events:
        output = event["record_output"]
        if not isinstance(output, Mapping) or type(output.get("ordinal")) is not int:
            raise ValueError(f"{event['event_id']}: detector output is malformed")
        operands = event["rec_operands"]
        if not isinstance(operands, list):
            raise ValueError(f"{event['event_id']}: operands are malformed")
        record_inputs.append(
            (
                output["ordinal"],
                event["event_id"],
                [(event, operand, operand["operand_ordinal"]) for operand in operands],
            )
        )

    observable_operands: list[
        tuple[Mapping[str, Any], Mapping[str, Any], int]
    ] = []
    for event in observable_events:
        operands = event["rec_operands"]
        if not isinstance(operands, list):
            raise ValueError(f"{event['event_id']}: operands are malformed")
        for operand in operands:
            observable_operands.append((event, operand, len(observable_operands)))
    record_inputs.append(
        (
            len(detector_events),
            final_event["event_id"],
            observable_operands,
        )
    )

    consumer_specs: dict[int, list[dict[str, Any]]] = {
        raw: [] for raw in raw_producers
    }
    for record_ordinal, _producer_event_id, operands in record_inputs:
        for event, operand, output_operand_ordinal in operands:
            raw = operand["absolute_raw_ordinal"]
            if type(raw) is not int or raw not in consumer_specs:
                raise ValueError("Record operand references an unknown raw output")
            consumer_specs[raw].append(
                {
                    "record_ordinal": record_ordinal,
                    "operand_ordinal": output_operand_ordinal,
                    "event_id": event["event_id"],
                    "event_operand_ordinal": operand["operand_ordinal"],
                }
            )

    consumer_indices: dict[tuple[str, int], str] = {}
    raw_ledger: list[dict[str, Any]] = []
    for raw in sorted(raw_producers):
        specs = sorted(
            consumer_specs[raw],
            key=lambda spec: (spec["record_ordinal"], spec["operand_ordinal"]),
        )
        previous = raw_producers[raw]
        consumers: list[dict[str, Any]] = []
        for consumer_ordinal, spec in enumerate(specs):
            consumer = builder.index(
                f"raw:{raw}:consumer:{consumer_ordinal}",
                "CONSUMER",
                event_id=spec["event_id"],
                role="RAW_CONSUMER",
                ordinal=consumer_ordinal,
            )
            following = builder.index(
                f"raw:{raw}:copy:{consumer_ordinal + 1}",
                "RAW",
                event_id=spec["event_id"],
                role="RAW_COPY_CHAIN",
                ordinal=consumer_ordinal + 1,
            )
            builder.factor(
                "COPY",
                [previous, consumer, following],
                event_id=spec["event_id"],
                role="RAW_COPY",
                ordinal=consumer_ordinal,
            )
            key = (spec["event_id"], spec["event_operand_ordinal"])
            if key in consumer_indices:
                raise ValueError("duplicate Record consumer identity")
            consumer_indices[key] = consumer
            consumers.append(
                {
                    "record_ordinal": spec["record_ordinal"],
                    "operand_ordinal": spec["operand_ordinal"],
                    "consumer_index": consumer,
                }
            )
            previous = following
        builder.factor(
            "ONE",
            [previous],
            event_id=None,
            role="RAW_TERMINAL",
            ordinal=raw,
        )
        raw_ledger.append(
            {
                "raw_ordinal": raw,
                "producer_index": raw_producers[raw],
                "consumers": consumers,
                "terminal_index": previous,
            }
        )

    boundary: list[str] = []
    for record_ordinal, producer_event_id, operands in record_inputs:
        if operands:
            accumulator = builder.index(
                f"record:{record_ordinal}:acc:0",
                "PARITY",
                event_id=producer_event_id,
                role="PARITY_ZERO",
                ordinal=0,
            )
            builder.factor(
                "ZERO",
                [accumulator],
                event_id=producer_event_id,
                role="PARITY_ZERO",
                ordinal=0,
            )
            for operand_index, (event, operand, _output_ordinal) in enumerate(operands):
                is_last = operand_index == len(operands) - 1
                output_index = builder.index(
                    (
                        f"record:{record_ordinal}"
                        if is_last
                        else f"record:{record_ordinal}:acc:{operand_index + 1}"
                    ),
                    "RECORD" if is_last else "PARITY",
                    event_id=producer_event_id,
                    role="RECORD_OUTPUT" if is_last else "PARITY_ACCUMULATOR",
                    ordinal=operand_index + 1,
                )
                consumer_key = (event["event_id"], operand["operand_ordinal"])
                if consumer_key not in consumer_indices:
                    raise ValueError("Record parity references a missing consumer")
                builder.factor(
                    "XOR",
                    [accumulator, consumer_indices[consumer_key], output_index],
                    event_id=producer_event_id,
                    role="PARITY_XOR",
                    ordinal=operand_index,
                )
                accumulator = output_index
            record_index = accumulator
        else:
            record_index = builder.index(
                f"record:{record_ordinal}",
                "RECORD",
                event_id=producer_event_id,
                role="RECORD_OUTPUT",
                ordinal=0,
            )
            builder.factor(
                "ZERO",
                [record_index],
                event_id=producer_event_id,
                role="PARITY_ZERO",
                ordinal=0,
            )
        builder.factor(
            "KEEP",
            [record_index],
            event_id=producer_event_id,
            role="RECORD_KEEP",
            ordinal=record_ordinal,
        )
        boundary.append(record_index)

    return {
        "index_catalog": builder.indices,
        "factors": builder.factors,
        "boundary": boundary,
        "marker_ledger": marker_ledger,
        "raw_consumer_ledger": raw_ledger,
        "sign_occurrence_ledger": sign_ledger,
    }


_DIRECT_TINY_WITNESSES: dict[str, dict[str, Any]] = {
    "T1": {
        "qubits": 1,
        "operations": (("R", 0), ("H", 0), ("M", 0)),
        "record_operands": ((0,), (0,)),
    },
    "T2": {
        "qubits": 1,
        "operations": (("R", 0), ("H", 0), ("MR", 0), ("M", 0)),
        "record_operands": ((0, 1), (1,)),
    },
    "T3": {
        "qubits": 1,
        "operations": (
            ("R", 0),
            ("H", 0),
            ("COHERENT_Z", 0),
            ("H", 0),
            ("COHERENT_Z", 0),
            ("H", 0),
            ("M", 0),
        ),
        "record_operands": ((0,), (0,)),
    },
    "T4": {
        "qubits": 2,
        "operations": (
            ("R", 0),
            ("R", 1),
            ("H", 0),
            ("CX", 0, 1),
            ("M", 0),
            ("M", 1),
        ),
        "record_operands": ((0, 1), (1,)),
    },
}

_Matrix = tuple[tuple[_Exact, ...], ...]


def _zero_matrix(dimension: int) -> _Matrix:
    return tuple(
        tuple(_ZERO for _column in range(dimension))
        for _row in range(dimension)
    )


def _matrix_add(left: _Matrix, right: _Matrix) -> _Matrix:
    if len(left) != len(right):
        raise ValueError("exact matrices have different dimensions")
    return tuple(
        tuple(a + b for a, b in zip(left_row, right_row, strict=True))
        for left_row, right_row in zip(left, right, strict=True)
    )


def _matrix_scale(scalar: _Exact, matrix: _Matrix) -> _Matrix:
    return tuple(tuple(scalar * value for value in row) for row in matrix)


def _matrix_multiply(left: _Matrix, right: _Matrix) -> _Matrix:
    dimension = len(left)
    if dimension == 0 or len(right) != dimension:
        raise ValueError("exact matrix multiplication has invalid dimensions")
    if any(len(row) != dimension for row in left + right):
        raise ValueError("exact matrix multiplication requires square matrices")
    return tuple(
        tuple(
            sum(
                (left[row][inner] * right[inner][column] for inner in range(dimension)),
                start=_ZERO,
            )
            for column in range(dimension)
        )
        for row in range(dimension)
    )


def _matrix_dagger(matrix: _Matrix) -> _Matrix:
    dimension = len(matrix)
    return tuple(
        tuple(matrix[column][row].conjugate() for column in range(dimension))
        for row in range(dimension)
    )


def _sandwich(operator: _Matrix, density: _Matrix) -> _Matrix:
    return _matrix_multiply(
        _matrix_multiply(operator, density),
        _matrix_dagger(operator),
    )


def _matrix_trace(matrix: _Matrix) -> _Exact:
    return sum((matrix[index][index] for index in range(len(matrix))), start=_ZERO)


def _matrix_is_zero(matrix: _Matrix) -> bool:
    return all(value == _ZERO for row in matrix for value in row)


def _basis_bit(basis_index: int, qubit: int, qubit_count: int) -> int:
    return (basis_index >> (qubit_count - qubit - 1)) & 1


def _embed_one_qubit(
    local: tuple[tuple[_Exact, _Exact], tuple[_Exact, _Exact]],
    qubit: int,
    qubit_count: int,
) -> _Matrix:
    dimension = 1 << qubit_count
    result = [[_ZERO for _column in range(dimension)] for _row in range(dimension)]
    for output_basis, input_basis in product(range(dimension), repeat=2):
        unchanged = all(
            _basis_bit(output_basis, other, qubit_count)
            == _basis_bit(input_basis, other, qubit_count)
            for other in range(qubit_count)
            if other != qubit
        )
        if unchanged:
            result[output_basis][input_basis] = local[
                _basis_bit(output_basis, qubit, qubit_count)
            ][_basis_bit(input_basis, qubit, qubit_count)]
    return tuple(tuple(row) for row in result)


def _cx_matrix(control: int, target: int, qubit_count: int) -> _Matrix:
    dimension = 1 << qubit_count
    result = [[_ZERO for _column in range(dimension)] for _row in range(dimension)]
    target_mask = 1 << (qubit_count - target - 1)
    for input_basis in range(dimension):
        output_basis = input_basis
        if _basis_bit(input_basis, control, qubit_count):
            output_basis ^= target_mask
        result[output_basis][input_basis] = _ONE
    return tuple(tuple(row) for row in result)


def _add_density(
    target: dict[tuple[int | None, tuple[int, ...]], _Matrix],
    key: tuple[int | None, tuple[int, ...]],
    value: _Matrix,
) -> None:
    if _matrix_is_zero(value):
        return
    combined = _matrix_add(target.get(key, _zero_matrix(len(value))), value)
    if _matrix_is_zero(combined):
        target.pop(key, None)
    else:
        target[key] = combined


def reconstruct_tiny_retained_tensor(
    witness_id: str, *, sign_process: str = "persistent"
) -> list[dict[str, Any]]:
    """Directly branch exact density matrices for frozen witnesses T1--T4.

    ``iid`` exists solely as the preregistered sign-resampling negative
    control.  This routine constructs literal operators and Kraus branches;
    it does not read the owner table catalog or contract an owner TN.
    """

    if witness_id not in _DIRECT_TINY_WITNESSES:
        raise ValueError("tiny density witness must be one of T1, T2, T3, T4")
    if sign_process not in {"persistent", "iid"}:
        raise ValueError("sign_process must be 'persistent' or 'iid'")

    witness = _DIRECT_TINY_WITNESSES[witness_id]
    qubit_count = witness["qubits"]
    dimension = 1 << qubit_count
    initial_rows = [
        [_ZERO for _column in range(dimension)] for _row in range(dimension)
    ]
    initial_rows[0][0] = _ONE
    initial = tuple(tuple(row) for row in initial_rows)

    # A persistent sign is sampled once; IID signs are sampled at each U only.
    states: dict[tuple[int | None, tuple[int, ...]], _Matrix] = {}
    if sign_process == "persistent":
        states[(-1, ())] = _matrix_scale(_HALF, initial)
        states[(1, ())] = _matrix_scale(_HALF, initial)
    else:
        states[(None, ())] = initial

    h_local = (
        (_INV_SQRT2, _INV_SQRT2),
        (_INV_SQRT2, -_INV_SQRT2),
    )
    reset_kraus = (
        ((_ONE, _ZERO), (_ZERO, _ZERO)),
        ((_ZERO, _ONE), (_ZERO, _ZERO)),
    )
    projectors = (
        ((_ONE, _ZERO), (_ZERO, _ZERO)),
        ((_ZERO, _ZERO), (_ZERO, _ONE)),
    )
    measure_reset_kraus = reset_kraus

    for operation in witness["operations"]:
        name = operation[0]
        following: dict[tuple[int | None, tuple[int, ...]], _Matrix] = {}
        for (persistent_sign, raw), density in states.items():
            if name == "R":
                qubit = operation[1]
                reset_density = _zero_matrix(dimension)
                for local_kraus in reset_kraus:
                    kraus = _embed_one_qubit(local_kraus, qubit, qubit_count)
                    reset_density = _matrix_add(
                        reset_density,
                        _sandwich(kraus, density),
                    )
                _add_density(following, (persistent_sign, raw), reset_density)
                continue

            if name == "H":
                qubit = operation[1]
                h = _embed_one_qubit(h_local, qubit, qubit_count)
                _add_density(
                    following,
                    (persistent_sign, raw),
                    _sandwich(h, density),
                )
                continue

            if name == "CX":
                cx = _cx_matrix(operation[1], operation[2], qubit_count)
                _add_density(
                    following,
                    (persistent_sign, raw),
                    _sandwich(cx, density),
                )
                continue

            if name == "COHERENT_Z":
                qubit = operation[1]
                signs = (
                    (persistent_sign, _ONE)
                    if type(persistent_sign) is int
                    else None
                )
                sign_branches = (
                    (signs,)
                    if signs is not None
                    else ((-1, _HALF), (1, _HALF))
                )
                for occurrence_sign, prior in sign_branches:
                    signed_is = _IS if occurrence_sign == 1 else -_IS
                    u_local = (
                        (_C - signed_is, _ZERO),
                        (_ZERO, _C + signed_is),
                    )
                    unitary = _embed_one_qubit(u_local, qubit, qubit_count)
                    _add_density(
                        following,
                        (persistent_sign, raw),
                        _matrix_scale(prior, _sandwich(unitary, density)),
                    )
                continue

            if name in {"M", "MR"}:
                qubit = operation[1]
                local_operators = (
                    projectors if name == "M" else measure_reset_kraus
                )
                for outcome, local_kraus in enumerate(local_operators):
                    kraus = _embed_one_qubit(local_kraus, qubit, qubit_count)
                    _add_density(
                        following,
                        (persistent_sign, raw + (outcome,)),
                        _sandwich(kraus, density),
                    )
                continue

            raise AssertionError(f"unknown direct tiny operation {name}")
        states = following

    retained: dict[tuple[int, int], _Exact] = {}
    record_operands = witness["record_operands"]
    for (_persistent_sign, raw), density in states.items():
        record = tuple(
            sum((raw[raw_ordinal] for raw_ordinal in operands), start=0) % 2
            for operands in record_operands
        )
        if len(record) != 2:
            raise AssertionError("tiny witness must retain exactly two Record bits")
        retained[record] = retained.get(record, _ZERO) + _matrix_trace(density)

    return [
        {
            "record": list(record),
            "value": retained.get(record, _ZERO).to_data(),
        }
        for record in product(range(2), repeat=2)
    ]
