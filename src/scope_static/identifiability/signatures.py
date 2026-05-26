from __future__ import annotations

import torch

from scope_static.fault_graph import FaultGraph


def detector_incidence(graph: FaultGraph) -> torch.Tensor:
    """Return H[j, d] = 1 iff effective DEM fault j touches detector d."""

    if graph.num_detectors <= 0:
        return torch.zeros((graph.M, 0), dtype=torch.float64)
    return graph.A[: graph.num_detectors, :].T.to(dtype=torch.float64, device="cpu")


def structural_signature(graph: FaultGraph) -> torch.Tensor:
    """Visible fault-support/geometry signature that does not use orbit labels."""

    dense = graph.A.to(device="cpu", dtype=torch.float64)
    detector_part = dense[: graph.num_detectors, :]
    logical_part = dense[graph.num_detectors :, :]
    total_weight = dense.sum(dim=0)
    detector_weight = detector_part.sum(dim=0)
    logical_weight = logical_part.sum(dim=0) if logical_part.numel() else torch.zeros(graph.M, dtype=torch.float64)
    features = [
        total_weight,
        detector_weight,
        logical_weight,
        total_weight / max(1, graph.B),
        detector_weight / max(1, graph.num_detectors),
        logical_weight / max(1, graph.num_observables),
    ]

    if graph.detector_coordinates is not None and graph.num_detectors > 0:
        coords = graph.detector_coordinates.to(device="cpu", dtype=torch.float64)
        denom = detector_weight.clamp_min(1.0)
        for coord_dim in range(coords.shape[1]):
            values = coords[:, coord_dim].unsqueeze(1)
            touched = detector_part * values
            mean_coord = touched.sum(dim=0) / denom
            present = detector_part > 0
            max_coord = torch.where(present, values, torch.full_like(values, float("-inf"))).max(dim=0).values
            min_coord = torch.where(present, values, torch.full_like(values, float("inf"))).min(dim=0).values
            span = torch.where(detector_weight > 0, max_coord - min_coord, torch.zeros_like(mean_coord))
            mean_coord = torch.where(detector_weight > 0, mean_coord, torch.zeros_like(mean_coord))
            features.extend([mean_coord, span])

    index = torch.arange(graph.M, dtype=torch.float64)
    features.append(index / max(1, graph.M - 1))
    return _finite_2d(torch.stack(features, dim=1))


def local_logit_signature(logits: torch.Tensor) -> torch.Tensor:
    """Fault-level signature from a visible local logit fit."""

    lam = torch.as_tensor(logits, dtype=torch.float64, device="cpu").flatten()
    if lam.ndim != 1:
        raise ValueError("logits must be a rank-1 fault-logit vector")
    prob = torch.sigmoid(lam)
    centered = lam - lam.mean() if lam.numel() else lam
    absolute = torch.abs(centered)
    return _finite_2d(torch.stack([lam, prob, centered, absolute], dim=1))


def moment_spectral_signature(
    graph: FaultGraph,
    observations: torch.Tensor,
    *,
    spectral_rank: int = 3,
) -> torch.Tensor:
    """Fault-level visible moment/PCA signature from detector/logical shots."""

    if int(spectral_rank) < 0:
        raise ValueError("spectral_rank must be non-negative")
    H = detector_incidence(graph)
    mu, covariance, rho = observation_moments(
        observations,
        num_detectors=graph.num_detectors,
        num_observables=graph.num_observables,
    )
    logical_weight = graph.A[graph.num_detectors :, :].to(dtype=torch.float64, device="cpu").sum(dim=0)
    rows: list[torch.Tensor] = []
    for fault in range(graph.M):
        support = torch.nonzero(H[fault] > 0, as_tuple=False).flatten()
        if support.numel() == 0:
            moment = torch.zeros((5,), dtype=torch.float64)
        else:
            mu_support = mu[support]
            cov_support = covariance.index_select(0, support).index_select(1, support)
            rho_support = rho[support]
            moment = torch.stack(
                [
                    mu_support.mean(),
                    mu_support.std(unbiased=False),
                    cov_support.mean(),
                    cov_support.max(),
                    rho_support.mean(),
                ]
            )
        rows.append(
            torch.cat(
                [
                    moment,
                    torch.tensor(
                        [float(support.numel()), float(logical_weight[fault].item())],
                        dtype=torch.float64,
                    ),
                ]
            )
        )
    moments = torch.stack(rows, dim=0) if rows else torch.empty((0, 7), dtype=torch.float64)
    spectral = _spectral_projection(H, covariance, spectral_rank=int(spectral_rank))
    return _finite_2d(torch.cat([moments, spectral], dim=1))


def combined_signature(*signatures: torch.Tensor) -> torch.Tensor:
    if not signatures:
        raise ValueError("at least one signature matrix is required")
    matrices = [_finite_2d(signature) for signature in signatures]
    num_faults = matrices[0].shape[0]
    if any(matrix.shape[0] != num_faults for matrix in matrices):
        raise ValueError("signature matrices must agree on M")
    return _finite_2d(torch.cat(matrices, dim=1))


def observation_moments(
    observations: torch.Tensor,
    *,
    num_detectors: int,
    num_observables: int,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    samples = torch.as_tensor(observations, dtype=torch.float64, device="cpu")
    if samples.ndim != 2:
        raise ValueError("observations must have shape [shots, B]")
    if samples.shape[1] < int(num_detectors) + int(num_observables):
        raise ValueError("observations have fewer bits than requested")
    detector_samples = samples[:, : int(num_detectors)]
    shots = int(detector_samples.shape[0])
    if shots == 0:
        mu = torch.zeros((int(num_detectors),), dtype=torch.float64)
        covariance = torch.zeros((int(num_detectors), int(num_detectors)), dtype=torch.float64)
        rho = torch.zeros((int(num_detectors),), dtype=torch.float64)
        return mu, covariance, rho

    mu = detector_samples.mean(dim=0)
    centered = detector_samples - mu.unsqueeze(0)
    denom = max(1, shots - 1)
    covariance = centered.T @ centered / denom
    if int(num_observables) <= 0:
        rho = torch.zeros((int(num_detectors),), dtype=torch.float64)
    else:
        logical_bits = samples[:, int(num_detectors) : int(num_detectors) + int(num_observables)]
        logical_signal = logical_bits.mean(dim=1)
        logical_centered = logical_signal - logical_signal.mean()
        rho = centered.T @ logical_centered / denom
    return _finite_1d(mu), _finite_2d(covariance), _finite_1d(rho)


def _spectral_projection(H: torch.Tensor, covariance: torch.Tensor, *, spectral_rank: int) -> torch.Tensor:
    if spectral_rank == 0:
        return torch.zeros((H.shape[0], 0), dtype=torch.float64)
    if H.shape[1] == 0:
        return torch.zeros((H.shape[0], spectral_rank), dtype=torch.float64)
    try:
        values, vectors = torch.linalg.eigh(covariance)
        order = torch.argsort(values, descending=True)
        q = min(int(spectral_rank), int(vectors.shape[1]))
        basis = vectors[:, order[:q]]
    except RuntimeError:
        basis = torch.zeros((H.shape[1], 0), dtype=torch.float64)
        q = 0
    projected = H @ basis if q else torch.zeros((H.shape[0], 0), dtype=torch.float64)
    norms = projected.norm(dim=1, keepdim=True).clamp_min(1e-12)
    projected = projected / norms if projected.numel() else projected
    if projected.shape[1] < int(spectral_rank):
        pad = torch.zeros((H.shape[0], int(spectral_rank) - projected.shape[1]), dtype=torch.float64)
        projected = torch.cat([projected, pad], dim=1)
    return _finite_2d(projected)


def _finite_1d(values: torch.Tensor) -> torch.Tensor:
    result = torch.as_tensor(values, dtype=torch.float64, device="cpu").flatten()
    return torch.nan_to_num(result, nan=0.0, posinf=0.0, neginf=0.0)


def _finite_2d(values: torch.Tensor) -> torch.Tensor:
    result = torch.as_tensor(values, dtype=torch.float64, device="cpu")
    if result.ndim != 2:
        raise ValueError("signature matrix must have shape [M, F]")
    return torch.nan_to_num(result, nan=0.0, posinf=0.0, neginf=0.0)
