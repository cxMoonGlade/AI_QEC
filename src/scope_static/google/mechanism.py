from __future__ import annotations

import math
from dataclasses import dataclass

import torch

from scope_static.dem.fault_graph import FaultGraph
from scope_static.identifiability import structural_signature
from scope_static.dem.metrics import adjusted_rand_index, normalized_mutual_info
from scope_static.numerics import NUMERICAL_ZERO


@dataclass(frozen=True)
class PrototypeLogitModel:
    labels: torch.Tensor
    logits: torch.Tensor
    prototype_logits: list[float]
    active_prototypes: int
    dead_prototypes: list[int]


def fit_cluster_mean_logits(labels: torch.Tensor, source_logits: torch.Tensor, *, num_clusters: int) -> PrototypeLogitModel:
    labels = torch.as_tensor(labels, dtype=torch.long, device="cpu").flatten()
    source = torch.as_tensor(source_logits, dtype=torch.float64, device="cpu").flatten()
    if labels.numel() != source.numel():
        raise ValueError("labels and source_logits must have the same length")
    global_mean = source.mean() if source.numel() else torch.tensor(-5.5, dtype=torch.float64)
    prototype_values = torch.full((int(num_clusters),), float(global_mean.item()), dtype=torch.float64)
    for cluster in range(int(num_clusters)):
        idx = labels == cluster
        if bool(idx.any()):
            prototype_values[cluster] = source[idx].mean()
    logits = prototype_values[labels] if labels.numel() else torch.empty((0,), dtype=torch.float64)
    masses = torch.bincount(labels, minlength=int(num_clusters))
    return PrototypeLogitModel(
        labels=labels,
        logits=torch.nan_to_num(logits, nan=NUMERICAL_ZERO, posinf=NUMERICAL_ZERO, neginf=-NUMERICAL_ZERO),
        prototype_logits=[float(value) for value in prototype_values.tolist()],
        active_prototypes=int((masses > 0).sum().item()),
        dead_prototypes=[idx for idx, value in enumerate(masses.tolist()) if int(value) <= 0],
    )


def probability_to_logit(probabilities: torch.Tensor, *, eps: float = NUMERICAL_ZERO) -> torch.Tensor:
    p = torch.as_tensor(probabilities, dtype=torch.float64, device="cpu").clamp(float(eps), 1.0 - float(eps))
    return torch.log(p) - torch.log1p(-p)


def proxy_partitions(graph: FaultGraph, *, basis: str, rounds: int, dem_source: str) -> dict[str, list[int]]:
    """Visible proxy labels for Google data. These are not true hidden omega labels."""

    A = graph.A.to(dtype=torch.float64, device="cpu")
    detector = A[: graph.num_detectors]
    logical = A[graph.num_detectors :]
    detector_weight = detector.sum(dim=0) if detector.numel() else torch.zeros(graph.M, dtype=torch.float64)
    logical_weight = logical.sum(dim=0) if logical.numel() else torch.zeros(graph.M, dtype=torch.float64)
    total_weight = detector_weight + logical_weight
    proxies = {
        "proxy_support_size": _dense_rank_labels(total_weight),
        "proxy_detector_degree": _dense_rank_labels(detector_weight),
        "proxy_boundary_bulk": _boundary_bulk_labels(graph, detector_weight, logical_weight),
        "proxy_space_time_region": _space_time_region_labels(graph),
        "proxy_basis_type": [0 if str(basis).upper() == "X" else 1 for _ in range(graph.M)],
        "proxy_round_layer": _round_layer_labels(graph, rounds=rounds),
        "proxy_decoder_prior_family": [_decoder_prior_label(dem_source) for _ in range(graph.M)],
        "proxy_fault_graph_community": _fault_graph_community_proxy(graph),
    }
    return {name: labels for name, labels in proxies.items() if len(labels) == graph.M}


def proxy_alignment(labels: torch.Tensor, proxies: dict[str, list[int]]) -> dict[str, dict[str, float | str]]:
    result: dict[str, dict[str, float | str]] = {}
    predicted = torch.as_tensor(labels, dtype=torch.long, device="cpu")
    for name, proxy in proxies.items():
        proxy_t = torch.as_tensor(proxy, dtype=torch.long, device="cpu")
        if proxy_t.numel() != predicted.numel():
            continue
        if len(set(int(value) for value in proxy_t.tolist())) <= 1:
            result[name] = {"ari": 0.0, "nmi": 0.0, "proxy_note": "constant_proxy"}
            continue
        result[name] = {
            "ari": float(adjusted_rand_index(predicted, proxy_t)),
            "nmi": float(normalized_mutual_info(predicted, proxy_t)),
            "proxy_note": "proxy_not_ground_truth",
        }
    return result


def pairwise_logit_stability(logit_columns: torch.Tensor, label_columns: list[torch.Tensor]) -> dict[str, object]:
    values = torch.as_tensor(logit_columns, dtype=torch.float64, device="cpu")
    correlations: list[float] = []
    abs_deltas: list[float] = []
    nmis: list[float] = []
    for left in range(values.shape[1]):
        for right in range(left + 1, values.shape[1]):
            correlations.append(_corr(values[:, left], values[:, right]))
            abs_deltas.append(float(torch.mean(torch.abs(values[:, left] - values[:, right])).item()))
            if left < len(label_columns) and right < len(label_columns):
                nmis.append(float(normalized_mutual_info(label_columns[left], label_columns[right])))
    return {
        "num_representations": int(values.shape[1]),
        "mean_pairwise_logit_corr": _mean(correlations),
        "min_pairwise_logit_corr": min(correlations) if correlations else None,
        "mean_pairwise_abs_logit_delta": _mean(abs_deltas),
        "mean_pairwise_cluster_nmi": _mean(nmis),
        "min_pairwise_cluster_nmi": min(nmis) if nmis else None,
    }


def dem_prior_agreement(local_logits: torch.Tensor, prior_logits: torch.Tensor | None, *, label: str) -> dict[str, object]:
    if prior_logits is None:
        return {
            "reference": label,
            "available": False,
            "corr": None,
            "mae": None,
        }
    local = torch.as_tensor(local_logits, dtype=torch.float64, device="cpu").flatten()
    prior = torch.as_tensor(prior_logits, dtype=torch.float64, device="cpu").flatten()
    if local.numel() != prior.numel():
        return {
            "reference": label,
            "available": False,
            "reason": "shape_mismatch",
            "corr": None,
            "mae": None,
        }
    return {
        "reference": label,
        "available": True,
        "corr": _corr(local, prior),
        "mae": float(torch.mean(torch.abs(local - prior)).item()),
    }


def _corr(left: torch.Tensor, right: torch.Tensor) -> float:
    a = torch.as_tensor(left, dtype=torch.float64, device="cpu").flatten()
    b = torch.as_tensor(right, dtype=torch.float64, device="cpu").flatten()
    if a.numel() != b.numel() or a.numel() == 0:
        return 0.0
    a = a - a.mean()
    b = b - b.mean()
    denom = a.norm() * b.norm()
    if float(denom.item()) <= NUMERICAL_ZERO:
        return 0.0
    return float((a @ b / denom).item())


def _mean(values: list[float]) -> float | None:
    return float(sum(values) / len(values)) if values else None


def _dense_rank_labels(values: torch.Tensor) -> list[int]:
    mapping: dict[float, int] = {}
    labels = []
    for value in values.tolist():
        key = float(value)
        labels.append(mapping.setdefault(key, len(mapping)))
    return labels


def _boundary_bulk_labels(graph: FaultGraph, detector_weight: torch.Tensor, logical_weight: torch.Tensor) -> list[int]:
    if graph.detector_coordinates is None or graph.num_detectors == 0:
        return [1 if float(logical_weight[fault]) > 0.0 else 0 for fault in range(graph.M)]
    coords = graph.detector_coordinates.to(dtype=torch.float64, device="cpu")
    min_coord = coords.min(dim=0).values
    max_coord = coords.max(dim=0).values
    spans = (max_coord - min_coord).clamp_min(NUMERICAL_ZERO)
    detector = graph.A[: graph.num_detectors].to(dtype=torch.float64, device="cpu")
    labels = []
    for fault in range(graph.M):
        support = torch.nonzero(detector[:, fault] > 0, as_tuple=False).flatten()
        if support.numel() == 0:
            labels.append(2 if float(logical_weight[fault]) > 0.0 else 0)
            continue
        mean = coords[support].mean(dim=0)
        normalized = (mean - min_coord) / spans
        near_boundary = bool(((normalized < 0.18) | (normalized > 0.82)).any().item())
        if float(logical_weight[fault]) > 0.0:
            labels.append(2)
        else:
            labels.append(1 if near_boundary else 0)
    return labels


def _space_time_region_labels(graph: FaultGraph) -> list[int]:
    if graph.detector_coordinates is None or graph.num_detectors == 0:
        return [0 for _ in range(graph.M)]
    coords = graph.detector_coordinates.to(dtype=torch.float64, device="cpu")
    detector = graph.A[: graph.num_detectors].to(dtype=torch.float64, device="cpu")
    mins = coords.min(dim=0).values
    maxs = coords.max(dim=0).values
    spans = (maxs - mins).clamp_min(NUMERICAL_ZERO)
    labels = []
    mapping: dict[tuple[int, ...], int] = {}
    dims = min(3, coords.shape[1])
    for fault in range(graph.M):
        support = torch.nonzero(detector[:, fault] > 0, as_tuple=False).flatten()
        if support.numel() == 0:
            key = tuple(-1 for _ in range(dims))
        else:
            normalized = (coords[support].mean(dim=0) - mins) / spans
            key = tuple(int(min(2, max(0, math.floor(float(normalized[dim]) * 3.0)))) for dim in range(dims))
        labels.append(mapping.setdefault(key, len(mapping)))
    return labels


def _round_layer_labels(graph: FaultGraph, *, rounds: int) -> list[int]:
    if graph.detector_coordinates is None or graph.detector_coordinates.shape[1] < 3:
        return [0 for _ in range(graph.M)]
    coords = graph.detector_coordinates.to(dtype=torch.float64, device="cpu")
    detector = graph.A[: graph.num_detectors].to(dtype=torch.float64, device="cpu")
    t = coords[:, -1]
    t_min = float(t.min().item())
    t_max = float(t.max().item())
    denom = max(NUMERICAL_ZERO, t_max - t_min)
    bins = max(2, min(4, int(rounds) if int(rounds) > 0 else 4))
    labels = []
    for fault in range(graph.M):
        support = torch.nonzero(detector[:, fault] > 0, as_tuple=False).flatten()
        if support.numel() == 0:
            labels.append(0)
        else:
            value = float((t[support].mean().item() - t_min) / denom)
            labels.append(1 + int(min(bins - 1, max(0, math.floor(value * bins)))))
    return labels


def _decoder_prior_label(dem_source: str) -> int:
    text = str(dem_source).lower()
    if "rl" in text:
        return 1
    if "si1000" in text:
        return 0
    return 2


def _fault_graph_community_proxy(graph: FaultGraph) -> list[int]:
    features = structural_signature(graph)
    if features.numel() == 0:
        return []
    # Keep this proxy intentionally coarse and visible. It is not a discovery
    # target; it only asks whether mechanisms align with graph structure.
    support_size = graph.A.to(dtype=torch.float64, device="cpu").sum(dim=0)
    structural = torch.cat([features[:, : min(3, features.shape[1])], support_size.unsqueeze(1)], dim=1)
    from scope_static.identifiability import deterministic_kmeans

    k = max(2, min(8, graph.M))
    return [int(value) for value in deterministic_kmeans(structural, k).labels.tolist()]
