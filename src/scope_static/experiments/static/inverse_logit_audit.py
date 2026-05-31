from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
import yaml

from scope_static.experiments.static.plan import ExperimentPlan
from scope_static.identifiability import deterministic_kmeans
from scope_static.dem.metrics import adjusted_rand_index, normalized_mutual_info
from scope_static.dem.multi_env import make_multi_env_teacher
from scope_static.numerics import NUMERICAL_ZERO


DISC13B_AUDIT = {
    "stage": "stage2A.2",
    "experiment": "DISC13b_inverse_logit_recovery_gap",
    "uses_hidden_omega_for_training": False,
    "uses_hidden_omega_for_initialization": False,
    "uses_hidden_omega_for_checkpoint_selection": False,
    "uses_hidden_omega_for_final_evaluation": True,
    "ari_nmi_used_for_selection": False,
}


def run_inverse_logit_audit(
    config_path: str | Path,
    *,
    output_dir: str | Path | None = None,
) -> dict[str, object]:
    plan = ExperimentPlan.from_path(config_path, output_dir=output_dir)
    cfg = dict(plan.config.get("disc13b", {}))
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
    local_logits = _load_local_logits(cfg, graph.M)
    oracle_logits = teacher.logits_by_env.to(dtype=torch.float64, device="cpu")
    local_matrix = _align_local_matrix(local_logits, oracle_logits.shape[1])
    oracle_features = _standardize_columns(oracle_logits)
    local_features = _standardize_columns(local_matrix)
    np.save(output / "oracle_logits.npy", oracle_logits.numpy())
    np.save(output / "local_logits.npy", local_matrix.numpy())

    oracle_cluster = deterministic_kmeans(oracle_features, graph.O)
    local_cluster = deterministic_kmeans(local_features, graph.O)
    linear = _linear_recovery_metrics(local_features, oracle_features)
    result = {
        **graph.audit_dict(
            exact_likelihood_trainable=bool(plan.training_cfg.get("exact_likelihood_trainable", False)),
            dem_fault_logit_claim=bool(plan.training_cfg.get("dem_fault_logit_claim", False)),
            cptp_gksl_claim=bool(plan.training_cfg.get("cptp_gksl_claim", False)),
        ),
        **plan.output_audit_dict(),
        **DISC13B_AUDIT,
        "schema": "scope_static_stage2a2_disc13b_inverse_logit_v1",
        "question": "Is the bottleneck local per-fault logit inversion or assignment learning on oracle-like logits?",
        "source_metrics_path": str(cfg.get("local_logit_metrics_path", "")),
        "oracle_logit_rank": _matrix_rank(oracle_features),
        "local_logit_rank": _matrix_rank(local_features),
        "oracle_logit_singular_values": _singular_values(oracle_features),
        "local_logit_singular_values": _singular_values(local_features),
        "corr_local_oracle": _mean_column_corr(local_features, oracle_features),
        "r2_local_to_oracle": linear["r2"],
        "linear_map_condition": linear["condition"],
        "ari_cluster_oracle_logit_vs_omega": adjusted_rand_index(oracle_cluster.labels, graph.orbit_ids),
        "nmi_cluster_oracle_logit_vs_omega": normalized_mutual_info(oracle_cluster.labels, graph.orbit_ids),
        "ari_cluster_local_logit_vs_omega": adjusted_rand_index(local_cluster.labels, graph.orbit_ids),
        "nmi_cluster_local_logit_vs_omega": normalized_mutual_info(local_cluster.labels, graph.orbit_ids),
        "ari_cluster_local_vs_oracle_logit": adjusted_rand_index(local_cluster.labels, oracle_cluster.labels),
        "nmi_cluster_local_vs_oracle_logit": normalized_mutual_info(local_cluster.labels, oracle_cluster.labels),
        "oracle_cluster_labels": [int(value) for value in oracle_cluster.labels.tolist()],
        "local_cluster_labels": [int(value) for value in local_cluster.labels.tolist()],
    }
    result["disc13b_conclusion"] = _disc13b_conclusion(result)
    _write_outputs(output, result)
    print(format_disc13b_terminal_summary(result))
    return result


def _load_local_logits(cfg: dict[str, object], num_faults: int) -> torch.Tensor:
    path = Path(str(cfg.get("local_logit_metrics_path", "outputs/scope_static/STAGE2A2_DISC12_multi_env/env_alpha.json")))
    if path.exists():
        data = json.loads(path.read_text())
        local = data.get("local_full_per_fault_per_env", {}).get("train")
        if local is None and isinstance(data.get("records"), list):
            for record in data["records"]:
                if record.get("model") == "local_full_per_fault_per_env":
                    local = record.get("env_alpha_train")
                    break
        if isinstance(local, dict) and local:
            rows = []
            for env in sorted(local, key=lambda value: int(value)):
                values = local[env]
                if isinstance(values, list) and len(values) == int(num_faults):
                    rows.append(torch.tensor(values, dtype=torch.float64))
            if rows:
                return torch.stack(rows, dim=1)
    raise ValueError(f"could not load local full per-fault env logits from {path}")


def _align_local_matrix(local_logits: torch.Tensor, num_oracle_envs: int) -> torch.Tensor:
    local = torch.as_tensor(local_logits, dtype=torch.float64, device="cpu")
    if local.ndim != 2:
        raise ValueError("local logits must have shape [M, E_local]")
    if local.shape[1] == int(num_oracle_envs):
        return local
    if local.shape[1] > int(num_oracle_envs):
        return local[:, : int(num_oracle_envs)]
    pad = local[:, -1:].expand(local.shape[0], int(num_oracle_envs) - local.shape[1])
    return torch.cat([local, pad], dim=1)


def _linear_recovery_metrics(local_features: torch.Tensor, oracle_features: torch.Tensor) -> dict[str, float | str]:
    x = torch.cat([local_features, torch.ones((local_features.shape[0], 1), dtype=torch.float64)], dim=1)
    y = oracle_features
    try:
        solution = torch.linalg.lstsq(x, y).solution
        pred = x @ solution
        ss_res = torch.sum((y - pred) ** 2)
        ss_tot = torch.sum((y - y.mean(dim=0, keepdim=True)) ** 2).clamp_min(NUMERICAL_ZERO)
        values = torch.linalg.svdvals(x)
        condition = float((values.max() / values.min().clamp_min(NUMERICAL_ZERO)).item()) if values.numel() else 0.0
        return {"r2": float((1.0 - ss_res / ss_tot).item()), "condition": condition}
    except RuntimeError:
        return {"r2": 0.0, "condition": "failed"}


def _disc13b_conclusion(result: dict[str, object]) -> str:
    oracle_ari = float(result["ari_cluster_oracle_logit_vs_omega"])
    local_ari = float(result["ari_cluster_local_logit_vs_omega"])
    local_vs_oracle = float(result["ari_cluster_local_vs_oracle_logit"])
    r2 = float(result["r2_local_to_oracle"])
    if oracle_ari >= 0.80 and local_ari < 0.50 and local_vs_oracle < 0.50:
        return "local_logit_inverse_gap_bottleneck"
    if oracle_ari >= 0.80 and r2 >= 0.80 and local_ari < 0.50:
        return "oracle_like_logits_linearly_present_but_clustering_assignment_fails"
    if oracle_ari >= 0.80 and local_ari >= 0.50:
        return "local_logits_contain_partial_target_signal"
    return "inverse_logit_audit_inconclusive"


def _standardize_columns(values: torch.Tensor) -> torch.Tensor:
    x = torch.as_tensor(values, dtype=torch.float64, device="cpu")
    x = x - x.mean(dim=0, keepdim=True)
    scale = x.std(dim=0, keepdim=True, unbiased=False).clamp_min(NUMERICAL_ZERO)
    return torch.nan_to_num(x / scale, nan=NUMERICAL_ZERO, posinf=NUMERICAL_ZERO, neginf=-NUMERICAL_ZERO)


def _mean_column_corr(left: torch.Tensor, right: torch.Tensor) -> float:
    cols = min(int(left.shape[1]), int(right.shape[1]))
    values = []
    for col in range(cols):
        a = left[:, col] - left[:, col].mean()
        b = right[:, col] - right[:, col].mean()
        denom = a.norm() * b.norm()
        values.append(float((a @ b / denom.clamp_min(NUMERICAL_ZERO)).item()))
    return float(sum(values) / len(values)) if values else 0.0


def _matrix_rank(values: torch.Tensor) -> int:
    return int(torch.linalg.matrix_rank(values).item())


def _singular_values(values: torch.Tensor) -> list[float]:
    try:
        return [float(value) for value in torch.linalg.svdvals(values).tolist()]
    except RuntimeError:
        return []


def _write_outputs(output: Path, result: dict[str, object]) -> None:
    (output / "metrics.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (output / "disc13b_summary.md").write_text(format_disc13b_summary_markdown(result))
    clusters = {
        "oracle_cluster_labels": result["oracle_cluster_labels"],
        "local_cluster_labels": result["local_cluster_labels"],
    }
    (output / "logit_clusters.json").write_text(json.dumps(clusters, indent=2, sort_keys=True) + "\n")


def format_disc13b_summary_markdown(result: dict[str, object]) -> str:
    lines = [
        "# DISC13b Inverse Logit Recovery Gap",
        "",
        f"- Conclusion: `{result['disc13b_conclusion']}`",
        f"- Corr local/oracle: `{_fmt(result['corr_local_oracle'])}`",
        f"- R2 local -> oracle: `{_fmt(result['r2_local_to_oracle'])}`",
        "",
        "| clustering target | ARI vs omega | NMI vs omega |",
        "| --- | ---: | ---: |",
        f"| oracle logits | {_fmt(result['ari_cluster_oracle_logit_vs_omega'])} | {_fmt(result['nmi_cluster_oracle_logit_vs_omega'])} |",
        f"| local logits | {_fmt(result['ari_cluster_local_logit_vs_omega'])} | {_fmt(result['nmi_cluster_local_logit_vs_omega'])} |",
        "",
        f"- ARI local cluster vs oracle cluster: `{_fmt(result['ari_cluster_local_vs_oracle_logit'])}`",
        f"- NMI local cluster vs oracle cluster: `{_fmt(result['nmi_cluster_local_vs_oracle_logit'])}`",
        "",
    ]
    return "\n".join(lines)


def format_disc13b_terminal_summary(result: dict[str, object]) -> str:
    return "\n".join(
        [
            "Stage 2A.2 DISC13b Inverse Logit Recovery Gap",
            f"config: {result.get('config_path')}",
            f"output: {result.get('output_dir')}",
            f"metrics: {Path(str(result.get('output_dir'))) / 'metrics.json'}",
            f"conclusion: {result['disc13b_conclusion']}",
            (
                "oracle cluster: "
                f"ARI={_fmt(result['ari_cluster_oracle_logit_vs_omega'])} "
                f"NMI={_fmt(result['nmi_cluster_oracle_logit_vs_omega'])}"
            ),
            (
                "local cluster:  "
                f"ARI={_fmt(result['ari_cluster_local_logit_vs_omega'])} "
                f"NMI={_fmt(result['nmi_cluster_local_logit_vs_omega'])}"
            ),
            f"corr={_fmt(result['corr_local_oracle'])} r2={_fmt(result['r2_local_to_oracle'])}",
        ]
    )


def _fmt(value: object) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.4g}"
    except (TypeError, ValueError):
        return str(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Stage 2A.2 DISC13b inverse-logit recovery gap audit.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args(argv)
    run_inverse_logit_audit(args.config, output_dir=args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
