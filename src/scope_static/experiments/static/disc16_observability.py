from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics

import numpy as np
import torch
import yaml

from scope_static.experiments.static.plan import ExperimentPlan
from scope_static.identifiability import deterministic_kmeans, evaluate_partition, random_baseline_summary, random_partition_baseline
from scope_static.dem.local_mechanism import local_probability_features, split_merge_audit
from scope_static.dem.metrics import normalized_mutual_info
from scope_static.dem.multi_env import MultiEnvLocalField, make_multi_env_teacher
from scope_static.dem.objectives import build_likelihood_objective
from scope_static.dem.stim_dem import sample_observations_from_logits


DISC16A_AUDIT = {
    "stage": "stage2D",
    "experiment": "DISC16a_shot_budget_sweep",
    "uses_hidden_omega_for_training": False,
    "uses_hidden_omega_for_initialization": False,
    "uses_hidden_omega_for_checkpoint_selection": False,
    "uses_hidden_omega_for_final_evaluation": True,
    "ari_nmi_used_for_selection": False,
    "candidate_selection": "disabled_predeclared_representation",
    "predeclared_representation": "local_logit_probability",
}


def run_disc16_observability(config_path: str | Path, *, output_dir: str | Path | None = None) -> dict[str, object]:
    plan = ExperimentPlan.from_path(config_path, output_dir=output_dir)
    cfg = dict(plan.config.get("disc16a", {}))
    multi_env_cfg = dict(plan.config.get("multi_env", {}))
    output = plan.output_dir
    output.mkdir(parents=True, exist_ok=True)
    (output / "config_snapshot.yaml").write_text(yaml.safe_dump(plan.config, sort_keys=False))

    graph = plan.build_graph(plan.teacher_residual_rank)
    teacher = make_multi_env_teacher(
        graph,
        seed=int(multi_env_cfg.get("teacher_seed", 0)),
        dtype=plan.dtype,
        contrast_strength=float(multi_env_cfg.get("contrast_strength", 1.0)),
        design=str(multi_env_cfg.get("environment_design", "default")),
    )
    train_env_ids = tuple(int(env) for env in cfg.get("train_env_ids", multi_env_cfg.get("train_env_ids", [0, 1, 2, 3])))
    shot_budgets = tuple(int(shots) for shots in cfg.get("shot_budgets", [25_000, 50_000, 100_000, 200_000, 500_000]))
    bootstrap_replicates = int(cfg.get("bootstrap_replicates", 2))
    heldout_shots = int(cfg.get("heldout_shots", plan.heldout_shots))
    steps = int(cfg.get("local_inverse_steps", plan.training_cfg.get("steps", 200)))
    lr = float(cfg.get("lr", plan.training_cfg.get("lr", 0.05)))
    k = int(cfg.get("num_clusters", graph.O))
    random_summary = random_baseline_summary(
        random_partition_baseline(graph.M, k, seed=int(cfg.get("random_baseline_seed", 0)), num_trials=int(cfg.get("random_baseline_trials", 32))),
        graph.orbit_ids,
    )
    heldout_observations = _sample_env_observations(
        graph,
        teacher.logits_by_env,
        shots=heldout_shots,
        seed_base=int(cfg.get("heldout_seed_base", 700_000)),
        env_ids=train_env_ids,
    )
    heldout_objectives = _build_objectives(plan, graph, heldout_observations, train_env_ids)

    shot_records = []
    cluster_audit = {}
    for shot_budget in shot_budgets:
        replicate_records = []
        probability_representations = []
        replicate_labels = []
        for replicate in range(bootstrap_replicates):
            observations = _sample_env_observations(
                graph,
                teacher.logits_by_env,
                shots=shot_budget,
                seed_base=int(cfg.get("sample_seed_base", 100_000)) + 10_000 * replicate + shot_budget,
                env_ids=train_env_ids,
            )
            fit = _fit_local_inverse(
                plan,
                graph,
                observations,
                train_env_ids=train_env_ids,
                steps=steps,
                lr=lr,
            )
            local_logits = fit["local_logits"]
            representation = local_probability_features(local_logits)
            clustering = deterministic_kmeans(representation, k)
            recovery = evaluate_partition(clustering.labels, graph.orbit_ids, num_clusters=k, random_baseline=random_summary)
            heldout_nll = _heldout_nll(heldout_objectives, local_logits, train_env_ids, device=plan.device)
            split_merge = split_merge_audit(clustering.labels, graph.orbit_ids)
            record = {
                "shots": int(shot_budget),
                "replicate": int(replicate),
                "train_final_nll": fit["train_final_nll"],
                "heldout_local_inverse_nll": heldout_nll,
                "ari": recovery["ari"],
                "nmi": recovery["nmi"],
                "active_clusters": recovery["active_clusters"],
                "cluster_masses": recovery["cluster_masses"],
                "dead_clusters": recovery["dead_clusters"],
                "within_cluster_dispersion": clustering.within_cluster_dispersion,
                "silhouette_like": clustering.silhouette_like,
                "cluster_mass_entropy_normalized": clustering.cluster_mass_entropy_normalized,
                "labels": [int(value) for value in clustering.labels.tolist()],
                **split_merge,
            }
            replicate_records.append(record)
            probability_representations.append(representation)
            replicate_labels.append(clustering.labels)
        summary = _shot_summary(int(shot_budget), replicate_records, probability_representations, replicate_labels)
        shot_records.append(summary)
        cluster_audit[str(shot_budget)] = {
            "primary_replicate": 0,
            "labels": replicate_records[0]["labels"],
            "cluster_masses": replicate_records[0]["cluster_masses"],
            "replicates": [
                {
                    "replicate": record["replicate"],
                    "ari": record["ari"],
                    "nmi": record["nmi"],
                    "active_clusters": record["active_clusters"],
                    "cluster_masses": record["cluster_masses"],
                    "mean_splits_per_omega": record["mean_splits_per_omega"],
                    "mean_cluster_purity": record["mean_cluster_purity"],
                }
                for record in replicate_records
            ],
        }

    conclusion = _disc16a_conclusion(shot_records)
    result = {
        **graph.audit_dict(
            exact_likelihood_trainable=bool(plan.training_cfg.get("exact_likelihood_trainable", False)),
            dem_fault_logit_claim=bool(plan.training_cfg.get("dem_fault_logit_claim", False)),
            cptp_gksl_claim=bool(plan.training_cfg.get("cptp_gksl_claim", False)),
        ),
        **plan.output_audit_dict(),
        **DISC16A_AUDIT,
        "schema": "scope_static_stage2d_disc16a_shot_budget_v1",
        "question": "Can more local inverse evidence turn DISC15c ARI 0.7923 into ARI >= 0.80?",
        "K_mode": "known_K_synthetic_audit",
        "teacher_env_names": list(teacher.env_names),
        "train_env_ids": [int(env) for env in train_env_ids],
        "shot_budgets": [int(value) for value in shot_budgets],
        "bootstrap_replicates": int(bootstrap_replicates),
        "heldout_shots": int(heldout_shots),
        "local_inverse_steps": int(steps),
        "strong_threshold": {"ari": 0.80, "nmi": 0.80},
        "random_partition_baseline": random_summary,
        "shot_sweep": shot_records,
        "cluster_audit": cluster_audit,
        "disc16a_result": conclusion,
    }
    _write_outputs(output, result)
    print(format_disc16a_terminal_summary(result))
    return result


def _sample_env_observations(graph, logits_by_env: torch.Tensor, *, shots: int, seed_base: int, env_ids: tuple[int, ...]) -> dict[int, torch.Tensor]:
    return {
        int(env): sample_observations_from_logits(
            graph,
            logits_by_env[:, int(env)],
            shots=int(shots),
            seed=int(seed_base) + int(env),
        )
        for env in env_ids
    }


def _build_objectives(plan: ExperimentPlan, graph, observations: dict[int, torch.Tensor], env_ids: tuple[int, ...]):
    return {
        int(env): build_likelihood_objective(
            graph,
            observations[int(env)],
            likelihood_objective=plan.likelihood_objective,
            observation_mode="full",
            aggregate_unique=plan.aggregate_unique,
            backend=plan.likelihood_backend,
            device=plan.device,
        )
        for env in env_ids
    }


def _fit_local_inverse(
    plan: ExperimentPlan,
    graph,
    observations: dict[int, torch.Tensor],
    *,
    train_env_ids: tuple[int, ...],
    steps: int,
    lr: float,
) -> dict[str, object]:
    field = MultiEnvLocalField(graph.M, len(train_env_ids), dtype=plan.dtype).to(device=plan.device)
    objectives = _build_objectives(plan, graph, observations, train_env_ids)
    optimizer = torch.optim.Adam(field.parameters(), lr=float(lr))
    history = []
    for _ in range(int(steps)):
        optimizer.zero_grad(set_to_none=True)
        losses = [
            objectives[int(env)].loss(field.realized_logits_for_env(slot))
            for slot, env in enumerate(train_env_ids)
        ]
        nll = torch.stack(losses).mean()
        nll.backward()
        optimizer.step()
        history.append(float(nll.detach().cpu()))
    local_logits = torch.stack(
        [field.realized_logits_for_env(slot).detach().cpu().to(dtype=torch.float64) for slot, _env in enumerate(train_env_ids)],
        dim=1,
    )
    return {"local_logits": local_logits, "train_final_nll": history[-1] if history else None}


def _heldout_nll(objectives: dict[int, object], local_logits: torch.Tensor, env_ids: tuple[int, ...], *, device: torch.device) -> float:
    losses = []
    for slot, env in enumerate(env_ids):
        logits = local_logits[:, slot].to(device=device)
        losses.append(float(objectives[int(env)].loss(logits).detach().cpu()))
    return float(sum(losses) / len(losses)) if losses else 0.0


def _shot_summary(
    shots: int,
    records: list[dict[str, object]],
    probability_representations: list[torch.Tensor],
    labels: list[torch.Tensor],
) -> dict[str, object]:
    summary = {
        "shots": int(shots),
        "replicates": records,
        "ari_mean": _mean(record["ari"] for record in records),
        "ari_std": _std(record["ari"] for record in records),
        "nmi_mean": _mean(record["nmi"] for record in records),
        "nmi_std": _std(record["nmi"] for record in records),
        "active_clusters_mean": _mean(record["active_clusters"] for record in records),
        "active_clusters_min": int(min(int(record["active_clusters"]) for record in records)),
        "heldout_local_inverse_nll_mean": _mean(record["heldout_local_inverse_nll"] for record in records),
        "heldout_local_inverse_nll_std": _std(record["heldout_local_inverse_nll"] for record in records),
        "bootstrap_label_pairwise_nmi": _pairwise_label_nmi(labels),
        "local_logit_probability_variance": _probability_variance(probability_representations),
        "primary_ari": float(records[0]["ari"]),
        "primary_nmi": float(records[0]["nmi"]),
        "primary_active_clusters": int(records[0]["active_clusters"]),
    }
    summary["strong_by_mean"] = bool(summary["ari_mean"] >= 0.80 and summary["nmi_mean"] >= 0.80)
    summary["strong_by_primary"] = bool(summary["primary_ari"] >= 0.80 and summary["primary_nmi"] >= 0.80)
    return summary


def _disc16a_conclusion(records: list[dict[str, object]]) -> str:
    if any(bool(record["strong_by_mean"]) for record in records):
        return "strong_recovery_by_predeclared_local_inverse_probability"
    ari_values = [float(record["ari_mean"]) for record in records]
    nmi_values = [float(record["nmi_mean"]) for record in records]
    if len(ari_values) >= 2 and ari_values[-1] < max(ari_values[:-1]) - 0.02:
        return "high_shot_decline_suggests_representation_or_clustering_bias"
    if _nondecreasing(ari_values, tolerance=0.01) and nmi_values[-1] >= 0.80:
        return "estimator_noise_part_of_bottleneck_but_not_sufficient"
    return "near_strong_stable_but_shot_budget_not_sufficient"


def _nondecreasing(values: list[float], *, tolerance: float) -> bool:
    return all(values[idx + 1] + float(tolerance) >= values[idx] for idx in range(len(values) - 1))


def _probability_variance(representations: list[torch.Tensor]) -> float:
    if len(representations) <= 1:
        return 0.0
    stacked = torch.stack([rep.to(dtype=torch.float64, device="cpu") for rep in representations], dim=0)
    return float(stacked.var(dim=0, unbiased=False).mean().item())


def _pairwise_label_nmi(labels: list[torch.Tensor]) -> float | None:
    values = []
    for left in range(len(labels)):
        for right in range(left + 1, len(labels)):
            values.append(float(normalized_mutual_info(labels[left], labels[right])))
    return _mean(values) if values else None


def _mean(values) -> float:
    numbers = [float(value) for value in values]
    return float(sum(numbers) / len(numbers)) if numbers else 0.0


def _std(values) -> float:
    numbers = [float(value) for value in values]
    if len(numbers) <= 1:
        return 0.0
    return float(statistics.stdev(numbers))


def _write_outputs(output: Path, result: dict[str, object]) -> None:
    (output / "metrics.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (output / "shot_sweep.json").write_text(json.dumps(result["shot_sweep"], indent=2, sort_keys=True) + "\n")
    (output / "cluster_audit.json").write_text(json.dumps(result["cluster_audit"], indent=2, sort_keys=True) + "\n")
    (output / "run_selection_audit.json").write_text(
        json.dumps(
            {
                "candidate_selection": result["candidate_selection"],
                "predeclared_representation": result["predeclared_representation"],
                "ari_nmi_used_for_selection": result["ari_nmi_used_for_selection"],
                "uses_hidden_omega_for_training": result["uses_hidden_omega_for_training"],
                "uses_hidden_omega_for_checkpoint_selection": result["uses_hidden_omega_for_checkpoint_selection"],
                "uses_hidden_omega_for_final_evaluation": result["uses_hidden_omega_for_final_evaluation"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    (output / "disc16a_summary.md").write_text(format_disc16a_summary(result))


def format_disc16a_summary(result: dict[str, object]) -> str:
    lines = [
        "# DISC16a Shot-Budget Sweep",
        "",
        f"- Result: `{result['disc16a_result']}`",
        f"- Predeclared representation: `{result['predeclared_representation']}`",
        f"- Candidate selection: `{result['candidate_selection']}`",
        f"- ARI/NMI used for selection: `{str(result['ari_nmi_used_for_selection']).lower()}`",
        "",
        "| shots | ARI mean | NMI mean | active min | boot NMI | prob var | heldout NLL | strong |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for record in result["shot_sweep"]:
        lines.append(
            f"| {record['shots']} | {_fmt(record['ari_mean'])} | {_fmt(record['nmi_mean'])} | "
            f"{record['active_clusters_min']} | {_fmt(record['bootstrap_label_pairwise_nmi'])} | "
            f"{_fmt(record['local_logit_probability_variance'])} | {_fmt(record['heldout_local_inverse_nll_mean'])} | "
            f"{str(record['strong_by_mean']).lower()} |"
        )
    lines.append("")
    return "\n".join(lines)


def format_disc16a_terminal_summary(result: dict[str, object]) -> str:
    lines = [
        "Stage 2D DISC16a Shot-Budget Sweep",
        f"config: {result.get('config_path')}",
        f"output: {result.get('output_dir')}",
        f"metrics: {Path(str(result.get('output_dir'))) / 'metrics.json'}",
        f"result: {result['disc16a_result']}",
        "shots      ARI     NMI     active  bootNMI  probVar    heldoutNLL  strong",
        "---------  ------  ------  ------  -------  ---------  ----------  ------",
    ]
    for record in result["shot_sweep"]:
        lines.append(
            f"{record['shots']:<9}  {_fmt(record['ari_mean']):<6}  {_fmt(record['nmi_mean']):<6}  "
            f"{record['active_clusters_min']:<6}  {_fmt(record['bootstrap_label_pairwise_nmi']):<7}  "
            f"{_fmt(record['local_logit_probability_variance']):<9}  {_fmt(record['heldout_local_inverse_nll_mean']):<10}  "
            f"{str(record['strong_by_mean']).lower()}"
        )
    return "\n".join(lines)


def _fmt(value: object) -> str:
    if value is None:
        return "-"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(number) < 1e-4 and number != 0.0:
        return f"{number:.3e}"
    return f"{number:.4g}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run DISC16a shot-budget sweep for local inverse observability.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args(argv)
    run_disc16_observability(args.config, output_dir=args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
