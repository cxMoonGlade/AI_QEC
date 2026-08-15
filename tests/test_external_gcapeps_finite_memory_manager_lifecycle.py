from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import stat
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT
    / "scripts"
    / "external_baselines"
    / "run_gcapeps_finite_memory_bond32.py"
)


def _load_module():
    name = "gcapeps_finite_memory_manager_lifecycle"
    spec = importlib.util.spec_from_file_location(name, MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _result(module, *, schema, marker, terminal_kind=None):
    payload = {"schema": schema, "manager_test_marker": marker}
    if terminal_kind is not None:
        payload["terminal_kind"] = terminal_kind
    core = module.with_result_projection(payload)
    core_bytes = module.canonical_json_bytes(core)
    timer = module._TIMING.LayeredTimer()
    with timer.span(
        f"{marker}.root",
        scope="manager_test_worker_total",
        kind="test_worker",
    ):
        pass
    timing = timer.finish()
    trailer_bytes = module._TIMING.build_late_telemetry_trailer(
        core_bytes,
        timing,
    )
    return {
        "core": core,
        "core_bytes": core_bytes,
        "timing": timing,
        "trailer_bytes": trailer_bytes,
        "framed_bytes": module._TIMING.encode_two_frames(
            core_bytes,
            trailer_bytes,
        ),
    }


def _input_identity(module, *, partition, role):
    return {
        "byte_length": 0,
        "sha256": module.sha256_hex(b""),
        "ordered_entries": [
            {"name": name, "source_sha256": "0" * 64}
            for name in module.expected_entry_sequence(partition, role)
        ],
    }


def _fixture_transport(module):
    manager = module.TransportArtifact.from_payload(
        name="manager_preflight_receipt",
        schema=module.MANAGER_PREFLIGHT_RECEIPT_SCHEMA,
        payload=module.with_result_projection(
            {
                "schema": module.MANAGER_PREFLIGHT_RECEIPT_SCHEMA,
                "selected_scope": "system",
            }
        ),
    )
    inventory_result = _result(
        module,
        schema=module.SDIM_INVENTORY_SCHEMA,
        marker="inventory",
    )
    launch_id = "inventory-for-fixture-smoke"
    cleanup = module.completed_cleanup_facts(deadline_ns=30_000_000_000)
    quarantine = module.completed_quarantine_facts(
        relative_path=f"raw_spools/{launch_id}"
    )
    node = module.build_node_terminal(
        launch_id=launch_id,
        run_partition=module.BOOTSTRAP,
        role=module.SDIM_INVENTORY_COLLECTOR,
        terminal_kind="completed_result",
        input_transport=_input_identity(
            module,
            partition=module.BOOTSTRAP,
            role=module.SDIM_INVENTORY_COLLECTOR,
        ),
        core=inventory_result["core"],
        trailer=module.parse_canonical_json_object(
            inventory_result["trailer_bytes"]
        ),
        raw_stdout=module.RawFileIdentity.from_bytes(
            inventory_result["framed_bytes"]
        ).as_dict(),
        raw_stderr=module.RawFileIdentity.from_bytes(b"").as_dict(),
        unit_facts={},
        cgroup_barrier={},
        exit_facts={},
        failure_snapshot=None,
        final_systemd_memory_peak_bytes=1,
        cleanup=cleanup,
        quarantine=quarantine,
    )
    node_raw = module.canonical_json_bytes(node)
    node_path = Path("/tmp/inventory-for-fixture-smoke.json")
    identity = module.PublishedFileIdentity(
        path=str(node_path),
        byte_length=len(node_raw),
        sha256=module.sha256_hex(node_raw),
        st_dev=1,
        st_ino=2,
        st_mode=stat.S_IFREG | 0o644,
        st_nlink=1,
    )
    receipt = module.build_launch_receipt(
        launch_id=launch_id,
        run_partition=module.BOOTSTRAP,
        role=module.SDIM_INVENTORY_COLLECTOR,
        node_terminal_path=node_path,
        node_terminal_identity=identity,
        terminal_kind="completed_result",
        cleanup=cleanup,
        quarantine=quarantine,
        supervisor_launch_wall_ns=1,
    )
    artifacts = (
        manager,
        module.TransportArtifact.from_payload(
            name="sdim_inventory_envelope",
            schema=module.NODE_TERMINAL_SCHEMA,
            payload=node,
        ),
        module.TransportArtifact.from_payload(
            name="sdim_inventory_launch_receipt",
            schema=module.LAUNCH_RECEIPT_SCHEMA,
            payload=receipt,
        ),
    )
    return module.build_input_transport(
        run_partition=module.CALIBRATION,
        role=module.NEUTRAL_FIXTURE_EMITTER,
        role_parameters={
            "width": 7,
            "rounds": 4,
            "axis_family": 3,
            "p_event_numerator": 3,
            "p_event_denominator": 4,
            "seed": 0,
            "gamma_index": 0,
            "rounds_index": 0,
            "run_blpensemble": False,
        },
        artifacts=artifacts,
    )


def _write(path, text):
    path.write_text(text, encoding="ascii")


class _FakeManager:
    def __init__(
        self,
        module,
        *,
        cgroup_root,
        proc_root,
        runtime_root,
        selected_cpu,
        worker_terminal_kind=None,
    ):
        self.module = module
        self.cgroup_root = cgroup_root
        self.proc_root = proc_root
        self.runtime_root = runtime_root
        self.selected_cpu = selected_cpu
        self.spec = None
        self.submitted = False
        self.continued = False
        self.stopped = False
        self.pid = 4242
        self.memory_peak = 123456
        self.worker_terminal_kind = worker_terminal_kind

    def _observation(self, command):
        return self.module.ManagerCommandObservation(
            command=tuple(command),
            returncode=0,
            stdout=b"",
            stderr=b"",
        )

    def submit(self, spec):
        self.spec = spec
        self.submitted = True
        output_path = Path(spec.property_map()["StandardOutput"][5:])
        result = _result(
            self.module,
            schema=self.module.FIXTURE_SCHEMA,
            marker="fixture",
            terminal_kind=self.worker_terminal_kind,
        )
        fd = os.open(output_path, os.O_WRONLY | os.O_TRUNC)
        try:
            os.write(fd, result["framed_bytes"])
            os.fsync(fd)
        finally:
            os.close(fd)
        group = self.cgroup_root / "fake.slice" / spec.unit_name
        group.mkdir(parents=True)
        _write(group / "cgroup.procs", f"{self.pid}\n")
        _write(group / "cgroup.threads", f"{self.pid}\n")
        _write(group / "memory.current", "100000\n")
        _write(group / "memory.peak", f"{self.memory_peak}\n")
        _write(group / "memory.swap.current", "0\n")
        _write(
            group / "memory.events",
            "low 0\nhigh 0\nmax 0\noom 0\noom_kill 0\noom_group_kill 0\n",
        )
        _write(group / "pids.current", "1\n")
        _write(group / "pids.peak", "1\n")
        _write(group / "pids.events", "max 0\n")
        _write(group / "cpu.stat", "usage_usec 12\nuser_usec 8\nsystem_usec 4\n")
        proc = self.proc_root / str(self.pid)
        proc.mkdir(parents=True)
        _write(
            proc / "status",
            "Name:\tfixture\nState:\tT (stopped)\n"
            "Uid:\t60001\t60001\t60001\t60001\n"
            f"Cpus_allowed_list:\t{self.selected_cpu}\n",
        )
        (self.runtime_root / spec.runtime_directory).mkdir()
        return self._observation(spec.command)

    def show(self, unit_name, properties):
        names = tuple(properties)
        if names == ("LoadState",):
            return {
                "LoadState": (
                    "not-found" if not self.submitted or self.stopped else "loaded"
                )
            }
        if names == ("MainPID", "ControlGroup"):
            return {
                "MainPID": str(self.pid),
                "ControlGroup": f"/fake.slice/{unit_name}",
            }
        if names == self.module._FULL_EFFECTIVE_PROPERTIES:
            return self.module.expected_effective_systemd_properties(self.spec)
        if names == self.module._UNIT_BARRIER_PROPERTIES:
            return {
                "MainPID": str(self.pid),
                "ControlPID": "0",
                "ControlGroup": f"/fake.slice/{unit_name}",
                "Result": "success",
                "ExecMainCode": "exited",
                "ExecMainStatus": "0",
                "InvocationID": "b" * 32,
            }
        if names == (
            "ActiveState",
            "SubState",
            "MainPID",
            "Result",
            "ExecMainCode",
            "ExecMainStatus",
            "MemoryPeak",
        ):
            if not self.continued:
                return {
                    "ActiveState": "activating",
                    "SubState": "start",
                    "MainPID": str(self.pid),
                    "Result": "success",
                    "ExecMainCode": "exited",
                    "ExecMainStatus": "0",
                    "MemoryPeak": str(self.memory_peak),
                }
            return {
                "ActiveState": "active",
                "SubState": "exited",
                "MainPID": "0",
                "Result": "success",
                "ExecMainCode": "exited",
                "ExecMainStatus": "0",
                "MemoryPeak": str(self.memory_peak),
            }
        raise AssertionError(f"unexpected show projection: {names}")

    def signal_continue(self, unit_name):
        self.continued = True
        return self._observation(("signal-continue", unit_name))

    def stop(self, unit_name):
        self.stopped = True
        runtime = self.runtime_root / self.spec.runtime_directory
        if runtime.exists():
            runtime.rmdir()
        return self._observation(("stop", unit_name))

    def wait_show(
        self,
        unit_name,
        properties,
        predicate,
        *,
        timeout_seconds,
    ):
        value = self.show(unit_name, properties)
        assert predicate(value)
        return value


class _FakeSacrificialManager(_FakeManager):
    def __init__(self, *args, accessible_probe=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.accessible_probe = accessible_probe

    def submit(self, spec):
        observation = super().submit(spec)
        properties = spec.property_map()
        stdin_path = Path(properties["StandardInput"][5:])
        stdout_path = Path(properties["StandardOutput"][5:])
        stderr_path = Path(properties["StandardError"][5:])
        parsed = self.module.parse_input_transport(
            stdin_path.read_bytes(),
            expected_partition=self.module.BOOTSTRAP,
            expected_role=self.module.SACRIFICIAL_MANAGER_PREFLIGHT,
        )
        parameters = parsed.manifest["role_parameters"]
        stdio_paths = (stdin_path, stdout_path, stderr_path)
        stdio = []
        for fd, path in enumerate(stdio_paths):
            observed = path.stat()
            stdio.append(
                {
                    "fd": fd,
                    "st_dev": int(observed.st_dev),
                    "st_ino": int(observed.st_ino),
                    "st_mode": int(observed.st_mode),
                    "st_nlink": int(observed.st_nlink),
                    "st_uid": int(observed.st_uid),
                    "is_regular": stat.S_ISREG(observed.st_mode),
                }
            )
        pid = parameters["runner_pid"]
        targets = (
            parameters["output_root_abs"],
            parameters["evaluator_probe_abs"],
            parameters["quarantined_spool_probe_abs"],
            f"/proc/{pid}/root",
            f"/proc/{pid}/fd",
            f"/proc/{pid}/mem",
            f"pid:{pid}",
            f"pid:{pid}",
        )
        attack_probes = []
        for index, (probe, target) in enumerate(
            zip(self.module._SACRIFICIAL_ATTACK_PROBES, targets)
        ):
            accessible = self.accessible_probe and index == 0
            attack_probes.append(
                {
                    "probe": probe,
                    "target": target,
                    "outcome": "accessible" if accessible else "denied",
                    "errno": None if accessible else 13,
                }
            )
        runner_namespaces = parameters["runner_namespace_identity"]
        core = self.module.with_result_projection(
            {
                "schema": self.module.SACRIFICIAL_PREFLIGHT_SCHEMA,
                "status": "observed",
                "runner_lineage": {
                    "pid": parameters["runner_pid"],
                    "proc_start_time_ticks": parameters[
                        "runner_start_time_ticks"
                    ],
                    "real_uid": parameters["runner_real_uid"],
                    "real_gid": parameters["runner_real_gid"],
                },
                "process_identity": {
                    "pid": self.pid,
                    "parent_pid": 1,
                    "real_uid": 60001,
                    "effective_uid": 60001,
                    "real_gid": 60001,
                    "effective_gid": 60001,
                    "supplementary_gids": [int(properties["SupplementaryGroups"])],
                    "working_directory": str(ROOT),
                    "cpu_affinity": [self.selected_cpu],
                },
                "stdio_identity": stdio,
                "namespace_identity": {
                    "user": runner_namespaces["user"] + "-child",
                    "mnt": runner_namespaces["mnt"] + "-child",
                    "net": runner_namespaces["net"] + "-child",
                    "pid": runner_namespaces["pid"],
                },
                "proc_security": {
                    "NoNewPrivs": "1",
                    "Seccomp": "2",
                    "Seccomp_filters": "1",
                },
                "environment_contract": {
                    "configured_values": dict(self.module._FROZEN_CHILD_ENVIRONMENT),
                    "pythonpath_present": False,
                },
                "attack_probes": attack_probes,
            }
        )
        core_bytes = self.module.canonical_json_bytes(core)
        timer = self.module._TIMING.LayeredTimer()
        with timer.span(
            "sacrificial.root", scope="sacrificial_test", kind="test_worker"
        ):
            pass
        trailer = self.module._TIMING.build_late_telemetry_trailer(
            core_bytes, timer.finish()
        )
        stdout_path.write_bytes(
            self.module._TIMING.encode_two_frames(core_bytes, trailer)
        )
        stderr_path.write_bytes(b"")
        return observation


class _FakeFailedManager:
    def __init__(
        self,
        module,
        *,
        cgroup_root,
        proc_root,
        runtime_root,
        selected_cpu,
        service_result,
        partial_stdout=b"partial",
    ):
        self.module = module
        self.cgroup_root = cgroup_root
        self.proc_root = proc_root
        self.runtime_root = runtime_root
        self.selected_cpu = selected_cpu
        self.service_result = service_result
        self.partial_stdout = partial_stdout
        self.spec = None
        self.submitted = False
        self.helper_continued = False
        self.stopped = False
        self.reset = False
        self.control_pid = 5151
        self.memory_peak = 30
        self.snapshot_raw = None

    def _observation(self, command):
        return self.module.ManagerCommandObservation(
            command=tuple(command),
            returncode=0,
            stdout=b"",
            stderr=b"",
        )

    def submit(self, spec):
        self.spec = spec
        self.submitted = True
        properties = spec.property_map()
        stdout_path = Path(properties["StandardOutput"][5:])
        stderr_path = Path(properties["StandardError"][5:])
        stdout_path.write_bytes(self.partial_stdout)
        stderr_path.write_bytes(b"synthetic failed child\n")
        group = self.cgroup_root / "fake.slice" / spec.unit_name
        group.mkdir(parents=True)
        runtime = self.runtime_root / spec.runtime_directory
        runtime.mkdir(mode=0o755)
        payload = _failure_snapshot_payload(
            self.module,
            launch_id=spec.launch_id,
            cgroup_path=group.resolve(),
            result=self.service_result,
        )
        self.snapshot_raw = self.module.canonical_json_bytes(payload)
        snapshot = runtime / "failure_snapshot.json"
        snapshot.write_bytes(self.snapshot_raw)
        snapshot.chmod(0o644)
        proc = self.proc_root / str(self.control_pid)
        proc.mkdir(parents=True)
        current_uid = os.geteuid()
        _write(
            proc / "status",
            "Name:\tsnapshot-helper\nState:\tT (stopped)\n"
            f"Uid:\t{current_uid}\t{current_uid}\t{current_uid}\t{current_uid}\n"
            f"Cpus_allowed_list:\t{self.selected_cpu}\n",
        )
        return self._observation(spec.command)

    def show(self, unit_name, properties):
        names = tuple(properties)
        if names == ("LoadState",):
            return {
                "LoadState": (
                    "not-found" if not self.submitted or self.reset else "loaded"
                )
            }
        if names == self.module._FULL_EFFECTIVE_PROPERTIES:
            return self.module.expected_effective_systemd_properties(self.spec)
        if names == self.module._UNIT_BARRIER_PROPERTIES:
            return {
                "MainPID": "0",
                "ControlPID": (
                    "0" if self.helper_continued else str(self.control_pid)
                ),
                "ControlGroup": f"/fake.slice/{unit_name}",
                "Result": self.service_result,
                "ExecMainCode": "exited",
                "ExecMainStatus": "1",
                "InvocationID": "a" * 32,
            }
        if names == self.module._FAILURE_HELPER_EXIT_PROPERTIES:
            return {
                "ActiveState": "failed",
                "SubState": "failed",
                "ControlPID": "0" if self.helper_continued else str(self.control_pid),
                "Result": self.service_result,
                "ExecMainCode": "exited",
                "ExecMainStatus": "1",
                "MemoryPeak": str(self.memory_peak),
            }
        raise AssertionError(f"unexpected failed-manager show: {names}")

    def signal_continue_control(self, unit_name):
        self.helper_continued = True
        runtime = self.runtime_root / self.spec.runtime_directory
        (runtime / "failure_snapshot.json").unlink()
        runtime.rmdir()
        return self._observation(("signal-control", unit_name))

    def stop(self, unit_name):
        self.stopped = True
        return self._observation(("stop", unit_name))

    def reset_failed(self, unit_name):
        assert self.stopped
        self.reset = True
        return self._observation(("reset-failed", unit_name))

    def wait_show(
        self,
        unit_name,
        properties,
        predicate,
        *,
        timeout_seconds,
    ):
        value = self.show(unit_name, properties)
        assert predicate(value)
        return value


def test_fixture_manager_vertical_slice_quarantines_and_publishes(tmp_path):
    module = _load_module()
    output = tmp_path / "output"
    output.mkdir(mode=0o755)
    quarantine = output / "raw_spools"
    quarantine.mkdir(mode=0o755)
    spool_parent = tmp_path / "spool-parent"
    spool_parent.mkdir(mode=0o700)
    cgroup_root = tmp_path / "cgroup"
    cgroup_root.mkdir()
    proc_root = tmp_path / "proc"
    proc_root.mkdir()
    runtime_root = tmp_path / "run"
    runtime_root.mkdir()
    selected_cpu = module.select_benchmark_cpu()
    manager = _FakeManager(
        module,
        cgroup_root=cgroup_root,
        proc_root=proc_root,
        runtime_root=runtime_root,
        selected_cpu=selected_cpu,
    )
    node_path = output / "fixture-smoke.node.json"
    receipt_path = output / "fixture-smoke.receipt.json"
    result = module.run_fixture_systemd_lifecycle(
        launch_id="fixture-manager-smoke-1",
        input_transport_raw=_fixture_transport(module),
        repository_abs=ROOT,
        run_output_abs=output,
        spool_parent_abs=spool_parent,
        quarantine_parent_abs=quarantine,
        node_terminal_path=node_path,
        launch_receipt_path=receipt_path,
        selected_cpu=selected_cpu,
        repository_read_gid=os.getgid(),
        python_executable=Path(sys.executable).resolve(),
        manager_client=manager,
        cgroup_root=cgroup_root,
        proc_root=proc_root,
        runtime_root=runtime_root,
    )
    assert manager.continued and manager.stopped
    assert result.node_terminal["terminal_kind"] == "completed_result"
    assert result.node_terminal["core_schema"] == module.FIXTURE_SCHEMA
    assert result.launch_receipt["node_terminal_complete_file_sha256"] == (
        result.node_identity.sha256
    )
    assert stat.S_IMODE(node_path.stat().st_mode) == 0o644
    assert stat.S_IMODE(receipt_path.stat().st_mode) == 0o644
    assert list(spool_parent.iterdir()) == []
    retained = quarantine / "fixture-manager-smoke-1"
    assert sorted(path.name for path in retained.iterdir()) == sorted(
        module._SPOOL_FILENAMES
    )
    assert all(
        stat.S_IMODE(path.stat().st_mode) == 0o600 for path in retained.iterdir()
    )
    module.validate_node_terminal(
        module.parse_canonical_json_object(node_path.read_bytes())
    )
    module.validate_launch_receipt(
        module.parse_canonical_json_object(receipt_path.read_bytes())
    )


def test_stopped_cgroup_rejects_a_running_thread(tmp_path):
    module = _load_module()
    cgroup_root = tmp_path / "cgroup"
    group = cgroup_root / "unit"
    group.mkdir(parents=True)
    proc_root = tmp_path / "proc"
    proc = proc_root / "7"
    proc.mkdir(parents=True)
    _write(group / "cgroup.procs", "7\n")
    _write(group / "cgroup.threads", "7\n")
    _write(
        proc / "status",
        "State:\tS (sleeping)\nUid:\t1\t1\t1\t1\nCpus_allowed_list:\t0\n",
    )
    with pytest.raises(ValueError, match="not stopped"):
        module.capture_stopped_cgroup_snapshot(
            {"MainPID": "7", "ControlGroup": "/unit"},
            selected_cpu=0,
            cgroup_root=cgroup_root,
            proc_root=proc_root,
        )


def test_system_scope_auth_failure_is_explicit_permission_blocker():
    module = _load_module()
    observation = module.ManagerCommandObservation(
        command=(
            "systemd-run",
            "--system",
            "--no-block",
            "--no-ask-password",
            "--unit=gcapeps-fm-preflight.service",
        ),
        returncode=1,
        stdout=b"",
        stderr=(
            b"Failed to start transient service unit: "
            b"Interactive authentication required.\n"
        ),
    )
    assert module.classify_system_manager_observation(observation) == (
        module.MANAGER_PERMISSION_BLOCKED
    )
    decision = module.build_permission_blocked_manager_preflight_decision(observation)
    payload = decision.as_payload()
    assert payload["status"] == "PERMISSION_BLOCKED"
    assert payload["selected_scope"] is None
    assert payload["user_manager_fallback_attempted"] is False
    assert payload["science_launch_eligible"] is False
    module.validate_result_projection(payload)
    client = module.SystemdManagerClient(
        command_runner=lambda command, timeout: observation,
    )
    with pytest.raises(
        module.SystemManagerCommandError,
        match="Interactive authentication required",
    ) as captured:
        client._require_success(observation.command)
    assert captured.value.classification == module.MANAGER_PERMISSION_BLOCKED


def _failure_snapshot_payload(module, *, launch_id, cgroup_path, result):
    return module.with_result_projection(
        {
            "schema": module.FAILURE_SNAPSHOT_SCHEMA,
            "launch_id": launch_id,
            "service_result": result,
            "exit_code": "exited",
            "exit_status": "1",
            "invocation_id": "a" * 32,
            "cgroup_path": str(cgroup_path),
            "live_cgroup": {
                "memory_current": 10,
                "memory_peak": 20,
                "memory_swap_current": 0,
                "pids_current": 1,
                "pids_peak": 1,
                "memory_events": {
                    "low": 0,
                    "high": 0,
                    "max": 0,
                    "oom": 0,
                    "oom_kill": 0,
                    "oom_group_kill": 0,
                },
                "pids_events": {"max": 0},
                "cpu_stat": {
                    "usage_usec": 3,
                    "user_usec": 2,
                    "system_usec": 1,
                },
            },
        }
    )


def test_failure_snapshot_is_copied_only_from_stopped_bound_helper(tmp_path):
    module = _load_module()
    launch_id = "failure-helper-copy-1"
    selected_cpu = module.select_benchmark_cpu()
    cgroup_root = tmp_path / "cgroup"
    group = cgroup_root / "fake.slice" / "unit.service"
    group.mkdir(parents=True)
    runtime_root = tmp_path / "run"
    runtime_root.mkdir()
    runtime = runtime_root / f"gcapeps-fm-{launch_id}"
    runtime.mkdir(mode=0o755)
    proc_root = tmp_path / "proc"
    control_pid = 5151
    proc = proc_root / str(control_pid)
    proc.mkdir(parents=True)
    current_uid = os.geteuid()
    _write(
        proc / "status",
        "Name:\tsnapshot-helper\nState:\tT (stopped)\n"
        f"Uid:\t{current_uid}\t{current_uid}\t{current_uid}\t{current_uid}\n"
        f"Cpus_allowed_list:\t{selected_cpu}\n",
    )
    payload = _failure_snapshot_payload(
        module,
        launch_id=launch_id,
        cgroup_path=group.resolve(),
        result="resources",
    )
    raw = module.canonical_json_bytes(payload)
    snapshot_path = runtime / "failure_snapshot.json"
    snapshot_path.write_bytes(raw)
    snapshot_path.chmod(0o644)
    unit_show = {
        "ControlPID": str(control_pid),
        "ControlGroup": "/fake.slice/unit.service",
        "Result": "resources",
        "ExecMainCode": "exited",
        "ExecMainStatus": "1",
        "InvocationID": "a" * 32,
    }
    spool_parent = tmp_path / "spool"
    spool_parent.mkdir(mode=0o700)
    spool = module.create_sealed_launch_spool(
        spool_parent_abs=spool_parent,
        launch_id=launch_id,
        input_transport_raw=_fixture_transport(module),
        expected_partition=module.CALIBRATION,
        expected_role=module.NEUTRAL_FIXTURE_EMITTER,
    )
    continued = []

    class _ControlClient:
        def signal_continue_control(self, unit_name):
            assert os.pread(
                spool.file_fds["failure_snapshot.copy"],
                len(raw),
                0,
            ) == raw
            continued.append(unit_name)
            return module.ManagerCommandObservation(
                command=("signal-control", unit_name),
                returncode=0,
                stdout=b"",
                stderr=b"",
            )

    client = _ControlClient()

    try:
        capture, control_observation = (
            module.capture_failure_snapshot_and_continue(
                client=client,
                unit_name="gcapeps-fm-failure-helper-copy-1.service",
                spool=spool,
                launch_id=launch_id,
                unit_show=unit_show,
                selected_cpu=selected_cpu,
                runtime_root=runtime_root,
                cgroup_root=cgroup_root,
                proc_root=proc_root,
            )
        )
        assert control_observation.returncode == 0
        assert continued == ["gcapeps-fm-failure-helper-copy-1.service"]
        assert capture.raw_bytes == raw
        assert capture.identity() == {
            "schema": module.FAILURE_SNAPSHOT_SCHEMA,
            "byte_length": len(raw),
            "sha256": module.sha256_hex(raw),
        }
        assert os.pread(
            spool.file_fds["failure_snapshot.copy"],
            len(raw),
            0,
        ) == raw
        assert module.classify_failure_snapshot_terminal(payload) == (
            "supervisor_censor"
        )
    finally:
        spool.close()


def test_failure_snapshot_binding_and_terminal_precedence_fail_closed(tmp_path):
    module = _load_module()
    cgroup = tmp_path / "cgroup"
    cgroup.mkdir()
    payload = _failure_snapshot_payload(
        module,
        launch_id="failure-binding-1",
        cgroup_path=cgroup,
        result="timeout",
    )
    assert module.classify_failure_snapshot_terminal(payload) == (
        "supervisor_censor"
    )
    assert module.classify_failure_snapshot_terminal(
        payload,
        self_stop_barrier_reached=True,
    ) == "invalid_control"
    assert module.classify_failure_snapshot_terminal(
        payload,
        sigcont_sent=True,
    ) == "invalid_control"
    assert module.classify_preunit_launch_error(
        OSError(module.errno.EAGAIN, "again")
    ) == "supervisor_censor"
    assert module.classify_preunit_launch_error(
        PermissionError(module.errno.EACCES, "denied")
    ) == "invalid_control"


def _case_roots(tmp_path):
    output = tmp_path / "output"
    output.mkdir(mode=0o755)
    quarantine = output / "raw_spools"
    quarantine.mkdir(mode=0o755)
    spool_parent = tmp_path / "spool-parent"
    spool_parent.mkdir(mode=0o700)
    cgroup_root = tmp_path / "cgroup"
    cgroup_root.mkdir()
    proc_root = tmp_path / "proc"
    proc_root.mkdir()
    runtime_root = tmp_path / "run"
    runtime_root.mkdir()
    return {
        "output": output,
        "quarantine": quarantine,
        "spool_parent": spool_parent,
        "cgroup_root": cgroup_root,
        "proc_root": proc_root,
        "runtime_root": runtime_root,
    }


def _run_fixture_case(module, roots, manager, *, launch_id):
    return module.run_fixture_systemd_lifecycle(
        launch_id=launch_id,
        input_transport_raw=_fixture_transport(module),
        repository_abs=ROOT,
        run_output_abs=roots["output"],
        spool_parent_abs=roots["spool_parent"],
        quarantine_parent_abs=roots["quarantine"],
        node_terminal_path=roots["output"] / f"{launch_id}.node.json",
        launch_receipt_path=roots["output"] / f"{launch_id}.receipt.json",
        selected_cpu=manager.selected_cpu,
        repository_read_gid=os.getgid(),
        python_executable=Path(sys.executable).resolve(),
        manager_client=manager,
        cgroup_root=roots["cgroup_root"],
        proc_root=roots["proc_root"],
        runtime_root=roots["runtime_root"],
    )


def test_clean_schema_valid_worker_censor_publishes_both_artifacts(tmp_path):
    module = _load_module()
    roots = _case_roots(tmp_path)
    manager = _FakeManager(
        module,
        cgroup_root=roots["cgroup_root"],
        proc_root=roots["proc_root"],
        runtime_root=roots["runtime_root"],
        selected_cpu=module.select_benchmark_cpu(),
        worker_terminal_kind="worker_censor",
    )
    result = _run_fixture_case(
        module,
        roots,
        manager,
        launch_id="fixture-worker-censor-1",
    )
    assert result.node_terminal["terminal_kind"] == "worker_censor"
    assert result.launch_receipt["terminal_kind"] == "worker_censor"
    assert result.node_terminal["core"]["terminal_kind"] == "worker_censor"


def _preflight_setup(module, tmp_path, *, accessible_probe):
    roots = _case_roots(tmp_path)
    evaluator = roots["output"] / "evaluator-probe.bin"
    prior_spool = roots["output"] / "prior-spool-probe.bin"
    evaluator.write_bytes(b"evaluator")
    prior_spool.write_bytes(b"prior-spool")
    selected_cpu = module.select_benchmark_cpu()
    manager = _FakeSacrificialManager(
        module,
        cgroup_root=roots["cgroup_root"],
        proc_root=roots["proc_root"],
        runtime_root=roots["runtime_root"],
        selected_cpu=selected_cpu,
        accessible_probe=accessible_probe,
    )
    pid = os.getpid()
    runner_identity = {
        "pid": pid,
        "proc_start_time_ticks": module._proc_start_time(pid),
        "real_uid": os.getuid(),
        "real_gid": os.getgid(),
        "pr_get_dumpable": 0,
    }
    manager_path = (roots["output"] / "manager-preflight.json").absolute()
    kwargs = {
        "launch_id": "sacrificial-manager-preflight-1",
        "runner_identity": runner_identity,
        "evaluator_probe_abs": evaluator,
        "quarantined_spool_probe_abs": prior_spool,
        "repository_abs": ROOT,
        "run_output_abs": roots["output"],
        "spool_parent_abs": roots["spool_parent"],
        "quarantine_parent_abs": roots["quarantine"],
        "node_terminal_path": (
            roots["output"] / "sacrificial-preflight.node.json"
        ).absolute(),
        "launch_receipt_path": (
            roots["output"] / "sacrificial-preflight.receipt.json"
        ).absolute(),
        "manager_preflight_path": manager_path,
        "selected_cpu": selected_cpu,
        "repository_read_gid": os.getgid(),
        "python_executable": Path(sys.executable).resolve(),
        "systemd_build": "systemd 255 (255.4-1)",
        "manager_cgroup": "0::/user.slice/test.scope",
        "cgroup_controllers": ("memory", "cpu", "pids"),
        "manager_client": manager,
        "cgroup_root": roots["cgroup_root"],
        "proc_root": roots["proc_root"],
        "runtime_root": roots["runtime_root"],
    }
    return roots, manager, manager_path, kwargs


def test_successful_sacrificial_preflight_publishes_eligible_exact_receipt(
    tmp_path,
):
    module = _load_module()
    roots, manager, manager_path, kwargs = _preflight_setup(
        module,
        tmp_path,
        accessible_probe=False,
    )
    result = module.run_manager_preflight_lifecycle(**kwargs)
    receipt = result.manager_preflight_receipt
    assert manager.continued and manager.stopped
    assert receipt["status"] == "PASSED"
    assert receipt["selected_scope"] == "system"
    assert receipt["science_launch_eligible"] is True
    assert all(receipt["security_gates"].values())
    assert manager_path.read_bytes() == module.canonical_json_bytes(receipt)
    assert receipt["sacrificial_node_identity"]["sha256"] == (
        result.lifecycle.node_identity.sha256
    )
    module.validate_successful_manager_preflight_receipt(receipt)
    altered = dict(receipt)
    altered["security_gates"] = dict(receipt["security_gates"])
    altered["security_gates"]["attack_probes_denied"] = False
    altered["result_projection_sha256"] = module._projection_sha256(altered)
    with pytest.raises(ValueError, match="unpassed gate"):
        module.validate_successful_manager_preflight_receipt(altered)
    assert list(roots["spool_parent"].iterdir()) == []


def test_accessible_attack_probe_never_publishes_science_eligibility(tmp_path):
    module = _load_module()
    roots, manager, manager_path, kwargs = _preflight_setup(
        module,
        tmp_path,
        accessible_probe=True,
    )
    with pytest.raises(ValueError, match="attack probe was not denied"):
        module.run_manager_preflight_lifecycle(**kwargs)
    assert manager.continued and manager.stopped
    assert not manager_path.exists()
    assert (roots["output"] / "sacrificial-preflight.node.json").exists()
    assert (roots["output"] / "sacrificial-preflight.receipt.json").exists()


@pytest.mark.parametrize(
    ("service_result", "expected_terminal"),
    (("resources", "supervisor_censor"), ("exit-code", "invalid_control")),
)
def test_failed_unit_snapshot_reset_unload_and_terminal_publication(
    tmp_path,
    service_result,
    expected_terminal,
):
    module = _load_module()
    roots = _case_roots(tmp_path)
    manager = _FakeFailedManager(
        module,
        cgroup_root=roots["cgroup_root"],
        proc_root=roots["proc_root"],
        runtime_root=roots["runtime_root"],
        selected_cpu=module.select_benchmark_cpu(),
        service_result=service_result,
        partial_stdout=b"partial",
    )
    launch_id = f"fixture-failed-{service_result}"
    result = _run_fixture_case(
        module,
        roots,
        manager,
        launch_id=launch_id,
    )
    assert manager.helper_continued and manager.stopped and manager.reset
    assert result.node_terminal["terminal_kind"] == expected_terminal
    assert result.launch_receipt["terminal_kind"] == expected_terminal
    assert result.node_terminal["core"] is None
    assert result.node_terminal["trailer"] is None
    assert result.node_terminal["failure_snapshot"]["sha256"] == (
        module.sha256_hex(manager.snapshot_raw)
    )
    facts = result.node_terminal["unit_facts"]
    assert facts["stdout_inspection"]["disposition"] == "truncated"
    assert facts["reset_failed"]["command"][0] == "reset-failed"
    assert facts["unloaded"] == {"LoadState": "not-found"}
    assert result.quarantined_spool.raw_files["failure_snapshot.copy"] == (
        manager.snapshot_raw
    )
    module.validate_node_terminal(result.node_terminal)
    module.validate_launch_receipt(result.launch_receipt)


def test_external_censor_stdout_inspector_rejects_extra_complete_bytes(tmp_path):
    module = _load_module()
    truncated = tmp_path / "truncated.stdout"
    truncated.write_bytes(b"abc")
    fd = os.open(truncated, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        assert module.inspect_external_censor_stdout_fd(
            fd,
            role=module.NEUTRAL_FIXTURE_EMITTER,
        ).disposition == "truncated"
    finally:
        os.close(fd)
    framed = _result(
        module,
        schema=module.FIXTURE_SCHEMA,
        marker="extra-byte",
    )["framed_bytes"]
    extra = tmp_path / "extra.stdout"
    extra.write_bytes(framed + b"x")
    fd = os.open(extra, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        inspection = module.inspect_external_censor_stdout_fd(
            fd,
            role=module.NEUTRAL_FIXTURE_EMITTER,
        )
    finally:
        os.close(fd)
    assert inspection.disposition == "invalid"
    assert inspection.reason == "extra_bytes"


def test_reset_failed_uses_noninteractive_system_scope_command():
    module = _load_module()
    calls = []

    def runner(command, timeout_seconds):
        calls.append((tuple(command), timeout_seconds))
        return module.ManagerCommandObservation(
            command=tuple(command), returncode=0, stdout=b"", stderr=b""
        )

    client = module.SystemdManagerClient(command_runner=runner)
    client.reset_failed("gcapeps-fm-reset-fixture.service")
    assert calls == [
        (
            (
                "systemctl",
                "--system",
                "--no-ask-password",
                "reset-failed",
                "gcapeps-fm-reset-fixture.service",
            ),
            30.0,
        )
    ]


def test_absolute_deadline_hook_is_bound_to_failure_barrier(tmp_path):
    module = _load_module()

    class _DeadlineManager:
        ready = False

        def show(self, unit_name, properties):
            assert tuple(properties) == module._UNIT_BARRIER_PROPERTIES
            return {
                "MainPID": "0",
                "ControlPID": "6161" if self.ready else "0",
                "ControlGroup": f"/fake.slice/{unit_name}",
                "Result": "resources" if self.ready else "",
                "ExecMainCode": "killed" if self.ready else "",
                "ExecMainStatus": "9" if self.ready else "",
                "InvocationID": "c" * 32 if self.ready else "",
            }

    manager = _DeadlineManager()
    observations = []

    def hook(client, unit_name):
        assert client is manager
        manager.ready = True
        observation = module.ManagerCommandObservation(
            command=("deadline-kill", unit_name),
            returncode=0,
            stdout=b"",
            stderr=b"",
        )
        observations.append(observation)
        return observation

    cgroup_root = tmp_path / "cgroup"
    cgroup_root.mkdir()
    proc_root = tmp_path / "proc"
    proc_root.mkdir()
    result = module._wait_for_unit_barrier(
        manager,
        "gcapeps-fm-deadline-fixture.service",
        selected_cpu=module.select_benchmark_cpu(),
        cgroup_root=cgroup_root,
        proc_root=proc_root,
        timeout_seconds=1.0,
        absolute_deadline_ns=1,
        deadline_kill_hook=hook,
        monotonic_ns=lambda: 2,
    )
    assert result.kind == "failure_helper"
    assert result.deadline_kill_observation is observations[0]
    assert result.show["Result"] == "resources"
