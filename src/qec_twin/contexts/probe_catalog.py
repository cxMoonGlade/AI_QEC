from __future__ import annotations

import json
import math
import time
from typing import Iterable

import numpy as np

from qec_twin.numerics import NUMERICAL_ZERO
from qec_twin.forward.channels import (
    M13_DEFAULT_DRIFT_VISIBILITY_SCALE,
    MechanismSpec,
    canonical_single_qubit_axis,
    mechanism_error_axis,
    mechanism_operation_axis,
)
from qec_twin.mechanisms.catalog import (
    IMPLEMENTED_MECHANISM_IDS,
    LEGACY_TO_CURRENT_MECHANISM_IDS,
    MECHANISM_NAMES,
    NAMED_MECHANISM_SETS,
    PREP_RESET_MECHANISM_IDS,
    READOUT_MECHANISM_IDS,
    RZZ_FAMILY_IDS,
)
from qec_twin.contexts.probe_contract import (
    EDGE_ORIENTATION_RULE,
    MIXED_BASIS_ACTIVE_PROBES,
    PHYC1_LEGACY_STAGE_NAME,
    RZZ_DEPTH_SWEEP_DEPTHS,
    RZZ_DEPTH_SWEEP_PROBES,
    RZZ_ECHO_CONTRAST_PROBES,
    RZZ_LOCAL_TOMOGRAPHY_PROBES,
    RZZ_MINIMAL_INTERVENTION_PROBES,
    RZZ_TOMO_EDGE_PARITIES,
    RZZ_TOMO_MEAS_AXES,
    RZZ_TOMO_PREP_STATES,
    circuit_depth,
    count_key_to_bit_row,
    counts_to_bit_matrix,
    mechanism_counts,
    probe_names,
)


GATE_MECHANISM_IDS = set(IMPLEMENTED_MECHANISM_IDS).difference(set(READOUT_MECHANISM_IDS) | set(PREP_RESET_MECHANISM_IDS))
OTHER_MECHANISM_IDS = {"M19", "M24"}


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

    def ry(self, _angle: float, _qubit: int) -> None:
        self._add("ry")

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
            "M1": {"p": 0.025},
            "M2": {"p": 0.011},
            "M3": {"p": 0.018},
            "M4": {"gamma": 0.018},
            "M5": {"p_z": 0.0025},
            "M6": {"epsilon": 0.035},
            "M7": {"epsilon": 0.04},
            "M8": {"epsilon": 0.045},
            "M9": {"p": 0.006},
            "M10": {"epsilon_x": 0.024, "epsilon_y": 0.017},
            "M11": {"epsilon": 0.025},
            "M12": {"gamma": 0.012},
            "M13": {
                "operation_axis": "rx",
                "epsilon_mean": 0.032,
                "epsilon_span": 0.018,
                "drift_visibility_scale": M13_DEFAULT_DRIFT_VISIBILITY_SCALE,
            },
            "M14": {"operation_axis": "rx", "error_axis": "rz", "epsilon": 0.028},
            "M15": {"eta": 0.02},
            "M16": {"p": 0.02},
            "M17": {"p": 0.018},
            "M18": {"epsilon": 0.025},
            "M19": {"eta": 0.006},
            "M20": {"epsilon": 0.03},
            "M21": {"epsilon": 0.035},
            "M22": {"epsilon": 0.022},
            "M23": {"epsilon": 0.019},
            "M24": {"gamma_up": 0.006},
            "M25": {"p": 0.006},
            "M26": {"p": 0.006},
            "M27": {"epsilon": 0.026},
            "M28": {"epsilon": 0.015},
            "M29": {"epsilon": 0.018},
            "M30": {"epsilon": 0.016},
            "M31": {"epsilon": 0.017},
            "M32": {"epsilon": 0.014},
            "M33": {"epsilon": 0.013},
            "M34": {"p": 0.004},
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
        specs.append(MechanismSpec("M0", MECHANISM_NAMES["M0"], 1, dict(params.get("M0", {})), instruction="id", qubits=(single_targets["M0"],)))
    if "M4" in enabled:
        specs.append(MechanismSpec("M4", MECHANISM_NAMES["M4"], 1, dict(params.get("M4", {})), instruction="id", qubits=(single_targets["M4"],)))
    if "M5" in enabled:
        specs.append(MechanismSpec("M5", MECHANISM_NAMES["M5"], 1, dict(params.get("M5", {})), instruction="id", qubits=(single_targets["M5"],)))
    if "M6" in enabled:
        specs.append(MechanismSpec("M6", MECHANISM_NAMES["M6"], 1, dict(params.get("M6", {})), instruction="rx", qubits=(single_targets["M6"],)))
    if "M7" in enabled:
        specs.append(MechanismSpec("M7", MECHANISM_NAMES["M7"], 1, dict(params.get("M7", {})), instruction="rz", qubits=(single_targets["M7"],)))
    if "M11" in enabled:
        m11_target = single_targets["M11"]
        specs.append(
            MechanismSpec(
                "M11",
                MECHANISM_NAMES["M11"],
                1,
                _m11_spectator_overlay_parameters(dict(params.get("M11", {})), circuit_id=0, target=m11_target, num_qubits=n),
                instruction="id",
                qubits=(m11_target,),
            )
        )
    if "M13" in enabled:
        drift = dict(params.get("M13", {}))
        instruction = _operation_instruction_from_params(drift, default="rx")
        for drift_idx, (target, epsilon) in enumerate(zip(_drift_targets(n), _drift_epsilons(drift, len(_drift_targets(n))))):
            local_drift = dict(drift)
            local_drift["epsilon"] = float(epsilon)
            local_drift["drift_index"] = int(drift_idx)
            specs.append(
                MechanismSpec(
                    "M13",
                    MECHANISM_NAMES["M13"],
                    1,
                    local_drift,
                    instruction=instruction,
                    qubits=(target,),
                )
            )
    if "M14" in enabled:
        m14_params = dict(params.get("M14", {}))
        specs.append(
            MechanismSpec(
                "M14",
                MECHANISM_NAMES["M14"],
                1,
                m14_params,
                instruction=_operation_instruction_from_params(m14_params, default="rx"),
                qubits=(single_targets["M14"],),
            )
        )
    if "M15" in enabled:
        specs.append(MechanismSpec("M15", MECHANISM_NAMES["M15"], 1, dict(params.get("M15", {})), instruction="id", qubits=(single_targets["M15"],)))
    if "M17" in enabled:
        specs.append(MechanismSpec("M17", MECHANISM_NAMES["M17"], 1, dict(params.get("M17", {})), instruction="reset", qubits=(single_targets["M17"],)))
    if "M18" in enabled:
        specs.append(MechanismSpec("M18", MECHANISM_NAMES["M18"], 1, dict(params.get("M18", {})), instruction="reset", qubits=(single_targets["M18"],)))
    if "M19" in enabled:
        specs.append(MechanismSpec("M19", MECHANISM_NAMES["M19"], 1, dict(params.get("M19", {})), instruction="id", qubits=(single_targets["M19"],)))
    if "M20" in enabled:
        specs.append(MechanismSpec("M20", MECHANISM_NAMES["M20"], 1, dict(params.get("M20", {})), instruction="ry", qubits=(single_targets["M20"],)))
    if "M24" in enabled:
        specs.append(MechanismSpec("M24", MECHANISM_NAMES["M24"], 1, dict(params.get("M24", {})), instruction="id", qubits=(single_targets["M24"],)))
    if "M25" in enabled:
        specs.append(MechanismSpec("M25", MECHANISM_NAMES["M25"], 1, dict(params.get("M25", {})), instruction="id", qubits=(single_targets["M25"],)))
    if "M26" in enabled:
        specs.append(MechanismSpec("M26", MECHANISM_NAMES["M26"], 1, dict(params.get("M26", {})), instruction="id", qubits=(single_targets["M26"],)))
    if "M27" in enabled:
        specs.append(MechanismSpec("M27", MECHANISM_NAMES["M27"], 1, dict(params.get("M27", {})), instruction="id", qubits=(single_targets["M27"],)))
    if "M34" in enabled:
        specs.append(MechanismSpec("M34", MECHANISM_NAMES["M34"], 1, dict(params.get("M34", {})), instruction="id", qubits=(single_targets["M34"],)))

    pair_plan = _pair_mechanism_plan(n, enabled)
    for mech, left in pair_plan:
        specs.append(MechanismSpec(mech, MECHANISM_NAMES[mech], 2, dict(params.get(mech, {})), instruction="rzz", qubits=(left, left + 1)))

    for readout_idx, (mech, name) in enumerate((
        ("M1", MECHANISM_NAMES["M1"]),
        ("M2", MECHANISM_NAMES["M2"]),
        ("M3", MECHANISM_NAMES["M3"]),
        ("M16", MECHANISM_NAMES["M16"]),
    )):
        if mech in enabled:
            q = (readout_idx + int(cfg.get("balanced_batch_index", 0) or 0)) % n
            specs.append(MechanismSpec(mech, name, 1, dict(params.get(mech, {})), instruction="measure", qubits=(q,)))
    return sorted(specs, key=lambda spec: (_mechanism_sort_key(spec.mechanism_id), spec.qubits))


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
        ry_qubits = set(_profile_ry_qubits(n))
        rz_qubits = set(_profile_rz_qubits(n))
        if any(_mechanism_set_contains(cfg, mech) for mech in ("M13", "M14", "M20")):
            mechanism_params = cfg.get("mechanisms", {})
            m13_params = (
                dict(mechanism_params.get("M13", {}))
                if isinstance(mechanism_params, dict) and isinstance(mechanism_params.get("M13", {}), dict)
                else {}
            )
            if _mechanism_set_contains(cfg, "M13"):
                axis = _operation_instruction_from_params(m13_params, default="rx")
                if axis == "ry":
                    ry_qubits.update(_drift_targets(n))
                elif axis == "rz":
                    rz_qubits.update(_drift_targets(n))
                else:
                    rx_qubits.update(_drift_targets(n))
            m14_params = (
                dict(mechanism_params.get("M14", {}))
                if isinstance(mechanism_params, dict) and isinstance(mechanism_params.get("M14", {}), dict)
                else {}
            )
            if _mechanism_set_contains(cfg, "M14"):
                axis = _operation_instruction_from_params(m14_params, default="rx")
                targets = [_single_targets(n)["M14"]]
                if axis == "ry":
                    ry_qubits.update(targets)
                elif axis == "rz":
                    rz_qubits.update(targets)
                else:
                    rx_qubits.update(targets)
            if _mechanism_set_contains(cfg, "M20"):
                ry_qubits.add(_single_targets(n)["M20"])
        for _layer_idx in range(circuit_depth):
            for q in range(n):
                qc.id(q)
            for q in sorted(rx_qubits):
                qc.rx(0.13 + 0.01 * (q % 3), q)
            for q in sorted(ry_qubits):
                qc.ry(0.11 + 0.01 * (q % 3), q)
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
        "schema": "qec_twin_s2d_active_probe_manifest_v1",
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
        "schema": "qec_twin_s2d_noise_application_audit_v1",
        "stage": PHYC1_LEGACY_STAGE_NAME,
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
        if spec.mechanism_id == "M8":
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
        elif spec.mechanism_id == "M6":
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
        elif spec.mechanism_id == "M7":
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
        elif spec.mechanism_id == "M10":
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
        elif spec.mechanism_id in {"M11", "M13", "M14", "M18", "M20", "M21", "M22", "M23", "M27", "M28", "M29", "M30", "M31", "M32", "M33"}:
            angle = float(spec.parameters.get("epsilon", spec.parameters.get("epsilon_mean", 0.03)))
            gate = mechanism_error_axis(spec) if spec.mechanism_id in {"M13", "M14"} else str(spec.parameters.get("axis", "rz")).lower()
            mechanism_records.append(
                {
                    "source": "oracle_noise",
                    "mechanism_id": spec.mechanism_id,
                    "gate": gate,
                    "operation_axis": mechanism_operation_axis(spec) if spec.mechanism_id in {"M13", "M14"} else None,
                    "angle": angle,
                    "location_qubits": [int(q) for q in spec.qubits],
                    "is_clifford_angle": _is_clifford_angle(angle),
                    "reason": "drift/crosstalk coherent over-rotation",
                }
            )
        elif spec.mechanism_id in {"M4", "M5", "M9", "M12", "M15", "M19", "M24", "M25", "M26", "M34"}:
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
        "schema": "qec_twin_s2d_non_clifford_audit_v1",
        "stage": PHYC1_LEGACY_STAGE_NAME,
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
    if spec.mechanism_id in {"M6", "M7", "M13", "M14", "M18", "M20", "M21", "M22", "M23", "M27", "M28", "M29", "M30", "M31", "M32", "M33"}:
        return "coherent_unitary_quantum_error"
    if spec.mechanism_id in {"M8", "M10", "M11"}:
        return "coherent_unitary_quantum_error"
    if spec.mechanism_id == "M4":
        return "amplitude_damping_quantum_error"
    if spec.mechanism_id in READOUT_MECHANISM_IDS:
        return "readout_error"
    if spec.mechanism_id in {"M5", "M15", "M19", "M24", "M25", "M26", "M34"}:
        return "custom_kraus_quantum_error"
    if spec.mechanism_id == "M9":
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
    return counts_to_bit_matrix(counts, shots=shots, num_bits=num_bits)


def _count_key_to_bit_row(key: object, *, num_bits: int) -> np.ndarray:
    return count_key_to_bit_row(key, num_bits=num_bits)


def _merged_config(config: dict[str, object] | None) -> dict[str, object]:
    base = default_teacher_config()
    if config and config.get("profile"):
        base.update(_profile_defaults(str(config["profile"])))
    if not config:
        return base
    legacy_mechanisms = _looks_like_legacy_mechanism_parameters(config.get("mechanisms"))
    result = dict(base)
    for key, value in config.items():
        if key == "mechanisms" and isinstance(value, dict):
            merged = dict(result["mechanisms"])  # type: ignore[arg-type]
            mechanism_items = _renumber_legacy_mapping(value) if legacy_mechanisms else value
            for mech, params in mechanism_items.items():
                merged[str(mech)] = {**dict(merged.get(str(mech), {})), **dict(params)}  # type: ignore[arg-type]
            result[key] = merged
        elif key == "mechanism_instance_counts" and isinstance(value, dict) and legacy_mechanisms:
            result[key] = _renumber_legacy_mapping(value)
        elif key == "mechanism_set" and isinstance(value, list) and legacy_mechanisms:
            result[key] = [LEGACY_TO_CURRENT_MECHANISM_IDS.get(str(item), str(item)) for item in value]
        else:
            result[key] = value
    if "circuit_depth" not in config:
        if "depth" in config:
            result["circuit_depth"] = config["depth"]
        elif "num_layers" in config:
            result["circuit_depth"] = config["num_layers"]
    if result.get("mechanism_weight_profile"):
        from qec_twin.mechanisms.profiles import apply_mechanism_weight_profile

        explicit_mechanisms: dict[object, object] = {}
        if isinstance(config.get("mechanisms"), dict):
            raw_mechanisms = config["mechanisms"]  # type: ignore[index]
            explicit_mechanisms = _renumber_legacy_mapping(raw_mechanisms) if legacy_mechanisms else dict(raw_mechanisms)
        explicit_counts: dict[object, object] = {}
        if isinstance(config.get("mechanism_instance_counts"), dict):
            raw_counts = config["mechanism_instance_counts"]  # type: ignore[index]
            explicit_counts = _renumber_legacy_mapping(raw_counts) if legacy_mechanisms else dict(raw_counts)
        profile_cfg = dict(result)
        profile_cfg["mechanisms"] = explicit_mechanisms
        if explicit_counts:
            profile_cfg["mechanism_instance_counts"] = explicit_counts
        else:
            profile_cfg.pop("mechanism_instance_counts", None)
        result = apply_mechanism_weight_profile(
            profile_cfg,
            profile_name=str(result["mechanism_weight_profile"]),
        )
    return result


def _looks_like_legacy_mechanism_parameters(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    m1 = value.get("M1")
    m13 = value.get("M13")
    return isinstance(m1, dict) and "epsilon" in m1 and isinstance(m13, dict) and "p" in m13


def _renumber_legacy_mapping(value: dict[object, object]) -> dict[str, object]:
    out: dict[str, object] = {}
    for key, item in value.items():
        out[LEGACY_TO_CURRENT_MECHANISM_IDS.get(str(key), str(key))] = item
    return out


def _probe_names(probe_set: str) -> list[str]:
    return probe_names(probe_set)


def _mechanism_record(location_id: int, spec: MechanismSpec) -> dict[str, object]:
    return {
        "location_id": int(location_id),
        **spec.audit_dict(),
        "oracle_label": spec.mechanism_id,
        "oracle_label_evaluator_only": True,
    }


def _mechanism_counts(records: Iterable[dict[str, object]]) -> dict[str, int]:
    return mechanism_counts(records)


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
            "mechanism_set": list(IMPLEMENTED_MECHANISM_IDS),
            "balanced_min_instances_per_mechanism": 3,
            "multicircuit_teacher_batch": True,
        },
        "phys15_multicircuit_allM_balanced": {
            "num_qubits": 15,
            "probe_set": "base_idle_echo",
            "mechanism_set": list(IMPLEMENTED_MECHANISM_IDS),
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
    raw = config.get("mechanism_set", "set_A")
    if isinstance(raw, str):
        if raw not in NAMED_MECHANISM_SETS:
            raise ValueError(f"unknown S2D mechanism set {raw!r}")
        enabled = set(NAMED_MECHANISM_SETS[raw])
    elif isinstance(raw, list):
        enabled = {str(item) for item in raw}
    else:
        raise ValueError("mechanism_set must be a named set or list of mechanism ids")
    if bool(config.get("include_m6", False)):
        enabled.add("M15")
    if not bool(config.get("include_m5", True)):
        enabled.difference_update(READOUT_MECHANISM_IDS)
    return enabled


def _mechanism_set_contains(config: dict[str, object], mechanism_id: str) -> bool:
    return str(mechanism_id) in _enabled_mechanism_ids(config)


def _balanced_profile_enabled(config: dict[str, object]) -> bool:
    return bool(config.get("multicircuit_teacher_batch")) or int(config.get("balanced_min_instances_per_mechanism", 0) or 0) > 0


def _balanced_repetitions(config: dict[str, object]) -> int:
    return max(1, int(config.get("balanced_min_instances_per_mechanism", 3)))


BALANCED_STRENGTH_PARAMETER_NAMES = (
    "p",
    "p_x",
    "p_y",
    "p_z",
    "p0_to_1",
    "p1_to_0",
    "gamma",
    "gamma_up",
    "eta",
    "epsilon",
    "epsilon_x",
    "epsilon_y",
    "strength",
    "spectator_strength",
)


def _balanced_strength_variants_enabled(config: dict[str, object]) -> bool:
    return bool(config.get("balanced_strength_variants", False))


def _balanced_strength_variant_strategy(config: dict[str, object]) -> str:
    return str(config.get("balanced_strength_variant_strategy", "monotone")).strip().lower()


def _balanced_strength_context_correlation(*, repetitions: int, stride: int, offset: int) -> float:
    if int(repetitions) <= 2:
        return 1.0
    context_ranks = np.arange(int(repetitions), dtype=float)
    strength_ranks = np.asarray([(idx * int(stride) + int(offset)) % int(repetitions) for idx in range(int(repetitions))], dtype=float)
    return abs(float(np.corrcoef(context_ranks, strength_ranks)[0, 1]))


def _balanced_strength_decorrelated_offset(
    config: dict[str, object],
    *,
    repetitions: int,
    stride: int,
    mechanism_id: str,
    location_period: int | None = None,
    location_offset: int = 0,
) -> int:
    max_corr = float(config.get("balanced_strength_max_context_corr", 0.05))
    scored: list[tuple[float, float, float, int]] = []
    for offset in range(int(repetitions)):
        context_corr = _balanced_strength_context_correlation(repetitions=repetitions, stride=stride, offset=offset)
        location_corr = 0.0
        if location_period is not None and int(location_period) > 2:
            locations = np.asarray(
                [(int(location_offset) + idx) % int(location_period) for idx in range(int(repetitions))], dtype=float
            )
            strength_ranks = np.asarray(
                [(idx * int(stride) + int(offset)) % int(repetitions) for idx in range(int(repetitions))], dtype=float
            )
            location_corr = abs(float(np.corrcoef(locations, strength_ranks)[0, 1]))
        scored.append((max(context_corr, location_corr), context_corr, location_corr, offset))
    scored = sorted(scored, key=lambda item: (item[0], item[1], item[2], item[3]))
    eligible = [item for item in scored if item[0] <= max_corr]
    if not eligible:
        eligible = scored[:1]
    return int(eligible[_mechanism_sort_key(str(mechanism_id)) % len(eligible)][3])


def _balanced_strength_rank(
    config: dict[str, object],
    *,
    circuit_id: int,
    mechanism_id: str,
    location_period: int | None = None,
    location_offset: int = 0,
) -> int:
    repetitions = _balanced_repetitions(config)
    if repetitions <= 1:
        return 0
    base_rank = int(circuit_id) % repetitions
    strategy = _balanced_strength_variant_strategy(config)
    if strategy in {"monotone", "linear", "context_monotone"}:
        return base_rank
    if strategy in {"decorrelated_latin", "latin", "mechanism_latin_square"}:
        stride = int(config.get("balanced_strength_decorrelation_stride", 0) or 0)
        if stride <= 0:
            stride = max(1, repetitions // 2 - 1)
        while math.gcd(stride, repetitions) != 1:
            stride += 1
        offset = _balanced_strength_decorrelated_offset(
            config,
            repetitions=repetitions,
            stride=stride,
            mechanism_id=str(mechanism_id),
            location_period=location_period,
            location_offset=location_offset,
        )
        return (base_rank * stride + offset) % repetitions
    raise ValueError(
        "balanced_strength_variant_strategy must be one of "
        "'monotone' or 'decorrelated_latin'"
    )


def _balanced_strength_scale(
    config: dict[str, object],
    *,
    circuit_id: int,
    mechanism_id: str,
    location_period: int | None = None,
    location_offset: int = 0,
) -> float:
    repetitions = _balanced_repetitions(config)
    if repetitions <= 1:
        return 1.0
    low = float(config.get("balanced_strength_min_scale", 0.65))
    high = float(config.get("balanced_strength_max_scale", 1.35))
    if high < low:
        low, high = high, low
    rank = _balanced_strength_rank(
        config,
        circuit_id=circuit_id,
        mechanism_id=mechanism_id,
        location_period=location_period,
        location_offset=location_offset,
    )
    fraction = float(rank) / float(repetitions - 1)
    return low + (high - low) * fraction


def _apply_balanced_strength_variant(
    params: dict[str, object],
    *,
    config: dict[str, object],
    circuit_id: int,
    mechanism_id: str,
    location_period: int | None = None,
    location_offset: int = 0,
) -> dict[str, object]:
    if not _balanced_strength_variants_enabled(config):
        return dict(params)
    scale = _balanced_strength_scale(
        config,
        circuit_id=circuit_id,
        mechanism_id=mechanism_id,
        location_period=location_period,
        location_offset=location_offset,
    )
    out = dict(params)
    scaled_values: list[float] = []
    for key in BALANCED_STRENGTH_PARAMETER_NAMES:
        if key not in out or isinstance(out.get(key), bool):
            continue
        try:
            value = float(out[key])  # type: ignore[arg-type]
        except (TypeError, ValueError):
            continue
        scaled = value * scale
        if key.startswith("p") or key.startswith("gamma") or key == "eta":
            scaled = min(max(scaled, 0.0), 1.0)
        out[key] = scaled
        scaled_values.append(abs(float(scaled)))
    if scaled_values and "strength" not in out:
        out["strength"] = max(scaled_values)
    return out


def _circuit_depth(config: dict[str, object]) -> int:
    return circuit_depth(config)


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
        "M0": (MECHANISM_NAMES["M0"], "id", 0),
        "M4": (MECHANISM_NAMES["M4"], "id", 3),
        "M5": (MECHANISM_NAMES["M5"], "id", 6),
        "M6": (MECHANISM_NAMES["M6"], "rx", 2),
        "M7": (MECHANISM_NAMES["M7"], "rz", 1),
        "M11": (MECHANISM_NAMES["M11"], "id", 5),
        "M13": (MECHANISM_NAMES["M13"], "rx", 7),
        "M14": (MECHANISM_NAMES["M14"], "rx", 8),
        "M15": (MECHANISM_NAMES["M15"], "id", 4),
        "M17": (MECHANISM_NAMES["M17"], "reset", 6),
        "M18": (MECHANISM_NAMES["M18"], "reset", 8),
        "M19": (MECHANISM_NAMES["M19"], "id", 8),
        "M20": (MECHANISM_NAMES["M20"], "ry", 9),
        "M24": (MECHANISM_NAMES["M24"], "id", 10),
        "M25": (MECHANISM_NAMES["M25"], "id", 11),
        "M26": (MECHANISM_NAMES["M26"], "id", 12),
        "M27": (MECHANISM_NAMES["M27"], "id", 13),
        "M34": (MECHANISM_NAMES["M34"], "id", 14),
    }
    for mech, (name, instruction, target) in single_plan.items():
        if mech not in enabled:
            continue
        local_params = dict(params.get(mech, {}))
        target_qubit = (int(target) + offset) % n
        location_offset = int(target) % n
        if mech == "M13":
            epsilons = _drift_epsilons(local_params, _balanced_repetitions(config))
            epsilon_rank = _balanced_strength_rank(
                config,
                circuit_id=circuit_id,
                mechanism_id=mech,
                location_period=n,
                location_offset=location_offset,
            )
            local_params["epsilon"] = epsilons[epsilon_rank % len(epsilons)]
            instruction = _operation_instruction_from_params(local_params, default="rx")
        if mech == "M14":
            instruction = _operation_instruction_from_params(local_params, default="rx")
        if mech == "M11":
            local_params = _m11_spectator_overlay_parameters(local_params, circuit_id=circuit_id, target=target_qubit, num_qubits=n)
        local_params = _apply_balanced_strength_variant(
            local_params,
            config=config,
            circuit_id=circuit_id,
            mechanism_id=mech,
            location_period=n,
            location_offset=location_offset,
        )
        specs.append(
            MechanismSpec(
                mech,
                name,
                1,
                local_params,
                instruction=instruction,
                qubits=(target_qubit,),
                circuit_id=circuit_id,
            )
        )

    pair_plan = [
        ("M8", MECHANISM_NAMES["M8"], 0),
        ("M9", MECHANISM_NAMES["M9"], 1),
        ("M10", MECHANISM_NAMES["M10"], 2),
        ("M12", MECHANISM_NAMES["M12"], 3),
        ("M21", MECHANISM_NAMES["M21"], 4),
        ("M22", MECHANISM_NAMES["M22"], 5),
        ("M23", MECHANISM_NAMES["M23"], 6),
        ("M28", MECHANISM_NAMES["M28"], 7),
        ("M29", MECHANISM_NAMES["M29"], 8),
        ("M30", MECHANISM_NAMES["M30"], 9),
        ("M31", MECHANISM_NAMES["M31"], 10),
        ("M32", MECHANISM_NAMES["M32"], 11),
        ("M33", MECHANISM_NAMES["M33"], 12),
    ]
    for mech, name, base_left in pair_plan:
        if mech not in enabled:
            continue
        left = (int(base_left) + pair_offset) % max(1, n - 1)
        location_period = max(1, n - 1)
        local_params = _apply_balanced_strength_variant(
            dict(params.get(mech, {})),
            config=config,
            circuit_id=circuit_id,
            mechanism_id=mech,
            location_period=location_period,
            location_offset=int(base_left) % location_period,
        )
        specs.append(
            MechanismSpec(
                mech,
                name,
                2,
                local_params,
                instruction="rzz",
                qubits=(left, left + 1),
                circuit_id=circuit_id,
            )
        )

    for readout_idx, (mech, name) in enumerate((
        ("M1", MECHANISM_NAMES["M1"]),
        ("M2", MECHANISM_NAMES["M2"]),
        ("M3", MECHANISM_NAMES["M3"]),
        ("M16", MECHANISM_NAMES["M16"]),
    )):
        if mech in enabled:
            q = (readout_idx + offset) % n
            local_params = _apply_balanced_strength_variant(
                dict(params.get(mech, {})),
                config=config,
                circuit_id=circuit_id,
                mechanism_id=mech,
                location_period=n,
                location_offset=readout_idx % n,
            )
            specs.append(MechanismSpec(mech, name, 1, local_params, instruction="measure", qubits=(q,), circuit_id=circuit_id))
    return sorted(specs, key=lambda spec: (_mechanism_sort_key(spec.mechanism_id), spec.qubits))


def _single_targets(num_qubits: int) -> dict[str, int]:
    n = int(num_qubits)
    requested = {
        "M0": 0,
        "M7": 1,
        "M6": 2,
        "M4": 3,
        "M15": 4,
        "M11": 5,
        "M5": 6,
        "M13": 7,
        "M14": 8,
        "M17": 6,
        "M18": 8,
        "M19": 8,
        "M20": 9,
        "M24": 10,
        "M25": 11,
        "M26": 12,
        "M27": 13,
        "M34": 14,
    }
    return {key: min(max(0, value), n - 1) for key, value in requested.items()}


def _m11_spectator_overlay_parameters(base: dict[str, object], *, circuit_id: int, target: int, num_qubits: int) -> dict[str, object]:
    params = dict(base)
    idx = int(circuit_id) % 4
    base_mechanisms = ("M8", "M7", "M1", "M17")
    coupling_axes = ("ZZ", "RZ", "readout_bias", "reset_bias")
    timing_contexts = ("same_cycle", "prev_cycle", "same_cycle", "shot_block_drift")
    victim_locations = ("edge", "qubit_id", "detector", "qubit_id")
    aggressor_locations = ("adjacent_gate", "previous_cycle_edge", "same_cycle_qubit", "shot_block")
    strength = float(params.get("strength", params.get("spectator_strength", params.get("epsilon", 0.02))))
    n = max(1, int(num_qubits))
    params.update(
        {
            "spectator_overlay_present": True,
            "base_mechanism": base_mechanisms[idx],
            "victim_relative_location": victim_locations[idx],
            "aggressor_relative_location": aggressor_locations[idx],
            "coupling_axis": coupling_axes[idx],
            "timing_context": timing_contexts[idx],
            "strength": strength,
            "spectator_strength": strength,
            "victim_qubit": int(target) % n,
            "aggressor_qubit": (int(target) + 1 + idx) % n,
            "claims_standalone_flat_mechanism": False,
        }
    )
    return params


def _operation_instruction_from_params(parameters: dict[str, object], *, default: str = "rx") -> str:
    return canonical_single_qubit_axis(
        parameters.get("operation_axis", parameters.get("instruction", parameters.get("axis", default))),
        default=default,
    )


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
        plan.append(("M8" if "M8" in enabled else pair_mechanisms[pair % len(pair_mechanisms)], pair))
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


def _profile_ry_qubits(num_qubits: int) -> list[int]:
    targets = [9]
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
