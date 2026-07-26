#!/usr/bin/env python3
"""Truncation error versus bond dimension, against the registered dense Born oracle.

The restricted QT/MPS route has a registered independent oracle: for a schedule small
enough to build an exact 2**N density matrix, `axis1_measurement_record_evidence_manifest`
enumerates the measurement-record distribution densely, and
`axis1_qt_mps_restricted_execution_manifest` compares its own record probabilities
against it and gates on `max_abs_probability_difference <= 1e-8`.

Every existing call site of the bond sweep passes `bond_values=(1, 2)`. This script asks
the question those call sites do not: how does the record-probability error actually
behave as `chi` is squeezed below the exact bond, and does the reported discarded weight
predict it?

CIRCUIT. `n` qubits in MPS site order 0..n-1. Hadamard the low half, then CX each low
qubit into its partner in the high half. Every one of the `n//2` resulting Bell pairs
straddles the middle cut, so the exact Schmidt rank there is `2**(n//2)` by construction
and `chi` below that must truncate. This is a designed truncation test, not a physics
circuit.

WHAT THIS DOES AND DOES NOT SHOW. It measures how far the truncated carrier's record
distribution moves away from an independent dense computation of the same distribution.
It is not a faithfulness claim about either one: both share this repository's schedule
lowering and mechanism selection, so they are not independent about that. See
`docs/FAITHFULNESS_PROTOCOL.md` §2. The comparison is `comparison_outcome_is_metric:
False` in the payload it comes from, and nothing here changes that.

MEASURED LIMITS (this script prints them; they were not assumed):

* Certified reach is n=4, not the `_RECORD_EVIDENCE_QUBIT_CAP = 8` the constant suggests.
  At n>=6 the dense oracle returns `full_positive_duration_coverage: False`, and it is
  neither the qubit cap nor compute -- the refusal takes 0.1s. With this circuit the
  Hadamard layer is dropped outright once it carries three or more simultaneous
  single-qubit gates, `reason: unsupported_one_qubit_gate_or_no_idle_window`, leaving
  `positive_duration_coverage_fraction = 2/3`. Serializing to one gate per tick does not
  rescue it and exposes the underlying rule: for a one-qubit gate the coverage ledger
  expects one row per (active, idle) qubit pair and the default selection plan supplies
  one, so a serialized n=6 covers 1 of 5 pairs and scores 1/7 overall. Either way,
  extending past n=4 needs a custom selection plan, which is a different piece of work.

* The curve is run noiseless on purpose. Under Lindblad noise the exact-bond residual is
  1.1e-3 -- five orders above the 1e-8 gate -- while the noiseless exact-bond residual is
  1.3e-15. So that residual is the finite-step error of the noise channel, not a carrier
  defect, and it is a floor under any noisy version of this curve. It cannot be refined
  away here: raising `microstep_count` to 2 already exceeds the 4096 branch cap at n=2,
  because `_apply_collapse_terms_to_branches` splits every branch once per Kraus operator
  per collapse term per substep.

* Exact branch enumeration under noise reaches n=2 at the default 4096 branch cap. n=3
  needs 65536 and takes ~19s; n=4 exceeds 65536.

Preconditions: CUDA, and the `ecs` environment.
"""

from __future__ import annotations

import argparse
import sys
import time

from error_coupling_simulator.frontend import (
    Axis1LocalLindbladContextSpec,
    CircuitBuilder,
    circuit_ir_to_substep_schedule,
)
from error_coupling_simulator.frontend import axis1_qt_mps_execution as qt
from error_coupling_simulator.frontend.axis1_record_evidence import (
    axis1_measurement_record_evidence_manifest,
)

DENSE_GATE = 1.0e-8


def emit(line: str = "") -> None:
    print(line, flush=True)


def build_schedule(n: int, *, gamma_per_ns: float):
    """n//2 Bell pairs, every one straddling the middle cut: exact rank 2**(n//2)."""

    if n % 2:
        raise ValueError(f"n must be even so the middle cut is well defined; got {n}")
    builder = CircuitBuilder(num_qubits=n)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=gamma_per_ns,
            gamma_1_per_ns=gamma_per_ns,
            gamma_readout_phi_per_ns=0.0,
        )
    )
    half = n // 2
    builder.h(tuple(range(half)))
    builder.tick()
    pairs: list[int] = []
    for i in range(half):
        pairs.extend((i, half + i))
    builder.cx(pairs)
    builder.tick()
    builder.measure(
        tuple(range(n)),
        key=tuple(f"m{i}" for i in range(n)),
        duration_ns=1.0e-6,
    )
    return circuit_ir_to_substep_schedule(builder.build())


def run_at_bond(n: int, *, chi: int, gamma_per_ns: float, max_branches: int) -> dict:
    schedule = build_schedule(n, gamma_per_ns=gamma_per_ns)
    started = time.perf_counter()
    try:
        run = qt.axis1_qt_mps_restricted_execution_manifest(
            schedule,
            max_bond=chi,
            max_branches=max_branches,
            dense_oracle_certification=True,
        )
    except Exception as exc:
        return {
            "error": f"{type(exc).__name__}: {exc}",
            "elapsed": time.perf_counter() - started,
        }
    execution = run["mps_execution"]
    ledger = execution.get("mps_truncation_ledger") or {}
    certification = run["dense_jointL_record_certification"]
    return {
        "elapsed": time.perf_counter() - started,
        "records": execution.get("record_count"),
        "maxdiff": certification.get("max_abs_probability_difference"),
        "cert_passed": certification.get("passed"),
        "discarded_sum": ledger.get("discarded_weight_sum"),
        "worst_cut": ledger.get("worst_cut_discarded_weight"),
        "exact_bond_sufficient": ledger.get("exact_bond_dimension_sufficient"),
    }


def report(label: str, out: dict) -> bool:
    if "error" in out:
        emit(f"  {label:<14s} {out['error']}   ({out['elapsed']:.1f}s)")
        return False
    emit(
        f"  {label:<14s} maxdiff={out['maxdiff']:.6e}  "
        f"discarded_sum={out['discarded_sum']:.6e}  "
        f"worst_cut={out['worst_cut']:.6e}  "
        f"cert={'PASS' if out['cert_passed'] else 'fail'}   ({out['elapsed']:.1f}s)"
    )
    return True


def curve(n: int, *, max_branches: int) -> int:
    exact_chi = 2 ** (n // 2)
    emit(f"[curve] n={n}, exact middle-cut rank {exact_chi}, noiseless")
    emit(f"[curve] dense-oracle certification gate is max|dp| <= {DENSE_GATE:g}")
    status = 0
    for chi in (1, 2, 4, 8, 16):
        if chi > exact_chi:
            break
        out = run_at_bond(n, chi=chi, gamma_per_ns=0.0, max_branches=max_branches)
        marker = "chi=%-2d%s" % (chi, "  (exact)" if chi == exact_chi else "")
        if not report(marker, out):
            status = 1
            continue
        if chi == exact_chi and not out["cert_passed"]:
            emit(
                "  FAIL: at the exact bond the carrier must reproduce the dense oracle; "
                "a residual here is not truncation"
            )
            status = 1
    emit(
        "  discarded_weight_sum accumulates over truncation events, so it is not a "
        "probability and may reach 1; read it as an upper proxy, not as the error"
    )
    return status


def noise_floor(max_branches: int) -> None:
    """The same comparison with the noise on, at the only size enumeration reaches."""

    emit("[floor] the noiseless run above is the control; this is why it is noiseless")
    for gamma, tag in ((0.0, "gamma=0    "), (1.0e-4, "gamma=1e-4 ")):
        out = run_at_bond(2, chi=2, gamma_per_ns=gamma, max_branches=max_branches)
        report(tag + "n=2", out)
    emit(
        "  a residual at exact bond with zero discarded weight is the noise finite step, "
        "not truncation and not a carrier defect"
    )


def walls(max_branches: int) -> None:
    emit("[wall] dense-oracle coverage versus n (noiseless)")
    for n in (2, 4, 6, 8):
        manifest = axis1_measurement_record_evidence_manifest(
            build_schedule(n, gamma_per_ns=0.0), device="cuda"
        )
        coverage = manifest["coverage"]
        emit(
            f"  n={n}  oracle_passed={manifest['passed']}  "
            f"full_coverage={coverage['full_positive_duration_coverage']}  "
            f"coverage_fraction="
            f"{coverage['positive_duration_coverage_fraction']:.4f}"
        )
    emit("[wall] exact branch enumeration under noise versus n")
    for n in (2, 4):
        out = run_at_bond(
            n, chi=2 ** (n // 2), gamma_per_ns=1.0e-4, max_branches=max_branches
        )
        state = out.get("error", f"ok in {out['elapsed']:.1f}s")
        emit(f"  n={n}  max_branches={max_branches}  {state}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--qubits",
        type=int,
        default=4,
        help="must be even; certified coverage currently reaches 4 (see module docstring)",
    )
    parser.add_argument("--max-branches", type=int, default=4096)
    parser.add_argument(
        "--skip-walls",
        action="store_true",
        help="skip the reach measurements and print only the curve",
    )
    args = parser.parse_args()

    import torch

    if not torch.cuda.is_available():
        emit("SKIP: the restricted QT/MPS route is GPU-only")
        return 0

    emit("truncation error versus bond dimension, against the registered dense oracle")
    emit("this certifies nothing; see the module docstring for the claim boundary")
    emit()
    status = curve(args.qubits, max_branches=args.max_branches)
    emit()
    noise_floor(args.max_branches)
    if not args.skip_walls:
        emit()
        walls(args.max_branches)
    return status


if __name__ == "__main__":
    sys.exit(main())
