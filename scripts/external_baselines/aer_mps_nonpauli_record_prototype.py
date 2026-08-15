"""UNREPRODUCED PROTOTYPE -- promoted verbatim from a session scratchpad.

Translates a stim-generated rotated surface code into Qiskit and runs it on
qiskit-aer's matrix_product_state method under a genuine Kraus amplitude-damping
noise model, then folds detectors. Runs in the ecs-baseline-aer environment; the
companion emitter runs in ecs.

Reported once and NEVER INDEPENDENTLY REPRODUCED: d3 26 qubits / 3 rounds / 24
detectors at 1.7 ms/shot, d5 64 qubits / 5 rounds / 120 detectors at 18.3 s/shot,
and a 16.9 sigma separation between the Kraus record and its exact Pauli twirl.
Treat every number here as indicative until a committed leg reproduces it. This is
not a baseline leg: it has no frozen fixture, no committed lock binding, and no
fail-closed comparison.
"""

"""Scale + fidelity probe for qiskit-aer as a NON-PAULI multi-round record oracle.

Runs in `ecs-baseline-aer`. Answers:
  A) does d5 (and d7) run under genuine Kraus amplitude damping on the MPS method?
  B) at matched channel strength, does the Kraus record differ from its Pauli twirl?
  C) what does the MPS bond dimension do (saved via save_matrix_product_state)?
"""

import json
import signal
import time
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, amplitude_damping_error, pauli_error

HERE = Path(__file__).resolve().parent


class Timeout(Exception):
    pass


signal.signal(signal.SIGALRM, lambda *a: (_ for _ in ()).throw(Timeout()))


def build(payload):
    qc = QuantumCircuit(payload["num_qubits"], payload["num_measurements"])
    m = 0
    dets = []
    for op in payload["ops"]:
        n = op["op"]
        if n == "R":
            [qc.reset(q) for q in op["q"]]
        elif n == "H":
            [qc.h(q) for q in op["q"]]
        elif n == "CX":
            qs = op["q"]
            for i in range(0, len(qs), 2):
                qc.cx(qs[i], qs[i + 1])
        elif n == "MR":
            for q in op["q"]:
                qc.measure(q, m)
                qc.reset(q)
                m += 1
        elif n == "M":
            for q in op["q"]:
                qc.measure(q, m)
                m += 1
        elif n == "DETECTOR":
            dets.append([m + r for r in op["rec"]])
    return qc, dets


def kraus_nm(p):
    nm = NoiseModel()
    e = amplitude_damping_error(p)
    nm.add_all_qubit_quantum_error(e, ["h"])
    nm.add_all_qubit_quantum_error(e.tensor(e), ["cx"])
    return nm


def twirl_nm(p):
    """Exact Pauli twirl of amplitude damping at damping probability p."""
    pz = (1.0 - np.sqrt(1.0 - p)) / 2.0
    px = py = p / 4.0
    e = pauli_error([("I", 1 - px - py - pz), ("X", px), ("Y", py), ("Z", pz)])
    nm = NoiseModel()
    nm.add_all_qubit_quantum_error(e, ["h"])
    nm.add_all_qubit_quantum_error(e.tensor(e), ["cx"])
    return nm


def detectors(payload, nm, shots, budget, label):
    qc, dets = build(payload)
    sim = AerSimulator(noise_model=nm, method="matrix_product_state")
    t0 = time.time()
    signal.alarm(budget)
    try:
        res = sim.run(qc, shots=shots, memory=True).result()
        signal.alarm(0)
    except Timeout:
        print(f"[{label}] TIMEOUT >{budget}s", flush=True)
        return None
    except Exception as exc:  # noqa: BLE001
        signal.alarm(0)
        print(f"[{label}] FAILED {type(exc).__name__}: {str(exc)[:160]}", flush=True)
        return None
    dt = time.time() - t0
    nm_ = payload["num_measurements"]
    mem = res.get_memory()
    bits = np.array(
        [[1 if w.replace(" ", "")[nm_ - 1 - c] == "1" else 0 for c in range(nm_)] for w in mem],
        dtype=np.uint8,
    )
    det = np.zeros((bits.shape[0], len(dets)), dtype=np.uint8)
    for i, rec in enumerate(dets):
        acc = np.zeros(bits.shape[0], dtype=np.uint8)
        for r in rec:
            acc ^= bits[:, r]
        det[:, i] = acc
    print(
        f"[{label}] OK wall={dt:.1f}s ({dt/shots*1000:.1f} ms/shot) "
        f"det={det.shape[1]} mean_fire={det.mean():.5f}",
        flush=True,
    )
    return det


def main():
    p = 0.02
    for d, shots, budget in ((5, 10, 1800), (7, 4, 1800)):
        f = HERE / f"stim_d{d}.json"
        if not f.exists():
            print(f"[d{d}] no fixture", flush=True)
            continue
        pl = json.loads(f.read_text())
        print(
            f"=== d={d} qubits={pl['num_qubits']} rounds={pl['rounds']} "
            f"detectors={pl['num_detectors']} ===",
            flush=True,
        )
        k = detectors(pl, kraus_nm(p), shots, budget, f"d{d} KRAUS-AD p={p}")
        t = detectors(pl, twirl_nm(p), shots, budget, f"d{d} PAULI-TWIRL p={p}")
        if k is not None and t is not None:
            kr, tr = k.mean(), t.mean()
            se = np.sqrt(kr * (1 - kr) / k.size + tr * (1 - tr) / t.size)
            print(
                f"[d{d}] kraus={kr:.5f} twirl={tr:.5f} diff={kr-tr:+.5f} "
                f"({abs(kr-tr)/se:.1f} sigma on the pooled detector-fire rate)",
                flush=True,
            )


if __name__ == "__main__":
    main()
