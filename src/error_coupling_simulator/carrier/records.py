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


def _binary_array(value: Any, *, name: str, ndim: tuple[int, ...]) -> np.ndarray:
    array = np.asarray(value)
    if array.ndim not in ndim:
        expected = " or ".join(str(item) for item in ndim)
        raise ValueError(f"{name} must have {expected} dimensions, got shape {array.shape}")
    if not np.issubdtype(array.dtype, np.integer) and array.dtype != np.bool_:
        raise TypeError(f"{name} must contain binary integer values, got dtype {array.dtype}")
    out = np.ascontiguousarray(array, dtype=np.uint8)
    if out.size and bool(np.any(out > 1)):
        raise ValueError(f"{name} must contain only 0/1 values")
    return out


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
    payload = np.asarray(packed)
    if payload.ndim != 2:
        raise ValueError(f"packed shots must be 2D, got shape {payload.shape}")
    if not np.issubdtype(payload.dtype, np.integer) and payload.dtype != np.bool_:
        raise TypeError(f"packed shots must be integer bytes, got dtype {payload.dtype}")
    payload = np.ascontiguousarray(payload, dtype=np.uint8)
    bits = rounds * num_stabilizers
    syndrome_bytes = (bits + 7) // 8
    expected_stride = syndrome_bytes + 1
    if payload.shape[1] != expected_stride:
        raise ValueError(
            f"packed shot stride {payload.shape[1]} != expected {expected_stride} "
            f"for R={rounds}, n_stab={num_stabilizers}"
        )
    flips = payload[:, syndrome_bytes]
    if flips.size and bool(np.any(flips > 1)):
        raise ValueError("packed logical-flip byte must contain only 0/1 values")
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
        n_shots = int(self.n_shots)
        syndrome_bits = int(self.syndrome_bits_per_shot)
        if n_shots < 0:
            raise ValueError(f"n_shots must be non-negative, got {n_shots}")
        if syndrome_bits < 1:
            raise ValueError(
                f"syndrome_bits_per_shot must be positive, got {syndrome_bits}"
            )
        if not isinstance(self.header, Mapping):
            raise TypeError("header must be a mapping")
        if not isinstance(self.diag, Mapping):
            raise TypeError("diag must be a mapping")
        if not isinstance(self.provenance, Mapping):
            raise TypeError("provenance must be a mapping")
        object.__setattr__(self, "header", dict(self.header))
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
            payload = np.asarray(self.shots)
            if payload.ndim != 2:
                raise ValueError(f"shots must be a 2D packed byte array, got {payload.shape}")
            payload = np.ascontiguousarray(payload, dtype=np.uint8)
            if payload.shape[0] != n_shots:
                raise ValueError(
                    f"packed shot count {payload.shape[0]} != declared n_shots {n_shots}"
                )
            expected_stride = (syndrome_bits + 7) // 8 + 1
            if payload.shape[1] != expected_stride:
                raise ValueError(
                    f"packed shot stride {payload.shape[1]} != declared stride "
                    f"{expected_stride}"
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
        record_header.update(
            {
                "format": record_header.get(
                    "format", "error_coupling_simulator.packed_shots/v1"
                ),
                "n_stab": num_stabilizers,
                "R": rounds,
                "N": int(syn.shape[0]),
                "syndrome_bits_per_shot": expected_bits,
                "out_stride_bytes": int(packed.shape[1]),
                "syndrome_layout": (
                    "shot_major: shot_id outer, then round, then stabilizer "
                    "(round-major, LSB-first packbits); logical flip in trailing byte"
                ),
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
        return self.shots

    def _header_geometry(self) -> tuple[int, int]:
        missing = [name for name in ("n_stab", "R") if name not in self.header]
        if missing:
            raise KeyError(
                f"PackedShotBatch header lacks {missing}; both 'n_stab' and 'R' are required"
            )
        n_stab = _positive_int("header['n_stab']", self.header["n_stab"])
        rounds = _positive_int("header['R']", self.header["R"])
        if n_stab * rounds != self.syndrome_bits_per_shot:
            raise ValueError(
                "header geometry does not match syndrome_bits_per_shot: "
                f"R*n_stab={rounds * n_stab}, declared={self.syndrome_bits_per_shot}"
            )
        return n_stab, rounds

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
        prefix_rounds = int(n_rounds)
        if not 0 <= prefix_rounds <= rounds:
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


# Transitional type name for callers that previously consumed qec_twin's ShotSet.
ShotSet = PackedShotBatch


def _positive_int(name: str, value: Any) -> int:
    integer = int(value)
    if integer < 1 or integer != value:
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
    "PackedShotBatch",
    "RecordBatch",
    "ShotSet",
    "pack_raw_syndrome_shots",
    "unpack_raw_syndrome_shots",
]
