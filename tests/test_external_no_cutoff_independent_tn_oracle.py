"""Independence and exactness contracts for the literal TN oracle."""

from __future__ import annotations

import ast
from copy import deepcopy
import inspect

import pytest


def test_independent_tn_oracle_has_no_owner_helper_import_or_call() -> None:
    import scripts.external_baselines.no_cutoff_minimal_exact_owners.independent_tn_oracle as oracle

    source = inspect.getsource(oracle)
    tree = ast.parse(source)
    imports = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    assert all(
        not isinstance(node, ast.ImportFrom) or node.level == 0
        for node in imports
    )
    for forbidden in (
        "no_cutoff_minimal_exact_owners.model",
        "no_cutoff_minimal_exact_owners.tn",
        "frozen_tn_graph",
        "run_retained_boundary_tn_owner",
        "verify_subset_dp_proof",
    ):
        assert forbidden not in source


def test_literal_oracle_freezes_all_optima_and_complete_dp_tables() -> None:
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.independent_tn_oracle import (
        run_independent_tn_oracle,
    )

    result = run_independent_tn_oracle()

    assert result["scope"] == "MICRO_QUALIFICATION_ONLY"
    assert result["solver_permission"] == "CODE_BLOCKED"
    assert result["target_lowering"] == "UNAVAILABLE"
    assert result["exhaustive"]["order_count"] == 120
    assert result["exhaustive"]["unweighted"]["exact_value"] == 3
    assert result["exhaustive"]["unweighted"]["optimum_count"] == 12
    assert result["exhaustive"]["unweighted"]["selected_order"] == [
        "d1", "c0", "c1", "d0", "d2",
    ]
    assert result["exhaustive"]["weighted"]["exact_value"] == 6
    assert result["exhaustive"]["weighted"]["peak_dense_entries"] == 64
    assert result["exhaustive"]["weighted"]["optimum_count"] == 16
    assert result["exhaustive"]["weighted"]["selected_order"] == [
        "d0", "c1", "d2", "d1", "c0",
    ]
    assert result["exhaustive"]["optimum_sets_disjoint"] is True

    width = result["subset_dp"]["unweighted"]
    weighted = result["subset_dp"]["weighted"]
    assert width["values"] == [
        1, 3, 3, 4, 3, 3, 3, 4, 3, 4, 3, 4, 3, 4, 3, 3,
        3, 3, 4, 4, 4, 4, 4, 4, 3, 4, 4, 4, 4, 4, 3, 3,
    ]
    assert weighted["values"] == [
        4, 6, 7, 7, 5, 6, 7, 7, 5, 6, 7, 7, 6, 7, 7, 7,
        6, 6, 7, 6, 6, 6, 7, 6, 6, 6, 7, 6, 7, 6, 7, 6,
    ]
    for proof in (width, weighted):
        assert len(proof["values"]) == 32
        assert len(proof["orders"]) == 32
        assert len(proof["values_sha256"]) == 64
        assert len(proof["orders_sha256"]) == 64
        assert len(proof["proof_sha256"]) == 64
    assert result["graph_sha256"] == (
        "6fca6b20dd9d4503f8212168fb30df4f474715fbf5674a53dc4f7c650dc1e0a7"
    )
    assert (width["values_sha256"], width["orders_sha256"], width["proof_sha256"]) == (
        "1b3ac8200d48cd61e9924605ab2af318158acd9ba21f097c7a5e29dbe1ca10cf",
        "2082a6474c9b94114de30d9efb145dcdc1d16720bb68ba161acfcb165162447f",
        "aed84adfb5caa08a7bffc68ede4e9d30a07b6be09292c6d1083cc26d7b91b746",
    )
    assert (
        weighted["values_sha256"],
        weighted["orders_sha256"],
        weighted["proof_sha256"],
    ) == (
        "bbe463e4926c5e43fda42907a3daff5be3513fe5e17497b28c05fc42d9b1cbbd",
        "b3460a5ba3e6a69e3e534137e7be3a1857074984c3f4c378e18ba3e6d0ee0b92",
        "a6b5edb358a4d084250881bdcc221de89fb30814d3c106fb3f954db1c6403d86",
    )


def test_independent_verifier_accepts_owner_proofs_at_test_boundary() -> None:
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.independent_tn_oracle import (
        run_independent_tn_oracle,
        verify_frozen_subset_proof,
    )
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.tn import (
        frozen_tn_graph,
        run_retained_boundary_tn_owner,
    )

    independent = run_independent_tn_oracle()
    owner = run_retained_boundary_tn_owner(frozen_tn_graph())

    assert independent["graph_sha256"] == owner["factor_graph_sha256"]
    for objective, owner_key, oracle_key in (
        ("width", "unweighted", "unweighted"),
        ("lambda", "weighted", "weighted"),
    ):
        proof = owner[owner_key]["proof"]
        verify_frozen_subset_proof(proof)
        oracle_proof = independent["subset_dp"][oracle_key]
        assert proof["objective"] == objective
        assert proof["values"] == oracle_proof["values"]
        assert proof["orders"] == oracle_proof["orders"]
        assert proof["proof_sha256"] == oracle_proof["proof_sha256"]

    corrupted = deepcopy(owner["weighted"]["proof"])
    corrupted["values"][2] = 6
    with pytest.raises(ValueError, match="recurrence"):
        verify_frozen_subset_proof(corrupted)


def test_literal_corruptions_are_metric_sensitive_and_fixed_output_is_ineligible() -> None:
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.independent_tn_oracle import (
        run_independent_tn_oracle,
    )

    corruptions = run_independent_tn_oracle()["corruption_checks"]
    assert corruptions["remove_edge_d0_d1"]["weighted_exact_value"] == 5
    assert corruptions["remove_edge_d1_d2"]["weighted_exact_value"] == 5
    assert corruptions["change_d1_log2_domain_2_to_1"]["weighted_exact_value"] == 5
    assert corruptions["change_c0_log2_domain_1_to_2"]["weighted_exact_value"] == 7
    assert corruptions["clamp_record_boundary_ineligible"] == {
        "classification": "INELIGIBLE_FIXED_OUTPUT_DIAGNOSTIC",
        "unweighted_exact_value": 2,
        "weighted_exact_value": 5,
    }
