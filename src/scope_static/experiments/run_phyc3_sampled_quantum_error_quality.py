from __future__ import annotations

import argparse
from pathlib import Path

from scope_static.physical.sampled_quantum_error_quality import run_sampled_quantum_error_quality_audit


def run_phyc3_sampled_quantum_error_quality(
    *,
    teacher_dir: str | Path,
    phyc2_dir: str | Path,
    output_dir: str | Path,
) -> dict[str, object]:
    result = run_sampled_quantum_error_quality_audit(
        teacher_dir=teacher_dir,
        phyc2_dir=phyc2_dir,
        output_dir=output_dir,
    )
    quality = result.get("quality_summary", {})
    if not isinstance(quality, dict):
        quality = {}
    predicted = quality.get("predicted_channel_distance", {})
    if not isinstance(predicted, dict):
        predicted = {}
    print(
        "PHYC3 sampled quantum-error quality complete\n"
        f"  decision={result.get('decision')}\n"
        f"  passed={bool(result.get('contract_passed'))}\n"
        f"  mean_predicted_channel_distance={float(predicted.get('mean', 0.0)):.6f}\n"
        f"  output={output_dir}"
    )
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run PHYC3 sampled quantum-error quality audit.")
    parser.add_argument("--teacher-dir", type=Path, required=True)
    parser.add_argument("--phyc2-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    run_phyc3_sampled_quantum_error_quality(
        teacher_dir=args.teacher_dir,
        phyc2_dir=args.phyc2_dir,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
