#!/usr/bin/env python
r"""Generate docs/CODE_MAP.md — the current, drift-proof code and service inventory.

WHY THIS EXISTS
---------------
Hand-written codebase maps (build contracts, handoffs, memory files) drift from the code and
then MISLEAD (a stale "NOT YET EARNED" list said modules were absent when they were built). This
tool derives the module map FROM THE CODE by ast-parsing every module (NO imports, NO CUDA, no
project logic) — so "what exists" cannot go stale. A tiny hand-maintained status overlay
(docs/code_status.json) adds the one thing code can't state mechanically (ACTIVE / PLACEHOLDER /
ARCHIVED + a one-line "what to know"), and this tool DRIFT-CHECKS that overlay against the code:
packages present in code but missing a status entry, and status entries whose target no longer
exists, are both flagged loudly so the overlay stays honest.

The runtime service catalog is separately hand-maintained in ``docs/service_status.json``. This
tool validates service IDs, repository paths, package-owned entry points, declared dependency
extras, negative-control entry points, and flow references before rendering a service matrix and
the complete Mermaid flow. It also performs the reverse check that EVERY Python module shipped in
``error_coupling_simulator`` (including namespace ``__init__.py`` files) is assigned either to one
or more runtime services or to an explicit non-service support role. A new unclassified module is
therefore a hard failure instead of a silently omitted capability. Finally, it AST-checks both the
installed package and every declared acceptance test for executable ``qec_twin`` import/resolution
edges. Historical persisted schema strings may remain, but a current simulator service cannot pass
through the legacy shim. The content hash covers code, both overlays, ``pyproject.toml``, and the
legacy-symlink target, so changing service/distribution boundaries also makes the map stale.

USE
---
    python tools/gen_code_map.py            # regenerate docs/CODE_MAP.md (run after ANY src change)
    python tools/gen_code_map.py --check    # exit 1 if the map or service contract is stale/invalid
                                            # (no rewrite) — for a pre-commit hook / CI

The map header stamps a complete-input content hash + git HEAD, so staleness is detectable. This is
a maintenance tool (ast + filesystem only); it is safe to run anywhere and needs no GPU / no aiqec env.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
import tomllib
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
# Walk real package directories under src/. Directory symlinks are deliberately not descended;
# ``src/qec_twin`` is reported separately as the legacy boundary. Package keys are fully-qualified
# relative to src/ (for example ``error_coupling_simulator/source``).
SRC = REPO / "src"
RUNTIME_PACKAGE = SRC / "error_coupling_simulator"
TOOLS = REPO / "tools"          # dev tooling (not shipped): gen_code_map, sync_obsidian, ...
TESTS_HARNESS = REPO / "tests" / "harness"   # the test/coverage harness lives WITH the tests (proc/gpu_pool/gate/mutation)
_ROOTS = (SRC, TOOLS, TESTS_HARNESS)
STATUS_PATH = REPO / "docs" / "code_status.json"
SERVICE_STATUS_PATH = REPO / "docs" / "service_status.json"
PROJECT_PATH = REPO / "pyproject.toml"
MANIFEST_PATH = REPO / "MANIFEST.in"
MAP_PATH = REPO / "docs" / "CODE_MAP.md"
GATES_DIR = REPO / "docs" / "twin_validation" / "gates"

_HASH_MARKER = "<!-- code-map-inputs-sha256:"
_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_ACCEPTANCE_LANES = frozenset({"cpu_light", "cpu_exclusive", "gpu_serial"})


def _first_line(text: str | None) -> str:
    if not text:
        return ""
    for ln in text.strip().splitlines():
        ln = ln.strip()
        if ln:
            return ln
    return ""


def _readme_first_line(pkg_dir: Path) -> str:
    rd = pkg_dir / "README.md"
    if not rd.exists():
        return ""
    for ln in rd.read_text(encoding="utf-8", errors="replace").splitlines():
        s = ln.strip().lstrip("#").strip()
        if s:
            return s
    return ""


def _module_facts(py: Path) -> dict:
    """AST-only extraction — module docstring first line + public top-level class/def names.
    Never imports the module (so no torch / CUDA / side effects)."""
    src = py.read_text(encoding="utf-8", errors="replace")
    loc = src.count("\n") + 1
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return {"loc": loc, "doc": f"[UNPARSEABLE: {exc.msg} @ line {exc.lineno}]",
                "classes": [], "funcs": []}
    doc = _first_line(ast.get_docstring(tree))
    if not doc:
        # Many modules here start with `from __future__ import annotations`, which makes the
        # following descriptive string NOT the official docstring (it is the 2nd statement). Fall
        # back to the first top-level bare string-constant expression so those modules still show.
        for node in tree.body:
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) \
                    and isinstance(node.value.value, str):
                doc = _first_line(node.value.value)
                break
    classes, funcs = [], []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            classes.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            funcs.append(node.name)
    return {"loc": loc, "doc": doc, "classes": classes, "funcs": funcs}


def _owning_root(py: Path) -> Path:
    """Which scan root (src/ or tools/) contains ``py``."""
    for r in _ROOTS:
        try:
            py.relative_to(r)
            return r
        except ValueError:
            continue
    return SRC


def _pkg_key(py: Path) -> str:
    """Package key for a module. src keys stay relative to src/ (UNCHANGED, e.g.
    'qec_twin/forward'); tools keys are prefixed by the root name ('tools', 'tools/harness') so the
    two roots never collide and existing src keys / code_status.json entries are untouched."""
    root = _owning_root(py)
    rel = py.parent.relative_to(root).as_posix()
    rel = "" if rel == "." else rel
    if root is SRC:
        return rel
    base = root.relative_to(REPO).as_posix()  # 'tools' or 'tests/harness'
    return base if not rel else f"{base}/{rel}"


def _mod_relpath(py: Path) -> str:
    """Per-module path key (for module-level status overrides + stale-status checks): src modules
    are relative to src/ ('qec_twin/forward/foo.py'); tools modules to the repo ('tools/harness/foo.py')."""
    root = _owning_root(py)
    return py.relative_to(SRC if root is SRC else REPO).as_posix()


def _pkg_dir(pkg: str) -> Path:
    """Directory for a package key (README lookup). Tools keys ('tools', 'tools/...') live under the
    repo root; src keys under src/."""
    if not pkg:
        return SRC
    repo_rooted = pkg in ("tools", "tests/harness") or pkg.startswith(("tools/", "tests/harness/"))
    return (REPO / pkg) if repo_rooted else (SRC / pkg)


def _iter_modules():
    """Yield (package_key, module_path) for every non-dunder .py under src/ AND dev tools/."""
    for root in _ROOTS:
        if not root.is_dir():
            continue
        for py in sorted(root.rglob("*.py")):
            if "__pycache__" in py.parts or py.name == "__init__.py":
                continue
            yield _pkg_key(py), py


def _iter_runtime_modules() -> list[Path]:
    """Every Python module shipped in the standalone simulator wheel.

    Unlike :func:`_iter_modules`, this includes ``__init__.py`` files because namespace facades are
    part of the installed API and must be deliberately classified by the service catalog.
    """

    if not RUNTIME_PACKAGE.is_dir():
        return []
    return sorted(
        py
        for py in RUNTIME_PACKAGE.rglob("*.py")
        if "__pycache__" not in py.parts and not py.is_symlink()
    )


def _packages() -> list[str]:
    pkgs = set()
    for pkg_rel, _ in _iter_modules():
        pkgs.add(pkg_rel)
    return sorted(pkgs)


def _code_map_inputs_hash() -> str:
    """Hash every input that can change the generated map or its distribution boundary."""

    h = hashlib.sha256()
    code_inputs = {py for _, py in _iter_modules()}
    code_inputs.update(_iter_runtime_modules())
    kernels = RUNTIME_PACKAGE / "carrier" / "kernels"
    if kernels.is_dir():
        code_inputs.update(kernels.glob("*.cpp"))
        code_inputs.update(kernels.glob("*.cu"))
    for py in sorted(code_inputs):
        rel = py.relative_to(REPO).as_posix()
        h.update(rel.encode())
        h.update(hashlib.sha256(py.read_bytes()).digest())
    for path in (STATUS_PATH, SERVICE_STATUS_PATH, PROJECT_PATH, MANIFEST_PATH):
        rel = path.relative_to(REPO).as_posix()
        h.update(rel.encode())
        if path.exists():
            h.update(hashlib.sha256(path.read_bytes()).digest())
        else:
            h.update(b"<missing>")
    legacy_link = SRC / "qec_twin"
    h.update(b"src/qec_twin-symlink-target")
    if legacy_link.is_symlink():
        h.update(legacy_link.readlink().as_posix().encode())
    elif legacy_link.exists():
        h.update(b"<not-a-symlink>")
    else:
        h.update(b"<missing>")
    return h.hexdigest()


def _git_head() -> str:
    try:
        out = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _reject_duplicate_json_keys(pairs: list[tuple[str, object]]) -> dict:
    """Fail closed instead of silently accepting the last duplicate JSON key."""

    out: dict[str, object] = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f"duplicate JSON key {key!r}")
        out[key] = value
    return out


def _load_json(path: Path, *, required: bool) -> dict:
    if not path.exists():
        if required:
            raise SystemExit(f"required catalog missing: {path.relative_to(REPO)}")
        return {}
    try:
        data = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_json_keys,
        )
    except (json.JSONDecodeError, ValueError) as exc:
        raise SystemExit(f"{path.relative_to(REPO)} is not valid unique-key JSON: {exc}")
    if not isinstance(data, dict):
        raise SystemExit(f"{path.relative_to(REPO)} root must be a JSON object")
    return data


def _load_status() -> dict:
    return _load_json(STATUS_PATH, required=False)


def _load_service_status() -> dict:
    return _load_json(SERVICE_STATUS_PATH, required=True)


def _committed_hash() -> str | None:
    if not MAP_PATH.exists():
        return None
    for ln in MAP_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
        if ln.startswith(_HASH_MARKER):
            return ln.split(":", 1)[1].strip().rstrip("->").strip()
    return None


def _render_local_index(local_index: dict) -> list[str]:
    """Curated LOCAL-ONLY (gitignored outputs/) working-code clusters. The globs are hand-maintained
    + stable; the FILES matching them are auto-discovered here, so new nm_*/cert_*/quantum_bath_*
    appear without editing the config. These files are NOT committed and NOT in the drift hash."""
    lines: list[str] = []
    if not local_index:
        return lines
    lines.append("## LOCAL-ONLY working code — gitignored `outputs/` (NOT committed; on the build "
                 "workstation only; re-run certs to confirm — they are not assumed)")
    lines.append("> Curated clusters (globs in `docs/code_status.json` `_local_index`); files "
                 "auto-discovered. This is where the P2 quantum-bath infrastructure lives — READ HERE "
                 "before assuming it is unbuilt.")
    lines.append("")
    for heading, globs in local_index.items():
        if heading.startswith("_"):
            continue
        matched: set[Path] = set()
        for g in globs:
            for p in REPO.glob(g):
                if p.suffix == ".py" and "__pycache__" not in p.parts:
                    matched.add(p)
        if not matched:
            lines.append(f"### {heading}")
            lines.append("- ⚠ (no files match the configured globs — patterns stale or code moved?)")
            lines.append("")
            continue
        lines.append(f"### {heading}")
        for p in sorted(matched):
            facts = _module_facts(p)
            rel = p.relative_to(REPO).as_posix()
            lines.append(f"- **`{rel}`** ({facts['loc']} LOC) — {facts['doc'] or '(no docstring)'}")
        lines.append("")
    return lines


def _normalise_dist_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _requirement_name(requirement: str) -> str:
    match = re.match(r"\s*([A-Za-z0-9_.-]+)", requirement)
    if match is None:
        return ""
    return _normalise_dist_name(match.group(1))


def _project_dependency_contract() -> tuple[set[str], set[str], list[str]]:
    try:
        project = tomllib.loads(PROJECT_PATH.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise SystemExit(f"pyproject.toml dependency contract is unreadable: {exc}")
    project_table = project.get("project", {})
    core = {
        _requirement_name(str(item))
        for item in project_table.get("dependencies", [])
    }
    extras_table = project_table.get("optional-dependencies", {})
    extras = {str(name) for name in extras_table}
    package_find = (
        project.get("tool", {})
        .get("setuptools", {})
        .get("packages", {})
        .get("find", {})
    )
    includes = [str(item) for item in package_find.get("include", [])]
    return core, extras, includes


def _module_source(module: str) -> tuple[Path, bool] | None:
    rel = Path(*module.split("."))
    module_file = (SRC / rel).with_suffix(".py")
    package_file = SRC / rel / "__init__.py"
    if module_file.is_file():
        return module_file, False
    if package_file.is_file():
        return package_file, True
    return None


def _relative_import_module(
    current_module: str,
    *,
    current_is_package: bool,
    level: int,
    imported: str | None,
) -> str | None:
    if level == 0:
        return imported
    base = current_module.split(".")
    if not current_is_package:
        base = base[:-1]
    ascend = level - 1
    if ascend > len(base):
        return None
    if ascend:
        base = base[:-ascend]
    if imported:
        base.extend(imported.split("."))
    return ".".join(base)


def _module_exports(
    module: str,
    *,
    seen: frozenset[str] = frozenset(),
) -> tuple[set[str], dict[str, set[str]]]:
    """Return statically bound names and direct class methods; never import project code."""

    if module in seen:
        return set(), {}
    source = _module_source(module)
    if source is None:
        return set(), {}
    path, is_package = source
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return set(), {}
    exports: set[str] = set()
    methods: dict[str, set[str]] = {}
    next_seen = seen | {module}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            exports.add(node.name)
        elif isinstance(node, ast.ClassDef):
            exports.add(node.name)
            methods[node.name] = {
                child.name
                for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    exports.add(target.id)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                exports.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            imported_module = _relative_import_module(
                module,
                current_is_package=is_package,
                level=node.level,
                imported=node.module,
            )
            for alias in node.names:
                if alias.name == "*" and imported_module:
                    star_exports, _ = _module_exports(imported_module, seen=next_seen)
                    exports.update(name for name in star_exports if not name.startswith("_"))
                elif alias.name != "*":
                    exports.add(alias.asname or alias.name)
    return exports, methods


def _entrypoint_error(entrypoint: str) -> str | None:
    if entrypoint.count(":") != 1:
        return "must use 'package.module:attribute' syntax"
    module, attribute = entrypoint.split(":", 1)
    if not module.startswith("error_coupling_simulator"):
        return "must be owned by the installed error_coupling_simulator package"
    source = _module_source(module)
    if source is None:
        return f"module {module!r} has no installed source file"
    parts = attribute.split(".")
    if not parts or any(not part.isidentifier() for part in parts):
        return f"attribute path {attribute!r} is invalid"
    exports, methods = _module_exports(module)
    if parts[0] not in exports:
        return f"{parts[0]!r} is not statically bound by {module!r}"
    if len(parts) == 2 and parts[1] not in methods.get(parts[0], set()):
        return f"method {attribute!r} is not directly defined in {module!r}"
    if len(parts) > 2:
        return "only module symbols and direct class methods are supported"
    return None


def _repo_path_error(value: str) -> str | None:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        return "must be a repository-relative path without '..'"
    if not (REPO / path).exists():
        return "does not exist"
    return None


def _legacy_qec_twin_edges(path: Path) -> list[str]:
    """Find executable legacy-module resolution edges without importing code.

    Plain string constants are deliberately ignored because historical ``qec_twin.*`` schema IDs
    are persisted compatibility vocabulary. Imports, dynamic imports, and string-based patch/
    monkeypatch targets resolve Python objects and therefore remain real legacy dependencies.
    """

    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError as exc:
        return [f"unparseable at line {exc.lineno}: {exc.msg}"]

    def is_legacy(value: object) -> bool:
        return isinstance(value, str) and (
            value == "qec_twin" or value.startswith("qec_twin.")
        )

    constant_bindings: dict[str, set[str]] = defaultdict(set)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value = node.value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                for target in targets:
                    if isinstance(target, ast.Name):
                        constant_bindings[target.id].add(value.value)

    def string_values(node: ast.AST) -> set[str]:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return {node.value}
        if isinstance(node, ast.Name):
            return constant_bindings.get(node.id, set())
        return set()

    edges: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if is_legacy(alias.name):
                    edges.append(f"line {node.lineno}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom) and is_legacy(node.module):
            edges.append(f"line {node.lineno}: from {node.module} import ...")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            else:
                func_name = ""
            if func_name in {
                "__import__",
                "find_spec",
                "import_module",
                "importorskip",
                "patch",
                "resolve_name",
                "setattr",
            }:
                arguments = list(node.args[:1]) + [keyword.value for keyword in node.keywords]
                for value in sorted({
                    candidate
                    for argument in arguments
                    for candidate in string_values(argument)
                    if is_legacy(candidate)
                }):
                    edges.append(f"line {node.lineno}: {func_name}({value!r}, ...)")
    return sorted(set(edges))


def _historical_path_error(value: str) -> str | None:
    """Validate historical/excluded paths without depending on ignored local outputs.

    ``outputs/`` is intentionally absent from a clean checkout, so catalog entries under that
    root are locators, not existence requirements. Tracked package/legacy/docs boundaries still
    have to exist when the map is generated.
    """

    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        return "must be a repository-relative path without '..'"
    if path.parts and path.parts[0] == "outputs":
        return None
    if not (REPO / path).exists():
        return "does not exist in the tracked checkout"
    return None


def _string_list_errors(
    obj: dict,
    field: str,
    *,
    owner: str,
    nonempty: bool = True,
) -> tuple[list[str], list[str]]:
    value = obj.get(field)
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        return [], [f"{owner}.{field} must be a list of non-empty strings"]
    if nonempty and not value:
        return [], [f"{owner}.{field} must not be empty"]
    if len(value) != len(set(value)):
        return value, [f"{owner}.{field} contains duplicate values"]
    return value, []


def _validate_service_status(catalog: dict) -> dict:
    """Validate the service catalog as a release-boundary contract."""

    errors: list[str] = []
    if catalog.get("_schema") != "error_coupling_simulator.service_status.v2":
        errors.append("_schema must equal 'error_coupling_simulator.service_status.v2'")
    service_definition = catalog.get("_service_definition")
    if not isinstance(service_definition, dict):
        errors.append("catalog._service_definition must be an object")
    else:
        for field in ("included", "excluded"):
            _, field_errors = _string_list_errors(
                service_definition,
                field,
                owner="catalog._service_definition",
            )
            errors.extend(field_errors)
    if not isinstance(catalog.get("api_surface"), str) or not catalog["api_surface"].strip():
        errors.append("catalog.api_surface must be a non-empty string")
    vocabulary, vocab_errors = _string_list_errors(
        catalog,
        "status_vocabulary",
        owner="catalog",
    )
    errors.extend(vocab_errors)
    kind_vocabulary, kind_vocab_errors = _string_list_errors(
        catalog,
        "service_kind_vocabulary",
        owner="catalog",
    )
    errors.extend(kind_vocab_errors)
    services = catalog.get("services")
    if not isinstance(services, list) or not services:
        errors.append("catalog.services must be a non-empty list")
        services = []
    core_dependencies, declared_extras, _ = _project_dependency_contract()
    service_ids: list[str] = []
    declared_control_refs: set[str] = set()
    service_modules: dict[str, set[str]] = defaultdict(set)
    acceptance_paths: set[str] = set()
    for index, service in enumerate(services):
        owner = f"services[{index}]"
        if not isinstance(service, dict):
            errors.append(f"{owner} must be an object")
            continue
        service_id = service.get("id")
        if not isinstance(service_id, str) or _ID_RE.fullmatch(service_id) is None:
            errors.append(f"{owner}.id must match {_ID_RE.pattern!r}")
            service_id = f"<invalid-{index}>"
        service_ids.append(service_id)
        for field in ("name", "layer"):
            if not isinstance(service.get(field), str) or not service[field].strip():
                errors.append(f"{owner}.{field} must be a non-empty string")
        if service.get("status") not in vocabulary:
            errors.append(f"{owner}.status {service.get('status')!r} is outside status_vocabulary")
        if service.get("kind") not in kind_vocabulary:
            errors.append(f"{owner}.kind {service.get('kind')!r} is outside service_kind_vocabulary")
        if not isinstance(service.get("canonical_record_output"), bool):
            errors.append(f"{owner}.canonical_record_output must be a boolean")
        for field in ("owners", "entrypoints", "external_inputs", "outputs", "acceptance"):
            values, field_errors = _string_list_errors(service, field, owner=owner)
            errors.extend(field_errors)
            if field in {"owners", "acceptance"}:
                for value in values:
                    path_error = _repo_path_error(value)
                    if path_error:
                        errors.append(f"{owner}.{field} path {value!r} {path_error}")
                    if field == "owners" and not value.startswith("src/error_coupling_simulator/"):
                        errors.append(f"{owner}.owners path {value!r} is outside the installed package")
                    if field == "owners" and (REPO / value).exists() and not (REPO / value).is_file():
                        errors.append(
                            f"{owner}.owners path {value!r} must be an exact file, not a directory"
                        )
                    if field == "owners" and value.endswith(".py"):
                        service_modules[value].add(service_id)
                    if field == "acceptance":
                        acceptance_paths.add(value)
            elif field == "entrypoints":
                for value in values:
                    ep_error = _entrypoint_error(value)
                    if ep_error:
                        errors.append(f"{owner}.entrypoint {value!r}: {ep_error}")
        if "legacy_sources" in service:
            legacy_sources, legacy_errors = _string_list_errors(
                service,
                "legacy_sources",
                owner=owner,
                nonempty=False,
            )
            errors.extend(legacy_errors)
            for legacy_path in legacy_sources:
                path_error = _historical_path_error(legacy_path)
                if path_error:
                    errors.append(f"{owner}.legacy_sources path {legacy_path!r} {path_error}")
        dependencies = service.get("dependencies")
        if not isinstance(dependencies, dict):
            errors.append(f"{owner}.dependencies must be an object")
        else:
            for key in ("core", "extras"):
                values, field_errors = _string_list_errors(
                    dependencies,
                    key,
                    owner=f"{owner}.dependencies",
                    nonempty=False,
                )
                errors.extend(field_errors)
                if key == "core":
                    for value in values:
                        if _normalise_dist_name(value) not in core_dependencies:
                            errors.append(
                                f"{owner}.dependencies.core {value!r} is not declared in project.dependencies"
                            )
                else:
                    for value in values:
                        if value not in declared_extras:
                            errors.append(
                                f"{owner}.dependencies.extras {value!r} is not a declared optional extra"
                            )
        controls = service.get("controls", [])
        if not isinstance(controls, list):
            errors.append(f"{owner}.controls must be a list when present")
            controls = []
        control_ids: list[str] = []
        for control_index, control in enumerate(controls):
            control_owner = f"{owner}.controls[{control_index}]"
            if not isinstance(control, dict):
                errors.append(f"{control_owner} must be an object")
                continue
            control_id = control.get("id")
            if not isinstance(control_id, str) or _ID_RE.fullmatch(control_id) is None:
                errors.append(f"{control_owner}.id must match {_ID_RE.pattern!r}")
            else:
                control_ids.append(control_id)
            for field in ("entrypoint", "semantics"):
                if not isinstance(control.get(field), str) or not control[field].strip():
                    errors.append(f"{control_owner}.{field} must be a non-empty string")
            if isinstance(control.get("entrypoint"), str):
                ep_error = _entrypoint_error(control["entrypoint"])
                if ep_error:
                    errors.append(f"{control_owner}.entrypoint: {ep_error}")
        if len(control_ids) != len(set(control_ids)):
            errors.append(f"{owner}.controls contains duplicate IDs")
        declared_control_refs.update(f"{service_id}:{control_id}" for control_id in control_ids)
    if len(service_ids) != len(set(service_ids)):
        errors.append("service IDs must be globally unique")
    service_id_set = set(service_ids)

    acceptance_execution = catalog.get("acceptance_execution")
    if not isinstance(acceptance_execution, dict):
        errors.append("catalog.acceptance_execution must be an object")
        acceptance_execution = {}
    if acceptance_execution.get("isolation") != "one_test_file_per_process":
        errors.append(
            "catalog.acceptance_execution.isolation must equal "
            "'one_test_file_per_process'"
        )
    for field in ("default_conda_environment", "runner", "reason"):
        if not isinstance(acceptance_execution.get(field), str) or not acceptance_execution[
            field
        ].strip():
            errors.append(f"catalog.acceptance_execution.{field} must be a non-empty string")
    runner = acceptance_execution.get("runner")
    if isinstance(runner, str):
        runner_error = _repo_path_error(runner)
        if runner_error:
            errors.append(f"catalog.acceptance_execution.runner {runner!r} {runner_error}")
    environment_overrides = acceptance_execution.get("environment_overrides")
    if not isinstance(environment_overrides, dict):
        errors.append("catalog.acceptance_execution.environment_overrides must be an object")
        environment_overrides = {}
    for path, environment in environment_overrides.items():
        if path not in acceptance_paths:
            errors.append(
                "catalog.acceptance_execution.environment_overrides references "
                f"non-acceptance path {path!r}"
            )
        if not isinstance(environment, str) or not environment.strip():
            errors.append(
                "catalog.acceptance_execution.environment_overrides values must be "
                "non-empty environment names"
            )
    if environment_overrides.get("tests/test_simulator_cudaq_grover.py") != "aiqec":
        errors.append(
            "CUDA-Q acceptance must remain isolated in the retained aiqec environment"
        )
    default_lane = acceptance_execution.get("default_lane")
    if not isinstance(default_lane, str) or default_lane not in _ACCEPTANCE_LANES:
        errors.append(
            "catalog.acceptance_execution.default_lane must be one of "
            f"{sorted(_ACCEPTANCE_LANES)!r}"
        )
    lane_overrides = acceptance_execution.get("lane_overrides")
    if not isinstance(lane_overrides, dict):
        errors.append("catalog.acceptance_execution.lane_overrides must be an object")
        lane_overrides = {}
    unknown_lanes = sorted(set(lane_overrides) - _ACCEPTANCE_LANES)
    if unknown_lanes:
        errors.append(
            "catalog.acceptance_execution.lane_overrides contains unknown lanes: "
            f"{unknown_lanes}"
        )
    overridden_paths: dict[str, str] = {}
    for lane, raw_paths in lane_overrides.items():
        if lane not in _ACCEPTANCE_LANES:
            continue
        paths, lane_errors = _string_list_errors(
            lane_overrides,
            lane,
            owner="catalog.acceptance_execution.lane_overrides",
            nonempty=False,
        )
        errors.extend(lane_errors)
        if not isinstance(raw_paths, list):
            continue
        for path in paths:
            if path not in acceptance_paths:
                errors.append(
                    "catalog.acceptance_execution.lane_overrides "
                    f"lane {lane!r} references non-acceptance path {path!r}"
                )
            prior_lane = overridden_paths.get(path)
            if prior_lane is not None:
                errors.append(
                    "catalog.acceptance_execution.lane_overrides assigns "
                    f"{path!r} to both {prior_lane!r} and {lane!r}"
                )
            else:
                overridden_paths[path] = lane
    acceptance_lane_by_path = {
        path: overridden_paths.get(path, default_lane)
        for path in acceptance_paths
    }
    acceptance_lane_counts = {
        lane: sum(assigned == lane for assigned in acceptance_lane_by_path.values())
        for lane in sorted(_ACCEPTANCE_LANES)
    }

    support_modules = catalog.get("support_modules")
    if not isinstance(support_modules, list) or not support_modules:
        errors.append("catalog.support_modules must be a non-empty list")
        support_modules = []
    support_assignments: dict[str, dict[str, object]] = {}
    for index, item in enumerate(support_modules):
        owner = f"support_modules[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{owner} must be an object")
            continue
        paths, path_errors = _string_list_errors(item, "paths", owner=owner)
        errors.extend(path_errors)
        used_by, used_by_errors = _string_list_errors(
            item,
            "used_by",
            owner=owner,
            nonempty=False,
        )
        errors.extend(used_by_errors)
        for service_id in used_by:
            if service_id not in service_id_set:
                errors.append(f"{owner}.used_by references unknown service {service_id!r}")
        for field in ("role", "reason"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                errors.append(f"{owner}.{field} must be a non-empty string")
        for value in paths:
            path_error = _repo_path_error(value)
            if path_error:
                errors.append(f"{owner}.paths path {value!r} {path_error}")
                continue
            if not value.startswith("src/error_coupling_simulator/") or not value.endswith(".py"):
                errors.append(
                    f"{owner}.paths path {value!r} must be an exact installed-package Python module"
                )
                continue
            if not (REPO / value).is_file():
                errors.append(f"{owner}.paths path {value!r} must be a file")
                continue
            if value in support_assignments:
                errors.append(f"support module {value!r} is classified more than once")
            support_assignments[value] = {
                "role": item.get("role", ""),
                "reason": item.get("reason", ""),
                "used_by": sorted(used_by),
            }

    overlap = sorted(set(service_modules).intersection(support_assignments))
    if overlap:
        errors.append(
            "package modules cannot be both service owners and support modules: "
            f"{overlap}"
        )
    runtime_modules = {
        path.relative_to(REPO).as_posix()
        for path in _iter_runtime_modules()
    }
    classified_modules = set(service_modules).union(support_assignments)
    missing_modules = sorted(runtime_modules - classified_modules)
    stale_modules = sorted(classified_modules - runtime_modules)
    if missing_modules:
        errors.append(f"installed Python modules absent from reverse service coverage: {missing_modules}")
    if stale_modules:
        errors.append(f"module coverage entries outside the installed Python package: {stale_modules}")

    for value in sorted(runtime_modules | acceptance_paths):
        path = REPO / value
        for edge in _legacy_qec_twin_edges(path):
            errors.append(
                f"current simulator surface {value!r} resolves through legacy qec_twin ({edge})"
            )

    support_assets = catalog.get("support_assets", [])
    if not isinstance(support_assets, list):
        errors.append("catalog.support_assets must be a list")
        support_assets = []
    seen_support_assets: set[str] = set()
    for index, item in enumerate(support_assets):
        owner = f"support_assets[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{owner} must be an object")
            continue
        paths, path_errors = _string_list_errors(item, "paths", owner=owner)
        errors.extend(path_errors)
        used_by, used_by_errors = _string_list_errors(
            item,
            "used_by",
            owner=owner,
            nonempty=False,
        )
        errors.extend(used_by_errors)
        for service_id in used_by:
            if service_id not in service_id_set:
                errors.append(f"{owner}.used_by references unknown service {service_id!r}")
        for field in ("role", "reason"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                errors.append(f"{owner}.{field} must be a non-empty string")
        for value in paths:
            path_error = _repo_path_error(value)
            if path_error:
                errors.append(f"{owner}.paths path {value!r} {path_error}")
            elif not value.startswith("src/error_coupling_simulator/"):
                errors.append(f"{owner}.paths path {value!r} is outside the installed package")
            elif value.endswith(".py"):
                errors.append(f"{owner}.paths path {value!r} belongs in support_modules")
            if value in seen_support_assets:
                errors.append(f"support asset {value!r} is classified more than once")
            seen_support_assets.add(value)

    excluded = catalog.get("excluded_surfaces")
    if not isinstance(excluded, list) or not excluded:
        errors.append("catalog.excluded_surfaces must be a non-empty list")
        excluded = []
    excluded_ids: list[str] = []
    for index, item in enumerate(excluded):
        owner = f"excluded_surfaces[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{owner} must be an object")
            continue
        item_id = item.get("id")
        if not isinstance(item_id, str) or _ID_RE.fullmatch(item_id) is None:
            errors.append(f"{owner}.id must match {_ID_RE.pattern!r}")
        else:
            excluded_ids.append(item_id)
        paths, path_errors = _string_list_errors(item, "paths", owner=owner)
        errors.extend(path_errors)
        for value in paths:
            path_error = _historical_path_error(value)
            if path_error:
                errors.append(f"{owner}.paths path {value!r} {path_error}")
        for field in ("disposition", "reason"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                errors.append(f"{owner}.{field} must be a non-empty string")
    if len(excluded_ids) != len(set(excluded_ids)):
        errors.append("excluded_surfaces IDs must be globally unique")
    if service_id_set.intersection(excluded_ids):
        errors.append("service IDs and excluded_surfaces IDs must not overlap")
    required_exclusions = {
        "bayes_floor_analysis",
        "legacy_thin_strip_mps",
        "legacy_symlink_boundary",
        "m0_m34_compatibility_catalog",
        "lru_dqlr_unimplemented",
    }
    missing_exclusions = sorted(required_exclusions - set(excluded_ids))
    if missing_exclusions:
        errors.append(f"required simulator exclusions/gaps missing: {missing_exclusions}")

    by_id = {
        service["id"]: service
        for service in services
        if isinstance(service, dict) and isinstance(service.get("id"), str)
    }
    source_service = by_id.get("classical_1f_nonmarkov_chain")
    if source_service is None or source_service.get("status") != "CORE":
        errors.append("classical_1f_nonmarkov_chain must exist as an independent CORE service")
    else:
        required_controls = {"matched_marginal_permutation", "source_off"}
        actual_controls = {
            control.get("id")
            for control in source_service.get("controls", [])
            if isinstance(control, dict)
        }
        missing_controls = sorted(required_controls - actual_controls)
        if missing_controls:
            errors.append(
                "classical_1f_nonmarkov_chain is missing required controls: "
                f"{missing_controls}"
            )

    flow = catalog.get("flow")
    flow_nodes: list[dict] = []
    flow_edges: list[dict] = []
    if not isinstance(flow, dict):
        errors.append("catalog.flow must be an object")
    else:
        if flow.get("direction") not in {"LR", "RL", "TB", "BT"}:
            errors.append("flow.direction must be one of LR, RL, TB, BT")
        if not isinstance(flow.get("nodes"), list) or not flow["nodes"]:
            errors.append("flow.nodes must be a non-empty list")
        else:
            flow_nodes = flow["nodes"]
        if not isinstance(flow.get("edges"), list) or not flow["edges"]:
            errors.append("flow.edges must be a non-empty list")
        else:
            flow_edges = flow["edges"]
    node_ids: list[str] = []
    referenced_services: set[str] = set()
    referenced_controls: set[str] = set()
    for index, node in enumerate(flow_nodes):
        owner = f"flow.nodes[{index}]"
        if not isinstance(node, dict):
            errors.append(f"{owner} must be an object")
            continue
        node_id = node.get("id")
        if not isinstance(node_id, str) or _ID_RE.fullmatch(node_id) is None:
            errors.append(f"{owner}.id must match {_ID_RE.pattern!r}")
        else:
            node_ids.append(node_id)
        for field in ("label", "group"):
            if not isinstance(node.get(field), str) or not node[field].strip():
                errors.append(f"{owner}.{field} must be a non-empty string")
        if "class" in node and node["class"] not in {
            "archived",
            "research",
            "plugin",
            "restricted",
            "support",
            "open",
        }:
            errors.append(f"{owner}.class {node.get('class')!r} is not a supported flow class")
        refs, ref_errors = _string_list_errors(
            node,
            "services",
            owner=owner,
            nonempty=False,
        )
        errors.extend(ref_errors)
        for service_id in refs:
            if service_id not in service_id_set:
                errors.append(f"{owner}.services references unknown service {service_id!r}")
            referenced_services.add(service_id)
        if "control_refs" in node:
            control_refs, control_ref_errors = _string_list_errors(
                node,
                "control_refs",
                owner=owner,
                nonempty=False,
            )
            errors.extend(control_ref_errors)
            for control_ref in control_refs:
                if control_ref not in declared_control_refs:
                    errors.append(f"{owner}.control_refs references unknown control {control_ref!r}")
                referenced_controls.add(control_ref)
    if len(node_ids) != len(set(node_ids)):
        errors.append("flow node IDs must be globally unique")
    node_id_set = set(node_ids)
    edge_keys: list[tuple[str, str, str]] = []
    connected_nodes: set[str] = set()
    for index, edge in enumerate(flow_edges):
        owner = f"flow.edges[{index}]"
        if not isinstance(edge, dict):
            errors.append(f"{owner} must be an object")
            continue
        start, end = edge.get("from"), edge.get("to")
        if start not in node_id_set:
            errors.append(f"{owner}.from references unknown node {start!r}")
        if end not in node_id_set:
            errors.append(f"{owner}.to references unknown node {end!r}")
        if isinstance(start, str):
            connected_nodes.add(start)
        if isinstance(end, str):
            connected_nodes.add(end)
        label = edge.get("label", "")
        if not isinstance(label, str):
            errors.append(f"{owner}.label must be a string when present")
            label = ""
        if isinstance(start, str) and isinstance(end, str):
            edge_keys.append((start, end, label))
    if len(edge_keys) != len(set(edge_keys)):
        errors.append("flow contains duplicate edges")
    orphan_nodes = sorted(node_id_set - connected_nodes)
    if orphan_nodes:
        errors.append(f"flow contains disconnected nodes: {orphan_nodes}")
    missing_flow_services = sorted(service_id_set - referenced_services)
    if missing_flow_services:
        errors.append(f"services absent from the complete flow: {missing_flow_services}")
    missing_flow_controls = sorted(declared_control_refs - referenced_controls)
    if missing_flow_controls:
        errors.append(f"service controls absent from the complete flow: {missing_flow_controls}")

    if errors:
        detail = "\n".join(f"  - {error}" for error in errors)
        raise SystemExit(f"docs/service_status.json validation failed:\n{detail}")
    module_assignments: dict[str, dict[str, object]] = {}
    for path in sorted(runtime_modules):
        if path in service_modules:
            module_assignments[path] = {
                "classification": "SERVICE",
                "services": sorted(service_modules[path]),
            }
        else:
            module_assignments[path] = {
                "classification": "SUPPORT",
                **support_assignments[path],
            }
    return {
        "services": len(services),
        "excluded": len(excluded),
        "flow_nodes": len(flow_nodes),
        "flow_edges": len(flow_edges),
        "runtime_modules": len(runtime_modules),
        "service_modules": len(service_modules),
        "support_modules": len(support_assignments),
        "acceptance_files": len(acceptance_paths),
        "acceptance_isolation": acceptance_execution.get("isolation", ""),
        "acceptance_default_lane": default_lane,
        "acceptance_lane_counts": acceptance_lane_counts,
        "module_assignments": module_assignments,
    }


def _markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def _code_lines(values: list[str]) -> str:
    return "<br>".join(f"`{_markdown_cell(value)}`" for value in values)


def _render_service_catalog(catalog: dict, validation: dict) -> list[str]:
    lines = [
        "## RUNTIME SERVICE MATRIX — validated distribution contract",
        "",
        "> Generated from `docs/service_status.json`. CORE means shipped in the default distribution; "
        "it does not erase the scientific claim boundary stated in the final column.",
        "",
        f"- ✅ catalog validation clean — {validation['services']} services, "
        f"{validation['excluded']} explicit exclusions, {validation['flow_nodes']} flow nodes, "
        f"{validation['flow_edges']} flow edges.",
        f"- ✅ reverse module coverage clean — all {validation['runtime_modules']} installed Python "
        f"modules are classified ({validation['service_modules']} service implementation modules + "
        f"{validation['support_modules']} explicit support modules).",
        f"- ✅ canonical ownership clean — installed modules and all "
        f"{validation['acceptance_files']} declared acceptance files have no executable "
        "`qec_twin` import, dynamic-import, or patch-target edge.",
        f"- ✅ native-backend lifetime isolation — {validation['acceptance_isolation']}; "
        f"runner `{catalog['acceptance_execution']['runner']}`, default environment "
        f"`{catalog['acceptance_execution']['default_conda_environment']}` with explicit "
        "per-file environment overrides.",
        f"- ✅ acceptance execution lanes — default `{validation['acceptance_default_lane']}`; "
        + ", ".join(
            f"`{lane}`={count}"
            for lane, count in validation["acceptance_lane_counts"].items()
        )
        + ". Every acceptance file resolves to exactly one validated lane.",
        "- Exact owner files, package entry points, dependency extras, control methods, unique IDs, "
        "reverse module coverage, and complete-flow references were checked without importing project code.",
        f"- API surface: {_markdown_cell(catalog['api_surface'])}",
        "- Included as a service when: "
        + "; ".join(_markdown_cell(item) for item in catalog["_service_definition"]["included"]),
        "- Kept out of the service count when: "
        + "; ".join(_markdown_cell(item) for item in catalog["_service_definition"]["excluded"]),
        "",
        "| Service | Status / kind / record | Installed owners | Public entry points and controls | Dependencies | "
        "Inputs → outputs | Claim / maturity boundary |",
        "|---|---|---|---|---|---|---|",
    ]
    for service in catalog["services"]:
        controls = service.get("controls", [])
        api_lines = list(service["entrypoints"])
        api_lines.extend(
            f"control:{control['id']} = {control['entrypoint']}"
            for control in controls
        )
        dependencies = service["dependencies"]
        dep_parts = [
            "core: " + (", ".join(dependencies["core"]) or "none"),
            "extras: " + (", ".join(dependencies["extras"]) or "none"),
        ]
        io = (
            "; ".join(service["external_inputs"])
            + " → "
            + "; ".join(service["outputs"])
        )
        boundary_parts = []
        if service.get("note"):
            boundary_parts.append(str(service["note"]))
        boundary_parts.append("acceptance: " + ", ".join(service["acceptance"]))
        lines.append(
            "| "
            + f"**`{service['id']}`**<br>{_markdown_cell(service['name'])} | "
            + f"**{service['status']}**<br>{_markdown_cell(service['kind'])}<br>"
            + ("canonical `{det, obs}`" if service["canonical_record_output"] else "no canonical record")
            + f"<br>{_markdown_cell(service['layer'])} | "
            + _code_lines(service["owners"])
            + " | "
            + _code_lines(api_lines)
            + " | "
            + _markdown_cell("; ".join(dep_parts))
            + " | "
            + _markdown_cell(io)
            + " | "
            + _markdown_cell(" ".join(boundary_parts))
            + " |"
        )
    lines.extend(
        [
            "",
            "### Explicit non-service support modules",
            "",
            "| Role | Exact installed modules | Used by | Reason |",
            "|---|---|---|---|",
        ]
    )
    for item in catalog["support_modules"]:
        lines.append(
            f"| **`{item['role']}`** | {_code_lines(item['paths'])} | "
            f"{_code_lines(item['used_by']) if item['used_by'] else 'package-wide'} | "
            f"{_markdown_cell(item['reason'])} |"
        )
    if catalog.get("support_assets"):
        lines.extend(
            [
                "",
                "### Native/package support assets",
                "",
                "| Role | Exact assets | Used by | Reason |",
                "|---|---|---|---|",
            ]
        )
        for item in catalog["support_assets"]:
            lines.append(
                f"| **`{item['role']}`** | {_code_lines(item['paths'])} | "
                f"{_code_lines(item['used_by']) if item['used_by'] else 'package-wide'} | "
                f"{_markdown_cell(item['reason'])} |"
            )
    lines.extend(
        [
            "",
            "### Explicitly excluded from the simulator service surface",
            "",
            "| ID | Disposition | Paths | Reason |",
            "|---|---|---|---|",
        ]
    )
    for item in catalog["excluded_surfaces"]:
        lines.append(
            f"| **`{item['id']}`** | `{item['disposition']}` | "
            f"{_code_lines(item['paths'])} | {_markdown_cell(item['reason'])} |"
        )
    lines.append("")
    return lines


def _mermaid_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', "&quot;").replace("\n", "<br/>")


def _render_service_flow(catalog: dict) -> list[str]:
    flow = catalog["flow"]
    groups: dict[str, list[dict]] = defaultdict(list)
    for node in flow["nodes"]:
        groups[node["group"]].append(node)
    lines = [
        "## COMPLETE SERVICE FLOW",
        "",
        "> This diagram is generated from the same validated catalog as the matrix. It distinguishes "
        "canonical record emission from reduced comparators, restricted evidence, research, archived "
        "findings, and the isolated CUDA-Q process. An arrow denotes an implemented data/dependency "
        "route unless its label explicitly says OPEN.",
        "",
        "```mermaid",
        f"flowchart {flow['direction']}",
    ]
    for group_index, (group, nodes) in enumerate(groups.items()):
        lines.append(f'  subgraph group_{group_index}["{_mermaid_text(group)}"]')
        for node in nodes:
            lines.append(f'    {node["id"]}["{_mermaid_text(node["label"])}"]')
        lines.append("  end")
    for edge in flow["edges"]:
        if edge.get("label"):
            lines.append(
                f'  {edge["from"]} -->|"{_mermaid_text(edge["label"])}"| {edge["to"]}'
            )
        else:
            lines.append(f'  {edge["from"]} --> {edge["to"]}')
    lines.extend(
        [
            "  classDef archived fill:#eeeeee,stroke:#777777,stroke-dasharray:5 5,color:#333333",
            "  classDef research fill:#fff4cc,stroke:#a37b00,color:#333333",
            "  classDef plugin fill:#e8ddff,stroke:#6941c6,color:#333333",
            "  classDef restricted fill:#e6f0ff,stroke:#3266a8,stroke-dasharray:3 3,color:#333333",
            "  classDef support fill:#f7f7f7,stroke:#999999,stroke-dasharray:2 2,color:#333333",
            "  classDef open fill:#ffe5e5,stroke:#b42318,stroke-dasharray:6 3,color:#333333",
        ]
    )
    by_class: dict[str, list[str]] = defaultdict(list)
    for node in flow["nodes"]:
        if node.get("class"):
            by_class[node["class"]].append(node["id"])
    for class_name, node_ids in by_class.items():
        lines.append(f"  class {','.join(node_ids)} {class_name}")
    lines.extend(["```", ""])
    return lines


def _render_legacy_symlink_boundary() -> list[str]:
    link = SRC / "qec_twin"
    _, _, includes = _project_dependency_contract()
    if link.is_symlink():
        target = link.readlink().as_posix()
        resolved = link.resolve().relative_to(REPO).as_posix()
        state = f"symbolic link → `{target}` (resolved: `{resolved}`)"
    elif link.exists():
        state = "⚠ exists but is not a symbolic link"
    else:
        state = "⚠ missing"
    scanned_qec_twin = any(
        _mod_relpath(py).startswith("qec_twin/")
        for _, py in _iter_modules()
    )
    return [
        "## LEGACY / DISTRIBUTION BOUNDARY",
        "",
        f"- `src/qec_twin`: {state}.",
        "- The AST inventory deliberately does not descend this directory symlink; "
        + ("⚠ qec_twin modules unexpectedly appeared in the scan." if scanned_qec_twin else "✅ no legacy qec_twin module entered the generated module inventory."),
        f"- Setuptools package allowlist: {_code_lines(includes)}. The wheel therefore ships only the "
        "installed `error_coupling_simulator` namespace; `qec_twin` remains an outward compatibility/RAG "
        "workspace boundary.",
        "- `docs/service_status.json` records Bayes-floor analysis, the old specialized thin-strip MPS, "
        "the M0–M34 compatibility adapter, the unimplemented LRU/DQLR bridge, and the symlinked legacy "
        "tree as explicit non-services or open gaps.",
        "",
    ]


def build_map() -> tuple[str, dict]:
    raw_status = _load_status()
    service_status = _load_service_status()
    service_validation = _validate_service_status(service_status)
    local_index = raw_status.get("_local_index", {})
    status = {k: v for k, v in raw_status.items() if not k.startswith("_")}
    pkgs = _packages()
    inputs_hash = _code_map_inputs_hash()
    head = _git_head()

    # drift detection: package coverage vs status keys.
    status_keys = set(status.keys())
    pkg_set = set(pkgs)
    missing_status = sorted(pkg_set - status_keys)                 # in code, no status entry
    # a status key is valid if it names an existing package, an existing module path, OR an ANCESTOR
    # namespace of some package (a dir whose only content is __init__ + subpackages, e.g. the
    # top-level `error_coupling_simulator`, has no direct module but is a real package).
    module_paths = {_mod_relpath(py) for _, py in _iter_modules()}
    stale_status = sorted(
        k for k in status_keys
        if k not in pkg_set and k not in module_paths
        and not any(p == k or p.startswith(k + "/") for p in pkg_set)
    )

    n_mod = n_cls = n_fn = 0
    lines: list[str] = []
    lines.append("# CODE_MAP — code + runtime-service inventory (GENERATED — do not hand-edit)")
    lines.append("")
    lines.append(f"{_HASH_MARKER} {inputs_hash} -->")
    lines.append(f"- **code-map inputs sha256:** `{inputs_hash}`  •  **git HEAD:** `{head}`")
    lines.append("- Generated by `tools/gen_code_map.py` from AST + validated service metadata (no "
                 "project imports). Regenerate after ANY listed `src/`, developer-tooling, status/catalog, "
                 "or packaging change: `python tools/gen_code_map.py`. Staleness: "
                 "`python tools/gen_code_map.py --check` exits 1 when the input hash above no longer "
                 "matches code, `docs/code_status.json`, `docs/service_status.json`, `pyproject.toml`, "
                 "`MANIFEST.in`, or the `src/qec_twin` symlink target.")
    lines.append("- **Status** (ACTIVE / PLACEHOLDER / ARCHIVED + one-line note) is the hand-maintained "
                 "module overlay `docs/code_status.json`. Runtime-service inclusion/exclusion, controls, "
                 "dependencies, acceptance paths, and flow live in `docs/service_status.json`.")
    lines.append("")

    lines.append("## DRIFT CHECK")
    if not missing_status and not stale_status:
        lines.append("- ✅ clean — every package has a status entry, no status entry is orphaned.")
    else:
        if missing_status:
            lines.append(f"- ⚠ **packages in code with NO status entry** (add to code_status.json): "
                         f"{', '.join('`'+m+'`' if m else '`<root>`' for m in missing_status)}")
        if stale_status:
            lines.append(f"- ⚠ **status entries pointing at NOTHING** (remove/rename in code_status.json): "
                         f"{', '.join('`'+m+'`' for m in stale_status)}")
    lines.append("")

    lines.extend(_render_service_catalog(service_status, service_validation))
    lines.extend(_render_service_flow(service_status))
    lines.extend(_render_legacy_symlink_boundary())

    # group modules by package.
    by_pkg: dict[str, list[Path]] = {}
    for pkg_rel, py in _iter_modules():
        by_pkg.setdefault(pkg_rel, []).append(py)

    for pkg in pkgs:
        label = pkg if pkg else "<root>"
        st = status.get(pkg, {})
        st_tag = st.get("status", "—")
        st_note = st.get("note", "")
        readme = _readme_first_line(_pkg_dir(pkg))
        lines.append(f"## `{label}/`  —  **[{st_tag}]**")
        if st_note:
            lines.append(f"> {st_note}")
        if readme:
            lines.append(f"> README: {readme}")
        lines.append("")
        for py in sorted(by_pkg[pkg]):
            facts = _module_facts(py)
            n_mod += 1
            n_cls += len(facts["classes"])
            n_fn += len(facts["funcs"])
            mod_status = status.get(_mod_relpath(py))
            tag = f" **[{mod_status['status']}]**" if mod_status else ""
            assignment = service_validation["module_assignments"].get(
                py.relative_to(REPO).as_posix()
            )
            assignment_text = ""
            if assignment and assignment["classification"] == "SERVICE":
                assignment_text = " — service: " + ", ".join(
                    f"`{service_id}`" for service_id in assignment["services"]
                )
            elif assignment:
                assignment_text = f" — support: `{assignment['role']}`"
            lines.append(
                f"- **`{py.name}`** ({facts['loc']} LOC){tag}{assignment_text} — "
                f"{facts['doc'] or '(no docstring)'}"
            )
            if facts["classes"]:
                lines.append(f"    - class: {', '.join('`'+c+'`' for c in facts['classes'])}")
            if facts["funcs"]:
                lines.append(f"    - def: {', '.join('`'+f+'`' for f in facts['funcs'])}")
        lines.append("")

    # tracked gate scripts (the record-level evidence suite).
    if GATES_DIR.exists():
        gate_py = sorted(GATES_DIR.glob("*.py"))
        if gate_py:
            lines.append("## tracked gates — `docs/twin_validation/gates/`")
            for g in gate_py:
                lines.append(f"- **`{g.name}`** ({_module_facts(g)['loc']} LOC) — "
                             f"{_module_facts(g)['doc'] or '(no docstring)'}")
            lines.append("")

    lines.extend(_render_local_index(local_index))

    lines.append("---")
    lines.append(f"_display inventory (excludes `__init__.py`): {len(pkgs)} packages, "
                 f"{n_mod} modules, {n_cls} public classes, {n_fn} public functions "
                 f"(committed `src/` + dev `tools/`) + curated local-only clusters above. "
                 f"The release-contract count above separately includes all "
                 f"{service_validation['runtime_modules']} installed package modules, including "
                 "namespace facades._")
    lines.append("")

    summary = {"packages": len(pkgs), "modules": n_mod, "classes": n_cls, "funcs": n_fn,
               "inputs_hash": inputs_hash, "head": head,
               "services": service_validation["services"],
               "runtime_modules": service_validation["runtime_modules"],
               "service_modules": service_validation["service_modules"],
               "support_modules": service_validation["support_modules"],
               "missing_status": missing_status, "stale_status": stale_status}
    return "\n".join(lines), summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if docs/CODE_MAP.md is stale vs the src tree (no rewrite)")
    args = ap.parse_args()

    assert SRC.is_dir(), f"source root not found at {SRC}"

    if args.check:
        service_status = _load_service_status()
        validation = _validate_service_status(service_status)
        current = _code_map_inputs_hash()
        committed = _committed_hash()
        if committed is None:
            print("CODE_MAP CHECK: FAIL — docs/CODE_MAP.md missing or has no hash marker", flush=True)
            return 1
        if committed != current:
            print(f"CODE_MAP CHECK: STALE — committed {committed[:12]}… != current {current[:12]}… "
                  f"(run: python tools/gen_code_map.py)", flush=True)
            return 1
        print(
            f"CODE_MAP CHECK: OK — up to date ({current[:12]}…); "
            f"service catalog valid ({validation['services']} services)",
            flush=True,
        )
        return 0

    text, summary = build_map()
    MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    MAP_PATH.write_text(text + "\n", encoding="utf-8")
    print(f"[gen_code_map] wrote {MAP_PATH.relative_to(REPO)}", flush=True)
    print(f"[gen_code_map] {summary['packages']} packages, {summary['modules']} modules, "
          f"{summary['classes']} classes, {summary['funcs']} funcs", flush=True)
    print(f"[gen_code_map] code-map inputs sha256 {summary['inputs_hash'][:16]}…  "
          f"git HEAD {summary['head']}",
          flush=True)
    print(f"[gen_code_map] service catalog: {summary['services']} validated services", flush=True)
    print(
        "[gen_code_map] reverse module coverage: "
        f"{summary['runtime_modules']} installed modules = "
        f"{summary['service_modules']} service + {summary['support_modules']} support",
        flush=True,
    )
    if summary["missing_status"]:
        print(f"[gen_code_map] ⚠ packages with NO status entry: {summary['missing_status']}", flush=True)
    if summary["stale_status"]:
        print(f"[gen_code_map] ⚠ orphaned status entries: {summary['stale_status']}", flush=True)
    if not summary["missing_status"] and not summary["stale_status"]:
        print("[gen_code_map] drift check: clean", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
