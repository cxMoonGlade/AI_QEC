#!/usr/bin/env python3
"""Supervise the committed GCAPEPS native 1/4-thread T3 regression.

The runner launches fresh worker processes for the frozen operation-100
finite-memory prefix.  Its verdict is limited to deterministic execution of
the selected finite-cap algorithm.  Candidate-versus-dense state accuracy,
generic PEPS faithfulness, QEC Records, and speed claims are outside scope.

The opt-in ``--degenerate-boundary trim_cluster`` flag runs the Stage-0
amended lane instead: native children at threads 1/2/4/8 with the fork's
degeneracy-aware boundary trim, gated on the preregistered amended bands
(``_STAGE0_AMENDED_BANDS``).  With the flag absent, behavior is the
committed default regression, unchanged.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from typing import Any, Mapping, Sequence


SCHEMA = (
    "error_coupling_simulator.external.gcapeps_finite_memory."
    "native_thread_regression.v1"
)
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
PROCESS_VARIABLES = (
    "QUIMB_NUM_PROCS",
    "QUIMB_NUM_MPI_WORKERS",
)
DYNAMIC_VARIABLES = (
    "OMP_DYNAMIC",
    "MKL_DYNAMIC",
)
QUIMB_NUMBA_CACHE = "False"
MPI_PRESENCE_VARIABLES = (
    "_QUIMB_MPI_LAUNCHED",
    "QUIMB_SYNCRO_MPI",
    "OMPI_COMM_WORLD_SIZE",
    "PMI_SIZE",
)
NUMBA_LAYER_VARIABLES = (
    "NUMBA_THREADING_LAYER",
    "NUMBA_THREADING_LAYER_PRIORITY",
)
CHECKPOINT_OPERATIONS = (99, 100)
STOP_AFTER_OPERATION = 100
INPUT_ID = 2
NATIVE_STRATEGY = "native_simple_update"
LEGACY_STRATEGY = "exact_tree_then_native_compress"
_NO_SHADOW_CAUSE = "not_observed_without_shadow"
_REPOSITORY = Path(__file__).resolve().parents[2]
_FORK_ROOT = _REPOSITORY / "external/forks/quimb-gcapeps"
_WORKER = Path(__file__).resolve().with_name(
    "gcapeps_native_thread_worker.py"
)
_FIXTURE_OWNER = Path(__file__).resolve().with_name(
    "emit_gcapeps_finite_memory_fixture.py"
)
_TIMING_OWNER = Path(__file__).resolve().with_name(
    "gcapeps_finite_memory_timing.py"
)
_DEFAULT_FORK_PYTHON = (
    _REPOSITORY
    / "external/forks/quimb-gcapeps/.pixi/envs/testpymid/bin/python"
)
_MAX_CHILD_STDOUT_BYTES = 64 * 1024 * 1024
_BANDS = {
    "relative_state_distance_max": 1.0e-9,
    "relative_norm_distance_max": 1.0e-10,
    "one_minus_fidelity_max": 1.0e-10,
    "fidelity_roundoff_correction_max": 1.0e-12,
}

# --- Stage-0 amended degenerate-boundary lane (opt-in, dormant by default) ---
DEGENERATE_BOUNDARY_CHOICES = ("trim_cluster",)
AMENDED_THREAD_COUNTS = (1, 2, 4, 8)
AMENDED_THREAD_PAIRS = ((1, 2), (1, 4), (1, 8), (2, 4), (2, 8), (4, 8))
# Exact relative tie tolerance of the fork's trim_cluster rule
# (quimb.tensor.decomp.DEGENERATE_BOUNDARY_RTOL at fork commit 33f74407).
_DEGENERATE_BOUNDARY_TIE_RTOL = 1.0e-10
_STAGE0_AMENDED_BAND_SET = "stage0_amended_trim_cluster"
_STAGE0_AMENDED_BANDS = {
    "relative_state_distance_max": 3.5e-2,
    "relative_norm_distance_max": 3.5e-2,
    "one_minus_fidelity_max": 6.1e-4,
    "fidelity_roundoff_correction_max": 1.0e-12,
}
_STAGE0_AMENDED_BANDS_JUSTIFICATION = (
    "Amended Stage-0 acceptance bands for the opt-in "
    "degenerate_boundary='trim_cluster' lane. Primary bit-identity across "
    "thread counts is not achievable because complex128 BLAS "
    "(zgemm/zgesdd) on this host is thread-count-dependent at the ulp "
    "level (measured 7.1e-14 / 4.5e-13). The degenerate-boundary trim "
    "removes the ill-posed-projector seeding at tied singular-value "
    "clusters (divergence onset 3.6e-9 -> 2.0e-12; transient "
    "amplification reduced by about four orders of magnitude). The "
    "6.1e-4 one-minus-fidelity band is the PARITY_REPAIR_SPEC Stage-0 "
    "preregistered tolerance (10x below the 6.1e-3 parity target); "
    "measured worst-pair margin >= 53x. Evidence: "
    ".scratch/thread-invariance/ (FIX_DECISION.md, "
    "runs/analysis_summary.json, runs/fix/, runs/verify/)."
)
_STAGE0_KEPT_DIMENSION_EXCLUSION_JUSTIFICATION = (
    "In the amended trim_cluster lane the cross-thread exact-metadata "
    "requirement excludes per-split kept dimensions "
    "(candidate_kept_dimensions): at noise-floor tie clusters (singular "
    "values at the ~1e-16 relative noise floor) the cluster extent is "
    "inherently ulp-sensitive to this host's thread-dependent complex128 "
    "BLAS, so cross-thread kept-dimension equality is unattainable for "
    "any rule that decides from the singular values; the associated "
    "discarded-weight differences are ~1e-31 and physically nil. "
    "State-level agreement is the meaningful criterion and passes the "
    "amended bands with >= 53x measured margin. Kept dimensions are "
    "demoted to a recorded per-pair diagnostic (mismatch count and max "
    "absolute difference); every other projection field (plan digest, "
    "canonical gate transcript, routing, configured policies, pullback, "
    "and fixture identity) remains strictly equality-checked, and the "
    "kept-dimension list length (split structure) must still agree "
    "exactly. Default mode keeps full strict equality."
)

EXPECTED_SPLIT_POLICY = {
    "max_bond": 32,
    "cutoff": 0.0,
    "cutoff_mode": "rel",
    "method": "svd",
    "renorm": False,
    "absorb": None,
    "smudge": 1.0e-12,
    "smudge_mode": "add",
    "power": 1.0,
}


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def _projection_sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _fixture_operation_prefix(
    fixture: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    try:
        rows = [
            operation
            for round_row in fixture["carrier_path"]["round_ledger"]
            for operation in round_row["operations"]
            if operation["operation_index"] <= STOP_AFTER_OPERATION
        ]
    except (KeyError, TypeError) as error:
        raise ValueError("fixture operation ledger is malformed") from error
    if [row["operation_index"] for row in rows] != list(
        range(STOP_AFTER_OPERATION + 1)
    ):
        raise ValueError("fixture operation prefix is not exact and contiguous")
    return rows


def _source_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path.resolve(strict=True))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _reject_duplicate_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _parse_json(raw: bytes, *, name: str) -> Mapping[str, Any]:
    if not isinstance(raw, bytes) or not raw:
        raise ValueError(f"{name} is empty")
    if len(raw) > _MAX_CHILD_STDOUT_BYTES:
        raise ValueError(f"{name} exceeds the byte cap")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"non-finite JSON token {token}")
            ),
        )
    except UnicodeDecodeError as exc:
        raise ValueError(f"{name} is not UTF-8") from exc
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} root must be an object")
    return value


def build_frozen_fixture() -> Mapping[str, Any]:
    owner = _load_path("_gcapeps_native_t3_fixture", _FIXTURE_OWNER)
    fixture = owner.build_fixture(
        run_partition="CALIBRATION",
        width=7,
        rounds=4,
        axis_family=3,
        p_event_numerator=3,
        seed=2,
        gamma_index=2,
        run_blpensemble=False,
    )
    owner.validate_fixture(fixture)
    if fixture["case_id"] != "calibration-g2-s2-w7-r4-a3-p3of4":
        raise ValueError("frozen T3 case id drifted")
    return fixture


def child_environment(
    parent: Mapping[str, str],
    *,
    thread_count: int,
) -> dict[str, str]:
    """Build the exact fresh-child thread envelope."""

    if (
        isinstance(thread_count, bool)
        or thread_count not in AMENDED_THREAD_COUNTS
    ):
        raise ValueError("thread_count must be exactly 1, 2, 4, or 8")
    environment = dict(parent)
    environment.pop("PYTHONPATH", None)
    value = str(thread_count)
    for name in THREAD_VARIABLES:
        environment[name] = value
    for name in PROCESS_VARIABLES:
        environment[name] = "1"
    for name in DYNAMIC_VARIABLES:
        environment[name] = "FALSE"
    environment["QUIMB_NUMBA_CACHE"] = QUIMB_NUMBA_CACHE
    environment["QUIMB_MPI_SPAWN"] = "False"
    for name in (*MPI_PRESENCE_VARIABLES, *NUMBA_LAYER_VARIABLES):
        environment.pop(name, None)
    environment["CUDA_VISIBLE_DEVICES"] = ""
    environment["PYTHONHASHSEED"] = "0"
    return environment


def _is_plain_int(value: Any, *, minimum: int | None = None) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and (minimum is None or value >= minimum)
    )


def _live_git_value(*args: str) -> str:
    completed = subprocess.run(
        ("git", "-C", str(_FORK_ROOT), *args),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


_LIVE_RUNTIME_IDENTITY_CACHE: dict[str, Mapping[str, Any]] = {}


def _live_fork_runtime_identity(
    python_executable: Path | str,
) -> Mapping[str, Any]:
    executable = str(Path(python_executable).resolve(strict=True))
    cached = _LIVE_RUNTIME_IDENTITY_CACHE.get(executable)
    if cached is not None:
        return cached
    probe = (
        "import json,numpy,quimb,stim,sys;"
        "print(json.dumps({"
        "'python_executable':sys.executable,"
        "'python_version':sys.version,"
        "'numpy_version':numpy.__version__,"
        "'stim_version':getattr(stim,'__version__',None),"
        "'quimb_import_origin':quimb.__file__,"
        "'quimb_version':quimb.__version__"
        "},sort_keys=True))"
    )
    completed = subprocess.run(
        (executable, "-c", probe),
        cwd=_REPOSITORY,
        env=child_environment(os.environ, thread_count=1),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60.0,
    )
    if completed.returncode != 0 or completed.stderr:
        raise RuntimeError(
            "fork runtime identity probe failed: "
            + completed.stderr.decode("utf-8", errors="replace")[-4000:]
        )
    identity = dict(
        _parse_json(completed.stdout, name="fork runtime identity probe")
    )
    expected_keys = {
        "python_executable",
        "python_version",
        "numpy_version",
        "stim_version",
        "quimb_import_origin",
        "quimb_version",
    }
    if set(identity) != expected_keys:
        raise ValueError("fork runtime identity probe key set drifted")
    identity["python_executable"] = str(
        Path(identity["python_executable"]).resolve(strict=True)
    )
    identity["quimb_import_origin"] = str(
        Path(identity["quimb_import_origin"]).resolve(strict=True)
    )
    _LIVE_RUNTIME_IDENTITY_CACHE[executable] = identity
    return identity


def _run_child(
    *,
    fixture_bytes: bytes,
    fork_python: Path,
    thread_count: int,
    strategy: str,
    shadow_evidence: bool,
    timeout_seconds: float,
    degenerate_boundary: str | None = None,
) -> dict[str, Any]:
    command = [
        str(fork_python),
        str(_WORKER),
        "--thread-count",
        str(thread_count),
        "--strategy",
        strategy,
    ]
    if degenerate_boundary is not None:
        if degenerate_boundary not in DEGENERATE_BOUNDARY_CHOICES:
            raise ValueError(
                "degenerate_boundary must be exactly 'trim_cluster'"
            )
        command.extend(("--degenerate-boundary", degenerate_boundary))
    if shadow_evidence:
        command.append("--shadow-evidence")
    environment = child_environment(
        os.environ,
        thread_count=thread_count,
    )
    wall_start = time.perf_counter_ns()
    completed = subprocess.run(
        command,
        cwd=_REPOSITORY,
        env=environment,
        input=fixture_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_seconds,
        check=False,
    )
    elapsed = time.perf_counter_ns() - wall_start
    if completed.returncode != 0:
        raise RuntimeError(
            f"worker failed with code {completed.returncode}: "
            + completed.stderr.decode("utf-8", errors="replace")[-4000:]
        )
    if completed.stderr:
        raise RuntimeError(
            "worker emitted unexpected stderr: "
            + completed.stderr.decode("utf-8", errors="replace")[-4000:]
        )
    core = dict(_parse_json(completed.stdout, name="worker stdout"))
    core["supervisor_process_receipt"] = {
        "thread_count": thread_count,
        "strategy": strategy,
        "shadow_evidence": shadow_evidence,
        "returncode": completed.returncode,
        "parent_observed_wall_duration_ns": elapsed,
        "stdout_nbytes": len(completed.stdout),
        "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
        "stderr_nbytes": 0,
    }
    return core


def decode_raw_vector(payload: Mapping[str, Any], *, n_qubits: int):
    """Decode one exact c128 ndarray-v1 payload without coordinate changes."""

    import numpy as np

    expected_keys = {
        "encoding",
        "dtype",
        "shape",
        "order",
        "nbytes",
        "data_sha256",
        "data_base64",
    }
    if not isinstance(payload, Mapping) or set(payload) != expected_keys:
        raise ValueError("vector payload has the wrong exact key set")
    if (
        payload["encoding"] != "ndarray-v1"
        or payload["dtype"] != "<c16"
        or payload["shape"] != [1 << n_qubits]
        or payload["order"] != "C"
        or payload["nbytes"] != (1 << n_qubits) * 16
    ):
        raise ValueError("vector encoding identity drifted")
    try:
        raw = base64.b64decode(payload["data_base64"], validate=True)
    except (ValueError, TypeError) as exc:
        raise ValueError("vector base64 is invalid") from exc
    if (
        len(raw) != payload["nbytes"]
        or hashlib.sha256(raw).hexdigest() != payload["data_sha256"]
    ):
        raise ValueError("vector byte identity failed")
    vector = np.frombuffer(raw, dtype=np.dtype("<c16")).copy()
    if (
        vector.shape != (1 << n_qubits,)
        or vector.dtype != np.dtype(np.complex128)
        or not vector.flags.c_contiguous
        or not np.isfinite(vector.real).all()
        or not np.isfinite(vector.imag).all()
    ):
        raise ValueError("decoded vector violates the raw c128 contract")
    return vector


def raw_complete_vector_metrics(
    reference,
    candidate,
    bands: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    """Compute the preregistered raw metrics with no phase or norm fitting.

    ``bands`` defaults to the committed exact-lane ``_BANDS``; the amended
    degenerate-boundary lane passes ``_STAGE0_AMENDED_BANDS`` explicitly.
    The band key set is pinned either way.
    """

    import numpy as np

    if bands is None:
        bands = _BANDS
    if not isinstance(bands, Mapping) or set(bands) != set(_BANDS):
        raise ValueError("acceptance band key set drifted")

    if (
        not isinstance(reference, np.ndarray)
        or not isinstance(candidate, np.ndarray)
        or reference.dtype != np.dtype(np.complex128)
        or candidate.dtype != np.dtype(np.complex128)
        or reference.ndim != 1
        or candidate.shape != reference.shape
        or reference.size == 0
        or not np.isfinite(reference).all()
        or not np.isfinite(candidate).all()
    ):
        raise ValueError("raw metric inputs must be same-shape finite c128 vectors")
    reference_mass = np.vdot(reference, reference)
    candidate_mass = np.vdot(candidate, candidate)
    overlap = np.vdot(reference, candidate)
    scalar_values = (
        reference_mass.real,
        reference_mass.imag,
        candidate_mass.real,
        candidate_mass.imag,
        overlap.real,
        overlap.imag,
    )
    if not all(math.isfinite(float(value)) for value in scalar_values):
        raise ValueError("raw inner products are non-finite")
    if reference_mass.real <= 0.0 or candidate_mass.real <= 0.0:
        raise ValueError("raw vector mass must be strictly positive")
    if (
        abs(float(reference_mass.imag)) > 1.0e-12
        or abs(float(candidate_mass.imag)) > 1.0e-12
    ):
        raise ValueError("raw norm-squared has an imaginary residual")
    fidelity_denominator = float(
        reference_mass.real * candidate_mass.real
    )
    if not math.isfinite(fidelity_denominator) or fidelity_denominator <= 0.0:
        raise ValueError("fidelity denominator is invalid")
    fidelity_raw = float(abs(overlap) ** 2 / fidelity_denominator)
    if not math.isfinite(fidelity_raw) or fidelity_raw < 0.0:
        raise ValueError("raw fidelity is invalid")
    correction = max(0.0, fidelity_raw - 1.0)
    if correction > bands["fidelity_roundoff_correction_max"]:
        raise ValueError("fidelity exceeds one beyond clipping allowance")
    fidelity = min(1.0, fidelity_raw)
    difference = candidate - reference
    d2 = float(np.linalg.norm(difference))
    dinf = float(np.max(np.abs(difference), initial=0.0))
    reference_norm = math.sqrt(float(reference_mass.real))
    candidate_norm = math.sqrt(float(candidate_mass.real))
    norm_sum = reference_norm + candidate_norm
    if not math.isfinite(norm_sum) or norm_sum <= 0.0:
        raise ValueError("raw norm sum is invalid")
    d_rel = 2.0 * d2 / norm_sum
    d_norm = 2.0 * abs(reference_norm - candidate_norm) / norm_sum
    metrics = {
        "dinf_raw": dinf,
        "d2_raw": d2,
        "relative_state_distance": d_rel,
        "relative_norm_distance": d_norm,
        "reference_raw_norm": reference_norm,
        "candidate_raw_norm": candidate_norm,
        "reference_raw_norm_squared": float(reference_mass.real),
        "candidate_raw_norm_squared": float(candidate_mass.real),
        "overlap_real": float(overlap.real),
        "overlap_imag": float(overlap.imag),
        "fidelity_denominator": fidelity_denominator,
        "fidelity_raw": fidelity_raw,
        "fidelity_roundoff_correction": correction,
        "fidelity": fidelity,
        "one_minus_fidelity": 1.0 - fidelity,
        "phase_fit": False,
        "normalization_before_comparison": False,
        "dtype_cast": False,
        "coordinate_permutation": False,
    }
    numeric = [
        value
        for value in metrics.values()
        if isinstance(value, float)
    ]
    if not all(math.isfinite(value) for value in numeric):
        raise ValueError("raw metric computation produced a non-finite value")
    gates = {
        "relative_state_distance": (
            d_rel <= bands["relative_state_distance_max"]
        ),
        "relative_norm_distance": (
            d_norm <= bands["relative_norm_distance_max"]
        ),
        "one_minus_fidelity": (
            1.0 - fidelity <= bands["one_minus_fidelity_max"]
        ),
        "fidelity_roundoff_correction": (
            correction
            <= bands["fidelity_roundoff_correction_max"]
        ),
    }
    return {
        "metrics": metrics,
        "bands": dict(bands),
        "gates": gates,
        "passed": all(gates.values()),
    }


def _checkpoint_vector(child: Mapping[str, Any], operation_index: int):
    row = child["checkpoints"][str(operation_index)]
    vector = decode_raw_vector(row["vector"], n_qubits=14)
    raw_sha = hashlib.sha256(vector.tobytes(order="C")).hexdigest()
    if (
        row["operation_index"] != operation_index
        or row["pre_metric"]["raw_vector_sha256"] != raw_sha
        or row["vector"]["data_sha256"] != raw_sha
    ):
        raise ValueError("checkpoint vector hashes do not join")
    return vector


def _metadata_projection(
    child: Mapping[str, Any],
    operation_index: int,
) -> dict[str, Any]:
    row = child["checkpoint_metadata"][str(operation_index)]
    required = (
        "operation_index",
        "round_index",
        "physical_request",
        "physical_pauli",
        "signed_pulled_word",
        "pullback",
        "strategy",
        "update_strategy",
        "routing_root",
        "routing_vertices",
        "routing_tree_edges",
        "configured_max_bond",
        "configured_cutoff",
    )
    if any(key not in row for key in required):
        raise ValueError("checkpoint metadata is incomplete")
    projection = {key: row[key] for key in required}
    if child["strategy"] == NATIVE_STRATEGY:
        for key in (
            "plan_digest_sha256",
            "canonical_gate_transcript",
            "candidate_kept_dimensions",
        ):
            if key not in row:
                raise ValueError("native checkpoint metadata is incomplete")
            projection[key] = row[key]
    return projection


def _is_lower_hex(value: Any, *, length: int) -> bool:
    return (
        isinstance(value, str)
        and len(value) == length
        and all(character in "0123456789abcdef" for character in value)
    )


def _validate_worker_envelope(
    child: Mapping[str, Any],
    *,
    thread_count: int,
    strategy: str,
    shadow_evidence: bool,
    degenerate_boundary: str | None = None,
) -> None:
    expected_keys = {
        "schema",
        "formal_claim_eligible",
        "faithfulness_claim",
        "performance_claim",
        "lane",
        "strategy",
        "legacy_diagnostic_only",
        "shadow_evidence_enabled",
        "environment",
        "fixture_identity",
        "split_policy",
        "operation_count",
        "checkpoint_metadata",
        "operation_records",
        "checkpoints",
        "shadow_builder_call_count",
        "shadow_span_count",
        "shadow_evidence_bytes",
        "shadow_builder_instrumentation",
        "source_identity",
        "stdout_write_included_in_timing",
        "claim_boundary",
        "result_projection_sha256",
        "timing",
        "supervisor_process_receipt",
    }
    if degenerate_boundary is not None:
        # Flag-mode-only worker metadata key; the default-mode top-level
        # key set is unchanged and rejects it.
        expected_keys.add("configured_degenerate_boundary")
    if set(child) != expected_keys:
        raise ValueError("worker top-level key set is not exact")

    expected_lane = (
        "gcapeps_native_finite_cap_development"
        if strategy == NATIVE_STRATEGY
        else "gcapeps_exact_tree_compress_diagnostic_only"
    )
    if (
        child["lane"] != expected_lane
        or child["legacy_diagnostic_only"]
        is not (strategy == LEGACY_STRATEGY)
        or child["stdout_write_included_in_timing"] is not False
        or not isinstance(child["claim_boundary"], str)
        or not child["claim_boundary"]
    ):
        raise ValueError("worker lane or claim boundary drifted")

    instrumentation = child["shadow_builder_instrumentation"]
    expected_instrumentation = {
        "no_shadow_uses_throwing_sentinel": (
            strategy == NATIVE_STRATEGY and not shadow_evidence
        ),
        "evidence_uses_counting_wrapper": (
            strategy == NATIVE_STRATEGY and shadow_evidence
        ),
        "original_builder_restored_before_return": True,
    }
    if instrumentation != expected_instrumentation:
        raise ValueError("shadow instrumentation receipt drifted")
    if shadow_evidence and (
        child["shadow_builder_call_count"] <= 0
        or child["shadow_span_count"]
        != child["shadow_builder_call_count"]
        or child["shadow_evidence_bytes"] <= 0
    ):
        raise ValueError("evidence child did not perform positive shadow work")

    source = child["source_identity"]
    source_keys = {
        "worker_source_sha256",
        "fixture_owner_source_sha256",
        "engine_source_sha256",
        "timing_owner_source_sha256",
        "native_source_sha256",
        "carrier_source_sha256",
        "fork",
        "python_executable",
        "python_version",
        "numpy_version",
        "stim_version",
    }
    if not isinstance(source, Mapping) or set(source) != source_keys:
        raise ValueError("worker source identity key set drifted")
    expected_sources = {
        "worker_source_sha256": _source_sha256(_WORKER),
        "fixture_owner_source_sha256": _source_sha256(_FIXTURE_OWNER),
        "engine_source_sha256": _source_sha256(
            _WORKER.with_name("gcapeps_finite_memory_engine.py")
        ),
        "timing_owner_source_sha256": _source_sha256(_TIMING_OWNER),
        "native_source_sha256": _source_sha256(
            _REPOSITORY
            / "external/forks/quimb-gcapeps/"
            "quimb/experimental/gcapeps/native.py"
        ),
        "carrier_source_sha256": _source_sha256(
            _REPOSITORY
            / "external/forks/quimb-gcapeps/"
            "quimb/experimental/gcapeps/carrier.py"
        ),
    }
    if any(source[key] != value for key, value in expected_sources.items()):
        raise ValueError("worker source hash disagrees with the live source")
    if not isinstance(source["python_executable"], str):
        raise ValueError("worker runtime identity is invalid")
    live_runtime = _live_fork_runtime_identity(source["python_executable"])
    live_fork_root = _FORK_ROOT.resolve(strict=True)
    live_fork_identity = {
        "root": str(live_fork_root),
        "commit": _live_git_value("rev-parse", "HEAD"),
        "tree": _live_git_value("rev-parse", "HEAD^{tree}"),
        "worktree_clean": (
            _live_git_value(
                "status",
                "--porcelain",
                "--untracked-files=all",
            )
            == ""
        ),
        "quimb_import_origin": live_runtime["quimb_import_origin"],
        "quimb_version": live_runtime["quimb_version"],
    }
    fork = source["fork"]
    if (
        not isinstance(fork, Mapping)
        or set(fork)
        != set(live_fork_identity)
        or dict(fork) != live_fork_identity
        or live_fork_identity["worktree_clean"] is not True
        or Path(live_fork_identity["quimb_import_origin"])
        != (live_fork_root / "quimb/__init__.py").resolve(strict=True)
    ):
        raise ValueError("worker fork identity is invalid")
    if (
        source["python_executable"] != live_runtime["python_executable"]
        or source["python_version"] != live_runtime["python_version"]
        or source["numpy_version"] != live_runtime["numpy_version"]
        or source["stim_version"] != live_runtime["stim_version"]
    ):
        raise ValueError("worker runtime identity is invalid")

    receipt = child["supervisor_process_receipt"]
    if (
        not isinstance(receipt, Mapping)
        or set(receipt)
        != {
            "thread_count",
            "strategy",
            "shadow_evidence",
            "returncode",
            "parent_observed_wall_duration_ns",
            "stdout_nbytes",
            "stdout_sha256",
            "stderr_nbytes",
        }
        or not _is_plain_int(receipt["thread_count"], minimum=1)
        or receipt["thread_count"] != thread_count
        or receipt["strategy"] != strategy
        or receipt["shadow_evidence"] is not shadow_evidence
        or not _is_plain_int(receipt["returncode"], minimum=0)
        or receipt["returncode"] != 0
        or not _is_plain_int(
            receipt["parent_observed_wall_duration_ns"], minimum=1
        )
        or not _is_plain_int(receipt["stdout_nbytes"], minimum=1)
        or not _is_plain_int(receipt["stderr_nbytes"], minimum=0)
        or receipt["stderr_nbytes"] != 0
    ):
        raise ValueError("supervisor process receipt is invalid")

    worker_payload = {
        key: value
        for key, value in child.items()
        if key != "supervisor_process_receipt"
    }
    worker_stdout = _canonical_json_bytes(worker_payload) + b"\n"
    if (
        receipt["stdout_nbytes"] != len(worker_stdout)
        or receipt["stdout_sha256"]
        != hashlib.sha256(worker_stdout).hexdigest()
    ):
        raise ValueError("supervisor stdout receipt does not authenticate child")
    projection = {
        key: value
        for key, value in worker_payload.items()
        if key != "result_projection_sha256"
    }
    if child["result_projection_sha256"] != _projection_sha256(projection):
        raise ValueError("worker result projection hash disagrees")


def _validate_child_identity(
    child: Mapping[str, Any],
    *,
    fixture: Mapping[str, Any],
    thread_count: int,
    strategy: str,
    shadow_evidence: bool,
    degenerate_boundary: str | None = None,
) -> None:
    if child.get("schema") != (
        "error_coupling_simulator.external.gcapeps_finite_memory."
        "native_thread_worker.v1"
    ):
        raise ValueError("worker schema drifted")
    identity = child["fixture_identity"]
    expected_identity_keys = {
        "case_id",
        "fixture_projection_sha256",
        "operation_prefix_count",
        "operation_prefix_sha256",
        "input_id",
        "stop_after_operation",
        "checkpoint_operations",
    }
    prefix = _fixture_operation_prefix(fixture)
    expected_prefix_hash = _projection_sha256(prefix)
    if (
        not isinstance(identity, Mapping)
        or set(identity) != expected_identity_keys
        or child["formal_claim_eligible"] is not False
        or child["faithfulness_claim"] is not False
        or child["performance_claim"] is not False
        or child["strategy"] != strategy
        or child["shadow_evidence_enabled"] is not shadow_evidence
        or identity["case_id"] != fixture["case_id"]
        or identity["operation_prefix_count"] != len(prefix)
        or identity["operation_prefix_sha256"] != expected_prefix_hash
        or identity["fixture_projection_sha256"]
        != fixture["result_projection_sha256"]
        or identity["input_id"] != INPUT_ID
        or identity["stop_after_operation"] != STOP_AFTER_OPERATION
        or identity["checkpoint_operations"]
        != list(CHECKPOINT_OPERATIONS)
        or child["operation_count"] != len(prefix)
    ):
        raise ValueError("worker identity disagrees with the T3 request")
    environment = child["environment"]
    if (
        environment["requested_thread_count"] != thread_count
        or environment["CUDA_VISIBLE_DEVICES"] != ""
        or environment["PYTHONHASHSEED"] != "0"
        or environment["PYTHONPATH_present"] is not False
        or environment[
            "validated_before_numpy_quimb_stim_import"
        ] is not True
        or any(
            environment["thread_variables"][name] != str(thread_count)
            for name in THREAD_VARIABLES
        )
        or any(
            environment["process_variables"][name] != "1"
            for name in PROCESS_VARIABLES
        )
        or any(
            environment["dynamic_variables"][name] != "FALSE"
            for name in DYNAMIC_VARIABLES
        )
        or environment["QUIMB_NUMBA_CACHE"] != QUIMB_NUMBA_CACHE
        or environment["QUIMB_MPI_SPAWN"] != "False"
        or environment["mpi_presence_variables_present"] != []
        or environment["numba_layer_variables_present"] != []
    ):
        raise ValueError("worker environment receipt is invalid")
    expected_split_policy = dict(EXPECTED_SPLIT_POLICY)
    if degenerate_boundary is not None:
        if degenerate_boundary not in DEGENERATE_BOUNDARY_CHOICES:
            raise ValueError(
                "degenerate_boundary must be exactly 'trim_cluster'"
            )
        expected_split_policy["degenerate_boundary"] = degenerate_boundary
    if child.get("split_policy") != expected_split_policy:
        raise ValueError("worker split policy drifted")
    if degenerate_boundary is not None and (
        child.get("configured_degenerate_boundary") != degenerate_boundary
    ):
        raise ValueError("worker degenerate-boundary receipt drifted")
    if not shadow_evidence and (
        child["shadow_builder_call_count"] != 0
        or child["shadow_span_count"] != 0
        or child["shadow_evidence_bytes"] != 0
    ):
        raise ValueError("no-shadow worker performed shadow work")
    for operation_index in CHECKPOINT_OPERATIONS:
        _checkpoint_vector(child, operation_index)
        _metadata_projection(child, operation_index)
    _timing_inventory(child)
    if strategy == NATIVE_STRATEGY:
        _validate_native_operation_ledgers(
            child,
            shadow_evidence=shadow_evidence,
            degenerate_boundary=degenerate_boundary,
        )
    _validate_worker_envelope(
        child,
        thread_count=thread_count,
        strategy=strategy,
        shadow_evidence=shadow_evidence,
        degenerate_boundary=degenerate_boundary,
    )


def _kept_dimension_diagnostic(
    left_kept: Any,
    right_kept: Any,
) -> dict[str, Any]:
    """Demoted cross-thread kept-dimension comparison for the trim lane.

    The list length (split structure) must agree exactly; element-wise
    kept dimensions are recorded as a diagnostic instead of gating, per
    ``_STAGE0_KEPT_DIMENSION_EXCLUSION_JUSTIFICATION``.
    """

    structure_equal = (
        isinstance(left_kept, list)
        and isinstance(right_kept, list)
        and len(left_kept) == len(right_kept)
        and all(
            _is_plain_int(value, minimum=1)
            for value in (*left_kept, *right_kept)
        )
    )
    if not structure_equal:
        return {
            "excluded_from_exact_equality": True,
            "structure_equal": False,
            "split_count": None,
            "mismatch_count": None,
            "max_abs_difference": None,
            "mismatches": None,
        }
    mismatches = [
        {
            "split_index": split_index,
            "left_kept": left_value,
            "right_kept": right_value,
        }
        for split_index, (left_value, right_value) in enumerate(
            zip(left_kept, right_kept)
        )
        if left_value != right_value
    ]
    return {
        "excluded_from_exact_equality": True,
        "structure_equal": True,
        "split_count": len(left_kept),
        "mismatch_count": len(mismatches),
        "max_abs_difference": max(
            (
                abs(row["left_kept"] - row["right_kept"])
                for row in mismatches
            ),
            default=0,
        ),
        "mismatches": mismatches,
    }


def _pair_comparison(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    *,
    name: str,
    bands: Mapping[str, float] | None = None,
    degenerate_boundary: str | None = None,
) -> dict[str, Any]:
    if degenerate_boundary is not None and (
        degenerate_boundary not in DEGENERATE_BOUNDARY_CHOICES
    ):
        raise ValueError("degenerate_boundary must be exactly 'trim_cluster'")
    checkpoints = {}
    for operation_index in CHECKPOINT_OPERATIONS:
        left_vector = _checkpoint_vector(left, operation_index)
        right_vector = _checkpoint_vector(right, operation_index)
        metrics = raw_complete_vector_metrics(
            left_vector,
            right_vector,
            bands=bands,
        )
        left_metadata = _metadata_projection(left, operation_index)
        right_metadata = _metadata_projection(right, operation_index)
        if degenerate_boundary is None:
            metadata_equal = (
                _canonical_json_bytes(left_metadata)
                == _canonical_json_bytes(right_metadata)
            )
            checkpoints[str(operation_index)] = {
                "operation_index": operation_index,
                "raw_metrics": metrics,
                "exact_metadata_equal": metadata_equal,
                "left_metadata_projection_sha256": _projection_sha256(
                    left_metadata
                ),
                "right_metadata_projection_sha256": _projection_sha256(
                    right_metadata
                ),
                "passed": metrics["passed"] and metadata_equal,
            }
            continue
        # Trim lane only: per-split kept dimensions are ulp-sensitive to
        # thread-dependent BLAS at noise-floor tie clusters and are
        # demoted to a recorded diagnostic; everything else in the
        # projection stays strictly equality-checked.
        left_core = {
            key: value
            for key, value in left_metadata.items()
            if key != "candidate_kept_dimensions"
        }
        right_core = {
            key: value
            for key, value in right_metadata.items()
            if key != "candidate_kept_dimensions"
        }
        metadata_equal = (
            _canonical_json_bytes(left_core)
            == _canonical_json_bytes(right_core)
        )
        kept_diagnostic = _kept_dimension_diagnostic(
            left_metadata.get("candidate_kept_dimensions"),
            right_metadata.get("candidate_kept_dimensions"),
        )
        checkpoints[str(operation_index)] = {
            "operation_index": operation_index,
            "raw_metrics": metrics,
            "exact_metadata_equal": metadata_equal,
            "kept_dimensions_excluded_from_equality": True,
            "kept_dimension_diagnostic": kept_diagnostic,
            "left_metadata_projection_sha256": _projection_sha256(
                left_core
            ),
            "right_metadata_projection_sha256": _projection_sha256(
                right_core
            ),
            "passed": (
                metrics["passed"]
                and metadata_equal
                and kept_diagnostic["structure_equal"] is True
            ),
        }
    result = {
        "name": name,
        "phase_fit": False,
        "checkpoints": checkpoints,
        "passed": all(row["passed"] for row in checkpoints.values()),
    }
    if degenerate_boundary is not None:
        rows = [
            checkpoints[str(operation_index)]["kept_dimension_diagnostic"]
            for operation_index in CHECKPOINT_OPERATIONS
        ]
        result["kept_dimension_diagnostic"] = {
            "excluded_from_exact_equality": True,
            "structure_equal": all(
                row["structure_equal"] is True for row in rows
            ),
            "mismatch_count": sum(
                row["mismatch_count"]
                for row in rows
                if row["mismatch_count"] is not None
            ),
            "max_abs_difference": max(
                (
                    row["max_abs_difference"]
                    for row in rows
                    if row["max_abs_difference"] is not None
                ),
                default=0,
            ),
        }
    return result


def _finite_float(value: Any, *, name: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
    ):
        raise ValueError(f"{name} must be a finite number")
    return float(value)


def _float_matches(left: Any, right: Any) -> bool:
    return math.isclose(
        _finite_float(left, name="reported numerical value"),
        _finite_float(right, name="recomputed numerical value"),
        rel_tol=1.0e-12,
        abs_tol=1.0e-15,
    )


def _checked_spectrum(value: Any, *, name: str) -> list[float]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{name} must be a nonempty list")
    spectrum = [
        _finite_float(item, name=f"{name}[{index}]")
        for index, item in enumerate(value)
    ]
    if any(item < 0.0 for item in spectrum) or any(
        right > left for left, right in zip(spectrum, spectrum[1:])
    ):
        raise ValueError(f"{name} must be nonnegative and nonincreasing")
    if spectrum[0] <= 0.0:
        raise ValueError(f"{name} must have positive leading weight")
    return spectrum


def _relative_discarded_fraction(
    spectrum: Sequence[float],
    *,
    kept_dimension: int,
) -> float:
    scale = spectrum[0]
    normalized = [value / scale for value in spectrum]
    denominator = math.fsum(value * value for value in normalized)
    numerator = math.fsum(
        value * value for value in normalized[kept_dimension:]
    )
    if denominator <= 0.0:
        raise ValueError("spectrum has nonpositive normalized weight")
    return numerator / denominator


def _trim_cluster_expected_keep(spectrum: Sequence[float]) -> int:
    """Tie-aware kept dimension under the fork's ``trim_cluster`` rule at
    the frozen cap of 32.

    A binding cap moves its cut to the outer edge of a tied singular-value
    cluster (keep fewer, never more), decided from the singular values
    only: descending neighbors ``a >= b`` are tied iff
    ``(a - b) < _DEGENERATE_BOUNDARY_TIE_RTOL * a``, except that an exact
    zero ties only with exact zeros, and at least one value is kept. The
    worker payload round-trips float64 exactly through canonical JSON, so
    this recomputation reproduces the fork's decision bit-for-bit.
    """

    dimension = len(spectrum)
    if dimension <= 32:
        return dimension
    keep = 32
    while keep > 1:
        upper = spectrum[keep - 1]
        lower = spectrum[keep]
        if upper == 0.0:
            tied = lower == 0.0
        else:
            tied = (upper - lower) < _DEGENERATE_BOUNDARY_TIE_RTOL * upper
        if not tied:
            break
        keep -= 1
    return keep


def _check_split_degenerate_boundary(
    split: Mapping[str, Any],
    *,
    degenerate_boundary: str | None,
    name: str,
) -> None:
    """Pin the per-split ``configured_degenerate_boundary`` field exactly.

    The registered fork emits the field unconditionally (JSON ``null``
    when the option is absent); pre-landing payloads and the committed
    synthetic regression children omit it entirely. Default mode therefore
    accepts absent-or-null and loudly rejects any configured value; trim
    mode requires exact presence with the requested value.
    """

    present = "configured_degenerate_boundary" in split
    if degenerate_boundary is None:
        if present and split["configured_degenerate_boundary"] is not None:
            raise ValueError(
                f"{name} configured a degenerate boundary in default mode"
            )
        return
    if degenerate_boundary not in DEGENERATE_BOUNDARY_CHOICES:
        raise ValueError("degenerate_boundary must be exactly 'trim_cluster'")
    if (
        not present
        or split["configured_degenerate_boundary"] != degenerate_boundary
    ):
        raise ValueError(
            f"{name} does not record the requested degenerate boundary"
        )


def _validate_execution_split(
    split: Mapping[str, Any],
    *,
    shadow_evidence: bool,
    degenerate_boundary: str | None = None,
) -> dict[str, Any]:
    expected_keys = {
        "step_index",
        "gate_role",
        "gate_kind",
        "edge",
        "ordered_sites",
        "configured_max_bond",
        "configured_cutoff",
        "configured_cutoff_mode",
        "candidate_kept_bond_dimension",
        "cause",
        "full_singular_values",
        "full_bond_dimension",
        "discarded_fraction",
        "dimension_reduced",
    }
    if (
        not isinstance(split, Mapping)
        or set(split) - {"configured_degenerate_boundary"} != expected_keys
    ):
        raise ValueError("native execution split key set drifted")
    _check_split_degenerate_boundary(
        split,
        degenerate_boundary=degenerate_boundary,
        name="native execution split",
    )
    step_index = split["step_index"]
    kept_dimension = split["candidate_kept_bond_dimension"]
    edge = split["edge"]
    ordered_sites = split["ordered_sites"]
    if (
        not _is_plain_int(step_index, minimum=0)
        or not isinstance(split["gate_role"], str)
        or not split["gate_role"]
        or split["gate_kind"] not in {"SWAP", "CX"}
        or not isinstance(edge, list)
        or not isinstance(ordered_sites, list)
        or len(edge) != 2
        or len(ordered_sites) != 2
        or any(not _is_plain_int(site, minimum=0) for site in edge)
        or any(
            not _is_plain_int(site, minimum=0) for site in ordered_sites
        )
        or sorted(edge) != sorted(ordered_sites)
        or len(set(edge)) != 2
        or split["configured_max_bond"] != 32
        or isinstance(split["configured_max_bond"], bool)
        or _finite_float(
            split["configured_cutoff"], name="configured cutoff"
        )
        != 0.0
        or split["configured_cutoff_mode"] != "rel"
        or not _is_plain_int(kept_dimension, minimum=1)
        or kept_dimension > 32
    ):
        raise ValueError("native execution split identity drifted")
    if not shadow_evidence:
        if (
            split["cause"] != _NO_SHADOW_CAUSE
            or split["full_singular_values"] is not None
            or split["full_bond_dimension"] is not None
            or split["discarded_fraction"] is not None
            or split["dimension_reduced"] is not None
        ):
            raise ValueError("no-shadow execution split contains evidence")
        return {"step_index": step_index, "kept_dimension": kept_dimension}

    spectrum = _checked_spectrum(
        split["full_singular_values"],
        name="full_singular_values",
    )
    full_dimension = split["full_bond_dimension"]
    if (
        not _is_plain_int(full_dimension, minimum=1)
        or full_dimension != len(spectrum)
    ):
        raise ValueError("native full bond dimension is inconsistent")
    if degenerate_boundary is None:
        expected_keep = min(full_dimension, 32)
    else:
        expected_keep = _trim_cluster_expected_keep(spectrum)
    expected_cause = "none" if expected_keep == full_dimension else "max_bond"
    expected_fraction = _relative_discarded_fraction(
        spectrum,
        kept_dimension=expected_keep,
    )
    if (
        kept_dimension != expected_keep
        or split["cause"] != expected_cause
        or not _float_matches(split["discarded_fraction"], expected_fraction)
        or split["dimension_reduced"] is not (
            expected_keep < full_dimension
        )
    ):
        raise ValueError("native execution split evidence is inconsistent")
    return {
        "step_index": step_index,
        "kept_dimension": kept_dimension,
        "spectrum": spectrum,
        "discarded_fraction": expected_fraction,
        "cause": expected_cause,
        "dimension_reduced": expected_keep < full_dimension,
    }


def _validate_truncation_ledger(
    ledger: Mapping[str, Any],
    *,
    execution_ledger: Mapping[str, Any],
    validated_splits: Sequence[Mapping[str, Any]],
    degenerate_boundary: str | None = None,
) -> None:
    expected_keys = {
        "compiler_revision",
        "plan_digest_sha256",
        "plan_step_count",
        "two_site_step_count",
        "split_records",
        "positive_discarded_event_count",
        "dimension_reduction_event_count",
        "total_discarded_squared_weight_diagnostic_only",
        "any_smudging_applied",
        "not_a_global_error_bound",
    }
    if not isinstance(ledger, Mapping) or set(ledger) != expected_keys:
        raise ValueError("native truncation ledger key set drifted")
    records = ledger["split_records"]
    execution_records = execution_ledger["split_records"]
    if (
        ledger["compiler_revision"] != execution_ledger["compiler_revision"]
        or ledger["plan_digest_sha256"]
        != execution_ledger["plan_digest_sha256"]
        or ledger["plan_step_count"] != execution_ledger["plan_step_count"]
        or ledger["two_site_step_count"]
        != execution_ledger["two_site_step_count"]
        or ledger["any_smudging_applied"]
        is not execution_ledger["any_smudging_applied"]
        or ledger["not_a_global_error_bound"] is not True
        or not isinstance(records, list)
        or len(records) != len(execution_records)
    ):
        raise ValueError("native truncation ledger identity drifted")

    positive_count = 0
    reduction_count = 0
    discarded_weights = []
    expected_split_keys = {
        "step_index",
        "gate_role",
        "edge",
        "ordered_sites",
        "configured_max_bond",
        "configured_cutoff",
        "configured_cutoff_mode",
        "full_singular_values",
        "kept_singular_values",
        "full_bond_dimension",
        "kept_bond_dimension",
        "pre_split_weight",
        "discarded_squared_weight",
        "discarded_fraction",
        "keep_by_cutoff",
        "keep_by_cap",
        "actual_keep",
        "cause",
        "dimension_reduced",
        "positive_discarded_weight",
        "positive_discarded_weight_threshold",
        "not_a_global_error_bound",
    }
    common_keys = {
        "step_index",
        "gate_role",
        "edge",
        "ordered_sites",
        "configured_max_bond",
        "configured_cutoff",
        "configured_cutoff_mode",
        "full_singular_values",
        "full_bond_dimension",
        "discarded_fraction",
        "cause",
        "dimension_reduced",
    }
    for record, execution, validated in zip(
        records, execution_records, validated_splits
    ):
        if (
            not isinstance(record, Mapping)
            or set(record) - {"configured_degenerate_boundary"}
            != expected_split_keys
        ):
            raise ValueError("native truncation split key set drifted")
        _check_split_degenerate_boundary(
            record,
            degenerate_boundary=degenerate_boundary,
            name="native truncation split",
        )
        if any(record[key] != execution[key] for key in common_keys):
            raise ValueError("execution and truncation split records differ")
        if ("configured_degenerate_boundary" in record) is not (
            "configured_degenerate_boundary" in execution
        ) or record.get("configured_degenerate_boundary") != execution.get(
            "configured_degenerate_boundary"
        ):
            raise ValueError("execution and truncation split records differ")
        spectrum = validated["spectrum"]
        kept_dimension = validated["kept_dimension"]
        kept_spectrum = _checked_spectrum(
            record["kept_singular_values"],
            name="kept_singular_values",
        )
        pre_weight = math.fsum(value * value for value in spectrum)
        discarded_weight = math.fsum(
            value * value for value in spectrum[kept_dimension:]
        )
        positive = discarded_weight > 1.0e-12
        expected_keep_by_cap = (
            min(len(spectrum), 32)
            if degenerate_boundary is None
            else _trim_cluster_expected_keep(spectrum)
        )
        if (
            record["kept_bond_dimension"] != kept_dimension
            or len(kept_spectrum) != kept_dimension
            or any(
                not _float_matches(left, right)
                for left, right in zip(
                    kept_spectrum, spectrum[:kept_dimension]
                )
            )
            or not _float_matches(record["pre_split_weight"], pre_weight)
            or not _float_matches(
                record["discarded_squared_weight"], discarded_weight
            )
            or record["keep_by_cutoff"] != len(spectrum)
            or record["keep_by_cap"] != expected_keep_by_cap
            or record["actual_keep"] != kept_dimension
            or record["positive_discarded_weight"] is not positive
            or record["positive_discarded_weight_threshold"] != 1.0e-12
            or record["not_a_global_error_bound"] is not True
        ):
            raise ValueError("native truncation split evidence is inconsistent")
        positive_count += int(positive)
        reduction_count += int(validated["dimension_reduced"])
        discarded_weights.append(discarded_weight)
    if (
        ledger["positive_discarded_event_count"] != positive_count
        or ledger["dimension_reduction_event_count"] != reduction_count
        or not _float_matches(
            ledger["total_discarded_squared_weight_diagnostic_only"],
            math.fsum(discarded_weights),
        )
    ):
        raise ValueError("native truncation aggregate is inconsistent")


def _validate_native_operation_ledgers(
    child: Mapping[str, Any],
    *,
    shadow_evidence: bool,
    degenerate_boundary: str | None = None,
) -> None:
    operations = child["operation_records"]
    if not isinstance(operations, list) or not operations:
        raise ValueError("native operation records must be a nonempty list")
    expected_ledger_keys = {
        "compiler_revision",
        "plan_digest_sha256",
        "plan_step_count",
        "one_site_step_count",
        "two_site_step_count",
        "candidate_gate_count_before",
        "candidate_gate_count_after",
        "shadow_evidence_enabled",
        "shadow_evidence_bytes",
        "split_records",
        "any_smudging_applied",
    }
    total_splits = 0
    total_shadow_bytes = 0
    by_operation = {}
    for operation in operations:
        if not isinstance(operation, Mapping):
            raise ValueError("native operation record must be a mapping")
        operation_index = operation["operation_index"]
        if (
            not _is_plain_int(operation_index, minimum=0)
            or operation_index in by_operation
            or operation["strategy"] != NATIVE_STRATEGY
        ):
            raise ValueError("native operation record identity drifted")
        by_operation[operation_index] = operation
        ledger = operation.get("native_execution_ledger")
        if not isinstance(ledger, Mapping) or set(ledger) != expected_ledger_keys:
            raise ValueError("native execution ledger key set drifted")
        split_records = ledger["split_records"]
        count_fields = (
            "plan_step_count",
            "one_site_step_count",
            "two_site_step_count",
            "candidate_gate_count_before",
            "candidate_gate_count_after",
            "shadow_evidence_bytes",
        )
        if (
            ledger["compiler_revision"] != "gcapeps_native_pauli_rotation.v1"
            or ledger["plan_digest_sha256"]
            != operation["plan_digest_sha256"]
            or any(
                not _is_plain_int(ledger[key], minimum=0)
                for key in count_fields
            )
            or ledger["one_site_step_count"]
            + ledger["two_site_step_count"]
            != ledger["plan_step_count"]
            or ledger["candidate_gate_count_after"]
            - ledger["candidate_gate_count_before"]
            != ledger["plan_step_count"]
            or ledger["shadow_evidence_enabled"] is not shadow_evidence
            or (ledger["shadow_evidence_bytes"] > 0) is not shadow_evidence
            or ledger["any_smudging_applied"] is not True
            or not isinstance(split_records, list)
            or len(split_records) != ledger["two_site_step_count"]
        ):
            raise ValueError("native execution ledger identity drifted")
        validated_splits = [
            _validate_execution_split(
                split,
                shadow_evidence=shadow_evidence,
                degenerate_boundary=degenerate_boundary,
            )
            for split in split_records
        ]
        step_indices = [row["step_index"] for row in validated_splits]
        if (
            step_indices != sorted(step_indices)
            or len(step_indices) != len(set(step_indices))
            or any(index >= ledger["plan_step_count"] for index in step_indices)
            or operation["candidate_kept_dimensions"]
            != [row["kept_dimension"] for row in validated_splits]
        ):
            raise ValueError("native execution split ordering drifted")
        truncation = operation.get("native_truncation_ledger")
        if shadow_evidence:
            _validate_truncation_ledger(
                truncation,
                execution_ledger=ledger,
                validated_splits=validated_splits,
                degenerate_boundary=degenerate_boundary,
            )
        elif truncation is not None:
            raise ValueError("no-shadow operation emitted truncation ledger")
        total_splits += len(split_records)
        total_shadow_bytes += ledger["shadow_evidence_bytes"]

    for operation_index in CHECKPOINT_OPERATIONS:
        if operation_index not in by_operation or (
            _canonical_json_bytes(child["checkpoint_metadata"][str(operation_index)])
            != _canonical_json_bytes(by_operation[operation_index])
        ):
            raise ValueError("checkpoint metadata differs from operation record")
    evidence_span_count = sum(
        row["scope"] == "evidence_shadow" for row in child["timing"]["spans"]
    )
    expected_shadow_count = total_splits if shadow_evidence else 0
    if (
        child["shadow_builder_call_count"] != expected_shadow_count
        or child["shadow_span_count"] != evidence_span_count
        or evidence_span_count != expected_shadow_count
        or child["shadow_evidence_bytes"] != total_shadow_bytes
        or (total_shadow_bytes > 0) is not shadow_evidence
    ):
        raise ValueError("native shadow accounting differs from ledgers/timing")


def select_nondegeneracy_witness(
    evidence_child: Mapping[str, Any],
    *,
    degenerate_boundary: str | None = None,
) -> dict[str, Any] | None:
    for operation in evidence_child["operation_records"]:
        ledger = operation.get("native_execution_ledger")
        if not isinstance(ledger, Mapping):
            continue
        for split_index, split in enumerate(ledger["split_records"]):
            full_dimension = split["full_bond_dimension"]
            kept_dimension = split["candidate_kept_bond_dimension"]
            fraction = split["discarded_fraction"]
            if degenerate_boundary is None:
                kept_matches_rule = kept_dimension == 32
            else:
                # Tie-aware rule: the binding cap keeps exactly the
                # trim_cluster dimension recomputed from the recorded
                # spectrum (never more than 32).
                spectrum = split.get("full_singular_values")
                kept_matches_rule = (
                    isinstance(spectrum, list)
                    and bool(spectrum)
                    and kept_dimension
                    == _trim_cluster_expected_keep(
                        _checked_spectrum(
                            spectrum,
                            name="full_singular_values",
                        )
                    )
                )
            if (
                isinstance(full_dimension, int)
                and not isinstance(full_dimension, bool)
                and full_dimension > 32
                and kept_matches_rule
                and split["cause"] == "max_bond"
                and isinstance(fraction, (int, float))
                and not isinstance(fraction, bool)
                and math.isfinite(float(fraction))
                and float(fraction) > 1.0e-12
            ):
                return {
                    "operation_index": operation["operation_index"],
                    "round_index": operation["round_index"],
                    "split_index": split_index,
                    "native_step_index": split["step_index"],
                    "edge": split["edge"],
                    "full_bond_dimension": full_dimension,
                    "kept_bond_dimension": kept_dimension,
                    "cause": split["cause"],
                    "discarded_fraction": float(fraction),
                }
    return None


def _timing_inventory(child: Mapping[str, Any]) -> dict[str, Any]:
    timing = child["timing"]
    timing_owner = _load_path(
        "_gcapeps_native_thread_timing_validator",
        _TIMING_OWNER,
    )
    timing_owner.validate_layered_timing(timing)
    if (
        timing["schema"]
        != (
            "error_coupling_simulator.external.gcapeps_finite_memory."
            "layered_timing.v1"
        )
        or timing["wall_clock"] != "time.perf_counter_ns"
        or timing["cpu_clock"] != "time.process_time_ns"
    ):
        raise ValueError("worker timing identity drifted")
    required_scopes = {
        "child_total",
        "initialization",
        "physical_operation",
        "named_algorithm_substep",
        "checkpoint_contraction",
        "serialization",
        "publication_accounting",
    }
    scopes = {row["scope"] for row in timing["spans"]}
    if not required_scopes.issubset(scopes):
        raise ValueError("worker timing lacks required scopes")
    totals = {}
    for row in timing["spans"]:
        key = f"{row['scope']}::{row['kind']}"
        aggregate = totals.setdefault(
            key,
            {
                "span_count": 0,
                "wall_duration_ns": 0,
                "cpu_duration_ns": 0,
            },
        )
        aggregate["span_count"] += 1
        aggregate["wall_duration_ns"] += row["wall_duration_ns"]
        aggregate["cpu_duration_ns"] += row["cpu_duration_ns"]
    return {
        "clock_identity": {
            "wall_clock": timing["wall_clock"],
            "cpu_clock": timing["cpu_clock"],
        },
        "raw_spans": timing["spans"],
        "aggregated_by_scope_and_kind": totals,
        "supervisor_process_receipt": child[
            "supervisor_process_receipt"
        ],
    }


def build_report(
    *,
    fixture: Mapping[str, Any],
    native_thread1: Mapping[str, Any],
    native_thread4: Mapping[str, Any],
    native_evidence_thread1: Mapping[str, Any],
    legacy_children: Sequence[Mapping[str, Any]] = (),
    native_thread2: Mapping[str, Any] | None = None,
    native_thread8: Mapping[str, Any] | None = None,
    degenerate_boundary: str | None = None,
) -> dict[str, Any]:
    if degenerate_boundary is not None:
        return _build_amended_report(
            fixture=fixture,
            native_thread1=native_thread1,
            native_thread2=native_thread2,
            native_thread4=native_thread4,
            native_thread8=native_thread8,
            native_evidence_thread1=native_evidence_thread1,
            legacy_children=legacy_children,
            degenerate_boundary=degenerate_boundary,
        )
    if native_thread2 is not None or native_thread8 is not None:
        raise ValueError(
            "thread-2/8 children require the degenerate-boundary lane"
        )
    _validate_child_identity(
        native_thread1,
        fixture=fixture,
        thread_count=1,
        strategy=NATIVE_STRATEGY,
        shadow_evidence=False,
    )
    _validate_child_identity(
        native_thread4,
        fixture=fixture,
        thread_count=4,
        strategy=NATIVE_STRATEGY,
        shadow_evidence=False,
    )
    _validate_child_identity(
        native_evidence_thread1,
        fixture=fixture,
        thread_count=1,
        strategy=NATIVE_STRATEGY,
        shadow_evidence=True,
    )
    thread_comparison = _pair_comparison(
        native_thread1,
        native_thread4,
        name="native_one_thread_vs_four_threads",
    )
    shadow_comparison = _pair_comparison(
        native_thread1,
        native_evidence_thread1,
        name="native_no_shadow_vs_evidence_shadow",
    )
    witness = select_nondegeneracy_witness(native_evidence_thread1)
    timing = {
        "native_threads1_no_shadow": _timing_inventory(native_thread1),
        "native_threads4_no_shadow": _timing_inventory(native_thread4),
        "native_threads1_evidence": _timing_inventory(
            native_evidence_thread1
        ),
    }
    legacy_report = None
    legacy_required_red = True
    if legacy_children:
        if len(legacy_children) != 2:
            raise ValueError("legacy diagnostic requires one and four threads")
        for thread_count, child in zip((1, 4), legacy_children):
            _validate_child_identity(
                child,
                fixture=fixture,
                thread_count=thread_count,
                strategy=LEGACY_STRATEGY,
                shadow_evidence=False,
            )
        legacy_comparison = _pair_comparison(
            legacy_children[0],
            legacy_children[1],
            name="legacy_diagnostic_one_thread_vs_four_threads",
        )
        legacy_report = {
            "lane": "gcapeps_exact_tree_compress_diagnostic_only",
            "formal_claim_eligible": False,
            "comparison": legacy_comparison,
            "violates_at_least_one_native_band_at_operation_100": (
                not legacy_comparison["checkpoints"]["100"]["passed"]
            ),
            "timing": {
                "threads1": _timing_inventory(legacy_children[0]),
                "threads4": _timing_inventory(legacy_children[1]),
            },
        }
        legacy_required_red = legacy_report[
            "violates_at_least_one_native_band_at_operation_100"
        ]
    passed = bool(
        thread_comparison["passed"]
        and shadow_comparison["passed"]
        and witness is not None
        and legacy_required_red
    )
    report = {
        "schema": SCHEMA,
        "formal_claim_eligible": False,
        "faithfulness_claim": False,
        "performance_claim": False,
        "selected_strategy": NATIVE_STRATEGY,
        "split_policy": dict(EXPECTED_SPLIT_POLICY),
        "fixture_identity": {
            "case_id": fixture["case_id"],
            "fixture_projection_sha256": fixture[
                "result_projection_sha256"
            ],
            "parameters": fixture["parameters"],
            "input_id": INPUT_ID,
            "checkpoint_operations": list(CHECKPOINT_OPERATIONS),
        },
        "thread_invariance": thread_comparison,
        "shadow_isolation": shadow_comparison,
        "nondegeneracy_witness": witness,
        "nondegeneracy_passed": witness is not None,
        "timing": timing,
        "raw_children": {
            "native_threads1_no_shadow": native_thread1,
            "native_threads4_no_shadow": native_thread4,
            "native_threads1_evidence": native_evidence_thread1,
        },
        "legacy_diagnostic": legacy_report,
        "dense_pairing": {
            "status": "not_run_by_this_regression",
            "role": "report_only_development_reference",
            "acceptance_band": None,
        },
        "passed": passed,
        "verdict": (
            "PASS_ENGINEERING_NATIVE_THREAD_REGRESSION"
            if passed
            else "FAIL_ENGINEERING_NATIVE_THREAD_REGRESSION"
        ),
        "claim_boundary": (
            "deterministic execution of one bounded finite-cap native "
            "algorithm prefix only; no whole-state faithfulness, generic "
            "PEPS, QEC Record, or speed conclusion"
        ),
        "source_identity": {
            "runner_source_sha256": _source_sha256(
                Path(__file__).resolve(strict=True)
            ),
            "worker_source_sha256": _source_sha256(_WORKER),
            "fixture_owner_source_sha256": _source_sha256(_FIXTURE_OWNER),
        },
        "result_projection_sha256": "",
    }
    report["result_projection_sha256"] = _projection_sha256(
        {
            key: value
            for key, value in report.items()
            if key != "result_projection_sha256"
        }
    )
    return report


def _build_amended_report(
    *,
    fixture: Mapping[str, Any],
    native_thread1: Mapping[str, Any],
    native_thread2: Mapping[str, Any] | None,
    native_thread4: Mapping[str, Any],
    native_thread8: Mapping[str, Any] | None,
    native_evidence_thread1: Mapping[str, Any],
    legacy_children: Sequence[Mapping[str, Any]],
    degenerate_boundary: str,
) -> dict[str, Any]:
    """Build the Stage-0 amended report: threads 1/2/4/8, all pairs,
    trim_cluster split policy, and the preregistered amended bands."""

    if degenerate_boundary not in DEGENERATE_BOUNDARY_CHOICES:
        raise ValueError("degenerate_boundary must be exactly 'trim_cluster'")
    if legacy_children:
        raise ValueError(
            "the amended degenerate-boundary lane does not run the legacy "
            "diagnostic"
        )
    children = {
        1: native_thread1,
        2: native_thread2,
        4: native_thread4,
        8: native_thread8,
    }
    if set(children) != set(AMENDED_THREAD_COUNTS):
        raise ValueError("amended lane thread census drifted")
    for thread_count, child in children.items():
        if child is None:
            raise ValueError(
                "the amended lane requires native children at threads "
                "1, 2, 4, and 8"
            )
        _validate_child_identity(
            child,
            fixture=fixture,
            thread_count=thread_count,
            strategy=NATIVE_STRATEGY,
            shadow_evidence=False,
            degenerate_boundary=degenerate_boundary,
        )
    _validate_child_identity(
        native_evidence_thread1,
        fixture=fixture,
        thread_count=1,
        strategy=NATIVE_STRATEGY,
        shadow_evidence=True,
        degenerate_boundary=degenerate_boundary,
    )
    pair_reports = {}
    for left_count, right_count in AMENDED_THREAD_PAIRS:
        name = f"native_threads{left_count}_vs_threads{right_count}"
        pair_reports[name] = _pair_comparison(
            children[left_count],
            children[right_count],
            name=name,
            bands=_STAGE0_AMENDED_BANDS,
            degenerate_boundary=degenerate_boundary,
        )
    thread_comparison = {
        "name": "native_all_pairs_threads_1_2_4_8",
        "thread_counts": list(AMENDED_THREAD_COUNTS),
        "pairs": pair_reports,
        "passed": all(row["passed"] for row in pair_reports.values()),
    }
    # Shadow isolation stays on the exact default bands and full strict
    # metadata equality (kept dimensions included): at a fixed thread
    # count the evidence replay must not perturb the committed path.
    shadow_comparison = _pair_comparison(
        native_thread1,
        native_evidence_thread1,
        name="native_no_shadow_vs_evidence_shadow",
        bands=_BANDS,
    )
    witness = select_nondegeneracy_witness(
        native_evidence_thread1,
        degenerate_boundary=degenerate_boundary,
    )
    timing = {
        "native_threads1_no_shadow": _timing_inventory(native_thread1),
        "native_threads2_no_shadow": _timing_inventory(native_thread2),
        "native_threads4_no_shadow": _timing_inventory(native_thread4),
        "native_threads8_no_shadow": _timing_inventory(native_thread8),
        "native_threads1_evidence": _timing_inventory(
            native_evidence_thread1
        ),
    }
    passed = bool(
        thread_comparison["passed"]
        and shadow_comparison["passed"]
        and witness is not None
    )
    expected_split_policy = dict(EXPECTED_SPLIT_POLICY)
    expected_split_policy["degenerate_boundary"] = degenerate_boundary
    report = {
        "schema": SCHEMA,
        "formal_claim_eligible": False,
        "faithfulness_claim": False,
        "performance_claim": False,
        "selected_strategy": NATIVE_STRATEGY,
        "degenerate_boundary": degenerate_boundary,
        "split_policy": expected_split_policy,
        "applied_bands": {
            "band_set": _STAGE0_AMENDED_BAND_SET,
            "bands": dict(_STAGE0_AMENDED_BANDS),
            "shadow_isolation_bands": dict(_BANDS),
            "justification": _STAGE0_AMENDED_BANDS_JUSTIFICATION,
            "kept_dimension_exclusion_justification": (
                _STAGE0_KEPT_DIMENSION_EXCLUSION_JUSTIFICATION
            ),
        },
        "fixture_identity": {
            "case_id": fixture["case_id"],
            "fixture_projection_sha256": fixture[
                "result_projection_sha256"
            ],
            "parameters": fixture["parameters"],
            "input_id": INPUT_ID,
            "checkpoint_operations": list(CHECKPOINT_OPERATIONS),
        },
        "thread_invariance": thread_comparison,
        "shadow_isolation": shadow_comparison,
        "nondegeneracy_witness": witness,
        "nondegeneracy_passed": witness is not None,
        "timing": timing,
        "raw_children": {
            "native_threads1_no_shadow": native_thread1,
            "native_threads2_no_shadow": native_thread2,
            "native_threads4_no_shadow": native_thread4,
            "native_threads8_no_shadow": native_thread8,
            "native_threads1_evidence": native_evidence_thread1,
        },
        "legacy_diagnostic": None,
        "dense_pairing": {
            "status": "not_run_by_this_regression",
            "role": "report_only_development_reference",
            "acceptance_band": None,
        },
        "passed": passed,
        "verdict": (
            "PASS_ENGINEERING_NATIVE_THREAD_REGRESSION"
            if passed
            else "FAIL_ENGINEERING_NATIVE_THREAD_REGRESSION"
        ),
        "claim_boundary": (
            "deterministic execution of one bounded finite-cap native "
            "algorithm prefix only; no whole-state faithfulness, generic "
            "PEPS, QEC Record, or speed conclusion"
        ),
        "source_identity": {
            "runner_source_sha256": _source_sha256(
                Path(__file__).resolve(strict=True)
            ),
            "worker_source_sha256": _source_sha256(_WORKER),
            "fixture_owner_source_sha256": _source_sha256(_FIXTURE_OWNER),
        },
        "result_projection_sha256": "",
    }
    report["result_projection_sha256"] = _projection_sha256(
        {
            key: value
            for key, value in report.items()
            if key != "result_projection_sha256"
        }
    )
    return report


def run_regression(
    *,
    fork_python: Path,
    timeout_seconds: float,
    include_legacy_diagnostic: bool,
    degenerate_boundary: str | None = None,
) -> dict[str, Any]:
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0.0:
        raise ValueError("timeout_seconds must be finite and positive")
    fork_python = fork_python.resolve(strict=True)
    if not fork_python.is_file() or not os.access(fork_python, os.X_OK):
        raise ValueError("fork Python is not an executable file")
    fixture = build_frozen_fixture()
    fixture_bytes = _canonical_json_bytes(fixture)
    if degenerate_boundary is not None:
        if degenerate_boundary not in DEGENERATE_BOUNDARY_CHOICES:
            raise ValueError(
                "degenerate_boundary must be exactly 'trim_cluster'"
            )
        if include_legacy_diagnostic:
            raise ValueError(
                "the amended degenerate-boundary lane does not run the "
                "legacy diagnostic"
            )
        children = {}
        for thread_count in AMENDED_THREAD_COUNTS:
            children[thread_count] = _run_child(
                fixture_bytes=fixture_bytes,
                fork_python=fork_python,
                thread_count=thread_count,
                strategy=NATIVE_STRATEGY,
                shadow_evidence=False,
                timeout_seconds=timeout_seconds,
                degenerate_boundary=degenerate_boundary,
            )
        native_evidence = _run_child(
            fixture_bytes=fixture_bytes,
            fork_python=fork_python,
            thread_count=1,
            strategy=NATIVE_STRATEGY,
            shadow_evidence=True,
            timeout_seconds=timeout_seconds,
            degenerate_boundary=degenerate_boundary,
        )
        return build_report(
            fixture=fixture,
            native_thread1=children[1],
            native_thread2=children[2],
            native_thread4=children[4],
            native_thread8=children[8],
            native_evidence_thread1=native_evidence,
            degenerate_boundary=degenerate_boundary,
        )
    native_thread1 = _run_child(
        fixture_bytes=fixture_bytes,
        fork_python=fork_python,
        thread_count=1,
        strategy=NATIVE_STRATEGY,
        shadow_evidence=False,
        timeout_seconds=timeout_seconds,
    )
    native_thread4 = _run_child(
        fixture_bytes=fixture_bytes,
        fork_python=fork_python,
        thread_count=4,
        strategy=NATIVE_STRATEGY,
        shadow_evidence=False,
        timeout_seconds=timeout_seconds,
    )
    native_evidence = _run_child(
        fixture_bytes=fixture_bytes,
        fork_python=fork_python,
        thread_count=1,
        strategy=NATIVE_STRATEGY,
        shadow_evidence=True,
        timeout_seconds=timeout_seconds,
    )
    legacy = []
    if include_legacy_diagnostic:
        for thread_count in (1, 4):
            legacy.append(
                _run_child(
                    fixture_bytes=fixture_bytes,
                    fork_python=fork_python,
                    thread_count=thread_count,
                    strategy=LEGACY_STRATEGY,
                    shadow_evidence=False,
                    timeout_seconds=timeout_seconds,
                )
            )
    return build_report(
        fixture=fixture,
        native_thread1=native_thread1,
        native_thread4=native_thread4,
        native_evidence_thread1=native_evidence,
        legacy_children=legacy,
    )


def _publish_fresh(path: Path, payload: bytes) -> None:
    target = path.resolve(strict=False)
    parent = target.parent.resolve(strict=True)
    if target.exists():
        raise FileExistsError(f"output already exists: {target}")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        directory_fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fork-python-executable",
        type=Path,
        default=_DEFAULT_FORK_PYTHON,
    )
    parser.add_argument("--timeout-seconds", type=float, default=3600.0)
    parser.add_argument(
        "--include-legacy-diagnostic",
        action="store_true",
        help="also run the explicitly ineligible legacy one/four-thread lane",
    )
    parser.add_argument(
        "--degenerate-boundary",
        choices=DEGENERATE_BOUNDARY_CHOICES,
        default=None,
        help=(
            "opt-in Stage-0 amended lane: forward the fork's degeneracy-"
            "aware boundary trim to every worker, run native children at "
            "threads 1/2/4/8, and gate all pairs on the preregistered "
            "amended bands; absent means the committed default regression"
        ),
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    report = run_regression(
        fork_python=args.fork_python_executable,
        timeout_seconds=args.timeout_seconds,
        include_legacy_diagnostic=args.include_legacy_diagnostic,
        degenerate_boundary=args.degenerate_boundary,
    )
    encoded = _canonical_json_bytes(report) + b"\n"
    if args.output is None:
        sys.stdout.buffer.write(encoded)
        sys.stdout.buffer.flush()
    else:
        _publish_fresh(args.output, encoded)
        summary = {
            "schema": report["schema"],
            "verdict": report["verdict"],
            "passed": report["passed"],
            "formal_claim_eligible": False,
            "output": str(args.output.resolve(strict=True)),
            "output_sha256": hashlib.sha256(encoded).hexdigest(),
        }
        sys.stdout.buffer.write(_canonical_json_bytes(summary) + b"\n")
        sys.stdout.buffer.flush()
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
