from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import json
import math
from pathlib import Path
import time
from typing import Callable, Iterable

import numpy as np
import stim

from scope_static.mechanism_discovery.baseline_registry import baseline_entry
from scope_static.numerics import NUMERICAL_ZERO

from .inventory import (
    DATASET_SURFACE_SET1,
    DEFAULT_DATASET_ROOTS,
    GoogleLeaf,
    decoder_pathways_for_leaf,
    iter_google_leaves,
    load_google_circuit,
    load_google_observations,
)


BASELINE_KEYS = (
    "dem_physics_prior_matching_si1000",
    "rl_optimized_prior_matching",
    "harmony_si1000",
    "harmony_rl_optimized",
    "independent_detector",
    "pairwise_ising",
    "factor_graph_crf",
    "graphical_lasso",
    "bayesian_hierarchical",
    "bernoulli_mixture_em",
    "sparse_coding_dictionary",
    "causal_discovery_structure",
    "vae",
    "gan",
    "ebm_rbm_crbm",
    "autoregressive_generative",
)
SCOPE_COMPARABLE_KEY = "scope_teacher_learner_latent_replay"
ALLOWED_BASELINE_KEYS = BASELINE_KEYS + (SCOPE_COMPARABLE_KEY,)

EXTERNAL_ADAPTER_REQUIRED_BASELINES = (
    "independent_detector",
    "pairwise_ising",
    "factor_graph_crf",
    "graphical_lasso",
    "bayesian_hierarchical",
    "bernoulli_mixture_em",
    "sparse_coding_dictionary",
    "causal_discovery_structure",
    "vae",
    "gan",
    "ebm_rbm_crbm",
    "autoregressive_generative",
)

DECODER_BASELINES = {
    "dem_physics_prior_matching_si1000": "correlated_matching_decoder_with_si1000_prior",
    "rl_optimized_prior_matching": "correlated_matching_decoder_with_rl_optimized_prior",
    "harmony_si1000": "harmony_decoder_with_si1000_prior",
    "harmony_rl_optimized": "harmony_decoder_with_rl_optimized_prior",
}

NUMERICAL_FLOOR = NUMERICAL_ZERO


@dataclass(frozen=True)
class BaselineSuiteConfig:
    dataset_root: Path = DEFAULT_DATASET_ROOTS[DATASET_SURFACE_SET1]
    dataset_name: str = DATASET_SURFACE_SET1
    output_dir: Path = Path("outputs/google_static/d3d5_baseline_suite")
    distances: tuple[int, ...] = (3, 5)
    bases: tuple[str, ...] = ("X", "Z")
    rounds: tuple[int, ...] = (1, 10)
    max_leaves_per_distance_basis: int = 2
    max_shots_per_leaf: int = 2048
    detector_limit: int = 32
    train_fraction: float = 0.7
    seed: int = 0
    seeds: tuple[int, ...] = (0,)
    validation_fraction: float = 0.2
    selection_profile: str = "single"
    mixture_components: int = 4
    max_iter: int = 20
    torch_epochs: int = 12
    torch_batch_size: int = 256
    gan_epochs: int | None = None
    rbm_steps: int | None = None
    autoregressive_steps: int | None = None
    baseline_keys: tuple[str, ...] = BASELINE_KEYS


def run_google_d3d5_baseline_suite(config: BaselineSuiteConfig | None = None) -> dict[str, object]:
    cfg = config or BaselineSuiteConfig()
    start = time.perf_counter()
    leaves = _select_leaves(cfg)
    if not leaves:
        raise ValueError("No Google D3/D5 leaves selected for baseline suite")
    leaf_results = []
    for repeat_index, repeat_seed in enumerate(cfg.seeds or (cfg.seed,)):
        rng = np.random.default_rng(int(repeat_seed))
        for leaf_idx, leaf in enumerate(leaves):
            leaf_seed = int(rng.integers(0, 2**31 - 1))
            leaf_results.append(
                _run_leaf_baselines(
                    leaf,
                    cfg=cfg,
                    seed=leaf_seed,
                    leaf_index=leaf_idx,
                    repeat_seed=int(repeat_seed),
                    repeat_index=int(repeat_index),
                )
            )
    baseline_keys = tuple(key for key in cfg.baseline_keys if key in ALLOWED_BASELINE_KEYS)
    aggregate = _aggregate_leaf_results(leaf_results, baseline_keys=baseline_keys)
    result = {
        "schema": "scope_static_google_d3d5_all_baseline_suite_v1",
        "decision": "google_d3d5_all_baselines_completed",
        "claim_boundary": {
            "uses_scope_layer123_or_v2_adapter": False,
            "uses_google_v2_stage3_artifacts": False,
            "uses_scope_teacher_learner_comparable_adapter": SCOPE_COMPARABLE_KEY in set(baseline_keys),
            "scope_teacher_learner_adapter_scope": (
                "shot_level_google_d3d5_scorecard_adapter_not_decoder_not_stage3_v2_artifact"
                if SCOPE_COMPARABLE_KEY in set(baseline_keys)
                else "not_run"
            ),
            "scope_teacher_learner_logical_p_l_status": (
                "not_reported_not_a_decoder"
                if SCOPE_COMPARABLE_KEY in set(baseline_keys)
                else "not_run"
            ),
            "uses_raw_google_detection_events": True,
            "uses_raw_google_observable_flips": True,
            "uses_google_decoder_pathway_predictions_for_decoder_baselines": True,
            "statistical_and_deep_baseline_policy": "official_or_cloned_upstream_only_no_native_proxy",
            "google_has_true_mechanism_location_strength_labels": False,
            "dem_f1_and_strength_spearman_status": "not_applicable_google_no_ground_truth",
            "cross_decoding_status": "not_run_no_downstream_decoder_retraining_in_this_one_round_suite",
        },
        "config": _config_dict(cfg),
        "dataset": {
            "dataset_name": cfg.dataset_name,
            "dataset_root": str(cfg.dataset_root),
            "selected_leaf_count": int(len(leaves)),
            "selected_context_ids": [leaf.context_id for leaf in leaves],
            "distance_counts": dict(Counter(int(leaf.distance or -1) for leaf in leaves)),
            "basis_counts": dict(Counter(str(leaf.basis) for leaf in leaves)),
            "round_counts": dict(Counter(int(leaf.rounds or -1) for leaf in leaves)),
            "repeat_seeds": [int(seed) for seed in (cfg.seeds or (cfg.seed,))],
            "leaf_result_count": int(len(leaf_results)),
        },
        "metric_definitions": _metric_definitions(),
        "baseline_keys": list(baseline_keys),
        "baseline_candidate_policy": _baseline_candidate_policy(cfg),
        "aggregate": aggregate,
        "leaf_results": leaf_results,
        "wall_clock_seconds": float(time.perf_counter() - start),
    }
    _write_outputs(result, cfg.output_dir)
    return result


def _run_leaf_baselines(
    leaf: GoogleLeaf,
    *,
    cfg: BaselineSuiteConfig,
    seed: int,
    leaf_index: int,
    repeat_seed: int,
    repeat_index: int,
) -> dict[str, object]:
    observations = load_google_observations(leaf, max_shots=int(cfg.max_shots_per_leaf)).astype(np.uint8)
    if observations.ndim != 2 or observations.shape[1] < 2:
        raise ValueError(f"Bad observation matrix for {leaf.context_id}: {observations.shape}")
    circuit = load_google_circuit(leaf)
    detector_count = int(circuit.num_detectors)
    observable_count = int(circuit.num_observables)
    detectors_full = observations[:, :detector_count].astype(np.float64)
    observable = observations[:, detector_count : detector_count + observable_count]
    y = observable[:, 0].astype(np.float64) if observable.size else np.zeros(observations.shape[0], dtype=np.float64)
    train_idx, test_idx = _train_test_indices(observations.shape[0], train_fraction=float(cfg.train_fraction), seed=seed)
    selected = _select_detector_columns(detectors_full[train_idx], limit=int(cfg.detector_limit))
    x_train = detectors_full[train_idx][:, selected]
    x_test = detectors_full[test_idx][:, selected]
    y_train = y[train_idx]
    y_test = y[test_idx]
    context = _leaf_context(leaf, leaf_index=leaf_index)
    reference = _timed_decoder_baseline_metrics(
        leaf,
        pathway=DECODER_BASELINES["dem_physics_prior_matching_si1000"],
        y=y,
        test_idx=test_idx,
        actual_curve_rate=float(np.mean(y_test)) if y_test.size else 0.0,
    )
    reference_p_l = _optional_float(reference.get("logical_p_L"))
    baselines: dict[str, dict[str, object]] = {
        "dem_physics_prior_matching_si1000": reference,
        "rl_optimized_prior_matching": _timed_decoder_baseline_metrics(
            leaf,
            pathway=DECODER_BASELINES["rl_optimized_prior_matching"],
            y=y,
            test_idx=test_idx,
            actual_curve_rate=float(np.mean(y_test)) if y_test.size else 0.0,
        ),
        "harmony_si1000": _timed_decoder_baseline_metrics(
            leaf,
            pathway=DECODER_BASELINES["harmony_si1000"],
            y=y,
            test_idx=test_idx,
            actual_curve_rate=float(np.mean(y_test)) if y_test.size else 0.0,
        ),
        "harmony_rl_optimized": _timed_decoder_baseline_metrics(
            leaf,
            pathway=DECODER_BASELINES["harmony_rl_optimized"],
            y=y,
            test_idx=test_idx,
            actual_curve_rate=float(np.mean(y_test)) if y_test.size else 0.0,
        ),
    }
    for key in tuple(DECODER_BASELINES):
        baselines[key] = _finalize_metric_record(baselines[key], reference_p_l=reference_p_l)

    requested_baselines = set(cfg.baseline_keys or BASELINE_KEYS)
    for key in EXTERNAL_ADAPTER_REQUIRED_BASELINES:
        if key in requested_baselines:
            baselines[key] = _external_adapter_missing_record(key)

    baseline_fns: dict[str, Callable[..., dict[str, object]]] = {
        SCOPE_COMPARABLE_KEY: _run_scope_teacher_learner_latent_replay,
    }
    for offset, (key, fn) in enumerate((item for item in baseline_fns.items() if item[0] in requested_baselines), start=1):
        baseline_start = time.perf_counter()
        try:
            metrics = _run_selected_baseline(
                key,
                fn,
                x_train=x_train,
                y_train=y_train,
                x_test=x_test,
                y_test=y_test,
                context=context,
                cfg=cfg,
                seed=int(seed + 1009 * offset),
            )
        except Exception as exc:  # Keep all baseline interfaces reporting in one round.
            metrics = _empty_metric_record(
                key,
                implementation_status="failed",
                notes=[f"{type(exc).__name__}: {exc}"],
            )
        metrics["wall_clock_seconds"] = _json_float(float(time.perf_counter() - baseline_start))
        baselines[key] = _finalize_metric_record(metrics, reference_p_l=reference_p_l)
    return {
        "schema": "scope_static_google_d3d5_baseline_leaf_result_v1",
        "context_id": leaf.context_id,
        "repeat_seed": int(repeat_seed),
        "repeat_index": int(repeat_index),
        "sample_id": leaf.sample_id,
        "patch_id": leaf.patch_id,
        "distance": int(leaf.distance or -1),
        "basis": str(leaf.basis),
        "rounds": int(leaf.rounds or -1),
        "shots_loaded": int(observations.shape[0]),
        "train_shots": int(len(train_idx)),
        "test_shots": int(len(test_idx)),
        "detector_count_full": int(detector_count),
        "detector_count_selected": int(len(selected)),
        "selected_detector_indices": [int(idx) for idx in selected],
        "actual_logical_rate_test": float(np.mean(y_test)) if y_test.size else None,
        "decoder_pathways_available": [pathway.pathway_name for pathway in decoder_pathways_for_leaf(leaf)],
        "baselines": baselines,
    }


def _decoder_baseline_metrics(
    leaf: GoogleLeaf,
    *,
    pathway: str,
    y: np.ndarray,
    test_idx: np.ndarray,
    actual_curve_rate: float,
) -> dict[str, object]:
    path = leaf.decoder_predictions(pathway)
    key = _decoder_key(pathway)
    if not path.is_file():
        return _empty_metric_record(
            key,
            implementation_status="missing_dataset_pathway",
            notes=[f"missing decoder predictions: {path}"],
        )
    circuit = load_google_circuit(leaf)
    pred = stim.read_shot_data_file(path=str(path), format="b8", num_measurements=int(circuit.num_observables)).astype(np.uint8)
    pred = pred[: y.shape[0], 0].astype(np.float64)
    pred_test = pred[test_idx]
    y_test = y[test_idx]
    p_l = float(np.mean(np.not_equal(pred_test, y_test))) if y_test.size else None
    return {
        **_empty_metric_record(key, implementation_status="dataset_pathway"),
        "baseline_family": key,
        "google_decoder_pathway": str(pathway),
        "logical_p_L": p_l,
        "logical_prediction_source": "google_decoder_obs_flips_predicted_b8",
        "decay_curve_point": {
            "rounds": int(leaf.rounds or -1),
            "baseline_logical_p_L": p_l,
            "actual_no_correction_logical_rate": float(actual_curve_rate),
        },
        "metric_notes": ["QEC decoder baseline reports logical metrics only; it does not generate detector syndromes here."],
    }


def _timed_decoder_baseline_metrics(
    leaf: GoogleLeaf,
    *,
    pathway: str,
    y: np.ndarray,
    test_idx: np.ndarray,
    actual_curve_rate: float,
) -> dict[str, object]:
    start = time.perf_counter()
    record = _decoder_baseline_metrics(
        leaf,
        pathway=pathway,
        y=y,
        test_idx=test_idx,
        actual_curve_rate=actual_curve_rate,
    )
    record["wall_clock_seconds"] = _json_float(float(time.perf_counter() - start))
    return record


def _run_selected_baseline(
    key: str,
    fn: Callable[..., dict[str, object]],
    *,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
    context: dict[str, object],
    cfg: BaselineSuiteConfig,
    seed: int,
) -> dict[str, object]:
    candidates = _baseline_candidates(key, cfg)
    if str(cfg.selection_profile) != "recommended_grid" or len(candidates) == 1:
        params = dict(candidates[0]["params"]) if candidates else {}
        metrics = fn(
            x_train=x_train,
            y_train=y_train,
            x_test=x_test,
            y_test=y_test,
            context=context,
            cfg=cfg,
            seed=seed,
            baseline_params=params,
        )
        metrics["selection_summary"] = {
            "selection_profile": str(cfg.selection_profile),
            "candidate_count": int(len(candidates)),
            "selected_params": params,
            "candidate_source": candidates[0].get("source") if candidates else "single_config",
            "selection_status": "single_candidate",
        }
        return metrics

    fit_idx, val_idx = _train_test_indices(
        x_train.shape[0],
        train_fraction=max(0.05, min(0.95, 1.0 - float(cfg.validation_fraction))),
        seed=seed + 7919,
    )
    x_fit = x_train[fit_idx]
    y_fit = y_train[fit_idx]
    x_val = x_train[val_idx]
    y_val = y_train[val_idx]
    scored: list[dict[str, object]] = []
    best_score = math.inf
    best_candidate = candidates[0]
    for idx, candidate in enumerate(candidates):
        params = dict(candidate["params"])
        candidate_seed = int(seed + 104729 * (idx + 1))
        val_metrics = fn(
            x_train=x_fit,
            y_train=y_fit,
            x_test=x_val,
            y_test=y_val,
            context=context,
            cfg=cfg,
            seed=candidate_seed,
            baseline_params=params,
        )
        score = _selection_score(val_metrics)
        scored.append(
            {
                "candidate_index": int(idx),
                "params": params,
                "selection_score": _json_float(score),
                "validation_metrics": _selection_metric_digest(val_metrics),
                "source": candidate.get("source"),
            }
        )
        if score < best_score:
            best_score = score
            best_candidate = candidate

    selected_params = dict(best_candidate["params"])
    metrics = fn(
        x_train=x_train,
        y_train=y_train,
        x_test=x_test,
        y_test=y_test,
        context=context,
        cfg=cfg,
        seed=seed,
        baseline_params=selected_params,
    )
    metrics["selection_summary"] = {
        "selection_profile": str(cfg.selection_profile),
        "candidate_count": int(len(candidates)),
        "selected_params": selected_params,
        "candidate_source": best_candidate.get("source"),
        "selection_metric": "validation_syndrome_score",
        "selected_validation_score": _json_float(best_score),
        "candidate_scores": scored,
    }
    return metrics


def _external_adapter_missing_record(key: str) -> dict[str, object]:
    try:
        entry = baseline_entry(_registry_key_for_suite_key(key))
    except KeyError:
        entry = None
    repos = [] if entry is None else [repo.to_dict() for repo in entry.external_repositories]
    notes = [
        "Not run: this suite now forbids SCOPE-native proxy implementations for external baselines.",
        "Clone is audited separately; a baseline becomes runnable only after a native upstream entrypoint runs on the target data without local model helpers.",
    ]
    if entry is not None:
        notes.append(f"Registry implementation_status={entry.implementation_status}.")
    return {
        **_empty_metric_record(key, implementation_status="not_run_external_adapter_missing"),
        "baseline_family": key,
        "runner_policy": "official_or_cloned_upstream_only_no_native_proxy",
        "external_repositories": repos,
        "metric_notes": notes,
    }


def _registry_key_for_suite_key(key: str) -> str:
    if key in {
        "dem_physics_prior_matching_si1000",
        "rl_optimized_prior_matching",
        "harmony_si1000",
        "harmony_rl_optimized",
    }:
        mapping = {
            "dem_physics_prior_matching_si1000": "dem_physics_prior",
            "rl_optimized_prior_matching": "rl_optimized_prior",
            "harmony_si1000": "harmony_decoder_ensemble",
            "harmony_rl_optimized": "harmony_decoder_ensemble",
        }
        return mapping[key]
    return key


def _run_scope_teacher_learner_latent_replay(**kwargs: object) -> dict[str, object]:
    x_train, y_train, x_test, y_test = _arrays(kwargs)
    cfg = kwargs["cfg"]
    assert isinstance(cfg, BaselineSuiteConfig)
    seed = int(kwargs["seed"])
    params = _baseline_params(kwargs)
    prototype_count = int(params.get("prototype_count", cfg.mixture_components))
    steps = int(params.get("max_iter", cfg.max_iter))
    train_detector = np.asarray(x_train, dtype=np.float64)
    if train_detector.size == 0:
        px = np.zeros(x_test.shape[1], dtype=np.float64)
        return _model_metric_record(
            "scope_teacher_learner_latent_replay",
            x_test=x_test,
            y_test=y_test,
            generated=np.zeros_like(x_test),
            detector_prob=np.repeat(_clip(px)[None, :], x_test.shape[0], axis=0),
            logical_prob=np.full(y_test.shape, _clip_scalar(float(np.mean(y_train)) if y_train.size else 0.0), dtype=np.float64),
            syndrome_nll_per_shot=_independent_nll(x_test, px),
            implementation_status="native_scope_teacher_learner_adapter",
            notes=["Empty-train fallback; no oracle mechanism labels used."],
        )

    weights, theta = _fit_bernoulli_mixture(
        train_detector,
        k=max(1, prototype_count),
        steps=max(1, steps),
        seed=seed,
    )
    test_log_resp = _mixture_log_responsibilities(x_test, weights, theta)
    test_resp = np.exp(test_log_resp)
    detector_prob = _clip(test_resp @ theta)
    nll = _mixture_nll(x_test, weights, theta)
    generated = _sample_bernoulli_mixture(weights, theta, x_test.shape[0], seed=seed + 1)
    return _model_metric_record(
        "scope_teacher_learner_latent_replay",
        x_test=x_test,
        y_test=y_test,
        generated=generated,
        detector_prob=detector_prob,
        logical_prob=None,
        syndrome_nll_per_shot=nll,
        implementation_status="native_scope_teacher_learner_adapter",
        structural_summary={
            "teacher_surface": "train-fold selected-detector syndromes",
            "learner": "no-oracle Bernoulli latent prototype mixture",
            "prototype_count": int(theta.shape[0]),
            "em_steps": int(steps),
            "assignment_unit": "heldout_shot_responsibility_over_train_visible_prototypes",
            "uses_google_true_mechanism_labels": False,
            "uses_oracle_location_or_strength": False,
            "uses_observable_flips_for_detector_prototypes": False,
            "uses_observable_flips_for_logical_proxy": False,
            "logical_p_l_status": "not_reported_not_a_decoder",
        },
        notes=[
            "SCOPE teacher-learner comparable adapter: learns latent visible prototypes from train detector syndromes only.",
            "Logical p_L is intentionally not reported here: this adapter does not emit decoder obs_flips_predicted.b8 or run cross-decoding.",
        ],
    )


def _component_observable_rates(responsibilities: np.ndarray, y: np.ndarray) -> np.ndarray:
    resp = np.asarray(responsibilities, dtype=np.float64)
    y_arr = np.asarray(y, dtype=np.float64)
    if resp.ndim != 2 or resp.shape[0] == 0:
        return np.zeros(resp.shape[1] if resp.ndim == 2 else 1, dtype=np.float64)
    mass = np.maximum(np.sum(resp, axis=0), NUMERICAL_FLOOR)
    global_rate = float(np.mean(y_arr)) if y_arr.size else 0.0
    rates = (resp.T @ y_arr) / mass
    empty = mass <= NUMERICAL_FLOOR * 10.0
    rates[empty] = global_rate
    return _clip(rates)


def _model_metric_record(
    key: str,
    *,
    x_test: np.ndarray,
    y_test: np.ndarray,
    generated: np.ndarray | None = None,
    detector_prob: np.ndarray | None = None,
    logical_prob: np.ndarray | None = None,
    syndrome_nll_per_shot: float | None = None,
    masked_pseudo_likelihood_nll_per_shot: float | None = None,
    gaussian_density_nll_per_shot: float | None = None,
    two_sample_auc: float | None = None,
    implementation_status: str,
    structural_summary: dict[str, object] | None = None,
    uncertainty_summary: dict[str, object] | None = None,
    notes: list[str] | None = None,
) -> dict[str, object]:
    generated = np.zeros_like(x_test) if generated is None else np.asarray(generated, dtype=np.float64)
    moment = _moment_metrics(x_test, generated)
    record = _empty_metric_record(key, implementation_status=implementation_status, notes=notes or [])
    record.update(moment)
    if detector_prob is not None:
        detector_prob = _clip(np.asarray(detector_prob, dtype=np.float64))
        record["syndrome_nll_per_shot"] = _json_float(
            syndrome_nll_per_shot if syndrome_nll_per_shot is not None else float(np.mean(np.sum(_binary_ce(x_test, detector_prob), axis=1)))
        )
        record["syndrome_nll_per_bit"] = _json_float(float(record["syndrome_nll_per_shot"]) / max(float(x_test.shape[1]), 1.0))
    elif syndrome_nll_per_shot is not None:
        record["syndrome_nll_per_shot"] = _json_float(syndrome_nll_per_shot)
        record["syndrome_nll_per_bit"] = _json_float(float(syndrome_nll_per_shot) / max(float(x_test.shape[1]), 1.0))
    if masked_pseudo_likelihood_nll_per_shot is not None:
        record["masked_pseudo_likelihood_nll_per_shot"] = _json_float(masked_pseudo_likelihood_nll_per_shot)
    if gaussian_density_nll_per_shot is not None:
        record["gaussian_density_nll_per_shot"] = _json_float(gaussian_density_nll_per_shot)
    if logical_prob is not None and y_test.size:
        logical_prob = _clip(np.asarray(logical_prob, dtype=np.float64))
        pred = (logical_prob >= 0.5).astype(np.float64)
        record["logical_p_L"] = _json_float(float(np.mean(np.not_equal(pred, y_test))))
        record["logical_prediction_source"] = "baseline_conditional_logical_probability_proxy"
        record["logical_brier"] = _json_float(float(np.mean((logical_prob - y_test) ** 2)))
    if two_sample_auc is not None:
        record["two_sample_auc"] = _json_float(two_sample_auc)
    else:
        record["two_sample_auc"] = _json_float(_two_sample_linear_auc(x_test, generated)) if generated.size else None
    if structural_summary:
        record["structural_summary"] = structural_summary
    if uncertainty_summary:
        record["uncertainty_summary"] = uncertainty_summary
    return record


def _empty_metric_record(key: str, *, implementation_status: str, notes: list[str] | None = None) -> dict[str, object]:
    return {
        "baseline_key": key,
        "implementation_status": implementation_status,
        "logical_p_L": None,
        "logical_delta_p_L_vs_matching_si1000": None,
        "decay_curve_distance_log_rms_vs_no_correction_curve": None,
        "cross_decoding_delta_p_L_vs_matching_si1000": None,
        "cross_decoding_status": "not_run_no_downstream_decoder_retraining_in_this_one_round_suite",
        "syndrome_first_moment_mae": None,
        "syndrome_second_moment_relative_fro": None,
        "syndrome_nll_per_shot": None,
        "syndrome_nll_per_bit": None,
        "masked_pseudo_likelihood_nll_per_shot": None,
        "gaussian_density_nll_per_shot": None,
        "two_sample_auc": None,
        "dem_f1": None,
        "dem_f1_status": "not_applicable_google_no_ground_truth_mechanism_labels",
        "strength_spearman": None,
        "strength_spearman_status": "not_applicable_google_no_ground_truth_strength_labels",
        "wall_clock_seconds": None,
        "metric_notes": notes or [],
    }


def _finalize_metric_record(record: dict[str, object], *, reference_p_l: float | None) -> dict[str, object]:
    p_l = _optional_float(record.get("logical_p_L"))
    if p_l is not None and reference_p_l is not None:
        record["logical_delta_p_L_vs_matching_si1000"] = _json_float(p_l - reference_p_l)
    return record


def _aggregate_leaf_results(leaf_results: list[dict[str, object]], *, baseline_keys: tuple[str, ...] = BASELINE_KEYS) -> dict[str, object]:
    out: dict[str, object] = {}
    for key in baseline_keys:
        rows = [dict(dict(row["baselines"])[key]) for row in leaf_results if key in dict(row["baselines"])]
        metrics: dict[str, object] = {}
        for metric in (
            "logical_p_L",
            "logical_delta_p_L_vs_matching_si1000",
            "syndrome_first_moment_mae",
            "syndrome_second_moment_relative_fro",
            "syndrome_nll_per_shot",
            "syndrome_nll_per_bit",
            "masked_pseudo_likelihood_nll_per_shot",
            "gaussian_density_nll_per_shot",
            "two_sample_auc",
            "logical_brier",
            "wall_clock_seconds",
        ):
            values = [_optional_float(row.get(metric)) for row in rows]
            values = [value for value in values if value is not None]
            metrics[metric] = _summary_stats(values)
        curve = _decay_curve_distance(leaf_results, key)
        metrics["decay_curve_distance_log_rms_vs_no_correction_curve"] = curve
        metrics["cross_decoding_delta_p_L_vs_matching_si1000"] = {
            "value": None,
            "status": "not_run_no_downstream_decoder_retraining_in_this_one_round_suite",
        }
        metrics["dem_f1"] = {"value": None, "status": "not_applicable_google_no_ground_truth_mechanism_labels"}
        metrics["strength_spearman"] = {"value": None, "status": "not_applicable_google_no_ground_truth_strength_labels"}
        out[key] = {
            "baseline_key": key,
            "leaf_count": int(len(rows)),
            "implementation_status_counts": dict(Counter(str(row.get("implementation_status")) for row in rows)),
            "metrics": metrics,
            "notes": sorted({note for row in rows for note in row.get("metric_notes", []) if isinstance(note, str)}),
        }
    return out


def _decay_curve_distance(leaf_results: list[dict[str, object]], key: str) -> dict[str, object]:
    by_round: dict[int, list[tuple[float, float]]] = defaultdict(list)
    for leaf in leaf_results:
        baseline = dict(dict(leaf.get("baselines", {})).get(key, {}))
        p_l = _optional_float(baseline.get("logical_p_L"))
        actual = _optional_float(leaf.get("actual_logical_rate_test"))
        rounds = int(leaf.get("rounds", -1))
        if p_l is not None and actual is not None:
            by_round[rounds].append((p_l, actual))
    if not by_round:
        return {"value": None, "status": "not_available_no_logical_curve"}
    deltas = []
    for pairs in by_round.values():
        pred = float(np.mean([p for p, _ in pairs]))
        actual = float(np.mean([a for _, a in pairs]))
        deltas.append((math.log(max(pred, NUMERICAL_FLOOR)) - math.log(max(actual, NUMERICAL_FLOOR))) ** 2)
    return {
        "value": _json_float(math.sqrt(float(np.mean(deltas)))) if deltas else None,
        "round_count": int(len(by_round)),
        "status": "reported_against_no_correction_actual_observable_flip_curve",
    }


def _baseline_candidate_policy(cfg: BaselineSuiteConfig) -> dict[str, object]:
    out = {}
    for key in (cfg.baseline_keys or BASELINE_KEYS):
        if key in EXTERNAL_ADAPTER_REQUIRED_BASELINES:
            out[key] = {
                "candidate_count": 0,
                "source": ["external_cloned_upstream_adapter_required"],
                "compute_budget": {
                    "selection_profile": str(cfg.selection_profile),
                    "repeat_seed_count": int(len(cfg.seeds or (cfg.seed,))),
                    "max_shots_per_leaf": int(cfg.max_shots_per_leaf),
                    "detector_limit": int(cfg.detector_limit),
                    "status": "not_applicable_until_native_upstream_entrypoint_runs",
                },
                "candidates": [],
                "run_policy": "not_run_until_native_upstream_entrypoint_runs",
                "external_repositories": _external_adapter_missing_record(key).get("external_repositories", []),
            }
            continue
        candidates = _baseline_candidates(key, cfg)
        out[key] = {
            "candidate_count": int(len(candidates)),
            "source": sorted({str(item.get("source")) for item in candidates}),
            "compute_budget": _candidate_budget_summary(key, cfg),
            "candidates": [dict(item["params"]) for item in candidates],
            "run_policy": "google_dataset_pathway_or_internal_scope_comparable_adapter",
        }
    return out


def _baseline_candidates(key: str, cfg: BaselineSuiteConfig) -> list[dict[str, object]]:
    def row(params: dict[str, object], source: str) -> dict[str, object]:
        return {"params": params, "source": source}

    if key in EXTERNAL_ADAPTER_REQUIRED_BASELINES:
        return []
    if key in DECODER_BASELINES:
        return [row({}, "google_dataset_decoder_pathway")]
    if key == "scope_teacher_learner_latent_replay":
        if str(cfg.selection_profile) in {"recommended_or_matched_budget", "matched_budget", "recommended_single"}:
            return [
                row(
                    {"prototype_count": int(cfg.mixture_components), "max_iter": max(50, int(cfg.max_iter))},
                    "scope_stage3b1_selected_k_matched_no_oracle_adapter",
                )
            ]
        if str(cfg.selection_profile) != "recommended_grid":
            return [
                row(
                    {"prototype_count": int(cfg.mixture_components), "max_iter": max(50, int(cfg.max_iter))},
                    "scope_stage3b1_selected_k_matched_no_oracle_adapter",
                )
            ]
        return [
            row(
                {"prototype_count": k, "max_iter": max(25, int(cfg.max_iter))},
                "scope_stage3b1_visible_latent_replay_grid",
            )
            for k in (4, 8, 16)
        ]
    return [row({}, "single_config")]


def _candidate_budget_summary(key: str, cfg: BaselineSuiteConfig) -> dict[str, object]:
    candidates = _baseline_candidates(key, cfg)
    params = [dict(item["params"]) for item in candidates]
    return {
        "selection_profile": str(cfg.selection_profile),
        "candidate_count": int(len(candidates)),
        "repeat_seed_count": int(len(cfg.seeds or (cfg.seed,))),
        "max_shots_per_leaf": int(cfg.max_shots_per_leaf),
        "detector_limit": int(cfg.detector_limit),
        "torch_batch_size": int(cfg.torch_batch_size),
        "epoch_values": sorted({int(p["epochs"]) for p in params if "epochs" in p}),
        "step_values": sorted({int(p["steps"]) for p in params if "steps" in p}),
    }


def _selection_score(metrics: dict[str, object]) -> float:
    for key in (
        "syndrome_nll_per_bit",
        "masked_pseudo_likelihood_nll_per_shot",
        "gaussian_density_nll_per_shot",
        "syndrome_nll_per_shot",
    ):
        value = _optional_float(metrics.get(key))
        if value is not None:
            return value
    auc = _optional_float(metrics.get("two_sample_auc"))
    first = _optional_float(metrics.get("syndrome_first_moment_mae"))
    second = _optional_float(metrics.get("syndrome_second_moment_relative_fro"))
    score = 0.0
    if first is not None:
        score += first
    if second is not None:
        score += second
    if auc is not None:
        score += abs(auc - 0.5)
    return score if score > 0.0 else math.inf


def _selection_metric_digest(metrics: dict[str, object]) -> dict[str, object]:
    keys = (
        "syndrome_nll_per_bit",
        "syndrome_nll_per_shot",
        "masked_pseudo_likelihood_nll_per_shot",
        "gaussian_density_nll_per_shot",
        "syndrome_first_moment_mae",
        "syndrome_second_moment_relative_fro",
        "two_sample_auc",
        "logical_p_L",
    )
    return {key: metrics.get(key) for key in keys if metrics.get(key) is not None}


def _select_leaves(cfg: BaselineSuiteConfig) -> list[GoogleLeaf]:
    leaves = iter_google_leaves(cfg.dataset_root, cfg.dataset_name)
    leaves = [
        leaf
        for leaf in leaves
        if int(leaf.distance or -1) in set(cfg.distances)
        and str(leaf.basis) in set(cfg.bases)
        and int(leaf.rounds or -1) in set(cfg.rounds)
    ]
    selected: list[GoogleLeaf] = []
    counts: Counter[tuple[int, str, int]] = Counter()
    per_round_limit = max(1, int(math.ceil(int(cfg.max_leaves_per_distance_basis) / max(len(set(cfg.rounds)), 1))))
    for leaf in sorted(leaves, key=lambda row: (int(row.distance or -1), str(row.basis), int(row.rounds or -1), str(row.sample_id))):
        key = (int(leaf.distance or -1), str(leaf.basis), int(leaf.rounds or -1))
        if counts[key] < per_round_limit:
            selected.append(leaf)
            counts[key] += 1
    return selected


def _train_test_indices(n: int, *, train_fraction: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    order = np.arange(n, dtype=np.int64)
    rng.shuffle(order)
    split = max(1, min(n - 1, int(round(float(train_fraction) * n)))) if n > 1 else n
    return np.sort(order[:split]), np.sort(order[split:])


def _select_detector_columns(x_train: np.ndarray, *, limit: int) -> np.ndarray:
    d = int(x_train.shape[1])
    if d <= int(limit):
        return np.arange(d, dtype=np.int64)
    variances = np.var(x_train, axis=0)
    return np.sort(np.argsort(-variances)[: int(limit)]).astype(np.int64)


def _leaf_context(leaf: GoogleLeaf, *, leaf_index: int) -> dict[str, object]:
    return {
        "leaf_index": int(leaf_index),
        "distance": int(leaf.distance or -1),
        "basis": str(leaf.basis),
        "rounds": int(leaf.rounds or -1),
        "sample_id": str(leaf.sample_id),
        "patch_id": str(leaf.patch_id),
    }


def _arrays(kwargs: dict[str, object]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    return (
        np.asarray(kwargs["x_train"], dtype=np.float64),
        np.asarray(kwargs["y_train"], dtype=np.float64),
        np.asarray(kwargs["x_test"], dtype=np.float64),
        np.asarray(kwargs["y_test"], dtype=np.float64),
    )


def _baseline_params(kwargs: dict[str, object]) -> dict[str, object]:
    params = kwargs.get("baseline_params", {})
    return dict(params) if isinstance(params, dict) else {}


def _moment_metrics(x: np.ndarray, generated: np.ndarray) -> dict[str, object]:
    if x.size == 0 or generated.size == 0:
        return {"syndrome_first_moment_mae": None, "syndrome_second_moment_relative_fro": None}
    mean_x = np.mean(x, axis=0)
    mean_g = np.mean(generated, axis=0)
    cov_x = _covariance(x)
    cov_g = _covariance(generated)
    denom = max(float(np.linalg.norm(cov_x, ord="fro")), NUMERICAL_FLOOR)
    return {
        "syndrome_first_moment_mae": _json_float(float(np.mean(np.abs(mean_g - mean_x)))),
        "syndrome_second_moment_relative_fro": _json_float(float(np.linalg.norm(cov_g - cov_x, ord="fro") / denom)),
    }


def _covariance(x: np.ndarray) -> np.ndarray:
    if x.shape[0] <= 1:
        return np.zeros((x.shape[1], x.shape[1]), dtype=np.float64)
    centered = x - np.mean(x, axis=0, keepdims=True)
    return (centered.T @ centered) / float(max(x.shape[0] - 1, 1))


def _independent_nll(x: np.ndarray, p: np.ndarray) -> float:
    if x.size == 0:
        return 0.0
    return float(np.mean(np.sum(_binary_ce(x, np.repeat(_clip(p)[None, :], x.shape[0], axis=0)), axis=1)))


def _binary_ce(x: np.ndarray, p: np.ndarray) -> np.ndarray:
    p = _clip(p)
    return -(x * np.log(p) + (1.0 - x) * np.log(1.0 - p))


def _clip(p: np.ndarray) -> np.ndarray:
    return np.clip(np.asarray(p, dtype=np.float64), NUMERICAL_FLOOR, 1.0 - NUMERICAL_FLOOR)


def _clip_scalar(value: float) -> float:
    return float(min(max(float(value), NUMERICAL_FLOOR), 1.0 - NUMERICAL_FLOOR))


def _rng_sample_bernoulli_matrix(p: np.ndarray, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return (rng.random(p.shape) < _clip(p)).astype(np.float64)


def _fit_bernoulli_mixture(data: np.ndarray, *, k: int, steps: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    n, d = data.shape
    k = max(1, min(int(k), n))
    theta = _clip(data[rng.choice(n, size=k, replace=False)].astype(np.float64) * 0.8 + 0.1)
    weights = np.full(k, 1.0 / k, dtype=np.float64)
    for _ in range(max(1, int(steps))):
        log_resp = _mixture_log_responsibilities(data, weights, theta)
        resp = np.exp(log_resp)
        nk = np.maximum(np.sum(resp, axis=0), NUMERICAL_FLOOR)
        weights = nk / float(n)
        theta = _clip((resp.T @ data) / nk[:, None])
    return weights, theta


def _mixture_log_responsibilities(data: np.ndarray, weights: np.ndarray, theta: np.ndarray) -> np.ndarray:
    log_prob = data @ np.log(_clip(theta)).T + (1.0 - data) @ np.log(1.0 - _clip(theta)).T
    log_prob += np.log(_clip(weights))[None, :]
    norm = _logsumexp(log_prob, axis=1)
    return log_prob - norm[:, None]


def _mixture_nll(data: np.ndarray, weights: np.ndarray, theta: np.ndarray) -> float:
    log_prob = data @ np.log(_clip(theta)).T + (1.0 - data) @ np.log(1.0 - _clip(theta)).T
    log_prob += np.log(_clip(weights))[None, :]
    return float(-np.mean(_logsumexp(log_prob, axis=1)))


def _sample_bernoulli_mixture(weights: np.ndarray, theta: np.ndarray, n: int, *, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    labels = rng.choice(theta.shape[0], size=int(n), p=_normalize(weights))
    return _rng_sample_bernoulli_matrix(theta[labels], seed=seed + 1)


def _logsumexp(x: np.ndarray, axis: int) -> np.ndarray:
    m = np.max(x, axis=axis)
    return m + np.log(np.sum(np.exp(x - np.expand_dims(m, axis=axis)), axis=axis))


def _two_sample_linear_auc(real: np.ndarray, generated: np.ndarray) -> float | None:
    if real.size == 0 or generated.size == 0:
        return None
    n = min(real.shape[0], generated.shape[0])
    real = real[:n]
    generated = generated[:n]
    w = np.mean(real, axis=0) - np.mean(generated, axis=0)
    scores = np.concatenate([real @ w, generated @ w])
    labels = np.concatenate([np.ones(n), np.zeros(n)])
    return _json_float(_auc_from_scores(labels, scores))


def _auc_from_scores(labels: np.ndarray, scores: np.ndarray) -> float:
    order = np.argsort(scores)
    ranks = np.empty_like(order, dtype=np.float64)
    ranks[order] = np.arange(1, len(scores) + 1, dtype=np.float64)
    pos = labels > 0.5
    n_pos = int(np.sum(pos))
    n_neg = int(len(labels) - n_pos)
    if n_pos == 0 or n_neg == 0:
        return 0.5
    return float((np.sum(ranks[pos]) - n_pos * (n_pos + 1) / 2.0) / float(n_pos * n_neg))


def _summary_stats(values: list[float]) -> dict[str, object]:
    if not values:
        return {"mean": None, "std": None, "min": None, "max": None, "count": 0}
    arr = np.asarray(values, dtype=np.float64)
    return {
        "mean": _json_float(float(np.mean(arr))),
        "std": _json_float(float(np.std(arr))),
        "min": _json_float(float(np.min(arr))),
        "max": _json_float(float(np.max(arr))),
        "count": int(arr.size),
    }


def _normalize(weights: np.ndarray) -> np.ndarray:
    weights = np.maximum(np.asarray(weights, dtype=np.float64), 0.0)
    total = float(np.sum(weights))
    if total <= 0.0:
        return np.full(weights.shape, 1.0 / max(weights.size, 1))
    return weights / total


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(out):
        return None
    return out


def _json_float(value: float | None) -> float | None:
    if value is None:
        return None
    out = float(value)
    if not math.isfinite(out):
        return None
    return out


def _decoder_key(pathway: str) -> str:
    for key, value in DECODER_BASELINES.items():
        if value == pathway:
            return key
    return pathway


def _metric_definitions() -> dict[str, object]:
    return {
        "logical_p_L": "Heldout observable-flip prediction failure rate. Decoder baselines use Google obs_flips_predicted.b8; external statistical baselines report this only if their upstream implementation provides a decoder or calibrated logical predictor.",
        "logical_delta_p_L_vs_matching_si1000": "logical_p_L minus correlated_matching_decoder_with_si1000_prior on the same leaf/test split.",
        "decay_curve_distance_log_rms_vs_no_correction_curve": "RMS log distance between baseline logical_p_L by round and the no-correction actual observable-flip rate by round.",
        "cross_decoding_delta_p_L_vs_matching_si1000": "Not run in this one-round suite because it requires downstream decoder retraining from generated data.",
        "syndrome_first_moment_mae": "Mean absolute difference between heldout detector-bit rates and generated/sample-implied detector-bit rates.",
        "syndrome_second_moment_relative_fro": "Relative Frobenius distance between heldout detector covariance and generated detector covariance.",
        "syndrome_nll_per_shot": "Tractable detector or joint binary NLL when native; per heldout shot over selected detector bits.",
        "masked_pseudo_likelihood_nll_per_shot": "Pseudo-likelihood or reconstruction proxy for models without exact normalized likelihood.",
        "two_sample_auc": "Linear two-sample AUC separating real heldout detector syndromes from generated detector syndromes; 0.5 is best.",
        "external_baseline_policy": "Statistical/deep baselines are official/cloned-upstream only. SCOPE-native proxy implementations are not reported as external baseline results.",
        "dem_f1": "Not applicable on Google hardware data because true mechanism/location support labels are absent.",
        "strength_spearman": "Not applicable on Google hardware data because true mechanism strength labels are absent.",
    }


def _config_dict(cfg: BaselineSuiteConfig) -> dict[str, object]:
    return {
        "dataset_root": str(cfg.dataset_root),
        "dataset_name": cfg.dataset_name,
        "output_dir": str(cfg.output_dir),
        "distances": list(cfg.distances),
        "bases": list(cfg.bases),
        "rounds": list(cfg.rounds),
        "max_leaves_per_distance_basis": int(cfg.max_leaves_per_distance_basis),
        "max_shots_per_leaf": int(cfg.max_shots_per_leaf),
        "detector_limit": int(cfg.detector_limit),
        "train_fraction": float(cfg.train_fraction),
        "seed": int(cfg.seed),
        "seeds": [int(seed) for seed in cfg.seeds],
        "validation_fraction": float(cfg.validation_fraction),
        "selection_profile": str(cfg.selection_profile),
        "mixture_components": int(cfg.mixture_components),
        "max_iter": int(cfg.max_iter),
        "torch_epochs": int(cfg.torch_epochs),
        "torch_batch_size": int(cfg.torch_batch_size),
        "gan_epochs": None if cfg.gan_epochs is None else int(cfg.gan_epochs),
        "rbm_steps": None if cfg.rbm_steps is None else int(cfg.rbm_steps),
        "autoregressive_steps": None if cfg.autoregressive_steps is None else int(cfg.autoregressive_steps),
        "baseline_keys": list(cfg.baseline_keys),
    }


def _write_outputs(result: dict[str, object], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "metrics.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "summary.md").write_text(_summary_markdown(result), encoding="utf-8")


def _summary_markdown(result: dict[str, object]) -> str:
    lines = [
        "# Google D3/D5 Baseline Suite",
        "",
        f"- Decision: `{result.get('decision')}`",
        f"- Selected leaves: `{dict(result.get('dataset', {})).get('selected_leaf_count')}`",
        f"- Wall clock seconds: `{result.get('wall_clock_seconds')}`",
        "",
        "| baseline | wall s | partial wall s | logical p_L | delta vs SI1000 | decay log RMS | 1st moment MAE | 2nd moment rel Fro | NLL/shot | NLL/bit | pseudo NLL/shot | Gaussian NLL/shot | two-sample AUC |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    aggregate = dict(result.get("aggregate", {}))
    for key in result.get("baseline_keys", BASELINE_KEYS):
        row = dict(dict(aggregate.get(key, {})).get("metrics", {}))
        lines.append(
            "| "
            + f"`{key}` | "
            + f"{_fmt_summary(row.get('wall_clock_seconds'))} | "
            + f"{_fmt_value(row.get('partial_run_wall_clock_seconds'))} | "
            + f"{_fmt_summary(row.get('logical_p_L'))} | "
            + f"{_fmt_summary(row.get('logical_delta_p_L_vs_matching_si1000'))} | "
            + f"{_fmt_value(row.get('decay_curve_distance_log_rms_vs_no_correction_curve'))} | "
            + f"{_fmt_summary(row.get('syndrome_first_moment_mae'))} | "
            + f"{_fmt_summary(row.get('syndrome_second_moment_relative_fro'))} | "
            + f"{_fmt_summary(row.get('syndrome_nll_per_shot'))} | "
            + f"{_fmt_summary(row.get('syndrome_nll_per_bit'))} | "
            + f"{_fmt_summary(row.get('masked_pseudo_likelihood_nll_per_shot'))} | "
            + f"{_fmt_summary(row.get('gaussian_density_nll_per_shot'))} | "
            + f"{_fmt_summary(row.get('two_sample_auc'))} |"
        )
    lines.extend(
        [
            "",
            "DEM-F1 and strength Spearman are not applicable on Google hardware data because the dataset has no true mechanism/location/strength labels.",
            "Cross-decoding delta is not run in this one-round suite because it requires downstream decoder retraining from generated data.",
        ]
    )
    return "\n".join(lines) + "\n"


def _fmt_summary(value: object) -> str:
    if not isinstance(value, dict):
        return "NA"
    mean = value.get("mean")
    if mean is None:
        return "NA"
    return f"{float(mean):.6g}"


def _fmt_value(value: object) -> str:
    if not isinstance(value, dict):
        return "NA"
    scalar = value.get("value")
    if scalar is None:
        return "NA"
    return f"{float(scalar):.6g}"
