#!/usr/bin/env python3
"""Run the frozen two-qubit MCWF X/Z fixture in isolated CPU QuTiP.

The worker imports no simulator package.  It uses QuTiP ``mcsolve`` for the
continuous-time jump trajectories and implements the neutral fixture's
declared X/Z projectors and reset instruments directly from kets.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from importlib import metadata, util
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from typing import Any

import numpy as np
import qutip
import scipy

import qutip_mcwf_xz_protocol as protocol


SCHEMA = "error_coupling_simulator.external_baseline.qutip_mcwf_xz_record.v3"
EXPECTED_ENVIRONMENT = "ecs-baseline-qutip"
EXPECTED_QUTIP_COMMIT = "f343ee3ca273a4ea19f6bebbd6f563354ea309ed"
EXPECTED_QUTIP_VERSION = "5.4.0.dev0+f343ee3"
REPO = Path(__file__).resolve().parents[2]
BASELINE_REPO = REPO / "external" / "baselines" / "qutip"
DEFAULT_REGISTRY = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "mcwf_xz_comparison_registry.json"
)
SELECTED_QUTIP_SOURCES = (
    "qutip/__init__.py",
    "qutip/solver/mcsolve.py",
    "qutip/solver/multitrajresult.py",
)
SANITIZED_INHERITED_ENVIRONMENT_KEYS = (
    "CONDA_DEFAULT_ENV",
    "CONDA_EXE",
    "CONDA_PREFIX",
    "CONDA_PROMPT_MODIFIER",
    "CONDA_PYTHON_EXE",
    "CONDA_SHLVL",
    "CUDA_HOME",
    "LD_LIBRARY_PATH",
    "VIRTUAL_ENV",
    "_CE_CONDA",
    "_CE_M",
)
MCWF_SOLVER_OPTIONS = {
    "map": "serial",
    "progress_bar": False,
    "store_final_state": True,
    "keep_runs_results": True,
    "improved_sampling": False,
    "method": "vern7",
    "atol": 1.0e-10,
    "rtol": 1.0e-8,
    "nsteps": 10_000,
    "mc_corr_eps": 1.0e-12,
    "norm_steps": 50,
    "norm_t_tol": 1.0e-8,
    "norm_tol": 1.0e-8,
    "norm_min_step": 0.01,
}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _distribution_content_identity(
    distribution: metadata.Distribution,
) -> dict[str, Any]:
    """Hash every installed file declared by the wheel/editable distribution."""

    declared = distribution.files
    if not declared:
        raise RuntimeError("installed QuTiP distribution has no file inventory")
    digest = hashlib.sha256()
    count = 0
    for relative in sorted(declared, key=lambda item: item.as_posix()):
        path = Path(distribution.locate_file(relative)).resolve()
        if path.suffix == ".pyc":
            continue
        if not path.is_file():
            raise RuntimeError(f"installed QuTiP distribution file missing: {relative}")
        encoded = relative.as_posix().encode("utf-8")
        payload = path.read_bytes()
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
        count += 1
    if count == 0:
        raise RuntimeError("installed QuTiP distribution inventory is empty")
    return {"file_count": count, "sha256": digest.hexdigest()}


def _git_at(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _runtime_provenance() -> dict[str, Any]:
    if "PYTHONPATH" in os.environ:
        raise RuntimeError("isolated QuTiP worker refuses caller-provided PYTHONPATH")
    leaked_parent_markers = sorted(
        key
        for key in os.environ
        if key.startswith("CONDA_")
        or key.startswith("_CE_")
        or key in {"CUDA_HOME", "LD_LIBRARY_PATH", "VIRTUAL_ENV"}
    )
    if leaked_parent_markers:
        raise RuntimeError(
            "isolated QuTiP worker inherited parent environment markers: "
            f"{leaked_parent_markers!r}"
        )
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "":
        raise RuntimeError("isolated QuTiP worker requires CUDA_VISIBLE_DEVICES='' ")
    cache_paths = {
        "home": Path(os.environ.get("HOME", "")).resolve(),
        "xdg_cache_home": Path(os.environ.get("XDG_CACHE_HOME", "")).resolve(),
        "matplotlib_config": Path(os.environ.get("MPLCONFIGDIR", "")).resolve(),
    }
    private_roots = {path.parent for path in cache_paths.values()}
    if (
        len(private_roots) != 1
        or {path.name for path in cache_paths.values()}
        != {"home", "xdg-cache", "mpl-config"}
        or any(not path.is_dir() or path.is_symlink() for path in cache_paths.values())
    ):
        raise RuntimeError("isolated QuTiP worker cache roots are not private")
    private_root = private_roots.pop()
    private_root_mode = private_root.stat().st_mode & 0o777
    if private_root_mode & 0o077:
        raise RuntimeError("isolated QuTiP worker private root is not owner-only")
    prefix = Path(sys.prefix).resolve()
    executable = Path(sys.executable).resolve()
    module_file = Path(qutip.__file__).resolve()
    if prefix.name != EXPECTED_ENVIRONMENT or not executable.is_relative_to(prefix):
        raise RuntimeError(
            f"QuTiP worker must run inside {EXPECTED_ENVIRONMENT!r}, got {prefix}"
        )
    if not module_file.is_relative_to(prefix):
        raise RuntimeError(f"QuTiP import escaped isolated prefix: {module_file}")
    if util.find_spec("error_coupling_simulator") is not None:
        raise RuntimeError("project implementation is importable in QuTiP baseline")
    project_modules = sorted(
        name
        for name in sys.modules
        if name == "error_coupling_simulator"
        or name.startswith("error_coupling_simulator.")
    )
    if project_modules:
        raise RuntimeError("project implementation leaked into QuTiP worker")
    observed_commit = _git_at(BASELINE_REPO, "rev-parse", "HEAD")
    if observed_commit != EXPECTED_QUTIP_COMMIT:
        raise RuntimeError(
            "QuTiP baseline commit drifted: "
            f"expected {EXPECTED_QUTIP_COMMIT}, observed {observed_commit}"
        )
    dirty = _git_at(
        BASELINE_REPO,
        "status",
        "--porcelain",
        "--untracked-files=all",
    )
    if dirty:
        raise RuntimeError(f"QuTiP baseline clone is not pristine:\n{dirty}")
    observed_tree = _git_at(BASELINE_REPO, "rev-parse", "HEAD^{tree}")
    if qutip.__version__ != EXPECTED_QUTIP_VERSION:
        raise RuntimeError(
            "QuTiP runtime version drifted: "
            f"expected {EXPECTED_QUTIP_VERSION}, observed {qutip.__version__}"
        )

    distribution = metadata.distribution("qutip")
    direct_url_text = distribution.read_text("direct_url.json")
    if direct_url_text is None:
        raise RuntimeError("installed QuTiP distribution has no direct_url.json")
    direct_url = json.loads(direct_url_text)
    expected_url = BASELINE_REPO.resolve().as_uri()
    vcs_info = direct_url.get("vcs_info", {})
    if (
        direct_url.get("url") != expected_url
        or vcs_info.get("vcs") != "git"
        or vcs_info.get("commit_id") != EXPECTED_QUTIP_COMMIT
        or vcs_info.get("requested_revision") != EXPECTED_QUTIP_COMMIT
    ):
        raise RuntimeError(f"installed QuTiP direct_url drifted: {direct_url!r}")

    package_root = module_file.parent
    selected_installed_sha256: dict[str, str] = {}
    selected_clone_sha256: dict[str, str] = {}
    for relative in SELECTED_QUTIP_SOURCES:
        package_relative = Path(relative).relative_to("qutip")
        installed_path = package_root / package_relative
        clone_path = BASELINE_REPO / relative
        installed_sha256 = _sha256_file(installed_path)
        clone_sha256 = _sha256_file(clone_path)
        if installed_sha256 != clone_sha256:
            raise RuntimeError(f"installed QuTiP source hash drifted: {relative}")
        selected_installed_sha256[relative] = installed_sha256
        selected_clone_sha256[relative] = clone_sha256

    resolved_sys_path = [str(Path(entry).resolve()) for entry in sys.path if entry]
    if str(REPO.resolve()) in resolved_sys_path:
        raise RuntimeError("project repository root leaked into QuTiP sys.path")
    return {
        "environment": EXPECTED_ENVIRONMENT,
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
        "python_prefix": str(prefix),
        "python_executable": str(executable),
        "cuda_visible_devices": "",
        "qutip_version": qutip.__version__,
        "qutip_module_file": str(module_file),
        "baseline_repo": str(BASELINE_REPO.relative_to(REPO)),
        "expected_commit": EXPECTED_QUTIP_COMMIT,
        "observed_commit": observed_commit,
        "observed_tree": observed_tree,
        "clone_pristine": True,
        "pythonpath_env": None,
        "project_modules_imported": [],
        "project_package_find_spec": None,
        "resolved_sys_path": resolved_sys_path,
        "cache_isolation": {
            **{name: str(path) for name, path in cache_paths.items()},
            "common_private_root": str(private_root),
            "common_private_root_mode_octal": f"{private_root_mode:03o}",
            "all_cache_roots_exist_and_are_nonsymlink_directories": True,
            "private_root_owner_only": True,
        },
        "sanitized_parent_environment": {
            key: os.environ.get(key)
            for key in SANITIZED_INHERITED_ENVIRONMENT_KEYS
        },
        "worker_sha256": _sha256_file(Path(__file__).resolve()),
        "protocol_sha256": _sha256_file(Path(protocol.__file__).resolve()),
        "installed_distribution": {
            "name": distribution.metadata["Name"],
            "version": distribution.version,
            "direct_url": direct_url,
            "selected_installed_sha256": selected_installed_sha256,
            "selected_clone_sha256": selected_clone_sha256,
            "selected_sources_match_clone": True,
            "content_identity": _distribution_content_identity(distribution),
        },
    }


def _lift_one_site(operator: qutip.Qobj, target: int) -> qutip.Qobj:
    factors = [qutip.qeye(2), qutip.qeye(2)]
    factors[target] = operator
    return qutip.tensor(factors)


def _measurement_ket(basis: str, label: int) -> qutip.Qobj:
    zero = qutip.basis(2, 0)
    one = qutip.basis(2, 1)
    if basis == "Z":
        return zero if label == 0 else one
    if basis == "X":
        return (zero + one).unit() if label == 0 else (zero - one).unit()
    raise ValueError(f"unsupported neutral measurement basis {basis!r}")


def _sample_local_measurement(
    state: qutip.Qobj,
    *,
    target: int,
    basis: str,
    reset: bool,
    rng: np.random.Generator,
    numerical_zero: float,
) -> tuple[int, qutip.Qobj]:
    projectors = []
    candidates = []
    probabilities = []
    for label in (0, 1):
        ket = _measurement_ket(basis, label)
        projector = _lift_one_site(ket * ket.dag(), target)
        candidate = projector * state
        probability = float(candidate.norm() ** 2)
        projectors.append(projector)
        candidates.append(candidate)
        probabilities.append(probability)
    total = math.fsum(probabilities)
    if not math.isfinite(total) or abs(total - 1.0) > numerical_zero:
        raise RuntimeError(f"invalid QuTiP measurement mass {probabilities!r}")
    probability_zero = probabilities[0] / total
    label = 0 if float(rng.random()) < probability_zero else 1
    selected = candidates[label]
    norm = float(selected.norm())
    if not math.isfinite(norm) or norm <= 0.0:
        raise RuntimeError("sampled zero-norm QuTiP measurement branch")
    conditioned = selected / norm
    if not reset:
        return label, conditioned
    measured = _measurement_ket(basis, label)
    reset_state = _measurement_ket("X", 0) if basis == "X" else _measurement_ket("Z", 0)
    reset_map = _lift_one_site(reset_state * measured.dag(), target)
    reset_candidate = reset_map * conditioned
    reset_norm = float(reset_candidate.norm())
    if not math.isfinite(reset_norm) or reset_norm <= 0.0:
        raise RuntimeError("invalid QuTiP post-measurement reset norm")
    return label, reset_candidate / reset_norm


def _run_mcwf_interval(
    initial_state: qutip.Qobj,
    *,
    fixture: dict[str, Any],
    seed: int,
) -> tuple[list[qutip.Qobj], int]:
    identity = qutip.tensor(qutip.qeye(2), qutip.qeye(2))
    destroy = qutip.destroy(2)
    number = qutip.basis(2, 1) * qutip.basis(2, 1).dag()
    local_operators = {
        "sigma_minus": destroy,
        "sigma_plus": destroy.dag(),
        "number_dephasing": number,
    }
    collapse_operators = []
    for term in fixture["collapse_terms"]:
        rate = float(term["generator_rate_per_ns"])
        collapse_operators.append(
            math.sqrt(rate)
            * _lift_one_site(
                local_operators[term["family"]],
                int(term["target"]),
            )
        )
    result = qutip.mcsolve(
        0.0 * identity,
        initial_state,
        [0.0, float(fixture["evolution_duration_ns"])],
        collapse_operators,
        ntraj=int(fixture["trajectory_count"]),
        seeds=int(seed),
        options=MCWF_SOLVER_OPTIONS,
    )
    final_states = result.runs_final_states
    if final_states is None or len(final_states) != int(fixture["trajectory_count"]):
        raise RuntimeError("QuTiP did not retain every MCWF final state")
    if result.stats.get("num_collapse") != len(collapse_operators):
        raise RuntimeError("QuTiP MCWF collapse-operator count drifted")
    jump_count = sum(len(trajectory) for trajectory in result.collapse)
    return list(final_states), int(jump_count)


def _histogram(records: list[tuple[int, ...]]) -> dict[str, Any]:
    counts = Counter(records)
    ordered = sorted(counts)
    total = len(records)
    return {
        "records": [list(row) for row in ordered],
        "counts": [int(counts[row]) for row in ordered],
        "probabilities": [float(counts[row] / total) for row in ordered],
    }


def _histogram_mapping(histogram: dict[str, Any]) -> dict[tuple[int, ...], float]:
    return {
        tuple(row): float(probability)
        for row, probability in zip(
            histogram["records"], histogram["probabilities"], strict=True
        )
    }


def _one_sample_tv(
    observed: dict[tuple[int, ...], float],
    expected: dict[tuple[int, ...], float],
    *,
    sample_count: int,
    alphabet_size: int,
    alpha: float,
) -> dict[str, Any]:
    radius = protocol.multinomial_tv_radius(
        sample_count=sample_count,
        alphabet_size=alphabet_size,
        alpha=alpha,
    )
    tv = protocol.total_variation(observed, expected)
    return {
        "schema": (
            "error_coupling_simulator.external_baseline."
            "one_sample_multinomial_tv.v1"
        ),
        "total_variation": tv,
        "sample_count": sample_count,
        "alphabet_size": alphabet_size,
        "alpha": alpha,
        "tv_radius": radius,
        "gate_rule": "observed_total_variation <= tv_radius",
        "passed": bool(tv <= radius),
    }


def build_report(
    fixture_path: Path,
    registry_path: Path = DEFAULT_REGISTRY,
) -> dict[str, Any]:
    fixture = protocol.load_fixture(fixture_path)
    registry = protocol.load_comparison_registry(registry_path)
    if fixture["comparison_family_alpha"] != registry["comparison_family_alpha"]:
        raise RuntimeError("fixture comparison alpha drifted from registry")
    runtime = _runtime_provenance()
    numerical_zero = float(fixture["numerical_zero"])
    trajectory_count = int(fixture["trajectory_count"])
    initial = qutip.basis([2, 2], [0, 1])
    reset_initial = qutip.tensor(_measurement_ket("X", 0), _measurement_ket("Z", 0))
    first_states, first_jump_count = _run_mcwf_interval(
        initial,
        fixture=fixture,
        seed=int(fixture["qutip_mcwf_seed"]),
    )
    second_states, second_jump_count = _run_mcwf_interval(
        reset_initial,
        fixture=fixture,
        seed=int(fixture["qutip_mcwf_seed"]) + 1,
    )
    measurement_rng = np.random.default_rng(int(fixture["qutip_measurement_seed"]))
    records: list[tuple[int, ...]] = []
    reset_residuals: list[float] = []
    expected_reset_dm = qutip.ket2dm(reset_initial).full()
    for first_state, second_state in zip(first_states, second_states, strict=True):
        x_before, after_x_reset = _sample_local_measurement(
            first_state,
            target=0,
            basis="X",
            reset=True,
            rng=measurement_rng,
            numerical_zero=numerical_zero,
        )
        z_before, after_both_resets = _sample_local_measurement(
            after_x_reset,
            target=1,
            basis="Z",
            reset=True,
            rng=measurement_rng,
            numerical_zero=numerical_zero,
        )
        reset_residuals.append(
            float(
                np.linalg.norm(
                    qutip.ket2dm(after_both_resets).full() - expected_reset_dm
                )
            )
        )
        x_after, after_x = _sample_local_measurement(
            second_state,
            target=0,
            basis="X",
            reset=False,
            rng=measurement_rng,
            numerical_zero=numerical_zero,
        )
        z_after, _after_z = _sample_local_measurement(
            after_x,
            target=1,
            basis="Z",
            reset=False,
            rng=measurement_rng,
            numerical_zero=numerical_zero,
        )
        records.append((x_before, z_before, x_after, z_after))

    label_histogram = _histogram(records)
    binary_histogram = _histogram(records)
    observed_final_state_dtypes = sorted(
        {
            str(np.asarray(state.full()).dtype)
            for state in (*first_states, *second_states)
        }
    )
    observed_probability_array_dtype = str(
        np.asarray(label_histogram["probabilities"]).dtype
    )
    if observed_final_state_dtypes != ["complex128"]:
        raise RuntimeError(
            f"QuTiP final-state dtype drifted: {observed_final_state_dtypes!r}"
        )
    if observed_probability_array_dtype != "float64":
        raise RuntimeError(
            "QuTiP probability dtype drifted: "
            f"{observed_probability_array_dtype!r}"
        )
    analytic = protocol.analytic_binary_distribution(fixture)
    component_alpha = float(registry["per_entry_alpha"])
    joint_tv = _one_sample_tv(
        _histogram_mapping(binary_histogram),
        analytic,
        sample_count=trajectory_count,
        alphabet_size=16,
        alpha=component_alpha,
    )
    marginal_diagnostics = {}
    for key in sorted(protocol.EXPECTED_DIRECTED_MARGINALS[fixture["fixture_id"]]):
        column = fixture["measurement_keys"].index(key)
        marginal_diagnostics[key] = protocol.total_variation(
            protocol.binary_column_marginal(
                _histogram_mapping(binary_histogram), column=column
            ),
            protocol.binary_column_marginal(analytic, column=column),
        )
    max_reset_residual = max(reset_residuals, default=math.inf)
    reset_passed = bool(max_reset_residual <= numerical_zero)
    total_jump_count = first_jump_count + second_jump_count
    all_checks_passed = bool(
        reset_passed
        and joint_tv["passed"]
        and total_jump_count > 0
        and math.fsum(label_histogram["counts"]) == trajectory_count
        and math.fsum(binary_histogram["counts"]) == trajectory_count
    )
    report = {
        "schema": SCHEMA,
        "claim_boundary": fixture["claim_boundary"],
        "fixture": {
            "schema": fixture["schema"],
            "id": fixture["fixture_id"],
            "path": str(Path(fixture_path).resolve()),
            "sha256": protocol.fixture_sha256(fixture_path),
            "initial_levels": fixture["initial_levels"],
            "collapse_terms": fixture["collapse_terms"],
            "evolution_segments_ns": fixture["evolution_segments_ns"],
            "comparison_registry_sha256": registry["sha256"],
        },
        "runtime_provenance": runtime,
        "numerical_provenance": {
            "state_dtype": observed_final_state_dtypes[0],
            "observed_final_state_dtypes": observed_final_state_dtypes,
            "probability_dtype": observed_probability_array_dtype,
            "observed_probability_array_dtype": (
                observed_probability_array_dtype
            ),
            "precision_purpose": (
                "independent continuous-time MCWF trajectory and X/Z Record-law differential"
            ),
            "repository_environment_lock": None,
            "environment_lock_status": "not_available_runtime_identity_recorded",
        },
        "solver": {
            "name": "qutip.mcsolve",
            "unravelling": "continuous_time_monte_carlo_wave_function",
            "device": "cpu",
            "trajectory_count": trajectory_count,
            "collapse_operator_count": len(fixture["collapse_terms"]),
            "first_interval_jump_count": first_jump_count,
            "second_interval_jump_count": second_jump_count,
            "total_jump_count": total_jump_count,
            "retained_final_state_count_per_interval": trajectory_count,
            "integrator_options": dict(MCWF_SOLVER_OPTIONS),
        },
        "record": {
            "measurement_keys": fixture["measurement_keys"],
            "measurement_targets": fixture["measurement_targets"],
            "measurement_bases": fixture["measurement_bases"],
            "reset_after": fixture["reset_after"],
            "label_records": label_histogram["records"],
            "label_counts": label_histogram["counts"],
            "label_probabilities": label_histogram["probabilities"],
            "binary_records": binary_histogram["records"],
            "binary_counts": binary_histogram["counts"],
            "binary_probabilities": binary_histogram["probabilities"],
            "qubit_label_to_binary_mapping": "identity_0_to_0_1_to_1",
        },
        "reset_checks": {
            "X_reset_state": "|+>",
            "Z_reset_state": "|0>",
            "max_post_reset_state_l2": max_reset_residual,
            "numerical_zero": numerical_zero,
            "passed": reset_passed,
        },
        "analytic_reference": {
            "derivation": (
                "closed-form local Lindblad population/coherence evolution composed "
                "with the ordered selective measurement and reset maps"
            ),
            "registered_statistic": next(
                entry["statistic_id"]
                for entry in protocol.comparison_entries_for_fixture(
                    registry, fixture["fixture_id"]
                )
                if entry["comparison_kind"] == "one_sample_qutip_dense"
            ),
            "registry_entry_count": registry["entry_count"],
            "bonferroni_component_alpha": component_alpha,
            "joint_tv": joint_tv,
            "nonverdict_directed_marginal_tv": marginal_diagnostics,
        },
        "statistical_limitations": {
            "finite_ntraj": trajectory_count,
            "rare_outcome_resolution_floor": 1.0 / trajectory_count,
            "scope": fixture["fixture_id"],
            "not_established": [
                "trajectory-by-trajectory coupling to the project RNG",
                "qutrit or leakage label semantics",
                "complete multi-round QEC Record faithfulness",
                "scalability or production readiness",
            ],
        },
        "atomic_publication": {
            "protocol": (
                "unlink_previous_fsync_parent_then_mkstemp_file_fsync_"
                "replace_parent_fsync"
            ),
            "stale_output_invalidated_before_compute": True,
            "file_fsync_before_replace": True,
            "parent_directory_fsync_after_replace": True,
            "durability_failure_removes_destination": True,
            "artifact_presence_means_current_invocation_completed": True,
        },
        "all_checks_passed": all_checks_passed,
    }
    report["content_hash"] = protocol.canonical_content_hash(report)
    return report


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(str(Path(path).resolve()), flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _prepare_output_path(path: Path) -> None:
    destination = path.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        destination.unlink()
    except FileNotFoundError:
        pass
    _fsync_directory(destination.parent)


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    destination = path.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
    )
    published = False
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        published = True
        _fsync_directory(destination.parent)
    except BaseException:
        if published:
            try:
                destination.unlink()
            except FileNotFoundError:
                pass
            try:
                _fsync_directory(destination.parent)
            except OSError:
                pass
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    _prepare_output_path(args.output)
    report = build_report(args.fixture, args.registry)
    _atomic_write_json(args.output, report)
    print(f"isolated QuTiP MCWF X/Z: {'PASS' if report['all_checks_passed'] else 'FAIL'}")
    print(f"wrote {args.output.resolve()}")
    return 0 if report["all_checks_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
