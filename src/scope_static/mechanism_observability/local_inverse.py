from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import numpy as np
import torch

from scope_static.identifiability import (
    deterministic_kmeans,
    evaluate_partition,
    random_baseline_summary,
    random_partition_baseline,
    standardize_features,
)
from scope_static.dem.local_mechanism import split_merge_audit
from scope_static.dem.metrics import normalized_mutual_info
from scope_static.numerics import NUMERICAL_ZERO

from scope_static.primitives.channels import MechanismSpec
from scope_static.primitives.ptm import channel_fingerprint, probe_response_fingerprint, rzz_type_feature_vector


DEFAULT_LOCAL_INVERSE_CONFIG: dict[str, object] = {
    "predeclared_representation": "physical_local_inverse_probability",
    "num_clusters": None,
    "random_baseline_seed": 0,
    "random_baseline_trials": 64,
    "bootstrap_replicates": 16,
    "heldout_fraction": 0.25,
    "seed": 0,
    "paper_informed_ptm_features": True,
}


def run_physical_local_inverse_discovery(
    *,
    teacher_dir: str | Path = "outputs/scope_static/S2D_PHYS1_teacher",
    separability_dir: str | Path = "outputs/scope_static/S2D_PHYS2_oracle_separability",
    output_dir: str | Path = "outputs/scope_static/S2D_PHYS3_local_inverse",
    config: dict[str, object] | None = None,
) -> dict[str, object]:
    cfg = _merged_config(config)
    teacher = Path(teacher_dir)
    separability = Path(separability_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    records = _load_mechanism_records(teacher / "oracle_mechanisms.json")
    observations, probe_names, shots = _load_observations(teacher / "observations.npz")
    hidden_labels, label_names = _encode_labels([str(record["oracle_label"]) for record in records])
    k, k_source = _num_clusters(cfg, label_names)
    train_observations, heldout_observations = _train_heldout_observations(
        observations,
        seed=int(cfg.get("seed", 0)),
        heldout_fraction=float(cfg.get("heldout_fraction", 0.25)),
    )

    train_bundle = build_visible_location_representations(records, train_observations, probe_names)
    heldout_bundle = build_visible_location_representations(records, heldout_observations, probe_names)
    full_bundle = build_visible_location_representations(records, observations, probe_names)
    np.save(output / "local_inverse_probabilities.npy", full_bundle["physical_local_inverse_probability"])

    random_labels = random_partition_baseline(
        len(records),
        k,
        seed=int(cfg.get("random_baseline_seed", 0)),
        num_trials=int(cfg.get("random_baseline_trials", 64)),
    )
    random_summary = random_baseline_summary(random_labels, hidden_labels)
    response_train = train_bundle["response_target"]
    response_heldout = heldout_bundle["response_target"]

    comparisons: list[dict[str, object]] = [
        _random_partition_record(
            random_labels,
            hidden_labels,
            k,
            response_train=response_train,
            response_heldout=response_heldout,
        )
    ]
    candidate_specs = [
        ("structural_only_features", "deterministic_kmeans", train_bundle["structural_only_features"]),
        ("raw_observation_probe_summary", "deterministic_kmeans", train_bundle["raw_observation_probe_summary"]),
        ("direct_S_alpha_assignment", "deterministic_kmeans", train_bundle["direct_S_alpha_assignment"]),
        ("raw_local_inverse_logits", "deterministic_kmeans", train_bundle["raw_local_inverse_logits"]),
    ]
    for name, method, features in candidate_specs:
        clustering = deterministic_kmeans(torch.as_tensor(features, dtype=torch.float64), k)
        comparisons.append(
            _comparison_record(
                name,
                method,
                clustering.labels,
                hidden_labels,
                k,
                features=features,
                response_train=response_train,
                response_heldout=response_heldout,
                random_summary=random_summary,
            )
        )

    main_features = train_bundle["physical_local_inverse_probability"]
    main_labels = _visible_operation_aware_local_inverse_labels(main_features, records, k)
    main_record = _comparison_record(
        "physical_local_inverse_probability",
        "visible_operation_aware_local_inverse_clustering",
        torch.as_tensor(main_labels, dtype=torch.long),
        hidden_labels,
        k,
        features=main_features,
        response_train=response_train,
        response_heldout=response_heldout,
        random_summary=random_summary,
    )
    comparisons.append(main_record)

    v2_features = train_bundle["physical_local_inverse_probability_v2"]
    v2_labels = _visible_operation_aware_local_inverse_labels(v2_features, records, k)
    v2_record = _comparison_record(
        "physical_local_inverse_probability_v2",
        "visible_operation_aware_local_inverse_clustering_v2",
        torch.as_tensor(v2_labels, dtype=torch.long),
        hidden_labels,
        k,
        features=v2_features,
        response_train=response_train,
        response_heldout=response_heldout,
        random_summary=random_summary,
    )
    comparisons.append(v2_record)

    oracle_record = _oracle_fingerprint_upper_bound_record(
        records,
        hidden_labels,
        label_names,
        k,
        separability_dir=separability,
        paper_informed=bool(cfg.get("paper_informed_ptm_features", True)),
        response_train=response_train,
        response_heldout=response_heldout,
    )
    comparisons.append(oracle_record)

    bootstrap = _bootstrap_nmi(
        records,
        observations,
        probe_names,
        reference_labels=[int(value) for value in main_record["labels"]],
        k=k,
        seed=int(cfg.get("seed", 0)),
        replicates=int(cfg.get("bootstrap_replicates", 16)),
    )
    direct_record = _find_comparison(comparisons, "direct_S_alpha_assignment")
    key_comparison = {
        "direct_S_alpha": _compact_comparison(direct_record),
        "physical_local_inverse_probability": _compact_comparison(main_record),
        "physical_local_inverse_probability_v2": _compact_comparison(v2_record),
        "local_inverse_beats_direct": bool(
            float(main_record["ari"]) > float(direct_record["ari"])
            and float(main_record["nmi"]) > float(direct_record["nmi"])
        ),
    }
    nll_difficulty = _nll_difficulty_audit(
        response_train=response_train,
        response_heldout=response_heldout,
        local_inverse_record=main_record,
        direct_record=direct_record,
        oracle_record=oracle_record,
    )
    separability_metrics = _load_separability_metrics(separability)
    run_selection_audit = _run_selection_audit(cfg, k_source)
    result_label = _acceptance_label(
        main_record,
        oracle_record,
        bootstrap,
        separability_metrics,
        no_oracle_leakage=not bool(run_selection_audit["oracle_labels_used_for_training_or_selection"]),
        k=k,
    )
    confusion = {
        "comparison": "physical_local_inverse_probability",
        "oracle_label_names": label_names,
        "predicted_cluster_ids": list(range(k)),
        "matrix": _confusion_matrix([int(value) for value in main_record["labels"]], hidden_labels.tolist(), num_pred=k, num_true=len(label_names)),
    }
    metrics = {
        "schema": "scope_static_s2d_phys3_local_inverse_v1",
        "stage": "S2D_PHYS3_local_inverse",
        "question": (
            "Can the local-inverse-first learner recover oracle physical mechanism labels from generated "
            "physical observations without oracle labels for training, initialization, or selection?"
        ),
        "teacher_dir": str(teacher),
        "separability_dir": str(separability),
        "output_dir": str(output),
        "num_locations": len(records),
        "num_probes": int(observations.shape[0]),
        "num_qubits": int(observations.shape[2]),
        "shots": int(shots),
        "train_shots": int(train_observations.shape[1]),
        "heldout_shots": int(heldout_observations.shape[1]),
        "oracle_label_names": label_names,
        "known_K_synthetic_audit": True,
        "num_clusters": int(k),
        "num_clusters_source": k_source,
        "predeclared_representation": str(cfg.get("predeclared_representation")),
        "ari_nmi_used_for_selection": False,
        "selection_rule": "predeclared_physical_local_inverse_probability_no_ari_nmi_selection",
        "main_result": _compact_comparison(main_record),
        "physical_local_inverse_probability_v2_result": _compact_comparison(v2_record),
        "direct_S_alpha_result": _compact_comparison(direct_record),
        "oracle_fingerprint_upper_bound": _compact_comparison(oracle_record),
        "key_comparison": key_comparison,
        "prediction_metrics": _prediction_metrics(
            local_inverse_record=main_record,
            local_inverse_v2_record=v2_record,
            direct_record=direct_record,
            oracle_record=oracle_record,
        ),
        "nll_difficulty_audit": nll_difficulty,
        "bootstrap_nmi": bootstrap,
        "s2d3_result": result_label,
        "acceptance_label": result_label,
        "random_partition_baseline": random_summary,
        "oracle_separability_gate": separability_metrics.get("separability_gate"),
        "oracle_separability_ari": separability_metrics.get("ari"),
        "oracle_separability_nmi": separability_metrics.get("nmi"),
        "response_source": "physical_probe_bit_and_parity_response_not_dem_detector_bits",
        "comparisons": comparisons,
        "confusion_matrix": confusion["matrix"],
        "run_selection_audit": run_selection_audit,
    }
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n")
    (output / "clusters.json").write_text(json.dumps(_clusters_artifact(comparisons, label_names), indent=2, sort_keys=True) + "\n")
    (output / "confusion_matrix.json").write_text(json.dumps(confusion, indent=2, sort_keys=True) + "\n")
    (output / "run_selection_audit.json").write_text(json.dumps(run_selection_audit, indent=2, sort_keys=True) + "\n")
    (output / "summary.md").write_text(format_local_inverse_summary(metrics))
    return metrics


def build_visible_location_representations(
    records: list[dict[str, object]],
    observations: np.ndarray,
    probe_names: Iterable[str],
) -> dict[str, np.ndarray]:
    obs = _validate_observations(observations)
    names = [str(name) for name in probe_names]
    if len(names) != int(obs.shape[0]):
        raise ValueError("probe_names length must match observations")
    num_qubits = int(obs.shape[2])
    instructions = _instruction_names(records)
    bit_rates = obs.mean(axis=1)
    structural_rows = []
    raw_rows = []
    direct_rows = []
    probability_rows = []
    v2_rows = []
    eps = 1e-4
    for record in records:
        qubits = _record_qubits(record, num_qubits)
        probe_indices = _record_probe_indices(record, obs)
        local_obs = obs[probe_indices]
        local_bit_rates = bit_rates[probe_indices]
        local_probe_names = [names[idx] for idx in probe_indices]
        inst = _instruction_one_hot(record, instructions)
        support = np.zeros(num_qubits, dtype=np.float64)
        support[qubits] = 1.0
        local_response = _local_response_features(local_obs, local_bit_rates, qubits)
        clipped = np.clip(local_response, eps, 1.0 - eps)
        logits = np.log(clipped / (1.0 - clipped))
        centered = np.abs(local_response - 0.5)
        structural = np.concatenate(
            [
                inst,
                np.array(
                    [
                        len(qubits) / max(1.0, min(2.0, float(num_qubits))),
                        float(np.mean(qubits)) / max(1.0, float(num_qubits - 1)),
                        float(max(qubits) - min(qubits)) / max(1.0, float(num_qubits - 1)),
                    ],
                    dtype=np.float64,
                ),
                support,
            ]
        )
        direct = np.concatenate(
            [
                inst,
                np.array(
                    [
                        float(np.mean(logits)),
                        float(np.std(logits)),
                        len(qubits) / max(1.0, min(2.0, float(num_qubits))),
                        float(np.mean(qubits)) / max(1.0, float(num_qubits - 1)),
                    ],
                    dtype=np.float64,
                ),
            ]
        )
        probability = np.concatenate(
            [
                local_response,
                1.0 - local_response,
                centered,
                _probe_axis_summary(local_response, local_probe_names),
                inst,
                np.array([1.0 if str(record.get("instruction")) == "measure" else 0.0], dtype=np.float64),
            ]
        )
        v2 = np.concatenate(
            [
                probability,
                local_response,
                _basis_response_differences(local_response, local_probe_names),
                _response_entropy_variance_features(local_response),
                _learner_visible_rzz_type_proxy(record, local_response, local_probe_names),
                structural,
            ]
        )
        structural_rows.append(structural)
        raw_rows.append(local_response)
        direct_rows.append(direct)
        probability_rows.append(probability)
        v2_rows.append(v2)

    raw = _finite(np.stack(raw_rows, axis=0))
    logits = _finite(np.log(np.clip(raw, eps, 1.0 - eps) / (1.0 - np.clip(raw, eps, 1.0 - eps))))
    return {
        "structural_only_features": _finite(np.stack(structural_rows, axis=0)),
        "raw_observation_probe_summary": raw,
        "direct_S_alpha_assignment": _finite(np.stack(direct_rows, axis=0)),
        "raw_local_inverse_logits": logits,
        "physical_local_inverse_probability": _finite(np.stack(probability_rows, axis=0)),
        "physical_local_inverse_probability_v2": _finite(np.stack(v2_rows, axis=0)),
        "response_target": raw,
    }


def format_local_inverse_summary(metrics: dict[str, object]) -> str:
    main = metrics["main_result"]
    v2 = metrics.get("physical_local_inverse_probability_v2_result")
    direct = metrics["direct_S_alpha_result"]
    upper = metrics["oracle_fingerprint_upper_bound"]
    lines = [
        "# S2D PHYS3 Local Inverse Discovery",
        "",
        f"- Result: `{metrics['s2d3_result']}`",
        f"- Predeclared representation: `{metrics['predeclared_representation']}`",
        f"- ARI/NMI used for selection: `{str(bool(metrics['ari_nmi_used_for_selection'])).lower()}`",
        f"- Oracle separability gate: `{metrics.get('oracle_separability_gate')}`",
        f"- NLL difficulty: `{metrics['nll_difficulty_audit']['response_task_classification']}`",
        "",
        "| comparison | ARI | NMI | active | heldout NLL | response MAE | boot/notes |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
        _summary_row(direct, "direct_S_alpha_assignment", ""),
        _summary_row(main, "physical_local_inverse_probability", f"bootstrap min {float(metrics['bootstrap_nmi']['min_vs_full']):.4f}"),
        _summary_row(v2, "physical_local_inverse_probability_v2", "") if isinstance(v2, dict) else "",
        _summary_row(upper, "oracle_fingerprint_upper_bound", "evaluator-only"),
        "",
        "## All Comparisons",
        "",
        "| comparison | method | ARI | NMI | active | cluster masses |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for record in metrics["comparisons"]:  # type: ignore[index]
        lines.append(
            f"| {record['comparison']} | {record['method']} | {_fmt(record['ari'])} | {_fmt(record['nmi'])} | "
            f"{record['active_clusters']} | `{record['cluster_masses']}` |"
        )
    lines.append("")
    return "\n".join(lines)


def _comparison_record(
    name: str,
    method: str,
    labels: torch.Tensor,
    hidden_labels: torch.Tensor,
    k: int,
    *,
    features: np.ndarray,
    response_train: np.ndarray,
    response_heldout: np.ndarray,
    random_summary: dict[str, float] | None = None,
    evaluator_only_upper_bound: bool = False,
) -> dict[str, object]:
    labels = torch.as_tensor(labels, dtype=torch.long, device="cpu").flatten()
    partition = evaluate_partition(labels, hidden_labels, num_clusters=k, random_baseline=random_summary)
    split_merge = split_merge_audit(labels, hidden_labels)
    reconstruction = _response_reconstruction(response_train, response_heldout, labels.numpy(), k)
    return {
        "comparison": name,
        "method": method,
        "training_role": "evaluator_only_upper_bound" if evaluator_only_upper_bound else "learner_visible_comparison",
        "feature_shape": [int(features.shape[0]), int(features.shape[1])],
        "finite_features": bool(np.isfinite(features).all()),
        "labels": [int(value) for value in labels.tolist()],
        "ari": float(partition["ari"]),
        "nmi": float(partition["nmi"]),
        "ari_nmi_used_for_selection": False,
        "active_clusters": int(partition["active_clusters"]),
        "cluster_masses": partition["cluster_masses"],
        "cluster_margin": _cluster_margin(features, labels.numpy()),
        "response_reconstruction_mse": reconstruction["mse"],
        "response_reconstruction_mae": reconstruction["mae"],
        "heldout_response_nll": reconstruction["nll"],
        "heldout_response_cross_entropy_nats": reconstruction["nll"],
        "detector_probe_response_mae": reconstruction["mae"],
        **{key: value for key, value in partition.items() if key not in {"ari", "nmi", "cluster_masses"}},
        **split_merge,
    }


def _random_partition_record(
    random_labels: list[torch.Tensor],
    hidden_labels: torch.Tensor,
    k: int,
    *,
    response_train: np.ndarray,
    response_heldout: np.ndarray,
) -> dict[str, object]:
    evaluations = [evaluate_partition(labels, hidden_labels, num_clusters=k) for labels in random_labels]
    if not evaluations:
        raise ValueError("random baseline produced no labels")
    first = random_labels[0]
    reconstruction = _response_reconstruction(response_train, response_heldout, first.numpy(), k)
    ari_values = [float(item["ari"]) for item in evaluations]
    nmi_values = [float(item["nmi"]) for item in evaluations]
    active_values = [int(item["active_clusters"]) for item in evaluations]
    masses = evaluations[0]["cluster_masses"]
    split_merge = split_merge_audit(first, hidden_labels)
    return {
        "comparison": "random_partition",
        "method": "uniform_random_partition_trials",
        "training_role": "negative_control",
        "feature_shape": [len(hidden_labels), 0],
        "finite_features": True,
        "labels": [int(value) for value in first.tolist()],
        "ari": float(sum(ari_values) / len(ari_values)),
        "nmi": float(sum(nmi_values) / len(nmi_values)),
        "ari_max": float(max(ari_values)),
        "nmi_max": float(max(nmi_values)),
        "ari_nmi_used_for_selection": False,
        "active_clusters": int(round(sum(active_values) / len(active_values))),
        "cluster_masses": masses,
        "cluster_margin": 0.0,
        "response_reconstruction_mse": reconstruction["mse"],
        "response_reconstruction_mae": reconstruction["mae"],
        "heldout_response_nll": reconstruction["nll"],
        "heldout_response_cross_entropy_nats": reconstruction["nll"],
        "detector_probe_response_mae": reconstruction["mae"],
        **split_merge,
    }


def _visible_operation_aware_local_inverse_labels(features: np.ndarray, records: list[dict[str, object]], k: int) -> list[int]:
    groups = _groups_by_instruction(records)
    non_idle = [(name, indices) for name, indices in groups.items() if name not in {"id", "delay", "idle", "barrier"}]
    idle_indices = [idx for name, indices in groups.items() if name in {"id", "delay", "idle", "barrier"} for idx in indices]
    if len(non_idle) >= int(k):
        return [int(value) for value in deterministic_kmeans(torch.as_tensor(features, dtype=torch.float64), k).labels.tolist()]

    labels = [-1 for _ in records]
    next_cluster = 0
    for _name, indices in sorted(non_idle, key=lambda item: (_instruction_priority(item[0]), item[0])):
        for idx in indices:
            labels[idx] = next_cluster
        next_cluster += 1

    remaining = max(1, int(k) - next_cluster)
    if idle_indices:
        idle_k = min(remaining, len(idle_indices))
        idle_features = torch.as_tensor(features[idle_indices], dtype=torch.float64)
        idle_labels = deterministic_kmeans(idle_features, idle_k).labels.tolist()
        for idx, local_label in zip(idle_indices, idle_labels):
            labels[idx] = next_cluster + int(local_label)
        next_cluster += idle_k

    while next_cluster < int(k):
        candidates = _active_cluster_indices(labels)
        splittable = [(cluster, indices) for cluster, indices in candidates.items() if len(indices) >= 2]
        if not splittable:
            break
        cluster, indices = max(splittable, key=lambda item: len(item[1]))
        local = deterministic_kmeans(torch.as_tensor(features[indices], dtype=torch.float64), 2).labels.tolist()
        for idx, local_label in zip(indices, local):
            if int(local_label) == 1:
                labels[idx] = next_cluster
            else:
                labels[idx] = cluster
        next_cluster += 1

    if any(label < 0 for label in labels):
        fallback = deterministic_kmeans(torch.as_tensor(features, dtype=torch.float64), k).labels.tolist()
        labels = [int(value) if label < 0 else int(label) for label, value in zip(labels, fallback)]
    return [int(label) for label in labels]


def _oracle_fingerprint_upper_bound_record(
    records: list[dict[str, object]],
    hidden_labels: torch.Tensor,
    label_names: list[str],
    k: int,
    *,
    separability_dir: Path,
    paper_informed: bool,
    response_train: np.ndarray,
    response_heldout: np.ndarray,
) -> dict[str, object]:
    features_path = separability_dir / "fingerprints.npy"
    if features_path.exists():
        features = np.asarray(np.load(features_path), dtype=np.float64)
    else:
        features = _oracle_fingerprint_features(records, paper_informed=paper_informed)
    clustering = deterministic_kmeans(torch.as_tensor(features, dtype=torch.float64), k)
    record = _comparison_record(
        "oracle_fingerprint_upper_bound",
        "oracle_ptm_probe_fingerprint_kmeans",
        clustering.labels,
        hidden_labels,
        k,
        features=features,
        response_train=response_train,
        response_heldout=response_heldout,
        random_summary=None,
        evaluator_only_upper_bound=True,
    )
    record["uses_oracle_channel_parameters"] = True
    record["oracle_label_names"] = label_names
    return record


def _oracle_fingerprint_features(records: list[dict[str, object]], *, paper_informed: bool) -> np.ndarray:
    specs = [_spec_from_record(record) for record in records]
    ptm = np.stack([channel_fingerprint(spec, paper_informed=paper_informed) for spec in specs], axis=0)
    probe = np.stack([probe_response_fingerprint(spec) for spec in specs], axis=0)
    parts = [ptm, probe]
    if paper_informed:
        parts.append(np.stack([rzz_type_feature_vector(spec) for spec in specs], axis=0))
    return _finite(np.concatenate(parts, axis=1))


def _local_response_features(observations: np.ndarray, bit_rates: np.ndarray, qubits: list[int]) -> np.ndarray:
    rows = []
    for probe in range(int(observations.shape[0])):
        local = observations[probe, :, qubits]
        single_rates = bit_rates[probe, qubits]
        shot_weight = local.mean(axis=1)
        parity = np.mod(local.sum(axis=1), 2).mean()
        any_one = (local.sum(axis=1) > 0).mean()
        all_one = (local.sum(axis=1) == len(qubits)).mean()
        equal = (local[:, 0] == local[:, -1]).mean() if len(qubits) > 1 else 1.0
        rows.extend(
            [
                float(np.mean(single_rates)),
                float(np.min(single_rates)),
                float(np.max(single_rates)),
                float(np.max(single_rates) - np.min(single_rates)),
                float(np.std(single_rates)),
                float(parity),
                float(any_one),
                float(all_one),
                float(equal),
                float(np.mean(shot_weight)),
                float(np.var(shot_weight)),
            ]
        )
    return _finite(np.asarray(rows, dtype=np.float64))


def _probe_axis_summary(local_response: np.ndarray, probe_names: list[str]) -> np.ndarray:
    per_probe_width = 11
    means = []
    for idx in range(len(probe_names)):
        start = idx * per_probe_width
        stop = start + per_probe_width
        means.append(float(np.mean(local_response[start:stop])))
    if not means:
        return np.zeros(4, dtype=np.float64)
    values = np.asarray(means, dtype=np.float64)
    return np.array(
        [
            float(values[0]),
            float(values[-1]),
            float(np.max(values) - np.min(values)),
            float(np.std(values)),
        ],
        dtype=np.float64,
    )


def _basis_response_differences(local_response: np.ndarray, probe_names: list[str]) -> np.ndarray:
    means = _probe_means(local_response, probe_names)
    z = means.get("z_basis", means.get("idle", 0.0))
    x = means.get("x_measure", means.get("x_basis", means.get("full_x", z)))
    y = means.get("y_measure", means.get("y_basis", means.get("full_y", z)))
    values = np.asarray(list(means.values()), dtype=np.float64) if means else np.zeros(1, dtype=np.float64)
    return np.array(
        [
            float(x - z),
            float(y - z),
            float(x - y),
            float(np.max(values) - np.min(values)),
            float(np.std(values)),
        ],
        dtype=np.float64,
    )


def _response_entropy_variance_features(local_response: np.ndarray) -> np.ndarray:
    values = np.clip(_finite(local_response), NUMERICAL_ZERO, 1.0 - NUMERICAL_ZERO)
    entropy = -(values * np.log(values) + (1.0 - values) * np.log(1.0 - values))
    return np.array(
        [
            float(np.mean(entropy)),
            float(np.std(entropy)),
            float(np.min(entropy)),
            float(np.max(entropy)),
            float(np.var(values)),
            float(np.mean(np.abs(values - 0.5))),
        ],
        dtype=np.float64,
    )


def _learner_visible_rzz_type_proxy(record: dict[str, object], local_response: np.ndarray, probe_names: list[str]) -> np.ndarray:
    instruction = str(record.get("instruction", "unknown"))
    is_rzz = 1.0 if instruction == "rzz" else 0.0
    means = _probe_means(local_response, probe_names)
    values = np.asarray(list(means.values()), dtype=np.float64) if means else np.zeros(1, dtype=np.float64)
    per_probe_width = 11
    equal_values = []
    for idx in range(len(probe_names)):
        start = idx * per_probe_width
        if start + 8 < len(local_response):
            equal_values.append(float(local_response[start + 8]))
    equal = float(np.mean(equal_values)) if equal_values else 0.0
    return np.array(
        [
            is_rzz * equal,
            is_rzz * float(np.max(values) - np.min(values)),
            is_rzz * float(np.std(local_response)),
            is_rzz * float(_response_entropy_variance_features(local_response)[0]),
        ],
        dtype=np.float64,
    )


def _probe_means(local_response: np.ndarray, probe_names: list[str]) -> dict[str, float]:
    per_probe_width = 11
    means: dict[str, float] = {}
    for idx, name in enumerate(probe_names):
        start = idx * per_probe_width
        stop = start + per_probe_width
        if start >= len(local_response):
            continue
        means[_probe_base_name(name)] = float(np.mean(local_response[start:stop]))
    return means


def _probe_base_name(name: str) -> str:
    text = str(name)
    return text.split(":", 1)[1] if ":" in text else text


def _bootstrap_nmi(
    records: list[dict[str, object]],
    observations: np.ndarray,
    probe_names: list[str],
    *,
    reference_labels: list[int],
    k: int,
    seed: int,
    replicates: int,
) -> dict[str, object]:
    if int(replicates) <= 0:
        return {"replicates": 0, "mean_vs_full": 1.0, "min_vs_full": 1.0, "mean_pairwise": 1.0, "labels": []}
    rng = np.random.default_rng(int(seed) + 10_001)
    labels = []
    scores = []
    for _ in range(int(replicates)):
        boot = _bootstrap_observations(observations, rng)
        features = build_visible_location_representations(records, boot, probe_names)["physical_local_inverse_probability"]
        current = _visible_operation_aware_local_inverse_labels(features, records, k)
        labels.append(current)
        scores.append(float(normalized_mutual_info(reference_labels, current)))
    pairwise = []
    for left_idx, left in enumerate(labels):
        for right in labels[left_idx + 1 :]:
            pairwise.append(float(normalized_mutual_info(left, right)))
    return {
        "replicates": int(replicates),
        "mean_vs_full": float(sum(scores) / len(scores)) if scores else 1.0,
        "min_vs_full": float(min(scores)) if scores else 1.0,
        "mean_pairwise": float(sum(pairwise) / len(pairwise)) if pairwise else 1.0,
        "min_pairwise": float(min(pairwise)) if pairwise else 1.0,
        "labels": labels,
    }


def _response_reconstruction(response_train: np.ndarray, response_heldout: np.ndarray, labels: np.ndarray, k: int) -> dict[str, float]:
    labels = np.asarray(labels, dtype=np.int64)
    train = _finite(response_train)
    heldout = _finite(response_heldout)
    global_mean = train.mean(axis=0)
    centers = np.tile(global_mean.reshape(1, -1), (int(k), 1))
    for cluster in range(int(k)):
        idx = labels == cluster
        if bool(np.any(idx)):
            centers[cluster] = train[idx].mean(axis=0)
    prediction = centers[labels]
    error = heldout - prediction
    p = np.clip(prediction, NUMERICAL_ZERO, 1.0 - NUMERICAL_ZERO)
    q = np.clip(heldout, NUMERICAL_ZERO, 1.0)
    nll = -np.mean(q * np.log(p) + (1.0 - q) * np.log(1.0 - p))
    return {"mse": float(np.mean(error * error)), "mae": float(np.mean(np.abs(error))), "nll": float(nll)}


def _nll_difficulty_audit(
    *,
    response_train: np.ndarray,
    response_heldout: np.ndarray,
    local_inverse_record: dict[str, object],
    direct_record: dict[str, object],
    oracle_record: dict[str, object],
) -> dict[str, object]:
    train = _finite(response_train)
    heldout = _finite(response_heldout)
    scalar = float(np.mean(train))
    scalar_prediction = np.full_like(heldout, scalar, dtype=np.float64)
    global_prediction = np.tile(train.mean(axis=0, keepdims=True), (heldout.shape[0], 1))
    base_rate_null = _bernoulli_cross_entropy(heldout, scalar_prediction)
    global_mean = _bernoulli_cross_entropy(heldout, global_prediction)
    oracle_nll = float(oracle_record["heldout_response_nll"])
    local_nll = float(local_inverse_record["heldout_response_nll"])
    direct_nll = float(direct_record["heldout_response_nll"])
    entropy = _bernoulli_entropy(heldout)
    oracle_lift = base_rate_null - oracle_nll
    local_lift = base_rate_null - local_nll
    return {
        "base_rate_null_NLL": float(base_rate_null),
        "global_mean_NLL": float(global_mean),
        "oracle_fingerprint_NLL": float(oracle_nll),
        "local_inverse_NLL": float(local_nll),
        "direct_Salpha_NLL": float(direct_nll),
        "NLL_lift_over_null": float(local_lift),
        "NLL_gap_to_oracle": float(local_nll - oracle_nll),
        "oracle_NLL_lift_over_null": float(oracle_lift),
        "direct_Salpha_NLL_lift_over_null": float(base_rate_null - direct_nll),
        "event_rate_mean": float(np.mean(heldout)),
        "event_rate_min": float(np.min(heldout)),
        "event_rate_max": float(np.max(heldout)),
        "response_entropy": float(entropy),
        "response_task_classification": _classify_nll_difficulty(
            event_rate_mean=float(np.mean(heldout)),
            event_rate_min=float(np.min(heldout)),
            event_rate_max=float(np.max(heldout)),
            response_entropy=float(entropy),
            oracle_lift=float(oracle_lift),
            local_gap=float(local_nll - oracle_nll),
        ),
    }


def _bernoulli_cross_entropy(target: np.ndarray, prediction: np.ndarray) -> float:
    q = np.clip(_finite(target), NUMERICAL_ZERO, 1.0)
    p = np.clip(_finite(prediction), NUMERICAL_ZERO, 1.0 - NUMERICAL_ZERO)
    return float(-np.mean(q * np.log(p) + (1.0 - q) * np.log(1.0 - p)))


def _bernoulli_entropy(target: np.ndarray) -> float:
    q = np.clip(_finite(target), NUMERICAL_ZERO, 1.0 - NUMERICAL_ZERO)
    return float(-np.mean(q * np.log(q) + (1.0 - q) * np.log(1.0 - q)))


def _classify_nll_difficulty(
    *,
    event_rate_mean: float,
    event_rate_min: float,
    event_rate_max: float,
    response_entropy: float,
    oracle_lift: float,
    local_gap: float,
) -> str:
    near_extreme = event_rate_mean <= 0.03 or event_rate_mean >= 0.97 or event_rate_max <= 0.08 or event_rate_min >= 0.92
    if near_extreme or response_entropy < 0.08 or oracle_lift < 0.005:
        return "too_easy"
    if local_gap > 0.05:
        return "hard"
    return "usable"


def _cluster_margin(features: np.ndarray, labels: np.ndarray) -> float:
    x = standardize_features(torch.as_tensor(features, dtype=torch.float64))
    labels_t = torch.as_tensor(labels, dtype=torch.long)
    active = sorted({int(value) for value in labels_t.tolist()})
    if x.numel() == 0 or len(active) <= 1:
        return 0.0
    centers = torch.stack([x[labels_t == cluster].mean(dim=0) for cluster in active], dim=0)
    distances = torch.cdist(x, centers, p=2)
    active_index = {cluster: idx for idx, cluster in enumerate(active)}
    own = torch.tensor([active_index[int(label)] for label in labels_t.tolist()], dtype=torch.long)
    own_dist = distances[torch.arange(x.shape[0]), own]
    masked = distances.clone()
    masked[torch.arange(x.shape[0]), own] = float("inf")
    other = torch.min(masked, dim=1).values
    margin = other - own_dist
    finite = torch.isfinite(margin)
    return float(margin[finite].mean().item()) if bool(finite.any()) else 0.0


def _acceptance_label(
    main_record: dict[str, object],
    oracle_record: dict[str, object],
    bootstrap: dict[str, object],
    separability_metrics: dict[str, object],
    *,
    no_oracle_leakage: bool,
    k: int,
) -> str:
    oracle_ari = float(separability_metrics.get("ari", oracle_record["ari"]) or 0.0)
    oracle_nmi = float(separability_metrics.get("nmi", oracle_record["nmi"]) or 0.0)
    if oracle_ari < 0.90 or oracle_nmi < 0.90:
        return "catalog_validation_probe_limited"
    ari = float(main_record["ari"])
    nmi = float(main_record["nmi"])
    active = int(main_record["active_clusters"])
    bootstrap_stable = float(bootstrap.get("min_vs_full", 0.0)) >= 0.80
    if ari >= 0.80 and nmi >= 0.80 and active >= max(1, int(k) - 1) and bootstrap_stable and no_oracle_leakage:
        return "catalog_validation_strong_recovery"
    if ari >= 0.75 and nmi >= 0.90 and no_oracle_leakage:
        return "catalog_validation_near_strong"
    return "catalog_validation_learner_limited"


def _run_selection_audit(cfg: dict[str, object], k_source: str) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d_phys3_run_selection_audit_v1",
        "predeclared_representation": str(cfg.get("predeclared_representation")),
        "selection_rule": "predeclared_physical_local_inverse_probability_no_candidate_selection_by_ari_nmi",
        "num_clusters_source": k_source,
        "uses_oracle_labels_for_training": False,
        "uses_oracle_labels_for_initialization": False,
        "uses_oracle_labels_for_selection": False,
        "oracle_labels_used_for_training_or_selection": False,
        "uses_oracle_labels_for_final_evaluation": True,
        "ari_nmi_used_for_selection": False,
        "oracle_fingerprint_upper_bound_evaluator_only": True,
        "known_K_synthetic_audit": True,
    }


def _prediction_metrics(
    *,
    local_inverse_record: dict[str, object],
    local_inverse_v2_record: dict[str, object],
    direct_record: dict[str, object],
    oracle_record: dict[str, object],
) -> dict[str, object]:
    return {
        "local_inverse": _compact_prediction_record(local_inverse_record),
        "local_inverse_v2": _compact_prediction_record(local_inverse_v2_record),
        "direct_Salpha": _compact_prediction_record(direct_record),
        "oracle_fingerprint": _compact_prediction_record(oracle_record),
    }


def _compact_prediction_record(record: dict[str, object]) -> dict[str, float]:
    return {
        "heldout_response_nll": float(record["heldout_response_nll"]),
        "response_reconstruction_mae": float(record["response_reconstruction_mae"]),
        "response_reconstruction_mse": float(record["response_reconstruction_mse"]),
        "detector_probe_response_mae": float(record["detector_probe_response_mae"]),
    }


def _clusters_artifact(comparisons: list[dict[str, object]], label_names: list[str]) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d_phys3_clusters_v1",
        "oracle_label_names": label_names,
        "comparisons": [
            {
                "comparison": record["comparison"],
                "method": record["method"],
                "labels": record["labels"],
                "active_clusters": record["active_clusters"],
                "cluster_masses": record["cluster_masses"],
                "ari": record["ari"],
                "nmi": record["nmi"],
            }
            for record in comparisons
        ],
    }


def _load_observations(path: Path) -> tuple[np.ndarray, list[str], int]:
    if not path.exists():
        raise FileNotFoundError(f"missing observations artifact: {path}")
    data = np.load(path)
    observations = _validate_observations(np.asarray(data["observations"], dtype=np.float64))
    probe_names = [str(value) for value in data["probe_names"].tolist()]
    shots = int(data["shots"][0]) if "shots" in data.files else int(observations.shape[1])
    return observations, probe_names, shots


def _load_mechanism_records(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        raise FileNotFoundError(f"missing oracle mechanism artifact: {path}")
    data = json.loads(path.read_text())
    records = data.get("mechanisms")
    if not isinstance(records, list) or not records:
        raise ValueError(f"{path} does not contain non-empty mechanisms")
    return [dict(record) for record in records]


def _load_separability_metrics(path: Path) -> dict[str, object]:
    metrics_path = path / "metrics.json"
    if not metrics_path.exists():
        return {}
    data = json.loads(metrics_path.read_text())
    return data if isinstance(data, dict) else {}


def _train_heldout_observations(observations: np.ndarray, *, seed: int, heldout_fraction: float) -> tuple[np.ndarray, np.ndarray]:
    obs = _validate_observations(observations)
    shots = int(obs.shape[1])
    heldout = max(1, min(shots - 1, int(round(shots * max(NUMERICAL_ZERO, min(0.9, float(heldout_fraction)))))))
    train = shots - heldout
    rng = np.random.default_rng(int(seed))
    train_rows = np.empty((obs.shape[0], train, obs.shape[2]), dtype=obs.dtype)
    heldout_rows = np.empty((obs.shape[0], heldout, obs.shape[2]), dtype=obs.dtype)
    for probe in range(int(obs.shape[0])):
        perm = rng.permutation(shots)
        train_rows[probe] = obs[probe, perm[:train]]
        heldout_rows[probe] = obs[probe, perm[train:]]
    return train_rows, heldout_rows


def _bootstrap_observations(observations: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    obs = _validate_observations(observations)
    out = np.empty_like(obs)
    shots = int(obs.shape[1])
    for probe in range(int(obs.shape[0])):
        indices = rng.integers(0, shots, size=shots)
        out[probe] = obs[probe, indices]
    return out


def _validate_observations(observations: np.ndarray) -> np.ndarray:
    obs = np.asarray(observations, dtype=np.float64)
    if obs.ndim != 3:
        raise ValueError("observations must have shape [num_probes, shots, num_qubits]")
    if min(obs.shape) <= 0:
        raise ValueError("observations must be non-empty")
    return _finite(obs)


def _num_clusters(cfg: dict[str, object], label_names: list[str]) -> tuple[int, str]:
    value = cfg.get("num_clusters")
    if value is None:
        return len(label_names), "synthetic_oracle_label_count_default"
    return int(value), "config"


def _encode_labels(labels: list[str]) -> tuple[torch.Tensor, list[str]]:
    names = sorted(set(labels))
    index = {name: idx for idx, name in enumerate(names)}
    return torch.tensor([index[label] for label in labels], dtype=torch.long), names


def _record_qubits(record: dict[str, object], num_qubits: int) -> list[int]:
    raw = record.get("qubits", [])
    if not isinstance(raw, list) or not raw:
        return [0]
    qubits = [int(value) for value in raw]
    if min(qubits) < 0 or max(qubits) >= int(num_qubits):
        raise ValueError(f"record has qubits outside observations: {record}")
    return qubits


def _record_probe_indices(record: dict[str, object], observations: np.ndarray) -> list[int]:
    raw = record.get("probe_indices", [])
    if isinstance(raw, list) and raw:
        indices = [int(value) for value in raw]
        if min(indices) < 0 or max(indices) >= int(observations.shape[0]):
            raise ValueError(f"record has probe_indices outside observations: {record}")
        return indices
    return list(range(int(observations.shape[0])))


def _instruction_names(records: list[dict[str, object]]) -> list[str]:
    return sorted({str(record.get("instruction", "unknown")) for record in records})


def _instruction_one_hot(record: dict[str, object], instructions: list[str]) -> np.ndarray:
    out = np.zeros(len(instructions), dtype=np.float64)
    index = {name: idx for idx, name in enumerate(instructions)}
    out[index[str(record.get("instruction", "unknown"))]] = 1.0
    return out


def _groups_by_instruction(records: list[dict[str, object]]) -> dict[str, list[int]]:
    groups: dict[str, list[int]] = {}
    for idx, record in enumerate(records):
        groups.setdefault(str(record.get("instruction", "unknown")), []).append(idx)
    return groups


def _instruction_priority(name: str) -> int:
    order = {"measure": 0, "rx": 1, "ry": 1, "rz": 1, "rzz": 2, "cx": 2, "cz": 2}
    return order.get(str(name), 10)


def _active_cluster_indices(labels: list[int]) -> dict[int, list[int]]:
    groups: dict[int, list[int]] = {}
    for idx, label in enumerate(labels):
        groups.setdefault(int(label), []).append(idx)
    return groups


def _spec_from_record(record: dict[str, object]) -> MechanismSpec:
    return MechanismSpec(
        mechanism_id=str(record["oracle_label"]),
        name=str(record.get("name", record["oracle_label"])),
        num_qubits=int(record.get("num_qubits", 1)),
        parameters=dict(record.get("parameters", {})),
        instruction=None if record.get("instruction") is None else str(record.get("instruction")),
        qubits=tuple(int(q) for q in record.get("qubits", [])),
        circuit_id=int(record.get("circuit_id", 0)),
        probe_indices=tuple(int(idx) for idx in record.get("probe_indices", [])),
    )


def _confusion_matrix(pred: list[int], true: list[int], *, num_pred: int, num_true: int) -> list[list[int]]:
    matrix = [[0 for _ in range(num_true)] for _ in range(num_pred)]
    for left, right in zip(pred, true):
        matrix[int(left)][int(right)] += 1
    return matrix


def _find_comparison(records: list[dict[str, object]], name: str) -> dict[str, object]:
    for record in records:
        if record.get("comparison") == name:
            return record
    raise KeyError(name)


def _compact_comparison(record: dict[str, object]) -> dict[str, object]:
    keys = [
        "comparison",
        "method",
        "ari",
        "nmi",
        "active_clusters",
        "cluster_masses",
        "cluster_margin",
        "response_reconstruction_mse",
        "response_reconstruction_mae",
        "heldout_response_nll",
        "heldout_response_cross_entropy_nats",
        "detector_probe_response_mae",
        "mean_splits_per_omega",
        "max_splits_per_omega",
        "mean_merged_omega_per_cluster",
        "max_merged_omega_per_cluster",
        "mean_cluster_purity",
    ]
    return {key: record[key] for key in keys if key in record}


def _summary_row(record: dict[str, object], name: str, note: str) -> str:
    return (
        f"| {name} | {_fmt(record['ari'])} | {_fmt(record['nmi'])} | {record['active_clusters']} | "
        f"{_fmt(record['heldout_response_nll'])} | "
        f"{_fmt(record['detector_probe_response_mae'])} | {note} |"
    )


def _fmt(value: object) -> str:
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return str(value)


def _merged_config(config: dict[str, object] | None) -> dict[str, object]:
    merged = dict(DEFAULT_LOCAL_INVERSE_CONFIG)
    if config:
        merged.update(config)
    return merged


def _finite(values: np.ndarray) -> np.ndarray:
    return np.nan_to_num(np.asarray(values, dtype=np.float64), nan=NUMERICAL_ZERO, posinf=NUMERICAL_ZERO, neginf=-NUMERICAL_ZERO)
