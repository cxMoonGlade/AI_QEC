from __future__ import annotations

import torch

from .fault_graph import FaultGraph
from .fields import FaultLogitField
from .objectives import LikelihoodObjective, build_likelihood_objective
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
    cuda_kernel_variant: str = "dp",
    spectral_min_abs_factor: float = 1e-6,
    spectral_memory_cap_bytes: int = 1024 * 1024 * 1024,
    observation_mode: str = "full",
    regularization_weight: float = 0.0,
    likelihood_objective: str = "global_exact",
    windows: WindowPlan | list[ObservationWindow] | tuple[ObservationWindow, ...] | None = None,
    prepared_objective: LikelihoodObjective | None = None,
) -> dict[str, object]:
    device = torch.device(device)
    field = field.to(device=device)
    optimizer = torch.optim.Adam(field.parameters(), lr=float(lr))
    history: list[float] = []
    resolved_backend = None
    objective = prepared_objective
    if objective is None:
        objective = build_likelihood_objective(
            graph,
            observations,
            likelihood_objective=likelihood_objective,
            observation_mode=observation_mode,
            aggregate_unique=aggregate_unique,
            backend=backend,
            cuda_kernel_variant=cuda_kernel_variant,
            spectral_min_abs_factor=spectral_min_abs_factor,
            spectral_memory_cap_bytes=spectral_memory_cap_bytes,
            windows=windows,
            device=device,
        )
    else:
        _validate_prepared_objective(
            objective,
            graph,
            likelihood_objective=likelihood_objective,
            observation_mode=observation_mode,
            aggregate_unique=aggregate_unique,
            backend=backend,
            cuda_kernel_variant=cuda_kernel_variant,
            spectral_min_abs_factor=spectral_min_abs_factor,
            spectral_memory_cap_bytes=spectral_memory_cap_bytes,
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
    objective_audit = objective.audit_dict(scalar_bytes=_field_scalar_bytes(field))
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
        "likelihood_math_objective": objective_audit["train_likelihood_math_objective"],
        "cuda_kernel_variant": objective_audit["train_cuda_kernel_variant"],
        "selected_cuda_kernel_variant": objective_audit["selected_cuda_kernel_variant"],
        "cuda_kernel_fallback_reason": objective_audit["cuda_kernel_fallback_reason"],
        "spectral_min_abs_factor": objective_audit["train_spectral_min_abs_factor"],
        "spectral_memory_cap_bytes": objective_audit["train_spectral_memory_cap_bytes"],
        "num_train_windows": objective_audit["num_train_windows"],
        "max_train_window_bits": objective_audit["max_train_window_bits"],
        "likelihood_gpu_batch_available": objective_audit["train_likelihood_gpu_batch_available"],
        "train_window_workload_audit": objective_audit.get("train_window_workload_audit", {}),
    }


def _field_scalar_bytes(field: FaultLogitField) -> int:
    for parameter in field.parameters():
        return int(parameter.element_size())
    return torch.empty((), dtype=torch.float64).element_size()


def _validate_prepared_objective(
    objective: LikelihoodObjective,
    graph: FaultGraph,
    *,
    likelihood_objective: str,
    observation_mode: str,
    aggregate_unique: bool,
    backend: str,
    cuda_kernel_variant: str,
    spectral_min_abs_factor: float,
    spectral_memory_cap_bytes: int,
) -> None:
    if objective.graph is not graph:
        raise ValueError("prepared_objective must be built for the same FaultGraph instance")
    if objective.name != likelihood_objective:
        raise ValueError("prepared_objective likelihood_objective does not match")
    if objective.observation_mode != observation_mode:
        raise ValueError("prepared_objective observation_mode does not match")
    if objective.aggregate_unique != bool(aggregate_unique):
        raise ValueError("prepared_objective aggregate_unique does not match")
    if objective.requested_backend != backend:
        raise ValueError("prepared_objective backend does not match")
    if objective.cuda_kernel_variant != cuda_kernel_variant:
        raise ValueError("prepared_objective cuda_kernel_variant does not match")
    if objective.spectral_min_abs_factor != float(spectral_min_abs_factor):
        raise ValueError("prepared_objective spectral_min_abs_factor does not match")
    if objective.spectral_memory_cap_bytes != int(spectral_memory_cap_bytes):
        raise ValueError("prepared_objective spectral_memory_cap_bytes does not match")
