from __future__ import annotations

"""Law-neutral state mechanics for restricted open-boundary MPS routes."""

from collections.abc import Iterable
import math
import operator
from typing import Any

import torch

from ...numerics import NUMERICAL_ZERO


def _finite_real_scalar(value: Any, *, name: str) -> float:
    tensor = torch.as_tensor(value)
    if tensor.numel() != 1:
        raise RuntimeError(f"{name} must be scalar, got shape {tuple(tensor.shape)}")
    numeric = complex(tensor.detach().cpu().item())
    if not math.isfinite(numeric.real) or not math.isfinite(numeric.imag):
        raise RuntimeError(f"{name} must be finite, got {numeric!r}")
    if abs(numeric.imag) > NUMERICAL_ZERO * max(1.0, abs(numeric.real)):
        raise RuntimeError(f"{name} must be real, got {numeric!r}")
    return float(numeric.real)


def mps_norm_squared(mps: Any) -> float:
    """Return a finite real MPS norm squared without normalizing the state."""

    return _finite_real_scalar(
        (mps.H & mps).contract(all),
        name="MPS norm squared",
    )


def max_mps_bond(states: Iterable[Any]) -> int:
    """Return the largest observed virtual bond across MPS states."""

    maximum = 1
    for state in states:
        sizes = tuple(state.bond_sizes())
        if sizes:
            maximum = max(maximum, *(int(size) for size in sizes))
    return int(maximum)


def exact_mps_bond_dimension(local_dims: Iterable[Any]) -> int:
    """Return the open-chain cut-product cap sufficient for any state."""

    dimensions: list[int] = []
    for site, value in enumerate(local_dims):
        if isinstance(value, bool):
            raise TypeError(f"local_dims[{site}] must be an integer, not bool")
        try:
            dimension = operator.index(value)
        except TypeError as exc:
            raise TypeError(
                f"local_dims[{site}] must be an integer, got {value!r}"
            ) from exc
        if dimension < 1:
            raise ValueError(
                f"local_dims[{site}] must be positive, got {dimension}"
            )
        dimensions.append(int(dimension))
    if len(dimensions) <= 1:
        return 1
    return int(
        max(
            min(math.prod(dimensions[:cut]), math.prod(dimensions[cut:]))
            for cut in range(1, len(dimensions))
        )
    )


def commit_mps_candidate_(target: Any, candidate: Any) -> None:
    """Commit an already-validated candidate with rollback on update error."""

    if int(target.L) != int(candidate.L):
        raise ValueError("target and candidate MPS lengths differ")
    old_arrays: list[Any] = []
    target_tensors = []
    candidate_tensors = []
    for site in range(int(target.L)):
        target_tensor = target[site]
        candidate_tensor = candidate[site]
        if tuple(target_tensor.inds) != tuple(candidate_tensor.inds):
            raise RuntimeError(f"candidate index structure drifted at site {site}")
        if set(target_tensor.tags) != set(candidate_tensor.tags):
            raise RuntimeError(f"candidate tag structure drifted at site {site}")
        target_tensors.append(target_tensor)
        candidate_tensors.append(candidate_tensor)
        old_arrays.append(target_tensor.data)
    try:
        for target_tensor, candidate_tensor in zip(
            target_tensors, candidate_tensors, strict=True
        ):
            target_tensor.modify(data=candidate_tensor.data)
    except Exception as commit_error:
        rollback_errors = []
        for site, (target_tensor, old_array) in enumerate(
            zip(target_tensors, old_arrays, strict=True)
        ):
            try:
                target_tensor.modify(data=old_array)
            except Exception as rollback_error:  # noqa: BLE001
                rollback_errors.append((site, rollback_error))
        if rollback_errors:
            details = ", ".join(
                f"site{site}:{type(error).__name__}"
                for site, error in rollback_errors
            )
            raise RuntimeError(
                f"MPS candidate commit failed and rollback was incomplete ({details})"
            ) from commit_error
        raise
