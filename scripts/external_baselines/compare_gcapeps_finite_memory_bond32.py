#!/usr/bin/env python3
"""Independent metric kernel for the finite-memory bond-32 comparison.

The terminal comparator is intentionally NumPy/stdlib-only.  In particular it
does not import Quimb, Stim, SDIM, GCAPEPS, or the simulator package.  Candidate
workers emit raw arrays and candidate-local diagnostics; this module alone
forms cross-artifact fidelity, distance, entropy-error, and stress statistics.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

import numpy as np


COMPARATOR_SCHEMA = (
    "error_coupling_simulator.external.gcapeps_finite_memory."
    "comparator_worker.v1"
)
FIXTURE_SCHEMA = (
    "error_coupling_simulator.external.gcapeps_finite_memory.fixture.v1"
)
DENSE_SCHEMA = (
    "error_coupling_simulator.external.gcapeps_finite_memory."
    "dense_reference.v1"
)
PLAIN_EVIDENCE_SCHEMA = (
    "error_coupling_simulator.external.gcapeps_finite_memory."
    "plain_evidence_worker.v1"
)
GCAPEPS_EVIDENCE_SCHEMA = (
    "error_coupling_simulator.external.gcapeps_finite_memory."
    "gcapeps_evidence_worker.v1"
)
LOGICAL_MEMORY_SCHEMA = (
    "error_coupling_simulator.external.gcapeps_finite_memory."
    "logical_memory.v1"
)
SDIM_SCHEMA = (
    "error_coupling_simulator.external.gcapeps_finite_memory."
    "sdim_frame_control.v1"
)
REQUEST_KEYS = (
    "run_partition",
    "case_id",
    "input_id",
    "input_preparation_transcript_sha256",
    "shared_evolution_transcript_sha256",
    "round_prefix",
    "collision_ordinal",
    "round_index",
    "site_index",
    "axis_index",
    "physical_pauli_body",
)
REQUEST_KEY_SET = frozenset(REQUEST_KEYS)
SDIM_ROW_KEYS = REQUEST_KEY_SET | frozenset({"sdim_sign", "sdim_body"})
STIM_ROW_KEYS = REQUEST_KEY_SET | frozenset({"stim_sign", "stim_body"})
GC_ROW_KEYS = REQUEST_KEY_SET | frozenset(
    {
        "physical_sign",
        "physical_body",
        "pulled_back_sign",
        "pulled_back_body",
    }
)
PRE_METRIC_KEYS = frozenset(
    {
        "raw_vector_sha256",
        "raw_norm_squared_real",
        "raw_norm_squared_imag_abs",
        "stored_vector_normalized_before_metric",
        "metric_local_normalized_copy",
        "phase_fit",
        "coordinate_permutation",
        "dtype_cast",
    }
)
POSITIVE_TAIL_THRESHOLD = 1.0e-12
NDARRAY_KEYS = frozenset(
    {
        "encoding",
        "dtype",
        "shape",
        "order",
        "nbytes",
        "data_sha256",
        "data_base64",
    }
)
ROUND_CONTINUITY_KEYS = frozenset(
    {
        "round_index",
        "prior_round_end_state_sha256",
        "round_start_state_sha256",
        "round_end_state_sha256",
        "starts_from_prior_round_end",
        "candidate_restarted_between_rounds",
        "memory_reset_between_rounds",
    }
)
PLAIN_SPLIT_KEYS = frozenset(
    {
        "operation_index",
        "round_index",
        "collision_ordinal",
        "ordered_sites",
        "pre_split_state_sha256",
        "shadow_pre_split_state_sha256",
        "configured_max_bond",
        "configured_cutoff",
        "configured_cutoff_mode",
        "configured_method",
        "configured_renorm",
        "configured_absorb",
        "configured_power",
        "configured_smudge",
        "full_singular_values",
        "kept_singular_values",
        "full_bond_dimension",
        "kept_bond_dimension",
        "pre_split_weight",
        "discarded_squared_weight",
        "discarded_fraction",
        "cause",
        "positive_discarded_weight",
        "positive_discarded_weight_threshold",
        "eligible_edges",
        "materialized_zero_gauge_edges",
        "smudge_actually_used",
        "spectrum_producer_binding_sha256",
    }
)
GC_SPLIT_KEYS = frozenset(
    {
        "operation_index",
        "round_index",
        "collision_ordinal",
        "split_index",
        "edge",
        "bond_index_before",
        "bond_index_after",
        "exact_precompression_bond",
        "kept_bond_dimension",
        "configured_max_bond",
        "configured_cutoff",
        "configured_cutoff_mode",
        "configured_method",
        "configured_renorm",
        "configured_absorb",
        "configured_smudge",
        "configured_power",
        "low_level_contract",
        "identity_matrix_sha256",
        "stripped_high_level_keys",
        "selected_gauges",
        "smudge_actually_used",
        "pre_split_state_sha256",
        "shadow_evidence_enabled",
        "shadow_pre_split_state_sha256",
        "full_singular_values",
        "kept_singular_values",
        "full_bond_dimension",
        "discarded_squared_weight",
        "discarded_fraction",
        "cause",
        "dimension_reduced",
        "positive_discarded_weight",
        "positive_discarded_weight_threshold",
        "physical_gate_count_before",
        "physical_gate_count_after",
        "info_mapping_was_fresh_and_empty",
        "not_a_global_error_bound",
        "spectrum_producer_binding_sha256",
    }
)
GC_SELECTED_GAUGE_KEYS = frozenset(
    {
        "graph_edge",
        "bond_index",
        "position",
        "had_exact_zero",
        "materialized_into_full_candidate",
        "present_after_zero_preprocessing",
        "strictly_positive_after_zero_preprocessing",
        "dtype",
    }
)
HERMITICITY_TOLERANCE = 1.0e-12
TRACE_TOLERANCE = 1.0e-12
NEGATIVE_MASS_TOLERANCE = 1.0e-12
EIGEN_RESIDUAL_TOLERANCE = 1.0e-10
FIDELITY_ROUNDOFF_TOLERANCE = 1.0e-12
NUMERICAL_RANK_RELATIVE_TOLERANCE = 1.0e-12
BLP_INCREMENT_TOLERANCE = 1.0e-10
ENTANGLEMENT_HYPOTHESIS_TOLERANCE = 1.0e-10


def _ndarray_root(array: np.ndarray) -> np.ndarray:
    """Return the terminal NumPy-array base used for logical-byte ownership."""

    if not isinstance(array, np.ndarray):
        raise TypeError("comparator array ownership accepts only ndarrays")
    root = array
    seen = {id(root)}
    while isinstance(root.base, np.ndarray):
        root = root.base
        if id(root) in seen:
            raise ValueError("ndarray base chain contains an identity cycle")
        seen.add(id(root))
    return root


class ComparatorArraySampler:
    """Sample live comparator-owned ndarray roots with identity deduplication."""

    def __init__(self) -> None:
        self._active: dict[int, np.ndarray] = {}
        self._maximum = 0

    def _current_bytes(self) -> int:
        roots: dict[int, np.ndarray] = {}
        for array in self._active.values():
            root = _ndarray_root(array)
            roots.setdefault(id(root), root)
        return sum(int(root.nbytes) for root in roots.values())

    def sample(self) -> int:
        current = self._current_bytes()
        self._maximum = max(self._maximum, current)
        return current

    def materialized(self, *arrays: np.ndarray) -> int:
        for array in arrays:
            if not isinstance(array, np.ndarray):
                raise TypeError(
                    "comparator materialization must be a NumPy ndarray"
                )
            self._active.setdefault(id(array), array)
        return self.sample()

    def release(self, *arrays: np.ndarray) -> int:
        """Sample pre-release coexistence, then stop owning the named arrays."""

        self.sample()
        for array in arrays:
            observed = self._active.get(id(array))
            if observed is not array:
                raise ValueError(
                    "attempted to release an unowned comparator ndarray"
                )
            del self._active[id(array)]
        return self.sample()

    @property
    def current_bytes(self) -> int:
        return self._current_bytes()

    @property
    def maximum_bytes(self) -> int:
        return self._maximum


def _arrays_materialized(
    sampler: ComparatorArraySampler | None,
    *arrays: np.ndarray,
) -> None:
    if sampler is not None:
        sampler.materialized(*arrays)


def _arrays_released(
    sampler: ComparatorArraySampler | None,
    *arrays: np.ndarray,
) -> None:
    if sampler is not None:
        sampler.release(*arrays)


def _strict_object(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON token: {value}")


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def projection_sha256(payload: Mapping[str, Any]) -> str:
    projected = dict(payload)
    projected.pop("result_projection_sha256", None)
    return hashlib.sha256(canonical_json_bytes(projected)).hexdigest()


def _require_exact_keys(
    value: Mapping[str, Any],
    expected: Sequence[str] | set[str] | frozenset[str],
    *,
    name: str,
) -> None:
    if not isinstance(value, Mapping):
        raise TypeError(f"{name} must be a JSON object")
    expected_set = set(expected)
    if set(value) != expected_set:
        missing = sorted(expected_set - set(value))
        extra = sorted(set(value) - expected_set)
        raise ValueError(
            f"{name} key mismatch: missing={missing}, extra={extra}"
        )


def _plain_int(
    value: Any,
    *,
    name: str,
    minimum: int = 0,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < minimum
    ):
        raise ValueError(
            f"{name} must be a non-boolean integer >= {minimum}"
        )
    return value


def _finite_float(value: Any, *, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite JSON number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


_LOGICAL_SAMPLE_KEYS = frozenset(
    {
        "label",
        "tensor_role",
        "carrier_tensor_bytes",
        "gauge_spectrum_bytes",
        "frame_bytes",
        "ledger_bytes",
        "total_owned_logical_bytes",
        "evidence_auxiliary_array_bytes",
        "evidence_auxiliary_ledger_bytes",
        "evidence_owned_logical_bytes",
    }
)
_LOGICAL_BASE_REPORT_KEYS = frozenset(
    {
        "schema",
        "tensor_role",
        "sample_count",
        "final_committed_owned_logical_bytes",
        "max_committed_owned_logical_bytes",
        "max_sampled_algorithm_owned_logical_bytes",
        "final_committed_sample",
        "max_committed_sample",
        "max_sampled_algorithm_sample",
    }
)
_LOGICAL_EVIDENCE_REPORT_KEYS = frozenset(
    {
        "max_sampled_evidence_owned_logical_bytes",
        "max_sampled_evidence_sample",
    }
)


def _validate_logical_memory_sample(
    sample: Mapping[str, Any],
    *,
    expected_tensor_role: str,
    name: str,
) -> None:
    _require_exact_keys(sample, _LOGICAL_SAMPLE_KEYS, name=name)
    if (
        not isinstance(sample["label"], str)
        or not sample["label"]
        or sample["tensor_role"] != expected_tensor_role
    ):
        raise ValueError(f"{name} label or tensor role is invalid")
    integer_fields = (
        "carrier_tensor_bytes",
        "gauge_spectrum_bytes",
        "frame_bytes",
        "ledger_bytes",
        "total_owned_logical_bytes",
        "evidence_auxiliary_array_bytes",
        "evidence_auxiliary_ledger_bytes",
        "evidence_owned_logical_bytes",
    )
    for field in integer_fields:
        _plain_int(sample[field], name=f"{name} {field}")
    base_total = sum(
        sample[field]
        for field in (
            "carrier_tensor_bytes",
            "gauge_spectrum_bytes",
            "frame_bytes",
            "ledger_bytes",
        )
    )
    evidence_total = base_total + sum(
        sample[field]
        for field in (
            "evidence_auxiliary_array_bytes",
            "evidence_auxiliary_ledger_bytes",
        )
    )
    if (
        sample["total_owned_logical_bytes"] != base_total
        or sample["evidence_owned_logical_bytes"] != evidence_total
    ):
        raise ValueError(f"{name} category sum is invalid")
    if expected_tensor_role == "none":
        if base_total != 0:
            raise ValueError(f"{name} evidence sample claims base ownership")
    elif (
        sample["evidence_auxiliary_array_bytes"] != 0
        or sample["evidence_auxiliary_ledger_bytes"] != 0
    ):
        raise ValueError(f"{name} base sample claims evidence ownership")
    if (
        expected_tensor_role == "plain_physical"
        and sample["frame_bytes"] != 0
    ):
        raise ValueError(f"{name} plain sample claims frame bytes")


def _validate_logical_memory_report(
    report: Mapping[str, Any],
    *,
    lane: str,
    require_evidence: bool,
    name: str,
) -> None:
    if not isinstance(report, Mapping):
        raise TypeError(f"{name} must be an object")
    expected_keys = set(_LOGICAL_BASE_REPORT_KEYS)
    if require_evidence:
        expected_keys.update(_LOGICAL_EVIDENCE_REPORT_KEYS)
    _require_exact_keys(report, expected_keys, name=name)
    tensor_role = "plain_physical" if lane == "plain" else "gc_residual"
    if (
        report["schema"] != LOGICAL_MEMORY_SCHEMA
        or report["tensor_role"] != tensor_role
    ):
        raise ValueError(f"{name} schema or tensor role is invalid")
    _plain_int(report["sample_count"], name=f"{name} sample_count", minimum=1)
    for field in (
        "final_committed_owned_logical_bytes",
        "max_committed_owned_logical_bytes",
        "max_sampled_algorithm_owned_logical_bytes",
    ):
        _plain_int(report[field], name=f"{name} {field}", minimum=1)
    samples = (
        ("final_committed_sample", "final_committed_owned_logical_bytes"),
        ("max_committed_sample", "max_committed_owned_logical_bytes"),
        (
            "max_sampled_algorithm_sample",
            "max_sampled_algorithm_owned_logical_bytes",
        ),
    )
    for sample_field, total_field in samples:
        sample = report[sample_field]
        _validate_logical_memory_sample(
            sample,
            expected_tensor_role=tensor_role,
            name=f"{name} {sample_field}",
        )
        if sample["total_owned_logical_bytes"] != report[total_field]:
            raise ValueError(f"{name} sample does not match its reported peak")
    if not (
        report["final_committed_owned_logical_bytes"]
        <= report["max_committed_owned_logical_bytes"]
        <= report["max_sampled_algorithm_owned_logical_bytes"]
    ):
        raise ValueError(f"{name} base memory peaks are not ordered")
    if require_evidence:
        evidence_total = _plain_int(
            report["max_sampled_evidence_owned_logical_bytes"],
            name=f"{name} max_sampled_evidence_owned_logical_bytes",
            minimum=1,
        )
        evidence_sample = report["max_sampled_evidence_sample"]
        _validate_logical_memory_sample(
            evidence_sample,
            expected_tensor_role="none",
            name=f"{name} max_sampled_evidence_sample",
        )
        if evidence_sample["evidence_owned_logical_bytes"] != evidence_total:
            raise ValueError(f"{name} evidence sample does not match its peak")


def _logical_memory_base_projection(report: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: report[key]
        for key in _LOGICAL_BASE_REPORT_KEYS
        if key != "sample_count"
    }


def _validate_projection(core: Mapping[str, Any], *, name: str) -> str:
    if not isinstance(core, Mapping):
        raise TypeError(f"{name} must be a JSON object")
    observed = core.get("result_projection_sha256")
    expected = projection_sha256(core)
    if not _is_sha256(observed) or observed != expected:
        raise ValueError(f"{name} result projection hash mismatch")
    return expected


def read_strict_canonical_json(path: Path) -> dict[str, Any]:
    raw = path.resolve(strict=True).read_bytes()
    try:
        value = json.loads(
            raw.decode("ascii"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON artifact: {path}") from exc
    if not isinstance(value, dict):
        raise ValueError("artifact must contain one JSON object")
    if canonical_json_bytes(value) != raw:
        raise ValueError("artifact is not canonical compact ASCII JSON")
    return value


def _checked_shape(value: Any) -> tuple[int, ...]:
    if not isinstance(value, list):
        raise TypeError("ndarray shape must be a JSON list")
    shape = []
    for index, dimension in enumerate(value):
        if (
            isinstance(dimension, bool)
            or not isinstance(dimension, int)
            or dimension < 0
        ):
            raise ValueError(f"shape[{index}] is not a nonnegative integer")
        shape.append(dimension)
    return tuple(shape)


def decode_ndarray_v1(
    payload: Mapping[str, Any],
    *,
    dtype: str,
    shape: tuple[int, ...],
    sampler: ComparatorArraySampler | None = None,
) -> np.ndarray:
    """Decode exact padded RFC4648 bytes with no cast or permutation."""

    if not isinstance(payload, Mapping) or set(payload) != NDARRAY_KEYS:
        raise ValueError("ndarray-v1 object has the wrong exact key set")
    if payload["encoding"] != "ndarray-v1" or payload["order"] != "C":
        raise ValueError("unsupported ndarray encoding or order")
    if payload["dtype"] != dtype:
        raise TypeError("ndarray dtype disagrees with the owning schema")
    if _checked_shape(payload["shape"]) != shape:
        raise ValueError("ndarray shape disagrees with the owning schema")
    item_dtype = np.dtype(dtype)
    expected_nbytes = math.prod(shape) * item_dtype.itemsize
    if (
        isinstance(payload["nbytes"], bool)
        or not isinstance(payload["nbytes"], int)
        or payload["nbytes"] != expected_nbytes
    ):
        raise ValueError("ndarray nbytes disagrees with dtype and shape")
    encoded = payload["data_base64"]
    if not isinstance(encoded, str):
        raise TypeError("data_base64 must be a string")
    try:
        encoded_ascii = encoded.encode("ascii")
        raw = base64.b64decode(encoded_ascii, validate=True)
    except (UnicodeEncodeError, binascii.Error) as exc:
        raise ValueError("data_base64 is not strict ASCII RFC4648") from exc
    if base64.b64encode(raw) != encoded_ascii:
        raise ValueError("data_base64 is not canonical padded RFC4648")
    if len(raw) != expected_nbytes:
        raise ValueError("decoded ndarray byte length disagrees with nbytes")
    digest = hashlib.sha256(raw).hexdigest()
    if payload["data_sha256"] != digest:
        raise ValueError("ndarray byte hash mismatch")
    array = np.frombuffer(raw, dtype=item_dtype).reshape(shape, order="C").copy(
        order="C"
    )
    if array.dtype.str != dtype or array.shape != shape:
        raise AssertionError("decoded array identity drifted")
    if not array.flags.c_contiguous or array.tobytes(order="C") != raw:
        raise AssertionError("decoded array bytes drifted")
    if sampler is not None:
        sampler.materialized(array)
    return array


def _finite_complex(array: np.ndarray, *, name: str) -> None:
    if not np.isfinite(array.real).all() or not np.isfinite(array.imag).all():
        raise ValueError(f"{name} contains a non-finite component")


def vector_gate(
    vector: np.ndarray,
    *,
    width: int,
    sampler: ComparatorArraySampler | None = None,
) -> dict[str, Any]:
    """Apply every mandatory pre-metric gate and form system diagnostics."""

    if isinstance(width, bool) or not isinstance(width, int) or width <= 0:
        raise ValueError("width must be a positive integer")
    if not isinstance(vector, np.ndarray):
        raise TypeError("vector must be a NumPy array")
    expected_shape = (2 ** (2 * width),)
    if vector.dtype.str != "<c16":
        raise TypeError("vector dtype must be exact little-endian <c16")
    if vector.shape != expected_shape:
        raise ValueError(f"vector shape must be exactly {expected_shape}")
    if not vector.flags.c_contiguous:
        raise ValueError("vector must be C-contiguous")
    _finite_complex(vector, name="vector")
    _arrays_materialized(sampler, vector)
    raw = vector.tobytes(order="C")
    z = np.vdot(vector, vector)
    z_real = float(z.real)
    z_imag_abs = float(abs(z.imag))
    if not math.isfinite(z_real) or not math.isfinite(z_imag_abs):
        raise ValueError("vector norm is non-finite")
    if z_imag_abs > 1.0e-12:
        raise ValueError("vector norm-squared imaginary residual is excessive")
    if z_real <= 0.0:
        raise ValueError("vector norm must be strictly positive")

    system_dimension = 2**width
    amplitude = vector.reshape(
        (system_dimension, system_dimension),
        order="C",
    )
    _arrays_materialized(sampler, amplitude)
    rho = np.ascontiguousarray(
        amplitude @ amplitude.conjugate().T / z_real,
        dtype=np.complex128,
    )
    _arrays_materialized(sampler, rho)
    hermiticity_residual = float(
        np.max(np.abs(rho - rho.conjugate().T), initial=0.0)
    )
    trace_residual = float(abs(np.trace(rho) - 1.0))
    if hermiticity_residual > HERMITICITY_TOLERANCE:
        raise ValueError("reduced state hermiticity residual is excessive")
    if trace_residual > TRACE_TOLERANCE:
        raise ValueError("reduced state trace residual is excessive")
    rho_h = np.ascontiguousarray(
        (rho + rho.conjugate().T) / 2.0,
        dtype=np.complex128,
    )
    _arrays_materialized(sampler, rho_h)
    eigenvalues, eigenvectors = np.linalg.eigh(rho_h)
    _arrays_materialized(sampler, eigenvalues, eigenvectors)
    pair_residual = float(
        np.max(
            np.abs(
                rho_h @ eigenvectors
                - eigenvectors * eigenvalues[np.newaxis, :]
            ),
            initial=0.0,
        )
    )
    reconstructed = (eigenvectors * eigenvalues[np.newaxis, :]) @ (
        eigenvectors.conjugate().T
    )
    _arrays_materialized(sampler, reconstructed)
    reconstruction_residual = float(
        np.max(np.abs(rho_h - reconstructed), initial=0.0)
    )
    minimum_eigenvalue = float(np.min(eigenvalues))
    negative_mass = float(np.maximum(0.0, -eigenvalues).sum())
    if minimum_eigenvalue < -NEGATIVE_MASS_TOLERANCE:
        raise ValueError("reduced state has excessive negative eigenvalue")
    if negative_mass > NEGATIVE_MASS_TOLERANCE:
        raise ValueError("reduced state has excessive negative mass")
    if pair_residual > EIGEN_RESIDUAL_TOLERANCE:
        raise ValueError("eigenpair residual is excessive")
    if reconstruction_residual > EIGEN_RESIDUAL_TOLERANCE:
        raise ValueError("eigendecomposition reconstruction failed")
    clipped = np.maximum(eigenvalues, 0.0)
    _arrays_materialized(sampler, clipped)
    clipped_sum = float(clipped.sum())
    if not math.isfinite(clipped_sum) or clipped_sum <= 0.0:
        raise ValueError("clipped eigenvalue sum is nonpositive")
    probabilities = clipped / clipped_sum
    positive = probabilities[probabilities > 0.0]
    _arrays_materialized(sampler, probabilities, positive)
    entropy_von_neumann = float(-np.sum(positive * np.log2(positive)))
    purity = float(np.sum(probabilities**2))
    entropy_renyi2 = float(-math.log2(purity))
    singular_values = np.linalg.svd(amplitude, compute_uv=False) / math.sqrt(
        z_real
    )
    _arrays_materialized(sampler, singular_values)
    largest = float(singular_values[0])
    numerical_rank = int(
        np.count_nonzero(
            singular_values > NUMERICAL_RANK_RELATIVE_TOLERANCE * largest
        )
    )
    normalized_schmidt_values = np.array(
        singular_values, dtype=np.float64, order="C", copy=True
    )
    _arrays_materialized(sampler, normalized_schmidt_values)
    result = {
        "raw_vector_sha256": hashlib.sha256(raw).hexdigest(),
        "raw_norm_squared_real": z_real,
        "raw_norm_squared_imag_abs": z_imag_abs,
        "raw_norm": math.sqrt(z_real),
        "rho_system": rho,
        "rho_hermiticity_residual": hermiticity_residual,
        "rho_trace_residual": trace_residual,
        "rho_hermitization_correction": hermiticity_residual / 2.0,
        "rho_minimum_eigenvalue": minimum_eigenvalue,
        "rho_negative_mass": negative_mass,
        "rho_eigenpair_residual": pair_residual,
        "rho_reconstruction_residual": reconstruction_residual,
        "rho_clipped_sum": clipped_sum,
        "rho_eigenvalue_renormalization_factor": 1.0 / clipped_sum,
        "entropy_von_neumann": entropy_von_neumann,
        "entropy_renyi2": entropy_renyi2,
        "normalized_schmidt_values": normalized_schmidt_values,
        "numerical_schmidt_rank": numerical_rank,
    }

    _arrays_released(
        sampler,
        amplitude,
        rho_h,
        eigenvalues,
        eigenvectors,
        reconstructed,
        clipped,
        probabilities,
        positive,
        singular_values,
    )
    return result


def trace_distance(
    rho_left: np.ndarray,
    rho_right: np.ndarray,
    *,
    sampler: ComparatorArraySampler | None = None,
) -> float:
    if (
        not isinstance(rho_left, np.ndarray)
        or not isinstance(rho_right, np.ndarray)
        or rho_left.dtype.str != "<c16"
        or rho_right.dtype.str != "<c16"
        or rho_left.shape != rho_right.shape
        or rho_left.ndim != 2
        or rho_left.shape[0] != rho_left.shape[1]
    ):
        raise ValueError("trace-distance inputs must be same-shape c128 matrices")
    _finite_complex(rho_left, name="rho_left")
    _finite_complex(rho_right, name="rho_right")
    difference = rho_left - rho_right
    _arrays_materialized(sampler, difference)
    delta = np.ascontiguousarray(
        (difference + difference.conjugate().T) / 2.0
    )
    eigenvalues = np.linalg.eigvalsh(delta)
    _arrays_materialized(sampler, delta, eigenvalues)
    value = 0.5 * float(np.sum(np.abs(eigenvalues)))
    if not math.isfinite(value) or value < 0.0:
        raise ValueError("trace distance is invalid")
    _arrays_released(sampler, difference, delta, eigenvalues)
    return value


def whole_state_metrics(
    reference: np.ndarray,
    candidate: np.ndarray,
    *,
    width: int,
    sampler: ComparatorArraySampler | None = None,
) -> dict[str, float]:
    """Compute every frozen complete-state metric without fitting phase."""

    reference_local = vector_gate(reference, width=width, sampler=sampler)
    candidate_local = vector_gate(candidate, width=width, sampler=sampler)
    nx2 = reference_local["raw_norm_squared_real"]
    ny2 = candidate_local["raw_norm_squared_real"]
    denominator = nx2 * ny2
    if not math.isfinite(denominator) or denominator <= 0.0:
        raise ValueError("fidelity denominator is invalid")
    overlap = np.vdot(reference, candidate)
    fidelity_raw = float(abs(overlap) ** 2 / denominator)
    if not math.isfinite(fidelity_raw) or fidelity_raw < 0.0:
        raise ValueError("raw fidelity is invalid")
    correction = max(0.0, fidelity_raw - 1.0)
    if correction > FIDELITY_ROUNDOFF_TOLERANCE:
        raise ValueError("fidelity exceeds one beyond roundoff allowance")
    fidelity = min(1.0, fidelity_raw)
    pure_trace_distance = math.sqrt(1.0 - fidelity)
    nx = math.sqrt(nx2)
    ny = math.sqrt(ny2)
    norm_sum = nx + ny
    if not math.isfinite(norm_sum) or norm_sum <= 0.0:
        raise ValueError("distance norm denominator is invalid")
    difference = reference - candidate
    normalized_reference = reference / nx
    normalized_candidate = candidate / ny
    normalized_difference = normalized_reference - normalized_candidate
    _arrays_materialized(
        sampler,
        difference,
        normalized_reference,
        normalized_candidate,
        normalized_difference,
    )
    result = {
        "fidelity_raw": fidelity_raw,
        "fidelity_roundoff_correction": correction,
        "fidelity": fidelity,
        "pure_state_trace_distance": pure_trace_distance,
        "relative_state_distance": 2.0
        * float(np.linalg.norm(difference))
        / norm_sum,
        "relative_norm_distance": 2.0 * abs(nx - ny) / norm_sum,
        "d2_raw": float(np.linalg.norm(difference)),
        "dinf_raw": float(np.max(np.abs(difference), initial=0.0)),
        "d2_normalized": float(np.linalg.norm(normalized_difference)),
        "dinf_normalized": float(
            np.max(np.abs(normalized_difference), initial=0.0)
        ),
        "reference_raw_norm": nx,
        "candidate_raw_norm": ny,
        "signed_raw_norm_error": ny - nx,
        "absolute_raw_norm_error": abs(ny - nx),
        "entropy_von_neumann_error": abs(
            candidate_local["entropy_von_neumann"]
            - reference_local["entropy_von_neumann"]
        ),
        "entropy_renyi2_error": abs(
            candidate_local["entropy_renyi2"]
            - reference_local["entropy_renyi2"]
        ),
        "reduced_state_trace_distance": trace_distance(
            reference_local["rho_system"],
            candidate_local["rho_system"],
            sampler=sampler,
        ),
    }

    _arrays_released(
        sampler,
        difference,
        normalized_reference,
        normalized_candidate,
        normalized_difference,
        reference_local["rho_system"],
        reference_local["normalized_schmidt_values"],
        candidate_local["rho_system"],
        candidate_local["normalized_schmidt_values"],
    )
    return result


def fixed_pair_checkpoint_error(
    dense_input1: np.ndarray,
    dense_input2: np.ndarray,
    candidate_input1: np.ndarray,
    candidate_input2: np.ndarray,
    *,
    width: int,
    sampler: ComparatorArraySampler | None = None,
) -> dict[str, float]:
    dense_1 = vector_gate(dense_input1, width=width, sampler=sampler)
    dense_2 = vector_gate(dense_input2, width=width, sampler=sampler)
    candidate_1 = vector_gate(
        candidate_input1, width=width, sampler=sampler
    )
    candidate_2 = vector_gate(
        candidate_input2, width=width, sampler=sampler
    )
    dense_distance = trace_distance(
        dense_1["rho_system"],
        dense_2["rho_system"],
        sampler=sampler,
    )
    candidate_distance = trace_distance(
        candidate_1["rho_system"],
        candidate_2["rho_system"],
        sampler=sampler,
    )
    result = {
        "dense_fixed_pair_trace_distance": dense_distance,
        "candidate_fixed_pair_trace_distance": candidate_distance,
        "absolute_trace_distance_error": abs(
            candidate_distance - dense_distance
        ),
    }
    _arrays_released(
        sampler,
        dense_1["rho_system"],
        dense_1["normalized_schmidt_values"],
        dense_2["rho_system"],
        dense_2["normalized_schmidt_values"],
        candidate_1["rho_system"],
        candidate_1["normalized_schmidt_values"],
        candidate_2["rho_system"],
        candidate_2["normalized_schmidt_values"],
    )
    return result


def stress_delta_f(
    *,
    plain_fidelities: Mapping[str, float],
    gcapeps_fidelities: Mapping[str, float],
    tie_tolerance: float = 1.0e-10,
) -> dict[str, Any]:
    if set(plain_fidelities) != {"input1", "input2"}:
        raise ValueError("plain stress fidelities must cover both inputs")
    if set(gcapeps_fidelities) != {"input1", "input2"}:
        raise ValueError("GC stress fidelities must cover both inputs")
    values = [*plain_fidelities.values(), *gcapeps_fidelities.values()]
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or float(value) < 0.0
        or float(value) > 1.0
        for value in values
    ):
        raise ValueError("stress fidelity is outside [0,1]")
    minimum_plain = min(float(value) for value in plain_fidelities.values())
    minimum_gc = min(float(value) for value in gcapeps_fidelities.values())
    delta = minimum_gc - minimum_plain
    if delta > tie_tolerance:
        direction = "gcapeps_higher"
    elif delta < -tie_tolerance:
        direction = "plain_higher"
    else:
        direction = "tie"
    return {
        "minimum_plain_fidelity": minimum_plain,
        "minimum_gcapeps_fidelity": minimum_gc,
        "delta_fidelity": delta,
        "tie_tolerance": tie_tolerance,
        "direction": direction,
    }


def _request_key(
    row: Mapping[str, Any],
    *,
    width: int,
    run_partition: str,
    case_id: str,
    input_hashes: Mapping[int, str],
    shared_evolution_sha256: str,
    exact_keys: frozenset[str],
    name: str,
) -> tuple[Any, ...]:
    _require_exact_keys(row, exact_keys, name=name)
    if row["run_partition"] != run_partition or row["case_id"] != case_id:
        raise ValueError(f"{name} partition or case identity mismatch")
    input_id = _plain_int(row["input_id"], name=f"{name}.input_id", minimum=1)
    if input_id not in (1, 2):
        raise ValueError(f"{name}.input_id is not one of the two fixed inputs")
    if (
        row["input_preparation_transcript_sha256"]
        != input_hashes[input_id]
        or row["shared_evolution_transcript_sha256"]
        != shared_evolution_sha256
    ):
        raise ValueError(f"{name} transcript identity mismatch")
    round_prefix = _plain_int(
        row["round_prefix"], name=f"{name}.round_prefix", minimum=1
    )
    round_index = _plain_int(
        row["round_index"], name=f"{name}.round_index", minimum=1
    )
    if round_prefix != round_index:
        raise ValueError(f"{name} round prefix/index mismatch")
    _plain_int(
        row["collision_ordinal"],
        name=f"{name}.collision_ordinal",
    )
    site_index = _plain_int(
        row["site_index"], name=f"{name}.site_index"
    )
    axis_index = _plain_int(
        row["axis_index"], name=f"{name}.axis_index"
    )
    if site_index >= width or axis_index not in (0, 1, 2):
        raise ValueError(f"{name} site or axis locator is out of range")
    body = row["physical_pauli_body"]
    if (
        not isinstance(body, str)
        or len(body) != 2 * width
        or any(label not in "IXYZ" for label in body)
    ):
        raise ValueError(f"{name} physical Pauli body is invalid")
    return tuple(row[field] for field in REQUEST_KEYS)


def _request_sequence(
    rows: Any,
    *,
    width: int,
    run_partition: str,
    case_id: str,
    input_hashes: Mapping[int, str],
    shared_evolution_sha256: str,
    exact_keys: frozenset[str],
    name: str,
) -> list[tuple[Any, ...]]:
    if not isinstance(rows, list):
        raise TypeError(f"{name} must be a JSON list")
    keys = [
        _request_key(
            row,
            width=width,
            run_partition=run_partition,
            case_id=case_id,
            input_hashes=input_hashes,
            shared_evolution_sha256=shared_evolution_sha256,
            exact_keys=exact_keys,
            name=f"{name}[{index}]",
        )
        for index, row in enumerate(rows)
    ]
    if len(keys) != len(set(keys)):
        raise ValueError(f"{name} contains a duplicate request key")
    try:
        ordered = sorted(keys)
    except TypeError as exc:
        raise ValueError(f"{name} request keys are not lexicographically typed") from exc
    if keys != ordered:
        raise ValueError(f"{name} is not in exact lexicographic order")
    return keys


def _fixture_operation_sequence(
    carrier_path: Mapping[str, Any],
    *,
    rounds: int,
    width: int,
) -> list[Mapping[str, Any]]:
    round_rows = carrier_path.get("round_ledger")
    if not isinstance(round_rows, list) or len(round_rows) != rounds:
        raise ValueError("fixture physical round ledger shape drifted")
    operations: list[Mapping[str, Any]] = []
    next_collision_ordinal = 0
    for expected_round, round_row in enumerate(round_rows, start=1):
        if (
            not isinstance(round_row, Mapping)
            or round_row.get("round_index") != expected_round
            or not isinstance(round_row.get("operations"), list)
        ):
            raise ValueError("fixture physical round ledger order drifted")
        for operation in round_row["operations"]:
            if not isinstance(operation, Mapping):
                raise TypeError("fixture operation must be an object")
            operation_index = _plain_int(
                operation.get("operation_index"),
                name="fixture operation_index",
            )
            targets = operation.get("targets")
            if (
                operation_index != len(operations)
                or operation.get("round_index") != expected_round
                or not isinstance(targets, list)
                or len(targets) not in (1, 2)
                or any(
                    isinstance(target, bool)
                    or not isinstance(target, int)
                    or target < 0
                    or target >= 2 * width
                    for target in targets
                )
                or len(set(targets)) != len(targets)
            ):
                raise ValueError("fixture operation locator or targets drifted")
            operation_class = operation.get("operation_class")
            gate_kind = operation.get("gate_kind")
            if operation_class == "clifford":
                if gate_kind not in {"H", "S", "CX"}:
                    raise ValueError("fixture Clifford gate kind drifted")
                if "collision_ordinal" in operation:
                    raise ValueError("fixture Clifford has collision locator")
            elif operation_class == "collision_rotation":
                if (
                    gate_kind != "PAULI_ROTATION"
                    or len(targets) != 2
                    or operation.get("collision_ordinal")
                    != next_collision_ordinal
                    or operation.get("site_index") != targets[0]
                    or targets[1] != width + targets[0]
                    or operation.get("axis_index") not in (0, 1, 2)
                ):
                    raise ValueError("fixture collision locator drifted")
                next_collision_ordinal += 1
            else:
                raise ValueError("fixture operation class drifted")
            operations.append(operation)
    return operations


def _validate_round_continuity(
    rows: Any,
    *,
    lane: str,
    rounds: int,
) -> list[dict[str, Any]]:
    if not isinstance(rows, list) or len(rows) != rounds:
        raise ValueError(f"{lane} round continuity cardinality mismatch")
    previous_end = None
    projected: list[dict[str, Any]] = []
    for expected_round, row in enumerate(rows, start=1):
        _require_exact_keys(
            row,
            ROUND_CONTINUITY_KEYS,
            name=f"{lane} continuity round {expected_round}",
        )
        hashes = (
            row["prior_round_end_state_sha256"],
            row["round_start_state_sha256"],
            row["round_end_state_sha256"],
        )
        if (
            row["round_index"] != expected_round
            or any(not _is_sha256(value) for value in hashes)
            or row["round_start_state_sha256"]
            != row["prior_round_end_state_sha256"]
            or (
                previous_end is not None
                and row["prior_round_end_state_sha256"] != previous_end
            )
            or row["starts_from_prior_round_end"] is not True
            or row["candidate_restarted_between_rounds"] is not False
            or row["memory_reset_between_rounds"] is not False
        ):
            raise ValueError(
                f"{lane} candidate restart or memory reset continuity failed"
            )
        previous_end = row["round_end_state_sha256"]
        projected.append(dict(row))
    return projected


def _validate_dense_import_audit(audit: Any) -> None:
    expected = {
        "schema",
        "source_sha256",
        "forbidden_roots",
        "static_import_roots",
        "forbidden_static_import_roots",
        "newly_loaded_forbidden_modules",
        "forbidden_bound_global_modules",
        "scientific_dependency_roots",
        "passed",
    }
    _require_exact_keys(audit, expected, name="dense import audit")
    forbidden = [
        "error_coupling_simulator",
        "gcapeps",
        "quimb",
        "sdim",
        "stim",
    ]
    if (
        audit["schema"]
        != (
            "error_coupling_simulator.external.gcapeps_finite_memory."
            "dense_import_independence_audit.v1"
        )
        or not _is_sha256(audit["source_sha256"])
        or audit["forbidden_roots"] != forbidden
        or not isinstance(audit["static_import_roots"], list)
        or audit["forbidden_static_import_roots"] != []
        or audit["newly_loaded_forbidden_modules"] != []
        or audit["forbidden_bound_global_modules"] != []
        or audit["scientific_dependency_roots"]
        != ["numpy", "python_stdlib"]
        or audit["passed"] is not True
    ):
        raise ValueError("dense import independence audit failed")


def _validate_partial_swap_audit(audit: Any, *, gamma_hex: str) -> None:
    expected = {
        "schema",
        "gamma_float64_hex",
        "rotation_theta_float64_hex",
        "analytic_global_phase",
        "ordered_product_max_abs_errors",
        "sum_instead_of_product_max_abs_residual",
        "removed_global_phase_max_abs_residual",
        "opposite_rotation_sign_max_abs_residual",
        "corruption_minimum_residual",
        "phase_fit_used",
        "passed",
    }
    _require_exact_keys(audit, expected, name="partial-SWAP audit")
    errors = audit["ordered_product_max_abs_errors"]
    if not isinstance(errors, Mapping) or set(errors) != {
        "XYZ",
        "XZY",
        "YXZ",
        "YZX",
        "ZXY",
        "ZYX",
    }:
        raise ValueError("partial-SWAP permutation coverage failed")
    minimum = _finite_float(
        audit["corruption_minimum_residual"],
        name="partial-SWAP corruption minimum",
    )
    if (
        audit["schema"]
        != (
            "error_coupling_simulator.external.gcapeps_finite_memory."
            "partial_swap_factorization_audit.v1"
        )
        or audit["gamma_float64_hex"] != gamma_hex
        or audit["rotation_theta_float64_hex"]
        != float(-float.fromhex(gamma_hex)).hex()
        or audit["analytic_global_phase"] != "exp(-0.5j*gamma)"
        or any(
            abs(_finite_float(value, name="partial-SWAP product error"))
            > 1.0e-12
            for value in errors.values()
        )
        or minimum != 1.0e-2
        or any(
            _finite_float(audit[field], name=f"partial-SWAP {field}")
            <= minimum
            for field in (
                "sum_instead_of_product_max_abs_residual",
                "removed_global_phase_max_abs_residual",
                "opposite_rotation_sign_max_abs_residual",
            )
        )
        or audit["phase_fit_used"] is not False
        or audit["passed"] is not True
    ):
        raise ValueError("partial-SWAP algebra firewall failed")


def _validate_fixture_identity(
    fixture: Mapping[str, Any],
) -> dict[str, Any]:
    _require_exact_keys(
        fixture,
        {
            "schema",
            "script_revision",
            "fixture_id",
            "run_partition",
            "case_id",
            "claim_boundary",
            "geometry",
            "coordinate_convention",
            "mask_contract",
            "state_contract",
            "gate_definitions",
            "parameters",
            "inputs",
            "checkpoints",
            "carrier_path",
            "blpensemble",
            "sdim_pullback_requests",
            "result_projection_sha256",
        },
        name="neutral fixture",
    )
    fixture_hash = _validate_projection(fixture, name="neutral fixture")
    case_id = fixture["case_id"]
    run_partition = fixture["run_partition"]
    if (
        fixture["schema"] != FIXTURE_SCHEMA
        or fixture["script_revision"]
        != "gcapeps-finite-memory-neutral-fixture-v1"
        or not isinstance(case_id, str)
        or not case_id
        or fixture["fixture_id"] != case_id
        or run_partition not in {"CALIBRATION", "HELDOUT"}
    ):
        raise ValueError("neutral fixture identity mismatch")
    parameters = fixture["parameters"]
    _require_exact_keys(
        parameters,
        {
            "width",
            "rounds",
            "axis_family",
            "active_axes",
            "p_event_numerator",
            "p_event_denominator",
            "seed",
            "gamma_index",
            "gamma_label",
            "gamma_float64_hex",
            "theta_float64_hex",
            "max_bond",
        },
        name="fixture parameters",
    )
    width = _plain_int(parameters["width"], name="fixture width", minimum=1)
    rounds = _plain_int(
        parameters["rounds"], name="fixture rounds", minimum=1
    )
    if width not in (3, 5, 7) or parameters["max_bond"] != 32:
        raise ValueError("fixture width or max_bond is outside the frozen grid")
    geometry = fixture["geometry"]
    if (
        not isinstance(geometry, Mapping)
        or geometry.get("width") != width
        or geometry.get("n_qubits") != 2 * width
        or geometry.get("system_sites") != list(range(width))
        or geometry.get("memory_sites") != list(range(width, 2 * width))
    ):
        raise ValueError("fixture geometry identity mismatch")
    checkpoints = sorted({0, 1, 2, 4, rounds}.intersection(range(rounds + 1)))
    if fixture["checkpoints"] != checkpoints:
        raise ValueError("fixture candidate checkpoint identity mismatch")
    inputs = fixture["inputs"]
    if not isinstance(inputs, list) or len(inputs) != 2:
        raise ValueError("fixture must contain exactly two inputs")
    input_hashes: dict[int, str] = {}
    for expected_input, row in zip((1, 2), inputs, strict=True):
        if not isinstance(row, Mapping) or row.get("input_id") != expected_input:
            raise ValueError("fixture input order or identity mismatch")
        digest = row.get("input_preparation_transcript_sha256")
        if not _is_sha256(digest):
            raise ValueError("fixture input transcript hash is invalid")
        input_hashes[expected_input] = digest
    carrier_path = fixture["carrier_path"]
    if not isinstance(carrier_path, Mapping):
        raise TypeError("fixture carrier_path must be an object")
    shared_hash = carrier_path.get("shared_evolution_transcript_sha256")
    if not _is_sha256(shared_hash):
        raise ValueError("fixture shared evolution hash is invalid")
    operations = _fixture_operation_sequence(
        carrier_path,
        rounds=rounds,
        width=width,
    )
    expected_keys = _request_sequence(
        fixture["sdim_pullback_requests"],
        width=width,
        run_partition=run_partition,
        case_id=case_id,
        input_hashes=input_hashes,
        shared_evolution_sha256=shared_hash,
        exact_keys=REQUEST_KEY_SET,
        name="fixture E rows",
    )
    return {
        "fixture_projection_sha256": fixture_hash,
        "case_id": case_id,
        "run_partition": run_partition,
        "width": width,
        "rounds": rounds,
        "n_qubits": 2 * width,
        "checkpoints": checkpoints,
        "input_hashes": input_hashes,
        "shared_evolution_sha256": shared_hash,
        "expected_keys": expected_keys,
        "operations": operations,
    }


def _validate_dense_checkpoint(
    checkpoint: Mapping[str, Any],
    *,
    width: int,
    round_index: int,
    sampler: ComparatorArraySampler,
) -> dict[str, Any]:
    """Recompute every registered entropy diagnostic from the raw vector."""

    _require_exact_keys(
        checkpoint,
        {
            "round_index",
            "vector",
            "raw_vector_guard",
            "reduced_state",
            "hermiticity_residual",
            "trace_residual",
            "hermitization_correction",
            "raw_eigenvalues",
            "minimum_raw_eigenvalue",
            "negative_eigenvalue_mass",
            "eigenpair_residual",
            "reconstruction_residual",
            "clipped_eigenvalue_sum",
            "eigenvalue_renormalization_factor",
            "normalized_eigenvalues",
            "entropy_s1",
            "entropy_s2",
            "normalized_schmidt_values",
            "numerical_schmidt_rank",
        },
        name=f"dense checkpoint {round_index}",
    )
    if checkpoint["round_index"] != round_index:
        raise ValueError("dense checkpoint order mismatch")
    state_dimension = 2 ** (2 * width)
    system_dimension = 2**width
    vector = decode_ndarray_v1(
        checkpoint["vector"],
        dtype="<c16",
        shape=(state_dimension,),
        sampler=sampler,
    )
    gate = vector_gate(vector, width=width, sampler=sampler)
    guard = checkpoint["raw_vector_guard"]
    expected_guard = {
        "vector_data_sha256": gate["raw_vector_sha256"],
        "norm_squared_real": gate["raw_norm_squared_real"],
        "norm_squared_imaginary_abs": gate["raw_norm_squared_imag_abs"],
        "norm": gate["raw_norm"],
        "stored_vector_normalized_before_metric": False,
        "metric_local_normalized_copy": True,
        "phase_fit": False,
        "coordinate_permutation": False,
        "dtype_cast": False,
    }
    _require_exact_keys(guard, expected_guard, name="dense raw vector guard")
    scalar_guard_fields = {
        "norm_squared_real",
        "norm_squared_imaginary_abs",
        "norm",
    }
    if any(
        not math.isclose(
            _finite_float(guard[field], name=f"dense guard {field}"),
            expected_guard[field],
            rel_tol=1.0e-12,
            abs_tol=1.0e-12,
        )
        for field in scalar_guard_fields
    ) or any(
        guard[field] != expected_guard[field]
        for field in set(expected_guard) - scalar_guard_fields
    ):
        raise ValueError("dense raw vector gate metadata mismatch")

    reduced = decode_ndarray_v1(
        checkpoint["reduced_state"],
        dtype="<c16",
        shape=(system_dimension, system_dimension),
        sampler=sampler,
    )
    raw_eigenvalues = decode_ndarray_v1(
        checkpoint["raw_eigenvalues"],
        dtype="<f8",
        shape=(system_dimension,),
        sampler=sampler,
    )
    normalized_eigenvalues = decode_ndarray_v1(
        checkpoint["normalized_eigenvalues"],
        dtype="<f8",
        shape=(system_dimension,),
        sampler=sampler,
    )
    schmidt = decode_ndarray_v1(
        checkpoint["normalized_schmidt_values"],
        dtype="<f8",
        shape=(system_dimension,),
        sampler=sampler,
    )
    rho_h = np.ascontiguousarray(
        (gate["rho_system"] + gate["rho_system"].conjugate().T) / 2.0,
        dtype=np.complex128,
    )
    recomputed_raw_eigenvalues = np.ascontiguousarray(
        np.linalg.eigvalsh(rho_h), dtype=np.float64
    )
    clipped = np.ascontiguousarray(
        np.maximum(recomputed_raw_eigenvalues, 0.0), dtype=np.float64
    )
    recomputed_normalized = np.ascontiguousarray(
        clipped / float(clipped.sum()), dtype=np.float64
    )
    _arrays_materialized(
        sampler,
        rho_h,
        recomputed_raw_eigenvalues,
        clipped,
        recomputed_normalized,
    )
    scalar_fields = {
        "hermiticity_residual": gate["rho_hermiticity_residual"],
        "trace_residual": gate["rho_trace_residual"],
        "hermitization_correction": gate["rho_hermitization_correction"],
        "minimum_raw_eigenvalue": gate["rho_minimum_eigenvalue"],
        "negative_eigenvalue_mass": gate["rho_negative_mass"],
        "eigenpair_residual": gate["rho_eigenpair_residual"],
        "reconstruction_residual": gate["rho_reconstruction_residual"],
        "clipped_eigenvalue_sum": gate["rho_clipped_sum"],
        "eigenvalue_renormalization_factor": gate[
            "rho_eigenvalue_renormalization_factor"
        ],
        "entropy_s1": gate["entropy_von_neumann"],
        "entropy_s2": gate["entropy_renyi2"],
    }
    scalar_mismatch = any(
        not math.isclose(
            _finite_float(checkpoint[field], name=f"dense {field}"),
            expected,
            rel_tol=1.0e-12,
            abs_tol=1.0e-12,
        )
        for field, expected in scalar_fields.items()
    )
    if (
        scalar_mismatch
        or not np.allclose(
            reduced,
            gate["rho_system"],
            rtol=1.0e-12,
            atol=1.0e-12,
        )
        or not np.allclose(
            raw_eigenvalues,
            recomputed_raw_eigenvalues,
            rtol=1.0e-12,
            atol=1.0e-12,
        )
        or not np.allclose(
            normalized_eigenvalues,
            recomputed_normalized,
            rtol=1.0e-12,
            atol=1.0e-12,
        )
        or not np.allclose(
            schmidt,
            gate["normalized_schmidt_values"],
            rtol=1.0e-12,
            atol=1.0e-12,
        )
        or checkpoint["numerical_schmidt_rank"]
        != gate["numerical_schmidt_rank"]
    ):
        raise ValueError("dense checkpoint diagnostics disagree with raw vector")
    _arrays_released(
        sampler,
        reduced,
        raw_eigenvalues,
        normalized_eigenvalues,
        schmidt,
        rho_h,
        recomputed_raw_eigenvalues,
        clipped,
        recomputed_normalized,
    )
    return {
        "vector": vector,
        "rho_system": gate["rho_system"],
        "entropy_s1": gate["entropy_von_neumann"],
        "entropy_s2": gate["entropy_renyi2"],
        "normalized_schmidt_values": gate[
            "normalized_schmidt_values"
        ],
        "numerical_schmidt_rank": gate["numerical_schmidt_rank"],
    }



_DENSE_PATH_KEYS = frozenset(
    {
        "namespace",
        "mask_index",
        "input_id",
        "preparation",
        "persistent_memory_across_rounds",
        "checkpoints",
        "mask_rows",
        "event_bits",
        "eligible_collision_count",
        "realized_event_count",
        "active_axis_rotation_count",
        "physical_operation_count",
    }
)
_BLP_KEYS = frozenset(
    {
        "object",
        "trace_distances",
        "increments",
        "summed_positive_increments",
        "maximum_increment",
        "witness_threshold",
        "verdict",
        "difference_eigenvalues_by_round",
    }
)


def _trace_distance_spectrum(
    rho_left: np.ndarray,
    rho_right: np.ndarray,
    *,
    sampler: ComparatorArraySampler,
) -> tuple[float, np.ndarray]:
    difference = np.ascontiguousarray(
        (
            (rho_left + rho_left.conjugate().T)
            - (rho_right + rho_right.conjugate().T)
        )
        / 2.0,
        dtype=np.complex128,
    )
    spectrum = np.ascontiguousarray(
        np.linalg.eigvalsh(difference), dtype=np.float64
    )
    _arrays_materialized(sampler, difference, spectrum)
    value = float(0.5 * np.sum(np.abs(spectrum)))
    if not math.isfinite(value) or value < 0.0:
        raise ValueError("dense BLP trace distance is invalid")
    _arrays_released(sampler, difference)
    return value, spectrum


def _recomputed_blp(
    distances: Sequence[float],
    spectra: Sequence[np.ndarray],
    *,
    ensemble: bool,
) -> dict[str, Any]:
    if len(distances) < 2 or len(spectra) != len(distances):
        raise ValueError("dense BLP trajectory cardinality is invalid")
    if abs(distances[0] - 1.0) > TRACE_TOLERANCE:
        raise ValueError("initial dense BLP trace distance is not one")
    increments = [
        float(distances[index] - distances[index - 1])
        for index in range(1, len(distances))
    ]
    maximum = max(increments)
    witnessed = maximum > BLP_INCREMENT_TOLERANCE
    if ensemble:
        object_name = "finite_32_mask_ensemble"
        verdict = (
            "BLP_WITNESSED_FINITE_32_MASK_ENSEMBLE"
            if witnessed
            else "NO_WITNESS_FINITE_32_MASK_ENSEMBLE_FOR_REGISTERED_PAIR"
        )
    else:
        object_name = "fixed_carrier_mask"
        verdict = (
            "BLP_WITNESSED_FIXED_MASK"
            if witnessed
            else "NO_WITNESS_FIXED_MASK_FOR_REGISTERED_PAIR"
        )
    return {
        "object": object_name,
        "trace_distances": list(distances),
        "increments": increments,
        "summed_positive_increments": float(
            math.fsum(max(0.0, value) for value in increments)
        ),
        "maximum_increment": maximum,
        "witness_threshold": BLP_INCREMENT_TOLERANCE,
        "verdict": verdict,
        "difference_eigenvalues_by_round": [
            spectrum.tolist() for spectrum in spectra
        ],
    }


def _float_sequence_equal(
    observed: Any,
    expected: Sequence[float],
    *,
    name: str,
) -> None:
    if not isinstance(observed, list) or len(observed) != len(expected):
        raise ValueError(f"{name} cardinality mismatch")
    for index, (left, right) in enumerate(
        zip(observed, expected, strict=True)
    ):
        if not math.isclose(
            _finite_float(left, name=f"{name}[{index}]"),
            right,
            rel_tol=1.0e-12,
            abs_tol=1.0e-12,
        ):
            raise ValueError(f"{name} disagrees with raw dense states")


def _validate_reported_blp(
    reported: Mapping[str, Any],
    recomputed: Mapping[str, Any],
    *,
    system_dimension: int,
    sampler: ComparatorArraySampler,
    name: str,
) -> None:
    _require_exact_keys(reported, _BLP_KEYS, name=name)
    for field in ("object", "verdict"):
        if reported[field] != recomputed[field]:
            raise ValueError(f"{name} {field} disagrees with recomputation")
    _float_sequence_equal(
        reported["trace_distances"],
        recomputed["trace_distances"],
        name=f"{name} trace_distances",
    )
    _float_sequence_equal(
        reported["increments"],
        recomputed["increments"],
        name=f"{name} increments",
    )
    for field in (
        "summed_positive_increments",
        "maximum_increment",
        "witness_threshold",
    ):
        if not math.isclose(
            _finite_float(reported[field], name=f"{name} {field}"),
            recomputed[field],
            rel_tol=1.0e-12,
            abs_tol=1.0e-12,
        ):
            raise ValueError(f"{name} {field} disagrees with recomputation")
    encoded_spectra = reported["difference_eigenvalues_by_round"]
    expected_spectra = recomputed["difference_eigenvalues_by_round"]
    if not isinstance(encoded_spectra, list) or len(encoded_spectra) != len(
        expected_spectra
    ):
        raise ValueError(f"{name} difference spectra cardinality mismatch")
    for round_index, (encoded, expected) in enumerate(
        zip(encoded_spectra, expected_spectra, strict=True)
    ):
        decoded = decode_ndarray_v1(
            encoded,
            dtype="<f8",
            shape=(system_dimension,),
            sampler=sampler,
        )
        if not np.allclose(
            decoded,
            np.asarray(expected, dtype=np.float64),
            rtol=1.0e-12,
            atol=1.0e-12,
        ):
            raise ValueError(
                f"{name} difference spectrum {round_index} disagrees"
            )
        _arrays_released(sampler, decoded)


def _fixture_path(
    fixture: Mapping[str, Any],
    *,
    namespace: str,
    mask_index: int,
) -> Mapping[str, Any]:
    if namespace == "CARRIER":
        if mask_index != 0:
            raise ValueError("CARRIER mask index must be zero")
        return fixture["carrier_path"]
    matches = [
        path
        for path in fixture["blpensemble"]["paths"]
        if path.get("mask_index") == mask_index
    ]
    if len(matches) != 1:
        raise ValueError("fixture BLPENSEMBLE mask identity is not unique")
    return matches[0]


def _project_fixture_mask_rows(
    fixture: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
    namespace: str,
    mask_index: int,
) -> list[dict[str, Any]]:
    path = _fixture_path(
        fixture,
        namespace=namespace,
        mask_index=mask_index,
    )
    parameters = fixture["parameters"]
    return [
        {
            "namespace": namespace,
            "seed": parameters["seed"],
            "mask_index": mask_index,
            "width": identity["width"],
            "round_index": row["round_index"],
            "site_index": row["site_index"],
            "probability_numerator": parameters["p_event_numerator"],
            "probability_denominator": 4,
            "payload_hex": row["payload_hex"],
            "digest_sha256": row["payload_sha256"],
            "h64": row["h64"],
            "event": row["event"],
        }
        for row in path["event_rows"]
    ]


def _validate_dense_path(
    path: Mapping[str, Any],
    *,
    fixture: Mapping[str, Any],
    identity: Mapping[str, Any],
    namespace: str,
    mask_index: int,
    input_id: int,
    sampler: ComparatorArraySampler,
) -> list[dict[str, Any]]:
    name = f"dense {namespace} mask{mask_index} input{input_id} path"
    _require_exact_keys(path, _DENSE_PATH_KEYS, name=name)
    expected_path = _fixture_path(
        fixture, namespace=namespace, mask_index=mask_index
    )
    expected_rows = _project_fixture_mask_rows(
        fixture,
        identity=identity,
        namespace=namespace,
        mask_index=mask_index,
    )
    expected_bits = [row["event"] for row in expected_rows]
    expected_operations = [
        operation
        for round_row in expected_path["round_ledger"]
        for operation in round_row["operations"]
    ]
    expected_rotations = sum(
        operation["gate_kind"] == "PAULI_ROTATION"
        for operation in expected_operations
    )
    expected_preparation = (
        "all_zero_product"
        if input_id == 1
        else f"central_system_X_q{identity['width'] // 2}"
    )
    if (
        path["namespace"] != namespace
        or path["mask_index"] != mask_index
        or path["input_id"] != input_id
        or path["preparation"] != expected_preparation
        or path["persistent_memory_across_rounds"] is not True
        or path["mask_rows"] != expected_rows
        or path["event_bits"] != expected_bits
        or path["eligible_collision_count"]
        != identity["width"] * identity["rounds"]
        or path["realized_event_count"] != sum(expected_bits)
        or path["active_axis_rotation_count"] != expected_rotations
        or path["physical_operation_count"] != len(expected_operations)
    ):
        raise ValueError(f"{name} metadata disagrees with neutral fixture")
    checkpoints = path["checkpoints"]
    if not isinstance(checkpoints, list) or len(checkpoints) != (
        identity["rounds"] + 1
    ):
        raise ValueError(f"{name} lacks every-round checkpoints")
    return [
        _validate_dense_checkpoint(
            checkpoint,
            width=identity["width"],
            round_index=round_index,
            sampler=sampler,
        )
        for round_index, checkpoint in enumerate(checkpoints)
    ]


def _validate_average_density_matrix(
    rho: np.ndarray,
    *,
    sampler: ComparatorArraySampler,
) -> None:
    hermiticity = float(
        np.max(np.abs(rho - rho.conjugate().T), initial=0.0)
    )
    trace_residual = float(abs(np.trace(rho) - 1.0))
    rho_h = np.ascontiguousarray(
        (rho + rho.conjugate().T) / 2.0, dtype=np.complex128
    )
    eigenvalues, eigenvectors = np.linalg.eigh(rho_h)
    reconstructed = (eigenvectors * eigenvalues[np.newaxis, :]) @ (
        eigenvectors.conjugate().T
    )
    _arrays_materialized(
        sampler, rho_h, eigenvalues, eigenvectors, reconstructed
    )
    reconstruction = float(
        np.max(np.abs(rho_h - reconstructed), initial=0.0)
    )
    if (
        hermiticity > HERMITICITY_TOLERANCE
        or trace_residual > TRACE_TOLERANCE
        or float(np.min(eigenvalues)) < -NEGATIVE_MASS_TOLERANCE
        or reconstruction > EIGEN_RESIDUAL_TOLERANCE
    ):
        raise ValueError("finite-32 average reduced state failed metric gates")
    _arrays_released(
        sampler, rho_h, eigenvalues, eigenvectors, reconstructed
    )


def _entropy_projection(
    checkpoints: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    entropy_s1 = [float(row["entropy_s1"]) for row in checkpoints]
    entropy_s2 = [float(row["entropy_s2"]) for row in checkpoints]
    increments = [
        float(entropy_s1[index] - entropy_s1[index - 1])
        for index in range(1, len(entropy_s1))
    ]
    negative_rows = [
        {"round_index": index, "increment": value}
        for index, value in enumerate(increments, start=1)
        if value < 0.0
    ]
    revival_rows = [
        {"round_index": index, "increment": value}
        for index, value in enumerate(increments, start=1)
        if value > 0.0
    ]
    terminal_minus_round1 = float(entropy_s1[-1] - entropy_s1[1])
    return {
        "source": "exact_dense_fixed_carrier_input1",
        "candidate_values_consumed": False,
        "round_indices": list(range(len(checkpoints))),
        "entropy_von_neumann": entropy_s1,
        "entropy_renyi2": entropy_s2,
        "normalized_schmidt_values_by_round": [
            row["normalized_schmidt_values"].tolist()
            for row in checkpoints
        ],
        "numerical_schmidt_rank_by_round": [
            row["numerical_schmidt_rank"] for row in checkpoints
        ],
        "entropy_von_neumann_increments": increments,
        "negative_increment_rows": negative_rows,
        "revival_rows": revival_rows,
        "maximum_entropy_von_neumann": max(entropy_s1),
        "terminal_entropy_von_neumann": entropy_s1[-1],
        "round1_entropy_von_neumann": entropy_s1[1],
        "terminal_minus_round1": terminal_minus_round1,
        "h_e_strict_threshold": ENTANGLEMENT_HYPOTHESIS_TOLERANCE,
        "h_e_condition_holds": (
            terminal_minus_round1 > ENTANGLEMENT_HYPOTHESIS_TOLERANCE
        ),
        "conditional_h_e_verdict_if_amendment_bound_stress_cell": (
            "supported"
            if terminal_minus_round1 > ENTANGLEMENT_HYPOTHESIS_TOLERANCE
            else "falsified"
        ),
        "h_e_applicability_deferred_to_amendment_bound_stress_cell": True,
    }


def _validate_p_event_zero_control(
    reported: Any,
    *,
    probability_numerator: int,
    fixed_blp: Mapping[str, Any],
    ensemble_blp: Mapping[str, Any] | None,
    every_event_false: bool,
    active_axis_rotation_count: int,
    maximum_entropy: float,
) -> dict[str, Any] | None:
    if probability_numerator != 0:
        if reported is not None:
            raise ValueError("nonzero-p dense core emitted p_event_zero_control")
        return None
    fixed_unit = all(
        abs(value - 1.0) <= TRACE_TOLERANCE
        for value in fixed_blp["trace_distances"]
    )
    ensemble_unit = True
    ensemble_increment = True
    if ensemble_blp is not None:
        ensemble_unit = all(
            abs(value - 1.0) <= TRACE_TOLERANCE
            for value in ensemble_blp["trace_distances"]
        )
        ensemble_increment = (
            ensemble_blp["maximum_increment"] <= BLP_INCREMENT_TOLERANCE
        )
    recomputed = {
        "every_event_bit_structural_false": every_event_false,
        "active_axis_rotation_count": active_axis_rotation_count,
        "all_system_memory_s1_s2_at_most_1e_12": (
            maximum_entropy <= HERMITICITY_TOLERANCE
        ),
        "fixed_trace_distance_one_within_1e_12": fixed_unit,
        "fixed_named_increment_at_most_1e_10": (
            fixed_blp["maximum_increment"] <= BLP_INCREMENT_TOLERANCE
        ),
        "ensemble_trace_distance_one_within_1e_12": ensemble_unit,
        "ensemble_named_increment_at_most_1e_10": ensemble_increment,
        "passed": False,
    }
    recomputed["passed"] = bool(
        recomputed["every_event_bit_structural_false"]
        and recomputed["active_axis_rotation_count"] == 0
        and recomputed["all_system_memory_s1_s2_at_most_1e_12"]
        and recomputed["fixed_trace_distance_one_within_1e_12"]
        and recomputed["fixed_named_increment_at_most_1e_10"]
        and recomputed["ensemble_trace_distance_one_within_1e_12"]
        and recomputed["ensemble_named_increment_at_most_1e_10"]
    )
    if not isinstance(reported, Mapping):
        raise ValueError("p_event=0 control is missing")
    _require_exact_keys(reported, set(recomputed), name="p_event_zero_control")
    if reported != recomputed or recomputed["passed"] is not True:
        raise ValueError("p_event=0 structural negative control failed")
    return recomputed


def _validate_dense_ensemble(
    ensemble: Any,
    *,
    fixture: Mapping[str, Any],
    identity: Mapping[str, Any],
    sampler: ComparatorArraySampler,
) -> dict[str, Any] | None:
    enabled = fixture["blpensemble"]["enabled"]
    if not enabled:
        if ensemble is not None:
            raise ValueError("dense core emitted an unregistered finite ensemble")
        return None
    if not isinstance(ensemble, Mapping):
        raise ValueError("registered finite-32 ensemble is missing")
    _require_exact_keys(
        ensemble,
        {
            "weights",
            "paths",
            "average_reduced_states",
            "blp",
            "aggregation_order",
            "path_deduplication",
        },
        name="finite_32_mask_ensemble",
    )
    weights = ensemble["weights"]
    if (
        not isinstance(weights, list)
        or len(weights) != 32
        or any(
            not math.isclose(
                _finite_float(value, name="finite ensemble weight"),
                1.0 / 32.0,
                rel_tol=0.0,
                abs_tol=0.0,
            )
            for value in weights
        )
        or ensemble["aggregation_order"]
        != "average_density_matrices_before_trace_distance"
        or ensemble["path_deduplication"] is not False
    ):
        raise ValueError("finite-32 ensemble aggregation policy drifted")
    paths = ensemble["paths"]
    if not isinstance(paths, list) or len(paths) != 64:
        raise ValueError("finite-32 ensemble must contain 64 input paths")
    rounds = identity["rounds"]
    system_dimension = 2 ** identity["width"]
    accumulators = {
        input_id: [
            np.zeros(
                (system_dimension, system_dimension),
                dtype=np.complex128,
                order="C",
            )
            for _ in range(rounds + 1)
        ]
        for input_id in (1, 2)
    }
    _arrays_materialized(
        sampler,
        *[
            rho
            for rows in accumulators.values()
            for rho in rows
        ],
    )
    maximum_entropy = 0.0
    every_event_false = True
    active_rotation_count = 0
    expected_index = 0
    for mask_index in range(32):
        for input_id in (1, 2):
            path = paths[expected_index]
            expected_index += 1
            diagnostics = _validate_dense_path(
                path,
                fixture=fixture,
                identity=identity,
                namespace="BLPENSEMBLE",
                mask_index=mask_index,
                input_id=input_id,
                sampler=sampler,
            )
            every_event_false = every_event_false and not any(
                path["event_bits"]
            )
            active_rotation_count += path["active_axis_rotation_count"]
            for round_index, diagnostic in enumerate(diagnostics):
                maximum_entropy = max(
                    maximum_entropy,
                    float(diagnostic["entropy_s1"]),
                    float(diagnostic["entropy_s2"]),
                )
                predecessor = accumulators[input_id][round_index]
                candidate = np.ascontiguousarray(
                    predecessor + diagnostic["rho_system"],
                    dtype=np.complex128,
                )
                _arrays_materialized(sampler, candidate)
                _arrays_released(sampler, predecessor)
                accumulators[input_id][round_index] = candidate
                _arrays_released(
                    sampler,
                    diagnostic["vector"],
                    diagnostic["rho_system"],
                    diagnostic["normalized_schmidt_values"],
                )
    averages: dict[int, list[np.ndarray]] = {1: [], 2: []}
    for input_id in (1, 2):
        for accumulator in accumulators[input_id]:
            average = np.ascontiguousarray(
                accumulator / 32.0, dtype=np.complex128
            )
            _arrays_materialized(sampler, average)
            _arrays_released(sampler, accumulator)
            _validate_average_density_matrix(average, sampler=sampler)
            averages[input_id].append(average)
    reported_averages = ensemble["average_reduced_states"]
    _require_exact_keys(
        reported_averages,
        {"input_1", "input_2"},
        name="finite ensemble average states",
    )
    for input_id in (1, 2):
        rows = reported_averages[f"input_{input_id}"]
        if not isinstance(rows, list) or len(rows) != rounds + 1:
            raise ValueError("finite ensemble average trajectory is incomplete")
        for round_index, (encoded, average) in enumerate(
            zip(rows, averages[input_id], strict=True)
        ):
            decoded = decode_ndarray_v1(
                encoded,
                dtype="<c16",
                shape=(system_dimension, system_dimension),
                sampler=sampler,
            )
            _validate_average_density_matrix(decoded, sampler=sampler)
            if not np.allclose(
                decoded,
                average,
                rtol=1.0e-12,
                atol=1.0e-12,
            ):
                raise ValueError(
                    "finite ensemble average reduced state disagrees "
                    f"at input {input_id}, round {round_index}"
                )
            _arrays_released(sampler, decoded)
    distances: list[float] = []
    spectra: list[np.ndarray] = []
    for left, right in zip(averages[1], averages[2], strict=True):
        distance, spectrum = _trace_distance_spectrum(
            left, right, sampler=sampler
        )
        distances.append(distance)
        spectra.append(spectrum)
    recomputed = _recomputed_blp(distances, spectra, ensemble=True)
    _validate_reported_blp(
        ensemble["blp"],
        recomputed,
        system_dimension=system_dimension,
        sampler=sampler,
        name="finite_32_mask_ensemble BLP",
    )
    _arrays_released(
        sampler,
        *averages[1],
        *averages[2],
        *spectra,
    )
    return {
        "blp": recomputed,
        "maximum_entropy": maximum_entropy,
        "every_event_false": every_event_false,
        "active_axis_rotation_count": active_rotation_count,
    }


def _validate_dense_core(
    dense_core: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
    fixture: Mapping[str, Any],
    sampler: ComparatorArraySampler,
) -> tuple[
    str,
    dict[int, dict[int, np.ndarray]],
    dict[str, Any],
]:
    """Validate dense raw evidence and retain only candidate-checkpoint vectors."""

    _require_exact_keys(
        dense_core,
        {
            "schema",
            "run_partition",
            "case_id",
            "coordinate_order",
            "system_axes",
            "memory_axes",
            "width",
            "rounds",
            "axis_family",
            "active_axes",
            "p_event_numerator",
            "p_event_denominator",
            "gamma_float64_hex",
            "theta_float64_hex",
            "seed",
            "fixed_mask",
            "fixed_paths",
            "fixed_blp",
            "finite_32_mask_ensemble",
            "p_event_zero_control",
            "max_sampled_dense_reference_array_bytes",
            "final_dense_reference_array_bytes",
            "scientific_dependencies",
            "import_independence_audit",
            "imports_candidate_or_simulator_helper",
            "partial_swap_factorization_audit",
            "claim_boundary",
            "result_projection_sha256",
        },
        name="dense core",
    )
    digest = _validate_projection(dense_core, name="dense core")
    parameters = fixture["parameters"]
    width = identity["width"]
    if (
        dense_core["schema"] != DENSE_SCHEMA
        or dense_core["run_partition"] != identity["run_partition"]
        or dense_core["case_id"] != identity["case_id"]
        or dense_core["coordinate_order"] != "q0_most_significant_bit"
        or dense_core["system_axes"] != list(range(width))
        or dense_core["memory_axes"] != list(range(width, 2 * width))
        or dense_core["width"] != width
        or dense_core["rounds"] != identity["rounds"]
        or dense_core["axis_family"] != parameters["axis_family"]
        or dense_core["active_axes"] != parameters["active_axes"]
        or dense_core["p_event_numerator"]
        != parameters["p_event_numerator"]
        or dense_core["p_event_denominator"] != 4
        or dense_core["gamma_float64_hex"]
        != parameters["gamma_float64_hex"]
        or dense_core["theta_float64_hex"]
        != parameters["theta_float64_hex"]
        or dense_core["seed"] != parameters["seed"]
        or dense_core["scientific_dependencies"]
        != ["numpy", "python_stdlib"]
        or dense_core["imports_candidate_or_simulator_helper"] is not False
        or dense_core["claim_boundary"]
        != "independent_exact_dense_reference_for_frozen_finite_memory_fixture"
    ):
        raise ValueError("dense core identity mismatch")
    maximum_reference_bytes = _plain_int(
        dense_core["max_sampled_dense_reference_array_bytes"],
        name="max_sampled_dense_reference_array_bytes",
        minimum=1,
    )
    final_reference_bytes = _plain_int(
        dense_core["final_dense_reference_array_bytes"],
        name="final_dense_reference_array_bytes",
        minimum=1,
    )
    if final_reference_bytes > maximum_reference_bytes:
        raise ValueError("dense final array bytes exceed the sampled maximum")
    _validate_dense_import_audit(dense_core["import_independence_audit"])
    _validate_partial_swap_audit(
        dense_core["partial_swap_factorization_audit"],
        gamma_hex=parameters["gamma_float64_hex"],
    )

    fixed_mask = dense_core["fixed_mask"]
    _require_exact_keys(
        fixed_mask,
        {"namespace", "mask_index", "rows", "payload_sequence_sha256"},
        name="dense fixed mask",
    )
    expected_rows = _project_fixture_mask_rows(
        fixture,
        identity=identity,
        namespace="CARRIER",
        mask_index=0,
    )
    expected_payload_sha256 = hashlib.sha256(
        b"".join(bytes.fromhex(row["payload_hex"]) for row in expected_rows)
    ).hexdigest()
    if (
        fixed_mask["namespace"] != "CARRIER"
        or fixed_mask["mask_index"] != 0
        or fixed_mask["rows"] != expected_rows
        or fixed_mask["payload_sequence_sha256"]
        != expected_payload_sha256
    ):
        raise ValueError("dense fixed-mask identity mismatch")

    paths = dense_core["fixed_paths"]
    if not isinstance(paths, list) or len(paths) != 2:
        raise ValueError("dense fixed paths must contain exactly two inputs")
    fixed_diagnostics: dict[int, list[dict[str, Any]]] = {}
    for expected_input, path in zip((1, 2), paths, strict=True):
        if not isinstance(path, Mapping):
            raise TypeError("dense fixed path must be an object")
        fixed_diagnostics[expected_input] = _validate_dense_path(
            path,
            fixture=fixture,
            identity=identity,
            namespace="CARRIER",
            mask_index=0,
            input_id=expected_input,
            sampler=sampler,
        )

    system_dimension = 2**width
    fixed_distances: list[float] = []
    fixed_spectra: list[np.ndarray] = []
    for left, right in zip(
        fixed_diagnostics[1], fixed_diagnostics[2], strict=True
    ):
        distance, spectrum = _trace_distance_spectrum(
            left["rho_system"], right["rho_system"], sampler=sampler
        )
        fixed_distances.append(distance)
        fixed_spectra.append(spectrum)
    fixed_blp = _recomputed_blp(
        fixed_distances,
        fixed_spectra,
        ensemble=False,
    )
    if not isinstance(dense_core["fixed_blp"], Mapping):
        raise TypeError("dense fixed BLP must be an object")
    _validate_reported_blp(
        dense_core["fixed_blp"],
        fixed_blp,
        system_dimension=system_dimension,
        sampler=sampler,
        name="fixed-mask BLP",
    )

    entropy = _entropy_projection(fixed_diagnostics[1])
    fixed_maximum_entropy = max(
        max(float(row["entropy_s1"]), float(row["entropy_s2"]))
        for diagnostics in fixed_diagnostics.values()
        for row in diagnostics
    )
    every_event_false = all(
        not event for path in paths for event in path["event_bits"]
    )
    active_rotation_count = sum(
        int(path["active_axis_rotation_count"]) for path in paths
    )
    ensemble_result = _validate_dense_ensemble(
        dense_core["finite_32_mask_ensemble"],
        fixture=fixture,
        identity=identity,
        sampler=sampler,
    )
    ensemble_blp = None if ensemble_result is None else ensemble_result["blp"]
    maximum_entropy = fixed_maximum_entropy
    if ensemble_result is not None:
        maximum_entropy = max(
            maximum_entropy,
            float(ensemble_result["maximum_entropy"]),
        )
        every_event_false = (
            every_event_false and ensemble_result["every_event_false"]
        )
        active_rotation_count += int(
            ensemble_result["active_axis_rotation_count"]
        )
    control = _validate_p_event_zero_control(
        dense_core["p_event_zero_control"],
        probability_numerator=parameters["p_event_numerator"],
        fixed_blp=fixed_blp,
        ensemble_blp=ensemble_blp,
        every_event_false=every_event_false,
        active_axis_rotation_count=active_rotation_count,
        maximum_entropy=maximum_entropy,
    )
    witnesses = {
        "fixed_blp": fixed_blp,
        "finite_32_mask_ensemble_blp": ensemble_blp,
        "p_event_zero_control": control,
        "trajectory1_entanglement": entropy,
    }

    vectors: dict[int, dict[int, np.ndarray]] = {1: {}, 2: {}}
    retained_rounds = set(identity["checkpoints"])
    for input_id, diagnostics in fixed_diagnostics.items():
        for round_index, diagnostic in enumerate(diagnostics):
            vector = diagnostic["vector"]
            if round_index in retained_rounds:
                vectors[input_id][round_index] = vector
            else:
                _arrays_released(sampler, vector)
            _arrays_released(
                sampler,
                diagnostic["rho_system"],
                diagnostic["normalized_schmidt_values"],
            )
    _arrays_released(sampler, *fixed_spectra)
    return digest, vectors, witnesses


def _validate_candidate_pre_metric(
    pre_metric: Mapping[str, Any],
    *,
    gate: Mapping[str, Any],
    lane: str,
    input_id: int,
    round_index: int,
) -> None:
    name = f"{lane} input{input_id} checkpoint {round_index} pre_metric"
    _require_exact_keys(pre_metric, PRE_METRIC_KEYS, name=name)
    expected = {
        "raw_vector_sha256": gate["raw_vector_sha256"],
        "raw_norm_squared_real": gate["raw_norm_squared_real"],
        "raw_norm_squared_imag_abs": gate["raw_norm_squared_imag_abs"],
        "stored_vector_normalized_before_metric": False,
        "metric_local_normalized_copy": True,
        "phase_fit": False,
        "coordinate_permutation": False,
        "dtype_cast": False,
    }
    scalar_fields = {
        "raw_norm_squared_real",
        "raw_norm_squared_imag_abs",
    }
    if any(
        not math.isclose(
            _finite_float(pre_metric[field], name=f"{name}.{field}"),
            expected[field],
            rel_tol=1.0e-12,
            abs_tol=1.0e-12,
        )
        for field in scalar_fields
    ) or any(
        pre_metric[field] != expected[field]
        for field in set(expected) - scalar_fields
    ):
        raise ValueError(f"{name} disagrees with the transported raw vector")


def _split_event_projection(
    row: Mapping[str, Any],
    *,
    lane: str,
    row_index: int,
    operation: Mapping[str, Any],
    gc_algorithm_row: Mapping[str, Any] | None,
    sampler: ComparatorArraySampler,
) -> tuple[bool, dict[str, Any] | None]:
    expected_keys = PLAIN_SPLIT_KEYS if lane == "plain" else GC_SPLIT_KEYS
    _require_exact_keys(
        row,
        expected_keys,
        name=f"{lane} split row {row_index}",
    )
    operation_index = _plain_int(
        row["operation_index"],
        name=f"{lane} split operation_index",
    )
    round_index = _plain_int(
        row["round_index"],
        name=f"{lane} split round_index",
        minimum=1,
    )
    if (
        operation_index != operation["operation_index"]
        or round_index != operation["round_index"]
        or row["collision_ordinal"] != operation.get("collision_ordinal")
    ):
        raise ValueError(
            f"{lane} split row {row_index} does not join its fixture operation"
        )
    producer_projection = dict(row)
    producer_binding = producer_projection.pop(
        "spectrum_producer_binding_sha256"
    )
    expected_binding = hashlib.sha256(
        canonical_json_bytes(
            {
                "schema": (
                    "error_coupling_simulator.external."
                    "gcapeps_finite_memory.split_spectrum_producer.v1"
                ),
                "lane": lane,
                "split_row": producer_projection,
            }
        )
    ).hexdigest()
    if (
        not _is_sha256(producer_binding)
        or producer_binding != expected_binding
        or not _is_sha256(row["pre_split_state_sha256"])
        or row["pre_split_state_sha256"]
        != row["shadow_pre_split_state_sha256"]
    ):
        raise ValueError(
            f"{lane} split row {row_index} producer binding failed"
        )
    if (
        row["configured_max_bond"] != 32
        or row["configured_cutoff"] != 0.0
        or row["configured_cutoff_mode"] != "rel"
        or row["configured_method"] != "svd"
        or row["configured_renorm"] is not False
        or row["configured_absorb"] is not None
        or row["configured_power"] != 1.0
        or row["configured_smudge"] != 1.0e-12
        or row["positive_discarded_weight_threshold"]
        != POSITIVE_TAIL_THRESHOLD
    ):
        raise ValueError(f"{lane} split row {row_index} policy mismatch")
    full_dimension = _plain_int(
        row["full_bond_dimension"],
        name=f"{lane} split full_bond_dimension",
        minimum=1,
    )
    kept_dimension = _plain_int(
        row["kept_bond_dimension"],
        name=f"{lane} split kept_bond_dimension",
        minimum=1,
    )
    full = decode_ndarray_v1(
        row["full_singular_values"],
        dtype="<f8",
        shape=(full_dimension,),
        sampler=sampler,
    )
    kept = decode_ndarray_v1(
        row["kept_singular_values"],
        dtype="<f8",
        shape=(kept_dimension,),
        sampler=sampler,
    )
    if (
        not np.isfinite(full).all()
        or not np.isfinite(kept).all()
        or np.any(full < 0.0)
        or np.any(kept < 0.0)
        or np.any(full[1:] > full[:-1] + 1.0e-12)
    ):
        raise ValueError(f"{lane} split spectrum is invalid")
    expected_kept = min(full_dimension, 32)
    if kept_dimension != expected_kept or not np.allclose(
        kept,
        full[:expected_kept],
        rtol=1.0e-12,
        atol=1.0e-12,
    ):
        raise ValueError(f"{lane} kept spectrum is not the capped prefix")
    pre_weight = float(np.sum(np.square(full)))
    discarded = float(np.sum(np.square(full[expected_kept:])))
    observed_discarded = _finite_float(
        row["discarded_squared_weight"],
        name=f"{lane} discarded_squared_weight",
    )
    observed_fraction = _finite_float(
        row["discarded_fraction"],
        name=f"{lane} discarded_fraction",
    )
    if pre_weight <= 0.0:
        raise ValueError(f"{lane} split pre-weight is nonpositive")
    if not math.isclose(
        observed_discarded,
        discarded,
        rel_tol=1.0e-12,
        abs_tol=1.0e-12,
    ) or not math.isclose(
        observed_fraction,
        discarded / pre_weight,
        rel_tol=1.0e-12,
        abs_tol=1.0e-12,
    ):
        raise ValueError(f"{lane} split tail ledger disagrees with spectrum")
    if lane == "plain":
        if (
            row["ordered_sites"] != operation["targets"]
            or not isinstance(row["eligible_edges"], list)
            or any(
                not isinstance(edge, list)
                or len(edge) != 2
                or any(
                    isinstance(site, bool) or not isinstance(site, int)
                    for site in edge
                )
                for edge in row["eligible_edges"]
            )
            or not isinstance(row["materialized_zero_gauge_edges"], list)
            or not isinstance(row["smudge_actually_used"], bool)
        ):
            raise ValueError(
                "plain split row does not join the fixture two-site gate"
            )
        observed_pre_weight = _finite_float(
            row["pre_split_weight"],
            name="plain pre_split_weight",
        )
        if not math.isclose(
            observed_pre_weight,
            pre_weight,
            rel_tol=1.0e-12,
            abs_tol=1.0e-12,
        ):
            raise ValueError("plain split pre-weight disagrees with spectrum")
    else:
        if gc_algorithm_row is None:
            raise ValueError("GC split row lacks its algorithm-ledger producer")
        compression = gc_algorithm_row["compression"]
        split_index = _plain_int(
            row["split_index"],
            name="GC split_index",
        )
        routed_edges = compression["routed_edge_order"]
        if (
            split_index >= len(routed_edges)
            or row["edge"] != routed_edges[split_index]
            or row["shadow_evidence_enabled"] is not True
            or row["configured_max_bond"]
            != compression["configured_max_bond"]
            or row["configured_cutoff"] != compression["configured_cutoff"]
            or row["configured_cutoff_mode"]
            != compression["configured_cutoff_mode"]
            or row["configured_method"] != compression["configured_method"]
            or row["configured_renorm"] != compression["configured_renorm"]
            or row["configured_absorb"] != compression["configured_absorb"]
            or row["configured_smudge"] != compression["configured_smudge"]
            or row["configured_power"] != compression["configured_power"]
            or row["low_level_contract"]
            != compression["low_level_contract"]
            or row["physical_gate_count_before"]
            != compression["physical_gate_count_before"]
            or row["physical_gate_count_after"]
            != compression["physical_gate_count_after"]
            or row["not_a_global_error_bound"]
            != compression["not_a_global_error_bound"]
            or not _is_sha256(row["identity_matrix_sha256"])
            or not isinstance(row["stripped_high_level_keys"], list)
            or len(set(row["stripped_high_level_keys"]))
            != len(row["stripped_high_level_keys"])
            or not set(row["stripped_high_level_keys"]).issubset(
                {"contract", "propagate_tags"}
            )
            or not isinstance(row["selected_gauges"], list)
            or not isinstance(row["smudge_actually_used"], bool)
            or row["info_mapping_was_fresh_and_empty"] is not True
        ):
            raise ValueError(
                "GC split row does not join its compression algorithm epoch"
            )
        for gauge_index, gauge in enumerate(row["selected_gauges"]):
            _require_exact_keys(
                gauge,
                GC_SELECTED_GAUGE_KEYS,
                name=f"GC selected gauge {gauge_index}",
            )
            if (
                not isinstance(gauge["graph_edge"], list)
                or len(gauge["graph_edge"]) != 2
                or any(
                    isinstance(site, bool) or not isinstance(site, int)
                    for site in gauge["graph_edge"]
                )
                or not isinstance(gauge["bond_index"], str)
                or not gauge["bond_index"]
                or gauge["position"] not in {"inner", "outer"}
                or not all(
                    isinstance(gauge[field], bool)
                    for field in (
                        "had_exact_zero",
                        "materialized_into_full_candidate",
                        "present_after_zero_preprocessing",
                        "strictly_positive_after_zero_preprocessing",
                    )
                )
                or gauge["materialized_into_full_candidate"]
                is not gauge["had_exact_zero"]
                or gauge["dtype"] != "float64"
            ):
                raise ValueError("GC selected gauge schema drifted")
            if gauge["had_exact_zero"]:
                if gauge["present_after_zero_preprocessing"] or gauge[
                    "strictly_positive_after_zero_preprocessing"
                ]:
                    raise ValueError("GC zero gauge preprocessing drifted")
            elif not gauge["present_after_zero_preprocessing"] or not gauge[
                "strictly_positive_after_zero_preprocessing"
            ]:
                raise ValueError("GC retained gauge preprocessing drifted")
    expected_cause = "max_bond" if full_dimension > 32 else "none"
    expected_positive = discarded > POSITIVE_TAIL_THRESHOLD
    if row["cause"] != expected_cause:
        raise ValueError(f"{lane} split cause disagrees with dimensions")
    if not isinstance(row["positive_discarded_weight"], bool):
        raise TypeError(f"{lane} positive_discarded_weight must be boolean")
    if row["positive_discarded_weight"] is not expected_positive:
        raise ValueError(f"{lane} positive flag disagrees with recomputed tail")
    qualifies = (
        full_dimension > 32
        and kept_dimension == 32
        and observed_discarded > POSITIVE_TAIL_THRESHOLD
        and row["cause"] == "max_bond"
        and row["configured_max_bond"] == 32
    )
    if expected_positive != qualifies:
        raise ValueError(f"{lane} positive flag does not satisfy all five gates")
    if lane == "gcapeps":
        if (
            row["dimension_reduced"]
            is not (kept_dimension < full_dimension)
            or _plain_int(
                row["exact_precompression_bond"],
                name="GC exact_precompression_bond",
                minimum=1,
            )
            != full_dimension
        ):
            raise ValueError("GC split dimension-reduction ledger mismatch")
    if not qualifies:
        _arrays_released(sampler, full, kept)
        return False, None
    locator = {
        "operation_index": row["operation_index"],
        "round_index": row["round_index"],
        "full_bond_dimension": full_dimension,
        "kept_bond_dimension": kept_dimension,
        "discarded_squared_weight": observed_discarded,
        "configured_max_bond": row["configured_max_bond"],
        "cause": row["cause"],
        "fixture_operation_class": operation["operation_class"],
        "fixture_gate_kind": operation["gate_kind"],
        "fixture_targets": operation["targets"],
        "fixture_collision_ordinal": operation.get("collision_ordinal"),
        "pre_split_state_sha256": row["pre_split_state_sha256"],
        "spectrum_producer_binding_sha256": producer_binding,
    }
    if lane == "gcapeps":
        locator["split_index"] = row["split_index"]
        locator["construction_epoch_before"] = gc_algorithm_row[
            "construction_epoch_before"
        ]
        locator["construction_epoch_after"] = gc_algorithm_row[
            "construction_epoch_after"
        ]
    _arrays_released(sampler, full, kept)
    return True, locator



def _validate_gc_algorithm_ledger(
    rows: Any,
    *,
    operations: list[Mapping[str, Any]],
    name: str,
) -> dict[int, Mapping[str, Any]]:
    if not isinstance(rows, list) or len(rows) != len(operations):
        raise ValueError(f"{name} does not cover every fixture operation")
    collision_epoch = 0
    projected: dict[int, Mapping[str, Any]] = {}
    clifford_keys = {
        "column",
        "round_index",
        "operation",
        "frame_revision_before",
        "frame_revision_after",
        "residual_revision_before",
        "residual_revision_after",
    }
    collision_keys = clifford_keys | {
        "physical_pauli",
        "pulled_back_pauli",
        "strategy",
        "support",
        "dependence_set",
        "routing_root",
        "routing_vertices",
        "routing_tree_edges",
        "max_bond_before",
        "max_bond_after",
        "construction_epoch_before",
        "construction_epoch_after",
        "edge_bonds",
        "resource_ledger",
        "compression",
    }
    compression_keys = {
        "compression_revision",
        "construction_epoch_before",
        "construction_epoch_after",
        "routed_edge_order",
        "configured_max_bond",
        "configured_cutoff",
        "configured_cutoff_mode",
        "configured_method",
        "configured_renorm",
        "configured_absorb",
        "configured_smudge",
        "configured_power",
        "low_level_contract",
        "routed_split_count",
        "physical_gate_count_before",
        "physical_gate_count_after",
        "product_maps_reset_to_one_on_commit",
        "counterfactual_lifetime_product_only",
        "not_a_global_error_bound",
    }
    for operation, row in zip(operations, rows, strict=True):
        operation_index = operation["operation_index"]
        expected_keys = (
            clifford_keys
            if operation["operation_class"] == "clifford"
            else collision_keys
        )
        _require_exact_keys(
            row,
            expected_keys,
            name=f"{name} operation {operation_index}",
        )
        if (
            row["column"] != operation_index
            or row["round_index"] != operation["round_index"]
            or row["operation"]
            != (
                "clifford_frame_update"
                if operation["operation_class"] == "clifford"
                else "pulled_pauli_rotation"
            )
        ):
            raise ValueError(
                f"{name} does not join fixture operation {operation_index}"
            )
        if operation["operation_class"] == "collision_rotation":
            compression = row["compression"]
            _require_exact_keys(
                compression,
                compression_keys,
                name=f"{name} compression {operation_index}",
            )
            routed_edges = compression["routed_edge_order"]
            if (
                not isinstance(row["physical_pauli"], str)
                or not row["physical_pauli"]
                or row["strategy"]
                != "exact_tree_then_native_identity_compress"
                or row["construction_epoch_before"] != collision_epoch
                or row["construction_epoch_after"] != collision_epoch + 1
                or compression["construction_epoch_before"]
                != collision_epoch
                or compression["construction_epoch_after"]
                != collision_epoch + 1
                or not isinstance(routed_edges, list)
                or any(
                    not isinstance(edge, list)
                    or len(edge) != 2
                    or any(
                        isinstance(site, bool) or not isinstance(site, int)
                        for site in edge
                    )
                    for edge in routed_edges
                )
                or compression["routed_split_count"] != len(routed_edges)
                or compression["configured_max_bond"] != 32
                or compression["configured_cutoff"] != 0.0
                or compression["configured_cutoff_mode"] != "rel"
                or compression["configured_method"] != "svd"
                or compression["configured_renorm"] is not False
                or compression["configured_absorb"] is not None
                or compression["configured_smudge"] != 1.0e-12
                or compression["configured_power"] != 1.0
                or compression["product_maps_reset_to_one_on_commit"]
                is not True
                or compression["counterfactual_lifetime_product_only"]
                is not True
                or compression["not_a_global_error_bound"] is not True
            ):
                raise ValueError(
                    f"{name} collision epoch or route ledger drifted"
                )
            collision_epoch += 1
        projected[operation_index] = row
    return projected

def _validate_candidate_core(
    core: Mapping[str, Any],
    *,
    lane: str,
    input_id: int,
    identity: Mapping[str, Any],
    sampler: ComparatorArraySampler,
) -> dict[str, Any]:
    common_keys = {
        "schema",
        "lane",
        "role",
        "case_id",
        "input_id",
        "fixture_projection_sha256",
        "no_shadow",
        "instrumented_final_carrier_hash",
        "operation_count",
        "max_exact_precompression_bond",
        "max_committed_bond",
        "final_committed_bond",
        "positive_cap_event_count",
        "split_records",
        "round_continuity_ledger",
        "checkpoints",
        "logical_memory",
        "contains_cross_artifact_metric",
        "result_projection_sha256",
    }
    expected_keys = set(common_keys)
    if lane == "gcapeps":
        expected_keys.update(
            {"signed_pullback_rows", "instrumented_algorithm_ledger"}
        )
    _require_exact_keys(core, expected_keys, name=f"{lane} input{input_id} core")
    digest = _validate_projection(core, name=f"{lane} input{input_id} core")
    expected_schema = (
        PLAIN_EVIDENCE_SCHEMA if lane == "plain" else GCAPEPS_EVIDENCE_SCHEMA
    )
    if (
        core["schema"] != expected_schema
        or core["lane"] != lane
        or core["role"] != "evidence"
        or core["case_id"] != identity["case_id"]
        or core["input_id"] != input_id
        or core["fixture_projection_sha256"]
        != identity["fixture_projection_sha256"]
        or core["contains_cross_artifact_metric"] is not False
    ):
        raise ValueError(f"{lane} input{input_id} artifact identity mismatch")
    if lane == "plain" and core["max_exact_precompression_bond"] is not None:
        raise ValueError("plain evidence cannot claim a GC exact transient bond")
    if lane == "gcapeps":
        _plain_int(
            core["max_exact_precompression_bond"],
            name="GC max_exact_precompression_bond",
            minimum=1,
        )
    operation_count = _plain_int(
        core["operation_count"], name=f"{lane} operation_count"
    )
    if operation_count != len(identity["operations"]):
        raise ValueError(f"{lane} operation ledger does not cover fixture")
    continuity = _validate_round_continuity(
        core["round_continuity_ledger"],
        lane=f"{lane} instrumented",
        rounds=identity["rounds"],
    )
    _validate_logical_memory_report(
        core["logical_memory"],
        lane=lane,
        require_evidence=True,
        name=f"{lane} logical_memory",
    )
    no_shadow = core["no_shadow"]
    if not isinstance(no_shadow, Mapping):
        raise TypeError(f"{lane} no_shadow must be an object")
    no_shadow_required = {
        "operation_count",
        "max_committed_bond",
        "final_committed_bond",
        "final_carrier_hash",
        "logical_memory",
        "round_continuity_ledger",
    }
    if lane == "gcapeps":
        no_shadow_required.update(
            {"max_exact_precompression_bond", "algorithm_ledger"}
        )
    if set(no_shadow) != no_shadow_required:
        raise ValueError(f"{lane} no_shadow identity fields are not exact")
    _validate_logical_memory_report(
        no_shadow["logical_memory"],
        lane=lane,
        require_evidence=False,
        name=f"{lane} no-shadow logical_memory",
    )
    no_shadow_continuity = _validate_round_continuity(
        no_shadow["round_continuity_ledger"],
        lane=f"{lane} no-shadow",
        rounds=identity["rounds"],
    )
    if no_shadow_continuity != continuity:
        raise ValueError(
            f"{lane} no-shadow/instrumented round continuity mismatch"
        )
    if core["logical_memory"]["sample_count"] <= no_shadow[
        "logical_memory"
    ]["sample_count"]:
        raise ValueError(
            f"{lane} instrumented memory samples do not extend no-shadow"
        )
    instrumented_hash = core["instrumented_final_carrier_hash"]
    no_shadow_hash = no_shadow["final_carrier_hash"]
    if (
        not isinstance(instrumented_hash, Mapping)
        or not isinstance(no_shadow_hash, Mapping)
        or not _is_sha256(instrumented_hash.get("sha256"))
        or instrumented_hash.get("sha256") != no_shadow_hash.get("sha256")
        or continuity[-1]["round_end_state_sha256"]
        != instrumented_hash.get("sha256")
        or no_shadow["operation_count"] != operation_count
        or no_shadow["max_committed_bond"] != core["max_committed_bond"]
        or no_shadow["final_committed_bond"] != core["final_committed_bond"]
        or _logical_memory_base_projection(no_shadow["logical_memory"])
        != _logical_memory_base_projection(core["logical_memory"])
    ):
        raise ValueError(f"{lane} no-shadow/instrumented identity mismatch")
    if (
        lane == "gcapeps"
        and no_shadow["max_exact_precompression_bond"]
        != core["max_exact_precompression_bond"]
    ):
        raise ValueError("GC no-shadow exact transient bond mismatch")
    gc_algorithm_by_operation: dict[int, Mapping[str, Any]] = {}
    if lane == "gcapeps":
        gc_algorithm_by_operation = _validate_gc_algorithm_ledger(
            core["instrumented_algorithm_ledger"],
            operations=identity["operations"],
            name="GC instrumented algorithm ledger",
        )
        _validate_gc_algorithm_ledger(
            no_shadow["algorithm_ledger"],
            operations=identity["operations"],
            name="GC no-shadow algorithm ledger",
        )
        if (
            no_shadow["algorithm_ledger"]
            != core["instrumented_algorithm_ledger"]
        ):
            raise ValueError(
                "GC no-shadow/instrumented algorithm epoch mismatch"
            )
    for field in ("max_committed_bond", "final_committed_bond"):
        value = _plain_int(core[field], name=f"{lane} {field}", minimum=1)
        if value > 32:
            raise ValueError(f"{lane} {field} exceeds the frozen cap")
    checkpoints = core["checkpoints"]
    if not isinstance(checkpoints, list) or len(checkpoints) != len(
        identity["checkpoints"]
    ):
        raise ValueError(f"{lane} input{input_id} checkpoint cardinality mismatch")
    vectors: dict[int, np.ndarray] = {}
    for expected_round, checkpoint in zip(
        identity["checkpoints"], checkpoints, strict=True
    ):
        _require_exact_keys(
            checkpoint,
            {"round_index", "source_branch", "pre_metric", "vector"},
            name=f"{lane} input{input_id} checkpoint",
        )
        if (
            checkpoint["round_index"] != expected_round
            or checkpoint["source_branch"] != "instrumented_replay"
        ):
            raise ValueError(
                f"{lane} input{input_id} checkpoint order or source mismatch"
            )
        vector = decode_ndarray_v1(
            checkpoint["vector"],
            dtype="<c16",
            shape=(2 ** identity["n_qubits"],),
            sampler=sampler,
        )
        gate = vector_gate(
            vector,
            width=identity["width"],
            sampler=sampler,
        )
        _validate_candidate_pre_metric(
            checkpoint["pre_metric"],
            gate=gate,
            lane=lane,
            input_id=input_id,
            round_index=expected_round,
        )
        _arrays_released(
            sampler,
            gate["rho_system"],
            gate["normalized_schmidt_values"],
        )
        del gate
        vectors[expected_round] = vector
    split_rows = core["split_records"]
    if not isinstance(split_rows, list):
        raise TypeError(f"{lane} split_records must be a JSON list")
    expected_split_rows: list[
        tuple[Mapping[str, Any], int | None]
    ] = []
    if lane == "plain":
        expected_split_rows = [
            (operation, None)
            for operation in identity["operations"]
            if len(operation["targets"]) == 2
        ]
    else:
        for operation in identity["operations"]:
            if operation["operation_class"] != "collision_rotation":
                continue
            algorithm_row = gc_algorithm_by_operation[
                operation["operation_index"]
            ]
            for split_index, _edge in enumerate(
                algorithm_row["compression"]["routed_edge_order"]
            ):
                expected_split_rows.append((operation, split_index))
    if len(split_rows) != len(expected_split_rows):
        raise ValueError(
            f"{lane} split ledger does not cover its exact producer sequence"
        )
    positive_locators = []
    for row_index, (row, expected) in enumerate(
        zip(split_rows, expected_split_rows, strict=True)
    ):
        operation, expected_split_index = expected
        if (
            lane == "gcapeps"
            and row.get("split_index") != expected_split_index
        ):
            raise ValueError("GC split index sequence drifted")
        qualifies, locator = _split_event_projection(
            row,
            lane=lane,
            row_index=row_index,
            operation=operation,
            gc_algorithm_row=(
                gc_algorithm_by_operation[operation["operation_index"]]
                if lane == "gcapeps"
                else None
            ),
            sampler=sampler,
        )
        if qualifies:
            assert locator is not None
            positive_locators.append(locator)
    observed_count = _plain_int(
        core["positive_cap_event_count"],
        name=f"{lane} positive_cap_event_count",
    )
    if observed_count != len(positive_locators):
        raise ValueError(
            f"{lane} positive event count disagrees with recomputed split rows"
        )
    return {
        "result_projection_sha256": digest,
        "vectors": vectors,
        "positive_event_count": len(positive_locators),
        "positive_event_locators": positive_locators,
        "signed_pullback_rows": (
            core["signed_pullback_rows"] if lane == "gcapeps" else None
        ),
        "bonds": {
            "max_exact_precompression_bond": core[
                "max_exact_precompression_bond"
            ],
            "max_committed_bond": core["max_committed_bond"],
            "final_committed_bond": core["final_committed_bond"],
        },
    }


def _validate_sdim_core(
    sdim_core: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
) -> dict[str, Any]:
    _require_exact_keys(
        sdim_core,
        {
            "schema",
            "role",
            "fixture_identity",
            "inventory_binding",
            "scope",
            "expected_key_sequence",
            "sdim_rows",
            "stim_rows",
            "pullback_rows",
            "coverage",
            "sdim_equals_stim",
            "result_projection_sha256",
        },
        name="SDIM core",
    )
    digest = _validate_projection(sdim_core, name="SDIM core")
    if (
        sdim_core["schema"] != SDIM_SCHEMA
        or sdim_core["role"] != "sdim_stim_qubit_frame_corroboration"
        or sdim_core["sdim_equals_stim"] is not True
    ):
        raise ValueError("SDIM core identity mismatch")
    fixture_identity = sdim_core["fixture_identity"]
    if (
        not isinstance(fixture_identity, Mapping)
        or fixture_identity.get("schema") != FIXTURE_SCHEMA
        or fixture_identity.get("fixture_projection_sha256")
        != identity["fixture_projection_sha256"]
        or fixture_identity.get("run_partition") != identity["run_partition"]
        or fixture_identity.get("case_id") != identity["case_id"]
        or fixture_identity.get("width") != identity["width"]
        or fixture_identity.get("n_qubits") != identity["n_qubits"]
        or fixture_identity.get("request_count")
        != len(identity["expected_keys"])
    ):
        raise ValueError("SDIM fixture identity mismatch")
    sequence_kwargs = {
        "width": identity["width"],
        "run_partition": identity["run_partition"],
        "case_id": identity["case_id"],
        "input_hashes": identity["input_hashes"],
        "shared_evolution_sha256": identity["shared_evolution_sha256"],
    }
    expected_keys = _request_sequence(
        sdim_core["expected_key_sequence"],
        exact_keys=REQUEST_KEY_SET,
        name="SDIM expected rows",
        **sequence_kwargs,
    )
    sdim_keys = _request_sequence(
        sdim_core["sdim_rows"],
        exact_keys=SDIM_ROW_KEYS,
        name="SDIM S rows",
        **sequence_kwargs,
    )
    stim_keys = _request_sequence(
        sdim_core["stim_rows"],
        exact_keys=STIM_ROW_KEYS,
        name="Stim T rows",
        **sequence_kwargs,
    )
    return {
        "result_projection_sha256": digest,
        "expected_keys": expected_keys,
        "sdim_keys": sdim_keys,
        "stim_keys": stim_keys,
        "sdim_rows": sdim_core["sdim_rows"],
        "stim_rows": sdim_core["stim_rows"],
        "pullback_rows": sdim_core["pullback_rows"],
        "coverage": sdim_core["coverage"],
    }


def _signed_value(
    row: Mapping[str, Any],
    *,
    sign_name: str,
    body_name: str,
    n_qubits: int,
    name: str,
) -> tuple[int, str]:
    sign = row[sign_name]
    body = row[body_name]
    if isinstance(sign, bool) or not isinstance(sign, int) or sign not in (-1, 1):
        raise ValueError(f"{name} sign is not exact +/-1")
    if (
        not isinstance(body, str)
        or len(body) != n_qubits
        or any(label not in "IXYZ" for label in body)
    ):
        raise ValueError(f"{name} body is not a complete Pauli word")
    return sign, body


def _join_signed_pullbacks(
    *,
    identity: Mapping[str, Any],
    sdim: Mapping[str, Any],
    gc_input1_rows: Any,
    gc_input2_rows: Any,
) -> dict[str, Any]:
    sequence_kwargs = {
        "width": identity["width"],
        "run_partition": identity["run_partition"],
        "case_id": identity["case_id"],
        "input_hashes": identity["input_hashes"],
        "shared_evolution_sha256": identity["shared_evolution_sha256"],
    }
    gc_rows_by_input = {1: gc_input1_rows, 2: gc_input2_rows}
    gc_keys_by_input: dict[int, list[tuple[Any, ...]]] = {}
    for input_id in (1, 2):
        rows = gc_rows_by_input[input_id]
        keys = _request_sequence(
            rows,
            exact_keys=GC_ROW_KEYS,
            name=f"GC input{input_id} G rows",
            **sequence_kwargs,
        )
        gc_keys_by_input[input_id] = keys
    gc_raw_keys = gc_keys_by_input[1] + gc_keys_by_input[2]
    if len(gc_raw_keys) != len(set(gc_raw_keys)):
        raise ValueError("GC rows contain a duplicate key across artifacts")
    for input_id in (1, 2):
        if any(key[2] != input_id for key in gc_keys_by_input[input_id]):
            raise ValueError(f"GC input{input_id} contains a cross-input key")
    gc_rows = list(gc_input1_rows) + list(gc_input2_rows)
    ordered_pairs = sorted(
        zip(gc_raw_keys, gc_rows, strict=True), key=lambda item: item[0]
    )
    gc_keys = [item[0] for item in ordered_pairs]
    expected = identity["expected_keys"]
    if not (
        expected
        == sdim["expected_keys"]
        == sdim["sdim_keys"]
        == sdim["stim_keys"]
        == gc_keys
    ):
        counts = {
            "E": len(expected),
            "S_expected": len(sdim["expected_keys"]),
            "S": len(sdim["sdim_keys"]),
            "T": len(sdim["stim_keys"]),
            "G": len(gc_keys),
        }
        raise ValueError(
            "pullback coverage gate E == S == T == G failed: "
            f"counts={counts}"
        )

    joined_rows = sdim["pullback_rows"]
    if not isinstance(joined_rows, list) or len(joined_rows) != len(expected):
        raise ValueError("SDIM joined pullback coverage cardinality mismatch")
    expected_coverage = {
        "expected_count": len(expected),
        "sdim_count": len(expected),
        "stim_count": len(expected),
        "joined_count": len(expected),
        "expected_sdim_stim_exact_ordered_sequence": True,
        "duplicates_rejected_before_join": True,
        "empty_sequence_legal_only_if_fixture_empty": True,
    }
    if sdim["coverage"] != expected_coverage:
        raise ValueError("SDIM coverage ledger disagrees with recomputed coverage")

    value_rows = []
    for index, (key, sdim_row, stim_row, gc_pair, joined) in enumerate(
        zip(
            expected,
            sdim["sdim_rows"],
            sdim["stim_rows"],
            ordered_pairs,
            joined_rows,
            strict=True,
        )
    ):
        gc_key, gc_row = gc_pair
        assert gc_key == key
        sdim_value = _signed_value(
            sdim_row,
            sign_name="sdim_sign",
            body_name="sdim_body",
            n_qubits=identity["n_qubits"],
            name=f"SDIM row {index}",
        )
        stim_value = _signed_value(
            stim_row,
            sign_name="stim_sign",
            body_name="stim_body",
            n_qubits=identity["n_qubits"],
            name=f"Stim row {index}",
        )
        gc_value = _signed_value(
            gc_row,
            sign_name="pulled_back_sign",
            body_name="pulled_back_body",
            n_qubits=identity["n_qubits"],
            name=f"GC row {index}",
        )
        physical_value = _signed_value(
            gc_row,
            sign_name="physical_sign",
            body_name="physical_body",
            n_qubits=identity["n_qubits"],
            name=f"GC physical row {index}",
        )
        if physical_value != (1, key[-1]):
            raise ValueError(f"GC physical signed value mismatch at key {key!r}")
        if sdim_value != stim_value or sdim_value != gc_value:
            raise ValueError(f"signed pullback value mismatch at key {key!r}")
        expected_joined_keys = REQUEST_KEY_SET | frozenset(
            {
                "sdim_sign",
                "sdim_body",
                "stim_sign",
                "stim_body",
                "sdim_equals_stim",
            }
        )
        _require_exact_keys(
            joined, expected_joined_keys, name=f"SDIM joined row {index}"
        )
        if (
            tuple(joined[field] for field in REQUEST_KEYS) != key
            or joined["sdim_equals_stim"] is not True
            or (joined["sdim_sign"], joined["sdim_body"]) != sdim_value
            or (joined["stim_sign"], joined["stim_body"]) != stim_value
        ):
            raise ValueError(f"SDIM joined signed row mismatch at key {key!r}")
        value_rows.append(
            {
                "key_sha256": hashlib.sha256(
                    canonical_json_bytes(
                        {field: sdim_row[field] for field in REQUEST_KEYS}
                    )
                ).hexdigest(),
                "sign": sdim_value[0],
                "body": sdim_value[1],
            }
        )
    return {
        "expected_count": len(expected),
        "sdim_count": len(sdim["sdim_keys"]),
        "stim_count": len(sdim["stim_keys"]),
        "gc_count": len(gc_keys),
        "local_duplicates_rejected": True,
        "cross_gc_duplicates_rejected": True,
        "exact_unique_ordered_E_equals_S_equals_T_equals_G": True,
        "signed_values_equal_after_coverage": True,
        "joined_value_rows": value_rows,
    }


_ENTROPY_WITNESS_KEYS = frozenset(
    {
        "source",
        "candidate_values_consumed",
        "round_indices",
        "entropy_von_neumann",
        "entropy_renyi2",
        "normalized_schmidt_values_by_round",
        "numerical_schmidt_rank_by_round",
        "entropy_von_neumann_increments",
        "negative_increment_rows",
        "revival_rows",
        "maximum_entropy_von_neumann",
        "terminal_entropy_von_neumann",
        "round1_entropy_von_neumann",
        "terminal_minus_round1",
        "h_e_strict_threshold",
        "h_e_condition_holds",
        "conditional_h_e_verdict_if_amendment_bound_stress_cell",
        "h_e_applicability_deferred_to_amendment_bound_stress_cell",
    }
)
_ZERO_CONTROL_KEYS = frozenset(
    {
        "every_event_bit_structural_false",
        "active_axis_rotation_count",
        "all_system_memory_s1_s2_at_most_1e_12",
        "fixed_trace_distance_one_within_1e_12",
        "fixed_named_increment_at_most_1e_10",
        "ensemble_trace_distance_one_within_1e_12",
        "ensemble_named_increment_at_most_1e_10",
        "passed",
    }
)


def _validate_emitted_blp_witness(
    witness: Any,
    *,
    object_name: str,
    system_dimension: int,
    name: str,
) -> None:
    if not isinstance(witness, Mapping):
        raise TypeError(f"{name} must be an object")
    _require_exact_keys(witness, _BLP_KEYS, name=name)
    spectra = witness["difference_eigenvalues_by_round"]
    distances = witness["trace_distances"]
    if (
        not isinstance(spectra, list)
        or not isinstance(distances, list)
        or len(spectra) != len(distances)
        or len(distances) < 2
    ):
        raise ValueError(f"{name} trajectory cardinality is invalid")
    spectral_distances: list[float] = []
    for round_index, spectrum in enumerate(spectra):
        if not isinstance(spectrum, list) or len(spectrum) != system_dimension:
            raise ValueError(f"{name} spectrum {round_index} shape is invalid")
        values = [
            _finite_float(
                value,
                name=f"{name} spectrum {round_index}[{index}]",
            )
            for index, value in enumerate(spectrum)
        ]
        spectral_distances.append(
            float(0.5 * math.fsum(abs(value) for value in values))
        )
    _float_sequence_equal(
        distances,
        spectral_distances,
        name=f"{name} trace_distances",
    )
    observed_distances = [
        _finite_float(value, name=f"{name} trace distance")
        for value in distances
    ]
    if abs(observed_distances[0] - 1.0) > TRACE_TOLERANCE:
        raise ValueError(f"{name} initial trace distance is not one")
    expected_increments = [
        float(observed_distances[index] - observed_distances[index - 1])
        for index in range(1, len(observed_distances))
    ]
    _float_sequence_equal(
        witness["increments"],
        expected_increments,
        name=f"{name} increments",
    )
    expected_positive_sum = float(
        math.fsum(max(0.0, value) for value in expected_increments)
    )
    expected_maximum = max(expected_increments)
    ensemble = object_name == "finite_32_mask_ensemble"
    witnessed = expected_maximum > BLP_INCREMENT_TOLERANCE
    expected_verdict = (
        (
            "BLP_WITNESSED_FINITE_32_MASK_ENSEMBLE"
            if witnessed
            else "NO_WITNESS_FINITE_32_MASK_ENSEMBLE_FOR_REGISTERED_PAIR"
        )
        if ensemble
        else (
            "BLP_WITNESSED_FIXED_MASK"
            if witnessed
            else "NO_WITNESS_FIXED_MASK_FOR_REGISTERED_PAIR"
        )
    )
    if (
        witness["object"] != object_name
        or witness["witness_threshold"] != BLP_INCREMENT_TOLERANCE
        or witness["verdict"] != expected_verdict
        or not math.isclose(
            _finite_float(
                witness["summed_positive_increments"],
                name=f"{name} summed_positive_increments",
            ),
            expected_positive_sum,
            rel_tol=1.0e-12,
            abs_tol=1.0e-12,
        )
        or not math.isclose(
            _finite_float(
                witness["maximum_increment"],
                name=f"{name} maximum_increment",
            ),
            expected_maximum,
            rel_tol=1.0e-12,
            abs_tol=1.0e-12,
        )
    ):
        raise ValueError(f"{name} derived fields are corrupted")


def _validate_emitted_entropy_witness(
    witness: Any,
    *,
    width: int,
    rounds: int,
) -> None:
    if not isinstance(witness, Mapping):
        raise TypeError("trajectory1 entropy witness must be an object")
    _require_exact_keys(
        witness,
        _ENTROPY_WITNESS_KEYS,
        name="trajectory1 entropy witness",
    )
    if (
        witness["source"] != "exact_dense_fixed_carrier_input1"
        or witness["candidate_values_consumed"] is not False
        or witness["round_indices"] != list(range(rounds + 1))
        or witness["h_e_strict_threshold"]
        != ENTANGLEMENT_HYPOTHESIS_TOLERANCE
        or witness["h_e_applicability_deferred_to_amendment_bound_stress_cell"]
        is not True
        or witness["conditional_h_e_verdict_if_amendment_bound_stress_cell"]
        not in {"supported", "falsified"}
    ):
        raise ValueError("trajectory1 entropy witness identity is invalid")
    entropy_s1 = witness["entropy_von_neumann"]
    entropy_s2 = witness["entropy_renyi2"]
    schmidt_rows = witness["normalized_schmidt_values_by_round"]
    ranks = witness["numerical_schmidt_rank_by_round"]
    cardinality = rounds + 1
    if any(
        not isinstance(rows, list) or len(rows) != cardinality
        for rows in (entropy_s1, entropy_s2, schmidt_rows, ranks)
    ):
        raise ValueError("trajectory1 entropy witness cardinality is invalid")
    checked_s1 = [
        _finite_float(value, name=f"trajectory1 S1 round {round_index}")
        for round_index, value in enumerate(entropy_s1)
    ]
    checked_s2 = [
        _finite_float(value, name=f"trajectory1 S2 round {round_index}")
        for round_index, value in enumerate(entropy_s2)
    ]
    system_dimension = 2**width
    for round_index, (row, observed_rank) in enumerate(
        zip(schmidt_rows, ranks, strict=True)
    ):
        if not isinstance(row, list) or len(row) != system_dimension:
            raise ValueError("trajectory1 Schmidt spectrum shape is invalid")
        singular_values = [
            _finite_float(
                value,
                name=f"trajectory1 Schmidt round {round_index}",
            )
            for value in row
        ]
        if (
            any(value < 0.0 for value in singular_values)
            or any(
                right > left + 1.0e-12
                for left, right in zip(
                    singular_values, singular_values[1:]
                )
            )
        ):
            raise ValueError("trajectory1 Schmidt spectrum is invalid")
        probabilities = [value * value for value in singular_values]
        if not math.isclose(
            math.fsum(probabilities),
            1.0,
            rel_tol=1.0e-12,
            abs_tol=1.0e-12,
        ):
            raise ValueError("trajectory1 Schmidt spectrum is not normalized")
        positive = [value for value in probabilities if value > 0.0]
        recomputed_s1 = float(
            -math.fsum(value * math.log2(value) for value in positive)
        )
        recomputed_s2 = float(
            -math.log2(math.fsum(value * value for value in probabilities))
        )
        if (
            not math.isclose(
                checked_s1[round_index],
                recomputed_s1,
                rel_tol=1.0e-10,
                abs_tol=1.0e-10,
            )
            or not math.isclose(
                checked_s2[round_index],
                recomputed_s2,
                rel_tol=1.0e-10,
                abs_tol=1.0e-10,
            )
        ):
            raise ValueError("trajectory1 entropy disagrees with Schmidt data")
        largest = singular_values[0]
        recomputed_rank = sum(
            value > NUMERICAL_RANK_RELATIVE_TOLERANCE * largest
            for value in singular_values
        )
        if (
            isinstance(observed_rank, bool)
            or not isinstance(observed_rank, int)
            or observed_rank != recomputed_rank
        ):
            raise ValueError("trajectory1 numerical Schmidt rank is invalid")
    increments = [
        float(checked_s1[index] - checked_s1[index - 1])
        for index in range(1, cardinality)
    ]
    expected_negative = [
        {"round_index": index, "increment": value}
        for index, value in enumerate(increments, start=1)
        if value < 0.0
    ]
    expected_revivals = [
        {"round_index": index, "increment": value}
        for index, value in enumerate(increments, start=1)
        if value > 0.0
    ]
    terminal_minus_round1 = float(checked_s1[-1] - checked_s1[1])
    if (
        witness["entropy_von_neumann_increments"] != increments
        or witness["negative_increment_rows"] != expected_negative
        or witness["revival_rows"] != expected_revivals
        or witness["maximum_entropy_von_neumann"] != max(checked_s1)
        or witness["terminal_entropy_von_neumann"] != checked_s1[-1]
        or witness["round1_entropy_von_neumann"] != checked_s1[1]
        or witness["terminal_minus_round1"] != terminal_minus_round1
        or witness["h_e_condition_holds"]
        is not (
            terminal_minus_round1
            > ENTANGLEMENT_HYPOTHESIS_TOLERANCE
        )
        or witness["conditional_h_e_verdict_if_amendment_bound_stress_cell"]
        != (
            "supported"
            if terminal_minus_round1 > ENTANGLEMENT_HYPOTHESIS_TOLERANCE
            else "falsified"
        )
    ):
        raise ValueError("trajectory1 entropy derived fields are corrupted")


def _validate_exact_dense_memory_witnesses(
    witness: Any,
    *,
    width: int,
    rounds: int,
) -> None:
    if not isinstance(witness, Mapping):
        raise TypeError("exact dense memory witnesses must be an object")
    _require_exact_keys(
        witness,
        {
            "fixed_blp",
            "finite_32_mask_ensemble_blp",
            "p_event_zero_control",
            "trajectory1_entanglement",
        },
        name="exact dense memory witnesses",
    )
    system_dimension = 2**width
    _validate_emitted_blp_witness(
        witness["fixed_blp"],
        object_name="fixed_carrier_mask",
        system_dimension=system_dimension,
        name="fixed-mask BLP witness",
    )
    ensemble = witness["finite_32_mask_ensemble_blp"]
    if ensemble is not None:
        _validate_emitted_blp_witness(
            ensemble,
            object_name="finite_32_mask_ensemble",
            system_dimension=system_dimension,
            name="finite-32 BLP witness",
        )
    control = witness["p_event_zero_control"]
    if control is not None:
        if not isinstance(control, Mapping):
            raise TypeError("p_event_zero_control must be an object or null")
        _require_exact_keys(
            control,
            _ZERO_CONTROL_KEYS,
            name="p_event_zero_control",
        )
        boolean_fields = set(_ZERO_CONTROL_KEYS) - {
            "active_axis_rotation_count"
        }
        if (
            control["active_axis_rotation_count"] != 0
            or any(control[field] is not True for field in boolean_fields)
        ):
            raise ValueError("p_event_zero_control is not a passing control")
    _validate_emitted_entropy_witness(
        witness["trajectory1_entanglement"],
        width=width,
        rounds=rounds,
    )


def _faithfulness_class(value: float) -> str:
    if value >= 0.99:
        return "high"
    if value >= 0.95:
        return "degraded"
    return "low"


def build_comparator_core(
    *,
    fixture: Mapping[str, Any],
    dense_core: Mapping[str, Any],
    plain_input1_core: Mapping[str, Any],
    plain_input2_core: Mapping[str, Any],
    gcapeps_input1_core: Mapping[str, Any],
    gcapeps_input2_core: Mapping[str, Any],
    sdim_core: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate seven sealed cores, join them, and compute evaluator metrics."""

    sampler = ComparatorArraySampler()
    identity = _validate_fixture_identity(fixture)
    dense_hash, dense_vectors, exact_dense_memory_witnesses = (
        _validate_dense_core(
            dense_core,
            identity=identity,
            fixture=fixture,
            sampler=sampler,
        )
    )
    candidates: dict[str, dict[int, dict[str, Any]]] = {
        "plain": {
            1: _validate_candidate_core(
                plain_input1_core,
                lane="plain",
                input_id=1,
                identity=identity,
                sampler=sampler,
            ),
            2: _validate_candidate_core(
                plain_input2_core,
                lane="plain",
                input_id=2,
                identity=identity,
                sampler=sampler,
            ),
        },
        "gcapeps": {
            1: _validate_candidate_core(
                gcapeps_input1_core,
                lane="gcapeps",
                input_id=1,
                identity=identity,
                sampler=sampler,
            ),
            2: _validate_candidate_core(
                gcapeps_input2_core,
                lane="gcapeps",
                input_id=2,
                identity=identity,
                sampler=sampler,
            ),
        },
    }
    sdim = _validate_sdim_core(sdim_core, identity=identity)
    pullback_join = _join_signed_pullbacks(
        identity=identity,
        sdim=sdim,
        gc_input1_rows=candidates["gcapeps"][1]["signed_pullback_rows"],
        gc_input2_rows=candidates["gcapeps"][2]["signed_pullback_rows"],
    )

    positive_paths = []
    for lane in ("plain", "gcapeps"):
        for input_id in (1, 2):
            row = candidates[lane][input_id]
            positive_paths.append(
                {
                    "lane": lane,
                    "input_id": input_id,
                    "positive_bond32_event": row["positive_event_count"] > 0,
                    "positive_event_count": row["positive_event_count"],
                    "qualifying_event_locators": row[
                        "positive_event_locators"
                    ],
                }
            )
    shared_positive = all(
        path["positive_bond32_event"] for path in positive_paths
    )

    checkpoint_metrics = []
    for round_index in identity["checkpoints"]:
        checkpoint_row: dict[str, Any] = {"round_index": round_index}
        for lane in ("plain", "gcapeps"):
            by_input = {
                f"input{input_id}": whole_state_metrics(
                    dense_vectors[input_id][round_index],
                    candidates[lane][input_id]["vectors"][round_index],
                    width=identity["width"],
                    sampler=sampler,
                )
                for input_id in (1, 2)
            }
            by_input["fixed_pair_checkpoint_error"] = (
                fixed_pair_checkpoint_error(
                    dense_vectors[1][round_index],
                    dense_vectors[2][round_index],
                    candidates[lane][1]["vectors"][round_index],
                    candidates[lane][2]["vectors"][round_index],
                    width=identity["width"],
                    sampler=sampler,
                )
            )
            checkpoint_row[lane] = by_input
        checkpoint_metrics.append(checkpoint_row)

    retained_vectors = [
        dense_vectors[input_id][round_index]
        for input_id in (1, 2)
        for round_index in identity["checkpoints"]
    ]
    retained_vectors.extend(
        candidates[lane][input_id]["vectors"][round_index]
        for lane in ("plain", "gcapeps")
        for input_id in (1, 2)
        for round_index in identity["checkpoints"]
    )
    _arrays_released(sampler, *retained_vectors)
    for vectors_by_round in dense_vectors.values():
        vectors_by_round.clear()
    for lane in ("plain", "gcapeps"):
        for input_id in (1, 2):
            candidates[lane][input_id]["vectors"].clear()
    retained_vectors.clear()
    if sampler.current_bytes != 0:
        raise AssertionError(
            "comparator array ownership was not empty after final release"
        )
    max_sampled_comparator_array_bytes = sampler.maximum_bytes
    if max_sampled_comparator_array_bytes <= 0:
        raise AssertionError("comparator sampled no decoded or metric arrays")

    final_round = identity["rounds"]
    final_metrics = checkpoint_metrics[-1]
    if final_metrics["round_index"] != final_round:
        raise AssertionError("fixture final checkpoint was not terminal")
    delta_f = stress_delta_f(
        plain_fidelities={
            f"input{input_id}": final_metrics["plain"][f"input{input_id}"][
                "fidelity"
            ]
            for input_id in (1, 2)
        },
        gcapeps_fidelities={
            f"input{input_id}": final_metrics["gcapeps"][
                f"input{input_id}"
            ]["fidelity"]
            for input_id in (1, 2)
        },
    )
    conditional_h_f_verdict = (
        "INELIGIBLE_NO_SHARED_POSITIVE_TRUNCATION"
        if not shared_positive
        else "supported"
        if delta_f["direction"] == "gcapeps_higher"
        else "falsified"
        if delta_f["direction"] == "plain_higher"
        else "tie/inconclusive"
    )

    artifact_bindings = {
        "fixture": identity["fixture_projection_sha256"],
        "dense": dense_hash,
        "plain_input1": candidates["plain"][1][
            "result_projection_sha256"
        ],
        "plain_input2": candidates["plain"][2][
            "result_projection_sha256"
        ],
        "gcapeps_input1": candidates["gcapeps"][1][
            "result_projection_sha256"
        ],
        "gcapeps_input2": candidates["gcapeps"][2][
            "result_projection_sha256"
        ],
        "sdim": sdim["result_projection_sha256"],
    }
    core: dict[str, Any] = {
        "schema": COMPARATOR_SCHEMA,
        "role": "terminal_cross_artifact_comparator",
        "fixture_identity": {
            "fixture_projection_sha256": identity[
                "fixture_projection_sha256"
            ],
            "run_partition": identity["run_partition"],
            "case_id": identity["case_id"],
            "width": identity["width"],
            "rounds": identity["rounds"],
            "n_qubits": identity["n_qubits"],
            "candidate_checkpoints": list(identity["checkpoints"]),
        },
        "artifact_bindings": artifact_bindings,
        "pullback_join": pullback_join,
        "positive_bond32_gate": {
            "definition": {
                "configured_max_bond": 32,
                "minimum_full_bond_dimension": 33,
                "kept_bond_dimension": 32,
                "discarded_squared_weight_strictly_greater_than": (
                    POSITIVE_TAIL_THRESHOLD
                ),
                "cause": "max_bond",
            },
            "paths": positive_paths,
            "all_four_paths_positive": shared_positive,
        },
        "exact_dense_memory_witnesses": exact_dense_memory_witnesses,
        "candidate_bonds": {
            lane: {
                f"input{input_id}": candidates[lane][input_id]["bonds"]
                for input_id in (1, 2)
            }
            for lane in ("plain", "gcapeps")
        },
        "checkpoint_metrics": checkpoint_metrics,
        "final_bond32_faithfulness": {
            "round_index": final_round,
            "delta_f": delta_f,
            "per_path_class": {
                lane: {
                    f"input{input_id}": _faithfulness_class(
                        final_metrics[lane][f"input{input_id}"]["fidelity"]
                    )
                    for input_id in (1, 2)
                }
                for lane in ("plain", "gcapeps")
            },
            "shared_positive_truncation_eligible": shared_positive,
            "conditional_h_f_verdict_if_amendment_bound_stress_cell": (
                conditional_h_f_verdict
            ),
            "h_f_applicability_deferred_to_amendment_bound_stress_cell": True,
        },
        "max_sampled_comparator_array_bytes": (
            max_sampled_comparator_array_bytes
        ),
        "claim_boundary": (
            "bounded frozen pure-state finite-memory fixture comparison; "
            "not a generic PEPS contraction certificate, QEC Record, or "
            "optimized BLP measure"
        ),
        "result_projection_sha256": "",
    }
    core["result_projection_sha256"] = projection_sha256(core)
    validate_comparator_core(core)
    return core


_WHOLE_STATE_METRIC_KEYS = frozenset(
    {
        "fidelity_raw",
        "fidelity_roundoff_correction",
        "fidelity",
        "pure_state_trace_distance",
        "relative_state_distance",
        "relative_norm_distance",
        "d2_raw",
        "dinf_raw",
        "d2_normalized",
        "dinf_normalized",
        "reference_raw_norm",
        "candidate_raw_norm",
        "signed_raw_norm_error",
        "absolute_raw_norm_error",
        "entropy_von_neumann_error",
        "entropy_renyi2_error",
        "reduced_state_trace_distance",
    }
)
_FIXED_PAIR_METRIC_KEYS = frozenset(
    {
        "dense_fixed_pair_trace_distance",
        "candidate_fixed_pair_trace_distance",
        "absolute_trace_distance_error",
    }
)


def _derived_float_equal(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=1.0e-13, abs_tol=1.0e-15)


def _validate_whole_state_metric_projection(
    metric: Any,
    *,
    name: str,
) -> float:
    if not isinstance(metric, Mapping):
        raise TypeError(f"{name} must be an object")
    _require_exact_keys(metric, _WHOLE_STATE_METRIC_KEYS, name=name)
    values = {
        key: _finite_float(value, name=f"{name}.{key}")
        for key, value in metric.items()
    }
    raw = values["fidelity_raw"]
    correction = values["fidelity_roundoff_correction"]
    fidelity = values["fidelity"]
    reference_norm = values["reference_raw_norm"]
    candidate_norm = values["candidate_raw_norm"]
    nonnegative = _WHOLE_STATE_METRIC_KEYS - {"signed_raw_norm_error"}
    if any(values[key] < 0.0 for key in nonnegative):
        raise ValueError(f"{name} contains a negative metric")
    expected_correction = max(0.0, raw - 1.0)
    expected_fidelity = min(1.0, raw)
    if (
        raw > 1.0 + FIDELITY_ROUNDOFF_TOLERANCE
        or correction > FIDELITY_ROUNDOFF_TOLERANCE
        or reference_norm <= 0.0
        or candidate_norm <= 0.0
        or not _derived_float_equal(correction, expected_correction)
        or not _derived_float_equal(fidelity, expected_fidelity)
        or not _derived_float_equal(
            values["pure_state_trace_distance"],
            math.sqrt(1.0 - fidelity),
        )
        or not _derived_float_equal(
            values["signed_raw_norm_error"],
            candidate_norm - reference_norm,
        )
        or not _derived_float_equal(
            values["absolute_raw_norm_error"],
            abs(candidate_norm - reference_norm),
        )
        or not _derived_float_equal(
            values["relative_norm_distance"],
            2.0
            * abs(candidate_norm - reference_norm)
            / (candidate_norm + reference_norm),
        )
        or not _derived_float_equal(
            values["relative_state_distance"],
            2.0
            * values["d2_raw"]
            / (candidate_norm + reference_norm),
        )
        or values["dinf_raw"] > values["d2_raw"] + 1.0e-15
        or values["dinf_normalized"]
        > values["d2_normalized"] + 1.0e-15
        or values["relative_norm_distance"] > 2.0 + 1.0e-12
        or values["relative_state_distance"] > 2.0 + 1.0e-12
        or values["d2_normalized"] > 2.0 + 1.0e-12
        or values["reduced_state_trace_distance"] > 1.0 + 1.0e-12
    ):
        raise ValueError(f"{name} derived metric projection is inconsistent")
    return fidelity


def _validate_fixed_pair_metric_projection(metric: Any, *, name: str) -> None:
    if not isinstance(metric, Mapping):
        raise TypeError(f"{name} must be an object")
    _require_exact_keys(metric, _FIXED_PAIR_METRIC_KEYS, name=name)
    dense = _finite_float(
        metric["dense_fixed_pair_trace_distance"],
        name=f"{name}.dense_fixed_pair_trace_distance",
    )
    candidate = _finite_float(
        metric["candidate_fixed_pair_trace_distance"],
        name=f"{name}.candidate_fixed_pair_trace_distance",
    )
    error = _finite_float(
        metric["absolute_trace_distance_error"],
        name=f"{name}.absolute_trace_distance_error",
    )
    if (
        not 0.0 <= dense <= 1.0 + 1.0e-12
        or not 0.0 <= candidate <= 1.0 + 1.0e-12
        or not _derived_float_equal(error, abs(candidate - dense))
    ):
        raise ValueError(f"{name} is inconsistent")


def _validate_comparator_derived_sections(
    core: Mapping[str, Any],
    *,
    width: int,
    rounds: int,
    checkpoints: list[int],
    fixture_sha256: str,
) -> None:
    bindings = core["artifact_bindings"]
    binding_keys = {
        "fixture",
        "dense",
        "plain_input1",
        "plain_input2",
        "gcapeps_input1",
        "gcapeps_input2",
        "sdim",
    }
    if not isinstance(bindings, Mapping):
        raise TypeError("comparator artifact_bindings must be an object")
    _require_exact_keys(bindings, binding_keys, name="artifact_bindings")
    if bindings["fixture"] != fixture_sha256 or any(
        not _is_sha256(value) for value in bindings.values()
    ):
        raise ValueError("comparator artifact binding is invalid")

    pullback = core["pullback_join"]
    pullback_keys = {
        "expected_count",
        "sdim_count",
        "stim_count",
        "gc_count",
        "local_duplicates_rejected",
        "cross_gc_duplicates_rejected",
        "exact_unique_ordered_E_equals_S_equals_T_equals_G",
        "signed_values_equal_after_coverage",
        "joined_value_rows",
    }
    if not isinstance(pullback, Mapping):
        raise TypeError("comparator pullback_join must be an object")
    _require_exact_keys(pullback, pullback_keys, name="pullback_join")
    counts = [
        _plain_int(pullback[key], name=f"pullback_join.{key}")
        for key in ("expected_count", "sdim_count", "stim_count", "gc_count")
    ]
    rows = pullback["joined_value_rows"]
    if (
        len(set(counts)) != 1
        or not isinstance(rows, list)
        or len(rows) != counts[0]
        or any(
            pullback[key] is not True
            for key in (
                "local_duplicates_rejected",
                "cross_gc_duplicates_rejected",
                "exact_unique_ordered_E_equals_S_equals_T_equals_G",
                "signed_values_equal_after_coverage",
            )
        )
    ):
        raise ValueError("comparator pullback coverage is inconsistent")
    key_hashes = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise TypeError(f"pullback joined row {index} must be an object")
        _require_exact_keys(
            row,
            {"key_sha256", "sign", "body"},
            name=f"pullback joined row {index}",
        )
        if (
            not _is_sha256(row["key_sha256"])
            or isinstance(row["sign"], bool)
            or row["sign"] not in (-1, 1)
            or not isinstance(row["body"], str)
            or len(row["body"]) != 2 * width
            or any(label not in "IXYZ" for label in row["body"])
        ):
            raise ValueError(f"pullback joined row {index} is invalid")
        key_hashes.append(row["key_sha256"])
    if len(key_hashes) != len(set(key_hashes)):
        raise ValueError("pullback joined key hash is duplicated")

    gate = core["positive_bond32_gate"]
    if not isinstance(gate, Mapping):
        raise TypeError("positive_bond32_gate must be an object")
    _require_exact_keys(
        gate,
        {"definition", "paths", "all_four_paths_positive"},
        name="positive_bond32_gate",
    )
    definition = gate["definition"]
    expected_definition = {
        "configured_max_bond": 32,
        "minimum_full_bond_dimension": 33,
        "kept_bond_dimension": 32,
        "discarded_squared_weight_strictly_greater_than": (
            POSITIVE_TAIL_THRESHOLD
        ),
        "cause": "max_bond",
    }
    if definition != expected_definition:
        raise ValueError("positive bond-32 definition drifted")
    paths = gate["paths"]
    expected_path_ids = [
        ("plain", 1),
        ("plain", 2),
        ("gcapeps", 1),
        ("gcapeps", 2),
    ]
    if not isinstance(paths, list) or len(paths) != len(expected_path_ids):
        raise ValueError("positive bond-32 paths are incomplete")
    maximum_positive_full_by_path = {
        path_id: 0 for path_id in expected_path_ids
    }
    observed_positive = []
    for index, (row, expected_path) in enumerate(
        zip(paths, expected_path_ids, strict=True)
    ):
        if not isinstance(row, Mapping):
            raise TypeError(f"positive bond-32 path {index} must be an object")
        _require_exact_keys(
            row,
            {
                "lane",
                "input_id",
                "positive_bond32_event",
                "positive_event_count",
                "qualifying_event_locators",
            },
            name=f"positive bond-32 path {index}",
        )
        count = _plain_int(
            row["positive_event_count"],
            name=f"positive bond-32 path {index} count",
        )
        locators = row["qualifying_event_locators"]
        if (
            (row["lane"], row["input_id"]) != expected_path
            or not isinstance(row["positive_bond32_event"], bool)
            or not isinstance(locators, list)
            or len(locators) != count
            or row["positive_bond32_event"] is not (count > 0)
        ):
            raise ValueError(f"positive bond-32 path {index} is inconsistent")
        common_locator_keys = {
            "operation_index",
            "round_index",
            "full_bond_dimension",
            "kept_bond_dimension",
            "discarded_squared_weight",
            "configured_max_bond",
            "cause",
            "fixture_operation_class",
            "fixture_gate_kind",
            "fixture_targets",
            "fixture_collision_ordinal",
            "pre_split_state_sha256",
            "spectrum_producer_binding_sha256",
        }
        locator_keys = set(common_locator_keys)
        if row["lane"] == "gcapeps":
            locator_keys.update(
                {
                    "split_index",
                    "construction_epoch_before",
                    "construction_epoch_after",
                }
            )
        locator_identities: set[str] = set()
        for locator_index, locator in enumerate(locators):
            locator_name = (
                f"positive bond-32 path {index} locator {locator_index}"
            )
            if not isinstance(locator, Mapping):
                raise TypeError(f"{locator_name} must be an object")
            _require_exact_keys(locator, locator_keys, name=locator_name)
            _plain_int(
                locator["operation_index"],
                name=f"{locator_name}.operation_index",
            )
            locator_round = _plain_int(
                locator["round_index"],
                name=f"{locator_name}.round_index",
                minimum=1,
            )
            full_dimension = _plain_int(
                locator["full_bond_dimension"],
                name=f"{locator_name}.full_bond_dimension",
                minimum=33,
            )
            kept_dimension = _plain_int(
                locator["kept_bond_dimension"],
                name=f"{locator_name}.kept_bond_dimension",
                minimum=1,
            )
            discarded = _finite_float(
                locator["discarded_squared_weight"],
                name=f"{locator_name}.discarded_squared_weight",
            )
            operation_class = locator["fixture_operation_class"]
            targets = locator["fixture_targets"]
            collision_ordinal = locator["fixture_collision_ordinal"]
            if (
                locator_round > rounds
                or kept_dimension != 32
                or discarded <= POSITIVE_TAIL_THRESHOLD
                or locator["configured_max_bond"] != 32
                or locator["cause"] != "max_bond"
                or operation_class not in {"clifford", "collision_rotation"}
                or not isinstance(locator["fixture_gate_kind"], str)
                or not locator["fixture_gate_kind"]
                or not isinstance(targets, list)
                or not targets
                or len(targets) != len(set(targets))
                or any(
                    isinstance(site, bool)
                    or not isinstance(site, int)
                    or not 0 <= site < 2 * width
                    for site in targets
                )
                or not _is_sha256(locator["pre_split_state_sha256"])
                or not _is_sha256(
                    locator["spectrum_producer_binding_sha256"]
                )
                or (
                    operation_class == "collision_rotation"
                    and (
                        isinstance(collision_ordinal, bool)
                        or not isinstance(collision_ordinal, int)
                        or collision_ordinal < 0
                    )
                )
                or (
                    operation_class == "clifford"
                    and collision_ordinal is not None
                )
                or (row["lane"] == "plain" and len(targets) != 2)
                or (
                    row["lane"] == "gcapeps"
                    and operation_class != "collision_rotation"
                )
            ):
                raise ValueError(f"{locator_name} is inconsistent")
            if row["lane"] == "gcapeps":
                epoch_before = _plain_int(
                    locator["construction_epoch_before"],
                    name=f"{locator_name}.construction_epoch_before",
                )
                epoch_after = _plain_int(
                    locator["construction_epoch_after"],
                    name=f"{locator_name}.construction_epoch_after",
                )
                _plain_int(
                    locator["split_index"],
                    name=f"{locator_name}.split_index",
                )
                if epoch_after != epoch_before + 1:
                    raise ValueError(f"{locator_name} epoch is inconsistent")
            locator_identity = hashlib.sha256(
                canonical_json_bytes(locator)
            ).hexdigest()
            if locator_identity in locator_identities:
                raise ValueError(f"{locator_name} is duplicated")
            locator_identities.add(locator_identity)
            maximum_positive_full_by_path[expected_path] = max(
                maximum_positive_full_by_path[expected_path],
                full_dimension,
            )
        observed_positive.append(row["positive_bond32_event"])
    if (
        not isinstance(gate["all_four_paths_positive"], bool)
        or gate["all_four_paths_positive"] is not all(observed_positive)
    ):
        raise ValueError("positive bond-32 aggregate is inconsistent")

    bonds = core["candidate_bonds"]
    if not isinstance(bonds, Mapping):
        raise TypeError("candidate_bonds must be an object")
    _require_exact_keys(bonds, {"plain", "gcapeps"}, name="candidate_bonds")
    for lane in ("plain", "gcapeps"):
        by_input = bonds[lane]
        if not isinstance(by_input, Mapping):
            raise TypeError(f"candidate_bonds.{lane} must be an object")
        _require_exact_keys(
            by_input,
            {"input1", "input2"},
            name=f"candidate_bonds.{lane}",
        )
        for input_name, row in by_input.items():
            if not isinstance(row, Mapping):
                raise TypeError(f"candidate_bonds.{lane}.{input_name} invalid")
            _require_exact_keys(
                row,
                {
                    "max_exact_precompression_bond",
                    "max_committed_bond",
                    "final_committed_bond",
                },
                name=f"candidate_bonds.{lane}.{input_name}",
            )
            maximum = _plain_int(
                row["max_committed_bond"],
                name=f"candidate_bonds.{lane}.{input_name}.maximum",
                minimum=1,
            )
            final = _plain_int(
                row["final_committed_bond"],
                name=f"candidate_bonds.{lane}.{input_name}.final",
                minimum=1,
            )
            exact = row["max_exact_precompression_bond"]
            if (
                maximum > 32
                or final > maximum
                or (lane == "plain" and exact is not None)
            ):
                raise ValueError("candidate bond summary is inconsistent")
            if lane == "gcapeps":
                exact_value = _plain_int(
                    exact,
                    name=f"candidate_bonds.{lane}.{input_name}.exact",
                    minimum=1,
                )
                input_id = int(input_name[-1])
                if exact_value < maximum_positive_full_by_path[
                    (lane, input_id)
                ]:
                    raise ValueError(
                        "GC exact precompression bond is below a positive "
                        "locator full bond"
                    )

    metrics = core["checkpoint_metrics"]
    if not isinstance(metrics, list) or len(metrics) != len(checkpoints):
        raise ValueError("checkpoint_metrics cardinality is invalid")
    final_fidelities: dict[str, dict[str, float]] = {}
    for expected_round, checkpoint in zip(checkpoints, metrics, strict=True):
        if not isinstance(checkpoint, Mapping):
            raise TypeError("checkpoint metric row must be an object")
        _require_exact_keys(
            checkpoint,
            {"round_index", "plain", "gcapeps"},
            name=f"checkpoint metric {expected_round}",
        )
        if checkpoint["round_index"] != expected_round:
            raise ValueError("checkpoint metric order drifted")
        for lane in ("plain", "gcapeps"):
            lane_metrics = checkpoint[lane]
            if not isinstance(lane_metrics, Mapping):
                raise TypeError("checkpoint lane metrics must be an object")
            _require_exact_keys(
                lane_metrics,
                {"input1", "input2", "fixed_pair_checkpoint_error"},
                name=f"checkpoint {expected_round} {lane}",
            )
            fidelities = {
                input_name: _validate_whole_state_metric_projection(
                    lane_metrics[input_name],
                    name=f"checkpoint {expected_round} {lane} {input_name}",
                )
                for input_name in ("input1", "input2")
            }
            _validate_fixed_pair_metric_projection(
                lane_metrics["fixed_pair_checkpoint_error"],
                name=f"checkpoint {expected_round} {lane} fixed pair",
            )
            if expected_round == rounds:
                final_fidelities[lane] = fidelities

    faithfulness = core["final_bond32_faithfulness"]
    if not isinstance(faithfulness, Mapping):
        raise TypeError("final_bond32_faithfulness must be an object")
    _require_exact_keys(
        faithfulness,
        {
            "round_index",
            "delta_f",
            "per_path_class",
            "shared_positive_truncation_eligible",
            "conditional_h_f_verdict_if_amendment_bound_stress_cell",
            "h_f_applicability_deferred_to_amendment_bound_stress_cell",
        },
        name="final_bond32_faithfulness",
    )
    expected_delta = stress_delta_f(
        plain_fidelities=final_fidelities["plain"],
        gcapeps_fidelities=final_fidelities["gcapeps"],
    )
    expected_classes = {
        lane: {
            input_name: _faithfulness_class(value)
            for input_name, value in final_fidelities[lane].items()
        }
        for lane in ("plain", "gcapeps")
    }
    expected_conditional_h_f = (
        "INELIGIBLE_NO_SHARED_POSITIVE_TRUNCATION"
        if not gate["all_four_paths_positive"]
        else "supported"
        if expected_delta["direction"] == "gcapeps_higher"
        else "falsified"
        if expected_delta["direction"] == "plain_higher"
        else "tie/inconclusive"
    )
    if (
        faithfulness["round_index"] != rounds
        or faithfulness["delta_f"] != expected_delta
        or faithfulness["per_path_class"] != expected_classes
        or faithfulness["shared_positive_truncation_eligible"]
        is not gate["all_four_paths_positive"]
        or faithfulness[
            "h_f_applicability_deferred_to_amendment_bound_stress_cell"
        ]
        is not True
        or faithfulness[
            "conditional_h_f_verdict_if_amendment_bound_stress_cell"
        ]
        != expected_conditional_h_f
    ):
        raise ValueError("final bond-32 faithfulness is inconsistent")

    expected_claim_boundary = (
        "bounded frozen pure-state finite-memory fixture comparison; "
        "not a generic PEPS contraction certificate, QEC Record, or "
        "optimized BLP measure"
    )
    if core["claim_boundary"] != expected_claim_boundary:
        raise ValueError("comparator claim boundary drifted")


def validate_comparator_core(core: Mapping[str, Any]) -> None:
    _require_exact_keys(
        core,
        {
            "schema",
            "role",
            "fixture_identity",
            "artifact_bindings",
            "pullback_join",
            "positive_bond32_gate",
            "exact_dense_memory_witnesses",
            "candidate_bonds",
            "checkpoint_metrics",
            "final_bond32_faithfulness",
            "max_sampled_comparator_array_bytes",
            "claim_boundary",
            "result_projection_sha256",
        },
        name="comparator core",
    )
    if (
        core["schema"] != COMPARATOR_SCHEMA
        or core["role"] != "terminal_cross_artifact_comparator"
        or core["result_projection_sha256"] != projection_sha256(core)
    ):
        raise ValueError("comparator core identity or projection mismatch")
    fixture_identity = core["fixture_identity"]
    if not isinstance(fixture_identity, Mapping):
        raise TypeError("comparator fixture_identity must be an object")
    _require_exact_keys(
        fixture_identity,
        {
            "fixture_projection_sha256",
            "run_partition",
            "case_id",
            "width",
            "rounds",
            "n_qubits",
            "candidate_checkpoints",
        },
        name="comparator fixture_identity",
    )
    width = _plain_int(
        fixture_identity["width"],
        name="comparator fixture width",
        minimum=1,
    )
    rounds = _plain_int(
        fixture_identity["rounds"],
        name="comparator fixture rounds",
        minimum=1,
    )
    if (
        fixture_identity["n_qubits"] != 2 * width
        or not _is_sha256(fixture_identity["fixture_projection_sha256"])
        or not isinstance(fixture_identity["case_id"], str)
        or not fixture_identity["case_id"]
        or fixture_identity["run_partition"] not in {"CALIBRATION", "HELDOUT"}
        or fixture_identity["candidate_checkpoints"]
        != sorted({0, 1, 2, 4, rounds}.intersection(range(rounds + 1)))
    ):
        raise ValueError("comparator fixture identity is invalid")
    _validate_exact_dense_memory_witnesses(
        core["exact_dense_memory_witnesses"],
        width=width,
        rounds=rounds,
    )
    _plain_int(
        core["max_sampled_comparator_array_bytes"],
        name="max_sampled_comparator_array_bytes",
        minimum=1,
    )
    _validate_comparator_derived_sections(
        core,
        width=width,
        rounds=rounds,
        checkpoints=list(fixture_identity["candidate_checkpoints"]),
        fixture_sha256=fixture_identity["fixture_projection_sha256"],
    )


def run_comparator_worker(
    *,
    fixture: Mapping[str, Any],
    dense_core: Mapping[str, Any],
    plain_input1_core: Mapping[str, Any],
    plain_input2_core: Mapping[str, Any],
    gcapeps_input1_core: Mapping[str, Any],
    gcapeps_input2_core: Mapping[str, Any],
    sdim_core: Mapping[str, Any],
    timing_module: Any,
) -> dict[str, Any]:
    """Build standard two-frame output with a supervisor-injected timer owner."""

    timer = timing_module.LayeredTimer()
    with timer.span(
        "comparator.root",
        scope="terminal_comparator_total",
        kind="worker",
        lane="comparator",
        case_id=fixture.get("case_id"),
    ):
        with timer.span(
            "comparator.join_and_metrics",
            scope="independent_artifact_join_and_metrics",
            kind="comparison",
            lane="comparator",
            case_id=fixture.get("case_id"),
        ):
            core = build_comparator_core(
                fixture=fixture,
                dense_core=dense_core,
                plain_input1_core=plain_input1_core,
                plain_input2_core=plain_input2_core,
                gcapeps_input1_core=gcapeps_input1_core,
                gcapeps_input2_core=gcapeps_input2_core,
                sdim_core=sdim_core,
            )
        with timer.span(
            "comparator.serialize",
            scope="serialization",
            kind="canonical_core_encoding",
            lane="comparator",
            case_id=fixture.get("case_id"),
        ):
            core_bytes = canonical_json_bytes(core)
    timing = timer.finish()
    trailer_bytes = timing_module.build_late_telemetry_trailer(
        core_bytes, timing
    )
    return {
        "core": core,
        "core_bytes": core_bytes,
        "timing": timing,
        "trailer_bytes": trailer_bytes,
        "framed_bytes": timing_module.encode_two_frames(
            core_bytes, trailer_bytes
        ),
    }


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compute independent finite-memory comparison metrics"
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run a minimal metric-kernel smoke check",
    )
    arguments = parser.parse_args(argv)
    if not arguments.self_test:
        parser.error(
            "artifact transport is supervisor-owned; use --self-test for the "
            "standalone metric kernel"
        )
    vector = np.zeros(4, dtype=np.complex128)
    vector[0] = 1.0
    result = whole_state_metrics(vector, vector.copy(), width=1)
    sys.stdout.buffer.write(
        canonical_json_bytes(
            {
                "schema": COMPARATOR_SCHEMA,
                "self_test": True,
                "metrics": result,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
