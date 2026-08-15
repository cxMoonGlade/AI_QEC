"""Exact retained-boundary factor-network lowering.

The builder owns explicit dense local tables and labelled incidence only.  It
does not choose an elimination order, contract a tensor, materialize a joint
Record, or emit any width/metric.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from fractions import Fraction
from itertools import product
from typing import Any

from scripts.external_baselines.no_cutoff_minimal_exact_owners.model import (
    ONE,
    ZERO,
    Qsqrt2i,
)

from .model import (
    TN_SCHEMA,
    StaticArtifact,
    canonical_json_bytes,
    validate_static_envelope,
)
from .neutral import validate_declared_error_record_program


_HALF = Qsqrt2i.rational(1, 2)
_C = Qsqrt2i.rational(9999, 10001)
_S = Qsqrt2i.rational(200, 10001)
_I = Qsqrt2i.imag()
_INV_SQRT2 = Qsqrt2i.sqrt2(Fraction(1, 2))

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
    # The frozen catalog's CLASSICAL slot is the all-ones terminal shared by
    # SIGN and RAW chains.  RECORD is the retained/open subtype of a PARITY
    # value, used by the final XOR output and by an operand-free ZERO factor.
    if expected == "CLASSICAL":
        return actual in {"SIGN", "RAW"}
    if expected == "PARITY" and actual == "RECORD":
        return (template_id, slot) in {("XOR", 2), ("ZERO", 0)}
    return actual == expected


def _conjugate(value: Qsqrt2i) -> Qsqrt2i:
    return Qsqrt2i(value.a, value.b, -value.c, -value.d)


def _bit(value: bool) -> Qsqrt2i:
    return ONE if value else ZERO


def _density_bits(code: int) -> tuple[int, int]:
    if code not in range(4):
        raise ValueError("density code must be in range(4)")
    return divmod(code, 2)


def _one_qubit_super_table(unitary: list[list[Qsqrt2i]]) -> list[Qsqrt2i]:
    table: list[Qsqrt2i] = []
    for q_in, q_out in product(range(4), repeat=2):
        in_ket, in_bra = _density_bits(q_in)
        out_ket, out_bra = _density_bits(q_out)
        table.append(
            unitary[out_ket][in_ket]
            * _conjugate(unitary[out_bra][in_bra])
        )
    return table


def _two_qubit_super_table(unitary: list[list[Qsqrt2i]]) -> list[Qsqrt2i]:
    table: list[Qsqrt2i] = []
    for control_in, target_in, control_out, target_out in product(
        range(4), repeat=4
    ):
        ci_ket, ci_bra = _density_bits(control_in)
        ti_ket, ti_bra = _density_bits(target_in)
        co_ket, co_bra = _density_bits(control_out)
        to_ket, to_bra = _density_bits(target_out)
        input_ket = 2 * ci_ket + ti_ket
        input_bra = 2 * ci_bra + ti_bra
        output_ket = 2 * co_ket + to_ket
        output_bra = 2 * co_bra + to_bra
        table.append(
            unitary[output_ket][input_ket]
            * _conjugate(unitary[output_bra][input_bra])
        )
    return table


def _template_catalog() -> list[dict[str, Any]]:
    h = [[_INV_SQRT2, _INV_SQRT2], [_INV_SQRT2, -_INV_SQRT2]]
    cx = [[ZERO for _ in range(4)] for _ in range(4)]
    for source, target in enumerate((0, 1, 3, 2)):
        cx[target][source] = ONE

    coherent: list[Qsqrt2i] = []
    for q_in, q_out, mu_bit in product(range(4), range(4), range(2)):
        latent = -1 if mu_bit == 0 else 1
        unitary = [
            [_C + (-(_I * Qsqrt2i.rational(latent) * _S)), ZERO],
            [ZERO, _C + (_I * Qsqrt2i.rational(latent) * _S)],
        ]
        coherent.append(_one_qubit_super_table(unitary)[4 * q_in + q_out])

    reset: list[Qsqrt2i] = []
    for q_in, q_out in product(range(4), repeat=2):
        in_ket, in_bra = _density_bits(q_in)
        reset.append(_bit(in_ket == in_bra and q_out == 0))

    measure: list[Qsqrt2i] = []
    measure_reset: list[Qsqrt2i] = []
    for q_in, outcome, q_out in product(range(4), range(2), range(4)):
        measured_code = 3 * outcome
        measure.append(_bit(q_in == measured_code and q_out == measured_code))
        measure_reset.append(_bit(q_in == measured_code and q_out == 0))

    sign_eq = [
        _bit(previous == mu == following)
        for previous, mu, following in product(range(2), repeat=3)
    ]
    copy = [
        _bit(source == consumer == terminal)
        for source, consumer, terminal in product(range(2), repeat=3)
    ]
    xor = [
        _bit(output == (accumulator ^ raw))
        for accumulator, raw, output in product(range(2), repeat=3)
    ]

    raw_templates = [
        ("INIT0", ["DENSITY"], [4], [ONE, ZERO, ZERO, ZERO]),
        ("TRACE", ["DENSITY"], [4], [ONE, ZERO, ZERO, ONE]),
        ("H", ["DENSITY", "DENSITY"], [4, 4], _one_qubit_super_table(h)),
        (
            "CX",
            ["DENSITY", "DENSITY", "DENSITY", "DENSITY"],
            [4, 4, 4, 4],
            _two_qubit_super_table(cx),
        ),
        (
            "COHERENT_Z",
            ["DENSITY", "DENSITY", "SIGN"],
            [4, 4, 2],
            coherent,
        ),
        ("R", ["DENSITY", "DENSITY"], [4, 4], reset),
        ("M", ["DENSITY", "RAW", "DENSITY"], [4, 2, 4], measure),
        ("MR", ["DENSITY", "RAW", "DENSITY"], [4, 2, 4], measure_reset),
        ("HALF", ["SIGN"], [2], [_HALF, _HALF]),
        ("SIGN_EQ", ["SIGN", "SIGN", "SIGN"], [2, 2, 2], sign_eq),
        ("ONE", ["CLASSICAL"], [2], [ONE, ONE]),
        ("COPY", ["RAW", "CONSUMER", "RAW"], [2, 2, 2], copy),
        ("ZERO", ["PARITY"], [2], [ONE, ZERO]),
        ("XOR", ["PARITY", "CONSUMER", "PARITY"], [2, 2, 2], xor),
        ("KEEP", ["RECORD"], [2], [ONE, ONE]),
    ]
    return [
        {
            "template_id": name,
            "scope_kinds": kinds,
            "shape": shape,
            "table": [value.to_data() for value in table],
        }
        for name, kinds, shape, table in raw_templates
    ]


class _NetworkBuilder:
    def __init__(self, templates: list[dict[str, Any]]) -> None:
        self.indices: list[dict[str, Any]] = []
        self.factors: list[dict[str, Any]] = []
        self._index_ids: set[str] = set()
        self._index_kinds: dict[str, str] = {}
        self._index_domains: dict[str, int] = {}
        self._templates = {template["template_id"]: template for template in templates}

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
        if index_id in self._index_ids:
            raise ValueError(f"duplicate TN index {index_id}")
        if kind not in _INDEX_DOMAINS:
            raise ValueError(f"unknown TN index kind {kind!r}")
        domain = _INDEX_DOMAINS[kind]
        self._index_ids.add(index_id)
        self._index_kinds[index_id] = kind
        self._index_domains[index_id] = domain
        self.indices.append(
            {
                "index_id": index_id,
                "kind": kind,
                "domain": domain,
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
        if template_id not in self._templates:
            raise ValueError(f"unknown TN template {template_id}")
        template = self._templates[template_id]
        if len(scope) != len(template["shape"]):
            raise ValueError(f"factor {template_id} scope/shape mismatch")
        if any(index not in self._index_ids for index in scope):
            raise ValueError(f"factor {template_id} uses an unknown index")
        for slot, (index_id, expected_kind, extent) in enumerate(
            zip(
                scope,
                template["scope_kinds"],
                template["shape"],
                strict=True,
            )
        ):
            actual_kind = self._index_kinds[index_id]
            if not _scope_kind_accepts(
                template_id, slot, expected_kind, actual_kind
            ):
                raise ValueError(
                    f"factor {template_id} slot {slot} expects {expected_kind}, "
                    f"got {actual_kind}"
                )
            if self._index_domains[index_id] != extent:
                raise ValueError(
                    f"factor {template_id} slot {slot} domain/shape mismatch"
                )
        factor_id = f"f{len(self.factors):06d}"
        self.factors.append(
            {
                "factor_id": factor_id,
                "template_id": template_id,
                "scope": list(scope),
                "shape": list(template["shape"]),
                "provenance": self._provenance(event_id, role, ordinal),
            }
        )
        return factor_id


def _validate_factor_network_types(semantic: object) -> None:
    """Validate factor signatures against index kinds without rebuilding."""

    if not isinstance(semantic, Mapping):
        raise ValueError("TN semantic body must be a mapping")
    index_catalog = semantic.get("index_catalog")
    table_catalog = semantic.get("table_catalog")
    factors = semantic.get("factors")
    if not isinstance(index_catalog, list):
        raise ValueError("TN index catalog must be a list")
    if not isinstance(table_catalog, list):
        raise ValueError("TN table catalog must be a list")
    if not isinstance(factors, list):
        raise ValueError("TN factor catalog must be a list")

    kinds_by_id: dict[str, str] = {}
    domains_by_id: dict[str, int] = {}
    for row in index_catalog:
        if not isinstance(row, Mapping):
            raise ValueError("TN index row must be a mapping")
        index_id, kind, domain = row.get("index_id"), row.get("kind"), row.get("domain")
        if not isinstance(index_id, str) or not index_id:
            raise ValueError("TN index identity must be a nonempty string")
        if index_id in kinds_by_id:
            raise ValueError(f"duplicate TN index {index_id}")
        if not isinstance(kind, str) or kind not in _INDEX_DOMAINS:
            raise ValueError(f"{index_id}: unknown TN index kind {kind!r}")
        if type(domain) is not int or domain != _INDEX_DOMAINS[kind]:
            raise ValueError(f"{index_id}: TN index domain does not match {kind}")
        kinds_by_id[index_id] = kind
        domains_by_id[index_id] = domain

    templates_by_id: dict[str, Mapping[str, Any]] = {}
    for row in table_catalog:
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


def build_retained_boundary_factor_network(neutral: StaticArtifact) -> StaticArtifact:
    """Build exact labelled target incidence and tables without contraction."""

    neutral = validate_declared_error_record_program(neutral.to_data())
    neutral_data = neutral.to_data()
    semantic = neutral_data["semantic"]
    events = semantic["events"]
    qubits = semantic["qubits"]
    table_catalog = _template_catalog()
    builder = _NetworkBuilder(table_catalog)

    current_wire: dict[int, str] = {}
    wire_counter: dict[int, int] = {}
    for qubit in qubits:
        stim_id = qubit["stim_id"]
        wire_counter[stim_id] = 0
        wire = builder.index(
            f"q{stim_id}:w0",
            "DENSITY",
            event_id=None,
            role="INITIAL_DENSITY",
            ordinal=qubit["dense_ordinal"],
        )
        current_wire[stim_id] = wire
        builder.factor(
            "INIT0",
            [wire],
            event_id=None,
            role="INITIAL_STATE",
            ordinal=qubit["dense_ordinal"],
        )

    sign_previous = builder.index(
        "sign:z:0", "SIGN", event_id=None, role="SIGN_PRIOR", ordinal=0
    )
    builder.factor(
        "HALF", [sign_previous], event_id=None, role="SIGN_PRIOR", ordinal=0
    )
    sign_occurrences: list[dict[str, Any]] = []
    marker_ledger: list[dict[str, str]] = []
    raw_producers: dict[int, str] = {}

    def next_wire(stim_id: int, event: dict[str, Any], role: str) -> str:
        wire_counter[stim_id] += 1
        return builder.index(
            f"q{stim_id}:w{wire_counter[stim_id]}",
            "DENSITY",
            event_id=event["event_id"],
            role=role,
            ordinal=wire_counter[stim_id],
        )

    for event in events:
        kind = event["kind"]
        event_id = event["event_id"]
        if kind in {"COORD_MARKER", "TICK_MARKER"}:
            marker_ledger.append({"event_id": event_id, "kind": kind})
            continue
        if kind in {"DETECTOR_APPEND", "OBSERVABLE_XOR", "FINALIZE_RECORD"}:
            continue
        if kind in {"RESET", "H", "M", "MR", "COHERENT_Z"}:
            qubit = event["qubits"][0]
            stim_id = qubit["stim_id"]
            q_in = current_wire[stim_id]
            q_out = next_wire(stim_id, event, f"{kind}_OUTPUT")
            if kind == "COHERENT_Z":
                occurrence = len(sign_occurrences)
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
                sign_occurrences.append(
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
                    raise ValueError("measurement raw ordinal is invalid or duplicated")
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
                template = "R" if kind == "RESET" else "H"
                builder.factor(
                    template,
                    [q_in, q_out],
                    event_id=event_id,
                    role=f"{kind}_CHANNEL",
                    ordinal=event["source_target_ordinal"],
                )
            current_wire[stim_id] = q_out
            continue
        if kind == "CX":
            control, target = event["qubits"]
            c_id, t_id = control["stim_id"], target["stim_id"]
            c_in, t_in = current_wire[c_id], current_wire[t_id]
            c_out = next_wire(c_id, event, "CX_CONTROL_OUTPUT")
            t_out = next_wire(t_id, event, "CX_TARGET_OUTPUT")
            builder.factor(
                "CX",
                [c_in, t_in, c_out, t_out],
                event_id=event_id,
                role="CX_CHANNEL",
                ordinal=event["source_target_ordinal"],
            )
            current_wire[c_id], current_wire[t_id] = c_out, t_out
            continue
        raise ValueError(f"unsupported canonical TN event {kind}")

    builder.factor(
        "ONE",
        [sign_previous],
        event_id=None,
        role="SIGN_TERMINAL",
        ordinal=len(sign_occurrences),
    )
    for qubit in qubits:
        stim_id = qubit["stim_id"]
        builder.factor(
            "TRACE",
            [current_wire[stim_id]],
            event_id=None,
            role="FINAL_TRACE",
            ordinal=qubit["dense_ordinal"],
        )

    detector_events = [event for event in events if event["kind"] == "DETECTOR_APPEND"]
    observable_events = [event for event in events if event["kind"] == "OBSERVABLE_XOR"]
    final_event = events[-1]
    if final_event["kind"] != "FINALIZE_RECORD":
        raise ValueError("neutral target program lacks finalization")
    record_inputs: list[tuple[int, str, list[tuple[dict[str, Any], dict[str, int], int]]]] = []
    for event in detector_events:
        ordinal = event["record_output"]["ordinal"]
        operands = [
            (event, operand, operand["operand_ordinal"])
            for operand in event["rec_operands"]
        ]
        record_inputs.append((ordinal, event["event_id"], operands))
    observable_ordinal = len(detector_events)
    observable_operands: list[tuple[dict[str, Any], dict[str, int], int]] = []
    for event in observable_events:
        for operand in event["rec_operands"]:
            observable_operands.append(
                (event, operand, len(observable_operands))
            )
    record_inputs.append(
        (observable_ordinal, final_event["event_id"], observable_operands)
    )

    specs_by_raw: dict[int, list[dict[str, Any]]] = {
        raw: [] for raw in raw_producers
    }
    for record_ordinal, _, operands in record_inputs:
        for event, operand, output_operand_ordinal in operands:
            raw = operand["absolute_raw_ordinal"]
            if raw not in specs_by_raw:
                raise ValueError("Record operand references an unknown raw bit")
            specs_by_raw[raw].append(
                {
                    "record_ordinal": record_ordinal,
                    "operand_ordinal": output_operand_ordinal,
                    "event_id": event["event_id"],
                    "event_operand_ordinal": operand["operand_ordinal"],
                }
            )

    consumer_index: dict[tuple[str, int], str] = {}
    raw_ledger: list[dict[str, Any]] = []
    for raw in sorted(raw_producers):
        specs = sorted(
            specs_by_raw[raw],
            key=lambda item: (item["record_ordinal"], item["operand_ordinal"]),
        )
        previous = raw_producers[raw]
        consumer_rows: list[dict[str, Any]] = []
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
            consumer_index[(spec["event_id"], spec["event_operand_ordinal"])] = consumer
            consumer_rows.append(
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
                "consumers": consumer_rows,
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
            for operand_index, (event, operand, _) in enumerate(operands):
                is_last = operand_index + 1 == len(operands)
                output = builder.index(
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
                consumer = consumer_index[(event["event_id"], operand["operand_ordinal"])]
                builder.factor(
                    "XOR",
                    [accumulator, consumer, output],
                    event_id=producer_event_id,
                    role="PARITY_XOR",
                    ordinal=operand_index,
                )
                accumulator = output
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

    return StaticArtifact(
        TN_SCHEMA,
        {
            "neutral_sha256": neutral.sha256,
            "index_catalog": builder.indices,
            "table_catalog": table_catalog,
            "factors": builder.factors,
            "boundary": boundary,
            "marker_ledger": marker_ledger,
            "raw_consumer_ledger": raw_ledger,
            "sign_occurrence_ledger": sign_occurrences,
        },
    )


def validate_retained_boundary_factor_network(
    data: object, *, neutral: StaticArtifact
) -> StaticArtifact:
    """Strictly reload a factor network against its frozen neutral owner."""

    validate_static_envelope(
        data,
        schema=TN_SCHEMA,
        semantic_keys={
            "neutral_sha256",
            "index_catalog",
            "table_catalog",
            "factors",
            "boundary",
            "marker_ledger",
            "raw_consumer_ledger",
            "sign_occurrence_ledger",
        },
    )
    if not isinstance(data, Mapping):
        raise ValueError("TN artifact must be a mapping")
    _validate_factor_network_types(data["semantic"])
    expected = build_retained_boundary_factor_network(neutral)
    if canonical_json_bytes(data) != canonical_json_bytes(expected.to_data()):
        raise ValueError("TN artifact does not reproduce frozen semantic identity")
    return expected


_TINY_WITNESSES: dict[str, dict[str, Any]] = {
    "T1": {
        "qubits": 1,
        "operations": [("R", 0), ("H", 0), ("M", 0)],
        "record_operands": [[0], [0]],
    },
    "T2": {
        "qubits": 1,
        "operations": [("R", 0), ("H", 0), ("MR", 0), ("M", 0)],
        "record_operands": [[0, 1], [1]],
    },
    "T3": {
        "qubits": 1,
        "operations": [
            ("R", 0),
            ("H", 0),
            ("COHERENT_Z", 0),
            ("H", 0),
            ("COHERENT_Z", 0),
            ("H", 0),
            ("M", 0),
        ],
        "record_operands": [[0], [0]],
    },
    "T4": {
        "qubits": 2,
        "operations": [
            ("R", 0),
            ("R", 1),
            ("H", 0),
            ("CX", 0, 1),
            ("M", 0),
            ("M", 1),
        ],
        "record_operands": [[0, 1], [1]],
    },
}


def _exact_from_data(value: object) -> Qsqrt2i:
    if not isinstance(value, list) or len(value) != 4:
        raise ValueError("exact TN table entry must have four coordinates")
    coordinates: list[Fraction] = []
    for pair in value:
        if (
            not isinstance(pair, list)
            or len(pair) != 2
            or type(pair[0]) is not int
            or type(pair[1]) is not int
            or pair[1] <= 0
        ):
            raise ValueError("exact TN rational encoding is invalid")
        item = Fraction(pair[0], pair[1])
        if [item.numerator, item.denominator] != pair:
            raise ValueError("exact TN rational is not reduced")
        coordinates.append(item)
    return Qsqrt2i(*coordinates)


def _tiny_tables(
    table_catalog: object | None = None,
) -> dict[str, list[Qsqrt2i]]:
    clean = _template_catalog()
    candidate = clean if table_catalog is None else table_catalog
    if not isinstance(candidate, list) or len(candidate) != len(clean):
        raise ValueError("tiny table override must contain the complete catalog")

    decoded: dict[str, list[Qsqrt2i]] = {}
    for ordinal, (actual, expected) in enumerate(zip(candidate, clean, strict=True)):
        if not isinstance(actual, Mapping):
            raise ValueError(f"tiny table override row {ordinal} must be a mapping")
        if set(actual) != {"template_id", "scope_kinds", "shape", "table"}:
            raise ValueError(f"tiny table override row {ordinal} has invalid fields")
        template_id = expected["template_id"]
        for field in ("template_id", "scope_kinds", "shape"):
            if actual[field] != expected[field]:
                raise ValueError(
                    f"tiny table override {template_id} changes {field}"
                )
        table = actual["table"]
        if not isinstance(table, list) or len(table) != len(expected["table"]):
            raise ValueError(
                f"tiny table override {template_id} table/shape mismatch"
            )
        decoded[template_id] = [_exact_from_data(value) for value in table]
    return decoded


TINY_TABLE_CORRUPTION_IDS = frozenset(
    {"tn_measurement_dephased", "tn_reset_trace_omitted"}
)


def build_tiny_corrupted_table_catalog(control_id: str) -> list[dict[str, Any]]:
    """Build one designated exact corruption for the frozen tiny witnesses.

    ``tn_measurement_dephased`` replaces the branch-resolved M instrument by
    nonselective computational-basis dephasing and fixes its otherwise absent
    raw outcome to zero.  ``tn_reset_trace_omitted`` deletes the ``|1>`` MR
    reset Kraus branch.  These catalogs are negative controls only.
    """

    if control_id not in TINY_TABLE_CORRUPTION_IDS:
        raise ValueError("unknown tiny TN table corruption")
    catalog = deepcopy(_template_catalog())
    templates = {row["template_id"]: row for row in catalog}
    if control_id == "tn_measurement_dephased":
        dephasing: list[Qsqrt2i] = []
        for q_in, raw, q_out in product(range(4), range(2), range(4)):
            ket, bra = _density_bits(q_in)
            dephasing.append(
                _bit(raw == 0 and ket == bra and q_out == q_in)
            )
        templates["M"]["table"] = [value.to_data() for value in dephasing]
    else:
        # MR(q_in=|1><1|, raw=1, q_out=|0><0|) is its K1 reset branch.
        k1_offset = (3 * 2 + 1) * 4
        if templates["MR"]["table"][k1_offset] != ONE.to_data():
            raise AssertionError("frozen MR K1 entry moved")
        templates["MR"]["table"][k1_offset] = ZERO.to_data()
    return catalog


def _add_exact(
    target: dict[tuple[Any, ...], Qsqrt2i],
    key: tuple[Any, ...],
    value: Qsqrt2i,
) -> None:
    if value == ZERO:
        return
    combined = target.get(key, ZERO) + value
    if combined == ZERO:
        target.pop(key, None)
    else:
        target[key] = combined


def contract_tiny_retained_tensor(
    witness_id: str,
    *,
    sign_process: str = "persistent",
    table_catalog: object | None = None,
    boundary_keep: str = "present",
) -> list[dict[str, Any]]:
    """Exactly contract only the frozen T1--T4 qualification witnesses.

    This is intentionally not a target-network entry point: it accepts no
    circuit, factor network, distance, or round count and emits no metric.
    The persistent path exercises the registered sign-chain tables; ``iid``
    is the preregistered negative control for T3.  ``table_catalog`` is a
    tiny-witness-only corruption seam: it must supply the complete frozen
    catalog metadata and exact dense tables.  ``boundary_keep`` may be
    ``omitted_control`` only to demonstrate that all-ones KEEP factors are
    numerically inert; structural qualification must audit their presence.
    """

    if witness_id not in _TINY_WITNESSES:
        raise ValueError("tiny TN witness must be one of T1, T2, T3, T4")
    if sign_process not in {"persistent", "iid"}:
        raise ValueError("sign_process must be 'persistent' or 'iid'")
    if boundary_keep not in {"present", "omitted_control"}:
        raise ValueError("boundary_keep must be 'present' or 'omitted_control'")

    witness = _TINY_WITNESSES[witness_id]
    qubit_count = witness["qubits"]
    tables = _tiny_tables(table_catalog)

    # State key: (density-code tuple, sign-chain endpoint or None, raw tuple).
    states: dict[tuple[Any, ...], Qsqrt2i] = {}
    for densities in product(range(4), repeat=qubit_count):
        initial = ONE
        for density in densities:
            initial = initial * tables["INIT0"][density]
        if sign_process == "persistent":
            for sign in range(2):
                _add_exact(
                    states,
                    (densities, sign, ()),
                    initial * tables["HALF"][sign],
                )
        else:
            _add_exact(states, (densities, None, ()), initial)

    for operation in witness["operations"]:
        name = operation[0]
        following: dict[tuple[Any, ...], Qsqrt2i] = {}
        for (densities, sign, raw), coefficient in states.items():
            if name in {"R", "H"}:
                qubit = operation[1]
                q_in = densities[qubit]
                for q_out in range(4):
                    next_density = list(densities)
                    next_density[qubit] = q_out
                    weight = tables[name][4 * q_in + q_out]
                    _add_exact(
                        following,
                        (tuple(next_density), sign, raw),
                        coefficient * weight,
                    )
            elif name == "CX":
                control, target = operation[1], operation[2]
                c_in, t_in = densities[control], densities[target]
                for c_out, t_out in product(range(4), repeat=2):
                    next_density = list(densities)
                    next_density[control] = c_out
                    next_density[target] = t_out
                    offset = ((c_in * 4 + t_in) * 4 + c_out) * 4 + t_out
                    _add_exact(
                        following,
                        (tuple(next_density), sign, raw),
                        coefficient * tables["CX"][offset],
                    )
            elif name == "COHERENT_Z":
                qubit = operation[1]
                q_in = densities[qubit]
                if sign_process == "persistent":
                    if type(sign) is not int:
                        raise AssertionError("persistent witness lost sign endpoint")
                    sign_choices = (
                        (mu, sign_next, tables["SIGN_EQ"][(sign * 2 + mu) * 2 + sign_next])
                        for mu, sign_next in product(range(2), repeat=2)
                    )
                else:
                    sign_choices = (
                        (mu, None, tables["HALF"][mu]) for mu in range(2)
                    )
                for mu, sign_next, sign_weight in sign_choices:
                    for q_out in range(4):
                        next_density = list(densities)
                        next_density[qubit] = q_out
                        channel = tables["COHERENT_Z"][(q_in * 4 + q_out) * 2 + mu]
                        _add_exact(
                            following,
                            (tuple(next_density), sign_next, raw),
                            coefficient * sign_weight * channel,
                        )
            elif name in {"M", "MR"}:
                qubit = operation[1]
                q_in = densities[qubit]
                for outcome, q_out in product(range(2), range(4)):
                    next_density = list(densities)
                    next_density[qubit] = q_out
                    offset = (q_in * 2 + outcome) * 4 + q_out
                    _add_exact(
                        following,
                        (tuple(next_density), sign, raw + (outcome,)),
                        coefficient * tables[name][offset],
                    )
            else:  # pragma: no cover - the catalog above is frozen
                raise AssertionError(f"unknown tiny TN operation {name}")
        states = following

    retained: dict[tuple[int, int], Qsqrt2i] = {}
    record_operands = witness["record_operands"]
    for (densities, sign, raw), coefficient in states.items():
        weight = coefficient
        for density in densities:
            weight = weight * tables["TRACE"][density]
        if sign_process == "persistent":
            if type(sign) is not int:
                raise AssertionError("persistent witness lost terminal sign")
            weight = weight * tables["ONE"][sign]

        uses_by_raw = [0] * len(raw)
        for operands in record_operands:
            for raw_ordinal in operands:
                uses_by_raw[raw_ordinal] += 1
        for raw_ordinal, use_count in enumerate(uses_by_raw):
            raw_bit = raw[raw_ordinal]
            for _ in range(use_count):
                weight = weight * tables["COPY"][(raw_bit * 2 + raw_bit) * 2 + raw_bit]
            weight = weight * tables["ONE"][raw_bit]

        record: list[int] = []
        for operands in record_operands:
            accumulator = 0
            weight = weight * tables["ZERO"][accumulator]
            for raw_ordinal in operands:
                raw_bit = raw[raw_ordinal]
                output = accumulator ^ raw_bit
                weight = weight * tables["XOR"][(accumulator * 2 + raw_bit) * 2 + output]
                accumulator = output
            if boundary_keep == "present":
                weight = weight * tables["KEEP"][accumulator]
            record.append(accumulator)
        _add_exact(retained, tuple(record), weight)

    return [
        {
            "record": list(record),
            "value": retained.get(record, ZERO).to_data(),
        }
        for record in product(range(2), repeat=2)
    ]
