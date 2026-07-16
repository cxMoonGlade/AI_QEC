from __future__ import annotations

"""Actual-split finite-bond adapter for restricted two-site MPS unitaries.

Quimb 1.14.0 does not expose a per-split callback through ``auto-mps``.  This
module mirrors its two-site auto-swap order with low-level ``Tensor.split``
calls so every SVD truncation is measured at the operation that actually
changes the state.  It is intentionally restricted to open-boundary,
complex128, qubit MPS states and unitary/Hamiltonian gates.  Kraus and MCWF
branch operators must not use this helper because their raw norm carries a
physical branch probability.
"""

from collections.abc import Mapping
import importlib.metadata
import math
import operator
from typing import Any

import torch

from ..numerics import NUMERICAL_ZERO


_SUPPORTED_QUIMB_VERSION = "1.14.0"
_SPLIT_METHOD = "svd"
_SPLIT_CUTOFF = 0.0
_SPLIT_CUTOFF_MODE = "rsum2"
_SPLIT_RENORM = None


def normalize_mps_max_bond(
    value: Any,
    *,
    allow_none: bool = True,
) -> int | None:
    """Normalize a bond cap without lossy ``int(...)`` coercion."""
    if value is None:
        if allow_none:
            return None
        raise TypeError("max_bond must be an integer, got None")
    if isinstance(value, bool):
        raise TypeError("max_bond must be an integer, not bool")
    try:
        normalized = operator.index(value)
    except TypeError as exc:
        raise TypeError(f"max_bond must be an integer, got {value!r}") from exc
    if normalized < 1:
        raise ValueError(
            f"max_bond must be positive (>= 1), got {normalized}"
        )
    return int(normalized)


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


def _frobenius_weight(data: torch.Tensor) -> float:
    flat = data.reshape(-1)
    return _finite_real_scalar(
        torch.vdot(flat, flat).real,
        name="pre-split local Frobenius weight",
    )


def _mps_norm_sq(mps: Any) -> float:
    return _finite_real_scalar(mps.H @ mps, name="MPS norm squared")


def _assert_quimb_contract() -> str:
    version = importlib.metadata.version("quimb")
    if version != _SUPPORTED_QUIMB_VERSION:
        raise RuntimeError(
            "actual-split adapter is pinned to quimb "
            f"{_SUPPORTED_QUIMB_VERSION}, found {version}"
        )
    return version


def _preflight(
    mps: Any,
    gate: torch.Tensor,
    *,
    support: tuple[int, int],
    max_bond: int,
) -> tuple[torch.Tensor, torch.device]:
    if bool(getattr(mps, "cyclic", False)):
        raise ValueError("actual-split adapter supports open-boundary MPS only")
    if int(max_bond) < 1:
        raise ValueError(f"max_bond must be >= 1, got {max_bond}")
    if len(support) != 2 or int(support[0]) == int(support[1]):
        raise ValueError(f"support must contain two distinct sites, got {support!r}")
    a, b = (int(support[0]), int(support[1]))
    length = int(mps.L)
    if not (0 <= a < length and 0 <= b < length):
        raise ValueError(f"support {support!r} lies outside MPS length {length}")

    site_arrays = [mps[i].data for i in range(length)]
    if not site_arrays or not all(isinstance(array, torch.Tensor) for array in site_arrays):
        raise TypeError("actual-split adapter requires Torch-backed MPS tensors")
    device = site_arrays[0].device
    for index, array in enumerate(site_arrays):
        if array.dtype != torch.complex128:
            raise TypeError(
                f"MPS site {index} must use torch.complex128, got {array.dtype}"
            )
        if array.device != device:
            raise ValueError("all MPS site tensors must occupy the same device")
        physical_dim = int(mps.ind_size(mps.site_ind(index)))
        if physical_dim != 2:
            raise ValueError(
                "finite-bond actual-split adapter currently supports qubit sites "
                f"only; site {index} has local dimension {physical_dim}"
            )

    gate = torch.as_tensor(gate)
    if gate.dtype != torch.complex128:
        raise TypeError(f"gate must use torch.complex128, got {gate.dtype}")
    if gate.device != device:
        raise ValueError(f"gate device {gate.device} does not match MPS device {device}")
    if tuple(gate.shape) != (4, 4):
        raise ValueError(f"two-qubit gate must have shape (4, 4), got {tuple(gate.shape)}")
    if not bool(torch.isfinite(gate).all().item()):
        raise ValueError("two-qubit gate contains non-finite values")
    identity = torch.eye(4, dtype=torch.complex128, device=device)
    unitary_residual = _finite_real_scalar(
        torch.linalg.matrix_norm(gate.conj().mT @ gate - identity),
        name="gate unitarity residual",
    )
    if unitary_residual > NUMERICAL_ZERO:
        raise ValueError(
            "actual-split norm restoration is restricted to unitary gates; "
            f"unitarity residual={unitary_residual:.3e}"
        )
    return gate, device


def _split_with_event(
    joined: Any,
    *,
    left_inds: list[str] | tuple[str, ...],
    right_inds: list[str] | tuple[str, ...] | None,
    bond_ind: str | None,
    absorb: str,
    path_role: str,
    split_sites: tuple[int, int],
    gate_leg_sites: tuple[int, int] | None,
    max_bond: int,
    sequence_index: int,
) -> tuple[Any, Any, dict[str, Any]]:
    split_info: dict[str, Any] = {}
    kwargs: dict[str, Any] = {
        "left_inds": list(left_inds),
        "absorb": str(absorb),
        "get": "tensors",
        "method": _SPLIT_METHOD,
        "max_bond": int(max_bond),
        "cutoff": _SPLIT_CUTOFF,
        "cutoff_mode": _SPLIT_CUTOFF_MODE,
        "renorm": _SPLIT_RENORM,
        "info": split_info,
    }
    if right_inds is not None:
        kwargs["right_inds"] = list(right_inds)
    if bond_ind is not None:
        kwargs["bond_ind"] = str(bond_ind)

    pre_split_weight = _frobenius_weight(joined.data)
    if pre_split_weight <= 0.0:
        raise RuntimeError("pre-split local Frobenius weight must be positive")
    result = joined.split(**kwargs)
    if not isinstance(result, tuple) or len(result) != 2:
        raise RuntimeError("quimb Tensor.split return contract drifted")
    left, right = result
    if "error" not in split_info:
        raise RuntimeError("quimb Tensor.split did not emit info['error']")
    error = _finite_real_scalar(split_info["error"], name="split truncation error")
    if error < 0.0:
        raise RuntimeError(f"split truncation error must be nonnegative, got {error}")
    discarded_raw = float(error * error)
    if discarded_raw > pre_split_weight + (
        100.0 * NUMERICAL_ZERO * max(1.0, pre_split_weight)
    ):
        raise RuntimeError(
            "split discarded weight exceeds its pre-split Frobenius weight: "
            f"{discarded_raw:.17g} > {pre_split_weight:.17g}"
        )
    shared = tuple(left.bonds(right))
    if len(shared) != 1:
        raise RuntimeError(
            f"split tensors must share exactly one bond, found {shared!r}"
        )
    kept_rank = int(left.ind_size(shared[0]))
    if not 1 <= kept_rank <= int(max_bond):
        raise RuntimeError(
            f"actual kept rank {kept_rank} violates requested max_bond={max_bond}"
        )
    event = {
        "sequence_index": int(sequence_index),
        "path_role": str(path_role),
        "split_sites": [int(split_sites[0]), int(split_sites[1])],
        "gate_leg_sites": (
            None
            if gate_leg_sites is None
            else [int(gate_leg_sites[0]), int(gate_leg_sites[1])]
        ),
        "requested_method": _SPLIT_METHOD,
        "requested_absorb": str(absorb),
        "requested_max_bond": int(max_bond),
        "requested_cutoff": _SPLIT_CUTOFF,
        "requested_cutoff_mode": _SPLIT_CUTOFF_MODE,
        "requested_renorm": _SPLIT_RENORM,
        "pre_split_total_weight": float(pre_split_weight),
        "actual_kept_rank": int(kept_rank),
        "actual_discarded_weight_raw": float(discarded_raw),
        "actual_discarded_weight_fraction_of_pre_split": float(
            discarded_raw / pre_split_weight
        ),
        "not_a_global_error_bound": True,
    }
    return left, right, event


def _swap_adjacent(
    candidate: Any,
    i: int,
    j: int,
    *,
    absorb: str,
    path_role: str,
    orthogonality_info: dict[str, Any],
    max_bond: int,
    sequence_index: int,
) -> dict[str, Any]:
    i, j = sorted((int(i), int(j)))
    if j != i + 1:
        raise ValueError(f"adjacent swap requires neighboring sites, got {(i, j)!r}")
    candidate.canonicalize_((i, j), info=orthogonality_info)
    ix_i, ix_j = candidate.site_ind(i), candidate.site_ind(j)
    tensor_i, tensor_j = candidate[i], candidate[j]
    shared = tuple(tensor_i.bonds(tensor_j))
    if len(shared) != 1:
        raise RuntimeError(
            f"open-MPS adjacent sites {(i, j)!r} must share one bond, found {shared!r}"
        )
    _, unshared = tensor_i.filter_bonds(tensor_j)
    joined = tensor_i @ tensor_j
    left_inds = [index for index in unshared if index != ix_i] + [ix_j]
    split_i, split_j, event = _split_with_event(
        joined,
        left_inds=left_inds,
        right_inds=None,
        bond_ind=None,
        absorb=absorb,
        path_role=path_role,
        split_sites=(i, j),
        gate_leg_sites=None,
        max_bond=max_bond,
        sequence_index=sequence_index,
    )
    split_i.reindex_({ix_j: ix_i}).transpose_like_(tensor_i)
    split_j.reindex_({ix_i: ix_j}).transpose_like_(tensor_j)
    tensor_i.modify(data=split_i.data)
    tensor_j.modify(data=split_j.data)
    orthogonality_info["cur_orthog"] = (i, i) if absorb == "left" else (j, j)
    return event


def _operator_split(
    candidate: Any,
    gate: torch.Tensor,
    *,
    where: tuple[int, int],
    absorb: str,
    max_bond: int,
    sequence_index: int,
) -> dict[str, Any]:
    import quimb.tensor as qtn
    from quimb.tensor.tensor_core import rand_uuid

    q0, q1 = (int(where[0]), int(where[1]))
    ix0, ix1 = candidate.site_ind(q0), candidate.site_ind(q1)
    tensor0, tensor1 = candidate[q0], candidate[q1]
    left_only, shared, right_only = qtn.group_inds(tensor0, tensor1)
    if len(shared) != 1:
        raise RuntimeError(
            f"operator sites {where!r} must share exactly one MPS bond, found {shared!r}"
        )
    old_bond = shared[0]
    input0, input1 = rand_uuid(), rand_uuid()
    dim0 = int(candidate.ind_size(ix0))
    dim1 = int(candidate.ind_size(ix1))
    gate_tensor = qtn.Tensor(
        gate.reshape(dim0, dim1, dim0, dim1),
        inds=(ix0, ix1, input0, input1),
        left_inds=(input0, input1),
    )
    joined = qtn.tensor_contract(
        tensor0.reindex({ix0: input0}),
        tensor1.reindex({ix1: input1}),
        gate_tensor,
    )
    split0, split1, event = _split_with_event(
        joined,
        left_inds=list(left_only),
        right_inds=list(right_only),
        bond_ind=old_bond,
        absorb=absorb,
        path_role="two_site_operator_split",
        split_sites=tuple(sorted(where)),
        gate_leg_sites=where,
        max_bond=max_bond,
        sequence_index=sequence_index,
    )
    split0.transpose_like_(tensor0)
    split1.transpose_like_(tensor1)
    tensor0.modify(data=split0.data)
    tensor1.modify(data=split1.data)
    return event


def apply_capped_two_site_unitary(
    mps: Any,
    gate: torch.Tensor,
    *,
    support: tuple[int, int],
    max_bond: int,
    context: Mapping[str, Any] | None = None,
) -> tuple[Any, dict[str, Any]]:
    """Return a compressed candidate and its per-actual-SVD risk ledger.

    ``mps`` is never mutated.  The caller may commit the returned candidate only
    after any higher-level checks pass.  The state norm is restored because this
    helper is restricted to deterministic unitary evolution; the raw norm loss
    remains recorded and is explicitly not a physical branch probability.
    """
    quimb_version = _assert_quimb_contract()
    normalized_max_bond = normalize_mps_max_bond(max_bond, allow_none=False)
    assert normalized_max_bond is not None
    normalized_support = (int(support[0]), int(support[1]))
    gate, _device = _preflight(
        mps,
        gate,
        support=normalized_support,
        max_bond=normalized_max_bond,
    )
    candidate = mps.copy()
    input_norm_sq = _mps_norm_sq(candidate)
    if input_norm_sq <= 0.0:
        raise RuntimeError("input MPS norm squared must be positive")

    a, b = normalized_support
    lo, hi = sorted((a, b))
    if a < b:
        final_where = (lo, lo + 1)
        operator_absorb = "right"
    else:
        final_where = (lo + 1, lo)
        operator_absorb = "left"

    split_records: list[dict[str, Any]] = []
    orthogonality_info: dict[str, Any] = {"cur_orthog": "calc"}
    for k in range(hi - 1, lo, -1):
        split_records.append(
            _swap_adjacent(
                candidate,
                k,
                k + 1,
                absorb="left",
                path_role="forward_swap_split",
                orthogonality_info=orthogonality_info,
                max_bond=normalized_max_bond,
                sequence_index=len(split_records),
            )
        )

    candidate.canonicalize_((lo, lo + 1), info=orthogonality_info)
    split_records.append(
        _operator_split(
            candidate,
            gate,
            where=final_where,
            absorb=operator_absorb,
            max_bond=normalized_max_bond,
            sequence_index=len(split_records),
        )
    )
    orthogonality_info["cur_orthog"] = (lo + 1, lo + 1)

    for k in range(lo + 1, hi):
        split_records.append(
            _swap_adjacent(
                candidate,
                k,
                k + 1,
                absorb="right",
                path_role="reverse_swap_split",
                orthogonality_info=orthogonality_info,
                max_bond=normalized_max_bond,
                sequence_index=len(split_records),
            )
        )

    expected_split_count = 2 * (hi - lo - 1) + 1
    if len(split_records) != expected_split_count:
        raise RuntimeError(
            "actual split-count invariant failed: "
            f"{len(split_records)} != {expected_split_count}"
        )
    raw_output_norm_sq = _mps_norm_sq(candidate)
    if raw_output_norm_sq <= 0.0:
        raise RuntimeError("capped unitary produced a nonpositive raw norm")
    if raw_output_norm_sq > input_norm_sq + NUMERICAL_ZERO * max(1.0, input_norm_sq):
        raise RuntimeError(
            "capped unitary increased norm beyond numerical tolerance: "
            f"{raw_output_norm_sq} > {input_norm_sq}"
        )
    discarded_raw = [
        float(record["actual_discarded_weight_raw"])
        for record in split_records
    ]
    discarded_raw_sum = float(sum(discarded_raw))
    observed_norm_loss = float(max(0.0, input_norm_sq - raw_output_norm_sq))
    consistency_scale = max(1.0, input_norm_sq, discarded_raw_sum)
    if abs(discarded_raw_sum - observed_norm_loss) > (
        100.0 * NUMERICAL_ZERO * consistency_scale
    ):
        raise RuntimeError(
            "actual-split discarded-weight ledger disagrees with observed unitary "
            "norm loss: "
            f"sum(error^2)={discarded_raw_sum:.17g}, "
            f"norm_loss={observed_norm_loss:.17g}"
        )
    restore_factor = math.sqrt(input_norm_sq / raw_output_norm_sq)
    if not math.isfinite(restore_factor) or restore_factor <= 0.0:
        raise RuntimeError(f"invalid deterministic norm restore factor {restore_factor!r}")
    candidate.multiply_(restore_factor, spread_over=1)
    restored_output_norm_sq = _mps_norm_sq(candidate)
    if not math.isclose(
        restored_output_norm_sq,
        input_norm_sq,
        rel_tol=NUMERICAL_ZERO,
        abs_tol=NUMERICAL_ZERO,
    ):
        raise RuntimeError(
            "deterministic MPS norm restoration failed: "
            f"{restored_output_norm_sq} != {input_norm_sq}"
        )

    discarded_fraction = [
        float(record["actual_discarded_weight_fraction_of_pre_split"])
        for record in split_records
    ]
    event = dict(context or {})
    event.update(
        {
            "support": [a, b],
            "gate_leg_sites": [int(final_where[0]), int(final_where[1])],
            "max_bond": normalized_max_bond,
            "quimb_version": str(quimb_version),
            "input_norm_sq": float(input_norm_sq),
            "raw_output_norm_sq": float(raw_output_norm_sq),
            "restored_output_norm_sq": float(restored_output_norm_sq),
            "deterministic_norm_restore_factor": float(restore_factor),
            "unitary_truncation_mass_loss": float(
                observed_norm_loss
            ),
            "physical_branch_probability": None,
            "split_count": len(split_records),
            "split_records": split_records,
            "actual_discarded_weight_raw_sum": discarded_raw_sum,
            "actual_discarded_weight_fraction_sum": float(sum(discarded_fraction)),
            "worst_actual_discarded_weight_fraction": float(
                max(discarded_fraction, default=0.0)
            ),
            "ledger_semantics": "per_actual_svd_split_heuristic_not_global_bound",
            "not_a_global_error_bound": True,
        }
    )
    return candidate, event


def commit_mps_candidate_(target: Any, candidate: Any) -> None:
    """Commit an already-validated candidate with rollback on an update error."""
    if int(target.L) != int(candidate.L):
        raise ValueError("target and candidate MPS lengths differ")
    old_arrays: list[torch.Tensor] = []
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
