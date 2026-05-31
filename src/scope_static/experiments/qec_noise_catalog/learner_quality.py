from __future__ import annotations

import argparse
from pathlib import Path

from scope_static.learner import run_sampled_quantum_error_quality_audit


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
    classification = result.get("mechanism_classification", {})
    if not isinstance(classification, dict):
        classification = {}
    prediction_source = result.get("prediction_source_audit", {})
    if not isinstance(prediction_source, dict):
        prediction_source = {}
    print(
        "PHYC3 no-leakage learner quantum-error quality complete\n"
        f"  decision={result.get('decision')}\n"
        f"  passed={bool(result.get('contract_passed'))}\n"
        f"  prediction_source={prediction_source.get('source_name', 'unknown')}\n"
        f"  learner_nmi={float(classification.get('normalized_mutual_info', 0.0)):.4f}\n"
        f"  mean_predicted_channel_distance={float(predicted.get('mean', 0.0)):.6f}\n"
        f"  output={output_dir}"
    )
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run PHYC3 no-leakage learner quantum-error quality audit.")
    parser.add_argument("--teacher-dir", type=Path, required=True)
    parser.add_argument("--prediction-dir", type=Path)
    parser.add_argument("--phyc2-dir", type=Path, help="Deprecated alias for --prediction-dir.")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    prediction_dir = args.prediction_dir if args.prediction_dir is not None else args.phyc2_dir
    if prediction_dir is None:
        parser.error("--prediction-dir is required")
    run_phyc3_sampled_quantum_error_quality(
        teacher_dir=args.teacher_dir,
        phyc2_dir=prediction_dir,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
