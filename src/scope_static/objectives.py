from __future__ import annotations

from dataclasses import dataclass

import torch

from .fault_graph import FaultGraph
from .likelihood import (
    WindowNLLCache,
    WindowBatchNLLCache,
    exact_dem_nll,
    exact_detector_dem_nll,
    resolve_likelihood_backend,
)
from .likelihoods.local_window_parity import ExactLocalWindowParityLikelihood
from .windows import ObservationWindow, WindowPlan


@dataclass(frozen=True)
class LikelihoodObjective:
    """Prepared DEM likelihood objective used by a training run."""

    name: str
    graph: FaultGraph
    observations: torch.Tensor
    observation_mode: str
    aggregate_unique: bool
    requested_backend: str
    cuda_kernel_variant: str = "dp"
    spectral_min_abs_factor: float = 1e-6
    spectral_memory_cap_bytes: int = 1024 * 1024 * 1024
    windows: tuple[ObservationWindow, ...] = ()
    window_caches: tuple[WindowNLLCache, ...] = ()
    window_batch_cache: WindowBatchNLLCache | None = None
    local_window_likelihood: ExactLocalWindowParityLikelihood | None = None

    def loss(self, logits: torch.Tensor) -> torch.Tensor:
        if self.name == "local_exact":
            return self._prepared_local_window_likelihood().loss(logits)
        if self.observation_mode == "detectors":
            return exact_detector_dem_nll(
                self.graph,
                logits,
                self.observations,
                aggregate_unique=self.aggregate_unique,
                backend=self.requested_backend,
            )
        return exact_dem_nll(
            self.graph,
            logits,
            self.observations,
            aggregate_unique=self.aggregate_unique,
            backend=self.requested_backend,
        )

    def resolved_backend_for(self, logits: torch.Tensor) -> str:
        return resolve_likelihood_backend(logits, self.requested_backend)

    def audit_dict(self) -> dict[str, object]:
        local_audit = self._prepared_local_window_likelihood().audit_dict() if self.name == "local_exact" else None
        result = {
            "train_requested_likelihood_backend": self.requested_backend,
            "train_observation_mode": self.observation_mode,
            "train_likelihood_objective": self.name,
            "train_likelihood_math_objective": _math_objective_name(self.name, self.observation_mode)
            if local_audit is None
            else local_audit["likelihood_objective"],
            "train_cuda_kernel_variant": self.cuda_kernel_variant,
            "train_spectral_min_abs_factor": float(self.spectral_min_abs_factor),
            "train_spectral_memory_cap_bytes": int(self.spectral_memory_cap_bytes),
            "num_train_windows": len(self.windows) if self.name == "local_exact" else 0,
            "max_train_window_bits": max((window.size for window in self.windows), default=0)
            if self.name == "local_exact"
            else 0,
            "train_likelihood_gpu_batch_available": self.window_batch_cache is not None,
        }
        if local_audit is not None:
            result.update(
                {
                    "train_requested_likelihood_backend": local_audit["requested_likelihood_backend"],
                    "train_observation_mode": local_audit["observation_mode"],
                    "train_cuda_kernel_variant": local_audit["cuda_kernel_variant"],
                    "train_spectral_min_abs_factor": local_audit["spectral_min_abs_factor"],
                    "train_spectral_memory_cap_bytes": local_audit["spectral_memory_cap_bytes"],
                    "num_train_windows": local_audit["num_windows"],
                    "max_train_window_bits": local_audit["max_window_bits"],
                    "train_likelihood_gpu_batch_available": local_audit["likelihood_gpu_batch_available"],
                    "train_likelihood_adapter": local_audit["adapter"],
                    "train_window_workload_audit": {
                        key: local_audit[key]
                        for key in (
                            "num_windows",
                            "max_window_bits",
                            "mean_state_count",
                            "total_window_state_count",
                            "mean_active_faults_per_window",
                            "max_active_faults_per_window",
                            "total_active_fault_window_pairs",
                            "unique_local_observation_patterns",
                        )
                        if key in local_audit
                    },
                    "requested_cuda_kernel_variant": local_audit["requested_cuda_kernel_variant"],
                    "selected_cuda_kernel_variant": local_audit["selected_cuda_kernel_variant"],
                    "cuda_kernel_fallback_reason": local_audit["cuda_kernel_fallback_reason"],
                    "spectral_history_rows": local_audit["spectral_history_rows"],
                    "spectral_required_bytes": local_audit["spectral_required_bytes"],
                    "spectral_memory_cap_bytes": local_audit["spectral_memory_cap_bytes"],
                }
            )
        else:
            result.update(
                {
                    "requested_cuda_kernel_variant": self.cuda_kernel_variant,
                    "selected_cuda_kernel_variant": self.cuda_kernel_variant,
                    "cuda_kernel_fallback_reason": None,
                }
            )
        return result

    def adapter_name(self, resolved_backend: str) -> str:
        if self.name == "local_exact":
            return self._prepared_local_window_likelihood().adapter_name(resolved_backend)
        if self.observation_mode == "detectors":
            return f"{resolved_backend}_detector_exact"
        return f"{resolved_backend}_global_exact"

    def _prepared_local_window_likelihood(self) -> ExactLocalWindowParityLikelihood:
        if self.local_window_likelihood is not None:
            return self.local_window_likelihood
        return ExactLocalWindowParityLikelihood(
            graph=self.graph,
            observations=self.observations,
            observation_mode=self.observation_mode,
            aggregate_unique=self.aggregate_unique,
            requested_backend=self.requested_backend,
            windows=self.windows,
            cuda_kernel_variant=self.cuda_kernel_variant,
            spectral_min_abs_factor=self.spectral_min_abs_factor,
            spectral_memory_cap_bytes=self.spectral_memory_cap_bytes,
            window_caches=self.window_caches,
            window_batch_cache=self.window_batch_cache,
        )


def build_likelihood_objective(
    graph: FaultGraph,
    observations: torch.Tensor,
    *,
    likelihood_objective: str = "global_exact",
    observation_mode: str = "full",
    aggregate_unique: bool = True,
    backend: str = "auto",
    cuda_kernel_variant: str = "dp",
    spectral_min_abs_factor: float = 1e-6,
    spectral_memory_cap_bytes: int = 1024 * 1024 * 1024,
    windows: WindowPlan | list[ObservationWindow] | tuple[ObservationWindow, ...] | None = None,
    device: str | torch.device = "cpu",
) -> LikelihoodObjective:
    if observation_mode not in {"full", "detectors"}:
        raise ValueError("observation_mode must be 'full' or 'detectors'")
    if likelihood_objective not in {"global_exact", "local_exact"}:
        raise ValueError("likelihood_objective must be 'global_exact' or 'local_exact'")

    objective_windows = _coerce_windows(windows)
    caches: tuple[WindowNLLCache, ...] = ()
    batch_cache: WindowBatchNLLCache | None = None
    local_window_likelihood: ExactLocalWindowParityLikelihood | None = None
    if likelihood_objective == "local_exact":
        local_window_likelihood = ExactLocalWindowParityLikelihood.prepare(
            graph,
            observations,
            windows=objective_windows,
            observation_mode=observation_mode,
            aggregate_unique=aggregate_unique,
            backend=backend,
            cuda_kernel_variant=cuda_kernel_variant,
            spectral_min_abs_factor=spectral_min_abs_factor,
            spectral_memory_cap_bytes=spectral_memory_cap_bytes,
            device=device,
        )
        objective_windows = local_window_likelihood.windows
        caches = local_window_likelihood.window_caches
        batch_cache = local_window_likelihood.window_batch_cache

    return LikelihoodObjective(
        name=likelihood_objective,
        graph=graph,
        observations=observations,
        observation_mode=observation_mode,
        aggregate_unique=bool(aggregate_unique),
        requested_backend=backend,
        cuda_kernel_variant=str(cuda_kernel_variant),
        spectral_min_abs_factor=float(spectral_min_abs_factor),
        spectral_memory_cap_bytes=int(spectral_memory_cap_bytes),
        windows=objective_windows,
        window_caches=caches,
        window_batch_cache=batch_cache,
        local_window_likelihood=local_window_likelihood,
    )


def _coerce_windows(
    windows: WindowPlan | list[ObservationWindow] | tuple[ObservationWindow, ...] | None,
) -> tuple[ObservationWindow, ...]:
    if windows is None:
        return ()
    if isinstance(windows, WindowPlan):
        return tuple(windows.windows)
    return tuple(windows)


def _math_objective_name(likelihood_objective: str, observation_mode: str) -> str:
    if likelihood_objective == "global_exact" and observation_mode == "detectors":
        return "exact_detector_dem_bernoulli_parity"
    if likelihood_objective == "global_exact":
        return "exact_global_dem_bernoulli_parity"
    return likelihood_objective
