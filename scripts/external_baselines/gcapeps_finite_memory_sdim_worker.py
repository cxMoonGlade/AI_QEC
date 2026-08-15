#!/usr/bin/env python3
"""Independent SDIM/Stim signed-pullback corroboration for finite memory.

This qubit-only control consumes the neutral fixture and the separately
collected runtime inventory.  It builds a fresh SDIM tableau and a fresh Stim
tableau for every requested prefix.  It never reads a GCAPEPS candidate,
constructs a PEPS/state vector, or acts as numerical ground truth.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


FRAME_CONTROL_SCHEMA = (
    "error_coupling_simulator.external.gcapeps_finite_memory."
    "sdim_frame_control.v1"
)
INVENTORY_SCHEMA = (
    "error_coupling_simulator.external.gcapeps_finite_memory."
    "sdim_inventory.v1"
)
EXPECTED_STIM_VERSION = "1.16.0"
EXPECTED_SDIM_VERSION = "1.3.3"
REQUEST_KEYS = (
    "run_partition",
    "case_id",
    "input_id",
    "input_preparation_transcript_sha256",
    "shared_evolution_transcript_sha256",
    "round_prefix",
    "collision_ordinal",
    "round_index",
    "site_index",
    "axis_index",
    "physical_pauli_body",
)
REQUEST_KEY_SET = frozenset(REQUEST_KEYS)
SDIM_ROW_KEYS = REQUEST_KEY_SET | frozenset({"sdim_sign", "sdim_body"})
STIM_ROW_KEYS = REQUEST_KEY_SET | frozenset({"stim_sign", "stim_body"})
PULLBACK_ROW_KEYS = REQUEST_KEY_SET | frozenset(
    {
        "sdim_sign",
        "sdim_body",
        "stim_sign",
        "stim_body",
        "sdim_equals_stim",
    }
)


def canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def canonical_sha256(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def projection_sha256(value: Mapping[str, Any]) -> str:
    projected = dict(value)
    projected.pop("result_projection_sha256", None)
    return canonical_sha256(projected)


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _load_sibling(filename: str, module_name: str) -> Any:
    path = Path(__file__).resolve(strict=True).with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load sibling owner {filename}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _load_fixture_owner() -> Any:
    return _load_sibling(
        "emit_gcapeps_finite_memory_fixture.py",
        "_gcapeps_fm_sdim_fixture_owner",
    )


def _load_inventory_owner() -> Any:
    return _load_sibling(
        "collect_gcapeps_finite_memory_sdim_inventory.py",
        "_gcapeps_fm_sdim_inventory_owner",
    )


def _load_timing_owner() -> Any:
    return _load_sibling(
        "gcapeps_finite_memory_timing.py",
        "_gcapeps_fm_sdim_timing_owner",
    )


def _load_sdim() -> Any:
    version = importlib.metadata.version("sdim")
    if version != EXPECTED_SDIM_VERSION:
        raise RuntimeError(
            f"SDIM version drifted: expected {EXPECTED_SDIM_VERSION}, "
            f"got {version}"
        )
    spec = importlib.util.find_spec("sdim")
    if spec is None or spec.origin is None:
        raise RuntimeError("SDIM module origin is unavailable")
    module = importlib.import_module("sdim")
    if getattr(module, "ExtendedTableau", None) is None:
        raise RuntimeError("sdim.ExtendedTableau is unavailable")
    return module


def _load_stim() -> Any:
    version = importlib.metadata.version("stim")
    if version != EXPECTED_STIM_VERSION:
        raise RuntimeError(
            f"Stim version drifted: expected {EXPECTED_STIM_VERSION}, "
            f"got {version}"
        )
    spec = importlib.util.find_spec("stim")
    if spec is None or spec.origin is None:
        raise RuntimeError("Stim module origin is unavailable")
    module = importlib.import_module("stim")
    if getattr(module, "__version__", None) != EXPECTED_STIM_VERSION:
        raise RuntimeError("Stim module version disagrees with its distribution")
    return module


def _plain_int(value: Any, *, label: str, minimum: int = 0) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < minimum
    ):
        raise ValueError(f"{label} must be a non-boolean integer >= {minimum}")
    return value


def request_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
    if not isinstance(row, Mapping) or frozenset(row) != REQUEST_KEY_SET:
        raise ValueError("pullback request has the wrong exact key set")
    return tuple(row[field] for field in REQUEST_KEYS)


def _validate_request_sequence(
    rows: Sequence[Mapping[str, Any]],
) -> list[tuple[Any, ...]]:
    if not isinstance(rows, list):
        raise TypeError("sdim_pullback_requests must be a JSON list")
    keys = [request_key(row) for row in rows]
    if keys != sorted(keys):
        raise ValueError("pullback requests are not in exact lexicographic order")
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate pullback request key")
    return keys


def _request_projection(row: Mapping[str, Any]) -> dict[str, Any]:
    return {field: row[field] for field in REQUEST_KEYS}


def _sdim_input_preparation(
    fixture: Mapping[str, Any],
    request: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    matches = [
        row
        for row in fixture["inputs"]
        if row["input_id"] == request["input_id"]
    ]
    if len(matches) != 1:
        raise ValueError("request input_id is not unique in the fixture")
    input_row = matches[0]
    if (
        input_row["input_preparation_transcript_sha256"]
        != request["input_preparation_transcript_sha256"]
    ):
        raise ValueError("request preparation transcript hash mismatch")
    transcript = input_row["input_preparation_transcript"]
    gates = transcript["gates"]
    if input_row["gc_frame_preparation_gates"] != gates:
        raise ValueError("fixture preparation representations disagree")
    return list(gates)


def _collision_for_request(
    fixture: Mapping[str, Any],
    request: Mapping[str, Any],
) -> Mapping[str, Any]:
    matches = []
    for round_row in fixture["carrier_path"]["round_ledger"]:
        for collision in round_row["collision_rotations"]:
            if collision["collision_ordinal"] == request["collision_ordinal"]:
                matches.append(collision)
    if len(matches) != 1:
        raise ValueError("collision_ordinal is not unique in the fixture")
    collision = matches[0]
    expected = {
        "round_index": collision["round_index"],
        "round_prefix": collision["round_index"],
        "site_index": collision["site_index"],
        "axis_index": collision["axis_index"],
        "physical_pauli_body": collision["physical_pauli_body"],
        "shared_evolution_transcript_sha256": fixture["carrier_path"][
            "shared_evolution_transcript_sha256"
        ],
    }
    if any(request[field] != value for field, value in expected.items()):
        raise ValueError("request collision locator or physical Pauli drifted")
    return collision


def _sdim_clifford_prefix(
    fixture: Mapping[str, Any],
    request: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    prefix = _plain_int(
        request["round_prefix"], label="round_prefix", minimum=1
    )
    if request["round_index"] != prefix:
        raise ValueError("round_prefix and round_index must be identical")
    operations: list[Mapping[str, Any]] = []
    last_operation_index = -1
    for round_row in fixture["carrier_path"]["round_ledger"]:
        round_index = _plain_int(
            round_row["round_index"], label="round_index", minimum=1
        )
        if round_index > prefix:
            break
        for operation in round_row["operations"]:
            operation_index = _plain_int(
                operation["operation_index"], label="operation_index"
            )
            if operation_index <= last_operation_index:
                raise ValueError("fixture operations are not strictly ascending")
            last_operation_index = operation_index
            if operation["operation_class"] == "clifford":
                operations.append(operation)
    if not operations or operations[-1]["round_index"] != prefix:
        raise ValueError("requested Clifford prefix is unavailable")
    return operations


def _stim_input_preparation(
    fixture: Mapping[str, Any],
    request: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    """Independently reconstruct Stim's input preparation from the fixture."""

    matching_input = None
    for input_row in fixture["inputs"]:
        if input_row["input_id"] != request["input_id"]:
            continue
        if matching_input is not None:
            raise ValueError("Stim replay found a duplicate fixture input")
        matching_input = input_row
    if matching_input is None:
        raise ValueError("Stim replay could not find the requested input")
    if (
        request["input_preparation_transcript_sha256"]
        != matching_input["input_preparation_transcript_sha256"]
    ):
        raise ValueError("Stim replay preparation hash mismatch")
    transcript_gates = matching_input["input_preparation_transcript"]["gates"]
    frame_gates = matching_input["gc_frame_preparation_gates"]
    if transcript_gates != frame_gates:
        raise ValueError("Stim replay preparation ledgers disagree")
    return [dict(gate) for gate in transcript_gates]


def _stim_clifford_prefix(
    fixture: Mapping[str, Any],
    request: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    """Independently reconstruct Stim's chronological Clifford prefix."""

    requested_round = _plain_int(
        request["round_prefix"],
        label="Stim round_prefix",
        minimum=1,
    )
    if request["round_index"] != requested_round:
        raise ValueError("Stim round_prefix and round_index disagree")
    selected: list[Mapping[str, Any]] = []
    previous_index = -1
    reached_round = False
    for round_row in fixture["carrier_path"]["round_ledger"]:
        current_round = _plain_int(
            round_row["round_index"],
            label="Stim fixture round_index",
            minimum=1,
        )
        if current_round > requested_round:
            continue
        if current_round == requested_round:
            reached_round = True
        for operation in round_row["operations"]:
            current_index = _plain_int(
                operation["operation_index"],
                label="Stim operation_index",
            )
            if current_index <= previous_index:
                raise ValueError("Stim fixture operation order is not ascending")
            previous_index = current_index
            if operation["operation_class"] == "clifford":
                selected.append(dict(operation))
    if not reached_round or not selected:
        raise ValueError("Stim requested Clifford prefix is unavailable")
    return selected


def _sdim_apply_x_conjugation(tableau: Any, target: int) -> None:
    """Left-compose one qubit X using SDIM's exact phase columns."""

    width = tableau.num_qudits
    target = _plain_int(target, label="X target")
    if target >= width or tableau.dimension != 2 or tableau.order != 4:
        raise ValueError("SDIM X conjugation requires a valid qubit target")
    for column in range(width):
        tableau.destab_phase_vector[column] = (
            int(tableau.destab_phase_vector[column])
            + 2 * int(tableau.destab_z_block[target, column])
        ) % 4
        tableau.phase_vector[column] = (
            int(tableau.phase_vector[column])
            + 2 * int(tableau.z_block[target, column])
        ) % 4
    tableau.modulo()


def _apply_inverse_sdim_gate(tableau: Any, operation: Mapping[str, Any]) -> None:
    token = operation["gate_kind"]
    targets = operation["targets"]
    if token == "H" and len(targets) == 1:
        tableau.hadamard(_plain_int(targets[0], label="H target"))
    elif token == "S" and len(targets) == 1:
        tableau.phase_inv(_plain_int(targets[0], label="S target"))
    elif token == "CX" and len(targets) == 2:
        control = _plain_int(targets[0], label="CX control")
        target = _plain_int(targets[1], label="CX target")
        if control == target:
            raise ValueError("CX control and target must differ")
        tableau.cnot(control, target)
    elif token == "X" and len(targets) == 1:
        _sdim_apply_x_conjugation(
            tableau, _plain_int(targets[0], label="X target")
        )
    else:
        raise ValueError(f"unsupported Clifford operation: {token!r}")
    tableau.modulo()


def _column(
    matrix: Any,
    *,
    column: int,
    width: int,
    label: str,
) -> list[int]:
    if getattr(matrix, "shape", None) != (width, width):
        raise ValueError(f"{label} shape drifted")
    dtype_kind = getattr(getattr(matrix, "dtype", None), "kind", None)
    if dtype_kind not in ("i", "u"):
        raise TypeError(f"{label} must have integer dtype")
    return [int(matrix[row, column]) % 2 for row in range(width)]


def _phase(
    vector: Any,
    *,
    index: int,
    width: int,
    label: str,
) -> int:
    if getattr(vector, "shape", None) != (width,):
        raise ValueError(f"{label} shape drifted")
    dtype_kind = getattr(getattr(vector, "dtype", None), "kind", None)
    if dtype_kind not in ("i", "u"):
        raise TypeError(f"{label} must have integer dtype")
    return int(vector[index]) % 4


def _sdim_generator_image(
    tableau: Any,
    *,
    kind: str,
    target: int,
    width: int,
) -> tuple[int, list[int], list[int]]:
    if kind == "X":
        return (
            _phase(
                tableau.destab_phase_vector,
                index=target,
                width=width,
                label="destab_phase_vector",
            ),
            _column(
                tableau.destab_x_block,
                column=target,
                width=width,
                label="destab_x_block",
            ),
            _column(
                tableau.destab_z_block,
                column=target,
                width=width,
                label="destab_z_block",
            ),
        )
    if kind == "Z":
        return (
            _phase(
                tableau.phase_vector,
                index=target,
                width=width,
                label="phase_vector",
            ),
            _column(
                tableau.x_block,
                column=target,
                width=width,
                label="x_block",
            ),
            _column(
                tableau.z_block,
                column=target,
                width=width,
                label="z_block",
            ),
        )
    raise ValueError("generator kind must be X or Z")


def _sdim_signed_image(
    tableau: Any,
    physical_body: str,
) -> tuple[int, str]:
    """Translate SDIM's ``i^p X^x Z^z`` columns without using Stim."""

    width = tableau.num_qudits
    if (
        not isinstance(physical_body, str)
        or len(physical_body) != width
        or any(label not in "IXYZ" for label in physical_body)
    ):
        raise ValueError("physical Pauli body has invalid width or alphabet")
    phase = sum(label == "Y" for label in physical_body) % 4
    x = [0] * width
    z = [0] * width

    def multiply(generator_phase: int, gx: list[int], gz: list[int]) -> None:
        nonlocal phase, x, z
        phase = (
            phase
            + generator_phase
            + 2 * sum(left * right for left, right in zip(z, gx, strict=True))
        ) % 4
        x = [(left + right) % 2 for left, right in zip(x, gx, strict=True)]
        z = [(left + right) % 2 for left, right in zip(z, gz, strict=True)]

    for target, label in enumerate(physical_body):
        if label in "XY":
            multiply(
                *_sdim_generator_image(
                    tableau, kind="X", target=target, width=width
                )
            )
    for target, label in enumerate(physical_body):
        if label in "ZY":
            multiply(
                *_sdim_generator_image(
                    tableau, kind="Z", target=target, width=width
                )
            )

    body = "".join(
        {
            (0, 0): "I",
            (1, 0): "X",
            (1, 1): "Y",
            (0, 1): "Z",
        }[(xb, zb)]
        for xb, zb in zip(x, z, strict=True)
    )
    relative_phase = (phase - body.count("Y")) % 4
    if relative_phase == 0:
        sign = 1
    elif relative_phase == 2:
        sign = -1
    else:
        raise RuntimeError("SDIM produced a non-Hermitian Pauli image")
    return sign, body


def _sdim_pullback(
    fixture: Mapping[str, Any],
    request: Mapping[str, Any],
    *,
    sdim_module: Any,
) -> tuple[int, str]:
    """Freshly replay one exact ``C^dagger P C`` request in SDIM."""

    width = _plain_int(
        fixture["geometry"]["n_qubits"], label="n_qubits", minimum=1
    )
    _collision_for_request(fixture, request)
    preparation = _sdim_input_preparation(fixture, request)
    cliffords = _sdim_clifford_prefix(fixture, request)
    tableau = sdim_module.ExtendedTableau(
        num_qudits=width,
        dimension=2,
    )
    if (
        tableau.num_qudits != width
        or tableau.dimension != 2
        or tableau.order != 4
    ):
        raise RuntimeError("SDIM did not construct the exact qubit tableau")
    for operation in reversed(cliffords):
        _apply_inverse_sdim_gate(tableau, operation)
    for operation in reversed(preparation):
        _apply_inverse_sdim_gate(tableau, operation)
    return _sdim_signed_image(tableau, request["physical_pauli_body"])


def _stim_signed_image(pauli: Any, *, width: int) -> tuple[int, str]:
    text = str(pauli)
    if len(text) == width + 1 and text[0] in "+-":
        sign_text, labels = text[0], text[1:]
    elif len(text) == width + 2 and text[:2] in ("+i", "-i"):
        raise RuntimeError("Stim produced a non-Hermitian Pauli image")
    else:
        raise RuntimeError("Stim Pauli string has an unexpected representation")
    body = labels.replace("_", "I")
    if len(body) != width or any(label not in "IXYZ" for label in body):
        raise RuntimeError("Stim Pauli body has invalid width or alphabet")
    return (1 if sign_text == "+" else -1), body


def _stim_pullback(
    fixture: Mapping[str, Any],
    request: Mapping[str, Any],
    *,
    stim_module: Any,
) -> tuple[int, str]:
    """Freshly replay the same request in an independently built Stim frame."""

    width = _plain_int(
        fixture["geometry"]["n_qubits"], label="n_qubits", minimum=1
    )
    _collision_for_request(fixture, request)
    preparation = _stim_input_preparation(fixture, request)
    cliffords = _stim_clifford_prefix(fixture, request)
    circuit = stim_module.Circuit()
    for operation in [*preparation, *cliffords]:
        token = operation["gate_kind"]
        targets = operation["targets"]
        if token not in {"H", "S", "CX", "X"}:
            raise ValueError(f"unsupported Stim Clifford operation: {token!r}")
        circuit.append(token, targets)
    tableau = stim_module.Tableau.from_circuit(circuit)
    if len(tableau) != width:
        raise RuntimeError("Stim replay tableau width drifted")
    physical = stim_module.PauliString(
        request["physical_pauli_body"].replace("I", "_")
    )
    pulled = tableau.inverse()(physical)
    return _stim_signed_image(pulled, width=width)


def _replay_sdim_rows(
    fixture: Mapping[str, Any],
    requests: Sequence[Mapping[str, Any]],
    *,
    sdim_module: Any,
) -> list[dict[str, Any]]:
    rows = []
    for request in requests:
        sign, body = _sdim_pullback(
            fixture, request, sdim_module=sdim_module
        )
        rows.append(
            {
                **_request_projection(request),
                "sdim_sign": sign,
                "sdim_body": body,
            }
        )
    return rows


def _replay_stim_rows(
    fixture: Mapping[str, Any],
    requests: Sequence[Mapping[str, Any]],
    *,
    stim_module: Any,
) -> list[dict[str, Any]]:
    rows = []
    for request in requests:
        sign, body = _stim_pullback(
            fixture, request, stim_module=stim_module
        )
        rows.append(
            {
                **_request_projection(request),
                "stim_sign": sign,
                "stim_body": body,
            }
        )
    return rows


def _value_row_keys(
    rows: Sequence[Mapping[str, Any]],
    *,
    exact_keys: frozenset[str],
    sign_name: str,
    body_name: str,
    width: int,
) -> list[tuple[Any, ...]]:
    width = _plain_int(width, label="signed Pauli width", minimum=1)
    keys = []
    for row in rows:
        if not isinstance(row, Mapping) or frozenset(row) != exact_keys:
            raise ValueError(f"{sign_name} replay row key set drifted")
        sign = row[sign_name]
        body = row[body_name]
        if sign not in (-1, 1) or isinstance(sign, bool):
            raise ValueError(f"{sign_name} must be integer -1 or +1")
        if (
            not isinstance(body, str)
            or len(body) != width
            or any(label not in "IXYZ" for label in body)
        ):
            raise ValueError(f"{body_name} has an invalid alphabet")
        keys.append(tuple(row[field] for field in REQUEST_KEYS))
    if len(keys) != len(set(keys)):
        raise ValueError(f"{sign_name} replay contains duplicate keys")
    return keys


def _require_live_inventory_match(
    inventory_core: Mapping[str, Any],
) -> tuple[Any, str]:
    owner = _load_inventory_owner()
    owner.validate_inventory_core(inventory_core)
    expected = inventory_core["inventory_state"]
    live = owner.collect_inventory_state()
    expected_bytes = owner.canonical_json_bytes(expected)
    live_bytes = owner.canonical_json_bytes(live)
    if live_bytes != expected_bytes:
        raise RuntimeError("live SDIM inventory differs from the frozen inventory")
    state_sha256 = hashlib.sha256(live_bytes).hexdigest()
    if state_sha256 != inventory_core["inventory_state_sha256"]:
        raise RuntimeError("live SDIM inventory hash differs from the frozen hash")
    return owner, state_sha256


def build_frame_control_core(
    fixture: Mapping[str, Any],
    *,
    inventory_core: Mapping[str, Any],
) -> dict[str, Any]:
    """Build one role-specific SDIM/Stim core after all exact controls pass."""

    fixture_owner = _load_fixture_owner()
    fixture_projection_sha256 = fixture_owner.validate_fixture(fixture)
    if tuple(fixture_owner.PULLBACK_REQUEST_KEYS) != REQUEST_KEYS:
        raise RuntimeError("fixture pullback-key contract drifted")
    requests = fixture["sdim_pullback_requests"]
    expected_keys = _validate_request_sequence(requests)
    _inventory_owner, inventory_state_sha256 = _require_live_inventory_match(
        inventory_core
    )
    sdim_module = _load_sdim()
    stim_module = _load_stim()

    sdim_rows = _replay_sdim_rows(
        fixture, requests, sdim_module=sdim_module
    )
    stim_rows = _replay_stim_rows(
        fixture, requests, stim_module=stim_module
    )
    sdim_keys = _value_row_keys(
        sdim_rows,
        exact_keys=SDIM_ROW_KEYS,
        sign_name="sdim_sign",
        body_name="sdim_body",
        width=fixture["geometry"]["n_qubits"],
    )
    stim_keys = _value_row_keys(
        stim_rows,
        exact_keys=STIM_ROW_KEYS,
        sign_name="stim_sign",
        body_name="stim_body",
        width=fixture["geometry"]["n_qubits"],
    )
    if expected_keys != sdim_keys or expected_keys != stim_keys:
        raise RuntimeError("exact ordered key gate E == S == T failed")

    pullback_rows: list[dict[str, Any]] = []
    for request, sdim_row, stim_row in zip(
        requests, sdim_rows, stim_rows, strict=True
    ):
        equal = (
            sdim_row["sdim_sign"] == stim_row["stim_sign"]
            and sdim_row["sdim_body"] == stim_row["stim_body"]
        )
        if not equal:
            raise RuntimeError(
                "SDIM/Stim signed pullback mismatch at "
                f"{request_key(request)!r}"
            )
        pullback_rows.append(
            {
                **_request_projection(request),
                "sdim_sign": sdim_row["sdim_sign"],
                "sdim_body": sdim_row["sdim_body"],
                "stim_sign": stim_row["stim_sign"],
                "stim_body": stim_row["stim_body"],
                "sdim_equals_stim": True,
            }
        )

    core: dict[str, Any] = {
        "schema": FRAME_CONTROL_SCHEMA,
        "role": "sdim_stim_qubit_frame_corroboration",
        "fixture_identity": {
            "schema": fixture["schema"],
            "fixture_projection_sha256": fixture_projection_sha256,
            "run_partition": fixture["run_partition"],
            "case_id": fixture["case_id"],
            "width": fixture["geometry"]["width"],
            "n_qubits": fixture["geometry"]["n_qubits"],
            "request_count": len(requests),
        },
        "inventory_binding": {
            "schema": inventory_core["schema"],
            "inventory_state_sha256": inventory_state_sha256,
            "inventory_result_projection_sha256": inventory_core[
                "result_projection_sha256"
            ],
        },
        "scope": {
            "dimension": 2,
            "qubit_only": True,
            "frame_only": True,
            "ground_truth": False,
            "imports_quimb": False,
            "imports_gcapeps": False,
            "receives_candidate_output": False,
            "constructs_peps": False,
            "constructs_state_vector": False,
            "enters_timing_ratio": False,
            "qutrit_evidence": False,
            "leakage_evidence": False,
        },
        "expected_key_sequence": [
            _request_projection(request) for request in requests
        ],
        "sdim_rows": sdim_rows,
        "stim_rows": stim_rows,
        "pullback_rows": pullback_rows,
        "coverage": {
            "expected_count": len(expected_keys),
            "sdim_count": len(sdim_keys),
            "stim_count": len(stim_keys),
            "joined_count": len(pullback_rows),
            "expected_sdim_stim_exact_ordered_sequence": True,
            "duplicates_rejected_before_join": True,
            "empty_sequence_legal_only_if_fixture_empty": True,
        },
        "sdim_equals_stim": True,
        "result_projection_sha256": "",
    }
    core["result_projection_sha256"] = projection_sha256(core)
    validate_frame_control_core(core)
    return core


def validate_frame_control_core(core: Mapping[str, Any]) -> None:
    expected_top = {
        "schema",
        "role",
        "fixture_identity",
        "inventory_binding",
        "scope",
        "expected_key_sequence",
        "sdim_rows",
        "stim_rows",
        "pullback_rows",
        "coverage",
        "sdim_equals_stim",
        "result_projection_sha256",
    }
    if not isinstance(core, Mapping) or set(core) != expected_top:
        raise ValueError("SDIM frame-control core key set drifted")
    if (
        core["schema"] != FRAME_CONTROL_SCHEMA
        or core["role"] != "sdim_stim_qubit_frame_corroboration"
        or core["sdim_equals_stim"] is not True
        or core["result_projection_sha256"] != projection_sha256(core)
    ):
        raise ValueError("SDIM frame-control identity or hash drifted")
    expected_rows = core["expected_key_sequence"]
    expected_keys = _validate_request_sequence(expected_rows)
    fixture_identity = core["fixture_identity"]
    if not isinstance(fixture_identity, Mapping) or set(fixture_identity) != {
        "schema",
        "fixture_projection_sha256",
        "run_partition",
        "case_id",
        "width",
        "n_qubits",
        "request_count",
    }:
        raise ValueError("SDIM fixture identity key set drifted")
    n_qubits = _plain_int(
        fixture_identity["n_qubits"],
        label="fixture n_qubits",
        minimum=1,
    )
    width = _plain_int(
        fixture_identity["width"], label="fixture width", minimum=1
    )
    if (
        2 * width != n_qubits
        or fixture_identity["request_count"] != len(expected_keys)
    ):
        raise ValueError("SDIM fixture width or request count drifted")
    if (
        not _is_sha256(fixture_identity["fixture_projection_sha256"])
        or fixture_identity["run_partition"] not in {"CALIBRATION", "HELDOUT"}
        or not isinstance(fixture_identity["case_id"], str)
        or not fixture_identity["case_id"]
    ):
        raise ValueError("SDIM fixture identity value drifted")
    inventory_binding = core["inventory_binding"]
    if not isinstance(inventory_binding, Mapping) or set(inventory_binding) != {
        "schema",
        "inventory_state_sha256",
        "inventory_result_projection_sha256",
    }:
        raise ValueError("SDIM inventory binding key set drifted")
    if (
        inventory_binding["schema"] != INVENTORY_SCHEMA
        or not _is_sha256(inventory_binding["inventory_state_sha256"])
        or not _is_sha256(
            inventory_binding["inventory_result_projection_sha256"]
        )
    ):
        raise ValueError("SDIM inventory binding value drifted")
    for request in expected_rows:
        if (
            request["run_partition"] != fixture_identity["run_partition"]
            or request["case_id"] != fixture_identity["case_id"]
            or request["input_id"] not in (1, 2)
            or isinstance(request["input_id"], bool)
        ):
            raise ValueError("SDIM request partition, case, or input drifted")
        for field, minimum in (
            ("round_prefix", 1),
            ("collision_ordinal", 0),
            ("round_index", 1),
            ("site_index", 0),
            ("axis_index", 0),
        ):
            _plain_int(
                request[field], label=f"request {field}", minimum=minimum
            )
        if request["round_prefix"] != request["round_index"] or request[
            "axis_index"
        ] not in (0, 1, 2):
            raise ValueError("SDIM request round prefix or axis drifted")
        body = request["physical_pauli_body"]
        if (
            not isinstance(body, str)
            or len(body) != n_qubits
            or any(label not in "IXYZ" for label in body)
        ):
            raise ValueError("SDIM request physical Pauli drifted")
        if (
            not _is_sha256(request["input_preparation_transcript_sha256"])
            or not _is_sha256(request["shared_evolution_transcript_sha256"])
        ):
            raise ValueError("SDIM request transcript hash drifted")
    sdim_rows = core["sdim_rows"]
    stim_rows = core["stim_rows"]
    pullback_rows = core["pullback_rows"]
    sdim_keys = _value_row_keys(
        sdim_rows,
        exact_keys=SDIM_ROW_KEYS,
        sign_name="sdim_sign",
        body_name="sdim_body",
        width=n_qubits,
    )
    stim_keys = _value_row_keys(
        stim_rows,
        exact_keys=STIM_ROW_KEYS,
        sign_name="stim_sign",
        body_name="stim_body",
        width=n_qubits,
    )
    if expected_keys != sdim_keys or expected_keys != stim_keys:
        raise ValueError("SDIM frame-control exact sequence gate drifted")
    if not isinstance(pullback_rows, list) or len(pullback_rows) != len(
        expected_keys
    ):
        raise ValueError("joined pullback row count drifted")
    for index, row in enumerate(pullback_rows):
        if not isinstance(row, Mapping) or frozenset(row) != PULLBACK_ROW_KEYS:
            raise ValueError("joined pullback row key set drifted")
        if tuple(row[field] for field in REQUEST_KEYS) != expected_keys[index]:
            raise ValueError("joined pullback key order drifted")
        if row["sdim_sign"] not in (-1, 1) or row["stim_sign"] not in (-1, 1):
            raise ValueError("joined pullback sign drifted")
        if (
            len(row["sdim_body"]) != n_qubits
            or any(label not in "IXYZ" for label in row["sdim_body"])
            or row["sdim_body"] != row["stim_body"]
            or row["sdim_sign"] != row["stim_sign"]
            or row["sdim_equals_stim"] is not True
        ):
            raise ValueError("joined signed pullback equality drifted")
    coverage = core["coverage"]
    expected_coverage = {
        "expected_count": len(expected_keys),
        "sdim_count": len(sdim_keys),
        "stim_count": len(stim_keys),
        "joined_count": len(pullback_rows),
        "expected_sdim_stim_exact_ordered_sequence": True,
        "duplicates_rejected_before_join": True,
        "empty_sequence_legal_only_if_fixture_empty": True,
    }
    if coverage != expected_coverage:
        raise ValueError("SDIM frame-control coverage ledger drifted")
    if core["scope"] != {
        "dimension": 2,
        "qubit_only": True,
        "frame_only": True,
        "ground_truth": False,
        "imports_quimb": False,
        "imports_gcapeps": False,
        "receives_candidate_output": False,
        "constructs_peps": False,
        "constructs_state_vector": False,
        "enters_timing_ratio": False,
        "qutrit_evidence": False,
        "leakage_evidence": False,
    }:
        raise ValueError("SDIM frame-control scope drifted")


def run_frame_control_worker(
    fixture: Mapping[str, Any],
    *,
    inventory_core: Mapping[str, Any],
) -> dict[str, Any]:
    """Return canonical role core plus standard late-telemetry framing."""

    timing = _load_timing_owner()
    timer = timing.LayeredTimer()
    with timer.span(
        "sdim_frame.root",
        scope="sdim_frame_worker_total",
        kind="worker",
        lane="sdim",
        case_id=fixture.get("case_id"),
    ):
        with timer.span(
            "sdim_frame.replay",
            scope="sdim_stim_independent_replay",
            kind="frame_corroboration",
            lane="sdim",
            case_id=fixture.get("case_id"),
        ):
            core = build_frame_control_core(
                fixture, inventory_core=inventory_core
            )
        with timer.span(
            "sdim_frame.serialize",
            scope="serialization",
            kind="canonical_core_encoding",
            lane="sdim",
            case_id=fixture.get("case_id"),
        ):
            core_bytes = timing.canonical_json_bytes(core)
    timing_payload = timer.finish()
    trailer_bytes = timing.build_late_telemetry_trailer(
        core_bytes, timing_payload
    )
    return {
        "core": core,
        "core_bytes": core_bytes,
        "timing": timing_payload,
        "trailer_bytes": trailer_bytes,
        "framed_bytes": timing.encode_two_frames(core_bytes, trailer_bytes),
    }
