from __future__ import annotations

"""qutip-cuquantum adapter probes for multi-level simulator backends.

This module is intentionally not the production 12-qutrit Grover carrier.
qutip-cuquantum's `mcsolve` path is a continuous-time H/c_ops solver; the
gate-level Grover workload is carried by `DenseQutritMcwfBackend`.
"""

from dataclasses import dataclass
from typing import Any

import numpy as np

MAX_QUTIP_CUQUANTUM_MCSOLVE_PROBE_QUTRITS = 4


@dataclass(frozen=True)
class QutipCuQuantumSymbolicCollapseSummary:
    num_qutrits: int
    site: int
    collapse_shape: tuple[int, int]
    collapse_data_type: str
    collapse_terms: int
    collapse_hilbert_dims: tuple[int, ...]
    cdc_shape: tuple[int, int]
    cdc_data_type: str
    cdc_terms: int
    cdc_hilbert_dims: tuple[int, ...]


@dataclass(frozen=True)
class QutipCuQuantumLocalMcwfProbeResult:
    num_qutrits: int
    ntraj: int
    method: str
    end_condition: str
    final_state_data_type: str | None
    final_state_shape: tuple[int, int] | None


def local_qutrit_operator_qobj(local_matrix: Any, *, site: int, num_qutrits: int):
    """Return a qutip Qobj backed by a local symbolic qutip-cuquantum CuOperator.

    Do not use ``qutip.tensor([...])`` for local qutrit collapse operators at
    12-qutrit scale: that expands to a full ``3**n x 3**n`` operator. This
    factory keeps the local 3x3 operator as a product term with an explicit
    ``mode`` and full ``hilbert_dims`` declaration.
    """

    qt, CuOperator = _qutip_cuquantum_operator_imports()
    n = _validate_num_qutrits(num_qutrits)
    s = _validate_site(site, n)
    arr = np.asarray(local_matrix, dtype=np.complex128)
    if arr.shape != (3, 3):
        raise ValueError(f"local_matrix must have shape (3, 3), got {arr.shape!r}")
    dims = [3] * n
    local = qt.Qobj(arr, dims=[[3], [3]])
    data = CuOperator(local.data, mode=s, hilbert_dims=tuple(dims))
    return qt.Qobj(data, dims=[dims, dims])


def zero_hamiltonian_qobj(*, num_qutrits: int):
    """Return a symbolic zero Hamiltonian on ``num_qutrits`` qutrits."""

    qt, CuOperator = _qutip_cuquantum_operator_imports()
    n = _validate_num_qutrits(num_qutrits)
    dims = [3] * n
    return qt.Qobj(CuOperator(hilbert_dims=tuple(dims)), dims=[dims, dims])


def seepage_collapse_matrix() -> np.ndarray:
    """Return the local seep collapse ``|1><2|`` for qutrit leakage probes."""

    out = np.zeros((3, 3), dtype=np.complex128)
    out[1, 2] = 1.0
    return out


def qutip_cuquantum_symbolic_collapse_summary(
    *,
    num_qutrits: int = 12,
    site: int = 0,
    rate: float = 1.0,
) -> QutipCuQuantumSymbolicCollapseSummary:
    """Summarize the symbolic local-collapse representation without solving.

    This is the scale-safety guard: for ``num_qutrits=12`` both ``c`` and
    ``c.dag() * c`` must remain qutip-cuquantum ``CuOperator`` objects. If this
    function ever returns dense data, the backend is unsafe for 12-qutrit use.
    """

    gamma = float(rate)
    if gamma < 0.0 or not np.isfinite(gamma):
        raise ValueError("rate must be finite and non-negative")
    c_op = local_qutrit_operator_qobj(
        np.sqrt(gamma) * seepage_collapse_matrix(),
        site=site,
        num_qutrits=num_qutrits,
    )
    cdc = c_op.dag() * c_op
    c_data = c_op.data
    cdc_data = cdc.data
    return QutipCuQuantumSymbolicCollapseSummary(
        num_qutrits=int(num_qutrits),
        site=int(site),
        collapse_shape=tuple(int(x) for x in c_op.shape),
        collapse_data_type=type(c_data).__name__,
        collapse_terms=int(len(getattr(c_data, "terms", ()))),
        collapse_hilbert_dims=tuple(int(x) for x in getattr(c_data, "hilbert_dims", ())),
        cdc_shape=tuple(int(x) for x in cdc.shape),
        cdc_data_type=type(cdc_data).__name__,
        cdc_terms=int(len(getattr(cdc_data, "terms", ()))),
        cdc_hilbert_dims=tuple(int(x) for x in getattr(cdc_data, "hilbert_dims", ())),
    )


def probe_qutip_cuquantum_local_mcwf(
    *,
    num_qutrits: int = 2,
    ntraj: int = 1,
    rate: float = 0.01,
    t_final: float = 1e-4,
) -> QutipCuQuantumLocalMcwfProbeResult:
    """Run a deliberately small qutip-cuquantum local-collapse MCWF smoke.

    The cap is intentional. qutip-cuquantum `mcsolve` is a continuous ODE
    backend and is not yet the production 12-qutrit gate-level Grover carrier.
    Use `DenseQutritMcwfBackend` for that workload.
    """

    n = _validate_num_qutrits(num_qutrits)
    if n > MAX_QUTIP_CUQUANTUM_MCSOLVE_PROBE_QUTRITS:
        raise ValueError(
            "qutip-cuquantum mcsolve probe is capped at "
            f"{MAX_QUTIP_CUQUANTUM_MCSOLVE_PROBE_QUTRITS} qutrits; "
            "production 12-qutrit Grover uses DenseQutritMcwfBackend"
        )
    gamma = float(rate)
    if gamma < 0.0 or not np.isfinite(gamma):
        raise ValueError("rate must be finite and non-negative")
    tf = float(t_final)
    if tf <= 0.0 or not np.isfinite(tf):
        raise ValueError("t_final must be finite and positive")
    k = int(ntraj)
    if k <= 0:
        raise ValueError("ntraj must be positive")

    qt, qutip_cuquantum, cudm = _qutip_cuquantum_solver_imports()
    dims = [3] * n
    with qutip_cuquantum.CuQuantumBackend(cudm.WorkStream()):
        H = zero_hamiltonian_qobj(num_qutrits=n)
        c0 = local_qutrit_operator_qobj(
            np.sqrt(gamma) * seepage_collapse_matrix(),
            site=0,
            num_qutrits=n,
        )
        psi0 = qt.tensor([qt.basis(3, 2)] + [qt.basis(3, 0) for _ in range(n - 1)])
        res = qt.mcsolve(
            H,
            psi0,
            [0.0, tf],
            c_ops=[c0],
            ntraj=k,
            e_ops=[],
            options={
                "progress_bar": False,
                "keep_runs_results": True,
                "store_states": False,
                "store_final_state": True,
            },
        )
    final_state = getattr(res, "final_state", None)
    if isinstance(final_state, list):
        final_state = final_state[0] if final_state else None
    if final_state is None:
        final_data_type = None
        final_shape = None
    else:
        final_data_type = type(final_state.data).__name__
        final_shape = tuple(int(x) for x in final_state.shape)
    return QutipCuQuantumLocalMcwfProbeResult(
        num_qutrits=n,
        ntraj=k,
        method=str(res.stats.get("method")),
        end_condition=str(res.stats.get("end_condition")),
        final_state_data_type=final_data_type,
        final_state_shape=final_shape,
    )


def _qutip_cuquantum_operator_imports():
    try:
        import qutip as qt
        from qutip_cuquantum import CuOperator
    except ImportError as exc:  # pragma: no cover - environment dependent.
        raise RuntimeError("qutip-cuquantum adapter requires qutip and qutip_cuquantum") from exc
    return qt, CuOperator


def _qutip_cuquantum_solver_imports():
    try:
        import qutip as qt
        import qutip_cuquantum
        import cuquantum.densitymat as cudm
    except ImportError as exc:  # pragma: no cover - environment dependent.
        raise RuntimeError("qutip-cuquantum mcsolve probe requires qutip_cuquantum and cuquantum.densitymat") from exc
    return qt, qutip_cuquantum, cudm


def _validate_num_qutrits(num_qutrits: int) -> int:
    n = int(num_qutrits)
    if n <= 0:
        raise ValueError("num_qutrits must be positive")
    return n


def _validate_site(site: int, num_qutrits: int) -> int:
    s = int(site)
    if s < 0 or s >= int(num_qutrits):
        raise ValueError(f"site must lie in [0, {num_qutrits}), got {site!r}")
    return s
