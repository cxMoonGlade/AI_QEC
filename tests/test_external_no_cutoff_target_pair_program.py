"""Public contracts for the static exact pair-transition program."""

from __future__ import annotations

from copy import deepcopy

import pytest


def test_pair_program_lowers_every_neutral_event_without_running_a_frontier() -> None:
    from scripts.external_baselines.no_cutoff_target_lowering.neutral import (
        lower_frozen_declared_error_record,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.pair import (
        build_exact_pair_transition_program,
    )

    neutral = lower_frozen_declared_error_record(distance=3, rounds=1)
    pair = build_exact_pair_transition_program(neutral)
    data = pair.to_data()
    semantic = data["semantic"]

    assert data["_schema"] == (
        "error_coupling_simulator.external.exact_pair_transition_program.v1"
    )
    assert semantic["neutral_sha256"] == neutral.sha256
    assert semantic["initial_terms"] == [
        {
            "coefficient": [[1, 2], [0, 1], [0, 1], [0, 1]],
            "latent_m": -1,
            "left": {"x": [0] * 17, "z": [0] * 17},
            "right": {"x": [0] * 17, "z": [0] * 17},
            "observable_accumulator": 0,
            "live_raw": [],
            "record": [],
        },
        {
            "coefficient": [[1, 2], [0, 1], [0, 1], [0, 1]],
            "latent_m": 1,
            "left": {"x": [0] * 17, "z": [0] * 17},
            "right": {"x": [0] * 17, "z": [0] * 17},
            "observable_accumulator": 0,
            "live_raw": [],
            "record": [],
        },
    ]
    assert len(semantic["kernels"]) == 156
    assert len(semantic["checkpoints"]) == 157
    assert semantic["checkpoints"][0]["record_width"] == 0
    assert semantic["checkpoints"][-1]["record_width"] == 9
    assert all(len(basis["stabilizers"]) == 17 for basis in semantic["basis_catalog"])
    assert all(len(basis["rref_rows"]) == 17 for basis in semantic["basis_catalog"])
    forbidden = {"support", "frontier", "current_map", "peak", "probability"}
    assert forbidden.isdisjoint(data)
    assert all(forbidden.isdisjoint(kernel) for kernel in semantic["kernels"])


def test_pair_local_kernels_match_the_independent_finite_matrix_oracle() -> None:
    from scripts.external_baselines.no_cutoff_target_lowering.independent_pair_oracle import (
        reconstruct_component_rows,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.model import (
        canonical_json_bytes,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.neutral import (
        lower_frozen_declared_error_record,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.pair import (
        build_exact_pair_transition_program,
    )

    neutral = lower_frozen_declared_error_record(distance=3, rounds=1)
    neutral_events = neutral.to_data()["semantic"]["events"]
    owner_kernels = build_exact_pair_transition_program(neutral).to_data()[
        "semantic"
    ]["kernels"]
    first_by_kind = {}
    for event, kernel in zip(neutral_events, owner_kernels, strict=True):
        first_by_kind.setdefault(event["kind"], (event, kernel))

    for kind in (
        "COORD_MARKER",
        "RESET",
        "TICK_MARKER",
        "H",
        "COHERENT_Z",
        "CX",
        "MR",
        "DETECTOR_APPEND",
        "M",
        "OBSERVABLE_XOR",
        "FINALIZE_RECORD",
    ):
        event, kernel = first_by_kind[kind]
        expected = reconstruct_component_rows(event)
        assert kernel["component_rows"] == expected
        assert kernel["component_rows"] == sorted(
            kernel["component_rows"], key=canonical_json_bytes
        )

    assert len(first_by_kind["COHERENT_Z"][1]["component_rows"]) == 4
    assert len(first_by_kind["RESET"][1]["component_rows"]) == 8
    assert len(first_by_kind["M"][1]["component_rows"]) == 8
    assert len(first_by_kind["MR"][1]["component_rows"]) == 8


def test_target_signed_rref_checkpoints_match_an_independent_gf2_oracle() -> None:
    from scripts.external_baselines.no_cutoff_target_lowering.independent_target_oracle import (
        reconstruct_checkpoint_bases,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.neutral import (
        lower_frozen_declared_error_record,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.pair import (
        build_exact_pair_transition_program,
    )

    neutral = lower_frozen_declared_error_record(distance=3, rounds=1)
    pair_semantic = build_exact_pair_transition_program(neutral).to_data()["semantic"]
    catalog = {
        basis["basis_id"]: {
            "pivots": basis["pivots"],
            "rref_rows": basis["rref_rows"],
            "stabilizers": basis["stabilizers"],
        }
        for basis in pair_semantic["basis_catalog"]
    }
    owner_history = [catalog[checkpoint["basis_id"]] for checkpoint in pair_semantic["checkpoints"]]
    independent_history = reconstruct_checkpoint_bases(
        neutral.to_data()["semantic"]["events"], qubit_count=17
    )

    assert owner_history == independent_history
    assert all(len(entry["pivots"]) == 17 for entry in independent_history)
    assert all(
        row["phase_mod4"] in (0, 2)
        for entry in independent_history
        for row in entry["rref_rows"]
    )


def test_ket_right_and_bra_left_coset_phases_match_independent_witnesses() -> None:
    from itertools import product

    from scripts.external_baselines.no_cutoff_target_lowering.independent_target_oracle import (
        canonicalize_pauli_independently,
        independent_signed_rref_basis,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.pair import (
        build_signed_rref_basis,
        canonicalize_pauli_against_basis,
    )

    witnesses = {
        "C1": [{"x": [0], "z": [1], "phase_mod4": 0}],
        "C2": [{"x": [1], "z": [0], "phase_mod4": 0}],
        "C3": [
            {"x": [1, 1], "z": [0, 0], "phase_mod4": 0},
            {"x": [0, 0], "z": [1, 1], "phase_mod4": 0},
        ],
        "C4": [
            {"x": [1, 1, 1], "z": [0, 0, 0], "phase_mod4": 0},
            {"x": [0, 0, 0], "z": [1, 1, 0], "phase_mod4": 0},
            {"x": [0, 0, 0], "z": [0, 1, 1], "phase_mod4": 0},
        ],
    }
    saw_orientation_phase = False
    for stabilizers in witnesses.values():
        owner_basis = build_signed_rref_basis(stabilizers)
        independent_basis = independent_signed_rref_basis(stabilizers)
        assert {
            key: owner_basis[key] for key in ("stabilizers", "rref_rows", "pivots")
        } == independent_basis
        n = len(stabilizers)
        for bits in product((0, 1), repeat=2 * n):
            pauli = {"x": list(bits[:n]), "z": list(bits[n:])}
            owner_ket = canonicalize_pauli_against_basis(
                pauli, owner_basis, side="ket"
            )
            owner_bra = canonicalize_pauli_against_basis(
                pauli, owner_basis, side="bra"
            )
            assert owner_ket == canonicalize_pauli_independently(
                pauli, independent_basis, side="ket"
            )
            assert owner_bra == canonicalize_pauli_independently(
                pauli, independent_basis, side="bra"
            )
            assert canonicalize_pauli_against_basis(
                owner_ket["representative"], owner_basis, side="ket"
            )["representative"] == owner_ket["representative"]
            saw_orientation_phase |= (
                owner_ket["coefficient_phase_mod4"]
                != owner_bra["coefficient_phase_mod4"]
            )
    assert saw_orientation_phase


def test_all_eight_target_pair_programs_match_independent_event_reconstruction() -> None:
    from scripts.external_baselines.no_cutoff_target_lowering.independent_pair_oracle import (
        reconstruct_pair_receipt_rows,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.model import sha256_json
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
            neutral_semantic = neutral.to_data()["semantic"]
            pair = build_exact_pair_transition_program(neutral).to_data()["semantic"]
            reconstructed = reconstruct_pair_receipt_rows(
                neutral_semantic["source"]["source_text"]
            )
            catalog = {
                basis["basis_id"]: {
                    "pivots": basis["pivots"],
                    "rref_rows": basis["rref_rows"],
                    "stabilizers": basis["stabilizers"],
                }
                for basis in pair["basis_catalog"]
            }
            assert reconstructed["initial_terms"] == pair["initial_terms"]
            assert reconstructed["basis_catalog"] == [
                catalog[checkpoint["basis_id"]]
                for checkpoint in pair["checkpoints"]
            ]
            assert reconstructed["checkpoint_codecs"] == [
                {
                    "checkpoint": checkpoint["ordinal"],
                    "fields": checkpoint["codec_fields"],
                    "validity_sha256": sha256_json(checkpoint["validity"]),
                }
                for checkpoint in pair["checkpoints"]
            ]
            assert reconstructed["kernel_normal_forms"] == [
                {
                    "event_id": kernel["event_id"],
                    "rows": kernel["component_rows"],
                }
                for kernel in pair["kernels"]
            ]


def test_complete_p1_p2_pair_component_matrices_match_independent_oracle() -> None:
    from scripts.external_baselines.no_cutoff_target_lowering.independent_pair_oracle import (
        verify_pair_witness_component_matrices,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.pair import (
        build_pair_witness_component_catalog,
    )

    p1 = verify_pair_witness_component_matrices(
        "P1", build_pair_witness_component_catalog("P1")
    )
    p2 = verify_pair_witness_component_matrices(
        "P2", build_pair_witness_component_catalog("P2")
    )
    assert len(p1) == 256
    assert len(p2) == 1024
    assert all(row["status"] == "PASS" for row in (*p1, *p2))
    assert all(
        row["expected_matrix"] == row["observed_matrix"] for row in (*p1, *p2)
    )

    paulis = ("I", "X", "Y", "Z")
    p1_operations = (
        "identity",
        "H",
        "COHERENT_Z",
        "R",
        "M(b=0)",
        "M(b=1)",
        "MR(b=0)",
        "MR(b=1)",
    )
    assert [
        (
            row["left_pauli"],
            row["right_pauli"],
            row["latent_m"],
            row["operation_id"],
        )
        for row in p1
    ] == [
        (left, right, latent, operation)
        for left in paulis
        for right in paulis
        for latent in (-1, 1)
        for operation in p1_operations
    ]

    two_qubit_paulis = tuple(
        first + second for first in paulis for second in paulis
    )
    p2_operations = (
        "H(q=0)",
        "H(q=1)",
        "CX(control=0,target=1)",
        "CX(control=1,target=0)",
    )
    assert [
        (row["left_pauli"], row["right_pauli"], row["operation_id"])
        for row in p2
    ] == [
        (left, right, operation)
        for left in two_qubit_paulis
        for right in two_qubit_paulis
        for operation in p2_operations
    ]
    assert all(
        isinstance(row["expected_matrix"], list)
        and isinstance(row["observed_matrix"], list)
        and all(
            isinstance(entry, str)
            for matrix_row in row["expected_matrix"]
            for entry in matrix_row
        )
        for row in (*p1, *p2)
    )


def test_pair_witness_oracle_rejects_non_frozen_catalog_order() -> None:
    from scripts.external_baselines.no_cutoff_target_lowering.independent_pair_oracle import (
        verify_pair_witness_component_matrices,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.pair import (
        build_pair_witness_component_catalog,
    )

    catalog = build_pair_witness_component_catalog("P1")
    catalog[0], catalog[1] = catalog[1], catalog[0]
    with pytest.raises(AssertionError, match="frozen Pauli/bit/operation order"):
        verify_pair_witness_component_matrices("P1", catalog)


def test_pair_builder_strictly_authenticates_its_neutral_input() -> None:
    import hashlib

    from scripts.external_baselines.no_cutoff_target_lowering.model import (
        NEUTRAL_SCHEMA,
        StaticArtifact,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.neutral import (
        lower_frozen_declared_error_record,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.pair import (
        build_exact_pair_transition_program,
    )

    neutral = lower_frozen_declared_error_record(distance=3, rounds=1)
    changed = deepcopy(neutral.to_data()["semantic"])
    changed["source"]["source_text"] = changed["source"]["source_text"].replace(
        "QUBIT_COORDS(1, 1) 1", "QUBIT_COORDS(1, 1) 2", 1
    )
    changed["source"]["source_text_sha256"] = hashlib.sha256(
        changed["source"]["source_text"].encode("utf-8")
    ).hexdigest()
    forged = StaticArtifact(NEUTRAL_SCHEMA, changed)
    with pytest.raises(ValueError, match="neutral artifact"):
        build_exact_pair_transition_program(forged)


def test_pair_builder_rejects_basis_id_collision_with_unequal_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts.external_baselines.no_cutoff_target_lowering.neutral import (
        lower_frozen_declared_error_record,
    )
    from scripts.external_baselines.no_cutoff_target_lowering import pair as pair_module

    original_sha256_json = pair_module.sha256_json

    def collide_basis_payloads(value: object) -> str:
        if isinstance(value, dict) and set(value) == {
            "stabilizers",
            "rref_rows",
            "pivots",
        }:
            return "0" * 64
        return original_sha256_json(value)

    monkeypatch.setattr(pair_module, "sha256_json", collide_basis_payloads)
    neutral = lower_frozen_declared_error_record(distance=3, rounds=1)
    with pytest.raises(ValueError, match="basis ID collision"):
        pair_module.build_exact_pair_transition_program(neutral)


def test_pair_receipt_oracle_reconstructs_all_assertion_rows_from_source_text() -> None:
    from scripts.external_baselines.no_cutoff_target_lowering.independent_pair_oracle import (
        reconstruct_pair_receipt_rows,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.model import sha256_json
    from scripts.external_baselines.no_cutoff_target_lowering.neutral import (
        lower_frozen_declared_error_record,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.pair import (
        build_exact_pair_transition_program,
    )

    neutral = lower_frozen_declared_error_record(distance=3, rounds=1)
    pair = build_exact_pair_transition_program(neutral).to_data()["semantic"]
    reconstructed = reconstruct_pair_receipt_rows(
        neutral.to_data()["semantic"]["source"]["source_text"]
    )
    catalog = {
        row["basis_id"]: {
            "pivots": row["pivots"],
            "rref_rows": row["rref_rows"],
            "stabilizers": row["stabilizers"],
        }
        for row in pair["basis_catalog"]
    }
    assert reconstructed == {
        "initial_terms": pair["initial_terms"],
        "basis_catalog": [
            catalog[checkpoint["basis_id"]] for checkpoint in pair["checkpoints"]
        ],
        "checkpoint_codecs": [
            {
                "checkpoint": checkpoint["ordinal"],
                "fields": checkpoint["codec_fields"],
                "validity_sha256": sha256_json(checkpoint["validity"]),
            }
            for checkpoint in pair["checkpoints"]
        ],
        "kernel_normal_forms": [
            {"event_id": kernel["event_id"], "rows": kernel["component_rows"]}
            for kernel in pair["kernels"]
        ],
    }
