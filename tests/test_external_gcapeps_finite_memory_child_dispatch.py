from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import time
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT
    / "scripts"
    / "external_baselines"
    / "run_gcapeps_finite_memory_bond32.py"
)


def _load_module():
    name = "gcapeps_finite_memory_child_dispatch"
    spec = importlib.util.spec_from_file_location(name, MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _input_identity(module, *, partition, role):
    return {
        "byte_length": 0,
        "sha256": module.sha256_hex(b""),
        "ordered_entries": [
            {"name": name, "source_sha256": "0" * 64}
            for name in module.expected_entry_sequence(partition, role)
        ],
    }


def _fake_result(module, *, schema, marker):
    core = module.with_result_projection(
        {"schema": schema, "dispatch_marker": marker}
    )
    core_bytes = module.canonical_json_bytes(core)
    timer = module._TIMING.LayeredTimer()
    with timer.span(
        f"{marker}.root",
        scope="test_dispatch_worker_total",
        kind="test_owner",
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


def _completed_node(module, *, name, partition, role):
    result = _fake_result(
        module,
        schema=module.ROLE_CORE_SCHEMAS[role],
        marker=name,
    )
    launch_id = name.replace("_", "-")
    node = module.build_node_terminal(
        launch_id=launch_id,
        run_partition=partition,
        role=role,
        terminal_kind="completed_result",
        input_transport=_input_identity(
            module,
            partition=partition,
            role=role,
        ),
        core=result["core"],
        trailer=module.parse_canonical_json_object(result["trailer_bytes"]),
        raw_stdout=module.RawFileIdentity.from_bytes(
            result["framed_bytes"]
        ).as_dict(),
        raw_stderr=module.RawFileIdentity.from_bytes(b"").as_dict(),
        unit_facts={},
        cgroup_barrier={},
        exit_facts={},
        failure_snapshot=None,
        final_systemd_memory_peak_bytes=1,
        cleanup=module.completed_cleanup_facts(deadline_ns=30_000_000_000),
        quarantine=module.completed_quarantine_facts(
            relative_path=f"raw_spools/{launch_id}"
        ),
    )
    return node, module.canonical_json_bytes(node)


def _published_identity(module, raw, *, path):
    return module.PublishedFileIdentity(
        path=str(path),
        byte_length=len(raw),
        sha256=module.sha256_hex(raw),
        st_dev=1,
        st_ino=2,
        st_mode=stat.S_IFREG | 0o644,
        st_nlink=1,
    )


def _completed_artifacts(module, *, partition, role):
    envelope_roles = {
        "sdim_inventory_envelope": (
            module.BOOTSTRAP,
            module.SDIM_INVENTORY_COLLECTOR,
        ),
        "neutral_fixture_envelope": (
            partition,
            module.NEUTRAL_FIXTURE_EMITTER,
        ),
        "dense_envelope": (partition, module.DENSE_REFERENCE),
        "plain_input1_envelope": (partition, module.PLAIN_EVIDENCE),
        "plain_input2_envelope": (partition, module.PLAIN_EVIDENCE),
        "gc_input1_envelope": (partition, module.GCAPEPS_EVIDENCE),
        "gc_input2_envelope": (partition, module.GCAPEPS_EVIDENCE),
        "sdim_envelope": (partition, module.SDIM_COMPUTATION),
    }
    receipt_envelopes = {
        "sdim_inventory_launch_receipt": "sdim_inventory_envelope",
        "neutral_fixture_launch_receipt": "neutral_fixture_envelope",
        "dense_launch_receipt": "dense_envelope",
        "plain_input1_launch_receipt": "plain_input1_envelope",
        "plain_input2_launch_receipt": "plain_input2_envelope",
        "gc_input1_launch_receipt": "gc_input1_envelope",
        "gc_input2_launch_receipt": "gc_input2_envelope",
        "sdim_launch_receipt": "sdim_envelope",
    }
    cached = {}
    artifacts = []
    for name in module.expected_entry_sequence(partition, role):
        if name == "manager_preflight_receipt":
            payload = module.with_result_projection(
                {
                    "schema": module.MANAGER_PREFLIGHT_RECEIPT_SCHEMA,
                    "selected_scope": "system",
                }
            )
            artifacts.append(
                module.TransportArtifact.from_payload(
                    name=name,
                    schema=module.MANAGER_PREFLIGHT_RECEIPT_SCHEMA,
                    payload=payload,
                )
            )
            continue
        if name == "target_amendment":
            payload = module.with_result_projection(
                {
                    "schema": module.TARGET_AMENDMENT_SCHEMA,
                    "amendment_identity": "test-heldout",
                }
            )
            artifacts.append(
                module.TransportArtifact.from_payload(
                    name=name,
                    schema=module.TARGET_AMENDMENT_SCHEMA,
                    payload=payload,
                )
            )
            continue
        if name in envelope_roles:
            node_partition, node_role = envelope_roles[name]
            node, raw = _completed_node(
                module,
                name=name,
                partition=node_partition,
                role=node_role,
            )
            cached[name] = (node, raw)
            artifacts.append(
                module.TransportArtifact.from_payload(
                    name=name,
                    schema=module.NODE_TERMINAL_SCHEMA,
                    payload=node,
                )
            )
            continue
        envelope_name = receipt_envelopes[name]
        node, raw = cached[envelope_name]
        node_partition, node_role = envelope_roles[envelope_name]
        path = Path(f"/tmp/{envelope_name}.json")
        receipt = module.build_launch_receipt(
            launch_id=node["launch_id"],
            run_partition=node_partition,
            role=node_role,
            node_terminal_path=path,
            node_terminal_identity=_published_identity(
                module,
                raw,
                path=path,
            ),
            terminal_kind="completed_result",
            cleanup=node["cleanup"],
            quarantine=node["quarantine"],
            supervisor_launch_wall_ns=1,
        )
        artifacts.append(
            module.TransportArtifact.from_payload(
                name=name,
                schema=module.LAUNCH_RECEIPT_SCHEMA,
                payload=receipt,
            )
        )
    return tuple(artifacts)


def _calibration_parameters(module, role):
    common = {"gamma_index": 0, "rounds_index": 0, "seed": 0}
    if role == module.NEUTRAL_FIXTURE_EMITTER:
        return {
            "width": 7,
            "rounds": 4,
            "axis_family": 3,
            "p_event_numerator": 3,
            "p_event_denominator": 4,
            "seed": 0,
            "gamma_index": 0,
            "rounds_index": 0,
            "run_blpensemble": False,
        }
    if role == module.DENSE_REFERENCE:
        return {**common, "calibration_stage": "A"}
    if role == module.PLAIN_CAP_PROBE:
        return {
            **common,
            "calibration_stage": "B",
            "input_id": 1,
            "attempt_ordinal": 1,
        }
    if role == module.GCAPEPS_CAP_PROBE:
        return {
            **common,
            "calibration_stage": "C",
            "input_id": 1,
            "attempt_ordinal": 1,
        }
    if role in {module.PLAIN_EVIDENCE, module.GCAPEPS_EVIDENCE}:
        return {**common, "calibration_stage": "D", "input_id": 1}
    return {**common, "calibration_stage": "D"}


def _prepare(module, tmp_path, *, partition, role, parameters, ordinal):
    raw = module.build_input_transport(
        run_partition=partition,
        role=role,
        role_parameters=parameters,
        artifacts=_completed_artifacts(
            module,
            partition=partition,
            role=role,
        ),
    )
    path = tmp_path / f"fixture-{ordinal}.stdin"
    path.write_bytes(raw)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        return module.prepare_child_dispatch(
            [role, f"dispatch-{ordinal}"],
            stdin_fd=fd,
        )
    finally:
        os.close(fd)


def _sacrificial_parameters(module, tmp_path):
    output = (tmp_path / "sacrificial-output").absolute()
    output.mkdir(mode=0o755, exist_ok=True)
    evaluator = output / "evaluator-probe.bin"
    prior_spool = output / "prior-spool-probe.bin"
    evaluator.write_bytes(b"evaluator")
    prior_spool.write_bytes(b"prior-spool")
    pid = os.getpid()
    return {
        "runner_pid": pid,
        "runner_start_time_ticks": module._proc_start_time(pid),
        "runner_real_uid": os.getuid(),
        "runner_real_gid": os.getgid(),
        "runner_namespace_identity": (
            module.capture_process_namespace_identity(pid)
        ),
        "selected_cpu": module.select_benchmark_cpu(),
        "output_root_abs": str(output),
        "evaluator_probe_abs": str(evaluator),
        "quarantined_spool_probe_abs": str(prior_spool),
    }


def _denied_sacrificial_probes(module, parameters):
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
    return [
        {"probe": probe, "target": target, "outcome": "denied", "errno": 13}
        for probe, target in zip(module._SACRIFICIAL_ATTACK_PROBES, targets)
    ]


def _fake_owner(module, request, calls):
    role = request.role

    def result(marker):
        calls.append((role, marker))
        return _fake_result(
            module,
            schema=request.expected_core_schema,
            marker=marker,
        )

    if role == module.SDIM_INVENTORY_COLLECTOR:
        return SimpleNamespace(run_inventory_worker=lambda: result("inventory"))
    if role == module.NEUTRAL_FIXTURE_EMITTER:
        def build_fixture(**parameters):
            calls.append((role, dict(parameters)))
            return module.with_result_projection(
                {
                    "schema": module.FIXTURE_SCHEMA,
                    "dispatch_marker": "fixture",
                }
            )

        return SimpleNamespace(
            build_fixture=build_fixture,
            validate_fixture=lambda fixture: fixture[
                "result_projection_sha256"
            ],
        )
    if role == module.DENSE_REFERENCE:
        return SimpleNamespace(
            build_framed_worker_output=lambda fixture: result("dense")[
                "framed_bytes"
            ]
        )
    if role in {module.PLAIN_CAP_PROBE, module.GCAPEPS_CAP_PROBE}:
        return SimpleNamespace(
            run_cap_probe=lambda fixture, input_id: result(
                f"probe-{input_id}"
            )
        )
    if role in {module.PLAIN_EVIDENCE, module.GCAPEPS_EVIDENCE}:
        return SimpleNamespace(
            run_evidence=lambda fixture, input_id: result(
                f"evidence-{input_id}"
            )
        )
    if role in {module.PLAIN_PERFORMANCE, module.GCAPEPS_PERFORMANCE}:
        return SimpleNamespace(
            run_performance=lambda fixture, input_id: result(
                f"performance-{input_id}"
            )
        )
    if role == module.SDIM_COMPUTATION:
        return SimpleNamespace(
            run_frame_control_worker=lambda fixture, inventory_core: result(
                "sdim"
            )
        )
    if role == module.TERMINAL_COMPARATOR:
        def run_comparator_worker(*, timing_module, **inputs):
            assert timing_module is module._TIMING
            assert set(inputs) == {
                "fixture",
                "dense_core",
                "plain_input1_core",
                "plain_input2_core",
                "gcapeps_input1_core",
                "gcapeps_input2_core",
                "sdim_core",
            }
            return result("comparator")

        return SimpleNamespace(run_comparator_worker=run_comparator_worker)
    raise AssertionError(f"missing fake owner for {role}")


def test_sacrificial_preflight_uses_builtin_observation_owner(tmp_path):
    module = _load_module()
    prepared = _prepare(
        module,
        tmp_path,
        partition=module.BOOTSTRAP,
        role=module.SACRIFICIAL_MANAGER_PREFLIGHT,
        parameters=_sacrificial_parameters(module, tmp_path),
        ordinal=999,
    )

    def forbidden_loader(request):
        raise AssertionError("sacrificial owner must not recursively import")

    result = module.invoke_prepared_dispatch(
        prepared,
        owner_loader=forbidden_loader,
        sacrificial_probe_runner=lambda parameters: _denied_sacrificial_probes(
            module, parameters
        ),
    )
    assert result.core["schema"] == module.SACRIFICIAL_PREFLIGHT_SCHEMA
    assert result.core["status"] == "observed"
    module.validate_sacrificial_preflight_core(result.core)
    assert module.decode_clean_worker_frames(
        result.framed_bytes,
        role=module.SACRIFICIAL_MANAGER_PREFLIGHT,
    ).core == result.core


def test_in_process_dispatch_covers_every_nonmanager_owner_role(tmp_path):
    module = _load_module()
    calibration_roles = (
        module.SDIM_INVENTORY_COLLECTOR,
        module.NEUTRAL_FIXTURE_EMITTER,
        module.DENSE_REFERENCE,
        module.PLAIN_CAP_PROBE,
        module.GCAPEPS_CAP_PROBE,
        module.PLAIN_EVIDENCE,
        module.GCAPEPS_EVIDENCE,
        module.SDIM_COMPUTATION,
        module.TERMINAL_COMPARATOR,
    )
    cases = []
    for role in calibration_roles:
        partition = (
            module.BOOTSTRAP
            if role == module.SDIM_INVENTORY_COLLECTOR
            else module.CALIBRATION
        )
        parameters = (
            {}
            if partition == module.BOOTSTRAP
            else _calibration_parameters(module, role)
        )
        cases.append((partition, role, parameters))
    for role in (module.PLAIN_PERFORMANCE, module.GCAPEPS_PERFORMANCE):
        cases.append(
            (
                module.HELDOUT,
                role,
                {
                    "heldout_cell_index": 0,
                    "input_id": 1,
                    "sample_kind": "measured",
                    "sample_index": 0,
                },
            )
        )

    calls = []
    for ordinal, (partition, role, parameters) in enumerate(cases):
        prepared = _prepare(
            module,
            tmp_path,
            partition=partition,
            role=role,
            parameters=parameters,
            ordinal=ordinal,
        )
        result = module.invoke_prepared_dispatch(
            prepared,
            owner_loader=lambda request: _fake_owner(
                module,
                request,
                calls,
            ),
        )
        assert result.core["schema"] == module.ROLE_CORE_SCHEMAS[role]
        assert module.decode_clean_worker_frames(
            result.framed_bytes,
            role=role,
        ).core == result.core
    assert len(calls) == len(cases)


def test_emitter_fsyncs_exact_frames_before_requesting_sigstop(tmp_path):
    module = _load_module()
    request = module.parse_dispatch_argv(
        [module.PLAIN_EVIDENCE, "emit-test-1"]
    )
    result = module._normalize_dispatch_result(
        request,
        _fake_result(
            module,
            schema=module.PLAIN_EVIDENCE_SCHEMA,
            marker="emit",
        ),
    )
    path = tmp_path / "raw.stdout"
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
    stops = []
    try:
        module.emit_dispatch_result_and_self_stop(
            result,
            stdout_fd=fd,
            process_id=123,
            stop_process=lambda pid, sig: stops.append((pid, sig)),
        )
        assert os.pread(fd, len(result.framed_bytes), 0) == result.framed_bytes
    finally:
        os.close(fd)
    assert stops == [(123, signal.SIGSTOP)]


def test_fresh_fixture_dispatch_subprocess_frames_fsyncs_and_self_stops(tmp_path):
    module = _load_module()
    role = module.NEUTRAL_FIXTURE_EMITTER
    raw = module.build_input_transport(
        run_partition=module.CALIBRATION,
        role=role,
        role_parameters=_calibration_parameters(module, role),
        artifacts=_completed_artifacts(
            module,
            partition=module.CALIBRATION,
            role=role,
        ),
    )
    stdin_path = tmp_path / "fixture.stdin"
    stdin_path.write_bytes(raw)
    stdin_fd = os.open(stdin_path, os.O_RDONLY | os.O_NOFOLLOW)
    stdout_fd = os.open(
        tmp_path / "raw.stdout",
        os.O_RDWR | os.O_CREAT | os.O_EXCL,
        0o600,
    )
    stderr_fd = os.open(
        tmp_path / "raw.stderr",
        os.O_RDWR | os.O_CREAT | os.O_EXCL,
        0o600,
    )
    process = subprocess.Popen(
        [sys.executable, str(MODULE_PATH), role, "fixture-subprocess-1"],
        cwd=ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        stdin=stdin_fd,
        stdout=stdout_fd,
        stderr=stderr_fd,
        close_fds=True,
    )
    os.close(stdin_fd)
    stopped = False
    try:
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline:
            waited_pid, status = os.waitpid(
                process.pid,
                os.WNOHANG | os.WUNTRACED,
            )
            if waited_pid == 0:
                time.sleep(0.01)
                continue
            assert os.WIFSTOPPED(status), status
            assert os.WSTOPSIG(status) == signal.SIGSTOP
            stopped = True
            break
        assert stopped, "dispatcher did not reach the self-stop barrier"
        stdout_size = os.fstat(stdout_fd).st_size
        framed = os.pread(stdout_fd, stdout_size, 0)
        decoded = module.decode_clean_worker_frames(framed, role=role)
        assert decoded.core["schema"] == module.FIXTURE_SCHEMA
        assert decoded.core["geometry"]["width"] == 7
        assert os.fstat(stderr_fd).st_size == 0
        os.kill(process.pid, signal.SIGCONT)
        assert process.wait(timeout=10) == 0
    finally:
        if process.poll() is None:
            os.kill(process.pid, signal.SIGCONT)
            process.kill()
            process.wait(timeout=10)
        os.close(stdout_fd)
        os.close(stderr_fd)
