from __future__ import annotations

"""Artifact writers for simulator frontend runs."""

import json
from dataclasses import dataclass, fields
import hashlib
from pathlib import Path
from typing import Any

import numpy as np

from qec_twin.hardware import b8_io


@dataclass(frozen=True)
class ArtifactPaths:
    out_dir: Path
    circuit_ideal: Path
    circuit_noisy_pauli: Path
    detector_error_model: Path
    detection_events: Path
    obs_flips_actual: Path
    obs_flips_predicted: Path
    ideal_detection_events: Path
    ideal_obs_flips_actual: Path
    sample_summary_ideal: Path
    sample_summary_noisy: Path
    theory_prediction: Path
    decoder_results: Path
    source_timeline: Path
    source_timeline_binding: Path
    manifest: Path


def artifact_paths(out_dir: str | Path) -> ArtifactPaths:
    root = Path(out_dir)
    return ArtifactPaths(
        out_dir=root,
        circuit_ideal=root / "circuit_ideal.stim",
        circuit_noisy_pauli=root / "circuit_noisy_pauli.stim",
        detector_error_model=root / "detector_error_model.dem",
        detection_events=root / "detection_events.b8",
        obs_flips_actual=root / "obs_flips_actual.b8",
        obs_flips_predicted=root / "obs_flips_predicted.b8",
        ideal_detection_events=root / "ideal_detection_events.b8",
        ideal_obs_flips_actual=root / "ideal_obs_flips_actual.b8",
        sample_summary_ideal=root / "sample_summary_ideal.json",
        sample_summary_noisy=root / "sample_summary_noisy.json",
        theory_prediction=root / "theory_prediction.json",
        decoder_results=root / "decoder_results.json",
        source_timeline=root / "source_timeline.npz",
        source_timeline_binding=root / "source_timeline_binding.json",
        manifest=root / "manifest.json",
    )


def write_b8(path: str | Path, bits: np.ndarray) -> Path:
    """Write unpacked bool/0-1 `[shots, bits]` as Stim-compatible packed `.b8`."""

    path = Path(path)
    arr = np.asarray(bits)
    if arr.ndim != 2:
        raise ValueError(f"expected [shots, bits] array, got shape {arr.shape}")
    if arr.shape[1] <= 0:
        raise ValueError("cannot write readable .b8 for zero-bit records")
    packed = b8_io.pack_bits(arr)
    path.write_bytes(np.ascontiguousarray(packed).tobytes())
    return path


def write_b8_optional(path: str | Path, bits: np.ndarray) -> Path | None:
    """Write `.b8` when bit width is positive; otherwise remove stale file."""

    path = Path(path)
    arr = np.asarray(bits)
    if arr.ndim != 2:
        raise ValueError(f"expected [shots, bits] array, got shape {arr.shape}")
    if arr.shape[1] == 0:
        path.unlink(missing_ok=True)
        return None
    return write_b8(path, arr)


def write_json(path: str | Path, payload: dict[str, Any]) -> Path:
    path = Path(path)
    path.write_text(json.dumps(_jsonable(payload), indent=2, sort_keys=True) + "\n")
    return path


def clear_known_artifacts(paths: ArtifactPaths) -> None:
    """Remove known output files before writing a new run into an existing directory."""

    for field in fields(paths):
        value = getattr(paths, field.name)
        if isinstance(value, Path) and field.name != "out_dir":
            value.unlink(missing_ok=True)


def file_sha256(path: str | Path | None) -> str | None:
    if path is None:
        return None
    p = Path(path)
    if not p.exists():
        return None
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def record_summary(detectors: np.ndarray, observables: np.ndarray) -> dict[str, Any]:
    """Small, JSON-safe summary of sampled detector/observable records."""

    det = np.asarray(detectors, dtype=np.bool_)
    obs = np.asarray(observables, dtype=np.bool_)
    return {
        "num_shots": int(det.shape[0]),
        "num_detectors": int(det.shape[1]) if det.ndim == 2 else 0,
        "num_observables": int(obs.shape[1]) if obs.ndim == 2 else 0,
        "detector_marginals": det.mean(axis=0).tolist() if det.size else [],
        "observable_marginals": obs.mean(axis=0).tolist() if obs.size else [],
        "any_detector_rate": float(det.any(axis=1).mean()) if det.size else 0.0,
        "any_observable_rate": float(obs.any(axis=1).mean()) if obs.size else 0.0,
    }


def _jsonable(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value
