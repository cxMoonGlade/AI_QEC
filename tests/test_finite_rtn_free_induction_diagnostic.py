from __future__ import annotations

import copy
import importlib.util
import math
from pathlib import Path

import numpy as np
import pytest


SCRIPT = Path(__file__).parents[1] / "scripts" / "finite_rtn_free_induction_diagnostic.py"
SPEC = importlib.util.spec_from_file_location("finite_rtn_free_induction_diagnostic", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


def test_single_ctmc_formula_matches_two_state_generator() -> None:
    times = (0.0, 0.5, 3.0, 10.0, 40.0)
    for amplitude, gamma in ((0.03, 0.01), (0.01, 0.03), (0.02, 0.02)):
        formula = GATE.single_ctmc_coherence(times, amplitude, gamma)
        oracle = np.asarray(
            [GATE.full_ctmc_coherence(t, [amplitude], [gamma]) for t in times]
        )
        np.testing.assert_allclose(formula, oracle, rtol=1.0e-12, atol=1.0e-12)


def test_joint_generator_has_declared_endpoint_autocorrelation() -> None:
    gamma = 0.037
    transition = GATE.expm(GATE.joint_ctmc_generator([gamma]))
    expected_flip = 0.5 * (1.0 - math.exp(-2.0 * gamma))
    np.testing.assert_allclose(
        transition,
        [[1.0 - expected_flip, expected_flip], [expected_flip, 1.0 - expected_flip]],
        rtol=1.0e-13,
        atol=1.0e-14,
    )


def test_factorized_ctmc_matches_full_joint_oracle() -> None:
    amplitudes = np.asarray([0.035, 0.02, 0.01])
    gammas = np.asarray([0.005, 0.03, 0.2])
    times = (0.0, 1.0, 8.0, 30.0, 100.0)
    product = GATE.product_ctmc_coherence(times, amplitudes, gammas)
    oracle = np.asarray(
        [GATE.full_ctmc_coherence(t, amplitudes, gammas) for t in times]
    )
    np.testing.assert_allclose(product, oracle, rtol=1.0e-11, atol=1.0e-12)


def test_factorized_held_sequence_matches_full_joint_oracle() -> None:
    amplitudes = np.asarray([0.035, 0.02, 0.01])
    gammas = np.asarray([0.005, 0.03, 0.2])
    product = GATE.product_held_sequence(amplitudes, gammas, 80)
    oracle = GATE.full_held_sequence(amplitudes, gammas, 80)
    np.testing.assert_allclose(product, oracle, rtol=1.0e-11, atol=1.0e-12)


def test_registered_controls_are_falsifiable() -> None:
    source = GATE.OneOverFDriftSource()
    amplitudes = source.amplitudes_radns * source.cycle_time_ns
    gammas = source.gammas_per_cycle
    grid = np.arange(0.0, 200.0 + 0.005, 0.01)

    exact = GATE.product_ctmc_coherence(grid, amplitudes, gammas)
    gaussian = GATE.gaussian_surrogate_coherence(grid, amplitudes, gammas)
    weak = GATE.product_ctmc_coherence(grid, amplitudes, 2.0 * amplitudes)

    _, exact_max_step = GATE.positive_excursion(exact)
    _, gaussian_max_step = GATE.positive_excursion(gaussian)
    _, weak_max_step = GATE.positive_excursion(weak)
    assert exact_max_step > GATE.MONOTONIC_TOL
    assert gaussian_max_step <= GATE.MONOTONIC_TOL
    assert weak_max_step <= GATE.MONOTONIC_TOL


def test_adjudication_distinguishes_null_from_implementation_failure() -> None:
    assert GATE.diagnostic_verdict(
        implementation_passed=True, positive_excursion_found=True
    ) == "CONFIRMED_DIAGNOSTIC_ONLY"
    assert GATE.diagnostic_verdict(
        implementation_passed=True, positive_excursion_found=False
    ) == "NULL_WITHIN_HORIZON"
    assert GATE.diagnostic_verdict(
        implementation_passed=False, positive_excursion_found=True
    ) == "IMPLEMENTATION_GATE_FAILED"
    assert GATE.summarize_diagnostics(
        implementation_passed=True,
        continuous_verdict="NULL_WITHIN_HORIZON",
        held_verdict="NULL_WITHIN_HORIZON",
    ) == "BOTH_DIAGNOSTICS_NULL_WITHIN_HORIZON"
    assert GATE.summarize_diagnostics(
        implementation_passed=True,
        continuous_verdict="CONFIRMED_DIAGNOSTIC_ONLY",
        held_verdict="NULL_WITHIN_HORIZON",
    ) == "MIXED_DIAGNOSTIC_RESULT"
    assert GATE.summarize_diagnostics(
        implementation_passed=False,
        continuous_verdict="CONFIRMED_DIAGNOSTIC_ONLY",
        held_verdict="CONFIRMED_DIAGNOSTIC_ONLY",
    ) == "IMPLEMENTATION_GATE_FAILED"


def test_positive_excursion_reports_zero_for_monotone_decrease() -> None:
    total, maximum = GATE.positive_excursion([1.0, 0.8, 0.3])
    assert total == 0.0
    assert maximum == 0.0


def test_current_contract_schema_and_default_output_are_hard_cut() -> None:
    assert (
        GATE.SCHEMA
        == "error_coupling_simulator.source.finite_rtn_free_induction_diagnostic.v1"
    )
    assert GATE.PROTOCOL_STATUS == "POST_RESULT_RECONSTRUCTION_NOT_PREREGISTERED"
    assert GATE.DIAGNOSTIC_CONTRACT == Path(
        "docs/simulator_validation/finite_rtn_free_induction_diagnostic_contract_2026-07-15.md"
    )
    assert GATE.DEFAULT_OUTPUT == Path(
        "outputs/simulator_validation/diagnostics/finite_rtn_free_induction/report.json"
    )


def test_current_defaults_have_exactly_three_strong_modes() -> None:
    source = GATE.OneOverFDriftSource()
    amplitudes = source.amplitudes_radns * source.cycle_time_ns
    ratios = amplitudes / source.gammas_per_cycle
    np.testing.assert_array_equal(np.flatnonzero(ratios > 1.0), [0, 1, 2])


def test_analytic_zero_recovers_at_high_precision() -> None:
    source = GATE.OneOverFDriftSource()
    amplitudes = source.amplitudes_radns * source.cycle_time_ns
    gammas = source.gammas_per_cycle
    mode, zero = GATE.earliest_strong_zero(amplitudes, gammas)
    assert mode == 0
    at_zero = abs(GATE.high_precision_product(zero, amplitudes, gammas))
    after_zero = abs(GATE.high_precision_product(zero + GATE.mp.mpf("1"), amplitudes, gammas))
    assert at_zero <= GATE.mp.mpf("1e-60")
    assert after_zero > GATE.mp.mpf("1e-12")


def test_registered_corruptions_disagree_with_full_state_oracle() -> None:
    source = GATE.OneOverFDriftSource()
    amplitudes = source.amplitudes_radns * source.cycle_time_ns
    gammas = source.gammas_per_cycle
    oracle = np.asarray(
        [GATE.full_ctmc_coherence(t, amplitudes, gammas) for t in GATE.CTMC_ORACLE_TIMES]
    )
    wrong_rate = GATE.product_ctmc_coherence(GATE.CTMC_ORACLE_TIMES, amplitudes, 2.0 * gammas)
    missing_mode = GATE.product_ctmc_coherence(
        GATE.CTMC_ORACLE_TIMES, amplitudes[1:], gammas[1:]
    )
    assert float(np.max(np.abs(oracle - wrong_rate))) > 100.0 * GATE.ORACLE_TOL
    assert float(np.max(np.abs(oracle - missing_mode))) > 100.0 * GATE.ORACLE_TOL


def test_full_report_contract_hash_and_claim_boundary(monkeypatch) -> None:
    monkeypatch.setattr(
        GATE,
        "execution_provenance",
        lambda: {
            "git_commit": "unit-test",
            "tracked_clean_paths": {},
            "file_sha256": {},
            "git_blob_ids": {},
            "import_origin": {
                "module": GATE.OneOverFDriftSource.__module__,
                "source_file": "src/error_coupling_simulator/source/process.py",
            },
            "runtime": {"python": "unit-test", "packages": {}},
        },
    )
    report = GATE.build_report()
    assert report["schema"] == GATE.SCHEMA
    assert report["protocol_status"] == GATE.PROTOCOL_STATUS
    assert report["diagnostic_contract"] == GATE.DIAGNOSTIC_CONTRACT.as_posix()
    assert report["implementation_verdict"] == "PASS"
    assert report["diagnostic_summary"] == "BOTH_DIAGNOSTICS_POSITIVE"
    assert report["claim_boundary"]["production_qec_bridge"] == "OPEN"
    assert "preregistration" not in report
    assert report["content_hash_sha256"] == GATE.report_content_hash(report)

    tampered = copy.deepcopy(report)
    tampered["source_defaults"]["cycle_time_ns"] += 1.0
    assert GATE.report_content_hash(tampered) != report["content_hash_sha256"]


def test_atomic_report_writer_publishes_exact_bytes(tmp_path) -> None:
    report = {"schema": GATE.SCHEMA, "content_hash_sha256": "test"}
    destination = tmp_path / "nested" / "report.json"
    byte_hash = GATE.write_report_atomic(destination, report)
    payload = destination.read_bytes()
    assert byte_hash == GATE.hashlib.sha256(payload).hexdigest()
    assert not list(destination.parent.glob(f".{destination.name}.*"))


def test_execution_provenance_rejects_wrong_import_origin(monkeypatch) -> None:
    monkeypatch.setattr(GATE.inspect, "getsourcefile", lambda _object: "/tmp/not-the-bound-source.py")
    with pytest.raises(RuntimeError, match="import origin"):
        GATE.execution_provenance()
