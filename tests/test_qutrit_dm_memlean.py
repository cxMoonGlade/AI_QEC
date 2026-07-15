"""Memory-bounded QutritDM apply-path falsifiers.

Every check uses a reference independent of the code under test:

* Chunked ``apply_channel`` matches both a per-Kraus ``apply_local_op_q`` sum and an
  unchunked transcription of the superoperator contraction for random CPTP channels,
  random mixed states, q in {3, 4}, and every site.
* ``hermitianize_inplace_blocked`` matches ``cptp_channel.hermitianize`` elementwise,
  including non-divisible block edges.
* ``_apply_op_vector`` matches the dense ``embed_operator_q @ psi`` reference.
* ``logical_distribution`` is checked on Z- and X-kind logical reads, including exact
  state restoration after the X-basis rotation.
* A CUDA projection loop at n=7 must peak below 3.5 density-matrix copies above a fixed
  128 MiB workspace allowance for both Z- and X-kind logical reads.
* Lazy ``rho`` construction materializes a zero matrix only on first access and supports
  pointer-preserving set/get round trips.
* ``_codestate_vector`` at n=7 must allocate less than 0.5 density-matrix copies above
  baseline, excluding a dense-embedding implementation.

GPU engine-device equivalence and memory tests use ``requires_cuda`` hard skips when CUDA
is unavailable. Explicit ``device="cpu"`` reference and bookkeeping tests run everywhere.
"""

import numpy as np
import pytest
import torch

from error_coupling_simulator.carrier.cptp_channel import hermitianize
from error_coupling_simulator.carrier.exact.qutrit_dm import (
    QutritDM,
    QuquartDM,
    _QuditDM,
    apply_local_op_q,
    embed_operator_q,
    hermitianize_inplace_blocked,
)

# Skip gate + canonical constants from tests/conftest.py.
from conftest import CDTYPE, DEVICE, requires_cuda


def _random_cptp_kraus(q: int, n_kraus: int, rng: np.random.Generator) -> list[torch.Tensor]:
    """A random CPTP single-qudit Kraus set via QR of a stacked Haar-ish block."""
    block = rng.standard_normal((n_kraus * q, q)) + 1j * rng.standard_normal((n_kraus * q, q))
    qmat, _ = np.linalg.qr(block)  # (n_kraus*q, q) with qmat^dag qmat = I_q
    return [torch.tensor(qmat[k * q:(k + 1) * q, :], dtype=CDTYPE) for k in range(n_kraus)]


def _random_mixed_rho(dim: int, rng: np.random.Generator) -> torch.Tensor:
    a = rng.standard_normal((dim, dim)) + 1j * rng.standard_normal((dim, dim))
    rho = a @ a.conj().T
    rho = rho / np.trace(rho).real
    return torch.tensor(rho, dtype=CDTYPE)


def _engine(cls, n: int, rho: torch.Tensor):
    # Engine-device checks are GPU-only and every consumer is requires_cuda-gated.
    eng = cls(n, device=DEVICE)
    eng.rho = rho.clone().to(DEVICE)
    return eng


# --------------------------------------------------------------------------- #
# Blockwise hermitianization                                                   #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("dim,block", [(7, 3), (16, 4), (81, 16), (81, 100)])
def test_hermitianize_blocked(dim, block):
    rng = np.random.default_rng(7)
    t = torch.tensor(
        rng.standard_normal((dim, dim)) + 1j * rng.standard_normal((dim, dim)),
        dtype=CDTYPE,
    )
    ref = hermitianize(t.clone())
    out = hermitianize_inplace_blocked(t.clone(), block=block)
    assert float((out - ref).abs().max()) < 1e-15
    # in place: the returned tensor IS the input storage
    t2 = t.clone()
    ret = hermitianize_inplace_blocked(t2, block=block)
    assert ret.data_ptr() == t2.data_ptr()


# --------------------------------------------------------------------------- #
# Chunked apply_channel equivalence (two independent references)               #
# --------------------------------------------------------------------------- #
@requires_cuda  # GPU-only engine-device test
@pytest.mark.parametrize("force_chunked", [False, True])
@pytest.mark.parametrize("cls,n", [(QutritDM, 2), (QutritDM, 3), (QutritDM, 4), (QuquartDM, 3)])
def test_apply_channel_matches_independent_paths(cls, n, force_chunked, monkeypatch):
    if force_chunked:
        # these registers sit below _CHUNK_MIN_DIM (the fast path); force the
        # chunked branch so BOTH code paths are equivalence-gated at unit scale.
        import error_coupling_simulator.carrier.exact.qutrit_dm as qdm
        monkeypatch.setattr(qdm, "_CHUNK_MIN_DIM", 1)
    q = cls.QDIM
    dim = q ** n
    rng = np.random.default_rng(1000 + 10 * q + n)
    kraus = _random_cptp_kraus(q, 3, rng)
    rho0 = _random_mixed_rho(dim, rng)
    for site in range(n):
        eng = _engine(cls, n, rho0)
        eng.apply_channel(kraus, site)
        got = eng.rho.cpu()

        # (a) independent path: per-Kraus sum of apply_local_op_q
        ref_a = torch.zeros_like(rho0)
        for k in kraus:
            ref_a = ref_a + apply_local_op_q(rho0.clone(), k, site, n, q)
        ref_a = hermitianize(ref_a)
        assert float((got - ref_a).abs().max()) < 1e-13, f"site {site} vs apply_local_op_q"

        # (b) from-scratch unchunked superoperator contraction
        left, right = q ** site, q ** (n - 1 - site)
        ks = torch.stack(kraus)
        sop = torch.einsum("kab,kce->acbe", ks, ks.conj())
        t = torch.einsum(
            "acbe,lbrLeR->larLcR", sop, rho0.reshape(left, q, right, left, q, right)
        ).reshape(dim, dim)
        ref_b = 0.5 * (t + t.conj().T)
        assert float((got - ref_b).abs().max()) < 1e-13, f"site {site} vs from-scratch einsum"


@requires_cuda  # GPU-only engine-device test
def test_apply_gate_unitary_roundtrip():
    """H then H on any site is the identity (chunked path, unitary special case)."""
    n, cls = 3, QutritDM
    rng = np.random.default_rng(5)
    rho0 = _random_mixed_rho(cls.QDIM ** n, rng)
    eng = _engine(cls, n, rho0)
    h = eng._hadamard()
    for site in range(n):
        eng.apply_gate(h, site)
        eng.apply_gate(h, site)
    assert float((eng.rho.cpu() - rho0).abs().max()) < 1e-13


# --------------------------------------------------------------------------- #
# Vector operation versus the dense embedding reference                        #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("cls,n", [(QutritDM, 3), (QutritDM, 5), (QuquartDM, 3)])
def test_apply_op_vector_matches_dense_embed(cls, n):
    q = cls.QDIM
    dim = q ** n
    rng = np.random.default_rng(2000 + n)
    psi = torch.tensor(
        rng.standard_normal(dim) + 1j * rng.standard_normal(dim), dtype=CDTYPE
    )
    op = torch.tensor(
        rng.standard_normal((q, q)) + 1j * rng.standard_normal((q, q)), dtype=CDTYPE
    )
    eng = cls(n, device="cpu")
    for site in range(n):
        got = eng._apply_op_vector(psi.clone(), op, site)
        full = embed_operator_q(op, site, n, q, device=psi.device)
        ref = full @ psi
        assert float((got - ref).abs().max()) < 1e-12, f"site {site}"


# --------------------------------------------------------------------------- #
# Lazy rho                                                                      #
# --------------------------------------------------------------------------- #
def test_lazy_rho_semantics():
    eng = QutritDM(3, device="cpu")
    assert eng._rho is None  # construction allocates no DM
    z = eng.rho  # first access materializes the zero-initialized matrix
    assert z.shape == (27, 27)
    assert float(z.abs().max()) == 0.0
    rho = _random_mixed_rho(27, np.random.default_rng(3))
    eng.rho = rho
    assert eng.rho.data_ptr() == rho.data_ptr()


def test_logical_distribution_regression():
    """Lean logical_distribution matches the definitional computation on a
    known state: |000> with logical_z={0:'Z'} reads (1,0); an X on qudit 0
    flips it to (0,1); a mixed rho normalizes correctly."""
    eng = QutritDM(3, device="cpu")
    eng.set_code(stabilizers=None, logical_z={0: "Z"})
    psi = torch.zeros(27, dtype=CDTYPE)
    psi[0] = 1.0
    eng.rho = torch.outer(psi, psi.conj())
    p0, p1 = eng.logical_distribution()
    assert abs(p0 - 1.0) < 1e-12 and abs(p1) < 1e-12
    eng.apply_gate(eng.single_qudit_gate("X"), 0)
    p0, p1 = eng.logical_distribution()
    assert abs(p0) < 1e-12 and abs(p1 - 1.0) < 1e-12
    # unnormalized rho: distribution is normalized internally
    eng.rho = 0.25 * eng.rho
    p0, p1 = eng.logical_distribution()
    assert abs(p1 - 1.0) < 1e-12


def test_logical_distribution_x_branch():
    """The X-kind logical readout uses clone-free rotation and exact restoration:
    |+>|00> reads logical_x={0:'X'} as p0=1; a Z on
    qudit 0 flips it to p1=1; rho is restored bit-identically after the call."""

    eng = QutritDM(3, device="cpu")
    eng.set_code(stabilizers=None, logical_x={0: "X"})
    psi = torch.zeros(27, dtype=CDTYPE)
    inv2 = 1.0 / (2.0 ** 0.5)
    psi[0] = inv2   # |000>
    psi[9] = inv2   # |100>  -> (|0>+|1>)/sqrt(2) on qudit 0
    eng.rho = torch.outer(psi, psi.conj())
    rho_before = eng.rho.clone()
    p0, p1 = eng.logical_distribution()
    assert abs(p0 - 1.0) < 1e-12 and abs(p1) < 1e-12
    assert float((eng.rho - rho_before).abs().max()) == 0.0  # restore is exact
    eng.apply_gate(eng.single_qudit_gate("Z"), 0)
    p0, p1 = eng.logical_distribution()
    assert abs(p0) < 1e-12 and abs(p1 - 1.0) < 1e-12


# --------------------------------------------------------------------------- #
# GPU projection-loop memory falsifier                                         #
# --------------------------------------------------------------------------- #
_WORKSPACE_ALLOWANCE = 128 * 2**20  # fixed cuBLAS/cuSOLVER workspace allowance (bytes)


@requires_cuda
@pytest.mark.parametrize("logical_kind", ["Z", "X"])
def test_detector_marg_loop_peak_below_3p5_copies(logical_kind):
    """At n=7 the peak above a fixed workspace allowance must stay below 3.5
    density-matrix copies. Both logical kinds run so the X-rotation readout branch
    of ``logical_distribution`` is bounded by the same threshold."""
    n = 7
    q = 3
    dim = q ** n
    copy_bytes = dim * dim * 16
    eng = QutritDM(n, device="cuda")
    stabs = [{0: "X", 1: "Z", 2: "Z", 3: "X"}, {2: "X", 3: "Z", 4: "Z", 5: "X"},
             {4: "X", 5: "Z", 6: "Z", 0: "X"}]
    logical = {0: logical_kind, 1: logical_kind}
    eng.set_code(stabilizers=stabs,
                 logical_z=logical if logical_kind == "Z" else None,
                 logical_x=logical if logical_kind == "X" else None)
    eng.init_logical(0)
    kraus = [torch.eye(q, dtype=CDTYPE) * (0.99 ** 0.5),
             torch.eye(q, dtype=CDTYPE) * (0.01 ** 0.5)]
    torch.cuda.empty_cache()
    # Measure the delta rather than the absolute peak so persistent module and cuBLAS
    # allocations from other CUDA tests are not charged to this test.
    base = torch.cuda.memory_allocated()
    torch.cuda.reset_peak_memory_stats()
    for s in range(n):
        eng.apply_channel(kraus, s)
    rho1 = eng.rho.clone()
    for stab in stabs:
        eng.rho = rho1.clone()
        eng.project_stabilizer(stab, 1, 0.9, "A")
    eng.rho = rho1.clone()
    eng.logical_distribution()
    peak = torch.cuda.max_memory_allocated() - base
    k = (peak - _WORKSPACE_ALLOWANCE) / copy_bytes
    # Structural live set: rho1 + working + apply output (+ chunk/tile temporaries)
    # The 3.5-copy cap above the allowance rejects redundant clones in either branch.
    assert k < 3.5, f"peak multiplier {k:.2f} >= 3.5 (memory-lean regression)"


@requires_cuda
def test_codestate_vector_allocates_no_dm():
    """The codestate-vector path must stay vector-scale; a dense
    ``embed_operator_q`` implementation allocates at least two density-matrix copies
    at n=7."""
    n = 7
    dim = 3 ** n
    copy_bytes = dim * dim * 16
    eng = QutritDM(n, device="cuda")
    stabs = [{0: "X", 1: "Z", 2: "Z", 3: "X"}, {2: "X", 3: "Z", 4: "Z", 5: "X"}]
    eng.set_code(stabilizers=stabs, logical_z={0: "Z", 1: "Z"})
    torch.cuda.empty_cache()
    base = torch.cuda.memory_allocated()
    torch.cuda.reset_peak_memory_stats()
    psi = eng._codestate_vector(0)
    assert psi.shape == (dim,)
    delta = torch.cuda.max_memory_allocated() - base
    assert delta < 0.5 * copy_bytes, (
        f"codestate-vector path allocated {delta / copy_bytes:.2f} DM copies "
        "(dense-embed regression)")
    # and the lazy constructor itself allocated no DM either
    assert eng._rho is None
