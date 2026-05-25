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
    alpha = -5.5 + 0.45 * torch.randn(graph.O, generator=generator, dtype=dtype)
    logits = alpha[graph.orbit_ids]

    if mode == "exact_orbit":
        return logits

    if mode == "in_family_soft_residual":
        beta = torch.randn((graph.O, graph.residual_rank), generator=generator, dtype=dtype)
        residual = (beta[graph.orbit_ids] * graph.phi.to(dtype=dtype)).sum(dim=1)
        return logits + float(epsilon_break) * residual

    if mode == "out_of_family_residual":
        delta = torch.randn(graph.M, generator=generator, dtype=dtype)
        for orbit in range(graph.O):
            idx = torch.nonzero(graph.orbit_ids == orbit, as_tuple=False).flatten()
            if idx.numel():
                delta[idx] = delta[idx] - delta[idx].mean()
        return logits + float(epsilon_break) * delta

    raise ValueError(f"unknown teacher mode {mode!r}")
