from __future__ import annotations

"""Record-schema and manifest guards for simulator frontend artifacts."""

from dataclasses import dataclass
from typing import Any

from . import stim_io

ALLOWED_BACKENDS = {"stim"}
ALLOWED_REPRESENTABILITY = {"stim_pauli"}
EVALUATOR_ONLY = "evaluator_only"


@dataclass(frozen=True)
class RecordSchema:
    """Detector/observable schema carried by one compiled frontend circuit."""

    num_qubits: int
    num_measurements: int
    num_detectors: int
    num_observables: int
    measurement_keys: tuple[str, ...] = ()
    detector_names: tuple[str, ...] = ()
    observable_names: tuple[str, ...] = ()

    @classmethod
    def from_stim(cls, circuit) -> "RecordSchema":
        counts = stim_io.counts(circuit)
        return cls(
            num_qubits=counts.num_qubits,
            num_measurements=counts.num_measurements,
            num_detectors=counts.num_detectors,
            num_observables=counts.num_observables,
        )

    @classmethod
    def from_circuit_ir(cls, circuit, stim_circuit) -> "RecordSchema":
        counts = stim_io.counts(stim_circuit)
        if counts.num_qubits != int(circuit.num_qubits):
            raise ValueError(
                f"Stim circuit uses {counts.num_qubits} qubits, but CircuitIR declares "
                f"{circuit.num_qubits}"
            )
        return cls(
            num_qubits=counts.num_qubits,
            num_measurements=counts.num_measurements,
            num_detectors=counts.num_detectors,
            num_observables=counts.num_observables,
            measurement_keys=tuple(circuit.measurement_keys),
            detector_names=tuple(circuit.detector_names),
            observable_names=tuple(circuit.observable_names),
        )

    @property
    def detector_bit_width(self) -> int:
        return self.num_detectors

    @property
    def observable_bit_width(self) -> int:
        return self.num_observables

    def to_manifest(self) -> dict[str, Any]:
        return {
            "num_qubits": self.num_qubits,
            "num_measurements": self.num_measurements,
            "num_detectors": self.num_detectors,
            "num_observables": self.num_observables,
            "detector_bit_width": self.detector_bit_width,
            "observable_bit_width": self.observable_bit_width,
            "measurement_keys": list(self.measurement_keys),
            "detector_names": list(self.detector_names),
            "observable_names": list(self.observable_names),
        }


def require_frontend_representability(*, backend: str, representability: str) -> None:
    """Refuse classes this Stim frontend cannot honestly represent."""

    if backend not in ALLOWED_BACKENDS:
        raise ValueError(f"unsupported simulator backend {backend!r}; allowed={sorted(ALLOWED_BACKENDS)}")
    if representability not in ALLOWED_REPRESENTABILITY:
        raise ValueError(
            f"unsupported frontend representability {representability!r}; "
            f"allowed={sorted(ALLOWED_REPRESENTABILITY)}"
        )


def require_stim_circuit(circuit, *, label: str):
    import stim

    if not isinstance(circuit, stim.Circuit):
        raise TypeError(f"{label} must be stim.Circuit, got {type(circuit)!r}")
    return circuit


def require_matching_schemas(ideal_circuit, noisy_circuit) -> RecordSchema:
    """Require ideal/noisy Stim circuits to expose the same record schema."""

    ideal = RecordSchema.from_stim(ideal_circuit)
    noisy = RecordSchema.from_stim(noisy_circuit)
    if ideal != noisy:
        raise ValueError(
            "ideal/noisy Stim circuits must have identical record schema; "
            f"ideal={ideal.to_manifest()} noisy={noisy.to_manifest()}"
        )
    return noisy


def validate_evaluator_sidecars(sidecars: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    """Validate evaluator-only truth sidecars so they cannot enter emitted-record payloads."""

    out: list[dict[str, Any]] = []
    for raw in sidecars:
        item = dict(raw)
        if item.get("visibility") != EVALUATOR_ONLY:
            raise ValueError(
                "truth sidecars must be marked visibility='evaluator_only'; "
                f"got {item!r}"
            )
        if "name" not in item or "path" not in item:
            raise ValueError(f"truth sidecar needs name and path: {item!r}")
        out.append(item)
    return tuple(out)


def b8_manifest_entry(filename: str, *, bits_per_shot: int) -> dict[str, Any]:
    """Manifest entry for a possibly omitted `.b8` artifact."""

    bits = int(bits_per_shot)
    if bits < 0:
        raise ValueError(f"bits_per_shot must be non-negative, got {bits}")
    if bits == 0:
        return {
            "file": None,
            "bits_per_shot": 0,
            "packed_bytes_per_shot": 0,
            "omitted_reason": "zero_bit_width",
        }
    return {
        "file": filename,
        "bits_per_shot": bits,
        "packed_bytes_per_shot": (bits + 7) // 8,
    }
