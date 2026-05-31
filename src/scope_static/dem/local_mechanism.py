from __future__ import annotations

import json
from pathlib import Path

import torch

from .fault_graph import FaultGraph
from ..identifiability import detector_incidence, standardize_features
from ..numerics import NUMERICAL_ZERO, probability_floor


def load_local_logit_matrix(path: str | Path, num_faults: int) -> torch.Tensor:
    """Load fitted local per-fault logits with shape [M, E]."""

    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"local logit source does not exist: {source}")
    if source.suffix == ".npy":
        matrix = torch.as_tensor(__import__("numpy").load(source), dtype=torch.float64)
        return _validate_local_matrix(matrix, num_faults, source)

    data = json.loads(source.read_text())
    local = data.get("local_full_per_fault_per_env", {}).get("train")
    if local is None and isinstance(data.get("records"), list):
        for record in data["records"]:
            if record.get("model") == "local_full_per_fault_per_env":
                local = record.get("env_alpha_train")
                break
    if not isinstance(local, dict) or not local:
        raise ValueError(f"could not find local_full_per_fault_per_env.train in {source}")
    rows = []
    for env in sorted(local, key=lambda value: int(value)):
        values = local[env]
        if not isinstance(values, list) or len(values) != int(num_faults):
            raise ValueError(f"environment {env} in {source} does not contain {num_faults} fault logits")
        rows.append(torch.tensor(values, dtype=torch.float64))
    return _validate_local_matrix(torch.stack(rows, dim=1), num_faults, source)


def local_probability_features(local_logits: torch.Tensor) -> torch.Tensor:
    logits = _finite_2d(local_logits)
    return _finite_2d(torch.cat([logits, torch.sigmoid(logits)], dim=1))


def graph_smooth_features(
    graph: FaultGraph,
    features: torch.Tensor,
    *,
    strength: float = 0.5,
    steps: int = 2,
) -> torch.Tensor:
    """Smooth fault features over the visible DEM detector-support overlap graph."""

    x = standardize_features(features)
    if x.numel() == 0 or int(steps) <= 0:
        return x
    overlap = fault_overlap_matrix(graph, device=x.device)
    degree = overlap.sum(dim=1, keepdim=True)
    transition = torch.where(
        degree > 0,
        overlap / degree.clamp_min(NUMERICAL_ZERO),
        torch.eye(overlap.shape[0], dtype=torch.float64, device=x.device),
    )
    alpha = probability_floor(float(strength))
    out = x
    for _ in range(int(steps)):
        out = (1.0 - alpha) * out + alpha * (transition @ out)
    return _finite_2d(out)


def fault_overlap_matrix(graph: FaultGraph, *, device: str | torch.device | None = None) -> torch.Tensor:
    target = torch.device("cpu") if device is None else torch.device(device)
    H = detector_incidence(graph, device=target)
    if H.numel() == 0:
        return torch.eye(graph.M, dtype=torch.float64, device=target)
    overlap = H @ H.T
    overlap.fill_diagonal_(0.0)
    return torch.nan_to_num(overlap, nan=NUMERICAL_ZERO, posinf=NUMERICAL_ZERO, neginf=-NUMERICAL_ZERO)


def pca_scores(features: torch.Tensor, rank: int) -> torch.Tensor:
    x = standardize_features(features)
    if x.numel() == 0:
        return x
    q = max(1, min(int(rank), min(x.shape)))
    try:
        U, S, _Vh = torch.linalg.svd(x, full_matrices=False)
        return _finite_2d(U[:, :q] * S[:q])
    except RuntimeError:
        return x[:, :q].clone()


def pca_denoised_features(features: torch.Tensor, rank: int) -> torch.Tensor:
    x = standardize_features(features)
    if x.numel() == 0:
        return x
    q = max(1, min(int(rank), min(x.shape)))
    try:
        U, S, Vh = torch.linalg.svd(x, full_matrices=False)
        return _finite_2d((U[:, :q] * S[:q]) @ Vh[:q, :])
    except RuntimeError:
        return x.clone()


def spectral_similarity_embedding(
    features: torch.Tensor,
    num_components: int,
    *,
    rbf_scale: float | None = None,
) -> torch.Tensor:
    x = standardize_features(features)
    if x.numel() == 0:
        return x
    k = max(1, min(int(num_components), x.shape[0]))
    distances = torch.cdist(x, x, p=2)
    positive = distances[distances > 0]
    scale = float(rbf_scale) if rbf_scale is not None else float(torch.median(positive).item()) if positive.numel() else 1.0
    scale = max(scale, NUMERICAL_ZERO)
    affinity = torch.exp(-(distances**2) / (2.0 * scale**2))
    affinity.fill_diagonal_(0.0)
    degree = affinity.sum(dim=1).clamp_min(NUMERICAL_ZERO)
    normalized = affinity / torch.sqrt(torch.outer(degree, degree))
    try:
        values, vectors = torch.linalg.eigh(normalized)
        order = torch.argsort(values, descending=True)
        return _finite_2d(vectors[:, order[:k]])
    except RuntimeError:
        return x[:, :k].clone()


def nmf_codes(
    features: torch.Tensor,
    rank: int,
    *,
    seed: int = 0,
    steps: int = 200,
) -> torch.Tensor:
    x = standardize_features(features)
    if x.numel() == 0:
        return x
    V = x - x.min(dim=0, keepdim=True).values
    V = V + NUMERICAL_ZERO
    m, f = V.shape
    r = max(1, min(int(rank), m, max(1, f)))
    device = V.device
    generator = torch.Generator(device=device)
    generator.manual_seed(int(seed))
    W = torch.rand((m, r), generator=generator, dtype=torch.float64, device=device).clamp_min(NUMERICAL_ZERO)
    H = torch.rand((r, f), generator=generator, dtype=torch.float64, device=device).clamp_min(NUMERICAL_ZERO)
    eps = NUMERICAL_ZERO
    for _ in range(int(steps)):
        H = H * ((W.T @ V) / ((W.T @ W @ H).clamp_min(eps)))
        W = W * ((V @ H.T) / ((W @ H @ H.T).clamp_min(eps)))
        W = W.clamp_min(eps)
        H = H.clamp_min(eps)
    row_sum = W.sum(dim=1, keepdim=True).clamp_min(eps)
    return _finite_2d(W / row_sum)


def overlapping_topk_codes(codes: torch.Tensor, *, topk: int = 2) -> torch.Tensor:
    x = _finite_2d(codes)
    if x.numel() == 0:
        return x
    k = max(1, min(int(topk), x.shape[1]))
    values, indices = torch.topk(x, k=k, dim=1)
    out = torch.zeros_like(x)
    out.scatter_(1, indices, values)
    row_sum = out.sum(dim=1, keepdim=True).clamp_min(NUMERICAL_ZERO)
    return _finite_2d(out / row_sum)


def split_merge_audit(labels: torch.Tensor, hidden_labels: torch.Tensor) -> dict[str, object]:
    pred = torch.as_tensor(labels, dtype=torch.long, device="cpu").flatten()
    hidden = torch.as_tensor(hidden_labels, dtype=torch.long, device="cpu").flatten()
    if pred.numel() != hidden.numel():
        raise ValueError("labels and hidden_labels must have the same length")
    true_values = sorted({int(value) for value in hidden.tolist()})
    pred_values = sorted({int(value) for value in pred.tolist()})
    split_counts = []
    for value in true_values:
        touched = pred[hidden == value]
        split_counts.append(len({int(item) for item in touched.tolist()}))
    merge_counts = []
    purities = []
    for value in pred_values:
        touched = hidden[pred == value]
        counts = torch.bincount(touched, minlength=max(true_values) + 1 if true_values else 0)
        positive = counts[counts > 0]
        merge_counts.append(int(positive.numel()))
        purities.append(float((positive.max() / positive.sum()).item()) if positive.numel() else 0.0)
    return {
        "mean_splits_per_omega": float(sum(split_counts) / len(split_counts)) if split_counts else 0.0,
        "max_splits_per_omega": int(max(split_counts)) if split_counts else 0,
        "mean_merged_omega_per_cluster": float(sum(merge_counts) / len(merge_counts)) if merge_counts else 0.0,
        "max_merged_omega_per_cluster": int(max(merge_counts)) if merge_counts else 0,
        "mean_cluster_purity": float(sum(purities) / len(purities)) if purities else 0.0,
    }


def _validate_local_matrix(matrix: torch.Tensor, num_faults: int, source: Path) -> torch.Tensor:
    result = _finite_2d(matrix)
    if result.shape[0] != int(num_faults):
        raise ValueError(f"{source} has {result.shape[0]} faults, expected {num_faults}")
    if result.shape[1] <= 0:
        raise ValueError(f"{source} has no local-logit environments")
    return result


def _finite_2d(values: torch.Tensor) -> torch.Tensor:
    device = values.device if isinstance(values, torch.Tensor) else torch.device("cpu")
    result = torch.as_tensor(values, dtype=torch.float64, device=device)
    if result.ndim != 2:
        raise ValueError("matrix must have shape [M, F]")
    return torch.nan_to_num(result, nan=NUMERICAL_ZERO, posinf=NUMERICAL_ZERO, neginf=-NUMERICAL_ZERO)
