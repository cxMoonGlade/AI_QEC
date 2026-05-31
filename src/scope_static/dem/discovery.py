from __future__ import annotations

from collections import defaultdict
import math

import torch

from .fault_graph import FaultGraph
from .metrics import adjusted_rand_index, normalized_mutual_info


DISCOVERY_MODELS = {"disc_hard", "disc_soft"}


def is_discovery_model(model_name: str) -> bool:
    return str(model_name) in DISCOVERY_MODELS


def matched_known_orbit_model(model_name: str) -> str | None:
    if model_name == "disc_hard":
        return "known_hard_orbit"
    if model_name == "disc_soft":
        return "known_soft_feature_orbit"
    return None


def discovery_parameter_audit(
    graph: FaultGraph,
    *,
    model_name: str,
    prototype_count: int,
    residual_rank: int = 0,
    assignment_parameterization: str = "free",
) -> dict[str, object]:
    k = int(prototype_count)
    r = int(residual_rank) if model_name == "disc_soft" else 0
    p_prototypes = k * (1 + r)
    p_assignment = graph.M * max(0, k - 1)
    p_total = p_prototypes + p_assignment
    return {
        "P_local": int(graph.M),
        "P_known_hard_orbit": int(graph.O),
        "P_known_soft_feature_orbit": int(graph.O * (1 + max(0, int(residual_rank)))),
        "P_discovery_prototypes": int(p_prototypes),
        "P_discovery_assignment": int(p_assignment),
        "P_discovery_total": int(p_total),
        "assignment_parameterization": assignment_parameterization,
        "compressed_claim_allowed": False,
        "discovery_identifiability_probe": True,
    }


def discovery_assignment_metrics(
    assignment_probabilities: torch.Tensor,
    hidden_labels: torch.Tensor | list[int] | tuple[int, ...] | None = None,
    *,
    active_mass_threshold: float = 1.0,
) -> dict[str, object]:
    S = torch.as_tensor(assignment_probabilities, dtype=torch.float64, device="cpu")
    if S.ndim != 2:
        raise ValueError("assignment_probabilities must have shape [M, K]")
    m, k = int(S.shape[0]), int(S.shape[1])
    if k <= 0:
        raise ValueError("assignment_probabilities must include at least one prototype")
    row_sums = S.sum(dim=1)
    hard = torch.argmax(S, dim=1).to(dtype=torch.long)
    hidden = None if hidden_labels is None else torch.as_tensor(hidden_labels, dtype=torch.long, device="cpu").flatten()
    if hidden is not None and hidden.numel() != m:
        raise ValueError("hidden_labels must have one entry per fault")

    positive = S > 0
    entropy_terms = torch.zeros_like(S)
    entropy_terms[positive] = -(S[positive] * S[positive].log())
    entropy = entropy_terms.sum(dim=1)
    entropy_mean = float(entropy.mean().item()) if m else 0.0
    entropy_normalized = 0.0 if k <= 1 else float(entropy_mean / math.log(k))
    masses = S.sum(dim=0)
    active = masses >= float(active_mass_threshold)
    hard_unique = sorted({int(value) for value in hard.tolist()})
    dead = [idx for idx, is_active in enumerate(active.tolist()) if not bool(is_active)]
    collapse = len(hard_unique) <= 1 or int(active.sum().item()) <= 1

    return {
        "ari": None if hidden is None else adjusted_rand_index(hard, hidden),
        "nmi": None if hidden is None else normalized_mutual_info(hard, hidden),
        "partition_recovery_ground_truth_available": hidden is not None,
        "assignment_entropy_mean": entropy_mean,
        "assignment_entropy_normalized": entropy_normalized,
        "assignment_entropy_units": "nats_per_fault",
        "assignment_row_sum_min": float(row_sums.min().item()) if row_sums.numel() else 0.0,
        "assignment_row_sum_max": float(row_sums.max().item()) if row_sums.numel() else 0.0,
        "prototype_masses": [float(value) for value in masses.tolist()],
        "active_prototype_mass_threshold": float(active_mass_threshold),
        "num_active_prototypes": int(active.sum().item()),
        "dead_prototype_ids": dead,
        "num_dead_prototypes": len(dead),
        "assignment_collapse": bool(collapse),
        "hard_assignment_labels": [int(value) for value in hard.tolist()],
        "hard_assignment_num_blocks": len(hard_unique),
        "hard_assignment_partition_for_ari_nmi_only": True,
    }


def field_discovery_metrics(
    field: object,
    hidden_labels: torch.Tensor | list[int] | tuple[int, ...] | None = None,
    *,
    active_mass_threshold: float = 1.0,
) -> dict[str, object]:
    if not hasattr(field, "assignment_probabilities"):
        return _null_assignment_metrics()
    assignment_probabilities = field.assignment_probabilities()
    return discovery_assignment_metrics(
        assignment_probabilities,
        hidden_labels,
        active_mass_threshold=active_mass_threshold,
    )


def _null_assignment_metrics() -> dict[str, object]:
    return {
        "ari": None,
        "nmi": None,
        "partition_recovery_ground_truth_available": False,
        "assignment_entropy_mean": None,
        "assignment_entropy_normalized": None,
        "assignment_entropy_units": "nats_per_fault",
        "assignment_row_sum_min": None,
        "assignment_row_sum_max": None,
        "prototype_masses": [],
        "active_prototype_mass_threshold": None,
        "num_active_prototypes": None,
        "dead_prototype_ids": [],
        "num_dead_prototypes": None,
        "assignment_collapse": None,
        "hard_assignment_labels": [],
        "hard_assignment_num_blocks": None,
        "hard_assignment_partition_for_ari_nmi_only": True,
    }


def selected_heldout_nll(record: dict[str, object]) -> tuple[float | None, str | None]:
    if record.get("heldout_exact_nll") is not None:
        return float(record["heldout_exact_nll"]), "global_exact"
    if record.get("heldout_local_window_nll") is not None:
        return float(record["heldout_local_window_nll"]), "local_window_exact"
    return None, None


def add_known_orbit_deltas(records: list[dict[str, object]]) -> list[dict[str, object]]:
    index: dict[tuple[object, ...], dict[str, object]] = {}
    for record in records:
        key = _known_delta_key(record, model_override=str(record.get("model")))
        index[key] = record

    for record in records:
        oracle_model = matched_known_orbit_model(str(record.get("model")))
        record["known_orbit_oracle_model"] = oracle_model
        record["known_orbit_oracle_available"] = False
        record["known_orbit_oracle_heldout_nll"] = None
        record["delta_nll_known_orbit"] = None
        record["delta_nll_known_orbit_source"] = None
        if oracle_model is None:
            continue
        oracle = index.get(_known_delta_key(record, model_override=oracle_model))
        model_nll, source = selected_heldout_nll(record)
        oracle_nll, oracle_source = selected_heldout_nll(oracle) if oracle is not None else (None, None)
        if model_nll is None or oracle_nll is None or source != oracle_source:
            continue
        record["known_orbit_oracle_available"] = True
        record["known_orbit_oracle_heldout_nll"] = float(oracle_nll)
        record["delta_nll_known_orbit"] = float(model_nll - oracle_nll)
        record["delta_nll_known_orbit_source"] = source
    return records


def build_discovery_important_results(
    records: list[dict[str, object]],
    *,
    threshold_epsilon: float,
) -> dict[str, object]:
    grouped: dict[tuple[object, ...], list[dict[str, object]]] = defaultdict(list)
    for record in records:
        if not is_discovery_model(str(record.get("model"))):
            continue
        key = (
            record.get("scenario"),
            record.get("teacher_mode"),
            record.get("epsilon_break"),
            record.get("shots"),
            record.get("model"),
            record.get("prototype_count_K"),
            record.get("residual_rank"),
        )
        grouped[key].append(record)

    rows = []
    for key in sorted(grouped, key=lambda item: tuple("" if value is None else str(value) for value in item)):
        scenario, teacher_mode, epsilon_break, shots, model, prototype_count, residual_rank = key
        group = grouped[key]
        row = {
            "scenario": scenario,
            "teacher_mode": teacher_mode,
            "epsilon_break": epsilon_break,
            "shots": shots,
            "model": model,
            "prototype_count_K": prototype_count,
            "residual_rank": residual_rank,
            "num_records": len(group),
            "num_seeds": len({int(record["seed"]) for record in group}),
            "num_selected_collapsed": sum(1 for record in group if bool(record.get("assignment_collapse"))),
        }
        for metric in (
            "ari",
            "nmi",
            "assignment_entropy_mean",
            "assignment_entropy_normalized",
            "num_active_prototypes",
            "delta_nll_known_orbit",
            "delta_nll_oracle",
        ):
            row.update(_summary_stats(group, metric))
        mean_delta = row.get("mean_delta_nll_known_orbit")
        row["passes_known_orbit_nll_threshold"] = (
            None if mean_delta is None else bool(float(mean_delta) <= float(threshold_epsilon))
        )
        rows.append(row)
    return {
        "schema": "scope_static_discovery_important_results_v1",
        "success_rule": (
            "Stage 2A success requires both high ARI/NMI against hidden omega(j) "
            "and heldout NLL close to the matched known-orbit oracle; NLL-only "
            "or ARI/NMI-only success is insufficient."
        ),
        "threshold_epsilon": float(threshold_epsilon),
        "discovery_summary": rows,
    }


def _known_delta_key(record: dict[str, object], *, model_override: str) -> tuple[object, ...]:
    return (
        record.get("seed"),
        record.get("teacher_mode"),
        record.get("epsilon_break"),
        record.get("shots"),
        record.get("residual_rank"),
        model_override,
    )


def _summary_stats(records: list[dict[str, object]], metric: str) -> dict[str, object]:
    values = [float(record[metric]) for record in records if record.get(metric) is not None]
    if not values:
        return {
            f"mean_{metric}": None,
            f"std_{metric}": None,
            f"min_{metric}": None,
            f"max_{metric}": None,
        }
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return {
        f"mean_{metric}": mean,
        f"std_{metric}": variance**0.5,
        f"min_{metric}": min(values),
        f"max_{metric}": max(values),
    }
