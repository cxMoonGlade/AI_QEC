"""M3 window-NLL scoring driver (R2-lite, ADR 0007 Decision 4 M3).

Scores gates P1-P3 and reported P4-P11 strictly against the dated
pre-registration (docs/metric_results.md, "2026-06-09 -- R2-lite M3
PRE-REGISTRATION"). Run:

    QEC_TWIN_HW_DATA=<parent dir> python -m qec_twin.hardware.m3_report

Committed adjudication notes (recorded with the build, BEFORE the run):
- "Mixed-state init" of the burn-in = the closed-form diagonal stationary
  product (forward/exact/steady_state.py docstring); from the maximally mixed
  state the registered fixed-point pin (1e-9 within 320 rounds) is provably
  unreachable at device rates for non-unital channels.
- The in-class naive point is operationalized as homogeneous
  ``f = q = 5.1e-3`` (matching the measured M1-P8 SI1000 MC detection fraction
  2.03% via ``1 - 2 p_det = (1-2f)^2 (1-2q)^2``) with ``delta = 0`` (X) /
  ``delta = 0.1 f`` (Z, the dephasing-asymmetry direction); the P2 rank
  statement is generic in any in-class point with the registered
  basis-symmetry structure.
- P1e flatness is pinned with PHASE-completion fiber members (strictly
  diagonal/antidiagonal Kraus: zero cat-term leak, exact flatness); a coherent
  fiber member's deviation is bounded by the registered cat-term ceiling
  (~1e-5 nats corpus) and is reported, not gated. The "corpus NLL" pin is
  operationalized per shot (460 blocks): float64 round-off alone exceeds 1e-9
  on a 6.4e7-nat corpus total.
- The drift-isolated fallback split trains on the FIRST half of sample_00 and
  scores the second half (training on the full sample would contaminate it).
- P10 sigma: shot-level bootstrap (B=1000, seed 20260609) of per-shot region
  sums over interior chains 1..26, layers [80, 999]; class entries from
  pooled-region moments (a pooled-moment estimate, not the M1 mean-of-entries).
- P11 sigma: spread of the per-window central-qubit ratio across the 19 clean
  windows (SE = std/sqrt(19)); the ratio is >= 1 by AM-GM, so the X-basis
  "= 1 within 2 sigma" carries a small positive Jensen bias, reported as such.
"""

from __future__ import annotations

import argparse
import os
import tempfile
from dataclasses import dataclass
from itertools import product
from pathlib import Path

import numpy as np
import torch

from qec_twin.calibration import hardware_nll
from qec_twin.forward.cptp_channel import CDTYPE, RDTYPE, StinespringChannel
from qec_twin.forward.exact.circuit_sim import rx
from qec_twin.forward.exact.steady_state import (
    fixed_point_residual,
    simulate_steady_block,
)
from qec_twin.hardware import b8_io, baselines, blocks, m1_report
from qec_twin.hardware.dataset import RepCodeD29
from qec_twin.hardware.pij import spitz_pij_exact
from qec_twin.hardware.stim_artifacts import DetectorGrid
from qec_twin.numerics import NUMERICAL_ZERO

M3_SEED = 20260609
BOOT_REPLICATES = 1000
TRAIN_SAMPLE = 0
HELDOUT_SAMPLES = (1, 2, 3, 4)
FIT_SEEDS = (0, 1)
FIT_STEPS = 300
NUM_BLOCKS = blocks.block_starts().size  # 460
MODELS = ("twin", "naive", "pij", "pij_nodiag", "in_class")

CLEAN_WINDOWS = blocks.CLEAN_INTERIOR_WINDOWS  # 19 windows
HOT_CONTROL_WINDOWS = blocks.HOT_WINDOWS  # {15, 19}: P7 positive control only
HOT_PAIR_WINDOWS = (16, 17, 18)  # P5 located set
W_QUIET = tuple(w for w in CLEAN_WINDOWS if w not in HOT_PAIR_WINDOWS)

# P1a pin: heterogeneous rates so site-permutation/convention bugs cannot cancel.
PIN_F = (0.008, 0.012, 0.010, 0.014, 0.009)
PIN_Q = (0.012, 0.015, 0.013, 0.011)
PIN_SHOTS = 1_000_000
PIN_ROUNDS = 8
PIN_BLOCK_LAYER = 4  # detector layers (4, 5): deep in the (exactly stationary) Pauli bulk

# In-class naive point (committed adjudication note above).
NAIVE_INCLASS_F = 5.1e-3
NAIVE_INCLASS_Q = 5.1e-3
NAIVE_INCLASS_DELTA = {"X": 0.0, "Z": 5.1e-4}

P2_RANK_REL_FLOOR = 1e-9
P2_TOP9_SHARE_MIN = 0.99
P3_MARGIN_BAND = {"X": (35.0, 160.0), "Z": (30.0, 150.0)}
P3_COUNT_FLOOR = 30.0
P4_BAND = (-4.0, 6.0)
P4_ABLATION_BAND = (1.0, 3.5)
P5_BAND = {17: (4.0, 13.0), 16: (2.3, 4.5), 18: (2.3, 4.5)}
P5_BASIS_REL_TOL = 0.15
P6_BAND = (0.0, 3.0)
P7_Q_BAND = (1.1e-2, 1.8e-2)
P7_F_BAND = (0.9e-2, 1.7e-2)
P7_EDGE_EXCESS = 1.2e-3
P7_REPLICATE_REL = 0.10
P8_RANGE_MAX = 2.0
P10_FLOOR = {"X": 5e-3, "Z": 6e-3}
P10_SIGMA_MIN = 10.0
P10_INTERIOR_CHAINS = (1, 26)  # inclusive; chain edges carry the one-sided bias
NLL_SANITY = {"X": (550.0, 700.0), "Z": (540.0, 690.0)}


def _in_band(value: float, band) -> bool:
    return band[0] <= value <= band[1]


def _resolve_device(device: str) -> str:
    if device == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    return device


# ---------------------------------------------------------------- in-class channels


def flip_channel_kraus(p01, p10, *, alpha: float = 0.0, beta: float = 0.0) -> torch.Tensor:
    """Diagonal-Markov fiber member ``{(p01, p10)}`` with phase completion.

    ``K0 = diag(sqrt(1-p01), e^{i alpha} sqrt(1-p10))``,
    ``K1 = antidiag(e^{i beta} sqrt(p10), sqrt(p01))`` -- strictly
    diagonal/antidiagonal Kraus, so the iso-pair phase family has ZERO
    cat-term leak (P1e). Differentiable in ``p01, p10``.
    """
    p01 = torch.as_tensor(p01, dtype=RDTYPE)
    p10 = torch.as_tensor(p10, dtype=RDTYPE).to(p01.device)
    ea = torch.exp(1j * torch.as_tensor(float(alpha), dtype=RDTYPE)).to(CDTYPE).to(p01.device)
    eb = torch.exp(1j * torch.as_tensor(float(beta), dtype=RDTYPE)).to(CDTYPE).to(p01.device)
    zero = torch.zeros((), dtype=CDTYPE, device=p01.device)
    k0 = torch.stack(
        [
            torch.stack([torch.sqrt(1 - p01).to(CDTYPE), zero]),
            torch.stack([zero, ea * torch.sqrt(1 - p10).to(CDTYPE)]),
        ]
    )
    k1 = torch.stack(
        [
            torch.stack([zero, eb * torch.sqrt(p10).to(CDTYPE)]),
            torch.stack([torch.sqrt(p01).to(CDTYPE), zero]),
        ]
    )
    return torch.stack([k0, k1])


def in_class_field(f, delta, theta=None):
    """Time-shared channel field of in-class members: flip(p01, p10) o RX(theta)."""
    f = list(f)
    delta = list(delta)
    theta = [0.0] * len(f) if theta is None else list(theta)
    stacks = []
    for fi, di, ti in zip(f, delta, theta):
        kraus = flip_channel_kraus(
            torch.as_tensor(fi, dtype=RDTYPE) + torch.as_tensor(di, dtype=RDTYPE),
            torch.as_tensor(fi, dtype=RDTYPE) - torch.as_tensor(di, dtype=RDTYPE),
        )
        ti_t = torch.as_tensor(ti, dtype=RDTYPE)
        if isinstance(ti, torch.Tensor) or float(ti_t) != 0.0:
            kraus = kraus @ rx(ti_t)
        stacks.append(kraus)
    return lambda t, i: stacks[i]


def in_class_block_law(
    f, delta, q, *, theta=None, device: str = "cpu", burn_in=40, max_burn_in=320, fp_tol=1e-9
) -> torch.Tensor:
    law = simulate_steady_block(
        in_class_field(f, delta, theta),
        burn_in=burn_in,
        max_burn_in=max_burn_in,
        fp_tol=fp_tol,
        device=device,
    )
    q_t = q if isinstance(q, torch.Tensor) else torch.as_tensor(list(q), dtype=RDTYPE, device=device)
    return hardware_nll.readout_convolution(law, q_t)


# ---------------------------------------------------------------- P1 pins


def _pin_stim_circuit(f, q, rounds: int):
    import stim

    lines = ["R 0 1 2 3 4 5 6 7 8"]
    for t in range(int(rounds)):
        for i, fi in enumerate(f):
            lines.append(f"X_ERROR({fi}) {i}")
        lines.append("CX 0 5 1 6 2 7 3 8")
        lines.append("CX 1 5 2 6 3 7 4 8")
        for j, qj in enumerate(q):
            lines.append(f"X_ERROR({qj}) {5 + j}")  # record flip; MR resets clean
        lines.append("MR 5 6 7 8")
        if t >= 1:
            for j in range(4):
                lines.append(f"DETECTOR rec[{-4 + j}] rec[{-8 + j}]")
    return stim.Circuit("\n".join(lines))


def run_p1a_pauli_slice(
    *, shots: int = PIN_SHOTS, seed: int = M3_SEED, device: str = "cpu"
) -> dict:
    """(a) Pauli-slice equivalence: twin steady block law == stim d=5 within 5 MC SE."""
    circuit = _pin_stim_circuit(PIN_F, PIN_Q, PIN_ROUNDS)
    sampler = circuit.compile_detector_sampler(seed=int(seed))
    dets = np.asarray(sampler.sample(int(shots)), dtype=np.uint8)
    base = (PIN_BLOCK_LAYER - 1) * 4  # detector layer t has indices (t-1)*4 + j
    pattern = np.zeros(dets.shape[0], dtype=np.int64)
    for k in range(4):
        pattern |= dets[:, base + k].astype(np.int64) << (2 * k)
        pattern |= dets[:, base + 4 + k].astype(np.int64) << (2 * k + 1)
    hist = np.bincount(pattern, minlength=256).astype(np.float64)
    empirical = hist / hist.sum()

    with torch.no_grad():
        law = in_class_block_law(PIN_F, [0.0] * 5, PIN_Q, device=device)
    model = law.cpu().numpy()
    se = np.maximum(np.sqrt(model * (1.0 - model) / float(shots)), 1.0 / float(shots))
    z = (empirical - model) / se
    tvd = 0.5 * float(np.abs(empirical - model).sum())
    return {
        "pin": "P1a",
        "passed": bool(np.abs(z).max() <= 5.0),
        "max_abs_z": float(np.abs(z).max()),
        "tvd": tvd,
        "shots": int(shots),
        "seed": int(seed),
    }


def run_p1b_fixed_point(
    *, device: str = "cpu", burn_in: int = 40, max_burn_in: int = 320, tol: float = 1e-9
) -> dict:
    """(b) fixed-point pin at the X (delta=0) and Z (delta!=0) in-class naive points."""
    rows = {}
    for basis in ("X", "Z"):
        delta = NAIVE_INCLASS_DELTA[basis]
        field = in_class_field([NAIVE_INCLASS_F] * 5, [delta] * 5)
        residual, rounds_used = fixed_point_residual(
            field, burn_in=burn_in, max_burn_in=max_burn_in, tol=tol, device=device
        )
        rows[basis] = {"residual": residual, "rounds": rounds_used, "delta": delta}
    return {
        "pin": "P1b",
        "passed": all(r["residual"] <= tol for r in rows.values()),
        "tol": tol,
        "rows": rows,
    }


def _readout_enumeration_reference(law: np.ndarray, q: np.ndarray) -> np.ndarray:
    """Brute-force 4096-flip-configuration reference for the readout convolution."""
    out = np.zeros_like(law)
    z = np.arange(law.size)
    site_configs = list(product([0, 1], repeat=3))
    for flips in product(range(8), repeat=4):
        prob = 1.0
        shift = 0
        for k, idx in enumerate(flips):
            a = site_configs[idx]
            w = sum(a)
            prob *= q[k] ** w * (1.0 - q[k]) ** (3 - w)
            e = (a[0] ^ a[1]) | ((a[1] ^ a[2]) << 1)
            shift |= e << (2 * k)
        out[z ^ shift] += prob * law
    return out


def run_p1c_convolution_vs_enumeration(*, seed: int = M3_SEED, device: str = "cpu") -> dict:
    """(c) analytic readout convolution == flip enumeration, <= 1e-12."""
    rng = np.random.default_rng(int(seed))
    law_np = rng.dirichlet(np.ones(256))
    q_np = np.array([0.012, 0.02, 0.008, 0.015])
    with torch.no_grad():
        conv = hardware_nll.readout_convolution(
            torch.as_tensor(law_np, dtype=RDTYPE, device=device),
            torch.as_tensor(q_np, dtype=RDTYPE, device=device),
        )
    reference = _readout_enumeration_reference(law_np, q_np)
    diff = float(np.abs(conv.cpu().numpy() - reference).max())
    return {"pin": "P1c", "passed": diff <= 1e-12, "max_abs_diff": diff}


def _reference_block_histograms(bits: np.ndarray, grid: DetectorGrid, windows, t0) -> np.ndarray:
    """Independent (per-block-loop) extractor for the P1d pipeline-identity pin."""
    hist = np.zeros((len(windows), 256), dtype=np.int64)
    weights0 = np.array([1, 4, 16, 64], dtype=np.int64)
    weights1 = np.array([2, 8, 32, 128], dtype=np.int64)
    for w, start in enumerate(windows):
        cols = blocks.interior_chains(start)
        for t in t0:
            det0 = bits[:, grid.grid[t, cols]].astype(np.int64)
            det1 = bits[:, grid.grid[t + 1, cols]].astype(np.int64)
            pat = det0 @ weights0 + det1 @ weights1
            hist[w] += np.bincount(pat, minlength=256)
    return hist


def run_p1d_extractor_identity(
    ds: RepCodeD29 | None, *, shots: int = 2000, seed: int = M3_SEED
) -> dict:
    """(d) extractor pipeline-identity on sim events (b8 round-trip + reference path)."""
    if ds is not None:
        grid = m1_report.build_grid(ds, ds.bases[0])
    else:  # synthetic complete grid with the d29 shape (extractor identity only)
        layers, chains = 1002, 28
        grid = DetectorGrid(
            det_to_layer=np.repeat(np.arange(layers, dtype=np.int32), chains),
            det_to_chain=np.tile(np.arange(chains, dtype=np.int32), layers),
            grid=np.arange(layers * chains, dtype=np.int64).reshape(layers, chains),
            num_layers=layers,
            num_chains=chains,
            chain_order_source="synthetic",
        )
    bits_per_shot = grid.num_layers * grid.num_chains
    rng = np.random.default_rng(int(seed))
    bits = (rng.random((int(shots), bits_per_shot)) < 0.05).astype(np.uint8)
    packed = b8_io.pack_bits(bits)
    windows = [1, 7, 21]
    handle, tmp_path = tempfile.mkstemp(suffix=".b8")
    try:
        os.close(handle)
        packed.tofile(tmp_path)
        pipeline = blocks.block_histograms(tmp_path, grid, windows, chunk_shots=512)
        # per-shot NLL consistency against the histogram on the same file
        rng2 = np.random.default_rng(int(seed) + 1)
        log_p = np.log(rng2.dirichlet(np.ones(256), size=len(windows)))
        nll = blocks.per_shot_block_nll_multi(tmp_path, grid, windows, log_p, chunk_shots=512)
        hist_nll = np.array([-(pipeline[w] * log_p[w]).sum() for w in range(len(windows))])
        nll_gap = float(np.abs(nll.sum(axis=0) - hist_nll).max())
    finally:
        os.unlink(tmp_path)
    reference = _reference_block_histograms(bits, grid, windows, blocks.block_starts())
    identical = bool((pipeline == reference).all())
    return {
        "pin": "P1d",
        "passed": identical and nll_gap <= 1e-6 * float(np.abs(hist_nll).max()),
        "histograms_identical": identical,
        "per_shot_vs_histogram_nll_gap": nll_gap,
        "grid_source": grid.chain_order_source,
    }


P1E_RATE_BUMP = 7e-3  # the device-naive rate gap P3 must resolve; sigma(b) = b/2 * sqrt(N_blk N_shots I_rate)
                      # measured I_rate ~ 153.5/block => predicted ~595 sigma, band [400, 800] (ledger adjudication 6)


def run_p1e_in_fiber_flatness(*, device: str = "cpu") -> dict:
    """(e) iso-{p01, p10} member swap is exactly flat; a rate step is not."""
    p01 = [0.013, 0.011, 0.014, 0.010, 0.012]
    p10 = [0.012, 0.013, 0.010, 0.013, 0.011]
    q = [0.013, 0.015, 0.012, 0.014]

    def law_for(alpha, beta, bump: float = 0.0):
        stacks = [
            flip_channel_kraus(p01[i] + (bump if i == 2 else 0.0), p10[i] + (bump if i == 2 else 0.0),
                               alpha=alpha, beta=beta)
            for i in range(5)
        ]
        field = lambda t, i: stacks[i]  # noqa: E731
        with torch.no_grad():
            law = simulate_steady_block(field, device=device)
            return hardware_nll.readout_convolution(
                law, torch.as_tensor(q, dtype=RDTYPE, device=device)
            ).cpu().numpy()

    law_a = law_for(0.0, 0.0)
    law_b = law_for(0.7, -0.4)
    law_bump = law_for(0.0, 0.0, bump=P1E_RATE_BUMP)

    ref = np.clip(law_a, NUMERICAL_ZERO, None)
    swap_nll_per_shot = NUM_BLOCKS * float(np.abs((ref * (np.log(np.clip(law_b, NUMERICAL_ZERO, None)) - np.log(ref))).sum()))
    delta_log = np.log(ref) - np.log(np.clip(law_bump, NUMERICAL_ZERO, None))
    shift_per_shot = NUM_BLOCKS * float((ref * delta_log).sum())
    var_block = float((ref * delta_log**2).sum() - ((ref * delta_log).sum()) ** 2)
    se_corpus = np.sqrt(NUM_BLOCKS * var_block / 4e5)  # held-out-sized corpus
    sigma_units = abs(shift_per_shot) / max(se_corpus, NUMERICAL_ZERO)
    return {
        "pin": "P1e",
        "passed": swap_nll_per_shot < 1e-9 and float(np.abs(law_a - law_b).max()) < 1e-13
        and sigma_units > 100.0,
        "swap_nll_per_shot": swap_nll_per_shot,
        "swap_law_max_diff": float(np.abs(law_a - law_b).max()),
        "rate_step_nll_per_shot": shift_per_shot,
        "rate_step_sigma_units": float(sigma_units),
    }


def run_p1f_z2_swap(*, device: str = "cpu", seed: int = 7) -> dict:
    """(f) per-qubit Z2 value relabel (X-conjugated channel) leaves the law invariant."""
    channels = [StinespringChannel.random(2, 2, seed=seed + i) for i in range(5)]
    q = torch.as_tensor([0.013, 0.015, 0.012, 0.014], dtype=RDTYPE, device=device)
    x = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)

    def law_for(conjugated: tuple) -> np.ndarray:
        stacks = []
        for i, channel in enumerate(channels):
            kraus = channel.kraus().detach()
            if i in conjugated:
                kraus = torch.einsum("ab,ebc,cd->ead", x, kraus, x)
            stacks.append(kraus)
        field = lambda t, i: stacks[i]  # noqa: E731
        with torch.no_grad():
            law = simulate_steady_block(field, device=device)
            return hardware_nll.readout_convolution(law, q).cpu().numpy()

    base = law_for(())
    rel = max(
        float(np.abs(law_for((2,)) - base).max()),
        float(np.abs(law_for((0, 4)) - base).max()),
    ) / max(float(base.max()), NUMERICAL_ZERO)
    return {"pin": "P1f", "passed": rel < 1e-12, "max_rel_diff": rel}


def run_p1g_reset_readout_gauge(*, seed: int = M3_SEED, device: str = "cpu") -> dict:
    """(g) two record-flip layers fold exactly: conv(conv(law, q), r) == conv(law, q*r)."""
    rng = np.random.default_rng(int(seed) + 2)
    law = torch.as_tensor(rng.dirichlet(np.ones(256)), dtype=RDTYPE, device=device)
    q = torch.as_tensor([0.010, 0.014, 0.008, 0.012], dtype=RDTYPE, device=device)
    r = torch.as_tensor([0.004, 0.002, 0.006, 0.003], dtype=RDTYPE, device=device)
    with torch.no_grad():
        twice = hardware_nll.readout_convolution(hardware_nll.readout_convolution(law, q), r)
        folded = hardware_nll.readout_convolution(law, q + r - 2 * q * r)
    diff = float((twice - folded).abs().max())
    return {"pin": "P1g", "passed": diff < 1e-12, "max_abs_diff": diff}


def run_p1_pins(
    ds: RepCodeD29 | None = None,
    *,
    device: str = "cpu",
    shots: int = PIN_SHOTS,
    max_burn_in: int = 320,
    fp_tol: float = 1e-9,
) -> dict:
    pins = {
        "a": run_p1a_pauli_slice(shots=shots, device=device),
        "b": run_p1b_fixed_point(device=device, max_burn_in=max_burn_in, tol=fp_tol),
        "c": run_p1c_convolution_vs_enumeration(device=device),
        "d": run_p1d_extractor_identity(ds),
        "e": run_p1e_in_fiber_flatness(device=device),
        "f": run_p1f_z2_swap(device=device),
        "g": run_p1g_reset_readout_gauge(device=device),
    }
    return {"gate": "P1", "passed": all(p["passed"] for p in pins.values()), "pins": pins}


# ---------------------------------------------------------------- P2 Fisher


def run_p2_fisher(
    *,
    device: str = "cpu",
    f0: float = NAIVE_INCLASS_F,
    q0: float = NAIVE_INCLASS_Q,
    deltas: dict = None,
    burn_in: int = 40,
    max_burn_in: int = 320,
    fp_tol: float = 1e-9,
) -> dict:
    """Fisher spectrum of the block NLL at the in-class naive point (run BEFORE fits).

    Parameterization (19): ``f_1..f_5``, ``delta_1..delta_5``, ``theta_1..theta_5``
    (coherent RX directions -- predicted numerical null), ``q_1..q_4``.
    ``F = J^T diag(1/p) J`` with ``J = d(law)/d(params)`` by autograd.
    """
    deltas = NAIVE_INCLASS_DELTA if deltas is None else deltas
    rows = {}
    for basis, delta0 in deltas.items():
        x0 = torch.tensor(
            [f0] * 5 + [float(delta0)] * 5 + [0.0] * 5 + [q0] * 4,
            dtype=RDTYPE,
            device=device,
        )

        def law_fn(x: torch.Tensor) -> torch.Tensor:
            f, delta, theta, q = x[0:5], x[5:10], x[10:15], x[15:19]
            return in_class_block_law(
                f, delta, q, theta=theta, device=device,
                burn_in=burn_in, max_burn_in=max_burn_in, fp_tol=fp_tol,
            )

        try:
            jac = torch.autograd.functional.jacobian(law_fn, x0, vectorize=True)  # (256, 19)
        except RuntimeError:  # vmap-unsupported op fallback: 256 plain backward passes
            jac = torch.autograd.functional.jacobian(law_fn, x0)
        with torch.no_grad():
            p = law_fn(x0).clamp_min(NUMERICAL_ZERO)
            fisher = jac.T @ (jac / p[:, None])
            eig = torch.linalg.eigvalsh(fisher).flip(0).cpu().numpy()  # descending
        top = float(eig[0])
        rank = int((eig > P2_RANK_REL_FLOOR * top).sum())
        top9_share = float(eig[:9].sum() / eig.sum())
        rows[basis] = {
            "eigenvalues": eig.tolist(),
            "rank": rank,
            "top9_trace_share": top9_share,
            "weak_eigs_10_plus": eig[9:14].tolist(),
            "passed": rank >= 9 and top9_share >= P2_TOP9_SHARE_MIN,
            "delta0": float(delta0),
        }
    return {"gate": "P2", "passed": all(r["passed"] for r in rows.values()), "rows": rows}


# ---------------------------------------------------------------- fits


@dataclass
class FitRecord:
    basis: str
    window: int
    seed: int
    split: str  # "full" | "first_half"
    ce_per_block: float
    law: np.ndarray  # [256]
    q_eff: np.ndarray  # [4]
    markov: np.ndarray  # [5, 2] (p01, p10)
    fp_residual: float
    fp_rounds: int


def _cache_key(basis: str, window: int, seed: int, split: str) -> str:
    return f"{basis}/{window}/{seed}/{split}"


def fit_windows(
    ds: RepCodeD29,
    basis: str,
    windows,
    *,
    seeds=FIT_SEEDS,
    steps: int = FIT_STEPS,
    device: str = "cpu",
    burn_in: int = 40,
    max_burn_in: int = 320,
    fp_tol: float = 1e-9,
    split: str = "full",
    cache_path: str | None = None,
    allow_fit: bool = True,
    verbose: bool = True,
) -> dict:
    """Fit every (window, seed); returns ``{"selected": {w: FitRecord}, "all": [...]}``.

    Train split = sample_00 (``split="first_half"`` = the drift-isolated
    fallback's train half). Selection: per window, the seed with the lower
    TRAIN cross-entropy (registered). ``cache_path`` stores finished fits so
    scoring sections can rerun without refitting.
    """
    grid = m1_report.build_grid(ds, basis)
    paths = ds.paths(basis, TRAIN_SAMPLE)
    shot_slice = None
    if split == "first_half":
        total = b8_io.num_shots_in_file(paths.detection_events, grid.num_layers * grid.num_chains)
        shot_slice = (0, total // 2)
    histograms = blocks.block_histograms(
        paths.detection_events, grid, list(windows), shot_slice=shot_slice
    )

    cache: dict = {}
    if cache_path and Path(cache_path).exists():
        cache = torch.load(cache_path, weights_only=False)
    records: list[FitRecord] = []
    for w_index, window in enumerate(windows):
        for seed in seeds:
            key = _cache_key(basis, int(window), int(seed), split)
            if key in cache:
                records.append(cache[key])
                continue
            if not allow_fit:
                raise RuntimeError(f"--skip-fit set but {key} is not in {cache_path}")
            result = hardware_nll.calibrate_window(
                histograms[w_index],
                steps=steps,
                seed=int(seed),
                device=device,
                burn_in=burn_in,
                max_burn_in=max_burn_in,
                fp_tol=fp_tol,
            )
            record = FitRecord(
                basis=basis,
                window=int(window),
                seed=int(seed),
                split=split,
                ce_per_block=float(result["ce_per_block"]),
                law=result["block_law"].cpu().numpy(),
                q_eff=result["q_eff"].cpu().numpy(),
                markov=result["markov_pairs"].cpu().numpy(),
                fp_residual=float(result["fp_residual"]),
                fp_rounds=int(result["fp_rounds"]),
            )
            records.append(record)
            cache[key] = record
            if cache_path:
                Path(cache_path).parent.mkdir(parents=True, exist_ok=True)
                torch.save(cache, cache_path)
            if verbose:
                print(
                    f"    fit {basis}/w{window}/s{seed}/{split}: CE/block "
                    f"{record.ce_per_block:.6f} (NLL/shot {NUM_BLOCKS * record.ce_per_block:.2f}), "
                    f"fp {record.fp_residual:.2e}@{record.fp_rounds}",
                    flush=True,
                )
    selected = {}
    for window in windows:
        candidates = [r for r in records if r.window == int(window)]
        selected[int(window)] = min(candidates, key=lambda r: r.ce_per_block)
    return {"selected": selected, "all": records, "histograms": histograms}


# ---------------------------------------------------------------- held-out scoring


def _log_law(law: np.ndarray) -> np.ndarray:
    return np.log(np.clip(np.asarray(law, dtype=np.float64), NUMERICAL_ZERO, None))


def build_model_laws(
    ds: RepCodeD29,
    basis: str,
    windows,
    fits: dict,
    *,
    device: str = "cpu",
    burn_in: int = 40,
    max_burn_in: int = 320,
    fp_tol: float = 1e-9,
    naive_shots: int = baselines.NAIVE_MC_SHOTS,
    train_shot_slice=None,
    verbose: bool = True,
) -> np.ndarray:
    """``[n_models, n_windows, 256]`` laws in MODELS order, all on the same family."""
    grid = m1_report.build_grid(ds, basis)
    paths = ds.paths(basis, TRAIN_SAMPLE)
    if verbose:
        print(f"    laws {basis}: naive MC ({naive_shots} shots, seed {baselines.NAIVE_MC_SEED})", flush=True)
    naive_hists = baselines.naive_block_histograms(
        paths.circuit_noisy_si1000, grid, list(windows), shots=naive_shots
    )
    if verbose:
        print(f"    laws {basis}: pij arm (train pooled moments)", flush=True)
    moments = baselines.pooled_block_moments(
        paths.detection_events, grid, shot_slice=train_shot_slice
    )
    with torch.no_grad():
        in_class = (
            in_class_block_law(
                [NAIVE_INCLASS_F] * 5,
                [NAIVE_INCLASS_DELTA[basis]] * 5,
                [NAIVE_INCLASS_Q] * 4,
                device=device,
                burn_in=burn_in,
                max_burn_in=max_burn_in,
                fp_tol=fp_tol,
            )
            .cpu()
            .numpy()
        )
    laws = np.zeros((len(MODELS), len(windows), 256), dtype=np.float64)
    for w_index, window in enumerate(windows):
        laws[0, w_index] = fits["selected"][int(window)].law
        laws[1, w_index] = baselines.kt_smooth(naive_hists[w_index])
        laws[2, w_index] = baselines.pij_block_model(moments, grid, window).law
        laws[3, w_index] = baselines.pij_block_model(
            moments, grid, window, drop_diagonal_edges=True
        ).law
        laws[4, w_index] = in_class
    return laws


def heldout_per_shot(
    ds: RepCodeD29,
    basis: str,
    windows,
    laws: np.ndarray,
    *,
    samples=HELDOUT_SAMPLES,
    shot_slices: dict | None = None,
    chunk_shots: int = 10_000,
    verbose: bool = True,
) -> dict:
    """Per held-out sample: ``[shots, n_models, n_windows]`` per-shot NLL arrays."""
    grid = m1_report.build_grid(ds, basis)
    log_p = np.stack([_log_law(laws[m]) for m in range(laws.shape[0])])
    out = {}
    for sample in samples:
        if verbose:
            print(f"    held-out {basis}/sample_{sample:02d}", flush=True)
        out[sample] = blocks.per_shot_block_nll_multi(
            ds.paths(basis, sample).detection_events,
            grid,
            list(windows),
            log_p,
            shot_slice=None if shot_slices is None else shot_slices.get(sample),
            chunk_shots=chunk_shots,
        )
    return out


def paired_bootstrap(
    values: np.ndarray, *, replicates: int = BOOT_REPLICATES, seed: int = M3_SEED
) -> dict:
    values = np.asarray(values, dtype=np.float64)
    rng = np.random.default_rng(int(seed))
    n = values.shape[0]
    reps = np.empty(int(replicates), dtype=np.float64)
    for b in range(int(replicates)):
        reps[b] = values[rng.integers(0, n, size=n)].mean()
    return {
        "mean": float(values.mean()),
        "se": float(reps.std(ddof=1)),
        "q01": float(np.quantile(reps, 0.01)),
        "q99": float(np.quantile(reps, 0.99)),
        "q025": float(np.quantile(reps, 0.025)),
        "q975": float(np.quantile(reps, 0.975)),
    }


def run_p3(basis: str, windows, per_shot: dict) -> dict:
    """The M3 GATE: aggregate held-out ΔNLL(naive - twin) > 0 at one-sided 99%."""
    pooled = np.concatenate([per_shot[s] for s in sorted(per_shot)], axis=0)
    twin, naive = pooled[:, 0, :], pooled[:, 1, :]
    delta = naive - twin  # [shots, n_windows]
    margins = {int(w): float(delta[:, i].mean()) for i, w in enumerate(windows)}
    boot = paired_bootstrap(delta.mean(axis=1))
    band = P3_MARGIN_BAND[basis]
    sanity = {int(w): float(twin[:, i].mean()) for i, w in enumerate(windows)}
    return {
        "gate": "P3",
        "basis": basis,
        "passed": boot["q01"] > 0.0,
        "aggregate": boot,
        "per_window_margin": margins,
        "margins_in_band": sum(_in_band(m, band) for m in margins.values()),
        "count_ge_30": sum(m >= P3_COUNT_FLOOR for m in margins.values()),
        "band": band,
        "nll_twin_per_window": sanity,
        "nll_sanity_band": NLL_SANITY[basis],
        "nll_sanity_ok": all(_in_band(v, NLL_SANITY[basis]) for v in sanity.values()),
    }


def run_p4_p5(basis: str, windows, per_shot: dict) -> dict:
    """G3 = NLL_twin - NLL_pij on W_quiet (P4, two-sided) + hot-pair windows (P5)."""
    pooled = np.concatenate([per_shot[s] for s in sorted(per_shot)], axis=0)
    twin, pij_arm, nodiag = pooled[:, 0, :], pooled[:, 2, :], pooled[:, 3, :]
    g3 = twin - pij_arm
    index = {int(w): i for i, w in enumerate(windows)}
    quiet_cols = [index[w] for w in W_QUIET if w in index]
    quiet_boot = paired_bootstrap(g3[:, quiet_cols].mean(axis=1))
    per_window_g3 = {int(w): float(g3[:, i].mean()) for i, w in enumerate(windows)}
    ablation = {
        int(w): float((nodiag[:, i] - pij_arm[:, i]).mean()) for i, w in enumerate(windows)
    }
    quiet_ablation = float(np.mean([ablation[w] for w in W_QUIET if w in index]))
    hot = {w: per_window_g3.get(w) for w in HOT_PAIR_WINDOWS}
    quiet_max = max(per_window_g3[w] for w in W_QUIET if w in index)
    return {
        "section": "P4/P5",
        "basis": basis,
        "g3_quiet": quiet_boot,
        "g3_band": P4_BAND,
        "g3_in_band": _in_band(quiet_boot["mean"], P4_BAND),
        "per_window_g3": per_window_g3,
        "ablation_quiet": quiet_ablation,
        "ablation_band": P4_ABLATION_BAND,
        "ablation_in_band": _in_band(quiet_ablation, P4_ABLATION_BAND),
        "per_window_ablation": ablation,
        "hot_g3": hot,
        "hot_bands": P5_BAND,
        "hot_17_exceeds_quiet_max": hot.get(17) is not None and hot[17] > quiet_max,
        "quiet_max_g3": quiet_max,
    }


def run_p6(basis: str, windows, per_shot: dict) -> dict:
    pooled = np.concatenate([per_shot[s] for s in sorted(per_shot)], axis=0)
    naive, in_class = pooled[:, 1, :], pooled[:, 4, :]
    delta = float((in_class - naive).mean())
    per_window = {int(w): float((in_class[:, i] - naive[:, i]).mean()) for i, w in enumerate(windows)}
    return {
        "section": "P6",
        "basis": basis,
        "in_class_minus_naive": delta,
        "band": P6_BAND,
        "in_band": _in_band(delta, P6_BAND),
        "per_window": per_window,
    }


def run_p7(basis: str, windows, fits: dict, hot_fits: dict | None = None) -> dict:
    """Parameter tables: q^eff and f-hat bands, edge excess, sliding replicates."""
    selected = fits["selected"]
    q_rows, f_rows = {}, {}
    site_estimates: dict[int, list] = {}
    qubit_estimates: dict[int, dict] = {}
    for window, record in selected.items():
        q_rows[window] = record.q_eff.tolist()
        f_hat = record.markov.mean(axis=1)  # (p01 + p10) / 2 per model qubit
        f_rows[window] = f_hat.tolist()
        for k in range(4):
            site_estimates.setdefault(window + 1 + k, []).append((window, float(record.q_eff[k])))
        for qubit in range(5):
            position = "edge" if qubit in (0, 4) else "interior"
            qubit_estimates.setdefault(window + 1 + qubit, {}).setdefault(position, []).append(
                float(f_hat[qubit])
            )
    interior_f = [v for d in qubit_estimates.values() for v in d.get("interior", [])]
    edge_f = [v for d in qubit_estimates.values() for v in d.get("edge", [])]
    seed_gap = {}
    for record in fits["all"]:
        if record.seed == FIT_SEEDS[0]:
            partner = next(
                (r for r in fits["all"] if r.window == record.window and r.seed != record.seed),
                None,
            )
            if partner is not None:  # relative seed-pair gap: the replicate-SE proxy
                mean_q = max(float((record.q_eff + partner.q_eff).mean() / 2.0), NUMERICAL_ZERO)
                seed_gap[record.window] = float(np.abs(record.q_eff - partner.q_eff).max()) / mean_q
    replicate = {}
    for site, pairs in site_estimates.items():
        values = np.array([v for _, v in pairs])
        if values.size >= 2:
            replicate[site] = float((values.max() - values.min()) / max(values.mean(), NUMERICAL_ZERO))
    hot_replicate = {}
    if hot_fits:
        for window, record in hot_fits["selected"].items():
            for k in range(4):
                site = window + 1 + k
                if site in site_estimates:
                    clean_mean = np.mean([v for _, v in site_estimates[site]])
                    hot_replicate[(window, site)] = float(
                        abs(record.q_eff[k] - clean_mean) / max(clean_mean, NUMERICAL_ZERO)
                    )
    q_all = np.array([v for row in q_rows.values() for v in row])
    return {
        "section": "P7",
        "basis": basis,
        "q_mean": float(q_all.mean()),
        "q_band": P7_Q_BAND,
        "q_in_band_frac": float(np.mean([(P7_Q_BAND[0] <= v <= P7_Q_BAND[1]) for v in q_all])),
        "interior_f_mean": float(np.mean(interior_f)),
        "edge_f_mean": float(np.mean(edge_f)),
        "edge_minus_interior": float(np.mean(edge_f) - np.mean(interior_f)),
        "edge_excess_prediction": P7_EDGE_EXCESS,
        "f_band": P7_F_BAND,
        "interior_f_in_band_frac": float(
            np.mean([(P7_F_BAND[0] <= v <= P7_F_BAND[1]) for v in interior_f])
        ),
        "replicate_rel_spread": replicate,
        "replicate_worst": max(replicate.values()) if replicate else float("nan"),
        "seed_q_gap": seed_gap,
        "hot_control_replicate": hot_replicate,
        "q_table": q_rows,
        "f_table": f_rows,
    }


def run_p8(basis: str, windows, per_shot: dict) -> dict:
    """Per-sample NLL_twin stability: range <= 2 nats/shot after MAD burst exclusion."""
    rows = {}
    for sample, arr in per_shot.items():
        twin = arr[:, 0, :]
        means = {}
        flagged = {}
        for i, w in enumerate(windows):
            v = twin[:, i]
            median = float(np.median(v))
            scale = 1.4826 * float(np.median(np.abs(v - median)))
            mask = np.abs(v - median) > 5.0 * scale if scale > 0 else np.zeros(v.size, bool)
            means[int(w)] = float(v[~mask].mean())
            flagged[int(w)] = int(mask.sum())
        rows[sample] = {"means": means, "flagged_shots": flagged}
    ranges = {}
    for i, w in enumerate(windows):
        values = [rows[s]["means"][int(w)] for s in rows]
        ranges[int(w)] = float(max(values) - min(values))
    worst = max(ranges.values())
    return {
        "section": "P8",
        "basis": basis,
        "per_window_range": ranges,
        "worst_range": worst,
        "in_band": worst <= P8_RANGE_MAX,
        "per_sample": rows,
    }


# ---------------------------------------------------------------- P10 budget deficit


_P10_CLASSES = ((0, 1, 0), (1, 0, 0), (1, 1, 1), (1, 1, -1))


def _budget_per_shot_sums(
    events_paths, grid: DetectorGrid, *, layer_lo=80, layer_hi=999, chunk_shots=10_000,
    shot_slices=None,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """Per-shot fire counts + per-class joint counts over the interior region."""
    c_lo, c_hi = P10_INTERIOR_CHAINS
    fires_all, joints_all = [], []
    counts = {}
    for p_index, path in enumerate(events_paths):
        bits_per_shot = grid.num_layers * grid.num_chains
        shot_slice = None if shot_slices is None else shot_slices[p_index]
        for _, packed in b8_io.iter_b8_chunks(
            path, bits_per_shot, chunk_shots=chunk_shots, shot_slice=shot_slice
        ):
            bits = np.unpackbits(packed, axis=1, count=bits_per_shot, bitorder="little")
            g = bits[:, grid.grid.ravel()].reshape(bits.shape[0], grid.num_layers, grid.num_chains)
            x = g[:, layer_lo : layer_hi + 1, c_lo : c_hi + 1]
            n, layers, chains = x.shape
            fires_all.append(x.reshape(n, -1).sum(axis=1, dtype=np.int64))
            row = np.zeros((n, len(_P10_CLASSES)), dtype=np.int64)
            for c_index, (di, dt, orient) in enumerate(_P10_CLASSES):
                rows = layers - dt
                if orient >= 0:
                    a = x[:, :rows, : chains - di] & x[:, dt:, di:]
                else:
                    a = x[:, dt:, : chains - di] & x[:, :rows, di:]
                row[:, c_index] = a.reshape(n, -1).sum(axis=1, dtype=np.int64)
                counts[(di, dt, orient)] = rows * (chains - di)
            joints_all.append(row)
    counts["sites"] = (layer_hi - layer_lo + 1) * (c_hi - c_lo + 1)
    return np.concatenate(fires_all), np.concatenate(joints_all), counts


def _deficit_from_sums(fires: np.ndarray, joints: np.ndarray, counts: dict) -> float:
    f_bar = fires.mean() / counts["sites"]
    total = 0.0
    for c_index, key in enumerate(_P10_CLASSES):
        mij = joints[:, c_index].mean() / counts[key]
        total += 2.0 * float(spitz_pij_exact(np.float64(f_bar), np.float64(f_bar), np.float64(mij)))
    bound = -0.5 * np.log(1.0 - 2.0 * f_bar)
    return float(total - bound)


def run_p10(ds: RepCodeD29, basis: str, *, chunk_shots: int = 10_000, verbose=True) -> dict:
    grid = m1_report.build_grid(ds, basis)
    rows = {}
    for split, samples in (("train", (TRAIN_SAMPLE,)), ("heldout", HELDOUT_SAMPLES)):
        if verbose:
            print(f"    P10 {basis}/{split}", flush=True)
        paths = [ds.paths(basis, s).detection_events for s in samples]
        fires, joints, counts = _budget_per_shot_sums(paths, grid, chunk_shots=chunk_shots)
        deficit = _deficit_from_sums(fires, joints, counts)
        rng = np.random.default_rng(M3_SEED)
        n = fires.shape[0]
        reps = np.empty(BOOT_REPLICATES)
        for b in range(BOOT_REPLICATES):
            idx = rng.integers(0, n, size=n)
            reps[b] = _deficit_from_sums(fires[idx], joints[idx], counts)
        se = float(reps.std(ddof=1))
        rows[split] = {
            "deficit": deficit,
            "se": se,
            "sigma": deficit / max(se, NUMERICAL_ZERO),
            "floor": P10_FLOOR[basis],
            "ok": deficit >= P10_FLOOR[basis] and deficit / max(se, NUMERICAL_ZERO) >= P10_SIGMA_MIN,
        }
    return {"section": "P10", "basis": basis, "rows": rows}


# ---------------------------------------------------------------- P11 bunching


def run_p11(basis: str, fits: dict) -> dict:
    central, interior_all, delta_prime = [], [], []
    for record in fits["selected"].values():
        pairs = record.markov
        for qubit in (1, 2, 3):
            p01, p10 = float(pairs[qubit, 0]), float(pairs[qubit, 1])
            ratio = (p01 + p10) ** 2 / max(4.0 * p01 * p10, NUMERICAL_ZERO)
            if qubit == 2:
                central.append(ratio)
                delta_prime.append(abs(p01 - p10) / max(p01 + p10, NUMERICAL_ZERO))
            interior_all.append(ratio)
    central = np.array(central)
    mean, se = float(central.mean()), float(central.std(ddof=1) / np.sqrt(central.size))
    sigma = (mean - 1.0) / max(se, NUMERICAL_ZERO)
    return {
        "section": "P11",
        "basis": basis,
        "central_ratio_mean": mean,
        "central_ratio_se": se,
        "sigma_above_1": sigma,
        "ordering_ok": sigma >= 10.0 if basis == "Z" else abs(sigma) <= 2.0,
        "interior_ratio_mean": float(np.mean(interior_all)),
        "central_delta_prime_mean": float(np.mean(delta_prime)),
        "jensen_caveat": "ratio >= 1 by AM-GM; X-basis '=1 within 2 sigma' carries positive bias",
    }


# ---------------------------------------------------------------- driver


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--skip-pins", action="store_true")
    parser.add_argument("--skip-fisher", action="store_true")
    parser.add_argument("--skip-fit", action="store_true", help="use only cached fits")
    parser.add_argument("--skip-gate", action="store_true", help="skip P3")
    parser.add_argument("--skip-pij", action="store_true", help="skip P4/P5")
    parser.add_argument("--skip-p6", action="store_true")
    parser.add_argument("--skip-params", action="store_true", help="skip P7")
    parser.add_argument("--skip-samples", action="store_true", help="skip P8")
    parser.add_argument("--skip-budget", action="store_true", help="skip P10")
    parser.add_argument("--skip-bunching", action="store_true", help="skip P11")
    parser.add_argument("--skip-hot-controls", action="store_true", help="skip {15,19} P7 control fits")
    parser.add_argument("--run-fallback", action="store_true", help="drift-isolated half-split (P8)")
    parser.add_argument("--bases", nargs="+", default=["X", "Z"])
    parser.add_argument("--seeds", type=int, nargs="+", default=list(FIT_SEEDS))
    parser.add_argument("--steps", type=int, default=FIT_STEPS)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--max-burn-in", type=int, default=320)
    parser.add_argument("--fp-tol", type=float, default=1e-9)
    parser.add_argument("--pin-shots", type=int, default=PIN_SHOTS)
    parser.add_argument("--chunk-shots", type=int, default=10_000)
    parser.add_argument("--fit-cache", default="outputs/m3_fit_cache.pt")
    args = parser.parse_args(argv)
    device = _resolve_device(args.device)
    print(f"device: {device}", flush=True)

    ds = RepCodeD29.from_env()
    print(f"dataset: {ds.root}", flush=True)

    if not args.skip_pins:
        p1 = run_p1_pins(
            ds, device=device, shots=args.pin_shots, max_burn_in=args.max_burn_in, fp_tol=args.fp_tol
        )
        print(f"\n== P1 machinery pins: {'PASS' if p1['passed'] else 'FAIL'}", flush=True)
        for name, pin in p1["pins"].items():
            detail = {k: v for k, v in pin.items() if k not in ("pin", "passed")}
            print(f"   ({name}) {'ok' if pin['passed'] else 'FAIL'}: {detail}", flush=True)

    if not args.skip_fisher:
        p2 = run_p2_fisher(device=device, max_burn_in=args.max_burn_in, fp_tol=args.fp_tol)
        print(f"\n== P2 Fisher spectrum (BEFORE any fit): {'PASS' if p2['passed'] else 'FAIL'}", flush=True)
        for basis, row in p2["rows"].items():
            eig = row["eigenvalues"]
            print(f"   {basis} (delta0={row['delta0']:.1e}): rank {row['rank']} "
                  f"top9 {row['top9_trace_share']:.4%}; eig[0,8,9,11,14] = "
                  f"{eig[0]:.3e} {eig[8]:.3e} {eig[9]:.3e} {eig[11]:.3e} {eig[14]:.3e}", flush=True)

    needs_fits = not (args.skip_gate and args.skip_pij and args.skip_p6 and args.skip_params
                      and args.skip_samples and args.skip_bunching)
    for basis in args.bases:
        if not needs_fits:
            break
        print(f"\n-- fits {basis} (cache: {args.fit_cache})", flush=True)
        fits = fit_windows(
            ds, basis, CLEAN_WINDOWS, seeds=tuple(args.seeds), steps=args.steps,
            device=device, max_burn_in=args.max_burn_in, fp_tol=args.fp_tol,
            cache_path=args.fit_cache, allow_fit=not args.skip_fit,
        )
        hot_fits = None
        if not args.skip_hot_controls and not args.skip_params:
            hot_fits = fit_windows(
                ds, basis, HOT_CONTROL_WINDOWS, seeds=tuple(args.seeds), steps=args.steps,
                device=device, max_burn_in=args.max_burn_in, fp_tol=args.fp_tol,
                cache_path=args.fit_cache, allow_fit=not args.skip_fit,
            )
        laws = build_model_laws(
            ds, basis, CLEAN_WINDOWS, fits, device=device,
            max_burn_in=args.max_burn_in, fp_tol=args.fp_tol,
        )
        per_shot = heldout_per_shot(ds, basis, CLEAN_WINDOWS, laws, chunk_shots=args.chunk_shots)

        if not args.skip_gate:
            p3 = run_p3(basis, CLEAN_WINDOWS, per_shot)
            agg = p3["aggregate"]
            print(f"\n== P3 GATE {basis}: {'PASS' if p3['passed'] else 'FAIL'} -- aggregate "
                  f"dNLL(naive - twin) {agg['mean']:.2f} (boot q01 {agg['q01']:.2f}, SE {agg['se']:.3f})",
                  flush=True)
            print(f"   margins in {p3['band']}: {p3['margins_in_band']}/19; >= +30: "
                  f"{p3['count_ge_30']}/19 (predict 19/19); twin NLL sanity "
                  f"{p3['nll_sanity_band']}: {p3['nll_sanity_ok']}", flush=True)
            print(f"   per-window margins: {p3['per_window_margin']}", flush=True)

        if not args.skip_pij:
            p4 = run_p4_p5(basis, CLEAN_WINDOWS, per_shot)
            g3 = p4["g3_quiet"]
            print(f"\n== P4 {basis} (reported, two-sided): G3 quiet {g3['mean']:.2f} "
                  f"[{g3['q025']:.2f}, {g3['q975']:.2f}] in {p4['g3_band']}: {p4['g3_in_band']}",
                  flush=True)
            print(f"   diagonal ablation quiet {p4['ablation_quiet']:.2f} in "
                  f"{p4['ablation_band']}: {p4['ablation_in_band']}", flush=True)
            print(f"== P5 {basis}: hot G3 {p4['hot_g3']} bands {p4['hot_bands']}; "
                  f"17 > quiet max ({p4['quiet_max_g3']:.2f}): {p4['hot_17_exceeds_quiet_max']}",
                  flush=True)

        if not args.skip_p6:
            p6 = run_p6(basis, CLEAN_WINDOWS, per_shot)
            print(f"\n== P6 {basis}: in-class SI1000 - naive-MC {p6['in_class_minus_naive']:.2f} "
                  f"in {p6['band']}: {p6['in_band']}", flush=True)

        if not args.skip_params:
            p7 = run_p7(basis, CLEAN_WINDOWS, fits, hot_fits)
            print(f"\n== P7 {basis}: q mean {p7['q_mean']:.4e} in {p7['q_band']} "
                  f"({p7['q_in_band_frac']:.0%} of entries); interior f {p7['interior_f_mean']:.4e} "
                  f"in {p7['f_band']} ({p7['interior_f_in_band_frac']:.0%}); edge - interior "
                  f"{p7['edge_minus_interior']:+.2e} (predict +{P7_EDGE_EXCESS:.1e})", flush=True)
            print(f"   replicate worst rel spread {p7['replicate_worst']:.2%} "
                  f"(crit max(10%, 5*SE)); hot-control deviations {p7['hot_control_replicate']}",
                  flush=True)

        if not args.skip_samples:
            p8 = run_p8(basis, CLEAN_WINDOWS, per_shot)
            print(f"\n== P8 {basis}: worst per-window range {p8['worst_range']:.2f} <= "
                  f"{P8_RANGE_MAX}: {p8['in_band']}", flush=True)
            if args.run_fallback:
                print(f"   fallback (drift-isolated) split {basis}: fitting first half", flush=True)
                fb_fits = fit_windows(
                    ds, basis, CLEAN_WINDOWS, seeds=tuple(args.seeds), steps=args.steps,
                    device=device, max_burn_in=args.max_burn_in, fp_tol=args.fp_tol,
                    split="first_half", cache_path=args.fit_cache,
                    allow_fit=not args.skip_fit,
                )
                fb_laws = build_model_laws(
                    ds, basis, CLEAN_WINDOWS, fb_fits, device=device,
                    max_burn_in=args.max_burn_in, fp_tol=args.fp_tol,
                    train_shot_slice=(0, 50_000),
                )
                fb_shots = heldout_per_shot(
                    ds, basis, CLEAN_WINDOWS, fb_laws, samples=(TRAIN_SAMPLE,),
                    shot_slices={TRAIN_SAMPLE: (50_000, 100_000)},
                    chunk_shots=args.chunk_shots,
                )
                fb = run_p3(basis, CLEAN_WINDOWS, fb_shots)
                print(f"   fallback aggregate dNLL {fb['aggregate']['mean']:.2f} "
                      f"(q01 {fb['aggregate']['q01']:.2f}); margins >= +30: {fb['count_ge_30']}/19",
                      flush=True)

        if not args.skip_bunching:
            p11 = run_p11(basis, fits)
            print(f"\n== P11 {basis}: central bunching ratio {p11['central_ratio_mean']:.4f} "
                  f"(SE {p11['central_ratio_se']:.4f}, {p11['sigma_above_1']:.1f} sigma above 1) "
                  f"ordering ok: {p11['ordering_ok']}; |delta'| {p11['central_delta_prime_mean']:.3f}",
                  flush=True)

    if not args.skip_budget:
        for basis in args.bases:
            p10 = run_p10(ds, basis, chunk_shots=args.chunk_shots)
            print(f"\n== P10 {basis}: budget deficit", flush=True)
            for split, row in p10["rows"].items():
                print(f"   {split}: {row['deficit']:.3e} (SE {row['se']:.1e}, "
                      f"{row['sigma']:.0f} sigma) >= {row['floor']:.0e} at >= 10 sigma: {row['ok']}",
                      flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
