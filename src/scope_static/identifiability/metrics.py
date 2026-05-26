from __future__ import annotations

from collections import defaultdict

import torch

from scope_static.metrics import adjusted_rand_index, normalized_mutual_info


def contingency_table(
    labels: torch.Tensor | list[int] | tuple[int, ...],
    hidden_labels: torch.Tensor | list[int] | tuple[int, ...],
) -> list[list[int]]:
    left = torch.as_tensor(labels, dtype=torch.long, device="cpu").flatten()
    right = torch.as_tensor(hidden_labels, dtype=torch.long, device="cpu").flatten()
    if left.numel() != right.numel():
        raise ValueError("labels and hidden_labels must have the same length")
    left_values = sorted({int(value) for value in left.tolist()})
    right_values = sorted({int(value) for value in right.tolist()})
    left_index = {value: idx for idx, value in enumerate(left_values)}
    right_index = {value: idx for idx, value in enumerate(right_values)}
    table = [[0 for _ in right_values] for _ in left_values]
    for a, b in zip(left.tolist(), right.tolist()):
        table[left_index[int(a)]][right_index[int(b)]] += 1
    return table


def active_cluster_stats(labels: torch.Tensor | list[int] | tuple[int, ...], *, num_clusters: int) -> dict[str, object]:
    values = torch.as_tensor(labels, dtype=torch.long, device="cpu").flatten()
    masses = torch.bincount(values, minlength=int(num_clusters)).to(dtype=torch.long)
    active = masses > 0
    return {
        "active_clusters": int(active.sum().item()),
        "cluster_masses": [int(value) for value in masses.tolist()],
        "dead_clusters": [idx for idx, value in enumerate(active.tolist()) if not bool(value)],
        "num_dead_clusters": int((~active).sum().item()),
    }


def evaluate_partition(
    labels: torch.Tensor | list[int] | tuple[int, ...],
    hidden_labels: torch.Tensor | list[int] | tuple[int, ...],
    *,
    num_clusters: int,
    random_baseline: dict[str, float] | None = None,
) -> dict[str, object]:
    labels_t = torch.as_tensor(labels, dtype=torch.long, device="cpu").flatten()
    hidden_t = torch.as_tensor(hidden_labels, dtype=torch.long, device="cpu").flatten()
    if labels_t.numel() != hidden_t.numel():
        raise ValueError("labels and hidden_labels must have the same length")
    stats = active_cluster_stats(labels_t, num_clusters=int(num_clusters))
    ari = adjusted_rand_index(labels_t, hidden_t)
    nmi = normalized_mutual_info(labels_t, hidden_t)
    baseline = dict(random_baseline or {})
    return {
        "ari": float(ari),
        "nmi": float(nmi),
        "ari_evaluator_only": True,
        "nmi_evaluator_only": True,
        "ari_nmi_used_for_selection": False,
        "contingency_table": contingency_table(labels_t, hidden_t),
        **stats,
        "passive_identifiability_result": classify_passive_identifiability(
            ari=ari,
            nmi=nmi,
            active_clusters=int(stats["active_clusters"]),
            num_clusters=int(num_clusters),
            random_ari=float(baseline.get("ari_mean", 0.0)),
            random_nmi=float(baseline.get("nmi_mean", 0.0)),
        ),
    }


def random_baseline_summary(
    random_labels: list[torch.Tensor],
    hidden_labels: torch.Tensor | list[int] | tuple[int, ...],
) -> dict[str, float]:
    hidden = torch.as_tensor(hidden_labels, dtype=torch.long, device="cpu").flatten()
    if not random_labels:
        return {"ari_mean": 0.0, "ari_max": 0.0, "nmi_mean": 0.0, "nmi_max": 0.0}
    ari_values = [adjusted_rand_index(labels, hidden) for labels in random_labels]
    nmi_values = [normalized_mutual_info(labels, hidden) for labels in random_labels]
    return {
        "ari_mean": float(sum(ari_values) / len(ari_values)),
        "ari_max": float(max(ari_values)),
        "nmi_mean": float(sum(nmi_values) / len(nmi_values)),
        "nmi_max": float(max(nmi_values)),
    }


def shuffled_omega_control(
    labels: torch.Tensor | list[int] | tuple[int, ...],
    hidden_labels: torch.Tensor | list[int] | tuple[int, ...],
    *,
    seed: int = 0,
) -> dict[str, float]:
    labels_t = torch.as_tensor(labels, dtype=torch.long, device="cpu").flatten()
    hidden = torch.as_tensor(hidden_labels, dtype=torch.long, device="cpu").flatten()
    generator = torch.Generator(device="cpu")
    generator.manual_seed(int(seed))
    shuffled = hidden[torch.randperm(hidden.numel(), generator=generator)]
    return {
        "shuffled_omega_ari": float(adjusted_rand_index(labels_t, shuffled)),
        "shuffled_omega_nmi": float(normalized_mutual_info(labels_t, shuffled)),
    }


def classify_passive_identifiability(
    *,
    ari: float,
    nmi: float,
    active_clusters: int,
    num_clusters: int,
    random_ari: float = 0.0,
    random_nmi: float = 0.0,
) -> str:
    k = int(num_clusters)
    active = int(active_clusters)
    ari = float(ari)
    nmi = float(nmi)
    ari_gap = ari - float(random_ari)
    nmi_gap = nmi - float(random_nmi)
    clearly_above_random = ari_gap >= 0.10 and nmi_gap >= 0.10
    one_metric_above_random = ari_gap >= 0.10 or nmi_gap >= 0.10
    collapsed = active <= max(1, k // 3)

    if ari >= 0.80 and nmi >= 0.80 and active >= max(1, k - 1) and clearly_above_random:
        return "separates"
    if collapsed:
        return "failed"
    if not one_metric_above_random:
        return "failed"
    if max(ari, nmi) >= 0.40 and max(ari, nmi) < 0.80:
        return "weak"
    if active < max(1, k - 1) and one_metric_above_random:
        return "weak"
    if one_metric_above_random and max(ari, nmi) >= 0.40:
        return "weak"
    if ari < 0.40 and nmi < 0.40:
        return "failed"
    return "failed"


def mean_by_key(records: list[dict[str, object]], key: str) -> float | None:
    values = [float(record[key]) for record in records if record.get(key) is not None]
    if not values:
        return None
    return float(sum(values) / len(values))


def group_records(records: list[dict[str, object]], key: str) -> dict[object, list[dict[str, object]]]:
    grouped: dict[object, list[dict[str, object]]] = defaultdict(list)
    for record in records:
        grouped[record.get(key)].append(record)
    return dict(grouped)
