from __future__ import annotations

from dataclasses import dataclass
import math

import torch

from .fault_graph import FaultGraph
from .fields import FaultLogitField
from .hardening import AssignmentInitialization, apply_assignment_initialization, local_logit_assignment_initialization
from .metrics import adjusted_rand_index, normalized_mutual_info
from .numerics import NUMERICAL_ZERO


@dataclass(frozen=True)
class MultiEnvTeacher:
    env_ids: tuple[int, ...]
    alpha_by_env: torch.Tensor
    logits_by_env: torch.Tensor
    env_names: tuple[str, ...]
    omega: torch.Tensor


class MultiEnvSharedAssignmentField(FaultLogitField):
    name = "multi_env_shared_S"

    def __init__(
        self,
        num_faults: int,
        num_prototypes: int,
        num_environments: int,
        *,
        init_logit: float = -5.5,
        alpha_init_scale: float = 0.01,
        assignment_init_scale: float = 0.01,
        assignment_entropy_weight: float = 0.0,
        assignment_balance_weight: float = 0.0,
        dtype: torch.dtype = torch.float64,
        seed: int | None = None,
    ):
        super().__init__()
        self.num_faults = int(num_faults)
        self.num_prototypes = int(num_prototypes)
        self.num_environments = int(num_environments)
        if self.num_faults <= 0:
            raise ValueError("num_faults must be positive")
        if self.num_prototypes <= 0:
            raise ValueError("num_prototypes must be positive")
        if self.num_environments <= 0:
            raise ValueError("num_environments must be positive")
        self.assignment_entropy_weight = float(assignment_entropy_weight)
        self.assignment_balance_weight = float(assignment_balance_weight)
        generator = _cpu_generator(seed)
        alpha = torch.full((self.num_environments, self.num_prototypes), float(init_logit), dtype=dtype)
        if alpha_init_scale:
            alpha = alpha + float(alpha_init_scale) * _randn(alpha.shape, dtype=dtype, generator=generator)
        self.alpha = torch.nn.Parameter(alpha)
        assignment = torch.zeros((self.num_faults, max(0, self.num_prototypes - 1)), dtype=dtype)
        if assignment.numel() and assignment_init_scale:
            assignment = assignment + float(assignment_init_scale) * _randn(
                assignment.shape,
                dtype=dtype,
                generator=generator,
            )
        self.assignment_logits = torch.nn.Parameter(assignment)

    def assignment_probabilities(self) -> torch.Tensor:
        if self.num_prototypes == 1:
            return self.alpha.new_ones((self.num_faults, 1))
        reference = self.assignment_logits.new_zeros((self.num_faults, 1))
        return torch.softmax(torch.cat([reference, self.assignment_logits], dim=1), dim=1)

    def hard_assignments(self) -> torch.Tensor:
        return torch.argmax(self.assignment_probabilities(), dim=1)

    def realized_logits(self, graph: FaultGraph | None = None) -> torch.Tensor:
        S = self.assignment_probabilities()
        return S @ self.alpha.T

    def realized_logits_for_env(self, env_slot: int) -> torch.Tensor:
        return self.assignment_probabilities() @ self.alpha[int(env_slot)]

    def regularization_loss(self) -> torch.Tensor:
        S = self.assignment_probabilities()
        loss = self.alpha.new_tensor(0.0)
        if self.assignment_entropy_weight:
            loss = loss + float(self.assignment_entropy_weight) * assignment_entropy(S)
        if self.assignment_balance_weight:
            masses = S.mean(dim=0)
            target = S.new_full((self.num_prototypes,), 1.0 / max(1, self.num_prototypes))
            loss = loss + float(self.assignment_balance_weight) * torch.mean((masses - target) ** 2)
        return loss


class MultiEnvIndependentAssignmentField(FaultLogitField):
    name = "multi_env_independent_S_per_env"

    def __init__(
        self,
        num_faults: int,
        num_prototypes: int,
        num_environments: int,
        *,
        init_logit: float = -5.5,
        alpha_init_scale: float = 0.01,
        assignment_init_scale: float = 0.01,
        dtype: torch.dtype = torch.float64,
        seed: int | None = None,
    ):
        super().__init__()
        self.num_faults = int(num_faults)
        self.num_prototypes = int(num_prototypes)
        self.num_environments = int(num_environments)
        generator = _cpu_generator(seed)
        alpha = torch.full((self.num_environments, self.num_prototypes), float(init_logit), dtype=dtype)
        if alpha_init_scale:
            alpha = alpha + float(alpha_init_scale) * _randn(alpha.shape, dtype=dtype, generator=generator)
        self.alpha = torch.nn.Parameter(alpha)
        assignment = torch.zeros((self.num_environments, self.num_faults, max(0, self.num_prototypes - 1)), dtype=dtype)
        if assignment.numel() and assignment_init_scale:
            assignment = assignment + float(assignment_init_scale) * _randn(
                assignment.shape,
                dtype=dtype,
                generator=generator,
            )
        self.assignment_logits = torch.nn.Parameter(assignment)

    def assignment_probabilities(self) -> torch.Tensor:
        if self.num_prototypes == 1:
            return self.alpha.new_ones((self.num_environments, self.num_faults, 1))
        reference = self.assignment_logits.new_zeros((self.num_environments, self.num_faults, 1))
        return torch.softmax(torch.cat([reference, self.assignment_logits], dim=2), dim=2)

    def assignment_probabilities_for_env(self, env_slot: int) -> torch.Tensor:
        return self.assignment_probabilities()[int(env_slot)]

    def realized_logits(self, graph: FaultGraph | None = None) -> torch.Tensor:
        S = self.assignment_probabilities()
        return torch.einsum("emk,ek->me", S, self.alpha)

    def realized_logits_for_env(self, env_slot: int) -> torch.Tensor:
        env = int(env_slot)
        return self.assignment_probabilities()[env] @ self.alpha[env]


class MultiEnvKnownOrbitField(FaultLogitField):
    name = "known_orbit_oracle_shared_S"

    def __init__(self, orbit_ids: torch.Tensor, num_environments: int, *, init_logit: float = -5.5, dtype: torch.dtype = torch.float64):
        super().__init__()
        orbit_ids = torch.as_tensor(orbit_ids, dtype=torch.long)
        self.register_buffer("orbit_ids", orbit_ids)
        self.num_environments = int(num_environments)
        self.num_prototypes = int(orbit_ids.max().item() + 1) if orbit_ids.numel() else 0
        self.alpha = torch.nn.Parameter(
            torch.full((self.num_environments, self.num_prototypes), float(init_logit), dtype=dtype)
        )

    def assignment_probabilities(self) -> torch.Tensor:
        return torch.nn.functional.one_hot(self.orbit_ids, num_classes=self.num_prototypes).to(dtype=self.alpha.dtype)

    def hard_assignments(self) -> torch.Tensor:
        return self.orbit_ids

    def realized_logits(self, graph: FaultGraph | None = None) -> torch.Tensor:
        return self.alpha[:, self.orbit_ids].T

    def realized_logits_for_env(self, env_slot: int) -> torch.Tensor:
        return self.alpha[int(env_slot), self.orbit_ids]


class MultiEnvLocalField(FaultLogitField):
    name = "local_full_per_fault_per_env"

    def __init__(
        self,
        num_faults: int,
        num_environments: int,
        *,
        init_logit: float = -5.5,
        dtype: torch.dtype = torch.float64,
    ):
        super().__init__()
        self.gamma = torch.nn.Parameter(torch.full((int(num_environments), int(num_faults)), float(init_logit), dtype=dtype))

    def realized_logits(self, graph: FaultGraph | None = None) -> torch.Tensor:
        return self.gamma.T

    def realized_logits_for_env(self, env_slot: int) -> torch.Tensor:
        return self.gamma[int(env_slot)]


def make_multi_env_teacher(
    graph: FaultGraph,
    *,
    seed: int = 0,
    dtype: torch.dtype = torch.float64,
    contrast_strength: float = 1.0,
    design: str = "default",
) -> MultiEnvTeacher:
    generator = torch.Generator(device="cpu")
    generator.manual_seed(int(seed))
    base = torch.linspace(-7.0, -4.0, graph.O, dtype=dtype)
    base = base[torch.randperm(graph.O, generator=generator)]
    support = graph.A[: graph.num_detectors, :].to(dtype=torch.float64).sum(dim=0)
    logical = graph.A[graph.num_detectors :, :].to(dtype=torch.float64).sum(dim=0)
    support_by_orbit = _orbit_mean(support, graph.orbit_ids, graph.O)
    logical_by_orbit = _orbit_mean(logical, graph.orbit_ids, graph.O)
    support_norm = _standardize_vector(support_by_orbit).to(dtype=dtype)
    logical_norm = _standardize_vector(logical_by_orbit).to(dtype=dtype)
    sparse = torch.zeros_like(base)
    sparse[torch.arange(graph.O) % 3 == 0] = 0.9
    if design == "codebook":
        perturb = codebook_perturbations(5, graph.O, dtype=dtype)
        alpha = base.unsqueeze(0) + float(contrast_strength) * perturb
        env_names = tuple(f"codebook_env_{env}" for env in range(5))
    elif design == "default":
        perturb = torch.stack(
            [
                torch.zeros_like(base),
                torch.linspace(-0.7, 0.7, graph.O, dtype=dtype),
                sparse,
                0.6 * support_norm + 0.3 * logical_norm,
                0.35 * torch.linspace(-1.0, 1.0, graph.O, dtype=dtype) + 0.45 * support_norm + 0.5 * sparse,
            ],
            dim=0,
        )
        alpha = base.unsqueeze(0) + float(contrast_strength) * perturb
        env_names = (
            "base_alpha",
            "group_scaled_alpha",
            "sparse_boosted_prototypes",
            "support_size_perturbation",
            "mixed_perturbation",
        )
    else:
        raise ValueError("multi-env teacher design must be 'default' or 'codebook'")
    logits = alpha[:, graph.orbit_ids].T.contiguous()
    return MultiEnvTeacher(
        env_ids=tuple(range(5)),
        alpha_by_env=alpha.contiguous(),
        logits_by_env=logits,
        env_names=env_names,
        omega=graph.orbit_ids.clone(),
    )


def codebook_perturbations(
    num_environments: int,
    num_prototypes: int,
    *,
    dtype: torch.dtype = torch.float64,
) -> torch.Tensor:
    rows = []
    prototype_index = torch.arange(int(num_prototypes), dtype=dtype)
    for env in range(int(num_environments)):
        frequency = env + 1
        pattern = torch.where(((prototype_index.long() * frequency + env) % 2) == 0, 1.0, -1.0).to(dtype=dtype)
        rows.append(pattern)
    code = torch.stack(rows, dim=0)
    code = code - code.mean(dim=0, keepdim=True)
    scale = code.std(dim=0, unbiased=False).clamp_min(NUMERICAL_ZERO)
    return code / scale


def initialize_shared_from_local_logits(
    field: MultiEnvSharedAssignmentField,
    local_logits: torch.Tensor,
    *,
    confidence: float = 6.0,
) -> AssignmentInitialization:
    init = local_logit_assignment_initialization(local_logits, num_prototypes=field.num_prototypes)
    # Reuse the single-env initializer on the shared assignment table, then copy
    # the same prototype centers into each environment as a visible warm start.
    proxy = _SingleAlphaProxy(field)
    apply_assignment_initialization(proxy, init, confidence=confidence)
    with torch.no_grad():
        field.assignment_logits.copy_(proxy.assignment_logits)
        field.alpha.copy_(init.alpha_init.to(dtype=field.alpha.dtype, device=field.alpha.device).unsqueeze(0).expand_as(field.alpha))
    return init


def assignment_recovery_metrics(
    assignment_probabilities: torch.Tensor,
    omega: torch.Tensor,
    *,
    active_mass_threshold: float = 1.0,
) -> dict[str, object]:
    S = torch.as_tensor(assignment_probabilities, dtype=torch.float64, device="cpu")
    if S.ndim != 2:
        raise ValueError("assignment_probabilities must have shape [M, K]")
    labels = torch.argmax(S, dim=1)
    masses = S.sum(dim=0)
    positive = S > 0
    entropy_terms = torch.zeros_like(S)
    entropy_terms[positive] = -(S[positive] * torch.log(S[positive]))
    entropy = entropy_terms.sum(dim=1).mean() if S.numel() else torch.tensor(0.0)
    return {
        "ari": adjusted_rand_index(labels, omega),
        "nmi": normalized_mutual_info(labels, omega),
        "hard_assignment_labels": [int(value) for value in labels.tolist()],
        "assignment_entropy_mean": float(entropy.item()),
        "assignment_entropy_normalized": 0.0 if S.shape[1] <= 1 else float(entropy.item() / math.log(int(S.shape[1]))),
        "prototype_masses": [float(value) for value in masses.tolist()],
        "num_active_prototypes": int((masses >= float(active_mass_threshold)).sum().item()),
        "assignment_collapse": bool(int((masses >= float(active_mass_threshold)).sum().item()) <= 1),
    }


def independent_assignment_recovery_metrics(
    assignment_probabilities: torch.Tensor,
    omega: torch.Tensor,
    *,
    active_mass_threshold: float = 1.0,
) -> dict[str, object]:
    S = torch.as_tensor(assignment_probabilities, dtype=torch.float64, device="cpu")
    rows = [
        assignment_recovery_metrics(S[env], omega, active_mass_threshold=active_mass_threshold)
        for env in range(int(S.shape[0]))
    ]
    return {
        "ari": _mean([row["ari"] for row in rows]),
        "nmi": _mean([row["nmi"] for row in rows]),
        "assignment_entropy_mean": _mean([row["assignment_entropy_mean"] for row in rows]),
        "assignment_entropy_normalized": _mean([row["assignment_entropy_normalized"] for row in rows]),
        "num_active_prototypes": _mean([row["num_active_prototypes"] for row in rows]),
        "assignment_collapse": any(bool(row["assignment_collapse"]) for row in rows),
        "per_env_assignment_recovery": rows,
    }


def assignment_entropy(S: torch.Tensor) -> torch.Tensor:
    positive = S > 0
    terms = torch.zeros_like(S)
    terms[positive] = -(S[positive] * torch.log(S[positive]))
    return terms.sum(dim=1).mean() if S.numel() else S.new_tensor(0.0)


def _orbit_mean(values: torch.Tensor, orbit_ids: torch.Tensor, num_orbits: int) -> torch.Tensor:
    result = torch.zeros((int(num_orbits),), dtype=torch.float64)
    for orbit in range(int(num_orbits)):
        idx = orbit_ids == orbit
        if bool(idx.any()):
            result[orbit] = values[idx].mean()
    return result


def _standardize_vector(values: torch.Tensor) -> torch.Tensor:
    centered = values - values.mean()
    return centered / centered.std(unbiased=False).clamp_min(NUMERICAL_ZERO)


def _mean(values: list[object]) -> float:
    floats = [float(value) for value in values if value is not None]
    return float(sum(floats) / len(floats)) if floats else 0.0


def _cpu_generator(seed: int | None) -> torch.Generator | None:
    if seed is None:
        return None
    generator = torch.Generator(device="cpu")
    generator.manual_seed(int(seed))
    return generator


def _randn(shape: tuple[int, ...] | torch.Size, *, dtype: torch.dtype, generator: torch.Generator | None) -> torch.Tensor:
    if generator is None:
        return torch.randn(shape, dtype=dtype)
    return torch.randn(shape, dtype=dtype, generator=generator)


class _SingleAlphaProxy:
    def __init__(self, field: MultiEnvSharedAssignmentField):
        self.alpha = torch.nn.Parameter(field.alpha[0].detach().clone())
        self.assignment_logits = torch.nn.Parameter(field.assignment_logits.detach().clone())
        self.num_faults = field.num_faults
        self.num_prototypes = field.num_prototypes
