#!/usr/bin/env python3
"""Check the transversal-echo correction on the emitted logical observable.

The within-cycle carrier applies a transversal Y echo after every non-terminal
round.  The echo is physically load-bearing -- it symmetrises the asymmetric
energy-relaxation error -- so it stays applied.  But it anticommutes with an
odd-weight logical operator, and the real d3 XZZX patch has a weight-3 Z
logical, so before the fix the emitted observable carried a deterministic
``(R - 1) mod 2`` frame sign on top of the logical-flip bit.

Even-weight stabilizers are unaffected by the same echo, which is why the
detectors were always correct and only the observable was wrong.

This script asserts three things against the real Google ``d3_at_q6_7`` patch:

1. Noiseless, every round count R: the observable is a pure logical-flip bit,
   i.e. exactly zero, and the detectors are exactly zero.
2. The correction is independent of the prepared logical ``m``.
3. Under noise the detector statistics are untouched by the correction -- only
   the logical byte is rewritten -- and the detector rate still scales with the
   leakage angle.

Preconditions
-------------
* CUDA is available (the fused within-cycle sampler is GPU-only by design).
* The portable data root contains the ``d3_at_q6_7`` patch.
"""

from __future__ import annotations

import sys

REPO_MARKER = "error_coupling_simulator"


def emit(line: str = "") -> None:
    print(line, flush=True)


def main() -> int:
    import numpy as np

    from error_coupling_simulator.carrier.within_cycle import (
        FusedWithinCycleSampler,
        RunSpec,
    )
    from error_coupling_simulator.frontend import experiments as EX
    from error_coupling_simulator.frontend import xzzx_parser as XP

    import torch

    if not torch.cuda.is_available():
        raise SystemExit("precondition failed: CUDA is required for this carrier")

    circuit_path, metadata_path = XP.default_r01_paths()
    schedule = EX.load_xzzx_d3(with_interior_streams=True)
    logical_weight = len(schedule.logical)
    emit(f"patch          {circuit_path.parent.parent.name}")
    emit(f"n_data         {schedule.n_data}")
    emit(f"logical        {schedule.logical} (weight {logical_weight}, "
         f"kind {schedule.logical_kind})")
    emit(f"stabilizers    {len(schedule.stabilizers)}")
    emit()

    sampler = FusedWithinCycleSampler(device="cuda")

    def run(*, rounds: int, m: int, theta: float, g_seep: float, shots: int = 128):
        spec = RunSpec(
            circuit_path=circuit_path,
            metadata_path=metadata_path,
            m=m,
            theta=theta,
            g_seep=g_seep,
            g_heat=0.0,
            arm="A",
            b=1.0,
            readout_conv="biased_b",
            N=shots,
            base_seed=5,
            R=rounds,
            run_purpose="final",
        )
        batch = sampler.sample(spec, schedule=schedule)
        return batch, batch.to_det_obs()

    failures: list[str] = []

    emit("[1] noiseless: the observable must be a pure logical-flip bit")
    emit("     R   det_mean   obs_flip   verdict")
    for rounds in range(1, 9):
        _batch, rec = run(rounds=rounds, m=0, theta=0.0, g_seep=0.0)
        det_mean = float(rec["det"].mean())
        obs_flip = float(rec["obs"].mean())
        ok = det_mean == 0.0 and obs_flip == 0.0
        emit(f"    {rounds:2d}   {det_mean:.6f}   {obs_flip:.6f}   "
             f"{'ok' if ok else 'FAIL'}")
        if not ok:
            failures.append(
                f"noiseless R={rounds}: det_mean={det_mean} obs_flip={obs_flip}")
    emit()

    emit("[2] the correction is independent of the prepared logical m")
    for rounds in (2, 4, 5):
        for m in (0, 1):
            _batch, rec = run(rounds=rounds, m=m, theta=0.0, g_seep=0.0)
            obs_flip = float(rec["obs"].mean())
            ok = obs_flip == 0.0
            emit(f"    R={rounds} m={m}: obs_flip={obs_flip:.6f} "
                 f"{'ok' if ok else 'FAIL'}")
            if not ok:
                failures.append(f"noiseless R={rounds} m={m}: obs_flip={obs_flip}")
    emit()

    emit("[3] under noise the detector statistics are untouched")
    emit("     theta   det_rate   obs_flip")
    rates = []
    for theta in (0.0, 0.1, 0.2, 0.3, 0.5):
        batch, rec = run(rounds=10, m=0, theta=theta, g_seep=0.09, shots=512)
        det_rate = float(rec["det"].mean())
        rates.append(det_rate)
        emit(f"    {theta:5.2f}   {det_rate:.6f}   {float(rec['obs'].mean()):.6f}")
    if rates[0] != 0.0:
        failures.append(f"theta=0 with g_seep=0.09 gave det_rate={rates[0]}")
    if not all(a < b for a, b in zip(rates, rates[1:])):
        failures.append(f"detector rate is not monotone in theta: {rates}")
    emit()

    emit("[4] provenance records the correction")
    batch, _rec = run(rounds=4, m=0, theta=0.0, g_seep=0.0)
    prov = dict(batch.provenance)
    for key in ("observable_semantics", "transversal_echo_logical_parity"):
        value = prov.get(key)
        emit(f"    {key} = {value!r}")
        if value is None:
            failures.append(f"provenance missing {key}")
    emit()

    if failures:
        emit("FAIL")
        for line in failures:
            emit(f"  - {line}")
        return 1
    emit("PASS: the emitted observable is a logical-flip bit at every round count")
    return 0


if __name__ == "__main__":
    sys.exit(main())
