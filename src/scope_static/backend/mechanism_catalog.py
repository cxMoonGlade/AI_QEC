from __future__ import annotations

IMPLEMENTED_MECHANISM_IDS = tuple(f"M{idx}" for idx in range(35))

MECHANISM_NAMES = {
    "M0": "local_stochastic_pauli_gate_error",
    "M1": "readout_0_to_1_bias",
    "M2": "readout_1_to_0_bias",
    "M3": "readout_symmetric_assignment_noise",
    "M4": "amplitude_damping_gate_error",
    "M5": "idle_dephasing_or_relaxation_error",
    "M6": "coherent_rx_overrotation",
    "M7": "coherent_rz_overrotation",
    "M8": "coherent_rzz_overrotation",
    "M9": "two_qubit_depolarizing_after_rzz",
    "M10": "coherent_rxx_ryy_perturbation",
    "M11": "spectator_crosstalk_rz_or_zz",
    "M12": "correlated_two_qubit_relaxation",
    "M13": "drifted_coherent_overrotation",
    "M14": "operation_dependent_error",
    "M15": "hard_non_pauli_kraus_gate_error",
    "M16": "measurement_context_bias",
    "M17": "reset_to_1_bias",
    "M18": "prep_axis_or_reset_asymmetry_bias",
    "M19": "weak_type4_ptm_mixing",
    "M20": "coherent_ry_overrotation",
    "M21": "conditional_phase_branch_error",
    "M22": "coherent_cxx_parasitic_coupling",
    "M23": "coherent_cyy_parasitic_coupling",
    "M24": "thermal_excitation_gate_error",
    "M25": "stochastic_bit_flip_gate_error",
    "M26": "stochastic_y_gate_error",
    "M27": "coherent_h_axis_overrotation",
    "M28": "coherent_xy_parasitic_coupling",
    "M29": "coherent_zx_parasitic_coupling",
    "M30": "coherent_zy_parasitic_coupling",
    "M31": "coherent_xz_parasitic_coupling",
    "M32": "coherent_yz_parasitic_coupling",
    "M33": "coherent_yx_parasitic_coupling",
    "M34": "leakage_relaxation_surrogate",
}

READOUT_MECHANISM_IDS = ("M1", "M2", "M3", "M16")
PREP_RESET_MECHANISM_IDS = ("M17", "M18")
SPECTATOR_MECHANISM_IDS = ("M11",)
RZZ_FAMILY_IDS = ("M8", "M9", "M10", "M12", "M21", "M22", "M23", "M28", "M29", "M30", "M31", "M32", "M33")

MECHANISM_SET_A_IDS = tuple(f"M{idx}" for idx in range(10))
MECHANISM_SET_B_IDS = tuple(f"M{idx}" for idx in range(15))
MECHANISM_SET_C_IDS = tuple(f"M{idx}" for idx in range(25))
MECHANISM_SET_D_IDS = IMPLEMENTED_MECHANISM_IDS

NAMED_MECHANISM_SETS = {
    "set_A": set(MECHANISM_SET_A_IDS),
    "set_B": set(MECHANISM_SET_B_IDS),
    "set_C": set(MECHANISM_SET_C_IDS),
    "set_D": set(MECHANISM_SET_D_IDS),
    "allM": set(IMPLEMENTED_MECHANISM_IDS),
}

LEGACY_TO_CURRENT_MECHANISM_IDS = {
    "M0": "M0",
    "M1": "M8",
    "M2": "M6",
    "M3": "M7",
    "M4": "M4",
    "M5": "M15",
    "M6": "M9",
    "M7": "M10",
    "M8": "M11",
    "M9": "M12",
    "M10": "M13",
    "M11": "M5",
    "M12": "M14",
    "M13": "M1",
    "M14": "M2",
    "M15": "M3",
    "M16": "M16",
    "M17": "M17",
    "M18": "M18",
    "M19": "M19",
}


def mechanism_name(mechanism_id: str) -> str:
    return MECHANISM_NAMES[str(mechanism_id)]
