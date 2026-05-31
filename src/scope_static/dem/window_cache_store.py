from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import torch

from .fault_graph import FaultGraph
from .likelihood import WindowBatchNLLCache
from .windows import ObservationWindow


WINDOW_BATCH_CACHE_SCHEMA_VERSION = 2


@dataclass(frozen=True)
class WindowBatchCacheLoad:
    cache: WindowBatchNLLCache | None
    status: str
    path: Path
    key: str
    metadata: dict[str, object]


def window_batch_cache_key(
    graph: FaultGraph,
    windows: list[ObservationWindow] | tuple[ObservationWindow, ...],
    identity: dict[str, object],
) -> str:
    """Stable content key for prepared local-window observation caches."""

    payload = {
        "schema_version": WINDOW_BATCH_CACHE_SCHEMA_VERSION,
        "identity": identity,
        "graph": {
            "B": graph.B,
            "M": graph.M,
            "num_detectors": graph.num_detectors,
            "num_observables": graph.num_observables,
            "supports_by_fault": graph.supports_by_fault,
        },
        "windows": [
            {
                "bits": tuple(int(bit) for bit in window.bits),
                "kind": window.kind,
                "name": window.name,
            }
            for window in windows
        ],
    }
    encoded = json.dumps(_stable_jsonable(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def window_batch_cache_file(cache_dir: str | Path, key: str) -> Path:
    return Path(cache_dir) / f"{key}.pt"


def save_window_batch_cache(
    path: str | Path,
    *,
    key: str,
    cache: WindowBatchNLLCache,
    metadata: dict[str, object] | None = None,
) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": WINDOW_BATCH_CACHE_SCHEMA_VERSION,
        "key": key,
        "metadata": _stable_jsonable(metadata or {}),
        "cache": _cache_to_payload(cache),
    }
    temporary = target.with_name(f"{target.name}.tmp.{os.getpid()}")
    torch.save(payload, temporary)
    temporary.replace(target)
    return target


def load_window_batch_cache(
    path: str | Path,
    *,
    expected_key: str,
    device: torch.device | str,
) -> WindowBatchCacheLoad:
    source = Path(path)
    if not source.exists():
        return WindowBatchCacheLoad(None, "miss", source, expected_key, {})
    try:
        payload = _torch_load(source)
    except Exception:
        return WindowBatchCacheLoad(None, "invalid", source, expected_key, {})
    if not isinstance(payload, dict):
        return WindowBatchCacheLoad(None, "invalid", source, expected_key, {})
    if int(payload.get("schema_version", -1)) != WINDOW_BATCH_CACHE_SCHEMA_VERSION:
        return WindowBatchCacheLoad(None, "schema_mismatch", source, expected_key, {})
    if payload.get("key") != expected_key:
        metadata = payload.get("metadata", {})
        return WindowBatchCacheLoad(None, "key_mismatch", source, expected_key, _metadata_dict(metadata))
    try:
        cache = _cache_from_payload(payload["cache"], device=device)
    except Exception:
        return WindowBatchCacheLoad(None, "invalid", source, expected_key, _metadata_dict(payload.get("metadata", {})))
    return WindowBatchCacheLoad(cache, "hit", source, expected_key, _metadata_dict(payload.get("metadata", {})))


def _cache_to_payload(cache: WindowBatchNLLCache) -> dict[str, object]:
    return {
        "flat_fault_ids": cache.flat_fault_ids.detach().cpu().to(dtype=torch.long),
        "flat_masks": cache.flat_masks.detach().cpu().to(dtype=torch.long),
        "fault_offsets": cache.fault_offsets.detach().cpu().to(dtype=torch.long),
        "flat_states": cache.flat_states.detach().cpu().to(dtype=torch.long),
        "flat_counts": cache.flat_counts.detach().cpu().to(dtype=torch.long),
        "state_offsets": cache.state_offsets.detach().cpu().to(dtype=torch.long),
        "window_num_bits": cache.window_num_bits.detach().cpu().to(dtype=torch.long),
        "window_total_counts": cache.window_total_counts.detach().cpu().to(dtype=torch.long),
        "max_faults_per_window": int(cache.max_faults_per_window),
        "max_state_count": int(cache.max_state_count),
        "num_windows": int(cache.num_windows),
    }


def _cache_from_payload(payload: dict[str, object], *, device: torch.device | str) -> WindowBatchNLLCache:
    target = torch.device(device)
    return WindowBatchNLLCache(
        flat_fault_ids=_payload_tensor(payload, "flat_fault_ids", target),
        flat_masks=_payload_tensor(payload, "flat_masks", target),
        fault_offsets=_payload_tensor(payload, "fault_offsets", target),
        flat_states=_payload_tensor(payload, "flat_states", target),
        flat_counts=_payload_tensor(payload, "flat_counts", target),
        state_offsets=_payload_tensor(payload, "state_offsets", target),
        window_num_bits=_payload_tensor(payload, "window_num_bits", target),
        window_total_counts=_payload_tensor(payload, "window_total_counts", target),
        max_faults_per_window=int(payload["max_faults_per_window"]),
        max_state_count=int(payload["max_state_count"]),
        num_windows=int(payload["num_windows"]),
    )


def _payload_tensor(payload: dict[str, object], key: str, device: torch.device) -> torch.Tensor:
    value = payload[key]
    if not isinstance(value, torch.Tensor):
        raise TypeError(f"{key} is not a tensor")
    return value.to(device=device, dtype=torch.long)


def _torch_load(path: Path) -> object:
    try:
        return torch.load(path, map_location="cpu", weights_only=True)
    except TypeError:
        return torch.load(path, map_location="cpu")


def _metadata_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _stable_jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    if isinstance(value, dict):
        return {str(key): _stable_jsonable(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple)):
        return [_stable_jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)
