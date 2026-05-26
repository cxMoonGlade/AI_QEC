from __future__ import annotations

from dataclasses import dataclass

import torch

from ..fault_graph import FaultGraph
from ..likelihood import (
    CudaKernelVariant,
    LikelihoodBackend,
    WindowBatchNLLCache,
    WindowNLLCache,
    build_window_batch_nll_cache,
    build_window_batch_nll_cache_from_observations,
    build_window_nll_caches,
    local_window_cuda_kernel_audit,
    local_window_exact_nll_batched_from_cache,
    local_window_exact_nll_from_caches,
    local_window_workload_audit,
    resolve_likelihood_backend,
)
from ..windows import ObservationWindow, WindowPlan, detector_only_windows


EXACT_LOCAL_WINDOW_PARITY_OBJECTIVE = "exact_local_window_bernoulli_parity"


@dataclass(frozen=True)
class ExactLocalWindowParityLikelihood:
    """Prepared exact local-window Bernoulli parity likelihood over DEM faults.

    This Module is intentionally below orbit/preprocessing/model logic. Callers
    provide logits over effective DEM fault columns; the adapter owns cache use,
    backend selection, CUDA kernel policy, and the audit fields for that math
    objective. It does not choose windows or infer detector/logical coverage;
    those evidence questions belong to the Window plan.
    """

    graph: FaultGraph
    observations: torch.Tensor
    observation_mode: str
    aggregate_unique: bool
    requested_backend: LikelihoodBackend
    windows: tuple[ObservationWindow, ...]
    cuda_kernel_variant: CudaKernelVariant = "dp"
    spectral_min_abs_factor: float = 1e-6
    spectral_memory_cap_bytes: int = 1024 * 1024 * 1024
    window_caches: tuple[WindowNLLCache, ...] = ()
    window_batch_cache: WindowBatchNLLCache | None = None

    @classmethod
    def prepare(
        cls,
        graph: FaultGraph,
        observations: torch.Tensor,
        *,
        windows: WindowPlan | list[ObservationWindow] | tuple[ObservationWindow, ...],
        observation_mode: str = "full",
        aggregate_unique: bool = True,
        backend: LikelihoodBackend = "auto",
        cuda_kernel_variant: CudaKernelVariant = "dp",
        spectral_min_abs_factor: float = 1e-6,
        spectral_memory_cap_bytes: int = 1024 * 1024 * 1024,
        device: str | torch.device = "cpu",
    ) -> "ExactLocalWindowParityLikelihood":
        if observation_mode not in {"full", "detectors"}:
            raise ValueError("observation_mode must be 'full' or 'detectors'")
        objective_windows = _coerce_windows(windows)
        if observation_mode == "detectors":
            objective_windows = tuple(detector_only_windows(graph, list(objective_windows)))
        if not objective_windows:
            raise ValueError("exact local-window parity likelihood requires at least one compatible window")

        target_device = torch.device(device)
        batch_cache: WindowBatchNLLCache | None = None
        caches: tuple[WindowNLLCache, ...] = ()
        if target_device.type == "cuda" and backend != "pytorch" and aggregate_unique:
            probe = torch.empty((1,), device=target_device)
            if resolve_likelihood_backend(probe, backend) == "cuda_extension":
                batch_cache = build_window_batch_nll_cache_from_observations(
                    graph,
                    observations,
                    list(objective_windows),
                    aggregate_unique=True,
                    device=target_device,
                    cache_backend="cuda_extension",
                )
        if batch_cache is None:
            caches = tuple(
                build_window_nll_caches(
                    graph,
                    observations,
                    list(objective_windows),
                    aggregate_unique=aggregate_unique,
                    device=target_device,
                )
            )
            if target_device.type == "cuda":
                batch_cache = build_window_batch_nll_cache(caches, device=target_device)

        return cls(
            graph=graph,
            observations=observations,
            observation_mode=observation_mode,
            aggregate_unique=bool(aggregate_unique),
            requested_backend=backend,
            windows=objective_windows,
            cuda_kernel_variant=str(cuda_kernel_variant),
            spectral_min_abs_factor=float(spectral_min_abs_factor),
            spectral_memory_cap_bytes=int(spectral_memory_cap_bytes),
            window_caches=caches,
            window_batch_cache=batch_cache,
        )

    def loss(self, logits: torch.Tensor) -> torch.Tensor:
        if logits.ndim != 1 or logits.numel() != self.graph.M:
            raise ValueError(f"logits must have shape [{self.graph.M}]")
        if self.adapter_name(self.resolved_backend_for(logits)) == "cuda_extension_batched_window_exact":
            if self.window_batch_cache is None:
                raise ValueError("CUDA local-window likelihood is missing its batch cache")
            return local_window_exact_nll_batched_from_cache(
                logits,
                self.window_batch_cache,
                cuda_kernel_variant=self.cuda_kernel_variant,
                spectral_min_abs_factor=self.spectral_min_abs_factor,
                spectral_memory_cap_bytes=self.spectral_memory_cap_bytes,
            )
        if not self.window_caches:
            raise ValueError("Python local-window likelihood is missing its window caches")
        return local_window_exact_nll_from_caches(
            logits,
            list(self.window_caches),
            backend=self.requested_backend,
        )

    def resolved_backend_for(self, logits: torch.Tensor) -> str:
        return resolve_likelihood_backend(logits, self.requested_backend)

    def adapter_name(self, resolved_backend: str) -> str:
        if resolved_backend == "cuda_extension" and self.window_batch_cache is not None:
            return "cuda_extension_batched_window_exact"
        return "python_window_loop_exact"

    def audit_dict(self) -> dict[str, object]:
        result = {
            "likelihood_objective": EXACT_LOCAL_WINDOW_PARITY_OBJECTIVE,
            "requested_likelihood_backend": self.requested_backend,
            "observation_mode": self.observation_mode,
            "aggregate_unique": bool(self.aggregate_unique),
            "cuda_kernel_variant": self.cuda_kernel_variant,
            "spectral_min_abs_factor": float(self.spectral_min_abs_factor),
            "spectral_memory_cap_bytes": int(self.spectral_memory_cap_bytes),
            "num_windows": self.num_windows,
            "max_window_bits": self.max_window_bits,
            "likelihood_gpu_batch_available": self.window_batch_cache is not None,
            "adapter": self.adapter_name("cuda_extension" if self.requested_backend != "pytorch" else "pytorch"),
        }
        if self.window_batch_cache is not None:
            result.update(local_window_workload_audit(self.window_batch_cache))
            result.update(
                local_window_cuda_kernel_audit(
                    self.window_batch_cache,
                    requested_kernel_variant=self.cuda_kernel_variant,
                    spectral_memory_cap_bytes=self.spectral_memory_cap_bytes,
                )
            )
        else:
            result.update(
                {
                    "requested_cuda_kernel_variant": self.cuda_kernel_variant,
                    "selected_cuda_kernel_variant": self.cuda_kernel_variant,
                    "cuda_kernel_fallback_reason": None,
                    "spectral_history_rows": 0,
                    "spectral_required_bytes": 0,
                    "spectral_memory_cap_bytes": int(self.spectral_memory_cap_bytes),
                }
            )
        return result

    @property
    def num_windows(self) -> int:
        if self.windows:
            return len(self.windows)
        if self.window_batch_cache is not None:
            return int(self.window_batch_cache.num_windows)
        return len(self.window_caches)

    @property
    def max_window_bits(self) -> int:
        if self.windows:
            return max((window.size for window in self.windows), default=0)
        if self.window_batch_cache is not None and self.window_batch_cache.num_windows:
            return int(self.window_batch_cache.window_num_bits.detach().max().cpu().item())
        return max((cache.window.size for cache in self.window_caches), default=0)


def _coerce_windows(
    windows: WindowPlan | list[ObservationWindow] | tuple[ObservationWindow, ...],
) -> tuple[ObservationWindow, ...]:
    if isinstance(windows, WindowPlan):
        return tuple(windows.windows)
    return tuple(windows)
