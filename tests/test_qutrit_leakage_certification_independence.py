"""Independent-reference checks for two-site qutrit leakage certification.

The certification path may call the carrier operator being certified, but its
reference level pairs must remain hand-typed and independent of the carrier's
private level map.  The corruption test below changes only that carrier map and
requires the certification result to fail.
"""

from __future__ import annotations

import pytest
import torch

import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as carrier
import error_coupling_simulator.frontend.axis1_qutrit_leakage_certification as certification


pytestmark = pytest.mark.skipif(
    not torch.cuda.is_available(),
    reason="two-site qutrit leakage operator certification requires CUDA",
)

DEVICE = "cuda"


def _transport_term(family: str, coefficient: float) -> dict:
    return {
        "kind": "hamiltonian",
        "operator_family": family,
        "support": [0, 1],
        "coefficient": float(coefficient),
        "substep_id": "independent_reference_probe",
    }


def _certify(term: dict) -> dict:
    return certification._certify_leakage_family_operator(
        term,
        dims=(3, 3),
        dt_ns=17.0,
        wrong_physics_control_min=certification._WRONG_PHYSICS_CONTROL_MIN,
        independent_reference_diff_gate=(
            certification._INDEPENDENT_REFERENCE_DIFF_GATE
        ),
        device=DEVICE,
    )


def test_reference_namespace_does_not_capture_carrier_grouping_or_level_map():
    """Only the per-term carrier operator is shared with certification."""
    assert certification._hamiltonian_matrix_for_term is carrier._hamiltonian_matrix_for_term
    assert not hasattr(certification, "_hamiltonian_group_gates")
    assert not hasattr(certification, "_TWO_SITE_LEAKAGE_HAMILTONIAN_LEVELS")


def test_carrier_level_map_corruption_is_detected(monkeypatch):
    """A shared carrier/reference level-map error must not certify itself."""
    family = "LEAK_EXCHANGE_11_02"
    coefficient = 0.137
    term = _transport_term(family, coefficient)

    baseline = _certify(term)
    assert baseline["passed"] is True

    corrupted = dict(carrier._TWO_SITE_LEAKAGE_HAMILTONIAN_LEVELS)
    corrupted[family] = ((1, 0), (0, 2))
    monkeypatch.setattr(
        carrier,
        "_TWO_SITE_LEAKAGE_HAMILTONIAN_LEVELS",
        corrupted,
        raising=True,
    )

    result = _certify(term)
    assert result["generator_matches_reference"] is False, result
    assert result["max_abs_generator_diff"] >= 1.0e-3, result
    assert result["passed"] is False, result

    # A reference reconstructed from the corrupted carrier map would mirror the
    # same error exactly.  Demonstrating that false agreement gives the
    # corruption check a concrete counterexample rather than a structural claim.
    left, right = corrupted[family]
    shared_reference = torch.zeros(
        (9, 9), dtype=torch.complex128, device=DEVICE
    )
    left_index = left[0] * 3 + left[1]
    right_index = right[0] * 3 + right[1]
    shared_reference[left_index, right_index] = coefficient
    shared_reference[right_index, left_index] = coefficient
    carrier_operator = carrier._hamiltonian_matrix_for_term(
        term,
        support=(0, 1),
        local_dims=(3, 3),
        device=DEVICE,
    )
    assert float(torch.max(torch.abs(carrier_operator - shared_reference)).item()) <= 1.0e-12
