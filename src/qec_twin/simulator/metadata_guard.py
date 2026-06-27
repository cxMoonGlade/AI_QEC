from __future__ import annotations

"""Learner-visible metadata guards for the simulator frontend."""

from typing import Any

_RESERVED_METADATA_KEY_PARTS = (
    "analog_truth",
    "axis1_error",
    "axis2_error",
    "baseline_noise",
    "cudaqx_noise",
    "cudaqx_error",
    "channel_truth",
    "dem_error_model",
    "error_ids",
    "error_model",
    "exact_channel",
    "evaluator_truth",
    "ground_truth",
    "hidden_state",
    "joint_lindbladian_truth",
    "kraus",
    "leakage_trace",
    "mechanism_truth",
    "oracle",
    "process_matrix",
    "ptm",
    "si1000_noise",
    "si1000_error",
    "source_trace",
    "source_trajectory",
    "teacher_id",
)
_RESERVED_METADATA_EXACT_KEYS = (
    "axis",
    "axis1",
    "axis2",
    "baseline",
    "cudaqx",
    "error",
    "noise_model",
    "si1000",
)


def validate_public_metadata(metadata: dict[str, Any] | None, *, label: str = "metadata") -> dict:
    """Return a copied public metadata dict after rejecting evaluator-truth keys."""

    copied = dict(metadata or {})
    _validate_keys(copied, path=label)
    return copied


def _validate_keys(value: Any, *, path: str) -> None:
    if isinstance(value, dict):
        for raw_key, item in value.items():
            key = str(raw_key)
            normalized = key.lower().replace("-", "_").replace(" ", "_")
            if normalized in _RESERVED_METADATA_EXACT_KEYS:
                raise ValueError(
                    "learner-visible metadata cannot contain evaluator/error-model semantics; "
                    f"reserved key {path}.{key!s} matches exact key {normalized!r}. "
                    "Put runnable noise in NoiseSpec and evaluator truth in evaluator_sidecars."
                )
            for reserved in _RESERVED_METADATA_KEY_PARTS:
                if reserved in normalized:
                    raise ValueError(
                        "learner-visible metadata cannot contain evaluator truth; "
                        f"reserved key {path}.{key!s} matches {reserved!r}. "
                        "Use evaluator_sidecars with visibility='evaluator_only'."
                    )
            _validate_keys(item, path=f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for i, item in enumerate(value):
            _validate_keys(item, path=f"{path}[{i}]")
