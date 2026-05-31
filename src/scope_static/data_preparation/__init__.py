"""Data preparation physical-process generator interface.

Layer1.P is the public data-preparation physical-process generator. The CUDA-Q sampler and
physicality audit live behind this package so callers import the Layer 1
interface instead of scattered generator modules.
"""

from .full_circuit_cudaq import generate_full_circuit_cudaq_teacher_dataset
from .physicality_audit import (
    CUDA_FLOAT32_TOLERANCE,
    CUDA_FLOAT64_TOLERANCE,
    DEFAULT_OUTPUT_DIR as DEFAULT_PHYSICALITY_AUDIT_OUTPUT_DIR,
    PROBABILITY_FLOOR_TOLERANCE,
    STRICT_TOLERANCE,
    run_teacher_physicality_audit,
)
from .physical_process import (
    DEFAULT_AUDIT_SUBDIR,
    DEFAULT_OUTPUT_DIR as DEFAULT_LAYER1P_TEACHER_OUTPUT_DIR,
    DEFAULT_PROBABILITY_TOLERANCE,
    DEFAULT_RANDOM_STATE_COUNT,
    DEFAULT_TOLERANCE_MODE,
    PRE_SAMPLING_TOLERANCE,
    STAGE_NAME,
    build_layer1p_pre_sampling_contract,
    format_layer1p_teacher_summary,
    generate_layer1p_teacher_dataset,
    layer1p_acceptance_audit,
    layer1p_teacher_config,
    layer1p_teacher_contract,
)

__all__ = [
    "CUDA_FLOAT32_TOLERANCE",
    "CUDA_FLOAT64_TOLERANCE",
    "DEFAULT_AUDIT_SUBDIR",
    "DEFAULT_LAYER1P_TEACHER_OUTPUT_DIR",
    "DEFAULT_PHYSICALITY_AUDIT_OUTPUT_DIR",
    "DEFAULT_PROBABILITY_TOLERANCE",
    "DEFAULT_RANDOM_STATE_COUNT",
    "DEFAULT_TOLERANCE_MODE",
    "PRE_SAMPLING_TOLERANCE",
    "PROBABILITY_FLOOR_TOLERANCE",
    "STAGE_NAME",
    "STRICT_TOLERANCE",
    "build_layer1p_pre_sampling_contract",
    "format_layer1p_teacher_summary",
    "generate_full_circuit_cudaq_teacher_dataset",
    "generate_layer1p_teacher_dataset",
    "layer1p_acceptance_audit",
    "layer1p_teacher_config",
    "layer1p_teacher_contract",
    "run_teacher_physicality_audit",
]
