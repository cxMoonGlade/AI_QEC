"""Isolated SDIM controls for the frozen GCAPEPS d=3/5/7 fixtures."""

from __future__ import annotations

import ast
import copy
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import sys

import pytest


REPO = Path(__file__).resolve().parents[1]
BASELINE = REPO / "scripts" / "external_baselines"
WORKER_PATH = BASELINE / "gcapeps_d357_sdim_worker.py"
EMITTER_PATH = (
    BASELINE / "emit_gcapeps_d357_unitary_prefix_fixture.py"
)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _worker():
    return _load(WORKER_PATH, "gcapeps_d357_sdim_worker_under_test")


def _emitter():
    return _load(
        EMITTER_PATH,
        "emit_gcapeps_d357_fixture_for_sdim_test",
    )


def _has_sdim_133() -> bool:
    try:
        return importlib.metadata.version("sdim") == "1.3.3"
    except importlib.metadata.PackageNotFoundError:
        return False


requires_sdim = pytest.mark.skipif(
    not _has_sdim_133(),
    reason="isolated SDIM control requires sdim 1.3.3",
)


def _fixture_path(tmp_path: Path, distance: int) -> Path:
    stim = pytest.importorskip("stim")
    emitter = _emitter()
    _circuit, fixture = emitter.emit_fixture(stim, distance=distance)
    path = tmp_path / f"d{distance}.json"
    path.write_bytes(emitter.canonical_json_bytes(fixture))
    return path


def test_worker_source_imports_neither_quimb_nor_gcapeps_or_timing() -> None:
    tree = ast.parse(WORKER_PATH.read_text(encoding="utf-8"))
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
    assert not any(name == "quimb" or name.startswith("quimb.") for name in imported)
    assert not any("gcapeps" in name.lower() for name in imported)
    assert not any(name == "time" or name.startswith("time.") for name in imported)


@requires_sdim
@pytest.mark.parametrize("distance", [3, 5, 7])
def test_sdim_replays_every_accumulated_layer_and_error_location(
    tmp_path: Path,
    distance: int,
) -> None:
    worker = _worker()
    fixture_path = _fixture_path(tmp_path, distance)
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))

    report = worker.build_report(fixture_json=fixture_path)
    worker.validate_report(report)

    assert report["schema"] == worker.WORKER_SCHEMA
    assert report["fixture_identity"]["distance"] == distance
    assert report["fixture_identity"]["n_qubits"] == 2 * distance**2 - 1
    assert report["runtime_identity"]["sdim_version"] == "1.3.3"
    replay = report["prefix_replay"]
    assert replay["gate_subset"] == ["H", "CX"]
    assert replay["inverse_replay_order"] is True
    assert replay["accumulated_layer_count"] == distance
    assert replay["error_location_count"] == 4
    assert replay["checked_row_count"] == 4 * distance

    schedule = report["accumulated_frame_schedule"]
    assert schedule["row_count"] == 4 * distance
    assert schedule["expected_rows"] == fixture[
        "accumulated_frame_schedule"
    ]["rows"]
    assert schedule["observed_rows"] == schedule["expected_rows"]
    assert schedule["expected_schedule_sha256"] == fixture[
        "accumulated_frame_schedule"
    ]["schedule_sha256"]
    assert schedule["observed_schedule_sha256"] == schedule[
        "expected_schedule_sha256"
    ]
    assert schedule["exact_match"] is True
    for index, row in enumerate(schedule["observed_rows"]):
        assert row["layer"] == index // 4 + 1
        assert row["location_rank"] == index % 4 + 1
        assert row["target"] == fixture["error_locations"][
            index % 4
        ]["target"]
        assert row["support"] == worker._support(
            row["signed_pullback"],
            width=fixture["n_qubits"],
        )
    assert report["scope"] == {
        "dimension": 2,
        "qubit_only": True,
        "untimed": True,
        "imports_quimb": False,
        "imports_gcapeps": False,
        "receives_peps": False,
        "emits_peps": False,
        "receives_state_vector": False,
        "emits_state_vector": False,
        "enters_performance_ratio": False,
        "ground_truth": False,
        "qutrit_evidence": False,
    }
    assert report["sdim_control_verdict"] == "PASS"


@requires_sdim
def test_wrong_sdim_sign_fails_before_report_or_publication(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    worker = _worker()
    fixture_path = _fixture_path(tmp_path, 3)
    output = tmp_path / "must-not-exist.json"
    original = worker._signed_y_output
    calls = 0

    def wrong_layer_two_sign(*args, **kwargs):
        nonlocal calls
        observed = original(*args, **kwargs)
        calls += 1
        if calls == 5:
            return ("-" if observed[0] == "+" else "+") + observed[1:]
        return observed

    monkeypatch.setattr(worker, "_signed_y_output", wrong_layer_two_sign)
    with pytest.raises(
        RuntimeError,
        match="layer 2, location 1",
    ):
        report = worker.build_report(fixture_json=fixture_path)
        worker.write_report_no_replace(output, report)
    assert not output.exists()


@requires_sdim
def test_schedule_target_order_and_support_mutations_fail_closed(
    tmp_path: Path,
) -> None:
    del tmp_path
    worker = _worker()
    emitter = _emitter()
    stim = pytest.importorskip("stim")
    _circuit, fixture = emitter.emit_fixture(stim, distance=3)
    sdim_module = worker._load_sdim()

    wrong_target = copy.deepcopy(fixture)
    wrong_target["accumulated_frame_schedule"]["rows"][0]["target"] = (
        fixture["error_locations"][1]["target"]
    )
    wrong_target["accumulated_frame_schedule"]["schedule_sha256"] = (
        emitter.canonical_json_sha256(
            wrong_target["accumulated_frame_schedule"]["rows"]
        )
    )
    with pytest.raises(ValueError, match="order or target"):
        worker._replay_accumulated_schedule(
            wrong_target,
            sdim_module=sdim_module,
            fixture_contract=emitter,
        )

    wrong_order = copy.deepcopy(fixture)
    rows = wrong_order["accumulated_frame_schedule"]["rows"]
    rows[0], rows[1] = rows[1], rows[0]
    wrong_order["accumulated_frame_schedule"]["schedule_sha256"] = (
        emitter.canonical_json_sha256(rows)
    )
    with pytest.raises(ValueError, match="order or target"):
        worker._replay_accumulated_schedule(
            wrong_order,
            sdim_module=sdim_module,
            fixture_contract=emitter,
        )

    wrong_support = copy.deepcopy(fixture)
    wrong_support["accumulated_frame_schedule"]["rows"][0][
        "support"
    ] = []
    wrong_support["accumulated_frame_schedule"]["schedule_sha256"] = (
        emitter.canonical_json_sha256(
            wrong_support["accumulated_frame_schedule"]["rows"]
        )
    )
    with pytest.raises(ValueError, match="support drifted"):
        worker._replay_accumulated_schedule(
            wrong_support,
            sdim_module=sdim_module,
            fixture_contract=emitter,
        )


@requires_sdim
def test_cli_atomically_writes_canonical_json_without_replace(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    worker = _worker()
    fixture = _fixture_path(tmp_path, 3)
    output = tmp_path / "sdim-control.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(WORKER_PATH),
            "--fixture",
            str(fixture),
            "--output",
            str(output),
        ],
    )

    assert worker.main() == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert output.read_bytes() == worker.canonical_json_bytes(report)
    worker.validate_report(report)
    original = output.read_bytes()

    with pytest.raises(FileExistsError, match="refusing to replace"):
        worker.main()
    assert output.read_bytes() == original


@requires_sdim
def test_report_self_hash_and_exact_schema_fail_closed(tmp_path: Path) -> None:
    worker = _worker()
    report = worker.build_report(
        fixture_json=_fixture_path(tmp_path, 3),
    )

    bad_hash = copy.deepcopy(report)
    bad_hash["content_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="self-hash"):
        worker.validate_report(bad_hash)

    extra = copy.deepcopy(report)
    extra["timing_ns"] = 0
    extra["content_sha256"] = worker.canonical_content_sha256(extra)
    with pytest.raises(ValueError, match="keys drifted"):
        worker.validate_report(extra)


def test_fixture_loader_rejects_noncanonical_and_duplicate_json(
    tmp_path: Path,
) -> None:
    worker = _worker()

    noncanonical = tmp_path / "noncanonical.json"
    noncanonical.write_text('{"schema": "x"}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="byte-canonical"):
        worker.load_fixture(noncanonical)

    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"distance":3,"distance":5}', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate JSON key"):
        worker.load_fixture(duplicate)
