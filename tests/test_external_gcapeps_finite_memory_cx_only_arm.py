"""Focused controls for the frozen CX-only (X1-analog) P2 control arm.

Covers the arm's single frozen delta over v1 -- an unconditional cross-row
CX on EVERY round at the contracted position, with the FULL unthinned
collision-rotation schedule -- plus every-round checkpoints, the shared v2
held-out seed binding, exact schema rejection, and the equivalence gate
against the verified screening X1 transform in
``.scratch/gcapeps-fixture-v2/screening`` (skipped when those development
artifacts are absent).

All fixtures built here are CALIBRATION cells; no held-out fixture is ever
materialized by this file.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


REPO = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO / "scripts" / "external_baselines"
EMITTER_ARM = SCRIPT_DIR / "emit_gcapeps_finite_memory_cx_only_arm.py"
EMITTER_SIBLING_ARM = SCRIPT_DIR / "emit_gcapeps_finite_memory_thin_only_arm.py"
EMITTER_V2 = SCRIPT_DIR / "emit_gcapeps_finite_memory_fixture_v2.py"
EMITTER_V1 = SCRIPT_DIR / "emit_gcapeps_finite_memory_fixture.py"
SCREENING_DIR = REPO / ".scratch" / "gcapeps-fixture-v2" / "screening"
SCREENING_RESULTS = SCREENING_DIR / "screening_results.json"

requires_screening_artifacts = pytest.mark.skipif(
    not (
        (SCREENING_DIR / "common.py").is_file() and SCREENING_RESULTS.is_file()
    ),
    reason="screening development artifacts are not present on this checkout",
)


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_arm():
    return _load_module(
        EMITTER_ARM, "emit_gcapeps_finite_memory_cx_only_arm_under_test"
    )


def _load_sibling_arm():
    return _load_module(
        EMITTER_SIBLING_ARM,
        "emit_gcapeps_finite_memory_thin_only_arm_reference",
    )


def _load_v2():
    return _load_module(
        EMITTER_V2, "emit_gcapeps_finite_memory_fixture_v2_arm_reference"
    )


def _load_v1():
    return _load_module(
        EMITTER_V1, "emit_gcapeps_finite_memory_fixture_v1_arm_reference"
    )


def _calibration_arguments(**overrides):
    arguments = {
        "run_partition": "CALIBRATION",
        "width": 7,
        "rounds": 4,
        "axis_family": 3,
        "p_event_numerator": 3,
        "seed": 2,
        "gamma_index": 2,
        "run_blpensemble": False,
    }
    arguments.update(overrides)
    return arguments


def _fixture(**overrides):
    emitter = _load_arm()
    fixture = emitter.build_fixture(**_calibration_arguments(**overrides))
    return emitter, fixture


def _screening_view(fixture) -> list[dict]:
    """Map an arm fixture operation stream into the screening representation."""

    rounds = []
    for round_row in fixture["carrier_path"]["round_ledger"]:
        cliffords, candidate, collisions = [], [], []
        for operation in round_row["operations"]:
            if operation["operation_class"] == "clifford":
                view = {
                    "kind": operation["gate_kind"],
                    "targets": tuple(operation["targets"]),
                }
                if operation["layer_index"] <= 5:
                    cliffords.append(view)
                else:
                    candidate.append(view)
            else:
                collisions.append(
                    {
                        "kind": "ROT",
                        "targets": tuple(operation["targets"]),
                        "theta": float.fromhex(operation["theta_float64_hex"]),
                        "axis": operation["axis"],
                        "body": operation["physical_pauli_body"],
                        "event_key": (
                            operation["round_index"],
                            operation["site_index"],
                        ),
                    }
                )
        rounds.append(
            {
                "round_index": round_row["round_index"],
                "cliffords": cliffords,
                "candidate_cliffords": candidate,
                "collisions": collisions,
            }
        )
    return rounds


def test_schema_revision_and_deterministic_reconstruction_round_trip() -> None:
    emitter, fixture = _fixture()

    assert fixture["schema"] == (
        "error_coupling_simulator.external.gcapeps_finite_memory."
        "fixture_cx_only_arm.v1"
    )
    assert fixture["script_revision"] == (
        "gcapeps-finite-memory-neutral-fixture-cx-only-arm-v1"
    )
    assert fixture["fixture_id"] == fixture["case_id"]
    assert fixture["case_id"].startswith("cx-only-arm-calibration-")
    assert emitter.validate_fixture(fixture) == fixture[
        "result_projection_sha256"
    ]
    assert emitter.projection_sha256(fixture) == fixture[
        "result_projection_sha256"
    ]

    rebuilt = emitter.build_fixture(**_calibration_arguments())
    assert emitter.canonical_json_bytes(rebuilt) == emitter.canonical_json_bytes(
        fixture
    )

    round_tripped = json.loads(emitter.canonical_json_bytes(fixture))
    assert emitter.validate_fixture(round_tripped) == fixture[
        "result_projection_sha256"
    ]

    corrupted = copy.deepcopy(fixture)
    corrupted["carrier_path"]["event_rows"][0]["event"] = not corrupted[
        "carrier_path"
    ]["event_rows"][0]["event"]
    with pytest.raises(ValueError, match="deterministic reconstruction"):
        emitter.validate_fixture(corrupted)


def test_cross_row_cx_layer_exact_on_every_round_at_contracted_position(
) -> None:
    emitter, fixture = _fixture(rounds=4)
    width = fixture["parameters"]["width"]
    control = width // 2
    target = width + width // 2
    contract = fixture["state_contract"]["cross_row_clifford"]
    assert contract["gate_kind"] == "CX"
    assert contract["control_site"] == control
    assert contract["target_site"] == target
    assert contract["round_parity"] == "all"
    assert contract["round_predicate"] == "True"
    assert contract["layer_index"] == 6
    assert contract["layer_position"] == (
        "after_memory_reverse_cx_layers_before_collision_layer"
    )
    assert fixture["state_contract"]["unconditional_cross_row_gate"] is True

    all_indices: list[int] = []
    for round_row in fixture["carrier_path"]["round_ledger"]:
        round_index = round_row["round_index"]
        parity = round_index % 2
        assert [layer["layer_name"] for layer in round_row["layers"]] == [
            "system_h",
            "system_s",
            f"system_cx_parity_{parity}",
            f"system_cx_parity_{1 - parity}",
            f"memory_reverse_cx_parity_{parity}",
            f"memory_reverse_cx_parity_{1 - parity}",
            "cross_row_cx",
            "event_conditioned_collisions",
        ]
        cross_operations = [
            operation
            for operation in round_row["operations"]
            if operation["layer_index"] == 6
        ]
        # X1-analog: exactly one cross-row CX on EVERY round, odd and even.
        assert len(cross_operations) == 1
        (cross,) = cross_operations
        assert cross["operation_class"] == "clifford"
        assert cross["gate_kind"] == "CX"
        assert cross["matrix_definition"] == "CX"
        assert cross["targets"] == [control, target]
        assert cross["within_layer_index"] == 0
        assert round_row["layers"][6]["operation_indices"] == [
            cross["operation_index"]
        ]
        earlier = [
            operation["operation_index"]
            for operation in round_row["operations"]
            if operation["layer_index"] <= 5
        ]
        later = [
            operation["operation_index"]
            for operation in round_row["operations"]
            if operation["layer_index"] == 7
        ]
        assert all(index < cross["operation_index"] for index in earlier)
        assert all(index > cross["operation_index"] for index in later)
        assert all(
            operation["layer_index"] == 7
            for operation in round_row["collision_rotations"]
        )
        all_indices.extend(
            operation["operation_index"]
            for operation in round_row["operations"]
        )
    assert all_indices == list(range(len(all_indices)))
    assert emitter.validate_fixture(fixture) == fixture[
        "result_projection_sha256"
    ]


def test_full_rotation_schedule_identical_to_v1_and_cliffords_preserved(
) -> None:
    v1 = _load_v1()
    _emitter, fixture = _fixture(rounds=4)
    reference = v1.build_fixture(**_calibration_arguments(rounds=4))
    v1_carrier = reference["carrier_path"]
    arm_carrier = fixture["carrier_path"]

    # Inherited verbatim: masks, event rows, inputs, geometry, convention.
    assert arm_carrier["event_rows"] == v1_carrier["event_rows"]
    assert arm_carrier["full_mask"] == v1_carrier["full_mask"]
    assert arm_carrier["realized_event_count"] == v1_carrier[
        "realized_event_count"
    ]
    assert arm_carrier["active_axis_rotation_count"] == v1_carrier[
        "active_axis_rotation_count"
    ]
    assert fixture["inputs"] == reference["inputs"]
    assert fixture["geometry"] == reference["geometry"]
    assert fixture["coordinate_convention"] == reference[
        "coordinate_convention"
    ]
    assert fixture["mask_contract"] == reference["mask_contract"]
    assert fixture["gate_definitions"] == reference["gate_definitions"]
    assert fixture["parameters"] == reference["parameters"]

    total_rotations = 0
    for v1_round, arm_round in zip(
        v1_carrier["round_ledger"], arm_carrier["round_ledger"], strict=True
    ):
        v1_cliffords = [
            (operation["gate_kind"], operation["targets"])
            for operation in v1_round["clifford_operations"]
        ]
        arm_original_cliffords = [
            (operation["gate_kind"], operation["targets"])
            for operation in arm_round["clifford_operations"]
            if operation["layer_index"] <= 5
        ]
        assert arm_original_cliffords == v1_cliffords

        # No thinning: every v1 rotation survives, in order, with every
        # non-renumbered field byte-identical (thetas stay hex-frozen).
        assert len(arm_round["collision_rotations"]) == len(
            v1_round["collision_rotations"]
        )
        for arm_rotation, v1_rotation in zip(
            arm_round["collision_rotations"],
            v1_round["collision_rotations"],
            strict=True,
        ):
            stripped_arm = {
                key: value
                for key, value in arm_rotation.items()
                if key not in {"operation_index", "layer_index"}
            }
            stripped_v1 = {
                key: value
                for key, value in v1_rotation.items()
                if key not in {"operation_index", "layer_index"}
            }
            assert stripped_arm == stripped_v1
            assert arm_rotation["layer_index"] == 7
        total_rotations += len(arm_round["collision_rotations"])

    assert total_rotations == arm_carrier["active_axis_rotation_count"]
    assert len(fixture["sdim_pullback_requests"]) == 2 * total_rotations
    arm_request_keys = [
        (
            row["input_id"],
            row["collision_ordinal"],
            row["round_index"],
            row["site_index"],
            row["axis_index"],
            row["physical_pauli_body"],
        )
        for row in fixture["sdim_pullback_requests"]
    ]
    v1_request_keys = [
        (
            row["input_id"],
            row["collision_ordinal"],
            row["round_index"],
            row["site_index"],
            row["axis_index"],
            row["physical_pauli_body"],
        )
        for row in reference["sdim_pullback_requests"]
    ]
    assert arm_request_keys == v1_request_keys


@pytest.mark.parametrize("rounds", [4, 6])
def test_checkpoint_policy_every_round_and_state_contract_blocks(
    rounds: int,
) -> None:
    _emitter, fixture = _fixture(rounds=rounds)
    contract = fixture["state_contract"]
    assert contract["version"] == (
        "gcapeps-finite-memory-state-contract.cx-only-arm.v1"
    )
    assert contract["arm"] == "cx-only-arm"
    assert contract["screening_transform_analog"] == "X1"
    assert contract["checkpoint_policy"] == "every_round"
    assert fixture["checkpoints"] == list(range(rounds + 1))
    assert contract["unconditional_cross_row_gate"] is True
    # The thinning lever is OFF: the arm carries no thinning contract.
    assert "rotation_thinning" not in contract
    # v1 lifecycle fields survive unchanged.
    assert contract["initial_state_kind"] == "computational_basis_product"
    assert contract["joint_state_retained_across_rounds"] is True
    assert contract["memory_row_policy"] == "never_discard_reset_or_recreate"
    assert contract["candidate_restart_between_rounds"] is False
    assert contract["physical_round_indexing"] == "one_based"
    assert contract["checkpoint_zero"] == "initial_state_only"


def test_heldout_seed_is_v2_seed_with_collision_guards() -> None:
    emitter = _load_arm()
    v2 = _load_v2()
    v1 = _load_v1()
    expected = int.from_bytes(
        hashlib.sha256(b"gcapeps-finite-memory-heldout-v2").digest()[:8],
        "big",
    )
    # The arm mints no namespace of its own: P2 compares the arms against
    # X8 on the same cells, so the arm's held-out seed IS v2's.
    assert emitter.HELDOUT_SEED == expected
    assert emitter.HELDOUT_SEED == v2.HELDOUT_SEED
    assert emitter.V1_HELDOUT_SEED == v1.HELDOUT_SEED
    assert emitter.HELDOUT_SEED != v1.HELDOUT_SEED

    with pytest.raises(ValueError, match="v2 held-out seed"):
        emitter.build_fixture(
            run_partition="HELDOUT",
            width=7,
            rounds=4,
            axis_family=3,
            p_event_numerator=3,
            seed=v1.HELDOUT_SEED,
            gamma_index=2,
            run_blpensemble=False,
        )


def test_heldout_stream_widening_inherited_from_v2_without_building() -> None:
    """Amendment 3 item 1: the arm inherits the widened five-seed
    hash-chain admission (hv2-0..hv2-4) with every guard.  Refusal paths
    and derivation strings only; no held-out fixture is built."""

    emitter = _load_arm()
    v2 = _load_v2()
    v1 = _load_v1()
    digest_0 = hashlib.sha256(b"gcapeps-finite-memory-heldout-v2").digest()
    digest_1 = hashlib.sha256(digest_0).digest()
    stream = digest_0 + digest_1
    assert emitter.HELDOUT_SEEDS == v2.HELDOUT_SEEDS
    assert emitter.HELDOUT_SEEDS == tuple(
        int.from_bytes(stream[8 * index : 8 * (index + 1)], "big")
        for index in range(5)
    )
    # Regression: hv2-0/hv2-1 stay byte-identical to the pre-chain
    # derivation windows D0[0:8] and D0[8:16].
    assert emitter.HELDOUT_SEEDS[0] == int.from_bytes(digest_0[:8], "big")
    assert emitter.HELDOUT_SEEDS[1] == int.from_bytes(
        digest_0[8:16], "big"
    )
    assert len(set(emitter.HELDOUT_SEEDS)) == 5
    assert all(seed != v1.HELDOUT_SEED for seed in emitter.HELDOUT_SEEDS)

    # Second and fifth seeds admitted: the seed gate precedes the rounds
    # gate, so an out-of-union rounds request must fail on ROUNDS, never
    # on the seed.
    for stream_index in (1, 4):
        with pytest.raises(ValueError, match="held-out rounds"):
            emitter.build_fixture(
                run_partition="HELDOUT",
                width=3,
                rounds=3,
                axis_family=3,
                p_event_numerator=4,
                seed=emitter.HELDOUT_SEEDS[stream_index],
                gamma_index=2,
                run_blpensemble=False,
            )

    # Sixth stream seed refused outright.
    with pytest.raises(ValueError, match="five frozen v2\\s+held-out seeds"):
        emitter.build_fixture(
            run_partition="HELDOUT",
            width=3,
            rounds=1,
            axis_family=3,
            p_event_numerator=4,
            seed=v2.heldout_seed(5),
            gamma_index=2,
            run_blpensemble=False,
        )

    # All five admitted seeds refused in the CALIBRATION context, like
    # the first always was.
    for seed in emitter.HELDOUT_SEEDS:
        with pytest.raises(ValueError, match="outside the frozen grid"):
            emitter.build_fixture(**_calibration_arguments(seed=seed))


def test_grid_gate_rejects_out_of_grid_cells() -> None:
    emitter = _load_arm()

    def build(**overrides):
        return emitter.build_fixture(**_calibration_arguments(**overrides))

    with pytest.raises(ValueError, match="frozen values"):
        build(width=4)
    with pytest.raises(ValueError, match="outside the frozen grid"):
        build(rounds=5)
    with pytest.raises(ValueError, match="outside the frozen grid"):
        build(width=3)
    with pytest.raises(ValueError, match="outside the frozen grid"):
        build(axis_family=1)
    with pytest.raises(ValueError, match="outside the frozen grid"):
        build(p_event_numerator=4)
    with pytest.raises(ValueError, match="outside the frozen grid"):
        build(seed=4)
    with pytest.raises(ValueError, match="BLPENSEMBLE"):
        build(run_blpensemble=True)
    with pytest.raises(ValueError, match="held-out rounds"):
        build(
            run_partition="HELDOUT",
            width=3,
            rounds=3,
            p_event_numerator=4,
            seed=emitter.HELDOUT_SEED,
        )
    with pytest.raises(ValueError, match="run_partition"):
        build(run_partition="DEVELOPMENT")


def test_schema_version_rejection_without_fallback() -> None:
    emitter, fixture = _fixture()
    v1 = _load_v1()
    v2 = _load_v2()
    sibling = _load_sibling_arm()

    for wrong_schema in (
        v1.FIXTURE_SCHEMA,
        v2.FIXTURE_SCHEMA,
        sibling.FIXTURE_SCHEMA,
        emitter.FIXTURE_SCHEMA + ".draft",
    ):
        relabeled = copy.deepcopy(fixture)
        relabeled["schema"] = wrong_schema
        with pytest.raises(ValueError, match="unsupported fixture schema"):
            emitter.validate_fixture(relabeled)

    genuine_v1 = v1.build_fixture(**_calibration_arguments())
    with pytest.raises(ValueError, match="unsupported fixture schema"):
        emitter.validate_fixture(genuine_v1)

    genuine_v2 = v2.build_fixture(**_calibration_arguments())
    with pytest.raises(ValueError, match="unsupported fixture schema"):
        emitter.validate_fixture(genuine_v2)


def test_family_identifiers_pairwise_distinct() -> None:
    emitter = _load_arm()
    sibling = _load_sibling_arm()
    v2 = _load_v2()
    v1 = _load_v1()

    schemas = {
        v1.FIXTURE_SCHEMA,
        v2.FIXTURE_SCHEMA,
        emitter.FIXTURE_SCHEMA,
        sibling.FIXTURE_SCHEMA,
    }
    assert len(schemas) == 4
    revisions = {
        v1.SCRIPT_REVISION,
        v2.SCRIPT_REVISION,
        emitter.SCRIPT_REVISION,
        sibling.SCRIPT_REVISION,
    }
    assert len(revisions) == 4
    contract_versions = {
        v2.STATE_CONTRACT_VERSION,
        emitter.STATE_CONTRACT_VERSION,
        sibling.STATE_CONTRACT_VERSION,
    }
    assert len(contract_versions) == 3
    assert emitter.ARM_ID != sibling.ARM_ID
    # The two arms share the v2 held-out seed by design (same P2 cells).
    assert emitter.HELDOUT_SEED == sibling.HELDOUT_SEED == v2.HELDOUT_SEED


def test_generator_has_no_candidate_reference_or_simulator_imports() -> None:
    source = EMITTER_ARM.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(EMITTER_ARM))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(
                alias.name.split(".", 1)[0] for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
    assert imported_roots.isdisjoint(
        {
            "numpy",
            "quimb",
            "stim",
            "sdim",
            "gcapeps",
            "error_coupling_simulator",
        }
    )


def test_cli_emits_one_exact_compact_json_core_without_newline() -> None:
    emitter = _load_arm()
    process = subprocess.run(
        [
            sys.executable,
            "-I",
            str(EMITTER_ARM),
            "--run-partition",
            "CALIBRATION",
            "--width",
            "7",
            "--rounds",
            "4",
            "--axis-family",
            "3",
            "--p-event-numerator",
            "3",
            "--seed",
            "0",
            "--gamma-index",
            "0",
        ],
        check=True,
        capture_output=True,
    )
    assert process.stderr == b""
    assert process.stdout.endswith(b"}")
    assert not process.stdout.endswith(b"\n")
    payload = json.loads(process.stdout)
    assert process.stdout == emitter.canonical_json_bytes(payload)
    assert emitter.validate_fixture(payload) == payload[
        "result_projection_sha256"
    ]


def _load_screening_common():
    return _load_module(
        SCREENING_DIR / "common.py", "_cx_only_arm_screening_common"
    )


@requires_screening_artifacts
def test_equivalence_gate_operation_stream_matches_screening_x1() -> None:
    common = _load_screening_common()
    p0_fixture = common.build_calibration_fixture(
        seed=2, gamma_index=2, rounds=10
    )
    base_rounds = common.flatten_rounds(p0_fixture)
    reference = common.make_candidate(base_rounds, "X1")

    _emitter, fixture = _fixture(rounds=10)
    mapped = _screening_view(fixture)

    assert len(mapped) == len(reference) == 10
    for got, want in zip(mapped, reference, strict=True):
        assert got["round_index"] == want["round_index"]
        assert got["cliffords"] == want["cliffords"]
        assert got["candidate_cliffords"] == want["candidate_cliffords"]
        assert got["collisions"] == want["collisions"]

    # Insertions are exactly the every-round CX(3, 10); the rotation set is
    # the full untouched v1 schedule with hex-identical thetas.
    assert [
        (round_row["round_index"], round_row["candidate_cliffords"])
        for round_row in mapped
    ] == [
        (round_index, [{"kind": "CX", "targets": (3, 10)}])
        for round_index in range(1, 11)
    ]
    theta_hexes = {
        rotation["theta_float64_hex"]
        for round_row in fixture["carrier_path"]["round_ledger"]
        for rotation in round_row["collision_rotations"]
    }
    assert theta_hexes == {p0_fixture["parameters"]["theta_float64_hex"]}
    assert sum(
        len(round_row["collisions"]) for round_row in mapped
    ) == fixture["carrier_path"]["active_axis_rotation_count"]


@requires_screening_artifacts
def test_equivalence_gate_dense_blp_matches_x1_reference_at_1e12() -> None:
    common = _load_screening_common()
    _emitter, fixture = _fixture(rounds=10)
    mapped = _screening_view(fixture)
    gates = common.decode_gate_matrices(fixture)
    states_1 = common.run_trajectory(
        mapped, common.initial_state(fixture, 1), gates
    )
    states_2 = common.run_trajectory(
        mapped, common.initial_state(fixture, 2), gates
    )
    distances = common.blp_trajectory(states_1, states_2)

    reference = json.loads(SCREENING_RESULTS.read_text(encoding="utf-8"))[
        "base_cell"
    ]["candidates"]["X1"]["distances"]
    assert len(distances) == len(reference) == 11
    for index, (got, want) in enumerate(
        zip(distances, reference, strict=True)
    ):
        assert abs(got - want) <= 1e-12, (index, got, want)
