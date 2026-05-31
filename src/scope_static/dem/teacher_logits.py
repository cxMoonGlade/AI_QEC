from __future__ import annotations

import torch

from .fault_graph import FaultGraph


def make_teacher_logits(
    graph: FaultGraph,
    *,
    mode: str,
    epsilon_break: float = 0.0,
    seed: int = 0,
    dtype: torch.dtype = torch.float64,
) -> torch.Tensor:
    generator = torch.Generator(device="cpu")
    generator.manual_seed(int(seed))
    if mode.endswith("_separated"):
        alpha = _separated_orbit_logits(graph.O, generator=generator, dtype=dtype)
        base_mode = mode[: -len("_separated")]
    else:
        alpha = -5.5 + 0.45 * torch.randn(graph.O, generator=generator, dtype=dtype)
        base_mode = mode
    logits = alpha[graph.orbit_ids]

    if base_mode == "exact_orbit":
        return logits

    if base_mode == "in_family_soft_residual":
        beta = torch.randn((graph.O, graph.residual_rank), generator=generator, dtype=dtype)
        residual = (beta[graph.orbit_ids] * graph.phi.to(dtype=dtype)).sum(dim=1)
        return logits + float(epsilon_break) * residual

    if base_mode == "out_of_family_residual":
        delta = torch.randn(graph.M, generator=generator, dtype=dtype)
        for orbit in range(graph.O):
            idx = torch.nonzero(graph.orbit_ids == orbit, as_tuple=False).flatten()
            if idx.numel():
                delta[idx] = delta[idx] - delta[idx].mean()
        return logits + float(epsilon_break) * delta

    raise ValueError(f"unknown teacher mode {mode!r}")


def _separated_orbit_logits(
    num_orbits: int,
    *,
    generator: torch.Generator,
    dtype: torch.dtype,
) -> torch.Tensor:
    """Teacher logits with clear prototype separation for identifiability checks."""

    if int(num_orbits) <= 0:
        return torch.empty((0,), dtype=dtype)
    values = torch.linspace(-7.0, -4.0, int(num_orbits), dtype=dtype)
    permutation = torch.randperm(int(num_orbits), generator=generator)
    return values[permutation]
