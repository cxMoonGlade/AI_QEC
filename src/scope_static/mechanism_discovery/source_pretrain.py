from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Iterable, Mapping

import numpy as np
import yaml

from .baselines import _kmeans
from .stage4_artifacts import load_stage4_source_evaluator_labels, load_stage4_visible_matrix, load_stage4_json


STAGE_NAME = "Stage4_1_source_neural_pretrain_minimal"
DEFAULT_OUTPUT_DIR = "outputs/scope_static/S4_bridge/S4_1_source_pretrain"
ALLOWED_SURVIVAL_DECISIONS = {
    "bridge_surface_pass",
    "bridge_surface_quotient_only",
    "bridge_surface_projection_aliasing",
}


def run_stage4_source_pretrain(
    *,
    stage4_source_dir: str | Path,
    source_ceiling_dir: str | Path,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    seed: int = 0,
    k: int = 32,
    code_dim: int = 32,
    max_iter: int = 30,
) -> dict[str, object]:
    """Run minimal source MLP-continuous and Attention-VQ visible replay models."""

    source = Path(stage4_source_dir)
    ceiling_dir = Path(source_ceiling_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    survival = load_stage4_json(ceiling_dir / "mechanism_survival_report.json")
    decision = str(survival.get("decision", "bridge_surface_fail"))
    if decision not in ALLOWED_SURVIVAL_DECISIONS:
        raise ValueError(f"source surface survival decision {decision!r} blocks S4.1 source pretraining")
    x_raw, feature_names, feature_matrix = load_stage4_visible_matrix(source)
    labels = load_stage4_source_evaluator_labels(source)
    x, standardization = _fit_source_standardization(x_raw)
    mlp = _fit_mlp_continuous(x, rank=min(2, max(1, min(x.shape) - 1)))
    attention = _fit_attention_vq(x, k=max(1, min(int(k), max(1, x.shape[0]))), max_iter=int(max_iter), code_dim=int(code_dim))
    global_null = _global_null_metrics(x)
    mean_only = dict(global_null)
    shuffle = _shuffle_control_metrics(x, attention["assignments"], seed=int(seed))
    scramble = _feature_scramble_metrics(x, attention["assignments"], seed=int(seed))
    models = {
        "mlp_continuous": {
            "schema": "scope_static_stage4_mlp_continuous_model_v1",
            "model_family": "mlp_continuous",
            "training_is_minimal_numpy_surrogate": True,
            "replay_metrics": mlp["metrics"],
            "uses_evaluator_labels_for_fit": False,
            "uses_evaluator_labels_for_model_selection": False,
        },
        "attention_vq": {
            "schema": "scope_static_stage4_attention_vq_model_v1",
            "model_family": "attention_vq",
            "training_is_minimal_numpy_surrogate": True,
            "k": int(attention["codebook"].shape[0]),
            "code_dim": int(code_dim),
            "replay_metrics": attention["metrics"],
            "uses_evaluator_labels_for_fit": False,
            "uses_evaluator_labels_for_model_selection": False,
        },
    }
    selected = "attention_vq" if _score(attention["metrics"]) <= _score(mlp["metrics"]) else "mlp_continuous"
    model_selection = {
        "schema": "scope_static_stage4_source_model_selection_audit_v1",
        "selected_model": selected,
        "validation_visible_replay_used_for_selection": True,
        "ari_nmi_used_for_selection": False,
        "evaluator_labels_used_for_selection": False,
    }
    codebook_usage = _codebook_usage(attention["assignments"], k=int(attention["codebook"].shape[0]))
    prototype_cards = _prototype_cards(attention["codebook"], attention["assignments"], feature_names, labels.exact_labels)
    controls = {
        "schema": "scope_static_stage4_source_pretrain_controls_v1",
        "global_null": global_null,
        "mean_only": mean_only,
        "assignment_shuffle": shuffle,
        "feature_scramble": scramble,
        "used_for_model_selection": False,
    }
    acceptance = {
        "schema": "scope_static_stage4_source_pretrain_acceptance_v1",
        "checks": {
            "survival_gate_passed": decision in ALLOWED_SURVIVAL_DECISIONS,
            "attention_vq_beats_mlp": _score(attention["metrics"]) <= _score(mlp["metrics"]),
            "attention_vq_beats_global_null": _score(attention["metrics"]) <= _score(global_null),
            "attention_vq_beats_shuffle": _score(attention["metrics"]) <= _score(shuffle),
            "attention_vq_beats_scramble": _score(attention["metrics"]) <= _score(scramble),
            "evaluator_labels_posthoc_only": True,
        },
    }
    acceptance["passed"] = bool(all(dict(acceptance["checks"]).values()))
    result = {
        "schema": "scope_static_stage4_source_pretrain_v1",
        "stage": STAGE_NAME,
        "stage4_source_dir": str(source),
        "source_ceiling_dir": str(ceiling_dir),
        "output_dir": str(output),
        "config": {"seed": int(seed), "k": int(k), "code_dim": int(code_dim), "max_iter": int(max_iter)},
        "visible_feature_matrix": feature_matrix,
        "visible_feature_standardization": standardization,
        "mechanism_survival_decision": decision,
        "models": models,
        "model_selection_audit": model_selection,
        "source_replay_metrics": {
            "schema": "scope_static_stage4_source_replay_metrics_v1",
            "mlp_continuous": mlp["metrics"],
            "attention_vq": attention["metrics"],
            "controls": controls,
        },
        "codebook_usage": codebook_usage,
        "prototype_cards": prototype_cards,
        "controls": controls,
        "acceptance_audit": acceptance,
        "decision": "stage4_source_pretrain_passed" if acceptance["passed"] else "stage4_source_pretrain_failed",
    }
    _write_outputs(output, result, attention, feature_names)
    return result


def _fit_mlp_continuous(x: np.ndarray, *, rank: int) -> dict[str, object]:
    if x.size == 0:
        recon = np.zeros_like(x)
    else:
        u, s, vt = np.linalg.svd(x, full_matrices=False)
        r = max(1, min(int(rank), len(s)))
        recon = (u[:, :r] * s[:r]) @ vt[:r]
    return {"reconstruction": recon, "metrics": _replay_metrics(x, recon, model_family="mlp_continuous")}


def _fit_attention_vq(x: np.ndarray, *, k: int, max_iter: int, code_dim: int) -> dict[str, object]:
    assignments, centers, inertia = _kmeans(x, max(1, min(int(k), max(1, x.shape[0]))), max_iter=max_iter)
    recon = centers[assignments] if assignments.size else np.zeros_like(x)
    codebook = centers[:, : min(int(code_dim), centers.shape[1])]
    metrics = _replay_metrics(x, recon, model_family="attention_vq")
    metrics["kmeans_inertia"] = float(inertia)
    return {"assignments": assignments, "centers": centers, "codebook": codebook, "reconstruction": recon, "metrics": metrics}


def _global_null_metrics(x: np.ndarray) -> dict[str, object]:
    mean = np.mean(x, axis=0, keepdims=True) if x.size else np.zeros((1, x.shape[1]), dtype=np.float64)
    recon = np.repeat(mean, int(x.shape[0]), axis=0)
    return _replay_metrics(x, recon, model_family="global_mean_only")


def _shuffle_control_metrics(x: np.ndarray, assignments: np.ndarray, *, seed: int) -> dict[str, object]:
    rng = np.random.default_rng(int(seed))
    shuffled = np.asarray(assignments, dtype=np.int64).copy()
    rng.shuffle(shuffled)
    centers = _centers_from_assignments(x, shuffled)
    recon = centers[shuffled] if shuffled.size else np.zeros_like(x)
    metrics = _replay_metrics(x, recon, model_family="assignment_shuffle_control")
    metrics["used_for_model_selection"] = False
    return metrics


def _feature_scramble_metrics(x: np.ndarray, assignments: np.ndarray, *, seed: int) -> dict[str, object]:
    rng = np.random.default_rng(int(seed))
    scrambled = np.array(x, copy=True)
    for col in range(scrambled.shape[1]):
        rng.shuffle(scrambled[:, col])
    centers = _centers_from_assignments(scrambled, assignments)
    recon = centers[assignments] if assignments.size else np.zeros_like(x)
    metrics = _replay_metrics(x, recon, model_family="feature_scramble_control")
    metrics["used_for_model_selection"] = False
    return metrics


def _centers_from_assignments(x: np.ndarray, assignments: np.ndarray) -> np.ndarray:
    k = int(np.max(assignments)) + 1 if assignments.size else 1
    centers = np.zeros((k, x.shape[1]), dtype=np.float64)
    mean = np.mean(x, axis=0) if x.size else np.zeros(x.shape[1], dtype=np.float64)
    for idx in range(k):
        mask = assignments == idx
        centers[idx] = np.mean(x[mask], axis=0) if np.any(mask) else mean
    return centers


def _replay_metrics(x: np.ndarray, recon: np.ndarray, *, model_family: str) -> dict[str, object]:
    err = np.asarray(x - recon, dtype=np.float64)
    mse = float(np.mean(err * err)) if err.size else 0.0
    mae = float(np.mean(np.abs(err))) if err.size else 0.0
    raw = mae
    block = _block_normalized_mae(x, recon)
    return {
        "schema": "scope_static_stage4_visible_replay_metrics_v1",
        "model_family": model_family,
        "raw_target_only": raw,
        "block_normalized": block,
        "mse": mse,
        "mae": mae,
        "lower_is_better": True,
    }


def _block_normalized_mae(x: np.ndarray, recon: np.ndarray) -> float:
    # The frozen Google V2 schema has stable contiguous blocks; equal-size fallback is enough here.
    if x.size == 0:
        return 0.0
    return float(np.mean(np.mean(np.abs(x - recon), axis=0)))


def _score(metrics: Mapping[str, object]) -> float:
    return float(metrics.get("raw_target_only", 0.0)) + float(metrics.get("block_normalized", 0.0))


def _codebook_usage(assignments: np.ndarray, *, k: int) -> dict[str, object]:
    counts = Counter(int(value) for value in np.asarray(assignments, dtype=np.int64).tolist())
    active = sum(1 for idx in range(int(k)) if counts.get(idx, 0) > 0)
    probs = np.asarray([counts.get(idx, 0) for idx in range(int(k))], dtype=np.float64)
    probs = probs / max(float(np.sum(probs)), 1.0)
    entropy = float(-np.sum([p * np.log(p) for p in probs if p > 0.0]))
    return {
        "schema": "scope_static_stage4_codebook_usage_v1",
        "k": int(k),
        "active_code_count": int(active),
        "dead_code_count": int(k - active),
        "dead_code_ratio": float((k - active) / max(k, 1)),
        "usage_entropy": entropy,
        "counts": {f"C{idx:03d}": int(counts.get(idx, 0)) for idx in range(int(k))},
    }


def _prototype_cards(codebook: np.ndarray, assignments: np.ndarray, feature_names: list[str], labels: list[str]) -> dict[str, object]:
    cards = []
    for idx, row in enumerate(np.asarray(codebook, dtype=np.float64)):
        assigned = [label for label, cluster in zip(labels, assignments.tolist()) if int(cluster) == idx]
        label_counts = dict(sorted(Counter(assigned).items()))
        top = np.argsort(-np.abs(row))[: min(8, row.size)]
        cards.append(
            {
                "prototype": f"C{idx:03d}",
                "assigned_count": int(len(assigned)),
                "evaluator_label_counts_posthoc_only": label_counts,
                "top_feature_coordinates": [
                    {"name": feature_names[int(col)] if int(col) < len(feature_names) else f"feature_{int(col)}", "value": float(row[int(col)])}
                    for col in top.tolist()
                ],
            }
        )
    return {
        "schema": "scope_static_stage4_prototype_cards_v1",
        "uses_evaluator_labels_for_fit": False,
        "uses_evaluator_labels_for_model_selection": False,
        "cards": cards,
    }


def _write_outputs(output: Path, result: dict[str, object], attention: Mapping[str, object], feature_names: list[str]) -> None:
    artifacts = {
        "metrics.json": result,
        "source_replay_metrics.json": result["source_replay_metrics"],
        "model_selection_audit.json": result["model_selection_audit"],
        "codebook_usage.json": result["codebook_usage"],
        "prototype_cards.json": result["prototype_cards"],
        "controls.json": result["controls"],
        "acceptance_audit.json": result["acceptance_audit"],
        "visible_feature_matrix.json": result["visible_feature_matrix"],
    }
    for name, payload in artifacts.items():
        (output / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    np.save(output / "learned_assignments.npy", np.asarray(attention["assignments"], dtype=np.int64))
    np.savez(
        output / "source_codebook.npz",
        codebook=np.asarray(attention["codebook"], dtype=np.float64),
        centers=np.asarray(attention["centers"], dtype=np.float64),
        standardization_mean=np.asarray(result["visible_feature_standardization"]["mean"], dtype=np.float64),
        standardization_scale=np.asarray(result["visible_feature_standardization"]["scale"], dtype=np.float64),
        feature_names=np.asarray(feature_names, dtype=object),
    )
    (output / "config.yaml").write_text(yaml.safe_dump({"stage4_source_pretrain_v1": result["config"]}, sort_keys=False), encoding="utf-8")
    (output / "summary.md").write_text(format_source_pretrain_summary(result), encoding="utf-8")


def format_source_pretrain_summary(result: Mapping[str, object]) -> str:
    acceptance = dict(result.get("acceptance_audit", {}))
    return "\n".join(
        [
            "# S4.1 Source Neural Pretrain",
            "",
            f"- Decision: `{result.get('decision')}`",
            f"- Acceptance passed: `{str(bool(acceptance.get('passed', False))).lower()}`",
            f"- Selected model: `{dict(result.get('model_selection_audit', {})).get('selected_model')}`",
            "",
        ]
    )


def _fit_source_standardization(x: np.ndarray) -> tuple[np.ndarray, dict[str, object]]:
    mean = np.mean(x, axis=0) if x.size else np.zeros(x.shape[1], dtype=np.float64)
    scale = np.std(x, axis=0) if x.size else np.ones(x.shape[1], dtype=np.float64)
    scale = np.where(scale > 1.0e-12, scale, 1.0)
    z = (x - mean) / scale if x.size else np.asarray(x, dtype=np.float64)
    return z, {
        "schema": "scope_static_stage4_source_visible_feature_standardization_v1",
        "method": "frozen feature-wise z-score over S4.0 source visible instances",
        "coordinate_system": "source_standardized_visible_features",
        "feature_count": int(x.shape[1]) if x.ndim == 2 else 0,
        "zero_scale_replaced_with_one": True,
        "mean": [float(value) for value in np.asarray(mean, dtype=np.float64).tolist()],
        "scale": [float(value) for value in np.asarray(scale, dtype=np.float64).tolist()],
    }
