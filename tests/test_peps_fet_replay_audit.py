from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import numpy as np
import pytest


SCRIPT = (
    Path(__file__).parents[1] / "tools/diagnostics/peps_fet_replay_audit.py"
)
SPEC = importlib.util.spec_from_file_location("peps_fet_replay_audit", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def _worker(
    case_id: str, *, seed: int = 0, debug: int = 0, repetition: int = 0
) -> dict:
    map_array = np.asarray([[1.0, 0.0], [0.0, 0.5]], dtype=np.complex128)
    state = np.asarray([1.0, 1.0j], dtype=np.complex128)
    entropy_gate = AUDIT.evaluate_entropy_gate(
        entropy=0.25, reference=0.25, leak_mass=0.0
    )
    entropy_gate.update(
        {
            "region_A": [0],
            "schmidt_rank": 2,
            "full_norm2": 2.0,
            "qubit_norm2": 2.0,
        }
    )
    cut = {
        "ordinal": 0,
        "bond": "B0_1",
        "dim_in": 2,
        "dim_out": 2,
        "exact_rank": 2,
        "env_rank": 2,
        "selected_env_rank": 2,
        "proposed_env_rank": 2,
        "map_rank_axis": 2,
        "Fid_gamma": AUDIT.classify_fid_gamma(0.999999999),
        "selected_Fid_gamma": 0.999999999,
        "applied_Fid_gamma": 1.0,
        "selector_outcome": "accepted",
        "outcome": "noop",
        "reason": "full_rank_identity",
        "writeback_applied": False,
        "writeback_call_count": 0,
        "requested_solver_seed": 0,
        "solver_seed": 0,
        "attempted_ranks": 2,
        "solver_failure_count": 0,
        "selected_target_met": True,
        "selected_fidelity_valid": True,
        "selector_consistent": True,
        "selector_metadata_valid": True,
        "solver_seed_consistent": True,
        "fallback_identity_factors": False,
        "trajectory_ledger_authentication": {
            "status": "AUTHENTICATED",
            "method": "selector_wrapper_vs_trajectory_ledger",
        },
        "observer_requested": False,
        "fidelity_curve": None,
        "map_frobenius_norm": float(np.linalg.norm(map_array)),
        "eps_fid_requested": AUDIT.EPS_FID,
        "eps_fid": AUDIT.EPS_FID,
        "map_shapes_ok": True,
        "map_dtype_ok": True,
        "map_device_ok": True,
        "map_finite": True,
        "map_sha256_c128le": AUDIT.array_sha256_c128le(map_array),
        "map_projective_sha256_c128le": (
            AUDIT.projective_array_sha256(map_array)
        ),
        "selected_map_sha256_c128le": AUDIT.array_sha256_c128le(map_array),
        "selected_map_projective_sha256_c128le": (
            AUDIT.projective_array_sha256(map_array)
        ),
        "applied_map_sha256_c128le": None,
        "applied_map_projective_sha256_c128le": None,
        "selected_applied_map_exact_match": None,
        "endpoint_absorption_exact_match": None,
        "expected_left_endpoint_sha256_c128le": None,
        "observed_left_endpoint_sha256_c128le": None,
        "expected_right_endpoint_sha256_c128le": None,
        "observed_right_endpoint_sha256_c128le": None,
    }
    wrapper_evidence = {
        key: copy.deepcopy(cut[key])
        for key in (
            "ordinal",
            "bond",
            "dim_in",
            "selected_env_rank",
            "proposed_env_rank",
            "map_rank_axis",
            "Fid_gamma",
            "selected_Fid_gamma",
            "selector_outcome",
            "eps_fid_requested",
            "requested_solver_seed",
            "solver_seed",
            "solver_failure_count",
            "attempted_ranks",
            "observer_requested",
            "fidelity_curve",
            "writeback_call_count",
            "map_shapes_ok",
            "map_dtype_ok",
            "map_device_ok",
            "map_finite",
            "fallback_identity_factors",
            "selected_map_sha256_c128le",
            "selected_map_projective_sha256_c128le",
            "applied_map_sha256_c128le",
            "applied_map_projective_sha256_c128le",
            "selected_applied_map_exact_match",
            "endpoint_absorption_exact_match",
            "expected_left_endpoint_sha256_c128le",
            "observed_left_endpoint_sha256_c128le",
            "expected_right_endpoint_sha256_c128le",
            "observed_right_endpoint_sha256_c128le",
            "map_frobenius_norm",
            "map_sha256_c128le",
            "map_projective_sha256_c128le",
        )
    }
    ledger_evidence = {
        "bond": "B0_1",
        "dim_in": 2,
        "selected_env_rank": 2,
        "proposed_env_rank": 2,
        "Fid_gamma": copy.deepcopy(cut["Fid_gamma"]),
        "selected_Fid_gamma": cut["selected_Fid_gamma"],
        "writeback_applied": False,
        "env_rank": 2,
        "dim_out": 2,
        "applied_Fid_gamma": 1.0,
        "outcome": "noop",
        "reason": "full_rank_identity",
        "selector_outcome": "accepted",
        "requested_fet_solver_seed": 0,
        "fet_solver_seed": 0,
        "attempted_ranks": 2,
        "solver_failure_count": 0,
        "fidelity_target": 1.0 - AUDIT.EPS_FID,
        "candidate_fidelity_valid": True,
        "target_met": True,
        "selected_target_met": True,
        "selected_fidelity_valid": True,
        "selector_consistent": True,
        "selector_metadata_valid": True,
        "solver_seed_consistent": True,
        "fallback_identity_factors": False,
        "map_shapes_ok": True,
        "map_dtype_ok": True,
        "map_device_ok": True,
        "map_finite": True,
        "map_valid": True,
        "exact_rank": 2,
        "eps_fid": AUDIT.EPS_FID,
    }
    cut["selector_wrapper_evidence"] = wrapper_evidence
    cut["trajectory_ledger_evidence"] = ledger_evidence
    cut.update(AUDIT.authenticate_fet_ledger_row(wrapper_evidence, ledger_evidence))
    cut.update(
        AUDIT.evaluate_fet_cut_contract(
            map_array=map_array,
            dim_in=cut["dim_in"],
            dim_out=cut["dim_out"],
            env_rank=cut["env_rank"],
            fid_gamma=cut["Fid_gamma"],
            eps_fid=cut["eps_fid"],
            writeback_applied=False,
        )
    )
    cut["fidelity_curve_observation"] = (
        AUDIT.validate_fidelity_curve_observation(cut)
    )
    return {
        "case_id": case_id,
        "case": {
            "cuda_seed": seed,
            "fidcurve_debug": debug,
            "repetition": repetition,
        },
        "input_identity_sha256": "f" * 64,
        "per_cut": [cut],
        "cut_count": 1,
        "round_state": {
            "sha256_c128le": AUDIT.array_sha256_c128le(state),
            "projective_sha256_c128le": AUDIT.projective_array_sha256(state),
            "amplitude_count": int(state.size),
        },
        "array_archive_manifest": {
            "format": "npz_temporary_authenticated_arrays",
            "exact_keys": ["map_0000", "round_state"],
            "dtype": "complex128",
            "retained_in_final_report": False,
        },
        "entropy_gate": entropy_gate,
        "record_payload_sha256": "a" * 64,
    }


def _arrays(*, map_array=None, state=None) -> dict:
    if map_array is None:
        map_array = np.asarray([[1.0, 0.0], [0.0, 0.5]], dtype=np.complex128)
    if state is None:
        state = np.asarray([1.0, 1.0j], dtype=np.complex128)
    return {"map_0000": map_array, "round_state": state}


def test_default_cases_cover_repeat_seed_and_debug_controls() -> None:
    assert AUDIT.DEFAULT_CASES[0] == (0, 0, 0)
    assert any(case[:2] == (0, 0) and case[2] != 0 for case in AUDIT.DEFAULT_CASES)
    assert any(case[0] != 0 and case[1] == 0 for case in AUDIT.DEFAULT_CASES)
    assert any(case[0] == 0 and case[1] == 1 for case in AUDIT.DEFAULT_CASES)
    assert len({AUDIT.case_id(case) for case in AUDIT.DEFAULT_CASES}) == len(
        AUDIT.DEFAULT_CASES
    )
    assert AUDIT.validate_case_matrix(AUDIT.DEFAULT_CASES) >= (
        AUDIT.REQUIRED_COMPARISON_KINDS
    )


@pytest.mark.parametrize(
    ("cases", "missing_kind"),
    [
        (
            ((0, 0, 0), (1, 0, 0), (0, 1, 0), (2, 1, 0)),
            "fresh_process_repeat",
        ),
        (
            ((0, 0, 0), (0, 0, 1), (0, 1, 0), (0, 1, 1)),
            "cuda_seed_sensitivity",
        ),
        (
            ((0, 0, 0), (0, 0, 1), (1, 0, 0), (2, 0, 0)),
            "fidcurve_debug_invariance",
        ),
    ],
)
def test_case_matrix_rejects_each_missing_control(cases, missing_kind) -> None:
    with pytest.raises(ValueError, match=missing_kind):
        AUDIT.validate_case_matrix(cases)


def test_comparison_stage_rejects_a_missing_required_control() -> None:
    incomplete = [
        {"kind": "fresh_process_repeat"},
        {"kind": "cuda_seed_sensitivity"},
    ]
    with pytest.raises(RuntimeError, match="fidcurve_debug_invariance"):
        AUDIT.validate_comparison_kinds(incomplete)


def test_projective_distance_removes_only_global_scale_and_phase() -> None:
    reference = np.asarray([1.0 + 2.0j, -0.3j, 0.7], dtype=np.complex128)
    equivalent = reference * (3.0 - 4.0j)
    distance = AUDIT.projective_array_distance(reference, equivalent)
    assert distance["l2"] <= 1.0e-15
    assert distance["max_abs"] <= 1.0e-15

    corrupted = equivalent.copy()
    corrupted[1] += 1.0e-4
    bad = AUDIT.projective_array_distance(reference, corrupted)
    assert bad["l2"] > 1.0e-6
    assert bad["max_abs"] > 1.0e-6


def test_independent_gf2_entropy_trips_on_corrupted_bell_generator() -> None:
    bell = [{0: "X", 1: "X"}, {0: "Z", 1: "Z"}]
    corrupted = [{0: "X"}, {0: "Z", 1: "Z"}]
    assert AUDIT.stabilizer_entropy_sa(bell, 2, (0,)) == 1.0
    assert AUDIT.stabilizer_entropy_sa(corrupted, 2, (0,)) == 0.0


def test_entropy_gate_requires_the_leakage_off_precondition() -> None:
    clean = AUDIT.evaluate_entropy_gate(
        entropy=2.0, reference=2.0, leak_mass=AUDIT.LEAK_MASS_TOL
    )
    assert clean["verdict"] == "PASS"
    assert clean["leakage_off_precondition_passed"] is True

    leaked = AUDIT.evaluate_entropy_gate(
        entropy=2.0,
        reference=2.0,
        leak_mass=AUDIT.LEAK_MASS_TOL * 10.0,
    )
    assert leaked["entropy_matches"] is True
    assert leaked["leakage_off_precondition_passed"] is False
    assert leaked["verdict"] == "RED"


def test_below_target_lossy_fet_writeback_is_a_contract_violation() -> None:
    identity = np.eye(2, dtype=np.complex128)
    safe_noop = AUDIT.evaluate_fet_cut_contract(
        map_array=identity,
        dim_in=2,
        dim_out=2,
        env_rank=2,
        fid_gamma=0.95,
        eps_fid=0.01,
    )
    assert safe_noop["target_met"] is False
    assert safe_noop["map_vs_identity_relative_error"] == 0.0
    assert safe_noop["fallback_contract_violation"] is False

    lossy_map = np.diag([1.0, 0.0]).astype(np.complex128)
    violation = AUDIT.evaluate_fet_cut_contract(
        map_array=lossy_map,
        dim_in=2,
        dim_out=1,
        env_rank=1,
        fid_gamma=0.95,
        eps_fid=0.01,
    )
    assert violation["fidelity_target"] == 0.99
    assert violation["target_met"] is False
    assert violation["nonidentity_or_lossy_writeback"] is True
    assert violation["fallback_contract_violation"] is True

    cut = {"ordinal": 3, "bond": "B3_4", **violation}
    aggregate = AUDIT.aggregate_fet_fallback_contract(
        [{"case_id": "synthetic", "per_cut": [cut]}]
    )
    assert aggregate["verdict"] == "RED"
    assert aggregate["violations"] == [
        {"case_id": "synthetic", "ordinal": 3, "bond": "B3_4"}
    ]
    assert (
        AUDIT.evaluate_overall_verdict(
            replay_verdict="PASS_SCOPED_BITWISE",
            entropy_red_case_ids=[],
            fet_verdict=aggregate["verdict"],
            solver_health_verdict="PASS",
            nondegeneracy_verdict="PASS",
        )
        == "RED"
    )


def test_nonfinite_safe_noop_replays_but_solver_health_keeps_overall_red() -> None:
    def with_fid(report: dict, value: float) -> dict:
        report = copy.deepcopy(report)
        cut = report["per_cut"][0]
        cut["Fid_gamma"] = AUDIT.classify_fid_gamma(value)
        cut.update(
            AUDIT.evaluate_fet_cut_contract(
                map_array=_arrays()["map_0000"],
                dim_in=cut["dim_in"],
                dim_out=cut["dim_out"],
                env_rank=cut["env_rank"],
                fid_gamma=cut["Fid_gamma"],
                eps_fid=cut["eps_fid"],
                writeback_applied=False,
            )
        )
        return report

    nonfinite = with_fid(_worker("nonfinite"), float("-inf"))
    evidence = nonfinite["per_cut"][0]["Fid_gamma"]
    assert evidence == {
        "classification": "negative_infinity",
        "value": None,
        "raw_repr": "-inf",
    }
    assert nonfinite["per_cut"][0]["nonfinite_fid_gamma_violation"] is False
    assert nonfinite["per_cut"][0]["fet_contract_violation"] is False
    AUDIT.canonical_json_bytes(nonfinite)

    aggregate = AUDIT.aggregate_fet_fallback_contract([nonfinite])
    assert aggregate["verdict"] == "PASS"
    assert aggregate["nonfinite_fid_gamma_count"] == 0
    solver_health = AUDIT.aggregate_fet_solver_health([nonfinite])
    assert solver_health["verdict"] == "RED"
    assert solver_health["unhealthy_cut_count"] == 1
    assert (
        AUDIT.evaluate_overall_verdict(
            replay_verdict="PASS_SCOPED_BITWISE",
            entropy_red_case_ids=[],
            fet_verdict=aggregate["verdict"],
            solver_health_verdict=solver_health["verdict"],
            nondegeneracy_verdict="PASS",
        )
        == "RED"
    )

    finite = _worker("finite")
    mismatch = AUDIT.compare_worker_results(
        finite, nonfinite, _arrays(), _arrays()
    )
    assert mismatch["same_Fid_gamma_classification_sequence"] is False
    assert mismatch["verdict"] == "FAIL_FID_GAMMA_CLASSIFICATION_MISMATCH"
    assert AUDIT.summarize_replay([mismatch]) == "FAIL_FRESH_PROCESS_REPEAT_DIVERGED"

    repeat_nonfinite = with_fid(_worker("repeat-nonfinite"), float("-inf"))
    deterministic = AUDIT.compare_worker_results(
        nonfinite, repeat_nonfinite, _arrays(), _arrays()
    )
    assert deterministic["same_Fid_gamma_classification_sequence"] is True
    assert deterministic["all_Fid_gamma_finite"] is False
    assert deterministic["verdict"] == "PASS_SCOPED_BITWISE"
    assert AUDIT.summarize_replay([deterministic]) == "PASS_SCOPED_BITWISE"


def test_nonfinite_candidate_with_strict_noop_is_not_a_fet_contract_violation() -> None:
    """Solver failure remains visible evidence but is safe when nothing mutates."""
    identity = np.eye(2, dtype=np.complex128)
    result = AUDIT.evaluate_fet_cut_contract(
        map_array=identity,
        dim_in=2,
        dim_out=2,
        env_rank=2,
        fid_gamma=float("-inf"),
        eps_fid=0.01,
        writeback_applied=False,
    )

    assert result["solver_failure"] is True
    assert result["target_met"] is False
    assert result["nonfinite_fid_gamma_violation"] is False
    assert result["fet_contract_violation"] is False
    assert result["fet_cut_contract_verdict"] == "SOLVER_FAILED_SAFE_NOOP"


def test_fet_nondegeneracy_rejects_every_all_noop_case() -> None:
    noop = _worker("all-noop")
    red = AUDIT.aggregate_fet_nondegeneracy([noop])
    assert red["verdict"] == "RED"
    assert red["red_case_ids"] == ["all-noop"]
    assert red["per_case"][0]["verdict"] == "RED_ALL_NOOP"
    assert (
        red["per_case"][0][
            "authenticated_rank_reducing_writeback_count"
        ]
        == 0
    )
    assert (
        AUDIT.evaluate_overall_verdict(
            replay_verdict="PASS_SCOPED_BITWISE",
            entropy_red_case_ids=[],
            fet_verdict="PASS",
            solver_health_verdict="PASS",
            nondegeneracy_verdict=red["verdict"],
        )
        == "RED"
    )


def test_fet_nondegeneracy_requires_an_authenticated_writeback_in_each_case() -> None:
    def accepted(case_id: str) -> dict:
        result = _worker(case_id)
        cut = result["per_cut"][0]
        accepted_map = np.diag([1.0, 0.0]).astype(np.complex128)
        raw_hash = AUDIT.array_sha256_c128le(accepted_map)
        projective_hash = AUDIT.projective_array_sha256(accepted_map)
        wrapper = cut["selector_wrapper_evidence"]
        wrapper.update(
            {
                "selected_env_rank": 1,
                "proposed_env_rank": 1,
                "map_rank_axis": 1,
                "attempted_ranks": 1,
                "writeback_call_count": 1,
                "selected_map_sha256_c128le": raw_hash,
                "selected_map_projective_sha256_c128le": projective_hash,
                "applied_map_sha256_c128le": raw_hash,
                "applied_map_projective_sha256_c128le": projective_hash,
                "selected_applied_map_exact_match": True,
                "endpoint_absorption_exact_match": True,
                "expected_left_endpoint_sha256_c128le": "3" * 64,
                "observed_left_endpoint_sha256_c128le": "3" * 64,
                "expected_right_endpoint_sha256_c128le": "4" * 64,
                "observed_right_endpoint_sha256_c128le": "4" * 64,
                "map_frobenius_norm": float(np.linalg.norm(accepted_map)),
                "map_sha256_c128le": raw_hash,
                "map_projective_sha256_c128le": projective_hash,
            }
        )
        ledger = cut["trajectory_ledger_evidence"]
        ledger.update(
            {
                "selected_env_rank": 1,
                "proposed_env_rank": 1,
                "writeback_applied": True,
                "env_rank": 1,
                "dim_out": 1,
                "applied_Fid_gamma": cut["selected_Fid_gamma"],
                "outcome": "accepted",
                "reason": "fidelity_target_met",
                "attempted_ranks": 1,
                "exact_rank": 1,
            }
        )
        for name, value in wrapper.items():
            cut[name] = copy.deepcopy(value)
        cut.update(AUDIT.authenticate_fet_ledger_row(wrapper, ledger))
        cut.update(
            AUDIT.evaluate_fet_cut_contract(
                map_array=accepted_map,
                dim_in=2,
                dim_out=1,
                env_rank=1,
                fid_gamma=cut["Fid_gamma"],
                eps_fid=cut["eps_fid"],
                writeback_applied=True,
            )
        )
        return result

    first = accepted("accepted-a")
    second = accepted("accepted-b")
    passed = AUDIT.aggregate_fet_nondegeneracy([first, second])
    assert passed["verdict"] == "PASS"
    assert passed["red_case_ids"] == []
    assert all(
        row["authenticated_rank_reducing_writeback_count"] == 1
        for row in passed["per_case"]
    )

    one_degenerate_control = AUDIT.aggregate_fet_nondegeneracy(
        [first, _worker("all-noop-control")]
    )
    assert one_degenerate_control["verdict"] == "RED"
    assert one_degenerate_control["red_case_ids"] == ["all-noop-control"]

    unauthenticated = copy.deepcopy(first)
    unauthenticated["case_id"] = "unauthenticated-writeback"
    unauthenticated["per_cut"][0]["trajectory_ledger_authentication"] = {
        "status": "UNAUTHENTICATED"
    }
    unauthenticated_gate = AUDIT.aggregate_fet_nondegeneracy([unauthenticated])
    assert unauthenticated_gate["verdict"] == "RED"
    assert unauthenticated_gate["red_case_ids"] == [
        "unauthenticated-writeback"
    ]

    broken_causal_binding = copy.deepcopy(first)
    broken_causal_binding["case_id"] = "broken-causal-binding"
    broken_cut = broken_causal_binding["per_cut"][0]
    broken_cut["selector_wrapper_evidence"][
        "applied_map_sha256_c128le"
    ] = "f" * 64
    broken_cut["applied_map_sha256_c128le"] = "f" * 64
    broken_gate = AUDIT.aggregate_fet_nondegeneracy([broken_causal_binding])
    assert broken_gate["verdict"] == "RED"
    assert broken_gate["red_case_ids"] == ["broken-causal-binding"]


def test_fail_on_scientific_red_exits_for_nondegeneracy_gate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    nondegeneracy = AUDIT.aggregate_fet_nondegeneracy([_worker("all-noop")])
    overall = AUDIT.evaluate_overall_verdict(
        replay_verdict="PASS_SCOPED_BITWISE",
        entropy_red_case_ids=[],
        fet_verdict="PASS",
        solver_health_verdict="PASS",
        nondegeneracy_verdict=nondegeneracy["verdict"],
    )
    report = {
        "replay_verdict": "PASS_SCOPED_BITWISE",
        "replay_passed": True,
        "entropy_gate": {"verdict": "PASS"},
        "fet_fallback_contract_gate": {"verdict": "PASS"},
        "fet_solver_health_gate": {"verdict": "PASS"},
        "fet_nondegeneracy_gate": nondegeneracy,
        "overall_verdict": overall,
        "content_hash_sha256": "a" * 64,
    }
    monkeypatch.setattr(AUDIT, "build_report", lambda *_args, **_kwargs: report)
    monkeypatch.setattr(AUDIT, "write_json_atomic", lambda *_args: "b" * 64)

    with pytest.raises(SystemExit) as exited:
        AUDIT.main(
            [
                "--output",
                str(tmp_path / "report.json"),
                "--fail-on-scientific-red",
            ]
        )
    assert exited.value.code == 3


def test_nonidentity_rejected_candidate_is_not_misreported_as_applied_mutation() -> None:
    """Explicit applied semantics override candidate-map appearance."""
    candidate = np.diag([1.0, 0.0]).astype(np.complex128)
    result = AUDIT.evaluate_fet_cut_contract(
        map_array=candidate,
        dim_in=2,
        dim_out=2,
        env_rank=2,
        fid_gamma=0.95,
        eps_fid=0.01,
        writeback_applied=False,
    )

    assert result["candidate_map_nonidentity"] is True
    assert result["rank_reducing_writeback"] is False
    assert result["nonidentity_or_lossy_writeback"] is False
    assert result["fallback_contract_violation"] is False
    assert result["fet_cut_contract_verdict"] == "SAFE_NOOP_FALLBACK"


def test_fet_ledger_authentication_uses_independent_selected_and_writeback_evidence() -> None:
    audit = {
        "bond": "B0_1",
        "dim_in": 2,
        "selected_env_rank": 1,
        "proposed_env_rank": 1,
        "map_rank_axis": 1,
        "Fid_gamma": AUDIT.classify_fid_gamma(0.995),
        "selected_Fid_gamma": 0.995,
        "selector_outcome": "accepted",
        "requested_solver_seed": 7,
        "solver_seed": 7,
        "attempted_ranks": 1,
        "solver_failure_count": 0,
        "eps_fid_requested": 0.01,
        "map_shapes_ok": True,
        "map_dtype_ok": True,
        "map_device_ok": True,
        "map_finite": True,
        "fallback_identity_factors": False,
        "writeback_call_count": 1,
        "selected_map_sha256_c128le": "a" * 64,
        "selected_map_projective_sha256_c128le": "b" * 64,
        "map_sha256_c128le": "a" * 64,
        "map_projective_sha256_c128le": "b" * 64,
        "applied_map_sha256_c128le": "a" * 64,
        "applied_map_projective_sha256_c128le": "b" * 64,
        "selected_applied_map_exact_match": True,
        "endpoint_absorption_exact_match": True,
        "expected_left_endpoint_sha256_c128le": "1" * 64,
        "observed_left_endpoint_sha256_c128le": "1" * 64,
        "expected_right_endpoint_sha256_c128le": "2" * 64,
        "observed_right_endpoint_sha256_c128le": "2" * 64,
    }
    ledger = {
        "bond": "B0_1",
        "dim_in": 2,
        "selected_env_rank": 1,
        "proposed_env_rank": 1,
        "Fid_gamma": 0.995,
        "selected_Fid_gamma": 0.995,
        "writeback_applied": True,
        "env_rank": 1,
        "dim_out": 1,
        "applied_Fid_gamma": 0.995,
        "outcome": "accepted",
        "reason": "fidelity_target_met",
        "selector_outcome": "accepted",
        "requested_fet_solver_seed": 7,
        "fet_solver_seed": 7,
        "attempted_ranks": 1,
        "solver_failure_count": 0,
        "fidelity_target": 0.99,
        "candidate_fidelity_valid": True,
        "target_met": True,
        "selected_target_met": True,
        "selected_fidelity_valid": True,
        "selector_consistent": True,
        "selector_metadata_valid": True,
        "solver_seed_consistent": True,
        "fallback_identity_factors": False,
        "map_shapes_ok": True,
        "map_dtype_ok": True,
        "map_device_ok": True,
        "map_finite": True,
        "map_valid": True,
        "exact_rank": 1,
        "eps_fid": 0.01,
    }

    authenticated = AUDIT.authenticate_fet_ledger_row(audit, ledger)
    assert authenticated["env_rank"] == 1
    assert authenticated["applied_Fid_gamma"] == 0.995
    assert authenticated["outcome"] == "accepted"

    for field, corruption in (
        ("env_rank", 2),
        ("applied_Fid_gamma", 1.0),
        ("selected_Fid_gamma", 0.5),
        ("outcome", "noop"),
        ("reason", "invalid_candidate_map"),
        ("selected_target_met", False),
        ("selected_fidelity_valid", False),
        ("selector_consistent", False),
        ("selector_outcome", "noop"),
        ("fet_solver_seed", 8),
        ("attempted_ranks", 2),
        ("solver_failure_count", 1),
    ):
        corrupted = copy.deepcopy(ledger)
        corrupted[field] = corruption
        with pytest.raises(RuntimeError):
            AUDIT.authenticate_fet_ledger_row(audit, corrupted)

    wrong_applied_map = copy.deepcopy(audit)
    wrong_applied_map["applied_map_sha256_c128le"] = "e" * 64
    with pytest.raises(RuntimeError, match="not exactly bound"):
        AUDIT.authenticate_fet_ledger_row(wrong_applied_map, ledger)

    wrong_endpoint = copy.deepcopy(audit)
    wrong_endpoint["observed_left_endpoint_sha256_c128le"] = "5" * 64
    with pytest.raises(RuntimeError, match="written FET endpoints"):
        AUDIT.authenticate_fet_ledger_row(wrong_endpoint, ledger)

    wrong_requested_seed = copy.deepcopy(audit)
    wrong_requested_seed["requested_solver_seed"] = 6
    corrupted_seed_ledger = copy.deepcopy(ledger)
    corrupted_seed_ledger["requested_fet_solver_seed"] = 6
    corrupted_seed_ledger["solver_seed_consistent"] = False
    corrupted_seed_ledger["selector_consistent"] = False
    corrupted_seed_ledger["writeback_applied"] = False
    with pytest.raises(RuntimeError):
        AUDIT.authenticate_fet_ledger_row(
            wrong_requested_seed, corrupted_seed_ledger
        )


def test_fet_ledger_authenticates_quarantined_solver_failure_reason() -> None:
    audit = {
        "bond": "B0_1",
        "dim_in": 2,
        "selected_env_rank": 2,
        "proposed_env_rank": None,
        "map_rank_axis": 2,
        "Fid_gamma": AUDIT.classify_fid_gamma(float("-inf")),
        "selected_Fid_gamma": 1.0,
        "selector_outcome": "solver_failed",
        "requested_solver_seed": 9,
        "solver_seed": 9,
        "attempted_ranks": 2,
        "solver_failure_count": 2,
        "eps_fid_requested": 0.01,
        "map_shapes_ok": True,
        "map_dtype_ok": True,
        "map_device_ok": True,
        "map_finite": True,
        "fallback_identity_factors": True,
        "writeback_call_count": 0,
        "selected_map_sha256_c128le": "c" * 64,
        "selected_map_projective_sha256_c128le": "d" * 64,
        "map_sha256_c128le": "c" * 64,
        "map_projective_sha256_c128le": "d" * 64,
        "applied_map_sha256_c128le": None,
        "applied_map_projective_sha256_c128le": None,
        "selected_applied_map_exact_match": None,
        "endpoint_absorption_exact_match": None,
        "expected_left_endpoint_sha256_c128le": None,
        "observed_left_endpoint_sha256_c128le": None,
        "expected_right_endpoint_sha256_c128le": None,
        "observed_right_endpoint_sha256_c128le": None,
    }
    ledger = {
        "bond": "B0_1",
        "dim_in": 2,
        "selected_env_rank": 2,
        "proposed_env_rank": None,
        "Fid_gamma": float("-inf"),
        "selected_Fid_gamma": 1.0,
        "writeback_applied": False,
        "env_rank": 2,
        "dim_out": 2,
        "applied_Fid_gamma": 1.0,
        "outcome": "solver_failed",
        "reason": "invalid_or_nonfinite_candidate_fidelity",
        "selector_outcome": "solver_failed",
        "requested_fet_solver_seed": 9,
        "fet_solver_seed": 9,
        "attempted_ranks": 2,
        "solver_failure_count": 2,
        "fidelity_target": 0.99,
        "candidate_fidelity_valid": False,
        "target_met": False,
        "selected_target_met": True,
        "selected_fidelity_valid": True,
        "selector_consistent": True,
        "selector_metadata_valid": True,
        "solver_seed_consistent": True,
        "fallback_identity_factors": True,
        "map_shapes_ok": True,
        "map_dtype_ok": True,
        "map_device_ok": True,
        "map_finite": True,
        "map_valid": True,
        "exact_rank": 2,
        "eps_fid": 0.01,
    }

    authenticated = AUDIT.authenticate_fet_ledger_row(audit, ledger)
    assert authenticated["writeback_applied"] is False
    assert authenticated["outcome"] == "solver_failed"


def test_fidelity_curve_observer_authenticates_full_frozen_acceptance() -> None:
    cut = {
        "dim_in": 3,
        "exact_rank": 3,
        "eps_fid": 0.01,
        "selected_env_rank": 2,
        "proposed_env_rank": 2,
        "Fid_gamma": AUDIT.classify_fid_gamma(0.995),
        "selected_Fid_gamma": 0.995,
        "selector_outcome": "accepted",
        "attempted_ranks": 2,
        "solver_failure_count": 1,
        "observer_requested": True,
        "fidelity_curve": [
            {"chi": 1, "fid": None, "solver_status": "solver_failed"},
            {"chi": 2, "fid": 0.995, "solver_status": "ok"},
            {"chi": 3, "fid": 0.999, "solver_status": "ok"},
        ],
    }

    authenticated = AUDIT.validate_fidelity_curve_observation(cut)
    assert authenticated == {
        "status": "AUTHENTICATED_FULL_SWEEP",
        "observer_requested": True,
        "curve_row_count": 3,
        "expected_full_rank_count": 3,
        "first_qualifying_rank": 2,
    }

    corruptions = []
    empty = copy.deepcopy(cut)
    empty["fidelity_curve"] = []
    corruptions.append(empty)
    partial = copy.deepcopy(cut)
    partial["fidelity_curve"].pop()
    corruptions.append(partial)
    noncontiguous = copy.deepcopy(cut)
    noncontiguous["fidelity_curve"][1]["chi"] = 3
    corruptions.append(noncontiguous)
    failed_with_value = copy.deepcopy(cut)
    failed_with_value["fidelity_curve"][0]["fid"] = 0.1
    corruptions.append(failed_with_value)
    wrong_selected_fid = copy.deepcopy(cut)
    wrong_selected_fid["selected_Fid_gamma"] = 0.996
    corruptions.append(wrong_selected_fid)
    wrong_attempt_count = copy.deepcopy(cut)
    wrong_attempt_count["attempted_ranks"] = 3
    corruptions.append(wrong_attempt_count)
    earlier_qualifier = copy.deepcopy(cut)
    earlier_qualifier["fidelity_curve"][0] = {
        "chi": 1,
        "fid": 0.999,
        "solver_status": "ok",
    }
    corruptions.append(earlier_qualifier)

    for corrupted in corruptions:
        with pytest.raises(RuntimeError):
            AUDIT.validate_fidelity_curve_observation(corrupted)


def test_fidelity_curve_observer_authenticates_no_qualifier_and_all_failed() -> None:
    rejected = {
        "dim_in": 3,
        "exact_rank": 3,
        "eps_fid": 0.01,
        "selected_env_rank": 3,
        "proposed_env_rank": 2,
        "Fid_gamma": AUDIT.classify_fid_gamma(0.98),
        "selected_Fid_gamma": 1.0,
        "selector_outcome": "noop",
        "attempted_ranks": 3,
        "solver_failure_count": 1,
        "observer_requested": True,
        "fidelity_curve": [
            {"chi": 1, "fid": None, "solver_status": "solver_failed"},
            {"chi": 2, "fid": 0.98, "solver_status": "ok"},
            {"chi": 3, "fid": 0.97, "solver_status": "ok"},
        ],
    }
    observed = AUDIT.validate_fidelity_curve_observation(rejected)
    assert observed["first_qualifying_rank"] is None

    hidden_qualifier = copy.deepcopy(rejected)
    hidden_qualifier["fidelity_curve"][2]["fid"] = 0.995
    with pytest.raises(RuntimeError, match="qualifying"):
        AUDIT.validate_fidelity_curve_observation(hidden_qualifier)

    all_failed = copy.deepcopy(rejected)
    all_failed.update(
        {
            "proposed_env_rank": None,
            "Fid_gamma": AUDIT.classify_fid_gamma(float("-inf")),
            "selector_outcome": "solver_failed",
            "solver_failure_count": 3,
            "fidelity_curve": [
                {"chi": chi, "fid": None, "solver_status": "solver_failed"}
                for chi in range(1, 4)
            ],
        }
    )
    assert AUDIT.validate_fidelity_curve_observation(all_failed)["status"] == (
        "AUTHENTICATED_FULL_SWEEP"
    )


def test_fidelity_curve_observer_cannot_be_vacuous_or_run_unrequested() -> None:
    not_requested = {
        "observer_requested": False,
        "fidelity_curve": None,
    }
    assert AUDIT.validate_fidelity_curve_observation(not_requested)["status"] == (
        "AUTHENTICATED_NOT_REQUESTED"
    )

    populated = copy.deepcopy(not_requested)
    populated["fidelity_curve"] = []
    with pytest.raises(RuntimeError, match="not requested"):
        AUDIT.validate_fidelity_curve_observation(populated)

    worker = _worker("observer", debug=1)
    cut = worker["per_cut"][0]
    cut.update(
        {
            "observer_requested": True,
            "attempted_ranks": 2,
            "solver_failure_count": 1,
            "fidelity_curve": [
                {"chi": 1, "fid": None, "solver_status": "solver_failed"},
                {
                    "chi": 2,
                    "fid": cut["selected_Fid_gamma"],
                    "solver_status": "ok",
                },
            ],
        }
    )
    cut["selector_wrapper_evidence"].update(
        {
            "observer_requested": True,
            "attempted_ranks": 2,
            "solver_failure_count": 1,
            "fidelity_curve": copy.deepcopy(cut["fidelity_curve"]),
        }
    )
    cut["trajectory_ledger_evidence"].update(
        {"attempted_ranks": 2, "solver_failure_count": 1}
    )
    cut.update(
        AUDIT.authenticate_fet_ledger_row(
            cut["selector_wrapper_evidence"],
            cut["trajectory_ledger_evidence"],
        )
    )
    cut["fidelity_curve_observation"] = (
        AUDIT.validate_fidelity_curve_observation(cut)
    )
    AUDIT.validate_worker_arrays(worker, _arrays())

    cut["fidelity_curve"] = []
    with pytest.raises(RuntimeError, match="fidelity_curve|no rows"):
        AUDIT.validate_worker_arrays(worker, _arrays())


def test_worker_array_authentication_accepts_exact_evidence() -> None:
    authenticated = AUDIT.validate_worker_arrays(_worker("case"), _arrays())
    assert authenticated["status"] == "AUTHENTICATED"
    assert authenticated["exact_keys"] == ["map_0000", "round_state"]
    map_norm = authenticated["arrays"]["map_0000"][
        "frobenius_norm_authentication"
    ]
    assert map_norm["passed"] is True
    assert map_norm["torch_recorded"] == map_norm["numpy_recomputed"]
    assert map_norm["abs_delta"] == 0.0
    assert map_norm["absolute_tolerance"] == AUDIT.NORM_AUTH_ABS_TOL
    assert map_norm["relative_tolerance"] == AUDIT.NORM_AUTH_REL_TOL


def test_cross_backend_norm_gate_is_scale_aware_and_rejects_corruption() -> None:
    large = 1.0e8
    close = AUDIT.evaluate_cross_backend_norm(
        torch_recorded=large,
        numpy_recomputed=large + 5.0e-5,
    )
    assert close["passed"] is True
    assert close["abs_delta"] == (large + 5.0e-5) - large
    assert close["relative_delta"] < AUDIT.NORM_AUTH_REL_TOL
    assert close["absolute_tolerance"] == AUDIT.NORM_AUTH_ABS_TOL
    assert close["relative_tolerance"] == AUDIT.NORM_AUTH_REL_TOL

    corrupted = AUDIT.evaluate_cross_backend_norm(
        torch_recorded=1.0,
        numpy_recomputed=1.0 + 1.0e-6,
    )
    assert corrupted["passed"] is False
    assert corrupted["relative_delta"] > AUDIT.NORM_AUTH_REL_TOL


def test_worker_array_authentication_rejects_payload_corruptions() -> None:
    corruptions = []

    missing = _arrays()
    missing.pop("map_0000")
    corruptions.append((_worker("missing"), missing))

    extra = _arrays()
    extra["unexpected"] = np.ones(1, dtype=np.complex128)
    corruptions.append((_worker("extra"), extra))

    wrong_dtype = _arrays()
    wrong_dtype["map_0000"] = wrong_dtype["map_0000"].astype(np.complex64)
    corruptions.append((_worker("dtype"), wrong_dtype))

    nonfinite = _arrays()
    nonfinite["map_0000"] = nonfinite["map_0000"].copy()
    nonfinite["map_0000"][0, 0] = np.nan
    corruptions.append((_worker("nonfinite"), nonfinite))

    wrong_shape = _arrays()
    wrong_shape["map_0000"] = wrong_shape["map_0000"].reshape(-1)
    corruptions.append((_worker("shape"), wrong_shape))

    wrong_hash_report = _worker("hash")
    wrong_hash_report["per_cut"][0]["map_sha256_c128le"] = "0" * 64
    corruptions.append((wrong_hash_report, _arrays()))

    wrong_norm_report = _worker("norm")
    wrong_norm_report["per_cut"][0]["map_frobenius_norm"] *= 1.01
    corruptions.append((wrong_norm_report, _arrays()))

    wrong_contract_report = _worker("contract")
    wrong_contract_report["per_cut"][0]["target_met"] = False
    corruptions.append((wrong_contract_report, _arrays()))

    malformed_fid_report = _worker("fid-schema")
    malformed_fid_report["per_cut"][0]["Fid_gamma"] = {
        "classification": "negative_infinity",
        "value": 0.0,
        "raw_repr": "-inf",
    }
    corruptions.append((malformed_fid_report, _arrays()))

    for field, value in (
        ("selected_Fid_gamma", 0.123),
        ("selected_env_rank", 777),
        ("outcome", "accepted"),
        ("reason", "fidelity_target_met"),
        ("writeback_call_count", 1),
        ("solver_failure_count", 99),
        ("map_rank_axis", 999),
    ):
        forged = _worker(f"forged-{field}")
        forged["per_cut"][0][field] = value
        corruptions.append((forged, _arrays()))

    for report, arrays in corruptions:
        with pytest.raises(RuntimeError):
            AUDIT.validate_worker_arrays(report, arrays)


def test_comparison_classifies_bitwise_and_numerical_replay() -> None:
    baseline = _worker("baseline")
    repeat = _worker("repeat")
    exact = AUDIT.compare_worker_results(
        baseline, repeat, _arrays(), _arrays()
    )
    assert exact["kind"] == "fresh_process_repeat"
    assert exact["verdict"] == "PASS_SCOPED_BITWISE"

    phase_shifted_arrays = _arrays(
        map_array=_arrays()["map_0000"] * 1.0j,
        state=_arrays()["round_state"] * (-2.0j),
    )
    phase_shifted = copy.deepcopy(repeat)
    phase_shifted["per_cut"][0]["map_sha256_c128le"] = AUDIT.array_sha256_c128le(
        phase_shifted_arrays["map_0000"]
    )
    phase_shifted["round_state"]["sha256_c128le"] = AUDIT.array_sha256_c128le(
        phase_shifted_arrays["round_state"]
    )
    numeric = AUDIT.compare_worker_results(
        baseline, phase_shifted, _arrays(), phase_shifted_arrays
    )
    assert numeric["verdict"] == "PASS_SCOPED_NUMERIC_NOT_BITWISE"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("outcome", "accepted"),
        ("reason", "fidelity_target_met"),
        ("selected_env_rank", 1),
        ("selected_Fid_gamma", 0.123),
        ("applied_Fid_gamma", 0.123),
        ("writeback_call_count", 1),
        ("solver_failure_count", 1),
    ],
)
def test_numeric_replay_never_ignores_selector_or_applied_evidence(
    field: str, value: object
) -> None:
    baseline = _worker("baseline")
    candidate = _worker("candidate", seed=1)
    candidate["per_cut"][0][field] = value

    comparison = AUDIT.compare_worker_results(
        baseline, candidate, _arrays(), _arrays()
    )

    assert comparison["verdict"] == "FAIL_DIVERGED"
    if field not in ("selected_Fid_gamma", "applied_Fid_gamma"):
        assert comparison["same_scoped_categorical_capture"] is False


def test_comparison_detects_rank_map_and_entropy_corruptions() -> None:
    baseline = _worker("baseline")
    candidate = _worker("seed-control", seed=1)
    corruptions = []

    wrong_rank = copy.deepcopy(candidate)
    wrong_rank["per_cut"][0]["env_rank"] = 1
    corruptions.append((wrong_rank, _arrays()))

    wrong_map = _arrays()
    wrong_map["map_0000"] = wrong_map["map_0000"].copy()
    wrong_map["map_0000"][0, 1] = 0.1
    map_report = copy.deepcopy(candidate)
    map_report["per_cut"][0]["map_sha256_c128le"] = AUDIT.array_sha256_c128le(
        wrong_map["map_0000"]
    )
    corruptions.append((map_report, wrong_map))

    wrong_entropy = copy.deepcopy(candidate)
    wrong_entropy["entropy_gate"]["S_A"] += 1.0e-3
    corruptions.append((wrong_entropy, _arrays()))

    wrong_record = copy.deepcopy(candidate)
    wrong_record["record_payload_sha256"] = "b" * 64
    corruptions.append((wrong_record, _arrays()))

    for report, arrays in corruptions:
        comparison = AUDIT.compare_worker_results(
            baseline, report, _arrays(), arrays
        )
        assert comparison["verdict"] == "FAIL_DIVERGED"
        assert AUDIT.summarize_replay([comparison]) == "FAIL_CUDA_SEED_SENSITIVE"


def test_content_hash_and_atomic_writer_are_corruption_sensitive(tmp_path: Path) -> None:
    report = {
        "schema": AUDIT.SCHEMA,
        "replay_verdict": "PASS_SCOPED_BITWISE",
        "cases": [{"entropy_gate": {"S_A": 0.25}}],
    }
    report["content_hash_sha256"] = AUDIT.report_content_hash(report)
    assert report["content_hash_sha256"] == AUDIT.report_content_hash(report)

    corrupted = copy.deepcopy(report)
    corrupted["cases"][0]["entropy_gate"]["S_A"] = 0.5
    assert AUDIT.report_content_hash(corrupted) != report["content_hash_sha256"]

    destination = tmp_path / "nested" / "report.json"
    byte_hash = AUDIT.write_json_atomic(destination, report)
    assert byte_hash == AUDIT.sha256_bytes(destination.read_bytes())
    assert not list(destination.parent.glob(f".{destination.name}.*"))
