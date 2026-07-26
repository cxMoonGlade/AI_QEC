#!/usr/bin/env python3
"""Emit a multi-round detector/observable Record for a real surface-code patch.

Two legs, both already working and neither previously packaged. Each answers a
different question and neither certifies the other.

**pauli** — `stim.Circuit.generated("surface_code:rotated_memory_z", ...)` supplies
geometry, schedule, detectors, observable and a four-knob circuit-level noise model
at any distance; that circuit is executed through this repository's own
`StimCircuitSource` and `Simulator`, which emit the artifact set. Noise is Pauli by
construction (`representability: stim_pauli`). Distance is a parameter here.

**analog** — the real Google `d3_at_q6_7` XZZX patch is executed through the
within-cycle fused-SV carrier under a registered qutrit leakage preset. The noise is
non-Pauli and untwirled. Distance is *not* a parameter: the kernel is specialized to
nine data qutrits, and 3**25 amplitudes puts d5 out of reach of any state vector.

CLAIM BOUNDARY. Neither leg certifies anything. `pytest` and the coverage gate are
engineering surfaces; a passing run here shows the pipeline produces a Record of the
declared shape, not that the Record is faithful. See `docs/FAITHFULNESS_PROTOCOL.md`,
and `docs/service_status.json` for what `restricted_axis1_1d_mps` does and does not
claim.

Preconditions
-------------
* pauli leg: `stim` importable in the running environment.
* analog leg: CUDA available, and the portable data root holding the `d3_at_q6_7`
  patch (see `ECS_D3_DATA_ROOT`).
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import tempfile
import time


def emit(line: str = "") -> None:
    print(line, flush=True)


def run_pauli_leg(*, distance: int, rounds: int, shots: int, out_dir: Path, seed: int) -> int:
    """Stim-generated rotated surface code executed through our own Simulator."""

    import stim

    from error_coupling_simulator.frontend.simulator import Simulator
    from error_coupling_simulator.frontend.stim_source import StimCircuitSource

    emit(f"[pauli] stim {stim.__version__}, rotated_memory_z d={distance} rounds={rounds}")
    knobs = dict(
        after_clifford_depolarization=1e-3,
        before_measure_flip_probability=1e-3,
        after_reset_flip_probability=1e-3,
        before_round_data_depolarization=1e-3,
    )
    ideal = stim.Circuit.generated(
        "surface_code:rotated_memory_z", distance=distance, rounds=rounds
    )
    noisy = stim.Circuit.generated(
        "surface_code:rotated_memory_z", distance=distance, rounds=rounds, **knobs
    )

    # An executable falsifier that the emitted circuit really has the claimed
    # distance. Nothing in this repository checks that for its own constructors.
    observed = len(noisy.shortest_graphlike_error())
    emit(f"[pauli] qubits={noisy.num_qubits} detectors={noisy.num_detectors} "
         f"observables={noisy.num_observables}")
    emit(f"[pauli] shortest_graphlike_error={observed} (claimed distance {distance})")
    if observed != distance:
        emit(f"[pauli] FAIL: emitted circuit distance {observed} != {distance}")
        return 1

    staging = Path(tempfile.mkdtemp(prefix="real_code_pauli_"))
    ideal_path = staging / "ideal.stim"
    noisy_path = staging / "noisy.stim"
    ideal_path.write_text(str(ideal), encoding="utf-8")
    noisy_path.write_text(str(noisy), encoding="utf-8")

    started = time.perf_counter()
    result = Simulator(
        StimCircuitSource.from_file(ideal_path, noisy_path=noisy_path)
    ).run(shots=shots, seed=seed, out_dir=out_dir)
    elapsed = time.perf_counter() - started

    # The Record itself lands on disk as packed .b8; the result object carries the
    # summaries, not the arrays. (A probe that assumed `result.record` swallowed the
    # AttributeError in a bare except and reported artifacts it had not read.)
    summary = result.sample_summary_noisy
    emit(f"[pauli] {summary['num_shots']} shots in {elapsed:.2f}s: "
         f"{summary['num_detectors']} detectors, {summary['num_observables']} observable(s), "
         f"representability {summary['representability']}")
    emit(f"[pauli] any_detector_rate={summary['any_detector_rate']:.6f} "
         f"any_observable_rate={summary['any_observable_rate']:.6f} "
         "(undecoded; a logical error rate needs a named decoder)")
    emit(f"[pauli] artifacts -> {out_dir}")
    for path in sorted(out_dir.iterdir()):
        emit(f"           {path.name:34s} {path.stat().st_size:>9d} B")
    return 0


def run_analog_leg(*, rounds: int, shots: int, seed: int) -> int:
    """The real d3 XZZX patch through the within-cycle carrier, under qutrit leakage."""

    import torch

    from error_coupling_simulator.carrier.within_cycle import FusedWithinCycleSampler
    from error_coupling_simulator.frontend import experiments as experiments_mod

    if not torch.cuda.is_available():
        emit("[analog] SKIP: the fused within-cycle carrier is GPU-only by design")
        return 0

    schedule = experiments_mod.load_xzzx_d3(with_interior_streams=True)
    n_stab = len(schedule.stabilizers)
    emit(f"[analog] patch n_data={schedule.n_data} n_stab={n_stab} "
         f"logical={dict(schedule.logical)} kind={schedule.logical_kind}")

    preset = experiments_mod.PRESET_LEAK_THETA_0P30
    spec = experiments_mod.run_spec_from_preset(
        preset, n_shots=shots, n_rounds=rounds, seed=seed, m=0, run_purpose="final"
    )
    # No out_path is set here. `run_spec_from_preset` is the registered facade, and a
    # spec rebuilt outside it fails `_validate_run_numerical_provenance` with
    # "complete numerical_provenance is accepted only from the registered facade" --
    # correctly, since the rebuilt object no longer carries facade provenance.
    # Persisting this leg is the job of the registered writer entrypoint
    # `frontend.write_axis1_mcwf_mps_record_samples`, not of this script.
    emit(f"[analog] preset={preset.name} R={spec.R} N={spec.N} dtype={spec.dtype} "
         f"purpose={spec.run_purpose}")

    started = time.perf_counter()
    batch = FusedWithinCycleSampler(device="cuda").sample(
        spec, schedule=schedule, materialize=True
    )
    record = batch.to_det_obs()
    elapsed = time.perf_counter() - started

    det, obs = record["det"], record["obs"]
    emit(f"[analog] det{det.shape} obs{obs.shape} in {elapsed:.2f}s "
         f"max_norm_drift={batch.diag['max_norm_drift']:.2e}")
    per_round = [
        round(float(det[:, r * n_stab:(r + 1) * n_stab].mean()), 5) for r in range(spec.R)
    ]
    emit(f"[analog] per-round detector on-rate {per_round}")
    emit(f"[analog] observable flip rate {float(obs.mean()):.6f}")

    frame = batch.header.get("codestate_check", {}).get("transversal_echo_frame")
    if frame is not None:
        emit(f"[analog] echo frame derived={frame['derived_parity']} "
             f"measured={frame['measured_parity']} gates={frame['frame_gates_applied']}")
    emit(f"[analog] observable_semantics = "
         f"{batch.provenance.get('observable_semantics')!r}")
    emit("[analog] in-memory only; persist through "
         "frontend.write_axis1_mcwf_mps_record_samples")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--leg", choices=("pauli", "analog", "both"), default="both")
    parser.add_argument("--distance", type=int, default=3, help="pauli leg only")
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--shots", type=int, default=1024)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="artifact destination; a fresh temporary directory when omitted",
    )
    args = parser.parse_args()

    root = args.out_dir or Path(tempfile.mkdtemp(prefix="real_code_records_"))
    emit(f"artifact root {root}")
    emit("this run certifies nothing; see the module docstring for the claim boundary")
    emit()

    status = 0
    if args.leg in ("pauli", "both"):
        status |= run_pauli_leg(
            distance=args.distance,
            rounds=args.rounds,
            shots=args.shots,
            out_dir=root / f"pauli_d{args.distance}",
            seed=args.seed,
        )
        emit()
    if args.leg in ("analog", "both"):
        status |= run_analog_leg(rounds=args.rounds, shots=args.shots, seed=args.seed)
    return status


if __name__ == "__main__":
    sys.exit(main())
