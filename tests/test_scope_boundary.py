"""Ownership and retired-API boundary checks for the current simulator."""

from __future__ import annotations

import ast
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "src" / "error_coupling_simulator"
TEST_ROOT = REPO_ROOT / "tests"


def _retired_namespace() -> str:
    # Keep the retired spelling out of the current source/test vocabulary while
    # still constructing the exact boundary value that the gate must reject.
    return "_".join(("qec", "twin"))


def _retired_symbol_names() -> frozenset[str]:
    stage = "G" + "2"
    symbols = {
        "Mechanism" + "Spec",
        "mechanism_" + "channel",
        "Shot" + "Set",
        "certify_" + "teacher",
        "Controlled" + "Teacher",
        "CoupledCycle" + "Teacher",
        "QutritLeakage" + "Teacher",
        "StaticZZ" + "Calibration",
        "Coupled" + "MechanismParams",
        f"Axis1{stage}Row",
        f"Axis1{stage}EvidenceResult",
        f"Axis1{stage}FreezeResult",
        f"Axis1{stage}RunnerResult",
        f"axis1_{stage.lower()}_frontend_gate",
        f"axis1_{stage.lower()}_gate_manifest",
        f"write_axis1_{stage.lower()}_evidence",
        f"freeze_axis1_{stage.lower()}_evidence",
        f"validate_axis1_{stage.lower()}_freeze",
        f"build_axis1_{stage.lower()}_frontend_schedule",
        f"run_axis1_{stage.lower()}_frontend_fixture",
        f"build_axis1_{stage.lower()}_selection_plan",
        f"AXIS1_{stage}_SELECTOR_ID",
    }
    symbols.update(
        f"{stage}_{suffix}"
        for suffix in (
            "ZETA_RAD_PER_NS",
            "GAMMA_PHI_PER_NS",
            "GAMMA_1_PER_NS",
            "DR_ZZ_BAND",
            "FIXED_OMEGA_BAND",
            "NONZERO_COMMUTATOR_MIN",
            "NONZERO_SUPEROP_DISTANCE_MIN",
            "DT_GRID",
            "DT_SMALL",
            "DT_CONTROL",
            "FIXED_OMEGA_RAD_PER_NS",
            "SLOPE_TOL",
            "ALLOWED_SOURCE_KINDS",
            "FORBIDDEN_OUTPUT_SUFFIXES",
            "FORBIDDEN_OUTPUT_NAMES",
        )
    )
    return frozenset(symbols)


def _retired_python_callable_names() -> frozenset[str]:
    # The source file remains because the explicit work-counter ABI is current;
    # only the ambiguous lumped callable is retired.
    return frozenset({"sv_" + "traj_d3"})


def _retired_current_modules() -> frozenset[str]:
    package = "error_coupling_simulator"
    stage = "g" + "2"
    return frozenset(
        {
            f"{package}.carrier." + "channels",
            f"{package}.mechanisms." + "catalog",
            f"{package}.mechanisms." + "teachers",
            f"{package}.mechanisms." + "seam_" + "teachers",
            f"{package}.mechanisms." + "qutrit_" + "teachers",
            f"{package}.frontend.axis1_" + "evidence_guard",
            f"{package}.frontend.axis1_" + "bridge",
            f"{package}.frontend.axis1_{stage}_runner",
        }
    )


def _dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _literal_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _is_retired_module(module: str) -> bool:
    retired = _retired_namespace()
    legacy_prefix = "legacy." + retired
    return (
        module == retired
        or module.startswith(retired + ".")
        or module == legacy_prefix
        or module.startswith(legacy_prefix + ".")
        or any(
            module == retired_module or module.startswith(retired_module + ".")
            for retired_module in _retired_current_modules()
        )
    )


def _is_retired_path(value: str) -> bool:
    retired = _retired_namespace()
    normalized = value.replace("\\", "/")
    return (
        normalized == f"src/{retired}"
        or normalized.startswith(f"src/{retired}/")
        or normalized == f"legacy/{retired}"
        or normalized.startswith(f"legacy/{retired}/")
    )


def _string_contract_violation(value: str) -> str | None:
    """Classify executable old schema/env/JIT/op strings, not prose or blockers."""

    retired = _retired_namespace()
    old_env_prefix = "_".join(("QEC", "TWIN")) + "_"
    if value.startswith(old_env_prefix):
        return "retired environment variable"
    if "axis1_" + "g" + "2" in value.lower():
        return "retired stage API token"
    if "g" + "2_jointl" in value.lower():
        return "retired stage artifact token"
    if value.startswith(retired + "::"):
        return "retired custom-op namespace"
    if value.startswith(retired + "_"):
        return "retired schema/JIT namespace"
    if (
        value.startswith(retired + ".")
        and not any(char.isspace() for char in value)
        and re.search(r"(?:^|[._])v\d+(?:$|[._])", value)
    ):
        return "retired schema namespace"
    return None


def _python_retired_api_violations(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError) as exc:
        return [f"{path.relative_to(REPO_ROOT)}: cannot parse: {exc}"]

    retired_symbols = _retired_symbol_names()
    retired_callables = _retired_python_callable_names()
    violations: set[str] = set()

    def add(node: ast.AST, message: str) -> None:
        line = getattr(node, "lineno", 1)
        violations.add(f"{path.relative_to(REPO_ROOT)}:{line}: {message}")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _is_retired_module(alias.name):
                    add(node, f"imports retired module {alias.name!r}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if _is_retired_module(module):
                add(node, f"imports from retired module {module!r}")
            for alias in node.names:
                if alias.name in retired_symbols:
                    add(node, f"imports retired symbol {alias.name!r}")
        elif isinstance(node, ast.Name) and node.id in retired_symbols | retired_callables:
            add(node, f"uses retired symbol {node.id!r}")
        elif isinstance(node, ast.Attribute) and node.attr in retired_symbols | retired_callables:
            add(node, f"uses retired attribute {node.attr!r}")
        elif isinstance(node, ast.Call):
            call_name = _dotted_name(node.func)
            first = _literal_string(node.args[0]) if node.args else None
            is_resolution_call = call_name in {
                "__import__",
                "find_spec",
                "import_module",
                "importlib.import_module",
                "importlib.util.find_spec",
                "pytest.importorskip",
            }
            is_patch_call = call_name.endswith((".patch", ".setattr", ".setitem"))
            if first is not None and (is_resolution_call or is_patch_call):
                if _is_retired_module(first):
                    add(node, f"resolves or patches retired module {first!r}")
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id == "__all__" for target in targets):
                for item in ast.walk(node.value):
                    exported = _literal_string(item)
                    if exported in retired_symbols | retired_callables:
                        add(node, f"exports retired symbol {exported!r}")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            reason = _string_contract_violation(node.value)
            if reason is not None:
                add(node, f"contains {reason} {node.value!r}")

    return sorted(violations)


def _walk_json_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _walk_json_strings(key)
            yield from _walk_json_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_json_strings(item)


def _json_retired_api_violations(path: Path) -> list[str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [f"{path.relative_to(REPO_ROOT)}: invalid JSON: {exc}"]

    violations: set[str] = set()
    retired_symbols = _retired_symbol_names()
    for value in _walk_json_strings(payload):
        reason = _string_contract_violation(value)
        if reason is not None:
            violations.add(
                f"{path.relative_to(REPO_ROOT)}: contains {reason} {value!r}"
            )
        if _is_retired_module(value):
            violations.add(
                f"{path.relative_to(REPO_ROOT)}: names retired module {value!r}"
            )
        if _is_retired_path(value):
            violations.add(
                f"{path.relative_to(REPO_ROOT)}: names retired source path {value!r}"
            )
        for symbol in retired_symbols:
            if re.search(rf"(?<![A-Za-z0-9_]){re.escape(symbol)}(?![A-Za-z0-9_])", value):
                violations.add(
                    f"{path.relative_to(REPO_ROOT)}: names retired symbol {symbol!r}"
                )
    return sorted(violations)


def _native_retired_api_violations(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    retired = _retired_namespace()
    old_env_prefix = "_".join(("QEC", "TWIN")) + "_"
    needles = (retired + "::", retired + "_", old_env_prefix)
    return [
        f"{path.relative_to(REPO_ROOT)}: contains retired native/API token {needle!r}"
        for needle in needles
        if needle in text
    ]


def _retired_api_violations() -> list[str]:
    violations: list[str] = []
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        violations.extend(_python_retired_api_violations(path))
    for path in sorted(TEST_ROOT.rglob("*.py")):
        violations.extend(_python_retired_api_violations(path))
    for path in sorted(TEST_ROOT.rglob("*.json")):
        violations.extend(_json_retired_api_violations(path))
    for suffix in ("*.cpp", "*.cu", "*.h", "*.hpp"):
        for path in sorted(PACKAGE_ROOT.rglob(suffix)):
            violations.extend(_native_retired_api_violations(path))
    return sorted(set(violations))


def test_public_package_description_matches_simulator_contract() -> None:
    import error_coupling_simulator

    doc = (error_coupling_simulator.__doc__ or "").lower()
    assert "emits a multi-time syndrome record" in doc


def test_current_noise_process_apis_are_exported_by_their_owners() -> None:
    from error_coupling_simulator.certify import certify_noise_process
    from error_coupling_simulator.mechanisms.qutrit_leakage import (
        QutritLeakageNoiseProcess,
        qutrit_leakage_process,
        qutrit_leakage_process_heterogeneous,
        solve_theta_for_wg_l1,
    )
    from error_coupling_simulator.noise_processes import (
        COUPLED_PROCESS_REPRESENTABILITY,
        COUPLED_PROCESS_SCHEMA,
        CoupledCycleNoiseProcess,
    )

    assert callable(certify_noise_process)
    assert callable(solve_theta_for_wg_l1)
    assert callable(qutrit_leakage_process)
    assert callable(qutrit_leakage_process_heterogeneous)
    assert QutritLeakageNoiseProcess.__module__.endswith("mechanisms.qutrit_leakage")
    assert CoupledCycleNoiseProcess.__module__.endswith("noise_processes.coupled_cycle")
    assert COUPLED_PROCESS_SCHEMA.startswith("error_coupling_simulator.")
    assert COUPLED_PROCESS_REPRESENTABILITY


def test_source_and_test_graph_has_no_retired_api_dependency() -> None:
    """The current package and retained tests must not resolve retired APIs."""

    violations = _retired_api_violations()
    if violations:
        shown = violations[:120]
        remainder = len(violations) - len(shown)
        detail = "\n".join(f"  - {item}" for item in shown)
        if remainder:
            detail += f"\n  - ... and {remainder} more"
        raise AssertionError(
            f"retired API dependency gate found {len(violations)} violation(s):\n{detail}"
        )


def test_runtime_import_graph_is_closed_over_the_current_package() -> None:
    """Import every installed module while a finder rejects the retired namespace."""

    retired_namespace = _retired_namespace()
    retired_modules = sorted(_retired_current_modules())
    retired_exports = {
        "error_coupling_simulator.carrier": sorted(
            {
                "Mechanism" + "Spec",
                "mechanism_" + "channel",
                "Shot" + "Set",
            }
        ),
        "error_coupling_simulator.certify": sorted(
            {"certify_" + "teacher", "Controlled" + "Teacher"}
        ),
        "error_coupling_simulator.mechanisms": sorted(
            {"QutritLeakage" + "Teacher"}
        ),
        "error_coupling_simulator.noise_processes": sorted(
            {"CoupledCycle" + "Teacher"}
        ),
        "error_coupling_simulator.source": sorted(
            {"StaticZZ" + "Calibration", "Coupled" + "MechanismParams"}
        ),
        "error_coupling_simulator.frontend": sorted(
            name
            for name in _retired_symbol_names()
            if "G" + "2" in name or "g" + "2" in name
        ),
        "error_coupling_simulator.carrier.kernels": sorted(
            _retired_python_callable_names()
        ),
    }
    script = f"""
import importlib
import importlib.abc
import importlib.util
import os
import pkgutil
import sys

retired_namespace = {retired_namespace!r}
retired_modules = {retired_modules!r}
retired_exports = {retired_exports!r}

class RetiredImportBlocker(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == retired_namespace or fullname.startswith(retired_namespace + '.'):
            raise ImportError('retired namespace resolution attempted: ' + fullname)
        return None

sys.meta_path.insert(0, RetiredImportBlocker())
package = importlib.import_module('error_coupling_simulator')
loaded = []
for info in pkgutil.walk_packages(package.__path__, package.__name__ + '.'):
    importlib.import_module(info.name)
    loaded.append(info.name)

for module_name in retired_modules:
    if importlib.util.find_spec(module_name) is not None:
        raise AssertionError('retired current-package module still resolves: ' + module_name)

for module_name, names in retired_exports.items():
    module = importlib.import_module(module_name)
    exported = set(getattr(module, '__all__', ()))
    for name in names:
        if name in exported or hasattr(module, name):
            raise AssertionError(f'retired export still visible: {{module_name}}.{{name}}')

if any(
    name == retired_namespace or name.startswith(retired_namespace + '.')
    for name in sys.modules
):
    raise AssertionError('retired namespace entered sys.modules')
if not loaded:
    raise AssertionError('current package walk imported no submodules')
print(f'imported {{len(loaded)}} current modules with retired imports blocked')
"""
    env = dict(os.environ)
    env["ECS_DISABLE_NATIVE_KERNELS"] = "1"
    probe = subprocess.run(
        [sys.executable, "-I", "-c", script],
        cwd=REPO_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert probe.returncode == 0, probe.stdout + probe.stderr
    assert re.fullmatch(
        r"imported \d+ current modules with retired imports blocked\n?",
        probe.stdout,
    ), probe.stdout


def test_retired_package_trees_are_not_present() -> None:
    retired_namespace = _retired_namespace()
    assert not (REPO_ROOT / "src" / retired_namespace).exists()
    assert not (REPO_ROOT / "legacy" / retired_namespace).exists()
