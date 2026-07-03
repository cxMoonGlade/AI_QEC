#!/usr/bin/env python
from __future__ import annotations

r"""G7 GATE — isolation (structural + scramble invariance).

Binds to docs/twin_validation/coupled_teacher_round_gates_prereg.md §6 EXACTLY. N_g7 = 64 (c) —
isolation is structural, not statistical.

  P-G7-1 (a): payload keys subset {det, obs, marg}; det (N,B) uint8; obs (N,) uint8; NO
              truth/manifest keys in the payload (red-team R4).
  P-G7-2 (a): (i) determinism: emit(seed) twice -> byte-identical det+obs.
              (ii) truth-label scramble: deep-copy teacher.truth, scramble every string-valued
                   label field in the LIVE dict, re-emit at the same seed -> byte-identical.
              (iii) relabel-hook probe: exercise a documented relabel/clone hook if present,
                    else SKIPPED(no-relabel-hook). A-G7-1: records exactly which forms ran.
              (iv, F7) last_emit snapshot: mutate truth['last_emit'] then re-access .truth ->
                    the fresh copy must be unaffected (the deepcopy is not a live reference).
  P-G7-3 (a): isinstance(teacher, ControlledTeacher) (runtime-checkable); .truth is a dict property
              reachable evaluator-side only; CertReport.truth is the only cert-side conduit.
  P-G7-4 (a): static import scan — NO module under src/qec_twin/calibration/ or hardware/ imports
              qec_twin.mechanisms (regex over source). simulator/ EXCLUDED (evaluator-side frontend
              legitimately imports mechanisms.axis1_primitives) with the printed reason.
  Cheat-twin: SKIPPED(optional diagnostic per contract G7 — not a gate) row.

Verdict: PASS <=> P-G7-1 AND P-G7-2(i,ii,iv) AND P-G7-3 AND P-G7-4.

SCRIPTED-EXECUTION: committed, __main__-guarded; preconditions + printed evidence + flush;
emits g7_isolation.json. GPU-only where the teacher touches cuda (emit at N=64 is cheap).
    conda run -n aiqec python docs/twin_validation/gates/g7_isolation.py --config <path>
"""

import argparse
import copy
import re
import sys
from pathlib import Path

import numpy as np

from _gate_common import (  # noqa: E402
    _REPO_ROOT,
    build_regime,
    construct_teacher,
    emit_gate_result,
    load_gate_config,
    write_evidence,
)

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

GATE = "G7_isolation"


# =========================================================================== #
# P-G7-1 payload surface                                                       #
# =========================================================================== #
def check_payload_surface(payload: dict, det_width_hint: int | None) -> dict:
    """P-G7-1: keys subset {det, obs, marg}; det (N,B) uint8; obs (N,) uint8; no truth/manifest."""

    keys = set(payload.keys())
    allowed = {"det", "obs", "marg"}
    extra = keys - allowed
    det = np.asarray(payload["det"])
    obs = np.asarray(payload["obs"])
    forbidden_substrings = ("truth", "manifest", "applied", "params", "source", "channel")
    forbidden_hit = [k for k in keys if any(s in str(k).lower() for s in forbidden_substrings)]
    ok = (not extra and det.ndim == 2 and det.dtype == np.uint8
          and obs.ndim == 1 and obs.dtype == np.uint8 and obs.shape[0] == det.shape[0]
          and not forbidden_hit)
    return {"payload_keys": sorted(keys), "extra_keys": sorted(extra),
            "det_shape": list(det.shape), "det_dtype": str(det.dtype),
            "obs_shape": list(obs.shape), "obs_dtype": str(obs.dtype),
            "forbidden_key_hits": forbidden_hit, "pass": bool(ok)}


# =========================================================================== #
# P-G7-2 determinism + truth-label scramble + relabel hook                     #
# =========================================================================== #
def check_determinism(teacher, regime, *, m: int, n: int, seed: int) -> dict:
    """(i) emit(seed) twice -> byte-identical det + obs."""

    a = teacher.emit(regime, m=int(m), N=int(n), seed=int(seed))
    b = teacher.emit(regime, m=int(m), N=int(n), seed=int(seed))
    det_id = bool(np.array_equal(np.asarray(a["det"]), np.asarray(b["det"])))
    obs_id = bool(np.array_equal(np.asarray(a["obs"]), np.asarray(b["obs"])))
    return {"det_byte_identical": det_id, "obs_byte_identical": obs_id,
            "pass": bool(det_id and obs_id)}


# operational string attributes that emit reads FUNCTIONALLY (a device string, an arm name, a
# coupling mode) — scrambling these would crash emit rather than test LABEL invariance, so form 2
# protects them by key. Everything else that is string-VALUED is a label and is fair game.
_PROTECTED_STRING_KEYS = frozenset({
    "_device", "device", "_arm", "arm", "coupling_arm", "coupling_mode",
    "source_kind", "backend", "basis", "kind",
})


def _scramble_label_strings_in_place(obj, rng, *, protect: frozenset[str]) -> int:
    """Scramble every LABEL string value (dict value / list item) IN PLACE, skipping any value
    whose dict key is in `protect` (operational strings emit reads functionally).

    Returns the count of scrambled fields. A scramble = replace the string with a random sentinel,
    so if emit read a mutable LABEL its output would change. Dict KEYS are never changed.
    """

    count = 0
    if isinstance(obj, dict):
        for k in list(obj.keys()):
            v = obj[k]
            if isinstance(v, str):
                if str(k) in protect:
                    continue
                obj[k] = f"__SCRAMBLED__{int(rng.integers(0, 1 << 30))}"
                count += 1
            else:
                count += _scramble_label_strings_in_place(v, rng, protect=protect)
    elif isinstance(obj, list):
        for i in range(len(obj)):
            if isinstance(obj[i], str):
                obj[i] = f"__SCRAMBLED__{int(rng.integers(0, 1 << 30))}"
                count += 1
            else:
                count += _scramble_label_strings_in_place(obj[i], rng, protect=protect)
    return count


def check_truth_scramble(teacher, regime, *, m: int, n: int, seed: int) -> dict:
    """(ii) baseline emit; then scramble every string-valued LABEL in the LIVE truth dict and
    re-emit at the same seed -> byte-identical (guards emit reading truth mutably).

    A-G7-1: the binding scramble form depends on Builder 2's surface; the gate records exactly
    which forms ran. teacher.truth is a PROPERTY that rebuilds a fresh dict on each access
    (coupled_teachers.py), so:
      * form 1 scrambles the truth-dict view the evaluator holds — a structural probe that the
        property does not hand emit a mutable label.
      * form 2 scrambles the LABEL string values on the instance __dict__ while PROTECTING the
        operational strings emit reads functionally (_PROTECTED_STRING_KEYS: device/arm/mode/…) —
        so a LABEL-reading emit moves the records while a legitimate operational read does not
        crash the probe. The instance is deep-copied and restored in `finally`."""

    rng = np.random.default_rng(int(seed) ^ 0x5F3759DF)
    base = teacher.emit(regime, m=int(m), N=int(n), seed=int(seed))
    forms_ran = []
    # form 1: scramble the truth dict view the evaluator holds (protect operational keys too).
    truth_view = teacher.truth
    n_scrambled_view = _scramble_label_strings_in_place(truth_view, rng, protect=_PROTECTED_STRING_KEYS)
    forms_ran.append({"form": "scramble_truth_property_view", "fields": n_scrambled_view})
    # form 2: scramble LABEL strings on the instance __dict__ (deep-copied first to restore;
    # operational strings protected so the re-emit exercises label-invariance, not a crash).
    saved = copy.deepcopy(getattr(teacher, "__dict__", {}))
    after = base  # default if form 2 cannot run
    n_scrambled_attr = 0
    try:
        n_scrambled_attr = _scramble_label_strings_in_place(
            teacher.__dict__, rng, protect=_PROTECTED_STRING_KEYS)
        forms_ran.append({"form": "scramble_instance_dict_label_strings", "fields": n_scrambled_attr})
        after = teacher.emit(regime, m=int(m), N=int(n), seed=int(seed))
    finally:
        # restore instance state so downstream checks see the pristine teacher.
        teacher.__dict__.clear()
        teacher.__dict__.update(saved)
    det_id = bool(np.array_equal(np.asarray(base["det"]), np.asarray(after["det"])))
    obs_id = bool(np.array_equal(np.asarray(base["obs"]), np.asarray(after["obs"])))
    # F7 honesty (scrutinize-vacuous-checks): report the coverage. Form 1 (truth property VIEW)
    # cannot affect emit BY CONSTRUCTION — teacher.truth rebuilds a fresh dict each access, so the
    # scrambled view is discarded and never reaches emit; it is a structural non-leak, not a
    # falsifiable behaviour test. Form 2 (instance __dict__) is the falsifiable probe, but for a
    # well-isolated teacher emit reads NO instance label strings and the frozen dataclass fields
    # (_source/_config/_spec) are not recursed, so it scrambles few fields (n_scrambled_attr). The
    # invariance holding is genuine evidence of isolation but the probe has LOW coverage.
    form2 = next((f for f in forms_ran if f["form"] == "scramble_instance_dict_label_strings"), None)
    n_form2 = int(form2["fields"]) if form2 else 0
    coverage = "GENUINE" if n_form2 >= 3 else "GENUINE-LOW-COVERAGE"
    return {"forms_ran": forms_ran, "det_byte_identical_after_scramble": det_id,
            "obs_byte_identical_after_scramble": obs_id, "pass": bool(det_id and obs_id),
            "protected_operational_keys": sorted(_PROTECTED_STRING_KEYS),
            "form2_scrambled_fields": n_form2, "coverage_class": coverage,
            "note": "scrambling string LABELS (not the numeric mechanism fields, not the protected "
                    "operational strings) must not move the records; a label-reading emit would "
                    "break here (red-team R4). Form 1 is a by-construction non-leak (fresh-dict "
                    "property); form 2 is the falsifiable probe but low-coverage for this teacher "
                    "(emit reads no instance label strings) — the pass is real isolation, weak power."}


def check_last_emit_snapshot(teacher, regime, *, m: int, n: int, seed: int) -> dict:
    """(iv, F7) truth['last_emit'] must be a SNAPSHOT (deep copy): an evaluator mutating it must not
    reach the teacher's internal `_last_emit`, and two `.truth` accesses must not share the mutable
    reference. C1 now reads truth['last_emit']['params_manifest_sample'], so this isolation matters.

    Emits once to populate `_last_emit`, grabs truth['last_emit'], mutates the evaluator's copy, then
    re-accesses `.truth` and asserts the fresh copy is unaffected (proves the deepcopy at
    coupled_teachers.py:truth). A live-reference bug would leak the mutation into the next access."""

    teacher.emit(regime, m=int(m), N=int(n), seed=int(seed))  # populate _last_emit
    t1 = teacher.truth
    le1 = t1.get("last_emit")
    if not isinstance(le1, dict):
        return {"status": "SKIPPED(last_emit-not-dict-after-emit)", "last_emit_type": str(type(le1)),
                "pass": True, "note": "no last_emit dict to probe (teacher may not record one)"}
    le1["__g7_mutation_probe__"] = "__MUTATED__"
    original_seed = le1.get("seed")
    if isinstance(original_seed, int):
        le1["seed"] = -999_999
    t2 = teacher.truth
    le2 = t2.get("last_emit") or {}
    fresh_object = bool(le1 is not le2)
    unaffected = bool("__g7_mutation_probe__" not in le2 and le2.get("seed") != -999_999)
    return {"fresh_object_each_access": fresh_object,
            "internal_state_unaffected_by_mutation": unaffected,
            "pass": bool(fresh_object and unaffected),
            "note": "truth['last_emit'] is a deepcopy snapshot; mutating the evaluator's copy must "
                    "not reach the teacher's _last_emit nor the next .truth access (F7)"}


def check_relabel_hook(teacher, regime, *, m: int, n: int, seed: int) -> dict:
    """(iii) if the teacher exposes a documented relabel/clone-with-labels hook, exercise it; else
    SKIPPED(no-relabel-hook) — visible, not silent (A-G7-1)."""

    hook_names = ("relabel", "clone_with_labels", "with_labels", "relabelled")
    present = [h for h in hook_names if hasattr(teacher, h) and callable(getattr(teacher, h))]
    if not present:
        return {"status": "SKIPPED(no-relabel-hook)", "hooks_probed": list(hook_names)}
    # a relabel hook, if present, must not change the emitted records at a fixed seed.
    base = teacher.emit(regime, m=int(m), N=int(n), seed=int(seed))
    hook = present[0]
    try:
        relabelled = getattr(teacher, hook)()
        after = relabelled.emit(regime, m=int(m), N=int(n), seed=int(seed))
        det_id = bool(np.array_equal(np.asarray(base["det"]), np.asarray(after["det"])))
        obs_id = bool(np.array_equal(np.asarray(base["obs"]), np.asarray(after["obs"])))
        return {"status": f"RAN({hook})", "det_byte_identical": det_id, "obs_byte_identical": obs_id,
                "pass": bool(det_id and obs_id)}
    except Exception as exc:  # a broken hook is a finding, reported, not a crash
        return {"status": f"RAN({hook})-ERROR", "error": f"{type(exc).__name__}: {exc}"[:200],
                "pass": False}


# =========================================================================== #
# P-G7-3 protocol + truth conduit                                              #
# =========================================================================== #
def check_protocol(teacher) -> dict:
    """P-G7-3: isinstance(teacher, ControlledTeacher) runtime-checkable; .truth is a dict property;
    truth carries no det/obs arrays (the evaluator-only conduit)."""

    from qec_twin.audit.certify.types import ControlledTeacher

    is_ct = isinstance(teacher, ControlledTeacher)
    truth = teacher.truth
    truth_is_dict = isinstance(truth, dict)
    truth_has_records = any(k in truth for k in ("det", "obs")) or any(
        isinstance(v, np.ndarray) for v in truth.values())
    return {"isinstance_ControlledTeacher": bool(is_ct), "truth_is_dict": bool(truth_is_dict),
            "truth_carries_record_arrays": bool(truth_has_records),
            "pass": bool(is_ct and truth_is_dict and not truth_has_records)}


# =========================================================================== #
# P-G7-4 static import scan (learner path never imports mechanisms)            #
# =========================================================================== #
def check_import_scan() -> dict:
    """P-G7-4: NO module under src/qec_twin/calibration/ or hardware/ imports qec_twin.mechanisms.

    Declared scope: the learner path = calibration (consumes observations) + hardware (contract
    §B-8). simulator/ is EXCLUDED (the evaluator-side frontend legitimately imports
    mechanisms.axis1_primitives) with the printed reason. Regex over source files.
    """

    pat = re.compile(r"(from\s+qec_twin\.mechanisms|import\s+qec_twin\.mechanisms)")
    src = _REPO_ROOT / "src" / "qec_twin"
    scanned = {"calibration": [], "hardware": []}
    violations = []
    for sub in ("calibration", "hardware"):
        base = src / sub
        if not base.exists():
            continue
        for py in sorted(base.rglob("*.py")):
            text = py.read_text(encoding="utf-8", errors="replace")
            scanned[sub].append(str(py.relative_to(_REPO_ROOT)))
            if pat.search(text):
                violations.append(str(py.relative_to(_REPO_ROOT)))
    return {"scanned_counts": {k: len(v) for k, v in scanned.items()},
            "violations": violations, "pass": bool(not violations),
            "excluded": {"simulator/": "evaluator-side frontend legitimately imports "
                                       "mechanisms.axis1_primitives (declared scope, §6 P-G7-4)"}}


# =========================================================================== #
# runner                                                                      #
# =========================================================================== #
def _preconditions(cfg: dict) -> dict:
    import torch

    assert torch.cuda.is_available(), "G7 teacher is GPU-only; cuda must be available"
    n_g7 = int(cfg.get("g7_n", 64))
    print(f"[precond] cuda={torch.cuda.is_available()} device={torch.cuda.get_device_name(0)}",
          flush=True)
    print(f"[precond] fixture={cfg['fixture']} R*={cfg['R_star']} N_g7={n_g7} (structural, not "
          "statistical)", flush=True)
    return {"n_g7": n_g7}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="G7 isolation gate")
    parser.add_argument("--config", default=None)
    args = parser.parse_args(argv)

    print("=" * 78, flush=True)
    print("G7 GATE — isolation (structural + scramble invariance; prereg §6)", flush=True)
    print("=" * 78, flush=True)

    cfg = load_gate_config(args.config)
    pre = _preconditions(cfg)
    n_g7 = pre["n_g7"]
    m = int(cfg.get("m", 0))
    seed = int(cfg.get("seeds", {}).get("shared", 101))

    teacher = construct_teacher(cfg)
    regime = build_regime(cfg, teacher)

    payload = teacher.emit(regime, m=m, N=n_g7, seed=seed)
    p1 = check_payload_surface(payload, teacher.n_stab * cfg["R_star"])
    print(f"[P-G7-1] payload keys={p1['payload_keys']} det={p1['det_shape']}/{p1['det_dtype']} "
          f"obs={p1['obs_shape']}/{p1['obs_dtype']} forbidden={p1['forbidden_key_hits']} -> "
          f"{'PASS' if p1['pass'] else 'FAIL'}", flush=True)

    p2i = check_determinism(teacher, regime, m=m, n=n_g7, seed=seed)
    print(f"[P-G7-2(i)] determinism det={p2i['det_byte_identical']} obs={p2i['obs_byte_identical']} "
          f"-> {'PASS' if p2i['pass'] else 'FAIL'}", flush=True)

    p2ii = check_truth_scramble(teacher, regime, m=m, n=n_g7, seed=seed)
    print(f"[P-G7-2(ii)] truth scramble forms={[f['form'] for f in p2ii['forms_ran']]} "
          f"byte-identical det={p2ii['det_byte_identical_after_scramble']} "
          f"obs={p2ii['obs_byte_identical_after_scramble']} -> {'PASS' if p2ii['pass'] else 'FAIL'}",
          flush=True)

    p2iii = check_relabel_hook(teacher, regime, m=m, n=n_g7, seed=seed)
    print(f"[P-G7-2(iii)] relabel hook: {p2iii['status']}", flush=True)

    p2iv = check_last_emit_snapshot(teacher, regime, m=m, n=n_g7, seed=seed)
    print(f"[P-G7-2(iv)] last_emit snapshot (F7): fresh_each_access="
          f"{p2iv.get('fresh_object_each_access')} unaffected_by_mutation="
          f"{p2iv.get('internal_state_unaffected_by_mutation')} -> "
          f"{'PASS' if p2iv['pass'] else 'FAIL'}", flush=True)

    p3 = check_protocol(teacher)
    print(f"[P-G7-3] isinstance(ControlledTeacher)={p3['isinstance_ControlledTeacher']} "
          f"truth_is_dict={p3['truth_is_dict']} truth_has_records={p3['truth_carries_record_arrays']} "
          f"-> {'PASS' if p3['pass'] else 'FAIL'}", flush=True)

    p4 = check_import_scan()
    print(f"[P-G7-4] import scan calibration+hardware: scanned={p4['scanned_counts']} "
          f"violations={p4['violations']} -> {'PASS' if p4['pass'] else 'FAIL'}", flush=True)

    verdict = "PASS" if (p1["pass"] and p2i["pass"] and p2ii["pass"] and p2iv["pass"]
                         and p3["pass"] and p4["pass"]) else "FAIL"

    check_class = {
        "P_G7_1_payload_surface": "GENUINE (a rich manifest leak fails — red-team R4)",
        "P_G7_2i_determinism": "GENUINE (same seed must reproduce byte-identical records — C-8)",
        "P_G7_2ii_truth_scramble": (
            f"{p2ii['coverage_class']} (form1 = by-construction non-leak via fresh-dict truth "
            f"property; form2 scrambled {p2ii['form2_scrambled_fields']} instance label strings — "
            "the invariance is real isolation, but weak power when emit reads no labels; F7)"),
        "P_G7_2iii_relabel_hook": "GENUINE if a hook exists, else SKIPPED(no-relabel-hook) (visible)",
        "P_G7_2iv_last_emit_snapshot": "GENUINE (a live-reference truth['last_emit'] would leak the "
                                       "evaluator's mutation into the next .truth access / teacher "
                                       "state — the F7 deepcopy must prevent it)",
        "P_G7_3_protocol": "GENUINE (runtime-checkable protocol + truth-carries-no-records)",
        "P_G7_4_import_scan": "GENUINE (a mechanisms import in calibration/hardware fails the "
                              "isolation contract; simulator/ excluded with reason)",
    }

    evidence = {
        "gate": GATE,
        "verdict": verdict,
        "prereg": "docs/twin_validation/coupled_teacher_round_gates_prereg.md#6",
        "metric": "structural isolation (no metric; N_g7=64 structural)",
        "config": {"path": cfg.get("_config_path"), "sha256": cfg.get("_config_sha256"),
                   "fixture": cfg["fixture"], "R_star": cfg["R_star"], "N_g7": n_g7},
        "P_G7_1_payload_surface": p1,
        "P_G7_2i_determinism": p2i,
        "P_G7_2ii_truth_scramble": p2ii,
        "P_G7_2iii_relabel_hook": p2iii,
        "P_G7_2iv_last_emit_snapshot": p2iv,
        "P_G7_3_protocol": p3,
        "P_G7_4_import_scan": p4,
        "cheat_twin": {"status": "SKIPPED(optional diagnostic per contract G7 — not a gate)"},
        "predictions": {f"P_G7_{i}": {"class": "a"} for i in (1, 2, 3, 4)},
        "check_class": check_class,
    }
    out_path, h = write_evidence(GATE, evidence, "g7_isolation.json")
    emit_gate_result(GATE, verdict, h, out_path)
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
