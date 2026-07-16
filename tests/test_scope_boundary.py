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
from urllib.parse import unquote, urlsplit


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "src" / "error_coupling_simulator"
TEST_ROOT = REPO_ROOT / "tests"


CURRENT_AUTHORITY_MARKDOWN = (
    "AGENTS.md",
    "README.md",
    "CLAUDE.md",
    "CONTEXT.md",
    "docs/SIMULATOR.md",
    "docs/ARCHITECTURE.md",
    "docs/METRICS.md",
    "docs/FAITHFULNESS_PROTOCOL.md",
    "docs/NUMERICAL_PROVENANCE.md",
    "docs/CODE_MAP.md",
    "tests/CODEBOOK.md",
    "docs/simulator_validation/PEPO_VALIDATION.md",
    "docs/simulator_validation/PEPS_FET_VALIDATION.md",
    "docs/simulator_validation/LEAKAGE_PROCESS_VALIDATION.md",
    "docs/simulator_validation/COHERENT_LEAKAGE_TRUNCATION_EVIDENCE.md",
    "docs/simulator_validation/finite_rtn_free_induction_literature_closure_2026-07-15.md",
    "docs/simulator_validation/finite_rtn_free_induction_diagnostic_contract_2026-07-15.md",
    "src/error_coupling_simulator/README.md",
    "src/error_coupling_simulator/carrier/kernels/README.md",
    "src/error_coupling_simulator/carrier/pepo/README.md",
    "src/error_coupling_simulator/carrier/peps/README.md",
    "src/error_coupling_simulator/certify/README.md",
    "src/error_coupling_simulator/frontend/README.md",
    "src/error_coupling_simulator/quantum_bath/README.md",
)
CURRENT_AUTHORITY_STRUCTURED = ("docs/service_status.json",)
CURRENT_SOURCE_TEXT_SUFFIXES = frozenset(
    {
        ".py", ".md", ".json", ".jsonc", ".toml", ".cfg", ".yaml", ".yml",
        ".lock", ".js", ".sh", ".cpp", ".cu", ".h", ".hpp",
    }
)
CURRENT_SOURCE_CONFIG_ROOTS = frozenset(
    {"src", "tests", "scripts", "tools", ".agents", ".claude", ".codex", ".github"}
)
CURRENT_ROOT_CONFIGS = frozenset(
    {
        "pyproject.toml",
        "setup.cfg",
        "MANIFEST.in",
        "environment-ecs.yml",
        "uv.lock",
        "core-environment-cu130.lock",
    }
)


def _retired_namespace() -> str:
    # Keep the retired spelling out of the current source/test vocabulary while
    # still constructing the exact boundary value that the gate must reject.
    return "_".join(("qec", "twin"))


def _retired_role_words() -> tuple[str, str]:
    return ("".join(("teach", "er")), "".join(("learn", "er")))


def _retired_symbol_names() -> frozenset[str]:
    stage = "G" + "2"
    process_role = _retired_role_words()[0]
    process_role_type = process_role.title()
    symbols = {
        "Mechanism" + "Spec",
        "mechanism_" + "channel",
        "Shot" + "Set",
        "certify_" + process_role,
        "Controlled" + process_role_type,
        "CoupledCycle" + process_role_type,
        "QutritLeakage" + process_role_type,
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
        "wg_" + "rates",
        "coherence_of_" + "leakage",
        "solve_theta_for_" + "wg_l1",
        "simulate_qutrit_" + "wg_leakage",
        "wg_" + "seep_collapse_matrix",
        "WG_L1_" + "REGIME",
        "WG_L2_" + "REGIME",
        "PRESET_LEAK_" + "WG_L1_5E3",
        "WG_LEAKAGE_" + "KRAUS_KEY",
        "wg_l1_" + "target",
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
    process_roles = _retired_role_words()[0] + "s"
    return frozenset(
        {
            f"{package}.carrier." + "channels",
            f"{package}.mechanisms." + "catalog",
            f"{package}.mechanisms." + process_roles,
            f"{package}.mechanisms." + "seam_" + process_roles,
            f"{package}.mechanisms." + "qutrit_" + process_roles,
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


def _retired_document_roots() -> tuple[str, ...]:
    product_validation = "_".join(("tw" + "in", "validation"))
    role_root = "_".join(("nonpauli", _retired_role_words()[0]))
    return tuple(
        "/".join(parts) + "/"
        for parts in (
            ("docs", product_validation),
            ("docs", role_root),
            ("docs", "white" + "box"),
            ("docs", "cf" + "_" + "wr"),
            ("docs", "archive"),
            ("outputs", product_validation),
            ("outputs", role_root),
        )
    )


def _retired_mechanism_number_pattern() -> re.Pattern[str]:
    return re.compile(
        rf"(?<![A-Za-z0-9]){re.escape('M')}(?:[0-9]|[12][0-9]|3[0-4])"
        r"(?![A-Za-z0-9])"
    )


def _documentation_vocabulary_violations(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    retired = _retired_namespace()
    old_env_prefix = "_".join(("QEC", "TWIN")) + "_"
    role_patterns = tuple(
        re.compile(
            rf"(?<![A-Za-z0-9]){re.escape(role)}s?(?![A-Za-z0-9])",
            re.IGNORECASE,
        )
        for role in _retired_role_words()
    )
    numbered_mechanism = _retired_mechanism_number_pattern()
    violations: set[str] = set()

    for line_number, line in enumerate(text.splitlines(), start=1):
        lowered = line.lower()
        if retired.lower() in lowered:
            violations.add(
                f"{path.relative_to(REPO_ROOT)}:{line_number}: retired namespace token"
            )
        if old_env_prefix.lower() in lowered:
            violations.add(
                f"{path.relative_to(REPO_ROOT)}:{line_number}: retired environment token"
            )
        if any(
            prefix.lower() in lowered
            for prefix in (retired + ".", retired + "_", retired + "::")
        ):
            violations.add(
                f"{path.relative_to(REPO_ROOT)}:{line_number}: retired schema/JIT/op token"
            )
        for old_root in _retired_document_roots():
            if old_root.lower() in lowered:
                violations.add(
                    f"{path.relative_to(REPO_ROOT)}:{line_number}: "
                    f"retired document/output root {old_root!r}"
                )
        numbered_match = numbered_mechanism.search(line)
        if numbered_match is not None:
            violations.add(
                f"{path.relative_to(REPO_ROOT)}:{line_number}: "
                f"retired numbered mechanism token {numbered_match.group(0)!r}"
            )
        for pattern in role_patterns:
            role_match = pattern.search(line)
            if role_match is not None:
                violations.add(
                    f"{path.relative_to(REPO_ROOT)}:{line_number}: "
                    f"retired role vocabulary {role_match.group(0)!r}"
                )
    return sorted(violations)


def _current_source_vocabulary_violations(path: Path) -> list[str]:
    """Reject retired product narrative in retained source, tests, and configs.

    ``test_scope_boundary.py`` itself is excluded by the caller because it must
    construct the forbidden values without making them available to product code.
    """

    text = path.read_text(encoding="utf-8", errors="replace")
    retired = _retired_namespace()
    old_env_prefix = "_".join(("QEC", "TWIN")) + "_"
    role_patterns = tuple(
        re.compile(
            rf"(?<![A-Za-z0-9]){re.escape(role)}s?(?![A-Za-z0-9])",
            re.IGNORECASE,
        )
        for role in _retired_role_words()
    )
    retired_stage_patterns = (
        re.compile(r"\bstage[_ -]?d\b", re.IGNORECASE),
        re.compile(r"\bH3[_ -]?H5\b", re.IGNORECASE),
        re.compile(r"\bWS[0-9]+\b"),
        re.compile(r"\bW-[A-Z]+\b"),
        re.compile(r"\bT-B\b"),
        re.compile(r"\bP4[ab]\b", re.IGNORECASE),
        re.compile(r"\bAM-[0-9]+\b", re.IGNORECASE),
        re.compile(r"\bWave-[12]\b", re.IGNORECASE),
        re.compile(
            r"\b(?:contract(?: row)?\s+(?:A1|C1|C2)|C1-asserted)\b",
            re.IGNORECASE,
        ),
    )
    numbered_mechanism = _retired_mechanism_number_pattern()
    violations: set[str] = set()

    for line_number, line in enumerate(text.splitlines(), start=1):
        lowered = line.lower()
        if retired.lower() in lowered:
            violations.add(
                f"{path.relative_to(REPO_ROOT)}:{line_number}: retired namespace token"
            )
        if old_env_prefix.lower() in lowered:
            violations.add(
                f"{path.relative_to(REPO_ROOT)}:{line_number}: retired environment token"
            )
        if "digital twin" in lowered:
            violations.add(
                f"{path.relative_to(REPO_ROOT)}:{line_number}: retired product narrative"
            )
        for old_root in _retired_document_roots():
            if old_root.lower() in lowered:
                violations.add(
                    f"{path.relative_to(REPO_ROOT)}:{line_number}: "
                    f"retired document/output root {old_root!r}"
                )
        numbered_match = numbered_mechanism.search(line)
        if numbered_match is not None:
            violations.add(
                f"{path.relative_to(REPO_ROOT)}:{line_number}: "
                f"retired numbered mechanism token {numbered_match.group(0)!r}"
            )
        for pattern in role_patterns:
            role_match = pattern.search(line)
            if role_match is not None:
                violations.add(
                    f"{path.relative_to(REPO_ROOT)}:{line_number}: "
                    f"retired role vocabulary {role_match.group(0)!r}"
                )
        for pattern in retired_stage_patterns:
            stage_match = pattern.search(line)
            if stage_match is not None:
                violations.add(
                    f"{path.relative_to(REPO_ROOT)}:{line_number}: "
                    f"retired stage/contract vocabulary {stage_match.group(0)!r}"
                )
    return sorted(violations)


def _current_source_config_paths() -> set[Path]:
    """Return current tracked/unignored source and configuration text files."""

    listed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
    )
    if listed.returncode == 0:
        relative_paths = [
            Path(raw.decode("utf-8"))
            for raw in listed.stdout.split(b"\0")
            if raw
        ]
        return {
            REPO_ROOT / relative
            for relative in relative_paths
            if (relative.name in CURRENT_ROOT_CONFIGS
                or (relative.parts and relative.parts[0] in CURRENT_SOURCE_CONFIG_ROOTS))
            and relative.suffix in CURRENT_SOURCE_TEXT_SUFFIXES
            and (REPO_ROOT / relative).is_file()
        }

    # Source archives may not carry ``.git``. Keep their installed/test surface
    # covered without treating absent repository-only tooling as a failure.
    paths = {
        REPO_ROOT / name
        for name in CURRENT_ROOT_CONFIGS
        if (REPO_ROOT / name).is_file()
    }
    for root_name in ("src", "tests", "scripts", "tools"):
        root = REPO_ROOT / root_name
        if root.exists():
            paths.update(
                path
                for path in root.rglob("*")
                if path.is_file() and path.suffix in CURRENT_SOURCE_TEXT_SUFFIXES
            )
    return paths


_INLINE_MARKDOWN_LINK = re.compile(
    r"!?\[[^\]]*\]\((?P<target><[^>]+>|[^)\s]+)"
)
_REFERENCE_MARKDOWN_LINK = re.compile(
    r"^\s*\[[^\]]+\]:\s*(?P<target><[^>]+>|\S+)",
    re.MULTILINE,
)


def _markdown_targets(text: str):
    for pattern in (_INLINE_MARKDOWN_LINK, _REFERENCE_MARKDOWN_LINK):
        for match in pattern.finditer(text):
            yield match.start(), match.group("target").strip("<>")


def _markdown_link_violations(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    violations: set[str] = set()
    for offset, raw_target in _markdown_targets(text):
        parsed = urlsplit(raw_target)
        if parsed.scheme or raw_target.startswith("//") or not parsed.path:
            continue
        local_path = Path(unquote(parsed.path))
        if local_path.is_absolute():
            resolved = (REPO_ROOT / str(local_path).lstrip("/")).resolve()
        else:
            resolved = (path.parent / local_path).resolve()
        line_number = text.count("\n", 0, offset) + 1
        try:
            resolved.relative_to(REPO_ROOT.resolve())
        except ValueError:
            violations.add(
                f"{path.relative_to(REPO_ROOT)}:{line_number}: "
                f"local Markdown link escapes repository: {raw_target!r}"
            )
            continue
        if not resolved.exists():
            violations.add(
                f"{path.relative_to(REPO_ROOT)}:{line_number}: "
                f"local Markdown link does not resolve: {raw_target!r}"
            )
    return sorted(violations)


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
        solve_exchange_angle_for_leakage_rate,
    )
    from error_coupling_simulator.noise_processes import (
        COUPLED_PROCESS_REPRESENTABILITY,
        COUPLED_PROCESS_SCHEMA,
        CoupledCycleNoiseProcess,
    )

    assert callable(certify_noise_process)
    assert callable(solve_exchange_angle_for_leakage_rate)
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


def test_current_source_tests_and_configs_have_no_retired_product_narrative() -> None:
    """Comments, docstrings, test labels, and configs are part of the product boundary."""

    boundary_file = Path(__file__).resolve()
    paths = _current_source_config_paths()
    paths.discard(boundary_file)

    violations: list[str] = []
    for path in sorted(paths):
        violations.extend(_current_source_vocabulary_violations(path))
    if violations:
        shown = sorted(set(violations))[:120]
        remainder = len(set(violations)) - len(shown)
        detail = "\n".join(f"  - {item}" for item in shown)
        if remainder:
            detail += f"\n  - ... and {remainder} more"
        raise AssertionError(
            "retired product narrative gate found "
            f"{len(set(violations))} violation(s):\n{detail}"
        )


def test_current_authority_documentation_is_clean_and_link_closed() -> None:
    """Only explicit current authority participates in the documentation gate."""

    relative_paths = CURRENT_AUTHORITY_MARKDOWN + CURRENT_AUTHORITY_STRUCTURED
    missing = [
        relative
        for relative in relative_paths
        if not (REPO_ROOT / relative).is_file()
    ]
    assert not missing, f"current authority file(s) missing: {missing!r}"

    violations: list[str] = []
    for relative in relative_paths:
        violations.extend(_documentation_vocabulary_violations(REPO_ROOT / relative))
    for relative in CURRENT_AUTHORITY_MARKDOWN:
        violations.extend(_markdown_link_violations(REPO_ROOT / relative))

    if violations:
        detail = "\n".join(f"  - {item}" for item in sorted(set(violations)))
        raise AssertionError(
            "current-authority documentation contract failed:\n" + detail
        )


def test_current_research_carrier_blockers_remain_visible() -> None:
    service_catalog = json.loads(
        (REPO_ROOT / "docs/service_status.json").read_text(encoding="utf-8")
    )
    pepo_services = [
        service
        for service in service_catalog["services"]
        if service.get("id") == "pepo_density_matrix_carrier"
    ]
    assert len(pepo_services) == 1
    assert pepo_services[0]["status"] == "RESEARCH"
    assert "remain open" in pepo_services[0]["note"].lower()

    pepo_validation = (
        REPO_ROOT / "docs/simulator_validation/PEPO_VALIDATION.md"
    ).read_text(encoding="utf-8")
    status_line = next(
        line for line in pepo_validation.splitlines() if line.startswith("Status:")
    ).lower()
    assert "research" in status_line
    assert "open" in status_line
    assert "closed" not in status_line

    fet_validation = (
        REPO_ROOT / "docs/simulator_validation/PEPS_FET_VALIDATION.md"
    ).read_text(encoding="utf-8")
    required_fet_evidence = (
        "tests/test_peps_fet.py::test_fet_env_round_preserves_stabilizer_entropy",
        "0.10860941571062639",
        "2.0",
        "1e-4",
    )
    missing_evidence = [
        item for item in required_fet_evidence if item not in fet_validation
    ]
    assert not missing_evidence, (
        "neutral PEPS/FET validation lost the current blocker evidence: "
        f"{missing_evidence!r}"
    )


def test_runtime_import_graph_is_closed_over_the_current_package() -> None:
    """Import every installed module while a finder rejects the retired namespace."""

    retired_namespace = _retired_namespace()
    retired_modules = sorted(_retired_current_modules())
    process_role = _retired_role_words()[0]
    process_role_type = process_role.title()
    retired_exports = {
        "error_coupling_simulator.carrier": sorted(
            {
                "Mechanism" + "Spec",
                "mechanism_" + "channel",
                "Shot" + "Set",
            }
        ),
        "error_coupling_simulator.certify": sorted(
            {"certify_" + process_role, "Controlled" + process_role_type}
        ),
        "error_coupling_simulator.mechanisms": sorted(
            {"QutritLeakage" + process_role_type}
        ),
        "error_coupling_simulator.noise_processes": sorted(
            {"CoupledCycle" + process_role_type}
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
