from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import yaml

from scope_static.experiments.s2d_config import load_s2d_physical_config, output_root_from_config
from scope_static.physical.generator_space_calibration import GeneratorCalibrationBundle, build_generator_space_calibration


DEFAULT_RUNS = [
    {"name": "phys9_setA", "purpose": "regression context for generator-space calibration"},
    {"name": "phys9_multicircuit_setB_balanced", "purpose": "balanced set_B calibration target"},
    {"name": "phys9_multicircuit_setC_balanced", "purpose": "balanced set_C calibration target"},
]
PRIMARY_RUNS = {"phys9_multicircuit_setB_balanced", "phys9_multicircuit_setC_balanced"}
ARTIFACT_NAMES = (
    "effective_rank_metrics",
    "generator_coordinate_statistics",
    "per_mechanism_generator_signatures",
    "pairwise_generator_margins",
    "circuit_residualization_audit",
    "edge_residualization_audit",
    "blockwise_decision_metrics",
    "mahalanobis_prototype_metrics",
    "whitening_ablation_metrics",
    "grouped_fold_predictions",
    "feature_block_results",
    "controls",
    "confusion_matrix_by_stage",
    "leakage_guardrail_audit",
)


def run_s2d10_generator_space_calibration(
    config_path: str | Path | None = None,
    *,
    output_dir: str | Path | None = None,
    max_runs: int | None = None,
) -> dict[str, object]:
    physical_cfg = load_s2d_physical_config(config_path)
    cfg = _load_config(config_path)
    root = output_root_from_config(physical_cfg)
    default_source = root / "S2D.9_local_Pauli_Lindblad_observability"
    default_output = root / "S2D.10_generator_space_calibration_and_nuisance_geometry"
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
            raise ValueError(f"S2D.10 source metrics do not contain run {run_name!r}")
        records.append(_run_one(output, source_records[run_name], run_cfg, cfg, source))

    result = {
        "schema": "scope_static_s2d10_generator_space_calibration_v1",
        "stage": "S2D.10_generator_space_calibration_and_nuisance_geometry",
        "primary_object": "generator_space_calibration_effective_rank_nuisance_decision_geometry",
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
    bundle = build_generator_space_calibration(
        source_record,
        seed=int(cfg.get("seed", 0)),
        permutation_repeats=int(cfg.get("permutation_repeats", 128)),
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
        "effective_rank_metrics": bundle.effective_rank_metrics,
        "generator_coordinate_statistics": bundle.generator_coordinate_statistics,
        "per_mechanism_generator_signatures": bundle.per_mechanism_generator_signatures,
        "pairwise_generator_margins": bundle.pairwise_generator_margins,
        "circuit_residualization_audit": bundle.circuit_residualization_audit,
        "edge_residualization_audit": bundle.edge_residualization_audit,
        "blockwise_decision_metrics": bundle.blockwise_decision_metrics,
        "mahalanobis_prototype_metrics": bundle.mahalanobis_prototype_metrics,
        "whitening_ablation_metrics": bundle.whitening_ablation_metrics,
        "grouped_fold_predictions": bundle.grouped_fold_predictions,
        "feature_block_results": bundle.feature_block_results,
        "controls": bundle.controls,
        "confusion_matrix_by_stage": bundle.confusion_matrix_by_stage,
        "leakage_guardrail_audit": bundle.leakage_guardrail_audit,
        "interpretation": _record_interpretation(bundle),
    }
    _write_run_artifacts(output / record["name"], record)
    return record


def _record_interpretation(bundle: GeneratorCalibrationBundle) -> str:
    whitening_pass = bool(bundle.whitening_ablation_metrics.get("run_success", {}).get("passed", False))
    stage1 = float(
        bundle.blockwise_decision_metrics.get("variants", {})
        .get("circuit_residualized_coordinates", {})
        .get("stage1_block_accuracy", 0.0)
    )
    control_gap = float(bundle.controls.get("real_minus_scrambled_balanced_accuracy", 0.0)) if bundle.controls else 0.0
    if whitening_pass and stage1 >= 0.80 and control_gap >= 0.25:
        return "generator-space calibration supports stable transferable RZZ-family recovery"
    if stage1 >= 0.80 and not whitening_pass:
        return "blockwise physics separation is stronger than flat grouped mechanism recovery"
    if control_gap < 0.25:
        return "generator-space decision signal remains close to scrambled control under grouped transfer"
    return "generator-space calibration is inconclusive and needs pairwise inspection"


def _summary(records: list[dict[str, object]]) -> dict[str, object]:
    primary = [record for record in records if record["name"] in PRIMARY_RUNS]
    return {
        "num_runs": int(len(records)),
        "num_primary_balanced_runs": int(len(primary)),
        "success": int(sum(1 for record in records if record["decision"] == "success")),
        "partial_blockwise_or_geometry": int(sum(1 for record in records if record["decision"] == "partial_blockwise_or_geometry")),
        "failure": int(sum(1 for record in records if record["decision"] == "failure")),
        "primary_balanced_success": bool(primary) and all(record["decision"] == "success" for record in primary),
    }


def _phase_summary(records: list[dict[str, object]]) -> dict[str, object]:
    primary = [record for record in records if record["name"] in PRIMARY_RUNS]
    primary_success = bool(primary) and all(record["decision"] == "success" for record in primary)
    primary_partial = bool(primary) and any(record["decision"] == "partial_blockwise_or_geometry" for record in primary)
    primary_failure = bool(primary) and all(record["decision"] == "failure" for record in primary)
    if primary_success:
        label = "generator_space_calibration_positive"
        conclusion = "Generator-space calibration resolves both balanced primary runs after nuisance/metric corrections."
        next_step = "freeze calibrated generator-space recovery and use hierarchical generator decisions"
    elif primary_partial:
        label = "generator_space_calibration_partial"
        conclusion = "Generator coordinates contain useful blockwise or calibrated signal, but flat grouped recovery is incomplete."
        next_step = "prefer hierarchical generator-space decisions; inspect residual pair-specific margins"
    elif primary_failure:
        label = "generator_space_calibration_negative"
        conclusion = "Full rank persists, but effective margins/control gaps remain too weak after calibration."
        next_step = "treat current local tomography as algebraically observable but statistically unstable for setB/setC"
    else:
        label = "generator_space_calibration_not_frozen"
        conclusion = "S2D.10 requires balanced primary runs before freezing the phase."
        next_step = None
    return {
        "schema": "scope_static_s2d10_phase_summary_v1",
        "stage": "S2D.10_generator_space_calibration_and_nuisance_geometry",
        "phase_label": label,
        "main_conclusion": conclusion,
        "primary_object": "effective_rank_per_generator_snr_residualization_and_decision_geometry",
        "no_new_probe_sampling": True,
        "next_recommended_step": next_step,
    }


def format_s2d10_summary(result: dict[str, object]) -> str:
    lines = [
        "# S2D.10 Generator-Space Calibration And Nuisance Geometry",
        "",
        "| run | decision | J rank | J cond | stage1 block acc | primary bal acc | real-scr bal gap | Mahalanobis bal acc |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for record in result["records"]:
        rank = record["effective_rank_metrics"]["response_jacobian"]
        block = record["blockwise_decision_metrics"]["variants"].get("circuit_residualized_coordinates", {})
        primary = record["feature_block_results"].get("circuit_residualized_coordinates", {}).get("overall", {})
        controls = record["controls"]
        maha = record["mahalanobis_prototype_metrics"]["variants"].get("circuit_residualized_coordinates", {}).get("real", {})
        lines.append(
            f"| {record['name']} | {record['decision']} | "
            f"{int(rank.get('rank', 0))} | "
            f"{_fmt(rank.get('condition_number'))} | "
            f"{_fmt(block.get('stage1_block_accuracy'))} | "
            f"{_fmt(primary.get('balanced_accuracy'))} | "
            f"{_fmt(controls.get('real_minus_scrambled_balanced_accuracy'))} | "
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
    (output / "summary.md").write_text(format_s2d10_summary(result))
    for artifact in ARTIFACT_NAMES:
        (output / f"{artifact}.json").write_text(json.dumps(_aggregate_artifact(result["records"], artifact), indent=2, sort_keys=True) + "\n")


def _write_run_artifacts(run_dir: Path, record: dict[str, object]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "metrics.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    (run_dir / "summary.md").write_text(format_s2d10_summary({"records": [record], "phase_summary": {}}))
    for artifact in ARTIFACT_NAMES:
        (run_dir / f"{artifact}.json").write_text(json.dumps(record[artifact], indent=2, sort_keys=True) + "\n")


def _aggregate_artifact(records: list[dict[str, object]], artifact: str) -> dict[str, object]:
    return {
        "schema": f"scope_static_s2d10_{artifact}_aggregate_v1",
        "runs": {str(record["name"]): record.get(artifact, {}) for record in records},
    }


def _load_source_metrics(source: Path) -> dict[str, object]:
    path = source / "metrics.json"
    if not path.exists():
        raise FileNotFoundError(f"S2D.10 requires existing S2D.9 metrics at {path}")
    data = json.loads(path.read_text())
    if not isinstance(data, dict) or "records" not in data:
        raise ValueError(f"{path} is not an S2D.9 metrics bundle")
    return data


def _enabled_runs(cfg: dict[str, object]) -> list[dict[str, object]]:
    raw = cfg.get("runs", DEFAULT_RUNS)
    if not isinstance(raw, list):
        raise ValueError("s2d10_generator_space_calibration.runs must be a list")
    return [dict(item) for item in raw if isinstance(item, dict) and bool(item.get("enabled", True))]


def _load_config(config_path: str | Path | None) -> dict[str, object]:
    if config_path is None:
        return {"runs": DEFAULT_RUNS}
    data = yaml.safe_load(Path(config_path).read_text())
    if not isinstance(data, dict):
        raise ValueError("S2D.10 config must be a mapping")
    section = data.get("s2d10_generator_space_calibration", {})
    if section is None:
        section = {}
    if not isinstance(section, dict):
        raise ValueError("s2d10_generator_space_calibration config must be a mapping")
    result = dict(section)
    result.setdefault("runs", DEFAULT_RUNS)
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run S2D.10 generator-space calibration and nuisance geometry audit.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--max-runs", type=int, default=None)
    args = parser.parse_args(argv)
    result = run_s2d10_generator_space_calibration(args.config, output_dir=args.output_dir, max_runs=args.max_runs)
    print(
        "S2D.10 generator-space calibration complete\n"
        f"  runs={result['run_order']}\n"
        f"  output={result['output_dir']}\n"
        f"  summary={result['summary']}"
    )


if __name__ == "__main__":
    main()
