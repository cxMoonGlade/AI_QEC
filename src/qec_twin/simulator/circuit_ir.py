from __future__ import annotations

"""User-facing circuit IR for simulator frontend artifacts.

This is a small, Stim-compatible intermediate representation, not a full analog
teacher IR. It captures the parts every QEC simulator frontend must agree on:
gates, ticks, measurements, detector definitions, and logical observables. Analog
joint-L / leakage truth is attached later as sidecar truth, not encoded here.
"""

from dataclasses import InitVar, dataclass, field
from typing import Sequence

from qec_twin.simulator.metadata_guard import (
    AXIS1_STATIC_ZZ_CALIBRATIONS_METADATA_KEY,
    AXIS1_STATIC_ZZ_COUPLINGS_METADATA_KEY,
    axis1_static_zz_calibrations_to_manifest,
    normalize_axis1_static_zz_calibrations,
    normalize_axis1_static_zz_couplings,
    validate_public_metadata,
)
from qec_twin.simulator.axis1_context import (
    AXIS1_LOCAL_LINDBLAD_CONTEXT_METADATA_KEY,
    Axis1LocalLindbladContextSpec,
    normalize_axis1_local_lindblad_context,
)

_RECORD_AFFECTING_GATE_NAMES = {
    "M",
    "MX",
    "MY",
    "MZ",
    "MR",
    "MRX",
    "MRY",
    "MRZ",
    "MPP",
    "DETECTOR",
    "OBSERVABLE_INCLUDE",
}

_SOURCE_NOISE_GATE_NAMES = {
    "CORRELATED_ERROR",
    "DEPOLARIZE1",
    "DEPOLARIZE2",
    "E",
    "ELSE_CORRELATED_ERROR",
    "HERALDED_ERASE",
    "HERALDED_PAULI_CHANNEL_1",
    "I_ERROR",
    "II_ERROR",
    "PAULI_CHANNEL_1",
    "PAULI_CHANNEL_2",
    "X_ERROR",
    "Y_ERROR",
    "Z_ERROR",
}

@dataclass(frozen=True)
class GateOp:
    """A Stim-compatible unitary/reset/noise instruction.

    Source circuits should contain gates and resets. Noise instructions are
    accepted only when a simulator noise pass has attached `noise_projection`
    metadata; this prevents source-embedded noise from masquerading as ideal or
    noiseless input.
    """

    name: str
    targets: tuple[int, ...]
    args: tuple[float, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", str(self.name).upper())
        object.__setattr__(self, "targets", tuple(int(t) for t in self.targets))
        object.__setattr__(self, "args", tuple(float(a) for a in self.args))


@dataclass(frozen=True)
class Tick:
    """A circuit time boundary."""


@dataclass(frozen=True)
class MeasureOp:
    """A measurement instruction with stable user keys for later detectors."""

    name: str
    targets: tuple[int, ...]
    keys: tuple[str, ...]
    args: tuple[float, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", str(self.name).upper())
        object.__setattr__(self, "targets", tuple(int(t) for t in self.targets))
        object.__setattr__(self, "keys", tuple(str(k) for k in self.keys))
        object.__setattr__(self, "args", tuple(float(a) for a in self.args))


@dataclass(frozen=True)
class DetectorDef:
    """Detector = XOR of earlier measurement keys."""

    name: str
    keys: tuple[str, ...]
    coords: tuple[float, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", str(self.name))
        object.__setattr__(self, "keys", tuple(str(k) for k in self.keys))
        object.__setattr__(self, "coords", tuple(float(c) for c in self.coords))


@dataclass(frozen=True)
class ObservableDef:
    """Logical observable = XOR of earlier measurement keys."""

    name: str
    keys: tuple[str, ...]
    index: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", str(self.name))
        object.__setattr__(self, "keys", tuple(str(k) for k in self.keys))
        object.__setattr__(self, "index", int(self.index))


CircuitStep = GateOp | Tick | MeasureOp | DetectorDef | ObservableDef


@dataclass(frozen=True)
class CircuitIR:
    """Stim-compatible circuit plus detector/observable record schema."""

    num_qubits: int
    steps: tuple[CircuitStep, ...]
    metadata: dict = field(default_factory=dict)
    _allow_noise_steps: InitVar[bool] = False

    def __post_init__(self, _allow_noise_steps: bool) -> None:
        object.__setattr__(self, "num_qubits", int(self.num_qubits))
        object.__setattr__(self, "steps", tuple(self.steps))
        object.__setattr__(
            self,
            "metadata",
            validate_public_metadata(self.metadata, label="CircuitIR.metadata"),
        )
        if self.num_qubits <= 0:
            raise ValueError("num_qubits must be positive")
        allow_noise_steps = bool(_allow_noise_steps)

        keys_seen: set[str] = set()
        detector_names: set[str] = set()
        observable_indices: set[int] = set()
        for step in self.steps:
            if isinstance(step, GateOp):
                if step.name in _RECORD_AFFECTING_GATE_NAMES:
                    raise ValueError(
                        f"record-affecting instruction {step.name!r} must use "
                        "MeasureOp/DetectorDef/ObservableDef, not GateOp"
                    )
                if step.name in _SOURCE_NOISE_GATE_NAMES and not allow_noise_steps:
                    raise ValueError(
                        f"source-embedded noise instruction {step.name!r} is not allowed in CircuitIR; "
                        "use NoiseBuilder/StimPauliNoiseSpec or pass an explicit pre-noised Stim source"
                    )
                _validate_targets(self.num_qubits, step.targets)
            elif isinstance(step, MeasureOp):
                _validate_targets(self.num_qubits, step.targets)
                if len(step.keys) != len(step.targets):
                    raise ValueError(f"measurement keys {step.keys} do not match {step.targets}")
                for key in step.keys:
                    if key in keys_seen:
                        raise ValueError(f"duplicate measurement key {key!r}")
                    keys_seen.add(key)
            elif isinstance(step, DetectorDef):
                if step.name in detector_names:
                    raise ValueError(f"duplicate detector name {step.name!r}")
                detector_names.add(step.name)
                _require_known_keys(keys_seen, step.keys)
            elif isinstance(step, ObservableDef):
                if step.index < 0:
                    raise ValueError(f"observable index must be non-negative, got {step.index}")
                if step.index in observable_indices:
                    raise ValueError(f"duplicate observable index {step.index}")
                observable_indices.add(step.index)
                _require_known_keys(keys_seen, step.keys)
            elif not isinstance(step, Tick):
                raise TypeError(f"unknown circuit step {type(step)!r}")

    @property
    def measurement_keys(self) -> tuple[str, ...]:
        keys: list[str] = []
        for step in self.steps:
            if isinstance(step, MeasureOp):
                keys.extend(step.keys)
        return tuple(keys)

    @property
    def detector_names(self) -> tuple[str, ...]:
        return tuple(step.name for step in self.steps if isinstance(step, DetectorDef))

    @property
    def observable_names(self) -> tuple[str, ...]:
        return tuple(step.name for step in self.steps if isinstance(step, ObservableDef))


def _as_targets(targets: int | Sequence[int]) -> tuple[int, ...]:
    if isinstance(targets, int):
        return (int(targets),)
    return tuple(int(t) for t in targets)


def _as_args(args: float | Sequence[float] | None) -> tuple[float, ...]:
    if args is None:
        return ()
    if isinstance(args, (int, float)):
        return (float(args),)
    return tuple(float(a) for a in args)


def _validate_targets(num_qubits: int, targets: tuple[int, ...]) -> None:
    for t in targets:
        if t < 0 or t >= num_qubits:
            raise ValueError(f"target {t} outside [0, {num_qubits})")


def _require_known_keys(keys_seen: set[str], keys: tuple[str, ...]) -> None:
    missing = [k for k in keys if k not in keys_seen]
    if missing:
        raise ValueError(f"unknown measurement key(s): {missing}")


class CircuitBuilder:
    """Ergonomic builder for :class:`CircuitIR`.

    Measurements receive stable keys. Detectors and observables refer to those
    keys; the Stim adapter later converts them into relative `rec[-k]` targets.
    """

    def __init__(self, num_qubits: int, *, metadata: dict | None = None) -> None:
        self.num_qubits = int(num_qubits)
        if self.num_qubits <= 0:
            raise ValueError("num_qubits must be positive")
        self._steps: list[CircuitStep] = []
        self._metadata = dict(metadata or {})
        self._keys_seen: set[str] = set()

    def gate(
        self,
        name: str,
        targets: int | Sequence[int],
        *,
        args: float | Sequence[float] | None = None,
    ) -> "CircuitBuilder":
        self._validate_targets(_as_targets(targets))
        self._steps.append(GateOp(str(name).upper(), _as_targets(targets), _as_args(args)))
        return self

    def tick(self) -> "CircuitBuilder":
        self._steps.append(Tick())
        return self

    def h(self, targets: int | Sequence[int]) -> "CircuitBuilder":
        return self.gate("H", targets)

    def x(self, targets: int | Sequence[int]) -> "CircuitBuilder":
        return self.gate("X", targets)

    def y(self, targets: int | Sequence[int]) -> "CircuitBuilder":
        return self.gate("Y", targets)

    def idle(
        self,
        targets: int | Sequence[int],
        *,
        duration_ns: float | None = None,
    ) -> "CircuitBuilder":
        """Insert an explicit Stim identity/idle instruction."""

        return self.gate("I", targets, args=None if duration_ns is None else float(duration_ns))

    def cz(self, targets: Sequence[int]) -> "CircuitBuilder":
        t = _as_targets(targets)
        if len(t) % 2:
            raise ValueError("CZ targets must be an even-length pair list")
        return self.gate("CZ", t)

    def cx(self, targets: Sequence[int]) -> "CircuitBuilder":
        t = _as_targets(targets)
        if len(t) % 2:
            raise ValueError("CX targets must be an even-length pair list")
        return self.gate("CX", t)

    def reset(self, targets: int | Sequence[int]) -> "CircuitBuilder":
        return self.gate("R", targets)

    def measure(
        self,
        target: int | Sequence[int],
        *,
        key: str | Sequence[str],
        basis: str = "Z",
        reset: bool = False,
        duration_ns: float | None = None,
    ) -> "CircuitBuilder":
        targets = _as_targets(target)
        if isinstance(key, str):
            keys = (key,)
        else:
            keys = tuple(str(k) for k in key)
        if len(keys) != len(targets):
            raise ValueError(f"measurement keys {keys} do not match targets {targets}")
        for k in keys:
            if k in self._keys_seen:
                raise ValueError(f"duplicate measurement key {k!r}")
            self._keys_seen.add(k)
        self._validate_targets(targets)
        basis = str(basis).upper()
        if basis not in {"X", "Y", "Z"}:
            raise ValueError(f"unsupported measurement basis {basis!r}")
        if basis == "Z":
            name = "MR" if reset else "M"
        else:
            name = f"MR{basis}" if reset else f"M{basis}"
        args = () if duration_ns is None else (float(duration_ns),)
        self._steps.append(MeasureOp(name, targets, keys, args))
        return self

    def detector(
        self,
        name: str,
        *,
        xor: Sequence[str],
        coords: Sequence[float] = (),
    ) -> "CircuitBuilder":
        keys = tuple(str(k) for k in xor)
        self._require_known_keys(keys)
        self._steps.append(DetectorDef(str(name), keys, tuple(float(c) for c in coords)))
        return self

    def observable(
        self,
        name: str,
        *,
        xor: Sequence[str],
        index: int = 0,
    ) -> "CircuitBuilder":
        keys = tuple(str(k) for k in xor)
        self._require_known_keys(keys)
        self._steps.append(ObservableDef(str(name), keys, int(index)))
        return self

    def declare_static_zz_couplings(
        self,
        edges: Sequence[Sequence[int]],
        *,
        zeta_rad_per_ns_by_edge: dict | Sequence[dict] | None = None,
    ) -> "CircuitBuilder":
        """Declare public static-ZZ device/schedule edges for Axis-1 lowering."""

        normalized = normalize_axis1_static_zz_couplings(
            edges,
            num_qubits=self.num_qubits,
            label="CircuitBuilder.declare_static_zz_couplings",
        )
        self._metadata[AXIS1_STATIC_ZZ_COUPLINGS_METADATA_KEY] = [
            list(edge) for edge in normalized
        ]
        calibrations = normalize_axis1_static_zz_calibrations(
            zeta_rad_per_ns_by_edge,
            num_qubits=self.num_qubits,
            declared_edges=normalized,
            label="CircuitBuilder.declare_static_zz_couplings.zeta_rad_per_ns_by_edge",
        )
        if calibrations:
            self._metadata[AXIS1_STATIC_ZZ_CALIBRATIONS_METADATA_KEY] = (
                axis1_static_zz_calibrations_to_manifest(calibrations)
            )
        else:
            self._metadata.pop(AXIS1_STATIC_ZZ_CALIBRATIONS_METADATA_KEY, None)
        return self

    def declare_axis1_local_lindblad_context(
        self,
        context: Axis1LocalLindbladContextSpec | dict,
    ) -> "CircuitBuilder":
        """Declare public Axis-1 Markovian context for joint-L lowering."""

        spec = normalize_axis1_local_lindblad_context(context)
        if spec.is_trivial:
            self._metadata.pop(AXIS1_LOCAL_LINDBLAD_CONTEXT_METADATA_KEY, None)
        else:
            self._metadata[AXIS1_LOCAL_LINDBLAD_CONTEXT_METADATA_KEY] = spec.to_manifest()
        return self

    def build(self) -> CircuitIR:
        return CircuitIR(
            num_qubits=self.num_qubits,
            steps=tuple(self._steps),
            metadata=dict(self._metadata),
        )

    def _validate_targets(self, targets: tuple[int, ...]) -> None:
        _validate_targets(self.num_qubits, targets)

    def _require_known_keys(self, keys: tuple[str, ...]) -> None:
        _require_known_keys(self._keys_seen, keys)
