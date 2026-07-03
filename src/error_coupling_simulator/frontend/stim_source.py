from __future__ import annotations

"""Circuit-source adapters for the simulator frontend.

The simulator facade consumes compiled Stim circuits. These adapters keep the
source of those circuits explicit: keyed `CircuitIR`, imported Stim, and later
compiled `CodeSpec` objects can all feed the same artifact path without making
XZZX or Stim parsing part of the simulator core.
"""

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Protocol, runtime_checkable

from . import stim_io
from .circuit_ir import CircuitIR
from .metadata_guard import validate_public_metadata
from .noise_spec import (
    SOURCE_PROJECTION_AUDIT_METADATA_KEY,
    FrontendNoiseSpec,
    apply_stim_pauli_noise,
)
from .record_schema import (
    RecordSchema,
    require_frontend_representability,
    require_matching_schemas,
    require_stim_circuit,
    validate_evaluator_sidecars,
)


@dataclass(frozen=True)
class CompiledCircuit:
    """Stim-backed circuit pair ready for sampling, DEM export, and decoding."""

    ideal_circuit: object
    noisy_circuit: object
    metadata: dict
    source_type: str
    backend: str = "stim"
    representability: str = "stim_pauli"
    noise_manifest: dict | None = None
    record_schema: RecordSchema | None = None
    evaluator_sidecars: tuple[dict, ...] = ()
    source_projection_audit: dict | None = None

    def __post_init__(self) -> None:
        require_frontend_representability(
            backend=str(self.backend), representability=str(self.representability)
        )
        ideal = require_stim_circuit(self.ideal_circuit, label="ideal_circuit")
        noisy = require_stim_circuit(self.noisy_circuit, label="noisy_circuit")
        actual_schema = require_matching_schemas(ideal, noisy)
        schema = self.record_schema or actual_schema
        if (
            schema.num_qubits != actual_schema.num_qubits
            or schema.num_measurements != actual_schema.num_measurements
            or schema.num_detectors != actual_schema.num_detectors
            or schema.num_observables != actual_schema.num_observables
        ):
            raise ValueError(
                "record_schema counts do not match compiled Stim circuits; "
                f"record_schema={schema.to_manifest()} actual={actual_schema.to_manifest()}"
            )
        object.__setattr__(
            self,
            "metadata",
            validate_public_metadata(self.metadata, label="CompiledCircuit.metadata"),
        )
        object.__setattr__(
            self,
            "noise_manifest",
            validate_public_metadata(
                self.noise_manifest,
                label="CompiledCircuit.noise_manifest",
            )
            if self.noise_manifest is not None
            else None,
        )
        object.__setattr__(self, "source_type", str(self.source_type))
        object.__setattr__(self, "backend", str(self.backend))
        object.__setattr__(self, "representability", str(self.representability))
        object.__setattr__(self, "record_schema", schema)
        object.__setattr__(
            self,
            "evaluator_sidecars",
            validate_evaluator_sidecars(tuple(self.evaluator_sidecars)),
        )
        if self.source_projection_audit is not None:
            audit = dict(self.source_projection_audit)
            if audit.get("visibility") != "evaluator_only":
                raise ValueError("source_projection_audit must be visibility='evaluator_only'")
            object.__setattr__(self, "source_projection_audit", audit)


@runtime_checkable
class CircuitSource(Protocol):
    """Frontend source that can compile to simulator-ready Stim circuits."""

    def compile(self, noise: FrontendNoiseSpec | None = None) -> CompiledCircuit:
        """Compile the source under the requested frontend noise projection."""


@dataclass(frozen=True)
class CircuitIRSource:
    """Adapter for the keyed in-repo `CircuitIR` builder surface."""

    circuit: CircuitIR

    def compile(self, noise: FrontendNoiseSpec | None = None) -> CompiledCircuit:
        noisy_ir = apply_stim_pauli_noise(self.circuit, noise)
        ideal_circuit = stim_io.circuit_to_stim(self.circuit)
        noisy_circuit = stim_io.circuit_to_stim(noisy_ir)
        noise_manifest = None
        if noise is not None:
            noise_manifest = dict(noisy_ir.metadata.get("noise_projection", noise.to_manifest()))
        source_projection_audit = noisy_ir.metadata.get(SOURCE_PROJECTION_AUDIT_METADATA_KEY)
        return CompiledCircuit(
            ideal_circuit=ideal_circuit,
            noisy_circuit=noisy_circuit,
            metadata=dict(self.circuit.metadata),
            source_type="circuit_ir",
            noise_manifest=noise_manifest,
            record_schema=RecordSchema.from_circuit_ir(self.circuit, noisy_circuit),
            source_projection_audit=source_projection_audit,
        )


@dataclass(frozen=True)
class CompiledCircuitSource:
    """Adapter for an already-compiled circuit pair.

    Future code compilers can return `CompiledCircuit` directly. The simulator
    accepts it through this thin wrapper so the run path remains source-uniform.
    """

    compiled: CompiledCircuit

    def compile(self, noise: FrontendNoiseSpec | None = None) -> CompiledCircuit:
        if noise is not None and not noise.is_trivial:
            raise ValueError("cannot apply new noise to an already compiled circuit pair")
        return self.compiled


@dataclass(frozen=True)
class StimCircuitSource:
    """Adapter for imported or externally compiled Stim circuits.

    `ideal_circuit` and `noisy_circuit` are both Stim circuits. If only
    `ideal_circuit` is provided, it is used for both ideal and noisy artifacts
    when `noise` is None or trivial. Non-trivial `StimPauliNoiseSpec` insertion
    is deliberately unsupported for raw Stim sources in this slice; placement
    rules need the next compiler/location layer to be unambiguous.
    """

    ideal_circuit: object
    noisy_circuit: object | None = None
    metadata: dict | None = None

    @classmethod
    def from_file(
        cls,
        ideal_path: str | Path,
        *,
        noisy_path: str | Path | None = None,
        metadata: dict | None = None,
    ) -> "StimCircuitSource":
        meta = dict(metadata or {})
        meta["ideal_path"] = str(ideal_path)
        meta["ideal_sha256"] = _sha256_file(ideal_path)
        noisy = None
        if noisy_path is not None:
            meta["noisy_path"] = str(noisy_path)
            meta["noisy_sha256"] = _sha256_file(noisy_path)
            noisy = stim_io.load_stim_circuit(noisy_path)
        else:
            meta["noisy_is_ideal"] = True
        return cls(
            ideal_circuit=stim_io.load_stim_circuit(ideal_path),
            noisy_circuit=noisy,
            metadata=meta,
        )

    def compile(self, noise: FrontendNoiseSpec | None = None) -> CompiledCircuit:
        if noise is not None and not noise.is_trivial:
            raise NotImplementedError(
                "non-trivial StimPauliNoiseSpec placement on raw Stim sources requires "
                "the location-aware compiler slice; pass a pre-noised Stim circuit as noisy_circuit"
            )
        noise_manifest = noise.to_manifest() if noise is not None else None
        if self.noisy_circuit is not None and noise_manifest is None:
            noise_manifest = {
                "type": "pre_noised_stim_source",
                "source_type": "stim_circuit",
                "placement": "external",
            }
        return CompiledCircuit(
            ideal_circuit=self.ideal_circuit,
            noisy_circuit=self.noisy_circuit if self.noisy_circuit is not None else self.ideal_circuit,
            metadata=dict(self.metadata or {}),
            source_type="stim_circuit",
            noise_manifest=noise_manifest,
        )


def _sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()
