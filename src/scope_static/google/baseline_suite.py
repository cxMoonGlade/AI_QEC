from __future__ import annotations

from contextlib import contextmanager
from collections import Counter, defaultdict
from dataclasses import dataclass
import importlib
import json
import math
from pathlib import Path
import sys
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

UPSTREAM_HELPER_BASELINES = (
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
    distances: tuple[int, ...] | None = (3, 5)
    bases: tuple[str, ...] | None = ("X", "Z")
    rounds: tuple[int, ...] | None = (1, 10)
    max_leaves_per_distance_basis: int | None = 2
    max_shots_per_leaf: int | None = 2048
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
    external_repo_root: Path = Path("external/baselines")
    external_work_dir: Path = Path("outputs/google_static/external_baseline_work")
    qecgpt_network: str = "made"
    qecgpt_depth: int = 3
    qecgpt_width: int = 20
    qecgpt_d_model: int = 128
    qecgpt_n_heads: int = 4
    qecgpt_d_ff: int = 512
    qecgpt_n_layers: int = 2
    qecgpt_batch_size: int = 10000
    qecgpt_lr: float = 0.001
    qecgpt_device: str = "cuda:0"
    rbm_hidden_units: int | None = None
    rbm_learning_rate: float = 0.1
    checkpoint_every_leaf_results: int | None = 50
    baseline_keys: tuple[str, ...] = BASELINE_KEYS


def run_google_d3d5_baseline_suite(config: BaselineSuiteConfig | None = None) -> dict[str, object]:
    cfg = config or BaselineSuiteConfig()
    start = time.perf_counter()
    leaves = _select_leaves(cfg)
    if not leaves:
        raise ValueError("No Google D3/D5 leaves selected for baseline suite")
    progress_path = _reset_progress_log(cfg)
    _append_progress(
        progress_path,
        {
            "event": "start",
            "selected_leaf_count": int(len(leaves)),
            "repeat_seed_count": int(len(cfg.seeds or (cfg.seed,))),
            "baseline_keys": list(cfg.baseline_keys),
        },
    )
    leaf_results = []
    for repeat_index, repeat_seed in enumerate(cfg.seeds or (cfg.seed,)):
        rng = np.random.default_rng(int(repeat_seed))
        for leaf_idx, leaf in enumerate(leaves):
            leaf_seed = int(rng.integers(0, 2**31 - 1))
            leaf_start = time.perf_counter()
            result = _run_leaf_baselines(
                leaf,
                cfg=cfg,
                seed=leaf_seed,
                leaf_index=leaf_idx,
                repeat_seed=int(repeat_seed),
                repeat_index=int(repeat_index),
            )
            leaf_results.append(result)
            _append_progress(
                progress_path,
                {
                    "event": "leaf_result",
                    "repeat_index": int(repeat_index),
                    "repeat_seed": int(repeat_seed),
                    "leaf_index": int(leaf_idx),
                    "context_id": leaf.context_id,
                    "shots_loaded": int(result.get("shots_loaded", 0)),
                    "wall_clock_seconds": float(time.perf_counter() - leaf_start),
                    "completed_leaf_results": int(len(leaf_results)),
                },
            )
            _maybe_write_partial_checkpoint(leaf_results, cfg, baseline_keys=cfg.baseline_keys)
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
    _append_progress(
        progress_path,
        {
            "event": "complete",
            "wall_clock_seconds": float(result["wall_clock_seconds"]),
            "metrics_json": str(cfg.output_dir / "metrics.json"),
        },
    )
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
    max_shots = None if cfg.max_shots_per_leaf is None else int(cfg.max_shots_per_leaf)
    observations = load_google_observations(leaf, max_shots=max_shots).astype(np.uint8)
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
        if key in requested_baselines and key not in UPSTREAM_HELPER_BASELINES:
            baselines[key] = _external_adapter_missing_record(key)

    baseline_fns: dict[str, Callable[..., dict[str, object]]] = {
        "independent_detector": lambda **kwargs: _run_upstream_dependency_probe("independent_detector", **kwargs),
        "pairwise_ising": lambda **kwargs: _run_upstream_dependency_probe("pairwise_ising", **kwargs),
        "factor_graph_crf": lambda **kwargs: _run_upstream_dependency_probe("factor_graph_crf", **kwargs),
        "graphical_lasso": lambda **kwargs: _run_upstream_dependency_probe("graphical_lasso", **kwargs),
        "bayesian_hierarchical": lambda **kwargs: _run_upstream_dependency_probe("bayesian_hierarchical", **kwargs),
        "bernoulli_mixture_em": lambda **kwargs: _run_upstream_dependency_probe("bernoulli_mixture_em", **kwargs),
        "sparse_coding_dictionary": lambda **kwargs: _run_upstream_dependency_probe("sparse_coding_dictionary", **kwargs),
        "causal_discovery_structure": lambda **kwargs: _run_upstream_dependency_probe("causal_discovery_structure", **kwargs),
        "vae": lambda **kwargs: _run_upstream_dependency_probe("vae", **kwargs),
        "gan": lambda **kwargs: _run_upstream_dependency_probe("gan", **kwargs),
        "ebm_rbm_crbm": _run_upstream_rbm,
        "autoregressive_generative": _run_upstream_qecgpt_autoregressive,
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


def _run_upstream_dependency_probe(key: str, **kwargs: object) -> dict[str, object]:
    cfg = kwargs["cfg"]
    assert isinstance(cfg, BaselineSuiteConfig)
    probes = _upstream_probe_specs(key, cfg)
    notes = [
        "Minimum helper ran only an upstream import/entrypoint compatibility probe; no local proxy model was fitted.",
    ]
    available = []
    missing = []
    for module_name, repo_path in probes:
        ok, detail = _probe_module_available(module_name, repo_path)
        row = {"module": module_name, "repo_path": str(repo_path), "detail": detail}
        if ok:
            available.append(row)
        else:
            missing.append(row)
    status = "not_run_upstream_entrypoint_pending" if available else "not_run_upstream_dependency_missing"
    try:
        entry = baseline_entry(_registry_key_for_suite_key(key))
        repos = [repo.to_dict() for repo in entry.external_repositories]
    except KeyError:
        repos = []
    if available:
        notes.append(
            "Upstream module import is available, but this baseline still lacks a native Google D3/D5 training/evaluation entrypoint."
        )
    else:
        notes.append("Upstream module import failed in the aiqec environment; install/build the cloned repository before scoring.")
    record = _empty_metric_record(key, implementation_status=status, notes=notes)
    record.update(
        {
            "baseline_family": key,
            "runner_policy": "minimum_helper_no_local_model_proxy",
            "external_repositories": repos,
            "upstream_probe_available": available,
            "upstream_probe_missing": missing,
        }
    )
    return record


def _upstream_probe_specs(key: str, cfg: BaselineSuiteConfig) -> list[tuple[str, Path]]:
    root = Path(cfg.external_repo_root)
    specs = {
        "independent_detector": [("pomegranate", root / "pomegranate")],
        "bernoulli_mixture_em": [("pomegranate", root / "pomegranate")],
        "pairwise_ising": [("coniii", root / "coniii")],
        "factor_graph_crf": [("pgmpy", root / "pgmpy")],
        "graphical_lasso": [("gglasso", root / "GGLasso")],
        "bayesian_hierarchical": [("pyro", root / "pyro")],
        "vae": [("pyro", root / "pyro"), ("vae", root / "pytorch-examples")],
        "sparse_coding_dictionary": [("prosper", root / "prosper")],
        "causal_discovery_structure": [("causallearn", root / "causal-learn")],
        "gan": [("models", root / "PyTorch-GAN")],
    }
    return list(specs.get(key, []))


def _probe_module_available(module_name: str, repo_path: Path) -> tuple[bool, str]:
    search_paths = [repo_path] if repo_path.exists() else []
    if repo_path.name == "PyTorch-GAN":
        search_paths.append(repo_path / "implementations")
    if repo_path.name == "pytorch-examples":
        search_paths.append(repo_path / "vae")
    try:
        with _temporary_sys_path(search_paths):
            module = importlib.import_module(module_name)
        return True, f"imported {getattr(module, '__file__', module_name)}"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def _run_upstream_rbm(**kwargs: object) -> dict[str, object]:
    x_train, _y_train, x_test, y_test = _arrays(kwargs)
    cfg = kwargs["cfg"]
    assert isinstance(cfg, BaselineSuiteConfig)
    seed = int(kwargs["seed"])
    params = _baseline_params(kwargs)
    repo_path = Path(cfg.external_repo_root) / "restricted-boltzmann-machines"
    if not (repo_path / "rbm.py").is_file():
        return _upstream_unavailable_record(
            "ebm_rbm_crbm",
            cfg=cfg,
            status="not_run_upstream_repository_missing",
            notes=[f"Missing upstream RBM file: {repo_path / 'rbm.py'}"],
        )
    if x_train.size == 0 or x_test.size == 0:
        return _model_metric_record(
            "ebm_rbm_crbm",
            x_test=x_test,
            y_test=y_test,
            generated=np.zeros_like(x_test),
            implementation_status="upstream_rbm_empty_data",
            notes=["Empty train/test split; upstream RBM was not fitted."],
        )
    np.random.seed(seed)
    with _temporary_sys_path([repo_path]):
        from rbm import RBM  # type: ignore

    hidden_units = int(params.get("hidden_units") or cfg.rbm_hidden_units or max(2, min(64, x_train.shape[1] // 2)))
    epochs = int(params.get("epochs") or cfg.rbm_steps or cfg.max_iter)
    learning_rate = float(params.get("learning_rate") or cfg.rbm_learning_rate)
    rbm = RBM(num_visible=int(x_train.shape[1]), num_hidden=hidden_units)
    rbm.debug_print = False
    rbm.train(np.asarray(x_train, dtype=np.float64), max_epochs=max(1, epochs), learning_rate=learning_rate)
    generated = np.asarray(rbm.daydream(int(x_test.shape[0])), dtype=np.float64)
    generated = (generated >= 0.5).astype(np.float64)
    return _model_metric_record(
        "ebm_rbm_crbm",
        x_test=x_test,
        y_test=y_test,
        generated=generated,
        implementation_status="upstream_rbm_native_class_minimum_helper",
        structural_summary={
            "upstream_repository": "external/baselines/restricted-boltzmann-machines",
            "upstream_entrypoint": "rbm.RBM.train/daydream",
            "helper_scope": "Google selected-detector matrix conversion plus common metric normalization",
            "hidden_units": int(hidden_units),
            "epochs": int(epochs),
            "learning_rate": float(learning_rate),
            "uses_google_true_mechanism_labels": False,
            "uses_observable_flips_for_detector_model": False,
            "logical_p_l_status": "not_reported_not_a_decoder",
        },
        notes=[
            "RBM helper imports and calls the cloned upstream RBM class; no local RBM equations are reimplemented.",
            "RBM reports generated-syndrome moment/AUC metrics only; no exact normalized NLL is provided by this upstream implementation.",
        ],
    )


def _run_upstream_qecgpt_autoregressive(**kwargs: object) -> dict[str, object]:
    x_train, _y_train, x_test, y_test = _arrays(kwargs)
    cfg = kwargs["cfg"]
    assert isinstance(cfg, BaselineSuiteConfig)
    seed = int(kwargs["seed"])
    params = _baseline_params(kwargs)
    repo_path = Path(cfg.external_repo_root) / "qecGPT"
    qec_path = repo_path / "qec"
    if not (qec_path / "module" / "MADE.py").is_file():
        return _upstream_unavailable_record(
            "autoregressive_generative",
            cfg=cfg,
            status="not_run_upstream_repository_missing",
            notes=[f"Missing upstream qecGPT module: {qec_path / 'module' / 'MADE.py'}"],
        )
    if x_train.size == 0 or x_test.size == 0:
        return _model_metric_record(
            "autoregressive_generative",
            x_test=x_test,
            y_test=y_test,
            generated=np.zeros_like(x_test),
            implementation_status="upstream_qecgpt_empty_data",
            notes=["Empty train/test split; qecGPT was not fitted."],
        )
    try:
        return _fit_qecgpt_autoregressive(
            x_train=x_train,
            x_test=x_test,
            y_test=y_test,
            cfg=cfg,
            params=params,
            seed=seed,
            qec_path=qec_path,
        )
    except Exception as exc:
        return _upstream_unavailable_record(
            "autoregressive_generative",
            cfg=cfg,
            status="failed_upstream_qecgpt_helper",
            notes=[f"{type(exc).__name__}: {exc}"],
        )


def _fit_qecgpt_autoregressive(
    *,
    x_train: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
    cfg: BaselineSuiteConfig,
    params: dict[str, object],
    seed: int,
    qec_path: Path,
) -> dict[str, object]:
    import torch

    with _temporary_sys_path([qec_path]):
        from module import MADE, TraDE  # type: ignore

    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    device_name = str(params.get("device") or cfg.qecgpt_device)
    if device_name.startswith("cuda") and not torch.cuda.is_available():
        device_name = "cpu"
    device = torch.device(device_name)
    dtype = torch.float32
    network = str(params.get("network") or cfg.qecgpt_network).lower()
    epochs = int(params.get("epochs") or cfg.autoregressive_steps or cfg.torch_epochs)
    batch_size = int(params.get("batch_size") or cfg.qecgpt_batch_size)
    lr = float(params.get("learning_rate") or cfg.qecgpt_lr)
    n_bits = int(x_train.shape[1])
    if network == "trade":
        model = TraDE(
            n=n_bits,
            d_model=int(params.get("d_model") or cfg.qecgpt_d_model),
            n_heads=int(params.get("n_heads") or cfg.qecgpt_n_heads),
            d_ff=int(params.get("d_ff") or cfg.qecgpt_d_ff),
            n_layers=int(params.get("n_layers") or cfg.qecgpt_n_layers),
            device=str(device),
            dropout=0,
        ).to(device).to(dtype)
        train_tensor = torch.as_tensor(x_train, dtype=dtype, device=device)
        test_tensor = torch.as_tensor(x_test, dtype=dtype, device=device)
    else:
        model = MADE(
            n=n_bits,
            depth=int(params.get("depth") or cfg.qecgpt_depth),
            width=int(params.get("width") or cfg.qecgpt_width),
            residual=False,
        ).to(device).to(dtype)
        train_tensor = torch.as_tensor(x_train * 2.0 - 1.0, dtype=dtype, device=device)
        test_tensor = torch.as_tensor(x_test * 2.0 - 1.0, dtype=dtype, device=device)
        network = "made"
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    n_train = int(train_tensor.shape[0])
    batch_size = max(1, min(batch_size, n_train))
    model.train()
    for _epoch in range(max(1, epochs)):
        idx = torch.randint(0, n_train, (batch_size,), device=device)
        batch = train_tensor[idx]
        loss = -torch.mean(model.log_prob(batch), dim=0)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    model.eval()
    with torch.no_grad():
        nll = float((-model.log_prob(test_tensor)).mean().detach().cpu())
        probs = model.forward(test_tensor).detach().cpu().numpy().astype(np.float64)
        if network == "made":
            samples = model.samples(int(x_test.shape[0]), n_bits, device=device, dtype=dtype)
            generated = ((samples.detach().cpu().numpy().astype(np.float64) + 1.0) / 2.0)
        else:
            samples = model.samples(int(x_test.shape[0]))
            generated = samples.detach().cpu().numpy().astype(np.float64)
    generated = (generated >= 0.5).astype(np.float64)
    return _model_metric_record(
        "autoregressive_generative",
        x_test=x_test,
        y_test=y_test,
        generated=generated,
        detector_prob=probs,
        syndrome_nll_per_shot=nll,
        implementation_status="upstream_qecgpt_native_model_minimum_helper",
        structural_summary={
            "upstream_repository": "external/baselines/qecGPT",
            "upstream_entrypoint": "qec.module.MADE/TraDE.log_prob/samples",
            "helper_scope": "Google selected-detector matrix conversion, upstream training loop invocation, common metric normalization",
            "network": network,
            "epochs": int(epochs),
            "batch_size": int(batch_size),
            "learning_rate": float(lr),
            "device": str(device),
            "uses_google_true_mechanism_labels": False,
            "uses_observable_flips_for_detector_model": False,
            "logical_p_l_status": "not_reported_not_a_decoder",
        },
        notes=[
            "qecGPT helper imports and trains the cloned upstream MADE/TraDE model class on Google detector bits.",
            "This reports generative syndrome metrics only; qecGPT logical decoding scripts are not used because their public Google path is hard-coded to a different .01/layout contract.",
        ],
    )


def _upstream_unavailable_record(
    key: str,
    *,
    cfg: BaselineSuiteConfig,
    status: str,
    notes: list[str],
) -> dict[str, object]:
    try:
        entry = baseline_entry(_registry_key_for_suite_key(key))
        repos = [repo.to_dict() for repo in entry.external_repositories]
    except KeyError:
        repos = []
    record = _empty_metric_record(key, implementation_status=status, notes=notes)
    record.update(
        {
            "baseline_family": key,
            "runner_policy": "minimum_helper_no_local_model_proxy",
            "external_repositories": repos,
            "external_repo_root": str(cfg.external_repo_root),
        }
    )
    return record


@contextmanager
def _temporary_sys_path(paths: Iterable[Path]):
    original = list(sys.path)
    try:
        for path in reversed([Path(item) for item in paths if Path(item).exists()]):
            sys.path.insert(0, str(path))
        yield
    finally:
        sys.path[:] = original


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
        if key in EXTERNAL_ADAPTER_REQUIRED_BASELINES and key not in UPSTREAM_HELPER_BASELINES:
            out[key] = {
                "candidate_count": 1,
                "source": ["minimum_upstream_probe_no_proxy_metrics"],
                "compute_budget": {
                    "selection_profile": str(cfg.selection_profile),
                    "repeat_seed_count": int(len(cfg.seeds or (cfg.seed,))),
                    "max_shots_per_leaf": None if cfg.max_shots_per_leaf is None else int(cfg.max_shots_per_leaf),
                    "detector_limit": int(cfg.detector_limit),
                    "status": "probe_only_until_native_upstream_google_entrypoint_runs",
                },
                "candidates": [{}],
                "run_policy": "minimum_helper_records_upstream_dependency_or_entrypoint_status_without_local_proxy",
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

    if key == "ebm_rbm_crbm":
        return [
            row(
                {
                    "hidden_units": None if cfg.rbm_hidden_units is None else int(cfg.rbm_hidden_units),
                    "epochs": int(cfg.rbm_steps or cfg.max_iter),
                    "learning_rate": float(cfg.rbm_learning_rate),
                },
                "cloned_upstream_restricted_boltzmann_machines_rbm_class",
            )
        ]
    if key == "autoregressive_generative":
        params = {
            "network": str(cfg.qecgpt_network),
            "epochs": int(cfg.autoregressive_steps or cfg.torch_epochs),
            "batch_size": int(cfg.qecgpt_batch_size),
            "learning_rate": float(cfg.qecgpt_lr),
            "device": str(cfg.qecgpt_device),
        }
        if str(cfg.qecgpt_network).lower() == "trade":
            params.update(
                {
                    "d_model": int(cfg.qecgpt_d_model),
                    "n_heads": int(cfg.qecgpt_n_heads),
                    "d_ff": int(cfg.qecgpt_d_ff),
                    "n_layers": int(cfg.qecgpt_n_layers),
                }
            )
        else:
            params.update({"depth": int(cfg.qecgpt_depth), "width": int(cfg.qecgpt_width)})
        return [row(params, "cloned_upstream_qecgpt_made_trade_model_class")]
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
        "max_shots_per_leaf": None if cfg.max_shots_per_leaf is None else int(cfg.max_shots_per_leaf),
        "detector_limit": int(cfg.detector_limit),
        "torch_batch_size": int(cfg.torch_batch_size),
        "qecgpt_batch_size": int(cfg.qecgpt_batch_size),
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
    distances = None if cfg.distances is None else set(cfg.distances)
    bases = None if cfg.bases is None else set(cfg.bases)
    rounds = None if cfg.rounds is None else set(cfg.rounds)
    leaves = [
        leaf
        for leaf in leaves
        if (distances is None or int(leaf.distance or -1) in distances)
        and (bases is None or str(leaf.basis) in bases)
        and (rounds is None or int(leaf.rounds or -1) in rounds)
    ]
    leaves = sorted(leaves, key=lambda row: (int(row.distance or -1), str(row.basis), int(row.rounds or -1), str(row.sample_id)))
    if cfg.max_leaves_per_distance_basis is None:
        return leaves
    selected: list[GoogleLeaf] = []
    counts: Counter[tuple[int, str, int]] = Counter()
    observed_rounds = {int(leaf.rounds or -1) for leaf in leaves}
    per_round_limit = max(1, int(math.ceil(int(cfg.max_leaves_per_distance_basis) / max(len(observed_rounds), 1))))
    for leaf in leaves:
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
        "distances": None if cfg.distances is None else list(cfg.distances),
        "bases": None if cfg.bases is None else list(cfg.bases),
        "rounds": None if cfg.rounds is None else list(cfg.rounds),
        "max_leaves_per_distance_basis": None
        if cfg.max_leaves_per_distance_basis is None
        else int(cfg.max_leaves_per_distance_basis),
        "max_shots_per_leaf": None if cfg.max_shots_per_leaf is None else int(cfg.max_shots_per_leaf),
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
        "external_repo_root": str(cfg.external_repo_root),
        "external_work_dir": str(cfg.external_work_dir),
        "qecgpt_network": str(cfg.qecgpt_network),
        "qecgpt_depth": int(cfg.qecgpt_depth),
        "qecgpt_width": int(cfg.qecgpt_width),
        "qecgpt_d_model": int(cfg.qecgpt_d_model),
        "qecgpt_n_heads": int(cfg.qecgpt_n_heads),
        "qecgpt_d_ff": int(cfg.qecgpt_d_ff),
        "qecgpt_n_layers": int(cfg.qecgpt_n_layers),
        "qecgpt_batch_size": int(cfg.qecgpt_batch_size),
        "qecgpt_lr": float(cfg.qecgpt_lr),
        "qecgpt_device": str(cfg.qecgpt_device),
        "rbm_hidden_units": None if cfg.rbm_hidden_units is None else int(cfg.rbm_hidden_units),
        "rbm_learning_rate": float(cfg.rbm_learning_rate),
        "checkpoint_every_leaf_results": None
        if cfg.checkpoint_every_leaf_results is None
        else int(cfg.checkpoint_every_leaf_results),
        "baseline_keys": list(cfg.baseline_keys),
    }


def _reset_progress_log(cfg: BaselineSuiteConfig) -> Path:
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    progress_path = cfg.output_dir / "progress.jsonl"
    progress_path.write_text("", encoding="utf-8")
    return progress_path


def _append_progress(path: Path, row: dict[str, object]) -> None:
    payload = {"time": time.strftime("%Y-%m-%dT%H:%M:%S%z"), **row}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def _maybe_write_partial_checkpoint(
    leaf_results: list[dict[str, object]],
    cfg: BaselineSuiteConfig,
    *,
    baseline_keys: tuple[str, ...],
) -> None:
    every = cfg.checkpoint_every_leaf_results
    if every is None or every <= 0 or len(leaf_results) % int(every) != 0:
        return
    partial = {
        "schema": "scope_static_google_d3d5_baseline_partial_checkpoint_v1",
        "completed_leaf_result_count": int(len(leaf_results)),
        "config": _config_dict(cfg),
        "aggregate": _aggregate_leaf_results(leaf_results, baseline_keys=baseline_keys),
    }
    (cfg.output_dir / "partial_metrics.json").write_text(
        json.dumps(partial, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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
