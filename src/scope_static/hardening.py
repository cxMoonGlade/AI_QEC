from __future__ import annotations

from dataclasses import dataclass

import torch

from .fields import DiscoveryHardFaultLogitField
from .identifiability import deterministic_kmeans, local_logit_signature


@dataclass(frozen=True)
class AssignmentInitialization:
    labels: torch.Tensor
    alpha_init: torch.Tensor
    source: str
    uses_hidden_omega: bool
    feature_family: str | None = None


def local_logit_assignment_initialization(
    local_logits: torch.Tensor,
    *,
    num_prototypes: int,
) -> AssignmentInitialization:
    """Cluster visible local logits into a prototype assignment initializer."""

    logits = torch.as_tensor(local_logits, dtype=torch.float64, device="cpu").flatten()
    result = deterministic_kmeans(local_logit_signature(logits), int(num_prototypes))
    labels = result.labels.to(dtype=torch.long)
    alpha = _cluster_alpha_from_logits(logits, labels, int(num_prototypes))
    return AssignmentInitialization(
        labels=labels,
        alpha_init=alpha,
        source="DISC10_local_logit_signature",
        uses_hidden_omega=False,
        feature_family="local_logit",
    )


def random_balanced_assignment_initialization(
    local_logits: torch.Tensor | None,
    *,
    num_faults: int,
    num_prototypes: int,
    seed: int,
    init_logit: float = -5.5,
) -> AssignmentInitialization:
    """Random visible initializer with roughly balanced prototype use."""

    labels = torch.arange(int(num_faults), dtype=torch.long) % int(num_prototypes)
    generator = torch.Generator(device="cpu")
    generator.manual_seed(int(seed))
    labels = labels[torch.randperm(labels.numel(), generator=generator)]
    if local_logits is None:
        alpha = torch.full((int(num_prototypes),), float(init_logit), dtype=torch.float64)
    else:
        alpha = _cluster_alpha_from_logits(
            torch.as_tensor(local_logits, dtype=torch.float64, device="cpu").flatten(),
            labels,
            int(num_prototypes),
            fallback=float(init_logit),
        )
    return AssignmentInitialization(
        labels=labels,
        alpha_init=alpha,
        source="random_balanced_labels",
        uses_hidden_omega=False,
        feature_family=None,
    )


def apply_assignment_initialization(
    field: DiscoveryHardFaultLogitField,
    initialization: AssignmentInitialization,
    *,
    confidence: float = 6.0,
) -> None:
    """Initialize prototype logits and free assignment logits from labels."""

    labels = torch.as_tensor(initialization.labels, dtype=torch.long, device=field.alpha.device).flatten()
    if labels.numel() != int(field.num_faults):
        raise ValueError("initializer labels must have one entry per fault")
    if labels.min().item() < 0 or labels.max().item() >= int(field.num_prototypes):
        raise ValueError("initializer labels must lie in [0, K)")
    alpha = initialization.alpha_init.to(device=field.alpha.device, dtype=field.alpha.dtype)
    if alpha.numel() != int(field.num_prototypes):
        raise ValueError("alpha_init must have one entry per prototype")
    full_logits = field.alpha.new_full((field.num_faults, field.num_prototypes), -float(confidence))
    full_logits[torch.arange(field.num_faults, device=field.alpha.device), labels] = float(confidence)
    with torch.no_grad():
        field.alpha.copy_(alpha)
        if field.num_prototypes > 1:
            field.assignment_logits.copy_(full_logits[:, 1:] - full_logits[:, :1])


def _cluster_alpha_from_logits(
    logits: torch.Tensor,
    labels: torch.Tensor,
    num_prototypes: int,
    *,
    fallback: float | None = None,
) -> torch.Tensor:
    fallback_value = float(logits.mean().item()) if logits.numel() else -5.5
    if fallback is not None:
        fallback_value = float(fallback)
    alpha = torch.full((int(num_prototypes),), fallback_value, dtype=torch.float64)
    for prototype in range(int(num_prototypes)):
        idx = labels == prototype
        if bool(idx.any()):
            alpha[prototype] = logits[idx].mean()
    return alpha
