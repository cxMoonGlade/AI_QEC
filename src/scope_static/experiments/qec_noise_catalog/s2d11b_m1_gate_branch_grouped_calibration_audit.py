from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import yaml

from scope_static.experiments.qec_noise_catalog.config import load_s2d_physical_config, output_root_from_config
from scope_static.mechanism_observability import run_m1_gate_calibration_audit


ARTIFACT_NAMES = (
    "m1_false_negative_audit",
    "m1_grouped_fold_breakdown",
    "m1_invariant_snr_audit",
    "m1_pairwise_margin_report",
    "m1_dense_vs_compact_feature_audit",
    "m1_calibration_thresholds_by_fold",
    "m1_soft_rule_ablation",
    "m1_vs_m6_m7_m10_tradeoff",
    "m1_vs_m7_m8_m12_tradeoff",
    "gate_neighbor_recall_report",
    "error_type_taxonomy",
    "error_type_metrics",
    "mechanism_metrics_by_error_type",
    "calibration_variant_metrics",
    "leakage_guardrail_audit",
)


def run_s2d11b_m1_gate_branch_grouped_calibration_audit(
    config_path: str | Path | None = None,
    *,
    output_dir: str | Path | None = None,
) -> dict[str, object]:
    physical_cfg = load_s2d_physical_config(config_path)
    cfg = _load_config(config_path)
    root = output_root_from_config(physical_cfg)
    default_source = root / "S2D.11_typed_SPAM_gate_invariant_learner"
    default_output = root / "S2D.11b_M1_gate_branch_grouped_calibration_audit"
    source = Path(str(cfg.get("source_root", default_source)))
    output = Path(output_dir) if output_dir is not None else Path(str(cfg.get("output_dir", default_output)))
    output.mkdir(parents=True, exist_ok=True)
    result = run_m1_gate_calibration_audit(
        source,
        seed=int(cfg.get("seed", 0)),
        run_two_stage_if_soft_fails=bool(cfg.get("run_two_stage_if_soft_fails", True)),
    )
    result = {**result, "output_dir": str(output)}
    _write_artifacts(output, result)
    return result


def format_s2d11b_summary(result: dict[str, object]) -> str:
    variants = result.get("calibration_variant_metrics", {})
    lines = [
        "# S2D.11b M1 Gate-Branch Grouped Calibration Audit",
        "",
        f"- Source: `{result.get('source_run_dir')}`",
        f"- Best variant: `{result.get('best_variant')}`",
        f"- Passed: `{str(bool(result.get('primary_verdict', {}).get('passed', False))).lower()}`",
        "",
        "| variant | status | bal acc | macro F1 | M1 recall | M7 RXX/RYY recall | M9 relaxation recall | M17 prep/reset recall |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, row in variants.items():
        if isinstance(row, dict) and row.get("skipped", False):
            lines.append(
                f"| {name} | skipped: {row.get('skip_reason', '')} | "
                "NA | NA | NA | NA | NA | NA |"
            )
            continue
        overall = row.get("overall", {}) if isinstance(row, dict) else {}
        recalls = overall.get("per_class_recall", {}) if isinstance(overall, dict) else {}
        lines.append(
            f"| {name} | "
            "ran | "
            f"{_fmt(overall.get('balanced_accuracy'))} | "
            f"{_fmt(overall.get('macro_F1'))} | "
            f"{_fmt(recalls.get('M1'))} | "
            f"{_fmt(recalls.get('M7'))} | "
            f"{_fmt(recalls.get('M9'))} | "
            f"{_fmt(recalls.get('M17'))} |"
        )
    verdict = result.get("primary_verdict", {})
    best = str(result.get("best_variant", ""))
    type_metrics = (
        result.get("error_type_metrics", {})
        .get("variants", {})
        .get(best, {})
        .get("overall", {})
    )
    type_recalls = type_metrics.get("per_class_recall", {}) if isinstance(type_metrics, dict) else {}
    if type_recalls:
        lines.extend(
            [
                "",
                "## Error Type Split",
                "",
                "| error type | recall | support |",
                "| --- | ---: | ---: |",
            ]
        )
        support = type_metrics.get("support", {})
        for kind in ("gate", "readout", "prep_reset"):
            lines.append(f"| {kind} | {_fmt(type_recalls.get(kind))} | {support.get(kind, 0)} |")
    lines.extend(
        [
            "",
            "## Verdict Checks",
            "",
            *[f"- `{name}`: `{str(bool(value)).lower()}`" for name, value in verdict.get("checks", {}).items()],
            "",
            "## Interpretation",
            "",
            str(result.get("summary", {}).get("interpretation", "")),
            "",
        ]
    )
    return "\n".join(lines)


def _write_artifacts(output: Path, result: dict[str, object]) -> None:
    (output / "metrics.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (output / "summary.md").write_text(format_s2d11b_summary(result))
    for name in ARTIFACT_NAMES:
        (output / f"{name}.json").write_text(json.dumps(result.get(name, {}), indent=2, sort_keys=True) + "\n")


def _load_config(config_path: str | Path | None) -> dict[str, object]:
    if config_path is None:
        return {}
    data = yaml.safe_load(Path(config_path).read_text())
    if not isinstance(data, dict):
        raise ValueError("S2D.11b config must be a mapping")
    section = data.get("s2d11b_m1_gate_branch_grouped_calibration_audit", {})
    if section is None:
        section = {}
    if not isinstance(section, dict):
        raise ValueError("s2d11b_m1_gate_branch_grouped_calibration_audit config must be a mapping")
    return dict(section)


def _fmt(value: object) -> str:
    if value is None:
        return "NA"
    try:
        current = float(value)
    except (TypeError, ValueError):
        return str(value)
    if not np.isfinite(current):
        return "inf"
    return f"{current:.4f}"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run S2D.11b M1 gate-branch grouped calibration audit.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    result = run_s2d11b_m1_gate_branch_grouped_calibration_audit(args.config, output_dir=args.output_dir)
    print(
        "S2D.11b M1 gate-branch grouped calibration audit complete\n"
        f"  output={result['output_dir']}\n"
        f"  best={result['best_variant']}\n"
        f"  passed={result['primary_verdict']['passed']}"
    )


if __name__ == "__main__":
    main()
