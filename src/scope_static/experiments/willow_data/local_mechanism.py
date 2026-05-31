from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import time

import numpy as np
import torch

from scope_static.dem.baselines import baseline_metadata
from scope_static.dem.dmle_upstream import UpstreamDMLEQECConfig, fit_upstream_dmle_qec_tensor_network
from scope_static.dem.fields import LocalFaultLogitField, make_field
from scope_static.google.mechanism import (
    dem_prior_agreement,
    fit_cluster_mean_logits,
    pairwise_logit_stability,
    probability_to_logit,
    proxy_alignment,
    proxy_partitions,
)
from scope_static.google.set1 import (
    CLAIM_BOUNDARY,
    build_google_fault_graph,
    build_google_schedule_context,
    find_google_set1_leaf,
    load_google_circuit,
    load_google_dem_data,
    load_google_observations,
    load_google_predicted_observables,
)
from scope_static.identifiability import combined_signature, deterministic_kmeans, structural_signature
from scope_static.dem.local_mechanism import (
    graph_smooth_features,
    local_probability_features,
    nmf_codes,
    overlapping_topk_codes,
    pca_denoised_features,
    pca_scores,
    spectral_similarity_embedding,
)
from scope_static.dem.likelihood import WindowBatchNLLCache, resolve_likelihood_backend, subset_window_batch_nll_cache
from scope_static.dem.likelihoods.local_window_parity import ExactLocalWindowParityLikelihood
from scope_static.dem.metrics import (
    _flat_window_evidence_fields,
    _window_evidence_groups,
    augment_model_comparison_metrics,
    decoder_prediction_metrics,
    empirical_detector_rate_metrics,
    empirical_local_correlation_metrics,
    empirical_window_entropy_from_batch_cache,
    evaluate_real_data_model,
    local_detector_pairs,
    logical_flip_calibration_metrics,
)
from scope_static.dem.training import fit_field
from scope_static.dem.windows import WindowPlan, window_coverage_audit_dict

from .static import (
    _fmt_float,
    _prepare_eval_cache,
    _prepare_google_fault_graph,
    _prepare_train_objectives,
    _print_table,
    _resolve_execution_mode,
    _eval_window_config,
    _same_windows,
    _spectral_memory_cap_bytes,
    _train_heldout_split,
    _window_plan_audit,
    _with_eval_window_metrics,
    _window_config,
    GOOGLE_PRIMARY_METRIC,
)


@dataclass(frozen=True)
class _WindowGroupEval:
    name: str
    likelihood: ExactLocalWindowParityLikelihood | None
    entropy: float | None
    num_windows: int
    mean_window_bits: float


@dataclass(frozen=True)
class _FastGoogleEvaluator:
    args: argparse.Namespace
    graph: object
    observations: torch.Tensor
    predicted_observables: torch.Tensor | None
    group_evals: dict[str, _WindowGroupEval]
    num_evaluation_windows: int
    max_evaluation_window_bits: int
    device: torch.device

    def evaluate(self, logits: torch.Tensor) -> dict[str, object]:
        model_logits = torch.as_tensor(logits, dtype=torch.float64, device=self.device)
        return self._evaluate_one(model_logits)

    def evaluate_batch(self, logits_batch: torch.Tensor) -> list[dict[str, object]]:
        model_logits_batch = torch.as_tensor(logits_batch, dtype=torch.float64, device=self.device)
        if model_logits_batch.ndim != 2:
            raise ValueError("logits_batch must have shape [C, M]")
        if model_logits_batch.shape[0] == 0:
            return []
        nll_by_group: dict[str, list[float | None]] = {}
        for group_name, group_eval in self.group_evals.items():
            if group_eval.likelihood is None:
                nll_by_group[group_name] = [None] * int(model_logits_batch.shape[0])
                continue
            values = group_eval.likelihood.loss_batch(model_logits_batch).detach().cpu().tolist()
            nll_by_group[group_name] = [float(value) for value in values]
        decoder_metrics = self._decoder_metrics()
        empirical_metrics = self._empirical_metrics_batch(model_logits_batch)
        results = []
        for candidate_idx in range(int(model_logits_batch.shape[0])):
            results.append(
                self._evaluate_one(
                    model_logits_batch[candidate_idx],
                    nll_by_group={group: values[candidate_idx] for group, values in nll_by_group.items()},
                    decoder_metrics=decoder_metrics,
                    empirical_metrics=empirical_metrics[candidate_idx],
                )
            )
        return results

    def _evaluate_one(
        self,
        model_logits: torch.Tensor,
        *,
        nll_by_group: dict[str, float | None] | None = None,
        decoder_metrics: dict[str, object] | None = None,
        empirical_metrics: dict[str, object] | None = None,
    ) -> dict[str, object]:
        result: dict[str, object] = {
            "requested_likelihood_backend": self.args.likelihood_backend,
            "resolved_likelihood_backend": resolve_likelihood_backend(model_logits, self.args.likelihood_backend),
            "exact_global_evaluated": False,
            "heldout_exact_nll": None,
            "oracle_exact_nll": None,
            "delta_nll_oracle": None,
            "delta_nll_oracle_source": "real_data_no_teacher",
            "num_evaluation_windows": int(self.num_evaluation_windows),
            "max_evaluation_window_bits": int(self.max_evaluation_window_bits),
            "window_nll_weighting": "equal_window",
            "window_nll_units": "nats_per_window",
            "window_empirical_entropy_source": "heldout_empirical_distribution",
            "window_excess_nll_definition": "model_window_nll_minus_empirical_window_entropy",
        }
        evidence_by_group: dict[str, dict[str, object]] = {}
        for group_name, group_eval in self.group_evals.items():
            if nll_by_group is not None:
                nll = nll_by_group[group_name]
            elif group_eval.likelihood is None:
                nll = None
            else:
                nll = float(group_eval.likelihood.loss(model_logits).detach().cpu())
            excess = None if nll is None or group_eval.entropy is None else float(nll - group_eval.entropy)
            evidence = {
                "num_windows": int(group_eval.num_windows),
                "mean_window_bits": float(group_eval.mean_window_bits),
                "nll": nll,
                "empirical_entropy": group_eval.entropy,
                "excess_nll": excess,
                "nll_units": "nats_per_window",
                "weighting": "equal_window",
            }
            evidence_by_group[group_name] = evidence
            result.update(_flat_window_evidence_fields(group_name, evidence))
        result["window_evidence_groups"] = evidence_by_group
        if empirical_metrics is None:
            result.update(empirical_detector_rate_metrics(self.graph, model_logits, self.observations))
            result.update(empirical_local_correlation_metrics(self.graph, model_logits, self.observations))
            result.update(logical_flip_calibration_metrics(self.graph, model_logits, self.observations))
        else:
            result.update(empirical_metrics)
        result.update(decoder_metrics if decoder_metrics is not None else self._decoder_metrics())
        return result

    def _decoder_metrics(self) -> dict[str, object]:
        if self.predicted_observables is None:
            return {
                "decoder_logical_prediction_available": False,
                "decoder_logical_prediction_error_rate": None,
            }
        return decoder_prediction_metrics(self.observations, self.predicted_observables, self.graph.num_detectors)

    def _empirical_metrics_batch(self, logits_batch: torch.Tensor) -> list[dict[str, object]]:
        detector_bits = tuple(range(self.graph.num_detectors))
        if detector_bits:
            detector_rates = _exact_observation_bit_rates_batch(self.graph, logits_batch, detector_bits)
            detector_empirical = self.observations[:, : self.graph.num_detectors].to(
                device=logits_batch.device,
                dtype=detector_rates.dtype,
            ).mean(dim=0)
            detector_mae = torch.mean(torch.abs(detector_rates - detector_empirical.unsqueeze(0)), dim=1)
        else:
            detector_mae = torch.zeros((logits_batch.shape[0],), dtype=logits_batch.dtype, device=logits_batch.device)

        pairs = tuple(local_detector_pairs(self.graph))
        if pairs:
            pair_rates = _exact_observation_pair_joint_rates_batch(self.graph, logits_batch, pairs)
            obs = self.observations.to(device=logits_batch.device, dtype=pair_rates.dtype)
            pair_empirical = torch.stack([obs[:, left] * obs[:, right] for left, right in pairs], dim=1).mean(dim=0)
            correlation_error = torch.mean(torch.abs(pair_rates - pair_empirical.unsqueeze(0)), dim=1)
        else:
            correlation_error = torch.zeros((logits_batch.shape[0],), dtype=logits_batch.dtype, device=logits_batch.device)

        if self.graph.num_observables == 0:
            logical_calibration = torch.zeros((logits_batch.shape[0],), dtype=logits_batch.dtype, device=logits_batch.device)
            logical_predicted = [[] for _ in range(int(logits_batch.shape[0]))]
            logical_empirical_list: list[float] = []
        else:
            logical_bits = tuple(range(self.graph.num_detectors, self.graph.B))
            logical_rates = _exact_observation_bit_rates_batch(self.graph, logits_batch, logical_bits)
            logical_empirical = self.observations[:, self.graph.num_detectors : self.graph.B].to(
                device=logits_batch.device,
                dtype=logical_rates.dtype,
            ).mean(dim=0)
            logical_calibration = torch.mean(torch.abs(logical_rates - logical_empirical.unsqueeze(0)), dim=1)
            logical_predicted = [[float(value) for value in row] for row in logical_rates.detach().cpu().tolist()]
            logical_empirical_list = [float(value) for value in logical_empirical.detach().cpu().tolist()]

        detector_mae_cpu = detector_mae.detach().cpu().tolist()
        correlation_error_cpu = correlation_error.detach().cpu().tolist()
        logical_calibration_cpu = logical_calibration.detach().cpu().tolist()
        return [
            {
                "detector_rate_mae": float(detector_mae_cpu[idx]),
                "local_correlation_error": float(correlation_error_cpu[idx]),
                "num_local_correlation_pairs": len(pairs),
                "logical_flip_rate_calibration": float(logical_calibration_cpu[idx]),
                "logical_flip_rate_predicted": logical_predicted[idx],
                "logical_flip_rate_empirical": logical_empirical_list,
            }
            for idx in range(int(logits_batch.shape[0]))
        ]


def _exact_observation_bit_rates_batch(
    graph,
    logits_batch: torch.Tensor,
    bits: tuple[int, ...],
) -> torch.Tensor:
    if not bits:
        return logits_batch.new_empty((logits_batch.shape[0], 0))
    parity_factors = 1 - 2 * torch.sigmoid(logits_batch)
    rates = []
    for bit in bits:
        parity_mean = _parity_mean_batch(parity_factors, graph.faults_by_observation_bit[int(bit)])
        rates.append((1 - parity_mean) / 2)
    return torch.stack(rates, dim=1)


def _exact_observation_pair_joint_rates_batch(
    graph,
    logits_batch: torch.Tensor,
    pairs: tuple[tuple[int, int], ...],
) -> torch.Tensor:
    if not pairs:
        return logits_batch.new_empty((logits_batch.shape[0], 0))
    parity_factors = 1 - 2 * torch.sigmoid(logits_batch)
    joint_rates = []
    for left, right in pairs:
        left_faults = set(graph.faults_by_observation_bit[int(left)])
        right_faults = set(graph.faults_by_observation_bit[int(right)])
        mean_left = _parity_mean_batch(parity_factors, tuple(sorted(left_faults)))
        mean_right = _parity_mean_batch(parity_factors, tuple(sorted(right_faults)))
        mean_xor = _parity_mean_batch(parity_factors, tuple(sorted(left_faults.symmetric_difference(right_faults))))
        joint_rates.append((1 - mean_left - mean_right + mean_xor) / 4)
    return torch.stack(joint_rates, dim=1)


def _parity_mean_batch(parity_factors: torch.Tensor, fault_ids) -> torch.Tensor:
    if not fault_ids:
        return torch.ones((parity_factors.shape[0],), dtype=parity_factors.dtype, device=parity_factors.device)
    idx = torch.tensor(tuple(int(value) for value in fault_ids), dtype=torch.long, device=parity_factors.device)
    return torch.prod(parity_factors.index_select(1, idx), dim=1)


def main(argv: list[str] | None = None) -> dict[str, object]:
    start = time.perf_counter()
    timings: dict[str, float] = {}
    candidate_timings: list[dict[str, object]] = []
    args = _parse_args(argv)
    _resolve_execution_mode(args)
    phase = time.perf_counter()
    dataset_root = args.dataset_root
    leaf = find_google_set1_leaf(
        dataset_root,
        sample_id=args.sample_id,
        patch_id=args.patch_id,
        basis=args.basis,
        rounds_label=args.rounds_label,
    )
    output_root = Path(args.output_root)
    g13_dir = output_root / "GDISC13b_real_local_inverse_audit"
    g15_dir = output_root / "GDISC15_real_local_mechanism_discovery"
    comparison_dir = output_root / "STIM_vs_Google_comparison"
    for directory in [g13_dir, g15_dir, comparison_dir]:
        directory.mkdir(parents=True, exist_ok=True)
    args.prepared_cache_dir = str(Path(args.prepared_cache_dir) if args.prepared_cache_dir else output_root / "prepared_cache")

    observations = load_google_observations(leaf)
    split = _train_heldout_split(observations.shape[0], args.train_shots, args.heldout_shots)
    train = observations[split["train_slice"]]
    heldout = observations[split["heldout_slice"]]
    predicted = load_google_predicted_observables(leaf, args.dem_source)
    heldout_predicted = None if predicted is None else predicted[split["heldout_slice"]]
    schedule_context = build_google_schedule_context(leaf, dem_source=args.dem_source, observations=observations)
    dem_data_cache: dict[str, object] = {}
    cache_events: list[dict[str, object]] = []
    graph, preprocessing_audit = _prepare_google_fault_graph(
        args,
        leaf,
        orbit_mode=args.orbit_mode,
        schedule_context=schedule_context,
        dem_data_cache=dem_data_cache,
        cache_events=cache_events,
    )
    train_window_config = _window_config(args)
    train_windows = WindowPlan.from_config(graph, train_window_config)
    eval_window_config = _eval_window_config(args, train_window_config)
    eval_windows = train_windows if train_window_config == eval_window_config else WindowPlan.from_config(graph, eval_window_config)
    train_objectives = _prepare_train_objectives(
        args,
        leaf,
        graph,
        train,
        train_windows,
        orbit_mode=args.orbit_mode,
        split=split,
        observation_modes={"detectors", "full"},
        cache_events=cache_events,
    )
    train_objective = train_objectives["full"]
    dmle_train_objective = train_objectives["detectors"]
    legacy_eval_cache = _prepare_eval_cache(
        args,
        leaf,
        graph,
        heldout,
        train_windows,
        orbit_mode=args.orbit_mode,
        role="gdisc_heldout_eval",
        slice_start=int(split["heldout_start"]),
        slice_end=int(split["heldout_end"]),
        cache_events=cache_events,
    )
    eval_cache = (
        legacy_eval_cache
        if train_windows is eval_windows
        else _prepare_eval_cache(
            args,
            leaf,
            graph,
            heldout,
            eval_windows,
            orbit_mode=args.orbit_mode,
            role=f"gdisc_heldout_eval_{args.eval_window_plan_mode}",
            slice_start=int(split["heldout_start"]),
            slice_end=int(split["heldout_end"]),
            cache_events=cache_events,
        )
    )
    prepared_evaluator = _prepare_fast_evaluator(args, graph, heldout, train_windows, legacy_eval_cache, heldout_predicted)
    eval_prepared_evaluator = (
        prepared_evaluator
        if train_windows is eval_windows
        else _prepare_fast_evaluator(args, graph, heldout, eval_windows, eval_cache, heldout_predicted)
    )
    timings["data_graph_window_cache_preparation"] = time.perf_counter() - phase

    dtype = torch.float64 if args.dtype == "float64" else torch.float32
    phase = time.perf_counter()
    local_fit = _fit_local(args, graph, train, train_objective=train_objective, dtype=dtype)
    timings["local_full_fit"] = time.perf_counter() - phase
    local_logits = local_fit["logits"]
    phase = time.perf_counter()
    local_metrics = _eval_logits(
        args,
        graph,
        local_logits,
        heldout,
        train_windows,
        legacy_eval_cache,
        heldout_predicted,
        prepared_evaluator=prepared_evaluator,
        eval_windows=eval_windows,
        structured_eval_cache=eval_cache,
        eval_prepared_evaluator=eval_prepared_evaluator,
    )
    timings["local_full_eval"] = time.perf_counter() - phase
    local_record = _model_record(
        "local_full",
        local_logits,
        local_metrics,
        parameter_count=graph.M,
        extra={"train_final_nll": local_fit["train_final_nll"]},
    )
    phase = time.perf_counter()
    dmle_fit = _fit_dmle_qec(args, graph, train, train_objective=dmle_train_objective, dtype=dtype)
    timings["dmle_qec_detector_fit"] = time.perf_counter() - phase
    phase = time.perf_counter()
    dmle_metrics = _eval_logits(
        args,
        graph,
        dmle_fit["logits"],
        heldout,
        train_windows,
        legacy_eval_cache,
        heldout_predicted,
        prepared_evaluator=prepared_evaluator,
        eval_windows=eval_windows,
        structured_eval_cache=eval_cache,
        eval_prepared_evaluator=eval_prepared_evaluator,
    )
    timings["dmle_qec_eval"] = time.perf_counter() - phase
    dmle_record = _model_record(
        "dmle_qec",
        dmle_fit["logits"],
        dmle_metrics,
        parameter_count=graph.M,
        extra={
            **baseline_metadata("dmle_qec"),
            "baseline_kind": "dmle_qec_style_detector_syndrome_independent_dem_mle",
            "train_observation_mode": "detectors",
            "train_final_nll": dmle_fit["train_final_nll"],
        },
    )
    upstream_dmle_record = None
    if bool(args.include_upstream_dmle):
        phase = time.perf_counter()
        upstream_dmle_fit = _fit_dmle_qec_upstream(args, leaf, graph, train, dtype=dtype)
        timings["dmle_qec_upstream_tensor_network_fit"] = time.perf_counter() - phase
        phase = time.perf_counter()
        upstream_dmle_metrics = _eval_logits(
            args,
            graph,
            upstream_dmle_fit["logits"],
            heldout,
            train_windows,
            legacy_eval_cache,
            heldout_predicted,
            prepared_evaluator=prepared_evaluator,
            eval_windows=eval_windows,
            structured_eval_cache=eval_cache,
            eval_prepared_evaluator=eval_prepared_evaluator,
        )
        timings["dmle_qec_upstream_eval"] = time.perf_counter() - phase
        upstream_dmle_record = _model_record(
            "dmle_qec_upstream",
            upstream_dmle_fit["logits"],
            upstream_dmle_metrics,
            parameter_count=graph.M,
            extra={
                **baseline_metadata("dmle_qec_upstream"),
                "baseline_kind": "upstream_dmle_qec_tensor_network_detector_syndrome_dem_mle",
                "train_observation_mode": "detectors",
                "train_final_nll": upstream_dmle_fit["train_final_nll"],
                "upstream_dmle_qec_audit": upstream_dmle_fit["audit"],
            },
        )
    global_logits = torch.full_like(local_logits, float(local_logits.mean().item()))
    phase = time.perf_counter()
    global_metrics = _eval_logits(
        args,
        graph,
        global_logits,
        heldout,
        train_windows,
        legacy_eval_cache,
        heldout_predicted,
        prepared_evaluator=prepared_evaluator,
        eval_windows=eval_windows,
        structured_eval_cache=eval_cache,
        eval_prepared_evaluator=eval_prepared_evaluator,
    )
    timings["global_shared_scalar_eval"] = time.perf_counter() - phase
    global_record = _model_record(
        "global_shared_scalar",
        global_logits,
        global_metrics,
        parameter_count=1,
        extra={"baseline_kind": "single_shared_fault_logit"},
    )

    phase = time.perf_counter()
    prior_records, prior_agreements = _reference_prior_records(
        args,
        leaf,
        graph,
        local_logits,
        heldout,
        train_windows,
        legacy_eval_cache,
        heldout_predicted,
        prepared_evaluator,
        eval_windows,
        eval_cache,
        eval_prepared_evaluator,
    )
    timings["prior_reference_eval"] = time.perf_counter() - phase
    phase = time.perf_counter()
    subsample = _fit_subsample_local_logits(args, graph, train, train_windows, dtype=dtype)
    timings["subsample_local_fits"] = time.perf_counter() - phase
    phase = time.perf_counter()
    stability = _local_inverse_stability(graph, local_logits, subsample)
    timings["stability_audit"] = time.perf_counter() - phase
    stability.update(
        {
            "predictiveness": _compact_predictiveness(local_metrics),
            "prior_agreement": prior_agreements,
            "nearby_sample_window_stability": "not_evaluated_in_smoke",
            "no_oracle_logits_available": True,
        }
    )

    phase = time.perf_counter()
    proxies = proxy_partitions(graph, basis=leaf.basis, rounds=leaf.rounds, dem_source=args.dem_source)
    candidates = _build_representation_candidates(args, graph, local_logits, subsample)
    timings["candidate_feature_construction"] = time.perf_counter() - phase
    g15_records = [local_record, dmle_record]
    if upstream_dmle_record is not None:
        g15_records.append(upstream_dmle_record)
    g15_records.extend([global_record, *prior_records])
    phase = time.perf_counter()
    candidate_specs = []
    for name, features, method in candidates:
        candidate_start = time.perf_counter()
        cluster = deterministic_kmeans(
            features,
            args.num_prototypes or graph.O,
            max_iter=int(args.kmeans_max_iter),
            check_convergence=bool(args.kmeans_check_convergence),
        )
        cluster_seconds = time.perf_counter() - candidate_start
        prototype = fit_cluster_mean_logits(cluster.labels, local_logits, num_clusters=args.num_prototypes or graph.O)
        candidate_specs.append(
            {
                "name": name,
                "features": features,
                "method": method,
                "cluster": cluster,
                "prototype": prototype,
                "cluster_seconds": cluster_seconds,
            }
        )
    timings["candidate_cluster_total"] = time.perf_counter() - phase
    eval_start = time.perf_counter()
    candidate_metrics = _eval_logits_batch(
        args,
        graph,
        [spec["prototype"].logits for spec in candidate_specs],
        heldout,
        train_windows,
        legacy_eval_cache,
        heldout_predicted,
        prepared_evaluator=prepared_evaluator,
        eval_windows=eval_windows,
        structured_eval_cache=eval_cache,
        eval_prepared_evaluator=eval_prepared_evaluator,
    )
    batch_eval_seconds = time.perf_counter() - eval_start
    timings["candidate_batch_eval"] = batch_eval_seconds
    eval_seconds_share = batch_eval_seconds / max(1, len(candidate_specs))
    for spec, metrics in zip(candidate_specs, candidate_metrics, strict=True):
        name = str(spec["name"])
        features = spec["features"]
        method = str(spec["method"])
        cluster = spec["cluster"]
        prototype = spec["prototype"]
        cluster_seconds = float(spec["cluster_seconds"])
        candidate_timings.append(
            {
                "candidate": name,
                "method": method,
                "cluster_seconds": cluster_seconds,
                "eval_seconds": eval_seconds_share,
                "eval_mode": "batched_candidate_logits",
                "batch_eval_total_seconds": batch_eval_seconds,
                "batch_eval_candidate_count": len(candidate_specs),
                "total_seconds": cluster_seconds + eval_seconds_share,
            }
        )
        record = _model_record(
            f"GDISC15_{name}",
            prototype.logits,
            metrics,
            parameter_count=prototype.active_prototypes,
            extra={
                "representation": name,
                "method": method,
                "active_prototypes": int(prototype.active_prototypes),
                "dead_prototypes": prototype.dead_prototypes,
                "assignment_entropy_normalized": _mass_entropy(cluster.cluster_masses),
                "cluster_masses": cluster.cluster_masses,
                "within_cluster_dispersion": cluster.within_cluster_dispersion,
                "silhouette_like": cluster.silhouette_like,
                "cluster_margin": _cluster_margin(features, cluster.labels, cluster.centers),
                "kmeans_iterations": int(cluster.iterations),
                "kmeans_max_iter": int(args.kmeans_max_iter),
                "kmeans_check_convergence": bool(args.kmeans_check_convergence),
                "proxy_partition_alignment": proxy_alignment(cluster.labels, proxies),
                "prototype_logits": prototype.prototype_logits,
                "labels": [int(value) for value in cluster.labels.tolist()],
                "no_true_omega_available": True,
                "proxy_ari_nmi_only": True,
            },
        )
        g15_records.append(record)
    timings["candidate_cluster_and_eval_total"] = time.perf_counter() - phase
    augment_model_comparison_metrics(g15_records, baseline_model="local_full")
    selected = _select_google_record(g15_records)
    result = {
        "run": {
            "name": "Google Stage 2B local inverse mechanism smoke",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "dataset_root": str(leaf.root),
            "leaf": {
                "sample_id": leaf.sample_id,
                "patch_id": leaf.patch_id,
                "basis": leaf.basis,
                "rounds_label": leaf.rounds_label,
            },
            "dem_source": args.dem_source,
            "orbit_mode": args.orbit_mode,
            "output_root": str(output_root),
            "device": args.device,
            "likelihood_backend": args.likelihood_backend,
            "cuda_kernel_variant": args.cuda_kernel_variant,
            "window_plan_mode": args.window_plan_mode,
            "eval_window_plan_mode": args.eval_window_plan_mode,
            "eval_max_window_bits": int(args.eval_max_window_bits),
            "eval_max_windows": int(args.eval_max_windows),
            "wall_seconds": time.perf_counter() - start,
            "wallclock_breakdown": timings,
            "claim_boundary": {
                **CLAIM_BOUNDARY,
                "google_discovery": (
                    "Google Stage 2B has no ground-truth hidden omega. It may report predictive utility, "
                    "stability, transfer, calibration, and explicitly labelled proxy ARI/NMI only."
                ),
            },
        },
        "train_heldout_split": _json_split(split),
        "graph_audit": {
            **graph.audit_dict(exact_likelihood_trainable=False, dem_fault_logit_claim=True, cptp_gksl_claim=False),
            **preprocessing_audit,
        },
        "window_audit": {
            **_window_plan_audit(graph, train_windows, preprocessing_mode=args.orbit_mode, role="train"),
            "train_window_audit": _window_plan_audit(graph, train_windows, preprocessing_mode=args.orbit_mode, role="train"),
            "eval_window_audit": _window_plan_audit(graph, eval_windows, preprocessing_mode=args.orbit_mode, role="eval"),
        },
        "schedule_context_audit": schedule_context.audit_dict(),
        "GDISC13b_real_local_inverse_audit": stability,
        "GDISC15_real_local_mechanism_discovery": {
            "question": "Do Google local inverse representations yield stable response modes with predictive utility?",
            "true_hidden_omega_available": False,
            "ari_nmi_ground_truth_recovery_claim_allowed": False,
            "proxy_partitions": sorted(proxies),
            "selection_rule": "heldout_excess_then_detector_mae_then_parameter_count",
            "selected_model": selected,
            "records": g15_records,
            "candidate_wallclock": candidate_timings,
        },
        "GDISC12_multi_context_shared_response": {
            "status": "not_run_by_this_smoke",
            "recommended_existing_runner": "scope_static.experiments.willow_data.static with cross-context extensions",
            "no_ari": True,
        },
        "prepared_cache_events": cache_events,
    }
    _write_outputs(g13_dir, g15_dir, comparison_dir, result)
    _print_summary(result)
    return result


def _prepare_fast_evaluator(
    args: argparse.Namespace,
    graph,
    heldout: torch.Tensor,
    windows: WindowPlan,
    eval_cache,
    heldout_predicted: torch.Tensor | None,
) -> _FastGoogleEvaluator | None:
    _window_caches, batch_cache = eval_cache
    device = torch.device(args.device)
    if batch_cache is None or device.type != "cuda" or args.likelihood_backend != "cuda_extension":
        return None

    all_windows = tuple(windows.windows)
    grouped = _window_evidence_groups(graph, all_windows)
    group_evals: dict[str, _WindowGroupEval] = {}
    for group_name, group in grouped.items():
        group_windows = list(group["windows"])
        group_indices = list(group["indices"])
        if not group_windows:
            group_evals[group_name] = _WindowGroupEval(
                name=group_name,
                likelihood=None,
                entropy=None,
                num_windows=0,
                mean_window_bits=0.0,
            )
            continue
        group_cache: WindowBatchNLLCache = (
            batch_cache
            if group_name == "combined"
            else subset_window_batch_nll_cache(batch_cache, tuple(int(index) for index in group_indices))
        )
        likelihood = ExactLocalWindowParityLikelihood(
            graph=graph,
            observations=heldout,
            observation_mode="full",
            aggregate_unique=True,
            requested_backend=args.likelihood_backend,
            windows=tuple(group_windows),
            cuda_kernel_variant=args.cuda_kernel_variant,
            spectral_min_abs_factor=float(args.spectral_min_abs_factor),
            spectral_memory_cap_bytes=_spectral_memory_cap_bytes(args),
            window_caches=(),
            window_batch_cache=group_cache,
        )
        entropy = empirical_window_entropy_from_batch_cache(batch_cache, tuple(int(index) for index in group_indices))
        group_evals[group_name] = _WindowGroupEval(
            name=group_name,
            likelihood=likelihood,
            entropy=entropy,
            num_windows=len(group_windows),
            mean_window_bits=float(sum(window.size for window in group_windows) / len(group_windows)),
        )
    return _FastGoogleEvaluator(
        args=args,
        graph=graph,
        observations=heldout,
        predicted_observables=heldout_predicted,
        group_evals=group_evals,
        num_evaluation_windows=len(all_windows),
        max_evaluation_window_bits=max((window.size for window in all_windows), default=0),
        device=device,
    )


def _fit_local(args: argparse.Namespace, graph, observations: torch.Tensor, *, train_objective, dtype: torch.dtype) -> dict[str, object]:
    torch.manual_seed(int(args.seed))
    field = LocalFaultLogitField.from_graph(graph, dtype=dtype)
    fit = fit_field(
        graph,
        field,
        observations,
        steps=int(args.steps),
        lr=float(args.lr),
        aggregate_unique=True,
        device=args.device,
        backend=args.likelihood_backend,
        cuda_kernel_variant=args.cuda_kernel_variant,
        spectral_min_abs_factor=float(args.spectral_min_abs_factor),
        spectral_memory_cap_bytes=_spectral_memory_cap_bytes(args),
        observation_mode="full",
        likelihood_objective="local_exact",
        windows=None,
        prepared_objective=train_objective,
        history_interval=max(1, int(args.steps)),
    )
    logits = fit["field"].realized_logits(graph).detach().to(dtype=torch.float64)
    history = list(fit.get("history", []))
    return {"logits": logits, "fit": fit, "train_final_nll": float(history[-1]) if history else None}


def _fit_dmle_qec(args: argparse.Namespace, graph, observations: torch.Tensor, *, train_objective, dtype: torch.dtype) -> dict[str, object]:
    seed = int(args.seed)
    torch.manual_seed(seed)
    field = make_field("dmle_qec", graph, dtype=dtype, seed=seed, model_options={"perturb_scale": 0.5})
    fit = fit_field(
        graph,
        field,
        observations,
        steps=int(args.steps),
        lr=float(args.lr),
        aggregate_unique=True,
        device=args.device,
        backend=args.likelihood_backend,
        cuda_kernel_variant=args.cuda_kernel_variant,
        spectral_min_abs_factor=float(args.spectral_min_abs_factor),
        spectral_memory_cap_bytes=_spectral_memory_cap_bytes(args),
        observation_mode="detectors",
        likelihood_objective="local_exact",
        windows=None,
        prepared_objective=train_objective,
        history_interval=max(1, int(args.steps)),
    )
    logits = fit["field"].realized_logits(graph).detach().to(dtype=torch.float64)
    history = list(fit.get("history", []))
    return {"logits": logits, "fit": fit, "train_final_nll": float(history[-1]) if history else None}


def _fit_dmle_qec_upstream(args: argparse.Namespace, leaf, graph, observations: torch.Tensor, *, dtype: torch.dtype) -> dict[str, object]:
    dem = _load_upstream_dmle_dem(args, leaf)
    config = UpstreamDMLEQECConfig(
        repo_path=Path(args.upstream_dmle_repo),
        device=str(args.device),
        dtype=dtype,
        seed=int(args.seed),
        epochs=int(args.upstream_dmle_epochs),
        lr=float(args.upstream_dmle_lr),
        batch_size=int(args.upstream_dmle_batch_size),
        minibatch=int(args.upstream_dmle_minibatch),
        path_file=None if not args.upstream_dmle_path_file else Path(args.upstream_dmle_path_file),
        path_search_max_time=int(args.upstream_dmle_path_search_max_time),
    )
    return fit_upstream_dmle_qec_tensor_network(
        dem=dem,
        graph=graph,
        observations=observations,
        config=config,
    )


def _load_upstream_dmle_dem(args: argparse.Namespace, leaf):
    import stim

    if args.dem_source in {"noisy_si1000", "circuit_noisy_si1000"}:
        return load_google_circuit(leaf, noisy=True).detector_error_model(decompose_errors=False)
    dem_data = load_google_dem_data(leaf, args.dem_source)
    return stim.DetectorErrorModel.from_file(str(dem_data.source_path))


def _fit_subsample_local_logits(args: argparse.Namespace, graph, train: torch.Tensor, windows: WindowPlan, *, dtype: torch.dtype) -> dict[str, torch.Tensor]:
    count = max(0, int(args.subsample_count))
    if count <= 0:
        return {}
    shots = int(train.shape[0])
    chunk = min(int(args.subsample_shots), max(1, shots // count))
    result = {}
    for idx in range(count):
        start = min(max(0, idx * chunk), max(0, shots - chunk))
        obs = train[start : start + chunk]
        objective = None
        fit = fit_field(
            graph,
            LocalFaultLogitField.from_graph(graph, dtype=dtype),
            obs,
            steps=int(args.subsample_steps),
            lr=float(args.lr),
            aggregate_unique=True,
            device=args.device,
            backend=args.likelihood_backend,
            cuda_kernel_variant=args.cuda_kernel_variant,
            spectral_min_abs_factor=float(args.spectral_min_abs_factor),
            spectral_memory_cap_bytes=_spectral_memory_cap_bytes(args),
            observation_mode="full",
            likelihood_objective="local_exact",
            windows=windows,
            prepared_objective=objective,
            history_interval=max(1, int(args.subsample_steps)),
        )
        result[f"subsample_{idx}"] = fit["field"].realized_logits(graph).detach().to(dtype=torch.float64)
    return result


def _eval_logits(
    args,
    graph,
    logits,
    heldout,
    windows,
    eval_cache,
    heldout_predicted,
    *,
    prepared_evaluator: "_FastGoogleEvaluator | None" = None,
    eval_windows: WindowPlan | None = None,
    structured_eval_cache=None,
    eval_prepared_evaluator: "_FastGoogleEvaluator | None" = None,
) -> dict[str, object]:
    eval_windows = windows if eval_windows is None else eval_windows
    structured_eval_cache = eval_cache if structured_eval_cache is None else structured_eval_cache
    if prepared_evaluator is not None:
        legacy_metrics = prepared_evaluator.evaluate(logits)
    else:
        legacy_metrics = evaluate_real_data_model(
            graph,
            torch.as_tensor(logits, dtype=torch.float64, device=torch.device(args.device)),
            heldout,
            aggregate_unique=True,
            backend=args.likelihood_backend,
            windows=list(windows.windows),
            window_caches=eval_cache[0],
            window_batch_cache=eval_cache[1],
            predicted_observables=heldout_predicted,
        )
    if _same_windows(windows, eval_windows):
        eval_metrics = legacy_metrics
    elif eval_prepared_evaluator is not None:
        eval_metrics = eval_prepared_evaluator.evaluate(logits)
    else:
        eval_metrics = evaluate_real_data_model(
            graph,
            torch.as_tensor(logits, dtype=torch.float64, device=torch.device(args.device)),
            heldout,
            aggregate_unique=True,
            backend=args.likelihood_backend,
            windows=list(eval_windows.windows),
            window_caches=structured_eval_cache[0],
            window_batch_cache=structured_eval_cache[1],
            predicted_observables=heldout_predicted,
        )
    return _with_eval_window_metrics(legacy_metrics, eval_metrics)


def _eval_logits_batch(
    args,
    graph,
    logits_list,
    heldout,
    windows,
    eval_cache,
    heldout_predicted,
    *,
    prepared_evaluator: "_FastGoogleEvaluator | None" = None,
    eval_windows: WindowPlan | None = None,
    structured_eval_cache=None,
    eval_prepared_evaluator: "_FastGoogleEvaluator | None" = None,
) -> list[dict[str, object]]:
    logits_values = list(logits_list)
    if not logits_values:
        return []
    eval_windows = windows if eval_windows is None else eval_windows
    structured_eval_cache = eval_cache if structured_eval_cache is None else structured_eval_cache
    if prepared_evaluator is not None:
        logits_batch = torch.stack(
            [torch.as_tensor(logits, dtype=torch.float64, device=prepared_evaluator.device) for logits in logits_values],
            dim=0,
        )
        legacy_results = prepared_evaluator.evaluate_batch(logits_batch)
    else:
        legacy_results = [
            evaluate_real_data_model(
                graph,
                torch.as_tensor(logits, dtype=torch.float64, device=torch.device(args.device)),
                heldout,
                aggregate_unique=True,
                backend=args.likelihood_backend,
                windows=list(windows.windows),
                window_caches=eval_cache[0],
                window_batch_cache=eval_cache[1],
                predicted_observables=heldout_predicted,
            )
            for logits in logits_values
        ]
    if _same_windows(windows, eval_windows):
        eval_results = legacy_results
    elif eval_prepared_evaluator is not None:
        logits_batch = torch.stack(
            [torch.as_tensor(logits, dtype=torch.float64, device=eval_prepared_evaluator.device) for logits in logits_values],
            dim=0,
        )
        eval_results = eval_prepared_evaluator.evaluate_batch(logits_batch)
    else:
        eval_results = [
            evaluate_real_data_model(
                graph,
                torch.as_tensor(logits, dtype=torch.float64, device=torch.device(args.device)),
                heldout,
                aggregate_unique=True,
                backend=args.likelihood_backend,
                windows=list(eval_windows.windows),
                window_caches=structured_eval_cache[0],
                window_batch_cache=structured_eval_cache[1],
                predicted_observables=heldout_predicted,
            )
            for logits in logits_values
        ]
    return [_with_eval_window_metrics(legacy, eval_) for legacy, eval_ in zip(legacy_results, eval_results, strict=True)]


def _reference_prior_records(
    args,
    leaf,
    graph,
    local_logits,
    heldout,
    windows,
    eval_cache,
    heldout_predicted,
    prepared_evaluator,
    eval_windows,
    structured_eval_cache,
    eval_prepared_evaluator,
):
    records = []
    agreements = {}
    base_prior = None
    if graph.effective_probabilities is not None:
        base_prior = probability_to_logit(graph.effective_probabilities)
        metrics = _eval_logits(
            args,
            graph,
            base_prior,
            heldout,
            windows,
            eval_cache,
            heldout_predicted,
            prepared_evaluator=prepared_evaluator,
            eval_windows=eval_windows,
            structured_eval_cache=structured_eval_cache,
            eval_prepared_evaluator=eval_prepared_evaluator,
        )
        records.append(_model_record("SI1000_prior_reference" if "si1000" in args.dem_source else f"{args.dem_source}_prior_reference", base_prior, metrics, parameter_count=0))
    agreements[args.dem_source] = dem_prior_agreement(local_logits, base_prior, label=args.dem_source)
    for source in [item.strip() for item in str(args.reference_dem_sources).split(",") if item.strip()]:
        if source == args.dem_source:
            continue
        try:
            dem_data = load_google_dem_data(leaf, source)
            ref_graph, _audit = build_google_fault_graph(
                leaf,
                dem_source=source,
                orbit_mode=args.orbit_mode,
                residual_rank=int(args.residual_rank),
                dem_data=dem_data,
            )
            if ref_graph.A.shape != graph.A.shape or not torch.equal(ref_graph.A, graph.A):
                agreements[source] = {"reference": source, "available": False, "reason": "dem_parity_map_mismatch"}
                continue
            prior = None if ref_graph.effective_probabilities is None else probability_to_logit(ref_graph.effective_probabilities)
            agreements[source] = dem_prior_agreement(local_logits, prior, label=source)
            if prior is not None:
                metrics = _eval_logits(
                    args,
                    graph,
                    prior,
                    heldout,
                    windows,
                    eval_cache,
                    heldout_predicted,
                    prepared_evaluator=prepared_evaluator,
                    eval_windows=eval_windows,
                    structured_eval_cache=structured_eval_cache,
                    eval_prepared_evaluator=eval_prepared_evaluator,
                )
                records.append(_model_record(f"{source}_prior_reference", prior, metrics, parameter_count=0))
        except Exception as exc:
            agreements[source] = {"reference": source, "available": False, "reason": str(exc)}
    return records, agreements


def _local_inverse_stability(graph, local_logits: torch.Tensor, subsample: dict[str, torch.Tensor]) -> dict[str, object]:
    columns = [local_logits, *subsample.values()]
    labels = [deterministic_kmeans(column.unsqueeze(1), max(1, graph.O), max_iter=32, check_convergence=False).labels for column in columns]
    matrix = torch.stack(columns, dim=1)
    result = pairwise_logit_stability(matrix, labels)
    result.update(
        {
            "question": "Do local inverse logits on Google data contain stable reusable structure or mostly window-specific noise?",
            "num_subsamples": len(subsample),
            "subsample_names": list(subsample),
        }
    )
    return result


def _build_representation_candidates(args, graph, local_logits: torch.Tensor, subsample: dict[str, torch.Tensor]):
    matrix = torch.stack([local_logits, *subsample.values()], dim=1)
    structural = structural_signature(graph, device=local_logits.device)
    candidates = [
        ("local_logit", local_logits.unsqueeze(1), "deterministic_kmeans"),
        ("local_logit_probability", local_probability_features(local_logits.unsqueeze(1)), "deterministic_kmeans"),
        ("multi_subsample_local_logit", matrix, "deterministic_kmeans"),
        ("structural_plus_local_logit", combined_signature(structural, local_logits.unsqueeze(1)), "deterministic_kmeans"),
    ]
    smoothed = graph_smooth_features(graph, local_logits.unsqueeze(1), strength=float(args.graph_smoothing_strength), steps=int(args.graph_smoothing_steps))
    candidates.append(("graph_smoothed_local_logit", smoothed, "graph_smoothing_kmeans"))
    candidates.append(("structural_plus_graph_smoothed", combined_signature(structural, smoothed), "graph_smoothing_kmeans"))
    for rank in [int(value) for value in str(args.pca_ranks).split(",") if str(value).strip()]:
        candidates.append((f"pca_scores_rank{rank}", pca_scores(matrix, rank), "pca_scores_kmeans"))
        candidates.append((f"pca_denoised_rank{rank}", pca_denoised_features(matrix, rank), "pca_denoised_kmeans"))
    k = int(args.num_prototypes or graph.O)
    candidates.append(("spectral_similarity_local", spectral_similarity_embedding(matrix, k), "spectral_similarity_kmeans"))
    codes = nmf_codes(matrix, k, seed=int(args.seed), steps=int(args.nmf_steps))
    candidates.append(("nmf_codes", codes, "nmf_code_kmeans"))
    candidates.append(("nmf_overlap_top2", overlapping_topk_codes(codes, topk=2), "overlapping_nmf_code_kmeans"))
    for rank in [int(value) for value in str(args.random_control_ranks).split(",") if str(value).strip()]:
        for seed in [int(value) for value in str(args.random_control_seeds).split(",") if str(value).strip()]:
            device = matrix.device
            generator = torch.Generator(device=device)
            generator.manual_seed(int(seed))
            features = torch.randn((graph.M, max(1, int(rank))), generator=generator, dtype=torch.float64, device=device)
            candidates.append((f"random_low_rank{rank}_seed{seed}", features, "random_low_rank_control"))
    return candidates


def _model_record(name: str, logits: torch.Tensor, metrics: dict[str, object], *, parameter_count: int, extra: dict[str, object] | None = None) -> dict[str, object]:
    record = {
        "model": name,
        "base_model": name,
        "parameter_count": int(parameter_count),
        "google_true_hidden_partition_available": False,
        "partition_recovery_claim_allowed": False,
    }
    record.update(metrics)
    record.update(extra or {})
    return record


def _select_google_record(records: list[dict[str, object]]) -> dict[str, object]:
    candidates = [record for record in records if record["model"].startswith("GDISC15_")]
    if not candidates:
        candidates = records
    best = min(
        candidates,
        key=lambda record: (
            _none_high(record.get(GOOGLE_PRIMARY_METRIC)),
            _none_high(record.get("detector_rate_mae")),
            int(record.get("parameter_count", 10**9)),
        ),
    )
    return _compact_record(best)


def _compact_predictiveness(metrics: dict[str, object]) -> dict[str, object]:
    keys = [
        "heldout_local_window_nll",
        "heldout_local_window_excess_nll",
        "heldout_eval_window_nll",
        "heldout_eval_window_excess_nll",
        "heldout_detector_window_excess_nll",
        "heldout_logical_window_excess_nll",
        "heldout_eval_detector_window_excess_nll",
        "heldout_eval_logical_window_excess_nll",
        "detector_rate_mae",
        "local_correlation_error",
        "logical_flip_rate_calibration",
        "decoder_logical_prediction_error_rate",
    ]
    return {key: metrics.get(key) for key in keys}


def _compact_record(record: dict[str, object]) -> dict[str, object]:
    keys = [
        "model",
        "parameter_count",
        "heldout_eval_window_excess_nll",
        "heldout_local_window_excess_nll",
        "heldout_detector_window_excess_nll",
        "heldout_logical_window_excess_nll",
        "heldout_eval_detector_window_excess_nll",
        "heldout_eval_logical_window_excess_nll",
        "detector_rate_mae",
        "local_correlation_error",
        "logical_flip_rate_calibration",
        "decoder_logical_prediction_error_rate",
        "compression_ratio",
    ]
    return {key: record.get(key) for key in keys}


def _cluster_margin(features: torch.Tensor, labels: torch.Tensor, centers: torch.Tensor) -> float:
    from scope_static.identifiability import standardize_features

    x = standardize_features(features)
    centers = centers.to(device=x.device, dtype=x.dtype)
    labels = labels.to(device=x.device, dtype=torch.long)
    row_ids = torch.arange(x.shape[0], device=x.device)
    distances = torch.cdist(x, centers, p=2)
    own = distances[row_ids, labels]
    masked = distances.clone()
    masked[row_ids, labels] = float("inf")
    other = torch.min(masked, dim=1).values
    margin = other - own
    finite = torch.isfinite(margin)
    return float(margin[finite].mean().item()) if bool(finite.any()) else 0.0


def _mass_entropy(masses: list[int]) -> float:
    total = sum(int(value) for value in masses)
    if total <= 0 or len(masses) <= 1:
        return 0.0
    entropy = 0.0
    for value in masses:
        if int(value) <= 0:
            continue
        p = int(value) / total
        entropy -= p * torch.log(torch.tensor(p)).item()
    return float(entropy / torch.log(torch.tensor(float(len(masses)))).item())


def _none_high(value: object) -> float:
    return float(value) if value is not None else float("inf")


def _json_split(split: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in split.items() if not isinstance(value, slice)}


def _write_outputs(g13_dir: Path, g15_dir: Path, comparison_dir: Path, result: dict[str, object]) -> None:
    g13 = {
        "run": result["run"],
        "train_heldout_split": result["train_heldout_split"],
        "GDISC13b_real_local_inverse_audit": result["GDISC13b_real_local_inverse_audit"],
    }
    g15 = {
        "run": result["run"],
        "train_heldout_split": result["train_heldout_split"],
        "graph_audit": result["graph_audit"],
        "window_audit": result["window_audit"],
        "GDISC15_real_local_mechanism_discovery": result["GDISC15_real_local_mechanism_discovery"],
    }
    (g13_dir / "metrics.json").write_text(json.dumps(_jsonable(g13), indent=2, sort_keys=True) + "\n")
    (g15_dir / "metrics.json").write_text(json.dumps(_jsonable(g15), indent=2, sort_keys=True) + "\n")
    (g13_dir / "summary.md").write_text(_g13_summary(g13))
    (g15_dir / "summary.md").write_text(_g15_summary(g15))
    (comparison_dir / "summary.md").write_text(_comparison_summary(result))


def _g13_summary(result: dict[str, object]) -> str:
    audit = result["GDISC13b_real_local_inverse_audit"]
    pred = audit["predictiveness"]
    return "\n".join(
        [
            "# GDISC13b Real Local Inverse Audit",
            "",
            f"- Mean pairwise logit corr: `{_fmt_float(audit.get('mean_pairwise_logit_corr'))}`",
            f"- Mean pairwise cluster NMI: `{_fmt_float(audit.get('mean_pairwise_cluster_nmi'))}`",
            f"- Heldout excess NLL: `{_fmt_float(pred.get('heldout_local_window_excess_nll'))}`",
            f"- Detector-rate MAE: `{_fmt_float(pred.get('detector_rate_mae'))}`",
            f"- Local-correlation error: `{_fmt_float(pred.get('local_correlation_error'))}`",
            "",
        ]
    )


def _g15_summary(result: dict[str, object]) -> str:
    payload = result["GDISC15_real_local_mechanism_discovery"]
    rows = [_compact_record(record) for record in payload["records"]]
    lines = [
        "# GDISC15 Real Local Mechanism Discovery",
        "",
        f"- Selection rule: `{payload['selection_rule']}`",
        f"- Selected model: `{payload['selected_model'].get('model')}`",
        f"- True omega available: `{str(payload['true_hidden_omega_available']).lower()}`",
        "",
        "| model | params | ex_nll | det_ex | log_ex | det_mae | corr_err | log_cal |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in sorted(rows, key=lambda item: _none_high(item.get(GOOGLE_PRIMARY_METRIC)))[:12]:
        lines.append(
            f"| {row.get('model')} | {row.get('parameter_count')} | {_fmt_float(row.get(GOOGLE_PRIMARY_METRIC))} | "
            f"{_fmt_float(row.get('heldout_detector_window_excess_nll'))} | {_fmt_float(row.get('heldout_logical_window_excess_nll'))} | "
            f"{_fmt_float(row.get('detector_rate_mae'))} | {_fmt_float(row.get('local_correlation_error'))} | "
            f"{_fmt_float(row.get('logical_flip_rate_calibration'))} |"
        )
    lines.append("")
    return "\n".join(lines)


def _comparison_summary(result: dict[str, object]) -> str:
    selected = result["GDISC15_real_local_mechanism_discovery"]["selected_model"]
    g13 = result["GDISC13b_real_local_inverse_audit"]
    return "\n".join(
        [
            "# STIM vs Google Stage 2 Comparison",
            "",
            "| Experiment | Synthetic/Stim result | Google result | Interpretation |",
            "| --- | --- | --- | --- |",
            "| DISC12 | weak recovery gain; high contrast nonmonotonic | not run in this smoke | shared real-context response remains future work |",
            (
                "| DISC13b | local logits contain substantial target signal | "
                f"mean logit corr {_fmt_float(g13.get('mean_pairwise_logit_corr'))}, "
                f"cluster NMI {_fmt_float(g13.get('mean_pairwise_cluster_nmi'))} | "
                "tests stability without oracle logits |"
            ),
            (
                "| DISC15 | evaluator-best local inverse representation nearly strong | "
                f"selected {selected.get('model')} ex_nll {_fmt_float(selected.get(GOOGLE_PRIMARY_METRIC))} | "
                "real-data claim is predictive utility, not true omega recovery |"
            ),
            "",
        ]
    )


def _print_summary(result: dict[str, object]) -> None:
    g13 = result["GDISC13b_real_local_inverse_audit"]
    selected = result["GDISC15_real_local_mechanism_discovery"]["selected_model"]
    print("Google Stage 2B local inverse mechanism smoke complete")
    print("outputs:")
    output_root = Path(str(result["run"].get("output_root", "outputs/google_static")))
    print(f"  {output_root / 'GDISC13b_real_local_inverse_audit' / 'metrics.json'}")
    print(f"  {output_root / 'GDISC15_real_local_mechanism_discovery' / 'metrics.json'}")
    print(f"  {output_root / 'STIM_vs_Google_comparison' / 'summary.md'}")
    print(
        "GDISC13b: "
        f"logit_corr={_fmt_float(g13.get('mean_pairwise_logit_corr'))} "
        f"cluster_nmi={_fmt_float(g13.get('mean_pairwise_cluster_nmi'))}"
    )
    print(
        "GDISC15 selected: "
        f"{selected.get('model')} ex_nll={_fmt_float(selected.get(GOOGLE_PRIMARY_METRIC))} "
        f"det_mae={_fmt_float(selected.get('detector_rate_mae'))} params={selected.get('parameter_count')}"
    )


def _jsonable(value):
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    return value


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Google Stage 2B local inverse mechanism smoke.")
    parser.add_argument("--dataset-root", default="/home/cx/Document/google_72Q_surface_code_d3_d5_set1")
    parser.add_argument("--sample-id", default="sample_00")
    parser.add_argument("--patch-id", default="d3_at_q5_5")
    parser.add_argument("--basis", default="X")
    parser.add_argument("--rounds-label", default="r13")
    parser.add_argument("--dem-source", default="decoder_si1000")
    parser.add_argument("--reference-dem-sources", default="decoder_si1000,decoder_rl")
    parser.add_argument("--orbit-mode", default="fault_graph_heuristic")
    parser.add_argument("--train-shots", type=int, default=8000)
    parser.add_argument("--heldout-shots", type=int, default=2000)
    parser.add_argument("--steps", type=int, default=80)
    parser.add_argument("--subsample-count", type=int, default=2)
    parser.add_argument("--subsample-shots", type=int, default=3000)
    parser.add_argument("--subsample-steps", type=int, default=60)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--residual-rank", type=int, default=2)
    parser.add_argument("--num-prototypes", type=int, default=0)
    parser.add_argument("--pca-ranks", default="1,2,3")
    parser.add_argument("--graph-smoothing-strength", type=float, default=0.55)
    parser.add_argument("--graph-smoothing-steps", type=int, default=2)
    parser.add_argument("--nmf-steps", type=int, default=120)
    parser.add_argument("--kmeans-max-iter", type=int, default=32)
    parser.add_argument("--kmeans-check-convergence", action="store_true")
    parser.add_argument("--include-upstream-dmle", action="store_true")
    parser.add_argument("--upstream-dmle-repo", default="/tmp/DMLE-QEC")
    parser.add_argument("--upstream-dmle-epochs", type=int, default=20)
    parser.add_argument("--upstream-dmle-lr", type=float, default=0.01)
    parser.add_argument("--upstream-dmle-batch-size", type=int, default=10000)
    parser.add_argument("--upstream-dmle-minibatch", type=int, default=1000)
    parser.add_argument("--upstream-dmle-path-file", default="")
    parser.add_argument("--upstream-dmle-path-search-max-time", type=int, default=0)
    parser.add_argument("--random-control-ranks", default="1,2,3,5,8")
    parser.add_argument("--random-control-seeds", default="0")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--dtype", choices=["float64", "float32"], default="float64")
    parser.add_argument("--likelihood-backend", choices=["auto", "pytorch", "cuda_extension"], default="auto")
    parser.add_argument("--cuda-kernel-variant", choices=["dp", "spectral_shadow", "spectral", "auto"], default="dp")
    parser.add_argument("--spectral-min-abs-factor", type=float, default=1e-6)
    parser.add_argument("--spectral-memory-cap-mib", type=int, default=1024)
    parser.add_argument("--native-gpu", action="store_true")
    parser.add_argument("--max-window-bits", type=int, default=8)
    parser.add_argument("--max-windows", type=int, default=128)
    parser.add_argument("--window-plan-mode", choices=["logical_aware", "detector_local"], default="logical_aware")
    parser.add_argument(
        "--eval-window-plan-mode",
        choices=["same_as_train", "structured_higher_order"],
        default="same_as_train",
    )
    parser.add_argument("--eval-max-window-bits", type=int, default=6)
    parser.add_argument("--eval-max-windows", type=int, default=256)
    parser.add_argument("--eval-radius", type=float, default=1.0)
    parser.add_argument("--eval-template-window-budget", type=int, default=32)
    parser.add_argument("--eval-orbit-window-budget", type=int, default=64)
    parser.add_argument("--detector-pair-window-budget", type=int, default=64)
    parser.add_argument("--logical-detector-pair-window-budget", type=int, default=64)
    parser.add_argument("--output-root", default="outputs/google_static")
    parser.add_argument("--prepared-cache-dir", default=None)
    parser.add_argument("--disable-prepared-cache", action="store_true")
    args = parser.parse_args(argv)
    if args.num_prototypes <= 0:
        args.num_prototypes = None
    return args


if __name__ == "__main__":
    main()
