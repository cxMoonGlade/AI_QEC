from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import yaml

from scope_static.experiments.qec_noise_catalog.config import load_s2d_physical_config, output_root_from_config
from scope_static.mechanism_observability import (
    GeneratorInvariantCalibrationBundle,
    build_generator_invariant_calibration,
)


DEFAULT_RUNS = [
    {"name": "phys9_setA", "purpose": "regression context for generator-invariant calibration"},
    {"name": "phys9_multicircuit_setB_balanced", "purpose": "balanced set_B invariant calibration target"},
    {"name": "phys9_multicircuit_setC_balanced", "purpose": "balanced set_C invariant calibration target"},
]
PRIMARY_RUNS = {"phys9_multicircuit_setB_balanced", "phys9_multicircuit_setC_balanced"}
ARTIFACT_NAMES = (
    "invariant_feature_manifest",
    "invariant_feature_table",
    "effective_rank_metrics",
    "generator_coordinate_statistics",
    "per_mechanism_generator_signatures",
    "pairwise_generator_margins",
    "circuit_residualization_audit",
    "edge_residualization_audit",
    "blockwise_decision_metrics",
    "mahalanobis_prototype_metrics",
    "invariant_ablation_metrics",
    "grouped_fold_predictions",
    "feature_block_results",
    "controls",
    "leakage_guardrail_audit",
    "features_schema_physics_visible",
    "audit_labels_schema_oracle_only",
)


def run_s2d10b_generator_invariant_calibration(
    config_path: str | Path | None = None,
    *,
    output_dir: str | Path | None = None,
    max_runs: int | None = None,
) -> dict[str, object]:
    physical_cfg = load_s2d_physical_config(config_path)
    cfg = _load_config(config_path)
    root = output_root_from_config(physical_cfg)
    default_source = root / "S2D.9_local_Pauli_Lindblad_observability"
    default_output = root / "S2D.10b_generator_invariant_calibration"
    source = Path(str(cfg.get("source_root", default_source)))
    output = Path(output_dir) if output_dir is not None else Path(str(cfg.get("output_dir", default_output)))
    output.mkdir(parents=True, exist_ok=True)

    source_metrics = _load_source_metrics(source)
    source_records = {str(record["name"]): dict(record) for record in source_metrics.get("records", []) if isinstance(record, dict)}
    runs = _enabled_runs(cfg)
    if max_runs is not None:
        runs = runs[: int(max_runs)]

    records = []
    for run_cfg in runs:
        run_name = str(run_cfg["name"])
        if run_name not in source_records:
            raise ValueError(f"S2D.10b source metrics do not contain run {run_name!r}")
        records.append(_run_one(output, source_records[run_name], run_cfg, cfg, source))

    result = {
        "schema": "scope_static_s2d10b_generator_invariant_calibration_v1",
        "stage": "S2D.10b_generator_invariant_calibration",
        "primary_object": "learner_visible_generator_scalar_invariants",
        "source_stage": source_metrics.get("stage"),
        "source_root": str(source),
        "output_dir": str(output),
        "run_order": [record["name"] for record in records],
        "records": records,
        "summary": _summary(records),
        "phase_summary": _phase_summary(records),
    }
    _write_artifacts(output, result)
    return result


def _run_one(output: Path, source_record: dict[str, object], run_cfg: dict[str, object], cfg: dict[str, object], source_root: Path) -> dict[str, object]:
    bundle = build_generator_invariant_calibration(
        source_record,
        seed=int(cfg.get("seed", 0)),
        permutation_repeats=int(cfg.get("permutation_repeats", 128)),
        eps=float(cfg.get("eps", 1e-9)),
    )
    record = {
        "name": str(run_cfg["name"]),
        "purpose": str(run_cfg.get("purpose", "")),
        "profile": str(source_record.get("profile", "")),
        "mechanism_set": str(source_record.get("mechanism_set", "")),
        "source_run": str(source_record.get("name", "")),
        "source_stage": "S2D.9_local_Pauli_Lindblad_observability",
        "source_root": str(source_root),
        "decision": bundle.decision,
        "invariant_feature_manifest": bundle.invariant_feature_manifest,
        "invariant_feature_table": bundle.invariant_feature_table,
        "effective_rank_metrics": bundle.effective_rank_metrics,
        "generator_coordinate_statistics": bundle.generator_coordinate_statistics,
        "per_mechanism_generator_signatures": bundle.per_mechanism_generator_signatures,
        "pairwise_generator_margins": bundle.pairwise_generator_margins,
        "circuit_residualization_audit": bundle.circuit_residualization_audit,
        "edge_residualization_audit": bundle.edge_residualization_audit,
        "blockwise_decision_metrics": bundle.blockwise_decision_metrics,
        "mahalanobis_prototype_metrics": bundle.mahalanobis_prototype_metrics,
        "invariant_ablation_metrics": bundle.invariant_ablation_metrics,
        "grouped_fold_predictions": bundle.grouped_fold_predictions,
        "feature_block_results": bundle.feature_block_results,
        "controls": bundle.controls,
        "leakage_guardrail_audit": bundle.leakage_guardrail_audit,
        "features_schema_physics_visible": bundle.features_schema_physics_visible,
        "audit_labels_schema_oracle_only": bundle.audit_labels_schema_oracle_only,
        "interpretation": _record_interpretation(bundle),
    }
    _write_run_artifacts(output / record["name"], record)
    return record


def _record_interpretation(bundle: GeneratorInvariantCalibrationBundle) -> str:
    passed = bool(bundle.invariant_ablation_metrics.get("run_success", {}).get("passed", False))
    primary = str(bundle.invariant_ablation_metrics.get("primary_block", "circuit_residualized_generator_coordinates_plus_invariants"))
    overall = bundle.feature_block_results.get(primary, {}).get("overall", {})
    balanced = float(overall.get("balanced_accuracy", 0.0)) if isinstance(overall, dict) else 0.0
    controls = bundle.controls
    gap = float(controls.get("real_minus_scrambled_balanced_accuracy", 0.0)) if isinstance(controls, dict) else 0.0
    if passed:
        return "scalar invariants support leakage-clean grouped RZZ-family recovery"
    if balanced >= 0.80 and gap >= 0.25:
        return "scalar invariants improve grouped recovery but miss at least one strict success criterion"
    if gap < 0.25:
        return "scalar invariant signal does not clearly beat scrambled control"
    return "scalar invariants are informative but not sufficient for full recovery"


def _summary(records: list[dict[str, object]]) -> dict[str, object]:
    primary = [record for record in records if record["name"] in PRIMARY_RUNS]
    return {
        "num_runs": int(len(records)),
        "num_primary_balanced_runs": int(len(primary)),
        "success": int(sum(1 for record in records if record["decision"] == "success")),
        "partial_invariant_signal": int(sum(1 for record in records if record["decision"] == "partial_invariant_signal")),
        "failure": int(sum(1 for record in records if record["decision"] == "failure")),
        "primary_balanced_success": bool(primary) and all(record["decision"] == "success" for record in primary),
    }


def _phase_summary(records: list[dict[str, object]]) -> dict[str, object]:
    primary = [record for record in records if record["name"] in PRIMARY_RUNS]
    primary_success = bool(primary) and all(record["decision"] == "success" for record in primary)
    primary_partial = bool(primary) and any(record["decision"] == "partial_invariant_signal" for record in primary)
    primary_failure = bool(primary) and all(record["decision"] == "failure" for record in primary)
    if primary_success:
        label = "generator_invariant_calibration_positive"
        conclusion = "Learner-visible scalar invariants resolve balanced setB/setC generator-space recovery."
        next_step = "promote scalar invariants into the physical generator learner representation"
    elif primary_partial:
        label = "generator_invariant_calibration_partial"
        conclusion = "Scalar invariants expose useful physics signal but do not fully close all grouped recovery criteria."
        next_step = "inspect residual class-specific errors and decide whether to use hierarchical invariant decisions"
    elif primary_failure:
        label = "generator_invariant_calibration_negative"
        conclusion = "Scalar invariants do not beat calibrated controls enough to explain the S2D.10 setB/setC gap."
        next_step = "return to nuisance estimation or stronger local characterization"
    else:
        label = "generator_invariant_calibration_not_frozen"
        conclusion = "S2D.10b requires balanced primary runs before freezing the phase."
        next_step = None
    return {
        "schema": "scope_static_s2d10b_phase_summary_v1",
        "stage": "S2D.10b_generator_invariant_calibration",
        "phase_label": label,
        "main_conclusion": conclusion,
        "primary_object": "learner_visible_generator_scalar_invariants",
        "no_new_probe_sampling": True,
        "next_recommended_step": next_step,
    }


def format_s2d10b_summary(result: dict[str, object]) -> str:
    lines = [
        "# S2D.10b Generator Invariant Calibration",
        "",
        "| run | decision | primary bal acc | macro F1 | min recall | real-scr bal gap | M8/M9 acc | Mahalanobis bal acc |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    primary_block = "circuit_residualized_generator_coordinates_plus_invariants"
    for record in result["records"]:
        primary = record["feature_block_results"].get(primary_block, {}).get("overall", {})
        pairwise = primary.get("pairwise", {}) if isinstance(primary, dict) else {}
        m8_m9 = pairwise.get("M8/M9", {}) if isinstance(pairwise, dict) else {}
        controls = record["controls"]
        maha = record["mahalanobis_prototype_metrics"]["variants"].get(primary_block, {}).get("real", {})
        lines.append(
            f"| {record['name']} | {record['decision']} | "
            f"{_fmt(primary.get('balanced_accuracy'))} | "
            f"{_fmt(primary.get('macro_F1'))} | "
            f"{_fmt(primary.get('min_class_recall'))} | "
            f"{_fmt(controls.get('real_minus_scrambled_balanced_accuracy'))} | "
            f"{_fmt(m8_m9.get('accuracy'))} | "
            f"{_fmt(maha.get('balanced_accuracy'))} |"
        )
    phase = result.get("phase_summary", {})
    if phase:
        lines.extend(
            [
                "",
                "## Phase Conclusion",
                "",
                f"- Label: `{phase.get('phase_label')}`",
                f"- Conclusion: {phase.get('main_conclusion')}",
                f"- Next: `{phase.get('next_recommended_step')}`",
            ]
        )
    lines.append("")
    return "\n".join(lines)


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


def _write_artifacts(output: Path, result: dict[str, object]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "metrics.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (output / "summary.md").write_text(format_s2d10b_summary(result))
    for artifact in ARTIFACT_NAMES:
        (output / f"{artifact}.json").write_text(json.dumps(_aggregate_artifact(result["records"], artifact), indent=2, sort_keys=True) + "\n")


def _write_run_artifacts(run_dir: Path, record: dict[str, object]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "metrics.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    (run_dir / "summary.md").write_text(format_s2d10b_summary({"records": [record], "phase_summary": {}}))
    for artifact in ARTIFACT_NAMES:
        (run_dir / f"{artifact}.json").write_text(json.dumps(record[artifact], indent=2, sort_keys=True) + "\n")


def _aggregate_artifact(records: list[dict[str, object]], artifact: str) -> dict[str, object]:
    return {
        "schema": f"scope_static_s2d10b_{artifact}_aggregate_v1",
        "runs": {str(record["name"]): record.get(artifact, {}) for record in records},
    }


def _load_source_metrics(source: Path) -> dict[str, object]:
    path = source / "metrics.json"
    if not path.exists():
        raise FileNotFoundError(f"S2D.10b requires existing S2D.9 metrics at {path}")
    data = json.loads(path.read_text())
    if not isinstance(data, dict) or "records" not in data:
        raise ValueError(f"{path} is not an S2D.9 metrics bundle")
    return data


def _enabled_runs(cfg: dict[str, object]) -> list[dict[str, object]]:
    raw = cfg.get("runs", DEFAULT_RUNS)
    if not isinstance(raw, list):
        raise ValueError("s2d10b_generator_invariant_calibration.runs must be a list")
    return [dict(item) for item in raw if isinstance(item, dict) and bool(item.get("enabled", True))]


def _load_config(config_path: str | Path | None) -> dict[str, object]:
    if config_path is None:
        return {"runs": DEFAULT_RUNS}
    data = yaml.safe_load(Path(config_path).read_text())
    if not isinstance(data, dict):
        raise ValueError("S2D.10b config must be a mapping")
    section = data.get("s2d10b_generator_invariant_calibration", {})
    if section is None:
        section = {}
    if not isinstance(section, dict):
        raise ValueError("s2d10b_generator_invariant_calibration config must be a mapping")
    result = dict(section)
    result.setdefault("runs", DEFAULT_RUNS)
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run S2D.10b generator invariant calibration.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--max-runs", type=int, default=None)
    args = parser.parse_args(argv)
    result = run_s2d10b_generator_invariant_calibration(args.config, output_dir=args.output_dir, max_runs=args.max_runs)
    print(
        "S2D.10b generator invariant calibration complete\n"
        f"  runs={result['run_order']}\n"
        f"  output={result['output_dir']}\n"
        f"  summary={result['summary']}"
    )


if __name__ == "__main__":
    main()
