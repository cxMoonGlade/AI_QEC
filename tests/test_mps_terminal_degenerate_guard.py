"""Regression: the serial hard3/soft terminal's degenerate (zero-norm) guard actually
fires (chip task_9f0687fe; batched_mps_backend_prereg.md v5 FINDING, tie-break/guard
registry).

``MpsLeakageForward._terminal_readout`` (mps_forward.py, hard3/soft level path) carries
the WRITTEN guard ``tot <= NUMERICAL_ZERO => kbar = 0``. Pre-fix it was NaN-shadowed dead
code: ``_site_population`` is a quimb NORMALIZED read that divides by the trace
unconditionally, so an exactly-zero-norm state (a projectively annihilated branch) gave
NaN populations, ``NaN <= NUMERICAL_ZERO`` is False, the cumulative loop fell through to
``kbar = 2``, and the ``|2> -> bit`` sub-draw's NaN-guard branches emitted
``bit = (0.5 < b_for_bit)`` (= 1 at b = 0.9). The fix reads the populations ONLY when the
pre-read norm ``wt > NUMERICAL_ZERO`` -- bit-identical on any live state (same normalized
reads, same arithmetic) -- so the degenerate leg lands on the written path: ``kbar = 0``,
``bit = 0``, no NaN. That is the batched arm's normative semantics
(``batched_mps.site_rdm``'s per-shot ``<= NUMERICAL_ZERO`` mask leaves a degenerate shot
unscaled -> populations ~0 -> the tot-guard fires).

GPU-only (model compute stays on cuda, house rule); n = 4 qutrits, O(GPU-seconds).
"""

from __future__ import annotations

import numpy as np
import pytest
import torch

qtn = pytest.importorskip("quimb.tensor")

from qec_twin.forward.scalable.mps_forward import MpsLeakageForward
from qec_twin.numerics import NUMERICAL_ZERO

# Skip gate + canonical constants from tests/conftest.py (Wave 1, contract C1).
from conftest import CDTYPE, DEVICE, PHYS, requires_cuda

pytestmark = [requires_cuda]

N = 4                 # qutrits (never the full d3 9-chain; keep it at GPU-seconds)
LOG_SUPPORT = [0, 1]  # engine positions of the logical support (identity site order)
B_EFF = 0.9           # readout bias: the pre-fix degenerate leg emitted bit=(0.5<0.9)=1


# AM-4 (api_hardening_ownership_design.md, v2 REVIEW DISPOSITIONS): this file is
# ARM-UNDER-TEST for mps_forward -- its `_qmps_product`/`_fwd` loaders are deliberately
# local (referees mps_forward; must not import mps_forward loaders or batched_mps).
# Do NOT migrate them to shared test support.
def _fwd() -> MpsLeakageForward:
    # __init__ only stores the device (quimb import lazy) -> the REAL serial method is
    # driven directly, same discipline as tests/test_batched_mps_ops.py; _eng_to_mps /
    # _log_eng_support are normally set by sample() -- set them explicitly (identity).
    fwd = MpsLeakageForward(device=DEVICE)
    fwd._eng_to_mps = {q: q for q in range(N)}
    fwd._log_eng_support = list(LOG_SUPPORT)
    return fwd


def _qmps_product(levels: "list[int]"):
    """quimb MPS ``|levels[0], levels[1], ...>`` (site-0-MSB ``from_dense`` convention,
    identity site order), arrays mapped to torch cuda complex128."""
    idx = 0
    for lv in levels:
        idx = idx * PHYS + int(lv)
    arr = np.zeros(PHYS ** N, dtype=np.complex128)
    arr[idx] = 1.0
    mps = qtn.MatrixProductState.from_dense(arr, dims=[PHYS] * N)
    mps.apply_to_arrays(lambda x: torch.as_tensor(x, dtype=CDTYPE, device=DEVICE))
    return mps


def _annihilate(mps) -> None:
    """Drive the MPS to EXACT zero norm the way production does: a projective collapse
    onto an orthogonal level (|1><1| on site 0 of |0...0>); ``_renormalize``'s
    skip-at-zero then leaves the zero state in place."""
    proj = torch.zeros((PHYS, PHYS), dtype=CDTYPE, device=DEVICE)
    proj[1, 1] = 1.0
    mps.gate_(proj, where=0, contract=True)
    MpsLeakageForward._renormalize(mps)


def _read(fwd, mps, m: int, u: float):
    return fwd._terminal_readout(
        mps, log_sites=list(LOG_SUPPORT), log_isx=[0] * len(LOG_SUPPORT), n_data=N,
        b_eff=B_EFF, m=int(m), u_draws=[float(u)] * N, mode="hard3", gen=None)


@pytest.mark.parametrize("m", [0, 1])
def test_hard3_zero_norm_state_takes_written_guard(m):
    """Zero-norm state through hard3: EVERY site must land on the written degenerate
    guard -- kbar = 0, bit = 0, flip = m -- with no NaN (pre-fix: NaN populations ->
    kbar = 2, bit = 1)."""
    fwd = _fwd()
    mps = _qmps_product([0] * N)
    _annihilate(mps)
    wt = MpsLeakageForward._norm_sq(mps)
    assert wt <= NUMERICAL_ZERO, f"precondition: state not degenerate (wt={wt!r})"
    tr = _read(fwd, mps, m=m, u=0.9)  # u=0.9: the pre-fix leg emitted bit=(0.5<0.9)=1
    assert list(tr.levels) == [0] * N, f"degenerate kbar must be 0 (got {tr.levels})"
    assert list(tr.bits) == [0] * N, f"degenerate bit must be 0 (got {tr.bits})"
    assert tr.flip == (m & 1), "flip = parity(=0) XOR m on the degenerate leg"
    d = mps.to_dense()
    if not isinstance(d, torch.Tensor):
        d = torch.as_tensor(np.asarray(d))
    assert bool(torch.isfinite(d.reshape(-1).abs()).all()), "post-readout state has NaN/Inf"


def test_hard3_live_state_control_unchanged():
    """POSITIVE CONTROL (fails on a wrong fix): a unit-norm |1,2,0,2> product state must
    still Born-sample deterministically -- levels (1,2,0,2); the |2> sub-draw
    u2 = 0.3 < b_for_bit = 0.9 -> bit 1. A fix that blankets kbar = 0 everywhere, or
    perturbs the live-state Born arithmetic, fails here (margins >= 0.3, no knife-edge)."""
    fwd = _fwd()
    lv_in = [1, 2, 0, 2]
    mps = _qmps_product(lv_in)
    wt = MpsLeakageForward._norm_sq(mps)
    assert abs(wt - 1.0) < 1e-12, f"precondition: control state not unit-norm (wt={wt!r})"
    tr = _read(fwd, mps, m=0, u=0.3)
    assert list(tr.levels) == lv_in, f"live-state levels changed (got {tr.levels})"
    assert list(tr.bits) == [1, 1, 0, 1], f"live-state bits changed (got {tr.bits})"
    assert tr.flip == 0, "parity over support [0,1] = 1 XOR 1 = 0, m = 0"
