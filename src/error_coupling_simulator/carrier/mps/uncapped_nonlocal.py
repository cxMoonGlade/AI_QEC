from __future__ import annotations

"""Bounded uncapped nonlocal-unitary mechanics for restricted MPS validation.

This module deliberately bypasses Quimb's high-level ``auto-mps`` route for
three-or-more-site gates. In Quimb 1.14.0 that route decomposes the dense gate
to an MPO before forwarding the caller's compression options, so the first
split can inherit a nonzero cutoff. Here both decomposition layers carry an
explicit zero cutoff. This is execution machinery, not a scientific carrier
or a global approximation certificate.
"""

from collections.abc import Mapping, Sequence
import importlib.metadata
import math
import operator
from typing import Any

import numpy as np
import quimb.tensor as qtn
import torch

from ...numerics import NUMERICAL_ZERO
from .state import mps_norm_squared


_SUPPORTED_QUIMB_VERSION = "1.14.0"
_EVENT_SCHEMA = "error_coupling_simulator.carrier.mps.uncapped_nonlocal_event.v1"
MAX_SUPPORT_SITES = 5
MAX_SUPPORT_HILBERT_DIMENSION = 256
MAX_DENSE_OPERATOR_ELEMENTS = 65_536
_SPLIT_METHOD = "svd"
_CUTOFF = 0.0
_CUTOFF_MODE = "rsum2"


def _strict_integer_tuple(values: Any, *, name: str) -> tuple[int, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError(f"{name} must be a sequence of integers")
    normalized: list[int] = []
    for index, value in enumerate(values):
        if isinstance(value, bool):
            raise TypeError(f"{name}[{index}] must be an integer, not bool")
        try:
            item = operator.index(value)
        except TypeError as exc:
            raise TypeError(f"{name}[{index}] must be an integer") from exc
        normalized.append(int(item))
    return tuple(normalized)


def preflight_uncapped_nonlocal_resource(
    *,
    support: Sequence[int],
    local_dims: Sequence[int],
) -> dict[str, Any]:
    """Validate the fixed numerical-only resource envelope before allocation."""
    sites = _strict_integer_tuple(support, name="support")
    dims = _strict_integer_tuple(local_dims, name="local_dims")
    if len(sites) < 3:
        raise ValueError("uncapped nonlocal mechanics require at least three sites")
    if len(sites) > MAX_SUPPORT_SITES:
        raise ValueError(
            "uncapped nonlocal support exceeds the numerical-only site cap: "
            f"{len(sites)} > {MAX_SUPPORT_SITES}"
        )
    if any(site < 0 for site in sites):
        raise ValueError("support sites must be nonnegative")
    if any(left >= right for left, right in zip(sites, sites[1:])):
        raise ValueError("support must contain distinct sites in ascending order")
    if not dims:
        raise ValueError("local_dims must not be empty")
    if any(dim < 2 for dim in dims):
        raise ValueError("every local dimension must be at least two")
    if sites[-1] >= len(dims):
        raise ValueError("support lies outside local_dims")

    support_dims = tuple(dims[site] for site in sites)
    hilbert_dimension = math.prod(support_dims)
    dense_elements = hilbert_dimension * hilbert_dimension
    if hilbert_dimension > MAX_SUPPORT_HILBERT_DIMENSION:
        raise ValueError(
            "uncapped nonlocal support exceeds the numerical-only Hilbert cap: "
            f"{hilbert_dimension} > {MAX_SUPPORT_HILBERT_DIMENSION}"
        )
    if dense_elements > MAX_DENSE_OPERATOR_ELEMENTS:
        raise ValueError(
            "uncapped nonlocal dense operator exceeds the numerical-only element cap: "
            f"{dense_elements} > {MAX_DENSE_OPERATOR_ELEMENTS}"
        )
    return {
        "support": list(sites),
        "support_local_dims": list(support_dims),
        "support_site_count": len(sites),
        "support_hilbert_dimension": int(hilbert_dimension),
        "dense_operator_elements": int(dense_elements),
        "max_support_sites": MAX_SUPPORT_SITES,
        "max_support_hilbert_dimension": MAX_SUPPORT_HILBERT_DIMENSION,
        "max_dense_operator_elements": MAX_DENSE_OPERATOR_ELEMENTS,
        "resource_gate_role": "numerical_only_preallocation_cap_not_accuracy_gate",
    }


def _finite_real_scalar(value: Any, *, name: str) -> float:
    if isinstance(value, torch.Tensor):
        if value.numel() != 1:
            raise RuntimeError(f"{name} must be scalar")
        numeric = complex(value.detach().cpu().item())
    else:
        array = np.asarray(value)
        if array.size != 1:
            raise RuntimeError(f"{name} must be scalar")
        numeric = complex(array.reshape(()).item())
    if not math.isfinite(numeric.real) or not math.isfinite(numeric.imag):
        raise RuntimeError(f"{name} must be finite")
    if abs(numeric.imag) > NUMERICAL_ZERO * max(1.0, abs(numeric.real)):
        raise RuntimeError(f"{name} must be real")
    return float(numeric.real)


def _assert_quimb_contract() -> str:
    version = importlib.metadata.version("quimb")
    if version != _SUPPORTED_QUIMB_VERSION:
        raise RuntimeError(
            "uncapped nonlocal mechanics are pinned to quimb "
            f"{_SUPPORTED_QUIMB_VERSION}, found {version}"
        )
    return version


def _validate_source_mps(
    mps: Any,
    *,
    local_dims: tuple[int, ...],
) -> tuple[str, Any]:
    if bool(getattr(mps, "cyclic", False)):
        raise ValueError("uncapped nonlocal mechanics require an open-boundary MPS")
    try:
        length = int(mps.L)
    except (AttributeError, TypeError, ValueError) as exc:
        raise TypeError("mps must expose an integer length") from exc
    if len(local_dims) != length:
        raise ValueError("local_dims must describe every MPS site")

    arrays = [mps[site].data for site in range(length)]
    if not arrays:
        raise ValueError("mps must contain at least one site")
    if all(isinstance(array, torch.Tensor) for array in arrays):
        backend = "torch"
        device = arrays[0].device
        for site, array in enumerate(arrays):
            if array.dtype != torch.complex128:
                raise TypeError(
                    f"Torch MPS site {site} must use complex128, got {array.dtype}"
                )
            if array.device != device:
                raise ValueError("all Torch MPS tensors must share one device")
            if not bool(torch.isfinite(array).all().item()):
                raise ValueError(f"MPS site {site} contains non-finite values")
    elif all(isinstance(array, np.ndarray) for array in arrays):
        backend = "numpy"
        device = None
        for site, array in enumerate(arrays):
            if array.dtype != np.dtype(np.complex128):
                raise TypeError(
                    f"NumPy MPS site {site} must use complex128, got {array.dtype}"
                )
            if not bool(np.isfinite(array).all()):
                raise ValueError(f"MPS site {site} contains non-finite values")
    else:
        raise TypeError("uncapped nonlocal mechanics require NumPy- or Torch-backed MPS tensors")

    for site, declared_dim in enumerate(local_dims):
        actual_dim = int(mps.ind_size(mps.site_ind(site)))
        if actual_dim != declared_dim:
            raise ValueError(
                f"MPS site {site} dimension {actual_dim} != declared {declared_dim}"
            )
    return backend, device


def _validate_gate(
    gate: Any,
    *,
    backend: str,
    device: Any,
    dimension: int,
) -> Any:
    try:
        if backend == "torch":
            array = torch.as_tensor(gate)
            if array.dtype != torch.complex128:
                raise ValueError("gate must use complex128")
            if array.device != device:
                raise ValueError("gate and MPS must occupy the same device")
            finite = bool(torch.isfinite(array).all().item())
        else:
            array = np.asarray(gate)
            if array.dtype != np.dtype(np.complex128):
                raise ValueError("gate must use complex128")
            finite = bool(np.isfinite(array).all())
    except ValueError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise ValueError("gate could not be materialized") from exc

    expected_shape = (dimension, dimension)
    if tuple(array.shape) != expected_shape:
        raise ValueError(f"gate shape {tuple(array.shape)} != {expected_shape}")
    if not finite:
        raise ValueError("gate contains non-finite values")
    if backend == "torch":
        identity = torch.eye(dimension, dtype=torch.complex128, device=device)
        residual = _finite_real_scalar(
            torch.linalg.matrix_norm(array.conj().mT @ array - identity),
            name="gate unitarity residual",
        )
    else:
        identity = np.eye(dimension, dtype=np.complex128)
        residual = float(np.linalg.norm(array.conj().T @ array - identity))
    if not math.isfinite(residual) or residual > NUMERICAL_ZERO:
        raise ValueError(f"gate must be unitary; residual={residual:.3e}")
    return array


def _validate_candidate_finite(candidate: Any, *, backend: str) -> None:
    for site in range(int(candidate.L)):
        array = candidate[site].data
        if backend == "torch":
            finite = isinstance(array, torch.Tensor) and bool(
                torch.isfinite(array).all().item()
            )
        else:
            finite = isinstance(array, np.ndarray) and bool(np.isfinite(array).all())
        if not finite:
            raise RuntimeError(f"candidate MPS site {site} contains non-finite values")


def apply_uncapped_nonlocal_unitary(
    mps: Any,
    gate: Any,
    *,
    support: Sequence[int],
    local_dims: Sequence[int],
    context: Mapping[str, Any] | None = None,
) -> tuple[Any, dict[str, Any]]:
    """Build and validate an uncapped candidate without mutating ``mps``."""
    resource = preflight_uncapped_nonlocal_resource(
        support=support,
        local_dims=local_dims,
    )
    sites = tuple(resource["support"])
    dims = _strict_integer_tuple(local_dims, name="local_dims")
    if context is not None and not isinstance(context, Mapping):
        raise TypeError("context must be a mapping or None")
    backend, device = _validate_source_mps(mps, local_dims=dims)
    gate_array = _validate_gate(
        gate,
        backend=backend,
        device=device,
        dimension=int(resource["support_hilbert_dimension"]),
    )
    input_norm_sq = mps_norm_squared(mps)
    if input_norm_sq <= 0.0:
        raise ValueError("source MPS norm must be positive")
    quimb_version = _assert_quimb_contract()

    try:
        candidate = mps.copy(deep=True)
        submpo = qtn.MatrixProductOperator.from_dense(
            gate_array,
            dims=tuple(resource["support_local_dims"]),
            sites=sites,
            L=int(mps.L),
            method=_SPLIT_METHOD,
            max_bond=None,
            cutoff=_CUTOFF,
            cutoff_mode=_CUTOFF_MODE,
            renorm=None,
        )
        candidate.gate_with_submpo_(
            submpo,
            where=sites,
            method="direct",
            max_bond=None,
            cutoff=_CUTOFF,
            cutoff_mode=_CUTOFF_MODE,
            normalize=False,
        )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("uncapped nonlocal Quimb execution failed") from exc

    _validate_candidate_finite(candidate, backend=backend)
    output_norm_sq = mps_norm_squared(candidate)
    if output_norm_sq <= 0.0:
        raise RuntimeError("candidate MPS norm must be positive")
    norm_drift = abs(output_norm_sq - input_norm_sq)
    if not math.isclose(
        output_norm_sq,
        input_norm_sq,
        rel_tol=NUMERICAL_ZERO,
        abs_tol=NUMERICAL_ZERO,
    ):
        raise RuntimeError(
            "uncapped unitary candidate changed the MPS norm: "
            f"{output_norm_sq} != {input_norm_sq}"
        )

    event = {
        "schema": _EVENT_SCHEMA,
        "support": list(sites),
        "support_local_dims": list(resource["support_local_dims"]),
        "support_hilbert_dimension": int(resource["support_hilbert_dimension"]),
        "dense_operator_elements": int(resource["dense_operator_elements"]),
        "requested_cutoff": _CUTOFF,
        "requested_max_bond": None,
        "requested_truncation": False,
        "split_method": _SPLIT_METHOD,
        "cutoff_mode": _CUTOFF_MODE,
        "quimb_version": quimb_version,
        "input_norm_sq": float(input_norm_sq),
        "output_norm_sq": float(output_norm_sq),
        "norm_drift_abs": float(norm_drift),
        "source_unchanged": True,
        "context": dict(context or {}),
        "not_a_scientific_carrier": True,
        "epistemic_class": "c",
    }
    return candidate, event


__all__ = [
    "MAX_DENSE_OPERATOR_ELEMENTS",
    "MAX_SUPPORT_HILBERT_DIMENSION",
    "MAX_SUPPORT_SITES",
    "apply_uncapped_nonlocal_unitary",
    "preflight_uncapped_nonlocal_resource",
]
