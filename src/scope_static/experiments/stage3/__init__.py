"""Stage 3 experiment command wrappers."""

from .assignment_shuffle_audit import run_stage3d1_assignment_shuffle_audit_from_config
from .baselines import run_stage3b0_baselines_from_config
from .discovery_model import run_stage3b1_discovery_model_from_config
from .generator_learning import run_stage3c_generator_learning_from_config
from .observability_ceiling import run_stage3a5_observability_ceiling_from_config
from .protocol_freeze import run_stage3a_protocol_freeze_from_config

__all__ = [
    "run_stage3a_protocol_freeze_from_config",
    "run_stage3a5_observability_ceiling_from_config",
    "run_stage3b0_baselines_from_config",
    "run_stage3b1_discovery_model_from_config",
    "run_stage3c_generator_learning_from_config",
    "run_stage3d1_assignment_shuffle_audit_from_config",
]
