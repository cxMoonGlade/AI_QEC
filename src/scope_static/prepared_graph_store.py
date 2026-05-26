from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import torch

from .fault_graph import FaultGraph
from .parity_map import DemParityMap


PREPARED_FAULT_GRAPH_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class PreparedFaultGraphCacheLoad:
    graph: FaultGraph | None
    audit: dict[str, object]
    status: str
    path: Path
    key: str
    metadata: dict[str, object]


def prepared_fault_graph_cache_key(identity: dict[str, object]) -> str:
    """Stable content key for prepared Stage-1 FaultGraph artifacts."""

    payload = {
        "schema_version": PREPARED_FAULT_GRAPH_SCHEMA_VERSION,
        "identity": identity,
    }
    encoded = json.dumps(_stable_jsonable(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def prepared_fault_graph_cache_file(cache_dir: str | Path, key: str) -> Path:
    return Path(cache_dir) / f"fault_graph_{key}.pt"


def save_prepared_fault_graph_cache(
    path: str | Path,
    *,
    key: str,
    graph: FaultGraph,
    audit: dict[str, object],
    metadata: dict[str, object] | None = None,
) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": PREPARED_FAULT_GRAPH_SCHEMA_VERSION,
        "key": key,
        "metadata": _stable_jsonable(metadata or {}),
        "graph": _graph_to_payload(graph),
        "audit": _stable_jsonable(audit),
    }
    temporary = target.with_name(f"{target.name}.tmp.{os.getpid()}")
    torch.save(payload, temporary)
    temporary.replace(target)
    return target


def load_prepared_fault_graph_cache(
    path: str | Path,
    *,
    expected_key: str,
) -> PreparedFaultGraphCacheLoad:
    source = Path(path)
    if not source.exists():
        return PreparedFaultGraphCacheLoad(None, {}, "miss", source, expected_key, {})
    try:
        payload = _torch_load(source)
    except Exception:
        return PreparedFaultGraphCacheLoad(None, {}, "invalid", source, expected_key, {})
    if not isinstance(payload, dict):
        return PreparedFaultGraphCacheLoad(None, {}, "invalid", source, expected_key, {})
    if int(payload.get("schema_version", -1)) != PREPARED_FAULT_GRAPH_SCHEMA_VERSION:
        return PreparedFaultGraphCacheLoad(None, {}, "schema_mismatch", source, expected_key, {})
    metadata = _metadata_dict(payload.get("metadata", {}))
    if payload.get("key") != expected_key:
        return PreparedFaultGraphCacheLoad(None, {}, "key_mismatch", source, expected_key, metadata)
    try:
        graph = _graph_from_payload(payload["graph"])
        audit = _metadata_dict(payload.get("audit", {}))
    except Exception:
        return PreparedFaultGraphCacheLoad(None, {}, "invalid", source, expected_key, metadata)
    return PreparedFaultGraphCacheLoad(graph, audit, "hit", source, expected_key, metadata)


def _graph_to_payload(graph: FaultGraph) -> dict[str, object]:
    dem = graph.dem_parity_map
    return {
        "dem_parity_map": {
            "num_observation_bits": int(dem.num_observation_bits),
            "num_faults": int(dem.num_faults),
            "supports_by_fault": dem.supports_by_fault,
            "faults_by_observation_bit": dem.faults_by_observation_bit,
            "packed_masks64": dem.packed_masks64,
            "dense_A": None if dem.dense_A is None else dem.dense_A.detach().cpu().to(dtype=torch.bool),
        },
        "num_detectors": int(graph.num_detectors),
        "num_observables": int(graph.num_observables),
        "raw_to_effective": graph.raw_to_effective.detach().cpu().to(dtype=torch.long),
        "effective_to_raw": graph.effective_to_raw,
        "duplicate_mask_groups": graph.duplicate_mask_groups,
        "zero_mask_raw_indices": graph.zero_mask_raw_indices,
        "orbit_ids": graph.orbit_ids.detach().cpu().to(dtype=torch.long),
        "orbit_sizes": graph.orbit_sizes.detach().cpu().to(dtype=torch.long),
        "template_ids": graph.template_ids.detach().cpu().to(dtype=torch.long),
        "raw_features": graph.raw_features.detach().cpu().to(dtype=torch.float64),
        "residual_features": graph.residual_features.detach().cpu().to(dtype=torch.float64),
        "selected_feature_indices": graph.selected_feature_indices.detach().cpu().to(dtype=torch.long),
        "feature_rank_by_orbit": {int(key): int(value) for key, value in graph.feature_rank_by_orbit.items()},
        "detector_coordinates": None
        if graph.detector_coordinates is None
        else graph.detector_coordinates.detach().cpu().to(dtype=torch.float64),
        "effective_probabilities": None
        if graph.effective_probabilities is None
        else graph.effective_probabilities.detach().cpu().to(dtype=torch.float64),
    }


def _graph_from_payload(payload: dict[str, object]) -> FaultGraph:
    dem_payload = _metadata_dict(payload["dem_parity_map"])
    dem = DemParityMap(
        num_observation_bits=int(dem_payload["num_observation_bits"]),
        num_faults=int(dem_payload["num_faults"]),
        supports_by_fault=_tuple_tuple_int(dem_payload["supports_by_fault"]),
        faults_by_observation_bit=_tuple_tuple_int(dem_payload["faults_by_observation_bit"]),
        packed_masks64=_tuple_tuple_int(dem_payload["packed_masks64"]),
        dense_A=_optional_tensor(dem_payload.get("dense_A"), dtype=torch.bool),
    )
    return FaultGraph(
        dem_parity_map=dem,
        num_detectors=int(payload["num_detectors"]),
        num_observables=int(payload["num_observables"]),
        raw_to_effective=_required_tensor(payload, "raw_to_effective", dtype=torch.long),
        effective_to_raw=_tuple_tuple_int(payload["effective_to_raw"]),
        duplicate_mask_groups=_tuple_tuple_int(payload["duplicate_mask_groups"]),
        zero_mask_raw_indices=tuple(int(value) for value in payload["zero_mask_raw_indices"]),
        orbit_ids=_required_tensor(payload, "orbit_ids", dtype=torch.long),
        orbit_sizes=_required_tensor(payload, "orbit_sizes", dtype=torch.long),
        template_ids=_required_tensor(payload, "template_ids", dtype=torch.long),
        raw_features=_required_tensor(payload, "raw_features", dtype=torch.float64),
        residual_features=_required_tensor(payload, "residual_features", dtype=torch.float64),
        selected_feature_indices=_required_tensor(payload, "selected_feature_indices", dtype=torch.long),
        feature_rank_by_orbit={
            int(key): int(value)
            for key, value in _metadata_dict(payload["feature_rank_by_orbit"]).items()
        },
        detector_coordinates=_optional_tensor(payload.get("detector_coordinates"), dtype=torch.float64),
        effective_probabilities=_optional_tensor(payload.get("effective_probabilities"), dtype=torch.float64),
    )


def _tuple_tuple_int(value: object) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(item) for item in group) for group in value)


def _required_tensor(payload: dict[str, object], key: str, *, dtype: torch.dtype) -> torch.Tensor:
    value = payload[key]
    if not isinstance(value, torch.Tensor):
        raise TypeError(f"{key} is not a tensor")
    return value.to(device="cpu", dtype=dtype).contiguous()


def _optional_tensor(value: object, *, dtype: torch.dtype) -> torch.Tensor | None:
    if value is None:
        return None
    if not isinstance(value, torch.Tensor):
        raise TypeError("expected tensor or None")
    return value.to(device="cpu", dtype=dtype).contiguous()


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
