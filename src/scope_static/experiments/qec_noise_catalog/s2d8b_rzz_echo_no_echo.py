from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
import yaml

from scope_static.experiments.qec_noise_catalog.config import load_s2d_physical_config, output_root_from_config
from scope_static.mechanism_observability import evaluate_active_mixed_basis_methods, rzz_family_metrics
from scope_static.mechanism_observability import evaluate_rzz_depth_sweep_methods
from scope_static.mechanism_observability import evaluate_rzz_echo_contrast_methods
from scope_static.mechanism_observability import evaluate_targeted_v3_methods
from scope_static.catalog_pipeline import run_catalog_pipeline, pipeline_stage_results


DEFAULT_RUNS = [
    {
        "name": "phys9_setA",
        "profile": "phys9_chain",
        "mechanism_set": "set_A",
        "purpose": "regression sanity profile before balanced echo/no-echo runs",
    },
    {
        "name": "phys9_multicircuit_setB_balanced",
        "profile": "phys9_multicircuit_setB_balanced",
        "mechanism_set": "set_B",
        "purpose": "balanced set_B RZZ echo/no-echo target",
    },
    {
        "name": "phys9_multicircuit_setC_balanced",
        "profile": "phys9_multicircuit_setC_balanced",
        "mechanism_set": "set_C",
        "purpose": "balanced set_C RZZ echo/no-echo target",
    },
]


def run_s2d8b_rzz_echo_no_echo(
    config_path: str | Path | None = None,
    *,
    output_dir: str | Path | None = None,
    max_runs: int | None = None,
) -> dict[str, object]:
    physical_cfg = load_s2d_physical_config(config_path)
    cfg = _load_config(config_path)
    root = output_root_from_config(physical_cfg)
    default_output = root / "S2D.8_RZZ_dynamical_probe_design" / "S2D.8b_RZZ_echo_no_echo_probe_design"
    output = Path(output_dir) if output_dir is not None else Path(str(cfg.get("output_dir", default_output)))
    output.mkdir(parents=True, exist_ok=True)
    runs = _enabled_runs(cfg)
    if max_runs is not None:
        runs = runs[: int(max_runs)]

    records = [_run_one(output, physical_cfg, cfg, run_cfg) for run_cfg in runs]
    result = {
        "schema": "scope_static_s2d8b_rzz_echo_no_echo_v1",
        "stage": "S2D.8b_RZZ_echo_no_echo_probe_design",
        "output_dir": str(output),
        "run_order": [record["name"] for record in records],
        "records": records,
        "summary": _summary(records),
        "phase_summary": _phase_summary(records),
    }
    (output / "metrics.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (output / "summary.md").write_text(format_s2d8b_summary(result))
    (output / "echo_probe_manifest.json").write_text(json.dumps(_aggregate(records, "echo_probe_manifest"), indent=2, sort_keys=True) + "\n")
    (output / "echo_response_features.json").write_text(json.dumps(_aggregate_nested(records, "echo_contrast", "echo_response_features"), indent=2, sort_keys=True) + "\n")
    (output / "rzz_family_distance_audit.json").write_text(
        json.dumps(_aggregate_nested(records, "echo_contrast", "rzz_family_distance_audit"), indent=2, sort_keys=True) + "\n"
    )
    (output / "scrambled_echo_control.json").write_text(json.dumps(_scrambled_echo_control(records), indent=2, sort_keys=True) + "\n")
    (output / "baseline_comparison.json").write_text(json.dumps(_baseline_comparison(records), indent=2, sort_keys=True) + "\n")
    (output / "feature_provenance_manifest.json").write_text(json.dumps(_aggregate(records, "feature_provenance_manifest"), indent=2, sort_keys=True) + "\n")
    (output / "phase_summary.json").write_text(json.dumps(result["phase_summary"], indent=2, sort_keys=True) + "\n")
    return result


def _run_one(output: Path, physical_cfg: dict[str, object], cfg: dict[str, object], run_cfg: dict[str, object]) -> dict[str, object]:
    run_dir = output / str(run_cfg["name"])
    run_dir.mkdir(parents=True, exist_ok=True)
    merged = dict(physical_cfg)
    merged.update({key: value for key, value in run_cfg.items() if key not in {"name", "purpose", "enabled"}})
    merged.update(dict(cfg.get("physical_overrides", {})))
    base_cfg = {**merged, "probe_set": str(cfg.get("baseline_probe_set", "base"))}
    static_cfg = {**merged, "probe_set": str(cfg.get("static_active_probe_set", "rzz_active_minimal"))}
    depth_cfg = {**merged, "probe_set": str(cfg.get("depth_probe_set", "rzz_depth_sweep"))}
    echo_cfg = {**merged, "probe_set": str(cfg.get("echo_probe_set", "rzz_echo_no_echo"))}

    base_stack = _run_phys_stack(run_dir / "base_probe", base_cfg, cfg)
    static_stack = _run_phys_stack(run_dir / "s2d7_static_active_probe", static_cfg, cfg)
    depth_stack = _run_phys_stack(run_dir / "s2d8a_depth_probe", depth_cfg, cfg)
    echo_stack = _run_phys_stack(run_dir / "rzz_echo_probe", echo_cfg, cfg)

    base_records, base_observations, base_probe_names, base_hidden, base_label_names = _load_pipeline_data(base_stack)
    static_records, static_observations, static_probe_names, static_hidden, static_label_names = _load_pipeline_data(static_stack)
    depth_records, depth_observations, depth_probe_names, depth_hidden, depth_label_names = _load_pipeline_data(depth_stack)
    echo_records, echo_observations, echo_probe_names, hidden, label_names = _load_pipeline_data(echo_stack)
    if (
        base_label_names != label_names
        or static_label_names != label_names
        or depth_label_names != label_names
        or len(base_records) != len(echo_records)
        or len(static_records) != len(echo_records)
        or len(depth_records) != len(echo_records)
    ):
        raise ValueError("S2D.8b probe stacks must produce the same mechanism label inventory")

    base_targeted = _targeted_from_stack(base_stack, base_records, base_observations, base_probe_names, base_hidden, base_label_names)
    static_targeted = _targeted_from_stack(static_stack, static_records, static_observations, static_probe_names, static_hidden, static_label_names)
    static_labels = static_targeted["labels_by_method"]
    static_local_labels = _comparison_labels(static_stack["local"])
    static_active = evaluate_active_mixed_basis_methods(
        static_records,
        static_observations,
        static_probe_names,
        static_hidden,
        static_label_names,
        comparison_labels={
            "active_probe_only_v3c": static_labels["v3c_physical_local_inverse_probability_v3_typed"],
            "direct_Salpha": static_local_labels["direct_S_alpha_assignment"],
            "oracle_fingerprint_upper_bound": static_local_labels["oracle_fingerprint_upper_bound"],
        },
    )

    depth_targeted = _targeted_from_stack(depth_stack, depth_records, depth_observations, depth_probe_names, depth_hidden, depth_label_names)
    depth_labels = depth_targeted["labels_by_method"]
    depth_local_labels = _comparison_labels(depth_stack["local"])
    depth_sweep = evaluate_rzz_depth_sweep_methods(
        depth_records,
        depth_observations,
        depth_probe_names,
        depth_hidden,
        depth_label_names,
        comparison_labels={
            "rzz_depth_probe_only_v3c": depth_labels["v3c_physical_local_inverse_probability_v3_typed"],
            "direct_Salpha": depth_local_labels["direct_S_alpha_assignment"],
            "oracle_fingerprint_upper_bound": depth_local_labels["oracle_fingerprint_upper_bound"],
        },
        bootstrap_replicates=0,
        seed=int(depth_cfg.get("seed", 0)),
    )

    echo_targeted = _targeted_from_stack(echo_stack, echo_records, echo_observations, echo_probe_names, hidden, label_names)
    echo_labels = echo_targeted["labels_by_method"]
    echo_local_labels = _comparison_labels(echo_stack["local"])
    echo_contrast = evaluate_rzz_echo_contrast_methods(
        echo_records,
        echo_observations,
        echo_probe_names,
        hidden,
        label_names,
        comparison_labels={
            "rzz_echo_probe_only_v3c": echo_labels["v3c_physical_local_inverse_probability_v3_typed"],
            "direct_Salpha": echo_local_labels["direct_S_alpha_assignment"],
            "oracle_fingerprint_upper_bound": echo_local_labels["oracle_fingerprint_upper_bound"],
        },
        bootstrap_replicates=int(cfg.get("bootstrap_replicates", 16)),
        seed=int(echo_cfg.get("seed", 0)),
    )

    combined_labels = _combined_labels(base_targeted, static_active, depth_sweep, echo_contrast)
    combined_rzz = rzz_family_metrics(combined_labels, hidden, label_names)
    method_rows = _combined_method_rows(base_targeted, static_active, depth_sweep, echo_contrast, combined_rzz)
    decision = _run_decision(method_rows, combined_rzz)
    record = {
        "name": str(run_cfg["name"]),
        "purpose": str(run_cfg.get("purpose", "")),
        "profile": str(merged.get("profile")),
        "mechanism_set": str(merged.get("mechanism_set")),
        "num_qubits": int(echo_stack["teacher"].get("num_qubits", echo_cfg.get("num_qubits", 0))),
        "shots": int(echo_cfg.get("shots", 0)),
        "baseline_probe_set": str(base_cfg.get("probe_set")),
        "static_active_probe_set": str(static_cfg.get("probe_set")),
        "depth_probe_set": str(depth_cfg.get("probe_set")),
        "echo_probe_set": str(echo_cfg.get("probe_set")),
        "decision": decision,
        "teacher": {
            "mechanism_counts": echo_stack["teacher"].get("mechanism_counts", {}),
            "num_circuit_batches": echo_stack["teacher"].get("num_circuit_batches", 1),
            "balanced_min_instances_per_mechanism": echo_stack["teacher"].get("balanced_min_instances_per_mechanism"),
        },
        "PHYS2": {
            "baseline": _compact_phys2(base_stack["separability"]),
            "static_active": _compact_phys2(static_stack["separability"]),
            "depth": _compact_phys2(depth_stack["separability"]),
            "echo": _compact_phys2(echo_stack["separability"]),
            "audit_only_upper_bound": True,
        },
        "PHYS3": {str(row["method"]): row for row in method_rows},
        "method_rows": method_rows,
        "combined_rzz_family_metrics": combined_rzz,
        "static_active": static_active,
        "depth_sweep": depth_sweep,
        "echo_contrast": echo_contrast,
        "echo_probe_manifest": echo_contrast["echo_probe_manifest"],
        "feature_provenance_manifest": echo_contrast["feature_provenance_manifest"],
    }
    _write_run_artifacts(run_dir, record)
    return record


def _run_phys_stack(run_dir: Path, cfg: dict[str, object], s2d8_cfg: dict[str, object]) -> dict[str, object]:
    pipeline = run_catalog_pipeline(
        cfg,
        output_dir=run_dir,
        bootstrap_replicates=int(s2d8_cfg.get("bootstrap_replicates", 16)),
        random_baseline_trials=int(s2d8_cfg.get("random_baseline_trials", 64)),
        run_local_inverse="always",
    )
    return pipeline_stage_results(pipeline)


def _load_pipeline_data(stack: dict[str, object]) -> tuple[list[dict[str, object]], np.ndarray, list[str], torch.Tensor, list[str]]:
    records = _load_mechanism_records(stack["teacher_dir"] / "oracle_mechanisms.json")
    observations, probe_names = _load_observations(stack["teacher_dir"] / "observations.npz")
    hidden, label_names = _encode_labels([str(record["oracle_label"]) for record in records])
    return records, observations, probe_names, hidden, label_names


def _targeted_from_stack(
    stack: dict[str, object],
    records: list[dict[str, object]],
    observations: np.ndarray,
    probe_names: list[str],
    hidden: torch.Tensor,
    label_names: list[str],
) -> dict[str, object]:
    comparisons = _comparison_labels(stack["local"])
    return evaluate_targeted_v3_methods(
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


def _comparison_labels(local: object) -> dict[str, list[int]]:
    return {str(item["comparison"]): [int(value) for value in item["labels"]] for item in local["comparisons"]}  # type: ignore[index]


def _combined_labels(
    base_targeted: dict[str, object],
    static_active: dict[str, object],
    depth_sweep: dict[str, object],
    echo_contrast: dict[str, object],
) -> dict[str, list[int]]:
    base = base_targeted["labels_by_method"]
    static = static_active["labels_by_method"]
    depth = depth_sweep["labels_by_method"]
    echo = echo_contrast["labels_by_method"]
    return {
        "baseline_v3c": [int(value) for value in base["v3c_physical_local_inverse_probability_v3_typed"]],
        "S2D.7_active_mixed_basis_moments_plus_signed_contrasts": [
            int(value) for value in static["active_mixed_basis_moments_plus_signed_contrasts"]
        ],
        "S2D.8a_rzz_depth_features": [int(value) for value in depth["rzz_depth_features"]],
        "rzz_echo_probe_only_v3c": [int(value) for value in echo["rzz_echo_probe_only_v3c"]],
        "rzz_echo_contrast_features": [int(value) for value in echo["rzz_echo_contrast_features"]],
        "scrambled_echo_control": [int(value) for value in echo["scrambled_echo_control"]],
        "direct_Salpha": [int(value) for value in echo["direct_Salpha"]],
        "oracle_fingerprint_upper_bound": [int(value) for value in echo["oracle_fingerprint_upper_bound"]],
    }


def _combined_method_rows(
    base_targeted: dict[str, object],
    static_active: dict[str, object],
    depth_sweep: dict[str, object],
    echo_contrast: dict[str, object],
    combined_rzz: dict[str, object],
) -> list[dict[str, object]]:
    rows = []
    base_map = {str(row["method"]): row for row in base_targeted["methods"]}  # type: ignore[index]
    baseline = dict(base_map["v3c_physical_local_inverse_probability_v3_typed"])
    baseline["method"] = "baseline_v3c"
    baseline["probe_role"] = "baseline_base_probe"
    rows.append(_with_rzz_metrics(baseline, combined_rzz))
    static_map = {str(row["method"]): row for row in static_active["methods"]}  # type: ignore[index]
    static = dict(static_map["active_mixed_basis_moments_plus_signed_contrasts"])
    static["method"] = "S2D.7_active_mixed_basis_moments_plus_signed_contrasts"
    static["probe_role"] = "S2D.7_static_active_reference"
    rows.append(_with_rzz_metrics(static, combined_rzz))
    depth_map = {str(row["method"]): row for row in depth_sweep["methods"]}  # type: ignore[index]
    depth = dict(depth_map["rzz_depth_features"])
    depth["method"] = "S2D.8a_rzz_depth_features"
    depth["probe_role"] = "S2D.8a_depth_reference"
    rows.append(_with_rzz_metrics(depth, combined_rzz))
    for row in echo_contrast["methods"]:  # type: ignore[index]
        current = dict(row)
        current["probe_role"] = "S2D.8b_echo_no_echo"
        rows.append(_with_rzz_metrics(current, combined_rzz))
    order = [
        "baseline_v3c",
        "S2D.7_active_mixed_basis_moments_plus_signed_contrasts",
        "S2D.8a_rzz_depth_features",
        "rzz_echo_probe_only_v3c",
        "rzz_echo_contrast_features",
        "scrambled_echo_control",
        "direct_Salpha",
        "oracle_fingerprint_upper_bound",
    ]
    index = {name: idx for idx, name in enumerate(order)}
    return sorted(rows, key=lambda item: index.get(str(item["method"]), 10_000))


def _with_rzz_metrics(row: dict[str, object], combined_rzz: dict[str, object]) -> dict[str, object]:
    method = str(row["method"])
    metrics = combined_rzz.get("methods", {}).get(method, {}) if isinstance(combined_rzz.get("methods"), dict) else {}
    return {**row, "rzz_family_metrics": metrics}


def _run_decision(method_rows: list[dict[str, object]], combined_rzz: dict[str, object]) -> str:
    methods = {str(row["method"]): row for row in method_rows}
    echo = methods.get("rzz_echo_contrast_features", {})
    scrambled = methods.get("scrambled_echo_control", {})
    direct = methods.get("direct_Salpha", {})
    baseline = methods.get("baseline_v3c", {})
    static = methods.get("S2D.7_active_mixed_basis_moments_plus_signed_contrasts", {})
    depth = methods.get("S2D.8a_rzz_depth_features", {})
    reference_rzz = min(
        _rzz_error(combined_rzz, "baseline_v3c"),
        _rzz_error(combined_rzz, "S2D.7_active_mixed_basis_moments_plus_signed_contrasts"),
        _rzz_error(combined_rzz, "S2D.8a_rzz_depth_features"),
    )
    echo_rzz = _rzz_error(combined_rzz, "rzz_echo_contrast_features")
    m1_m6_m9_ref = min(
        _rzz_error(combined_rzz, "baseline_v3c", include_transverse=False),
        _rzz_error(combined_rzz, "S2D.7_active_mixed_basis_moments_plus_signed_contrasts", include_transverse=False),
        _rzz_error(combined_rzz, "S2D.8a_rzz_depth_features", include_transverse=False),
    )
    m1_m6_m9_echo = _rzz_error(combined_rzz, "rzz_echo_contrast_features", include_transverse=False)
    regression_clean = (
        float(baseline.get("ari", 0.0)) >= 0.99
        and float(static.get("ari", 0.0)) >= 0.99
        and float(depth.get("ari", 0.0)) >= 0.99
        and float(echo.get("ari", 0.0)) >= 0.99
        and float(echo.get("nmi", 0.0)) >= 0.99
        and echo_rzz <= reference_rzz
    )
    if regression_clean:
        return "regression_pass"
    global_ok = float(echo.get("ari", 0.0)) >= 0.80 and float(echo.get("nmi", 0.0)) >= 0.80
    if global_ok and echo_rzz < reference_rzz and _beats(echo, scrambled) and _beats(echo, direct):
        return "success"
    if m1_m6_m9_echo < m1_m6_m9_ref:
        return "partial_m1_m6_m9_improved"
    return "failure"


def _rzz_error(combined_rzz: dict[str, object], method: str, *, include_transverse: bool = True) -> int:
    metrics = combined_rzz.get("methods", {}).get(method, {}) if isinstance(combined_rzz.get("methods"), dict) else {}
    keys = ["M8_M9_merge_count", "M8_M12_merge_count", "M8_split_count"]
    if include_transverse:
        keys.append("M8_M10_merge_count")
    return int(sum(int(metrics.get(key, 0)) for key in keys))


def _beats(left: dict[str, object], right: dict[str, object]) -> bool:
    return float(left.get("ari", 0.0)) > float(right.get("ari", 0.0)) and float(left.get("nmi", 0.0)) > float(right.get("nmi", 0.0))


def _summary(records: list[dict[str, object]]) -> dict[str, object]:
    primary = [record for record in records if "balanced" in str(record.get("profile", ""))]
    return {
        "num_runs": len(records),
        "num_primary_balanced_runs": len(primary),
        "success": sum(1 for record in records if record["decision"] == "success"),
        "regression_pass": sum(1 for record in records if record["decision"] == "regression_pass"),
        "partial_m1_m6_m9_improved": sum(1 for record in records if record["decision"] == "partial_m1_m6_m9_improved"),
        "failure": sum(1 for record in records if record["decision"] == "failure"),
        "primary_balanced_success": all(record["decision"] == "success" for record in primary) if primary else False,
    }


def _phase_summary(records: list[dict[str, object]]) -> dict[str, object]:
    primary = [record for record in records if "balanced" in str(record.get("profile", ""))]
    primary_success = bool(primary) and all(record["decision"] == "success" for record in primary)
    primary_failed = bool(primary) and all(record["decision"] == "failure" for record in primary)
    primary_partial = bool(primary) and any(str(record["decision"]).startswith("partial") for record in primary)
    scrambled_matched = bool(primary) and all(
        record["echo_contrast"]["scrambled_echo_control"].get("real_ari") == record["echo_contrast"]["scrambled_echo_control"].get("scrambled_ari")
        and record["echo_contrast"]["scrambled_echo_control"].get("real_nmi") == record["echo_contrast"]["scrambled_echo_control"].get("scrambled_nmi")
        for record in primary
    )
    real_not_better_than_scrambled = bool(primary) and all(
        not bool(record["echo_contrast"]["scrambled_echo_control"].get("real_beats_scrambled", False)) for record in primary
    )
    if primary_success:
        phase_label = "echo_no_echo_positive"
        conclusion = "RZZ echo/no-echo paired contrasts expose learner-visible RZZ-family signal on balanced primary runs."
        ruled_out = None
        next_step = "S2D.8c_minimal_twirl_style_probes only if residual M7/M9 ambiguity remains"
    elif primary_partial and real_not_better_than_scrambled:
        phase_label = "echo_no_echo_mixed_control_limited"
        conclusion = (
            "RZZ echo/no-echo paired contrasts give a partial RZZ-family improvement on one balanced run, "
            "but fail on the other and do not beat the scrambled-echo control."
        )
        ruled_out = "current paired echo/no-echo final-shot contrasts as a sufficient RZZ-family fix."
        next_step = "S2D.8c_minimal_twirl_style_probes"
    elif primary_failed and scrambled_matched:
        phase_label = "echo_no_echo_control_matched_negative"
        conclusion = (
            "RZZ echo/no-echo paired contrasts are learner-visible, but they match the scrambled-echo control "
            "and do not close the RZZ-family gap."
        )
        ruled_out = "RZZ-family gap can be solved by current paired echo/no-echo final-shot contrasts alone."
        next_step = "S2D.8c_minimal_twirl_style_probes"
    elif primary_failed and real_not_better_than_scrambled:
        phase_label = "echo_no_echo_control_limited_negative"
        conclusion = (
            "RZZ echo/no-echo paired contrasts fail on balanced primary runs and do not beat the scrambled-echo control."
        )
        ruled_out = "RZZ-family gap can be solved by current paired echo/no-echo final-shot contrasts alone."
        next_step = "S2D.8c_minimal_twirl_style_probes"
    else:
        phase_label = "echo_no_echo_not_frozen"
        conclusion = "S2D.8b phase conclusion requires balanced primary decisions and scrambled-control interpretation."
        ruled_out = None
        next_step = None
    return {
        "schema": "scope_static_s2d8b_phase_summary_v1",
        "stage": "S2D.8b_RZZ_echo_no_echo_probe_design",
        "phase_label": phase_label,
        "main_conclusion": conclusion,
        "ruled_out_hypothesis": ruled_out,
        "not_ruled_out": (
            "twirl-style dynamical probes or stronger local channel characterization"
            if (primary_failed or primary_partial) and real_not_better_than_scrambled
            else None
        ),
        "next_recommended_step": next_step,
    }


def format_s2d8b_summary(result: dict[str, object]) -> str:
    phase = result.get("phase_summary", {})
    lines = [
        "# S2D.8b RZZ Echo / No-Echo",
        "",
        "| run | decision | baseline v3c | S2D.7 static | S2D.8a depth | echo contrast | scrambled echo | RZZ error ref/echo | boot NMI |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for record in result["records"]:  # type: ignore[index]
        methods = {str(row["method"]): row for row in record["method_rows"]}
        baseline = methods["baseline_v3c"]
        static = methods["S2D.7_active_mixed_basis_moments_plus_signed_contrasts"]
        depth = methods["S2D.8a_rzz_depth_features"]
        echo = methods["rzz_echo_contrast_features"]
        scrambled = methods["scrambled_echo_control"]
        rzz = record["combined_rzz_family_metrics"]
        ref_error = min(
            _rzz_error(rzz, "baseline_v3c"),
            _rzz_error(rzz, "S2D.7_active_mixed_basis_moments_plus_signed_contrasts"),
            _rzz_error(rzz, "S2D.8a_rzz_depth_features"),
        )
        echo_error = _rzz_error(rzz, "rzz_echo_contrast_features")
        bootstrap = echo.get("bootstrap_nmi", {})
        lines.append(
            f"| {record['name']} | {record['decision']} | "
            f"{float(baseline['ari']):.4f}/{float(baseline['nmi']):.4f} | "
            f"{float(static['ari']):.4f}/{float(static['nmi']):.4f} | "
            f"{float(depth['ari']):.4f}/{float(depth['nmi']):.4f} | "
            f"{float(echo['ari']):.4f}/{float(echo['nmi']):.4f} | "
            f"{float(scrambled['ari']):.4f}/{float(scrambled['nmi']):.4f} | "
            f"{ref_error}/{echo_error} | {float(bootstrap.get('min_vs_full', 1.0)):.4f} |"
        )
    if phase:
        lines.extend(
            [
                "",
                "## Phase Conclusion",
                "",
                f"- Label: `{phase.get('phase_label')}`",
                f"- Conclusion: {phase.get('main_conclusion')}",
                f"- Ruled out: `{phase.get('ruled_out_hypothesis')}`",
                f"- Next: `{phase.get('next_recommended_step')}`",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def _write_run_artifacts(run_dir: Path, record: dict[str, object]) -> None:
    (run_dir / "metrics.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    (run_dir / "summary.md").write_text(format_s2d8b_summary({"records": [record]}))
    (run_dir / "echo_probe_manifest.json").write_text(json.dumps(record["echo_probe_manifest"], indent=2, sort_keys=True) + "\n")
    (run_dir / "echo_response_features.json").write_text(json.dumps(record["echo_contrast"]["echo_response_features"], indent=2, sort_keys=True) + "\n")
    (run_dir / "rzz_family_distance_audit.json").write_text(json.dumps(record["echo_contrast"]["rzz_family_distance_audit"], indent=2, sort_keys=True) + "\n")
    (run_dir / "scrambled_echo_control.json").write_text(json.dumps(record["echo_contrast"]["scrambled_echo_control"], indent=2, sort_keys=True) + "\n")
    (run_dir / "baseline_comparison.json").write_text(json.dumps(_run_baseline_comparison(record), indent=2, sort_keys=True) + "\n")
    (run_dir / "feature_provenance_manifest.json").write_text(json.dumps(record["feature_provenance_manifest"], indent=2, sort_keys=True) + "\n")


def _aggregate(records: list[dict[str, object]], key: str) -> dict[str, object]:
    return {"schema": f"scope_static_s2d8b_{key}_aggregate_v1", "runs": {str(record["name"]): record[key] for record in records}}


def _aggregate_nested(records: list[dict[str, object]], parent: str, key: str) -> dict[str, object]:
    return {"schema": f"scope_static_s2d8b_{key}_aggregate_v1", "runs": {str(record["name"]): record[parent][key] for record in records}}


def _scrambled_echo_control(records: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d8b_scrambled_echo_control_v1",
        "runs": {str(record["name"]): record["echo_contrast"]["scrambled_echo_control"] for record in records},
    }


def _baseline_comparison(records: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d8b_baseline_comparison_v1",
        "runs": {str(record["name"]): _run_baseline_comparison(record) for record in records},
    }


def _run_baseline_comparison(record: dict[str, object]) -> dict[str, object]:
    methods = {str(row["method"]): row for row in record["method_rows"]}
    return {
        "decision": record["decision"],
        "baseline_v3c": _compact_method(methods["baseline_v3c"]),
        "S2D.7_active_mixed_basis_moments_plus_signed_contrasts": _compact_method(
            methods["S2D.7_active_mixed_basis_moments_plus_signed_contrasts"]
        ),
        "S2D.8a_rzz_depth_features": _compact_method(methods["S2D.8a_rzz_depth_features"]),
        "rzz_echo_contrast_features": _compact_method(methods["rzz_echo_contrast_features"]),
        "scrambled_echo_control": _compact_method(methods["scrambled_echo_control"]),
        "direct_Salpha": _compact_method(methods["direct_Salpha"]),
        "oracle_fingerprint_upper_bound": _compact_method(methods["oracle_fingerprint_upper_bound"]),
        "echo_key_comparison": record["echo_contrast"]["key_comparison"],
    }


def _compact_method(row: dict[str, object]) -> dict[str, object]:
    return {
        "ari": row.get("ari"),
        "nmi": row.get("nmi"),
        "active_clusters": row.get("active_clusters"),
        "rzz_family_metrics": row.get("rzz_family_metrics"),
    }


def _compact_phys2(metrics: dict[str, object]) -> dict[str, object]:
    return {
        "ari": metrics.get("ari"),
        "nmi": metrics.get("nmi"),
        "active_clusters": metrics.get("active_clusters"),
        "separability_gate": metrics.get("separability_gate"),
        "feature_shape": metrics.get("feature_shape"),
        "fingerprint_families": metrics.get("fingerprint_families"),
    }


def _enabled_runs(cfg: dict[str, object]) -> list[dict[str, object]]:
    raw = cfg.get("runs", DEFAULT_RUNS)
    if not isinstance(raw, list):
        raise ValueError("s2d8b_rzz_echo_no_echo.runs must be a list")
    return [dict(item) for item in raw if isinstance(item, dict) and bool(item.get("enabled", True))]


def _load_config(config_path: str | Path | None) -> dict[str, object]:
    if config_path is None:
        return {"runs": DEFAULT_RUNS}
    data = yaml.safe_load(Path(config_path).read_text())
    if not isinstance(data, dict):
        raise ValueError("S2D.8b config must be a mapping")
    section = data.get("s2d8b_rzz_echo_no_echo", {})
    if section is None:
        section = {}
    if not isinstance(section, dict):
        raise ValueError("s2d8b_rzz_echo_no_echo config must be a mapping")
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
    parser = argparse.ArgumentParser(description="Run S2D.8b RZZ echo/no-echo probe design.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--max-runs", type=int, default=None)
    args = parser.parse_args(argv)
    result = run_s2d8b_rzz_echo_no_echo(args.config, output_dir=args.output_dir, max_runs=args.max_runs)
    print(
        "S2D.8b RZZ echo/no-echo complete\n"
        f"  runs={result['run_order']}\n"
        f"  output={result['output_dir']}\n"
        f"  summary={result['summary']}"
    )


if __name__ == "__main__":
    main()
