from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
COMPARATOR = (
    ROOT
    / "scripts"
    / "external_baselines"
    / "compare_gcapeps_finite_memory_bond32.py"
)
EMITTER = (
    ROOT
    / "scripts"
    / "external_baselines"
    / "emit_gcapeps_finite_memory_fixture.py"
)
DENSE = (
    ROOT
    / "scripts"
    / "external_baselines"
    / "gcapeps_finite_memory_dense_reference.py"
)
OUTER_TEST = (
    ROOT
    / "tests"
    / "test_external_gcapeps_finite_memory_outer_orchestration.py"
)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _rehash(core, comparator):
    core["result_projection_sha256"] = comparator.projection_sha256(core)


@pytest.fixture(scope="module")
def zero_ensemble_dense_bundle():
    comparator = _load(COMPARATOR, "_terminal_gates_comparator")
    emitter = _load(EMITTER, "_terminal_gates_emitter")
    dense = _load(DENSE, "_terminal_gates_dense")
    fixture = emitter.build_fixture(
        run_partition="HELDOUT",
        width=3,
        rounds=1,
        axis_family=3,
        p_event_numerator=0,
        seed=emitter.HELDOUT_SEED,
        gamma_index=0,
        run_blpensemble=True,
    )
    core = dense.build_core_payload(fixture)
    identity = comparator._validate_fixture_identity(fixture)
    sampler = comparator.ComparatorArraySampler()
    digest, vectors, witnesses = comparator._validate_dense_core(
        core,
        identity=identity,
        fixture=fixture,
        sampler=sampler,
    )
    del digest
    comparator._validate_exact_dense_memory_witnesses(
        witnesses,
        width=3,
        rounds=1,
    )
    comparator._arrays_released(
        sampler,
        *[
            vector
            for by_round in vectors.values()
            for vector in by_round.values()
        ],
    )
    assert sampler.current_bytes == 0
    return comparator, fixture, core, witnesses


def test_dense_terminal_recomputes_fixed_ensemble_control_and_entropy(
    zero_ensemble_dense_bundle,
):
    _, _, _, witnesses = zero_ensemble_dense_bundle
    assert witnesses["fixed_blp"]["trace_distances"] == [1.0, 1.0]
    assert witnesses["finite_32_mask_ensemble_blp"]["trace_distances"] == [
        1.0,
        1.0,
    ]
    assert witnesses["p_event_zero_control"]["passed"] is True
    entropy = witnesses["trajectory1_entanglement"]
    assert entropy["source"] == "exact_dense_fixed_carrier_input1"
    assert entropy["candidate_values_consumed"] is False
    assert entropy[
        "h_e_applicability_deferred_to_amendment_bound_stress_cell"
    ] is True
    assert entropy[
        "conditional_h_e_verdict_if_amendment_bound_stress_cell"
    ] == "falsified"


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("fixed_blp", "maximum_increment"),
        ("ensemble_blp", "maximum_increment"),
        ("ensemble_policy", "aggregation policy"),
        ("p0_omission", "control is missing"),
        ("entropy", "diagnostics disagree"),
    ),
)
def test_dense_terminal_rejects_corrupted_or_omitted_registered_evidence(
    zero_ensemble_dense_bundle,
    mutation,
    message,
):
    comparator, fixture, original, _ = zero_ensemble_dense_bundle
    core = copy.deepcopy(original)
    if mutation == "fixed_blp":
        core["fixed_blp"]["maximum_increment"] = 1.0e-3
    elif mutation == "ensemble_blp":
        core["finite_32_mask_ensemble"]["blp"][
            "maximum_increment"
        ] = 1.0e-3
    elif mutation == "ensemble_policy":
        core["finite_32_mask_ensemble"][
            "aggregation_order"
        ] = "average_pathwise_trace_distances"
    elif mutation == "p0_omission":
        core["p_event_zero_control"] = None
    else:
        core["fixed_paths"][0]["checkpoints"][1]["entropy_s1"] += 1.0e-3
    _rehash(core, comparator)
    with pytest.raises(ValueError, match=message):
        comparator._validate_dense_core(
            core,
            identity=comparator._validate_fixture_identity(fixture),
            fixture=fixture,
            sampler=comparator.ComparatorArraySampler(),
        )


@pytest.mark.parametrize(
    "mutation",
    ("omit_witness_member", "corrupt_blp_spectrum", "corrupt_schmidt"),
)
def test_exact_dense_witness_validator_rejects_omission_and_corruption(
    zero_ensemble_dense_bundle,
    mutation,
):
    comparator, _, _, witnesses = zero_ensemble_dense_bundle
    exact = copy.deepcopy(witnesses)
    comparator._validate_exact_dense_memory_witnesses(
        exact,
        width=3,
        rounds=1,
    )
    if mutation == "omit_witness_member":
        del exact["fixed_blp"]
    elif mutation == "corrupt_blp_spectrum":
        exact["fixed_blp"]["difference_eigenvalues_by_round"][0][0] += 1.0e-3
    else:
        exact["trajectory1_entanglement"][
            "normalized_schmidt_values_by_round"
        ][0][0] = 0.9
    with pytest.raises(ValueError):
        comparator._validate_exact_dense_memory_witnesses(
            exact,
            width=3,
            rounds=1,
        )


def _blp(object_name: str, rounds: int):
    distances = [1.0] * (rounds + 1)
    increments = [0.0] * rounds
    ensemble = object_name == "finite_32_mask_ensemble"
    return {
        "object": object_name,
        "trace_distances": distances,
        "increments": increments,
        "summed_positive_increments": 0.0,
        "maximum_increment": 0.0,
        "witness_threshold": 1.0e-10,
        "verdict": (
            "NO_WITNESS_FINITE_32_MASK_ENSEMBLE_FOR_REGISTERED_PAIR"
            if ensemble
            else "NO_WITNESS_FIXED_MASK_FOR_REGISTERED_PAIR"
        ),
        "difference_eigenvalues_by_round": [[] for _ in distances],
    }


def _control():
    return {
        "every_event_bit_structural_false": True,
        "active_axis_rotation_count": 0,
        "all_system_memory_s1_s2_at_most_1e_12": True,
        "fixed_trace_distance_one_within_1e_12": True,
        "fixed_named_increment_at_most_1e_10": True,
        "ensemble_trace_distance_one_within_1e_12": True,
        "ensemble_named_increment_at_most_1e_10": True,
        "passed": True,
    }


def _entropy(s1):
    increments = [
        float(s1[index] - s1[index - 1])
        for index in range(1, len(s1))
    ]
    delta = float(s1[-1] - s1[1])
    return {
        "source": "exact_dense_fixed_carrier_input1",
        "candidate_values_consumed": False,
        "round_indices": list(range(len(s1))),
        "entropy_von_neumann": s1,
        "entropy_renyi2": list(s1),
        "normalized_schmidt_values_by_round": [[] for _ in s1],
        "numerical_schmidt_rank_by_round": [1 for _ in s1],
        "entropy_von_neumann_increments": increments,
        "negative_increment_rows": [
            {"round_index": index, "increment": value}
            for index, value in enumerate(increments, start=1)
            if value < 0.0
        ],
        "revival_rows": [
            {"round_index": index, "increment": value}
            for index, value in enumerate(increments, start=1)
            if value > 0.0
        ],
        "maximum_entropy_von_neumann": max(s1),
        "terminal_entropy_von_neumann": s1[-1],
        "round1_entropy_von_neumann": s1[1],
        "terminal_minus_round1": delta,
        "h_e_strict_threshold": 1.0e-10,
        "h_e_condition_holds": delta > 1.0e-10,
        "conditional_h_e_verdict_if_amendment_bound_stress_cell": (
            "supported" if delta > 1.0e-10 else "falsified"
        ),
        "h_e_applicability_deferred_to_amendment_bound_stress_cell": True,
    }


def _acceptance_core(
    cell_row,
    s1,
    *,
    minimum_plain=0.8,
    minimum_gc=0.8,
    shared_positive=True,
):
    width, rounds, _, numerator, _ = cell_row["cell"]
    ensemble = (
        _blp("finite_32_mask_ensemble", rounds)
        if cell_row["run_blpensemble"]
        else None
    )
    delta_f = minimum_gc - minimum_plain
    direction = (
        "gcapeps_higher"
        if delta_f > 1.0e-10
        else "plain_higher"
        if delta_f < -1.0e-10
        else "tie"
    )
    return {
        "fixture_identity": {
            "run_partition": "HELDOUT",
            "case_id": cell_row["case_id"],
            "width": width,
            "rounds": rounds,
        },
        "positive_bond32_gate": {
            "all_four_paths_positive": shared_positive,
        },
        "exact_dense_memory_witnesses": {
            "fixed_blp": _blp("fixed_carrier_mask", rounds),
            "finite_32_mask_ensemble_blp": ensemble,
            "p_event_zero_control": _control() if numerator == 0 else None,
            "trajectory1_entanglement": _entropy(s1),
        },
        "final_bond32_faithfulness": {
            "round_index": rounds,
            "delta_f": {
                "minimum_plain_fidelity": minimum_plain,
                "minimum_gcapeps_fidelity": minimum_gc,
                "delta_fidelity": delta_f,
                "tie_tolerance": 1.0e-10,
                "direction": direction,
            },
            "per_path_class": {},
            "shared_positive_truncation_eligible": shared_positive,
            "conditional_h_f_verdict_if_amendment_bound_stress_cell": (
                "INELIGIBLE_NO_SHARED_POSITIVE_TRUNCATION"
                if not shared_positive
                else "supported"
                if direction == "gcapeps_higher"
                else "falsified"
                if direction == "plain_higher"
                else "tie/inconclusive"
            ),
            "h_f_applicability_deferred_to_amendment_bound_stress_cell": True,
        },
    }


@pytest.fixture(scope="module")
def terminal_amendment():
    outer = _load(OUTER_TEST, "_terminal_gates_outer_helpers")
    module = outer._module()
    return module, outer._amendment(module)


def test_h_e_is_assigned_only_at_stress_cell_and_need_not_be_monotone(
    terminal_amendment,
):
    module, amendment = terminal_amendment
    stress_index, stress_row = next(
        (index, row)
        for index, row in enumerate(amendment["heldout"]["cell_list"])
        if row["cell"] == [7, 4, 3, 3, 4]
    )
    supported = module.classify_terminal_cell_science(
        amendment=amendment,
        cell_index=stress_index,
        comparator_terminal_kind="completed_result",
        comparator_core=_acceptance_core(
            stress_row,
            [0.0, 0.1, 0.2, 0.15, 0.3],
        ),
    )
    h_e = supported["scientific_evidence"]["h_e"]
    assert h_e["verdict"] == "supported"
    assert h_e["monotonic_step_claim"] is False
    assert supported[
        "candidate_worker_truth_consumed_for_blp_or_h_e"
    ] is False

    falsified = module.classify_terminal_cell_science(
        amendment=amendment,
        cell_index=stress_index,
        comparator_terminal_kind="completed_result",
        comparator_core=_acceptance_core(
            stress_row,
            [0.0, 0.2, 0.3, 0.25, 0.2],
        ),
    )
    assert falsified["scientific_evidence"]["h_e"]["verdict"] == "falsified"

    descriptive_index, descriptive_row = next(
        (index, row)
        for index, row in enumerate(amendment["heldout"]["cell_list"])
        if row["cell"] != [7, 4, 3, 3, 4]
        and row["cell"][3] != 0
    )
    rounds = descriptive_row["cell"][1]
    descriptive = module.classify_terminal_cell_science(
        amendment=amendment,
        cell_index=descriptive_index,
        comparator_terminal_kind="completed_result",
        comparator_core=_acceptance_core(
            descriptive_row,
            [0.0] + [0.2] * rounds,
        ),
    )
    assert (
        descriptive["scientific_evidence"]["h_e"]["verdict"]
        == "DESCRIPTIVE_NOT_APPLICABLE"
    )
    assert (
        descriptive["scientific_evidence"]["h_f"]["verdict"]
        == "DESCRIPTIVE_NOT_APPLICABLE"
    )


@pytest.mark.parametrize(
    ("minimum_plain", "minimum_gc", "shared_positive", "expected"),
    (
        (0.7, 0.8, True, "supported"),
        (0.8, 0.7, True, "falsified"),
        (0.8, 0.8, True, "tie/inconclusive"),
        (
            0.7,
            0.8,
            False,
            "INELIGIBLE_NO_SHARED_POSITIVE_TRUNCATION",
        ),
    ),
)
def test_h_f_is_classified_only_by_amendment_bound_stress_cell(
    terminal_amendment,
    minimum_plain,
    minimum_gc,
    shared_positive,
    expected,
):
    module, amendment = terminal_amendment
    stress_index, stress_row = next(
        (index, row)
        for index, row in enumerate(amendment["heldout"]["cell_list"])
        if row["cell"] == [7, 4, 3, 3, 4]
    )
    result = module.classify_terminal_cell_science(
        amendment=amendment,
        cell_index=stress_index,
        comparator_terminal_kind="completed_result",
        comparator_core=_acceptance_core(
            stress_row,
            [0.0, 0.1, 0.2, 0.15, 0.3],
            minimum_plain=minimum_plain,
            minimum_gc=minimum_gc,
            shared_positive=shared_positive,
        ),
    )
    h_f = result["scientific_evidence"]["h_f"]
    assert h_f["applicable_only_to_registered_stress_cell"] is True
    assert h_f["verdict"] == expected

@pytest.mark.parametrize(
    "mutation",
    (
        "omit_final",
        "delta_mismatch",
        "direction_mismatch",
        "conditional_verdict_mismatch",
        "minimum_out_of_range",
        "shared_gate_mismatch",
        "round_mismatch",
    ),
)
def test_terminal_h_f_trust_seam_rejects_corrupted_evidence(
    terminal_amendment,
    mutation,
):
    module, amendment = terminal_amendment
    stress_index, stress_row = next(
        (index, row)
        for index, row in enumerate(amendment["heldout"]["cell_list"])
        if row["cell"] == [7, 4, 3, 3, 4]
    )
    core = _acceptance_core(
        stress_row,
        [0.0, 0.1, 0.2, 0.15, 0.3],
        minimum_plain=0.7,
        minimum_gc=0.8,
    )
    if mutation == "omit_final":
        core.pop("final_bond32_faithfulness")
    elif mutation == "delta_mismatch":
        core["final_bond32_faithfulness"]["delta_f"]["delta_fidelity"] = 0.2
    elif mutation == "direction_mismatch":
        core["final_bond32_faithfulness"]["delta_f"]["direction"] = "tie"
    elif mutation == "conditional_verdict_mismatch":
        core["final_bond32_faithfulness"][
            "conditional_h_f_verdict_if_amendment_bound_stress_cell"
        ] = "falsified"
    elif mutation == "minimum_out_of_range":
        core["final_bond32_faithfulness"]["delta_f"][
            "minimum_gcapeps_fidelity"
        ] = 1.1
    elif mutation == "shared_gate_mismatch":
        core["final_bond32_faithfulness"][
            "shared_positive_truncation_eligible"
        ] = False
    else:
        core["final_bond32_faithfulness"]["round_index"] += 1
    with pytest.raises(ValueError):
        module.classify_terminal_cell_science(
            amendment=amendment,
            cell_index=stress_index,
            comparator_terminal_kind="completed_result",
            comparator_core=core,
        )





def test_terminal_classification_rejects_p0_control_omission_and_separates_censors(
    terminal_amendment,
):
    module, amendment = terminal_amendment
    zero_index, zero_row = next(
        (index, row)
        for index, row in enumerate(amendment["heldout"]["cell_list"])
        if row["cell"][3] == 0
    )
    rounds = zero_row["cell"][1]
    core = _acceptance_core(zero_row, [0.0] * (rounds + 1))
    core["exact_dense_memory_witnesses"]["p_event_zero_control"] = None
    with pytest.raises(ValueError, match="did not pass"):
        module.classify_terminal_cell_science(
            amendment=amendment,
            cell_index=zero_index,
            comparator_terminal_kind="completed_result",
            comparator_core=core,
        )

    invalid = module.classify_terminal_cell_science(
        amendment=amendment,
        cell_index=zero_index,
        comparator_terminal_kind="invalid_control",
        comparator_core=None,
    )
    assert invalid["scientific_class"] == module.HELDOUT_INVALID
    censored = module.classify_terminal_cell_science(
        amendment=amendment,
        cell_index=zero_index,
        comparator_terminal_kind="worker_censor",
        comparator_core=None,
    )
    assert censored["scientific_class"] == "INCOMPLETE_CENSORED"
