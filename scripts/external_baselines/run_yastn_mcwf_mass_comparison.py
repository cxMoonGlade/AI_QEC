#!/usr/bin/env python3
"""Run an isolated YASTN product-MPS candidate-mass comparison.

This adapter imports no project implementation.  It reconstructs the frozen
six-site T1 candidate family with YASTN product MPS objects, checks every MPS
norm against a hand-computed reference, exercises an omitted-jump corruption
falsifier, and writes one neutral JSON artifact.  It is a candidate-mass and
MPS-representation comparator, not a QEC Record or trajectory-law oracle.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Sequence


SCHEMA = "ai_qec.external_baseline.yastn_mcwf_candidate_mass.v1"
EXPECTED_YASTN_VERSION = "1.6.2.dev384+g595bd802b"
EXPECTED_YASTN_COMMIT = "595bd802ba0753a187b4bf7fd5c6d5007c0170d0"
EXPECTED_ENVIRONMENT = "ecs-baseline-yastn"
NUM_SITES = 6
EXPECTED_INITIAL_NORM_SQUARED = 1.0
EXPECTED_NO_JUMP_NORM_SQUARED = 1.0 / 4096.0
EXPECTED_JUMP_NORMS_SQUARED = (1.0,) * NUM_SITES
ABS_TOLERANCE = 1.0e-15

REPO = Path(__file__).resolve().parents[2]
BASELINE_REPO = REPO / "external" / "baselines" / "yastn"


def analyze_candidate_masses(
    *,
    initial_norm_squared: float,
    no_jump_norm_squared: float,
    jump_norms_squared: Sequence[float],
) -> dict[str, Any]:
    """Validate and compare one raw MCWF candidate-mass family."""

    initial = _finite_nonnegative(initial_norm_squared, "initial_norm_squared")
    no_jump = _finite_nonnegative(no_jump_norm_squared, "no_jump_norm_squared")
    jumps = [
        _finite_nonnegative(value, f"jump_norms_squared[{index}]")
        for index, value in enumerate(jump_norms_squared)
    ]
    candidate_mass = math.fsum([no_jump, *jumps])
    residual = abs(candidate_mass - initial)
    matches = bool(
        len(jumps) == NUM_SITES
        and math.isclose(
            initial,
            EXPECTED_INITIAL_NORM_SQUARED,
            rel_tol=0.0,
            abs_tol=ABS_TOLERANCE,
        )
        and math.isclose(
            no_jump,
            EXPECTED_NO_JUMP_NORM_SQUARED,
            rel_tol=0.0,
            abs_tol=ABS_TOLERANCE,
        )
        and all(
            math.isclose(
                observed,
                expected,
                rel_tol=0.0,
                abs_tol=ABS_TOLERANCE,
            )
            for observed, expected in zip(jumps, EXPECTED_JUMP_NORMS_SQUARED)
        )
    )
    return {
        "initial_norm_squared": initial,
        "no_jump_norm_squared": no_jump,
        "jump_norms_squared": jumps,
        "candidate_mass": candidate_mass,
        "candidate_mass_residual": residual,
        "matches_frozen_reference": matches,
        "corruption_falsifier_detected": not matches,
    }


def _finite_nonnegative(value: float, name: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a real value, not bool")
    normalized = float(value)
    if not math.isfinite(normalized) or normalized < 0.0:
        raise ValueError(f"{name} must be finite and nonnegative")
    return normalized


def _git(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(BASELINE_REPO), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _assert_runtime_provenance(yastn_module: Any) -> dict[str, Any]:
    observed_commit = _git("rev-parse", "HEAD")
    if observed_commit != EXPECTED_YASTN_COMMIT:
        raise RuntimeError(
            "YASTN baseline commit drifted: "
            f"expected {EXPECTED_YASTN_COMMIT}, observed {observed_commit}"
        )
    dirty = _git("status", "--porcelain", "--untracked-files=all")
    if dirty:
        raise RuntimeError(f"YASTN baseline clone is not pristine:\n{dirty}")
    observed_version = str(yastn_module.__version__)
    if observed_version != EXPECTED_YASTN_VERSION:
        raise RuntimeError(
            "YASTN runtime version drifted: "
            f"expected {EXPECTED_YASTN_VERSION}, observed {observed_version}"
        )
    prefix = Path(sys.prefix).resolve()
    executable = Path(sys.executable).resolve()
    module_file = Path(yastn_module.__file__).resolve()
    if prefix.name != EXPECTED_ENVIRONMENT or not executable.is_relative_to(prefix):
        raise RuntimeError(
            f"YASTN comparator must run inside {EXPECTED_ENVIRONMENT!r}, got {prefix}"
        )
    if not module_file.is_relative_to(prefix):
        raise RuntimeError(f"YASTN import escaped isolated prefix: {module_file}")
    return {
        "environment": EXPECTED_ENVIRONMENT,
        "python_prefix": str(prefix),
        "python_executable": str(executable),
        "yastn_version": observed_version,
        "yastn_module_file": str(module_file),
        "baseline_repo": str(BASELINE_REPO.relative_to(REPO)),
        "expected_commit": EXPECTED_YASTN_COMMIT,
        "observed_commit": observed_commit,
        "clone_pristine": True,
    }


def build_report() -> dict[str, Any]:
    """Construct the comparison report using only YASTN public MPS APIs."""

    import yastn
    import yastn.tn.mps as mps

    provenance = _assert_runtime_provenance(yastn)
    operators = yastn.operators.Spin12(sym="dense")
    ground = operators.vec_z(val=1)
    excited = operators.vec_z(val=-1)

    initial = mps.product_mps(excited, N=NUM_SITES)
    no_jump = mps.product_mps(0.5 * excited, N=NUM_SITES)
    jump_states = [
        mps.product_mps(
            [ground if site == jump_site else excited for site in range(NUM_SITES)]
        )
        for jump_site in range(NUM_SITES)
    ]
    observed = analyze_candidate_masses(
        initial_norm_squared=float(initial.norm()) ** 2,
        no_jump_norm_squared=float(no_jump.norm()) ** 2,
        jump_norms_squared=[float(state.norm()) ** 2 for state in jump_states],
    )
    corrupted = analyze_candidate_masses(
        initial_norm_squared=observed["initial_norm_squared"],
        no_jump_norm_squared=observed["no_jump_norm_squared"],
        jump_norms_squared=[*observed["jump_norms_squared"][:-1], 0.0],
    )
    bond_dimensions = {
        "initial": list(initial.get_bond_dimensions()),
        "no_jump": list(no_jump.get_bond_dimensions()),
        "jumps": [list(state.get_bond_dimensions()) for state in jump_states],
    }
    bond_one = all(
        dimension == 1
        for dimensions in [
            bond_dimensions["initial"],
            bond_dimensions["no_jump"],
            *bond_dimensions["jumps"],
        ]
        for dimension in dimensions
    )
    all_checks_passed = bool(
        observed["matches_frozen_reference"]
        and corrupted["corruption_falsifier_detected"]
        and bond_one
    )
    return {
        "schema": SCHEMA,
        "claim_boundary": (
            "independent product-MPS candidate-mass comparator; not a QEC Record, "
            "trajectory-law, or restricted-acceptance oracle"
        ),
        "fixture": {
            "id": "six_site_product_t1_raw_candidate_mass",
            "num_sites": NUM_SITES,
            "gamma_1_per_ns": 0.05,
            "dt_ns": 20.0,
            "local_no_jump_amplitude": 0.5,
            "initial_state": "|111111>",
        },
        "provenance": provenance,
        "bond_dimensions": bond_dimensions,
        "all_states_have_bond_dimension_one": bond_one,
        "observed": observed,
        "omitted_jump_corruption": corrupted,
        "all_checks_passed": all_checks_passed,
    }


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report()
    _atomic_write_json(args.output, report)
    print(
        f"YASTN MCWF candidate-mass comparator: "
        f"{'PASS' if report['all_checks_passed'] else 'FAIL'}"
    )
    print(f"wrote {args.output.resolve()}")
    return 0 if report["all_checks_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
