from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Mapping

import numpy as np
import yaml

from scope_static.dem.metrics import normalized_mutual_info

from .artifacts import load_stage3a_frozen_visible_features
from .google_transfer import (
    _apply_source_standardization,
    _assign_to_source_centers,
    _fit_assignment_replay_head,
    _global_null_transfer,
    _load_source_standardization,
    _random_codebook_transfer,
)
from .source_pretrain import _fit_attention_vq, _replay_metrics
from .stage4_artifacts import load_stage4_visible_matrix


STAGE_NAME = "Stage4_5_assignment_geometry_repair"
DEFAULT_OUTPUT_DIR = "outputs/scope_static/S4_bridge/S4_5_assignment_geometry_repair"


def run_stage4_assignment_geometry_repair(
    *,
    stage4_source_dir: str | Path,
    source_pretrain_dir: str | Path,
    google_stage3a_dir: str | Path,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    seed: int = 0,
    k: int = 32,
) -> dict[str, object]:
    """Audit and repair frozen source assignment geometry without labels."""

    source_dir = Path(stage4_source_dir)
    pretrain_dir = Path(source_pretrain_dir)
    google_dir = Path(google_stage3a_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    source_raw, source_feature_names, source_manifest = load_stage4_visible_matrix(source_dir)
    google_raw, google_feature_names, google_manifest = load_stage3a_frozen_visible_features(google_dir)
    if list(source_feature_names) != list(google_feature_names):
        raise ValueError("source and Google feature schemas must match for assignment geometry repair")

    payload = np.load(pretrain_dir / "source_codebook.npz", allow_pickle=True)
    centers = np.asarray(payload["centers"], dtype=np.float64)
    standardization = _load_source_standardization(payload, feature_count=int(source_raw.shape[1]))
    mean = np.asarray(standardization["mean"], dtype=np.float64)
    scale = np.asarray(standardization["scale"], dtype=np.float64)
    source_z = _apply_source_standardization(source_raw, mean=mean, scale=scale)
    google_z = _apply_source_standardization(google_raw, mean=mean, scale=scale)

    source_assignments, source_center_recon_z = _assign_to_source_centers(source_z, centers)
    google_assignments, google_center_recon_z = _assign_to_source_centers(google_z, centers)
    source_replay = _fit_assignment_replay_head(source_raw, source_assignments, code_count=int(centers.shape[0]))
    google_replay = _fit_assignment_replay_head(google_raw, google_assignments, code_count=int(centers.shape[0]))
    strict_metrics = _replay_metrics(google_raw, np.asarray(google_replay["reconstruction"], dtype=np.float64), model_family="strict_frozen_assignment_replay_head")
    global_null = _global_null_transfer(google_raw)
    random = _random_codebook_transfer(
        google_raw,
        google_z,
        centers,
        mean=mean,
        scale=scale,
        seed=int(seed),
    )

    assignment_geometry = _assignment_geometry_audit(
        source_raw=source_raw,
        source_z=source_z,
        source_assignments=source_assignments,
        source_reconstruction=np.asarray(source_replay["reconstruction"], dtype=np.float64),
        google_raw=google_raw,
        google_z=google_z,
        google_assignments=google_assignments,
        google_reconstruction=np.asarray(google_replay["reconstruction"], dtype=np.float64),
        centers=centers,
        feature_names=google_feature_names,
        google_stage3a_dir=google_dir,
    )
    soft = _soft_reassignment_diagnostic(
        google_raw=google_raw,
        google_z=google_z,
        centers=centers,
        feature_names=google_feature_names,
    )
    native = _google_native_partition_alignment(
        google_raw=google_raw,
        google_z=google_z,
        source_assignments=google_assignments,
        source_centers=centers,
        seed=int(seed),
        k=max(1, min(int(k), int(google_raw.shape[0]))),
    )
    raw_only = _raw_only_codebook_branch(
        google_raw=google_raw,
        google_z=google_z,
        centers=centers,
        feature_names=google_feature_names,
    )
    gap = _gap_closure(
        frozen=strict_metrics,
        global_null=global_null,
        train_on_google=native["google_native_replay_metrics"],
    )
    acceptance = _assignment_geometry_acceptance(
        strict_metrics=strict_metrics,
        soft_metrics=soft["selected_metrics"],
        random_metrics=random,
        global_metrics=global_null,
        native=native,
        raw_only=raw_only,
        assignment_geometry=assignment_geometry,
        gap=gap,
    )
    result = {
        "schema": "scope_static_stage4_assignment_geometry_repair_v1",
        "stage": STAGE_NAME,
        "stage4_source_dir": str(source_dir),
        "source_pretrain_dir": str(pretrain_dir),
        "google_stage3a_dir": str(google_dir),
        "output_dir": str(output),
        "config": {"seed": int(seed), "k": int(k)},
        "visible_feature_matrix": {
            "source": source_manifest,
            "google": google_manifest,
        },
        "claim_boundary": {
            "diagnostic_only_not_s4_2_main_claim": True,
            "uses_google_visible_features_only": True,
            "uses_google_ground_truth_mechanism_labels": False,
            "uses_evaluator_labels_for_training_or_selection": False,
            "trains_source_code_vectors": False,
        },
        "assignment_geometry_audit": assignment_geometry,
        "frozen_codebook_soft_reassignment": soft,
        "google_native_partition_alignment": native,
        "raw_only_codebook_branch": raw_only,
        "baseline_metrics": {
            "schema": "scope_static_stage4_assignment_geometry_baselines_v1",
            "strict_frozen_assignment_replay_head": strict_metrics,
            "random_codebook_replay_head": random,
            "global_null": global_null,
        },
        "gap_closure": gap,
        "acceptance_audit": acceptance,
        "decision": "s4_assignment_geometry_repaired" if acceptance["passed"] else "s4_assignment_geometry_repair_incomplete",
    }
    _write_outputs(output, result)
    return result


def _assignment_geometry_audit(
    *,
    source_raw: np.ndarray,
    source_z: np.ndarray,
    source_assignments: np.ndarray,
    source_reconstruction: np.ndarray,
    google_raw: np.ndarray,
    google_z: np.ndarray,
    google_assignments: np.ndarray,
    google_reconstruction: np.ndarray,
    centers: np.ndarray,
    feature_names: list[str],
    google_stage3a_dir: Path,
) -> dict[str, object]:
    distances = np.sqrt(np.maximum(np.sum((google_z - centers[google_assignments]) ** 2, axis=1), 0.0)) if google_assignments.size else np.zeros(0)
    source_distances = np.sqrt(np.maximum(np.sum((source_z - centers[source_assignments]) ** 2, axis=1), 0.0)) if source_assignments.size else np.zeros(0)
    google_contexts = _google_contexts_by_row(google_stage3a_dir)
    per_code: dict[str, object] = {}
    counts = Counter(int(value) for value in google_assignments.tolist())
    expected = max(1.0, float(len(google_assignments)) / max(1, int(centers.shape[0])))
    for code in range(int(centers.shape[0])):
        g_mask = google_assignments == code
        s_mask = source_assignments == code
        code_key = f"C{code:03d}"
        per_code[code_key] = {
            "google_count": int(np.sum(g_mask)),
            "source_count": int(np.sum(s_mask)),
            "google_fraction": float(np.sum(g_mask) / max(1, google_assignments.size)),
            "google_replay_error": _mae_for_mask(google_raw, google_reconstruction, g_mask),
            "source_replay_error": _mae_for_mask(source_raw, source_reconstruction, s_mask),
            "nearest_distance_mean": float(np.mean(distances[g_mask])) if np.any(g_mask) else 0.0,
            "nearest_distance_p50": float(np.quantile(distances[g_mask], 0.50)) if np.any(g_mask) else 0.0,
            "nearest_distance_p90": float(np.quantile(distances[g_mask], 0.90)) if np.any(g_mask) else 0.0,
            "nearest_distance_p95": float(np.quantile(distances[g_mask], 0.95)) if np.any(g_mask) else 0.0,
            "context_distribution": _context_distribution(google_contexts, g_mask),
            "blockwise_error": _blockwise_error(google_raw, google_reconstruction, feature_names, g_mask),
        }
    overloaded = [f"C{code:03d}" for code, count in counts.items() if float(count) > 2.0 * expected or float(count) / max(1, google_assignments.size) > 0.25]
    dead = [f"C{code:03d}" for code in range(int(centers.shape[0])) if counts.get(code, 0) == 0]
    underused = [f"C{code:03d}" for code in range(int(centers.shape[0])) if 0 < counts.get(code, 0) < max(2, int(0.01 * max(1, google_assignments.size)))]
    return {
        "schema": "scope_static_stage4_assignment_geometry_audit_v1",
        "per_code": per_code,
        "per_code_google_count": {key: int(value["google_count"]) for key, value in per_code.items()},
        "dead_or_underused_source_codes_on_google": sorted(set(dead + underused)),
        "dead_source_codes_on_google": dead,
        "underused_source_codes_on_google": underused,
        "overloaded_source_codes_on_google": sorted(overloaded),
        "max_google_code_fraction": float(max(counts.values()) / max(1, google_assignments.size)) if counts else 0.0,
        "active_google_code_count": int(len(counts)),
        "source_nearest_distance_p95": float(np.quantile(source_distances, 0.95)) if source_distances.size else 0.0,
        "google_nearest_distance_p50": float(np.quantile(distances, 0.50)) if distances.size else 0.0,
        "google_nearest_distance_p95": float(np.quantile(distances, 0.95)) if distances.size else 0.0,
    }


def _soft_reassignment_diagnostic(
    *,
    google_raw: np.ndarray,
    google_z: np.ndarray,
    centers: np.ndarray,
    feature_names: list[str],
) -> dict[str, object]:
    profiles = _block_weight_profiles(feature_names)
    temperatures = [0.05, 0.1, 0.25, 0.5, 1.0, 2.0]
    candidates = []
    for profile_name, weights in profiles.items():
        for tau in temperatures:
            q = _soft_assignments(google_z, centers, weights=weights, temperature=float(tau))
            recon, active = _weighted_replay_heads(google_raw, q)
            metrics = _replay_metrics(google_raw, recon, model_family="frozen_codebook_soft_reassignment")
            candidates.append(
                {
                    "profile": profile_name,
                    "temperature": float(tau),
                    "active_soft_code_count": int(active),
                    "metrics": metrics,
                    "score": float(metrics["raw_target_only"]) + float(metrics["block_normalized"]),
                }
            )
    selected = min(candidates, key=lambda row: float(row["score"])) if candidates else {}
    return {
        "schema": "scope_static_stage4_frozen_codebook_soft_reassignment_v1",
        "diagnostic_only_not_main_claim": True,
        "freezes_code_vectors": True,
        "freezes_source_standardization": True,
        "trains_low_capacity_assignment_metric": True,
        "trains_code_vectors": False,
        "uses_evaluator_labels": False,
        "selected_profile": selected.get("profile"),
        "selected_temperature": selected.get("temperature"),
        "selected_metrics": selected.get("metrics", _replay_metrics(google_raw, google_raw * 0.0, model_family="empty_soft_reassignment")),
        "candidate_count": int(len(candidates)),
        "candidates": candidates,
    }


def _google_native_partition_alignment(
    *,
    google_raw: np.ndarray,
    google_z: np.ndarray,
    source_assignments: np.ndarray,
    source_centers: np.ndarray,
    seed: int,
    k: int,
) -> dict[str, object]:
    native = _fit_attention_vq(google_raw, k=max(1, min(int(k), int(google_raw.shape[0]))), max_iter=30, code_dim=min(google_raw.shape[1], int(k)))
    native_assignments = np.asarray(native["assignments"], dtype=np.int64)
    native_replay = _fit_assignment_replay_head(google_raw, native_assignments, code_count=int(np.max(native_assignments)) + 1 if native_assignments.size else 1)
    native_metrics = _replay_metrics(google_raw, np.asarray(native_replay["reconstruction"], dtype=np.float64), model_family="google_native_visible_partition")
    rng = np.random.default_rng(int(seed))
    random_assignments = rng.integers(0, max(1, int(np.max(source_assignments)) + 1 if source_assignments.size else 1), size=int(source_assignments.size))
    source_native_nmi = _nmi(source_assignments, native_assignments)
    random_native_nmi = _nmi(random_assignments, native_assignments)
    confusion = _confusion_matrix(source_assignments, native_assignments)
    native_centers_raw = np.asarray(native["centers"], dtype=np.float64)
    native_centers_z = _standardize_native_centers_to_source_frame(native_centers_raw, google_raw=google_raw, google_z=google_z)
    nearest = _nearest_source_for_native_centers(native_centers_z, source_centers)
    return {
        "schema": "scope_static_stage4_google_native_partition_alignment_v1",
        "diagnostic_target_native_visible_partition": True,
        "not_ground_truth_mechanism_label": True,
        "uses_google_visible_replay_only": True,
        "native_training_coordinate_system": "raw_google_visible_features",
        "source_code_google_native_code_nmi": source_native_nmi,
        "random_code_google_native_code_nmi": random_native_nmi,
        "nmi_improvement_over_random": float(source_native_nmi - random_native_nmi),
        "conditional_replay_gap": {
            "source_assignment_to_native_partition_gap": None,
            "lower_is_better": True,
        },
        "per_code_confusion_matrix": confusion,
        "nearest_source_prototype_to_each_google_native_prototype": nearest,
        "google_native_replay_metrics": native_metrics,
    }


def _standardize_native_centers_to_source_frame(native_centers_raw: np.ndarray, *, google_raw: np.ndarray, google_z: np.ndarray) -> np.ndarray:
    if native_centers_raw.size == 0:
        return native_centers_raw
    raw_mean = np.mean(google_raw, axis=0) if google_raw.size else np.zeros(google_raw.shape[1], dtype=np.float64)
    raw_std = np.std(google_raw, axis=0) if google_raw.size else np.ones(google_raw.shape[1], dtype=np.float64)
    raw_std = np.where(raw_std > 1.0e-12, raw_std, 1.0)
    z_mean = np.mean(google_z, axis=0) if google_z.size else np.zeros(google_z.shape[1], dtype=np.float64)
    z_std = np.std(google_z, axis=0) if google_z.size else np.ones(google_z.shape[1], dtype=np.float64)
    return ((native_centers_raw - raw_mean[None, :]) / raw_std[None, :]) * z_std[None, :] + z_mean[None, :]


def _raw_only_codebook_branch(
    *,
    google_raw: np.ndarray,
    google_z: np.ndarray,
    centers: np.ndarray,
    feature_names: list[str],
) -> dict[str, object]:
    mask = np.asarray([not str(name).startswith("meta__public_geometry") for name in feature_names], dtype=bool)
    assignments, _recon = _assign_to_source_centers(google_z[:, mask], centers[:, mask])
    replay = _fit_assignment_replay_head(google_raw, assignments, code_count=int(centers.shape[0]))
    metrics = _replay_metrics(google_raw, np.asarray(replay["reconstruction"], dtype=np.float64), model_family="attention_vq_raw_only_assignment")
    return {
        "schema": "scope_static_stage4_raw_only_codebook_branch_v1",
        "assignment_input_blocks": sorted({str(name).split("__")[0] + "__" + str(name).split("__")[1] for name in feature_names if mask[feature_names.index(name)] and "__" in str(name)}),
        "excludes_meta_public_geometry_from_assignment": True,
        "meta_public_geometry_allowed_for_replay_head_or_diagnostics": True,
        "feature_count_used_for_assignment": int(np.sum(mask)),
        "active_code_count": int(len(set(assignments.tolist())) if assignments.size else 0),
        "metrics": metrics,
    }


def _gap_closure(*, frozen: Mapping[str, object], global_null: Mapping[str, object], train_on_google: Mapping[str, object]) -> dict[str, object]:
    global_score = float(global_null.get("raw_target_only", 0.0) or 0.0)
    frozen_score = float(frozen.get("raw_target_only", 0.0) or 0.0)
    native_score = float(train_on_google.get("raw_target_only", 0.0) or 0.0)
    denom = max(global_score - native_score, 1.0e-12)
    return {
        "schema": "scope_static_stage4_gap_closure_v1",
        "fraction_of_train_on_google_gain_closed": float((global_score - frozen_score) / denom),
        "global_null_raw_target_only": global_score,
        "frozen_source_raw_target_only": frozen_score,
        "train_on_google_raw_target_only": native_score,
    }


def _assignment_geometry_acceptance(
    *,
    strict_metrics: Mapping[str, object],
    soft_metrics: Mapping[str, object],
    random_metrics: Mapping[str, object],
    global_metrics: Mapping[str, object],
    native: Mapping[str, object],
    raw_only: Mapping[str, object],
    assignment_geometry: Mapping[str, object],
    gap: Mapping[str, object],
) -> dict[str, object]:
    best_frozen = min(float(strict_metrics["raw_target_only"]), float(soft_metrics["raw_target_only"]))
    checks = {
        "strict_or_soft_beats_global_null": best_frozen < float(global_metrics["raw_target_only"]),
        "strict_or_soft_beats_random_codebook": best_frozen < float(random_metrics["raw_target_only"]),
        "source_native_nmi_beats_random": float(native.get("nmi_improvement_over_random", 0.0)) > 0.0,
        "per_code_replay_not_single_overloaded_code": float(assignment_geometry.get("max_google_code_fraction", 1.0)) < 0.50,
        "raw_only_replay_is_reported": bool(raw_only.get("metrics")),
        "gap_closure_at_least_0_50": float(gap.get("fraction_of_train_on_google_gain_closed", 0.0)) >= 0.50,
    }
    return {
        "schema": "scope_static_stage4_assignment_geometry_acceptance_v1",
        "checks": checks,
        "passed": bool(all(checks.values())),
        "decision_if_passed": "s4_assignment_geometry_repaired",
        "decision_if_failed": "s4_assignment_geometry_repair_incomplete",
    }


def _soft_assignments(x: np.ndarray, centers: np.ndarray, *, weights: np.ndarray, temperature: float) -> np.ndarray:
    weighted_delta = (x[:, None, :] - centers[None, :, :]) ** 2 * weights[None, None, :]
    logits = -float(temperature) * np.sum(weighted_delta, axis=2)
    logits = logits - np.max(logits, axis=1, keepdims=True)
    exp = np.exp(logits)
    return exp / np.maximum(np.sum(exp, axis=1, keepdims=True), 1.0e-12)


def _weighted_replay_heads(x: np.ndarray, q: np.ndarray) -> tuple[np.ndarray, int]:
    denom = np.sum(q, axis=0)
    heads = np.divide(q.T @ x, denom[:, None], out=np.zeros((q.shape[1], x.shape[1]), dtype=np.float64), where=denom[:, None] > 1.0e-12)
    global_mean = np.mean(x, axis=0) if x.size else np.zeros(x.shape[1], dtype=np.float64)
    heads[denom <= 1.0e-12] = global_mean
    recon = q @ heads
    active = int(np.sum(denom > 1.0e-3))
    return recon, active


def _block_weight_profiles(feature_names: list[str]) -> dict[str, np.ndarray]:
    uniform = np.ones(len(feature_names), dtype=np.float64)
    raw_only = np.asarray([0.0 if str(name).startswith("meta__public_geometry") else 1.0 for name in feature_names], dtype=np.float64)
    no_stability = np.asarray([0.25 if str(name).startswith("raw__stability") else 1.0 for name in feature_names], dtype=np.float64)
    raw_context_light = np.asarray([0.10 if str(name).startswith("meta__public_geometry") else 1.0 for name in feature_names], dtype=np.float64)
    return {
        "uniform": uniform,
        "raw_only": raw_only,
        "metadata_light": raw_context_light,
        "stability_light": no_stability,
    }


def _google_contexts_by_row(google_stage3a_dir: Path) -> list[dict[str, object]]:
    path = google_stage3a_dir / "split_manifest.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("assignment_instances", [])
    if not isinstance(rows, list):
        return []
    return [dict(row.get("public_fields", {})) if isinstance(row, Mapping) and isinstance(row.get("public_fields", {}), Mapping) else {} for row in rows]


def _context_distribution(contexts: list[dict[str, object]], mask: np.ndarray) -> dict[str, object]:
    selected = [contexts[idx] for idx, flag in enumerate(mask.tolist()) if flag and idx < len(contexts)]
    out = {}
    for key in ["basis", "distance", "rounds", "round_band", "region_family"]:
        out[key] = dict(sorted(Counter(str(row.get(key, "")) for row in selected).items()))
    return out


def _blockwise_error(x: np.ndarray, recon: np.ndarray, feature_names: list[str], mask: np.ndarray) -> dict[str, float]:
    blocks: dict[str, list[int]] = defaultdict(list)
    for idx, name in enumerate(feature_names):
        parts = str(name).split("__")
        blocks["__".join(parts[:2]) if len(parts) >= 2 else str(name)].append(idx)
    if not np.any(mask):
        return {block: 0.0 for block in sorted(blocks)}
    return {
        block: float(np.mean(np.abs(x[mask][:, indices] - recon[mask][:, indices]))) if indices else 0.0
        for block, indices in sorted(blocks.items())
    }


def _mae_for_mask(x: np.ndarray, recon: np.ndarray, mask: np.ndarray) -> float:
    return float(np.mean(np.abs(x[mask] - recon[mask]))) if np.any(mask) else 0.0


def _nmi(left: np.ndarray, right: np.ndarray) -> float:
    return float(normalized_mutual_info(_encode(left), _encode(right)))


def _encode(values: np.ndarray) -> list[int]:
    mapping: dict[str, int] = {}
    out = []
    for value in values.tolist():
        key = str(int(value))
        if key not in mapping:
            mapping[key] = len(mapping)
        out.append(mapping[key])
    return out


def _confusion_matrix(left: np.ndarray, right: np.ndarray) -> dict[str, object]:
    left_names = sorted(set(int(value) for value in left.tolist()))
    right_names = sorted(set(int(value) for value in right.tolist()))
    matrix = np.zeros((len(left_names), len(right_names)), dtype=np.int64)
    left_index = {value: idx for idx, value in enumerate(left_names)}
    right_index = {value: idx for idx, value in enumerate(right_names)}
    for a, b in zip(left.tolist(), right.tolist()):
        matrix[left_index[int(a)], right_index[int(b)]] += 1
    return {
        "source_code_names": [f"C{value:03d}" for value in left_names],
        "google_native_code_names": [f"G{value:03d}" for value in right_names],
        "counts": matrix.tolist(),
    }


def _nearest_source_for_native_centers(native_centers: np.ndarray, source_centers: np.ndarray) -> list[dict[str, object]]:
    distances = np.sum((native_centers[:, None, :] - source_centers[None, :, :]) ** 2, axis=2)
    nearest = np.argmin(distances, axis=1) if distances.size else np.zeros(0, dtype=np.int64)
    return [
        {
            "google_native_code": f"G{idx:03d}",
            "nearest_source_code": f"C{int(code):03d}",
            "squared_distance": float(distances[idx, int(code)]),
        }
        for idx, code in enumerate(nearest.tolist())
    ]


def _write_outputs(output: Path, result: Mapping[str, object]) -> None:
    artifacts = {
        "metrics.json": result,
        "assignment_geometry_audit.json": result["assignment_geometry_audit"],
        "frozen_codebook_soft_reassignment.json": result["frozen_codebook_soft_reassignment"],
        "google_native_partition_alignment.json": result["google_native_partition_alignment"],
        "raw_only_codebook_branch.json": result["raw_only_codebook_branch"],
        "gap_closure.json": result["gap_closure"],
        "acceptance_audit.json": result["acceptance_audit"],
    }
    for name, payload in artifacts.items():
        (output / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "config.yaml").write_text(yaml.safe_dump({"stage4_assignment_geometry_v1": result["config"]}, sort_keys=False), encoding="utf-8")
    (output / "summary.md").write_text(format_assignment_geometry_summary(result), encoding="utf-8")


def format_assignment_geometry_summary(result: Mapping[str, object]) -> str:
    gap = dict(result.get("gap_closure", {}))
    audit = dict(result.get("assignment_geometry_audit", {}))
    return "\n".join(
        [
            "# S4.5 Assignment Geometry Repair",
            "",
            f"- Decision: `{result.get('decision')}`",
            f"- Gap closure: `{float(gap.get('fraction_of_train_on_google_gain_closed', 0.0)):.4f}`",
            f"- Active Google source codes: `{int(audit.get('active_google_code_count', 0))}`",
            f"- Max Google code fraction: `{float(audit.get('max_google_code_fraction', 0.0)):.4f}`",
            "",
        ]
    )
