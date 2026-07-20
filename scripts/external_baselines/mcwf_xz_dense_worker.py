#!/usr/bin/env python3
"""Independent dense reference for the neutral two-qubit MCWF X/Z fixtures.

The worker imports no simulator package and consumes no compiled Carrier
program. It hand-builds every matrix from the neutral fixture, constructs the
16x16 Lindblad superoperator under column-major vectorization, and composes the
declared selective measurements and reset channels on unnormalized branches.
"""

from __future__ import annotations

import argparse
import hashlib
from importlib import util
import json
import math
import os
from pathlib import Path
import platform
import sys
import tempfile
from typing import Any, Callable, Mapping

import numpy as np
import scipy
from scipy.linalg import expm

import qutip_mcwf_xz_protocol as protocol


SCHEMA = "error_coupling_simulator.external_baseline.mcwf_xz_dense_record.v1"
TermTransform = Callable[[dict[str, Any]], dict[str, Any] | None]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _array_sha256(array: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(array)
    digest = hashlib.sha256()
    digest.update(str(contiguous.shape).encode("ascii"))
    digest.update(b"\0")
    digest.update(str(contiguous.dtype).encode("ascii"))
    digest.update(b"\0")
    digest.update(contiguous.tobytes(order="C"))
    return digest.hexdigest()


def _local_operators() -> dict[str, np.ndarray]:
    zero = np.asarray([1.0, 0.0], dtype=np.complex128)
    one = np.asarray([0.0, 1.0], dtype=np.complex128)
    plus = (zero + one) / math.sqrt(2.0)
    minus = (zero - one) / math.sqrt(2.0)
    return {
        "identity": np.eye(2, dtype=np.complex128),
        "number_dephasing": np.outer(one, one.conj()),
        "sigma_minus": np.outer(zero, one.conj()),
        "sigma_plus": np.outer(one, zero.conj()),
        "X0": np.outer(plus, plus.conj()),
        "X1": np.outer(minus, minus.conj()),
        "Z0": np.outer(zero, zero.conj()),
        "Z1": np.outer(one, one.conj()),
        "ket_|+>": plus,
        "ket_|0>": zero,
    }


def _lift_one_site(local: np.ndarray, target: int) -> np.ndarray:
    identity = np.eye(2, dtype=np.complex128)
    if target == 0:
        return np.kron(local, identity)
    if target == 1:
        return np.kron(identity, local)
    raise ValueError("dense neutral fixture target must be 0 or 1")


def _transformed_terms(
    fixture: Mapping[str, Any], term_transform: TermTransform | None
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for raw in fixture["collapse_terms"]:
        term = dict(raw)
        if term_transform is not None:
            term = term_transform(term)
            if term is None:
                continue
        transformed.append(term)
    return transformed


def _collapse_operators(
    fixture: Mapping[str, Any],
    *,
    term_transform: TermTransform | None = None,
    phases: Mapping[str, complex] | None = None,
) -> tuple[list[np.ndarray], list[dict[str, Any]]]:
    local = _local_operators()
    operators: list[np.ndarray] = []
    ledger: list[dict[str, Any]] = []
    phase_map = {} if phases is None else dict(phases)
    for term in _transformed_terms(fixture, term_transform):
        rate = float(term["generator_rate_per_ns"])
        if not math.isfinite(rate) or rate <= 0.0:
            raise ValueError("dense collapse generator rate must be finite and positive")
        phase = complex(phase_map.get(term["term_id"], 1.0 + 0.0j))
        if not math.isclose(abs(phase), 1.0, rel_tol=0.0, abs_tol=1.0e-15):
            raise ValueError("dense collapse phase must have unit modulus")
        matrix = phase * math.sqrt(rate) * _lift_one_site(
            local[term["family"]], int(term["target"])
        )
        operators.append(matrix)
        ledger.append(
            {
                "term_id": term["term_id"],
                "family": term["family"],
                "target": int(term["target"]),
                "generator_rate_per_ns": rate,
                "matrix_sha256": _array_sha256(matrix),
            }
        )
    return operators, ledger


def _liouvillian(collapse_operators: list[np.ndarray]) -> np.ndarray:
    dimension = 4
    identity = np.eye(dimension, dtype=np.complex128)
    generator = np.zeros((dimension * dimension, dimension * dimension), dtype=np.complex128)
    for collapse in collapse_operators:
        product = collapse.conj().T @ collapse
        generator += np.kron(collapse.conj(), collapse)
        generator -= 0.5 * np.kron(identity, product)
        generator -= 0.5 * np.kron(product.T, identity)
    return generator


def _evolve(rho: np.ndarray, propagator: np.ndarray) -> np.ndarray:
    vector = np.asarray(rho, dtype=np.complex128).reshape(-1, order="F")
    evolved = propagator @ vector
    return evolved.reshape((4, 4), order="F")


def _measurement_projector(basis: str, label: int, target: int) -> np.ndarray:
    local = _local_operators()
    key = f"{basis}{label}"
    if key not in local:
        raise ValueError("dense neutral measurement basis/label is unsupported")
    return _lift_one_site(local[key], target)


def _reset_map(rho: np.ndarray, target: int, reset_state: str) -> np.ndarray:
    local = _local_operators()
    reset_ket = local.get(f"ket_{reset_state}")
    if reset_ket is None:
        raise ValueError("dense neutral reset state is unsupported")
    output = np.zeros_like(rho, dtype=np.complex128)
    for source_label in (0, 1):
        basis_ket = np.eye(2, dtype=np.complex128)[:, source_label]
        reset_operator = np.outer(reset_ket, basis_ket.conj())
        lifted = _lift_one_site(reset_operator, target)
        output += lifted @ rho @ lifted.conj().T
    return output


def _record_distribution(
    fixture: Mapping[str, Any],
    *,
    term_transform: TermTransform | None = None,
    phases: Mapping[str, complex] | None = None,
) -> tuple[dict[tuple[int, int, int, int], float], dict[str, Any]]:
    collapse_operators, collapse_ledger = _collapse_operators(
        fixture,
        term_transform=term_transform,
        phases=phases,
    )
    generator = _liouvillian(collapse_operators)
    durations = [float(value) for value in fixture["evolution_segments_ns"]]
    propagators = [expm(duration * generator) for duration in durations]

    initial = np.zeros(4, dtype=np.complex128)
    initial[1] = 1.0
    rho = np.outer(initial, initial.conj())
    branches: list[tuple[tuple[int, ...], np.ndarray]] = [
        ((), _evolve(rho, propagators[0]))
    ]
    measurements = fixture["measurements"]
    maximum_hermiticity_residual = 0.0
    minimum_branch_mass = math.inf
    for measurement_index, measurement in enumerate(measurements):
        if measurement_index == 2:
            branches = [
                (record, _evolve(branch, propagators[1]))
                for record, branch in branches
            ]
        next_branches: list[tuple[tuple[int, ...], np.ndarray]] = []
        for record, branch in branches:
            for label in (0, 1):
                projector = _measurement_projector(
                    str(measurement["basis"]),
                    label,
                    int(measurement["target"]),
                )
                selected = projector @ branch @ projector
                if measurement["reset"]:
                    selected = _reset_map(
                        selected,
                        int(measurement["target"]),
                        str(measurement["reset_state"]),
                    )
                mass = float(np.trace(selected).real)
                minimum_branch_mass = min(minimum_branch_mass, mass)
                maximum_hermiticity_residual = max(
                    maximum_hermiticity_residual,
                    float(np.max(np.abs(selected - selected.conj().T))),
                )
                next_branches.append((record + (label,), selected))
        branches = next_branches

    if len(branches) != 16 or any(len(record) != 4 for record, _ in branches):
        raise RuntimeError("dense neutral Record branch shape drifted")
    raw = {
        tuple(record): float(np.trace(branch).real) for record, branch in branches
    }
    total = math.fsum(raw.values())
    if not math.isfinite(total) or total <= 0.0:
        raise RuntimeError("dense neutral Record mass must be finite and positive")
    normalized = {record: mass / total for record, mass in raw.items()}
    diagnostics = {
        "collapse_ledger": collapse_ledger,
        "collapse_operator_count": len(collapse_operators),
        "liouvillian_dimension": 16,
        "liouvillian_sha256": _array_sha256(generator),
        "propagator_sha256": [_array_sha256(value) for value in propagators],
        "raw_total_probability": total,
        "total_probability_residual": abs(total - 1.0),
        "minimum_branch_mass": minimum_branch_mass,
        "maximum_branch_hermiticity_residual": maximum_hermiticity_residual,
    }
    return normalized, diagnostics


def _histogram_payload(
    distribution: Mapping[tuple[int, ...], float]
) -> dict[str, Any]:
    records = sorted(distribution)
    return {
        "records": [list(record) for record in records],
        "probabilities": [float(distribution[record]) for record in records],
    }


def build_report(
    fixture_path: Path,
    *,
    require_project_isolation: bool = False,
) -> dict[str, Any]:
    resolved_fixture = Path(fixture_path).resolve()
    fixture = protocol.load_fixture(resolved_fixture)
    project_modules = sorted(
        name
        for name in sys.modules
        if name == "error_coupling_simulator"
        or name.startswith("error_coupling_simulator.")
    )
    project_spec = util.find_spec("error_coupling_simulator")
    if require_project_isolation and (project_modules or project_spec is not None):
        raise RuntimeError("independent dense worker can access project implementation")
    dense_law, diagnostics = _record_distribution(fixture)
    analytic_law = protocol.analytic_binary_distribution(fixture)
    tolerance = 1000.0 * float(fixture["numerical_zero"])
    maximum_cell_difference = max(
        abs(dense_law[record] - analytic_law[record]) for record in analytic_law
    )
    structural_zero_records = sorted(
        record for record, mass in analytic_law.items() if mass == 0.0
    )
    structural_zeros_preserved = all(
        dense_law[record] == 0.0 for record in structural_zero_records
    )
    sanity_passed = bool(
        diagnostics["total_probability_residual"] <= tolerance
        and diagnostics["minimum_branch_mass"] >= 0.0
        and diagnostics["maximum_branch_hermiticity_residual"] <= tolerance
        and maximum_cell_difference <= tolerance
        and structural_zeros_preserved
    )
    report: dict[str, Any] = {
        "schema": SCHEMA,
        "claim_boundary": fixture["claim_boundary"],
        "fixture": {
            "schema": fixture["schema"],
            "id": fixture["fixture_id"],
            "path": str(resolved_fixture),
            "sha256": protocol.fixture_sha256(resolved_fixture),
        },
        "runtime_provenance": {
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "numpy_version": np.__version__,
            "scipy_version": scipy.__version__,
            "worker_sha256": _sha256_file(Path(__file__).resolve()),
            "protocol_sha256": _sha256_file(Path(protocol.__file__).resolve()),
            "project_program_consumed": False,
            "project_implementation_imported": bool(project_modules),
            "project_modules_imported": project_modules,
            "project_package_find_spec": (
                None if project_spec is None else str(project_spec.origin)
            ),
            "project_isolation_required": require_project_isolation,
        },
        "construction": {
            "density_matrix_dimension": 4,
            "liouvillian_dimension": diagnostics["liouvillian_dimension"],
            "vectorization": "column_major",
            "dissipator": "kron(L.conj(),L)-0.5*kron(I,LdagL)-0.5*kron((LdagL).T,I)",
            "collapse_operator_count": diagnostics["collapse_operator_count"],
            "collapse_ledger": diagnostics["collapse_ledger"],
            "liouvillian_sha256": diagnostics["liouvillian_sha256"],
            "propagator_sha256": diagnostics["propagator_sha256"],
        },
        "record": {
            "measurement_keys": fixture["measurement_keys"],
            "measurement_targets": fixture["measurement_targets"],
            "measurement_bases": fixture["measurement_bases"],
            "reset_after": fixture["reset_after"],
            **_histogram_payload(dense_law),
        },
        "closed_form_crosscheck": {
            "maximum_cell_difference": maximum_cell_difference,
            "absolute_tolerance": tolerance,
            "structural_zero_records": [
                list(record) for record in structural_zero_records
            ],
            "structural_zeros_preserved": structural_zeros_preserved,
            "passed": bool(
                maximum_cell_difference <= tolerance
                and structural_zeros_preserved
            ),
        },
        "numerical_sanity": {
            "raw_total_probability": diagnostics["raw_total_probability"],
            "total_probability_residual": diagnostics[
                "total_probability_residual"
            ],
            "minimum_branch_mass": diagnostics["minimum_branch_mass"],
            "maximum_branch_hermiticity_residual": diagnostics[
                "maximum_branch_hermiticity_residual"
            ],
            "absolute_tolerance": tolerance,
            "passed": sanity_passed,
        },
        "all_checks_passed": sanity_passed,
    }
    report["content_hash"] = protocol.canonical_content_hash(report)
    return report


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    destination = Path(path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        _fsync_directory(destination.parent)
    except BaseException:
        temporary.unlink(missing_ok=True)
        destination.unlink(missing_ok=True)
        try:
            _fsync_directory(destination.parent)
        except OSError:
            pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    destination = args.output.resolve()
    destination.unlink(missing_ok=True)
    _fsync_directory(destination.parent)
    report = build_report(args.fixture, require_project_isolation=True)
    _atomic_write_json(destination, report)
    print(f"fixture={report['fixture']['id']}")
    print(f"all_checks_passed={report['all_checks_passed']}")
    print(f"content_hash={report['content_hash']}")
    return 0 if report["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
