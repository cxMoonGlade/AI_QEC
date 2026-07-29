from __future__ import annotations

import copy
import gc
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import signal
import struct
import subprocess
import sys
import weakref

import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNNER = (
    ROOT
    / "scripts"
    / "external_baselines"
    / "run_gcapeps_finite_memory_development_sweep.py"
)
PLAN = (
    ROOT
    / "scripts"
    / "external_baselines"
    / "gcapeps_finite_memory_development_sweep.py"
)
FIXTURE = (
    ROOT
    / "scripts"
    / "external_baselines"
    / "emit_gcapeps_finite_memory_fixture.py"
)
FORK_PYTHON = (
    ROOT
    / "external"
    / "forks"
    / "quimb-gcapeps"
    / ".pixi"
    / "envs"
    / "testpymid"
    / "bin"
    / "python"
)
SDIM_PYTHON = Path("/home/cx/miniforge3/envs/gcapeps-sdim/bin/python")


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def runner():
    return _load(RUNNER, "_test_gcapeps_fm_development_runner")


@pytest.fixture(scope="module")
def plan_owner():
    return _load(PLAN, "_test_gcapeps_fm_development_plan_runner")


@pytest.fixture(scope="module")
def fixture_owner():
    return _load(FIXTURE, "_test_gcapeps_fm_development_fixture_runner")


def _run_preflight(interpreter: Path, kind: str) -> dict:
    completed = subprocess.run(
        (str(interpreter), "-I", str(RUNNER), "--preflight", kind),
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60.0,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode(
        "utf-8", errors="replace"
    )
    assert completed.stderr == b""
    return json.loads(completed.stdout.decode("ascii"))


@pytest.fixture(scope="module")
def fork_preflight():
    if not FORK_PYTHON.exists():
        pytest.skip("frozen fork interpreter is unavailable")
    return _run_preflight(FORK_PYTHON, "fork")


@pytest.fixture(scope="module")
def sdim_preflight():
    if not SDIM_PYTHON.exists():
        pytest.skip("frozen SDIM interpreter is unavailable")
    return _run_preflight(SDIM_PYTHON, "sdim")


def test_print_plan_cli_is_executable_and_nonclaim():
    completed = subprocess.run(
        (
            sys.executable,
            "-I",
            str(RUNNER),
            "--gamma-index",
            "0",
            "--rounds-star",
            "6",
            "--print-plan",
        ),
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30.0,
        check=True,
    )
    assert completed.stderr == b""
    value = json.loads(completed.stdout.decode("ascii"))
    assert value["run_partition"] == "DEVELOPMENT_SWEEP"
    assert value["formal_claim_eligible"] is False
    assert value["is_heldout_evidence"] is False
    assert value["transport_equivalent_to_B_CAL_or_B_HELD"] is False
    assert len(value["cells"]) == 12


def test_plan_rebuild_is_deterministic(plan_owner):
    first = plan_owner.build_development_plan(
        gamma_index=3,
        rounds_star=8,
    )
    second = plan_owner.build_development_plan(
        gamma_index=3,
        rounds_star=8,
    )
    assert first == second
    plan_owner.validate_development_plan(first)


def test_fork_and_sdim_preflights_are_executable(
    runner, fork_preflight, sdim_preflight
):
    assert fork_preflight["formal_claim_eligible"] is False
    assert fork_preflight["fork_identity"]["commit"] == runner.FORK_COMMIT
    assert fork_preflight["fork_identity"]["tree"] == runner.FORK_TREE
    assert (
        fork_preflight["fork_identity"]["pixi_lock_sha256"]
        == runner.FORK_PIXI_LOCK_SHA256
    )
    assert fork_preflight["fork_identity"]["tracked_and_untracked_clean"] is True
    origins = {row["name"]: row["origin"] for row in fork_preflight["modules"]}
    checkout = Path(fork_preflight["fork_identity"]["checkout"])
    assert Path(origins["quimb"]).is_relative_to(checkout)
    assert Path(origins["quimb.experimental.gcapeps"]).is_relative_to(checkout)
    assert sdim_preflight["formal_claim_eligible"] is False
    assert {row["name"]: row["version"] for row in sdim_preflight["distributions"]} == {
        "sdim": "1.3.3",
        "stim": "1.16.0",
    }


def test_preflight_exact_keys_reject_claim_lock_and_status_drift(
    runner, fork_preflight
):
    resolved = Path(fork_preflight["python_executable"]).resolve(strict=True)
    runner._validate_preflight_payload(
        fork_preflight,
        kind="fork",
        resolved=resolved,
    )
    extra = copy.deepcopy(fork_preflight)
    extra["formal_result_id"] = "forbidden"
    extra["result_projection_sha256"] = runner._projection(extra)
    with pytest.raises(RuntimeError, match="wrong keys"):
        runner._validate_preflight_payload(extra, kind="fork", resolved=resolved)

    lock_drift = copy.deepcopy(fork_preflight)
    lock_drift["fork_identity"]["pixi_lock_sha256"] = "0" * 64
    lock_drift["result_projection_sha256"] = runner._projection(lock_drift)
    with pytest.raises(RuntimeError, match="repository identity"):
        runner._validate_preflight_payload(
            lock_drift,
            kind="fork",
            resolved=resolved,
        )

    status_drift = copy.deepcopy(fork_preflight)
    status_drift["fork_identity"]["status_porcelain_v1_z_sha256"] = (
        hashlib.sha256(b"?? untracked\x00").hexdigest()
    )
    status_drift["fork_identity"]["tracked_and_untracked_clean"] = False
    status_drift["result_projection_sha256"] = runner._projection(status_drift)
    with pytest.raises(RuntimeError, match="repository identity"):
        runner._validate_preflight_payload(
            status_drift,
            kind="fork",
            resolved=resolved,
        )


def _manifest(runner, *, role: str, parameters: dict, entries: list[dict]):
    return {
        "schema": runner.INPUT_SCHEMA,
        "run_partition": runner.DEVELOPMENT_SWEEP,
        "formal_claim_eligible": False,
        "is_heldout_evidence": False,
        "execution_class": "claim_ineligible_development_diagnostic",
        "heldout_shaped_fixture_reuse_only": True,
        "transport_equivalent_to_B_CAL_or_B_HELD": False,
        "role": role,
        "case_id": (
            None
            if role == runner.SDIM_INVENTORY
            else "development-sweep-c00"
        ),
        "role_parameters": parameters,
        "entries": entries,
    }


def _transport_bytes(runner, manifest: dict, cores: list[bytes]) -> bytes:
    raw = runner._canonical(manifest)
    framed = bytearray(struct.pack(">Q", len(raw)))
    framed.extend(raw)
    for core in cores:
        framed.extend(struct.pack(">Q", len(core)))
        framed.extend(core)
    return bytes(framed)


def test_transport_rejects_extra_claim_field_and_bool_input_id(runner):
    extra = _manifest(
        runner,
        role=runner.SDIM_INVENTORY,
        parameters={},
        entries=[],
    )
    extra["amendment_id"] = "forbidden"
    with pytest.raises(ValueError, match="wrong keys"):
        runner._read_transport(io.BytesIO(_transport_bytes(runner, extra, [])))

    fixture_core = runner._canonical({"schema": runner.FIXTURE_SCHEMA})
    row = {
        "name": "fixture",
        "source_core_schema": runner.FIXTURE_SCHEMA,
        "byte_length": len(fixture_core),
        "sha256": hashlib.sha256(fixture_core).hexdigest(),
    }
    bool_id = _manifest(
        runner,
        role=runner.PLAIN_EVIDENCE,
        parameters={"input_id": True},
        entries=[row],
    )
    with pytest.raises(ValueError, match="plain integer"):
        runner._read_transport(
            io.BytesIO(_transport_bytes(runner, bool_id, [fixture_core]))
        )


def test_binary_artifact_roundtrip_and_component_timing(runner, tmp_path):
    core = {
        "schema": "development-test-core.v1",
        "payload": [1, 2, 3],
        "result_projection_sha256": "",
    }
    core["result_projection_sha256"] = runner._projection(core)
    core_bytes = runner._canonical(core)
    trailer = {
        "timing": {
            "spans": [
                {
                    "parent_span_id": None,
                    "scope": "dense_reference_worker_total",
                    "wall_duration_ns": 123,
                    "cpu_duration_ns": 45,
                }
            ]
        }
    }
    trailer_bytes = runner._canonical(trailer)
    header = runner._artifact_header(
        schema=runner.CHILD_SCHEMA,
        role=runner.DENSE_REFERENCE,
        case_id="development-sweep-c00",
        role_parameters={},
        source_core_schema=core["schema"],
        source_core_projection_sha256=core["result_projection_sha256"],
        core_bytes=core_bytes,
        trailer_bytes=trailer_bytes,
        process_receipt={
            "launch_id": "dev-c00-dense",
            "development_process_wall_ns": 150,
        },
    )
    identity = runner._publish_binary_artifact(
        tmp_path / "dense.devbin",
        header=header,
        core_bytes=core_bytes,
        trailer_bytes=trailer_bytes,
    )
    observed_raw, observed_core = runner._read_artifact_core(identity)
    assert observed_raw == core_bytes
    assert observed_core == core
    assert identity.header["formal_claim_eligible"] is False
    assert identity.header["is_heldout_evidence"] is False
    assert identity.header["source_core_projection_sha256"] == runner._projection(
        observed_core
    )
    timing = runner._component_timings({"dense": identity})
    assert timing == [
        {
            "artifact_key": "dense",
            "role": runner.DENSE_REFERENCE,
            "role_parameters": {},
            "launch_id": "dev-c00-dense",
            "development_process_wall_ns": 150,
            "worker_root_scope": "dense_reference_worker_total",
            "worker_root_wall_ns": 123,
            "worker_root_cpu_ns": 45,
            "timing_artifact": identity.binding(),
        }
    ]


def test_fixture_wrapper_recomputes_projection_before_publication(runner, tmp_path):
    with pytest.raises(ValueError, match="projection identity"):
        runner._publish_fixture(
            path=tmp_path / "bad-fixture.devbin",
            fixture={"result_projection_sha256": "0" * 64},
            development_case_id="development-sweep-c00",
            parent_source_projection_sha256="1" * 64,
        )
    assert not (tmp_path / "bad-fixture.devbin").exists()


def test_scientific_child_command_is_isolated(runner):
    command = runner._scientific_child_command(
        Path("/opt/frozen/python"),
        runner.PLAIN_PERFORMANCE,
    )
    assert command == (
        "/opt/frozen/python",
        "-I",
        str(RUNNER.resolve(strict=True)),
        "--child",
        runner.PLAIN_PERFORMANCE,
    )


@pytest.mark.skipif(os.name != "posix", reason="process groups require POSIX")
def test_process_group_cleanup_kills_descendant_after_leader_exit(runner):
    program = (
        "import subprocess,sys;"
        "subprocess.Popen((sys.executable,'-I','-c',"
        "'import time;time.sleep(30)'))"
    )
    process = subprocess.Popen(
        (sys.executable, "-I", "-c", program),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )
    try:
        assert process.wait(timeout=5.0) == 0
        assert runner._process_group_exists(process.pid)
        runner._cleanup_process_group(process)
        assert runner._process_group_exists(process.pid) is False
    finally:
        if runner._process_group_exists(process.pid):
            os.killpg(process.pid, signal.SIGKILL)


def _git(repository: Path, *arguments: str) -> None:
    subprocess.run(
        ("git", "-C", str(repository), *arguments),
        check=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30.0,
    )


def test_parent_source_identity_refuses_untracked_and_records_limitations(
    runner, tmp_path
):
    repository = tmp_path / "repository"
    repository.mkdir()
    _git(repository, "init", "-q")
    _git(repository, "config", "user.email", "test@example.invalid")
    _git(repository, "config", "user.name", "Development Sweep Test")
    source = repository / "runner.py"
    source.write_text("print('bound')\n", encoding="utf-8")
    _git(repository, "add", "runner.py")
    _git(repository, "commit", "-q", "-m", "fixture")
    identity = runner._collect_repository_source_identity(
        repository=repository,
        source_relative_paths=("runner.py",),
    )
    assert identity["tracked_and_untracked_clean"] is True
    assert identity["status_porcelain_v1_z_sha256"] == hashlib.sha256(
        b""
    ).hexdigest()
    assert identity["source_files"][0]["byte_length"] == source.stat().st_size
    provenance = runner._development_report_provenance(identity)
    assert provenance["parent_source_identity"] == identity
    assert provenance["cpu_affinity_frozen"] is False
    assert provenance["scheduler_migration_controlled"] is False
    assert provenance["timing_portability"] == (
        "descriptive_development_only_not_a_portable_benchmark"
    )

    source.write_text("print('tracked drift')\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="tracked or untracked"):
        runner._collect_repository_source_identity(
            repository=repository,
            source_relative_paths=("runner.py",),
        )
    source.write_text("print('bound')\n", encoding="utf-8")
    (repository / "untracked.txt").write_text("drift\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="tracked or untracked"):
        runner._collect_repository_source_identity(
            repository=repository,
            source_relative_paths=("runner.py",),
        )


@pytest.mark.parametrize(
    ("drift_target", "message"),
    (
        ("parent", "parent source identity changed"),
        ("fork", "fork interpreter identity changed"),
        ("sdim", "SDIM interpreter identity changed"),
    ),
)
def test_post_run_identity_recheck_refuses_persistent_drift(
    runner, monkeypatch, drift_target, message
):
    initial_parent = {"identity": "parent-initial"}
    initial_fork = {"identity": "fork-initial"}
    initial_sdim = {"identity": "sdim-initial"}
    observed_parent = (
        {"identity": "parent-drifted"}
        if drift_target == "parent"
        else initial_parent
    )
    observed = {
        "fork": (
            {"identity": "fork-drifted"}
            if drift_target == "fork"
            else initial_fork
        ),
        "sdim": (
            {"identity": "sdim-drifted"}
            if drift_target == "sdim"
            else initial_sdim
        ),
    }
    monkeypatch.setattr(
        runner,
        "_authenticate_parent_repository",
        lambda: observed_parent,
    )
    monkeypatch.setattr(
        runner,
        "_authenticate_interpreter",
        lambda path, *, kind: observed[kind],
    )
    with pytest.raises(RuntimeError, match=message):
        runner._recheck_execution_identities(
            parent_source_identity=initial_parent,
            fork_identity=initial_fork,
            sdim_identity=initial_sdim,
            fork_python=Path("/unused/fork-python"),
            sdim_python=Path("/unused/sdim-python"),
        )


def test_output_root_allows_gitignored_repo_path_and_rejects_other(
    runner, tmp_path
):
    repository = tmp_path / "repository"
    repository.mkdir()
    _git(repository, "init", "-q")
    _git(repository, "config", "user.email", "test@example.invalid")
    _git(repository, "config", "user.name", "Development Sweep Test")
    (repository / ".gitignore").write_text("outputs/\n", encoding="utf-8")
    _git(repository, "add", ".gitignore")
    _git(repository, "commit", "-q", "-m", "ignore outputs")
    ignored = repository / "outputs" / "development-run"
    assert (
        runner._resolve_development_output_root(
            ignored,
            repository=repository,
        )
        == ignored
    )
    with pytest.raises(ValueError, match="must be gitignored"):
        runner._resolve_development_output_root(
            repository / "not-ignored" / "development-run",
            repository=repository,
        )
    outside = tmp_path / "outside-development-run"
    assert (
        runner._resolve_development_output_root(
            outside,
            repository=repository,
        )
        == outside
    )


def test_case_timing_scopes_include_fixture_and_enforce_order(runner):
    scopes = runner._case_timing_scopes(
        workflow_wall_ns=100,
        with_fixture_wall_ns=150,
    )
    assert scopes["development_case_workflow_wall_ns"] == 100
    assert scopes["development_case_with_fixture_wall_ns"] == 150
    assert (
        scopes["development_case_with_fixture_wall_ns"]
        >= scopes["development_case_workflow_wall_ns"]
    )
    assert "lazy_fixture_construction" in scopes[
        "development_case_timing_scope"
    ]["with_fixture_includes"]
    assert "case_summary_encoding" in scopes[
        "development_case_timing_scope"
    ]["both_exclude"]
    with pytest.raises(ValueError, match="outside its allowed range"):
        runner._case_timing_scopes(
            workflow_wall_ns=100,
            with_fixture_wall_ns=99,
        )


def test_parent_and_interpreter_auth_fail_before_output_root(
    runner, tmp_path, monkeypatch
):
    source_identity = {
        "result_projection_sha256": "2" * 64,
    }
    monkeypatch.setattr(
        runner,
        "_authenticate_parent_repository",
        lambda: source_identity,
    )

    def reject_interpreter(path, *, kind):
        raise RuntimeError(f"{kind} rejected")

    monkeypatch.setattr(runner, "_authenticate_interpreter", reject_interpreter)
    output_root = tmp_path / "must-not-exist"
    with pytest.raises(RuntimeError, match="fork rejected"):
        runner.run_sweep(
            output_root=output_root,
            gamma_index=0,
            rounds_star=4,
            fork_python=Path(sys.executable),
            sdim_python=Path(sys.executable),
            timeout_seconds=1.0,
            cell_limit=1,
        )
    assert not output_root.exists()


@pytest.mark.parametrize(("rounds_star", "expected_count"), ((4, 11), (6, 12)))
def test_full_grid_serial_execution_bounds_parsed_payload_to_one_cell(
    runner,
    plan_owner,
    fixture_owner,
    rounds_star,
    expected_count,
):
    plan = plan_owner.build_development_plan(
        gamma_index=0,
        rounds_star=rounds_star,
    )
    fixture_cells = fixture_owner.build_heldout_cells(rounds_star)
    tracker = {
        "live": 0,
        "live_bytes": 0,
        "maximum_live": 0,
        "maximum_live_bytes": 0,
        "builds": 0,
    }
    payload_size = 1_000_000

    class Payload(dict):
        pass

    class FakeFixtureOwner:
        HELDOUT_SEED = fixture_owner.HELDOUT_SEED

        @staticmethod
        def build_fixture(
            *,
            run_partition,
            width,
            rounds,
            axis_family,
            p_event_numerator,
            seed,
            gamma_index,
            run_blpensemble,
        ):
            assert run_partition == "HELDOUT"
            assert seed == fixture_owner.HELDOUT_SEED
            assert gamma_index == 0
            tracker["live"] += 1
            tracker["live_bytes"] += payload_size
            tracker["maximum_live"] = max(
                tracker["maximum_live"], tracker["live"]
            )
            tracker["maximum_live_bytes"] = max(
                tracker["maximum_live_bytes"], tracker["live_bytes"]
            )
            tracker["builds"] += 1
            payload = Payload(
                {
                    "case_id": (
                        f"heldout-w{width}-r{rounds}-a{axis_family}-"
                        f"p{p_event_numerator}of4"
                    ),
                    "result_projection_sha256": "3" * 64,
                    "parsed_payload": bytearray(payload_size),
                    "run_blpensemble": run_blpensemble,
                }
            )

            def release():
                tracker["live"] -= 1
                tracker["live_bytes"] -= payload_size

            weakref.finalize(payload, release)
            return payload

        @staticmethod
        def validate_fixture(fixture):
            return fixture["result_projection_sha256"]

    def execute_one(cell):
        fixture = runner._build_single_development_fixture(
            fixture_owner=FakeFixtureOwner,
            fixture_cell=fixture_cells[cell["cell_index"]],
            development_cell=cell,
            gamma_index=0,
        )
        assert tracker["live"] == 1
        assert tracker["live_bytes"] == payload_size
        summary = {
            "cell_index": cell["cell_index"],
            "run_partition": "DEVELOPMENT_SWEEP",
            "formal_claim_eligible": False,
            "is_heldout_evidence": False,
        }
        del fixture
        gc.collect()
        assert tracker["live"] == 0
        assert tracker["live_bytes"] == 0
        return summary

    summaries = runner.execute_cells_serially(plan["cells"], execute_one)
    assert len(summaries) == expected_count
    assert tracker == {
        "live": 0,
        "live_bytes": 0,
        "maximum_live": 1,
        "maximum_live_bytes": payload_size,
        "builds": expected_count,
    }
    assert all(
        not isinstance(value, (bytes, bytearray, memoryview))
        for summary in summaries
        for value in runner._walk(summary)
    )


def test_serial_executor_rejects_raw_payload_in_summary(runner):
    with pytest.raises(ValueError, match="retained raw payload bytes"):
        runner.execute_cells_serially(
            [{"cell_index": 0}],
            lambda cell: {"cell_index": cell["cell_index"], "raw": b"bad"},
        )


def test_only_authoritative_timing_validator_is_exposed(runner, plan_owner):
    assert not hasattr(plan_owner, "measured_timing_row")
    assert not hasattr(plan_owner, "aggregate_measured_timing")
    names = set(runner._case_summary.__code__.co_names)
    assert "measured_timing_sample_from_trailer" in names
    assert "aggregate_primary_timing" in names
