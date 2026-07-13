from __future__ import annotations

"""Axis-1 joint-channel evidence from compiler-produced substep schedules.

This module is the carrier-evidence bridge between schedule-derived mechanism
selections and `forward.joint_lindbladian.assemble_substep_channel`. It writes
metadata proving the joint channel was assembled from one generator exponential,
but it does not serialize Kraus, Choi, or superoperator payloads and does not
emit QEC records.
"""

from dataclasses import dataclass, replace
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from ..carrier.joint_lindbladian import (
    assemble_substep_channel,
    assemble_substep_channels_factored_batched,
)
from ..mechanisms.axis1_primitives import (
    Axis1PrimitiveBundle,
    Axis1PrimitiveParams,
    Axis1PrimitiveRecord,
    default_axis1_primitive_registry,
)
from .analog_schedule import (
    ANALOG_SCHEDULE_REPRESENTABILITY,
    COMPILER_SCHEDULE_SEAL_SCHEMA,
    SubstepSchedule,
    has_valid_compiler_schedule_seal,
    require_compiler_schedule_seal,
)
from .artifacts import file_sha256, write_json
from .axis1_bridge import (
    G2_GAMMA_1_PER_NS,
    G2_GAMMA_PHI_PER_NS,
    G2_ZETA_RAD_PER_NS,
)
from .axis1_context import (
    axis1_local_lindblad_context_from_schedule,
)
from .axis1_ideal_controls import lower_ideal_controls_for_selection
from .metadata_guard import (
    axis1_static_zz_calibrations_to_manifest,
    normalize_axis1_static_zz_calibrations,
)
from .axis1_selection import (
    Axis1MechanismSelection,
    Axis1SelectionLayer,
    axis1_selection_layers_in_schedule_order,
    axis1_selection_partition_manifest,
    build_axis1_schedule_selection_plan,
    flatten_axis1_selection_layers,
)


AXIS1_CHANNEL_EVIDENCE_SCHEMA = "qec_twin.simulator.axis1_substep_channel_evidence.v1"
AXIS1_CHANNEL_EVIDENCE_REPRESENTABILITY = "axis1_joint_channel_evidence_no_record_emission"
AXIS1_CHANNEL_ALLOWED_SOURCE_KINDS = frozenset(
    {"circuit_ir", "code_spec_compiler", "stim_circuit"}
)
AXIS1_CHANNEL_FORBIDDEN_OUTPUT_SUFFIXES = frozenset({".stim", ".dem", ".b8", ".npz", ".npy"})
AXIS1_CHANNEL_FORBIDDEN_OUTPUT_NAMES = frozenset(
    {
        "decoder_results.json",
        "leakage_by_site.json",
        "manifest.json",
        "measurement_counts.json",
        "qutrit_outcome_counts.json",
        "sample_summary_ideal.json",
        "sample_summary_noisy.json",
        "source_timeline_binding.json",
        "statevector.json",
        "theory_prediction.json",
    }
)


@dataclass(frozen=True)
class Axis1SubstepChannelRow:
    """One joint-channel carrier-evidence row for a schedule-derived selection."""

    row_id: str
    source_kind: str
    source_hash: str
    selection_id: str
    row_kind: str
    substep_id: str
    substep_kind: str
    operation_names: tuple[str, ...]
    source_step_indices: tuple[int, ...]
    operation_records: tuple[dict[str, Any], ...]
    ideal_controls: tuple[dict[str, Any], ...]
    lowered_mechanisms: tuple[dict[str, Any], ...]
    participant: tuple[int, ...]
    coupling_edges: tuple[tuple[int, int], ...]
    primitive_names: tuple[str, ...]
    mechanism_pair: tuple[str, str]
    context_mechanisms: tuple[str, ...]
    dt_ns: float
    dt_ns_nominal: float | None
    dt_ns_bracket: tuple[float, float]
    dt_source: str
    joint_channel: dict[str, Any]
    passed: bool
    failure_reason: str | None = None
    epistemic_class: str = "c"

    def to_manifest(self) -> dict[str, Any]:
        return {
            "row_id": self.row_id,
            "source_kind": self.source_kind,
            "source_hash": self.source_hash,
            "selection_id": self.selection_id,
            "row_kind": self.row_kind,
            "substep_id": self.substep_id,
            "substep": self.substep_id,
            "substep_kind": self.substep_kind,
            "operation_names": list(self.operation_names),
            "source_step_indices": list(self.source_step_indices),
            "source_operation_ids": [f"step:{i}" for i in self.source_step_indices],
            "operations": [dict(record) for record in self.operation_records],
            "ideal_controls": [dict(record) for record in self.ideal_controls],
            "lowered_mechanisms": [dict(record) for record in self.lowered_mechanisms],
            "participant": list(self.participant),
            "coupling_edges": [list(edge) for edge in self.coupling_edges],
            "primitive_names": list(self.primitive_names),
            "mechanism_pair": list(self.mechanism_pair),
            "pair_ij": " x ".join(self.mechanism_pair),
            "context_mechanisms": list(self.context_mechanisms),
            "dt_ns": self.dt_ns,
            "dt_ns_nominal": self.dt_ns_nominal,
            "dt_ns_bracket": list(self.dt_ns_bracket),
            "dt_source": self.dt_source,
            "joint_channel": dict(self.joint_channel),
            "expected_class": "joint_channel_carrier_evidence",
            "epistemic_class": self.epistemic_class,
            "epistemic_classes": {
                "single_joint_generator_semantics": "a",
                "ideal_control_unitary_representative": "a",
                "tp_residual_threshold": "c",
                "channel_payload_omission": "a",
            },
            "passed": self.passed,
            "failure_reason": self.failure_reason,
        }


@dataclass(frozen=True)
class Axis1SubstepChannelEvidenceResult:
    """Files and manifest returned by `write_axis1_substep_channel_evidence`."""

    out_dir: Path
    channel_evidence: Path
    manifest: dict[str, Any]
    content_hash: str


@dataclass(frozen=True)
class Axis1AssembledSelectionChannel:
    """One selection lowered to controls, primitive mechanisms, and a joint channel.

    The joint substep channel is carried in the EXACT coupling-component-factored form
    ``components`` (a list of ``(window_local_qubits, comp_kraus)`` in ascending-first-qubit
    order — see `assemble_substep_channel_factored`). The apply loop consumes ``components``
    directly (applying each block's Kraus to its own qubits, which is exact because disjoint-
    support Lindbladians commute). ``kraus`` remains available as the equivalent FULL-WINDOW
    channel for the diagnostic channel/state-evidence paths and `CoupledCycleNoiseProcess.channels`;
    it is assembled lazily (on first access) from the stored generators, so the hot record path
    never pays the full-window ``expm`` + Choi ``eigh`` it eliminated. When
    ``QEC_TWIN_NO_FACTORIZE=1`` (or a genuine single full-window component), ``components`` is a
    single ``(range(nq), full_window_kraus)`` entry and ``kraus`` returns that same tensor.
    """

    components: Any
    primitive_bundle: Any
    ideal_controls: Any
    _dt_ns: float
    _device: str

    @property
    def H_list(self) -> tuple[Any, ...]:
        return tuple(self.ideal_controls.H_list) + tuple(self.primitive_bundle.H_list)

    @property
    def c_list(self) -> tuple[Any, ...]:
        return tuple(self.primitive_bundle.c_list)

    @property
    def kraus(self) -> Any:
        """The equivalent FULL-WINDOW Kraus channel (diagnostic / non-hot-path consumers).

        If ``components`` is the single full-window entry (fallback or a genuinely
        full-window substep), returns that tensor with no rebuild. Otherwise assembles the
        full-window channel once via `assemble_substep_channel` on the stored generators —
        the SAME math the components factor exactly, just not factored. Callers on the record
        hot path must use ``components`` (never ``kraus``) so the factorization win is realized.
        """
        comps = self.components
        if len(comps) == 1:
            local_qubits, comp_kraus = comps[0]
            return comp_kraus
        return assemble_substep_channel(
            list(self.H_list), list(self.c_list), self._dt_ns, device=self._device,
        )


@dataclass(frozen=True)
class Axis1SubstepChannelFreezeResult:
    """Freeze manifest returned by `freeze_axis1_substep_channel_evidence`."""

    freeze_path: Path
    evidence_path: Path
    manifest: dict[str, Any]


def axis1_substep_channel_rows(
    schedule: SubstepSchedule,
    *,
    device: str = "cuda",
) -> tuple[Axis1SubstepChannelRow, ...]:
    """Assemble joint-channel carrier evidence for supported schedule selections."""

    _validate_schedule_for_axis1_channel_evidence(schedule)
    selection_plan = build_axis1_schedule_selection_plan(schedule)
    if not selection_plan.selections:
        raise ValueError("Axis-1 channel evidence requires at least one mechanism selection")
    selection_layers = axis1_selection_layers_in_schedule_order(
        schedule,
        selection_plan.selections,
        consumer_name="Axis-1 channel evidence",
    )
    return _channel_rows_from_selection_layers(schedule, selection_layers, device=device)


def axis1_substep_channel_evidence_manifest(
    schedule: SubstepSchedule,
    *,
    device: str = "cuda",
) -> dict[str, Any]:
    """Return serializable Axis-1 joint-channel carrier evidence."""

    _validate_schedule_for_axis1_channel_evidence(schedule)
    selection_plan = build_axis1_schedule_selection_plan(schedule)
    if not selection_plan.selections:
        raise ValueError("Axis-1 channel evidence requires at least one mechanism selection")
    selection_layers = axis1_selection_layers_in_schedule_order(
        schedule,
        selection_plan.selections,
        consumer_name="Axis-1 channel evidence",
    )
    rows = _channel_rows_from_selection_layers(schedule, selection_layers, device=device)
    coverage = _coverage_manifest(schedule, selection_plan)
    selected_rows_passed = all(row.passed for row in rows)
    passed = selected_rows_passed and bool(coverage["full_positive_duration_coverage"])
    axis1_context = axis1_local_lindblad_context_from_schedule(schedule)
    payload = {
        "schema": AXIS1_CHANNEL_EVIDENCE_SCHEMA,
        "verdict": "pass" if passed else "fail",
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "representability": AXIS1_CHANNEL_EVIDENCE_REPRESENTABILITY,
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
        "selection_partition": axis1_selection_partition_manifest(selection_layers),
        "coverage": coverage,
        "metric_reference": "docs/METRICS.md#forward-fidelity--coupling-metrics",
        "bridge_scope": (
            "joint channel carrier evidence only; no analog record emission, no Axis-2 source timeline, "
            "no leakage/qutrit integration"
        ),
        "channel_payload_policy": (
            "Kraus, Choi, and superoperator arrays are computed on GPU as carrier evidence but are not "
            "serialized into this artifact"
        ),
        "rows": [row.to_manifest() for row in rows],
        "selected_rows_passed": selected_rows_passed,
        "passed": passed,
    }
    if not axis1_context.is_trivial:
        payload["axis1_local_lindblad_context"] = axis1_context.to_manifest()
    static_zz_calibrations = _axis1_static_zz_calibrations_for_schedule(schedule)
    if static_zz_calibrations:
        payload["static_zz_calibrations"] = axis1_static_zz_calibrations_to_manifest(
            static_zz_calibrations
        )
    payload["content_hash"] = _stable_payload_hash(payload)
    return payload


def write_axis1_substep_channel_evidence(
    schedule: SubstepSchedule,
    out_dir: str | Path,
    *,
    device: str = "cuda",
    filename: str = "axis1_substep_channels.json",
) -> Axis1SubstepChannelEvidenceResult:
    """Write only the Axis-1 joint-channel evidence manifest."""

    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    _assert_clean_axis1_channel_evidence_dir(root)
    path = _axis1_safe_evidence_output_path(
        root,
        filename,
        writer_name="Axis-1 channel evidence writer",
    )
    manifest = axis1_substep_channel_evidence_manifest(schedule, device=device)
    write_json(path, manifest)
    return Axis1SubstepChannelEvidenceResult(
        out_dir=root,
        channel_evidence=path,
        manifest=manifest,
        content_hash=str(manifest["content_hash"]),
    )


def freeze_axis1_substep_channel_evidence(
    channel_evidence: str | Path,
    freeze_path: str | Path | None = None,
    *,
    overwrite: bool = False,
) -> Axis1SubstepChannelFreezeResult:
    """Write or validate a deterministic freeze guard for channel evidence."""

    evidence_path = Path(channel_evidence)
    manifest = _load_channel_evidence_manifest(evidence_path)
    _validate_channel_evidence_content_hash(manifest, evidence_path)
    sha = file_sha256(evidence_path)
    if sha is None:
        raise FileNotFoundError(evidence_path)
    out = Path(freeze_path) if freeze_path is not None else _default_freeze_path(evidence_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and not overwrite:
        existing = _load_channel_freeze_manifest(out)
        if existing["evidence_file"] != evidence_path.name:
            raise ValueError(
                "Axis-1 channel-evidence freeze evidence_file mismatch: "
                f"freeze={existing['evidence_file']!r} requested={evidence_path.name!r}"
            )
        validate_axis1_substep_channel_freeze(out)
        return Axis1SubstepChannelFreezeResult(
            freeze_path=out,
            evidence_path=evidence_path,
            manifest=existing,
        )
    payload = {
        "schema": "qec_twin.simulator.axis1_substep_channel_freeze.v1",
        "evidence_file": evidence_path.name,
        "evidence_schema": manifest.get("schema"),
        "evidence_sha256": sha,
        "evidence_content_hash": manifest.get("content_hash"),
        "source_kind": manifest.get("source_kind"),
        "source_hash": manifest.get("source_hash"),
        "verdict": manifest.get("verdict"),
        "passed": bool(manifest.get("passed")),
        "row_count": len(manifest.get("rows", [])),
        "representability": manifest.get("representability"),
        "primitive_registry_id": manifest.get("primitive_registry", {}).get("registry_id"),
        "scope": (
            "Axis-1 joint-channel carrier evidence freeze only; not analog record emission, "
            "not Axis-2 source projection"
        ),
    }
    write_json(out, payload)
    return Axis1SubstepChannelFreezeResult(
        freeze_path=out,
        evidence_path=evidence_path,
        manifest=payload,
    )


def validate_axis1_substep_channel_freeze(freeze_path: str | Path) -> dict[str, Any]:
    """Validate that frozen channel evidence did not drift."""

    path = Path(freeze_path)
    freeze = _load_channel_freeze_manifest(path)
    evidence_path = path.parent / str(freeze["evidence_file"])
    manifest = _load_channel_evidence_manifest(evidence_path)
    sha = file_sha256(evidence_path)
    if sha != freeze["evidence_sha256"]:
        raise ValueError(
            "Axis-1 channel evidence sha256 mismatch: "
            f"frozen={freeze['evidence_sha256']} current={sha}"
        )
    _validate_channel_evidence_content_hash(manifest, evidence_path)
    checks = {
        "evidence_schema": manifest.get("schema") == freeze["evidence_schema"],
        "evidence_content_hash": manifest.get("content_hash")
        == freeze["evidence_content_hash"],
        "source_kind": manifest.get("source_kind") == freeze["source_kind"],
        "source_hash": manifest.get("source_hash") == freeze["source_hash"],
        "verdict": manifest.get("verdict") == freeze["verdict"],
        "passed": bool(manifest.get("passed")) == bool(freeze["passed"]),
        "row_count": len(manifest.get("rows", [])) == int(freeze["row_count"]),
        "representability": manifest.get("representability") == freeze["representability"],
        "primitive_registry_id": manifest.get("primitive_registry", {}).get("registry_id")
        == freeze["primitive_registry_id"],
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise ValueError(f"Axis-1 channel freeze metadata mismatch: {failed}")
    return {
        "schema": "qec_twin.simulator.axis1_substep_channel_freeze_validation.v1",
        "freeze_file": path.name,
        "evidence_file": evidence_path.name,
        "evidence_sha256": sha,
        "evidence_content_hash": manifest.get("content_hash"),
        "checks": checks,
        "pass": True,
    }


def _channel_row_from_selection(
    schedule: SubstepSchedule,
    selection: Axis1MechanismSelection,
    *,
    device: str,
) -> Axis1SubstepChannelRow:
    dt = _nominal_positive_dt(selection)
    params = _axis1_primitive_params_for_schedule(schedule)
    static_zz_calibrations = _axis1_static_zz_calibrations_for_schedule(schedule)
    assembled = _assemble_selection_joint_channel(
        selection,
        dt_ns=dt,
        params=params,
        device=device,
        static_zz_calibrations=static_zz_calibrations,
    )
    channel_summary = _joint_channel_summary(
        assembled.kraus,
        device=device,
        ideal_controls=assembled.ideal_controls.records,
    )
    passed = channel_summary["tp_residual"] <= 1.0e-8
    failure = None
    if not passed:
        failure = (
            "joint channel trace-preservation residual too large: "
            f"{channel_summary['tp_residual']:.3e}"
        )
    return Axis1SubstepChannelRow(
        row_id=f"{selection.selection_id}:joint_channel:dt={dt:g}",
        source_kind=schedule.source_kind,
        source_hash=schedule.source_hash,
        selection_id=selection.selection_id,
        row_kind=selection.row_kind,
        substep_id=selection.substep_id,
        substep_kind=selection.substep_kind,
        operation_names=selection.operation_names,
        source_step_indices=selection.source_step_indices,
        operation_records=selection.operation_records,
        ideal_controls=tuple(record.to_manifest() for record in assembled.ideal_controls.records),
        lowered_mechanisms=tuple(
            record.to_manifest() for record in assembled.primitive_bundle.records
        ),
        participant=selection.participant,
        coupling_edges=selection.coupling_edges,
        primitive_names=selection.primitive_names,
        mechanism_pair=selection.mechanism_pair,
        context_mechanisms=selection.context_mechanisms,
        dt_ns=dt,
        dt_ns_nominal=selection.dt_ns_nominal,
        dt_ns_bracket=selection.dt_ns_bracket,
        dt_source=selection.dt_source,
        joint_channel=channel_summary,
        passed=passed,
        failure_reason=failure,
    )


def _channel_rows_from_selection_layers(
    schedule: SubstepSchedule,
    selection_layers: tuple[Axis1SelectionLayer, ...],
    *,
    device: str,
) -> tuple[Axis1SubstepChannelRow, ...]:
    return tuple(
        _channel_row_from_selection(schedule, selection, device=device)
        for selection in flatten_axis1_selection_layers(selection_layers)
    )


def _assemble_selection_joint_channel(
    selection: Axis1MechanismSelection,
    *,
    dt_ns: float,
    params: Axis1PrimitiveParams,
    device: str,
    static_zz_calibrations: dict[tuple[int, int], dict[str, Any]] | None = None,
) -> Axis1AssembledSelectionChannel:
    static_zz_calibrations = dict(static_zz_calibrations or {})
    if selection.row_kind in {
        "idle_cluster_joint_channel",
        "idle_zz_cluster_joint_channel",
        "multi_one_qubit_drive_cluster_joint_channel",
        "multi_one_qubit_drive_local_joint_channel",
        "multi_one_qubit_drive_zz_cluster_joint_channel",
        "one_qubit_drive_cluster_joint_channel",
        "one_qubit_drive_local_joint_channel",
        "one_qubit_drive_zz_cluster_joint_channel",
        "readout_cluster_joint_channel",
        "readout_zz_cluster_joint_channel",
        "two_qubit_control_cluster_joint_channel",
        "two_qubit_control_zz_cluster_joint_channel",
    }:
        primitive_bundle = _lower_one_qubit_drive_cluster_primitives(
            selection,
            dt_ns=dt_ns,
            params=params,
            device=device,
            static_zz_calibrations=static_zz_calibrations,
        )
    else:
        params = _params_with_single_edge_static_zz_calibration(
            params,
            selection,
            static_zz_calibrations,
        )
        primitive_bundle = default_axis1_primitive_registry().lower(
            selection.primitive_names,
            dt_ns=dt_ns,
            params=params,
            device=device,
        )
    ideal_controls = lower_ideal_controls_for_selection(
        selection,
        dt_ns=dt_ns,
        device=device,
    )
    H_list = tuple(ideal_controls.H_list) + tuple(primitive_bundle.H_list)
    c_list = tuple(primitive_bundle.c_list)
    # EXACT coupling-component factorization (SPEC 2026-07-04): the joint substep channel is
    # the tensor product over the connected components of the 2-qubit coupling graph, built at
    # small per-component dimension instead of one full-window expm + Choi eigh. Honors
    # QEC_TWIN_NO_FACTORIZE=1 (and the single-full-window case) as the exact current path.
    #
    # THIN BATCH LAYER (measured 2026-07-04): the per-component builds are launch-bound (many tiny
    # sequential matrix_exp/eigh on 4x4/16x16), 88% of the per-manifest cost. Grouping this selection's
    # components BY DIMENSION into one batched matrix_exp+eigh per D-group (`assemble_substep_channels_
    # factored_batched` on a single item) is EXACT (verified gauge-invariant equal to the per-item loop,
    # <=2.1e-15; outputs/twin_validation/factored_batch_options_probe.py) and byte-identical on records
    # (G-records). It is a 1-line swap with NO apply-loop restructure — the low-risk half of the batching
    # win (~11% of the channel-build cost); the whole-manifest cross-substep batch (~20%) was declined to
    # keep the correctness-critical apply loop untouched (coordinator: correct+simple > slightly faster).
    components = assemble_substep_channels_factored_batched(
        [(H_list, c_list, dt_ns)], device=device
    )[0]
    return Axis1AssembledSelectionChannel(
        components=components,
        primitive_bundle=primitive_bundle,
        ideal_controls=ideal_controls,
        _dt_ns=float(dt_ns),
        _device=str(device),
    )


def _axis1_primitive_params_for_schedule(schedule: SubstepSchedule) -> Axis1PrimitiveParams:
    defaults = Axis1PrimitiveParams(
        zeta_rad_per_ns=G2_ZETA_RAD_PER_NS,
        gamma_phi_per_ns=G2_GAMMA_PHI_PER_NS,
        gamma_1_per_ns=G2_GAMMA_1_PER_NS,
    )
    context = axis1_local_lindblad_context_from_schedule(schedule)
    return context.to_axis1_primitive_params(defaults)


def _axis1_static_zz_calibrations_for_schedule(
    schedule: SubstepSchedule,
) -> dict[tuple[int, int], dict[str, Any]]:
    return normalize_axis1_static_zz_calibrations(
        getattr(schedule, "static_zz_calibrations", {}),
        declared_edges=getattr(schedule, "static_zz_couplings", ()),
        label="SubstepSchedule.static_zz_calibrations",
    )


def _params_with_single_edge_static_zz_calibration(
    params: Axis1PrimitiveParams,
    selection: Axis1MechanismSelection,
    static_zz_calibrations: dict[tuple[int, int], dict[str, Any]],
) -> Axis1PrimitiveParams:
    if "ZZ" not in selection.primitive_names or len(selection.coupling_edges) != 1:
        return params
    edge = _normal_edge(selection.coupling_edges[0])
    payload = static_zz_calibrations.get(edge)
    if payload is None:
        return params
    return replace(params, zeta_rad_per_ns=float(payload["zeta_rad_per_ns"]))


def _lower_one_qubit_drive_cluster_primitives(
    selection: Axis1MechanismSelection,
    *,
    dt_ns: float,
    params: Axis1PrimitiveParams,
    device: str,
    static_zz_calibrations: dict[tuple[int, int], dict[str, Any]] | None = None,
) -> Axis1PrimitiveBundle:
    import math
    import torch

    support_size = len(selection.participant)
    if support_size < 1:
        raise ValueError(
            "frontend-control cluster/local joint channel requires at least one "
            f"qubit; got participant={selection.participant!r}"
        )
    dev = str(device)
    if not dev.startswith("cuda"):
        raise ValueError("Axis-1 cluster primitive lowering is GPU-only")
    cdt = torch.complex128
    n_op = torch.tensor([[0.0, 0.0], [0.0, 1.0]], dtype=cdt, device=dev)
    sm_op = torch.tensor([[0.0, 1.0], [0.0, 0.0]], dtype=cdt, device=dev)
    sp_op = torch.tensor([[0.0, 0.0], [1.0, 0.0]], dtype=cdt, device=dev)
    swap_01_10 = torch.zeros((4, 4), dtype=cdt, device=dev)
    swap_01_10[1, 2] = 1.0
    swap_01_10[2, 1] = 1.0
    H_list: list[Any] = []
    c_ops: list[Any] = []
    records: list[Axis1PrimitiveRecord] = []
    primitive_names = set(selection.primitive_names)
    participant_index = {int(q): index for index, q in enumerate(selection.participant)}
    static_zz_calibrations = dict(static_zz_calibrations or {})
    if (
        selection.row_kind
        in {
            "idle_zz_cluster_joint_channel",
            "multi_one_qubit_drive_zz_cluster_joint_channel",
            "one_qubit_drive_zz_cluster_joint_channel",
            "readout_zz_cluster_joint_channel",
            "two_qubit_control_zz_cluster_joint_channel",
        }
        and not selection.coupling_edges
    ):
        raise ValueError(
            f"{selection.row_kind} requires at least one coupling edge"
        )
    for edge in selection.coupling_edges:
        edge_qubits = tuple(int(q) for q in edge)
        zeta = _static_zz_zeta_for_edge(
            params,
            edge_qubits,
            static_zz_calibrations,
        )
        left, right = sorted(
            (
                participant_index[edge_qubits[0]],
                participant_index[edge_qubits[1]],
            )
        )
        H_list.append(
            zeta
            * _embed_two_qubit_local_operator(
                n_op,
                n_op,
                left_index=left,
                right_index=right,
                num_qubits=support_size,
                device=dev,
            )
        )
        records.append(
            Axis1PrimitiveRecord(
                "ZZ",
                "hamiltonian",
                zeta,
                support=(left, right),
            )
        )
    if selection.substep_kind == "two_qubit_gate":
        for pair in _active_two_qubit_pairs(selection):
            if pair[0] not in participant_index or pair[1] not in participant_index:
                continue
            left = participant_index[pair[0]]
            right = participant_index[pair[1]]
            if "FSIM_SWAP" in primitive_names:
                coeff = params.fsim_delta_theta_rad / float(dt_ns)
                H_list.append(
                    coeff
                    * _embed_two_qubit_operator_matrix(
                        swap_01_10,
                        left_index=left,
                        right_index=right,
                        num_qubits=support_size,
                        device=dev,
                    )
                )
                records.append(
                    Axis1PrimitiveRecord(
                        "FSIM_SWAP",
                        "hamiltonian",
                        coeff,
                        support=(left, right),
                    )
                )
            if "FSIM_PHASE" in primitive_names:
                coeff = params.fsim_delta_phi_rad / float(dt_ns)
                H_list.append(
                    coeff
                    * _embed_two_qubit_local_operator(
                        n_op,
                        n_op,
                        left_index=left,
                        right_index=right,
                        num_qubits=support_size,
                        device=dev,
                    )
                )
                records.append(
                    Axis1PrimitiveRecord(
                        "FSIM_PHASE",
                        "hamiltonian",
                        coeff,
                        support=(left, right),
                    )
                )
    gamma_phi_coeff = math.sqrt(2.0 * params.gamma_phi_per_ns)
    gamma_readout_phi_coeff = math.sqrt(2.0 * params.gamma_readout_phi_per_ns)
    gamma_1_coeff = math.sqrt(params.gamma_1_per_ns)
    gamma_up_coeff = math.sqrt(params.gamma_up_per_ns)
    active_targets = set(_active_one_qubit_targets(selection)) if selection.substep_kind != "idle" else set()
    for local_index in range(support_size):
        global_qubit = int(selection.participant[local_index])
        is_active = global_qubit in active_targets
        if selection.substep_kind == "idle":
            dephasing_name = "T2"
            relaxation_name = "T1"
            excitation_name = "T1_UP"
        elif selection.substep_kind == "measurement":
            if is_active:
                c_ops.append(
                    gamma_readout_phi_coeff
                    * _embed_one_qubit_local_operator(
                        n_op,
                        target_index=local_index,
                        num_qubits=support_size,
                        device=dev,
                    )
                )
                records.append(
                    Axis1PrimitiveRecord(
                        "RD",
                        "collapse",
                        gamma_readout_phi_coeff,
                        support=(local_index,),
                    )
                )
            dephasing_name = "T2" if is_active else "T2_B"
            relaxation_name = "T1" if is_active else "T1_B"
            excitation_name = "T1_UP" if is_active else "T1_UP_B"
        else:
            dephasing_name = "T2" if is_active else "T2_B"
            relaxation_name = "T1" if is_active else "T1_B"
            excitation_name = "T1_UP" if is_active else "T1_UP_B"
        c_ops.append(
            gamma_phi_coeff
            * _embed_one_qubit_local_operator(
                n_op,
                target_index=local_index,
                num_qubits=support_size,
                device=dev,
            )
        )
        records.append(
            Axis1PrimitiveRecord(
                dephasing_name,
                "collapse",
                gamma_phi_coeff,
                support=(local_index,),
            )
        )
        c_ops.append(
            gamma_1_coeff
            * _embed_one_qubit_local_operator(
                sm_op,
                target_index=local_index,
                num_qubits=support_size,
                device=dev,
            )
        )
        records.append(
            Axis1PrimitiveRecord(
                relaxation_name,
                "collapse",
                gamma_1_coeff,
                support=(local_index,),
            )
        )
        if excitation_name in primitive_names:
            c_ops.append(
                gamma_up_coeff
                * _embed_one_qubit_local_operator(
                    sp_op,
                    target_index=local_index,
                    num_qubits=support_size,
                    device=dev,
                )
            )
            records.append(
                Axis1PrimitiveRecord(
                    excitation_name,
                    "collapse",
                    gamma_up_coeff,
                    support=(local_index,),
                )
            )
    return Axis1PrimitiveBundle(
        primitive_names=selection.primitive_names,
        H_list=tuple(torch.as_tensor(op, device=dev) for op in H_list),
        c_list=tuple(torch.as_tensor(op, device=dev) for op in c_ops),
        records=tuple(records),
        params=params,
        dt_ns=float(dt_ns),
    )


def _active_one_qubit_targets(selection: Axis1MechanismSelection) -> tuple[int, ...]:
    targets: set[int] = set()
    participant_set = set(int(q) for q in selection.participant)
    for op in selection.operation_records:
        for target in op.get("targets", ()):
            q = int(target)
            if q in participant_set:
                targets.add(q)
    ordered = tuple(int(q) for q in selection.participant if int(q) in targets)
    if not ordered:
        raise ValueError(f"selection {selection.selection_id!r} has no active frontend targets")
    return ordered


def _active_two_qubit_pairs(selection: Axis1MechanismSelection) -> tuple[tuple[int, int], ...]:
    pairs: list[tuple[int, int]] = []
    participant_set = set(int(q) for q in selection.participant)
    for op in selection.operation_records:
        targets = tuple(int(q) for q in op.get("targets", ()))
        if len(targets) % 2:
            raise ValueError(f"two-qubit operation record has odd target count: {op!r}")
        for i in range(0, len(targets), 2):
            pair = (int(targets[i]), int(targets[i + 1]))
            if pair[0] in participant_set and pair[1] in participant_set:
                pairs.append(pair)
    return tuple(pairs)


def _static_zz_zeta_for_edge(
    params: Axis1PrimitiveParams,
    edge: tuple[int, int],
    static_zz_calibrations: dict[tuple[int, int], dict[str, Any]],
) -> float:
    payload = static_zz_calibrations.get(_normal_edge(edge))
    if payload is None:
        return float(params.zeta_rad_per_ns)
    return float(payload["zeta_rad_per_ns"])


def _normal_edge(edge: tuple[int, int]) -> tuple[int, int]:
    a, b = int(edge[0]), int(edge[1])
    return (a, b) if a < b else (b, a)


def _embed_one_qubit_local_operator(op, *, target_index: int, num_qubits: int, device: str):
    import torch

    n = int(num_qubits)
    target = int(target_index)
    if n < 1:
        raise ValueError("num_qubits must be positive for local operator embedding")
    if target < 0 or target >= n:
        raise ValueError(f"target_index {target} outside local support of size {n}")
    eye = torch.eye(2, dtype=torch.complex128, device=device)
    local = torch.as_tensor(op, dtype=torch.complex128, device=device)
    factors = [local if index == target else eye for index in range(n)]
    out = factors[0].contiguous()
    for factor in factors[1:]:
        out = torch.kron(out.contiguous(), factor.contiguous())
    return out


def _embed_two_qubit_operator_matrix(
    op,
    *,
    left_index: int,
    right_index: int,
    num_qubits: int,
    device: str,
):
    import torch

    n = int(num_qubits)
    left = int(left_index)
    right = int(right_index)
    if n < 2:
        raise ValueError("num_qubits must be at least two for two-qubit operator embedding")
    if left == right:
        raise ValueError("two-qubit operator embedding requires distinct local indices")
    if left < 0 or left >= n or right < 0 or right >= n:
        raise ValueError(
            f"local indices {(left, right)} outside local support of size {n}"
        )
    local = torch.as_tensor(op, dtype=torch.complex128, device=device)
    if local.shape != (4, 4):
        raise ValueError(f"two-qubit operator matrix must have shape (4, 4), got {tuple(local.shape)}")
    dim = 2**n
    out = torch.zeros((dim, dim), dtype=torch.complex128, device=device)
    other_indices = tuple(index for index in range(n) if index not in {left, right})
    for row in range(dim):
        row_bits = _basis_bits(row, n)
        row_pair = 2 * row_bits[left] + row_bits[right]
        for col in range(dim):
            col_bits = _basis_bits(col, n)
            if any(row_bits[index] != col_bits[index] for index in other_indices):
                continue
            col_pair = 2 * col_bits[left] + col_bits[right]
            out[row, col] = local[row_pair, col_pair]
    return out


def _basis_bits(index: int, num_bits: int) -> tuple[int, ...]:
    n = int(num_bits)
    return tuple((int(index) >> (n - 1 - bit)) & 1 for bit in range(n))


def _embed_two_qubit_local_operator(
    left_op,
    right_op,
    *,
    left_index: int,
    right_index: int,
    num_qubits: int,
    device: str,
):
    import torch

    n = int(num_qubits)
    left = int(left_index)
    right = int(right_index)
    if n < 2:
        raise ValueError("num_qubits must be at least two for two-qubit operator embedding")
    if left == right:
        raise ValueError("two-qubit operator embedding requires distinct local indices")
    if left < 0 or left >= n or right < 0 or right >= n:
        raise ValueError(
            f"local indices {(left, right)} outside local support of size {n}"
        )
    eye = torch.eye(2, dtype=torch.complex128, device=device)
    local_left = torch.as_tensor(left_op, dtype=torch.complex128, device=device)
    local_right = torch.as_tensor(right_op, dtype=torch.complex128, device=device)
    factors = []
    for index in range(n):
        if index == left:
            factors.append(local_left)
        elif index == right:
            factors.append(local_right)
        else:
            factors.append(eye)
    out = factors[0].contiguous()
    for factor in factors[1:]:
        out = torch.kron(out.contiguous(), factor.contiguous())
    return out


def _joint_channel_summary(
    kraus,
    *,
    device: str,
    ideal_controls: tuple[Any, ...] = (),
) -> dict[str, Any]:
    import torch

    dev = str(device)
    kraus = torch.as_tensor(kraus, dtype=torch.complex128, device=dev)
    if kraus.ndim != 3 or kraus.shape[-1] != kraus.shape[-2]:
        raise ValueError(f"expected Kraus stack (k,D,D), got {tuple(kraus.shape)}")
    dim = int(kraus.shape[-1])
    eye = torch.eye(dim, dtype=torch.complex128, device=dev)
    skk = torch.zeros((dim, dim), dtype=torch.complex128, device=dev)
    for k in range(kraus.shape[0]):
        K = kraus[k]
        skk = skk + K.conj().transpose(-1, -2) @ K
    tp_residual = float(torch.max(torch.abs(skk - eye)).item())
    return {
        "assembled_by": "qec_twin.forward.joint_lindbladian.assemble_substep_channel",
        "assembly_semantics": "single_joint_generator_expm",
        "generator_form": "L_substep = -i[sum_i H_i, .] + sum_k D[c_k]",
        "contains_ideal_control_hamiltonian": bool(ideal_controls),
        "ideal_control_names": [str(record.name) for record in ideal_controls],
        "contains_serialized_channel_payload": False,
        "dimension": dim,
        "num_kraus": int(kraus.shape[0]),
        "tp_residual": tp_residual,
        "tp_residual_threshold": 1.0e-8,
        "device": dev,
        "dtype": str(kraus.dtype).replace("torch.", ""),
    }


def _validate_schedule_for_axis1_channel_evidence(
    schedule: SubstepSchedule,
    *,
    allow_multilevel_leakage_context: bool = False,
) -> None:
    if schedule.representability != ANALOG_SCHEDULE_REPRESENTABILITY:
        raise ValueError(
            "Axis-1 channel evidence requires "
            f"{ANALOG_SCHEDULE_REPRESENTABILITY!r}, got {schedule.representability!r}"
        )
    if not schedule.source_hash:
        raise ValueError("Axis-1 channel evidence requires a non-empty source_hash")
    if schedule.source_kind == "oracle_unit":
        raise ValueError("oracle_unit schedules are not accepted by Axis-1 channel evidence")
    if schedule.source_kind not in AXIS1_CHANNEL_ALLOWED_SOURCE_KINDS:
        allowed = ", ".join(sorted(AXIS1_CHANNEL_ALLOWED_SOURCE_KINDS))
        raise ValueError(
            "Axis-1 channel evidence only accepts implemented schedule source kinds "
            f"({allowed}); got {schedule.source_kind!r}"
        )
    bad = [sub.substep_id for sub in schedule.substeps if not sub.generated_by_compiler]
    if bad:
        raise ValueError(f"Axis-1 channel evidence requires compiler-generated substeps: {bad}")
    context = axis1_local_lindblad_context_from_schedule(schedule)
    if context.include_leakage and not bool(allow_multilevel_leakage_context):
        raise ValueError(
            "Axis-1 dense computational-subspace evidence cannot silently ignore "
            "public qutrit leakage context; route this schedule through "
            "execution_backend_contract='mcwf_mps_state_record' with declared "
            "local_dims >= 3, or add a registered dense qutrit oracle first"
        )
    require_compiler_schedule_seal(schedule)


def _coverage_manifest(schedule: SubstepSchedule, selection_plan) -> dict[str, Any]:
    selected = tuple(selection.substep_id for selection in selection_plan.selections)
    selected_set = set(selected)
    selected_schedule_order = [
        substep.substep_id
        for substep in schedule.substeps
        if substep.substep_id in selected_set
    ]
    selected_participants_by_substep: dict[str, set[tuple[int, ...]]] = {}
    for selection in selection_plan.selections:
        selected_participants_by_substep.setdefault(selection.substep_id, set()).add(
            tuple(int(q) for q in selection.participant)
        )
    omitted = [
        _omitted_substep_record(substep)
        for substep in schedule.substeps
        if substep.substep_id not in selected_set
    ]
    positive_substeps = [
        substep for substep in schedule.substeps if substep.dt_ns_nominal is not None
    ]
    positive_duration = [substep.substep_id for substep in positive_substeps]
    participant_records = [
        _participant_coverage_record(substep, selected_participants_by_substep)
        for substep in positive_substeps
    ]
    selected_positive = [substep_id for substep_id in positive_duration if substep_id in selected_set]
    fully_covered_positive = [
        record["substep_id"]
        for record in participant_records
        if bool(record["full_participant_coverage"])
    ]
    partial_positive = [
        record
        for record in participant_records
        if record["selected_participants"] and not bool(record["full_participant_coverage"])
    ]
    coverage_fraction = (
        1.0
        if not positive_duration
        else float(len(fully_covered_positive)) / float(len(positive_duration))
    )
    expected_window_count = sum(
        len(record["expected_participants"])
        + len(record["unpaired_qubits"])
        + len(record.get("covered_unpaired_qubits", ()))
        for record in participant_records
    )
    covered_window_count = sum(
        len(record["covered_participants"])
        + len(record.get("covered_unpaired_qubits", ()))
        for record in participant_records
    )
    window_coverage_fraction = (
        1.0
        if expected_window_count == 0
        else float(covered_window_count) / float(expected_window_count)
    )
    return {
        "total_substeps": len(schedule.substeps),
        "positive_duration_substeps": positive_duration,
        "selected_substep_ids": selected_schedule_order,
        "selected_positive_duration_substep_ids": selected_positive,
        "fully_covered_positive_duration_substep_ids": fully_covered_positive,
        "full_positive_duration_coverage": len(fully_covered_positive) == len(positive_duration),
        "positive_duration_coverage_fraction": coverage_fraction,
        "positive_duration_window_coverage_fraction": window_coverage_fraction,
        "selected_row_count": len(selection_plan.selections),
        "participant_coverage": participant_records,
        "partial_positive_duration_substeps": partial_positive,
        "omitted_substeps": omitted,
        "coverage_scope": (
            "supported local Axis-1 joint-channel evidence only; coverage is counted by "
            "expected public participant windows, not merely by substep id"
        ),
    }


def _participant_coverage_record(
    substep,
    selected_participants_by_substep: dict[str, set[tuple[int, ...]]],
) -> dict[str, Any]:
    expected, unpaired, basis = _expected_axis1_participants(substep)
    selected = tuple(sorted(selected_participants_by_substep.get(substep.substep_id, set())))
    expected_set = set(expected)
    selected_set = set(selected)
    covered = tuple(sorted(pair for pair in expected if _participant_window_is_covered(pair, selected)))
    covered_unpaired = tuple(
        int(q)
        for q in unpaired
        if any(int(q) in set(int(x) for x in participant) for participant in selected)
    )
    covered_set = set(covered)
    missing = tuple(sorted(expected_set.difference(covered_set)))
    missing_unpaired = tuple(int(q) for q in unpaired if int(q) not in set(covered_unpaired))
    extra = tuple(
        sorted(
            participant
            for participant in selected_set
            if not _selected_participant_covers_any_expected(participant, expected)
            and not any(int(q) in set(int(x) for x in participant) for q in unpaired)
        )
    )
    denominator = len(expected) + len(unpaired)
    fraction = (
        0.0
        if denominator == 0
        else float(len(covered) + len(covered_unpaired)) / float(denominator)
    )
    full = denominator > 0 and not missing and not extra and not missing_unpaired
    return {
        "substep_id": substep.substep_id,
        "kind": substep.kind,
        "coverage_basis": basis,
        "dt_ns_nominal": substep.dt_ns_nominal,
        "expected_participants": [list(pair) for pair in expected],
        "selected_participants": [list(pair) for pair in selected],
        "covered_participants": [list(pair) for pair in covered],
        "missing_participants": [list(pair) for pair in missing],
        "extra_selected_participants": [list(pair) for pair in extra],
        "unpaired_qubits": list(missing_unpaired),
        "covered_unpaired_qubits": list(covered_unpaired),
        "full_participant_coverage": full,
        "participant_coverage_fraction": fraction,
    }


def _participant_window_is_covered(
    expected_pair: tuple[int, int],
    selected_participants: tuple[tuple[int, ...], ...],
) -> bool:
    expected = set(int(q) for q in expected_pair)
    return any(expected.issubset(set(int(q) for q in participant)) for participant in selected_participants)


def _selected_participant_covers_any_expected(
    participant: tuple[int, ...],
    expected_pairs: tuple[tuple[int, int], ...],
) -> bool:
    selected = set(int(q) for q in participant)
    return any(set(int(q) for q in pair).issubset(selected) for pair in expected_pairs)


def _expected_axis1_participants(substep) -> tuple[tuple[tuple[int, int], ...], tuple[int, ...], str]:
    if substep.kind == "one_qubit_gate":
        if not substep.idle_qubits:
            return (
                (),
                tuple(int(q) for q in substep.active_qubits),
                "active_only_one_qubit_controls_visible_in_schedule",
            )
        expected = tuple(
            (int(active), int(idle))
            for active in substep.active_qubits
            for idle in substep.idle_qubits
            if int(active) != int(idle)
        )
        return expected, (), "all_active_idle_pairs_visible_in_schedule"
    if substep.kind == "two_qubit_gate":
        expected = tuple(
            tuple(int(q) for q in pair)
            for pair in substep.participants
            if len(pair) == 2
        )
        return (
            expected,
            tuple(int(q) for q in substep.idle_qubits),
            "scheduled_two_qubit_gate_participants_plus_idle_qubits",
        )
    if substep.kind == "idle":
        pairs, unpaired = _consecutive_pair_partition(tuple(int(q) for q in substep.idle_qubits))
        return pairs, unpaired, "explicit_idle_consecutive_pair_partition"
    if substep.kind == "measurement":
        pairs, unpaired = _consecutive_pair_partition(tuple(int(q) for q in substep.active_qubits))
        return pairs, unpaired, "explicit_readout_consecutive_pair_partition"
    return (), (), "unsupported_positive_substep_kind"


def _consecutive_pair_partition(qubits: tuple[int, ...]) -> tuple[tuple[tuple[int, int], ...], tuple[int, ...]]:
    pairs = tuple((qubits[i], qubits[i + 1]) for i in range(0, len(qubits) - 1, 2))
    unpaired = () if len(qubits) % 2 == 0 else (qubits[-1],)
    return pairs, unpaired


def _omitted_substep_record(substep) -> dict[str, Any]:
    if substep.dt_ns_nominal is None:
        reason = "structural_or_no_nominal_dt"
    elif substep.kind == "one_qubit_gate":
        reason = "unsupported_one_qubit_gate_or_no_idle_window"
    elif substep.kind == "idle":
        reason = "unsupported_idle_duration_or_unpaired_idle_window"
    elif substep.kind == "measurement":
        reason = "unsupported_readout_duration_or_unpaired_readout_window"
    elif substep.kind == "two_qubit_gate":
        reason = "unsupported_two_qubit_gate"
    else:
        reason = "unsupported_substep_kind"
    return {
        "substep_id": substep.substep_id,
        "kind": substep.kind,
        "reason": reason,
        "dt_ns_nominal": substep.dt_ns_nominal,
        "dt_ns_bracket": list(substep.dt_ns_bracket),
    }


def _nominal_positive_dt(selection: Axis1MechanismSelection) -> float:
    if selection.dt_ns_nominal is None:
        raise ValueError(
            f"selection {selection.selection_id!r} has no nominal dt for channel evidence"
        )
    dt = float(selection.dt_ns_nominal)
    if not math.isfinite(dt) or dt <= 0.0:
        raise ValueError(f"selection {selection.selection_id!r} has invalid dt {dt!r}")
    return dt


def _assert_clean_axis1_channel_evidence_dir(root: Path) -> None:
    stale = [
        path.name
        for path in sorted(root.iterdir())
        if path.is_file()
        and _axis1_forbidden_artifact_path(path)
    ]
    if stale:
        raise ValueError(
            "Axis-1 channel evidence writer refuses simulator-run artifact directories; "
            f"found stale artifact(s): {stale}"
        )


def _axis1_safe_evidence_output_path(
    root: Path,
    filename: str,
    *,
    writer_name: str,
    forbidden_suffixes: frozenset[str] = AXIS1_CHANNEL_FORBIDDEN_OUTPUT_SUFFIXES,
    forbidden_names: frozenset[str] = AXIS1_CHANNEL_FORBIDDEN_OUTPUT_NAMES,
) -> Path:
    raw = str(filename)
    candidate = Path(raw)
    if not raw or candidate.is_absolute() or candidate.name != raw:
        raise ValueError(f"{writer_name} refuses non-local evidence filename: {raw!r}")
    if _axis1_forbidden_artifact_path(
        candidate,
        forbidden_suffixes=forbidden_suffixes,
        forbidden_names=forbidden_names,
    ):
        raise ValueError(f"{writer_name} refuses forbidden evidence filename: {raw!r}")
    return root / candidate.name


def _axis1_forbidden_artifact_path(
    path: Path,
    *,
    forbidden_suffixes: frozenset[str] = AXIS1_CHANNEL_FORBIDDEN_OUTPUT_SUFFIXES,
    forbidden_names: frozenset[str] = AXIS1_CHANNEL_FORBIDDEN_OUTPUT_NAMES,
) -> bool:
    suffixes = {str(s).lower() for s in forbidden_suffixes}
    names = {str(name).lower() for name in forbidden_names}
    return path.suffix.lower() in suffixes or path.name.lower() in names


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


def _load_channel_evidence_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    data = json.loads(path.read_text())
    if data.get("schema") != AXIS1_CHANNEL_EVIDENCE_SCHEMA:
        raise ValueError(
            f"{path} is not an Axis-1 channel-evidence manifest: schema={data.get('schema')!r}"
        )
    return data


def _load_channel_freeze_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    data = json.loads(path.read_text())
    if data.get("schema") != "qec_twin.simulator.axis1_substep_channel_freeze.v1":
        raise ValueError(
            f"{path} is not an Axis-1 channel-evidence freeze: schema={data.get('schema')!r}"
        )
    evidence_file = Path(str(data.get("evidence_file", "")))
    if evidence_file.name != str(data.get("evidence_file", "")) or evidence_file.is_absolute():
        raise ValueError("Axis-1 channel freeze evidence_file must be a local filename")
    return data


def _validate_channel_evidence_content_hash(manifest: dict[str, Any], path: Path) -> None:
    expected = _stable_payload_hash(manifest)
    if manifest.get("content_hash") != expected:
        raise ValueError(
            "Axis-1 channel evidence content_hash mismatch for "
            f"{path}: stored={manifest.get('content_hash')} computed={expected}"
        )


def _default_freeze_path(evidence_path: Path) -> Path:
    return evidence_path.with_name(f"{evidence_path.stem}.freeze.json")


__all__ = [
    "AXIS1_CHANNEL_EVIDENCE_REPRESENTABILITY",
    "AXIS1_CHANNEL_EVIDENCE_SCHEMA",
    "Axis1SubstepChannelEvidenceResult",
    "Axis1SubstepChannelFreezeResult",
    "Axis1SubstepChannelRow",
    "axis1_substep_channel_evidence_manifest",
    "axis1_substep_channel_rows",
    "freeze_axis1_substep_channel_evidence",
    "validate_axis1_substep_channel_freeze",
    "write_axis1_substep_channel_evidence",
]
