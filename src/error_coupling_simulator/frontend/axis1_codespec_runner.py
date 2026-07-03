from __future__ import annotations

"""Reproducible runner for compiler-generated Axis-1 CodeSpec record evidence."""

from dataclasses import dataclass
import argparse
import json
from pathlib import Path
from typing import Sequence

from .analog_schedule import (
    SubstepSchedule,
    compile_code_spec_to_substep_schedule,
)
from .axis1_record_evidence import (
    Axis1MeasurementRecordEvidenceResult,
    Axis1MeasurementRecordFreezeResult,
    freeze_axis1_measurement_record_evidence,
    validate_axis1_measurement_record_freeze,
    write_axis1_measurement_record_evidence,
)
from .code_spec import (
    CodeQubit,
    CodeSpec,
    LogicalObservableSpec,
    PauliTerm,
    StabilizerCheck,
)


@dataclass(frozen=True)
class Axis1CodeSpecRecordRunnerResult:
    """Result from the reproducible CodeSpec -> Axis-1 record evidence fixture."""

    spec: CodeSpec
    schedule: SubstepSchedule
    evidence: Axis1MeasurementRecordEvidenceResult
    freeze: Axis1MeasurementRecordFreezeResult | None


def build_axis1_codespec_frontend_spec(*, rounds: int = 2) -> CodeSpec:
    """Build a small mixed-basis CodeSpec fixture for Axis-1 frontend gates."""

    return CodeSpec(
        name="axis1_codespec_mixed_basis_frontend",
        num_qubits=5,
        data_qubits=(
            CodeQubit(0, "data", (0.0,)),
            CodeQubit(1, "data", (1.0,)),
            CodeQubit(2, "data", (2.0,)),
        ),
        ancilla_qubits=(
            CodeQubit(3, "ancilla", (0.0, 0.5)),
            CodeQubit(4, "ancilla", (1.0, 0.5)),
        ),
        checks=(
            StabilizerCheck("x0", 3, (PauliTerm(0, "X"),), (0.0, 0.5)),
            StabilizerCheck("z1", 4, (PauliTerm(1, "Z"),), (1.0, 0.5)),
        ),
        logical_observables=(
            LogicalObservableSpec("logical_z2", (PauliTerm(2, "Z"),), index=0),
        ),
        rounds=int(rounds),
        metadata={"fixture": "axis1_codespec_record_frontend", "encoded_distance_certified": False},
    )


def build_axis1_codespec_4q_frontend_spec(*, rounds: int = 2) -> CodeSpec:
    """Build the registered 4q coupled-teacher variant (prereg §1.1): 3 data + 1 X-check ancilla.

    Drops the ``z1`` Z-check (and ancilla 4) of the 5q fixture; keeps the ``x0`` X-check (X on
    data 0 via ancilla 3, the same superposition-bearing static-ZZ edge (0,3)) and the
    ``logical_z2`` Z-logical on data 2. Data qubit 1 sits in NO check and NO observable, so it
    gets no final measurement (grounded via ``record_layout.final_measurements``): finals =
    ``{q0: X, q2: Z}``. Hence measured bits ``M(R) = R`` (one ancilla read per round) ``+ 2``
    finals ``= R + 2`` (n_stab = 1). Registered as a SEPARATE curve — no silent fixture swap.
    """

    return CodeSpec(
        name="axis1_codespec_4q_frontend",
        num_qubits=4,
        data_qubits=(
            CodeQubit(0, "data", (0.0,)),
            CodeQubit(1, "data", (1.0,)),
            CodeQubit(2, "data", (2.0,)),
        ),
        ancilla_qubits=(
            CodeQubit(3, "ancilla", (0.0, 0.5)),
        ),
        checks=(
            StabilizerCheck("x0", 3, (PauliTerm(0, "X"),), (0.0, 0.5)),
        ),
        logical_observables=(
            LogicalObservableSpec("logical_z2", (PauliTerm(2, "Z"),), index=0),
        ),
        rounds=int(rounds),
        metadata={"fixture": "axis1_codespec_4q_frontend", "encoded_distance_certified": False},
    )


def build_axis1_codespec_frontend_schedule(*, rounds: int = 2) -> SubstepSchedule:
    """Compile the CodeSpec fixture into a sealed Axis-1 substep schedule."""

    return compile_code_spec_to_substep_schedule(
        build_axis1_codespec_frontend_spec(rounds=rounds)
    )


def run_axis1_codespec_record_fixture(
    out_dir: str | Path,
    *,
    rounds: int = 2,
    device: str = "cuda",
    write_freeze: bool = True,
    refresh_freeze: bool = False,
) -> Axis1CodeSpecRecordRunnerResult:
    """Generate Axis-1 record evidence from the compiler-generated CodeSpec fixture."""

    spec = build_axis1_codespec_frontend_spec(rounds=rounds)
    schedule = compile_code_spec_to_substep_schedule(spec)
    evidence = write_axis1_measurement_record_evidence(schedule, out_dir, device=device)
    freeze = (
        freeze_axis1_measurement_record_evidence(
            evidence.record_evidence,
            overwrite=refresh_freeze,
        )
        if write_freeze
        else None
    )
    return Axis1CodeSpecRecordRunnerResult(
        spec=spec,
        schedule=schedule,
        evidence=evidence,
        freeze=freeze,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        default="outputs/twin_validation/axis1_codespec_record_evidence",
        help="Directory for axis1_measurement_records.json and optional freeze manifest.",
    )
    parser.add_argument("--rounds", type=int, default=2, help="CodeSpec measurement rounds.")
    parser.add_argument("--device", default="cuda", help="Torch device. The release lane is cuda.")
    parser.add_argument(
        "--no-freeze",
        action="store_true",
        help="Write axis1_measurement_records.json without a freeze manifest.",
    )
    parser.add_argument(
        "--refresh-freeze",
        action="store_true",
        help="Overwrite the record freeze after an intentional evidence update.",
    )
    parser.add_argument(
        "--validate-freeze",
        type=Path,
        default=None,
        help="Validate an existing record freeze manifest instead of generating evidence.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.validate_freeze is not None:
        validation = validate_axis1_measurement_record_freeze(args.validate_freeze)
        print(json.dumps(validation, indent=2, sort_keys=True))
        return 0

    result = run_axis1_codespec_record_fixture(
        args.out_dir,
        rounds=int(args.rounds),
        device=args.device,
        write_freeze=not args.no_freeze,
        refresh_freeze=bool(args.refresh_freeze),
    )
    record = result.evidence.manifest["record_evidence"]
    coverage = result.evidence.manifest["coverage"]
    summary = {
        "schema": "qec_twin.simulator.axis1_codespec_record_runner_summary.v1",
        "out_dir": str(result.evidence.out_dir),
        "record_evidence": str(result.evidence.record_evidence),
        "content_hash": result.evidence.content_hash,
        "verdict": result.evidence.manifest["verdict"],
        "passed": bool(result.evidence.manifest["passed"]),
        "source_kind": result.evidence.manifest["source_kind"],
        "source_hash": result.evidence.manifest["source_hash"],
        "record_count": int(record["record_count"]),
        "measurement_key_count": len(record["measurement_keys"]),
        "applied_channel_count": int(record["applied_channel_count"]),
        "measurement_basis": record["measurement_basis"],
        "full_positive_duration_coverage": bool(
            coverage["full_positive_duration_coverage"]
        ),
        "freeze": str(result.freeze.freeze_path) if result.freeze is not None else None,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "Axis1CodeSpecRecordRunnerResult",
    "build_axis1_codespec_4q_frontend_spec",
    "build_axis1_codespec_frontend_schedule",
    "build_axis1_codespec_frontend_spec",
    "main",
    "run_axis1_codespec_record_fixture",
]
