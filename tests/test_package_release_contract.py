"""Release-contract gates for the standalone simulator distribution."""

from __future__ import annotations

import ast
from importlib import metadata
import json
from pathlib import Path
import subprocess
import sys
import tomllib


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "src" / "error_coupling_simulator"

_OWNER_LIKE_FIELDS = frozenset(
    {
        "assembled_by",
        "backend",
        "carrier_object_under_test",
        "carrier_operator",
        "compiler",
        "name",
        "oracle",
        "oracle_schema",
        "reference",
        "scope",
        "source",
        "workload_adapter",
    }
)


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


def test_code_map_legacy_edge_scanner_distinguishes_schema_ids_from_resolution(
    tmp_path: Path,
) -> None:
    from tools.gen_code_map import _legacy_qec_twin_edges

    probe = tmp_path / "probe.py"
    probe.write_text(
        "\n".join(
            (
                "SCHEMA = 'qec_twin.persisted.v1'",
                "import qec_twin.forward",
                "pytest.importorskip('qec_twin.simulator')",
                "monkeypatch.setattr('qec_twin.simulator.fn', replacement)",
                "legacy_module = 'qec_twin.dynamic'",
                "importlib.import_module(legacy_module)",
                "importlib.util.find_spec(name='qec_twin.keyword')",
            )
        ),
        encoding="utf-8",
    )

    edges = _legacy_qec_twin_edges(probe)

    assert len(edges) == 5
    assert any("import qec_twin.forward" in edge for edge in edges)
    assert any("importorskip" in edge for edge in edges)
    assert any("setattr" in edge for edge in edges)
    assert any("qec_twin.dynamic" in edge for edge in edges)
    assert any("qec_twin.keyword" in edge for edge in edges)
    assert all("persisted" not in edge for edge in edges)


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


def _target_field_names(target: ast.expr) -> set[str]:
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, ast.Attribute):
        return {target.attr}
    if isinstance(target, (ast.List, ast.Tuple)):
        return {
            name
            for element in target.elts
            for name in _target_field_names(element)
        }
    return set()


def _legacy_owner_literal(node: ast.AST | None) -> str | None:
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and "qec_twin." in node.value
    ):
        return node.value
    return None


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
    assert identity["schema"] == "error_coupling_simulator.package_build_identity.v1"
    assert identity["distribution"] == "error-coupling-simulator"
    assert identity["version"] == metadata.version("error-coupling-simulator")
    assert len(identity["package_tree_sha256"]) == 64
    int(identity["package_tree_sha256"], 16)
    assert identity["git_commit"] is None or identity["git_commit"]


def test_active_package_has_no_executable_legacy_import_back_edge() -> None:
    offenders: list[str] = []
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
        legacy = sorted(
            name for name in imported
            if name == "qec_twin" or name.startswith("qec_twin.")
        )
        if legacy:
            offenders.append(f"{path.relative_to(PACKAGE_ROOT)}: {legacy}")
    assert offenders == []


def test_active_owner_metadata_names_only_installed_package_owners() -> None:
    """Compatibility schema IDs may stay old; active owner provenance may not."""

    offenders: list[str] = []
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        relative = path.relative_to(PACKAGE_ROOT)
        for node in ast.walk(tree):
            if isinstance(node, ast.Dict):
                for key, value in zip(node.keys, node.values, strict=True):
                    if not (
                        isinstance(key, ast.Constant)
                        and isinstance(key.value, str)
                        and key.value in _OWNER_LIKE_FIELDS
                    ):
                        continue
                    legacy = _legacy_owner_literal(value)
                    if legacy is not None:
                        offenders.append(
                            f"{relative}:{value.lineno}: {key.value}={legacy!r}"
                        )
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                field_names = {
                    name
                    for target in targets
                    for name in _target_field_names(target)
                }
                if not field_names.intersection(_OWNER_LIKE_FIELDS):
                    continue
                legacy = _legacy_owner_literal(node.value)
                if legacy is not None:
                    offenders.append(
                        f"{relative}:{node.value.lineno}: "
                        f"{sorted(field_names)!r}={legacy!r}"
                    )
            elif isinstance(node, ast.keyword) and node.arg in _OWNER_LIKE_FIELDS:
                legacy = _legacy_owner_literal(node.value)
                if legacy is not None:
                    offenders.append(
                        f"{relative}:{node.value.lineno}: {node.arg}={legacy!r}"
                    )

    assert offenders == []


def test_active_package_contains_no_symlink_to_repository_code() -> None:
    assert [path for path in PACKAGE_ROOT.rglob("*") if path.is_symlink()] == []
