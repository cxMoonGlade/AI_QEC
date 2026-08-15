#!/usr/bin/env python3
"""NumPy-only exact anchor for the frozen GCAPEPS truncation bridge.

Preconditions
-------------
* NumPy is available and supplies IEEE-754 ``float64``/``complex128``.
* The formal confirmatory fixture is ``a=12/13``, ``b=5/13``, and
  ``theta=pi/5`` in the basis ``(|00>, |01>, |10>, |11>)`` with qubit 0 as
  the most-significant bit.
* This anchor is an untimed exact-small reference.  It must not be imported
  into, or counted as part of, a Quimb/GCAPEPS performance sample.

The module deliberately imports only the Python standard library and NumPy.
It does not import Quimb, Stim, SDIM, GCAPEPS, or
``error_coupling_simulator``.  Its command-line interface emits the formal
JSON payload to stdout; it never runs either candidate implementation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from typing import Any, Mapping

import numpy as np


ANCHOR_SCHEMA = (
    "error_coupling_simulator.external.gcapeps_forced_truncation_dense_anchor.v1"
)
FIXTURE_SCHEMA = (
    "error_coupling_simulator.external.gcapeps_native_forced_truncation_fixture.v1"
)

FORMAL_A = np.float64(12.0 / 13.0)
FORMAL_B = np.float64(5.0 / 13.0)
FORMAL_THETA = np.float64(np.pi / 5.0)
PILOT_A = np.float64(4.0 / 5.0)
PILOT_B = np.float64(3.0 / 5.0)
PILOT_THETA = np.float64(np.pi / 3.0)

EXACT_ABSOLUTE_BAND = 1.0e-12
FIDELITY_ROUNDOFF_BAND = 1.0e-12
K0_RELATIVE_CUTOFF = 0.4
K1_RELATIVE_CUTOFF = 0.5

_COMPLEX128 = np.dtype("complex128")
_FLOAT64 = np.dtype("float64")
_EXPECTED_ARRAY_SHAPES = {
    "input_state": (4,),
    "preparation_gate": (2, 2),
    "literal_cx": (4, 4),
    "rz": (2, 2),
    "u_zz_diagonal": (4,),
    "u_zz_operator": (4, 4),
    "compiled_operator": (4, 4),
    "first_cx_state": (4,),
    "first_cx_coefficient_matrix": (2, 2),
    "first_cx_cap1_state": (4,),
    "cap1_after_rz_state": (4,),
    "exact_vector": (4,),
    "cap_only_lossy_vector": (4,),
    "cutoff_inert_vector": (4,),
    "cutoff_only_lossy_vector": (4,),
    "direct_final_gate_control_vector": (4,),
    "final_exact_coefficient_matrix": (2, 2),
}


def _validated_real(value: Any, *, label: str) -> np.float64:
    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value,
        (int, float, np.integer, np.floating),
    ):
        raise TypeError(f"{label} must be a real numeric scalar")
    result = np.float64(value)
    if not np.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def _validated_fixture_parameters(
    *,
    a: Any,
    b: Any,
    theta: Any,
) -> tuple[np.float64, np.float64, np.float64]:
    a_value = _validated_real(a, label="a")
    b_value = _validated_real(b, label="b")
    theta_value = _validated_real(theta, label="theta")
    if not (a_value > b_value > np.float64(0.0)):
        raise ValueError("the anchor requires the nondegenerate order a > b > 0")
    normalization_residual = abs(
        float(a_value * a_value + b_value * b_value - np.float64(1.0))
    )
    if normalization_residual > EXACT_ABSOLUTE_BAND:
        raise ValueError("the anchor input coefficients must be normalized")
    return a_value, b_value, theta_value


def _as_c128(value: Any, *, shape: tuple[int, ...], label: str) -> np.ndarray:
    array = np.ascontiguousarray(np.asarray(value, dtype=np.complex128))
    if (
        array.shape != shape
        or array.dtype != _COMPLEX128
        or not array.flags.c_contiguous
        or not np.all(np.isfinite(array))
    ):
        raise ValueError(f"{label} is not a finite C-contiguous complex128 array")
    return array


def _literal_cx() -> np.ndarray:
    """Return the literal q0-control, q1-target CNOT in big-endian order."""

    return _as_c128(
        (
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 1.0, 0.0, 0.0),
            (0.0, 0.0, 0.0, 1.0),
            (0.0, 0.0, 1.0, 0.0),
        ),
        shape=(4, 4),
        label="literal CX",
    )


def _rz(theta: np.float64) -> np.ndarray:
    half = np.float64(theta / np.float64(2.0))
    return _as_c128(
        (
            (np.exp(np.complex128(-1.0j * half)), 0.0),
            (0.0, np.exp(np.complex128(1.0j * half))),
        ),
        shape=(2, 2),
        label="RZ",
    )


def _u_zz_diagonal(theta: np.float64) -> np.ndarray:
    half = np.float64(theta / np.float64(2.0))
    u = np.complex128(np.exp(np.complex128(-1.0j * half)))
    u_conjugate = np.complex128(np.conjugate(u))
    return _as_c128(
        (u, u_conjugate, u_conjugate, u),
        shape=(4,),
        label="U_ZZ diagonal",
    )


def _sha256_c128(array: np.ndarray) -> str:
    checked = np.asarray(array)
    if (
        checked.dtype != _COMPLEX128
        or not checked.flags.c_contiguous
        or not np.all(np.isfinite(checked))
    ):
        raise ValueError("only finite C-contiguous complex128 arrays can be sealed")
    little_endian = np.ascontiguousarray(checked, dtype="<c16")
    return hashlib.sha256(little_endian.tobytes(order="C")).hexdigest()


def _encode_complex_array(array: np.ndarray) -> dict[str, Any]:
    checked = np.asarray(array)
    if (
        checked.dtype != _COMPLEX128
        or not checked.flags.c_contiguous
        or not np.all(np.isfinite(checked))
    ):
        raise ValueError("encoded arrays must already be finite C-contiguous c128")
    flat = checked.reshape(-1)
    return {
        "dtype": "complex128",
        "shape": [int(axis) for axis in checked.shape],
        "order": "C",
        "values_real_imag": [[float(value.real), float(value.imag)] for value in flat],
        "sha256_little_endian_c_order": _sha256_c128(checked),
    }


def decode_complex_array(
    encoded: Mapping[str, Any],
    *,
    label: str = "encoded array",
) -> np.ndarray:
    """Decode one anchor array without dtype coercion ambiguity."""

    if not isinstance(encoded, Mapping):
        raise TypeError(f"{label} must be a mapping")
    if encoded.get("dtype") != "complex128" or encoded.get("order") != "C":
        raise ValueError(f"{label} dtype/order contract drifted")
    raw_shape = encoded.get("shape")
    raw_values = encoded.get("values_real_imag")
    if (
        not isinstance(raw_shape, list)
        or not raw_shape
        or any(
            isinstance(axis, bool) or not isinstance(axis, int) or axis <= 0
            for axis in raw_shape
        )
        or not isinstance(raw_values, list)
    ):
        raise ValueError(f"{label} shape/value encoding is invalid")
    size = math.prod(raw_shape)
    if len(raw_values) != size:
        raise ValueError(f"{label} encoded length does not match its shape")
    values = np.empty(size, dtype=np.complex128)
    for index, pair in enumerate(raw_values):
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError(f"{label} complex value {index} is malformed")
        real = _validated_real(pair[0], label=f"{label}[{index}].real")
        imag = _validated_real(pair[1], label=f"{label}[{index}].imag")
        values[index] = np.complex128(complex(float(real), float(imag)))
    result = np.ascontiguousarray(values.reshape(tuple(raw_shape)))
    digest = encoded.get("sha256_little_endian_c_order")
    if not isinstance(digest, str) or digest != _sha256_c128(result):
        raise ValueError(f"{label} content hash drifted")
    return result


def _validated_metric_vector(value: Any, *, label: str) -> np.ndarray:
    array = np.asarray(value)
    if (
        array.shape != (4,)
        or array.dtype != _COMPLEX128
        or not array.flags.c_contiguous
        or not np.all(np.isfinite(array))
    ):
        raise ValueError(
            f"{label} must already be a finite C-contiguous length-four c128 vector"
        )
    norm = float(np.linalg.norm(array))
    if not math.isfinite(norm) or norm <= 0.0:
        raise ValueError(f"{label} norm must be finite and strictly positive")
    return array


def evaluate_metrics(reference: Any, candidate: Any) -> dict[str, Any]:
    """Evaluate the preregistered complete-vector metrics independently."""

    reference_array = _validated_metric_vector(reference, label="reference")
    candidate_array = _validated_metric_vector(candidate, label="candidate")
    reference_norm = float(np.linalg.norm(reference_array))
    candidate_norm = float(np.linalg.norm(candidate_array))
    reference_mass = float(np.vdot(reference_array, reference_array).real)
    candidate_mass = float(np.vdot(candidate_array, candidate_array).real)
    if (
        not math.isfinite(reference_mass)
        or not math.isfinite(candidate_mass)
        or reference_mass <= 0.0
        or candidate_mass <= 0.0
    ):
        raise ValueError("metric state masses must be finite and strictly positive")

    difference = reference_array - candidate_array
    d_inf = float(np.max(np.abs(difference)))
    d_2 = float(np.linalg.norm(difference))
    d_rel = float(d_2 / reference_norm)
    d_norm = float(abs(reference_norm - candidate_norm) / reference_norm)

    overlap = np.vdot(reference_array, candidate_array)
    denominator = reference_mass * candidate_mass
    if not math.isfinite(denominator) or denominator <= 0.0:
        raise ValueError("fidelity denominator is invalid")
    fidelity_raw = float(abs(overlap) ** 2 / denominator)
    if not math.isfinite(fidelity_raw) or fidelity_raw < 0.0:
        raise ValueError("fidelity is nonfinite or negative")
    fidelity_roundoff_correction = max(0.0, fidelity_raw - 1.0)
    if fidelity_roundoff_correction > FIDELITY_ROUNDOFF_BAND:
        raise ValueError("fidelity exceeds one beyond the frozen roundoff band")
    fidelity = min(1.0, fidelity_raw)
    infidelity = max(0.0, 1.0 - fidelity)
    trace_distance = math.sqrt(infidelity)

    scalars = (
        reference_norm,
        candidate_norm,
        reference_mass,
        candidate_mass,
        d_inf,
        d_2,
        d_rel,
        d_norm,
        fidelity_raw,
        fidelity_roundoff_correction,
        fidelity,
        infidelity,
        trace_distance,
    )
    if not all(math.isfinite(value) for value in scalars):
        raise ValueError("a complete-vector metric is nonfinite")
    return {
        "reference_norm": reference_norm,
        "candidate_norm": candidate_norm,
        "reference_norm_squared": reference_mass,
        "candidate_norm_squared": candidate_mass,
        "d_inf": d_inf,
        "d_2": d_2,
        "d_rel": d_rel,
        "d_norm": d_norm,
        "fidelity_raw": fidelity_raw,
        "fidelity_roundoff_correction": fidelity_roundoff_correction,
        "fidelity": fidelity,
        "infidelity": infidelity,
        "normalized_pure_state_trace_distance": trace_distance,
        "phase_fit_performed": False,
        "normalization_performed": False,
        "dtype_cast_performed": False,
        "coordinate_permutation_performed": False,
    }


def _relative_cutoff_keep_count(
    singular_values: np.ndarray,
    *,
    cutoff: float,
) -> int:
    values = np.asarray(singular_values)
    if (
        values.shape != (2,)
        or values.dtype != _FLOAT64
        or not np.all(np.isfinite(values))
        or np.any(values < 0.0)
        or values[0] < values[1]
    ):
        raise ValueError("singular values must be ordered finite float64 values")
    cutoff_value = _validated_real(cutoff, label="relative cutoff")
    if cutoff_value < 0.0:
        raise ValueError("relative cutoff must be nonnegative")
    if cutoff_value == 0.0:
        return int(values.size)
    return max(1, int(np.count_nonzero(values > cutoff_value * values[0])))


def _construct_arrays(
    *,
    a: np.float64,
    b: np.float64,
    theta: np.float64,
) -> dict[str, np.ndarray]:
    preparation_gate = _as_c128(
        ((a, -b), (b, a)),
        shape=(2, 2),
        label="preparation gate",
    )
    input_state = _as_c128(
        (a, 0.0, b, 0.0),
        shape=(4,),
        label="input state",
    )
    cx = _literal_cx()
    rz = _rz(theta)
    identity = np.eye(2, dtype=np.complex128)
    lifted_rz = _as_c128(
        np.kron(identity, rz),
        shape=(4, 4),
        label="I tensor RZ",
    )
    u_zz_diagonal = _u_zz_diagonal(theta)
    u_zz_operator = _as_c128(
        np.diag(u_zz_diagonal),
        shape=(4, 4),
        label="U_ZZ operator",
    )
    compiled_operator = _as_c128(
        cx @ lifted_rz @ cx,
        shape=(4, 4),
        label="compiled operator",
    )

    first_cx_state = _as_c128(
        cx @ input_state,
        shape=(4,),
        label="first-CX state",
    )
    first_cx_coefficient_matrix = _as_c128(
        first_cx_state.reshape(2, 2),
        shape=(2, 2),
        label="first-CX coefficient matrix",
    )
    first_cx_cap1_state = _as_c128(
        (a, 0.0, 0.0, 0.0),
        shape=(4,),
        label="rank-one first-CX state",
    )
    cap1_after_rz_state = _as_c128(
        lifted_rz @ first_cx_cap1_state,
        shape=(4,),
        label="rank-one state after RZ",
    )
    cap_only_lossy_vector = _as_c128(
        cx @ cap1_after_rz_state,
        shape=(4,),
        label="cap-only lossy output",
    )
    exact_vector = _as_c128(
        u_zz_diagonal * input_state,
        shape=(4,),
        label="exact output",
    )

    analytic_singular_values = np.ascontiguousarray(
        np.asarray((a, b), dtype=np.float64)
    )
    k0_keep = _relative_cutoff_keep_count(
        analytic_singular_values,
        cutoff=K0_RELATIVE_CUTOFF,
    )
    k1_keep = _relative_cutoff_keep_count(
        analytic_singular_values,
        cutoff=K1_RELATIVE_CUTOFF,
    )
    cutoff_inert_vector = _as_c128(
        exact_vector if k0_keep == 2 else cap_only_lossy_vector,
        shape=(4,),
        label="K0 output",
    )
    cutoff_only_lossy_vector = _as_c128(
        exact_vector if k1_keep == 2 else cap_only_lossy_vector,
        shape=(4,),
        label="K1 output",
    )
    direct_final_gate_control_vector = _as_c128(
        u_zz_operator @ input_state,
        shape=(4,),
        label="direct final-gate control",
    )
    final_exact_coefficient_matrix = _as_c128(
        exact_vector.reshape(2, 2),
        shape=(2, 2),
        label="final exact coefficient matrix",
    )
    return {
        "input_state": input_state,
        "preparation_gate": preparation_gate,
        "literal_cx": cx,
        "rz": rz,
        "u_zz_diagonal": u_zz_diagonal,
        "u_zz_operator": u_zz_operator,
        "compiled_operator": compiled_operator,
        "first_cx_state": first_cx_state,
        "first_cx_coefficient_matrix": first_cx_coefficient_matrix,
        "first_cx_cap1_state": first_cx_cap1_state,
        "cap1_after_rz_state": cap1_after_rz_state,
        "exact_vector": exact_vector,
        "cap_only_lossy_vector": cap_only_lossy_vector,
        "cutoff_inert_vector": cutoff_inert_vector,
        "cutoff_only_lossy_vector": cutoff_only_lossy_vector,
        "direct_final_gate_control_vector": direct_final_gate_control_vector,
        "final_exact_coefficient_matrix": final_exact_coefficient_matrix,
    }


def _max_abs_residual(left: np.ndarray, right: np.ndarray) -> float:
    if left.shape != right.shape:
        raise ValueError("residual operands must have the same shape")
    return float(np.max(np.abs(left - right)))


def _unitarity_residual(matrix: np.ndarray) -> float:
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("unitarity requires a square matrix")
    identity = np.eye(matrix.shape[0], dtype=np.complex128)
    return _max_abs_residual(matrix.conj().T @ matrix, identity)


def _construct_payload(
    *,
    a: np.float64,
    b: np.float64,
    theta: np.float64,
) -> dict[str, Any]:
    arrays = _construct_arrays(a=a, b=b, theta=theta)
    analytic_spectrum = np.ascontiguousarray(np.asarray((a, b), dtype=np.float64))
    numeric_first_spectrum = np.ascontiguousarray(
        np.linalg.svd(
            arrays["first_cx_coefficient_matrix"],
            compute_uv=False,
        ),
        dtype=np.float64,
    )
    numeric_final_spectrum = np.ascontiguousarray(
        np.linalg.svd(
            arrays["final_exact_coefficient_matrix"],
            compute_uv=False,
        ),
        dtype=np.float64,
    )
    if (
        numeric_first_spectrum.dtype != _FLOAT64
        or numeric_final_spectrum.dtype != _FLOAT64
        or not np.all(np.isfinite(numeric_first_spectrum))
        or not np.all(np.isfinite(numeric_final_spectrum))
    ):
        raise RuntimeError("NumPy SVD returned an invalid spectrum")

    operator_difference = arrays["compiled_operator"] - arrays["u_zz_operator"]
    column_errors = [
        float(np.max(np.abs(operator_difference[:, column]))) for column in range(4)
    ]
    exact_from_compiled = _as_c128(
        arrays["compiled_operator"] @ arrays["input_state"],
        shape=(4,),
        label="compiled exact output",
    )
    k0_keep = _relative_cutoff_keep_count(
        analytic_spectrum,
        cutoff=K0_RELATIVE_CUTOFF,
    )
    k1_keep = _relative_cutoff_keep_count(
        analytic_spectrum,
        cutoff=K1_RELATIVE_CUTOFF,
    )
    formal_target = bool(a == FORMAL_A and b == FORMAL_B and theta == FORMAL_THETA)

    return {
        "schema": ANCHOR_SCHEMA,
        "fixture": {
            "schema": FIXTURE_SCHEMA,
            "fixture_id": "gcapeps_native_forced_truncation_two_site_bridge",
            "formal_target": formal_target,
            "n_qubits": 2,
            "sites": [0, 1],
            "edges": [[0, 1]],
            "basis": ["|00>", "|01>", "|10>", "|11>"],
            "q0_bit_significance": "most_significant",
            "matrix_indices": "row_is_output_column_is_input",
            "dtype": "complex128",
            "a": float(a),
            "b": float(b),
            "theta": float(theta),
            "a_fraction": "12/13" if formal_target else None,
            "b_fraction": "5/13" if formal_target else None,
            "theta_symbolic": "pi/5" if formal_target else None,
            "normalization_residual": float(abs(a * a + b * b - np.float64(1.0))),
        },
        "pilot_excluded": {
            "excluded_from_formal_finding": True,
            "a": float(PILOT_A),
            "b": float(PILOT_B),
            "theta": float(PILOT_THETA),
            "theta_symbolic": "pi/3",
            "allowed_use": "coordinate_and_gate_convention_unit_tests_only",
        },
        "dependency_boundary": {
            "allowed": ["python_standard_library", "numpy"],
            "forbidden": [
                "quimb",
                "stim",
                "sdim",
                "gcapeps",
                "error_coupling_simulator",
            ],
            "candidate_or_target_executed": False,
            "enters_timing_or_rss": False,
            "ground_truth_claimed": False,
            "role": "independent_exact_small_reference",
        },
        "numerical_policy": {
            "state_and_gate_dtype": "complex128",
            "singular_value_dtype": "float64",
            "renorm": False,
            "relative_cutoff_mode": "strict_s_gt_cutoff_times_s1",
            "exact_absolute_band": EXACT_ABSOLUTE_BAND,
            "fidelity_roundoff_band": FIDELITY_ROUNDOFF_BAND,
        },
        "arrays": {
            name: _encode_complex_array(array) for name, array in arrays.items()
        },
        "operator_identity": {
            "identity": "CX @ (I tensor RZ(theta)) @ CX == U_ZZ(theta)",
            "all_four_columns_checked": True,
            "per_column_d_inf": column_errors,
            "all_column_d_inf": max(column_errors),
            "frobenius_error": float(np.linalg.norm(operator_difference)),
            "compiled_action_d_inf": _max_abs_residual(
                exact_from_compiled,
                arrays["exact_vector"],
            ),
            "cx_unitarity_residual": _unitarity_residual(arrays["literal_cx"]),
            "rz_unitarity_residual": _unitarity_residual(arrays["rz"]),
            "u_zz_unitarity_residual": _unitarity_residual(arrays["u_zz_operator"]),
            "compiled_unitarity_residual": _unitarity_residual(
                arrays["compiled_operator"]
            ),
        },
        "first_cx_spectrum": {
            "analytic_singular_values": [float(value) for value in analytic_spectrum],
            "numeric_singular_values": [
                float(value) for value in numeric_first_spectrum
            ],
            "analytic_numeric_d_inf": float(
                np.max(np.abs(analytic_spectrum - numeric_first_spectrum))
            ),
            "ordered_gap": float(a - b),
            "nondegenerate": bool(a > b),
            "full_rank": bool(b > 0.0),
            "cap1_kept_dimension": 1,
            "discarded_squared_weight": float(b * b),
            "discarded_svd_norm": float(b),
            "positive_discarded_weight": bool(b * b > 0.0),
            "not_a_global_error_bound": True,
        },
        "final_exact_spectrum": {
            "numeric_singular_values": [
                float(value) for value in numeric_final_spectrum
            ],
            "physical_rank_at_absolute_1e_12": int(
                np.count_nonzero(numeric_final_spectrum > EXACT_ABSOLUTE_BAND)
            ),
            "fits_bond_one": bool(
                np.count_nonzero(numeric_final_spectrum > EXACT_ABSOLUTE_BAND) == 1
            ),
        },
        "cutoff_controls": {
            "K0": {
                "max_bond": None,
                "relative_cutoff": K0_RELATIVE_CUTOFF,
                "keep_by_cutoff": k0_keep,
                "actual_keep": k0_keep,
                "cause": "none" if k0_keep == 2 else "cutoff",
                "positive_discarded_weight": bool(k0_keep < 2),
            },
            "K1": {
                "max_bond": None,
                "relative_cutoff": K1_RELATIVE_CUTOFF,
                "keep_by_cutoff": k1_keep,
                "actual_keep": k1_keep,
                "cause": "none" if k1_keep == 2 else "cutoff",
                "positive_discarded_weight": bool(k1_keep < 2),
            },
        },
        "exact_predictions": {
            "exact_self": evaluate_metrics(
                arrays["exact_vector"],
                arrays["exact_vector"],
            ),
            "cap_only": evaluate_metrics(
                arrays["exact_vector"],
                arrays["cap_only_lossy_vector"],
            ),
            "cutoff_inert": evaluate_metrics(
                arrays["exact_vector"],
                arrays["cutoff_inert_vector"],
            ),
            "cutoff_only": evaluate_metrics(
                arrays["exact_vector"],
                arrays["cutoff_only_lossy_vector"],
            ),
            "direct_final_gate_control": evaluate_metrics(
                arrays["exact_vector"],
                arrays["direct_final_gate_control_vector"],
            ),
            "cap_only_expected_values": {
                "candidate_norm": float(a),
                "candidate_norm_squared": float(a * a),
                "d_2": float(b),
                "d_inf": float(b),
                "d_rel": float(b),
                "d_norm": float(np.float64(1.0) - a),
                "fidelity": float(a * a),
                "normalized_pure_state_trace_distance": float(b),
                "discarded_squared_weight": float(b * b),
                "kept_bond_dimension": 1,
            },
            "direct_final_gate_expected": {
                "positive_discarded_weight": False,
                "final_physical_rank": 1,
                "matches_exact_vector": True,
            },
        },
        "validation_policy": {
            "formal_constants_are_fixed": True,
            "payload_is_canonical_exact_match": True,
            "all_arrays_require_c128_finite_shape_and_hash": True,
            "operator_identity_all_columns_required": True,
            "formal_validation_tolerance": EXACT_ABSOLUTE_BAND,
        },
    }


def _canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def validate_anchor_payload(payload: Mapping[str, Any]) -> bool:
    """Strictly validate the fixed formal anchor; raise on any drift."""

    if not isinstance(payload, Mapping):
        raise TypeError("anchor payload must be a mapping")
    if payload.get("schema") != ANCHOR_SCHEMA:
        raise ValueError("anchor schema drifted")
    fixture = payload.get("fixture")
    if not isinstance(fixture, Mapping):
        raise ValueError("anchor fixture block is missing")
    if (
        fixture.get("schema") != FIXTURE_SCHEMA
        or fixture.get("formal_target") is not True
        or fixture.get("a") != float(FORMAL_A)
        or fixture.get("b") != float(FORMAL_B)
        or fixture.get("theta") != float(FORMAL_THETA)
        or fixture.get("q0_bit_significance") != "most_significant"
        or fixture.get("basis") != ["|00>", "|01>", "|10>", "|11>"]
        or fixture.get("dtype") != "complex128"
    ):
        raise ValueError("formal fixture identity drifted")

    arrays_block = payload.get("arrays")
    if not isinstance(arrays_block, Mapping) or set(arrays_block) != set(
        _EXPECTED_ARRAY_SHAPES
    ):
        raise ValueError("anchor array family is incomplete or widened")
    observed_arrays: dict[str, np.ndarray] = {}
    for name, shape in _EXPECTED_ARRAY_SHAPES.items():
        array = decode_complex_array(
            arrays_block[name],
            label=f"arrays.{name}",
        )
        if array.shape != shape:
            raise ValueError(f"arrays.{name} shape drifted")
        observed_arrays[name] = array

    expected_arrays = _construct_arrays(
        a=FORMAL_A,
        b=FORMAL_B,
        theta=FORMAL_THETA,
    )
    for name in _EXPECTED_ARRAY_SHAPES:
        if not np.array_equal(observed_arrays[name], expected_arrays[name]):
            raise ValueError(f"arrays.{name} differs from the formal construction")

    operator = payload.get("operator_identity")
    if not isinstance(operator, Mapping):
        raise ValueError("operator identity evidence is missing")
    all_column_error = operator.get("all_column_d_inf")
    per_column_error = operator.get("per_column_d_inf")
    if (
        not isinstance(all_column_error, (int, float))
        or isinstance(all_column_error, bool)
        or not math.isfinite(float(all_column_error))
        or float(all_column_error) > EXACT_ABSOLUTE_BAND
        or not isinstance(per_column_error, list)
        or len(per_column_error) != 4
        or any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or float(value) > EXACT_ABSOLUTE_BAND
            for value in per_column_error
        )
    ):
        raise ValueError("all-column operator identity failed")

    spectrum = payload.get("first_cx_spectrum")
    if not isinstance(spectrum, Mapping):
        raise ValueError("first-CX spectrum evidence is missing")
    analytic_values = spectrum.get("analytic_singular_values")
    if analytic_values != [float(FORMAL_A), float(FORMAL_B)]:
        raise ValueError("formal first-CX analytic spectrum drifted")
    if spectrum.get("nondegenerate") is not True:
        raise ValueError("formal first-CX spectrum became degenerate")
    if spectrum.get("positive_discarded_weight") is not True:
        raise ValueError("formal cap no longer discards positive weight")

    expected = _construct_payload(
        a=FORMAL_A,
        b=FORMAL_B,
        theta=FORMAL_THETA,
    )
    if _canonical_json_bytes(payload) != _canonical_json_bytes(expected):
        raise ValueError("anchor payload differs from the canonical formal payload")
    return True


def build_anchor_payload(
    *,
    a: Any = FORMAL_A,
    b: Any = FORMAL_B,
    theta: Any = FORMAL_THETA,
) -> dict[str, Any]:
    """Build an analytic fixture payload.

    Parameters are exposed for non-claim-bearing unit probes.  Only the
    bit-for-bit formal values pass :func:`validate_anchor_payload`; the formal
    default is self-validated before being returned.
    """

    a_value, b_value, theta_value = _validated_fixture_parameters(
        a=a,
        b=b,
        theta=theta,
    )
    payload = _construct_payload(a=a_value, b=b_value, theta=theta_value)
    if payload["fixture"]["formal_target"]:
        validate_anchor_payload(payload)
    return payload


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Emit the frozen NumPy-only GCAPEPS forced-truncation anchor "
            "to stdout without executing either candidate."
        ),
        epilog=(
            "Precondition: use this exact-small anchor outside all target "
            "timing and RSS samples."
        ),
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="emit canonical compact JSON instead of indented JSON",
    )
    return parser.parse_args()


def main() -> int:
    """Emit the self-validated formal anchor to stdout."""

    arguments = _parse_args()
    payload = build_anchor_payload()
    validate_anchor_payload(payload)
    if arguments.compact:
        output = _canonical_json_bytes(payload).decode("utf-8")
    else:
        output = json.dumps(
            payload,
            allow_nan=False,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
