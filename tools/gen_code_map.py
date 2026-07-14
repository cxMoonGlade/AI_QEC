#!/usr/bin/env python
r"""Generate docs/CODE_MAP.md — the current, drift-proof inventory of src/qec_twin.

WHY THIS EXISTS
---------------
Hand-written codebase maps (build contracts, handoffs, memory files) drift from the code and
then MISLEAD (a stale "NOT YET EARNED" list said modules were absent when they were built). This
tool derives the map FROM THE CODE by ast-parsing every module (NO imports, NO CUDA, no project
logic) — so "what exists" cannot go stale. A tiny hand-maintained status overlay
(docs/code_status.json) adds the one thing code can't state mechanically (ACTIVE / PLACEHOLDER /
ARCHIVED + a one-line "what to know"), and this tool DRIFT-CHECKS that overlay against the code:
packages present in code but missing a status entry, and status entries whose target no longer
exists, are both flagged loudly so the overlay stays honest.

USE
---
    python tools/gen_code_map.py            # regenerate docs/CODE_MAP.md (run after ANY src change)
    python tools/gen_code_map.py --check    # exit 1 if the committed map is stale vs the src tree
                                            # (no rewrite) — for a pre-commit hook / CI

The map header stamps a src-tree content hash + git HEAD, so staleness is detectable. This is a
maintenance tool (ast + filesystem only); it is safe to run anywhere and needs no GPU / no aiqec env.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
# Walk ALL top-level packages under src/ (qec_twin AND error_coupling_simulator, ...), so the map
# covers the whole tree. Package keys are fully-qualified relative to src/ (e.g. "qec_twin/forward",
# "error_coupling_simulator/source"). This is what stops the map from missing a whole package.
SRC = REPO / "src"
TOOLS = REPO / "tools"          # dev tooling (not shipped): gen_code_map, sync_obsidian, ...
TESTS_HARNESS = REPO / "tests" / "harness"   # the test/coverage harness lives WITH the tests (proc/gpu_pool/gate/mutation)
_ROOTS = (SRC, TOOLS, TESTS_HARNESS)
STATUS_PATH = REPO / "docs" / "code_status.json"
MAP_PATH = REPO / "docs" / "CODE_MAP.md"
GATES_DIR = REPO / "docs" / "twin_validation" / "gates"

_HASH_MARKER = "<!-- src-tree-sha256:"


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


def _packages() -> list[str]:
    pkgs = set()
    for pkg_rel, _ in _iter_modules():
        pkgs.add(pkg_rel)
    return sorted(pkgs)


def _src_tree_hash() -> str:
    h = hashlib.sha256()
    for _, py in _iter_modules():
        rel = py.relative_to(REPO).as_posix()
        h.update(rel.encode())
        h.update(hashlib.sha256(py.read_bytes()).digest())
    return h.hexdigest()


def _git_head() -> str:
    try:
        out = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _load_status() -> dict:
    if not STATUS_PATH.exists():
        return {}
    try:
        return json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"docs/code_status.json is not valid JSON: {exc}")


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


def build_map() -> tuple[str, dict]:
    raw_status = _load_status()
    local_index = raw_status.get("_local_index", {})
    status = {k: v for k, v in raw_status.items() if not k.startswith("_")}
    pkgs = _packages()
    tree_hash = _src_tree_hash()
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
    lines.append("# CODE_MAP — `src/` + dev `tools/` inventory (GENERATED — do not hand-edit)")
    lines.append("")
    lines.append(f"{_HASH_MARKER} {tree_hash} -->")
    lines.append(f"- **src-tree sha256:** `{tree_hash}`  •  **git HEAD:** `{head}`")
    lines.append("- Generated by `tools/gen_code_map.py` from AST (no imports). Regenerate after ANY "
                 "listed `src/` or developer-tooling change: `python tools/gen_code_map.py`. Staleness: "
                 "`python tools/gen_code_map.py --check` exits 1 when the tree hash above no longer "
                 "matches the code.")
    lines.append("- **Status** (ACTIVE / PLACEHOLDER / ARCHIVED + one-line note) is the hand-maintained "
                 "overlay `docs/code_status.json`; everything else here is derived from the code.")
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
            lines.append(f"- **`{py.name}`** ({facts['loc']} LOC){tag} — {facts['doc'] or '(no docstring)'}")
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
    lines.append(f"_inventory: {len(pkgs)} packages, {n_mod} modules, {n_cls} public classes, "
                 f"{n_fn} public functions (committed `src/` + dev `tools/`) + curated local-only clusters above._")
    lines.append("")

    summary = {"packages": len(pkgs), "modules": n_mod, "classes": n_cls, "funcs": n_fn,
               "tree_hash": tree_hash, "head": head,
               "missing_status": missing_status, "stale_status": stale_status}
    return "\n".join(lines), summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if docs/CODE_MAP.md is stale vs the src tree (no rewrite)")
    args = ap.parse_args()

    assert SRC.is_dir(), f"src/qec_twin not found at {SRC}"

    if args.check:
        current = _src_tree_hash()
        committed = _committed_hash()
        if committed is None:
            print("CODE_MAP CHECK: FAIL — docs/CODE_MAP.md missing or has no hash marker", flush=True)
            return 1
        if committed != current:
            print(f"CODE_MAP CHECK: STALE — committed {committed[:12]}… != current {current[:12]}… "
                  f"(run: python tools/gen_code_map.py)", flush=True)
            return 1
        print(f"CODE_MAP CHECK: OK — up to date ({current[:12]}…)", flush=True)
        return 0

    text, summary = build_map()
    MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    MAP_PATH.write_text(text + "\n", encoding="utf-8")
    print(f"[gen_code_map] wrote {MAP_PATH.relative_to(REPO)}", flush=True)
    print(f"[gen_code_map] {summary['packages']} packages, {summary['modules']} modules, "
          f"{summary['classes']} classes, {summary['funcs']} funcs", flush=True)
    print(f"[gen_code_map] src-tree sha256 {summary['tree_hash'][:16]}…  git HEAD {summary['head']}",
          flush=True)
    if summary["missing_status"]:
        print(f"[gen_code_map] ⚠ packages with NO status entry: {summary['missing_status']}", flush=True)
    if summary["stale_status"]:
        print(f"[gen_code_map] ⚠ orphaned status entries: {summary['stale_status']}", flush=True)
    if not summary["missing_status"] and not summary["stale_status"]:
        print("[gen_code_map] drift check: clean", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
