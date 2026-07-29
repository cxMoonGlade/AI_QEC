from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import math
from pathlib import Path
import signal
from types import SimpleNamespace
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = (
    ROOT
    / "scripts"
    / "external_baselines"
    / "run_gcapeps_finite_memory_experiment.py"
)
RUNNER_PATH = (
    ROOT
    / "scripts"
    / "external_baselines"
    / "run_gcapeps_finite_memory_bond32.py"
)
ORCHESTRATION_PATH = (
    ROOT
    / "scripts"
    / "external_baselines"
    / "gcapeps_finite_memory_orchestration.py"
)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def adapter():
    return _load(ADAPTER_PATH, "gcapeps_finite_memory_experiment_adapter_tests")


@pytest.fixture(scope="module")
def authenticated_interpreters(adapter):
    return adapter.authenticate_direct_interpreters(
        fork_python=adapter._DEFAULT_FORK_PYTHON,
        sdim_python=adapter._DEFAULT_SDIM_PYTHON,
    )


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("ascii")).hexdigest()


def _mock_parent_source_identity(adapter):
    return {
        "checkout_realpath": str(adapter._REPOSITORY.resolve(strict=True)),
        "commit": "1" * 40,
        "tree": "2" * 40,
        "tracked_and_untracked_clean": True,
        "status_porcelain_v1_z_sha256": hashlib.sha256(b"").hexdigest(),
        "source_files": {
            name: adapter._source_file_identity(path)
            for name, path in sorted(
                adapter._DEVELOPMENT_SOURCE_PATHS.items()
            )
        },
    }


def _runner_tokens():
    return SimpleNamespace(
        BOOTSTRAP="BOOTSTRAP",
        CALIBRATION="CALIBRATION",
        NEUTRAL_FIXTURE_EMITTER="neutral_fixture_emitter",
        SDIM_INVENTORY_COLLECTOR="sdim_inventory_collector",
        DENSE_REFERENCE="dense_reference",
        PLAIN_CAP_PROBE="plain_cap_probe",
        GCAPEPS_CAP_PROBE="gcapeps_cap_probe",
        PLAIN_EVIDENCE="plain_evidence",
        GCAPEPS_EVIDENCE="gcapeps_evidence",
        PLAIN_PERFORMANCE="plain_performance",
        GCAPEPS_PERFORMANCE="gcapeps_performance",
        SDIM_COMPUTATION="sdim_computation",
        TERMINAL_COMPARATOR="terminal_comparator",
    )


def _spec(role: str, *, launch_id="launch", dependencies=(), input_id=None):
    parameters = {} if input_id is None else {"input_id": input_id}
    return SimpleNamespace(
        launch_id=launch_id,
        run_partition="CALIBRATION",
        role=role,
        dependency_launch_ids=tuple(dependencies),
        parameter_map=lambda: dict(parameters),
    )


def _product(adapter, role: str, launch_id: str, *, input_id=None):
    return adapter.DirectProduct(
        launch_id=launch_id,
        role=role,
        terminal_kind="completed_result",
        core={"schema": "test"},
        core_bytes=b"{}",
        trailer_bytes=b"trailer",
        stdout_identity={
            "path": launch_id,
            "byte_length": 0,
            "sha256": _digest(launch_id),
        },
        stderr_identity={
            "path": launch_id + "-err",
            "byte_length": 0,
            "sha256": _digest(launch_id + "-err"),
        },
        process_receipt={
            "role_parameters": (
                {} if input_id is None else {"input_id": input_id}
            ),
            "core_identity": {
                "path": launch_id + "-core",
                "byte_length": 2,
                "sha256": _digest(launch_id + "-core"),
            },
        },
        process_receipt_identity=SimpleNamespace(
            sha256=_digest(launch_id + "-receipt"),
            as_dict=lambda: {
                "path": launch_id + "-receipt",
                "byte_length": 0,
                "sha256": _digest(launch_id + "-receipt"),
            },
        ),
    )


def _dense_core(distances=(0.2, 0.3)):
    increments = [
        float(distances[index] - distances[index - 1])
        for index in range(1, len(distances))
    ]
    maximum = max(increments)
    return {
        "fixed_blp": {
            "object": "fixed_carrier_mask",
            "trace_distances": list(distances),
            "increments": increments,
            "summed_positive_increments": float(
                math.fsum(max(0.0, value) for value in increments)
            ),
            "maximum_increment": maximum,
            "witness_threshold": 1.0e-10,
            "verdict": (
                "BLP_WITNESSED_FIXED_MASK"
                if maximum > 1.0e-10
                else "NO_WITNESS_FIXED_MASK_FOR_REGISTERED_PAIR"
            ),
        }
    }


def _comparator_core():
    return {
        "positive_bond32_gate": {
            "definition": {
                "configured_max_bond": 32,
                "minimum_full_bond_dimension": 33,
                "kept_bond_dimension": 32,
                "discarded_squared_weight_strictly_greater_than": 1.0e-12,
                "cause": "max_bond",
            },
            "paths": [
                {
                    "lane": lane,
                    "input_id": input_id,
                    "positive_bond32_event": True,
                    "positive_event_count": 1,
                    "qualifying_event_locators": [{"round": 1}],
                }
                for lane in ("plain", "gcapeps")
                for input_id in (1, 2)
            ],
            "all_four_paths_positive": True,
        }
    }


def test_import_firewall_and_retired_stage_literal_are_clean():
    source = ADAPTER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        node.names[0].name.split(".")[0]
        for node in tree.body
        if isinstance(node, ast.Import)
    }
    imports.update(
        node.module.split(".")[0]
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module is not None
    )
    assert imports.isdisjoint({"numpy", "quimb", "stim", "sdim"})
    retired_label = "".join(("Stage", chr(45), "D"))
    assert retired_label not in source
    orchestration_source = ORCHESTRATION_PATH.read_text(encoding="utf-8")
    assert retired_label not in orchestration_source


def test_cli_formal_modes_fail_closed_and_development_options_parse(
    adapter,
    monkeypatch,
):
    args = adapter._parse_args(
        [
            "--development-direct",
            "--fork-python-executable",
            sys.executable,
            "--sdim-python-executable",
            sys.executable,
        ]
    )
    assert args.development_direct is True
    assert args.fork_python_executable == Path(sys.executable)
    assert args.sdim_python_executable == Path(sys.executable)
    monkeypatch.setattr(adapter, "initialize_runtime", lambda: object())
    with pytest.raises(RuntimeError, match="fail-closed"):
        adapter.main(["--formal-calibrate"])
    with pytest.raises(RuntimeError, match="fail-closed"):
        adapter.main(["--formal-heldout"])


def test_default_fork_interpreter_has_authenticated_repo_origins(
    adapter,
    authenticated_interpreters,
    tmp_path,
):
    default_args = adapter._parse_args(["--development-direct"])
    assert default_args.fork_python_executable == adapter._DEFAULT_FORK_PYTHON
    authentication = authenticated_interpreters.fork_identity[
        "module_origin_authentication"
    ]
    expected_origins = {
        name: str(path.resolve(strict=True))
        for name, path in adapter._EXPECTED_FORK_MODULE_ORIGINS.items()
    }
    assert authentication["isolated_python_mode"] is True
    assert authentication["module_origins"] == expected_origins
    checkout = authenticated_interpreters.fork_identity[
        "fork_checkout_authentication"
    ]
    assert checkout == {
        "checkout_realpath": str(adapter._FORK_ROOT.resolve(strict=True)),
        "commit": adapter._EXPECTED_FORK_COMMIT,
        "tree": adapter._EXPECTED_FORK_TREE,
        "tracked_and_untracked_clean": True,
        "status_porcelain_v1_z_sha256": hashlib.sha256(b"").hexdigest(),
        "pixi_lock_realpath": str(
            adapter._FORK_PIXI_LOCK.resolve(strict=True)
        ),
        "pixi_lock_sha256": adapter._EXPECTED_FORK_PIXI_LOCK_SHA256,
    }
    sdim_authentication = authenticated_interpreters.sdim_identity[
        "module_origin_authentication"
    ]
    assert sdim_authentication["isolated_python_mode"] is True
    assert set(sdim_authentication["module_origins"]) == {"sdim", "stim"}
    for origin in sdim_authentication["module_origins"].values():
        assert Path(origin).resolve(strict=True).is_file()

    tampered_identity = dict(authenticated_interpreters.fork_identity)
    tampered_authentication = copy.deepcopy(authentication)
    tampered_authentication["module_origins"]["quimb"] = "/tmp/not-quimb"
    tampered_identity["module_origin_authentication"] = tampered_authentication
    tampered = adapter.DirectInterpreters(
        fork_python=authenticated_interpreters.fork_python,
        fork_identity=tampered_identity,
        sdim_python=authenticated_interpreters.sdim_python,
        sdim_identity=authenticated_interpreters.sdim_identity,
    )
    output_root = tmp_path / "must-not-exist"
    with pytest.raises(ValueError, match="module-origin"):
        adapter.run_development_direct(
            runtime=SimpleNamespace(runner=None, orchestration=None),
            output_root=output_root,
            interpreters=tampered,
            timeout_seconds=1.0,
        )
    assert not output_root.exists()


def test_development_root_is_not_created_when_fork_checkout_recheck_drifts(
    adapter,
    authenticated_interpreters,
    monkeypatch,
    tmp_path,
):
    live = copy.deepcopy(
        authenticated_interpreters.fork_identity[
            "fork_checkout_authentication"
        ]
    )
    live["tree"] = "0" * 40
    monkeypatch.setattr(adapter, "_authenticate_fork_checkout", lambda: live)
    output_root = tmp_path / "must-not-exist"
    with pytest.raises(ValueError, match="fork checkout authentication drifted"):
        adapter.run_development_direct(
            runtime=SimpleNamespace(runner=None, orchestration=None),
            output_root=output_root,
            interpreters=authenticated_interpreters,
            timeout_seconds=1.0,
        )
    assert not output_root.exists()


def test_fork_checkout_authentication_rejects_untracked_source_drift(
    adapter,
    monkeypatch,
):
    git_stdout = adapter._git_stdout

    def with_untracked_source(checkout, *arguments):
        if arguments and arguments[0] == "status":
            return b"?? rogue_source.py\0"
        return git_stdout(checkout, *arguments)

    monkeypatch.setattr(adapter, "_git_stdout", with_untracked_source)
    with pytest.raises(RuntimeError, match="tracked or untracked source drift"):
        adapter._authenticate_fork_checkout()


def test_fork_checkout_authentication_rejects_lock_hash_drift(adapter, monkeypatch):
    monkeypatch.setattr(
        adapter,
        "_EXPECTED_FORK_PIXI_LOCK_SHA256",
        "0" * 64,
    )
    with pytest.raises(RuntimeError, match="fork pixi lock drifted"):
        adapter._authenticate_fork_checkout()


def test_untracked_parent_source_refuses_before_development_root_creation(
    adapter,
    authenticated_interpreters,
    monkeypatch,
    tmp_path,
):
    git_stdout = adapter._git_stdout
    parent = adapter._REPOSITORY.resolve(strict=True)

    def with_untracked_parent(checkout, *arguments):
        if (
            checkout.resolve(strict=True) == parent
            and arguments
            and arguments[0] == "status"
        ):
            return b"?? uncommitted_science.py\0"
        return git_stdout(checkout, *arguments)

    monkeypatch.setattr(adapter, "_git_stdout", with_untracked_parent)
    output_root = tmp_path / "must-not-exist"
    with pytest.raises(
        RuntimeError,
        match="parent repository has tracked or untracked source drift",
    ):
        adapter.run_development_direct(
            runtime=SimpleNamespace(runner=None, orchestration=None),
            output_root=output_root,
            interpreters=authenticated_interpreters,
            timeout_seconds=1.0,
        )
    assert not output_root.exists()


def test_persistent_parent_drift_blocks_report_after_worker_cleanup(
    adapter,
    authenticated_interpreters,
    monkeypatch,
    tmp_path,
):
    source_identity = _mock_parent_source_identity(adapter)
    drifted_identity = copy.deepcopy(source_identity)
    drifted_identity["tree"] = "3" * 40
    observations = iter(
        (source_identity, source_identity, drifted_identity)
    )
    monkeypatch.setattr(
        adapter,
        "_authenticate_parent_repository",
        lambda: next(observations),
    )
    runner = _runner_tokens()
    runtime = adapter.RuntimeModules(
        runner=runner,
        orchestration=None,
        runner_identity={},
    )

    def failed_inventory(**kwargs):
        product = _product(
            adapter,
            runner.SDIM_INVENTORY_COLLECTOR,
            kwargs["spec"].launch_id,
        )
        return adapter.DirectProduct(
            **{
                **product.__dict__,
                "terminal_kind": "invalid_control",
            }
        )

    output_root = tmp_path / "development"
    with pytest.raises(
        ValueError,
        match="parent repository source changed during development run",
    ):
        adapter.run_development_direct(
            runtime=runtime,
            output_root=output_root,
            interpreters=authenticated_interpreters,
            timeout_seconds=1.0,
            launch_direct=failed_inventory,
        )
    assert output_root.is_dir()
    assert not (output_root / "development_direct_report.json").exists()


def test_persistent_interpreter_drift_fails_canonical_final_recheck(
    adapter,
    authenticated_interpreters,
    monkeypatch,
):
    source_identity = _mock_parent_source_identity(adapter)
    monkeypatch.setattr(
        adapter, "_authenticate_parent_repository", lambda: source_identity
    )
    drifted = copy.deepcopy(authenticated_interpreters.fork_identity)
    drifted["sha256"] = "4" * 64
    monkeypatch.setattr(
        adapter,
        "authenticate_direct_interpreters",
        lambda **kwargs: adapter.DirectInterpreters(
            fork_python=authenticated_interpreters.fork_python,
            fork_identity=drifted,
            sdim_python=authenticated_interpreters.sdim_python,
            sdim_identity=authenticated_interpreters.sdim_identity,
        ),
    )
    bound = adapter._bind_development_source_identity(
        authenticated_interpreters,
        source_identity,
    )
    with pytest.raises(ValueError, match="interpreter or source identity changed"):
        adapter._recheck_development_execution_identity(
            interpreters=bound,
            source_identity=source_identity,
        )


def test_module_origin_probe_rejects_missing_and_wrong_origins(
    adapter,
    monkeypatch,
):
    class Completed:
        returncode = 0
        stderr = b""

        def __init__(self, stdout):
            self.stdout = stdout

    missing = b'{"quimb":"/tmp/quimb.py"}\n'
    monkeypatch.setattr(adapter.subprocess, "run", lambda *args, **kwargs: Completed(missing))
    with pytest.raises(ValueError, match="wrong keys"):
        adapter._authenticate_fork_module_origins(Path("/python"))

    wrong = adapter.json.dumps(
        {name: str(ADAPTER_PATH) for name in adapter._EXPECTED_FORK_MODULE_ORIGINS}
    ).encode("ascii")
    monkeypatch.setattr(adapter.subprocess, "run", lambda *args, **kwargs: Completed(wrong))
    with pytest.raises(ValueError, match="unauthenticated origin"):
        adapter._authenticate_fork_module_origins(Path("/python"))
    sdim_missing = b'{"sdim":"/tmp/sdim.py"}\n'
    monkeypatch.setattr(adapter.subprocess, "run", lambda *args, **kwargs: Completed(sdim_missing))
    with pytest.raises(ValueError, match="wrong keys"):
        adapter._authenticate_sdim_module_origins(Path("/python"))



def test_interpreter_split_routes_only_sdim_roles_to_isolated_python(adapter):
    runner = _runner_tokens()
    interpreters = adapter.DirectInterpreters(
        fork_python=Path("/fork/python"),
        fork_identity={"kind": "fork"},
        sdim_python=Path("/sdim/python"),
        sdim_identity={"kind": "sdim"},
    )
    for role in (runner.SDIM_INVENTORY_COLLECTOR, runner.SDIM_COMPUTATION):
        assert interpreters.select(runner, role)[1] == {"kind": "sdim"}
    other_roles = (
        runner.DENSE_REFERENCE,
        runner.PLAIN_EVIDENCE,
        runner.TERMINAL_COMPARATOR,
    )
    for role in other_roles:
        assert interpreters.select(runner, role)[1] == {"kind": "fork"}


def test_exact_dependency_roles_order_and_cardinality(adapter):
    runner = _runner_tokens()
    roles = (
        runner.NEUTRAL_FIXTURE_EMITTER,
        runner.DENSE_REFERENCE,
        runner.PLAIN_EVIDENCE,
        runner.PLAIN_EVIDENCE,
        runner.GCAPEPS_EVIDENCE,
        runner.GCAPEPS_EVIDENCE,
        runner.SDIM_COMPUTATION,
    )
    ids = ("fixture", "dense", "p1", "p2", "g1", "g2", "sdim")
    input_ids = (None, None, 1, 2, 1, 2, None)
    registry = {
        launch_id: _product(adapter, role, launch_id, input_id=input_id)
        for launch_id, role, input_id in zip(
            ids, roles, input_ids, strict=True
        )
    }
    inventory = _product(
        adapter,
        runner.SDIM_INVENTORY_COLLECTOR,
        "inventory",
    )
    spec = _spec(runner.TERMINAL_COMPARATOR, dependencies=ids)
    dependencies = adapter._semantic_dependency_products(
        runner,
        spec,
        registry,
        inventory=inventory,
    )
    assert tuple(dependencies) == (
        "fixture",
        "dense",
        "plain_input1",
        "plain_input2",
        "gc_input1",
        "gc_input2",
        "sdim",
    )
    with pytest.raises(ValueError, match="role/input cardinality"):
        adapter._semantic_dependency_products(
            runner,
            _spec(
                runner.TERMINAL_COMPARATOR,
                dependencies=(ids[1], ids[0], *ids[2:]),
            ),
            registry,
            inventory=inventory,
        )
    with pytest.raises(ValueError, match="duplicated"):
        adapter._semantic_dependency_products(
            runner,
            _spec(
                runner.TERMINAL_COMPARATOR,
                dependencies=(*ids[:-1], ids[-2]),
            ),
            registry,
            inventory=inventory,
        )


def test_qualifiers_recompute_dense_tail_and_terminal_gate(adapter):
    runner = _runner_tokens()
    dense_spec = _spec(runner.DENSE_REFERENCE)
    assert adapter._qualifier_from_core(
        runner, dense_spec, _dense_core()
    ) is True
    inconsistent = copy.deepcopy(_dense_core())
    inconsistent["fixed_blp"]["maximum_increment"] = 0.0
    with pytest.raises(ValueError, match="inconsistent"):
        adapter._qualifier_from_core(runner, dense_spec, inconsistent)

    cap_spec = _spec(runner.GCAPEPS_EVIDENCE)
    cap = {
        "positive_cap_event_count": 1,
        "split_records": [{"positive_discarded_weight": True}],
    }
    assert adapter._qualifier_from_core(runner, cap_spec, cap) is True
    cap["positive_cap_event_count"] = 0
    with pytest.raises(ValueError, match="disagrees"):
        adapter._qualifier_from_core(runner, cap_spec, cap)

    comparator_spec = _spec(runner.TERMINAL_COMPARATOR)
    assert adapter._qualifier_from_core(
        runner, comparator_spec, _comparator_core()
    ) is True
    malformed = _comparator_core()
    malformed["positive_bond32_gate"]["paths"][0]["lane"] = []
    with pytest.raises(ValueError, match="inconsistent"):
        adapter._qualifier_from_core(runner, comparator_spec, malformed)


def test_dense_qualifier_recomputes_each_multistep_blp_increment_once(adapter):
    runner = _runner_tokens()
    dense_spec = _spec(runner.DENSE_REFERENCE)
    distances = (0.6, 0.2, 0.35, 0.1)
    core = _dense_core(distances)

    assert core["fixed_blp"]["increments"] == pytest.approx(
        [-0.4, 0.15, -0.25]
    )
    assert adapter._qualifier_from_core(runner, dense_spec, core) is True


def test_development_search_serializes_a_nonempty_calibration_selection(adapter):
    pair = SimpleNamespace(
        gamma_index=2,
        gamma_label="gamma_2",
        gamma_float64_hex="0x1.0000000000000p-2",
        rounds_index=3,
        rounds=10,
    )
    result = SimpleNamespace(
        selection=SimpleNamespace(
            pair=pair,
            qualifying_seeds=(101, 202, 303),
        ),
        wall_root_ns=11,
        wall_deadline_ns=22,
        probe_attempt_count=3,
        prepublication_disposition="TARGET_SELECTED",
        launch_audit=(),
        stage_seed_audit=(),
    )

    payload = adapter._development_search_json(None, result)

    assert payload["selection"] == {
        "gamma_index": 2,
        "gamma_label": "gamma_2",
        "gamma_float64_hex": "0x1.0000000000000p-2",
        "rounds_index": 3,
        "rounds_star": 10,
        "qualifying_seeds": [101, 202, 303],
    }
    assert payload["probe_attempt_count"] == 3
    assert payload["prepublication_disposition"] == "TARGET_SELECTED"
    assert payload["launch_audit"] == []
    assert payload["stage_seed_audit"] == []


def test_timeout_values_reject_before_launch(adapter):
    for value in (True, 0, -1, math.nan, math.inf, -math.inf):
        with pytest.raises(ValueError, match="timeout"):
            adapter.launch_development_direct(
                runtime=None,
                spec=None,
                dependencies={},
                output_root=Path("/not-used"),
                interpreters=None,
                timeout_seconds=value,
            )


def test_descendant_group_after_parent_exit_must_disappear(adapter, monkeypatch):
    class ExitedParent:
        pid = 73001

        @staticmethod
        def poll():
            return 0

        @staticmethod
        def wait(*, timeout):
            raise AssertionError("exited parent must not be waited")

    calls = []
    probes_after_kill = 0

    def eventual_killpg(pgid, sig):
        nonlocal probes_after_kill
        calls.append((pgid, sig))
        if sig == signal.SIGKILL:
            probes_after_kill = 1
        elif sig == 0 and probes_after_kill:
            probes_after_kill += 1
            if probes_after_kill == 3:
                raise ProcessLookupError

    monkeypatch.setattr(adapter.os, "killpg", eventual_killpg)
    monkeypatch.setattr(adapter.time, "sleep", lambda _: None)
    method = adapter._terminate_process_group(
        ExitedParent(),
        grace_seconds=1.0,
    )
    assert method == "sigterm_then_sigkill_group"
    assert (ExitedParent.pid, signal.SIGKILL) in calls
    assert calls[-1] == (ExitedParent.pid, 0)

    monkeypatch.setattr(adapter.os, "killpg", lambda pgid, sig: None)
    ticks = iter((10.0, 10.0))
    monkeypatch.setattr(adapter.time, "monotonic", lambda: next(ticks))
    with pytest.raises(RuntimeError, match="survived SIGKILL"):
        adapter._terminate_process_group(
            ExitedParent(),
            grace_seconds=0.0,
        )


def test_file_caps_exclusive_write_and_all_streams_close(
    adapter,
    tmp_path,
    monkeypatch,
):
    path = (tmp_path / "artifact.bin").absolute()
    identity = adapter._write_bytes_exclusive(path, b"abcdef")
    assert identity["sha256"] == hashlib.sha256(b"abcdef").hexdigest()
    with pytest.raises(FileExistsError):
        adapter._write_bytes_exclusive(path, b"replacement")
    bounded, raw, exceeded = adapter._bounded_regular_file(path, byte_cap=6)
    assert bounded["byte_length"] == 6
    assert raw == b"abcdef"
    assert exceeded is False
    _, raw, exceeded = adapter._bounded_regular_file(path, byte_cap=5)
    assert raw is None
    assert exceeded is True

    class Stream:
        def __init__(self, fd):
            self.fd = fd
            self.closed = False

        def fileno(self):
            return self.fd

        def close(self):
            self.closed = True

    first, second = Stream(1), Stream(2)
    monkeypatch.setattr(
        adapter.os,
        "fsync",
        lambda fd: (
            (_ for _ in ()).throw(OSError("fsync")) if fd == 1 else None
        ),
    )
    with pytest.raises(OSError, match="fsync"):
        adapter._close_development_streams(
            (first, second),
            active_error=False,
        )
    assert first.closed is True
    assert second.closed is True


def test_development_child_sets_file_limit_before_runtime_import(
    adapter,
    monkeypatch,
    tmp_path,
):
    events = []
    monkeypatch.setattr(
        adapter.resource,
        "setrlimit",
        lambda resource_id, limits: events.append((resource_id, limits)),
    )

    def stop_runtime():
        events.append("runtime")
        raise RuntimeError("stop")

    monkeypatch.setattr(adapter, "initialize_runtime", stop_runtime)
    with pytest.raises(RuntimeError, match="stop"):
        adapter._development_child(
            tmp_path / "unused.json",
            file_limit_bytes=4096,
        )
    assert events[0] == (
        adapter.resource.RLIMIT_FSIZE,
        (4096, 4096),
    )
    assert events[1] == "runtime"


def test_fresh_subprocess_launch_has_no_fake_systemd_facts(
    adapter,
    monkeypatch,
    tmp_path,
):
    published = []

    class Identity:
        def __init__(self, path):
            self.path = str(path)
            self.sha256 = _digest(str(path))

    runner = _runner_tokens()
    runner.STDERR_MAX_BYTES = 128
    runner.frame_limits = lambda role: (1, 1, 128)
    runner.with_result_projection = lambda payload: dict(payload)
    runner.publish_canonical_json_noreplace = lambda path, value: (
        published.append((path, value)) or Identity(path)
    )
    runner.decode_clean_worker_frames = lambda raw, role: (
        _ for _ in ()
    ).throw(ValueError("empty"))
    runner.classify_clean_worker_core = lambda core: "completed_result"
    runtime = adapter.RuntimeModules(
        runner=runner,
        orchestration=None,
        runner_identity={},
    )
    interpreters = adapter.DirectInterpreters(
        fork_python=Path(sys.executable),
        fork_identity={"path": sys.executable},
        sdim_python=Path(sys.executable),
        sdim_identity={"path": sys.executable},
    )
    popen_kwargs = {}

    class Process:
        pid = 74001
        returncode = 0

        def __init__(self, command, **kwargs):
            popen_kwargs.update(command=command, **kwargs)

        def wait(self, timeout):
            return 0

        def poll(self):
            return 0

    monkeypatch.setattr(adapter.subprocess, "Popen", Process)
    result = adapter.launch_development_direct(
        runtime=runtime,
        spec=_spec(runner.DENSE_REFERENCE),
        dependencies={},
        output_root=tmp_path,
        interpreters=interpreters,
        timeout_seconds=1.0,
    )
    assert popen_kwargs["start_new_session"] is True
    assert "PYTHONPATH" not in popen_kwargs["env"]
    assert "--development-file-limit-bytes" in popen_kwargs["command"]
    assert result.terminal_kind == "invalid_control"
    assert result.process_receipt["systemd_facts"] is None
    assert result.process_receipt["fresh_ordinary_subprocess"] is True


def test_mocked_full_grid_run_has_bounded_dependency_registry(
    adapter,
    authenticated_interpreters,
    monkeypatch,
    tmp_path,
):
    runner = _load(RUNNER_PATH, "gcapeps_fm_adapter_mock_runner")
    orchestration = _load(
        ORCHESTRATION_PATH,
        "gcapeps_fm_adapter_mock_orchestration",
    )
    runtime = adapter.RuntimeModules(
        runner=runner,
        orchestration=orchestration,
        runner_identity={},
    )
    launches = []
    source_identity = _mock_parent_source_identity(adapter)
    monkeypatch.setattr(
        adapter, "_authenticate_parent_repository", lambda: source_identity
    )

    def launch_direct(
        *,
        runtime,
        spec,
        dependencies,
        output_root,
        interpreters,
        timeout_seconds,
    ):
        launches.append(spec)
        assert interpreters.fork_identity[
            "development_source_authentication"
        ] == source_identity
        assert interpreters.sdim_identity[
            "development_source_authentication"
        ] == source_identity
        if spec.role == runner.DENSE_REFERENCE:
            core = (
                _dense_core()
                if spec.parameter_map()["seed"] == 0
                else _dense_core((0.3, 0.2))
            )
        elif spec.role in {
            runner.PLAIN_CAP_PROBE,
            runner.GCAPEPS_CAP_PROBE,
            runner.PLAIN_EVIDENCE,
            runner.GCAPEPS_EVIDENCE,
        }:
            core = {
                "positive_cap_event_count": 1,
                "split_records": [
                    {"positive_discarded_weight": True}
                ],
            }
        elif spec.role == runner.TERMINAL_COMPARATOR:
            core = _comparator_core()
        else:
            core = {"schema": "mock.completed.v1"}
        core = dict(core)
        core["schema"] = runner.ROLE_CORE_SCHEMAS[spec.role]
        product = _product(
            adapter,
            spec.role,
            spec.launch_id,
            input_id=spec.parameter_map().get("input_id"),
        )
        return adapter.DirectProduct(
            **{
                **product.__dict__,
                "core": core,
                "core_bytes": b"{}",
            }
        )

    report, identity = adapter.run_development_direct(
        runtime=runtime,
        output_root=tmp_path / "development",
        interpreters=authenticated_interpreters,
        timeout_seconds=1.0,
        launch_direct=launch_direct,
    )
    assert len(launches) > 300
    assert report["formal_claim_eligible"] is False
    assert report["runs_full_adaptive_calibration"] is True
    assert report["development_pair_bound"] is None
    assert report["systemd_facts"] is None
    assert report["production_b_cal_transport_equivalent"] is False
    assert report["source_identity"] == source_identity
    assert report["calibration"]["selection"] is None
    registry = report["dependency_registry"]
    assert registry["maximum_live_entries"] <= 13
    assert registry["maximum_retained_core_or_trailer_bytes"] == 0
    assert registry["pair_reset_count"] == 19
    assert registry["final_live_entries"] == 0
    assert registry["retention"] == (
        "pair_scoped_authenticated_core_file_identity_only"
    )
    assert set(report["forbidden_outputs"]) == {
        "target_amendment",
        "formal_heldout_report",
        "systemd_node_terminal",
        "systemd_launch_receipt",
    }
    assert Path(identity.path).is_file()
