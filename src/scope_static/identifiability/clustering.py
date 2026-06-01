from __future__ import annotations

from dataclasses import dataclass
import math

import torch

from scope_static.numerics import NUMERICAL_ZERO, positive_floor


@dataclass(frozen=True)
class KMeansResult:
    labels: torch.Tensor
    centers: torch.Tensor
    inertia: float
    within_cluster_dispersion: float
    silhouette_like: float
    active_clusters: int
    cluster_masses: list[int]
    cluster_mass_entropy_normalized: float
    observable_selection_score: float
    iterations: int


def standardize_features(features: torch.Tensor) -> torch.Tensor:
    device = features.device if isinstance(features, torch.Tensor) else torch.device("cpu")
    x = torch.as_tensor(features, dtype=torch.float64, device=device)
    if x.ndim != 2:
        raise ValueError("features must have shape [M, F]")
    x = torch.nan_to_num(x, nan=NUMERICAL_ZERO, posinf=NUMERICAL_ZERO, neginf=-NUMERICAL_ZERO)
    if x.numel() == 0:
        return x.clone()
    centered = x - x.mean(dim=0, keepdim=True)
    scale = centered.std(dim=0, keepdim=True, unbiased=False).clamp_min(NUMERICAL_ZERO)
    standardized = centered / scale
    return torch.nan_to_num(standardized, nan=NUMERICAL_ZERO, posinf=NUMERICAL_ZERO, neginf=-NUMERICAL_ZERO)


def deterministic_kmeans(
    features: torch.Tensor,
    num_clusters: int,
    *,
    max_iter: int = 100,
    check_convergence: bool = True,
) -> KMeansResult:
    x = standardize_features(features)
    m = int(x.shape[0])
    k = int(num_clusters)
    if m <= 0:
        raise ValueError("cannot cluster an empty feature matrix")
    if k <= 0:
        raise ValueError("num_clusters must be positive")
    k_eff = min(k, m)

    centers = _farthest_point_initial_centers(x, k_eff)
    labels = torch.zeros((m,), dtype=torch.long, device=x.device)
    iterations = 0
    for step in range(int(max_iter)):
        iterations = step + 1
        distances = torch.cdist(x, centers, p=2)
        next_labels = torch.argmin(distances, dim=1)
        next_centers = _label_means(x, next_labels, k_eff)
        empty = torch.bincount(next_labels, minlength=k_eff) == 0
        if bool(empty.any()):
            farthest = torch.argmax(torch.min(distances, dim=1).values)
            next_centers[empty] = x[int(farthest)]
        if check_convergence and torch.equal(next_labels, labels) and torch.allclose(next_centers, centers):
            centers = next_centers
            labels = next_labels
            break
        centers = next_centers
        labels = next_labels

    if k_eff < k:
        # Preserve the requested K in cluster-mass accounting; labels still only
        # use available data-backed clusters.
        padded_centers = torch.zeros((k, x.shape[1]), dtype=x.dtype, device=x.device)
        padded_centers[:k_eff] = centers
        centers = padded_centers

    return _kmeans_result(x, centers[:k_eff], labels, requested_clusters=k, iterations=iterations)


def random_partition_baseline(
    num_items: int,
    num_clusters: int,
    *,
    seed: int = 0,
    num_trials: int = 16,
) -> list[torch.Tensor]:
    if int(num_items) <= 0:
        raise ValueError("num_items must be positive")
    if int(num_clusters) <= 0:
        raise ValueError("num_clusters must be positive")
    generator = torch.Generator(device="cpu")
    generator.manual_seed(int(seed))
    return [
        torch.randint(int(num_clusters), (int(num_items),), generator=generator, dtype=torch.long)
        for _ in range(int(num_trials))
    ]


def _farthest_point_initial_centers(x: torch.Tensor, k: int) -> torch.Tensor:
    norms = torch.sum(x**2, dim=1)
    first = torch.argmax(norms)
    indices = torch.empty((int(k),), dtype=torch.long, device=x.device)
    indices[0] = first
    pairwise = torch.cdist(x, x, p=2)
    min_distances = pairwise[:, first].clone()
    for center_id in range(1, int(k)):
        min_distances.index_fill_(0, indices[:center_id], -1.0)
        candidate = torch.argmax(min_distances)
        indices[center_id] = candidate
        min_distances = torch.minimum(min_distances, pairwise[:, candidate])
    return x.index_select(0, indices).clone()


def _label_means(x: torch.Tensor, labels: torch.Tensor, k: int) -> torch.Tensor:
    sums = torch.zeros((int(k), x.shape[1]), dtype=x.dtype, device=x.device)
    sums.index_add_(0, labels, x)
    counts = torch.bincount(labels, minlength=int(k)).to(device=x.device, dtype=x.dtype).unsqueeze(1)
    return sums / counts.clamp_min(NUMERICAL_ZERO)


def _kmeans_result(
    x: torch.Tensor,
    centers: torch.Tensor,
    labels: torch.Tensor,
    *,
    requested_clusters: int,
    iterations: int,
) -> KMeansResult:
    distances = torch.cdist(x, centers, p=2)
    row_ids = torch.arange(x.shape[0], device=x.device)
    own_distances = distances[row_ids, labels]
    squared = own_distances**2
    inertia = float(squared.sum().item())
    dispersion = float(squared.mean().item()) if squared.numel() else 0.0
    silhouette = _silhouette_like(distances, labels)
    masses = torch.bincount(labels, minlength=int(requested_clusters)).to(dtype=torch.long)
    active = int((masses > 0).sum().item())
    entropy = _mass_entropy_normalized(masses)
    score = _observable_selection_score(
        finite=bool(torch.isfinite(x).all() and torch.isfinite(centers).all()),
        active_clusters=active,
        requested_clusters=int(requested_clusters),
        dispersion=dispersion,
        silhouette=silhouette,
        mass_entropy=entropy,
    )
    return KMeansResult(
        labels=labels.detach().cpu().to(dtype=torch.long),
        centers=centers.detach().cpu(),
        inertia=inertia,
        within_cluster_dispersion=dispersion,
        silhouette_like=silhouette,
        active_clusters=active,
        cluster_masses=[int(value) for value in masses.tolist()],
        cluster_mass_entropy_normalized=entropy,
        observable_selection_score=score,
        iterations=int(iterations),
    )


def _silhouette_like(distances: torch.Tensor, labels: torch.Tensor) -> float:
    if distances.shape[1] <= 1:
        return 0.0
    row_ids = torch.arange(distances.shape[0], device=distances.device)
    labels = labels.to(device=distances.device, dtype=torch.long)
    own = distances[row_ids, labels]
    masked = distances.clone()
    masked[row_ids, labels] = float("inf")
    other = torch.min(masked, dim=1).values
    denom = torch.maximum(own, other).clamp_min(NUMERICAL_ZERO)
    score = (other - own) / denom
    finite = torch.isfinite(score)
    return float(score[finite].mean().item()) if bool(finite.any()) else 0.0


def _mass_entropy_normalized(masses: torch.Tensor) -> float:
    total = float(masses.sum().item())
    if total <= 0.0 or masses.numel() <= 1:
        return 0.0
    probs = masses.to(dtype=torch.float64) / total
    positive = probs > 0
    entropy = -torch.sum(probs[positive] * torch.log(probs[positive]))
    return float((entropy / math.log(int(masses.numel()))).item())


def _observable_selection_score(
    *,
    finite: bool,
    active_clusters: int,
    requested_clusters: int,
    dispersion: float,
    silhouette: float,
    mass_entropy: float,
) -> float:
    if not finite:
        return float("-inf")
    active_fraction = active_clusters / max(1, requested_clusters)
    compactness = -math.log1p(positive_floor(float(dispersion)))
    return float(silhouette + mass_entropy + active_fraction + compactness)
