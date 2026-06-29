from __future__ import annotations

"""Reproducible runner for the Axis-1 frontend G2 evidence fixture."""

from dataclasses import dataclass
import argparse
import json
from pathlib import Path
from typing import Sequence

from qec_twin.simulator.analog_schedule import SubstepSchedule, circuit_ir_to_substep_schedule
from qec_twin.simulator.axis1_bridge import (
    Axis1G2EvidenceResult,
    Axis1G2FreezeResult,
    freeze_axis1_g2_evidence,
    validate_axis1_g2_freeze,
    write_axis1_g2_evidence,
)
from qec_twin.simulator.circuit_ir import CircuitBuilder


@dataclass(frozen=True)
class Axis1G2RunnerResult:
    """Result from the reproducible Axis-1 frontend G2 fixture."""

    schedule: SubstepSchedule
    evidence: Axis1G2EvidenceResult
    freeze: Axis1G2FreezeResult | None


def build_axis1_g2_frontend_schedule() -> SubstepSchedule:
    """Build the minimal compiler-generated schedule required by the G2 gate."""

    builder = CircuitBuilder(
        num_qubits=2,
        metadata={"fixture": "axis1_g2_frontend", "encoded_distance_certified": False},
    )
    builder.declare_static_zz_couplings(((0, 1),))
    builder.h(0)
    builder.tick()
    builder.cz((0, 1))
    return circuit_ir_to_substep_schedule(builder.build())


def run_axis1_g2_frontend_fixture(
    out_dir: str | Path,
    *,
    device: str = "cuda",
    write_freeze: bool = True,
    refresh_freeze: bool = False,
) -> Axis1G2RunnerResult:
    """Generate `g2_jointL.json` from the compiler/schedule frontend fixture."""

    schedule = build_axis1_g2_frontend_schedule()
    evidence = write_axis1_g2_evidence(schedule, out_dir, device=device)
    freeze = (
        freeze_axis1_g2_evidence(evidence.g2_jointL, overwrite=refresh_freeze)
        if write_freeze
        else None
    )
    return Axis1G2RunnerResult(schedule=schedule, evidence=evidence, freeze=freeze)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        default="outputs/twin_validation/axis1_g2_frontend",
        help="Directory for g2_jointL.json and optional freeze manifest.",
    )
    parser.add_argument("--device", default="cuda", help="Torch device. The release lane is cuda.")
    parser.add_argument(
        "--no-freeze",
        action="store_true",
        help="Write g2_jointL.json without g2_jointL.freeze.json.",
    )
    parser.add_argument(
        "--refresh-freeze",
        action="store_true",
        help="Overwrite g2_jointL.freeze.json after an intentional evidence update.",
    )
    parser.add_argument(
        "--validate-freeze",
        type=Path,
        default=None,
        help="Validate an existing freeze manifest instead of generating evidence.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.validate_freeze is not None:
        validation = validate_axis1_g2_freeze(args.validate_freeze)
        print(json.dumps(validation, indent=2, sort_keys=True))
        return 0

    result = run_axis1_g2_frontend_fixture(
        args.out_dir,
        device=args.device,
        write_freeze=not args.no_freeze,
        refresh_freeze=bool(args.refresh_freeze),
    )
    summary = {
        "schema": "qec_twin.simulator.axis1_g2_runner_summary.v1",
        "out_dir": str(result.evidence.out_dir),
        "g2_jointL": str(result.evidence.g2_jointL),
        "content_hash": result.evidence.content_hash,
        "verdict": result.evidence.manifest["verdict"],
        "passed": bool(result.evidence.manifest["passed"]),
        "row_count": len(result.evidence.manifest["rows"]),
        "freeze": str(result.freeze.freeze_path) if result.freeze is not None else None,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "Axis1G2RunnerResult",
    "build_axis1_g2_frontend_schedule",
    "main",
    "run_axis1_g2_frontend_fixture",
]
