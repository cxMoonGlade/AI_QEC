from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
import yaml

from scope_static.experiments.plan import ExperimentPlan
from scope_static.identifiability import deterministic_kmeans
from scope_static.metrics import adjusted_rand_index, exact_observation_bit_rates, normalized_mutual_info
from scope_static.multi_env import make_multi_env_teacher


DISC13_AUDIT = {
    "stage": "stage2A.2",
    "experiment": "DISC13_observational_quotient_audit",
    "uses_hidden_omega_for_training": False,
    "uses_hidden_omega_for_initialization": False,
    "uses_hidden_omega_for_checkpoint_selection": False,
    "uses_hidden_omega_for_final_evaluation": True,
    "ari_nmi_used_for_selection": False,
}


def run_observational_quotient_audit(
    config_path: str | Path,
    *,
    output_dir: str | Path | None = None,
) -> dict[str, object]:
    plan = ExperimentPlan.from_path(config_path, output_dir=output_dir)
    cfg = dict(plan.config.get("disc13", {}))
    multi_env_cfg = dict(plan.config.get("multi_env", {}))
    output = plan.output_dir
    output.mkdir(parents=True, exist_ok=True)
    fingerprints_dir = output / "fingerprints"
    fingerprints_dir.mkdir(parents=True, exist_ok=True)
    (output / "config_snapshot.yaml").write_text(yaml.safe_dump(plan.config, sort_keys=False))

    graph = plan.build_graph(plan.teacher_residual_rank)
    teacher = make_multi_env_teacher(
        graph,
        seed=int(multi_env_cfg.get("teacher_seed", 0)),
        dtype=plan.dtype,
        contrast_strength=float(multi_env_cfg.get("contrast_strength", 1.0)),
        design=str(multi_env_cfg.get("environment_design", "default")),
    )
    primary_family = str(cfg.get("primary_observational_quotient_family", "observation_side"))
    fingerprints = build_disc13_fingerprints(graph, teacher.logits_by_env)
    quotient_records = []
    quotient_labels: dict[str, list[int]] = {}
    for family, features in fingerprints.items():
        np.save(fingerprints_dir / f"{family}.npy", features.numpy())
        result = deterministic_kmeans(features, graph.O)
        labels = [int(value) for value in result.labels.tolist()]
        quotient_labels[family] = labels
        quotient_records.append(
            {
                "fingerprint_family": family,
                "feature_dim": int(features.shape[1]),
                "observable_selection_score": float(result.observable_selection_score),
                "within_cluster_dispersion": float(result.within_cluster_dispersion),
                "active_clusters": int(result.active_clusters),
                "ari_obs_quotient_vs_hidden_omega": adjusted_rand_index(result.labels, graph.orbit_ids),
                "nmi_obs_quotient_vs_hidden_omega": normalized_mutual_info(result.labels, graph.orbit_ids),
                "labels": labels,
            }
        )

    learned_partitions = _load_learned_partitions(cfg)
    alignment_records = _target_alignment_records(
        learned_partitions,
        quotient_labels,
        graph.orbit_ids,
        primary_family=primary_family,
    )
    conclusion = _disc13_conclusion(alignment_records, quotient_records, primary_family=primary_family)
    result = {
        **graph.audit_dict(
            exact_likelihood_trainable=bool(plan.training_cfg.get("exact_likelihood_trainable", False)),
            dem_fault_logit_claim=bool(plan.training_cfg.get("dem_fault_logit_claim", False)),
            cptp_gksl_claim=bool(plan.training_cfg.get("cptp_gksl_claim", False)),
        ),
        **plan.output_audit_dict(),
        **DISC13_AUDIT,
        "schema": "scope_static_stage2a2_disc13_observational_quotient_v1",
        "question": "Is hidden teacher omega(j) the right recoverable target under the DEM/Bernoulli observation map?",
        "primary_observational_quotient_family": primary_family,
        "source_learned_partition_path": str(cfg.get("learned_partition_path", "")),
        "env_names": list(teacher.env_names),
        "quotient_records": quotient_records,
        "target_alignment": alignment_records,
        "disc13_conclusion": conclusion,
        "claim_boundary": (
            "DISC13 is evaluator-only. It audits target alignment and does not train, initialize, "
            "or select checkpoints with hidden omega(j)."
        ),
    }
    _write_disc13_outputs(output, result, quotient_labels)
    print(format_disc13_terminal_summary(result))
    return result


def build_disc13_fingerprints(graph, logits_by_env: torch.Tensor) -> dict[str, torch.Tensor]:
    logits = logits_by_env.detach().cpu().to(dtype=torch.float64)
    probs = torch.sigmoid(logits)
    support = _support_features(graph)
    observation = _observation_side_fingerprint(graph, logits)
    oracle_logit = torch.cat([logits, probs], dim=1)
    oracle_logit_support = torch.cat([oracle_logit, support], dim=1)
    combined = torch.cat([oracle_logit, observation, support], dim=1)
    return {
        "oracle_logit": _finite_2d(oracle_logit),
        "oracle_logit_support": _finite_2d(oracle_logit_support),
        "observation_side": _finite_2d(torch.cat([observation, support], dim=1)),
        "combined": _finite_2d(combined),
    }


def _observation_side_fingerprint(graph, logits_by_env: torch.Tensor) -> torch.Tensor:
    rows = []
    supports = graph.supports_by_fault
    detector_supports = [
        [bit for bit in support if bit < graph.num_detectors]
        for support in supports
    ]
    logical_supports = [
        [bit for bit in support if bit >= graph.num_detectors]
        for support in supports
    ]
    for env in range(int(logits_by_env.shape[1])):
        logits = logits_by_env[:, env]
        rates = exact_observation_bit_rates(graph, logits).detach().cpu().to(dtype=torch.float64)
        env_features = []
        for fault in range(graph.M):
            support = list(supports[fault])
            detector_bits = detector_supports[fault]
            logical_bits = logical_supports[fault]
            support_rates = rates[torch.tensor(support, dtype=torch.long)] if support else torch.empty((0,), dtype=torch.float64)
            detector_rates = (
                rates[torch.tensor(detector_bits, dtype=torch.long)] if detector_bits else torch.empty((0,), dtype=torch.float64)
            )
            logical_rates = (
                rates[torch.tensor(logical_bits, dtype=torch.long)] if logical_bits else torch.empty((0,), dtype=torch.float64)
            )
            env_features.append(
                torch.tensor(
                    [
                        float(torch.sigmoid(logits[fault]).item()),
                        _mean_tensor(support_rates),
                        _std_tensor(support_rates),
                        _max_tensor(support_rates),
                        _mean_tensor(detector_rates),
                        _mean_tensor(logical_rates),
                    ],
                    dtype=torch.float64,
                )
            )
        rows.append(torch.stack(env_features, dim=0))
    return torch.cat(rows, dim=1)


def _support_features(graph) -> torch.Tensor:
    dense = graph.A.to(dtype=torch.float64, device="cpu")
    detector = dense[: graph.num_detectors]
    logical = dense[graph.num_detectors :]
    detector_weight = detector.sum(dim=0)
    logical_weight = logical.sum(dim=0) if logical.numel() else torch.zeros(graph.M, dtype=torch.float64)
    total_weight = detector_weight + logical_weight
    features = [
        detector_weight,
        logical_weight,
        total_weight,
        detector_weight / max(1, graph.num_detectors),
        logical_weight / max(1, graph.num_observables),
    ]
    if graph.detector_coordinates is not None and graph.num_detectors:
        coords = graph.detector_coordinates.to(dtype=torch.float64, device="cpu")
        denom = detector_weight.clamp_min(1.0)
        for dim in range(coords.shape[1]):
            values = coords[:, dim].unsqueeze(1)
            mean_coord = (detector * values).sum(dim=0) / denom
            features.append(torch.where(detector_weight > 0, mean_coord, torch.zeros_like(mean_coord)))
    return _finite_2d(torch.stack(features, dim=1))


def _load_learned_partitions(cfg: dict[str, object]) -> dict[str, list[int]]:
    path = Path(str(cfg.get("learned_partition_path", "outputs/scope_static/STAGE2A2_DISC12_multi_env/shared_assignment.json")))
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    partitions = {}
    for model, payload in data.items():
        labels = payload.get("hard_assignment_labels") if isinstance(payload, dict) else None
        if labels:
            partitions[str(model)] = [int(value) for value in labels]
    return partitions


def _target_alignment_records(
    learned_partitions: dict[str, list[int]],
    quotient_labels: dict[str, list[int]],
    omega: torch.Tensor,
    *,
    primary_family: str,
) -> list[dict[str, object]]:
    records = []
    hidden = torch.as_tensor(omega, dtype=torch.long)
    for learned_name, learned_labels in learned_partitions.items():
        learned = torch.as_tensor(learned_labels, dtype=torch.long)
        learned_vs_hidden_ari = adjusted_rand_index(learned, hidden)
        learned_vs_hidden_nmi = normalized_mutual_info(learned, hidden)
        for family, labels in quotient_labels.items():
            obs = torch.as_tensor(labels, dtype=torch.long)
            records.append(
                {
                    "learned_partition": learned_name,
                    "observational_quotient_family": family,
                    "is_primary_family": family == primary_family,
                    "ari_learned_vs_hidden_omega": learned_vs_hidden_ari,
                    "nmi_learned_vs_hidden_omega": learned_vs_hidden_nmi,
                    "ari_observational_quotient_vs_hidden_omega": adjusted_rand_index(obs, hidden),
                    "nmi_observational_quotient_vs_hidden_omega": normalized_mutual_info(obs, hidden),
                    "ari_learned_vs_observational_quotient": adjusted_rand_index(learned, obs),
                    "nmi_learned_vs_observational_quotient": normalized_mutual_info(learned, obs),
                    "ari_alignment_gap_obs_minus_hidden": adjusted_rand_index(learned, obs) - learned_vs_hidden_ari,
                    "nmi_alignment_gap_obs_minus_hidden": normalized_mutual_info(learned, obs) - learned_vs_hidden_nmi,
                }
            )
    return records


def _disc13_conclusion(
    alignment_records: list[dict[str, object]],
    quotient_records: list[dict[str, object]],
    *,
    primary_family: str,
) -> str:
    primary = [record for record in alignment_records if bool(record.get("is_primary_family"))]
    if any(
        float(record["ari_alignment_gap_obs_minus_hidden"]) >= 0.10
        and float(record["nmi_alignment_gap_obs_minus_hidden"]) >= 0.05
        for record in primary
    ):
        return "target_mismatch_confirmed_learned_aligns_better_with_observational_quotient"
    if primary:
        return "target_mismatch_not_confirmed_learned_not_meaningfully_closer_to_observational_quotient"
    primary_quotient = next(
        (record for record in quotient_records if record["fingerprint_family"] == primary_family),
        None,
    )
    if primary_quotient is not None:
        if (
            float(primary_quotient["ari_obs_quotient_vs_hidden_omega"]) >= 0.80
            and float(primary_quotient["nmi_obs_quotient_vs_hidden_omega"]) >= 0.80
        ):
            return "target_mismatch_not_confirmed_observational_quotient_matches_hidden_omega"
    if primary:
        return "target_alignment_inconclusive"
    return "target_alignment_not_evaluated_no_learned_partitions"


def _write_disc13_outputs(output: Path, result: dict[str, object], quotient_labels: dict[str, list[int]]) -> None:
    (output / "metrics.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (output / "disc13_summary.md").write_text(format_disc13_summary_markdown(result))
    (output / "observational_quotient.json").write_text(json.dumps(quotient_labels, indent=2, sort_keys=True) + "\n")
    (output / "target_alignment.json").write_text(
        json.dumps({"target_alignment": result["target_alignment"]}, indent=2, sort_keys=True) + "\n"
    )


def format_disc13_summary_markdown(result: dict[str, object]) -> str:
    lines = [
        "# DISC13 Observational Quotient Audit",
        "",
        f"- Conclusion: `{result['disc13_conclusion']}`",
        f"- Primary quotient family: `{result['primary_observational_quotient_family']}`",
        f"- ARI/NMI used for selection: `{str(result['ari_nmi_used_for_selection']).lower()}`",
        "",
        "## Observational Quotients",
        "",
        "| family | dim | active | ARI vs omega | NMI vs omega |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for record in result["quotient_records"]:
        lines.append(
            f"| {record['fingerprint_family']} | {record['feature_dim']} | {record['active_clusters']} | "
            f"{_fmt(record['ari_obs_quotient_vs_hidden_omega'])} | {_fmt(record['nmi_obs_quotient_vs_hidden_omega'])} |"
        )
    lines.extend(
        [
            "",
            "## Target Alignment",
            "",
            "| learned | quotient | ARI learned/omega | ARI learned/obs | gap | NMI learned/omega | NMI learned/obs |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for record in result["target_alignment"]:
        if not bool(record["is_primary_family"]):
            continue
        lines.append(
            f"| {record['learned_partition']} | {record['observational_quotient_family']} | "
            f"{_fmt(record['ari_learned_vs_hidden_omega'])} | {_fmt(record['ari_learned_vs_observational_quotient'])} | "
            f"{_fmt(record['ari_alignment_gap_obs_minus_hidden'])} | {_fmt(record['nmi_learned_vs_hidden_omega'])} | "
            f"{_fmt(record['nmi_learned_vs_observational_quotient'])} |"
        )
    lines.append("")
    return "\n".join(lines)


def format_disc13_terminal_summary(result: dict[str, object]) -> str:
    lines = [
        "Stage 2A.2 DISC13 Observational Quotient Audit",
        f"config: {result.get('config_path')}",
        f"output: {result.get('output_dir')}",
        f"metrics: {Path(str(result.get('output_dir'))) / 'metrics.json'}",
        f"conclusion: {result['disc13_conclusion']}",
        "",
        "family                ARI_obs_omega  NMI_obs_omega  active",
        "--------------------  -------------  -------------  ------",
    ]
    for record in result["quotient_records"]:
        lines.append(
            f"{record['fingerprint_family']:<20}  {_fmt(record['ari_obs_quotient_vs_hidden_omega']):>13}  "
            f"{_fmt(record['nmi_obs_quotient_vs_hidden_omega']):>13}  {record['active_clusters']:>6}"
        )
    return "\n".join(lines)


def _mean_tensor(values: torch.Tensor) -> float:
    return float(values.mean().item()) if values.numel() else 0.0


def _std_tensor(values: torch.Tensor) -> float:
    return float(values.std(unbiased=False).item()) if values.numel() else 0.0


def _max_tensor(values: torch.Tensor) -> float:
    return float(values.max().item()) if values.numel() else 0.0


def _finite_2d(values: torch.Tensor) -> torch.Tensor:
    result = torch.as_tensor(values, dtype=torch.float64, device="cpu")
    if result.ndim != 2:
        raise ValueError("fingerprint matrix must have shape [M, F]")
    return torch.nan_to_num(result, nan=0.0, posinf=0.0, neginf=0.0)


def _fmt(value: object) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.4g}"
    except (TypeError, ValueError):
        return str(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Stage 2A.2 DISC13 observational quotient audit.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args(argv)
    run_observational_quotient_audit(args.config, output_dir=args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
