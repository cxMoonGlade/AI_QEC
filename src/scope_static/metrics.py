from __future__ import annotations

from collections import defaultdict
from itertools import combinations
import math

import torch

from .fault_graph import FaultGraph, _mask_key
from .likelihood import (
    WindowBatchNLLCache,
    WindowNLLCache,
    exact_dem_nll,
    local_window_exact_nll,
    parity_distribution,
    resolve_likelihood_backend,
)
from .likelihoods.local_window_parity import ExactLocalWindowParityLikelihood
from .windows import ObservationWindow


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


def exact_observation_bit_rates(
    graph: FaultGraph,
    logits: torch.Tensor,
    bits: list[int] | tuple[int, ...] | None = None,
) -> torch.Tensor:
    """Exact parity-bit rates from sparse supports, without global 2^B DP."""

    selected_bits = tuple(range(graph.B)) if bits is None else tuple(int(bit) for bit in bits)
    probs = torch.sigmoid(logits)
    parity_factors = 1 - 2 * probs
    rates = []
    for bit in selected_bits:
        fault_ids = graph.faults_by_observation_bit[bit]
        if fault_ids:
            idx = torch.tensor(fault_ids, device=logits.device, dtype=torch.long)
            parity_mean = torch.prod(parity_factors[idx])
        else:
            parity_mean = logits.new_tensor(1.0)
        rates.append((1 - parity_mean) / 2)
    return torch.stack(rates) if rates else logits.new_empty((0,))


def local_detector_pairs(graph: FaultGraph) -> list[tuple[int, int]]:
    pairs: set[tuple[int, int]] = set()
    for support in graph.supports_by_fault:
        detector_bits = [bit for bit in support if bit < graph.num_detectors]
        for left, right in combinations(detector_bits, 2):
            pairs.add((min(left, right), max(left, right)))
    return sorted(pairs)


def exact_observation_pair_joint_rates(
    graph: FaultGraph,
    logits: torch.Tensor,
    pairs: list[tuple[int, int]] | tuple[tuple[int, int], ...],
) -> torch.Tensor:
    """Exact P(y_left=1, y_right=1) for selected parity-bit pairs."""

    probs = torch.sigmoid(logits)
    parity_factors = 1 - 2 * probs
    joint_rates = []
    for left, right in pairs:
        left_faults = set(graph.faults_by_observation_bit[int(left)])
        right_faults = set(graph.faults_by_observation_bit[int(right)])
        xor_faults = sorted(left_faults.symmetric_difference(right_faults))
        mean_left = _parity_mean_from_faults(logits, parity_factors, sorted(left_faults))
        mean_right = _parity_mean_from_faults(logits, parity_factors, sorted(right_faults))
        mean_xor = _parity_mean_from_faults(logits, parity_factors, xor_faults)
        joint_rates.append((1 - mean_left - mean_right + mean_xor) / 4)
    return torch.stack(joint_rates) if joint_rates else logits.new_empty((0,))


def _parity_mean_from_faults(logits: torch.Tensor, parity_factors: torch.Tensor, fault_ids: list[int]) -> torch.Tensor:
    if not fault_ids:
        return logits.new_tensor(1.0)
    idx = torch.tensor(fault_ids, device=logits.device, dtype=torch.long)
    return torch.prod(parity_factors[idx])


def detector_rate_mae(graph: FaultGraph, logits: torch.Tensor, target_logits: torch.Tensor) -> float:
    detector_bits = tuple(range(graph.num_detectors))
    pred_rates = exact_observation_bit_rates(graph, logits, detector_bits)
    target_rates = exact_observation_bit_rates(
        graph,
        target_logits.to(device=logits.device, dtype=logits.dtype),
        detector_bits,
    )
    return float(torch.mean(torch.abs(pred_rates - target_rates)).detach().cpu())


def local_correlation_error(graph: FaultGraph, logits: torch.Tensor, target_logits: torch.Tensor) -> float:
    pairs = local_detector_pairs(graph)
    if not pairs:
        return 0.0
    pred_pairs = exact_observation_pair_joint_rates(graph, logits, pairs)
    target_pairs = exact_observation_pair_joint_rates(
        graph,
        target_logits.to(device=logits.device, dtype=logits.dtype),
        pairs,
    )
    return float(torch.mean(torch.abs(pred_pairs - target_pairs)).detach().cpu())


def compression_ratio(local_parameter_count: int, parameter_count: int) -> float:
    if parameter_count == 0:
        return float("inf")
    return float(local_parameter_count / parameter_count)


def compression_audit(graph: FaultGraph) -> dict[str, object]:
    feature_audit = graph.residual_feature_audit_dict()
    p_local = graph.M
    p_hard = graph.O
    p_soft = graph.O * (1 + graph.residual_rank)
    return {
        "P_local": int(p_local),
        "P_hard": int(p_hard),
        "P_soft": int(p_soft),
        "hard_compressed": bool(p_hard < p_local),
        "soft_compressed": bool(p_soft < p_local),
        "rank_condition_satisfied": bool(
            graph.residual_rank > 0 and int(feature_audit["num_orbits_with_nonzero_centered_feature_rank"]) > 0
        ),
    }


def partition_audit(labels: torch.Tensor | list[int] | tuple[int, ...]) -> dict[str, object]:
    """Summarize an orbit/partition assignment over effective DEM faults."""

    values = [int(value) for value in torch.as_tensor(labels, dtype=torch.long).flatten().tolist()]
    counts: dict[int, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    orbit_sizes = sorted(counts.values(), reverse=True)
    m = len(values)
    num_orbits = len(orbit_sizes)
    return {
        "num_orbits": num_orbits,
        "orbit_size_distribution": orbit_sizes,
        "num_singleton_orbits": sum(1 for size in orbit_sizes if size == 1),
        "compression_ratio": float(m / num_orbits) if num_orbits else float("inf"),
    }


def adjusted_rand_index(
    labels_left: torch.Tensor | list[int] | tuple[int, ...],
    labels_right: torch.Tensor | list[int] | tuple[int, ...],
) -> float:
    """Adjusted Rand index for two partitions, without an sklearn dependency."""

    left, right = _coerce_partition_pair(labels_left, labels_right)
    n = len(left)
    if n < 2:
        return 1.0
    contingency: dict[tuple[int, int], int] = {}
    left_counts: dict[int, int] = {}
    right_counts: dict[int, int] = {}
    for a, b in zip(left, right):
        contingency[(a, b)] = contingency.get((a, b), 0) + 1
        left_counts[a] = left_counts.get(a, 0) + 1
        right_counts[b] = right_counts.get(b, 0) + 1
    sum_pairs = sum(_comb2(value) for value in contingency.values())
    left_pairs = sum(_comb2(value) for value in left_counts.values())
    right_pairs = sum(_comb2(value) for value in right_counts.values())
    total_pairs = _comb2(n)
    expected = left_pairs * right_pairs / total_pairs if total_pairs else 0.0
    max_index = 0.5 * (left_pairs + right_pairs)
    denom = max_index - expected
    if abs(denom) < 1e-12:
        return 1.0 if sum_pairs == max_index else 0.0
    return float((sum_pairs - expected) / denom)


def normalized_mutual_info(
    labels_left: torch.Tensor | list[int] | tuple[int, ...],
    labels_right: torch.Tensor | list[int] | tuple[int, ...],
) -> float:
    """sqrt-normalized mutual information for two partitions."""

    left, right = _coerce_partition_pair(labels_left, labels_right)
    n = len(left)
    if n == 0:
        return 1.0
    contingency: dict[tuple[int, int], int] = {}
    left_counts: dict[int, int] = {}
    right_counts: dict[int, int] = {}
    for a, b in zip(left, right):
        contingency[(a, b)] = contingency.get((a, b), 0) + 1
        left_counts[a] = left_counts.get(a, 0) + 1
        right_counts[b] = right_counts.get(b, 0) + 1
    mutual_info = 0.0
    for (a, b), count in contingency.items():
        mutual_info += (count / n) * math.log((count * n) / (left_counts[a] * right_counts[b]))
    h_left = _entropy_from_counts(left_counts.values(), n)
    h_right = _entropy_from_counts(right_counts.values(), n)
    denom = math.sqrt(h_left * h_right)
    if denom < 1e-12:
        return 1.0 if left == right else 0.0
    return float(mutual_info / denom)


def partition_refines(
    finer_labels: torch.Tensor | list[int] | tuple[int, ...],
    coarser_labels: torch.Tensor | list[int] | tuple[int, ...],
) -> bool:
    """Return true when every finer block is contained in one coarser block."""

    finer, coarser = _coerce_partition_pair(finer_labels, coarser_labels)
    mapping: dict[int, int] = {}
    for fine, coarse in zip(finer, coarser):
        if fine in mapping and mapping[fine] != coarse:
            return False
        mapping[fine] = coarse
    return True


def partition_comparison(
    heuristic_labels: torch.Tensor | list[int] | tuple[int, ...],
    schedule_labels: torch.Tensor | list[int] | tuple[int, ...],
) -> dict[str, object]:
    """Compare current FaultGraph heuristic orbits with schedule-derived orbits."""

    heuristic, schedule = _coerce_partition_pair(heuristic_labels, schedule_labels)
    return {
        "fault_graph_heuristic": partition_audit(heuristic),
        "schedule_geometric": partition_audit(schedule),
        "ari_heuristic_schedule": adjusted_rand_index(heuristic, schedule),
        "nmi_heuristic_schedule": normalized_mutual_info(heuristic, schedule),
        "schedule_refines_heuristic": partition_refines(schedule, heuristic),
        "heuristic_refines_schedule": partition_refines(heuristic, schedule),
    }


def _coerce_partition_pair(
    labels_left: torch.Tensor | list[int] | tuple[int, ...],
    labels_right: torch.Tensor | list[int] | tuple[int, ...],
) -> tuple[list[int], list[int]]:
    left = [int(value) for value in torch.as_tensor(labels_left, dtype=torch.long).flatten().tolist()]
    right = [int(value) for value in torch.as_tensor(labels_right, dtype=torch.long).flatten().tolist()]
    if len(left) != len(right):
        raise ValueError("partition labels must have the same length")
    return left, right


def _comb2(value: int) -> int:
    return int(value) * (int(value) - 1) // 2


def _entropy_from_counts(counts: object, n: int) -> float:
    entropy = 0.0
    for count in counts:
        prob = int(count) / n
        if prob > 0:
            entropy -= prob * math.log(prob)
    return entropy


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
    windows: list[ObservationWindow] | tuple[ObservationWindow, ...] | None = None,
    global_exact_max_bits: int | None = None,
) -> dict[str, object]:
    resolved_backend = resolve_likelihood_backend(logits, backend)
    teacher_logits = teacher_logits.to(device=logits.device, dtype=logits.dtype)
    compute_global = global_exact_max_bits is None or graph.B <= int(global_exact_max_bits)
    result = {
        "requested_likelihood_backend": backend,
        "resolved_likelihood_backend": resolved_backend,
        "detector_rate_mae": detector_rate_mae(graph, logits, teacher_logits),
        "local_correlation_error": local_correlation_error(graph, logits, teacher_logits),
        "d_q_dem": d_q_dem_distance(graph, logits, teacher_logits),
    }
    local_delta = None
    if windows:
        model_local_nll = local_window_exact_nll(
            graph,
            logits,
            heldout_observations,
            list(windows),
            aggregate_unique=aggregate_unique,
            backend=backend,
        )
        oracle_local_nll = local_window_exact_nll(
            graph,
            teacher_logits,
            heldout_observations,
            list(windows),
            aggregate_unique=aggregate_unique,
            backend=backend,
        )
        local_delta = delta_nll_oracle(float(model_local_nll.detach().cpu()), float(oracle_local_nll.detach().cpu()))
        result.update(
            {
                "heldout_local_window_nll": float(model_local_nll.detach().cpu()),
                "oracle_local_window_nll": float(oracle_local_nll.detach().cpu()),
                "delta_local_window_nll_oracle": local_delta,
                "num_evaluation_windows": len(windows),
                "max_evaluation_window_bits": max((window.size for window in windows), default=0),
            }
        )
    else:
        result.update(
            {
                "heldout_local_window_nll": None,
                "oracle_local_window_nll": None,
                "delta_local_window_nll_oracle": None,
                "num_evaluation_windows": 0,
                "max_evaluation_window_bits": 0,
            }
        )

    if compute_global:
        model_nll = exact_dem_nll(graph, logits, heldout_observations, aggregate_unique=aggregate_unique, backend=backend)
        oracle_nll = exact_dem_nll(
            graph,
            teacher_logits,
            heldout_observations,
            aggregate_unique=aggregate_unique,
            backend=backend,
        )
        global_delta = delta_nll_oracle(float(model_nll.detach().cpu()), float(oracle_nll.detach().cpu()))
        result.update(
            {
                "exact_global_evaluated": True,
                "heldout_exact_nll": float(model_nll.detach().cpu()),
                "oracle_exact_nll": float(oracle_nll.detach().cpu()),
                "delta_nll_oracle": global_delta,
                "delta_nll_oracle_source": "global_exact",
            }
        )
        return result

    if local_delta is None:
        raise ValueError("global exact NLL was disabled by max bits and no local windows were provided")
    result.update(
        {
            "exact_global_evaluated": False,
            "heldout_exact_nll": None,
            "oracle_exact_nll": None,
            "delta_nll_oracle": local_delta,
            "delta_nll_oracle_source": "local_window_exact",
        }
    )
    return result


def evaluate_real_data_model(
    graph: FaultGraph,
    logits: torch.Tensor,
    heldout_observations: torch.Tensor,
    *,
    aggregate_unique: bool = True,
    backend: str = "auto",
    windows: list[ObservationWindow] | tuple[ObservationWindow, ...] | None = None,
    window_caches: list[WindowNLLCache] | tuple[WindowNLLCache, ...] | None = None,
    window_batch_cache: WindowBatchNLLCache | None = None,
    predicted_observables: torch.Tensor | None = None,
) -> dict[str, object]:
    """Evaluate a fitted DEM logit field against empirical Google observations."""

    resolved_backend = resolve_likelihood_backend(logits, backend)
    observations = torch.as_tensor(heldout_observations, dtype=torch.bool)
    result: dict[str, object] = {
        "requested_likelihood_backend": backend,
        "resolved_likelihood_backend": resolved_backend,
        "exact_global_evaluated": False,
        "heldout_exact_nll": None,
        "oracle_exact_nll": None,
        "delta_nll_oracle": None,
        "delta_nll_oracle_source": "real_data_no_teacher",
    }
    if window_batch_cache is not None or window_caches is not None or windows:
        if window_batch_cache is not None or window_caches is not None:
            local_likelihood = ExactLocalWindowParityLikelihood(
                graph=graph,
                observations=observations,
                observation_mode="full",
                aggregate_unique=aggregate_unique,
                requested_backend=backend,
                windows=tuple(windows or ()),
                window_caches=tuple(window_caches or ()),
                window_batch_cache=window_batch_cache,
            )
        else:
            local_likelihood = ExactLocalWindowParityLikelihood.prepare(
                graph,
                observations,
                windows=tuple(windows or ()),
                observation_mode="full",
                aggregate_unique=aggregate_unique,
                backend=backend,
                device=logits.device,
            )
        local_audit = local_likelihood.audit_dict()
        model_local_nll = local_likelihood.loss(logits)
        num_windows = int(local_audit["num_windows"])
        max_window_bits = int(local_audit["max_window_bits"])
    else:
        model_local_nll = None
        num_windows = 0
        max_window_bits = 0
    if model_local_nll is not None:
        result.update(
            {
                "heldout_local_window_nll": float(model_local_nll.detach().cpu()),
                "num_evaluation_windows": num_windows,
                "max_evaluation_window_bits": max_window_bits,
            }
        )
    else:
        result.update(
            {
                "heldout_local_window_nll": None,
                "num_evaluation_windows": 0,
                "max_evaluation_window_bits": 0,
            }
        )

    result.update(empirical_detector_rate_metrics(graph, logits, observations))
    result.update(empirical_local_correlation_metrics(graph, logits, observations))
    result.update(logical_flip_calibration_metrics(graph, logits, observations))
    if predicted_observables is not None:
        result.update(decoder_prediction_metrics(observations, predicted_observables, graph.num_detectors))
    else:
        result.update(
            {
                "decoder_logical_prediction_available": False,
                "decoder_logical_prediction_error_rate": None,
            }
        )
    return result


def empirical_detector_rate_metrics(
    graph: FaultGraph,
    logits: torch.Tensor,
    observations: torch.Tensor,
) -> dict[str, object]:
    detector_bits = tuple(range(graph.num_detectors))
    if not detector_bits:
        return {"detector_rate_mae": 0.0}
    pred_rates = exact_observation_bit_rates(graph, logits, detector_bits).detach().cpu()
    empirical = observations[:, : graph.num_detectors].to(dtype=pred_rates.dtype).mean(dim=0).cpu()
    return {"detector_rate_mae": float(torch.mean(torch.abs(pred_rates - empirical)).item())}


def empirical_local_correlation_metrics(
    graph: FaultGraph,
    logits: torch.Tensor,
    observations: torch.Tensor,
) -> dict[str, object]:
    pairs = local_detector_pairs(graph)
    if not pairs:
        return {"local_correlation_error": 0.0, "num_local_correlation_pairs": 0}
    pred_pairs = exact_observation_pair_joint_rates(graph, logits, pairs).detach().cpu()
    obs = observations.to(dtype=pred_pairs.dtype, device="cpu")
    empirical = torch.stack([obs[:, left] * obs[:, right] for left, right in pairs]).mean(dim=1)
    return {
        "local_correlation_error": float(torch.mean(torch.abs(pred_pairs - empirical)).item()),
        "num_local_correlation_pairs": len(pairs),
    }


def logical_flip_calibration_metrics(
    graph: FaultGraph,
    logits: torch.Tensor,
    observations: torch.Tensor,
) -> dict[str, object]:
    if graph.num_observables == 0:
        return {
            "logical_flip_rate_calibration": 0.0,
            "logical_flip_rate_predicted": [],
            "logical_flip_rate_empirical": [],
        }
    logical_bits = tuple(range(graph.num_detectors, graph.B))
    pred_rates = exact_observation_bit_rates(graph, logits, logical_bits).detach().cpu()
    empirical = observations[:, graph.num_detectors : graph.B].to(dtype=pred_rates.dtype).mean(dim=0).cpu()
    return {
        "logical_flip_rate_calibration": float(torch.mean(torch.abs(pred_rates - empirical)).item()),
        "logical_flip_rate_predicted": [float(value) for value in pred_rates.tolist()],
        "logical_flip_rate_empirical": [float(value) for value in empirical.tolist()],
    }


def decoder_prediction_metrics(
    observations: torch.Tensor,
    predicted_observables: torch.Tensor,
    num_detectors: int,
) -> dict[str, object]:
    actual = torch.as_tensor(observations, dtype=torch.bool)[:, int(num_detectors) :]
    predicted = torch.as_tensor(predicted_observables, dtype=torch.bool)
    if predicted.shape[0] != actual.shape[0]:
        limit = min(int(predicted.shape[0]), int(actual.shape[0]))
        predicted = predicted[:limit]
        actual = actual[:limit]
    if predicted.ndim == 2 and actual.ndim == 2 and predicted.shape[1] != actual.shape[1]:
        width = min(int(predicted.shape[1]), int(actual.shape[1]))
        predicted = predicted[:, :width]
        actual = actual[:, :width]
    if actual.numel() == 0:
        error_rate = 0.0
    else:
        error_rate = float(torch.logical_xor(predicted, actual).to(dtype=torch.float64).mean().item())
    return {
        "decoder_logical_prediction_available": True,
        "decoder_logical_prediction_error_rate": error_rate,
    }
