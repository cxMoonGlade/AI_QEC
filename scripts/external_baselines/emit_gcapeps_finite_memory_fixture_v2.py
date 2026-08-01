#!/usr/bin/env python3
"""Emit the neutral GCAPEPS finite-memory fixture v2 (X8 family).

v2 inherits the v1 fixture semantics verbatim -- 2xw ladder geometry, event
masks, gamma grid, axis families, inputs, and coordinate convention -- and adds
exactly the deltas frozen by
``docs/simulator_validation/GCAPEPS_FINITE_MEMORY_FIXTURE_V2_X8_PREREG_2026-08-01.md``:

* one unconditional cross-row ``CX(control = system center site w//2,
  target = memory center site w + w//2)`` on even rounds
  (``round_index % 2 == 0``), inserted as a new layer AFTER the memory
  reverse-CX layers and BEFORE the collision layer.  The insertion position is
  a frozen contract field (the screening verifier measured 1e-2..5e-2
  trajectory shifts for other positions).
* rotation thinning: only collision EVENTS with an even global realized-event
  index keep their rotations, where realized events are enumerated in
  ``(round_index, site_index)`` ascending order across the whole schedule; all
  active-axis rotations of a kept event stay together.  This reproduces the
  screening rule in ``.scratch/gcapeps-fixture-v2/screening/common.py``
  ``make_candidate`` cases "X7"/"X8" exactly.
* ``checkpoint_policy == "every_round"`` (checkpoints are ``0..rounds``).
* a NEW v2 held-out seed derivation (same construction as v1's
  ``HELDOUT_SEED``, v2 namespace string); v1's held-out seed is never reused.
  Pre-run amendment 2 item 1 (2026-08-01) widens the held-out namespace
  admission from one seed to the FIRST TWO seeds of the same derivation
  stream: the SHA-256 digest of the frozen v2 namespace read as consecutive
  big-endian 8-byte windows (``hv2-0`` = bytes 0..8 -- byte-identical to the
  original single-seed derivation -- and ``hv2-1`` = bytes 8..16).  Both
  seeds inherit every collision and anti-build guard; nothing from either
  held-out seed may be built before the owner's release of the confirmatory
  run.

Shared primitives -- canonical JSON/SHA helpers, gate definitions, event
machinery, geometry, inputs, pullback requests -- are imported from the v1
emitter module, which stays untouched.  Like v1, this owner is deterministic
experiment input only: it does not import numpy, Quimb, Stim, SDIM, GCAPEPS,
or ECS.  Validation happens before emission; the CLI writes exactly one
canonical fixture core to stdout without a trailing newline.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


_V1_MODULE_NAME = "_gcapeps_fm_fixture_v1_for_v2"


def _load_v1_emitter():
    if _V1_MODULE_NAME in sys.modules:
        return sys.modules[_V1_MODULE_NAME]
    path = Path(__file__).resolve(strict=True).with_name(
        "emit_gcapeps_finite_memory_fixture.py"
    )
    spec = importlib.util.spec_from_file_location(_V1_MODULE_NAME, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load the v1 fixture emitter module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[_V1_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


_V1 = _load_v1_emitter()

if _V1.FIXTURE_SCHEMA != (
    "error_coupling_simulator.external.gcapeps_finite_memory.fixture.v1"
):
    raise RuntimeError("v1 emitter schema drifted; v2 inheritance is unsafe")
if _V1.SCRIPT_REVISION != "gcapeps-finite-memory-neutral-fixture-v1":
    raise RuntimeError("v1 emitter revision drifted; v2 inheritance is unsafe")

# Shared primitives re-exported from the untouched v1 module.
canonical_json_bytes = _V1.canonical_json_bytes
canonical_sha256 = _V1.canonical_sha256
projection_sha256 = _V1.projection_sha256
fixture_case_id = _V1.fixture_case_id
event_payload = _V1.event_payload
event_bit = _V1.event_bit
RUN_PARTITIONS = _V1.RUN_PARTITIONS
AXIS_FAMILIES = _V1.AXIS_FAMILIES
GAMMA_GRID = _V1.GAMMA_GRID
CALIBRATION_ROUNDS = _V1.CALIBRATION_ROUNDS
P_EVENT_DENOMINATOR = _V1.P_EVENT_DENOMINATOR
ENSEMBLE_PATH_COUNT = _V1.ENSEMBLE_PATH_COUNT
MAX_BOND = _V1.MAX_BOND
PULLBACK_REQUEST_KEYS = _V1.PULLBACK_REQUEST_KEYS
V1_HELDOUT_SEED = _V1.HELDOUT_SEED

FIXTURE_SCHEMA = (
    "error_coupling_simulator.external.gcapeps_finite_memory.fixture.v2"
)
SCRIPT_REVISION = "gcapeps-finite-memory-neutral-fixture-v2"
STATE_CONTRACT_VERSION = "gcapeps-finite-memory-state-contract.v2"
HELDOUT_SEED_NAMESPACE = b"gcapeps-finite-memory-heldout-v2"
_HELDOUT_SEED_DIGEST = hashlib.sha256(HELDOUT_SEED_NAMESPACE).digest()
# Amendment 2 item 1: exactly the FIRST TWO seeds of the derivation stream
# are admitted (hv2-0, hv2-1).
HELDOUT_SEED_ADMITTED_COUNT = 2


def heldout_seed(index: int) -> int:
    """Seed ``hv2-<index>`` of the frozen v2 held-out derivation stream.

    The stream is the SHA-256 digest of ``HELDOUT_SEED_NAMESPACE`` read as
    consecutive big-endian 8-byte windows; index 0 reproduces the original
    single-seed derivation (``digest[:8]``) byte-for-byte.
    """

    if not isinstance(index, int) or isinstance(index, bool):
        raise TypeError("held-out seed index must be a plain int")
    if not 0 <= index < len(_HELDOUT_SEED_DIGEST) // 8:
        raise ValueError(
            "held-out seed index is outside the v2 derivation stream"
        )
    return int.from_bytes(
        _HELDOUT_SEED_DIGEST[8 * index : 8 * (index + 1)], "big"
    )


HELDOUT_SEEDS = tuple(
    heldout_seed(index) for index in range(HELDOUT_SEED_ADMITTED_COUNT)
)
HELDOUT_SEED = HELDOUT_SEEDS[0]  # hv2-0; the original v2 derivation
CROSS_ROW_GATE_KIND = "CX"
CROSS_ROW_ROUND_RESIDUE = 0  # the CX is applied when round_index % 2 == 0
CROSS_ROW_LAYER_INDEX = 6  # after memory reverse-CX (4, 5), before collisions
COLLISION_LAYER_INDEX = 7
CROSS_ROW_LAYER_NAME = "cross_row_cx"
THINNING_MODULUS = 2
THINNING_KEEP_RESIDUE = 0

# Collision guards, inherited by EVERY admitted stream seed (amendment 2
# item 1): no admitted v2 seed may collide with v1's held-out seed, and the
# admitted seeds must be pairwise distinct.
for _admitted_seed in HELDOUT_SEEDS:
    if _admitted_seed == V1_HELDOUT_SEED:
        raise RuntimeError(
            "v2 held-out seed collided with v1's held-out seed"
        )
if len(set(HELDOUT_SEEDS)) != len(HELDOUT_SEEDS):
    raise RuntimeError("v2 held-out stream seeds collided with each other")
del _admitted_seed


def _cross_row_sites(width: int) -> tuple[int, int]:
    """Frozen control/target rule: system center controls memory center."""

    return width // 2, width + width // 2


def _cross_row_clifford_contract(width: int) -> dict[str, Any]:
    control, target = _cross_row_sites(width)
    return {
        "gate_kind": CROSS_ROW_GATE_KIND,
        "control_site": control,
        "control_site_rule": "system_center_width_floor_div_2",
        "target_site": target,
        "target_site_rule": "memory_center_width_plus_width_floor_div_2",
        "round_parity": "even",
        "round_predicate": "round_index % 2 == 0",
        "layer_index": CROSS_ROW_LAYER_INDEX,
        "layer_name": CROSS_ROW_LAYER_NAME,
        "layer_position": (
            "after_memory_reverse_cx_layers_before_collision_layer"
        ),
    }


def _state_contract(width: int) -> dict[str, Any]:
    return {
        "version": STATE_CONTRACT_VERSION,
        "initial_state_kind": "computational_basis_product",
        "joint_state_retained_across_rounds": True,
        "memory_row_policy": "never_discard_reset_or_recreate",
        "candidate_restart_between_rounds": False,
        "physical_round_indexing": "one_based",
        "checkpoint_zero": "initial_state_only",
        "checkpoint_policy": "every_round",
        "unconditional_cross_row_gate": True,
        "cross_row_clifford": _cross_row_clifford_contract(width),
        "rotation_thinning": {
            "rule": "keep_even_global_realized_event_index",
            "event_enumeration": (
                "(round_index,site_index)_ascending_over_realized_events"
            ),
            "modulus": THINNING_MODULUS,
            "keep_residue": THINNING_KEEP_RESIDUE,
            "grouping": (
                "all_active_axis_rotations_of_a_kept_event_stay_together"
            ),
        },
    }


def _thinning_selection(
    event_rows: Sequence[Mapping[str, Any]],
) -> tuple[dict[tuple[int, int], dict[str, int]], int]:
    """Return kept (round, site) -> indices, plus the realized-event count.

    Realized events are enumerated in ``(round_index, site_index)`` ascending
    order; an event keeps its rotations exactly when its global index is even.
    """

    realized = [row for row in event_rows if row["event"]]
    locators = [(row["round_index"], row["site_index"]) for row in realized]
    if locators != sorted(locators) or len(locators) != len(set(locators)):
        raise RuntimeError(
            "event rows are not unique (round, site) ascending; thinning "
            "enumeration would drift"
        )
    kept: dict[tuple[int, int], dict[str, int]] = {}
    for global_index, row in enumerate(realized):
        if global_index % THINNING_MODULUS == THINNING_KEEP_RESIDUE:
            kept[(row["round_index"], row["site_index"])] = {
                "global_event_index": global_index,
                "event_row_index": row["event_row_index"],
            }
    return kept, len(realized)


def _round_ledger(
    *,
    width: int,
    rounds: int,
    active_axes: Sequence[str],
    event_rows: Sequence[Mapping[str, Any]],
    gamma: Mapping[str, Any],
    kept_events: Mapping[tuple[int, int], Mapping[str, int]],
) -> list[dict[str, Any]]:
    """Transform the v1 round ledger with the two frozen v2 deltas.

    The v1 Clifford layers 0..5 are preserved op-for-op in order; the
    cross-row CX layer is inserted at index 6 (after the memory reverse-CX
    layers, before the collisions); the collision layer moves to index 7 and
    keeps only the rotations of even-global-index events.  Operation indices,
    within-layer indices, and collision ordinals are renumbered to stay
    chronological and gapless.
    """

    base = _V1._round_ledger(
        width=width,
        rounds=rounds,
        active_axes=active_axes,
        event_rows=event_rows,
        gamma=gamma,
    )
    control, target = _cross_row_sites(width)
    operation_index = 0
    collision_ordinal = 0
    ledger: list[dict[str, Any]] = []

    for round_row in base:
        round_index = round_row["round_index"]
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
                "v1 memory reverse-CX layers drifted; the frozen insertion "
                "position is unsafe"
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

        cross_operations: list[dict[str, Any]] = []
        if round_index % 2 == CROSS_ROW_ROUND_RESIDUE:
            cross_operations.append(
                _V1._clifford_operation(
                    operation_index=operation_index,
                    round_index=round_index,
                    layer_index=CROSS_ROW_LAYER_INDEX,
                    within_layer_index=0,
                    gate_kind=CROSS_ROW_GATE_KIND,
                    targets=(control, target),
                )
            )
            operation_index += 1
        layer_specs.append((CROSS_ROW_LAYER_NAME, None, cross_operations))

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
                "round_index": round_index,
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
    kept_events, realized_check = _thinning_selection(event_rows)
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
        # v2 thinning outcome: rotations actually present in round_ledger.
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
                "held-out fixture must use one of the two frozen v2 "
                "held-out seeds (hv2-0, hv2-1; amendment 2 item 1)"
            )
        if rounds not in {1, 2, *CALIBRATION_ROUNDS}:
            raise ValueError("held-out rounds are outside the frozen union")

    gamma = _V1._gamma_metadata(gamma_index)
    active_axes = AXIS_FAMILIES[axis_family]
    case_id = fixture_case_id(
        run_partition=run_partition,
        width=width,
        rounds=rounds,
        axis_family=axis_family,
        p_event_numerator=numerator,
        gamma_index=gamma_index,
        seed=seed,
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
            "bounded pure-state 2xw persistent-memory unitary carrier fixture "
            "with an unconditional even-round cross-row CX layer and "
            "even-index collision-event thinning; not a QEC Record, "
            "calibrated device model, or generic PEPS claim"
        ),
        "geometry": _V1._geometry(width),
        "coordinate_convention": _V1._coordinate_convention(width),
        "mask_contract": _V1._mask_contract(),
        "state_contract": _state_contract(width),
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
    """Build one deterministic neutral v2 fixture core."""

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
    """Validate the exact v2 schema/content and return its projection hash.

    Only ``FIXTURE_SCHEMA`` (the ``.v2`` string) is accepted; any other
    schema, including v1's, is rejected without fallback.
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
