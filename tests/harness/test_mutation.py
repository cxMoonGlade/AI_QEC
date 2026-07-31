"""CPU-only self-tests for mutation-result accounting."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import stat
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from harness import mutation


def test_also_copy_paths_include_src_and_registry_support_files() -> None:
    paths = mutation._also_copy_paths(
        {
            "mutation_also_copy": [
                "docs/service_status.json",
                "src",
                "scripts/mps_actual_split_diagnostic.py",
            ]
        }
    )

    assert paths == (
        "src",
        "docs/service_status.json",
        "scripts/mps_actual_split_diagnostic.py",
    )


@pytest.mark.parametrize(
    "value",
    ["docs/service_status.json", [""], ["../outside"], ["/tmp/outside"]],
)
def test_also_copy_paths_reject_malformed_or_escaping_entries(value: object) -> None:
    error_type = (
        TypeError
        if value == "docs/service_status.json" or value == [""]
        else ValueError
    )
    with pytest.raises(error_type, match="mutation_also_copy"):
        mutation._also_copy_paths({"mutation_also_copy": value})


def test_prepare_also_copy_destinations_creates_only_file_parents(
    tmp_path,
) -> None:
    support = tmp_path / "docs" / "service_status.json"
    support.parent.mkdir(parents=True)
    support.write_text("{}", encoding="utf-8")
    (tmp_path / "src").mkdir()

    mutation._prepare_also_copy_destinations(
        ("src", "docs/service_status.json"),
        repo=tmp_path,
    )

    assert (tmp_path / "mutants" / "docs").is_dir()
    assert not (tmp_path / "mutants" / "src").exists()


def test_parse_results_accounts_for_every_mutmut_status_exactly() -> None:
    rows = mutation.parse_mutmut_results(
        """
        pkg.mod.x_a__mutmut_1: killed
        pkg.mod.x_b__mutmut_1: survived
        pkg.mod.x_c__mutmut_1: timeout
        pkg.mod.x_d__mutmut_1: suspicious
        pkg.mod.x_e__mutmut_1: no tests
        pkg.mod.x_f__mutmut_1: skipped
        pkg.mod.x_g__mutmut_1: caught by type check
        pkg.mod.x_h__mutmut_1: check was interrupted by user
        pkg.mod.x_i__mutmut_1: not checked
        pkg.mod.x_j__mutmut_1: segfault
        """
    )

    assert rows == {
        "pkg.mod.x_a__mutmut_1": "killed",
        "pkg.mod.x_b__mutmut_1": "survived",
        "pkg.mod.x_c__mutmut_1": "timeout",
        "pkg.mod.x_d__mutmut_1": "suspicious",
        "pkg.mod.x_e__mutmut_1": "no_tests",
        "pkg.mod.x_f__mutmut_1": "skipped",
        "pkg.mod.x_g__mutmut_1": "caught_by_type_check",
        "pkg.mod.x_h__mutmut_1": "check_was_interrupted_by_user",
        "pkg.mod.x_i__mutmut_1": "not_checked",
        "pkg.mod.x_j__mutmut_1": "segfault",
    }


@pytest.mark.parametrize(
    "incomplete_status",
    ["not_checked", "check_was_interrupted_by_user"],
)
def test_score_batch_rejects_incomplete_mutation_execution(
    incomplete_status: str,
) -> None:
    rows = {
        "pkg.mod.x_a__mutmut_1": "killed",
        "pkg.mod.x_b__mutmut_1": incomplete_status,
    }

    with pytest.raises(ValueError, match="incomplete mutmut execution"):
        mutation.score_mutation_rows(
            rows,
            modules=("src/pkg/mod.py",),
            bar=0.50,
        )


def test_cpu_lane_hides_cuda_and_pins_nested_thread_pools() -> None:
    parent = {
        "KEEP": "yes",
        "CUDA_VISIBLE_DEVICES": "7",
        "ECS_GPU_SLOT": "7",
        "OMP_NUM_THREADS": "8",
        "MKL_NUM_THREADS": "8",
        "OPENBLAS_NUM_THREADS": "8",
        "NUMEXPR_NUM_THREADS": "8",
        "PYTHONPATH": "/untrusted",
    }

    child = mutation.lane_environment(parent, lane="cpu_parallel")

    assert child == {
        "KEEP": "yes",
        "CUDA_VISIBLE_DEVICES": "",
        "OMP_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1",
        "PYTHONNOUSERSITE": "1",
    }
    assert "PYTHONPATH" not in child
    assert parent["CUDA_VISIBLE_DEVICES"] == "7"
    assert parent["ECS_GPU_SLOT"] == "7"


def test_gpu_lane_preserves_lease_and_pins_each_fresh_child_to_one_host_thread() -> None:
    parent = {
        "CUDA_VISIBLE_DEVICES": "0",
        "ECS_GPU_SLOT": "0",
        "OMP_NUM_THREADS": "8",
        "PYTEST_ADDOPTS": "-n 8",
        "PYTEST_PLUGINS": "xdist.plugin",
        "PYTEST_XDIST_WORKER": "gw0",
        "PYTEST_XDIST_WORKER_COUNT": "8",
        "PYTEST_XDIST_TESTRUNUID": "run",
        "PYTHONPATH": "/untrusted",
        "KEEP": "yes",
    }

    child = mutation.lane_environment(parent, lane="gpu_serial")

    assert child["CUDA_VISIBLE_DEVICES"] == "0"
    assert child["ECS_GPU_SLOT"] == "0"
    assert child["PYTHONDONTWRITEBYTECODE"] == "1"
    for name in (
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        assert child[name] == "1"
    assert child["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
    assert child["PYTHONNOUSERSITE"] == "1"
    assert "PYTHONPATH" not in child
    for name in (
        "PYTEST_ADDOPTS",
        "PYTEST_PLUGINS",
        "PYTEST_XDIST_WORKER",
        "PYTEST_XDIST_WORKER_COUNT",
        "PYTEST_XDIST_TESTRUNUID",
    ):
        assert name not in child
    assert child["KEEP"] == "yes"
    assert parent["OMP_NUM_THREADS"] == "8"
    assert parent["PYTEST_ADDOPTS"] == "-n 8"
    assert "PYTHONDONTWRITEBYTECODE" not in parent


def test_cpu_lane_defaults_to_four_jobs_and_accepts_registry_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MUTMUT_JOBS", raising=False)

    assert mutation.resolve_jobs({}, lane="cpu_parallel", requested=None) == 4
    assert mutation.resolve_jobs(
        {"harness": {"mutation_gate": {"jobs": 6}}},
        lane="cpu_parallel",
        requested=None,
    ) == 6
    assert mutation.resolve_jobs({}, lane="cpu_parallel", requested=3) == 3


@pytest.mark.parametrize("jobs", [1, 2, 3, 4, 8, 16])
def test_gpu_lane_accepts_fresh_exec_workers_up_to_the_ceiling(jobs: int) -> None:
    assert mutation.resolve_jobs(
        {"harness": {"mutation_gate": {"jobs": jobs}}},
        lane="gpu_serial",
        requested=None,
    ) == jobs
    assert mutation.execution_policy(lane="gpu_serial", jobs=jobs) == {
        "lane": "gpu_serial",
        "jobs": jobs,
        "cuda_hidden": False,
        "stock_mutmut_worker_pool": False,
        "fresh_exec_per_tested_mutant": True,
        "max_concurrent_mutant_workers": jobs,
    }


@pytest.mark.parametrize("jobs", [17, 32])
def test_gpu_lane_rejects_more_workers_than_the_ceiling(jobs: int) -> None:
    ceiling = mutation._GPU_MAX_FRESH_WORKERS
    assert jobs > ceiling
    with pytest.raises(ValueError, match=f"at most {ceiling}"):
        mutation.resolve_jobs({}, lane="gpu_serial", requested=jobs)
    with pytest.raises(ValueError, match=f"at most {ceiling}"):
        mutation.execution_policy(lane="gpu_serial", jobs=jobs)


def test_gpu_execution_policy_requires_complete_bound_identity() -> None:
    env = mutation.lane_environment(
        {"CUDA_VISIBLE_DEVICES": "0", "ECS_GPU_SLOT": "0"},
        lane="gpu_serial",
    )
    policy = {
        **mutation.execution_policy(lane="gpu_serial", jobs=4),
        "timeout_multiplier": 15.0,
        "timeout_constant": 1.0,
        "explicit_timeout": None,
        "bound_environment": mutation._gpu_bound_environment(env),
        "device_identity": mutation._gpu_device_identity_document(
            slot=0,
            uuid="GPU-test",
            driver_version="test-driver",
        ),
    }

    assert mutation._validate_gpu_execution_policy(policy) == 4
    for key in (
        "max_concurrent_mutant_workers",
        "fresh_exec_per_tested_mutant",
        "bound_environment",
    ):
        broken = dict(policy)
        broken.pop(key)
        with pytest.raises((TypeError, ValueError), match="GPU execution policy"):
            mutation._validate_gpu_execution_policy(broken)

    drifted = json.loads(json.dumps(policy))
    drifted["bound_environment"]["values"]["CUDA_VISIBLE_DEVICES"] = "1"
    with pytest.raises(ValueError, match="bound environment digest"):
        mutation._validate_gpu_execution_policy(drifted)


def test_gpu_device_identity_probe_binds_slot_uuid_and_driver(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append(list(command))
        assert kwargs["timeout"] == 15.0
        return SimpleNamespace(
            returncode=0,
            stdout=(
                "0, GPU-aaaaaaaa, 580.65.06\n"
                "1, GPU-bbbbbbbb, 580.65.06\n"
            ),
            stderr="",
        )

    monkeypatch.setattr(mutation.subprocess, "run", fake_run)
    identity = mutation._gpu_device_identity(
        {"ECS_GPU_SLOT": "1", "CUDA_VISIBLE_DEVICES": "1"}
    )

    assert identity["slot"] == 1
    assert identity["uuid"] == "GPU-bbbbbbbb"
    assert identity["driver_version"] == "580.65.06"
    assert len(identity["sha256"]) == 64
    assert calls == [
        [
            "nvidia-smi",
            "--query-gpu=index,uuid,driver_version",
            "--format=csv,noheader,nounits",
        ]
    ]


def test_fresh_pytest_command_disables_shared_writes_and_uses_unique_basetemp(
    tmp_path: Path,
) -> None:
    first_sentinel = tmp_path / ".worker_1.json"
    second_sentinel = tmp_path / ".worker_2.json"

    first = mutation._fresh_pytest_command(
        ["tests/test_mod.py::test_value"],
        sentinel_path=first_sentinel,
    )
    second = mutation._fresh_pytest_command(
        ["tests/test_mod.py::test_value"],
        sentinel_path=second_sentinel,
    )

    cache_index = first.index("no:cacheprovider")
    assert first[cache_index - 1 : cache_index + 1] == ["-p", "no:cacheprovider"]
    addopts_index = first.index("addopts=")
    assert first[addopts_index - 1 : addopts_index + 1] == ["-o", "addopts="]
    first_basetemp = next(arg for arg in first if arg.startswith("--basetemp="))
    second_basetemp = next(arg for arg in second if arg.startswith("--basetemp="))
    assert first_basetemp != second_basetemp
    assert str(first_sentinel.parent) in first_basetemp
    assert str(second_sentinel.parent) in second_basetemp


def test_input_snapshot_is_order_independent_and_detects_drift(tmp_path) -> None:
    source = tmp_path / "src" / "pkg" / "mod.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    test_file = tmp_path / "tests" / "test_mod.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("def test_value(): pass\n", encoding="utf-8")

    before = mutation.input_snapshot(
        ("src", "tests/test_mod.py"),
        repo=tmp_path,
    )
    reordered = mutation.input_snapshot(
        ("tests/test_mod.py", "src"),
        repo=tmp_path,
    )
    source.write_text("VALUE = 2\n", encoding="utf-8")
    after = mutation.input_snapshot(
        ("src", "tests/test_mod.py"),
        repo=tmp_path,
    )

    assert before == reordered
    assert after != before


def test_suite_merge_weights_by_mutant_count_not_batch_percentage() -> None:
    cpu = mutation.score_mutation_rows(
        {
            **{f"pkg.cpu.x_check__mutmut_{index}": "killed" for index in range(9)},
            "pkg.cpu.x_check__mutmut_9": "survived",
        },
        modules=("src/pkg/cpu.py",),
        bar=0.90,
    )
    cpu.update(schema=mutation._MUTATION_BATCH_RUN_SCHEMA, tag="cpu")
    gpu = mutation.score_mutation_rows(
        {"pkg.gpu.x_check__mutmut_1": "killed"},
        modules=("src/pkg/gpu.py",),
        bar=0.90,
    )
    gpu.update(schema=mutation._MUTATION_BATCH_RUN_SCHEMA, tag="gpu")

    merged = mutation.merge_mutation_batches((cpu, gpu), bar=0.90)

    assert merged["total"] == 11
    assert merged["killed"] == 10
    assert merged["kill_rate"] == 0.9091
    assert merged["status_counts"]["killed"] == 10
    assert merged["status_counts"]["survived"] == 1
    assert merged["pass"] is True


def test_suite_merge_weights_raw_and_semantic_denominators_independently() -> None:
    cpu_semantic = "pkg.cpu.x_check__mutmut_1"
    cpu_prose = "pkg.cpu.x_check__mutmut_2"
    cpu = mutation.score_mutation_rows(
        {cpu_semantic: "killed", cpu_prose: "survived"},
        modules=("src/pkg/cpu.py",),
        bar=0.90,
        classifications={
            cpu_semantic: {"kind": "semantic", "criticality": "critical"},
            cpu_prose: {
                "kind": "exception_prose_noncontractual",
                "criticality": "not_applicable",
            },
        },
    )
    cpu.update(schema=mutation._MUTATION_BATCH_RUN_SCHEMA, tag="cpu")
    gpu_semantic = "pkg.gpu.x_check__mutmut_1"
    gpu = mutation.score_mutation_rows(
        {gpu_semantic: "killed"},
        modules=("src/pkg/gpu.py",),
        bar=0.90,
        classifications={
            gpu_semantic: {"kind": "semantic", "criticality": "critical"}
        },
    )
    gpu.update(schema=mutation._MUTATION_BATCH_RUN_SCHEMA, tag="gpu")

    merged = mutation.merge_mutation_batches((cpu, gpu), bar=0.90)

    assert merged["raw"]["total"] == 3
    assert merged["raw"]["killed"] == 2
    assert merged["raw"]["kill_rate"] == 0.6667
    assert merged["semantic"]["total"] == 2
    assert merged["semantic"]["killed"] == 2
    assert merged["semantic"]["kill_rate"] == 1.0
    assert merged["semantic"]["excluded_counts"] == {
        "exception_prose_noncontractual": 1,
    }
    assert merged["machine_excluded"]["total"] == 1
    assert set(merged["semantic"]["modules"]) == {
        "src/pkg/cpu.py",
        "src/pkg/gpu.py",
    }
    assert merged["pass"] is True


def test_suite_merge_rejects_raw_semantic_batch_mixture() -> None:
    raw = mutation.score_mutation_rows(
        {"pkg.raw.x_check__mutmut_1": "killed"},
        modules=("src/pkg/raw.py",),
        bar=0.90,
    )
    raw.update(schema=mutation._MUTATION_BATCH_RUN_SCHEMA, tag="raw")
    semantic_mutant = "pkg.semantic.x_check__mutmut_1"
    semantic = mutation.score_mutation_rows(
        {semantic_mutant: "killed"},
        modules=("src/pkg/semantic.py",),
        bar=0.90,
        classifications={
            semantic_mutant: {"kind": "semantic", "criticality": "critical"}
        },
    )
    semantic.update(schema=mutation._MUTATION_BATCH_RUN_SCHEMA, tag="semantic")

    with pytest.raises(ValueError, match="raw/semantic mixture"):
        mutation.merge_mutation_batches((raw, semantic), bar=0.90)


def test_atomic_json_publication_leaves_only_complete_destination(tmp_path) -> None:
    destination = tmp_path / "result.json"

    mutation.write_json_atomic(destination, {"schema": "test.v1", "pass": True})

    assert destination.read_text(encoding="utf-8") == (
        '{\n  "schema": "test.v1",\n  "pass": true\n}\n'
    )
    assert not (tmp_path / ".result.json.tmp").exists()


def test_atomic_json_publication_fsyncs_file_and_parent(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    events: list[str] = []
    real_fsync = mutation.os.fsync
    real_replace = mutation.os.replace

    def tracked_fsync(file_descriptor: int) -> None:
        mode = os.fstat(file_descriptor).st_mode
        events.append("fsync-directory" if stat.S_ISDIR(mode) else "fsync-file")
        real_fsync(file_descriptor)

    def tracked_replace(source: Path, destination: Path) -> None:
        events.append("replace")
        real_replace(source, destination)

    monkeypatch.setattr(mutation.os, "fsync", tracked_fsync)
    monkeypatch.setattr(mutation.os, "replace", tracked_replace)

    mutation.write_json_atomic(tmp_path / "result.json", {"schema": "test.v1"})

    assert events == ["fsync-file", "replace", "fsync-directory"]


def test_durable_file_sha256_fsyncs_file_and_parent_before_hash(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    payload = tmp_path / "worker.log"
    payload.write_bytes(b"durable worker evidence\n")
    synced: list[tuple[str, int]] = []
    real_fsync = mutation.os.fsync
    payload_inode = payload.stat().st_ino

    def tracked_fsync(file_descriptor: int) -> None:
        status = os.fstat(file_descriptor)
        synced.append(
            ("directory" if stat.S_ISDIR(status.st_mode) else "file", status.st_ino)
        )
        real_fsync(file_descriptor)

    monkeypatch.setattr(mutation.os, "fsync", tracked_fsync)

    digest = mutation._durable_file_sha256(payload)

    assert digest == hashlib.sha256(payload.read_bytes()).hexdigest()
    assert synced[0] == ("file", payload_inode)
    assert synced[1][0] == "directory"


@pytest.mark.parametrize(
    "ran",
    [
        SimpleNamespace(
            ok=True,
            returncode=0,
            timed_out=False,
            group_cleanup_verified=False,
        ),
        SimpleNamespace(
            ok=True,
            returncode=0,
            timed_out=True,
            group_cleanup_verified=True,
        ),
        SimpleNamespace(
            ok=True,
            returncode=1,
            timed_out=False,
            group_cleanup_verified=True,
        ),
    ],
)
def test_process_success_validation_fails_closed_on_inconsistent_evidence(ran) -> None:
    with pytest.raises(RuntimeError, match="inconsistent process failed"):
        mutation._require_process_ok("inconsistent process", ran)


@pytest.mark.parametrize("returncode", [3, 4])
def test_fresh_pytest_internal_or_usage_error_is_not_credited_as_killed(
    returncode: int,
) -> None:
    ran = SimpleNamespace(
        ok=False,
        returncode=returncode,
        timed_out=False,
        group_cleanup_verified=True,
    )

    assert mutation._fresh_worker_status(ran) == "suspicious"


def test_fresh_rc_one_requires_authenticated_pytest_completion_sentinel(
    tmp_path,
) -> None:
    ran = SimpleNamespace(
        ok=False,
        returncode=1,
        timed_out=False,
        group_cleanup_verified=True,
    )
    sentinel = tmp_path / "completion.json"

    status, evidence = mutation._authenticated_fresh_worker_status(
        ran,
        sentinel_path=sentinel,
    )
    assert status == "suspicious"
    assert evidence is None

    sentinel.write_text(
        json.dumps(
            {
                "schema": mutation._PYTEST_SENTINEL_SCHEMA,
                "completed": True,
                "pytest_exit_code": 1,
                "sentinel_name": sentinel.name,
                "resource_exhaustion_detected": False,
                "resource_exhaustion_kinds": [],
            }
        ),
        encoding="utf-8",
    )
    status, evidence = mutation._authenticated_fresh_worker_status(
        ran,
        sentinel_path=sentinel,
    )
    assert status == "killed"
    assert evidence is not None
    assert evidence["pytest_exit_code"] == 1
    assert evidence["sentinel_name"] == sentinel.name
    assert evidence["resource_exhaustion_detected"] is False
    assert not sentinel.exists()


def test_authenticated_resource_clean_mutant_timeout_is_killed_and_resumable(
    tmp_path: Path,
) -> None:
    ran = SimpleNamespace(
        ok=False,
        returncode=-15,
        timed_out=True,
        group_cleanup_verified=True,
    )
    sentinel = tmp_path / "timeout_completion.json"
    sentinel.write_text(
        json.dumps(
            {
                "schema": mutation._PYTEST_SENTINEL_SCHEMA,
                "completed": True,
                "pytest_exit_code": 1,
                "sentinel_name": sentinel.name,
                "resource_exhaustion_detected": False,
                "resource_exhaustion_kinds": [],
            }
        ),
        encoding="utf-8",
    )

    status, evidence = mutation._authenticated_fresh_worker_status(
        ran,
        sentinel_path=sentinel,
    )
    row = {
        "process_executed": True,
        "status": status,
        "group_cleanup_verified": ran.group_cleanup_verified,
        "timed_out": ran.timed_out,
        "completion_sentinel_authenticated": evidence is not None,
        "completion_sentinel": evidence,
    }

    assert status == "killed"
    assert evidence is not None
    assert evidence["pytest_exit_code"] == 1
    assert mutation._gpu_worker_row_is_resumable(row) is True
    assert not sentinel.exists()


def test_mutant_timeout_without_authenticated_completion_is_not_resumable(
    tmp_path: Path,
) -> None:
    ran = SimpleNamespace(
        ok=False,
        returncode=-15,
        timed_out=True,
        group_cleanup_verified=True,
    )
    status, evidence = mutation._authenticated_fresh_worker_status(
        ran,
        sentinel_path=tmp_path / "missing.json",
    )

    assert status == "timeout"
    assert evidence is None
    assert mutation._gpu_worker_row_is_resumable(
        {
            "process_executed": True,
            "status": status,
            "group_cleanup_verified": True,
            "timed_out": True,
            "completion_sentinel_authenticated": False,
            "completion_sentinel": None,
        }
    ) is False


def test_mutant_timeout_with_resource_exhaustion_is_not_resumable(
    tmp_path: Path,
) -> None:
    ran = SimpleNamespace(
        ok=False,
        returncode=-15,
        timed_out=True,
        group_cleanup_verified=True,
    )
    sentinel = tmp_path / "oom_timeout.json"
    sentinel.write_text(
        json.dumps(
            {
                "schema": mutation._PYTEST_SENTINEL_SCHEMA,
                "completed": True,
                "pytest_exit_code": 1,
                "sentinel_name": sentinel.name,
                "resource_exhaustion_detected": True,
                "resource_exhaustion_kinds": ["cuda_out_of_memory"],
            }
        ),
        encoding="utf-8",
    )
    status, evidence = mutation._authenticated_fresh_worker_status(
        ran,
        sentinel_path=sentinel,
    )

    assert status == "timeout"
    assert evidence is not None
    assert evidence["resource_exhaustion_detected"] is True
    assert mutation._gpu_worker_row_is_resumable(
        {
            "process_executed": True,
            "status": status,
            "group_cleanup_verified": True,
            "timed_out": True,
            "completion_sentinel_authenticated": True,
            "completion_sentinel": evidence,
        }
    ) is False


def test_fresh_rc_one_with_cuda_oom_sentinel_is_never_credited_as_killed(
    tmp_path: Path,
) -> None:
    ran = SimpleNamespace(
        ok=False,
        returncode=1,
        timed_out=False,
        group_cleanup_verified=True,
    )
    sentinel = tmp_path / "oom_completion.json"
    sentinel.write_text(
        json.dumps(
            {
                "schema": mutation._PYTEST_SENTINEL_SCHEMA,
                "completed": True,
                "pytest_exit_code": 1,
                "sentinel_name": sentinel.name,
                "resource_exhaustion_detected": True,
                "resource_exhaustion_kinds": ["cuda_out_of_memory"],
            }
        ),
        encoding="utf-8",
    )

    status, evidence = mutation._authenticated_fresh_worker_status(
        ran,
        sentinel_path=sentinel,
    )

    assert status == "suspicious"
    assert evidence is not None
    assert evidence["resource_exhaustion_detected"] is True
    assert evidence["resource_exhaustion_kinds"] == ["cuda_out_of_memory"]
    assert not sentinel.exists()


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (MemoryError(), "host_out_of_memory"),
        (RuntimeError("CUDA out of memory. Tried to allocate 1.00 GiB"), "cuda_out_of_memory"),
        (RuntimeError("ordinary assertion helper failed"), None),
    ],
)
def test_resource_exhaustion_classifier_is_narrow(
    exc: BaseException,
    expected: str | None,
) -> None:
    assert mutation._resource_exhaustion_kind(exc) == expected


def test_resource_exhaustion_classifier_traverses_causes_and_groups() -> None:
    cuda_oom = RuntimeError("CUDA out of memory while allocating tensor")
    wrapped = RuntimeError("worker failed")
    wrapped.__cause__ = cuda_oom
    grouped = ExceptionGroup(
        "parallel failures",
        [wrapped, MemoryError("host allocation failed")],
    )

    assert mutation._resource_exhaustion_kind(wrapped) == "cuda_out_of_memory"
    assert mutation._resource_exhaustion_kinds(grouped) == {
        "cuda_out_of_memory",
        "host_out_of_memory",
    }


def test_resource_exhaustion_plugin_records_nested_oom_kinds() -> None:
    cuda_oom = RuntimeError("CUDA error: out of memory")
    wrapped = RuntimeError("worker failed")
    wrapped.__context__ = cuda_oom
    plugin = mutation._ResourceExhaustionPlugin()
    call = SimpleNamespace(
        excinfo=SimpleNamespace(
            value=ExceptionGroup("parallel failures", [wrapped, MemoryError()])
        )
    )

    plugin.pytest_runtest_makereport(None, call)

    assert plugin.kinds == {"cuda_out_of_memory", "host_out_of_memory"}


def test_fresh_pytest_worker_registers_resource_plugin_and_writes_sentinel(
    tmp_path: Path,
) -> None:
    test_file = tmp_path / "test_clean.py"
    test_file.write_text("def test_clean():\n    assert True\n", encoding="utf-8")
    sentinel = tmp_path / "completion.json"

    exit_code = mutation.run_fresh_pytest_worker(
        sentinel,
        ["-q", "-p", "no:cacheprovider", str(test_file)],
    )

    assert exit_code == 0
    payload = json.loads(sentinel.read_text(encoding="utf-8"))
    assert payload["pytest_exit_code"] == 0
    assert payload["resource_exhaustion_detected"] is False


def test_cpu_batch_uses_parallel_stock_mutmut_with_exact_results_and_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    module = tmp_path / "src" / "pkg" / "mod.py"
    module.parent.mkdir(parents=True)
    module.write_text("def value(): return 1\n", encoding="utf-8")
    test_file = tmp_path / "tests" / "test_mod.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("def test_value(): pass\n", encoding="utf-8")
    harness = tmp_path / "tests" / "harness"
    harness.mkdir()
    (harness / "mutation.py").write_text("# harness\n", encoding="utf-8")
    config = tmp_path / "tests" / "harness_config.json"
    config.write_text('{"mutation_gate": {"jobs": null}}\n', encoding="utf-8")
    registry = tmp_path / "cpu.json"
    registry.write_text(
        json.dumps(
            {
                "schema": "error_coupling_simulator.harness.mutation_batch.v1",
                "lane": "cpu_parallel",
                "requires_gpu": False,
                "reconcile_modules": ["src/pkg/mod.py"],
                "covered_by_test_files": ["tests/test_mod.py"],
                "harness": {"mutation_gate": {"kill_rate_bar": 0.9, "jobs": 4}},
            }
        ),
        encoding="utf-8",
    )
    setup = tmp_path / "setup.cfg"
    setup.write_text("[original]\nvalue=1\n", encoding="utf-8")
    calls: list[tuple[list[str], dict]] = []

    def fake_run(command, **kwargs):
        calls.append((list(command), kwargs))
        if command[:2] == ["mutmut", "run"]:
            meta = tmp_path / "mutants" / "src" / "pkg" / "mod.py.meta"
            meta.parent.mkdir(parents=True, exist_ok=True)
            meta.write_text(
                json.dumps(
                    {
                        "exit_code_by_key": {
                            "pkg.mod.x_value__mutmut_1": 1,
                        }
                    }
                ),
                encoding="utf-8",
            )
        if command[:2] == ["mutmut", "results"]:
            result_path = kwargs["log_path"]
            with open(result_path, "w", encoding="utf-8") as handle:
                handle.write("    pkg.mod.x_value__mutmut_1: killed\n")
        return SimpleNamespace(
            ok=True,
            returncode=0,
            timed_out=False,
            group_cleanup_verified=True,
        )

    monkeypatch.setattr(mutation, "REPO", tmp_path)
    monkeypatch.setattr(mutation, "LOGDIR", tmp_path / "logs")
    monkeypatch.setattr(mutation, "CONFIG_PATH", config)
    monkeypatch.setattr(mutation.proc, "run", fake_run)
    monkeypatch.delenv("MUTMUT_JOBS", raising=False)

    result = mutation.run_mutation(str(registry))

    assert calls[0][0] == ["mutmut", "run", "--max-children", "4"]
    assert calls[1][0] == ["mutmut", "results", "--all", "True"]
    assert calls[0][1]["env"]["CUDA_VISIBLE_DEVICES"] == ""
    assert calls[0][1]["env"]["OMP_NUM_THREADS"] == "1"
    assert result["input_snapshot_sha256"] == result["verified_snapshot_sha256"]
    assert result["processes"]["run"]["group_cleanup_verified"] is True
    assert result["execution_policy"] == {
        "lane": "cpu_parallel",
        "jobs": 4,
        "cuda_hidden": True,
        "stock_mutmut_worker_pool": True,
        "fresh_exec_per_tested_mutant": False,
        "max_concurrent_mutant_workers": 4,
    }
    assert result["pass"] is True
    assert setup.read_text(encoding="utf-8") == "[original]\nvalue=1\n"


def test_gpu_batch_uses_one_fresh_exec_per_tested_mutant_and_never_stock_run(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    module = tmp_path / "src" / "pkg" / "mod.py"
    module.parent.mkdir(parents=True)
    module.write_text("def value(): return 1\n", encoding="utf-8")
    test_file = tmp_path / "tests" / "test_mod.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("def test_value(): pass\n", encoding="utf-8")
    harness = tmp_path / "tests" / "harness"
    harness.mkdir()
    harness_script = harness / "mutation.py"
    harness_script.write_text("# harness\n", encoding="utf-8")
    config = tmp_path / "tests" / "harness_config.json"
    config.write_text('{"mutation_gate": {"jobs": null}}\n', encoding="utf-8")
    registry = tmp_path / "gpu.json"
    registry.write_text(
        json.dumps(
            {
                "schema": "error_coupling_simulator.harness.mutation_batch.v1",
                "lane": "gpu_serial",
                "requires_gpu": True,
                "reconcile_modules": ["src/pkg/mod.py"],
                "covered_by_test_files": ["tests/test_mod.py"],
                "harness": {"mutation_gate": {"kill_rate_bar": 0.5, "jobs": 1}},
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "setup.cfg").write_text("[original]\n", encoding="utf-8")
    calls: list[tuple[list[str], dict]] = []
    topology_events: list[str] = []

    def fake_run(command, **kwargs):
        command = list(command)
        calls.append((command, kwargs))
        if "--prepare-fresh-exec" in command:
            topology_events.append("prepare_and_validate_checkpoint")
            assert kwargs["env"]["CUDA_VISIBLE_DEVICES"] == "0"
            assert kwargs["env"]["ECS_GPU_SLOT"] == "0"
            plan_path = command[command.index("--prepare-fresh-exec") + 1]
            with open(plan_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "schema": (
                            "error_coupling_simulator.harness."
                            "mutation_fresh_exec_plan.v3"
                        ),
                        "generated_catalog_sha256": "a" * 64,
                        "clean_control": {
                            "tests": ["tests/test_mod.py::test_value"],
                            "estimated_test_time": 0.01,
                        },
                        "mutants": [
                            {
                                "name": "pkg.mod.x_value__mutmut_1",
                                "tests": ["tests/test_mod.py::test_value"],
                                "estimated_test_time": 0.01,
                            },
                            {
                                "name": "pkg.mod.x_value__mutmut_2",
                                "tests": [],
                                "estimated_test_time": 0.0,
                            },
                        ]
                    },
                    handle,
                )
            return SimpleNamespace(
                ok=True, returncode=0, timed_out=False, group_cleanup_verified=True
            )
        assert "--run-fresh-pytest" in command
        sentinel_path = Path(command[command.index("--run-fresh-pytest") + 1])
        is_clean = kwargs["env"]["MUTANT_UNDER_TEST"] == ""
        exit_code = 0 if is_clean else 1
        Path(kwargs["log_path"]).write_text(
            f"mutant={kwargs['env']['MUTANT_UNDER_TEST']}\n",
            encoding="utf-8",
        )
        _write_fake_pytest_sentinel(sentinel_path, exit_code=exit_code)
        if is_clean:
            return SimpleNamespace(
                ok=True,
                returncode=0,
                timed_out=False,
                group_cleanup_verified=True,
            )
        return SimpleNamespace(
            ok=False, returncode=1, timed_out=False, group_cleanup_verified=True
        )

    class Slot:
        slot = 0

        def child_env(self, base):
            child = dict(base)
            child["CUDA_VISIBLE_DEVICES"] = "0"
            child["ECS_GPU_SLOT"] = "0"
            return child

        def release(self):
            return None

    def acquire_slot():
        topology_events.append("acquire_gpu")
        return Slot()

    monkeypatch.setattr(mutation, "REPO", tmp_path)
    monkeypatch.setattr(mutation, "LOGDIR", tmp_path / "logs")
    monkeypatch.setattr(mutation, "CONFIG_PATH", config)
    monkeypatch.setattr(mutation.proc, "run", fake_run)
    monkeypatch.setattr(mutation.gpu_pool, "acquire_gpu_slot", acquire_slot)
    monkeypatch.setattr(
        mutation,
        "_mutation_runtime_fingerprint",
        lambda: {"schema": "test-runtime", "sha256": "a" * 64},
    )
    monkeypatch.delenv("MUTMUT_JOBS", raising=False)

    result = mutation.run_mutation(str(registry))

    assert topology_events == ["acquire_gpu", "prepare_and_validate_checkpoint"]
    assert all(command[:2] != ["mutmut", "run"] for command, _ in calls)
    pytest_calls = [
        (command, kwargs)
        for command, kwargs in calls
        if "--run-fresh-pytest" in command
    ]
    assert len(pytest_calls) == 2
    assert pytest_calls[0][1]["cwd"] == str(tmp_path / "mutants")
    assert pytest_calls[0][1]["env"]["MUTANT_UNDER_TEST"] == ""
    assert pytest_calls[1][1]["env"]["MUTANT_UNDER_TEST"] == (
        "pkg.mod.x_value__mutmut_1"
    )
    assert pytest_calls[1][1]["env"]["CUDA_VISIBLE_DEVICES"] == "0"
    assert result["processes"]["clean_control"]["returncode"] == 0
    assert result["status_counts"]["killed"] == 1
    assert result["status_counts"]["no_tests"] == 1
    assert result["execution_policy"] == {
        "lane": "gpu_serial",
        "jobs": 1,
        "cuda_hidden": False,
        "stock_mutmut_worker_pool": False,
        "fresh_exec_per_tested_mutant": True,
        "max_concurrent_mutant_workers": 1,
    }
    assert result["pass"] is True


def test_main_dispatches_hidden_fresh_exec_preparation_without_running_batch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    plan = tmp_path / "plan.json"
    prepared: list[tuple[Path, tuple[str, ...]]] = []

    monkeypatch.setattr(
        mutation,
        "prepare_fresh_exec_plan",
        lambda path, *, modules: prepared.append((path, modules)),
    )
    monkeypatch.setattr(
        mutation,
        "run_mutation",
        lambda *_args, **_kwargs: pytest.fail("batch runner must not be entered"),
    )

    assert mutation.main(
        ["--prepare-fresh-exec", str(plan), "src/pkg/mod.py"]
    ) == 0
    assert prepared == [(plan, ("src/pkg/mod.py",))]


def test_restricted_mps_suite_loads_exact_disjoint_cpu_gpu_shards() -> None:
    suite_path = (
        mutation.REPO / "tests" / "_support" / "restricted_mps_mutation_suite.json"
    )

    plan = mutation.load_mutation_suite(suite_path)

    # Each GPU shard declares the worker count suited to the host that runs it.
    # Only the ordering, the lanes, and the per-host ceiling are contractual;
    # the value tracks the host's uniform-speed core count and will change with
    # the hardware.
    assert [(batch["lane"], batch["jobs"]) for batch in plan["batches"]] == [
        ("cpu_parallel", 4),
        ("gpu_serial", 8),
        ("gpu_serial", 8),
        ("gpu_serial", 8),
        ("gpu_serial", 8),
        ("gpu_serial", 8),
    ]
    batch_modules = [
        set(batch["registry_doc"]["reconcile_modules"])
        for batch in plan["batches"]
    ]
    assert [len(modules) for modules in batch_modules[1:]] == [1, 1, 1, 1, 2]
    assert batch_modules[-1] == {
        "src/error_coupling_simulator/certify/axis1_mps.py",
        "src/error_coupling_simulator/certify/mcwf_operator_reference.py",
    }
    assert all(
        left.isdisjoint(right)
        for index, left in enumerate(batch_modules)
        for right in batch_modules[index + 1 :]
    )
    assert set().union(*batch_modules) == set(
        plan["coverage_doc"]["reconcile_modules"]
    )


def test_restricted_mps_gpu_mutation_copies_phase5_document_dependencies() -> None:
    suite_path = (
        mutation.REPO / "tests" / "_support" / "restricted_mps_mutation_suite.json"
    )

    plan = mutation.load_mutation_suite(suite_path)

    gpu_batches = [
        batch for batch in plan["batches"] if batch["lane"] == "gpu_serial"
    ]
    assert len(gpu_batches) == 5
    for gpu in gpu_batches:
        registry = gpu["registry_doc"]
        assert "tests/test_mps_phase5_consolidation.py" in registry[
            "covered_by_test_files"
        ]
        assert {
            "docs/ARCHITECTURE.md",
            "docs/SIMULATOR.md",
        } <= set(registry["mutation_also_copy"])


def test_restricted_mps_mutation_excludes_raw_source_scanners_from_trampolines() -> None:
    suite_path = (
        mutation.REPO / "tests" / "_support" / "restricted_mps_mutation_suite.json"
    )

    plan = mutation.load_mutation_suite(suite_path)

    static_gates = {
        "tests/test_mps_quimb_cutoff_static_gate.py",
        "tests/test_mps_phase6_certification_ownership.py",
    }
    service_status = json.loads(
        (mutation.REPO / "docs" / "service_status.json").read_text(encoding="utf-8")
    )
    restricted_service = next(
        service
        for service in service_status["services"]
        if service["id"] == "restricted_axis1_1d_mps"
    )
    assert static_gates <= set(restricted_service["acceptance"])
    assert all(
        static_gates.isdisjoint(batch["registry_doc"]["covered_by_test_files"])
        for batch in plan["batches"]
        if batch["lane"] == "gpu_serial"
    ), (
        "raw-source AST/text gates inspect every candidate embedded in a mutmut "
        "trampoline, not only the active mutant; keep them in release acceptance "
        "but out of clean-control and per-mutant GPU selection"
    )


def test_mutmut_config_deselects_trampoline_incompatible_static_scanners(
    tmp_path: Path,
) -> None:
    setup = tmp_path / "setup.cfg"

    mutation._write_mutmut_config(
        setup,
        modules=("src/pkg/mod.py",),
        tests=("tests/test_mod.py",),
        also_copy=(),
        timeout_multiplier=15.0,
        timeout_constant=1.0,
    )

    assert (
        "pytest_add_cli_args_test_selection=-m\n"
        "\tnot mutation_trampoline_incompatible\n"
        "\ttests/test_mod.py\n"
    ) in setup.read_text(encoding="utf-8")


def _write_suite_fixture(root: Path) -> tuple[Path, Path]:
    source = root / "src" / "pkg"
    source.mkdir(parents=True)
    (source / "cpu.py").write_text("VALUE = 1\n", encoding="utf-8")
    (source / "gpu.py").write_text("VALUE = 2\n", encoding="utf-8")
    tests = root / "tests"
    tests.mkdir()
    (tests / "test_cpu.py").write_text("def test_cpu(): pass\n", encoding="utf-8")
    (tests / "test_gpu.py").write_text("def test_gpu(): pass\n", encoding="utf-8")
    harness = tests / "harness"
    harness.mkdir()
    (harness / "mutation.py").write_text("# harness\n", encoding="utf-8")
    (tests / "harness_config.json").write_text("{}\n", encoding="utf-8")

    coverage = root / "coverage.json"
    coverage.write_text(
        json.dumps(
            {
                "reconcile_modules": ["src/pkg/cpu.py", "src/pkg/gpu.py"],
            }
        ),
        encoding="utf-8",
    )
    for name, lane, jobs, requires_gpu in (
        ("cpu", "cpu_parallel", 4, False),
        ("gpu", "gpu_serial", 4, True),
    ):
        (root / f"{name}.json").write_text(
            json.dumps(
                {
                    "schema": "error_coupling_simulator.harness.mutation_batch.v1",
                    "lane": lane,
                    "requires_gpu": requires_gpu,
                    "covered_by_test_files": [f"tests/test_{name}.py"],
                    "reconcile_modules": [f"src/pkg/{name}.py"],
                    "harness": {
                        "mutation_gate": {
                            "jobs": jobs,
                            "kill_rate_bar": 0.75,
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
    suite = root / "suite.json"
    suite.write_text(
        json.dumps(
            {
                "schema": "error_coupling_simulator.harness.mutation_suite.v1",
                "coverage_registry": "coverage.json",
                "harness": {"mutation_gate": {"kill_rate_bar": 0.75}},
                "batches": [
                    {
                        "name": "cpu",
                        "registry": "cpu.json",
                        "lane": "cpu_parallel",
                        "jobs": 4,
                        "default_scope": True,
                        "scope_rationale": "scope declared by the fixture so the suite loader accepts it; the real suite carries a substantive scientific rationale per batch",
                    },
                    {
                        "name": "gpu",
                        "registry": "gpu.json",
                        "lane": "gpu_serial",
                        "default_scope": True,
                        "scope_rationale": "scope declared by the fixture so the suite loader accepts it; the real suite carries a substantive scientific rationale per batch",
                        "jobs": 4,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    return suite, source / "cpu.py"


def _fake_raw_batch_result(
    tag: str,
    *,
    total: int = 1,
    killed: int = 1,
    bar: float = 0.75,
) -> dict:
    rows = {
        f"pkg.{tag}.x_check__mutmut_{index}": (
            "killed" if index < killed else "survived"
        )
        for index in range(total)
    }
    result = mutation.score_mutation_rows(
        rows,
        modules=(f"src/pkg/{tag}.py",),
        bar=bar,
    )
    return {
        "schema": mutation._MUTATION_BATCH_RUN_SCHEMA,
        "tag": tag,
        **result,
    }


def test_suite_executes_cpu_parallel_then_gpu_serial_and_weights_results(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    suite, _source = _write_suite_fixture(tmp_path)
    calls: list[tuple[str, int | None, str | None]] = []

    def fake_run(registry, *, jobs=None, timeout=None, lane=None):
        calls.append((Path(registry).stem, jobs, lane))
        if lane == "cpu_parallel":
            return _fake_raw_batch_result("cpu", total=3, killed=3)
        return _fake_raw_batch_result("gpu")

    monkeypatch.setattr(mutation, "REPO", tmp_path)
    monkeypatch.setattr(mutation, "LOGDIR", tmp_path / "logs")
    monkeypatch.setattr(mutation, "CONFIG_PATH", tmp_path / "tests/harness_config.json")
    monkeypatch.setattr(mutation, "run_mutation", fake_run)

    result = mutation.run_mutation_suite(str(suite), timeout=17.0)

    assert calls == [
        ("cpu", 4, "cpu_parallel"),
        ("gpu", 4, "gpu_serial"),
    ]
    assert result["total"] == 4
    assert result["killed"] == 4
    assert result["kill_rate"] == 1.0
    assert result["pass"] is True
    assert result["schema"] == mutation._MUTATION_SUITE_RUN_SCHEMA
    assert result["input_snapshot_sha256"] == result["verified_snapshot_sha256"]
    assert json.loads(
        (tmp_path / "logs/suite_mutation_survivors.json").read_text(encoding="utf-8")
    ) == result


def test_suite_rejects_gpu_jobs_above_the_ceiling(tmp_path: Path) -> None:
    ceiling = mutation._GPU_MAX_FRESH_WORKERS
    over = ceiling + 1
    suite, _source = _write_suite_fixture(tmp_path)
    suite_doc = json.loads(suite.read_text(encoding="utf-8"))
    suite_doc["batches"][1]["jobs"] = over
    suite.write_text(json.dumps(suite_doc), encoding="utf-8")
    registry = tmp_path / "gpu.json"
    registry_doc = json.loads(registry.read_text(encoding="utf-8"))
    registry_doc["harness"]["mutation_gate"]["jobs"] = over
    registry.write_text(json.dumps(registry_doc), encoding="utf-8")

    with pytest.raises(ValueError, match=f"at most {ceiling}"):
        mutation.load_mutation_suite(suite)


def test_suite_loader_rejects_child_kill_bar_drift(tmp_path: Path) -> None:
    suite, _source = _write_suite_fixture(tmp_path)
    child = tmp_path / "gpu.json"
    child_doc = json.loads(child.read_text(encoding="utf-8"))
    child_doc["harness"]["mutation_gate"]["kill_rate_bar"] = 0.76
    child.write_text(json.dumps(child_doc), encoding="utf-8")

    with pytest.raises(ValueError, match="suite/child kill-rate bar mismatch"):
        mutation.load_mutation_suite(suite)


def test_suite_rejects_v1_semantic_manifest_before_any_batch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    suite, _source = _write_suite_fixture(tmp_path)
    manifest = tmp_path / "dispositions.json"
    manifest.write_text(
        json.dumps(
            {
                "schema": (
                    "error_coupling_simulator.harness."
                    "mutation_semantic_dispositions.v1"
                ),
                "classifier_policy": "conservative_exception_prose_ast.v2",
                "reviewed": [],
            }
        ),
        encoding="utf-8",
    )
    suite_doc = json.loads(suite.read_text(encoding="utf-8"))
    suite_doc["semantic_dispositions"] = manifest.name
    suite.write_text(json.dumps(suite_doc), encoding="utf-8")
    for child_name in ("cpu.json", "gpu.json"):
        child = tmp_path / child_name
        child_doc = json.loads(child.read_text(encoding="utf-8"))
        child_doc["semantic_dispositions"] = manifest.name
        child.write_text(json.dumps(child_doc), encoding="utf-8")

    monkeypatch.setattr(mutation, "REPO", tmp_path)
    monkeypatch.setattr(mutation, "LOGDIR", tmp_path / "logs")
    monkeypatch.setattr(mutation, "CONFIG_PATH", tmp_path / "tests/harness_config.json")

    def forbidden_batch(*_args, **_kwargs):
        raise AssertionError("batch executed before semantic manifest validation")

    monkeypatch.setattr(mutation, "run_mutation", forbidden_batch)
    with pytest.raises(ValueError, match="unsupported semantic disposition schema"):
        mutation.run_mutation_suite(str(suite))


@pytest.mark.parametrize(
    ("manifest_document", "message"),
    [
        (
            {
                "schema": (
                    "error_coupling_simulator.harness."
                    "mutation_semantic_dispositions.v1"
                ),
                "classifier_policy": "conservative_exception_prose_ast.v2",
                "reviewed": [],
            },
            "unsupported semantic disposition schema",
        ),
        (
            {
                "schema": mutation._SEMANTIC_DISPOSITION_SCHEMA,
                "classifier_policy": mutation._SEMANTIC_CLASSIFIER_POLICY,
                "reviewed": [{}],
            },
            "semantic disposition review fields mismatch",
        ),
    ],
)
def test_direct_batch_rejects_static_semantic_manifest_defects_before_setup_mutation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    manifest_document: dict,
    message: str,
) -> None:
    manifest = tmp_path / "dispositions.json"
    manifest.write_text(
        json.dumps(manifest_document),
        encoding="utf-8",
    )
    registry = tmp_path / "direct.json"
    registry.write_text(
        json.dumps(
            {
                "schema": "error_coupling_simulator.harness.mutation_batch.v1",
                "lane": "cpu_parallel",
                "requires_gpu": False,
                "covered_by_test_files": ["tests/test_direct.py"],
                "reconcile_modules": ["src/pkg/direct.py"],
                "semantic_dispositions": manifest.name,
                "harness": {
                    "mutation_gate": {
                        "jobs": 1,
                        "kill_rate_bar": 0.90,
                        "timeout_multiplier": 15.0,
                        "timeout_constant": 1.0,
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(mutation, "REPO", tmp_path)
    monkeypatch.setattr(mutation, "LOGDIR", tmp_path / "logs")
    monkeypatch.setattr(
        mutation,
        "_begin_setup_override",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("setup mutated before semantic manifest validation")
        ),
    )

    with pytest.raises(ValueError, match=message):
        mutation.run_mutation(str(registry))


def test_merge_rejects_forged_child_module_rate_and_pass() -> None:
    first = mutation.score_mutation_rows(
        {
            **{f"pkg.first.x_check__mutmut_{index}": "killed" for index in range(8)},
            **{
                f"pkg.first.x_check__mutmut_{index}": "survived"
                for index in range(8, 10)
            },
        },
        modules=("src/pkg/first.py",),
        bar=0.90,
    )
    first["modules"]["src/pkg/first.py"]["kill_rate"] = 1.0
    first["modules"]["src/pkg/first.py"]["pass"] = True
    first["pass"] = True
    first["schema"] = mutation._MUTATION_BATCH_RUN_SCHEMA
    second = mutation.score_mutation_rows(
        {
            f"pkg.second.x_check__mutmut_{index}": "killed"
            for index in range(10)
        },
        modules=("src/pkg/second.py",),
        bar=0.90,
    )
    second["schema"] = mutation._MUTATION_BATCH_RUN_SCHEMA

    with pytest.raises(ValueError, match="module score disagrees with counts"):
        mutation.merge_mutation_batches((first, second), bar=0.90)


def test_merge_rejects_legacy_batch_result_schema() -> None:
    legacy = mutation.score_mutation_rows(
        {"pkg.mod.x_check__mutmut_1": "killed"},
        modules=("src/pkg/mod.py",),
        bar=0.90,
    )
    legacy["schema"] = (
        "error_coupling_simulator.harness.mutation_batch_run.v2"
    )

    with pytest.raises(ValueError, match="unsupported mutation batch result schema"):
        mutation.merge_mutation_batches((legacy,), bar=0.90)


@pytest.mark.parametrize("field", ["bar", "kill_rate", "modules", "pass"])
def test_merge_rejects_v3_batch_missing_required_score_field(field: str) -> None:
    batch = _fake_raw_batch_result("required", bar=0.75)
    del batch[field]

    with pytest.raises(ValueError, match="required score fields"):
        mutation.merge_mutation_batches((batch,), bar=0.75)


def test_merge_rejects_v3_batch_with_incomplete_status_vector() -> None:
    batch = _fake_raw_batch_result("statuses", bar=0.75)
    del batch["status_counts"]["timeout"]

    with pytest.raises(ValueError, match="status keys"):
        mutation.merge_mutation_batches((batch,), bar=0.75)


def test_merge_rejects_v3_batch_with_unknown_zero_status() -> None:
    batch = _fake_raw_batch_result("unknown-status", bar=0.75)
    batch["status_counts"]["invented"] = 0

    with pytest.raises(ValueError, match="status keys"):
        mutation.merge_mutation_batches((batch,), bar=0.75)


@pytest.mark.parametrize("score_name", ["raw", "semantic"])
def test_merge_rejects_unexpected_nested_score_field(score_name: str) -> None:
    mutant = "pkg.extra.x_check__mutmut_1"
    batch = mutation.score_mutation_rows(
        {mutant: "killed"},
        modules=("src/pkg/extra.py",),
        bar=0.90,
        classifications={
            mutant: {"kind": "semantic", "criticality": "critical"}
        },
    )
    batch["schema"] = mutation._MUTATION_BATCH_RUN_SCHEMA
    batch[score_name]["forged"] = 0

    with pytest.raises(ValueError, match="score fields"):
        mutation.merge_mutation_batches((batch,), bar=0.90)


@pytest.mark.parametrize("field", ["bar", "kill_rate", "modules"])
def test_merge_rejects_semantic_batch_raw_alias_drift(field: str) -> None:
    mutant = "pkg.alias.x_check__mutmut_1"
    batch = mutation.score_mutation_rows(
        {mutant: "killed"},
        modules=("src/pkg/alias.py",),
        bar=0.90,
        classifications={
            mutant: {"kind": "semantic", "criticality": "critical"}
        },
    )
    batch["schema"] = mutation._MUTATION_BATCH_RUN_SCHEMA
    batch[field] = {} if field == "modules" else 0.5

    with pytest.raises(ValueError, match="raw aliases disagree"):
        mutation.merge_mutation_batches((batch,), bar=0.90)


@pytest.mark.parametrize("corruption", ["total_bool", "killed_text", "pass"])
def test_merge_rejects_typed_semantic_batch_alias_drift(corruption: str) -> None:
    mutant = "pkg.typed_alias.x_check__mutmut_1"
    batch = mutation.score_mutation_rows(
        {mutant: "killed"},
        modules=("src/pkg/typed_alias.py",),
        bar=0.90,
        classifications={
            mutant: {"kind": "semantic", "criticality": "critical"}
        },
    )
    batch["schema"] = mutation._MUTATION_BATCH_RUN_SCHEMA
    if corruption == "total_bool":
        batch["total"] = True
    elif corruption == "killed_text":
        batch["killed"] = "1"
    else:
        batch["pass"] = not batch["semantic"]["pass"]

    with pytest.raises(ValueError, match="raw aliases disagree|pass alias disagrees"):
        mutation.merge_mutation_batches((batch,), bar=0.90)


@pytest.mark.parametrize("corruption", ["declared", "killed", "not_killed"])
def test_merge_rejects_forged_semantic_critical_evidence(corruption: str) -> None:
    killed = "pkg.critical.x_check__mutmut_1"
    survived = "pkg.critical.x_check__mutmut_2"
    batch = mutation.score_mutation_rows(
        {killed: "killed", survived: "survived"},
        modules=("src/pkg/critical.py",),
        bar=0.50,
        classifications={
            killed: {"kind": "semantic", "criticality": "critical"},
            survived: {"kind": "semantic", "criticality": "critical"},
        },
    )
    batch["schema"] = mutation._MUTATION_BATCH_RUN_SCHEMA
    critical = batch["semantic"]["critical"]
    if corruption == "declared":
        critical["declared"] -= 1
    elif corruption == "killed":
        critical["killed"] -= 1
    else:
        critical["not_killed"] = []

    with pytest.raises(ValueError, match="critical evidence"):
        mutation.merge_mutation_batches((batch,), bar=0.50)


@pytest.mark.parametrize("corruption", ["status", "bool_count", "identity"])
def test_merge_rejects_malformed_semantic_critical_identity(corruption: str) -> None:
    killed = "pkg.identity.x_check__mutmut_1"
    survived = "pkg.identity.x_check__mutmut_2"
    batch = mutation.score_mutation_rows(
        {killed: "killed", survived: "survived"},
        modules=("src/pkg/identity.py",),
        bar=0.50,
        classifications={
            killed: {"kind": "semantic", "criticality": "critical"},
            survived: {"kind": "semantic", "criticality": "critical"},
        },
    )
    batch["schema"] = mutation._MUTATION_BATCH_RUN_SCHEMA
    critical = batch["semantic"]["critical"]
    if corruption == "status":
        critical["not_killed"][0]["status"] = "timeout"
    elif corruption == "bool_count":
        critical["declared"] = True
    else:
        critical["not_killed"][0]["mutant"] = ""

    with pytest.raises((TypeError, ValueError), match="critical evidence"):
        mutation.merge_mutation_batches((batch,), bar=0.50)


@pytest.mark.parametrize("corruption", ["status", "kind"])
def test_merge_rejects_noncanonical_machine_exclusion_domain(
    corruption: str,
) -> None:
    semantic = "pkg.machine.x_check__mutmut_1"
    prose = "pkg.machine.x_check__mutmut_2"
    batch = mutation.score_mutation_rows(
        {semantic: "killed", prose: "survived"},
        modules=("src/pkg/machine.py",),
        bar=0.90,
        classifications={
            semantic: {"kind": "semantic", "criticality": "critical"},
            prose: {
                "kind": "exception_prose_noncontractual",
                "criticality": "not_applicable",
            },
        },
    )
    batch["schema"] = mutation._MUTATION_BATCH_RUN_SCHEMA
    machine = batch["machine_excluded"]
    if corruption == "status":
        machine["status_counts"]["invented"] = 0
    else:
        count = machine["kind_counts"].pop("exception_prose_noncontractual")
        machine["kind_counts"]["renamed"] = count

    with pytest.raises(ValueError, match="machine exclusion"):
        mutation.merge_mutation_batches((batch,), bar=0.90)


@pytest.mark.parametrize("field", ["total", "survived_status"])
def test_merge_rejects_nonconserved_machine_exclusion(field: str) -> None:
    semantic = "pkg.mod.x_check__mutmut_1"
    prose = "pkg.mod.x_check__mutmut_2"
    batch = mutation.score_mutation_rows(
        {semantic: "killed", prose: "survived"},
        modules=("src/pkg/mod.py",),
        bar=0.90,
        classifications={
            semantic: {"kind": "semantic", "criticality": "critical"},
            prose: {
                "kind": "exception_prose_noncontractual",
                "criticality": "not_applicable",
            },
        },
    )
    batch["schema"] = mutation._MUTATION_BATCH_RUN_SCHEMA
    if field == "total":
        batch["machine_excluded"]["total"] = 0
    else:
        batch["machine_excluded"]["status_counts"]["survived"] = 0

    with pytest.raises(ValueError, match="machine exclusion is not conserved"):
        mutation.merge_mutation_batches((batch,), bar=0.90)


def test_direct_mutation_waits_for_suite_orchestration_lock(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(mutation, "LOGDIR", tmp_path)
    lock_path = tmp_path / ".ecs_mutation_suite.lock"
    owner_fd = mutation.os.open(
        str(lock_path),
        mutation.os.O_CREAT | mutation.os.O_WRONLY,
        0o644,
    )
    mutation.fcntl.flock(owner_fd, mutation.fcntl.LOCK_EX)
    acquired = threading.Event()
    release = threading.Event()
    errors: list[BaseException] = []

    def contender() -> None:
        try:
            fd = mutation._acquire_direct_suite_lock()
            assert fd is not None
            acquired.set()
            assert release.wait(2.0)
            mutation.os.close(fd)
        except BaseException as exc:
            errors.append(exc)

    thread = threading.Thread(target=contender, daemon=True)
    thread.start()
    try:
        assert not acquired.wait(0.1)
    finally:
        mutation.os.close(owner_fd)
    assert acquired.wait(2.0)
    release.set()
    thread.join(2.0)
    assert not thread.is_alive()
    assert errors == []


def test_suite_retires_gpu_checkpoint_only_after_aggregate_publish(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    suite, _source = _write_suite_fixture(tmp_path)
    logs = tmp_path / "logs"
    checkpoint = logs / "gpu_mutation_checkpoint.json"
    published_with_checkpoint: list[Path] = []
    real_write_json_atomic = mutation.write_json_atomic

    def fake_run(registry, *, jobs=None, timeout=None, lane=None):
        tag = Path(registry).stem
        if lane == "gpu_serial":
            checkpoint.write_text('{"resume": true}\n', encoding="utf-8")
        return _fake_raw_batch_result(tag)

    def tracked_publish(destination: Path, payload: dict) -> None:
        assert checkpoint.is_file()
        published_with_checkpoint.append(destination)
        real_write_json_atomic(destination, payload)

    monkeypatch.setattr(mutation, "REPO", tmp_path)
    monkeypatch.setattr(mutation, "LOGDIR", logs)
    monkeypatch.setattr(mutation, "CONFIG_PATH", tmp_path / "tests/harness_config.json")
    monkeypatch.setattr(mutation, "run_mutation", fake_run)
    monkeypatch.setattr(mutation, "write_json_atomic", tracked_publish)

    result = mutation.run_mutation_suite(str(suite))

    assert result["pass"] is True
    assert published_with_checkpoint == [logs / "suite_mutation_survivors.json"]
    assert not checkpoint.exists()


def test_suite_publish_failure_retains_gpu_checkpoint(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    suite, _source = _write_suite_fixture(tmp_path)
    logs = tmp_path / "logs"
    checkpoint = logs / "gpu_mutation_checkpoint.json"

    def fake_run(registry, *, jobs=None, timeout=None, lane=None):
        tag = Path(registry).stem
        if lane == "gpu_serial":
            checkpoint.write_text('{"resume": true}\n', encoding="utf-8")
        return _fake_raw_batch_result(tag)

    def fail_publish(_destination: Path, _payload: dict) -> None:
        assert checkpoint.is_file()
        raise RuntimeError("injected aggregate publication failure")

    monkeypatch.setattr(mutation, "REPO", tmp_path)
    monkeypatch.setattr(mutation, "LOGDIR", logs)
    monkeypatch.setattr(mutation, "CONFIG_PATH", tmp_path / "tests/harness_config.json")
    monkeypatch.setattr(mutation, "run_mutation", fake_run)
    monkeypatch.setattr(mutation, "write_json_atomic", fail_publish)

    with pytest.raises(RuntimeError, match="publication failure"):
        mutation.run_mutation_suite(str(suite))

    assert checkpoint.is_file()


def test_suite_recovery_failure_retires_stale_aggregate_pass(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    suite, _source = _write_suite_fixture(tmp_path)
    logs = tmp_path / "logs"
    logs.mkdir()
    stale_result = logs / "suite_mutation_survivors.json"
    stale_result.write_text('{"pass": true}\n', encoding="utf-8")
    (logs / ".setup.cfg.bak").write_text("[original]\n", encoding="utf-8")
    (logs / ".setup.cfg.absent").write_text("absent\n", encoding="utf-8")

    monkeypatch.setattr(mutation, "REPO", tmp_path)
    monkeypatch.setattr(mutation, "LOGDIR", logs)
    monkeypatch.setattr(mutation, "CONFIG_PATH", tmp_path / "tests/harness_config.json")

    with pytest.raises(RuntimeError, match="conflicting stale setup.cfg"):
        mutation.run_mutation_suite(str(suite))

    assert not stale_result.exists()


def test_suite_stops_before_gpu_if_cpu_batch_mutates_an_input(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    suite, source = _write_suite_fixture(tmp_path)
    calls: list[str] = []
    logs = tmp_path / "logs"
    logs.mkdir()
    old_result = logs / "suite_mutation_survivors.json"
    old_result.write_text('{"pass": true}\n', encoding="utf-8")

    def drifting_run(registry, **_kwargs):
        calls.append(Path(registry).stem)
        source.write_text("VALUE = 999\n", encoding="utf-8")
        return _fake_raw_batch_result("cpu")

    monkeypatch.setattr(mutation, "REPO", tmp_path)
    monkeypatch.setattr(mutation, "LOGDIR", logs)
    monkeypatch.setattr(mutation, "CONFIG_PATH", tmp_path / "tests/harness_config.json")
    monkeypatch.setattr(mutation, "run_mutation", drifting_run)

    with pytest.raises(RuntimeError, match="snapshot drifted after batch cpu"):
        mutation.run_mutation_suite(str(suite))

    assert calls == ["cpu"]
    assert not old_result.exists()


def test_suite_rejects_final_snapshot_drift_before_publish(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    suite, _source = _write_suite_fixture(tmp_path)
    logs = tmp_path / "logs"
    snapshots = iter(["stable", "stable", "stable", "stable", "stable", "drifted"])

    def fake_run(registry, **_kwargs):
        return _fake_raw_batch_result(Path(registry).stem)

    monkeypatch.setattr(mutation, "REPO", tmp_path)
    monkeypatch.setattr(mutation, "LOGDIR", logs)
    monkeypatch.setattr(mutation, "CONFIG_PATH", tmp_path / "tests/harness_config.json")
    monkeypatch.setattr(mutation, "run_mutation", fake_run)
    monkeypatch.setattr(
        mutation,
        "input_snapshot",
        lambda *_args, **_kwargs: next(snapshots),
    )

    with pytest.raises(RuntimeError, match="snapshot drifted before suite publish"):
        mutation.run_mutation_suite(str(suite))

    assert not (logs / "suite_mutation_survivors.json").exists()


def test_suite_rechecks_snapshot_after_merge_before_publish(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    suite, source = _write_suite_fixture(tmp_path)
    logs = tmp_path / "logs"
    real_merge = mutation.merge_mutation_batches

    def fake_run(registry, **_kwargs):
        return _fake_raw_batch_result(Path(registry).stem)

    def drifting_merge(batches, *, bar):
        result = real_merge(batches, bar=bar)
        source.write_text("VALUE = 999\n", encoding="utf-8")
        return result

    monkeypatch.setattr(mutation, "REPO", tmp_path)
    monkeypatch.setattr(mutation, "LOGDIR", logs)
    monkeypatch.setattr(mutation, "CONFIG_PATH", tmp_path / "tests/harness_config.json")
    monkeypatch.setattr(mutation, "run_mutation", fake_run)
    monkeypatch.setattr(mutation, "merge_mutation_batches", drifting_merge)

    with pytest.raises(RuntimeError, match="snapshot drifted before suite publish"):
        mutation.run_mutation_suite(str(suite))

    assert not (logs / "suite_mutation_survivors.json").exists()


def test_suite_lock_prevents_failed_second_run_from_leaving_first_pass(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    suite, _source = _write_suite_fixture(tmp_path)
    logs = tmp_path / "logs"
    a_entered = threading.Event()
    allow_a = threading.Event()
    b_entered = threading.Event()
    results: dict[str, dict] = {}
    errors: dict[str, BaseException] = {}

    def fake_run(registry, **_kwargs):
        batch = Path(registry).stem
        if threading.current_thread().name == "suite-a":
            if batch == "cpu":
                a_entered.set()
                assert allow_a.wait(timeout=2.0)
            return _fake_raw_batch_result(batch)
        b_entered.set()
        raise RuntimeError("second suite forced failure")

    def invoke(label: str) -> None:
        try:
            results[label] = mutation.run_mutation_suite(str(suite))
        except BaseException as exc:  # captured for assertions across threads
            errors[label] = exc

    monkeypatch.setattr(mutation, "REPO", tmp_path)
    monkeypatch.setattr(mutation, "LOGDIR", logs)
    monkeypatch.setattr(mutation, "CONFIG_PATH", tmp_path / "tests/harness_config.json")
    monkeypatch.setattr(mutation, "run_mutation", fake_run)

    first = threading.Thread(target=invoke, args=("a",), name="suite-a")
    second = threading.Thread(target=invoke, args=("b",), name="suite-b")
    first.start()
    assert a_entered.wait(timeout=2.0)
    second.start()
    assert not b_entered.wait(timeout=0.05)
    allow_a.set()
    first.join(timeout=2.0)
    second.join(timeout=2.0)

    assert not first.is_alive()
    assert not second.is_alive()
    assert results["a"]["pass"] is True
    assert isinstance(errors["b"], RuntimeError)
    assert b_entered.is_set()
    assert not (logs / "suite_mutation_survivors.json").exists()


@pytest.mark.parametrize(
    "text, message",
    [
        ("pkg.x__mutmut_1: invented\n", "unknown mutmut result row"),
        (
            "pkg.x__mutmut_1: killed\npkg.x__mutmut_1: survived\n",
            "duplicate or empty mutmut result",
        ),
        ("\n", "contained no mutant rows"),
    ],
)
def test_parse_results_rejects_unknown_duplicate_or_empty_output(
    text: str,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        mutation.parse_mutmut_results(text)


def test_score_requires_each_declared_module_to_have_mutants_and_meet_bar() -> None:
    score = mutation.score_mutation_rows(
        {
            "pkg.cpu.x_a__mutmut_1": "killed",
            "pkg.gpu.x_b__mutmut_1": "survived",
        },
        modules=("src/pkg/cpu.py", "src/pkg/gpu.py"),
        bar=0.75,
    )

    assert score["kill_rate"] == 0.5
    assert score["pass"] is False
    assert score["modules"]["src/pkg/cpu.py"]["pass"] is True
    assert score["modules"]["src/pkg/gpu.py"]["pass"] is False


@pytest.mark.parametrize(
    ("original", "mutant"),
    [
        (
            "def f(value):\n    raise ValueError('bad value')\n",
            "def g(value):\n    raise ValueError(None)\n",
        ),
        (
            "def f(value):\n    raise TypeError('bad value')\n",
            "def g(value):\n    raise TypeError('XXbad valueXX')\n",
        ),
        (
            "def f(value):\n    raise RuntimeError(f'bad {value!r}')\n",
            "def g(value):\n    raise RuntimeError(None)\n",
        ),
    ],
)
def test_exception_prose_classifier_accepts_only_outer_text_replacements(
    original: str,
    mutant: str,
) -> None:
    assert mutation._is_exception_prose_only(
        ast.parse(original).body[0],
        ast.parse(mutant).body[0],
    )


def test_exception_prose_classifier_accepts_one_static_fstring_segment() -> None:
    original = ast.parse(
        "def f(value):\n    raise ValueError(f'bad {value!r} suffix')\n"
    ).body[0]
    mutant = ast.parse(
        "def g(value):\n    raise ValueError(f'XXbad XX{value!r} suffix')\n"
    ).body[0]

    assert mutation._is_exception_prose_only(original, mutant)


@pytest.mark.parametrize(
    ("original", "mutant"),
    [
        (
            "def f(value):\n    if value < 0:\n        raise ValueError('bad')\n",
            "def g(value):\n    if value <= 0:\n        raise ValueError('bad')\n",
        ),
        (
            "def f(value):\n    raise ValueError('bad')\n",
            "def g(value):\n    raise TypeError('bad')\n",
        ),
        (
            "def f(value):\n    raise KeyError('bad')\n",
            "def g(value):\n    raise KeyError(None)\n",
        ),
        (
            "def f(value):\n    return 'bad'\n",
            "def g(value):\n    return None\n",
        ),
        (
            "def f(tensor):\n    raise RuntimeError(f'bad {tuple(tensor.shape)}')\n",
            "def g(tensor):\n    raise RuntimeError(f'bad {tuple(None)}')\n",
        ),
        (
            "def f(value):\n    raise RuntimeError(f'bad {value!r}')\n",
            "def g(value):\n    raise RuntimeError(f'bad {value!s}')\n",
        ),
        (
            "def f(value):\n    raise RuntimeError(f'bad {value:.2f}')\n",
            "def g(value):\n    raise RuntimeError(f'bad {value:.3f}')\n",
        ),
        (
            "def f(value):\n    raise RuntimeError(f'bad {value} suffix')\n",
            "def g(value):\n    raise RuntimeError(f'XXbad XX{value}XX suffixXX')\n",
        ),
        (
            "def f(value):\n    raise ValueError(('bad', value))\n",
            "def g(value):\n    raise ValueError(None)\n",
        ),
    ],
)
def test_exception_prose_classifier_keeps_behavioral_deltas_semantic(
    original: str,
    mutant: str,
) -> None:
    assert not mutation._is_exception_prose_only(
        ast.parse(original).body[0],
        ast.parse(mutant).body[0],
    )


def test_semantic_catalog_authenticates_trampoline_inventory_and_classifies(
    tmp_path,
) -> None:
    module = "src/pkg/mod.py"
    source = tmp_path / module
    source.parent.mkdir(parents=True)
    source.write_text(
        "def check(value):\n    if value < 0:\n        raise ValueError(f'bad {value}')\n",
        encoding="utf-8",
    )
    trampoline = tmp_path / "mutants" / module
    trampoline.parent.mkdir(parents=True)
    trampoline.write_text(
        "def x_check__mutmut_orig(value):\n"
        "    if value < 0:\n"
        "        raise ValueError(f'bad {value}')\n\n"
        "def x_check__mutmut_1(value):\n"
        "    if value < 0:\n"
        "        raise ValueError(None)\n\n"
        "def x_check__mutmut_2(value):\n"
        "    if value <= 0:\n"
        "        raise ValueError(f'bad {value}')\n",
        encoding="utf-8",
    )
    rows = {
        "pkg.mod.x_check__mutmut_1": "survived",
        "pkg.mod.x_check__mutmut_2": "killed",
    }

    catalog = mutation.build_semantic_mutant_catalog(
        rows,
        modules=(module,),
        repo=tmp_path,
    )

    classifications = catalog["classifications"]
    assert classifications["pkg.mod.x_check__mutmut_1"]["kind"] == (
        "exception_prose_noncontractual"
    )
    assert classifications["pkg.mod.x_check__mutmut_2"]["kind"] == "semantic"
    assert classifications["pkg.mod.x_check__mutmut_2"]["criticality"] == (
        "critical"
    )
    assert catalog["modules"][module]["mutant_count"] == 2
    assert len(catalog["modules"][module]["catalog_sha256"]) == 64
    assert catalog["generator"] == {"name": "mutmut", "version": "3.6.0"}

    with pytest.raises(ValueError, match="trampoline mutant inventory"):
        mutation.build_semantic_mutant_catalog(
            {**rows, "pkg.mod.x_check__mutmut_3": "survived"},
            modules=(module,),
            repo=tmp_path,
        )


def test_semantic_score_keeps_raw_informational_and_excludes_prose_survivor() -> None:
    killed = "pkg.mod.x_check__mutmut_1"
    prose = "pkg.mod.x_check__mutmut_2"
    score = mutation.score_mutation_rows(
        {killed: "killed", prose: "survived"},
        modules=("src/pkg/mod.py",),
        bar=0.90,
        classifications={
            killed: {"kind": "semantic", "criticality": "critical"},
            prose: {
                "kind": "exception_prose_noncontractual",
                "criticality": "not_applicable",
            },
        },
    )

    assert score["raw"]["total"] == 2
    assert score["raw"]["killed"] == 1
    assert score["raw"]["kill_rate"] == 0.5
    assert score["semantic"]["total"] == 1
    assert score["semantic"]["killed"] == 1
    assert score["semantic"]["kill_rate"] == 1.0
    assert score["semantic"]["excluded_counts"] == {
        "exception_prose_noncontractual": 1,
    }
    assert score["machine_excluded"]["total"] == 1
    assert score["pass"] is True


def test_machine_exclusion_is_status_independent_and_exactly_conserved() -> None:
    semantic = "pkg.mod.x_check__mutmut_1"
    survived_prose = "pkg.mod.x_check__mutmut_2"
    killed_prose = "pkg.mod.x_check__mutmut_3"
    rows = {
        semantic: "killed",
        survived_prose: "survived",
        killed_prose: "killed",
    }
    classifications = {
        semantic: {"kind": "semantic", "criticality": "critical"},
        survived_prose: {
            "kind": "exception_prose_noncontractual",
            "criticality": "not_applicable",
        },
        killed_prose: {
            "kind": "exception_prose_noncontractual",
            "criticality": "not_applicable",
        },
    }

    score = mutation.score_mutation_rows(
        rows,
        modules=("src/pkg/mod.py",),
        bar=0.90,
        classifications=classifications,
    )

    excluded = score["machine_excluded"]
    assert excluded["total"] == 2
    assert excluded["status_counts"]["killed"] == 1
    assert excluded["status_counts"]["survived"] == 1
    assert score["raw"]["total"] == score["semantic"]["total"] + excluded["total"]
    for status, raw_count in score["raw"]["status_counts"].items():
        assert raw_count == (
            score["semantic"]["status_counts"][status]
            + excluded["status_counts"][status]
        )
    assert score["pass"] is True


def test_semantic_score_fails_closed_on_unreviewed_critical_survivor() -> None:
    rows = {
        **{f"pkg.mod.x_check__mutmut_{index}": "killed" for index in range(1, 10)},
        "pkg.mod.x_check__mutmut_10": "survived",
    }
    classifications = {
        mutant: {"kind": "semantic", "criticality": "critical"}
        for mutant in rows
    }

    score = mutation.score_mutation_rows(
        rows,
        modules=("src/pkg/mod.py",),
        bar=0.90,
        classifications=classifications,
    )

    assert score["semantic"]["kill_rate"] == 0.9
    assert score["semantic"]["modules"]["src/pkg/mod.py"]["pass"] is True
    assert score["semantic"]["critical"]["not_killed"] == [
        {"mutant": "pkg.mod.x_check__mutmut_10", "status": "survived"}
    ]
    assert score["pass"] is False


def test_semantic_score_rejects_human_reviewed_noncritical_headroom() -> None:
    rows = {
        **{f"pkg.mod.x_check__mutmut_{index}": "killed" for index in range(1, 10)},
        "pkg.mod.x_check__mutmut_10": "survived",
    }
    classifications = {
        mutant: {"kind": "semantic", "criticality": "critical"}
        for mutant in rows
    }
    classifications["pkg.mod.x_check__mutmut_10"] = {
        "kind": "semantic",
        "criticality": "reviewed_noncritical",
    }

    with pytest.raises(ValueError, match="invalid semantic classification"):
        mutation.score_mutation_rows(
            rows,
            modules=("src/pkg/mod.py",),
            bar=0.90,
            classifications=classifications,
        )


def test_semantic_score_accepts_killed_machine_exclusion_and_rejects_identity_drift() -> None:
    semantic = "pkg.mod.x_check__mutmut_1"
    excluded = "pkg.mod.x_check__mutmut_2"
    score = mutation.score_mutation_rows(
        {semantic: "killed", excluded: "killed"},
        modules=("src/pkg/mod.py",),
        bar=0.90,
        classifications={
            semantic: {"kind": "semantic", "criticality": "critical"},
            excluded: {
                "kind": "exception_prose_noncontractual",
                "criticality": "not_applicable",
            },
        },
    )
    assert score["machine_excluded"]["status_counts"]["killed"] == 1

    with pytest.raises(ValueError, match="classification identities"):
        mutation.score_mutation_rows(
            {semantic: "survived"},
            modules=("src/pkg/mod.py",),
            bar=0.90,
            classifications={},
        )


def _semantic_disposition_catalog(mutant: str) -> dict:
    return {
        "schema": "error_coupling_simulator.harness.semantic_mutant_catalog.v2",
        "classifier_policy": "conservative_exception_prose_ast.v2",
        "python_version": "3.test",
        "modules": {
            "src/pkg/mod.py": {
                "source_sha256": "a" * 64,
                "mutant_count": 1,
                "catalog_sha256": "b" * 64,
                "exception_prose_count": 0,
                "exception_prose_set_sha256": "c" * 64,
            }
        },
        "classifications": {
            mutant: {
                "kind": "semantic",
                "criticality": "critical",
                "module": "src/pkg/mod.py",
                "source_sha256": "a" * 64,
                "original_ast_sha256": "d" * 64,
                "mutant_ast_sha256": "e" * 64,
                "mutation_diff_sha256": "f" * 64,
            }
        },
    }


def test_semantic_disposition_authenticates_fingerprint_and_evidence(tmp_path) -> None:
    mutant = "pkg.mod.x_check__mutmut_1"
    evidence = tmp_path / "tests" / "test_mod.py"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("def test_witness(): pass\n", encoding="utf-8")
    path = tmp_path / "tests" / "_support" / "dispositions.json"
    path.parent.mkdir()
    path.write_text(
        json.dumps(
            {
                "schema": (
                    "error_coupling_simulator.harness."
                    "mutation_semantic_dispositions.v2"
                ),
                "classifier_policy": "conservative_exception_prose_ast.v2",
                "reviewed": [
                    {
                        "mutant": mutant,
                        "mutation_diff_sha256": "f" * 64,
                        "disposition": "reviewed_noncritical",
                        "reviewer": "restricted-mps-review",
                        "rationale": "Bounded API spelling mutation; semantic but noncritical.",
                        "evidence_locator": "tests/test_mod.py::test_witness",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    classifications, authentication = mutation.authenticate_semantic_dispositions(
        path,
        rows={mutant: "survived"},
        catalog=_semantic_disposition_catalog(mutant),
        repo=tmp_path,
    )

    assert classifications[mutant]["kind"] == "semantic"
    assert classifications[mutant]["criticality"] == "critical"
    assert classifications[mutant]["review"]["disposition"] == (
        "reviewed_noncritical"
    )
    assert authentication["reviewed_count"] == 1
    assert authentication["path"] == "tests/_support/dispositions.json"
    assert len(authentication["sha256"]) == 64


def test_reviewed_noncontractual_disposition_is_annotation_only(
    tmp_path,
) -> None:
    mutant = "pkg.mod.x_check__mutmut_1"
    evidence = tmp_path / "tests" / "test_mod.py"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("def test_witness(): pass\n", encoding="utf-8")
    path = tmp_path / "dispositions.json"
    path.write_text(
        json.dumps(
            {
                "schema": (
                    "error_coupling_simulator.harness."
                    "mutation_semantic_dispositions.v2"
                ),
                "classifier_policy": "conservative_exception_prose_ast.v2",
                "reviewed": [
                    {
                        "mutant": mutant,
                        "mutation_diff_sha256": "f" * 64,
                        "disposition": "reviewed_noncontractual",
                        "reviewer": "restricted-mps-review",
                        "rationale": (
                            "Exact review proves that only noncontractual "
                            "exception prose changes."
                        ),
                        "evidence_locator": "tests/test_mod.py::test_witness",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    classifications, authentication = mutation.authenticate_semantic_dispositions(
        path,
        rows={mutant: "survived"},
        catalog=_semantic_disposition_catalog(mutant),
        repo=tmp_path,
    )

    assert classifications[mutant]["kind"] == "semantic"
    assert classifications[mutant]["criticality"] == "critical"
    assert classifications[mutant]["review"]["disposition"] == (
        "reviewed_noncontractual"
    )
    assert authentication["reviewed_count"] == 1


def test_v2_human_annotation_never_changes_machine_classification(
    tmp_path: Path,
) -> None:
    mutant = "pkg.mod.x_check__mutmut_1"
    evidence = tmp_path / "tests" / "test_mod.py"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("def test_witness(): pass\n", encoding="utf-8")
    path = tmp_path / "annotations.json"
    path.write_text(
        json.dumps(
            {
                "schema": (
                    "error_coupling_simulator.harness."
                    "mutation_semantic_dispositions.v2"
                ),
                "classifier_policy": "conservative_exception_prose_ast.v2",
                "reviewed": [
                    {
                        "mutant": mutant,
                        "mutation_diff_sha256": "f" * 64,
                        "disposition": "reviewed_noncontractual",
                        "reviewer": "restricted-mps-review",
                        "rationale": "Human annotation only; no scoring authority.",
                        "evidence_locator": "tests/test_mod.py::test_witness",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    catalog = _semantic_disposition_catalog(mutant)
    machine_classification = json.loads(
        json.dumps(catalog["classifications"][mutant])
    )

    classifications, authentication = mutation.authenticate_semantic_dispositions(
        path,
        rows={mutant: "survived"},
        catalog=catalog,
        repo=tmp_path,
    )

    assert {
        key: value
        for key, value in classifications[mutant].items()
        if key != "review"
    } == machine_classification
    assert classifications[mutant]["kind"] == "semantic"
    assert classifications[mutant]["criticality"] == "critical"
    assert classifications[mutant]["review"]["disposition"] == (
        "reviewed_noncontractual"
    )
    assert authentication["applied_reviewed_count"] == 1


def test_global_disposition_scopes_reviews_to_the_current_batch_catalog(
    tmp_path,
) -> None:
    mutant = "pkg.mod.x_check__mutmut_1"
    other = "pkg.other.x_check__mutmut_1"
    evidence = tmp_path / "tests" / "test_mod.py"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("def test_witness(): pass\n", encoding="utf-8")

    def review(name: str, fingerprint: str) -> dict[str, str]:
        return {
            "mutant": name,
            "mutation_diff_sha256": fingerprint,
            "disposition": "reviewed_equivalent",
            "reviewer": "restricted-mps-review",
            "rationale": "Exact invariant proof for this generated mutation.",
            "evidence_locator": "tests/test_mod.py::test_witness",
        }

    path = tmp_path / "dispositions.json"
    path.write_text(
        json.dumps(
            {
                "schema": (
                    "error_coupling_simulator.harness."
                    "mutation_semantic_dispositions.v2"
                ),
                "classifier_policy": "conservative_exception_prose_ast.v2",
                "reviewed": [review(mutant, "f" * 64), review(other, "e" * 64)],
            }
        ),
        encoding="utf-8",
    )

    classifications, authentication = mutation.authenticate_semantic_dispositions(
        path,
        rows={mutant: "survived"},
        catalog=_semantic_disposition_catalog(mutant),
        repo=tmp_path,
    )

    assert classifications[mutant]["kind"] == "semantic"
    assert classifications[mutant]["criticality"] == "critical"
    assert authentication["reviewed_count"] == 2
    assert authentication["applied_reviewed_count"] == 1
    assert authentication["out_of_scope_reviewed_count"] == 1
    assert authentication["applied_mutants"] == [mutant]
    assert authentication["out_of_scope_mutants"] == [other]


def test_global_disposition_rejects_unknown_mutant_in_owned_scope(tmp_path) -> None:
    mutant = "pkg.mod.x_check__mutmut_1"
    stale = "pkg.mod.x_check__mutmut_999"
    evidence = tmp_path / "tests" / "test_mod.py"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("def test_witness(): pass\n", encoding="utf-8")
    path = tmp_path / "dispositions.json"
    path.write_text(
        json.dumps(
            {
                "schema": (
                    "error_coupling_simulator.harness."
                    "mutation_semantic_dispositions.v2"
                ),
                "classifier_policy": "conservative_exception_prose_ast.v2",
                "reviewed": [
                    {
                        "mutant": stale,
                        "mutation_diff_sha256": "e" * 64,
                        "disposition": "reviewed_equivalent",
                        "reviewer": "restricted-mps-review",
                        "rationale": "Stale generated identity must not be deferred.",
                        "evidence_locator": "tests/test_mod.py::test_witness",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unknown mutant in owned scope"):
        mutation.authenticate_semantic_dispositions(
            path,
            rows={mutant: "survived"},
            catalog=_semantic_disposition_catalog(mutant),
            repo=tmp_path,
        )


def test_global_disposition_validates_foreign_rows_before_deferring(tmp_path) -> None:
    mutant = "pkg.mod.x_check__mutmut_1"
    evidence = tmp_path / "tests" / "test_mod.py"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("def test_witness(): pass\n", encoding="utf-8")
    path = tmp_path / "dispositions.json"
    path.write_text(
        json.dumps(
            {
                "schema": (
                    "error_coupling_simulator.harness."
                    "mutation_semantic_dispositions.v2"
                ),
                "classifier_policy": "conservative_exception_prose_ast.v2",
                "reviewed": [
                    {
                        "mutant": "pkg.other.x_check__mutmut_1",
                        "mutation_diff_sha256": "NOT-A-SHA256",
                        "disposition": "reviewed_equivalent",
                        "reviewer": "restricted-mps-review",
                        "rationale": "Foreign rows still require global static validation.",
                        "evidence_locator": "tests/test_mod.py::test_witness",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="lowercase sha256"):
        mutation.authenticate_semantic_dispositions(
            path,
            rows={mutant: "survived"},
            catalog=_semantic_disposition_catalog(mutant),
            repo=tmp_path,
        )


def test_suite_disposition_partition_requires_every_review_exactly_once(
    tmp_path,
) -> None:
    first = "pkg.cpu.x_check__mutmut_1"
    second = "pkg.gpu.x_check__mutmut_1"
    path = tmp_path / "dispositions.json"
    path.write_text(
        json.dumps(
            {
                "schema": (
                    "error_coupling_simulator.harness."
                    "mutation_semantic_dispositions.v2"
                ),
                "classifier_policy": "conservative_exception_prose_ast.v2",
                "reviewed": [
                    {"mutant": first},
                    {"mutant": second},
                ],
            }
        ),
        encoding="utf-8",
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()

    def authentication(applied: str, out_of_scope: str) -> dict:
        return {
            "schema": (
                "error_coupling_simulator.harness."
                "mutation_semantic_dispositions.v2"
            ),
            "path": "dispositions.json",
            "sha256": digest,
            "classifier_policy": "conservative_exception_prose_ast.v2",
            "reviewed_count": 2,
            "applied_reviewed_count": 1,
            "out_of_scope_reviewed_count": 1,
            "applied_mutants": [applied],
            "out_of_scope_mutants": [out_of_scope],
        }

    batches = [
        {
            "tag": "cpu",
            "disposition_authentication": authentication(first, second),
        },
        {
            "tag": "gpu",
            "disposition_authentication": authentication(second, first),
        },
    ]

    result = mutation._authenticate_suite_disposition_partition(
        batches,
        disposition_path=path,
        repo=tmp_path,
    )

    assert result["reviewed_count"] == 2
    assert result["applied_exactly_once_count"] == 2
    duplicate = json.loads(json.dumps(batches))
    duplicate[1]["disposition_authentication"] = authentication(first, second)
    with pytest.raises(ValueError, match="exactly one batch"):
        mutation._authenticate_suite_disposition_partition(
            duplicate,
            disposition_path=path,
            repo=tmp_path,
        )


def test_suite_disposition_partition_rejects_batch_policy_mismatch(
    tmp_path,
) -> None:
    mutant = "pkg.cpu.x_check__mutmut_1"
    review = {
        "mutant": mutant,
        "mutation_diff_sha256": "f" * 64,
        "disposition": "reviewed_equivalent",
        "reviewer": "restricted-mps-review",
        "rationale": "Exact invariant proof for this generated mutation.",
        "evidence_locator": "tests/test_mod.py::test_witness",
    }
    path = tmp_path / "dispositions.json"
    path.write_text(
        json.dumps(
            {
                "schema": (
                    "error_coupling_simulator.harness."
                    "mutation_semantic_dispositions.v2"
                ),
                "classifier_policy": "conservative_exception_prose_ast.v2",
                "reviewed": [review],
            }
        ),
        encoding="utf-8",
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    batch = {
        "tag": "cpu",
        "disposition_authentication": {
            "schema": (
                "error_coupling_simulator.harness."
                "mutation_semantic_dispositions.v2"
            ),
            "path": "dispositions.json",
            "sha256": digest,
            "classifier_policy": "forged-policy",
            "reviewed_count": 1,
            "applied_reviewed_count": 1,
            "out_of_scope_reviewed_count": 0,
            "applied_mutants": [mutant],
            "out_of_scope_mutants": [],
            "scope_modules": ["src/pkg/cpu.py"],
            "scope_complete": True,
            "module_catalogs": {},
        },
        "semantic_classification": {
            "catalog": {"modules": {}},
            "classifications": {mutant: {"review": review}},
        },
    }

    with pytest.raises(ValueError, match="classifier policy mismatch"):
        mutation._authenticate_suite_disposition_partition(
            [batch],
            disposition_path=path,
            repo=tmp_path,
            require_classifications=True,
        )


def test_suite_disposition_partition_rejects_scope_catalog_mismatch(
    tmp_path,
) -> None:
    mutant = "pkg.owner.x_check__mutmut_1"
    review = {
        "mutant": mutant,
        "mutation_diff_sha256": "f" * 64,
        "disposition": "reviewed_equivalent",
        "reviewer": "restricted-mps-review",
        "rationale": "Exact invariant proof for this generated mutation.",
        "evidence_locator": "tests/test_mod.py::test_witness",
    }
    path = tmp_path / "dispositions.json"
    path.write_text(
        json.dumps(
            {
                "schema": (
                    "error_coupling_simulator.harness."
                    "mutation_semantic_dispositions.v2"
                ),
                "classifier_policy": "conservative_exception_prose_ast.v2",
                "reviewed": [review],
            }
        ),
        encoding="utf-8",
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    module_catalogs = {"src/pkg/owner.py": {"mutant_count": 1}}
    batch = {
        "tag": "owner",
        "disposition_authentication": {
            "schema": (
                "error_coupling_simulator.harness."
                "mutation_semantic_dispositions.v2"
            ),
            "path": "dispositions.json",
            "sha256": digest,
            "classifier_policy": "conservative_exception_prose_ast.v2",
            "reviewed_count": 1,
            "applied_reviewed_count": 1,
            "out_of_scope_reviewed_count": 0,
            "applied_mutants": [mutant],
            "out_of_scope_mutants": [],
            "scope_modules": ["src/pkg/forged.py"],
            "scope_complete": True,
            "module_catalogs": module_catalogs,
        },
        "semantic_classification": {
            "catalog": {"modules": module_catalogs},
            "classifications": {
                mutant: {"module": "src/pkg/owner.py", "review": review}
            },
        },
    }

    with pytest.raises(ValueError, match="scope modules mismatch"):
        mutation._authenticate_suite_disposition_partition(
            [batch],
            disposition_path=path,
            repo=tmp_path,
            require_classifications=True,
        )


@pytest.mark.parametrize(
    ("field", "value", "pattern"),
    [
        ("mutation_diff_sha256", "0" * 64, "fingerprint"),
        ("evidence_locator", "../outside.py", "evidence locator"),
        ("rationale", "", "rationale"),
    ],
)
def test_semantic_disposition_rejects_stale_or_unauditable_review(
    tmp_path,
    field: str,
    value: str,
    pattern: str,
) -> None:
    mutant = "pkg.mod.x_check__mutmut_1"
    evidence = tmp_path / "tests" / "test_mod.py"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("def test_witness(): pass\n", encoding="utf-8")
    row = {
        "mutant": mutant,
        "mutation_diff_sha256": "f" * 64,
        "disposition": "reviewed_equivalent",
        "reviewer": "restricted-mps-review",
        "rationale": "Algebraically identical on the declared domain.",
        "evidence_locator": "tests/test_mod.py::test_witness",
    }
    row[field] = value
    path = tmp_path / "dispositions.json"
    path.write_text(
        json.dumps(
            {
                "schema": (
                    "error_coupling_simulator.harness."
                    "mutation_semantic_dispositions.v2"
                ),
                "classifier_policy": "conservative_exception_prose_ast.v2",
                "reviewed": [row],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises((ValueError, FileNotFoundError), match=pattern):
        mutation.authenticate_semantic_dispositions(
            path,
            rows={mutant: "survived"},
            catalog=_semantic_disposition_catalog(mutant),
            repo=tmp_path,
        )


def test_batch_snapshot_includes_semantic_disposition_content(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    module = tmp_path / "src" / "pkg" / "mod.py"
    module.parent.mkdir(parents=True)
    module.write_text("VALUE = 1\n", encoding="utf-8")
    test_file = tmp_path / "tests" / "test_mod.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("def test_value(): pass\n", encoding="utf-8")
    disposition = tmp_path / "tests" / "_support" / "dispositions.json"
    disposition.parent.mkdir()
    disposition.write_text('{"reviewed": []}\n', encoding="utf-8")
    registry = tmp_path / "tests" / "_support" / "registry.json"
    registry.write_text("{}\n", encoding="utf-8")
    config = tmp_path / "tests" / "harness_config.json"
    config.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(mutation, "REPO", tmp_path)
    monkeypatch.setattr(mutation, "CONFIG_PATH", config)
    reg = {
        "reconcile_modules": ["src/pkg/mod.py"],
        "covered_by_test_files": ["tests/test_mod.py"],
        "semantic_dispositions": "tests/_support/dispositions.json",
    }

    paths = mutation._batch_snapshot_paths(registry, reg)
    before = mutation.input_snapshot(paths, repo=tmp_path)
    disposition.write_text('{"reviewed": ["changed"]}\n', encoding="utf-8")
    after = mutation.input_snapshot(paths, repo=tmp_path)

    assert disposition in paths
    assert after != before


def test_cpu_raw_meta_exit_three_is_suspicious_not_text_reported_killed(
    tmp_path,
) -> None:
    meta = tmp_path / "mutants" / "src" / "pkg" / "mod.py.meta"
    meta.parent.mkdir(parents=True)
    mutant = "pkg.mod.x_value__mutmut_1"
    meta.write_text(
        json.dumps(
            {
                "exit_code_by_key": {mutant: 3},
                "durations_by_key": {},
                "estimated_durations_by_key": {},
                "type_check_error_by_key": {},
            }
        ),
        encoding="utf-8",
    )

    rows, raw_codes = mutation._load_mutmut_meta_rows(
        ("src/pkg/mod.py",),
        repo=tmp_path,
    )
    mismatches = mutation._cross_check_mutmut_display(
        rows,
        {mutant: "killed"},
        raw_codes=raw_codes,
    )

    assert rows == {mutant: "suspicious"}
    assert raw_codes == {mutant: 3}
    assert mismatches == [
        {
            "mutant": mutant,
            "raw_exit_code": 3,
            "canonical_status": "suspicious",
            "display_status": "killed",
        }
    ]


def test_cpu_raw_meta_null_is_not_checked_and_rejected(tmp_path) -> None:
    meta = tmp_path / "mutants" / "src" / "pkg" / "mod.py.meta"
    meta.parent.mkdir(parents=True)
    mutant = "pkg.mod.x_value__mutmut_1"
    meta.write_text(
        json.dumps(
            {
                "exit_code_by_key": {mutant: None},
                "durations_by_key": {},
                "estimated_durations_by_key": {},
                "type_check_error_by_key": {},
            }
        ),
        encoding="utf-8",
    )

    rows, raw_codes = mutation._load_mutmut_meta_rows(
        ("src/pkg/mod.py",),
        repo=tmp_path,
    )

    assert rows == {mutant: "not_checked"}
    assert raw_codes == {mutant: None}
    with pytest.raises(ValueError, match="incomplete mutmut execution"):
        mutation.score_mutation_rows(
            rows,
            modules=("src/pkg/mod.py",),
            bar=0.9,
        )


def test_batch_snapshot_covers_all_mutmut_automatic_inputs(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    source = tmp_path / "src" / "pkg" / "mod.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_mod.py").write_text("def test_value(): pass\n", encoding="utf-8")
    conftest = tests / "conftest.py"
    conftest.write_text("VALUE = 1\n", encoding="utf-8")
    harness = tests / "harness"
    harness.mkdir()
    (harness / "mutation.py").write_text("# harness\n", encoding="utf-8")
    config = tests / "harness_config.json"
    config.write_text("{}\n", encoding="utf-8")
    setup = tmp_path / "setup.cfg"
    setup.write_text("[original]\n", encoding="utf-8")
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[build-system]\n", encoding="utf-8")
    registry = tmp_path / "registry.json"
    registry.write_text("{}\n", encoding="utf-8")
    reg = {
        "reconcile_modules": ["src/pkg/mod.py"],
        "covered_by_test_files": ["tests/test_mod.py"],
    }

    monkeypatch.setattr(mutation, "REPO", tmp_path)
    monkeypatch.setattr(mutation, "CONFIG_PATH", config)
    paths = mutation._batch_snapshot_paths(registry, reg)
    before = mutation.input_snapshot(paths, repo=tmp_path)
    conftest.write_text("VALUE = 2\n", encoding="utf-8")
    after = mutation.input_snapshot(paths, repo=tmp_path)

    assert tests in paths
    assert setup in paths
    assert pyproject in paths
    assert before != after


@pytest.mark.parametrize(
    ("bar", "multiplier", "constant", "pattern"),
    [
        (-1.0, 15.0, 1.0, "kill_rate_bar"),
        (float("nan"), 15.0, 1.0, "kill_rate_bar"),
        (0.9, 0.0, 1.0, "timeout_multiplier"),
        (0.9, float("inf"), 1.0, "timeout_multiplier"),
        (0.9, 15.0, -1.0, "timeout_constant"),
        (0.9, 15.0, float("nan"), "timeout_constant"),
    ],
)
def test_mutation_gate_knobs_reject_nonfinite_or_out_of_range_values(
    bar: float,
    multiplier: float,
    constant: float,
    pattern: str,
) -> None:
    with pytest.raises(ValueError, match=pattern):
        mutation._validate_mutation_gate_knobs(
            bar=bar,
            timeout_multiplier=multiplier,
            timeout_constant=constant,
        )


def test_environment_cannot_weaken_registered_mutation_bar(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ECS_MUT_BAR", "0.10")
    reg = {"harness": {"mutation_gate": {"kill_rate_bar": 0.90}}}

    with pytest.raises(ValueError, match="cannot weaken"):
        mutation._resolve_mutation_bar(reg)


def test_fresh_exec_plan_rejects_nonfinite_estimated_time(tmp_path) -> None:
    plan = tmp_path / "plan.json"
    plan.write_text(
        json.dumps(
            {
                "schema": (
                    "error_coupling_simulator.harness."
                    "mutation_fresh_exec_plan.v3"
                ),
                "generated_catalog_sha256": "a" * 64,
                "clean_control": {
                    "tests": ["tests/test_mod.py::test_value"],
                    "estimated_test_time": 0.1,
                },
                "mutants": [
                    {
                        "name": "pkg.mod.x_value__mutmut_1",
                        "tests": ["tests/test_mod.py::test_value"],
                        "estimated_test_time": float("nan"),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="estimated test time"):
        mutation._load_fresh_exec_plan(plan)


def test_fresh_exec_plan_identity_ignores_timing_but_binds_order_and_tests() -> None:
    plan = {
        "schema": (
            "error_coupling_simulator.harness.mutation_fresh_exec_plan.v3"
        ),
        "generated_catalog_sha256": "a" * 64,
        "clean_control": {
            "tests": ["tests/test_mod.py::test_value"],
            "estimated_test_time": 0.1,
        },
        "mutants": [
            {
                "name": "pkg.mod.x_value__mutmut_1",
                "tests": ["tests/test_mod.py::test_value"],
                "estimated_test_time": 0.1,
            },
            {
                "name": "pkg.mod.x_value__mutmut_2",
                "tests": ["tests/test_mod.py::test_value"],
                "estimated_test_time": 0.2,
            },
        ],
    }
    timing_drift = json.loads(json.dumps(plan))
    timing_drift["clean_control"]["estimated_test_time"] = 9.0
    timing_drift["mutants"][0]["estimated_test_time"] = 8.0
    timing_drift["mutants"][1]["estimated_test_time"] = 7.0

    identity = mutation._fresh_exec_plan_identity(plan)

    assert mutation._fresh_exec_plan_identity(timing_drift) == identity
    reordered = json.loads(json.dumps(plan))
    reordered["mutants"].reverse()
    assert mutation._fresh_exec_plan_identity(reordered) != identity
    changed_tests = json.loads(json.dumps(plan))
    changed_tests["mutants"][0]["tests"] = ["tests/test_mod.py::test_other"]
    assert mutation._fresh_exec_plan_identity(changed_tests) != identity
    changed_catalog = json.loads(json.dumps(plan))
    changed_catalog["generated_catalog_sha256"] = "b" * 64
    assert mutation._fresh_exec_plan_identity(changed_catalog) != identity


_GPU_TEST_RUNTIME_FINGERPRINT = {
    "schema": "test-runtime.v1",
    "sha256": "d" * 64,
}


def _gpu_test_execution_policy(jobs: int = 4) -> dict:
    env = mutation.lane_environment(
        {"CUDA_VISIBLE_DEVICES": "0", "ECS_GPU_SLOT": "0"},
        lane="gpu_serial",
    )
    return {
        **mutation.execution_policy(lane="gpu_serial", jobs=jobs),
        "timeout_multiplier": 15.0,
        "timeout_constant": 1.0,
        "explicit_timeout": None,
        "bound_environment": mutation._gpu_bound_environment(env),
        "device_identity": mutation._gpu_device_identity_document(
            slot=0,
            uuid="GPU-test",
            driver_version="test-driver",
        ),
    }


_GPU_TEST_EXECUTION_POLICY = _gpu_test_execution_policy(1)


def _write_fake_pytest_sentinel(
    sentinel_path: Path,
    *,
    exit_code: int,
    resource_exhaustion_kinds: tuple[str, ...] = (),
) -> None:
    kinds = sorted(set(resource_exhaustion_kinds))
    mutation.write_json_atomic(
        sentinel_path,
        {
            "schema": mutation._PYTEST_SENTINEL_SCHEMA,
            "completed": True,
            "pytest_exit_code": exit_code,
            "sentinel_name": sentinel_path.name,
            "resource_exhaustion_detected": bool(kinds),
            "resource_exhaustion_kinds": kinds,
        },
    )


def _prepared_gpu_plan(
    mutant_count: int,
    *,
    policy: dict,
) -> dict[str, object]:
    selected_tests = ["tests/test_mod.py::test_value"]
    plan = {
        "schema": mutation._FRESH_EXEC_PLAN_SCHEMA,
        "generated_catalog_sha256": "c" * 64,
        "clean_control": {
            "tests": selected_tests,
            "estimated_test_time": 0.1,
        },
        "mutants": [
            {
                "name": f"pkg.mod.x_value__mutmut_{index}",
                "tests": selected_tests,
                "estimated_test_time": 0.1,
            }
            for index in range(1, mutant_count + 1)
        ],
    }
    return {
        "tag": "gpu",
        "input_snapshot_sha256": "snapshot",
        "prepare": {"returncode": 0, "group_cleanup_verified": True},
        "plan": plan,
        "plan_sha256": "a" * 64,
        "plan_identity_sha256": mutation._fresh_exec_plan_identity(plan),
        "execution_policy": policy,
        "runtime_fingerprint": _GPU_TEST_RUNTIME_FINGERPRINT,
        "rows": {},
        "resumed_workers": [],
        "raw_plan_sha256_history": ["b" * 64],
    }


def test_gpu_authenticated_timeout_kill_is_checkpointed_and_resumed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    harness = tmp_path / "tests" / "harness"
    harness.mkdir(parents=True)
    (harness / "mutation.py").write_text("# harness\n", encoding="utf-8")
    (tmp_path / "mutants").mkdir()
    policy = _gpu_test_execution_policy(1)
    prepared = _prepared_gpu_plan(1, policy=policy)
    checkpoint = tmp_path / "checkpoint.json"
    calls: list[str] = []

    def fake_run(command, **kwargs):
        command = list(command)
        mutant = kwargs["env"]["MUTANT_UNDER_TEST"]
        calls.append(mutant)
        Path(kwargs["log_path"]).write_text(
            f"mutant={mutant}\n",
            encoding="utf-8",
        )
        sentinel_path = Path(command[command.index("--run-fresh-pytest") + 1])
        exit_code = 0 if mutant == "" else 1
        _write_fake_pytest_sentinel(sentinel_path, exit_code=exit_code)
        if mutant == "":
            return SimpleNamespace(
                ok=True,
                returncode=0,
                timed_out=False,
                group_cleanup_verified=True,
            )
        return SimpleNamespace(
            ok=False,
            returncode=-15,
            timed_out=True,
            group_cleanup_verified=True,
        )

    monkeypatch.setattr(mutation, "REPO", tmp_path)
    monkeypatch.setattr(mutation.proc, "run", fake_run)
    rows, _evidence = mutation._run_gpu_fresh_exec(
        tag="gpu",
        env={"CUDA_VISIBLE_DEVICES": "0", "ECS_GPU_SLOT": "0"},
        timeout=None,
        log=tmp_path / "mutation.log",
        plan_path=tmp_path / "plan.json",
        checkpoint_path=checkpoint,
        input_snapshot_sha256="snapshot",
        execution_policy=policy,
        runtime_fingerprint=_GPU_TEST_RUNTIME_FINGERPRINT,
        timeout_multiplier=15.0,
        timeout_constant=1.0,
        prepared=prepared,
    )

    assert calls == ["", "pkg.mod.x_value__mutmut_1"]
    assert rows == {"pkg.mod.x_value__mutmut_1": "killed"}
    checkpoint_doc = json.loads(checkpoint.read_text(encoding="utf-8"))
    worker = checkpoint_doc["completed_prefix"][0]
    assert worker["status"] == "killed"
    assert worker["timed_out"] is True
    assert worker["returncode"] == -15
    assert worker["completion_sentinel"]["pytest_exit_code"] == 1

    loaded_rows, loaded_workers, history = mutation._load_gpu_checkpoint(
        checkpoint,
        tag="gpu",
        input_snapshot_sha256="snapshot",
        plan=prepared["plan"],
        plan_identity_sha256=prepared["plan_identity_sha256"],
        raw_plan_sha256=prepared["plan_sha256"],
        execution_policy=policy,
        runtime_fingerprint=_GPU_TEST_RUNTIME_FINGERPRINT,
    )
    resumed = {
        **prepared,
        "rows": loaded_rows,
        "resumed_workers": loaded_workers,
        "raw_plan_sha256_history": history,
    }
    calls.clear()
    resumed_rows, resumed_evidence = mutation._run_gpu_fresh_exec(
        tag="gpu",
        env={"CUDA_VISIBLE_DEVICES": "0", "ECS_GPU_SLOT": "0"},
        timeout=None,
        log=tmp_path / "mutation.log",
        plan_path=tmp_path / "plan.json",
        checkpoint_path=checkpoint,
        input_snapshot_sha256="snapshot",
        execution_policy=policy,
        runtime_fingerprint=_GPU_TEST_RUNTIME_FINGERPRINT,
        timeout_multiplier=15.0,
        timeout_constant=1.0,
        prepared=resumed,
    )

    assert calls == [""]
    assert resumed_rows == rows
    assert resumed_evidence["checkpoint"]["resumed_prefix_count"] == 1


def test_gpu_mutant_worker_authenticates_only_a_durable_log(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    (tmp_path / "mutants").mkdir()
    mutant = "pkg.mod.x_value__mutmut_1"
    durable_paths: list[Path] = []
    real_durable_file_sha256 = mutation._durable_file_sha256
    real_sha256_file = mutation._sha256_file

    def fake_run(command, **kwargs):
        command = list(command)
        log_path = Path(kwargs["log_path"])
        log_path.write_text("authenticated worker evidence\n", encoding="utf-8")
        sentinel_path = Path(command[command.index("--run-fresh-pytest") + 1])
        _write_fake_pytest_sentinel(sentinel_path, exit_code=1)
        return SimpleNamespace(
            ok=False,
            returncode=1,
            timed_out=False,
            group_cleanup_verified=True,
        )

    def tracked_durable_file_sha256(path: Path) -> str:
        durable_paths.append(path)
        return real_durable_file_sha256(path)

    def reject_plain_worker_log_hash(path: Path) -> str:
        if path.name.startswith("gpu_worker_"):
            raise AssertionError("worker log bypassed durable authentication")
        return real_sha256_file(path)

    monkeypatch.setattr(mutation, "REPO", tmp_path)
    monkeypatch.setattr(mutation.proc, "run", fake_run)
    monkeypatch.setattr(mutation, "_durable_file_sha256", tracked_durable_file_sha256)
    monkeypatch.setattr(mutation, "_sha256_file", reject_plain_worker_log_hash)

    row = mutation._run_gpu_mutant_worker(
        tag="gpu",
        sequence_index=1,
        plan_row={
            "name": mutant,
            "tests": ["tests/test_mod.py::test_value"],
            "estimated_test_time": 0.1,
        },
        env={"CUDA_VISIBLE_DEVICES": "0", "ECS_GPU_SLOT": "0"},
        timeout=None,
        timeout_multiplier=15.0,
        timeout_constant=1.0,
        contention_factor=4,
        plan_path=tmp_path / "plan.json",
        log_root=tmp_path,
        cancellation_event=threading.Event(),
    )

    assert row["status"] == "killed"
    assert durable_paths == [tmp_path / row["log"]]


def test_gpu_fresh_exec_uses_four_clean_replicas_then_four_worker_waves(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    harness = tmp_path / "tests" / "harness"
    harness.mkdir(parents=True)
    (harness / "mutation.py").write_text("# harness\n", encoding="utf-8")
    (tmp_path / "mutants").mkdir()
    policy = _gpu_test_execution_policy(4)
    prepared = _prepared_gpu_plan(6, policy=policy)
    checkpoint = tmp_path / "checkpoint.json"
    state_lock = threading.Lock()
    clean_release = threading.Event()
    mutant_release = threading.Event()
    clean_active = 0
    mutant_active = 0
    max_clean_active = 0
    max_mutant_active = 0
    clean_sentinels: list[str] = []
    mutant_calls: list[str] = []
    automatic_timeouts: list[float] = []

    def fake_run(command, **kwargs):
        nonlocal clean_active, mutant_active, max_clean_active, max_mutant_active
        command = list(command)
        assert "--run-fresh-pytest" in command
        sentinel_path = Path(command[command.index("--run-fresh-pytest") + 1])
        mutant = kwargs["env"]["MUTANT_UNDER_TEST"]
        automatic_timeouts.append(kwargs["timeout"])
        Path(kwargs["log_path"]).write_text(
            f"worker={sentinel_path.name} mutant={mutant}\n",
            encoding="utf-8",
        )
        if mutant == "":
            with state_lock:
                clean_active += 1
                max_clean_active = max(max_clean_active, clean_active)
                clean_sentinels.append(sentinel_path.name)
                if clean_active == 4:
                    clean_release.set()
            try:
                if not clean_release.wait(2.0):
                    raise RuntimeError("four clean-control replicas were not concurrent")
            finally:
                with state_lock:
                    clean_active -= 1
            exit_code = 0
        else:
            with state_lock:
                mutant_active += 1
                max_mutant_active = max(max_mutant_active, mutant_active)
                mutant_calls.append(mutant)
                if mutant_active == 4:
                    mutant_release.set()
            try:
                if not mutant_release.wait(2.0):
                    raise RuntimeError("four mutant workers were not concurrent")
            finally:
                with state_lock:
                    mutant_active -= 1
            exit_code = 1
        _write_fake_pytest_sentinel(sentinel_path, exit_code=exit_code)
        return SimpleNamespace(
            ok=exit_code == 0,
            returncode=exit_code,
            timed_out=False,
            group_cleanup_verified=True,
        )

    monkeypatch.setattr(mutation, "REPO", tmp_path)
    monkeypatch.setattr(mutation.proc, "run", fake_run)

    rows, evidence = mutation._run_gpu_fresh_exec(
        tag="gpu",
        env={"CUDA_VISIBLE_DEVICES": "0", "ECS_GPU_SLOT": "0"},
        timeout=None,
        log=tmp_path / "mutation.log",
        plan_path=tmp_path / "plan.json",
        checkpoint_path=checkpoint,
        input_snapshot_sha256="snapshot",
        execution_policy=policy,
        runtime_fingerprint=_GPU_TEST_RUNTIME_FINGERPRINT,
        timeout_multiplier=15.0,
        timeout_constant=1.0,
        prepared=prepared,
    )

    assert max_clean_active == 4
    assert max_mutant_active == 4
    assert automatic_timeouts == pytest.approx([66.0] * 10)
    assert len(clean_sentinels) == 4
    assert len(set(clean_sentinels)) == 4
    assert sorted(mutant_calls) == [
        f"pkg.mod.x_value__mutmut_{index}" for index in range(1, 7)
    ]
    assert rows == {
        f"pkg.mod.x_value__mutmut_{index}": "killed"
        for index in range(1, 7)
    }
    workers = evidence["workers"]
    assert isinstance(workers, list)
    assert [worker["sequence_index"] for worker in workers] == list(range(1, 7))
    assert len({worker["log"] for worker in workers}) == 6
    assert len({worker["completion_sentinel"]["sha256"] for worker in workers}) == 6
    assert evidence["clean_control"]["replica_count"] == 4
    checkpoint_doc = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert [
        worker["sequence_index"] for worker in checkpoint_doc["completed_prefix"]
    ] == list(range(1, 7))


def test_gpu_parallel_wave_does_not_checkpoint_out_of_order_completion(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    harness = tmp_path / "tests" / "harness"
    harness.mkdir(parents=True)
    (harness / "mutation.py").write_text("# harness\n", encoding="utf-8")
    (tmp_path / "mutants").mkdir()
    policy = _gpu_test_execution_policy(4)
    prepared = _prepared_gpu_plan(5, policy=policy)
    checkpoint = tmp_path / "checkpoint.json"
    release_first = threading.Event()
    later_workers_done = threading.Event()
    state_lock = threading.Lock()
    completed_later = 0
    mutant_calls: list[str] = []
    result: dict[str, object] = {}
    errors: list[BaseException] = []

    def fake_run(command, **kwargs):
        nonlocal completed_later
        command = list(command)
        sentinel_path = Path(command[command.index("--run-fresh-pytest") + 1])
        mutant = kwargs["env"]["MUTANT_UNDER_TEST"]
        if mutant == "":
            time.sleep(0.01)
        if mutant:
            with state_lock:
                mutant_calls.append(mutant)
            sequence_index = int(mutant.rsplit("_", 1)[1])
            if sequence_index == 1:
                if not release_first.wait(3.0):
                    raise RuntimeError("first mutant was not released")
            elif sequence_index <= 4:
                with state_lock:
                    completed_later += 1
                    if completed_later == 3:
                        later_workers_done.set()
        Path(kwargs["log_path"]).write_text(
            f"mutant={mutant}\n",
            encoding="utf-8",
        )
        exit_code = 0 if mutant == "" else 1
        _write_fake_pytest_sentinel(sentinel_path, exit_code=exit_code)
        return SimpleNamespace(
            ok=exit_code == 0,
            returncode=exit_code,
            timed_out=False,
            group_cleanup_verified=True,
        )

    def orchestrate() -> None:
        try:
            rows, evidence = mutation._run_gpu_fresh_exec(
                tag="gpu",
                env={"CUDA_VISIBLE_DEVICES": "0", "ECS_GPU_SLOT": "0"},
                timeout=None,
                log=tmp_path / "mutation.log",
                plan_path=tmp_path / "plan.json",
                checkpoint_path=checkpoint,
                input_snapshot_sha256="snapshot",
                execution_policy=policy,
                runtime_fingerprint=_GPU_TEST_RUNTIME_FINGERPRINT,
                timeout_multiplier=15.0,
                timeout_constant=1.0,
                prepared=prepared,
            )
            result.update(rows=rows, evidence=evidence)
        except BaseException as exc:
            errors.append(exc)

    monkeypatch.setattr(mutation, "REPO", tmp_path)
    monkeypatch.setattr(mutation.proc, "run", fake_run)
    runner = threading.Thread(target=orchestrate, daemon=True)
    runner.start()
    assert later_workers_done.wait(2.0)
    assert not checkpoint.exists()
    assert not any(call.endswith("mutmut_5") for call in mutant_calls)
    release_first.set()
    runner.join(3.0)
    assert not runner.is_alive()
    assert errors == []
    assert len(result["rows"]) == 5
    checkpoint_doc = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert [
        row["sequence_index"] for row in checkpoint_doc["completed_prefix"]
    ] == [1, 2, 3, 4, 5]


def test_gpu_parallel_wave_resource_exhaustion_blocks_later_waves(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    harness = tmp_path / "tests" / "harness"
    harness.mkdir(parents=True)
    (harness / "mutation.py").write_text("# harness\n", encoding="utf-8")
    (tmp_path / "mutants").mkdir()
    policy = _gpu_test_execution_policy(4)
    prepared = _prepared_gpu_plan(6, policy=policy)
    checkpoint = tmp_path / "checkpoint.json"
    mutant_calls: list[str] = []

    def fake_run(command, **kwargs):
        command = list(command)
        sentinel_path = Path(command[command.index("--run-fresh-pytest") + 1])
        mutant = kwargs["env"]["MUTANT_UNDER_TEST"]
        if mutant == "":
            time.sleep(0.01)
        if mutant:
            mutant_calls.append(mutant)
        Path(kwargs["log_path"]).write_text(
            f"mutant={mutant}\n",
            encoding="utf-8",
        )
        is_oom = mutant.endswith("mutmut_1")
        exit_code = 0 if mutant == "" else 1
        _write_fake_pytest_sentinel(
            sentinel_path,
            exit_code=exit_code,
            resource_exhaustion_kinds=("cuda_oom",) if is_oom else (),
        )
        return SimpleNamespace(
            ok=exit_code == 0,
            returncode=exit_code,
            timed_out=False,
            group_cleanup_verified=True,
        )

    monkeypatch.setattr(mutation, "REPO", tmp_path)
    monkeypatch.setattr(mutation.proc, "run", fake_run)
    with pytest.raises(RuntimeError, match="non-resumable evidence"):
        mutation._run_gpu_fresh_exec(
            tag="gpu",
            env={"CUDA_VISIBLE_DEVICES": "0", "ECS_GPU_SLOT": "0"},
            timeout=None,
            log=tmp_path / "mutation.log",
            plan_path=tmp_path / "plan.json",
            checkpoint_path=checkpoint,
            input_snapshot_sha256="snapshot",
            execution_policy=policy,
            runtime_fingerprint=_GPU_TEST_RUNTIME_FINGERPRINT,
            timeout_multiplier=15.0,
            timeout_constant=1.0,
            prepared=prepared,
        )

    assert sorted(mutant_calls) == [
        f"pkg.mod.x_value__mutmut_{index}" for index in range(1, 5)
    ]
    assert not checkpoint.exists()


def test_later_gpu_oom_cancels_hanging_siblings_before_timeout(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    harness = tmp_path / "tests" / "harness"
    harness.mkdir(parents=True)
    (harness / "mutation.py").write_text("# harness\n", encoding="utf-8")
    (tmp_path / "mutants").mkdir()
    policy = _gpu_test_execution_policy(4)
    prepared = _prepared_gpu_plan(6, policy=policy)
    checkpoint = tmp_path / "checkpoint.json"
    mutant_calls: list[str] = []

    def fake_run(command, **kwargs):
        command = list(command)
        sentinel_path = Path(command[command.index("--run-fresh-pytest") + 1])
        mutant = kwargs["env"]["MUTANT_UNDER_TEST"]
        if mutant == "":
            time.sleep(0.01)
            Path(kwargs["log_path"]).write_text("clean\n", encoding="utf-8")
            _write_fake_pytest_sentinel(sentinel_path, exit_code=0)
            return SimpleNamespace(
                ok=True,
                returncode=0,
                timed_out=False,
                group_cleanup_verified=True,
            )
        mutant_calls.append(mutant)
        Path(kwargs["log_path"]).write_text(
            f"mutant={mutant}\n",
            encoding="utf-8",
        )
        if mutant.endswith("mutmut_4"):
            _write_fake_pytest_sentinel(
                sentinel_path,
                exit_code=1,
                resource_exhaustion_kinds=("cuda_out_of_memory",),
            )
            return SimpleNamespace(
                ok=False,
                returncode=1,
                timed_out=False,
                group_cleanup_verified=True,
            )
        cancellation = kwargs["cancellation_event"]
        if not cancellation.wait(1.0):
            raise RuntimeError("sibling cancellation was not delivered")
        return SimpleNamespace(
            ok=False,
            returncode=-15,
            timed_out=False,
            group_cleanup_verified=True,
        )

    monkeypatch.setattr(mutation, "REPO", tmp_path)
    monkeypatch.setattr(mutation.proc, "run", fake_run)
    started = time.monotonic()
    with pytest.raises(
        RuntimeError,
        match="GPU mutant worker 4 produced non-resumable evidence",
    ):
        mutation._run_gpu_fresh_exec(
            tag="gpu",
            env={"CUDA_VISIBLE_DEVICES": "0", "ECS_GPU_SLOT": "0"},
            timeout=None,
            log=tmp_path / "mutation.log",
            plan_path=tmp_path / "plan.json",
            checkpoint_path=checkpoint,
            input_snapshot_sha256="snapshot",
            execution_policy=policy,
            runtime_fingerprint=_GPU_TEST_RUNTIME_FINGERPRINT,
            timeout_multiplier=15.0,
            timeout_constant=1.0,
            prepared=prepared,
        )

    assert time.monotonic() - started < 1.0
    assert sorted(mutant_calls) == [
        f"pkg.mod.x_value__mutmut_{index}" for index in range(1, 5)
    ]
    assert not checkpoint.exists()


def test_gpu_parallel_wave_exception_checkpoints_only_safe_prefix(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    harness = tmp_path / "tests" / "harness"
    harness.mkdir(parents=True)
    (harness / "mutation.py").write_text("# harness\n", encoding="utf-8")
    (tmp_path / "mutants").mkdir()
    policy = _gpu_test_execution_policy(4)
    prepared = _prepared_gpu_plan(6, policy=policy)
    checkpoint = tmp_path / "checkpoint.json"
    mutant_calls: list[str] = []

    def fake_run(command, **kwargs):
        command = list(command)
        sentinel_path = Path(command[command.index("--run-fresh-pytest") + 1])
        mutant = kwargs["env"]["MUTANT_UNDER_TEST"]
        if mutant == "":
            time.sleep(0.01)
        if mutant:
            mutant_calls.append(mutant)
        if mutant.endswith("mutmut_2"):
            raise RuntimeError("injected second-worker failure")
        Path(kwargs["log_path"]).write_text(
            f"mutant={mutant}\n",
            encoding="utf-8",
        )
        exit_code = 0 if mutant == "" else 1
        _write_fake_pytest_sentinel(sentinel_path, exit_code=exit_code)
        return SimpleNamespace(
            ok=exit_code == 0,
            returncode=exit_code,
            timed_out=False,
            group_cleanup_verified=True,
        )

    monkeypatch.setattr(mutation, "REPO", tmp_path)
    monkeypatch.setattr(mutation.proc, "run", fake_run)
    with pytest.raises(RuntimeError, match="injected second-worker failure"):
        mutation._run_gpu_fresh_exec(
            tag="gpu",
            env={"CUDA_VISIBLE_DEVICES": "0", "ECS_GPU_SLOT": "0"},
            timeout=None,
            log=tmp_path / "mutation.log",
            plan_path=tmp_path / "plan.json",
            checkpoint_path=checkpoint,
            input_snapshot_sha256="snapshot",
            execution_policy=policy,
            runtime_fingerprint=_GPU_TEST_RUNTIME_FINGERPRINT,
            timeout_multiplier=15.0,
            timeout_constant=1.0,
            prepared=prepared,
        )

    assert sorted(mutant_calls) == [
        f"pkg.mod.x_value__mutmut_{index}" for index in range(1, 5)
    ]
    checkpoint_doc = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert [
        row["sequence_index"] for row in checkpoint_doc["completed_prefix"]
    ] == [1]


def test_gpu_clean_admission_oom_starts_no_mutants(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    harness = tmp_path / "tests" / "harness"
    harness.mkdir(parents=True)
    (harness / "mutation.py").write_text("# harness\n", encoding="utf-8")
    (tmp_path / "mutants").mkdir()
    policy = _gpu_test_execution_policy(4)
    prepared = _prepared_gpu_plan(2, policy=policy)
    checkpoint = tmp_path / "checkpoint.json"
    mutant_calls: list[str] = []

    def fake_run(command, **kwargs):
        command = list(command)
        sentinel_path = Path(command[command.index("--run-fresh-pytest") + 1])
        mutant = kwargs["env"]["MUTANT_UNDER_TEST"]
        if mutant:
            mutant_calls.append(mutant)
        Path(kwargs["log_path"]).write_text("clean admission\n", encoding="utf-8")
        _write_fake_pytest_sentinel(
            sentinel_path,
            exit_code=1,
            resource_exhaustion_kinds=("cuda_oom",),
        )
        return SimpleNamespace(
            ok=False,
            returncode=1,
            timed_out=False,
            group_cleanup_verified=True,
        )

    monkeypatch.setattr(mutation, "REPO", tmp_path)
    monkeypatch.setattr(mutation.proc, "run", fake_run)
    with pytest.raises(RuntimeError, match="clean admission detected"):
        mutation._run_gpu_fresh_exec(
            tag="gpu",
            env={"CUDA_VISIBLE_DEVICES": "0", "ECS_GPU_SLOT": "0"},
            timeout=None,
            log=tmp_path / "mutation.log",
            plan_path=tmp_path / "plan.json",
            checkpoint_path=checkpoint,
            input_snapshot_sha256="snapshot",
            execution_policy=policy,
            runtime_fingerprint=_GPU_TEST_RUNTIME_FINGERPRINT,
            timeout_multiplier=15.0,
            timeout_constant=1.0,
            prepared=prepared,
        )

    assert mutant_calls == []
    assert not checkpoint.exists()


def _authenticated_gpu_checkpoint_fixture(tmp_path: Path) -> tuple[dict, dict]:
    plan = {
        "schema": (
            "error_coupling_simulator.harness.mutation_fresh_exec_plan.v3"
        ),
        "generated_catalog_sha256": "c" * 64,
        "clean_control": {
            "tests": ["tests/test_mod.py::test_value"],
            "estimated_test_time": 0.1,
        },
        "mutants": [
            {
                "name": "pkg.mod.x_value__mutmut_1",
                "tests": ["tests/test_mod.py::test_value"],
                "estimated_test_time": 0.1,
            }
        ],
    }
    mutant = plan["mutants"][0]["name"]
    log_name = mutation._gpu_worker_log_name("gpu", 1, mutant)
    sentinel_name = mutation._gpu_worker_sentinel_name("gpu", 1)
    log_path = tmp_path / log_name
    log_path.write_text("authenticated worker evidence\n", encoding="utf-8")
    checkpoint = {
        "schema": mutation._GPU_CHECKPOINT_SCHEMA,
        "tag": "gpu",
        "lane": "gpu_serial",
        "input_snapshot_sha256": "snapshot",
        "plan_schema": plan["schema"],
        "plan_identity_sha256": mutation._fresh_exec_plan_identity(plan),
        "generated_catalog_sha256": plan["generated_catalog_sha256"],
        "plan_mutant_count": 1,
        "execution_policy": _GPU_TEST_EXECUTION_POLICY,
        "runtime_fingerprint": _GPU_TEST_RUNTIME_FINGERPRINT,
        "raw_plan_sha256_history": ["a" * 64],
        "completed_prefix": [
            {
                "sequence_index": 1,
                "mutant": "pkg.mod.x_value__mutmut_1",
                "tests": ["tests/test_mod.py::test_value"],
                "estimated_test_time": 0.1,
                "effective_timeout": 2.0,
                "status": "killed",
                "process_executed": True,
                "completion_sentinel_authenticated": True,
                "completion_sentinel": {
                    "schema": mutation._PYTEST_SENTINEL_SCHEMA,
                    "sha256": mutation._completion_sentinel_sha256(
                        1,
                        sentinel_name=sentinel_name,
                    ),
                    "pytest_exit_code": 1,
                    "sentinel_name": sentinel_name,
                    "resource_exhaustion_detected": False,
                    "resource_exhaustion_kinds": [],
                },
                "returncode": 1,
                "timed_out": False,
                "group_cleanup_verified": True,
                "ok": False,
                "log": log_name,
                "log_sha256": mutation._sha256_file(log_path),
            }
        ],
    }
    return plan, checkpoint


def test_gpu_checkpoint_resumes_authenticated_resource_clean_timeout_kill(
    tmp_path: Path,
) -> None:
    plan, checkpoint = _authenticated_gpu_checkpoint_fixture(tmp_path)
    checkpoint["completed_prefix"][0]["timed_out"] = True
    checkpoint["completed_prefix"][0]["returncode"] = -15
    checkpoint_path = tmp_path / "checkpoint.json"
    checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")

    rows, workers, history = mutation._load_gpu_checkpoint(
        checkpoint_path,
        tag="gpu",
        input_snapshot_sha256="snapshot",
        plan=plan,
        plan_identity_sha256=mutation._fresh_exec_plan_identity(plan),
        raw_plan_sha256="b" * 64,
        execution_policy=_GPU_TEST_EXECUTION_POLICY,
        runtime_fingerprint=_GPU_TEST_RUNTIME_FINGERPRINT,
    )

    assert rows == {"pkg.mod.x_value__mutmut_1": "killed"}
    assert workers[0]["timed_out"] is True
    assert workers[0]["status"] == "killed"
    assert history == ["a" * 64, "b" * 64]


@pytest.mark.parametrize(
    ("corrupt", "error_type", "match"),
    [
        (
            lambda doc: doc.update(schema="unsupported"),
            ValueError,
            "checkpoint schema",
        ),
        (
            lambda doc: doc.update(tag="other"),
            ValueError,
            "batch identity",
        ),
        (
            lambda doc: doc.update(input_snapshot_sha256="drift"),
            RuntimeError,
            "input snapshot mismatch",
        ),
        (
            lambda doc: doc.update(plan_identity_sha256="0" * 64),
            RuntimeError,
            "semantic plan mismatch",
        ),
        (
            lambda doc: doc.update(generated_catalog_sha256="0" * 64),
            RuntimeError,
            "semantic plan mismatch",
        ),
        (
            lambda doc: doc.update(plan_mutant_count=2),
            RuntimeError,
            "semantic plan mismatch",
        ),
        (
            lambda doc: doc.update(execution_policy={"lane": "cpu_parallel"}),
            RuntimeError,
            "execution policy mismatch",
        ),
        (
            lambda doc: doc.update(runtime_fingerprint={"sha256": "0" * 64}),
            RuntimeError,
            "runtime fingerprint mismatch",
        ),
        (
            lambda doc: doc.update(raw_plan_sha256_history=["z" * 64]),
            ValueError,
            "raw plan history",
        ),
        (
            lambda doc: doc["completed_prefix"][0].update(sequence_index=2),
            ValueError,
            "not contiguous",
        ),
        (
            lambda doc: doc["completed_prefix"][0].update(mutant="other"),
            ValueError,
            "mutant identity",
        ),
        (
            lambda doc: doc["completed_prefix"][0]["completion_sentinel"].update(
                sha256="0" * 64
            ),
            ValueError,
            "sentinel digest",
        ),
        (
            lambda doc: doc["completed_prefix"][0].update(log_sha256="0" * 64),
            ValueError,
            "worker log digest mismatch",
        ),
        (
            lambda doc: doc["completed_prefix"][0].update(
                group_cleanup_verified=False
            ),
            ValueError,
            "cleanup",
        ),
        (
            lambda doc: doc["completed_prefix"][0].update(ok=True),
            ValueError,
            "ok flag",
        ),
        (
            lambda doc: doc["completed_prefix"][0].update(status="survived"),
            ValueError,
            "worker status",
        ),
        (
            lambda doc: doc["completed_prefix"][0].update(
                status="suspicious",
                completion_sentinel_authenticated=False,
                completion_sentinel=None,
                returncode=2,
            ),
            ValueError,
            "authenticated completion sentinel",
        ),
    ],
)
def test_gpu_checkpoint_rejects_corruption(
    tmp_path,
    corrupt,
    error_type: type[Exception],
    match: str,
) -> None:
    plan, checkpoint = _authenticated_gpu_checkpoint_fixture(tmp_path)
    checkpoint = json.loads(json.dumps(checkpoint))
    corrupt(checkpoint)
    path = tmp_path / "checkpoint.json"
    path.write_text(json.dumps(checkpoint), encoding="utf-8")

    with pytest.raises(error_type, match=match):
        mutation._load_gpu_checkpoint(
            path,
            tag="gpu",
            input_snapshot_sha256="snapshot",
            plan=plan,
            plan_identity_sha256=mutation._fresh_exec_plan_identity(plan),
            raw_plan_sha256="b" * 64,
            execution_policy=_GPU_TEST_EXECUTION_POLICY,
            runtime_fingerprint=_GPU_TEST_RUNTIME_FINGERPRINT,
        )


def test_gpu_checkpoint_rejects_a_worker_log_truncated_after_publication(
    tmp_path: Path,
) -> None:
    plan, checkpoint = _authenticated_gpu_checkpoint_fixture(tmp_path)
    checkpoint_path = tmp_path / "checkpoint.json"
    checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")
    worker_log = tmp_path / checkpoint["completed_prefix"][0]["log"]
    worker_log.write_bytes(b"")

    with pytest.raises(ValueError, match="worker log digest mismatch"):
        mutation._load_gpu_checkpoint(
            checkpoint_path,
            tag="gpu",
            input_snapshot_sha256="snapshot",
            plan=plan,
            plan_identity_sha256=mutation._fresh_exec_plan_identity(plan),
            raw_plan_sha256="b" * 64,
            execution_policy=_GPU_TEST_EXECUTION_POLICY,
            runtime_fingerprint=_GPU_TEST_RUNTIME_FINGERPRINT,
        )


def test_mutants_tree_cleanup_fails_if_directory_survives(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    mutants = tmp_path / "mutants"
    mutants.mkdir()
    monkeypatch.setattr(mutation.shutil, "rmtree", lambda _path: None)

    with pytest.raises(RuntimeError, match="mutants tree"):
        mutation._clear_mutants_tree(repo=tmp_path)


def test_mutants_tree_cleanup_recovers_read_only_tree_after_abrupt_exit(
    tmp_path: Path,
) -> None:
    root = tmp_path / "mutants"
    package = root / "src" / "pkg"
    package.mkdir(parents=True)
    module = package / "mod.py"
    module.write_text("VALUE = 1\n", encoding="utf-8")

    frozen = mutation._make_generated_tree_read_only(root)
    try:
        mutation._clear_mutants_tree(repo=tmp_path)
    finally:
        if root.exists():
            mutation._restore_generated_tree_modes(frozen)

    assert not root.exists()


def test_generated_mutant_tree_is_read_only_during_workers_and_modes_restore(
    tmp_path: Path,
) -> None:
    root = tmp_path / "mutants"
    package = root / "src" / "pkg"
    package.mkdir(parents=True)
    module = package / "mod.py"
    module.write_text("VALUE = 1\n", encoding="utf-8")
    package.chmod(0o750)
    module.chmod(0o640)

    frozen = mutation._make_generated_tree_read_only(root)
    try:
        assert package.stat().st_mode & 0o222 == 0
        assert module.stat().st_mode & 0o222 == 0
    finally:
        mutation._restore_generated_tree_modes(frozen)

    assert package.stat().st_mode & 0o777 == 0o750
    assert module.stat().st_mode & 0o777 == 0o640


@pytest.mark.parametrize("returncode", [1, 2])
def test_batch_failure_retires_old_pass_and_restores_setup(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    returncode: int,
) -> None:
    module = tmp_path / "src" / "pkg" / "mod.py"
    module.parent.mkdir(parents=True)
    module.write_text("VALUE = 1\n", encoding="utf-8")
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_mod.py").write_text("def test_value(): pass\n", encoding="utf-8")
    harness = tests / "harness"
    harness.mkdir()
    (harness / "mutation.py").write_text("# harness\n", encoding="utf-8")
    config = tests / "harness_config.json"
    config.write_text("{}\n", encoding="utf-8")
    registry = tmp_path / "cpu.json"
    registry.write_text(
        json.dumps(
            {
                "schema": "error_coupling_simulator.harness.mutation_batch.v1",
                "lane": "cpu_parallel",
                "requires_gpu": False,
                "reconcile_modules": ["src/pkg/mod.py"],
                "covered_by_test_files": ["tests/test_mod.py"],
                "harness": {
                    "mutation_gate": {"kill_rate_bar": 0.9, "jobs": 4}
                },
            }
        ),
        encoding="utf-8",
    )
    setup = tmp_path / "setup.cfg"
    setup.write_text("[original]\n", encoding="utf-8")
    logs = tmp_path / "logs"
    logs.mkdir()
    old_result = logs / "cpu_mutation_survivors.json"
    old_result.write_text('{"pass": true}\n', encoding="utf-8")
    calls: list[list[str]] = []

    def fake_run(command, **_kwargs):
        calls.append(list(command))
        return SimpleNamespace(
            ok=False,
            returncode=returncode,
            timed_out=False,
            group_cleanup_verified=True,
        )

    monkeypatch.setattr(mutation, "REPO", tmp_path)
    monkeypatch.setattr(mutation, "LOGDIR", logs)
    monkeypatch.setattr(mutation, "CONFIG_PATH", config)
    monkeypatch.setattr(mutation.proc, "run", fake_run)

    with pytest.raises(RuntimeError, match="mutmut run failed"):
        mutation.run_mutation(str(registry))

    assert not old_result.exists()
    assert setup.read_text(encoding="utf-8") == "[original]\n"
    assert calls == [["mutmut", "run", "--max-children", "4"]]


def test_gpu_fresh_exec_stops_before_mutants_when_clean_child_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    harness = tmp_path / "tests" / "harness"
    harness.mkdir(parents=True)
    (harness / "mutation.py").write_text("# harness\n", encoding="utf-8")
    mutants = tmp_path / "mutants"
    mutants.mkdir()
    log = tmp_path / "mutation.log"
    plan_path = tmp_path / "plan.json"
    calls: list[tuple[list[str], dict]] = []

    def fake_run(command, **kwargs):
        command = list(command)
        calls.append((command, kwargs))
        if "--prepare-fresh-exec" in command:
            plan_path.write_text(
                json.dumps(
                    {
                        "schema": (
                            "error_coupling_simulator.harness."
                            "mutation_fresh_exec_plan.v3"
                        ),
                        "generated_catalog_sha256": "c" * 64,
                        "clean_control": {
                            "tests": ["tests/test_mod.py::test_value"],
                            "estimated_test_time": 0.1,
                        },
                        "mutants": [
                            {
                                "name": "pkg.mod.x_value__mutmut_1",
                                "tests": ["tests/test_mod.py::test_value"],
                                "estimated_test_time": 0.1,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            return SimpleNamespace(
                ok=True,
                returncode=0,
                timed_out=False,
                group_cleanup_verified=True,
            )
        sentinel_path = Path(command[command.index("--run-fresh-pytest") + 1])
        _write_fake_pytest_sentinel(sentinel_path, exit_code=1)
        return SimpleNamespace(
            ok=False,
            returncode=1,
            timed_out=False,
            group_cleanup_verified=True,
        )

    monkeypatch.setattr(mutation, "REPO", tmp_path)
    monkeypatch.setattr(mutation.proc, "run", fake_run)

    with pytest.raises(RuntimeError, match="clean control failed"):
        mutation._run_gpu_fresh_exec(
            tag="gpu",
            env={"CUDA_VISIBLE_DEVICES": "0", "ECS_GPU_SLOT": "0"},
            timeout=10.0,
            log=log,
            plan_path=plan_path,
            checkpoint_path=tmp_path / "checkpoint.json",
            input_snapshot_sha256="snapshot",
            execution_policy={
                **_GPU_TEST_EXECUTION_POLICY,
                "explicit_timeout": 10.0,
            },
            runtime_fingerprint=_GPU_TEST_RUNTIME_FINGERPRINT,
            timeout_multiplier=15.0,
            timeout_constant=1.0,
        )

    assert len(calls) == 2
    assert calls[1][1]["env"]["MUTANT_UNDER_TEST"] == ""


def test_gpu_checkpoint_resumes_only_authenticated_contiguous_prefix(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    harness = tmp_path / "tests" / "harness"
    harness.mkdir(parents=True)
    (harness / "mutation.py").write_text("# harness\n", encoding="utf-8")
    (tmp_path / "mutants").mkdir()
    log = tmp_path / "mutation.log"
    plan_path = tmp_path / "plan.json"
    checkpoint = tmp_path / "checkpoint.json"
    phase = {"value": 1}
    fresh_calls: list[str] = []

    def write_plan(estimated: float) -> None:
        plan_path.write_text(
            json.dumps(
                {
                    "schema": (
                        "error_coupling_simulator.harness."
                        "mutation_fresh_exec_plan.v3"
                    ),
                    "generated_catalog_sha256": "c" * 64,
                    "clean_control": {
                        "tests": ["tests/test_mod.py::test_value"],
                        "estimated_test_time": estimated,
                    },
                    "mutants": [
                        {
                            "name": "pkg.mod.x_value__mutmut_1",
                            "tests": ["tests/test_mod.py::test_value"],
                            "estimated_test_time": estimated,
                        },
                        {
                            "name": "pkg.mod.x_value__mutmut_2",
                            "tests": ["tests/test_mod.py::test_value"],
                            "estimated_test_time": estimated,
                        },
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    def fake_run(command, **kwargs):
        command = list(command)
        if "--prepare-fresh-exec" in command:
            write_plan(0.1 if phase["value"] == 1 else 0.9)
            return SimpleNamespace(
                ok=True,
                returncode=0,
                timed_out=False,
                group_cleanup_verified=True,
            )
        mutant = kwargs["env"]["MUTANT_UNDER_TEST"]
        fresh_calls.append(mutant)
        if phase["value"] == 1 and mutant.endswith("mutmut_2"):
            raise RuntimeError("injected worker interruption")
        exit_code = 0 if mutant == "" else 1
        Path(kwargs["log_path"]).write_text(
            f"mutant={mutant}\n",
            encoding="utf-8",
        )
        sentinel_path = Path(command[command.index("--run-fresh-pytest") + 1])
        _write_fake_pytest_sentinel(sentinel_path, exit_code=exit_code)
        return SimpleNamespace(
            ok=exit_code == 0,
            returncode=exit_code,
            timed_out=False,
            group_cleanup_verified=True,
        )

    monkeypatch.setattr(mutation, "REPO", tmp_path)
    monkeypatch.setattr(mutation.proc, "run", fake_run)

    with pytest.raises(RuntimeError, match="injected worker interruption"):
        mutation._run_gpu_fresh_exec(
            tag="gpu",
            env={"CUDA_VISIBLE_DEVICES": "0", "ECS_GPU_SLOT": "0"},
            timeout=None,
            log=log,
            plan_path=plan_path,
            checkpoint_path=checkpoint,
            input_snapshot_sha256="snapshot",
            execution_policy=_GPU_TEST_EXECUTION_POLICY,
            runtime_fingerprint=_GPU_TEST_RUNTIME_FINGERPRINT,
            timeout_multiplier=15.0,
            timeout_constant=1.0,
        )

    checkpoint_doc = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert [row["mutant"] for row in checkpoint_doc["completed_prefix"]] == [
        "pkg.mod.x_value__mutmut_1"
    ]
    assert not checkpoint.with_name(f".{checkpoint.name}.tmp").exists()

    phase["value"] = 2
    fresh_calls.clear()
    rows, evidence = mutation._run_gpu_fresh_exec(
        tag="gpu",
        env={"CUDA_VISIBLE_DEVICES": "0", "ECS_GPU_SLOT": "0"},
        timeout=None,
        log=log,
        plan_path=plan_path,
        checkpoint_path=checkpoint,
        input_snapshot_sha256="snapshot",
        execution_policy=_GPU_TEST_EXECUTION_POLICY,
        runtime_fingerprint=_GPU_TEST_RUNTIME_FINGERPRINT,
        timeout_multiplier=15.0,
        timeout_constant=1.0,
    )

    assert fresh_calls == ["", "pkg.mod.x_value__mutmut_2"]
    assert rows == {
        "pkg.mod.x_value__mutmut_1": "killed",
        "pkg.mod.x_value__mutmut_2": "killed",
    }
    assert evidence["checkpoint"]["resumed_prefix_count"] == 1
    assert len(json.loads(checkpoint.read_text(encoding="utf-8"))["completed_prefix"]) == 2


def test_gpu_resume_rechecks_clean_and_preserves_checkpoint_on_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    harness = tmp_path / "tests" / "harness"
    harness.mkdir(parents=True)
    (harness / "mutation.py").write_text("# harness\n", encoding="utf-8")
    (tmp_path / "mutants").mkdir()
    plan, checkpoint_doc = _authenticated_gpu_checkpoint_fixture(tmp_path)
    plan_path = tmp_path / "plan.json"
    checkpoint_path = tmp_path / "checkpoint.json"
    checkpoint_path.write_text(
        json.dumps(checkpoint_doc, indent=2) + "\n",
        encoding="utf-8",
    )
    checkpoint_before = checkpoint_path.read_bytes()
    fresh_mutants: list[str] = []

    def fake_run(command, **kwargs):
        command = list(command)
        if "--prepare-fresh-exec" in command:
            plan_path.write_text(
                json.dumps(plan, indent=2) + "\n",
                encoding="utf-8",
            )
            return SimpleNamespace(
                ok=True,
                returncode=0,
                timed_out=False,
                group_cleanup_verified=True,
            )
        fresh_mutants.append(kwargs["env"]["MUTANT_UNDER_TEST"])
        sentinel_path = Path(command[command.index("--run-fresh-pytest") + 1])
        _write_fake_pytest_sentinel(sentinel_path, exit_code=1)
        return SimpleNamespace(
            ok=False,
            returncode=1,
            timed_out=False,
            group_cleanup_verified=True,
        )

    monkeypatch.setattr(mutation, "REPO", tmp_path)
    monkeypatch.setattr(mutation.proc, "run", fake_run)

    with pytest.raises(RuntimeError, match="clean control failed"):
        mutation._run_gpu_fresh_exec(
            tag="gpu",
            env={"CUDA_VISIBLE_DEVICES": "0", "ECS_GPU_SLOT": "0"},
            timeout=None,
            log=tmp_path / "mutation.log",
            plan_path=plan_path,
            checkpoint_path=checkpoint_path,
            input_snapshot_sha256="snapshot",
            execution_policy=_GPU_TEST_EXECUTION_POLICY,
            runtime_fingerprint=_GPU_TEST_RUNTIME_FINGERPRINT,
            timeout_multiplier=15.0,
            timeout_constant=1.0,
        )

    assert fresh_mutants == [""]
    assert checkpoint_path.read_bytes() == checkpoint_before


def test_stale_setup_backup_and_absence_marker_are_recoverable(tmp_path) -> None:
    setup = tmp_path / "setup.cfg"
    backup = tmp_path / "backup"
    marker = tmp_path / "absent"
    setup.write_text("[mutmut]\n", encoding="utf-8")
    backup.write_text("[original]\n", encoding="utf-8")

    mutation._recover_stale_setup_state(
        setup=setup,
        backup=backup,
        absent_marker=marker,
    )

    assert setup.read_text(encoding="utf-8") == "[original]\n"
    assert not backup.exists()
    setup.write_text("[mutmut]\n", encoding="utf-8")
    marker.write_text("absent\n", encoding="utf-8")
    mutation._recover_stale_setup_state(
        setup=setup,
        backup=backup,
        absent_marker=marker,
    )
    assert not setup.exists()
    assert not marker.exists()


def test_new_batch_recovers_global_setup_backup_left_by_different_tag(
    tmp_path,
) -> None:
    setup = tmp_path / "setup.cfg"
    global_backup = tmp_path / ".setup.cfg.bak"
    global_marker = tmp_path / ".setup.cfg.absent"
    setup.write_text("[mutmut]\nsource_paths=tag_a.py\n", encoding="utf-8")
    global_backup.write_text("[original]\n", encoding="utf-8")

    had_config = mutation._begin_setup_override(
        setup=setup,
        backup=global_backup,
        absent_marker=global_marker,
    )

    assert had_config is True
    assert setup.read_text(encoding="utf-8") == "[original]\n"
    assert global_backup.read_text(encoding="utf-8") == "[original]\n"
    mutation._restore_setup_override(
        setup=setup,
        backup=global_backup,
        absent_marker=global_marker,
        had_config=had_config,
    )
    assert setup.read_text(encoding="utf-8") == "[original]\n"


def test_partial_setup_backup_copy_never_publishes_recoverable_backup(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    setup = tmp_path / "setup.cfg"
    backup = tmp_path / ".setup.cfg.bak"
    marker = tmp_path / ".setup.cfg.absent"
    setup.write_text("[original]\n", encoding="utf-8")

    def partial_copy(_source, destination):
        Path(destination).write_text("[truncated", encoding="utf-8")
        raise OSError("injected partial copy")

    monkeypatch.setattr(mutation.shutil, "copy2", partial_copy)

    with pytest.raises(OSError, match="injected partial copy"):
        mutation._begin_setup_override(
            setup=setup,
            backup=backup,
            absent_marker=marker,
        )

    assert setup.read_text(encoding="utf-8") == "[original]\n"
    assert not backup.exists()
    assert not backup.with_name(f".{backup.name}.tmp").exists()


def test_direct_mutation_rejects_schema_less_coverage_registry(tmp_path) -> None:
    registry = tmp_path / "coverage.json"
    registry.write_text(
        json.dumps(
            {
                "reconcile_modules": ["src/pkg/mod.py"],
                "covered_by_test_files": ["tests/test_mod.py"],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="mutation_batch.v1"):
        mutation.run_mutation(str(registry))


@pytest.mark.parametrize("value", [float("nan"), float("inf"), 0.0, -1.0])
def test_explicit_mutation_timeout_must_be_finite_positive(value: float) -> None:
    with pytest.raises(ValueError, match="explicit mutation timeout"):
        mutation._effective_worker_timeout(
            explicit_timeout=value,
            estimated_test_time=1.0,
            timeout_multiplier=15.0,
            timeout_constant=1.0,
        )


def test_gpu4_automatic_timeout_scales_for_contention_but_explicit_timeout_does_not() -> None:
    estimated = 0.10633709101966815

    assert mutation._effective_worker_timeout(
        explicit_timeout=None,
        estimated_test_time=estimated,
        timeout_multiplier=15.0,
        timeout_constant=1.0,
        contention_factor=4,
    ) == pytest.approx((estimated + 1.0) * 15.0 * 4.0)
    assert mutation._effective_worker_timeout(
        explicit_timeout=23.0,
        estimated_test_time=estimated,
        timeout_multiplier=15.0,
        timeout_constant=1.0,
        contention_factor=4,
    ) == 23.0
