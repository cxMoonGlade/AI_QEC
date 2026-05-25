from __future__ import annotations

import functools
import os
from pathlib import Path
import tempfile

import torch

from .fault_graph import FaultGraph, mask_states_from_matrix

LikelihoodBackend = str


def observation_bits_to_states(observations: torch.Tensor, *, B: int) -> torch.Tensor:
    obs = torch.as_tensor(observations, dtype=torch.bool)
    if obs.ndim != 2 or obs.shape[1] != B:
        raise ValueError(f"observations must have shape [N, {B}]")
    if B >= 63:
        raise ValueError("exact state indexing currently requires B < 63")
    powers = (2 ** torch.arange(B, dtype=torch.long, device=obs.device)).view(1, B)
    return (obs.to(torch.long) * powers).sum(dim=1)


def resolve_likelihood_backend(logits: torch.Tensor, backend: LikelihoodBackend = "auto") -> str:
    """Resolve `auto` to the concrete likelihood backend used for this tensor."""

    if backend not in {"auto", "pytorch", "cuda_extension"}:
        raise ValueError("backend must be 'auto', 'pytorch', or 'cuda_extension'")
    if backend != "auto":
        return backend
    if not logits.is_cuda:
        return "pytorch"
    try:
        _load_cuda_extension()
    except Exception:
        return "pytorch"
    return "cuda_extension"


def parity_distribution_from_mask_states(
    logits: torch.Tensor,
    mask_states: torch.Tensor,
    *,
    num_bits: int,
    backend: LikelihoodBackend = "auto",
) -> torch.Tensor:
    """Exact parity-state distribution for packed fault masks."""

    if logits.ndim != 1:
        raise ValueError("logits must be rank-1")
    if mask_states.ndim != 1 or mask_states.numel() != logits.numel():
        raise ValueError("mask_states must have one packed mask per logit")
    if num_bits >= 63:
        raise ValueError("exact state indexing currently requires num_bits < 63")

    concrete_backend = resolve_likelihood_backend(logits, backend)
    if concrete_backend == "cuda_extension":
        return _parity_distribution_cuda_extension_from_masks(logits, mask_states, num_bits)

    device = logits.device
    dtype = logits.dtype
    state_count = 1 << int(num_bits)
    states = torch.arange(state_count, device=device, dtype=torch.long)
    q = torch.zeros(state_count, device=device, dtype=dtype)
    q[0] = 1
    probs = torch.sigmoid(logits)
    masks = mask_states.to(device=device, dtype=torch.long)
    for prob, mask in zip(probs, masks):
        xor_index = states ^ mask
        q = (1 - prob) * q + prob * q[xor_index]
    return q


def parity_distribution(
    graph: FaultGraph,
    logits: torch.Tensor,
    *,
    backend: LikelihoodBackend = "auto",
) -> torch.Tensor:
    """Exact distribution q_M over DEM parity states."""

    if logits.ndim != 1 or logits.numel() != graph.M:
        raise ValueError(f"logits must have shape [{graph.M}]")
    return parity_distribution_from_mask_states(
        logits,
        graph.mask_states,
        num_bits=graph.B,
        backend=backend,
    )


def exact_dem_nll(
    graph: FaultGraph,
    logits: torch.Tensor,
    observations: torch.Tensor,
    *,
    aggregate_unique: bool = True,
    backend: LikelihoodBackend = "auto",
) -> torch.Tensor:
    """Exact mean NLL for observations under the DEM parity-map likelihood."""

    dist = parity_distribution(graph, logits, backend=backend)
    states = observation_bits_to_states(observations, B=graph.B).to(device=logits.device)
    if aggregate_unique:
        unique_states, counts = torch.unique(states, sorted=False, return_counts=True)
        probs = dist[unique_states].clamp_min(torch.finfo(dist.dtype).tiny)
        return -(counts.to(dtype=dist.dtype) * torch.log(probs)).sum() / counts.sum()
    probs = dist[states].clamp_min(torch.finfo(dist.dtype).tiny)
    return -torch.log(probs).mean()


def exact_detector_dem_nll(
    graph: FaultGraph,
    logits: torch.Tensor,
    observations: torch.Tensor,
    *,
    aggregate_unique: bool = True,
    backend: LikelihoodBackend = "auto",
) -> torch.Tensor:
    """Exact mean NLL for detector syndromes only, matching DMLE-QEC training."""

    if logits.ndim != 1 or logits.numel() != graph.M:
        raise ValueError(f"logits must have shape [{graph.M}]")
    detector_observations = torch.as_tensor(observations, dtype=torch.bool)[:, : graph.num_detectors]
    detector_mask_states = mask_states_from_matrix(graph.A[: graph.num_detectors])
    dist = parity_distribution_from_mask_states(
        logits,
        detector_mask_states,
        num_bits=graph.num_detectors,
        backend=backend,
    )
    states = observation_bits_to_states(detector_observations, B=graph.num_detectors).to(device=logits.device)
    if aggregate_unique:
        unique_states, counts = torch.unique(states, sorted=False, return_counts=True)
        probs = dist[unique_states].clamp_min(torch.finfo(dist.dtype).tiny)
        return -(counts.to(dtype=dist.dtype) * torch.log(probs)).sum() / counts.sum()
    probs = dist[states].clamp_min(torch.finfo(dist.dtype).tiny)
    return -torch.log(probs).mean()


def exact_observation_nll_from_states(
    graph: FaultGraph,
    logits: torch.Tensor,
    states: torch.Tensor,
    counts: torch.Tensor,
    *,
    backend: LikelihoodBackend = "auto",
) -> torch.Tensor:
    dist = parity_distribution(graph, logits, backend=backend)
    states = states.to(device=logits.device, dtype=torch.long)
    counts = counts.to(device=logits.device, dtype=dist.dtype)
    probs = dist[states].clamp_min(torch.finfo(dist.dtype).tiny)
    return -(counts * torch.log(probs)).sum() / counts.sum()


def aggregate_observations(observations: torch.Tensor, *, B: int) -> tuple[torch.Tensor, torch.Tensor]:
    states = observation_bits_to_states(observations, B=B)
    unique_states, counts = torch.unique(states, sorted=True, return_counts=True)
    return unique_states, counts


@functools.lru_cache(maxsize=1)
def _load_cuda_extension():
    from torch.utils.cpp_extension import load

    cuda_dir = Path(__file__).resolve().parent / "cuda"
    build_root = Path(os.environ.get("TORCH_EXTENSIONS_DIR", Path(tempfile.gettempdir()) / "torch_extensions_scope_static"))
    build_dir = build_root / "scope_static_dem_likelihood_cuda"
    build_dir.mkdir(parents=True, exist_ok=True)
    return load(
        name="scope_static_dem_likelihood_cuda",
        sources=[
            str(cuda_dir / "dem_likelihood.cpp"),
            str(cuda_dir / "dem_likelihood_kernel.cu"),
        ],
        build_directory=str(build_dir),
        with_cuda=True,
        extra_cflags=["-O3"],
        extra_cuda_cflags=["-O3"],
        verbose=False,
    )


class _DemParityDistributionCuda(torch.autograd.Function):
    @staticmethod
    def forward(ctx, logits: torch.Tensor, masks: torch.Tensor, num_bits: int) -> torch.Tensor:
        extension = _load_cuda_extension()
        dist, history, probabilities = extension.dem_parity_distribution_forward_with_history(
            logits.contiguous(),
            masks.contiguous(),
            int(num_bits),
        )
        ctx.save_for_backward(history, probabilities, masks)
        ctx.num_bits = int(num_bits)
        return dist

    @staticmethod
    def backward(ctx, grad_output: torch.Tensor) -> tuple[torch.Tensor, None, None]:
        history, probabilities, masks = ctx.saved_tensors
        extension = _load_cuda_extension()
        grad_logits = extension.dem_parity_distribution_backward(
            grad_output.contiguous(),
            history,
            probabilities,
            masks,
            ctx.num_bits,
        )
        return grad_logits, None, None


def _parity_distribution_cuda_extension_from_masks(
    logits: torch.Tensor,
    mask_states: torch.Tensor,
    num_bits: int,
) -> torch.Tensor:
    if not logits.is_cuda:
        raise ValueError("cuda_extension backend requires CUDA logits")
    try:
        extension = _load_cuda_extension()
    except Exception as exc:  # pragma: no cover - depends on local build tooling
        raise RuntimeError("failed to load C++/CUDA DEM likelihood extension") from exc
    masks = mask_states.to(device=logits.device, dtype=torch.long)
    if torch.is_grad_enabled() and logits.requires_grad:
        return _DemParityDistributionCuda.apply(logits.contiguous(), masks.contiguous(), int(num_bits))
    return extension.dem_parity_distribution(logits.contiguous(), masks.contiguous(), int(num_bits))
