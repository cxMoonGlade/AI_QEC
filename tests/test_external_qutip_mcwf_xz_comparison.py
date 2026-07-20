"""Contract tests for the isolated QuTiP MCWF X/Z Record comparator."""

from __future__ import annotations

import ast
import copy
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import pytest


REPO = Path(__file__).resolve().parents[1]
PROTOCOL = (
    REPO
    / "scripts"
    / "external_baselines"
    / "qutip_mcwf_xz_protocol.py"
)
FIXTURE = (
    REPO
    / "scripts"
    / "external_baselines"
    / "fixtures"
    / "qutip_mcwf_xz_two_qubit_t1.json"
)
QUTIP_WORKER = (
    REPO
    / "scripts"
    / "external_baselines"
    / "qutip_mcwf_xz_worker.py"
)
COMPARATOR = (
    REPO
    / "scripts"
    / "external_baselines"
    / "run_qutip_mcwf_xz_comparison.py"
)


def _load_protocol():
    spec = importlib.util.spec_from_file_location("qutip_mcwf_xz_protocol", PROTOCOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_comparator(monkeypatch):
    protocol = _load_protocol()
    monkeypatch.setitem(sys.modules, "qutip_mcwf_xz_protocol", protocol)
    spec = importlib.util.spec_from_file_location(
        "run_qutip_mcwf_xz_comparison_under_test",
        COMPARATOR,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_neutral_fixture_binds_ordered_xz_reset_contract_and_analytic_law():
    protocol = _load_protocol()
    fixture = protocol.load_fixture(FIXTURE)

    assert fixture["schema"] == (
        "error_coupling_simulator.neutral.mcwf_xz_fixture.v2"
    )
    assert fixture["measurement_keys"] == [
        "mx_before",
        "mz_before",
        "mx_after",
        "mz_after",
    ]
    assert fixture["measurement_targets"] == [0, 1, 0, 1]
    assert fixture["measurement_bases"] == ["X", "Z", "X", "Z"]
    assert fixture["reset_after"] == [True, True, False, False]
    assert fixture["reset_states"] == {"X": "|+>", "Z": "|0>"}
    assert fixture["target_survival_probability"] == 0.25
    assert math.exp(
        -fixture["gamma_1_per_ns"] * fixture["evolution_duration_ns"]
    ) == pytest.approx(0.25, abs=1.0e-15)

    analytic = protocol.analytic_binary_distribution(fixture)
    assert math.fsum(analytic.values()) == 1.0
    assert len(analytic) == 16
    assert all(record[3] == 0 or mass == 0.0 for record, mass in analytic.items())
    assert {record for record, mass in analytic.items() if mass > 0.0} == {
        (x_before, z_before, x_after, 0)
        for x_before in (0, 1)
        for z_before in (0, 1)
        for x_after in (0, 1)
    }


def test_neutral_protocol_and_finite_step_recurrence_are_standard_library_only():
    tree = ast.parse(PROTOCOL.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots <= {
        "__future__",
        "collections",
        "hashlib",
        "json",
        "math",
        "pathlib",
        "typing",
    }
    source = PROTOCOL.read_text(encoding="utf-8")
    assert "finite_step_binary_distribution" in source


def test_neutral_fixture_is_hash_pinned_and_tampering_fails_closed(tmp_path: Path):
    protocol = _load_protocol()

    assert protocol.fixture_sha256(FIXTURE) == (
        "72d46d517d2e880327f22148e94611aa3b3c503a4a62d8ee18cf12b2d610257b"
    )
    corrupted = json.loads(FIXTURE.read_text(encoding="utf-8"))
    corrupted["gamma_1_per_ns"] = 0.021
    corrupted_path = tmp_path / FIXTURE.name
    corrupted_path.write_text(json.dumps(corrupted), encoding="utf-8")

    with pytest.raises(ValueError, match="fixture SHA-256 mismatch"):
        protocol.load_fixture(corrupted_path)


def test_two_sample_tv_gate_rejects_deterministic_z_reset_corruption():
    protocol = _load_protocol()
    fixture = protocol.load_fixture(FIXTURE)
    law = protocol.analytic_binary_distribution(fixture)
    sample_count = fixture["trajectory_count"]
    alpha = fixture["comparison_alpha"]

    healthy = protocol.two_sample_tv_comparison(
        law,
        law,
        left_sample_count=sample_count,
        right_sample_count=sample_count,
        alphabet_size=16,
        alpha=alpha,
    )
    corrupted_law = protocol.flip_binary_column(law, column=3)
    corrupted = protocol.two_sample_tv_comparison(
        law,
        corrupted_law,
        left_sample_count=sample_count,
        right_sample_count=sample_count,
        alphabet_size=16,
        alpha=alpha,
    )

    assert healthy["passed"] is True
    assert healthy["total_variation"] == 0.0
    assert 0.0 < healthy["simultaneous_tv_radius"] < 1.0
    assert corrupted["total_variation"] == 1.0
    assert corrupted["passed"] is False
    assert corrupted["total_variation"] > corrupted["simultaneous_tv_radius"]


def test_x_after_marginal_gate_rejects_population_rate_for_coherence_mutation():
    protocol = _load_protocol()
    fixture = protocol.load_fixture(FIXTURE)
    law = protocol.analytic_binary_distribution(fixture)
    survival = math.exp(
        -float(fixture["gamma_1_per_ns"])
        * float(fixture["evolution_duration_ns"])
    )
    healthy_x_after = {
        (label,): math.fsum(
            probability
            for record, probability in law.items()
            if record[2] == label
        )
        for label in (0, 1)
    }
    population_rate_mutation = protocol.population_rate_x_coherence_mutation(
        fixture
    )
    comparison = protocol.two_sample_tv_comparison(
        healthy_x_after,
        population_rate_mutation,
        left_sample_count=int(fixture["trajectory_count"]),
        right_sample_count=int(fixture["trajectory_count"]),
        alphabet_size=2,
        alpha=float(fixture["comparison_alpha"]) / 6.0,
    )

    assert comparison["total_variation"] == pytest.approx(
        0.5 * (math.sqrt(survival) - survival)
    )
    assert comparison["passed"] is False
    assert (
        comparison["total_variation"]
        > comparison["simultaneous_tv_radius"]
    )


def test_optional_gpu_comparison_does_not_override_supervisor_cuda_lease():
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    target = next(
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name
        == "test_optional_public_gpu_mcwf_matches_isolated_qutip_and_detects_corruption"
    )
    overwritten_keys = {
        subscript.slice.value
        for node in ast.walk(target)
        if isinstance(node, ast.Assign)
        for subscript in node.targets
        if isinstance(subscript, ast.Subscript)
        and isinstance(subscript.slice, ast.Constant)
        and isinstance(subscript.slice.value, str)
    }

    assert "CUDA_VISIBLE_DEVICES" not in overwritten_keys
    assert "ECS_GPU_SLOT" not in overwritten_keys


def test_canonical_report_hash_detects_payload_mutation():
    protocol = _load_protocol()
    report = {"schema": "example.v1", "value": 7}
    report["content_hash"] = protocol.canonical_content_hash(report)

    assert protocol.canonical_content_hash(report) == report["content_hash"]
    report["value"] = 8
    assert protocol.canonical_content_hash(report) != report["content_hash"]


def test_project_evidence_provenance_binds_clean_sources_and_honest_lock_scope(
    monkeypatch,
):
    comparator = _load_comparator(monkeypatch)
    commit = "a" * 40

    def clean_git(*arguments):
        if arguments == ("rev-parse", "HEAD"):
            return commit
        if arguments[:3] == ("ls-files", "--error-unmatch", "--"):
            return "\n".join(arguments[3:])
        if arguments == ("status", "--porcelain=v1", "--untracked-files=all"):
            return ""
        raise AssertionError(f"unexpected git query: {arguments!r}")

    monkeypatch.setattr(comparator, "_git", clean_git)
    source = comparator._project_source_provenance()
    locks = comparator._environment_lock_provenance()

    assert source["repo_commit"] == commit
    assert source["selected_sources_clean_at_repo_commit"] is True
    assert source["whole_worktree_clean_including_untracked"] is True
    assert set(source["selected_sources"]) >= {
        "scripts/external_baselines/qutip_mcwf_xz_protocol.py",
        "scripts/external_baselines/run_qutip_mcwf_xz_comparison.py",
        "tests/test_axis1_mcwf_convergence.py",
        "tests/test_external_qutip_mcwf_xz_comparison.py",
    }
    assert all(
        len(identity["sha256"]) == 64
        for identity in source["selected_sources"].values()
    )
    baseline_lock = locks["baseline_environment_lock"]
    assert baseline_lock["path"] == (
        "baseline-environment-qutip-linux-64.lock.json"
    )
    assert baseline_lock["conda_explicit_package_count"] > 0
    assert baseline_lock["qutip_commit"] == comparator.EXPECTED_QUTIP_COMMIT
    assert baseline_lock["qutip_tree"] == comparator.EXPECTED_QUTIP_TREE
    assert baseline_lock["authoritative_lock_conformance_checked"] is True
    assert locks["claims_qutip_baseline_lock_conformance"] is True
    assert locks["claims_reproducible_environment"] is True
    assert locks["core_lock_scope"] == "project_ecs_only_not_qutip_baseline"
    assert locks["uv_lock_scope"] == "project_ecs_only_not_qutip_baseline"
    assert len(locks["project_environment_locks"]["core-environment-cu130.lock"]) == 64
    assert len(locks["project_environment_locks"]["uv.lock"]) == 64

    monkeypatch.setattr(
        comparator,
        "_git",
        lambda *arguments: (
            commit
            if arguments == ("rev-parse", "HEAD")
            else "\n".join(arguments[3:])
            if arguments[:3] == ("ls-files", "--error-unmatch", "--")
            else " M scripts/external_baselines/qutip_mcwf_xz_protocol.py"
        ),
    )
    with pytest.raises(RuntimeError, match="clean Git worktree"):
        comparator._project_source_provenance()


def test_qutip_report_shapes_have_distinct_current_schema_versions():
    worker_source = QUTIP_WORKER.read_text(encoding="utf-8")
    comparator_source = COMPARATOR.read_text(encoding="utf-8")

    assert (
        'SCHEMA = "error_coupling_simulator.external_baseline.'
        'qutip_mcwf_xz_record.v3"' in worker_source
    )
    assert (
        'SCHEMA = "ai_qec.external_baseline.qutip_project_mcwf_xz_comparison.v3"'
        in comparator_source
    )
    assert (
        '"error_coupling_simulator.external_baseline.qutip_mcwf_xz_record.v3"'
        in comparator_source
    )
    assert (
        'WORKER_ENVELOPE_SCHEMA = '
        '"ai_qec.external_baseline.qutip_mcwf_xz_worker_envelope.v1"'
        in comparator_source
    )
    assert "_validate_isolated_qutip_report" in comparator_source
    assert '"finite_step_convergence": finite_step_convergence' in comparator_source


def test_exact_key_validator_rejects_missing_and_additional_fields(monkeypatch):
    comparator = _load_comparator(monkeypatch)

    comparator._require_exact_keys({"alpha": 1, "beta": 2}, {"alpha", "beta"}, label="fixture")
    with pytest.raises(RuntimeError, match="fixture fields drifted"):
        comparator._require_exact_keys({"alpha": 1}, {"alpha", "beta"}, label="fixture")
    with pytest.raises(RuntimeError, match="fixture fields drifted"):
        comparator._require_exact_keys(
            {"alpha": 1, "beta": 2, "gamma": 3},
            {"alpha", "beta"},
            label="fixture",
        )


def test_worker_transport_envelope_preserves_verified_payload(monkeypatch):
    comparator = _load_comparator(monkeypatch)
    protocol = _load_protocol()
    worker_report = {
        "schema": comparator.WORKER_SCHEMA,
        "all_checks_passed": True,
        "value": [1, 2, 3],
    }
    worker_report["content_hash"] = protocol.canonical_content_hash(worker_report)
    original = copy.deepcopy(worker_report)

    envelope = comparator._worker_transport_envelope(
        worker_report,
        stdout="worker stdout",
        stderr="",
        returncode=0,
    )

    assert worker_report == original
    assert envelope["schema"] == comparator.WORKER_ENVELOPE_SCHEMA
    assert envelope["worker_report"] == original
    assert envelope["worker_report"] is not worker_report
    assert envelope["worker_report_content_hash"] == original["content_hash"]
    assert len(envelope["worker_report_raw_json_sha256"]) == 64
    assert envelope["worker_report_raw_json_size_bytes"] > 0
    assert envelope["fresh_process"] == {
        "stdout": "worker stdout",
        "stderr": "",
        "returncode": 0,
    }
    assert envelope["content_hash"] == protocol.canonical_content_hash(envelope)
    with pytest.raises(RuntimeError, match="raw JSON does not match"):
        comparator._worker_transport_envelope(
            worker_report,
            stdout="worker stdout",
            stderr="",
            returncode=0,
            raw_json_bytes=b'{"different_payload":true}',
        )
    bool_coercion = copy.deepcopy(worker_report)
    bool_coercion["value"][0] = True
    with pytest.raises(RuntimeError, match="raw JSON does not match"):
        comparator._worker_transport_envelope(
            worker_report,
            stdout="worker stdout",
            stderr="",
            returncode=0,
            raw_json_bytes=json.dumps(bool_coercion).encode("utf-8"),
        )


def test_atomic_publication_invalidates_stale_output_and_fsyncs_parent(
    monkeypatch,
    tmp_path: Path,
):
    comparator = _load_comparator(monkeypatch)
    destination = tmp_path / "nested" / "report.json"
    destination.parent.mkdir()
    destination.write_text("stale", encoding="utf-8")
    fsynced = []
    monkeypatch.setattr(
        comparator,
        "_fsync_directory",
        lambda path: fsynced.append(Path(path).resolve()),
    )

    comparator._prepare_output_path(destination)

    assert not destination.exists()
    assert fsynced == [destination.parent.resolve()]
    fsynced.clear()
    comparator._atomic_write_json(destination, {"schema": "example.v1"})
    assert json.loads(destination.read_text(encoding="utf-8")) == {
        "schema": "example.v1"
    }
    assert fsynced == [destination.parent.resolve()]


def test_strict_worker_json_parser_rejects_duplicate_and_nonfinite_values(
    monkeypatch,
):
    comparator = _load_comparator(monkeypatch)

    assert comparator._strict_json_loads(b'{"schema":"example.v1"}') == {
        "schema": "example.v1"
    }
    with pytest.raises(RuntimeError, match="duplicate JSON key"):
        comparator._strict_json_loads(b'{"schema":"a","schema":"b"}')
    with pytest.raises(RuntimeError, match="non-finite JSON"):
        comparator._strict_json_loads(b'{"value":NaN}')
    with pytest.raises(RuntimeError, match="non-finite JSON"):
        comparator._strict_json_loads(b'{"value":1e999}')
    with pytest.raises(RuntimeError, match="must be a JSON object"):
        comparator._strict_json_loads(b"[]")


def test_atomic_publication_removes_replaced_target_when_directory_fsync_fails(
    monkeypatch,
    tmp_path: Path,
):
    comparator = _load_comparator(monkeypatch)
    destination = tmp_path / "report.json"
    comparator._prepare_output_path(destination)
    calls = 0

    def fail_first_directory_fsync(_path):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("injected directory fsync failure")

    monkeypatch.setattr(
        comparator,
        "_fsync_directory",
        fail_first_directory_fsync,
    )

    with pytest.raises(OSError, match="injected directory fsync failure"):
        comparator._atomic_write_json(destination, {"schema": "example.v1"})

    assert calls == 2
    assert not destination.exists()


def test_worker_launch_environment_strips_all_conda_and_loader_markers(
    monkeypatch,
    tmp_path: Path,
):
    comparator = _load_comparator(monkeypatch)
    baseline_python = Path("/isolated/ecs-baseline-qutip/bin/python")
    parent = {
        "PATH": "/parent/bin",
        "PYTHONPATH": "/project",
        "CONDA_PREFIX": "/parent/ecs",
        "CONDA_PREFIX_7": "/parent/base",
        "CONDA_EXE": "/parent/conda",
        "CONDA_PYTHON_EXE": "/parent/python",
        "_CE_CONDA": "conda",
        "_CE_M_EXTRA": "value",
        "LD_LIBRARY_PATH": "/parent/lib",
        "CUDA_HOME": "/parent/cuda",
        "VIRTUAL_ENV": "/parent/venv",
        "KEEP_ME": "yes",
    }

    isolated = comparator._worker_launch_environment(
        parent,
        baseline_python=baseline_python,
        cache_root=tmp_path / "private-runtime",
    )

    assert isolated["KEEP_ME"] == "yes"
    assert isolated["CUDA_VISIBLE_DEVICES"] == ""
    assert isolated["PYTHONNOUSERSITE"] == "1"
    assert isolated["PATH"].startswith(str(baseline_python.parent))
    assert "PYTHONPATH" not in isolated
    assert not any(
        key.startswith("CONDA_") or key.startswith("_CE_")
        for key in isolated
    )
    for key in ("LD_LIBRARY_PATH", "CUDA_HOME", "VIRTUAL_ENV"):
        assert key not in isolated
    private_root = tmp_path / "private-runtime"
    assert private_root.stat().st_mode & 0o777 == 0o700
    assert Path(isolated["HOME"]) == private_root / "home"
    assert Path(isolated["XDG_CACHE_HOME"]) == private_root / "xdg-cache"
    assert Path(isolated["MPLCONFIGDIR"]) == private_root / "mpl-config"
    assert all(Path(isolated[key]).is_dir() for key in (
        "HOME",
        "XDG_CACHE_HOME",
        "MPLCONFIGDIR",
    ))


@pytest.mark.parametrize("bad_bit", [0.9, True, "1"])
def test_all_qutip_comparator_histogram_validators_reject_coercible_bits(
    monkeypatch,
    bad_bit,
):
    comparator = _load_comparator(monkeypatch)
    fixture = {
        "measurement_keys": ["mx_before", "mz_before", "mx_after", "mz_after"],
        "measurement_targets": [0, 1, 0, 1],
        "measurement_bases": ["X", "Z", "X", "Z"],
        "reset_after": [True, True, False, False],
        "trajectory_count": 1,
    }
    bad_row = [bad_bit, 0, 0, 0]
    project_record = {
        **{field: fixture[field] for field in (
            "measurement_keys",
            "measurement_targets",
            "measurement_bases",
            "reset_after",
        )},
        "measurement_records": [bad_row],
        "record_counts": [1],
        "record_probabilities": [1.0],
    }
    project_labels = {
        "level_records": [bad_row],
        "level_record_counts": [1],
        "level_record_probabilities": [1.0],
    }
    worker_record = {
        "label_records": [bad_row],
        "label_counts": [1],
        "label_probabilities": [1.0],
    }

    with pytest.raises(RuntimeError, match="bit domain drifted"):
        comparator._validate_record_payload(
            project_record, fixture, label_prefix="project"
        )
    with pytest.raises(RuntimeError, match="bit domain drifted"):
        comparator._validate_label_payload(project_labels, fixture)
    with pytest.raises(RuntimeError, match="bit domain drifted"):
        comparator._validate_worker_histogram(
            worker_record,
            kind="label",
            trajectory_count=1,
        )


@pytest.mark.parametrize("field_value", [True, 1.0, "1"])
def test_qutip_comparator_histogram_validators_reject_non_integer_counts(
    monkeypatch,
    field_value,
):
    comparator = _load_comparator(monkeypatch)
    worker_record = {
        "label_records": [[0, 0, 0, 0]],
        "label_counts": [field_value],
        "label_probabilities": [1.0],
    }

    with pytest.raises(RuntimeError, match="counts drifted"):
        comparator._validate_worker_histogram(
            worker_record,
            kind="label",
            trajectory_count=1,
        )


@pytest.mark.parametrize("field_value", [True, "1", math.inf])
def test_qutip_comparator_histogram_validators_reject_invalid_probabilities(
    monkeypatch,
    field_value,
):
    comparator = _load_comparator(monkeypatch)
    worker_record = {
        "label_records": [[0, 0, 0, 0]],
        "label_counts": [1],
        "label_probabilities": [field_value],
    }

    with pytest.raises(RuntimeError, match="probabilities drifted"):
        comparator._validate_worker_histogram(
            worker_record,
            kind="label",
            trajectory_count=1,
        )


def test_qutip_worker_source_imports_no_project_implementation_or_private_helper():
    tree = ast.parse(QUTIP_WORKER.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])

    assert "error_coupling_simulator" not in imported_roots
    assert imported_roots <= {
        "__future__",
        "argparse",
        "collections",
        "hashlib",
        "importlib",
        "json",
        "math",
        "numpy",
        "os",
        "pathlib",
        "platform",
        "qutip",
        "qutip_mcwf_xz_protocol",
        "scipy",
        "subprocess",
        "sys",
        "tempfile",
        "typing",
    }


def test_project_comparator_uses_only_public_simulator_imports():
    source = COMPARATOR.read_text(encoding="utf-8")
    tree = ast.parse(source)
    project_imports = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module
        and node.module.startswith("error_coupling_simulator")
    }

    assert project_imports == {
        "error_coupling_simulator.frontend",
        "error_coupling_simulator.numerics",
    }
    for forbidden in (
        "_collapse_operator",
        "_hamiltonian_matrix_for_term",
        "_measurement_records",
        "_measure_site_declared_basis",
        "_readout_bit_from_level",
    ):
        assert forbidden not in source
    assert "start_new_session=True" not in source
    assert "_terminate_worker_process" in source


def test_isolated_worker_nonzero_exit_cleans_direct_worker(monkeypatch):
    comparator = _load_comparator(monkeypatch)

    class _FailedProcess:
        pid = 9173
        returncode = 7

        def communicate(self, *, timeout):
            assert timeout == 3.0
            return "worker stdout", "worker stderr"

    process = _FailedProcess()
    terminated = []
    monkeypatch.setattr(
        comparator,
        "_terminate_worker_process",
        lambda candidate: terminated.append(candidate),
    )

    with pytest.raises(RuntimeError, match="isolated QuTiP worker failed"):
        comparator._communicate_isolated_process(process, timeout_s=3.0)

    assert terminated == [process]


def test_worker_cleanup_kills_a_term_ignoring_direct_child(
    monkeypatch,
):
    comparator = _load_comparator(monkeypatch)
    process = subprocess.Popen(
        [
            "bash",
            "-lc",
            "trap '' TERM; exec sleep 60",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(0.05)
    try:
        comparator._terminate_worker_process(process)
        assert process.poll() is not None
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5.0)


@pytest.mark.skipif(
    os.environ.get("ECS_RUN_QUTIP_MCWF_XZ_COMPARISON") != "1",
    reason="set ECS_RUN_QUTIP_MCWF_XZ_COMPARISON=1 for isolated QuTiP worker",
)
def test_optional_isolated_qutip_worker_emits_ordered_xz_reset_artifact(
    tmp_path: Path,
    monkeypatch,
):
    from harness import proc

    protocol = _load_protocol()
    conda = shutil.which("conda")
    assert conda is not None
    comparator = _load_comparator(monkeypatch)
    baseline_python = comparator._resolve_named_conda_python(
        conda,
        environment_name="ecs-baseline-qutip",
    )
    output = tmp_path / "qutip_mcwf_xz.json"
    log = tmp_path / "qutip_mcwf_xz.log"
    environment = comparator._worker_launch_environment(
        os.environ,
        baseline_python=baseline_python,
        cache_root=tmp_path / "private-runtime",
    )
    ran = proc.run(
        [
            str(baseline_python),
            str(QUTIP_WORKER),
            "--fixture",
            str(FIXTURE),
            "--output",
            str(output),
        ],
        cwd=str(REPO),
        env=environment,
        timeout=300.0,
        log_path=str(log),
    )

    assert ran.ok, log.read_text(encoding="utf-8", errors="replace")
    assert ran.group_cleanup_verified is True
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["schema"] == (
        "error_coupling_simulator.external_baseline.qutip_mcwf_xz_record.v3"
    )
    assert report["all_checks_passed"] is True
    assert report["fixture"]["sha256"] == (
        "72d46d517d2e880327f22148e94611aa3b3c503a4a62d8ee18cf12b2d610257b"
    )
    assert report["runtime_provenance"]["environment"] == "ecs-baseline-qutip"
    assert report["runtime_provenance"]["clone_pristine"] is True
    assert report["runtime_provenance"]["project_package_find_spec"] is None
    assert report["runtime_provenance"]["python_version"]
    assert report["runtime_provenance"]["numpy_version"]
    assert report["runtime_provenance"]["scipy_version"]
    assert len(report["runtime_provenance"]["worker_sha256"]) == 64
    assert len(report["runtime_provenance"]["protocol_sha256"]) == 64
    assert report["runtime_provenance"]["installed_distribution"][
        "content_identity"
    ]["file_count"] > 0
    assert report["solver"]["name"] == "qutip.mcsolve"
    assert report["solver"]["trajectory_count"] == 2048
    assert report["solver"]["collapse_operator_count"] == 2
    assert report["solver"]["total_jump_count"] > 0
    assert report["solver"]["integrator_options"]["method"] == "vern7"
    assert report["solver"]["integrator_options"]["atol"] == 1.0e-10
    assert report["solver"]["integrator_options"]["rtol"] == 1.0e-8
    assert report["numerical_provenance"]["state_dtype"] == "complex128"
    assert report["numerical_provenance"]["probability_dtype"] == "float64"
    assert report["numerical_provenance"]["observed_final_state_dtypes"] == [
        "complex128"
    ]
    assert (
        report["numerical_provenance"]["observed_probability_array_dtype"]
        == "float64"
    )
    assert report["atomic_publication"][
        "artifact_presence_means_current_invocation_completed"
    ] is True
    assert report["atomic_publication"]["parent_directory_fsync_after_replace"] is True
    assert report["atomic_publication"]["durability_failure_removes_destination"] is True
    record = report["record"]
    assert record["measurement_bases"] == ["X", "Z", "X", "Z"]
    assert record["reset_after"] == [True, True, False, False]
    assert record["label_counts"] == record["binary_counts"]
    assert sum(record["label_counts"]) == 2048
    assert sum(record["binary_counts"]) == 2048
    assert report["reset_checks"]["X_reset_state"] == "|+>"
    assert report["reset_checks"]["Z_reset_state"] == "|0>"
    assert report["reset_checks"]["max_post_reset_state_l2"] <= 1.0e-12
    assert report["reset_checks"]["passed"] is True
    assert report["analytic_reference"]["joint_tv"]["passed"] is True
    assert report["analytic_reference"]["registered_statistic"] == (
        "f1.qutip_dense_joint"
    )
    assert set(
        report["analytic_reference"]["nonverdict_directed_marginal_tv"]
    ) == {"mz_before", "mx_after"}
    assert report["content_hash"] == protocol.canonical_content_hash(report)

    corrupted_fixture = tmp_path / "corrupted_fixture.json"
    corrupted_payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    corrupted_payload["collapse_terms"][0]["generator_rate_per_ns"] = 0.0
    corrupted_fixture.write_text(json.dumps(corrupted_payload), encoding="utf-8")
    output.write_text("stale artifact", encoding="utf-8")
    failed = proc.run(
        [
            str(baseline_python),
            str(QUTIP_WORKER),
            "--fixture",
            str(corrupted_fixture),
            "--output",
            str(output),
        ],
        cwd=str(REPO),
        env=environment,
        timeout=60.0,
        log_path=str(tmp_path / "qutip_mcwf_xz_failure.log"),
    )
    assert failed.ok is False
    assert failed.group_cleanup_verified is True
    assert not output.exists()


@pytest.mark.skipif(
    os.environ.get("ECS_RUN_QUTIP_MCWF_XZ_COMPARISON") != "1",
    reason="set ECS_RUN_QUTIP_MCWF_XZ_COMPARISON=1 for sanitized QuTiP launch",
)
def test_optional_comparator_launches_sanitized_immutable_worker_envelope(
    monkeypatch,
):
    comparator = _load_comparator(monkeypatch)
    protocol = _load_protocol()

    envelope = comparator._run_isolated_qutip(FIXTURE)

    assert envelope["schema"] == comparator.WORKER_ENVELOPE_SCHEMA
    assert envelope["content_hash"] == protocol.canonical_content_hash(envelope)
    assert envelope["fresh_process"]["returncode"] == 0
    worker_report = envelope["worker_report"]
    assert worker_report["schema"] == comparator.WORKER_SCHEMA
    assert worker_report["content_hash"] == protocol.canonical_content_hash(
        worker_report
    )
    assert set(
        worker_report["runtime_provenance"]["sanitized_parent_environment"]
    ) == set(comparator.SANITIZED_INHERITED_ENVIRONMENT_KEYS)
    assert all(
        value is None
        for value in worker_report["runtime_provenance"][
            "sanitized_parent_environment"
        ].values()
    )


@pytest.mark.skipif(
    os.environ.get("ECS_RUN_QUTIP_MCWF_XZ_COMPARISON") != "1",
    reason="set ECS_RUN_QUTIP_MCWF_XZ_COMPARISON=1 for GPU/QuTiP differential",
)
def test_optional_public_gpu_mcwf_matches_isolated_qutip_and_detects_corruption(
    tmp_path: Path,
    monkeypatch,
):
    from harness import proc

    conda = shutil.which("conda")
    assert conda is not None
    output = tmp_path / "qutip_project_mcwf_xz_comparison.json"
    log = tmp_path / "qutip_project_mcwf_xz_comparison.log"
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment["PYTHONNOUSERSITE"] = "1"
    visible_device = environment.get("CUDA_VISIBLE_DEVICES")
    assert visible_device not in (None, "")
    leased_slot = environment.get("ECS_GPU_SLOT")
    if leased_slot is not None:
        assert visible_device == leased_slot
    ran = proc.run(
        [
            conda,
            "run",
            "--no-capture-output",
            "-n",
            "ecs",
            "python",
            str(COMPARATOR),
            "--fixture",
            str(FIXTURE),
            "--output",
            str(output),
        ],
        cwd=str(REPO),
        env=environment,
        timeout=600.0,
        log_path=str(log),
    )

    assert ran.ok, log.read_text(encoding="utf-8", errors="replace")
    assert ran.group_cleanup_verified is True
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["schema"] == (
        "ai_qec.external_baseline.qutip_project_mcwf_xz_comparison.v3"
    )
    assert report["all_checks_passed"] is True
    assert report["fixture"]["sha256"] == (
        "72d46d517d2e880327f22148e94611aa3b3c503a4a62d8ee18cf12b2d610257b"
    )
    assert report["project"]["direct"]["passed"] is True
    assert report["project"]["carrier"]["passed"] is True
    assert report["project"]["direct_carrier_exact_record_match"] is True
    assert report["numerical_provenance"]["project_array_backend"] == (
        "torch_cuda_complex128"
    )
    assert report["numerical_provenance"]["carrier_array_backend"] == (
        "torch_cuda_complex128"
    )
    assert report["atomic_publication"][
        "artifact_presence_means_current_invocation_completed"
    ] is True
    assert report["atomic_publication"]["parent_directory_fsync_after_replace"] is True
    assert report["atomic_publication"]["durability_failure_removes_destination"] is True
    finite_step = report["finite_step_convergence"]
    assert finite_step["all_checks_passed"] is True
    deterministic = finite_step["deterministic_recurrence"]
    assert deterministic["microstep_counts"] == [10, 20, 40, 80]
    public_m40 = finite_step["public_m40_sample_gate"]
    assert public_m40["all_checks_passed"] is True
    assert public_m40["direct"]["passed"] is True
    assert public_m40["carrier"]["passed"] is True
    assert public_m40["direct"]["observed_tv"] == public_m40["carrier"][
        "observed_tv"
    ]
    assert deterministic["corruption_controls"]["nojump_half_to_one"][
        "detected"
    ] is True
    assert deterministic["corruption_controls"]["wrong_dt"]["detected"] is True
    source_provenance = report["project_runtime_provenance"]["source_provenance"]
    assert source_provenance["whole_worktree_clean_including_untracked"] is True
    assert source_provenance["selected_sources_clean_at_repo_commit"] is True
    assert set(source_provenance["selected_sources"]) >= {
        "scripts/external_baselines/qutip_mcwf_xz_protocol.py",
        "scripts/external_baselines/run_qutip_mcwf_xz_comparison.py",
        "tests/test_axis1_mcwf_convergence.py",
        "tests/test_external_qutip_mcwf_xz_comparison.py",
    }
    locks = report["project_runtime_provenance"]["environment_lock_provenance"]
    assert locks["baseline_environment_lock"][
        "authoritative_lock_conformance_checked"
    ] is True
    assert locks["claims_qutip_baseline_lock_conformance"] is True
    assert locks["claims_reproducible_environment"] is True
    assert report["canonical_report_identity"]["content_hash_locator"] == (
        "#/content_hash"
    )
    envelope = report["isolated_qutip"]
    assert envelope["schema"] == (
        "ai_qec.external_baseline.qutip_mcwf_xz_worker_envelope.v1"
    )
    assert envelope["fresh_process"]["returncode"] == 0
    assert envelope["worker_report"]["schema"] == (
        "error_coupling_simulator.external_baseline.qutip_mcwf_xz_record.v3"
    )
    assert envelope["worker_report_content_hash"] == envelope["worker_report"][
        "content_hash"
    ]
    assert len(envelope["worker_report_raw_json_sha256"]) == 64
    assert envelope["worker_report_raw_json_size_bytes"] > 0
    comparator = _load_comparator(monkeypatch)
    protocol = _load_protocol()
    fixture = protocol.load_fixture(FIXTURE)
    inner = envelope["worker_report"]
    comparator._validate_isolated_qutip_report(
        inner,
        fixture=fixture,
        fixture_path=FIXTURE,
    )
    semantic_mutations = (
        lambda candidate: candidate.__setitem__(
            "schema", "ai_qec.external_baseline.qutip_mcwf_xz_record.v1"
        ),
        lambda candidate: candidate["runtime_provenance"].__setitem__(
            "unexpected", True
        ),
        lambda candidate: candidate["fixture"].__setitem__(
            "comparison_registry_sha256", "0" * 64
        ),
        lambda candidate: candidate["solver"]["integrator_options"].__setitem__(
            "atol", 1.0e-4
        ),
        lambda candidate: candidate["record"]["binary_counts"].__setitem__(
            0, candidate["record"]["binary_counts"][0] + 1
        ),
        lambda candidate: candidate["record"]["binary_records"][0].__setitem__(
            0, True
        ),
        lambda candidate: candidate["reset_checks"].__setitem__(
            "passed", False
        ),
        lambda candidate: candidate["analytic_reference"]["joint_tv"].__setitem__(
            "total_variation", 1.0
        ),
        lambda candidate: candidate.__setitem__("all_checks_passed", False),
    )
    for mutate in semantic_mutations:
        candidate = copy.deepcopy(inner)
        mutate(candidate)
        candidate["content_hash"] = protocol.canonical_content_hash(candidate)
        with pytest.raises(RuntimeError):
            comparator._validate_isolated_qutip_report(
                candidate,
                fixture=fixture,
                fixture_path=FIXTURE,
            )
    assert report["ordered_measurement_contract"]["measurement_bases"] == [
        "X",
        "Z",
        "X",
        "Z",
    ]
    assert report["ordered_measurement_contract"]["reset_after"] == [
        True,
        True,
        False,
        False,
    ]
    assert report["ordered_measurement_contract"]["X_reset_state"] == "|+>"
    assert report["ordered_measurement_contract"]["Z_reset_state"] == "|0>"
    assert report["ordered_measurement_contract"]["directed_x_after_column"] == 2
    assert report["ordered_measurement_contract"]["directed_x_after_key"] == "mx_after"
    comparisons = report["comparisons"]
    assert comparisons["qutip_vs_direct_labels"]["passed"] is True
    assert comparisons["qutip_vs_direct_binary"]["passed"] is True
    assert comparisons["qutip_vs_carrier_binary"]["passed"] is True
    assert comparisons["qutip_vs_direct_labels_x_after"]["passed"] is True
    assert comparisons["qutip_vs_direct_binary_x_after"]["passed"] is True
    assert comparisons["qutip_vs_carrier_binary_x_after"]["passed"] is True
    assert report["corruption_negative_control"]["comparison"]["passed"] is False
    assert report["corruption_negative_control"]["detected"] is True
    assert report["corruption_negative_control"]["forces_overall_fail"] is True
    assert report["x_coherence_mutation_negative_control"]["comparison"][
        "passed"
    ] is False
    assert report["x_coherence_mutation_negative_control"]["detected"] is True
    assert report["x_coherence_mutation_negative_control"][
        "forces_overall_fail"
    ] is True
    assert report["content_hash"] == protocol.canonical_content_hash(report)
