from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
import yaml

from scope_static.identifiability import deterministic_kmeans, evaluate_partition
from scope_static.local_mechanism import split_merge_audit
from scope_static.numerics import NUMERICAL_ZERO
from scope_static.physical.channels import MechanismSpec
from scope_static.physical.local_inverse import (
    _train_heldout_observations,
    _visible_operation_aware_local_inverse_labels,
    build_visible_location_representations,
)
from scope_static.physical.ptm import channel_fingerprint, rzz_type_feature_vector
from scope_static.physical.teacher import build_default_oracle_mechanisms


DEFAULT_RUNS = ["phys5_setB", "phys9_setB", "phys9_setC"]
DEFAULT_PHYS4_DIR = Path("outputs/scope_static/S2D_PHYS4_difficulty_expansion")
DEFAULT_OUTPUT_DIR = Path("outputs/scope_static/S2D.5_learner_limit_audit_and_representation_v2")


def run_s2d5_learner_limit_audit(
    config_path: str | Path | None = None,
    *,
    phys4_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, object]:
    cfg = _load_config(config_path)
    source = Path(phys4_dir) if phys4_dir is not None else Path(str(cfg.get("phys4_dir", DEFAULT_PHYS4_DIR)))
    output = Path(output_dir) if output_dir is not None else Path(str(cfg.get("output_dir", DEFAULT_OUTPUT_DIR)))
    output.mkdir(parents=True, exist_ok=True)
    runs = [str(item) for item in cfg.get("runs", DEFAULT_RUNS)]

    records = []
    for run_name in runs:
        run_record = _audit_run(source / run_name, output / run_name)
        records.append(run_record)

    balanced = _balanced_teacher_profile_audit()
    result = {
        "schema": "scope_static_s2d5_learner_limit_audit_v1",
        "stage": "S2D.5_learner_limit_audit_and_representation_v2",
        "source_phys4_dir": str(source),
        "output_dir": str(output),
        "runs": records,
        "balanced_teacher_profiles": balanced,
        "summary": _summary(records, balanced),
    }
    (output / "metrics.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (output / "summary.md").write_text(format_s2d5_summary(result))
    (output / "balanced_teacher_profiles.json").write_text(json.dumps(balanced, indent=2, sort_keys=True) + "\n")
    return result


def _audit_run(run_dir: Path, output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    teacher_dir = run_dir / "S2D_PHYS1_teacher"
    sep_dir = run_dir / "S2D_PHYS2_oracle_separability"
    local_dir = run_dir / "S2D_PHYS3_local_inverse"
    records = _load_mechanism_records(teacher_dir / "oracle_mechanisms.json")
    observations, probe_names, _shots = _load_observations(teacher_dir / "observations.npz")
    local_metrics = json.loads((local_dir / "metrics.json").read_text())
    hidden, label_names = _encode_labels([str(record["oracle_label"]) for record in records])
    main = _find_comparison(local_metrics["comparisons"], "physical_local_inverse_probability")

    failure = _failure_pair_audit(
        predicted=[int(value) for value in main["labels"]],
        true=hidden.tolist(),
        label_names=label_names,
    )
    representation = _representation_gap_audit(
        records=records,
        observations=observations,
        probe_names=probe_names,
        hidden=hidden,
        label_names=label_names,
        sep_dir=sep_dir,
        comparisons=local_metrics["comparisons"],
    )
    nll = _response_nll_calibration_audit(
        records=records,
        observations=observations,
        probe_names=probe_names,
        comparisons=local_metrics["comparisons"],
        seed=int(local_metrics.get("seed", 0)),
    )
    record = {
        "run": run_dir.name,
        "source_run_dir": str(run_dir),
        "decision": _decision_from_metrics(local_metrics),
        "failure_pair_audit": failure,
        "representation_gap_audit": representation,
        "response_nll_audit": nll,
    }
    (output_dir / "failure_pair_audit.json").write_text(json.dumps(failure, indent=2, sort_keys=True) + "\n")
    (output_dir / "representation_gap_audit.json").write_text(json.dumps(representation, indent=2, sort_keys=True) + "\n")
    (output_dir / "response_nll_audit.json").write_text(json.dumps(nll, indent=2, sort_keys=True) + "\n")
    (output_dir / "metrics.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    return record


def _failure_pair_audit(*, predicted: list[int], true: list[int], label_names: list[str]) -> dict[str, object]:
    pred = np.asarray(predicted, dtype=np.int64)
    labels = np.asarray(true, dtype=np.int64)
    num_pred = int(max(pred.tolist()) + 1) if pred.size else 0
    matrix = _confusion_matrix(pred.tolist(), labels.tolist(), num_pred=num_pred, num_true=len(label_names))
    merges = []
    for cluster, row in enumerate(matrix):
        present = {label_names[idx]: int(count) for idx, count in enumerate(row) if int(count) > 0}
        if len(present) > 1:
            merges.append({"cluster": int(cluster), "mechanisms": present})
    splits = []
    for true_idx, name in enumerate(label_names):
        present = {int(cluster): int(matrix[cluster][true_idx]) for cluster in range(num_pred) if int(matrix[cluster][true_idx]) > 0}
        if len(present) > 1:
            splits.append({"mechanism": name, "clusters": present})

    per_mechanism = []
    singleton_failures = []
    for true_idx, name in enumerate(label_names):
        true_count = int(np.sum(labels == true_idx))
        cluster_counts = [(cluster, int(matrix[cluster][true_idx])) for cluster in range(num_pred)]
        best_cluster, best_count = max(cluster_counts, key=lambda item: item[1]) if cluster_counts else (0, 0)
        cluster_total = int(sum(matrix[best_cluster])) if num_pred else 0
        recall = best_count / max(1, true_count)
        purity = best_count / max(1, cluster_total)
        entry = {
            "mechanism": name,
            "support": true_count,
            "best_cluster": int(best_cluster),
            "recall": float(recall),
            "dominant_cluster_purity": float(purity),
            "singleton": bool(true_count == 1),
            "failed_singleton": bool(true_count == 1 and cluster_total > best_count),
        }
        per_mechanism.append(entry)
        if entry["failed_singleton"]:
            singleton_failures.append(entry)

    return {
        "confusion_matrix": matrix,
        "oracle_label_names": label_names,
        "merge_clusters": merges,
        "split_mechanisms": splits,
        "per_mechanism_recall_purity": per_mechanism,
        "singleton_failure_count": len(singleton_failures),
        "singleton_failures": singleton_failures,
        "rx_rz_distinguishable": _group_distinguishability(matrix, label_names, ["M2", "M3"]),
        "readout_amplitude_damping_distinguishable": _group_distinguishability(matrix, label_names, ["M5", "M4"]),
        "pauli_depolarizing_custom_kraus_distinguishable": _group_distinguishability(matrix, label_names, ["M0", "M7", "M6"]),
        "degradation_pattern": "specific_pair_or_singleton_failures" if len(merges) <= max(2, len(label_names) // 4) else "broad_degradation",
    }


def _representation_gap_audit(
    *,
    records: list[dict[str, object]],
    observations: np.ndarray,
    probe_names: list[str],
    hidden: torch.Tensor,
    label_names: list[str],
    sep_dir: Path,
    comparisons: list[dict[str, object]],
) -> dict[str, object]:
    bundle = build_visible_location_representations(records, observations, probe_names)
    specs = [_spec_from_record(record) for record in records]
    oracle_features = np.asarray(np.load(sep_dir / "fingerprints.npy"), dtype=np.float64)
    ptm_lite = np.stack([channel_fingerprint(spec, paper_informed=False) for spec in specs], axis=0)
    rzz_lite = np.stack([rzz_type_feature_vector(spec) for spec in specs], axis=0)
    v1 = bundle["physical_local_inverse_probability"]
    v2 = bundle["physical_local_inverse_probability_v2"]
    feature_spaces = [
        ("PHYS2_oracle_PTM_probe_fingerprint", oracle_features, "oracle_only", "deterministic_kmeans", None),
        (
            "PHYS3_current_local_inverse_probability_v1",
            v1,
            "learner_visible",
            "phys3_predeclared_visible_operation_aware_labels",
            _comparison_labels(comparisons, "physical_local_inverse_probability"),
        ),
        (
            "direct_Salpha_assignment",
            bundle["direct_S_alpha_assignment"],
            "learner_visible",
            "phys3_direct_Salpha_labels",
            _comparison_labels(comparisons, "direct_S_alpha_assignment"),
        ),
        (
            "local_inverse_probability_plus_probe_stack",
            np.concatenate([v1, bundle["raw_observation_probe_summary"]], axis=1),
            "learner_visible",
            "deterministic_kmeans",
            None,
        ),
        (
            "local_inverse_probability_plus_standard_PTM_lite",
            np.concatenate([v1, ptm_lite], axis=1),
            "oracle_only",
            "deterministic_kmeans",
            None,
        ),
        (
            "local_inverse_probability_plus_RZZ_type_features",
            np.concatenate([v1, rzz_lite], axis=1),
            "oracle_only",
            "deterministic_kmeans",
            None,
        ),
        (
            "structural_plus_local_inverse_combined",
            np.concatenate([bundle["structural_only_features"], v1], axis=1),
            "learner_visible",
            "deterministic_kmeans",
            None,
        ),
        (
            "physical_local_inverse_probability_v2",
            v2,
            "learner_visible",
            "visible_operation_aware_local_inverse_clustering_v2",
            _comparison_labels(comparisons, "physical_local_inverse_probability_v2")
            or _visible_operation_aware_local_inverse_labels(v2, records, len(label_names)),
        ),
    ]
    rows = []
    k = len(label_names)
    oracle_ari = 0.0
    oracle_nmi = 0.0
    for name, features, role, method, precomputed_labels in feature_spaces:
        if precomputed_labels is None:
            clustering = deterministic_kmeans(torch.as_tensor(features, dtype=torch.float64), k)
            labels = clustering.labels
        else:
            labels = torch.as_tensor(precomputed_labels, dtype=torch.long)
        partition = evaluate_partition(labels, hidden, num_clusters=k)
        if name == "PHYS2_oracle_PTM_probe_fingerprint":
            oracle_ari = float(partition["ari"])
            oracle_nmi = float(partition["nmi"])
        rows.append(
            {
                "feature_space": name,
                "feature_role": role,
                "clustering_method": method,
                "uses_oracle_channel_parameters": role == "oracle_only",
                "uses_oracle_labels": False,
                "shape": [int(features.shape[0]), int(features.shape[1])],
                "ari": float(partition["ari"]),
                "nmi": float(partition["nmi"]),
                "active_clusters": int(partition["active_clusters"]),
                "cluster_masses": partition["cluster_masses"],
                "gap_to_oracle_ari": float(oracle_ari - float(partition["ari"])) if oracle_ari else 0.0,
                "gap_to_oracle_nmi": float(oracle_nmi - float(partition["nmi"])) if oracle_nmi else 0.0,
                **split_merge_audit(labels, hidden),
            }
        )
    return {
        "question": "How much PHYS2 separability is missing from learner-visible PHYS3 representations?",
        "feature_spaces": rows,
        "best_learner_visible": _best_feature_space(rows, role="learner_visible"),
        "oracle_upper_bound": rows[0],
    }


def _response_nll_calibration_audit(
    *,
    records: list[dict[str, object]],
    observations: np.ndarray,
    probe_names: list[str],
    comparisons: list[dict[str, object]],
    seed: int,
) -> dict[str, object]:
    train_obs, heldout_obs = _train_heldout_observations(observations, seed=int(seed), heldout_fraction=0.25)
    train = build_visible_location_representations(records, train_obs, probe_names)["response_target"]
    heldout = build_visible_location_representations(records, heldout_obs, probe_names)["response_target"]
    k = len({str(record["oracle_label"]) for record in records})
    entries = {
        "base_rate_null": _scalar_prediction_record(train, heldout),
        "global_mean": _global_prediction_record(train, heldout),
    }
    for key, comparison_name in [
        ("oracle_fingerprint", "oracle_fingerprint_upper_bound"),
        ("local_inverse", "physical_local_inverse_probability"),
        ("local_inverse_v2", "physical_local_inverse_probability_v2"),
        ("direct_Salpha", "direct_S_alpha_assignment"),
    ]:
        labels = _labels_for_prediction(
            comparison_name,
            comparisons=comparisons,
            records=records,
            observations=observations,
            probe_names=probe_names,
            k=k,
        )
        entries[key] = _cluster_prediction_record(train, heldout, labels, k)
    oracle_worse = float(entries["oracle_fingerprint"]["nll"]) > float(entries["global_mean"]["nll"])
    return {
        "schema": "scope_static_s2d5_response_nll_calibration_v1",
        "null_NLL": entries["base_rate_null"]["nll"],
        "global_mean_NLL": entries["global_mean"]["nll"],
        "oracle_fingerprint_NLL": entries["oracle_fingerprint"]["nll"],
        "local_inverse_NLL": entries["local_inverse"]["nll"],
        "local_inverse_v2_NLL": entries["local_inverse_v2"]["nll"],
        "direct_Salpha_NLL": entries["direct_Salpha"]["nll"],
        "event_response_entropy": _bernoulli_entropy(heldout),
        "entries": entries,
        "nll_primary_ranking_trusted": not oracle_worse,
        "decision": (
            "response_NLL_not_primary_ranking_signal_or_oracle_predictor_uncalibrated"
            if oracle_worse
            else "response_NLL_passes_oracle_vs_global_mean_sanity_check"
        ),
    }


def _balanced_teacher_profile_audit() -> dict[str, object]:
    profiles = {}
    for profile in ["phys9_multicircuit_setB_balanced", "phys9_multicircuit_setC_balanced"]:
        specs = build_default_oracle_mechanisms({"profile": profile})
        counts: dict[str, int] = {}
        for spec in specs:
            counts[spec.mechanism_id] = counts.get(spec.mechanism_id, 0) + 1
        profiles[profile] = {
            "profile": profile,
            "num_locations": len(specs),
            "mechanism_counts": counts,
            "min_instances_per_mechanism": min(counts.values()) if counts else 0,
            "constraint_min_instances_per_mechanism": 3,
            "constraint_satisfied": all(value >= 3 for value in counts.values()),
            "multicircuit_teacher_batch": True,
            "num_circuit_batches": 3,
        }
    return profiles


def _cluster_prediction_record(train: np.ndarray, heldout: np.ndarray, labels: list[int], k: int) -> dict[str, object]:
    labels_arr = np.asarray(labels, dtype=np.int64)
    centers = _cluster_centers(train, labels_arr, k)
    prediction = centers[labels_arr]
    return _prediction_record(heldout, prediction)


def _labels_for_prediction(
    comparison_name: str,
    *,
    comparisons: list[dict[str, object]],
    records: list[dict[str, object]],
    observations: np.ndarray,
    probe_names: list[str],
    k: int,
) -> list[int]:
    try:
        comparison = _find_comparison(comparisons, comparison_name)
        return [int(value) for value in comparison["labels"]]
    except KeyError:
        if comparison_name != "physical_local_inverse_probability_v2":
            raise
    features = build_visible_location_representations(records, observations, probe_names)["physical_local_inverse_probability_v2"]
    clustering = deterministic_kmeans(torch.as_tensor(features, dtype=torch.float64), int(k))
    return [int(value) for value in clustering.labels.tolist()]


def _scalar_prediction_record(train: np.ndarray, heldout: np.ndarray) -> dict[str, object]:
    return _prediction_record(heldout, np.full_like(heldout, float(np.mean(train)), dtype=np.float64))


def _global_prediction_record(train: np.ndarray, heldout: np.ndarray) -> dict[str, object]:
    prediction = np.tile(np.mean(train, axis=0, keepdims=True), (heldout.shape[0], 1))
    return _prediction_record(heldout, prediction)


def _cluster_centers(train: np.ndarray, labels: np.ndarray, k: int) -> np.ndarray:
    global_mean = train.mean(axis=0)
    centers = np.tile(global_mean.reshape(1, -1), (int(k), 1))
    for cluster in range(int(k)):
        idx = labels == cluster
        if bool(np.any(idx)):
            centers[cluster] = train[idx].mean(axis=0)
    return centers


def _prediction_record(target: np.ndarray, prediction: np.ndarray) -> dict[str, object]:
    q = np.clip(np.asarray(target, dtype=np.float64), NUMERICAL_ZERO, 1.0)
    p = np.clip(np.asarray(prediction, dtype=np.float64), NUMERICAL_ZERO, 1.0 - NUMERICAL_ZERO)
    error = q - p
    return {
        "nll": float(-np.mean(q * np.log(p) + (1.0 - q) * np.log(1.0 - p))),
        "brier_mse": float(np.mean(error * error)),
        "mae": float(np.mean(np.abs(error))),
        "calibration_curve": _calibration_curve(q, p),
    }


def _calibration_curve(target: np.ndarray, prediction: np.ndarray, *, bins: int = 10) -> list[dict[str, float]]:
    q = np.asarray(target, dtype=np.float64).reshape(-1)
    p = np.asarray(prediction, dtype=np.float64).reshape(-1)
    edges = np.linspace(0.0, 1.0, int(bins) + 1)
    rows = []
    for idx in range(int(bins)):
        if idx == int(bins) - 1:
            mask = (p >= edges[idx]) & (p <= edges[idx + 1])
        else:
            mask = (p >= edges[idx]) & (p < edges[idx + 1])
        count = int(np.sum(mask))
        rows.append(
            {
                "bin_left": float(edges[idx]),
                "bin_right": float(edges[idx + 1]),
                "count": count,
                "prediction_mean": float(np.mean(p[mask])) if count else 0.0,
                "target_mean": float(np.mean(q[mask])) if count else 0.0,
            }
        )
    return rows


def _group_distinguishability(matrix: list[list[int]], label_names: list[str], group: list[str]) -> dict[str, object]:
    present = [label for label in group if label in label_names]
    label_indices = [label_names.index(label) for label in present]
    shared_clusters = []
    for cluster, row in enumerate(matrix):
        values = {label_names[idx]: int(row[idx]) for idx in label_indices if int(row[idx]) > 0}
        if len(values) > 1:
            shared_clusters.append({"cluster": int(cluster), "mechanisms": values})
    return {"mechanisms": present, "distinguishable": not bool(shared_clusters), "shared_clusters": shared_clusters}


def _best_feature_space(rows: list[dict[str, object]], *, role: str) -> dict[str, object] | None:
    candidates = [row for row in rows if row["feature_role"] == role]
    if not candidates:
        return None
    return max(candidates, key=lambda row: (float(row["ari"]), float(row["nmi"])))


def _decision_from_metrics(metrics: dict[str, object]) -> str:
    main = metrics["main_result"]
    if float(main["ari"]) >= 0.85 and float(main["nmi"]) >= 0.85:
        return "strong_or_near_strong"
    return "learner_limited"


def _summary(records: list[dict[str, object]], balanced: dict[str, object]) -> dict[str, object]:
    return {
        "audited_runs": len(records),
        "learner_limited_runs": sum(1 for record in records if record["decision"] == "learner_limited"),
        "nll_untrusted_runs": sum(
            1 for record in records if not bool(record["response_nll_audit"]["nll_primary_ranking_trusted"])
        ),
        "balanced_profiles_satisfy_min_instances": all(bool(item["constraint_satisfied"]) for item in balanced.values()),
    }


def format_s2d5_summary(result: dict[str, object]) -> str:
    lines = [
        "# S2D.5 Learner-Limit Audit and Representation v2",
        "",
        "| run | decision | singleton failures | best learner-visible representation | best ARI/NMI | NLL trusted |",
        "| --- | --- | ---: | --- | ---: | --- |",
    ]
    for record in result["runs"]:  # type: ignore[index]
        failure = record["failure_pair_audit"]
        rep = record["representation_gap_audit"]["best_learner_visible"]
        nll = record["response_nll_audit"]
        lines.append(
            f"| {record['run']} | {record['decision']} | {failure['singleton_failure_count']} | "
            f"{rep['feature_space']} | {float(rep['ari']):.4f}/{float(rep['nmi']):.4f} | "
            f"{str(bool(nll['nll_primary_ranking_trusted'])).lower()} |"
        )
    lines.extend(["", "## Balanced Profiles", ""])
    for profile, audit in result["balanced_teacher_profiles"].items():  # type: ignore[union-attr]
        lines.append(
            f"- `{profile}`: min instances {audit['min_instances_per_mechanism']} "
            f"(satisfied={str(bool(audit['constraint_satisfied'])).lower()})"
        )
    lines.append("")
    return "\n".join(lines)


def _load_config(config_path: str | Path | None) -> dict[str, object]:
    if config_path is None:
        return {}
    data = yaml.safe_load(Path(config_path).read_text())
    if not isinstance(data, dict):
        raise ValueError("S2D.5 config must be a mapping")
    section = data.get("s2d5_learner_limit_audit", {})
    if section is None:
        return {}
    if not isinstance(section, dict):
        raise ValueError("s2d5_learner_limit_audit must be a mapping")
    return dict(section)


def _load_mechanism_records(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text())
    records = data.get("mechanisms")
    if not isinstance(records, list) or not records:
        raise ValueError(f"{path} does not contain non-empty mechanisms")
    return [dict(record) for record in records]


def _load_observations(path: Path) -> tuple[np.ndarray, list[str], int]:
    data = np.load(path)
    observations = np.asarray(data["observations"], dtype=np.float64)
    probe_names = [str(value) for value in data["probe_names"].tolist()]
    shots = int(data["shots"][0]) if "shots" in data.files else int(observations.shape[1])
    return observations, probe_names, shots


def _encode_labels(labels: list[str]) -> tuple[torch.Tensor, list[str]]:
    names = sorted(set(labels))
    index = {name: idx for idx, name in enumerate(names)}
    return torch.tensor([index[label] for label in labels], dtype=torch.long), names


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


def _comparison_labels(records: list[dict[str, object]], name: str) -> list[int] | None:
    try:
        return [int(value) for value in _find_comparison(records, name)["labels"]]
    except KeyError:
        return None


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


def _bernoulli_entropy(target: np.ndarray) -> float:
    q = np.clip(np.asarray(target, dtype=np.float64), NUMERICAL_ZERO, 1.0 - NUMERICAL_ZERO)
    return float(-np.mean(q * np.log(q) + (1.0 - q) * np.log(1.0 - q)))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run S2D.5 learner-limit and representation-v2 audits.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--phys4-dir", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    result = run_s2d5_learner_limit_audit(args.config, phys4_dir=args.phys4_dir, output_dir=args.output_dir)
    print(
        "S2D.5 learner-limit audit complete\n"
        f"  output={result['output_dir']}\n"
        f"  summary={result['summary']}"
    )


if __name__ == "__main__":
    main()
