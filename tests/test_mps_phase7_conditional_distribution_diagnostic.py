from __future__ import annotations

import copy
from decimal import Decimal
import importlib.util
import itertools
import json
import os
from pathlib import Path

import pytest

from conftest import requires_cuda


SCRIPT = (
    Path(__file__).parents[1]
    / "scripts"
    / "mps_phase7_conditional_distribution_diagnostic.py"
)
SPEC = importlib.util.spec_from_file_location(
    "mps_phase7_conditional_distribution_diagnostic",
    SCRIPT,
)
assert SPEC is not None and SPEC.loader is not None
DIAGNOSTIC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DIAGNOSTIC)


def test_total_variation_aligns_record_values_on_union_with_missing_zero() -> None:
    exact = DIAGNOSTIC.record_probability_map(
        [[0, 0], [1, 1]],
        [0.75, 0.25],
        name="exact",
    )
    sampled = DIAGNOSTIC.record_probability_map(
        [[0, 0], [0, 1]],
        [0.50, 0.50],
        name="sampled",
    )

    comparison = DIAGNOSTIC.compare_record_distributions(
        exact,
        sampled,
        trajectory_count=1000,
        rng_seed=7,
    )

    assert comparison["record_support_alignment_policy"] == (
        "union_of_record_values_missing_probability_zero"
    )
    assert comparison["union_record_support"] == [[0, 0], [0, 1], [1, 1]]
    assert comparison["total_variation_distance"] == pytest.approx(0.5)


def test_frozen_gate_distinguishes_strict_from_confidence_adjusted_acceptance() -> None:
    exact = DIAGNOSTIC.record_probability_map(
        [[0, 0], [1, 1]],
        [0.50, 0.50],
        name="exact",
    )
    sampled = DIAGNOSTIC.record_probability_map(
        [[0, 0], [1, 1]],
        [0.29, 0.71],
        name="sampled",
    )

    comparison = DIAGNOSTIC.compare_record_distributions(
        exact,
        sampled,
        trajectory_count=1000,
        rng_seed=19,
    )
    expected_per_bin = (
        DIAGNOSTIC.math.log(2.0 / 0.001) / (2.0 * 1000.0)
    ) ** 0.5
    expected_tv_halfwidth = 2.0 / 2.0 * expected_per_bin

    assert comparison["confidence_level"] == 0.999
    assert comparison["alpha"] == pytest.approx(0.001)
    assert comparison["per_bin_hoeffding_halfwidth"] == pytest.approx(
        expected_per_bin
    )
    assert comparison["tv_halfwidth"] == pytest.approx(expected_tv_halfwidth)
    assert comparison["strict_tv_gate"] == 0.2
    assert comparison["strict_passed"] is False
    assert comparison["confidence_adjusted_gross_gate"] == pytest.approx(
        0.2 + expected_tv_halfwidth
    )
    assert comparison["confidence_adjusted_passed"] is True
    assert comparison["acceptance_basis"] == "confidence_adjusted_gross_gate"


def test_deliberate_corruption_is_large_and_rejected_by_frozen_ceiling() -> None:
    exact = DIAGNOSTIC.record_probability_map(
        [[0, 0], [1, 1]],
        [0.50, 0.50],
        name="exact",
    )

    falsifier = DIAGNOSTIC.deliberate_corruption_falsifier(exact)

    assert falsifier["corruption"] == "flip_final_bit_of_every_positive_record"
    assert falsifier["total_variation_distance"] >= 0.5
    assert falsifier["required_minimum_total_variation"] == 0.5
    assert falsifier["rejection_gate"] == 0.45
    assert falsifier["rejected_by_gross_gate_ceiling"] is True
    assert falsifier["passed"] is True


def _exact_bell_repeated_execution() -> dict:
    records = [list(record) for record in itertools.product((0, 1), repeat=4)]
    probabilities = [
        0.5 if record in ([0, 0, 0, 0], [1, 1, 1, 1]) else 0.0
        for record in records
    ]
    return {
        "measurement_records": records,
        "record_probabilities": probabilities,
        "trajectory_sampling": {
            "mode": "exact_branch_enumeration",
            "trajectory_count": None,
            "record_support_policy": "full_binary_record_support",
        },
    }


def _sampled_bell_repeated_execution(seed: int, p_zero: float) -> dict:
    zero_count = round(p_zero * 1000)
    return {
        "measurement_records": [[0, 0, 0, 0], [1, 1, 1, 1]],
        "record_counts": [zero_count, 1000 - zero_count],
        "record_probabilities": [zero_count / 1000.0, (1000 - zero_count) / 1000.0],
        "trajectory_sampling": {
            "mode": "sampled_product_channel_trajectories",
            "trajectory_count": 1000,
            "rng_seed": seed,
            "rng_seed_was_explicit": True,
            "record_support_policy": "observed_empirical_outcomes_only",
        },
    }


def test_analysis_accepts_multiple_explicit_seed_sparse_distributions() -> None:
    analysis = DIAGNOSTIC.analyze_distribution_payloads(
        _exact_bell_repeated_execution(),
        [
            _sampled_bell_repeated_execution(7, 0.48),
            _sampled_bell_repeated_execution(19, 0.53),
        ],
        trajectory_count=1000,
    )

    assert analysis["exact_hand_distribution_check"]["passed"] is True
    assert analysis["exact_hand_distribution_check"][
        "total_variation_distance"
    ] == pytest.approx(0.0)
    assert [row["rng_seed"] for row in analysis["seed_comparisons"]] == [7, 19]
    assert all(
        row["union_record_support_size"] == 16
        for row in analysis["seed_comparisons"]
    )
    assert analysis["all_seed_strict_passed"] is True
    assert analysis["all_seed_confidence_adjusted_passed"] is True
    assert analysis["deliberate_corruption_falsifier"]["passed"] is True
    assert analysis["passed"] is True
    assert analysis["acceptance_basis"] == (
        "every_seed_tv_at_or_below_confidence_adjusted_gross_gate"
    )


@pytest.mark.parametrize(
    "invalid_probability",
    [True, "0.5", Decimal("0.5"), 0.5 + 0.0j],
    ids=["bool", "numeric_string", "decimal_coercible", "complex"],
)
def test_probability_map_rejects_non_real_or_implicitly_coercible_values(
    invalid_probability: object,
) -> None:
    with pytest.raises(TypeError, match="real number"):
        DIAGNOSTIC.record_probability_map(
            [[0], [1]],
            [invalid_probability, 0.5],
            name="corrupted",
        )


@pytest.mark.parametrize(
    "corruption",
    [
        {"record_counts": [480]},
        {"record_counts": [480, 519]},
        {"record_counts": [True, 999]},
        {"record_counts": [520, 480]},
        {"record_probabilities": [0.49, 0.51]},
    ],
    ids=[
        "count_length",
        "count_total",
        "boolean_count",
        "counts_swapped_against_probabilities",
        "probability_not_count_over_n",
    ],
)
def test_sampled_analysis_rejects_corrupted_count_probability_contract(
    corruption: dict,
) -> None:
    sampled = _sampled_bell_repeated_execution(7, 0.48)
    sampled.update(copy.deepcopy(corruption))

    with pytest.raises(ValueError, match="record_counts|count / trajectory_count"):
        DIAGNOSTIC.analyze_distribution_payloads(
            _exact_bell_repeated_execution(),
            [sampled, _sampled_bell_repeated_execution(19, 0.53)],
            trajectory_count=1000,
        )


def _fake_manifest(execution: dict, *, source_hash: str) -> dict:
    return {
        "schema": (
            "error_coupling_simulator.frontend.qt_mps_restricted_execution.v6"
        ),
        "content_hash": "a" * 64,
        "source_hash": source_hash,
        "execution_status": "completed",
        "verdict": "pass",
        "passed": True,
        "blocked_reason": None,
        "qt_mps_backend_executed": True,
        "claims_exact_joint_lindblad_generator": False,
        "claims_dense_channel_evidence": False,
        "claims_production_scalable_backend": False,
        "mps_execution": execution,
    }


def test_report_is_hashed_claim_bounded_and_written_atomically(tmp_path: Path) -> None:
    exact_execution = _exact_bell_repeated_execution()
    sampled_executions = [
        _sampled_bell_repeated_execution(7, 0.48),
        _sampled_bell_repeated_execution(19, 0.53),
    ]
    analysis = DIAGNOSTIC.analyze_distribution_payloads(
        exact_execution,
        sampled_executions,
        trajectory_count=1000,
    )
    report = DIAGNOSTIC.build_report(
        fixture={"source_hash": "fixture-hash", "measurement_width": 4},
        exact_manifest=_fake_manifest(
            exact_execution,
            source_hash="fixture-hash",
        ),
        sampled_manifests=[
            _fake_manifest(execution, source_hash="fixture-hash")
            for execution in sampled_executions
        ],
        analysis=analysis,
        provenance={"git_commit": "deadbeef", "binding_file_sha256": {}},
        generated_at_utc="2026-07-17T00:00:00+00:00",
        runtime_seconds=1.25,
    )

    assert report["schema"] == DIAGNOSTIC.REPORT_SCHEMA
    assert report["diagnostic_acceptance"]["passed"] is True
    assert report["claim_boundary"]["production_error_bound"] is False
    assert report["claim_boundary"]["record_faithfulness"] is False
    assert report["claim_boundary"]["independent_scientific_oracle"] is False
    assert report["content_hash_sha256"] == DIAGNOSTIC.canonical_payload_hash(
        report,
        hash_field="content_hash_sha256",
    )

    output = tmp_path / "nested" / "report.json"
    DIAGNOSTIC.atomic_write_json(output, report)
    assert json.loads(output.read_text(encoding="utf-8")) == report
    assert list(output.parent.glob("*.tmp")) == []


def test_hand_checkable_fixture_has_two_targets_and_two_correlated_boundaries() -> None:
    schedule, fixture = DIAGNOSTIC.build_hand_checkable_schedule()

    assert fixture["source_hash"] == schedule.source_hash
    assert fixture["num_qubits"] == 2
    assert fixture["measurement_boundary_count"] == 2
    assert fixture["measurement_width"] == 4
    assert [row["targets"] for row in fixture["measurement_boundaries"]] == [
        [0, 1],
        [0, 1],
    ]
    assert fixture["expected_positive_distribution"] == [
        {"record": [0, 0, 0, 0], "probability": 0.5},
        {"record": [1, 1, 1, 1], "probability": 0.5},
    ]
    assert fixture["local_lindblad_context"]["gamma_phi_per_ns"] == 0.0
    assert fixture["local_lindblad_context"]["gamma_1_per_ns"] == 0.0
    assert fixture["local_lindblad_context"]["gamma_readout_phi_per_ns"] == 0.0


@requires_cuda
@pytest.mark.skipif(
    os.environ.get("ECS_RUN_MPS_PHASE7_GPU_INTEGRATION") != "1",
    reason="opt-in Phase 7 QT/MPS GPU diagnostic integration",
)
def test_gpu_diagnostic_runs_exact_and_multiple_explicit_sampled_seeds(
    tmp_path: Path,
) -> None:
    output = tmp_path / "report.json"
    report = DIAGNOSTIC.run_diagnostic(
        trajectory_count=32,
        seeds=(7, 19),
        output=output,
    )

    assert report["diagnostic_acceptance"]["passed"] is True
    assert report["exact_branch"]["trajectory_mode"] == "exact_branch_enumeration"
    assert [row["rng_seed"] for row in report["sampled_branches"]] == [7, 19]
    assert all(
        row["rng_seed_was_explicit"] is True
        for row in report["sampled_branches"]
    )
    assert output.is_file()
