"""Controlled generative noise processes for the coupling-error simulator.

Slice-1 dense source-coupled process: ``CoupledCycleNoiseProcess`` (a memory-ful 1/f shared source ->
per-round Axis-1 params -> sealed dense {det,obs} emitter, with a matched-marginal permutation arm
and a source-off arm). Source
trajectories and channel fields are evaluator-only truth and are not emitted.
"""
from error_coupling_simulator.noise_processes.coupled_cycle import (
    COUPLED_PROCESS_REPRESENTABILITY,
    COUPLED_PROCESS_SCHEMA,
    COUPLED_PROCESS_STIM_EXPORT_SCHEMA,
    DEFAULT_STATIC_ZZ_EDGE,
    MEMORYFUL_SHARED_SOURCES,
    CoupledCycleNoiseProcess,
    default_coupled_code_spec,
    default_coupled_code_spec_4q,
    default_coupled_code_spec_d3_repz,
    derive_round_map_for_substep_schedule,
    params_for_substep_from_round_map,
    per_round_axis1_params,
    trajectory_mean_instrument,
)

__all__ = [
    "COUPLED_PROCESS_REPRESENTABILITY",
    "COUPLED_PROCESS_SCHEMA",
    "COUPLED_PROCESS_STIM_EXPORT_SCHEMA",
    "DEFAULT_STATIC_ZZ_EDGE",
    "MEMORYFUL_SHARED_SOURCES",
    "CoupledCycleNoiseProcess",
    "default_coupled_code_spec",
    "default_coupled_code_spec_4q",
    "default_coupled_code_spec_d3_repz",
    "derive_round_map_for_substep_schedule",
    "params_for_substep_from_round_map",
    "per_round_axis1_params",
    "trajectory_mean_instrument",
]
