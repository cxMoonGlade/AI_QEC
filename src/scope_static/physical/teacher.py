from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Iterable
import warnings

import numpy as np

from ..numerics import NUMERICAL_ZERO, positive_floor
from .channels import (
    MechanismSpec,
    amplitude_damping_kraus,
    correlated_relaxation_kraus,
    custom_non_pauli_kraus,
    readout_bias_matrix,
    rx_unitary,
    rxx_ryy_unitary,
    rz_unitary,
    rzz_unitary,
    weak_type4_mixing_kraus,
)
from .preflight import audit_aer_backend, write_backend_audit


MIXED_BASIS_ACTIVE_PROBES = ("alt_xz", "alt_zx", "alt_yz", "alt_zy", "alt_xy", "alt_yx")
RZZ_DEPTH_SWEEP_DEPTHS = (1, 2, 4, 8)
RZZ_DEPTH_SWEEP_PROBES = tuple(f"rzz_depth_{depth}" for depth in RZZ_DEPTH_SWEEP_DEPTHS)
RZZ_ECHO_CONTRAST_PROBES = (
    "rzz_no_echo",
    "rzz_echo_left_even",
    "rzz_echo_right_even",
    "rzz_echo_both_even",
    "rzz_echo_left_odd",
    "rzz_echo_right_odd",
    "rzz_echo_both_odd",
)
RZZ_MINIMAL_INTERVENTION_PROBES = (
    "rzz_int_no_intervention",
    "rzz_int_basis_x",
    "rzz_int_basis_y",
    "rzz_int_basis_xz",
    "rzz_int_basis_yz",
    "rzz_int_twirl_x_left_even",
    "rzz_int_twirl_x_left_odd",
    "rzz_int_twirl_y_left_even",
    "rzz_int_twirl_y_left_odd",
    "rzz_int_twirl_xy_even",
    "rzz_int_twirl_xy_odd",
    "rzz_int_sign_no_flip",
    "rzz_int_sign_flip_left_even",
    "rzz_int_sign_flip_right_even",
    "rzz_int_sign_flip_left_odd",
    "rzz_int_sign_flip_right_odd",
)
RZZ_TOMO_PREP_STATES = ("Zp", "Zm", "Xp", "Yp")
RZZ_TOMO_MEAS_AXES = ("X", "Y", "Z")
RZZ_TOMO_EDGE_PARITIES = ("even", "odd")
RZZ_LOCAL_TOMOGRAPHY_PROBES = tuple(
    f"rzz_tomo_p{prep_left}{prep_right}_m{meas_left}{meas_right}_{parity}"
    for prep_left in RZZ_TOMO_PREP_STATES
    for prep_right in RZZ_TOMO_PREP_STATES
    for meas_left in RZZ_TOMO_MEAS_AXES
    for meas_right in RZZ_TOMO_MEAS_AXES
    for parity in RZZ_TOMO_EDGE_PARITIES
)
EDGE_ORIENTATION_RULE = "lower_qubit_to_higher_qubit"
GATE_MECHANISM_IDS = {f"M{idx}" for idx in range(0, 13)}
READOUT_MECHANISM_IDS = {"M13", "M14", "M15", "M16"}
PREP_RESET_MECHANISM_IDS = {"M17", "M18"}
OTHER_MECHANISM_IDS = {"M19"}
RZZ_FAMILY_IDS = ("M1", "M6", "M7", "M9")
AER_GPU_SUPPORTED_METHODS = {
    "statevector",
    "density_matrix",
    "unitary",
    "tensor_network",
}


def default_teacher_config() -> dict[str, object]:
    return {
        "backend": "qiskit_aer_gpu",
        "require_gpu": True,
        "allow_cpu_aer_fallback": False,
        "num_qubits": 5,
        "profile": "phys5_chain",
        "mechanism_set": "set_A",
        "shots": 10_000,
        "seed": 0,
        "theta": 0.18,
        "circuit_depth": 1,
        "probe_set": "base",
        "include_m5": True,
        "include_m6": False,
        "paper_informed_ptm_features": True,
        "aer_simulation_method": "auto",
        "aer_tensor_network_qubit_threshold": 15,
        "aer_large_qubit_method": "matrix_product_state",
        "aer_simulator_options": {},
        "aer_sampling_mode": "batch",
        "aer_sampling_job_batch_size": 0,
        "aer_auto_parallel_experiments": True,
        "aer_max_parallel_experiments_auto_cap": 8,
        "mechanisms": {
            "M0": {"p_x": 0.0015, "p_y": 0.0008, "p_z": 0.0022},
            "M1": {"epsilon": 0.045},
            "M2": {"epsilon": 0.035},
            "M3": {"epsilon": 0.04},
            "M4": {"gamma": 0.018},
            "M5": {"eta": 0.02},
            "M6": {"p": 0.006},
            "M7": {"epsilon_x": 0.024, "epsilon_y": 0.017},
            "M8": {"epsilon": 0.025},
            "M9": {"gamma": 0.012},
            "M10": {"axis": "rx", "epsilon_mean": 0.032, "epsilon_span": 0.018},
            "M11": {"p_z": 0.0025},
            "M12": {"axis": "rx", "epsilon": 0.028},
            "M13": {"p": 0.025},
            "M14": {"p": 0.011},
            "M15": {"p": 0.018},
            "M16": {"p": 0.02},
            "M17": {"p": 0.018},
            "M18": {"epsilon": 0.025},
            "M19": {"eta": 0.006},
        },
    }


def build_default_oracle_mechanisms(config: dict[str, object] | None = None) -> list[MechanismSpec]:
    cfg = _merged_config(config)
    if _balanced_profile_enabled(cfg):
        return _build_balanced_oracle_mechanisms(cfg)
    params = dict(cfg.get("mechanisms", {}))
    n = int(cfg.get("num_qubits", 5))
    enabled = _enabled_mechanism_ids(cfg)
    specs: list[MechanismSpec] = []
    single_targets = _single_targets(n)
    if "M0" in enabled:
        specs.append(MechanismSpec("M0", "stochastic_pauli_gate_error", 1, dict(params.get("M0", {})), instruction="id", qubits=(single_targets["M0"],)))
    if "M2" in enabled:
        specs.append(MechanismSpec("M2", "coherent_rx_overrotation", 1, dict(params.get("M2", {})), instruction="rx", qubits=(single_targets["M2"],)))
    if "M3" in enabled:
        specs.append(MechanismSpec("M3", "coherent_rz_overrotation", 1, dict(params.get("M3", {})), instruction="rz", qubits=(single_targets["M3"],)))
    if "M4" in enabled:
        specs.append(MechanismSpec("M4", "amplitude_damping_gate_error", 1, dict(params.get("M4", {})), instruction="id", qubits=(single_targets["M4"],)))
    if "M5" in enabled:
        specs.append(MechanismSpec("M5", "hard_non_pauli_kraus_gate_error", 1, dict(params.get("M5", {})), instruction="id", qubits=(single_targets["M5"],)))
    if "M8" in enabled:
        specs.append(MechanismSpec("M8", "spectator_crosstalk_rz_or_zz", 1, dict(params.get("M8", {})), instruction="id", qubits=(single_targets["M8"],)))
    if "M10" in enabled:
        drift = dict(params.get("M10", {}))
        axis = str(drift.get("axis", "rx")).lower()
        instruction = "rz" if axis == "rz" else "rx"
        for drift_idx, (target, epsilon) in enumerate(zip(_drift_targets(n), _drift_epsilons(drift, len(_drift_targets(n))))):
            local_drift = dict(drift)
            local_drift["epsilon"] = float(epsilon)
            local_drift["drift_index"] = int(drift_idx)
            specs.append(
                MechanismSpec(
                    "M10",
                    "drifted_coherent_overrotation",
                    1,
                    local_drift,
                    instruction=instruction,
                    qubits=(target,),
                )
            )
    if "M11" in enabled:
        specs.append(MechanismSpec("M11", "idle_dephasing_or_relaxation_error", 1, dict(params.get("M11", {})), instruction="id", qubits=(single_targets["M11"],)))
    if "M12" in enabled:
        specs.append(MechanismSpec("M12", "operation_dependent_error", 1, dict(params.get("M12", {})), instruction=str(params.get("M12", {}).get("instruction", "rx")), qubits=(single_targets["M12"],)))
    if "M17" in enabled:
        specs.append(MechanismSpec("M17", "reset_to_1_bias", 1, dict(params.get("M17", {})), instruction="reset", qubits=(single_targets["M17"],)))
    if "M18" in enabled:
        specs.append(MechanismSpec("M18", "prep_axis_or_reset_asymmetry_bias", 1, dict(params.get("M18", {})), instruction="reset", qubits=(single_targets["M18"],)))
    if "M19" in enabled:
        specs.append(MechanismSpec("M19", "weak_type4_ptm_mixing", 1, dict(params.get("M19", {})), instruction="id", qubits=(single_targets["M19"],)))

    pair_plan = _pair_mechanism_plan(n, enabled)
    for mech, left in pair_plan:
        names = {
            "M1": "coherent_rzz_overrotation",
            "M6": "two_qubit_depolarizing_after_rzz",
            "M7": "coherent_rxx_ryy_perturbation",
            "M9": "correlated_two_qubit_relaxation",
        }
        specs.append(MechanismSpec(mech, names[mech], 2, dict(params.get(mech, {})), instruction="rzz", qubits=(left, left + 1)))

    for readout_idx, (mech, name) in enumerate((
        ("M13", "readout_0_to_1_bias"),
        ("M14", "readout_1_to_0_bias"),
        ("M15", "readout_symmetric_assignment_noise"),
        ("M16", "measurement_context_bias"),
    )):
        if mech in enabled:
            q = (readout_idx + int(cfg.get("balanced_batch_index", 0) or 0)) % n
            specs.append(MechanismSpec(mech, name, 1, dict(params.get(mech, {})), instruction="measure", qubits=(q,)))
    return sorted(specs, key=lambda spec: (_mechanism_sort_key(spec.mechanism_id), spec.qubits))


def generate_physical_teacher_dataset(
    config: dict[str, object] | None = None,
    *,
    output_dir: str | Path = "outputs/scope_static/S2D_PHYS1_teacher",
    preflight_dir: str | Path = "outputs/scope_static/S2D_PHYS0_preflight",
) -> dict[str, object]:
    cfg = _merged_config(config)
    audit = audit_aer_backend(
        backend=str(cfg.get("backend", "qiskit_aer_gpu")),
        require_gpu=bool(cfg.get("require_gpu", True)),
        allow_cpu_aer_fallback=bool(cfg.get("allow_cpu_aer_fallback", False)),
    )
    write_backend_audit(audit, preflight_dir)
    if not bool(audit.get("backend_usable")):
        raise RuntimeError("S2D_PHYS1_teacher requires a passing S2D_PHYS0_preflight backend audit")
    if _balanced_profile_enabled(cfg):
        return _generate_balanced_physical_teacher_dataset(cfg, output_dir=output_dir, preflight_dir=preflight_dir, audit=audit)

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    circuits, probe_names = build_probe_circuits(cfg)
    probe_manifest = build_probe_basis_manifest(
        probe_names,
        num_qubits=int(cfg.get("num_qubits", 5)),
        circuit_depth=_circuit_depth(cfg),
    )
    noise_model, mechanisms = build_qiskit_noise_model(cfg)
    observations, sampling_warnings, sampling_audit = _sample_circuits(circuits, cfg, noise_model)
    aer_settings = resolve_aer_simulator_settings(cfg)
    np.savez_compressed(
        output / "observations.npz",
        observations=observations,
        probe_names=np.asarray(probe_names),
        shots=np.asarray([int(cfg.get("shots", 10_000))], dtype=np.int64),
    )
    mechanism_records = [_mechanism_record(idx, spec) for idx, spec in enumerate(mechanisms)]
    noise_application = build_noise_application_audit(mechanisms, probe_names=probe_names, config=cfg)
    non_clifford_audit = build_non_clifford_audit(mechanisms, probe_names=probe_names, config=cfg)
    (output / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": mechanism_records}, indent=2, sort_keys=True) + "\n")
    (output / "teacher_config.json").write_text(json.dumps(cfg, indent=2, sort_keys=True) + "\n")
    (output / "active_probe_manifest.json").write_text(json.dumps(probe_manifest, indent=2, sort_keys=True) + "\n")
    (output / "noise_application_audit.json").write_text(json.dumps(noise_application, indent=2, sort_keys=True) + "\n")
    (output / "non_clifford_audit.json").write_text(json.dumps(non_clifford_audit, indent=2, sort_keys=True) + "\n")
    (output / "sampling_audit.json").write_text(json.dumps(sampling_audit, indent=2, sort_keys=True) + "\n")
    summary = {
        "stage": "S2D_PHYS1_teacher",
        "output_dir": str(output),
        "num_probes": len(probe_names),
        "num_qubits": int(cfg.get("num_qubits", 5)),
        "shots": int(cfg.get("shots", 10_000)),
        "mechanism_counts": _mechanism_counts(mechanism_records),
        "backend_audit_dir": str(preflight_dir),
        "aer_simulator": _summary_aer_settings(aer_settings),
        "active_probe_manifest": str(output / "active_probe_manifest.json"),
        "noise_application_audit": str(output / "noise_application_audit.json"),
        "sampling": sampling_audit,
        "sampling_audit": str(output / "sampling_audit.json"),
        "non_clifford_teacher": bool(non_clifford_audit["non_clifford_teacher"]),
        "non_clifford_audit": str(output / "non_clifford_audit.json"),
        "warnings": _merged_warning_strings(audit.get("warnings", []), sampling_warnings),
    }
    (output / "summary.md").write_text(format_teacher_summary(summary))
    return {**summary, "oracle_mechanisms": mechanism_records}


def _generate_balanced_physical_teacher_dataset(
    cfg: dict[str, object],
    *,
    output_dir: str | Path,
    preflight_dir: str | Path,
    audit: dict[str, object],
) -> dict[str, object]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    all_observations = []
    all_probe_names: list[str] = []
    all_mechanisms: list[MechanismSpec] = []
    sampling_warnings: list[dict[str, str]] = []
    sampling_audits: list[dict[str, object]] = []
    local_probe_count = 0
    for circuit_id in range(_balanced_repetitions(cfg)):
        batch_cfg = dict(cfg)
        batch_cfg["balanced_batch_index"] = circuit_id
        circuits, probe_names = _build_single_probe_circuits(batch_cfg)
        mechanisms = _build_balanced_oracle_mechanism_batch(batch_cfg, circuit_id=circuit_id)
        probe_indices = tuple(range(local_probe_count, local_probe_count + len(probe_names)))
        mechanisms = [
            MechanismSpec(
                spec.mechanism_id,
                spec.name,
                spec.num_qubits,
                dict(spec.parameters),
                instruction=spec.instruction,
                qubits=spec.qubits,
                circuit_id=circuit_id,
                probe_indices=probe_indices,
            )
            for spec in mechanisms
        ]
        noise_model, _ = _build_qiskit_noise_model_for_mechanisms(batch_cfg, mechanisms)
        observations, warnings_for_batch, sampling_audit = _sample_circuits(circuits, batch_cfg, noise_model)
        all_observations.append(observations)
        all_probe_names.extend([f"c{circuit_id}:{name}" for name in probe_names])
        all_mechanisms.extend(mechanisms)
        sampling_warnings.extend(warnings_for_batch)
        sampling_audits.append(sampling_audit)
        local_probe_count += len(probe_names)

    observations = np.concatenate(all_observations, axis=0)
    probe_manifest = build_probe_basis_manifest(
        all_probe_names,
        num_qubits=int(cfg.get("num_qubits", 9)),
        circuit_depth=_circuit_depth(cfg),
    )
    np.savez_compressed(
        output / "observations.npz",
        observations=observations,
        probe_names=np.asarray(all_probe_names),
        shots=np.asarray([int(cfg.get("shots", 10_000))], dtype=np.int64),
    )
    mechanism_records = [_mechanism_record(idx, spec) for idx, spec in enumerate(all_mechanisms)]
    aer_settings = resolve_aer_simulator_settings(cfg)
    noise_application = build_noise_application_audit(all_mechanisms, probe_names=all_probe_names, config=cfg)
    non_clifford_audit = build_non_clifford_audit(all_mechanisms, probe_names=all_probe_names, config=cfg)
    sampling_audit = _merge_sampling_audits(sampling_audits, config=cfg)
    (output / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": mechanism_records}, indent=2, sort_keys=True) + "\n")
    (output / "teacher_config.json").write_text(json.dumps(cfg, indent=2, sort_keys=True) + "\n")
    (output / "active_probe_manifest.json").write_text(json.dumps(probe_manifest, indent=2, sort_keys=True) + "\n")
    (output / "noise_application_audit.json").write_text(json.dumps(noise_application, indent=2, sort_keys=True) + "\n")
    (output / "non_clifford_audit.json").write_text(json.dumps(non_clifford_audit, indent=2, sort_keys=True) + "\n")
    (output / "sampling_audit.json").write_text(json.dumps(sampling_audit, indent=2, sort_keys=True) + "\n")
    summary = {
        "stage": "S2D_PHYS1_teacher",
        "output_dir": str(output),
        "num_probes": len(all_probe_names),
        "num_qubits": int(cfg.get("num_qubits", 9)),
        "shots": int(cfg.get("shots", 10_000)),
        "mechanism_counts": _mechanism_counts(mechanism_records),
        "balanced_min_instances_per_mechanism": int(cfg.get("balanced_min_instances_per_mechanism", 3)),
        "multicircuit_teacher_batch": True,
        "num_circuit_batches": _balanced_repetitions(cfg),
        "backend_audit_dir": str(preflight_dir),
        "aer_simulator": _summary_aer_settings(aer_settings),
        "active_probe_manifest": str(output / "active_probe_manifest.json"),
        "noise_application_audit": str(output / "noise_application_audit.json"),
        "sampling": sampling_audit,
        "sampling_audit": str(output / "sampling_audit.json"),
        "non_clifford_teacher": bool(non_clifford_audit["non_clifford_teacher"]),
        "non_clifford_audit": str(output / "non_clifford_audit.json"),
        "warnings": _merged_warning_strings(audit.get("warnings", []), sampling_warnings),
    }
    (output / "summary.md").write_text(format_teacher_summary(summary))
    return {**summary, "oracle_mechanisms": mechanism_records}


def build_probe_circuits(config: dict[str, object] | None = None):
    cfg = _merged_config(config)
    if _balanced_profile_enabled(cfg):
        all_circuits = []
        all_probe_names = []
        for circuit_id in range(_balanced_repetitions(cfg)):
            circuits, probe_names = _build_single_probe_circuits(cfg)
            all_circuits.extend(circuits)
            all_probe_names.extend([f"c{circuit_id}:{name}" for name in probe_names])
        return all_circuits, all_probe_names
    return _build_single_probe_circuits(cfg)


def _build_single_probe_circuits(config: dict[str, object] | None = None):
    from qiskit import QuantumCircuit

    cfg = _merged_config(config)
    n = int(cfg.get("num_qubits", 5))
    theta = float(cfg.get("theta", 0.18))
    circuit_depth = _circuit_depth(cfg)
    probe_names = _probe_names(str(cfg.get("probe_set", "base")))
    circuits = []
    for probe in probe_names:
        qc = QuantumCircuit(n, n)
        if any(_mechanism_set_contains(cfg, mech) for mech in PREP_RESET_MECHANISM_IDS):
            for q in range(n):
                qc.reset(q)
        if probe in {"x_basis", "full_x"}:
            for q in range(n):
                qc.h(q)
        elif probe in {"y_basis", "full_y"}:
            for q in range(n):
                qc.h(q)
                qc.s(q)
        elif probe == "alternating_x":
            for q in range(0, n, 2):
                qc.h(q)
        elif probe == "echo":
            for q in range(n):
                qc.x(q)
        _apply_rzz_tomography_preparation(qc, probe, n)
        rx_qubits = set(_profile_rx_qubits(n))
        rz_qubits = set(_profile_rz_qubits(n))
        if any(_mechanism_set_contains(cfg, mech) for mech in ("M10", "M12")):
            mechanism_params = cfg.get("mechanisms", {})
            m10_params = (
                dict(mechanism_params.get("M10", {}))
                if isinstance(mechanism_params, dict) and isinstance(mechanism_params.get("M10", {}), dict)
                else {}
            )
            if _mechanism_set_contains(cfg, "M10"):
                axis = str(m10_params.get("axis", "rx")).lower()
                if axis == "rz":
                    rz_qubits.update(_drift_targets(n))
                else:
                    rx_qubits.update(_drift_targets(n))
            m12_params = (
                dict(mechanism_params.get("M12", {}))
                if isinstance(mechanism_params, dict) and isinstance(mechanism_params.get("M12", {}), dict)
                else {}
            )
            if _mechanism_set_contains(cfg, "M12"):
                axis = str(m12_params.get("axis", "rx")).lower()
                targets = [_single_targets(n)["M12"]]
                if axis == "rz":
                    rz_qubits.update(targets)
                else:
                    rx_qubits.update(targets)
        for _layer_idx in range(circuit_depth):
            for q in range(n):
                qc.id(q)
            for q in sorted(rx_qubits):
                qc.rx(0.13 + 0.01 * (q % 3), q)
            for q in sorted(rz_qubits):
                qc.rz(0.09 + 0.01 * (q % 2), q)
            if _is_rzz_tomography_probe(probe):
                _apply_rzz_tomography_block(qc, probe, n, theta)
            elif _is_rzz_echo_probe(probe):
                _apply_rzz_echo_block(qc, probe, n, theta)
            elif _is_rzz_minimal_sign_probe(probe):
                _apply_rzz_minimal_sign_block(qc, probe, n, theta)
            else:
                _apply_rzz_pauli_frame(qc, probe, n)
                for _depth_step in range(_probe_rzz_depth(probe)):
                    for left in range(n - 1):
                        qc.rzz(theta, left, left + 1)
                _apply_rzz_pauli_frame(qc, probe, n)
        if probe == "echo":
            for q in range(n):
                qc.x(q)
        _apply_measurement_basis_rotations(qc, probe, n)
        qc.measure(range(n), range(n))
        circuits.append(qc)
    return circuits, probe_names


def build_probe_basis_manifest(probe_names: Iterable[str], *, num_qubits: int, circuit_depth: int = 1) -> dict[str, object]:
    """Visible probe-basis metadata, independent of oracle channels or labels."""

    n = int(num_qubits)
    records = []
    for idx, name in enumerate(probe_names):
        basis = probe_basis_by_qubit(str(name), num_qubits=n)
        records.append(
            {
                "probe_index": int(idx),
                "probe_name": str(name),
                "base_probe_name": _probe_base_name(str(name)),
                "basis_by_qubit": basis,
                "rzz_depth": _probe_rzz_depth(str(name)),
                "rzz_echo_role": probe_rzz_echo_role(str(name)),
                "rzz_echo_edge_parity": probe_rzz_echo_edge_parity(str(name)),
                "rzz_echo_edge_pairs": _rzz_echo_edge_pairs(str(name), n),
                "rzz_intervention_family": probe_rzz_intervention_family(str(name)),
                "rzz_intervention_role": probe_rzz_intervention_role(str(name)),
                "rzz_intervention_edge_parity": probe_rzz_intervention_edge_parity(str(name)),
                "rzz_intervention_pauli_frame": probe_rzz_intervention_pauli_frame(str(name)),
                "rzz_intervention_edge_pairs": _rzz_intervention_edge_pairs(str(name), n),
                "rzz_tomography_prep": probe_rzz_tomography_prep(str(name)),
                "rzz_tomography_measurement": probe_rzz_tomography_measurement(str(name)),
                "rzz_tomography_edge_parity": probe_rzz_tomography_edge_parity(str(name)),
                "rzz_tomography_edge_pairs": _rzz_tomography_edge_pairs(str(name), n),
                "circuit_depth": int(circuit_depth),
                "edge_orientation_rule": EDGE_ORIENTATION_RULE,
                "measurable_edge_pairs": [
                    {
                        "edge": [int(left), int(left + 1)],
                        "basis_pair": f"{basis[left]}{basis[left + 1]}",
                    }
                    for left in range(max(0, n - 1))
                ],
                "source": "visible_circuit_schedule",
                "uses_oracle_label": False,
                "uses_exact_teacher_channel": False,
                "uses_exact_ptm": False,
            }
        )
    return {
        "schema": "scope_static_s2d_active_probe_manifest_v1",
        "probe_set_role": "learner_visible_measurement_metadata",
        "edge_orientation_rule": EDGE_ORIENTATION_RULE,
        "num_qubits": n,
        "circuit_depth": int(circuit_depth),
        "probe_records": records,
    }


def probe_basis_by_qubit(probe_name: str, *, num_qubits: int) -> list[str]:
    base = _probe_base_name(str(probe_name))
    n = int(num_qubits)
    if base in {"x_measure", "full_x"}:
        return ["X" for _ in range(n)]
    if base in {"y_measure", "full_y"}:
        return ["Y" for _ in range(n)]
    if base.startswith("alt_") and len(base) == len("alt_xz"):
        left_axis = base[-2].upper()
        right_axis = base[-1].upper()
        if left_axis in {"X", "Y", "Z"} and right_axis in {"X", "Y", "Z"}:
            return [left_axis if q % 2 == 0 else right_axis for q in range(n)]
    if base.startswith("rzz_int_basis_"):
        suffix = base[len("rzz_int_basis_") :].lower()
        if suffix in {"x", "y", "z"}:
            return [suffix.upper() for _ in range(n)]
        if suffix in {"xz", "yz", "xy", "yx"}:
            left_axis = suffix[0].upper()
            right_axis = suffix[1].upper()
            return [left_axis if q % 2 == 0 else right_axis for q in range(n)]
    tomo = _parse_rzz_tomography_probe(base)
    if tomo is not None:
        basis = ["Z" for _ in range(n)]
        meas_left, meas_right = str(tomo["meas_left"]), str(tomo["meas_right"])
        parity = str(tomo["parity"])
        for left in _edge_left_indices_for_parity(parity, n):
            basis[left] = meas_left
            basis[left + 1] = meas_right
        return basis
    return ["Z" for _ in range(n)]


def probe_rzz_depth(probe_name: str) -> int:
    return _probe_rzz_depth(str(probe_name))


def probe_rzz_echo_role(probe_name: str) -> str:
    return _probe_rzz_echo_role(str(probe_name))


def probe_rzz_echo_edge_parity(probe_name: str) -> str:
    return _probe_rzz_echo_edge_parity(str(probe_name))


def probe_rzz_intervention_family(probe_name: str) -> str:
    return _probe_rzz_intervention_family(str(probe_name))


def probe_rzz_intervention_role(probe_name: str) -> str:
    return _probe_rzz_intervention_role(str(probe_name))


def probe_rzz_intervention_edge_parity(probe_name: str) -> str:
    return _probe_rzz_intervention_edge_parity(str(probe_name))


def probe_rzz_intervention_pauli_frame(probe_name: str) -> dict[str, object]:
    return _probe_rzz_intervention_pauli_frame(str(probe_name))


def probe_rzz_tomography_prep(probe_name: str) -> dict[str, str]:
    parsed = _parse_rzz_tomography_probe(str(probe_name))
    if parsed is None:
        return {"left": "none", "right": "none"}
    return {"left": str(parsed["prep_left"]), "right": str(parsed["prep_right"])}


def probe_rzz_tomography_measurement(probe_name: str) -> dict[str, str]:
    parsed = _parse_rzz_tomography_probe(str(probe_name))
    if parsed is None:
        return {"left": "none", "right": "none"}
    return {"left": str(parsed["meas_left"]), "right": str(parsed["meas_right"])}


def probe_rzz_tomography_edge_parity(probe_name: str) -> str:
    parsed = _parse_rzz_tomography_probe(str(probe_name))
    return "none" if parsed is None else str(parsed["parity"])


def _probe_base_name(name: str) -> str:
    text = str(name)
    return text.split(":", 1)[1] if ":" in text else text


def _probe_rzz_depth(name: str) -> int:
    base = _probe_base_name(str(name))
    prefix = "rzz_depth_"
    if base.startswith(prefix):
        try:
            value = int(base[len(prefix) :])
        except ValueError:
            return 1
        return value if value in set(RZZ_DEPTH_SWEEP_DEPTHS) else 1
    return 1


def _is_rzz_echo_probe(name: str) -> bool:
    return _probe_base_name(str(name)) in set(RZZ_ECHO_CONTRAST_PROBES)


def _is_rzz_minimal_intervention_probe(name: str) -> bool:
    return _probe_base_name(str(name)) in set(RZZ_MINIMAL_INTERVENTION_PROBES)


def _is_rzz_tomography_probe(name: str) -> bool:
    return _parse_rzz_tomography_probe(str(name)) is not None


def _is_rzz_minimal_sign_probe(name: str) -> bool:
    return _probe_rzz_intervention_family(str(name)) == "sign_flip_echo"


def _probe_rzz_echo_role(name: str) -> str:
    base = _probe_base_name(str(name))
    if base == "rzz_no_echo":
        return "no_echo"
    if base.startswith("rzz_echo_left_"):
        return "echo_left"
    if base.startswith("rzz_echo_right_"):
        return "echo_right"
    if base.startswith("rzz_echo_both_"):
        return "echo_both"
    return "none"


def _probe_rzz_echo_edge_parity(name: str) -> str:
    base = _probe_base_name(str(name))
    if base == "rzz_no_echo":
        return "all"
    if base.endswith("_even"):
        return "even"
    if base.endswith("_odd"):
        return "odd"
    return "none"


def _rzz_echo_edge_pairs(name: str, num_qubits: int) -> list[dict[str, object]]:
    role = _probe_rzz_echo_role(str(name))
    parity = _probe_rzz_echo_edge_parity(str(name))
    if role == "none":
        return []
    out = []
    for left in range(max(0, int(num_qubits) - 1)):
        selected = parity == "all" or (parity == "even" and left % 2 == 0) or (parity == "odd" and left % 2 == 1)
        if selected:
            out.append({"edge": [int(left), int(left + 1)], "echo_role": role, "edge_parity": parity})
    return out


def _probe_rzz_intervention_family(name: str) -> str:
    base = _probe_base_name(str(name))
    if base == "rzz_int_no_intervention":
        return "baseline"
    if base.startswith("rzz_int_basis_"):
        return "basis_rotation"
    if base.startswith("rzz_int_twirl_"):
        return "pauli_frame_twirl"
    if base.startswith("rzz_int_sign_"):
        return "sign_flip_echo"
    return "none"


def _probe_rzz_intervention_role(name: str) -> str:
    base = _probe_base_name(str(name))
    if base == "rzz_int_no_intervention":
        return "no_intervention"
    if base.startswith("rzz_int_basis_"):
        return base[len("rzz_int_basis_") :]
    if base.startswith("rzz_int_twirl_"):
        body = base[len("rzz_int_twirl_") :]
        if body.startswith("x_left_"):
            return "twirl_x_left"
        if body.startswith("y_left_"):
            return "twirl_y_left"
        if body.startswith("xy_"):
            return "twirl_xy"
    if base == "rzz_int_sign_no_flip":
        return "sign_no_flip"
    if base.startswith("rzz_int_sign_flip_left_"):
        return "sign_flip_left"
    if base.startswith("rzz_int_sign_flip_right_"):
        return "sign_flip_right"
    return "none"


def _probe_rzz_intervention_edge_parity(name: str) -> str:
    base = _probe_base_name(str(name))
    if not _is_rzz_minimal_intervention_probe(base):
        return "none"
    if base in {"rzz_int_no_intervention", "rzz_int_sign_no_flip"} or base.startswith("rzz_int_basis_"):
        return "all"
    if base.endswith("_even"):
        return "even"
    if base.endswith("_odd"):
        return "odd"
    return "none"


def _probe_rzz_intervention_pauli_frame(name: str) -> dict[str, object]:
    role = _probe_rzz_intervention_role(str(name))
    if role == "twirl_x_left":
        return {"left": "X", "right": "I"}
    if role == "twirl_y_left":
        return {"left": "Y", "right": "I"}
    if role == "twirl_xy":
        return {"left": "X", "right": "Y"}
    if role == "sign_flip_left":
        return {"left": "X", "right": "I"}
    if role == "sign_flip_right":
        return {"left": "I", "right": "X"}
    return {"left": "I", "right": "I"}


def _rzz_intervention_edge_pairs(name: str, num_qubits: int) -> list[dict[str, object]]:
    family = _probe_rzz_intervention_family(str(name))
    role = _probe_rzz_intervention_role(str(name))
    parity = _probe_rzz_intervention_edge_parity(str(name))
    if family == "none":
        return []
    frame = _probe_rzz_intervention_pauli_frame(str(name))
    out = []
    for left in range(max(0, int(num_qubits) - 1)):
        selected = parity == "all" or (parity == "even" and left % 2 == 0) or (parity == "odd" and left % 2 == 1)
        if selected:
            out.append(
                {
                    "edge": [int(left), int(left + 1)],
                    "intervention_family": family,
                    "intervention_role": role,
                    "edge_parity": parity,
                    "pauli_frame": frame,
                }
            )
    return out


def _parse_rzz_tomography_probe(name: str) -> dict[str, str] | None:
    base = _probe_base_name(str(name))
    prefix = "rzz_tomo_p"
    if not base.startswith(prefix):
        return None
    try:
        prep_part, rest = base[len(prefix) :].split("_m", 1)
        meas_part, parity = rest.split("_", 1)
    except ValueError:
        return None
    if len(prep_part) != 4 or len(meas_part) != 2:
        return None
    prep_left = prep_part[:2]
    prep_right = prep_part[2:]
    meas_left = meas_part[0]
    meas_right = meas_part[1]
    if prep_left not in RZZ_TOMO_PREP_STATES or prep_right not in RZZ_TOMO_PREP_STATES:
        return None
    if meas_left not in RZZ_TOMO_MEAS_AXES or meas_right not in RZZ_TOMO_MEAS_AXES:
        return None
    if parity not in RZZ_TOMO_EDGE_PARITIES:
        return None
    return {
        "prep_left": prep_left,
        "prep_right": prep_right,
        "meas_left": meas_left,
        "meas_right": meas_right,
        "parity": parity,
    }


def _rzz_tomography_edge_pairs(name: str, num_qubits: int) -> list[dict[str, object]]:
    parsed = _parse_rzz_tomography_probe(str(name))
    if parsed is None:
        return []
    return [
        {
            "edge": [int(left), int(left + 1)],
            "prep": {"left": parsed["prep_left"], "right": parsed["prep_right"]},
            "measurement": {"left": parsed["meas_left"], "right": parsed["meas_right"]},
            "edge_parity": parsed["parity"],
        }
        for left in _edge_left_indices_for_parity(str(parsed["parity"]), int(num_qubits))
    ]


def _edge_left_indices_for_parity(parity: str, num_qubits: int) -> list[int]:
    start = 0 if str(parity) == "even" else 1
    return list(range(start, max(0, int(num_qubits) - 1), 2))


def _apply_rzz_echo_block(qc, probe: str, num_qubits: int, theta: float) -> None:
    role = _probe_rzz_echo_role(str(probe))
    parity = _probe_rzz_echo_edge_parity(str(probe))
    half_theta = float(theta) / 2.0
    for left in range(int(num_qubits) - 1):
        qc.rzz(half_theta, left, left + 1)
    echoed = _echo_qubits_for_role(role, parity, int(num_qubits))
    for q in echoed:
        qc.x(q)
    for left in range(int(num_qubits) - 1):
        qc.rzz(half_theta, left, left + 1)
    for q in echoed:
        qc.x(q)


def _echo_qubits_for_role(role: str, parity: str, num_qubits: int) -> list[int]:
    if role == "no_echo":
        return []
    qubits: set[int] = set()
    for left in range(max(0, int(num_qubits) - 1)):
        selected = parity == "all" or (parity == "even" and left % 2 == 0) or (parity == "odd" and left % 2 == 1)
        if not selected:
            continue
        if role in {"echo_left", "echo_both"}:
            qubits.add(left)
        if role in {"echo_right", "echo_both"}:
            qubits.add(left + 1)
    return sorted(qubits)


def _apply_rzz_tomography_preparation(qc, probe: str, num_qubits: int) -> None:
    parsed = _parse_rzz_tomography_probe(str(probe))
    if parsed is None:
        return
    for left in _edge_left_indices_for_parity(str(parsed["parity"]), int(num_qubits)):
        _prepare_tomography_state(qc, left, str(parsed["prep_left"]))
        _prepare_tomography_state(qc, left + 1, str(parsed["prep_right"]))


def _prepare_tomography_state(qc, qubit: int, prep: str) -> None:
    if prep == "Zp":
        return
    if prep == "Zm":
        qc.x(qubit)
    elif prep == "Xp":
        qc.h(qubit)
    elif prep == "Yp":
        qc.h(qubit)
        qc.s(qubit)


def _apply_rzz_tomography_block(qc, probe: str, num_qubits: int, theta: float) -> None:
    parsed = _parse_rzz_tomography_probe(str(probe))
    if parsed is None:
        return
    for left in _edge_left_indices_for_parity(str(parsed["parity"]), int(num_qubits)):
        qc.rzz(float(theta), left, left + 1)


def _apply_rzz_minimal_sign_block(qc, probe: str, num_qubits: int, theta: float) -> None:
    role = _probe_rzz_intervention_role(str(probe))
    parity = _probe_rzz_intervention_edge_parity(str(probe))
    half_theta = float(theta) / 2.0
    for left in range(int(num_qubits) - 1):
        qc.rzz(half_theta, left, left + 1)
    flipped = _intervention_qubits_for_role(role, parity, int(num_qubits))
    for q in flipped:
        qc.x(q)
    for left in range(int(num_qubits) - 1):
        qc.rzz(half_theta, left, left + 1)
    for q in flipped:
        qc.x(q)


def _apply_rzz_pauli_frame(qc, probe: str, num_qubits: int) -> None:
    if _probe_rzz_intervention_family(str(probe)) != "pauli_frame_twirl":
        return
    role = _probe_rzz_intervention_role(str(probe))
    parity = _probe_rzz_intervention_edge_parity(str(probe))
    for q, axis in _intervention_pauli_operations_for_role(role, parity, int(num_qubits)):
        if axis == "X":
            qc.x(q)
        elif axis == "Y":
            qc.y(q)


def _intervention_qubits_for_role(role: str, parity: str, num_qubits: int) -> list[int]:
    qubits: set[int] = set()
    for left in range(max(0, int(num_qubits) - 1)):
        selected = parity == "all" or (parity == "even" and left % 2 == 0) or (parity == "odd" and left % 2 == 1)
        if not selected:
            continue
        if role == "sign_flip_left":
            qubits.add(left)
        elif role == "sign_flip_right":
            qubits.add(left + 1)
    return sorted(qubits)


def _intervention_pauli_operations_for_role(role: str, parity: str, num_qubits: int) -> list[tuple[int, str]]:
    operations: list[tuple[int, str]] = []
    for left in range(max(0, int(num_qubits) - 1)):
        selected = parity == "all" or (parity == "even" and left % 2 == 0) or (parity == "odd" and left % 2 == 1)
        if not selected:
            continue
        if role == "twirl_x_left":
            operations.append((left, "X"))
        elif role == "twirl_y_left":
            operations.append((left, "Y"))
        elif role == "twirl_xy":
            operations.append((left, "X"))
            operations.append((left + 1, "Y"))
    return operations


def _apply_measurement_basis_rotations(qc, probe: str, num_qubits: int) -> None:
    basis = probe_basis_by_qubit(str(probe), num_qubits=int(num_qubits))
    for q, axis in enumerate(basis):
        if axis == "X":
            qc.h(q)
        elif axis == "Y":
            qc.sdg(q)
            qc.h(q)


def build_qiskit_noise_model(config: dict[str, object] | None = None):
    try:
        from qiskit_aer.noise import NoiseModel, ReadoutError
        from qiskit_aer.noise.errors import (
            amplitude_damping_error,
            coherent_unitary_error,
            depolarizing_error,
            kraus_error,
            pauli_error,
        )
    except Exception as exc:  # pragma: no cover - depends on optional Aer install
        raise RuntimeError(f"qiskit_aer noise imports failed: {type(exc).__name__}: {exc}") from exc

    cfg = _merged_config(config)
    mechanisms = build_default_oracle_mechanisms(cfg)
    if _balanced_profile_enabled(cfg):
        raise ValueError("balanced multicircuit profiles use one noise model per circuit batch")
    return _build_qiskit_noise_model_for_mechanisms(cfg, mechanisms)


def _build_qiskit_noise_model_for_mechanisms(config: dict[str, object], mechanisms: list[MechanismSpec]):
    try:
        from qiskit_aer.noise import NoiseModel, ReadoutError
        from qiskit_aer.noise.errors import (
            amplitude_damping_error,
            coherent_unitary_error,
            depolarizing_error,
            kraus_error,
            pauli_error,
        )
    except Exception as exc:  # pragma: no cover - depends on optional Aer install
        raise RuntimeError(f"qiskit_aer noise imports failed: {type(exc).__name__}: {exc}") from exc

    noise_model = NoiseModel()
    for spec in mechanisms:
        if spec.mechanism_id in READOUT_MECHANISM_IDS:
            matrix = _readout_matrix_for_spec(spec)
            noise_model.add_readout_error(ReadoutError(matrix.tolist()), list(spec.qubits))
            continue
        error = _quantum_error_for_spec(
            spec,
            pauli_error=pauli_error,
            coherent_unitary_error=coherent_unitary_error,
            amplitude_damping_error=amplitude_damping_error,
            kraus_error=kraus_error,
            depolarizing_error=depolarizing_error,
        )
        noise_model.add_quantum_error(error, [str(spec.instruction)], list(spec.qubits))
    return noise_model, mechanisms


def build_noise_application_audit(
    mechanisms: list[MechanismSpec],
    *,
    probe_names: list[str],
    config: dict[str, object],
) -> dict[str, object]:
    records = []
    for idx, spec in enumerate(mechanisms):
        records.append(
            {
                "location_id": int(idx),
                "oracle_label": spec.mechanism_id,
                "name": spec.name,
                "instruction": spec.instruction,
                "qubits": [int(q) for q in spec.qubits],
                "circuit_id": int(spec.circuit_id),
                "probe_indices": [int(idx) for idx in spec.probe_indices],
                "num_qubits": int(spec.num_qubits),
                "noise_kind": _noise_kind(spec),
                "qiskit_application_api": "add_readout_error" if spec.mechanism_id in READOUT_MECHANISM_IDS else "add_quantum_error",
                "applies_to_all_qubits": False,
                "parameters": {str(key): value for key, value in spec.audit_dict()["parameters"].items()},
                "oracle_label_evaluator_only": True,
            }
        )
    return {
        "schema": "scope_static_s2d_noise_application_audit_v1",
        "stage": "S2D_PHYS1_teacher",
        "backend": str(config.get("backend", "qiskit_aer_gpu")),
        "num_qubits": int(config.get("num_qubits", 5)),
        "probe_names": list(probe_names),
        "mechanism_counts": _mechanism_counts(records),
        "num_noise_applications": len(records),
        "uses_oracle_labels_for_training": False,
        "uses_oracle_labels_for_selection": False,
        "records": records,
    }


def build_non_clifford_audit(
    mechanisms: list[MechanismSpec],
    *,
    probe_names: list[str],
    config: dict[str, object],
) -> dict[str, object]:
    theta = float(config.get("theta", 0.18))
    ideal_records = [
        {
            "source": "ideal_probe_circuit",
            "gate": "rx",
            "angle": 0.13,
            "is_clifford_angle": _is_clifford_angle(0.13),
            "reason": "single-qubit arbitrary-angle probe rotation",
        },
        {
            "source": "ideal_probe_circuit",
            "gate": "rzz",
            "angle": theta,
            "is_clifford_angle": _is_clifford_angle(theta),
            "reason": "two-qubit arbitrary-angle RZZ entangling probe",
        },
    ]
    mechanism_records = []
    for spec in mechanisms:
        if spec.mechanism_id == "M1":
            angle = float(spec.parameters.get("epsilon", 0.045))
            mechanism_records.append(
                {
                    "source": "oracle_noise",
                    "mechanism_id": spec.mechanism_id,
                    "gate": "rzz",
                    "angle": angle,
                    "location_qubits": [int(q) for q in spec.qubits],
                    "is_clifford_angle": _is_clifford_angle(angle),
                    "reason": "coherent RZZ over-rotation",
                }
            )
        elif spec.mechanism_id == "M2":
            angle = float(spec.parameters.get("epsilon", 0.035))
            mechanism_records.append(
                {
                    "source": "oracle_noise",
                    "mechanism_id": spec.mechanism_id,
                    "gate": "rx",
                    "angle": angle,
                    "location_qubits": [int(q) for q in spec.qubits],
                    "is_clifford_angle": _is_clifford_angle(angle),
                    "reason": "coherent RX over-rotation",
                }
            )
        elif spec.mechanism_id == "M3":
            angle = float(spec.parameters.get("epsilon", 0.04))
            mechanism_records.append(
                {
                    "source": "oracle_noise",
                    "mechanism_id": spec.mechanism_id,
                    "gate": "rz",
                    "angle": angle,
                    "location_qubits": [int(q) for q in spec.qubits],
                    "is_clifford_angle": _is_clifford_angle(angle),
                    "reason": "coherent RZ over-rotation",
                }
            )
        elif spec.mechanism_id == "M7":
            angle = float(spec.parameters.get("epsilon_x", spec.parameters.get("epsilon", 0.024)))
            mechanism_records.append(
                {
                    "source": "oracle_noise",
                    "mechanism_id": spec.mechanism_id,
                    "gate": "rxx_ryy",
                    "angle": angle,
                    "location_qubits": [int(q) for q in spec.qubits],
                    "is_clifford_angle": _is_clifford_angle(angle),
                    "reason": "coherent RXX/RYY perturbation",
                }
            )
        elif spec.mechanism_id in {"M8", "M10", "M12", "M18"}:
            angle = float(spec.parameters.get("epsilon", spec.parameters.get("epsilon_mean", 0.03)))
            mechanism_records.append(
                {
                    "source": "oracle_noise",
                    "mechanism_id": spec.mechanism_id,
                    "gate": str(spec.parameters.get("axis", "rz")).lower(),
                    "angle": angle,
                    "location_qubits": [int(q) for q in spec.qubits],
                    "is_clifford_angle": _is_clifford_angle(angle),
                    "reason": "drift/crosstalk coherent over-rotation",
                }
            )
        elif spec.mechanism_id in {"M4", "M5", "M9", "M11", "M19"}:
            mechanism_records.append(
                {
                    "source": "oracle_noise",
                    "mechanism_id": spec.mechanism_id,
                    "gate": None,
                    "angle": None,
                    "location_qubits": [int(q) for q in spec.qubits],
                    "is_clifford_angle": False,
                    "reason": "non-Pauli Kraus channel",
                }
            )
    non_clifford_sources = [record for record in [*ideal_records, *mechanism_records] if not bool(record["is_clifford_angle"])]
    return {
        "schema": "scope_static_s2d_non_clifford_audit_v1",
        "stage": "S2D_PHYS1_teacher",
        "non_clifford_teacher": bool(non_clifford_sources),
        "claim": "teacher_contains_non_clifford_ideal_gates_and_non_clifford_oracle_noise",
        "probe_names": list(probe_names),
        "ideal_gate_records": ideal_records,
        "oracle_noise_records": mechanism_records,
        "non_clifford_sources": non_clifford_sources,
    }


def format_teacher_summary(summary: dict[str, object]) -> str:
    lines = [
        "# S2D PHYS1 Teacher",
        "",
        f"- Output: `{summary['output_dir']}`",
        f"- Probes: `{summary['num_probes']}`",
        f"- Qubits: `{summary['num_qubits']}`",
        f"- Shots: `{summary['shots']}`",
        f"- Backend audit: `{summary['backend_audit_dir']}`",
        f"- Aer simulator: `{_format_aer_settings(summary.get('aer_simulator'))}`",
        f"- Sampling audit: `{summary.get('sampling_audit', '')}`",
        f"- Active probe manifest: `{summary.get('active_probe_manifest', '')}`",
        f"- Noise application audit: `{summary['noise_application_audit']}`",
        f"- Non-Clifford teacher: `{str(bool(summary['non_clifford_teacher'])).lower()}`",
        f"- Non-Clifford audit: `{summary['non_clifford_audit']}`",
        "",
        "| mechanism | count |",
        "| --- | ---: |",
    ]
    counts = summary.get("mechanism_counts", {})
    if isinstance(counts, dict):
        for key, value in sorted(counts.items()):
            lines.append(f"| {key} | {value} |")
    warnings_list = summary.get("warnings", [])
    if isinstance(warnings_list, list) and warnings_list:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {item}" for item in warnings_list)
    lines.append("")
    return "\n".join(lines)


def _quantum_error_for_spec(spec: MechanismSpec, **factories):
    if spec.mechanism_id == "M0":
        p_x = float(spec.parameters.get("p_x", 0.0015))
        p_y = float(spec.parameters.get("p_y", 0.0008))
        p_z = float(spec.parameters.get("p_z", 0.0022))
        p_i = positive_floor(1.0 - p_x - p_y - p_z)
        return factories["pauli_error"]([("I", p_i), ("X", p_x), ("Y", p_y), ("Z", p_z)])
    if spec.mechanism_id == "M1":
        return factories["coherent_unitary_error"](rzz_unitary(float(spec.parameters.get("epsilon", 0.045))))
    if spec.mechanism_id == "M2":
        return factories["coherent_unitary_error"](rx_unitary(float(spec.parameters.get("epsilon", 0.035))))
    if spec.mechanism_id == "M3":
        return factories["coherent_unitary_error"](rz_unitary(float(spec.parameters.get("epsilon", 0.04))))
    if spec.mechanism_id == "M4":
        return factories["amplitude_damping_error"](float(spec.parameters.get("gamma", 0.018)))
    if spec.mechanism_id == "M5":
        return factories["kraus_error"](custom_non_pauli_kraus(float(spec.parameters.get("eta", 0.02))))
    if spec.mechanism_id == "M6":
        return factories["depolarizing_error"](float(spec.parameters.get("p", 0.006)), 2)
    if spec.mechanism_id == "M7":
        return factories["coherent_unitary_error"](
            rxx_ryy_unitary(
                theta_x=float(spec.parameters.get("epsilon_x", spec.parameters.get("epsilon", 0.024))),
                theta_y=float(spec.parameters.get("epsilon_y", float(spec.parameters.get("epsilon", 0.024)) * 0.7)),
            )
        )
    if spec.mechanism_id == "M8":
        return factories["coherent_unitary_error"](rz_unitary(float(spec.parameters.get("epsilon", 0.025))))
    if spec.mechanism_id == "M9":
        return factories["kraus_error"](correlated_relaxation_kraus(float(spec.parameters.get("gamma", 0.012))))
    if spec.mechanism_id == "M10":
        angle = float(spec.parameters.get("epsilon", spec.parameters.get("epsilon_mean", 0.032)))
        axis = str(spec.parameters.get("axis", "rx")).lower()
        return factories["coherent_unitary_error"](rx_unitary(angle) if axis == "rx" else rz_unitary(angle))
    if spec.mechanism_id == "M11":
        p = float(spec.parameters.get("p_z", spec.parameters.get("p", 0.0025)))
        return factories["pauli_error"]([("I", positive_floor(1.0 - p)), ("Z", p)])
    if spec.mechanism_id == "M12":
        angle = float(spec.parameters.get("epsilon", 0.028))
        axis = str(spec.parameters.get("axis", "rx")).lower()
        return factories["coherent_unitary_error"](rx_unitary(angle) if axis == "rx" else rz_unitary(angle))
    if spec.mechanism_id == "M17":
        p = float(spec.parameters.get("p", 0.018))
        return factories["pauli_error"]([("I", positive_floor(1.0 - p)), ("X", p)])
    if spec.mechanism_id == "M18":
        return factories["coherent_unitary_error"](rx_unitary(float(spec.parameters.get("epsilon", 0.025))))
    if spec.mechanism_id == "M19":
        return factories["kraus_error"](weak_type4_mixing_kraus(float(spec.parameters.get("eta", 0.006))))
    raise ValueError(f"unsupported quantum mechanism {spec.mechanism_id!r}")


def _noise_kind(spec: MechanismSpec) -> str:
    if spec.mechanism_id == "M0":
        return "stochastic_pauli_quantum_error"
    if spec.mechanism_id in {"M1", "M2"}:
        return "coherent_unitary_quantum_error"
    if spec.mechanism_id in {"M3", "M7", "M8", "M10", "M12", "M18"}:
        return "coherent_unitary_quantum_error"
    if spec.mechanism_id == "M4":
        return "amplitude_damping_quantum_error"
    if spec.mechanism_id in READOUT_MECHANISM_IDS:
        return "readout_error"
    if spec.mechanism_id in {"M5", "M9", "M19"}:
        return "custom_kraus_quantum_error"
    if spec.mechanism_id == "M11":
        return "idle_pauli_quantum_error"
    if spec.mechanism_id == "M6":
        return "two_qubit_depolarizing_quantum_error"
    if spec.mechanism_id in PREP_RESET_MECHANISM_IDS:
        return "reset_preparation_bias_quantum_error"
    return "unknown"


def _readout_matrix_for_spec(spec: MechanismSpec) -> np.ndarray:
    params = dict(spec.parameters)
    p = float(params.get("p", 0.02))
    p0_to_1 = p if spec.mechanism_id in {"M13", "M15", "M16"} else NUMERICAL_ZERO
    p1_to_0 = p if spec.mechanism_id in {"M14", "M15"} else NUMERICAL_ZERO
    if spec.mechanism_id == "M16":
        p1_to_0 = 0.5 * p
    return readout_bias_matrix(
        p0_to_1=float(params.get("p0_to_1", p0_to_1)),
        p1_to_0=float(params.get("p1_to_0", p1_to_0)),
    )


def _is_clifford_angle(angle: float, *, atol: float = 1e-9) -> bool:
    """Return true for rotations equivalent to integer multiples of pi/2."""

    import math

    scaled = float(angle) / (math.pi / 2.0)
    return abs(scaled - round(scaled)) <= float(atol)


def _sample_circuits(circuits, config: dict[str, object], noise_model) -> tuple[np.ndarray, list[dict[str, str]], dict[str, object]]:
    from qiskit_aer import AerSimulator

    shots = int(config.get("shots", 10_000))
    n = int(config.get("num_qubits", 5))
    circuit_list = list(circuits)
    sampling_mode = _resolve_sampling_mode(config)
    job_batch_size = _resolve_sampling_job_batch_size(config, num_circuits=len(circuit_list), sampling_mode=sampling_mode)
    aer_settings = _apply_sampling_aer_option_defaults(
        resolve_aer_simulator_settings(config),
        config=config,
        sampling_mode=sampling_mode,
        job_batch_size=job_batch_size,
    )
    simulator = AerSimulator(
        method=str(aer_settings["method"]),
        device=str(aer_settings["device"]),
        noise_model=noise_model,
        **dict(aer_settings["options"]),
    )
    results: list[np.ndarray] = []
    warning_records: list[dict[str, str]] = []
    unique_outcome_counts: list[int] = []
    sampling_seconds = 0.0
    materialization_seconds = 0.0
    total_start = time.perf_counter()
    seed = int(config.get("seed", 0))
    num_jobs = 0
    for batch_start, circuit_batch in _sampling_batches(circuit_list, batch_size=job_batch_size, mode=sampling_mode):
        run_input = circuit_batch if sampling_mode == "batch" else circuit_batch[0]
        seed_simulator = seed + (batch_start if sampling_mode == "per_circuit" else num_jobs)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            run_start = time.perf_counter()
            job = simulator.run(run_input, shots=shots, seed_simulator=seed_simulator)
            result = job.result()
            sampling_seconds += time.perf_counter() - run_start
        warning_records.extend(_warning_records(caught))
        counts_by_circuit = _counts_from_aer_result(result, num_circuits=len(circuit_batch), batched=sampling_mode == "batch")
        for counts in counts_by_circuit:
            unique_outcome_counts.append(len(counts))
            materialize_start = time.perf_counter()
            results.append(_counts_to_bit_matrix(counts, shots=shots, num_bits=n))
            materialization_seconds += time.perf_counter() - materialize_start
        num_jobs += 1
    observations = np.stack(results, axis=0) if results else np.zeros((0, shots, n), dtype=np.uint8)
    audit = _sampling_audit(
        config=config,
        aer_settings=aer_settings,
        sampling_mode=sampling_mode,
        job_batch_size=job_batch_size,
        num_jobs=num_jobs,
        num_circuits=len(circuit_list),
        shots=shots,
        unique_outcome_counts=unique_outcome_counts,
        sampling_seconds=sampling_seconds,
        materialization_seconds=materialization_seconds,
        total_seconds=time.perf_counter() - total_start,
    )
    return observations, _dedupe_warning_records(warning_records), audit


def resolve_aer_simulator_settings(config: dict[str, object] | None = None) -> dict[str, object]:
    """Resolve GPU Aer method/device/options for the physical teacher.

    The default stays exact dense density-matrix for small teacher circuits, but
    15+ qubit chain profiles use MPS instead of a dense 2^n x 2^n density
    matrix. Qiskit Aer's MPS method is CPU-only in the Aer builds this project
    targets, so the resolved settings separately audit requested GPU device and
    whether the selected method can actually execute on GPU.
    """

    cfg = _merged_config(config)
    n = int(cfg.get("num_qubits", 5))
    threshold = int(cfg.get("aer_tensor_network_qubit_threshold", 15))
    explicit_method, explicit_source = _explicit_aer_method(cfg)
    if explicit_method is None:
        requested = "auto"
    else:
        requested = explicit_method
    requested = _normalize_aer_method(requested)
    if requested == "auto":
        if n >= threshold:
            method = _normalize_aer_method(str(cfg.get("aer_large_qubit_method", "matrix_product_state")))
            reason = "auto_large_qubit_tensor_network"
        else:
            method = "density_matrix"
            reason = "auto_small_qubit_density_matrix"
    else:
        method = requested
        reason = f"explicit_{explicit_source}"
    device = _resolve_aer_device(cfg)
    options = _aer_simulator_options(cfg)
    if method == "matrix_product_state":
        options.setdefault("matrix_product_state_truncation_threshold", NUMERICAL_ZERO)
    return {
        "method": method,
        "device": device,
        "method_gpu_supported": _aer_method_gpu_supported(method),
        "requested_gpu_method_supported": bool(device == "GPU" and _aer_method_gpu_supported(method)),
        "gpu_support_note": _aer_gpu_support_note(method, device),
        "options": options,
        "num_qubits": n,
        "tensor_network_threshold": threshold,
        "requested_method": requested,
        "selection_reason": reason,
    }


def _explicit_aer_method(config: dict[str, object]) -> tuple[str | None, str]:
    for key in ("aer_simulation_method", "aer_simulator_method", "aer_method"):
        if key in config:
            method = _normalize_aer_method(str(config[key]))
            if method != "auto":
                return method, key
    raw_options = config.get("aer_simulator_options", {})
    if isinstance(raw_options, dict) and "method" in raw_options:
        method = _normalize_aer_method(str(raw_options["method"]))
        if method != "auto":
            return method, "aer_simulator_options.method"
    return None, "default_auto"


def _normalize_aer_method(value: str) -> str:
    text = str(value).strip().lower().replace("-", "_")
    aliases = {
        "": "auto",
        "auto": "auto",
        "scope_auto": "auto",
        "dense": "density_matrix",
        "density": "density_matrix",
        "dm": "density_matrix",
        "density_matrix": "density_matrix",
        "mps": "matrix_product_state",
        "matrix_product_state": "matrix_product_state",
        "matrix_product": "matrix_product_state",
        "tn": "tensor_network",
        "tensor": "tensor_network",
        "tensor_network": "tensor_network",
        "cutensornet": "tensor_network",
        "cu_tensor_net": "tensor_network",
        "cuquantum": "tensor_network",
        "automatic": "automatic",
        "statevector": "statevector",
        "stabilizer": "stabilizer",
        "extended_stabilizer": "extended_stabilizer",
        "unitary": "unitary",
        "superop": "superop",
    }
    if text not in aliases:
        supported = ", ".join(sorted(set(aliases.values())))
        raise ValueError(f"unsupported Aer simulation method {value!r}; expected one of {supported}")
    return aliases[text]


def _resolve_aer_device(config: dict[str, object]) -> str:
    explicit: object | None = None
    for key in ("aer_device", "aer_simulator_device"):
        if key in config:
            explicit = config[key]
            break
    raw_options = config.get("aer_simulator_options", {})
    if explicit is None and isinstance(raw_options, dict) and "device" in raw_options:
        explicit = raw_options["device"]
    if explicit is None:
        device = "GPU" if str(config.get("backend", "qiskit_aer_gpu")) == "qiskit_aer_gpu" or bool(config.get("require_gpu", True)) else "CPU"
    else:
        device = str(explicit).strip().upper()
    if device not in {"CPU", "GPU"}:
        raise ValueError(f"unsupported Aer simulator device {device!r}; expected 'CPU' or 'GPU'")
    if device == "CPU" and bool(config.get("require_gpu", True)) and not bool(config.get("allow_cpu_aer_fallback", False)):
        raise ValueError("Aer simulator device is CPU but require_gpu is true and allow_cpu_aer_fallback is false")
    return device


def _summary_aer_settings(settings: dict[str, object]) -> dict[str, object]:
    return {
        "method": str(settings.get("method", "")),
        "device": str(settings.get("device", "")),
        "method_gpu_supported": bool(settings.get("method_gpu_supported", False)),
        "requested_gpu_method_supported": bool(settings.get("requested_gpu_method_supported", False)),
        "gpu_support_note": str(settings.get("gpu_support_note", "")),
        "selection_reason": str(settings.get("selection_reason", "")),
        "requested_method": str(settings.get("requested_method", "")),
        "num_qubits": int(settings.get("num_qubits", 0) or 0),
        "tensor_network_threshold": int(settings.get("tensor_network_threshold", 0) or 0),
        "options": dict(settings.get("options", {})) if isinstance(settings.get("options", {}), dict) else {},
    }


def _format_aer_settings(value: object) -> str:
    if not isinstance(value, dict):
        return "unavailable"
    method = str(value.get("method", ""))
    device = str(value.get("device", ""))
    reason = str(value.get("selection_reason", ""))
    gpu_note = str(value.get("gpu_support_note", ""))
    n = value.get("num_qubits", "")
    threshold = value.get("tensor_network_threshold", "")
    parts = [f"method={method}", f"device={device}"]
    if n != "":
        parts.append(f"n={n}")
    if threshold != "":
        parts.append(f"threshold={threshold}")
    if reason:
        parts.append(f"reason={reason}")
    if gpu_note:
        parts.append(f"gpu={gpu_note}")
    return ", ".join(parts)


def _aer_method_gpu_supported(method: str) -> bool:
    return _normalize_aer_method(str(method)) in AER_GPU_SUPPORTED_METHODS


def _aer_gpu_support_note(method: str, device: str) -> str:
    normalized = _normalize_aer_method(str(method))
    if str(device).upper() != "GPU":
        return "gpu_not_requested"
    if _aer_method_gpu_supported(normalized):
        return "aer_method_supports_gpu"
    return f"aer_method_{normalized}_does_not_support_gpu"


def _resolve_sampling_mode(config: dict[str, object]) -> str:
    mode = str(config.get("aer_sampling_mode", "batch")).strip().lower().replace("-", "_")
    aliases = {
        "batch": "batch",
        "batched": "batch",
        "multi_circuit": "batch",
        "multi": "batch",
        "per_circuit": "per_circuit",
        "single": "per_circuit",
        "legacy": "per_circuit",
    }
    if mode not in aliases:
        raise ValueError("aer_sampling_mode must be 'batch' or 'per_circuit'")
    return aliases[mode]


def _resolve_sampling_job_batch_size(config: dict[str, object], *, num_circuits: int, sampling_mode: str) -> int:
    if sampling_mode == "per_circuit":
        return 1
    raw = int(config.get("aer_sampling_job_batch_size", 0) or 0)
    if raw <= 0:
        return max(1, int(num_circuits))
    return max(1, raw)


def _apply_sampling_aer_option_defaults(
    aer_settings: dict[str, object],
    *,
    config: dict[str, object],
    sampling_mode: str,
    job_batch_size: int,
) -> dict[str, object]:
    resolved = dict(aer_settings)
    options = dict(resolved.get("options", {})) if isinstance(resolved.get("options", {}), dict) else {}
    defaults: dict[str, object] = {}
    if (
        bool(config.get("aer_auto_parallel_experiments", True))
        and sampling_mode == "batch"
        and int(job_batch_size) > 1
        and str(resolved.get("device", "")).upper() == "GPU"
        and "max_parallel_experiments" not in options
    ):
        cap = max(1, int(config.get("aer_max_parallel_experiments_auto_cap", 8) or 8))
        defaults["max_parallel_experiments"] = min(int(job_batch_size), cap)
        options["max_parallel_experiments"] = defaults["max_parallel_experiments"]
    resolved["options"] = options
    resolved["sampling_option_defaults"] = defaults
    return resolved


def _sampling_batches(circuits: list[object], *, batch_size: int, mode: str) -> Iterable[tuple[int, list[object]]]:
    if mode == "per_circuit":
        for idx, circuit in enumerate(circuits):
            yield idx, [circuit]
        return
    for start in range(0, len(circuits), max(1, int(batch_size))):
        yield start, circuits[start : start + max(1, int(batch_size))]


def _counts_from_aer_result(result, *, num_circuits: int, batched: bool) -> list[dict[str, int]]:
    if not batched:
        return [dict(result.get_counts())]
    counts_by_circuit = []
    for idx in range(int(num_circuits)):
        counts_by_circuit.append(dict(result.get_counts(idx)))
    return counts_by_circuit


def _sampling_audit(
    *,
    config: dict[str, object],
    aer_settings: dict[str, object],
    sampling_mode: str,
    job_batch_size: int,
    num_jobs: int,
    num_circuits: int,
    shots: int,
    unique_outcome_counts: list[int],
    sampling_seconds: float,
    materialization_seconds: float,
    total_seconds: float,
) -> dict[str, object]:
    counts = np.asarray(unique_outcome_counts, dtype=np.float64) if unique_outcome_counts else np.asarray([], dtype=np.float64)
    return {
        "schema": "scope_static_s2d_phys1_sampling_audit_v1",
        "stage": "S2D_PHYS1_teacher",
        "backend": str(config.get("backend", "qiskit_aer_gpu")),
        "aer_method": str(aer_settings.get("method", "")),
        "aer_device": str(aer_settings.get("device", "")),
        "aer_method_gpu_supported": bool(aer_settings.get("method_gpu_supported", False)),
        "aer_requested_gpu_method_supported": bool(aer_settings.get("requested_gpu_method_supported", False)),
        "aer_gpu_support_note": str(aer_settings.get("gpu_support_note", "")),
        "aer_options": dict(aer_settings.get("options", {})) if isinstance(aer_settings.get("options", {}), dict) else {},
        "aer_sampling_option_defaults": dict(aer_settings.get("sampling_option_defaults", {}))
        if isinstance(aer_settings.get("sampling_option_defaults", {}), dict)
        else {},
        "requested_mode": str(config.get("aer_sampling_mode", "batch")),
        "mode": sampling_mode,
        "job_batch_size": int(job_batch_size),
        "num_jobs": int(num_jobs),
        "num_circuits": int(num_circuits),
        "shots_per_circuit": int(shots),
        "total_requested_shots": int(shots) * int(num_circuits),
        "seed": int(config.get("seed", 0)),
        "seed_policy": "one_seed_per_aer_job" if sampling_mode == "batch" else "seed_plus_circuit_index",
        "counts_unique_outcomes": {
            "min": int(counts.min()) if counts.size else 0,
            "max": int(counts.max()) if counts.size else 0,
            "mean": float(counts.mean()) if counts.size else 0.0,
        },
        "sampling_wall_clock_seconds": float(sampling_seconds),
        "materialization_wall_clock_seconds": float(materialization_seconds),
        "total_wall_clock_seconds": float(total_seconds),
        "count_materialization": "grouped_counts_np_repeat",
        "metrics_are_wall_clock": True,
    }


def _merge_sampling_audits(audits: list[dict[str, object]], *, config: dict[str, object]) -> dict[str, object]:
    if not audits:
        return _sampling_audit(
            config=config,
            aer_settings=resolve_aer_simulator_settings(config),
            sampling_mode=_resolve_sampling_mode(config),
            job_batch_size=0,
            num_jobs=0,
            num_circuits=0,
            shots=int(config.get("shots", 10_000)),
            unique_outcome_counts=[],
            sampling_seconds=0.0,
            materialization_seconds=0.0,
            total_seconds=0.0,
        )
    first = dict(audits[0])
    min_values = []
    max_values = []
    weighted_unique_total = 0.0
    weighted_unique_count = 0
    for audit in audits:
        stats = audit.get("counts_unique_outcomes", {})
        if not isinstance(stats, dict):
            continue
        min_values.append(int(stats.get("min", 0)))
        max_values.append(int(stats.get("max", 0)))
        num = int(audit.get("num_circuits", 0) or 0)
        weighted_unique_total += float(stats.get("mean", 0.0)) * num
        weighted_unique_count += num
    first.update(
        {
            "mode": "balanced_multicircuit_merged",
            "requested_mode": str(config.get("aer_sampling_mode", first.get("requested_mode", "batch"))),
            "num_jobs": int(sum(int(audit.get("num_jobs", 0) or 0) for audit in audits)),
            "num_circuits": int(sum(int(audit.get("num_circuits", 0) or 0) for audit in audits)),
            "total_requested_shots": int(sum(int(audit.get("total_requested_shots", 0) or 0) for audit in audits)),
            "sampling_wall_clock_seconds": float(sum(float(audit.get("sampling_wall_clock_seconds", 0.0) or 0.0) for audit in audits)),
            "materialization_wall_clock_seconds": float(sum(float(audit.get("materialization_wall_clock_seconds", 0.0) or 0.0) for audit in audits)),
            "total_wall_clock_seconds": float(sum(float(audit.get("total_wall_clock_seconds", 0.0) or 0.0) for audit in audits)),
            "counts_unique_outcomes": {
                "min": min(min_values) if min_values else 0,
                "max": max(max_values) if max_values else 0,
                "mean": weighted_unique_total / weighted_unique_count if weighted_unique_count else 0.0,
            },
            "balanced_sampling_batches": len(audits),
            "metrics_are_wall_clock": True,
        }
    )
    return first


def _counts_to_bit_matrix(counts: dict[str, int], *, shots: int, num_bits: int) -> np.ndarray:
    num_bits = int(num_bits)
    keys = []
    repeat_counts = []
    total = 0
    for key, count in sorted(counts.items()):
        c = int(count)
        keys.append(key)
        repeat_counts.append(c)
        total += c
    if total != int(shots):
        raise ValueError(f"counts contain {total} shots, expected {shots}")
    if not keys:
        return np.zeros((0, num_bits), dtype=np.uint8)
    unique_rows = np.zeros((len(keys), num_bits), dtype=np.uint8)
    for idx, key in enumerate(keys):
        unique_rows[idx] = _count_key_to_bit_row(key, num_bits=num_bits)
    return np.repeat(unique_rows, np.asarray(repeat_counts, dtype=np.int64), axis=0)


def _count_key_to_bit_row(key: object, *, num_bits: int) -> np.ndarray:
    text = str(key).replace(" ", "")
    row = np.zeros(int(num_bits), dtype=np.uint8)
    if text.startswith(("0x", "0X")):
        value = int(text, 16)
        for idx in range(int(num_bits)):
            row[idx] = (value >> idx) & 1
        return row
    for idx, char in enumerate(reversed(text[-int(num_bits) :])):
        row[idx] = 1 if char == "1" else 0
    return row


def _merged_config(config: dict[str, object] | None) -> dict[str, object]:
    base = default_teacher_config()
    if config and config.get("profile"):
        base.update(_profile_defaults(str(config["profile"])))
    if not config:
        return base
    result = dict(base)
    for key, value in config.items():
        if key == "mechanisms" and isinstance(value, dict):
            merged = dict(result["mechanisms"])  # type: ignore[arg-type]
            for mech, params in value.items():
                merged[str(mech)] = {**dict(merged.get(str(mech), {})), **dict(params)}  # type: ignore[arg-type]
            result[key] = merged
        elif key == "aer_simulator_options" and isinstance(value, dict):
            result[key] = {**dict(result.get(key, {})), **dict(value)}
        else:
            result[key] = value
    if "circuit_depth" not in config:
        if "depth" in config:
            result["circuit_depth"] = config["depth"]
        elif "num_layers" in config:
            result["circuit_depth"] = config["num_layers"]
    return result


def _probe_names(probe_set: str) -> list[str]:
    if probe_set == "base":
        return ["z_basis", "x_measure", "y_measure"]
    if probe_set == "rzz_active_minimal":
        return ["z_basis", "x_measure", "y_measure", *MIXED_BASIS_ACTIVE_PROBES]
    if probe_set == "rzz_depth_sweep":
        return ["z_basis", "x_measure", "y_measure", *RZZ_DEPTH_SWEEP_PROBES]
    if probe_set == "rzz_echo_no_echo":
        return ["z_basis", "x_measure", "y_measure", *RZZ_ECHO_CONTRAST_PROBES]
    if probe_set == "rzz_minimal_intervention":
        return ["z_basis", "x_measure", "y_measure", *RZZ_MINIMAL_INTERVENTION_PROBES]
    if probe_set == "rzz_local_tomography":
        return list(RZZ_LOCAL_TOMOGRAPHY_PROBES)
    if probe_set == "basis":
        return ["z_basis", "x_basis", "y_basis", "x_measure", "y_measure"]
    if probe_set == "full":
        return ["z_basis", "x_basis", "y_basis", "x_measure", "y_measure", "alternating_x", "echo"]
    if probe_set == "echo":
        return ["z_basis", "echo"]
    if probe_set == "base_idle_echo":
        return ["z_basis", "x_measure", "y_measure", "idle", "echo"]
    return [probe_set]


def _mechanism_record(location_id: int, spec: MechanismSpec) -> dict[str, object]:
    return {
        "location_id": int(location_id),
        **spec.audit_dict(),
        "oracle_label": spec.mechanism_id,
        "oracle_label_evaluator_only": True,
    }


def _mechanism_counts(records: Iterable[dict[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        label = str(record["oracle_label"])
        counts[label] = counts.get(label, 0) + 1
    return counts


def _profile_defaults(profile: str) -> dict[str, object]:
    profiles = {
        "phys5_chain": {"num_qubits": 5, "probe_set": "base"},
        "phys7_chain": {"num_qubits": 7, "probe_set": "base"},
        "phys9_chain": {"num_qubits": 9, "probe_set": "base"},
        "phys15_chain": {"num_qubits": 15, "probe_set": "base_idle_echo"},
        "phys20_chain": {"num_qubits": 20, "probe_set": "base_idle_echo"},
        "phys9_setB_balanced": {
            "num_qubits": 9,
            "probe_set": "base",
            "mechanism_set": "set_B",
            "balanced_min_instances_per_mechanism": 3,
            "multicircuit_teacher_batch": True,
        },
        "phys9_setC_balanced": {
            "num_qubits": 9,
            "probe_set": "base",
            "mechanism_set": "set_C",
            "balanced_min_instances_per_mechanism": 3,
            "multicircuit_teacher_batch": True,
        },
        "phys9_multicircuit_setB_balanced": {
            "num_qubits": 9,
            "probe_set": "base",
            "mechanism_set": "set_B",
            "balanced_min_instances_per_mechanism": 3,
            "multicircuit_teacher_batch": True,
        },
        "phys9_multicircuit_setC_balanced": {
            "num_qubits": 9,
            "probe_set": "base",
            "mechanism_set": "set_C",
            "balanced_min_instances_per_mechanism": 3,
            "multicircuit_teacher_batch": True,
        },
        "phys9_multicircuit_setD_balanced": {
            "num_qubits": 9,
            "probe_set": "base",
            "mechanism_set": "set_D",
            "balanced_min_instances_per_mechanism": 3,
            "multicircuit_teacher_batch": True,
        },
        "phys9_multicircuit_allM_balanced": {
            "num_qubits": 9,
            "probe_set": "base",
            "mechanism_set": [f"M{idx}" for idx in range(20)],
            "balanced_min_instances_per_mechanism": 3,
            "multicircuit_teacher_batch": True,
        },
        "phys15_multicircuit_allM_balanced": {
            "num_qubits": 15,
            "probe_set": "base_idle_echo",
            "mechanism_set": [f"M{idx}" for idx in range(20)],
            "balanced_min_instances_per_mechanism": 3,
            "multicircuit_teacher_batch": True,
        },
        "phys9_multicircuit_setB_balanced_rzz_active": {
            "num_qubits": 9,
            "probe_set": "rzz_active_minimal",
            "mechanism_set": "set_B",
            "balanced_min_instances_per_mechanism": 3,
            "multicircuit_teacher_batch": True,
        },
        "phys9_multicircuit_setC_balanced_rzz_active": {
            "num_qubits": 9,
            "probe_set": "rzz_active_minimal",
            "mechanism_set": "set_C",
            "balanced_min_instances_per_mechanism": 3,
            "multicircuit_teacher_batch": True,
        },
    }
    if profile not in profiles:
        raise ValueError(f"unknown S2D physical circuit profile {profile!r}")
    return {"profile": profile, **profiles[profile]}


def _enabled_mechanism_ids(config: dict[str, object]) -> set[str]:
    named_sets = {
        "set_A": {"M0", "M1", "M2", "M3", "M4", "M13", "M14", "M15", "M16"},
        "set_B": {"M0", "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M13", "M14", "M15", "M16"},
        "set_C": {"M0", "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9", "M13", "M14", "M15", "M16"},
        "set_D": {f"M{idx}" for idx in range(19)},
        "allM": {f"M{idx}" for idx in range(20)},
    }
    raw = config.get("mechanism_set", "set_A")
    if isinstance(raw, str):
        if raw not in named_sets:
            raise ValueError(f"unknown S2D mechanism set {raw!r}")
        enabled = set(named_sets[raw])
    elif isinstance(raw, list):
        enabled = {str(item) for item in raw}
    else:
        raise ValueError("mechanism_set must be a named set or list of mechanism ids")
    if bool(config.get("include_m6", False)):
        enabled.add("M5")
    if not bool(config.get("include_m5", True)):
        enabled.difference_update(READOUT_MECHANISM_IDS)
    return enabled


def _mechanism_set_contains(config: dict[str, object], mechanism_id: str) -> bool:
    return str(mechanism_id) in _enabled_mechanism_ids(config)


def _balanced_profile_enabled(config: dict[str, object]) -> bool:
    return bool(config.get("multicircuit_teacher_batch")) or int(config.get("balanced_min_instances_per_mechanism", 0) or 0) > 0


def _balanced_repetitions(config: dict[str, object]) -> int:
    return max(1, int(config.get("balanced_min_instances_per_mechanism", 3)))


def _circuit_depth(config: dict[str, object]) -> int:
    for key in ("circuit_depth", "depth", "num_layers"):
        if key in config:
            return max(1, int(config.get(key, 1) or 1))
    return 1


def _build_balanced_oracle_mechanisms(config: dict[str, object]) -> list[MechanismSpec]:
    specs: list[MechanismSpec] = []
    probe_count = len(_probe_names(str(config.get("probe_set", "base"))))
    for circuit_id in range(_balanced_repetitions(config)):
        batch_cfg = dict(config)
        batch_cfg["balanced_batch_index"] = circuit_id
        probe_indices = tuple(range(circuit_id * probe_count, (circuit_id + 1) * probe_count))
        for spec in _build_balanced_oracle_mechanism_batch(batch_cfg, circuit_id=circuit_id):
            specs.append(
                MechanismSpec(
                    spec.mechanism_id,
                    spec.name,
                    spec.num_qubits,
                    dict(spec.parameters),
                    instruction=spec.instruction,
                    qubits=spec.qubits,
                    circuit_id=circuit_id,
                    probe_indices=probe_indices,
                )
            )
    return sorted(specs, key=lambda spec: (spec.circuit_id, _mechanism_sort_key(spec.mechanism_id), spec.qubits))


def _build_balanced_oracle_mechanism_batch(config: dict[str, object], *, circuit_id: int) -> list[MechanismSpec]:
    params = dict(config.get("mechanisms", {}))
    n = int(config.get("num_qubits", 9))
    enabled = _enabled_mechanism_ids({**config, "balanced_min_instances_per_mechanism": 0, "multicircuit_teacher_batch": False})
    offset = int(circuit_id) % max(1, n)
    pair_offset = int(circuit_id) % max(1, n - 1)
    specs: list[MechanismSpec] = []
    single_plan = {
        "M0": ("stochastic_pauli_gate_error", "id", 0),
        "M2": ("coherent_rx_overrotation", "rx", 2),
        "M3": ("coherent_rz_overrotation", "rz", 1),
        "M4": ("amplitude_damping_gate_error", "id", 3),
        "M5": ("hard_non_pauli_kraus_gate_error", "id", 4),
        "M8": ("spectator_crosstalk_rz_or_zz", "id", 5),
        "M10": ("drifted_coherent_overrotation", "rx", 7),
        "M11": ("idle_dephasing_or_relaxation_error", "id", 6),
        "M12": ("operation_dependent_error", "rx", 8),
        "M17": ("reset_to_1_bias", "reset", 6),
        "M18": ("prep_axis_or_reset_asymmetry_bias", "reset", 8),
        "M19": ("weak_type4_ptm_mixing", "id", 8),
    }
    for mech, (name, instruction, target) in single_plan.items():
        if mech not in enabled:
            continue
        local_params = dict(params.get(mech, {}))
        if mech == "M10":
            epsilons = _drift_epsilons(local_params, _balanced_repetitions(config))
            local_params["epsilon"] = epsilons[int(circuit_id) % len(epsilons)]
            instruction = "rz" if str(local_params.get("axis", "rx")).lower() == "rz" else "rx"
        specs.append(
            MechanismSpec(
                mech,
                name,
                1,
                local_params,
                instruction=instruction,
                qubits=((int(target) + offset) % n,),
                circuit_id=circuit_id,
            )
        )

    pair_plan = [
        ("M1", "coherent_rzz_overrotation", 0),
        ("M6", "two_qubit_depolarizing_after_rzz", 1),
        ("M7", "coherent_rxx_ryy_perturbation", 2),
        ("M9", "correlated_two_qubit_relaxation", 3),
    ]
    for mech, name, base_left in pair_plan:
        if mech not in enabled:
            continue
        left = (int(base_left) + pair_offset) % max(1, n - 1)
        specs.append(
            MechanismSpec(
                mech,
                name,
                2,
                dict(params.get(mech, {})),
                instruction="rzz",
                qubits=(left, left + 1),
                circuit_id=circuit_id,
            )
        )

    for readout_idx, (mech, name) in enumerate((
        ("M13", "readout_0_to_1_bias"),
        ("M14", "readout_1_to_0_bias"),
        ("M15", "readout_symmetric_assignment_noise"),
        ("M16", "measurement_context_bias"),
    )):
        if mech in enabled:
            q = (readout_idx + offset) % n
            specs.append(MechanismSpec(mech, name, 1, dict(params.get(mech, {})), instruction="measure", qubits=(q,), circuit_id=circuit_id))
    return sorted(specs, key=lambda spec: (_mechanism_sort_key(spec.mechanism_id), spec.qubits))


def _single_targets(num_qubits: int) -> dict[str, int]:
    n = int(num_qubits)
    requested = {
        "M0": 0,
        "M3": 1,
        "M2": 2,
        "M4": 3,
        "M5": 4,
        "M8": 5,
        "M11": 6,
        "M10": 7,
        "M12": 8,
        "M17": 6,
        "M18": 8,
        "M19": 8,
    }
    return {key: min(max(0, value), n - 1) for key, value in requested.items()}


def _drift_targets(num_qubits: int) -> list[int]:
    preferred = [4, 7, 10, 13]
    targets = [q for q in preferred if q < int(num_qubits)]
    if targets:
        return targets
    return [max(0, int(num_qubits) - 1)]


def _drift_epsilons(parameters: dict[str, object], count: int) -> list[float]:
    if "epsilon" in parameters:
        center = float(parameters["epsilon"])
        span = float(parameters.get("epsilon_span", 0.0))
    else:
        center = float(parameters.get("epsilon_mean", 0.032))
        span = float(parameters.get("epsilon_span", 0.018))
    if int(count) <= 1 or abs(span) <= NUMERICAL_ZERO:
        return [center for _ in range(max(1, int(count)))]
    offsets = np.linspace(-0.5 * span, 0.5 * span, int(count))
    return [float(center + offset) for offset in offsets]


def _pair_mechanism_plan(num_qubits: int, enabled: set[str]) -> list[tuple[str, int]]:
    pair_mechanisms = [mech for mech in RZZ_FAMILY_IDS if mech in enabled]
    if not pair_mechanisms:
        return []
    num_pairs = max(1, int(num_qubits) - 1)
    plan: list[tuple[str, int]] = []
    for idx, mech in enumerate(pair_mechanisms):
        plan.append((mech, idx % num_pairs))
    for pair in range(len(pair_mechanisms), num_pairs):
        plan.append(("M1" if "M1" in enabled else pair_mechanisms[pair % len(pair_mechanisms)], pair))
    seen: set[int] = set()
    out: list[tuple[str, int]] = []
    for mech, left in plan:
        if left in seen:
            continue
        seen.add(left)
        out.append((mech, left))
    return out


def _profile_rx_qubits(num_qubits: int) -> list[int]:
    targets = [2, 7]
    return [q for q in targets if q < int(num_qubits)]


def _profile_rz_qubits(num_qubits: int) -> list[int]:
    targets = [1, 5, 8]
    return [q for q in targets if q < int(num_qubits)]


def _mechanism_sort_key(mechanism_id: str) -> int:
    try:
        return int(str(mechanism_id).lstrip("M"))
    except ValueError:
        return 10_000


def _aer_simulator_options(config: dict[str, object]) -> dict[str, object]:
    raw = config.get("aer_simulator_options", {})
    if not isinstance(raw, dict):
        return {}
    allowed = {
        "max_parallel_threads",
        "max_parallel_experiments",
        "max_parallel_shots",
        "num_threads_per_device",
        "batched_shots_gpu",
        "batched_shots_gpu_max_qubits",
        "cuStateVec_enable",
        "matrix_product_state_max_bond_dimension",
        "matrix_product_state_truncation_threshold",
        "mps_lapack",
        "mps_log_data",
        "mps_omp_threads",
        "mps_parallel_threshold",
        "mps_sample_measure_algorithm",
        "mps_swap_direction",
        "shot_branching_enable",
        "shot_branching_sampling_enable",
        "tensor_network_num_sampling_qubits",
    }
    return {str(key): value for key, value in raw.items() if str(key) in allowed}


def _warning_records(caught: list[warnings.WarningMessage]) -> list[dict[str, str]]:
    return [{"category": item.category.__name__, "message": str(item.message)} for item in caught]


def _dedupe_warning_records(records: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    seen = set()
    for record in records:
        key = (record.get("category", ""), record.get("message", ""))
        if key in seen:
            continue
        seen.add(key)
        out.append({"category": key[0], "message": key[1]})
    return out


def _merged_warning_strings(*sources: object) -> list[str]:
    out: list[str] = []
    seen = set()
    for source in sources:
        if not isinstance(source, list):
            continue
        for item in source:
            if isinstance(item, dict):
                text = f"{item.get('category')}: {item.get('message')}"
            else:
                text = str(item)
            if text and text not in seen:
                seen.add(text)
                out.append(text)
    return out
