"""Controlled record teachers (evaluator-only) for the coupling-error simulator.

Slice-1 dense source-coupled teacher: ``CoupledCycleTeacher`` (a memory-ful 1/f shared source ->
per-round Axis-1 params -> sealed dense {det,obs} emitter, with markovian_baseline / off_source
control arms). Evaluator-only ground truth; NOT consumed by the label-free learner path.
"""
from error_coupling_simulator.teachers.coupled_cycle import (
    COUPLED_TEACHER_REPRESENTABILITY,
    COUPLED_TEACHER_SCHEMA,
    DEFAULT_STATIC_ZZ_EDGE,
    MEMORYFUL_SHARED_SOURCES,
    CoupledCycleTeacher,
    default_coupled_code_spec,
    default_coupled_code_spec_4q,
    derive_round_map_for_substep_schedule,
    params_for_substep_from_round_map,
    per_round_axis1_params,
    trajectory_mean_instrument,
)

__all__ = [
    "COUPLED_TEACHER_REPRESENTABILITY",
    "COUPLED_TEACHER_SCHEMA",
    "DEFAULT_STATIC_ZZ_EDGE",
    "MEMORYFUL_SHARED_SOURCES",
    "CoupledCycleTeacher",
    "default_coupled_code_spec",
    "default_coupled_code_spec_4q",
    "derive_round_map_for_substep_schedule",
    "params_for_substep_from_round_map",
    "per_round_axis1_params",
    "trajectory_mean_instrument",
]
