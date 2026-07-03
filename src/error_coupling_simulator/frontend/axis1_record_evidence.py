from __future__ import annotations

"""Axis-1 selected-channel measurement-record evidence.

This is the narrow record-emission carrier after selected joint-channel state
evidence. It enumerates Pauli-basis measurement branches on a small-N GPU
density matrix and returns exact measurement, detector, and logical-observable
record arrays when the schedule carries public XOR wiring. X/Y boundaries are
handled by exact basis rotations around the Z enumerator. It can also sample
`.b8` record carriers, but still does not write DEM or decoder artifacts.
An optional ``params_for_substep`` callable overrides the schedule-global
Axis-1 primitive params once per selected substep (the per-round param seam a
coupled teacher drives); the emitter never derives round indices itself, and
the default ``None`` path is byte-identical to the schedule-global read.
"""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from ..carrier.cptp_channel import RDTYPE
from ..carrier.exact.circuit_sim import (
    apply_channel_local,
    apply_unitary,
    measure_qubit_enumerate,
    pauli_x,
    project_qubit,
    zero_state,
)
from ..mechanisms.axis1_primitives import (
    Axis1PrimitiveParams,
    default_axis1_primitive_registry,
)
from .analog_schedule import (
    AnalogSubstepIR,
    COMPILER_SCHEDULE_SEAL_SCHEMA,
    SubstepOperation,
    SubstepSchedule,
    has_valid_compiler_schedule_seal,
)
from .artifacts import write_json
from .artifacts import file_sha256, record_summary, write_b8_optional
from .axis1_channel_evidence import (
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
from .axis1_selection import (
    Axis1MechanismSelection,
    axis1_selection_layers_in_schedule_order,
    axis1_selection_partition_manifest,
    build_axis1_schedule_selection_plan,
)
from .axis1_state_evidence import (
    _require_cuda_device,
)


AXIS1_RECORD_EVIDENCE_SCHEMA = "qec_twin.simulator.axis1_measurement_record_evidence.v1"
AXIS1_RECORD_EVIDENCE_REPRESENTABILITY = (
    "axis1_selected_joint_channel_record_evidence_no_b8_or_decoder"
)


@dataclass(frozen=True)
class Axis1MeasurementRecordEvidenceResult:
    """Files and manifest returned by `write_axis1_measurement_record_evidence`."""

    out_dir: Path
    record_evidence: Path
    manifest: dict[str, Any]
    content_hash: str


@dataclass(frozen=True)
class Axis1MeasurementRecordSampleResult:
    """Files returned by `write_axis1_measurement_record_samples`."""

    out_dir: Path
    exact_evidence: Path
    detection_events: Path | None
    obs_flips_actual: Path | None
    sample_summary: Path
    exact_manifest: dict[str, Any]
    sample_manifest: dict[str, Any]


@dataclass(frozen=True)
class Axis1MeasurementRecordFreezeResult:
    """Freeze manifest returned by `freeze_axis1_measurement_record_evidence`."""

    freeze_path: Path
    evidence_path: Path
    manifest: dict[str, Any]


@dataclass(frozen=True)
class Axis1ReadoutResetInstrumentSpec:
    """Explicit noisy record/preparation instrument for Axis-1 record evidence.

    Readout probabilities act on the reported classical measurement record after
    exact branch enumeration. Reset probability is a qubit preparation flip
    applied after an ideal reset in the reset basis. These are intentionally not
    Hamiltonian or collapse-operator primitives.
    """

    readout_p0_to_1: float = 0.0
    readout_p1_to_0: float = 0.0
    readout_pair_flip_probability: float = 0.0
    reset_flip_probability: float = 0.0
    source: str = "heuristic_readout_reset_instrument_v1"
    epistemic_class: str = "c"

    def __post_init__(self) -> None:
        for field_name in (
            "readout_p0_to_1",
            "readout_p1_to_0",
            "readout_pair_flip_probability",
            "reset_flip_probability",
        ):
            value = float(getattr(self, field_name))
            if not (0.0 <= value <= 1.0):
                raise ValueError(f"{field_name} must be in [0, 1], got {value!r}")
            object.__setattr__(self, field_name, value)
        object.__setattr__(self, "source", str(self.source))
        object.__setattr__(self, "epistemic_class", str(self.epistemic_class))
        if self.epistemic_class not in {"a", "b", "c"}:
            raise ValueError(f"invalid epistemic_class {self.epistemic_class!r}")

    @property
    def has_readout_assignment(self) -> bool:
        return (
            self.readout_p0_to_1 > 0.0
            or self.readout_p1_to_0 > 0.0
            or self.readout_pair_flip_probability > 0.0
        )

    @property
    def has_reset_noise(self) -> bool:
        return self.reset_flip_probability > 0.0

    @property
    def is_trivial(self) -> bool:
        return not self.has_readout_assignment and not self.has_reset_noise

    def to_manifest(self) -> dict[str, Any]:
        return {
            "schema": "qec_twin.simulator.axis1_readout_reset_instrument_spec.v1",
            "source": self.source,
            "epistemic_class": self.epistemic_class,
            "active": not self.is_trivial,
            "readout_p0_to_1": self.readout_p0_to_1,
            "readout_p1_to_0": self.readout_p1_to_0,
            "readout_pair_flip_probability": self.readout_pair_flip_probability,
            "readout_pair_policy": "adjacent_keys_within_same_measurement_operation",
            "reset_flip_probability": self.reset_flip_probability,
            "semantics": {
                "readout_assignment": (
                    "classical reported-record stochastic map after exact branch enumeration"
                ),
                "readout_pair_flip": (
                    "same-operation adjacent-key pair both-flip event; heuristic crosstalk carrier"
                ),
                "reset_flip": "post-reset preparation flip in the reset basis",
            },
            "claims_joint_lindbladian": False,
            "claims_axis2_source_projection": False,
            "claims_leakage_or_mist": False,
        }


def axis1_measurement_record_evidence_manifest(
    schedule: SubstepSchedule,
    *,
    device: str = "cuda",
    instrument_spec: Axis1ReadoutResetInstrumentSpec | None = None,
    params_for_substep: Callable[[AnalogSubstepIR], Axis1PrimitiveParams] | None = None,
) -> dict[str, Any]:
    """Return exact measurement-record evidence for a small-N local schedule.

    ``params_for_substep`` optionally overrides the single schedule-global
    Axis-1 primitive-params read: it is called exactly once for each substep
    that carries selected joint channels (schedule order, before that substep's
    selections are assembled) and must return the ``Axis1PrimitiveParams`` used
    for every selection in that substep. The emitter stays agnostic to HOW a
    round index is derived — the callable owns that
    (``AnalogSubstepIR.round_index`` is compiler-hardcoded ``None``; derive
    rounds from ``tick_index`` or measurement-key prefixes instead). Substeps
    without selected channels (barriers, resets, measurements without explicit
    durations) are never resolved. Default ``None`` keeps the manifest
    byte-identical to the schedule-global path: the ``params_resolution`` key
    is added only when a callable is supplied.
    """

    _validate_record_evidence_schedule(schedule, device=device)
    if params_for_substep is not None and not callable(params_for_substep):
        raise TypeError(
            "params_for_substep must be a callable substep -> Axis1PrimitiveParams "
            f"or None; got {type(params_for_substep).__name__}"
        )
    instrument = instrument_spec or Axis1ReadoutResetInstrumentSpec()
    selection_plan = build_axis1_schedule_selection_plan(schedule)
    selection_partition = axis1_selection_layers_in_schedule_order(
        schedule,
        selection_plan.selections,
        consumer_name="Axis-1 selected-window evidence",
    )
    selection_layers = tuple(layer.selections for layer in selection_partition)
    if not selection_layers:
        raise ValueError("Axis-1 measurement record evidence requires mechanism selections")

    record_evidence = _enumerate_measurement_records(
        schedule,
        selection_layers,
        device=device,
        instrument_spec=instrument,
        params_for_substep=params_for_substep,
    )
    coverage = _coverage_manifest(schedule, selection_plan)
    probability_residual_passed = record_evidence["total_probability_residual"] <= 1.0e-8
    passed = probability_residual_passed and bool(coverage["full_positive_duration_coverage"])
    payload = {
        "schema": AXIS1_RECORD_EVIDENCE_SCHEMA,
        "verdict": "pass" if passed else "fail",
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "representability": AXIS1_RECORD_EVIDENCE_REPRESENTABILITY,
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
        "readout_reset_instrument_spec": instrument.to_manifest(),
        "coverage": coverage,
        "metric_reference": "docs/METRICS.md#forward-fidelity--coupling-metrics",
        "representability_limits": (
            "selected local or union-support joint channels plus exact Pauli-basis "
            "measurement branch enumeration; detector/logical records only when "
            "public XOR wiring is present, no .b8 artifact, no decoder output, "
            "no Axis-2 source timeline, no leakage/qutrit integration"
        ),
        "record_evidence": record_evidence,
        "probability_residual_passed": probability_residual_passed,
        "passed": passed,
    }
    # Added ONLY when a callable is supplied so the default-None payload (and its
    # content_hash / freeze guards) stays byte-identical to the schedule-global path.
    if params_for_substep is not None:
        payload["params_resolution"] = "per_substep_callable"
    payload["content_hash"] = _stable_payload_hash(payload)
    return payload


def write_axis1_measurement_record_evidence(
    schedule: SubstepSchedule,
    out_dir: str | Path,
    *,
    device: str = "cuda",
    filename: str = "axis1_measurement_records.json",
    instrument_spec: Axis1ReadoutResetInstrumentSpec | None = None,
) -> Axis1MeasurementRecordEvidenceResult:
    """Write only the Axis-1 measurement-record evidence manifest."""

    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    _assert_clean_axis1_record_evidence_dir(root)
    path = _axis1_safe_evidence_output_path(
        root,
        filename,
        writer_name="Axis-1 measurement record evidence writer",
    )
    manifest = axis1_measurement_record_evidence_manifest(
        schedule,
        device=device,
        instrument_spec=instrument_spec,
    )
    write_json(path, manifest)
    return Axis1MeasurementRecordEvidenceResult(
        out_dir=root,
        record_evidence=path,
        manifest=manifest,
        content_hash=str(manifest["content_hash"]),
    )


def write_axis1_measurement_record_samples(
    schedule: SubstepSchedule,
    out_dir: str | Path,
    *,
    shots: int,
    seed: int = 0,
    device: str = "cuda",
    instrument_spec: Axis1ReadoutResetInstrumentSpec | None = None,
    params_for_substep: Callable[[AnalogSubstepIR], Axis1PrimitiveParams] | None = None,
) -> Axis1MeasurementRecordSampleResult:
    """Sample Axis-1 detector/logical records on CUDA and write `.b8` carriers.

    This writer intentionally does not write `.stim`, `.dem`, or decoder outputs:
    the selected joint-L records are not a Stim-Pauli/DEM model.
    ``params_for_substep`` is threaded into the exact record-evidence manifest
    (see `axis1_measurement_record_evidence_manifest`); sampling itself is
    params-independent.
    """

    import numpy as np
    import torch

    shot_count = int(shots)
    if shot_count <= 0:
        raise ValueError(f"shots must be positive, got {shots!r}")
    dev = _require_cuda_device(device)
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    _assert_clean_axis1_sample_dir(root)

    exact = axis1_measurement_record_evidence_manifest(
        schedule,
        device=dev,
        instrument_spec=instrument_spec,
        params_for_substep=params_for_substep,
    )
    record = exact["record_evidence"]
    probabilities = torch.tensor(record["record_probabilities"], dtype=torch.float64, device=dev)
    if probabilities.ndim != 1 or probabilities.numel() == 0:
        raise ValueError("Axis-1 record sampling requires a non-empty probability vector")
    probabilities = probabilities / probabilities.sum()
    generator = torch.Generator(device=dev).manual_seed(int(seed))
    sample_index = torch.multinomial(
        probabilities,
        num_samples=shot_count,
        replacement=True,
        generator=generator,
    )
    det_table = torch.tensor(record["detector_records"], dtype=torch.uint8, device=dev)
    obs_table = torch.tensor(record["logical_observable_records"], dtype=torch.uint8, device=dev)
    det_samples = det_table.index_select(0, sample_index).to("cpu").numpy().astype(np.bool_)
    obs_samples = obs_table.index_select(0, sample_index).to("cpu").numpy().astype(np.bool_)

    exact_path = root / "axis1_measurement_records.json"
    det_path = write_b8_optional(root / "detection_events.b8", det_samples)
    obs_path = write_b8_optional(root / "obs_flips_actual.b8", obs_samples)
    summary_path = root / "axis1_sample_summary.json"

    write_json(exact_path, exact)
    summary = record_summary(det_samples, obs_samples)
    summary.update(
        {
            "schema": "qec_twin.simulator.axis1_record_sample_summary.v1",
            "representability": "axis1_jointL_record_samples_b8_no_dem_no_decoder",
            "exact_evidence_file": exact_path.name,
            "exact_evidence_content_hash": exact["content_hash"],
            "shots": shot_count,
            "seed": int(seed),
            "device": dev,
            "sample_source": "torch.multinomial_on_cuda_from_exact_axis1_record_distribution",
            "claims_dem_artifact": False,
            "claims_decoder_integration": False,
            "claims_stim_pauli_model": False,
            "artifacts": {
                "detection_events": _sample_file_entry(det_path, record["detector_records_emitted"]),
                "obs_flips_actual": _sample_file_entry(
                    obs_path,
                    record["logical_observables_emitted"],
                ),
                "detector_error_model": None,
                "decoder_results": None,
            },
            "exact_detector_marginals": list(record["detector_marginals"]),
            "exact_logical_observable_marginals": list(
                record["logical_observable_marginals"]
            ),
            "epistemic_classes": {
                "sampling_from_exact_record_distribution": "a",
                "finite_shot_sample_marginals": "c",
                "b8_encoding": "a",
                "dem_non_emission": "a",
            },
        }
    )
    summary["content_hash"] = _stable_payload_hash(summary)
    write_json(summary_path, summary)
    return Axis1MeasurementRecordSampleResult(
        out_dir=root,
        exact_evidence=exact_path,
        detection_events=det_path,
        obs_flips_actual=obs_path,
        sample_summary=summary_path,
        exact_manifest=exact,
        sample_manifest=summary,
    )


def freeze_axis1_measurement_record_evidence(
    record_evidence: str | Path,
    freeze_path: str | Path | None = None,
    *,
    overwrite: bool = False,
) -> Axis1MeasurementRecordFreezeResult:
    """Write or validate a deterministic freeze guard for record evidence."""

    evidence_path = Path(record_evidence)
    manifest = _load_record_evidence_manifest(evidence_path)
    _validate_record_evidence_content_hash(manifest, evidence_path)
    sha = file_sha256(evidence_path)
    if sha is None:
        raise FileNotFoundError(evidence_path)
    out = Path(freeze_path) if freeze_path is not None else _default_freeze_path(evidence_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and not overwrite:
        existing = _load_record_freeze_manifest(out)
        if existing["evidence_file"] != evidence_path.name:
            raise ValueError(
                "Axis-1 record-evidence freeze evidence_file mismatch: "
                f"freeze={existing['evidence_file']!r} requested={evidence_path.name!r}"
            )
        validate_axis1_measurement_record_freeze(out)
        return Axis1MeasurementRecordFreezeResult(
            freeze_path=out,
            evidence_path=evidence_path,
            manifest=existing,
        )

    record = manifest.get("record_evidence", {})
    coverage = manifest.get("coverage", {})
    payload = {
        "schema": "qec_twin.simulator.axis1_measurement_record_freeze.v1",
        "evidence_file": evidence_path.name,
        "evidence_schema": manifest.get("schema"),
        "evidence_sha256": sha,
        "evidence_content_hash": manifest.get("content_hash"),
        "source_kind": manifest.get("source_kind"),
        "source_hash": manifest.get("source_hash"),
        "verdict": manifest.get("verdict"),
        "passed": bool(manifest.get("passed")),
        "representability": manifest.get("representability"),
        "record_count": int(record.get("record_count", -1)),
        "measurement_key_count": len(record.get("measurement_keys", [])),
        "detector_count": len(record.get("detector_names", [])),
        "logical_observable_count": len(record.get("logical_observable_names", [])),
        "applied_channel_count": int(record.get("applied_channel_count", -1)),
        "measurement_basis": record.get("measurement_basis"),
        "full_positive_duration_coverage": bool(
            coverage.get("full_positive_duration_coverage")
        ),
        "primitive_registry_id": manifest.get("primitive_registry", {}).get("registry_id"),
        "scope": (
            "Axis-1 measurement-record carrier evidence freeze only; not DEM, "
            "not decoder integration, not Axis-2 source projection"
        ),
    }
    write_json(out, payload)
    return Axis1MeasurementRecordFreezeResult(
        freeze_path=out,
        evidence_path=evidence_path,
        manifest=payload,
    )


def validate_axis1_measurement_record_freeze(freeze_path: str | Path) -> dict[str, Any]:
    """Validate that frozen record evidence did not drift."""

    path = Path(freeze_path)
    freeze = _load_record_freeze_manifest(path)
    evidence_path = path.parent / str(freeze["evidence_file"])
    manifest = _load_record_evidence_manifest(evidence_path)
    sha = file_sha256(evidence_path)
    if sha != freeze["evidence_sha256"]:
        raise ValueError(
            "Axis-1 record evidence sha256 mismatch: "
            f"frozen={freeze['evidence_sha256']} current={sha}"
        )
    _validate_record_evidence_content_hash(manifest, evidence_path)
    record = manifest.get("record_evidence", {})
    coverage = manifest.get("coverage", {})
    checks = {
        "evidence_schema": manifest.get("schema") == freeze["evidence_schema"],
        "evidence_content_hash": manifest.get("content_hash")
        == freeze["evidence_content_hash"],
        "source_kind": manifest.get("source_kind") == freeze["source_kind"],
        "source_hash": manifest.get("source_hash") == freeze["source_hash"],
        "verdict": manifest.get("verdict") == freeze["verdict"],
        "passed": bool(manifest.get("passed")) == bool(freeze["passed"]),
        "representability": manifest.get("representability") == freeze["representability"],
        "record_count": int(record.get("record_count", -1)) == int(freeze["record_count"]),
        "measurement_key_count": len(record.get("measurement_keys", []))
        == int(freeze["measurement_key_count"]),
        "detector_count": len(record.get("detector_names", [])) == int(freeze["detector_count"]),
        "logical_observable_count": len(record.get("logical_observable_names", []))
        == int(freeze["logical_observable_count"]),
        "applied_channel_count": int(record.get("applied_channel_count", -1))
        == int(freeze["applied_channel_count"]),
        "measurement_basis": record.get("measurement_basis") == freeze["measurement_basis"],
        "full_positive_duration_coverage": bool(
            coverage.get("full_positive_duration_coverage")
        )
        == bool(freeze["full_positive_duration_coverage"]),
        "primitive_registry_id": manifest.get("primitive_registry", {}).get("registry_id")
        == freeze["primitive_registry_id"],
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise ValueError(f"Axis-1 record freeze metadata mismatch: {failed}")
    return {
        "schema": "qec_twin.simulator.axis1_measurement_record_freeze_validation.v1",
        "freeze_file": path.name,
        "evidence_file": evidence_path.name,
        "evidence_sha256": sha,
        "evidence_content_hash": manifest.get("content_hash"),
        "checks": checks,
        "pass": True,
    }


def _enumerate_measurement_records(
    schedule: SubstepSchedule,
    selection_layers: tuple[tuple[Axis1MechanismSelection, ...], ...],
    *,
    device: str,
    instrument_spec: Axis1ReadoutResetInstrumentSpec,
    params_for_substep: Callable[[AnalogSubstepIR], Axis1PrimitiveParams] | None = None,
) -> dict[str, Any]:
    import torch

    dev = _require_cuda_device(device)
    selection_layers_by_substep = {layer[0].substep_id: layer for layer in selection_layers}
    params = _axis1_primitive_params_for_schedule(schedule)
    static_zz_calibrations = _axis1_static_zz_calibrations_for_schedule(schedule)
    rho = zero_state(schedule.num_qubits, device=dev).unsqueeze(0)
    outcomes = torch.zeros((1, 0), dtype=RDTYPE, device=dev)
    measurement_keys: list[str] = []
    applied_steps: list[dict[str, Any]] = []
    applied_layers: list[dict[str, Any]] = []
    reset_steps: list[dict[str, Any]] = []
    measurement_steps: list[dict[str, Any]] = []

    for substep in schedule.substeps:
        layer = selection_layers_by_substep.get(substep.substep_id)
        if layer is not None:
            # Resolved exactly ONCE per substep (never per selection): every
            # selection in a substep shares the substep's tick/round, so a single
            # resolution is exact for per-round variation (ledger S1).
            step_params = (
                params
                if params_for_substep is None
                else _resolve_substep_params(params_for_substep, substep)
            )
            layer_index = len(applied_layers)
            layer_steps: list[str] = []
            for selection in layer:
                dt = _nominal_positive_dt(selection)
                assembled = _assemble_selection_joint_channel(
                    selection,
                    dt_ns=dt,
                    params=step_params,
                    device=dev,
                    static_zz_calibrations=static_zz_calibrations,
                )
                kraus = assembled.kraus
                rho = _apply_channel_to_branches(
                    rho,
                    kraus,
                    selection.participant,
                    schedule.num_qubits,
                )
                layer_steps.append(selection.selection_id)
                applied_steps.append(
                    {
                        "application_index": len(applied_steps),
                        "parallel_layer_index": layer_index,
                        "selection_id": selection.selection_id,
                        "substep_id": selection.substep_id,
                        "row_kind": selection.row_kind,
                        "participant": list(selection.participant),
                        "coupling_edges": [list(edge) for edge in selection.coupling_edges],
                        "primitive_names": list(selection.primitive_names),
                        "mechanism_pair": list(selection.mechanism_pair),
                        "context_mechanisms": list(selection.context_mechanisms),
                        "ideal_controls": [
                            record.to_manifest() for record in assembled.ideal_controls.records
                        ],
                        "lowered_mechanisms": [
                            record.to_manifest()
                            for record in assembled.primitive_bundle.records
                        ],
                        "dt_ns": dt,
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
                    }
                )
            applied_layers.append(
                {
                    "parallel_layer_index": layer_index,
                    "substep_id": substep.substep_id,
                    "selection_ids": layer_steps,
                    "window_count": len(layer),
                    "same_substep_semantics": (
                        "parallel_disjoint_local_windows_or_single_union_support"
                    ),
                }
            )

        if substep.kind == "reset":
            for op in substep.operations:
                rho, reset_noise = _reset_operation(
                    rho,
                    op,
                    num_qubits=schedule.num_qubits,
                    instrument_spec=instrument_spec,
                )
                reset_step = {
                    "substep_id": substep.substep_id,
                    "operation": op.to_manifest(),
                    "reset_semantics": _reset_semantics_for_operation(op),
                }
                if reset_noise:
                    reset_step["reset_noise"] = reset_noise
                reset_steps.append(reset_step)
            continue
        if substep.kind != "measurement":
            continue
        for op in substep.operations:
            rho, outcomes, new_keys, measurement_reset_noise = _measure_operation(
                rho,
                outcomes,
                op,
                num_qubits=schedule.num_qubits,
                instrument_spec=instrument_spec,
            )
            measurement_keys.extend(new_keys)
            measurement_step = {
                "substep_id": substep.substep_id,
                "operation": op.to_manifest(),
                "measurement_keys": list(new_keys),
                "reset_after_measurement": bool(op.reset_after_measurement),
            }
            if measurement_reset_noise:
                measurement_step["reset_noise"] = measurement_reset_noise
            measurement_steps.append(measurement_step)

    if not measurement_keys:
        raise ValueError("Axis-1 measurement record evidence requires at least one measurement")

    probs = torch.diagonal(rho, dim1=-2, dim2=-1).real.sum(-1)
    measurement_records_gpu, probs, readout_assignment_steps = _apply_readout_assignment_instrument(
        outcomes.to(torch.int64),
        probs,
        measurement_keys,
        measurement_steps,
        instrument_spec,
    )
    total_probability = float(probs.sum().item())
    measurement_records = measurement_records_gpu.detach().to(torch.int64).to("cpu")
    record_probabilities = probs.detach().to("cpu")
    detector_records, detector_defs = _xor_records(
        measurement_records,
        measurement_keys,
        schedule.record_layout_ref.get("detectors", ()),
    )
    logical_records, observable_defs = _xor_records(
        measurement_records,
        measurement_keys,
        schedule.record_layout_ref.get("observables", ()),
    )
    measurement_bases = sorted(
        {
            str(step["operation"].get("basis", "Z"))
            for step in measurement_steps
        }
    )
    return {
        "initial_state": "computational_zero_density_matrix",
        "device": dev,
        "dtype": str(rho.dtype).replace("torch.", ""),
        "num_qubits": int(schedule.num_qubits),
        "applied_channel_count": len(applied_steps),
        "application_semantics": (
            "schedule_order_selected_joint_channels_with_parallel_disjoint_or_union_support_layers_then_measurements"
        ),
        "same_substep_window_semantics": (
            "selected windows sharing a substep must either be qubit-disjoint or represented "
            "as a single union-support joint channel; overlapping selected windows fail closed"
        ),
        "measurement_basis": "Z" if measurement_bases == ["Z"] else "mixed_pauli",
        "measurement_bases": measurement_bases,
        "measurement_basis_semantics": (
            "X/Y measurements and resets are implemented by exact basis rotation "
            "before Z-branch enumeration and rotation back afterward"
        ),
        "reset_steps": reset_steps,
        "readout_reset_instrument_spec": instrument_spec.to_manifest(),
        "readout_assignment_steps": readout_assignment_steps,
        "measurement_keys": measurement_keys,
        "measurement_steps": measurement_steps,
        "measurement_records": measurement_records.tolist(),
        "record_probabilities": [float(p) for p in record_probabilities.tolist()],
        "record_count": int(measurement_records_gpu.shape[0]),
        "total_probability": total_probability,
        "total_probability_residual": abs(total_probability - 1.0),
        "total_probability_residual_threshold": 1.0e-8,
        "applied_layers": applied_layers,
        "applied_steps": applied_steps,
        "detector_records_emitted": bool(detector_defs),
        "logical_observables_emitted": bool(observable_defs),
        "detector_names": [str(item["name"]) for item in detector_defs],
        "logical_observable_names": [str(item["name"]) for item in observable_defs],
        "detector_records": detector_records.tolist(),
        "logical_observable_records": logical_records.tolist(),
        "detector_marginals": _weighted_marginals(detector_records, record_probabilities),
        "logical_observable_marginals": _weighted_marginals(
            logical_records,
            record_probabilities,
        ),
        "claims_b8_artifact": False,
        "claims_decoder_integration": False,
        "claims_full_schedule_coverage": False,
        "claims_overlapping_window_joint_generator": False,
        "claims_axis2_source_projection": False,
        "record_layout_ref": dict(schedule.record_layout_ref),
        "detector_observable_boundary": "public schedule XOR wiring only; no decoder output",
        "epistemic_classes": {
            "joint_channel_application_semantics": "a",
            "measurement_branch_enumeration": "a",
            "readout_assignment_map_application": "a",
            "readout_assignment_probability_values": (
                instrument_spec.epistemic_class
                if instrument_spec.has_readout_assignment
                else "a"
            ),
            "reset_flip_channel_application": "a",
            "reset_flip_probability_values": (
                instrument_spec.epistemic_class
                if instrument_spec.has_reset_noise
                else "a"
            ),
            "probability_residual_threshold": "c",
            "detector_logical_xor_projection": "a",
            "b8_non_emission": "a",
        },
    }


def _resolve_substep_params(
    params_for_substep: Callable[[AnalogSubstepIR], Axis1PrimitiveParams],
    substep: AnalogSubstepIR,
) -> Axis1PrimitiveParams:
    """Resolve injected per-substep params; fail loudly on a wrong return type.

    The callable owns round derivation (``AnalogSubstepIR.round_index`` is
    compiler-hardcoded ``None`` — key off ``tick_index`` or measurement-key
    prefixes, never that dead field).
    """

    resolved = params_for_substep(substep)
    if not isinstance(resolved, Axis1PrimitiveParams):
        raise TypeError(
            "params_for_substep must return Axis1PrimitiveParams for substep "
            f"{substep.substep_id!r}; got {type(resolved).__name__}"
        )
    return resolved


def _measure_operation(
    rho,
    outcomes,
    op: SubstepOperation,
    *,
    num_qubits: int,
    instrument_spec: Axis1ReadoutResetInstrumentSpec,
):
    if op.basis not in {"X", "Y", "Z"}:
        raise ValueError(
            "Axis-1 measurement record evidence currently supports only Pauli-basis "
            f"measurements; got {op.basis!r} for {op.name!r}"
        )
    if len(op.targets) != len(op.measurement_keys):
        raise ValueError(
            f"measurement operation keys {op.measurement_keys} do not match targets {op.targets}"
        )
    keys: list[str] = []
    reset_noise_steps: list[dict[str, Any]] = []
    for target, key in zip(op.targets, op.measurement_keys, strict=True):
        rotation = _basis_pre_rotation(op.basis, rho.device)
        if rotation is not None:
            rho = apply_unitary(rho, rotation, [int(target)], num_qubits)
        rho, outcomes = measure_qubit_enumerate(
            rho,
            outcomes,
            int(target),
            num_qubits,
            reset=op.reset_after_measurement,
        )
        if op.reset_after_measurement and instrument_spec.reset_flip_probability > 0.0:
            rho = _apply_reset_flip_channel(
                rho,
                int(target),
                num_qubits,
                probability=instrument_spec.reset_flip_probability,
            )
            reset_noise_steps.append(
                {
                    "target": int(target),
                    "measurement_key": str(key),
                    "basis": str(op.basis),
                    "flip_probability": instrument_spec.reset_flip_probability,
                    "epistemic_class": instrument_spec.epistemic_class,
                    "semantics": "post_measurement_reset_preparation_flip_before_basis_rotation_back",
                }
            )
        if rotation is not None:
            rho = apply_unitary(
                rho,
                rotation.conj().transpose(-1, -2),
                [int(target)],
                num_qubits,
            )
        keys.append(str(key))
    return rho, outcomes, keys, reset_noise_steps


def _reset_operation(
    rho,
    op: SubstepOperation,
    *,
    num_qubits: int,
    instrument_spec: Axis1ReadoutResetInstrumentSpec,
):
    reset_basis = _reset_basis(op.name)
    if reset_basis is None:
        raise ValueError(
            "Axis-1 measurement record evidence currently supports only Pauli-basis "
            f"standalone reset operations; got {op.name!r}"
        )
    reset_noise_steps: list[dict[str, Any]] = []
    for target in op.targets:
        rho = _reset_qubit_to_basis_zero(
            rho,
            int(target),
            num_qubits,
            basis=reset_basis,
            reset_flip_probability=instrument_spec.reset_flip_probability,
        )
        if instrument_spec.reset_flip_probability > 0.0:
            reset_noise_steps.append(
                {
                    "target": int(target),
                    "basis": reset_basis,
                    "flip_probability": instrument_spec.reset_flip_probability,
                    "epistemic_class": instrument_spec.epistemic_class,
                    "semantics": "standalone_post_reset_preparation_flip",
                }
            )
    return rho, reset_noise_steps


def _reset_basis(name: str) -> str | None:
    if name in {"R", "RZ"}:
        return "Z"
    if name == "RX":
        return "X"
    if name == "RY":
        return "Y"
    return None


def _reset_semantics_for_operation(op: SubstepOperation) -> str:
    basis = _reset_basis(op.name)
    if basis == "Z":
        return "nonselective_z_reset_to_zero_no_record"
    if basis in {"X", "Y"}:
        return f"nonselective_{basis.lower()}_reset_to_plus_eigenstate_no_record"
    raise ValueError(f"unsupported standalone reset operation {op.name!r}")


def _reset_qubit_to_basis_zero(
    rho,
    qubit: int,
    num_qubits: int,
    *,
    basis: str,
    reset_flip_probability: float = 0.0,
):
    rotation = _basis_pre_rotation(basis, rho.device)
    if rotation is not None:
        rho = apply_unitary(rho, rotation, [qubit], num_qubits)
    rho = _reset_qubit_to_zero(rho, qubit, num_qubits)
    if reset_flip_probability > 0.0:
        rho = _apply_reset_flip_channel(
            rho,
            qubit,
            num_qubits,
            probability=reset_flip_probability,
        )
    if rotation is not None:
        rho = apply_unitary(
            rho,
            rotation.conj().transpose(-1, -2),
            [qubit],
            num_qubits,
        )
    return rho


def _apply_reset_flip_channel(rho, qubit: int, num_qubits: int, *, probability: float):
    import torch

    p = float(probability)
    if not (0.0 <= p <= 1.0):
        raise ValueError(f"reset flip probability must be in [0, 1], got {p!r}")
    if p == 0.0:
        return rho
    identity = torch.eye(2, dtype=rho.dtype, device=rho.device)
    x_op = pauli_x(rho.device).to(dtype=rho.dtype)
    kraus = torch.stack(
        [
            torch.sqrt(torch.as_tensor(1.0 - p, dtype=RDTYPE, device=rho.device)).to(rho.dtype)
            * identity,
            torch.sqrt(torch.as_tensor(p, dtype=RDTYPE, device=rho.device)).to(rho.dtype)
            * x_op,
        ]
    )
    return _apply_channel_to_branches(rho, kraus, (qubit,), num_qubits)


def _reset_qubit_to_zero(rho, qubit: int, num_qubits: int):
    rho0 = project_qubit(rho, qubit, 0, num_qubits)
    rho1 = project_qubit(rho, qubit, 1, num_qubits)
    rho1_to_zero = apply_unitary(rho1, pauli_x(rho.device), [qubit], num_qubits)
    return rho0 + rho1_to_zero


def _basis_pre_rotation(basis: str | None, device):
    if basis is None or basis == "Z":
        return None

    import torch

    cdt = torch.complex128
    inv_sqrt2 = 2.0**-0.5
    H = inv_sqrt2 * torch.tensor(
        [[1.0, 1.0], [1.0, -1.0]],
        dtype=cdt,
        device=device,
    )
    if basis == "X":
        return H
    if basis == "Y":
        Sdg = torch.tensor(
            [[1.0, 0.0], [0.0, -1.0j]],
            dtype=cdt,
            device=device,
        )
        return H @ Sdg
    raise ValueError(f"unsupported Pauli measurement/reset basis {basis!r}")


def _apply_channel_to_branches(rho, kraus, targets, num_qubits: int):
    import torch

    if rho.dim() == 2:
        return apply_channel_local(rho, kraus, targets, num_qubits)
    branches = [
        apply_channel_local(rho[index], kraus, targets, num_qubits)
        for index in range(int(rho.shape[0]))
    ]
    return torch.stack(branches, dim=0)


def _xor_records(measurement_records, measurement_keys: list[str], definitions) -> tuple[Any, list[dict[str, Any]]]:
    import torch

    key_to_index = {key: index for index, key in enumerate(measurement_keys)}
    defs: list[dict[str, Any]] = []
    cols = []
    for raw in definitions or ():
        if not isinstance(raw, dict):
            raise ValueError(f"record-layout definition must be a dict, got {type(raw)!r}")
        keys = [str(key) for key in raw.get("keys", ())]
        missing = [key for key in keys if key not in key_to_index]
        if missing:
            raise ValueError(
                f"record-layout definition {raw.get('name')!r} references unknown keys {missing}"
            )
        acc = torch.zeros(
            (measurement_records.shape[0],),
            dtype=measurement_records.dtype,
            device=measurement_records.device,
        )
        for key in keys:
            acc = (acc + measurement_records[:, key_to_index[key]]) % 2
        cols.append(acc)
        defs.append(dict(raw))
    if not cols:
        return (
            torch.zeros(
                (measurement_records.shape[0], 0),
                dtype=measurement_records.dtype,
                device=measurement_records.device,
            ),
            defs,
        )
    return torch.stack(cols, dim=1), defs


def _apply_readout_assignment_instrument(
    records,
    probabilities,
    measurement_keys: list[str],
    measurement_steps: list[dict[str, Any]],
    instrument_spec: Axis1ReadoutResetInstrumentSpec,
):
    if not instrument_spec.has_readout_assignment:
        return records, probabilities, []

    steps: list[dict[str, Any]] = []
    if instrument_spec.readout_p0_to_1 > 0.0 or instrument_spec.readout_p1_to_0 > 0.0:
        for col, key in enumerate(measurement_keys):
            records, probabilities = _branch_asymmetric_readout_flip(
                records,
                probabilities,
                col,
                p0_to_1=instrument_spec.readout_p0_to_1,
                p1_to_0=instrument_spec.readout_p1_to_0,
            )
            records, probabilities = _aggregate_record_distribution(records, probabilities)
            steps.append(
                {
                    "kind": "independent_asymmetric_assignment",
                    "measurement_key": str(key),
                    "column": int(col),
                    "p0_to_1": instrument_spec.readout_p0_to_1,
                    "p1_to_0": instrument_spec.readout_p1_to_0,
                    "epistemic_class": instrument_spec.epistemic_class,
                }
            )

    pair_probability = instrument_spec.readout_pair_flip_probability
    if pair_probability > 0.0:
        key_to_index = {key: index for index, key in enumerate(measurement_keys)}
        for step in measurement_steps:
            keys = [str(key) for key in step.get("measurement_keys", ())]
            for offset in range(0, len(keys) - 1, 2):
                left = keys[offset]
                right = keys[offset + 1]
                records, probabilities = _branch_pair_both_flip(
                    records,
                    probabilities,
                    key_to_index[left],
                    key_to_index[right],
                    probability=pair_probability,
                )
                records, probabilities = _aggregate_record_distribution(records, probabilities)
                steps.append(
                    {
                        "kind": "same_operation_pair_both_flip_assignment",
                        "measurement_keys": [left, right],
                        "columns": [int(key_to_index[left]), int(key_to_index[right])],
                        "probability": pair_probability,
                        "pairing_policy": "adjacent_keys_within_same_measurement_operation",
                        "epistemic_class": instrument_spec.epistemic_class,
                    }
                )

    return records, probabilities, steps


def _branch_asymmetric_readout_flip(
    records,
    probabilities,
    column: int,
    *,
    p0_to_1: float,
    p1_to_0: float,
):
    import torch

    col = int(column)
    bits = records[:, col]
    no_flip = torch.where(
        bits == 0,
        torch.as_tensor(1.0 - float(p0_to_1), dtype=probabilities.dtype, device=probabilities.device),
        torch.as_tensor(1.0 - float(p1_to_0), dtype=probabilities.dtype, device=probabilities.device),
    )
    flip = torch.where(
        bits == 0,
        torch.as_tensor(float(p0_to_1), dtype=probabilities.dtype, device=probabilities.device),
        torch.as_tensor(float(p1_to_0), dtype=probabilities.dtype, device=probabilities.device),
    )
    flipped_records = records.clone()
    flipped_records[:, col] = 1 - flipped_records[:, col]
    return (
        torch.cat([records, flipped_records], dim=0),
        torch.cat([probabilities * no_flip, probabilities * flip], dim=0),
    )


def _branch_pair_both_flip(records, probabilities, left_column: int, right_column: int, *, probability: float):
    import torch

    p = float(probability)
    flipped_records = records.clone()
    flipped_records[:, int(left_column)] = 1 - flipped_records[:, int(left_column)]
    flipped_records[:, int(right_column)] = 1 - flipped_records[:, int(right_column)]
    return (
        torch.cat([records, flipped_records], dim=0),
        torch.cat([probabilities * (1.0 - p), probabilities * p], dim=0),
    )


def _aggregate_record_distribution(records, probabilities):
    import torch

    unique_records, inverse = torch.unique(records, sorted=True, return_inverse=True, dim=0)
    aggregated = torch.zeros(
        (unique_records.shape[0],),
        dtype=probabilities.dtype,
        device=probabilities.device,
    )
    aggregated.scatter_add_(0, inverse, probabilities)
    keep = aggregated > 0.0
    return unique_records[keep], aggregated[keep]


def _weighted_marginals(records, probabilities) -> list[float]:
    if records.shape[1] == 0:
        return []
    return [float(value) for value in (probabilities[:, None] * records).sum(0).tolist()]


def _validate_record_evidence_schedule(schedule: SubstepSchedule, *, device: str) -> None:
    _require_cuda_device(device)
    _validate_schedule_for_axis1_channel_evidence(schedule)
    if int(schedule.num_qubits) > 8:
        raise ValueError(
            "Axis-1 measurement record evidence uses exact density matrices and is "
            f"currently capped at 8 qubits; got num_qubits={schedule.num_qubits}"
        )


def _assert_clean_axis1_record_evidence_dir(root: Path) -> None:
    stale = [
        path.name
        for path in sorted(root.iterdir())
        if path.is_file()
        and _axis1_forbidden_artifact_path(path)
    ]
    if stale:
        raise ValueError(
            "Axis-1 measurement record evidence writer refuses simulator-run artifact directories; "
            f"found stale artifact(s): {stale}"
        )


def _assert_clean_axis1_sample_dir(root: Path) -> None:
    sample_forbidden_names = (
        AXIS1_CHANNEL_FORBIDDEN_OUTPUT_NAMES
        | frozenset({"axis1_substep_channels.json", "axis1_state_evolution.json"})
    )
    stale = [
        path.name
        for path in sorted(root.iterdir())
        if path.is_file()
        and _axis1_forbidden_artifact_path(
            path,
            forbidden_suffixes=frozenset({".stim", ".dem", ".npz", ".npy"}),
            forbidden_names=sample_forbidden_names,
        )
    ]
    if stale:
        raise ValueError(
            "Axis-1 record sampler refuses mixed simulator/decoder artifact directories; "
            f"found stale artifact(s): {stale}"
        )


def _sample_file_entry(path: Path | None, present: bool) -> dict[str, Any] | None:
    if path is None:
        return None
    return {
        "file": path.name,
        "sha256": file_sha256(path),
        "present": bool(present),
    }


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


def _load_record_evidence_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    data = json.loads(path.read_text())
    if data.get("schema") != AXIS1_RECORD_EVIDENCE_SCHEMA:
        raise ValueError(
            f"{path} is not an Axis-1 record-evidence manifest: schema={data.get('schema')!r}"
        )
    return data


def _load_record_freeze_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    data = json.loads(path.read_text())
    if data.get("schema") != "qec_twin.simulator.axis1_measurement_record_freeze.v1":
        raise ValueError(
            f"{path} is not an Axis-1 record-evidence freeze: schema={data.get('schema')!r}"
        )
    required = {
        "evidence_file",
        "evidence_schema",
        "evidence_sha256",
        "evidence_content_hash",
        "source_kind",
        "source_hash",
        "verdict",
        "passed",
        "representability",
        "record_count",
        "measurement_key_count",
        "detector_count",
        "logical_observable_count",
        "applied_channel_count",
        "measurement_basis",
        "full_positive_duration_coverage",
        "primitive_registry_id",
    }
    missing = sorted(required.difference(data))
    if missing:
        raise ValueError(f"Axis-1 record freeze manifest missing fields: {missing}")
    if Path(str(data["evidence_file"])).name != str(data["evidence_file"]):
        raise ValueError("Axis-1 record freeze evidence_file must be a local filename")
    return data


def _validate_record_evidence_content_hash(manifest: dict[str, Any], path: Path) -> None:
    expected = _stable_payload_hash(manifest)
    if manifest.get("content_hash") != expected:
        raise ValueError(
            "Axis-1 record evidence content_hash mismatch for "
            f"{path}: stored={manifest.get('content_hash')} computed={expected}"
        )


def _default_freeze_path(evidence_path: Path) -> Path:
    return evidence_path.with_name(f"{evidence_path.stem}.freeze.json")


__all__ = [
    "AXIS1_RECORD_EVIDENCE_REPRESENTABILITY",
    "AXIS1_RECORD_EVIDENCE_SCHEMA",
    "Axis1MeasurementRecordEvidenceResult",
    "Axis1MeasurementRecordFreezeResult",
    "Axis1MeasurementRecordSampleResult",
    "Axis1ReadoutResetInstrumentSpec",
    "axis1_measurement_record_evidence_manifest",
    "freeze_axis1_measurement_record_evidence",
    "validate_axis1_measurement_record_freeze",
    "write_axis1_measurement_record_evidence",
    "write_axis1_measurement_record_samples",
]
