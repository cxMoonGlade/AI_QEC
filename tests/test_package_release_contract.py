"""Release-contract gates for the standalone simulator distribution."""

from __future__ import annotations

import ast
from importlib import metadata
from pathlib import Path
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
