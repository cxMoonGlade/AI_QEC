from __future__ import annotations

"""Grover workload adapter for the dense qutrit MCWF backend.

This module describes the Grover schedule. The reusable trajectory carrier lives
in :mod:`qec_twin.simulator.mcwf_backend`.
"""

from dataclasses import dataclass
import json
from pathlib import Path
import time
from typing import Any

import numpy as np
import torch

from ..mechanisms.qutrit_teachers import (
    G_HEAT_DEFAULT,
    G_SEEP_DEFAULT,
    THETA_DEFAULT,
    coherence_of_leakage,
    leakage_kraus_torch,
    wg_rates,
)
from .cudaq_grover import (
    bitstring_from_index,
    grover_theory_prediction,
    optimal_grover_iterations,
)
from .mcwf_backend import (
    CDTYPE,
    DenseQutritMcwfBackend,
    MAX_DENSE_MCWF_QUTRITS,
    QUTRIT_MCWF_CONVENTION,
    qutrit_index_from_digits,
)
from .mcwf_executor import (
    BlockTrajectoryMcwfExecutor,
    DenseQutritMcwfExecutor,
    GraphCapturedMcwfExecutor,
    NativeOpStreamMcwfExecutor,
)
from .mcwf_program import (
    CompiledMcwfProgram,
    all_ones_phase,
    h,
    kraus_all_sites,
    x,
)

LEAKAGE_SCHEDULE = "after_initial_h_and_after_each_grover_iteration_all_sites"
WG_LEAKAGE_KRAUS_KEY = "wg_leakage"


@dataclass(frozen=True)
class McwfGroverArtifacts:
    out_dir: Path
    measurement_counts: Path
    qutrit_outcome_counts: Path
    leakage_by_site: Path
    trajectory_summary: Path
    theory_prediction: Path
    manifest: Path


@dataclass(frozen=True)
class McwfGroverResult:
    num_qutrits: int
    marked_state: str
    marked_bit_index: int
    marked_qutrit_index: int
    iterations: int
    shots: int
    seed: int
    theta: float
    g_seep: float
    g_heat: float
    leaked_readout_b: float
    counts: dict[str, int]
    qutrit_counts: dict[str, int]
    leakage_by_site: list[dict[str, float]]
    trajectory_summary: dict[str, Any]
    theory_prediction: dict[str, Any]
    manifest: dict[str, Any]
    artifacts: McwfGroverArtifacts | None = None

    @property
    def marked_counts(self) -> int:
        return int(self.counts.get(self.marked_state, 0))

    @property
    def marked_fraction(self) -> float:
        return float(self.marked_counts / self.shots) if self.shots else 0.0

    @property
    def mean_pre_readout_marked_probability(self) -> float:
        return float(self.trajectory_summary["mean_pre_readout_marked_probability"])

    @property
    def mean_final_leaked_sites(self) -> float:
        return float(self.trajectory_summary["mean_final_leaked_sites"])

    def top_outcomes(self, k: int = 8) -> list[tuple[str, int]]:
        return sorted(self.counts.items(), key=lambda kv: kv[1], reverse=True)[: int(k)]

    def top_qutrit_outcomes(self, k: int = 8) -> list[tuple[str, int]]:
        return sorted(self.qutrit_counts.items(), key=lambda kv: kv[1], reverse=True)[: int(k)]


def simulate_mcwf_qutrit_grover_leakage(
    *,
    num_qubits: int = 12,
    marked_state: str | int | None = None,
    iterations: int | None = None,
    shots: int = 64,
    seed: int = 0,
    theta: float = THETA_DEFAULT,
    g_seep: float = G_SEEP_DEFAULT,
    g_heat: float = G_HEAT_DEFAULT,
    leaked_readout_b: float = 1.0,
    batch_size: int = 8,
    device: str | torch.device = "cuda",
    use_fused_kernels: bool = True,
    executor_mode: str = "graph_capture",
    out_dir: str | Path | None = None,
) -> McwfGroverResult:
    """Run qutrit Grover trajectories with MCWF leakage and final measurement.

    Grover's oracle/diffuser are algorithmic gates extended to qutrits by leaving
    ``|2>`` inert on one-site qubit gates and by not firing multi-controlled
    phases on leaked controls. The MCWF carrier itself is generic; this function
    only supplies the Grover workload, WG leakage channel, and artifact schema.
    """

    n = int(num_qubits)
    if not 2 <= n <= MAX_DENSE_MCWF_QUTRITS:
        raise ValueError(f"dense qutrit MCWF Grover supports 2 <= num_qubits <= {MAX_DENSE_MCWF_QUTRITS}")
    if int(shots) <= 0:
        raise ValueError("shots must be positive")
    if int(batch_size) <= 0:
        raise ValueError("batch_size must be positive")
    b = float(leaked_readout_b)
    if not 0.0 <= b <= 1.0:
        raise ValueError("leaked_readout_b must lie in [0, 1]")
    marked = _normalize_marked_state(marked_state, n)
    r = optimal_grover_iterations(n) if iterations is None else int(iterations)
    if r < 0:
        raise ValueError("iterations must be non-negative")

    backend = DenseQutritMcwfBackend(n, seed=int(seed), device=device, use_fused_kernels=bool(use_fused_kernels))
    mode = str(executor_mode)
    if mode == "graph_capture":
        executor = GraphCapturedMcwfExecutor(backend)
    elif mode == "block_traj":
        executor = BlockTrajectoryMcwfExecutor(backend)
    elif mode == "native_opstream":
        executor = NativeOpStreamMcwfExecutor(backend)
    elif mode == "dense":
        executor = DenseQutritMcwfExecutor(backend)
    else:
        raise ValueError("executor_mode must be 'graph_capture', 'block_traj', 'native_opstream', or 'dense'")
    kraus = torch.stack(leakage_kraus_torch(theta, g_seep, g_heat, device=backend.device)).to(CDTYPE)
    program = compile_mcwf_grover_program(num_qutrits=n, marked_state=marked, iterations=r)

    marked_qidx = qutrit_index_from_digits(tuple(int(ch) for ch in marked))
    marked_bit_index = int(marked[::-1], 2)

    bit_counts: dict[str, int] = {}
    qutrit_counts: dict[str, int] = {}
    pre_readout_marked_probs: list[float] = []
    final_leaked_counts: list[int] = []
    leaked_by_site_acc = np.zeros(n, dtype=np.float64)
    physics_program_s = 0.0
    probability_s = 0.0
    measurement_sampling_s = 0.0
    batches = 0

    remaining = int(shots)
    while remaining:
        B = min(int(batch_size), remaining)
        remaining -= B
        batches += 1
        exec_result = executor.run(program, batch_size=B, kraus_families={WG_LEAKAGE_KRAUS_KEY: kraus})
        physics_program_s += float(exec_result.timing.physics_program_s)

        t0 = time.perf_counter()
        psi = exec_result.psi
        probs = backend.probabilities(psi)
        if backend.device.type == "cuda":
            torch.cuda.synchronize(backend.device)
        probability_s += time.perf_counter() - t0
        t0 = time.perf_counter()
        pre_readout_marked_probs.extend(probs[:, marked_qidx].detach().cpu().numpy().astype(np.float64).tolist())
        measurement = backend.sample_measurements(probabilities=probs, leaked_readout_b=b)
        if backend.device.type == "cuda":
            torch.cuda.synchronize(backend.device)
        measurement_sampling_s += time.perf_counter() - t0
        final_leaked_counts.extend(measurement.final_leaked_counts.tolist())
        leaked_by_site_acc += measurement.leaked_by_site_counts
        _merge_counts(bit_counts, measurement.bit_counts)
        _merge_counts(qutrit_counts, measurement.qutrit_counts)

    wg_l1, wg_l2 = wg_rates(theta, g_seep, g_heat)
    leakage_by_site = [
        {"site": int(site), "p_leaked_at_final_measurement": float(leaked_by_site_acc[site] / int(shots))}
        for site in range(n)
    ]
    theory = grover_theory_prediction(num_qubits=n, iterations=r)
    summary = {
        "estimator": "mcwf_trajectories",
        "carrier": "dense_qutrit_statevector",
        "qutrit_dimension": int(backend.dim),
        "leakage_schedule": LEAKAGE_SCHEDULE,
        "mean_pre_readout_marked_probability": float(np.mean(pre_readout_marked_probs)),
        "std_pre_readout_marked_probability": float(np.std(pre_readout_marked_probs, ddof=1))
        if len(pre_readout_marked_probs) > 1
        else 0.0,
        "mean_final_leaked_sites": float(np.mean(final_leaked_counts)),
        "std_final_leaked_sites": float(np.std(final_leaked_counts, ddof=1)) if len(final_leaked_counts) > 1 else 0.0,
        "any_leakage_fraction": float(np.mean(np.asarray(final_leaked_counts) > 0)),
        "marked_fraction_after_leaked_readout": float(bit_counts.get(marked, 0) / int(shots)),
        "execution": {
            "executor": executor.name,
            "batches": int(batches),
            "physics_program_s": float(physics_program_s),
            "probability_s": float(probability_s),
            "measurement_sampling_s": float(measurement_sampling_s),
            "timing_method": "cuda_event_for_physics_program_and_perf_counter_for_host_bound_steps",
        },
    }
    executor_manifest = executor.manifest()
    manifest = {
        "schema": "qec_twin.simulator_mcwf_qutrit_grover_leakage.v1",
        "backend": "qec_twin.simulator.mcwf_backend.DenseQutritMcwfBackend",
        "workload_adapter": "qec_twin.simulator.mcwf_grover",
        "representability": "dense_qutrit_statevector_mcwf_leakage",
        "kernel_backend": executor_manifest["kernel_backend"],
        "executor": executor_manifest,
        "program": program.summary(),
        "algorithm": "single_solution_grover_gate_level",
        "grover_realization": {
            "oracle": "x_mask_to_all_ones_then_multi_controlled_phase_then_unmask",
            "diffuser": "H_all_X_all_multi_controlled_phase_X_all_H_all",
            "multi_control_condition": "qutrit_controls_fire_only_on_level_1_not_level_2",
        },
        "qutrit_string_convention": QUTRIT_MCWF_CONVENTION,
        "num_qutrits": n,
        "marked_state": marked,
        "marked_bit_index": marked_bit_index,
        "marked_qutrit_index": marked_qidx,
        "iterations": r,
        "shots": int(shots),
        "seed": int(seed),
        "batch_size": int(batch_size),
        "parameters": {
            "theta": float(theta),
            "g_seep": float(g_seep),
            "g_heat": float(g_heat),
            "WG_L1": float(wg_l1),
            "WG_L2": float(wg_l2),
            "C_L": float(coherence_of_leakage(theta, g_seep, g_heat)),
            "kraus_rank": int(kraus.shape[0]),
            "leaked_readout_b": b,
        },
        "noise": {
            "type": "qutrit_leakage_mcwf",
            "source": "qec_twin.mechanisms.qutrit_teachers.leakage_kraus_torch",
            "schedule": LEAKAGE_SCHEDULE,
        },
        "decoder": None,
        "artifacts": {},
    }
    result = McwfGroverResult(
        num_qutrits=n,
        marked_state=marked,
        marked_bit_index=marked_bit_index,
        marked_qutrit_index=marked_qidx,
        iterations=r,
        shots=int(shots),
        seed=int(seed),
        theta=float(theta),
        g_seep=float(g_seep),
        g_heat=float(g_heat),
        leaked_readout_b=b,
        counts=bit_counts,
        qutrit_counts=qutrit_counts,
        leakage_by_site=leakage_by_site,
        trajectory_summary=summary,
        theory_prediction=theory,
        manifest=manifest,
    )
    if out_dir is None:
        return result

    artifacts = write_mcwf_grover_artifacts(result, out_dir)
    manifest = dict(manifest)
    manifest["artifacts"] = {
        "measurement_counts": artifacts.measurement_counts.name,
        "qutrit_outcome_counts": artifacts.qutrit_outcome_counts.name,
        "leakage_by_site": artifacts.leakage_by_site.name,
        "trajectory_summary": artifacts.trajectory_summary.name,
        "theory_prediction": artifacts.theory_prediction.name,
    }
    _write_json(artifacts.manifest, manifest)
    return McwfGroverResult(
        num_qutrits=n,
        marked_state=marked,
        marked_bit_index=marked_bit_index,
        marked_qutrit_index=marked_qidx,
        iterations=r,
        shots=int(shots),
        seed=int(seed),
        theta=float(theta),
        g_seep=float(g_seep),
        g_heat=float(g_heat),
        leaked_readout_b=b,
        counts=bit_counts,
        qutrit_counts=qutrit_counts,
        leakage_by_site=leakage_by_site,
        trajectory_summary=summary,
        theory_prediction=theory,
        manifest=manifest,
        artifacts=artifacts,
    )


def compile_mcwf_grover_program(
    *,
    num_qutrits: int,
    marked_state: str,
    iterations: int,
) -> CompiledMcwfProgram:
    """Compile the Grover workload to the generic MCWF operation stream."""

    n = int(num_qutrits)
    marked = _normalize_marked_state(marked_state, n)
    r = int(iterations)
    if r < 0:
        raise ValueError("iterations must be non-negative")
    ops = []
    for site in range(n):
        ops.append(h(site))
    ops.append(kraus_all_sites(WG_LEAKAGE_KRAUS_KEY, range(n)))
    for _ in range(r):
        ops.extend(_marked_oracle_ops(n, marked))
        ops.extend(_diffuser_ops(n))
        ops.append(kraus_all_sites(WG_LEAKAGE_KRAUS_KEY, range(n)))
    return CompiledMcwfProgram(
        num_qutrits=n,
        operations=tuple(ops),
        description="single_solution_grover_gate_level_with_qutrit_wg_leakage_slots",
    )


def write_mcwf_grover_artifacts(result: McwfGroverResult, out_dir: str | Path) -> McwfGroverArtifacts:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    counts_path = out / "measurement_counts.json"
    qutrit_counts_path = out / "qutrit_outcome_counts.json"
    leakage_path = out / "leakage_by_site.json"
    summary_path = out / "trajectory_summary.json"
    theory_path = out / "theory_prediction.json"
    manifest_path = out / "manifest.json"
    _write_json(counts_path, result.counts)
    _write_json(qutrit_counts_path, result.qutrit_counts)
    _write_json(leakage_path, result.leakage_by_site)
    _write_json(summary_path, result.trajectory_summary)
    _write_json(theory_path, result.theory_prediction)
    _write_json(manifest_path, result.manifest)
    return McwfGroverArtifacts(
        out_dir=out,
        measurement_counts=counts_path,
        qutrit_outcome_counts=qutrit_counts_path,
        leakage_by_site=leakage_path,
        trajectory_summary=summary_path,
        theory_prediction=theory_path,
        manifest=manifest_path,
    )


def _normalize_marked_state(marked_state: str | int | None, n: int) -> str:
    if marked_state is None:
        return "1" * int(n)
    if isinstance(marked_state, int):
        if not 0 <= int(marked_state) < (1 << int(n)):
            raise ValueError(f"marked_state integer outside [0, 2**{int(n)})")
        return bitstring_from_index(int(marked_state), int(n))
    marked = str(marked_state).strip()
    if len(marked) != int(n) or any(ch not in "01" for ch in marked):
        raise ValueError(f"marked_state must be a {int(n)}-bit 0/1 string")
    return marked


def _apply_marked_oracle(
    psi: torch.Tensor,
    *,
    backend: DenseQutritMcwfBackend,
    marked: str,
) -> torch.Tensor:
    cur = psi
    for site, bit in enumerate(marked):
        if bit == "0":
            cur = backend.apply_x(cur, site)
    cur = backend.apply_computational_all_ones_phase(cur, phase=-1.0)
    for site, bit in reversed(tuple(enumerate(marked))):
        if bit == "0":
            cur = backend.apply_x(cur, site)
    return cur


def _marked_oracle_ops(n: int, marked: str):
    for site, bit in enumerate(marked):
        if bit == "0":
            yield x(site)
    yield all_ones_phase(range(int(n)), phase=-1.0)
    for site, bit in reversed(tuple(enumerate(marked))):
        if bit == "0":
            yield x(site)


def _apply_diffuser(
    psi: torch.Tensor,
    *,
    backend: DenseQutritMcwfBackend,
) -> torch.Tensor:
    cur = psi
    for site in range(backend.num_qutrits):
        cur = backend.apply_h(cur, site)
    for site in range(backend.num_qutrits):
        cur = backend.apply_x(cur, site)
    cur = backend.apply_computational_all_ones_phase(cur, phase=-1.0)
    for site in range(backend.num_qutrits):
        cur = backend.apply_x(cur, site)
    for site in range(backend.num_qutrits):
        cur = backend.apply_h(cur, site)
    return cur


def _diffuser_ops(n: int):
    for site in range(int(n)):
        yield h(site)
    for site in range(int(n)):
        yield x(site)
    yield all_ones_phase(range(int(n)), phase=-1.0)
    for site in range(int(n)):
        yield x(site)
    for site in range(int(n)):
        yield h(site)


def _merge_counts(dst: dict[str, int], src: dict[str, int]) -> None:
    for key, value in src.items():
        dst[key] = dst.get(key, 0) + int(value)


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
