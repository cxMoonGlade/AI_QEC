#!/usr/bin/env python3
"""Emit the neutral GCAPEPS finite-memory thin-only control-arm fixture.

This is the P2 lever-isolation thin-only arm of the fixture-v2 (X8)
preregistration
``docs/simulator_validation/GCAPEPS_FINITE_MEMORY_FIXTURE_V2_X8_PREREG_2026-08-01.md``
-- the X7-analog: the v1 fixture plus v2's rotation thinning (keep only
collision EVENTS with an even global realized-event index, enumerated in
``(round_index, site_index)`` ascending order across the whole schedule)
and NO cross-row CX layer of any kind (``g_C = 0`` on every round).  The
screening definition this arm reproduces is ``make_candidate(..., "X7")``
in ``.scratch/gcapeps-fixture-v2/screening/common.py`` (SCREENING.md 2x2
row "thinned", column "no CX").

The round-ledger layer structure stays v1's -- seven layers with the
collision layer at index 6 -- because the CX lever's counterpart change
(the inserted layer and the collision-layer displacement) is exactly what
this arm removes.  The frozen thinning rule is imported from the untouched
v2 emitter (``_thinning_selection`` and its contract block), never
re-specified.

Checkpoints are every round (``0..rounds``), matching the confirmatory-cell
protocol.  The arm runs on the SAME cells as the v2 (X8) fixture (prereg P2:
"on the same cells"), so the HELDOUT partition binds the v2 held-out seed
verbatim: a fresh arm namespace would decouple the arm's event masks from
X8's and destroy the 2x2 lever isolation.  No new held-out namespace is
introduced; the v2 derivation is recomputed from its frozen namespace bytes
and collision-guarded against v1's at import.

Like v1 and v2, this owner is deterministic experiment input only: it does
not import numpy, Quimb, Stim, SDIM, GCAPEPS, or ECS.  Validation happens
before emission; the CLI writes exactly one canonical fixture core to
stdout without a trailing newline.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


_V2_MODULE_NAME = "_gcapeps_fm_fixture_v2_for_thin_only_arm"


def _load_v2_emitter():
    if _V2_MODULE_NAME in sys.modules:
        return sys.modules[_V2_MODULE_NAME]
    path = Path(__file__).resolve(strict=True).with_name(
        "emit_gcapeps_finite_memory_fixture_v2.py"
    )
    spec = importlib.util.spec_from_file_location(_V2_MODULE_NAME, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load the v2 fixture emitter module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[_V2_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


_V2 = _load_v2_emitter()

if _V2.FIXTURE_SCHEMA != (
    "error_coupling_simulator.external.gcapeps_finite_memory.fixture.v2"
):
    raise RuntimeError("v2 emitter schema drifted; arm inheritance is unsafe")
if _V2.SCRIPT_REVISION != "gcapeps-finite-memory-neutral-fixture-v2":
    raise RuntimeError("v2 emitter revision drifted; arm inheritance is unsafe")

_V1 = _V2._V1

# Shared primitives re-exported from the untouched v1/v2 modules.
canonical_json_bytes = _V2.canonical_json_bytes
canonical_sha256 = _V2.canonical_sha256
projection_sha256 = _V2.projection_sha256
fixture_case_id = _V2.fixture_case_id
RUN_PARTITIONS = _V2.RUN_PARTITIONS
AXIS_FAMILIES = _V2.AXIS_FAMILIES
GAMMA_GRID = _V2.GAMMA_GRID
CALIBRATION_ROUNDS = _V2.CALIBRATION_ROUNDS
P_EVENT_DENOMINATOR = _V2.P_EVENT_DENOMINATOR
ENSEMBLE_PATH_COUNT = _V2.ENSEMBLE_PATH_COUNT
MAX_BOND = _V2.MAX_BOND
V1_HELDOUT_SEED = _V2.V1_HELDOUT_SEED
V2_HELDOUT_SEED = _V2.HELDOUT_SEED
THINNING_MODULUS = _V2.THINNING_MODULUS
THINNING_KEEP_RESIDUE = _V2.THINNING_KEEP_RESIDUE

FIXTURE_SCHEMA = (
    "error_coupling_simulator.external.gcapeps_finite_memory."
    "fixture_thin_only_arm.v1"
)
SCRIPT_REVISION = "gcapeps-finite-memory-neutral-fixture-thin-only-arm-v1"
STATE_CONTRACT_VERSION = "gcapeps-finite-memory-state-contract.thin-only-arm.v1"
ARM_ID = "thin-only-arm"
SCREENING_TRANSFORM_ANALOG = "X7"
COLLISION_LAYER_INDEX = 6  # v1's position: no cross-row layer is inserted

if FIXTURE_SCHEMA in {_V1.FIXTURE_SCHEMA, _V2.FIXTURE_SCHEMA}:
    raise RuntimeError("arm fixture schema collided with v1/v2 schemas")

# Held-out namespace collision guards.  The arm mints NO namespace of its
# own: P2 compares the arms against X8 on the same cells, so the arm's
# held-out seeds ARE the v2 held-out seeds (amendment 3 item 1 widened the
# admission to the first five hash-chain stream seeds hv2-0..hv2-4; the
# arm inherits all five, with every guard).  Recompute the v2 derivation
# stream -- the frozen chain D0 = sha256(namespace), D1 = sha256(D0) read
# as consecutive big-endian 8-byte windows -- from the frozen namespace
# bytes to pin drift, and re-assert the v1 collision guard so this arm
# cannot silently bind v1's held-out partition.
HELDOUT_SEEDS = _V2.HELDOUT_SEEDS
HELDOUT_SEED = HELDOUT_SEEDS[0]
_heldout_digest_0 = hashlib.sha256(_V2.HELDOUT_SEED_NAMESPACE).digest()
_heldout_digest_1 = hashlib.sha256(_heldout_digest_0).digest()
_heldout_stream = _heldout_digest_0 + _heldout_digest_1
if HELDOUT_SEEDS != tuple(
    int.from_bytes(_heldout_stream[8 * index : 8 * (index + 1)], "big")
    for index in range(len(HELDOUT_SEEDS))
):
    raise RuntimeError(
        "v2 held-out seed derivation drifted; the arm cannot bind the "
        "shared P2 cells"
    )
for _admitted_seed in HELDOUT_SEEDS:
    if _admitted_seed == V1_HELDOUT_SEED:
        raise RuntimeError(
            "v2 held-out seed collided with v1's held-out seed"
        )
if len(set(HELDOUT_SEEDS)) != len(HELDOUT_SEEDS):
    raise RuntimeError("v2 held-out stream seeds collided with each other")
del _admitted_seed, _heldout_digest_0, _heldout_digest_1, _heldout_stream


def _rotation_thinning_contract() -> dict[str, Any]:
    """v2's frozen thinning contract block, cross-checked and reused."""

    block = dict(_V2._state_contract(3)["rotation_thinning"])
    if (
        block["modulus"] != THINNING_MODULUS
        or block["keep_residue"] != THINNING_KEEP_RESIDUE
        or block["rule"] != "keep_even_global_realized_event_index"
    ):
        raise RuntimeError(
            "v2 rotation-thinning contract drifted; arm reuse is unsafe"
        )
    return block


def _state_contract() -> dict[str, Any]:
    return {
        "version": STATE_CONTRACT_VERSION,
        "arm": ARM_ID,
        "screening_transform_analog": SCREENING_TRANSFORM_ANALOG,
        "initial_state_kind": "computational_basis_product",
        "joint_state_retained_across_rounds": True,
        "memory_row_policy": "never_discard_reset_or_recreate",
        "candidate_restart_between_rounds": False,
        "physical_round_indexing": "one_based",
        "checkpoint_zero": "initial_state_only",
        "checkpoint_policy": "every_round",
        "unconditional_cross_row_gate": False,
        "rotation_thinning": _rotation_thinning_contract(),
    }


def _round_ledger(
    *,
    width: int,
    rounds: int,
    active_axes: Sequence[str],
    event_rows: Sequence[Mapping[str, Any]],
    gamma: Mapping[str, Any],
    kept_events: Mapping[tuple[int, int], Mapping[str, int]],
) -> list[dict[str, Any]]:
    """Transform the v1 round ledger with the single thin-only arm delta.

    The v1 Clifford layers 0..5 are preserved op-for-op in order; NO
    cross-row layer is inserted; the collision layer stays at v1's index 6
    and keeps only the rotations of even-global-index events.  Operation
    indices, within-layer indices, and collision ordinals are renumbered to
    stay chronological and gapless.
    """

    base = _V1._round_ledger(
        width=width,
        rounds=rounds,
        active_axes=active_axes,
        event_rows=event_rows,
        gamma=gamma,
    )
    operation_index = 0
    collision_ordinal = 0
    ledger: list[dict[str, Any]] = []

    for round_row in base:
        v1_layers = round_row["layers"]
        v1_layer_names = [layer["layer_name"] for layer in v1_layers]
        if (
            len(v1_layer_names) != 7
            or v1_layer_names[-1] != "event_conditioned_collisions"
        ):
            raise RuntimeError("v1 round layer structure drifted")
        if not all(
            name.startswith("memory_reverse_cx_parity_")
            for name in v1_layer_names[4:6]
        ):
            raise RuntimeError(
                "v1 memory reverse-CX layers drifted; the frozen layer "
                "structure is unsafe"
            )

        cliffords_by_layer: dict[int, list[Mapping[str, Any]]] = {}
        v1_collisions: list[Mapping[str, Any]] = []
        for operation in round_row["operations"]:
            if operation["operation_class"] == "clifford":
                cliffords_by_layer.setdefault(
                    operation["layer_index"], []
                ).append(operation)
            elif operation["operation_class"] == "collision_rotation":
                v1_collisions.append(operation)
            else:
                raise RuntimeError("unknown operation class in v1 ledger")
        if set(cliffords_by_layer) - set(range(6)):
            raise RuntimeError("v1 clifford layer indices drifted")

        layer_specs: list[tuple[str, int | None, list[dict[str, Any]]]] = []
        for layer in v1_layers[:6]:
            operations: list[dict[str, Any]] = []
            for operation in cliffords_by_layer.get(layer["layer_index"], []):
                renumbered = dict(operation)
                renumbered["operation_index"] = operation_index
                operation_index += 1
                operations.append(renumbered)
            layer_specs.append(
                (layer["layer_name"], layer["parity"], operations)
            )

        kept_rotations: list[dict[str, Any]] = []
        for operation in v1_collisions:
            locator = (operation["round_index"], operation["site_index"])
            kept_row = kept_events.get(locator)
            if kept_row is None:
                continue
            renumbered = dict(operation)
            renumbered["operation_index"] = operation_index
            renumbered["layer_index"] = COLLISION_LAYER_INDEX
            renumbered["within_layer_index"] = len(kept_rotations)
            renumbered["collision_ordinal"] = collision_ordinal
            renumbered["global_event_index"] = kept_row["global_event_index"]
            operation_index += 1
            collision_ordinal += 1
            kept_rotations.append(renumbered)
        layer_specs.append(
            ("event_conditioned_collisions", None, kept_rotations)
        )

        operations = [
            operation
            for _name, _parity, layer_operations in layer_specs
            for operation in layer_operations
        ]
        ledger.append(
            {
                "round_index": round_row["round_index"],
                "layers": [
                    {
                        "layer_index": layer_index,
                        "layer_name": name,
                        "parity": parity,
                        "operation_indices": [
                            operation["operation_index"]
                            for operation in layer_operations
                        ],
                    }
                    for layer_index, (name, parity, layer_operations) in (
                        enumerate(layer_specs)
                    )
                ],
                "operations": operations,
                "clifford_operations": [
                    operation
                    for operation in operations
                    if operation["operation_class"] == "clifford"
                ],
                "collision_rotations": [
                    operation
                    for operation in operations
                    if operation["operation_class"] == "collision_rotation"
                ],
            }
        )
    return ledger


def _build_path(
    *,
    namespace: str,
    seed: int,
    mask_index: int,
    width: int,
    rounds: int,
    p_event_numerator: int,
    active_axes: Sequence[str],
    gamma: Mapping[str, Any],
    weight_numerator: int,
    weight_denominator: int,
) -> dict[str, Any]:
    event_rows, full_mask = _V1._event_rows(
        namespace=namespace,
        seed=seed,
        mask_index=mask_index,
        width=width,
        rounds=rounds,
        p_event_numerator=p_event_numerator,
    )
    realized = sum(int(value) for row in full_mask for value in row)
    eligible = width * rounds
    kept_events, realized_check = _V2._thinning_selection(event_rows)
    if realized_check != realized:
        raise RuntimeError("realized-event recount drifted during thinning")
    round_ledger = _round_ledger(
        width=width,
        rounds=rounds,
        active_axes=active_axes,
        event_rows=event_rows,
        gamma=gamma,
        kept_events=kept_events,
    )
    ledger_rotation_count = sum(
        len(round_row["collision_rotations"]) for round_row in round_ledger
    )
    if ledger_rotation_count != len(kept_events) * len(active_axes):
        raise RuntimeError("kept-rotation count drifted from the ledger")
    if any(
        operation["layer_index"] > 5
        for round_row in round_ledger
        for operation in round_row["clifford_operations"]
    ):
        raise RuntimeError("thin-only arm acquired a cross-row layer")
    return {
        "namespace": namespace,
        "mask_index": mask_index,
        "seed": seed,
        "weight_numerator": weight_numerator,
        "weight_denominator": weight_denominator,
        "event_rows": event_rows,
        "event_rows_sha256": canonical_sha256(event_rows),
        "full_mask": full_mask,
        "full_mask_sha256": canonical_sha256(full_mask),
        "eligible_collision_count": eligible,
        "realized_event_count": realized,
        "realized_event_fraction": {
            "numerator": realized,
            "denominator": eligible,
        },
        # v1 meaning retained: rotations implied by the mask BEFORE thinning.
        "active_axis_rotation_count": realized * len(active_axes),
        # thinning outcome: rotations actually present in round_ledger.
        "kept_event_count": len(kept_events),
        "kept_event_row_indices": [
            row["event_row_index"] for row in kept_events.values()
        ],
        "kept_rotation_count": len(kept_events) * len(active_axes),
        "mask_multiplicity": 1,
        "distinct_mask_count": 1,
        "round_ledger": round_ledger,
        "shared_evolution_transcript_sha256": canonical_sha256(round_ledger),
    }


def _build_fixture_unvalidated(
    *,
    run_partition: str,
    width: int,
    rounds: int,
    axis_family: int,
    p_event_numerator: int,
    seed: int,
    gamma_index: int,
    run_blpensemble: bool,
) -> dict[str, Any]:
    if run_partition not in RUN_PARTITIONS:
        raise ValueError(f"run_partition must be one of {RUN_PARTITIONS}")
    width = _V1._require_plain_int("width", width, minimum=1, maximum=7)
    if width not in (3, 5, 7):
        raise ValueError("width must be one of the frozen values 3, 5, 7")
    rounds = _V1._require_plain_int("rounds", rounds, minimum=1)
    axis_family = _V1._require_plain_int("axis_family", axis_family, minimum=1)
    if axis_family not in AXIS_FAMILIES:
        raise ValueError("axis_family must be one of 1, 2, 3")
    numerator = _V1._require_plain_int(
        "p_event_numerator", p_event_numerator, maximum=P_EVENT_DENOMINATOR
    )
    seed = _V1._require_uint64("seed", seed)
    if not isinstance(run_blpensemble, bool):
        raise TypeError("run_blpensemble must be a bool")
    if run_partition == "CALIBRATION":
        if (
            width != 7
            or rounds not in CALIBRATION_ROUNDS
            or axis_family != 3
            or numerator != 3
            or seed not in range(4)
        ):
            raise ValueError(
                "calibration fixture identity is outside the frozen grid"
            )
        if run_blpensemble:
            raise ValueError(
                "calibration fixtures cannot materialize BLPENSEMBLE"
            )
    else:
        if seed not in HELDOUT_SEEDS:
            raise ValueError(
                "held-out arm fixture must use one of the five frozen v2 "
                "held-out seeds shared by the P2 cells (hv2-0..hv2-4; "
                "amendment 3 item 1)"
            )
        if rounds not in {1, 2, *CALIBRATION_ROUNDS}:
            raise ValueError("held-out rounds are outside the frozen union")

    gamma = _V1._gamma_metadata(gamma_index)
    active_axes = AXIS_FAMILIES[axis_family]
    case_id = "{}-{}".format(
        ARM_ID,
        fixture_case_id(
            run_partition=run_partition,
            width=width,
            rounds=rounds,
            axis_family=axis_family,
            p_event_numerator=numerator,
            gamma_index=gamma_index,
            seed=seed,
        ),
    )
    carrier_path = _build_path(
        namespace="CARRIER",
        seed=seed,
        mask_index=0,
        width=width,
        rounds=rounds,
        p_event_numerator=numerator,
        active_axes=active_axes,
        gamma=gamma,
        weight_numerator=1,
        weight_denominator=1,
    )
    inputs = _V1._inputs(width)

    ensemble_paths: list[dict[str, Any]] = []
    if run_blpensemble:
        for mask_index in range(ENSEMBLE_PATH_COUNT):
            ensemble_paths.append(
                _build_path(
                    namespace="BLPENSEMBLE",
                    seed=seed,
                    mask_index=mask_index,
                    width=width,
                    rounds=rounds,
                    p_event_numerator=numerator,
                    active_axes=active_axes,
                    gamma=gamma,
                    weight_numerator=1,
                    weight_denominator=ENSEMBLE_PATH_COUNT,
                )
            )
    ensemble_distinct = _V1._assign_mask_multiplicity(ensemble_paths)

    checkpoints = list(range(rounds + 1))
    parameters = {
        "width": width,
        "rounds": rounds,
        "axis_family": axis_family,
        "active_axes": list(active_axes),
        "p_event_numerator": numerator,
        "p_event_denominator": P_EVENT_DENOMINATOR,
        "seed": seed,
        **gamma,
        "max_bond": MAX_BOND,
    }
    result = {
        "schema": FIXTURE_SCHEMA,
        "script_revision": SCRIPT_REVISION,
        "fixture_id": case_id,
        "run_partition": run_partition,
        "case_id": case_id,
        "claim_boundary": (
            "bounded pure-state 2xw persistent-memory unitary carrier "
            "fixture with even-index collision-event thinning and no "
            "cross-row CX layer; P2 lever-isolation thin-only control arm "
            "(X7-analog) of the v2 X8 family; not a QEC Record, calibrated "
            "device model, or generic PEPS claim"
        ),
        "geometry": _V1._geometry(width),
        "coordinate_convention": _V1._coordinate_convention(width),
        "mask_contract": _V1._mask_contract(),
        "state_contract": _state_contract(),
        "gate_definitions": _V1._gate_definitions(),
        "parameters": parameters,
        "inputs": inputs,
        "checkpoints": checkpoints,
        "carrier_path": carrier_path,
        "blpensemble": {
            "enabled": run_blpensemble,
            "registered_path_count": ENSEMBLE_PATH_COUNT,
            "path_count": len(ensemble_paths),
            "weight_numerator": 1,
            "weight_denominator": ENSEMBLE_PATH_COUNT,
            "distinct_mask_count": ensemble_distinct,
            "paths": ensemble_paths,
        },
        "sdim_pullback_requests": _V1._pullback_requests(
            run_partition=run_partition,
            case_id=case_id,
            inputs=inputs,
            carrier_path=carrier_path,
        ),
    }
    return _V1._with_projection_sha256(result)


def build_fixture(
    *,
    run_partition: str,
    width: int,
    rounds: int,
    axis_family: int,
    p_event_numerator: int,
    seed: int,
    gamma_index: int,
    run_blpensemble: bool,
) -> dict[str, Any]:
    """Build one deterministic neutral thin-only arm fixture core."""

    return _build_fixture_unvalidated(
        run_partition=run_partition,
        width=width,
        rounds=rounds,
        axis_family=axis_family,
        p_event_numerator=p_event_numerator,
        seed=seed,
        gamma_index=gamma_index,
        run_blpensemble=run_blpensemble,
    )


def validate_fixture(fixture: Mapping[str, Any]) -> str:
    """Validate the exact arm schema/content and return its projection hash.

    Only ``FIXTURE_SCHEMA`` (the ``fixture_thin_only_arm.v1`` string) is
    accepted; any other schema, including v1's, v2's, and the CX-only
    arm's, is rejected without fallback.
    """

    if not isinstance(fixture, Mapping):
        raise TypeError("fixture must be a mapping")
    expected_top = {
        "schema",
        "script_revision",
        "fixture_id",
        "run_partition",
        "case_id",
        "claim_boundary",
        "geometry",
        "coordinate_convention",
        "mask_contract",
        "state_contract",
        "gate_definitions",
        "parameters",
        "inputs",
        "checkpoints",
        "carrier_path",
        "blpensemble",
        "sdim_pullback_requests",
        "result_projection_sha256",
    }
    if set(fixture) != expected_top:
        raise ValueError("fixture top-level key set is not exact")
    if fixture["schema"] != FIXTURE_SCHEMA:
        raise ValueError(
            f"unsupported fixture schema: {fixture['schema']!r}; "
            f"this validator accepts only {FIXTURE_SCHEMA!r}"
        )
    parameters = fixture.get("parameters")
    ensemble = fixture.get("blpensemble")
    if not isinstance(parameters, Mapping) or not isinstance(ensemble, Mapping):
        raise ValueError("fixture parameters and blpensemble must be mappings")
    try:
        expected = _build_fixture_unvalidated(
            run_partition=fixture["run_partition"],
            width=parameters["width"],
            rounds=parameters["rounds"],
            axis_family=parameters["axis_family"],
            p_event_numerator=parameters["p_event_numerator"],
            seed=parameters["seed"],
            gamma_index=parameters["gamma_index"],
            run_blpensemble=ensemble["enabled"],
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(
            "fixture cannot be reconstructed from its identity"
        ) from error
    if canonical_json_bytes(fixture) != canonical_json_bytes(expected):
        raise ValueError("fixture differs from deterministic reconstruction")
    digest = projection_sha256(fixture)
    if fixture["result_projection_sha256"] != digest:
        raise ValueError("fixture result_projection_sha256 mismatch")
    return digest


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-partition", choices=RUN_PARTITIONS, required=True)
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--rounds", type=int, required=True)
    parser.add_argument(
        "--axis-family", type=int, choices=tuple(AXIS_FAMILIES), required=True
    )
    parser.add_argument(
        "--p-event-numerator", type=int, choices=range(5), required=True
    )
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument(
        "--gamma-index", type=int, choices=range(len(GAMMA_GRID)), required=True
    )
    parser.add_argument("--run-blpensemble", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Emit exactly one canonical fixture core to stdout, without a newline."""

    args = _parse_args(argv)
    fixture = build_fixture(
        run_partition=args.run_partition,
        width=args.width,
        rounds=args.rounds,
        axis_family=args.axis_family,
        p_event_numerator=args.p_event_numerator,
        seed=args.seed,
        gamma_index=args.gamma_index,
        run_blpensemble=args.run_blpensemble,
    )
    validate_fixture(fixture)
    sys.stdout.buffer.write(canonical_json_bytes(fixture))
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
