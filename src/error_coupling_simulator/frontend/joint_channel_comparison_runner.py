from __future__ import annotations

"""Reproducible runner for the joint-channel comparison fixture."""

from dataclasses import dataclass
import argparse
import json
from pathlib import Path
from typing import Sequence

from .analog_schedule import SubstepSchedule, circuit_ir_to_substep_schedule
from .joint_channel_comparison import (
    JointChannelEvidenceResult,
    JointChannelFreezeResult,
    freeze_joint_channel_comparison_evidence,
    validate_joint_channel_comparison_freeze,
    write_joint_channel_comparison_evidence,
)
from .circuit_ir import CircuitBuilder


@dataclass(frozen=True)
class JointChannelComparisonRunnerResult:
    """Result from the reproducible joint-channel comparison fixture."""

    schedule: SubstepSchedule
    evidence: JointChannelEvidenceResult
    freeze: JointChannelFreezeResult | None


def build_joint_channel_comparison_schedule() -> SubstepSchedule:
    """Build the minimal compiler-generated schedule required by the comparison gate."""

    builder = CircuitBuilder(
        num_qubits=2,
        metadata={
            "fixture": "joint_channel_comparison",
            "encoded_distance_certified": False,
        },
    )
    builder.declare_static_zz_couplings(((0, 1),))
    builder.h(0)
    builder.tick()
    builder.cz((0, 1))
    return circuit_ir_to_substep_schedule(builder.build())


def run_joint_channel_comparison_fixture(
    out_dir: str | Path,
    *,
    device: str = "cuda",
    write_freeze: bool = True,
    refresh_freeze: bool = False,
) -> JointChannelComparisonRunnerResult:
    """Generate comparison evidence from the compiler/schedule frontend fixture."""

    schedule = build_joint_channel_comparison_schedule()
    evidence = write_joint_channel_comparison_evidence(schedule, out_dir, device=device)
    freeze = (
        freeze_joint_channel_comparison_evidence(
            evidence.joint_channel_comparison,
            overwrite=refresh_freeze,
        )
        if write_freeze
        else None
    )
    return JointChannelComparisonRunnerResult(
        schedule=schedule,
        evidence=evidence,
        freeze=freeze,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        default="outputs/simulator_validation/joint_channel_comparison",
        help="Directory for joint_channel_comparison.json and optional freeze manifest.",
    )
    parser.add_argument("--device", default="cuda", help="Torch device. The release lane is cuda.")
    parser.add_argument(
        "--no-freeze",
        action="store_true",
        help="Write comparison evidence without its freeze manifest.",
    )
    parser.add_argument(
        "--refresh-freeze",
        action="store_true",
        help="Overwrite the freeze manifest after an intentional evidence update.",
    )
    parser.add_argument(
        "--validate-freeze",
        type=Path,
        default=None,
        help="Validate an existing freeze manifest instead of generating evidence.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.validate_freeze is not None:
        validation = validate_joint_channel_comparison_freeze(args.validate_freeze)
        print(json.dumps(validation, indent=2, sort_keys=True))
        return 0

    result = run_joint_channel_comparison_fixture(
        args.out_dir,
        device=args.device,
        write_freeze=not args.no_freeze,
        refresh_freeze=bool(args.refresh_freeze),
    )
    summary = {
        "schema": (
            "error_coupling_simulator.frontend."
            "joint_channel_comparison_runner_summary.v1"
        ),
        "out_dir": str(result.evidence.out_dir),
        "joint_channel_comparison": str(result.evidence.joint_channel_comparison),
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
    "JointChannelComparisonRunnerResult",
    "build_joint_channel_comparison_schedule",
    "main",
    "run_joint_channel_comparison_fixture",
]
