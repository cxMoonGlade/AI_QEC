#!/usr/bin/env python3
"""Symmetric complete-vector metrics for the frozen GCAPEPS differential."""

from __future__ import annotations

import math
from typing import Any, Mapping

import numpy as np


VECTOR_COMPARISON_SCHEMA = (
    "error_coupling_simulator.external."
    "gcapeps_n8_r3_complete_vector_comparison.v1"
)
REQUIRED_BANDS = {
    "d_rel_max",
    "d_norm_max",
    "infidelity_max",
    "fidelity_roundoff_correction_max",
}


def _validated_vector(value: Any, *, label: str) -> np.ndarray:
    array = np.asarray(value)
    if array.shape != (256,):
        raise ValueError(f"{label} must have shape (256,)")
    if array.dtype != np.dtype("complex128"):
        raise ValueError(f"{label} must already have dtype complex128")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{label} contains a nonfinite value")
    norm = float(np.linalg.norm(array))
    if not math.isfinite(norm) or norm <= 0.0:
        raise ValueError(f"{label} norm must be finite and strictly positive")
    return array


def _validated_bands(bands: Mapping[str, Any]) -> dict[str, float]:
    if not isinstance(bands, Mapping) or not REQUIRED_BANDS.issubset(bands):
        raise ValueError("complete-vector comparison bands are incomplete")
    validated: dict[str, float] = {}
    for name in REQUIRED_BANDS:
        value = bands[name]
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(float(value))
            or float(value) < 0.0
        ):
            raise ValueError(f"comparison band {name} is invalid")
        validated[name] = float(value)
    return validated


def compare_complete_vectors(
    left: Any,
    right: Any,
    *,
    bands: Mapping[str, Any],
) -> dict[str, Any]:
    """Compare two equal-status raw c128 vectors without fitting or casting."""

    left_array = _validated_vector(left, label="left vector")
    right_array = _validated_vector(right, label="right vector")
    limits = _validated_bands(bands)

    difference = right_array - left_array
    d_inf = float(np.max(np.abs(difference)))
    d_2 = float(np.linalg.norm(difference))
    left_norm = float(np.linalg.norm(left_array))
    right_norm = float(np.linalg.norm(right_array))
    denominator = left_norm + right_norm
    if not math.isfinite(denominator) or denominator <= 0.0:
        raise ValueError("complete-vector comparison denominator is invalid")
    d_rel = float(2.0 * d_2 / denominator)
    d_norm = float(2.0 * abs(right_norm - left_norm) / denominator)

    left_mass = float(np.vdot(left_array, left_array).real)
    right_mass = float(np.vdot(right_array, right_array).real)
    fidelity_denominator = left_mass * right_mass
    if (
        not math.isfinite(left_mass)
        or not math.isfinite(right_mass)
        or left_mass <= 0.0
        or right_mass <= 0.0
        or not math.isfinite(fidelity_denominator)
        or fidelity_denominator <= 0.0
    ):
        raise ValueError("complete-vector fidelity denominator is invalid")
    overlap = np.vdot(left_array, right_array)
    fidelity_raw = float(abs(overlap) ** 2 / fidelity_denominator)
    if not math.isfinite(fidelity_raw) or fidelity_raw < 0.0:
        raise ValueError("complete-vector fidelity is invalid")
    roundoff_correction = max(0.0, fidelity_raw - 1.0)
    roundoff_pass = (
        roundoff_correction
        <= limits["fidelity_roundoff_correction_max"]
    )
    fidelity = min(1.0, fidelity_raw) if roundoff_pass else fidelity_raw
    infidelity = 1.0 - fidelity

    gates = {
        "d_rel": d_rel <= limits["d_rel_max"],
        "d_norm": d_norm <= limits["d_norm_max"],
        "infidelity": infidelity <= limits["infidelity_max"],
        "fidelity_roundoff_correction": roundoff_pass,
    }
    verdict = "AGREE" if all(gates.values()) else "MISMATCH"
    return {
        "schema": VECTOR_COMPARISON_SCHEMA,
        "verdict": verdict,
        "d_inf": d_inf,
        "d_2": d_2,
        "d_rel": d_rel,
        "d_norm": d_norm,
        "left_norm": left_norm,
        "right_norm": right_norm,
        "fidelity_raw": fidelity_raw,
        "fidelity_roundoff_correction": roundoff_correction,
        "fidelity": fidelity,
        "infidelity": infidelity,
        "gates": gates,
        "phase_fit_performed": False,
        "normalization_performed": False,
        "dtype_cast_performed": False,
        "coordinate_permutation_performed": False,
    }


def grade_candidate_state_action(
    *,
    plain_preparation: Any,
    gcapeps_preparation: Any,
    plain_after_clifford: Any,
    gcapeps_after_clifford: Any,
    plain_final: Any,
    gcapeps_final: Any,
    gcapeps_residual: Any,
    anchor_vectors: Mapping[str, Any],
    bands: Mapping[str, Any],
) -> dict[str, Any]:
    """Grade the frozen pair symmetrically, with separate anchor rows."""

    required_anchor_names = {
        "closed_form_preparation",
        "gate_replay_preparation",
        "residual_state",
        "physical_preparation_after_clifford",
        "physical_from_residual_lift",
        "physical_from_signed_terms",
    }
    if not isinstance(anchor_vectors, Mapping) or not required_anchor_names.issubset(
        anchor_vectors
    ):
        raise ValueError("anchor vector family is incomplete")

    pair_rows = {
        "after_clifford": compare_complete_vectors(
            plain_after_clifford,
            gcapeps_after_clifford,
            bands=bands,
        ),
        "after_rank_three_update": compare_complete_vectors(
            plain_final,
            gcapeps_final,
            bands=bands,
        ),
    }
    differential_verdict = (
        "AGREE"
        if all(row["verdict"] == "AGREE" for row in pair_rows.values())
        else "MISMATCH"
    )

    fairness_rows = {
        "plain_preparation_vs_anchor": compare_complete_vectors(
            anchor_vectors["closed_form_preparation"],
            plain_preparation,
            bands=bands,
        ),
        "gcapeps_preparation_vs_anchor": compare_complete_vectors(
            anchor_vectors["closed_form_preparation"],
            gcapeps_preparation,
            bands=bands,
        ),
        "plain_prefix_vs_anchor": compare_complete_vectors(
            anchor_vectors["physical_preparation_after_clifford"],
            plain_after_clifford,
            bands=bands,
        ),
        "gcapeps_prefix_vs_anchor": compare_complete_vectors(
            anchor_vectors["physical_preparation_after_clifford"],
            gcapeps_after_clifford,
            bands=bands,
        ),
    }
    fairness_passed = all(
        row["verdict"] == "AGREE" for row in fairness_rows.values()
    )

    anchor_rows = {
        "anchor_dual_physical_form": compare_complete_vectors(
            anchor_vectors["physical_from_residual_lift"],
            anchor_vectors["physical_from_signed_terms"],
            bands=bands,
        ),
        "gcapeps_residual_vs_anchor_residual": compare_complete_vectors(
            anchor_vectors["residual_state"],
            gcapeps_residual,
            bands=bands,
        ),
        "plain_physical_vs_anchor_physical": compare_complete_vectors(
            anchor_vectors["physical_from_signed_terms"],
            plain_final,
            bands=bands,
        ),
        "gcapeps_physical_vs_anchor_physical": compare_complete_vectors(
            anchor_vectors["physical_from_signed_terms"],
            gcapeps_final,
            bands=bands,
        ),
    }
    anchor_verdict = (
        "PASS"
        if all(row["verdict"] == "AGREE" for row in anchor_rows.values())
        else "FAIL"
    )
    return {
        "candidate_role": "equal_status",
        "plain_candidate_is_truth": False,
        "gcapeps_candidate_is_truth": False,
        "pair_rows": pair_rows,
        "differential_verdict": differential_verdict,
        "fairness_rows": fairness_rows,
        "fairness_passed": fairness_passed,
        "anchor_rows": anchor_rows,
        "anchor_verdict": anchor_verdict,
    }


def terminal_semantics(
    *,
    differential_verdict: str,
    anchor_verdict: str,
    sdim_frame_verdict: str,
    exact_structure_and_fairness_passed: bool,
    controls_passed: bool,
    provenance_passed: bool,
    publication_preflight_passed: bool,
) -> dict[str, str]:
    """Apply terminal eligibility without changing pair or anchor numbers."""

    if differential_verdict not in {"AGREE", "MISMATCH", "INELIGIBLE"}:
        raise ValueError("invalid differential verdict")
    if anchor_verdict not in {"PASS", "FAIL", "INELIGIBLE"}:
        raise ValueError("invalid anchor verdict")
    if sdim_frame_verdict not in {"PASS", "FAIL", "INELIGIBLE"}:
        raise ValueError("invalid SDIM-frame verdict")
    for name, value in {
        "exact_structure_and_fairness_passed": (
            exact_structure_and_fairness_passed
        ),
        "controls_passed": controls_passed,
        "provenance_passed": provenance_passed,
        "publication_preflight_passed": publication_preflight_passed,
    }.items():
        if not isinstance(value, bool):
            raise ValueError(f"{name} must be boolean")

    eligibility_passed = (
        exact_structure_and_fairness_passed
        and controls_passed
        and provenance_passed
        and publication_preflight_passed
        and differential_verdict != "INELIGIBLE"
        and anchor_verdict != "INELIGIBLE"
        and sdim_frame_verdict == "PASS"
    )
    if not eligibility_passed:
        qualification = "INELIGIBLE"
        efficiency = "INELIGIBLE"
    elif differential_verdict == "AGREE" and anchor_verdict == "PASS":
        qualification = "BOUNDED_EXACT_SMALL_STATE_ACTION_ANCHORED"
        efficiency = (
            "ELIGIBLE_ONLY_IF_DIFFERENTIAL_ANCHOR_AND_SDIM_AGREEMENT"
        )
    else:
        qualification = "FAILED"
        efficiency = "INELIGIBLE"

    return {
        "differential_verdict": differential_verdict,
        "anchor_verdict": anchor_verdict,
        "sdim_frame_verdict": sdim_frame_verdict,
        "state_action_qualification_status": qualification,
        "efficiency_interpretation": efficiency,
    }
