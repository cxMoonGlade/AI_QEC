from __future__ import annotations

"""Backend-neutral detector/observable record batches and packed-shot I/O.

The packed carrier payload stores raw, round-major stabilizer outcomes because
that is the byte layout emitted by the trajectory kernels.  Raw syndromes are
not the simulator product: :class:`PackedShotBatch` applies the declared
temporal XOR fold before exposing ``det`` records.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from .record_fold import s_to_det

_EVALUATOR_ONLY_PROVENANCE_KEYS = frozenset(
    {
        "analog_truth",
        "channel_truth",
        "evaluator_truth",
        "ground_truth",
        "hidden_state",
        "mechanism_truth",
        "process_truth",
        "source_timeline",
        "source_trace",
        "source_trajectory",
        "truth",
    }
)

PACKED_SHOT_SCHEMA = "error_coupling_simulator.carrier.packed_shots.v1"
PACKED_SYNDROME_LAYOUT = "round_major_lsb_syndrome_then_logical_u8"
PACKED_DETECTOR_INITIAL_PRIOR = "all_zero"
_PACKED_HEADER_FIELDS = (
    "format",
    "n_stab",
    "R",
    "N",
    "syndrome_bits_per_shot",
    "out_stride_bytes",
    "syndrome_layout",
    "detector_initial_prior",
)


def _binary_array(value: Any, *, name: str, ndim: tuple[int, ...]) -> np.ndarray:
    array = np.asarray(value)
    if array.ndim not in ndim:
        expected = " or ".join(str(item) for item in ndim)
        raise ValueError(f"{name} must have {expected} dimensions, got shape {array.shape}")
    if not np.issubdtype(array.dtype, np.integer) and array.dtype != np.bool_:
        raise TypeError(
            f"{name} must have an integer or bool dtype containing 0/1 values, "
            f"got {array.dtype}"
        )
    if array.size and bool(np.any((array != 0) & (array != 1))):
        raise ValueError(f"{name} must contain only 0/1 values")
    out = np.array(array, dtype=np.uint8, order="C", copy=True)
    out.setflags(write=False)
    return out


def _packed_byte_array(
    value: Any,
    *,
    name: str,
    n_shots: int | None,
    syndrome_bits_per_shot: int,
) -> np.ndarray:
    """Validate packed bytes before narrowing and return an immutable snapshot."""

    array = np.asarray(value)
    if array.ndim != 2:
        raise ValueError(f"{name} must be a 2D packed byte array, got {array.shape}")
    if np.issubdtype(array.dtype, np.floating):
        if array.size and not bool(np.all(np.isfinite(array))):
            raise ValueError(f"{name} must contain only finite byte values")
        raise TypeError(f"{name} must contain integer byte values, got dtype {array.dtype}")
    if not np.issubdtype(array.dtype, np.integer) and array.dtype != np.bool_:
        raise TypeError(f"{name} must contain integer byte values, got dtype {array.dtype}")
    if array.size and bool(np.any((array < 0) | (array > 255))):
        raise ValueError(f"{name} byte values must lie in [0, 255] before uint8 conversion")

    payload = np.array(array, dtype=np.uint8, order="C", copy=True)
    if n_shots is not None and payload.shape[0] != n_shots:
        raise ValueError(
            f"packed shot count {payload.shape[0]} != declared n_shots {n_shots}"
        )

    syndrome_bytes = (syndrome_bits_per_shot + 7) // 8
    expected_stride = syndrome_bytes + 1
    if payload.shape[1] != expected_stride:
        raise ValueError(
            f"packed shot stride {payload.shape[1]} != declared stride {expected_stride}"
        )

    flips = payload[:, syndrome_bytes]
    if flips.size and bool(np.any(flips > 1)):
        raise ValueError("packed logical-flip byte must contain only 0/1 values")

    used_bits_in_final_byte = syndrome_bits_per_shot % 8
    if used_bits_in_final_byte:
        padding_mask = (~((1 << used_bits_in_final_byte) - 1)) & 0xFF
        final_syndrome_byte = payload[:, syndrome_bytes - 1]
        if final_syndrome_byte.size and bool(
            np.any(final_syndrome_byte & padding_mask)
        ):
            raise ValueError("packed syndrome padding bits must be zero")

    payload.setflags(write=False)
    return payload


def _validate_packed_header(
    header: Mapping[str, Any],
    *,
    n_shots: int,
    syndrome_bits_per_shot: int,
) -> tuple[int, int]:
    missing = [name for name in _PACKED_HEADER_FIELDS if name not in header]
    if missing:
        raise ValueError(f"PackedShotBatch header lacks required fields {missing}")

    if header["format"] != PACKED_SHOT_SCHEMA:
        raise ValueError(
            "PackedShotBatch header format must be "
            f"{PACKED_SHOT_SCHEMA!r}, got {header['format']!r}"
        )
    if header["syndrome_layout"] != PACKED_SYNDROME_LAYOUT:
        raise ValueError(
            "PackedShotBatch header syndrome_layout must be "
            f"{PACKED_SYNDROME_LAYOUT!r}, got {header['syndrome_layout']!r}"
        )
    if header["detector_initial_prior"] != PACKED_DETECTOR_INITIAL_PRIOR:
        raise ValueError(
            "PackedShotBatch header detector_initial_prior must be "
            f"{PACKED_DETECTOR_INITIAL_PRIOR!r}, "
            f"got {header['detector_initial_prior']!r}"
        )

    header_n_shots = _nonnegative_int("header['N']", header["N"])
    header_bits = _positive_int(
        "header['syndrome_bits_per_shot']", header["syndrome_bits_per_shot"]
    )
    header_stride = _positive_int(
        "header['out_stride_bytes']", header["out_stride_bytes"]
    )
    n_stab = _positive_int("header['n_stab']", header["n_stab"])
    rounds = _positive_int("header['R']", header["R"])

    if header_n_shots != n_shots:
        raise ValueError(
            f"PackedShotBatch header N={header_n_shots} != n_shots={n_shots}"
        )
    if header_bits != syndrome_bits_per_shot:
        raise ValueError(
            "PackedShotBatch header syndrome_bits_per_shot="
            f"{header_bits} != declared {syndrome_bits_per_shot}"
        )
    if n_stab * rounds != syndrome_bits_per_shot:
        raise ValueError(
            "PackedShotBatch header geometry does not match "
            "syndrome_bits_per_shot: "
            f"R*n_stab={rounds * n_stab}, declared={syndrome_bits_per_shot}"
        )
    expected_stride = (syndrome_bits_per_shot + 7) // 8 + 1
    if header_stride != expected_stride:
        raise ValueError(
            "PackedShotBatch header out_stride_bytes="
            f"{header_stride} != expected {expected_stride}"
        )
    return n_stab, rounds


@dataclass(frozen=True)
class RecordBatch:
    """One backend's emitted detector events and logical-observable flips.

    ``det`` is always ``(shots, detectors)``.  ``obs`` may be ``(shots,)`` for
    the common single-observable carrier or ``(shots, observables)`` for a
    multi-observable circuit.  Both arrays contain only ``uint8`` 0/1 values.
    Evaluator-only process truth is forbidden from ``provenance``.
    """

    det: np.ndarray
    obs: np.ndarray
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        det = _binary_array(self.det, name="det", ndim=(2,))
        obs = _binary_array(self.obs, name="obs", ndim=(1, 2))
        if obs.shape[0] != det.shape[0]:
            raise ValueError(
                f"record shot-count mismatch: det has {det.shape[0]}, obs has {obs.shape[0]}"
            )
        if not isinstance(self.provenance, Mapping):
            raise TypeError("provenance must be a mapping")
        _reject_evaluator_only_provenance(self.provenance)
        object.__setattr__(self, "det", det)
        object.__setattr__(self, "obs", obs)
        object.__setattr__(self, "provenance", dict(self.provenance))

    @property
    def n_shots(self) -> int:
        return int(self.det.shape[0])

    def to_det_obs(self) -> dict[str, np.ndarray]:
        """Return the standard record payload with temporal detector events."""

        return {"det": self.det, "obs": self.obs}


def pack_raw_syndrome_shots(
    syndromes: np.ndarray,
    logical_flips: np.ndarray,
) -> np.ndarray:
    """Pack raw round-major syndromes LSB-first plus a trailing flip byte."""

    syn = _binary_array(syndromes, name="syndromes", ndim=(2,))
    flips = _binary_array(logical_flips, name="logical_flips", ndim=(1,))
    if flips.shape[0] != syn.shape[0]:
        raise ValueError(
            f"shot-count mismatch: {syn.shape[0]} syndromes vs {flips.shape[0]} flips"
        )
    syn_packed = np.packbits(syn, axis=1, bitorder="little")
    return np.concatenate((syn_packed, flips[:, None]), axis=1)


def unpack_raw_syndrome_shots(
    packed: np.ndarray,
    *,
    rounds: int,
    num_stabilizers: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Inverse of :func:`pack_raw_syndrome_shots`."""

    rounds = _positive_int("rounds", rounds)
    num_stabilizers = _positive_int("num_stabilizers", num_stabilizers)
    bits = rounds * num_stabilizers
    payload = _packed_byte_array(
        packed,
        name="packed shots",
        n_shots=None,
        syndrome_bits_per_shot=bits,
    )
    syndrome_bytes = (bits + 7) // 8
    flips = payload[:, syndrome_bytes]
    syndromes = np.unpackbits(
        payload[:, :syndrome_bytes], axis=1, bitorder="little"
    )[:, :bits]
    return syndromes.astype(np.uint8, copy=False), flips.astype(np.uint8, copy=False)


@dataclass(frozen=True)
class PackedShotBatch:
    """Self-describing packed trajectory output with conforming record accessors."""

    header: Mapping[str, Any]
    path: Path | None
    header_path: Path | None
    n_shots: int
    syndrome_bits_per_shot: int
    diag: Mapping[str, Any] = field(default_factory=dict)
    shots: np.ndarray | None = None
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        n_shots = _nonnegative_int("n_shots", self.n_shots)
        syndrome_bits = _positive_int(
            "syndrome_bits_per_shot", self.syndrome_bits_per_shot
        )
        if not isinstance(self.header, Mapping):
            raise TypeError("header must be a mapping")
        if not isinstance(self.diag, Mapping):
            raise TypeError("diag must be a mapping")
        if not isinstance(self.provenance, Mapping):
            raise TypeError("provenance must be a mapping")
        header = dict(self.header)
        _validate_packed_header(
            header,
            n_shots=n_shots,
            syndrome_bits_per_shot=syndrome_bits,
        )
        object.__setattr__(self, "header", header)
        object.__setattr__(self, "diag", dict(self.diag))
        object.__setattr__(self, "provenance", dict(self.provenance))
        object.__setattr__(self, "n_shots", n_shots)
        object.__setattr__(self, "syndrome_bits_per_shot", syndrome_bits)
        object.__setattr__(self, "path", None if self.path is None else Path(self.path))
        object.__setattr__(
            self,
            "header_path",
            None if self.header_path is None else Path(self.header_path),
        )
        if self.shots is not None:
            payload = _packed_byte_array(
                self.shots,
                name="shots",
                n_shots=n_shots,
                syndrome_bits_per_shot=syndrome_bits,
            )
            object.__setattr__(self, "shots", payload)

    @classmethod
    def from_raw_syndromes(
        cls,
        syndromes: np.ndarray,
        logical_flips: np.ndarray,
        *,
        rounds: int,
        num_stabilizers: int,
        provenance: Mapping[str, Any] | None = None,
        header: Mapping[str, Any] | None = None,
    ) -> "PackedShotBatch":
        rounds = _positive_int("rounds", rounds)
        num_stabilizers = _positive_int("num_stabilizers", num_stabilizers)
        syn = _binary_array(syndromes, name="syndromes", ndim=(2,))
        expected_bits = rounds * num_stabilizers
        if syn.shape[1] != expected_bits:
            raise ValueError(
                f"syndrome width {syn.shape[1]} != R*n_stab = {expected_bits}"
            )
        flips = _binary_array(logical_flips, name="logical_flips", ndim=(1,))
        packed = pack_raw_syndrome_shots(syn, flips)
        record_header = dict(header or {})
        record_header.setdefault("format", PACKED_SHOT_SCHEMA)
        record_header.setdefault("syndrome_layout", PACKED_SYNDROME_LAYOUT)
        record_header.setdefault(
            "detector_initial_prior", PACKED_DETECTOR_INITIAL_PRIOR
        )
        record_header.update(
            {
                "n_stab": num_stabilizers,
                "R": rounds,
                "N": int(syn.shape[0]),
                "syndrome_bits_per_shot": expected_bits,
                "out_stride_bytes": int(packed.shape[1]),
            }
        )
        return cls(
            header=record_header,
            path=None,
            header_path=None,
            n_shots=int(syn.shape[0]),
            syndrome_bits_per_shot=expected_bits,
            shots=packed,
            provenance=dict(provenance or {}),
        )

    def _require_shots(self, method: str) -> np.ndarray:
        if self.shots is None:
            raise ValueError(
                f"PackedShotBatch.{method}: shots is None; materialize the run or "
                f"load its packed buffer from path={self.path}"
            )
        _validate_packed_header(
            self.header,
            n_shots=self.n_shots,
            syndrome_bits_per_shot=self.syndrome_bits_per_shot,
        )
        return _packed_byte_array(
            self.shots,
            name=f"PackedShotBatch.{method} shots",
            n_shots=self.n_shots,
            syndrome_bits_per_shot=self.syndrome_bits_per_shot,
        )

    def _header_geometry(self) -> tuple[int, int]:
        return _validate_packed_header(
            self.header,
            n_shots=self.n_shots,
            syndrome_bits_per_shot=self.syndrome_bits_per_shot,
        )

    def to_raw_syndrome_obs(self) -> dict[str, np.ndarray]:
        """Explicit diagnostic accessor for the packed pre-fold syndrome payload."""

        n_stab, rounds = self._header_geometry()
        syndrome, obs = unpack_raw_syndrome_shots(
            self._require_shots("to_raw_syndrome_obs"),
            rounds=rounds,
            num_stabilizers=n_stab,
        )
        return {"syndrome": syndrome, "obs": obs}

    def to_record_batch(self) -> RecordBatch:
        """Decode and fold raw syndromes into the simulator's record product."""

        n_stab, rounds = self._header_geometry()
        raw = self.to_raw_syndrome_obs()
        provenance = dict(self.provenance)
        for key in (
            "backend",
            "compiled_semantics",
            "run_purpose",
            "dtype",
            "precision_policy",
            "evidence_eligibility",
            "physics_construction_dtype",
            "build_identity",
            "package_version",
            "package_tree_sha256",
        ):
            if key in self.header and key not in provenance:
                provenance[key] = self.header[key]
        provenance.update(
            {
                "record_semantics": "temporal_detector_events",
                "raw_syndrome_layout": "round_major",
                "rounds": rounds,
                "num_stabilizers": n_stab,
            }
        )
        return RecordBatch(
            det=s_to_det(raw["syndrome"], rounds, n_stab),
            obs=raw["obs"],
            provenance=provenance,
        )

    def to_det_obs(self) -> dict[str, np.ndarray]:
        """Return conforming temporal detector events, never raw syndromes."""

        return self.to_record_batch().to_det_obs()

    def packed_bytes(self) -> bytes:
        return np.ascontiguousarray(self._require_shots("packed_bytes")).tobytes()

    def syndrome_prefix_bytes(self, n_rounds: int) -> bytes:
        packed = self._require_shots("syndrome_prefix_bytes")
        n_stab, rounds = self._header_geometry()
        prefix_rounds = _nonnegative_int("n_rounds", n_rounds)
        if prefix_rounds > rounds:
            raise ValueError(
                f"n_rounds must be in [0, R={rounds}], got {prefix_rounds}"
            )
        prefix_bits = prefix_rounds * n_stab
        if prefix_bits == 0:
            return b""
        if prefix_bits % 8 == 0:
            return np.ascontiguousarray(packed[:, : prefix_bits // 8]).tobytes()
        raw = self.to_raw_syndrome_obs()["syndrome"]
        prefix = np.packbits(raw[:, :prefix_bits], axis=1, bitorder="little")
        return np.ascontiguousarray(prefix).tobytes()


def _strict_int(name: str, value: Any) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, np.integer)
    ):
        raise TypeError(f"{name} must be an integer, got {value!r}")
    return int(value)


def _nonnegative_int(name: str, value: Any) -> int:
    integer = _strict_int(name, value)
    if integer < 0:
        raise ValueError(f"{name} must be a non-negative integer, got {value!r}")
    return integer


def _positive_int(name: str, value: Any) -> int:
    integer = _strict_int(name, value)
    if integer < 1:
        raise ValueError(f"{name} must be a positive integer, got {value!r}")
    return integer


def _reject_evaluator_only_provenance(value: Any, *, path: str = "provenance") -> None:
    if isinstance(value, Mapping):
        for raw_key, item in value.items():
            key = str(raw_key).lower().replace("-", "_").replace(" ", "_")
            if key in _EVALUATOR_ONLY_PROVENANCE_KEYS or (
                key == "visibility" and str(item).lower() == "evaluator_only"
            ):
                raise ValueError(
                    f"record provenance cannot contain evaluator-only process truth at "
                    f"{path}.{raw_key}"
                )
            _reject_evaluator_only_provenance(item, path=f"{path}.{raw_key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_evaluator_only_provenance(item, path=f"{path}[{index}]")


__all__ = [
    "PACKED_DETECTOR_INITIAL_PRIOR",
    "PACKED_SHOT_SCHEMA",
    "PACKED_SYNDROME_LAYOUT",
    "PackedShotBatch",
    "RecordBatch",
    "pack_raw_syndrome_shots",
    "unpack_raw_syndrome_shots",
]
