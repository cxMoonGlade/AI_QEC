from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from scope_static.numerics import NUMERICAL_ZERO
from scope_static.primitives.born_local import (
    BORN_LOCAL_EFFECTIVE_CIRCUIT_DEPTH,
    born_local_outcome_probabilities,
    born_local_probability_tables,
)
from scope_static.primitives.channels import MechanismSpec, readout_bias_matrix, rx_unitary, rzz_unitary
from scope_static.data_preparation.local_observable_teacher import (
    RZZ_ALIAS_GROUP,
    READOUT_ALIAS_GROUP,
    _born_local_scope_audit,
    _build_local_observable_records,
    _normalize_response_model,
    _record_pair_correlation_profile,
    _record_probability_table,
    generate_local_observable_teacher_dataset,
)
from scope_static.teacher import run_sampled_observation_separability_audit
from scope_static.primitives.probe_catalog import _probe_names


def test_born_local_one_qubit_probability_matches_direct_density_matrix() -> None:
    spec = MechanismSpec(
        "M6",
        "coherent_rx_overrotation",
        1,
        {"epsilon": 0.035},
        instruction="rx",
        qubits=(0,),
    )

    actual = born_local_outcome_probabilities(spec, "z_basis", theta=0.18, num_qubits=1)

    rho = _density(_state("Zp"))
    rho = _apply_unitary(rho, rx_unitary(0.13))
    rho = _apply_unitary(rho, rx_unitary(0.035))
    expected = _measure_one(rho, "Z")

    np.testing.assert_allclose(actual, expected, atol=1e-12)


def test_born_local_two_qubit_rzz_probability_matches_direct_density_matrix() -> None:
    theta = 0.18
    epsilon = 0.045
    spec = MechanismSpec(
        "M8",
        "coherent_rzz_overrotation",
        2,
        {"epsilon": epsilon},
        instruction="rzz",
        qubits=(0, 1),
    )

    actual = born_local_outcome_probabilities(
        spec,
        "rzz_tomo_pXpZm_mXY_even",
        theta=theta,
        num_qubits=2,
    )

    rho = np.kron(_density(_state("Xp")), _density(_state("Zm")))
    rho = _apply_unitary(rho, rzz_unitary(theta))
    rho = _apply_unitary(rho, rzz_unitary(epsilon))
    expected = _measure_two(rho, "X", "Y")

    np.testing.assert_allclose(actual, expected, atol=1e-12)


def test_born_local_readout_bias_applies_after_povm() -> None:
    spec = MechanismSpec(
        "M1",
        "readout_0_to_1_bias",
        1,
        {"p": 0.025},
        instruction="measure",
        qubits=(0,),
    )

    actual = born_local_outcome_probabilities(spec, "z_basis", theta=0.18, num_qubits=1)

    true_probs = _normalize([1.0, 0.0])
    matrix = readout_bias_matrix(p0_to_1=0.025, p1_to_0=NUMERICAL_ZERO)
    expected = _normalize(true_probs @ matrix)

    np.testing.assert_allclose(actual, expected, atol=1e-12)


def test_born_local_rejects_hidden_depth_stacking() -> None:
    spec = MechanismSpec(
        "M6",
        "coherent_rx_overrotation",
        1,
        {"epsilon": 0.035},
        instruction="rx",
        qubits=(0,),
    )

    actual = born_local_outcome_probabilities(
        spec,
        "z_basis",
        theta=0.18,
        circuit_depth=BORN_LOCAL_EFFECTIVE_CIRCUIT_DEPTH,
        num_qubits=1,
    )

    assert actual.shape == (2,)
    with pytest.raises(ValueError, match="effective circuit depth is exactly 1"):
        born_local_outcome_probabilities(spec, "z_basis", theta=0.18, circuit_depth=2, num_qubits=1)


def test_born_local_inactive_rzz_tomography_probe_skips_pair_mechanism() -> None:
    m8 = MechanismSpec("M8", "coherent_rzz_overrotation", 2, {"epsilon": 0.045}, instruction="rzz", qubits=(0, 1))
    m10 = MechanismSpec(
        "M10",
        "coherent_rxx_ryy_perturbation",
        2,
        {"epsilon_x": 0.024, "epsilon_y": 0.017},
        instruction="rzz",
        qubits=(0, 1),
    )

    inactive_m8 = born_local_outcome_probabilities(m8, "rzz_tomo_pXpZp_mXY_odd", theta=0.18, num_qubits=3)
    inactive_m10 = born_local_outcome_probabilities(m10, "rzz_tomo_pXpZp_mXY_odd", theta=0.18, num_qubits=3)
    active_m8 = born_local_outcome_probabilities(m8, "rzz_tomo_pXpZp_mXY_even", theta=0.18, num_qubits=3)

    np.testing.assert_allclose(inactive_m8, inactive_m10, atol=1e-12)
    assert float(np.linalg.norm(active_m8 - inactive_m8)) > 1e-4


def test_born_local_readout_probability_profiles_are_pairwise_distinct() -> None:
    probe_names = _probe_names("rzz_local_tomography")
    profiles = {}
    for mechanism_id in READOUT_ALIAS_GROUP:
        record = {
            "oracle_label": mechanism_id,
            "name": f"{mechanism_id}_readout_alias_test",
            "num_qubits": 1,
            "parameters": {"p": 0.02},
            "instruction": "measure",
            "qubits": [0],
            "circuit_id": 0,
            "probe_indices": list(range(len(probe_names))),
        }
        profiles[mechanism_id] = _record_probability_table(
            record,
            probe_names,
            response_model="born_local",
            num_qubits=6,
            theta=0.18,
        ).reshape(-1)

    for left_idx, left in enumerate(READOUT_ALIAS_GROUP):
        for right in READOUT_ALIAS_GROUP[left_idx + 1 :]:
            assert float(np.linalg.norm(profiles[left] - profiles[right])) > 0.05


def test_born_local_rzz_family_joint_profiles_are_pairwise_distinct() -> None:
    probe_names = _probe_names("rzz_local_tomography")
    profiles = {}
    for mechanism_id in RZZ_ALIAS_GROUP:
        spec = MechanismSpec(
            mechanism_id,
            f"{mechanism_id}_rzz_alias_test",
            2,
            {"epsilon": 0.045, "p": 0.006, "gamma": 0.012, "epsilon_x": 0.024, "epsilon_y": 0.017},
            instruction="rzz",
            qubits=(0, 1),
        )
        outcomes, _ = born_local_probability_tables(spec, probe_names, theta=0.18, num_qubits=6)
        profiles[mechanism_id] = outcomes.reshape(-1)

    for left_idx, left in enumerate(RZZ_ALIAS_GROUP):
        for right in RZZ_ALIAS_GROUP[left_idx + 1 :]:
            assert float(np.linalg.norm(profiles[left] - profiles[right])) > 1e-4


def test_born_local_response_model_has_no_template_overlay() -> None:
    assert _normalize_response_model("PHYC2-Born-local") == "born_local"
    record = {
        "oracle_label": "M8",
        "name": "coherent_rzz_overrotation",
        "num_qubits": 2,
        "parameters": {"epsilon": 0.045},
        "instruction": "rzz",
        "qubits": [0, 1],
        "circuit_id": 0,
        "probe_indices": [0],
    }

    profile = _record_pair_correlation_profile(record, ["rzz_tomo_pXpZp_mXY_even"], response_model="born_local")

    assert profile.shape == (1,)
    assert np.all(np.isfinite(profile))


def test_born_local_allm_thin_slice_excludes_only_m11() -> None:
    records, _, _ = _build_local_observable_records(
        {
            "mechanism_set": "allM",
            "num_qubits": 9,
            "probe_set": "rzz_local_tomography",
            "balanced_min_instances_per_mechanism": 2,
        }
    )

    audit = _born_local_scope_audit(records)

    assert audit["excluded_unsupported_mechanisms"] == ["M11"]
    assert "spectator" in str(audit["unsupported_mechanism_reasons"]["M11"])
    assert audit["num_excluded_records"] == 2
    assert audit["num_supported_records"] == len(records) - 2


@pytest.mark.parametrize(
    ("mechanisms", "expects_joint_sampling"),
    [
        (["M1", "M2", "M3", "M16"], False),
        (["M8", "M9", "M10", "M12"], True),
    ],
)
def test_born_local_teacher_writes_phyc2_evaluable_artifact_when_cuda_available(
    tmp_path: Path,
    mechanisms: list[str],
    expects_joint_sampling: bool,
) -> None:
    torch = pytest.importorskip("torch")
    if not torch.cuda.is_available():
        pytest.skip("requires CUDA")

    teacher_dir = tmp_path / "teacher"
    result = generate_local_observable_teacher_dataset(
        {
            "mechanism_set": mechanisms,
            "num_qubits": 6,
            "circuit_depth": 2,
            "probe_set": "rzz_local_tomography",
            "balanced_min_instances_per_mechanism": 2,
            "shots": 256,
            "seed": 0,
            "local_observable_response_model": "born_local",
        },
        output_dir=teacher_dir,
    )
    audit = run_sampled_observation_separability_audit(teacher_dir=teacher_dir, output_dir=tmp_path / "phyc2")

    assert result["local_observable_response_model"] == "born_local"
    assert result["configured_circuit_depth"] == 2
    assert result["effective_circuit_depth"] == BORN_LOCAL_EFFECTIVE_CIRCUIT_DEPTH
    assert result["sampling"]["effective_circuit_depth"] == BORN_LOCAL_EFFECTIVE_CIRCUIT_DEPTH
    assert result["sampling"]["pair_correlation_overlay"]["enabled"] is False
    assert result["sampling"]["born_local_joint_sampling"]["enabled"] is True
    assert bool(result["sampling"]["born_local_joint_sampling"]["num_entries"]) is expects_joint_sampling
    assert audit["coverage"]["contract_evaluable"] is True


def test_born_local_matches_direct_statevector_rzz_probe_probability() -> None:
    theta = 0.18
    epsilon = 0.045
    spec = MechanismSpec("M8", "coherent_rzz_overrotation", 2, {"epsilon": epsilon}, instruction="rzz", qubits=(0, 1))
    actual = born_local_outcome_probabilities(spec, "rzz_tomo_pXpZm_mXY_even", theta=theta, num_qubits=2)

    rho = np.kron(_density(_state("Xp")), _density(_state("Zm")))
    rho = _apply_unitary(rho, rzz_unitary(theta))
    rho = _apply_unitary(rho, rzz_unitary(epsilon))
    expected = _measure_two(rho, "X", "Y")

    np.testing.assert_allclose(actual, expected, atol=1e-12)


def _apply_unitary(rho: np.ndarray, unitary: np.ndarray) -> np.ndarray:
    return unitary @ rho @ unitary.conj().T


def _density(state: np.ndarray) -> np.ndarray:
    ket = state.reshape(-1, 1)
    return ket @ ket.conj().T


def _state(label: str) -> np.ndarray:
    inv_sqrt2 = 1.0 / math.sqrt(2.0)
    states = {
        "Zp": np.asarray([1.0, 0.0], dtype=np.complex128),
        "Zm": np.asarray([0.0, 1.0], dtype=np.complex128),
        "Xp": inv_sqrt2 * np.asarray([1.0, 1.0], dtype=np.complex128),
        "Xm": inv_sqrt2 * np.asarray([1.0, -1.0], dtype=np.complex128),
        "Yp": inv_sqrt2 * np.asarray([1.0, 1.0j], dtype=np.complex128),
        "Ym": inv_sqrt2 * np.asarray([1.0, -1.0j], dtype=np.complex128),
    }
    return states[label]


def _projectors(axis: str) -> tuple[np.ndarray, np.ndarray]:
    if axis == "X":
        return _density(_state("Xp")), _density(_state("Xm"))
    if axis == "Y":
        return _density(_state("Yp")), _density(_state("Ym"))
    return _density(_state("Zp")), _density(_state("Zm"))


def _measure_one(rho: np.ndarray, axis: str) -> np.ndarray:
    projectors = _projectors(axis)
    return _normalize([float(np.trace(projector @ rho).real) for projector in projectors])


def _measure_two(rho: np.ndarray, left_axis: str, right_axis: str) -> np.ndarray:
    left = _projectors(left_axis)
    right = _projectors(right_axis)
    return _normalize(
        [
            float(np.trace(np.kron(left[left_bit], right[right_bit]) @ rho).real)
            for left_bit in (0, 1)
            for right_bit in (0, 1)
        ]
    )


def _normalize(values) -> np.ndarray:
    probs = np.maximum(np.asarray(values, dtype=np.float64), NUMERICAL_ZERO)
    return probs / float(np.sum(probs))
