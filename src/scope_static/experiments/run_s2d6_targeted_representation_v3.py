from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
import yaml

from scope_static.experiments.s2d_config import load_s2d_physical_config, output_root_from_config
from scope_static.physical.local_inverse import run_physical_local_inverse_discovery
from scope_static.physical.separability import run_oracle_separability_audit
from scope_static.physical.targeted_v3 import evaluate_targeted_v3_methods, typed_feature_manifest
from scope_static.physical.teacher import generate_physical_teacher_dataset


DEFAULT_RUNS: list[dict[str, object]] = [
    {
        "name": "phys9_multicircuit_setB_balanced",
        "profile": "phys9_multicircuit_setB_balanced",
        "mechanism_set": "set_B",
        "purpose": "balanced set_B primary v3 target",
    },
    {
        "name": "phys9_multicircuit_setC_balanced",
        "profile": "phys9_multicircuit_setC_balanced",
        "mechanism_set": "set_C",
        "purpose": "balanced set_C primary v3 target",
    },
    {
        "name": "phys9_setA",
        "profile": "phys9_chain",
        "mechanism_set": "set_A",
        "purpose": "regression sanity profile",
    },
]


def run_s2d6_targeted_representation_v3(
    config_path: str | Path | None = None,
    *,
    output_dir: str | Path | None = None,
    max_runs: int | None = None,
) -> dict[str, object]:
    physical_cfg = load_s2d_physical_config(config_path)
    cfg = _load_config(config_path)
    root = output_root_from_config(physical_cfg)
    output = Path(output_dir) if output_dir is not None else Path(str(cfg.get("output_dir", root / "S2D.6_targeted_representation_v3")))
    output.mkdir(parents=True, exist_ok=True)
    runs = _enabled_runs(cfg)
    if max_runs is not None:
        runs = runs[: int(max_runs)]

    records = [_run_one(output, physical_cfg, cfg, run_cfg) for run_cfg in runs]
    result = {
        "schema": "scope_static_s2d6_targeted_representation_v3_v1",
        "stage": "S2D.6_targeted_representation_v3",
        "output_dir": str(output),
        "run_order": [record["name"] for record in records],
        "records": records,
        "summary": _summary(records),
    }
    (output / "metrics.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (output / "summary.md").write_text(format_s2d6_summary(result))
    (output / "typed_feature_manifest.json").write_text(json.dumps(typed_feature_manifest(), indent=2, sort_keys=True) + "\n")
    (output / "feature_block_ablation.json").write_text(json.dumps(_feature_block_ablation(records), indent=2, sort_keys=True) + "\n")
    (output / "rzz_family_confusion_audit.json").write_text(json.dumps(_aggregate_audit(records, "rzz_family_confusion_audit"), indent=2, sort_keys=True) + "\n")
    (output / "readout_split_audit.json").write_text(json.dumps(_aggregate_audit(records, "readout_split_audit"), indent=2, sort_keys=True) + "\n")
    (output / "balanced_profile_results.json").write_text(json.dumps(_balanced_profile_results(records), indent=2, sort_keys=True) + "\n")
    return result


def _run_one(output: Path, physical_cfg: dict[str, object], cfg: dict[str, object], run_cfg: dict[str, object]) -> dict[str, object]:
    run_dir = output / str(run_cfg["name"])
    run_dir.mkdir(parents=True, exist_ok=True)
    merged = dict(physical_cfg)
    merged.update({key: value for key, value in run_cfg.items() if key not in {"name", "purpose", "enabled"}})
    merged.update(dict(cfg.get("physical_overrides", {})))
    teacher_dir = run_dir / "S2D_PHYS1_teacher"
    sep_dir = run_dir / "S2D_PHYS2_oracle_separability"
    local_dir = run_dir / "S2D_PHYS3_local_inverse"

    teacher = generate_physical_teacher_dataset(merged, output_dir=teacher_dir, preflight_dir=run_dir / "S2D_PHYS0_preflight")
    separability = run_oracle_separability_audit(
        teacher_dir=teacher_dir,
        output_dir=sep_dir,
        paper_informed=bool(merged.get("paper_informed_ptm_features", True)),
    )
    local = run_physical_local_inverse_discovery(
        teacher_dir=teacher_dir,
        separability_dir=sep_dir,
        output_dir=local_dir,
        config={
            **merged,
            "num_clusters": len(separability["oracle_label_names"]),
            "bootstrap_replicates": int(cfg.get("bootstrap_replicates", 16)),
            "random_baseline_trials": int(cfg.get("random_baseline_trials", 64)),
        },
    )
    records = _load_mechanism_records(teacher_dir / "oracle_mechanisms.json")
    observations, probe_names = _load_observations(teacher_dir / "observations.npz")
    hidden, label_names = _encode_labels([str(record["oracle_label"]) for record in records])
    comparisons = {str(item["comparison"]): [int(value) for value in item["labels"]] for item in local["comparisons"]}  # type: ignore[index]
    targeted = evaluate_targeted_v3_methods(
        records,
        observations,
        probe_names,
        hidden,
        label_names,
        comparison_labels={
            "physical_local_inverse_probability": comparisons["physical_local_inverse_probability"],
            **({"physical_local_inverse_probability_v2": comparisons["physical_local_inverse_probability_v2"]} if "physical_local_inverse_probability_v2" in comparisons else {}),
            "direct_S_alpha_assignment": comparisons["direct_S_alpha_assignment"],
            "oracle_fingerprint_upper_bound": comparisons["oracle_fingerprint_upper_bound"],
        },
    )
    decision = _run_decision(targeted)
    record = {
        "name": str(run_cfg["name"]),
        "purpose": str(run_cfg.get("purpose", "")),
        "profile": str(merged.get("profile")),
        "mechanism_set": str(merged.get("mechanism_set")),
        "num_qubits": int(teacher.get("num_qubits", merged.get("num_qubits", 0))),
        "shots": int(merged.get("shots", 0)),
        "decision": decision,
        "teacher": {
            "mechanism_counts": teacher.get("mechanism_counts", {}),
            "num_circuit_batches": teacher.get("num_circuit_batches", 1),
            "balanced_min_instances_per_mechanism": teacher.get("balanced_min_instances_per_mechanism"),
        },
        "PHYS2": {
            "ari": separability.get("ari"),
            "nmi": separability.get("nmi"),
            "active_clusters": separability.get("active_clusters"),
            "separability_gate": separability.get("separability_gate"),
        },
        "PHYS3": {
            "v1": local.get("main_result"),
            "v2": local.get("physical_local_inverse_probability_v2_result"),
            "direct_Salpha": local.get("direct_S_alpha_result"),
            "oracle": local.get("oracle_fingerprint_upper_bound"),
        },
        "targeted_audit_deltas": _targeted_audit_deltas(targeted),
        "targeted_v3": targeted,
    }
    (run_dir / "metrics.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    (run_dir / "feature_block_ablation.json").write_text(json.dumps(targeted["methods"], indent=2, sort_keys=True) + "\n")
    (run_dir / "rzz_family_confusion_audit.json").write_text(json.dumps(targeted["rzz_family_confusion_audit"], indent=2, sort_keys=True) + "\n")
    (run_dir / "readout_split_audit.json").write_text(json.dumps(targeted["readout_split_audit"], indent=2, sort_keys=True) + "\n")
    (run_dir / "summary.md").write_text(format_run_summary(record))
    return record


def _run_decision(targeted: dict[str, object]) -> str:
    methods = {str(item["method"]): item for item in targeted["methods"]}  # type: ignore[index]
    v1 = methods.get("v1_physical_local_inverse_probability", {})
    v2 = methods.get("v2_physical_local_inverse_probability_v2", {})
    v3c = methods.get("v3c_physical_local_inverse_probability_v3_typed", {})
    best_baseline_ari = max(float(v1.get("ari", 0.0)), float(v2.get("ari", 0.0)))
    best_baseline_nmi = max(float(v1.get("nmi", 0.0)), float(v2.get("nmi", 0.0)))
    v3_ari = float(v3c.get("ari", 0.0))
    v3_nmi = float(v3c.get("nmi", 0.0))
    audits = _targeted_audit_deltas(targeted)
    rzz_helped = bool(audits["rzz_merge_nonworse"]) and bool(audits["rzz_split_nonworse"])
    readout_helped = bool(audits["readout_split_nonworse"])
    improved = v3_ari > best_baseline_ari + 0.02 or v3_nmi > best_baseline_nmi + 0.02
    if v3_ari >= 0.80 and v3_nmi >= 0.80 and rzz_helped and readout_helped:
        return "success"
    if improved and (rzz_helped or readout_helped):
        return "partial_improvement"
    if readout_helped:
        return "partial_readout_fixed"
    return "failure"


def _targeted_audit_deltas(targeted: dict[str, object]) -> dict[str, object]:
    rzz = targeted.get("rzz_family_confusion_audit", {})
    readout = targeted.get("readout_split_audit", {})
    rzz_methods = rzz if isinstance(rzz, dict) else {}
    readout_methods = readout.get("methods", {}) if isinstance(readout, dict) else {}
    baseline_names = ["v1_physical_local_inverse_probability", "v2_physical_local_inverse_probability_v2"]
    v3_name = "v3c_physical_local_inverse_probability_v3_typed"
    baseline_rzz_merge = min(int(rzz_methods.get(name, {}).get("merge_count", 10_000)) for name in baseline_names)
    baseline_rzz_split = min(int(rzz_methods.get(name, {}).get("split_count", 10_000)) for name in baseline_names)
    v3_rzz_merge = int(rzz_methods.get(v3_name, {}).get("merge_count", 10_000))
    v3_rzz_split = int(rzz_methods.get(v3_name, {}).get("split_count", 10_000))
    baseline_readout_split = min(int(readout_methods.get(name, {}).get("M5_split_count", 10_000)) for name in baseline_names)
    v3_readout_split = int(readout_methods.get(v3_name, {}).get("M5_split_count", 10_000))
    return {
        "baseline_best_rzz_merge_count": baseline_rzz_merge,
        "v3c_rzz_merge_count": v3_rzz_merge,
        "rzz_merge_nonworse": v3_rzz_merge <= baseline_rzz_merge,
        "baseline_best_rzz_split_count": baseline_rzz_split,
        "v3c_rzz_split_count": v3_rzz_split,
        "rzz_split_nonworse": v3_rzz_split <= baseline_rzz_split,
        "baseline_best_M5_split_count": baseline_readout_split,
        "v3c_M5_split_count": v3_readout_split,
        "readout_split_nonworse": v3_readout_split <= baseline_readout_split,
    }


def _summary(records: list[dict[str, object]]) -> dict[str, object]:
    primary = [record for record in records if "balanced" in str(record.get("profile", ""))]
    return {
        "num_runs": len(records),
        "num_primary_balanced_runs": len(primary),
        "success": sum(1 for record in records if record["decision"] == "success"),
        "partial_improvement": sum(1 for record in records if record["decision"] == "partial_improvement"),
        "partial_readout_fixed": sum(1 for record in records if record["decision"] == "partial_readout_fixed"),
        "failure": sum(1 for record in records if record["decision"] == "failure"),
        "primary_balanced_success": all(record["decision"] == "success" for record in primary) if primary else False,
    }


def format_s2d6_summary(result: dict[str, object]) -> str:
    lines = [
        "# S2D.6 Targeted Representation v3",
        "",
        "| run | profile | decision | v1 ARI/NMI | v2 ARI/NMI | v3c ARI/NMI | readout split v1/v3c | RZZ merge v1/v3c |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for record in result["records"]:  # type: ignore[index]
        methods = {str(item["method"]): item for item in record["targeted_v3"]["methods"]}
        v1 = methods["v1_physical_local_inverse_probability"]
        v2 = methods["v2_physical_local_inverse_probability_v2"]
        v3c = methods["v3c_physical_local_inverse_probability_v3_typed"]
        readout = record["targeted_v3"]["readout_split_audit"].get("methods", {})
        rzz = record["targeted_v3"]["rzz_family_confusion_audit"]
        lines.append(
            f"| {record['name']} | {record['profile']} | {record['decision']} | "
            f"{float(v1['ari']):.4f}/{float(v1['nmi']):.4f} | "
            f"{float(v2['ari']):.4f}/{float(v2['nmi']):.4f} | "
            f"{float(v3c['ari']):.4f}/{float(v3c['nmi']):.4f} | "
            f"{readout.get('v1_physical_local_inverse_probability', {}).get('M5_split_count', '')}/"
            f"{readout.get('v3c_physical_local_inverse_probability_v3_typed', {}).get('M5_split_count', '')} | "
            f"{rzz.get('v1_physical_local_inverse_probability', {}).get('merge_count', '')}/"
            f"{rzz.get('v3c_physical_local_inverse_probability_v3_typed', {}).get('merge_count', '')} |"
        )
    lines.append("")
    return "\n".join(lines)


def format_run_summary(record: dict[str, object]) -> str:
    result = {
        "records": [record],
    }
    return format_s2d6_summary(result)


def _feature_block_ablation(records: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d6_feature_block_ablation_v1",
        "runs": [
            {
                "run": record["name"],
                "profile": record["profile"],
                "methods": record["targeted_v3"]["methods"],
                "key_comparison": record["targeted_v3"]["key_comparison"],
            }
            for record in records
        ],
    }


def _aggregate_audit(records: list[dict[str, object]], key: str) -> dict[str, object]:
    return {
        "schema": f"scope_static_s2d6_{key}_v1",
        "runs": {str(record["name"]): record["targeted_v3"][key] for record in records},
    }


def _balanced_profile_results(records: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d6_balanced_profile_results_v1",
        "runs": [
            {
                "run": record["name"],
                "profile": record["profile"],
                "decision": record["decision"],
                "mechanism_counts": record["teacher"]["mechanism_counts"],
                "key_comparison": record["targeted_v3"]["key_comparison"],
            }
            for record in records
            if "balanced" in str(record["profile"])
        ],
    }


def _enabled_runs(cfg: dict[str, object]) -> list[dict[str, object]]:
    raw = cfg.get("runs", DEFAULT_RUNS)
    if not isinstance(raw, list):
        raise ValueError("s2d6_targeted_representation_v3.runs must be a list")
    return [dict(item) for item in raw if isinstance(item, dict) and bool(item.get("enabled", True))]


def _load_config(config_path: str | Path | None) -> dict[str, object]:
    if config_path is None:
        return {"runs": DEFAULT_RUNS}
    data = yaml.safe_load(Path(config_path).read_text())
    if not isinstance(data, dict):
        raise ValueError("S2D.6 config must be a mapping")
    section = data.get("s2d6_targeted_representation_v3", {})
    if section is None:
        section = {}
    if not isinstance(section, dict):
        raise ValueError("s2d6_targeted_representation_v3 config must be a mapping")
    result = dict(section)
    result.setdefault("runs", DEFAULT_RUNS)
    return result


def _load_mechanism_records(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text())
    records = data.get("mechanisms")
    if not isinstance(records, list) or not records:
        raise ValueError(f"{path} does not contain non-empty mechanisms")
    return [dict(record) for record in records]


def _load_observations(path: Path) -> tuple[np.ndarray, list[str]]:
    data = np.load(path)
    return np.asarray(data["observations"], dtype=np.float64), [str(value) for value in data["probe_names"].tolist()]


def _encode_labels(labels: list[str]) -> tuple[torch.Tensor, list[str]]:
    names = sorted(set(labels))
    index = {name: idx for idx, name in enumerate(names)}
    return torch.tensor([index[label] for label in labels], dtype=torch.long), names


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run S2D.6 targeted representation v3.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--max-runs", type=int, default=None)
    args = parser.parse_args(argv)
    result = run_s2d6_targeted_representation_v3(args.config, output_dir=args.output_dir, max_runs=args.max_runs)
    print(
        "S2D.6 targeted representation v3 complete\n"
        f"  runs={result['run_order']}\n"
        f"  output={result['output_dir']}\n"
        f"  summary={result['summary']}"
    )


if __name__ == "__main__":
    main()
