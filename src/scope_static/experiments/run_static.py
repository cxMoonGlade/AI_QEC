from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
import yaml

from scope_static.baselines import baseline_metadata
from scope_static.fields import make_field
from scope_static.metrics import compression_ratio, evaluate_model, shots_to_threshold
from scope_static.stim_dem import build_surface_code_graph, sample_observations_from_logits
from scope_static.teachers import make_teacher_logits
from scope_static.training import fit_field


def _dtype_from_config(name: str) -> torch.dtype:
    if name == "float32":
        return torch.float32
    if name == "float64":
        return torch.float64
    raise ValueError(f"unsupported dtype {name!r}")


def _device_from_config(name: str) -> torch.device:
    if name == "cuda" and not torch.cuda.is_available():
        return torch.device("cpu")
    return torch.device(name)


def _residual_ranks_from_config(graph_cfg: dict[str, object]) -> list[int]:
    if "residual_ranks" in graph_cfg:
        ranks = [int(rank) for rank in graph_cfg["residual_ranks"]]
    else:
        ranks = [int(graph_cfg.get("residual_rank", 0))]
    if not ranks:
        raise ValueError("graph.residual_ranks must not be empty")
    if any(rank < 0 for rank in ranks):
        raise ValueError("residual ranks must be non-negative")
    return ranks


def _build_graph_for_rank(
    circuit_cfg: dict[str, object],
    graph_cfg: dict[str, object],
    residual_rank: int,
):
    return build_surface_code_graph(
        family=circuit_cfg.get("family", "surface_code:rotated_memory_x"),
        distance=int(circuit_cfg.get("distance", 3)),
        rounds=int(circuit_cfg.get("rounds", 1)),
        noise=circuit_cfg.get("noise", {}),
        residual_rank=int(residual_rank),
        canonicalize_duplicate_masks=bool(graph_cfg.get("canonicalize_duplicate_masks", True)),
    )


def run_experiment(config_path: str | Path, *, output_dir: str | Path | None = None) -> dict[str, object]:
    config_path = Path(config_path)
    config = yaml.safe_load(config_path.read_text())
    run_cfg = config.get("run", {})
    circuit_cfg = config["circuit"]
    graph_cfg = config["graph"]
    experiment_cfg = config["experiment"]
    training_cfg = config["training"]

    dtype = _dtype_from_config(run_cfg.get("dtype", "float64"))
    device = _device_from_config(run_cfg.get("device", "cpu"))
    output = Path(output_dir or run_cfg.get("output_dir", "outputs/scope_static/run"))
    output.mkdir(parents=True, exist_ok=True)

    residual_ranks = _residual_ranks_from_config(graph_cfg)
    teacher_residual_rank = int(experiment_cfg.get("teacher_residual_rank", max(residual_ranks)))
    graph_cache = {
        rank: _build_graph_for_rank(circuit_cfg, graph_cfg, rank)
        for rank in sorted(set(residual_ranks + [teacher_residual_rank]))
    }
    teacher_graph = graph_cache[teacher_residual_rank]
    graph_runs = [(rank, graph_cache[rank]) for rank in residual_ranks]
    for rank, graph in graph_runs:
        if not torch.equal(graph.A, teacher_graph.A):
            raise ValueError(f"rank {rank} graph parity matrix differs from teacher rank {teacher_residual_rank}")
    audits = []
    for rank, graph in graph_runs:
        audit = graph.audit_dict(
            exact_likelihood_trainable=bool(training_cfg.get("exact_likelihood_trainable", False)),
            dem_fault_logit_claim=bool(training_cfg.get("dem_fault_logit_claim", False)),
            cptp_gksl_claim=bool(training_cfg.get("cptp_gksl_claim", False)),
        )
        audit["residual_rank"] = int(rank)
        audits.append(audit)
    graph_audit_payload: dict[str, object]
    if len(audits) == 1:
        graph_audit_payload = audits[0]
    else:
        graph_audit_payload = {
            "residual_ranks": [int(rank) for rank in residual_ranks],
            "teacher_residual_rank": int(teacher_residual_rank),
            "graph_audits": audits,
        }
    likelihood_backend = str(training_cfg.get("likelihood_backend", "auto"))

    records: list[dict[str, object]] = []
    for seed in experiment_cfg.get("seeds", [0]):
        for teacher_mode in experiment_cfg.get("teacher_modes", ["exact_orbit"]):
            for epsilon_break in experiment_cfg.get("epsilon_breaks", [0.0]):
                teacher_logits = make_teacher_logits(
                    teacher_graph,
                    mode=teacher_mode,
                    epsilon_break=float(epsilon_break),
                    seed=int(seed),
                    dtype=dtype,
                )
                heldout = sample_observations_from_logits(
                    teacher_graph,
                    teacher_logits,
                    shots=int(experiment_cfg.get("heldout_shots", 2048)),
                    seed=int(seed) + 10_000,
                )
                train_observations_by_shots = {
                    int(shots): sample_observations_from_logits(
                        teacher_graph,
                        teacher_logits,
                        shots=int(shots),
                        seed=int(seed) + int(shots),
                    )
                    for shots in experiment_cfg.get("shot_budgets", [128])
                }
                for residual_rank, graph in graph_runs:
                    local_parameter_count = graph.M
                    feature_audit = graph.residual_feature_audit_dict()
                    for shots, train_obs in train_observations_by_shots.items():
                        for model_name in training_cfg.get("models", ["local", "hard_orbit", "soft_feature_orbit"]):
                            observation_mode = "detectors" if model_name == "dmle_qec" else "full"
                            model_options = training_cfg.get("model_options", {}).get(model_name, {})
                            regularization_weight = 0.0
                            if model_name == "soft_feature_orbit":
                                regularization_weight = float(
                                    model_options.get(
                                        "beta_l2",
                                        training_cfg.get("soft_beta_l2", 0.0),
                                    )
                                )
                            field = make_field(
                                model_name,
                                graph,
                                dtype=dtype,
                                seed=int(seed),
                                model_options=model_options,
                            )
                            fit = fit_field(
                                graph,
                                field,
                                train_obs,
                                steps=int(training_cfg.get("steps", 200)),
                                lr=float(training_cfg.get("lr", 0.05)),
                                aggregate_unique=bool(training_cfg.get("aggregate_unique", True)),
                                device=device,
                                backend=likelihood_backend,
                                observation_mode=observation_mode,
                                regularization_weight=regularization_weight,
                            )
                            fitted_field = fit["field"]
                            logits = fitted_field.realized_logits(graph)
                            metrics = evaluate_model(
                                graph,
                                logits,
                                teacher_logits.to(device=logits.device, dtype=logits.dtype),
                                heldout,
                                aggregate_unique=bool(training_cfg.get("aggregate_unique", True)),
                                backend=likelihood_backend,
                            )
                            record = {
                                "seed": int(seed),
                                "teacher_mode": teacher_mode,
                                "teacher_residual_rank": int(teacher_residual_rank),
                                "epsilon_break": float(epsilon_break),
                                "shots": int(shots),
                                "model": model_name,
                                "residual_rank": int(residual_rank),
                                "parameter_count": int(fitted_field.parameter_count),
                                "compression_ratio_vs_local": compression_ratio(
                                    local_parameter_count,
                                    int(fitted_field.parameter_count),
                                ),
                                "train_initial_nll": fit["history"][0] if fit["history"] else None,
                                "train_final_nll": fit["history"][-1] if fit["history"] else None,
                                "train_requested_likelihood_backend": fit["requested_backend"],
                                "train_resolved_likelihood_backend": fit["resolved_backend"],
                                "train_observation_mode": fit["observation_mode"],
                                "train_regularization_weight": fit["regularization_weight"],
                                "num_orbits_with_nonzero_centered_feature_rank": feature_audit[
                                    "num_orbits_with_nonzero_centered_feature_rank"
                                ],
                                "mean_centered_feature_rank": feature_audit["mean_centered_feature_rank"],
                                "max_centered_feature_rank": feature_audit["max_centered_feature_rank"],
                                "selected_feature_indices": feature_audit["selected_feature_indices"],
                            }
                            record.update(baseline_metadata(model_name))
                            record.update(metrics)
                            records.append(record)

    thresholds = shots_to_threshold(
        records,
        threshold_epsilon=float(experiment_cfg.get("threshold_epsilon", 0.01)),
        seed_policy=str(experiment_cfg.get("threshold_seed_policy", "mean")),
    )
    threshold_records = [
        {
            "model": key[0],
            "teacher_mode": key[1],
            "epsilon_break": key[2],
            "residual_rank": key[3],
            **value,
        }
        for key, value in thresholds.items()
    ]
    result = {
        **audits[0],
        "config_path": str(config_path),
        "residual_ranks": [int(rank) for rank in residual_ranks],
        "teacher_residual_rank": int(teacher_residual_rank),
        "graph_audits": audits,
        "requested_likelihood_backend": likelihood_backend,
        "records": records,
        "shots_to_threshold": threshold_records,
    }
    (output / "config_snapshot.yaml").write_text(yaml.safe_dump(config, sort_keys=False))
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
