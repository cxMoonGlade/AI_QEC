"""CPU-only self-tests for mutation-result accounting."""

from __future__ import annotations

import pytest

from harness import mutation


def test_result_counts_never_credit_no_tests_as_killed() -> None:
    counts = mutation._result_counts(
        5,
        """
        pkg.x_a__mutmut_1: survived
        pkg.x_b__mutmut_1: timeout
        pkg.x_c__mutmut_1: suspicious
        pkg.x_d__mutmut_1: no tests
        """,
    )

    assert counts == {
        "killed": 1,
        "survived": 3,
        "no_tests": 1,
        "survivors": [
            "pkg.x_a__mutmut_1",
            "pkg.x_b__mutmut_1",
            "pkg.x_c__mutmut_1",
        ],
        "no_test_mutants": ["pkg.x_d__mutmut_1"],
    }


def test_result_counts_preserve_legacy_survivor_accounting_without_no_tests() -> None:
    counts = mutation._result_counts(
        10,
        "pkg.x_a__mutmut_1: survived\n",
    )

    assert counts["killed"] == 9
    assert counts["survived"] == 1
    assert counts["no_tests"] == 0
    assert counts["no_test_mutants"] == []


def test_score_results_fails_when_no_tests_would_have_falsely_passed() -> None:
    score = mutation._score_results(
        10,
        "pkg.x_a__mutmut_1: no tests\npkg.x_b__mutmut_1: no tests\n",
        bar=0.90,
    )

    assert score["killed"] == 8
    assert score["no_tests"] == 2
    assert score["kill_rate"] == 0.8
    assert score["pass"] is False


def test_result_counts_fail_loudly_on_impossible_total() -> None:
    with pytest.raises(ValueError, match="2 non-killed mutants for total=1"):
        mutation._result_counts(
            1,
            "pkg.x_a__mutmut_1: survived\npkg.x_b__mutmut_1: no tests\n",
        )
