from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import stim

from scope_static.google.inventory import DATASET_SURFACE_SET1


def write_tiny_google_s3_dataset(tmp_path: Path, *, contexts: int = 3) -> Path:
    root = tmp_path / DATASET_SURFACE_SET1 / DATASET_SURFACE_SET1
    for idx in range(int(contexts)):
        leaf = root / f"sample_{idx:02d}" / "d3_at_q5_5" / "X" / "r13"
        decoder = leaf / "decoding_results" / "correlated_matching_decoder_with_si1000_prior"
        decoder.mkdir(parents=True, exist_ok=True)
        circuit = stim.Circuit(
            """
            QUBIT_COORDS(0, 0) 0
            QUBIT_COORDS(1, 0) 1
            R 0 1
            TICK
            CX sweep[0] 0
            TICK
            M 0
            DETECTOR(0, 0, 0) rec[-1]
            OBSERVABLE_INCLUDE(0) rec[-1]
            """
        )
        (leaf / "circuit_ideal.stim").write_text(str(circuit), encoding="utf-8")
        (leaf / "circuit_noisy_si1000.stim").write_text(str(circuit), encoding="utf-8")
        (leaf / "metadata.json").write_text(
            json.dumps(
                {
                    "basis": "X",
                    "distance": 3,
                    "rounds": 13,
                    "shots": 4,
                    "data_qubit_coords": [[0, 0]],
                    "meas_qubit_coords": [[1, 0]],
                }
            ),
            encoding="utf-8",
        )
        _write_b8(leaf / "detection_events.b8", [[0], [1], [0], [1]])
        _write_b8(leaf / "obs_flips_actual.b8", [[0], [0], [1], [1]])
        _write_b8(leaf / "measurements.b8", [[0], [1], [1], [0]])
        _write_b8(leaf / "sweep_bits.b8", [[0], [1], [0], [1]])
        _write_b8(decoder / "obs_flips_predicted.b8", [[0], [1], [1], [0]])
        (decoder / "error_model.dem").write_text("error(0.1) D0\nerror(0.2) D0 L0\n", encoding="utf-8")
    return tmp_path / DATASET_SURFACE_SET1


def _write_b8(path: Path, rows: list[list[int]]) -> None:
    data = np.array(rows, dtype=np.bool_)
    stim.write_shot_data_file(path=str(path), data=data, format="b8", num_measurements=data.shape[1])

