from __future__ import annotations

"""Executable Axis-1 carrier seam.

This module consumes the schedule-derived :mod:`axis1_carrier_program` IR. The
default backend executes only the dense-checkable route through the existing
joint-L state and record evidence paths. A separate explicit qutip-cuquantum
backend executes the restricted over-cap probe slice. Neither path is the future
production QT/MPS carrier, and no path silently replaces over-cap rows with a
dense channel or pairwise fallback.
"""

import copy
import ctypes
from dataclasses import dataclass
import errno
import hashlib
from importlib import metadata
import json
import math
from numbers import Real
import os
from pathlib import Path
import platform
import stat
import subprocess
import tempfile
from typing import Any

import numpy as np
import torch

from .. import _PACKAGE_TREE_SHA256_AT_IMPORT
from ..carrier.records import RecordBatch
from ..carrier.mps.controls import (
    normalize_mps_bool,
    normalize_mps_choice,
    normalize_mps_device,
    normalize_mps_finite_real,
    normalize_mps_index,
    normalize_mps_index_sequence,
    normalize_mps_max_bond,
    normalize_optional_mps_index,
)
from ..numerics import NUMERICAL_ZERO
from .analog_schedule import SubstepSchedule
from .axis1_carrier_program import (
    AXIS1_CARRIER_DEFAULT_BACKEND_CONTRACT,
    AXIS1_CARRIER_MCWF_MPS_BACKEND_CONTRACT,
    AXIS1_CARRIER_PROGRAM_SCHEMA,
    axis1_carrier_program_manifest,
)
from .axis1_channel_evidence import (
    _validate_schedule_for_axis1_channel_evidence,
)
from .axis1_record_evidence import (
    Axis1ReadoutResetInstrumentSpec,
    axis1_measurement_record_evidence_manifest,
)
from .axis1_record_layout import (
    Axis1ScheduleRecordLayout,
    _require_exact_binary_record_matrix,
    _validate_axis1_projected_record_payload,
    axis1_record_layout_from_schedule,
    project_axis1_xor_records,
)
from .axis1_state_evidence import (
    AXIS1_STATE_MAX_EXACT_QUBITS,
    _require_cuda_device,
    axis1_state_evolution_evidence_manifest,
)
from .axis1_qutip_cuquantum_probe import (
    AXIS1_QUTIP_CUQUANTUM_PROBE_BACKEND_CONTRACT,
    axis1_qutip_cuquantum_record_probe_manifest,
    axis1_qutip_cuquantum_trajectory_probe_manifest,
)
from .artifacts import (
    file_sha256,
    record_summary,
    write_b8_optional,
)


AXIS1_CARRIER_EXECUTION_SCHEMA = "error_coupling_simulator.frontend.carrier_execution.v5"
AXIS1_CARRIER_EXECUTION_REPRESENTABILITY = (
    "axis1_carrier_execution_dense_jointL_probe_no_scalable_overcap"
)
AXIS1_CARRIER_QUTIP_RESTRICTED_EXECUTION_REPRESENTABILITY = (
    "axis1_carrier_execution_qutip_cuquantum_restricted_no_production_scalable"
)
AXIS1_CARRIER_EXECUTION_BACKEND_CONTRACT = "dense_jointL_probe"
AXIS1_CARRIER_QUTIP_RESTRICTED_EXECUTION_BACKEND_CONTRACT = (
    "qutip_cuquantum_restricted_state_record_probe"
)
AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_REPRESENTABILITY = (
    "axis1_carrier_execution_qt_mps_restricted_no_production_scalable"
)
AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT = (
    AXIS1_CARRIER_DEFAULT_BACKEND_CONTRACT
)
AXIS1_CARRIER_MCWF_MPS_EXECUTION_REPRESENTABILITY = (
    "axis1_carrier_execution_mcwf_mps_fixed_microstep_or_fail_closed"
)
AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT = (
    AXIS1_CARRIER_MCWF_MPS_BACKEND_CONTRACT
)
AXIS1_CARRIER_AUTO_BACKEND_CONTRACT = "auto"
AXIS1_CARRIER_AUTO_EXECUTION_SCHEMA = (
    "error_coupling_simulator.frontend.carrier_auto_routed_execution.v5"
)
AXIS1_MCWF_MPS_RECORD_OUTPUT_SCHEMA = (
    "error_coupling_simulator.frontend.mcwf_mps_record_sample_summary.v1"
)
AXIS1_MCWF_MPS_RECORD_OUTPUT_REPRESENTABILITY = (
    "axis1_mcwf_mps_grouped_canonical_record_batch_b8_"
    "no_original_trajectory_order"
)
# The grouped writer preallocates one uint8 output table and RecordBatch freezes
# one copy. Its current binary validation can transiently hold up to three bool
# comparison arrays for either side, so four bytes per output bit is the exact
# conservative NumPy Record-array payload bound. It is not a whole-process RSS
# estimate and excludes the already-resident Carrier, Python metadata, canonical
# JSON authentication, allocator overhead, and publication provenance.
AXIS1_MCWF_MPS_RECORD_MAX_ARRAY_PAYLOAD_BYTES = 512 * 1024 * 1024
AXIS1_MCWF_MPS_RECORD_MAX_SUPPORT_CELLS = 16 * 1024 * 1024
_MCWF_RECORD_ARRAY_PAYLOAD_BYTES_PER_OUTPUT_BIT = 4
_MCWF_RECORD_MATERIALIZATION_ORDER = (
    "carrier_histogram_grouped_canonical_support_order"
)
_MCWF_RECORD_SAMPLE_SUMMARY_FILENAME = "axis1_mcwf_mps_sample_summary.json"
_MCWF_RECORD_CARRIER_EVIDENCE_FILENAME = "axis1_mcwf_mps_carrier_execution.json"
_MCWF_RECORD_CARRIER_PROGRAM_FILENAME = "axis1_mcwf_mps_carrier_program.json"
_AT_FDCWD = -100
_RENAME_NOREPLACE = 1
_MCWF_RECORD_SOURCE_SHA256_AT_IMPORT = file_sha256(Path(__file__).resolve())
if (
    not isinstance(_MCWF_RECORD_SOURCE_SHA256_AT_IMPORT, str)
    or len(_MCWF_RECORD_SOURCE_SHA256_AT_IMPORT) != 64
):
    raise RuntimeError("MCWF Record source-file SHA-256 is unavailable at import")


@dataclass(frozen=True)
class Axis1McwfMpsRecordSampleResult:
    """Canonical RecordBatch and `.b8` files materialized from one MCWF run."""

    out_dir: Path
    detection_events: Path | None
    obs_flips_actual: Path | None
    carrier_evidence: Path
    carrier_program_evidence: Path
    sample_summary: Path
    sample_manifest: dict[str, Any]
    record_batch: RecordBatch


@dataclass(frozen=True)
class _Axis1McwfMpsRecordBinding:
    """Same-call consistency hashes, not a cryptographic or replay boundary."""

    carrier_content_hash: str
    direct_content_hash: str
    record_execution_content_hash: str
    restricted_acceptance_policy_content_hash: str


@dataclass(frozen=True)
class _Axis1McwfMpsRecordPreflight:
    source_kind: str
    source_hash: str
    schedule_representability: str
    num_qubits: int
    device: str
    execution_backend_options: dict[str, Any]
    expected_execution_options: dict[str, Any]
    carrier_program: dict[str, Any]
    layout: Axis1ScheduleRecordLayout
    trajectory_count: int
    detector_width: int
    observable_width: int
    estimated_peak_record_array_payload_bytes: int
    max_record_array_payload_bytes: int
    estimated_record_support_upper_bound: int
    estimated_record_support_cells: int
    max_record_support_cells: int


@dataclass(frozen=True)
class _Axis1McwfMpsRecordPublicationPreflight:
    target_parent: Path
    target_parent_fd: int
    target_parent_device: int
    target_parent_inode: int
    environment_lock_path: Path
    environment_lock_sha256: str
    build_identity: dict[str, Any]
    source_implementation: dict[str, Any]
    environment_identity: dict[str, Any]


@dataclass(frozen=True)
class _Axis1McwfMpsRecordStage:
    name: str
    fd: int
    path: Path
    device: int
    inode: int


@dataclass(frozen=True)
class _Axis1McwfMpsRecordArtifactSeal:
    name: str
    device: int
    inode: int
    mode: int
    size_bytes: int
    mtime_ns: int
    ctime_ns: int
    sha256: str
_RESTRICTED_POLICY_SCHEMAS = {
    "mcwf": (
        "error_coupling_simulator.frontend."
        "mcwf_mps_restricted_acceptance_policy.v7"
    ),
    "qt": (
        "error_coupling_simulator.frontend."
        "qt_mps_restricted_acceptance_policy.v2"
    ),
}
_RESTRICTED_EXECUTION_SCHEMAS = {
    "mcwf": (
        "error_coupling_simulator.frontend."
        "mcwf_mps_state_record_execution.v8"
    ),
    "qt": (
        "error_coupling_simulator.frontend."
        "qt_mps_restricted_execution.v6"
    ),
}
_RESTRICTED_POLICY_ROLE = "restricted_execution_acceptance_not_metric"
_MCWF_SAMPLED_TRAJECTORY_MODE = "sampled_fixed_microstep_mcwf_trajectories"
_MCWF_MEASUREMENT_SAMPLING_POLICY = (
    "sequential_conditional_single_site_level_xz_v1"
)
_MCWF_RECORD_SUPPORT_POLICY = "observed_empirical_outcomes_only"
_MCWF_MEASUREMENT_POLICY_NAME = (
    "declared_basis_eigenlabel_sample_then_binary_record"
)
_MCWF_MEASUREMENT_BIT_MAPPING = (
    "eigenlabel_0_to_bit_0_eigenlabel_1_to_bit_1_"
    "eigenlabel_ge_2_to_bit_1_with_probability_leaked_readout_b"
)
_MCWF_MEASUREMENT_BASIS_SEMANTICS = (
    "measurement_bases and reset_after are schedule-ordered one-per-Record-column; "
    "X measurement rotates into Z, projects, then rotates back unless reset prepares |+>"
)
_MCWF_JOINT_LEVEL_BINARY_COMPARISON_OBJECT = (
    "measurement_basis_level_and_emitted_binary_record_populations"
)
_MCWF_DIRECT_REPRESENTABILITY = (
    "axis1_mcwf_mps_fixed_microstep_local_dims_state_record"
)
_MCWF_DIRECT_CHILD_FIELDS = frozenset(
    {
        "schema",
        "source_kind",
        "source_hash",
        "schedule_representability",
        "representability",
        "backend_contract",
        "gpu_required",
        "device",
        "carrier_program",
        "local_hilbert_space",
        "max_bond",
        "worst_cut_discarded_weight_gate",
        "total_discarded_weight_gate",
        "microstep_count",
        "mass_residual_budget",
        "finite_step_order",
        "trajectory_count",
        "rng_seed",
        "initial_levels",
        "leaked_readout_b",
        "execution_status",
        "certification_status",
        "diagnostic_only",
        "claims_mcwf_mps_backend_execution",
        "claims_production_scalable_backend",
        "claims_exact_joint_lindblad_generator",
        "claims_dense_channel_evidence",
        "claims_dem_decoder_semantics",
        "claims_axis2_source_timeline",
        "scored_quantity_policy",
        "approximation_book",
        "epistemic_classes",
        "verdict",
        "passed",
        "mcwf_mps_backend_executed",
        "blocked_reason",
        "blocked_substeps",
        "mps_execution",
        "dynamics_artifact_reference_certification",
        "restricted_acceptance_policy",
        "scope",
        "content_hash",
    }
)
_MCWF_CARRIER_CHILD_FIELDS = frozenset(
    {
        "schema",
        "source_kind",
        "source_hash",
        "schedule_representability",
        "representability",
        "execution_backend_contract",
        "gpu_required",
        "device",
        "execution_backend_options",
        "execution_status",
        "certification_status",
        "diagnostic_only",
        "verdict",
        "passed",
        "blocked_reason",
        "dense_probe_executed",
        "qt_mps_backend_executed",
        "mcwf_mps_backend_executed",
        "qutip_cuquantum_probe_executed",
        "carrier_program",
        "local_hilbert_space",
        "state_execution",
        "record_execution",
        "mcwf_mps_execution",
        "dynamics_artifact_reference_certification",
        "restricted_acceptance_policy",
        "claims_mcwf_mps_backend_execution",
        "claims_qt_mps_backend_execution",
        "claims_qutip_cuquantum_execution",
        "claims_production_scalable_backend",
        "claims_scalable_backend_completed",
        "claims_exact_joint_lindblad_generator",
        "claims_dense_channel_evidence",
        "claims_dem_decoder_semantics",
        "claims_axis2_source_timeline",
        "scored_quantity_policy",
        "epistemic_classes",
        "scope",
        "content_hash",
    }
)
_MCWF_CARRIER_STATE_EXECUTION_FIELDS = frozenset(
    {
        "executed",
        "reason",
        "evidence_schema",
        "evidence_content_hash",
        "representability",
        "mps_library",
        "array_backend",
        "unraveling_policy",
        "initial_levels",
        "finite_step_policy",
        "mps_truncation_ledger",
    }
)
_MCWF_CARRIER_RECORD_EXECUTION_FIELDS = frozenset(
    {
        "executed",
        "reason",
        "measurement_keys",
        "measurement_targets",
        "measurement_bases",
        "reset_after",
        "measurement_basis",
        "measurement_basis_semantics",
        "multilevel_measurement_policy",
        "measurement_records",
        "record_counts",
        "record_probabilities",
        "detector_records",
        "logical_observable_records",
        "trajectory_sampling",
        "jump_sampling",
        "claims_b8_artifact",
        "claims_decoder_integration",
    }
)
_MCWF_CARRIER_EXECUTION_SUMMARY_FIELDS = frozenset(
    {
        "schema",
        "content_hash",
        "representability",
        "backend_contract",
        "execution_status",
        "certification_status",
        "diagnostic_only",
        "passed",
        "mcwf_mps_backend_executed",
        "claims_exact_joint_lindblad_generator",
        "claims_dense_channel_evidence",
        "claims_production_scalable_backend",
        "dynamics_artifact_reference_certification",
    }
)
_MCWF_TRAJECTORY_SAMPLING_FIELDS = frozenset(
    {
        "mode",
        "trajectory_count",
        "rng_seed",
        "rng_seed_required_for_acceptance",
        "rng_seed_was_explicit",
        "rng_seed_default_policy",
        "rng_backend",
        "measurement_sampling_policy",
        "record_support_policy",
        "zero_frequency_records_emitted",
        "probability_semantics",
        "single_trajectory_density_claim",
        "comparison_outcome_is_metric",
    }
)
_MCWF_FINITE_STEP_POLICY_FIELDS = frozenset(
    {
        "name",
        "order",
        "microstep_count",
        "microstep_dt_policy",
        "hamiltonian_grouping_policy",
        "exact_summed_lindbladian_claim",
        "comparison_outcome_is_metric",
    }
)
_MCWF_UNCAPPED_TRUNCATION_LEDGER_FIELDS = frozenset(
    {
        "explicit_truncation_requested",
        "exact_bond_dimension_sufficient",
        "exact_bond_policy",
        "accepted_as_exact_bond_representation",
        "discarded_weight_ledger_complete",
        "discarded_weight_sum",
        "worst_cut_discarded_weight",
        "path_aggregated_local_discarded_fraction_sum",
        "path_aggregated_actual_discarded_weight_raw_sum",
        "path_aggregated_unitary_truncation_mass_loss_sum",
        "aggregation",
        "n_truncating_ops",
        "max_observed_bond",
        "ledger_scope",
        "epistemic_class",
    }
)
_MCWF_CAPPED_TRUNCATION_LEDGER_FIELDS = frozenset(
    {
        "explicit_truncation_requested",
        "max_bond",
        "exact_bond_dimension_sufficient",
        "exact_bond_policy",
        "accepted_as_exact_bond_representation",
        "discarded_weight_ledger_complete",
        "ledger_method",
        "actual_discarded_weight_raw_sum",
        "actual_discarded_weight_fraction_sum",
        "worst_actual_discarded_weight_fraction",
        "actual_split_count",
        "unitary_truncation_mass_loss_sum",
        "worst_unitary_truncation_mass_loss",
        "path_aggregated_local_discarded_fraction_sum",
        "path_aggregated_actual_discarded_weight_raw_sum",
        "path_aggregated_unitary_truncation_mass_loss_sum",
        "discarded_weight_sum",
        "worst_cut_discarded_weight",
        "discarded_weight_units",
        "compatibility_aliases",
        "not_a_global_error_bound",
        "aggregation",
        "n_truncating_ops",
        "n_tracked_two_site_ops",
        "max_observed_bond",
        "truncation_events",
        "ledger_scope",
        "epistemic_class",
    }
)
_MCWF_BLOCKED_POLICY_FIELDS = frozenset(
    {
        "schema",
        "policy_role",
        "execution_status",
        "certification_status",
        "diagnostic_only",
        "accepted_for_restricted_execution",
        "accepted_for_sampled_execution_evidence",
        "accepted_for_exact_dense_probability_evidence",
        "accepted_for_production_scalable_backend",
        "blocked_reason",
        "dynamics_artifact_reference_certification",
        "trajectory",
        "production_blockers",
        "comparison_outcome_is_metric",
        "epistemic_class",
    }
)
_MCWF_COMPLETED_POLICY_FIELDS = frozenset(
    {
        "schema",
        "policy_role",
        "execution_status",
        "certification_status",
        "diagnostic_only",
        "accepted_for_restricted_execution",
        "accepted_for_sampled_execution_evidence",
        "accepted_for_exact_dense_probability_evidence",
        "accepted_for_production_scalable_backend",
        "accepted_as_restricted_overcap_execution",
        "blocked_reason",
        "dynamics_artifact_reference_certification",
        "gross_strict_gate_split",
        "dense_jointL_record_certification",
        "trajectory",
        "finite_step",
        "mps_truncation",
        "probability",
        "production_blockers",
        "scored_quantity_policy",
        "comparison_outcome_is_metric",
        "epistemic_class",
    }
)
_MCWF_POLICY_GROSS_STRICT_FIELDS = frozenset(
    {
        "gross_gate_role",
        "strict_gate_role",
        "dense_passed_gross",
        "dense_passed_strict",
        "comparison_outcome_is_metric",
        "epistemic_class",
    }
)
_MCWF_POLICY_DENSE_CERTIFICATION_FIELDS = frozenset(
    {
        "executed",
        "passed",
        "passed_gross",
        "status",
        "comparison_object",
        "metric",
        "metric_convention",
        "value",
        "component_values",
        "gate",
        "gross_gate",
        "effective_gate_including_sampling_ci",
        "gross_effective_gate_including_sampling_ci",
        "gross_gate_ceiling",
        "sampling_finite_shot_halfwidth",
        "sampling_support_size",
        "sampling_ci_method",
        "sampling_confidence",
        "trajectory_count",
        "dense_evidence_schema",
        "dense_evidence_content_hash",
        "oracle",
        "oracle_role",
        "oracle_independent_of_carrier_grouping",
        "readout_model_independent",
        "comparison_outcome_is_metric",
        "metric_epistemic_class",
        "gate_epistemic_class",
        "reason",
    }
)
_MCWF_POLICY_TRAJECTORY_FIELDS = frozenset(
    {
        "mode",
        "trajectory_count",
        "rng_seed",
        "rng_seed_required_for_acceptance",
        "rng_seed_was_explicit",
        "accepted_as_empirical_record_evidence",
        "single_trajectory_density_claim",
        "comparison_outcome_is_metric",
        "epistemic_class",
    }
)
_MCWF_POLICY_FINITE_STEP_FIELDS = frozenset(
    {
        "exact_summed_lindbladian_claim",
        "accepted_as_error_bound",
        "comparison_outcome_is_metric",
        "epistemic_class",
    }
)
_MCWF_POLICY_TRUNCATION_FIELDS = frozenset(
    {
        "explicit_truncation_requested",
        "exact_bond_dimension_sufficient",
        "exact_bond_policy",
        "accepted_as_exact_bond_representation",
        "discarded_weight_ledger_complete",
        "discarded_weight_sum",
        "worst_cut_discarded_weight",
        "truncation_detected",
        "observed_lossless_finite_bond_execution",
        "gate",
        "candidate_gate_complete",
        "accepted_as_finite_bond_candidate",
        "accepted_as_production_error_bound",
        "comparison_outcome_is_metric",
        "epistemic_class",
    }
)
_MCWF_POLICY_PROBABILITY_FIELDS = frozenset(
    {
        "normalization_invariant",
        "normalization_invariant_is_finite_nonnegative_real",
        "normalization_invariant_gate",
        "role",
        "runtime_candidate_mass_residual",
        "runtime_candidate_mass_residual_budget",
        "runtime_candidate_mass_residual_is_finite_nonnegative",
        "runtime_candidate_mass_residual_within_budget",
        "runtime_candidate_mass_residual_required_for_restricted_acceptance",
        "comparison_outcome_is_metric",
        "epistemic_class",
    }
)
_QT_EXACT_TRAJECTORY_MODE = "exact_branch_enumeration"
_QT_SAMPLED_TRAJECTORY_MODE = "sampled_product_channel_trajectories"
# Conservative fraction of FREE VRAM the dense record probe's PROJECTED PEAK is allowed to occupy
# before the auto-router routes to the memory-bounded MCWF/MPS backend instead. 0.25 matches the
# window_channel register guard (_RHO_MEM_FRACTION) and leaves headroom for allocator fragmentation
# and autograd/transient buffers beyond the projection.
AXIS1_CARRIER_DENSE_VRAM_SAFETY_FRACTION = 0.25
# Transient multiplier on the resident branch-batch peak: the record path builds a torch.stack copy
# of the per-branch results plus per-branch project_qubit intermediates, so the instantaneous peak
# exceeds the resident (2^m, 2^n, 2^n) batch. 2x is a deliberate over-estimate (fails toward MCWF).
AXIS1_CARRIER_DENSE_RECORD_TRANSIENT_FACTOR = 2.0
AXIS1_CARRIER_ALLOWED_EXECUTION_BACKEND_CONTRACTS = frozenset(
    {
        AXIS1_CARRIER_EXECUTION_BACKEND_CONTRACT,
        AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT,
        AXIS1_CARRIER_QUTIP_RESTRICTED_EXECUTION_BACKEND_CONTRACT,
        AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT,
        AXIS1_CARRIER_AUTO_BACKEND_CONTRACT,
    }
)


def axis1_carrier_execution_manifest(
    schedule: SubstepSchedule,
    *,
    device: str = "cuda",
    instrument_spec: Axis1ReadoutResetInstrumentSpec | None = None,
    execution_backend_contract: str = AXIS1_CARRIER_EXECUTION_BACKEND_CONTRACT,
    execution_backend_options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute the carrier program where dense joint-L probe execution is valid.

    The default backend is not the scalable QT/MPS backend. It is a GPU-only
    execution seam that proves the carrier program can drive the already
    registered small-window joint-L state/record path, while over-cap rows remain
    explicit blockers unless the restricted qutip-cuquantum backend contract is
    requested.
    """

    backend = str(execution_backend_contract)
    backend_options = dict(execution_backend_options or {})
    if backend not in AXIS1_CARRIER_ALLOWED_EXECUTION_BACKEND_CONTRACTS:
        raise ValueError(f"unsupported Axis-1 carrier execution backend {backend!r}")
    if backend == AXIS1_CARRIER_AUTO_BACKEND_CONTRACT:
        return _axis1_auto_routed_execution_manifest(
            schedule,
            device=device,
            instrument_spec=instrument_spec,
            execution_backend_options=backend_options,
        )
    if backend == AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT:
        return _axis1_qt_mps_restricted_execution_manifest(
            schedule,
            device=device,
            instrument_spec=instrument_spec,
            execution_backend_options=backend_options,
        )
    if backend == AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT:
        return _axis1_mcwf_mps_execution_manifest(
            schedule,
            device=device,
            instrument_spec=instrument_spec,
            execution_backend_options=backend_options,
        )
    if backend_options:
        raise ValueError(
            "execution_backend_options are currently supported only for "
            f"{AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT!r} "
            f"or {AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT!r}"
        )
    if backend == AXIS1_CARRIER_QUTIP_RESTRICTED_EXECUTION_BACKEND_CONTRACT:
        return _axis1_qutip_cuquantum_restricted_execution_manifest(
            schedule,
            device=device,
            instrument_spec=instrument_spec,
        )

    dev = _require_cuda_device(device)
    _validate_schedule_for_axis1_channel_evidence(schedule)
    program = axis1_carrier_program_manifest(schedule)
    carrier_summary = _carrier_program_summary(program)
    base_payload: dict[str, Any] = {
        "schema": AXIS1_CARRIER_EXECUTION_SCHEMA,
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "representability": AXIS1_CARRIER_EXECUTION_REPRESENTABILITY,
        "execution_backend_contract": AXIS1_CARRIER_EXECUTION_BACKEND_CONTRACT,
        "gpu_required": True,
        "device": dev,
        "carrier_program": carrier_summary,
        "claims_dense_channel_evidence": False,
        "claims_dem_decoder_semantics": False,
        "claims_axis2_source_timeline": False,
        "claims_scalable_backend_completed": False,
        "scored_quantity_policy": (
            "no new scored quantity; nested state/record evidence keeps its existing "
            "METRICS.md references"
        ),
        "epistemic_classes": {
            "program_consumption": "a",
            "dense_jointL_probe_execution": "a/c",
            "overcap_blocker": "a",
            "scalable_backend_status": "a",
        },
    }
    if bool(program["requires_scalable_backend"]):
        payload = {
            **base_payload,
            "verdict": "fail",
            "passed": False,
            "blocked_reason": "requires_scalable_backend_extension",
            "dense_probe_executed": False,
            "state_execution": None,
            "record_execution": None,
            "scope": (
                "carrier program contains scalable_required rows; dense_jointL_probe "
                "will not approximate them with pairwise or sequential composition"
            ),
        }
        payload["content_hash"] = _stable_payload_hash(payload)
        return payload

    if int(schedule.num_qubits) > AXIS1_STATE_MAX_EXACT_QUBITS:
        payload = {
            **base_payload,
            "verdict": "fail",
            "passed": False,
            "blocked_reason": "dense_jointL_probe_qubit_cap_exceeded",
            "dense_probe_executed": False,
            "state_execution": None,
            "record_execution": None,
            "scope": (
                "dense_jointL_probe is exact-density small-N only; connect the "
                "scalable carrier backend before executing this schedule"
            ),
        }
        payload["content_hash"] = _stable_payload_hash(payload)
        return payload

    state = axis1_state_evolution_evidence_manifest(schedule, device=dev)
    record = (
        axis1_measurement_record_evidence_manifest(
            schedule,
            device=dev,
            instrument_spec=instrument_spec,
        )
        if _has_measurement_substep(schedule)
        else None
    )
    state_execution = _state_execution_summary(state)
    record_execution = _record_execution_summary(record)
    passed = bool(state.get("passed")) and (
        record is None or bool(record.get("passed"))
    )
    payload = {
        **base_payload,
        "verdict": "pass" if passed else "fail",
        "passed": passed,
        "blocked_reason": None,
        "dense_probe_executed": True,
        "state_execution": state_execution,
        "record_execution": record_execution,
        "scope": (
            "dense-checkable carrier execution probe only; no serialized channel "
            "payload, no DEM/decoder semantics, no Axis-2 source timeline, no "
            "scalable QT/MPS backend claim"
        ),
    }
    payload["content_hash"] = _streaming_stable_payload_hash(payload)
    return payload


def _preflight_mcwf_record_materialization(
    schedule: SubstepSchedule,
    *,
    device: str,
    execution_backend_options: dict[str, Any] | None,
    max_record_array_payload_bytes: int,
    max_record_support_cells: int = AXIS1_MCWF_MPS_RECORD_MAX_SUPPORT_CELLS,
) -> _Axis1McwfMpsRecordPreflight:
    """Reject impossible or over-budget output before CUDA execution."""

    normalized_device = normalize_mps_device(device)
    normalized_options = _validate_mcwf_mps_execution_options(
        dict(execution_backend_options or {})
    )
    expected_options = _mcwf_mps_expected_options(
        normalized_options,
        num_sites=int(schedule.num_qubits),
    )
    carrier_program = axis1_carrier_program_manifest(
        schedule,
        backend_contract=AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT,
    )
    layout = axis1_record_layout_from_schedule(schedule)
    if layout.measurement_width <= 0:
        raise ValueError("MCWF Record materialization requires measurement columns")
    if any(basis not in {"X", "Z"} for basis in layout.measurement_bases):
        raise ValueError("MCWF Record materialization supports only X/Z bases")
    detector_width = len(layout.detectors)
    observable_width = len(layout.observables)
    output_width = detector_width + observable_width
    if output_width <= 0:
        raise ValueError(
            "MCWF Record materialization requires at least one detector or observable"
        )
    materialization_limit = normalize_mps_index(
        max_record_array_payload_bytes,
        name="max_record_array_payload_bytes",
        minimum=1,
    )
    trajectory_count = int(expected_options["trajectory_count"])
    support_cell_limit = normalize_mps_index(
        max_record_support_cells,
        name="max_record_support_cells",
        minimum=1,
    )
    if layout.measurement_width >= trajectory_count.bit_length():
        support_upper_bound = trajectory_count
    else:
        support_upper_bound = 1 << layout.measurement_width
    layout_reference_cells = layout.measurement_width + sum(
        len(definition.columns)
        for definition in (*layout.detectors, *layout.observables)
    )
    estimated_record_support_cells = (
        support_upper_bound * (layout.measurement_width + output_width + 2)
        + layout_reference_cells
    )
    if estimated_record_support_cells > support_cell_limit:
        raise ValueError(
            "MCWF Record support-cell budget exceeded before execution: "
            f"required={estimated_record_support_cells}, limit={support_cell_limit}"
        )
    estimated_peak_bytes = (
        _MCWF_RECORD_ARRAY_PAYLOAD_BYTES_PER_OUTPUT_BIT
        * trajectory_count
        * output_width
    )
    if estimated_peak_bytes > materialization_limit:
        raise ValueError(
            "MCWF Record-array payload byte budget exceeded before execution: "
            f"required={estimated_peak_bytes}, limit={materialization_limit}"
        )
    if trajectory_count > int(np.iinfo(np.intp).max):
        raise ValueError("MCWF Record trajectory_count exceeds platform index range")
    return _Axis1McwfMpsRecordPreflight(
        source_kind=schedule.source_kind,
        source_hash=schedule.source_hash,
        schedule_representability=schedule.representability,
        num_qubits=int(schedule.num_qubits),
        device=normalized_device,
        execution_backend_options=normalized_options,
        expected_execution_options=expected_options,
        carrier_program=carrier_program,
        layout=layout,
        trajectory_count=trajectory_count,
        detector_width=detector_width,
        observable_width=observable_width,
        estimated_peak_record_array_payload_bytes=estimated_peak_bytes,
        max_record_array_payload_bytes=materialization_limit,
        estimated_record_support_upper_bound=support_upper_bound,
        estimated_record_support_cells=estimated_record_support_cells,
        max_record_support_cells=support_cell_limit,
    )


def axis1_mcwf_mps_record_batch(
    schedule: SubstepSchedule,
    *,
    device: str = "cuda",
    execution_backend_options: dict[str, Any] | None = None,
    max_record_array_payload_bytes: int = (
        AXIS1_MCWF_MPS_RECORD_MAX_ARRAY_PAYLOAD_BYTES
    ),
    max_record_support_cells: int = AXIS1_MCWF_MPS_RECORD_MAX_SUPPORT_CELLS,
) -> RecordBatch:
    """Execute MCWF Carrier once and materialize its authenticated histogram.

    Rows are repeated by their exact integer counts in canonical support order.
    This reconstructs an exchangeable shot batch without drawing a second
    sample; the original per-trajectory order was not retained by the child and
    is therefore explicitly unavailable.
    """

    preflight = _preflight_mcwf_record_materialization(
        schedule,
        device=device,
        execution_backend_options=execution_backend_options,
        max_record_array_payload_bytes=max_record_array_payload_bytes,
        max_record_support_cells=max_record_support_cells,
    )
    _, record_batch = _execute_mcwf_carrier_record_batch(
        schedule,
        preflight=preflight,
    )
    return record_batch


def write_axis1_mcwf_mps_record_samples(
    schedule: SubstepSchedule,
    out_dir: str | Path,
    *,
    device: str = "cuda",
    execution_backend_options: dict[str, Any] | None = None,
    max_record_array_payload_bytes: int = (
        AXIS1_MCWF_MPS_RECORD_MAX_ARRAY_PAYLOAD_BYTES
    ),
    max_record_support_cells: int = AXIS1_MCWF_MPS_RECORD_MAX_SUPPORT_CELLS,
) -> Axis1McwfMpsRecordSampleResult:
    """Write canonical MCWF detector/observable `.b8` products fail closed.

    The writer owns the `.b8` claim; the restricted Carrier child continues to
    claim no artifact emission. Validation and bounded RecordBatch construction
    finish before the output directory is touched.
    """

    root = Path(out_dir).absolute()
    _require_fresh_mcwf_record_output_directory(root)
    preflight = _preflight_mcwf_record_materialization(
        schedule,
        device=device,
        execution_backend_options=execution_backend_options,
        max_record_array_payload_bytes=max_record_array_payload_bytes,
        max_record_support_cells=max_record_support_cells,
    )
    publication_preflight = _preflight_mcwf_record_publication(
        root,
        device=preflight.device,
    )
    try:
        carrier, record_batch = _execute_mcwf_carrier_record_batch(
            schedule,
            preflight=preflight,
        )
        _validate_mcwf_record_publication_preflight(
            publication_preflight,
            device=preflight.device,
        )
        return _publish_mcwf_record_samples(
            root,
            carrier=carrier,
            record_batch=record_batch,
            preflight=preflight,
            publication_preflight=publication_preflight,
        )
    finally:
        os.close(publication_preflight.target_parent_fd)


def _execute_mcwf_carrier_record_batch(
    schedule: SubstepSchedule,
    *,
    preflight: _Axis1McwfMpsRecordPreflight,
) -> tuple[dict[str, Any], RecordBatch]:
    produced = _axis1_mcwf_mps_execution_manifest(
        schedule,
        device=preflight.device,
        instrument_spec=None,
        execution_backend_options=copy.deepcopy(
            preflight.execution_backend_options
        ),
        _return_record_binding=True,
    )
    if not isinstance(produced, tuple) or len(produced) != 2:
        raise TypeError("MCWF Record producer did not return a same-call binding")
    carrier, binding = produced
    record_batch = _materialize_mcwf_carrier_record_batch(
        carrier,
        preflight=preflight,
        binding=binding,
    )
    return carrier, record_batch


def _require_fresh_mcwf_record_output_directory(root: Path) -> None:
    if root.exists() or root.is_symlink():
        raise ValueError(
            "MCWF Record writer requires a fresh output directory: "
            f"{root}"
        )


def _mcwf_record_authoritative_environment_lock() -> Path:
    return Path(__file__).resolve().parents[3] / "core-environment-cu130.lock"


def _require_mcwf_record_environment_lock_sha256(value: object) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(
            "MCWF Record authoritative environment lock hash is invalid"
        )
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(
            "MCWF Record authoritative environment lock hash is invalid"
        ) from exc
    return value


def _preflight_mcwf_record_publication(
    root: Path,
    *,
    device: str,
) -> _Axis1McwfMpsRecordPublicationPreflight:
    target_parent = root.parent
    target_parent_device, target_parent_inode = (
        _mcwf_record_target_parent_identity(target_parent)
    )
    target_parent_fd = _open_mcwf_record_target_parent(
        target_parent,
        expected_identity=(target_parent_device, target_parent_inode),
    )
    try:
        environment_lock = _mcwf_record_authoritative_environment_lock()
        if not environment_lock.is_file():
            raise FileNotFoundError(
                "MCWF Record publication requires the authoritative environment lock: "
                f"{environment_lock}"
            )
        environment_lock_hash = _require_mcwf_record_environment_lock_sha256(
            file_sha256(environment_lock)
        )
        _probe_atomic_noreplace_publication(
            target_parent,
            parent_fd=target_parent_fd,
        )
        if _mcwf_record_target_parent_identity(target_parent) != (
            target_parent_device,
            target_parent_inode,
        ):
            raise RuntimeError(
                "MCWF Record target parent changed during publication preflight"
            )
        build_identity = _mcwf_record_build_identity()
        source_implementation = _mcwf_record_source_implementation_identity()
        environment_identity = _mcwf_record_environment_identity(
            environment_lock=environment_lock,
            environment_lock_hash=environment_lock_hash,
            device=device,
        )
        if _mcwf_record_target_parent_identity(target_parent) != (
            target_parent_device,
            target_parent_inode,
        ):
            raise RuntimeError(
                "MCWF Record target parent changed during identity preflight"
            )
        return _Axis1McwfMpsRecordPublicationPreflight(
            target_parent=target_parent,
            target_parent_fd=target_parent_fd,
            target_parent_device=target_parent_device,
            target_parent_inode=target_parent_inode,
            environment_lock_path=environment_lock,
            environment_lock_sha256=environment_lock_hash,
            build_identity=copy.deepcopy(build_identity),
            source_implementation=copy.deepcopy(source_implementation),
            environment_identity=copy.deepcopy(environment_identity),
        )
    except BaseException:
        os.close(target_parent_fd)
        raise


def _mcwf_record_target_parent_identity(parent: Path) -> tuple[int, int]:
    try:
        parent_stat = parent.stat()
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"MCWF Record target parent must already exist: {parent}"
        ) from exc
    if not stat.S_ISDIR(parent_stat.st_mode):
        raise NotADirectoryError(
            f"MCWF Record target parent is not a directory: {parent}"
        )
    return int(parent_stat.st_dev), int(parent_stat.st_ino)


def _open_mcwf_record_target_parent(
    parent: Path,
    *,
    expected_identity: tuple[int, int],
) -> int:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
    parent_fd = os.open(parent, flags)
    try:
        parent_stat = os.fstat(parent_fd)
        actual_identity = (int(parent_stat.st_dev), int(parent_stat.st_ino))
        if actual_identity != expected_identity:
            raise RuntimeError("MCWF Record target parent changed while opening dirfd")
        return parent_fd
    except BaseException:
        os.close(parent_fd)
        raise


def _validate_mcwf_record_publication_preflight(
    preflight: _Axis1McwfMpsRecordPublicationPreflight,
    *,
    device: str,
) -> None:
    try:
        sealed_parent_stat = os.fstat(preflight.target_parent_fd)
    except OSError as exc:
        raise RuntimeError("MCWF Record sealed target-parent dirfd is unavailable") from exc
    if (
        int(sealed_parent_stat.st_dev),
        int(sealed_parent_stat.st_ino),
    ) != (
        preflight.target_parent_device,
        preflight.target_parent_inode,
    ):
        raise RuntimeError("MCWF Record sealed target-parent dirfd identity changed")
    current_parent_identity = _mcwf_record_target_parent_identity(
        preflight.target_parent
    )
    if current_parent_identity != (
        preflight.target_parent_device,
        preflight.target_parent_inode,
    ):
        raise RuntimeError("MCWF Record target parent changed after preflight")

    current_environment_lock = _mcwf_record_authoritative_environment_lock()
    if current_environment_lock != preflight.environment_lock_path:
        raise RuntimeError("MCWF Record authoritative environment lock changed")
    if not current_environment_lock.is_file():
        raise RuntimeError("MCWF Record authoritative environment lock disappeared")
    _require_mcwf_record_environment_lock_sha256(
        preflight.environment_lock_sha256
    )
    current_environment_lock_hash = _require_mcwf_record_environment_lock_sha256(
        file_sha256(current_environment_lock)
    )
    if current_environment_lock_hash != preflight.environment_lock_sha256:
        raise RuntimeError("MCWF Record environment lock changed after preflight")

    if _mcwf_record_build_identity() != preflight.build_identity:
        raise RuntimeError("MCWF Record build identity changed after preflight")
    if (
        _mcwf_record_source_implementation_identity()
        != preflight.source_implementation
    ):
        raise RuntimeError(
            "MCWF Record source implementation changed after preflight"
        )
    current_environment_identity = _mcwf_record_environment_identity(
        environment_lock=current_environment_lock,
        environment_lock_hash=current_environment_lock_hash,
        device=device,
    )
    if (
        current_environment_identity.get("runtime")
        != preflight.environment_identity.get("runtime")
    ):
        raise RuntimeError("MCWF Record runtime identity changed after preflight")
    if current_environment_identity != preflight.environment_identity:
        raise RuntimeError("MCWF Record environment identity changed after preflight")


def _require_atomic_noreplace_publication():
    if platform.system() != "Linux":
        raise OSError(
            errno.ENOTSUP,
            "claim-bearing MCWF Record publication requires Linux renameat2",
        )
    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        raise OSError(
            errno.ENOTSUP,
            "claim-bearing MCWF Record publication requires renameat2",
        )
    renameat2.argtypes = (
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    )
    renameat2.restype = ctypes.c_int
    return renameat2


def _atomic_rename_directory_noreplace(
    source: str | Path,
    destination: str | Path,
    *,
    source_dir_fd: int = _AT_FDCWD,
    destination_dir_fd: int = _AT_FDCWD,
) -> None:
    renameat2 = _require_atomic_noreplace_publication()
    result = renameat2(
        source_dir_fd,
        os.fsencode(source),
        destination_dir_fd,
        os.fsencode(destination),
        _RENAME_NOREPLACE,
    )
    if result != 0:
        error_code = ctypes.get_errno()
        raise OSError(error_code, os.strerror(error_code), str(destination))


def _probe_atomic_noreplace_publication(
    parent: Path,
    *,
    parent_fd: int | None = None,
) -> None:
    """Exercise no-clobber rename semantics on the actual target filesystem."""

    _require_atomic_noreplace_publication()
    owns_parent_fd = parent_fd is None
    if parent_fd is None:
        expected_identity = _mcwf_record_target_parent_identity(parent)
        parent_fd = _open_mcwf_record_target_parent(
            parent,
            expected_identity=expected_identity,
        )
    source_name: str | None = None
    destination_name: str | None = None
    try:
        source_name = Path(
            tempfile.mkdtemp(
                prefix=".mcwf-noreplace-source-",
                dir=f"/proc/self/fd/{parent_fd}",
            )
        ).name
        destination_name = Path(
            tempfile.mkdtemp(
                prefix=".mcwf-noreplace-destination-",
                dir=f"/proc/self/fd/{parent_fd}",
            )
        ).name
        source_identity = _mcwf_record_directory_entry_identity(
            parent_fd,
            source_name,
        )
        destination_identity = _mcwf_record_directory_entry_identity(
            parent_fd,
            destination_name,
        )
        try:
            _atomic_rename_directory_noreplace(
                source_name,
                destination_name,
                source_dir_fd=parent_fd,
                destination_dir_fd=parent_fd,
            )
        except FileExistsError:
            pass
        except OSError as exc:
            raise OSError(
                exc.errno or errno.ENOTSUP,
                "target filesystem does not support renameat2 RENAME_NOREPLACE",
                str(parent),
            ) from exc
        else:
            raise OSError(
                errno.ENOTSUP,
                "target filesystem failed to preserve an existing no-replace destination",
                str(parent),
            )
        if (
            _mcwf_record_directory_entry_identity(parent_fd, source_name)
            != source_identity
            or _mcwf_record_directory_entry_identity(parent_fd, destination_name)
            != destination_identity
        ):
            raise OSError(
                errno.ENOTSUP,
                "target filesystem no-replace probe did not preserve both directory identities",
                str(parent),
            )

        os.rmdir(destination_name, dir_fd=parent_fd)
        try:
            _atomic_rename_directory_noreplace(
                source_name,
                destination_name,
                source_dir_fd=parent_fd,
                destination_dir_fd=parent_fd,
            )
        except OSError as exc:
            raise OSError(
                exc.errno or errno.ENOTSUP,
                "target filesystem does not support successful no-replace rename",
                str(parent),
            ) from exc
        if (
            _mcwf_record_directory_entry_exists(parent_fd, source_name)
            or _mcwf_record_directory_entry_identity(parent_fd, destination_name)
            != source_identity
        ):
            raise OSError(
                errno.ENOTSUP,
                "target filesystem no-replace probe produced an invalid rename result",
                str(parent),
            )
    finally:
        try:
            for probe_name in (source_name, destination_name):
                if probe_name is None:
                    continue
                try:
                    os.rmdir(probe_name, dir_fd=parent_fd)
                except FileNotFoundError:
                    pass
        finally:
            if owns_parent_fd:
                os.close(parent_fd)


def _mcwf_record_directory_entry_identity(
    parent_fd: int,
    name: str,
) -> tuple[int, int]:
    entry_stat = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    return int(entry_stat.st_dev), int(entry_stat.st_ino)


def _mcwf_record_directory_entry_exists(parent_fd: int, name: str) -> bool:
    try:
        os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return False
    return True


def _publish_mcwf_record_samples(
    root: Path,
    *,
    carrier: dict[str, Any],
    record_batch: RecordBatch,
    preflight: _Axis1McwfMpsRecordPreflight,
    publication_preflight: _Axis1McwfMpsRecordPublicationPreflight,
) -> Axis1McwfMpsRecordSampleResult:
    """Publish a complete artifact directory with one atomic rename."""

    if root.parent != publication_preflight.target_parent:
        raise ValueError("MCWF Record publication preflight targets another parent")
    _require_fresh_mcwf_record_output_directory(root)
    stage = _create_mcwf_record_stage(
        publication_preflight.target_parent_fd,
        output_name=root.name,
    )
    published = False
    try:
        staged_detection_events = stage.path / "detection_events.b8"
        staged_obs_flips_actual = stage.path / "obs_flips_actual.b8"
        staged_carrier_evidence = (
            stage.path / _MCWF_RECORD_CARRIER_EVIDENCE_FILENAME
        )
        staged_carrier_program = (
            stage.path / _MCWF_RECORD_CARRIER_PROGRAM_FILENAME
        )
        staged_summary = stage.path / _MCWF_RECORD_SAMPLE_SUMMARY_FILENAME
        det_path = write_b8_optional(staged_detection_events, record_batch.det)
        obs_path = write_b8_optional(staged_obs_flips_actual, record_batch.obs)
        _require_mcwf_record_b8_artifact_presence(
            det_path,
            expected_path=staged_detection_events,
            bit_width=int(record_batch.det.shape[1]),
            label="detector",
        )
        _require_mcwf_record_b8_artifact_presence(
            obs_path,
            expected_path=staged_obs_flips_actual,
            bit_width=int(record_batch.obs.shape[1]),
            label="observable",
        )
        for path in (det_path, obs_path):
            if path is not None:
                _fsync_required_mcwf_record_artifact(stage.fd, path.name)
        _write_canonical_json_streaming(
            staged_carrier_program,
            preflight.carrier_program,
        )
        _fsync_required_mcwf_record_artifact(
            stage.fd,
            staged_carrier_program.name,
        )
        _write_canonical_json_streaming(staged_carrier_evidence, carrier)
        _fsync_required_mcwf_record_artifact(
            stage.fd,
            staged_carrier_evidence.name,
        )
        artifact_seals = {
            staged_carrier_program.name: _seal_required_mcwf_record_artifact(
                stage.fd,
                staged_carrier_program.name,
                expected_sha256=_canonical_json_payload_sha256(
                    preflight.carrier_program
                ),
            ),
            staged_carrier_evidence.name: _seal_required_mcwf_record_artifact(
                stage.fd,
                staged_carrier_evidence.name,
                expected_sha256=_canonical_json_payload_sha256(carrier),
            ),
        }
        if det_path is not None:
            artifact_seals[det_path.name] = _seal_required_mcwf_record_artifact(
                stage.fd,
                det_path.name,
                expected_sha256=_mcwf_record_expected_b8_sha256(record_batch.det),
            )
        if obs_path is not None:
            artifact_seals[obs_path.name] = _seal_required_mcwf_record_artifact(
                stage.fd,
                obs_path.name,
                expected_sha256=_mcwf_record_expected_b8_sha256(record_batch.obs),
            )
        sample_manifest = _mcwf_record_sample_manifest(
            carrier,
            record_batch,
            detection_events=det_path,
            obs_flips_actual=obs_path,
            carrier_evidence=staged_carrier_evidence,
            carrier_program_evidence=staged_carrier_program,
            artifact_seals=artifact_seals,
            preflight=preflight,
            publication_preflight=publication_preflight,
        )
        _validate_child_content_hash_streaming(
            sample_manifest,
            context="MCWF Record sample manifest",
        )
        _write_canonical_json_streaming(staged_summary, sample_manifest)
        _fsync_required_mcwf_record_artifact(stage.fd, staged_summary.name)
        publication_artifact_seals = dict(artifact_seals)
        publication_artifact_seals[staged_summary.name] = (
            _seal_required_mcwf_record_artifact(
                stage.fd,
                staged_summary.name,
                expected_sha256=_canonical_json_payload_sha256(sample_manifest),
            )
        )
        _fsync_directory(stage.path)
        _validate_mcwf_record_staged_artifact_set(
            stage.fd,
            publication_artifact_seals,
        )
        _validate_mcwf_record_publication_preflight(
            publication_preflight,
            device=preflight.device,
        )
        _require_fresh_mcwf_record_output_directory(root)
        _validate_mcwf_record_staged_artifact_set(
            stage.fd,
            publication_artifact_seals,
        )
        _validate_mcwf_record_publication_preflight(
            publication_preflight,
            device=preflight.device,
        )
        _validate_mcwf_record_staged_artifact_metadata(
            stage.fd,
            publication_artifact_seals,
        )
        try:
            _atomic_rename_directory_noreplace(
                stage.name,
                root.name,
                source_dir_fd=publication_preflight.target_parent_fd,
                destination_dir_fd=publication_preflight.target_parent_fd,
            )
        except BaseException:
            published = _mcwf_record_directory_entry_matches_identity(
                publication_preflight.target_parent_fd,
                root.name,
                expected_identity=(stage.device, stage.inode),
            )
            raise
        if not _mcwf_record_directory_entry_matches_identity(
            publication_preflight.target_parent_fd,
            root.name,
            expected_identity=(stage.device, stage.inode),
        ):
            raise RuntimeError(
                "MCWF Record published directory identity does not match sealed stage"
            )
        published = True
        _validate_mcwf_record_staged_artifact_set(
            stage.fd,
            publication_artifact_seals,
        )
        _fsync_directory_fd(publication_preflight.target_parent_fd)
        _require_mcwf_record_published_directory_identity(
            publication_preflight.target_parent_fd,
            root.name,
            expected_identity=(stage.device, stage.inode),
        )
        _validate_mcwf_record_staged_artifact_set(
            stage.fd,
            publication_artifact_seals,
        )
        _validate_mcwf_record_publication_preflight(
            publication_preflight,
            device=preflight.device,
        )
        _validate_mcwf_record_staged_artifact_metadata(
            stage.fd,
            publication_artifact_seals,
        )
        _require_mcwf_record_published_directory_identity(
            publication_preflight.target_parent_fd,
            root.name,
            expected_identity=(stage.device, stage.inode),
        )
        _require_mcwf_record_return_parent_identity(publication_preflight)
    finally:
        if published:
            os.close(stage.fd)
        else:
            _remove_unpublished_mcwf_record_stage(
                stage,
                parent_fd=publication_preflight.target_parent_fd,
            )

    detection_events = (
        root / staged_detection_events.name if det_path is not None else None
    )
    obs_flips_actual = (
        root / staged_obs_flips_actual.name if obs_path is not None else None
    )
    carrier_evidence = root / staged_carrier_evidence.name
    carrier_program_evidence = root / staged_carrier_program.name
    sample_summary = root / staged_summary.name
    return Axis1McwfMpsRecordSampleResult(
        out_dir=root,
        detection_events=detection_events,
        obs_flips_actual=obs_flips_actual,
        carrier_evidence=carrier_evidence,
        carrier_program_evidence=carrier_program_evidence,
        sample_summary=sample_summary,
        sample_manifest=sample_manifest,
        record_batch=record_batch,
    )


def _create_mcwf_record_stage(
    parent_fd: int,
    *,
    output_name: str,
) -> _Axis1McwfMpsRecordStage:
    stage_name = Path(
        tempfile.mkdtemp(
            prefix=f".{output_name}.tmp-",
            dir=f"/proc/self/fd/{parent_fd}",
        )
    ).name
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        stage_fd = os.open(stage_name, flags, dir_fd=parent_fd)
    except BaseException:
        os.rmdir(stage_name, dir_fd=parent_fd)
        raise
    try:
        stage_stat = os.fstat(stage_fd)
        stage_identity = (int(stage_stat.st_dev), int(stage_stat.st_ino))
        if (
            _mcwf_record_directory_entry_identity(parent_fd, stage_name)
            != stage_identity
        ):
            raise RuntimeError("MCWF Record staging directory changed while opening")
        return _Axis1McwfMpsRecordStage(
            name=stage_name,
            fd=stage_fd,
            path=Path(f"/proc/self/fd/{stage_fd}"),
            device=stage_identity[0],
            inode=stage_identity[1],
        )
    except BaseException:
        os.close(stage_fd)
        try:
            os.rmdir(stage_name, dir_fd=parent_fd)
        except OSError:
            pass
        raise


def _remove_unpublished_mcwf_record_stage(
    stage: _Axis1McwfMpsRecordStage,
    *,
    parent_fd: int,
) -> None:
    owned_stage_entry = False
    try:
        owned_stage_entry = _mcwf_record_directory_entry_matches_identity(
            parent_fd,
            stage.name,
            expected_identity=(stage.device, stage.inode),
        )
        if owned_stage_entry:
            try:
                child_names = os.listdir(stage.fd)
            except OSError:
                child_names = []
            for child_name in child_names:
                try:
                    os.unlink(child_name, dir_fd=stage.fd)
                except OSError:
                    pass
    finally:
        os.close(stage.fd)
    if not owned_stage_entry:
        return
    try:
        if _mcwf_record_directory_entry_identity(parent_fd, stage.name) != (
            stage.device,
            stage.inode,
        ):
            return
        os.rmdir(stage.name, dir_fd=parent_fd)
    except OSError:
        pass


def _mcwf_record_directory_entry_matches_identity(
    parent_fd: int,
    name: str,
    *,
    expected_identity: tuple[int, int],
) -> bool:
    try:
        return (
            _mcwf_record_directory_entry_identity(parent_fd, name)
            == expected_identity
        )
    except FileNotFoundError:
        return False


def _fsync_directory_fd(directory_fd: int) -> None:
    os.fsync(directory_fd)


def _require_mcwf_record_published_directory_identity(
    parent_fd: int,
    output_name: str,
    *,
    expected_identity: tuple[int, int],
) -> None:
    try:
        matches_identity = _mcwf_record_directory_entry_matches_identity(
            parent_fd,
            output_name,
            expected_identity=expected_identity,
        )
    except OSError as exc:
        raise RuntimeError(
            "MCWF Record published directory identity changed after parent fsync"
        ) from exc
    if not matches_identity:
        raise RuntimeError(
            "MCWF Record published directory identity changed after parent fsync"
        )


def _require_mcwf_record_return_parent_identity(
    preflight: _Axis1McwfMpsRecordPublicationPreflight,
) -> None:
    try:
        current_identity = _mcwf_record_target_parent_identity(
            preflight.target_parent
        )
    except OSError as exc:
        raise RuntimeError(
            "MCWF Record target parent changed after atomic publication"
        ) from exc
    if current_identity != (
        preflight.target_parent_device,
        preflight.target_parent_inode,
    ):
        raise RuntimeError("MCWF Record target parent changed after atomic publication")


def _write_canonical_json_streaming(path: Path, payload: dict[str, Any]) -> None:
    encoder = json.JSONEncoder(
        indent=2,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
    )
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for chunk in encoder.iterencode(payload):
            stream.write(chunk)
        stream.write("\n")


def _require_mcwf_record_b8_artifact_presence(
    path: Path | None,
    *,
    expected_path: Path,
    bit_width: int,
    label: str,
) -> None:
    expected_present = bit_width > 0
    if expected_present and path != expected_path:
        raise RuntimeError(
            f"MCWF Record artifact presence does not match {label} width"
        )
    if not expected_present and path is not None:
        raise RuntimeError(
            f"MCWF Record artifact presence does not match {label} width"
        )


def _open_required_mcwf_record_artifact(stage_fd: int, name: str) -> int:
    if not isinstance(name, str) or not name or Path(name).name != name:
        raise RuntimeError("MCWF Record required staged artifact name is invalid")
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise RuntimeError("MCWF Record required staged artifact no-follow is unavailable")
    flags = (
        os.O_RDONLY
        | nofollow
        | getattr(os, "O_NONBLOCK", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        return os.open(name, flags, dir_fd=stage_fd)
    except OSError as exc:
        raise RuntimeError(
            f"MCWF Record required staged artifact is unavailable: {name}"
        ) from exc


def _fsync_required_mcwf_record_artifact(stage_fd: int, name: str) -> None:
    artifact_fd = _open_required_mcwf_record_artifact(stage_fd, name)
    try:
        artifact_stat = os.fstat(artifact_fd)
        if not stat.S_ISREG(artifact_stat.st_mode):
            raise RuntimeError(
                f"MCWF Record required staged artifact is not regular: {name}"
            )
        os.fsync(artifact_fd)
    finally:
        os.close(artifact_fd)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _canonical_json_payload_sha256(payload: dict[str, Any]) -> str:
    encoder = json.JSONEncoder(
        indent=2,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
    )
    digest = hashlib.sha256()
    for chunk in encoder.iterencode(payload):
        digest.update(chunk.encode("utf-8"))
    digest.update(b"\n")
    return digest.hexdigest()


def _mcwf_record_expected_b8_sha256(records: np.ndarray) -> str:
    array = np.asarray(records)
    if array.ndim != 2 or int(array.shape[1]) <= 0:
        raise RuntimeError("MCWF Record required staged .b8 source is invalid")
    digest = hashlib.sha256()
    row_width = int(array.shape[1])
    rows_per_chunk = max(1, 1_048_576 // row_width)
    for start in range(0, int(array.shape[0]), rows_per_chunk):
        chunk = array[start : start + rows_per_chunk]
        if not bool(np.logical_or(chunk == 0, chunk == 1).all()):
            raise RuntimeError("MCWF Record required staged .b8 source is nonbinary")
        packed = np.packbits(
            chunk.astype(np.uint8, copy=False),
            axis=1,
            bitorder="little",
        )
        digest.update(np.ascontiguousarray(packed).tobytes())
    return digest.hexdigest()


def _seal_required_mcwf_record_artifact(
    stage_fd: int,
    name: str,
    *,
    expected_sha256: str,
) -> _Axis1McwfMpsRecordArtifactSeal:
    _require_mcwf_record_artifact_sha256(expected_sha256)
    artifact_fd = _open_required_mcwf_record_artifact(stage_fd, name)
    try:
        before = os.fstat(artifact_fd)
        if not stat.S_ISREG(before.st_mode):
            raise RuntimeError(
                f"MCWF Record required staged artifact is not regular: {name}"
            )
        digest = hashlib.sha256()
        while True:
            chunk = os.read(artifact_fd, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
        os.fsync(artifact_fd)
        after = os.fstat(artifact_fd)
    finally:
        os.close(artifact_fd)
    before_version = (
        int(before.st_dev),
        int(before.st_ino),
        int(before.st_mode),
        int(before.st_size),
        int(before.st_mtime_ns),
        int(before.st_ctime_ns),
    )
    after_version = (
        int(after.st_dev),
        int(after.st_ino),
        int(after.st_mode),
        int(after.st_size),
        int(after.st_mtime_ns),
        int(after.st_ctime_ns),
    )
    if after_version != before_version:
        raise RuntimeError(
            f"MCWF Record required staged artifact changed while hashing: {name}"
        )
    sha256 = digest.hexdigest()
    _require_mcwf_record_artifact_sha256(sha256)
    if sha256 != expected_sha256:
        raise RuntimeError(
            f"MCWF Record required staged artifact content changed: {name}"
        )
    return _Axis1McwfMpsRecordArtifactSeal(
        name=name,
        device=int(after.st_dev),
        inode=int(after.st_ino),
        mode=int(after.st_mode),
        size_bytes=int(after.st_size),
        mtime_ns=int(after.st_mtime_ns),
        ctime_ns=int(after.st_ctime_ns),
        sha256=sha256,
    )


def _require_mcwf_record_artifact_sha256(value: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise RuntimeError("MCWF Record required staged artifact SHA-256 is invalid")
    try:
        int(value, 16)
    except ValueError as exc:
        raise RuntimeError(
            "MCWF Record required staged artifact SHA-256 is invalid"
        ) from exc


def _validate_mcwf_record_staged_artifact_set(
    stage_fd: int,
    expected: dict[str, _Axis1McwfMpsRecordArtifactSeal],
) -> None:
    directory_version_before = _validate_mcwf_record_staged_artifact_metadata(
        stage_fd,
        expected,
    )
    for name, expected_seal in expected.items():
        try:
            observed_seal = _seal_required_mcwf_record_artifact(
                stage_fd,
                name,
                expected_sha256=expected_seal.sha256,
            )
        except RuntimeError as exc:
            raise RuntimeError(
                f"MCWF Record staged artifact set revalidation failed: {name}"
            ) from exc
        if observed_seal != expected_seal:
            raise RuntimeError(
                f"MCWF Record staged artifact set identity changed: {name}"
            )
    directory_version_after = _validate_mcwf_record_staged_artifact_metadata(
        stage_fd,
        expected,
    )
    if directory_version_after != directory_version_before:
        raise RuntimeError("MCWF Record staged artifact directory changed")


def _validate_mcwf_record_staged_artifact_metadata(
    stage_fd: int,
    expected: dict[str, _Axis1McwfMpsRecordArtifactSeal],
) -> tuple[int, int, int, int, int, int]:
    directory_version_before = _mcwf_record_staged_directory_version(stage_fd)
    try:
        observed_names = os.listdir(stage_fd)
    except OSError as exc:
        raise RuntimeError("MCWF Record staged artifact set is unavailable") from exc
    if set(observed_names) != set(expected):
        raise RuntimeError("MCWF Record staged artifact set is not exact")
    for name, expected_seal in expected.items():
        try:
            entry_stat = os.stat(
                name,
                dir_fd=stage_fd,
                follow_symlinks=False,
            )
        except OSError as exc:
            raise RuntimeError(
                f"MCWF Record staged artifact set metadata is unavailable: {name}"
            ) from exc
        if not _mcwf_record_artifact_seal_matches_stat(expected_seal, entry_stat):
            raise RuntimeError(
                f"MCWF Record staged artifact set identity changed: {name}"
            )
    try:
        final_names = os.listdir(stage_fd)
    except OSError as exc:
        raise RuntimeError("MCWF Record staged artifact set is unavailable") from exc
    if set(final_names) != set(expected):
        raise RuntimeError("MCWF Record staged artifact set is not exact")
    for name, expected_seal in expected.items():
        try:
            final_stat = os.stat(
                name,
                dir_fd=stage_fd,
                follow_symlinks=False,
            )
        except OSError as exc:
            raise RuntimeError(
                f"MCWF Record staged artifact set metadata is unavailable: {name}"
            ) from exc
        if not _mcwf_record_artifact_seal_matches_stat(expected_seal, final_stat):
            raise RuntimeError(
                f"MCWF Record staged artifact set identity changed: {name}"
            )
    directory_version_after = _mcwf_record_staged_directory_version(stage_fd)
    if directory_version_after != directory_version_before:
        raise RuntimeError("MCWF Record staged artifact directory changed")
    return directory_version_after


def _mcwf_record_artifact_seal_matches_stat(
    seal: _Axis1McwfMpsRecordArtifactSeal,
    entry_stat: os.stat_result,
) -> bool:
    return (
        stat.S_ISREG(entry_stat.st_mode)
        and int(entry_stat.st_dev) == seal.device
        and int(entry_stat.st_ino) == seal.inode
        and int(entry_stat.st_mode) == seal.mode
        and int(entry_stat.st_size) == seal.size_bytes
        and int(entry_stat.st_mtime_ns) == seal.mtime_ns
        and int(entry_stat.st_ctime_ns) == seal.ctime_ns
    )


def _mcwf_record_staged_directory_version(
    stage_fd: int,
) -> tuple[int, int, int, int, int, int]:
    try:
        directory_stat = os.fstat(stage_fd)
    except OSError as exc:
        raise RuntimeError("MCWF Record staged artifact directory is unavailable") from exc
    if not stat.S_ISDIR(directory_stat.st_mode):
        raise RuntimeError("MCWF Record staged artifact directory is not a directory")
    return (
        int(directory_stat.st_dev),
        int(directory_stat.st_ino),
        int(directory_stat.st_mode),
        int(directory_stat.st_size),
        int(directory_stat.st_mtime_ns),
        int(directory_stat.st_ctime_ns),
    )


def _materialize_mcwf_carrier_record_batch(
    carrier: dict[str, Any],
    *,
    preflight: _Axis1McwfMpsRecordPreflight,
    binding: _Axis1McwfMpsRecordBinding,
) -> RecordBatch:
    """Authenticate and expand one Carrier histogram without resampling."""

    if type(carrier) is not dict:
        raise TypeError("MCWF Record materialization requires an exact Carrier mapping")
    if type(preflight) is not _Axis1McwfMpsRecordPreflight:
        raise TypeError("MCWF Record materialization requires a sealed preflight")
    if type(binding) is not _Axis1McwfMpsRecordBinding:
        raise TypeError("MCWF Record materialization requires a same-call binding")
    _validate_child_content_hash_streaming(
        carrier,
        context="MCWF Record materialization Carrier",
    )
    _require_exact_summary_fields(
        carrier,
        _MCWF_CARRIER_CHILD_FIELDS,
        context="MCWF Record materialization Carrier",
    )
    _reject_auto_routed_evaluator_truth(
        carrier,
        path="MCWF Record materialization Carrier",
    )
    if carrier["content_hash"] != binding.carrier_content_hash:
        raise ValueError(
            "MCWF Record materialization Carrier content changed after binding"
        )
    expected_identity = {
        "schema": AXIS1_CARRIER_EXECUTION_SCHEMA,
        "source_kind": preflight.source_kind,
        "source_hash": preflight.source_hash,
        "schedule_representability": preflight.schedule_representability,
        "representability": AXIS1_CARRIER_MCWF_MPS_EXECUTION_REPRESENTABILITY,
        "execution_backend_contract": (
            AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
        ),
        "device": preflight.device,
    }
    for field, expected_value in expected_identity.items():
        if carrier.get(field) != expected_value:
            raise ValueError(
                f"MCWF Record materialization Carrier {field} must match the request"
            )
    actual_options = carrier.get("execution_backend_options")
    if type(actual_options) is not dict:
        raise TypeError(
            "MCWF Record materialization Carrier options must be an exact mapping"
        )
    if _stable_payload_hash({"options": actual_options}) != _stable_payload_hash(
        {"options": _jsonable(preflight.execution_backend_options)}
    ):
        raise ValueError(
            "MCWF Record materialization Carrier options must match the request"
        )
    expected_program_summary = _restricted_mps_program_summary(
        preflight.carrier_program
    )
    actual_program_summary = carrier.get("carrier_program")
    if (
        type(actual_program_summary) is not dict
        or actual_program_summary != expected_program_summary
    ):
        raise ValueError(
            "MCWF Record materialization Carrier program must match the sealed input"
        )
    passed = _require_manifest_bool(
        carrier,
        "passed",
        context="MCWF Record materialization Carrier",
    )
    verdict = _require_manifest_text(
        carrier,
        "verdict",
        context="MCWF Record materialization Carrier",
    )
    execution_status = _require_manifest_text(
        carrier,
        "execution_status",
        context="MCWF Record materialization Carrier",
    )
    certification_status = _require_manifest_text(
        carrier,
        "certification_status",
        context="MCWF Record materialization Carrier",
    )
    diagnostic_only = _require_manifest_bool(
        carrier,
        "diagnostic_only",
        context="MCWF Record materialization Carrier",
    )
    backend_executed = _require_manifest_bool(
        carrier,
        "mcwf_mps_backend_executed",
        context="MCWF Record materialization Carrier",
    )
    _validate_restricted_child_state_machine(
        passed=passed,
        child_verdict=verdict,
        backend_executed=backend_executed,
        execution_status=execution_status,
        certification_status=certification_status,
        diagnostic_only=diagnostic_only,
        blocked_reason=carrier.get("blocked_reason"),
        context="MCWF Record materialization Carrier",
    )
    if not (
        passed
        and backend_executed
        and execution_status == "completed"
        and certification_status == "accepted"
        and not diagnostic_only
        and carrier.get("blocked_reason") is None
    ):
        raise ValueError(
            "MCWF Record materialization requires accepted completed evidence"
        )

    record_execution = carrier.get("record_execution")
    if not isinstance(record_execution, dict):
        raise TypeError("MCWF Record materialization record_execution must be a mapping")
    _require_exact_summary_fields(
        record_execution,
        _MCWF_CARRIER_RECORD_EXECUTION_FIELDS,
        context="MCWF Record materialization record_execution",
    )
    if _streaming_stable_payload_hash({"record_execution": record_execution}) != (
        binding.record_execution_content_hash
    ):
        raise ValueError(
            "MCWF Record materialization Record law does not match its same-call binding"
        )
    if not _require_manifest_bool(
        record_execution,
        "executed",
        context="MCWF Record materialization record_execution",
    ):
        raise ValueError(
            "MCWF Record materialization requires a schedule with measurement Records"
        )
    for field in ("claims_b8_artifact", "claims_decoder_integration"):
        if _require_manifest_bool(
            record_execution,
            field,
            context="MCWF Record materialization record_execution",
        ):
            raise ValueError(
                f"MCWF Carrier child must not pre-claim output ownership via {field}"
            )

    policy = carrier.get("restricted_acceptance_policy")
    direct = carrier.get("mcwf_mps_execution")
    if not isinstance(policy, dict) or not isinstance(direct, dict):
        raise TypeError(
            "MCWF Record materialization requires policy and direct summaries"
        )
    if _streaming_stable_payload_hash({"policy": policy}) != (
        binding.restricted_acceptance_policy_content_hash
    ):
        raise ValueError(
            "MCWF Record materialization policy does not match its same-call binding"
        )
    accepted = _require_manifest_bool(
        policy,
        "accepted_for_restricted_execution",
        context="MCWF Record materialization policy",
    )
    if accepted is not True:
        raise ValueError(
            "MCWF Record materialization requires accepted restricted evidence"
        )
    direct_schema = _require_manifest_text(
        direct,
        "schema",
        context="MCWF Record materialization direct summary",
    )
    if direct_schema != _RESTRICTED_EXECUTION_SCHEMAS["mcwf"]:
        raise ValueError("MCWF Record materialization direct schema is not registered")
    direct_hash = _require_manifest_text(
        direct,
        "content_hash",
        context="MCWF Record materialization direct summary",
    )
    if direct_hash != binding.direct_content_hash:
        raise ValueError(
            "MCWF Record materialization direct hash does not match its same-call binding"
        )
    if len(direct_hash) != 64 or any(
        character not in "0123456789abcdef" for character in direct_hash
    ):
        raise ValueError("MCWF Record materialization direct hash is invalid")
    direct_mirrors = {
        "execution_status": execution_status,
        "certification_status": certification_status,
        "diagnostic_only": diagnostic_only,
        "passed": True,
        "mcwf_mps_backend_executed": True,
    }
    for field, expected_value in direct_mirrors.items():
        if direct.get(field) != expected_value or type(direct.get(field)) is not type(
            expected_value
        ):
            raise ValueError(
                f"MCWF Record materialization direct {field} must mirror Carrier"
            )

    measurement_records = _require_exact_binary_record_matrix(
        record_execution.get("measurement_records"),
        field="measurement_records",
        context="MCWF Record materialization",
    )
    layout = preflight.layout
    expected_metadata = {
        "measurement_keys": list(layout.measurement_keys),
        "measurement_targets": list(layout.measurement_targets),
        "measurement_bases": list(layout.measurement_bases),
        "reset_after": list(layout.reset_after),
    }
    for field, expected_value in expected_metadata.items():
        actual_value = record_execution.get(field)
        if type(actual_value) is not list or actual_value != expected_value:
            raise ValueError(
                f"MCWF Record materialization {field} must match the sealed layout"
            )
    expected_basis_summary = (
        "X"
        if all(basis == "X" for basis in layout.measurement_bases)
        else (
            "Z"
            if all(basis == "Z" for basis in layout.measurement_bases)
            else "mixed_pauli"
        )
    )
    if record_execution.get("measurement_basis") != expected_basis_summary:
        raise ValueError(
            "MCWF Record materialization measurement_basis must summarize the layout"
        )
    if record_execution.get("measurement_basis_semantics") != (
        _MCWF_MEASUREMENT_BASIS_SEMANTICS
    ):
        raise ValueError(
            "MCWF Record materialization measurement semantics are not registered"
        )
    detector_rows = _require_exact_binary_record_matrix(
        record_execution.get("detector_records"),
        field="detector_records",
        context="MCWF Record materialization",
    )
    observable_rows = _require_exact_binary_record_matrix(
        record_execution.get("logical_observable_records"),
        field="logical_observable_records",
        context="MCWF Record materialization",
    )
    _validate_mcwf_record_support_projection(
        layout,
        measurement_records=measurement_records,
        detector_rows=detector_rows,
        observable_rows=observable_rows,
    )

    counts = record_execution.get("record_counts")
    probabilities = record_execution.get("record_probabilities")
    sampling = record_execution.get("trajectory_sampling")
    if type(counts) is not list or type(probabilities) is not list:
        raise TypeError("MCWF Record counts and probabilities must be exact lists")
    if not isinstance(sampling, dict):
        raise TypeError("MCWF Record trajectory_sampling must be a mapping")
    trajectory_count = sampling.get("trajectory_count")
    if type(trajectory_count) is not int or trajectory_count <= 0:
        raise ValueError("MCWF Record trajectory_count must be a positive exact integer")
    if trajectory_count != preflight.trajectory_count:
        raise ValueError("MCWF Record trajectory_count must match the request")
    if sampling.get("mode") != _MCWF_SAMPLED_TRAJECTORY_MODE:
        raise ValueError("MCWF Record trajectory mode is not registered")
    expected_seed = preflight.expected_execution_options["rng_seed"]
    if expected_seed is None:
        expected_seed = 0
    if sampling.get("rng_seed") != expected_seed or type(
        sampling.get("rng_seed")
    ) is not int:
        raise ValueError("MCWF Record rng_seed must match the executed request")
    if not (
        len(measurement_records)
        == len(detector_rows)
        == len(observable_rows)
        == len(counts)
        == len(probabilities)
    ):
        raise ValueError("MCWF Record support rows, counts, and probabilities must align")
    for index, (count, probability) in enumerate(
        zip(counts, probabilities, strict=True)
    ):
        if type(count) is not int or count <= 0:
            raise ValueError(f"record_counts[{index}] must be a positive exact integer")
        if (
            isinstance(probability, bool)
            or not isinstance(probability, Real)
            or float(probability) < 0.0
        ):
            raise ValueError(f"record_probabilities[{index}] is invalid")
        if abs(float(probability) - count / trajectory_count) > NUMERICAL_ZERO:
            raise ValueError("MCWF Record probabilities must equal counts / trajectories")
    if sum(counts) != trajectory_count:
        raise ValueError("MCWF Record counts must sum to trajectory_count")
    if abs(math.fsum(float(value) for value in probabilities) - 1.0) > NUMERICAL_ZERO:
        raise ValueError("MCWF Record probabilities must sum to one")

    detector_width = preflight.detector_width
    observable_width = preflight.observable_width
    detector_samples = np.empty(
        (trajectory_count, detector_width),
        dtype=np.uint8,
    )
    observable_samples = np.empty(
        (trajectory_count, observable_width),
        dtype=np.uint8,
    )
    cursor = 0
    for detector_row, observable_row, count in zip(
        detector_rows,
        observable_rows,
        counts,
        strict=True,
    ):
        stop = cursor + count
        if detector_width:
            detector_samples[cursor:stop, :] = detector_row
        if observable_width:
            observable_samples[cursor:stop, :] = observable_row
        cursor = stop

    layout_manifest = _mcwf_record_layout_manifest(layout)
    provenance = {
        "backend": AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT,
        "representability": AXIS1_MCWF_MPS_RECORD_OUTPUT_REPRESENTABILITY,
        "record_semantics": "temporal_detector_events_and_logical_observable_flips",
        "source_kind": preflight.source_kind,
        "source_hash": preflight.source_hash,
        "carrier_execution_schema": carrier["schema"],
        "carrier_execution_content_hash": carrier["content_hash"],
        "direct_execution_schema": direct_schema,
        "direct_execution_content_hash": direct_hash,
        "restricted_acceptance_policy_content_hash": (
            binding.restricted_acceptance_policy_content_hash
        ),
        "measurement_keys": list(layout.measurement_keys),
        "measurement_targets": list(layout.measurement_targets),
        "measurement_bases": list(layout.measurement_bases),
        "reset_after": list(layout.reset_after),
        "measurement_basis": record_execution["measurement_basis"],
        "record_layout_schema": layout_manifest["schema"],
        "record_layout_content_hash": layout_manifest["content_hash"],
        "detector_names": [definition.name for definition in layout.detectors],
        "observable_names": [definition.name for definition in layout.observables],
        "detector_xor_columns": [
            list(definition.columns) for definition in layout.detectors
        ],
        "observable_xor_columns": [
            list(definition.columns) for definition in layout.observables
        ],
        "trajectory_count": trajectory_count,
        "rng_seed": expected_seed,
        "device": preflight.device,
        "local_dims": list(preflight.expected_execution_options["local_dims"]),
        "initial_levels": list(
            preflight.expected_execution_options["initial_levels"]
        ),
        "microstep_count": preflight.expected_execution_options[
            "microstep_count"
        ],
        "finite_step_order": preflight.expected_execution_options[
            "finite_step_order"
        ],
        "mass_residual_budget": preflight.expected_execution_options[
            "mass_residual_budget"
        ],
        "max_bond": preflight.expected_execution_options["max_bond"],
        "worst_cut_discarded_weight_gate": preflight.expected_execution_options[
            "worst_cut_discarded_weight_gate"
        ],
        "total_discarded_weight_gate": preflight.expected_execution_options[
            "total_discarded_weight_gate"
        ],
        "leaked_readout_b": preflight.expected_execution_options[
            "leaked_readout_b"
        ],
        "state_dtype": "torch.complex128",
        "record_dtype": "numpy.uint8",
        "estimated_peak_record_array_payload_bytes": (
            preflight.estimated_peak_record_array_payload_bytes
        ),
        "max_record_array_payload_bytes": preflight.max_record_array_payload_bytes,
        "estimated_record_support_upper_bound": (
            preflight.estimated_record_support_upper_bound
        ),
        "estimated_record_support_cells": preflight.estimated_record_support_cells,
        "max_record_support_cells": preflight.max_record_support_cells,
        "materialization_order": _MCWF_RECORD_MATERIALIZATION_ORDER,
        "original_trajectory_order_preserved": False,
        "execution_status": execution_status,
        "certification_status": certification_status,
        "diagnostic_only": diagnostic_only,
        "accepted_for_restricted_execution": True,
    }
    record_batch = RecordBatch(
        det=detector_samples,
        obs=observable_samples,
        provenance=provenance,
    )
    if record_batch.n_shots != trajectory_count:
        raise ValueError("MCWF RecordBatch shot count changed during freezing")
    return record_batch


def _validate_mcwf_record_support_projection(
    layout: Axis1ScheduleRecordLayout,
    *,
    measurement_records: list[list[int]],
    detector_rows: list[list[int]],
    observable_rows: list[list[int]],
) -> None:
    """Stream canonical-order and sealed-XOR checks with O(one row) workspace."""

    if not (
        len(measurement_records) == len(detector_rows) == len(observable_rows)
    ):
        raise ValueError("MCWF Record support projection rows must align")
    previous_row: list[int] | None = None
    for row_index, (measurement_row, detector_row, observable_row) in enumerate(
        zip(
            measurement_records,
            detector_rows,
            observable_rows,
            strict=True,
        )
    ):
        if len(measurement_row) != layout.measurement_width:
            raise ValueError(
                f"MCWF measurement record {row_index} width does not match the sealed layout"
            )
        if previous_row is not None and previous_row >= measurement_row:
            raise ValueError(
                "MCWF Record materialization requires sorted unique measurement Records"
            )
        previous_row = measurement_row
        if len(detector_row) != len(layout.detectors):
            raise ValueError("MCWF detector row width does not match the sealed layout")
        if len(observable_row) != len(layout.observables):
            raise ValueError("MCWF observable row width does not match the sealed layout")
        for output_index, definition in enumerate(layout.detectors):
            expected = 0
            for column in definition.columns:
                expected ^= measurement_row[column]
            if detector_row[output_index] != expected:
                raise ValueError(
                    "MCWF detector rows do not match the sealed XOR projection"
                )
        for output_index, definition in enumerate(layout.observables):
            expected = 0
            for column in definition.columns:
                expected ^= measurement_row[column]
            if observable_row[output_index] != expected:
                raise ValueError(
                    "MCWF observable rows do not match the sealed XOR projection"
                )


def _mcwf_record_layout_manifest(
    layout: Axis1ScheduleRecordLayout,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema": layout.schema,
        "source_hash": layout.source_hash,
        "schedule_schema": layout.schedule_schema,
        "measurement_keys": list(layout.measurement_keys),
        "measurement_targets": list(layout.measurement_targets),
        "measurement_bases": list(layout.measurement_bases),
        "reset_after": list(layout.reset_after),
        "measurement_boundaries": [
            {
                "substep_id": boundary.substep_id,
                "substep_index": boundary.substep_index,
                "global_slice": list(boundary.global_slice),
            }
            for boundary in layout.boundaries
        ],
        "detectors": [
            {
                "ordinal": definition.ordinal,
                "name": definition.name,
                "keys": list(definition.keys),
                "columns": list(definition.columns),
            }
            for definition in layout.detectors
        ],
        "observables": [
            {
                "ordinal": definition.ordinal,
                "name": definition.name,
                "keys": list(definition.keys),
                "columns": list(definition.columns),
            }
            for definition in layout.observables
        ],
    }
    payload["content_hash"] = _streaming_stable_payload_hash(payload)
    return payload


def _mcwf_record_sample_manifest(
    carrier: dict[str, Any],
    record_batch: RecordBatch,
    *,
    detection_events: Path | None,
    obs_flips_actual: Path | None,
    carrier_evidence: Path,
    carrier_program_evidence: Path,
    artifact_seals: dict[str, _Axis1McwfMpsRecordArtifactSeal],
    preflight: _Axis1McwfMpsRecordPreflight,
    publication_preflight: _Axis1McwfMpsRecordPublicationPreflight,
) -> dict[str, Any]:
    provenance = dict(record_batch.provenance)
    layout_manifest = _mcwf_record_layout_manifest(preflight.layout)
    summary = record_summary(record_batch.det, record_batch.obs)
    summary.update(
        {
            "schema": AXIS1_MCWF_MPS_RECORD_OUTPUT_SCHEMA,
            "representability": AXIS1_MCWF_MPS_RECORD_OUTPUT_REPRESENTABILITY,
            "source_kind": provenance["source_kind"],
            "source_hash": provenance["source_hash"],
            "carrier_execution_schema": provenance["carrier_execution_schema"],
            "carrier_execution_content_hash": provenance[
                "carrier_execution_content_hash"
            ],
            "direct_execution_schema": provenance["direct_execution_schema"],
            "direct_execution_content_hash": provenance[
                "direct_execution_content_hash"
            ],
            "restricted_acceptance_policy_content_hash": provenance[
                "restricted_acceptance_policy_content_hash"
            ],
            "execution_status": provenance["execution_status"],
            "certification_status": provenance["certification_status"],
            "diagnostic_only": provenance["diagnostic_only"],
            "accepted_for_restricted_execution": provenance[
                "accepted_for_restricted_execution"
            ],
            "verdict": carrier["verdict"],
            "passed": carrier["passed"],
            "trajectory_count": provenance["trajectory_count"],
            "measurement_keys": list(provenance["measurement_keys"]),
            "measurement_targets": list(provenance["measurement_targets"]),
            "measurement_bases": list(provenance["measurement_bases"]),
            "reset_after": list(provenance["reset_after"]),
            "measurement_basis": provenance["measurement_basis"],
            "record_layout": layout_manifest,
            "record_semantics": provenance["record_semantics"],
            "materialization_order": _MCWF_RECORD_MATERIALIZATION_ORDER,
            "original_trajectory_order_preserved": False,
            "estimated_peak_record_array_payload_bytes": (
                preflight.estimated_peak_record_array_payload_bytes
            ),
            "max_record_array_payload_bytes": (
                preflight.max_record_array_payload_bytes
            ),
            "estimated_record_support_upper_bound": (
                preflight.estimated_record_support_upper_bound
            ),
            "estimated_record_support_cells": (
                preflight.estimated_record_support_cells
            ),
            "max_record_support_cells": preflight.max_record_support_cells,
            "record_array_payload_peak_model": (
                "4 * trajectory_count * (detector_width + observable_width) "
                "bytes: preallocated uint8 rows plus RecordBatch binary "
                "validation/freezing temporaries"
            ),
            "record_array_payload_bound_scope": (
                "incremental NumPy Record arrays only; excludes resident Carrier, "
                "Python support/layout objects, canonical JSON authentication, "
                "array headers/allocator overhead, build provenance, and publication RSS"
            ),
            "run_configuration": {
                "num_qubits": preflight.num_qubits,
                "trajectory_count": preflight.trajectory_count,
                "detector_width": preflight.detector_width,
                "observable_width": preflight.observable_width,
                "device": preflight.device,
                "local_dims": list(
                    preflight.expected_execution_options["local_dims"]
                ),
                "initial_levels": list(
                    preflight.expected_execution_options["initial_levels"]
                ),
                "rng_seed": provenance["rng_seed"],
                "microstep_count": preflight.expected_execution_options[
                    "microstep_count"
                ],
                "finite_step_order": preflight.expected_execution_options[
                    "finite_step_order"
                ],
                "mass_residual_budget": preflight.expected_execution_options[
                    "mass_residual_budget"
                ],
                "max_bond": preflight.expected_execution_options["max_bond"],
                "worst_cut_discarded_weight_gate": (
                    preflight.expected_execution_options[
                        "worst_cut_discarded_weight_gate"
                    ]
                ),
                "total_discarded_weight_gate": (
                    preflight.expected_execution_options[
                        "total_discarded_weight_gate"
                    ]
                ),
                "leaked_readout_b": preflight.expected_execution_options[
                    "leaked_readout_b"
                ],
                "state_dtype": "torch.complex128",
                "record_dtype": "numpy.uint8",
                "precision_purpose": (
                    "complex128 restricted-state execution; exact binary "
                    "Record encoding"
                ),
            },
              "build_identity": copy.deepcopy(publication_preflight.build_identity),
              "build_identity_scope": (
                  "disk_package_tree_matches_package_import_time_digest_at_"
                  "validation_checkpoints"
              ),
            "source_implementation": copy.deepcopy(
                publication_preflight.source_implementation
            ),
              "source_implementation_identity_scope": (
                  "disk_source_file_matches_module_import_time_digest_at_"
                  "validation_checkpoints"
              ),
            "claims_runtime_code_object_attestation": False,
            "environment_identity": copy.deepcopy(
                publication_preflight.environment_identity
            ),
            "carrier_child_claims_b8_artifact": carrier["record_execution"][
                "claims_b8_artifact"
            ],
            "claims_b8_artifact": True,
            "claims_dem_artifact": False,
            "claims_decoder_integration": False,
              "claims_original_trajectory_order": False,
              "claims_production_scalable_backend": False,
              "offline_audit_scope": (
                  "public_record_gate_and_binding_not_evaluator_replay"
              ),
              "claims_evaluator_oracle_replay": False,
              "metric_and_gate_policy": {
                "new_metric": None,
                "new_gate": None,
                "negative_controls": [
                    "reject_unaccepted_or_diagnostic_carrier",
                    "reject_rehashed_record_law_without_same_call_binding",
                    "reject_noncanonical_or_over_budget_output",
                ],
                "verdict_source": (
                    "same-call-validated Carrier restricted acceptance"
                ),
                "verdict_evidence_locator": (
                    f"{carrier_evidence.name}#/restricted_acceptance_policy"
                ),
                  "program_evidence_locator": carrier_program_evidence.name,
                  "direct_execution_summary_locator": (
                      f"{carrier_evidence.name}#/mcwf_mps_execution"
                  ),
                  "evaluator_replay_available": False,
              },
            "artifacts": {
                  "carrier_program": _mcwf_record_carrier_program_entry(
                      carrier_program_evidence,
                      program=preflight.carrier_program,
                      seal=artifact_seals[carrier_program_evidence.name],
                  ),
                  "carrier_execution": _mcwf_record_carrier_evidence_entry(
                      carrier_evidence,
                      carrier=carrier,
                      seal=artifact_seals[carrier_evidence.name],
                  ),
                  "detection_events": _mcwf_record_artifact_entry(
                      detection_events,
                      bit_width=int(record_batch.det.shape[1]),
                      seal=(
                          artifact_seals[detection_events.name]
                          if detection_events is not None
                          else None
                      ),
                  ),
                  "obs_flips_actual": _mcwf_record_artifact_entry(
                      obs_flips_actual,
                      bit_width=int(record_batch.obs.shape[1]),
                      seal=(
                          artifact_seals[obs_flips_actual.name]
                          if obs_flips_actual is not None
                          else None
                      ),
                  ),
                "detector_error_model": None,
                "decoder_results": None,
            },
              "publication_status": "prepared_for_atomic_publication",
              "claims_offline_durability_confirmation": False,
              "atomic_publication": {
                "protocol": (
                    "sealed_parent_dirfd_staged_fsync_renameat2_noreplace_v2"
                ),
                "manifest_written_last_in_stage": True,
                "complete_artifact_set_visible_after_single_rename": True,
                "staging_directory_fsync_required_before_rename": True,
                "staging_directory_fsync_success_attested_in_bundle": False,
                "staged_artifact_set_policy": (
                    "exact_regular_files_bound_by_st_dev_st_ino_st_mode_st_size_"
                    "st_mtime_ns_st_ctime_ns_sha256"
                ),
                "artifact_file_fsync_required_at_each_seal_checkpoint": True,
                "artifact_file_fsync_success_attested_in_bundle": False,
                "staged_artifact_set_revalidation_required_after_stage_fsync": True,
                "staged_artifact_set_revalidation_success_attested_in_bundle": False,
                "published_artifact_set_recheck_after_rename_required": True,
                "published_artifact_set_recheck_after_rename_success_attested_in_bundle": False,
                "published_artifact_set_recheck_after_parent_fsync_required": True,
                "published_artifact_set_recheck_after_parent_fsync_success_attested_in_bundle": False,
                "parent_directory_fsync_required_after_rename": True,
                  "parent_directory_fsync_success_attested_in_bundle": False,
                  "destination_no_clobber": True,
                  "unsupported_atomic_noreplace_fails_closed": True,
                  "target_parent_renameat2_noreplace_probe": (
                      "passed_before_mcwf_execution"
                  ),
                  "target_parent_identity_fields": ["st_dev", "st_ino"],
                  "sealed_parent_dirfd_held_since_preflight": True,
                  "rename_on_sealed_parent_dirfd_required": True,
                  "parent_fsync_on_sealed_parent_dirfd_required": True,
                  "return_path_parent_identity_recheck_required_after_parent_fsync": True,
                  "published_destination_identity_match_required_after_rename": True,
                  "published_destination_identity_match_success_attested_in_bundle": False,
                  "published_destination_identity_recheck_after_parent_fsync_required": True,
                  "published_destination_identity_recheck_success_attested_in_bundle": False,
                  "published_destination_identity_recheck_after_final_artifact_recheck_required": True,
                  "published_destination_identity_recheck_after_final_artifact_recheck_success_attested_in_bundle": False,
                  "rename_exception_policy": (
                      "detect_sealed_stage_at_destination_preserve_and_raise"
                  ),
                  "sealed_identity_revalidation_required_after_execution": True,
                  "sealed_identity_revalidation_required_before_atomic_rename": True,
                  "sealed_identity_revalidation_required_after_final_artifact_recheck": True,
                  "sealed_identity_revalidation_success_attested_in_bundle": False,
                  "durability_confirmation": (
                      "successful_writer_return_only_not_self_attested_in_bundle"
                  ),
                  "durability_failure_policy": (
                      "preserve_published_directory_raise_without_path_cleanup"
                  ),
            },
            "scored_quantity_policy": (
                "canonical Record materialization only; no new scored quantity"
            ),
            "epistemic_classes": {
                "histogram_count_expansion": "a",
                "sealed_xor_projection_binding": "a",
                "b8_encoding": "a",
                "restricted_scientific_status": "c",
                "dem_decoder_non_claim": "a",
            },
        }
    )
    summary["content_hash"] = _streaming_stable_payload_hash(summary)
    return summary


def _mcwf_record_build_identity() -> dict[str, Any]:
    """Return a fresh, uncached package identity for a claim-bearing run."""

    package_tree_sha256 = _mcwf_record_fresh_package_tree_sha256()
    if package_tree_sha256 != _PACKAGE_TREE_SHA256_AT_IMPORT:
        raise RuntimeError(
            "MCWF Record loaded package tree differs from current disk package tree"
        )
    package_version = _required_distribution_version("error-coupling-simulator")
    return {
        "schema": "error_coupling_simulator.carrier.package_build_identity.v1",
        "distribution": "error-coupling-simulator",
        "version": package_version,
        "package_tree_sha256": package_tree_sha256,
        "git_commit": _mcwf_record_fresh_git_commit(),
    }


def _mcwf_record_fresh_package_tree_sha256() -> str:
    package_root = Path(__file__).resolve().parents[1]
    included_suffixes = {".py", ".cpp", ".cu", ".md", ".json", ".npz"}
    paths = sorted(
        path
        for path in package_root.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix in included_suffixes
    )
    digest = hashlib.sha256()
    for path in paths:
        relative = path.relative_to(package_root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        data = path.read_bytes()
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def _mcwf_record_fresh_git_commit() -> str:
    try:
        repository_root = Path(__file__).resolve().parents[3]
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repository_root),
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception as exc:
        raise RuntimeError("MCWF Record Git HEAD identity is unavailable") from exc
    commit = result.stdout.strip()
    if result.returncode != 0 or len(commit) not in {40, 64}:
        raise RuntimeError("MCWF Record Git HEAD identity is unavailable")
    try:
        int(commit, 16)
    except ValueError as exc:
        raise RuntimeError("MCWF Record Git HEAD identity is invalid") from exc
    return commit


def _mcwf_record_source_implementation_identity() -> dict[str, Any]:
    source_path = Path(__file__).resolve()
    source_sha256 = file_sha256(source_path)
    if not isinstance(source_sha256, str) or len(source_sha256) != 64:
        raise RuntimeError("MCWF Record source-file SHA-256 is unavailable")
    try:
        int(source_sha256, 16)
    except ValueError as exc:
        raise RuntimeError("MCWF Record source-file SHA-256 is invalid") from exc
    if source_sha256 != _MCWF_RECORD_SOURCE_SHA256_AT_IMPORT:
        raise RuntimeError(
            "MCWF Record loaded source file differs from current disk source file"
        )
    return {
        "module": "error_coupling_simulator.frontend.axis1_carrier_execution",
        "package_relative_file": "frontend/axis1_carrier_execution.py",
        "resolved_import_origin": str(source_path),
        "sha256": source_sha256,
    }


def _mcwf_record_environment_identity(
    *,
    environment_lock: Path,
    environment_lock_hash: str,
    device: str,
) -> dict[str, Any]:
    return {
        "authoritative_lock_file": environment_lock.name,
        "authoritative_lock_path": str(environment_lock),
        "authoritative_lock_sha256": environment_lock_hash,
        "authoritative_lock_status": "bound",
        "authoritative_lock_scope": "lock_hash_bound_only",
        "authoritative_lock_conformance_checked": False,
        "claims_reproducible_environment": False,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "torch": _required_distribution_version("torch"),
        "quimb": _required_distribution_version("quimb"),
        "scipy": _required_distribution_version("scipy"),
        "runtime": _mcwf_record_runtime_identity(device),
    }


def _mcwf_record_runtime_identity(device: str) -> dict[str, Any]:
    if not device.startswith("cuda") or not torch.cuda.is_available():
        raise RuntimeError(
            "claim-bearing MCWF Record publication requires in-process CUDA identity"
        )
    if ":" in device:
        logical_index = int(device.split(":", 1)[1])
    else:
        logical_index = int(torch.cuda.current_device())
    properties = torch.cuda.get_device_properties(logical_index)
    gpu_uuid = str(getattr(properties, "uuid", ""))
    cuda_build_version = torch.version.cuda
    if (
        not gpu_uuid
        or gpu_uuid == "None"
        or not isinstance(cuda_build_version, str)
        or not cuda_build_version.strip()
        or cuda_build_version == "None"
    ):
        raise RuntimeError("MCWF Record CUDA UUID/build identity is unavailable")
    driver_path = Path("/proc/driver/nvidia/version")
    try:
        driver_line = driver_path.read_text(encoding="utf-8").splitlines()[0]
    except (OSError, IndexError) as exc:
        raise RuntimeError("MCWF Record NVIDIA driver identity is unavailable") from exc
    driver_version = next(
        (
            token
            for token in driver_line.split()
            if token.count(".") == 2
            and all(part.isdigit() for part in token.split("."))
        ),
        None,
    )
    if driver_version is None:
        raise RuntimeError("MCWF Record NVIDIA driver version is unavailable")
    return {
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "logical_device_index": logical_index,
        "gpu_name": str(properties.name),
        "gpu_uuid": gpu_uuid,
        "pci_bus_id": int(getattr(properties, "pci_bus_id", -1)),
        "compute_capability": [int(properties.major), int(properties.minor)],
        "total_memory_bytes": int(properties.total_memory),
        "torch_cuda_build_version": cuda_build_version,
        "loaded_cuda_runtime_version": None,
        "loaded_cuda_runtime_version_status": "not_attested",
        "cudnn_runtime": torch.backends.cudnn.version(),
        "nvidia_driver": driver_version,
    }


def _distribution_version(distribution: str) -> str | None:
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return None


def _required_distribution_version(distribution: str) -> str:
    version = _distribution_version(distribution)
    if not isinstance(version, str) or not version:
        raise RuntimeError(
            f"MCWF Record distribution identity is unavailable: {distribution}"
        )
    return version


def _mcwf_record_carrier_evidence_entry(
    path: Path,
    *,
    carrier: dict[str, Any],
    seal: _Axis1McwfMpsRecordArtifactSeal,
) -> dict[str, Any]:
    _require_mcwf_record_artifact_seal_name(path, seal)
    return {
        "file": path.name,
        "sha256": seal.sha256,
        "size_bytes": seal.size_bytes,
        "status": "written",
        "schema": carrier["schema"],
        "content_hash": carrier["content_hash"],
        "contains_restricted_acceptance_policy": True,
        "contains_carrier_program_summary": True,
        "contains_evaluator_only_truth": False,
        "restricted_acceptance_policy_locator": (
            f"{path.name}#/restricted_acceptance_policy"
        ),
        "carrier_program_summary_locator": f"{path.name}#/carrier_program",
        "direct_execution_summary_locator": f"{path.name}#/mcwf_mps_execution",
        "record_execution_locator": f"{path.name}#/record_execution",
        "audit_role": "exact_materialization_input_not_downstream_record",
        "present": True,
    }


def _mcwf_record_carrier_program_entry(
    path: Path,
    *,
    program: dict[str, Any],
    seal: _Axis1McwfMpsRecordArtifactSeal,
) -> dict[str, Any]:
    _require_mcwf_record_artifact_seal_name(path, seal)
    return {
        "file": path.name,
        "sha256": seal.sha256,
        "size_bytes": seal.size_bytes,
        "status": "written",
        "schema": program["schema"],
        "content_hash": program["content_hash"],
        "contains_complete_sealed_program": True,
        "contains_evaluator_only_truth": False,
        "audit_role": "exact_sealed_execution_input_not_downstream_record",
        "present": True,
    }


def _mcwf_record_artifact_entry(
    path: Path | None,
    *,
    bit_width: int,
    seal: _Axis1McwfMpsRecordArtifactSeal | None,
) -> dict[str, Any] | None:
    if path is None:
        if seal is not None:
            raise RuntimeError("MCWF Record absent artifact has an unexpected seal")
        return None
    if seal is None:
        raise RuntimeError("MCWF Record required staged artifact seal is missing")
    _require_mcwf_record_artifact_seal_name(path, seal)
    return {
        "file": path.name,
        "sha256": seal.sha256,
        "size_bytes": seal.size_bytes,
        "status": "written",
        "bit_width": int(bit_width),
        "packing": "little_endian_bits_padded_per_shot",
        "present": True,
    }


def _require_mcwf_record_artifact_seal_name(
    path: Path,
    seal: _Axis1McwfMpsRecordArtifactSeal,
) -> None:
    if path.name != seal.name:
        raise RuntimeError("MCWF Record required staged artifact seal name changed")


def _count_measured_qubits(schedule: SubstepSchedule) -> int:
    """Total measured qubits across the schedule — the dense record branch exponent.

    The dense record enumerator holds a BATCH of measurement branches and doubles
    the batch on every measured qubit (``measure_qubit_enumerate`` returns the
    stacked outcome-0/outcome-1 blocks, ``forward/exact/circuit_sim.py``), with no
    pruning in that path. So the resident branch count is ``2 ** (this count)``.
    """

    total = 0
    for substep in schedule.substeps:
        if substep.kind != "measurement":
            continue
        for op in substep.operations:
            total += len(getattr(op, "measurement_keys", ()) or ())
    return total


def _project_dense_record_vram_bytes(schedule: SubstepSchedule) -> float:
    """Project the dense joint-L record-probe PEAK VRAM need (bytes).

    The dense record path does NOT hold a single ``(2**n, 2**n)`` density matrix —
    it holds ``2**m`` of them stacked along a branch axis, where ``m`` is the total
    number of measured qubits (each measurement doubles the resident batch; no
    pruning). The peak is therefore ``2**m * 4**n * 16`` bytes, with a transient
    multiplier for the ``torch.stack`` copy + per-branch projection intermediates.

    Modelling the branch factor is the load-bearing correction: a bare ``4**n``
    projection is a LOWER bound on the real need, and routing-to-dense on a lower
    bound is UNSAFE (it admits dense for schedules whose branch-inflated peak then
    OOMs). This projection is an over-estimate, so it fails TOWARD MCWF.
    """

    n = int(schedule.num_qubits)
    m = _count_measured_qubits(schedule)
    return (
        AXIS1_CARRIER_DENSE_RECORD_TRANSIENT_FACTOR
        * (2.0**m)
        * (4.0**n)
        * 16.0
    )


def _available_vram_bytes(device: str) -> float:
    """Free VRAM (bytes) on the CUDA device, via the same probe window_channel uses."""

    import torch

    free_bytes, _total = torch.cuda.mem_get_info(device)
    return float(free_bytes)


def _select_dense_or_mcwf(
    schedule: SubstepSchedule,
    device: str,
    program: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Route dense vs MCWF: dense only if it fits VRAM AND is under the structural caps.

    The VRAM trigger is the user-requested rule — if the projected dense need
    exceeds the safety fraction of currently-free VRAM, route to MCWF. The qubit
    cap and ``requires_scalable_backend`` are kept as additional structural
    backstops, all of which fail TOWARD the memory-bounded backend (anti-OOM).
    """

    n = int(schedule.num_qubits)
    measured_qubits = _count_measured_qubits(schedule)
    projected = _project_dense_record_vram_bytes(schedule)
    free_observation = _available_vram_bytes(device)
    free_is_finite_positive = (
        isinstance(free_observation, Real)
        and type(free_observation) is not bool
        and math.isfinite(float(free_observation))
        and float(free_observation) > 0.0
    )
    free = float(free_observation) if free_is_finite_positive else None
    budget = (
        AXIS1_CARRIER_DENSE_VRAM_SAFETY_FRACTION * free
        if free is not None
        else None
    )
    requires_scalable = _require_manifest_bool(
        program,
        "requires_scalable_backend",
        context="Axis-1 carrier program",
    )
    over_qubit_cap = n > AXIS1_STATE_MAX_EXACT_QUBITS
    over_vram = budget is None or projected > budget
    use_dense = (not requires_scalable) and (not over_qubit_cap) and (not over_vram)
    chosen = (
        AXIS1_CARRIER_EXECUTION_BACKEND_CONTRACT
        if use_dense
        else AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
    )
    reasons: list[str] = []
    if not free_is_finite_positive:
        reasons.append("invalid_available_vram_bytes")
    if requires_scalable:
        reasons.append("requires_scalable_backend")
    if over_qubit_cap:
        reasons.append(f"num_qubits>{AXIS1_STATE_MAX_EXACT_QUBITS}")
    if over_vram and free_is_finite_positive:
        reasons.append("projected_dense_vram_exceeds_safety_budget")
    decision = {
        "schema": "error_coupling_simulator.frontend.carrier_auto_routing_decision.v3",
        "num_qubits": n,
        "measured_qubits": measured_qubits,
        "branch_factor_log2": measured_qubits,
        "dense_record_transient_factor": AXIS1_CARRIER_DENSE_RECORD_TRANSIENT_FACTOR,
        "projected_dense_vram_bytes": projected,
        "projected_dense_vram_gib": projected / (1024.0**3),
        "free_vram_bytes": free,
        "free_vram_gib": None if free is None else free / (1024.0**3),
        "available_vram_is_finite_positive": free_is_finite_positive,
        "safety_fraction": AXIS1_CARRIER_DENSE_VRAM_SAFETY_FRACTION,
        "dense_vram_budget_bytes": budget,
        "dense_vram_budget_gib": None if budget is None else budget / (1024.0**3),
        "requires_scalable_backend": requires_scalable,
        "over_qubit_cap": over_qubit_cap,
        "over_vram_budget": over_vram,
        "use_dense": use_dense,
        "resolved_backend_contract": chosen,
        "route_reasons": reasons if reasons else ["dense_fits_vram_and_under_caps"],
        "projection_semantics": (
            "dense record peak = transient_factor * 2^(measured_qubits) * (2^n,2^n) "
            "complex128 * 16 bytes; the 2^(measured_qubits) branch batch is the "
            "load-bearing term and this projection over-estimates it, so routing "
            "fails TOWARD the memory-bounded MCWF backend; a nonfinite or "
            "nonpositive free-VRAM observation also fails toward MCWF and is "
            "never serialized as a nonfinite JSON number"
        ),
    }
    return chosen, decision


def _axis1_auto_routed_execution_manifest(
    schedule: SubstepSchedule,
    *,
    device: str,
    instrument_spec: Axis1ReadoutResetInstrumentSpec | None,
    execution_backend_options: dict[str, Any] | None,
) -> dict[str, Any]:
    """VRAM-aware auto-router: pick dense vs MCWF, delegate, wrap with the decision.

    On over-cap / over-VRAM it routes to the memory-bounded MCWF/MPS backend
    instead of failing closed. Two caller inputs are incompatible with that
    routing and are rejected UP FRONT with a clear message rather than failing
    deep inside the chosen backend: (1) an ``instrument_spec`` (readout/reset
    noise) is dense-only — MCWF does not implement it; (2) MCWF-tuning
    ``execution_backend_options`` are meaningless for the dense backend (which
    rejects any options), so they are forwarded ONLY when MCWF is chosen.
    """

    device = normalize_mps_device(device)
    raw_options = dict(execution_backend_options or {})
    options = (
        _validate_mcwf_mps_execution_options(raw_options)
        if raw_options
        else {}
    )
    canonical_options = copy.deepcopy(options)
    dev = _require_cuda_device(device)
    program = axis1_carrier_program_manifest(schedule)
    chosen, decision = _select_dense_or_mcwf(schedule, dev, program)
    routes_to_mcwf = chosen == AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
    if routes_to_mcwf and instrument_spec is not None:
        raise ValueError(
            "auto routing selected the MCWF/MPS backend "
            f"(reasons={decision['route_reasons']}) but an Axis1ReadoutResetInstrumentSpec "
            "was supplied; the readout/reset instrument is dense-only. Request "
            f"{AXIS1_CARRIER_EXECUTION_BACKEND_CONTRACT!r} explicitly for the small-N "
            "instrument path, or drop the instrument_spec for the scalable backend."
        )
    if options and not routes_to_mcwf:
        raise ValueError(
            "auto routing selected the dense backend "
            f"(reasons={decision['route_reasons']}) but execution_backend_options "
            f"{sorted(options)} were supplied; those tune the MCWF/MPS backend and the "
            "dense probe accepts none. Drop the options, or force the scalable backend."
        )
    inner = axis1_carrier_execution_manifest(
        schedule,
        device=dev,
        instrument_spec=instrument_spec,
        execution_backend_contract=chosen,
        execution_backend_options=(
            copy.deepcopy(canonical_options) if routes_to_mcwf else None
        ),
    )
    inner_passed = _require_manifest_bool(
        inner, "passed", context="auto-routed Carrier execution"
    )
    inner_verdict = _require_manifest_text(
        inner, "verdict", context="auto-routed Carrier execution"
    )
    expected_verdict = "pass" if inner_passed else "fail"
    if inner_verdict != expected_verdict:
        raise ValueError(
            "auto-routed Carrier child verdict must agree with its passed field"
        )
    _validate_auto_routed_carrier_child(
        inner,
        schedule=schedule,
        chosen_backend_contract=chosen,
        expected_device=dev,
        expected_execution_backend_options=(
            canonical_options if routes_to_mcwf else None
        ),
    )
    payload: dict[str, Any] = {
        "schema": AXIS1_CARRIER_AUTO_EXECUTION_SCHEMA,
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "gpu_required": True,
        "device": dev,
        "requested_backend_contract": AXIS1_CARRIER_AUTO_BACKEND_CONTRACT,
        "resolved_backend_contract": chosen,
        "auto_routing": decision,
        "verdict": inner_verdict,
        "passed": inner_passed,
        "blocked_reason": inner.get("blocked_reason"),
        "execution": inner,
        "dynamics_artifact_reference_certification": (
            copy.deepcopy(
                inner.get("dynamics_artifact_reference_certification")
            )
            if routes_to_mcwf
            else None
        ),
        "scored_quantity_policy": (
            "VRAM-aware backend router; no new scored quantity; the delegated "
            "backend keeps its own representability and evidence"
        ),
        "claims_dense_channel_evidence": False,
        "claims_axis2_source_timeline": False,
    }
    payload["content_hash"] = _stable_payload_hash(payload)
    return payload


def _validate_auto_routed_carrier_child(
    child: dict[str, Any],
    *,
    schedule: SubstepSchedule,
    chosen_backend_contract: str,
    expected_device: str,
    expected_execution_backend_options: dict[str, Any] | None,
) -> None:
    """Authenticate the delegated Carrier envelope against the router request."""

    _validate_child_content_hash(child, context="auto-routed Carrier child")
    schema = _require_manifest_text(
        child,
        "schema",
        context="auto-routed Carrier child",
    )
    if schema != AXIS1_CARRIER_EXECUTION_SCHEMA:
        raise ValueError("auto-routed Carrier child schema is not registered")
    expected_representability_by_route = {
        AXIS1_CARRIER_EXECUTION_BACKEND_CONTRACT: (
            AXIS1_CARRIER_EXECUTION_REPRESENTABILITY
        ),
        AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT: (
            AXIS1_CARRIER_MCWF_MPS_EXECUTION_REPRESENTABILITY
        ),
    }
    if chosen_backend_contract not in expected_representability_by_route:
        raise ValueError("auto-routed Carrier resolved backend is not registered")
    expected_text_fields = {
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "representability": expected_representability_by_route[
            chosen_backend_contract
        ],
        "execution_backend_contract": chosen_backend_contract,
        "device": expected_device,
    }
    for field, expected in expected_text_fields.items():
        actual = _require_manifest_text(
            child,
            field,
            context="auto-routed Carrier child",
        )
        if actual != expected:
            raise ValueError(
                f"auto-routed Carrier child {field} must match the resolved request"
            )
    if not _require_manifest_bool(
        child,
        "gpu_required",
        context="auto-routed Carrier child",
    ):
        raise ValueError("auto-routed Carrier child gpu_required must be true")

    if chosen_backend_contract == AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT:
        if expected_execution_backend_options is None:
            raise ValueError(
                "auto-routed MCWF Carrier request options must be registered"
            )
        trusted_program = axis1_carrier_program_manifest(
            schedule,
            backend_contract=chosen_backend_contract,
        )
        expected_mcwf = _mcwf_mps_expected_options(
            expected_execution_backend_options,
            num_sites=int(schedule.num_qubits),
        )
        _validate_auto_routed_mcwf_summary(
            child,
            schedule=schedule,
            expected_execution_backend_options=(
                expected_execution_backend_options
            ),
            trusted_program=trusted_program,
            expected=expected_mcwf,
            expected_device=expected_device,
        )
        expected_program = _restricted_mps_program_summary(trusted_program)
        route_false_claims = (
            "claims_production_scalable_backend",
            "claims_exact_joint_lindblad_generator",
            "claims_qt_mps_backend_execution",
            "claims_qutip_cuquantum_execution",
        )
        optional_route_false_claims: tuple[str, ...] = ()
        _validate_auto_routed_mcwf_record_execution(
            child,
            schedule=schedule,
            expected_execution=expected_mcwf,
        )
    else:
        trusted_program = axis1_carrier_program_manifest(schedule)
        expected_program = _carrier_program_summary(trusted_program)
        route_false_claims = ()
        optional_route_false_claims = (
            "claims_production_scalable_backend",
            "claims_exact_joint_lindblad_generator",
            "claims_mcwf_mps_backend_execution",
            "claims_qt_mps_backend_execution",
            "claims_qutip_cuquantum_execution",
        )
    child_program = child.get("carrier_program")
    if not isinstance(child_program, dict):
        raise TypeError("auto-routed Carrier child carrier_program must be a mapping")
    if _stable_payload_hash({"carrier_program": child_program}) != (
        _stable_payload_hash({"carrier_program": expected_program})
    ):
        raise ValueError(
            "auto-routed Carrier child carrier_program must match the trusted "
            "schedule and resolved route"
        )

    for field in (
        "claims_dense_channel_evidence",
        "claims_dem_decoder_semantics",
        "claims_axis2_source_timeline",
        "claims_scalable_backend_completed",
        *route_false_claims,
    ):
        if _require_manifest_bool(
            child,
            field,
            context="auto-routed Carrier child",
        ):
            raise ValueError(f"auto-routed Carrier child {field} must be false")
    for field in optional_route_false_claims:
        if field not in child:
            continue
        if _require_manifest_bool(
            child,
            field,
            context="auto-routed Carrier child",
        ):
            raise ValueError(f"auto-routed Carrier child {field} must be false")


def _reject_auto_routed_evaluator_truth(
    value: Any,
    *,
    path: str = "auto-routed Carrier child",
) -> None:
    """Reject evaluator-only field families anywhere in an emitted child."""

    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{path} keys must be text")
            if key.startswith("evaluator_only") or key.startswith("level_record"):
                raise ValueError(
                    f"{path}.{key} exposes evaluator-only Record truth"
                )
            _reject_auto_routed_evaluator_truth(child, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_auto_routed_evaluator_truth(
                child,
                path=f"{path}[{index}]",
            )


def _require_exact_summary_fields(
    payload: dict[str, Any],
    expected_fields: frozenset[str],
    *,
    context: str,
) -> None:
    actual_fields = set(payload)
    if actual_fields != set(expected_fields):
        missing = sorted(set(expected_fields) - actual_fields)
        extra = sorted(actual_fields - set(expected_fields))
        raise ValueError(
            f"{context} fields must be exact; missing={missing}, extra={extra}"
        )


def _expected_mcwf_local_hilbert_space(local_dims: list[int]) -> dict[str, Any]:
    dims = [int(dim) for dim in local_dims]
    dimension_classes = {dim if dim <= 4 else 5 for dim in dims}
    return {
        "local_dims": dims,
        "num_sites": len(dims),
        "hilbert_dim": int(math.prod(dims)),
        "site_order_policy": "identity_schedule_qubit_order_v1",
        "local_dims_source": (
            "caller_backend_config_or_default_qubit_dims_not_evaluator_truth"
        ),
        "supports_qubit_sites": 2 in dimension_classes,
        "supports_qutrit_sites": 3 in dimension_classes,
        "supports_ququart_sites": 4 in dimension_classes,
        "supports_mixed_local_dimensions": len(set(dims)) > 1,
        "dimension_validation_epistemic_class": "a",
        "modeling_choice_epistemic_class": "c",
    }


def _mcwf_carrier_record_execution_summary(
    direct: dict[str, Any],
    execution: dict[str, Any],
    *,
    executed: bool,
) -> dict[str, Any]:
    """Build the one canonical public Record summary for a direct MCWF child."""

    record_executed = bool(executed and execution.get("measurement_keys"))
    return {
        "executed": record_executed,
        "reason": (
            None
            if record_executed
            else (
                direct.get("blocked_reason")
                if not executed
                else "schedule_has_no_measurement_substep"
            )
        ),
        "measurement_keys": list(execution.get("measurement_keys", ())),
        "measurement_targets": list(
            execution.get("measurement_targets", ())
        ),
        "measurement_bases": list(execution.get("measurement_bases", ())),
        "reset_after": list(execution.get("reset_after", ())),
        "measurement_basis": execution.get("measurement_basis"),
        "measurement_basis_semantics": execution.get(
            "measurement_basis_semantics"
        ),
        "multilevel_measurement_policy": dict(
            execution.get("multilevel_measurement_policy", {})
        ),
        "measurement_records": list(execution.get("measurement_records", ())),
        "record_counts": list(execution.get("record_counts", ())),
        "record_probabilities": list(execution.get("record_probabilities", ())),
        "detector_records": list(execution.get("detector_records", ())),
        "logical_observable_records": list(
            execution.get("logical_observable_records", ())
        ),
        "trajectory_sampling": dict(execution.get("trajectory_sampling", {})),
        "jump_sampling": dict(execution.get("jump_sampling", {})),
        "claims_b8_artifact": (
            _require_manifest_bool(
                execution,
                "claims_b8_artifact",
                context="MCWF/MPS child mps_execution",
            )
            if executed
            else False
        ),
        "claims_decoder_integration": (
            _require_manifest_bool(
                execution,
                "claims_decoder_integration",
                context="MCWF/MPS child mps_execution",
            )
            if executed
            else False
        ),
    }


def _trusted_mcwf_artifact_authority(
    program: dict[str, Any],
    *,
    expected: dict[str, Any],
    device: Any,
) -> tuple[dict[str, Any], str | None]:
    """Rebuild and recertify artifacts from sealed inputs, never child claims."""

    from .axis1_mcwf_mps_execution import (
        _compile_mcwf_dynamics_artifacts,
        _first_order_mass_residual_blocks,
        _mcwf_dynamics_artifacts_content_hash,
        _unsupported_substeps,
    )
    from ..certify.axis1_mps import (
        mcwf_dynamics_artifact_reference_certification,
    )

    dims = tuple(int(dim) for dim in expected["local_dims"])
    if expected["max_bond"] is not None and any(dim != 2 for dim in dims):
        reason = "mcwf_mps_multilevel_finite_bond_ledger_not_implemented"
        packet = mcwf_dynamics_artifact_reference_certification(
            program,
            dynamics_artifacts=None,
            dynamics_artifact_content_hash=None,
            local_dims=dims,
            microstep_count=expected["microstep_count"],
            finite_step_order=expected["finite_step_order"],
            post_execution_integrity_verified=False,
            not_executed_reason=reason,
        )
        return packet, reason
    unsupported = _unsupported_substeps(program, local_dims=dims)
    if unsupported:
        reason = str(unsupported[0]["reason"])
        packet = mcwf_dynamics_artifact_reference_certification(
            program,
            dynamics_artifacts=None,
            dynamics_artifact_content_hash=None,
            local_dims=dims,
            microstep_count=expected["microstep_count"],
            finite_step_order=expected["finite_step_order"],
            post_execution_integrity_verified=False,
            not_executed_reason=reason,
        )
        return packet, reason
    try:
        dynamics_artifacts = _compile_mcwf_dynamics_artifacts(
            program,
            local_dims=dims,
            device=device,
            microstep_count=expected["microstep_count"],
            finite_step_order=expected["finite_step_order"],
        )
    except Exception as exc:
        reason = (
            "mcwf_dynamics_artifact_compile_unavailable:"
            f"{type(exc).__name__}"
        )
        packet = mcwf_dynamics_artifact_reference_certification(
            program,
            dynamics_artifacts=None,
            dynamics_artifact_content_hash=None,
            local_dims=dims,
            microstep_count=expected["microstep_count"],
            finite_step_order=expected["finite_step_order"],
            post_execution_integrity_verified=False,
            not_executed_reason=reason,
        )
        return packet, reason
    artifact_hash = _mcwf_dynamics_artifacts_content_hash(
        program,
        dynamics_artifacts,
        local_dims=dims,
        microstep_count=expected["microstep_count"],
        finite_step_order=expected["finite_step_order"],
    )
    pre_execution_packet = mcwf_dynamics_artifact_reference_certification(
        program,
        dynamics_artifacts=dynamics_artifacts,
        dynamics_artifact_content_hash=artifact_hash,
        local_dims=dims,
        microstep_count=expected["microstep_count"],
        finite_step_order=expected["finite_step_order"],
        post_execution_integrity_verified=False,
    )
    if pre_execution_packet["passed"] is not True:
        return pre_execution_packet, str(pre_execution_packet["reason"])
    if expected["mass_residual_budget"] is not None:
        residual_blocks = _first_order_mass_residual_blocks(
            program,
            local_dims=dims,
            microstep_count=expected["microstep_count"],
            device=device,
            budget=expected["mass_residual_budget"],
            dynamics_artifacts=dynamics_artifacts,
        )
        if residual_blocks:
            return pre_execution_packet, str(residual_blocks[0]["reason"])
    completed_packet = mcwf_dynamics_artifact_reference_certification(
        program,
        dynamics_artifacts=dynamics_artifacts,
        dynamics_artifact_content_hash=artifact_hash,
        local_dims=dims,
        microstep_count=expected["microstep_count"],
        finite_step_order=expected["finite_step_order"],
        post_execution_integrity_verified=True,
    )
    return completed_packet, None


def _trusted_mcwf_blocked_reason(
    program: dict[str, Any],
    *,
    expected: dict[str, Any],
    device: Any,
) -> str | None:
    """Compatibility wrapper for callers that only need the trusted blocker."""

    _, reason = _trusted_mcwf_artifact_authority(
        program,
        expected=expected,
        device=device,
    )
    return reason


def _trusted_seeded_mcwf_direct_authority(
    schedule: SubstepSchedule,
    *,
    execution_backend_options: dict[str, Any],
    device: Any,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Independently replay a seeded direct child and derive its public Record."""

    from .axis1_mcwf_mps_execution import (
        axis1_mcwf_mps_state_record_execution_manifest,
    )

    direct = axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        device=device,
        **copy.deepcopy(execution_backend_options),
    )
    _validate_child_content_hash(direct, context="trusted seeded direct MCWF child")
    executed = _require_manifest_bool(
        direct,
        "mcwf_mps_backend_executed",
        context="trusted seeded direct MCWF child",
    )
    raw_execution = direct.get("mps_execution")
    if executed and not isinstance(raw_execution, dict):
        raise TypeError("trusted seeded direct MCWF execution must be a mapping")
    if not executed and raw_execution is not None:
        raise ValueError("trusted blocked direct MCWF execution must be None")
    execution = raw_execution or {}
    return direct, _mcwf_carrier_record_execution_summary(
        direct,
        execution,
        executed=executed,
    )


def _validate_auto_routed_mcwf_summary(
    child: dict[str, Any],
    *,
    schedule: SubstepSchedule,
    expected_execution_backend_options: dict[str, Any],
    trusted_program: dict[str, Any],
    expected: dict[str, Any],
    expected_device: Any,
) -> None:
    """Authenticate MCWF Carrier state, policy, and request provenance."""

    _require_exact_summary_fields(
        child,
        _MCWF_CARRIER_CHILD_FIELDS,
        context="auto-routed MCWF Carrier child",
    )
    _reject_auto_routed_evaluator_truth(child)

    actual_options = child.get("execution_backend_options")
    if type(actual_options) is not dict:
        raise TypeError(
            "auto-routed MCWF Carrier child execution_backend_options must be an exact mapping"
        )
    if _stable_payload_hash({"options": actual_options}) != _stable_payload_hash(
        {"options": _jsonable(expected_execution_backend_options)}
    ):
        raise ValueError(
            "auto-routed MCWF Carrier child execution_backend_options must match the caller request"
        )
    passed = _require_manifest_bool(
        child,
        "passed",
        context="auto-routed MCWF Carrier child",
    )
    verdict = _require_manifest_text(
        child,
        "verdict",
        context="auto-routed MCWF Carrier child",
    )
    backend_executed = _require_manifest_bool(
        child,
        "mcwf_mps_backend_executed",
        context="auto-routed MCWF Carrier child",
    )
    claimed_execution = _require_manifest_bool(
        child,
        "claims_mcwf_mps_backend_execution",
        context="auto-routed MCWF Carrier child",
    )
    if claimed_execution is not backend_executed:
        raise ValueError(
            "auto-routed MCWF Carrier execution claim must equal backend state"
        )
    trusted_artifact_certification, trusted_blocked_reason = (
        _trusted_mcwf_artifact_authority(
            trusted_program,
            expected=expected,
            device=expected_device,
        )
    )
    artifact_certification = child.get(
        "dynamics_artifact_reference_certification"
    )
    if not isinstance(artifact_certification, dict):
        raise TypeError(
            "auto-routed MCWF Carrier artifact certification must be a mapping"
        )
    if _stable_payload_hash(
        {"certification": artifact_certification}
    ) != _stable_payload_hash(
        {"certification": trusted_artifact_certification}
    ):
        raise ValueError(
            "auto-routed MCWF Carrier artifact certification must match sealed-input authority"
        )
    if backend_executed and trusted_blocked_reason is not None:
        raise ValueError(
            "auto-routed MCWF Carrier executed despite a sealed-input blocker"
        )
    execution_status = _require_manifest_text(
        child,
        "execution_status",
        context="auto-routed MCWF Carrier child",
    )
    certification_status = _require_manifest_text(
        child,
        "certification_status",
        context="auto-routed MCWF Carrier child",
    )
    diagnostic_only = _require_manifest_bool(
        child,
        "diagnostic_only",
        context="auto-routed MCWF Carrier child",
    )
    _validate_restricted_child_state_machine(
        passed=passed,
        child_verdict=verdict,
        backend_executed=backend_executed,
        execution_status=execution_status,
        certification_status=certification_status,
        diagnostic_only=diagnostic_only,
        blocked_reason=child.get("blocked_reason"),
        context="auto-routed MCWF Carrier",
    )

    policy = child.get("restricted_acceptance_policy")
    if not isinstance(policy, dict):
        raise TypeError(
            "auto-routed MCWF Carrier restricted_acceptance_policy must be a mapping"
        )
    accepted = _require_manifest_bool(
        policy,
        "accepted_for_restricted_execution",
        context="auto-routed MCWF Carrier restricted acceptance policy",
    )
    if accepted is not passed:
        raise ValueError(
            "auto-routed MCWF Carrier passed must equal restricted acceptance"
        )
    policy_artifact_certification = policy.get(
        "dynamics_artifact_reference_certification"
    )
    if not isinstance(policy_artifact_certification, dict):
        raise TypeError(
            "auto-routed MCWF Carrier policy artifact certification must be a mapping"
        )
    if _stable_payload_hash(
        {"certification": policy_artifact_certification}
    ) != _stable_payload_hash(
        {"certification": trusted_artifact_certification}
    ):
        raise ValueError(
            "auto-routed MCWF Carrier policy artifact certification must match authority"
        )
    _validate_restricted_policy_state(
        policy,
        execution_status=execution_status,
        certification_status=certification_status,
        diagnostic_only=diagnostic_only,
        blocked_reason=child.get("blocked_reason"),
        context="auto-routed MCWF Carrier",
        route_kind="mcwf",
    )
    if not backend_executed:
        from .axis1_mcwf_mps_execution import _blocked_acceptance_policy

        if trusted_blocked_reason is None:
            raise ValueError(
                "auto-routed MCWF Carrier reported blocked without a trusted "
                "preflight blocker"
            )
        if child.get("blocked_reason") != trusted_blocked_reason:
            raise ValueError(
                "auto-routed MCWF Carrier blocked_reason must match trusted "
                "preflight"
            )
        canonical_blocked_policy = _blocked_acceptance_policy(
            blocked_reason=trusted_blocked_reason,
            rng_seed=expected["rng_seed"],
            trajectory_count=expected["trajectory_count"],
            dynamics_artifact_reference_certification=(
                trusted_artifact_certification
            ),
        )
        if _stable_payload_hash({"policy": policy}) != _stable_payload_hash(
            {"policy": canonical_blocked_policy}
        ):
            raise ValueError(
                "auto-routed blocked MCWF Carrier policy must be canonical"
            )

    local_hilbert_space = child.get("local_hilbert_space")
    if not isinstance(local_hilbert_space, dict):
        raise TypeError(
            "auto-routed MCWF Carrier local_hilbert_space must be a mapping"
        )
    expected_hilbert_space = _expected_mcwf_local_hilbert_space(
        expected["local_dims"]
    )
    if _stable_payload_hash({"local_hilbert_space": local_hilbert_space}) != (
        _stable_payload_hash({"local_hilbert_space": expected_hilbert_space})
    ):
        raise ValueError(
            "auto-routed MCWF Carrier local_hilbert_space must match caller local_dims"
        )

    state = child.get("state_execution")
    summary = child.get("mcwf_mps_execution")
    if not isinstance(state, dict) or not isinstance(summary, dict):
        raise TypeError(
            "auto-routed MCWF Carrier state and execution summaries must be mappings"
        )
    _require_exact_summary_fields(
        state,
        _MCWF_CARRIER_STATE_EXECUTION_FIELDS,
        context="auto-routed MCWF Carrier state_execution",
    )
    _require_exact_summary_fields(
        summary,
        _MCWF_CARRIER_EXECUTION_SUMMARY_FIELDS,
        context="auto-routed MCWF Carrier mcwf_mps_execution",
    )
    summary_artifact_certification = summary.get(
        "dynamics_artifact_reference_certification"
    )
    if not isinstance(summary_artifact_certification, dict):
        raise TypeError(
            "auto-routed MCWF direct summary artifact certification must be a mapping"
        )
    if _stable_payload_hash(
        {"certification": summary_artifact_certification}
    ) != _stable_payload_hash(
        {"certification": trusted_artifact_certification}
    ):
        raise ValueError(
            "auto-routed MCWF direct summary artifact certification must match authority"
        )

    direct_schema = _require_manifest_text(
        summary,
        "schema",
        context="auto-routed MCWF Carrier direct summary",
    )
    if direct_schema != _RESTRICTED_EXECUTION_SCHEMAS["mcwf"]:
        raise ValueError("auto-routed MCWF Carrier direct schema is not registered")
    if state.get("evidence_schema") != direct_schema:
        raise ValueError(
            "auto-routed MCWF Carrier state evidence schema must match direct summary"
        )
    direct_hash = _require_manifest_text(
        summary,
        "content_hash",
        context="auto-routed MCWF Carrier direct summary",
    )
    if (
        len(direct_hash) != 64
        or any(char not in "0123456789abcdef" for char in direct_hash)
        or state.get("evidence_content_hash") != direct_hash
    ):
        raise ValueError(
            "auto-routed MCWF Carrier direct evidence hashes must be registered and equal"
        )
    if (
        summary.get("representability") != _MCWF_DIRECT_REPRESENTABILITY
        or state.get("representability") != _MCWF_DIRECT_REPRESENTABILITY
        or summary.get("backend_contract")
        != AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
    ):
        raise ValueError(
            "auto-routed MCWF Carrier direct identity is not registered"
        )
    for field, expected_value in (
        ("execution_status", execution_status),
        ("certification_status", certification_status),
        ("diagnostic_only", diagnostic_only),
        ("passed", passed),
        ("mcwf_mps_backend_executed", backend_executed),
    ):
        actual = summary.get(field)
        if actual != expected_value or type(actual) is not type(expected_value):
            raise ValueError(
                f"auto-routed MCWF Carrier direct summary {field} must match Carrier state"
            )
    for field in (
        "claims_exact_joint_lindblad_generator",
        "claims_dense_channel_evidence",
        "claims_production_scalable_backend",
    ):
        if _require_manifest_bool(
            summary,
            field,
            context="auto-routed MCWF Carrier direct summary",
        ):
            raise ValueError(
                f"auto-routed MCWF Carrier direct summary {field} must be false"
            )
    state_executed = _require_manifest_bool(
        state,
        "executed",
        context="auto-routed MCWF Carrier state_execution",
    )
    if state_executed is not backend_executed:
        raise ValueError(
            "auto-routed MCWF Carrier state execution must match backend state"
        )
    expected_reason = None if backend_executed else child.get("blocked_reason")
    if state.get("reason") != expected_reason:
        raise ValueError(
            "auto-routed MCWF Carrier state reason must match backend state"
        )
    state_initial_levels = state.get("initial_levels")
    if (
        type(state_initial_levels) is not list
        or state_initial_levels != expected["initial_levels"]
        or any(type(level) is not int for level in state_initial_levels)
    ):
        raise ValueError(
            "auto-routed MCWF Carrier state initial_levels must match caller request"
        )

    if backend_executed:
        expected_static_state = {
            "mps_library": "quimb.tensor.MatrixProductState",
            "array_backend": "torch_cuda_complex128",
            "unraveling_policy": "fixed_microstep_first_order_quantum_jump_mcwf",
        }
        for field, expected_value in expected_static_state.items():
            if state.get(field) != expected_value:
                raise ValueError(
                    f"auto-routed MCWF Carrier state {field} is not registered"
                )
        record_execution = child.get("record_execution")
        if not isinstance(record_execution, dict):
            raise TypeError(
                "auto-routed MCWF Carrier record_execution must be a mapping"
            )
        actual_measurement_policy = record_execution.get(
            "multilevel_measurement_policy"
        )
        if not isinstance(actual_measurement_policy, dict):
            raise TypeError(
                "auto-routed MCWF Carrier measurement policy must be a mapping"
            )
        pseudo_execution = {
            "trajectory_sampling": record_execution.get("trajectory_sampling"),
            "finite_step_policy": state.get("finite_step_policy"),
            "mps_truncation_ledger": state.get("mps_truncation_ledger"),
            "multilevel_measurement_policy": actual_measurement_policy,
            "initial_levels": state_initial_levels,
            "local_dims": local_hilbert_space.get("local_dims"),
        }
        _validate_mcwf_mps_child_execution_options(
            pseudo_execution,
            policy=policy,
            expected=expected,
        )
        _validate_auto_routed_mcwf_policy_evidence(
            policy=policy,
            record_execution=record_execution,
            ledger=state.get("mps_truncation_ledger"),
            expected=expected,
        )
    else:
        for field in ("mps_library", "array_backend", "unraveling_policy"):
            if state.get(field) is not None:
                raise ValueError(
                    f"auto-routed blocked MCWF Carrier state {field} must be None"
                )
        if state.get("finite_step_policy") != {} or state.get(
            "mps_truncation_ledger"
        ) != {}:
            raise ValueError(
                "auto-routed blocked MCWF Carrier state controls must be empty"
            )

    if passed:
        if expected["rng_seed"] is None:
            raise ValueError(
                "accepted auto-routed MCWF evidence requires a seeded direct execution"
            )
        trusted_direct, trusted_record_execution = (
            _trusted_seeded_mcwf_direct_authority(
                schedule,
                execution_backend_options=expected_execution_backend_options,
                device=expected_device,
            )
        )
        if (
            trusted_direct.get("passed") is not True
            or trusted_direct.get("content_hash") != direct_hash
        ):
            raise ValueError(
                "auto-routed MCWF summary must match the seeded direct MCWF execution"
            )
        actual_record_execution = child.get("record_execution")
        if not isinstance(actual_record_execution, dict):
            raise TypeError(
                "auto-routed MCWF Carrier record_execution must be a mapping"
            )
        if _stable_payload_hash(
            {"record_execution": actual_record_execution}
        ) != _stable_payload_hash(
            {"record_execution": trusted_record_execution}
        ):
            raise ValueError(
                "auto-routed MCWF Record summary must match the seeded direct MCWF execution"
            )
        trusted_policy = trusted_direct.get("restricted_acceptance_policy")
        if not isinstance(trusted_policy, dict) or _stable_payload_hash(
            {"policy": policy}
        ) != _stable_payload_hash({"policy": trusted_policy}):
            raise ValueError(
                "auto-routed MCWF policy must match the seeded direct MCWF execution"
            )


def _validate_auto_routed_mcwf_policy_evidence(
    *,
    policy: dict[str, Any],
    record_execution: dict[str, Any],
    ledger: Any,
    expected: dict[str, Any],
) -> None:
    """Cross-bind runtime probability/truncation evidence to public policy."""

    for field, expected_fields in (
        ("gross_strict_gate_split", _MCWF_POLICY_GROSS_STRICT_FIELDS),
        (
            "dense_jointL_record_certification",
            _MCWF_POLICY_DENSE_CERTIFICATION_FIELDS,
        ),
        ("trajectory", _MCWF_POLICY_TRAJECTORY_FIELDS),
        ("finite_step", _MCWF_POLICY_FINITE_STEP_FIELDS),
        ("mps_truncation", _MCWF_POLICY_TRUNCATION_FIELDS),
        ("probability", _MCWF_POLICY_PROBABILITY_FIELDS),
    ):
        nested = policy.get(field)
        if not isinstance(nested, dict):
            raise TypeError(
                f"auto-routed MCWF Carrier policy {field} must be a mapping"
            )
        _require_exact_summary_fields(
            nested,
            expected_fields,
            context=f"auto-routed MCWF Carrier policy {field}",
        )

    dense_certification = policy["dense_jointL_record_certification"]
    component_values = dense_certification.get("component_values")
    if dense_certification.get("comparison_object") == (
        _MCWF_JOINT_LEVEL_BINARY_COMPARISON_OBJECT
    ):
        expected_component_fields = {
            "declared_basis_eigenlabel_tv",
            "emitted_binary_record_tv",
        }
        if not isinstance(component_values, dict):
            raise TypeError(
                "auto-routed joint MCWF certification component_values must be a mapping"
            )
        if set(component_values) != expected_component_fields:
            raise ValueError(
                "auto-routed joint MCWF certification component_values fields "
                "must be exact"
            )
        normalized_components: list[float] = []
        for name in sorted(expected_component_fields):
            value = component_values[name]
            if (
                isinstance(value, bool)
                or not isinstance(value, Real)
                or not math.isfinite(float(value))
                or float(value) < 0.0
                or float(value) > 1.0
            ):
                raise ValueError(
                    "auto-routed joint MCWF certification component TV must lie in [0, 1]"
                )
            normalized_components.append(float(value))
        aggregate_value = dense_certification.get("value")
        if (
            isinstance(aggregate_value, bool)
            or not isinstance(aggregate_value, Real)
            or abs(float(aggregate_value) - max(normalized_components))
            > NUMERICAL_ZERO
        ):
            raise ValueError(
                "auto-routed joint MCWF certification value must equal the "
                "maximum component TV"
            )
    elif component_values is not None:
        raise ValueError(
            "auto-routed non-joint MCWF certification cannot carry component_values"
        )

    probability = policy.get("probability")
    jump_sampling = record_execution.get("jump_sampling")
    if not isinstance(probability, dict) or not isinstance(jump_sampling, dict):
        raise TypeError(
            "auto-routed MCWF Carrier probability and jump policies must be mappings"
        )
    runtime_residual = jump_sampling.get("probability_mass_residual_max")
    if (
        isinstance(runtime_residual, bool)
        or not isinstance(runtime_residual, Real)
        or not math.isfinite(float(runtime_residual))
        or float(runtime_residual) < 0.0
    ):
        raise ValueError(
            "auto-routed MCWF Carrier runtime mass residual must be finite and nonnegative"
        )
    residual_value = float(runtime_residual)
    residual_budget = expected["mass_residual_budget"]
    expected_within_budget = (
        None
        if residual_budget is None
        else residual_value <= float(residual_budget)
    )
    probability_mirrors = (
        ("runtime_candidate_mass_residual", residual_value),
        ("runtime_candidate_mass_residual_budget", residual_budget),
        ("runtime_candidate_mass_residual_is_finite_nonnegative", True),
        ("runtime_candidate_mass_residual_within_budget", expected_within_budget),
        ("runtime_candidate_mass_residual_required_for_restricted_acceptance", True),
        ("comparison_outcome_is_metric", False),
    )
    for field, expected_value in probability_mirrors:
        actual = probability.get(field)
        if actual != expected_value or type(actual) is not type(expected_value):
            raise ValueError(
                f"auto-routed MCWF Carrier probability policy {field} is not request-bound"
            )

    truncation = policy.get("mps_truncation")
    if not isinstance(truncation, dict) or not isinstance(ledger, dict):
        raise TypeError(
            "auto-routed MCWF Carrier truncation policy and ledger must be mappings"
        )
    from ..certify.axis1_mps import _mcwf_truncation_gate_result

    expected_gate = _mcwf_truncation_gate_result(
        ledger,
        worst_cut_discarded_weight_gate=expected[
            "worst_cut_discarded_weight_gate"
        ],
        total_discarded_weight_gate=expected["total_discarded_weight_gate"],
    )
    actual_gate = truncation.get("gate")
    if not isinstance(actual_gate, dict) or _stable_payload_hash(
        {"gate": actual_gate}
    ) != _stable_payload_hash({"gate": expected_gate}):
        raise ValueError(
            "auto-routed MCWF Carrier truncation gate must match ledger and caller gates"
        )
    for policy_field, ledger_field in (
        ("explicit_truncation_requested", "explicit_truncation_requested"),
        ("discarded_weight_sum", "discarded_weight_sum"),
        ("worst_cut_discarded_weight", "worst_cut_discarded_weight"),
    ):
        policy_value = truncation.get(policy_field)
        ledger_value = ledger.get(ledger_field)
        if policy_value != ledger_value or type(policy_value) is not type(
            ledger_value
        ):
            raise ValueError(
                f"auto-routed MCWF Carrier truncation {policy_field} must match ledger"
            )
    observed_total = expected_gate["observed_total_discarded_weight"]
    expected_truncation_detected = bool(
        observed_total is not None and observed_total > 0.0
    )
    actual_truncation_detected = _require_manifest_bool(
        truncation,
        "truncation_detected",
        context="auto-routed MCWF Carrier truncation policy",
    )
    if actual_truncation_detected is not expected_truncation_detected:
        raise ValueError(
            "auto-routed MCWF Carrier truncation_detected must match canonical "
            "discarded-weight evidence"
        )
    for field in (
        "accepted_as_production_error_bound",
        "comparison_outcome_is_metric",
    ):
        if _require_manifest_bool(
            truncation,
            field,
            context="auto-routed MCWF Carrier truncation policy",
        ):
            raise ValueError(
                f"auto-routed MCWF Carrier truncation policy {field} must be false"
            )
    if expected["max_bond"] is None:
        if (
            ledger.get("n_truncating_ops") != 0
            or ledger.get("discarded_weight_sum") != 0.0
            or ledger.get("worst_cut_discarded_weight") != 0.0
            or expected_truncation_detected
        ):
            raise ValueError(
                "auto-routed uncapped MCWF Carrier cannot report truncation loss"
            )


def _validate_auto_routed_mcwf_record_execution(
    child: dict[str, Any],
    *,
    schedule: SubstepSchedule,
    expected_execution: dict[str, Any],
) -> None:
    """Rebind a completed MCWF Carrier summary to the sealed Record layout."""

    backend_executed = _require_manifest_bool(
        child,
        "mcwf_mps_backend_executed",
        context="auto-routed Carrier child",
    )
    record_execution = child.get("record_execution")
    if not isinstance(record_execution, dict):
        raise TypeError(
            "auto-routed MCWF Carrier child record_execution must be a mapping"
        )
    _require_exact_summary_fields(
        record_execution,
        _MCWF_CARRIER_RECORD_EXECUTION_FIELDS,
        context="auto-routed MCWF Carrier record_execution",
    )
    record_executed = _require_manifest_bool(
        record_execution,
        "executed",
        context="auto-routed MCWF Carrier child record_execution",
    )
    if not backend_executed:
        expected_blocked_record = {
            "executed": False,
            "reason": child.get("blocked_reason"),
            "measurement_keys": [],
            "measurement_targets": [],
            "measurement_bases": [],
            "reset_after": [],
            "measurement_basis": None,
            "measurement_basis_semantics": None,
            "multilevel_measurement_policy": {},
            "measurement_records": [],
            "record_counts": [],
            "record_probabilities": [],
            "detector_records": [],
            "logical_observable_records": [],
            "trajectory_sampling": {},
            "jump_sampling": {},
            "claims_b8_artifact": False,
            "claims_decoder_integration": False,
        }
        if _stable_payload_hash(
            {"record_execution": record_execution}
        ) != _stable_payload_hash(
            {"record_execution": expected_blocked_record}
        ):
            raise ValueError(
                "auto-routed blocked MCWF Carrier Record summary must be canonical"
            )
        return

    layout = axis1_record_layout_from_schedule(schedule)
    if record_executed is not bool(layout.measurement_width):
        raise ValueError(
            "auto-routed MCWF Carrier child Record execution disagrees with the sealed layout"
        )
    expected_reason = None if record_executed else "schedule_has_no_measurement_substep"
    if record_execution.get("reason") != expected_reason:
        raise ValueError(
            "auto-routed MCWF Carrier child Record reason disagrees with execution state"
        )
    for field in ("claims_b8_artifact", "claims_decoder_integration"):
        if _require_manifest_bool(
            record_execution,
            field,
            context="auto-routed MCWF Carrier child record_execution",
        ):
            raise ValueError(
                f"auto-routed MCWF Carrier child record_execution {field} must be false"
            )
    expected_metadata = {
        "measurement_keys": list(layout.measurement_keys),
        "measurement_targets": list(layout.measurement_targets),
        "measurement_bases": list(layout.measurement_bases),
        "reset_after": list(layout.reset_after),
    }
    for field, expected in expected_metadata.items():
        actual = record_execution.get(field)
        if type(actual) is not list or len(actual) != len(expected):
            raise ValueError(
                f"auto-routed MCWF Carrier child {field} must match the sealed Record layout"
            )
        if any(
            type(actual_item) is not type(expected_item)
            or actual_item != expected_item
            for actual_item, expected_item in zip(actual, expected, strict=True)
        ):
            raise ValueError(
                f"auto-routed MCWF Carrier child {field} must match the sealed Record layout"
            )

    bases = expected_metadata["measurement_bases"]
    expected_basis_summary = (
        "none"
        if not bases
        else (
            "X"
            if all(basis == "X" for basis in bases)
            else (
                "Z"
                if all(basis == "Z" for basis in bases)
                else "mixed_pauli"
            )
        )
    )
    if record_execution.get("measurement_basis") != expected_basis_summary:
        raise ValueError(
            "auto-routed MCWF Carrier child measurement_basis disagrees with the sealed layout"
        )
    if record_execution.get("measurement_basis_semantics") != (
        _MCWF_MEASUREMENT_BASIS_SEMANTICS
    ):
        raise ValueError(
            "auto-routed MCWF Carrier child measurement_basis_semantics is not registered"
        )
    measurement_policy = record_execution.get("multilevel_measurement_policy")
    if not isinstance(measurement_policy, dict):
        raise TypeError(
            "auto-routed MCWF Carrier child multilevel_measurement_policy must be a mapping"
        )
    expected_measurement_policy = {
        "name": _MCWF_MEASUREMENT_POLICY_NAME,
        "bit_mapping": _MCWF_MEASUREMENT_BIT_MAPPING,
        "leaked_readout_b": expected_execution["leaked_readout_b"],
        "comparison_outcome_is_metric": False,
        "epistemic_class": "c",
    }
    if _stable_payload_hash({"policy": measurement_policy}) != _stable_payload_hash(
        {"policy": expected_measurement_policy}
    ):
        raise ValueError(
            "auto-routed MCWF Carrier child measurement policy is not canonical"
        )

    records = _require_exact_binary_record_matrix(
        record_execution.get("measurement_records"),
        field="measurement_records",
        context="auto-routed MCWF Carrier child",
    )
    record_tuples = [tuple(row) for row in records]
    if record_tuples != sorted(record_tuples) or len(record_tuples) != len(
        set(record_tuples)
    ):
        raise ValueError(
            "auto-routed MCWF Carrier child measurement_records must be sorted and unique"
        )
    projected = project_axis1_xor_records(layout, records)
    expected_projections = {
        "detector_records": [list(row) for row in projected.detector_records],
        "logical_observable_records": [
            list(row) for row in projected.observable_records
        ],
    }
    for field, expected in expected_projections.items():
        actual = _require_exact_binary_record_matrix(
            record_execution.get(field),
            field=field,
            context="auto-routed MCWF Carrier child",
        )
        if actual != expected:
            raise ValueError(
                f"auto-routed MCWF Carrier child {field} must match the sealed Record projection"
            )

    counts = record_execution.get("record_counts")
    probabilities = record_execution.get("record_probabilities")
    sampling = record_execution.get("trajectory_sampling")
    if type(counts) is not list or type(probabilities) is not list:
        raise TypeError(
            "auto-routed MCWF Carrier child Record counts and probabilities must be exact lists"
        )
    if not isinstance(sampling, dict):
        raise TypeError(
            "auto-routed MCWF Carrier child trajectory_sampling must be a mapping"
        )
    trajectory_count = sampling.get("trajectory_count")
    if type(trajectory_count) is not int or trajectory_count <= 0:
        raise ValueError(
            "auto-routed MCWF Carrier child trajectory_count must be a positive exact integer"
        )
    if trajectory_count != expected_execution["trajectory_count"]:
        raise ValueError(
            "auto-routed MCWF Carrier child trajectory_count must match caller request"
        )
    if not (len(records) == len(counts) == len(probabilities)):
        raise ValueError(
            "auto-routed MCWF Carrier child records, counts, and probabilities must align"
        )
    for index, (count, probability) in enumerate(
        zip(counts, probabilities, strict=True)
    ):
        if type(count) is not int or count <= 0:
            raise ValueError(
                f"auto-routed MCWF Carrier child record_counts[{index}] must be positive"
            )
        if (
            isinstance(probability, bool)
            or not isinstance(probability, Real)
            or not math.isfinite(float(probability))
            or float(probability) < 0.0
        ):
            raise ValueError(
                f"auto-routed MCWF Carrier child record_probabilities[{index}] is invalid"
            )
        expected_probability = float(count) / float(trajectory_count)
        if abs(float(probability) - expected_probability) > NUMERICAL_ZERO:
            raise ValueError(
                "auto-routed MCWF Carrier child Record probabilities must equal counts / trajectories"
            )
    if sum(counts) != trajectory_count:
        raise ValueError(
            "auto-routed MCWF Carrier child record_counts must sum to trajectory_count"
        )
    if abs(math.fsum(float(value) for value in probabilities) - 1.0) > NUMERICAL_ZERO:
        raise ValueError(
            "auto-routed MCWF Carrier child record probabilities must sum to one"
        )

    jump_sampling = record_execution.get("jump_sampling")
    if not isinstance(jump_sampling, dict):
        raise TypeError(
            "auto-routed MCWF Carrier child jump_sampling must be a mapping"
        )
    if set(jump_sampling) != {
        "max_jumps_per_microstep",
        "probability_mass_residual_max",
        "probability_mass_residual_mean",
        "probability_mass_residual_gate_role",
        "epistemic_class",
    }:
        raise ValueError(
            "auto-routed MCWF Carrier child jump_sampling fields are not canonical"
        )
    if jump_sampling.get("max_jumps_per_microstep") != 1:
        raise ValueError(
            "auto-routed MCWF Carrier child max_jumps_per_microstep must equal one"
        )
    residual_max = jump_sampling.get("probability_mass_residual_max")
    residual_mean = jump_sampling.get("probability_mass_residual_mean")
    for field, value in (
        ("probability_mass_residual_max", residual_max),
        ("probability_mass_residual_mean", residual_mean),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, Real)
            or not math.isfinite(float(value))
            or float(value) < 0.0
        ):
            raise ValueError(
                f"auto-routed MCWF Carrier child {field} must be finite and nonnegative"
            )
    if float(residual_mean) > float(residual_max) + NUMERICAL_ZERO:
        raise ValueError(
            "auto-routed MCWF Carrier child residual mean cannot exceed residual max"
        )
    if jump_sampling.get("probability_mass_residual_gate_role") != (
        "diagnostic_runtime_crosscheck_of_preflight_mass_residual_gate"
    ) or jump_sampling.get("epistemic_class") != "c":
        raise ValueError(
            "auto-routed MCWF Carrier child jump_sampling semantics are not registered"
        )


def _axis1_mcwf_mps_execution_manifest(
    schedule: SubstepSchedule,
    *,
    device: str,
    instrument_spec: Axis1ReadoutResetInstrumentSpec | None,
    execution_backend_options: dict[str, Any] | None,
    _return_record_binding: bool = False,
) -> dict[str, Any] | tuple[dict[str, Any], _Axis1McwfMpsRecordBinding]:
    """Execute or fail closed through the MCWF/MPS carrier endpoint."""

    if instrument_spec is not None:
        raise ValueError(
            "MCWF/MPS carrier execution does not support "
            "Axis1ReadoutResetInstrumentSpec in the first slice"
        )
    options = _validate_mcwf_mps_execution_options(execution_backend_options or {})
    device = normalize_mps_device(device)
    dev = _require_cuda_device(device)
    _validate_schedule_for_axis1_channel_evidence(
        schedule,
        allow_multilevel_leakage_context=True,
    )
    program = axis1_carrier_program_manifest(
        schedule,
        backend_contract=AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT,
    )
    expected = _mcwf_mps_expected_options(
        options,
        num_sites=int(schedule.num_qubits),
    )
    from .axis1_mcwf_mps_execution import (
        AXIS1_MCWF_MPS_EXECUTION_REPRESENTABILITY,
        _blocked_acceptance_policy,
        axis1_mcwf_mps_state_record_execution_manifest,
    )

    mcwf_mps = axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        device=dev,
        **options,
    )
    _validate_child_content_hash(mcwf_mps, context="MCWF/MPS child")
    _require_exact_summary_fields(
        mcwf_mps,
        _MCWF_DIRECT_CHILD_FIELDS,
        context="MCWF/MPS direct child",
    )
    if mcwf_mps.get("source_kind") != schedule.source_kind:
        raise ValueError("MCWF/MPS child source_kind must match the requested schedule")
    if mcwf_mps.get("source_hash") != schedule.source_hash:
        raise ValueError("MCWF/MPS child source_hash must match the requested schedule")
    if mcwf_mps.get("schedule_representability") != schedule.representability:
        raise ValueError(
            "MCWF/MPS child schedule_representability must match the schedule"
        )
    if mcwf_mps.get("representability") != (
        AXIS1_MCWF_MPS_EXECUTION_REPRESENTABILITY
    ):
        raise ValueError("MCWF/MPS child representability is not registered")
    if mcwf_mps.get("backend_contract") != (
        AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
    ):
        raise ValueError("MCWF/MPS child backend_contract is not registered")
    if mcwf_mps.get("gpu_required") is not True:
        raise ValueError("MCWF/MPS child gpu_required must be true")
    if mcwf_mps.get("device") != dev:
        raise ValueError("MCWF/MPS child device must match the requested device")
    if mcwf_mps.get("carrier_program") != _restricted_mps_program_summary(program):
        raise ValueError(
            "MCWF/MPS child carrier_program must match the requested schedule"
        )
    _validate_mcwf_mps_child_options(
        mcwf_mps,
        expected=expected,
    )
    raw_execution = mcwf_mps.get("mps_execution")
    execution = raw_execution or {}
    passed = _require_manifest_bool(mcwf_mps, "passed", context="MCWF/MPS execution")
    child_verdict = _require_manifest_text(
        mcwf_mps, "verdict", context="MCWF/MPS execution"
    )
    if child_verdict != ("pass" if passed else "fail"):
        raise ValueError("MCWF/MPS child verdict must agree with its passed field")
    child_schema = _require_manifest_text(
        mcwf_mps,
        "schema",
        context="MCWF/MPS execution",
    )
    if child_schema != _RESTRICTED_EXECUTION_SCHEMAS["mcwf"]:
        raise ValueError("MCWF/MPS execution schema is not registered")
    executed = _require_manifest_bool(
        mcwf_mps,
        "mcwf_mps_backend_executed",
        context="MCWF/MPS execution",
    )
    claimed_execution = _require_manifest_bool(
        mcwf_mps,
        "claims_mcwf_mps_backend_execution",
        context="MCWF/MPS execution",
    )
    if claimed_execution is not executed:
        raise ValueError(
            "MCWF/MPS backend execution claim must equal actual backend state"
        )
    trusted_artifact_certification, trusted_blocked_reason = (
        _trusted_mcwf_artifact_authority(
            program,
            expected=expected,
            device=dev,
        )
    )
    artifact_certification = mcwf_mps.get(
        "dynamics_artifact_reference_certification"
    )
    if not isinstance(artifact_certification, dict):
        raise TypeError(
            "MCWF/MPS dynamics artifact reference certification must be a mapping"
        )
    if _stable_payload_hash(
        {"certification": artifact_certification}
    ) != _stable_payload_hash(
        {"certification": trusted_artifact_certification}
    ):
        raise ValueError(
            "MCWF/MPS artifact certification must match sealed-input authority"
        )
    if executed and trusted_blocked_reason is not None:
        raise ValueError(
            "MCWF/MPS child executed despite a sealed-input preflight blocker"
        )
    for field in (
        "claims_production_scalable_backend",
        "claims_exact_joint_lindblad_generator",
        "claims_dense_channel_evidence",
        "claims_dem_decoder_semantics",
        "claims_axis2_source_timeline",
    ):
        if _require_manifest_bool(
            mcwf_mps,
            field,
            context="MCWF/MPS execution",
        ):
            raise ValueError(f"MCWF/MPS child {field} must be false")
    acceptance = mcwf_mps.get("restricted_acceptance_policy")
    if not isinstance(acceptance, dict):
        raise TypeError("MCWF/MPS restricted_acceptance_policy must be a mapping")
    accepted = _require_manifest_bool(
        acceptance,
        "accepted_for_restricted_execution",
        context="MCWF/MPS restricted acceptance policy",
    )
    if passed is not accepted:
        raise ValueError(
            "MCWF/MPS execution passed must equal accepted_for_restricted_execution"
        )
    policy_artifact_certification = acceptance.get(
        "dynamics_artifact_reference_certification"
    )
    if not isinstance(policy_artifact_certification, dict):
        raise TypeError(
            "MCWF/MPS policy artifact certification must be a mapping"
        )
    if _stable_payload_hash(
        {"certification": policy_artifact_certification}
    ) != _stable_payload_hash(
        {"certification": trusted_artifact_certification}
    ):
        raise ValueError(
            "MCWF/MPS policy artifact certification must match sealed-input authority"
        )
    execution_status = _require_manifest_text(
        mcwf_mps, "execution_status", context="MCWF/MPS execution"
    )
    certification_status = _require_manifest_text(
        mcwf_mps, "certification_status", context="MCWF/MPS execution"
    )
    diagnostic_only = _require_manifest_bool(
        mcwf_mps, "diagnostic_only", context="MCWF/MPS execution"
    )
    _validate_restricted_child_state_machine(
        passed=passed,
        child_verdict=child_verdict,
        backend_executed=executed,
        execution_status=execution_status,
        certification_status=certification_status,
        diagnostic_only=diagnostic_only,
        blocked_reason=mcwf_mps.get("blocked_reason"),
        context="MCWF/MPS",
    )
    _validate_restricted_policy_state(
        acceptance,
        execution_status=execution_status,
        certification_status=certification_status,
        diagnostic_only=diagnostic_only,
        blocked_reason=mcwf_mps.get("blocked_reason"),
        context="MCWF/MPS",
        route_kind="mcwf",
    )
    if not executed:
        if raw_execution is not None:
            raise ValueError(
                "MCWF/MPS blocked child mps_execution must be canonical None"
            )
        if execution_status != "blocked":
            raise ValueError(
                "MCWF/MPS non-executed child must be a canonical blocked child"
            )
        expected_blocked_reason = trusted_blocked_reason
        if expected_blocked_reason is None:
            raise ValueError(
                "MCWF/MPS child reported blocked without a trusted preflight blocker"
            )
        if mcwf_mps.get("blocked_reason") != expected_blocked_reason:
            raise ValueError(
                "MCWF/MPS child blocked_reason must match trusted preflight"
            )
        canonical_blocked_policy = _blocked_acceptance_policy(
            blocked_reason=expected_blocked_reason,
            rng_seed=expected["rng_seed"],
            trajectory_count=expected["trajectory_count"],
            dynamics_artifact_reference_certification=(
                trusted_artifact_certification
            ),
        )
        if _stable_payload_hash(
            {"policy": acceptance}
        ) != _stable_payload_hash(
            {"policy": canonical_blocked_policy}
        ):
            raise ValueError(
                "MCWF/MPS blocked child restricted_acceptance_policy must be canonical"
            )
    if executed:
        if not isinstance(execution, dict):
            raise TypeError("MCWF/MPS child mps_execution must be a mapping")
        for field in ("claims_b8_artifact", "claims_decoder_integration"):
            if _require_manifest_bool(
                execution,
                field,
                context="MCWF/MPS child mps_execution",
            ):
                raise ValueError(f"MCWF/MPS child mps_execution {field} must be false")
        sampling = execution.get("trajectory_sampling")
        if not isinstance(sampling, dict):
            raise TypeError(
                "MCWF/MPS child trajectory_sampling must be a mapping"
            )
        actual_trajectory_mode = _require_manifest_text(
            sampling,
            "mode",
            context="MCWF/MPS child trajectory_sampling",
        )
        if actual_trajectory_mode != acceptance["trajectory"]["mode"]:
            raise ValueError(
                "MCWF/MPS policy trajectory mode must match actual child execution"
            )
        _validate_mcwf_mps_child_execution_options(
            execution,
            policy=acceptance,
            expected=expected,
        )
        record_layout = axis1_record_layout_from_schedule(schedule)
        expected_record_metadata = {
            "measurement_keys": list(record_layout.measurement_keys),
            "measurement_targets": list(record_layout.measurement_targets),
            "measurement_bases": list(record_layout.measurement_bases),
            "reset_after": list(record_layout.reset_after),
        }
        for field, expected_value in expected_record_metadata.items():
            actual_value = execution.get(field)
            if type(actual_value) is not list or actual_value != expected_value:
                raise ValueError(
                    f"MCWF/MPS child {field} must match the sealed schedule Record layout"
                )
        bases = expected_record_metadata["measurement_bases"]
        expected_basis_summary = (
            "none"
            if not bases
            else (
                "X"
                if all(basis == "X" for basis in bases)
                else (
                    "Z"
                    if all(basis == "Z" for basis in bases)
                    else "mixed_pauli"
                )
            )
        )
        if execution.get("measurement_basis") != expected_basis_summary:
            raise ValueError(
                "MCWF/MPS child measurement_basis must summarize the sealed layout"
            )
        if execution.get("measurement_basis_semantics") != (
            "measurement_bases and reset_after are schedule-ordered one-per-Record-column; "
            "X measurement rotates into Z, projects, then rotates back unless reset prepares |+>"
        ):
            raise ValueError(
                "MCWF/MPS child measurement_basis_semantics is not registered"
            )
        from ..certify.axis1_mps import (
            _validate_metric_family_execution_payload,
            dense_jointL_record_certification,
            restricted_acceptance_policy,
        )

        _validate_metric_family_execution_payload(
            execution,
            sampled=True,
            trajectory_count=expected["trajectory_count"],
            declared_local_dims=expected["local_dims"],
            program=program,
        )
        _validate_axis1_projected_record_payload(
            record_layout,
            execution,
            context="MCWF/MPS child",
        )
        if expected["mass_residual_budget"] is None:
            certification = {
                "executed": False,
                "passed": False,
                "passed_gross": False,
                "reason": "mass_residual_budget_not_declared_diagnostic_only",
                "comparison_outcome_is_metric": False,
                "epistemic_class": "c",
            }
        else:
            certification = dense_jointL_record_certification(
                schedule,
                execution,
                program,
                declared_local_dims=expected["local_dims"],
                device=dev,
            )
        canonical_acceptance = restricted_acceptance_policy(
            execution=execution,
            certification=certification,
            program=program,
            declared_local_dims=expected["local_dims"],
            rng_seed=expected["rng_seed"],
            trajectory_count=expected["trajectory_count"],
            mass_residual_budget=expected["mass_residual_budget"],
            worst_cut_discarded_weight_gate=(
                expected["worst_cut_discarded_weight_gate"]
            ),
            total_discarded_weight_gate=expected["total_discarded_weight_gate"],
            dynamics_artifact_reference_certification=(
                trusted_artifact_certification
            ),
        )
        if _stable_payload_hash({"policy": acceptance}) != _stable_payload_hash(
            {"policy": canonical_acceptance}
        ):
            raise ValueError(
                "MCWF/MPS child restricted_acceptance_policy must equal the "
                "canonical restricted acceptance policy independently recomputed "
                "from the requested schedule, options, execution, and dense metric"
            )
    record_execution_summary = _mcwf_carrier_record_execution_summary(
        mcwf_mps,
        execution,
        executed=executed,
    )
    payload: dict[str, Any] = {
        "schema": AXIS1_CARRIER_EXECUTION_SCHEMA,
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "representability": AXIS1_CARRIER_MCWF_MPS_EXECUTION_REPRESENTABILITY,
        "execution_backend_contract": (
            AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
        ),
        "gpu_required": True,
        "device": dev,
        "execution_backend_options": _jsonable(options),
        "execution_status": execution_status,
        "certification_status": certification_status,
        "diagnostic_only": diagnostic_only,
        "verdict": "pass" if passed else "fail",
        "passed": passed,
        "blocked_reason": mcwf_mps.get("blocked_reason"),
        "dense_probe_executed": False,
        "qt_mps_backend_executed": False,
        "mcwf_mps_backend_executed": executed,
        "qutip_cuquantum_probe_executed": False,
        "carrier_program": dict(mcwf_mps["carrier_program"]),
        "local_hilbert_space": dict(mcwf_mps.get("local_hilbert_space", {})),
        "state_execution": {
            "executed": executed,
            "reason": None if executed else mcwf_mps.get("blocked_reason"),
            "evidence_schema": mcwf_mps.get("schema"),
            "evidence_content_hash": mcwf_mps.get("content_hash"),
            "representability": mcwf_mps.get("representability"),
            "mps_library": execution.get("mps_library"),
            "array_backend": execution.get("array_backend"),
            "unraveling_policy": execution.get("unraveling_policy"),
            "initial_levels": list(mcwf_mps.get("initial_levels", ())),
            "finite_step_policy": dict(execution.get("finite_step_policy", {})),
            "mps_truncation_ledger": dict(execution.get("mps_truncation_ledger", {})),
        },
        "record_execution": record_execution_summary,
        "mcwf_mps_execution": {
            "schema": mcwf_mps.get("schema"),
            "content_hash": mcwf_mps.get("content_hash"),
            "representability": mcwf_mps.get("representability"),
            "backend_contract": mcwf_mps.get("backend_contract"),
            "execution_status": execution_status,
            "certification_status": certification_status,
            "diagnostic_only": diagnostic_only,
            "passed": passed,
            "mcwf_mps_backend_executed": executed,
            "claims_exact_joint_lindblad_generator": _require_manifest_bool(
                mcwf_mps,
                "claims_exact_joint_lindblad_generator",
                context="MCWF/MPS execution",
            ),
            "claims_dense_channel_evidence": _require_manifest_bool(
                mcwf_mps,
                "claims_dense_channel_evidence",
                context="MCWF/MPS execution",
            ),
            "claims_production_scalable_backend": _require_manifest_bool(
                mcwf_mps,
                "claims_production_scalable_backend",
                context="MCWF/MPS execution",
            ),
            "dynamics_artifact_reference_certification": dict(
                trusted_artifact_certification
            ),
        },
        "dynamics_artifact_reference_certification": dict(
            trusted_artifact_certification
        ),
        "restricted_acceptance_policy": dict(
            mcwf_mps.get("restricted_acceptance_policy", {})
        ),
        "claims_mcwf_mps_backend_execution": executed,
        "claims_qt_mps_backend_execution": False,
        "claims_qutip_cuquantum_execution": False,
        "claims_production_scalable_backend": False,
        "claims_scalable_backend_completed": False,
        "claims_exact_joint_lindblad_generator": False,
        "claims_dense_channel_evidence": False,
        "claims_dem_decoder_semantics": False,
        "claims_axis2_source_timeline": False,
        "scored_quantity_policy": (
            "MCWF/MPS execution/fail-closed carrier wrapper; no new scored quantity"
        ),
        "epistemic_classes": {
            "program_consumption": "a",
            "mcwf_mps_execution_contract": "a/c",
            "backend_execution_status": "a",
            "production_backend_status": "a",
            "dem_decoder_non_claim": "a",
        },
        "scope": (
            "Axis-1 carrier execution endpoint for the MCWF/MPS backend; first "
            "slice executes fixed-microstep MCWF/MPS with declared local_dims "
            "and fails closed for multilevel finite-bond ledgers, with no dense "
            "fallback, no DEM/decoder semantics, and no Axis-2 source timeline"
        ),
    }
    payload["content_hash"] = _streaming_stable_payload_hash(payload)
    if _return_record_binding:
        direct_content_hash = _require_manifest_text(
            mcwf_mps,
            "content_hash",
            context="MCWF/MPS same-call Record binding",
        )
        binding = _Axis1McwfMpsRecordBinding(
            carrier_content_hash=payload["content_hash"],
            direct_content_hash=direct_content_hash,
            record_execution_content_hash=_streaming_stable_payload_hash(
                {"record_execution": record_execution_summary}
            ),
            restricted_acceptance_policy_content_hash=_streaming_stable_payload_hash(
                {"policy": mcwf_mps["restricted_acceptance_policy"]}
            ),
        )
        return payload, binding
    return payload


def _axis1_qt_mps_restricted_execution_manifest(
    schedule: SubstepSchedule,
    *,
    device: str,
    instrument_spec: Axis1ReadoutResetInstrumentSpec | None,
    execution_backend_options: dict[str, Any] | None,
) -> dict[str, Any]:
    """Execute the restricted QT/MPS carrier backend through the carrier seam."""

    if instrument_spec is not None:
        raise ValueError(
            "QT/MPS restricted carrier execution does not support "
            "Axis1ReadoutResetInstrumentSpec; use dense_jointL_probe for the "
            "small-N instrument path"
        )
    device = normalize_mps_device(device)
    _validate_schedule_for_axis1_channel_evidence(schedule)
    program = axis1_carrier_program_manifest(
        schedule,
        backend_contract=AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT,
    )
    carrier_summary = _carrier_program_summary(program)
    qt_mps_options = _validate_qt_mps_backend_options(execution_backend_options or {})
    from .axis1_qt_mps_execution import (
        _record_materialization_preflight_for_schedule,
        _validate_qt_restricted_child,
        axis1_qt_mps_restricted_execution_manifest,
    )
    qt_mps = axis1_qt_mps_restricted_execution_manifest(
        schedule,
        device=device,
        **qt_mps_options,
    )
    expected = _qt_mps_expected_options(qt_mps_options)
    expected_preflight = _record_materialization_preflight_for_schedule(
        schedule,
        max_record_materialization_outcomes=expected[
            "max_record_materialization_outcomes"
        ],
        trajectory_count=expected["trajectory_count"],
    )
    _validate_qt_restricted_child(
        qt_mps,
        context="QT/MPS Carrier child",
        expected_trajectory_mode=(
            _QT_SAMPLED_TRAJECTORY_MODE
            if expected["trajectory_count"] is not None
            else _QT_EXACT_TRAJECTORY_MODE
        ),
        expected_schedule=schedule,
        expected_source_kind=schedule.source_kind,
        expected_source_hash=schedule.source_hash,
        expected_schedule_representability=schedule.representability,
        expected_carrier_program=_restricted_mps_program_summary(program),
        expected_device=device,
        expected_max_bond=expected["max_bond"],
        expected_max_branches=expected["max_branches"],
        expected_record_budget=expected["max_record_materialization_outcomes"],
        expected_record_materialization_preflight=expected_preflight,
        expected_record_layout=axis1_record_layout_from_schedule(schedule),
        expected_microstep_count=expected["microstep_count"],
        expected_finite_step_order=expected["finite_step_order"],
        expected_trajectory_count=expected["trajectory_count"],
        expected_rng_seed=expected["rng_seed"],
        expected_worst_cut_discarded_weight_gate=expected[
            "worst_cut_discarded_weight_gate"
        ],
        expected_total_discarded_weight_gate=expected[
            "total_discarded_weight_gate"
        ],
        expected_dense_oracle_certification=expected[
            "dense_oracle_certification"
        ],
    )
    if qt_mps.get("carrier_program") != _restricted_mps_program_summary(program):
        raise ValueError(
            "QT/MPS child carrier_program must match the requested schedule"
        )
    dev = qt_mps.get("device")
    if not isinstance(dev, str) or not dev:
        raise TypeError("QT/MPS execution manifest device must be a nonempty string")
    if dev != device:
        raise ValueError("QT/MPS child device must match the requested device")
    acceptance = qt_mps.get("restricted_acceptance_policy")
    if not isinstance(acceptance, dict):
        raise TypeError("QT/MPS restricted_acceptance_policy must be a mapping")
    certification = qt_mps.get("dense_jointL_record_certification")
    if not isinstance(certification, dict):
        raise TypeError("QT/MPS dense_jointL_record_certification must be a mapping")
    dense_probe_executed = _require_manifest_bool(
        certification,
        "executed",
        context="QT/MPS dense certification",
    )
    if dense_probe_executed or "passed" in certification:
        _require_manifest_bool(
            certification,
            "passed",
            context="QT/MPS dense certification",
        )
    passed = _require_manifest_bool(qt_mps, "passed", context="QT/MPS execution")
    child_verdict = _require_manifest_text(
        qt_mps, "verdict", context="QT/MPS execution"
    )
    child_schema = _require_manifest_text(
        qt_mps,
        "schema",
        context="QT/MPS execution",
    )
    if child_schema != _RESTRICTED_EXECUTION_SCHEMAS["qt"]:
        raise ValueError("QT/MPS execution schema is not registered")
    accepted = _require_manifest_bool(
        acceptance,
        "accepted_for_restricted_execution",
        context="QT/MPS restricted acceptance policy",
    )
    if passed is not accepted:
        raise ValueError(
            "QT/MPS execution passed must equal "
            "accepted_for_restricted_execution"
        )
    execution_status = _require_manifest_text(
        qt_mps, "execution_status", context="QT/MPS execution"
    )
    certification_status = _require_manifest_text(
        qt_mps, "certification_status", context="QT/MPS execution"
    )
    diagnostic_only = _require_manifest_bool(
        qt_mps, "diagnostic_only", context="QT/MPS execution"
    )
    qt_backend_executed = _require_manifest_bool(
        qt_mps,
        "qt_mps_backend_executed",
        context="QT/MPS execution",
    )
    _validate_restricted_child_state_machine(
        passed=passed,
        child_verdict=child_verdict,
        backend_executed=qt_backend_executed,
        execution_status=execution_status,
        certification_status=certification_status,
        diagnostic_only=diagnostic_only,
        blocked_reason=qt_mps.get("blocked_reason"),
        context="QT/MPS",
    )
    claims_qt_backend_execution = _require_manifest_bool(
        qt_mps,
        "claims_qt_mps_backend_execution",
        context="QT/MPS execution",
    )
    if claims_qt_backend_execution is not qt_backend_executed:
        raise ValueError(
            "QT/MPS backend execution claim must equal actual backend state"
        )
    _validate_restricted_policy_state(
        acceptance,
        execution_status=execution_status,
        certification_status=certification_status,
        diagnostic_only=diagnostic_only,
        blocked_reason=qt_mps.get("blocked_reason"),
        context="QT/MPS",
        route_kind="qt",
    )
    if qt_backend_executed:
        execution = qt_mps.get("mps_execution")
        if not isinstance(execution, dict):
            raise TypeError("QT/MPS child mps_execution must be a mapping")
        sampling = execution.get("trajectory_sampling")
        if not isinstance(sampling, dict):
            raise TypeError("QT/MPS child trajectory_sampling must be a mapping")
        actual_trajectory_mode = _require_manifest_text(
            sampling,
            "mode",
            context="QT/MPS child trajectory_sampling",
        )
        if actual_trajectory_mode != acceptance["trajectory"]["mode"]:
            raise ValueError(
                "QT/MPS policy trajectory mode must match actual child execution"
            )
    payload: dict[str, Any] = {
        "schema": AXIS1_CARRIER_EXECUTION_SCHEMA,
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "representability": AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_REPRESENTABILITY,
        "execution_backend_contract": (
            AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT
        ),
        "gpu_required": True,
        "device": dev,
        "carrier_program": carrier_summary,
        "execution_backend_options": _jsonable(qt_mps_options),
        "execution_status": execution_status,
        "certification_status": certification_status,
        "diagnostic_only": diagnostic_only,
        "verdict": "pass" if passed else "fail",
        "passed": passed,
        "blocked_reason": qt_mps.get("blocked_reason"),
        "dense_probe_executed": dense_probe_executed,
        "qt_mps_backend_executed": qt_backend_executed,
        "qutip_cuquantum_probe_executed": False,
        "state_execution": _qt_mps_state_execution_summary(qt_mps),
        "record_execution": _qt_mps_record_execution_summary(qt_mps),
        "qt_mps_execution": _qt_mps_execution_summary(qt_mps),
        "dense_jointL_record_certification": dict(
            qt_mps.get("dense_jointL_record_certification", {})
        ),
        "restricted_acceptance_policy": dict(
            qt_mps.get("restricted_acceptance_policy", {})
        ),
        "claims_dense_channel_evidence": False,
        "claims_dem_decoder_semantics": False,
        "claims_axis2_source_timeline": False,
        "claims_scalable_backend_completed": False,
        "claims_production_scalable_backend": False,
        "claims_qt_mps_backend_execution": qt_backend_executed,
        "claims_qutip_cuquantum_execution": False,
        "claims_exact_joint_lindblad_generator": False,
        "scored_quantity_policy": (
            "restricted QT/MPS carrier execution is a verification gate only; "
            "no new scored quantity"
        ),
        "epistemic_classes": {
            "program_consumption": "a",
            "restricted_qt_mps_execution": "c",
            "dense_oracle_certification": "a/c",
            "production_backend_status": "a",
            "dem_decoder_non_claim": "a",
        },
        "scope": (
            "restricted QT/MPS state/record execution through the carrier seam; "
            "no dense channel payload, no DEM/decoder semantics, no Axis-2 source "
            "timeline, no exact joint-Lindblad generator claim, no production "
            "scalable backend claim"
        ),
    }
    payload["content_hash"] = _stable_payload_hash(payload)
    return payload


def _validate_mcwf_mps_execution_options(options: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "finite_step_order",
        "initial_levels",
        "leaked_readout_b",
        "local_dims",
        "max_bond",
        "mass_residual_budget",
        "microstep_count",
        "rng_seed",
        "total_discarded_weight_gate",
        "trajectory_count",
        "worst_cut_discarded_weight_gate",
    }
    unknown = sorted(set(options) - allowed)
    if unknown:
        joined = ", ".join(unknown)
        raise ValueError(f"unsupported MCWF/MPS execution options: {joined}")
    out = dict(options)
    if "local_dims" in out:
        if out["local_dims"] is None:
            out.pop("local_dims")
        else:
            out["local_dims"] = list(
                normalize_mps_index_sequence(
                    out["local_dims"],
                    name="local_dims",
                    minimum=2,
                )
            )
    if "initial_levels" in out:
        if out["initial_levels"] is None:
            out.pop("initial_levels")
        else:
            out["initial_levels"] = list(
                normalize_mps_index_sequence(
                    out["initial_levels"],
                    name="initial_levels",
                    minimum=0,
                )
            )
    if "leaked_readout_b" in out:
        out["leaked_readout_b"] = normalize_mps_finite_real(
            out["leaked_readout_b"],
            name="leaked_readout_b",
            minimum=0.0,
            maximum=1.0,
        )
    if "max_bond" in out and out["max_bond"] is not None:
        out["max_bond"] = normalize_mps_max_bond(
            out["max_bond"], allow_none=False
        )
    if "microstep_count" in out:
        out["microstep_count"] = normalize_mps_index(
            out["microstep_count"],
            name="microstep_count",
            minimum=1,
        )
    if "trajectory_count" in out:
        out["trajectory_count"] = normalize_mps_index(
            out["trajectory_count"],
            name="trajectory_count",
            minimum=1,
        )
    if "rng_seed" in out and out["rng_seed"] is not None:
        out["rng_seed"] = normalize_optional_mps_index(
            out["rng_seed"],
            name="rng_seed",
        )
    if "finite_step_order" in out:
        out["finite_step_order"] = normalize_mps_choice(
            out["finite_step_order"],
            name="finite_step_order",
            choices=(
                "first_order",
                "symmetric_hamiltonian_first_order_collapse",
            ),
        )
    for name in (
        "mass_residual_budget",
        "total_discarded_weight_gate",
        "worst_cut_discarded_weight_gate",
    ):
        if name in out and out[name] is not None:
            out[name] = normalize_mps_finite_real(
                out[name],
                name=name,
                minimum=0.0,
            )
    if out.get("mass_residual_budget") == 0.0:
        raise ValueError("mass_residual_budget must be positive when provided")
    return out


def _mcwf_mps_expected_options(
    requested: dict[str, Any],
    *,
    num_sites: int,
) -> dict[str, Any]:
    expected = {
        "local_dims": [2] * num_sites,
        "initial_levels": [0] * num_sites,
        "leaked_readout_b": 1.0,
        "max_bond": None,
        "worst_cut_discarded_weight_gate": None,
        "total_discarded_weight_gate": None,
        "microstep_count": 1,
        "mass_residual_budget": 0.1,
        "finite_step_order": "first_order",
        "trajectory_count": 1,
        "rng_seed": None,
    }
    expected.update(requested)
    return expected


def _validate_mcwf_mps_child_options(
    child: dict[str, Any],
    *,
    expected: dict[str, Any],
) -> None:
    for option_name, expected_value in expected.items():
        actual_value = (
            child.get("local_hilbert_space", {}).get("local_dims")
            if option_name == "local_dims"
            else child.get(option_name)
        )
        if (
            actual_value != expected_value
            or type(actual_value) is not type(expected_value)
        ):
            raise ValueError(
                f"MCWF/MPS child {option_name} must match the requested option"
            )


def _validate_mcwf_mps_child_execution_options(
    execution: dict[str, Any],
    *,
    policy: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    sampling = execution.get("trajectory_sampling")
    if not isinstance(sampling, dict):
        raise TypeError("MCWF/MPS child trajectory_sampling must be a mapping")
    _require_exact_summary_fields(
        sampling,
        _MCWF_TRAJECTORY_SAMPLING_FIELDS,
        context="MCWF/MPS child trajectory_sampling",
    )
    expected_seed = 0 if expected["rng_seed"] is None else expected["rng_seed"]
    mirrors = (
        (sampling, "trajectory_count", expected["trajectory_count"], "trajectory_sampling"),
        (sampling, "rng_seed", expected_seed, "trajectory_sampling"),
        (
            sampling,
            "rng_seed_was_explicit",
            expected["rng_seed"] is not None,
            "trajectory_sampling",
        ),
        (
            sampling,
            "measurement_sampling_policy",
            _MCWF_MEASUREMENT_SAMPLING_POLICY,
            "trajectory_sampling",
        ),
        (
            sampling,
            "record_support_policy",
            _MCWF_RECORD_SUPPORT_POLICY,
            "trajectory_sampling",
        ),
        (
            sampling,
            "zero_frequency_records_emitted",
            False,
            "trajectory_sampling",
        ),
    )
    finite_step = execution.get("finite_step_policy")
    if not isinstance(finite_step, dict):
        raise TypeError("MCWF/MPS child finite_step_policy must be a mapping")
    _require_exact_summary_fields(
        finite_step,
        _MCWF_FINITE_STEP_POLICY_FIELDS,
        context="MCWF/MPS child finite_step_policy",
    )
    mirrors += (
        (finite_step, "order", expected["finite_step_order"], "finite_step_policy"),
        (
            finite_step,
            "microstep_count",
            expected["microstep_count"],
            "finite_step_policy",
        ),
    )
    ledger = execution.get("mps_truncation_ledger")
    if not isinstance(ledger, dict):
        raise TypeError("MCWF/MPS child mps_truncation_ledger must be a mapping")
    expected_ledger_fields = _MCWF_CAPPED_TRUNCATION_LEDGER_FIELDS
    if expected["max_bond"] is None:
        expected_ledger_fields = _MCWF_UNCAPPED_TRUNCATION_LEDGER_FIELDS
        if any(int(dim) != 2 for dim in expected["local_dims"]):
            expected_ledger_fields = expected_ledger_fields | {"local_dims"}
    _require_exact_summary_fields(
        ledger,
        frozenset(expected_ledger_fields),
        context="MCWF/MPS child mps_truncation_ledger",
    )
    explicit_truncation = _require_manifest_bool(
        ledger,
        "explicit_truncation_requested",
        context="MCWF/MPS child mps_truncation_ledger",
    )
    if explicit_truncation != (expected["max_bond"] is not None):
        raise ValueError(
            "MCWF/MPS child mps_truncation_ledger explicit-truncation state "
            "must match max_bond"
        )
    if expected["max_bond"] is None:
        if "max_bond" in ledger:
            raise ValueError(
                "MCWF/MPS uncapped child ledger cannot carry max_bond"
            )
    else:
        mirrors += (
            (ledger, "max_bond", expected["max_bond"], "mps_truncation_ledger"),
        )
    measurement_policy = execution.get("multilevel_measurement_policy")
    if not isinstance(measurement_policy, dict):
        raise TypeError(
            "MCWF/MPS child multilevel_measurement_policy must be a mapping"
        )
    mirrors += (
        (
            measurement_policy,
            "name",
            _MCWF_MEASUREMENT_POLICY_NAME,
            "multilevel_measurement_policy",
        ),
        (
            measurement_policy,
            "bit_mapping",
            _MCWF_MEASUREMENT_BIT_MAPPING,
            "multilevel_measurement_policy",
        ),
        (
            measurement_policy,
            "leaked_readout_b",
            expected["leaked_readout_b"],
            "multilevel_measurement_policy",
        ),
        (execution, "initial_levels", expected["initial_levels"], "mps_execution"),
        (execution, "local_dims", expected["local_dims"], "mps_execution"),
    )
    trajectory_policy = policy.get("trajectory")
    if not isinstance(trajectory_policy, dict):
        raise TypeError("MCWF/MPS policy trajectory must be a mapping")
    mirrors += (
        (
            trajectory_policy,
            "trajectory_count",
            expected["trajectory_count"],
            "policy trajectory",
        ),
        (trajectory_policy, "rng_seed", expected["rng_seed"], "policy trajectory"),
    )
    for container, field, expected_value, context in mirrors:
        if field not in container:
            raise ValueError(f"MCWF/MPS child {context}.{field} is required")
        actual_value = container[field]
        if (
            actual_value != expected_value
            or type(actual_value) is not type(expected_value)
        ):
            raise ValueError(
                f"MCWF/MPS child {context}.{field} must match the requested option"
            )


def _validate_qt_mps_backend_options(options: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "max_bond",
        "max_branches",
        "microstep_count",
        "finite_step_order",
        "worst_cut_discarded_weight_gate",
        "total_discarded_weight_gate",
        "trajectory_count",
        "rng_seed",
        "dense_oracle_certification",
        "max_record_materialization_outcomes",
    }
    unknown = sorted(set(options) - allowed)
    if unknown:
        joined = ", ".join(unknown)
        raise ValueError(f"unsupported QT/MPS execution_backend_options: {joined}")
    out = dict(options)
    if "max_bond" in out:
        out["max_bond"] = normalize_mps_max_bond(out["max_bond"])
    for name in ("max_branches", "microstep_count"):
        if name in out:
            out[name] = normalize_mps_index(
                out[name],
                name=name,
                minimum=1,
            )
    if "max_record_materialization_outcomes" in out:
        out["max_record_materialization_outcomes"] = normalize_mps_index(
            out["max_record_materialization_outcomes"],
            name="max_record_materialization_outcomes",
            minimum=1,
        )
    if "trajectory_count" in out:
        out["trajectory_count"] = normalize_optional_mps_index(
            out["trajectory_count"],
            name="trajectory_count",
            minimum=1,
        )
    if "rng_seed" in out:
        out["rng_seed"] = normalize_optional_mps_index(
            out["rng_seed"],
            name="rng_seed",
        )
    if "finite_step_order" in out:
        out["finite_step_order"] = normalize_mps_choice(
            out["finite_step_order"],
            name="finite_step_order",
            choices=("first_order", "strang_second_order"),
        )
    if "dense_oracle_certification" in out:
        out["dense_oracle_certification"] = normalize_mps_bool(
            out["dense_oracle_certification"],
            name="dense_oracle_certification",
        )
    for name in (
        "total_discarded_weight_gate",
        "worst_cut_discarded_weight_gate",
    ):
        if name in out and out[name] is not None:
            out[name] = normalize_mps_finite_real(
                out[name],
                name=name,
                minimum=0.0,
            )
    return out


def _qt_mps_expected_options(requested: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "max_bond": None,
        "max_branches": 4096,
        "max_record_materialization_outcomes": 4096,
        "microstep_count": 1,
        "finite_step_order": "first_order",
        "worst_cut_discarded_weight_gate": None,
        "total_discarded_weight_gate": None,
        "trajectory_count": None,
        "rng_seed": None,
        "dense_oracle_certification": True,
    }
    expected.update(requested)
    return expected


def _axis1_qutip_cuquantum_restricted_execution_manifest(
    schedule: SubstepSchedule,
    *,
    device: str,
    instrument_spec: Axis1ReadoutResetInstrumentSpec | None,
) -> dict[str, Any]:
    """Execute the restricted qutip-cuquantum carrier-probe backend.

    This backend is an executable over-cap adapter, not the production QT/MPS
    carrier. It delegates to the qutip-cuquantum trajectory or record probes and
    keeps their representability boundaries intact.
    """

    if instrument_spec is not None:
        raise ValueError(
            "qutip-cuquantum restricted carrier execution does not support "
            "Axis1ReadoutResetInstrumentSpec; use dense_jointL_probe for the "
            "small-N instrument path"
        )
    dev = _require_cuda_device(device)
    _validate_schedule_for_axis1_channel_evidence(schedule)
    program = axis1_carrier_program_manifest(
        schedule,
        backend_contract=AXIS1_QUTIP_CUQUANTUM_PROBE_BACKEND_CONTRACT,
    )
    carrier_summary = _carrier_program_summary(program)
    base_payload: dict[str, Any] = {
        "schema": AXIS1_CARRIER_EXECUTION_SCHEMA,
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "representability": AXIS1_CARRIER_QUTIP_RESTRICTED_EXECUTION_REPRESENTABILITY,
        "execution_backend_contract": (
            AXIS1_CARRIER_QUTIP_RESTRICTED_EXECUTION_BACKEND_CONTRACT
        ),
        "gpu_required": True,
        "device": dev,
        "carrier_program": carrier_summary,
        "claims_dense_channel_evidence": False,
        "claims_dem_decoder_semantics": False,
        "claims_axis2_source_timeline": False,
        "claims_scalable_backend_completed": False,
        "claims_production_scalable_backend": False,
        "claims_qt_mps_backend_execution": False,
        "claims_qutip_cuquantum_execution": True,
        "scored_quantity_policy": (
            "restricted qutip-cuquantum execution is a verification gate only; "
            "no new scored quantity"
        ),
        "epistemic_classes": {
            "program_consumption": "a",
            "restricted_qutip_execution": "c",
            "production_backend_status": "a",
            "dem_decoder_non_claim": "a",
        },
    }
    if _has_measurement_substep(schedule):
        record = axis1_qutip_cuquantum_record_probe_manifest(schedule, device=dev)
        passed = bool(record.get("passed"))
        payload = {
            **base_payload,
            "verdict": "pass" if passed else "fail",
            "passed": passed,
            "blocked_reason": record.get("blocked_reason"),
            "dense_probe_executed": False,
            "qutip_cuquantum_probe_executed": bool(record.get("record_probe_executed")),
            "state_execution": {
                "executed": False,
                "reason": "record_probe_executes_trajectory_branches_not_density_state",
            },
            "record_execution": _qutip_record_execution_summary(record),
            "qutip_probe": {
                "schema": record.get("schema"),
                "content_hash": record.get("content_hash"),
                "representability": record.get("representability"),
                "execution_backend_contract": record.get("execution_backend_contract"),
                "passed": bool(record.get("passed")),
            },
            "scope": (
                "restricted qutip-cuquantum state/record execution probe; no QT/MPS "
                "backend execution, no dense channel payload, no DEM/decoder "
                "semantics, no Axis-2 source timeline, no production scalable "
                "backend claim"
            ),
        }
        payload["content_hash"] = _stable_payload_hash(payload)
        return payload

    trajectory = axis1_qutip_cuquantum_trajectory_probe_manifest(schedule, device=dev)
    passed = bool(trajectory.get("passed"))
    payload = {
        **base_payload,
        "verdict": "pass" if passed else "fail",
        "passed": passed,
        "blocked_reason": trajectory.get("blocked_reason"),
        "dense_probe_executed": False,
        "qutip_cuquantum_probe_executed": bool(
            trajectory.get("trajectory_probe_executed")
        ),
        "state_execution": _qutip_trajectory_execution_summary(trajectory),
        "record_execution": {
            "executed": False,
            "reason": "schedule_has_no_measurement_substep",
        },
        "qutip_probe": {
            "schema": trajectory.get("schema"),
            "content_hash": trajectory.get("content_hash"),
            "representability": trajectory.get("representability"),
            "execution_backend_contract": trajectory.get("execution_backend_contract"),
            "passed": bool(trajectory.get("passed")),
        },
        "scope": (
            "restricted qutip-cuquantum state/record execution probe; no QT/MPS "
            "backend execution, no dense channel payload, no DEM/decoder semantics, "
            "no Axis-2 source timeline, no production scalable backend claim"
        ),
    }
    payload["content_hash"] = _stable_payload_hash(payload)
    return payload


def _carrier_program_summary(program: dict[str, Any]) -> dict[str, Any]:
    if program.get("schema") != AXIS1_CARRIER_PROGRAM_SCHEMA:
        raise ValueError(
            "Axis-1 carrier execution requires an Axis1CarrierProgram manifest; "
            f"got schema={program.get('schema')!r}"
        )
    substeps = list(program.get("program", {}).get("substeps", ()))
    routes = sorted({str(step.get("route")) for step in substeps})
    return {
        "schema": program.get("schema"),
        "content_hash": program.get("content_hash"),
        "backend_contract": program.get("backend_contract"),
        "requires_scalable_backend": _require_manifest_bool(
            program,
            "requires_scalable_backend",
            context="Axis-1 carrier program",
        ),
        "substep_count": len(substeps),
        "routes": routes,
        "route_reasons": sorted({str(step.get("route_reason")) for step in substeps}),
        "claims_dense_channel_evidence": bool(
            program.get("claims_dense_channel_evidence")
        ),
        "claims_dem_decoder_semantics": bool(
            program.get("claims_dem_decoder_semantics")
        ),
        "claims_axis2_source_timeline": bool(
            program.get("claims_axis2_source_timeline")
        ),
    }


def _restricted_mps_program_summary(program: dict[str, Any]) -> dict[str, Any]:
    substeps = list(program.get("program", {}).get("substeps", ()))
    return {
        "schema": program.get("schema"),
        "content_hash": program.get("content_hash"),
        "backend_contract": program.get("backend_contract"),
        "requires_scalable_backend": _require_manifest_bool(
            program,
            "requires_scalable_backend",
            context="Axis-1 Carrier program",
        ),
        "routes": sorted({str(step.get("route")) for step in substeps}),
        "substep_count": len(substeps),
    }


def _require_manifest_bool(
    manifest: dict[str, Any],
    field: str,
    *,
    context: str,
) -> bool:
    value = manifest[field]
    if type(value) is not bool:
        raise TypeError(f"{context} field {field!r} must be an actual bool")
    return value


def _require_manifest_text(
    manifest: dict[str, Any],
    field: str,
    *,
    context: str,
) -> str:
    value = manifest[field]
    if not isinstance(value, str) or not value:
        raise TypeError(f"{context} field {field!r} must be a nonempty string")
    return value


def _validate_restricted_child_state_machine(
    *,
    passed: bool,
    child_verdict: str,
    backend_executed: bool,
    execution_status: str,
    certification_status: str,
    diagnostic_only: bool,
    blocked_reason: Any,
    context: str,
) -> None:
    expected_verdict = "pass" if passed else "fail"
    if child_verdict != expected_verdict:
        raise ValueError(
            f"{context} child verdict must agree with its passed field"
        )

    if backend_executed != (execution_status == "completed"):
        raise ValueError(
            f"{context} backend execution must agree with execution_status"
        )
    if passed and blocked_reason is not None:
        raise ValueError(f"{context} passing child must not carry a blocked reason")

    if passed:
        valid = (
            execution_status == "completed"
            and certification_status == "accepted"
            and not diagnostic_only
        )
    elif execution_status in {"blocked", "failed"}:
        valid = (
            certification_status in {"not_evaluated", "unavailable"}
            and not diagnostic_only
        )
    elif execution_status == "completed" and certification_status == "rejected":
        valid = not diagnostic_only
    elif execution_status == "completed" and certification_status in {
        "not_evaluated",
        "unavailable",
    }:
        valid = diagnostic_only
    else:
        valid = False

    if not valid:
        raise ValueError(
            f"{context} child state machine is inconsistent: "
            f"passed={passed}, execution_status={execution_status!r}, "
            f"certification_status={certification_status!r}, "
            f"diagnostic_only={diagnostic_only}"
        )


def _validate_restricted_policy_state(
    policy: dict[str, Any],
    *,
    execution_status: str,
    certification_status: str,
    diagnostic_only: bool,
    blocked_reason: Any,
    context: str,
    route_kind: str | None = None,
) -> None:
    trajectory_mode: str | None = None
    if route_kind is not None:
        if route_kind not in _RESTRICTED_POLICY_SCHEMAS:
            raise ValueError(f"{context} restricted policy route kind is invalid")
        if route_kind == "mcwf":
            if execution_status == "completed":
                expected_policy_fields = _MCWF_COMPLETED_POLICY_FIELDS
            elif execution_status == "blocked":
                expected_policy_fields = _MCWF_BLOCKED_POLICY_FIELDS
            else:
                raise ValueError(
                    f"{context} MCWF restricted policy execution status is invalid"
                )
            _require_exact_summary_fields(
                policy,
                expected_policy_fields,
                context=f"{context} restricted acceptance policy",
            )
        schema = _require_manifest_text(
            policy,
            "schema",
            context=f"{context} restricted acceptance policy",
        )
        expected_schema = _RESTRICTED_POLICY_SCHEMAS[route_kind]
        if schema != expected_schema:
            raise ValueError(
                f"{context} restricted acceptance policy schema must equal "
                f"{expected_schema!r}"
            )
        policy_role = _require_manifest_text(
            policy,
            "policy_role",
            context=f"{context} restricted acceptance policy",
        )
        if policy_role != _RESTRICTED_POLICY_ROLE:
            raise ValueError(
                f"{context} restricted acceptance policy role is invalid"
            )
        trajectory = policy.get("trajectory")
        if not isinstance(trajectory, dict):
            raise TypeError(
                f"{context} restricted acceptance policy trajectory must be a mapping"
            )
        trajectory_mode = _require_manifest_text(
            trajectory,
            "mode",
            context=f"{context} restricted acceptance policy trajectory",
        )
    policy_execution_status = _require_manifest_text(
        policy,
        "execution_status",
        context=f"{context} restricted acceptance policy",
    )
    policy_certification_status = _require_manifest_text(
        policy,
        "certification_status",
        context=f"{context} restricted acceptance policy",
    )
    policy_diagnostic_only = _require_manifest_bool(
        policy,
        "diagnostic_only",
        context=f"{context} restricted acceptance policy",
    )
    if (
        policy_execution_status != execution_status
        or policy_certification_status != certification_status
        or policy_diagnostic_only != diagnostic_only
    ):
        raise ValueError(
            f"{context} restricted acceptance policy state must match child state"
        )
    if "blocked_reason" not in policy:
        raise KeyError(
            f"{context} restricted acceptance policy missing blocked_reason"
        )
    policy_blocked_reason = policy["blocked_reason"]
    if policy_blocked_reason is not None and not isinstance(
        policy_blocked_reason,
        str,
    ):
        raise TypeError(
            f"{context} restricted acceptance policy blocked_reason must be text or None"
        )
    if policy_blocked_reason != blocked_reason:
        raise ValueError(
            f"{context} restricted acceptance policy blocked_reason must match child"
        )

    accepted = _require_manifest_bool(
        policy,
        "accepted_for_restricted_execution",
        context=f"{context} restricted acceptance policy",
    )
    production_accepted = _require_manifest_bool(
        policy,
        "accepted_for_production_scalable_backend",
        context=f"{context} restricted acceptance policy",
    )
    if production_accepted:
        raise ValueError(
            f"{context} restricted policy cannot claim production scalable acceptance"
        )
    exact_accepted = _require_manifest_bool(
        policy,
        "accepted_for_exact_dense_probability_evidence",
        context=f"{context} restricted acceptance policy",
    )
    sampled_accepted = _require_manifest_bool(
        policy,
        "accepted_for_sampled_execution_evidence",
        context=f"{context} restricted acceptance policy",
    )
    if (exact_accepted or sampled_accepted) and not accepted:
        raise ValueError(
            f"{context} evidence acceptance requires restricted acceptance"
        )
    if route_kind == "mcwf":
        if trajectory_mode != _MCWF_SAMPLED_TRAJECTORY_MODE:
            raise ValueError(
                f"{context} sampled MCWF policy trajectory mode is invalid"
            )
        if exact_accepted:
            raise ValueError(
                f"{context} exact evidence tier is invalid for sampled MCWF"
            )
        if sampled_accepted != accepted:
            raise ValueError(
                f"{context} sampled evidence tier must equal restricted acceptance"
            )
    elif route_kind == "qt":
        if trajectory_mode == _QT_EXACT_TRAJECTORY_MODE:
            if exact_accepted != accepted or sampled_accepted:
                raise ValueError(
                    f"{context} exact QT evidence tier is inconsistent"
                )
        elif trajectory_mode == _QT_SAMPLED_TRAJECTORY_MODE:
            if exact_accepted or sampled_accepted != accepted:
                raise ValueError(
                    f"{context} sampled QT evidence tier is inconsistent"
                )
        else:
            raise ValueError(f"{context} QT trajectory mode is invalid")


def _qt_mps_execution_summary(qt_mps: dict[str, Any]) -> dict[str, Any]:
    acceptance = qt_mps["restricted_acceptance_policy"]
    certification = qt_mps.get("dense_jointL_record_certification", {})
    certification_executed = _require_manifest_bool(
        certification, "executed", context="QT/MPS dense certification"
    )
    certification_passed = (
        _require_manifest_bool(
            certification, "passed", context="QT/MPS dense certification"
        )
        if certification_executed or "passed" in certification
        else False
    )
    return {
        "schema": qt_mps.get("schema"),
        "content_hash": qt_mps.get("content_hash"),
        "representability": qt_mps.get("representability"),
        "backend_contract": qt_mps.get("backend_contract"),
        "execution_status": _require_manifest_text(
            qt_mps, "execution_status", context="QT/MPS execution"
        ),
        "certification_status": _require_manifest_text(
            qt_mps, "certification_status", context="QT/MPS execution"
        ),
        "diagnostic_only": _require_manifest_bool(
            qt_mps, "diagnostic_only", context="QT/MPS execution"
        ),
        "passed": _require_manifest_bool(
            qt_mps, "passed", context="QT/MPS execution"
        ),
        "qt_mps_backend_executed": _require_manifest_bool(
            qt_mps,
            "qt_mps_backend_executed",
            context="QT/MPS execution",
        ),
        "accepted_for_restricted_execution": _require_manifest_bool(
            acceptance,
            "accepted_for_restricted_execution",
            context="QT/MPS restricted acceptance policy",
        ),
        "accepted_for_production_scalable_backend": _require_manifest_bool(
            acceptance,
            "accepted_for_production_scalable_backend",
            context="QT/MPS restricted acceptance policy",
        ),
        "dense_jointL_record_certification_status": (
            "passed"
            if certification_executed and certification_passed
            else certification.get("reason", "not_executed")
        ),
        "claims_exact_joint_lindblad_generator": _require_manifest_bool(
            qt_mps,
            "claims_exact_joint_lindblad_generator",
            context="QT/MPS execution",
        ),
        "claims_dense_channel_evidence": _require_manifest_bool(
            qt_mps,
            "claims_dense_channel_evidence",
            context="QT/MPS execution",
        ),
        "claims_dem_decoder_semantics": _require_manifest_bool(
            qt_mps,
            "claims_dem_decoder_semantics",
            context="QT/MPS execution",
        ),
        "claims_axis2_source_timeline": _require_manifest_bool(
            qt_mps,
            "claims_axis2_source_timeline",
            context="QT/MPS execution",
        ),
        "claims_production_scalable_backend": _require_manifest_bool(
            qt_mps,
            "claims_production_scalable_backend",
            context="QT/MPS execution",
        ),
    }


def _qt_mps_state_execution_summary(qt_mps: dict[str, Any]) -> dict[str, Any]:
    execution = qt_mps.get("mps_execution")
    if not execution:
        return {
            "executed": False,
            "passed": _require_manifest_bool(
                qt_mps, "passed", context="QT/MPS execution"
            ),
            "blocked_reason": qt_mps.get("blocked_reason"),
            "blocked_substeps": list(qt_mps.get("blocked_substeps", ())),
        }
    return {
        "executed": True,
        "evidence_schema": qt_mps["schema"],
        "evidence_content_hash": qt_mps["content_hash"],
        "representability": qt_mps["representability"],
        "passed": _require_manifest_bool(
            qt_mps, "passed", context="QT/MPS execution"
        ),
        "mps_library": execution["mps_library"],
        "array_backend": execution["array_backend"],
        "finite_step_policy": dict(execution["finite_step_policy"]),
        "mps_truncation_ledger": dict(execution["mps_truncation_ledger"]),
        "applied_substeps": list(execution["applied_substeps"]),
        "total_probability_residual": float(execution["total_probability_residual"]),
        "claims_density_state_evidence": False,
        "claims_exact_joint_lindblad_generator": False,
    }


def _qt_mps_record_execution_summary(qt_mps: dict[str, Any]) -> dict[str, Any]:
    execution = qt_mps.get("mps_execution")
    if not execution:
        return {
            "executed": False,
            "passed": _require_manifest_bool(
                qt_mps, "passed", context="QT/MPS execution"
            ),
            "blocked_reason": qt_mps.get("blocked_reason"),
            "blocked_substeps": list(qt_mps.get("blocked_substeps", ())),
        }
    return {
        "executed": True,
        "evidence_schema": qt_mps["schema"],
        "evidence_content_hash": qt_mps["content_hash"],
        "representability": qt_mps["representability"],
        "passed": _require_manifest_bool(
            qt_mps, "passed", context="QT/MPS execution"
        ),
        "measurement_keys": list(execution["measurement_keys"]),
        "measurement_records": list(execution["measurement_records"]),
        "record_probabilities": list(execution["record_probabilities"]),
        "detector_records": list(execution["detector_records"]),
        "logical_observable_records": list(execution["logical_observable_records"]),
        "total_probability": float(execution["total_probability"]),
        "total_probability_residual": float(execution["total_probability_residual"]),
        "trajectory_sampling": dict(execution["trajectory_sampling"]),
        "claims_b8_artifact": bool(execution["claims_b8_artifact"]),
        "claims_decoder_integration": bool(execution["claims_decoder_integration"]),
        "claims_dense_channel_evidence": bool(
            qt_mps.get("claims_dense_channel_evidence", False)
        ),
        "claims_axis2_source_timeline": bool(
            qt_mps.get("claims_axis2_source_timeline", False)
        ),
        "claims_production_scalable_backend": bool(
            qt_mps.get("claims_production_scalable_backend", False)
        ),
    }


def _state_execution_summary(state: dict[str, Any]) -> dict[str, Any]:
    evolution = state["state_evolution"]
    return {
        "executed": True,
        "evidence_schema": state["schema"],
        "evidence_content_hash": state["content_hash"],
        "representability": state["representability"],
        "passed": bool(state["passed"]),
        "applied_channel_count": int(evolution["applied_channel_count"]),
        "final_trace": float(evolution["final_trace"]),
        "trace_residual": float(evolution["trace_residual"]),
        "final_z_probabilities": list(evolution["final_z_probabilities"]),
        "joint_generator_semantics": "single_joint_generator_expm",
        "claims_record_emission": bool(evolution["claims_record_emission"]),
        "claims_axis2_source_projection": bool(
            evolution["claims_axis2_source_projection"]
        ),
    }


def _record_execution_summary(record: dict[str, Any] | None) -> dict[str, Any]:
    if record is None:
        return {
            "executed": False,
            "reason": "schedule_has_no_measurement_substep",
        }
    evidence = record["record_evidence"]
    return {
        "executed": True,
        "evidence_schema": record["schema"],
        "evidence_content_hash": record["content_hash"],
        "representability": record["representability"],
        "passed": bool(record["passed"]),
        "applied_channel_count": int(evidence["applied_channel_count"]),
        "measurement_keys": list(evidence["measurement_keys"]),
        "measurement_records": list(evidence["measurement_records"]),
        "record_probabilities": list(evidence["record_probabilities"]),
        "detector_records": list(evidence["detector_records"]),
        "logical_observable_records": list(evidence["logical_observable_records"]),
        "total_probability": float(evidence["total_probability"]),
        "total_probability_residual": float(evidence["total_probability_residual"]),
        "joint_generator_semantics": "single_joint_generator_expm",
        "claims_b8_artifact": bool(evidence["claims_b8_artifact"]),
        "claims_decoder_integration": bool(evidence["claims_decoder_integration"]),
        "claims_axis2_source_projection": bool(
            evidence["claims_axis2_source_projection"]
        ),
    }


def _qutip_trajectory_execution_summary(trajectory: dict[str, Any]) -> dict[str, Any]:
    probe = trajectory.get("trajectory_probe")
    if not probe:
        return {
            "executed": False,
            "passed": bool(trajectory.get("passed")),
            "blocked_reason": trajectory.get("blocked_reason"),
            "blocked_substeps": list(trajectory.get("blocked_substeps", ())),
        }
    return {
        "executed": True,
        "evidence_schema": trajectory["schema"],
        "evidence_content_hash": trajectory["content_hash"],
        "representability": trajectory["representability"],
        "passed": bool(trajectory["passed"]),
        "solver": probe["solver"],
        "solver_methods": list(probe["solver_methods"]),
        "ntraj": int(probe["ntraj"]),
        "final_z_probabilities": list(probe["final_z_probabilities"]),
        "final_norm": float(probe["final_norm"]),
        "norm_residual": float(probe["norm_residual"]),
        "applied_substeps": list(probe["applied_substeps"]),
        "statevector_payload_serialized": bool(
            probe["statevector_payload_serialized"]
        ),
        "claims_record_execution": False,
        "claims_density_state_evidence": False,
    }


def _qutip_record_execution_summary(record: dict[str, Any]) -> dict[str, Any]:
    probe = record.get("record_probe")
    if not probe:
        return {
            "executed": False,
            "passed": bool(record.get("passed")),
            "blocked_reason": record.get("blocked_reason"),
            "blocked_substeps": list(record.get("blocked_substeps", ())),
        }
    return {
        "executed": True,
        "evidence_schema": record["schema"],
        "evidence_content_hash": record["content_hash"],
        "representability": record["representability"],
        "passed": bool(record["passed"]),
        "solver": probe["solver"],
        "solver_methods": list(probe["solver_methods"]),
        "measurement_keys": list(probe["measurement_keys"]),
        "measurement_records": list(probe["measurement_records"]),
        "record_probabilities": list(probe["record_probabilities"]),
        "detector_records": list(probe["detector_records"]),
        "logical_observable_records": list(probe["logical_observable_records"]),
        "total_probability": float(probe["total_probability"]),
        "total_probability_residual": float(
            probe["total_probability_residual"]
        ),
        "applied_substeps": list(probe["applied_substeps"]),
        "claims_b8_artifact": bool(probe["claims_b8_artifact"]),
        "claims_decoder_integration": bool(probe["claims_decoder_integration"]),
        "claims_dense_channel_evidence": bool(
            probe["claims_dense_channel_evidence"]
        ),
        "claims_axis2_source_timeline": bool(
            probe["claims_axis2_source_timeline"]
        ),
        "claims_production_scalable_backend": bool(
            probe["claims_production_scalable_backend"]
        ),
    }


def _has_measurement_substep(schedule: SubstepSchedule) -> bool:
    return any(substep.kind == "measurement" for substep in schedule.substeps)


def _jsonable(value: Any) -> Any:
    return json.loads(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    )


def _stable_payload_hash(payload: dict[str, Any]) -> str:
    without_hash = dict(payload)
    without_hash.pop("content_hash", None)
    data = json.dumps(
        without_hash,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _streaming_stable_payload_hash(payload: dict[str, Any]) -> str:
    """Hash canonical JSON without materializing one full JSON string/bytes pair."""

    without_hash = dict(payload)
    without_hash.pop("content_hash", None)
    encoder = json.JSONEncoder(
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    digest = hashlib.sha256()
    for chunk in encoder.iterencode(without_hash):
        digest.update(chunk.encode("utf-8"))
    return digest.hexdigest()


def _validate_child_content_hash_streaming(
    child: dict[str, Any],
    *,
    context: str,
) -> None:
    declared = child.get("content_hash")
    if not isinstance(declared, str) or not declared:
        raise TypeError(f"{context} content_hash must be a nonempty string")
    if declared != _streaming_stable_payload_hash(child):
        raise ValueError(f"{context} content_hash does not authenticate its payload")


def _validate_child_content_hash(
    child: dict[str, Any],
    *,
    context: str,
) -> None:
    declared = child.get("content_hash")
    if not isinstance(declared, str) or not declared:
        raise TypeError(f"{context} content_hash must be a nonempty string")
    if declared != _stable_payload_hash(child):
        raise ValueError(f"{context} content_hash does not authenticate its payload")


__all__ = [
    "AXIS1_CARRIER_ALLOWED_EXECUTION_BACKEND_CONTRACTS",
    "AXIS1_CARRIER_AUTO_BACKEND_CONTRACT",
    "AXIS1_CARRIER_AUTO_EXECUTION_SCHEMA",
    "AXIS1_CARRIER_DENSE_RECORD_TRANSIENT_FACTOR",
    "AXIS1_CARRIER_DENSE_VRAM_SAFETY_FRACTION",
    "AXIS1_CARRIER_EXECUTION_BACKEND_CONTRACT",
    "AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT",
    "AXIS1_CARRIER_MCWF_MPS_EXECUTION_REPRESENTABILITY",
    "AXIS1_CARRIER_QUTIP_RESTRICTED_EXECUTION_BACKEND_CONTRACT",
    "AXIS1_CARRIER_QUTIP_RESTRICTED_EXECUTION_REPRESENTABILITY",
    "AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT",
    "AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_REPRESENTABILITY",
    "AXIS1_CARRIER_EXECUTION_REPRESENTABILITY",
    "AXIS1_CARRIER_EXECUTION_SCHEMA",
    "AXIS1_MCWF_MPS_RECORD_MAX_ARRAY_PAYLOAD_BYTES",
    "AXIS1_MCWF_MPS_RECORD_MAX_SUPPORT_CELLS",
    "AXIS1_MCWF_MPS_RECORD_OUTPUT_REPRESENTABILITY",
    "AXIS1_MCWF_MPS_RECORD_OUTPUT_SCHEMA",
    "Axis1McwfMpsRecordSampleResult",
    "axis1_carrier_execution_manifest",
    "axis1_mcwf_mps_record_batch",
    "write_axis1_mcwf_mps_record_samples",
]
