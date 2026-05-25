from __future__ import annotations

from dataclasses import dataclass
import functools
import os
from pathlib import Path
import tempfile

import torch

from .fault_graph import FaultGraph
from .windows import ObservationWindow

LikelihoodBackend = str


@dataclass(frozen=True)
class WindowNLLCache:
    window: ObservationWindow
    fault_ids: torch.Tensor
    mask_states: torch.Tensor
    states: torch.Tensor
    counts: torch.Tensor | None
    num_observations: int

    def to(self, device: torch.device | str) -> "WindowNLLCache":
        target = torch.device(device)
        return WindowNLLCache(
            window=self.window,
            fault_ids=self.fault_ids.to(device=target, dtype=torch.long),
            mask_states=self.mask_states.to(device=target, dtype=torch.long),
            states=self.states.to(device=target, dtype=torch.long),
            counts=None if self.counts is None else self.counts.to(device=target, dtype=torch.long),
            num_observations=self.num_observations,
        )


@dataclass(frozen=True)
class WindowBatchNLLCache:
    flat_fault_ids: torch.Tensor
    flat_masks: torch.Tensor
    fault_offsets: torch.Tensor
    flat_states: torch.Tensor
    flat_counts: torch.Tensor
    state_offsets: torch.Tensor
    window_num_bits: torch.Tensor
    max_faults_per_window: int
    max_state_count: int
    num_windows: int

    @classmethod
    def from_window_caches(cls, caches: list[WindowNLLCache] | tuple[WindowNLLCache, ...]) -> "WindowBatchNLLCache":
        if not caches:
            raise ValueError("WindowBatchNLLCache requires at least one window cache")
        flat_fault_ids: list[torch.Tensor] = []
        flat_masks: list[torch.Tensor] = []
        fault_offsets = [0]
        flat_states: list[torch.Tensor] = []
        flat_counts: list[torch.Tensor] = []
        state_offsets = [0]
        window_num_bits = []
        max_faults = 0
        max_state_count = 1
        for cache in caches:
            fault_ids = cache.fault_ids.to(device="cpu", dtype=torch.long)
            masks = cache.mask_states.to(device="cpu", dtype=torch.long)
            states = cache.states.to(device="cpu", dtype=torch.long)
            counts = (
                torch.ones_like(states, dtype=torch.long)
                if cache.counts is None
                else cache.counts.to(device="cpu", dtype=torch.long)
            )
            flat_fault_ids.append(fault_ids)
            flat_masks.append(masks)
            flat_states.append(states)
            flat_counts.append(counts)
            fault_offsets.append(fault_offsets[-1] + int(fault_ids.numel()))
            state_offsets.append(state_offsets[-1] + int(states.numel()))
            window_num_bits.append(int(cache.window.size))
            max_faults = max(max_faults, int(fault_ids.numel()))
            max_state_count = max(max_state_count, 1 << int(cache.window.size))

        return cls(
            flat_fault_ids=_cat_or_empty(flat_fault_ids),
            flat_masks=_cat_or_empty(flat_masks),
            fault_offsets=torch.tensor(fault_offsets, dtype=torch.long),
            flat_states=_cat_or_empty(flat_states),
            flat_counts=_cat_or_empty(flat_counts),
            state_offsets=torch.tensor(state_offsets, dtype=torch.long),
            window_num_bits=torch.tensor(window_num_bits, dtype=torch.long),
            max_faults_per_window=max_faults,
            max_state_count=max_state_count,
            num_windows=len(caches),
        )

    def to(self, device: torch.device | str) -> "WindowBatchNLLCache":
        target = torch.device(device)
        return WindowBatchNLLCache(
            flat_fault_ids=self.flat_fault_ids.to(device=target, dtype=torch.long),
            flat_masks=self.flat_masks.to(device=target, dtype=torch.long),
            fault_offsets=self.fault_offsets.to(device=target, dtype=torch.long),
            flat_states=self.flat_states.to(device=target, dtype=torch.long),
            flat_counts=self.flat_counts.to(device=target, dtype=torch.long),
            state_offsets=self.state_offsets.to(device=target, dtype=torch.long),
            window_num_bits=self.window_num_bits.to(device=target, dtype=torch.long),
            max_faults_per_window=self.max_faults_per_window,
            max_state_count=self.max_state_count,
            num_windows=self.num_windows,
        )


def _cat_or_empty(tensors: list[torch.Tensor]) -> torch.Tensor:
    nonempty = [tensor for tensor in tensors if tensor.numel()]
    if not nonempty:
        return torch.empty((0,), dtype=torch.long)
    return torch.cat(nonempty).to(dtype=torch.long)


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
    fault_ids, detector_mask_states = graph.project_window(tuple(range(graph.num_detectors)))
    detector_logits = logits[fault_ids.to(device=logits.device)] if fault_ids.numel() else logits.new_empty((0,))
    dist = parity_distribution_from_mask_states(
        detector_logits,
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


def projected_window_mask_states(
    graph: FaultGraph,
    window_bits: tuple[int, ...],
) -> tuple[torch.Tensor, torch.Tensor]:
    """Return fault indices and packed local masks for a window projection."""

    return graph.project_window(window_bits)


def exact_window_nll(
    graph: FaultGraph,
    logits: torch.Tensor,
    observations: torch.Tensor,
    window: ObservationWindow,
    *,
    aggregate_unique: bool = True,
    backend: LikelihoodBackend = "auto",
) -> torch.Tensor:
    """Exact mean NLL after projecting the DEM parity map to one observation window."""

    if logits.ndim != 1 or logits.numel() != graph.M:
        raise ValueError(f"logits must have shape [{graph.M}]")
    cache = build_window_nll_cache(graph, observations, window, aggregate_unique=aggregate_unique).to(logits.device)
    return exact_window_nll_from_cache(logits, cache, backend=backend)


def build_window_nll_cache(
    graph: FaultGraph,
    observations: torch.Tensor,
    window: ObservationWindow,
    *,
    aggregate_unique: bool = True,
) -> WindowNLLCache:
    if not window.bits:
        raise ValueError("window must contain at least one observation bit")
    fault_ids, mask_states = projected_window_mask_states(graph, window.bits)
    local_observations = torch.as_tensor(observations, dtype=torch.bool)[:, list(window.bits)]
    states = observation_bits_to_states(local_observations, B=window.size)
    if aggregate_unique:
        states, counts = torch.unique(states, sorted=False, return_counts=True)
    else:
        counts = None
    return WindowNLLCache(
        window=window,
        fault_ids=fault_ids,
        mask_states=mask_states,
        states=states,
        counts=counts,
        num_observations=int(local_observations.shape[0]),
    )


def build_window_nll_caches(
    graph: FaultGraph,
    observations: torch.Tensor,
    windows: list[ObservationWindow] | tuple[ObservationWindow, ...],
    *,
    aggregate_unique: bool = True,
    device: torch.device | str | None = None,
) -> list[WindowNLLCache]:
    caches = [
        build_window_nll_cache(graph, observations, window, aggregate_unique=aggregate_unique)
        for window in windows
    ]
    if device is None:
        return caches
    return [cache.to(device) for cache in caches]


def build_window_batch_nll_cache(
    caches: list[WindowNLLCache] | tuple[WindowNLLCache, ...],
    *,
    device: torch.device | str | None = None,
) -> WindowBatchNLLCache:
    batch = WindowBatchNLLCache.from_window_caches(caches)
    return batch if device is None else batch.to(device)


def exact_window_nll_from_cache(
    logits: torch.Tensor,
    cache: WindowNLLCache,
    *,
    backend: LikelihoodBackend = "auto",
) -> torch.Tensor:
    if cache.fault_ids.numel() == 0:
        states = cache.states.to(device=logits.device)
        zero = logits.new_tensor(0.0)
        impossible = states != 0
        if bool(impossible.any()):
            return zero + torch.finfo(logits.dtype).max
        return zero

    local_logits = logits[cache.fault_ids.to(device=logits.device)]
    if cache.window.size <= 2:
        dist = _small_window_distribution_from_logits(
            local_logits,
            cache.mask_states.to(device=logits.device),
            cache.window.size,
        )
        return _nll_from_cached_states(dist, cache)

    dist = parity_distribution_from_mask_states(
        local_logits,
        cache.mask_states,
        num_bits=cache.window.size,
        backend=backend,
    )
    return _nll_from_cached_states(dist, cache)


def _nll_from_cached_states(dist: torch.Tensor, cache: WindowNLLCache) -> torch.Tensor:
    states = cache.states.to(device=dist.device)
    if cache.counts is not None:
        counts = cache.counts.to(device=dist.device)
        probs = dist[states].clamp_min(torch.finfo(dist.dtype).tiny)
        return -(counts.to(dtype=dist.dtype) * torch.log(probs)).sum() / counts.sum()
    probs = dist[states].clamp_min(torch.finfo(dist.dtype).tiny)
    return -torch.log(probs).mean()


def _small_window_distribution_from_logits(
    local_logits: torch.Tensor,
    mask_states: torch.Tensor,
    num_bits: int,
) -> torch.Tensor:
    if num_bits == 1:
        mean0 = _parity_mean(local_logits, mask_states == 1)
        p1 = (1 - mean0) / 2
        return torch.stack([1 - p1, p1])
    if num_bits == 2:
        mean0 = _parity_mean(local_logits, (mask_states & 1) != 0)
        mean1 = _parity_mean(local_logits, (mask_states & 2) != 0)
        mean01 = _parity_mean(local_logits, (mask_states == 1) | (mask_states == 2))
        return torch.stack(
            [
                (1 + mean0 + mean1 + mean01) / 4,
                (1 - mean0 + mean1 - mean01) / 4,
                (1 + mean0 - mean1 - mean01) / 4,
                (1 - mean0 - mean1 + mean01) / 4,
            ]
        )
    raise ValueError("small-window closed form only supports one or two bits")


def _parity_mean(local_logits: torch.Tensor, selector: torch.Tensor) -> torch.Tensor:
    if not bool(selector.any()):
        return local_logits.new_tensor(1.0)
    parity_factors = 1 - 2 * torch.sigmoid(local_logits)
    return torch.prod(parity_factors[selector])


def local_window_exact_nll(
    graph: FaultGraph,
    logits: torch.Tensor,
    observations: torch.Tensor,
    windows: list[ObservationWindow] | tuple[ObservationWindow, ...],
    *,
    aggregate_unique: bool = True,
    backend: LikelihoodBackend = "auto",
) -> torch.Tensor:
    """Composite exact local likelihood averaged over observation windows."""

    if not windows:
        raise ValueError("local_window_exact_nll requires at least one window")
    caches = build_window_nll_caches(
        graph,
        observations,
        windows,
        aggregate_unique=aggregate_unique,
        device=logits.device,
    )
    if resolve_likelihood_backend(logits, backend) == "cuda_extension":
        batch_cache = build_window_batch_nll_cache(caches, device=logits.device)
        return local_window_exact_nll_batched_from_cache(logits, batch_cache)
    return local_window_exact_nll_from_caches(logits, caches, backend=backend)


def local_window_exact_nll_from_caches(
    logits: torch.Tensor,
    caches: list[WindowNLLCache] | tuple[WindowNLLCache, ...],
    *,
    backend: LikelihoodBackend = "auto",
) -> torch.Tensor:
    if not caches:
        raise ValueError("local_window_exact_nll_from_caches requires at least one cache")
    losses = [exact_window_nll_from_cache(logits, cache, backend=backend) for cache in caches]
    return torch.stack(losses).mean()


def local_window_exact_nll_batched_from_cache(
    logits: torch.Tensor,
    cache: WindowBatchNLLCache,
) -> torch.Tensor:
    if not logits.is_cuda:
        raise ValueError("batched CUDA local-window NLL requires CUDA logits")
    if logits.ndim != 1:
        raise ValueError("logits must be rank-1")
    return _LocalWindowNLLCuda.apply(
        logits,
        cache.flat_fault_ids,
        cache.flat_masks,
        cache.fault_offsets,
        cache.flat_states,
        cache.flat_counts,
        cache.state_offsets,
        cache.window_num_bits,
        cache.max_faults_per_window,
        cache.max_state_count,
    )


class _LocalWindowNLLCuda(torch.autograd.Function):
    @staticmethod
    def forward(
        ctx,
        logits: torch.Tensor,
        flat_fault_ids: torch.Tensor,
        flat_masks: torch.Tensor,
        fault_offsets: torch.Tensor,
        flat_states: torch.Tensor,
        flat_counts: torch.Tensor,
        state_offsets: torch.Tensor,
        window_num_bits: torch.Tensor,
        max_faults_per_window: int,
        max_state_count: int,
    ) -> torch.Tensor:
        extension = _load_cuda_extension()
        loss, grad_logits = extension.local_window_nll_value_and_grad(
            logits.contiguous(),
            flat_fault_ids.contiguous(),
            flat_masks.contiguous(),
            fault_offsets.contiguous(),
            flat_states.contiguous(),
            flat_counts.contiguous(),
            state_offsets.contiguous(),
            window_num_bits.contiguous(),
            int(max_faults_per_window),
            int(max_state_count),
        )
        ctx.save_for_backward(grad_logits)
        return loss

    @staticmethod
    def backward(ctx, grad_output: torch.Tensor) -> tuple[torch.Tensor, None, None, None, None, None, None, None, None, None]:
        (grad_logits,) = ctx.saved_tensors
        return grad_output * grad_logits, None, None, None, None, None, None, None, None, None


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
