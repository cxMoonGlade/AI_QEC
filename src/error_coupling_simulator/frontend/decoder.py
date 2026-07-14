"""Optional external PyMatching decoder used by the simulator frontend.

The simulator does not bundle or implement a decoder. Installing the ``hw``
extra supplies the pinned external PyMatching wheel used here at upstream
defaults.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np


PYMATCHING_PIN = "2.4.0"
PYMATCHING_WHEEL_FILENAME = (
    "pymatching-2.4.0-cp312-cp312-manylinux_2_27_x86_64."
    "manylinux_2_28_x86_64.whl"
)
PYMATCHING_WHEEL_SHA256 = (
    "15e6d73153713a8f383f44ba4497d478fb4c4d765fbdd30f9fc1e1d47af75760"
)


def _require_pymatching():
    try:
        import pymatching
    except ImportError as exc:  # pragma: no cover - exercised in the minimal ecs env
        raise ImportError(
            "PyMatching decoding requires the optional 'hw' extra: "
            "install error-coupling-simulator[hw]"
        ) from exc
    return pymatching


def pymatching_provenance() -> dict:
    """Return the frozen wheel pin and best-effort installed binary identity."""

    installed_version: str | None = None
    binary_sha256: str | None = None
    binary_path: str | None = None
    try:
        import pymatching

        installed_version = getattr(pymatching, "__version__", None)
        try:
            from pymatching import _cpp_pymatching

            binary_path = getattr(_cpp_pymatching, "__file__", None)
            if binary_path:
                binary_sha256 = hashlib.sha256(Path(binary_path).read_bytes()).hexdigest()
        except Exception:
            pass
    except ImportError:
        pass
    return {
        "pinned_version": PYMATCHING_PIN,
        "installed_version": installed_version,
        "version_match": installed_version == PYMATCHING_PIN,
        "wheel_filename": PYMATCHING_WHEEL_FILENAME,
        "wheel_sha256": PYMATCHING_WHEEL_SHA256,
        "installed_binary_path": binary_path,
        "installed_binary_sha256": binary_sha256,
        "provenance_complete": installed_version == PYMATCHING_PIN,
    }


def _as_dem(dem_like):
    """Coerce a Stim DEM object, path, text, or ``.dem``-bearing wrapper."""

    import stim

    if isinstance(dem_like, stim.DetectorErrorModel):
        return dem_like
    if hasattr(dem_like, "dem"):
        return _as_dem(dem_like.dem)
    if isinstance(dem_like, Path):
        return stim.DetectorErrorModel.from_file(str(dem_like))
    if isinstance(dem_like, str):
        if "\n" not in dem_like and Path(dem_like).is_file():
            return stim.DetectorErrorModel.from_file(dem_like)
        return stim.DetectorErrorModel(dem_like)
    raise TypeError(
        f"cannot interpret {type(dem_like).__name__} as a detector error model"
    )


def _normalize_detector_records(
    num_detectors: int,
    detectors: np.ndarray,
) -> tuple[np.ndarray, bool]:
    """Return contiguous records and whether they are packed bytes."""

    records = np.asarray(detectors)
    if records.ndim != 2:
        raise ValueError(
            f"detection events must be 2D [shots, ...], got shape {records.shape}"
        )
    packed_width = (int(num_detectors) + 7) // 8
    if records.dtype == np.bool_:
        if records.shape[1] != num_detectors:
            raise ValueError(
                f"bool dets width {records.shape[1]} != num_detectors {num_detectors}"
            )
        return np.ascontiguousarray(records.astype(np.uint8)), False
    if records.dtype == np.uint8:
        if records.shape[1] == packed_width and packed_width != num_detectors:
            return np.ascontiguousarray(records), True
        if records.shape[1] == num_detectors and records.max(initial=0) <= 1:
            if records.shape[1] == packed_width:
                raise ValueError(
                    "ambiguous uint8 dets: width equals both the packed and the "
                    "unpacked layout -- pass bool for unpacked input"
                )
            return np.ascontiguousarray(records), False
        raise ValueError(
            f"uint8 dets width {records.shape[1]} matches neither packed "
            f"({packed_width}) nor 0/1 unpacked ({num_detectors}) layout"
        )
    raise ValueError(f"dets dtype must be bool or uint8, got {records.dtype}")


def decode_dem(dem, detectors: np.ndarray) -> np.ndarray:
    """Decode detector records with pinned external PyMatching defaults.

    Accepted inputs are unpacked bool ``[shots, detectors]`` or unambiguous
    packed uint8 ``[shots, ceil(detectors / 8)]``. Predictions are uint8 with
    shape ``[shots, observables]``.
    """

    detector_error_model = _as_dem(dem)
    pymatching = _require_pymatching()
    matching = pymatching.Matching.from_detector_error_model(detector_error_model)
    records, bit_packed = _normalize_detector_records(
        detector_error_model.num_detectors,
        detectors,
    )
    predictions = matching.decode_batch(records, bit_packed_shots=bit_packed)
    return np.asarray(predictions, dtype=np.uint8).reshape(records.shape[0], -1)


__all__ = [
    "PYMATCHING_PIN",
    "PYMATCHING_WHEEL_FILENAME",
    "PYMATCHING_WHEEL_SHA256",
    "decode_dem",
    "pymatching_provenance",
]
