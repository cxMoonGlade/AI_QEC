from __future__ import annotations

"""Compiled operation stream for dense qutrit MCWF workloads.

This module is the simulator-side program IR for trajectory workloads. It does
not own physics mechanisms; it only records the order in which a backend should
apply qutrit-lifted gates and finite-Kraus channels.
"""

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np
import torch

from .mcwf_backend import DenseQutritMcwfBackend


@dataclass(frozen=True)
class McwfQubitGateOp:
    """Apply a 1/2/3-qubit unitary on the qutrit computational subspace."""

    sites: tuple[int, ...]
    unitary: tuple[tuple[complex, ...], ...]
    label: str = "qubit_gate"


@dataclass(frozen=True)
class McwfCachedQubitGateOp:
    """Apply a backend-cached common one-qubit gate such as H or X."""

    name: str
    site: int


@dataclass(frozen=True)
class McwfAllOnesPhaseOp:
    """Apply a qutrit-lifted multi-controlled phase firing only on level |1>."""

    sites: tuple[int, ...]
    phase: complex = -1.0


@dataclass(frozen=True)
class McwfKrausAllSitesOp:
    """Apply the same one-site Kraus family to selected qutrit sites."""

    kraus_key: str
    sites: tuple[int, ...]


McwfOp = McwfQubitGateOp | McwfCachedQubitGateOp | McwfAllOnesPhaseOp | McwfKrausAllSitesOp


@dataclass(frozen=True)
class CompiledMcwfProgram:
    """Algorithm-neutral MCWF operation stream.

    The program is deliberately small and typed. Workload adapters compile to it;
    backends execute it. Future native CUDA trajectory kernels should consume this
    schema instead of parsing Grover-specific Python loops.
    """

    num_qutrits: int
    operations: tuple[McwfOp, ...]
    initial_levels: tuple[int, ...] | None = None
    schema: str = "qec_twin.simulator.CompiledMcwfProgram.v1"
    description: str = ""

    def __post_init__(self) -> None:
        n = int(self.num_qutrits)
        if n <= 0:
            raise ValueError("num_qutrits must be positive")
        if self.initial_levels is not None:
            levels = tuple(int(x) for x in self.initial_levels)
            if len(levels) != n or any(x not in (0, 1, 2) for x in levels):
                raise ValueError("initial_levels must be length num_qutrits with entries in {0,1,2}")
            object.__setattr__(self, "initial_levels", levels)
        for op in self.operations:
            self._validate_op(op)

    def run(
        self,
        backend: DenseQutritMcwfBackend,
        *,
        batch_size: int,
        kraus_families: Mapping[str, torch.Tensor],
    ) -> torch.Tensor:
        """Execute this program on ``backend`` and return the final batched state."""

        if int(backend.num_qutrits) != int(self.num_qutrits):
            raise ValueError(
                f"program num_qutrits={self.num_qutrits} does not match backend {backend.num_qutrits}"
            )
        psi = backend.basis_state(int(batch_size), self.initial_levels)
        return self.apply(backend, psi, kraus_families=kraus_families)

    def apply(
        self,
        backend: DenseQutritMcwfBackend,
        psi: torch.Tensor,
        *,
        kraus_families: Mapping[str, torch.Tensor],
    ) -> torch.Tensor:
        """Apply this program to an existing batched state."""

        out = psi
        for op in self.operations:
            if isinstance(op, McwfCachedQubitGateOp):
                out = _apply_cached_gate(backend, out, op)
            elif isinstance(op, McwfQubitGateOp):
                unitary = torch.as_tensor(np.asarray(op.unitary, dtype=np.complex128), dtype=backend.dtype, device=backend.device)
                out = backend.apply_qubit_gate(out, unitary, op.sites)
            elif isinstance(op, McwfAllOnesPhaseOp):
                out = backend.apply_computational_all_ones_phase(out, phase=op.phase, sites=op.sites)
            elif isinstance(op, McwfKrausAllSitesOp):
                try:
                    kraus = kraus_families[op.kraus_key]
                except KeyError as exc:
                    raise KeyError(f"missing Kraus family {op.kraus_key!r}") from exc
                out = backend.apply_kraus_all_sites(out, kraus, op.sites)
            else:  # pragma: no cover - exhaustive guard for future op additions.
                raise TypeError(f"unknown MCWF op {op!r}")
        return out

    def summary(self) -> dict[str, object]:
        """Return manifest-safe program metadata."""

        counts: dict[str, int] = {}
        for op in self.operations:
            key = op.__class__.__name__
            counts[key] = counts.get(key, 0) + 1
        return {
            "schema": self.schema,
            "description": self.description,
            "num_qutrits": int(self.num_qutrits),
            "initial_levels": None if self.initial_levels is None else list(self.initial_levels),
            "num_operations": len(self.operations),
            "operation_counts": counts,
        }

    def _validate_op(self, op: McwfOp) -> None:
        if isinstance(op, McwfCachedQubitGateOp):
            if op.name not in {"h", "x"}:
                raise ValueError(f"unsupported cached gate {op.name!r}")
            _validate_sites((op.site,), self.num_qutrits)
        elif isinstance(op, McwfQubitGateOp):
            _validate_sites(op.sites, self.num_qutrits)
            m = len(op.sites)
            if not 1 <= m <= 3:
                raise ValueError("qubit gate arity must be 1, 2, or 3")
            mat = np.asarray(op.unitary, dtype=np.complex128)
            dim = 1 << m
            if mat.shape != (dim, dim):
                raise ValueError(f"unitary for {op.label!r} must have shape {(dim, dim)}")
        elif isinstance(op, McwfAllOnesPhaseOp):
            _validate_sites(op.sites, self.num_qutrits)
        elif isinstance(op, McwfKrausAllSitesOp):
            if not op.kraus_key:
                raise ValueError("kraus_key must be non-empty")
            _validate_sites(op.sites, self.num_qutrits)
        else:
            raise TypeError(f"unknown MCWF op {op!r}")


def h(site: int) -> McwfCachedQubitGateOp:
    return McwfCachedQubitGateOp(name="h", site=int(site))


def x(site: int) -> McwfCachedQubitGateOp:
    return McwfCachedQubitGateOp(name="x", site=int(site))


def all_ones_phase(sites: Sequence[int], phase: complex = -1.0) -> McwfAllOnesPhaseOp:
    return McwfAllOnesPhaseOp(sites=tuple(int(s) for s in sites), phase=complex(phase))


def kraus_all_sites(kraus_key: str, sites: Sequence[int]) -> McwfKrausAllSitesOp:
    return McwfKrausAllSitesOp(kraus_key=str(kraus_key), sites=tuple(int(s) for s in sites))


def qubit_gate(
    sites: Sequence[int],
    unitary: Sequence[Sequence[complex]],
    *,
    label: str = "qubit_gate",
) -> McwfQubitGateOp:
    rows = tuple(tuple(complex(x) for x in row) for row in unitary)
    return McwfQubitGateOp(sites=tuple(int(s) for s in sites), unitary=rows, label=str(label))


def _apply_cached_gate(
    backend: DenseQutritMcwfBackend,
    psi: torch.Tensor,
    op: McwfCachedQubitGateOp,
) -> torch.Tensor:
    if op.name == "h":
        return backend.apply_h(psi, op.site)
    if op.name == "x":
        return backend.apply_x(psi, op.site)
    raise ValueError(f"unsupported cached gate {op.name!r}")


def _validate_sites(sites: Sequence[int], n: int) -> tuple[int, ...]:
    out = tuple(int(s) for s in sites)
    if not out:
        raise ValueError("sites must be non-empty")
    if len(set(out)) != len(out):
        raise ValueError(f"sites must be unique, got {out!r}")
    for site in out:
        if site < 0 or site >= int(n):
            raise ValueError(f"site {site} outside [0, {int(n)})")
    return out
