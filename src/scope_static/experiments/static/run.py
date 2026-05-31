from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import torch
import yaml

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


def run_experiment(config_path: str | Path, *, output_dir: str | Path | None = None) -> dict[str, object]:
    plan = ExperimentPlan.from_path(config_path, output_dir=output_dir)
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

    if len(audits) == 1:
        graph_audit_payload: dict[str, object] = audits[0]
    else:
        graph_audit_payload = {
            "residual_ranks": [int(rank) for rank in plan.residual_ranks],
            "teacher_residual_rank": int(plan.teacher_residual_rank),
            "graph_audits": audits,
        }

    evidence_config = EvidenceConfig(
        aggregate_unique=plan.aggregate_unique,
        backend=plan.likelihood_backend,
        global_exact_max_bits=plan.global_exact_max_bits,
    )
    records: list[dict[str, object]] = []
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
                        if cached is None:
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
                                windows=rank_windows,
                            )
                            fitted_field = fit["field"]
                            logits = fitted_field.realized_logits(graph)
                            metrics = evaluate_evidence(
                                graph,
                                logits,
                                teacher_logits.to(device=logits.device, dtype=logits.dtype),
                                heldout,
                                config=evidence_config,
                                windows=rank_windows,
                            )
                            fit_summary = {
                                "parameter_count": int(fitted_field.parameter_count),
                                "train_initial_nll": fit["history"][0] if fit["history"] else None,
                                "train_final_nll": fit["history"][-1] if fit["history"] else None,
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
                            cached = {"fit_summary": fit_summary, "metrics": metrics}
                            if cache_key is not None:
                                fit_cache[cache_key] = cached
                            num_model_fits_executed += 1
                        else:
                            num_model_fit_cache_hits += 1

                        records.append(
                            build_evidence_record(
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
                                fit_summary=cached["fit_summary"],
                                metrics=cached["metrics"],
                            )
                        )
                        if plan.progress_every_records and len(records) % plan.progress_every_records == 0:
                            print(
                                f"[scope-static] records={len(records)} fits={num_model_fits_executed} cache_hits={num_model_fit_cache_hits}",
                                file=sys.stderr,
                                flush=True,
                            )

    threshold_records = threshold_record_list(
        records,
        threshold_epsilon=plan.threshold_epsilon,
        seed_policy=plan.threshold_seed_policy,
    )
    run_summary = {
        **plan.output_audit_dict(),
        "requested_likelihood_backend": plan.likelihood_backend,
        "likelihood_objective": plan.likelihood_objective,
        "residual_ranks": [int(rank) for rank in plan.residual_ranks],
        "teacher_residual_rank": int(plan.teacher_residual_rank),
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
        "records": records,
        "shots_to_threshold": threshold_records,
    }
    (output / "config_snapshot.yaml").write_text(yaml.safe_dump(plan.config, sort_keys=False))
    (output / "graph_audit.json").write_text(json.dumps(graph_audit_payload, indent=2, sort_keys=True))
    (output / "metrics.json").write_text(json.dumps(result, indent=2, sort_keys=True))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SCOPE-Static DEM fault-logit MVP experiments.")
    parser.add_argument("--config", required=True, help="Path to YAML config.")
    parser.add_argument("--output-dir", default=None, help="Optional output directory override.")
    args = parser.parse_args()
    result = run_experiment(args.config, output_dir=args.output_dir)
    print(json.dumps({k: result[k] for k in result if k != "records"}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
