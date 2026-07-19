#!/usr/bin/env python3
"""Neutral fixtures for the MPS-016 ours/Quimb/dense-SVD comparator."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
from typing import Any, Sequence

import numpy as np


FIXTURE_SCHEMA = "error_coupling_simulator.diagnostics.mps_three_leg_fixture.v1"
LEG_RESULT_SCHEMA = "error_coupling_simulator.diagnostics.mps_three_leg_result.v2"
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


def atomic_write_json(path: Path, payload: dict[str, Any]) -> str:
    """Write one strict JSON artifact atomically and return its exact-byte hash."""

    output = Path(path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    encoded = (
        json.dumps(payload, allow_nan=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.name}.",
        dir=output.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    return hashlib.sha256(encoded).hexdigest()


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


THREE_LEG_RESULT_SCHEMA = (
    "error_coupling_simulator.diagnostics.mps_three_leg_gate.v2"
)
_COMPARISON_ATOL = 1.0e-12
_FINE_CORRUPTION = 1.0e-8


def _validate_fixture_manifest(manifest: dict[str, Any]) -> None:
    if manifest.get("schema") != FIXTURE_SCHEMA:
        raise ValueError("fixture schema mismatch")
    if manifest.get("content_hash_sha256") != canonical_hash(
        manifest,
        hash_field="content_hash_sha256",
    ):
        raise ValueError("fixture manifest content hash mismatch")


def _fixture_arrays(
    fixture: dict[str, Any],
) -> tuple[list[np.ndarray], np.ndarray, tuple[int, int], int]:
    factors = [
        _complex_array_from_payload(payload)
        for payload in fixture["initial_product_factors"]
    ]
    operator = _complex_array_from_payload(fixture["two_site_operator"])
    support = tuple(int(site) for site in fixture["support"])
    if len(support) != 2:
        raise ValueError("fixture support must contain two sites")
    return factors, operator, support, int(fixture["max_bond"])


def _fixture_mps(factors: Sequence[np.ndarray]):
    import quimb.tensor as qtn
    import torch

    tensors = [
        torch.as_tensor(factor, dtype=torch.complex128, device="cpu")
        for factor in factors
    ]
    return qtn.MPS_product_state(tensors)


def _mps_dense(mps: Any) -> np.ndarray:
    values = mps.to_dense()
    if hasattr(values, "detach"):
        values = values.detach().cpu().numpy()
    return np.asarray(values, dtype=np.complex128).reshape(-1)


def _state_summary(state: np.ndarray) -> dict[str, Any]:
    normalized, norm_sq = _normalized(state)
    return {
        "representation": "normalized_amplitudes_plus_raw_norm_sq",
        "raw_norm_sq": float(norm_sq),
        "normalized_state": _complex_array_payload(normalized),
    }


def _ours_case(fixture: dict[str, Any]) -> dict[str, Any]:
    import torch

    from error_coupling_simulator.carrier.mps.capped_two_site import (
        apply_capped_two_site_unitary,
    )

    factors, operator, support, max_bond = _fixture_arrays(fixture)
    fixture_sha256 = hashlib.sha256(canonical_json_bytes(fixture)).hexdigest()
    candidate, event = apply_capped_two_site_unitary(
        _fixture_mps(factors),
        torch.as_tensor(operator, dtype=torch.complex128, device="cpu"),
        support=support,
        max_bond=max_bond,
        context={
            "comparator_fixture_id": str(fixture["fixture_id"]),
            "comparator_fixture_sha256": fixture_sha256,
        },
    )
    return {
        "fixture_id": fixture["fixture_id"],
        "fixture_sha256": fixture_sha256,
        "support": list(support),
        "max_bond": max_bond,
        "candidate_state": _state_summary(_mps_dense(candidate)),
        "actual_split_event": event,
    }


def run_ours_leg(manifest: dict[str, Any]) -> dict[str, Any]:
    """Run the editable-package actual-split adapter on every frozen fixture."""

    _validate_fixture_manifest(manifest)
    cases = [_ours_case(fixture) for fixture in manifest["fixtures"]]
    result = {
        "schema": LEG_RESULT_SCHEMA,
        "leg": "repository_actual_split",
        "fixture_manifest_sha256": manifest["content_hash_sha256"],
        "case_count": len(cases),
        "cases": cases,
        "claim_boundary": {
            "repository_implementation_under_test": True,
            "state_math_oracle": False,
            "actual_split_ledger_source": True,
            "actual_split_ledger_is_global_error_bound": False,
            "production_error_bound": False,
            "record_faithfulness": False,
        },
    }
    result["content_hash_sha256"] = canonical_hash(
        result,
        hash_field="content_hash_sha256",
    )
    return result


def _quimb_case(fixture: dict[str, Any]) -> dict[str, Any]:
    import quimb
    import torch

    factors, operator, support, max_bond = _fixture_arrays(fixture)
    mps = _fixture_mps(factors)
    info: dict[str, Any] = {"cur_orthog": "calc"}
    mps.gate_(
        torch.as_tensor(operator, dtype=torch.complex128, device="cpu"),
        where=support,
        contract="swap+split",
        method="svd",
        max_bond=max_bond,
        cutoff=0.0,
        cutoff_mode="rsum2",
        renorm=None,
        info=info,
    )
    center = info.get("cur_orthog")
    return {
        "fixture_id": fixture["fixture_id"],
        "fixture_sha256": hashlib.sha256(
            canonical_json_bytes(fixture)
        ).hexdigest(),
        "support": list(support),
        "max_bond": max_bond,
        "candidate_state": _state_summary(_mps_dense(mps)),
        "public_call": {
            "library": "quimb",
            "version": str(quimb.__version__),
            "api": "MatrixProductState.gate_",
            "contract": "swap+split",
            "method": "svd",
            "max_bond": max_bond,
            "cutoff": 0.0,
            "cutoff_mode": "rsum2",
            "renorm": None,
            "ordered_where": list(support),
            "orthogonality_center_after": (
                None if center is None else list(center)
            ),
        },
        "actual_split_ledger": None,
    }


def run_quimb_wiring_leg(manifest: dict[str, Any]) -> dict[str, Any]:
    """Run pinned Quimb's public MPS wiring; this is not an independent oracle."""

    _validate_fixture_manifest(manifest)
    cases = [_quimb_case(fixture) for fixture in manifest["fixtures"]]
    result = {
        "schema": LEG_RESULT_SCHEMA,
        "leg": "quimb_public_wiring",
        "fixture_manifest_sha256": manifest["content_hash_sha256"],
        "case_count": len(cases),
        "cases": cases,
        "claim_boundary": {
            "wiring_only": True,
            "same_pinned_backend_as_repository_adapter": True,
            "independent_scientific_oracle": False,
            "state_math_oracle": False,
            "actual_split_ledger_source": False,
            "production_error_bound": False,
            "record_faithfulness": False,
        },
    }
    result["content_hash_sha256"] = canonical_hash(
        result,
        hash_field="content_hash_sha256",
    )
    return result


def _close(left: float, right: float) -> bool:
    return bool(
        math.isfinite(float(left))
        and math.isfinite(float(right))
        and math.isclose(
            float(left),
            float(right),
            rel_tol=_COMPARISON_ATOL,
            abs_tol=_COMPARISON_ATOL,
        )
    )


def _validate_actual_split_case(
    fixture: dict[str, Any],
    case: dict[str, Any],
) -> list[str]:
    """Reconcile one returned state with every fine-grained ledger identity."""

    errors: list[str] = []
    event = case["actual_split_event"]
    expected = fixture["expected_split_path"]
    records = event["split_records"]
    support = [int(site) for site in fixture["support"]]
    max_bond = int(fixture["max_bond"])

    if case["support"] != support or event["support"] != support:
        errors.append("ordered_support_mismatch")
    if int(case["max_bond"]) != max_bond or int(event["max_bond"]) != max_bond:
        errors.append("max_bond_mismatch")
    if event["gate_leg_sites"] != expected["operator_gate_leg_sites"]:
        errors.append("operator_gate_leg_order_mismatch")
    if int(event["split_count"]) != len(records):
        errors.append("split_count_vs_records_mismatch")
    if len(records) != len(expected["split_sites"]):
        errors.append("split_count_vs_expected_path_mismatch")

    raw_weights: list[float] = []
    fractions: list[float] = []
    for index, (record, expected_sites, expected_role) in enumerate(
        zip(
            records,
            expected["split_sites"],
            expected["roles"],
            strict=True,
        )
    ):
        if int(record["sequence_index"]) != index:
            errors.append(f"split_{index}_sequence_index_mismatch")
        if record["split_sites"] != expected_sites:
            errors.append(f"split_{index}_topology_mismatch")
        if record["path_role"] != expected_role:
            errors.append(f"split_{index}_role_mismatch")
        expected_gate_legs = (
            expected["operator_gate_leg_sites"]
            if expected_role == "two_site_operator_split"
            else None
        )
        if record["gate_leg_sites"] != expected_gate_legs:
            errors.append(f"split_{index}_gate_leg_mismatch")
        if int(record["requested_max_bond"]) != max_bond:
            errors.append(f"split_{index}_max_bond_mismatch")
        if (
            record["requested_method"] != "svd"
            or float(record["requested_cutoff"]) != 0.0
            or record["requested_cutoff_mode"] != "rsum2"
            or record["requested_renorm"] is not None
        ):
            errors.append(f"split_{index}_decomposition_policy_mismatch")
        kept_bond_dimension = int(record["actual_kept_bond_dimension"])
        if not 1 <= kept_bond_dimension <= max_bond:
            errors.append(f"split_{index}_kept_bond_dimension_out_of_bounds")

        pre_weight = float(record["pre_split_total_weight"])
        raw_weight = float(record["actual_discarded_weight_raw"])
        fraction = float(
            record["actual_discarded_weight_fraction_of_pre_split"]
        )
        if not math.isfinite(pre_weight) or pre_weight <= 0.0:
            errors.append(f"split_{index}_invalid_pre_split_weight")
        if not math.isfinite(raw_weight) or raw_weight < 0.0:
            errors.append(f"split_{index}_invalid_discarded_weight")
        if not math.isfinite(fraction) or fraction < 0.0:
            errors.append(f"split_{index}_invalid_discarded_fraction")
        if pre_weight > 0.0 and not _close(fraction, raw_weight / pre_weight):
            errors.append(f"split_{index}_fraction_reconciliation_mismatch")
        raw_weights.append(raw_weight)
        fractions.append(fraction)

    raw_sum = float(math.fsum(raw_weights))
    fraction_sum = float(math.fsum(fractions))
    if not _close(raw_sum, event["actual_discarded_weight_raw_sum"]):
        errors.append("split_raw_sum_reconciliation_mismatch")
    if not _close(
        fraction_sum,
        event["actual_discarded_weight_fraction_sum"],
    ):
        errors.append("split_fraction_sum_reconciliation_mismatch")
    if not _close(
        max(fractions, default=0.0),
        event["worst_actual_discarded_weight_fraction"],
    ):
        errors.append("worst_split_fraction_reconciliation_mismatch")

    input_norm = float(event["input_norm_sq"])
    raw_output_norm = float(event["raw_output_norm_sq"])
    restored_norm = float(event["restored_output_norm_sq"])
    restore_factor = float(event["deterministic_norm_restore_factor"])
    norm_loss = float(event["unitary_truncation_mass_loss"])
    if not _close(norm_loss, max(0.0, input_norm - raw_output_norm)):
        errors.append("unitary_norm_loss_reconciliation_mismatch")
    if not _close(raw_sum, norm_loss):
        errors.append("ledger_raw_sum_vs_norm_loss_mismatch")
    if not _close(
        raw_output_norm * restore_factor * restore_factor,
        restored_norm,
    ):
        errors.append("norm_restore_factor_reconciliation_mismatch")
    if not _close(
        case["candidate_state"]["raw_norm_sq"],
        restored_norm,
    ):
        errors.append("candidate_state_norm_vs_event_mismatch")

    normalized_state = _complex_array_from_payload(
        case["candidate_state"]["normalized_state"]
    )
    normalized_norm = float(
        np.vdot(normalized_state.reshape(-1), normalized_state.reshape(-1)).real
    )
    if not _close(normalized_norm, 1.0):
        errors.append("serialized_normalized_state_norm_mismatch")
    if event["physical_branch_probability"] is not None:
        errors.append("unitary_ledger_claims_physical_branch_probability")
    if event["not_a_global_error_bound"] is not True:
        errors.append("ledger_global_error_boundary_missing")
    return errors


def _cases_by_fixture(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    cases = result["cases"]
    mapped = {str(case["fixture_id"]): case for case in cases}
    if len(mapped) != len(cases):
        raise ValueError("leg result contains duplicate fixture ids")
    return mapped


def _comparison_case(
    fixture: dict[str, Any],
    dense_case: dict[str, Any],
    ours_case: dict[str, Any],
    quimb_case: dict[str, Any],
) -> dict[str, Any]:
    dense_reference = dense_case["dense_reference"]
    dense_state = _complex_array_from_payload(dense_reference["normalized_state"])
    ours_state = _complex_array_from_payload(
        ours_case["candidate_state"]["normalized_state"]
    )
    quimb_state = _complex_array_from_payload(
        quimb_case["candidate_state"]["normalized_state"]
    )
    ours_vs_dense = _state_fidelity(dense_state, ours_state)
    quimb_vs_dense = _state_fidelity(dense_state, quimb_state)
    ours_vs_quimb = _state_fidelity(ours_state, quimb_state)
    ours_dense_l2 = _phase_aligned_l2(dense_state, ours_state)
    quimb_dense_l2 = _phase_aligned_l2(dense_state, quimb_state)
    max_bond = int(fixture["max_bond"])
    numerical_rank = int(dense_reference["numerical_schmidt_rank"])
    high_cap = max_bond >= numerical_rank
    expected_fidelity = float(dense_reference["best_rank_cap_fidelity"])
    event = ours_case["actual_split_event"]
    ours_returned_norm = float(ours_case["candidate_state"]["raw_norm_sq"])
    ours_pre_restore_norm = float(event["raw_output_norm_sq"])
    quimb_raw_norm = float(quimb_case["candidate_state"]["raw_norm_sq"])

    common_pass = bool(
        _close(ours_vs_quimb, 1.0)
        and _close(ours_returned_norm, 1.0)
        and _close(ours_pre_restore_norm, quimb_raw_norm)
        and not _validate_actual_split_case(fixture, ours_case)
    )
    if high_cap:
        behavior = "high_cap_exact_state"
        behavior_passed = bool(
            common_pass
            and _close(ours_vs_dense, 1.0)
            and _close(quimb_vs_dense, 1.0)
            and _close(ours_pre_restore_norm, 1.0)
            and _close(event["actual_discarded_weight_raw_sum"], 0.0)
        )
    else:
        behavior = "bounded_cap_expected_rank_one_projection"
        behavior_passed = bool(
            common_pass
            and _close(ours_vs_dense, expected_fidelity)
            and _close(quimb_vs_dense, expected_fidelity)
            and _close(ours_pre_restore_norm, expected_fidelity)
            and _close(quimb_raw_norm, expected_fidelity)
            and _close(
                event["actual_discarded_weight_raw_sum"],
                1.0 - expected_fidelity,
            )
        )
    return {
        "fixture_id": fixture["fixture_id"],
        "support": list(fixture["support"]),
        "max_bond": max_bond,
        "dense_numerical_schmidt_rank": numerical_rank,
        "behavior_class": behavior,
        "expected_dense_rank_cap_fidelity": expected_fidelity,
        "ours_vs_dense_state_fidelity": ours_vs_dense,
        "quimb_vs_dense_state_fidelity": quimb_vs_dense,
        "ours_vs_quimb_state_fidelity": ours_vs_quimb,
        "ours_vs_dense_phase_aligned_l2": ours_dense_l2,
        "quimb_vs_dense_phase_aligned_l2": quimb_dense_l2,
        "ours_returned_norm_sq": ours_returned_norm,
        "ours_pre_restore_norm_sq": ours_pre_restore_norm,
        "quimb_raw_norm_sq": quimb_raw_norm,
        "actual_split_count": int(event["split_count"]),
        "dense_cut_tail_is_actual_split_ledger": False,
        "expected_behavior_passed": behavior_passed,
    }


def _swapped_topology_falsifier(
    manifest: dict[str, Any],
    dense: dict[str, Any],
) -> dict[str, Any]:
    fixture = next(
        row
        for row in manifest["fixtures"]
        if row["support"] == [4, 0] and int(row["max_bond"]) == 4
    )
    corrupted = json.loads(canonical_json_bytes(fixture))
    corrupted["support"] = [0, 4]
    dense_case = _cases_by_fixture(dense)[str(fixture["fixture_id"])]
    reference = _complex_array_from_payload(
        dense_case["dense_reference"]["normalized_state"]
    )
    ours_corrupted = _complex_array_from_payload(
        _ours_case(corrupted)["candidate_state"]["normalized_state"]
    )
    quimb_corrupted = _complex_array_from_payload(
        _quimb_case(corrupted)["candidate_state"]["normalized_state"]
    )
    ours_fidelity = _state_fidelity(reference, ours_corrupted)
    quimb_fidelity = _state_fidelity(reference, quimb_corrupted)
    return {
        "fixture_id": fixture["fixture_id"],
        "corruption": "ordered_support_silently_sorted",
        "correct_support": [4, 0],
        "corrupted_support": [0, 4],
        "repository_corrupted_state_fidelity": ours_fidelity,
        "quimb_corrupted_state_fidelity": quimb_fidelity,
        "detected": bool(ours_fidelity < 0.99 and quimb_fidelity < 0.99),
    }


def _reconciliation_corruption_falsifiers(
    manifest: dict[str, Any],
    ours: dict[str, Any],
) -> dict[str, Any]:
    fixture = next(
        row
        for row in manifest["fixtures"]
        if row["support"] == [0, 4] and int(row["max_bond"]) == 1
    )
    original = _cases_by_fixture(ours)[str(fixture["fixture_id"])]
    baseline_errors = _validate_actual_split_case(fixture, original)

    norm_corrupted = json.loads(canonical_json_bytes(original))
    norm_corrupted["candidate_state"]["raw_norm_sq"] += _FINE_CORRUPTION
    norm_errors = _validate_actual_split_case(fixture, norm_corrupted)

    ledger_corrupted = json.loads(canonical_json_bytes(original))
    ledger_corrupted["actual_split_event"]["split_records"][0][
        "actual_discarded_weight_raw"
    ] += _FINE_CORRUPTION
    ledger_errors = _validate_actual_split_case(fixture, ledger_corrupted)
    return {
        "fixture_id": fixture["fixture_id"],
        "fine_corruption_delta": _FINE_CORRUPTION,
        "baseline_errors": baseline_errors,
        "norm_corruption_errors": norm_errors,
        "ledger_corruption_errors": ledger_errors,
        "norm_corruption_detected": (
            "candidate_state_norm_vs_event_mismatch" in norm_errors
        ),
        "ledger_corruption_detected": bool(
            "split_raw_sum_reconciliation_mismatch" in ledger_errors
            and "ledger_raw_sum_vs_norm_loss_mismatch" in ledger_errors
        ),
    }


def run_three_leg_gate(manifest: dict[str, Any]) -> dict[str, Any]:
    """Compare dense math, repository actual splits, and Quimb wiring."""

    _validate_fixture_manifest(manifest)
    dense = run_dense_leg(manifest)
    ours = run_ours_leg(manifest)
    quimb = run_quimb_wiring_leg(manifest)
    dense_cases = _cases_by_fixture(dense)
    ours_cases = _cases_by_fixture(ours)
    quimb_cases = _cases_by_fixture(quimb)
    expected_ids = [str(row["fixture_id"]) for row in manifest["fixtures"]]
    if not (
        set(dense_cases) == set(ours_cases) == set(quimb_cases) == set(expected_ids)
    ):
        raise ValueError("three-leg fixture identity mismatch")
    comparisons = [
        _comparison_case(
            fixture,
            dense_cases[str(fixture["fixture_id"])],
            ours_cases[str(fixture["fixture_id"])],
            quimb_cases[str(fixture["fixture_id"])],
        )
        for fixture in manifest["fixtures"]
    ]
    swapped = _swapped_topology_falsifier(manifest, dense)
    reconciliation = _reconciliation_corruption_falsifiers(manifest, ours)
    passed = bool(
        all(row["expected_behavior_passed"] for row in comparisons)
        and dense["corruption_falsifiers"]["all_required_corruptions_detected"]
        and swapped["detected"]
        and not reconciliation["baseline_errors"]
        and reconciliation["norm_corruption_detected"]
        and reconciliation["ledger_corruption_detected"]
    )
    result = {
        "schema": THREE_LEG_RESULT_SCHEMA,
        "fixture_manifest_sha256": manifest["content_hash_sha256"],
        "passed": passed,
        "verdict": "pass" if passed else "fail",
        "legs": {
            "dense_numpy": dense,
            "repository_actual_split": ours,
            "quimb_public_wiring": quimb,
        },
        "comparisons": comparisons,
        "corruption_falsifiers": {
            "dense_reference": dense["corruption_falsifiers"],
            "swapped_topology": swapped,
            "fine_grained_norm_and_ledger": reconciliation,
        },
        "claim_boundary": {
            "independent_state_math_oracle": "dense_numpy",
            "actual_split_ledger_source": "repository_actual_split",
            "quimb_public_leg_role": (
                "wiring_only_same_dependency_not_independent_scientific_oracle"
            ),
            "dense_cut_tail_is_actual_split_ledger": False,
            "actual_split_ledger_is_global_error_bound": False,
            "production_error_bound": False,
            "record_faithfulness": False,
        },
    }
    result["content_hash_sha256"] = canonical_hash(
        result,
        hash_field="content_hash_sha256",
    )
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    result = run_three_leg_gate(build_fixture_manifest())
    if args.output is None:
        print(
            json.dumps(
                result,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
        )
    else:
        exact_byte_sha256 = atomic_write_json(args.output, result)
        print(
            "MPS three-leg comparator: "
            f"{'PASS' if result['passed'] else 'FAIL'}"
        )
        print(
            f"wrote {args.output.resolve()} "
            f"exact_byte_sha256={exact_byte_sha256}"
        )
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
