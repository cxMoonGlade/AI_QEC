"""Exact-small oracle for the no-cutoff structure census.

This module deliberately does not import the simulator implementation.  It
owns only the preregistered one-qubit tracer and a supplemental final-Record
PMF MTBDD.  In particular, the MTBDD built here is not the dynamic exact-pair
ADD and its node count is not eligible for the structure-census headline.
"""

from __future__ import annotations

from collections.abc import Mapping
from functools import lru_cache
from hashlib import sha256
from itertools import product
from typing import Any

from sympy import I, Matrix, Rational, conjugate, simplify, sqrt


Record = tuple[int, ...]
ExactLaw = dict[Record, Rational]


def _require_sympy_rational(value: object, *, name: str) -> Rational:
    if not isinstance(value, Rational):
        raise TypeError(f"{name} must be a SymPy Rational")
    return value


def _require_rounds(rounds: object) -> int:
    if isinstance(rounds, bool) or not isinstance(rounds, int):
        raise TypeError("rounds must be an integer")
    if rounds < 1:
        raise ValueError("rounds must be positive")
    return rounds


def _require_normalized_pair(c: object, s: object) -> tuple[Rational, Rational]:
    c_exact = _require_sympy_rational(c, name="c")
    s_exact = _require_sympy_rational(s, name="s")
    if c_exact**2 + s_exact**2 != 1:
        raise ValueError("c and s must satisfy c**2 + s**2 == 1 exactly")
    return c_exact, s_exact


def pythagorean_pair(t: Rational) -> tuple[Rational, Rational]:
    """Return the exact half-angle rational parametrization for ``t``.

    ``fractions.Fraction`` and floats are intentionally rejected.  Quietly
    converting either would weaken the exact-arithmetic tripwire.
    """

    t_exact = _require_sympy_rational(t, name="t")
    denominator = 1 + t_exact**2
    return (
        (1 - t_exact**2) / denominator,
        2 * t_exact / denominator,
    )


def _all_record_keys(rounds: int) -> tuple[Record, ...]:
    return tuple(product((0, 1), repeat=rounds + 1))


def _record_from_raw(raw_outcomes: tuple[int, ...]) -> Record:
    previous = 0
    detectors: list[int] = []
    for outcome in raw_outcomes:
        detectors.append(outcome ^ previous)
        previous = outcome
    return (*detectors, raw_outcomes[-1])


def persistent_record_law(
    rounds: int,
    c: Rational,
    s: Rational,
) -> ExactLaw:
    """Closed exact Record law for one sign retained across every round.

    The keys are ``(d_0, ..., d_(R-1), o)``.  Structural-zero records are
    retained explicitly, so the returned mapping always has ``2**(R+1)``
    entries.
    """

    rounds_exact = _require_rounds(rounds)
    c_exact, s_exact = _require_normalized_pair(c, s)
    delta = 2 * c_exact * s_exact
    q_plus = (1 + delta) / 2
    q_minus = (1 - delta) / 2

    law: ExactLaw = {}
    for detectors in product((0, 1), repeat=rounds_exact):
        weight = sum(detectors)
        probability = (
            q_plus**weight * q_minus ** (rounds_exact - weight)
            + q_minus**weight * q_plus ** (rounds_exact - weight)
        ) / 2
        valid_observable = weight % 2
        for observable in (0, 1):
            law[(*detectors, observable)] = (
                probability if observable == valid_observable else Rational(0)
            )
    return law


def iid_sign_record_law(
    rounds: int,
    c: Rational,
    s: Rational,
) -> ExactLaw:
    """Exact matched-marginal rival with an independently redrawn sign.

    Averaging the two signs in every round makes each detector flip exactly
    fair.  The observable remains the deterministic detector parity.
    """

    rounds_exact = _require_rounds(rounds)
    _require_normalized_pair(c, s)
    valid_probability = Rational(1, 2**rounds_exact)
    law: ExactLaw = {}
    for detectors in product((0, 1), repeat=rounds_exact):
        valid_observable = sum(detectors) % 2
        for observable in (0, 1):
            law[(*detectors, observable)] = (
                valid_probability
                if observable == valid_observable
                else Rational(0)
            )
    return law


def matrix_branch_record_law(
    rounds: int,
    c: Rational,
    s: Rational,
) -> ExactLaw:
    """Independently enumerate the tracer with exact SymPy matrices.

    This implementation does not call the closed recurrence above.  It applies
    ``U_M=cI-iMsY``, then ``R_Y(pi/2)``, branches on the Z projector, and feeds
    each normalized basis state into the next round without a reset.
    """

    rounds_exact = _require_rounds(rounds)
    c_exact, s_exact = _require_normalized_pair(c, s)

    pauli_y = Matrix(((0, -I), (I, 0)))
    identity = Matrix.eye(2)
    ry_pi_over_two = Matrix(((1, -1), (1, 1))) / sqrt(2)
    basis_states = (Matrix((1, 0)), Matrix((0, 1)))

    law: ExactLaw = {record: Rational(0) for record in _all_record_keys(rounds_exact)}
    for sign in (-1, 1):
        coherent = c_exact * identity - I * sign * s_exact * pauli_y
        round_operator = ry_pi_over_two * coherent
        branches: list[tuple[tuple[int, ...], Matrix, Rational]] = [
            ((), basis_states[0], Rational(1, 2))
        ]
        for _ in range(rounds_exact):
            next_branches: list[tuple[tuple[int, ...], Matrix, Rational]] = []
            for outcomes, state, branch_probability in branches:
                evolved = round_operator * state
                for outcome, collapsed_state in enumerate(basis_states):
                    amplitude = evolved[outcome, 0]
                    measurement_probability = simplify(
                        conjugate(amplitude) * amplitude
                    )
                    next_branches.append(
                        (
                            (*outcomes, outcome),
                            collapsed_state,
                            simplify(branch_probability * measurement_probability),
                        )
                    )
            branches = next_branches

        for raw_outcomes, _state, probability in branches:
            record = _record_from_raw(raw_outcomes)
            law[record] = simplify(law[record] + probability)

    return law


def total_variation_exact(
    left: Mapping[Record, Rational],
    right: Mapping[Record, Rational],
) -> Rational:
    """Return ``1/2 * L1`` over the union support using exact rationals."""

    keys = set(left) | set(right)
    distance = Rational(0)
    for key in keys:
        left_value = _require_sympy_rational(
            left.get(key, Rational(0)), name="left probability"
        )
        right_value = _require_sympy_rational(
            right.get(key, Rational(0)), name="right probability"
        )
        distance += abs(left_value - right_value)
    return distance / 2


def frozen_tail_fixture() -> dict[str, object]:
    """Evaluate the immutable positive sub-1e-12 tail atom directly."""

    t = Rational(3, 7)
    c, s = pythagorean_pair(t)
    rounds = 8
    detectors = (1, 1, 1, 1, 0, 0, 0, 0)
    observable = 0
    delta = 2 * c * s
    probability = ((1 - delta**2) / 4) ** 4
    return {
        "t": t,
        "c": c,
        "s": s,
        "rounds": rounds,
        "detectors": detectors,
        "observable": observable,
        "probability": probability,
        "wrong_observable_probability": Rational(0),
    }


def rational_bytes(value: Rational) -> bytes:
    """Canonical, lossless ASCII bytes for one exact rational value."""

    exact = _require_sympy_rational(value, name="value")
    return f"{exact.p}/{exact.q}".encode("ascii")


def _rational_from_bytes(encoded: object) -> Rational:
    if not isinstance(encoded, bytes):
        raise TypeError("encoded rational must be bytes")
    try:
        numerator_text, denominator_text = encoded.decode("ascii").split("/", 1)
        value = Rational(int(numerator_text), int(denominator_text))
    except (UnicodeDecodeError, ValueError, ZeroDivisionError) as exc:
        raise ValueError("invalid canonical rational bytes") from exc
    if rational_bytes(value) != encoded:
        raise ValueError("noncanonical rational bytes")
    return value


def _canonical_digest(lines: list[bytes]) -> str:
    payload = b"".join(len(line).to_bytes(8, "big") + line for line in lines)
    return sha256(payload).hexdigest()


def _validate_complete_law(law: Mapping[Record, Rational]) -> tuple[int, ExactLaw]:
    if not isinstance(law, Mapping) or not law:
        raise ValueError("law must be a nonempty mapping")

    lengths: set[int] = set()
    normalized: ExactLaw = {}
    for record, probability in law.items():
        if not isinstance(record, tuple) or not record:
            raise TypeError("every Record key must be a nonempty tuple")
        if any(
            isinstance(bit, bool) or not isinstance(bit, int) or bit not in (0, 1)
            for bit in record
        ):
            raise ValueError("Record keys must contain only integer bits")
        exact = _require_sympy_rational(probability, name="probability")
        if exact < 0:
            raise ValueError("Record PMF must be nonnegative")
        lengths.add(len(record))
        normalized[record] = exact

    if len(lengths) != 1:
        raise ValueError("Record keys must all have the same length")
    variable_count = lengths.pop()
    expected_keys = set(product((0, 1), repeat=variable_count))
    if set(normalized) != expected_keys:
        raise ValueError("Record PMF must explicitly cover the complete bit domain")
    if sum(normalized.values(), Rational(0)) != 1:
        raise ValueError("Record PMF must be exactly normalized")
    return variable_count, normalized


def build_record_pmf_mtbdd(law: Mapping[Record, Rational]) -> dict[str, Any]:
    """Build a canonical reduced ordered MTBDD for the final Record PMF.

    Variable order is chronological detector order followed by the observable.
    Nodes are canonically numbered after reduction: terminals by exact value
    bytes, then internal nodes bottom-up by ``(level, low_id, high_id)``.
    """

    variable_count, complete_law = _validate_complete_law(law)
    detector_count = variable_count - 1
    variable_order = tuple(
        [f"d_{index}" for index in range(detector_count)] + ["o"]
    )

    # A token is a fully structural, allocation-order-independent node name.
    # Terminal tokens are ("terminal", exact_bytes); internal tokens are
    # ("node", level, low_token, high_token).
    @lru_cache(maxsize=None)
    def build_token(level: int, prefix: Record) -> tuple[Any, ...]:
        if level == variable_count:
            return ("terminal", rational_bytes(complete_law[prefix]))
        low = build_token(level + 1, (*prefix, 0))
        high = build_token(level + 1, (*prefix, 1))
        if low == high:
            return low
        return ("node", level, low, high)

    root_token = build_token(0, ())
    terminal_tokens: set[tuple[Any, ...]] = set()
    nodes_by_level: dict[int, set[tuple[Any, ...]]] = {
        level: set() for level in range(variable_count)
    }

    def collect(token: tuple[Any, ...]) -> None:
        if token[0] == "terminal":
            terminal_tokens.add(token)
            return
        level = token[1]
        if token in nodes_by_level[level]:
            return
        nodes_by_level[level].add(token)
        collect(token[2])
        collect(token[3])

    collect(root_token)

    token_ids: dict[tuple[Any, ...], int] = {}
    terminals: list[dict[str, object]] = []
    next_id = 0
    for token in sorted(terminal_tokens, key=lambda item: item[1]):
        token_ids[token] = next_id
        terminals.append({"id": next_id, "value": token[1]})
        next_id += 1

    nodes: list[dict[str, int]] = []
    for level in reversed(range(variable_count)):
        ordered = sorted(
            nodes_by_level[level],
            key=lambda token: (token_ids[token[2]], token_ids[token[3]]),
        )
        for token in ordered:
            low_id = token_ids[token[2]]
            high_id = token_ids[token[3]]
            token_ids[token] = next_id
            nodes.append(
                {
                    "id": next_id,
                    "level": level,
                    "low": low_id,
                    "high": high_id,
                }
            )
            next_id += 1

    order_lines = [name.encode("ascii") for name in variable_order]
    table_lines = [
        b"T|" + str(row["id"]).encode("ascii") + b"|" + row["value"]
        for row in terminals
    ]
    table_lines.extend(
        (
            f"N|{row['id']}|{row['level']}|{row['low']}|{row['high']}"
        ).encode("ascii")
        for row in nodes
    )
    pmf_lines = [
        bytes(record) + b"|" + rational_bytes(complete_law[record])
        for record in sorted(complete_law)
    ]

    internal_node_count = len(nodes)
    terminal_node_count = len(terminals)
    return {
        "schema": "error_coupling_simulator.external.record_pmf_mtbdd.v1",
        "metric_name": "n_record_pmf_mtbdd_nodes_final",
        "headline_eligible": False,
        "represented_object": "final_complete_record_pmf",
        "variable_order": variable_order,
        "root_id": token_ids[root_token],
        "terminals": tuple(terminals),
        "nodes": tuple(nodes),
        "terminal_values": tuple(row["value"] for row in terminals),
        "internal_node_count": internal_node_count,
        "terminal_node_count": terminal_node_count,
        "node_count": internal_node_count + terminal_node_count,
        "order_sha256": _canonical_digest(order_lines),
        "node_table_sha256": _canonical_digest(table_lines),
        "pmf_sha256": _canonical_digest(pmf_lines),
    }


def reconstruct_record_pmf_mtbdd(diagram: Mapping[str, Any]) -> ExactLaw:
    """Reconstruct and validate the complete PMF represented by ``diagram``."""

    if diagram.get("metric_name") != "n_record_pmf_mtbdd_nodes_final":
        raise ValueError("not a final Record PMF MTBDD")
    variable_order = diagram.get("variable_order")
    if not isinstance(variable_order, tuple) or not variable_order:
        raise ValueError("invalid MTBDD variable order")
    variable_count = len(variable_order)

    terminal_by_id: dict[int, Rational] = {}
    for row in diagram.get("terminals", ()):
        node_id = row.get("id")
        if isinstance(node_id, bool) or not isinstance(node_id, int):
            raise ValueError("invalid terminal ID")
        if node_id in terminal_by_id:
            raise ValueError("duplicate terminal ID")
        terminal_by_id[node_id] = _rational_from_bytes(row.get("value"))

    node_by_id: dict[int, tuple[int, int, int]] = {}
    for row in diagram.get("nodes", ()):
        node_id = row.get("id")
        level = row.get("level")
        low = row.get("low")
        high = row.get("high")
        if any(
            isinstance(value, bool) or not isinstance(value, int)
            for value in (node_id, level, low, high)
        ):
            raise ValueError("invalid internal-node field")
        if node_id in node_by_id or node_id in terminal_by_id:
            raise ValueError("duplicate MTBDD node ID")
        if not 0 <= level < variable_count or low == high:
            raise ValueError("invalid reduced internal node")
        node_by_id[node_id] = (level, low, high)

    root_id = diagram.get("root_id")
    if isinstance(root_id, bool) or not isinstance(root_id, int):
        raise ValueError("invalid MTBDD root ID")

    def evaluate(bits: Record) -> Rational:
        current = root_id
        previous_level = -1
        seen: set[int] = set()
        while current in node_by_id:
            if current in seen:
                raise ValueError("cyclic MTBDD")
            seen.add(current)
            level, low, high = node_by_id[current]
            if level <= previous_level:
                raise ValueError("MTBDD violates its variable order")
            previous_level = level
            current = high if bits[level] else low
        if current not in terminal_by_id:
            raise ValueError("MTBDD edge references a missing node")
        return terminal_by_id[current]

    law: ExactLaw = {
        bits: evaluate(bits) for bits in product((0, 1), repeat=variable_count)
    }
    _validate_complete_law(law)
    return law


__all__ = [
    "build_record_pmf_mtbdd",
    "frozen_tail_fixture",
    "iid_sign_record_law",
    "matrix_branch_record_law",
    "persistent_record_law",
    "pythagorean_pair",
    "rational_bytes",
    "reconstruct_record_pmf_mtbdd",
    "total_variation_exact",
]
