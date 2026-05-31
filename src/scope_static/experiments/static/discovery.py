from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import torch
import yaml

from scope_static.dem.discovery import (
    add_known_orbit_deltas,
    build_discovery_important_results,
    discovery_parameter_audit,
    field_discovery_metrics,
    is_discovery_model,
)
from scope_static.dem.evidence import (
    EvidenceConfig,
    EvidenceContext,
    build_evidence_record,
    build_important_results,
    evaluate_evidence,
    threshold_record_list,
)
from scope_static.experiments.static.plan import ExperimentPlan
from scope_static.dem.fields import make_field
from scope_static.dem.metrics import compression_audit
from scope_static.dem.stim_dem import sample_observations_from_logits
from scope_static.dem.teacher_logits import make_teacher_logits
from scope_static.dem.training import fit_field
from scope_static.dem.windows import WindowPlan


def run_discovery_experiment(config_path: str | Path, *, output_dir: str | Path | None = None) -> dict[str, object]:
    path = Path(config_path)
    config = yaml.safe_load(path.read_text())
    if isinstance(config, dict) and "scenarios" in config:
        return _run_discovery_scenarios(path, config, output_dir=output_dir)
    return _run_single_discovery_experiment(path, config, output_dir=output_dir)


def _run_single_discovery_experiment(
    config_path: Path,
    config: dict[str, object],
    *,
    output_dir: str | Path | None = None,
) -> dict[str, object]:
    plan = ExperimentPlan.from_config(config, config_path=config_path, output_dir=output_dir)
    output = plan.output_dir
    output.mkdir(parents=True, exist_ok=True)

    graph_cache = {
        rank: plan.build_graph(rank)
        for rank in sorted(set([*plan.residual_ranks, plan.teacher_residual_rank]))
    }
    teacher_graph = graph_cache[plan.teacher_residual_rank]
    graph_runs = [(rank, graph_cache[rank]) for rank in plan.residual_ranks]
    window_plans = {rank: WindowPlan.from_config(graph, plan.windows_cfg) for rank, graph in graph_runs}
    for rank, graph in graph_runs:
        if not torch.equal(graph.A, teacher_graph.A):
            raise ValueError(f"rank {rank} graph parity matrix differs from teacher rank {plan.teacher_residual_rank}")

    audits: list[dict[str, object]] = []
    window_audits: list[dict[str, object]] = []
    for rank, graph in graph_runs:
        audit = graph.audit_dict(
            exact_likelihood_trainable=bool(plan.training_cfg.get("exact_likelihood_trainable", False)),
            dem_fault_logit_claim=bool(plan.training_cfg.get("dem_fault_logit_claim", False)),
            cptp_gksl_claim=bool(plan.training_cfg.get("cptp_gksl_claim", False)),
        )
        audit["residual_rank"] = int(rank)
        audit.update(compression_audit(graph))
        window_audit = window_plans[rank].audit_dict()
        window_audit["residual_rank"] = int(rank)
        audit.update(window_audit)
        audits.append(audit)
        window_audits.append(window_audit)

    graph_audit_payload: dict[str, object]
    if len(audits) == 1:
        graph_audit_payload = audits[0]
    else:
        graph_audit_payload = {
            "residual_ranks": [int(rank) for rank in plan.residual_ranks],
            "teacher_residual_rank": int(plan.teacher_residual_rank),
            "graph_audits": audits,
        }

    discovery_cfg = dict(plan.training_cfg.get("discovery", {}))
    num_restarts = int(discovery_cfg.get("restarts", plan.training_cfg.get("discovery_restarts", 4)))
    active_mass_threshold = float(discovery_cfg.get("active_mass_threshold", 1.0))
    restart_poor_ari_threshold = float(discovery_cfg.get("restart_poor_ari_threshold", 0.5))

    evidence_config = EvidenceConfig(
        aggregate_unique=plan.aggregate_unique,
        backend=plan.likelihood_backend,
        global_exact_max_bits=plan.global_exact_max_bits,
    )
    records: list[dict[str, object]] = []
    restart_records: list[dict[str, object]] = []
    fit_cache: dict[tuple[object, ...], dict[str, object]] = {}
    num_model_fits_executed = 0
    num_model_fit_cache_hits = 0

    for seed in plan.seeds:
        for teacher_case in plan.teacher_cases:
            teacher_logits = make_teacher_logits(
                teacher_graph,
                mode=teacher_case.mode,
                epsilon_break=teacher_case.epsilon_break,
                seed=int(seed),
                dtype=plan.dtype,
            )
            heldout = sample_observations_from_logits(
                teacher_graph,
                teacher_logits,
                shots=plan.heldout_shots,
                seed=int(seed) + 10_000,
            )
            train_observations_by_shots = {
                int(shots): sample_observations_from_logits(
                    teacher_graph,
                    teacher_logits,
                    shots=int(shots),
                    seed=int(seed) + int(shots),
                )
                for shots in plan.shot_budgets
            }

            for residual_rank, graph in graph_runs:
                rank_windows = window_plans[residual_rank]
                for shots, train_obs in train_observations_by_shots.items():
                    for model_name in plan.model_names:
                        prototype_counts = _prototype_counts_for_model(plan, graph, model_name)
                        for prototype_count in prototype_counts:
                            if is_discovery_model(model_name):
                                selected, outcomes = _fit_discovery_restarts(
                                    plan,
                                    graph,
                                    model_name=model_name,
                                    prototype_count=int(prototype_count),
                                    train_obs=train_obs,
                                    heldout=heldout,
                                    teacher_logits=teacher_logits,
                                    seed=int(seed),
                                    shots=int(shots),
                                    teacher_mode=teacher_case.mode,
                                    epsilon_break=float(teacher_case.epsilon_break),
                                    residual_rank=int(residual_rank),
                                    windows=rank_windows,
                                    evidence_config=evidence_config,
                                    num_restarts=num_restarts,
                                    active_mass_threshold=active_mass_threshold,
                                    restart_poor_ari_threshold=restart_poor_ari_threshold,
                                )
                                num_model_fits_executed += len(outcomes)
                                restart_records.extend(outcomes)
                                fit_summary = selected["fit_summary"]
                                metrics = selected["metrics"]
                            else:
                                cached = _fit_cached_baseline(
                                    plan,
                                    graph,
                                    model_name=model_name,
                                    train_obs=train_obs,
                                    heldout=heldout,
                                    teacher_logits=teacher_logits,
                                    seed=int(seed),
                                    shots=int(shots),
                                    teacher_case=teacher_case,
                                    windows=rank_windows,
                                    evidence_config=evidence_config,
                                    fit_cache=fit_cache,
                                )
                                if cached["cache_hit"]:
                                    num_model_fit_cache_hits += 1
                                else:
                                    num_model_fits_executed += 1
                                fit_summary = cached["fit_summary"]
                                metrics = cached["metrics"]

                            record = build_evidence_record(
                                graph,
                                context=EvidenceContext(
                                    seed=int(seed),
                                    teacher_mode=teacher_case.mode,
                                    teacher_residual_rank=int(plan.teacher_residual_rank),
                                    epsilon_break=float(teacher_case.epsilon_break),
                                    shots=int(shots),
                                    model_name=model_name,
                                    residual_rank=int(residual_rank),
                                ),
                                fit_summary=fit_summary,
                                metrics=metrics,
                            )
                            record.update(
                                {
                                    "evidence_record_schema": "scope_static_discovery_v1",
                                    "stage": "stage2A",
                                    "stage2a_question": (
                                        "Can learned DEM-fault assignments S[j,k] recover hidden omega(j) "
                                        "from DEM parity-map observations alone?"
                                    ),
                                    "stage2a_success_requires_partition_and_likelihood": True,
                                    "prototype_count_K": None if prototype_count is None else int(prototype_count),
                                    "hidden_partition_available_to_learner": False,
                                    "hidden_partition_used_by": "synthetic_teacher_and_evaluator_only",
                                }
                            )
                            if is_discovery_model(model_name):
                                record.update(
                                    discovery_parameter_audit(
                                        graph,
                                        model_name=model_name,
                                        prototype_count=int(prototype_count),
                                        residual_rank=int(residual_rank),
                                    )
                                )
                            records.append(record)

                            if plan.progress_every_records and len(records) % plan.progress_every_records == 0:
                                print(
                                    f"[scope-static-disc] records={len(records)} fits={num_model_fits_executed} cache_hits={num_model_fit_cache_hits}",
                                    file=sys.stderr,
                                    flush=True,
                                )

    add_known_orbit_deltas(records)
    threshold_records = threshold_record_list(
        records,
        threshold_epsilon=plan.threshold_epsilon,
        seed_policy=plan.threshold_seed_policy,
    )
    run_summary = {
        **plan.output_audit_dict(),
        "stage": "stage2A",
        "requested_likelihood_backend": plan.likelihood_backend,
        "likelihood_objective": plan.likelihood_objective,
        "residual_ranks": [int(rank) for rank in plan.residual_ranks],
        "teacher_residual_rank": int(plan.teacher_residual_rank),
        "discovery_restarts": num_restarts,
        "active_prototype_mass_threshold": active_mass_threshold,
        "num_model_fits_executed": num_model_fits_executed,
        "num_model_fit_cache_hits": num_model_fit_cache_hits,
        "num_model_fit_requests": num_model_fits_executed + num_model_fit_cache_hits,
        "model_fit_cache_hit_rate": (
            num_model_fit_cache_hits / (num_model_fits_executed + num_model_fit_cache_hits)
            if (num_model_fits_executed + num_model_fit_cache_hits)
            else 0.0
        ),
    }
    result = {
        **audits[0],
        **run_summary,
        "graph_audits": audits,
        "window_audits": window_audits,
        "teacher_cases": [teacher_case.audit_dict() for teacher_case in plan.teacher_cases],
        "important_results": build_important_results(
            records,
            graph_audits=audits,
            window_audits=window_audits,
            threshold_records=threshold_records,
            run_summary=run_summary,
        ),
        "discovery_important_results": build_discovery_important_results(
            records,
            threshold_epsilon=plan.threshold_epsilon,
        ),
        "discovery_restart_records": restart_records,
        "records": records,
        "shots_to_threshold": threshold_records,
    }
    (output / "config_snapshot.yaml").write_text(yaml.safe_dump(plan.config, sort_keys=False))
    (output / "graph_audit.json").write_text(json.dumps(graph_audit_payload, indent=2, sort_keys=True))
    (output / "metrics.json").write_text(json.dumps(result, indent=2, sort_keys=True))
    return result


def _run_discovery_scenarios(
    config_path: Path,
    config: dict[str, object],
    *,
    output_dir: str | Path | None = None,
) -> dict[str, object]:
    scenarios = config.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError("scenario discovery config requires a non-empty scenarios list")

    root_output = Path(output_dir or dict(config.get("run", {})).get("output_dir", "outputs/scope_static/DISC_full"))
    root_output.mkdir(parents=True, exist_ok=True)
    base = {key: value for key, value in config.items() if key != "scenarios"}

    combined_records: list[dict[str, object]] = []
    combined_restarts: list[dict[str, object]] = []
    scenario_summaries: list[dict[str, object]] = []
    total_fits = 0
    total_cache_hits = 0
    threshold_epsilon = float(dict(config.get("experiment", {})).get("threshold_epsilon", 0.01))

    for scenario in scenarios:
        if not isinstance(scenario, dict):
            raise ValueError("each discovery scenario must be a mapping")
        scenario_name = str(scenario["name"])
        scenario_config = _deep_merge_dicts(base, {key: value for key, value in scenario.items() if key != "name"})
        scenario_output = root_output / scenario_name
        scenario_run = dict(scenario_config.get("run", {}))
        scenario_run["output_dir"] = str(scenario_output)
        scenario_run["name"] = f"{scenario_run.get('name', dict(config.get('run', {})).get('name', 'stage2a'))}_{scenario_name}"
        scenario_config["run"] = scenario_run

        result = _run_single_discovery_experiment(config_path, scenario_config, output_dir=scenario_output)
        total_fits += int(result.get("num_model_fits_executed", 0))
        total_cache_hits += int(result.get("num_model_fit_cache_hits", 0))
        for record in result.get("records", []):
            record["scenario"] = scenario_name
            combined_records.append(record)
        for restart in result.get("discovery_restart_records", []):
            restart["scenario"] = scenario_name
            combined_restarts.append(restart)
        scenario_summaries.append(
            {
                "scenario": scenario_name,
                "output_dir": str(scenario_output),
                "metrics_path": str(scenario_output / "metrics.json"),
                "num_records": len(result.get("records", [])),
                "num_model_fits_executed": int(result.get("num_model_fits_executed", 0)),
                "num_model_fit_cache_hits": int(result.get("num_model_fit_cache_hits", 0)),
                "discovery_summary": result.get("discovery_important_results", {}).get("discovery_summary", []),
            }
        )

    combined_result = {
        "stage": "stage2A",
        "scenario_config": True,
        "run_name": str(dict(config.get("run", {})).get("name", "")),
        "config_path": str(config_path),
        "config_stem": config_path.stem,
        "output_dir": str(root_output),
        "output_dir_overridden": output_dir is not None,
        "requested_likelihood_backend": dict(config.get("training", {})).get("likelihood_backend", "auto"),
        "likelihood_objective": dict(config.get("training", {})).get("likelihood_objective", "global_exact"),
        "discovery_restarts": dict(dict(config.get("training", {})).get("discovery", {})).get("restarts", 4),
        "num_model_fits_executed": total_fits,
        "num_model_fit_cache_hits": total_cache_hits,
        "num_model_fit_requests": total_fits + total_cache_hits,
        "scenario_summaries": scenario_summaries,
        "discovery_important_results": build_discovery_important_results(
            combined_records,
            threshold_epsilon=threshold_epsilon,
        ),
        "discovery_restart_records": combined_restarts,
        "records": combined_records,
    }
    (root_output / "config_snapshot.yaml").write_text(yaml.safe_dump(config, sort_keys=False))
    (root_output / "metrics.json").write_text(json.dumps(combined_result, indent=2, sort_keys=True))
    return combined_result


def _fit_discovery_restarts(
    plan: ExperimentPlan,
    graph,
    *,
    model_name: str,
    prototype_count: int,
    train_obs: torch.Tensor,
    heldout: torch.Tensor,
    teacher_logits: torch.Tensor,
    seed: int,
    shots: int,
    teacher_mode: str,
    epsilon_break: float,
    residual_rank: int,
    windows: WindowPlan,
    evidence_config: EvidenceConfig,
    num_restarts: int,
    active_mass_threshold: float,
    restart_poor_ari_threshold: float,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    outcomes: list[dict[str, object]] = []
    selected: dict[str, object] | None = None
    best_nll = float("inf")
    restarts = max(1, int(num_restarts))
    for restart_index in range(restarts):
        model_options = plan.model_options(model_name)
        model_options["prototype_count"] = int(prototype_count)
        restart_seed = _restart_seed(seed=seed, prototype_count=prototype_count, restart_index=restart_index)
        field = make_field(
            model_name,
            graph,
            dtype=plan.dtype,
            seed=restart_seed,
            model_options=model_options,
        )
        regularization_weight = plan.regularization_weight(model_name, model_options)
        fit = fit_field(
            graph,
            field,
            train_obs,
            steps=int(plan.training_cfg.get("steps", 200)),
            lr=float(plan.training_cfg.get("lr", 0.05)),
            aggregate_unique=plan.aggregate_unique,
            device=plan.device,
            backend=plan.likelihood_backend,
            observation_mode=plan.observation_mode(model_name),
            regularization_weight=regularization_weight,
            likelihood_objective=plan.likelihood_objective,
            windows=windows,
        )
        fitted_field = fit["field"]
        logits = fitted_field.realized_logits(graph)
        metrics = evaluate_evidence(
            graph,
            logits,
            teacher_logits.to(device=logits.device, dtype=logits.dtype),
            heldout,
            config=evidence_config,
            windows=windows,
        )
        metrics.update(
            field_discovery_metrics(
                fitted_field,
                graph.orbit_ids,
                active_mass_threshold=active_mass_threshold,
            )
        )
        fit_summary = _fit_summary(fitted_field, fit)
        train_final = float(fit_summary["train_final_nll"]) if fit_summary["train_final_nll"] is not None else float("inf")
        outcome = {
            "seed": int(seed),
            "teacher_mode": teacher_mode,
            "epsilon_break": float(epsilon_break),
            "shots": int(shots),
            "model": model_name,
            "prototype_count_K": int(prototype_count),
            "residual_rank": int(residual_rank),
            "restart_index": int(restart_index),
            "restart_seed": int(restart_seed),
            "selected": False,
            "train_initial_nll": fit_summary["train_initial_nll"],
            "train_final_nll": fit_summary["train_final_nll"],
            "ari": metrics.get("ari"),
            "nmi": metrics.get("nmi"),
            "assignment_entropy_mean": metrics.get("assignment_entropy_mean"),
            "assignment_entropy_normalized": metrics.get("assignment_entropy_normalized"),
            "num_active_prototypes": metrics.get("num_active_prototypes"),
            "assignment_collapse": metrics.get("assignment_collapse"),
            "poor_partition_recovery": (
                None if metrics.get("ari") is None else bool(float(metrics["ari"]) < float(restart_poor_ari_threshold))
            ),
        }
        outcomes.append(outcome)
        if selected is None or train_final < best_nll:
            best_nll = train_final
            selected = {
                "restart_index": restart_index,
                "restart_seed": restart_seed,
                "fit_summary": fit_summary,
                "metrics": metrics,
            }

    assert selected is not None
    for outcome in outcomes:
        outcome["selected"] = outcome["restart_index"] == selected["restart_index"]
    selected["metrics"].update(
        {
            "discovery_num_restarts": restarts,
            "discovery_selected_restart_index": int(selected["restart_index"]),
            "discovery_selected_restart_seed": int(selected["restart_seed"]),
            "discovery_restart_selection_metric": "train_final_nll",
            "discovery_restart_outcomes": outcomes,
            "discovery_nonselected_restart_collapses": sum(
                1 for outcome in outcomes if not outcome["selected"] and bool(outcome.get("assignment_collapse"))
            ),
            "discovery_nonselected_restart_poor_recovery": sum(
                1 for outcome in outcomes if not outcome["selected"] and bool(outcome.get("poor_partition_recovery"))
            ),
        }
    )
    return selected, outcomes


def _fit_cached_baseline(
    plan: ExperimentPlan,
    graph,
    *,
    model_name: str,
    train_obs: torch.Tensor,
    heldout: torch.Tensor,
    teacher_logits: torch.Tensor,
    seed: int,
    shots: int,
    teacher_case,
    windows: WindowPlan,
    evidence_config: EvidenceConfig,
    fit_cache: dict[tuple[object, ...], dict[str, object]],
) -> dict[str, object]:
    observation_mode = plan.observation_mode(model_name)
    model_options = plan.model_options(model_name)
    regularization_weight = plan.regularization_weight(model_name, model_options)
    cache_key = plan.fit_cache_key(
        seed=int(seed),
        teacher_case=teacher_case,
        shots=int(shots),
        model_name=model_name,
        observation_mode=observation_mode,
    )
    cached = fit_cache.get(cache_key) if cache_key is not None else None
    if cached is not None:
        return {**cached, "cache_hit": True}

    field = make_field(
        model_name,
        graph,
        dtype=plan.dtype,
        seed=int(seed),
        model_options=model_options,
    )
    fit = fit_field(
        graph,
        field,
        train_obs,
        steps=int(plan.training_cfg.get("steps", 200)),
        lr=float(plan.training_cfg.get("lr", 0.05)),
        aggregate_unique=plan.aggregate_unique,
        device=plan.device,
        backend=plan.likelihood_backend,
        observation_mode=observation_mode,
        regularization_weight=regularization_weight,
        likelihood_objective=plan.likelihood_objective,
        windows=windows,
    )
    fitted_field = fit["field"]
    logits = fitted_field.realized_logits(graph)
    metrics = evaluate_evidence(
        graph,
        logits,
        teacher_logits.to(device=logits.device, dtype=logits.dtype),
        heldout,
        config=evidence_config,
        windows=windows,
    )
    payload = {"fit_summary": _fit_summary(fitted_field, fit), "metrics": metrics}
    if cache_key is not None:
        fit_cache[cache_key] = payload
    return {**payload, "cache_hit": False}


def _fit_summary(field, fit: dict[str, object]) -> dict[str, object]:
    history = fit["history"]
    return {
        "parameter_count": int(field.parameter_count),
        "train_initial_nll": history[0] if history else None,
        "train_final_nll": history[-1] if history else None,
        "train_requested_likelihood_backend": fit["requested_backend"],
        "train_resolved_likelihood_backend": fit["resolved_backend"],
        "train_likelihood_adapter": fit["likelihood_adapter"],
        "train_likelihood_gpu_batch_available": fit["likelihood_gpu_batch_available"],
        "train_observation_mode": fit["observation_mode"],
        "train_regularization_weight": fit["regularization_weight"],
        "train_likelihood_objective": fit["likelihood_objective"],
        "num_train_windows": fit["num_train_windows"],
        "max_train_window_bits": fit["max_train_window_bits"],
    }


def _prototype_counts_for_model(plan: ExperimentPlan, graph, model_name: str) -> tuple[int | None, ...]:
    if not is_discovery_model(model_name):
        return (None,)
    discovery_cfg = dict(plan.training_cfg.get("discovery", {}))
    raw = discovery_cfg.get("prototype_counts", plan.experiment_cfg.get("prototype_counts", [graph.O]))
    if isinstance(raw, (str, int)):
        raw_values = [raw]
    else:
        raw_values = list(raw)
    return tuple(_resolve_prototype_count(value, graph.O) for value in raw_values)


def _resolve_prototype_count(value: object, num_orbits: int) -> int:
    if isinstance(value, str):
        text = value.strip().upper()
        if text == "O":
            return int(num_orbits)
        if text.startswith("O+") or text.startswith("O-"):
            return int(num_orbits + int(text[1:]))
    return int(value)


def _restart_seed(*, seed: int, prototype_count: int, restart_index: int) -> int:
    return int(seed) + 100_000 + 1_000 * int(prototype_count) + int(restart_index)


def _deep_merge_dicts(base: dict[str, object], override: dict[str, object]) -> dict[str, object]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge_dicts(dict(merged[key]), value)
        else:
            merged[key] = value
    return merged


def format_discovery_terminal_summary(result: dict[str, object]) -> str:
    output_dir = str(result.get("output_dir", ""))
    metrics_path = str(Path(output_dir) / "metrics.json") if output_dir else "metrics.json"
    lines = [
        "Stage 2A Discovery Summary",
        f"config: {result.get('config_path')}",
        f"output: {output_dir}",
        f"metrics: {metrics_path}",
        (
            "backend: "
            f"{result.get('requested_likelihood_backend')} | "
            f"objective: {result.get('likelihood_objective')} | "
            f"restarts: {result.get('discovery_restarts')}"
        ),
        (
            "records: "
            f"{len(result.get('records', []))} | "
            f"fits: {result.get('num_model_fits_executed')} | "
            f"cache_hits: {result.get('num_model_fit_cache_hits')}"
        ),
        "",
    ]

    rows = (
        result.get("discovery_important_results", {})
        .get("discovery_summary", [])
        if isinstance(result.get("discovery_important_results"), dict)
        else []
    )
    if not rows:
        lines.append("No discovery model summary rows were produced.")
        return "\n".join(lines)

    include_scenario = any(row.get("scenario") is not None for row in rows)
    headers = []
    if include_scenario:
        headers.append("scenario")
    headers.extend(
        [
        "teacher",
        "eps",
        "shots",
        "model",
        "K",
        "r",
        "ARI",
        "NMI",
        "ent",
        "active",
        "dNLL_known",
        "collapse",
        "pass",
        ]
    )
    table = [headers]
    for row in rows:
        table_row = []
        if include_scenario:
            table_row.append(str(row.get("scenario")))
        table_row.extend(
            [
                str(row.get("teacher_mode")),
                _fmt_number(row.get("epsilon_break"), digits=3),
                str(row.get("shots")),
                str(row.get("model")),
                str(row.get("prototype_count_K")),
                str(row.get("residual_rank")),
                _fmt_number(row.get("mean_ari"), digits=3),
                _fmt_number(row.get("mean_nmi"), digits=3),
                _fmt_number(row.get("mean_assignment_entropy_normalized"), digits=3),
                _fmt_number(row.get("mean_num_active_prototypes"), digits=2),
                _fmt_number(row.get("mean_delta_nll_known_orbit"), digits=5),
                str(row.get("num_selected_collapsed")),
                _fmt_bool(row.get("passes_known_orbit_nll_threshold")),
            ]
        )
        table.append(table_row)
    lines.extend(_format_table(table))
    return "\n".join(lines)


def _fmt_number(value: object, *, digits: int) -> str:
    if value is None:
        return "-"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if not torch.isfinite(torch.tensor(number)):
        return str(value)
    return f"{number:.{digits}g}"


def _fmt_bool(value: object) -> str:
    if value is None:
        return "-"
    return "yes" if bool(value) else "no"


def _format_table(rows: list[list[str]]) -> list[str]:
    widths = [max(len(str(row[index])) for row in rows) for index in range(len(rows[0]))]
    formatted = []
    for row_index, row in enumerate(rows):
        formatted.append("  ".join(str(value).ljust(widths[index]) for index, value in enumerate(row)))
        if row_index == 0:
            formatted.append("  ".join("-" * width for width in widths))
    return formatted


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SCOPE-Static Stage 2A discovery experiments.")
    parser.add_argument("--config", required=True, help="Path to YAML config.")
    parser.add_argument("--output-dir", default=None, help="Optional output directory override.")
    args = parser.parse_args()
    result = run_discovery_experiment(args.config, output_dir=args.output_dir)
    print(format_discovery_terminal_summary(result))


if __name__ == "__main__":
    main()
