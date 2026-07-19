"""Behavioral contract for the MPS-016 three-leg comparator."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import pytest


SCRIPT = Path(__file__).parents[1] / "scripts" / "mps_three_leg_comparator.py"
SPEC = importlib.util.spec_from_file_location("mps_three_leg_comparator", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
COMPARATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(COMPARATOR)


def _complex_array(payload: dict) -> np.ndarray:
    real = np.asarray(payload["real"], dtype=np.float64)
    imag = np.asarray(payload["imag"], dtype=np.float64)
    return (real + 1j * imag).reshape(payload["shape"])


def _fidelity(reference: np.ndarray, candidate: np.ndarray) -> float:
    reference = np.asarray(reference, dtype=np.complex128).reshape(-1)
    candidate = np.asarray(candidate, dtype=np.complex128).reshape(-1)
    reference = reference / np.linalg.norm(reference)
    candidate = candidate / np.linalg.norm(candidate)
    return float(abs(np.vdot(reference, candidate)) ** 2)


def test_fixture_manifest_freezes_nondegenerate_ordered_support_cases() -> None:
    manifest = COMPARATOR.build_fixture_manifest()

    assert manifest["schema"] == COMPARATOR.FIXTURE_SCHEMA
    assert manifest["dtype"] == "complex128"
    assert manifest["qubit_order"] == "site_0_most_significant_big_endian"
    assert manifest["fixture_count"] == 6
    assert {
        (tuple(case["support"]), case["max_bond"])
        for case in manifest["fixtures"]
    } == {
        ((0, 4), 1),
        ((0, 4), 2),
        ((0, 4), 4),
        ((4, 0), 1),
        ((4, 0), 2),
        ((4, 0), 4),
    }

    expected_active_factor = np.asarray(
        [math.sqrt(3.0) / 2.0, 0.5j],
        dtype=np.complex128,
    )
    expected_cnot = np.asarray(
        [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]],
        dtype=np.complex128,
    )
    expected_sites = [[3, 4], [2, 3], [1, 2], [0, 1], [1, 2], [2, 3], [3, 4]]
    expected_roles = [
        "forward_swap_split",
        "forward_swap_split",
        "forward_swap_split",
        "two_site_operator_split",
        "reverse_swap_split",
        "reverse_swap_split",
        "reverse_swap_split",
    ]

    for case in manifest["fixtures"]:
        support = tuple(case["support"])
        factors = [_complex_array(value) for value in case["initial_product_factors"]]
        np.testing.assert_allclose(
            factors[support[0]],
            expected_active_factor,
            atol=0.0,
            rtol=0.0,
        )
        for site, factor in enumerate(factors):
            if site != support[0]:
                np.testing.assert_array_equal(factor, [1.0, 0.0])
        np.testing.assert_array_equal(
            _complex_array(case["two_site_operator"]),
            expected_cnot,
        )
        assert case["cutoff"] == 0.0
        assert case["cutoff_mode"] == "rsum2"
        assert case["renorm"] is None
        assert case["expected_split_path"]["split_sites"] == expected_sites
        assert case["expected_split_path"]["roles"] == expected_roles
        assert case["expected_split_path"]["operator_gate_leg_sites"] == (
            [0, 1] if support == (0, 4) else [1, 0]
        )

    assert manifest["content_hash_sha256"] == COMPARATOR.canonical_hash(
        manifest,
        hash_field="content_hash_sha256",
    )


def test_dense_leg_is_ordered_svd_oracle_and_detects_corruptions() -> None:
    fixtures = COMPARATOR.build_fixture_manifest()
    result = COMPARATOR.run_dense_leg(fixtures)

    assert result["schema"] == COMPARATOR.LEG_RESULT_SCHEMA
    assert result["leg"] == "dense_numpy"
    assert result["fixture_manifest_sha256"] == fixtures["content_hash_sha256"]
    assert result["case_count"] == 6
    assert result["claim_boundary"] == {
        "state_math_oracle": True,
        "actual_split_ledger_oracle": False,
        "dense_cut_tail_is_actual_split_ledger": False,
        "production_error_bound": False,
        "record_faithfulness": False,
    }

    for case in result["cases"]:
        assert case["dense_reference"]["raw_norm_sq"] == pytest.approx(
            1.0, abs=1.0e-15
        )
        assert case["dense_reference"]["numerical_schmidt_rank"] == 2
        records = case["dense_reference"]["schmidt_records"]
        assert [record["cut_index"] for record in records] == [1, 2, 3, 4]
        expected_tail = 0.25 if case["max_bond"] == 1 else 0.0
        assert [
            record["discarded_weight_at_cap"] for record in records
        ] == pytest.approx(
            [expected_tail] * 4,
            abs=1.0e-15,
        )
        assert case["dense_reference"][
            "best_rank_cap_fidelity"
        ] == pytest.approx(
            0.75 if case["max_bond"] == 1 else 1.0,
            abs=1.0e-15,
        )

    falsifiers = result["corruption_falsifiers"]
    assert falsifiers["reversed_support_sorted_fidelity"] == pytest.approx(
        0.5625, abs=1.0e-15
    )
    assert falsifiers["relative_phase_sign_fidelity"] == pytest.approx(
        0.25, abs=1.0e-15
    )
    assert falsifiers["global_phase_fidelity"] == pytest.approx(
        1.0, abs=1.0e-15
    )
    assert falsifiers["global_phase_aligned_l2"] == pytest.approx(
        0.0, abs=1.0e-15
    )
    assert falsifiers["all_required_corruptions_detected"] is True
    assert result["content_hash_sha256"] == COMPARATOR.canonical_hash(
        result,
        hash_field="content_hash_sha256",
    )


def test_three_leg_report_atomic_writer_emits_strict_stable_json(
    tmp_path: Path,
) -> None:
    report = {"schema": "fixture.three_leg.v1", "passed": True}
    output = tmp_path / "nested" / "report.json"

    exact_byte_sha256 = COMPARATOR.atomic_write_json(output, report)

    expected = (
        json.dumps(report, allow_nan=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    assert output.read_bytes() == expected
    assert exact_byte_sha256 == hashlib.sha256(expected).hexdigest()


def test_ours_leg_runs_the_repository_actual_split_adapter_on_every_fixture() -> None:
    fixtures = COMPARATOR.build_fixture_manifest()
    dense = COMPARATOR.run_dense_leg(fixtures)
    result = COMPARATOR.run_ours_leg(fixtures)

    assert result["schema"] == COMPARATOR.LEG_RESULT_SCHEMA
    assert result["leg"] == "repository_actual_split"
    assert result["fixture_manifest_sha256"] == fixtures["content_hash_sha256"]
    assert result["case_count"] == 6
    assert result["claim_boundary"] == {
        "repository_implementation_under_test": True,
        "state_math_oracle": False,
        "actual_split_ledger_source": True,
        "actual_split_ledger_is_global_error_bound": False,
        "production_error_bound": False,
        "record_faithfulness": False,
    }

    dense_by_id = {case["fixture_id"]: case for case in dense["cases"]}
    fixtures_by_id = {
        case["fixture_id"]: case for case in fixtures["fixtures"]
    }
    for case in result["cases"]:
        fixture = fixtures_by_id[case["fixture_id"]]
        target = _complex_array(
            dense_by_id[case["fixture_id"]]["dense_reference"]["normalized_state"]
        )
        candidate = _complex_array(case["candidate_state"]["normalized_state"])
        event = case["actual_split_event"]
        expected_fidelity = 0.75 if case["max_bond"] == 1 else 1.0

        assert _fidelity(target, candidate) == pytest.approx(
            expected_fidelity,
            abs=1.0e-14,
        )
        assert case["candidate_state"]["raw_norm_sq"] == pytest.approx(
            1.0,
            abs=1.0e-14,
        )
        assert event["support"] == fixture["support"]
        assert event["gate_leg_sites"] == fixture["expected_split_path"][
            "operator_gate_leg_sites"
        ]
        assert event["split_count"] == 7
        assert [row["split_sites"] for row in event["split_records"]] == (
            fixture["expected_split_path"]["split_sites"]
        )
        assert [row["path_role"] for row in event["split_records"]] == (
            fixture["expected_split_path"]["roles"]
        )
        assert event["restored_output_norm_sq"] == pytest.approx(
            1.0,
            abs=1.0e-14,
        )
        expected_loss = 0.25 if case["max_bond"] == 1 else 0.0
        assert event["actual_discarded_weight_raw_sum"] == pytest.approx(
            expected_loss,
            abs=1.0e-14,
        )
        assert event["raw_output_norm_sq"] == pytest.approx(
            1.0 - expected_loss,
            abs=1.0e-14,
        )
        assert event["not_a_global_error_bound"] is True

    assert result["content_hash_sha256"] == COMPARATOR.canonical_hash(
        result,
        hash_field="content_hash_sha256",
    )


def test_quimb_leg_uses_public_ordered_wiring_without_oracle_claim() -> None:
    fixtures = COMPARATOR.build_fixture_manifest()
    dense = COMPARATOR.run_dense_leg(fixtures)
    result = COMPARATOR.run_quimb_wiring_leg(fixtures)

    assert result["schema"] == COMPARATOR.LEG_RESULT_SCHEMA
    assert result["leg"] == "quimb_public_wiring"
    assert result["case_count"] == 6
    assert result["claim_boundary"] == {
        "wiring_only": True,
        "same_pinned_backend_as_repository_adapter": True,
        "independent_scientific_oracle": False,
        "state_math_oracle": False,
        "actual_split_ledger_source": False,
        "production_error_bound": False,
        "record_faithfulness": False,
    }

    dense_by_id = {case["fixture_id"]: case for case in dense["cases"]}
    for case in result["cases"]:
        target = _complex_array(
            dense_by_id[case["fixture_id"]]["dense_reference"]["normalized_state"]
        )
        candidate = _complex_array(case["candidate_state"]["normalized_state"])
        expected = 0.75 if case["max_bond"] == 1 else 1.0
        public_call = case["public_call"]

        assert _fidelity(target, candidate) == pytest.approx(
            expected,
            abs=1.0e-14,
        )
        assert case["candidate_state"]["raw_norm_sq"] == pytest.approx(
            expected,
            abs=1.0e-14,
        )
        assert public_call["library"] == "quimb"
        assert public_call["version"] == "1.14.0"
        assert public_call["api"] == "MatrixProductState.gate_"
        assert public_call["contract"] == "swap+split"
        assert public_call["method"] == "svd"
        assert public_call["max_bond"] == case["max_bond"]
        assert public_call["cutoff"] == 0.0
        assert public_call["cutoff_mode"] == "rsum2"
        assert public_call["renorm"] is None
        assert public_call["ordered_where"] == case["support"]
        assert case["actual_split_ledger"] is None

    assert result["content_hash_sha256"] == COMPARATOR.canonical_hash(
        result,
        hash_field="content_hash_sha256",
    )


def test_three_leg_gate_matches_dense_and_kills_topology_norm_ledger_corruptions() -> None:
    fixtures = COMPARATOR.build_fixture_manifest()
    result = COMPARATOR.run_three_leg_gate(fixtures)

    assert result["schema"] == COMPARATOR.THREE_LEG_RESULT_SCHEMA
    assert result["verdict"] == "pass"
    assert result["passed"] is True
    assert len(result["comparisons"]) == 6
    for row in result["comparisons"]:
        assert row["actual_split_count"] == 7
        assert row["ours_vs_quimb_state_fidelity"] == pytest.approx(
            1.0,
            abs=1.0e-14,
        )
        assert row["ours_returned_norm_sq"] == pytest.approx(
            1.0,
            abs=1.0e-14,
        )
        assert row["ours_pre_restore_norm_sq"] == pytest.approx(
            row["quimb_raw_norm_sq"],
            abs=1.0e-14,
        )
        assert row["dense_cut_tail_is_actual_split_ledger"] is False
        assert row["expected_behavior_passed"] is True
        if row["max_bond"] == 1:
            assert row["behavior_class"] == (
                "bounded_cap_expected_rank_one_projection"
            )
            assert row["ours_vs_dense_state_fidelity"] == pytest.approx(
                0.75,
                abs=1.0e-14,
            )
            assert row["quimb_vs_dense_state_fidelity"] == pytest.approx(
                0.75,
                abs=1.0e-14,
            )
        else:
            assert row["behavior_class"] == "high_cap_exact_state"
            assert row["ours_vs_dense_state_fidelity"] == pytest.approx(
                1.0,
                abs=1.0e-14,
            )
            assert row["quimb_vs_dense_state_fidelity"] == pytest.approx(
                1.0,
                abs=1.0e-14,
            )

    swapped = result["corruption_falsifiers"]["swapped_topology"]
    assert swapped["corruption"] == "ordered_support_silently_sorted"
    assert swapped["repository_corrupted_state_fidelity"] == pytest.approx(
        0.5625,
        abs=1.0e-14,
    )
    assert swapped["quimb_corrupted_state_fidelity"] == pytest.approx(
        0.5625,
        abs=1.0e-14,
    )
    assert swapped["detected"] is True

    reconciliation = result["corruption_falsifiers"][
        "fine_grained_norm_and_ledger"
    ]
    assert reconciliation["fine_corruption_delta"] == 1.0e-8
    assert reconciliation["baseline_errors"] == []
    assert reconciliation["norm_corruption_errors"] == [
        "candidate_state_norm_vs_event_mismatch"
    ]
    assert reconciliation["norm_corruption_detected"] is True
    assert "split_raw_sum_reconciliation_mismatch" in reconciliation[
        "ledger_corruption_errors"
    ]
    assert "ledger_raw_sum_vs_norm_loss_mismatch" in reconciliation[
        "ledger_corruption_errors"
    ]
    assert reconciliation["ledger_corruption_detected"] is True

    assert result["claim_boundary"] == {
        "independent_state_math_oracle": "dense_numpy",
        "actual_split_ledger_source": "repository_actual_split",
        "quimb_public_leg_role": (
            "wiring_only_same_dependency_not_independent_scientific_oracle"
        ),
        "dense_cut_tail_is_actual_split_ledger": False,
        "actual_split_ledger_is_global_error_bound": False,
        "production_error_bound": False,
        "record_faithfulness": False,
    }
    assert result["content_hash_sha256"] == COMPARATOR.canonical_hash(
        result,
        hash_field="content_hash_sha256",
    )
