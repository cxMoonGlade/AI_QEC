"""Public contracts for direct static dynamic-ADD relation programs."""

from __future__ import annotations

import pytest


def test_add_relations_bind_pair_semantics_without_a_root_or_frontier() -> None:
    from scripts.external_baselines.no_cutoff_target_lowering.add_relations import (
        build_dynamic_add_relation_program,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.neutral import (
        lower_frozen_declared_error_record,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.pair import (
        build_exact_pair_transition_program,
    )

    neutral = lower_frozen_declared_error_record(distance=3, rounds=1)
    pair = build_exact_pair_transition_program(neutral)
    add = build_dynamic_add_relation_program(pair, neutral=neutral)
    data = add.to_data()
    semantic = data["semantic"]
    pair_semantic = pair.to_data()["semantic"]

    assert data["_schema"] == (
        "error_coupling_simulator.external.dynamic_add_relation_program.v1"
    )
    assert semantic["pair_sha256"] == pair.sha256
    assert len(semantic["events"]) == len(pair_semantic["kernels"]) == 156
    for relation, kernel in zip(
        semantic["events"], pair_semantic["kernels"], strict=True
    ):
        assert relation["event_id"] == kernel["event_id"]
        assert relation["pair_semantic_sha256"] == kernel["semantic_sha256"]
        assert relation["relation_order"] == [
            *(f"in.{field}" for field in relation["input_codec"]["fields"]),
            *(f"out.{field}" for field in relation["output_codec"]["fields"]),
        ]
        assert relation["abstraction"] == [
            f"in.{field}" for field in relation["input_codec"]["fields"]
        ]
        assert relation["rename"] == [
            {"from": f"out.{field}", "to": field}
            for field in relation["output_codec"]["fields"]
        ]
    forbidden = ("current_root", "root", "node_table", "frontier", "support")
    rendered = repr(data)
    assert all(name not in rendered for name in forbidden)


def test_all_target_add_relations_match_source_driven_independent_reconstruction() -> None:
    from scripts.external_baselines.no_cutoff_target_lowering.add_relations import (
        build_dynamic_add_relation_program,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.independent_target_oracle import (
        reconstruct_add_relation_events,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.neutral import (
        lower_frozen_declared_error_record,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.pair import (
        build_exact_pair_transition_program,
    )

    for distance in (3, 5):
        for rounds in (1, 3, 5, 7):
            neutral = lower_frozen_declared_error_record(
                distance=distance, rounds=rounds
            )
            pair = build_exact_pair_transition_program(neutral)
            owner = build_dynamic_add_relation_program(
                pair, neutral=neutral
            ).to_data()["semantic"]
            independent = reconstruct_add_relation_events(
                neutral.to_data()["semantic"]["source"]["source_text"]
            )
            assert owner["events"] == independent


def test_add_builder_rejects_self_hashed_forged_pair_before_lowering() -> None:
    from copy import deepcopy

    from scripts.external_baselines.no_cutoff_target_lowering.add_relations import (
        build_dynamic_add_relation_program,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.model import (
        PAIR_SCHEMA,
        StaticArtifact,
        sha256_json,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.neutral import (
        lower_frozen_declared_error_record,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.pair import (
        build_exact_pair_transition_program,
    )

    neutral = lower_frozen_declared_error_record(distance=3, rounds=1)
    pair = build_exact_pair_transition_program(neutral)
    semantic = pair.to_data()["semantic"]

    forged_semantics = []

    changed_algebra = deepcopy(semantic)
    changed_algebra["algebra"]["zero_policy"] = "prune_small_values"
    forged_semantics.append(changed_algebra)

    changed_kernel = deepcopy(semantic)
    kernel = changed_kernel["kernels"][0]
    kernel["component_rows"][0]["classical_action"]["opcode"] = "FORGED"
    kernel["semantic_sha256"] = sha256_json(
        {key: value for key, value in kernel.items() if key != "semantic_sha256"}
    )
    forged_semantics.append(changed_kernel)

    changed_checkpoint = deepcopy(semantic)
    changed_checkpoint["checkpoints"][0]["codec_fields"][0:2] = reversed(
        changed_checkpoint["checkpoints"][0]["codec_fields"][0:2]
    )
    forged_semantics.append(changed_checkpoint)

    for forged_semantic in forged_semantics:
        forged_pair = StaticArtifact(PAIR_SCHEMA, forged_semantic)
        # The forged envelope and all explicitly nested hashes are internally
        # self-consistent.  ADD must nevertheless reproduce it from neutral.
        with pytest.raises(ValueError, match="frozen semantic identity"):
            build_dynamic_add_relation_program(forged_pair, neutral=neutral)


def test_complete_tiny_add_truth_is_the_full_input_output_cartesian_relation() -> None:
    from itertools import islice

    from scripts.external_baselines.no_cutoff_target_lowering.add_relations import (
        iter_tiny_add_truth_rows,
        tiny_add_truth_row_count,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.independent_target_oracle import (
        iter_reconstructed_tiny_add_truth_rows,
        reconstructed_tiny_add_truth_row_count,
    )

    zero = [[0, 1], [0, 1], [0, 1], [0, 1]]
    frozen_counts = {
        "P1": 32_768,
        "P2": 4_194_304,
        "T1": 98_304,
        "T2": 163_840,
        "T3": 114_688,
        "T4": 44_040_192,
    }
    for witness_id, frozen_count in frozen_counts.items():
        assert tiny_add_truth_row_count(witness_id) == frozen_count
        assert reconstructed_tiny_add_truth_row_count(witness_id) == frozen_count

        owner_prefix = list(islice(iter_tiny_add_truth_rows(witness_id), 32))
        independent_prefix = list(
            islice(iter_reconstructed_tiny_add_truth_rows(witness_id), 32)
        )
        assert owner_prefix == independent_prefix
        assert owner_prefix
        assert all(
            set(row)
            == {
                "operation_index",
                "input_bits",
                "output_bits",
                "input_valid",
                "output_valid",
                "totalized_coefficient",
            }
            for row in owner_prefix
        )

    # P1 is small enough to inspect literally.  Each operation has a six-bit
    # input codec and a six-bit output codec, hence all 2**12 pairs occur once.
    owner = list(iter_tiny_add_truth_rows("P1"))
    independent = list(iter_reconstructed_tiny_add_truth_rows("P1"))
    assert owner == independent
    assert len(owner) == frozen_counts["P1"]
    for operation_index in range(8):
        operation_rows = [
            row for row in owner if row["operation_index"] == operation_index
        ]
        assert len(operation_rows) == 4096
        assert len(
            {
                (tuple(row["input_bits"]), tuple(row["output_bits"]))
                for row in operation_rows
            }
        ) == 4096
    invalid = [
        row
        for row in owner
        if not row["input_valid"] or not row["output_valid"]
    ]
    assert invalid
    assert all(row["totalized_coefficient"] == zero for row in invalid)


def test_complete_tiny_add_truth_streaming_digest_matches_independent_path() -> None:
    from scripts.external_baselines.no_cutoff_target_lowering.add_relations import (
        iter_tiny_add_truth_rows,
        summarize_tiny_add_truth_assertion,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.independent_target_oracle import (
        summarize_reconstructed_tiny_add_truth_assertion,
    )

    subject = "P1/complete-static-add-truth"
    owner = summarize_tiny_add_truth_assertion(
        "P1", assertion_id="every_valid_and_invalid_code", subject=subject
    )
    independent = summarize_reconstructed_tiny_add_truth_assertion(
        "P1", assertion_id="every_valid_and_invalid_code", subject=subject
    )
    assert owner == independent
    assert owner["row_count"] == 32_768
    assert len(owner["sha256"]) == 64
    assert len(owner["rows_sha256"]) == 64

    # Guard the streaming byte framing against the ordinary canonical JSON
    # definition on the small witness where materialization is safe.
    from scripts.external_baselines.no_cutoff_target_lowering.model import sha256_json

    assert owner["sha256"] == sha256_json(
        {
            "assertion_id": "every_valid_and_invalid_code",
            "subject": subject,
            "rows": list(iter_tiny_add_truth_rows("P1")),
        }
    )
    assert owner["rows_sha256"] == sha256_json(
        list(iter_tiny_add_truth_rows("P1"))
    )
