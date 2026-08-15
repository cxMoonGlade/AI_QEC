"""No-cutoff structure-census contracts and exact-small falsifiers.

This file protects a bounded research instrument. It does not certify the
d=3/5 complete Record law and cannot authorize a solver.
"""

from __future__ import annotations

import ast
from copy import deepcopy
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import sys

import pytest
from sympy import Rational


REPO = Path(__file__).resolve().parents[1]
BASELINES = REPO / "scripts" / "external_baselines"
CENSUS_PATH = BASELINES / "no_cutoff_structure_census.py"
ORACLE_PATH = BASELINES / "no_cutoff_structure_census_exact_oracle.py"
PREREG_PATH = (
    REPO
    / "docs"
    / "simulator_validation"
    / "NO_CUTOFF_STRUCTURE_CENSUS_PREREG_2026-08-03.md"
)
FIXTURE_MANIFEST_PATH = (
    REPO
    / "docs"
    / "simulator_validation"
    / "NO_CUTOFF_STRUCTURE_CENSUS_FIXTURE_MANIFEST_2026-08-03.json"
)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _census():
    return _load(CENSUS_PATH, "no_cutoff_structure_census_under_test")


def _oracle():
    return _load(ORACLE_PATH, "no_cutoff_structure_oracle_under_test")


def _leaf(value: int) -> dict[str, object]:
    return {
        "status": "EXACT",
        "value": value,
        "identity": {"metric": "test_burden", "route": "unit"},
    }


def _interval(lower: int, upper: int) -> dict[str, object]:
    return {
        "status": "CERTIFIED_INTERVAL",
        "lower": lower,
        "upper": upper,
        "derivation_sha256": "a" * 64,
        "identity": {"metric": "test_burden", "route": "unit"},
    }


def _observed_clifft_leaf(census, *, k_max: int) -> dict[str, object]:
    history = [0] if k_max == 0 else [0, k_max]
    pass_manifest = {
        "bytecode_passes": None,
        "hir_passes": ["StatevectorSqueezePass"],
        "normalize_syndromes": False,
    }
    deterministic = {
        "active_k_history": history,
        "num_instructions": len(history),
        "pass_manifest": pass_manifest,
        "peak_rank": k_max,
    }
    inert_deterministic = {
        "active_k_history": [0],
        "num_instructions": 1,
        "pass_manifest": pass_manifest,
        "peak_rank": 0,
    }
    return {
        "status": "EXACT",
        "value": k_max,
        "burden": 2**k_max,
        "active_k_history": history,
        "controls": {
            "inert": {
                "active_k_history": [0],
                "circuit_sha256": "a" * 64,
                "k_max": 0,
                "num_instructions": 1,
                "pass_manifest": pass_manifest,
                "stdout_sha256": "b" * 64,
                "structural_output_sha256": census.sha256_bytes(
                    census.canonical_json_bytes(inert_deterministic)
                ),
            },
            "nonzero_primary_sign_tiny_invariance": "PASS",
        },
        "identity": {
            "active_k_history_sha256": census.sha256_bytes(
                census.canonical_json_bytes(history)
            ),
            "circuit_sha256": {
                shadow: "d" * 64 for shadow in census.NONZERO_SHADOWS
            },
            "extension_sha256": "e" * 64,
            "metric": "k_max_clifft_squeeze_no_peephole",
            "num_instructions": len(history),
            "pass_manifest": pass_manifest,
            "python_version": "3.12.13",
            "route": "clifft_frame",
            "structural_output_sha256": census.sha256_bytes(
                census.canonical_json_bytes(deterministic)
            ),
            "variant_stdout_sha256": {
                shadow: "f" * 64 for shadow in census.NONZERO_SHADOWS
            },
            "variant_structural_output_sha256": {
                shadow: census.sha256_bytes(
                    census.canonical_json_bytes(deterministic)
                )
                for shadow in census.NONZERO_SHADOWS
            },
            "version": "test",
        },
    }


def _observed_symft_leaf(census, *, k_max: int) -> dict[str, object]:
    deterministic = {
        "estimated_component_vector_work": "0",
        "estimated_dense_vector_work": "0",
        "structure": {
            "dense_peak_dimension": 2**k_max,
            "max_active_qubits": k_max,
        },
    }
    inert_deterministic = {
        "estimated_component_vector_work": "0",
        "estimated_dense_vector_work": "0",
        "structure": {
            "dense_peak_dimension": 1,
            "max_active_qubits": 0,
        },
    }
    return {
        "status": "EXACT",
        "value": k_max,
        "b_frame_symft_monolithic": 2**k_max,
        "controls": {
            "inert": {
                "circuit_sha256": "1" * 64,
                "deterministic_structure": inert_deterministic,
                "stdout_sha256": "2" * 64,
                "structural_output_sha256": census.sha256_bytes(
                    census.canonical_json_bytes(inert_deterministic)
                ),
            },
            "nonzero_primary_sign_tiny_invariance": "PASS",
        },
        "deterministic_structure": deterministic,
        "headline_eligible": False,
        "identity": {
            "circuit_sha256": {
                shadow: "4" * 64 for shadow in census.NONZERO_SHADOWS
            },
            "executable_sha256": "5" * 64,
            "metric": "k_max_symft",
            "route": "symft_diagnostic",
            "structural_output_sha256": census.sha256_bytes(
                census.canonical_json_bytes(deterministic)
            ),
            "variant_stdout_sha256": {
                shadow: "6" * 64 for shadow in census.NONZERO_SHADOWS
            },
            "variant_structural_output_sha256": {
                shadow: census.sha256_bytes(
                    census.canonical_json_bytes(deterministic)
                )
                for shadow in census.NONZERO_SHADOWS
            },
        },
    }


def _external_sources(census) -> dict[str, object]:
    return {
        "clifft": {
            "anchor_sha256": {
                path: "7" * 64 for path in census._CLIFFT_SOURCE_ANCHORS
            },
            "build_dependency_lock_attested": False,
            "commit": census.CLIFFT_COMMIT,
            "pristine": True,
            "python_executable_sha256": "8" * 64,
            "tree": census.CLIFFT_TREE,
        },
        "symft": {
            "anchor_sha256": {
                path: "9" * 64 for path in census._SYMFT_SOURCE_ANCHORS
            },
            "build_dependency_lock_attested": False,
            "commit": census.SYMFT_COMMIT,
            "planner_executable_sha256": "a" * 64,
            "pristine": True,
            "tree": census.SYMFT_TREE,
        },
    }


def test_preregistration_is_active_but_solver_remains_blocked() -> None:
    text = PREREG_PATH.read_text(encoding="utf-8")
    assert "ACTIVE PRE-REGISTRATION, CODE_BLOCKED" in text
    assert "new solver work remains" in text
    assert "KILL_STRUCTURE" in text
    assert "certification_verdict = PASS | FAIL | UNANCHORED" in text


def test_exact_oracle_is_implementation_independent() -> None:
    tree = ast.parse(ORACLE_PATH.read_text(encoding="utf-8"))
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports.update(
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    )
    assert not any(name.startswith("error_coupling_simulator") for name in imports)
    assert "numpy" not in imports


def test_pythagorean_pair_and_closed_law_match_independent_sympy_matrices() -> None:
    oracle = _oracle()
    c, s = oracle.pythagorean_pair(Rational(1, 100))
    assert (c, s) == (Rational(9999, 10001), Rational(200, 10001))
    assert c**2 + s**2 == 1

    for rounds in range(1, 6):
        closed = oracle.persistent_record_law(rounds, c, s)
        matrix = oracle.matrix_branch_record_law(rounds, c, s)
        assert closed == matrix
        assert sum(closed.values(), Rational(0)) == 1
        assert len(closed) == 2 ** (rounds + 1)


def test_persistence_falsifier_has_matched_one_round_and_exact_two_round_tv() -> None:
    oracle = _oracle()
    c, s = oracle.pythagorean_pair(Rational(1, 100))
    persistent_1 = oracle.persistent_record_law(1, c, s)
    iid_1 = oracle.iid_sign_record_law(1, c, s)
    assert persistent_1 == iid_1

    persistent_2 = oracle.persistent_record_law(2, c, s)
    iid_2 = oracle.iid_sign_record_law(2, c, s)
    delta = 2 * c * s
    assert oracle.total_variation_exact(persistent_2, iid_2) == delta**2 / 2
    assert oracle.total_variation_exact(persistent_2, iid_2) > 0

    for record, probability in persistent_2.items():
        detectors, observable = record[:-1], record[-1]
        if observable != sum(detectors) % 2:
            assert probability == 0


def test_tracer_inert_law_is_uniform_on_valid_records_not_all_zero() -> None:
    oracle = _oracle()
    c, s = oracle.pythagorean_pair(Rational(0))
    persistent = oracle.persistent_record_law(4, c, s)
    iid = oracle.iid_sign_record_law(4, c, s)
    assert persistent == iid
    for record, probability in persistent.items():
        detectors, observable = record[:-1], record[-1]
        expected = Rational(1, 16) if observable == sum(detectors) % 2 else 0
        assert probability == expected


def test_frozen_sub_1e12_tail_is_positive_and_wrong_observable_is_exact_zero() -> None:
    oracle = _oracle()
    tail = oracle.frozen_tail_fixture()
    expected = Rational(
        7984925229121,
        64063097262168921289605376,
    )
    assert tail["t"] == Rational(3, 7)
    assert tail["c"] == Rational(20, 29)
    assert tail["s"] == Rational(21, 29)
    assert tail["rounds"] == 8
    assert tail["detectors"] == (1, 1, 1, 1, 0, 0, 0, 0)
    assert tail["observable"] == 0
    assert tail["probability"] == expected
    assert 0 < expected < Rational(1, 10**12)
    assert tail["wrong_observable_probability"] == 0


def test_final_record_mtbdd_is_exact_but_explicitly_not_dynamic_ndd() -> None:
    oracle = _oracle()
    c, s = oracle.pythagorean_pair(Rational(3, 7))
    law = oracle.persistent_record_law(8, c, s)
    diagram = oracle.build_record_pmf_mtbdd(law)
    assert diagram["metric_name"] == "n_record_pmf_mtbdd_nodes_final"
    assert diagram["headline_eligible"] is False
    assert diagram["represented_object"] == "final_complete_record_pmf"
    assert diagram["node_count"] == (
        diagram["internal_node_count"] + diagram["terminal_node_count"]
    )
    assert oracle.reconstruct_record_pmf_mtbdd(diagram) == law

    exact_tail = Rational(
        7984925229121,
        64063097262168921289605376,
    )
    assert oracle.rational_bytes(exact_tail) in diagram["terminal_values"]

    truncated = {
        record: (Rational(0) if 0 < value < Rational(1, 10**12) else value)
        for record, value in law.items()
    }
    assert sum(truncated.values(), Rational(0)) < 1
    with pytest.raises(ValueError, match="normalized"):
        oracle.build_record_pmf_mtbdd(truncated)


def test_binary64_shadow_serialization_is_frozen_and_rounding_checked() -> None:
    census = _census()
    observed = census.verify_angle_serializations()
    assert observed["primary"]["positive_decimal"] == "0.012731971059633021"
    assert observed["primary"]["positive_hex"] == "0x1.a13383a84979bp-7"
    assert (
        observed["nonzero_invariance"]["positive_decimal"]
        == "1.2732395447351627e-20"
    )
    assert (
        observed["nonzero_invariance"]["positive_hex"]
        == "0x1.e1042c3d96d7fp-67"
    )
    assert observed["inert"]["positive_decimal"] == "0"
    assert observed["inert"]["negative_decimal"] == "0"
    assert observed["inert"]["positive_hex"] == "0x0.0p+0"
    assert all(row["strictly_inside_rounding_cell"] for row in observed.values())


def test_stim_fixture_manifest_and_every_shadow_hash_reproduce() -> None:
    census = _census()
    frozen = json.loads(FIXTURE_MANIFEST_PATH.read_text(encoding="utf-8"))
    observed = census.build_fixture_manifest()
    assert census.canonical_json_bytes(observed) == census.canonical_json_bytes(frozen)
    assert census.sha256_bytes(census.canonical_json_bytes(observed)) == (
        "40474ca0beab8341d53bfa41da5438e052744bb83ae6af2632e1bfe273c53c74"
    )
    assert [(row["distance"], row["rounds"]) for row in observed["cells"]] == [
        (3, 1),
        (3, 3),
        (3, 5),
        (3, 7),
        (5, 1),
        (5, 3),
        (5, 5),
        (5, 7),
    ]


def test_shadow_bundle_has_no_stochastic_channel_and_zero_is_algebraic() -> None:
    census = _census()
    bundle = census.build_shadow_bundle(distance=3, rounds=3)
    assert "DEPOLARIZE" in bundle["source_text"]
    for name in ("primary_plus", "primary_minus", "tiny_plus", "tiny_minus"):
        text = bundle["shadows"][name]["text"]
        assert "R_Z(" in text
        assert not census.contains_stochastic_channel(text)
    inert = bundle["shadows"]["inert"]["text"]
    assert "R_Z(" not in inert
    assert "DEPOLARIZE" not in inert
    assert "-0" not in inert
    signatures = {
        census.structural_shadow_signature(bundle["shadows"][name]["text"])
        for name in ("primary_plus", "primary_minus", "tiny_plus", "tiny_minus")
    }
    assert len(signatures) == 1
    assert bundle["identity"]["replacement_rows"] == len(bundle["site_map"])
    assert all(
        set(row) == {"instruction_index", "source_args", "source_gate", "targets"}
        for row in bundle["site_map"]
    )


def test_growth_gate_uses_exact_burdens_and_all_three_transitions() -> None:
    census = _census()
    killed = census.adjudicate_burden_series(
        {1: _leaf(1), 3: _leaf(2), 5: _leaf(4), 7: _leaf(8)}
    )
    assert killed["structure_disposition"] == "KILL_STRUCTURE"
    assert killed["first_proved_doubling_transition"] == "1->3"

    not_killed = census.adjudicate_burden_series(
        {1: _leaf(1), 3: _leaf(2), 5: _leaf(3), 7: _leaf(8)}
    )
    assert (
        not_killed["structure_disposition"]
        == "NOT_KILLED_ON_FROZEN_GRID"
    )

    overlap = census.adjudicate_burden_series(
        {
            1: _interval(1, 2),
            3: _interval(2, 4),
            5: _interval(4, 8),
            7: _interval(8, 16),
        }
    )
    assert overlap["structure_disposition"] == "INDETERMINATE"

    missing = census.adjudicate_burden_series(
        {
            1: _leaf(1),
            3: _leaf(2),
            5: census.unavailable_metric(
                "NO_EXACT_PAIR_OWNER",
                metric="n_pauli_pair_states_peak",
                route="exact_pair",
            ),
            7: _leaf(8),
        }
    )
    assert missing["structure_disposition"] == "INDETERMINATE"


def test_symft_parser_drops_telemetry_and_qualifies_component_early_return() -> None:
    census = _census()
    raw = """\
qubits 7
records 11
detectors 5
instructions 19
max_active_qubits 7
active_components dense_fallback
component_count 0
dense_peak_dimension 128
component_peak_live_dimension 0
component_allocated_dimension 0
pending_operations_before 11
pending_operations_after 7
fused_rotations 4
cancelled_rotations 0
measurement_left_swaps 3
estimated_dense_vector_work 0
estimated_component_vector_work 0
parse_seconds 0.125
plan_seconds 0.5
peak_rss_kib 1234
"""
    parsed = census.parse_symft_plan_output(raw)
    normalized = census.normalized_symft_structure(parsed)
    assert normalized["max_active_qubits"] == 7
    assert normalized["dense_peak_dimension"] == 128
    assert normalized["active_components"] == "not_constructed"
    assert normalized["component_plan_status"] == "NOT_CONSTRUCTED_K_LT_8"
    assert "parse_seconds" not in normalized
    assert "plan_seconds" not in normalized
    assert "peak_rss_kib" not in normalized
    assert "estimated_dense_vector_work" not in normalized


def test_symft_parser_accepts_source_dense_fallback_spelling() -> None:
    census = _census()
    raw = """\
qubits 17
records 24
detectors 8
instructions 91
max_active_qubits 9
active_components dense_fallback
component_count 3
dense_peak_dimension 512
component_peak_live_dimension 64
component_allocated_dimension 96
estimated_dense_vector_work 4096
estimated_component_vector_work 1024
pending_operations_before 31
pending_operations_after 17
fused_rotations 14
cancelled_rotations 0
measurement_left_swaps 6
parse_seconds 0.125
plan_seconds 0.5
peak_rss_kib 1234
"""
    parsed = census.parse_symft_plan_output(raw)
    normalized = census.normalized_symft_structure(parsed)
    assert normalized["active_components"] == "dense_fallback"
    assert normalized["component_plan_status"] == "NOT_SELECTED"
    assert normalized["dense_peak_dimension"] == 512


def test_clifft_worker_parser_requires_squeeze_only_no_peephole_route() -> None:
    census = _census()
    payload = {
        "_schema": census.CLIFFT_WORKER_SCHEMA,
        "active_k_history": [0, 1, 3, 2],
        "extension_sha256": "b" * 64,
        "num_instructions": 4,
        "pass_manifest": {
            "bytecode_passes": None,
            "hir_passes": ["StatevectorSqueezePass"],
            "normalize_syndromes": False,
        },
        "peak_rank": 3,
        "python_version": "3.12.13",
        "version": "test",
    }
    parsed = census.parse_clifft_worker_output(census.canonical_json_bytes(payload))
    assert parsed["k_max_clifft_squeeze_no_peephole"] == 3
    assert parsed["burden"] == 8

    contaminated = deepcopy(payload)
    contaminated["pass_manifest"]["hir_passes"].append("PeepholeFusionPass")
    with pytest.raises(ValueError, match="Peephole"):
        census.parse_clifft_worker_output(
            census.canonical_json_bytes(contaminated)
        )


def test_fail_closed_report_has_all_cells_metrics_and_binding_verdict() -> None:
    census = _census()
    report = census.build_fail_closed_report()
    census.validate_report(report)
    assert report["_schema"] == (
        "error_coupling_simulator.external.no_cutoff_structure_census.v1"
    )
    assert report["faithfulness_disposition"] == "UNAVAILABLE"
    assert report["certification_verdict"] == "UNANCHORED"
    assert report["solver_permission"] == "CODE_BLOCKED"
    assert set(report["structure_dispositions"]) == {
        "clifft_frame",
        "exact_pair",
        "dynamic_add",
        "retained_boundary_tn",
    }
    assert len(report["cells"]) == 8
    assert [(row["distance"], row["rounds"]) for row in report["cells"]] == [
        (3, 1),
        (3, 3),
        (3, 5),
        (3, 7),
        (5, 1),
        (5, 3),
        (5, 5),
        (5, 7),
    ]
    for cell in report["cells"]:
        metrics = cell["metrics"]
        assert set(metrics) == {"k_max", "n_pair", "n_dd", "tw", "delta_tv_cert"}
        assert metrics["n_pair"]["reason"] == "NO_EXACT_PAIR_OWNER"
        assert metrics["n_dd"]["reason"] == "NO_EXACT_DYNAMIC_ADD_OWNER"
        assert (
            metrics["tw"]["record_boundary_constrained_induced_width"]["reason"]
            == "NO_CANONICAL_RETAINED_RECORD_TN_OWNER"
        )
        assert metrics["delta_tv_cert"]["reason"] == "UNANCHORED_FULL_RECORD"
        for leaf in census.iter_metric_leaves(metrics):
            if leaf["status"] in {"UNAVAILABLE", "CENSORED_RESOURCE"}:
                assert not ({"value", "lower", "upper", "estimate"} & set(leaf))


def test_observed_k_report_adjudicates_clifft_burden_but_never_symft() -> None:
    census = _census()
    clifft_k = {
        (3, 1): 1,
        (3, 3): 2,
        (3, 5): 2,
        (3, 7): 2,
        (5, 1): 1,
        (5, 3): 2,
        (5, 5): 3,
        (5, 7): 4,
    }
    # Deliberately explosive: SymFT still has no route-disposition key.
    symft_k = {cell: index for index, cell in enumerate(census.GRID, start=1)}
    clifft = {
        cell: _observed_clifft_leaf(census, k_max=value)
        for cell, value in clifft_k.items()
    }
    symft = {
        cell: _observed_symft_leaf(census, k_max=value)
        for cell, value in symft_k.items()
    }
    report = census.assemble_structure_census_report(
        clifft_observations=clifft,
        symft_observations=symft,
        external_sources=_external_sources(census),
    )
    census.validate_report(report)
    frame = report["structure_dispositions"]["clifft_frame"]
    assert frame["distance_3"]["structure_disposition"] == (
        "NOT_KILLED_ON_FROZEN_GRID"
    )
    assert frame["distance_5"]["structure_disposition"] == "KILL_STRUCTURE"
    assert frame["aggregate"]["structure_disposition"] == "KILL_STRUCTURE"
    assert set(report["structure_dispositions"]) == set(census.ROUTE_KEYS)
    assert "symft" not in report["structure_dispositions"]
    assert report["faithfulness_disposition"] == "UNAVAILABLE"
    assert report["certification_verdict"] == "UNANCHORED"
    assert report["solver_permission"] == "CODE_BLOCKED"


def test_observed_k_report_requires_exactly_the_frozen_grid() -> None:
    census = _census()
    observations = {
        cell: _observed_clifft_leaf(census, k_max=1)
        for cell in census.GRID
    }
    observations.pop((5, 7))
    with pytest.raises(ValueError, match="frozen grid"):
        census.assemble_structure_census_report(
            clifft_observations=observations,
            symft_observations={},
            external_sources={},
        )


def test_observed_report_rejects_a_burden_inconsistent_with_k() -> None:
    census = _census()
    clifft = {
        cell: _observed_clifft_leaf(census, k_max=1) for cell in census.GRID
    }
    symft = {
        cell: _observed_symft_leaf(census, k_max=1) for cell in census.GRID
    }
    report = census.assemble_structure_census_report(
        clifft_observations=clifft,
        symft_observations=symft,
        external_sources=_external_sources(census),
    )
    report["cells"][0]["metrics"]["k_max"]["clifft"]["burden"] = 3
    with pytest.raises(ValueError, match="burden"):
        census.validate_report(report)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("history", "history length"),
        ("variant_invariance", "invariance"),
        ("metric_identity", "metric identity"),
        ("source_tree", "source identity"),
        ("symft_promotion", "headline"),
        ("disposition", "recomputable"),
    ],
)
def test_observed_report_rejects_provenance_and_join_mutations(
    mutation: str,
    message: str,
) -> None:
    census = _census()
    clifft = {
        cell: _observed_clifft_leaf(census, k_max=1) for cell in census.GRID
    }
    symft = {
        cell: _observed_symft_leaf(census, k_max=1) for cell in census.GRID
    }
    report = census.assemble_structure_census_report(
        clifft_observations=clifft,
        symft_observations=symft,
        external_sources=_external_sources(census),
    )
    first = report["cells"][0]["metrics"]["k_max"]
    if mutation == "history":
        first["clifft"]["identity"]["num_instructions"] += 1
    elif mutation == "variant_invariance":
        first["clifft"]["identity"]["variant_structural_output_sha256"][
            "tiny_minus"
        ] = "0" * 64
    elif mutation == "metric_identity":
        first["clifft"]["identity"]["metric"] = "k_max"
    elif mutation == "source_tree":
        report["external_sources"]["clifft"]["tree"] = "0" * 40
    elif mutation == "symft_promotion":
        first["symft"]["headline_eligible"] = True
    elif mutation == "disposition":
        report["structure_dispositions"]["clifft_frame"]["aggregate"][
            "structure_disposition"
        ] = "KILL_STRUCTURE"
    else:  # pragma: no cover
        raise AssertionError(mutation)
    with pytest.raises(ValueError, match=message):
        census.validate_report(report)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("numeric_unavailable", "numeric"),
        ("latent_truth", "evaluator"),
        ("raw_recursion_proxy", "probability_node_count"),
        ("final_mtbdd_promoted", "dynamic ADD"),
        ("wrong_grid_order", "canonical grid"),
    ],
)
def test_report_validator_rejects_missing_truth_and_proxy_mutations(
    mutation: str,
    message: str,
) -> None:
    census = _census()
    report = census.build_fail_closed_report()
    if mutation == "numeric_unavailable":
        report["cells"][0]["metrics"]["n_pair"]["value"] = 0
    elif mutation == "latent_truth":
        report["cells"][0]["latent_sign"] = 1
    elif mutation == "raw_recursion_proxy":
        report["cells"][0]["metrics"]["n_dd"]["probability_node_count"] = 17
    elif mutation == "final_mtbdd_promoted":
        report["cells"][0]["metrics"]["n_dd"] = {
            "status": "EXACT",
            "value": 7,
            "identity": {
                "metric": "n_record_pmf_mtbdd_nodes_final",
                "route": "output_projection",
            },
        }
    elif mutation == "wrong_grid_order":
        report["cells"][0], report["cells"][1] = (
            report["cells"][1],
            report["cells"][0],
        )
    else:  # pragma: no cover
        raise AssertionError(mutation)
    with pytest.raises(ValueError, match=message):
        census.validate_report(report)


def test_report_canonical_json_refuses_nonfinite_values() -> None:
    census = _census()
    with pytest.raises(ValueError):
        census.canonical_json_bytes({"bad": float("nan")})


def test_fraction_inputs_are_not_silently_coerced_to_float() -> None:
    oracle = _oracle()
    with pytest.raises(TypeError, match="SymPy Rational"):
        oracle.pythagorean_pair(Fraction(1, 100))
