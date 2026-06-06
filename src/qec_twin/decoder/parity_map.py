from __future__ import annotations

from dataclasses import dataclass

import torch


def _column_state(column: torch.Tensor) -> int:
    state = 0
    for bit, value in enumerate(column.to(dtype=torch.bool).cpu().tolist()):
        if value:
            state |= 1 << bit
    return state


def mask_states_from_matrix(matrix: torch.Tensor) -> torch.Tensor:
    mat = torch.as_tensor(matrix, dtype=torch.bool).cpu()
    if mat.ndim != 2:
        raise ValueError("matrix must have shape [B, M]")
    return torch.tensor([_column_state(mat[:, col]) for col in range(mat.shape[1])], dtype=torch.long)


def sparse_supports_from_matrix(
    matrix: torch.Tensor,
) -> tuple[tuple[tuple[int, ...], ...], tuple[tuple[int, ...], ...]]:
    """Build sparse DEM parity-map adjacency views from a dense compatibility matrix."""

    mat = torch.as_tensor(matrix, dtype=torch.bool).cpu()
    if mat.ndim != 2:
        raise ValueError("matrix must have shape [B, M]")
    supports_by_fault = tuple(
        tuple(int(bit) for bit in torch.nonzero(mat[:, fault], as_tuple=False).flatten().tolist())
        for fault in range(mat.shape[1])
    )
    faults_by_bit: list[list[int]] = [[] for _ in range(mat.shape[0])]
    for fault, support in enumerate(supports_by_fault):
        for bit in support:
            faults_by_bit[bit].append(fault)
    return supports_by_fault, tuple(tuple(faults) for faults in faults_by_bit)


def packed_masks64_from_supports(
    supports_by_fault: tuple[tuple[int, ...], ...],
    num_bits: int,
) -> tuple[tuple[int, ...], ...]:
    """Pack each sparse support into little-endian 64-bit chunks."""

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


@dataclass(frozen=True)
class DemParityMap:
    """Sparse DEM parity map with optional dense compatibility storage."""

    num_observation_bits: int
    num_faults: int
    supports_by_fault: tuple[tuple[int, ...], ...]
    faults_by_observation_bit: tuple[tuple[int, ...], ...]
    packed_masks64: tuple[tuple[int, ...], ...]
    dense_A: torch.Tensor | None = None

    @classmethod
    def from_dense(cls, matrix: torch.Tensor, *, keep_dense: bool = True) -> "DemParityMap":
        mat = torch.as_tensor(matrix, dtype=torch.bool).cpu()
        if mat.ndim != 2:
            raise ValueError("matrix must have shape [B, M]")
        supports_by_fault, faults_by_observation_bit = sparse_supports_from_matrix(mat)
        return cls(
            num_observation_bits=int(mat.shape[0]),
            num_faults=int(mat.shape[1]),
            supports_by_fault=supports_by_fault,
            faults_by_observation_bit=faults_by_observation_bit,
            packed_masks64=packed_masks64_from_supports(supports_by_fault, int(mat.shape[0])),
            dense_A=mat.contiguous() if keep_dense else None,
        )

    @property
    def mask_states(self) -> torch.Tensor:
        return mask_states_from_packed_masks64(self.packed_masks64, self.num_observation_bits)

    @property
    def num_sparse_support_entries(self) -> int:
        return sum(len(support) for support in self.supports_by_fault)

    def to_dense(self) -> torch.Tensor:
        if self.dense_A is not None:
            return self.dense_A
        dense = torch.zeros((self.num_observation_bits, self.num_faults), dtype=torch.bool)
        for fault, support in enumerate(self.supports_by_fault):
            for bit in support:
                dense[int(bit), fault] = True
        return dense

    def apply_faults(self, faults: torch.Tensor) -> torch.Tensor:
        """Apply sampled fault bits to observation bits using sparse supports."""

        fault_bits = torch.as_tensor(faults, dtype=torch.bool)
        if fault_bits.ndim != 2 or fault_bits.shape[1] != self.num_faults:
            raise ValueError(f"faults must have shape [N, {self.num_faults}]")
        observations = torch.zeros(
            (int(fault_bits.shape[0]), self.num_observation_bits),
            dtype=torch.bool,
            device=fault_bits.device,
        )
        for fault, support in enumerate(self.supports_by_fault):
            if not support:
                continue
            active = fault_bits[:, fault]
            if not bool(active.any()):
                continue
            bits = torch.tensor(support, device=fault_bits.device, dtype=torch.long)
            observations[:, bits] = torch.logical_xor(observations[:, bits], active[:, None])
        return observations

    def project_window(self, window_bits: tuple[int, ...]) -> tuple[torch.Tensor, torch.Tensor]:
        """Return fault indices and packed local masks for a projected observation window."""

        if len(window_bits) >= 63:
            raise ValueError("window exact state indexing currently requires |W| < 63")
        local_bit_index = {int(bit): local for local, bit in enumerate(window_bits)}
        candidate_faults: set[int] = set()
        for bit in window_bits:
            if int(bit) < 0 or int(bit) >= self.num_observation_bits:
                raise ValueError("window bit index out of range")
            candidate_faults.update(self.faults_by_observation_bit[int(bit)])

        fault_ids: list[int] = []
        mask_states: list[int] = []
        for fault in sorted(candidate_faults):
            state = 0
            for bit in self.supports_by_fault[fault]:
                local = local_bit_index.get(bit)
                if local is not None:
                    state |= 1 << local
            if state:
                fault_ids.append(fault)
                mask_states.append(state)
        return torch.tensor(fault_ids, dtype=torch.long), torch.tensor(mask_states, dtype=torch.long)

    def audit_dict(self) -> dict[str, object]:
        return {
            "parity_storage": "sparse_supports_with_dense_A_compat" if self.dense_A is not None else "sparse_supports",
            "dense_A_compat": self.dense_A is not None,
            "num_sparse_support_entries": self.num_sparse_support_entries,
            "max_fault_support_size": max((len(support) for support in self.supports_by_fault), default=0),
            "max_observation_fault_degree": max(
                (len(faults) for faults in self.faults_by_observation_bit),
                default=0,
            ),
            "packed_mask64_chunks": len(self.packed_masks64[0])
            if self.packed_masks64
            else max(1, (self.num_observation_bits + 63) // 64),
        }
