"""Local Google d=29 repetition-code release (R2-lite rung; ADR 0007).

Layout: ``{X,Z}/sample_00..99/`` with ``circuit_ideal.stim``,
``circuit_noisy_si1000.stim``, ``measurements.b8``, ``sweep_bits.b8``,
``detection_events.b8``, ``obs_flips_actual.b8``, ``metadata.json`` and the
evaluator-only ``decoding_results/`` subtree. All ``.b8`` artifacts are stim
bit-packed (little-endian within bytes, each shot padded to a byte boundary).
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

HW_DATA_ENV = "QEC_TWIN_HW_DATA"
REP29_DIRNAME = "google_72Q_repetition_code_d29"

BASES = ("X", "Z")
NUM_SAMPLES = 100
NUM_SHOTS = 100_000

DISTANCE = 29
NUM_CHAINS = 28
NUM_DETECTOR_LAYERS = 1002  # 1 init + 1000 bulk + 1 final
NUM_ANCILLA_ROUNDS = 1001
NUM_DETECTORS = NUM_CHAINS * NUM_DETECTOR_LAYERS  # 28_056
NUM_MEASUREMENTS = NUM_CHAINS * NUM_ANCILLA_ROUNDS + DISTANCE  # 28_057
NUM_OBSERVABLES = 1
NUM_SWEEP_BITS = DISTANCE  # 29

DETECTOR_BYTES_PER_SHOT = 3507
MEASUREMENT_BYTES_PER_SHOT = 3508
SWEEP_BYTES_PER_SHOT = 4
OBSERVABLE_BYTES_PER_SHOT = 1

RL_DECODING_SUBDIR = Path("decoding_results") / "MWPM_decoder_with_RL_optimized_prior"

_B8_STRUCTURE = {
    "detection_events.b8": DETECTOR_BYTES_PER_SHOT,
    "measurements.b8": MEASUREMENT_BYTES_PER_SHOT,
    "sweep_bits.b8": SWEEP_BYTES_PER_SHOT,
    "obs_flips_actual.b8": OBSERVABLE_BYTES_PER_SHOT,
}


def resolve_rep29_root() -> Path | None:
    """Locate the local d=29 release; ``None`` (never raises) when unset/absent."""

    parent = os.environ.get(HW_DATA_ENV)
    if not parent:
        return None
    root = Path(parent) / REP29_DIRNAME
    return root if root.is_dir() else None


@dataclass(frozen=True)
class SamplePaths:
    """Learner-facing artifact paths for one ``(basis, sample)`` acquisition."""

    basis: str
    sample: int
    circuit_ideal: Path
    circuit_noisy_si1000: Path
    measurements: Path
    sweep_bits: Path
    detection_events: Path
    obs_flips_actual: Path
    metadata: Path


@dataclass(frozen=True)
class EvaluatorDecodingArtifacts:
    """EVALUATOR-ONLY shipped decoding artifacts (RL-optimized DEM prior + its
    predicted observable flips). Baseline/scoring material under the isolation
    contract — never to be mixed into learner-facing observation containers."""

    basis: str
    sample: int
    error_model_dem: Path
    obs_flips_predicted: Path
    evaluator_only: bool = True


class RepCodeD29:
    """The d=29 repetition-code release as an enumerable dataset object."""

    def __init__(self, root: Path) -> None:
        root = Path(root)
        if not root.is_dir():
            raise FileNotFoundError(f"dataset root not found: {root}")
        self.root = root

    @classmethod
    def from_env(cls) -> "RepCodeD29":
        root = resolve_rep29_root()
        if root is None:
            raise FileNotFoundError(f"set {HW_DATA_ENV} to the parent of {REP29_DIRNAME}/")
        return cls(root)

    @property
    def bases(self) -> tuple[str, ...]:
        return tuple(b for b in BASES if (self.root / b).is_dir())

    def samples(self, basis: str) -> tuple[int, ...]:
        base_dir = self.root / basis
        found = []
        for entry in sorted(base_dir.iterdir()):
            match = re.fullmatch(r"sample_(\d+)", entry.name)
            if match and entry.is_dir():
                found.append(int(match.group(1)))
        return tuple(found)

    def sample_dir(self, basis: str, sample: int) -> Path:
        return self.root / basis / f"sample_{int(sample):02d}"

    def paths(self, basis: str, sample: int) -> SamplePaths:
        d = self.sample_dir(basis, sample)
        if not d.is_dir():
            raise FileNotFoundError(f"sample directory not found: {d}")
        return SamplePaths(
            basis=basis,
            sample=int(sample),
            circuit_ideal=d / "circuit_ideal.stim",
            circuit_noisy_si1000=d / "circuit_noisy_si1000.stim",
            measurements=d / "measurements.b8",
            sweep_bits=d / "sweep_bits.b8",
            detection_events=d / "detection_events.b8",
            obs_flips_actual=d / "obs_flips_actual.b8",
            metadata=d / "metadata.json",
        )

    def load_metadata(self, basis: str, sample: int) -> dict:
        with open(self.paths(basis, sample).metadata, encoding="utf-8") as handle:
            return json.load(handle)

    def validate_structure(self, basis: str, sample: int, *, num_shots: int = NUM_SHOTS) -> dict[str, int]:
        """Assert the P1 structure integers on the b8 artifacts (exact file sizes)."""

        d = self.sample_dir(basis, sample)
        sizes: dict[str, int] = {}
        for name, bytes_per_shot in _B8_STRUCTURE.items():
            path = d / name
            expected = int(num_shots) * int(bytes_per_shot)
            actual = path.stat().st_size
            if actual != expected:
                raise ValueError(
                    f"P1 structure violation: {path} has {actual} bytes, "
                    f"expected {expected} ({num_shots} shots x {bytes_per_shot} B/shot)"
                )
            sizes[name] = actual
        return sizes

    def evaluator_decoding_artifacts(self, basis: str, sample: int) -> EvaluatorDecodingArtifacts:
        """EVALUATOR-ONLY accessor for the shipped RL-prior decoding artifacts."""

        d = self.sample_dir(basis, sample) / RL_DECODING_SUBDIR
        return EvaluatorDecodingArtifacts(
            basis=basis,
            sample=int(sample),
            error_model_dem=d / "error_model.dem",
            obs_flips_predicted=d / "obs_flips_predicted.b8",
        )


def metadata_qubit_order(metadata: dict) -> list | None:
    """Tolerant lookup of the chain-ordered qubit listing inside metadata.json."""

    for key in ("qubit_order", "qubits", "qubit_coords", "measure_qubit_order", "qubit_layout"):
        value = metadata.get(key)
        if isinstance(value, (list, tuple)) and value:
            return list(value)
    return None
