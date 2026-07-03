from __future__ import annotations

"""Generic dense qutrit MCWF trajectory backend.

This module owns the reusable trajectory carrier. Algorithm adapters such as
Grover should describe workloads in terms of backend operations instead of
embedding MCWF sampling logic directly.
"""

from dataclasses import dataclass
import math
from typing import Sequence

import numpy as np
import torch

CDTYPE = torch.complex128
RDTYPE = torch.float64
MAX_DENSE_MCWF_QUTRITS = 12
MAX_DENSE_QUDIT_MCWF_DIM = 3**12
QUTRIT_MCWF_CONVENTION = "base3_most_significant_q0_left_to_right"
QUDIT_MCWF_CONVENTION = "mixed_radix_most_significant_site0_left_to_right"


@dataclass(frozen=True)
class QutritMcwfMeasurementBatch:
    bit_counts: dict[str, int]
    qutrit_counts: dict[str, int]
    leaked_by_site_counts: np.ndarray
    final_leaked_counts: np.ndarray

    @property
    def shots(self) -> int:
        return int(sum(self.qutrit_counts.values()))


class DenseQuditMcwfBackend:
    """Batched dense-state MCWF carrier for arbitrary local Hilbert dimensions.

    This is the dimension-polymorphic correctness core. It supports qubit,
    qutrit, ququart, and mixed-dimension local Hilbert spaces through
    ``local_dims``. It deliberately does not know about Stim, DEM, leakage labels,
    or a decoder; physics adapters provide local operators and Kraus families.
    """

    convention: str = QUDIT_MCWF_CONVENTION

    def __init__(
        self,
        local_dims: Sequence[int],
        *,
        seed: int = 0,
        device: str | torch.device = "cuda",
        dtype: torch.dtype = CDTYPE,
    ) -> None:
        dims = tuple(int(dim) for dim in local_dims)
        if not dims:
            raise ValueError("local_dims must be non-empty")
        if any(dim < 2 for dim in dims):
            raise ValueError(f"local_dims entries must be >= 2, got {dims!r}")
        dim = math.prod(dims)
        if dim > MAX_DENSE_QUDIT_MCWF_DIM:
            raise ValueError(
                "dense qudit MCWF backend dimension cap exceeded: "
                f"dim={dim} cap={MAX_DENSE_QUDIT_MCWF_DIM}"
            )
        self.local_dims = dims
        self.num_sites = len(dims)
        self.dim = int(dim)
        self.device = torch.device(device)
        if self.device.type != "cuda":
            raise ValueError("DenseQuditMcwfBackend is GPU-only; CPU execution is intentionally unsupported")
        if not torch.cuda.is_available():
            raise RuntimeError(
                "DenseQuditMcwfBackend requested CUDA but torch.cuda.is_available() is false; "
                "fix CUDA visibility before running MCWF trajectories"
            )
        self.dtype = dtype
        self.generator = torch.Generator(device=self.device)
        self.generator.manual_seed(int(seed))

    def basis_state(
        self,
        batch_size: int,
        levels: str | Sequence[int] | None = None,
    ) -> torch.Tensor:
        """Return a batched computational-basis state for ``local_dims``."""

        b = int(batch_size)
        if b <= 0:
            raise ValueError("batch_size must be positive")
        digits = self.normalize_levels(levels)
        index = self.index_from_digits(digits)
        psi = torch.zeros((b, self.dim), dtype=self.dtype, device=self.device)
        psi[:, index] = 1.0
        return psi

    def apply_operator(
        self,
        psi: torch.Tensor,
        operator: torch.Tensor,
        sites: Sequence[int],
    ) -> torch.Tensor:
        """Apply an arbitrary local operator on the ordered ``sites`` subsystem."""

        self._validate_state(psi)
        target_sites = self._validate_sites(sites)
        target_dim = math.prod(self.local_dims[site] for site in target_sites)
        op = torch.as_tensor(operator, dtype=self.dtype, device=self.device)
        if op.shape != (target_dim, target_dim):
            raise ValueError(
                f"operator for sites {target_sites!r} must have shape "
                f"{(target_dim, target_dim)}, got {tuple(op.shape)}"
            )
        permuted, order = self._target_rest_view(psi, target_sites)
        out = torch.einsum("ab,Bbr->Bar", op, permuted)
        return self._restore_target_rest_view(out, order, psi.shape[0])

    def apply_kraus(
        self,
        psi: torch.Tensor,
        kraus: torch.Tensor,
        sites: Sequence[int],
    ) -> torch.Tensor:
        """Sample and apply one Kraus branch by the Born rule for each trajectory."""

        self._validate_state(psi)
        target_sites = self._validate_sites(sites)
        target_dim = math.prod(self.local_dims[site] for site in target_sites)
        k_ops = torch.as_tensor(kraus, dtype=self.dtype, device=self.device)
        if k_ops.ndim != 3 or k_ops.shape[1:] != (target_dim, target_dim):
            raise ValueError(
                f"kraus for sites {target_sites!r} must have shape "
                f"(rank, {target_dim}, {target_dim}), got {tuple(k_ops.shape)}"
            )
        phis = torch.stack(
            [self.apply_operator(psi, k_ops[k], target_sites) for k in range(k_ops.shape[0])],
            dim=0,
        )
        norms2 = (phis.conj() * phis).real.sum(dim=2).transpose(0, 1)
        totals = norms2.sum(dim=1, keepdim=True)
        if bool((totals <= 0.0).any().detach().cpu().item()):
            raise ValueError("cannot sample a Kraus family with zero total Born weight")
        probs = norms2 / totals
        rand = torch.rand((psi.shape[0], 1), dtype=RDTYPE, device=self.device, generator=self.generator)
        cdf = torch.cumsum(probs, dim=1)
        sel = (rand > cdf).sum(dim=1).clamp_max(k_ops.shape[0] - 1)
        chosen = phis[sel, torch.arange(psi.shape[0], device=self.device), :]
        norm = torch.linalg.vector_norm(chosen, dim=1, keepdim=True).clamp_min(1e-300).to(self.dtype)
        return chosen / norm

    def measure_sites(
        self,
        psi: torch.Tensor,
        sites: Sequence[int],
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Sample computational-basis outcomes and return ``(outcomes, collapsed)``."""

        self._validate_state(psi)
        target_sites = self._validate_sites(sites)
        target_dims = tuple(self.local_dims[site] for site in target_sites)
        permuted, order = self._target_rest_view(psi, target_sites)
        probs = (permuted.conj() * permuted).real.sum(dim=2)
        probs = probs / probs.sum(dim=1, keepdim=True).clamp_min(1e-300)
        sel = torch.multinomial(probs, num_samples=1, replacement=True, generator=self.generator).squeeze(1)
        rows = torch.arange(psi.shape[0], device=self.device)
        selected = permuted[rows, sel, :]
        norm = torch.linalg.vector_norm(selected, dim=1, keepdim=True).clamp_min(1e-300).to(self.dtype)
        collapsed = torch.zeros_like(permuted)
        collapsed[rows, sel, :] = selected / norm
        return (
            mixed_radix_digits_from_indices_t(sel, dims=target_dims),
            self._restore_target_rest_view(collapsed, order, psi.shape[0]),
        )

    def probabilities(self, psi: torch.Tensor) -> torch.Tensor:
        self._validate_state(psi)
        probs = (psi.conj() * psi).real
        return probs / probs.sum(dim=1, keepdim=True).clamp_min(1e-300)

    def normalize_levels(self, levels: str | Sequence[int] | None) -> tuple[int, ...]:
        if levels is None:
            return tuple(0 for _ in self.local_dims)
        if isinstance(levels, str):
            raw = tuple(int(ch) for ch in levels.strip())
        else:
            raw = tuple(int(x) for x in levels)
        if len(raw) != self.num_sites:
            raise ValueError(f"levels must have length {self.num_sites}")
        for value, dim in zip(raw, self.local_dims, strict=True):
            if value < 0 or value >= dim:
                raise ValueError(f"level {value} outside local dimension {dim}")
        return raw

    def index_from_digits(self, digits: Sequence[int]) -> int:
        levels = tuple(int(x) for x in digits)
        if len(levels) != self.num_sites:
            raise ValueError(f"digits must have length {self.num_sites}")
        out = 0
        for site, value in enumerate(levels):
            dim = self.local_dims[site]
            if value < 0 or value >= dim:
                raise ValueError(f"digit {value} outside local dimension {dim}")
            place = math.prod(self.local_dims[site + 1 :])
            out += int(value) * int(place)
        return int(out)

    def digits_from_indices(self, indices: torch.Tensor) -> torch.Tensor:
        return mixed_radix_digits_from_indices_t(indices, dims=self.local_dims)

    def _validate_sites(self, sites: Sequence[int]) -> tuple[int, ...]:
        out = tuple(int(site) for site in sites)
        if not out:
            raise ValueError("sites must be non-empty")
        if len(set(out)) != len(out):
            raise ValueError(f"sites must be unique, got {out!r}")
        for site in out:
            if site < 0 or site >= self.num_sites:
                raise ValueError(f"site {site} outside [0, {self.num_sites})")
        return out

    def _validate_state(self, psi: torch.Tensor) -> None:
        if psi.ndim != 2 or psi.shape[1] != self.dim:
            raise ValueError(f"state must have shape (batch, {self.dim}), got {tuple(psi.shape)}")
        if psi.device.type != self.device.type or (
            self.device.index is not None and psi.device.index != self.device.index
        ):
            raise ValueError(f"state device {psi.device} does not match backend device {self.device}")

    def _target_rest_view(
        self,
        psi: torch.Tensor,
        sites: tuple[int, ...],
    ) -> tuple[torch.Tensor, list[int]]:
        rest = [site for site in range(self.num_sites) if site not in sites]
        order = list(sites) + rest
        view = psi.reshape(psi.shape[0], *self.local_dims)
        permuted = view.permute(0, *[1 + site for site in order])
        target_dim = math.prod(self.local_dims[site] for site in sites)
        return permuted.reshape(psi.shape[0], int(target_dim), -1), order

    def _restore_target_rest_view(
        self,
        permuted: torch.Tensor,
        order: list[int],
        batch_size: int,
    ) -> torch.Tensor:
        ordered_dims = [self.local_dims[site] for site in order]
        restored = permuted.reshape(int(batch_size), *ordered_dims)
        inv_perm = [0] + [1 + order.index(site) for site in range(self.num_sites)]
        return restored.permute(*inv_perm).reshape(int(batch_size), self.dim)


class DenseQutritMcwfBackend:
    """Batched dense-state qutrit MCWF carrier.

    The backend is algorithm-neutral: it can initialize basis states, apply
    single-site qutrit matrices, sample Kraus branches on a site, and perform
    final qutrit/Born measurement with a declared leaked-readout map. It does not
    know about Grover, XZZX, Stim, DEM, or a decoder.
    """

    qutrit_dim: int = 3

    def __init__(
        self,
        num_qutrits: int,
        *,
        seed: int = 0,
        device: str | torch.device = "cuda",
        dtype: torch.dtype = CDTYPE,
        use_fused_kernels: bool = True,
    ) -> None:
        n = int(num_qutrits)
        if not 1 <= n <= MAX_DENSE_MCWF_QUTRITS:
            raise ValueError(f"dense qutrit MCWF backend supports 1 <= num_qutrits <= {MAX_DENSE_MCWF_QUTRITS}")
        self.num_qutrits = n
        self.dim = 3**n
        self.device = torch.device(device)
        if self.device.type != "cuda":
            raise ValueError("DenseQutritMcwfBackend is GPU-only; CPU execution is intentionally unsupported")
        if not torch.cuda.is_available():
            raise RuntimeError(
                "DenseQutritMcwfBackend requested CUDA but torch.cuda.is_available() is false; "
                "fix CUDA visibility before running MCWF trajectories"
            )
        self.dtype = dtype
        self.generator = torch.Generator(device=self.device)
        self.generator.manual_seed(int(seed))
        self.use_fused_kernels = bool(use_fused_kernels)
        self._fused_ops = None
        self._fused_ops_checked = False
        self._ones_phase_masks: dict[tuple[int, ...], torch.Tensor] = {}
        self._qubit_gate_cache: dict[str, torch.Tensor] = {}

    def basis_state(
        self,
        batch_size: int,
        initial_levels: str | Sequence[int] | None = None,
    ) -> torch.Tensor:
        """Return a batched qutrit basis state, defaulting to ``|00...0>``."""

        b = int(batch_size)
        if b <= 0:
            raise ValueError("batch_size must be positive")
        levels = _normalize_qutrit_levels(initial_levels, self.num_qutrits)
        idx = qutrit_index_from_digits(levels)
        psi = torch.zeros((b, self.dim), dtype=self.dtype, device=self.device)
        psi[:, idx] = 1.0
        return psi

    def apply_h(self, psi: torch.Tensor, site: int) -> torch.Tensor:
        """Apply a qubit Hadamard on the ``|0>,|1>`` subspace; leave ``|2>`` inert."""

        return self.apply_qubit_gate(psi, self._cached_qubit_gate("h"), [site])

    def apply_x(self, psi: torch.Tensor, site: int) -> torch.Tensor:
        """Apply a qubit X on the ``|0>,|1>`` subspace; leave ``|2>`` inert."""

        return self.apply_qubit_gate(psi, self._cached_qubit_gate("x"), [site])

    def apply_qubit_gate(
        self,
        psi: torch.Tensor,
        unitary: torch.Tensor,
        sites: Sequence[int],
    ) -> torch.Tensor:
        """Apply a 1/2/3-qubit gate on the qutrit computational subspace.

        Any target qutrit in ``|2>`` leaves that amplitude unchanged. This is the
        project-native qutrit lift used by the MCWF carrier; it supports common
        one-, two-, and three-qubit gates without turning leakage into qubit
        population.
        """

        self._validate_state(psi)
        target_sites = tuple(self._validate_site(s) for s in sites)
        if not 1 <= len(target_sites) <= 3:
            raise ValueError("qubit gate arity must be 1, 2, or 3")
        if len(set(target_sites)) != len(target_sites):
            raise ValueError(f"gate sites must be unique, got {target_sites!r}")
        U = torch.as_tensor(unitary, dtype=self.dtype, device=self.device)
        dim = 1 << len(target_sites)
        if U.shape != (dim, dim):
            raise ValueError(f"unitary must have shape {(dim, dim)}, got {tuple(U.shape)}")
        fused = self._get_fused_ops()
        if fused is not None:
            return fused.apply_qubit_gate(psi, U, target_sites, self.num_qutrits)
        return self._apply_qubit_gate_torch(psi, U, target_sites)

    def apply_site_matrix(self, psi: torch.Tensor, matrix: torch.Tensor, site: int) -> torch.Tensor:
        """Apply a dense 3x3 matrix to one qutrit site."""

        self._validate_state(psi)
        s = self._validate_site(site)
        mat = torch.as_tensor(matrix, dtype=self.dtype, device=self.device)
        if mat.shape != (3, 3):
            raise ValueError(f"site matrix must have shape (3, 3), got {tuple(mat.shape)}")
        left, right = 3**s, 3 ** (self.num_qutrits - 1 - s)
        t = torch.einsum("ab,Blbr->Blar", mat, psi.reshape(psi.shape[0], left, 3, right))
        return t.reshape_as(psi)

    def apply_basis_phase(self, psi: torch.Tensor, basis_index: int, phase: complex | float) -> torch.Tensor:
        """Multiply one basis-state amplitude by a phase."""

        self._validate_state(psi)
        idx = int(basis_index)
        if idx < 0 or idx >= self.dim:
            raise ValueError(f"basis_index outside [0, {self.dim})")
        out = psi.clone()
        out[:, idx] *= complex(phase)
        return out

    def apply_computational_all_ones_phase(
        self,
        psi: torch.Tensor,
        *,
        phase: complex | float = -1.0,
        sites: Sequence[int] | None = None,
    ) -> torch.Tensor:
        """Apply a multi-controlled phase on qutrit controls in level ``|1>``.

        This is the qutrit-lifted gate primitive used by standard Grover
        oracles/diffusers. Controls only fire on computational level ``|1>``;
        leaked ``|2>`` controls do not satisfy the gate condition.
        """

        self._validate_state(psi)
        controls = tuple(range(self.num_qutrits)) if sites is None else tuple(self._validate_site(s) for s in sites)
        if not controls:
            raise ValueError("at least one control site is required")
        if len(set(controls)) != len(controls):
            raise ValueError(f"control sites must be unique, got {controls!r}")
        fused = self._get_fused_ops()
        if fused is not None:
            return fused.multi_controlled_phase(psi, controls, phase, self.num_qutrits)
        mask = self._ones_control_mask(controls)
        out = psi.clone()
        out[:, mask] *= complex(phase)
        return out

    def apply_kraus_site(self, psi: torch.Tensor, kraus: torch.Tensor, site: int) -> torch.Tensor:
        """Sample and apply one Kraus branch on one qutrit site by the Born rule."""

        self._validate_state(psi)
        s = self._validate_site(site)
        k_ops = torch.as_tensor(kraus, dtype=self.dtype, device=self.device)
        if k_ops.ndim != 3 or k_ops.shape[1:] != (3, 3):
            raise ValueError(f"kraus must have shape (rank, 3, 3), got {tuple(k_ops.shape)}")
        fused = self._get_fused_ops()
        if fused is not None:
            rand = torch.rand((psi.shape[0],), dtype=RDTYPE, device=self.device, generator=self.generator)
            return fused.apply_kraus_site(psi, k_ops, rand, s, self.num_qutrits)
        phis = torch.stack([self.apply_site_matrix(psi, k_ops[k], s) for k in range(k_ops.shape[0])], dim=0)
        norms2 = (phis.conj() * phis).real.sum(dim=2).transpose(0, 1)
        probs = norms2 / norms2.sum(dim=1, keepdim=True).clamp_min(1e-300)
        rand = torch.rand((psi.shape[0], 1), dtype=RDTYPE, device=self.device, generator=self.generator)
        cdf = torch.cumsum(probs, dim=1)
        sel = (rand > cdf).sum(dim=1).clamp_max(k_ops.shape[0] - 1)
        chosen = phis[sel, torch.arange(psi.shape[0], device=self.device), :]
        norm = torch.linalg.vector_norm(chosen, dim=1, keepdim=True).clamp_min(1e-300).to(self.dtype)
        return chosen / norm

    def apply_kraus_all_sites(self, psi: torch.Tensor, kraus: torch.Tensor, sites: Sequence[int] | None = None) -> torch.Tensor:
        """Sample and apply the same one-site Kraus family on each selected site."""

        self._validate_state(psi)
        k_ops = torch.as_tensor(kraus, dtype=self.dtype, device=self.device)
        if k_ops.ndim != 3 or k_ops.shape[1:] != (3, 3):
            raise ValueError(f"kraus must have shape (rank, 3, 3), got {tuple(k_ops.shape)}")
        active_sites = tuple(range(self.num_qutrits)) if sites is None else tuple(self._validate_site(int(s)) for s in sites)
        if not active_sites:
            return psi
        if len(set(active_sites)) != len(active_sites):
            raise ValueError(f"sites must be unique, got {active_sites!r}")
        fused = self._get_fused_ops()
        if fused is not None:
            # Match the reference draw order exactly: one length-B uniform vector
            # per site, in site order. A single rand((S, B)) call does not produce
            # the same CUDA generator sequence as S separate rand((B,)) calls.
            rand = torch.stack(
                [
                    torch.rand((psi.shape[0],), dtype=RDTYPE, device=self.device, generator=self.generator)
                    for _ in active_sites
                ],
                dim=0,
            )
            return fused.apply_kraus_all_sites(psi, k_ops, rand, active_sites, self.num_qutrits)
        out = psi
        for site in active_sites:
            out = self.apply_kraus_site(out, k_ops, site)
        return out

    def probabilities(self, psi: torch.Tensor) -> torch.Tensor:
        """Return normalized Born probabilities for a batched state."""

        self._validate_state(psi)
        probs = (psi.conj() * psi).real
        return probs / probs.sum(dim=1, keepdim=True).clamp_min(1e-300)

    def sample_measurements(
        self,
        psi: torch.Tensor | None = None,
        *,
        probabilities: torch.Tensor | None = None,
        leaked_readout_b: float = 1.0,
    ) -> QutritMcwfMeasurementBatch:
        """Sample final qutrit outcomes and binary readout counts.

        The raw qutrit counts preserve final ``|2>`` leakage. The binary counts
        map leaked qutrits to bit ``1`` with probability ``leaked_readout_b`` and
        to bit ``0`` otherwise.
        """

        b = float(leaked_readout_b)
        if not 0.0 <= b <= 1.0:
            raise ValueError("leaked_readout_b must lie in [0, 1]")
        if probabilities is None:
            if psi is None:
                raise ValueError("either psi or probabilities must be provided")
            probs = self.probabilities(psi)
        else:
            probs = torch.as_tensor(probabilities, dtype=RDTYPE, device=self.device)
            if probs.ndim != 2 or probs.shape[1] != self.dim:
                raise ValueError(f"probabilities must have shape (batch, {self.dim}), got {tuple(probs.shape)}")
            probs = probs / probs.sum(dim=1, keepdim=True).clamp_min(1e-300)

        sampled = torch.multinomial(probs, num_samples=1, replacement=True, generator=self.generator).squeeze(1)
        digits_t = self.digits_from_indices(sampled)
        leaked_mask = digits_t == 2
        readout_digits = digits_t.clone()
        if leaked_mask.any():
            leak_rand = torch.rand(readout_digits.shape, dtype=RDTYPE, device=self.device, generator=self.generator)
            readout_digits = torch.where(leaked_mask, (leak_rand < b).to(torch.long), readout_digits)

        qdigits_np = digits_t.detach().cpu().numpy().astype(np.int8)
        bits_np = readout_digits.detach().cpu().numpy().astype(np.int8)
        return QutritMcwfMeasurementBatch(
            bit_counts=_count_digit_rows(bits_np),
            qutrit_counts=_count_digit_rows(qdigits_np),
            leaked_by_site_counts=leaked_mask.to(RDTYPE).sum(dim=0).detach().cpu().numpy().astype(np.float64),
            final_leaked_counts=leaked_mask.sum(dim=1).detach().cpu().numpy().astype(np.int64),
        )

    def digits_from_indices(self, indices: torch.Tensor) -> torch.Tensor:
        return digits_from_indices_t(indices, n=self.num_qutrits, q=3)

    def _validate_site(self, site: int) -> int:
        s = int(site)
        if s < 0 or s >= self.num_qutrits:
            raise ValueError(f"site must lie in [0, {self.num_qutrits}), got {site!r}")
        return s

    def _validate_state(self, psi: torch.Tensor) -> None:
        if psi.ndim != 2 or psi.shape[1] != self.dim:
            raise ValueError(f"state must have shape (batch, {self.dim}), got {tuple(psi.shape)}")
        if psi.device.type != self.device.type or (
            self.device.index is not None and psi.device.index != self.device.index
        ):
            raise ValueError(f"state device {psi.device} does not match backend device {self.device}")

    def _ones_control_mask(self, controls: tuple[int, ...]) -> torch.Tensor:
        cached = self._ones_phase_masks.get(controls)
        if cached is not None:
            return cached
        indices = torch.arange(self.dim, device=self.device)
        mask = torch.ones((self.dim,), dtype=torch.bool, device=self.device)
        for site in controls:
            place = 3 ** (self.num_qutrits - 1 - int(site))
            mask &= ((indices // place) % 3) == 1
        self._ones_phase_masks[controls] = mask
        return mask

    def _get_fused_ops(self):
        if not self.use_fused_kernels:
            return None
        if self._fused_ops_checked:
            return self._fused_ops
        self._fused_ops_checked = True
        from ..carrier.kernels import qutrit_mcwf_ops_loader as _ops

        self._fused_ops = _ops if _ops.available() else None
        return self._fused_ops

    def _cached_qubit_gate(self, name: str) -> torch.Tensor:
        cached = self._qubit_gate_cache.get(name)
        if cached is not None:
            return cached
        if name == "h":
            inv = 1.0 / math.sqrt(2.0)
            value = torch.tensor([[inv, inv], [inv, -inv]], dtype=self.dtype, device=self.device)
        elif name == "x":
            value = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=self.dtype, device=self.device)
        else:
            raise ValueError(f"unknown cached gate {name!r}")
        self._qubit_gate_cache[name] = value
        return value

    def _apply_qubit_gate_torch(
        self,
        psi: torch.Tensor,
        unitary: torch.Tensor,
        sites: tuple[int, ...],
    ) -> torch.Tensor:
        m = len(sites)
        rest = [q for q in range(self.num_qutrits) if q not in sites]
        order = list(sites) + rest
        view = psi.reshape(psi.shape[0], *([3] * self.num_qutrits))
        permuted = view.permute(0, *[1 + q for q in order]).reshape(psi.shape[0], 3**m, -1)
        out = permuted.clone()
        nonleaked: list[tuple[int, int]] = []
        for qrow in range(3**m):
            digits = _digits_base(qrow, m, 3)
            if all(d in (0, 1) for d in digits):
                brow = 0
                for d in digits:
                    brow = (brow << 1) | int(d)
                nonleaked.append((qrow, brow))
        for qrow, brow in nonleaked:
            acc = torch.zeros_like(permuted[:, qrow, :])
            for qcol, bcol in nonleaked:
                acc = acc + unitary[brow, bcol] * permuted[:, qcol, :]
            out[:, qrow, :] = acc
        restored = out.reshape(psi.shape[0], *([3] * self.num_qutrits))
        inv_perm = [0] + [1 + order.index(q) for q in range(self.num_qutrits)]
        return restored.permute(*inv_perm).reshape_as(psi)


def qutrit_index_from_digits(digits: Sequence[int]) -> int:
    levels = tuple(int(x) for x in digits)
    out = 0
    for site, value in enumerate(levels):
        if value not in (0, 1, 2):
            raise ValueError("qutrit digits must be in {0, 1, 2}")
        out += value * (3 ** (len(levels) - 1 - site))
    return int(out)


def qutrit_string_from_index(index: int, n: int) -> str:
    idx = int(index)
    nn = int(n)
    if idx < 0 or idx >= 3**nn:
        raise ValueError(f"index outside [0, 3**{nn})")
    out = []
    for site in range(nn):
        place = 3 ** (nn - 1 - site)
        digit = idx // place
        out.append(str(int(digit)))
        idx %= place
    return "".join(out)


def digits_from_indices_t(indices: torch.Tensor, *, n: int, q: int) -> torch.Tensor:
    cols = []
    for site in range(int(n)):
        place = int(q) ** (int(n) - 1 - site)
        cols.append(((indices // place) % int(q)).to(torch.long))
    return torch.stack(cols, dim=1)


def mixed_radix_digits_from_indices_t(
    indices: torch.Tensor,
    *,
    dims: Sequence[int],
) -> torch.Tensor:
    local_dims = tuple(int(dim) for dim in dims)
    if not local_dims:
        raise ValueError("dims must be non-empty")
    if any(dim < 2 for dim in local_dims):
        raise ValueError(f"dims entries must be >= 2, got {local_dims!r}")
    cols = []
    for site, dim in enumerate(local_dims):
        place = math.prod(local_dims[site + 1 :])
        cols.append(((indices // int(place)) % int(dim)).to(torch.long))
    return torch.stack(cols, dim=1)


def _digits_base(index: int, width: int, base: int) -> tuple[int, ...]:
    idx = int(index)
    out = []
    for pos in range(int(width)):
        place = int(base) ** (int(width) - 1 - pos)
        out.append(idx // place)
        idx %= place
    return tuple(int(x) for x in out)


def _normalize_qutrit_levels(levels: str | Sequence[int] | None, n: int) -> tuple[int, ...]:
    if levels is None:
        return tuple(0 for _ in range(int(n)))
    if isinstance(levels, str):
        raw = tuple(int(ch) for ch in levels.strip())
    else:
        raw = tuple(int(x) for x in levels)
    if len(raw) != int(n) or any(x not in (0, 1, 2) for x in raw):
        raise ValueError(f"initial_levels must be a length-{int(n)} qutrit string/sequence")
    return raw


def _count_digit_rows(rows: np.ndarray) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = "".join(str(int(x)) for x in row)
        counts[key] = counts.get(key, 0) + 1
    return counts
