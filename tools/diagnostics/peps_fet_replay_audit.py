#!/usr/bin/env python3
"""Fresh-process replay audit for the bounded d3 PEPS/FET trajectory.

This is a diagnostic adapter around the current production modules.  It does not
change the FET solver, the trajectory, or the external baseline repositories.  A
parent process launches each case in a new process, captures every applied FET map,
and compares:

* a same-seed fresh-process repetition;
* a different CUDA global seed; and
* the behavior-identical ``FET_FIDCURVE_DEBUG=1`` path.

The independent GF(2) entropy reference and the dense-state entropy read are
diagnostic state-level checks.  Neither a replay pass nor a local ``Fid_gamma``
pass certifies the complete detector/observable record law.
"""

from __future__ import annotations

import argparse
from contextlib import nullcontext
import copy
import hashlib
import importlib.metadata
import importlib.util
import inspect
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from typing import Any, Iterable, Sequence


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "error_coupling_simulator.peps.fet_replay_audit.v2"
WORKER_SCHEMA = "error_coupling_simulator.peps.fet_replay_audit.worker.v2"
DEFAULT_OUTPUT = Path(
    "outputs/simulator_validation/diagnostics/peps_fet_replay_audit/report.json"
)
DEFAULT_CASES = ((0, 0, 0), (0, 0, 1), (1, 0, 0), (0, 1, 0))

PATCH = "d3_at_q6_7"
G_SEEP = 0.09
G_HEAT = 0.0
B_BIAS = 0.9
ARM = "A"
READOUT_CONV = "biased_b"
LOGICAL_M = 0
FIT_SEED = 0
BASE_SEED = 2026
LEAKAGE_RATE = 0.0
EPS_FID = 1.0e-8
CUT_A = (0, 1, 2, 3)
ENTROPY_REFERENCE = 2.0
ENTROPY_TOL = 1.0e-4
LEAK_MASS_TOL = 1.0e-6

# Replay comparisons are intentionally much tighter than the scientific entropy
# gate.  Projective array differences remove only an overall complex scale/phase.
FID_REPLAY_TOL = 1.0e-10
ENTROPY_REPLAY_TOL = 1.0e-10
ARRAY_REPLAY_TOL = 1.0e-10
SCALAR_REPLAY_TOL = 1.0e-10
FET_IDENTITY_RELATIVE_TOL = 1.0e-12
REQUIRED_COMPARISON_KINDS = frozenset(
    {
        "fresh_process_repeat",
        "cuda_seed_sensitivity",
        "fidcurve_debug_invariance",
    }
)
STATIC_EXECUTION_BINDINGS = {
    "diagnostic": Path("tools/diagnostics/peps_fet_replay_audit.py"),
    "peps_init": Path("src/error_coupling_simulator/carrier/peps/__init__.py"),
    "peps_fet": Path("src/error_coupling_simulator/carrier/peps/fet.py"),
    "peps_trajectory": Path(
        "src/error_coupling_simulator/carrier/peps/trajectory.py"
    ),
    "peps_state": Path("src/error_coupling_simulator/carrier/peps/state.py"),
    "peps_contraction": Path(
        "src/error_coupling_simulator/carrier/peps/contraction.py"
    ),
    "peps_diagnostics": Path(
        "src/error_coupling_simulator/carrier/peps/diagnostics.py"
    ),
    "peps_sampling_maps": Path(
        "src/error_coupling_simulator/carrier/peps/sampling_maps.py"
    ),
    "peps_stab_tt": Path(
        "src/error_coupling_simulator/carrier/peps/stab_tt.py"
    ),
    "pepo_dynamics": Path(
        "src/error_coupling_simulator/carrier/pepo/dynamics.py"
    ),
    "pepo_sampler": Path("src/error_coupling_simulator/carrier/pepo/sampler.py"),
    "pepo_layout": Path("src/error_coupling_simulator/carrier/pepo/layout.py"),
    "within_cycle": Path(
        "src/error_coupling_simulator/carrier/within_cycle.py"
    ),
    "records": Path("src/error_coupling_simulator/carrier/records.py"),
    "record_fold": Path("src/error_coupling_simulator/carrier/record_fold.py"),
    "xzzx_parser": Path("src/error_coupling_simulator/frontend/xzzx_parser.py"),
    "qutrit_leakage": Path(
        "src/error_coupling_simulator/mechanisms/qutrit_leakage.py"
    ),
    "numerics": Path("src/error_coupling_simulator/numerics.py"),
    "harness_proc": Path("tests/harness/proc.py"),
    "harness_gpu_pool": Path("tests/harness/gpu_pool.py"),
    "python_lock": Path("uv.lock"),
    "core_environment_lock": Path("core-environment-cu130.lock"),
    "environment_spec": Path("environment-ecs.yml"),
    "project_metadata": Path("pyproject.toml"),
}
_HARNESS_MODULES: dict[str, Any] = {}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def report_content_hash(report: dict[str, Any]) -> str:
    payload = copy.deepcopy(report)
    payload.pop("content_hash_sha256", None)
    return sha256_bytes(canonical_json_bytes(payload))


def write_json_atomic(path: Path, report: dict[str, Any]) -> str:
    """Publish stable, sorted JSON bytes and return their SHA-256."""

    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)
    return sha256_bytes(encoded)


def _finite_float(value: Any, *, name: str) -> float:
    out = float(value)
    if not math.isfinite(out):
        raise RuntimeError(f"{name} is non-finite: {out!r}")
    return out


def classify_fid_gamma(value: Any) -> dict[str, Any]:
    """Encode a possibly non-finite fidelity without emitting invalid JSON."""

    numeric = float(value)
    raw_repr = repr(numeric)
    if math.isfinite(numeric):
        classification = "finite"
        json_value: float | None = numeric
    elif math.isnan(numeric):
        classification = "nan"
        json_value = None
    elif numeric > 0.0:
        classification = "positive_infinity"
        json_value = None
    else:
        classification = "negative_infinity"
        json_value = None
    return {
        "classification": classification,
        "value": json_value,
        "raw_repr": raw_repr,
    }


def validate_fid_gamma_evidence(value: Any) -> dict[str, Any]:
    """Validate the exact JSON-safe fidelity evidence schema."""

    if not isinstance(value, dict) or set(value) != {
        "classification",
        "value",
        "raw_repr",
    }:
        raise ValueError("Fid_gamma evidence must have classification/value/raw_repr")
    classification = value["classification"]
    raw_repr = value["raw_repr"]
    if not isinstance(classification, str) or not isinstance(raw_repr, str):
        raise ValueError("Fid_gamma classification and raw_repr must be strings")
    if classification == "finite":
        numeric = value["value"]
        if isinstance(numeric, bool) or not isinstance(numeric, (int, float)):
            raise ValueError("finite Fid_gamma evidence must contain a numeric value")
        numeric = float(numeric)
        if not math.isfinite(numeric) or raw_repr != repr(numeric):
            raise ValueError("finite Fid_gamma evidence is internally inconsistent")
    else:
        expected_raw = {
            "nan": "nan",
            "positive_infinity": "inf",
            "negative_infinity": "-inf",
        }.get(classification)
        if expected_raw is None or value["value"] is not None:
            raise ValueError("non-finite Fid_gamma evidence has invalid classification/value")
        if raw_repr != expected_raw:
            raise ValueError("non-finite Fid_gamma evidence raw_repr is inconsistent")
    return {
        "classification": classification,
        "value": None if value["value"] is None else float(value["value"]),
        "raw_repr": raw_repr,
    }


def _coerce_fid_gamma_evidence(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return validate_fid_gamma_evidence(value)
    return classify_fid_gamma(value)


def _complex128_array(value: Any):
    import numpy as np

    return np.ascontiguousarray(np.asarray(value, dtype=np.complex128))


def array_sha256_c128le(value: Any) -> str:
    import numpy as np

    array = _complex128_array(value).astype(np.dtype("<c16"), copy=False)
    return sha256_bytes(array.tobytes(order="C"))


def projective_array(value: Any):
    """Normalize an array and fix its largest entry to positive real phase."""

    import numpy as np

    array = _complex128_array(value).reshape(-1).copy()
    norm = float(np.linalg.norm(array))
    if not math.isfinite(norm) or norm <= 0.0:
        raise ValueError("projective_array requires a finite nonzero array")
    array /= norm
    pivot = int(np.argmax(np.abs(array)))
    phase = array[pivot] / abs(array[pivot])
    array /= phase
    # Remove signed zero, which has no numerical or physical significance but
    # otherwise creates distinct byte hashes.
    real = array.real.copy()
    imag = array.imag.copy()
    real[real == 0.0] = 0.0
    imag[imag == 0.0] = 0.0
    return np.ascontiguousarray(real + 1j * imag)


def projective_array_sha256(value: Any) -> str:
    return array_sha256_c128le(projective_array(value))


def projective_array_distance(left: Any, right: Any) -> dict[str, Any]:
    """Scale/phase-invariant L2 and max-entry distance between two arrays."""

    import numpy as np

    a = _complex128_array(left).reshape(-1)
    b = _complex128_array(right).reshape(-1)
    if a.shape != b.shape:
        return {
            "comparable": False,
            "reason": "shape_mismatch",
            "l2": None,
            "max_abs": None,
        }
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if not (math.isfinite(na) and math.isfinite(nb)) or na <= 0.0 or nb <= 0.0:
        return {
            "comparable": False,
            "reason": "nonfinite_or_zero_norm",
            "l2": None,
            "max_abs": None,
        }
    a = a / na
    b = b / nb
    overlap = np.vdot(a, b)
    if abs(overlap) > 0.0:
        b = b * (np.conj(overlap) / abs(overlap))
    delta = a - b
    return {
        "comparable": True,
        "reason": None,
        "l2": float(np.linalg.norm(delta)),
        "max_abs": float(np.max(np.abs(delta), initial=0.0)),
    }


def _gf2_rank(rows: Iterable[int]) -> int:
    basis: list[int] = []
    for row in rows:
        current = int(row)
        for pivot in basis:
            current = min(current, current ^ pivot)
        if current:
            basis.append(current)
            basis.sort(reverse=True)
    return len(basis)


def stabilizer_entropy_sa(
    generators: Sequence[dict[int, str]], n_sites: int, region_a: Sequence[int]
) -> float:
    """Pure GF(2) stabilizer entropy, independent of the PEPS/FET code path."""

    set_a = {int(site) for site in region_a}
    region_b = [site for site in range(int(n_sites)) if site not in set_a]
    b_index = {site: index for index, site in enumerate(region_b)}
    rows: list[int] = []
    for generator in generators:
        row = 0
        for site, pauli in generator.items():
            site = int(site)
            if site not in b_index:
                continue
            label = str(pauli).upper()
            if label == "X":
                row |= 1 << b_index[site]
            elif label == "Z":
                row |= 1 << (len(region_b) + b_index[site])
            else:
                raise ValueError(f"non-X/Z Pauli {pauli!r} at site {site}")
        rows.append(row)
    return float(_gf2_rank(rows) - len(region_b))


def dense_carrier_entropy(state: Any, region_a: Sequence[int]) -> dict[str, Any]:
    """Exact d3 dense entropy read with the leakage-off qubit projection."""

    import torch

    from error_coupling_simulator.carrier.peps import dense_psi

    n_sites = int(state.layout.n_data)
    psi = (
        torch.as_tensor(dense_psi(state))
        .reshape(-1)
        .detach()
        .to(torch.complex128)
        .cpu()
    )
    full_norm2 = _finite_float(torch.vdot(psi, psi).real, name="full state norm")
    psi3 = psi.reshape([3] * n_sites)
    psi2 = psi3[tuple(slice(0, 2) for _ in range(n_sites))].contiguous()
    qubit_norm2 = _finite_float(
        torch.vdot(psi2.reshape(-1), psi2.reshape(-1)).real,
        name="qubit-sector norm",
    )
    if full_norm2 <= 0.0 or qubit_norm2 <= 0.0:
        raise RuntimeError(
            f"nonpositive dense norm: full={full_norm2!r}, qubit={qubit_norm2!r}"
        )
    leak_mass = max(0.0, full_norm2 - qubit_norm2) / full_norm2
    psi2 = psi2 / math.sqrt(qubit_norm2)
    a_sites = sorted(int(site) for site in region_a)
    b_sites = [site for site in range(n_sites) if site not in a_sites]
    matrix = psi2.permute(*(a_sites + b_sites)).reshape(
        2 ** len(a_sites), 2 ** len(b_sites)
    )
    singular_values = torch.linalg.svdvals(matrix)
    probabilities = (singular_values * singular_values).real
    probabilities = probabilities / probabilities.sum()
    nonzero = probabilities[probabilities > 1.0e-15]
    entropy = _finite_float(
        -(nonzero * torch.log2(nonzero)).sum(), name="carrier entropy"
    )
    leading = float(singular_values[0]) if singular_values.numel() else 0.0
    rank = (
        int((singular_values > 1.0e-9 * leading).sum()) if leading > 0.0 else 0
    )
    return {
        "S_A": entropy,
        "leak_mass": float(leak_mass),
        "schmidt_rank": rank,
        "full_norm2": full_norm2,
        "qubit_norm2": qubit_norm2,
        "state": psi.numpy(),
    }


def evaluate_entropy_gate(
    *,
    entropy: float,
    reference: float,
    leak_mass: float,
    entropy_tolerance: float = ENTROPY_TOL,
    leak_mass_tolerance: float = LEAK_MASS_TOL,
) -> dict[str, Any]:
    """Evaluate the entropy equality only on a valid leakage-off state."""

    entropy = _finite_float(entropy, name="entropy gate S_A")
    reference = _finite_float(reference, name="entropy gate GF2 reference")
    leak_mass = _finite_float(leak_mass, name="entropy gate leak mass")
    if entropy_tolerance < 0.0 or leak_mass_tolerance < 0.0:
        raise ValueError("entropy and leak-mass tolerances must be nonnegative")
    entropy_deviation = abs(entropy - reference)
    entropy_matches = entropy_deviation <= float(entropy_tolerance)
    leakage_off = 0.0 <= leak_mass <= float(leak_mass_tolerance)
    return {
        "S_A": entropy,
        "GF2_reference": reference,
        "absolute_deviation": entropy_deviation,
        "tolerance": float(entropy_tolerance),
        "entropy_matches": bool(entropy_matches),
        "leak_mass": leak_mass,
        "leak_mass_tolerance": float(leak_mass_tolerance),
        "leakage_off_precondition_passed": bool(leakage_off),
        "verdict": "PASS" if entropy_matches and leakage_off else "RED",
    }


def evaluate_fet_cut_contract(
    *,
    map_array: Any,
    dim_in: int,
    dim_out: int,
    env_rank: int,
    fid_gamma: Any,
    eps_fid: float,
) -> dict[str, Any]:
    """Check that a failed FET target can only write back a genuine no-op."""

    import numpy as np

    dim_in = int(dim_in)
    dim_out = int(dim_out)
    env_rank = int(env_rank)
    if dim_in <= 0 or dim_out <= 0 or env_rank <= 0:
        raise ValueError("FET dimensions and rank must be positive")
    fid_evidence = _coerce_fid_gamma_evidence(fid_gamma)
    fid_gamma_value = fid_evidence["value"]
    fid_gamma_finite = fid_evidence["classification"] == "finite"
    eps_fid = _finite_float(eps_fid, name="FET contract eps_fid")
    if not 0.0 <= eps_fid < 1.0:
        raise ValueError(f"FET eps_fid must lie in [0, 1), got {eps_fid!r}")
    array = _complex128_array(map_array)
    if array.shape != (dim_in, dim_in):
        raise ValueError(
            f"FET map shape {array.shape} does not match dim_in={dim_in}"
        )
    if not np.isfinite(array.real).all() or not np.isfinite(array.imag).all():
        raise ValueError("FET contract map contains non-finite values")
    identity = np.eye(dim_in, dtype=np.complex128)
    identity_relative_error = float(
        np.linalg.norm(array - identity) / np.linalg.norm(identity)
    )
    fidelity_target = 1.0 - eps_fid
    target_met = bool(
        fid_gamma_finite and float(fid_gamma_value) >= fidelity_target
    )
    map_is_identity = identity_relative_error <= FET_IDENTITY_RELATIVE_TOL
    rank_reducing = dim_out < dim_in or env_rank < dim_in
    changed_writeback = rank_reducing or not map_is_identity
    fallback_violation = not target_met and changed_writeback
    nonfinite_violation = not fid_gamma_finite
    contract_violation = fallback_violation or nonfinite_violation
    if nonfinite_violation:
        verdict = "NONFINITE_FID_GAMMA"
    elif fallback_violation:
        verdict = "FALLBACK_CONTRACT_VIOLATION"
    elif target_met:
        verdict = "TARGET_MET"
    else:
        verdict = "SAFE_NOOP_FALLBACK"
    return {
        "fidelity_target": float(fidelity_target),
        "target_met": bool(target_met),
        "fid_gamma_finite": bool(fid_gamma_finite),
        "nonfinite_fid_gamma_violation": bool(nonfinite_violation),
        "map_vs_identity_relative_error": identity_relative_error,
        "identity_relative_tolerance": FET_IDENTITY_RELATIVE_TOL,
        "map_is_identity": bool(map_is_identity),
        "rank_reducing_writeback": bool(rank_reducing),
        "nonidentity_or_lossy_writeback": bool(changed_writeback),
        "fallback_contract_violation": bool(fallback_violation),
        "fet_contract_violation": bool(contract_violation),
        "fet_cut_contract_verdict": verdict,
    }


def aggregate_fet_fallback_contract(
    results: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate per-cut fallback violations without weakening replay evidence."""

    violations: list[dict[str, Any]] = []
    below_target: list[dict[str, Any]] = []
    nonfinite: list[dict[str, Any]] = []
    for result in results:
        identifier = str(result["case_id"])
        for cut in result["per_cut"]:
            row = {
                "case_id": identifier,
                "ordinal": int(cut["ordinal"]),
                "bond": str(cut["bond"]),
            }
            if bool(cut["fid_gamma_finite"]) and not bool(cut["target_met"]):
                below_target.append(row)
            if bool(cut["nonfinite_fid_gamma_violation"]):
                nonfinite.append(
                    {
                        **row,
                        "classification": cut["Fid_gamma"]["classification"],
                        "raw_repr": cut["Fid_gamma"]["raw_repr"],
                    }
                )
            if bool(cut["fet_contract_violation"]):
                violations.append(row)
    return {
        "verdict": "RED" if violations else "PASS",
        "violation_count": len(violations),
        "violations": violations,
        "below_target_count": len(below_target),
        "below_target_cuts": below_target,
        "nonfinite_fid_gamma_count": len(nonfinite),
        "nonfinite_fid_gamma_cuts": nonfinite,
        "rule": (
            "Fid_gamma must be finite; a finite cut below 1-eps_fid may only "
            "write back a full-rank identity no-op"
        ),
    }


def evaluate_overall_verdict(
    *, replay_verdict: str, entropy_red_case_ids: Sequence[str], fet_verdict: str
) -> str:
    """Keep a deterministic but scientifically invalid audit visibly RED."""

    passed = (
        str(replay_verdict).startswith("PASS_")
        and not entropy_red_case_ids
        and str(fet_verdict) == "PASS"
    )
    return "PASS" if passed else "RED"


def parse_case(text: str) -> tuple[int, int, int]:
    try:
        seed_text, debug_text, repetition_text = text.split(":")
        seed = int(seed_text)
        debug = int(debug_text)
        repetition = int(repetition_text)
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError(
            f"case must be CUDA_SEED:DEBUG_0_OR_1:REPETITION, got {text!r}"
        ) from exc
    if seed < 0 or debug not in (0, 1) or repetition < 0:
        raise argparse.ArgumentTypeError(
            f"invalid case {text!r}: require seed>=0, debug in {{0,1}}, repetition>=0"
        )
    return seed, debug, repetition


def case_id(case: tuple[int, int, int]) -> str:
    seed, debug, repetition = case
    return f"cuda_seed_{seed:010d}__debug_{debug}__rep_{repetition:03d}"


def comparison_kind(
    baseline_case: dict[str, int], candidate_case: dict[str, int]
) -> str:
    same_seed = baseline_case["cuda_seed"] == candidate_case["cuda_seed"]
    same_debug = baseline_case["fidcurve_debug"] == candidate_case["fidcurve_debug"]
    if same_seed and same_debug:
        return "fresh_process_repeat"
    if not same_seed and same_debug:
        return "cuda_seed_sensitivity"
    if same_seed and not same_debug:
        return "fidcurve_debug_invariance"
    return "combined_control_change"


def validate_case_matrix(cases: Sequence[tuple[int, int, int]]) -> set[str]:
    """Require all three fresh-process controls before any GPU worker launches."""

    if len(cases) < 4:
        raise ValueError("the replay audit requires at least four control cases")
    if len(set(cases)) != len(cases):
        raise ValueError("case triples must be unique; use repetition to distinguish repeats")
    baseline = cases[0]
    if baseline[1] != 0:
        raise ValueError("the first/baseline case must have FET_FIDCURVE_DEBUG=0")
    baseline_payload = {
        "cuda_seed": int(baseline[0]),
        "fidcurve_debug": int(baseline[1]),
        "repetition": int(baseline[2]),
    }
    kinds = {
        comparison_kind(
            baseline_payload,
            {
                "cuda_seed": int(case[0]),
                "fidcurve_debug": int(case[1]),
                "repetition": int(case[2]),
            },
        )
        for case in cases[1:]
    }
    missing = sorted(REQUIRED_COMPARISON_KINDS - kinds)
    if missing:
        raise ValueError(f"replay audit case matrix is missing controls: {missing}")
    return kinds


def validate_comparison_kinds(
    comparisons: Sequence[dict[str, Any]],
) -> set[str]:
    """Fail closed if a required control did not reach the comparison stage."""

    kinds = {str(comparison["kind"]) for comparison in comparisons}
    missing = sorted(REQUIRED_COMPARISON_KINDS - kinds)
    if missing:
        raise RuntimeError(
            f"replay audit comparisons are missing required controls: {missing}"
        )
    return kinds


def _max_fid_delta(
    left_cuts: list[dict[str, Any]], right_cuts: list[dict[str, Any]]
) -> float | None:
    if len(left_cuts) != len(right_cuts):
        return None
    pairs: list[tuple[float, float]] = []
    for left, right in zip(left_cuts, right_cuts, strict=True):
        left_fid = validate_fid_gamma_evidence(left["Fid_gamma"])
        right_fid = validate_fid_gamma_evidence(right["Fid_gamma"])
        if left_fid["value"] is None or right_fid["value"] is None:
            return None
        pairs.append((float(left_fid["value"]), float(right_fid["value"])))
    return max(
        (abs(left - right) for left, right in pairs),
        default=0.0,
    )


def _scoped_scalar_capture(result: dict[str, Any]) -> dict[str, Any]:
    """Scalars covered by the scoped bitwise replay verdict."""

    entropy = result["entropy_gate"]
    return {
        "per_cut": [
            {
                "ordinal": cut["ordinal"],
                "bond": cut["bond"],
                "dim_in": cut["dim_in"],
                "dim_out": cut["dim_out"],
                "exact_rank": cut["exact_rank"],
                "env_rank": cut["env_rank"],
                "map_rank_axis": cut["map_rank_axis"],
                "Fid_gamma": cut["Fid_gamma"],
                "fidelity_target": cut["fidelity_target"],
                "target_met": cut["target_met"],
                "fid_gamma_finite": cut["fid_gamma_finite"],
                "nonfinite_fid_gamma_violation": cut[
                    "nonfinite_fid_gamma_violation"
                ],
                "map_frobenius_norm": cut["map_frobenius_norm"],
                "map_vs_identity_relative_error": cut[
                    "map_vs_identity_relative_error"
                ],
                "map_is_identity": cut["map_is_identity"],
                "rank_reducing_writeback": cut["rank_reducing_writeback"],
                "nonidentity_or_lossy_writeback": cut[
                    "nonidentity_or_lossy_writeback"
                ],
                "fallback_contract_violation": cut[
                    "fallback_contract_violation"
                ],
                "fet_contract_violation": cut["fet_contract_violation"],
                "fet_cut_contract_verdict": cut["fet_cut_contract_verdict"],
                "eps_fid": cut["eps_fid"],
            }
            for cut in result["per_cut"]
        ],
        "round_state_amplitude_count": result["round_state"]["amplitude_count"],
        "entropy_gate": {
            key: entropy[key]
            for key in (
                "S_A",
                "GF2_reference",
                "absolute_deviation",
                "tolerance",
                "entropy_matches",
                "leak_mass",
                "leak_mass_tolerance",
                "leakage_off_precondition_passed",
                "schmidt_rank",
                "full_norm2",
                "qubit_norm2",
                "verdict",
            )
        },
        "record_payload_sha256": result["record_payload_sha256"],
    }


def _max_scoped_scalar_delta(
    baseline: dict[str, Any], candidate: dict[str, Any]
) -> float | None:
    """Largest scale-sensitive floating difference in the captured evidence."""

    left_cuts = baseline["per_cut"]
    right_cuts = candidate["per_cut"]
    if len(left_cuts) != len(right_cuts):
        return None
    pairs: list[tuple[float, float]] = []
    for left, right in zip(left_cuts, right_cuts, strict=True):
        left_fid = validate_fid_gamma_evidence(left["Fid_gamma"])
        right_fid = validate_fid_gamma_evidence(right["Fid_gamma"])
        if left_fid["value"] is None or right_fid["value"] is None:
            return None
        pairs.extend(
            (
                (float(left_fid["value"]), float(right_fid["value"])),
                (
                    float(left["fidelity_target"]),
                    float(right["fidelity_target"]),
                ),
                (
                    float(left["map_frobenius_norm"]),
                    float(right["map_frobenius_norm"]),
                ),
                (
                    float(left["map_vs_identity_relative_error"]),
                    float(right["map_vs_identity_relative_error"]),
                ),
            )
        )
    for key in ("S_A", "leak_mass", "full_norm2", "qubit_norm2"):
        pairs.append(
            (
                float(baseline["entropy_gate"][key]),
                float(candidate["entropy_gate"][key]),
            )
        )
    return max((abs(left - right) for left, right in pairs), default=0.0)


def compare_worker_results(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    baseline_arrays: dict[str, Any],
    candidate_arrays: dict[str, Any],
) -> dict[str, Any]:
    """Compare two worker results without treating hashes as a numerical metric."""

    left_cuts = list(baseline["per_cut"])
    right_cuts = list(candidate["per_cut"])
    same_bonds = [cut["bond"] for cut in left_cuts] == [
        cut["bond"] for cut in right_cuts
    ]
    same_ranks = [cut["env_rank"] for cut in left_cuts] == [
        cut["env_rank"] for cut in right_cuts
    ]
    same_raw_map_hashes = [cut["map_sha256_c128le"] for cut in left_cuts] == [
        cut["map_sha256_c128le"] for cut in right_cuts
    ]
    left_fid_evidence = [
        validate_fid_gamma_evidence(cut["Fid_gamma"]) for cut in left_cuts
    ]
    right_fid_evidence = [
        validate_fid_gamma_evidence(cut["Fid_gamma"]) for cut in right_cuts
    ]
    same_fid_classifications = [
        item["classification"] for item in left_fid_evidence
    ] == [item["classification"] for item in right_fid_evidence]
    all_fid_gamma_finite = all(
        item["classification"] == "finite"
        for item in (*left_fid_evidence, *right_fid_evidence)
    )

    map_distances: list[dict[str, Any]] = []
    max_map_l2 = 0.0
    max_map_abs = 0.0
    maps_comparable = True
    if len(left_cuts) != len(right_cuts):
        maps_comparable = False
    else:
        for index in range(len(left_cuts)):
            key = f"map_{index:04d}"
            if key not in baseline_arrays or key not in candidate_arrays:
                maps_comparable = False
                map_distances.append({"ordinal": index, "missing_array": True})
                continue
            distance = projective_array_distance(
                baseline_arrays[key], candidate_arrays[key]
            )
            if not distance["comparable"]:
                maps_comparable = False
            else:
                max_map_l2 = max(max_map_l2, float(distance["l2"]))
                max_map_abs = max(max_map_abs, float(distance["max_abs"]))
            map_distances.append({"ordinal": index, **distance})

    state_distance = projective_array_distance(
        baseline_arrays["round_state"], candidate_arrays["round_state"]
    )
    fid_delta = _max_fid_delta(left_cuts, right_cuts)
    scalar_delta = _max_scoped_scalar_delta(baseline, candidate)
    entropy_delta = abs(
        float(baseline["entropy_gate"]["S_A"])
        - float(candidate["entropy_gate"]["S_A"])
    )
    input_match = (
        baseline["input_identity_sha256"] == candidate["input_identity_sha256"]
    )
    same_record_payload = (
        baseline["record_payload_sha256"] == candidate["record_payload_sha256"]
    )
    same_entropy_rank = (
        baseline["entropy_gate"]["schmidt_rank"]
        == candidate["entropy_gate"]["schmidt_rank"]
    )
    same_scoped_scalars = (
        canonical_json_bytes(_scoped_scalar_capture(baseline))
        == canonical_json_bytes(_scoped_scalar_capture(candidate))
    )
    numeric_pass = all(
        (
            input_match,
            same_bonds,
            same_ranks,
            same_record_payload,
            same_entropy_rank,
            all_fid_gamma_finite,
            same_fid_classifications,
            fid_delta is not None and fid_delta <= FID_REPLAY_TOL,
            scalar_delta is not None and scalar_delta <= SCALAR_REPLAY_TOL,
            entropy_delta <= ENTROPY_REPLAY_TOL,
            maps_comparable,
            max_map_l2 <= ARRAY_REPLAY_TOL,
            state_distance["comparable"],
            state_distance["l2"] is not None
            and state_distance["l2"] <= ARRAY_REPLAY_TOL,
        )
    )
    bitwise_pass = all(
        (
            numeric_pass,
            same_raw_map_hashes,
            same_scoped_scalars,
            baseline["round_state"]["sha256_c128le"]
            == candidate["round_state"]["sha256_c128le"],
        )
    )
    if not all_fid_gamma_finite:
        verdict = "FAIL_NONFINITE_FID_GAMMA"
    elif bitwise_pass:
        verdict = "PASS_SCOPED_BITWISE"
    elif numeric_pass:
        verdict = "PASS_SCOPED_NUMERIC_NOT_BITWISE"
    else:
        verdict = "FAIL_DIVERGED"
    return {
        "baseline_case_id": baseline["case_id"],
        "candidate_case_id": candidate["case_id"],
        "kind": comparison_kind(baseline["case"], candidate["case"]),
        "input_identity_match": bool(input_match),
        "same_bond_sequence": bool(same_bonds),
        "same_rank_sequence": bool(same_ranks),
        "same_raw_map_hash_sequence": bool(same_raw_map_hashes),
        "same_Fid_gamma_classification_sequence": bool(
            same_fid_classifications
        ),
        "all_Fid_gamma_finite": bool(all_fid_gamma_finite),
        "same_record_payload": bool(same_record_payload),
        "same_entropy_schmidt_rank": bool(same_entropy_rank),
        "same_scoped_scalar_capture": bool(same_scoped_scalars),
        "max_Fid_gamma_delta": None if fid_delta is None else float(fid_delta),
        "max_scoped_scalar_delta": (
            None if scalar_delta is None else float(scalar_delta)
        ),
        "S_A_delta": float(entropy_delta),
        "projective_maps_comparable": bool(maps_comparable),
        "max_projective_map_l2": float(max_map_l2) if maps_comparable else None,
        "max_projective_map_abs": float(max_map_abs) if maps_comparable else None,
        "round_state_comparable": bool(state_distance["comparable"]),
        "round_state_projective_l2": state_distance["l2"],
        "round_state_projective_max_abs": state_distance["max_abs"],
        "numeric_tolerances": {
            "Fid_gamma": FID_REPLAY_TOL,
            "S_A": ENTROPY_REPLAY_TOL,
            "projective_array_l2": ARRAY_REPLAY_TOL,
            "scale_sensitive_scalar": SCALAR_REPLAY_TOL,
        },
        "verdict_scope": (
            "captured per-cut maps and scalars, round dense state, entropy/leakage "
            "scalars, and packed record payload; not complete record-law faithfulness"
        ),
        "verdict": verdict,
        "per_cut_projective_map_distance": map_distances,
    }


def summarize_replay(comparisons: Sequence[dict[str, Any]]) -> str:
    if any(
        item["verdict"] == "FAIL_NONFINITE_FID_GAMMA"
        for item in comparisons
    ):
        return "FAIL_NONFINITE_FID_GAMMA"
    failed = [item for item in comparisons if not item["verdict"].startswith("PASS_")]
    if failed:
        kinds = {item["kind"] for item in failed}
        if "fresh_process_repeat" in kinds:
            return "FAIL_FRESH_PROCESS_REPEAT_DIVERGED"
        if "cuda_seed_sensitivity" in kinds:
            return "FAIL_CUDA_SEED_SENSITIVE"
        if "fidcurve_debug_invariance" in kinds:
            return "FAIL_FIDCURVE_DEBUG_CHANGED_BEHAVIOR"
        return "FAIL_REPLAY_DIVERGED"
    if any(
        item["verdict"] == "PASS_SCOPED_NUMERIC_NOT_BITWISE"
        for item in comparisons
    ):
        return "PASS_SCOPED_NUMERIC_NOT_BITWISE"
    return "PASS_SCOPED_BITWISE"


def _git_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _tracked_file_provenance(paths: dict[str, Path]) -> dict[str, Any]:
    """Authenticate tracked, clean files against the current Git commit."""

    resolved = {
        name: (path if path.is_absolute() else ROOT / path).resolve()
        for name, path in paths.items()
    }
    relative: dict[str, str] = {}
    for name, path in resolved.items():
        if not path.is_file():
            raise RuntimeError(f"{name} execution input is missing: {path}")
        try:
            relative[name] = path.relative_to(ROOT).as_posix()
        except ValueError as exc:
            raise RuntimeError(
                f"{name} execution input is outside the repository: {path}"
            ) from exc
    for name, relpath in relative.items():
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", relpath],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if tracked.returncode != 0:
            raise RuntimeError(
                f"{name} execution input is not tracked; commit before running: {relpath}"
            )
        for diff_args in (("diff", "--quiet"), ("diff", "--cached", "--quiet")):
            clean = subprocess.run(
                ["git", *diff_args, "--", relpath],
                cwd=ROOT,
                check=False,
                capture_output=True,
            )
            if clean.returncode != 0:
                raise RuntimeError(
                    f"{name} execution input has uncommitted changes: {relpath}"
                )
    return {
        "git_commit": _git_commit(),
        "paths": relative,
        "file_sha256": {
            name: sha256_file(path) for name, path in resolved.items()
        },
        "git_blob_ids": {
            name: subprocess.run(
                ["git", "rev-parse", f"HEAD:{relpath}"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            for name, relpath in relative.items()
        },
    }


def committed_execution_provenance() -> dict[str, Any]:
    """Bind the diagnostic, harness, declared source, and environment locks."""

    return _tracked_file_provenance(dict(STATIC_EXECUTION_BINDINGS))


def _module_source_path(module: Any) -> Path | None:
    origin = getattr(module, "__file__", None)
    if origin is None:
        spec = getattr(module, "__spec__", None)
        origin = None if spec is None else getattr(spec, "origin", None)
    if not origin or origin in {"built-in", "frozen"}:
        return None
    path = Path(origin).resolve()
    if path.suffix in {".pyc", ".pyo"}:
        try:
            path = Path(importlib.util.source_from_cache(str(path))).resolve()
        except ValueError:
            return None
    return path if path.suffix == ".py" else None


def loaded_project_module_provenance() -> dict[str, Any]:
    """Bind every imported Python module from the simulator package."""

    source_root = (ROOT / "src/error_coupling_simulator").resolve()
    paths: dict[str, Path] = {}
    for name, module in sorted(sys.modules.items()):
        if name != "error_coupling_simulator" and not name.startswith(
            "error_coupling_simulator."
        ):
            continue
        path = _module_source_path(module)
        if path is None:
            continue
        try:
            path.relative_to(source_root)
        except ValueError as exc:
            raise RuntimeError(
                f"simulator module {name} imported outside repo source tree: {path}"
            ) from exc
        paths[name] = path
    if not paths:
        raise RuntimeError("no simulator Python modules were available for provenance")
    return _tracked_file_provenance(paths)


def _distribution_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _callable_source_manifest(callables: dict[str, Any]) -> dict[str, Any]:
    paths: dict[str, Path] = {}
    for name, value in callables.items():
        source = inspect.getsourcefile(value)
        if source is None:
            raise RuntimeError(f"cannot locate runtime source for {name}")
        paths[name] = Path(source).resolve()
    return {
        "paths": {name: path.as_posix() for name, path in paths.items()},
        "file_sha256": {name: sha256_file(path) for name, path in paths.items()},
    }


def tensor_runtime_identity(torch: Any) -> dict[str, Any]:
    """Capture the tensor libraries and the exact visible CUDA device."""

    import numpy as np
    import quimb
    import quimb.tensor as qtn

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable while recording runtime identity")
    device_index = int(torch.cuda.current_device())
    properties = torch.cuda.get_device_properties(device_index)
    uuid = getattr(properties, "uuid", None)
    if isinstance(uuid, bytes):
        uuid = uuid.decode("ascii", errors="replace")
    callable_sources = _callable_source_manifest(
        {
            "quimb.Tensor": qtn.Tensor,
            "quimb.TensorNetwork": qtn.TensorNetwork,
            "quimb.TensorNetwork.contract": qtn.TensorNetwork.contract,
            "quimb.TN_matching": qtn.TN_matching,
            "quimb.tensor_network_1d_compress": qtn.tensor_network_1d_compress,
        }
    )
    numpy_origin = Path(np.__file__).resolve()
    torch_origin = Path(torch.__file__).resolve()
    quimb_origin = Path(quimb.__file__).resolve()
    return {
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable": Path(sys.executable).resolve().as_posix(),
        },
        "numpy": {
            "version": str(np.__version__),
            "distribution_version": _distribution_version("numpy"),
            "origin": numpy_origin.as_posix(),
            "origin_sha256": sha256_file(numpy_origin),
        },
        "torch": {
            "version": str(torch.__version__),
            "distribution_version": _distribution_version("torch"),
            "origin": torch_origin.as_posix(),
            "origin_sha256": sha256_file(torch_origin),
            "build_config": str(torch.__config__.show()),
            "default_dtype": str(torch.get_default_dtype()),
            "deterministic_algorithms_enabled": bool(
                torch.are_deterministic_algorithms_enabled()
            ),
            "num_threads": int(torch.get_num_threads()),
        },
        "quimb": {
            "version": str(quimb.__version__),
            "distribution_version": _distribution_version("quimb"),
            "origin": quimb_origin.as_posix(),
            "origin_sha256": sha256_file(quimb_origin),
            "load_bearing_source": callable_sources,
        },
        "cuda": {
            "available": True,
            "torch_build_cuda": str(torch.version.cuda),
            "cudnn_version": torch.backends.cudnn.version(),
            "visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
            "ecs_gpu_slot": os.environ.get("ECS_GPU_SLOT"),
            "cublas_workspace_config": os.environ.get("CUBLAS_WORKSPACE_CONFIG"),
            "cudnn_deterministic": bool(torch.backends.cudnn.deterministic),
            "cudnn_benchmark": bool(torch.backends.cudnn.benchmark),
            "matmul_allow_tf32": bool(torch.backends.cuda.matmul.allow_tf32),
            "current_device_index": device_index,
            "device_name": str(properties.name),
            "device_uuid": None if uuid is None else str(uuid),
            "compute_capability": [int(properties.major), int(properties.minor)],
            "total_memory_bytes": int(properties.total_memory),
            "multi_processor_count": int(properties.multi_processor_count),
        },
    }


def _input_manifest(schedule: Any, source_paths: Sequence[Path]) -> dict[str, Any]:
    generators = [dict(stabilizer.paulis) for stabilizer in schedule.stabilizers]
    generators.append(dict(schedule.logical))
    gf2_reference = stabilizer_entropy_sa(generators, int(schedule.n_data), CUT_A)
    if abs(gf2_reference - ENTROPY_REFERENCE) > 1.0e-12:
        raise RuntimeError(
            f"fixed-input GF(2) reference drifted: {gf2_reference!r} != {ENTROPY_REFERENCE!r}"
        )
    source_names = ("r01_circuit", "r01_metadata", "r10_circuit", "r10_metadata")
    return {
        "patch": PATCH,
        "n_data": int(schedule.n_data),
        "n_stabilizers": len(schedule.stabilizers),
        "run": {
            "G_seep": G_SEEP,
            "G_heat": G_HEAT,
            "b": B_BIAS,
            "arm": ARM,
            "readout_convention": READOUT_CONV,
            "logical_m": LOGICAL_M,
            "fit_seed": FIT_SEED,
            "trajectory_base_seed": BASE_SEED,
            "leakage_rate": LEAKAGE_RATE,
            "rounds": 1,
            "shots": 1,
            "dtype": "c128",
            "policy": "fet_env",
            "eps_fid": EPS_FID,
        },
        "entropy_reference": {
            "method": "independent_GF2_stabilizer_algebra",
            "region_A": list(CUT_A),
            "S_A": gf2_reference,
            "tolerance": ENTROPY_TOL,
        },
        "source_file_sha256": {
            name: sha256_file(path)
            for name, path in zip(source_names, source_paths, strict=True)
        },
        "source_file_paths": {
            name: path.resolve().as_posix()
            for name, path in zip(source_names, source_paths, strict=True)
        },
        "production_file_sha256": {
            "fet.py": sha256_file(
                ROOT / "src/error_coupling_simulator/carrier/peps/fet.py"
            ),
            "trajectory.py": sha256_file(
                ROOT / "src/error_coupling_simulator/carrier/peps/trajectory.py"
            ),
            "state.py": sha256_file(
                ROOT / "src/error_coupling_simulator/carrier/peps/state.py"
            ),
        },
        "diagnostic_file_sha256": sha256_file(Path(__file__).resolve()),
    }


def validate_worker_arrays(
    result: dict[str, Any], arrays: dict[str, Any]
) -> dict[str, Any]:
    """Authenticate a temporary NPZ payload before any replay comparison."""

    import numpy as np

    cuts = list(result["per_cut"])
    cut_count = int(result["cut_count"])
    if cut_count != len(cuts):
        raise RuntimeError(
            f"worker cut-count mismatch: declared={cut_count}, rows={len(cuts)}"
        )
    ordinals = [int(cut["ordinal"]) for cut in cuts]
    if ordinals != list(range(cut_count)):
        raise RuntimeError(f"worker cut ordinals are not contiguous: {ordinals}")

    expected_keys = {f"map_{index:04d}" for index in range(cut_count)}
    expected_keys.add("round_state")
    actual_keys = set(arrays)
    if actual_keys != expected_keys:
        raise RuntimeError(
            "worker NPZ key mismatch: "
            f"missing={sorted(expected_keys - actual_keys)}, "
            f"extra={sorted(actual_keys - expected_keys)}"
        )
    archive_manifest = result["array_archive_manifest"]
    if archive_manifest.get("format") != "npz_temporary_authenticated_arrays":
        raise RuntimeError("worker NPZ manifest format is not authenticated")
    if archive_manifest.get("exact_keys") != sorted(expected_keys):
        raise RuntimeError("worker NPZ manifest exact-key declaration mismatches cuts")
    if archive_manifest.get("dtype") != "complex128":
        raise RuntimeError("worker NPZ manifest dtype must be complex128")

    authenticated: dict[str, dict[str, Any]] = {}
    for index, cut in enumerate(cuts):
        key = f"map_{index:04d}"
        array = arrays[key]
        if not isinstance(array, np.ndarray):
            raise RuntimeError(f"worker NPZ {key} is not an ndarray")
        if array.dtype != np.dtype(np.complex128):
            raise RuntimeError(
                f"worker NPZ {key} dtype mismatch: {array.dtype} != complex128"
            )
        expected_shape = (int(cut["dim_in"]), int(cut["dim_in"]))
        if array.shape != expected_shape:
            raise RuntimeError(
                f"worker NPZ {key} shape mismatch: {array.shape} != {expected_shape}"
            )
        if not np.isfinite(array.real).all() or not np.isfinite(array.imag).all():
            raise RuntimeError(f"worker NPZ {key} contains non-finite values")
        if float(np.linalg.norm(array)) <= 0.0:
            raise RuntimeError(f"worker NPZ {key} has zero norm")
        raw_hash = array_sha256_c128le(array)
        projective_hash = projective_array_sha256(array)
        if raw_hash != cut["map_sha256_c128le"]:
            raise RuntimeError(f"worker NPZ {key} raw hash mismatch")
        if projective_hash != cut["map_projective_sha256_c128le"]:
            raise RuntimeError(f"worker NPZ {key} projective hash mismatch")
        map_norm = float(np.linalg.norm(array))
        if abs(map_norm - float(cut["map_frobenius_norm"])) > SCALAR_REPLAY_TOL:
            raise RuntimeError(f"worker NPZ {key} Frobenius norm mismatch")
        try:
            fid_evidence = validate_fid_gamma_evidence(cut["Fid_gamma"])
        except ValueError as exc:
            raise RuntimeError(
                f"worker NPZ {key} Fid_gamma evidence schema is invalid"
            ) from exc
        recomputed_contract = evaluate_fet_cut_contract(
            map_array=array,
            dim_in=int(cut["dim_in"]),
            dim_out=int(cut["dim_out"]),
            env_rank=int(cut["env_rank"]),
            fid_gamma=fid_evidence,
            eps_fid=float(cut["eps_fid"]),
        )
        for name, expected in recomputed_contract.items():
            observed = cut[name]
            if isinstance(expected, float):
                matches = math.isclose(
                    float(observed), expected, rel_tol=1.0e-14, abs_tol=1.0e-15
                )
            else:
                matches = observed == expected
            if not matches:
                raise RuntimeError(
                    f"worker NPZ {key} FET contract field {name} mismatches"
                )
        authenticated[key] = {
            "shape": list(array.shape),
            "dtype": str(array.dtype),
            "sha256_c128le": raw_hash,
            "projective_sha256_c128le": projective_hash,
        }

    state = arrays["round_state"]
    if not isinstance(state, np.ndarray):
        raise RuntimeError("worker NPZ round_state is not an ndarray")
    if state.dtype != np.dtype(np.complex128):
        raise RuntimeError(
            f"worker NPZ round_state dtype mismatch: {state.dtype} != complex128"
        )
    expected_state_shape = (int(result["round_state"]["amplitude_count"]),)
    if state.shape != expected_state_shape:
        raise RuntimeError(
            "worker NPZ round_state shape mismatch: "
            f"{state.shape} != {expected_state_shape}"
        )
    if not np.isfinite(state.real).all() or not np.isfinite(state.imag).all():
        raise RuntimeError("worker NPZ round_state contains non-finite values")
    if float(np.linalg.norm(state)) <= 0.0:
        raise RuntimeError("worker NPZ round_state has zero norm")
    raw_state_hash = array_sha256_c128le(state)
    projective_state_hash = projective_array_sha256(state)
    if raw_state_hash != result["round_state"]["sha256_c128le"]:
        raise RuntimeError("worker NPZ round_state raw hash mismatch")
    if (
        projective_state_hash
        != result["round_state"]["projective_sha256_c128le"]
    ):
        raise RuntimeError("worker NPZ round_state projective hash mismatch")
    state_norm2 = float(np.vdot(state.reshape(-1), state.reshape(-1)).real)
    if (
        abs(state_norm2 - float(result["entropy_gate"]["full_norm2"]))
        > SCALAR_REPLAY_TOL
    ):
        raise RuntimeError("worker NPZ round_state full norm mismatch")
    authenticated["round_state"] = {
        "shape": list(state.shape),
        "dtype": str(state.dtype),
        "sha256_c128le": raw_state_hash,
        "projective_sha256_c128le": projective_state_hash,
    }
    return {
        "status": "AUTHENTICATED",
        "exact_keys": sorted(expected_keys),
        "arrays": authenticated,
    }


def _worker_run(
    *,
    cuda_seed: int,
    fidcurve_debug: int,
    repetition: int,
    output: Path,
    arrays_output: Path,
) -> None:
    """Execute one fixed trajectory.  This function runs only in a child process."""

    import contextlib
    import io
    import random

    execution_provenance = committed_execution_provenance()

    import numpy as np
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable; the PEPS/FET audit is GPU-only")
    if fidcurve_debug not in (0, 1):
        raise ValueError("fidcurve_debug must be 0 or 1")
    os.environ["FET_FIDCURVE_DEBUG"] = str(int(fidcurve_debug))
    random.seed(int(cuda_seed))
    np.random.seed(int(cuda_seed))
    torch.manual_seed(int(cuda_seed))
    torch.cuda.manual_seed_all(int(cuda_seed))

    from error_coupling_simulator.carrier.peps import PepsSampler, TruncationPolicy
    from error_coupling_simulator.carrier.within_cycle import RunSpec
    from error_coupling_simulator.frontend import xzzx_parser as xp
    from error_coupling_simulator.mechanisms.qutrit_leakage import (
        solve_exchange_angle_for_leakage_rate,
    )
    import error_coupling_simulator.carrier.peps.fet as fet
    import error_coupling_simulator.carrier.peps.trajectory as trajectory

    expected_fet = ROOT / "src/error_coupling_simulator/carrier/peps/fet.py"
    expected_trajectory = ROOT / "src/error_coupling_simulator/carrier/peps/trajectory.py"
    if Path(fet.__file__).resolve() != expected_fet.resolve():
        raise RuntimeError(
            f"FET import origin mismatch: {fet.__file__!r} != {expected_fet}"
        )
    if Path(trajectory.__file__).resolve() != expected_trajectory.resolve():
        raise RuntimeError(
            "trajectory import origin mismatch: "
            f"{trajectory.__file__!r} != {expected_trajectory}"
        )

    c01, m01 = xp.default_r01_paths(patch=PATCH, basis="X")
    c10, m10 = xp.default_r10_paths(patch=PATCH, basis="X")
    source_paths = tuple(Path(path) for path in (c01, m01, c10, m10))
    missing = [path.as_posix() for path in source_paths if not path.is_file()]
    if missing:
        raise RuntimeError(
            "real d3 XZZX files are required; no synthetic fallback: " + repr(missing)
        )
    schedule = xp.parse_xzzx_circuit(c01, m01, verify=True)
    schedule = schedule.with_within_cycle_streams(
        xp.parse_within_cycle_streams(c10, m10)
    )
    if int(schedule.n_data) != 9 or len(schedule.stabilizers) != 8:
        raise RuntimeError(
            f"fixed d3 schedule drifted: n_data={schedule.n_data}, "
            f"n_stabilizers={len(schedule.stabilizers)}"
        )
    input_manifest = _input_manifest(schedule, source_paths)
    input_identity = sha256_bytes(canonical_json_bytes(input_manifest))

    theta = solve_exchange_angle_for_leakage_rate(
        LEAKAGE_RATE, g_seep=G_SEEP, g_heat=G_HEAT
    )
    spec = RunSpec(
        circuit_path=c01,
        metadata_path=m01,
        m=LOGICAL_M,
        theta=float(theta),
        g_seep=G_SEEP,
        g_heat=G_HEAT,
        arm=ARM,
        b=B_BIAS,
        readout_conv=READOUT_CONV,
        N=1,
        base_seed=BASE_SEED,
        R=1,
        dtype="c128",
    )

    per_cut: list[dict[str, Any]] = []
    map_arrays: dict[str, Any] = {}
    original_env_optimal_rank = fet.env_optimal_rank

    def audited_env_optimal_rank(state: Any, bond: str, eps_fid: float):
        result = original_env_optimal_rank(state, bond, eps_fid)
        env_rank, u, vh, fid_gamma = result
        map_tensor = (u @ vh).detach().to(torch.complex128).cpu().contiguous()
        map_array = map_tensor.numpy()
        ordinal = len(per_cut)
        map_arrays[f"map_{ordinal:04d}"] = map_array
        per_cut.append(
            {
                "ordinal": ordinal,
                "bond": str(bond),
                "dim_in": int(u.shape[0]),
                "env_rank": int(env_rank),
                "map_rank_axis": int(u.shape[1]),
                "Fid_gamma": classify_fid_gamma(fid_gamma),
                "map_frobenius_norm": _finite_float(
                    torch.linalg.vector_norm(map_tensor),
                    name=f"map_frobenius_norm[{ordinal}]",
                ),
                "map_sha256_c128le": array_sha256_c128le(map_array),
                "map_projective_sha256_c128le": projective_array_sha256(map_array),
            }
        )
        return result

    fet.env_optimal_rank = audited_env_optimal_rank
    captured: dict[str, Any] = {}

    def round_hook(state: Any, round_index: int, shot_index: int) -> None:
        if int(round_index) != 0 or int(shot_index) != 0:
            raise RuntimeError(
                f"unexpected hook coordinates round={round_index}, shot={shot_index}"
            )
        if "state" in captured:
            raise RuntimeError("round hook fired more than once for the fixed one-round input")
        captured["state"] = state.copy()

    stream = io.StringIO()
    try:
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            shotset, ledgers = PepsSampler(device="cuda").sample(
                spec,
                sched=schedule,
                policy=TruncationPolicy("fet_env", eps_fid=EPS_FID),
                R_n=None,
                R_x=None,
                fit_seed=FIT_SEED,
                materialize=True,
                d_abort=None,
                round_hook=round_hook,
            )
    finally:
        fet.env_optimal_rank = original_env_optimal_rank
    torch.cuda.synchronize()
    if "state" not in captured:
        raise RuntimeError("fixed one-round trajectory did not produce a round snapshot")
    if len(ledgers) != 1:
        raise RuntimeError(f"expected one trajectory ledger, got {len(ledgers)}")

    fet_ledger = [entry for entry in ledgers[0] if entry.get("op") == "fet_truncate"]
    if len(fet_ledger) != len(per_cut):
        raise RuntimeError(
            f"audit/trajectory cut-count mismatch: wrapper={len(per_cut)}, "
            f"ledger={len(fet_ledger)}"
        )
    for audit, ledger in zip(per_cut, fet_ledger, strict=True):
        if audit["bond"] != str(ledger["bond"]):
            raise RuntimeError(f"bond ledger mismatch: audit={audit!r}, ledger={ledger!r}")
        if audit["env_rank"] != int(ledger["env_rank"]):
            raise RuntimeError(f"rank ledger mismatch: audit={audit!r}, ledger={ledger!r}")
        ledger_fid = classify_fid_gamma(ledger["Fid_gamma"])
        if canonical_json_bytes(audit["Fid_gamma"]) != canonical_json_bytes(
            ledger_fid
        ):
            raise RuntimeError(
                "Fid_gamma ledger evidence mismatch: "
                f"audit={audit['Fid_gamma']!r}, ledger={ledger_fid!r}"
            )
        audit["dim_out"] = int(ledger["dim_out"])
        audit["exact_rank"] = (
            None if ledger.get("exact_rank") is None else int(ledger["exact_rank"])
        )
        audit["eps_fid"] = float(ledger["eps_fid"])
        audit.update(
            evaluate_fet_cut_contract(
                map_array=map_arrays[f"map_{audit['ordinal']:04d}"],
                dim_in=int(audit["dim_in"]),
                dim_out=int(audit["dim_out"]),
                env_rank=int(audit["env_rank"]),
                fid_gamma=audit["Fid_gamma"],
                eps_fid=float(audit["eps_fid"]),
            )
        )

    entropy = dense_carrier_entropy(captured["state"], CUT_A)
    round_state = entropy.pop("state")
    map_arrays["round_state"] = round_state
    arrays_output.parent.mkdir(parents=True, exist_ok=True)
    np.savez(arrays_output, **map_arrays)

    reference = float(input_manifest["entropy_reference"]["S_A"])
    entropy_gate = evaluate_entropy_gate(
        entropy=float(entropy["S_A"]),
        reference=reference,
        leak_mass=float(entropy["leak_mass"]),
    )
    entropy_gate.update(
        {
            "region_A": list(CUT_A),
            "schmidt_rank": int(entropy["schmidt_rank"]),
            "full_norm2": float(entropy["full_norm2"]),
            "qubit_norm2": float(entropy["qubit_norm2"]),
        }
    )
    record_payload = np.ascontiguousarray(shotset.shots).tobytes()
    debug_lines = [line.strip() for line in stream.getvalue().splitlines() if line.strip()]
    case = {
        "cuda_seed": int(cuda_seed),
        "fidcurve_debug": int(fidcurve_debug),
        "repetition": int(repetition),
    }
    fet_contract_gate = aggregate_fet_fallback_contract(
        [{"case_id": case_id((cuda_seed, fidcurve_debug, repetition)), "per_cut": per_cut}]
    )
    result = {
        "schema": WORKER_SCHEMA,
        "case_id": case_id((cuda_seed, fidcurve_debug, repetition)),
        "case": case,
        "git_commit": execution_provenance["git_commit"],
        "execution_provenance": execution_provenance,
        "input": input_manifest,
        "input_identity_sha256": input_identity,
        "per_cut": per_cut,
        "cut_count": len(per_cut),
        "round_state": {
            "sha256_c128le": array_sha256_c128le(round_state),
            "projective_sha256_c128le": projective_array_sha256(round_state),
            "amplitude_count": int(round_state.size),
        },
        "array_archive_manifest": {
            "format": "npz_temporary_authenticated_arrays",
            "exact_keys": sorted(map_arrays),
            "dtype": "complex128",
            "retained_in_final_report": False,
        },
        "entropy_gate": entropy_gate,
        "fet_fallback_contract_gate": fet_contract_gate,
        "record_payload_sha256": sha256_bytes(record_payload),
        "solver_log": debug_lines,
        "solver_log_sha256": sha256_bytes("\n".join(debug_lines).encode("utf-8")),
        "claim_boundary": {
            "state_level_replay_only": True,
            "complete_record_law_certified": False,
            "d5_d7_faithfulness": "OPEN",
        },
    }
    execution_provenance["loaded_project_modules"] = (
        loaded_project_module_provenance()
    )
    execution_provenance["tensor_runtime"] = tensor_runtime_identity(torch)
    result["content_hash_sha256"] = report_content_hash(result)
    write_json_atomic(output, result)


def _load_harness_module(name: str):
    if name in _HARNESS_MODULES:
        return _HARNESS_MODULES[name]
    path = ROOT / "tests/harness" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"fet_audit_{name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load harness module {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _HARNESS_MODULES[name] = module
    return module


def _run_worker_case(
    case: tuple[int, int, int],
    directory: Path,
    *,
    timeout: float,
    child_env: dict[str, str],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    import numpy as np

    identifier = case_id(case)
    worker_output = directory / f"{identifier}.json"
    arrays_output = directory / f"{identifier}.npz"
    log_output = directory / f"{identifier}.log"
    seed, debug, repetition = case
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker",
        "--worker-output",
        str(worker_output),
        "--arrays-output",
        str(arrays_output),
        "--cuda-seed",
        str(seed),
        "--fidcurve-debug",
        str(debug),
        "--repetition",
        str(repetition),
    ]
    proc = _load_harness_module("proc")
    ran = proc.run(
        command,
        cwd=str(ROOT),
        env=child_env,
        timeout=float(timeout),
        log_path=str(log_output),
    )
    execution = {
        "case_id": identifier,
        "returncode": int(ran.returncode),
        "timed_out": bool(ran.timed_out),
        "process_group_cleanup_verified": bool(ran.group_cleanup_verified),
    }
    if not ran.ok:
        log = log_output.read_text(errors="replace") if log_output.is_file() else ""
        raise RuntimeError(
            f"worker {identifier} failed: execution={execution!r}\n"
            f"--- worker log ---\n{log[-12000:]}"
        )
    if not worker_output.is_file() or not arrays_output.is_file():
        raise RuntimeError(
            f"worker {identifier} exited successfully without both output artifacts"
        )
    result = json.loads(worker_output.read_text())
    if result.get("schema") != WORKER_SCHEMA or result.get("case_id") != identifier:
        raise RuntimeError(f"worker result identity mismatch: {result!r}")
    if report_content_hash(result) != result.get("content_hash_sha256"):
        raise RuntimeError(f"worker result content hash mismatch: {identifier}")
    with np.load(arrays_output, allow_pickle=False) as archive:
        archive_keys = list(archive.files)
        if len(archive_keys) != len(set(archive_keys)):
            raise RuntimeError(f"worker NPZ has duplicate keys: {archive_keys}")
        arrays = {key: np.asarray(archive[key]).copy() for key in archive_keys}
    execution["array_archive_authentication"] = validate_worker_arrays(
        result, arrays
    )
    return result, arrays, execution


def build_report(
    cases: Sequence[tuple[int, int, int]], *, timeout: float
) -> dict[str, Any]:
    requested_comparison_kinds = validate_case_matrix(cases)
    execution_provenance = committed_execution_provenance()

    gpu_pool = _load_harness_module("gpu_pool")
    inherited_slot = os.environ.get("ECS_GPU_SLOT")
    lease_context = (
        nullcontext(None)
        if inherited_slot is not None
        else gpu_pool.acquire_gpu_slot()
    )
    results: list[dict[str, Any]] = []
    arrays_by_case: dict[str, dict[str, Any]] = {}
    executions: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="ecs_peps_fet_replay_") as temporary:
        directory = Path(temporary)
        with lease_context as lease:
            child_env = (
                dict(os.environ) if lease is None else lease.child_env(dict(os.environ))
            )
            for case in cases:
                result, arrays, execution = _run_worker_case(
                    case, directory, timeout=timeout, child_env=child_env
                )
                results.append(result)
                arrays_by_case[result["case_id"]] = arrays
                executions.append(execution)

        baseline = results[0]
        baseline_arrays = arrays_by_case[baseline["case_id"]]
        comparisons = [
            compare_worker_results(
                baseline,
                candidate,
                baseline_arrays,
                arrays_by_case[candidate["case_id"]],
            )
            for candidate in results[1:]
        ]
        observed_comparison_kinds = validate_comparison_kinds(comparisons)

    input_hashes = {result["input_identity_sha256"] for result in results}
    if len(input_hashes) != 1:
        raise RuntimeError(f"worker fixed-input identities disagree: {sorted(input_hashes)}")
    entropy_red = [
        result["case_id"]
        for result in results
        if result["entropy_gate"]["verdict"] != "PASS"
    ]
    fet_contract_gate = aggregate_fet_fallback_contract(results)
    replay_verdict = summarize_replay(comparisons)
    report = {
        "schema": SCHEMA,
        "protocol_status": "DIAGNOSTIC_ONLY_NOT_CERTIFICATION",
        "git_commit": execution_provenance["git_commit"],
        "execution_provenance": execution_provenance,
        "fixed_input_identity_sha256": next(iter(input_hashes)),
        "cases": results,
        "fresh_process_execution": executions,
        "comparisons": comparisons,
        "required_comparison_kinds": sorted(REQUIRED_COMPARISON_KINDS),
        "requested_comparison_kinds": sorted(requested_comparison_kinds),
        "observed_comparison_kinds": sorted(observed_comparison_kinds),
        "replay_verdict": replay_verdict,
        "replay_passed": replay_verdict.startswith("PASS_"),
        "replay_scope": (
            "captured per-cut maps and scalars, round dense state, "
            "entropy/leakage scalars, and packed record payload"
        ),
        "entropy_gate": {
            "verdict": "PASS" if not entropy_red else "RED",
            "red_case_ids": entropy_red,
            "GF2_reference": ENTROPY_REFERENCE,
            "tolerance": ENTROPY_TOL,
            "leak_mass_tolerance": LEAK_MASS_TOL,
            "leakage_off_is_precondition": True,
        },
        "fet_fallback_contract_gate": fet_contract_gate,
        "overall_verdict": evaluate_overall_verdict(
            replay_verdict=replay_verdict,
            entropy_red_case_ids=entropy_red,
            fet_verdict=fet_contract_gate["verdict"],
        ),
        "claim_boundary": {
            "diagnostic_execution_success_is_not_scientific_pass": True,
            "local_Fid_gamma_is_not_record_faithfulness": True,
            "state_entropy_gate_must_remain_visible": True,
            "deterministic_contract_violation_remains_red": True,
            "complete_record_law_certified": False,
            "production_behavior_changed": False,
        },
    }
    report["content_hash_sha256"] = report_content_hash(report)
    return report


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--case",
        action="append",
        type=parse_case,
        dest="cases",
        help=(
            "fresh-process case CUDA_SEED:DEBUG_0_OR_1:REPETITION; repeat the "
            "option to override the four default cases"
        ),
    )
    parser.add_argument("--timeout", type=float, default=7200.0)
    parser.add_argument("--fail-on-replay-divergence", action="store_true")
    parser.add_argument("--fail-on-scientific-red", action="store_true")

    # Internal worker arguments.  They are explicit so a worker invocation is
    # reproducible from its command line, but the parent owns normal use.
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--worker-output", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--arrays-output", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--cuda-seed", type=int, help=argparse.SUPPRESS)
    parser.add_argument(
        "--fidcurve-debug",
        type=int,
        choices=(0, 1),
        help=argparse.SUPPRESS,
    )
    parser.add_argument("--repetition", type=int, default=0, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if args.worker:
        required = {
            "worker_output": args.worker_output,
            "arrays_output": args.arrays_output,
            "cuda_seed": args.cuda_seed,
            "fidcurve_debug": args.fidcurve_debug,
        }
        missing = [name for name, value in required.items() if value is None]
        if missing:
            parser.error(f"worker mode requires {', '.join(missing)}")
        _worker_run(
            cuda_seed=int(args.cuda_seed),
            fidcurve_debug=int(args.fidcurve_debug),
            repetition=int(args.repetition),
            output=args.worker_output,
            arrays_output=args.arrays_output,
        )
        return

    cases = tuple(args.cases) if args.cases else DEFAULT_CASES
    report = build_report(cases, timeout=float(args.timeout))
    byte_hash = write_json_atomic(args.output, report)
    print(
        "PEPS_FET_REPLAY_AUDIT",
        f"replay={report['replay_verdict']}",
        f"entropy={report['entropy_gate']['verdict']}",
        f"fet_contract={report['fet_fallback_contract_gate']['verdict']}",
        f"overall={report['overall_verdict']}",
        f"artifact={args.output}",
        f"content_sha256={report['content_hash_sha256']}",
        f"byte_sha256={byte_hash}",
        flush=True,
    )
    if args.fail_on_replay_divergence and not report["replay_passed"]:
        raise SystemExit(2)
    if args.fail_on_scientific_red and report["overall_verdict"] != "PASS":
        raise SystemExit(3)


if __name__ == "__main__":
    main()
