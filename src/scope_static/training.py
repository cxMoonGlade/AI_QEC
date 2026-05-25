from __future__ import annotations

import torch

from .fault_graph import FaultGraph
from .fields import FaultLogitField
from .objectives import build_likelihood_objective
from .windows import ObservationWindow, WindowPlan


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
    windows: WindowPlan | list[ObservationWindow] | tuple[ObservationWindow, ...] | None = None,
) -> dict[str, object]:
    device = torch.device(device)
    field = field.to(device=device)
    optimizer = torch.optim.Adam(field.parameters(), lr=float(lr))
    history: list[float] = []
    resolved_backend = None
    objective = build_likelihood_objective(
        graph,
        observations,
        likelihood_objective=likelihood_objective,
        observation_mode=observation_mode,
        aggregate_unique=aggregate_unique,
        backend=backend,
        windows=windows,
        device=device,
    )
    for _ in range(int(steps)):
        optimizer.zero_grad(set_to_none=True)
        logits = field.realized_logits(graph)
        if resolved_backend is None:
            resolved_backend = objective.resolved_backend_for(logits)
        nll = objective.loss(logits)
        reg = field.regularization_loss()
        loss = nll + float(regularization_weight) * reg
        loss.backward()
        optimizer.step()
        history.append(float(nll.detach().cpu()))
    objective_audit = objective.audit_dict()
    adapter_name = objective.adapter_name(resolved_backend or backend)
    return {
        "field": field,
        "history": history,
        "requested_backend": objective_audit["train_requested_likelihood_backend"],
        "resolved_backend": resolved_backend or backend,
        "likelihood_adapter": adapter_name,
        "observation_mode": objective_audit["train_observation_mode"],
        "regularization_weight": float(regularization_weight),
        "likelihood_objective": objective_audit["train_likelihood_objective"],
        "num_train_windows": objective_audit["num_train_windows"],
        "max_train_window_bits": objective_audit["max_train_window_bits"],
        "likelihood_gpu_batch_available": objective_audit["train_likelihood_gpu_batch_available"],
    }
