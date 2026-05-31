from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import yaml

from scope_static.experiments.qec_noise_catalog import s2d9_local_pauli_lindblad_observability as runner
from scope_static.backend.channels import correlated_relaxation_kraus, rxx_ryy_unitary, rxx_unitary, rzz_unitary
from scope_static.mechanism_observability import (
    PAULI_LABELS,
    fit_generator_coordinates,
    local_error_ptm_from_observed,
    reconstruct_record_local_ptm,
)
from scope_static.backend.ptm import ptm_from_kraus, ptm_from_unitary
from scope_static.backend.probe_catalog import RZZ_LOCAL_TOMOGRAPHY_PROBES, build_probe_basis_manifest, build_probe_circuits


TOMO_PROBES = list(RZZ_LOCAL_TOMOGRAPHY_PROBES)


def test_tomography_probe_naming_and_edge_coloring() -> None:
    circuits, names = build_probe_circuits({"profile": "phys9_chain", "probe_set": "rzz_local_tomography"})

    assert len(names) == 4 * 4 * 3 * 3 * 2
    assert names[0] == "rzz_tomo_pZpZp_mXX_even"
    assert names[-1] == "rzz_tomo_pYpYp_mZZ_odd"
    assert {int(circuit.count_ops().get("rzz", 0)) for circuit in circuits} == {4}

    manifest = build_probe_basis_manifest(names, num_qubits=9)
    first = manifest["probe_records"][0]
    assert first["rzz_tomography_prep"] == {"left": "Zp", "right": "Zp"}
    assert first["rzz_tomography_measurement"] == {"left": "X", "right": "X"}
    assert first["rzz_tomography_edge_parity"] == "even"
    assert [item["edge"] for item in first["rzz_tomography_edge_pairs"]] == [[0, 1], [2, 3], [4, 5], [6, 7]]


def test_ptm_convention_post_ideal_order_with_noncommuting_sentinel() -> None:
    u_ideal = rzz_unitary(0.18)
    u_noise = _single_axis_rotation("XI", 0.03)
    r_ideal = ptm_from_unitary(u_ideal)
    r_noise = ptm_from_unitary(u_noise)
    r_after = ptm_from_unitary(u_noise @ u_ideal)
    r_before = ptm_from_unitary(u_ideal @ u_noise)

    assert np.allclose(r_after, r_noise @ r_ideal, atol=1e-12)
    assert np.allclose(r_before, r_ideal @ r_noise, atol=1e-12)
    assert not np.allclose(r_after, r_ideal @ r_noise, atol=1e-4)


def test_known_ideal_rzz_plus_small_rxx_recovers_hxx_sign() -> None:
    r_ideal = ptm_from_unitary(rzz_unitary(0.18))
    r_est = ptm_from_unitary(rxx_unitary(0.031) @ rzz_unitary(0.18))
    r_error = local_error_ptm_from_observed(r_est, r_ideal, error_order="post_ideal")
    coords = fit_generator_coordinates(r_error)["coordinates"]

    assert coords["h_XX"] > 0.02
    assert abs(coords["h_XX"]) > 5 * abs(coords["h_ZZ"])
    assert abs(coords["h_XX"]) > 5 * abs(coords["h_YY"])


def test_known_ideal_rzz_plus_small_rzz_recovers_hzz_sign() -> None:
    r_ideal = ptm_from_unitary(rzz_unitary(0.18))
    r_est = ptm_from_unitary(rzz_unitary(0.027) @ rzz_unitary(0.18))
    r_error = local_error_ptm_from_observed(r_est, r_ideal, error_order="post_ideal")
    coords = fit_generator_coordinates(r_error)["coordinates"]

    assert coords["h_ZZ"] > 0.02
    assert abs(coords["h_ZZ"]) > 5 * abs(coords["h_XX"])
    assert abs(coords["h_ZZ"]) > 5 * abs(coords["h_YY"])


def test_known_rxx_ryy_mixture_recovers_relative_hxx_hyy() -> None:
    r_ideal = ptm_from_unitary(rzz_unitary(0.18))
    r_est = ptm_from_unitary(rxx_ryy_unitary(theta_x=0.024, theta_y=0.017) @ rzz_unitary(0.18))
    r_error = local_error_ptm_from_observed(r_est, r_ideal, error_order="post_ideal")
    coords = fit_generator_coordinates(r_error)["coordinates"]

    assert coords["h_XX"] > 0.015
    assert coords["h_YY"] > 0.010
    assert coords["h_XX"] > coords["h_YY"]


def test_tomography_reconstructs_identity_and_visible_ideal_rzz() -> None:
    record = _record()
    manifest = build_probe_basis_manifest(TOMO_PROBES, num_qubits=2)

    identity_obs = _observations_from_ptm(np.eye(16), shots=400)
    identity = reconstruct_record_local_ptm(record, identity_obs, TOMO_PROBES, manifest, theta=0.18)
    assert np.allclose(identity["R_est"], np.eye(16), atol=0.04)

    ideal_ptm = ptm_from_unitary(rzz_unitary(0.18))
    ideal_obs = _observations_from_ptm(ideal_ptm, shots=800)
    reconstructed = reconstruct_record_local_ptm(record, ideal_obs, TOMO_PROBES, manifest, theta=0.18)
    assert np.allclose(reconstructed["R_est"], ideal_ptm, atol=0.06)
    assert np.allclose(reconstructed["R_error"], np.eye(16), atol=0.08)


def test_stochastic_and_relaxation_coordinates_load_expected_blocks() -> None:
    stochastic = fit_generator_coordinates(ptm_from_kraus(_two_qubit_pauli_kraus("ZZ", 0.012)))["coordinates"]
    relaxation = fit_generator_coordinates(ptm_from_kraus(correlated_relaxation_kraus(0.012)))

    assert stochastic["gamma_ZZ"] > 0.008
    assert abs(stochastic["gamma_ZZ"]) > abs(stochastic["h_ZZ"])
    assert relaxation["coordinates"]["relaxation_pair"] > 0.005
    assert relaxation["nonunital_norm_proxy"] > 0.0


def test_s2d9_runner_writes_required_artifacts_with_fakes(tmp_path: Path, monkeypatch) -> None:
    config = {
        "run": {"output_root": str(tmp_path)},
        "s2d_physical": {"shots": 64, "theta": 0.18},
        "s2d9_local_pauli_lindblad_observability": {
            "output_dir": str(tmp_path / "S2D.9_local_Pauli_Lindblad_observability"),
            "permutation_repeats": 2,
            "runs": [{"name": "phys9_setA", "profile": "phys9_chain", "mechanism_set": "set_A"}],
        },
    }
    config_path = tmp_path / "s2d9.yaml"
    config_path.write_text(yaml.safe_dump(config))

    def fake_teacher(cfg, *, output_dir, preflight_dir):
        out = Path(output_dir)
        out.mkdir(parents=True)
        records = [
            {
                "location_id": 0,
                "mechanism_id": "M1",
                "name": "coherent_rzz_overrotation",
                "num_qubits": 2,
                "parameters": {"epsilon": 0.045},
                "instruction": "rzz",
                "qubits": [0, 1],
                "circuit_id": 0,
                "probe_indices": list(range(len(TOMO_PROBES))),
                "oracle_label": "M1",
            }
        ]
        np.savez_compressed(
            out / "observations.npz",
            observations=_observations_from_ptm(ptm_from_unitary(rzz_unitary(0.18)), shots=64),
            probe_names=np.asarray(TOMO_PROBES),
            shots=np.asarray([64], dtype=np.int64),
        )
        (out / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}, indent=2) + "\n")
        return {"mechanism_counts": {"M1": 1}, "num_qubits": 2, "num_probes": len(TOMO_PROBES), "output_dir": str(out)}

    monkeypatch.setattr(runner, "generate_controlled_catalog_teacher_dataset", fake_teacher)

    result = runner.run_s2d9_local_pauli_lindblad_observability(config_path)
    out = tmp_path / "S2D.9_local_Pauli_Lindblad_observability"

    assert result["stage"] == "S2D.9_local_Pauli_Lindblad_observability"
    for name in [
        "metrics.json",
        "summary.md",
        "generator_dictionary.json",
        "probe_observable_schema.json",
        "ptm_convention_audit.json",
        "response_jacobian.npy",
        "response_jacobian.json",
        "observability_rank_metrics.json",
        "ptm_block_reconstruction.json",
        "generator_coordinate_estimates.json",
        "generator_recovery_metrics.json",
        "grouped_fold_predictions.json",
        "feature_block_results.json",
        "controls.json",
        "leakage_guardrail_audit.json",
    ]:
        assert (out / name).exists()


def _record() -> dict[str, object]:
    return {
        "location_id": 0,
        "oracle_label": "M1",
        "instruction": "rzz",
        "qubits": [0, 1],
        "circuit_id": 0,
        "probe_indices": list(range(len(TOMO_PROBES))),
    }


def _observations_from_ptm(ptm: np.ndarray, *, shots: int) -> np.ndarray:
    manifest = build_probe_basis_manifest(TOMO_PROBES, num_qubits=2)
    observations = np.zeros((len(TOMO_PROBES), int(shots), 2), dtype=np.uint8)
    for record in manifest["probe_records"]:
        idx = int(record["probe_index"])
        if record["rzz_tomography_edge_parity"] != "even":
            continue
        prep = record["rzz_tomography_prep"]
        meas = record["rzz_tomography_measurement"]
        vin = _prep_vector(prep["left"], prep["right"])
        vout = np.asarray(ptm, dtype=np.float64) @ vin
        a = float(vout[PAULI_LABELS.index(f"{meas['left']}I")])
        b = float(vout[PAULI_LABELS.index(f"I{meas['right']}")])
        c = float(vout[PAULI_LABELS.index(f"{meas['left']}{meas['right']}")])
        observations[idx] = _samples_for_moments(a, b, c, int(shots))
    return observations


def _prep_vector(prep_left: str, prep_right: str) -> np.ndarray:
    left = _prep_bloch(prep_left)
    right = _prep_bloch(prep_right)
    return np.asarray([_axis_value(label[0], left) * _axis_value(label[1], right) for label in PAULI_LABELS], dtype=np.float64)


def _prep_bloch(prep: str) -> dict[str, float]:
    return {
        "Zp": {"X": 0.0, "Y": 0.0, "Z": 1.0},
        "Zm": {"X": 0.0, "Y": 0.0, "Z": -1.0},
        "Xp": {"X": 1.0, "Y": 0.0, "Z": 0.0},
        "Yp": {"X": 0.0, "Y": 1.0, "Z": 0.0},
    }[prep]


def _axis_value(axis: str, bloch: dict[str, float]) -> float:
    return 1.0 if axis == "I" else float(bloch.get(axis, 0.0))


def _samples_for_moments(a: float, b: float, c: float, shots: int) -> np.ndarray:
    probs = []
    outcomes = []
    for left_bit, s in [(0, 1.0), (1, -1.0)]:
        for right_bit, t in [(0, 1.0), (1, -1.0)]:
            probs.append(max(0.0, 0.25 * (1.0 + a * s + b * t + c * s * t)))
            outcomes.append((left_bit, right_bit))
    probs = np.asarray(probs, dtype=np.float64)
    probs = probs / probs.sum()
    counts = np.floor(probs * int(shots)).astype(int)
    while int(np.sum(counts)) < int(shots):
        counts[int(np.argmax(probs * int(shots) - counts))] += 1
    rows = []
    for count, outcome in zip(counts.tolist(), outcomes):
        rows.extend([outcome for _ in range(int(count))])
    return np.asarray(rows[: int(shots)], dtype=np.uint8)


def _single_axis_rotation(label: str, theta: float) -> np.ndarray:
    pauli = _two_qubit_pauli_matrix(label)
    return np.cos(float(theta) / 2.0) * np.eye(4, dtype=np.complex128) - 1j * np.sin(float(theta) / 2.0) * pauli


def _two_qubit_pauli_kraus(label: str, probability: float) -> list[np.ndarray]:
    pauli = _two_qubit_pauli_matrix(label)
    p = float(probability)
    return [np.sqrt(1.0 - p) * np.eye(4, dtype=np.complex128), np.sqrt(p) * pauli]


def _two_qubit_pauli_matrix(label: str) -> np.ndarray:
    one = {
        "I": np.eye(2, dtype=np.complex128),
        "X": np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128),
        "Y": np.array([[0.0, -1j], [1j, 0.0]], dtype=np.complex128),
        "Z": np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128),
    }
    return np.kron(one[label[0]], one[label[1]])
