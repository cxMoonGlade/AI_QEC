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

MECHANISM_CONTRACTS: dict[str, dict[str, object]] = {
    "M0": {
        "contract_role": "aggregate_family",
        "base_family": "local_pauli_process",
        "dimensions": ["pauli_axis_mixture", "strength", "context_relative_location"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": False,
    },
    "M1": {
        "contract_role": "family_direction_slice",
        "base_family": "readout_spam",
        "dimensions": ["assignment_direction_0_to_1", "strength", "context_relative_location"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": False,
    },
    "M2": {
        "contract_role": "family_direction_slice",
        "base_family": "readout_spam",
        "dimensions": ["assignment_direction_1_to_0", "strength", "context_relative_location"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": False,
    },
    "M3": {
        "contract_role": "coarse_mixture_family",
        "base_family": "readout_spam",
        "dimensions": ["symmetric_assignment", "strength", "context_relative_location"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": False,
    },
    "M4": {
        "contract_role": "atomic_channel",
        "base_family": "relaxation_dephasing",
        "dimensions": ["relaxation_down", "strength", "context_relative_location"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": True,
    },
    "M5": {
        "contract_role": "family_axis_slice",
        "base_family": "relaxation_dephasing",
        "dimensions": ["idle_phase_axis", "strength", "context_relative_location"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": True,
    },
    "M6": {
        "contract_role": "family_axis_slice",
        "base_family": "coherent_control",
        "dimensions": ["axis_rx", "strength", "context_relative_location"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": True,
        "current_visible_surface_flat_exact_claim_allowed": False,
        "current_visible_surface_claim_target": "family_axis_dimension_recovery",
        "paired_observability_group": ["M6", "M13"],
        "flat_exact_claim_blocker": (
            "M6 shares the RX coherent-control surface with drifted M13; current Stage 3/S5 "
            "Z/X-visible rows support family, location, strength, and axis diagnostics, not a "
            "standalone flat-exact M6 claim when M13 is present."
        ),
    },
    "M7": {
        "contract_role": "family_axis_slice",
        "base_family": "coherent_control",
        "dimensions": ["axis_rz", "strength", "context_relative_location"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": True,
    },
    "M8": {
        "contract_role": "family_axis_slice",
        "base_family": "coherent_two_qubit_phase",
        "dimensions": ["axis_zz", "strength", "context_relative_edge"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": True,
    },
    "M9": {
        "contract_role": "coarse_mixture_family",
        "base_family": "two_qubit_pauli_process",
        "dimensions": ["15_pauli_support_mixture", "strength", "context_relative_edge"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": False,
    },
    "M10": {
        "contract_role": "coherent_mixture_family",
        "base_family": "parasitic_coupling",
        "dimensions": ["xx_component", "yy_component", "strength", "context_relative_edge"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": False,
    },
    "M11": {
        "contract_role": "overlay_family",
        "base_family": "spectator_crosstalk",
        "dimensions": ["base_mechanism", "victim_relative_location", "aggressor_relative_location", "coupling_axis", "timing_context", "strength"],
        "leaf_exact_effect_supported": False,
        "primary_flat_cluster_target": False,
    },
    "M12": {
        "contract_role": "atomic_channel",
        "base_family": "correlated_relaxation",
        "dimensions": ["correlated_relaxation", "strength", "context_relative_edge"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": True,
    },
    "M13": {
        "contract_role": "context_conditioned_family",
        "base_family": "coherent_control_drift",
        "dimensions": ["operation_axis", "drift_index", "drift_strength", "drift_mixture_span", "context_relative_location"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": False,
        "current_visible_surface_flat_exact_claim_allowed": False,
        "current_visible_surface_claim_target": "context_conditioned_drift_recovery",
        "paired_observability_group": ["M6", "M13"],
        "row_level_visible_geometry": "random_unitary_drift_overlay_on_declared_operation_axis",
        "flat_exact_claim_blocker": "M13 is a multi-context drift-overlay target, not a single flat exact cluster target.",
    },
    "M14": {
        "contract_role": "operation_conditioned_family",
        "base_family": "coherent_control_operation_context",
        "dimensions": ["operation_axis", "error_axis", "strength", "context_relative_location"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": False,
    },
    "M15": {
        "contract_role": "surrogate_stress_family",
        "base_family": "non_pauli_stress",
        "dimensions": ["custom_kraus_eta", "strength", "context_relative_location"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": False,
    },
    "M16": {
        "contract_role": "context_conditioned_family",
        "base_family": "readout_spam",
        "dimensions": ["measurement_context", "assignment_direction", "strength", "context_relative_location"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": False,
    },
    "M17": {
        "contract_role": "atomic_channel",
        "base_family": "prep_reset_spam",
        "dimensions": ["reset_to_1", "strength", "context_relative_location"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": True,
    },
    "M18": {
        "contract_role": "operation_conditioned_family",
        "base_family": "prep_reset_spam",
        "dimensions": ["prep_or_reset_axis", "coherent_asymmetry", "strength", "context_relative_location"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": False,
    },
    "M19": {
        "contract_role": "surrogate_stress_family",
        "base_family": "non_pauli_stress",
        "dimensions": ["mixed_ptm_residual", "eta", "context_relative_location"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": False,
    },
    "M20": {
        "contract_role": "family_axis_slice",
        "base_family": "coherent_control",
        "dimensions": ["axis_ry", "strength", "context_relative_location"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": True,
    },
    "M21": {
        "contract_role": "family_branch_slice",
        "base_family": "coherent_two_qubit_phase",
        "dimensions": ["conditional_phase_branch", "strength", "context_relative_edge"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": True,
    },
    "M22": {
        "contract_role": "family_axis_slice",
        "base_family": "parasitic_coupling",
        "dimensions": ["axis_xx", "strength", "context_relative_edge"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": True,
        "current_visible_surface_flat_exact_claim_allowed": False,
        "current_visible_surface_claim_target": "parasitic_axis_dimension_recovery",
        "paired_observability_group": ["M22", "M23"],
        "flat_exact_claim_blocker": (
            "M22/M23 require an axis-sensitive quadrature probe before current Stage 3/S5 "
            "Z/X-visible evidence may claim flat-exact XX-vs-YY separation."
        ),
    },
    "M23": {
        "contract_role": "family_axis_slice",
        "base_family": "parasitic_coupling",
        "dimensions": ["axis_yy", "strength", "context_relative_edge"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": True,
        "current_visible_surface_flat_exact_claim_allowed": False,
        "current_visible_surface_claim_target": "parasitic_axis_dimension_recovery",
        "paired_observability_group": ["M22", "M23"],
        "flat_exact_claim_blocker": (
            "M22/M23 require an axis-sensitive quadrature probe before current Stage 3/S5 "
            "Z/X-visible evidence may claim flat-exact XX-vs-YY separation."
        ),
    },
    "M24": {
        "contract_role": "atomic_channel",
        "base_family": "thermal_relaxation",
        "dimensions": ["excitation_up", "strength", "context_relative_location"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": True,
    },
    "M25": {
        "contract_role": "family_axis_slice",
        "base_family": "local_pauli_process",
        "dimensions": ["pauli_axis_x", "strength", "context_relative_location"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": True,
    },
    "M26": {
        "contract_role": "family_axis_slice",
        "base_family": "local_pauli_process",
        "dimensions": ["pauli_axis_y", "strength", "context_relative_location"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": True,
    },
    "M27": {
        "contract_role": "coherent_mixture_family",
        "base_family": "coherent_control",
        "dimensions": ["axis_xz_vector", "strength", "context_relative_location"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": False,
    },
    "M28": {
        "contract_role": "family_axis_slice",
        "base_family": "parasitic_coupling",
        "dimensions": ["axis_xy", "strength", "context_relative_edge"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": True,
    },
    "M29": {
        "contract_role": "family_axis_slice",
        "base_family": "parasitic_coupling",
        "dimensions": ["axis_zx", "strength", "context_relative_edge"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": True,
    },
    "M30": {
        "contract_role": "family_axis_slice",
        "base_family": "parasitic_coupling",
        "dimensions": ["axis_zy", "strength", "context_relative_edge"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": True,
    },
    "M31": {
        "contract_role": "family_axis_slice",
        "base_family": "parasitic_coupling",
        "dimensions": ["axis_xz", "strength", "context_relative_edge"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": True,
    },
    "M32": {
        "contract_role": "family_axis_slice",
        "base_family": "parasitic_coupling",
        "dimensions": ["axis_yz", "strength", "context_relative_edge"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": True,
    },
    "M33": {
        "contract_role": "family_axis_slice",
        "base_family": "parasitic_coupling",
        "dimensions": ["axis_yx", "strength", "context_relative_edge"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": True,
    },
    "M34": {
        "contract_role": "surrogate_stress_family",
        "base_family": "leakage_surrogate",
        "dimensions": ["computational_subspace_survival", "strength", "context_relative_location"],
        "leaf_exact_effect_supported": True,
        "primary_flat_cluster_target": False,
    },
}

MECHANISM_LEAF_EXACT_IDS = tuple(mechanism_id for mechanism_id in IMPLEMENTED_MECHANISM_IDS if MECHANISM_CONTRACTS[mechanism_id]["leaf_exact_effect_supported"])
PRIMARY_FLAT_CLUSTER_TARGET_IDS = tuple(
    mechanism_id for mechanism_id in IMPLEMENTED_MECHANISM_IDS if MECHANISM_CONTRACTS[mechanism_id]["primary_flat_cluster_target"]
)
NON_FLAT_PRIMARY_TARGET_IDS = tuple(
    mechanism_id for mechanism_id in IMPLEMENTED_MECHANISM_IDS if not MECHANISM_CONTRACTS[mechanism_id]["primary_flat_cluster_target"]
)
CURRENT_VISIBLE_SURFACE_FLAT_EXACT_CLAIM_TARGET_IDS = tuple(
    mechanism_id
    for mechanism_id in PRIMARY_FLAT_CLUSTER_TARGET_IDS
    if bool(MECHANISM_CONTRACTS[mechanism_id].get("current_visible_surface_flat_exact_claim_allowed", True))
)
SURFACE_CONDITIONAL_DIMENSION_TARGET_IDS = tuple(
    mechanism_id
    for mechanism_id in PRIMARY_FLAT_CLUSTER_TARGET_IDS
    if not bool(MECHANISM_CONTRACTS[mechanism_id].get("current_visible_surface_flat_exact_claim_allowed", True))
)
CONTRACT_TYPED_DIMENSION_TARGET_IDS = tuple(
    dict.fromkeys((*NON_FLAT_PRIMARY_TARGET_IDS, *SURFACE_CONDITIONAL_DIMENSION_TARGET_IDS))
)

PRIMARY_FLAT_PUBLIC_LABELS = tuple(f"F{idx}" for idx, _mechanism_id in enumerate(PRIMARY_FLAT_CLUSTER_TARGET_IDS))
NON_FLAT_PUBLIC_LABELS = tuple(f"M{idx}" for idx, _mechanism_id in enumerate(NON_FLAT_PRIMARY_TARGET_IDS))
LEGACY_MECHANISM_ID_TO_PUBLIC_LABEL = {
    **{mechanism_id: label for mechanism_id, label in zip(PRIMARY_FLAT_CLUSTER_TARGET_IDS, PRIMARY_FLAT_PUBLIC_LABELS)},
    **{mechanism_id: label for mechanism_id, label in zip(NON_FLAT_PRIMARY_TARGET_IDS, NON_FLAT_PUBLIC_LABELS)},
}
PUBLIC_LABEL_TO_LEGACY_MECHANISM_ID = {label: mechanism_id for mechanism_id, label in LEGACY_MECHANISM_ID_TO_PUBLIC_LABEL.items()}
LEGACY_MECHANISM_ID_TO_LABEL_NAMESPACE = {
    **{mechanism_id: "flat" for mechanism_id in PRIMARY_FLAT_CLUSTER_TARGET_IDS},
    **{mechanism_id: "non_flat" for mechanism_id in NON_FLAT_PRIMARY_TARGET_IDS},
}

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


def mechanism_public_label(mechanism_id: str) -> str:
    """Return the canonical public F/M label for a legacy catalog ID."""

    key = str(mechanism_id)
    if key not in LEGACY_MECHANISM_ID_TO_PUBLIC_LABEL:
        raise KeyError(f"unknown mechanism id {mechanism_id!r}")
    return LEGACY_MECHANISM_ID_TO_PUBLIC_LABEL[key]


def mechanism_label_namespace(mechanism_id: str) -> str:
    """Return ``flat`` or ``non_flat`` for a legacy catalog ID."""

    key = str(mechanism_id)
    if key not in LEGACY_MECHANISM_ID_TO_LABEL_NAMESPACE:
        raise KeyError(f"unknown mechanism id {mechanism_id!r}")
    return LEGACY_MECHANISM_ID_TO_LABEL_NAMESPACE[key]


def legacy_mechanism_id(public_label: str) -> str:
    """Return the legacy catalog ID for a canonical public F/M label."""

    key = str(public_label)
    if key not in PUBLIC_LABEL_TO_LEGACY_MECHANISM_ID:
        raise KeyError(f"unknown public mechanism label {public_label!r}")
    return PUBLIC_LABEL_TO_LEGACY_MECHANISM_ID[key]


def mechanism_contract(mechanism_id: str) -> dict[str, object]:
    """Return the Stage 3/5 interpretation contract for a legacy catalog ID."""

    key = str(mechanism_id)
    if key not in MECHANISM_CONTRACTS:
        raise KeyError(f"unknown mechanism id {mechanism_id!r}")
    return {
        "legacy_catalog_id": key,
        "public_label": mechanism_public_label(key),
        "label_namespace": mechanism_label_namespace(key),
        **dict(MECHANISM_CONTRACTS[key]),
    }


def mechanism_taxonomy_contract_audit() -> dict[str, object]:
    """Audit whether the legacy catalog is covered by explicit public labels."""

    covered = set(MECHANISM_CONTRACTS)
    expected = set(IMPLEMENTED_MECHANISM_IDS)
    missing = sorted(expected - covered)
    extra = sorted(covered - expected)
    leaf = list(MECHANISM_LEAF_EXACT_IDS)
    primary_flat = list(PRIMARY_FLAT_CLUSTER_TARGET_IDS)
    non_flat = list(NON_FLAT_PRIMARY_TARGET_IDS)
    current_flat_claim = list(CURRENT_VISIBLE_SURFACE_FLAT_EXACT_CLAIM_TARGET_IDS)
    surface_conditional = list(SURFACE_CONDITIONAL_DIMENSION_TARGET_IDS)
    checks = {
        "all_implemented_mechanisms_have_contracts": not missing and not extra,
        "m11_is_overlay_not_leaf_exact": "M11" not in set(leaf) and MECHANISM_CONTRACTS["M11"]["contract_role"] == "overlay_family",
        "non_flat_primary_targets_are_explicit": bool(non_flat),
        "leaf_exact_targets_are_subset_of_implemented": set(leaf).issubset(expected),
        "primary_flat_targets_are_subset_of_leaf_exact": set(primary_flat).issubset(set(leaf)),
        "current_visible_surface_flat_exact_claim_targets_are_subset_of_primary_flat": set(current_flat_claim).issubset(set(primary_flat)),
        "surface_conditional_dimension_targets_are_primary_flat": set(surface_conditional).issubset(set(primary_flat)),
        "surface_conditional_dimension_targets_have_blocker": all(
            bool(MECHANISM_CONTRACTS[value].get("flat_exact_claim_blocker", "")) for value in surface_conditional
        ),
        "all_implemented_mechanisms_have_public_labels": set(LEGACY_MECHANISM_ID_TO_PUBLIC_LABEL) == expected,
        "public_labels_are_unique": len(set(LEGACY_MECHANISM_ID_TO_PUBLIC_LABEL.values())) == len(IMPLEMENTED_MECHANISM_IDS),
        "flat_targets_use_f_namespace": all(str(LEGACY_MECHANISM_ID_TO_PUBLIC_LABEL[value]).startswith("F") for value in primary_flat),
        "non_flat_targets_use_m_namespace": all(str(LEGACY_MECHANISM_ID_TO_PUBLIC_LABEL[value]).startswith("M") for value in non_flat),
        "public_label_reverse_map_is_complete": set(PUBLIC_LABEL_TO_LEGACY_MECHANISM_ID.values()) == expected,
    }
    return {
        "schema": "scope_static_mechanism_taxonomy_contract_audit_v2",
        "passed": all(checks.values()),
        "checks": checks,
        "label_scheme": "flat_F_nonflat_M_v1",
        "legacy_catalog_id_policy": "M0-M34 remain implementation-stable legacy IDs; public_label is the semantic mechanism label.",
        "missing_contracts": missing,
        "extra_contracts": extra,
        "leaf_exact_effect_ids": leaf,
        "primary_flat_cluster_target_ids": primary_flat,
        "non_flat_primary_target_ids": non_flat,
        "current_visible_surface_flat_exact_claim_target_ids": current_flat_claim,
        "surface_conditional_dimension_target_ids": surface_conditional,
        "contract_typed_dimension_target_ids": list(CONTRACT_TYPED_DIMENSION_TARGET_IDS),
        "primary_flat_public_labels": list(PRIMARY_FLAT_PUBLIC_LABELS),
        "non_flat_public_labels": list(NON_FLAT_PUBLIC_LABELS),
        "legacy_catalog_id_to_public_label": dict(LEGACY_MECHANISM_ID_TO_PUBLIC_LABEL),
        "public_label_to_legacy_catalog_id": dict(PUBLIC_LABEL_TO_LEGACY_MECHANISM_ID),
        "contracts": {key: mechanism_contract(key) for key in IMPLEMENTED_MECHANISM_IDS},
    }
