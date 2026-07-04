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
# CircuitIR's metadata as an internal transport (noise_spec.py sets it; stim_source.py extracts it) and is
# surfaced ONLY through a separate evaluator-only field (CompiledCircuit.source_projection_audit,
# visibility='evaluator_only'). The learner-visible CompiledCircuit.metadata uses the clean pre-projection
# circuit and never carries it (tests/test_simulator_source_projection asserts `source_timeline` is absent
# from the learner manifest). The public-metadata guard therefore SKIPS this subtree — it is not
# learner-visible truth. (Must match noise_spec.SOURCE_PROJECTION_AUDIT_METADATA_KEY /
# analog_schedule._SOURCE_PROJECTION_AUDIT_METADATA_KEY.)
_EVALUATOR_ONLY_AUDIT_KEYS = frozenset({"_source_projection_evaluator_audit"})


def validate_public_metadata(metadata: dict[str, Any] | None, *, label: str = "metadata") -> dict:
    """Return a copied public metadata dict after rejecting evaluator-truth keys."""

    copied = dict(metadata or {})
    _validate_keys(copied, path=label)
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


def _validate_keys(value: Any, *, path: str) -> None:
    if isinstance(value, dict):
        for raw_key, item in value.items():
            key = str(raw_key)
            if key in _EVALUATOR_ONLY_AUDIT_KEYS:
                # Declared evaluator-only audit transport; never learner-visible (see constant above).
                continue
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
            _validate_keys(item, path=f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for i, item in enumerate(value):
            _validate_keys(item, path=f"{path}[{i}]")
