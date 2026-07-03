#!/usr/bin/env python
from __future__ import annotations

r"""G8 — gate-suite runner + durability object.

Binds to docs/twin_validation/coupled_teacher_round_gates_prereg.md §7 EXACTLY.
Sequence (each a subprocess; stdout streamed + GATE_RESULT lines parsed):
    G2 fresh re-run (gates/g2_jointL.py) -> G4 -> G5 -> G6 -> G7.
SKIPPED rows for G1, G3a, G3b with the EXACT reason string:
    "not-this-round (ratified 2026-07-03 order: G0->teacher->G4-G8)".
g8_runner.json = {tracked_scripts (paths + sha256), output_hashes (per-gate JSON sha256),
result_summaries (gate, verdict, content_hash, rc), skipped rows, runner_rc,
outputs_dir_scratch_only: true, content_hash}. rc = 0 <=> every RUN gate PASS.
--fail-fast stops at the first FAIL (default: run all, aggregate).

SCRIPTED-EXECUTION: committed, __main__-guarded; the runner itself launches project code only via
subprocess (the orchestrator invokes THIS through outputs/run_gates_suite.sh). GPU-only gates run
serially — one subprocess at a time (no concurrent GPU jobs).
    conda run -n aiqec python docs/twin_validation/gates/run_gates.py --config <path> [--fail-fast]
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

_GATES_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _GATES_DIR.parents[2]

GATE = "G8_runner"
SKIP_REASON = "not-this-round (ratified 2026-07-03 order: G0->teacher->G4-G8)"
GATE_RESULT_RE = re.compile(r"^GATE_RESULT\s+(\S+)\s+(\S+)\s+(\S+)\s*$", re.MULTILINE)

# The RUN sequence (§7): each entry (label, script path relative to repo root, json output name).
# G2 takes no --config (its params are self-contained); G4-G7 require --config.
RUN_SEQUENCE = [
    ("G2_jointL", "docs/twin_validation/gates/g2_jointL.py", "g2_jointL.json", False),
    ("G4_imprint", "docs/twin_validation/gates/g4_imprint.py", "g4_imprint.json", True),
    ("G5_baseline", "docs/twin_validation/gates/g5_baseline.py", "g5_baseline.json", True),
    ("G6_ablation", "docs/twin_validation/gates/g6_ablation.py", "g6_ablation.json", True),
    ("G7_isolation", "docs/twin_validation/gates/g7_isolation.py", "g7_isolation.json", True),
]
SKIPPED_GATES = ["G1", "G3a", "G3b"]


def _sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_gate(label: str, script_rel: str, wants_config: bool, config: str | None,
              corrqec_root: str | None) -> dict:
    """Run one gate script as a subprocess; stream stdout; parse its GATE_RESULT line."""

    script = _REPO_ROOT / script_rel
    cmd = [sys.executable, str(script)]
    if wants_config and config is not None:
        cmd += ["--config", config]
    if label == "G4_imprint" and corrqec_root:
        cmd += ["--corrqec-root", corrqec_root]
    print(f"\n{'#' * 78}\n# RUN {label}: {' '.join(cmd)}\n{'#' * 78}", flush=True)
    proc = subprocess.run(cmd, cwd=str(_REPO_ROOT), capture_output=True, text=True)
    sys.stdout.write(proc.stdout)
    if proc.stderr:
        sys.stderr.write(proc.stderr)
    sys.stdout.flush()
    verdict = None
    content_hash = None
    matches = GATE_RESULT_RE.findall(proc.stdout)
    if matches:
        gate_name, verdict, content_hash = matches[-1]
    return {"gate": label, "verdict": verdict, "content_hash": content_hash,
            "rc": int(proc.returncode), "gate_result_seen": bool(matches)}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="G8 gate-suite runner")
    parser.add_argument("--config", default=None, help="gate_run_config.json for G4-G7")
    parser.add_argument("--corrqec-root", default=None, help="pristine corrqec root (G4)")
    parser.add_argument("--fail-fast", action="store_true", help="stop at the first FAIL")
    args = parser.parse_args(argv)

    print("=" * 78, flush=True)
    print("G8 RUNNER — G2-fresh -> G4 -> G5 -> G6 -> G7 (prereg §7)", flush=True)
    print("=" * 78, flush=True)

    result_summaries: list[dict] = []
    aborted = False
    for label, script_rel, _json_name, wants_config in RUN_SEQUENCE:
        res = _run_gate(label, script_rel, wants_config, args.config, args.corrqec_root)
        result_summaries.append(res)
        if args.fail_fast and (res["verdict"] != "PASS"):
            print(f"\n[fail-fast] {label} verdict={res['verdict']} rc={res['rc']} — stopping.",
                  flush=True)
            aborted = True
            break

    skipped = [{"gate": g, "reason": SKIP_REASON} for g in SKIPPED_GATES]
    for row in skipped:
        print(f"[SKIPPED] {row['gate']}: {row['reason']}", flush=True)

    tracked_scripts = {}
    for label, script_rel, _json_name, _wc in RUN_SEQUENCE:
        tracked_scripts[label] = {"path": script_rel,
                                  "sha256": _sha256_file(_REPO_ROOT / script_rel)}
    # the shared plumbing + this runner are tracked too.
    for extra in ("docs/twin_validation/gates/_gate_common.py",
                  "docs/twin_validation/gates/run_gates.py"):
        tracked_scripts[Path(extra).stem] = {"path": extra, "sha256": _sha256_file(_REPO_ROOT / extra)}

    output_hashes = {}
    for label, _s, json_name, _wc in RUN_SEQUENCE:
        output_hashes[label] = _sha256_file(_GATES_DIR / json_name)

    run_gates = [r for r in result_summaries if r["gate_result_seen"] or not aborted]
    all_pass = bool(result_summaries) and all(
        r["verdict"] == "PASS" for r in result_summaries) and not aborted
    runner_rc = 0 if all_pass else 1

    evidence = {
        "gate": GATE,
        "verdict": "PASS" if all_pass else "FAIL",
        "prereg": "docs/twin_validation/coupled_teacher_round_gates_prereg.md#7",
        "run_order": [r[0] for r in RUN_SEQUENCE],
        "tracked_scripts": tracked_scripts,
        "output_hashes": output_hashes,
        "result_summaries": result_summaries,
        "skipped": skipped,
        "aborted_fail_fast": bool(aborted),
        "runner_rc": runner_rc,
        "outputs_dir_scratch_only": True,
        "config": args.config,
    }
    payload = json.dumps(evidence, sort_keys=True, default=str).encode("utf-8")
    content_hash = hashlib.sha256(payload).hexdigest()
    evidence["content_hash"] = content_hash
    out_path = _GATES_DIR / "g8_runner.json"
    out_path.write_text(json.dumps(evidence, indent=2, sort_keys=True, default=str), encoding="utf-8")

    print("\n" + "=" * 78, flush=True)
    print("G8 SUMMARY", flush=True)
    for r in result_summaries:
        print(f"   {r['gate']:<14} verdict={r['verdict']} rc={r['rc']} "
              f"hash={(r['content_hash'] or '-')[:16]}", flush=True)
    for row in skipped:
        print(f"   {row['gate']:<14} SKIPPED ({row['reason']})", flush=True)
    print(f"   runner_rc={runner_rc} (0 <=> every RUN gate PASS)", flush=True)
    print(f"evidence -> {out_path}", flush=True)
    print(f"GATE_RESULT {GATE} {'PASS' if all_pass else 'FAIL'} {content_hash}", flush=True)
    print("=" * 78, flush=True)
    sys.stdout.flush()
    return runner_rc


if __name__ == "__main__":
    raise SystemExit(main())
