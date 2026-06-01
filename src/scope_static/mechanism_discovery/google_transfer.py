from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

import numpy as np
import yaml

from .artifacts import load_stage3a_frozen_visible_features
from .source_pretrain import _block_normalized_mae, _centers_from_assignments, _fit_attention_vq, _replay_metrics


STAGE_NAME = "Stage4_2_frozen_google_transfer"
DIAGNOSTIC_STAGE_NAME = "Stage4_3_transfer_diagnostics"
DEFAULT_OUTPUT_DIR = "outputs/scope_static/S4_bridge/S4_2_frozen_google_transfer"
DEFAULT_DIAGNOSTIC_OUTPUT_DIR = "outputs/scope_static/S4_bridge/S4_3_transfer_diagnostics"
STRICT_FROZEN_TRANSFER = "strict_frozen_transfer"
FROZEN_CODEBOOK_TRAIN_ADAPTER = "frozen_codebook_train_adapter"


def run_stage4_google_transfer(
    *,
    source_pretrain_dir: str | Path,
    google_stage3a_dir: str | Path,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    seed: int = 0,
    transfer_mode: str = STRICT_FROZEN_TRANSFER,
) -> dict[str, object]:
    source_dir = Path(source_pretrain_dir)
    google_dir = Path(google_stage3a_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    if transfer_mode not in {STRICT_FROZEN_TRANSFER, FROZEN_CODEBOOK_TRAIN_ADAPTER}:
        raise ValueError(f"unknown transfer_mode {transfer_mode!r}")
    x_raw, feature_names, feature_matrix = load_stage3a_frozen_visible_features(google_dir)
    codebook_payload = np.load(source_dir / "source_codebook.npz", allow_pickle=True)
    centers = np.asarray(codebook_payload["centers"], dtype=np.float64)
    source_feature_names = [str(value) for value in codebook_payload["feature_names"].tolist()]
    if list(feature_names) != source_feature_names:
        raise ValueError("Google feature schema must match source codebook feature schema for Stage 4 transfer")
    standardization = _load_source_standardization(codebook_payload, feature_count=int(x_raw.shape[1]))
    mean = np.asarray(standardization["mean"], dtype=np.float64)
    scale = np.asarray(standardization["scale"], dtype=np.float64)
    x = _apply_source_standardization(x_raw, mean=mean, scale=scale)
    assignments, recon_standardized = _assign_to_source_centers(x, centers)
    if transfer_mode == FROZEN_CODEBOOK_TRAIN_ADAPTER:
        recon_standardized = _affine_adapter(recon_standardized, x)
    else:
        recon_standardized = _calibrate_mean(recon_standardized, x)
    source_center_recon = _invert_source_standardization(recon_standardized, mean=mean, scale=scale)
    replay_head = _fit_assignment_replay_head(x_raw, assignments, code_count=int(centers.shape[0]))
    recon = np.asarray(replay_head["reconstruction"], dtype=np.float64)
    source_transfer = _replay_metrics(x_raw, recon, model_family=transfer_mode)
    source_center_transfer = _replay_metrics(x_raw, source_center_recon, model_family=f"{transfer_mode}_source_center_direct")
    train_on_google = _fit_attention_vq(
        x_raw,
        k=max(1, min(centers.shape[0], x_raw.shape[0])),
        max_iter=20,
        code_dim=min(centers.shape[1], x_raw.shape[1]),
    )["metrics"]
    random = _random_codebook_transfer(x_raw, x, centers, mean=mean, scale=scale, seed=int(seed))
    global_null = _global_null_transfer(x_raw)
    controls = {
        "schema": "scope_static_stage4_google_transfer_controls_v1",
        "train_on_google_only": train_on_google,
        "random_codebook_transfer": random,
        "global_mean_only": global_null,
        "mean_only": dict(global_null),
        "assignment_shuffle": _assignment_shuffle_transfer(x_raw, recon, seed=int(seed)),
        "feature_scramble": _feature_scramble_transfer(x_raw, recon, seed=int(seed)),
        "public_stratified_null": dict(global_null),
    }
    coordinate_system_audit = _coordinate_system_audit(
        x_raw=x_raw,
        x_source_standardized=x,
        centers=centers,
        assignments=assignments,
        standardization=standardization,
    )
    claim_boundary = _claim_boundary()
    acceptance = {
        "schema": "scope_static_stage4_google_transfer_acceptance_v1",
        "checks": {
            "claim_boundary_disallows_true_google_mechanism_recovery": not claim_boundary["claims_true_google_physical_mechanism_recovery"],
            "claim_boundary_disallows_google_m_label_recovery": not claim_boundary["claims_google_m_label_recovery"],
            "raw_target_beats_random_codebook": _strictly_better(source_transfer, random, "raw_target_only"),
            "block_normalized_beats_random_codebook": _strictly_better(source_transfer, random, "block_normalized"),
            "raw_target_beats_train_on_google_only": _strictly_better(source_transfer, train_on_google, "raw_target_only"),
            "block_normalized_beats_train_on_google_only": _strictly_better(source_transfer, train_on_google, "block_normalized"),
            "raw_target_beats_global_null": _strictly_better(source_transfer, global_null, "raw_target_only"),
            "block_normalized_beats_global_null": _strictly_better(source_transfer, global_null, "block_normalized"),
            "schema_matches_source_codebook": True,
        },
    }
    acceptance["passed"] = bool(all(dict(acceptance["checks"]).values()))
    result = {
        "schema": "scope_static_stage4_google_transfer_v1",
        "stage": STAGE_NAME,
        "source_pretrain_dir": str(source_dir),
        "google_stage3a_dir": str(google_dir),
        "output_dir": str(output),
        "config": {"seed": int(seed), "transfer_mode": str(transfer_mode)},
        "transfer_mode": str(transfer_mode),
        "visible_feature_matrix": feature_matrix,
        "claim_boundary": claim_boundary,
        "coordinate_system_audit": coordinate_system_audit,
        "google_transfer_metrics": {
            "schema": "scope_static_stage4_google_transfer_metrics_v1",
            "source_transfer": source_transfer,
            "source_center_direct": source_center_transfer,
            "controls": controls,
            "raw_target_only": source_transfer["raw_target_only"],
            "block_normalized": source_transfer["block_normalized"],
        },
        "assignment_summary": {
            "schema": "scope_static_stage4_google_transfer_assignment_summary_v1",
            "row_count": int(assignments.size),
            "source_code_count": int(centers.shape[0]),
            "active_source_code_count": int(len(set(assignments.tolist())) if assignments.size else 0),
        },
        "replay_head_audit": replay_head["audit"],
        "controls": controls,
        "acceptance_audit": acceptance,
        "decision": "stage4_google_transfer_passed" if acceptance["passed"] else "stage4_google_transfer_failed",
    }
    _write_transfer_outputs(output, result, assignments)
    return result


def run_stage4_transfer_diagnostics(
    *,
    source_pretrain_dir: str | Path,
    google_stage3a_dir: str | Path,
    output_dir: str | Path = DEFAULT_DIAGNOSTIC_OUTPUT_DIR,
    seed: int = 0,
) -> dict[str, object]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    strict = run_stage4_google_transfer(
        source_pretrain_dir=source_pretrain_dir,
        google_stage3a_dir=google_stage3a_dir,
        output_dir=output / STRICT_FROZEN_TRANSFER,
        seed=int(seed),
        transfer_mode=STRICT_FROZEN_TRANSFER,
    )
    adapter = run_stage4_google_transfer(
        source_pretrain_dir=source_pretrain_dir,
        google_stage3a_dir=google_stage3a_dir,
        output_dir=output / FROZEN_CODEBOOK_TRAIN_ADAPTER,
        seed=int(seed),
        transfer_mode=FROZEN_CODEBOOK_TRAIN_ADAPTER,
    )
    domain_shift_report = _domain_shift_report(strict, adapter)
    failure_taxonomy = _failure_taxonomy(strict, adapter, domain_shift_report)
    result = {
        "schema": "scope_static_stage4_transfer_diagnostics_v1",
        "stage": DIAGNOSTIC_STAGE_NAME,
        "source_pretrain_dir": str(source_pretrain_dir),
        "google_stage3a_dir": str(google_stage3a_dir),
        "output_dir": str(output),
        "strict_frozen_transfer": _summarize_transfer(strict),
        "frozen_codebook_train_adapter": _summarize_transfer(adapter),
        "domain_shift_report": domain_shift_report,
        "failure_taxonomy": failure_taxonomy,
        "transfer_diagnostics_decision": "stage4_transfer_diagnostics_completed",
        "diagnostic_interpretation": _diagnostic_interpretation(strict, adapter),
        "does_not_replace_main_claim": True,
        "decision": "stage4_transfer_diagnostics_completed",
    }
    (output / "metrics.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "transfer_diagnostics.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "domain_shift_report.json").write_text(json.dumps(domain_shift_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "failure_taxonomy.json").write_text(json.dumps(failure_taxonomy, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "config.yaml").write_text(yaml.safe_dump({"stage4_transfer_diagnostics_v1": {"seed": int(seed)}}, sort_keys=False), encoding="utf-8")
    return result


def _assign_to_source_centers(x: np.ndarray, centers: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if x.shape[1] != centers.shape[1]:
        raise ValueError("source centers and target visible matrix must have the same feature count")
    distances = ((x[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
    assignments = np.argmin(distances, axis=1).astype(np.int64) if distances.size else np.zeros(0, dtype=np.int64)
    return assignments, centers[assignments] if assignments.size else np.zeros_like(x)


def _strictly_better(left: Mapping[str, object], right: Mapping[str, object], key: str) -> bool:
    return float(left.get(key, 0.0) or 0.0) < float(right.get(key, 0.0) or 0.0) - 1.0e-12


def _load_source_standardization(payload: np.lib.npyio.NpzFile, *, feature_count: int) -> dict[str, object]:
    if "standardization_mean" in payload.files and "standardization_scale" in payload.files:
        mean = np.asarray(payload["standardization_mean"], dtype=np.float64)
        scale = np.asarray(payload["standardization_scale"], dtype=np.float64)
        loaded = True
    else:
        mean = np.zeros(int(feature_count), dtype=np.float64)
        scale = np.ones(int(feature_count), dtype=np.float64)
        loaded = False
    if mean.shape[0] != int(feature_count) or scale.shape[0] != int(feature_count):
        raise ValueError("source standardization shape must match Google feature count")
    scale = np.where(scale > 1.0e-12, scale, 1.0)
    return {
        "schema": "scope_static_stage4_frozen_source_standardization_v1",
        "coordinate_system": "source_standardized_visible_features",
        "loaded_from_source_codebook": loaded,
        "feature_count": int(feature_count),
        "mean": mean,
        "scale": scale,
    }


def _apply_source_standardization(x: np.ndarray, *, mean: np.ndarray, scale: np.ndarray) -> np.ndarray:
    return (np.asarray(x, dtype=np.float64) - mean[None, :]) / scale[None, :] if x.size else np.asarray(x, dtype=np.float64)


def _invert_source_standardization(x: np.ndarray, *, mean: np.ndarray, scale: np.ndarray) -> np.ndarray:
    return np.asarray(x, dtype=np.float64) * scale[None, :] + mean[None, :] if x.size else np.asarray(x, dtype=np.float64)


def _calibrate_mean(recon: np.ndarray, target: np.ndarray) -> np.ndarray:
    if recon.size == 0:
        return recon
    return recon + (np.mean(target, axis=0, keepdims=True) - np.mean(recon, axis=0, keepdims=True))


def _affine_adapter(recon: np.ndarray, target: np.ndarray) -> np.ndarray:
    if recon.size == 0:
        return recon
    r_mean = np.mean(recon, axis=0, keepdims=True)
    t_mean = np.mean(target, axis=0, keepdims=True)
    r_std = np.std(recon, axis=0, keepdims=True)
    t_std = np.std(target, axis=0, keepdims=True)
    scale = np.divide(t_std, r_std, out=np.ones_like(t_std), where=r_std > 1.0e-12)
    return (recon - r_mean) * scale + t_mean


def _random_codebook_transfer(
    x_raw: np.ndarray,
    x_source_standardized: np.ndarray,
    centers: np.ndarray,
    *,
    mean: np.ndarray,
    scale: np.ndarray,
    seed: int,
) -> dict[str, object]:
    rng = np.random.default_rng(int(seed))
    random_centers = rng.normal(loc=0.0, scale=1.0, size=centers.shape)
    assignments, recon_standardized = _assign_to_source_centers(x_source_standardized, random_centers)
    _direct_recon = _invert_source_standardization(recon_standardized, mean=mean, scale=scale)
    replay_head = _fit_assignment_replay_head(x_raw, assignments, code_count=int(centers.shape[0]))
    recon = np.asarray(replay_head["reconstruction"], dtype=np.float64)
    return _replay_metrics(x_raw, recon, model_family="random_codebook_transfer")


def _global_null_transfer(x: np.ndarray) -> dict[str, object]:
    mean = np.mean(x, axis=0, keepdims=True) if x.size else np.zeros((1, x.shape[1]), dtype=np.float64)
    return _replay_metrics(x, np.repeat(mean, int(x.shape[0]), axis=0), model_family="global_mean_only")


def _assignment_shuffle_transfer(x: np.ndarray, recon: np.ndarray, *, seed: int) -> dict[str, object]:
    rng = np.random.default_rng(int(seed))
    shuffled = np.asarray(recon, dtype=np.float64).copy()
    rng.shuffle(shuffled, axis=0)
    return _replay_metrics(x, shuffled, model_family="assignment_shuffle_transfer")


def _feature_scramble_transfer(x: np.ndarray, recon: np.ndarray, *, seed: int) -> dict[str, object]:
    rng = np.random.default_rng(int(seed))
    scrambled = np.asarray(recon, dtype=np.float64).copy()
    for col in range(scrambled.shape[1]):
        rng.shuffle(scrambled[:, col])
    return _replay_metrics(x, scrambled, model_family="feature_scramble_transfer")


def _fit_assignment_replay_head(target: np.ndarray, assignments: np.ndarray, *, code_count: int) -> dict[str, object]:
    x = np.asarray(target, dtype=np.float64)
    labels = np.asarray(assignments, dtype=np.int64)
    global_mean = np.mean(x, axis=0) if x.size else np.zeros(x.shape[1], dtype=np.float64)
    heads = np.zeros((int(code_count), x.shape[1]), dtype=np.float64)
    counts: dict[str, int] = {}
    for code in range(int(code_count)):
        mask = labels == code
        count = int(np.sum(mask))
        counts[f"C{code:03d}"] = count
        heads[code] = np.mean(x[mask], axis=0) if count else global_mean
    recon = heads[labels] if labels.size else np.zeros_like(x)
    active = sum(1 for count in counts.values() if count > 0)
    return {
        "reconstruction": recon,
        "audit": {
            "schema": "scope_static_stage4_assignment_replay_head_audit_v1",
            "head_type": "per_frozen_code_target_mean",
            "trains_encoder": False,
            "trains_codebook": False,
            "trains_standardization": False,
            "trains_low_capacity_replay_head": True,
            "code_count": int(code_count),
            "active_code_count": int(active),
            "assignment_counts": counts,
        },
    }


def _coordinate_system_audit(
    *,
    x_raw: np.ndarray,
    x_source_standardized: np.ndarray,
    centers: np.ndarray,
    assignments: np.ndarray,
    standardization: Mapping[str, object],
) -> dict[str, object]:
    counts = {int(idx): int(np.sum(assignments == idx)) for idx in range(int(centers.shape[0]))}
    active = sum(1 for value in counts.values() if value > 0)
    total = max(1, int(assignments.size))
    probs = np.asarray([count / total for count in counts.values()], dtype=np.float64)
    entropy = float(-np.sum([p * np.log(p) for p in probs if p > 0.0]))
    return {
        "schema": "scope_static_stage4_google_transfer_coordinate_system_audit_v1",
        "source_standardization_loaded": bool(standardization.get("loaded_from_source_codebook", False)),
        "assignment_coordinate_system": "source_standardized_visible_features",
        "replay_scoring_coordinate_system": "raw_google_visible_features",
        "google_raw_shape": [int(dim) for dim in x_raw.shape],
        "google_source_standardized_abs_mean": float(np.mean(np.abs(x_source_standardized))) if x_source_standardized.size else 0.0,
        "google_source_standardized_abs_p95": float(np.quantile(np.abs(x_source_standardized), 0.95)) if x_source_standardized.size else 0.0,
        "source_code_count": int(centers.shape[0]),
        "active_source_code_count": int(active),
        "assignment_entropy": entropy,
        "assignment_counts": {f"C{idx:03d}": count for idx, count in sorted(counts.items())},
    }


def _claim_boundary() -> dict[str, object]:
    return {
        "schema": "scope_static_stage4_google_transfer_claim_boundary_v1",
        "claims_true_google_physical_mechanism_recovery": False,
        "claims_google_m_label_recovery": False,
        "claims_visible_syndrome_response_replay": True,
        "claims_source_to_google_prototype_transfer": True,
        "google_ground_truth_mechanism_labels_available": False,
    }


def _write_transfer_outputs(output: Path, result: dict[str, object], assignments: np.ndarray) -> None:
    artifacts = {
        "metrics.json": result,
        "google_transfer_metrics.json": result["google_transfer_metrics"],
        "claim_boundary.json": result["claim_boundary"],
        "coordinate_system_audit.json": result["coordinate_system_audit"],
        "replay_head_audit.json": result["replay_head_audit"],
        "controls.json": result["controls"],
        "acceptance_audit.json": result["acceptance_audit"],
        "assignment_summary.json": result["assignment_summary"],
        "visible_feature_matrix.json": result["visible_feature_matrix"],
    }
    for name, payload in artifacts.items():
        (output / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    np.save(output / "google_source_code_assignments.npy", np.asarray(assignments, dtype=np.int64))
    (output / "config.yaml").write_text(yaml.safe_dump({"stage4_google_transfer_v1": result["config"]}, sort_keys=False), encoding="utf-8")
    (output / "summary.md").write_text(format_google_transfer_summary(result), encoding="utf-8")


def _summarize_transfer(result: Mapping[str, object]) -> dict[str, object]:
    metrics = dict(result.get("google_transfer_metrics", {}))
    source = dict(metrics.get("source_transfer", {}))
    return {
        "decision": result.get("decision"),
        "transfer_mode": result.get("transfer_mode"),
        "raw_target_only": source.get("raw_target_only"),
        "block_normalized": source.get("block_normalized"),
        "acceptance_passed": bool(dict(result.get("acceptance_audit", {})).get("passed", False)),
    }


def _diagnostic_interpretation(strict: Mapping[str, object], adapter: Mapping[str, object]) -> str:
    strict_pass = bool(dict(strict.get("acceptance_audit", {})).get("passed", False))
    adapter_pass = bool(dict(adapter.get("acceptance_audit", {})).get("passed", False))
    if strict_pass:
        return "strict_frozen_transfer_passed"
    if adapter_pass:
        return "strict_failed_but_frozen_codebook_adapter_passed_domain_shift_likely"
    return "both_transfer_modes_failed_surface_mismatch_or_nontransfer_likely"


def _domain_shift_report(strict: Mapping[str, object], adapter: Mapping[str, object]) -> dict[str, object]:
    strict_summary = _summarize_transfer(strict)
    adapter_summary = _summarize_transfer(adapter)
    strict_raw = float(strict_summary.get("raw_target_only", 0.0) or 0.0)
    adapter_raw = float(adapter_summary.get("raw_target_only", 0.0) or 0.0)
    strict_block = float(strict_summary.get("block_normalized", 0.0) or 0.0)
    adapter_block = float(adapter_summary.get("block_normalized", 0.0) or 0.0)
    return {
        "schema": "scope_static_stage4_domain_shift_report_v1",
        "strict_frozen_transfer": strict_summary,
        "frozen_codebook_train_adapter": adapter_summary,
        "adapter_minus_strict_raw_target_only": float(adapter_raw - strict_raw),
        "adapter_minus_strict_block_normalized": float(adapter_block - strict_block),
        "adapter_improves_raw_target_only": bool(adapter_raw < strict_raw),
        "adapter_improves_block_normalized": bool(adapter_block < strict_block),
        "lower_is_better": True,
    }


def _failure_taxonomy(strict: Mapping[str, object], adapter: Mapping[str, object], domain_shift_report: Mapping[str, object]) -> dict[str, object]:
    strict_pass = bool(dict(strict.get("acceptance_audit", {})).get("passed", False))
    adapter_pass = bool(dict(adapter.get("acceptance_audit", {})).get("passed", False))
    if strict_pass:
        label = "strict_frozen_transfer_pass"
    elif adapter_pass:
        label = "normalization_or_domain_shift"
    else:
        label = "source_google_surface_mismatch_or_source_prototype_non_transfer"
    return {
        "schema": "scope_static_stage4_transfer_failure_taxonomy_v1",
        "failure_mode": label,
        "strict_frozen_transfer_passed": strict_pass,
        "frozen_codebook_train_adapter_passed": adapter_pass,
        "domain_shift_signal": {
            "adapter_improves_raw_target_only": bool(domain_shift_report.get("adapter_improves_raw_target_only", False)),
            "adapter_improves_block_normalized": bool(domain_shift_report.get("adapter_improves_block_normalized", False)),
        },
        "does_not_replace_s4_2_main_claim": True,
    }


def format_google_transfer_summary(result: Mapping[str, object]) -> str:
    acceptance = dict(result.get("acceptance_audit", {}))
    return "\n".join(
        [
            "# S4.2 Google Transfer",
            "",
            f"- Decision: `{result.get('decision')}`",
            f"- Transfer mode: `{result.get('transfer_mode')}`",
            f"- Acceptance passed: `{str(bool(acceptance.get('passed', False))).lower()}`",
            "",
        ]
    )
