from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass

import torch

from .baselines import baseline_metadata
from .fault_graph import FaultGraph
from .metrics import compression_audit, compression_ratio, evaluate_model, shots_to_threshold
from .windows import ObservationWindow, WindowPlan


@dataclass(frozen=True)
class EvidenceConfig:
    aggregate_unique: bool = True
    backend: str = "auto"
    global_exact_max_bits: int | None = None


@dataclass(frozen=True)
class EvidenceContext:
    seed: int
    teacher_mode: str
    teacher_residual_rank: int
    epsilon_break: float
    shots: int
    model_name: str
    residual_rank: int


def evaluate_evidence(
    graph: FaultGraph,
    logits: torch.Tensor,
    teacher_logits: torch.Tensor,
    heldout_observations: torch.Tensor,
    *,
    config: EvidenceConfig,
    windows: WindowPlan | list[ObservationWindow] | tuple[ObservationWindow, ...] | None = None,
) -> dict[str, object]:
    return evaluate_model(
        graph,
        logits,
        teacher_logits,
        heldout_observations,
        aggregate_unique=config.aggregate_unique,
        backend=config.backend,
        windows=_coerce_windows(windows),
        global_exact_max_bits=config.global_exact_max_bits,
    )


def build_evidence_record(
    graph: FaultGraph,
    *,
    context: EvidenceContext,
    fit_summary: dict[str, object],
    metrics: dict[str, object],
) -> dict[str, object]:
    feature_audit = graph.residual_feature_audit_dict()
    record = {
        "evidence_record_schema": "scope_static_v1",
        "seed": int(context.seed),
        "teacher_mode": context.teacher_mode,
        "teacher_residual_rank": int(context.teacher_residual_rank),
        "epsilon_break": float(context.epsilon_break),
        "shots": int(context.shots),
        "model": context.model_name,
        "residual_rank": int(context.residual_rank),
        "parameter_count": int(fit_summary["parameter_count"]),
        "compression_ratio_vs_local": compression_ratio(graph.M, int(fit_summary["parameter_count"])),
        "train_initial_nll": fit_summary["train_initial_nll"],
        "train_final_nll": fit_summary["train_final_nll"],
        "train_requested_likelihood_backend": fit_summary["train_requested_likelihood_backend"],
        "train_resolved_likelihood_backend": fit_summary["train_resolved_likelihood_backend"],
        "train_likelihood_adapter": fit_summary["train_likelihood_adapter"],
        "train_likelihood_gpu_batch_available": fit_summary["train_likelihood_gpu_batch_available"],
        "train_observation_mode": fit_summary["train_observation_mode"],
        "train_regularization_weight": fit_summary["train_regularization_weight"],
        "train_likelihood_objective": fit_summary["train_likelihood_objective"],
        "num_train_windows": fit_summary["num_train_windows"],
        "max_train_window_bits": fit_summary["max_train_window_bits"],
        "num_orbits_with_nonzero_centered_feature_rank": feature_audit[
            "num_orbits_with_nonzero_centered_feature_rank"
        ],
        "mean_centered_feature_rank": feature_audit["mean_centered_feature_rank"],
        "max_centered_feature_rank": feature_audit["max_centered_feature_rank"],
        "selected_feature_indices": feature_audit["selected_feature_indices"],
    }
    record.update(compression_audit(graph))
    record.update(baseline_metadata(context.model_name))
    record.update(metrics)
    return record


def threshold_record_list(
    records: list[dict[str, object]],
    *,
    threshold_epsilon: float,
    seed_policy: str,
) -> list[dict[str, object]]:
    thresholds = shots_to_threshold(
        records,
        threshold_epsilon=float(threshold_epsilon),
        seed_policy=seed_policy,
    )
    return [
        {
            "model": key[0],
            "teacher_mode": key[1],
            "epsilon_break": key[2],
            "residual_rank": key[3],
            **value,
        }
        for key, value in thresholds.items()
    ]


def build_important_results(
    records: list[dict[str, object]],
    *,
    graph_audits: list[dict[str, object]],
    window_audits: list[dict[str, object]],
    threshold_records: list[dict[str, object]],
    run_summary: dict[str, object],
) -> dict[str, object]:
    """Build the compact analysis block written into metrics.json."""

    model_rank_summary = _model_rank_summary(records)
    max_shots = max((int(record["shots"]) for record in records), default=None)
    max_shot_rows = [row for row in model_rank_summary if row["shots"] == max_shots]
    return {
        "schema": "scope_static_important_results_v1",
        "run": {
            **run_summary,
            "num_records": len(records),
            "shot_budgets": sorted({int(record["shots"]) for record in records}),
            "seeds": sorted({int(record["seed"]) for record in records}),
            "teacher_cases": _teacher_cases_from_records(records),
            "train_resolved_likelihood_backend_counts": _counter_entries(
                record.get("train_resolved_likelihood_backend") for record in records
            ),
            "train_likelihood_adapter_counts": _counter_entries(
                record.get("train_likelihood_adapter") for record in records
            ),
            "train_likelihood_gpu_batch_available_counts": _counter_entries(
                record.get("train_likelihood_gpu_batch_available") for record in records
            ),
            "delta_nll_oracle_source_counts": _counter_entries(
                record.get("delta_nll_oracle_source") for record in records
            ),
            "exact_global_evaluated_counts": _counter_entries(
                record.get("exact_global_evaluated") for record in records
            ),
        },
        "compression_by_rank": _compression_by_rank(graph_audits),
        "window_summary_by_rank": _window_summary_by_rank(window_audits),
        "best_by_teacher_case_at_max_shots": _best_rows(
            max_shot_rows,
            group_fields=("teacher_mode", "epsilon_break"),
        ),
        "best_by_teacher_case_and_shots": _best_rows(
            model_rank_summary,
            group_fields=("teacher_mode", "epsilon_break", "shots"),
        ),
        "model_rank_summary": model_rank_summary,
        "threshold_summary": _threshold_summary(threshold_records),
    }


def _model_rank_summary(records: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[object, ...], list[dict[str, object]]] = defaultdict(list)
    for record in records:
        key = (
            str(record["teacher_mode"]),
            float(record["epsilon_break"]),
            int(record["shots"]),
            str(record["model"]),
            int(record["residual_rank"]),
        )
        grouped[key].append(record)

    rows = []
    for key in sorted(grouped, key=lambda item: (item[0], item[1], item[2], item[3], item[4])):
        teacher_mode, epsilon_break, shots, model, residual_rank = key
        group = grouped[key]
        first = group[0]
        row = {
            "teacher_mode": teacher_mode,
            "epsilon_break": epsilon_break,
            "shots": shots,
            "model": model,
            "residual_rank": residual_rank,
            "num_records": len(group),
            "num_seeds": len({int(record["seed"]) for record in group}),
            "parameter_count": int(first["parameter_count"]),
            "P_local": int(first["P_local"]),
            "P_hard": int(first["P_hard"]),
            "P_soft": int(first["P_soft"]),
            "hard_compressed": bool(first["hard_compressed"]),
            "soft_compressed": bool(first["soft_compressed"]),
            "rank_condition_satisfied": bool(first["rank_condition_satisfied"]),
            "train_likelihood_objective": first.get("train_likelihood_objective"),
            "train_likelihood_adapter": first.get("train_likelihood_adapter"),
            "train_resolved_likelihood_backend": first.get("train_resolved_likelihood_backend"),
            "delta_nll_oracle_source": first.get("delta_nll_oracle_source"),
            "exact_global_evaluated": first.get("exact_global_evaluated"),
        }
        for metric in (
            "delta_nll_oracle",
            "delta_local_window_nll_oracle",
            "d_q_dem",
            "detector_rate_mae",
            "local_correlation_error",
            "train_final_nll",
        ):
            row.update(_metric_stats(group, metric))
        rows.append(row)
    return rows


def _metric_stats(records: list[dict[str, object]], metric: str) -> dict[str, object]:
    values = [float(record[metric]) for record in records if record.get(metric) is not None]
    prefix = metric
    if not values:
        return {
            f"mean_{prefix}": None,
            f"std_{prefix}": None,
            f"min_{prefix}": None,
            f"max_{prefix}": None,
        }
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return {
        f"mean_{prefix}": mean,
        f"std_{prefix}": variance**0.5,
        f"min_{prefix}": min(values),
        f"max_{prefix}": max(values),
    }


def _best_rows(rows: list[dict[str, object]], *, group_fields: tuple[str, ...]) -> list[dict[str, object]]:
    best: dict[tuple[object, ...], dict[str, object]] = {}
    for row in rows:
        mean_delta = row.get("mean_delta_nll_oracle")
        if mean_delta is None:
            continue
        key = tuple(row[field] for field in group_fields)
        current = best.get(key)
        if current is None or float(mean_delta) < float(current["mean_delta_nll_oracle"]):
            best[key] = row
    return [_best_row_view(best[key]) for key in sorted(best)]


def _best_row_view(row: dict[str, object]) -> dict[str, object]:
    fields = (
        "teacher_mode",
        "epsilon_break",
        "shots",
        "model",
        "residual_rank",
        "num_records",
        "num_seeds",
        "parameter_count",
        "P_local",
        "P_hard",
        "P_soft",
        "hard_compressed",
        "soft_compressed",
        "rank_condition_satisfied",
        "mean_delta_nll_oracle",
        "std_delta_nll_oracle",
        "mean_d_q_dem",
        "mean_detector_rate_mae",
        "mean_local_correlation_error",
        "delta_nll_oracle_source",
        "train_likelihood_adapter",
    )
    return {field: row.get(field) for field in fields if field in row}


def _compression_by_rank(graph_audits: list[dict[str, object]]) -> list[dict[str, object]]:
    fields = (
        "residual_rank",
        "P_local",
        "P_hard",
        "P_soft",
        "hard_compressed",
        "soft_compressed",
        "rank_condition_satisfied",
        "num_orbits_with_nonzero_centered_feature_rank",
        "mean_centered_feature_rank",
        "max_centered_feature_rank",
        "selected_feature_indices",
    )
    return [
        {field: audit.get(field) for field in fields if field in audit}
        for audit in sorted(graph_audits, key=lambda item: int(item.get("residual_rank", 0)))
    ]


def _window_summary_by_rank(window_audits: list[dict[str, object]]) -> list[dict[str, object]]:
    fields = (
        "residual_rank",
        "num_windows",
        "max_window_bits",
        "mean_window_bits",
        "window_kinds",
        "window_plan_builders",
        "window_plan_enabled",
    )
    return [
        {field: audit.get(field) for field in fields if field in audit}
        for audit in sorted(window_audits, key=lambda item: int(item.get("residual_rank", 0)))
    ]


def _threshold_summary(threshold_records: list[dict[str, object]]) -> dict[str, object]:
    return {
        "counts_by_shots_to_threshold": _counter_entries(
            record.get("shots_to_threshold") for record in threshold_records
        ),
        "threshold_table": [
            {
                "model": record["model"],
                "teacher_mode": record["teacher_mode"],
                "epsilon_break": record["epsilon_break"],
                "residual_rank": record["residual_rank"],
                "shots_to_threshold": record["shots_to_threshold"],
                "threshold_seed_policy": record["threshold_seed_policy"],
                "threshold_epsilon": record["threshold_epsilon"],
                "passing_summary": record["passing_summary"],
            }
            for record in threshold_records
        ],
    }


def _counter_entries(values) -> list[dict[str, object]]:
    counts = Counter(values)
    return [
        {"value": value, "count": count}
        for value, count in sorted(counts.items(), key=lambda item: (str(item[0]), item[1]))
    ]


def _teacher_cases_from_records(records: list[dict[str, object]]) -> list[dict[str, object]]:
    cases = {
        (str(record["teacher_mode"]), float(record["epsilon_break"]))
        for record in records
    }
    return [
        {"teacher_mode": teacher_mode, "epsilon_break": epsilon_break}
        for teacher_mode, epsilon_break in sorted(cases)
    ]


def _coerce_windows(
    windows: WindowPlan | list[ObservationWindow] | tuple[ObservationWindow, ...] | None,
) -> list[ObservationWindow]:
    if windows is None:
        return []
    if isinstance(windows, WindowPlan):
        return list(windows.windows)
    return list(windows)
