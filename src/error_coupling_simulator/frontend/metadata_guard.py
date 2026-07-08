from __future__ import annotations

"""Learner-visible metadata guards for the simulator frontend."""

from collections.abc import Mapping, Sequence
import math
from typing import Any

AXIS1_STATIC_ZZ_COUPLINGS_METADATA_KEY = "axis1_static_zz_couplings"
AXIS1_STATIC_ZZ_CALIBRATIONS_METADATA_KEY = "axis1_static_zz_calibrations"

_RESERVED_METADATA_KEY_PARTS = (
    "analog_truth",
    "axis1_error",
    "axis2_error",
    "baseline_noise",
    "cudaqx_noise",
    "cudaqx_error",
    "channel_truth",
    "dem_error_model",
    "error_ids",
    "error_model",
    "exact_channel",
    "evaluator_truth",
    "ground_truth",
    "hidden_state",
    "joint_lindbladian_truth",
    "kraus",
    "leakage_trace",
    "mechanism_truth",
    "oracle",
    "process_matrix",
    "ptm",
    "si1000_noise",
    "si1000_error",
    "source_binding",
    "source_fanout",
    "source_payload",
    "source_process",
    "source_trace",
    "source_timeline",
    "source_trajectory",
    "teacher_id",
)
_RESERVED_METADATA_EXACT_KEYS = (
    "axis",
    "axis1",
    "axis2",
    "baseline",
    "cudaqx",
    "error",
    "noise_model",
    "si1000",
)

# `_source_projection_evaluator_audit` is a DECLARED evaluator-only audit that rides in the TRANSIENT noisy
# CircuitIR's metadata as an internal transport (noise_spec.py sets it AT THE METADATA ROOT; stim_source.py
# extracts it from the root) and is surfaced ONLY through a separate evaluator-only field
# (CompiledCircuit.source_projection_audit, visibility='evaluator_only'). The learner-visible
# CompiledCircuit.metadata uses the clean pre-projection circuit and never carries it
# (tests/test_simulator_source_projection asserts `source_timeline` is absent from the learner manifest).
#
# FAIL-CLOSED: by DEFAULT the guard REJECTS this key at EVERY position (top level and nested). It is skipped
# ONLY when the caller explicitly opts in via `allow_evaluator_audit_transport=True`, which is passed by the
# SINGLE internal construction that legitimately carries it: the transient noisy CircuitIR (gated by
# `_allow_noise_steps`, see circuit_ir.py). Every learner-visible boundary — CompiledCircuit, OperationSpec,
# CodeSpec, and any user-built CircuitIR — uses the default and therefore rejects the key. This closes a
# guard-bypass: without it, wrapping ANY reserved Axis-2 key under a TOP-LEVEL audit key would smuggle it
# verbatim into the stored learner-visible metadata (copied into CompiledCircuit.metadata and serialized
# into the run manifest at simulator.py `circuit_metadata`, entirely outside the schedule compiler's reject
# guard). It also aligns this data boundary with the schedule compiler, which rejects a top-level audit key
# outright (analog_schedule._reject_projected_or_noisy_circuit) and recurses for nested Axis-2 truth
# (analog_schedule._find_axis2_source_metadata_path). (Must match
# noise_spec.SOURCE_PROJECTION_AUDIT_METADATA_KEY / analog_schedule._SOURCE_PROJECTION_AUDIT_METADATA_KEY.)
_EVALUATOR_ONLY_AUDIT_KEYS = frozenset({"_source_projection_evaluator_audit"})


def validate_public_metadata(
    metadata: dict[str, Any] | None,
    *,
    label: str = "metadata",
    allow_evaluator_audit_transport: bool = False,
) -> dict:
    """Return a copied public metadata dict after rejecting evaluator-truth keys.

    ``allow_evaluator_audit_transport`` is an INTERNAL opt-in (default False = fail-closed):
    only the transient noisy ``CircuitIR`` produced by the noise pipeline sets it True (gated
    by ``_allow_noise_steps``) so its declared TOP-LEVEL ``_source_projection_evaluator_audit``
    transport survives. Every learner-visible boundary uses the default and rejects that key at
    every position. See ``_EVALUATOR_ONLY_AUDIT_KEYS`` above.
    """

    copied = dict(metadata or {})
    _validate_keys(copied, path=label, allow_audit_transport=bool(allow_evaluator_audit_transport))
    return copied


def normalize_axis1_static_zz_couplings(
    raw_edges: Any,
    *,
    num_qubits: int | None = None,
    label: str = AXIS1_STATIC_ZZ_COUPLINGS_METADATA_KEY,
) -> tuple[tuple[int, int], ...]:
    """Normalize public static-ZZ device/schedule edges without adding physics truth."""

    if raw_edges in (None, ()):
        return ()
    if not isinstance(raw_edges, Sequence) or isinstance(raw_edges, (str, bytes)):
        raise ValueError(f"{label} must be a sequence of two-qubit edges")
    nq = None if num_qubits is None else int(num_qubits)
    if nq is not None and nq <= 0:
        raise ValueError(f"{label} num_qubits must be positive, got {nq}")
    edges: list[tuple[int, int]] = []
    for i, raw_edge in enumerate(raw_edges):
        if not isinstance(raw_edge, Sequence) or isinstance(raw_edge, (str, bytes)):
            raise ValueError(f"{label}[{i}] must be a two-qubit edge")
        if len(raw_edge) != 2:
            raise ValueError(f"{label}[{i}] must contain exactly two qubit indices")
        a, b = (int(raw_edge[0]), int(raw_edge[1]))
        if a == b:
            raise ValueError(f"{label}[{i}] has duplicate endpoint {a}")
        for q in (a, b):
            if q < 0:
                raise ValueError(f"{label}[{i}] endpoint {q} must be non-negative")
            if nq is not None and q >= nq:
                raise ValueError(f"{label}[{i}] endpoint {q} outside [0, {nq})")
        edge = (a, b) if a < b else (b, a)
        edges.append(edge)
    if len(set(edges)) != len(edges):
        raise ValueError(f"{label} must not contain duplicate edges")
    return tuple(sorted(edges))


def normalize_axis1_static_zz_calibrations(
    raw_calibrations: Any,
    *,
    num_qubits: int | None = None,
    declared_edges: Sequence[Sequence[int]] | None = None,
    label: str = AXIS1_STATIC_ZZ_CALIBRATIONS_METADATA_KEY,
) -> dict[tuple[int, int], dict[str, Any]]:
    """Normalize public per-edge static-ZZ calibration metadata."""

    if raw_calibrations in (None, (), {}):
        return {}
    nq = None if num_qubits is None else int(num_qubits)
    declared = None
    if declared_edges is not None:
        declared = set(
            normalize_axis1_static_zz_couplings(
                declared_edges,
                num_qubits=nq,
                label=f"{label}.declared_edges",
            )
        )
    records = (
        _static_zz_calibration_records_from_mapping(raw_calibrations, label=label)
        if isinstance(raw_calibrations, Mapping)
        else _static_zz_calibration_records_from_sequence(raw_calibrations, label=label)
    )
    out: dict[tuple[int, int], dict[str, Any]] = {}
    for i, record in enumerate(records):
        edge = normalize_axis1_static_zz_couplings(
            (record["edge"],),
            num_qubits=nq,
            label=f"{label}[{i}].edge",
        )[0]
        if declared is not None and edge not in declared:
            raise ValueError(
                f"{label}[{i}] edge {edge!r} is not declared in "
                f"{AXIS1_STATIC_ZZ_COUPLINGS_METADATA_KEY}"
            )
        if edge in out:
            raise ValueError(f"{label} must not contain duplicate edge calibration {edge!r}")
        zeta = float(record["zeta_rad_per_ns"])
        if not math.isfinite(zeta) or zeta < 0.0:
            raise ValueError(f"{label}[{i}].zeta_rad_per_ns must be finite and non-negative")
        epistemic_class = str(record.get("epistemic_class", "c"))
        if epistemic_class not in {"b", "c"}:
            raise ValueError(f"{label}[{i}].epistemic_class must be 'b' or 'c'")
        out[edge] = {
            "zeta_rad_per_ns": zeta,
            "epistemic_class": epistemic_class,
        }
    return dict(sorted(out.items()))


def axis1_static_zz_calibrations_to_manifest(
    calibrations: Mapping[tuple[int, int], Mapping[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Return JSON-safe static-ZZ calibration records in deterministic order."""

    normalized = normalize_axis1_static_zz_calibrations(calibrations or {})
    return [
        {
            "edge": [edge[0], edge[1]],
            "zeta_rad_per_ns": payload["zeta_rad_per_ns"],
            "epistemic_class": payload["epistemic_class"],
        }
        for edge, payload in normalized.items()
    ]


def _static_zz_calibration_records_from_mapping(
    raw: Mapping[Any, Any],
    *,
    label: str,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for raw_edge, raw_value in raw.items():
        edge = _parse_static_zz_edge_key(raw_edge, label=label)
        if isinstance(raw_value, Mapping):
            value = dict(raw_value)
            value["edge"] = edge
        else:
            value = {"edge": edge, "zeta_rad_per_ns": raw_value}
        records.append(value)
    return records


def _static_zz_calibration_records_from_sequence(
    raw: Any,
    *,
    label: str,
) -> list[dict[str, Any]]:
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ValueError(f"{label} must be a sequence of calibration records")
    records: list[dict[str, Any]] = []
    for i, item in enumerate(raw):
        if not isinstance(item, Mapping):
            raise ValueError(f"{label}[{i}] must be a calibration record")
        record = dict(item)
        edge = record.get("edge", record.get("qubits"))
        if edge is None:
            raise ValueError(f"{label}[{i}] must contain 'edge'")
        if "zeta_rad_per_ns" not in record:
            raise ValueError(f"{label}[{i}] must contain 'zeta_rad_per_ns'")
        record["edge"] = edge
        records.append(record)
    return records


def _parse_static_zz_edge_key(raw_edge: Any, *, label: str) -> tuple[int, int]:
    if isinstance(raw_edge, str):
        parts = raw_edge.replace("-", ",").replace(" ", "").split(",")
        if len(parts) != 2 or not all(parts):
            raise ValueError(f"{label} mapping key {raw_edge!r} must encode two qubits")
        return (int(parts[0]), int(parts[1]))
    if isinstance(raw_edge, Sequence) and not isinstance(raw_edge, (str, bytes)):
        if len(raw_edge) != 2:
            raise ValueError(f"{label} mapping key {raw_edge!r} must contain two qubits")
        return (int(raw_edge[0]), int(raw_edge[1]))
    raise ValueError(f"{label} mapping key {raw_edge!r} must encode two qubits")


def _validate_keys(
    value: Any, *, path: str, is_root: bool = True, allow_audit_transport: bool = False
) -> None:
    if isinstance(value, dict):
        for raw_key, item in value.items():
            key = str(raw_key)
            if key in _EVALUATOR_ONLY_AUDIT_KEYS:
                if is_root and allow_audit_transport:
                    # Declared evaluator-only audit transport on the INTERNAL transient noisy CircuitIR
                    # (the only construction that opts in via _allow_noise_steps). Skip its subtree — it
                    # legitimately carries source truth and is extracted into the evaluator-only
                    # CompiledCircuit.source_projection_audit before any learner sees it (see constant).
                    continue
                if is_root:
                    # Top level on a LEARNER-VISIBLE object (default, fail-closed). The audit key is an
                    # internal source-projection transport, never learner metadata. Rejecting it closes
                    # the guard-bypass where a top-level audit key smuggles any wrapped Axis-2 key into
                    # the stored metadata / run manifest, outside the schedule compiler's reject guard.
                    raise ValueError(
                        "learner-visible metadata cannot carry the evaluator-only audit transport; "
                        f"reserved key {path}.{key!s} is an internal source-projection transport "
                        "(permitted only on the transient noisy CircuitIR), not learner-visible "
                        "metadata. Use evaluator_sidecars with visibility='evaluator_only'."
                    )
                # A NESTED audit key is never the declared (top-level-only) transport. Reject it so a
                # reserved Axis-2 key cannot hide under an audit subtree and survive into the STORED
                # learner-visible metadata. Aligns this boundary's depth scope with the schedule
                # compiler's analog_schedule._find_axis2_source_metadata_path full recursion.
                raise ValueError(
                    "learner-visible metadata cannot nest the evaluator-only audit transport; "
                    f"reserved key {path}.{key!s} is permitted only at the top level of the transient "
                    "noisy CircuitIR. Use evaluator_sidecars with visibility='evaluator_only'."
                )
            normalized = key.lower().replace("-", "_").replace(" ", "_")
            if normalized in _RESERVED_METADATA_EXACT_KEYS:
                raise ValueError(
                    "learner-visible metadata cannot contain evaluator/error-model semantics; "
                    f"reserved key {path}.{key!s} matches exact key {normalized!r}. "
                    "Put runnable noise in NoiseSpec and evaluator truth in evaluator_sidecars."
                )
            for reserved in _RESERVED_METADATA_KEY_PARTS:
                if reserved in normalized:
                    raise ValueError(
                        "learner-visible metadata cannot contain evaluator truth; "
                        f"reserved key {path}.{key!s} matches {reserved!r}. "
                        "Use evaluator_sidecars with visibility='evaluator_only'."
                    )
            # Nested subtrees are never the declared transport: recurse fail-closed (audit rejected).
            _validate_keys(item, path=f"{path}.{key}", is_root=False)
    elif isinstance(value, (list, tuple)):
        for i, item in enumerate(value):
            _validate_keys(item, path=f"{path}[{i}]", is_root=False)
