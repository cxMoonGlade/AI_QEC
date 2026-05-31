from __future__ import annotations

import torch

from .fault_graph import FaultGraph, fixed_fault_features
from ..numerics import NUMERICAL_ZERO


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


class DiscoveryHardFaultLogitField(FaultLogitField):
    name = "disc_hard"

    def __init__(
        self,
        num_faults: int,
        num_prototypes: int,
        *,
        init_logit: float = -5.5,
        alpha_init_scale: float = 0.01,
        assignment_init_scale: float = 0.01,
        assignment_entropy_weight: float = 0.0,
        assignment_balance_weight: float = 0.0,
        prototype_separation_weight: float = 0.0,
        prototype_separation_margin: float = 0.5,
        assignment_mode: str = "soft",
        assignment_temperature: float = 1.0,
        dtype: torch.dtype = torch.float64,
        seed: int | None = None,
    ):
        super().__init__()
        num_faults = int(num_faults)
        num_prototypes = int(num_prototypes)
        if num_faults < 0:
            raise ValueError("num_faults must be non-negative")
        if num_prototypes <= 0:
            raise ValueError("num_prototypes must be positive")
        self.num_faults = num_faults
        self.num_prototypes = num_prototypes
        self.assignment_entropy_weight = float(assignment_entropy_weight)
        self.assignment_balance_weight = float(assignment_balance_weight)
        self.prototype_separation_weight = float(prototype_separation_weight)
        self.prototype_separation_margin = float(prototype_separation_margin)
        self.assignment_mode = _normalize_assignment_mode(assignment_mode)
        self.assignment_temperature = float(assignment_temperature)
        if self.assignment_temperature <= 0.0:
            raise ValueError("assignment_temperature must be positive")
        generator = _cpu_generator(seed)
        alpha = torch.full((num_prototypes,), float(init_logit), dtype=dtype)
        if alpha_init_scale:
            alpha = alpha + float(alpha_init_scale) * _randn(alpha.shape, dtype=dtype, generator=generator)
        self.alpha = torch.nn.Parameter(alpha)
        assignment_shape = (num_faults, max(0, num_prototypes - 1))
        assignment = torch.zeros(assignment_shape, dtype=dtype)
        if assignment.numel() and assignment_init_scale:
            assignment = assignment + float(assignment_init_scale) * _randn(
                assignment.shape,
                dtype=dtype,
                generator=generator,
            )
        self.assignment_logits = torch.nn.Parameter(assignment)

    @classmethod
    def from_graph(
        cls,
        graph: FaultGraph,
        *,
        num_prototypes: int | None = None,
        prototype_count: int | None = None,
        K: int | None = None,
        **kwargs,
    ) -> "DiscoveryHardFaultLogitField":
        resolved_k = _resolve_num_prototypes(graph, num_prototypes=num_prototypes, prototype_count=prototype_count, K=K)
        return cls(graph.M, resolved_k, **kwargs)

    def assignment_probabilities(self) -> torch.Tensor:
        if self.num_prototypes == 1:
            return self.alpha.new_ones((self.num_faults, 1))
        reference = self.assignment_logits.new_zeros((self.num_faults, 1))
        logits = torch.cat([reference, self.assignment_logits], dim=1)
        logits = logits / max(NUMERICAL_ZERO, float(self.assignment_temperature))
        return torch.softmax(logits, dim=1)

    def hard_assignments(self) -> torch.Tensor:
        return torch.argmax(self.assignment_probabilities(), dim=1)

    def realized_logits(self, graph: FaultGraph | None = None) -> torch.Tensor:
        return self._assignment_weights_for_forward() @ self.alpha

    def regularization_loss(self) -> torch.Tensor:
        loss = self.alpha.new_tensor(0.0)
        S = self.assignment_probabilities()
        if self.assignment_entropy_weight:
            positive = S > 0
            entropy_terms = torch.zeros_like(S)
            entropy_terms[positive] = -(S[positive] * torch.log(S[positive]))
            entropy = entropy_terms.sum(dim=1).mean() if S.numel() else self.alpha.new_tensor(0.0)
            loss = loss + float(self.assignment_entropy_weight) * entropy
        if self.assignment_balance_weight and S.numel():
            masses = S.mean(dim=0)
            target = S.new_full((self.num_prototypes,), 1.0 / max(1, self.num_prototypes))
            loss = loss + float(self.assignment_balance_weight) * torch.mean((masses - target) ** 2)
        if self.prototype_separation_weight and self.alpha.numel() > 1:
            diffs = torch.abs(self.alpha.unsqueeze(0) - self.alpha.unsqueeze(1))
            mask = torch.triu(torch.ones_like(diffs, dtype=torch.bool), diagonal=1)
            shortfall = torch.relu(float(self.prototype_separation_margin) - diffs[mask])
            if shortfall.numel():
                loss = loss + float(self.prototype_separation_weight) * torch.mean(shortfall**2)
        return loss

    def _assignment_weights_for_forward(self) -> torch.Tensor:
        S = self.assignment_probabilities()
        if self.assignment_mode == "soft":
            return S
        hard = torch.nn.functional.one_hot(torch.argmax(S, dim=1), num_classes=self.num_prototypes).to(dtype=S.dtype)
        if self.assignment_mode == "straight_through":
            return hard + S - S.detach()
        if self.assignment_mode == "hard":
            return hard
        raise ValueError(f"unsupported assignment_mode {self.assignment_mode!r}")


class DiscoverySoftFeatureFaultLogitField(DiscoveryHardFaultLogitField):
    name = "disc_soft"

    def __init__(
        self,
        num_faults: int,
        num_prototypes: int,
        phi: torch.Tensor,
        *,
        init_logit: float = -5.5,
        alpha_init_scale: float = 0.01,
        assignment_init_scale: float = 0.01,
        assignment_entropy_weight: float = 0.0,
        assignment_balance_weight: float = 0.0,
        prototype_separation_weight: float = 0.0,
        prototype_separation_margin: float = 0.5,
        assignment_mode: str = "soft",
        assignment_temperature: float = 1.0,
        beta_l2: float = 0.0,
        dtype: torch.dtype = torch.float64,
        seed: int | None = None,
    ):
        super().__init__(
            num_faults,
            num_prototypes,
            init_logit=init_logit,
            alpha_init_scale=alpha_init_scale,
            assignment_init_scale=assignment_init_scale,
            assignment_entropy_weight=assignment_entropy_weight,
            assignment_balance_weight=assignment_balance_weight,
            prototype_separation_weight=prototype_separation_weight,
            prototype_separation_margin=prototype_separation_margin,
            assignment_mode=assignment_mode,
            assignment_temperature=assignment_temperature,
            dtype=dtype,
            seed=seed,
        )
        phi = torch.as_tensor(phi, dtype=dtype)
        if phi.ndim != 2:
            raise ValueError("phi must have shape [M, r]")
        if phi.shape[0] != int(num_faults):
            raise ValueError("phi and num_faults must agree on M")
        self.register_buffer("phi", phi)
        self.beta = torch.nn.Parameter(torch.zeros((int(num_prototypes), int(phi.shape[1])), dtype=dtype))
        self.beta_l2 = float(beta_l2)
        self.learner_visible_feature_source = "fixed_fault_features_without_hidden_orbit_selection_or_centering"
        self.learner_feature_uses_hidden_orbit_centering = False

    @classmethod
    def from_graph(
        cls,
        graph: FaultGraph,
        *,
        num_prototypes: int | None = None,
        prototype_count: int | None = None,
        K: int | None = None,
        residual_rank: int | None = None,
        dtype: torch.dtype = torch.float64,
        **kwargs,
    ) -> "DiscoverySoftFeatureFaultLogitField":
        resolved_k = _resolve_num_prototypes(graph, num_prototypes=num_prototypes, prototype_count=prototype_count, K=K)
        rank = graph.residual_rank if residual_rank is None else int(residual_rank)
        phi = discovery_fault_features(graph, residual_rank=rank, dtype=dtype)
        return cls(graph.M, resolved_k, phi, dtype=dtype, **kwargs)

    def realized_logits(self, graph: FaultGraph | None = None) -> torch.Tensor:
        prototype_logits = self.alpha.unsqueeze(0) + self.phi @ self.beta.T
        return torch.sum(self._assignment_weights_for_forward() * prototype_logits, dim=1)

    def regularization_loss(self) -> torch.Tensor:
        loss = super().regularization_loss()
        if self.beta_l2 and self.beta.numel():
            loss = loss + float(self.beta_l2) * torch.mean(self.beta**2)
        return loss


def discovery_fault_features(
    graph: FaultGraph,
    *,
    residual_rank: int | None = None,
    dtype: torch.dtype = torch.float64,
) -> torch.Tensor:
    """Learner-visible Stage-2 fault features that do not use hidden orbit labels."""

    rank = graph.residual_rank if residual_rank is None else int(residual_rank)
    features, _selected = fixed_fault_features(
        graph.A,
        graph.detector_coordinates,
        rank,
        graph.num_detectors,
        orbit_ids=None,
    )
    return features.to(dtype=dtype)


def _resolve_num_prototypes(
    graph: FaultGraph,
    *,
    num_prototypes: int | None = None,
    prototype_count: int | None = None,
    K: int | None = None,
) -> int:
    candidates = [value for value in (num_prototypes, prototype_count, K) if value is not None]
    if len(candidates) > 1 and len({int(value) for value in candidates}) != 1:
        raise ValueError("num_prototypes, prototype_count, and K must agree when provided together")
    return int(candidates[0]) if candidates else graph.O


def _cpu_generator(seed: int | None) -> torch.Generator | None:
    if seed is None:
        return None
    generator = torch.Generator(device="cpu")
    generator.manual_seed(int(seed))
    return generator


def _randn(
    shape: tuple[int, ...] | torch.Size,
    *,
    dtype: torch.dtype,
    generator: torch.Generator | None,
) -> torch.Tensor:
    if generator is None:
        return torch.randn(shape, dtype=dtype)
    return torch.randn(shape, dtype=dtype, generator=generator)


LocalField = LocalFaultLogitField
HardOrbitField = HardOrbitFaultLogitField
SoftFeatureOrbitField = SoftFeatureOrbitFaultLogitField
DiscoveryHardField = DiscoveryHardFaultLogitField
DiscoverySoftFeatureField = DiscoverySoftFeatureFaultLogitField


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
    if model_name in {"hard_orbit", "known_hard_orbit"}:
        return HardOrbitFaultLogitField.from_graph(graph, dtype=dtype)
    if model_name in {"soft_feature_orbit", "known_soft_feature_orbit"}:
        return SoftFeatureOrbitFaultLogitField.from_graph(graph, dtype=dtype)
    if model_name == "disc_hard":
        return DiscoveryHardFaultLogitField.from_graph(
            graph,
            dtype=dtype,
            seed=seed,
            num_prototypes=_option_int(model_options, "num_prototypes", "prototype_count", "K"),
            init_logit=float(model_options.get("init_logit", -5.5)),
            alpha_init_scale=float(model_options.get("alpha_init_scale", 0.01)),
            assignment_init_scale=float(model_options.get("assignment_init_scale", 0.01)),
            assignment_entropy_weight=float(model_options.get("assignment_entropy_weight", 0.0)),
            assignment_balance_weight=float(model_options.get("assignment_balance_weight", 0.0)),
            prototype_separation_weight=float(model_options.get("prototype_separation_weight", 0.0)),
            prototype_separation_margin=float(model_options.get("prototype_separation_margin", 0.5)),
            assignment_mode=str(model_options.get("assignment_mode", "soft")),
            assignment_temperature=float(model_options.get("assignment_temperature", 1.0)),
        )
    if model_name == "disc_soft":
        return DiscoverySoftFeatureFaultLogitField.from_graph(
            graph,
            dtype=dtype,
            seed=seed,
            num_prototypes=_option_int(model_options, "num_prototypes", "prototype_count", "K"),
            residual_rank=_option_int(model_options, "residual_rank"),
            init_logit=float(model_options.get("init_logit", -5.5)),
            alpha_init_scale=float(model_options.get("alpha_init_scale", 0.01)),
            assignment_init_scale=float(model_options.get("assignment_init_scale", 0.01)),
            assignment_entropy_weight=float(model_options.get("assignment_entropy_weight", 0.0)),
            assignment_balance_weight=float(model_options.get("assignment_balance_weight", 0.0)),
            prototype_separation_weight=float(model_options.get("prototype_separation_weight", 0.0)),
            prototype_separation_margin=float(model_options.get("prototype_separation_margin", 0.5)),
            assignment_mode=str(model_options.get("assignment_mode", "soft")),
            assignment_temperature=float(model_options.get("assignment_temperature", 1.0)),
            beta_l2=float(model_options.get("beta_l2", 0.0)),
        )
    if model_name == "dmle_qec":
        from .baselines import DMLEQECIndependentField

        return DMLEQECIndependentField.from_graph(
            graph,
            dtype=dtype,
            seed=seed,
            perturb_scale=float(model_options.get("perturb_scale", 0.0)),
        )
    raise ValueError(f"unknown model_name {model_name!r}")


def _option_int(model_options: dict[str, object], *keys: str) -> int | None:
    values = [model_options[key] for key in keys if key in model_options and model_options[key] is not None]
    if not values:
        return None
    ints = {int(value) for value in values}
    if len(ints) != 1:
        raise ValueError(f"model option aliases {keys!r} disagree")
    return ints.pop()


def _normalize_assignment_mode(mode: str) -> str:
    normalized = str(mode).strip().lower().replace("-", "_")
    aliases = {
        "soft": "soft",
        "free": "soft",
        "st": "straight_through",
        "hard_st": "straight_through",
        "straight_through": "straight_through",
        "straightthrough": "straight_through",
        "hard": "hard",
    }
    if normalized not in aliases:
        raise ValueError("assignment_mode must be 'soft', 'straight_through', or 'hard'")
    return aliases[normalized]
