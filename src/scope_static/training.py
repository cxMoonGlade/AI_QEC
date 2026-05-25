from __future__ import annotations

import torch

from .fault_graph import FaultGraph
from .fields import FaultLogitField
from .likelihood import (
    build_window_nll_caches,
    exact_dem_nll,
    exact_detector_dem_nll,
    local_window_exact_nll_from_caches,
    resolve_likelihood_backend,
)
from .windows import ObservationWindow, detector_only_windows


def fit_field(
    graph: FaultGraph,
    field: FaultLogitField,
    observations: torch.Tensor,
    *,
    steps: int = 200,
    lr: float = 0.05,
    aggregate_unique: bool = True,
    device: str | torch.device = "cpu",
    backend: str = "auto",
    observation_mode: str = "full",
    regularization_weight: float = 0.0,
    likelihood_objective: str = "global_exact",
    windows: list[ObservationWindow] | tuple[ObservationWindow, ...] | None = None,
) -> dict[str, object]:
    if observation_mode not in {"full", "detectors"}:
        raise ValueError("observation_mode must be 'full' or 'detectors'")
    if likelihood_objective not in {"global_exact", "local_exact"}:
        raise ValueError("likelihood_objective must be 'global_exact' or 'local_exact'")
    device = torch.device(device)
    field = field.to(device=device)
    optimizer = torch.optim.Adam(field.parameters(), lr=float(lr))
    history: list[float] = []
    resolved_backend = None
    nll_fn = exact_detector_dem_nll if observation_mode == "detectors" else exact_dem_nll
    objective_windows = list(windows or [])
    objective_caches = []
    if likelihood_objective == "local_exact":
        if observation_mode == "detectors":
            objective_windows = detector_only_windows(graph, objective_windows)
        if not objective_windows:
            raise ValueError("local_exact training requires at least one compatible window")
        objective_caches = build_window_nll_caches(
            graph,
            observations,
            objective_windows,
            aggregate_unique=aggregate_unique,
            device=device,
        )
    for _ in range(int(steps)):
        optimizer.zero_grad(set_to_none=True)
        logits = field.realized_logits(graph)
        if resolved_backend is None:
            resolved_backend = resolve_likelihood_backend(logits, backend)
        if likelihood_objective == "local_exact":
            nll = local_window_exact_nll_from_caches(
                logits,
                objective_caches,
                backend=backend,
            )
        else:
            nll = nll_fn(graph, logits, observations, aggregate_unique=aggregate_unique, backend=backend)
        reg = field.regularization_loss()
        loss = nll + float(regularization_weight) * reg
        loss.backward()
        optimizer.step()
        history.append(float(nll.detach().cpu()))
    return {
        "field": field,
        "history": history,
        "requested_backend": backend,
        "resolved_backend": resolved_backend or backend,
        "observation_mode": observation_mode,
        "regularization_weight": float(regularization_weight),
        "likelihood_objective": likelihood_objective,
        "num_train_windows": len(objective_windows) if likelihood_objective == "local_exact" else 0,
        "max_train_window_bits": max((window.size for window in objective_windows), default=0)
        if likelihood_objective == "local_exact"
        else 0,
    }
