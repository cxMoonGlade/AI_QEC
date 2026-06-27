from __future__ import annotations

"""User-facing simulator frontend.

This is the first product-surface slice: custom CircuitIR -> Stim-compatible
artifacts -> `.b8` detector/observable records -> DEM/PyMatching decode summary.
Analog coupling backends will attach below this facade without changing the
artifact surface.
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from qec_twin.hardware import b8_io, m4_decode
from qec_twin.simulator import stim_io
from qec_twin.simulator.artifacts import (
    ArtifactPaths,
    artifact_paths,
    clear_known_artifacts,
    file_sha256,
    record_summary,
    write_b8_optional,
    write_json,
)
from qec_twin.simulator.circuit_ir import CircuitIR
from qec_twin.simulator.noise_spec import FrontendNoiseSpec
from qec_twin.simulator.record_schema import b8_manifest_entry
from qec_twin.simulator.stim_source import (
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
    decoder_results: dict
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
        """Read decoder-predicted logical-observable flips."""

        return _load_b8_from_manifest(
            self.paths.obs_flips_predicted,
            manifest=self.manifest,
            artifact_key="obs_flips_predicted",
        )


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
        seed: int = 0,
        decoder: str = "pymatching",
    ) -> SimulationResult:
        """Run the Stim-compatible frontend and write standard simulator artifacts."""

        if int(shots) <= 0:
            raise ValueError("shots must be positive")
        if decoder != "pymatching":
            raise ValueError("only decoder='pymatching' is implemented in the frontend slice")

        compiled = self.source.compile(noise)
        ideal_circuit = compiled.ideal_circuit
        noisy_circuit = compiled.noisy_circuit
        schema = compiled.record_schema
        if schema is None:  # pragma: no cover - CompiledCircuit validation sets this
            raise ValueError("compiled circuit is missing record_schema")

        paths = artifact_paths(out_dir)
        paths.out_dir.mkdir(parents=True, exist_ok=True)
        clear_known_artifacts(paths)

        dem = stim_io.detector_error_model(noisy_circuit, decompose_errors=True)

        ideal_det, ideal_obs = stim_io.sample_detector_records(
            ideal_circuit, shots=int(shots), seed=int(seed)
        )
        noisy_det, noisy_obs = stim_io.sample_detector_records(
            noisy_circuit, shots=int(shots), seed=int(seed)
        )

        preds = m4_decode.decode_dem(dem, noisy_det)
        decoder_results = _decoder_summary(preds, noisy_obs)

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
        pred_path = write_b8_optional(paths.obs_flips_predicted, preds)
        write_json(paths.sample_summary_ideal, sample_summary_ideal)
        write_json(paths.sample_summary_noisy, sample_summary_noisy)
        write_json(paths.theory_prediction, theory_prediction)
        write_json(paths.decoder_results, decoder_results)

        artifacts = {
            "circuit_ideal": _file_entry(paths.circuit_ideal),
            "circuit_noisy_pauli": _file_entry(paths.circuit_noisy_pauli),
            "detector_error_model": _file_entry(paths.detector_error_model),
            "detection_events": _b8_entry(det_path, schema.detector_bit_width),
            "obs_flips_actual": _b8_entry(obs_path, schema.observable_bit_width),
            "obs_flips_predicted": _b8_entry(pred_path, schema.observable_bit_width),
            "ideal_detection_events": _b8_entry(ideal_det_path, schema.detector_bit_width),
            "ideal_obs_flips_actual": _b8_entry(ideal_obs_path, schema.observable_bit_width),
            "sample_summary_ideal": _file_entry(paths.sample_summary_ideal),
            "sample_summary_noisy": _file_entry(paths.sample_summary_noisy),
            "theory_prediction": _file_entry(paths.theory_prediction),
            "decoder_results": _file_entry(paths.decoder_results),
        }
        manifest = {
            "schema": "qec_twin.simulator_frontend.v1",
            "backend": compiled.backend,
            "representability": compiled.representability,
            "source_type": compiled.source_type,
            "shots": int(shots),
            "seed": int(seed),
            "decoder": decoder,
            "decoder_provenance": m4_decode.pymatching_provenance(),
            "num_qubits": schema.num_qubits,
            "num_measurements": schema.num_measurements,
            "num_detectors": schema.num_detectors,
            "num_observables": schema.num_observables,
            "record_schema": schema.to_manifest(),
            "circuit_metadata": dict(compiled.metadata),
            "noise": compiled.noise_manifest,
            "evaluator_sidecars": list(compiled.evaluator_sidecars),
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
        seed: int = 0,
        decoder: str = "pymatching",
    ) -> SimulationResult:
        """Run the circuit with no simulator-added noise."""

        compiled = self.source.compile(None)
        if compiled.noise_manifest is not None or str(compiled.ideal_circuit) != str(compiled.noisy_circuit):
            raise ValueError(
                "run_noiseless requires the source to compile to identical ideal/noisy circuits "
                "with no noise manifest; use run(noise=None) for pre-noised sources"
            )
        return Simulator(compiled).run(shots=shots, out_dir=out_dir, noise=None, seed=seed, decoder=decoder)


def simulate_noiseless(
    circuit: CircuitIR | CircuitSource | CompiledCircuit,
    *,
    shots: int,
    out_dir: str | Path,
    seed: int = 0,
    decoder: str = "pymatching",
) -> SimulationResult:
    """Convenience wrapper for a no-noise frontend simulation."""

    return Simulator(circuit).run_noiseless(
        shots=shots,
        out_dir=out_dir,
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
        raise ValueError(f"manifest artifact {artifact_key!r} has positive width but no file")
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


def _b8_entry(path, bits_per_shot: int) -> dict:
    if path is None and int(bits_per_shot) > 0:
        raise ValueError(f"positive-width .b8 artifact was not written: bits={bits_per_shot}")
    filename = path.name if path is not None else ""
    entry = b8_manifest_entry(filename, bits_per_shot=bits_per_shot)
    if path is not None:
        entry["sha256"] = file_sha256(path)
    return entry
