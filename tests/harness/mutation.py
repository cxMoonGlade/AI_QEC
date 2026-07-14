"""Registry-driven L2 MUTATION runner in Python (replaces stage_d_mutation.sh).

Runs mutmut via harness.proc so mutmut AND its worker pool live in one process group -> killed
ATOMICALLY (no orphaned workers -- the exact failure the .sh runner had) with a real timeout.
mutmut 3.6 config lives in setup.cfg (no run-CLI), so: back up setup.cfg -> write a per-batch
[mutmut] (newline-joined lists; comma breaks mutmut's parser) -> run -> ALWAYS restore (finally).
Serialized by an flock on the shared setup.cfg. GPU pool acquired if the registry is requires_gpu.
STAGE_D_SKIP_SLOW=1 exported so slow physics pins are skipped under mutation. Gate: kill_rate>=BAR.
Mutants reported by mutmut as ``no tests`` (worker exit 33) are non-killed and are reported
separately; they must never inflate the kill rate.

Usage:  python tests/harness/mutation.py <registry.json>  [--jobs N] [--timeout SEC]
"""
from __future__ import annotations

import fcntl
import json
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # tests/ on path (-> `from harness import ...`)
from harness import gpu_pool, proc  # noqa: E402

REPO = Path(__file__).resolve().parents[2]          # portable (works on spark too), not hardcoded
LOGDIR = REPO / "outputs/twin_validation/logs"
ENVBIN = str(Path(sys.executable).parent)           # the running interpreter's bin (portable: aiqec OR spark venv)
CONFIG_PATH = REPO / "tests" / "harness_config.json"
_NON_KILLED_RESULT = re.compile(
    r"^\s*(?P<mutant>.+?):\s*(?P<status>survived|timeout|suspicious|no tests)\s*$"
)


def _knob(reg: dict, section: str, key: str, envname: str, default, cast):
    """Resolve a harness knob. Precedence: env > registry 'harness' block > tests/harness_config.json
    default. Keeps the important tunables (timeout, bar, jobs) in ONE visible config, not buried."""
    if envname and os.environ.get(envname) not in (None, ""):
        return cast(os.environ[envname])
    rh = (reg.get("harness") or {}).get(section, {})
    if key in rh:
        return cast(rh[key])
    try:
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8")).get(section, {})
        if key in cfg and not str(key).startswith("_"):
            return cast(cfg[key])
    except Exception:
        pass
    return default


def _env() -> dict:
    e = dict(os.environ)
    e["PATH"] = ENVBIN + ":" + e.get("PATH", "")
    e["STAGE_D_SKIP_SLOW"] = "1"
    return e


def _result_counts(total: int, results_text: str) -> dict:
    """Parse mutmut's non-killed result rows without crediting ``no tests`` as killed."""
    survivors: list[str] = []
    no_test_mutants: list[str] = []
    for line in results_text.splitlines():
        match = _NON_KILLED_RESULT.match(line)
        if match is None:
            continue
        mutant = match.group("mutant").strip()
        if match.group("status") == "no tests":
            no_test_mutants.append(mutant)
        else:
            survivors.append(mutant)

    non_killed = len(survivors) + len(no_test_mutants)
    if non_killed > total:
        raise ValueError(
            f"mutmut reported {non_killed} non-killed mutants for total={total}"
        )
    return {
        "killed": total - non_killed,
        "survived": len(survivors),
        "no_tests": len(no_test_mutants),
        "survivors": survivors,
        "no_test_mutants": no_test_mutants,
    }


def _score_results(total: int, results_text: str, bar: float) -> dict:
    """Return compatible mutation fields plus an honest rate/pass decision."""
    counts = _result_counts(total, results_text)
    rate = counts["killed"] / total if total else 0.0
    return {
        **counts,
        "kill_rate": round(rate, 4),
        "pass": rate >= bar,
    }


def run_mutation(registry: str, *, jobs: int | None = None,
                 timeout: float | None = None) -> dict:
    reg = json.loads(Path(registry).read_text(encoding="utf-8"))
    tag = Path(registry).stem
    modules = reg["reconcile_modules"]
    tests = reg["covered_by_test_files"]
    bar = _knob(reg, "mutation_gate", "kill_rate_bar", "ECS_MUT_BAR", 0.90, float)
    tmult = _knob(reg, "mutation_gate", "timeout_multiplier", "ECS_MUT_TIMEOUT_MULT", 15.0, float)
    tconst = _knob(reg, "mutation_gate", "timeout_constant", "ECS_MUT_TIMEOUT_CONST", 1.0, float)
    LOGDIR.mkdir(parents=True, exist_ok=True)
    log = LOGDIR / f"{tag}_mutation.log"
    res = LOGDIR / f"{tag}_mutation_results.txt"
    surv_json = LOGDIR / f"{tag}_mutation_survivors.json"
    setup = REPO / "setup.cfg"
    bak = LOGDIR / f".setup.cfg.bak.{tag}"

    # serialize: mutmut config lives in the SHARED setup.cfg -> flock queues concurrent callers.
    lock_fd = os.open(str(LOGDIR / ".ecs_mutation.lock"), os.O_CREAT | os.O_WRONLY, 0o644)
    fcntl.flock(lock_fd, fcntl.LOCK_EX)
    had_cfg = setup.exists()
    if had_cfg:
        shutil.copy(setup, bak)
    gpu = gpu_pool.acquire_gpu_slot() if reg.get("requires_gpu") else None
    try:
        setup.write_text(
            "[mutmut]\n"
            "source_paths=" + "\n\t".join(modules) + "\n"
            "pytest_add_cli_args_test_selection=" + "\n\t".join(tests) + "\n"
            "also_copy=src\n"
            f"timeout_multiplier={tmult}\n"
            f"timeout_constant={tconst}\n", encoding="utf-8")
        shutil.rmtree(REPO / "mutants", ignore_errors=True)
        n = jobs or int(os.environ.get("MUTMUT_JOBS", os.cpu_count() or 4))
        env = _env()
        if gpu is not None:
            env = gpu.child_env(env)
        with open(log, "w", encoding="utf-8") as f:
            f.write(f"tag={tag}\nsource_paths={modules}\ntest_selection={tests}\n"
                    f"max_children={n}\n")
        proc.run(["mutmut", "run", "--max-children", str(n)], cwd=str(REPO), env=env,
                 timeout=timeout, log_path=str(log), append=True)
        proc.run(["mutmut", "results"], cwd=str(REPO), env=env, log_path=str(res))
    finally:
        if had_cfg:
            shutil.copy(bak, setup)
            bak.unlink(missing_ok=True)
        else:
            setup.unlink(missing_ok=True)
        if gpu:
            gpu.release()
        os.close(lock_fd)  # release the mutation serialization lock

    logtxt = log.read_text(encoding="utf-8", errors="replace")
    prog = re.findall(r"(\d+)/(\d+)", logtxt)
    total = int(prog[-1][1]) if prog else 0
    score = _score_results(
        total,
        res.read_text(encoding="utf-8", errors="replace"),
        bar,
    )
    doc = {"tag": tag, "total": total, "killed": score["killed"],
           "survived": score["survived"], "no_tests": score["no_tests"],
           "kill_rate": score["kill_rate"], "bar": bar, "pass": score["pass"],
           "timeout_multiplier": tmult, "survivors": score["survivors"],
           "no_test_mutants": score["no_test_mutants"]}
    surv_json.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return doc


def main(argv: list) -> int:
    args = list(argv)
    jobs = timeout = None
    if "--jobs" in args:
        i = args.index("--jobs")
        jobs = int(args[i + 1]); del args[i:i + 2]
    if "--timeout" in args:
        i = args.index("--timeout")
        timeout = float(args[i + 1]); del args[i:i + 2]
    assert args, "usage: mutation.py <registry.json> [--jobs N] [--timeout SEC]"
    doc = run_mutation(args[0], jobs=jobs, timeout=timeout)
    print(f"MUTATION tag={doc['tag']} total={doc['total']} killed={doc['killed']} "
          f"survived={doc['survived']} no_tests={doc['no_tests']} "
          f"kill_rate={doc['kill_rate']:.4f} bar={doc['bar']} "
          f"timeout_x{doc['timeout_multiplier']} {'PASS' if doc['pass'] else 'FAIL'}")
    return 0 if doc["pass"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
