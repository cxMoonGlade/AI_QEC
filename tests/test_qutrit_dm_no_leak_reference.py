"""Independent no-leak reference and frontend corruption test for ``QutritDM``."""

from __future__ import annotations

import json
import math

import numpy as np
import pytest

from conftest import requires_cuda, requires_data
from error_coupling_simulator.carrier.exact.qutrit_dm import QutritDM
from error_coupling_simulator.frontend import xzzx_parser


TOLERANCE = 1.0e-12


def _all_z_code():
    stabilizers = [{0: "Z", 1: "Z"}, {1: "Z", 2: "Z"}]
    logical_z = {0: "Z", 1: "Z", 2: "Z"}
    logical_x = {0: "X", 1: "X", 2: "X"}
    return stabilizers, logical_z, logical_x


def _embed_qubit_operator(operator: np.ndarray, site: int, n_sites: int) -> np.ndarray:
    embedded = np.array([[1.0 + 0.0j]])
    for current in range(n_sites):
        factor = operator if current == site else np.eye(2, dtype=np.complex128)
        embedded = np.kron(embedded, factor)
    return embedded


def _independent_qubit_codestate(
    n_sites: int,
    stabilizers: list[dict[int, str]],
    logical_z: dict[int, str],
    logical_index: int,
) -> np.ndarray:
    hadamard = np.array([[1, 1], [1, -1]], dtype=np.complex128) / math.sqrt(2.0)
    pauli_x = np.array([[0, 1], [1, 0]], dtype=np.complex128)
    pauli_z = np.array([[1, 0], [0, -1]], dtype=np.complex128)

    def project(vector: np.ndarray, paulis: dict[int, str], eigenvalue: int) -> np.ndarray:
        operated = vector.copy()
        for site, kind in paulis.items():
            local = pauli_x if kind == "X" else pauli_z
            operated = _embed_qubit_operator(local, site, n_sites) @ operated
        return 0.5 * (vector + float(eigenvalue) * operated)

    state = np.zeros(2**n_sites, dtype=np.complex128)
    state[0] = 1.0
    for site in range(n_sites):
        state = _embed_qubit_operator(hadamard, site, n_sites) @ state
    for stabilizer in stabilizers:
        state = project(state, stabilizer, +1)
    state = project(state, logical_z, (-1) ** logical_index)
    state /= np.linalg.norm(state)
    return np.outer(state, state.conj())


def _qubit_parity(n_sites: int, sites: list[int]) -> np.ndarray:
    basis = np.arange(2**n_sites)
    parity = np.zeros(2**n_sites, dtype=np.uint8)
    for site in sites:
        parity ^= ((basis >> (n_sites - 1 - site)) & 1).astype(np.uint8)
    return parity


def _independent_qubit_syndrome_distribution(
    density: np.ndarray,
    stabilizers: list[dict[int, str]],
    n_sites: int,
) -> dict[tuple[int, ...], float]:
    distribution: dict[tuple[int, ...], float] = {}

    def descend(branch: np.ndarray, index: int, prefix: tuple[int, ...]) -> None:
        if index == len(stabilizers):
            distribution[prefix] = float(np.trace(branch).real)
            return
        parity = _qubit_parity(n_sites, sorted(stabilizers[index]))
        for outcome in (0, 1):
            keep = parity == outcome
            mask = np.outer(keep, keep).astype(branch.dtype)
            descend(branch * mask, index + 1, prefix + (outcome,))

    descend(density, 0, ())
    return distribution


@requires_cuda
@pytest.mark.parametrize("logical_index", [0, 1])
@pytest.mark.parametrize("leaked_readout_bias", [0.0, 0.5, 1.0])
def test_no_leak_qutrit_distribution_matches_independent_qubit_reference(
    logical_index: int,
    leaked_readout_bias: float,
):
    n_sites = 3
    stabilizers, logical_z, logical_x = _all_z_code()
    engine = QutritDM(n_sites, device="cuda")
    engine.set_code(
        stabilizers=stabilizers,
        logical_x=logical_x,
        logical_z=logical_z,
    )
    engine.init_logical(logical_index)
    qutrit_distribution = engine.syndrome_distribution(
        stabilizers,
        b=leaked_readout_bias,
    )

    qubit_state = _independent_qubit_codestate(
        n_sites,
        stabilizers,
        logical_z,
        logical_index,
    )
    qubit_distribution = _independent_qubit_syndrome_distribution(
        qubit_state,
        stabilizers,
        n_sites,
    )
    keys = set(qutrit_distribution) | set(qubit_distribution)
    difference = max(
        abs(qutrit_distribution.get(key, 0.0) - qubit_distribution.get(key, 0.0))
        for key in keys
    )
    assert difference <= TOLERANCE
    assert abs(sum(qutrit_distribution.values()) - 1.0) <= TOLERANCE


@requires_data
def test_frontend_parser_rejects_corrupted_stabilizer_support(monkeypatch):
    import stim

    circuit_path, metadata_path = xzzx_parser.default_r01_paths()
    circuit = stim.Circuit.from_file(str(circuit_path))
    metadata = json.loads(metadata_path.read_text())
    data_indices, measurement_indices, _ = xzzx_parser._classify_qubits(
        circuit, metadata
    )
    measurement_set = set(measurement_indices)
    ancilla_order = [
        ancilla
        for ancilla in xzzx_parser._first_ancilla_measure_order(circuit)
        if ancilla in measurement_set
    ]
    first_ancilla = ancilla_order[0]
    real_pullback = xzzx_parser._pullback_stabilizer

    def corrupted_pullback(circuit_in, ancilla, data_indices_in):
        support = real_pullback(circuit_in, ancilla, data_indices_in)
        if ancilla != first_ancilla or not support:
            return support
        corrupted = dict(support)
        removed = next(iter(corrupted))
        replacement = next(
            data_index
            for data_index in data_indices_in
            if data_index not in support
        )
        corrupted[replacement] = corrupted.pop(removed)
        return corrupted

    monkeypatch.setattr(
        xzzx_parser,
        "_pullback_stabilizer",
        corrupted_pullback,
        raising=True,
    )
    with pytest.raises(AssertionError):
        xzzx_parser.extract_stabilizers(
            circuit,
            data_indices,
            ancilla_order,
            verify=True,
        )
