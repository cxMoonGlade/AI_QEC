"""Ownership and retired-API boundary checks for the current simulator."""

from __future__ import annotations

import ast
import json
import math
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
HISTORICAL_DOCUMENT_SNAPSHOTS = frozenset(
    {
        "docs/SCIENTIFIC_FORMULA_PROVENANCE.md",
        "docs/simulator_validation/CLEANUP_AUDIT_2026-07-14.md",
    }
)
OWNER_README_EXEMPTIONS = {
    "src/error_coupling_simulator/certify/anchors": (
        "src/error_coupling_simulator/certify/README.md",
        "public anchor-adapter leaf explicitly owned by its certify parent",
    ),
}
HARNESS_CHILD_OUTPUT_ENVIRONMENT = frozenset({"ECS_GPU_SLOT"})
ROOT_MARKDOWN_BASENAMES = frozenset(
    {"AGENTS.md", "CLAUDE.md", "CONTEXT.md"}
)
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
    numbered_adr = re.compile(r"\bADR\s+(?P<number>0[0-9]+)\b", re.IGNORECASE)
    violations: set[str] = set()

    for match in numbered_adr.finditer(text):
        number = match.group("number")
        if _numbered_adr_document_exists(number):
            continue
        line_number = text.count("\n", 0, match.start()) + 1
        violations.add(
            f"{path.relative_to(REPO_ROOT)}:{line_number}: "
            f"numbered ADR reference has no current document: {match.group(0)!r}"
        )

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


def _numbered_adr_document_exists(number: str, adr_dir: Path | None = None) -> bool:
    directory = adr_dir or (REPO_ROOT / "docs" / "adr")
    filename = re.compile(rf"{re.escape(number)}(?:[-_].+)?\.md")
    return directory.is_dir() and any(
        candidate.is_file() and filename.fullmatch(candidate.name) is not None
        for candidate in directory.iterdir()
    )


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
_BACKTICK_MARKDOWN_PATH = re.compile(
    r"`(?P<target>[^`\n]+\.md(?:#[^`\n]+)?)`"
)


def _display_repo_path(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _markdown_targets(text: str):
    for pattern in (_INLINE_MARKDOWN_LINK, _REFERENCE_MARKDOWN_LINK):
        for match in pattern.finditer(text):
            yield match.start(), match.group("target").strip("<>")


def _markdown_heading_fragments(path: Path) -> frozenset[str]:
    """Return GitHub-style fragments declared by Markdown headings."""

    fragments: set[str] = set()
    counts: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\s{0,3}#{1,6}\s+(?P<title>.*?)\s*#*\s*$", line)
        if match is None:
            continue
        title = re.sub(r"!?\[([^\]]+)\]\([^)]*\)", r"\1", match.group("title"))
        title = re.sub(r"<[^>]+>", "", title)
        title = title.replace("`", "").strip().lower()
        slug = re.sub(r"[^\w\- ]", "", title, flags=re.UNICODE)
        slug = re.sub(r"\s+", "-", slug).strip("-")
        if not slug:
            continue
        duplicate = counts.get(slug, 0)
        counts[slug] = duplicate + 1
        fragments.add(slug if duplicate == 0 else f"{slug}-{duplicate}")
    return frozenset(fragments)


def _markdown_fragment_violation(
    *, source_path: Path, line_number: int, raw_target: str, resolved: Path, fragment: str
) -> str | None:
    if not fragment or resolved.suffix.lower() != ".md" or not resolved.is_file():
        return None
    decoded = unquote(fragment)
    if decoded in _markdown_heading_fragments(resolved):
        return None
    return (
        f"{_display_repo_path(source_path)}:{line_number}: "
        f"local Markdown fragment does not resolve: {raw_target!r}"
    )


def _markdown_link_violations(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    violations: set[str] = set()
    for offset, raw_target in _markdown_targets(text):
        parsed = urlsplit(raw_target)
        if (parsed.scheme and parsed.scheme != "file") or raw_target.startswith("//") or not parsed.path:
            continue
        local_path = Path(unquote(parsed.path))
        line_number = text.count("\n", 0, offset) + 1
        if local_path.is_absolute():
            violations.add(
                f"{path.relative_to(REPO_ROOT)}:{line_number}: "
                f"absolute local Markdown link is forbidden: {raw_target!r}"
            )
            continue
        resolved = (path.parent / local_path).resolve()
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
            continue
        fragment_violation = _markdown_fragment_violation(
            source_path=path,
            line_number=line_number,
            raw_target=raw_target,
            resolved=resolved,
            fragment=parsed.fragment,
        )
        if fragment_violation is not None:
            violations.add(fragment_violation)
    return sorted(violations)


def _backtick_markdown_path_violations(
    path: Path, *, repository_root: Path = REPO_ROOT
) -> list[str]:
    """Resolve exact backticked Markdown paths in current authority prose.

    Historical snapshots are outside the caller's closed authority set. Template
    placeholders and glob patterns are examples rather than concrete file claims.
    """

    text = path.read_text(encoding="utf-8")
    violations: set[str] = set()
    for match in _BACKTICK_MARKDOWN_PATH.finditer(text):
        raw_target = match.group("target")
        if any(marker in raw_target for marker in ("<", ">", "*", "?", "[", "]")):
            continue
        parsed = urlsplit(raw_target)
        if (parsed.scheme and parsed.scheme != "file") or raw_target.startswith("//"):
            continue
        target = parsed.path if parsed.scheme == "file" else raw_target.split("#", 1)[0]
        if not target:
            continue
        local_path = Path(target)
        line_number = text.count("\n", 0, match.start()) + 1
        if local_path.is_absolute():
            violations.add(
                f"{_display_repo_path(path)}:{line_number}: "
                f"absolute backticked Markdown path is forbidden: {raw_target!r}"
            )
            continue
        elif (
            local_path.name in ROOT_MARKDOWN_BASENAMES
            and len(local_path.parts) == 1
        ) or local_path.parts[0] in {"docs", "src", "tests", "scripts", "tools"}:
            resolved = (repository_root / local_path).resolve()
        else:
            resolved = (path.parent / local_path).resolve()
        try:
            resolved.relative_to(repository_root.resolve())
        except ValueError:
            violations.add(
                f"{_display_repo_path(path)}:{line_number}: "
                f"backticked Markdown path escapes repository: {raw_target!r}"
            )
            continue
        if not resolved.is_file():
            violations.add(
                f"{_display_repo_path(path)}:{line_number}: "
                f"backticked Markdown path does not resolve: {raw_target!r}"
            )
            continue
        fragment_violation = _markdown_fragment_violation(
            source_path=path,
            line_number=line_number,
            raw_target=raw_target,
            resolved=resolved,
            fragment=parsed.fragment,
        )
        if fragment_violation is not None:
            violations.add(fragment_violation)
    return sorted(violations)


def _owner_package_directories() -> tuple[Path, ...]:
    """Return level-one/two package owners, excluding declared parent-owned leaves."""

    owners: list[Path] = []
    for init_path in PACKAGE_ROOT.rglob("__init__.py"):
        directory = init_path.parent
        depth = len(directory.relative_to(PACKAGE_ROOT).parts)
        if depth not in {1, 2}:
            continue
        relative = directory.relative_to(REPO_ROOT).as_posix()
        if relative in OWNER_README_EXEMPTIONS and not (directory / "README.md").is_file():
            continue
        owners.append(directory)
    return tuple(sorted(owners))


def _current_authority_markdown_paths() -> tuple[Path, ...]:
    declared = [REPO_ROOT / relative for relative in CURRENT_AUTHORITY_MARKDOWN]
    owner_readmes = [
        directory / "README.md"
        for directory in _owner_package_directories()
        if (directory / "README.md").is_file()
    ]
    return tuple(dict.fromkeys((*declared, *owner_readmes)))


def _assigned_names(target: ast.AST) -> set[str]:
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.Tuple, ast.List)):
        return set().union(*(_assigned_names(item) for item in target.elts))
    return set()


def _module_string_bindings(tree: ast.Module) -> dict[str, str]:
    """Return single-assignment module strings; ambiguous ECS aliases fail closed."""

    assignments: dict[str, list[str | None]] = {}
    for statement in tree.body:
        if not isinstance(statement, (ast.Assign, ast.AnnAssign)):
            continue
        targets = statement.targets if isinstance(statement, ast.Assign) else (statement.target,)
        value = _literal_string(statement.value)
        for target in targets:
            for name in _assigned_names(target):
                assignments.setdefault(name, []).append(value)
    ambiguous = sorted(
        name
        for name, values in assignments.items()
        if len(values) != 1
        and any(value is not None and value.startswith("ECS_") for value in values)
    )
    assert not ambiguous, f"ambiguous module environment-key binding(s): {ambiguous!r}"
    return {
        name: values[0]
        for name, values in assignments.items()
        if len(values) == 1 and values[0] is not None
    }


def _resolved_string(node: ast.AST, bindings: dict[str, str]) -> str | None:
    literal = _literal_string(node)
    if literal is not None:
        return literal
    if isinstance(node, ast.Name):
        return bindings.get(node.id)
    return None


def _lexical_nodes(body: list[ast.stmt]):
    pending: list[ast.AST] = list(body)
    while pending:
        item = pending.pop()
        yield item
        if not isinstance(
            item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
        ):
            pending.extend(ast.iter_child_nodes(item))


def _function_bound_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    names = {
        argument.arg
        for argument in (
            *node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs
        )
    }
    for item in _lexical_nodes(node.body):
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(item.name)
            continue
        if isinstance(item, ast.Assign):
            names.update(*(_assigned_names(target) for target in item.targets))
        elif isinstance(item, (ast.AnnAssign, ast.NamedExpr, ast.For, ast.AsyncFor)):
            names.update(_assigned_names(item.target))
    return names


def _environment_accesses(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    parents = {
        child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)
    }
    scopes: dict[ast.AST, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            scopes[node] = _function_bound_names(node)
        elif isinstance(node, ast.Lambda):
            scopes[node] = {
                argument.arg
                for argument in (
                    *node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs
                )
            }
    parameter_order = lambda node: tuple(
        argument.arg for argument in (*node.args.posonlyargs, *node.args.args)
    )
    knobs = {
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        if node.name == "_knob"
        and parameter_order(node) == ("reg", "section", "key", "envname", "default", "cast")
        and not node.args.kwonlyargs
        and node.args.vararg is None
        and node.args.kwarg is None
    }
    allow_knob = path.resolve() == (TEST_ROOT / "harness" / "mutation.py").resolve()
    if allow_knob:
        assert len(knobs) == 1, "tests/harness/mutation.py must contain one closed _knob adapter"

    keys: list[ast.AST] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and node.args and _dotted_name(node.func) in {
            "os.environ.get", "os.getenv"
        }:
            keys.append(node.args[0])
        elif isinstance(node, ast.Subscript) and _dotted_name(node.value) == "os.environ":
            keys.append(node.slice)
        elif isinstance(node, ast.Compare) and any(
            _dotted_name(item) == "os.environ" for item in node.comparators
        ):
            keys.append(node.left)

    bindings = _module_string_bindings(tree)
    names: set[str] = set()
    unresolved: set[str] = set()
    for key in keys:
        ancestors: list[ast.AST] = []
        parent = parents.get(key)
        while parent is not None:
            ancestors.append(parent)
            parent = parents.get(parent)
        shadowed = set().union(*(scopes[node] for node in ancestors if node in scopes))
        value = None if isinstance(key, ast.Name) and key.id in shadowed else _resolved_string(
            key, bindings
        )
        dynamic_knob = (
            allow_knob
            and isinstance(key, ast.Name)
            and key.id == "envname"
            and any(node in knobs for node in ancestors)
        )
        if value is not None:
            names.add(value)
        elif not dynamic_knob:
            unresolved.add(ast.unparse(key))
    assert not unresolved, f"unresolved environment-key access in {path}: {sorted(unresolved)!r}"
    return {name for name in names if name.startswith("ECS_")}


def _runtime_environment_contract() -> frozenset[str]:
    paths = tuple(PACKAGE_ROOT.rglob("*.py")) + (TEST_ROOT / "conftest.py",)
    return frozenset().union(*(_environment_accesses(path) for path in paths))


def _environment_mapping_writes(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    bindings = _module_string_bindings(tree)
    names: set[str] = set()
    unresolved: set[str] = set()
    scopes = [tree.body] + [
        node.body
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    for body in scopes:
        nodes: list[ast.AST] = []
        pending: list[ast.AST] = list(body)
        while pending:
            node = pending.pop()
            nodes.append(node)
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                pending.extend(ast.iter_child_nodes(node))
        assignments = {
            name: node.value
            for node in nodes
            if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None
            for target in (node.targets if isinstance(node, ast.Assign) else (node.target,))
            for name in _assigned_names(target)
        }
        mappings: set[str] = set()

        def _source(node: ast.AST) -> bool:
            if _dotted_name(node) == "os.environ" or (
                isinstance(node, ast.Name) and node.id in mappings
            ):
                return True
            return isinstance(node, ast.IfExp) and any(
                _dotted_name(branch) == "os.environ" for branch in (node.body, node.orelse)
            ) and all(
                _dotted_name(branch) == "os.environ"
                or (isinstance(branch, ast.Name) and branch.id.lower().endswith("env"))
                for branch in (node.body, node.orelse)
            )

        changed = True
        while changed:
            before = len(mappings)
            for name, value in assignments.items():
                if not isinstance(value, ast.Call) or value.keywords:
                    continue
                if _dotted_name(value.func) == "dict" and len(value.args) == 1:
                    copied = _source(value.args[0])
                else:
                    copied = (
                        isinstance(value.func, ast.Attribute)
                        and value.func.attr == "copy"
                        and not value.args
                        and _source(value.func.value)
                    )
                if copied:
                    mappings.add(name)
            changed = len(mappings) != before
        for target in (
            target
            for node in nodes
            if isinstance(node, (ast.Assign, ast.AnnAssign))
            for target in (node.targets if isinstance(node, ast.Assign) else (node.target,))
            if isinstance(target, ast.Subscript)
            if isinstance(target.value, ast.Name) and target.value.id in mappings
        ):
            value = _resolved_string(target.slice, bindings)
            if value is None:
                unresolved.add(ast.unparse(target.slice))
            elif value.startswith("ECS_"):
                names.add(value)
    assert not unresolved, (
        f"unresolved child-environment key write in {path}: {sorted(unresolved)!r}"
    )
    return names


def _knob_environment_bindings(path: Path) -> set[tuple[str, str, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and _dotted_name(node.func) == "_knob"
    ]
    assert all(
        len(node.args) >= 4
        and all(_literal_string(node.args[index]) is not None for index in (1, 2, 3))
        for node in calls
    ), "tests/harness/mutation.py has a dynamic _knob binding"
    return {
        tuple(_literal_string(node.args[index]) for index in (1, 2, 3))
        for node in calls
        if _literal_string(node.args[3]).startswith("ECS_")
    }


def _harness_environment_contract() -> frozenset[str]:
    config = json.loads((TEST_ROOT / "harness_config.json").read_text(encoding="utf-8"))
    configured_bindings = {
        (section, str(key)): value
        for section, payload in config.items()
        if isinstance(payload, dict) and isinstance(payload.get("_env"), dict)
        for key, value in payload["_env"].items()
        if isinstance(value, str) and value.startswith("ECS_")
    }
    configured = set(configured_bindings.values())
    inputs: set[str] = set()
    outputs: set[str] = set()
    knob_bindings: set[tuple[str, str, str]] = set()
    for path in (TEST_ROOT / "harness").rglob("*.py"):
        inputs.update(_environment_accesses(path))
        outputs.update(_environment_mapping_writes(path))
        if path.name == "mutation.py":
            knob_bindings.update(_knob_environment_bindings(path))
    mismatches = sorted(
        (section, key, environment, configured_bindings.get((section, key)))
        for section, key, environment in knob_bindings
        if configured_bindings.get((section, key)) != environment
    )
    assert not mismatches, f"harness _knob/config mismatch(es): {mismatches!r}"
    inputs.update(environment for _, _, environment in knob_bindings)
    assert inputs <= configured, f"unregistered harness ECS input(s): {sorted(inputs-configured)!r}"
    assert outputs <= configured | HARNESS_CHILD_OUTPUT_ENVIRONMENT, (
        f"unregistered harness ECS output(s): {sorted(outputs-configured-HARNESS_CHILD_OUTPUT_ENVIRONMENT)!r}"
    )
    assert HARNESS_CHILD_OUTPUT_ENVIRONMENT <= outputs, (
        "declared harness child-output(s) not AST-located: "
        f"{sorted(HARNESS_CHILD_OUTPUT_ENVIRONMENT - outputs)!r}"
    )
    assert configured <= inputs | outputs, (
        f"harness_config ECS key(s) lack a consumer: {sorted(configured-inputs-outputs)!r}"
    )
    return frozenset(configured | inputs | outputs)


def _documented_environment_section(text: str, heading: str) -> frozenset[str]:
    match = re.search(
        rf"^(?P<marks>#{{1,6}})[ \t]+{re.escape(heading)}[ \t]*#*[ \t]*$",
        text,
        re.MULTILINE,
    )
    if match is None:
        return frozenset()
    body_start = match.end()
    level = len(match.group("marks"))
    next_heading = re.search(rf"^#{{1,{level}}}[ \t]+", text[body_start:], re.MULTILINE)
    stop = body_start + next_heading.start() if next_heading is not None else len(text)
    return frozenset(re.findall(r"`(ECS_[A-Z0-9_]+)`", text[body_start:stop]))


def _forbidden_probability_floor_symbols() -> frozenset[str]:
    return frozenset(
        {
            "NUMERICAL_" + "FLOOR",
            "positive_" + "floor",
            "probability_" + "floor",
        }
    )


def _is_numerical_zero_expression(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Name)
        and node.id in {"NUMERICAL_ZERO", "NUMERICAL_FLOOR"}
    ) or (
        isinstance(node, ast.Constant)
        and isinstance(node.value, (int, float))
        and float(node.value) == 1e-12
    )


def _is_one_minus_numerical_zero(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.BinOp)
        and isinstance(node.op, ast.Sub)
        and isinstance(node.left, ast.Constant)
        and isinstance(node.left.value, (int, float))
        and float(node.left.value) == 1.0
        and _is_numerical_zero_expression(node.right)
    )


def _numeric_literal(node: ast.AST) -> float | None:
    sign = -1.0 if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub) else 1.0
    node = node.operand if sign < 0.0 else node
    return (
        sign * float(node.value)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float))
        else None
    )


def _call_has_bound(node: ast.AST, name: str, predicate) -> bool:
    return (
        isinstance(node, ast.Call)
        and _dotted_name(node.func) == name
        and any(predicate(argument) for argument in node.args)
    )


def _is_probability_interval_clamp(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    name = _dotted_name(node.func)
    if name in {"min", "max"} and len(node.args) == 2:
        inner, inner_bound, outer_bound = (
            ("max", _is_numerical_zero_expression, _is_one_minus_numerical_zero)
            if name == "min"
            else ("min", _is_one_minus_numerical_zero, _is_numerical_zero_expression)
        )
        return any(
            outer_bound(outer) and _call_has_bound(value, inner, inner_bound)
            for value, outer in ((node.args[0], node.args[1]), (node.args[1], node.args[0]))
        )
    if name.endswith("clip") and len(node.args) >= 3:
        return _is_numerical_zero_expression(node.args[1]) and _is_one_minus_numerical_zero(
            node.args[2]
        )
    if name.endswith("clamp"):
        bounds = {keyword.arg: keyword.value for keyword in node.keywords if keyword.arg}
        return _is_numerical_zero_expression(
            bounds.get("min", ast.Constant(value=None))
        ) and _is_one_minus_numerical_zero(
            bounds.get("max", ast.Constant(value=None))
        )
    return False


def _is_symmetric_sixty_clamp(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call) or len(node.args) != 2:
        return False
    patterns = {"max": (-60.0, "min", 60.0), "min": (60.0, "max", -60.0)}
    if _dotted_name(node.func) not in patterns:
        return False
    outer_value, inner_name, inner_value = patterns[_dotted_name(node.func)]
    return any(
        _numeric_literal(outer) == outer_value
        and isinstance(inner, ast.Call)
        and _dotted_name(inner.func) == inner_name
        and any(_numeric_literal(argument) == inner_value for argument in inner.args)
        for outer, inner in ((node.args[0], node.args[1]), (node.args[1], node.args[0]))
    )


def _probability_threshold_policy_violations(path: Path) -> list[str]:
    """Reject threshold-created probability mass without banning denominator guards."""

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    violations: set[str] = set()
    relative = _display_repo_path(path)
    for node in ast.walk(tree):
        if _is_probability_interval_clamp(node):
            violations.add(
                f"{relative}:{node.lineno}: numerical threshold clamps a unit probability interval"
            )
        if (
            path.name == "numerics.py"
            and isinstance(node, ast.Call)
            and _dotted_name(node.func) in {"min", "max"}
            and any(_is_numerical_zero_expression(argument) for argument in node.args)
        ):
            violations.add(
                f"{relative}:{node.lineno}: shared numerics implements a positive floor"
            )
        if _is_symmetric_sixty_clamp(node):
            violations.add(
                f"{relative}:{node.lineno}: finite scientific map is replaced by a [-60, 60] cap"
            )

    for function in (
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ):
        probability_names: set[str] = set()
        assignments = [
            node
            for node in _lexical_nodes(function.body)
            if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None
        ]
        changed = True
        while changed:
            before = len(probability_names)
            for node in assignments:
                value_names = {
                    item.id for item in ast.walk(node.value) if isinstance(item, ast.Name)
                }
                from_probability = "marginals" in value_names or any(
                    isinstance(item, ast.Call)
                    and _dotted_name(item.func).endswith("_validate_probability")
                    for item in ast.walk(node.value)
                )
                if from_probability or value_names & probability_names:
                    targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
                    probability_names.update(
                        *(_assigned_names(target) for target in targets)
                    )
            changed = len(probability_names) != before
        for node in _lexical_nodes(function.body):
            if not isinstance(node, ast.Compare):
                continue
            operands = (node.left, *node.comparators)
            for left, right in zip(operands, operands[1:]):
                left_names = {
                    item.id for item in ast.walk(left) if isinstance(item, ast.Name)
                }
                right_names = {
                    item.id for item in ast.walk(right) if isinstance(item, ast.Name)
                }
                if (
                    bool(left_names & probability_names)
                    and _is_numerical_zero_expression(right)
                ) or (
                    bool(right_names & probability_names)
                    and _is_numerical_zero_expression(left)
                ):
                    violations.add(
                        f"{relative}:{node.lineno}: probability-derived value uses "
                        "NUMERICAL_ZERO as structural zero"
                    )
    return sorted(violations)


def _current_probability_threshold_policy_violations() -> list[str]:
    violations: list[str] = []
    for path in PACKAGE_ROOT.rglob("*.py"):
        violations.extend(_probability_threshold_policy_violations(path))
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

    markdown_paths = _current_authority_markdown_paths()
    historical_paths = {
        (REPO_ROOT / relative).resolve() for relative in HISTORICAL_DOCUMENT_SNAPSHOTS
    }
    assert historical_paths.isdisjoint(path.resolve() for path in markdown_paths)

    relative_paths = CURRENT_AUTHORITY_MARKDOWN + CURRENT_AUTHORITY_STRUCTURED
    missing = [
        relative
        for relative in relative_paths
        if not (REPO_ROOT / relative).is_file()
    ]
    assert not missing, f"current authority file(s) missing: {missing!r}"

    violations: list[str] = []
    for relative in CURRENT_AUTHORITY_STRUCTURED:
        violations.extend(_documentation_vocabulary_violations(REPO_ROOT / relative))
    for path in markdown_paths:
        violations.extend(_documentation_vocabulary_violations(path))
        violations.extend(_markdown_link_violations(path))
        violations.extend(_backtick_markdown_path_violations(path))

    if violations:
        detail = "\n".join(f"  - {item}" for item in sorted(set(violations)))
        raise AssertionError(
            "current-authority documentation contract failed:\n" + detail
        )


def test_level_one_and_two_owner_packages_have_readme_files() -> None:
    """Every current level-one/two package owner has one local owner document."""

    exemption_errors: list[str] = []
    for relative, (owner_readme, reason) in OWNER_README_EXEMPTIONS.items():
        directory = REPO_ROOT / relative
        owner_path = REPO_ROOT / owner_readme
        valid = (
            bool(reason.strip())
            and (directory / "__init__.py").is_file()
            and owner_path == directory.parent / "README.md"
            and owner_readme in CURRENT_AUTHORITY_MARKDOWN
            and owner_path.is_file()
            and f"{directory.name}/" in owner_path.read_text(encoding="utf-8")
        )
        if not valid:
            exemption_errors.append(f"invalid parent-owned leaf: {relative} -> {owner_readme}")
    assert not exemption_errors, f"invalid owner README exemption(s): {exemption_errors!r}"

    missing = [
        (directory / "README.md").relative_to(REPO_ROOT).as_posix()
        for directory in _owner_package_directories()
        if not (directory / "README.md").is_file()
    ]
    assert not missing, f"owner package README(s) missing: {missing!r}"


def test_claude_documents_exact_runtime_and_harness_environment_contracts() -> None:
    """Document actual environment access separately from harness-only controls."""

    text = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    actual = (_runtime_environment_contract(), _harness_environment_contract())
    documented = tuple(
        _documented_environment_section(text, heading)
        for heading in ("Runtime and test-surface environment", "Harness-only environment")
    )
    assert actual[0].isdisjoint(actual[1]), f"runtime/harness ECS overlap: {actual[0]&actual[1]}"
    assert documented == actual, (
        f"CLAUDE ECS contract mismatch: documented={documented!r}, actual={actual!r}"
    )


def test_environment_extractor_is_scope_and_mapping_aware(tmp_path: Path) -> None:
    """A similarly named local or ordinary mapping cannot fabricate an ECS contract."""

    documented_probe = (
        "## Runtime and test-surface environment\n"
        "`ECS_RUNTIME`\n"
        "### Nested details\n"
        "`ECS_NESTED`\n"
        "## Runtime and test-surface environment appendix\n"
        "`ECS_OUTSIDE`\n"
    )
    assert _documented_environment_section(
        documented_probe, "Runtime and test-surface environment"
    ) == {"ECS_RUNTIME", "ECS_NESTED"}

    probe = tmp_path / "environment_probe.py"
    probe.write_text(
        'import os\nMODULE_KEY="ECS_MODULE"\n'
        'def f():\n metrics={}\n metrics["ECS_NOT_ENV"]=1\n'
        ' meta=dict(snapshot=os.environ)\n meta["ECS_NOT_ENV"]=1\n'
        ' base=dict(os.environ)\n child=base.copy()\n child["ECS_CHILD"]=1\n'
        'def g(): return os.getenv(MODULE_KEY)\n', encoding="utf-8"
    )
    assert _environment_accesses(probe) == {"ECS_MODULE"}
    assert _environment_mapping_writes(probe) == {"ECS_CHILD"}
    cases = (
        ("ambiguous.py", 'import os\nK="ECS_A"\nos.getenv(K)\nK="ECS_B"\n', _environment_accesses, "ambiguous module"),
        (
            "shadow.py", 'import os\nK="ECS_MODULE"\ndef f(K): return os.getenv(K)\n',
            _environment_accesses, "unresolved environment-key",
        ),
        (
            "local_input.py", 'import os\ndef f():\n k="ECS_LOCAL"\n return os.getenv(k)\n',
            _environment_accesses, "unresolved environment-key",
        ),
        (
            "local_output.py",
            'import os\ndef f():\n k="ECS_LOCAL"\n e=dict(os.environ)\n e[k]=1\n',
            _environment_mapping_writes, "unresolved child-environment",
        ),
        (
            "fake_knob.py",
            'import os\ndef _knob(reg,section,key,envname,default,cast): '
            'return os.getenv(envname)\n',
            _environment_accesses, "unresolved environment-key",
        ),
    )
    for filename, source, extractor, message in cases:
        candidate = tmp_path / filename
        candidate.write_text(source, encoding="utf-8")
        try:
            extractor(candidate)
        except AssertionError as exc:
            assert message in str(exc)
        else:
            raise AssertionError(f"environment extractor did not fail closed: {filename}")


def test_backticked_path_and_adr_extractors_reject_only_concrete_breakage(
    tmp_path: Path,
) -> None:
    """Path examples stay exempt, while concrete local claims remain closed."""

    note = tmp_path / "My Note.md"
    note.write_text("# Current section\n", encoding="utf-8")
    authority = tmp_path / "authority.md"
    authority.write_text(
        "`My Note.md#current-section` `My Note.md#missing-section` "
        "`https://example.org/spec.md` `<placeholder>.md` `notes/*.md` "
        "`/absolute/local.md` `file:///tmp/local.md` `missing.md`\n",
        encoding="utf-8",
    )
    violations = _backtick_markdown_path_violations(
        authority, repository_root=tmp_path
    )
    assert len(violations) == 4
    assert sum("absolute backticked Markdown path is forbidden" in item for item in violations) == 2
    assert sum("backticked Markdown path does not resolve" in item for item in violations) == 1
    assert sum("fragment does not resolve" in item for item in violations) == 1

    adr_dir = tmp_path / "adr"
    adr_dir.mkdir()
    (adr_dir / "00110-unrelated.md").write_text("wrong\n", encoding="utf-8")
    assert not _numbered_adr_document_exists("0011", adr_dir)
    (adr_dir / "0011-current.md").write_text("current\n", encoding="utf-8")
    assert _numbered_adr_document_exists("0011", adr_dir)


def test_probability_threshold_extractor_catches_inline_corruptions(
    tmp_path: Path,
) -> None:
    """Renaming or inlining a floor cannot make the static gate vacuously green."""

    numerics_probe = tmp_path / "numerics.py"
    numerics_probe.write_text(
        """\
NUMERICAL_ZERO = 1e-12
def renamed_floor(value):
    return max(NUMERICAL_ZERO, value)
""",
        encoding="utf-8",
    )
    assert len(_probability_threshold_policy_violations(numerics_probe)) == 1

    probability_probe = tmp_path / "probability_mapping.py"
    probability_probe.write_text(
        """\
NUMERICAL_ZERO = 1e-12
def map_probability(raw, shift):
    probability = _validate_probability("p", raw)
    value = probability
    if value <= NUMERICAL_ZERO:
        return 0.0
    value = min(max(value, NUMERICAL_ZERO), 1.0 - NUMERICAL_ZERO)
    bounded = max(-60.0, min(60.0, shift))
    relative = raw / max(abs(shift), NUMERICAL_ZERO)
    return value, bounded, relative
def unrelated(marginal_cost, x, y):
    if marginal_cost <= NUMERICAL_ZERO:
        return combine(max(x, NUMERICAL_ZERO), min(y, 1.0 - NUMERICAL_ZERO))
""",
        encoding="utf-8",
    )
    assert len(_probability_threshold_policy_violations(probability_probe)) == 3

    safe_current_files = (
        "src/error_coupling_simulator/frontend/pij.py",
        "src/error_coupling_simulator/carrier/pepo/dynamics.py",
        "src/error_coupling_simulator/carrier/peps/trajectory.py",
        "src/error_coupling_simulator/carrier/peps/stab_tt.py",
    )
    assert all(
        not _probability_threshold_policy_violations(REPO_ROOT / relative)
        for relative in safe_current_files
    )


def test_shared_numerics_exposes_no_probability_floor_api() -> None:
    """The shared policy exposes a comparison threshold, not probability-mass helpers."""

    import error_coupling_simulator.numerics as numerics

    present = sorted(
        name for name in _forbidden_probability_floor_symbols() if hasattr(numerics, name)
    )
    assert not present, f"forbidden numerical-floor API remains importable: {present!r}"


def test_current_source_has_no_probability_threshold_floor_pattern() -> None:
    """Static policy catches renamed/inlined floors but permits non-probability guards."""

    violations = _current_probability_threshold_policy_violations()
    assert not violations, "probability-threshold policy violation(s):\n  - " + "\n  - ".join(
        violations
    )


def test_source_structural_zeros_preserve_tiny_positive_values() -> None:
    """A comparison tolerance cannot turn a positive source parameter into exact zero."""

    from error_coupling_simulator.source.coupling import (
        SourceCouplingConfig,
        _modulate_positive_rate,
        _modulate_probability_logit,
        drift_to_t2,
    )
    from error_coupling_simulator.frontend.noise_spec import SourceStimPauliRule
    from error_coupling_simulator.source.process import (
        RTNSource,
        SourceTimeline,
        TemporalStormSPPSource,
        _rtn_flip_probability,
    )

    def _close(left: float, right: float) -> bool:
        return math.isclose(
            float(left),
            float(right),
            rel_tol=8.0 * sys.float_info.epsilon,
            abs_tol=0.0,
        )

    def _rejects_nonrepresentable(function) -> bool:
        try:
            function()
        except ValueError:
            return True
        return False

    def _returns_close(function, expected: float) -> bool:
        try:
            return _close(function(), expected)
        except (OverflowError, ValueError):
            return False

    def _mp_product(base: float, shift: float) -> float:
        import mpmath

        with mpmath.workdps(200):
            base_num, base_den = float(base).as_integer_ratio()
            shift_num, shift_den = float(shift).as_integer_ratio()
            exact_base = mpmath.mpf(base_num) / base_den
            exact_shift = mpmath.mpf(shift_num) / shift_den
            return float(exact_base * mpmath.exp(exact_shift))

    def _returns_within_ulps(function, expected: float, *, max_ulps: int) -> bool:
        try:
            value = float(function())
        except (OverflowError, ValueError):
            return False
        return abs(value - expected) <= max_ulps * math.ulp(expected)

    p_min = math.nextafter(0.0, 1.0)
    p_max = math.nextafter(1.0, 0.0)
    y_min = math.log(p_min) - math.log1p(-p_min)
    y_max = math.log(p_max) - math.log1p(-p_max)

    def _pins_open_probability_bound(mapper, *, lower: bool) -> bool:
        boundary = y_min if lower else y_max
        inside = math.nextafter(boundary, math.inf if lower else -math.inf)
        outside = math.nextafter(boundary, -math.inf if lower else math.inf)
        expected = p_min if lower else p_max
        try:
            boundary_value = mapper(boundary)
            inside_value = mapper(inside)
        except (OverflowError, ValueError):
            return False
        return (
            boundary_value == expected
            and inside_value == expected
            and _rejects_nonrepresentable(lambda: mapper(outside))
        )

    tiny = 0.5e-12
    near_one = float.fromhex("0x1.fffffffffffffp-1")
    exact_rate = 1e-4 * math.exp(-100.0)
    exp_y = math.exp(-100.0)
    exact_probability = exp_y / (1.0 + exp_y)
    timeline = SourceTimeline(
        name="negative_logit_probe",
        n_cycles=1,
        cycle_time_ns=1.0,
        payload={"z": (-100.0,)},
    )
    rule = SourceStimPauliRule(
        position="before",
        match_kind="measurement_type",
        measure_name="M",
        noise="X_ERROR",
        payload_key="z",
        base_p=0.5,
        sensitivity=1.0,
        z_scale=1.0,
    )

    def _frontend_probability_at(logit_value: float) -> float:
        return rule.probability_for(
            SourceTimeline(
                name="asymmetric_logit_boundary",
                n_cycles=1,
                cycle_time_ns=1.0,
                payload={"z": (logit_value,)},
            ),
            cycle_index=0,
            targets=(0,),
        )
    rejected_nonzero_shift = False
    try:
        _modulate_probability_logit(0.0, 1.0, tiny, name="p")
    except ValueError:
        rejected_nonzero_shift = True
    try:
        preserved_zero_shift = (
            _modulate_probability_logit(0.0, 0.0, 0.5, name="p") == 0.0
            and _modulate_positive_rate(0.0, 0.0, 0.5, name="rate") == 0.0
        )
    except ValueError:
        preserved_zero_shift = False
    zero_base_shift_contract = rejected_nonzero_shift and preserved_zero_shift
    config = SourceCouplingConfig(gamma_phi_base_per_ns=tiny, gamma_phi_sensitivity=0.0)
    gamma, tphi = drift_to_t2(0.0, config)
    stationary = TemporalStormSPPSource(
        a=0.25e-12, b=0.5e-12
    ).stationary_distribution.tolist()
    tiny_markov = 1e-20
    tiny_storm = TemporalStormSPPSource(a=tiny_markov, b=2.0 * tiny_markov)
    fixed_storm = TemporalStormSPPSource.from_fixed_marginal(
        marginal=(0.9, 0.04, 0.03, 0.03),
        q_storm=(0.7, 0.1, 0.1, 0.1),
        storm_probability=0.2,
        correlation_length_cycles=1e17,
    )
    checks = (
        ("tiny positive rate lost zero-shift identity",
         _modulate_positive_rate(tiny, 7.0, 0.0, name="rate") == tiny),
        ("tiny positive probability lost zero-shift identity",
         _modulate_probability_logit(tiny, 7.0, 0.0, name="p") == tiny),
        ("near-one probability lost zero-shift identity",
         _modulate_probability_logit(near_one, 0.0, 0.0, name="p") == near_one),
        ("finite positive rate was capped", _close(
            _modulate_positive_rate(1e-4, -100.0, 1.0, name="rate"), exact_rate)),
        ("finite logit probability was capped", _close(
            _modulate_probability_logit(0.5, -100.0, 1.0, name="p"), exact_probability)),
        ("frontend projection was capped", _close(
            rule.probability_for(timeline, cycle_index=0, targets=(0,)), exact_probability)),
        ("zero base did not distinguish zero from nonzero shift", zero_base_shift_contract),
        ("tiny dephasing rate produced infinite Tphi", _close(gamma, tiny) and _close(tphi, 1.0 / tiny)),
        ("tiny transition rates produced degenerate mass", all(
            _close(v, e)
            for v, e in zip(stationary, (2.0 / 3.0, 1.0 / 3.0), strict=True)
        )),
        ("tiny RTN rate produced zero flip probability", _close(
            _rtn_flip_probability(tiny_markov), -0.5 * math.expm1(-2.0 * tiny_markov)
        )),
        ("tiny transition rates produced infinite correlation length", _close(
            tiny_storm.correlation_length_cycles,
            -1.0 / math.log1p(-3.0 * tiny_markov),
        )),
        ("long fixed correlation produced zero transition rates", _close(
            fixed_storm.a, 0.2 * -math.expm1(-1e-17)
        ) and _close(fixed_storm.b, 0.8 * -math.expm1(-1e-17))),
        ("positive rate underflow did not fail closed", _rejects_nonrepresentable(
            lambda: _modulate_positive_rate(1.0, -1000.0, 1.0, name="rate")
        )),
        ("positive rate overflow did not fail closed", _rejects_nonrepresentable(
            lambda: _modulate_positive_rate(1e308, 100.0, 1.0, name="rate")
        )),
        ("lower logit representability boundary was not fail-closed",
         _pins_open_probability_bound(
             lambda y: _modulate_probability_logit(0.5, y, 1.0, name="p"),
             lower=True,
         )),
        ("upper logit representability boundary was not fail-closed",
         _pins_open_probability_bound(
             lambda y: _modulate_probability_logit(0.5, y, 1.0, name="p"),
             lower=False,
         )),
        ("frontend asymmetric logit boundaries were not fail-closed",
         _pins_open_probability_bound(_frontend_probability_at, lower=True)
         and _pins_open_probability_bound(_frontend_probability_at, lower=False)),
        ("representable rate was lost to an intermediate exponential endpoint",
         _returns_within_ulps(
             lambda: _modulate_positive_rate(1e-300, 710.0, 1.0, name="rate"),
             _mp_product(1e-300, 710.0),
             max_ulps=1,
         )
         and _returns_within_ulps(
             lambda: _modulate_positive_rate(1e300, -1000.0, 1.0, name="rate"),
             _mp_product(1e300, -1000.0),
             max_ulps=1,
         )),
        ("Tphi reciprocal overflow did not fail closed", _rejects_nonrepresentable(
            lambda: drift_to_t2(
                0.0,
                SourceCouplingConfig(
                    gamma_phi_base_per_ns=float.fromhex("0x0.0000000000001p-1022"),
                    gamma_phi_sensitivity=0.0,
                ),
            )
        )),
        ("positive RTN rate produced endpoint flip probability", _rejects_nonrepresentable(
            lambda: _rtn_flip_probability(1e308)
        )),
        ("positive RTN rate produced endpoint autocorrelation", _rejects_nonrepresentable(
            lambda: RTNSource(gamma_per_cycle=tiny_markov).autocorr_base
        )),
        ("fixed-marginal transition underflow did not fail closed", _rejects_nonrepresentable(
            lambda: TemporalStormSPPSource.from_fixed_marginal(
                marginal=(0.9, 0.04, 0.03, 0.03),
                q_storm=(0.7, 0.1, 0.1, 0.1),
                storm_probability=float.fromhex("0x0.0000000000001p-1022"),
                correlation_length_cycles=1e308,
            )
        )),
    )
    failures = [message for message, passed in checks if not passed]
    assert not failures, "structural-zero falsifier(s) fired:\n  - " + "\n  - ".join(
        failures
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
        "research carrier",
        "B1_3",
        "stored dimension 12",
        "structural local rank 4",
        "eps_fid=1e-8",
        "Gamma",
        "historical pre-repair evidence",
        "all-noop state",
        "clean-head fresh-process replay artifact",
        "full-record faithfulness",
    )
    missing_evidence = [
        item for item in required_fet_evidence if item not in fet_validation
    ]
    assert not missing_evidence, (
        "neutral PEPS/FET validation lost current repair or open-boundary evidence: "
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
