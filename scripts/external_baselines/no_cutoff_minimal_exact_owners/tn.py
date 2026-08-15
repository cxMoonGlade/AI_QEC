"""Exact-small retained-boundary graph metrics and subset-DP certificates."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from .model import MICRO_SCOPE, SOLVER_PERMISSION, TARGET_LOWERING, sha256_json


TERMINAL_REPRESENTATION = "factorized_boundary_factors"
MAX_EXACT_INTERNAL_INDICES = 20


@dataclass(frozen=True, slots=True)
class Index:
    name: str
    role: str
    domain_size: int

    def __post_init__(self) -> None:
        if type(self.name) is not str or not self.name:
            raise ValueError("index name must be nonempty")
        if self.role not in ("density", "classical", "record"):
            raise ValueError("unknown index role")
        if type(self.domain_size) is not int or self.domain_size not in (2, 4):
            raise ValueError("micro-owner domains must be exactly two or four")
        if self.role == "density" and self.domain_size != 4:
            raise ValueError("density index must have domain four")
        if self.role in ("classical", "record") and self.domain_size != 2:
            raise ValueError("classical and Record indices must have domain two")

    @property
    def log2_domain(self) -> int:
        return 1 if self.domain_size == 2 else 2

    def to_data(self) -> dict[str, object]:
        return {"domain_size": self.domain_size, "name": self.name, "role": self.role}


@dataclass(frozen=True, slots=True)
class Factor:
    name: str
    kind: str
    scope: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.name) is not str or not self.name:
            raise ValueError("factor name must be nonempty")
        if self.kind not in ("PAIR", "KEEP"):
            raise ValueError("unknown factor kind")
        if type(self.scope) is not tuple or not self.scope:
            raise ValueError("factor scope must be a nonempty tuple")
        if len(set(self.scope)) != len(self.scope):
            raise ValueError("factor scope may not repeat an index")
        if self.kind == "KEEP" and len(self.scope) != 1:
            raise ValueError("KEEP factor must be unary")

    def to_data(self) -> dict[str, object]:
        return {"kind": self.kind, "name": self.name, "scope": list(self.scope)}


@dataclass(frozen=True, slots=True)
class FactorGraph:
    indices: tuple[Index, ...]
    internal: tuple[str, ...]
    boundary: tuple[str, ...]
    factors: tuple[Factor, ...]
    terminal_record_representation: str = TERMINAL_REPRESENTATION

    def __post_init__(self) -> None:
        names = tuple(index.name for index in self.indices)
        if len(names) != len(set(names)):
            raise ValueError("index names must be unique")
        if type(self.internal) is not tuple or type(self.boundary) is not tuple:
            raise TypeError("internal and boundary orders must be tuples")
        if len(self.internal) != len(set(self.internal)):
            raise ValueError("internal index order may not contain duplicates")
        if len(self.boundary) != len(set(self.boundary)):
            raise ValueError("boundary index order may not contain duplicates")
        if set(self.internal) & set(self.boundary):
            raise ValueError("internal and boundary indices must be disjoint")
        if set(self.internal) | set(self.boundary) != set(names):
            raise ValueError("internal and boundary indices must partition the graph")
        if not self.boundary:
            raise ValueError("retained-boundary graph requires KEEP indices")
        index_by_name = {index.name: index for index in self.indices}
        if any(index_by_name[name].role != "record" for name in self.boundary):
            raise ValueError("boundary indices must have Record role")
        if len({factor.name for factor in self.factors}) != len(self.factors):
            raise ValueError("factor names must be unique")
        for factor in self.factors:
            if any(name not in index_by_name for name in factor.scope):
                raise ValueError("factor references an unknown index")
        keep_scopes = [factor.scope for factor in self.factors if factor.kind == "KEEP"]
        if sorted(keep_scopes) != sorted((name,) for name in self.boundary):
            raise ValueError("each boundary index requires exactly one unary KEEP factor")
        if self.terminal_record_representation != TERMINAL_REPRESENTATION:
            raise ValueError("terminal Record representation must remain factorized")
        used = {name for factor in self.factors for name in factor.scope}
        if used != set(names):
            raise ValueError("every index must occur in a factor")

    @property
    def index_by_name(self) -> dict[str, Index]:
        return {index.name: index for index in self.indices}

    @property
    def vertex_order(self) -> tuple[str, ...]:
        return tuple(index.name for index in self.indices)

    def to_data(self) -> dict[str, object]:
        return {
            "boundary": list(self.boundary),
            "factors": [factor.to_data() for factor in self.factors],
            "indices": [index.to_data() for index in self.indices],
            "internal": list(self.internal),
            "route": "retained_boundary_mixed_domain_micro.v1",
            "terminal_record_representation": self.terminal_record_representation,
        }

    @property
    def sha256(self) -> str:
        return sha256_json(self.to_data())


def frozen_tn_graph() -> FactorGraph:
    return FactorGraph(
        indices=(
            Index("d0", "density", 4),
            Index("d1", "density", 4),
            Index("c0", "classical", 2),
            Index("c1", "classical", 2),
            Index("d2", "density", 4),
            Index("o0", "record", 2),
            Index("o1", "record", 2),
        ),
        internal=("d0", "d1", "c0", "c1", "d2"),
        boundary=("o0", "o1"),
        factors=(
            Factor("KEEP:o0", "KEEP", ("o0",)),
            Factor("KEEP:o1", "KEEP", ("o1",)),
            Factor("d0-d1", "PAIR", ("d0", "d1")),
            Factor("d0-c1", "PAIR", ("d0", "c1")),
            Factor("d0-o0", "PAIR", ("d0", "o0")),
            Factor("d1-d2", "PAIR", ("d1", "d2")),
            Factor("d1-o1", "PAIR", ("d1", "o1")),
            Factor("c0-c1", "PAIR", ("c0", "c1")),
            Factor("c0-d2", "PAIR", ("c0", "d2")),
            Factor("c0-o1", "PAIR", ("c0", "o1")),
            Factor("c1-o1", "PAIR", ("c1", "o1")),
            Factor("d2-o0", "PAIR", ("d2", "o0")),
        ),
    )


def validate_frozen_tn_graph(graph: FactorGraph) -> None:
    if graph.sha256 != frozen_tn_graph().sha256:
        raise ValueError("graph does not match the frozen TN fixture identity")


def primal_adjacency(graph: FactorGraph) -> dict[str, set[str]]:
    adjacency = {name: set() for name in graph.vertex_order}
    for factor in graph.factors:
        for left, right in combinations(factor.scope, 2):
            adjacency[left].add(right)
            adjacency[right].add(left)
    return adjacency


def _initial_floors(graph: FactorGraph) -> tuple[int, int]:
    weights = {name: index.log2_domain for name, index in graph.index_by_name.items()}
    w0 = max(len(factor.scope) - 1 for factor in graph.factors)
    lambda0 = max(sum(weights[name] for name in factor.scope) for factor in graph.factors)
    return w0, lambda0


def _eliminate(adjacency: dict[str, set[str]], name: str) -> tuple[str, ...]:
    if name not in adjacency:
        raise ValueError("elimination order repeats or names an absent index")
    neighbors = tuple(sorted(adjacency[name]))
    for left, right in combinations(neighbors, 2):
        adjacency[left].add(right)
        adjacency[right].add(left)
    for neighbor in neighbors:
        adjacency[neighbor].discard(name)
    del adjacency[name]
    return neighbors


def replay_order(graph: FactorGraph, order: tuple[str, ...]) -> dict[str, object]:
    if type(order) is not tuple:
        raise TypeError("elimination order must be a tuple")
    if len(order) != len(graph.internal) or set(order) != set(graph.internal):
        raise ValueError("order must be a permutation of internal indices only")
    if set(order) & set(graph.boundary):
        raise ValueError("KEEP boundary indices may not be eliminated")
    adjacency = primal_adjacency(graph)
    weights = {name: index.log2_domain for name, index in graph.index_by_name.items()}
    width, lambda_value = _initial_floors(graph)
    history = []
    ordinal = {name: index for index, name in enumerate(graph.vertex_order)}
    for name in order:
        neighbors = _eliminate(adjacency, name)
        neighbors = tuple(sorted(neighbors, key=ordinal.__getitem__))
        bucket_lambda = weights[name] + sum(weights[neighbor] for neighbor in neighbors)
        width = max(width, len(neighbors))
        lambda_value = max(lambda_value, bucket_lambda)
        history.append(
            {
                "bucket_lambda": bucket_lambda,
                "eliminated": name,
                "neighbor_count": len(neighbors),
                "neighbors": list(neighbors),
            }
        )
    return {"history": history, "lambda": lambda_value, "width": width}


def _torso_after(graph: FactorGraph, eliminated: frozenset[str]) -> dict[str, set[str]]:
    if not eliminated <= set(graph.internal):
        raise ValueError("torso subset may contain only internal indices")
    adjacency = primal_adjacency(graph)
    for name in graph.internal:
        if name in eliminated:
            _eliminate(adjacency, name)
    return adjacency


def subset_dp(graph: FactorGraph, objective: str) -> dict[str, object]:
    if objective not in ("width", "lambda"):
        raise ValueError("objective must be width or lambda")
    if len(graph.internal) > MAX_EXACT_INTERNAL_INDICES:
        raise RuntimeError("CENSORED_RESOURCE")
    n = len(graph.internal)
    size = 1 << n
    w0, lambda0 = _initial_floors(graph)
    floor = w0 if objective == "width" else lambda0
    values = [0] * size
    orders: list[tuple[str, ...]] = [tuple() for _ in range(size)]
    values[0] = floor
    ordinal = {name: index for index, name in enumerate(graph.internal)}
    weights = {name: index.log2_domain for name, index in graph.index_by_name.items()}

    def order_key(order: tuple[str, ...]) -> tuple[int, ...]:
        return tuple(ordinal[name] for name in order)

    for mask in range(1, size):
        best_value: int | None = None
        best_order: tuple[str, ...] | None = None
        for bit, name in enumerate(graph.internal):
            if not mask & (1 << bit):
                continue
            previous = mask ^ (1 << bit)
            eliminated = frozenset(
                graph.internal[index] for index in range(n) if previous & (1 << index)
            )
            adjacency = _torso_after(graph, eliminated)
            neighbors = adjacency[name]
            next_cost = (
                len(neighbors)
                if objective == "width"
                else weights[name] + sum(weights[neighbor] for neighbor in neighbors)
            )
            candidate_value = max(values[previous], next_cost)
            candidate_order = orders[previous] + (name,)
            if best_value is None or (candidate_value, order_key(candidate_order)) < (
                best_value,
                order_key(best_order or tuple()),
            ):
                best_value = candidate_value
                best_order = candidate_order
        assert best_value is not None and best_order is not None
        values[mask] = best_value
        orders[mask] = best_order

    proof_body = {
        "floor": floor,
        "graph_sha256": graph.sha256,
        "mask_bit_order": list(graph.internal),
        "objective": objective,
        "orders": [list(order) for order in orders],
        "tie_break": "lexicographic_frozen_internal_ordinal",
        "values": values,
    }
    return {**proof_body, "proof_sha256": sha256_json(proof_body)}


def verify_subset_dp_proof(graph: FactorGraph, proof: dict[str, object]) -> None:
    if set(proof) != {
        "floor",
        "graph_sha256",
        "mask_bit_order",
        "objective",
        "orders",
        "proof_sha256",
        "tie_break",
        "values",
    }:
        raise ValueError("proof key set is invalid")
    objective = proof.get("objective")
    if objective not in ("width", "lambda"):
        raise ValueError("proof objective is invalid")
    if proof.get("graph_sha256") != graph.sha256:
        raise ValueError("proof graph identity mismatch")
    if proof.get("mask_bit_order") != list(graph.internal):
        raise ValueError("proof mask order mismatch")
    values = proof.get("values")
    orders = proof.get("orders")
    if not isinstance(values, list) or not isinstance(orders, list):
        raise TypeError("proof values and orders must be lists")
    expected = subset_dp(graph, str(objective))
    if proof.get("floor") != expected["floor"]:
        raise ValueError("subset-DP proof floor mismatch")
    if proof.get("tie_break") != expected["tie_break"]:
        raise ValueError("subset-DP proof tie-break mismatch")
    if values != expected["values"] or orders != expected["orders"]:
        raise ValueError("subset-DP recurrence or tie-break mismatch")
    body = {key: value for key, value in proof.items() if key != "proof_sha256"}
    if proof.get("proof_sha256") != sha256_json(body):
        raise ValueError("subset-DP proof hash mismatch")
    full_order = tuple(orders[-1])
    replay = replay_order(graph, full_order)
    replay_value = replay["width" if objective == "width" else "lambda"]
    if replay_value != values[-1]:
        raise ValueError("proof upper order does not match its exact value")


def solve_exact_retained_boundary(graph: FactorGraph) -> dict[str, object]:
    width_proof = subset_dp(graph, "width")
    lambda_proof = subset_dp(graph, "lambda")
    verify_subset_dp_proof(graph, width_proof)
    verify_subset_dp_proof(graph, lambda_proof)
    width_order = tuple(width_proof["orders"][-1])
    lambda_order = tuple(lambda_proof["orders"][-1])
    width_replay = replay_order(graph, width_order)
    lambda_replay = replay_order(graph, lambda_order)
    return {
        "boundary": list(graph.boundary),
        "factor_graph": graph.to_data(),
        "factor_graph_sha256": graph.sha256,
        "terminal_record_representation": graph.terminal_record_representation,
        "unweighted": {
            "exact_value": width_proof["values"][-1],
            "order": list(width_order),
            "proof": width_proof,
            "replay": width_replay,
            "status": "EXACT",
        },
        "weighted": {
            "exact_value": lambda_proof["values"][-1],
            "order": list(lambda_order),
            "peak_dense_entries": 1 << int(lambda_proof["values"][-1]),
            "proof": lambda_proof,
            "replay": lambda_replay,
            "status": "EXACT",
        },
    }


def run_retained_boundary_tn_owner(graph: FactorGraph) -> dict[str, object]:
    validate_frozen_tn_graph(graph)
    result = solve_exact_retained_boundary(graph)
    return {
        **result,
        "scope": MICRO_SCOPE,
        "solver_permission": SOLVER_PERMISSION,
        "target_lowering": TARGET_LOWERING,
    }
