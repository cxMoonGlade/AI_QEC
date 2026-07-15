"""Release-contract gates for the standalone simulator distribution."""

from __future__ import annotations

from importlib import metadata
import json
from pathlib import Path
import subprocess
import sys
import tomllib


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "src" / "error_coupling_simulator"

def test_generated_code_map_and_reverse_service_coverage_are_current() -> None:
    """The release must classify every installed module and ship a fresh flow/catalog."""

    probe = subprocess.run(
        [sys.executable, "tools/gen_code_map.py", "--check"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert probe.returncode == 0, probe.stdout + probe.stderr


def test_service_acceptance_plan_is_unique_process_isolated_and_routes_cudaq() -> None:
    catalog = json.loads(
        (REPO_ROOT / "docs" / "service_status.json").read_text(encoding="utf-8")
    )
    expected_paths = sorted({
        path
        for service in catalog["services"]
        for path in service["acceptance"]
    })
    execution = catalog["acceptance_execution"]
    expected_lanes = {
        path: execution["default_lane"]
        for path in expected_paths
    }
    for lane, paths in execution["lane_overrides"].items():
        for path in paths:
            expected_lanes[path] = lane
    expected_environments = {
        path: execution["environment_overrides"].get(
            path,
            execution["default_conda_environment"],
        )
        for path in expected_paths
    }
    probe = subprocess.run(
        [sys.executable, "tests/harness/service_acceptance.py", "--list"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert probe.returncode == 0, probe.stdout + probe.stderr
    rows = [line.split("\t") for line in probe.stdout.splitlines() if line]
    assert all(len(row) == 3 for row in rows)
    assert [path for _, _, path in rows] == expected_paths
    assert len(rows) == len({path for _, _, path in rows})
    assert {
        path: lane
        for lane, _, path in rows
    } == expected_lanes
    assert {
        path: environment
        for _, environment, path in rows
    } == expected_environments
    assert {lane for lane, _, _ in rows} == {
        "cpu_light",
        "cpu_exclusive",
        "gpu_serial",
    }
    assert {
        path: environment
        for _, environment, path in rows
        if environment != "ecs"
    } == {"tests/test_simulator_cudaq_grover.py": "aiqec"}


def test_pepo_allocator_environment_contract_is_exact_and_file_local() -> None:
    catalog = json.loads(
        (REPO_ROOT / "docs" / "service_status.json").read_text(encoding="utf-8")
    )
    execution = catalog["acceptance_execution"]
    expected = {
        path: {"PYTORCH_ALLOC_CONF": "expandable_segments:True"}
        for path in (
            "tests/test_pepo_density_compressed_caps.py",
            "tests/test_pepo_density_killers.py",
            "tests/test_pepo_density_nonselective_round.py",
            "tests/test_pepo_density_ntu_precut.py",
            "tests/test_pepo_density_observables.py",
            "tests/test_pepo_density_stabilizer.py",
            "tests/test_pepo_density_state.py",
            "tests/test_pepo_density_token_ops.py",
        )
    }
    all_acceptance = {
        path
        for service in catalog["services"]
        for path in service["acceptance"]
    }

    assert execution["process_environment_overrides"] == expected
    assert set(expected) <= all_acceptance
    assert set(expected) <= set(execution["lane_overrides"]["gpu_serial"])
    assert "tests/test_pepo_host_seam.py" not in expected
    assert "tests/test_pepo_density_layout_guards.py" not in expected
    assert "tests/test_simulator_cudaq_grover.py" not in expected


def test_runtime_package_version_matches_distribution_metadata() -> None:
    import error_coupling_simulator as ecs

    assert ecs.__version__ == metadata.version("error-coupling-simulator")


def test_declared_python_and_runtime_dependencies_cover_active_carriers() -> None:
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())["project"]
    dependencies = tuple(str(item) for item in project["dependencies"])

    assert project["requires-python"] == ">=3.11"
    assert any(item.startswith("qutip==5.3.0") for item in dependencies)
    assert any(item.startswith("quimb==") and ";" not in item for item in dependencies)
    assert any(item.startswith("scipy==") and ";" not in item for item in dependencies)


def test_package_build_identity_survives_without_a_git_checkout() -> None:
    from error_coupling_simulator.carrier.within_cycle import (
        package_build_identity,
    )

    identity = package_build_identity()
    assert identity["schema"] == "error_coupling_simulator.carrier.package_build_identity.v1"
    assert identity["distribution"] == "error-coupling-simulator"
    assert identity["version"] == metadata.version("error-coupling-simulator")
    assert len(identity["package_tree_sha256"]) == 64
    int(identity["package_tree_sha256"], 16)
    assert identity["git_commit"] is None or identity["git_commit"]


def test_active_package_contains_no_symlink_to_repository_code() -> None:
    assert [path for path in PACKAGE_ROOT.rglob("*") if path.is_symlink()] == []
