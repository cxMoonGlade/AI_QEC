from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Iterable

import numpy as np

from ..numerics import NUMERICAL_ZERO
from .channels import MechanismSpec
from .preflight import audit_cudaq_backend, write_backend_audit


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


class ProbeCircuit:
    """Lightweight visible probe schedule used after retiring simulator-specific circuits."""

    def __init__(self, num_qubits: int, num_clbits: int, *, name: str) -> None:
        self.num_qubits = int(num_qubits)
        self.num_clbits = int(num_clbits)
        self.name = str(name)
        self._ops: dict[str, int] = {}

    def count_ops(self) -> dict[str, int]:
        return dict(self._ops)

    def _add(self, name: str, count: int = 1) -> None:
        self._ops[str(name)] = self._ops.get(str(name), 0) + int(count)

    def h(self, _qubit: int) -> None:
        self._add("h")

    def s(self, _qubit: int) -> None:
        self._add("s")

    def sdg(self, _qubit: int) -> None:
        self._add("sdg")

    def x(self, _qubit: int) -> None:
        self._add("x")

    def y(self, _qubit: int) -> None:
        self._add("y")

    def id(self, _qubit: int) -> None:
        self._add("id")

    def reset(self, _qubit: int) -> None:
        self._add("reset")

    def rx(self, _angle: float, _qubit: int) -> None:
        self._add("rx")

    def rz(self, _angle: float, _qubit: int) -> None:
        self._add("rz")

    def rzz(self, _angle: float, _left: int, _right: int) -> None:
        self._add("rzz")

    def measure(self, qubits, _clbits) -> None:
        try:
            count = len(list(qubits))
        except TypeError:
            count = 1
        self._add("measure", count)


def default_teacher_config() -> dict[str, object]:
    return {
        "backend": "cudaq",
        "require_gpu": True,
        "cudaq_target": "nvidia",
        "cudaq_target_options": "fp32",
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
        "local_observable_response_model": "born_local",
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
    audit = audit_cudaq_backend(
        backend=str(cfg.get("backend", "cudaq")),
        require_gpu=bool(cfg.get("require_gpu", True)),
        cudaq_target=str(cfg.get("cudaq_target", "nvidia")),
        cudaq_target_options=str(cfg.get("cudaq_target_options", "fp32")),
    )
    write_backend_audit(audit, preflight_dir)
    if not bool(audit.get("backend_usable")):
        raise RuntimeError("S2D_PHYS1_teacher requires a passing S2D_PHYS0_preflight backend audit")
    from .local_observable_teacher import generate_local_observable_teacher_dataset

    cfg["backend"] = "cudaq"
    cfg.setdefault("local_observable_response_model", "born_local")
    summary = generate_local_observable_teacher_dataset(cfg, output_dir=output_dir)
    summary["backend_audit_dir"] = str(preflight_dir)
    summary["cudaq_backend"] = {
        "target": audit.get("cudaq_target"),
        "gpu_count": audit.get("cudaq_gpu_count"),
        "tiny_cudaq_sample": audit.get("tiny_cudaq_sample"),
    }
    return summary


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
    cfg = _merged_config(config)
    n = int(cfg.get("num_qubits", 5))
    theta = float(cfg.get("theta", 0.18))
    circuit_depth = _circuit_depth(cfg)
    probe_names = _probe_names(str(cfg.get("probe_set", "base")))
    circuits = []
    for probe in probe_names:
        qc = ProbeCircuit(n, n, name=str(probe))
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
                "mechanism_application_kind": "readout_confusion" if spec.mechanism_id in READOUT_MECHANISM_IDS else "local_channel",
                "applies_to_all_qubits": False,
                "parameters": {str(key): value for key, value in spec.audit_dict()["parameters"].items()},
                "oracle_label_evaluator_only": True,
            }
        )
    return {
        "schema": "scope_static_s2d_noise_application_audit_v1",
        "stage": "S2D_PHYS1_teacher",
        "backend": str(config.get("backend", "cudaq")),
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


def _is_clifford_angle(angle: float, *, atol: float = 1e-9) -> bool:
    """Return true for rotations equivalent to integer multiples of pi/2."""

    import math

    scaled = float(angle) / (math.pi / 2.0)
    return abs(scaled - round(scaled)) <= float(atol)


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
