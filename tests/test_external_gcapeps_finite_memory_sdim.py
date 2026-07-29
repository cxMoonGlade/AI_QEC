"""Focused controls for finite-memory SDIM/Stim corroboration owners."""

from __future__ import annotations

import ast
import copy
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


REPO = Path(__file__).resolve().parents[1]
BASELINE = REPO / "scripts" / "external_baselines"
EMITTER_PATH = BASELINE / "emit_gcapeps_finite_memory_fixture.py"
INVENTORY_PATH = (
    BASELINE / "collect_gcapeps_finite_memory_sdim_inventory.py"
)
WORKER_PATH = BASELINE / "gcapeps_finite_memory_sdim_worker.py"
TIMING_PATH = BASELINE / "gcapeps_finite_memory_timing.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _emitter():
    return _load(EMITTER_PATH, "_fm_sdim_test_emitter")


def _inventory():
    return _load(INVENTORY_PATH, "_fm_sdim_test_inventory")


def _worker():
    return _load(WORKER_PATH, "_fm_sdim_test_worker")


def _timing():
    return _load(TIMING_PATH, "_fm_sdim_test_timing")


def _declared_runtime_available() -> bool:
    try:
        return (
            sys.version_info[:3] == (3, 12, 13)
            and importlib.metadata.version("stim") == "1.16.0"
            and importlib.metadata.version("sdim") == "1.3.3"
        )
    except importlib.metadata.PackageNotFoundError:
        return False


requires_declared_sdim = pytest.mark.skipif(
    not _declared_runtime_available(),
    reason=(
        "finite-memory frame control requires the declared Python 3.12.13, "
        "Stim 1.16.0, and SDIM 1.3.3 environment"
    ),
)


def _small_fixture(*, rounds: int = 1):
    emitter = _emitter()
    return emitter.build_fixture(
        run_partition="HELDOUT",
        width=3,
        rounds=rounds,
        axis_family=3,
        p_event_numerator=4,
        seed=emitter.HELDOUT_SEED,
        gamma_index=0,
        run_blpensemble=False,
    )


@requires_declared_sdim
def _live_inventory_core():
    inventory = _inventory()
    return inventory.build_inventory_core(
        inventory.collect_inventory_state()
    )


def _import_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add(node.module or "")
    return names


def test_computation_source_has_static_candidate_and_evaluator_firewall() -> None:
    imports = _import_roots(WORKER_PATH)
    forbidden = {
        name
        for name in imports
        if name == "quimb"
        or name.startswith("quimb.")
        or name == "error_coupling_simulator"
        or name.startswith("error_coupling_simulator.")
        or name == "numpy"
        or name.startswith("numpy.")
    }
    assert forbidden == set()
    source = WORKER_PATH.read_text(encoding="utf-8")
    assert "candidate_output" not in source.replace(
        '"receives_candidate_output"', ""
    )
    assert "compare_gcapeps_finite_memory_bond32" not in source


def test_inventory_source_does_not_import_quimb_or_gcapeps() -> None:
    imports = _import_roots(INVENTORY_PATH)
    assert not any(
        name == "quimb" or name.startswith("quimb.") for name in imports
    )
    assert not any("gcapeps" in name.lower() for name in imports)


def test_distribution_normalization_rejects_duplicate_names(
    tmp_path: Path,
) -> None:
    inventory = _inventory()

    class FakeDistribution:
        def __init__(self, name: str, version: str, path: Path):
            self.metadata = {"Name": name}
            self.version = version
            self._path = path

    first_path = tmp_path / "A_B-1.dist-info"
    second_path = tmp_path / "a-b-2.dist-info"
    first_path.mkdir()
    second_path.mkdir()
    distributions = [
        FakeDistribution("A_B", "1", first_path),
        FakeDistribution("a-b", "2", second_path),
    ]
    with pytest.raises(
        RuntimeError, match="duplicate normalized installed-distribution"
    ):
        inventory.collect_distribution_records(distributions)


@requires_declared_sdim
def test_inventory_binds_complete_declared_runtime_and_editable_fork() -> None:
    inventory = _inventory()
    state = inventory.collect_inventory_state()
    inventory.validate_inventory_state(state)
    core = inventory.build_inventory_core(state)
    inventory.validate_inventory_core(core)

    records = state["installed_distributions"]["records"]
    normalized_names = [row["normalized_name"] for row in records]
    assert normalized_names == sorted(normalized_names)
    assert len(normalized_names) == len(set(normalized_names))
    versions = {row["normalized_name"]: row["version"] for row in records}
    assert versions["stim"] == "1.16.0"
    assert versions["sdim"] == "1.3.3"
    assert "quimb" in versions
    assert state["python"]["version"] == "3.12.13"
    assert state["editable_quimb"]["direct_url_editable"] is True
    assert state["editable_quimb"]["origin_within_checkout"] is True
    assert isinstance(state["editable_quimb"]["clean"], bool)
    assert len(state["editable_quimb"]["commit"]) == 40
    assert len(state["editable_quimb"]["tree"]) == 40
    assert core["inventory_state_sha256"] == inventory.canonical_sha256(
        state
    )
    assert core["result_projection_sha256"] == inventory.projection_sha256(
        core
    )


@requires_declared_sdim
def test_both_inputs_all_requests_replay_with_exact_sdim_stim_equality() -> None:
    worker = _worker()
    fixture = _small_fixture(rounds=2)
    core = worker.build_frame_control_core(
        fixture,
        inventory_core=_live_inventory_core(),
    )
    worker.validate_frame_control_core(core)

    expected = fixture["sdim_pullback_requests"]
    assert core["expected_key_sequence"] == expected
    assert len(core["sdim_rows"]) == len(expected)
    assert len(core["stim_rows"]) == len(expected)
    assert len(core["pullback_rows"]) == len(expected)
    assert {row["input_id"] for row in core["pullback_rows"]} == {1, 2}
    assert all(row["sdim_equals_stim"] for row in core["pullback_rows"])
    assert all(
        row["sdim_sign"] == row["stim_sign"]
        and row["sdim_body"] == row["stim_body"]
        for row in core["pullback_rows"]
    )
    assert all(
        len(row["sdim_body"]) == fixture["geometry"]["n_qubits"]
        for row in core["pullback_rows"]
    )

    def collision_identity(row):
        return (
            row["round_prefix"],
            row["collision_ordinal"],
            row["round_index"],
            row["site_index"],
            row["axis_index"],
            row["physical_pauli_body"],
        )

    by_input = {
        input_id: {
            collision_identity(row): (row["sdim_sign"], row["sdim_body"])
            for row in core["pullback_rows"]
            if row["input_id"] == input_id
        }
        for input_id in (1, 2)
    }
    assert set(by_input[1]) == set(by_input[2])
    assert any(
        by_input[1][key] != by_input[2][key] for key in by_input[1]
    )


@requires_declared_sdim
def test_empty_sequence_is_legal_exactly_when_fixture_requests_are_empty() -> None:
    emitter = _emitter()
    fixture = emitter.build_fixture(
        run_partition="HELDOUT",
        width=3,
        rounds=1,
        axis_family=3,
        p_event_numerator=0,
        seed=emitter.HELDOUT_SEED,
        gamma_index=0,
        run_blpensemble=False,
    )
    assert fixture["sdim_pullback_requests"] == []
    worker = _worker()
    core = worker.build_frame_control_core(
        fixture,
        inventory_core=_live_inventory_core(),
    )
    worker.validate_frame_control_core(core)
    assert core["expected_key_sequence"] == []
    assert core["sdim_rows"] == []
    assert core["stim_rows"] == []
    assert core["pullback_rows"] == []


@requires_declared_sdim
@pytest.mark.parametrize("corruption", ["sign", "support", "order"])
def test_sign_support_and_order_corruptions_fail_before_core(
    monkeypatch: pytest.MonkeyPatch,
    corruption: str,
) -> None:
    worker = _worker()
    fixture = _small_fixture()
    inventory_core = _live_inventory_core()

    if corruption in {"sign", "support"}:
        original = worker._sdim_pullback
        calls = 0

        def corrupt_sdim(*args, **kwargs):
            nonlocal calls
            sign, body = original(*args, **kwargs)
            calls += 1
            if calls != 1:
                return sign, body
            if corruption == "sign":
                return -sign, body
            active = next(index for index, label in enumerate(body) if label != "I")
            return sign, body[:active] + "I" + body[active + 1 :]

        monkeypatch.setattr(worker, "_sdim_pullback", corrupt_sdim)
        match = "signed pullback mismatch"
    else:
        original = worker._replay_stim_rows

        def reverse_stim(*args, **kwargs):
            return list(reversed(original(*args, **kwargs)))

        monkeypatch.setattr(worker, "_replay_stim_rows", reverse_stim)
        match = "E == S == T"

    with pytest.raises(RuntimeError, match=match):
        worker.build_frame_control_core(
            fixture,
            inventory_core=inventory_core,
        )


@requires_declared_sdim
@pytest.mark.parametrize("corruption", ["preparation", "round_prefix"])
def test_preparation_and_prefix_corruptions_break_independent_replay(
    monkeypatch: pytest.MonkeyPatch,
    corruption: str,
) -> None:
    worker = _worker()
    fixture = _small_fixture(rounds=2)
    inventory_core = _live_inventory_core()
    if corruption == "preparation":
        original = worker._sdim_input_preparation

        def omit_input_two_preparation(fixture_arg, request):
            gates = original(fixture_arg, request)
            return [] if request["input_id"] == 2 else gates

        monkeypatch.setattr(
            worker, "_sdim_input_preparation", omit_input_two_preparation
        )
    else:
        original = worker._sdim_clifford_prefix

        def omit_last_prefix_gate(fixture_arg, request):
            gates = original(fixture_arg, request)
            return gates[:-1]

        monkeypatch.setattr(
            worker, "_sdim_clifford_prefix", omit_last_prefix_gate
        )

    with pytest.raises(RuntimeError, match="signed pullback mismatch"):
        worker.build_frame_control_core(
            fixture,
            inventory_core=inventory_core,
        )


@requires_declared_sdim
def test_live_inventory_drift_fails_before_sdim_or_stim_replay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    worker = _worker()
    inventory = _inventory()
    state = inventory.collect_inventory_state()
    core = inventory.build_inventory_core(state)
    drifted = copy.deepcopy(state)
    drifted["editable_quimb"]["clean"] = not drifted["editable_quimb"]["clean"]

    class DriftedInventoryOwner:
        validate_inventory_core = staticmethod(inventory.validate_inventory_core)
        canonical_json_bytes = staticmethod(inventory.canonical_json_bytes)

        @staticmethod
        def collect_inventory_state():
            return drifted

    monkeypatch.setattr(
        worker,
        "_load_inventory_owner",
        lambda: DriftedInventoryOwner,
    )
    monkeypatch.setattr(
        worker,
        "_load_sdim",
        lambda: pytest.fail("SDIM replay ran after inventory drift"),
    )
    with pytest.raises(RuntimeError, match="live SDIM inventory differs"):
        worker.build_frame_control_core(
            _small_fixture(),
            inventory_core=core,
        )


@requires_declared_sdim
def test_standard_two_frame_outputs_bind_canonical_cores() -> None:
    inventory = _inventory()
    worker = _worker()
    timing = _timing()

    inventory_result = inventory.run_inventory_worker()
    inventory_core_raw, inventory_trailer_raw = timing.decode_two_frames(
        inventory_result["framed_bytes"],
        core_max=16 * 1024 * 1024,
        trailer_max=16 * 1024 * 1024,
    )
    assert inventory_core_raw == inventory_result["core_bytes"]
    inventory.validate_inventory_core(json.loads(inventory_core_raw))
    inventory_trailer = json.loads(inventory_trailer_raw)
    assert inventory_trailer["core_sha256"] == timing.sha256_hex(
        inventory_core_raw
    )

    frame_result = worker.run_frame_control_worker(
        _small_fixture(),
        inventory_core=inventory_result["core"],
    )
    frame_core_raw, frame_trailer_raw = timing.decode_two_frames(
        frame_result["framed_bytes"],
        core_max=64 * 1024 * 1024,
        trailer_max=16 * 1024 * 1024,
    )
    assert frame_core_raw == frame_result["core_bytes"]
    worker.validate_frame_control_core(json.loads(frame_core_raw))
    frame_trailer = json.loads(frame_trailer_raw)
    assert frame_trailer["core_sha256"] == timing.sha256_hex(frame_core_raw)

@requires_declared_sdim
def test_inventory_direct_cli_defines_all_validation_helpers_before_main(
    tmp_path: Path,
) -> None:
    inventory = _inventory()
    timing = _timing()
    stdout_path = tmp_path / "inventory.frames"
    with stdout_path.open("wb") as stdout:
        completed = subprocess.run(
            [sys.executable, "-I", str(INVENTORY_PATH)],
            cwd=REPO,
            check=False,
            stdout=stdout,
            stderr=subprocess.PIPE,
        )
    assert completed.returncode == 0, completed.stderr.decode()
    core_raw, trailer_raw = timing.decode_two_frames(
        stdout_path.read_bytes(),
        core_max=16 * 1024 * 1024,
        trailer_max=16 * 1024 * 1024,
    )
    inventory.validate_inventory_core(json.loads(core_raw))
    assert json.loads(trailer_raw)["core_sha256"] == timing.sha256_hex(core_raw)



@requires_declared_sdim
def test_fresh_process_computation_never_imports_quimb_gcapeps_or_ecs() -> None:
    code = f"""
import importlib.util
import sys
from pathlib import Path

base = Path({str(BASELINE)!r})
def load(filename, name):
    spec = importlib.util.spec_from_file_location(name, base / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

emitter = load("emit_gcapeps_finite_memory_fixture.py", "_fresh_emitter")
inventory = load(
    "collect_gcapeps_finite_memory_sdim_inventory.py", "_fresh_inventory"
)
worker = load("gcapeps_finite_memory_sdim_worker.py", "_fresh_worker")
fixture = emitter.build_fixture(
    run_partition="HELDOUT",
    width=3,
    rounds=1,
    axis_family=1,
    p_event_numerator=4,
    seed=emitter.HELDOUT_SEED,
    gamma_index=0,
    run_blpensemble=False,
)
inventory_core = inventory.build_inventory_core(
    inventory.collect_inventory_state()
)
core = worker.build_frame_control_core(
    fixture, inventory_core=inventory_core
)
worker.validate_frame_control_core(core)
forbidden = sorted(
    name for name in sys.modules
    if name == "quimb"
    or name.startswith("quimb.")
    or name == "error_coupling_simulator"
    or name.startswith("error_coupling_simulator.")
)
if forbidden:
    raise SystemExit("forbidden imports: " + repr(forbidden))
print("FRESH_PROCESS_FIREWALL_PASS")
"""
    completed = subprocess.run(
        [sys.executable, "-I", "-c", code],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stderr == ""
    assert completed.stdout.strip() == "FRESH_PROCESS_FIREWALL_PASS"
