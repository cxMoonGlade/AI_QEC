from __future__ import annotations

import torch

from .fault_graph import FaultGraph


class FaultLogitField(torch.nn.Module):
    name = "base"

    def realized_logits(self, graph: FaultGraph | None = None) -> torch.Tensor:
        raise NotImplementedError

    def regularization_loss(self) -> torch.Tensor:
        parameters = list(self.parameters())
        if not parameters:
            return torch.tensor(0.0)
        return parameters[0].new_tensor(0.0)

    @property
    def parameter_count(self) -> int:
        return sum(parameter.numel() for parameter in self.parameters())


class LocalFaultLogitField(FaultLogitField):
    name = "local"

    def __init__(self, num_faults: int, *, init_logit: float = -5.5, dtype: torch.dtype = torch.float64):
        super().__init__()
        self.gamma = torch.nn.Parameter(torch.full((int(num_faults),), float(init_logit), dtype=dtype))

    @classmethod
    def from_graph(cls, graph: FaultGraph, **kwargs) -> "LocalFaultLogitField":
        return cls(graph.M, **kwargs)

    def realized_logits(self, graph: FaultGraph | None = None) -> torch.Tensor:
        return self.gamma


class HardOrbitFaultLogitField(FaultLogitField):
    name = "hard_orbit"

    def __init__(
        self,
        orbit_ids: torch.Tensor,
        *,
        init_logit: float = -5.5,
        dtype: torch.dtype = torch.float64,
    ):
        super().__init__()
        orbit_ids = torch.as_tensor(orbit_ids, dtype=torch.long)
        self.register_buffer("orbit_ids", orbit_ids)
        num_orbits = int(orbit_ids.max().item() + 1) if orbit_ids.numel() else 0
        self.alpha = torch.nn.Parameter(torch.full((num_orbits,), float(init_logit), dtype=dtype))

    @classmethod
    def from_graph(cls, graph: FaultGraph, **kwargs) -> "HardOrbitFaultLogitField":
        return cls(graph.orbit_ids, **kwargs)

    def realized_logits(self, graph: FaultGraph | None = None) -> torch.Tensor:
        return self.alpha[self.orbit_ids]


class SoftFeatureOrbitFaultLogitField(FaultLogitField):
    name = "soft_feature_orbit"

    def __init__(
        self,
        orbit_ids: torch.Tensor,
        phi: torch.Tensor,
        *,
        init_logit: float = -5.5,
        dtype: torch.dtype = torch.float64,
    ):
        super().__init__()
        orbit_ids = torch.as_tensor(orbit_ids, dtype=torch.long)
        phi = torch.as_tensor(phi, dtype=dtype)
        if phi.ndim != 2:
            raise ValueError("phi must have shape [M, r]")
        if phi.shape[0] != orbit_ids.numel():
            raise ValueError("phi and orbit_ids must agree on M")
        self.register_buffer("orbit_ids", orbit_ids)
        self.register_buffer("phi", phi)
        num_orbits = int(orbit_ids.max().item() + 1) if orbit_ids.numel() else 0
        residual_rank = int(phi.shape[1])
        self.alpha = torch.nn.Parameter(torch.full((num_orbits,), float(init_logit), dtype=dtype))
        self.beta = torch.nn.Parameter(torch.zeros((num_orbits, residual_rank), dtype=dtype))

    @classmethod
    def from_graph(cls, graph: FaultGraph, **kwargs) -> "SoftFeatureOrbitFaultLogitField":
        return cls(graph.orbit_ids, graph.phi, **kwargs)

    def realized_logits(self, graph: FaultGraph | None = None) -> torch.Tensor:
        return self.alpha[self.orbit_ids] + (self.beta[self.orbit_ids] * self.phi).sum(dim=1)

    def regularization_loss(self) -> torch.Tensor:
        if self.beta.numel() == 0:
            return self.beta.new_tensor(0.0)
        return torch.mean(self.beta**2)


LocalField = LocalFaultLogitField
HardOrbitField = HardOrbitFaultLogitField
SoftFeatureOrbitField = SoftFeatureOrbitFaultLogitField


def make_field(
    model_name: str,
    graph: FaultGraph,
    *,
    dtype: torch.dtype = torch.float64,
    seed: int | None = None,
    model_options: dict[str, object] | None = None,
) -> FaultLogitField:
    model_options = dict(model_options or {})
    if model_name == "local":
        return LocalFaultLogitField.from_graph(graph, dtype=dtype)
    if model_name == "hard_orbit":
        return HardOrbitFaultLogitField.from_graph(graph, dtype=dtype)
    if model_name == "soft_feature_orbit":
        return SoftFeatureOrbitFaultLogitField.from_graph(graph, dtype=dtype)
    if model_name == "dmle_qec":
        from .baselines import DMLEQECIndependentField

        return DMLEQECIndependentField.from_graph(
            graph,
            dtype=dtype,
            seed=seed,
            perturb_scale=float(model_options.get("perturb_scale", 0.0)),
        )
    raise ValueError(f"unknown model_name {model_name!r}")
