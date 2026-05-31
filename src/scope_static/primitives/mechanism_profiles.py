from __future__ import annotations

from copy import deepcopy
from typing import Mapping

from .mechanism_catalog import IMPLEMENTED_MECHANISM_IDS, MECHANISM_NAMES


PROFILE_SCHEMA = "scope_static_mechanism_weight_profile_v1"


_CURRENT_MECHANISM_PARAMETERS: dict[str, dict[str, object]] = {
    "M0": {"p_x": 0.0015, "p_y": 0.0008, "p_z": 0.0022},
    "M1": {"p0_to_1": 0.028, "p1_to_0": 0.006},
    "M2": {"p0_to_1": 0.006, "p1_to_0": 0.024},
    "M3": {"p": 0.020},
    "M4": {"gamma": 0.018},
    "M5": {"p_z": 0.0025},
    "M6": {"epsilon": 0.026},
    "M7": {"epsilon": 0.022},
    "M8": {"epsilon": 0.028},
    "M9": {"p": 0.007},
    "M10": {"epsilon_x": 0.020, "epsilon_y": 0.014},
    "M11": {"epsilon": 0.014},
    "M12": {"gamma": 0.011},
    "M13": {"operation_axis": "rx", "epsilon_mean": 0.030, "epsilon_span": 0.014},
    "M14": {"operation_axis": "rx", "error_axis": "rz", "epsilon": 0.026},
    "M15": {"eta": 0.016},
    "M16": {"p": 0.018},
    "M17": {"p": 0.020},
    "M18": {"epsilon": 0.022},
    "M19": {"eta": 0.004},
    "M20": {"epsilon": 0.024},
    "M21": {"epsilon": 0.030},
    "M22": {"epsilon": 0.018},
    "M23": {"epsilon": 0.016},
    "M24": {"gamma_up": 0.004},
    "M25": {"p": 0.006},
    "M26": {"p": 0.0035},
    "M27": {"epsilon": 0.020},
    "M28": {"epsilon": 0.012},
    "M29": {"epsilon": 0.018},
    "M30": {"epsilon": 0.013},
    "M31": {"epsilon": 0.013},
    "M32": {"epsilon": 0.012},
    "M33": {"epsilon": 0.011},
    "M34": {"p": 0.004},
}


_REALISTIC_COUNTS: dict[str, int] = {
    "M0": 12,
    "M1": 12,
    "M2": 10,
    "M3": 12,
    "M4": 10,
    "M5": 10,
    "M6": 8,
    "M7": 8,
    "M8": 11,
    "M9": 10,
    "M10": 5,
    "M11": 4,
    "M12": 5,
    "M13": 7,
    "M14": 7,
    "M15": 3,
    "M16": 9,
    "M17": 8,
    "M18": 7,
    "M19": 3,
    "M20": 5,
    "M21": 6,
    "M22": 4,
    "M23": 4,
    "M24": 6,
    "M25": 9,
    "M26": 5,
    "M27": 4,
    "M28": 3,
    "M29": 5,
    "M30": 3,
    "M31": 3,
    "M32": 3,
    "M33": 3,
    "M34": 4,
}


_FAMILY: dict[str, str] = {
    "M0": "local_stochastic_process",
    "M1": "readout_spam",
    "M2": "readout_spam",
    "M3": "readout_spam",
    "M4": "relaxation_dephasing",
    "M5": "relaxation_dephasing",
    "M6": "coherent_control",
    "M7": "coherent_control",
    "M8": "two_qubit_gate",
    "M9": "two_qubit_gate",
    "M10": "parasitic_coupling",
    "M11": "spectator_crosstalk",
    "M12": "correlated_relaxation",
    "M13": "slow_drift",
    "M14": "operation_context",
    "M15": "non_pauli_stress",
    "M16": "readout_spam",
    "M17": "prep_reset_spam",
    "M18": "prep_reset_spam",
    "M19": "non_pauli_stress",
    "M20": "coherent_control",
    "M21": "two_qubit_gate",
    "M22": "parasitic_coupling",
    "M23": "parasitic_coupling",
    "M24": "thermal_relaxation",
    "M25": "local_stochastic_process",
    "M26": "local_stochastic_process",
    "M27": "coherent_control",
    "M28": "parasitic_coupling",
    "M29": "parasitic_coupling",
    "M30": "parasitic_coupling",
    "M31": "parasitic_coupling",
    "M32": "parasitic_coupling",
    "M33": "parasitic_coupling",
    "M34": "leakage_surrogate",
}


_TIER: dict[str, str] = {
    "M0": "high",
    "M1": "highest",
    "M2": "highest",
    "M3": "highest",
    "M4": "high",
    "M5": "high",
    "M6": "high",
    "M7": "high",
    "M8": "high",
    "M9": "high",
    "M10": "medium",
    "M11": "rare_high_impact",
    "M12": "medium",
    "M13": "high",
    "M14": "high",
    "M15": "stress_floor",
    "M16": "highest",
    "M17": "highest",
    "M18": "highest",
    "M19": "stress_floor",
    "M20": "high",
    "M21": "medium",
    "M22": "medium",
    "M23": "medium",
    "M24": "high",
    "M25": "high",
    "M26": "high",
    "M27": "medium",
    "M28": "medium",
    "M29": "medium",
    "M30": "medium",
    "M31": "medium",
    "M32": "medium",
    "M33": "medium",
    "M34": "rare_high_impact",
}


def mechanism_profile_names() -> tuple[str, ...]:
    return ("weighted_realistic_v1", "weighted_discovery_floor_v1")


def resolve_mechanism_weight_profile(name: str) -> dict[str, object]:
    """Resolve a named current-catalog mechanism weighting profile.

    The returned mapping is safe to merge into teacher configs. It is
    intentionally not a hardware-calibrated probability table; it is a
    literature-informed, exposure-weighted synthetic support profile.
    """

    profile = str(name)
    if profile == "weighted_realistic_v1":
        counts = dict(_REALISTIC_COUNTS)
        rare_floor = 3
    elif profile == "weighted_discovery_floor_v1":
        counts = {key: max(4, value) for key, value in _REALISTIC_COUNTS.items()}
        rare_floor = 4
    else:
        raise ValueError(f"unknown mechanism_weight_profile {name!r}")
    _validate_profile_counts(counts)
    parameters = deepcopy(_CURRENT_MECHANISM_PARAMETERS)
    return {
        "schema": PROFILE_SCHEMA,
        "profile_name": profile,
        "profile_type": "exposure_weighted_superconducting_qec_synthetic_prior",
        "not_hardware_calibrated": True,
        "claim_boundary": (
            "Mechanism weights encode realistic-ish superconducting QEC exposure imbalance "
            "for controlled synthetic stress tests. They are not measured device mechanism frequencies."
        ),
        "mechanism_set": list(IMPLEMENTED_MECHANISM_IDS),
        "mechanism_instance_counts": counts,
        "mechanisms": parameters,
        "rare_mechanism_floor": int(rare_floor),
        "entries": {
            mechanism_id: {
                "name": MECHANISM_NAMES[mechanism_id],
                "family": _FAMILY[mechanism_id],
                "tier": _TIER[mechanism_id],
                "instance_count": int(counts[mechanism_id]),
                "parameters": deepcopy(parameters[mechanism_id]),
            }
            for mechanism_id in IMPLEMENTED_MECHANISM_IDS
        },
    }


def apply_mechanism_weight_profile(
    config: Mapping[str, object],
    *,
    profile_name: str,
) -> dict[str, object]:
    resolved = resolve_mechanism_weight_profile(profile_name)
    result = dict(config)
    configured_mechanisms = result.get("mechanisms", {})
    configured_counts = result.get("mechanism_instance_counts", {})
    profile_mechanisms = dict(resolved["mechanisms"])  # type: ignore[arg-type]
    if isinstance(configured_mechanisms, dict):
        for mechanism_id, parameters in configured_mechanisms.items():
            current = dict(profile_mechanisms.get(str(mechanism_id), {}))
            current.update(dict(parameters) if isinstance(parameters, dict) else {})
            profile_mechanisms[str(mechanism_id)] = current
    result["mechanism_set"] = list(resolved["mechanism_set"])  # type: ignore[arg-type]
    result["mechanisms"] = profile_mechanisms
    result["mechanism_instance_counts"] = (
        dict(configured_counts)
        if isinstance(configured_counts, dict) and configured_counts
        else dict(resolved["mechanism_instance_counts"])  # type: ignore[arg-type]
    )
    result["mechanism_weight_profile_manifest"] = {
        key: deepcopy(value)
        for key, value in resolved.items()
        if key not in {"mechanisms", "mechanism_instance_counts"}
    }
    return result


def _validate_profile_counts(counts: Mapping[str, int]) -> None:
    expected = set(IMPLEMENTED_MECHANISM_IDS)
    actual = {str(key) for key in counts}
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValueError(f"mechanism profile must cover exactly current allM ids; missing={missing}, extra={extra}")
    for mechanism_id, count in counts.items():
        if int(count) <= 0:
            raise ValueError(f"mechanism profile count for {mechanism_id} must be positive")
        if MECHANISM_NAMES[str(mechanism_id)] != resolve_catalog_name(str(mechanism_id)):
            raise ValueError(f"mechanism profile semantic drift for {mechanism_id}")


def resolve_catalog_name(mechanism_id: str) -> str:
    return MECHANISM_NAMES[str(mechanism_id)]
