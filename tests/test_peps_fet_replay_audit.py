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
        "map_rank_axis": 2,
        "Fid_gamma": AUDIT.classify_fid_gamma(0.999999999),
        "map_frobenius_norm": float(np.linalg.norm(map_array)),
        "eps_fid": AUDIT.EPS_FID,
        "map_sha256_c128le": AUDIT.array_sha256_c128le(map_array),
        "map_projective_sha256_c128le": (
            AUDIT.projective_array_sha256(map_array)
        ),
    }
    cut.update(
        AUDIT.evaluate_fet_cut_contract(
            map_array=map_array,
            dim_in=cut["dim_in"],
            dim_out=cut["dim_out"],
            env_rank=cut["env_rank"],
            fid_gamma=cut["Fid_gamma"],
            eps_fid=cut["eps_fid"],
        )
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
        )
        == "RED"
    )


def test_nonfinite_fid_gamma_is_json_safe_and_forces_every_gate_red() -> None:
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
    assert nonfinite["per_cut"][0]["nonfinite_fid_gamma_violation"] is True
    assert nonfinite["per_cut"][0]["fet_contract_violation"] is True
    AUDIT.canonical_json_bytes(nonfinite)
    AUDIT.validate_worker_arrays(nonfinite, _arrays())

    aggregate = AUDIT.aggregate_fet_fallback_contract([nonfinite])
    assert aggregate["verdict"] == "RED"
    assert aggregate["nonfinite_fid_gamma_count"] == 1
    assert (
        AUDIT.evaluate_overall_verdict(
            replay_verdict="PASS_SCOPED_BITWISE",
            entropy_red_case_ids=[],
            fet_verdict=aggregate["verdict"],
        )
        == "RED"
    )

    finite = _worker("finite")
    mismatch = AUDIT.compare_worker_results(
        finite, nonfinite, _arrays(), _arrays()
    )
    assert mismatch["same_Fid_gamma_classification_sequence"] is False
    assert mismatch["verdict"] == "FAIL_NONFINITE_FID_GAMMA"

    repeat_nonfinite = with_fid(_worker("repeat-nonfinite"), float("-inf"))
    deterministic = AUDIT.compare_worker_results(
        nonfinite, repeat_nonfinite, _arrays(), _arrays()
    )
    assert deterministic["same_Fid_gamma_classification_sequence"] is True
    assert deterministic["verdict"] == "FAIL_NONFINITE_FID_GAMMA"
    assert AUDIT.summarize_replay([deterministic]) == "FAIL_NONFINITE_FID_GAMMA"


def test_worker_array_authentication_accepts_exact_evidence() -> None:
    authenticated = AUDIT.validate_worker_arrays(_worker("case"), _arrays())
    assert authenticated["status"] == "AUTHENTICATED"
    assert authenticated["exact_keys"] == ["map_0000", "round_state"]


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
