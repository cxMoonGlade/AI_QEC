"""Label-free hardware observation container (the M3 calibration input).

OBSERVATIONS ONLY: packed detection events / measurements / sweep bits /
observable flips + circuit context + basis/sample provenance. The release's
``decoding_results/`` artifacts (RL DEM prior, predicted flips) are EXCLUDED by
construction — they are evaluator material, reachable only through
``RepCodeD29.evaluator_decoding_artifacts`` (isolation contract, module README).
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from qec_twin.hardware.b8_io import DEFAULT_CHUNK_SHOTS, iter_b8_chunks, read_b8
from qec_twin.hardware.dataset import (
    NUM_DETECTORS,
    NUM_MEASUREMENTS,
    NUM_OBSERVABLES,
    NUM_SWEEP_BITS,
    RepCodeD29,
)


@dataclass(frozen=True)
class HardwareObservations:
    """One ``(basis, sample)`` acquisition as label-free observations."""

    basis: str
    sample: int
    num_shots: int
    num_detectors: int
    num_measurements: int
    num_sweep_bits: int
    num_observables: int
    detection_events_path: Path
    measurements_path: Path
    sweep_bits_path: Path
    obs_flips_path: Path
    circuit_ideal_path: Path
    circuit_noisy_path: Path
    provenance: dict = field(default_factory=dict)

    def iter_detection_chunks(
        self, *, chunk_shots: int = DEFAULT_CHUNK_SHOTS
    ) -> Iterator[tuple[int, np.ndarray]]:
        return iter_b8_chunks(
            self.detection_events_path, self.num_detectors, chunk_shots=chunk_shots
        )

    def iter_measurement_chunks(
        self, *, chunk_shots: int = DEFAULT_CHUNK_SHOTS
    ) -> Iterator[tuple[int, np.ndarray]]:
        return iter_b8_chunks(
            self.measurements_path, self.num_measurements, chunk_shots=chunk_shots
        )

    def read_sweep_bits(self, shot_slice=None) -> np.ndarray:
        return read_b8(self.sweep_bits_path, self.num_sweep_bits, shot_slice)

    def read_obs_flips(self, shot_slice=None) -> np.ndarray:
        return read_b8(self.obs_flips_path, self.num_observables, shot_slice)


def observations_from_dataset(ds: RepCodeD29, basis: str, sample: int) -> HardwareObservations:
    """Build the container; asserts the P1 structure integers on load."""

    sizes = ds.validate_structure(basis, sample)
    paths = ds.paths(basis, sample)
    num_shots = sizes["detection_events.b8"] // ((NUM_DETECTORS + 7) // 8)
    return HardwareObservations(
        basis=basis,
        sample=int(sample),
        num_shots=int(num_shots),
        num_detectors=NUM_DETECTORS,
        num_measurements=NUM_MEASUREMENTS,
        num_sweep_bits=NUM_SWEEP_BITS,
        num_observables=NUM_OBSERVABLES,
        detection_events_path=paths.detection_events,
        measurements_path=paths.measurements,
        sweep_bits_path=paths.sweep_bits,
        obs_flips_path=paths.obs_flips_actual,
        circuit_ideal_path=paths.circuit_ideal,
        circuit_noisy_path=paths.circuit_noisy_si1000,
        provenance={
            "dataset": "google_72Q_repetition_code_d29",
            "release_family": "zenodo_13273331",
            "basis": basis,
            "sample": f"sample_{int(sample):02d}",
        },
    )
