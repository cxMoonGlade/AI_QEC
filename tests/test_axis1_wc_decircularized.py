"""Step-4 (W-C) regression + GPU cert — the two-site leakage cert is DE-CIRCULARIZED.

The shipped cert was CIRCULAR (round-1 W-C, all 4 models): it imported ``_hamiltonian_group_gates``
from the carrier under test and built its "independent" oracle from the carrier's byte-equal level
dict, so a SHARED wrong physics map (e.g. a transposed/wrong level pair) was mirrored on both sides
and passed with diff 0 — certifying nothing about the physics map (FAITHFULNESS rule I violation).

The fix (``axis1_qutrit_leakage_certification``): the reference is HAND-TYPED from the literature
(Wood-Gambetta 1704.03081 / Varbanov 2002.07119 / Miao 2211.04728), the carrier side imports ONLY
``_hamiltonian_matrix_for_term`` (the operator under test), and ``_hamiltonian_group_gates`` /
``_TWO_SITE_LEAKAGE_HAMILTONIAN_LEVELS`` appear nowhere in the cert's executable code.

THE C2 FALSIFIER (``test_wc_cert_catches_corrupted_carrier_level_map``): corrupt the carrier's level
dict (|11><02| -> |10><02|). The DE-CIRCULARIZED cert CATCHES it (hand-typed ref disagrees, fail),
and we show the old circular reference (derived from the SAME corrupted dict) would mirror the
corruption to diff 0 — i.e. would FALSE-PASS. This is the test the old cert fails and the fix passes.

GPU-only (memory rule) — collection FAILS without CUDA.
Run:  conda run -n aiqec python -m pytest -q tests/test_axis1_wc_decircularized.py
"""
from __future__ import annotations

import inspect

import pytest
import torch

cuda_ok = torch.cuda.is_available()
if not cuda_ok:
    pytest.fail(
        "W-C de-circularization cert is GPU-gated; CUDA-MISSING is NOT A RELEASE BASIS",
        pytrace=False,
    )

import qec_twin.simulator.axis1_mcwf_mps_execution as carrier_mod  # noqa: E402
import qec_twin.simulator.axis1_qutrit_leakage_certification as cert_mod  # noqa: E402

DEV = "cuda"


def _make_term(family: str, coeff: float) -> dict:
    return {
        "kind": "hamiltonian",
        "operator_family": family,
        "support": [0, 1],
        "coefficient": float(coeff),
        "substep_id": "wc_cert",
    }


def test_wc_cert_does_not_import_carrier_grouping_or_level_dict():
    """Structural (namespace, robust): the de-circularized cert imports the carrier per-term
    operator builder (the object under test) but NOT the carrier GROUPING path
    (``_hamiltonian_group_gates``) nor the carrier level dict
    (``_TWO_SITE_LEAKAGE_HAMILTONIAN_LEVELS``) — those are the circular surfaces it removed."""
    assert hasattr(cert_mod, "_hamiltonian_matrix_for_term")  # the operator under test (allowed)
    assert not hasattr(cert_mod, "_hamiltonian_group_gates"), "cert must NOT import the grouping path"
    assert not hasattr(cert_mod, "_TWO_SITE_LEAKAGE_HAMILTONIAN_LEVELS"), "cert must NOT import the carrier level dict"


def test_wc_cert_catches_corrupted_carrier_level_map(monkeypatch):
    """C2: a corrupted carrier physics map is CAUGHT by the de-circularized cert (the old
    circular cert would have mirrored it and false-passed)."""
    family = "LEAK_EXCHANGE_11_02"
    base = cert_mod._certify_leakage_family_operator(
        _make_term(family, 0.137),
        dims=(3, 3),
        dt_ns=17.0,
        wrong_physics_control_min=cert_mod._WRONG_PHYSICS_CONTROL_MIN,
        independent_reference_diff_gate=cert_mod._INDEPENDENT_REFERENCE_DIFF_GATE,
        device=DEV,
    )
    assert base["passed"] is True  # faithful carrier matches the hand-typed reference

    # Corrupt ONLY the carrier dict (a shared-wrong-physics map): |11><02| -> |10><02|.
    good = dict(carrier_mod._TWO_SITE_LEAKAGE_HAMILTONIAN_LEVELS)
    corrupted = dict(good)
    corrupted[family] = ((1, 0), (0, 2))
    monkeypatch.setattr(
        carrier_mod, "_TWO_SITE_LEAKAGE_HAMILTONIAN_LEVELS", corrupted, raising=True
    )
    bad = cert_mod._certify_leakage_family_operator(
        _make_term(family, 0.137),
        dims=(3, 3),
        dt_ns=17.0,
        wrong_physics_control_min=cert_mod._WRONG_PHYSICS_CONTROL_MIN,
        independent_reference_diff_gate=cert_mod._INDEPENDENT_REFERENCE_DIFF_GATE,
        device=DEV,
    )
    # the independent hand-typed reference CATCHES the corruption (the round-1 blind spot).
    assert bad["generator_matches_reference"] is False, bad
    assert bad["max_abs_generator_diff"] >= 1e-3, bad
    assert bad["passed"] is False, bad

    # PROOF the shipped circular path would FALSE-PASS: a reference derived FROM the corrupted
    # carrier dict mirrors the corruption -> diff 0.
    left, right = corrupted[family]
    d1 = 3
    shared_ref = torch.zeros((9, 9), dtype=torch.complex128, device=DEV)
    li, ri = left[0] * d1 + left[1], right[0] * d1 + right[1]
    shared_ref[li, ri] = 0.137
    shared_ref[ri, li] = 0.137
    carrier_h = carrier_mod._hamiltonian_matrix_for_term(
        _make_term(family, 0.137), support=(0, 1), local_dims=(3, 3), device=DEV
    )
    assert float(torch.max(torch.abs(carrier_h - shared_ref)).item()) <= 1e-12
