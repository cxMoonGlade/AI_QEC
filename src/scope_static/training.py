from __future__ import annotations

import torch

from .fault_graph import FaultGraph
from .fields import FaultLogitField
from .likelihood import exact_dem_nll, exact_detector_dem_nll, resolve_likelihood_backend


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
) -> dict[str, object]:
    if observation_mode not in {"full", "detectors"}:
        raise ValueError("observation_mode must be 'full' or 'detectors'")
    device = torch.device(device)
    field = field.to(device=device)
    optimizer = torch.optim.Adam(field.parameters(), lr=float(lr))
    history: list[float] = []
    resolved_backend = None
    nll_fn = exact_detector_dem_nll if observation_mode == "detectors" else exact_dem_nll
    for _ in range(int(steps)):
        optimizer.zero_grad(set_to_none=True)
        logits = field.realized_logits(graph)
        if resolved_backend is None:
            resolved_backend = resolve_likelihood_backend(logits, backend)
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
    }
