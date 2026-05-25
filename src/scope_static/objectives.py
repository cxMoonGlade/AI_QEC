from __future__ import annotations

from dataclasses import dataclass

import torch

from .fault_graph import FaultGraph
from .likelihood import (
    WindowNLLCache,
    WindowBatchNLLCache,
    build_window_batch_nll_cache,
    build_window_nll_caches,
    exact_dem_nll,
    exact_detector_dem_nll,
    local_window_exact_nll_batched_from_cache,
    local_window_exact_nll_from_caches,
    resolve_likelihood_backend,
)
from .windows import ObservationWindow, WindowPlan, detector_only_windows


@dataclass(frozen=True)
class LikelihoodObjective:
    """Prepared DEM likelihood objective used by a training run."""

    name: str
    graph: FaultGraph
    observations: torch.Tensor
    observation_mode: str
    aggregate_unique: bool
    requested_backend: str
    windows: tuple[ObservationWindow, ...] = ()
    window_caches: tuple[WindowNLLCache, ...] = ()
    window_batch_cache: WindowBatchNLLCache | None = None

    def loss(self, logits: torch.Tensor) -> torch.Tensor:
        if self.name == "local_exact":
            if self.adapter_name(self.resolved_backend_for(logits)) == "cuda_extension_batched_window_exact":
                if self.window_batch_cache is None:
                    raise ValueError("CUDA local-window objective is missing its batch cache")
                return local_window_exact_nll_batched_from_cache(logits, self.window_batch_cache)
            return local_window_exact_nll_from_caches(
                logits,
                list(self.window_caches),
                backend=self.requested_backend,
            )
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
        return {
            "train_requested_likelihood_backend": self.requested_backend,
            "train_observation_mode": self.observation_mode,
            "train_likelihood_objective": self.name,
            "num_train_windows": len(self.windows) if self.name == "local_exact" else 0,
            "max_train_window_bits": max((window.size for window in self.windows), default=0)
            if self.name == "local_exact"
            else 0,
            "train_likelihood_gpu_batch_available": self.window_batch_cache is not None,
        }

    def adapter_name(self, resolved_backend: str) -> str:
        if self.name == "local_exact" and resolved_backend == "cuda_extension" and self.window_batch_cache is not None:
            return "cuda_extension_batched_window_exact"
        if self.name == "local_exact":
            return "python_window_loop_exact"
        if self.observation_mode == "detectors":
            return f"{resolved_backend}_detector_exact"
        return f"{resolved_backend}_global_exact"


def build_likelihood_objective(
    graph: FaultGraph,
    observations: torch.Tensor,
    *,
    likelihood_objective: str = "global_exact",
    observation_mode: str = "full",
    aggregate_unique: bool = True,
    backend: str = "auto",
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
    if likelihood_objective == "local_exact":
        if observation_mode == "detectors":
            objective_windows = tuple(detector_only_windows(graph, list(objective_windows)))
        if not objective_windows:
            raise ValueError("local_exact training requires at least one compatible window")
        caches = tuple(
            build_window_nll_caches(
                graph,
                observations,
                list(objective_windows),
                aggregate_unique=aggregate_unique,
                device=device,
            )
        )
        if torch.device(device).type == "cuda":
            batch_cache = build_window_batch_nll_cache(caches, device=device)

    return LikelihoodObjective(
        name=likelihood_objective,
        graph=graph,
        observations=observations,
        observation_mode=observation_mode,
        aggregate_unique=bool(aggregate_unique),
        requested_backend=backend,
        windows=objective_windows,
        window_caches=caches,
        window_batch_cache=batch_cache,
    )


def _coerce_windows(
    windows: WindowPlan | list[ObservationWindow] | tuple[ObservationWindow, ...] | None,
) -> tuple[ObservationWindow, ...]:
    if windows is None:
        return ()
    if isinstance(windows, WindowPlan):
        return tuple(windows.windows)
    return tuple(windows)
