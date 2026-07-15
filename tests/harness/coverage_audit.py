#!/usr/bin/env python
"""Registry-driven statement and branch coverage audit.

Each current owner registry supplies its canonical units, source modules, covering
tests, and explicit exemptions.  Source ranges are derived from the live AST so a
renamed, removed, or moved unit fails closed instead of inheriting stale line ranges.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
from pathlib import Path

#: repo root (tests/harness/coverage_audit.py -> harness -> tests -> root)
REPO_ROOT = Path(__file__).resolve().parents[2]

# Populated for each registry invocation so bare covered_by names resolve only
# against that registry's declared test files.
COVERED_BY_TEST_FILES: tuple[str, ...] = ()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _print_evidence(cov_json: Path, registry_path: Path, out) -> None:
    """Printed evidence FIRST (scripted-execution discipline): own script sha256 + the
    coverage-json sha256 + the registry sha256, so the log pins exactly what was audited
    with what."""
    me = Path(__file__).resolve()
    print(f"script={me}", file=out)
    print(f"script_sha256={_sha256(me)}", file=out)
    print(f"coverage_json={cov_json}", file=out)
    print(f"coverage_json_sha256={_sha256(cov_json)}", file=out)
    print(f"registry={registry_path}", file=out)
    print(f"registry_sha256={_sha256(registry_path)}", file=out)
    out.flush()


def _rel_to_repo(module: str) -> str:
    """The registry stores repo-relative module paths; coverage.py keys files by the path
    it was invoked with. Normalize both to a POSIX repo-relative string for matching."""
    return module.replace("\\", "/")


def _coverage_file_record(cov_doc: dict, module: str) -> dict:
    """The per-file coverage record for ``module`` (repo-relative). coverage.py may key
    files as repo-relative, absolute, or with a leading ``./``; match on the repo-relative
    SUFFIX so the audit is robust to the invocation cwd. Fail loud if absent (a unit whose
    module never appears means the unit-test files did not import it -- a real gap)."""
    want = _rel_to_repo(module)
    files = cov_doc.get("files", {})
    # exact repo-relative key first
    if want in files:
        return files[want]
    # else: unique suffix match
    hits = [k for k in files if _rel_to_repo(k).endswith(want)]
    assert hits, (
        f"PRECONDITION: module {want!r} has NO file record in the coverage json "
        f"(the registered unit-test files never imported/exercised it -- coverage keys: "
        f"{sorted(files)[:8]}{'...' if len(files) > 8 else ''})")
    assert len(hits) == 1, (
        f"PRECONDITION: module {want!r} matches MULTIPLE coverage keys {hits} -- "
        f"ambiguous; pin the registry module path to the exact coverage key")
    return files[hits[0]]


# ------------------------------------------------------------------------------------ #
# AST unit resolution -- the anti-stale core (findings 1/3/5)                           #
# ------------------------------------------------------------------------------------ #
def _module_ast(module: str):
    """Parse ``module`` (repo-relative) into an AST, cached per path within one run."""
    path = REPO_ROOT / module
    assert path.is_file(), f"PRECONDITION: source module not found on disk: {path}"
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _find_func_by_qualname(tree, qualname: str):
    """Return the ``FunctionDef``/``AsyncFunctionDef`` node whose dotted qualname (nested
    class/function path, no ``<locals>``) equals ``qualname``. Fail loud if absent (a
    renamed/deleted unit -- exactly the drift a stale line range would silently hide)."""
    found = []

    def walk(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                qn = f"{prefix}{child.name}"
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and qn == qualname:
                    found.append(child)
                walk(child, qn + ".")

    walk(tree, "")
    assert found, (
        f"PRECONDITION: qualname {qualname!r} not found in the source AST -- the unit was "
        f"renamed/deleted (a stale registry, or a real removal). Re-point the registry's "
        f"'qualname' at the current definition, or drop the unit if it is gone.")
    assert len(found) == 1, (
        f"PRECONDITION: qualname {qualname!r} is AMBIGUOUS ({len(found)} matches) -- "
        f"disambiguate the registry qualname")
    return found[0]


def _unit_line_set(fn) -> set:
    """The unit's OWN statement/branch line set: every line in ``fn.body`` in
    ``[fn.lineno, fn.end_lineno]`` MINUS the line ranges of any NESTED def
    (nested functions are separate units / out of this unit's scope). We take the FULL
    inclusive span and subtract nested-def spans; coverage.py's executed/missing sets are
    then intersected with this, so only lines coverage.py actually tracks are scored."""
    span = set(range(fn.lineno, fn.end_lineno + 1))
    for node in ast.walk(fn):
        if node is fn:
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            span -= set(range(node.lineno, node.end_lineno + 1))
    return span


def _raise_lines(fn) -> set:
    """Every ``raise`` statement line inside ``fn`` (used to re-validate line-exemptions
    and to locate torch-None / defensive raises)."""
    out = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Raise):
            out.add(node.lineno)
    return out


def _torch_none_raise_line(fn) -> "int | None":
    """The raise line inside a ``if torch is None:`` guard within ``fn``, or None.

    Recognizes ``if torch is None:`` (``Compare`` with a single ``Is`` op, left = Name
    'torch', comparator = ``None``) whose body contains a ``Raise``."""
    for node in ast.walk(fn):
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if (isinstance(test, ast.Compare)
                and isinstance(test.left, ast.Name) and test.left.id == "torch"
                and len(test.ops) == 1 and isinstance(test.ops[0], ast.Is)
                and len(test.comparators) == 1
                and isinstance(test.comparators[0], ast.Constant)
                and test.comparators[0].value is None):
            for stmt in ast.walk(node):
                if isinstance(stmt, ast.Raise):
                    return stmt.lineno
    return None


def _branch_decision_lines(fn) -> set:
    """Lines that are genuine branch DECISION points inside ``fn`` (if/for/while/
    boolop/ternary/comprehension) -- used to re-validate a ``stmt_kind='branch'``
    line-exemption points at a real decision, not a no-op."""
    out = set()
    for node in ast.walk(fn):
        if isinstance(node, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.IfExp,
                             ast.BoolOp)):
            out.add(node.lineno)
        if isinstance(node, (ast.comprehension,)):
            # comprehensions carry their line via the enclosing expr; approximate with
            # any 'if' guards inside the comprehension.
            for g in node.ifs:
                out.add(g.lineno)
    return out


# ------------------------------------------------------------------------------------ #
# Exemption resolution -- stable selectors, loud on drift (findings 1/2/3/6)            #
# ------------------------------------------------------------------------------------ #
def _resolve_exemption(ex: dict, module: str, tree, fn, line_set: set, errors: list) -> set:
    """Resolve ONE exemption to the set of source lines it removes from this unit's
    denominator. Appends a message to ``errors`` (and returns an empty set) on ANY
    integrity failure -- a broken exemption NEVER silently relaxes the gate.

    Integrity gates applied to EVERY exemption:
      * ``covered_by`` present + non-empty (finding 2);
      * every ``covered_by`` test EXISTS in the suite (finding 6);
      * the selector resolves to a REAL raise/branch inside the unit's CURRENT AST body
        (findings 1/3 -- a degraded selector fails loudly, never a no-op).
    """
    kind = ex.get("kind")
    selector = ex.get("selector", {})
    covered_by = ex.get("covered_by", [])
    reason = ex.get("reason", "")
    tag = f"exemption(kind={kind!r}, selector={selector!r})"

    # -- finding 2: covered_by must be present + non-empty --------------------------- #
    if not isinstance(covered_by, list) or not covered_by:
        errors.append(f"{tag}: MISSING/empty 'covered_by' (finding 2: an exemption must "
                      f"name the gate/test that covers the exempted line)")
        return set()
    if not reason:
        errors.append(f"{tag}: MISSING 'reason' (every exemption carries a reason)")
        return set()

    # -- finding 6: every covered_by test must exist in the suite --------------------- #
    for entry in covered_by:
        if not _covered_by_exists(entry):
            errors.append(f"{tag}: covered_by {entry!r} does NOT exist in the test suite "
                          f"(finding 6: dangling covered_by -- no such 'def <name>')")

    # -- selector -> exempt line set (findings 1/3: stable + re-validated) ------------ #
    if kind == "torch_missing" and selector.get("type") == "raise_in_torch_none_guard":
        ln = _torch_none_raise_line(fn)
        if ln is None:
            errors.append(f"{tag}: no `if torch is None:` guard with a raise found in the "
                          f"unit's AST body -- selector no longer resolves (finding 3)")
            return set()
        return {ln}

    if kind == "defensive_assert" and selector.get("type") == "raise_in_callee":
        callee = selector.get("callee")
        seam = _find_toplevel_func(tree, callee)
        if seam is None:
            errors.append(f"{tag}: defensive-assert callee {callee!r} not found in "
                          f"{module} -- the extracted _assert_* seam is missing (finding 3)")
            return set()
        seam_range = set(range(seam.lineno, seam.end_lineno + 1))
        # the seam MUST contain a raise (proves the guard has teeth structurally); AND the
        # unit MUST actually CALL it (else the exemption is about an unused function).
        if not _raise_lines(seam):
            errors.append(f"{tag}: callee {callee!r} contains no raise -- not a defensive "
                          f"assert (finding 3)")
            return set()
        if not _unit_calls(fn, callee):
            errors.append(f"{tag}: unit does not call {callee!r} -- exemption is about a "
                          f"function this unit never invokes")
            return set()
        # The seam is a SEPARATE function: its lines are OUT of the unit's AST body already
        # (so nothing to remove from THIS unit's denominator). Return the intersection with
        # the unit body for the general (inline, not-yet-extracted) case.
        return seam_range & line_set

    if kind == "line" and selector.get("type") == "line":
        # fallback: allowed ONLY if re-validated against the CURRENT AST (finding 3).
        ln = selector.get("line")
        stmt_kind = selector.get("stmt_kind")
        if not isinstance(ln, int):
            errors.append(f"{tag}: line-selector lacks an integer 'line'")
            return set()
        if ln not in line_set:
            errors.append(f"{tag}: exempt line {ln} is OUTSIDE the unit's current AST body "
                          f"(finding 1/3: a stale line-exemption -- re-derive it)")
            return set()
        if stmt_kind == "raise":
            if ln not in _raise_lines(fn):
                errors.append(f"{tag}: exempt line {ln} is NOT a raise statement in the "
                              f"current source (finding 3: exemption degraded to a no-op)")
                return set()
        elif stmt_kind == "branch":
            if ln not in _branch_decision_lines(fn):
                errors.append(f"{tag}: exempt line {ln} is NOT a branch decision point in "
                              f"the current source (finding 3: exemption degraded to a no-op)")
                return set()
        else:
            errors.append(f"{tag}: line-selector 'stmt_kind' must be 'raise' or 'branch' "
                          f"(got {stmt_kind!r})")
            return set()
        return {ln}

    errors.append(f"{tag}: unrecognized exemption kind/selector combination")
    return set()


def _find_toplevel_func(tree, name):
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


def _unit_calls(fn, callee: str) -> bool:
    """True if ``fn`` contains a call to ``callee`` (a bare Name call)."""
    for node in ast.walk(fn):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id == callee:
            return True
    return False


# ------------------------------------------------------------------------------------ #
# covered_by existence check (finding 6)                                                #
# ------------------------------------------------------------------------------------ #
_COVERED_BY_CACHE: dict = {}


def _test_defs_in_file(relpath: str) -> set:
    if relpath in _COVERED_BY_CACHE:
        return _COVERED_BY_CACHE[relpath]
    path = REPO_ROOT / relpath
    names: set = set()
    if path.is_file():
        for m in re.finditer(r"^\s*def\s+(\w+)\s*\(", path.read_text(encoding="utf-8"),
                             flags=re.MULTILINE):
            names.add(m.group(1))
    _COVERED_BY_CACHE[relpath] = names
    return names


def _covered_by_exists(entry: str) -> bool:
    """A ``covered_by`` entry exists iff ``def <test>`` appears in its named file
    (``path::test``) or in ANY registered test file (bare ``test``). The test name may
    carry a parametrization suffix (``test_x[case]``) -- strip at the first ``[``.

    LIMITATION (review finding 4, shared with the pilot gate): this checks the named test
    EXISTS, NOT that it actually exercises the exempted arc -- a covered_by repointed at an
    unrelated existing test still passes. For the load-bearing case (a gpu_bound/quimb_bound
    out_of_scope claim) the discriminating guard is instead the STRUCTURAL module-import check
    (``_module_imports``), which a false claim cannot satisfy. Full arc-attribution of a
    covered_by test (run it under coverage, confirm it hits the arc) is deferred to Stage E."""
    entry = str(entry).strip()
    if "::" in entry:
        relpath, _, tname = entry.partition("::")
        tname = tname.split("[", 1)[0].strip()
        return tname in _test_defs_in_file(relpath.strip())
    tname = entry.split("[", 1)[0].strip()
    return any(tname in _test_defs_in_file(f) for f in COVERED_BY_TEST_FILES)


# ------------------------------------------------------------------------------------ #
# per-unit scoring                                                                      #
# ------------------------------------------------------------------------------------ #
def _unit_scores(rec: dict, line_set: set, exempt: set) -> tuple:
    """Statement + branch coverage of one unit, scoped to the AST-derived ``line_set``
    with ``exempt`` lines removed. Returns
    ``(stmt_cov, stmt_hit, stmt_tot, br_cov, br_hit, br_tot, missing_stmt, missing_br)``.
    A denominator of 0 (no statements / no branch arcs after exemptions) scores as 1.0
    (nothing to miss), matching coverage.py's empty-file convention.
    """
    scored = line_set - exempt

    executed = set(int(x) for x in rec.get("executed_lines", []))
    missing = set(int(x) for x in rec.get("missing_lines", []))

    stmt_exec = {ln for ln in executed if ln in scored}
    stmt_miss = {ln for ln in missing if ln in scored}
    stmt_tot = len(stmt_exec) + len(stmt_miss)
    stmt_hit = len(stmt_exec)
    stmt_cov = 1.0 if stmt_tot == 0 else stmt_hit / stmt_tot

    def arc_in_scope(arc) -> bool:
        return int(arc[0]) in scored

    br_exec = [tuple(a) for a in rec.get("executed_branches", []) if arc_in_scope(a)]
    br_miss = [tuple(a) for a in rec.get("missing_branches", []) if arc_in_scope(a)]
    br_tot = len(br_exec) + len(br_miss)
    br_hit = len(br_exec)
    br_cov = 1.0 if br_tot == 0 else br_hit / br_tot

    return (stmt_cov, stmt_hit, stmt_tot, br_cov, br_hit, br_tot,
            sorted(stmt_miss), sorted(br_miss))


def _public_units_in_module(module: str) -> set:
    """Every PUBLIC unit qualname in ``module``'s AST -- the AST-derived anti-under-population
    surface (SS12.4 reconcile). A public unit = a top-level ``def`` with a public name (not
    starting with ``_``) PLUS every public method of a top-level ``class`` (``_private``
    methods skipped, but the load-bearing ``__post_init__`` dunder is kept). Nested/local
    functions are NOT units. Matches the inventory's 'unit definition'."""
    tree = _module_ast(module)
    out: set = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                out.add(node.name)
        elif isinstance(node, ast.ClassDef):
            for m in node.body:
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if (not m.name.startswith("_")) or m.name == "__post_init__":
                        out.add(f"{node.name}.{m.name}")
    return out


#: allowed out_of_scope classes (SS12.4). gpu_bound/quimb_bound carry a STRUCTURAL
#: anti-lie: the parked unit's module MUST actually import the lib -- a real CPU-pure unit
#: (numpy/math only) CANNOT be parked as gpu_bound to dodge scoring (review finding 1).
ALLOWED_OOS_CLASSES = ("gpu_bound", "quimb_bound", "retracted", "deferred")
LIB_FOR_OOS_CLASS = {"gpu_bound": ("torch",), "quimb_bound": ("quimb",)}


def _module_imports(module: str, libs) -> bool:
    """True if ``module``'s source imports any top-level package in ``libs`` (``import x`` or
    ``from x import ...``). Used to structurally refute a false gpu_bound/quimb_bound claim."""
    tree = _module_ast(module)
    libset = set(libs)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] in libset:
                    return True
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] in libset:
                return True
    return False


def _load_registry(registry_path: Path) -> dict:
    assert registry_path.is_file(), (
        f"PRECONDITION: registered coverage-target registry missing: {registry_path} "
        f"(author it per the contract SS7.2 in a reviewed commit)")
    doc = json.loads(registry_path.read_text(encoding="utf-8"))
    assert isinstance(doc.get("units"), list) and doc["units"], (
        f"PRECONDITION: {registry_path} lacks a non-empty 'units' list")
    return doc


def audit(cov_json: Path, *, registry_path: Path,
          canonical=(), covered_by_files=(),
          reconcile_modules=(), out_of_scope=None) -> int:
    """Audit ``cov_json`` against the registry. Exit 1 on any under-target unit, any
    missing canonical unit, any stray enumerated unit, any UNRECONCILED public unit, any
    broken exemption, or a malformed input.

    The caller threads ``canonical`` / ``covered_by_files`` / ``reconcile_modules`` /
    ``out_of_scope`` from the selected current-owner registry."""
    # helpers read the covered-by test-file set from this module global; set it for the
    # active registry so a bare covered_by name resolves against the right file set.
    global COVERED_BY_TEST_FILES
    COVERED_BY_TEST_FILES = tuple(covered_by_files)
    out_of_scope = dict(out_of_scope or {})

    doc = _load_registry(registry_path)
    default_target = doc.get("default_target", {"statement": 1.0, "branch": 1.0})

    units = doc["units"]
    enumerated = [str(u["unit"]) for u in units]
    # duplicate enumeration would silently collapse a target -- fail loud.
    assert len(enumerated) == len(set(enumerated)), (
        "PRECONDITION: duplicate 'unit' names in the registry")

    registered_set = set(enumerated)
    canonical_set = set(canonical)

    # ---- AM-3: registry MUST enumerate exactly the canonical set ----
    missing_from_registry = sorted(canonical_set - registered_set)
    stray_in_registry = sorted(registered_set - canonical_set)
    hard_error = False
    for name in missing_from_registry:
        print(f"MISSING-CANONICAL-UNIT (HARD ERROR, AM-3): {name!r} is an in-scope unit "
              f"but is NOT enumerated in the registry -- under-population is forbidden")
        hard_error = True
    for name in stray_in_registry:
        print(f"STRAY-REGISTERED-UNIT (HARD ERROR, AM-3): {name!r} is enumerated in the "
              f"registry but is NOT in the canonical set -- a renamed/typo unit")
        hard_error = True
    print(f"n_units_canonical={len(canonical_set)}")
    print(f"n_units_registered={len(enumerated)}")

    # ---- SS12.4 AST reconcile: every PUBLIC unit of each reconcile module MUST be either
    #      registered or explicitly out_of_scope (the AST-derived anti-under-population
    #      guard -- stronger than the pilot's hard-coded list; it cannot drift). ----
    registered_qn = {str(u.get("qualname")) for u in units if u.get("qualname")}
    all_pubs: set = set()
    pub_to_module: dict = {}
    for module in reconcile_modules:
        pubs = _public_units_in_module(module)
        all_pubs |= pubs
        for qn in pubs:
            pub_to_module[qn] = module
        for qn in sorted(pubs):
            if qn not in registered_qn and qn not in out_of_scope:
                print(f"UNRECONCILED-PUBLIC-UNIT (HARD ERROR, SS12.4): {module}:{qn} is a "
                      f"public unit but is neither registered nor listed in out_of_scope -- "
                      f"under-population forbidden")
                hard_error = True
        print(f"reconcile {module}: public_units={len(pubs)}")
    # out_of_scope integrity (review finding 1): parking a unit in out_of_scope is the
    # realistic under-population evasion, so EVERY entry is validated. A stale key (names no
    # public unit) is a hard error; a malformed/under-justified entry is a hard error; and a
    # gpu_bound/quimb_bound CLAIM is structurally refuted if the unit's module does not even
    # import the lib (a pure numpy/math unit CANNOT be gpu_bound).
    if reconcile_modules:
        for qn in sorted(out_of_scope):
            spec = out_of_scope[qn]
            if qn not in all_pubs:
                print(f"STALE-OUT-OF-SCOPE (HARD ERROR, SS12.4): {qn!r} is listed in "
                      f"out_of_scope but is not a public unit of any reconcile module")
                hard_error = True
                continue
            if not isinstance(spec, dict):
                print(f"OUT-OF-SCOPE-MALFORMED (HARD ERROR, SS12.4): {qn!r} -> {spec!r} is "
                      f"not a {{class, reason, covered_by}} object")
                hard_error = True
                continue
            cls = spec.get("class")
            reason = spec.get("reason")
            cov = spec.get("covered_by", [])
            if cls not in ALLOWED_OOS_CLASSES:
                print(f"OUT-OF-SCOPE-BAD-CLASS (HARD ERROR, SS12.4): {qn!r} class {cls!r} "
                      f"not in {ALLOWED_OOS_CLASSES}")
                hard_error = True
            if not reason:
                print(f"OUT-OF-SCOPE-NO-REASON (HARD ERROR, SS12.4): {qn!r} has no reason")
                hard_error = True
            if not isinstance(cov, list) or not cov:
                print(f"OUT-OF-SCOPE-NO-COVER (HARD ERROR, SS12.4): {qn!r} names no "
                      f"covered_by test (a parked unit must still name the gate/diagnostic "
                      f"that exercises it)")
                hard_error = True
            else:
                for entry in cov:
                    if not _covered_by_exists(entry):
                        print(f"OUT-OF-SCOPE-DANGLING-COVER (HARD ERROR, SS12.4): {qn!r} "
                              f"covered_by {entry!r} does not exist")
                        hard_error = True
            if cls in LIB_FOR_OOS_CLASS:
                mod = pub_to_module.get(qn)
                libs = LIB_FOR_OOS_CLASS[cls]
                if mod and not _module_imports(mod, libs):
                    print(f"FALSE-OUT-OF-SCOPE-CLASS (HARD ERROR, SS12.4): {qn!r} is declared "
                          f"{cls!r} but its module {mod} imports NONE of {libs} -- a "
                          f"CPU-pure unit cannot be parked as {cls} to dodge scoring")
                    hard_error = True

    cov_doc = json.loads(cov_json.read_text(encoding="utf-8"))

    exemption_errors: list = []
    under_target = []
    for u in units:
        name = str(u["unit"])
        module = str(u["module"])

        # ---- value-pin units (no source body to score: registered constants) -------- #
        if u.get("kind") == "value_pin" or u.get("qualname") in (None, ""):
            covered_by = u.get("covered_by", [])
            if not isinstance(covered_by, list) or not covered_by:
                print(f"VALUE-PIN-NO-COVER (HARD ERROR): {name!r} is a value-pin unit but "
                      f"names no covered_by test")
                hard_error = True
            else:
                for entry in covered_by:
                    if not _covered_by_exists(entry):
                        print(f"VALUE-PIN-DANGLING-COVER (HARD ERROR): {name!r} covered_by "
                              f"{entry!r} does not exist (finding 6)")
                        hard_error = True
            print(f"UNIT {name}: value_pin (no source body scored) covered_by="
                  f"{covered_by}")
            continue

        qualname = str(u["qualname"])
        tree = _module_ast(module)
        fn = _find_func_by_qualname(tree, qualname)
        line_set = _unit_line_set(fn)

        # ---- resolve exemptions (stable selectors; loud on drift) ------------------- #
        exempt: set = set()
        for ex in u.get("exemptions", []):
            exempt |= _resolve_exemption(ex, module, tree, fn, line_set,
                                         exemption_errors)

        tgt = u.get("target", default_target)
        t_stmt = float(tgt.get("statement", default_target["statement"]))
        t_br = float(tgt.get("branch", default_target["branch"]))

        # review finding 5: a per-unit target BELOW the default silently relaxes the gate.
        # Allowed ONLY with an explicit target_waiver (reason + covered_by that exists).
        d_stmt = float(default_target.get("statement", 1.0))
        d_br = float(default_target.get("branch", 1.0))
        if t_stmt + 1e-12 < d_stmt or t_br + 1e-12 < d_br:
            waiver = u.get("target_waiver")
            wcov = (waiver or {}).get("covered_by") if isinstance(waiver, dict) else None
            if not (isinstance(waiver, dict) and waiver.get("reason")
                    and isinstance(wcov, list) and wcov
                    and all(_covered_by_exists(e) for e in wcov)):
                print(f"TARGET-BELOW-DEFAULT (HARD ERROR): {name}: target "
                      f"stmt={t_stmt:.4f},branch={t_br:.4f} is below the default "
                      f"stmt={d_stmt:.4f},branch={d_br:.4f} without a valid target_waiver "
                      f"(reason + existing covered_by)")
                hard_error = True

        rec = _coverage_file_record(cov_doc, module)
        (stmt_cov, s_hit, s_tot, br_cov, b_hit, b_tot,
         miss_stmt, miss_br) = _unit_scores(rec, line_set, exempt)

        lo, hi = min(line_set), max(line_set)
        ex = f" (exempt {sorted(exempt)})" if exempt else ""
        print(f"UNIT {name} [{qualname}]: stmt={stmt_cov:.4f} ({s_hit}/{s_tot}) "
              f"branch={br_cov:.4f} ({b_hit}/{b_tot}) "
              f"target=stmt>={t_stmt:.4f},branch>={t_br:.4f} ast_lines=[{lo},{hi}]{ex}")

        # tiny float slack so 1.0 targets are exact-integer comparisons, not fp noise.
        fails = []
        if stmt_cov + 1e-9 < t_stmt:
            fails.append(f"stmt {stmt_cov:.4f} < {t_stmt:.4f} (missing {miss_stmt})")
        if br_cov + 1e-9 < t_br:
            fails.append(f"branch {br_cov:.4f} < {t_br:.4f} (missing arcs {miss_br})")
        if fails:
            under_target.append((name, fails))
            for f in fails:
                print(f"UNIT-UNDER-TARGET (VIOLATION): {name}: {f}")

    for msg in exemption_errors:
        print(f"EXEMPTION-INTEGRITY (HARD ERROR): {msg}")
    if exemption_errors:
        hard_error = True

    ok = (not hard_error) and (not under_target)
    print(f"COVERAGE-AUDIT: {'PASS' if ok else 'FAIL'} "
          f"(units={len(enumerated)}, under_target={len(under_target)}, "
          f"missing_canonical={len(missing_from_registry)}, "
          f"stray_registered={len(stray_in_registry)}, "
          f"exemption_errors={len(exemption_errors)})")
    sys.stdout.flush()
    return 0 if ok else 1


def main(argv: list) -> int:
    args = list(argv)
    assert len(args) == 3 and args[0] == "--registry", (
        "usage: coverage_audit.py --registry <registry-json> <coverage-json>\n"
        + (__doc__ or "")
    )
    registry_path = Path(args[1]).resolve()
    assert registry_path.is_file(), (
        f"PRECONDITION: registry not found: {registry_path}")
    rdoc = json.loads(registry_path.read_text(encoding="utf-8"))
    canonical = tuple(rdoc.get("canonical_units", ()))
    assert canonical, (
        f"PRECONDITION: registry {registry_path} lacks a non-empty "
        "'canonical_units' set"
    )
    covered_by_files = tuple(rdoc.get("covered_by_test_files", ()))
    reconcile_modules = tuple(rdoc.get("reconcile_modules", ()))
    out_of_scope = dict(rdoc.get("out_of_scope", {}))
    cov_json = Path(args[2]).resolve()
    assert cov_json.is_file(), f"PRECONDITION: coverage json not found: {cov_json}"
    _print_evidence(cov_json, registry_path, out=sys.stdout)
    return audit(cov_json, registry_path=registry_path, canonical=canonical,
                 covered_by_files=covered_by_files, reconcile_modules=reconcile_modules,
                 out_of_scope=out_of_scope)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
