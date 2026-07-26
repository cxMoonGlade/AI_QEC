"""Emit a flattened stim rotated-surface-code memory circuit as JSON (runs in `ecs`).

Read-only probe. Writes one JSON file per distance into the scratchpad.
"""

import json
import sys
from pathlib import Path

import stim

OUT = Path(__file__).resolve().parent


def flatten(circuit):
    ops = []
    for inst in circuit.flattened():
        name = inst.name
        targets = inst.targets_copy()
        if name in ("QUBIT_COORDS", "SHIFT_COORDS", "TICK"):
            continue
        if name == "DETECTOR":
            ops.append({"op": "DETECTOR", "rec": [t.value for t in targets]})
        elif name == "OBSERVABLE_INCLUDE":
            ops.append(
                {
                    "op": "OBSERVABLE_INCLUDE",
                    "index": int(inst.gate_args_copy()[0]),
                    "rec": [t.value for t in targets],
                }
            )
        else:
            ops.append({"op": name, "q": [t.qubit_value for t in targets]})
    return ops


def main():
    for d in (3, 5):
        rounds = d
        c = stim.Circuit.generated(
            f"surface_code:rotated_memory_z", distance=d, rounds=rounds
        )
        payload = {
            "distance": d,
            "rounds": rounds,
            "num_qubits": c.num_qubits,
            "num_detectors": c.num_detectors,
            "num_observables": c.num_observables,
            "num_measurements": c.num_measurements,
            "ops": flatten(c),
        }
        p = OUT / f"stim_d{d}.json"
        p.write_text(json.dumps(payload))
        print(f"wrote {p} qubits={c.num_qubits} det={c.num_detectors} meas={c.num_measurements}", flush=True)


if __name__ == "__main__":
    main()
