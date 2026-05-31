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
    observation_bits_to_states,
    parity_distribution,
    resolve_likelihood_backend,
    subset_window_batch_nll_cache,
)
from .likelihoods.local_window_parity import ExactLocalWindowParityLikelihood
from ..numerics import NUMERICAL_ZERO
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


def total_variation_distance(left: torch.Tensor, right: torch.Tensor) -> float:
    left = torch.as_tensor(left, dtype=torch.float64)
    right = torch.as_tensor(right, dtype=torch.float64)
    if left.shape != right.shape:
        raise ValueError("distributions must have matching shapes")
    return float((0.5 * torch.sum(torch.abs(left - right))).detach().cpu())


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


def augment_model_comparison_metrics(
    records: list[dict[str, object]],
    *,
    baseline_model: str = "local",
) -> list[dict[str, object]]:
    """Add effect-size fields comparing each record against a baseline model.

    Real-data excess NLL values are intentionally small because they measure
    nats per local window above the heldout empirical entropy. These derived
    fields make the same object easier to compare without changing the
    likelihood or decision rule.
    """

    grouped: dict[tuple[object, ...], list[dict[str, object]]] = defaultdict(list)
    for record in records:
        grouped[_model_comparison_group_key(record)].append(record)

    for group_records in grouped.values():
        baseline = next((record for record in group_records if record.get("model") == baseline_model), None)
        _augment_group_against_baseline(group_records, baseline, baseline_model=baseline_model)
        _augment_pareto_status(group_records)
    return records


def augment_transfer_comparison_metrics(
    records: list[dict[str, object]],
    *,
    baseline_model: str = "local",
) -> list[dict[str, object]]:
    """Add local-baseline comparison fields to cross-sample transfer records."""

    grouped: dict[tuple[object, ...], list[dict[str, object]]] = defaultdict(list)
    for record in records:
        if not bool(record.get("transfer_evaluated", True)):
            continue
        grouped[_transfer_comparison_group_key(record)].append(record)

    for group_records in grouped.values():
        baseline = next((record for record in group_records if record.get("model") == baseline_model), None)
        _augment_group_against_baseline(
            group_records,
            baseline,
            baseline_model=baseline_model,
            metric_prefix="cross_sample_",
            combined_key="cross_sample_transfer_excess_NLL",
            detector_key="cross_sample_detector_window_excess_NLL",
            logical_key="cross_sample_logical_window_excess_NLL",
            window_count_key="num_combined_windows",
            heldout_count_key=None,
        )
    return records


def _model_comparison_group_key(record: dict[str, object]) -> tuple[object, ...]:
    return (
        record.get("sample_id"),
        record.get("patch_id"),
        record.get("basis"),
        record.get("rounds_label"),
        record.get("dem_source"),
        record.get("preprocessing_mode"),
        record.get("seed"),
    )


def _transfer_comparison_group_key(record: dict[str, object]) -> tuple[object, ...]:
    return (
        record.get("sample_id"),
        record.get("train_sample_id"),
        record.get("preprocessing_mode"),
    )


def _augment_group_against_baseline(
    group_records: list[dict[str, object]],
    baseline: dict[str, object] | None,
    *,
    baseline_model: str,
    metric_prefix: str = "",
    combined_key: str = "heldout_combined_window_excess_nll",
    detector_key: str = "heldout_detector_window_excess_nll",
    logical_key: str = "heldout_logical_window_excess_nll",
    window_count_key: str = "num_combined_windows",
    heldout_count_key: str | None = "train_heldout_split",
) -> None:
    baseline_combined = _finite_float(baseline.get(combined_key)) if baseline is not None else None
    baseline_detector = _finite_float(baseline.get(detector_key)) if baseline is not None else None
    baseline_logical = _finite_float(baseline.get(logical_key)) if baseline is not None else None
    baseline_params = int(baseline["parameter_count"]) if baseline is not None and baseline.get("parameter_count") is not None else None

    for record in group_records:
        combined = _finite_float(record.get(combined_key))
        detector = _finite_float(record.get(detector_key))
        logical = _finite_float(record.get(logical_key))
        num_windows = _safe_int(record.get(window_count_key), default=0)
        heldout_shots = _record_heldout_shots(record, heldout_count_key)

        record[f"{metric_prefix}baseline_model"] = baseline_model
        record[f"{metric_prefix}baseline_available"] = baseline is not None
        record[f"{metric_prefix}excess_mnats_per_window"] = _scale_or_none(combined, 1000.0)
        record[f"{metric_prefix}detector_excess_mnats_per_window"] = _scale_or_none(detector, 1000.0)
        record[f"{metric_prefix}logical_excess_mnats_per_window"] = _scale_or_none(logical, 1000.0)
        record[f"{metric_prefix}comparison_units"] = {
            "excess": "nats_per_window",
            "excess_mnats_per_window": "1000 * excess_nats_per_window",
            "pseudo_delta_nats_per_shot": (
                "delta_excess_nats_per_window * num_combined_windows; "
                "diagnostic pseudo-likelihood scale, not a global exact NLL"
            ),
        }

        if combined is not None and baseline_combined is not None:
            delta = combined - baseline_combined
            record[f"{metric_prefix}excess_delta_vs_baseline"] = float(delta)
            record[f"{metric_prefix}excess_delta_mnats_vs_baseline"] = float(1000.0 * delta)
            record[f"{metric_prefix}excess_ratio_vs_baseline"] = _ratio_or_none(combined, baseline_combined)
            record[f"{metric_prefix}pseudo_delta_nats_per_shot_vs_baseline"] = float(delta * num_windows)
            record[f"{metric_prefix}pseudo_delta_bits_per_shot_vs_baseline"] = float(delta * num_windows / math.log(2))
            if heldout_shots is not None:
                record[f"{metric_prefix}pseudo_delta_nats_on_heldout_vs_baseline"] = float(delta * num_windows * heldout_shots)
        else:
            _set_none_fields(
                record,
                [
                    f"{metric_prefix}excess_delta_vs_baseline",
                    f"{metric_prefix}excess_delta_mnats_vs_baseline",
                    f"{metric_prefix}excess_ratio_vs_baseline",
                    f"{metric_prefix}pseudo_delta_nats_per_shot_vs_baseline",
                    f"{metric_prefix}pseudo_delta_bits_per_shot_vs_baseline",
                    f"{metric_prefix}pseudo_delta_nats_on_heldout_vs_baseline",
                ],
            )

        _set_delta_fields(
            record,
            f"{metric_prefix}detector_excess",
            detector,
            baseline_detector,
        )
        _set_delta_fields(
            record,
            f"{metric_prefix}logical_excess",
            logical,
            baseline_logical,
        )

        parameter_count = _safe_int(record.get("parameter_count"), default=0)
        if baseline_params is not None:
            record[f"{metric_prefix}parameter_delta_vs_baseline"] = int(parameter_count - baseline_params)
            record[f"{metric_prefix}parameter_fraction_of_baseline"] = (
                float(parameter_count / baseline_params) if baseline_params else None
            )
        else:
            record[f"{metric_prefix}parameter_delta_vs_baseline"] = None
            record[f"{metric_prefix}parameter_fraction_of_baseline"] = None


def _augment_pareto_status(group_records: list[dict[str, object]]) -> None:
    comparable = [
        record
        for record in group_records
        if _finite_float(record.get("heldout_combined_window_excess_nll")) is not None
        and record.get("parameter_count") is not None
    ]
    for record in group_records:
        record["combined_excess_parameter_pareto_status"] = "not_comparable"
        record["combined_excess_parameter_dominated_by"] = []
    for record in comparable:
        metric = float(record["heldout_combined_window_excess_nll"])
        params = int(record["parameter_count"])
        dominators = []
        for other in comparable:
            if other is record:
                continue
            other_metric = float(other["heldout_combined_window_excess_nll"])
            other_params = int(other["parameter_count"])
            dominates = (
                other_metric <= metric
                and other_params <= params
                and (other_metric < metric or other_params < params)
            )
            if dominates:
                dominators.append(str(other.get("model")))
        record["combined_excess_parameter_pareto_status"] = "dominated" if dominators else "pareto"
        record["combined_excess_parameter_dominated_by"] = sorted(dominators)


def _record_heldout_shots(record: dict[str, object], heldout_count_key: str | None) -> int | None:
    if heldout_count_key is None:
        return None
    split = record.get(heldout_count_key)
    if isinstance(split, dict) and split.get("heldout_shots") is not None:
        return int(split["heldout_shots"])
    return None


def _set_delta_fields(
    record: dict[str, object],
    prefix: str,
    value: float | None,
    baseline: float | None,
) -> None:
    if value is None or baseline is None:
        record[f"{prefix}_delta_vs_baseline"] = None
        record[f"{prefix}_delta_mnats_vs_baseline"] = None
        record[f"{prefix}_ratio_vs_baseline"] = None
        return
    delta = value - baseline
    record[f"{prefix}_delta_vs_baseline"] = float(delta)
    record[f"{prefix}_delta_mnats_vs_baseline"] = float(1000.0 * delta)
    record[f"{prefix}_ratio_vs_baseline"] = _ratio_or_none(value, baseline)


def _set_none_fields(record: dict[str, object], keys: list[str]) -> None:
    for key in keys:
        record[key] = None


def _scale_or_none(value: float | None, scale: float) -> float | None:
    return None if value is None else float(scale * value)


def _ratio_or_none(value: float, denominator: float) -> float | None:
    if abs(denominator) < NUMERICAL_ZERO:
        return None
    return float(value / denominator)


def _finite_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _safe_int(value: object, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


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
    if abs(denom) < NUMERICAL_ZERO:
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
    if denom < NUMERICAL_ZERO:
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
        model_dist = parity_distribution(graph, logits, backend=backend)
        oracle_dist = parity_distribution(graph, teacher_logits, backend=backend)
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
                "tvd": total_variation_distance(model_dist, oracle_dist),
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
            "tvd": None,
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
        local_audit = local_likelihood.audit_dict(scalar_bytes=logits.element_size())
        model_local_nll = local_likelihood.loss(logits)
        num_windows = int(local_audit["num_windows"])
        max_window_bits = int(local_audit["max_window_bits"])
    else:
        model_local_nll = None
        num_windows = 0
        max_window_bits = 0
    if model_local_nll is not None:
        model_local_nll_value = float(model_local_nll.detach().cpu())
        result.update(
            {
                "heldout_local_window_nll": model_local_nll_value,
                "heldout_combined_window_nll": model_local_nll_value,
                "num_evaluation_windows": num_windows,
                "max_evaluation_window_bits": max_window_bits,
            }
        )
    else:
        model_local_nll_value = None
        result.update(
            {
                "heldout_local_window_nll": None,
                "heldout_combined_window_nll": None,
                "num_evaluation_windows": 0,
                "max_evaluation_window_bits": 0,
            }
        )
    result.update(
        window_evidence_metrics(
            graph,
            logits,
            observations,
            windows=tuple(windows or ()),
            aggregate_unique=aggregate_unique,
            backend=backend,
            window_batch_cache=window_batch_cache,
            combined_nll_override=model_local_nll_value,
        )
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


def window_evidence_metrics(
    graph: FaultGraph,
    logits: torch.Tensor,
    observations: torch.Tensor,
    *,
    windows: list[ObservationWindow] | tuple[ObservationWindow, ...],
    aggregate_unique: bool = True,
    backend: str = "auto",
    window_batch_cache: WindowBatchNLLCache | None = None,
    combined_nll_override: float | None = None,
) -> dict[str, object]:
    """Evidence-oriented local-window metrics with an empirical entropy baseline.

    Raw NLL is a cross-entropy in nats per local window. Empirical entropy is
    the plug-in heldout entropy of the same projected windows. Their difference
    is the empirical excess NLL, an intuitive approximation to local-window KL.
    """

    grouped = _window_evidence_groups(graph, tuple(windows))
    evidence_by_group: dict[str, dict[str, object]] = {}
    result: dict[str, object] = {
        "window_nll_weighting": "equal_window",
        "window_nll_units": "nats_per_window",
        "window_empirical_entropy_source": "heldout_empirical_distribution",
        "window_excess_nll_definition": "model_window_nll_minus_empirical_window_entropy",
    }
    for group_name, group in grouped.items():
        group_windows = group["windows"]
        evidence = _window_group_evidence(
            graph,
            logits,
            observations,
            group_windows,
            aggregate_unique=aggregate_unique,
            backend=backend,
            window_batch_cache=window_batch_cache,
            window_indices=group["indices"],
            model_nll_override=combined_nll_override if group_name == "combined" else None,
        )
        evidence_by_group[group_name] = evidence
        result.update(_flat_window_evidence_fields(group_name, evidence))
    result["window_evidence_groups"] = evidence_by_group
    return result


def logical_specific_window_nll_metrics(
    graph: FaultGraph,
    logits: torch.Tensor,
    observations: torch.Tensor,
    *,
    windows: list[ObservationWindow] | tuple[ObservationWindow, ...],
    aggregate_unique: bool = True,
    backend: str = "auto",
) -> dict[str, object]:
    """Evaluate detector/logical subfamilies of the same local-window objective."""

    evidence = window_evidence_metrics(
        graph,
        logits,
        observations,
        windows=windows,
        aggregate_unique=aggregate_unique,
        backend=backend,
    )
    return {
        key: value
        for key, value in evidence.items()
        if key.endswith("_nll")
        or key.endswith("_empirical_entropy")
        or key.endswith("_excess_nll")
        or key.startswith("num_")
        or key.startswith("mean_")
    }


def _window_group_nll(
    graph: FaultGraph,
    logits: torch.Tensor,
    observations: torch.Tensor,
    windows: list[ObservationWindow],
    *,
    aggregate_unique: bool,
    backend: str,
    window_batch_cache: WindowBatchNLLCache | None = None,
    window_indices: list[int] | None = None,
) -> float | None:
    if not windows:
        return None
    if (
        window_batch_cache is not None
        and window_indices is not None
        and resolve_likelihood_backend(logits, backend) == "cuda_extension"
    ):
        likelihood = ExactLocalWindowParityLikelihood(
            graph=graph,
            observations=observations,
            windows=tuple(windows),
            observation_mode="full",
            aggregate_unique=aggregate_unique,
            requested_backend=backend,
            window_batch_cache=subset_window_batch_nll_cache(window_batch_cache, tuple(window_indices)),
        )
        nll = likelihood.loss(logits)
        return float(nll.detach().cpu())
    likelihood = ExactLocalWindowParityLikelihood.prepare(
        graph,
        observations,
        windows=tuple(windows),
        observation_mode="full",
        aggregate_unique=aggregate_unique,
        backend=backend,
        device=logits.device,
    )
    nll = likelihood.loss(logits)
    return float(nll.detach().cpu())


def empirical_window_entropy(
    observations: torch.Tensor,
    windows: list[ObservationWindow] | tuple[ObservationWindow, ...],
    *,
    window_batch_cache: WindowBatchNLLCache | None = None,
    window_indices: list[int] | tuple[int, ...] | None = None,
) -> float | None:
    """Mean plug-in empirical entropy over local-window observation patterns."""

    if not windows:
        return None
    if window_batch_cache is not None and window_indices is not None:
        return empirical_window_entropy_from_batch_cache(window_batch_cache, window_indices)
    obs = torch.as_tensor(observations, dtype=torch.bool, device="cpu")
    entropies = []
    for window in windows:
        local = obs[:, list(window.bits)]
        states = observation_bits_to_states(local, B=window.size)
        _unique, counts = torch.unique(states, sorted=False, return_counts=True)
        entropies.append(_entropy_from_counts(counts.tolist(), int(counts.sum().item())))
    return float(sum(entropies) / len(entropies))


def empirical_window_entropy_from_batch_cache(
    cache: WindowBatchNLLCache,
    window_indices: list[int] | tuple[int, ...],
) -> float | None:
    """Mean empirical entropy from a prepared local-window state/count cache."""

    indices = [int(index) for index in window_indices]
    if not indices:
        return None
    if min(indices) < 0 or max(indices) >= int(cache.num_windows):
        raise IndexError("window index out of range")
    state_offsets = cache.state_offsets.detach().cpu().to(dtype=torch.long)
    flat_counts = cache.flat_counts.detach().cpu().to(dtype=torch.float64)
    entropies = []
    for index in indices:
        start = int(state_offsets[index].item())
        end = int(state_offsets[index + 1].item())
        counts = flat_counts[start:end]
        total = float(counts.sum().item())
        if total <= 0:
            entropies.append(0.0)
            continue
        probabilities = counts / total
        positive = probabilities[probabilities > 0]
        entropies.append(float(-(positive * torch.log(positive)).sum().item()))
    return float(sum(entropies) / len(entropies))


def _window_evidence_groups(
    graph: FaultGraph,
    windows: tuple[ObservationWindow, ...],
) -> dict[str, dict[str, list[object]]]:
    indexed = list(enumerate(windows))

    def group(predicate) -> dict[str, list[object]]:
        selected = [(index, window) for index, window in indexed if predicate(window)]
        return {
            "indices": [index for index, _window in selected],
            "windows": [window for _index, window in selected],
        }

    return {
        "combined": {
            "indices": [index for index, _window in indexed],
            "windows": list(windows),
        },
        "detector": group(lambda window: all(bit < graph.num_detectors for bit in window.bits)),
        "logical": group(lambda window: any(bit >= graph.num_detectors for bit in window.bits)),
        "logical_single": group(lambda window: window.kind == "logical_single"),
        "logical_fault_support": group(lambda window: window.kind == "logical_fault_support"),
        "logical_detector_pair": group(lambda window: window.kind == "logical_detector_pair"),
    }


def _window_group_evidence(
    graph: FaultGraph,
    logits: torch.Tensor,
    observations: torch.Tensor,
    windows: list[ObservationWindow],
    *,
    aggregate_unique: bool,
    backend: str,
    window_batch_cache: WindowBatchNLLCache | None = None,
    window_indices: list[int] | None = None,
    model_nll_override: float | None = None,
) -> dict[str, object]:
    window_count = len(windows)
    mean_bits = float(sum(window.size for window in windows) / window_count) if window_count else 0.0
    entropy = empirical_window_entropy(
        observations,
        windows,
        window_batch_cache=window_batch_cache,
        window_indices=window_indices,
    )
    nll = (
        model_nll_override
        if model_nll_override is not None
        else _window_group_nll(
            graph,
            logits,
            observations,
            windows,
            aggregate_unique=aggregate_unique,
            backend=backend,
            window_batch_cache=window_batch_cache,
            window_indices=window_indices,
        )
    )
    excess = None if nll is None or entropy is None else float(nll - entropy)
    return {
        "num_windows": int(window_count),
        "mean_window_bits": mean_bits,
        "nll": nll,
        "empirical_entropy": entropy,
        "excess_nll": excess,
        "nll_units": "nats_per_window",
        "weighting": "equal_window",
    }


def _flat_window_evidence_fields(group_name: str, evidence: dict[str, object]) -> dict[str, object]:
    if group_name == "combined":
        return {
            "heldout_local_window_nll": evidence["nll"],
            "heldout_combined_window_nll": evidence["nll"],
            "heldout_local_window_empirical_entropy": evidence["empirical_entropy"],
            "heldout_combined_window_empirical_entropy": evidence["empirical_entropy"],
            "heldout_local_window_excess_nll": evidence["excess_nll"],
            "heldout_combined_window_excess_nll": evidence["excess_nll"],
            "num_combined_windows": evidence["num_windows"],
            "mean_combined_window_bits": evidence["mean_window_bits"],
        }
    if group_name in {"detector", "logical"}:
        return {
            f"heldout_{group_name}_window_nll": evidence["nll"],
            f"heldout_{group_name}_window_empirical_entropy": evidence["empirical_entropy"],
            f"heldout_{group_name}_window_excess_nll": evidence["excess_nll"],
            f"num_{group_name}_windows": evidence["num_windows"],
            f"mean_{group_name}_window_bits": evidence["mean_window_bits"],
        }
    return {
        f"{group_name}_nll": evidence["nll"],
        f"{group_name}_empirical_entropy": evidence["empirical_entropy"],
        f"{group_name}_excess_nll": evidence["excess_nll"],
        f"num_{group_name}_windows": evidence["num_windows"],
        f"mean_{group_name}_window_bits": evidence["mean_window_bits"],
    }


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
