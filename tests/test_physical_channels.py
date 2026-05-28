from __future__ import annotations

import numpy as np

from scope_static.physical.channels import (
    MechanismSpec,
    amplitude_damping_kraus,
    mechanism_channel,
    pauli_stochastic_kraus,
    readout_bias_matrix,
    rzz_unitary,
)
from scope_static.physical.density_sim import apply_kraus, measurement_probabilities_z
from scope_static.physical.mechanism_catalog import IMPLEMENTED_MECHANISM_IDS, MECHANISM_NAMES, READOUT_MECHANISM_IDS, RZZ_FAMILY_IDS
from scope_static.physical.ptm import channel_fingerprint, ptm_from_kraus, ptm_from_unitary, rzz_ptm_block_audit
from scope_static.physical.ptm import probe_response_fingerprint, rzz_type_feature_names, rzz_type_feature_vector


def test_amplitude_damping_preserves_trace_and_probabilities_normalize() -> None:
    rho = np.array([[0.2, 0.1], [0.1, 0.8]], dtype=np.complex128)
    out = apply_kraus(rho, amplitude_damping_kraus(0.25))
    probs = measurement_probabilities_z(out, num_qubits=1)

    assert np.isclose(np.trace(out), 1.0)
    assert np.isclose(probs.sum(), 1.0)
    assert np.all(probs >= 0.0)


def test_stochastic_pauli_ptm_is_diagonal() -> None:
    kraus = pauli_stochastic_kraus({"X": 0.01, "Y": 0.02, "Z": 0.03})
    ptm = ptm_from_kraus(kraus)

    assert ptm.shape == (4, 4)
    assert np.allclose(ptm, np.diag(np.diag(ptm)), atol=1e-12)
    assert np.isclose(ptm[0, 0], 1.0)


def test_rzz_ptm_has_fixed_and_two_entry_blocks() -> None:
    ptm = ptm_from_unitary(rzz_unitary(0.2))
    audit = rzz_ptm_block_audit(ptm)

    assert ptm.shape == (16, 16)
    assert audit["max_column_support"] <= 2
    assert audit["num_fixed_columns"] > 0
    assert audit["num_two_entry_columns"] > 0


def test_readout_and_mechanism_fingerprints_are_finite() -> None:
    matrix = readout_bias_matrix(p0_to_1=0.02, p1_to_0=0.01)
    assert np.allclose(matrix.sum(axis=1), 1.0)

    specs = [
        MechanismSpec("M0", "pauli", 1, {"p_x": 0.001, "p_y": 0.002, "p_z": 0.003}),
        MechanismSpec("M8", "rzz", 2, {"epsilon": 0.04}),
        MechanismSpec("M6", "rx", 1, {"axis": "rx", "epsilon": 0.03}),
        MechanismSpec("M7", "rz", 1, {"epsilon": 0.04}),
        MechanismSpec("M4", "amp", 1, {"gamma": 0.02}),
        MechanismSpec("M15", "custom", 1, {"eta": 0.02}),
        MechanismSpec("M9", "depolarizing", 2, {"p": 0.006}),
        MechanismSpec("M1", "readout", 1, {"p": 0.02}),
    ]
    for spec in specs:
        channel = mechanism_channel(spec)
        features = channel_fingerprint(spec, paper_informed=True)
        probe = probe_response_fingerprint(spec)
        assert channel["kind"] in {"kraus", "unitary", "readout"}
        assert features.ndim == 1
        assert np.isfinite(features).all()
        assert probe.shape == (32,)
        assert np.isfinite(probe).all()


def test_rzz_type_features_are_named_and_rzz_specific() -> None:
    rzz = MechanismSpec("M8", "rzz", 2, {"epsilon": 0.04})
    pauli = MechanismSpec("M0", "pauli", 1, {"p_x": 0.001, "p_y": 0.002, "p_z": 0.003})

    assert rzz_type_feature_names() == [
        "rzz_type1_commuting_fixed_fraction",
        "rzz_type2_two_entry_rotation_fraction",
        "rzz_type3_nonclifford_rotation_strength",
        "rzz_type4_hard_residual_leakage",
    ]
    assert rzz_type_feature_vector(rzz).shape == (4,)
    assert np.isfinite(rzz_type_feature_vector(rzz)).all()
    assert np.allclose(rzz_type_feature_vector(pauli), 0.0)


def test_implemented_catalog_mechanisms_have_distinct_channel_fingerprints() -> None:
    fingerprints = {}
    for mechanism_id in IMPLEMENTED_MECHANISM_IDS:
        num_qubits = 2 if mechanism_id in RZZ_FAMILY_IDS else 1
        instruction = "rzz" if num_qubits == 2 else ("measure" if mechanism_id in READOUT_MECHANISM_IDS else "id")
        spec = MechanismSpec(
            mechanism_id,
            MECHANISM_NAMES[mechanism_id],
            num_qubits,
            {},
            instruction=instruction,
            qubits=tuple(range(num_qubits)),
        )
        channel = mechanism_channel(spec)
        fingerprint = np.concatenate([channel_fingerprint(spec, paper_informed=True), probe_response_fingerprint(spec)])

        assert channel["kind"] in {"kraus", "unitary", "readout"}
        assert np.isfinite(fingerprint).all()
        fingerprints[mechanism_id] = fingerprint

    assert set(fingerprints) == set(IMPLEMENTED_MECHANISM_IDS)
    for left_idx, left in enumerate(IMPLEMENTED_MECHANISM_IDS):
        for right in IMPLEMENTED_MECHANISM_IDS[left_idx + 1 :]:
            assert float(np.linalg.norm(fingerprints[left] - fingerprints[right])) > 1e-6
