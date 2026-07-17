#!/usr/bin/env python3
"""Neutral fixtures for the MPS-016 ours/Quimb/dense-SVD comparator."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Sequence

import numpy as np


FIXTURE_SCHEMA = "error_coupling_simulator.diagnostics.mps_three_leg_fixture.v1"
LEG_RESULT_SCHEMA = "error_coupling_simulator.diagnostics.mps_three_leg_result.v1"
DTYPE = "complex128"
QUBIT_ORDER = "site_0_most_significant_big_endian"
_SPLIT_SITES = ((3, 4), (2, 3), (1, 2), (0, 1), (1, 2), (2, 3), (3, 4))
_SPLIT_ROLES = (
    "forward_swap_split",
    "forward_swap_split",
    "forward_swap_split",
    "two_site_operator_split",
    "reverse_swap_split",
    "reverse_swap_split",
    "reverse_swap_split",
)


def canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_hash(payload: dict[str, Any], *, hash_field: str) -> str:
    unhashed = {key: value for key, value in payload.items() if key != hash_field}
    return hashlib.sha256(canonical_json_bytes(unhashed)).hexdigest()


def _complex_array_payload(values: np.ndarray | Sequence[complex]) -> dict[str, Any]:
    array = np.asarray(values, dtype=np.complex128)
    flat = array.reshape(-1)
    return {
        "dtype": DTYPE,
        "shape": list(array.shape),
        "real": [float(value) for value in flat.real],
        "imag": [float(value) for value in flat.imag],
    }


def _ordered_cnot() -> np.ndarray:
    return np.asarray(
        [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]],
        dtype=np.complex128,
    )


def _fixture(*, support: tuple[int, int], max_bond: int) -> dict[str, Any]:
    zero = np.asarray([1.0, 0.0], dtype=np.complex128)
    active = np.asarray([math.sqrt(3.0) / 2.0, 0.5j], dtype=np.complex128)
    factors = [zero.copy() for _ in range(5)]
    factors[support[0]] = active
    support_slug = "_".join(str(site) for site in support)
    return {
        "fixture_id": f"ordered_cnot_{support_slug}_cap{max_bond}",
        "num_sites": 5,
        "local_dimension": 2,
        "support": list(support),
        "max_bond": int(max_bond),
        "cutoff": 0.0,
        "cutoff_mode": "rsum2",
        "renorm": None,
        "initial_product_factors": [
            _complex_array_payload(factor) for factor in factors
        ],
        "two_site_operator": _complex_array_payload(_ordered_cnot()),
        "expected_split_path": {
            "split_sites": [list(pair) for pair in _SPLIT_SITES],
            "roles": list(_SPLIT_ROLES),
            "operator_gate_leg_sites": (
                [0, 1] if support == (0, 4) else [1, 0]
            ),
        },
    }


def build_fixture_manifest() -> dict[str, Any]:
    fixtures = [
        _fixture(support=support, max_bond=max_bond)
        for support in ((0, 4), (4, 0))
        for max_bond in (1, 2, 4)
    ]
    manifest = {
        "schema": FIXTURE_SCHEMA,
        "dtype": DTYPE,
        "qubit_order": QUBIT_ORDER,
        "fixture_count": len(fixtures),
        "fixtures": fixtures,
    }
    manifest["content_hash_sha256"] = canonical_hash(
        manifest,
        hash_field="content_hash_sha256",
    )
    return manifest


def _complex_array_from_payload(payload: dict[str, Any]) -> np.ndarray:
    if payload.get("dtype") != DTYPE:
        raise ValueError(f"complex array dtype must be {DTYPE!r}")
    shape = payload.get("shape")
    real = payload.get("real")
    imag = payload.get("imag")
    if not isinstance(shape, list) or not isinstance(real, list) or not isinstance(
        imag, list
    ):
        raise ValueError("complex array payload is malformed")
    if len(real) != math.prod(shape) or len(imag) != math.prod(shape):
        raise ValueError("complex array payload length does not match shape")
    values = np.asarray(real, dtype=np.float64) + 1j * np.asarray(
        imag, dtype=np.float64
    )
    if not np.all(np.isfinite(values)):
        raise ValueError("complex array payload contains nonfinite values")
    return values.astype(np.complex128, copy=False).reshape(shape)


def _product_dense(factors: Sequence[np.ndarray]) -> np.ndarray:
    state = np.asarray([1.0 + 0.0j], dtype=np.complex128)
    for factor in factors:
        state = np.kron(state, np.asarray(factor, dtype=np.complex128))
    return state


def _apply_two_site_dense(
    state: np.ndarray,
    operator: np.ndarray,
    *,
    support: tuple[int, int],
    num_sites: int,
) -> np.ndarray:
    if len(set(support)) != 2:
        raise ValueError("ordered support must contain two distinct sites")
    rest = tuple(site for site in range(num_sites) if site not in support)
    permutation = support + rest
    inverse = np.argsort(permutation)
    front = np.transpose(
        np.asarray(state, dtype=np.complex128).reshape((2,) * num_sites),
        permutation,
    ).reshape(4, -1)
    acted = (np.asarray(operator, dtype=np.complex128) @ front).reshape(
        (2, 2) + (2,) * len(rest)
    )
    return np.transpose(acted, inverse).reshape(-1)


def _normalized(state: np.ndarray) -> tuple[np.ndarray, float]:
    values = np.asarray(state, dtype=np.complex128).reshape(-1)
    norm_sq = float(np.vdot(values, values).real)
    if not math.isfinite(norm_sq) or norm_sq <= 0.0:
        raise ValueError("state must have finite positive norm")
    return values / math.sqrt(norm_sq), norm_sq


def _state_fidelity(reference: np.ndarray, candidate: np.ndarray) -> float:
    ref, _ = _normalized(reference)
    got, _ = _normalized(candidate)
    return float(abs(np.vdot(ref, got)) ** 2)


def _phase_aligned_l2(reference: np.ndarray, candidate: np.ndarray) -> float:
    ref, _ = _normalized(reference)
    got, _ = _normalized(candidate)
    overlap = np.vdot(ref, got)
    phase = 1.0 + 0.0j if abs(overlap) == 0.0 else overlap / abs(overlap)
    return float(np.linalg.norm(ref - got / phase))


def _schmidt_records(
    state: np.ndarray,
    *,
    num_sites: int,
    max_bond: int,
) -> list[dict[str, Any]]:
    normalized, _ = _normalized(state)
    records: list[dict[str, Any]] = []
    for cut in range(1, num_sites):
        singular_values = np.linalg.svd(
            normalized.reshape(2**cut, 2 ** (num_sites - cut)),
            compute_uv=False,
        )
        weights = np.square(np.abs(singular_values))
        kept = min(int(max_bond), int(weights.size))
        records.append(
            {
                "cut_index": cut,
                "singular_values": [float(value) for value in singular_values],
                "numerical_rank": int(np.count_nonzero(singular_values > 1.0e-12)),
                "discarded_weight_at_cap": float(math.fsum(weights[kept:])),
                "dense_cut_tail_is_actual_split_ledger": False,
            }
        )
    return records


def _dense_case(fixture: dict[str, Any]) -> dict[str, Any]:
    factors = [
        _complex_array_from_payload(payload)
        for payload in fixture["initial_product_factors"]
    ]
    initial = _product_dense(factors)
    operator = _complex_array_from_payload(fixture["two_site_operator"])
    target = _apply_two_site_dense(
        initial,
        operator,
        support=tuple(fixture["support"]),
        num_sites=int(fixture["num_sites"]),
    )
    normalized, norm_sq = _normalized(target)
    schmidt = _schmidt_records(
        target,
        num_sites=int(fixture["num_sites"]),
        max_bond=int(fixture["max_bond"]),
    )
    best_rank_cap_fidelity = min(
        1.0 - float(record["discarded_weight_at_cap"]) for record in schmidt
    )
    return {
        "fixture_id": fixture["fixture_id"],
        "fixture_sha256": hashlib.sha256(
            canonical_json_bytes(fixture)
        ).hexdigest(),
        "support": list(fixture["support"]),
        "max_bond": int(fixture["max_bond"]),
        "dense_reference": {
            "method": "explicit_big_endian_axis_permutation_and_numpy_svd",
            "raw_norm_sq": norm_sq,
            "normalized_state": _complex_array_payload(normalized),
            "numerical_schmidt_rank": max(
                int(record["numerical_rank"]) for record in schmidt
            ),
            "schmidt_records": schmidt,
            "best_rank_cap_fidelity": best_rank_cap_fidelity,
        },
    }


def _dense_corruption_falsifiers(manifest: dict[str, Any]) -> dict[str, Any]:
    fixture = next(
        case
        for case in manifest["fixtures"]
        if case["support"] == [4, 0] and case["max_bond"] == 4
    )
    factors = [
        _complex_array_from_payload(payload)
        for payload in fixture["initial_product_factors"]
    ]
    initial = _product_dense(factors)
    operator = _complex_array_from_payload(fixture["two_site_operator"])
    correct = _apply_two_site_dense(
        initial,
        operator,
        support=(4, 0),
        num_sites=5,
    )
    sorted_support = _apply_two_site_dense(
        initial,
        operator,
        support=(0, 4),
        num_sites=5,
    )

    phase_corrupted_factors = [factor.copy() for factor in factors]
    phase_corrupted_factors[4][1] *= -1.0
    phase_corrupted = _apply_two_site_dense(
        _product_dense(phase_corrupted_factors),
        operator,
        support=(4, 0),
        num_sites=5,
    )
    globally_phased = np.exp(0.37j) * correct

    sorted_fidelity = _state_fidelity(correct, sorted_support)
    phase_fidelity = _state_fidelity(correct, phase_corrupted)
    global_fidelity = _state_fidelity(correct, globally_phased)
    global_l2 = _phase_aligned_l2(correct, globally_phased)
    return {
        "reversed_support_sorted_fidelity": sorted_fidelity,
        "relative_phase_sign_fidelity": phase_fidelity,
        "global_phase_fidelity": global_fidelity,
        "global_phase_aligned_l2": global_l2,
        "all_required_corruptions_detected": bool(
            sorted_fidelity < 0.99
            and phase_fidelity < 0.99
            and abs(global_fidelity - 1.0) <= 1.0e-14
            and global_l2 <= 1.0e-14
        ),
    }


def run_dense_leg(manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest.get("schema") != FIXTURE_SCHEMA:
        raise ValueError("fixture schema mismatch")
    if manifest.get("content_hash_sha256") != canonical_hash(
        manifest,
        hash_field="content_hash_sha256",
    ):
        raise ValueError("fixture manifest content hash mismatch")
    cases = [_dense_case(fixture) for fixture in manifest["fixtures"]]
    result = {
        "schema": LEG_RESULT_SCHEMA,
        "leg": "dense_numpy",
        "fixture_manifest_sha256": manifest["content_hash_sha256"],
        "case_count": len(cases),
        "cases": cases,
        "corruption_falsifiers": _dense_corruption_falsifiers(manifest),
        "claim_boundary": {
            "state_math_oracle": True,
            "actual_split_ledger_oracle": False,
            "dense_cut_tail_is_actual_split_ledger": False,
            "production_error_bound": False,
            "record_faithfulness": False,
        },
    }
    result["content_hash_sha256"] = canonical_hash(
        result,
        hash_field="content_hash_sha256",
    )
    return result
