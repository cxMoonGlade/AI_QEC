"""TDD contracts for the exact retained-boundary TN micro-owner."""

from __future__ import annotations

from copy import deepcopy
from itertools import combinations, permutations

import pytest


def _literal_replay(order: tuple[str, ...]) -> tuple[int, int]:
    vertices = ("d0", "d1", "c0", "c1", "d2", "o0", "o1")
    edges = (
        ("d0", "d1"),
        ("d0", "c1"),
        ("d0", "o0"),
        ("d1", "d2"),
        ("d1", "o1"),
        ("c0", "c1"),
        ("c0", "d2"),
        ("c0", "o1"),
        ("c1", "o1"),
        ("d2", "o0"),
    )
    weights = {"d0": 2, "d1": 2, "c0": 1, "c1": 1, "d2": 2, "o0": 1, "o1": 1}
    adjacency = {name: set() for name in vertices}
    for left, right in edges:
        adjacency[left].add(right)
        adjacency[right].add(left)
    width = 1
    lambda_value = 4
    for name in order:
        neighbors = set(adjacency[name])
        width = max(width, len(neighbors))
        lambda_value = max(lambda_value, weights[name] + sum(weights[x] for x in neighbors))
        for left, right in combinations(neighbors, 2):
            adjacency[left].add(right)
            adjacency[right].add(left)
        for neighbor in neighbors:
            adjacency[neighbor].remove(name)
        del adjacency[name]
    return width, lambda_value


def test_independent_120_order_oracle_confirms_counts_and_disjoint_optima() -> None:
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.tn import (
        frozen_tn_graph,
        run_retained_boundary_tn_owner,
    )

    internal = ("d0", "d1", "c0", "c1", "d2")
    observations = {order: _literal_replay(order) for order in permutations(internal)}
    best_width = min(value[0] for value in observations.values())
    best_lambda = min(value[1] for value in observations.values())
    width_orders = {order for order, value in observations.items() if value[0] == best_width}
    lambda_orders = {order for order, value in observations.items() if value[1] == best_lambda}

    assert best_width == 3
    assert best_lambda == 6
    assert len(width_orders) == 12
    assert len(lambda_orders) == 16
    assert width_orders.isdisjoint(lambda_orders)
    assert min(width_orders, key=lambda order: tuple(internal.index(x) for x in order)) == (
        "d1",
        "c0",
        "c1",
        "d0",
        "d2",
    )
    assert min(lambda_orders, key=lambda order: tuple(internal.index(x) for x in order)) == (
        "d0",
        "c1",
        "d2",
        "d1",
        "c0",
    )

    result = run_retained_boundary_tn_owner(frozen_tn_graph())
    assert result["unweighted"]["exact_value"] == best_width
    assert result["weighted"]["exact_value"] == best_lambda


def test_complete_subset_dp_tables_are_checked_lower_equality_proofs() -> None:
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.tn import (
        frozen_tn_graph,
        run_retained_boundary_tn_owner,
        verify_subset_dp_proof,
    )
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.model import (
        sha256_json,
    )

    graph = frozen_tn_graph()
    result = run_retained_boundary_tn_owner(graph)
    width_proof = result["unweighted"]["proof"]
    lambda_proof = result["weighted"]["proof"]
    assert width_proof["values"] == [
        1, 3, 3, 4, 3, 3, 3, 4, 3, 4, 3, 4, 3, 4, 3, 3,
        3, 3, 4, 4, 4, 4, 4, 4, 3, 4, 4, 4, 4, 4, 3, 3,
    ]
    assert lambda_proof["values"] == [
        4, 6, 7, 7, 5, 6, 7, 7, 5, 6, 7, 7, 6, 7, 7, 7,
        6, 6, 7, 6, 6, 6, 7, 6, 6, 6, 7, 6, 7, 6, 7, 6,
    ]
    assert len(width_proof["proof_sha256"]) == 64
    assert len(lambda_proof["proof_sha256"]) == 64
    verify_subset_dp_proof(graph, width_proof)
    verify_subset_dp_proof(graph, lambda_proof)

    corrupted = deepcopy(lambda_proof)
    corrupted["values"][2] = 6
    with pytest.raises(ValueError, match="recurrence"):
        verify_subset_dp_proof(graph, corrupted)

    for key, value, message in (
        ("floor", 999, "floor"),
        ("tie_break", "POST_HOC", "tie-break"),
    ):
        corrupted = deepcopy(lambda_proof)
        corrupted[key] = value
        body = {
            field: item
            for field, item in corrupted.items()
            if field != "proof_sha256"
        }
        corrupted["proof_sha256"] = sha256_json(body)
        with pytest.raises(ValueError, match=message):
            verify_subset_dp_proof(graph, corrupted)


def test_edge_domain_keep_and_boundary_corruptions_fail_or_change_the_metric() -> None:
    from dataclasses import replace

    import pytest

    from scripts.external_baselines.no_cutoff_minimal_exact_owners.tn import (
        Index,
        frozen_tn_graph,
        replay_order,
        run_retained_boundary_tn_owner,
        solve_exact_retained_boundary,
        verify_subset_dp_proof,
    )

    graph = frozen_tn_graph()
    original = run_retained_boundary_tn_owner(graph)

    for edge_name in ("d0-d1", "d1-d2"):
        without_edge = replace(
            graph,
            factors=tuple(
                factor for factor in graph.factors if factor.name != edge_name
            ),
        )
        changed_edge_result = solve_exact_retained_boundary(without_edge)
        assert changed_edge_result["weighted"]["exact_value"] == 5
        with pytest.raises(ValueError, match="graph identity"):
            verify_subset_dp_proof(without_edge, original["weighted"]["proof"])
        with pytest.raises(ValueError, match="frozen TN fixture"):
            run_retained_boundary_tn_owner(without_edge)

    changed_indices = tuple(
        Index("d1", "classical", 2) if index.name == "d1" else index
        for index in graph.indices
    )
    changed_domain = replace(graph, indices=changed_indices)
    assert solve_exact_retained_boundary(changed_domain)["weighted"]["exact_value"] == 5

    heavier_indices = tuple(
        Index("c0", "density", 4) if index.name == "c0" else index
        for index in graph.indices
    )
    heavier_domain = replace(graph, indices=heavier_indices)
    assert solve_exact_retained_boundary(heavier_domain)["weighted"]["exact_value"] == 7

    with pytest.raises(ValueError, match="KEEP factor"):
        replace(
            graph,
            factors=tuple(factor for factor in graph.factors if factor.name != "KEEP:o0"),
        )
    with pytest.raises(ValueError, match="permutation"):
        replay_order(graph, ("d0", "d1", "c0", "c1", "o0"))


def test_clamped_fixed_output_is_an_ineligible_two_five_diagnostic() -> None:
    internal = ("d0", "d1", "c0", "c1", "d2")
    edges = (
        ("d0", "d1"),
        ("d0", "c1"),
        ("d1", "d2"),
        ("c0", "c1"),
        ("c0", "d2"),
    )
    weights = {"d0": 2, "d1": 2, "c0": 1, "c1": 1, "d2": 2}

    def replay_fixed(order: tuple[str, ...]) -> tuple[int, int]:
        adjacency = {name: set() for name in internal}
        for left, right in edges:
            adjacency[left].add(right)
            adjacency[right].add(left)
        width, lambda_value = 1, 4
        for name in order:
            neighbors = set(adjacency[name])
            width = max(width, len(neighbors))
            lambda_value = max(
                lambda_value, weights[name] + sum(weights[x] for x in neighbors)
            )
            for left, right in combinations(neighbors, 2):
                adjacency[left].add(right)
                adjacency[right].add(left)
            for neighbor in neighbors:
                adjacency[neighbor].remove(name)
            del adjacency[name]
        return width, lambda_value

    observations = [replay_fixed(order) for order in permutations(internal)]
    assert min(value[0] for value in observations) == 2
    assert min(value[1] for value in observations) == 5


def test_tn_schema_rejects_unknown_invalid_and_incomplete_inputs() -> None:
    from dataclasses import replace

    from scripts.external_baselines.no_cutoff_minimal_exact_owners.tn import (
        Factor,
        Index,
        frozen_tn_graph,
        replay_order,
    )

    graph = frozen_tn_graph()
    with pytest.raises(ValueError, match="unknown index"):
        replace(
            graph,
            factors=graph.factors + (Factor("ghost-edge", "PAIR", ("d0", "ghost")),),
        )
    with pytest.raises(ValueError, match="domains|domain"):
        Index("bad-domain", "classical", 3)
    with pytest.raises(ValueError, match="density index"):
        Index("bad-density", "density", 2)
    with pytest.raises(ValueError, match="duplicates"):
        replace(graph, internal=("d0", "d0", "c0", "c1", "d2"))
    with pytest.raises(ValueError, match="permutation"):
        replay_order(graph, ("d0", "d1", "c0", "c1"))


def test_retained_boundary_tn_tracer_bullet_separates_both_exact_objectives() -> None:
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.tn import (
        frozen_tn_graph,
        run_retained_boundary_tn_owner,
    )

    result = run_retained_boundary_tn_owner(frozen_tn_graph())

    assert result["scope"] == "MICRO_QUALIFICATION_ONLY"
    assert result["terminal_record_representation"] == "factorized_boundary_factors"
    assert result["unweighted"]["exact_value"] == 3
    assert result["unweighted"]["order"] == ["d1", "c0", "c1", "d0", "d2"]
    assert result["unweighted"]["replay"]["lambda"] == 7
    assert result["weighted"]["exact_value"] == 6
    assert result["weighted"]["peak_dense_entries"] == 64
    assert result["weighted"]["order"] == ["d0", "c1", "d2", "d1", "c0"]
    assert result["weighted"]["replay"]["width"] == 4
    assert result["target_lowering"] == "UNAVAILABLE"
    assert result["solver_permission"] == "CODE_BLOCKED"
