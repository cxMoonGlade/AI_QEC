from __future__ import annotations

"""Joint-channel comparison evidence from a compiler-produced schedule.

This module compares composed and joint same-substep channels from compiler-produced
`SubstepSchedule` metadata. It is intentionally
narrow: only the declared `ZZ x T2` exact-zero row and `DR x ZZ` nonzero
row are supported. It does not emit QEC records, does not consume Axis-2 source
timelines, and does not define a general mechanism library.
"""

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from ..carrier.joint_lindbladian import (
    SUPEROP_EXACTZERO_TOL,
    _choi_state_from_kraus,
    _composed_superop,
    _state_fidelity,
    _superop_expm,
    composed_substep_channel,
    composed_vs_joint_choi_distance,
    composed_vs_joint_infidelity,
    composed_vs_joint_infidelity_leading,
    composed_vs_joint_superop_distance,
    liouvillian_commutator_norm,
    superop_to_kraus,
)
from ..mechanisms.axis1_primitives import (
    Axis1PrimitiveParams,
    default_axis1_primitive_registry,
)
from ..numerics import NUMERICAL_ZERO
from .analog_schedule import (
    ANALOG_SCHEDULE_REPRESENTABILITY,
    COMPILER_SCHEDULE_SEAL_SCHEMA,
    SubstepSchedule,
    has_valid_compiler_schedule_seal,
    require_compiler_schedule_seal,
)
from .artifacts import file_sha256, write_json
from .axis1_selection import (
    Axis1MechanismSelection,
    build_axis1_joint_channel_selection_plan,
)

JOINT_CHANNEL_ZETA_RAD_PER_NS = 2.0 * math.pi * 0.37e-3
JOINT_CHANNEL_GAMMA_PHI_PER_NS = 1.0 / 30000.0
JOINT_CHANNEL_GAMMA_1_PER_NS = 1.0 / 30000.0
JOINT_CHANNEL_DR_ZZ_BAND = (6.0e-4, 3.0e-3)
JOINT_CHANNEL_FIXED_OMEGA_BAND = (4.0e-4, 4.0e-3)
JOINT_CHANNEL_NONZERO_COMMUTATOR_MIN = 1.0e-6
JOINT_CHANNEL_NONZERO_SUPEROP_DISTANCE_MIN = 1.0e-3
JOINT_CHANNEL_DT_GRID = (20.0, 22.5, 25.0, 27.5, 30.0)
JOINT_CHANNEL_DT_SMALL = (4.0, 6.0, 8.0, 10.0)
JOINT_CHANNEL_DT_CONTROL = (20.0, 25.0, 30.0)
JOINT_CHANNEL_FIXED_OMEGA_RAD_PER_NS = math.pi / 25.0
JOINT_CHANNEL_SLOPE_TOL = 0.35
JOINT_CHANNEL_ALLOWED_SOURCE_KINDS = frozenset(
    {"circuit_ir", "code_spec_compiler", "stim_circuit"}
)
JOINT_CHANNEL_FORBIDDEN_OUTPUT_SUFFIXES = frozenset(
    {".stim", ".dem", ".b8", ".npz", ".npy"}
)
JOINT_CHANNEL_FORBIDDEN_OUTPUT_NAMES = frozenset(
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
class JointChannelComparisonRow:
    """One joint-channel comparison row tied to a compiler-generated substep."""

    row_id: str
    source_kind: str
    source_hash: str
    substep_id: str
    substep_kind: str
    operation_names: tuple[str, ...]
    source_step_indices: tuple[int, ...]
    operation_records: tuple[dict[str, Any], ...]
    lowered_mechanisms: tuple[dict[str, Any], ...]
    participant: tuple[int, ...]
    mechanism_pair: tuple[str, str]
    context_mechanisms: tuple[str, ...]
    dt_ns: float
    dt_ns_nominal: float | None
    dt_ns_bracket: tuple[float, float]
    dt_source: str
    sweep_mode: str
    liouvillian_commutator_norm: float
    superop_distance: float
    one_minus_F_e: float
    leading_one_minus_F_e: float | None
    expected_class: str
    epistemic_class: str
    passed: bool
    failure_reason: str | None = None

    def to_manifest(self) -> dict:
        exact_zero = self.expected_class == "exact_zero"
        predicted_band = None
        in_band = None
        value = self.one_minus_F_e
        value_metric = "process_infidelity_one_minus_F_e"
        if self.mechanism_pair == ("DR", "ZZ"):
            predicted_band = list(JOINT_CHANNEL_DR_ZZ_BAND)
            in_band = bool(
                JOINT_CHANNEL_DR_ZZ_BAND[0]
                <= self.one_minus_F_e
                <= JOINT_CHANNEL_DR_ZZ_BAND[1]
            )
        if exact_zero:
            value = self.superop_distance
            value_metric = "superop_frobenius_distance_exact_zero_witness"
        return {
            "row_id": self.row_id,
            "source_kind": self.source_kind,
            "source_hash": self.source_hash,
            "substep_id": self.substep_id,
            "substep": self.substep_id,
            "substep_kind": self.substep_kind,
            "operation_names": list(self.operation_names),
            "source_step_indices": list(self.source_step_indices),
            "source_operation_ids": [f"step:{i}" for i in self.source_step_indices],
            "operations": [dict(record) for record in self.operation_records],
            "lowered_mechanisms": [dict(record) for record in self.lowered_mechanisms],
            "participant": list(self.participant),
            "mechanism_pair": list(self.mechanism_pair),
            "pair_ij": " x ".join(self.mechanism_pair),
            "context_mechanisms": list(self.context_mechanisms),
            "dt_ns": self.dt_ns,
            "dt_ns_nominal": self.dt_ns_nominal,
            "dt_ns_bracket": list(self.dt_ns_bracket),
            "dt_source": self.dt_source,
            "sweep_mode": self.sweep_mode,
            "liouvillian_commutator_norm": self.liouvillian_commutator_norm,
            "commutator_fro": self.liouvillian_commutator_norm,
            "superop_distance": self.superop_distance,
            "one_minus_F_e": self.one_minus_F_e,
            "value": value,
            "value_metric": value_metric,
            "leading_one_minus_F_e": self.leading_one_minus_F_e,
            "exact_zero": exact_zero,
            "predicted_band": predicted_band,
            "in_band": in_band,
            "witness": {
                "structural_liouvillian_commutator_fro": self.liouvillian_commutator_norm,
                "channel_superop_frobenius_distance": self.superop_distance,
                "process_infidelity_one_minus_F_e": self.one_minus_F_e,
            },
            "expected_class": self.expected_class,
            "epistemic_class": self.epistemic_class,
            "epistemic_classes": _epistemic_breakdown(self.expected_class),
            "class": self.epistemic_class,
            "passed": self.passed,
            "failure_reason": self.failure_reason,
        }


@dataclass(frozen=True)
class JointChannelEvidenceResult:
    """Files and manifest returned by `write_joint_channel_comparison_evidence`."""

    out_dir: Path
    joint_channel_comparison: Path
    manifest: dict
    content_hash: str


@dataclass(frozen=True)
class JointChannelFreezeResult:
    """Freeze manifest returned by `freeze_joint_channel_comparison_evidence`."""

    freeze_path: Path
    evidence_path: Path
    manifest: dict


def joint_channel_comparison_gate(
    schedule: SubstepSchedule,
    *,
    device: str = "cuda",
) -> tuple[JointChannelComparisonRow, ...]:
    """Run the minimal declared joint-channel comparison gate.

    The input must be a compiler-generated schedule seam. The returned rows are
    evidence diagnostics only; they do not claim full analog process execution.
    """

    _validate_schedule_for_joint_channel_comparison(schedule)
    selection_plan = build_axis1_joint_channel_selection_plan(schedule)
    exact_selections = selection_plan.require_kind("zz_t2_exact_zero")
    nonzero_selections = selection_plan.require_kind("dr_zz_prediction_band")
    rows: list[JointChannelComparisonRow] = []
    for selection in exact_selections:
        for dt in _positive_dt_sweep(selection):
            rows.append(_zz_t2_exact_zero_row(schedule, selection, dt=dt, device=device))
    for selection in nonzero_selections:
        for dt in _positive_dt_sweep(selection):
            rows.append(_dr_zz_nonzero_row(schedule, selection, dt=dt, device=device))
    return tuple(rows)


def joint_channel_comparison_manifest(
    schedule: SubstepSchedule,
    *,
    device: str = "cuda",
) -> dict:
    """Return a serializable manifest for the joint-channel comparison gate."""

    rows = joint_channel_comparison_gate(schedule, device=device)
    selection_plan = build_axis1_joint_channel_selection_plan(schedule)
    details = _joint_channel_comparison_anti_toy_details(device=device)
    passed = all(row.passed for row in rows) and bool(details["pass"])
    payload = {
        "schema": "error_coupling_simulator.frontend.joint_channel_comparison.v1",
        "verdict": "pass" if passed else "fail",
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "compiler_provenance": {
            "schedule_seal_schema": COMPILER_SCHEDULE_SEAL_SCHEMA,
            "schedule_seal_valid": has_valid_compiler_schedule_seal(schedule),
            "schedule_seal_public": False,
            "generated_substeps": all(
                substep.generated_by_compiler for substep in schedule.substeps
            ),
        },
        "primitive_registry": default_axis1_primitive_registry().to_manifest(),
        "measured_on": "assembled q=2 substep channels from compiler schedule fixture",
        "metric": "composed-vs-joint channel infidelity",
        "metric_convention": "process/entanglement infidelity 1-F_e between trace-normalized Choi states",
        "metric_reference": "docs/METRICS.md#forward-fidelity--coupling-metrics",
        "comparison_scope": (
            "joint-channel comparison evidence only; no analog record emission, "
            "no Axis-2 source timeline, "
            "no leakage/qutrit integration"
        ),
        "selection_plan": selection_plan.to_manifest(),
        "rows": [row.to_manifest() for row in rows],
        "details": details,
        "passed": passed,
    }
    payload["content_hash"] = _stable_payload_hash(payload)
    return payload


def write_joint_channel_comparison_evidence(
    schedule: SubstepSchedule,
    out_dir: str | Path,
    *,
    device: str = "cuda",
    filename: str = "joint_channel_comparison.json",
) -> JointChannelEvidenceResult:
    """Write the comparison evidence object to `joint_channel_comparison.json`.

    This writer intentionally produces only the comparison evidence artifact. It does
    not run `Simulator`, does not write `.stim/.dem/.b8`, and does not attach
    source or leakage sidecars.
    """

    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    _assert_clean_joint_channel_evidence_dir(root)
    path = _safe_joint_channel_evidence_output_path(root, filename)
    manifest = joint_channel_comparison_manifest(schedule, device=device)
    write_json(path, manifest)
    return JointChannelEvidenceResult(
        out_dir=root,
        joint_channel_comparison=path,
        manifest=manifest,
        content_hash=str(manifest["content_hash"]),
    )


def freeze_joint_channel_comparison_evidence(
    joint_channel_comparison: str | Path,
    freeze_path: str | Path | None = None,
    *,
    overwrite: bool = False,
) -> JointChannelFreezeResult:
    """Write a deterministic freeze guard for a joint-channel comparison artifact."""

    evidence_path = Path(joint_channel_comparison)
    manifest = _load_joint_channel_manifest(evidence_path)
    _validate_joint_channel_manifest_content_hash(manifest, evidence_path)
    sha = file_sha256(evidence_path)
    if sha is None:
        raise FileNotFoundError(evidence_path)
    out = Path(freeze_path) if freeze_path is not None else _default_freeze_path(evidence_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and not overwrite:
        existing = _load_freeze_manifest(out)
        if existing["evidence_file"] != evidence_path.name:
            raise ValueError(
                "joint-channel comparison freeze evidence_file mismatch: "
                f"freeze={existing['evidence_file']!r} requested={evidence_path.name!r}"
            )
        validate_joint_channel_comparison_freeze(out)
        return JointChannelFreezeResult(
            freeze_path=out,
            evidence_path=evidence_path,
            manifest=existing,
        )
    payload = {
        "schema": "error_coupling_simulator.frontend.joint_channel_comparison_freeze.v1",
        "evidence_file": evidence_path.name,
        "evidence_schema": manifest.get("schema"),
        "evidence_sha256": sha,
        "evidence_content_hash": manifest.get("content_hash"),
        "source_kind": manifest.get("source_kind"),
        "source_hash": manifest.get("source_hash"),
        "verdict": manifest.get("verdict"),
        "passed": bool(manifest.get("passed")),
        "row_count": len(manifest.get("rows", [])),
        "details_schema": manifest.get("details", {}).get("schema"),
        "metric": manifest.get("metric"),
        "metric_reference": manifest.get("metric_reference"),
        "scope": (
            "joint-channel comparison evidence freeze only; not a full analog simulator run, "
            "not Axis-2 source projection"
        ),
    }
    write_json(out, payload)
    return JointChannelFreezeResult(
        freeze_path=out,
        evidence_path=evidence_path,
        manifest=payload,
    )


def validate_joint_channel_comparison_freeze(freeze_path: str | Path) -> dict:
    """Validate that frozen joint-channel comparison evidence did not drift."""

    path = Path(freeze_path)
    freeze = _load_freeze_manifest(path)
    evidence_path = path.parent / str(freeze["evidence_file"])
    manifest = _load_joint_channel_manifest(evidence_path)
    sha = file_sha256(evidence_path)
    if sha != freeze["evidence_sha256"]:
        raise ValueError(
            "joint-channel comparison evidence sha256 mismatch: "
            f"frozen={freeze['evidence_sha256']} current={sha}"
        )
    _validate_joint_channel_manifest_content_hash(manifest, evidence_path)
    checks = {
        "evidence_schema": manifest.get("schema") == freeze["evidence_schema"],
        "evidence_content_hash": manifest.get("content_hash")
        == freeze["evidence_content_hash"],
        "source_kind": manifest.get("source_kind") == freeze["source_kind"],
        "source_hash": manifest.get("source_hash") == freeze["source_hash"],
        "verdict": manifest.get("verdict") == freeze["verdict"],
        "passed": bool(manifest.get("passed")) == bool(freeze["passed"]),
        "row_count": len(manifest.get("rows", [])) == int(freeze["row_count"]),
        "details_schema": manifest.get("details", {}).get("schema") == freeze["details_schema"],
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise ValueError(f"joint-channel comparison freeze metadata mismatch: {failed}")
    return {
        "schema": (
            "error_coupling_simulator.frontend."
            "joint_channel_comparison_freeze_validation.v1"
        ),
        "freeze_file": path.name,
        "evidence_file": evidence_path.name,
        "evidence_sha256": sha,
        "evidence_content_hash": manifest.get("content_hash"),
        "checks": checks,
        "pass": True,
    }


def _validate_schedule_for_joint_channel_comparison(schedule: SubstepSchedule) -> None:
    if schedule.representability != ANALOG_SCHEDULE_REPRESENTABILITY:
        raise ValueError(
            "joint-channel comparison gate requires "
            f"{ANALOG_SCHEDULE_REPRESENTABILITY!r}, got {schedule.representability!r}"
        )
    if not schedule.source_hash:
        raise ValueError("joint-channel comparison gate requires a non-empty source_hash")
    if schedule.source_kind == "oracle_unit":
        raise ValueError("oracle_unit schedules are not accepted by the joint-channel comparison gate")
    if schedule.source_kind not in JOINT_CHANNEL_ALLOWED_SOURCE_KINDS:
        allowed = ", ".join(sorted(JOINT_CHANNEL_ALLOWED_SOURCE_KINDS))
        raise ValueError(
            "joint-channel comparison gate only accepts implemented schedule source kinds "
            f"({allowed}); got {schedule.source_kind!r}"
        )
    bad = [sub.substep_id for sub in schedule.substeps if not sub.generated_by_compiler]
    if bad:
        raise ValueError(
            "joint-channel comparison gate requires compiler-generated substeps: "
            f"{bad}"
        )
    require_compiler_schedule_seal(schedule)


def _positive_dt_sweep(selection: Axis1MechanismSelection) -> tuple[float, ...]:
    values = [selection.dt_ns_bracket[0], selection.dt_ns_nominal, selection.dt_ns_bracket[1]]
    out: list[float] = []
    for raw in values:
        if raw is None:
            continue
        dt = float(raw)
        if dt <= 0.0:
            continue
        if not any(abs(dt - prev) <= 1e-12 for prev in out):
            out.append(dt)
    if not out:
        raise ValueError(f"selection {selection.selection_id!r} has no positive dt values")
    return tuple(out)


def _epistemic_breakdown(expected_class: str) -> dict[str, str]:
    if expected_class == "exact_zero":
        return {
            "structural_commutation_identity": "a",
            "superop_distance_threshold": "c",
            "process_infidelity_diagnostic": "c",
        }
    if expected_class == "prediction_band_nonzero":
        return {
            "nonzero_commutator_witness": "a",
            "process_infidelity_prediction_band": "b",
            "dt_bracket_and_thresholds": "c",
        }
    return {"row": "c"}


def _zz_t2_exact_zero_row(
    schedule: SubstepSchedule,
    selection: Axis1MechanismSelection,
    *,
    dt: float,
    device: str,
) -> JointChannelComparisonRow:
    bundle = _lower_primitives(selection.primitive_names, dt=dt, device=device)
    H_ZZ = bundle.H_list[0]
    c_T2 = bundle.c_list[0]
    comm = liouvillian_commutator_norm({"H": H_ZZ}, {"c": c_T2}, device=device)
    superop_distance = composed_vs_joint_superop_distance(
        bundle.H_list,
        bundle.c_list,
        dt,
        device=device,
    )
    one_minus = composed_vs_joint_infidelity(bundle.H_list, bundle.c_list, dt, device=device)
    passed = comm <= NUMERICAL_ZERO and superop_distance <= SUPEROP_EXACTZERO_TOL
    failure = None
    if not passed:
        failure = (
            "ZZ x T2 exact-zero witnesses failed: "
            f"commutator={comm:.3e}, superop_distance={superop_distance:.3e}"
        )
    return JointChannelComparisonRow(
        row_id=f"{selection.selection_id}:dt={dt:g}",
        source_kind=schedule.source_kind,
        source_hash=schedule.source_hash,
        substep_id=selection.substep_id,
        substep_kind=selection.substep_kind,
        operation_names=selection.operation_names,
        source_step_indices=selection.source_step_indices,
        operation_records=selection.operation_records,
        lowered_mechanisms=tuple(record.to_manifest() for record in bundle.records),
        participant=selection.participant,
        mechanism_pair=selection.mechanism_pair,
        context_mechanisms=selection.context_mechanisms,
        dt_ns=float(dt),
        dt_ns_nominal=selection.dt_ns_nominal,
        dt_ns_bracket=selection.dt_ns_bracket,
        dt_source=selection.dt_source,
        sweep_mode="exact_zero_dt_sweep",
        liouvillian_commutator_norm=comm,
        superop_distance=superop_distance,
        one_minus_F_e=one_minus,
        leading_one_minus_F_e=None,
        expected_class="exact_zero",
        epistemic_class="a",
        passed=passed,
        failure_reason=failure,
    )


def _dr_zz_nonzero_row(
    schedule: SubstepSchedule,
    selection: Axis1MechanismSelection,
    *,
    dt: float,
    device: str,
) -> JointChannelComparisonRow:
    bundle = _lower_primitives(selection.primitive_names, dt=dt, device=device)
    coherent = _lower_primitives(("DR", "ZZ"), dt=dt, device=device)
    H_DR = coherent.H_list[0]
    H_ZZ = coherent.H_list[1]
    comm = liouvillian_commutator_norm({"H": H_DR}, {"H": H_ZZ}, device=device)
    superop_distance = composed_vs_joint_superop_distance(
        bundle.H_list,
        bundle.c_list,
        dt,
        device=device,
    )
    one_minus = composed_vs_joint_infidelity(
        bundle.H_list,
        bundle.c_list,
        dt,
        device=device,
    )
    leading = composed_vs_joint_infidelity_leading(coherent.H_list, dt, device=device)
    lo, hi = JOINT_CHANNEL_DR_ZZ_BAND
    passed = (
        comm > JOINT_CHANNEL_NONZERO_COMMUTATOR_MIN
        and superop_distance > JOINT_CHANNEL_NONZERO_SUPEROP_DISTANCE_MIN
        and lo <= one_minus <= hi
    )
    failure = None
    if not passed:
        failure = (
            "DR x ZZ nonzero witnesses failed: "
            f"commutator={comm:.3e}, superop_distance={superop_distance:.3e}, "
            f"one_minus_F_e={one_minus:.3e}, band=[{lo:.3e}, {hi:.3e}]"
        )
    return JointChannelComparisonRow(
        row_id=f"{selection.selection_id}:dt={dt:g}",
        source_kind=schedule.source_kind,
        source_hash=schedule.source_hash,
        substep_id=selection.substep_id,
        substep_kind=selection.substep_kind,
        operation_names=selection.operation_names,
        source_step_indices=selection.source_step_indices,
        operation_records=selection.operation_records,
        lowered_mechanisms=tuple(record.to_manifest() for record in bundle.records),
        participant=selection.participant,
        mechanism_pair=selection.mechanism_pair,
        context_mechanisms=selection.context_mechanisms,
        dt_ns=float(dt),
        dt_ns_nominal=selection.dt_ns_nominal,
        dt_ns_bracket=selection.dt_ns_bracket,
        dt_source=selection.dt_source,
        sweep_mode="area_preserving_pi_pulse_dt_sweep",
        liouvillian_commutator_norm=comm,
        superop_distance=superop_distance,
        one_minus_F_e=one_minus,
        leading_one_minus_F_e=leading,
        expected_class="prediction_band_nonzero",
        epistemic_class="b",
        passed=passed,
        failure_reason=failure,
    )


def _joint_channel_comparison_anti_toy_details(*, device: str) -> dict:
    """Full anti-toy checks for the joint-channel comparison.

    Rows carry schedule provenance. These details carry the comparison gate's
    non-vacuity checks: exact-zero diagnostics, broken-assembler negative
    control, physical/fixed-omega power laws, and zeta scaling.
    """

    check1 = _check_exact_zero_control(device=device)
    check2 = _check_broken_control_must_fail(device=device)
    check3 = _check_dr_zz_band_and_powerlaws(device=device)
    params = {
        "zeta_rad_per_ns": JOINT_CHANNEL_ZETA_RAD_PER_NS,
        "gamma_phi_per_ns": JOINT_CHANNEL_GAMMA_PHI_PER_NS,
        "gamma_1_per_ns": JOINT_CHANNEL_GAMMA_1_PER_NS,
        "phys_band": list(JOINT_CHANNEL_DR_ZZ_BAND),
        "fixed_omega_band": list(JOINT_CHANNEL_FIXED_OMEGA_BAND),
        "dt_grid": list(JOINT_CHANNEL_DT_GRID),
        "dt_control": list(JOINT_CHANNEL_DT_CONTROL),
        "dt_small": list(JOINT_CHANNEL_DT_SMALL),
        "fixed_omega_rad_per_ns": JOINT_CHANNEL_FIXED_OMEGA_RAD_PER_NS,
        "slope_tol": JOINT_CHANNEL_SLOPE_TOL,
    }
    return {
        "schema": (
            "error_coupling_simulator.frontend."
            "joint_channel_comparison_anti_toy_details.v1"
        ),
        "check1_exact_zero_control": check1,
        "check2_broken_control_must_fail": check2,
        "check3_dr_zz_band_powerlaws": check3,
        "params": params,
        "pass": bool(check1["pass"] and check2["pass"] and check3["pass"]),
    }


def _check_exact_zero_control(*, device: str) -> dict:
    H_list = [_H_ZZ(device=device)]
    c_list = [_c_T2(device=device)]
    liou_comm_norm = liouvillian_commutator_norm({"H": H_list[0]}, {"c": c_list[0]}, device=device)
    structural_ok = liou_comm_norm <= NUMERICAL_ZERO
    superop_dist = {}
    choi_dist = {}
    inf_1mF = {}
    for dt in JOINT_CHANNEL_DT_CONTROL:
        key = f"dt_{dt:g}"
        superop_dist[key] = composed_vs_joint_superop_distance(H_list, c_list, dt, device=device)
        choi_dist[key] = composed_vs_joint_choi_distance(H_list, c_list, dt, device=device)
        inf_1mF[key] = composed_vs_joint_infidelity(H_list, c_list, dt, device=device)
    max_superop_dist = max(superop_dist.values())
    channel_ok = max_superop_dist <= SUPEROP_EXACTZERO_TOL
    return {
        "liouvillian_commutator_fro": liou_comm_norm,
        "liouvillian_commutator_tol": NUMERICAL_ZERO,
        "structural_witness_ok": bool(structural_ok),
        "superop_frobenius_dist_per_dt": superop_dist,
        "superop_exactzero_tol": SUPEROP_EXACTZERO_TOL,
        "max_superop_frobenius_dist": max_superop_dist,
        "channel_witness_ok": bool(channel_ok),
        "choi_frobenius_dist_per_dt_DIAGNOSTIC": choi_dist,
        "one_minus_Fe_per_dt_DIAGNOSTIC": inf_1mF,
        "pass": bool(structural_ok and channel_ok),
    }


def _check_broken_control_must_fail(*, device: str) -> dict:
    H_list = [_H_ZZ(device=device)]
    c_list = [_c_T2(device=device)]
    broken_superop = {}
    broken_choi = {}
    broken_1mF = {}
    for dt in JOINT_CHANNEL_DT_CONTROL:
        key = f"dt_{dt:g}"
        sd, cd, one_minus = _broken_distances_and_infidelity(
            H_list,
            c_list,
            dt,
            device=device,
        )
        broken_superop[key] = sd
        broken_choi[key] = cd
        broken_1mF[key] = one_minus
    min_broken_superop = min(broken_superop.values())
    loud = min_broken_superop > 1.0e-6
    return {
        "broken_superop_dist_per_dt": broken_superop,
        "broken_choi_dist_per_dt_DIAGNOSTIC": broken_choi,
        "broken_one_minus_Fe_per_dt_DIAGNOSTIC": broken_1mF,
        "min_broken_superop_dist": min_broken_superop,
        "loud_threshold": 1.0e-6,
        "broken_fails_loudly": bool(loud),
        "pass": bool(loud),
    }


def _check_dr_zz_band_and_powerlaws(*, device: str) -> dict:
    c_list = [_c_T2(device=device), _c_T1(device=device)]

    phys_band_vals = []
    fixed_band_vals = []
    for dt in JOINT_CHANNEL_DT_GRID:
        phys_band_vals.append(
            composed_vs_joint_infidelity(
                [_H_DR(math.pi / dt, device=device), _H_ZZ(device=device)],
                c_list,
                dt,
                device=device,
            )
        )
        fixed_band_vals.append(
            composed_vs_joint_infidelity(
                [
                    _H_DR(JOINT_CHANNEL_FIXED_OMEGA_RAD_PER_NS, device=device),
                    _H_ZZ(device=device),
                ],
                c_list,
                dt,
                device=device,
            )
        )
    phys_in_band = all(
        JOINT_CHANNEL_DR_ZZ_BAND[0] <= v <= JOINT_CHANNEL_DR_ZZ_BAND[1]
        for v in phys_band_vals
    )
    fixed_in_band = all(
        JOINT_CHANNEL_FIXED_OMEGA_BAND[0] <= v <= JOINT_CHANNEL_FIXED_OMEGA_BAND[1]
        for v in fixed_band_vals
    )
    phys_full_context_slope = _loglog_slope(JOINT_CHANNEL_DT_GRID, phys_band_vals)
    fixed_full_context_slope = _loglog_slope(JOINT_CHANNEL_DT_GRID, fixed_band_vals)

    phys_ham_vals = [
        composed_vs_joint_infidelity(
            [_H_DR(math.pi / dt, device=device), _H_ZZ(device=device)],
            [],
            dt,
            device=device,
        )
        for dt in JOINT_CHANNEL_DT_GRID
    ]
    phys_slope = _loglog_slope(JOINT_CHANNEL_DT_GRID, phys_ham_vals)
    phys_slope_ok = abs(phys_slope - 2.0) <= JOINT_CHANNEL_SLOPE_TOL

    fixed_small_vals = [
        composed_vs_joint_infidelity(
            [
                _H_DR(JOINT_CHANNEL_FIXED_OMEGA_RAD_PER_NS, device=device),
                _H_ZZ(device=device),
            ],
            [],
            dt,
            device=device,
        )
        for dt in JOINT_CHANNEL_DT_SMALL
    ]
    fixed_small_slope = _loglog_slope(JOINT_CHANNEL_DT_SMALL, fixed_small_vals)
    fixed_small_slope_ok = abs(fixed_small_slope - 4.0) <= JOINT_CHANNEL_SLOPE_TOL

    fixed_device_vals = [
        composed_vs_joint_infidelity(
            [
                _H_DR(JOINT_CHANNEL_FIXED_OMEGA_RAD_PER_NS, device=device),
                _H_ZZ(device=device),
            ],
            [],
            dt,
            device=device,
        )
        for dt in JOINT_CHANNEL_DT_GRID
    ]
    fixed_leading_vals = [
        composed_vs_joint_infidelity_leading(
            [
                _H_DR(JOINT_CHANNEL_FIXED_OMEGA_RAD_PER_NS, device=device),
                _H_ZZ(device=device),
            ],
            dt,
            device=device,
        )
        for dt in JOINT_CHANNEL_DT_GRID
    ]
    fixed_device_slope = _loglog_slope(JOINT_CHANNEL_DT_GRID, fixed_device_vals)
    fixed_leading_slope = _loglog_slope(JOINT_CHANNEL_DT_GRID, fixed_leading_vals)

    dt0 = 25.0
    omega0 = math.pi / dt0
    zeta_grid = [
        0.5 * JOINT_CHANNEL_ZETA_RAD_PER_NS,
        JOINT_CHANNEL_ZETA_RAD_PER_NS,
        2.0 * JOINT_CHANNEL_ZETA_RAD_PER_NS,
    ]
    zeta_vals = [
        composed_vs_joint_infidelity(
            [_H_DR(omega0, device=device), _H_ZZ(zeta, device=device)],
            [],
            dt0,
            device=device,
        )
        for zeta in zeta_grid
    ]
    zeta_slope = _loglog_slope(zeta_grid, zeta_vals)
    zeta_slope_ok = abs(zeta_slope - 2.0) <= JOINT_CHANNEL_SLOPE_TOL

    passed = (
        phys_in_band
        and fixed_in_band
        and phys_slope_ok
        and fixed_small_slope_ok
        and zeta_slope_ok
    )
    return {
        "physical": {
            "dt_grid": list(JOINT_CHANNEL_DT_GRID),
            "band_vals_full_substep": phys_band_vals,
            "band": list(JOINT_CHANNEL_DR_ZZ_BAND),
            "in_band": bool(phys_in_band),
            "full_substep_context_slope_FINDING": phys_full_context_slope,
            "full_substep_context_mechanisms": ["T2", "T1"],
            "powerlaw_vals_ham_only": phys_ham_vals,
            "gated_powerlaw_scope": "coherent_DR_ZZ_component_hamiltonian_only",
            "loglog_slope_exact": phys_slope,
            "target_slope": 2.0,
            "slope_ok": bool(phys_slope_ok),
        },
        "fixed_omega": {
            "dt_grid_device": list(JOINT_CHANNEL_DT_GRID),
            "dt_grid_small": list(JOINT_CHANNEL_DT_SMALL),
            "band_vals_full_substep": fixed_band_vals,
            "band": list(JOINT_CHANNEL_FIXED_OMEGA_BAND),
            "in_band": bool(fixed_in_band),
            "full_substep_context_slope_FINDING": fixed_full_context_slope,
            "full_substep_context_mechanisms": ["T2", "T1"],
            "smalldt_exact_vals": fixed_small_vals,
            "gated_powerlaw_scope": "coherent_DR_ZZ_component_hamiltonian_only",
            "smalldt_exact_slope": fixed_small_slope,
            "target_slope": 4.0,
            "smalldt_slope_ok": bool(fixed_small_slope_ok),
            "device_exact_vals": fixed_device_vals,
            "device_exact_slope_FINDING": fixed_device_slope,
            "leading_order_vals_DIAGNOSTIC": fixed_leading_vals,
            "leading_order_slope_DIAGNOSTIC": fixed_leading_slope,
            "omega_const": JOINT_CHANNEL_FIXED_OMEGA_RAD_PER_NS,
        },
        "zeta_scaling": {
            "zeta_grid": zeta_grid,
            "vals": zeta_vals,
            "loglog_slope": zeta_slope,
            "target_slope": 2.0,
            "slope_ok": bool(zeta_slope_ok),
            "dt": dt0,
        },
        "pass": bool(passed),
    }


def _broken_distances_and_infidelity(H_list, c_list, dt, *, device: str) -> tuple[float, float, float]:
    import torch

    L_broken = _broken_liouvillian_superop(H_list, c_list, device=device)
    S_broken = _superop_expm(L_broken, dt, device=device)
    S_composed = _composed_superop(H_list, c_list, dt, device=device)
    superop_dist = float(torch.linalg.matrix_norm(S_broken - S_composed).item())
    joint_broken, _r, _d = superop_to_kraus(S_broken, device=device)
    composed = composed_substep_channel(H_list, c_list, dt, device=device)
    J_joint = _choi_state_from_kraus(joint_broken, device=device)
    J_comp = _choi_state_from_kraus(composed, device=device)
    choi_dist = float(torch.linalg.matrix_norm(J_joint - J_comp).item())
    one_minus = float(max(0.0, 1.0 - _state_fidelity(J_joint, J_comp, device=device)))
    return superop_dist, choi_dist, one_minus


def _broken_liouvillian_superop(H_list, c_list, *, device: str):
    import torch

    dev = str(device)
    cdt = torch.complex128
    ops = list(H_list) + list(c_list)
    if not ops:
        raise ValueError("broken Liouvillian needs at least one H or c operator")
    D = int(torch.as_tensor(ops[0]).shape[-1])
    eye = torch.eye(D, dtype=cdt, device=dev)
    H = torch.zeros((D, D), dtype=cdt, device=dev)
    for Hi in H_list:
        H = H + torch.as_tensor(Hi, dtype=cdt, device=dev)
    L = +1j * (
        torch.kron(eye.contiguous(), H.contiguous())
        - torch.kron(H.transpose(-1, -2).contiguous(), eye.contiguous())
    )
    for ck in c_list:
        c = torch.as_tensor(ck, dtype=cdt, device=dev)
        cdag_c = c.conj().transpose(-1, -2) @ c
        L = L + torch.kron(c.conj().contiguous(), c.contiguous())
        L = L - 0.5 * torch.kron(eye.contiguous(), cdag_c.contiguous())
        L = L - 0.5 * torch.kron(cdag_c.transpose(-1, -2).contiguous(), eye.contiguous())
    return L


def _loglog_slope(xs, ys) -> float:
    lx = [math.log(float(x)) for x in xs]
    ly = [math.log(float(y)) for y in ys]
    mean_x = sum(lx) / len(lx)
    mean_y = sum(ly) / len(ly)
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(lx, ly, strict=True))
    den = sum((x - mean_x) ** 2 for x in lx)
    return num / den if den else float("nan")


def _H_DR(omega: float, *, device: str):
    return _lower_primitives(
        ("DR",),
        dt=25.0,
        device=device,
        drive_omega_rad_per_ns=float(omega),
    ).H_list[0]


def _H_ZZ(zeta: float = JOINT_CHANNEL_ZETA_RAD_PER_NS, *, device: str):
    return _lower_primitives(("ZZ",), dt=25.0, device=device, zeta_rad_per_ns=float(zeta)).H_list[0]


def _c_T2(*, device: str):
    return _lower_primitives(("T2",), dt=25.0, device=device).c_list[0]


def _c_T1(*, device: str):
    return _lower_primitives(("T1",), dt=25.0, device=device).c_list[0]


def _lower_primitives(
    names,
    *,
    dt: float,
    device: str,
    zeta_rad_per_ns: float | None = None,
    drive_omega_rad_per_ns: float | None = None,
):
    return default_axis1_primitive_registry().lower(
        names,
        dt_ns=float(dt),
        params=Axis1PrimitiveParams(
            zeta_rad_per_ns=(
                JOINT_CHANNEL_ZETA_RAD_PER_NS
                if zeta_rad_per_ns is None
                else float(zeta_rad_per_ns)
            ),
            gamma_phi_per_ns=JOINT_CHANNEL_GAMMA_PHI_PER_NS,
            gamma_1_per_ns=JOINT_CHANNEL_GAMMA_1_PER_NS,
            drive_omega_rad_per_ns=drive_omega_rad_per_ns,
        ),
        device=device,
    )


def _stable_payload_hash(payload: dict[str, Any]) -> str:
    content = dict(payload)
    content.pop("content_hash", None)
    encoded = json.dumps(
        _jsonable(content),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _default_freeze_path(evidence_path: Path) -> Path:
    return evidence_path.with_name(f"{evidence_path.stem}.freeze.json")


def _assert_clean_joint_channel_evidence_dir(root: Path) -> None:
    forbidden = sorted(
        path.name
        for path in root.iterdir()
        if path.is_file()
        and _joint_channel_forbidden_artifact_path(path)
    )
    if forbidden:
        raise ValueError(
            "joint-channel comparison writer refuses simulator-run artifact directories: "
            f"{forbidden}"
        )


def _safe_joint_channel_evidence_output_path(root: Path, filename: str) -> Path:
    raw = str(filename)
    candidate = Path(raw)
    if not raw or candidate.is_absolute() or candidate.name != raw:
        raise ValueError(
            "joint-channel comparison writer refuses non-local evidence filename: "
            f"{raw!r}"
        )
    if _joint_channel_forbidden_artifact_path(candidate):
        raise ValueError(
            "joint-channel comparison writer refuses forbidden evidence filename: "
            f"{raw!r}"
        )
    return root / candidate.name


def _joint_channel_forbidden_artifact_path(path: Path) -> bool:
    suffixes = {str(s).lower() for s in JOINT_CHANNEL_FORBIDDEN_OUTPUT_SUFFIXES}
    names = {str(name).lower() for name in JOINT_CHANNEL_FORBIDDEN_OUTPUT_NAMES}
    return path.suffix.lower() in suffixes or path.name.lower() in names


def _load_joint_channel_manifest(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(
            f"joint-channel comparison manifest must be a JSON object: {path}"
        )
    expected_schema = "error_coupling_simulator.frontend.joint_channel_comparison.v1"
    if payload.get("schema") != expected_schema:
        raise ValueError(
            "unexpected joint-channel comparison schema in "
            f"{path}: {payload.get('schema')!r}"
        )
    return payload


def _load_freeze_manifest(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(
            f"joint-channel comparison freeze manifest must be a JSON object: {path}"
        )
    expected_schema = (
        "error_coupling_simulator.frontend.joint_channel_comparison_freeze.v1"
    )
    if payload.get("schema") != expected_schema:
        raise ValueError(
            "unexpected joint-channel comparison freeze schema in "
            f"{path}: {payload.get('schema')!r}"
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
        "row_count",
        "details_schema",
    }
    missing = sorted(required - set(payload))
    if missing:
        raise ValueError(f"joint-channel comparison freeze manifest missing fields: {missing}")
    evidence_file = Path(str(payload["evidence_file"]))
    if evidence_file.name != str(payload["evidence_file"]) or evidence_file.is_absolute():
        raise ValueError(
            "joint-channel comparison freeze evidence_file must be a local filename"
        )
    return payload


def _validate_joint_channel_manifest_content_hash(manifest: dict, path: Path) -> None:
    expected = manifest.get("content_hash")
    if not isinstance(expected, str) or len(expected) != 64:
        raise ValueError(
            f"joint-channel comparison manifest has invalid content_hash: {path}"
        )
    actual = _stable_payload_hash(manifest)
    if actual != expected:
        raise ValueError(
            "joint-channel comparison content_hash mismatch: "
            f"frozen={expected} recomputed={actual}"
        )


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


__all__ = [
    "JOINT_CHANNEL_ALLOWED_SOURCE_KINDS",
    "JOINT_CHANNEL_DR_ZZ_BAND",
    "JOINT_CHANNEL_GAMMA_1_PER_NS",
    "JOINT_CHANNEL_GAMMA_PHI_PER_NS",
    "JOINT_CHANNEL_NONZERO_COMMUTATOR_MIN",
    "JOINT_CHANNEL_NONZERO_SUPEROP_DISTANCE_MIN",
    "JOINT_CHANNEL_ZETA_RAD_PER_NS",
    "JointChannelComparisonRow",
    "JointChannelEvidenceResult",
    "JointChannelFreezeResult",
    "freeze_joint_channel_comparison_evidence",
    "joint_channel_comparison_gate",
    "joint_channel_comparison_manifest",
    "validate_joint_channel_comparison_freeze",
    "write_joint_channel_comparison_evidence",
]
