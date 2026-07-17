#!/usr/bin/env python3
"""Run an isolated YASTN product-MPS candidate-mass comparison.

This adapter imports no project implementation. It reconstructs the frozen
six-site T1 candidate family with public YASTN tensor and product-MPS APIs,
checks every MPS norm against a hand-computed reference, exercises an
operator-corruption falsifier, and writes one neutral JSON artifact. It is
a candidate-mass and MPS-representation comparator, not a QEC Record or
trajectory-law oracle.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import hashlib
from importlib import metadata
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any


SCHEMA = "ai_qec.external_baseline.yastn_mcwf_candidate_mass.v2"
EXPECTED_YASTN_VERSION = "1.6.2.dev384+g595bd802b"
EXPECTED_YASTN_COMMIT = "595bd802ba0753a187b4bf7fd5c6d5007c0170d0"
EXPECTED_ENVIRONMENT = "ecs-baseline-yastn"
NUM_SITES = 6
GAMMA_1_PER_NS = 0.05
DT_NS = 20.0
LOCAL_NO_JUMP_AMPLITUDE = 1.0 - 0.5 * GAMMA_1_PER_NS * DT_NS
EXPECTED_INITIAL_NORM_SQUARED = 1.0
EXPECTED_NO_JUMP_NORM_SQUARED = LOCAL_NO_JUMP_AMPLITUDE ** (2 * NUM_SITES)
EXPECTED_JUMP_NORMS_SQUARED = (GAMMA_1_PER_NS * DT_NS,) * NUM_SITES
ABS_TOLERANCE = 1.0e-15

REPO = Path(__file__).resolve().parents[2]
BASELINE_REPO = REPO / "external" / "baselines" / "yastn"
ADAPTER = REPO / "scripts" / "external_baselines" / Path(__file__).name


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


def validate_yastn_direct_url(payload: object) -> dict[str, str]:
    """Require the installed distribution to bind to the frozen clone commit."""

    if not isinstance(payload, Mapping):
        raise RuntimeError("installed YASTN direct_url metadata is missing or malformed")
    expected_url = BASELINE_REPO.resolve().as_uri()
    if payload.get("url") != expected_url:
        raise RuntimeError(
            f"installed YASTN source drifted: expected {expected_url!r}, "
            f"observed {payload.get('url')!r}"
        )
    vcs_info = payload.get("vcs_info")
    if not isinstance(vcs_info, Mapping) or vcs_info.get("vcs") != "git":
        raise RuntimeError("installed YASTN direct_url is not a git VCS binding")
    commit_id = vcs_info.get("commit_id")
    if commit_id != EXPECTED_YASTN_COMMIT:
        raise RuntimeError(
            "installed YASTN commit drifted: "
            f"expected {EXPECTED_YASTN_COMMIT}, observed {commit_id}"
        )
    requested_revision = vcs_info.get("requested_revision")
    if requested_revision != EXPECTED_YASTN_COMMIT:
        raise RuntimeError(
            "installed YASTN requested revision drifted: "
            f"expected {EXPECTED_YASTN_COMMIT}, observed {requested_revision}"
        )
    return {
        "url": expected_url,
        "vcs": "git",
        "commit_id": EXPECTED_YASTN_COMMIT,
        "requested_revision": EXPECTED_YASTN_COMMIT,
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_at(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _assert_adapter_provenance() -> dict[str, Any]:
    relative_adapter = str(ADAPTER.relative_to(REPO))
    _git_at(REPO, "ls-files", "--error-unmatch", relative_adapter)
    status = _git_at(
        REPO,
        "status",
        "--porcelain",
        "--untracked-files=all",
        "--",
        relative_adapter,
    )
    if status:
        raise RuntimeError(
            "YASTN comparator adapter must be committed and clean before execution: "
            f"{status!r}"
        )
    return {
        "repo_commit": _git_at(REPO, "rev-parse", "HEAD"),
        "path": relative_adapter,
        "sha256": _sha256_file(ADAPTER),
        "tracked": True,
        "clean": True,
    }


def _assert_runtime_provenance(yastn_module: Any) -> dict[str, Any]:
    if "PYTHONPATH" in os.environ:
        raise RuntimeError("YASTN comparator refuses caller-provided PYTHONPATH")
    observed_commit = _git_at(BASELINE_REPO, "rev-parse", "HEAD")
    if observed_commit != EXPECTED_YASTN_COMMIT:
        raise RuntimeError(
            "YASTN baseline commit drifted: "
            f"expected {EXPECTED_YASTN_COMMIT}, observed {observed_commit}"
        )
    dirty = _git_at(BASELINE_REPO, "status", "--porcelain", "--untracked-files=all")
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
    resolved_sys_path = [str(Path(entry).resolve()) for entry in sys.path if entry]
    forbidden_import_roots = {str(REPO.resolve()), str(BASELINE_REPO.resolve())}
    leaked_roots = sorted(forbidden_import_roots.intersection(resolved_sys_path))
    if leaked_roots:
        raise RuntimeError(
            f"YASTN comparator sys.path contains forbidden roots: {leaked_roots}"
        )
    project_modules = [
        name
        for name in sys.modules
        if name == "error_coupling_simulator"
        or name.startswith("error_coupling_simulator.")
    ]
    if project_modules:
        raise RuntimeError("project implementation leaked into YASTN comparator process")

    distribution = metadata.distribution("yastn")
    direct_url_text = distribution.read_text("direct_url.json")
    if direct_url_text is None:
        raise RuntimeError("installed YASTN distribution has no direct_url.json binding")
    direct_url = validate_yastn_direct_url(json.loads(direct_url_text))
    distribution_files = distribution.files or ()
    record_entry = next(
        (
            entry
            for entry in distribution_files
            if entry.name == "RECORD" and ".dist-info" in str(entry)
        ),
        None,
    )
    if record_entry is None:
        raise RuntimeError("installed YASTN distribution has no RECORD file")
    record_path = Path(distribution.locate_file(record_entry)).resolve()
    selected_package_files = {
        "yastn/__init__.py": module_file,
        "yastn/tn/mps/_initialize.py": (
            module_file.parent / "tn" / "mps" / "_initialize.py"
        ),
        "yastn/tn/mps/_mps_obc.py": (
            module_file.parent / "tn" / "mps" / "_mps_obc.py"
        ),
    }
    if not all(
        path.is_file() and path.is_relative_to(prefix)
        for path in selected_package_files.values()
    ):
        raise RuntimeError("installed YASTN selected files escaped isolated prefix")
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
        "pythonpath_env": None,
        "resolved_sys_path": resolved_sys_path,
        "project_modules_imported": [],
        "installed_distribution": {
            "name": distribution.metadata["Name"],
            "version": distribution.version,
            "direct_url": direct_url,
            "record_path": str(record_path),
            "record_sha256": _sha256_file(record_path),
            "selected_package_sha256": {
                name: _sha256_file(path)
                for name, path in selected_package_files.items()
            },
        },
    }


def build_report() -> dict[str, Any]:
    """Construct the comparison report using only YASTN public MPS APIs."""

    import yastn
    import yastn.tn.mps as mps

    adapter_provenance = _assert_adapter_provenance()
    runtime_provenance = _assert_runtime_provenance(yastn)
    operators = yastn.operators.Spin12(sym="dense")
    ground = operators.vec_z(val=1)
    excited = operators.vec_z(val=-1)
    collapse_operator = math.sqrt(GAMMA_1_PER_NS) * operators.sp()
    no_jump_operator = (
        operators.I()
        - 0.5 * DT_NS * (collapse_operator.H @ collapse_operator)
    )
    no_jump_local = no_jump_operator @ excited
    jump_local = math.sqrt(DT_NS) * (collapse_operator @ excited)
    wrong_jump_local = math.sqrt(DT_NS) * (operators.sm() @ excited)
    operator_checks = {
        "computational_one_is_spin_z_minus": True,
        "computational_zero_is_spin_z_plus": True,
        "no_jump_local_action_l2": float(
            (no_jump_local - LOCAL_NO_JUMP_AMPLITUDE * excited).norm()
        ),
        "jump_local_action_l2": float((jump_local - ground).norm()),
        "wrong_sm_jump_norm": float(wrong_jump_local.norm()),
    }
    operator_checks_passed = all(
        value <= ABS_TOLERANCE
        for key, value in operator_checks.items()
        if key.endswith("_l2")
    )

    initial = mps.product_mps(excited, N=NUM_SITES)
    no_jump_mpo = mps.product_mpo(no_jump_operator, N=NUM_SITES)
    no_jump = no_jump_mpo @ initial
    jump_mpos = [
        mps.product_mpo(
            [
                math.sqrt(DT_NS) * collapse_operator
                if site == jump_site
                else operators.I()
                for site in range(NUM_SITES)
            ]
        )
        for jump_site in range(NUM_SITES)
    ]
    jump_states = [jump_mpo @ initial for jump_mpo in jump_mpos]
    observed = analyze_candidate_masses(
        initial_norm_squared=float(initial.norm()) ** 2,
        no_jump_norm_squared=float(no_jump.norm()) ** 2,
        jump_norms_squared=[float(state.norm()) ** 2 for state in jump_states],
    )
    wrong_jump_mpo = mps.product_mpo(
        [
            math.sqrt(DT_NS) * operators.sm()
            if site == NUM_SITES - 1
            else operators.I()
            for site in range(NUM_SITES)
        ]
    )
    wrong_jump_state = wrong_jump_mpo @ initial
    corrupted = analyze_candidate_masses(
        initial_norm_squared=observed["initial_norm_squared"],
        no_jump_norm_squared=observed["no_jump_norm_squared"],
        jump_norms_squared=[
            *observed["jump_norms_squared"][:-1],
            float(wrong_jump_state.norm()) ** 2,
        ],
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
        and operator_checks_passed
    )
    return {
        "schema": SCHEMA,
        "claim_boundary": (
            "external product-MPS candidate-mass comparator with an independent "
            "hand formula; not a QEC Record, trajectory-law, or restricted-acceptance oracle"
        ),
        "fixture": {
            "id": "six_site_product_t1_raw_candidate_mass",
            "num_sites": NUM_SITES,
            "gamma_1_per_ns": GAMMA_1_PER_NS,
            "dt_ns": DT_NS,
            "local_no_jump_amplitude": LOCAL_NO_JUMP_AMPLITUDE,
            "initial_state": "|111111>",
        },
        "adapter_provenance": adapter_provenance,
        "runtime_provenance": runtime_provenance,
        "local_operator_reconstruction": {
            "basis_map": {"computational_zero": "spin_z_plus", "computational_one": "spin_z_minus"},
            "no_jump_operator": "I - 0.5 * gamma_1 * dt * |1><1|",
            "collapse_operator": (
                "sqrt(gamma_1) * Spin12.sp under the declared basis map"
            ),
            "candidate_construction": "public product_mpo operators applied to initial MPS",
            "checks": operator_checks,
            "passed": operator_checks_passed,
        },
        "bond_dimensions": bond_dimensions,
        "all_states_have_bond_dimension_one": bond_one,
        "observed": observed,
        "wrong_sm_jump_operator_corruption": corrupted,
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
