from __future__ import annotations

from dataclasses import replace
import importlib.util
import os
from pathlib import Path
import stat
import struct
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
    name = "gcapeps_finite_memory_supervisor_foundation"
    spec = importlib.util.spec_from_file_location(name, MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


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


def _input_identity(module, *, partition, role):
    return {
        "byte_length": 0,
        "sha256": module.sha256_hex(b""),
        "ordered_entries": [
            {
                "name": name,
                "source_sha256": "0" * 64,
            }
            for name in module.expected_entry_sequence(partition, role)
        ],
    }


def _raw_identity(module, raw=b""):
    return module.RawFileIdentity.from_bytes(raw).as_dict()


def _node_payload(module, *, partition, role, launch_id):
    return module.build_node_terminal(
        launch_id=launch_id,
        run_partition=partition,
        role=role,
        terminal_kind="supervisor_censor",
        input_transport=_input_identity(
            module,
            partition=partition,
            role=role,
        ),
        core=None,
        trailer=None,
        raw_stdout=_raw_identity(module),
        raw_stderr=_raw_identity(module),
        unit_facts=None,
        cgroup_barrier=None,
        exit_facts=None,
        failure_snapshot=None,
        final_systemd_memory_peak_bytes=None,
        cleanup=module.completed_cleanup_facts(deadline_ns=30_000_000_000),
        quarantine=module.completed_quarantine_facts(
            relative_path=f"raw_spools/{launch_id}",
        ),
    )


def _node_identity(module, raw, *, path):
    return module.PublishedFileIdentity(
        path=str(path),
        byte_length=len(raw),
        sha256=module.sha256_hex(raw),
        st_dev=1,
        st_ino=2,
        st_mode=stat.S_IFREG | 0o644,
        st_nlink=1,
    )


def _artifact_for_name(module, name, *, partition):
    if name == "manager_preflight_receipt":
        payload = module.with_result_projection(
            {
                "schema": module.MANAGER_PREFLIGHT_RECEIPT_SCHEMA,
                "selected_scope": "system",
            }
        )
        return module.TransportArtifact.from_payload(
            name=name,
            schema=module.MANAGER_PREFLIGHT_RECEIPT_SCHEMA,
            payload=payload,
        )
    if name == "target_amendment":
        payload = module.with_result_projection(
            {
                "schema": module.TARGET_AMENDMENT_SCHEMA,
                "amendment_identity": "fixture-bound",
            }
        )
        return module.TransportArtifact.from_payload(
            name=name,
            schema=module.TARGET_AMENDMENT_SCHEMA,
            payload=payload,
        )
    if name.startswith("sdim_inventory_"):
        artifact_partition = module.BOOTSTRAP
        role = module.SDIM_INVENTORY_COLLECTOR
    elif name.startswith("neutral_fixture_"):
        artifact_partition = partition
        role = module.NEUTRAL_FIXTURE_EMITTER
    elif name.startswith("dense_"):
        artifact_partition = partition
        role = module.DENSE_REFERENCE
    elif name.startswith("plain_input"):
        artifact_partition = partition
        role = module.PLAIN_EVIDENCE
    elif name.startswith("gc_input"):
        artifact_partition = partition
        role = module.GCAPEPS_EVIDENCE
    elif name.startswith("sdim_"):
        artifact_partition = partition
        role = module.SDIM_COMPUTATION
    else:
        raise AssertionError(f"test artifact mapping missing for {name}")
    receipt_to_envelope = {
        "sdim_inventory_launch_receipt": "sdim_inventory_envelope",
        "neutral_fixture_launch_receipt": "neutral_fixture_envelope",
        "dense_launch_receipt": "dense_envelope",
        "plain_input1_launch_receipt": "plain_input1_envelope",
        "plain_input2_launch_receipt": "plain_input2_envelope",
        "gc_input1_launch_receipt": "gc_input1_envelope",
        "gc_input2_launch_receipt": "gc_input2_envelope",
        "sdim_launch_receipt": "sdim_envelope",
    }
    envelope_name = receipt_to_envelope.get(name, name)
    launch_id = envelope_name.replace("_", "-")[:80]
    node = _node_payload(
        module,
        partition=artifact_partition,
        role=role,
        launch_id=launch_id,
    )
    node_raw = module.canonical_json_bytes(node)
    if name.endswith("_launch_receipt"):
        receipt = module.build_launch_receipt(
            launch_id=launch_id,
            run_partition=artifact_partition,
            role=role,
            node_terminal_path=Path(f"/tmp/{envelope_name}.json"),
            node_terminal_identity=_node_identity(
                module,
                node_raw,
                path=Path(f"/tmp/{envelope_name}.json"),
            ),
            terminal_kind="supervisor_censor",
            cleanup=node["cleanup"],
            quarantine=node["quarantine"],
            supervisor_launch_wall_ns=1,
        )
        return module.TransportArtifact.from_payload(
            name=name,
            schema=module.LAUNCH_RECEIPT_SCHEMA,
            payload=receipt,
        )
    return module.TransportArtifact.from_payload(
        name=name,
        schema=module.NODE_TERMINAL_SCHEMA,
        payload=node,
    )


def _artifacts(module, *, partition, role):
    return tuple(
        _artifact_for_name(module, name, partition=partition)
        for name in module.expected_entry_sequence(partition, role)
    )


def _cal_evidence_parameters(module, *, input_id=1):
    return {
        "gamma_index": 1,
        "rounds_index": 2,
        "seed": 3,
        "calibration_stage": "D",
        "input_id": input_id,
    }


def test_input_transport_round_trip_preserves_exact_order_and_source_bytes():
    module = _load_module()
    artifacts = _artifacts(
        module,
        partition=module.CALIBRATION,
        role=module.PLAIN_EVIDENCE,
    )
    raw = module.build_input_transport(
        run_partition=module.CALIBRATION,
        role=module.PLAIN_EVIDENCE,
        role_parameters=_cal_evidence_parameters(module),
        artifacts=artifacts,
    )
    parsed = module.parse_input_transport(
        raw,
        expected_partition=module.CALIBRATION,
        expected_role=module.PLAIN_EVIDENCE,
        external_source_sha256={
            artifact.name: artifact.external_complete_file_sha256
            for artifact in artifacts
        },
    )
    assert tuple(name for name, _ in parsed.artifacts) == module.B_CAL
    assert tuple(data for _, data in parsed.artifacts) == tuple(
        artifact.raw_bytes for artifact in artifacts
    )
    assert parsed.raw_sha256 == module.sha256_hex(raw)
    assert parsed.identity()["ordered_entries"] == [
        {
            "name": artifact.name,
            "source_sha256": artifact.external_complete_file_sha256,
        }
        for artifact in artifacts
    ]


def test_heldout_comparator_gets_exact_cross_role_sequence_and_bound_receipts():
    module = _load_module()
    artifacts = _artifacts(
        module,
        partition=module.HELDOUT,
        role=module.TERMINAL_COMPARATOR,
    )
    raw = module.build_input_transport(
        run_partition=module.HELDOUT,
        role=module.TERMINAL_COMPARATOR,
        role_parameters={"heldout_cell_index": 4},
        artifacts=artifacts,
    )
    parsed = module.parse_input_transport(raw)
    assert tuple(name for name, _ in parsed.artifacts) == module.B_HELD + module.X

    corrupted = list(artifacts)
    receipt_index = next(
        index
        for index, artifact in enumerate(corrupted)
        if artifact.name == "neutral_fixture_launch_receipt"
    )
    receipt = module.parse_canonical_json_object(
        corrupted[receipt_index].raw_bytes
    )
    receipt["node_terminal_complete_file_sha256"] = "f" * 64
    receipt["result_projection_sha256"] = module._projection_sha256(receipt)
    corrupted[receipt_index] = module.TransportArtifact.from_payload(
        name="neutral_fixture_launch_receipt",
        schema=module.LAUNCH_RECEIPT_SCHEMA,
        payload=receipt,
    )
    with pytest.raises(ValueError, match="envelope SHA-256"):
        module.build_input_transport(
            run_partition=module.HELDOUT,
            role=module.TERMINAL_COMPARATOR,
            role_parameters={"heldout_cell_index": 4},
            artifacts=corrupted,
        )


def test_transport_rejects_sequence_role_and_parameter_widening():
    module = _load_module()
    artifacts = _artifacts(
        module,
        partition=module.CALIBRATION,
        role=module.PLAIN_EVIDENCE,
    )
    with pytest.raises(ValueError, match="sequence"):
        module.build_input_transport(
            run_partition=module.CALIBRATION,
            role=module.PLAIN_EVIDENCE,
            role_parameters=_cal_evidence_parameters(module),
            artifacts=tuple(reversed(artifacts)),
        )
    widened = _cal_evidence_parameters(module)
    widened["dense_path"] = "/forbidden"
    with pytest.raises(ValueError, match="key set"):
        module.build_input_transport(
            run_partition=module.CALIBRATION,
            role=module.PLAIN_EVIDENCE,
            role_parameters=widened,
            artifacts=artifacts,
        )
    with pytest.raises(ValueError, match="forbidden"):
        module.expected_entry_sequence(
            module.CALIBRATION,
            module.PLAIN_PERFORMANCE,
        )
    with pytest.raises(ValueError, match="only for input 1"):
        module.validate_role_parameters(
            module.HELDOUT,
            module.GCAPEPS_PERFORMANCE,
            {
                "heldout_cell_index": 0,
                "input_id": 2,
                "sample_kind": "measured",
                "sample_index": 0,
            },
        )


def test_transport_rejects_noncanonical_oversize_hash_and_trailing_bytes():
    module = _load_module()
    artifacts = _artifacts(
        module,
        partition=module.BOOTSTRAP,
        role=module.SDIM_INVENTORY_COLLECTOR,
    )
    raw = module.build_input_transport(
        run_partition=module.BOOTSTRAP,
        role=module.SDIM_INVENTORY_COLLECTOR,
        role_parameters={},
        artifacts=artifacts,
    )
    manifest_size = struct.unpack(">Q", raw[:8])[0]
    manifest_raw = raw[8 : 8 + manifest_size]
    manifest = module.parse_canonical_json_object(manifest_raw)
    noncanonical = (
        __import__("json").dumps(manifest, indent=2).encode("utf-8")
    )
    rest = raw[8 + manifest_size :]
    with pytest.raises(ValueError, match="canonical"):
        module.parse_input_transport(
            struct.pack(">Q", len(noncanonical)) + noncanonical + rest,
        )
    with pytest.raises(ValueError, match="manifest exceeds"):
        module.parse_input_transport(
            struct.pack(">Q", module.MANIFEST_MAX_BYTES + 1),
        )
    with pytest.raises(ValueError, match="trailing"):
        module.parse_input_transport(raw + b"x")
    broken = bytearray(raw)
    broken[-1] ^= 1
    with pytest.raises(ValueError, match="SHA-256"):
        module.parse_input_transport(bytes(broken))


def test_transport_fd_preflights_size_and_round_trips(tmp_path):
    module = _load_module()
    raw = module.build_input_transport(
        run_partition=module.BOOTSTRAP,
        role=module.SACRIFICIAL_MANAGER_PREFLIGHT,
        role_parameters=_sacrificial_parameters(module, tmp_path),
        artifacts=(),
    )
    path = tmp_path / "fixture.stdin"
    path.write_bytes(raw)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        parsed = module.read_input_transport_fd(
            fd,
            expected_partition=module.BOOTSTRAP,
            expected_role=module.SACRIFICIAL_MANAGER_PREFLIGHT,
        )
    finally:
        os.close(fd)
    assert parsed.raw_sha256 == module.sha256_hex(raw)


def test_transport_fd_rejects_sparse_oversize_before_payload_read(tmp_path):
    module = _load_module()
    path = tmp_path / "oversize.stdin"
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.ftruncate(fd, module.ORDINARY_STDIN_MAX_BYTES + 1)
        with pytest.raises(ValueError, match="outside its cap"):
            module.read_input_transport_fd(
                fd,
                expected_partition=module.BOOTSTRAP,
                expected_role=module.SACRIFICIAL_MANAGER_PREFLIGHT,
            )
    finally:
        os.close(fd)


def test_node_and_launch_receipt_reject_self_digest_and_schema_drift():
    module = _load_module()
    node = _node_payload(
        module,
        partition=module.BOOTSTRAP,
        role=module.SDIM_INVENTORY_COLLECTOR,
        launch_id="inventory-1",
    )
    corrupted_node = dict(node)
    corrupted_node["complete_file_sha256"] = "0" * 64
    corrupted_node["result_projection_sha256"] = module._projection_sha256(
        corrupted_node
    )
    with pytest.raises(ValueError, match="key set"):
        module.validate_node_terminal(corrupted_node)

    node_raw = module.canonical_json_bytes(node)
    receipt = module.build_launch_receipt(
        launch_id="inventory-1",
        run_partition=module.BOOTSTRAP,
        role=module.SDIM_INVENTORY_COLLECTOR,
        node_terminal_path=Path("/tmp/inventory.json"),
        node_terminal_identity=_node_identity(
            module,
            node_raw,
            path=Path("/tmp/inventory.json"),
        ),
        terminal_kind="supervisor_censor",
        cleanup=node["cleanup"],
        quarantine=node["quarantine"],
        supervisor_launch_wall_ns=10,
    )
    corrupted_receipt = dict(receipt)
    corrupted_receipt["launch_receipt_complete_file_sha256"] = "1" * 64
    corrupted_receipt["result_projection_sha256"] = module._projection_sha256(
        corrupted_receipt
    )
    with pytest.raises(ValueError, match="key set"):
        module.validate_launch_receipt(corrupted_receipt)


def test_two_frame_decoder_uses_role_caps_and_rejects_trailing_or_bad_binding(
    tmp_path,
):
    module = _load_module()
    core = module.with_result_projection(
        {
            "schema": module.PLAIN_PERFORMANCE_SCHEMA,
            "status": "completed",
        }
    )
    core_raw = module.canonical_json_bytes(core)
    timer = module._TIMING.LayeredTimer()
    with timer.span(
        "root",
        scope="performance_worker_total",
        kind="worker",
        lane="plain",
    ):
        pass
    trailer_raw = module._TIMING.build_late_telemetry_trailer(
        core_raw,
        timer.finish(),
    )
    framed = module._TIMING.encode_two_frames(core_raw, trailer_raw)
    decoded = module.decode_clean_worker_frames(
        framed,
        role=module.PLAIN_PERFORMANCE,
    )
    assert decoded.core == core
    with pytest.raises(ValueError, match="trailing"):
        module.decode_clean_worker_frames(
            framed + b"x",
            role=module.PLAIN_PERFORMANCE,
        )
    with pytest.raises(ValueError, match="core frame exceeds"):
        module.decode_clean_worker_frames(
            struct.pack(">Q", module._OTHER_CORE_MAX + 1) + b"\0" * 8,
            role=module.PLAIN_PERFORMANCE,
        )
    trailer = module.parse_canonical_json_object(trailer_raw)
    trailer["core_sha256"] = "0" * 64
    bad_trailer = module.canonical_json_bytes(trailer)
    with pytest.raises(ValueError, match="core SHA-256"):
        module.decode_clean_worker_frames(
            module._TIMING.encode_two_frames(core_raw, bad_trailer),
            role=module.PLAIN_PERFORMANCE,
        )

    path = tmp_path / "raw.stdout"
    path.write_bytes(framed)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        assert (
            module.read_clean_worker_frames_fd(
                fd,
                role=module.PLAIN_PERFORMANCE,
            ).core
            == core
        )
    finally:
        os.close(fd)


def test_completed_node_terminal_binds_exact_framed_stdout():
    module = _load_module()
    core = module.with_result_projection(
        {"schema": module.PLAIN_PERFORMANCE_SCHEMA, "status": "completed"}
    )
    core_raw = module.canonical_json_bytes(core)
    timer = module._TIMING.LayeredTimer()
    with timer.span(
        "root",
        scope="performance_worker_total",
        kind="worker",
        lane="plain",
    ):
        pass
    trailer_raw = module._TIMING.build_late_telemetry_trailer(
        core_raw,
        timer.finish(),
    )
    trailer = module.parse_canonical_json_object(trailer_raw)
    framed = module._TIMING.encode_two_frames(core_raw, trailer_raw)
    node = module.build_node_terminal(
        launch_id="plain-performance-1",
        run_partition=module.HELDOUT,
        role=module.PLAIN_PERFORMANCE,
        terminal_kind="completed_result",
        input_transport=_input_identity(
            module,
            partition=module.HELDOUT,
            role=module.PLAIN_PERFORMANCE,
        ),
        core=core,
        trailer=trailer,
        raw_stdout=_raw_identity(module, framed),
        raw_stderr=_raw_identity(module),
        unit_facts={},
        cgroup_barrier={},
        exit_facts={},
        failure_snapshot=None,
        final_systemd_memory_peak_bytes=1,
        cleanup=module.completed_cleanup_facts(deadline_ns=30_000_000_000),
        quarantine=module.completed_quarantine_facts(
            relative_path="raw_spools/plain-performance-1"
        ),
    )
    assert node["raw_stdout"]["sha256"] == module.sha256_hex(framed)


def test_atomic_publication_is_mode_0644_noreplace_and_symlink_safe(tmp_path):
    module = _load_module()
    payload = module.with_result_projection(
        {"schema": "test.publication.v1", "value": 7}
    )
    destination = (tmp_path / "artifact.json").absolute()
    identity = module.publish_canonical_json_noreplace(destination, payload)
    assert destination.read_bytes() == module.canonical_json_bytes(payload)
    assert stat.S_IMODE(destination.stat().st_mode) == 0o644
    assert destination.stat().st_ino == identity.st_ino
    with pytest.raises(FileExistsError):
        module.publish_canonical_json_noreplace(destination, payload)
    assert destination.read_bytes() == module.canonical_json_bytes(payload)
    assert not any(
        path.name.startswith(".artifact.json.tmp-")
        for path in tmp_path.iterdir()
    )

    target = tmp_path / "target.json"
    target.write_bytes(b"untouched")
    symlink = tmp_path / "symlink.json"
    symlink.symlink_to(target)
    with pytest.raises(FileExistsError):
        module.publish_canonical_json_noreplace(
            symlink.absolute(),
            payload,
        )
    assert symlink.is_symlink()
    assert target.read_bytes() == b"untouched"


def test_atomic_publication_preserves_destination_if_wrapper_raises_after_move(
    tmp_path,
    monkeypatch,
):
    module = _load_module()
    payload = module.with_result_projection(
        {"schema": "test.publication.v1", "value": 9}
    )
    expected = module.canonical_json_bytes(payload)
    destination = (tmp_path / "post-move.json").absolute()

    def move_then_raise(oldfd, oldname, newfd, newname, flags):
        assert flags == module._RENAME_NOREPLACE
        os.rename(
            os.fsdecode(oldname),
            os.fsdecode(newname),
            src_dir_fd=oldfd,
            dst_dir_fd=newfd,
        )
        raise RuntimeError("injected post-move wrapper failure")

    monkeypatch.setattr(module, "_renameat2", move_then_raise)
    with pytest.raises(RuntimeError, match="post-move"):
        module.publish_canonical_json_noreplace(destination, payload)
    assert destination.read_bytes() == expected
    assert not any(
        path.name.startswith(".post-move.json.tmp-")
        for path in tmp_path.iterdir()
    )


def test_published_source_artifact_is_reopened_and_reauthenticated(tmp_path):
    module = _load_module()
    payload = module.with_result_projection(
        {
            "schema": module.MANAGER_PREFLIGHT_RECEIPT_SCHEMA,
            "selected_scope": "system",
        }
    )
    destination = (tmp_path / "manager-preflight.json").absolute()
    identity = module.publish_canonical_json_noreplace(destination, payload)
    artifact = module.transport_artifact_from_published_file(
        name="manager_preflight_receipt",
        identity=identity,
    )
    assert artifact.raw_bytes == module.canonical_json_bytes(payload)
    assert artifact.external_complete_file_sha256 == identity.sha256

    with pytest.raises(ValueError, match="SHA-256 drifted"):
        module.transport_artifact_from_published_file(
            name="manager_preflight_receipt",
            identity=replace(identity, sha256="0" * 64),
        )

    symlink = (tmp_path / "manager-preflight-link.json").absolute()
    symlink.symlink_to(destination)
    with pytest.raises(OSError):
        module.transport_artifact_from_published_file(
            name="manager_preflight_receipt",
            identity=replace(identity, path=str(symlink)),
        )


def test_prctl_wrapper_sets_then_verifies_and_binds_proc_start(tmp_path):
    module = _load_module()
    pid = os.getpid()
    proc_dir = tmp_path / str(pid)
    proc_dir.mkdir(parents=True)
    fields_3_through_22 = ["S"] + ["1"] * 18 + ["123456"]
    (proc_dir / "stat").write_text(
        f"{pid} (test worker) " + " ".join(fields_3_through_22) + "\n",
        encoding="ascii",
    )
    calls = []

    def fake_prctl(option, arg2, arg3, arg4, arg5):
        calls.append((option, arg2, arg3, arg4, arg5))
        return 0

    identity = module.set_runner_nondumpable(
        prctl_call=fake_prctl,
        proc_root=tmp_path,
    )
    assert calls == [
        (module.PR_SET_DUMPABLE, 0, 0, 0, 0),
        (module.PR_GET_DUMPABLE, 0, 0, 0, 0),
    ]
    assert identity["proc_start_time_ticks"] == 123456
    assert identity["pr_get_dumpable"] == 0

    def still_dumpable(option, arg2, arg3, arg4, arg5):
        return 1 if option == module.PR_GET_DUMPABLE else 0

    with pytest.raises(RuntimeError, match="confirm zero"):
        module.set_runner_nondumpable(
            prctl_call=still_dumpable,
            proc_root=tmp_path,
        )


def test_pure_dispatch_parser_resolves_owner_and_authenticates_stdin(tmp_path):
    module = _load_module()
    request = module.parse_dispatch_argv(
        [module.PLAIN_EVIDENCE, "calibration-plain-evidence-1"]
    )
    assert request.role == module.PLAIN_EVIDENCE
    assert request.owner_path.name == (
        "plain_quimb_finite_memory_evidence_worker.py"
    )
    assert request.expected_core_schema == module.PLAIN_EVIDENCE_SCHEMA
    assert request.stdin_max_bytes == module.ORDINARY_STDIN_MAX_BYTES

    raw = module.build_input_transport(
        run_partition=module.BOOTSTRAP,
        role=module.SACRIFICIAL_MANAGER_PREFLIGHT,
        role_parameters=_sacrificial_parameters(module, tmp_path),
        artifacts=(),
    )
    path = tmp_path / "fixture.stdin"
    path.write_bytes(raw)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        prepared = module.prepare_child_dispatch(
            [module.SACRIFICIAL_MANAGER_PREFLIGHT, "manager-preflight-1"],
            stdin_fd=fd,
        )
    finally:
        os.close(fd)
    assert prepared.run_partition == module.BOOTSTRAP
    assert prepared.input_transport.raw_sha256 == module.sha256_hex(raw)
    assert prepared.request.owner_path == MODULE_PATH.resolve()

    for invalid in (
        [],
        [module.PLAIN_EVIDENCE],
        [module.PLAIN_EVIDENCE, "ok", "extra"],
        ["not-a-role", "valid-launch"],
        [module.PLAIN_EVIDENCE, "INVALID"],
    ):
        with pytest.raises(ValueError, match="dispatch"):
            module.parse_dispatch_argv(invalid)


def test_system_manager_builder_pins_noninteractive_security_and_resources(
    tmp_path,
):
    module = _load_module()
    common = {
        "launch_id": "heldout-node-0001",
        "repository_abs": ROOT,
        "run_output_abs": (tmp_path / "output").absolute(),
        "spool_abs": (tmp_path / "spool").absolute(),
        "selected_cpu": module.select_benchmark_cpu(),
        "repository_read_gid": os.getgid(),
        "python_executable": Path(sys.executable).resolve(),
        "worker_path": MODULE_PATH,
        "snapshot_helper_path": (
            ROOT
            / "scripts"
            / "external_baselines"
            / "gcapeps_finite_memory_systemd_snapshot.py"
        ),
    }
    performance = module.build_systemd_service_spec(
        role=module.PLAIN_PERFORMANCE,
        **common,
    )
    props = performance.property_map()
    assert performance.command[:4] == (
        "systemd-run",
        "--system",
        "--no-block",
        "--no-ask-password",
    )
    assert props["DynamicUser"] == "yes"
    assert props["PrivateUsers"] == "yes"
    assert props["CPUAffinity"] == str(module.select_benchmark_cpu())
    assert props["MemoryMax"] == "12884901888"
    assert props["TimeoutStartSec"] == "600s"
    assert props["RuntimeMaxSec"] == "infinity"
    assert props["RuntimeDirectoryMode"] == "0755"
    assert props["RuntimeDirectoryPreserve"] == "no"
    assert props["LimitCORE"] == "0"
    assert props["StandardInput"].endswith("/fixture.stdin")
    assert not {"--wait", "--pipe", "--collect", "--user"}.intersection(
        performance.command
    )

    evidence = module.build_systemd_service_spec(
        role=module.GCAPEPS_EVIDENCE,
        **common,
    )
    assert evidence.property_map()["MemoryMax"] == "25769803776"
    assert evidence.property_map()["TimeoutStartSec"] == "1800s"
    assert evidence.property_map()["LimitFSIZE"] == "285212688"
    assert evidence.command[-3] == str(MODULE_PATH.resolve())
    assert module.resolve_role_owner(module.GCAPEPS_EVIDENCE).name == (
        "gcapeps_finite_memory_evidence_worker.py"
    )

    direct_worker = dict(common)
    direct_worker["worker_path"] = (
        ROOT
        / "scripts"
        / "external_baselines"
        / "gcapeps_finite_memory_evidence_worker.py"
    )
    with pytest.raises(ValueError, match="supervisor dispatcher"):
        module.build_systemd_service_spec(
            role=module.GCAPEPS_EVIDENCE,
            **direct_worker,
        )

    altered = list(performance.properties)
    index = next(
        i for i, (name, _) in enumerate(altered) if name == "MemoryMax"
    )
    altered[index] = ("MemoryMax", "25769803776")
    with pytest.raises(ValueError, match="MemoryMax"):
        module.validate_systemd_service_spec(
            replace(performance, properties=tuple(altered))
        )
    with pytest.raises(ValueError, match="prefix"):
        module.validate_systemd_service_spec(
            replace(
                performance,
                command=("systemd-run", "--user") + performance.command[2:],
            )
        )


@pytest.mark.parametrize(
    "role",
    sorted(
        role
        for role in (
            "sdim_inventory_collector",
            "neutral_fixture_emitter",
            "dense_reference",
            "plain_cap_probe",
            "gcapeps_cap_probe",
            "plain_evidence",
            "gcapeps_evidence",
            "plain_performance",
            "gcapeps_performance",
            "sdim_computation",
            "terminal_comparator",
        )
    ),
)
def test_effective_property_gate_is_role_generic(role, tmp_path):
    module = _load_module()
    spec = module.build_systemd_service_spec(
        launch_id=f"role-generic-{role.replace('_', '-')}",
        role=role,
        repository_abs=ROOT,
        run_output_abs=(tmp_path / "output").absolute(),
        spool_abs=(tmp_path / "spool").absolute(),
        selected_cpu=module.select_benchmark_cpu(),
        repository_read_gid=os.getgid(),
        python_executable=Path(sys.executable).resolve(),
        worker_path=MODULE_PATH,
    )
    effective = module.expected_effective_systemd_properties(spec)
    module.validate_effective_systemd_properties(effective, spec)

    altered = dict(effective)
    altered["ReadOnlyPaths"] = str(tmp_path / "wrong-repository")
    with pytest.raises(ValueError, match="ReadOnlyPaths"):
        module.validate_effective_systemd_properties(altered, spec)

    altered = dict(effective)
    altered["ExecStopPost"] = altered["ExecStopPost"].replace(
        "ignore_errors=no", "ignore_errors=yes"
    )
    with pytest.raises(ValueError, match="ExecStopPost"):
        module.validate_effective_systemd_properties(altered, spec)
