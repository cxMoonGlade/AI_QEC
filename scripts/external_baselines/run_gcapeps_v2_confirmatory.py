#!/usr/bin/env python3
"""Confirmatory-run harness for the GCAPEPS finite-memory fixture v2 (X8).

Governing preregistration (frozen; read it in full, INCLUDING "Pre-run
amendment 1 (2026-08-01)" AND "Pre-run amendment 2 (2026-08-01)" at the end):
  docs/simulator_validation/GCAPEPS_FINITE_MEMORY_FIXTURE_V2_X8_PREREG_2026-08-01.md
This script is the committed confirmatory harness required by amendment 1
item 9(iii): it embeds amendment-1 item 3 (mandatory X5-variant theta=0
dual gates), item 5 (Stage-0 measured worst-pair re-record + 1e-4 refusal),
and item 8 (inherited v1 exactness controls re-tripped at run time), plus
the frozen metric ladder (v1 BLP objects, guard 1e-10, the 10 x err_cell
two-sided margin, verdict vocabulary) and the frozen adjudication rules
(item 2 majority >= 4 of 6 with 3/6 = NOT-CONFIRMED; item 4 strict
all-below-margin = fixture-capability MISS).

Carrier lanes.  The frozen preregistration names exactly two lanes for the
confirmatory measurement: the DENSE oracle (prereg section 3; every headline
number is dense-computed) and the PLAIN lane, used only to measure
``err_cell`` for the margin rule (prereg section 2: "the plain-lane
trace-distance error measured on that cell against the dense oracle at the
same cap").  No GCAPEPS-fork carrier lane runs here (section 4: v2 makes no
truncation or carrier claim), and the l2bp/D compressor lane of the sibling
compression-ladder preregistration is NOT adopted by this preregistration
(adoption would need its own amendment).

Modes:
  --mode development   CALIBRATION cells only; dry runs; nothing here is a
                       registered result and every payload says so.  This
                       mode structurally cannot build a HELDOUT fixture.
  --mode registered    enforces every amendment gate, refuses dirty
                       load-bearing surfaces and a dirty fork, and is the
                       only path to HELDOUT cells.  The six-cell
                       confirmatory frame is FROZEN by amendment 2 item 1
                       (see below); with amendment 2 landed, exactly ONE
                       gate remains before the first heldout build: the
                       owner-release token (``--owner-release-token``).  No
                       token has been minted yet -- the owner mints it at
                       release time and freezes its SHA-256 in
                       ``OWNER_RELEASE_TOKEN_SHA256`` below -- so registered
                       execution currently refuses at that gate and nowhere
                       else.

Preconditions (all printed, all fatal on failure):
  * interpreter: the canonical ``ecs`` environment (numpy + stim); the
    plain-lane children run under the fork pixi interpreter
    (``external/forks/quimb-gcapeps/.pixi/envs/testpymid/bin/python``),
    the only build carrying quimb's ``CircuitPEPSSimpleUpdate`` path;
  * no scientific module is imported before the thread envelope is set;
  * the preregistration file exists, hashes, and carries BOTH pre-run
    amendment headings (a stale pre-amendment copy is refused);
  * registered mode: clean load-bearing main-repository surfaces, clean
    fork tree, and a Stage-0 evidence file whose MEASURED worst-pair
    one-minus-fidelity is <= 1e-4 (amendment 1 item 5);
  * every fixture built in development mode is CALIBRATION; the HELDOUT
    seeds appear below only as frozen configuration.

AMBIGUITY RULINGS.  The build-report ambiguities FA-1..FA-8 that earlier
revisions of this harness flagged were owner-decided on 2026-08-01 as
pre-run amendment 2; this harness now ENFORCES those rulings rather than
flagging them:

  FA-1  RULED by amendment 2 item 1.  The confirmatory cells are exactly
        heldout seeds {hv2-0, hv2-1} (the FIRST TWO seeds of the existing
        v2 heldout derivation stream) x gamma-index {1, 2, 3} x w7 r10 x
        the X8 arm, each cell carrying the registered input pair
        internally: six cells, structurally congruent to the six
        development screening cells (``FROZEN_CONFIRMATORY_CELLS``).
        NOTHING from either heldout seed may be built before the owner's
        release of the confirmatory run (the owner-release token gate).
  FA-2  RULED by amendment 2 item 2 (X5-theta0 vehicle by equivalence).
        At theta = 0 every rotation is the identity and thinning acts only
        on rotations, so the X5-variant theta=0 Clifford stream equals the
        CX-only arm's stream operation-for-operation.  The mandatory
        X5-theta0 anchor arm is REALIZED AS the landed cx-only-arm emitter
        at theta=0 on the REGISTERED path; the harness verifies and prints
        the op-for-op equivalence at run time (reconstructing the X5-theta0
        stream from the thin-only arm's Clifford stream plus the frozen
        every-round cross-row CX and comparing operation lists exactly).
  FA-3  RULED by amendment 2 item 4.  Both err_cell operational
        definitions -- max_r |D_r^plain - D_r^dense| and the state-level
        max reduced trace distance over checkpoints and inputs -- are
        computed and recorded; the run REFUSES if they ever classify a
        cell differently under the 10x-margin rule.
  FA-4  RULED by amendment 2 item 5.  The CX-only and thin-only arms run
        on the same six coordinates as P2 controls; they are never
        additional confirmatory cells and never carry witness adjudication
        weight outside P2.
  FA-5  RULED by amendment 2 item 3.  (i) The "untruncated run F = 1"
        control is retained and wired to the plain engine's explicit
        uncapped-bond override (``execute_plain(...,
        untruncated_control=True)``), reachable ONLY from this harness's
        control lane; the control's semantics are unchanged.  (ii) The
        "LOCAL-alphabet F = 1" inherited row is AMENDED DOWN with
        justification: no implementation exists anywhere in the
        repository, rebuilding one is new mechanism code carrying its own
        validation debt, and the remaining controls (untruncated F=1;
        theta0-plus-no-CX constancy with firing corruption trip; the dual
        theta0 gates; the section 3b controls) cover the
        pipeline-integrity surface it addressed.  Its removal is a
        disclosed weakening, not a silent one.
  FA-6  RULED by amendment 2 item 6.  "Minority" for the thin-only
        sub-claim is the complement of the >= 4/6 majority rule: <= 2/6 is
        a minority PASS; exactly 3/6 scores NOT-CONFIRMED (mirrors
        amendment 1 item 2).
  FA-7  RULED by amendment 2 item 7.  P1 is read conjunctively per cell
        (guard AND magnitude band AND location band simultaneously); the
        three components are additionally reported separately for audit.
  FA-8  RULED by amendment 2 item 8.  The section 3b inert-checkpoint
        control's numeric cross-check (+7.227e-4 at r8->r9) binds on the
        development cell only; on confirmatory cells the control's value
        is recorded and any deviation is a reported finding, not an
        automatic refusal (the refusal surfaces remain the frozen gates).

Reporting rules carried from amendment 1 items 6, 7, and 9: X5-measured
numbers are cited only as X5's (re-affirmed by amendment 2 item 2);
rotation counts are cited as rotations, not events; no
PEPS/2D-representational-content claim rides on this fixture (the v2
geometry remains exactly-MPS under rung fusion).

Run (development dry run, CALIBRATION only):
  conda run -n ecs python \
      scripts/external_baselines/run_gcapeps_v2_confirmatory.py \
      --mode development --cell s2-g2-r10 --plain-lane off
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

REPO = Path(__file__).resolve().parents[2]
FORK = REPO / "external/forks/quimb-gcapeps"
# The plain lane's CircuitPEPSSimpleUpdate path exists only on the fork's
# quimb build (ecs quimb has neither quimb.tensor.circuit.gates nor
# CircuitPEPSSimpleUpdate), so plain-lane children run under the fork pixi
# interpreter -- the same interpreter the registered ladder runner uses.
FORK_PYTHON = FORK / ".pixi/envs/testpymid/bin/python"
PREREG_RELATIVE = (
    "docs/simulator_validation/"
    "GCAPEPS_FINITE_MEMORY_FIXTURE_V2_X8_PREREG_2026-08-01.md"
)
PREREG = REPO / PREREG_RELATIVE
AMENDMENT_HEADING = "## Pre-run amendment 1 (2026-08-01)"
AMENDMENT_2_HEADING = "## Pre-run amendment 2 (2026-08-01)"
RUNNER_RELATIVE = "scripts/external_baselines/run_gcapeps_v2_confirmatory.py"

SCHEMA = (
    "error_coupling_simulator.external."
    "gcapeps_finite_memory.fixture_v2_confirmatory.v1"
)

DEVELOPMENT_LABEL = (
    "DEVELOPMENT dry run on CALIBRATION cells only; nonclaim-bearing; "
    "no registered standing"
)
REGISTERED_LABEL = (
    "REGISTERED fixture-v2 confirmatory cell; headline PROVISIONAL until "
    "the full frozen frame reports"
)

# ---------------------------------------------------------------------
# frozen metric and adjudication constants (prereg sections 2/2a/2b +
# amendment items 2, 4, 5; v1-ledgered BLP objects)
# ---------------------------------------------------------------------
GUARD = 1.0e-10  # v1-registered numerical guard for the BLP objects
MARGIN_FACTOR = 10.0  # two-sided margin: WITNESS needs > 10 x err_cell
ANCHOR_TOL = 1.0e-12  # theta=0 Stim-vs-dense agreement (prereg section 3)
P3_FLAT_TOL = 1.0e-12  # P3: every X8-theta0 increment below 1e-12
CAP = 32
CELL_COUNT = 6  # P1/P2/items 2 and 4 adjudicate exactly six cells
MAJORITY_MIN = 4  # amendment item 2: majority means >= 4 of 6
TIE_COUNT = 3  # amendment item 2: exactly 3/6 scores NOT-CONFIRMED
P1_MAGNITUDE_BAND = (1.0e-3, 1.0e-1)
P1_LOCATION_ROUNDS = (1, 5)  # location within rounds 1..5
STAGE0_WORST_PAIR_MAX = 1.0e-4  # amendment item 5 refusal threshold
STAGE0_SCHEMA = (
    "error_coupling_simulator.external.gcapeps_finite_memory."
    "native_thread_regression.v1"
)
STAGE0_BAND_SET = "stage0_amended_trim_cluster"
STAGE0_PASS_VERDICT = "PASS_ENGINEERING_NATIVE_THREAD_REGRESSION"
STAGE0_EXPECTED_PAIRS = (
    "native_threads1_vs_threads2",
    "native_threads1_vs_threads4",
    "native_threads1_vs_threads8",
    "native_threads2_vs_threads4",
    "native_threads2_vs_threads8",
    "native_threads4_vs_threads8",
)

VERDICT_WITNESS = "WITNESS"
VERDICT_BELOW_MARGIN = "WITNESS_BELOW_MARGIN"
VERDICT_NO_WITNESS = "NO_WITNESS_FIXED_MASK_FOR_REGISTERED_PAIR"
VERDICT_CAPABILITY_MISS = (
    "FIXTURE_CAPABILITY_MISS_AT_CURRENT_CARRIER_ERROR_FLOORS"
)

# Amendment 2 item 3(i): the inherited "untruncated run F = 1" control,
# wired to the plain engine's explicit uncapped-bond override.  Fidelity is
# the v1-ledgered normalized squared overlap with the independent dense
# state for the same input trajectory; the pass band reuses the v1 1e-10
# numerical decision band (bond32 prereg H_F).
UNTRUNCATED_ONE_MINUS_F_MAX = 1.0e-10

# Arm registry: schema-dispatched emitters (arm -> sibling emitter module,
# expected fixture schema).  The X5 theta=0 arm is intentionally absent
# from this table: amendment 2 item 2 REALIZES it as the cx_only arm at
# theta=0 (exact operation-for-operation equivalence, verified at run
# time); no separate X5 emitter exists, by design.
ARM_EMITTERS = {
    "X8": (
        "emit_gcapeps_finite_memory_fixture_v2",
        "error_coupling_simulator.external.gcapeps_finite_memory.fixture.v2",
    ),
    "cx_only": (
        "emit_gcapeps_finite_memory_cx_only_arm",
        "error_coupling_simulator.external.gcapeps_finite_memory."
        "fixture_cx_only_arm.v1",
    ),
    "thin_only": (
        "emit_gcapeps_finite_memory_thin_only_arm",
        "error_coupling_simulator.external.gcapeps_finite_memory."
        "fixture_thin_only_arm.v1",
    ),
}
P2_CONTROL_ARMS = ("cx_only", "thin_only")

# Amendment 1 item 3: the confirmatory harness runs BOTH theta=0 gates.
THETA0_REQUIRED_GATES = ("d_trajectory", "inner_product_ag")

# ---------------------------------------------------------------------
# frozen confirmatory cell frame (amendment 2 item 1).  The HELDOUT seed
# values appear here only as frozen configuration; this module never
# builds a HELDOUT fixture until the owner-release token gate passes.
# ---------------------------------------------------------------------
_HELDOUT_SEED_DIGEST = hashlib.sha256(
    b"gcapeps-finite-memory-heldout-v2"
).digest()
# The first two seeds of the existing v2 heldout derivation stream: the
# namespace digest read as consecutive big-endian 8-byte windows (hv2-0 is
# byte-identical to the original single-seed derivation).
V2_HELDOUT_SEEDS = tuple(
    int.from_bytes(_HELDOUT_SEED_DIGEST[8 * index : 8 * (index + 1)], "big")
    for index in range(2)
)
V2_HELDOUT_SEED = V2_HELDOUT_SEEDS[0]  # hv2-0
HELDOUT_SEED_LABELS = {
    V2_HELDOUT_SEEDS[0]: "hv2-0",
    V2_HELDOUT_SEEDS[1]: "hv2-1",
}
FROZEN_CONFIRMATORY_CONSTRAINTS = {
    "run_partition": "HELDOUT",
    "seeds": V2_HELDOUT_SEEDS,  # amendment 2 item 1: hv2-0 and hv2-1
    "witness_arm": "X8",
    "inputs": (1, 2),  # the registered pair; both are consumed per cell
    "mandatory_anchor_arm": (
        "x5_variant_theta0 (realized as cx_only at theta=0; "
        "amendment 2 item 2)"
    ),
}
# The exact six confirmatory cells (amendment 2 item 1): heldout seeds
# {hv2-0, hv2-1} x gamma-index {1, 2, 3} x w7 r10 x the X8 arm, each cell
# consuming the registered input pair internally; structurally congruent
# to the six development screening cells.
FROZEN_CONFIRMATORY_CELLS = tuple(
    {
        "seed": seed,
        "gamma_index": gamma_index,
        "rounds": 10,
        "width": 7,
        "axis_family": 3,
        "p_event_numerator": 3,
        "run_partition": "HELDOUT",
    }
    for seed in V2_HELDOUT_SEEDS
    for gamma_index in (1, 2, 3)
)

# The ONE remaining registered gate: the owner's release of the first
# heldout build.  No token has been minted yet; at release time the owner
# mints a token out-of-band and freezes its SHA-256 hex digest here.
OWNER_RELEASE_TOKEN_SHA256 = None

THREAD_VARIABLES = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "BLIS_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "OMP_THREAD_LIMIT",
    "NUMBA_NUM_THREADS",
    "QUIMB_NUM_THREAD_WORKERS",
)

# Main-repository surfaces whose dirtiness invalidates a registered stamp
# (same set as the registered compression-ladder runner).
LOAD_BEARING_PREFIXES = (
    "scripts/external_baselines/",
    "docs/simulator_validation/",
)


class Refusal(RuntimeError):
    """A preregistration gate refused execution."""


def _set_thread_envelope() -> None:
    for name in THREAD_VARIABLES:
        os.environ[name] = "1"
    for name in ("QUIMB_NUM_PROCS", "QUIMB_NUM_MPI_WORKERS"):
        os.environ[name] = "1"
    for name in ("OMP_DYNAMIC", "MKL_DYNAMIC"):
        os.environ[name] = "FALSE"
    os.environ["QUIMB_NUMBA_CACHE"] = "False"
    os.environ["QUIMB_MPI_SPAWN"] = "False"
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    os.environ["PYTHONHASHSEED"] = "0"
    os.environ.pop("PYTHONPATH", None)
    loaded = sorted(
        name
        for name in sys.modules
        if name.split(".", 1)[0] in {"numpy", "quimb", "stim", "scipy"}
    )
    if loaded:
        raise RuntimeError(
            "scientific modules loaded early: " + ",".join(loaded)
        )


def _load_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(
        name, path.resolve(strict=True)
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_sibling(name: str):
    return _load_path(
        f"_gcapeps_v2_confirmatory_{name}",
        Path(__file__).resolve(strict=True).with_name(f"{name}.py"),
    )


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


# ======================================================================
# provenance stamps (registered-runner pattern)
# ======================================================================


def collect_provenance_stamps(mode: str) -> dict:
    """Collect the frozen stamp set; refuse invalid provenance outright."""

    prereg_bytes = PREREG.read_bytes()
    if AMENDMENT_HEADING.encode("utf-8") not in prereg_bytes:
        raise Refusal(
            "the preregistration file does not carry the pre-run "
            f"amendment-1 heading {AMENDMENT_HEADING!r}; a stale copy "
            "cannot govern a confirmatory run"
        )
    if AMENDMENT_2_HEADING.encode("utf-8") not in prereg_bytes:
        raise Refusal(
            "the preregistration file does not carry the pre-run "
            f"amendment-2 heading {AMENDMENT_2_HEADING!r}; a stale copy "
            "cannot govern a confirmatory run (this harness enforces the "
            "amendment-2 rulings)"
        )

    main_head = _run_git(REPO, "rev-parse", "HEAD")
    main_status = _run_git(
        REPO, "status", "--porcelain", "--untracked-files=all"
    )
    load_bearing_dirty = [
        line
        for line in main_status.splitlines()
        if line[3:].startswith(LOAD_BEARING_PREFIXES)
    ]
    if mode == "registered" and load_bearing_dirty:
        raise Refusal(
            "registered mode refuses a dirty load-bearing main-repository "
            "surface (the HEAD stamp would not describe the executed "
            "code):\n" + "\n".join(load_bearing_dirty)
        )

    fork_commit = None
    fork_status_clean = None
    if FORK.exists():
        fork_status = _run_git(
            FORK, "status", "--porcelain", "--untracked-files=all"
        )
        fork_status_clean = not fork_status
        if mode == "registered" and fork_status:
            raise Refusal(
                "registered mode refuses a dirty fork tree:\n" + fork_status
            )
        fork_commit = _run_git(FORK, "rev-parse", "HEAD")
    elif mode == "registered":
        raise Refusal(
            "registered mode requires the fork checkout to exist for the "
            "provenance stamp"
        )

    runner_path = Path(__file__).resolve(strict=True)
    loaded_sources = {}
    for name in (
        "emit_gcapeps_finite_memory_fixture",
        "emit_gcapeps_finite_memory_fixture_v2",
        "emit_gcapeps_finite_memory_cx_only_arm",
        "emit_gcapeps_finite_memory_thin_only_arm",
        "gcapeps_finite_memory_dense_reference",
        "gcapeps_finite_memory_worker_common",
        "plain_quimb_finite_memory_worker_common",
        "plain_quimb_finite_memory_engine",
        "run_gcapeps_native_thread_regression",
    ):
        sibling = runner_path.with_name(f"{name}.py")
        if sibling.exists():
            loaded_sources[name] = _sha256_file(sibling)

    return {
        "main_repository_head_commit": main_head,
        "main_repository_load_bearing_dirty": load_bearing_dirty,
        "fork_commit": fork_commit,
        "fork_status_clean": fork_status_clean,
        "preregistration_path": PREREG_RELATIVE,
        "preregistration_sha256": hashlib.sha256(prereg_bytes).hexdigest(),
        "preregistration_carries_amendment_1": True,
        "preregistration_carries_amendment_2": True,
        "runner_path": RUNNER_RELATIVE,
        "runner_source_sha256": _sha256_file(runner_path),
        "interpreter_version": sys.version,
        "interpreter_executable": str(Path(sys.executable).resolve()),
        "loaded_source_sha256": loaded_sources,
        "collected_utc": datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat(),
    }


# ======================================================================
# Stage-0 measured worst-pair gate (amendment item 5)
# ======================================================================


def stage0_gate(evidence_path: Path) -> dict:
    """Re-record the MEASURED Stage-0 worst-pair value; refuse above 1e-4.

    Amendment item 5: the R0 row's criterion (thread variance <= 1e-4 in
    the witness metric) is met by the MEASURED value, not by the 6.1e-4
    band, so the confirmatory run must re-record the measured worst-pair
    one-minus-fidelity from its own Stage-0 evidence and refuse if it
    exceeds 1e-4.
    """

    try:
        report = json.loads(evidence_path.read_text())
    except (OSError, ValueError) as error:
        raise Refusal(
            f"Stage-0 evidence is unreadable ({evidence_path}): {error}"
        ) from error
    if report.get("schema") != STAGE0_SCHEMA:
        raise Refusal(
            "Stage-0 evidence schema mismatch: "
            f"{report.get('schema')!r} != {STAGE0_SCHEMA!r}"
        )
    applied = report.get("applied_bands")
    if not isinstance(applied, dict) or applied.get("band_set") != (
        STAGE0_BAND_SET
    ):
        raise Refusal(
            "Stage-0 evidence is not the amended trim_cluster lane "
            "(amendment item 5 discharges R0 through commit edb8ae8's "
            "amended acceptance)"
        )
    if report.get("verdict") != STAGE0_PASS_VERDICT:
        raise Refusal(
            f"Stage-0 evidence verdict is {report.get('verdict')!r}, "
            f"not {STAGE0_PASS_VERDICT!r}"
        )
    invariance = report.get("thread_invariance")
    pairs = invariance.get("pairs") if isinstance(invariance, dict) else None
    if not isinstance(pairs, dict) or sorted(pairs) != sorted(
        STAGE0_EXPECTED_PAIRS
    ):
        raise Refusal(
            "Stage-0 evidence does not carry exactly the six amended "
            "thread pairs"
        )
    worst_pair_value = None
    worst_pair_name = None
    for pair_name, pair_row in pairs.items():
        checkpoints = pair_row.get("checkpoints")
        if not isinstance(checkpoints, dict) or not checkpoints:
            raise Refusal(
                f"Stage-0 pair {pair_name} carries no checkpoints"
            )
        for checkpoint_row in checkpoints.values():
            try:
                value = checkpoint_row["raw_metrics"]["metrics"][
                    "one_minus_fidelity"
                ]
            except (KeyError, TypeError) as error:
                raise Refusal(
                    f"Stage-0 pair {pair_name} is missing the measured "
                    "one-minus-fidelity"
                ) from error
            value = float(value)
            if not math.isfinite(value) or value < 0.0:
                raise Refusal(
                    f"Stage-0 pair {pair_name} carries an invalid "
                    f"one-minus-fidelity {value!r}"
                )
            if worst_pair_value is None or value > worst_pair_value:
                worst_pair_value = value
                worst_pair_name = pair_name
    if worst_pair_value is None:
        raise Refusal("Stage-0 evidence carries no measured pair values")
    record = {
        "evidence_path": str(evidence_path),
        "evidence_sha256": _sha256_file(evidence_path),
        "stage0_verdict": report["verdict"],
        "stage0_band_set": STAGE0_BAND_SET,
        "stage0_result_projection_sha256": report.get(
            "result_projection_sha256"
        ),
        "stage0_fixture_identity": report.get("fixture_identity"),
        "measured_worst_pair_one_minus_fidelity": worst_pair_value,
        "measured_worst_pair_name": worst_pair_name,
        "threshold": STAGE0_WORST_PAIR_MAX,
        "criterion": (
            "amendment item 5: measured worst-pair value, not the band"
        ),
    }
    if worst_pair_value > STAGE0_WORST_PAIR_MAX:
        raise Refusal(
            "Stage-0 measured worst-pair one-minus-fidelity "
            f"{worst_pair_value:.6e} exceeds the amendment-item-5 "
            f"threshold {STAGE0_WORST_PAIR_MAX:g}; the run is refused"
        )
    return record


# ======================================================================
# cell frame (amendment 2 item 1: frozen six-cell list) + owner release
# ======================================================================


def parse_cell(text: str) -> dict:
    """Parse ``s<seed>-g<gamma>-r<rounds>`` or ``hv2-<k>-g<gamma>-r<rounds>``.

    The ``hv2-<k>`` form names the k-th frozen heldout stream seed
    (amendment 2 item 1) without spelling out its 20-digit value.
    """

    match = re.fullmatch(r"(?:s(\d+)|hv2-(\d+))-g(\d+)-r(\d+)", text)
    if match is None:
        raise argparse.ArgumentTypeError(
            "cell must look like s2-g2-r10 or hv2-0-g1-r10 "
            "(seed / gamma-index / rounds)"
        )
    if match.group(2) is not None:
        stream_index = int(match.group(2))
        if stream_index >= len(V2_HELDOUT_SEEDS):
            raise argparse.ArgumentTypeError(
                "only hv2-0 and hv2-1 are admitted heldout stream seeds "
                "(amendment 2 item 1)"
            )
        seed = V2_HELDOUT_SEEDS[stream_index]
    else:
        seed = int(match.group(1))
    return {
        "seed": seed,
        "gamma_index": int(match.group(3)),
        "rounds": int(match.group(4)),
    }


def cell_label(cell: dict) -> str:
    """Human-stable cell id; heldout seeds print as hv2-<k>, never digits."""

    seed_label = HELDOUT_SEED_LABELS.get(cell["seed"], f"s{cell['seed']}")
    return f"{seed_label}-g{cell['gamma_index']}-r{cell['rounds']}"


def _frame_key(cell: dict) -> tuple:
    return (cell["seed"], cell["gamma_index"], cell["rounds"])


def resolve_cells(mode: str, requested: list) -> list:
    """Resolve the cells this mode may execute; refuse everything else.

    Development: CALIBRATION grid cells only (the emitters enforce the
    frozen calibration identity: w7, rounds in the calibration set, axis
    family 3, p 3/4, seeds 0..3).  A request naming EITHER HELDOUT seed is
    refused outright: development mode must be structurally unable to
    build a HELDOUT fixture.

    Registered: the six-cell confirmatory frame is FROZEN by amendment 2
    item 1 (``FROZEN_CONFIRMATORY_CELLS``).  With no ``--cell`` request the
    frozen frame is resolved verbatim; an explicit request must match the
    frozen frame exactly (any other cell is refused).  Resolution builds
    nothing: every heldout build stays behind the owner-release token gate.
    """

    if mode == "development":
        if not requested:
            raise Refusal("no cells requested; pass --cell at least once")
        for cell in requested:
            if cell["seed"] in V2_HELDOUT_SEEDS:
                raise Refusal(
                    "development mode refuses the v2 HELDOUT seeds "
                    "(hv2-0, hv2-1); dry runs are CALIBRATION-only"
                )
            if cell["seed"] not in range(4):
                raise Refusal(
                    "development cells use the frozen CALIBRATION seeds "
                    f"0..3; got seed {cell['seed']}"
                )
        return [
            {**cell, "run_partition": "CALIBRATION"} for cell in requested
        ]
    # registered mode: the frame is frozen, not caller-chosen.
    frame = [dict(cell) for cell in FROZEN_CONFIRMATORY_CELLS]
    if not requested:
        return frame
    for cell in requested:
        if cell["seed"] not in V2_HELDOUT_SEEDS:
            raise Refusal(
                "registered mode accepts only the two frozen v2 heldout "
                "seeds hv2-0 and hv2-1 (amendment 2 item 1; emitter "
                f"heldout-namespace guard); got seed {cell['seed']}"
            )
    requested_keys = sorted(_frame_key(cell) for cell in requested)
    frame_keys = sorted(_frame_key(cell) for cell in frame)
    if requested_keys != frame_keys:
        raise Refusal(
            "registered mode runs exactly the frozen six-cell confirmatory "
            "frame {hv2-0, hv2-1} x gamma{1,2,3} x w7 r10 x X8 "
            "(amendment 2 item 1); the requested cell list differs from "
            "it.  Omit --cell to run the frozen frame verbatim."
        )
    return frame


def enforce_owner_release(mode: str, token: str | None) -> dict:
    """The ONE remaining registered gate: owner release of the first
    heldout build (amendment 2 item 1: "NOTHING from either heldout seed
    may be built before the owner's release of the confirmatory run")."""

    if mode != "registered":
        if token is not None:
            raise Refusal(
                "--owner-release-token is meaningful in registered mode "
                "only; development dry runs never touch heldout builds"
            )
        return {"status": "NOT_APPLICABLE_IN_DEVELOPMENT"}
    if token is None:
        raise Refusal(
            "OWNER-RELEASE GATE: every other registered gate is wired and "
            "the six-cell confirmatory frame is frozen (amendment 2 "
            "item 1); the ONE remaining gate before the first heldout "
            "build is the owner's release.  Pass --owner-release-token "
            "<token>.  No token has been minted yet -- the owner mints it "
            "at release time and freezes its SHA-256 as "
            "OWNER_RELEASE_TOKEN_SHA256 in this runner."
        )
    if OWNER_RELEASE_TOKEN_SHA256 is None:
        raise Refusal(
            "OWNER-RELEASE GATE: an --owner-release-token was supplied, "
            "but no owner-release token has been minted "
            "(OWNER_RELEASE_TOKEN_SHA256 is unset); the first heldout "
            "build stays refused until the owner mints the token at "
            "release time"
        )
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    if digest != OWNER_RELEASE_TOKEN_SHA256:
        raise Refusal(
            "OWNER-RELEASE GATE: the supplied token does not match the "
            "owner-minted release token"
        )
    return {
        "status": "RELEASED",
        "token_sha256": digest,
    }


# ======================================================================
# fixture building (arm schema routing)
# ======================================================================


def fixture_for_arm(arm: str, cell: dict) -> tuple[dict, str, str]:
    """Build and validate one arm fixture; return (fixture, hash, schema).

    The fixture is validated twice: by its owning emitter (deterministic
    reconstruction) and -- for schemas the worker-common dispatch table
    supports -- through the schema-dispatched ``validate_fixture`` used by
    the production lanes.  Both hashes must agree.
    """

    row = ARM_EMITTERS.get(arm)
    if row is None:
        raise Refusal(
            f"unknown arm {arm!r}; the registered arms are "
            f"{sorted(ARM_EMITTERS)} (the X5-variant theta=0 arm has no "
            "committed emitter surface; FA-2)"
        )
    emitter_name, expected_schema = row
    emitter = _load_sibling(emitter_name)
    try:
        fixture = emitter.build_fixture(
            run_partition=cell["run_partition"],
            width=cell.get("width", 7),
            rounds=cell["rounds"],
            axis_family=cell.get("axis_family", 3),
            p_event_numerator=cell.get("p_event_numerator", 3),
            seed=cell["seed"],
            gamma_index=cell["gamma_index"],
            run_blpensemble=False,
        )
    except (TypeError, ValueError) as error:
        raise Refusal(
            f"arm {arm}: the emitter refused the requested cell "
            f"(outside the frozen grid): {error}"
        ) from error
    if fixture["schema"] != expected_schema:
        raise Refusal(
            f"arm {arm} produced schema {fixture['schema']!r}, expected "
            f"{expected_schema!r}"
        )
    fixture_hash = emitter.validate_fixture(fixture)
    worker_common = _load_sibling("gcapeps_finite_memory_worker_common")
    try:
        dispatched_hash = worker_common.validate_fixture(fixture)
    except ValueError:
        if arm == "X8":
            raise
        dispatched_hash = None  # arm schemas are not production-dispatched
    if dispatched_hash is not None and dispatched_hash != fixture_hash:
        raise Refusal(
            f"arm {arm}: emitter and dispatched fixture hashes disagree"
        )
    return fixture, fixture_hash, expected_schema


# ======================================================================
# dense oracle (prereg section 3; ladder-runner lineage)
# ======================================================================


class DenseOracle:
    """Numpy+stdlib exact evolution over a fixture's round ledger."""

    def __init__(self):
        import numpy as np

        self.np = np
        self.dense_ref = _load_sibling("gcapeps_finite_memory_dense_reference")
        audit = self.dense_ref.audit_import_independence()
        if not audit["passed"]:
            raise Refusal(
                "dense-reference import-independence audit failed; the "
                "oracle firewall is not intact"
            )

    def initial_state(self, fixture: dict, input_id: int):
        np = self.np
        n_qubits = fixture["geometry"]["n_qubits"]
        row = next(
            r for r in fixture["inputs"] if r["input_id"] == input_id
        )
        bits = row["dense_plain_initial_bits"]
        index = sum(
            int(bit) << (n_qubits - 1 - qubit)
            for qubit, bit in enumerate(bits)
        )
        state = np.zeros(1 << n_qubits, dtype=np.complex128)
        state[index] = 1.0
        return state

    def round_states(
        self, fixture: dict, input_id: int, *, theta_zero: bool = False,
        clifford_layer_max: int | None = None,
        corrupt_theta_zero_off: bool = False,
    ) -> dict:
        """States at round boundaries r=0..R.

        ``theta_zero`` skips every collision rotation;
        ``clifford_layer_max`` keeps only Clifford layers <= the bound
        (used for the inherited-stream no-CX control);
        ``corrupt_theta_zero_off`` silently breaks the theta_zero flag,
        re-applying every collision rotation at its true theta -- the
        harness-chosen corruption vehicle of the theta0-plus-no-CX control
        re-trip (FA-5).  A single restored rotation is NOT used: it
        provably leaves the reduced branches orthogonal (D stays exactly
        1), which this harness's own dry run demonstrated.
        """

        dense_ref = self.dense_ref
        n_qubits = fixture["geometry"]["n_qubits"]
        state = self.initial_state(fixture, input_id)
        states = {0: state.copy()}
        for round_row in fixture["carrier_path"]["round_ledger"]:
            for operation in round_row["operations"]:
                if operation["operation_class"] == "collision_rotation":
                    if theta_zero and not corrupt_theta_zero_off:
                        continue
                    matrix = dense_ref.pauli_rotation_matrix(
                        operation["axis"],
                        float.fromhex(operation["theta_float64_hex"]),
                    )
                else:
                    if (
                        clifford_layer_max is not None
                        and operation["layer_index"] > clifford_layer_max
                    ):
                        continue
                    if operation["gate_kind"] == "CX":
                        matrix = dense_ref.cx_matrix()
                    else:
                        matrix = dense_ref.one_qubit_matrix(
                            operation["gate_kind"]
                        )
                state = dense_ref.apply_gate_q0_msb(
                    state,
                    matrix,
                    operation["targets"],
                    num_qubits=n_qubits,
                )
            states[round_row["round_index"]] = state.copy()
        return states

    def system_rho(self, state, *, width: int):
        np = self.np
        amplitude = state.reshape(1 << width, 1 << width)
        norm_sq = float(np.real(np.vdot(state, state)))
        if norm_sq <= 0.0:
            raise ValueError("state has nonpositive norm")
        return np.ascontiguousarray(
            amplitude @ amplitude.conj().T / norm_sq, dtype=np.complex128
        )

    def trace_distance(self, rho_1, rho_2) -> float:
        return float(
            self.dense_ref.trace_distance(rho_1, rho_2)["value"]
        )

    def blp_trajectory(self, states_1: dict, states_2: dict, *, width: int):
        if sorted(states_1) != sorted(states_2):
            raise ValueError("branch checkpoints disagree")
        distances = []
        for round_index in sorted(states_1):
            distances.append(
                self.trace_distance(
                    self.system_rho(states_1[round_index], width=width),
                    self.system_rho(states_2[round_index], width=width),
                )
            )
        return distances


def blp_objects(distances: list) -> dict:
    """The v1-ledgered fixed-pair BLP objects for one D trajectory."""

    increments = [
        distances[index] - distances[index - 1]
        for index in range(1, len(distances))
    ]
    positive_sum = float(sum(max(0.0, value) for value in increments))
    if increments:
        best = max(range(len(increments)), key=lambda i: increments[i])
        delta_max = float(increments[best])
        location = f"r{best}->r{best + 1}"
        location_round = best + 1
    else:
        delta_max = float("-inf")
        location = None
        location_round = None
    return {
        "distances": [float(value) for value in distances],
        "increments": [float(value) for value in increments],
        "positive_increment_sum_w": positive_sum,
        "max_increment": delta_max,
        "max_increment_location": location,
        "max_increment_arrival_round": location_round,
        "positive_above_guard": bool(delta_max > GUARD),
        "guard": GUARD,
    }


# ======================================================================
# GF(2) frame instruments (P4 + section 3b degeneracy detector)
# ======================================================================


def _gate_symplectic(np, kind: str, targets, n: int):
    """GF(2) conjugation matrix G with v(U P U^dag) = G v(P)."""

    g = np.eye(2 * n, dtype=np.uint8)
    if kind == "H":
        (q,) = targets
        g[[q, n + q]] = g[[n + q, q]]
    elif kind == "S":
        (q,) = targets
        g[n + q, q] = 1
    elif kind == "X":
        (q,) = targets  # letters-only: X acts trivially on GF(2) vectors
    elif kind == "CX":
        control, target = targets
        g[target, control] = 1
        g[n + control, n + target] = 1
    else:
        raise ValueError(f"unsupported Clifford kind {kind!r}")
    return g


def gf2_rank(np, matrix) -> int:
    m = matrix.copy() % 2
    rank = 0
    n_rows, n_cols = m.shape
    for col in range(n_cols):
        pivot = next((r for r in range(rank, n_rows) if m[r, col]), None)
        if pivot is None:
            continue
        m[[rank, pivot]] = m[[pivot, rank]]
        for r in range(n_rows):
            if r != rank and m[r, col]:
                m[r] ^= m[rank]
        rank += 1
    return rank


def frame_instruments(np, fixture: dict) -> dict:
    """g_C per round and pullback weights over the fixture's own ledger.

    Productionized from the adversarially verified screening instruments
    (SymplecticTableau / tableau_instruments); exact GF(2) arithmetic.
    """

    width = fixture["parameters"]["width"]
    n = fixture["geometry"]["n_qubits"]
    forward = np.eye(2 * n, dtype=np.uint8)
    inverse = np.eye(2 * n, dtype=np.uint8)
    g_c_per_round = []
    coupled_rounds = []
    pullback_weights = []

    def pauli_vector(body: str):
        vector = np.zeros(2 * n, dtype=np.uint8)
        for qubit, letter in enumerate(body):
            if letter in ("X", "Y"):
                vector[qubit] = 1
            if letter in ("Z", "Y"):
                vector[n + qubit] = 1
            if letter not in ("I", "X", "Y", "Z"):
                raise ValueError(body)
        return vector

    for round_row in fixture["carrier_path"]["round_ledger"]:
        crossing = False
        for operation in round_row["operations"]:
            if operation["operation_class"] == "clifford":
                targets = operation["targets"]
                if len(targets) == 2 and (
                    (targets[0] < width) != (targets[1] < width)
                ):
                    crossing = True
                g = _gate_symplectic(
                    np, operation["gate_kind"], targets, n
                )
                forward = (g @ forward) % 2
                inverse = (inverse @ g) % 2
            else:
                pulled = (
                    inverse @ pauli_vector(operation["physical_pauli_body"])
                ) % 2
                support = pulled[:n] | pulled[n:]
                pullback_weights.append(int(support.sum()))
        if crossing:
            coupled_rounds.append(round_row["round_index"])
        rows = []
        for site in range(width):
            for column in (site, n + site):
                image = forward[:, column]
                support = image[:n] | image[n:]
                rows.append(
                    [int(support[m]) for m in range(width, 2 * width)]
                )
        g_c_per_round.append(gf2_rank(np, np.array(rows, dtype=np.uint8)))

    mean_weight = (
        float(sum(pullback_weights)) / float(len(pullback_weights))
        if pullback_weights
        else None
    )
    return {
        "g_c_per_round": g_c_per_round,
        "cx_coupled_rounds": coupled_rounds,
        "pullback_weights_per_rotation": pullback_weights,
        "pullback_rotation_count": len(pullback_weights),
        "mean_pulled_back_weight": mean_weight,
        "max_pulled_back_weight": (
            max(pullback_weights) if pullback_weights else None
        ),
        "degenerate_regime_mean_weight_2": bool(
            mean_weight is not None and abs(mean_weight - 2.0) <= 0.005
        ),
        "note": (
            "pullback weight is reported beside every witness number; "
            "mean weight ~= 2.00 flags an inert frame (prereg section 3b); "
            "counts are rotations, not events (amendment item 9 / M7)"
        ),
    }


def adjudicate_p4(instruments: dict) -> dict:
    """P4: g_C = 1 on every CX-coupled round, 0 before the first coupling."""

    g_c = instruments["g_c_per_round"]
    coupled = instruments["cx_coupled_rounds"]
    first_coupled = coupled[0] if coupled else None
    failures = []
    for position, value in enumerate(g_c, start=1):
        if position in coupled and value != 1:
            failures.append(
                f"round {position}: coupled but g_C = {value} != 1"
            )
        if first_coupled is not None and position < first_coupled and (
            value != 0
        ):
            failures.append(
                f"round {position}: before first coupling but g_C = {value}"
            )
    return {
        "prediction": "P4",
        "class": "a_exact",
        "g_c_per_round": g_c,
        "cx_coupled_rounds": coupled,
        "passed": not failures,
        "failures": failures,
    }


# ======================================================================
# theta=0 dual gates (amendment item 3; productionized from the T2
# corruption-trip instrument -- .scratch/gcapeps-fixture-v2/
# corruption_trips/run_corruption_trips.py -- not re-derived)
# ======================================================================


def clifford_schedule(fixture: dict) -> list:
    """Per-round ordered Clifford (kind, targets) rows from the ledger."""

    rounds = []
    for round_row in fixture["carrier_path"]["round_ledger"]:
        rounds.append(
            [
                (operation["gate_kind"], tuple(operation["targets"]))
                for operation in round_row["operations"]
                if operation["operation_class"] == "clifford"
            ]
        )
    return rounds


def stim_theta0_distances(schedule: list, *, width: int) -> list:
    """Stim/tableau route for the theta=0 reduced D(r); D in {0,1} exactly.

    Derivation (class (a), carried verbatim from the discharged T2
    instrument): at theta=0 both branches evolve under the same Clifford
    U_r, so psi_2(r) = P(r) psi_1(r) with P(r) = U_r X_c U_r^dag; the
    reduced theta=0 D(r) is 1 exactly when P(r)'s system part anticommutes
    with an element of the system-supported stabilizer subgroup, else 0.
    D depends only on Pauli letters, never on tableau signs -- which is
    why the inner-product gate below must run alongside this one.
    """

    import numpy as np
    import stim

    n_qubits = 2 * width
    system = tuple(range(width))
    memory = tuple(range(width, 2 * width))
    center = width // 2

    def gf2_system_supported_basis(stabilizers):
        rows = []
        for pauli in stabilizers:
            vector = np.zeros(4 * width, dtype=np.uint8)
            for column, qubit in enumerate(memory):
                letter = pauli[qubit]
                vector[column] = 1 if letter in (1, 2) else 0
                vector[width + column] = 1 if letter in (2, 3) else 0
            for column, qubit in enumerate(system):
                letter = pauli[qubit]
                vector[2 * width + column] = 1 if letter in (1, 2) else 0
                vector[3 * width + column] = 1 if letter in (2, 3) else 0
            rows.append(vector)
        matrix = np.array(rows, dtype=np.uint8)
        rank = 0
        n_rows, n_cols = matrix.shape
        for col in range(n_cols):
            pivot = next(
                (r for r in range(rank, n_rows) if matrix[r, col]), None
            )
            if pivot is None:
                continue
            matrix[[rank, pivot]] = matrix[[pivot, rank]]
            for r in range(n_rows):
                if r != rank and matrix[r, col]:
                    matrix[r] ^= matrix[rank]
            rank += 1
        basis = []
        for row in matrix:
            if not row.any() or row[: 2 * width].any():
                continue
            basis.append(
                np.concatenate(
                    [row[2 * width: 3 * width], row[3 * width:]]
                )
            )
        return basis

    def pauli_sys_vector(pauli):
        vector = np.zeros(2 * width, dtype=np.uint8)
        for column, qubit in enumerate(system):
            letter = pauli[qubit]
            vector[column] = 1 if letter in (1, 2) else 0
            vector[width + column] = 1 if letter in (2, 3) else 0
        return vector

    def anticommutes(a, b) -> bool:
        return (
            int(
                np.dot(a[:width], b[width:])
                + np.dot(a[width:], b[:width])
            )
            % 2
            == 1
        )

    simulator = stim.TableauSimulator()
    simulator.set_num_qubits(n_qubits)
    accumulated = stim.Circuit()

    def d_now() -> float:
        base = stim.PauliString(n_qubits)
        base[center] = "X"  # branch-2 preparation X on the central site
        conjugated = base.after(accumulated)
        p_sys = pauli_sys_vector(conjugated)
        basis = gf2_system_supported_basis(
            simulator.canonical_stabilizers()
        )
        return 1.0 if any(anticommutes(g, p_sys) for g in basis) else 0.0

    out = [d_now()]
    for round_ops in schedule:
        for kind, targets in round_ops:
            if kind == "H":
                (qubit,) = targets
                simulator.h(qubit)
                accumulated.append("H", [qubit])
            elif kind == "S":
                (qubit,) = targets
                simulator.s(qubit)
                accumulated.append("S", [qubit])
            elif kind == "X":
                (qubit,) = targets
                simulator.x(qubit)
                accumulated.append("X", [qubit])
            elif kind == "CX":
                left, right = targets
                simulator.cx(left, right)
                accumulated.append("CX", [left, right])
            else:
                raise ValueError(f"unsupported Clifford kind {kind!r}")
        out.append(d_now())
    return out


def stim_overlap(prep_a: list, prep_b: list, n_qubits: int) -> float:
    """|<0|C_a^dag C_b|0>| via tableau + sequential postselection.

    The Aaronson-Gottesman inner-product instrument
    (quant-ph/0406196v5, end of Sec. III), carried verbatim from the
    discharged T2 route.
    """

    import stim

    simulator = stim.TableauSimulator()
    simulator.set_num_qubits(n_qubits)

    def apply(kind, targets, inverse):
        if kind == "H":
            (qubit,) = targets
            simulator.h(qubit)
        elif kind == "S":
            (qubit,) = targets
            if inverse:
                simulator.s_dag(qubit)
            else:
                simulator.s(qubit)
        elif kind == "X":
            (qubit,) = targets
            simulator.x(qubit)
        elif kind == "CX":
            left, right = targets
            simulator.cx(left, right)
        else:
            raise ValueError(f"unsupported Clifford kind {kind!r}")

    for kind, targets in prep_b:
        apply(kind, targets, inverse=False)
    for kind, targets in reversed(prep_a):
        apply(kind, targets, inverse=True)

    probability = 1.0
    for qubit in range(n_qubits):
        expectation = simulator.peek_z(qubit)
        if expectation == -1:
            return 0.0
        if expectation == 0:
            probability *= 0.5
            simulator.postselect_z(qubit, desired_value=False)
    return math.sqrt(probability)


def _theta0_d_trajectory_gate(context: dict) -> dict:
    """Gate 1: Stim-route D(r) equals dense D(r) at 1e-12, all rounds,
    on the non-flat X5-variant theta=0 trajectory, which must show the
    Clifford recurrence (D reaching exactly 0 and reviving to 1.0)."""

    d_dense = context["x5_dense_theta0_distances"]
    d_stim = context["x5_stim_theta0_distances"]
    if len(d_dense) != len(d_stim):
        raise Refusal("theta0 route lengths disagree")
    worst = max(
        abs(a - b) for a, b in zip(d_stim, d_dense)
    )
    dip_index = min(range(len(d_dense)), key=lambda i: d_dense[i])
    revival = max(d_dense[dip_index:])
    recurrence = bool(
        d_dense[dip_index] <= 1.0e-12 and revival >= 1.0 - 1.0e-12
    )
    flat = all(
        abs(d_dense[i] - d_dense[i - 1]) < P3_FLAT_TOL
        for i in range(1, len(d_dense))
    )
    return {
        "gate": "d_trajectory",
        "ran": True,
        "max_abs_stim_minus_dense": float(worst),
        "tolerance": ANCHOR_TOL,
        "agreement_passed": bool(worst <= ANCHOR_TOL),
        "dense_distances": [float(v) for v in d_dense],
        "stim_distances": [float(v) for v in d_stim],
        "clifford_recurrence": recurrence,
        "recurrence_dip_round": dip_index,
        "vehicle_is_non_flat": bool(not flat),
        "passed": bool(
            worst <= ANCHOR_TOL and recurrence and not flat
        ),
    }


def _theta0_inner_product_ag_gate(context: dict) -> dict:
    """Gate 2: the A-G printed example 1/sqrt(2) must reproduce and the
    round-trip identity |<0|C^dag C|0>| = 1 must hold on the fixture's own
    Clifford prefix (the sign-corruption detection surface: the theta=0
    D trajectory is provably sign-blind)."""

    bell = [("H", (0,)), ("CX", (0, 1))]
    example = stim_overlap([], bell, 2)
    expected = 2.0 ** -0.5
    example_ok = bool(abs(example - expected) <= 1.0e-15)
    prefix = [
        (kind, targets)
        for round_ops in context["x5_schedule"][:2]
        for kind, targets in round_ops
    ]
    if not prefix:
        raise Refusal("theta0 anchor prefix is empty")
    round_trip = stim_overlap(
        prefix, prefix, context["n_qubits"]
    )
    round_trip_ok = bool(round_trip == 1.0)
    return {
        "gate": "inner_product_ag",
        "ran": True,
        "ag_printed_example_overlap": float(example),
        "ag_printed_example_expected": float(expected),
        "ag_printed_example_passed": example_ok,
        "round_trip_overlap": float(round_trip),
        "round_trip_ops": len(prefix),
        "round_trip_passed": round_trip_ok,
        "passed": bool(example_ok and round_trip_ok),
    }


_THETA0_GATE_IMPLEMENTATIONS = {
    "d_trajectory": _theta0_d_trajectory_gate,
    "inner_product_ag": _theta0_inner_product_ag_gate,
}


def run_theta0_dual_gates(context: dict) -> dict:
    """Run BOTH registered theta=0 gates (amendment item 3)."""

    results = {}
    for gate_name in THETA0_REQUIRED_GATES:
        implementation = _THETA0_GATE_IMPLEMENTATIONS.get(gate_name)
        if implementation is None:
            raise Refusal(
                f"theta=0 gate {gate_name!r} is not wired; amendment "
                "item 3 requires BOTH gates to run"
            )
        results[gate_name] = implementation(context)
    return results


def adjudicate_theta0_dual_gates(results: dict) -> dict:
    """Both gates must have run and passed; a missing gate refuses."""

    missing = [
        name
        for name in THETA0_REQUIRED_GATES
        if name not in results or not results[name].get("ran")
    ]
    if missing:
        raise Refusal(
            "amendment item 3 dual-gate requirement violated; missing or "
            f"not-run gates: {missing}"
        )
    return {
        "required_gates": list(THETA0_REQUIRED_GATES),
        "all_ran": True,
        "all_passed": all(
            results[name]["passed"] for name in THETA0_REQUIRED_GATES
        ),
        "per_gate_passed": {
            name: bool(results[name]["passed"])
            for name in THETA0_REQUIRED_GATES
        },
    }


# ======================================================================
# plain lane (err_cell measurement only; fresh-process topology)
# ======================================================================


def run_plain_child(
    fixture_json: Path,
    input_id: int,
    output_npz: Path,
    *,
    untruncated: bool = False,
) -> dict:
    """Child body: one plain-lane trajectory with per-round checkpoints.

    Executed in a fresh process (``--plain-child``); validates the fixture
    through the schema-dispatched production validator, runs the committed
    plain engine at the frozen cap, and writes the checkpoint vectors.

    ``untruncated`` is the control lane of amendment 2 item 3(i): it opts
    into the plain engine's explicit uncapped-bond override
    (``untruncated_control=True``) for the inherited "untruncated run
    F = 1" control, and is reachable ONLY through this harness's control
    lane (the engine itself refuses the override on instrumented/evidence
    runs).
    """

    import numpy as np

    fixture = json.loads(fixture_json.read_text())
    worker_common = _load_sibling("plain_quimb_finite_memory_worker_common")
    fixture_hash = worker_common.validate_fixture(fixture)
    engine = _load_sibling("plain_quimb_finite_memory_engine")
    if engine.SPLIT_POLICY["max_bond"] != CAP:
        raise Refusal("plain lane split policy cap drifted from 32")
    result = engine.execute_plain(
        fixture,
        input_id=input_id,
        instrumented=False,
        materialize_checkpoints=True,
        untruncated_control=untruncated,
    )
    if untruncated and result.get("untruncated_control") is not True:
        raise Refusal(
            "the plain engine did not stamp the untruncated-control "
            "payload; the control lane cannot certify the uncapped run"
        )
    vectors = result["checkpoint_vectors"]
    np.savez(
        output_npz,
        **{f"r{k}": np.asarray(v, dtype=np.complex128) for k, v in vectors.items()},
    )
    summary = {
        "fixture_hash": fixture_hash,
        "case_id": fixture["case_id"],
        "input_id": input_id,
        "operation_count": result["operation_count"],
        "max_committed_bond": int(result["max_committed_bond"]),
        "final_committed_bond": int(result["final_committed_bond"]),
        "checkpoints": sorted(int(k) for k in vectors),
        "npz": str(output_npz),
    }
    if untruncated:
        summary["untruncated_control"] = True
    return summary


def _spawn_plain_children(
    np, fixture_path: Path, scratch_dir: Path, tag: str, *,
    untruncated: bool = False,
) -> tuple[dict, dict]:
    """Fresh plain-lane child per input; returns (states, summaries)."""

    plain_states = {}
    child_summaries = {}
    if not FORK_PYTHON.exists():
        raise Refusal(
            "the plain lane needs the fork pixi interpreter "
            f"({FORK_PYTHON}); it is missing on this checkout"
        )
    for input_id in (1, 2):
        npz_path = scratch_dir / f"plain_{tag}_in{input_id}.npz"
        command = [
            str(FORK_PYTHON),
            str(Path(__file__).resolve(strict=True)),
            "--plain-child",
            "--fixture-json",
            str(fixture_path),
            "--input",
            str(input_id),
            "--child-output",
            str(npz_path),
        ]
        if untruncated:
            command.append("--untruncated")
        completed = subprocess.run(
            command, capture_output=True, text=True
        )
        if completed.returncode != 0:
            raise Refusal(
                f"plain-lane child failed for input {input_id}:\n"
                + completed.stdout
                + completed.stderr
            )
        summary = json.loads(completed.stdout.splitlines()[-1])
        if untruncated and summary.get("untruncated_control") is not True:
            raise Refusal(
                "the untruncated control child did not certify the "
                "uncapped run (missing untruncated_control stamp)"
            )
        child_summaries[input_id] = summary
        with np.load(npz_path) as archive:
            plain_states[input_id] = {
                int(key[1:]): archive[key] for key in archive.files
            }
    return plain_states, child_summaries


def plain_lane_err_cell(
    oracle: DenseOracle,
    fixture: dict,
    fixture_path: Path,
    dense_states: dict,
    dense_distances: list,
    scratch_dir: Path,
    tag: str,
) -> dict:
    """Measure err_cell on this cell via fresh plain-lane child processes.

    Ruled by amendment 2 item 4: both operational definitions are
    computed and recorded -- ``err_d_trajectory``
    (max_r |D_r^plain - D_r^dense|) and ``err_reduced_state`` (max over
    checkpoints and inputs of the reduced trace distance between the
    plain and dense states) -- and the run refuses if they ever classify
    a cell differently under the 10x-margin rule.
    """

    np = oracle.np
    width = fixture["parameters"]["width"]
    plain_states, child_summaries = _spawn_plain_children(
        np, fixture_path, scratch_dir, tag
    )
    expected_rounds = sorted(dense_states[1])
    for input_id in (1, 2):
        if sorted(plain_states[input_id]) != expected_rounds:
            raise Refusal(
                "plain lane did not materialize every-round checkpoints"
            )
    plain_distances = oracle.blp_trajectory(
        plain_states[1], plain_states[2], width=width
    )
    err_d_trajectory = max(
        abs(a - b) for a, b in zip(plain_distances, dense_distances)
    )
    err_reduced_state = 0.0
    for input_id in (1, 2):
        for round_index in expected_rounds:
            value = oracle.trace_distance(
                oracle.system_rho(
                    plain_states[input_id][round_index], width=width
                ),
                oracle.system_rho(
                    dense_states[input_id][round_index], width=width
                ),
            )
            err_reduced_state = max(err_reduced_state, value)
    return {
        "lane": "plain",
        "cap": CAP,
        "children": child_summaries,
        "plain_distances": [float(v) for v in plain_distances],
        "err_d_trajectory": float(err_d_trajectory),
        "err_reduced_state": float(err_reduced_state),
        "err_cell_ruling": (
            "amendment 2 item 4: both err_cell definitions computed and "
            "recorded; the run refuses if they classify a cell "
            "differently under the 10x-margin rule"
        ),
    }


def untruncated_f1_control(
    oracle: DenseOracle,
    fixture: dict,
    fixture_path: Path,
    dense_states: dict,
    scratch_dir: Path,
    tag: str,
) -> dict:
    """Inherited "untruncated run F = 1" control (amendment 2 item 3(i)).

    Runs the plain engine's explicit uncapped-bond override in fresh
    control-lane children and checks the v1-ledgered fidelity (normalized
    squared overlap with the independent dense state, same input
    trajectory) at every checkpoint for both registered inputs.
    """

    np = oracle.np
    plain_states, child_summaries = _spawn_plain_children(
        np, fixture_path, scratch_dir, f"{tag}_untrunc", untruncated=True
    )
    expected_rounds = sorted(dense_states[1])
    worst = 0.0
    worst_locator = None
    for input_id in (1, 2):
        if sorted(plain_states[input_id]) != expected_rounds:
            raise Refusal(
                "untruncated control did not materialize every-round "
                "checkpoints"
            )
        for round_index in expected_rounds:
            x = plain_states[input_id][round_index]
            y = dense_states[input_id][round_index]
            nx = float(np.real(np.vdot(x, x)))
            ny = float(np.real(np.vdot(y, y)))
            if nx <= 0.0 or ny <= 0.0:
                raise Refusal(
                    "untruncated control state has nonpositive norm"
                )
            fidelity = float(abs(np.vdot(x, y)) ** 2 / (nx * ny))
            one_minus_f = 1.0 - fidelity
            if one_minus_f > worst:
                worst = one_minus_f
                worst_locator = {
                    "input_id": input_id,
                    "round_index": round_index,
                }
    return {
        "control": "untruncated_f_equals_1",
        "ruling": "amendment 2 item 3(i); semantics unchanged from v1",
        "children": child_summaries,
        "worst_one_minus_fidelity": float(worst),
        "worst_locator": worst_locator,
        "threshold": UNTRUNCATED_ONE_MINUS_F_MAX,
        "passed": bool(worst <= UNTRUNCATED_ONE_MINUS_F_MAX),
    }


# ======================================================================
# adjudication (frozen sections 2/2a/2b + amendment items 2 and 4)
# ======================================================================


def classify_cell_witness(blp: dict, err_cell: float | None) -> dict:
    """Frozen two-sided margin rule for one cell's headline verdict."""

    delta_max = blp["max_increment"]
    if not delta_max > GUARD:
        verdict = VERDICT_NO_WITNESS
    elif err_cell is None:
        verdict = "UNCLASSIFIED_MARGIN_ERR_CELL_NOT_MEASURED"
    elif delta_max > MARGIN_FACTOR * err_cell:
        verdict = VERDICT_WITNESS
    else:
        verdict = VERDICT_BELOW_MARGIN
    return {
        "max_increment": delta_max,
        "guard": GUARD,
        "err_cell": err_cell,
        "margin_bar": (
            MARGIN_FACTOR * err_cell if err_cell is not None else None
        ),
        "verdict": verdict,
    }


def adjudicate_margin_outcome(cell_verdicts: list) -> dict:
    """Amendment item 4 (owner-decided: strict).

    If all six confirmatory cells report WITNESS_BELOW_MARGIN the outcome
    scores as a fixture-capability MISS at the current carrier error
    floors and the confirmatory claim dies; it is NOT evidence of witness
    absence, and revisiting requires a NEW preregistration anchored on a
    demonstrably lower MEASURED err_cell.
    """

    complete = len(cell_verdicts) == CELL_COUNT
    all_below = complete and all(
        verdict == VERDICT_BELOW_MARGIN for verdict in cell_verdicts
    )
    row = {
        "rule": "amendment item 4 (strict, owner-decided 2026-08-01)",
        "cell_count": len(cell_verdicts),
        "cell_verdicts": list(cell_verdicts),
        "all_below_margin": bool(all_below),
        "fired": bool(all_below),
    }
    if all_below:
        row.update(
            {
                "outcome": VERDICT_CAPABILITY_MISS,
                "confirmatory_claim_dies": True,
                "evidence_of_witness_absence": False,
                "revisit_requires": (
                    "a NEW preregistration round anchored on a "
                    "demonstrably lower MEASURED err_cell; post-unblinding "
                    "floor shopping is foreclosed"
                ),
            }
        )
    return row


def _majority_verdict(count: int, total: int) -> str:
    """Amendment item 2: majority means >= 4 of 6; exactly 3/6 is a MISS."""

    if total != CELL_COUNT:
        return "INCOMPLETE_FRAME"
    if count >= MAJORITY_MIN:
        return "CONFIRMED"
    if count == TIE_COUNT:
        return "NOT_CONFIRMED_MISS_AT_TIE"
    return "NOT_CONFIRMED_MISS"


def adjudicate_p1(cell_rows: list) -> dict:
    """P1: positive dense witness above guard in >= 4 of the 6 cells,
    magnitude in [1e-3, 1e-1], location within rounds 1..5 (ruled by
    amendment 2 item 7: conjunctive per cell; components additionally
    reported separately for audit)."""

    per_cell = []
    qualifying = 0
    for row in cell_rows:
        blp = row["blp"]
        above_guard = blp["positive_above_guard"]
        magnitude_in_band = bool(
            above_guard
            and P1_MAGNITUDE_BAND[0] <= blp["max_increment"]
            <= P1_MAGNITUDE_BAND[1]
        )
        location_in_band = bool(
            above_guard
            and blp["max_increment_arrival_round"] is not None
            and P1_LOCATION_ROUNDS[0]
            <= blp["max_increment_arrival_round"]
            <= P1_LOCATION_ROUNDS[1]
        )
        qualifies = bool(
            above_guard and magnitude_in_band and location_in_band
        )
        qualifying += qualifies
        per_cell.append(
            {
                "cell": row["cell_id"],
                "above_guard": above_guard,
                "magnitude_in_band": magnitude_in_band,
                "location_in_band": location_in_band,
                "qualifies_conjunctively": qualifies,
            }
        )
    return {
        "prediction": "P1",
        "class": "b_band",
        "magnitude_band": list(P1_MAGNITUDE_BAND),
        "location_rounds": list(P1_LOCATION_ROUNDS),
        "qualifying_cells": qualifying,
        "cell_count": len(cell_rows),
        "per_cell": per_cell,
        "verdict": _majority_verdict(qualifying, len(cell_rows)),
        "conjunctive_ruling": (
            "ruled by amendment 2 item 7: conjunctive reading; "
            "components reported per cell"
        ),
    }


def adjudicate_p2(
    x8_rows: list, cx_rows: list, thin_rows: list
) -> dict:
    """P2 interaction effect with amendment-1-item-2 majority semantics.

    The arms run as controls on the same six coordinates, never as
    additional confirmatory cells (ruled by amendment 2 item 5).
    Sub-claims (each mapped to a majority assertion; the thin-only
    minority mapping is ruled by amendment 2 item 6):
      cx_only:   NO positive witness above guard in >= 4 of 6 cells;
      thin_only: positive witness in a minority == no positive witness in
                 >= 4 of 6 cells;
      X8:        positive witness above guard in >= 4 of 6 cells.
    Distinguisher: if the thin-only arm matches X8's witness rate, the CX
    lever is not established -- that outcome kills the X8 mechanism
    reading and is reported as such.
    """

    def positive_count(rows):
        return sum(1 for row in rows if row["blp"]["positive_above_guard"])

    totals = {
        "X8": len(x8_rows),
        "cx_only": len(cx_rows),
        "thin_only": len(thin_rows),
    }
    positives = {
        "X8": positive_count(x8_rows),
        "cx_only": positive_count(cx_rows),
        "thin_only": positive_count(thin_rows),
    }
    sub_claims = {
        "cx_only_no_witness_majority": _majority_verdict(
            totals["cx_only"] - positives["cx_only"], totals["cx_only"]
        ),
        "thin_only_witness_minority": _majority_verdict(
            totals["thin_only"] - positives["thin_only"],
            totals["thin_only"],
        ),
        "x8_witness_majority": _majority_verdict(
            positives["X8"], totals["X8"]
        ),
    }
    rates_match = bool(
        totals["thin_only"] == totals["X8"]
        and positives["thin_only"] == positives["X8"]
    )
    verdict = (
        "CONFIRMED"
        if all(value == "CONFIRMED" for value in sub_claims.values())
        and not rates_match
        else "NOT_CONFIRMED_MISS"
        if all(
            value != "INCOMPLETE_FRAME" for value in sub_claims.values()
        )
        else "INCOMPLETE_FRAME"
    )
    row = {
        "prediction": "P2",
        "class": "b_band",
        "positive_counts": positives,
        "cell_counts": totals,
        "sub_claims": sub_claims,
        "thin_only_matches_x8_rate": rates_match,
        "verdict": verdict,
        "minority_ruling": (
            "ruled by amendment 2 item 6: minority claims mapped to "
            "complementary majority claims; <= 2/6 is a minority PASS and "
            "exactly 3/6 scores NOT-CONFIRMED (mirrors amendment 1 item 2)"
        ),
    }
    if rates_match:
        row["mechanism_reading"] = (
            "CX_LEVER_NOT_ESTABLISHED_X8_MECHANISM_READING_KILLED"
        )
    return row


def adjudicate_p3(x8_theta0_blp: dict) -> dict:
    """P3 (X8 side): the X8 theta=0 arm is flat -- every increment below
    1e-12.  (The X5-variant recurrence half of P3 lives in the dual-gate
    context.)"""

    increments = x8_theta0_blp["increments"]
    max_abs = max((abs(v) for v in increments), default=0.0)
    return {
        "prediction": "P3_x8_flatness",
        "class": "a_exact",
        "max_abs_increment": float(max_abs),
        "tolerance": P3_FLAT_TOL,
        "passed": bool(max_abs < P3_FLAT_TOL),
    }


# ======================================================================
# inherited v1 exactness controls (amendment 1 item 8; surfaces ruled by
# amendment 2 item 3)
# ======================================================================


def inherited_exactness_controls(
    oracle: DenseOracle,
    fixture: dict,
    *,
    plain_lane: str,
    scratch_dir: Path,
    tag: str,
) -> dict:
    """Run-time re-trip of the inherited v1 exactness controls.

    Implemented: theta=0-plus-no-CX arm has constant D (inherited Clifford
    stream only, layers <= 5), plus a corruption re-trip (every collision
    rotation restored at its true theta must move D; harness-chosen
    vehicle, disclosed below), and -- ruled by amendment 2 item 3(i) --
    the "untruncated run F = 1" control wired to the plain engine's
    explicit uncapped-bond override through this harness's control lane
    (it runs whenever the plain lane runs; registered mode always runs
    the plain lane).  The "LOCAL-alphabet F = 1" row is REMOVED by
    amendment 2 item 3(ii) as a disclosed weakening, not a silent one.
    """

    width = fixture["parameters"]["width"]
    states_1 = oracle.round_states(
        fixture, 1, theta_zero=True, clifford_layer_max=5
    )
    states_2 = oracle.round_states(
        fixture, 2, theta_zero=True, clifford_layer_max=5
    )
    distances = oracle.blp_trajectory(states_1, states_2, width=width)
    spread = max(distances) - min(distances)
    constant = bool(spread <= 1.0e-12)

    corrupted_1 = oracle.round_states(
        fixture,
        1,
        theta_zero=True,
        clifford_layer_max=5,
        corrupt_theta_zero_off=True,
    )
    corrupted_2 = oracle.round_states(
        fixture,
        2,
        theta_zero=True,
        clifford_layer_max=5,
        corrupt_theta_zero_off=True,
    )
    corrupted = oracle.blp_trajectory(corrupted_1, corrupted_2, width=width)
    corrupted_spread = max(corrupted) - min(corrupted)
    trip_fired = bool(corrupted_spread > GUARD)

    if plain_lane == "subprocess":
        fixture_path = scratch_dir / f"fixture_controls_{tag}.json"
        fixture_path.write_text(json.dumps(fixture, sort_keys=True))
        dense_states = {
            1: oracle.round_states(fixture, 1),
            2: oracle.round_states(fixture, 2),
        }
        untruncated = untruncated_f1_control(
            oracle, fixture, fixture_path, dense_states, scratch_dir, tag
        )
    else:
        untruncated = {
            "control": "untruncated_f_equals_1",
            "status": "NOT_RUN",
            "detail": (
                "development dry run with --plain-lane off; the wired "
                "control (amendment 2 item 3(i)) runs whenever the plain "
                "lane runs, and registered mode always runs the plain "
                "lane"
            ),
        }

    implemented_passed = bool(constant and trip_fired)
    if untruncated.get("passed") is not None:
        implemented_passed = implemented_passed and bool(
            untruncated["passed"]
        )

    return {
        "theta0_plus_no_cx_constant_d": {
            "distances": [float(v) for v in distances],
            "spread": float(spread),
            "passed": constant,
        },
        "theta0_plus_no_cx_corruption_trip": {
            "vehicle": (
                "theta_zero flag corrupted off (every rotation restored "
                "at its true theta); harness-chosen and disclosed -- the "
                "frozen text does not name v1's corresponding registered "
                "corruption, and a single restored rotation provably "
                "cannot fire (reduced branches stay orthogonal, D = 1)"
            ),
            "corrupted_spread": float(corrupted_spread),
            "fired": trip_fired,
        },
        "untruncated_f_equals_1": untruncated,
        "local_alphabet_f_equals_1": {
            "status": "REMOVED_BY_AMENDMENT_2_ITEM_3II",
            "detail": (
                "amendment 2 item 3(ii): amended down with justification "
                "-- no implementation exists anywhere in the repository, "
                "rebuilding one is new mechanism code carrying its own "
                "validation debt, and the remaining controls cover the "
                "pipeline-integrity surface it addressed; a disclosed "
                "weakening, not a silent one"
            ),
        },
        "all_implemented_controls_passed": implemented_passed,
        "registered_mode_blockers": [],
    }


# ======================================================================
# section 3b inert-checkpoint control (ruled by amendment 2 item 8)
# ======================================================================

SHIPPED_CHECKPOINT_SET = (0, 1, 2, 4, 10)
DEV_CELL_REFERENCE = {
    "cell": "s2-g2-r10",
    "p0_all_rounds_witness": "+7.227e-4",
    "p0_all_rounds_location": "r8->r9",
}


def inert_checkpoint_control(
    oracle: DenseOracle, cell: dict
) -> dict:
    """P0 under the shipped checkpoint set must report NO WITNESS while
    the all-rounds set reports a positive witness (prereg section 3b)."""

    emitter = _load_sibling("emit_gcapeps_finite_memory_fixture")
    fixture = emitter.build_fixture(
        run_partition=cell["run_partition"],
        width=cell.get("width", 7),
        rounds=cell["rounds"],
        axis_family=cell.get("axis_family", 3),
        p_event_numerator=cell.get("p_event_numerator", 3),
        seed=cell["seed"],
        gamma_index=cell["gamma_index"],
        run_blpensemble=False,
    )
    emitter.validate_fixture(fixture)
    width = fixture["parameters"]["width"]
    states_1 = oracle.round_states(fixture, 1)
    states_2 = oracle.round_states(fixture, 2)
    distances = oracle.blp_trajectory(states_1, states_2, width=width)
    all_rounds = blp_objects(distances)
    shipped_rounds = [
        r for r in SHIPPED_CHECKPOINT_SET if r <= fixture["parameters"]["rounds"]
    ]
    shipped = blp_objects([distances[r] for r in shipped_rounds])
    return {
        "control": "inert_shipped_checkpoint_set",
        "p0_case_id": fixture["case_id"],
        "shipped_checkpoint_set": shipped_rounds,
        "shipped_witness_above_guard": shipped["positive_above_guard"],
        "all_rounds_witness_above_guard": all_rounds["positive_above_guard"],
        "all_rounds_max_increment": all_rounds["max_increment"],
        "all_rounds_location": all_rounds["max_increment_location"],
        "expected": (
            "shipped set NO WITNESS; all-rounds positive (checkpoint "
            "repair is load-bearing)"
        ),
        "as_expected": bool(
            not shipped["positive_above_guard"]
            and all_rounds["positive_above_guard"]
        ),
        "fresh_cell_ruling": (
            "ruled by amendment 2 item 8: the numeric cross-check binds "
            f"on the development cell only ({DEV_CELL_REFERENCE}); on "
            "confirmatory cells the value is recorded and any deviation "
            "is a reported finding, not an automatic refusal"
        ),
    }


# ======================================================================
# per-cell execution
# ======================================================================


def run_cell(
    oracle: DenseOracle,
    cell: dict,
    *,
    plain_lane: str,
    scratch_dir: Path,
) -> dict:
    """Execute one cell: X8 witness measurement + P2 control arms (the
    arms are controls on the same coordinates, never additional
    confirmatory cells; ruled by amendment 2 item 5)."""

    cell_id = cell_label(cell)
    arm_rows = {}
    fixture_paths = {}
    for arm in ("X8", *P2_CONTROL_ARMS):
        started = time.perf_counter()
        fixture, fixture_hash, schema = fixture_for_arm(arm, cell)
        if fixture["run_partition"] != cell["run_partition"]:
            raise Refusal("fixture partition drifted from the cell request")
        width = fixture["parameters"]["width"]
        states_1 = oracle.round_states(fixture, 1)
        states_2 = oracle.round_states(fixture, 2)
        distances = oracle.blp_trajectory(states_1, states_2, width=width)
        blp = blp_objects(distances)
        instruments = frame_instruments(oracle.np, fixture)
        row = {
            "cell_id": cell_id,
            "arm": arm,
            "case_id": fixture["case_id"],
            "fixture_schema": schema,
            "fixture_hash": fixture_hash,
            "blp": blp,
            "frame_instruments": instruments,
            "wall_seconds": time.perf_counter() - started,
        }
        if arm == "X8":
            row["p4"] = adjudicate_p4(instruments)
            theta0_states_1 = oracle.round_states(
                fixture, 1, theta_zero=True
            )
            theta0_states_2 = oracle.round_states(
                fixture, 2, theta_zero=True
            )
            theta0_blp = blp_objects(
                oracle.blp_trajectory(
                    theta0_states_1, theta0_states_2, width=width
                )
            )
            row["x8_theta0_blp"] = theta0_blp
            row["p3_x8_flatness"] = adjudicate_p3(theta0_blp)
            fixture_path = scratch_dir / f"fixture_{cell_id}_{arm}.json"
            fixture_path.write_text(json.dumps(fixture, sort_keys=True))
            fixture_paths[arm] = fixture_path
            if plain_lane == "subprocess":
                row["plain_lane"] = plain_lane_err_cell(
                    oracle,
                    fixture,
                    fixture_path,
                    {1: states_1, 2: states_2},
                    distances,
                    scratch_dir,
                    f"{cell_id}_{arm}",
                )
                classification_a = classify_cell_witness(
                    blp, row["plain_lane"]["err_d_trajectory"]
                )
                classification_b = classify_cell_witness(
                    blp, row["plain_lane"]["err_reduced_state"]
                )
                if (
                    classification_a["verdict"]
                    != classification_b["verdict"]
                ):
                    raise Refusal(
                        "amendment 2 item 4: the two err_cell "
                        f"definitions classify cell {cell_id} "
                        f"differently ({classification_a['verdict']} vs "
                        f"{classification_b['verdict']}) under the "
                        "10x-margin rule; the run is refused"
                    )
                row["margin_classification"] = classification_a
                row["margin_classification_reduced_state_def"] = (
                    classification_b
                )
            else:
                row["plain_lane"] = {
                    "status": "NOT_RUN",
                    "detail": "development dry run with --plain-lane off",
                }
                row["margin_classification"] = classify_cell_witness(
                    blp, None
                )
        print(
            f"[{cell_id}] arm={arm} witness_max={blp['max_increment']:+.6e} "
            f"at {blp['max_increment_location']} "
            f"above_guard={blp['positive_above_guard']} "
            f"pullback_mean={instruments['mean_pulled_back_weight']}",
            flush=True,
        )
        arm_rows[arm] = row
    return {
        "cell_id": cell_id,
        "cell": dict(cell),
        "arms": arm_rows,
        "fixture_paths": {k: str(v) for k, v in fixture_paths.items()},
    }


def verify_x5_theta0_equivalence(cell: dict) -> dict:
    """Run-time op-for-op verification of the amendment-2-item-2 vehicle.

    The X5-variant theta=0 Clifford stream is reconstructed WITHOUT the
    cx_only vehicle: X5 = every-round cross-row CX + thinning, and at
    theta=0 thinning acts on nothing (every rotation is the identity), so
    the X5 theta=0 stream is the thin-only arm's Clifford stream (= the
    inherited v1 stream) with the frozen cross-row
    ``CX(w//2, w + w//2)`` appended at the layer-6 position on EVERY
    round.  That reconstruction must equal the cx_only arm's Clifford
    stream operation-for-operation; a mismatch refuses the run.
    """

    cx_fixture, cx_hash, _ = fixture_for_arm("cx_only", cell)
    thin_fixture, thin_hash, _ = fixture_for_arm("thin_only", cell)
    width = cx_fixture["parameters"]["width"]
    cross_row = ("CX", (width // 2, width + width // 2))
    vehicle_stream = clifford_schedule(cx_fixture)
    reconstructed = [
        [*round_ops, cross_row]
        for round_ops in clifford_schedule(thin_fixture)
    ]
    if vehicle_stream != reconstructed:
        raise Refusal(
            "amendment 2 item 2: the reconstructed X5-variant theta=0 "
            "Clifford stream does not equal the cx-only vehicle stream "
            "operation-for-operation; the adopted equivalence does not "
            "hold on this cell and the run is refused"
        )
    operation_count = sum(len(round_ops) for round_ops in vehicle_stream)
    print(
        "[theta0] X5-theta0 vehicle op-for-op equivalence VERIFIED "
        f"(amendment 2 item 2): {operation_count} Clifford operations "
        f"across {len(vehicle_stream)} rounds equal the reconstructed "
        "X5-variant theta=0 stream (thin-only Clifford stream + frozen "
        f"every-round cross-row CX{cross_row[1]}); thinning touches only "
        "rotations, which vanish at theta=0.",
        flush=True,
    )
    return {
        "verified": True,
        "operation_count": operation_count,
        "round_count": len(vehicle_stream),
        "cross_row_gate": ["CX", list(cross_row[1])],
        "vehicle_fixture_hash": cx_hash,
        "reconstruction_fixture_hash": thin_hash,
        "ruling": "amendment 2 item 2 (X5-theta0 vehicle by equivalence)",
    }


def build_theta0_context(oracle: DenseOracle, cell: dict) -> dict:
    """Assemble the mandatory X5-variant theta=0 dual-gate context.

    Amendment 2 item 2: the mandatory X5-theta0 anchor arm is REALIZED AS
    the landed cx-only-arm emitter at theta=0 on the registered path (at
    theta=0 every rotation is the identity and thinning acts only on
    rotations, so the streams agree operation-for-operation).  The
    equivalence is verified and printed at run time before the dual gates
    consume the vehicle.  X5-measured numbers remain citable only as X5's
    (amendment 1 item 7).
    """

    equivalence = verify_x5_theta0_equivalence(cell)
    fixture, fixture_hash, schema = fixture_for_arm("cx_only", cell)
    width = fixture["parameters"]["width"]
    dense_1 = oracle.round_states(fixture, 1, theta_zero=True)
    dense_2 = oracle.round_states(fixture, 2, theta_zero=True)
    dense_distances = oracle.blp_trajectory(dense_1, dense_2, width=width)
    schedule = clifford_schedule(fixture)
    stim_distances = stim_theta0_distances(schedule, width=width)
    return {
        "vehicle": "cx-only-arm-clifford-stream",
        "vehicle_adopted_by": (
            "amendment 2 item 2 (X5-theta0 vehicle by equivalence; "
            "registered path)"
        ),
        "vehicle_fixture_hash": fixture_hash,
        "vehicle_fixture_schema": schema,
        "x5_theta0_equivalence": equivalence,
        "x5_dense_theta0_distances": dense_distances,
        "x5_stim_theta0_distances": stim_distances,
        "x5_schedule": schedule,
        "n_qubits": fixture["geometry"]["n_qubits"],
    }


# ======================================================================
# CLI
# ======================================================================


def refuse(message: str) -> int:
    print(f"REFUSED: {message}", flush=True)
    return 2


def _atomic_write_json(path: Path, payload: dict) -> None:
    """One writer, atomic publish."""

    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, indent=1, sort_keys=True)
    descriptor, temp_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=path.name, suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise


def _parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0]
    )
    parser.add_argument(
        "--mode", choices=("development", "registered")
    )
    parser.add_argument(
        "--cell",
        type=parse_cell,
        action="append",
        default=None,
        help=(
            "cell spec s<seed>-g<gamma_index>-r<rounds> or "
            "hv2-<k>-g<gamma_index>-r<rounds>; repeatable.  Registered "
            "mode runs the frozen six-cell frame; omit --cell there or "
            "name the frame exactly"
        ),
    )
    parser.add_argument(
        "--stage0-evidence",
        type=Path,
        default=None,
        help=(
            "Stage-0 amended-lane evidence JSON (amendment 1 item 5); "
            "required in registered mode"
        ),
    )
    parser.add_argument(
        "--owner-release-token",
        default=None,
        help=(
            "the ONE remaining registered gate: the owner's release of "
            "the first heldout build (amendment 2 item 1).  No token has "
            "been minted yet; the owner mints it at release time"
        ),
    )
    parser.add_argument(
        "--plain-lane",
        choices=("off", "subprocess"),
        default=None,
        help=(
            "err_cell measurement lane; default off in development, "
            "forced subprocess in registered"
        ),
    )
    parser.add_argument("--output", type=Path, default=None)
    # plain-child protocol (fresh-process topology)
    parser.add_argument("--plain-child", action="store_true")
    parser.add_argument("--fixture-json", type=Path, default=None)
    parser.add_argument("--input", type=int, choices=(1, 2), default=None)
    parser.add_argument("--child-output", type=Path, default=None)
    parser.add_argument(
        "--untruncated",
        action="store_true",
        help=(
            "plain-child only: run the control lane's uncapped-bond "
            "override (amendment 2 item 3(i))"
        ),
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = _parse_args(argv)

    if args.plain_child:
        if (
            args.fixture_json is None
            or args.input is None
            or args.child_output is None
        ):
            return refuse(
                "--plain-child needs --fixture-json, --input, "
                "--child-output"
            )
        _set_thread_envelope()
        summary = run_plain_child(
            args.fixture_json,
            args.input,
            args.child_output,
            untruncated=args.untruncated,
        )
        print(json.dumps(summary, sort_keys=True), flush=True)
        return 0
    if args.untruncated:
        return refuse(
            "--untruncated is the plain-child control lane only "
            "(amendment 2 item 3(i)); it is not a run-level option"
        )

    if args.mode is None:
        return refuse("--mode is required")
    mode = args.mode
    try:
        _set_thread_envelope()
        print(f"preconditions: prereg {PREREG_RELATIVE}", flush=True)
        stamps = collect_provenance_stamps(mode)
        for key in (
            "main_repository_head_commit",
            "fork_commit",
            "preregistration_sha256",
            "runner_source_sha256",
            "interpreter_version",
        ):
            print(f"stamp {key}: {stamps[key]}", flush=True)
        if stamps["main_repository_load_bearing_dirty"]:
            print(
                "stamp main_repository_load_bearing_dirty: "
                + json.dumps(stamps["main_repository_load_bearing_dirty"]),
                flush=True,
            )

        # amendment item 5: Stage-0 measured worst-pair gate
        if args.stage0_evidence is not None:
            stage0 = stage0_gate(args.stage0_evidence)
            print(
                "stage0 measured worst-pair one-minus-fidelity: "
                f"{stage0['measured_worst_pair_one_minus_fidelity']:.6e} "
                f"<= {STAGE0_WORST_PAIR_MAX:g} "
                f"({stage0['measured_worst_pair_name']})",
                flush=True,
            )
        elif mode == "registered":
            raise Refusal(
                "registered mode requires --stage0-evidence: the "
                "confirmatory run must re-record the MEASURED Stage-0 "
                "worst-pair value from its own Stage-0 evidence "
                "(amendment item 5)"
            )
        else:
            stage0 = {
                "status": "NOT_RECORDED",
                "detail": (
                    "development dry run without Stage-0 evidence; a "
                    "confirmatory run is REFUSED without it"
                ),
            }
            print(
                "stage0 evidence: NOT PROVIDED (development dry run only)",
                flush=True,
            )

        cells = resolve_cells(mode, args.cell or [])

        # The ONE remaining registered gate (amendment 2 item 1): nothing
        # from either heldout seed may be built before the owner's release.
        owner_release = enforce_owner_release(
            mode, args.owner_release_token
        )
        print(
            f"owner-release gate: {owner_release['status']}", flush=True
        )

        plain_lane = args.plain_lane
        if mode == "registered":
            plain_lane = "subprocess"  # margin rule needs err_cell
        elif plain_lane is None:
            plain_lane = "off"

        scratch_root = (
            REPO / ".scratch" / "gcapeps-fixture-v2" / "confirmatory"
        )
        run_scratch = scratch_root / mode / "work"
        run_scratch.mkdir(parents=True, exist_ok=True)

        oracle = DenseOracle()

        # theta=0 dual gates (amendment 1 item 3) on the first cell's
        # coordinates; both gates must run before any witness adjudication.
        # The X5-theta0 vehicle is the cx-only arm at theta=0, adopted on
        # the registered path by amendment 2 item 2 with the op-for-op
        # equivalence verified and printed at run time.
        theta0_context = build_theta0_context(oracle, cells[0])
        theta0_results = run_theta0_dual_gates(theta0_context)
        theta0_adjudication = adjudicate_theta0_dual_gates(theta0_results)
        for gate_name in THETA0_REQUIRED_GATES:
            print(
                f"[theta0] gate {gate_name}: "
                f"passed={theta0_results[gate_name]['passed']}",
                flush=True,
            )
        if not theta0_adjudication["all_passed"]:
            raise Refusal(
                "theta=0 dual gates did not both pass; the anchor is not "
                "established (amendment item 3)"
            )

        # amendment 1 item 8: inherited v1 exactness controls at run time
        # (surfaces ruled by amendment 2 item 3: untruncated F=1 wired to
        # the plain override; LOCAL-alphabet removed as a disclosed
        # weakening)
        first_x8_fixture, _, _ = fixture_for_arm("X8", cells[0])
        controls = inherited_exactness_controls(
            oracle,
            first_x8_fixture,
            plain_lane=plain_lane,
            scratch_dir=run_scratch,
            tag=cell_label(cells[0]),
        )
        print(
            "[controls] theta0-plus-no-CX constant D: "
            f"passed={controls['theta0_plus_no_cx_constant_d']['passed']} "
            "corruption trip fired="
            f"{controls['theta0_plus_no_cx_corruption_trip']['fired']}",
            flush=True,
        )
        untruncated_row = controls["untruncated_f_equals_1"]
        print(
            "[controls] untruncated F=1 (amendment 2 item 3(i)): "
            + (
                f"passed={untruncated_row['passed']} "
                f"worst_one_minus_fidelity="
                f"{untruncated_row['worst_one_minus_fidelity']:.3e}"
                if "passed" in untruncated_row
                else untruncated_row["status"]
            ),
            flush=True,
        )
        print(
            "[controls] LOCAL-alphabet F=1: "
            f"{controls['local_alphabet_f_equals_1']['status']}",
            flush=True,
        )
        if not controls["all_implemented_controls_passed"]:
            raise Refusal(
                "inherited v1 exactness controls failed or did not "
                "re-trip (amendment 1 item 8)"
            )
        if mode == "registered" and controls["registered_mode_blockers"]:
            raise Refusal(
                "inherited controls lack committed surfaces "
                f"({controls['registered_mode_blockers']}); registered "
                "execution is refused until they land"
            )

        # section 3b inert-checkpoint control (amendment 2 item 8:
        # recorded on fresh cells, not fatal)
        inert_control = inert_checkpoint_control(oracle, cells[0])
        print(
            "[controls] inert shipped-checkpoint control as expected: "
            f"{inert_control['as_expected']}",
            flush=True,
        )

        # state phase: per-cell arms
        cell_results = [
            run_cell(
                oracle,
                cell,
                plain_lane=plain_lane,
                scratch_dir=run_scratch,
            )
            for cell in cells
        ]

        # adjudication
        x8_rows = [row["arms"]["X8"] for row in cell_results]
        cx_rows = [row["arms"]["cx_only"] for row in cell_results]
        thin_rows = [row["arms"]["thin_only"] for row in cell_results]
        p1 = adjudicate_p1(x8_rows)
        p2 = adjudicate_p2(x8_rows, cx_rows, thin_rows)
        margin_outcome = adjudicate_margin_outcome(
            [row["margin_classification"]["verdict"] for row in x8_rows]
        )
        p3_rows = [row["p3_x8_flatness"] for row in x8_rows]
        p4_rows = [row["p4"] for row in x8_rows]

        adjudication = {
            "p1": p1,
            "p2": p2,
            "p3_x8_flatness_per_cell": p3_rows,
            "p3_x5_recurrence": {
                "carried_by": "theta0 dual gates (d_trajectory)",
                "clifford_recurrence": theta0_results["d_trajectory"][
                    "clifford_recurrence"
                ],
            },
            "p4_per_cell": p4_rows,
            "theta0_dual_gates": theta0_adjudication,
            "margin_outcome": margin_outcome,
            "zero_witness_reading": (
                "a zero witness is never evidence of Markovianity "
                "(BLP fixed-pair limitation, v1-closed)"
            ),
        }
        if mode == "development":
            adjudication["standing"] = (
                "DEVELOPMENT_DRY_RUN_NONCLAIM: adjudication preview on "
                "CALIBRATION cells; the frozen 6-cell frame (amendment 2 "
                "item 1) is registered-only and no verdict here carries "
                "standing"
            )

        payload = {
            "schema": SCHEMA,
            "mode": mode,
            "registered_standing": mode == "registered",
            "label": (
                REGISTERED_LABEL
                if mode == "registered"
                else DEVELOPMENT_LABEL
            ),
            "claim_boundary": (
                "bounded dense BLP witness measurement on the frozen "
                "fixture-v2 (X8) family; no truncation, carrier, PEPS/2D, "
                "QEC Record, or LER claim; the v2 geometry remains "
                "exactly-MPS under rung fusion (amendment item 6)"
            ),
            "lanes": {
                "headline": "dense oracle (every headline number)",
                "err_cell": (
                    "plain lane at cap 32"
                    if plain_lane == "subprocess"
                    else "not measured in this dry run"
                ),
                "l2bp_compressor_lane": (
                    "NOT adopted by this preregistration"
                ),
            },
            "provenance_stamps": stamps,
            "stage0_gate": stage0,
            "owner_release_gate": owner_release,
            "frozen_constraints": {
                k: (list(v) if isinstance(v, tuple) else v)
                for k, v in FROZEN_CONFIRMATORY_CONSTRAINTS.items()
            },
            "frozen_confirmatory_cells": [
                {**cell, "cell_id": cell_label(cell)}
                for cell in FROZEN_CONFIRMATORY_CELLS
            ],
            "theta0_dual_gate_context": {
                key: value
                for key, value in theta0_context.items()
                if key != "x5_schedule"
            },
            "theta0_dual_gate_results": theta0_results,
            "inherited_exactness_controls": controls,
            "inert_checkpoint_control": inert_control,
            "cells": cell_results,
            "adjudication": adjudication,
            "amendment_2_rulings": {
                "FA-1": "ruled by amendment 2 item 1 (frozen six-cell frame)",
                "FA-2": (
                    "ruled by amendment 2 item 2 (X5-theta0 vehicle by "
                    "equivalence; op-for-op verified at run time)"
                ),
                "FA-3": (
                    "ruled by amendment 2 item 4 (both err_cell "
                    "definitions; divergent classification refuses)"
                ),
                "FA-4": (
                    "ruled by amendment 2 item 5 (arms are controls, "
                    "not cells)"
                ),
                "FA-5": (
                    "ruled by amendment 2 item 3 (untruncated F=1 wired "
                    "to the plain override; LOCAL-alphabet removed as a "
                    "disclosed weakening)"
                ),
                "FA-6": "ruled by amendment 2 item 6 (minority semantics)",
                "FA-7": "ruled by amendment 2 item 7 (P1 conjunctive)",
                "FA-8": (
                    "ruled by amendment 2 item 8 (fresh-cell control "
                    "deviations recorded, not refused)"
                ),
            },
        }

        if args.output is not None:
            output_path = args.output
            if output_path.suffix != ".json":
                return refuse("--output must end with .json")
        else:
            tag = "_".join(row["cell_id"] for row in cell_results)
            output_path = (
                scratch_root / mode / f"confirmatory_{tag}.json"
            )
        _atomic_write_json(output_path, payload)
        print(
            f"done mode={mode} cells={len(cell_results)} "
            f"p1={p1['verdict']} p2={p2['verdict']} "
            f"margin_fired={margin_outcome['fired']} "
            f"wrote {output_path}",
            flush=True,
        )
        return 0
    except Refusal as error:
        return refuse(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
