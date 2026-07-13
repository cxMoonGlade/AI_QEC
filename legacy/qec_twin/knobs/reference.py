from __future__ import annotations

"""Canonical stim reference circuit for the rep-code twin.

One builder with the exact wiring the density-matrix forward
(:mod:`qec_twin.forward.exact.rep_code`) implements -- same qubits, CX
order, ``MR``/``M`` order, detector ``rec`` offsets, and ``data 0`` observable.
Used to (a) cross-check the exact forward on the pure-Pauli slice and (b) build
the frozen MWPM decoder's detector error model. Keeping a single source of the
convention prevents the sim and the decoder graph from drifting apart.
"""

from qec_twin.forward.exact.rep_code import rep_code_qubits


def stim_rep_code_circuit(distance: int, rounds: int, p_data: float, *, logical: int = 0):
    """Bit-flip repetition-code memory circuit (logical ``|0_L>`` or ``|1_L>``).

    ``p_data`` is the per-round ``X_ERROR`` probability on every data qubit (set
    to a uniform nominal value to get a weight-uniform, noise-agnostic decoder
    graph). Detectors are emitted syndrome-round-major; the observable is data
    qubit ``0``.
    """
    import stim

    d = int(distance)
    nchecks = d - 1
    data, anc, _ = rep_code_qubits(d)
    circuit = stim.Circuit()

    if logical:
        circuit.append("X", data)  # prepare |1_L>

    for t in range(int(rounds)):
        if p_data > 0:
            circuit.append("X_ERROR", data, p_data)
        for j in range(nchecks):
            circuit.append("CX", [data[j], anc[j]])
            circuit.append("CX", [data[j + 1], anc[j]])
        circuit.append("MR", anc)
        for j in range(nchecks):
            if t == 0:
                circuit.append("DETECTOR", [stim.target_rec(-nchecks + j)])
            else:
                circuit.append(
                    "DETECTOR",
                    [stim.target_rec(-nchecks + j), stim.target_rec(-2 * nchecks + j)],
                )

    circuit.append("M", data)
    for j in range(nchecks):
        circuit.append(
            "DETECTOR",
            [
                stim.target_rec(-d + j),
                stim.target_rec(-d + j + 1),
                stim.target_rec(-d - nchecks + j),
            ],
        )
    circuit.append("OBSERVABLE_INCLUDE", [stim.target_rec(-d)], 0)
    return circuit
