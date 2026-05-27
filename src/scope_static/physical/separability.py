from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch

from scope_static.identifiability import deterministic_kmeans, evaluate_partition
from scope_static.local_mechanism import split_merge_audit
from scope_static.numerics import NUMERICAL_ZERO

from .channels import MechanismSpec
from .ptm import channel_fingerprint, probe_response_fingerprint, rzz_type_feature_names, rzz_type_feature_vector


def run_oracle_separability_audit(
    *,
    teacher_dir: str | Path = "outputs/scope_static/S2D_PHYS1_teacher",
    output_dir: str | Path = "outputs/scope_static/S2D_PHYS2_oracle_separability",
    paper_informed: bool = True,
) -> dict[str, object]:
    teacher = Path(teacher_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    records = _load_mechanism_records(teacher / "oracle_mechanisms.json")
    labels, label_names = _encode_labels([str(record["oracle_label"]) for record in records])
    specs = [_spec_from_record(record) for record in records]
    ptm_fingerprints = np.stack([channel_fingerprint(spec, paper_informed=paper_informed) for spec in specs], axis=0)
    probe_fingerprints = np.stack([probe_response_fingerprint(spec) for spec in specs], axis=0)
    rzz_type_features = np.stack([rzz_type_feature_vector(spec) for spec in specs], axis=0)
    parts = [ptm_fingerprints, probe_fingerprints]
    if bool(paper_informed):
        parts.append(rzz_type_features)
    fingerprints = np.concatenate(parts, axis=1)
    np.save(output / "ptm_fingerprints.npy", ptm_fingerprints)
    np.save(output / "probe_fingerprints.npy", probe_fingerprints)
    np.save(output / "rzz_type_features.npy", rzz_type_features)
    np.save(output / "fingerprints.npy", fingerprints)

    k = len(label_names)
    clustering = deterministic_kmeans(torch.as_tensor(fingerprints, dtype=torch.float64), k)
    partition = evaluate_partition(clustering.labels, labels, num_clusters=k)
    split_merge = split_merge_audit(clustering.labels, labels)
    confusion = _confusion_matrix(clustering.labels.tolist(), labels.tolist(), num_pred=k, num_true=k)
    metrics = {
        "schema": "scope_static_s2d_oracle_separability_v1",
        "stage": "S2D_PHYS2_oracle_separability",
        "teacher_dir": str(teacher),
        "output_dir": str(output),
        "paper_informed_ptm_features": bool(paper_informed),
        "fingerprint_families": {
            "ptm": {"shape": [int(ptm_fingerprints.shape[0]), int(ptm_fingerprints.shape[1])]},
            "probe_response": {
                "shape": [int(probe_fingerprints.shape[0]), int(probe_fingerprints.shape[1])],
                "source": "oracle_channel_probe_responses",
            },
            "rzz_type_features": {
                "shape": [int(rzz_type_features.shape[0]), int(rzz_type_features.shape[1])],
                "enabled_in_combined": bool(paper_informed),
                "feature_names": rzz_type_feature_names(),
            },
        },
        "num_locations": len(records),
        "oracle_label_names": label_names,
        "feature_shape": [int(fingerprints.shape[0]), int(fingerprints.shape[1])],
        "ari": float(partition["ari"]),
        "nmi": float(partition["nmi"]),
        "ari_nmi_used_for_selection": False,
        "active_clusters": int(partition["active_clusters"]),
        "cluster_masses": partition["cluster_masses"],
        "nearest_class_margin": _nearest_class_margin(fingerprints, labels.numpy()),
        "pairwise_mechanism_distance": _pairwise_class_distances(fingerprints, labels.numpy(), label_names),
        "separability_gate": _separability_gate(float(partition["ari"]), float(partition["nmi"])),
        "confusion_matrix": confusion,
        "labels": [int(value) for value in clustering.labels.tolist()],
        **split_merge,
    }
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n")
    (output / "confusion_matrix.json").write_text(json.dumps({"matrix": confusion, "oracle_label_names": label_names}, indent=2) + "\n")
    (output / "summary.md").write_text(format_separability_summary(metrics))
    return metrics


def fingerprint_from_record(record: dict[str, object], *, paper_informed: bool = False) -> np.ndarray:
    spec = _spec_from_record(record)
    return channel_fingerprint(spec, paper_informed=paper_informed)


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


def format_separability_summary(metrics: dict[str, object]) -> str:
    lines = [
        "# S2D PHYS2 Oracle Separability",
        "",
        f"- Gate: `{metrics['separability_gate']}`",
        f"- ARI: `{float(metrics['ari']):.4f}`",
        f"- NMI: `{float(metrics['nmi']):.4f}`",
        f"- Active clusters: `{metrics['active_clusters']}`",
        f"- Nearest-class margin: `{float(metrics['nearest_class_margin']):.4f}`",
        "",
        "| mechanism pair | distance |",
        "| --- | ---: |",
    ]
    distances = metrics.get("pairwise_mechanism_distance", {})
    if isinstance(distances, dict):
        for key, value in sorted(distances.items()):
            lines.append(f"| {key} | {float(value):.4f} |")
    lines.append("")
    return "\n".join(lines)


def _load_mechanism_records(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text())
    records = data.get("mechanisms")
    if not isinstance(records, list) or not records:
        raise ValueError(f"{path} does not contain non-empty mechanisms")
    return [dict(record) for record in records]


def _encode_labels(labels: list[str]) -> tuple[torch.Tensor, list[str]]:
    names = sorted(set(labels))
    index = {name: idx for idx, name in enumerate(names)}
    return torch.tensor([index[label] for label in labels], dtype=torch.long), names


def _confusion_matrix(pred: list[int], true: list[int], *, num_pred: int, num_true: int) -> list[list[int]]:
    matrix = [[0 for _ in range(num_true)] for _ in range(num_pred)]
    for left, right in zip(pred, true):
        matrix[int(left)][int(right)] += 1
    return matrix


def _nearest_class_margin(features: np.ndarray, labels: np.ndarray) -> float:
    x = _standardize(features)
    centers = _class_centers(x, labels)
    if len(centers) <= 1:
        return 0.0
    margins = []
    for row, label in zip(x, labels):
        own = float(np.linalg.norm(row - centers[int(label)]))
        other = min(float(np.linalg.norm(row - center)) for key, center in centers.items() if key != int(label))
        margins.append(other - own)
    return float(np.mean(margins)) if margins else 0.0


def _pairwise_class_distances(features: np.ndarray, labels: np.ndarray, names: list[str]) -> dict[str, float]:
    x = _standardize(features)
    centers = _class_centers(x, labels)
    distances: dict[str, float] = {}
    for left in range(len(names)):
        for right in range(left + 1, len(names)):
            if left in centers and right in centers:
                distances[f"{names[left]}__{names[right]}"] = float(np.linalg.norm(centers[left] - centers[right]))
    return distances


def _class_centers(features: np.ndarray, labels: np.ndarray) -> dict[int, np.ndarray]:
    centers = {}
    for label in sorted(set(int(value) for value in labels.tolist())):
        centers[label] = features[labels == label].mean(axis=0)
    return centers


def _standardize(features: np.ndarray) -> np.ndarray:
    x = np.nan_to_num(np.asarray(features, dtype=np.float64), nan=NUMERICAL_ZERO, posinf=NUMERICAL_ZERO, neginf=-NUMERICAL_ZERO)
    scale = x.std(axis=0)
    scale[scale < NUMERICAL_ZERO] = 1.0
    return (x - x.mean(axis=0)) / scale


def _separability_gate(ari: float, nmi: float) -> str:
    score = min(float(ari), float(nmi))
    if score >= 0.90:
        return "identifying"
    if score >= 0.70:
        return "limited_but_usable"
    return "probe_set_insufficient"
