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
CudaKernelVariant = str

CUDA_KERNEL_VARIANTS = {"dp", "spectral_shadow", "spectral", "auto"}


def _likelihood_probability_floor(dtype: torch.dtype) -> float:
    if dtype == torch.float32:
        return 1e-7
    if dtype == torch.float64:
        return 1e-12
    return torch.finfo(dtype).tiny


def _clamp_likelihood_probabilities(probabilities: torch.Tensor) -> torch.Tensor:
    return probabilities.clamp_min(_likelihood_probability_floor(probabilities.dtype))


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
    window_total_counts: torch.Tensor
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
        window_total_counts = []
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
            window_total_counts.append(int(counts.sum().item()))
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
            window_total_counts=torch.tensor(window_total_counts, dtype=torch.long),
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
            window_total_counts=self.window_total_counts.to(device=target, dtype=torch.long),
            max_faults_per_window=self.max_faults_per_window,
            max_state_count=self.max_state_count,
            num_windows=self.num_windows,
        )


def subset_window_batch_nll_cache(
    cache: WindowBatchNLLCache,
    window_indices: list[int] | tuple[int, ...],
) -> WindowBatchNLLCache:
    """Return a view-like compact batch cache for a subset of prepared windows."""

    indices = [int(index) for index in window_indices]
    if not indices:
        raise ValueError("subset_window_batch_nll_cache requires at least one window index")
    if min(indices) < 0 or max(indices) >= int(cache.num_windows):
        raise IndexError("window index out of range")

    fault_offsets_cpu = cache.fault_offsets.detach().cpu().to(dtype=torch.long)
    state_offsets_cpu = cache.state_offsets.detach().cpu().to(dtype=torch.long)
    window_bits_cpu = cache.window_num_bits.detach().cpu().to(dtype=torch.long)
    total_counts_cpu = cache.window_total_counts.detach().cpu().to(dtype=torch.long)
    flat_fault_ids: list[torch.Tensor] = []
    flat_masks: list[torch.Tensor] = []
    flat_states: list[torch.Tensor] = []
    flat_counts: list[torch.Tensor] = []
    fault_offsets = [0]
    state_offsets = [0]
    window_num_bits: list[int] = []
    window_total_counts: list[int] = []
    max_faults = 0
    max_state_count = 1

    for index in indices:
        fault_start = int(fault_offsets_cpu[index].item())
        fault_end = int(fault_offsets_cpu[index + 1].item())
        state_start = int(state_offsets_cpu[index].item())
        state_end = int(state_offsets_cpu[index + 1].item())
        fault_count = fault_end - fault_start
        state_count = state_end - state_start
        num_bits = int(window_bits_cpu[index].item())

        flat_fault_ids.append(cache.flat_fault_ids[fault_start:fault_end])
        flat_masks.append(cache.flat_masks[fault_start:fault_end])
        flat_states.append(cache.flat_states[state_start:state_end])
        flat_counts.append(cache.flat_counts[state_start:state_end])
        fault_offsets.append(fault_offsets[-1] + fault_count)
        state_offsets.append(state_offsets[-1] + state_count)
        window_num_bits.append(num_bits)
        window_total_counts.append(int(total_counts_cpu[index].item()))
        max_faults = max(max_faults, fault_count)
        max_state_count = max(max_state_count, 1 << num_bits)

    device = cache.flat_fault_ids.device
    return WindowBatchNLLCache(
        flat_fault_ids=_cat_or_empty(flat_fault_ids).to(device=device),
        flat_masks=_cat_or_empty(flat_masks).to(device=device),
        fault_offsets=torch.tensor(fault_offsets, dtype=torch.long, device=device),
        flat_states=_cat_or_empty(flat_states).to(device=device),
        flat_counts=_cat_or_empty(flat_counts).to(device=device),
        state_offsets=torch.tensor(state_offsets, dtype=torch.long, device=device),
        window_num_bits=torch.tensor(window_num_bits, dtype=torch.long, device=device),
        window_total_counts=torch.tensor(window_total_counts, dtype=torch.long, device=device),
        max_faults_per_window=max_faults,
        max_state_count=max_state_count,
        num_windows=len(indices),
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
        probs = _clamp_likelihood_probabilities(dist[unique_states])
        return -(counts.to(dtype=dist.dtype) * torch.log(probs)).sum() / counts.sum()
    probs = _clamp_likelihood_probabilities(dist[states])
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
        probs = _clamp_likelihood_probabilities(dist[unique_states])
        return -(counts.to(dtype=dist.dtype) * torch.log(probs)).sum() / counts.sum()
    probs = _clamp_likelihood_probabilities(dist[states])
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


def local_window_workload_audit(cache: WindowBatchNLLCache) -> dict[str, object]:
    """Summarize active-fault and observation-state work in a batched window cache."""

    if cache.num_windows <= 0:
        return {
            "num_windows": 0,
            "max_window_bits": 0,
            "mean_state_count": 0.0,
            "total_window_state_count": 0,
            "mean_active_faults_per_window": 0.0,
            "max_active_faults_per_window": 0,
            "total_active_fault_window_pairs": 0,
            "unique_local_observation_patterns": 0,
        }
    window_bits = cache.window_num_bits.detach().cpu().to(dtype=torch.long)
    state_counts = torch.pow(2, window_bits).to(dtype=torch.long)
    fault_offsets = cache.fault_offsets.detach().cpu().to(dtype=torch.long)
    active_fault_counts = fault_offsets[1:] - fault_offsets[:-1]
    return {
        "num_windows": int(cache.num_windows),
        "max_window_bits": int(window_bits.max().item()),
        "mean_state_count": float(state_counts.to(dtype=torch.float64).mean().item()),
        "total_window_state_count": int(state_counts.sum().item()),
        "mean_active_faults_per_window": float(active_fault_counts.to(dtype=torch.float64).mean().item()),
        "max_active_faults_per_window": int(active_fault_counts.max().item()),
        "total_active_fault_window_pairs": int(active_fault_counts.sum().item()),
        "unique_local_observation_patterns": int(cache.flat_states.numel()),
        "mean_cached_observations_per_window": float(
            cache.window_total_counts.detach().cpu().to(dtype=torch.float64).mean().item()
        ),
    }


def local_window_cuda_kernel_audit(
    cache: WindowBatchNLLCache,
    *,
    requested_kernel_variant: CudaKernelVariant = "dp",
    spectral_memory_cap_bytes: int = 1024 * 1024 * 1024,
    scalar_bytes: int = 8,
) -> dict[str, object]:
    """Audit CUDA local-window kernel selection and spectral memory requirements."""

    _validate_cuda_kernel_variant(requested_kernel_variant)
    history_rows = int(cache.flat_fault_ids.numel()) + int(cache.num_windows)
    spectral_bytes = 2 * history_rows * int(cache.max_state_count) * int(scalar_bytes)
    dense_bytes = 2 * int(cache.num_windows) * int(cache.max_state_count) * int(scalar_bytes)
    required_bytes = spectral_bytes + dense_bytes
    fallback_reason = None
    selected = requested_kernel_variant
    if requested_kernel_variant == "auto":
        if int(cache.max_state_count) <= 256 and required_bytes <= int(spectral_memory_cap_bytes):
            selected = "spectral"
        else:
            selected = "dp"
            fallback_reason = (
                "auto_spectral_max_state_count_exceeded"
                if int(cache.max_state_count) > 256
                else "auto_spectral_memory_cap_exceeded"
            )
    elif requested_kernel_variant in {"spectral", "spectral_shadow"}:
        if int(cache.max_state_count) > 4096:
            fallback_reason = "spectral_max_state_count_exceeded"
        elif required_bytes > int(spectral_memory_cap_bytes):
            fallback_reason = "spectral_memory_cap_exceeded"
    return {
        "requested_cuda_kernel_variant": requested_kernel_variant,
        "selected_cuda_kernel_variant": selected,
        "cuda_kernel_fallback_reason": fallback_reason,
        "spectral_history_rows": history_rows,
        "spectral_required_bytes": int(required_bytes),
        "spectral_memory_cap_bytes": int(spectral_memory_cap_bytes),
    }


def build_window_batch_nll_cache_from_observations(
    graph: FaultGraph,
    observations: torch.Tensor,
    windows: list[ObservationWindow] | tuple[ObservationWindow, ...],
    *,
    aggregate_unique: bool = True,
    device: torch.device | str | None = None,
    cache_backend: str = "auto",
) -> WindowBatchNLLCache:
    """Build a batched local-window cache, using CUDA for observation aggregation when available."""

    if cache_backend not in {"auto", "pytorch", "cuda_extension"}:
        raise ValueError("cache_backend must be 'auto', 'pytorch', or 'cuda_extension'")
    if not windows:
        raise ValueError("WindowBatchNLLCache requires at least one window")
    target = torch.device(device) if device is not None else torch.as_tensor(observations).device
    if aggregate_unique and target.type == "cuda" and cache_backend != "pytorch":
        try:
            return _build_window_batch_nll_cache_cuda(graph, observations, windows, device=target)
        except Exception as exc:
            if cache_backend == "cuda_extension":
                raise RuntimeError("failed to build CUDA local-window observation cache") from exc

    caches = build_window_nll_caches(
        graph,
        observations,
        windows,
        aggregate_unique=aggregate_unique,
        device=target if device is not None else None,
    )
    return build_window_batch_nll_cache(caches, device=target if device is not None else None)


def _build_window_batch_nll_cache_cuda(
    graph: FaultGraph,
    observations: torch.Tensor,
    windows: list[ObservationWindow] | tuple[ObservationWindow, ...],
    *,
    device: torch.device,
) -> WindowBatchNLLCache:
    obs = torch.as_tensor(observations, dtype=torch.bool, device=device)
    if obs.ndim != 2 or obs.shape[1] != graph.B:
        raise ValueError(f"observations must have shape [N, {graph.B}]")
    obs = obs.contiguous()

    flat_window_bits, window_offsets, window_num_bits = _window_layout_tensors(windows)
    max_window_bits = int(window_num_bits.max().item()) if window_num_bits.numel() else 0
    if max_window_bits >= 63:
        raise ValueError("exact state indexing currently requires window size < 63")
    if max_window_bits > 20:
        raise ValueError("CUDA window-cache builder supports max_window_bits <= 20")
    max_state_count = 1 << max_window_bits

    flat_fault_ids, flat_masks, fault_offsets, max_faults = _window_projection_tensors(graph, windows)
    extension = _load_cuda_extension()
    flat_states, flat_counts, state_offsets = extension.window_observation_state_counts(
        obs,
        flat_window_bits.to(device=device, dtype=torch.long).contiguous(),
        window_offsets.to(device=device, dtype=torch.long).contiguous(),
        window_num_bits.to(device=device, dtype=torch.long).contiguous(),
        int(max_state_count),
    )
    return WindowBatchNLLCache(
        flat_fault_ids=flat_fault_ids.to(device=device, dtype=torch.long),
        flat_masks=flat_masks.to(device=device, dtype=torch.long),
        fault_offsets=fault_offsets.to(device=device, dtype=torch.long),
        flat_states=flat_states.to(device=device, dtype=torch.long),
        flat_counts=flat_counts.to(device=device, dtype=torch.long),
        state_offsets=state_offsets.to(device=device, dtype=torch.long),
        window_num_bits=window_num_bits.to(device=device, dtype=torch.long),
        window_total_counts=torch.full((len(windows),), int(obs.shape[0]), dtype=torch.long, device=device),
        max_faults_per_window=max_faults,
        max_state_count=max_state_count,
        num_windows=len(windows),
    )


def _window_layout_tensors(
    windows: list[ObservationWindow] | tuple[ObservationWindow, ...],
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    flat_bits: list[int] = []
    offsets = [0]
    num_bits: list[int] = []
    for window in windows:
        if not window.bits:
            raise ValueError("window must contain at least one observation bit")
        for bit in window.bits:
            flat_bits.append(int(bit))
        offsets.append(len(flat_bits))
        num_bits.append(int(window.size))
    return (
        torch.tensor(flat_bits, dtype=torch.long),
        torch.tensor(offsets, dtype=torch.long),
        torch.tensor(num_bits, dtype=torch.long),
    )


def _window_projection_tensors(
    graph: FaultGraph,
    windows: list[ObservationWindow] | tuple[ObservationWindow, ...],
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, int]:
    flat_fault_ids: list[torch.Tensor] = []
    flat_masks: list[torch.Tensor] = []
    fault_offsets = [0]
    max_faults = 0
    for window in windows:
        fault_ids, masks = projected_window_mask_states(graph, window.bits)
        flat_fault_ids.append(fault_ids.to(device="cpu", dtype=torch.long))
        flat_masks.append(masks.to(device="cpu", dtype=torch.long))
        fault_offsets.append(fault_offsets[-1] + int(fault_ids.numel()))
        max_faults = max(max_faults, int(fault_ids.numel()))
    return (
        _cat_or_empty(flat_fault_ids),
        _cat_or_empty(flat_masks),
        torch.tensor(fault_offsets, dtype=torch.long),
        max_faults,
    )


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
        probs = _clamp_likelihood_probabilities(dist[states])
        return -(counts.to(dtype=dist.dtype) * torch.log(probs)).sum() / counts.sum()
    probs = _clamp_likelihood_probabilities(dist[states])
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
    cuda_kernel_variant: CudaKernelVariant = "dp",
    spectral_min_abs_factor: float = 1e-6,
    spectral_memory_cap_bytes: int = 1024 * 1024 * 1024,
) -> torch.Tensor:
    """Composite exact local likelihood averaged over observation windows."""

    if not windows:
        raise ValueError("local_window_exact_nll requires at least one window")
    if resolve_likelihood_backend(logits, backend) == "cuda_extension" and aggregate_unique:
        batch_cache = build_window_batch_nll_cache_from_observations(
            graph,
            observations,
            windows,
            aggregate_unique=True,
            device=logits.device,
            cache_backend="cuda_extension",
        )
        return local_window_exact_nll_batched_from_cache(
            logits,
            batch_cache,
            cuda_kernel_variant=cuda_kernel_variant,
            spectral_min_abs_factor=spectral_min_abs_factor,
            spectral_memory_cap_bytes=spectral_memory_cap_bytes,
        )
    caches = build_window_nll_caches(
        graph,
        observations,
        windows,
        aggregate_unique=aggregate_unique,
        device=logits.device,
    )
    if resolve_likelihood_backend(logits, backend) == "cuda_extension":
        batch_cache = build_window_batch_nll_cache(caches, device=logits.device)
        return local_window_exact_nll_batched_from_cache(
            logits,
            batch_cache,
            cuda_kernel_variant=cuda_kernel_variant,
            spectral_min_abs_factor=spectral_min_abs_factor,
            spectral_memory_cap_bytes=spectral_memory_cap_bytes,
        )
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
    *,
    cuda_kernel_variant: CudaKernelVariant = "dp",
    spectral_min_abs_factor: float = 1e-6,
    spectral_memory_cap_bytes: int = 1024 * 1024 * 1024,
) -> torch.Tensor:
    _validate_cuda_kernel_variant(cuda_kernel_variant)
    if not logits.is_cuda:
        raise ValueError("batched CUDA local-window NLL requires CUDA logits")
    if logits.ndim != 1:
        raise ValueError("logits must be rank-1")
    if not (torch.is_grad_enabled() and logits.requires_grad):
        return _local_window_exact_nll_batched_forward_only(logits, cache)
    selected_kernel_variant = _select_cuda_kernel_variant(
        cache,
        cuda_kernel_variant,
        spectral_memory_cap_bytes=spectral_memory_cap_bytes,
        scalar_bytes=logits.element_size(),
    )
    return _LocalWindowNLLCuda.apply(
        logits,
        cache.flat_fault_ids,
        cache.flat_masks,
        cache.fault_offsets,
        cache.flat_states,
        cache.flat_counts,
        cache.state_offsets,
        cache.window_num_bits,
        cache.window_total_counts,
        cache.max_faults_per_window,
        cache.max_state_count,
        selected_kernel_variant,
        float(spectral_min_abs_factor),
        int(spectral_memory_cap_bytes),
    )


def _select_cuda_kernel_variant(
    cache: WindowBatchNLLCache,
    requested_kernel_variant: CudaKernelVariant,
    *,
    spectral_memory_cap_bytes: int,
    scalar_bytes: int,
) -> str:
    audit = local_window_cuda_kernel_audit(
        cache,
        requested_kernel_variant=requested_kernel_variant,
        spectral_memory_cap_bytes=spectral_memory_cap_bytes,
        scalar_bytes=scalar_bytes,
    )
    return str(audit["selected_cuda_kernel_variant"])


def _validate_cuda_kernel_variant(cuda_kernel_variant: CudaKernelVariant) -> None:
    if cuda_kernel_variant not in CUDA_KERNEL_VARIANTS:
        raise ValueError("cuda_kernel_variant must be 'dp', 'spectral_shadow', 'spectral', or 'auto'")


def _local_window_exact_nll_batched_forward_only(
    logits: torch.Tensor,
    cache: WindowBatchNLLCache,
) -> torch.Tensor:
    extension = _load_cuda_extension()
    if hasattr(extension, "local_window_nll_value") and cache.max_state_count <= 4096:
        return extension.local_window_nll_value(
            logits.contiguous(),
            cache.flat_fault_ids.contiguous(),
            cache.flat_masks.contiguous(),
            cache.fault_offsets.contiguous(),
            cache.flat_states.contiguous(),
            cache.flat_counts.contiguous(),
            cache.state_offsets.contiguous(),
            cache.window_num_bits.contiguous(),
            cache.window_total_counts.contiguous(),
            int(cache.max_faults_per_window),
            int(cache.max_state_count),
        )
    loss, _grad_logits = extension.local_window_nll_value_and_grad(
        logits.contiguous(),
        cache.flat_fault_ids.contiguous(),
        cache.flat_masks.contiguous(),
        cache.fault_offsets.contiguous(),
        cache.flat_states.contiguous(),
        cache.flat_counts.contiguous(),
        cache.state_offsets.contiguous(),
        cache.window_num_bits.contiguous(),
        cache.window_total_counts.contiguous(),
        int(cache.max_faults_per_window),
        int(cache.max_state_count),
    )
    return loss


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
        window_total_counts: torch.Tensor,
        max_faults_per_window: int,
        max_state_count: int,
        cuda_kernel_variant: str,
        spectral_min_abs_factor: float,
        spectral_memory_cap_bytes: int,
    ) -> torch.Tensor:
        extension = _load_cuda_extension()
        common_args = (
            logits.contiguous(),
            flat_fault_ids.contiguous(),
            flat_masks.contiguous(),
            fault_offsets.contiguous(),
            flat_states.contiguous(),
            flat_counts.contiguous(),
            state_offsets.contiguous(),
            window_num_bits.contiguous(),
            window_total_counts.contiguous(),
            int(max_faults_per_window),
            int(max_state_count),
        )
        if cuda_kernel_variant == "spectral":
            loss, grad_logits = extension.local_window_nll_value_and_grad_spectral(
                *common_args,
                float(spectral_min_abs_factor),
                int(spectral_memory_cap_bytes),
            )
        elif cuda_kernel_variant == "spectral_shadow":
            dp_loss, dp_grad_logits = extension.local_window_nll_value_and_grad(*common_args)
            spectral_loss, spectral_grad_logits = extension.local_window_nll_value_and_grad_spectral(
                *common_args,
                float(spectral_min_abs_factor),
                int(spectral_memory_cap_bytes),
            )
            loss_atol, grad_atol = _spectral_shadow_tolerances(logits.dtype)
            loss_diff = float((spectral_loss - dp_loss).abs().detach().cpu())
            grad_diff = float((spectral_grad_logits - dp_grad_logits).abs().max().detach().cpu())
            if loss_diff > loss_atol or grad_diff > grad_atol:
                raise RuntimeError(
                    "spectral_shadow mismatch: "
                    f"loss_abs_diff={loss_diff:.6g} grad_max_abs_diff={grad_diff:.6g}"
                )
            loss, grad_logits = dp_loss, dp_grad_logits
        else:
            loss, grad_logits = extension.local_window_nll_value_and_grad(*common_args)
        ctx.save_for_backward(grad_logits)
        return loss

    @staticmethod
    def backward(
        ctx,
        grad_output: torch.Tensor,
    ) -> tuple[torch.Tensor, None, None, None, None, None, None, None, None, None, None, None, None, None]:
        (grad_logits,) = ctx.saved_tensors
        return grad_output * grad_logits, None, None, None, None, None, None, None, None, None, None, None, None, None


def _spectral_shadow_tolerances(dtype: torch.dtype) -> tuple[float, float]:
    if dtype == torch.float64:
        return 1e-10, 1e-8
    return 1e-5, 1e-4


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
    probs = _clamp_likelihood_probabilities(dist[states])
    return -(counts * torch.log(probs)).sum() / counts.sum()


def aggregate_observations(observations: torch.Tensor, *, B: int) -> tuple[torch.Tensor, torch.Tensor]:
    states = observation_bits_to_states(observations, B=B)
    unique_states, counts = torch.unique(states, sorted=True, return_counts=True)
    return unique_states, counts


@functools.lru_cache(maxsize=1)
def _load_cuda_extension():
    from torch.utils.cpp_extension import load

    cuda_dir = Path(__file__).resolve().parents[1] / "cuda"
    build_root = Path(os.environ.get("TORCH_EXTENSIONS_DIR", Path(tempfile.gettempdir()) / "torch_extensions_scope_static"))
    build_dir = build_root / "scope_static_dem_likelihood_cuda"
    build_dir.mkdir(parents=True, exist_ok=True)
    return load(
        name="scope_static_dem_likelihood_cuda",
        sources=[
            str(cuda_dir / "dem_likelihood.cpp"),
            str(cuda_dir / "dem_likelihood_kernel.cu"),
            str(cuda_dir / "window_cache.cpp"),
            str(cuda_dir / "window_cache_kernel.cu"),
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
