"""Independent literal oracle for the retained-boundary TN microfixture.

This module intentionally depends only on the Python standard library.  The
fixture, primal graph construction, elimination replay, exhaustive search, and
subset recurrence are restated here rather than imported from the candidate
owner.  It qualifies only the frozen microfixture; it is not a target lowering.
"""

from __future__ import annotations

import hashlib
from itertools import combinations, permutations
import json


MICRO_SCOPE = "MICRO_QUALIFICATION_ONLY"
SOLVER_PERMISSION = "CODE_BLOCKED"
TARGET_LOWERING = "UNAVAILABLE"

VERTICES = ("d0", "d1", "c0", "c1", "d2", "o0", "o1")
INTERNAL = ("d0", "d1", "c0", "c1", "d2")
BOUNDARY = ("o0", "o1")
LOG2_DOMAINS = {
    "d0": 2,
    "d1": 2,
    "c0": 1,
    "c1": 1,
    "d2": 2,
    "o0": 1,
    "o1": 1,
}
ROLES = {
    "d0": "density",
    "d1": "density",
    "c0": "classical",
    "c1": "classical",
    "d2": "density",
    "o0": "record",
    "o1": "record",
}
FACTORS = (
    ("KEEP:o0", "KEEP", ("o0",)),
    ("KEEP:o1", "KEEP", ("o1",)),
    ("d0-d1", "PAIR", ("d0", "d1")),
    ("d0-c1", "PAIR", ("d0", "c1")),
    ("d0-o0", "PAIR", ("d0", "o0")),
    ("d1-d2", "PAIR", ("d1", "d2")),
    ("d1-o1", "PAIR", ("d1", "o1")),
    ("c0-c1", "PAIR", ("c0", "c1")),
    ("c0-d2", "PAIR", ("c0", "d2")),
    ("c0-o1", "PAIR", ("c0", "o1")),
    ("c1-o1", "PAIR", ("c1", "o1")),
    ("d2-o0", "PAIR", ("d2", "o0")),
)


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _literal_graph_data() -> dict[str, object]:
    return {
        "boundary": list(BOUNDARY),
        "factors": [
            {"kind": kind, "name": name, "scope": list(scope)}
            for name, kind, scope in FACTORS
        ],
        "indices": [
            {
                "domain_size": 1 << LOG2_DOMAINS[name],
                "name": name,
                "role": ROLES[name],
            }
            for name in VERTICES
        ],
        "internal": list(INTERNAL),
        "route": "retained_boundary_mixed_domain_micro.v1",
        "terminal_record_representation": "factorized_boundary_factors",
    }


GRAPH_SHA256 = _canonical_sha256(_literal_graph_data())


def _validate_spec(
    vertices: tuple[str, ...],
    internal: tuple[str, ...],
    boundary: tuple[str, ...],
    log2_domains: dict[str, int],
    factors: tuple[tuple[str, str, tuple[str, ...]], ...],
) -> None:
    if len(vertices) != len(set(vertices)):
        raise ValueError("literal vertices must be unique")
    if set(internal) & set(boundary) or set(internal) | set(boundary) != set(vertices):
        raise ValueError("literal internal and boundary sets must partition vertices")
    if set(log2_domains) != set(vertices) or any(
        type(value) is not int or value not in (1, 2)
        for value in log2_domains.values()
    ):
        raise ValueError("literal domain weights must be one or two")
    if len({name for name, _, _ in factors}) != len(factors):
        raise ValueError("literal factor names must be unique")
    for _, kind, scope in factors:
        if kind not in ("PAIR", "KEEP"):
            raise ValueError("literal factor kind is invalid")
        if not scope or len(scope) != len(set(scope)) or not set(scope) <= set(vertices):
            raise ValueError("literal factor scope is invalid")
        if kind == "KEEP" and len(scope) != 1:
            raise ValueError("literal KEEP scope must be unary")
    keep_scopes = sorted(scope for _, kind, scope in factors if kind == "KEEP")
    if keep_scopes != sorted((name,) for name in boundary):
        raise ValueError("literal retained boundary requires one KEEP per output")
    used = {name for _, _, scope in factors for name in scope}
    if used != set(vertices):
        raise ValueError("literal factors must cover every vertex")


def _adjacency(
    vertices: tuple[str, ...],
    factors: tuple[tuple[str, str, tuple[str, ...]], ...],
) -> dict[str, set[str]]:
    adjacency = {name: set() for name in vertices}
    for _, _, scope in factors:
        for left, right in combinations(scope, 2):
            adjacency[left].add(right)
            adjacency[right].add(left)
    return adjacency


def _eliminate(adjacency: dict[str, set[str]], name: str) -> set[str]:
    if name not in adjacency:
        raise ValueError("literal elimination order repeats or names an absent vertex")
    neighbors = set(adjacency[name])
    for left, right in combinations(neighbors, 2):
        adjacency[left].add(right)
        adjacency[right].add(left)
    for neighbor in neighbors:
        adjacency[neighbor].remove(name)
    del adjacency[name]
    return neighbors


def _initial_floors(
    log2_domains: dict[str, int],
    factors: tuple[tuple[str, str, tuple[str, ...]], ...],
) -> tuple[int, int]:
    width_floor = max(len(scope) - 1 for _, _, scope in factors)
    lambda_floor = max(
        sum(log2_domains[name] for name in scope) for _, _, scope in factors
    )
    return width_floor, lambda_floor


def _replay(
    order: tuple[str, ...],
    *,
    vertices: tuple[str, ...] = VERTICES,
    internal: tuple[str, ...] = INTERNAL,
    boundary: tuple[str, ...] = BOUNDARY,
    log2_domains: dict[str, int] = LOG2_DOMAINS,
    factors: tuple[tuple[str, str, tuple[str, ...]], ...] = FACTORS,
) -> tuple[int, int]:
    _validate_spec(vertices, internal, boundary, log2_domains, factors)
    if type(order) is not tuple or len(order) != len(internal) or set(order) != set(internal):
        raise ValueError("literal order must permute internal vertices only")
    adjacency = _adjacency(vertices, factors)
    width, lambda_value = _initial_floors(log2_domains, factors)
    for name in order:
        neighbors = _eliminate(adjacency, name)
        width = max(width, len(neighbors))
        lambda_value = max(
            lambda_value,
            log2_domains[name] + sum(log2_domains[neighbor] for neighbor in neighbors),
        )
    return width, lambda_value


def _subset_dp(
    objective: str,
    *,
    vertices: tuple[str, ...] = VERTICES,
    internal: tuple[str, ...] = INTERNAL,
    boundary: tuple[str, ...] = BOUNDARY,
    log2_domains: dict[str, int] = LOG2_DOMAINS,
    factors: tuple[tuple[str, str, tuple[str, ...]], ...] = FACTORS,
    graph_sha256: str = GRAPH_SHA256,
) -> dict[str, object]:
    if objective not in ("width", "lambda"):
        raise ValueError("literal objective must be width or lambda")
    _validate_spec(vertices, internal, boundary, log2_domains, factors)
    width_floor, lambda_floor = _initial_floors(log2_domains, factors)
    floor = width_floor if objective == "width" else lambda_floor
    size = 1 << len(internal)
    values = [0] * size
    orders: list[tuple[str, ...]] = [tuple() for _ in range(size)]
    values[0] = floor
    ordinal = {name: position for position, name in enumerate(internal)}

    def order_key(order: tuple[str, ...]) -> tuple[int, ...]:
        return tuple(ordinal[name] for name in order)

    for mask in range(1, size):
        best: tuple[int, tuple[int, ...], tuple[str, ...]] | None = None
        for bit, name in enumerate(internal):
            if not mask & (1 << bit):
                continue
            previous = mask ^ (1 << bit)
            adjacency = _adjacency(vertices, factors)
            for previous_bit, previous_name in enumerate(internal):
                if previous & (1 << previous_bit):
                    _eliminate(adjacency, previous_name)
            neighbors = adjacency[name]
            next_cost = (
                len(neighbors)
                if objective == "width"
                else log2_domains[name]
                + sum(log2_domains[neighbor] for neighbor in neighbors)
            )
            candidate_order = orders[previous] + (name,)
            candidate = (
                max(values[previous], next_cost),
                order_key(candidate_order),
                candidate_order,
            )
            if best is None or candidate[:2] < best[:2]:
                best = candidate
        if best is None:
            raise AssertionError("nonempty subset has no predecessor")
        values[mask], _, orders[mask] = best

    order_lists = [list(order) for order in orders]
    proof_body = {
        "floor": floor,
        "graph_sha256": graph_sha256,
        "mask_bit_order": list(internal),
        "objective": objective,
        "orders": order_lists,
        "tie_break": "lexicographic_frozen_internal_ordinal",
        "values": values,
    }
    return {
        **proof_body,
        "orders_sha256": _canonical_sha256(order_lists),
        "proof_sha256": _canonical_sha256(proof_body),
        "values_sha256": _canonical_sha256(values),
    }


def _exhaustive() -> dict[str, object]:
    observations = {order: _replay(order) for order in permutations(INTERNAL)}
    best_width = min(value[0] for value in observations.values())
    best_lambda = min(value[1] for value in observations.values())
    width_orders = tuple(
        order for order, value in observations.items() if value[0] == best_width
    )
    lambda_orders = tuple(
        order for order, value in observations.items() if value[1] == best_lambda
    )
    return {
        "optimum_sets_disjoint": set(width_orders).isdisjoint(lambda_orders),
        "order_count": len(observations),
        "unweighted": {
            "exact_value": best_width,
            "optimum_count": len(width_orders),
            "optimum_orders": [list(order) for order in width_orders],
            "selected_order": list(width_orders[0]),
        },
        "weighted": {
            "exact_value": best_lambda,
            "optimum_count": len(lambda_orders),
            "optimum_orders": [list(order) for order in lambda_orders],
            "peak_dense_entries": 1 << best_lambda,
            "selected_order": list(lambda_orders[0]),
        },
    }


def verify_frozen_subset_proof(proof: dict[str, object]) -> None:
    """Verify an owner-style proof using only the independently restated fixture."""

    if not isinstance(proof, dict):
        raise TypeError("literal proof must be a dictionary")
    objective = proof.get("objective")
    if objective not in ("width", "lambda"):
        raise ValueError("literal proof objective is invalid")
    expected = _subset_dp(str(objective))
    for key in ("graph_sha256", "mask_bit_order", "floor", "tie_break"):
        if proof.get(key) != expected[key]:
            raise ValueError(f"literal proof {key} mismatch")
    if proof.get("values") != expected["values"] or proof.get("orders") != expected["orders"]:
        raise ValueError("literal subset-DP recurrence or tie-break mismatch")
    owner_style_body = {
        key: proof.get(key)
        for key in (
            "floor",
            "graph_sha256",
            "mask_bit_order",
            "objective",
            "orders",
            "tie_break",
            "values",
        )
    }
    if proof.get("proof_sha256") != _canonical_sha256(owner_style_body):
        raise ValueError("literal subset-DP proof hash mismatch")
    final_order = tuple(expected["orders"][-1])
    width, lambda_value = _replay(final_order)
    replay_value = width if objective == "width" else lambda_value
    if replay_value != expected["values"][-1]:
        raise ValueError("literal subset-DP upper order mismatch")


def _corruption_checks() -> dict[str, object]:
    removed_edge = tuple(factor for factor in FACTORS if factor[0] != "d0-d1")
    removed_edge_value = _subset_dp("lambda", factors=removed_edge)["values"][-1]
    removed_second_edge = tuple(factor for factor in FACTORS if factor[0] != "d1-d2")
    removed_second_edge_value = _subset_dp(
        "lambda", factors=removed_second_edge
    )["values"][-1]

    lighter_domains = {**LOG2_DOMAINS, "d1": 1}
    lighter_value = _subset_dp("lambda", log2_domains=lighter_domains)["values"][-1]

    heavier_domains = {**LOG2_DOMAINS, "c0": 2}
    heavier_value = _subset_dp("lambda", log2_domains=heavier_domains)["values"][-1]

    clamped_factors = tuple(
        factor for factor in FACTORS if set(factor[2]) <= set(INTERNAL)
    )
    clamped_domains = {name: LOG2_DOMAINS[name] for name in INTERNAL}
    fixed_width = _subset_dp(
        "width",
        vertices=INTERNAL,
        internal=INTERNAL,
        boundary=tuple(),
        log2_domains=clamped_domains,
        factors=clamped_factors,
        graph_sha256="INELIGIBLE_FIXED_OUTPUT_DIAGNOSTIC",
    )["values"][-1]
    fixed_lambda = _subset_dp(
        "lambda",
        vertices=INTERNAL,
        internal=INTERNAL,
        boundary=tuple(),
        log2_domains=clamped_domains,
        factors=clamped_factors,
        graph_sha256="INELIGIBLE_FIXED_OUTPUT_DIAGNOSTIC",
    )["values"][-1]

    missing_keep_rejected = False
    try:
        _validate_spec(
            VERTICES,
            INTERNAL,
            BOUNDARY,
            LOG2_DOMAINS,
            tuple(factor for factor in FACTORS if factor[0] != "KEEP:o0"),
        )
    except ValueError:
        missing_keep_rejected = True

    boundary_elimination_rejected = False
    try:
        _replay(("d0", "d1", "c0", "c1", "o0"))
    except ValueError:
        boundary_elimination_rejected = True

    tampered = _subset_dp("lambda")
    tampered["values"] = list(tampered["values"])
    tampered["values"][2] = 6
    tampered_rejected = False
    try:
        verify_frozen_subset_proof(tampered)
    except ValueError:
        tampered_rejected = True

    return {
        "boundary_elimination_rejected": boundary_elimination_rejected,
        "change_c0_log2_domain_1_to_2": {"weighted_exact_value": heavier_value},
        "change_d1_log2_domain_2_to_1": {"weighted_exact_value": lighter_value},
        "clamp_record_boundary_ineligible": {
            "classification": "INELIGIBLE_FIXED_OUTPUT_DIAGNOSTIC",
            "unweighted_exact_value": fixed_width,
            "weighted_exact_value": fixed_lambda,
        },
        "missing_keep_rejected": missing_keep_rejected,
        "remove_edge_d0_d1": {"weighted_exact_value": removed_edge_value},
        "remove_edge_d1_d2": {"weighted_exact_value": removed_second_edge_value},
        "tampered_dp_cell_rejected": tampered_rejected,
    }


def run_independent_tn_oracle() -> dict[str, object]:
    """Return the independent exact micro-oracle and its falsifier receipts."""

    _validate_spec(VERTICES, INTERNAL, BOUNDARY, LOG2_DOMAINS, FACTORS)
    exhaustive = _exhaustive()
    width_proof = _subset_dp("width")
    lambda_proof = _subset_dp("lambda")
    if width_proof["values"][-1] != exhaustive["unweighted"]["exact_value"]:
        raise AssertionError("literal exhaustive and subset width disagree")
    if lambda_proof["values"][-1] != exhaustive["weighted"]["exact_value"]:
        raise AssertionError("literal exhaustive and subset lambda disagree")
    if width_proof["orders"][-1] != exhaustive["unweighted"]["selected_order"]:
        raise AssertionError("literal width tie-break disagree")
    if lambda_proof["orders"][-1] != exhaustive["weighted"]["selected_order"]:
        raise AssertionError("literal lambda tie-break disagree")
    return {
        "corruption_checks": _corruption_checks(),
        "exhaustive": exhaustive,
        "graph_sha256": GRAPH_SHA256,
        "oracle": "stdlib_literal_retained_boundary_tn.v1",
        "scope": MICRO_SCOPE,
        "solver_permission": SOLVER_PERMISSION,
        "subset_dp": {
            "unweighted": width_proof,
            "weighted": lambda_proof,
        },
        "target_lowering": TARGET_LOWERING,
    }
