from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import torch


def _as_bool_matrix(raw_masks: torch.Tensor | Iterable[Iterable[int]]) -> torch.Tensor:
    masks = torch.as_tensor(raw_masks, dtype=torch.bool)
    if masks.ndim != 2:
        raise ValueError("raw masks must have shape [B, M]")
    return masks


def _mask_key(column: torch.Tensor) -> tuple[int, ...]:
    return tuple(int(v) for v in column.to(dtype=torch.uint8).cpu().tolist())


def gf2_rank(matrix: torch.Tensor) -> int:
    """Compute rank over F_2 using Python integer row reduction."""

    mat = torch.as_tensor(matrix, dtype=torch.bool).cpu()
    if mat.ndim != 2:
        raise ValueError("matrix must be rank-2")
    rows, cols = mat.shape
    row_bits: list[int] = []
    for row in range(rows):
        bits = 0
        for col in range(cols):
            if bool(mat[row, col]):
                bits |= 1 << col
        row_bits.append(bits)

    rank = 0
    for col in reversed(range(cols)):
        pivot = None
        for row in range(rank, rows):
            if (row_bits[row] >> col) & 1:
                pivot = row
                break
        if pivot is None:
            continue
        row_bits[rank], row_bits[pivot] = row_bits[pivot], row_bits[rank]
        for row in range(rows):
            if row != rank and ((row_bits[row] >> col) & 1):
                row_bits[row] ^= row_bits[rank]
        rank += 1
        if rank == rows:
            break
    return rank


def combine_duplicate_probabilities(probabilities: torch.Tensor) -> torch.Tensor:
    """Combine indistinguishable Bernoulli faults with identical parity masks."""

    probs = torch.as_tensor(probabilities)
    if probs.numel() == 0:
        raise ValueError("cannot combine an empty duplicate group")
    return (1 - torch.prod(1 - 2 * probs)) / 2


def _column_state(column: torch.Tensor) -> int:
    state = 0
    for bit, value in enumerate(column.to(dtype=torch.bool).cpu().tolist()):
        if value:
            state |= 1 << bit
    return state


def mask_states_from_matrix(matrix: torch.Tensor) -> torch.Tensor:
    mat = torch.as_tensor(matrix, dtype=torch.bool).cpu()
    return torch.tensor([_column_state(mat[:, col]) for col in range(mat.shape[1])], dtype=torch.long)


def sparse_supports_from_matrix(
    matrix: torch.Tensor,
) -> tuple[tuple[tuple[int, ...], ...], tuple[tuple[int, ...], ...]]:
    """Build sparse parity-map adjacency views from a dense compatibility matrix."""

    mat = torch.as_tensor(matrix, dtype=torch.bool).cpu()
    supports_by_fault = tuple(
        tuple(int(bit) for bit in torch.nonzero(mat[:, fault], as_tuple=False).flatten().tolist())
        for fault in range(mat.shape[1])
    )
    faults_by_bit: list[list[int]] = [[] for _ in range(mat.shape[0])]
    for fault, support in enumerate(supports_by_fault):
        for bit in support:
            faults_by_bit[bit].append(fault)
    return supports_by_fault, tuple(tuple(faults) for faults in faults_by_bit)


def packed_masks64_from_supports(supports_by_fault: tuple[tuple[int, ...], ...], num_bits: int) -> tuple[tuple[int, ...], ...]:
    """Pack each sparse support into little-endian 64-bit chunks.

    This is independent of the exact-DP single-word state limit. Large graphs
    can still use the sparse supports; small exact paths use chunk 0 as before.
    """

    num_chunks = max(1, (int(num_bits) + 63) // 64)
    packed = []
    for support in supports_by_fault:
        chunks = [0] * num_chunks
        for bit in support:
            chunk = int(bit) // 64
            offset = int(bit) % 64
            chunks[chunk] |= 1 << offset
        packed.append(tuple(chunks))
    return tuple(packed)


def mask_states_from_packed_masks64(packed_masks64: tuple[tuple[int, ...], ...], num_bits: int) -> torch.Tensor:
    if num_bits >= 63:
        raise ValueError("single-word exact state indexing currently requires B < 63")
    return torch.tensor([chunks[0] if chunks else 0 for chunks in packed_masks64], dtype=torch.long)


def _standardize_features(features: torch.Tensor) -> torch.Tensor:
    features = features - features.mean(dim=0, keepdim=True)
    scale = features.std(dim=0, keepdim=True, unbiased=False).clamp_min(1e-12)
    return features / scale


def fixed_fault_feature_candidates(
    masks: torch.Tensor,
    detector_coordinates: torch.Tensor | None,
    num_detectors: int,
    *,
    min_features: int = 0,
) -> torch.Tensor:
    """Create deterministic fixed fault-level raw feature candidates."""

    if min_features < 0:
        raise ValueError("min_features must be non-negative")
    m = masks.shape[1]
    if m == 0:
        return torch.empty((0, min_features), dtype=torch.float64)

    mask_f = masks.to(dtype=torch.float64)
    detector_part = mask_f[:num_detectors]
    logical_part = mask_f[num_detectors:]
    detector_weight = detector_part.sum(dim=0)
    total_weight = mask_f.sum(dim=0)
    logical_weight = logical_part.sum(dim=0)
    base_features = [
        total_weight / max(1, masks.shape[0]),
        detector_weight / max(1, num_detectors),
        logical_weight / max(1, masks.shape[0] - num_detectors),
    ]

    if detector_coordinates is not None and num_detectors > 0:
        coords = detector_coordinates.to(dtype=torch.float64)
        for coord_dim in range(coords.shape[1]):
            values = coords[:, coord_dim].unsqueeze(1)
            denom = detector_weight.clamp_min(1.0)
            mean_coord = (detector_part * values).sum(dim=0) / denom
            max_abs = mean_coord.abs().max().clamp_min(1.0)
            base_features.append(mean_coord / max_abs)

    index = torch.arange(m, dtype=torch.float64)
    denom = max(1, m - 1)
    base_features.append(index / denom)
    base_features.append(torch.sin((index + 1) * 1.61803398875))
    base_features.append(torch.cos((index + 1) * 1.61803398875))

    features = torch.stack(base_features, dim=1)
    while features.shape[1] < min_features:
        k = features.shape[1] + 1
        extra = torch.sin((index + 1) * (k + 0.5)).unsqueeze(1)
        features = torch.cat([features, extra], dim=1)

    return _standardize_features(features)


def select_intra_orbit_feature_indices(
    features: torch.Tensor,
    orbit_ids: torch.Tensor,
    residual_rank: int,
) -> torch.Tensor:
    """Choose raw feature columns with the most centered within-orbit variation."""

    if residual_rank < 0:
        raise ValueError("residual_rank must be non-negative")
    if residual_rank == 0:
        return torch.empty((0,), dtype=torch.long)
    phi = torch.as_tensor(features, dtype=torch.float64)
    if phi.ndim != 2:
        raise ValueError("features must have shape [M, F]")
    centered = center_features_within_orbits(phi, orbit_ids)
    energies = (centered**2).sum(dim=0)
    order = sorted(range(phi.shape[1]), key=lambda idx: (-float(energies[idx]), idx))
    if len(order) < residual_rank:
        order.extend(range(len(order), residual_rank))
    return torch.tensor(order[:residual_rank], dtype=torch.long)


def fixed_fault_features(
    masks: torch.Tensor,
    detector_coordinates: torch.Tensor | None,
    residual_rank: int,
    num_detectors: int,
    orbit_ids: torch.Tensor | None = None,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Create selected deterministic fault-level raw features in R^r."""

    if residual_rank < 0:
        raise ValueError("residual_rank must be non-negative")
    m = masks.shape[1]
    if residual_rank == 0:
        return torch.empty((m, 0), dtype=torch.float64), torch.empty((0,), dtype=torch.long)

    candidate_count = max(residual_rank, 8)
    candidates = fixed_fault_feature_candidates(
        masks,
        detector_coordinates,
        num_detectors,
        min_features=candidate_count,
    )
    if orbit_ids is None:
        selected = torch.arange(residual_rank, dtype=torch.long)
    else:
        selected = select_intra_orbit_feature_indices(candidates, torch.as_tensor(orbit_ids), residual_rank)
    return candidates[:, selected], selected


def center_features_within_orbits(features: torch.Tensor, orbit_ids: torch.Tensor) -> torch.Tensor:
    """Center fault-level features within each known DEM-fault orbit."""

    phi = torch.as_tensor(features)
    orbits = torch.as_tensor(orbit_ids, dtype=torch.long)
    if phi.ndim != 2:
        raise ValueError("features must have shape [M, r]")
    if phi.shape[0] != orbits.numel():
        raise ValueError("features and orbit_ids must agree on M")
    centered = phi.clone()
    for omega in orbits.unique(sorted=True):
        idx = orbits == omega
        centered[idx] = centered[idx] - centered[idx].mean(dim=0, keepdim=True)
    return centered


def feature_rank_by_orbit(features: torch.Tensor, orbit_ids: torch.Tensor) -> dict[int, int]:
    """Return centered feature rank for each DEM-fault orbit."""

    phi = torch.as_tensor(features)
    orbits = torch.as_tensor(orbit_ids, dtype=torch.long)
    if phi.ndim != 2:
        raise ValueError("features must have shape [M, r]")
    if phi.shape[0] != orbits.numel():
        raise ValueError("features and orbit_ids must agree on M")

    num_orbits = int(orbits.max().item() + 1) if orbits.numel() else 0
    ranks: dict[int, int] = {}
    for omega in range(num_orbits):
        idx = orbits == omega
        if int(idx.sum().item()) <= 1 or phi.shape[1] == 0:
            ranks[omega] = 0
            continue
        centered = phi[idx] - phi[idx].mean(dim=0, keepdim=True)
        ranks[omega] = int(torch.linalg.matrix_rank(centered).item())
    return ranks


def fixed_residual_features(
    masks: torch.Tensor,
    detector_coordinates: torch.Tensor | None,
    residual_rank: int,
    num_detectors: int,
    orbit_ids: torch.Tensor | None = None,
) -> torch.Tensor:
    """Create deterministic fixed residual features, centered when orbits are given."""

    raw_features, _selected = fixed_fault_features(
        masks,
        detector_coordinates,
        residual_rank,
        num_detectors,
        orbit_ids=orbit_ids,
    )
    if orbit_ids is None:
        return raw_features
    return center_features_within_orbits(raw_features, orbit_ids)


def default_orbit_ids(
    masks: torch.Tensor,
    detector_coordinates: torch.Tensor | None,
    num_detectors: int,
) -> torch.Tensor:
    """Assign known Stage-1 orbits from observable parity-mask features."""

    keys: list[tuple[object, ...]] = []
    for col in range(masks.shape[1]):
        mask = masks[:, col]
        detector_ids = torch.nonzero(mask[:num_detectors], as_tuple=False).flatten().tolist()
        logical_weight = int(mask[num_detectors:].sum().item())
        detector_weight = len(detector_ids)
        if detector_coordinates is None or not detector_ids:
            coord_key: tuple[object, ...] = ()
        else:
            coords = detector_coordinates[detector_ids].to(dtype=torch.float64)
            mins = coords.min(dim=0).values
            maxs = coords.max(dim=0).values
            span = tuple(round(float(v), 6) for v in (maxs - mins).tolist())
            center = tuple(round(float(v * 2) / 2, 3) for v in coords.mean(dim=0).tolist())
            coord_key = (span, center[-1] if center else 0.0)
        keys.append((detector_weight, logical_weight, coord_key))

    orbit_map: dict[tuple[object, ...], int] = {}
    orbit_ids: list[int] = []
    for key in keys:
        orbit_ids.append(orbit_map.setdefault(key, len(orbit_map)))
    return torch.tensor(orbit_ids, dtype=torch.long)


@dataclass(frozen=True)
class FaultGraph:
    """Canonicalized DEM parity-map graph for Stage-1 SCOPE-Static."""

    A: torch.Tensor
    num_detectors: int
    num_observables: int
    raw_to_effective: torch.Tensor
    effective_to_raw: tuple[tuple[int, ...], ...]
    duplicate_mask_groups: tuple[tuple[int, ...], ...]
    zero_mask_raw_indices: tuple[int, ...]
    orbit_ids: torch.Tensor
    orbit_sizes: torch.Tensor
    template_ids: torch.Tensor
    raw_features: torch.Tensor
    residual_features: torch.Tensor
    selected_feature_indices: torch.Tensor
    feature_rank_by_orbit: dict[int, int]
    supports_by_fault: tuple[tuple[int, ...], ...]
    faults_by_observation_bit: tuple[tuple[int, ...], ...]
    packed_masks64: tuple[tuple[int, ...], ...]
    detector_coordinates: torch.Tensor | None = None
    effective_probabilities: torch.Tensor | None = None

    @classmethod
    def from_raw_masks(
        cls,
        raw_masks: torch.Tensor | Iterable[Iterable[int]],
        *,
        num_detectors: int,
        num_observables: int,
        raw_probabilities: torch.Tensor | Iterable[float] | None = None,
        detector_coordinates: torch.Tensor | Iterable[Iterable[float]] | None = None,
        residual_rank: int = 0,
        canonicalize_duplicate_masks: bool = True,
        orbit_ids: torch.Tensor | Iterable[int] | None = None,
        template_ids: torch.Tensor | Iterable[int] | None = None,
    ) -> "FaultGraph":
        masks = _as_bool_matrix(raw_masks)
        expected_b = int(num_detectors) + int(num_observables)
        if masks.shape[0] != expected_b:
            raise ValueError(f"raw masks have B={masks.shape[0]}, expected {expected_b}")

        probs = None if raw_probabilities is None else torch.as_tensor(raw_probabilities, dtype=torch.float64)
        if probs is not None and probs.numel() != masks.shape[1]:
            raise ValueError("raw_probabilities must have one entry per raw mask")

        coords = None
        if detector_coordinates is not None:
            coords = torch.as_tensor(detector_coordinates, dtype=torch.float64)
            if coords.shape[0] != num_detectors:
                raise ValueError("detector_coordinates must have one row per detector")

        if canonicalize_duplicate_masks:
            graph_parts = _canonicalize_masks(masks, probs)
            eff_masks = graph_parts["A"]
            raw_to_eff = graph_parts["raw_to_effective"]
            eff_to_raw = graph_parts["effective_to_raw"]
            duplicates = graph_parts["duplicate_mask_groups"]
            zero_indices = graph_parts["zero_mask_raw_indices"]
            eff_probs = graph_parts["effective_probabilities"]
        else:
            keep = [idx for idx in range(masks.shape[1]) if bool(masks[:, idx].any())]
            eff_masks = masks[:, keep].clone()
            raw_to_eff = torch.full((masks.shape[1],), -1, dtype=torch.long)
            for eff, raw in enumerate(keep):
                raw_to_eff[raw] = eff
            eff_to_raw = tuple((raw,) for raw in keep)
            groups: dict[tuple[int, ...], list[int]] = {}
            for raw in keep:
                groups.setdefault(_mask_key(masks[:, raw]), []).append(raw)
            duplicates = tuple(tuple(v) for v in groups.values() if len(v) > 1)
            zero_indices = tuple(idx for idx in range(masks.shape[1]) if not bool(masks[:, idx].any()))
            eff_probs = None if probs is None else probs[keep].clone()

        if orbit_ids is None:
            orbits = default_orbit_ids(eff_masks, coords, num_detectors)
        else:
            orbits = torch.as_tensor(orbit_ids, dtype=torch.long)
            if orbits.numel() != eff_masks.shape[1]:
                raise ValueError("orbit_ids must have one entry per effective mask")

        if template_ids is None:
            templates = torch.zeros(eff_masks.shape[1], dtype=torch.long)
        else:
            templates = torch.as_tensor(template_ids, dtype=torch.long)
            if templates.numel() != eff_masks.shape[1]:
                raise ValueError("template_ids must have one entry per effective mask")

        raw_features, selected_feature_indices = fixed_fault_features(
            eff_masks,
            coords,
            residual_rank,
            num_detectors,
            orbit_ids=orbits,
        )
        residual_features = center_features_within_orbits(raw_features, orbits)
        num_orbits = int(orbits.max().item() + 1) if orbits.numel() else 0
        orbit_sizes = torch.bincount(orbits, minlength=num_orbits).to(dtype=torch.long)
        ranks = feature_rank_by_orbit(residual_features, orbits)
        supports_by_fault, faults_by_observation_bit = sparse_supports_from_matrix(eff_masks)
        packed_masks64 = packed_masks64_from_supports(supports_by_fault, eff_masks.shape[0])
        return cls(
            A=eff_masks.contiguous(),
            num_detectors=int(num_detectors),
            num_observables=int(num_observables),
            raw_to_effective=raw_to_eff,
            effective_to_raw=eff_to_raw,
            duplicate_mask_groups=duplicates,
            zero_mask_raw_indices=zero_indices,
            orbit_ids=orbits.contiguous(),
            orbit_sizes=orbit_sizes.contiguous(),
            template_ids=templates.contiguous(),
            raw_features=raw_features.contiguous(),
            residual_features=residual_features.contiguous(),
            selected_feature_indices=selected_feature_indices.contiguous(),
            feature_rank_by_orbit=ranks,
            supports_by_fault=supports_by_fault,
            faults_by_observation_bit=faults_by_observation_bit,
            packed_masks64=packed_masks64,
            detector_coordinates=coords,
            effective_probabilities=None if eff_probs is None else eff_probs.contiguous(),
        )

    @property
    def B(self) -> int:
        return int(self.A.shape[0])

    @property
    def M(self) -> int:
        return int(self.A.shape[1])

    @property
    def O(self) -> int:
        return int(self.orbit_ids.max().item() + 1) if self.orbit_ids.numel() else 0

    @property
    def residual_rank(self) -> int:
        return int(self.residual_features.shape[1])

    @property
    def phi(self) -> torch.Tensor:
        """Backward-compatible alias for fault-level residual features."""

        return self.residual_features

    @property
    def mask_states(self) -> torch.Tensor:
        return mask_states_from_packed_masks64(self.packed_masks64, self.B)

    @property
    def num_sparse_support_entries(self) -> int:
        return sum(len(support) for support in self.supports_by_fault)

    def residual_feature_audit_dict(self) -> dict[str, object]:
        non_singleton_ranks = [
            int(self.feature_rank_by_orbit.get(omega, 0))
            for omega, size in enumerate(self.orbit_sizes.tolist())
            if int(size) > 1
        ]
        num_nonzero = sum(1 for rank in non_singleton_ranks if rank > 0)
        mean_rank = float(sum(non_singleton_ranks) / len(non_singleton_ranks)) if non_singleton_ranks else 0.0
        max_rank = max(non_singleton_ranks) if non_singleton_ranks else 0
        return {
            "num_orbits": self.O,
            "num_non_singleton_orbits": len(non_singleton_ranks),
            "num_orbits_with_nonzero_centered_feature_rank": num_nonzero,
            "mean_centered_feature_rank": mean_rank,
            "max_centered_feature_rank": max_rank,
            "selected_feature_indices": [int(idx) for idx in self.selected_feature_indices.tolist()],
        }

    def audit_dict(
        self,
        *,
        exact_likelihood_trainable: bool,
        dem_fault_logit_claim: bool,
        cptp_gksl_claim: bool,
    ) -> dict[str, object]:
        state_count = 1 << self.B if self.B < 63 else None
        audit = {
            "num_observation_bits_B": self.B,
            "num_faults_raw_M": int(self.raw_to_effective.numel()),
            "num_faults_effective_M": self.M,
            "num_orbits_O": self.O,
            "gf2_rank_A": gf2_rank(self.A),
            "num_duplicate_mask_groups": len(self.duplicate_mask_groups),
            "state_count_2_pow_B": state_count,
            "log2_state_count": self.B,
            "global_exact_state_count_materialized": state_count is not None,
            "exact_likelihood_trainable": bool(exact_likelihood_trainable),
            "dem_fault_logit_claim": bool(dem_fault_logit_claim),
            "cptp_gksl_claim": bool(cptp_gksl_claim),
            "canonicalize_duplicate_masks": True,
            "num_zero_mask_raw_indices": len(self.zero_mask_raw_indices),
            "parity_storage": "sparse_supports_with_dense_A_compat",
            "dense_A_compat": True,
            "num_sparse_support_entries": self.num_sparse_support_entries,
            "max_fault_support_size": max((len(support) for support in self.supports_by_fault), default=0),
            "max_observation_fault_degree": max((len(faults) for faults in self.faults_by_observation_bit), default=0),
            "packed_mask64_chunks": len(self.packed_masks64[0]) if self.packed_masks64 else max(1, (self.B + 63) // 64),
        }
        audit.update(self.residual_feature_audit_dict())
        return audit


def _canonicalize_masks(
    masks: torch.Tensor,
    raw_probabilities: torch.Tensor | None,
) -> dict[str, object]:
    groups: dict[tuple[int, ...], list[int]] = {}
    zero_indices: list[int] = []
    for raw in range(masks.shape[1]):
        if not bool(masks[:, raw].any()):
            zero_indices.append(raw)
            continue
        groups.setdefault(_mask_key(masks[:, raw]), []).append(raw)

    ordered = sorted(groups.items(), key=lambda item: item[0])
    effective_columns = [torch.tensor(key, dtype=torch.bool) for key, _ in ordered]
    if effective_columns:
        effective_masks = torch.stack(effective_columns, dim=1)
    else:
        effective_masks = torch.empty((masks.shape[0], 0), dtype=torch.bool)

    raw_to_eff = torch.full((masks.shape[1],), -1, dtype=torch.long)
    effective_to_raw: list[tuple[int, ...]] = []
    duplicate_groups: list[tuple[int, ...]] = []
    effective_probs: list[torch.Tensor] = []
    for eff, (_, raw_indices) in enumerate(ordered):
        raw_tuple = tuple(raw_indices)
        effective_to_raw.append(raw_tuple)
        if len(raw_indices) > 1:
            duplicate_groups.append(raw_tuple)
        for raw in raw_indices:
            raw_to_eff[raw] = eff
        if raw_probabilities is not None:
            effective_probs.append(combine_duplicate_probabilities(raw_probabilities[raw_indices]))

    eff_prob_tensor = None
    if raw_probabilities is not None:
        eff_prob_tensor = torch.stack(effective_probs) if effective_probs else torch.empty(0, dtype=torch.float64)

    return {
        "A": effective_masks,
        "raw_to_effective": raw_to_eff,
        "effective_to_raw": tuple(effective_to_raw),
        "duplicate_mask_groups": tuple(duplicate_groups),
        "zero_mask_raw_indices": tuple(zero_indices),
        "effective_probabilities": eff_prob_tensor,
    }
