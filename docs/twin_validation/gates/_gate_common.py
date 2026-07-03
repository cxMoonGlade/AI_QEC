#!/usr/bin/env python
from __future__ import annotations

r"""Shared record-gate plumbing (G4-G7) — config seam, arms, det-column map, cluster bootstrap.

Binds to docs/twin_validation/coupled_teacher_round_gates_prereg.md §2 (gate-suite common
protocol): §2.1 run-config seam + A-CFG-1, §2.2 pinned teacher interface + A-DET-1, §2.3
seeds/arms, §2.4 batching + cluster-aware inference (red-team R6), §2.5 GENUINE-vs-VACUOUS.

This module is TRACKED gate plumbing; it runs no project logic at import (the cuda teacher is
imported lazily inside functions that the orchestrator runs serially post-review). Epistemic
classes carried per the prereg's registered ids.

SCRIPTED-EXECUTION DISCIPLINE: helpers only; each gate script owns its precondition asserts,
printed evidence, JSON emission, GATE_RESULT line and __main__ guard.
"""

import hashlib
import importlib
import json
import sys
from pathlib import Path
from typing import Any, Callable

import numpy as np

# --- import path: make `qec_twin` importable when a gate is run as a bare script ---------
_REPO_ROOT = Path(__file__).resolve().parents[3]
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

#: default config path the orchestrator writes after G0-v2 (§2.1).
DEFAULT_CONFIG_PATH = "docs/twin_validation/gates/gate_run_config.json"
CONFIG_SCHEMA = "qec_twin.gates.coupled_teacher_gate_run_config.v1"

#: n_checks per fixture (§2.1 A-CFG-1 structural consistency check).
FIXTURE_N_CHECKS = {"4q": 1, "5q": 2}

#: §2.4 registered floor (c): cluster count n_traj = N_run/S must be >= this.
MIN_N_TRAJ = 2000

#: the primary lag for the single-test statistics (§5.1); lags 2..4 reported.
PRIMARY_LAG = 1


# --------------------------------------------------------------------------- #
# config seam (§2.1)                                                           #
# --------------------------------------------------------------------------- #
class ConfigError(RuntimeError):
    """A missing / sentinel / malformed gate_run_config.json — the gate fails LOUDLY (§2.1)."""


def load_gate_config(path: str | None) -> dict[str, Any]:
    """Load + validate gate_run_config.json. FAIL LOUDLY on missing OR sentinel values.

    Sentinel test (brief): R_star < 1 OR fixture == "PENDING_G0V2" => the orchestrator has
    not provisioned the config from G0-v2's chosen triple yet.
    """

    cfg_path = Path(path or DEFAULT_CONFIG_PATH)
    if not cfg_path.is_file():
        raise ConfigError(
            f"gate_run_config.json not provisioned by G0-v2 yet (missing at {cfg_path}); "
            "the orchestrator writes it from G0-v2's chosen (fixture, R*, N*) triple"
        )
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    if cfg.get("schema") != CONFIG_SCHEMA:
        raise ConfigError(f"config schema {cfg.get('schema')!r} != {CONFIG_SCHEMA!r}")
    fixture = str(cfg.get("fixture", ""))
    r_star = int(cfg.get("R_star", 0))
    if r_star < 1 or fixture == "PENDING_G0V2":
        raise ConfigError(
            "gate_run_config.json not provisioned by G0-v2 yet "
            f"(R_star={r_star}, fixture={fixture!r} still carry template sentinels)"
        )
    if fixture not in FIXTURE_N_CHECKS:
        raise ConfigError(f"unknown fixture {fixture!r}; expected one of {sorted(FIXTURE_N_CHECKS)}")
    if int(cfg.get("N_star", 0)) < 1:
        raise ConfigError(f"N_star must be >= 1, got {cfg.get('N_star')!r}")
    cfg["_config_path"] = str(cfg_path)
    cfg["_config_sha256"] = hashlib.sha256(cfg_path.read_bytes()).hexdigest()
    return cfg


def import_teacher_factory(dotted: str) -> Callable[..., Any]:
    """Import a "module:callable" teacher factory (§2.1 A-CFG-1)."""

    if ":" not in dotted:
        raise ConfigError(f"teacher_factory {dotted!r} must be 'module:callable'")
    mod_name, _, attr = dotted.partition(":")
    module = importlib.import_module(mod_name)
    factory = getattr(module, attr)
    return factory


def build_regime(cfg: dict[str, Any], teacher: Any):
    """Regime(R=R_star, register="subregister", n_active=<fixture qubits>, n_stab=<n_checks>) (§2.2).

    n_active is read from the constructed teacher's schedule (the fixture's qubit count),
    n_stab from the teacher's n_stab property — both authoritative over any config guess.
    """

    from qec_twin.audit.certify import Regime  # lazy: value types, no GPU

    n_active = int(teacher.sched.num_qubits)
    n_stab = int(teacher.n_stab)
    return Regime(R=int(cfg["R_star"]), register="subregister", n_active=n_active, n_stab=n_stab)


def construct_teacher(cfg: dict[str, Any]) -> Any:
    """Import teacher_factory + call with **teacher_kwargs (§2.1 A-CFG-1)."""

    factory = import_teacher_factory(str(cfg["teacher_factory"]))
    kwargs = dict(cfg.get("teacher_kwargs") or {})
    return factory(**kwargs)


def assert_fixture_consistency(cfg: dict[str, Any], teacher: Any, det_width: int) -> dict[str, Any]:
    """§2.1 A-CFG-1: det width B == R*·n_checks (n_checks: 4q->1, 5q->2). FAIL LOUD with shapes."""

    fixture = str(cfg["fixture"])
    r_star = int(cfg["R_star"])
    n_checks_expected = FIXTURE_N_CHECKS[fixture]
    n_stab_teacher = int(teacher.n_stab)
    b_expected = r_star * n_checks_expected
    ok = (det_width == b_expected) and (n_stab_teacher == n_checks_expected)
    if not ok:
        raise ConfigError(
            "fixture/teacher/det-width inconsistency (A-CFG-1): "
            f"fixture={fixture!r} expects n_checks={n_checks_expected}, R*={r_star} => B={b_expected}; "
            f"observed det_width={det_width}, teacher.n_stab={n_stab_teacher}"
        )
    return {"fixture": fixture, "R_star": r_star, "n_checks_expected": n_checks_expected,
            "det_width_B": det_width, "teacher_n_stab": n_stab_teacher, "consistent": True}


# --------------------------------------------------------------------------- #
# arms (§2.3)                                                                  #
# --------------------------------------------------------------------------- #
def emit_arm(teacher: Any, regime: Any, *, m: int, N: int, seed: int) -> dict[str, np.ndarray]:
    """Emit one arm's {det,obs}, asserting the pinned payload surface (§2.2)."""

    payload = teacher.emit(regime, m=int(m), N=int(N), seed=int(seed))
    if set(payload.keys()) - {"det", "obs", "marg"}:
        raise RuntimeError(f"emit payload carried unexpected keys {sorted(payload.keys())}")
    det = np.asarray(payload["det"])
    obs = np.asarray(payload["obs"])
    if det.ndim != 2 or det.dtype != np.uint8:
        raise RuntimeError(f"det must be (N,B) uint8, got shape {det.shape} dtype {det.dtype}")
    if obs.ndim != 1 or obs.dtype != np.uint8 or obs.shape[0] != det.shape[0]:
        raise RuntimeError(f"obs must be (N,) uint8 aligned with det, got {obs.shape} {obs.dtype}")
    return {"det": det, "obs": obs}


# --------------------------------------------------------------------------- #
# detector-column map (§2.2 A-DET-1)                                           #
# --------------------------------------------------------------------------- #
def detector_column_map(teacher: Any, det_width: int) -> dict[str, Any]:
    """Build the (check, round) -> column map from teacher.sched.record_layout_ref["detectors"].

    A-DET-1: det columns follow the schedule record-layout detector order (round-major round-delta
    'delta:<check>:round<r>' rows for rounds 1..R-1, then 'final:<check>' closure rows — see
    simulator/record_layout.py build_repeated_memory_record_layout). The schedule's
    record_layout_ref detector dicts carry `name` but NOT a `kind` field (grounded in-source
    2026-07-03: analog_schedule._record_layout_ref rebuilds detectors from DetectorDef steps with
    name/keys/coords only), so the round-delta-vs-final-closure split is derived from the DECLARED
    NAME PREFIX ('delta:' vs 'final:'), which IS the A-DET-1 declaration order. A column-count
    mismatch vs det width B, or any detector whose name matches neither prefix, FAILS loudly.
    Round-delta detectors are the timelike stream S1/S2 consume; the final-closure detectors are
    the last column block.
    """

    layout = teacher.sched.record_layout_ref
    detectors = list(layout.get("detectors", ()))
    if len(detectors) != det_width:
        raise RuntimeError(
            f"record_layout detectors count {len(detectors)} != det width B {det_width} (A-DET-1)"
        )
    names = [str(d.get("name", "")) for d in detectors]
    round_delta_cols = [i for i, nm in enumerate(names) if nm.startswith("delta:")]
    final_cols = [i for i, nm in enumerate(names) if nm.startswith("final:")]
    known = set(round_delta_cols) | set(final_cols)
    if known != set(range(det_width)):
        unknown = [names[i] for i in range(det_width) if i not in known]
        raise RuntimeError(
            "record_layout detector names do not partition cleanly into delta:/final: "
            f"(A-DET-1); unrecognized detector names: {unknown}"
        )
    return {
        "detector_names": names,
        "round_delta_columns": round_delta_cols,
        "final_closure_columns": final_cols,
        "n_round_delta": len(round_delta_cols),
        "n_final_closure": len(final_cols),
    }


def require_min_delta_rounds(colmap: dict[str, Any], n_stab: int, min_delta: int, gate: str) -> int:
    """FAIL loudly if the schedule has fewer than `min_delta` round-delta rounds.

    The cross-cycle statistics (Spitz p_ij / count autocov at lag L) need at least L+1 delta
    rounds; the timelike pairs vanish otherwise. There are R-1 delta rounds for an R-round
    schedule, so lag-1 needs R >= 3. G0-v2's decision tree expects R* well above this (4q R*
    in {12,16}); a degenerate small-R* config must fail loudly here, not read nan.
    """

    n_delta = len(colmap["round_delta_columns"]) // int(n_stab)
    if n_delta < int(min_delta):
        raise ConfigError(
            f"{gate}: schedule has {n_delta} round-delta rounds (R-1); the cross-cycle "
            f"statistics need >= {min_delta} (lag-1 needs >= 2 => R* >= 3). Chosen R* is too "
            "small for record-level correlation — G0-v2's decision tree expects a larger R*."
        )
    return n_delta


def round_delta_by_round(det: np.ndarray, colmap: dict[str, Any], n_stab: int) -> np.ndarray:
    """Reshape the round-delta detector columns into (N, n_rounds_delta, n_stab).

    Round-major: the round-delta columns are consecutive blocks of n_stab per delta round
    (record_layout declaration order, A-DET-1). Returns the (shots, delta_round, check) cube
    the cross-cycle statistics slice. n_stab must divide the round-delta column count.
    """

    cols = colmap["round_delta_columns"]
    n_delta = len(cols) // int(n_stab)
    if n_delta * int(n_stab) != len(cols):
        raise RuntimeError(
            f"round-delta columns {len(cols)} not divisible by n_stab {n_stab} (A-DET-1)"
        )
    sub = det[:, cols]  # (N, n_delta*n_stab) in round-major declaration order
    return sub.reshape(det.shape[0], n_delta, int(n_stab))


# --------------------------------------------------------------------------- #
# batching / cluster-aware inference (§2.4, red-team R6, L11)                  #
# --------------------------------------------------------------------------- #
def precondition_n_traj(n_run: int, spt: int) -> int:
    """§2.4 floor (c): number of clusters n_traj = N_run/S >= MIN_N_TRAJ else FAIL preconditions."""

    spt = int(spt)
    if spt < 1:
        raise ConfigError(f"shots_per_trajectory must be >= 1, got {spt}")
    n_traj = (int(n_run) + spt - 1) // spt
    if n_traj < MIN_N_TRAJ:
        raise ConfigError(
            f"cluster count n_traj={n_traj} (N_run={n_run}, S={spt}) below the registered "
            f"floor {MIN_N_TRAJ} (§2.4 L11) — a batched config with too few trajectories "
            "cannot carry honest cluster SEs"
        )
    return n_traj


def cluster_blocks(n_run: int, spt: int) -> list[np.ndarray]:
    """Consecutive S-blocks of shot indices = the trajectory clusters (§2.4).

    Degenerates to per-shot clusters at S=1 (a shot bootstrap). Returns a list of index arrays.
    """

    spt = int(spt)
    idx = np.arange(int(n_run))
    if spt <= 1:
        return [idx[i:i + 1] for i in range(int(n_run))]
    return [idx[j * spt:(j + 1) * spt] for j in range((int(n_run) + spt - 1) // spt)]


def cluster_bootstrap_se(
    statistic: Callable[[np.ndarray], float],
    n_run: int,
    spt: int,
    *,
    B: int,
    seed: int,
) -> dict[str, float]:
    """Trajectory-cluster bootstrap SE of `statistic(shot_index_subset)` (§2.4, L11).

    Resamples CLUSTERS (consecutive S-blocks) with replacement, concatenates their shot
    indices, recomputes the statistic on that resample. Returns {point, se, B_effective}.
    The statistic receives the resampled shot indices (into the arm arrays the caller closed
    over). NaN statistic values (e.g. a degenerate resample) are dropped and counted.
    """

    blocks = cluster_blocks(n_run, spt)
    rng = np.random.default_rng(int(seed))
    n_clusters = len(blocks)
    point = float(statistic(np.arange(int(n_run))))
    draws: list[float] = []
    for _ in range(int(B)):
        pick = rng.integers(0, n_clusters, size=n_clusters)
        idx = np.concatenate([blocks[p] for p in pick])
        val = statistic(idx)
        if np.isfinite(val):
            draws.append(float(val))
    if len(draws) < 2:
        return {"point": point, "se": float("nan"), "B_effective": len(draws)}
    se = float(np.std(np.asarray(draws), ddof=1))
    return {"point": point, "se": se, "B_effective": len(draws)}


def zscore(point: float, se: float) -> float:
    """point / se, guarding se == 0 / nan (returns +/-inf on a real nonzero point, nan on 0/0)."""

    if not np.isfinite(se) or se == 0.0:
        if point == 0.0 or not np.isfinite(point):
            return float("nan")
        return float(np.inf) if point > 0 else float(-np.inf)
    return float(point) / float(se)


# --------------------------------------------------------------------------- #
# evidence emission                                                           #
# --------------------------------------------------------------------------- #
def content_hash(evidence: dict[str, Any]) -> str:
    """sha256 over the load-bearing numbers (deterministic key order)."""

    payload = json.dumps(evidence, sort_keys=True, default=_json_default).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _json_default(o: Any):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return float(o)


def write_evidence(gate: str, evidence: dict[str, Any], out_name: str) -> tuple[Path, str]:
    """Attach content_hash, write gates/<out_name>, return (path, hash)."""

    h = content_hash(evidence)
    evidence["content_hash"] = h
    out_path = Path(__file__).resolve().parent / out_name
    out_path.write_text(json.dumps(evidence, indent=2, sort_keys=True, default=_json_default),
                        encoding="utf-8")
    return out_path, h


def emit_gate_result(gate: str, verdict: str, h: str, out_path: Path) -> None:
    """Print the runner-aggregable evidence footer + GATE_RESULT line."""

    print("\n" + "=" * 78, flush=True)
    print(f"{gate} VERDICT: {verdict}   content_hash={h[:16]}...", flush=True)
    print(f"evidence -> {out_path}", flush=True)
    print(f"GATE_RESULT {gate} {verdict} {h}", flush=True)
    print("=" * 78, flush=True)
    sys.stdout.flush()
