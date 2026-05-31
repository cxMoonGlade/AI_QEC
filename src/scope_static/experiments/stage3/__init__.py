"""Stage 3 experiment command wrappers.

The package keeps command modules lazy so ``python -m`` can execute a stage
module without first importing that same module through this package.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_EXPORTS = {
    "run_stage3a_protocol_freeze_from_config": (".protocol_freeze", "run_stage3a_protocol_freeze_from_config"),
    "run_stage3a5_observability_ceiling_from_config": (".observability_ceiling", "run_stage3a5_observability_ceiling_from_config"),
    "run_stage3b0_baselines_from_config": (".baselines", "run_stage3b0_baselines_from_config"),
    "run_stage3b1_discovery_model_from_config": (".discovery_model", "run_stage3b1_discovery_model_from_config"),
    "run_stage3c_generator_learning_from_config": (".generator_learning", "run_stage3c_generator_learning_from_config"),
    "run_stage3d1_assignment_shuffle_audit_from_config": (
        ".assignment_shuffle_audit",
        "run_stage3d1_assignment_shuffle_audit_from_config",
    ),
    "run_stage3d2_feature_scramble_audit_from_config": (
        ".feature_scramble_audit",
        "run_stage3d2_feature_scramble_audit_from_config",
    ),
    "run_stage3d3_context_shuffle_audit_from_config": (
        ".context_shuffle_audit",
        "run_stage3d3_context_shuffle_audit_from_config",
    ),
    "run_stage3d4_k_stress_audit_from_config": (
        ".k_stress_audit",
        "run_stage3d4_k_stress_audit_from_config",
    ),
    "run_stage3d4b_overcomplete_merge_prune_audit_from_config": (
        ".overcomplete_merge_prune_audit",
        "run_stage3d4b_overcomplete_merge_prune_audit_from_config",
    ),
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(name)
    module_name, attr_name = _EXPORTS[name]
    value = getattr(import_module(module_name, __name__), attr_name)
    globals()[name] = value
    return value
