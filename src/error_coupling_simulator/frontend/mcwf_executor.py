from __future__ import annotations

"""Executors for compiled qutrit MCWF programs."""

from dataclasses import dataclass
import json
from typing import Any

import torch

from .mcwf_backend import RDTYPE
from .mcwf_backend import DenseQutritMcwfBackend
from .mcwf_program import (
    CompiledMcwfProgram,
    McwfAllOnesPhaseOp,
    McwfCachedQubitGateOp,
    McwfKrausAllSitesOp,
    McwfQubitGateOp,
)

_OP_H = 1
_OP_X = 2
_OP_ALL_ONES_PHASE = 3
_OP_KRAUS_ALL_SITES = 4
_OP_X_LAYER = 5


@dataclass(frozen=True)
class McwfExecutionTiming:
    """Per-program execution timing for one batch."""

    physics_program_s: float
    timing_method: str

    def as_dict(self) -> dict[str, float | str]:
        return {
            "physics_program_s": float(self.physics_program_s),
            "timing_method": self.timing_method,
        }


@dataclass(frozen=True)
class McwfExecutionResult:
    """Final state and timing for one compiled-program execution."""

    psi: torch.Tensor
    timing: McwfExecutionTiming


class DenseQutritMcwfExecutor:
    """Execute :class:`CompiledMcwfProgram` on ``DenseQutritMcwfBackend``.

    This adapter is intentionally thin. It is the stable call surface that future
    native trajectory kernels / CUDA graph replay should implement without
    changing workload adapters or artifact schemas.
    """

    name = "error_coupling_simulator.frontend.mcwf_executor.DenseQutritMcwfExecutor"
    schema = "error_coupling_simulator.frontend.dense_qutrit_mcwf_executor.v1"

    def __init__(self, backend: DenseQutritMcwfBackend) -> None:
        self.backend = backend

    def run(
        self,
        program: CompiledMcwfProgram,
        *,
        batch_size: int,
        kraus_families: dict[str, torch.Tensor],
        measure_timing: bool = True,
    ) -> McwfExecutionResult:
        """Run one batch of a compiled MCWF program."""

        if int(program.num_qutrits) != int(self.backend.num_qutrits):
            raise ValueError(
                f"program num_qutrits={program.num_qutrits} does not match backend {self.backend.num_qutrits}"
            )
        if not measure_timing:
            psi = program.run(self.backend, batch_size=int(batch_size), kraus_families=kraus_families)
            return McwfExecutionResult(
                psi=psi,
                timing=McwfExecutionTiming(physics_program_s=0.0, timing_method="disabled"),
            )
        if self.backend.device.type != "cuda":
            raise RuntimeError("DenseQutritMcwfExecutor is GPU-only; backend device must be CUDA")
        start = torch.cuda.Event(enable_timing=True)
        end = torch.cuda.Event(enable_timing=True)
        start.record()
        psi = program.run(self.backend, batch_size=int(batch_size), kraus_families=kraus_families)
        end.record()
        end.synchronize()
        elapsed_s = float(start.elapsed_time(end) / 1000.0)
        return McwfExecutionResult(
            psi=psi,
            timing=McwfExecutionTiming(physics_program_s=elapsed_s, timing_method="cuda_event"),
        )

    def manifest(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "name": self.name,
            "backend": (
                "error_coupling_simulator.frontend.mcwf_backend."
                "DenseQutritMcwfBackend"
            ),
            "kernel_backend": "fused_cuda_if_available" if self.backend.use_fused_kernels else "torch_cuda_reference",
        }


class NativeOpStreamMcwfExecutor:
    """Execute cached-subset MCWF programs through the native CUDA op-stream runner."""

    name = (
        "error_coupling_simulator.frontend.mcwf_executor."
        "NativeOpStreamMcwfExecutor"
    )
    schema = "error_coupling_simulator.frontend.native_op_stream_mcwf_executor.v1"
    supported_ops = (
        "McwfCachedQubitGateOp[h,x]",
        "McwfAllOnesPhaseOp[phase=-1]",
        "McwfKrausAllSitesOp[single_key]",
        "lowering: adjacent unique-site X ops -> exact X-layer permutation",
    )

    def __init__(self, backend: DenseQutritMcwfBackend) -> None:
        self.backend = backend

    def run(
        self,
        program: CompiledMcwfProgram,
        *,
        batch_size: int,
        kraus_families: dict[str, torch.Tensor],
        measure_timing: bool = True,
    ) -> McwfExecutionResult:
        if int(program.num_qutrits) != int(self.backend.num_qutrits):
            raise ValueError(
                f"program num_qutrits={program.num_qutrits} does not match backend {self.backend.num_qutrits}"
            )
        if self.backend.device.type != "cuda":
            raise RuntimeError("NativeOpStreamMcwfExecutor is GPU-only; backend device must be CUDA")
        from ..carrier.kernels import qutrit_mcwf_ops_loader as _ops

        lowered = _lower_cached_opstream(program, self.backend, int(batch_size), kraus_families)
        psi0 = self.backend.basis_state(int(batch_size), program.initial_levels)
        if not measure_timing:
            psi = _ops.run_cached_opstream(psi0, *lowered, int(program.num_qutrits))
            return McwfExecutionResult(
                psi=psi,
                timing=McwfExecutionTiming(physics_program_s=0.0, timing_method="disabled"),
            )
        start = torch.cuda.Event(enable_timing=True)
        end = torch.cuda.Event(enable_timing=True)
        start.record()
        psi = _ops.run_cached_opstream(psi0, *lowered, int(program.num_qutrits))
        end.record()
        end.synchronize()
        return McwfExecutionResult(
            psi=psi,
            timing=McwfExecutionTiming(
                physics_program_s=float(start.elapsed_time(end) / 1000.0),
                timing_method="cuda_event",
            ),
        )

    def manifest(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "name": self.name,
            "backend": (
                "error_coupling_simulator.carrier.kernels.qutrit_mcwf_ops_loader."
                "run_cached_opstream"
            ),
            "kernel_backend": "native_cached_opstream_cuda",
            "supported_ops": list(self.supported_ops),
        }


class BlockTrajectoryMcwfExecutor:
    """Execute cached-subset programs in one CUDA block per trajectory.

    This executor is a device-side op-stream slice: each CUDA block owns one
    trajectory statevector and runs the whole cached program with block-local
    synchronization between operations. It preserves the same finite-Kraus MCWF
    semantics as ``NativeOpStreamMcwfExecutor`` but trades broad per-op grid
    parallelism for fewer host kernel launches.
    """

    name = (
        "error_coupling_simulator.frontend.mcwf_executor."
        "BlockTrajectoryMcwfExecutor"
    )
    schema = "error_coupling_simulator.frontend.block_trajectory_mcwf_executor.v1"
    supported_ops = NativeOpStreamMcwfExecutor.supported_ops

    def __init__(self, backend: DenseQutritMcwfBackend) -> None:
        self.backend = backend

    def run(
        self,
        program: CompiledMcwfProgram,
        *,
        batch_size: int,
        kraus_families: dict[str, torch.Tensor],
        measure_timing: bool = True,
    ) -> McwfExecutionResult:
        if int(program.num_qutrits) != int(self.backend.num_qutrits):
            raise ValueError(
                f"program num_qutrits={program.num_qutrits} does not match backend {self.backend.num_qutrits}"
            )
        if self.backend.device.type != "cuda":
            raise RuntimeError("BlockTrajectoryMcwfExecutor is GPU-only; backend device must be CUDA")
        from ..carrier.kernels import qutrit_mcwf_ops_loader as _ops

        lowered = _lower_cached_opstream(program, self.backend, int(batch_size), kraus_families)
        psi0 = self.backend.basis_state(int(batch_size), program.initial_levels)
        if not measure_timing:
            psi = _ops.run_block_traj_opstream(psi0, *lowered, int(program.num_qutrits))
            return McwfExecutionResult(
                psi=psi,
                timing=McwfExecutionTiming(physics_program_s=0.0, timing_method="disabled"),
            )
        start = torch.cuda.Event(enable_timing=True)
        end = torch.cuda.Event(enable_timing=True)
        start.record()
        psi = _ops.run_block_traj_opstream(psi0, *lowered, int(program.num_qutrits))
        end.record()
        end.synchronize()
        return McwfExecutionResult(
            psi=psi,
            timing=McwfExecutionTiming(
                physics_program_s=float(start.elapsed_time(end) / 1000.0),
                timing_method="cuda_event",
            ),
        )

    def manifest(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "name": self.name,
            "backend": (
                "error_coupling_simulator.carrier.kernels.qutrit_mcwf_ops_loader."
                "run_block_traj_opstream"
            ),
            "kernel_backend": "block_trajectory_opstream_cuda",
            "supported_ops": list(self.supported_ops),
            "mapping": "one_cuda_block_per_trajectory",
        }


@dataclass
class _CapturedMcwfGraph:
    graph: torch.cuda.CUDAGraph
    static_psi: torch.Tensor
    static_kraus: torch.Tensor
    static_rand: torch.Tensor
    static_out: torch.Tensor
    rand_rows: int
    kraus_key: str | None


class GraphCapturedMcwfExecutor:
    """CUDA-graph replay wrapper around the native cached op-stream runner."""

    name = (
        "error_coupling_simulator.frontend.mcwf_executor."
        "GraphCapturedMcwfExecutor"
    )
    schema = "error_coupling_simulator.frontend.graph_captured_mcwf_executor.v1"

    def __init__(self, backend: DenseQutritMcwfBackend) -> None:
        self.backend = backend
        self._graphs: dict[str, _CapturedMcwfGraph] = {}

    def run(
        self,
        program: CompiledMcwfProgram,
        *,
        batch_size: int,
        kraus_families: dict[str, torch.Tensor],
        measure_timing: bool = True,
    ) -> McwfExecutionResult:
        if int(program.num_qutrits) != int(self.backend.num_qutrits):
            raise ValueError(
                f"program num_qutrits={program.num_qutrits} does not match backend {self.backend.num_qutrits}"
            )
        if self.backend.device.type != "cuda":
            raise RuntimeError("GraphCapturedMcwfExecutor is GPU-only; backend device must be CUDA")
        key = _graph_cache_key(program, int(batch_size), kraus_families)
        captured = self._graphs.get(key)
        first_capture = captured is None
        if captured is None:
            captured = self._capture(program, int(batch_size), kraus_families)
            self._graphs[key] = captured
        else:
            if captured.kraus_key is not None:
                current_kraus = _kraus_family_tensor(
                    captured.kraus_key,
                    self.backend,
                    kraus_families,
                )
                if tuple(current_kraus.shape) != tuple(captured.static_kraus.shape):
                    raise ValueError(
                        "captured graph Kraus shape changed from "
                        f"{tuple(captured.static_kraus.shape)} to {tuple(current_kraus.shape)}"
                    )
                captured.static_kraus.copy_(current_kraus)
            if captured.rand_rows:
                captured.static_rand.copy_(_draw_rand(self.backend, int(batch_size), captured.rand_rows))
        if not measure_timing:
            captured.graph.replay()
            return McwfExecutionResult(
                psi=captured.static_out,
                timing=McwfExecutionTiming(physics_program_s=0.0, timing_method="disabled"),
            )
        start = torch.cuda.Event(enable_timing=True)
        end = torch.cuda.Event(enable_timing=True)
        start.record()
        captured.graph.replay()
        end.record()
        end.synchronize()
        method = "cuda_graph_replay_after_capture" if first_capture else "cuda_graph_replay"
        return McwfExecutionResult(
            psi=captured.static_out,
            timing=McwfExecutionTiming(
                physics_program_s=float(start.elapsed_time(end) / 1000.0),
                timing_method=method,
            ),
        )

    def _capture(
        self,
        program: CompiledMcwfProgram,
        batch_size: int,
        kraus_families: dict[str, torch.Tensor],
    ) -> _CapturedMcwfGraph:
        from ..carrier.kernels import qutrit_mcwf_ops_loader as _ops

        op_kind, op_site_ptr, op_sites, kraus_t, rand_rows = _lower_cached_opstream_structure(
            program,
            self.backend,
            kraus_families,
            metadata_device=torch.device("cpu"),
        )
        kraus_key = _unique_kraus_key(program)
        static_psi = self.backend.basis_state(batch_size, program.initial_levels)
        static_rand = _draw_rand(self.backend, batch_size, rand_rows)

        # Warm up the exact call shape before capture so JIT/load and allocator
        # setup happen outside the graph. The zero-rand output is discarded.
        warm_rand = torch.zeros_like(static_rand)
        _ = _ops.run_cached_opstream(
            static_psi,
            op_kind,
            op_site_ptr,
            op_sites,
            kraus_t,
            warm_rand,
            int(program.num_qutrits),
        )
        torch.cuda.synchronize(self.backend.device)

        graph = torch.cuda.CUDAGraph()
        with torch.cuda.graph(graph):
            static_out = _ops.run_cached_opstream(
                static_psi,
                op_kind,
                op_site_ptr,
                op_sites,
                kraus_t,
                static_rand,
                int(program.num_qutrits),
            )
        return _CapturedMcwfGraph(
            graph=graph,
            static_psi=static_psi,
            static_kraus=kraus_t,
            static_rand=static_rand,
            static_out=static_out,
            rand_rows=rand_rows,
            kraus_key=kraus_key,
        )

    def manifest(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "name": self.name,
            "backend": (
                "error_coupling_simulator.carrier.kernels.qutrit_mcwf_ops_loader."
                "run_cached_opstream"
            ),
            "kernel_backend": "cuda_graph_cached_opstream",
            "capture": "fixed_program_fixed_batch_fixed_kraus_shape_static_buffers",
        }


def _lower_cached_opstream(
    program: CompiledMcwfProgram,
    backend: DenseQutritMcwfBackend,
    batch_size: int,
    kraus_families: dict[str, torch.Tensor],
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    op_kind_t, op_site_ptr_t, op_sites_t, kraus_t, rand_rows = _lower_cached_opstream_structure(
        program,
        backend,
        kraus_families,
        metadata_device=backend.device,
    )
    rand = _draw_rand(backend, batch_size, rand_rows)
    return (op_kind_t, op_site_ptr_t, op_sites_t, kraus_t, rand)


def _lower_cached_opstream_structure(
    program: CompiledMcwfProgram,
    backend: DenseQutritMcwfBackend,
    kraus_families: dict[str, torch.Tensor],
    *,
    metadata_device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, int]:
    op_kind: list[int] = []
    op_site_ptr: list[int] = [0]
    op_sites: list[int] = []
    kraus_keys: list[str] = []
    rand_rows = 0
    ops = tuple(program.operations)
    oi = 0
    while oi < len(ops):
        op = ops[oi]
        if isinstance(op, McwfCachedQubitGateOp):
            if op.name == "x":
                layer_sites: list[int] = []
                seen: set[int] = set()
                while oi < len(ops):
                    layer_op = ops[oi]
                    if not isinstance(layer_op, McwfCachedQubitGateOp) or layer_op.name != "x":
                        break
                    site = int(layer_op.site)
                    if site in seen:
                        break
                    seen.add(site)
                    layer_sites.append(site)
                    oi += 1
                op_kind.append(_OP_X_LAYER if len(layer_sites) > 1 else _OP_X)
                op_sites.extend(layer_sites)
                op_site_ptr.append(len(op_sites))
                continue
            op_kind.append(_OP_H)
            op_sites.append(int(op.site))
        elif isinstance(op, McwfAllOnesPhaseOp):
            if complex(op.phase) != complex(-1.0):
                raise NotImplementedError("NativeOpStreamMcwfExecutor currently supports phase=-1 only")
            op_kind.append(_OP_ALL_ONES_PHASE)
            op_sites.extend(int(s) for s in op.sites)
        elif isinstance(op, McwfKrausAllSitesOp):
            op_kind.append(_OP_KRAUS_ALL_SITES)
            op_sites.extend(int(s) for s in op.sites)
            kraus_keys.append(str(op.kraus_key))
            rand_rows += len(op.sites)
        elif isinstance(op, McwfQubitGateOp):
            raise NotImplementedError(
                "NativeOpStreamMcwfExecutor does not yet support arbitrary 1/2/3-qubit unitary ops; "
                "use DenseQutritMcwfExecutor for this program"
            )
        else:  # pragma: no cover
            raise TypeError(f"unknown MCWF op {op!r}")
        op_site_ptr.append(len(op_sites))
        oi += 1
    unique_keys = sorted(set(kraus_keys))
    if len(unique_keys) > 1:
        raise NotImplementedError("NativeOpStreamMcwfExecutor currently supports one Kraus family per program")
    if unique_keys:
        kraus_t = _kraus_family_tensor(unique_keys[0], backend, kraus_families)
    else:
        kraus_t = torch.empty((0, 3, 3), dtype=backend.dtype, device=backend.device)
    dev = metadata_device
    return (
        torch.as_tensor(op_kind, dtype=torch.int32, device=dev).contiguous(),
        torch.as_tensor(op_site_ptr, dtype=torch.int32, device=dev).contiguous(),
        torch.as_tensor(op_sites, dtype=torch.int32, device=dev).contiguous(),
        kraus_t,
        int(rand_rows),
    )


def _draw_rand(backend: DenseQutritMcwfBackend, batch_size: int, rand_rows: int) -> torch.Tensor:
    return (
        torch.stack(
            [
                torch.rand((int(batch_size),), dtype=RDTYPE, device=backend.device, generator=backend.generator)
                for _ in range(int(rand_rows))
            ],
            dim=0,
        )
        if int(rand_rows)
        else torch.empty((0, int(batch_size)), dtype=RDTYPE, device=backend.device)
    ).contiguous()


def _unique_kraus_key(program: CompiledMcwfProgram) -> str | None:
    keys = sorted({str(op.kraus_key) for op in program.operations if isinstance(op, McwfKrausAllSitesOp)})
    if len(keys) > 1:
        raise NotImplementedError("NativeOpStreamMcwfExecutor currently supports one Kraus family per program")
    return keys[0] if keys else None


def _kraus_family_tensor(
    kraus_key: str,
    backend: DenseQutritMcwfBackend,
    kraus_families: dict[str, torch.Tensor],
) -> torch.Tensor:
    try:
        kraus = kraus_families[str(kraus_key)]
    except KeyError as exc:
        raise KeyError(f"missing Kraus family {kraus_key!r}") from exc
    return torch.as_tensor(kraus, dtype=backend.dtype, device=backend.device).contiguous()


def _graph_cache_key(
    program: CompiledMcwfProgram,
    batch_size: int,
    kraus_families: dict[str, torch.Tensor],
) -> str:
    payload: dict[str, Any] = {
        "program": program.summary(),
        "batch_size": int(batch_size),
        "ops": [op.__class__.__name__ + ":" + repr(op) for op in program.operations],
        "kraus": {
            str(k): {
                "shape": list(v.shape),
                "dtype": str(v.dtype),
                "device": str(v.device),
            }
            for k, v in sorted(kraus_families.items())
        },
    }
    return json.dumps(payload, sort_keys=True)
