"""Focused controls for the frozen neutral finite-memory fixture v2 (X8).

Covers the frozen v2 deltas over v1 -- even-round cross-row CX layer at the
contracted position, even-global-index rotation thinning, every-round
checkpoints, the v2 held-out seed, and .v2 schema rejection -- plus the
preregistration equivalence gate against the verified screening machinery in
``.scratch/gcapeps-fixture-v2/screening`` (skipped when those development
artifacts are absent).
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
EMITTER_V2 = (
    REPO
    / "scripts"
    / "external_baselines"
    / "emit_gcapeps_finite_memory_fixture_v2.py"
)
EMITTER_V1 = (
    REPO
    / "scripts"
    / "external_baselines"
    / "emit_gcapeps_finite_memory_fixture.py"
)
SCREENING_DIR = REPO / ".scratch" / "gcapeps-fixture-v2" / "screening"
SCREENING_RESULTS = SCREENING_DIR / "x7_x8_results.json"

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


def _load_v2():
    return _load_module(
        EMITTER_V2, "emit_gcapeps_finite_memory_fixture_v2_under_test"
    )


def _load_v1():
    return _load_module(
        EMITTER_V1, "emit_gcapeps_finite_memory_fixture_v1_reference"
    )


def _load_screening_common():
    return _load_module(SCREENING_DIR / "common.py", "_v2_gate_screening_common")


def _fixture(
    *,
    run_partition: str = "HELDOUT",
    width: int = 3,
    rounds: int = 2,
    axis_family: int = 3,
    numerator: int = 4,
    seed: int | None = None,
    gamma_index: int = 2,
    ensemble: bool = False,
):
    emitter = _load_v2()
    if seed is None:
        seed = emitter.HELDOUT_SEED if run_partition == "HELDOUT" else 2
    fixture = emitter.build_fixture(
        run_partition=run_partition,
        width=width,
        rounds=rounds,
        axis_family=axis_family,
        p_event_numerator=numerator,
        seed=seed,
        gamma_index=gamma_index,
        run_blpensemble=ensemble,
    )
    return emitter, fixture


def _realized_locators(fixture) -> list[tuple[int, int]]:
    """Independent recount: realized (round, site) from the mask alone."""

    mask = fixture["carrier_path"]["full_mask"]
    return [
        (row_index + 1, site_index)
        for row_index, row in enumerate(mask)
        for site_index, value in enumerate(row)
        if value
    ]


def _screening_view(fixture) -> list[dict]:
    """Map a v2 fixture operation stream into the screening representation."""

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
    emitter, fixture = _fixture(rounds=2, axis_family=2, numerator=2)

    assert fixture["schema"] == (
        "error_coupling_simulator.external.gcapeps_finite_memory.fixture.v2"
    )
    assert fixture["script_revision"] == (
        "gcapeps-finite-memory-neutral-fixture-v2"
    )
    assert fixture["fixture_id"] == fixture["case_id"]
    assert emitter.validate_fixture(fixture) == fixture[
        "result_projection_sha256"
    ]
    assert emitter.projection_sha256(fixture) == fixture[
        "result_projection_sha256"
    ]

    rebuilt = emitter.build_fixture(
        run_partition="HELDOUT",
        width=3,
        rounds=2,
        axis_family=2,
        p_event_numerator=2,
        seed=emitter.HELDOUT_SEED,
        gamma_index=2,
        run_blpensemble=False,
    )
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


@pytest.mark.parametrize("width", [3, 7])
def test_cross_row_cx_layer_exact_on_even_rounds_at_contracted_position(
    width: int,
) -> None:
    if width == 7:
        emitter, fixture = _fixture(
            run_partition="CALIBRATION",
            width=7,
            rounds=4,
            numerator=3,
            seed=2,
        )
    else:
        emitter, fixture = _fixture(width=3, rounds=4, numerator=4)
    control = width // 2
    target = width + width // 2
    contract = fixture["state_contract"]["cross_row_clifford"]
    assert contract["gate_kind"] == "CX"
    assert contract["control_site"] == control
    assert contract["target_site"] == target
    assert contract["round_parity"] == "even"
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
        cross_layer = round_row["layers"][6]
        cross_operations = [
            operation
            for operation in round_row["operations"]
            if operation["layer_index"] == 6
        ]
        assert cross_layer["operation_indices"] == [
            operation["operation_index"] for operation in cross_operations
        ]
        if round_index % 2 == 0:
            assert len(cross_operations) == 1
            (cross,) = cross_operations
            assert cross["operation_class"] == "clifford"
            assert cross["gate_kind"] == "CX"
            assert cross["matrix_definition"] == "CX"
            assert cross["targets"] == [control, target]
            assert cross["within_layer_index"] == 0
            # Frozen position: strictly after every layer-0..5 Clifford and
            # strictly before every collision rotation of the round.
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
        else:
            assert cross_operations == []
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


@pytest.mark.parametrize("numerator", [2, 3, 4])
def test_thinning_keeps_exactly_even_global_events_vs_mask_recount(
    numerator: int,
) -> None:
    emitter, fixture = _fixture(width=3, rounds=6, numerator=numerator)
    carrier = fixture["carrier_path"]
    active_axes = fixture["parameters"]["active_axes"]

    realized = _realized_locators(fixture)
    expected_kept = [
        locator for index, locator in enumerate(realized) if index % 2 == 0
    ]

    ledger_events: list[tuple[int, int]] = []
    for round_row in carrier["round_ledger"]:
        rotations = round_row["collision_rotations"]
        for start in range(0, len(rotations), len(active_axes)):
            group = rotations[start : start + len(active_axes)]
            locators = {
                (rotation["round_index"], rotation["site_index"])
                for rotation in group
            }
            assert len(locators) == 1
            assert [rotation["axis"] for rotation in group] == active_axes
            ledger_events.append(next(iter(locators)))

    assert ledger_events == expected_kept
    assert carrier["kept_event_count"] == len(expected_kept)
    assert carrier["kept_rotation_count"] == len(expected_kept) * len(
        active_axes
    )
    assert carrier["kept_rotation_count"] == sum(
        len(round_row["collision_rotations"])
        for round_row in carrier["round_ledger"]
    )
    assert carrier["realized_event_count"] == len(realized)
    assert carrier["active_axis_rotation_count"] == len(realized) * len(
        active_axes
    )
    width = fixture["parameters"]["width"]
    assert carrier["kept_event_row_indices"] == [
        (round_index - 1) * width + site_index
        for round_index, site_index in expected_kept
    ]
    global_indices = [
        rotation["global_event_index"]
        for round_row in carrier["round_ledger"]
        for rotation in round_row["collision_rotations"]
    ]
    assert all(index % 2 == 0 for index in global_indices)
    assert sorted(set(global_indices)) == [
        index for index in range(len(realized)) if index % 2 == 0
    ]
    assert len(fixture["sdim_pullback_requests"]) == 2 * carrier[
        "kept_rotation_count"
    ]


def test_all_v1_cliffords_preserved_in_order_and_theta_hex_untouched() -> None:
    v1 = _load_v1()
    emitter, fixture = _fixture(
        run_partition="CALIBRATION", width=7, rounds=4, numerator=3, seed=2
    )
    reference = v1.build_fixture(
        run_partition="CALIBRATION",
        width=7,
        rounds=4,
        axis_family=3,
        p_event_numerator=3,
        seed=2,
        gamma_index=2,
        run_blpensemble=False,
    )
    v1_carrier = reference["carrier_path"]
    v2_carrier = fixture["carrier_path"]

    # Inherited verbatim: masks, event rows, inputs, geometry, convention.
    assert v2_carrier["event_rows"] == v1_carrier["event_rows"]
    assert v2_carrier["full_mask"] == v1_carrier["full_mask"]
    assert fixture["inputs"] == reference["inputs"]
    assert fixture["geometry"] == reference["geometry"]
    assert fixture["coordinate_convention"] == reference[
        "coordinate_convention"
    ]
    assert fixture["mask_contract"] == reference["mask_contract"]
    assert fixture["gate_definitions"] == reference["gate_definitions"]
    assert fixture["parameters"] == reference["parameters"]

    for v1_round, v2_round in zip(
        v1_carrier["round_ledger"], v2_carrier["round_ledger"], strict=True
    ):
        v1_cliffords = [
            (operation["gate_kind"], operation["targets"])
            for operation in v1_round["clifford_operations"]
        ]
        v2_original_cliffords = [
            (operation["gate_kind"], operation["targets"])
            for operation in v2_round["clifford_operations"]
            if operation["layer_index"] <= 5
        ]
        assert v2_original_cliffords == v1_cliffords

        v1_rotations = {
            (
                rotation["round_index"],
                rotation["site_index"],
                rotation["axis"],
            ): rotation
            for rotation in v1_round["collision_rotations"]
        }
        for rotation in v2_round["collision_rotations"]:
            key = (
                rotation["round_index"],
                rotation["site_index"],
                rotation["axis"],
            )
            original = v1_rotations[key]
            assert rotation["theta_float64_hex"] == original[
                "theta_float64_hex"
            ]
            assert rotation["gamma_float64_hex"] == original[
                "gamma_float64_hex"
            ]
            assert rotation["physical_pauli_body"] == original[
                "physical_pauli_body"
            ]
            assert rotation["targets"] == original["targets"]
            assert rotation["event_row_index"] == original["event_row_index"]
            assert rotation["rotation_convention"] == original[
                "rotation_convention"
            ]


def test_checkpoint_policy_every_round_and_state_contract_blocks() -> None:
    for rounds in (1, 4):
        _emitter, fixture = _fixture(width=3, rounds=rounds, numerator=4)
        contract = fixture["state_contract"]
        assert contract["version"] == "gcapeps-finite-memory-state-contract.v2"
        assert contract["checkpoint_policy"] == "every_round"
        assert fixture["checkpoints"] == list(range(rounds + 1))
        assert contract["unconditional_cross_row_gate"] is True
        assert contract["rotation_thinning"] == {
            "rule": "keep_even_global_realized_event_index",
            "event_enumeration": (
                "(round_index,site_index)_ascending_over_realized_events"
            ),
            "modulus": 2,
            "keep_residue": 0,
            "grouping": (
                "all_active_axis_rotations_of_a_kept_event_stay_together"
            ),
        }
        # v1 lifecycle fields survive unchanged.
        assert contract["joint_state_retained_across_rounds"] is True
        assert contract["memory_row_policy"] == (
            "never_discard_reset_or_recreate"
        )
        assert contract["checkpoint_zero"] == "initial_state_only"


def test_v2_heldout_seed_construction_differs_from_v1() -> None:
    emitter = _load_v2()
    v1 = _load_v1()
    expected = int.from_bytes(
        hashlib.sha256(b"gcapeps-finite-memory-heldout-v2").digest()[:8],
        "big",
    )
    assert emitter.HELDOUT_SEED == expected
    assert emitter.V1_HELDOUT_SEED == v1.HELDOUT_SEED
    assert emitter.HELDOUT_SEED != v1.HELDOUT_SEED

    with pytest.raises(ValueError, match="v2 held-out seed"):
        emitter.build_fixture(
            run_partition="HELDOUT",
            width=3,
            rounds=1,
            axis_family=3,
            p_event_numerator=4,
            seed=v1.HELDOUT_SEED,
            gamma_index=0,
            run_blpensemble=False,
        )


def test_grid_gate_rejects_out_of_grid_cells() -> None:
    emitter = _load_v2()

    def build(**overrides):
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
        return emitter.build_fixture(**arguments)

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
    emitter, fixture = _fixture(rounds=1, axis_family=1, numerator=3)
    v1 = _load_v1()

    downgraded = copy.deepcopy(fixture)
    downgraded["schema"] = v1.FIXTURE_SCHEMA
    with pytest.raises(ValueError, match="unsupported fixture schema"):
        emitter.validate_fixture(downgraded)

    unknown = copy.deepcopy(fixture)
    unknown["schema"] = emitter.FIXTURE_SCHEMA + ".draft"
    with pytest.raises(ValueError, match="unsupported fixture schema"):
        emitter.validate_fixture(unknown)

    genuine_v1 = v1.build_fixture(
        run_partition="HELDOUT",
        width=3,
        rounds=1,
        axis_family=1,
        p_event_numerator=3,
        seed=v1.HELDOUT_SEED,
        gamma_index=2,
        run_blpensemble=False,
    )
    with pytest.raises(ValueError, match="unsupported fixture schema"):
        emitter.validate_fixture(genuine_v1)


def test_generator_has_no_candidate_reference_or_simulator_imports() -> None:
    source = EMITTER_V2.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(EMITTER_V2))
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
    emitter = _load_v2()
    process = subprocess.run(
        [
            sys.executable,
            "-I",
            str(EMITTER_V2),
            "--run-partition",
            "HELDOUT",
            "--width",
            "3",
            "--rounds",
            "1",
            "--axis-family",
            "1",
            "--p-event-numerator",
            "0",
            "--seed",
            str(emitter.HELDOUT_SEED),
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


@requires_screening_artifacts
def test_equivalence_gate_operation_stream_matches_screening_x8() -> None:
    common = _load_screening_common()
    p0_fixture = common.build_calibration_fixture(
        seed=2, gamma_index=2, rounds=10
    )
    base_rounds = common.flatten_rounds(p0_fixture)
    reference = common.make_candidate(base_rounds, "X8")

    emitter, fixture = _fixture(
        run_partition="CALIBRATION", width=7, rounds=10, numerator=3, seed=2
    )
    mapped = _screening_view(fixture)

    assert len(mapped) == len(reference) == 10
    for got, want in zip(mapped, reference, strict=True):
        assert got["round_index"] == want["round_index"]
        assert got["cliffords"] == want["cliffords"]
        assert got["candidate_cliffords"] == want["candidate_cliffords"]
        assert got["collisions"] == want["collisions"]

    # Insertions are exactly the even-round CX(3, 10); thinned thetas are
    # hex-identical to the frozen v1 cell value.
    assert [
        (round_row["round_index"], round_row["candidate_cliffords"])
        for round_row in mapped
        if round_row["candidate_cliffords"]
    ] == [
        (round_index, [{"kind": "CX", "targets": (3, 10)}])
        for round_index in (2, 4, 6, 8, 10)
    ]
    theta_hexes = {
        rotation["theta_float64_hex"]
        for round_row in fixture["carrier_path"]["round_ledger"]
        for rotation in round_row["collision_rotations"]
    }
    assert theta_hexes == {p0_fixture["parameters"]["theta_float64_hex"]}
    assert sum(
        len(round_row["collisions"]) for round_row in mapped
    ) == fixture["carrier_path"]["kept_rotation_count"]


@requires_screening_artifacts
def test_equivalence_gate_dense_blp_matches_x8_reference_at_1e12() -> None:
    common = _load_screening_common()
    _emitter, fixture = _fixture(
        run_partition="CALIBRATION", width=7, rounds=10, numerator=3, seed=2
    )
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
    ]["X8"]["distances"]
    assert len(distances) == len(reference) == 11
    for index, (got, want) in enumerate(
        zip(distances, reference, strict=True)
    ):
        assert abs(got - want) <= 1e-12, (index, got, want)
