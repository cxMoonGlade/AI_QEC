from __future__ import annotations

from collections import defaultdict

import torch

from .fault_graph import FaultGraph, _mask_key
from .likelihood import exact_dem_nll, parity_distribution, resolve_likelihood_backend


def delta_nll_oracle(model_nll: float, oracle_nll: float) -> float:
    return float(model_nll - oracle_nll)


ThresholdKey = tuple[str, str, float, int | None]
ThresholdSummary = dict[str, object]


def shots_to_threshold(
    records: list[dict[str, object]],
    *,
    threshold_epsilon: float,
    seed_policy: str = "mean",
) -> dict[ThresholdKey, ThresholdSummary]:
    """Compute seed-aware shots-to-threshold.

    `seed_policy="mean"` requires the mean delta NLL across seeds at a shot
    budget to pass. `seed_policy="all"` requires every seed at that shot budget
    to pass. The old optimistic behavior was equivalent to letting one passing
    seed decide the threshold for the whole group.
    """

    if seed_policy not in {"mean", "all"}:
        raise ValueError("seed_policy must be 'mean' or 'all'")

    grouped: dict[ThresholdKey, dict[int, list[tuple[int, float]]]] = defaultdict(lambda: defaultdict(list))
    for record in records:
        residual_rank = record.get("residual_rank")
        key = (
            str(record["model"]),
            str(record["teacher_mode"]),
            float(record["epsilon_break"]),
            None if residual_rank is None else int(residual_rank),
        )
        grouped[key][int(record["shots"])].append((int(record["seed"]), float(record["delta_nll_oracle"])))

    result: dict[ThresholdKey, ThresholdSummary] = {}
    for key, by_shots in grouped.items():
        threshold_shots = None
        passing_summary = None
        per_shot_summary = []
        for shots, seed_values in sorted(by_shots.items()):
            unique_seed_values = _latest_value_per_seed(seed_values)
            deltas = [delta for _, delta in unique_seed_values]
            mean_delta = sum(deltas) / len(deltas)
            max_delta = max(deltas)
            min_delta = min(deltas)
            num_seeds = len(deltas)
            num_passing = sum(delta <= threshold_epsilon for delta in deltas)
            passes = mean_delta <= threshold_epsilon if seed_policy == "mean" else num_passing == num_seeds
            summary = {
                "shots": shots,
                "num_seeds": num_seeds,
                "num_passing_seeds": num_passing,
                "mean_delta_nll_oracle": mean_delta,
                "max_delta_nll_oracle": max_delta,
                "min_delta_nll_oracle": min_delta,
                "passes_threshold": passes,
            }
            per_shot_summary.append(summary)
            if passes:
                threshold_shots = shots
                passing_summary = summary
                break
        result[key] = {
            "shots_to_threshold": threshold_shots,
            "threshold_seed_policy": seed_policy,
            "threshold_epsilon": float(threshold_epsilon),
            "passing_summary": passing_summary,
            "per_shot_summary": per_shot_summary,
        }
    return result


def _latest_value_per_seed(seed_values: list[tuple[int, float]]) -> list[tuple[int, float]]:
    by_seed: dict[int, float] = {}
    for seed, delta in seed_values:
        by_seed[seed] = delta
    return sorted(by_seed.items())


def state_bit_matrix(B: int, *, device: torch.device, dtype: torch.dtype) -> torch.Tensor:
    states = torch.arange(1 << B, device=device, dtype=torch.long)
    powers = 2 ** torch.arange(B, device=device, dtype=torch.long)
    return ((states[:, None] & powers[None, :]) > 0).to(dtype=dtype)


def observation_bit_rates_from_distribution(dist: torch.Tensor, B: int) -> torch.Tensor:
    bits = state_bit_matrix(B, device=dist.device, dtype=dist.dtype)
    return dist @ bits


def observation_pair_rates_from_distribution(dist: torch.Tensor, B: int) -> torch.Tensor:
    bits = state_bit_matrix(B, device=dist.device, dtype=dist.dtype)
    weighted = bits * dist[:, None]
    return weighted.T @ bits


def detector_rate_mae(graph: FaultGraph, logits: torch.Tensor, target_logits: torch.Tensor) -> float:
    pred = parity_distribution(graph, logits, backend="auto")
    target = parity_distribution(graph, target_logits.to(device=logits.device, dtype=logits.dtype), backend="auto")
    pred_rates = observation_bit_rates_from_distribution(pred, graph.B)
    target_rates = observation_bit_rates_from_distribution(target, graph.B)
    return float(torch.mean(torch.abs(pred_rates - target_rates)).detach().cpu())


def local_correlation_error(graph: FaultGraph, logits: torch.Tensor, target_logits: torch.Tensor) -> float:
    pred = parity_distribution(graph, logits, backend="auto")
    target = parity_distribution(graph, target_logits.to(device=logits.device, dtype=logits.dtype), backend="auto")
    pred_pairs = observation_pair_rates_from_distribution(pred, graph.B)
    target_pairs = observation_pair_rates_from_distribution(target, graph.B)
    return float(torch.mean(torch.abs(pred_pairs - target_pairs)).detach().cpu())


def compression_ratio(local_parameter_count: int, parameter_count: int) -> float:
    if parameter_count == 0:
        return float("inf")
    return float(local_parameter_count / parameter_count)


def d_q_dem_distance(graph: FaultGraph, learned_logits: torch.Tensor, teacher_logits: torch.Tensor) -> float:
    """DEM quotient distance over only A-preserving fault permutations.

    With no observation-bit relabeling, A-preserving permutations can only permute
    columns with identical parity masks. Canonicalized graphs usually reduce this
    metric to ordinary RMSE, but this implementation also handles noncanonical
    graph-like inputs used by tests.
    """

    learned = learned_logits.detach().to(device="cpu", dtype=torch.float64)
    teacher = teacher_logits.detach().to(device="cpu", dtype=torch.float64)
    if learned.numel() != graph.A.shape[1] or teacher.numel() != graph.A.shape[1]:
        raise ValueError("logits must have one entry per graph fault")

    groups: dict[tuple[int, ...], list[int]] = defaultdict(list)
    for col in range(graph.A.shape[1]):
        groups[_mask_key(graph.A[:, col])].append(col)

    squared_error = torch.tensor(0.0, dtype=torch.float64)
    for indices in groups.values():
        idx = torch.tensor(indices, dtype=torch.long)
        learned_group = torch.sort(learned[idx]).values
        teacher_group = torch.sort(teacher[idx]).values
        squared_error = squared_error + torch.sum((learned_group - teacher_group) ** 2)
    return float(torch.sqrt(squared_error / max(1, graph.A.shape[1])).item())


def evaluate_model(
    graph: FaultGraph,
    logits: torch.Tensor,
    teacher_logits: torch.Tensor,
    heldout_observations: torch.Tensor,
    *,
    aggregate_unique: bool = True,
    backend: str = "auto",
) -> dict[str, float]:
    resolved_backend = resolve_likelihood_backend(logits, backend)
    model_nll = exact_dem_nll(graph, logits, heldout_observations, aggregate_unique=aggregate_unique, backend=backend)
    oracle_nll = exact_dem_nll(
        graph,
        teacher_logits.to(device=logits.device, dtype=logits.dtype),
        heldout_observations,
        aggregate_unique=aggregate_unique,
        backend=backend,
    )
    return {
        "requested_likelihood_backend": backend,
        "resolved_likelihood_backend": resolved_backend,
        "heldout_exact_nll": float(model_nll.detach().cpu()),
        "oracle_exact_nll": float(oracle_nll.detach().cpu()),
        "delta_nll_oracle": delta_nll_oracle(float(model_nll.detach().cpu()), float(oracle_nll.detach().cpu())),
        "detector_rate_mae": detector_rate_mae(graph, logits, teacher_logits),
        "local_correlation_error": local_correlation_error(graph, logits, teacher_logits),
        "d_q_dem": d_q_dem_distance(graph, logits, teacher_logits),
    }
