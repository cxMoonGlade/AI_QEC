from __future__ import annotations

"""Axis-1 selected-channel state-evolution evidence.

This module applies schedule-selected local or union-support joint channels to a
small-N GPU density matrix in substep order. It is a carrier seam toward analog
execution: it proves that selected joint-L channels can be consumed by a
frontend state path, but it does not emit QEC records and does not claim logical
gate semantics.
"""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from qec_twin.forward.cptp_channel import measurement_probabilities_z
from qec_twin.forward.exact.circuit_sim import apply_channel_local, zero_state
from qec_twin.mechanisms.axis1_primitives import default_axis1_primitive_registry
from qec_twin.simulator.analog_schedule import (
    COMPILER_SCHEDULE_SEAL_SCHEMA,
    SubstepSchedule,
    has_valid_compiler_schedule_seal,
)
from qec_twin.simulator.artifacts import file_sha256, write_json
from qec_twin.simulator.axis1_channel_evidence import (
    AXIS1_CHANNEL_FORBIDDEN_OUTPUT_NAMES,
    AXIS1_CHANNEL_FORBIDDEN_OUTPUT_SUFFIXES,
    _assemble_selection_joint_channel,
    _axis1_primitive_params_for_schedule,
    _axis1_forbidden_artifact_path,
    _axis1_safe_evidence_output_path,
    _axis1_static_zz_calibrations_for_schedule,
    _coverage_manifest,
    _nominal_positive_dt,
    _validate_schedule_for_axis1_channel_evidence,
)
from qec_twin.simulator.axis1_selection import (
    Axis1MechanismSelection,
    axis1_selection_layers_in_schedule_order,
    axis1_selection_partition_manifest,
    build_axis1_schedule_selection_plan,
)


AXIS1_STATE_EVIDENCE_SCHEMA = "qec_twin.simulator.axis1_state_evolution_evidence.v1"
AXIS1_STATE_EVIDENCE_REPRESENTABILITY = (
    "axis1_selected_joint_channel_state_evidence_no_record_emission"
)
AXIS1_STATE_MAX_EXACT_QUBITS = 8


@dataclass(frozen=True)
class Axis1StateEvolutionEvidenceResult:
    """Files and manifest returned by `write_axis1_state_evolution_evidence`."""

    out_dir: Path
    state_evidence: Path
    manifest: dict[str, Any]
    content_hash: str


@dataclass(frozen=True)
class Axis1StateEvolutionFreezeResult:
    """Hash guard returned by `freeze_axis1_state_evolution_evidence`."""

    freeze_path: Path
    evidence_path: Path
    manifest: dict[str, Any]


def axis1_state_evolution_evidence_manifest(
    schedule: SubstepSchedule,
    *,
    device: str = "cuda",
) -> dict[str, Any]:
    """Apply selected Axis-1 joint channels to a small-N GPU density matrix."""

    _validate_state_evidence_schedule(schedule, device=device)
    selection_plan = build_axis1_schedule_selection_plan(schedule)
    selection_partition = axis1_selection_layers_in_schedule_order(
        schedule,
        selection_plan.selections,
        consumer_name="Axis-1 selected-window evidence",
    )
    selection_layers = tuple(layer.selections for layer in selection_partition)
    if not selection_layers:
        raise ValueError("Axis-1 state evidence requires at least one mechanism selection")

    state_evolution = _apply_selected_joint_channels(schedule, selection_layers, device=device)
    coverage = _coverage_manifest(schedule, selection_plan)
    trace_residual_passed = state_evolution["trace_residual"] <= 1.0e-8
    passed = trace_residual_passed and bool(coverage["full_positive_duration_coverage"])
    payload = {
        "schema": AXIS1_STATE_EVIDENCE_SCHEMA,
        "verdict": "pass" if passed else "fail",
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "representability": AXIS1_STATE_EVIDENCE_REPRESENTABILITY,
        "compiler_provenance": {
            "schedule_seal_schema": COMPILER_SCHEDULE_SEAL_SCHEMA,
            "schedule_seal_valid": has_valid_compiler_schedule_seal(schedule),
            "schedule_seal_public": False,
            "generated_substeps": all(
                substep.generated_by_compiler for substep in schedule.substeps
            ),
        },
        "primitive_registry": default_axis1_primitive_registry().to_manifest(),
        "selection_plan": selection_plan.to_manifest(),
        "selection_partition": axis1_selection_partition_manifest(selection_partition),
        "coverage": coverage,
        "metric_reference": "docs/METRICS.md#forward-fidelity--coupling-metrics",
        "representability_limits": (
            "selected local or union-support joint channels applied to a small-N "
            "density matrix; no analog record emission, no full schedule operation "
            "semantics, no Axis-2 source timeline, no leakage/qutrit integration"
        ),
        "state_evolution": state_evolution,
        "trace_residual_passed": trace_residual_passed,
        "passed": passed,
    }
    payload["content_hash"] = _stable_payload_hash(payload)
    return payload


def write_axis1_state_evolution_evidence(
    schedule: SubstepSchedule,
    out_dir: str | Path,
    *,
    device: str = "cuda",
    filename: str = "axis1_state_evolution.json",
) -> Axis1StateEvolutionEvidenceResult:
    """Write only the Axis-1 selected-channel state-evolution manifest."""

    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    _assert_clean_axis1_state_evidence_dir(root)
    path = _axis1_safe_evidence_output_path(
        root,
        filename,
        writer_name="Axis-1 state evidence writer",
    )
    manifest = axis1_state_evolution_evidence_manifest(schedule, device=device)
    write_json(path, manifest)
    return Axis1StateEvolutionEvidenceResult(
        out_dir=root,
        state_evidence=path,
        manifest=manifest,
        content_hash=str(manifest["content_hash"]),
    )


def freeze_axis1_state_evolution_evidence(
    evidence_path: str | Path,
    *,
    freeze_path: str | Path | None = None,
    overwrite: bool = False,
) -> Axis1StateEvolutionFreezeResult:
    """Write or validate a freeze manifest for Axis-1 state evidence."""

    evidence_path = Path(evidence_path)
    manifest = _load_state_evidence_manifest(evidence_path)
    _validate_state_evidence_content_hash(manifest, evidence_path)
    out = Path(freeze_path) if freeze_path is not None else _default_freeze_path(evidence_path)
    if out.exists() and not overwrite:
        validate_axis1_state_evolution_freeze(out)
        return Axis1StateEvolutionFreezeResult(
            freeze_path=out,
            evidence_path=evidence_path,
            manifest=json.loads(out.read_text()),
        )
    state = manifest["state_evolution"]
    payload = {
        "schema": "qec_twin.simulator.axis1_state_evolution_freeze.v1",
        "evidence_file": evidence_path.name,
        "evidence_sha256": file_sha256(evidence_path),
        "evidence_schema": manifest["schema"],
        "evidence_content_hash": manifest["content_hash"],
        "source_kind": manifest["source_kind"],
        "source_hash": manifest["source_hash"],
        "verdict": manifest["verdict"],
        "passed": bool(manifest["passed"]),
        "applied_channel_count": int(state["applied_channel_count"]),
        "trace_residual": float(state["trace_residual"]),
        "full_positive_duration_coverage": bool(
            manifest["coverage"]["full_positive_duration_coverage"]
        ),
        "primitive_registry_id": manifest["primitive_registry"]["registry_id"],
        "epistemic_classes": {
            "evidence_sha256": "a/c",
            "evidence_content_hash": "a/c",
            "trace_residual": "c",
            "full_positive_duration_coverage": "a/c",
        },
    }
    write_json(out, payload)
    return Axis1StateEvolutionFreezeResult(
        freeze_path=out,
        evidence_path=evidence_path,
        manifest=payload,
    )


def validate_axis1_state_evolution_freeze(freeze_path: str | Path) -> dict[str, Any]:
    """Validate that frozen state evidence did not drift."""

    path = Path(freeze_path)
    freeze = _load_state_freeze_manifest(path)
    evidence_path = path.parent / str(freeze["evidence_file"])
    manifest = _load_state_evidence_manifest(evidence_path)
    sha = file_sha256(evidence_path)
    if sha != freeze["evidence_sha256"]:
        raise ValueError(
            "Axis-1 state evidence sha256 mismatch: "
            f"frozen={freeze['evidence_sha256']} current={sha}"
        )
    _validate_state_evidence_content_hash(manifest, evidence_path)
    state = manifest["state_evolution"]
    checks = {
        "evidence_schema": manifest.get("schema") == freeze["evidence_schema"],
        "evidence_content_hash": manifest.get("content_hash")
        == freeze["evidence_content_hash"],
        "source_kind": manifest.get("source_kind") == freeze["source_kind"],
        "source_hash": manifest.get("source_hash") == freeze["source_hash"],
        "verdict": manifest.get("verdict") == freeze["verdict"],
        "passed": bool(manifest.get("passed")) == bool(freeze["passed"]),
        "applied_channel_count": int(state["applied_channel_count"])
        == int(freeze["applied_channel_count"]),
        "trace_residual": float(state["trace_residual"]) == float(freeze["trace_residual"]),
        "full_positive_duration_coverage": bool(
            manifest["coverage"]["full_positive_duration_coverage"]
        )
        == bool(freeze["full_positive_duration_coverage"]),
        "primitive_registry_id": manifest.get("primitive_registry", {}).get("registry_id")
        == freeze["primitive_registry_id"],
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise ValueError(f"Axis-1 state freeze metadata mismatch: {failed}")
    return {
        "schema": "qec_twin.simulator.axis1_state_evolution_freeze_validation.v1",
        "freeze_file": path.name,
        "evidence_file": evidence_path.name,
        "evidence_sha256": sha,
        "evidence_content_hash": manifest.get("content_hash"),
        "checks": checks,
        "pass": True,
    }


def _apply_selected_joint_channels(
    schedule: SubstepSchedule,
    selection_layers: tuple[tuple[Axis1MechanismSelection, ...], ...],
    *,
    device: str,
) -> dict[str, Any]:
    import torch

    dev = _require_cuda_device(device)
    params = _axis1_primitive_params_for_schedule(schedule)
    static_zz_calibrations = _axis1_static_zz_calibrations_for_schedule(schedule)
    rho = zero_state(schedule.num_qubits, device=dev)
    applied_steps: list[dict[str, Any]] = []
    applied_layers: list[dict[str, Any]] = []

    for layer_index, layer in enumerate(selection_layers):
        layer_steps: list[str] = []
        for selection in layer:
            dt = _nominal_positive_dt(selection)
            assembled = _assemble_selection_joint_channel(
                selection,
                dt_ns=dt,
                params=params,
                device=dev,
                static_zz_calibrations=static_zz_calibrations,
            )
            kraus = assembled.kraus
            rho = apply_channel_local(rho, kraus, selection.participant, schedule.num_qubits)
            trace_after = float(torch.trace(rho).real.item())
            application_index = len(applied_steps)
            layer_steps.append(selection.selection_id)
            applied_steps.append(
                {
                    "application_index": application_index,
                    "parallel_layer_index": layer_index,
                    "selection_id": selection.selection_id,
                    "substep_id": selection.substep_id,
                    "row_kind": selection.row_kind,
                    "participant": list(selection.participant),
                    "coupling_edges": [list(edge) for edge in selection.coupling_edges],
                    "primitive_names": list(selection.primitive_names),
                    "mechanism_pair": list(selection.mechanism_pair),
                    "context_mechanisms": list(selection.context_mechanisms),
                    "dt_ns": dt,
                    "dt_ns_nominal": selection.dt_ns_nominal,
                    "dt_ns_bracket": list(selection.dt_ns_bracket),
                    "operation_names": list(selection.operation_names),
                    "source_step_indices": list(selection.source_step_indices),
                    "ideal_controls": [
                        record.to_manifest() for record in assembled.ideal_controls.records
                    ],
                    "lowered_mechanisms": [
                        record.to_manifest() for record in assembled.primitive_bundle.records
                    ],
                    "channel_assembly": {
                        "assembled_by": (
                            "qec_twin.forward.joint_lindbladian.assemble_substep_channel"
                        ),
                        "assembly_semantics": "single_joint_generator_expm",
                        "contains_ideal_control_hamiltonian": bool(
                            assembled.ideal_controls.records
                        ),
                        "ideal_control_names": [
                            record.name for record in assembled.ideal_controls.records
                        ],
                        "contains_serialized_channel_payload": False,
                        "num_kraus": int(kraus.shape[0]),
                        "dimension": int(kraus.shape[-1]),
                    },
                    "trace_after_application": trace_after,
                }
            )
        applied_layers.append(
            {
                "parallel_layer_index": layer_index,
                "substep_id": layer[0].substep_id,
                "selection_ids": layer_steps,
                "window_count": len(layer),
                "same_substep_semantics": (
                    "parallel_disjoint_local_windows_or_single_union_support"
                ),
            }
        )

    trace = float(torch.trace(rho).real.item())
    probs = measurement_probabilities_z(rho).detach().to("cpu").tolist()
    return {
        "initial_state": "computational_zero_density_matrix",
        "device": dev,
        "dtype": str(rho.dtype).replace("torch.", ""),
        "num_qubits": int(schedule.num_qubits),
        "applied_channel_count": len(applied_steps),
        "application_semantics": (
            "schedule_order_selected_joint_channels_with_parallel_disjoint_or_union_support_layers"
        ),
        "same_substep_window_semantics": (
            "selected windows sharing a substep must either be qubit-disjoint or represented "
            "as a single union-support joint channel; overlapping selected windows fail closed"
        ),
        "claims_logical_gate_semantics": False,
        "claims_record_emission": False,
        "claims_full_schedule_coverage": False,
        "claims_overlapping_window_joint_generator": False,
        "claims_axis2_source_projection": False,
        "final_trace": trace,
        "trace_residual": abs(trace - 1.0),
        "trace_residual_threshold": 1.0e-8,
        "final_z_probabilities": [float(p) for p in probs],
        "final_z_probability_order": "computational_basis_qubit0_msb",
        "applied_layers": applied_layers,
        "applied_steps": applied_steps,
        "epistemic_classes": {
            "joint_generator_application_semantics": "a",
            "trace_residual_threshold": "c",
            "final_z_probabilities": "c",
        },
    }


def _validate_state_evidence_schedule(schedule: SubstepSchedule, *, device: str) -> None:
    _require_cuda_device(device)
    _validate_schedule_for_axis1_channel_evidence(schedule)
    if int(schedule.num_qubits) > AXIS1_STATE_MAX_EXACT_QUBITS:
        raise ValueError(
            "Axis-1 state evolution evidence uses exact density matrices and is "
            f"currently capped at {AXIS1_STATE_MAX_EXACT_QUBITS} qubits; "
            f"got num_qubits={schedule.num_qubits}"
        )


def _schedule_order_selection_layers(
    schedule: SubstepSchedule,
    selections: tuple[Axis1MechanismSelection, ...],
) -> tuple[tuple[Axis1MechanismSelection, ...], ...]:
    return tuple(
        layer.selections
        for layer in axis1_selection_layers_in_schedule_order(
            schedule,
            selections,
            consumer_name="Axis-1 selected-window evidence",
        )
    )


def _schedule_order_unique_selections(
    schedule: SubstepSchedule,
    selections: tuple[Axis1MechanismSelection, ...],
) -> tuple[Axis1MechanismSelection, ...]:
    """Compatibility helper returning the flattened schedule-order selection list."""

    return tuple(
        selection
        for layer in _schedule_order_selection_layers(schedule, selections)
        for selection in layer
    )


def _require_cuda_device(device: str) -> str:
    import torch

    dev = str(device)
    if not dev.startswith("cuda"):
        raise ValueError(f"Axis-1 state evolution evidence is GPU-only; got device={dev!r}")
    if not torch.cuda.is_available():
        raise RuntimeError("Axis-1 state evolution evidence requires CUDA; CPU fallback is disabled")
    return dev


def _assert_clean_axis1_state_evidence_dir(root: Path) -> None:
    stale = [
        path.name
        for path in sorted(root.iterdir())
        if path.is_file()
        and _axis1_forbidden_artifact_path(path)
    ]
    if stale:
        raise ValueError(
            "Axis-1 state evidence writer refuses simulator-run artifact directories; "
            f"found stale artifact(s): {stale}"
        )


def _stable_payload_hash(payload: dict[str, Any]) -> str:
    without_hash = dict(payload)
    without_hash.pop("content_hash", None)
    data = json.dumps(
        without_hash,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _default_freeze_path(evidence_path: Path) -> Path:
    return evidence_path.with_name(f"{evidence_path.stem}.freeze.json")


def _load_state_evidence_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    data = json.loads(path.read_text())
    if data.get("schema") != AXIS1_STATE_EVIDENCE_SCHEMA:
        raise ValueError(
            f"{path} is not an Axis-1 state-evidence manifest: schema={data.get('schema')!r}"
        )
    return data


def _load_state_freeze_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    data = json.loads(path.read_text())
    if data.get("schema") != "qec_twin.simulator.axis1_state_evolution_freeze.v1":
        raise ValueError(
            f"{path} is not an Axis-1 state-evidence freeze: schema={data.get('schema')!r}"
        )
    required = {
        "schema",
        "evidence_file",
        "evidence_sha256",
        "evidence_schema",
        "evidence_content_hash",
        "source_kind",
        "source_hash",
        "verdict",
        "passed",
        "applied_channel_count",
        "trace_residual",
        "full_positive_duration_coverage",
        "primitive_registry_id",
    }
    missing = sorted(required.difference(data))
    if missing:
        raise ValueError(f"Axis-1 state freeze manifest missing fields: {missing}")
    evidence_file = Path(str(data["evidence_file"]))
    if evidence_file.name != str(data["evidence_file"]) or evidence_file.is_absolute():
        raise ValueError("Axis-1 state freeze evidence_file must be a local filename")
    return data


def _validate_state_evidence_content_hash(manifest: dict[str, Any], path: Path) -> None:
    expected = _stable_payload_hash(manifest)
    actual = manifest.get("content_hash")
    if actual != expected:
        raise ValueError(
            "Axis-1 state evidence content_hash mismatch for "
            f"{path}: manifest={actual!r} recomputed={expected!r}"
        )


__all__ = [
    "AXIS1_STATE_EVIDENCE_REPRESENTABILITY",
    "AXIS1_STATE_EVIDENCE_SCHEMA",
    "Axis1StateEvolutionEvidenceResult",
    "Axis1StateEvolutionFreezeResult",
    "axis1_state_evolution_evidence_manifest",
    "freeze_axis1_state_evolution_evidence",
    "validate_axis1_state_evolution_freeze",
    "write_axis1_state_evolution_evidence",
]
