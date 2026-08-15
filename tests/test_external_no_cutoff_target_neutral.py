"""Public contracts for the route-neutral no-cutoff target program."""

from __future__ import annotations


def test_d3_r1_lowering_owns_the_frozen_record_program() -> None:
    from scripts.external_baselines.no_cutoff_target_lowering.neutral import (
        lower_frozen_declared_error_record,
    )

    program = lower_frozen_declared_error_record(distance=3, rounds=1)
    data = program.to_data()
    semantic = data["semantic"]

    assert data["_schema"] == (
        "error_coupling_simulator.external.declared_error_record_program.v1"
    )
    assert data["scope"] == "STATIC_TARGET_LOWERING_ONLY"
    assert semantic["source"]["source_text_sha256"] == (
        "c5401c047aec554d7a4f34b84223e7009a120db9e7131d58259370299d082403"
    )
    assert [q["stim_id"] for q in semantic["qubits"]] == [
        1,
        2,
        3,
        5,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        25,
    ]
    assert len(semantic["events"]) == 156
    assert sum(e["kind"] == "COHERENT_Z" for e in semantic["events"]) == 56
    assert semantic["record_schema"] == {
        "detector_count": 8,
        "observable_indices": [0],
        "outputs": [
            {
                "kind": "DETECTOR",
                "ordinal": ordinal,
                "producer_event_id": next(
                    event["event_id"]
                    for event in semantic["events"]
                    if event["record_output"]
                    == {"kind": "DETECTOR", "ordinal": ordinal}
                ),
            }
            for ordinal in range(8)
        ]
        + [
            {
                "kind": "OBSERVABLE",
                "ordinal": 0,
                "producer_event_id": semantic["events"][-1]["event_id"],
            }
        ],
        "raw_measurement_count": 17,
        "record_width": 9,
    }
    assert semantic["events"][-1]["kind"] == "FINALIZE_RECORD"
    assert "selected_sign" not in repr(data)


def test_all_frozen_cells_match_the_independent_source_text_oracle() -> None:
    from scripts.external_baselines.no_cutoff_target_lowering.independent_source_oracle import (
        reconstruct_source_facts,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.neutral import (
        lower_frozen_declared_error_record,
    )

    expected = {
        (3, 1): (17, 17, 8, 9, 56, 156),
        (3, 3): (17, 33, 24, 25, 168, 378),
        (3, 5): (17, 49, 40, 41, 280, 600),
        (3, 7): (17, 65, 56, 57, 392, 822),
        (5, 1): (49, 49, 24, 25, 184, 468),
        (5, 3): (49, 97, 72, 73, 552, 1154),
        (5, 5): (49, 145, 120, 121, 920, 1840),
        (5, 7): (49, 193, 168, 169, 1288, 2526),
    }
    for cell, frozen in expected.items():
        program = lower_frozen_declared_error_record(
            distance=cell[0], rounds=cell[1]
        )
        semantic = program.to_data()["semantic"]
        independent = reconstruct_source_facts(semantic["source"]["source_text"])
        observed = (
            len(semantic["qubits"]),
            semantic["record_schema"]["raw_measurement_count"],
            semantic["record_schema"]["detector_count"],
            semantic["record_schema"]["record_width"],
            sum(event["kind"] == "COHERENT_Z" for event in semantic["events"]),
            len(semantic["events"]),
        )
        assert observed == frozen
        assert independent == {
            "coherent_occurrences": frozen[4],
            "declared_qubits": [q["stim_id"] for q in semantic["qubits"]],
            "detectors": frozen[2],
            "program_events": frozen[5],
            "raw_measurements": frozen[1],
            "record_width": frozen[3],
            "resolved_record_operands": [
                [
                    operand["absolute_raw_ordinal"]
                    for operand in event["rec_operands"]
                ]
                for event in semantic["events"]
                if event["kind"] in {"DETECTOR_APPEND", "OBSERVABLE_XOR"}
            ],
        }


def test_neutral_reload_rejects_selected_evaluator_truth_even_with_a_fresh_hash() -> None:
    from copy import deepcopy

    import pytest

    from scripts.external_baselines.no_cutoff_target_lowering.model import sha256_json
    from scripts.external_baselines.no_cutoff_target_lowering.neutral import (
        lower_frozen_declared_error_record,
        validate_declared_error_record_program,
    )

    corrupted = deepcopy(
        lower_frozen_declared_error_record(distance=3, rounds=1).to_data()
    )
    corrupted["semantic"]["process"]["latent"]["selected_sign"] = 1
    corrupted["semantic_sha256"] = sha256_json(corrupted["semantic"])

    with pytest.raises(ValueError, match="selected_sign"):
        validate_declared_error_record_program(corrupted)


def test_synthetic_unsupported_stim_operations_and_early_rec_fail_closed(
    monkeypatch,
) -> None:
    import pytest

    from scripts.external_baselines.no_cutoff_structure_census import (
        build_shadow_bundle as build_original_bundle,
    )
    from scripts.external_baselines.no_cutoff_target_lowering import neutral

    base = build_original_bundle(distance=3, rounds=1)
    source = str(base["source_text"])
    first_reset = source.index("\nR ")
    observable = "OBSERVABLE_INCLUDE(0)"
    cases = {
        "X": source[:first_reset] + "\nX 1" + source[first_reset:],
        "MPP": source[:first_reset] + "\nMPP Z1*Z2" + source[first_reset:],
        "feedback": source.replace(
            observable, "CX rec[-1] 1\n" + observable, 1
        ),
        "observable-one": source.replace(observable, "OBSERVABLE_INCLUDE(1)", 1),
        "early-rec": source[:first_reset]
        + "\nDETECTOR rec[-1]"
        + source[first_reset:],
    }
    patterns = {
        "X": "unsupported",
        "MPP": "unsupported",
        "feedback": "non-qubit target",
        "observable-one": "observable zero",
        "early-rec": "invalid rec offset",
    }
    for case_id, corrupted_source in cases.items():
        corrupted = {**base, "source_text": corrupted_source}
        monkeypatch.setattr(
            neutral,
            "build_shadow_bundle",
            lambda *, distance, rounds, value=corrupted: value,
        )
        with pytest.raises(ValueError, match=patterns[case_id]):
            neutral.lower_frozen_declared_error_record(distance=3, rounds=1)


def test_canonical_object_key_order_is_invariant_but_event_order_is_bound() -> None:
    from copy import deepcopy

    import pytest

    from scripts.external_baselines.no_cutoff_target_lowering.model import (
        canonical_json_bytes,
        sha256_json,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.neutral import (
        lower_frozen_declared_error_record,
        validate_declared_error_record_program,
    )

    original = lower_frozen_declared_error_record(distance=3, rounds=1).to_data()

    def reverse_object_keys(value):
        if isinstance(value, dict):
            return {
                key: reverse_object_keys(value[key]) for key in reversed(list(value))
            }
        if isinstance(value, list):
            return [reverse_object_keys(item) for item in value]
        return value

    reordered = reverse_object_keys(original)
    validate_declared_error_record_program(reordered)
    assert canonical_json_bytes(reordered) == canonical_json_bytes(original)

    event_reordered = deepcopy(original)
    event_reordered["semantic"]["events"][0:2] = reversed(
        event_reordered["semantic"]["events"][0:2]
    )
    event_reordered["semantic_sha256"] = sha256_json(event_reordered["semantic"])
    assert event_reordered["semantic_sha256"] != original["semantic_sha256"]
    with pytest.raises(ValueError, match="frozen semantic identity"):
        validate_declared_error_record_program(event_reordered)


def test_record_boundary_schema_explicitly_rejects_raw_and_latent_outputs() -> None:
    from copy import deepcopy

    import pytest

    from scripts.external_baselines.no_cutoff_target_lowering.model import sha256_json
    from scripts.external_baselines.no_cutoff_target_lowering.neutral import (
        lower_frozen_declared_error_record,
        validate_declared_error_record_program,
    )

    clean = lower_frozen_declared_error_record(distance=3, rounds=1).to_data()
    for kind in ("RAW", "LATENT"):
        changed = deepcopy(clean)
        record = changed["semantic"]["record_schema"]
        record["outputs"].append(
            {"kind": kind, "ordinal": 0, "producer_event_id": "e000000"}
        )
        record["record_width"] += 1
        changed["semantic_sha256"] = sha256_json(changed["semantic"])
        with pytest.raises(ValueError, match="Record schema"):
            validate_declared_error_record_program(changed)
