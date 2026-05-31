from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time

import numpy as np
import torch

from scope_static.dem.fields import LocalFaultLogitField
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
from scope_static.dem.metrics import augment_model_comparison_metrics, evaluate_real_data_model
from scope_static.dem.training import fit_field
from scope_static.dem.windows import WindowPlan, window_coverage_audit_dict

from .static import (
    _fmt_float,
    _prepare_eval_cache,
    _prepare_google_fault_graph,
    _prepare_train_objectives,
    _print_table,
    _resolve_execution_mode,
    _spectral_memory_cap_bytes,
    _train_heldout_split,
    _window_config,
)


def main(argv: list[str] | None = None) -> dict[str, object]:
    start = time.perf_counter()
    args = _parse_args(argv)
    _resolve_execution_mode(args)
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
    windows = WindowPlan.from_config(graph, _window_config(args))
    train_objective = _prepare_train_objectives(
        args,
        leaf,
        graph,
        train,
        windows,
        orbit_mode=args.orbit_mode,
        split=split,
        observation_modes={"full"},
        cache_events=cache_events,
    )["full"]
    eval_cache = _prepare_eval_cache(
        args,
        leaf,
        graph,
        heldout,
        windows,
        orbit_mode=args.orbit_mode,
        role="gdisc_heldout_eval",
        slice_start=int(split["heldout_start"]),
        slice_end=int(split["heldout_end"]),
        cache_events=cache_events,
    )

    dtype = torch.float64 if args.dtype == "float64" else torch.float32
    local_fit = _fit_local(args, graph, train, train_objective=train_objective, dtype=dtype)
    local_logits = local_fit["logits"]
    local_metrics = _eval_logits(args, graph, local_logits, heldout, windows, eval_cache, heldout_predicted)
    local_record = _model_record(
        "local_full",
        local_logits,
        local_metrics,
        parameter_count=graph.M,
        extra={"train_final_nll": local_fit["train_final_nll"]},
    )
    global_logits = torch.full_like(local_logits, float(local_logits.mean().item()))
    global_metrics = _eval_logits(args, graph, global_logits, heldout, windows, eval_cache, heldout_predicted)
    global_record = _model_record(
        "global_shared_scalar",
        global_logits,
        global_metrics,
        parameter_count=1,
        extra={"baseline_kind": "single_shared_fault_logit"},
    )

    prior_records, prior_agreements = _reference_prior_records(
        args,
        leaf,
        graph,
        local_logits,
        heldout,
        windows,
        eval_cache,
        heldout_predicted,
    )
    subsample = _fit_subsample_local_logits(args, graph, train, windows, dtype=dtype)
    stability = _local_inverse_stability(graph, local_logits, subsample)
    stability.update(
        {
            "predictiveness": _compact_predictiveness(local_metrics),
            "prior_agreement": prior_agreements,
            "nearby_sample_window_stability": "not_evaluated_in_smoke",
            "no_oracle_logits_available": True,
        }
    )

    proxies = proxy_partitions(graph, basis=leaf.basis, rounds=leaf.rounds, dem_source=args.dem_source)
    candidates = _build_representation_candidates(args, graph, local_logits, subsample)
    g15_records = [local_record, global_record, *prior_records]
    cluster_records = []
    for name, features, method in candidates:
        cluster = deterministic_kmeans(features, args.num_prototypes or graph.O)
        prototype = fit_cluster_mean_logits(cluster.labels, local_logits, num_clusters=args.num_prototypes or graph.O)
        metrics = _eval_logits(args, graph, prototype.logits, heldout, windows, eval_cache, heldout_predicted)
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
                "proxy_partition_alignment": proxy_alignment(cluster.labels, proxies),
                "prototype_logits": prototype.prototype_logits,
                "labels": [int(value) for value in cluster.labels.tolist()],
                "no_true_omega_available": True,
                "proxy_ari_nmi_only": True,
            },
        )
        cluster_records.append(record)
        g15_records.append(record)
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
            "wall_seconds": time.perf_counter() - start,
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
            **window_coverage_audit_dict(graph, list(windows.windows)),
            **windows.audit_dict(),
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
        },
        "GDISC12_multi_context_shared_response": {
            "status": "not_run_by_this_smoke",
            "recommended_existing_runner": "scope_static.experiments.google.static with cross-context extensions",
            "no_ari": True,
        },
        "prepared_cache_events": cache_events,
    }
    _write_outputs(g13_dir, g15_dir, comparison_dir, result)
    _print_summary(result)
    return result


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
    )
    logits = fit["field"].realized_logits(graph).detach().cpu().to(dtype=torch.float64)
    history = list(fit.get("history", []))
    return {"logits": logits, "fit": fit, "train_final_nll": float(history[-1]) if history else None}


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
        )
        result[f"subsample_{idx}"] = fit["field"].realized_logits(graph).detach().cpu().to(dtype=torch.float64)
    return result


def _eval_logits(args, graph, logits, heldout, windows, eval_cache, heldout_predicted) -> dict[str, object]:
    return evaluate_real_data_model(
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


def _reference_prior_records(args, leaf, graph, local_logits, heldout, windows, eval_cache, heldout_predicted):
    records = []
    agreements = {}
    base_prior = None
    if graph.effective_probabilities is not None:
        base_prior = probability_to_logit(graph.effective_probabilities)
        metrics = _eval_logits(args, graph, base_prior, heldout, windows, eval_cache, heldout_predicted)
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
                metrics = _eval_logits(args, graph, prior, heldout, windows, eval_cache, heldout_predicted)
                records.append(_model_record(f"{source}_prior_reference", prior, metrics, parameter_count=0))
        except Exception as exc:
            agreements[source] = {"reference": source, "available": False, "reason": str(exc)}
    return records, agreements


def _local_inverse_stability(graph, local_logits: torch.Tensor, subsample: dict[str, torch.Tensor]) -> dict[str, object]:
    columns = [local_logits, *subsample.values()]
    labels = [deterministic_kmeans(column.unsqueeze(1), max(1, graph.O)).labels for column in columns]
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
    structural = structural_signature(graph)
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
            generator = torch.Generator(device="cpu")
            generator.manual_seed(int(seed))
            features = torch.randn((graph.M, max(1, int(rank))), generator=generator, dtype=torch.float64)
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
            _none_high(record.get("heldout_local_window_excess_nll")),
            _none_high(record.get("detector_rate_mae")),
            int(record.get("parameter_count", 10**9)),
        ),
    )
    return _compact_record(best)


def _compact_predictiveness(metrics: dict[str, object]) -> dict[str, object]:
    keys = [
        "heldout_local_window_nll",
        "heldout_local_window_excess_nll",
        "heldout_detector_window_excess_nll",
        "heldout_logical_window_excess_nll",
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
        "heldout_local_window_excess_nll",
        "heldout_detector_window_excess_nll",
        "heldout_logical_window_excess_nll",
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
    distances = torch.cdist(x, centers, p=2)
    labels = labels.to(dtype=torch.long)
    own = distances[torch.arange(x.shape[0]), labels]
    masked = distances.clone()
    masked[torch.arange(x.shape[0]), labels] = float("inf")
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
    for row in sorted(rows, key=lambda item: _none_high(item.get("heldout_local_window_excess_nll")))[:12]:
        lines.append(
            f"| {row.get('model')} | {row.get('parameter_count')} | {_fmt_float(row.get('heldout_local_window_excess_nll'))} | "
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
                f"selected {selected.get('model')} ex_nll {_fmt_float(selected.get('heldout_local_window_excess_nll'))} | "
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
        f"{selected.get('model')} ex_nll={_fmt_float(selected.get('heldout_local_window_excess_nll'))} "
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
    parser.add_argument("--allow-cpu-fallback", action="store_true")
    parser.add_argument("--max-window-bits", type=int, default=8)
    parser.add_argument("--max-windows", type=int, default=128)
    parser.add_argument("--window-plan-mode", choices=["logical_aware", "detector_local"], default="logical_aware")
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
