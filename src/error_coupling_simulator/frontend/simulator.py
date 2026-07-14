from __future__ import annotations

"""User-facing simulator frontend.

This is the first product-surface slice: custom CircuitIR -> Stim-compatible
artifacts -> `.b8` detector/observable records.  PyMatching is an opt-in,
external reduction of that record, never a prerequisite for emitting it.
Analog coupling backends will attach below this facade without changing the
record contract.
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ..carrier.records import RecordBatch
from ..source.process import SourceTimeline
from . import b8_io, decoder as m4_decode, stim_io
from .artifacts import (
    ArtifactPaths,
    artifact_paths,
    clear_known_artifacts,
    file_sha256,
    record_summary,
    write_b8_optional,
    write_json,
)
from .circuit_ir import CircuitIR
from .noise_spec import FrontendNoiseSpec
from .record_schema import b8_manifest_entry, validate_evaluator_sidecars
from .source_sidecar import (
    SourceTimelineBinding,
    build_source_timeline_binding_manifest,
    load_source_timeline_from_manifest,
    source_binding_public_stub,
    write_source_timeline_sidecar,
)
from .stim_source import (
    CircuitIRSource,
    CircuitSource,
    CompiledCircuit,
    CompiledCircuitSource,
)


@dataclass(frozen=True)
class SimulationResult:
    """Summary returned by `Simulator.run`."""

    paths: ArtifactPaths
    sample_summary_ideal: dict
    sample_summary_noisy: dict
    theory_prediction: dict
    decoder_results: dict | None
    manifest: dict

    def load_detection_events(self, *, ideal: bool = False) -> np.ndarray:
        """Read detector records from the run's `.b8` artifact."""

        key = "ideal_detection_events" if ideal else "detection_events"
        path = self.paths.ideal_detection_events if ideal else self.paths.detection_events
        return _load_b8_from_manifest(
            path,
            manifest=self.manifest,
            artifact_key=key,
        )

    def load_observable_flips(self, *, ideal: bool = False) -> np.ndarray:
        """Read actual logical-observable flips from the run's `.b8` artifact."""

        key = "ideal_obs_flips_actual" if ideal else "obs_flips_actual"
        path = self.paths.ideal_obs_flips_actual if ideal else self.paths.obs_flips_actual
        return _load_b8_from_manifest(
            path,
            manifest=self.manifest,
            artifact_key=key,
        )

    def load_predicted_observable_flips(self) -> np.ndarray:
        """Read decoder predictions from a run that explicitly requested decoding.

        A positive-width prediction artifact is absent from record-only runs and
        raises the manifest's stable ``decoder_not_requested`` contract error.
        """

        return _load_b8_from_manifest(
            self.paths.obs_flips_predicted,
            manifest=self.manifest,
            artifact_key="obs_flips_predicted",
        )

    def load_record_batch(self, *, ideal: bool = False) -> RecordBatch:
        """Load this run through the backend-neutral simulator record contract."""

        return RecordBatch(
            det=self.load_detection_events(ideal=ideal),
            obs=self.load_observable_flips(ideal=ideal),
            provenance={
                "backend": self.manifest["backend"],
                "representability": (
                    "stim_ideal" if ideal else self.manifest["representability"]
                ),
                "record_semantics": "temporal_detector_events",
                "source_type": self.manifest["source_type"],
            },
        )

    def load_source_timeline(self) -> SourceTimeline:
        """Read the evaluator-only source timeline sidecar for this run."""

        return load_source_timeline_from_manifest(self.paths.out_dir, self.manifest)


class Simulator:
    """Small frontend facade for Stim-compatible QEC simulator artifacts."""

    def __init__(self, circuit: CircuitIR | CircuitSource | CompiledCircuit) -> None:
        if isinstance(circuit, CircuitIR):
            self.source: CircuitSource = CircuitIRSource(circuit)
        elif isinstance(circuit, CompiledCircuit):
            self.source = CompiledCircuitSource(circuit)
        elif isinstance(circuit, CircuitSource):
            self.source = circuit
        else:
            raise TypeError(
                "Simulator expects CircuitIR, CompiledCircuit, or a CircuitSource with compile(...), "
                f"got {type(circuit)!r}"
            )

    def run(
        self,
        *,
        shots: int,
        out_dir: str | Path,
        noise: FrontendNoiseSpec | None = None,
        source_timeline: SourceTimeline | None = None,
        source_binding: SourceTimelineBinding | None = None,
        seed: int = 0,
        decoder: str | None = None,
    ) -> SimulationResult:
        """Run the Stim-compatible frontend and write record-first artifacts.

        ``decoder=None`` is the core default: detector and observable records are
        emitted without importing PyMatching.  Pass ``decoder="pymatching"`` to
        request the optional external reduction and its prediction artifacts.
        """

        shot_count = _require_positive_int("shots", shots)
        if decoder is not None and (
            not isinstance(decoder, str) or decoder != "pymatching"
        ):
            raise ValueError(
                "decoder must be None or 'pymatching' in the frontend slice"
            )
        paths = artifact_paths(out_dir)
        paths.out_dir.mkdir(parents=True, exist_ok=True)
        clear_known_artifacts(paths)

        noise_source_timeline = getattr(noise, "source_timeline", None)
        if noise_source_timeline is not None:
            if source_timeline is not None and source_timeline.to_manifest() != noise_source_timeline.to_manifest():
                raise ValueError("noise source_timeline and run source_timeline do not match")
            source_timeline = noise_source_timeline
        noise_source_binding = getattr(noise, "source_binding", None)
        if noise_source_binding is not None:
            if source_binding is not None and source_binding != noise_source_binding:
                raise ValueError("noise source_binding and run source_binding do not match")
            source_binding = noise_source_binding

        compiled = self.source.compile(noise)
        ideal_circuit = compiled.ideal_circuit
        noisy_circuit = compiled.noisy_circuit
        schema = compiled.record_schema
        if schema is None:  # pragma: no cover - CompiledCircuit validation sets this
            raise ValueError("compiled circuit is missing record_schema")
        source_projection_audit = getattr(compiled, "source_projection_audit", None)
        source_projection_status = (
            source_projection_audit.get("execution_status")
            if isinstance(source_projection_audit, dict)
            else None
        )
        source_binding_manifest = None
        source_binding_stub = None
        if source_timeline is not None:
            source_binding_manifest = build_source_timeline_binding_manifest(
                source_timeline,
                binding=source_binding,
                compiled_metadata=compiled.metadata,
                shots=shot_count,
                execution_status=source_projection_status,
                projection_audit=source_projection_audit,
            )
            source_binding_stub = source_binding_public_stub(source_binding_manifest)

        dem_decompose_errors = decoder == "pymatching"
        dem = stim_io.detector_error_model(
            noisy_circuit,
            decompose_errors=dem_decompose_errors,
        )

        ideal_det, ideal_obs = stim_io.sample_detector_records(
            ideal_circuit, shots=shot_count, seed=int(seed)
        )
        noisy_det, noisy_obs = stim_io.sample_detector_records(
            noisy_circuit, shots=shot_count, seed=int(seed)
        )

        if decoder is None:
            preds = None
            decoder_results = None
            decoder_provenance = None
        else:
            preds = m4_decode.decode_dem(dem, noisy_det)
            decoder_results = _decoder_summary(preds, noisy_obs)
            decoder_provenance = m4_decode.pymatching_provenance()

        sample_summary_ideal = record_summary(ideal_det, ideal_obs)
        sample_summary_ideal.update(
            {"representability": "stim_ideal", "estimator": "finite_shot_sample"}
        )
        sample_summary_noisy = record_summary(noisy_det, noisy_obs)
        sample_summary_noisy.update(
            {
                "representability": "stim_pauli",
                "estimator": "finite_shot_sample",
                "decoder": decoder_results,
            }
        )
        theory_prediction = {
            "available": False,
            "reason": (
                "stim detector sampling frontend currently reports finite-shot summaries; "
                "exact/analytic theory predictions require a backend-declared method"
            ),
        }

        stim_io.write_stim_circuit(ideal_circuit, paths.circuit_ideal)
        stim_io.write_stim_circuit(noisy_circuit, paths.circuit_noisy_pauli)
        stim_io.write_detector_error_model(dem, paths.detector_error_model)
        ideal_det_path = write_b8_optional(paths.ideal_detection_events, ideal_det)
        ideal_obs_path = write_b8_optional(paths.ideal_obs_flips_actual, ideal_obs)
        det_path = write_b8_optional(paths.detection_events, noisy_det)
        obs_path = write_b8_optional(paths.obs_flips_actual, noisy_obs)
        pred_path = (
            None
            if preds is None
            else write_b8_optional(paths.obs_flips_predicted, preds)
        )
        write_json(paths.sample_summary_ideal, sample_summary_ideal)
        write_json(paths.sample_summary_noisy, sample_summary_noisy)
        write_json(paths.theory_prediction, theory_prediction)
        if decoder_results is not None:
            write_json(paths.decoder_results, decoder_results)

        evaluator_sidecars = list(compiled.evaluator_sidecars)
        source_artifacts = None
        if source_timeline is not None:
            source_artifacts, source_sidecar, source_binding_manifest, source_binding_stub = write_source_timeline_sidecar(
                source_timeline,
                paths,
                binding=source_binding,
                compiled_metadata=compiled.metadata,
                shots=shot_count,
                execution_status=source_projection_status,
                projection_audit=source_projection_audit,
            )
            evaluator_sidecars.append(source_sidecar)
        evaluator_sidecars = list(validate_evaluator_sidecars(tuple(evaluator_sidecars)))

        artifacts = {
            "circuit_ideal": _file_entry(paths.circuit_ideal),
            "circuit_noisy_pauli": _file_entry(paths.circuit_noisy_pauli),
            "detector_error_model": _dem_entry(
                paths.detector_error_model,
                decompose_errors=dem_decompose_errors,
            ),
            "detection_events": _b8_entry(det_path, schema.detector_bit_width),
            "obs_flips_actual": _b8_entry(obs_path, schema.observable_bit_width),
            "obs_flips_predicted": (
                _omitted_b8_entry(
                    schema.observable_bit_width,
                    reason="decoder_not_requested",
                )
                if decoder is None
                else _b8_entry(pred_path, schema.observable_bit_width)
            ),
            "ideal_detection_events": _b8_entry(ideal_det_path, schema.detector_bit_width),
            "ideal_obs_flips_actual": _b8_entry(ideal_obs_path, schema.observable_bit_width),
            "sample_summary_ideal": _file_entry(paths.sample_summary_ideal),
            "sample_summary_noisy": _file_entry(paths.sample_summary_noisy),
            "theory_prediction": _file_entry(paths.theory_prediction),
            "decoder_results": (
                _omitted_file_entry(reason="decoder_not_requested")
                if decoder is None
                else _file_entry(paths.decoder_results)
            ),
        }
        if source_artifacts is not None:
            artifacts.update(source_artifacts)
        manifest = {
            "schema": "qec_twin.simulator_frontend.v1",
            "backend": compiled.backend,
            "representability": compiled.representability,
            "source_type": compiled.source_type,
            "shots": shot_count,
            "seed": int(seed),
            "decoder": decoder,
            "decoder_provenance": decoder_provenance,
            "num_qubits": schema.num_qubits,
            "num_measurements": schema.num_measurements,
            "num_detectors": schema.num_detectors,
            "num_observables": schema.num_observables,
            "record_schema": schema.to_manifest(),
            "circuit_metadata": dict(compiled.metadata),
            "noise": compiled.noise_manifest,
            "evaluator_sidecars": evaluator_sidecars,
            "source_binding": source_binding_stub,
            "artifacts": artifacts,
        }
        write_json(paths.manifest, manifest)

        return SimulationResult(
            paths=paths,
            sample_summary_ideal=sample_summary_ideal,
            sample_summary_noisy=sample_summary_noisy,
            theory_prediction=theory_prediction,
            decoder_results=decoder_results,
            manifest=manifest,
        )

    def run_noiseless(
        self,
        *,
        shots: int,
        out_dir: str | Path,
        source_timeline: SourceTimeline | None = None,
        source_binding: SourceTimelineBinding | None = None,
        seed: int = 0,
        decoder: str | None = None,
    ) -> SimulationResult:
        """Run without simulator-added noise; decoding remains opt-in."""

        compiled = self.source.compile(None)
        if compiled.noise_manifest is not None or str(compiled.ideal_circuit) != str(compiled.noisy_circuit):
            raise ValueError(
                "run_noiseless requires the source to compile to identical ideal/noisy circuits "
                "with no noise manifest; use run(noise=None) for pre-noised sources"
            )
        return Simulator(compiled).run(
            shots=shots,
            out_dir=out_dir,
            noise=None,
            source_timeline=source_timeline,
            source_binding=source_binding,
            seed=seed,
            decoder=decoder,
        )


def simulate_noiseless(
    circuit: CircuitIR | CircuitSource | CompiledCircuit,
    *,
    shots: int,
    out_dir: str | Path,
    source_timeline: SourceTimeline | None = None,
    source_binding: SourceTimelineBinding | None = None,
    seed: int = 0,
    decoder: str | None = None,
) -> SimulationResult:
    """Convenience wrapper for a record-first no-noise frontend simulation."""

    return Simulator(circuit).run_noiseless(
        shots=shots,
        out_dir=out_dir,
        source_timeline=source_timeline,
        source_binding=source_binding,
        seed=seed,
        decoder=decoder,
    )


def _decoder_summary(predictions: np.ndarray, observables: np.ndarray) -> dict:
    preds = np.asarray(predictions, dtype=np.uint8)
    obs = np.asarray(observables, dtype=np.uint8)
    if obs.ndim != 2:
        raise ValueError(f"observables must be [shots, num_observables], got {obs.shape}")
    if preds.shape != obs.shape:
        raise ValueError(f"decoder predictions shape {preds.shape} != observables shape {obs.shape}")
    if obs.shape[1] == 0:
        return {
            "num_shots": int(obs.shape[0]),
            "num_observables": 0,
            "per_observable_ler": [],
            "any_observable_ler": None,
        }
    logical_errors = preds ^ obs
    return {
        "num_shots": int(obs.shape[0]),
        "num_observables": int(obs.shape[1]),
        "per_observable_ler": logical_errors.mean(axis=0).tolist(),
        "any_observable_ler": float(logical_errors.any(axis=1).mean()),
    }


def _load_b8_from_manifest(
    path: Path,
    *,
    manifest: dict,
    artifact_key: str,
) -> np.ndarray:
    entry = manifest["artifacts"][artifact_key]
    shots = int(manifest["shots"])
    bits = int(entry["bits_per_shot"])
    if bits == 0:
        return np.zeros((shots, 0), dtype=np.bool_)
    if entry["file"] is None:
        reason = entry.get("omitted_reason", "unspecified")
        raise ValueError(
            f"manifest artifact {artifact_key!r} was omitted: {reason}"
        )
    if path.name != entry["file"]:
        raise ValueError(
            f"manifest artifact {artifact_key!r} points to {entry['file']!r}, "
            f"but result path is {path.name!r}"
        )
    expected_sha = entry.get("sha256")
    actual_sha = file_sha256(path)
    if expected_sha is not None and actual_sha != expected_sha:
        raise ValueError(
            f"manifest artifact {artifact_key!r} sha256 mismatch: "
            f"manifest={expected_sha}, actual={actual_sha}"
        )
    records = b8_io.unpack_bits(b8_io.read_b8(path, bits), bits)
    if records.shape[0] != shots:
        raise ValueError(
            f"manifest declares {shots} shots for {artifact_key!r}, "
            f"but {path} contains {records.shape[0]}"
        )
    return records


def _file_entry(path) -> dict:
    return {"file": path.name, "sha256": file_sha256(path)}


def _dem_entry(path, *, decompose_errors: bool) -> dict:
    """Manifest entry declaring whether graphlike decomposition was requested."""

    return {
        **_file_entry(path),
        "decompose_errors": bool(decompose_errors),
    }


def _b8_entry(path, bits_per_shot: int) -> dict:
    if path is None and int(bits_per_shot) > 0:
        raise ValueError(f"positive-width .b8 artifact was not written: bits={bits_per_shot}")
    filename = path.name if path is not None else ""
    entry = b8_manifest_entry(filename, bits_per_shot=bits_per_shot)
    if path is not None:
        entry["sha256"] = file_sha256(path)
    return entry


def _omitted_b8_entry(bits_per_shot: int, *, reason: str) -> dict:
    """Manifest entry for a deliberately unrequested positive- or zero-width record."""

    bits = int(bits_per_shot)
    if bits < 0:
        raise ValueError(f"bits_per_shot must be non-negative, got {bits}")
    return {
        "file": None,
        "bits_per_shot": bits,
        "packed_bytes_per_shot": (bits + 7) // 8 if bits else 0,
        "omitted_reason": str(reason),
    }


def _omitted_file_entry(*, reason: str) -> dict:
    """Manifest entry for a deliberately unrequested non-record artifact."""

    return {"file": None, "omitted_reason": str(reason)}


def _require_positive_int(name: str, value: int) -> int:
    if isinstance(value, bool) or isinstance(value, (str, bytes)):
        raise ValueError(f"{name} must be a positive integer, got {value!r}")
    if isinstance(value, (int, np.integer)):
        out = int(value)
    elif isinstance(value, (float, np.floating)) and float(value).is_integer():
        out = int(value)
    else:
        raise ValueError(f"{name} must be a positive integer, got {value!r}")
    if out <= 0:
        raise ValueError(f"{name} must be a positive integer, got {value!r}")
    return out
