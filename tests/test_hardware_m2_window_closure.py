"""R2-lite M2 — window-closure audit · pre-registered 2026-06-09 (docs/metric_results.md).

W1 (reported): interior-window naive closure X1 in [14%,22%] (X) / [12%,22%] (Z) —
the derived correction of the original "<5% naive" guess (boundary sep-1 stack
dominates via the device's 5.9x space-like excess).
W2 (HARD GATE): margin-2 leakage X2 <= 5% on every interior window, both bases
(point prediction ~1.9%). Pass => margin-2 windowed calibration (M3) is sound.
W3 (reported): end-window X1 / interior mean in [0.5, 0.8].
W4 (reported): interior X1 flat (rel std < 15%); spikes are located back-edge
directions, never attributed.
"""
from __future__ import annotations

import functools
import warnings

import pytest

from qec_twin.hardware.dataset import RepCodeD29, resolve_rep29_root

pytestmark = pytest.mark.skipif(
    resolve_rep29_root() is None, reason="R2-lite d29 dataset absent (set QEC_TWIN_HW_DATA)"
)

from qec_twin.hardware import pij, stim_artifacts, windows  # noqa: E402

W1_BAND = {"X": (0.14, 0.22), "Z": (0.12, 0.22)}
W2_GATE = 0.05
W3_BAND = (0.5, 0.8)
W4_RELSTD = 0.15


@functools.lru_cache(maxsize=None)
def _scores(basis: str):
    ds = RepCodeD29(resolve_rep29_root())
    paths = ds.paths(basis, 0)
    grid = stim_artifacts.detector_grid(
        stim_artifacts.load_circuit(paths.circuit_ideal),
        dem_circuit=stim_artifacts.load_circuit(paths.circuit_noisy_si1000),
        qubit_order=ds.load_metadata(basis, 0).get("qubit_order"),
    )
    counts = pij.accumulate_pair_counts(paths.detection_events, grid)
    masses = windows.site_pair_masses(counts, grid)
    return windows.window_closure_audit(masses, grid.num_chains)


def _soft(condition: bool, message: str) -> None:
    print(message)
    if not condition:
        warnings.warn(f"side-bet out of band (finding, not failure): {message}")


def test_w2_margin2_closure_gate():
    for basis in ("X", "Z"):
        scores = _scores(basis)
        interior = [s for s in scores if s.is_interior]
        worst = max(interior, key=lambda s: s.x2)
        print(f"W2 {basis}: max interior X2 = {worst.x2:.4%} at window {worst.start} (gate {W2_GATE:.0%})")
        assert all(s.x2 <= W2_GATE for s in interior), (
            f"W2 FAIL {basis}: X2 {worst.x2:.4%} > {W2_GATE:.0%} at window {worst.start} "
            f"— margin-2 windowing unsound; pre-registered routing: widen windows/margin "
            f"or accelerate the ADR 0008 carrier; the leakage profile is the back-edge output"
        )


def test_w1_w3_w4_reported():
    for basis in ("X", "Z"):
        scores = _scores(basis)
        interior = [s.x1 for s in scores if s.is_interior]
        ends = [s.x1 for s in scores if not s.is_interior]
        mean_x1 = sum(interior) / len(interior)
        lo, hi = W1_BAND[basis]
        _soft(lo <= mean_x1 <= hi, f"W1 {basis}: interior X1 mean {mean_x1:.2%} in [{lo:.0%}, {hi:.0%}]")
        for e in ends:
            _soft(W3_BAND[0] <= e / mean_x1 <= W3_BAND[1],
                  f"W3 {basis}: end-window X1 ratio {e / mean_x1:.2f} in {W3_BAND}")
        rel_std = (sum((x - mean_x1) ** 2 for x in interior) / len(interior)) ** 0.5 / mean_x1
        _soft(rel_std < W4_RELSTD, f"W4 {basis}: interior X1 rel std {rel_std:.2%} < {W4_RELSTD:.0%}")
        table = " ".join(f"{s.start}:{s.x1:.3f}/{s.x2:.4f}" for s in scores)
        print(f"   {basis} windows start:X1/X2 -> {table}")
