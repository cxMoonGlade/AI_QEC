from __future__ import annotations

"""CUDA-Q noiseless Grover frontend.

This adapter is for algorithmic, non-Clifford circuits such as Grover search.
It deliberately does not produce Stim/DEM artifacts.
"""

from dataclasses import dataclass
import json
import math
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np


BITSTRING_CONVENTION = "cudaq_allocation_order_left_to_right_q0_to_qNminus1"


@dataclass(frozen=True)
class CudaQGroverArtifacts:
    out_dir: Path
    statevector: Path
    probabilities: Path
    measurement_counts: Path
    theory_prediction: Path
    manifest: Path


@dataclass(frozen=True)
class CudaQGroverResult:
    num_qubits: int
    marked_state: str
    marked_index: int
    iterations: int
    shots: int
    seed: int
    statevector: np.ndarray
    probabilities: np.ndarray
    counts: dict[str, int]
    theory_prediction: dict[str, Any]
    manifest: dict[str, Any]
    timings: dict[str, float]
    artifacts: CudaQGroverArtifacts | None = None

    @property
    def marked_probability(self) -> float:
        return float(self.probabilities[self.marked_index])

    @property
    def marked_counts(self) -> int:
        return int(self.counts.get(self.marked_state, 0))

    def top_outcomes(self, k: int = 8) -> list[tuple[str, float, int]]:
        indices = np.argsort(self.probabilities)[::-1][:int(k)]
        return [
            (
                bitstring_from_index(int(index), self.num_qubits),
                float(self.probabilities[int(index)]),
                int(self.counts.get(bitstring_from_index(int(index), self.num_qubits), 0)),
            )
            for index in indices
        ]


def simulate_cudaq_grover_noiseless(
    *,
    num_qubits: int = 12,
    marked_state: str | int | None = None,
    iterations: int | None = None,
    shots: int = 1024,
    seed: int = 0,
    out_dir: str | Path | None = None,
) -> CudaQGroverResult:
    """Run a single-solution Grover circuit with CUDA-Q's noiseless statevector target."""

    cudaq = _cudaq()
    n = int(num_qubits)
    if n < 2:
        raise ValueError("Grover backend requires at least 2 qubits")
    if int(shots) < 0:
        raise ValueError("shots must be non-negative")
    marked = normalize_marked_state(marked_state, n)
    marked_index = index_from_bitstring(marked)
    r = optimal_grover_iterations(n) if iterations is None else int(iterations)
    if r < 0:
        raise ValueError("iterations must be non-negative")

    t0 = perf_counter()
    state_kernel = build_cudaq_grover_kernel(
        num_qubits=n,
        marked_state=marked,
        iterations=r,
        measure=False,
    )
    t1 = perf_counter()
    sample_kernel = build_cudaq_grover_kernel(
        num_qubits=n,
        marked_state=marked,
        iterations=r,
        measure=True,
    )
    t2 = perf_counter()

    state = np.asarray(cudaq.get_state(state_kernel))
    t3 = perf_counter()
    probabilities = np.abs(state) ** 2
    probabilities = probabilities / probabilities.sum()
    t4 = perf_counter()

    cudaq.set_random_seed(int(seed))
    raw_counts = cudaq.sample(sample_kernel, shots_count=int(shots)) if int(shots) else {}
    t5 = perf_counter()
    counts = {str(key): int(value) for key, value in dict(raw_counts.items()).items()}
    theory = grover_theory_prediction(num_qubits=n, iterations=r)
    timings = {
        "build_state_kernel_s": float(t1 - t0),
        "build_sample_kernel_s": float(t2 - t1),
        "get_state_s": float(t3 - t2),
        "probabilities_numpy_s": float(t4 - t3),
        "sample_s": float(t5 - t4),
        "pre_artifact_total_s": float(t5 - t0),
    }
    manifest = _manifest(
        cudaq=cudaq,
        num_qubits=n,
        marked_state=marked,
        marked_index=marked_index,
        iterations=r,
        shots=int(shots),
        seed=int(seed),
        counts=counts,
        marked_probability=float(probabilities[marked_index]),
        theory=theory,
        timings=timings,
    )

    result = CudaQGroverResult(
        num_qubits=n,
        marked_state=marked,
        marked_index=marked_index,
        iterations=r,
        shots=int(shots),
        seed=int(seed),
        statevector=state,
        probabilities=probabilities,
        counts=counts,
        theory_prediction=theory,
        manifest=manifest,
        timings=timings,
    )
    if out_dir is not None:
        t_art0 = perf_counter()
        artifacts = write_cudaq_grover_artifacts(result, out_dir)
        t_art1 = perf_counter()
        timings = dict(timings)
        timings["artifact_write_s"] = float(t_art1 - t_art0)
        timings["total_s"] = float(t_art1 - t0)
        manifest = dict(result.manifest)
        manifest["timings"] = timings
        manifest["artifacts"] = {
            "statevector": artifacts.statevector.name,
            "probabilities": artifacts.probabilities.name,
            "measurement_counts": artifacts.measurement_counts.name,
            "theory_prediction": artifacts.theory_prediction.name,
        }
        _write_json(artifacts.manifest, manifest)
        result = CudaQGroverResult(
            num_qubits=n,
            marked_state=marked,
            marked_index=marked_index,
            iterations=r,
            shots=int(shots),
            seed=int(seed),
            statevector=state,
            probabilities=probabilities,
            counts=counts,
            theory_prediction=theory,
            manifest=manifest,
            timings=timings,
            artifacts=artifacts,
        )
    return result


def build_cudaq_grover_kernel(
    *,
    num_qubits: int,
    marked_state: str | int,
    iterations: int,
    measure: bool,
):
    """Build the CUDA-Q Grover kernel.

    The user-facing bitstring convention is CUDA-Q allocation order:
    left-to-right `q0 q1 ... qN-1`. The last qubit is the target of the
    multi-controlled phase; the preceding qubits are allocated as its control
    register.
    """

    cudaq = _cudaq()
    n = int(num_qubits)
    marked = normalize_marked_state(marked_state, n)

    z_kernel, target_arg = cudaq.make_kernel(cudaq.qubit)
    z_kernel.z(target_arg)

    kernel = cudaq.make_kernel()
    controls = kernel.qalloc(n - 1)
    target = kernel.qalloc()

    _apply_all(kernel, controls, target, n, "h")
    for _ in range(int(iterations)):
        _marked_phase(kernel, z_kernel, controls, target, marked)
        _diffuser(kernel, z_kernel, controls, target, n)
    if measure:
        kernel.mz(controls)
        kernel.mz(target)
    return kernel


def normalize_marked_state(marked_state: str | int | None, num_qubits: int) -> str:
    n = int(num_qubits)
    if marked_state is None:
        return "1" * n
    if isinstance(marked_state, int):
        if not 0 <= marked_state < (1 << n):
            raise ValueError(f"marked_state integer outside [0, 2**{n})")
        return bitstring_from_index(marked_state, n)
    marked = str(marked_state).strip()
    if len(marked) != n or any(ch not in "01" for ch in marked):
        raise ValueError(f"marked_state must be a {n}-bit 0/1 string")
    return marked


def index_from_bitstring(bitstring: str) -> int:
    """Return statevector index for `q0 q1 ...` bitstring convention."""

    out = 0
    for q, bit in enumerate(str(bitstring)):
        if bit == "1":
            out |= 1 << q
    return out


def bitstring_from_index(index: int, num_qubits: int) -> str:
    return "".join(str((int(index) >> q) & 1) for q in range(int(num_qubits)))


def optimal_grover_iterations(num_qubits: int) -> int:
    theta = math.asin(1.0 / math.sqrt(1 << int(num_qubits)))
    return max(0, int(round(math.pi / (4.0 * theta) - 0.5)))


def grover_theory_prediction(*, num_qubits: int, iterations: int) -> dict[str, Any]:
    theta = math.asin(1.0 / math.sqrt(1 << int(num_qubits)))
    success = math.sin((2 * int(iterations) + 1) * theta) ** 2
    return {
        "available": True,
        "method": "single_solution_grover_closed_form",
        "theta": theta,
        "success_probability": success,
    }


def write_cudaq_grover_artifacts(
    result: CudaQGroverResult,
    out_dir: str | Path,
) -> CudaQGroverArtifacts:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    artifacts = CudaQGroverArtifacts(
        out_dir=root,
        statevector=root / "statevector.npy",
        probabilities=root / "probabilities.npy",
        measurement_counts=root / "measurement_counts.json",
        theory_prediction=root / "theory_prediction.json",
        manifest=root / "manifest.json",
    )
    np.save(artifacts.statevector, result.statevector)
    np.save(artifacts.probabilities, result.probabilities)
    _write_json(
        artifacts.measurement_counts,
        {
            "shots": result.shots,
            "seed": result.seed,
            "marked_state": result.marked_state,
            "marked_counts": result.marked_counts,
            "counts": result.counts,
            "top_outcomes": result.top_outcomes(16),
        },
    )
    _write_json(artifacts.theory_prediction, result.theory_prediction)
    _write_json(artifacts.manifest, result.manifest)
    return artifacts


def _apply_all(kernel, controls, target, num_qubits: int, gate: str) -> None:
    for qubit in range(int(num_qubits) - 1):
        getattr(kernel, gate)(controls[qubit])
    getattr(kernel, gate)(target)


def _marked_phase(kernel, z_kernel, controls, target, marked: str) -> None:
    n = len(marked)
    for qubit, bit in enumerate(marked[:-1]):
        if bit == "0":
            kernel.x(controls[qubit])
    if marked[-1] == "0":
        kernel.x(target)
    kernel.control(z_kernel, controls, target)
    if marked[-1] == "0":
        kernel.x(target)
    for qubit, bit in reversed(tuple(enumerate(marked[:-1]))):
        if bit == "0":
            kernel.x(controls[qubit])


def _diffuser(kernel, z_kernel, controls, target, num_qubits: int) -> None:
    _apply_all(kernel, controls, target, num_qubits, "h")
    _apply_all(kernel, controls, target, num_qubits, "x")
    kernel.control(z_kernel, controls, target)
    _apply_all(kernel, controls, target, num_qubits, "x")
    _apply_all(kernel, controls, target, num_qubits, "h")


def _manifest(
    *,
    cudaq,
    num_qubits: int,
    marked_state: str,
    marked_index: int,
    iterations: int,
    shots: int,
    seed: int,
    counts: dict[str, int],
    marked_probability: float,
    theory: dict[str, Any],
    timings: dict[str, float],
) -> dict[str, Any]:
    marked_counts = int(counts.get(marked_state, 0))
    return {
        "schema": "qec_twin.simulator_cudaq_grover_noiseless.v1",
        "backend": "cudaq",
        "cudaq_target": str(cudaq.get_target()),
        "representability": "cudaq_statevector_noiseless",
        "algorithm": "single_solution_grover",
        "bitstring_convention": BITSTRING_CONVENTION,
        "num_qubits": int(num_qubits),
        "marked_state": marked_state,
        "marked_index": int(marked_index),
        "iterations": int(iterations),
        "shots": int(shots),
        "seed": int(seed),
        "noise": None,
        "statevector_marked_probability": float(marked_probability),
        "sample_marked_counts": marked_counts,
        "sample_marked_rate": (marked_counts / shots) if shots else None,
        "theory_prediction": theory,
        "timings": timings,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(_jsonable(payload), indent=2, sort_keys=True) + "\n")


def _jsonable(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def _cudaq():
    try:
        import cudaq
    except ModuleNotFoundError as exc:  # pragma: no cover - env-dependent
        raise RuntimeError(
            "CUDA-Q is required for simulate_cudaq_grover_noiseless; "
            "run inside the aiqec environment with cudaq installed"
        ) from exc
    return cudaq
