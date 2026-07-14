"""Registry-driven per-unit COVERAGE GATE in Python (replaces stage_d_gate.sh).

Runs `coverage run --branch` over the registry's test files restricted to its reconcile_modules,
with DETERMINISTIC Hypothesis (-p no:cacheprovider --hypothesis-seed=0), emits a coverage json,
then invokes the AST-derived per-unit audit (imported as a Python module) -- 100% stmt+branch per
unit minus NAMED exemptions + the public-unit reconcile + out_of_scope anti-lie. GPU pool acquired
if the registry is requires_gpu. Everything through harness.proc (process groups, no orphans).

Usage:  python tests/harness/gate.py <registry.json>
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))          # tests/  (-> `from harness import ...`)
from harness import gpu_pool, proc  # noqa: E402

REPO = Path(__file__).resolve().parents[2]           # tests/harness/gate.py -> repo (portable)
LOGDIR = REPO / "outputs/twin_validation/logs"
ENVBIN = str(Path(sys.executable).parent)            # the running interpreter's bin (portable)
# the AST-derived per-unit audit now lives WITH the harness; import it as a sibling module.
from harness import coverage_audit as audit_mod  # noqa: E402


def run_gate(registry: str) -> bool:
    reg = json.loads(Path(registry).read_text(encoding="utf-8"))
    tag = Path(registry).stem
    modules = reg["reconcile_modules"]
    tests = reg["covered_by_test_files"]
    include = ",".join("*/" + m.split("src/", 1)[-1] for m in modules)
    LOGDIR.mkdir(parents=True, exist_ok=True)
    cov_data = LOGDIR / f".coverage.{tag}"
    cov_json = LOGDIR / f"{tag}_coverage.json"
    log = LOGDIR / f"{tag}_gate.log"

    env = dict(os.environ)
    env["PATH"] = ENVBIN + ":" + env.get("PATH", "")
    env["COVERAGE_FILE"] = str(cov_data)

    gpu = gpu_pool.acquire_gpu_slot() if reg.get("requires_gpu") else None
    try:
        if gpu is not None:
            env = gpu.child_env(env)
        r = proc.run(["python", "-m", "coverage", "run", "--branch", f"--include={include}",
                      "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider",
                      "--hypothesis-seed=0", *tests],
                     cwd=str(REPO), env=env, log_path=str(log))
        rj = proc.run(["python", "-m", "coverage", "json", "-o", str(cov_json),
                       f"--include={include}"], cwd=str(REPO), env=env, log_path=str(log),
                      append=True)
    finally:
        if gpu:
            gpu.release()

    if not (r.ok and rj.ok and cov_json.exists()):
        print(f"GATE {tag}: pytest_ok={r.ok} covjson_ok={rj.ok} -> FAIL (see {log})")
        return False
    # the audit prints per-unit lines + PASS/FAIL; returns 0 on pass.
    rc = audit_mod.audit(cov_json, registry_path=Path(registry).resolve(),
                         canonical=tuple(reg["canonical_units"]),
                         covered_by_files=tuple(reg.get("covered_by_test_files", [])),
                         reconcile_modules=tuple(reg.get("reconcile_modules", [])),
                         out_of_scope=reg.get("out_of_scope", {}))
    return rc == 0


def main(argv: list) -> int:
    assert argv, "usage: gate.py <registry.json>"
    ok = run_gate(argv[0])
    print(f"GATE: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
