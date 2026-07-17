"""Behavioral contract for the MPS-016 three-leg comparator."""

from __future__ import annotations

import importlib.util
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
