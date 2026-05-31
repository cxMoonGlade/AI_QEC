from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import torch
import yaml

from scope_static.dem.discovery import (
    add_known_orbit_deltas,
    discovery_parameter_audit,
    field_discovery_metrics,
)
from scope_static.dem.evidence import EvidenceConfig, EvidenceContext, build_evidence_record, evaluate_evidence
from scope_static.experiments.static.plan import ExperimentPlan
from scope_static.dem.fields import make_field
from scope_static.dem.hardening import (
    apply_assignment_initialization,
    local_logit_assignment_initialization,
    random_balanced_assignment_initialization,
)
from scope_static.dem.metrics import normalized_mutual_info
from scope_static.dem.objectives import build_likelihood_objective
from scope_static.dem.stim_dem import sample_observations_from_logits
from scope_static.dem.teacher_logits import make_teacher_logits
from scope_static.dem.training import fit_field
from scope_static.dem.windows import WindowPlan


DEFAULT_CONDITIONS = [
    {
        "id": "A",
        "name": "free_random_init",
        "assignment_mode": "soft",
        "initializer": "random",
    },
    {
        "id": "B",
        "name": "free_local_logit_init",
        "assignment_mode": "soft",
        "initializer": "local_logit",
    },
    {
        "id": "C",
        "name": "hard_st_random_init",
        "assignment_mode": "straight_through",
        "initializer": "random_balanced",
    },
    {
        "id": "D",
        "name": "hard_st_local_logit_init",
        "assignment_mode": "straight_through",
        "initializer": "local_logit",
    },
    {
        "id": "E",
        "name": "hard_st_local_logit_init_entropy_anneal",
        "assignment_mode": "straight_through",
        "initializer": "local_logit",
        "entropy_annealing": {"enabled": True, "start": 0.0, "end": 0.04},
    },
    {
        "id": "F",
        "name": "hard_st_local_logit_init_entropy_balance",
        "assignment_mode": "straight_through",
        "initializer": "local_logit",
        "entropy_annealing": {"enabled": True, "start": 0.0, "end": 0.04},
        "assignment_balance_weight": 0.5,
    },
    {
        "id": "G",
        "name": "hard_st_local_logit_init_entropy_balance_separation",
        "assignment_mode": "straight_through",
        "initializer": "local_logit",
        "entropy_annealing": {"enabled": True, "start": 0.0, "end": 0.04},
        "assignment_balance_weight": 0.5,
        "prototype_separation_weight": 0.05,
        "prototype_separation_margin": 0.35,
    },
]


def run_hardening_experiment(
    config_path: str | Path,
    *,
    output_dir: str | Path | None = None,
) -> dict[str, object]:
    plan = ExperimentPlan.from_path(config_path, output_dir=output_dir)
    hardening_cfg = dict(plan.config.get("hardening", {}))
    output = plan.output_dir
    output.mkdir(parents=True, exist_ok=True)
    (output / "config_snapshot.yaml").write_text(yaml.safe_dump(plan.config, sort_keys=False))

    graph = plan.build_graph(plan.teacher_residual_rank)
    windows = WindowPlan.from_config(graph, plan.windows_cfg)
    evidence_config = EvidenceConfig(
        aggregate_unique=plan.aggregate_unique,
        backend=plan.likelihood_backend,
        global_exact_max_bits=plan.global_exact_max_bits,
    )
    conditions = _condition_specs(hardening_cfg)
    restarts = int(hardening_cfg.get("restarts", 4))
    validation_shots = int(hardening_cfg.get("validation_shots", plan.heldout_shots))
    active_mass_threshold = float(hardening_cfg.get("active_mass_threshold", 1.0))
    restart_poor_ari_threshold = float(hardening_cfg.get("restart_poor_ari_threshold", 0.5))
    selection_cfg = dict(hardening_cfg.get("selection", {}))
    prior_context = _load_prior_context(hardening_cfg)

    records: list[dict[str, object]] = []
    restart_records: list[dict[str, object]] = []
    num_model_fits_executed = 0

    for seed in plan.seeds:
        for teacher_case in plan.teacher_cases:
            teacher_logits = make_teacher_logits(
                graph,
                mode=teacher_case.mode,
                epsilon_break=teacher_case.epsilon_break,
                seed=int(seed),
                dtype=plan.dtype,
            )
            heldout = sample_observations_from_logits(
                graph,
                teacher_logits,
                shots=plan.heldout_shots,
                seed=int(seed) + 10_000,
            )
            validation = sample_observations_from_logits(
                graph,
                teacher_logits,
                shots=validation_shots,
                seed=int(seed) + 20_000,
            )
            for shots in plan.shot_budgets:
                train_obs = sample_observations_from_logits(
                    graph,
                    teacher_logits,
                    shots=int(shots),
                    seed=int(seed) + int(shots),
                )
                local_payload = _fit_baseline(
                    plan,
                    graph,
                    "local",
                    train_obs=train_obs,
                    heldout=heldout,
                    teacher_logits=teacher_logits,
                    seed=int(seed),
                    shots=int(shots),
                    teacher_case=teacher_case,
                    windows=windows,
                    evidence_config=evidence_config,
                )
                num_model_fits_executed += 1
                records.append(local_payload["record"])
                local_logits = local_payload["logits"].detach().cpu().to(dtype=torch.float64)

                for baseline_model in ("known_hard_orbit",):
                    payload = _fit_baseline(
                        plan,
                        graph,
                        baseline_model,
                        train_obs=train_obs,
                        heldout=heldout,
                        teacher_logits=teacher_logits,
                        seed=int(seed),
                        shots=int(shots),
                        teacher_case=teacher_case,
                        windows=windows,
                        evidence_config=evidence_config,
                    )
                    num_model_fits_executed += 1
                    records.append(payload["record"])

                for condition in conditions:
                    selected, outcomes = _fit_condition_restarts(
                        plan,
                        graph,
                        condition=condition,
                        prototype_count=graph.O,
                        train_obs=train_obs,
                        validation_obs=validation,
                        heldout=heldout,
                        teacher_logits=teacher_logits,
                        local_logits=local_logits,
                        seed=int(seed),
                        shots=int(shots),
                        teacher_mode=teacher_case.mode,
                        epsilon_break=float(teacher_case.epsilon_break),
                        windows=windows,
                        evidence_config=evidence_config,
                        num_restarts=restarts,
                        active_mass_threshold=active_mass_threshold,
                        restart_poor_ari_threshold=restart_poor_ari_threshold,
                        selection_cfg=selection_cfg,
                        prior_context=prior_context,
                    )
                    num_model_fits_executed += len(outcomes)
                    restart_records.extend(outcomes)
                    record = build_evidence_record(
                        graph,
                        context=EvidenceContext(
                            seed=int(seed),
                            teacher_mode=teacher_case.mode,
                            teacher_residual_rank=int(plan.teacher_residual_rank),
                            epsilon_break=float(teacher_case.epsilon_break),
                            shots=int(shots),
                            model_name="disc_hard",
                            residual_rank=int(plan.teacher_residual_rank),
                        ),
                        fit_summary=selected["fit_summary"],
                        metrics=selected["metrics"],
                    )
                    record.update(
                        {
                            "evidence_record_schema": "scope_static_stage2a1_hardening_v1",
                            "stage": "stage2A.1",
                            "stage2a1_question": (
                                "Can recovery-biased optimization recover hidden omega(j) "
                                "when Stage 2A.0 free assignment is likelihood-positive but recovery-negative?"
                            ),
                            "stage2a1_condition_id": condition["id"],
                            "stage2a1_condition": condition["name"],
                            "prototype_count_K": int(graph.O),
                            "hidden_partition_available_to_learner": False,
                            "hidden_partition_used_by": "synthetic_teacher_and_evaluator_only",
                            "ari_nmi_used_for_selection": False,
                            "selection_rule": "validation_nll_plus_observable_health",
                            "disc10_controlled_use": _disc10_controlled_use(prior_context, condition),
                        }
                    )
                    record.update(
                        discovery_parameter_audit(
                            graph,
                            model_name="disc_hard",
                            prototype_count=graph.O,
                            residual_rank=int(plan.teacher_residual_rank),
                            assignment_parameterization=str(condition.get("assignment_parameterization", "free_hardened")),
                        )
                    )
                    records.append(record)

    add_known_orbit_deltas(records)
    important = _hardening_important_results(
        records,
        restart_records,
        conditions=conditions,
        threshold_epsilon=plan.threshold_epsilon,
        prior_context=prior_context,
    )
    result = {
        **graph.audit_dict(
            exact_likelihood_trainable=bool(plan.training_cfg.get("exact_likelihood_trainable", False)),
            dem_fault_logit_claim=bool(plan.training_cfg.get("dem_fault_logit_claim", False)),
            cptp_gksl_claim=bool(plan.training_cfg.get("cptp_gksl_claim", False)),
        ),
        **plan.output_audit_dict(),
        "stage": "stage2A.1",
        "schema": "scope_static_stage2a1_hardening_v1",
        "requested_likelihood_backend": plan.likelihood_backend,
        "likelihood_objective": plan.likelihood_objective,
        "hardening_conditions": conditions,
        "hardening_restarts": restarts,
        "validation_shots": validation_shots,
        "prior_context": prior_context,
        "stage2a1_acceptance_rule": _acceptance_rule(plan.threshold_epsilon),
        "num_model_fits_executed": num_model_fits_executed,
        "records": records,
        "hardening_restart_records": restart_records,
        "stage2a1_important_results": important,
    }
    (output / "metrics.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (output / "stage2a1_summary.md").write_text(format_hardening_summary_markdown(result))
    print(format_hardening_terminal_summary(result))
    return result


def _fit_condition_restarts(
    plan: ExperimentPlan,
    graph,
    *,
    condition: dict[str, object],
    prototype_count: int,
    train_obs: torch.Tensor,
    validation_obs: torch.Tensor,
    heldout: torch.Tensor,
    teacher_logits: torch.Tensor,
    local_logits: torch.Tensor,
    seed: int,
    shots: int,
    teacher_mode: str,
    epsilon_break: float,
    windows: WindowPlan,
    evidence_config: EvidenceConfig,
    num_restarts: int,
    active_mass_threshold: float,
    restart_poor_ari_threshold: float,
    selection_cfg: dict[str, object],
    prior_context: dict[str, object],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    selected: dict[str, object] | None = None
    best_score = float("inf")
    outcomes: list[dict[str, object]] = []
    for restart_index in range(max(1, int(num_restarts))):
        restart_seed = _restart_seed(seed=seed, prototype_count=prototype_count, restart_index=restart_index)
        model_options = _condition_model_options(condition)
        model_options["prototype_count"] = int(prototype_count)
        field = make_field("disc_hard", graph, dtype=plan.dtype, seed=restart_seed, model_options=model_options)
        init_audit = _apply_condition_initializer(
            field,
            condition=condition,
            local_logits=local_logits,
            restart_seed=restart_seed,
            init_logit=float(model_options.get("init_logit", -5.5)),
        )
        fit = _fit_field_hardening(
            plan,
            graph,
            field,
            train_obs,
            condition=condition,
            windows=windows,
        )
        fitted_field = fit["field"]
        logits = fitted_field.realized_logits(graph)
        validation_nll = _validation_nll(
            plan,
            graph,
            logits,
            validation_obs,
            windows=windows,
        )
        health = field_discovery_metrics(
            fitted_field,
            None,
            active_mass_threshold=active_mass_threshold,
        )
        health_penalty = _observable_health_penalty(health, prototype_count=prototype_count, selection_cfg=selection_cfg)
        selection_score = float(validation_nll + health_penalty)
        evaluator = field_discovery_metrics(
            fitted_field,
            graph.orbit_ids,
            active_mass_threshold=active_mass_threshold,
        )
        fit_summary = _fit_summary(fitted_field, fit)
        outcome = {
            "stage": "stage2A.1",
            "seed": int(seed),
            "teacher_mode": teacher_mode,
            "epsilon_break": float(epsilon_break),
            "shots": int(shots),
            "model": "disc_hard",
            "stage2a1_condition_id": condition["id"],
            "stage2a1_condition": condition["name"],
            "prototype_count_K": int(prototype_count),
            "restart_index": int(restart_index),
            "restart_seed": int(restart_seed),
            "selected": False,
            "train_initial_nll": fit_summary["train_initial_nll"],
            "train_final_nll": fit_summary["train_final_nll"],
            "validation_nll": validation_nll,
            "observable_health_penalty": health_penalty,
            "selection_score": selection_score,
            "selection_rule": "validation_nll_plus_observable_health",
            "ari_nmi_used_for_selection": False,
            "ari": evaluator.get("ari"),
            "nmi": evaluator.get("nmi"),
            "assignment_entropy_mean": evaluator.get("assignment_entropy_mean"),
            "assignment_entropy_normalized": evaluator.get("assignment_entropy_normalized"),
            "num_active_prototypes": evaluator.get("num_active_prototypes"),
            "assignment_collapse": evaluator.get("assignment_collapse"),
            "poor_partition_recovery": (
                None
                if evaluator.get("ari") is None
                else bool(float(evaluator["ari"]) < float(restart_poor_ari_threshold))
            ),
            **fit["assignment_movement_audit"],
            **init_audit,
        }
        outcomes.append(outcome)
        if selection_score < best_score:
            best_score = selection_score
            selected = {
                "restart_index": restart_index,
                "restart_seed": restart_seed,
                "fit_summary": fit_summary,
                "validation_nll": validation_nll,
                "observable_health_penalty": health_penalty,
                "selection_score": selection_score,
                "metrics": evaluator,
                "field": fitted_field,
                "initializer_audit": init_audit,
                "assignment_movement_audit": fit["assignment_movement_audit"],
            }

    assert selected is not None
    for outcome in outcomes:
        outcome["selected"] = outcome["restart_index"] == selected["restart_index"]

    fitted_field = selected["field"]
    logits = fitted_field.realized_logits(graph)
    selected_metrics = evaluate_evidence(
        graph,
        logits,
        teacher_logits.to(device=logits.device, dtype=logits.dtype),
        heldout,
        config=evidence_config,
        windows=windows,
    )
    selected_metrics.update(selected["metrics"])
    selected_metrics.update(
        {
            "stage2a1_condition_id": condition["id"],
            "stage2a1_condition": condition["name"],
            "stage2a1_assignment_mode": str(condition.get("assignment_mode", "soft")),
            "stage2a1_initializer": str(condition.get("initializer", "random")),
            "stage2a1_entropy_annealing": dict(condition.get("entropy_annealing", {})),
            "stage2a1_assignment_balance_weight": float(condition.get("assignment_balance_weight", 0.0)),
            "stage2a1_prototype_separation_weight": float(condition.get("prototype_separation_weight", 0.0)),
            "validation_nll": float(selected["validation_nll"]),
            "observable_health_penalty": float(selected["observable_health_penalty"]),
            "selection_score": float(selected["selection_score"]),
            "stage2a1_selection_metric": "validation_nll_plus_observable_health",
            "ari_nmi_used_for_selection": False,
            "hardening_num_restarts": max(1, int(num_restarts)),
            "hardening_selected_restart_index": int(selected["restart_index"]),
            "hardening_selected_restart_seed": int(selected["restart_seed"]),
            "hardening_restart_outcomes": outcomes,
            "hardening_nonselected_restart_collapses": sum(
                1 for outcome in outcomes if not outcome["selected"] and bool(outcome.get("assignment_collapse"))
            ),
            "hardening_nonselected_restart_poor_recovery": sum(
                1 for outcome in outcomes if not outcome["selected"] and bool(outcome.get("poor_partition_recovery"))
            ),
            "assignment_movement_audit": selected["assignment_movement_audit"],
            **selected["assignment_movement_audit"],
            **selected["initializer_audit"],
        }
    )
    selected["metrics"] = selected_metrics
    return selected, outcomes


def _fit_baseline(
    plan: ExperimentPlan,
    graph,
    model_name: str,
    *,
    train_obs: torch.Tensor,
    heldout: torch.Tensor,
    teacher_logits: torch.Tensor,
    seed: int,
    shots: int,
    teacher_case,
    windows: WindowPlan,
    evidence_config: EvidenceConfig,
) -> dict[str, object]:
    field = make_field(model_name, graph, dtype=plan.dtype, seed=seed, model_options=plan.model_options(model_name))
    fit = fit_field(
        graph,
        field,
        train_obs,
        steps=int(plan.training_cfg.get("steps", 200)),
        lr=float(plan.training_cfg.get("lr", 0.05)),
        aggregate_unique=plan.aggregate_unique,
        device=plan.device,
        backend=plan.likelihood_backend,
        observation_mode=plan.observation_mode(model_name),
        regularization_weight=plan.regularization_weight(model_name, plan.model_options(model_name)),
        likelihood_objective=plan.likelihood_objective,
        windows=windows,
    )
    fitted = fit["field"]
    logits = fitted.realized_logits(graph)
    metrics = evaluate_evidence(
        graph,
        logits,
        teacher_logits.to(device=logits.device, dtype=logits.dtype),
        heldout,
        config=evidence_config,
        windows=windows,
    )
    record = build_evidence_record(
        graph,
        context=EvidenceContext(
            seed=int(seed),
            teacher_mode=teacher_case.mode,
            teacher_residual_rank=int(plan.teacher_residual_rank),
            epsilon_break=float(teacher_case.epsilon_break),
            shots=int(shots),
            model_name=model_name,
            residual_rank=int(plan.teacher_residual_rank),
        ),
        fit_summary=_fit_summary(fitted, fit),
        metrics=metrics,
    )
    record.update({"stage": "stage2A.1", "stage2a1_baseline": True})
    return {"field": fitted, "logits": logits, "record": record}


def _fit_field_hardening(plan: ExperimentPlan, graph, field, observations, *, condition, windows: WindowPlan):
    device = plan.device
    field = field.to(device=device)
    optimizer = torch.optim.Adam(field.parameters(), lr=float(plan.training_cfg.get("lr", 0.05)))
    objective = build_likelihood_objective(
        graph,
        observations,
        likelihood_objective=plan.likelihood_objective,
        observation_mode="full",
        aggregate_unique=plan.aggregate_unique,
        backend=plan.likelihood_backend,
        cuda_kernel_variant=str(plan.training_cfg.get("cuda_kernel_variant", "dp")),
        windows=windows,
        device=device,
    )
    history: list[float] = []
    reg_history: list[float] = []
    assignment_grad_norms: list[float] = []
    start_state = _assignment_state(field)
    alpha_start = field.alpha.detach().clone()
    resolved_backend = None
    steps = int(plan.training_cfg.get("steps", 200))
    regularization_weight = float(condition.get("regularization_weight", 1.0))
    for step in range(steps):
        _apply_schedules(field, condition, step=step, steps=steps)
        optimizer.zero_grad(set_to_none=True)
        logits = field.realized_logits(graph)
        if resolved_backend is None:
            resolved_backend = objective.resolved_backend_for(logits)
        nll = objective.loss(logits)
        reg = field.regularization_loss()
        loss = nll + regularization_weight * reg
        loss.backward()
        assignment_grad = getattr(field, "assignment_logits", None)
        if assignment_grad is not None and assignment_grad.grad is not None:
            assignment_grad_norms.append(float(assignment_grad.grad.detach().norm().cpu()))
        optimizer.step()
        history.append(float(nll.detach().cpu()))
        reg_history.append(float(reg.detach().cpu()))
    end_state = _assignment_state(field)
    movement_audit = _assignment_movement_audit(
        start_state,
        end_state,
        assignment_grad_norms=assignment_grad_norms,
        prototype_param_delta_norm=float((field.alpha.detach() - alpha_start).norm().cpu()),
    )
    objective_audit = objective.audit_dict(
        scalar_bytes=next(parameter.element_size() for parameter in field.parameters())
    )
    return {
        "field": field,
        "history": history,
        "regularization_history": reg_history,
        "requested_backend": objective_audit["train_requested_likelihood_backend"],
        "resolved_backend": resolved_backend or plan.likelihood_backend,
        "likelihood_adapter": objective.adapter_name(resolved_backend or plan.likelihood_backend),
        "observation_mode": objective_audit["train_observation_mode"],
        "regularization_weight": regularization_weight,
        "likelihood_objective": objective_audit["train_likelihood_objective"],
        "cuda_kernel_variant": objective_audit["train_cuda_kernel_variant"],
        "selected_cuda_kernel_variant": objective_audit["selected_cuda_kernel_variant"],
        "cuda_kernel_fallback_reason": objective_audit["cuda_kernel_fallback_reason"],
        "num_train_windows": objective_audit["num_train_windows"],
        "max_train_window_bits": objective_audit["max_train_window_bits"],
        "likelihood_gpu_batch_available": objective_audit["train_likelihood_gpu_batch_available"],
        "stage2a1_final_assignment_entropy_weight": float(getattr(field, "assignment_entropy_weight", 0.0)),
        "stage2a1_final_assignment_balance_weight": float(getattr(field, "assignment_balance_weight", 0.0)),
        "stage2a1_final_prototype_separation_weight": float(getattr(field, "prototype_separation_weight", 0.0)),
        "assignment_movement_audit": movement_audit,
    }


def _validation_nll(plan: ExperimentPlan, graph, logits: torch.Tensor, observations: torch.Tensor, *, windows: WindowPlan) -> float:
    objective = build_likelihood_objective(
        graph,
        observations,
        likelihood_objective=plan.likelihood_objective,
        observation_mode="full",
        aggregate_unique=plan.aggregate_unique,
        backend=plan.likelihood_backend,
        cuda_kernel_variant=str(plan.training_cfg.get("cuda_kernel_variant", "dp")),
        windows=windows,
        device=plan.device,
    )
    with torch.no_grad():
        return float(objective.loss(logits).detach().cpu())


def _assignment_state(field) -> dict[str, object]:
    with torch.no_grad():
        S = field.assignment_probabilities().detach().cpu().to(dtype=torch.float64)
        labels = torch.argmax(S, dim=1).to(dtype=torch.long)
        positive = S > 0
        entropy_terms = torch.zeros_like(S)
        entropy_terms[positive] = -(S[positive] * torch.log(S[positive]))
        entropy = entropy_terms.sum(dim=1)
        hard_masses = torch.bincount(labels, minlength=int(S.shape[1])).to(dtype=torch.long)
        soft_masses = S.sum(dim=0)
    return {
        "labels": labels,
        "mean_entropy": float(entropy.mean().item()) if entropy.numel() else 0.0,
        "mean_entropy_normalized": 0.0 if S.shape[1] <= 1 else float(entropy.mean().item() / math.log(int(S.shape[1]))),
        "cluster_mass": [int(value) for value in hard_masses.tolist()],
        "prototype_mass": [float(value) for value in soft_masses.tolist()],
    }


def _assignment_movement_audit(
    start: dict[str, object],
    end: dict[str, object],
    *,
    assignment_grad_norms: list[float],
    prototype_param_delta_norm: float,
) -> dict[str, object]:
    start_labels = torch.as_tensor(start["labels"], dtype=torch.long)
    end_labels = torch.as_tensor(end["labels"], dtype=torch.long)
    changed = start_labels != end_labels
    return {
        "assignment_movement_audit_schema": "scope_static_stage2a1_assignment_movement_v1",
        "init_final_assignment_nmi": normalized_mutual_info(start_labels, end_labels),
        "fraction_rows_changed": float(changed.to(dtype=torch.float64).mean().item()) if changed.numel() else 0.0,
        "mean_assignment_entropy_start": float(start["mean_entropy"]),
        "mean_assignment_entropy_end": float(end["mean_entropy"]),
        "mean_assignment_entropy_normalized_start": float(start["mean_entropy_normalized"]),
        "mean_assignment_entropy_normalized_end": float(end["mean_entropy_normalized"]),
        "assignment_logit_grad_norm": float(sum(assignment_grad_norms) / len(assignment_grad_norms))
        if assignment_grad_norms
        else 0.0,
        "assignment_logit_grad_norm_final": float(assignment_grad_norms[-1]) if assignment_grad_norms else 0.0,
        "assignment_logit_grad_norm_max": float(max(assignment_grad_norms)) if assignment_grad_norms else 0.0,
        "prototype_param_delta_norm": float(prototype_param_delta_norm),
        "cluster_mass_start": list(start["cluster_mass"]),
        "cluster_mass_end": list(end["cluster_mass"]),
        "prototype_mass_start": list(start["prototype_mass"]),
        "prototype_mass_end": list(end["prototype_mass"]),
        "selected_by_ari_nmi": False,
    }


def _apply_condition_initializer(
    field,
    *,
    condition: dict[str, object],
    local_logits: torch.Tensor,
    restart_seed: int,
    init_logit: float,
) -> dict[str, object]:
    initializer = str(condition.get("initializer", "random"))
    confidence = float(condition.get("initializer_confidence", 6.0))
    if initializer == "local_logit":
        initialization = local_logit_assignment_initialization(local_logits, num_prototypes=field.num_prototypes)
        apply_assignment_initialization(field, initialization, confidence=confidence)
    elif initializer == "random_balanced":
        initialization = random_balanced_assignment_initialization(
            None,
            num_faults=field.num_faults,
            num_prototypes=field.num_prototypes,
            seed=restart_seed,
            init_logit=init_logit,
        )
        apply_assignment_initialization(field, initialization, confidence=confidence)
    elif initializer == "random":
        return {
            "assignment_initializer": "random_parameter_init",
            "assignment_initializer_feature_family": None,
            "uses_hidden_omega_for_initialization": False,
            "initializer_confidence": None,
        }
    else:
        raise ValueError(f"unknown Stage 2A.1 initializer {initializer!r}")
    return {
        "assignment_initializer": initialization.source,
        "assignment_initializer_feature_family": initialization.feature_family,
        "uses_hidden_omega_for_initialization": initialization.uses_hidden_omega,
        "initializer_confidence": confidence,
    }


def _condition_model_options(condition: dict[str, object]) -> dict[str, object]:
    entropy = dict(condition.get("entropy_annealing", {}))
    initial_entropy = float(entropy.get("start", condition.get("assignment_entropy_weight", 0.0)))
    return {
        "assignment_mode": str(condition.get("assignment_mode", "soft")),
        "assignment_entropy_weight": initial_entropy,
        "assignment_balance_weight": float(condition.get("assignment_balance_weight", 0.0)),
        "prototype_separation_weight": float(condition.get("prototype_separation_weight", 0.0)),
        "prototype_separation_margin": float(condition.get("prototype_separation_margin", 0.5)),
        "assignment_temperature": float(condition.get("assignment_temperature", 1.0)),
        "init_logit": float(condition.get("init_logit", -5.5)),
        "alpha_init_scale": float(condition.get("alpha_init_scale", 0.01)),
        "assignment_init_scale": float(condition.get("assignment_init_scale", 0.01)),
    }


def _apply_schedules(field, condition: dict[str, object], *, step: int, steps: int) -> None:
    entropy = dict(condition.get("entropy_annealing", {}))
    if bool(entropy.get("enabled", False)):
        start = float(entropy.get("start", 0.0))
        end = float(entropy.get("end", 0.0))
        progress = 1.0 if steps <= 1 else float(step) / float(steps - 1)
        field.assignment_entropy_weight = start + progress * (end - start)


def _observable_health_penalty(
    health: dict[str, object],
    *,
    prototype_count: int,
    selection_cfg: dict[str, object],
) -> float:
    active = int(health.get("num_active_prototypes") or 0)
    entropy = float(health.get("assignment_entropy_normalized") or 0.0)
    collapse = bool(health.get("assignment_collapse", False))
    target_active = max(1, int(prototype_count) - 1)
    deficit = max(0, target_active - active)
    penalty = float(selection_cfg.get("active_deficit_penalty", 0.05)) * deficit
    if collapse:
        penalty += float(selection_cfg.get("collapse_penalty", 1.0))
    if entropy > float(selection_cfg.get("max_entropy_normalized", 0.95)):
        penalty += float(selection_cfg.get("diffuse_entropy_penalty", 0.02)) * (entropy - 0.95)
    return float(penalty)


def _fit_summary(field, fit: dict[str, object]) -> dict[str, object]:
    history = fit["history"]
    summary = {
        "parameter_count": int(field.parameter_count),
        "train_initial_nll": history[0] if history else None,
        "train_final_nll": history[-1] if history else None,
        "train_requested_likelihood_backend": fit["requested_backend"],
        "train_resolved_likelihood_backend": fit["resolved_backend"],
        "train_likelihood_adapter": fit["likelihood_adapter"],
        "train_likelihood_gpu_batch_available": fit["likelihood_gpu_batch_available"],
        "train_observation_mode": fit["observation_mode"],
        "train_regularization_weight": fit["regularization_weight"],
        "train_likelihood_objective": fit["likelihood_objective"],
        "num_train_windows": fit["num_train_windows"],
        "max_train_window_bits": fit["max_train_window_bits"],
    }
    for key in (
        "stage2a1_final_assignment_entropy_weight",
        "stage2a1_final_assignment_balance_weight",
        "stage2a1_final_prototype_separation_weight",
    ):
        if key in fit:
            summary[key] = fit[key]
    return summary


def _condition_specs(hardening_cfg: dict[str, object]) -> list[dict[str, object]]:
    raw = hardening_cfg.get("conditions", DEFAULT_CONDITIONS)
    conditions = [dict(condition) for condition in raw]
    for condition in conditions:
        condition.setdefault("assignment_parameterization", "free_hardened")
        condition.setdefault("initializer_confidence", 6.0)
        if "id" not in condition or "name" not in condition:
            raise ValueError("each Stage 2A.1 condition needs id and name")
    return conditions


def _hardening_important_results(
    records: list[dict[str, object]],
    restart_records: list[dict[str, object]],
    *,
    conditions: list[dict[str, object]],
    threshold_epsilon: float,
    prior_context: dict[str, object],
) -> dict[str, object]:
    discovery_records = [record for record in records if record.get("stage2a1_condition_id") is not None]
    rows = []
    for condition in conditions:
        group = [record for record in discovery_records if record.get("stage2a1_condition_id") == condition["id"]]
        restart_group = [record for record in restart_records if record.get("stage2a1_condition_id") == condition["id"]]
        row = {
            "condition_id": condition["id"],
            "condition": condition["name"],
            "num_records": len(group),
            "num_restarts": len(restart_group),
            "mean_ari": _mean(group, "ari"),
            "mean_nmi": _mean(group, "nmi"),
            "mean_delta_nll_known_orbit": _mean(group, "delta_nll_known_orbit"),
            "mean_validation_nll": _mean(group, "validation_nll"),
            "mean_selection_score": _mean(group, "selection_score"),
            "mean_assignment_entropy_normalized": _mean(group, "assignment_entropy_normalized"),
            "mean_active_prototypes": _mean(group, "num_active_prototypes"),
            "min_active_prototypes": _min(group, "num_active_prototypes"),
            "num_selected_collapsed": sum(1 for record in group if bool(record.get("assignment_collapse", False))),
            "ari_nmi_used_for_selection": False,
            "selected_by_ari_nmi": False,
            "mean_init_final_assignment_nmi": _mean(group, "init_final_assignment_nmi"),
            "mean_fraction_rows_changed": _mean(group, "fraction_rows_changed"),
            "mean_assignment_entropy_start": _mean(group, "mean_assignment_entropy_start"),
            "mean_assignment_entropy_end": _mean(group, "mean_assignment_entropy_end"),
            "mean_assignment_logit_grad_norm": _mean(group, "assignment_logit_grad_norm"),
            "mean_prototype_param_delta_norm": _mean(group, "prototype_param_delta_norm"),
        }
        row["stage2a1_acceptance"] = _classify_stage2a1(row, threshold_epsilon, prior_context)
        rows.append(row)
    movement = _movement_summary(rows)
    return {
        "schema": "scope_static_stage2a1_important_results_v1",
        "acceptance_rule": _acceptance_rule(threshold_epsilon),
        "prior_context": prior_context,
        "condition_summary": rows,
        "assignment_movement_audit": movement,
        "stage2a1_conclusion": _stage2a1_conclusion(rows, threshold_epsilon=threshold_epsilon),
        "assignment_movement_interpretation": _assignment_movement_interpretation(movement),
        "main_comparisons": _main_comparisons(rows),
    }


def _classify_stage2a1(row: dict[str, object], threshold_epsilon: float, prior_context: dict[str, object]) -> str:
    ari = float(row.get("mean_ari") or 0.0)
    nmi = float(row.get("mean_nmi") or 0.0)
    delta = row.get("mean_delta_nll_known_orbit")
    nll_close = delta is not None and float(delta) <= float(threshold_epsilon)
    active_ok = int(row.get("min_active_prototypes") or 0) >= int(prior_context.get("K_minus_1", 0))
    no_collapse = int(row.get("num_selected_collapsed") or 0) == 0
    if ari >= 0.80 and nmi >= 0.80 and nll_close and active_ok and no_collapse:
        return "strong_recovery"
    baseline_ari = float(prior_context.get("baseline_recovery_ari", 0.0))
    baseline_nmi = float(prior_context.get("baseline_recovery_nmi", 0.0))
    improved = (ari - baseline_ari) >= 0.10 or (nmi - baseline_nmi) >= 0.10
    if improved and no_collapse:
        return "partial_recovery"
    if nll_close and ari < 0.80:
        return "failure_likelihood_good_recovery_low"
    return "failure"


def _main_comparisons(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_id = {str(row["condition_id"]): row for row in rows}
    pairs = [("A", "B", "audited_initialization"), ("B", "D", "hard_assignment"), ("D", "E", "entropy_annealing"), ("E", "F", "balance"), ("F", "G", "prototype_separation")]
    result = []
    for left, right, label in pairs:
        if left not in by_id or right not in by_id:
            continue
        a = by_id[left]
        b = by_id[right]
        result.append(
            {
                "comparison": f"{left}_to_{right}",
                "question": label,
                "delta_mean_ari": _delta(b, a, "mean_ari"),
                "delta_mean_nmi": _delta(b, a, "mean_nmi"),
                "delta_mean_delta_nll_known_orbit": _delta(b, a, "mean_delta_nll_known_orbit"),
            }
        )
    return result


def _movement_summary(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "condition_id": row["condition_id"],
            "condition": row["condition"],
            "init_final_assignment_nmi": row["mean_init_final_assignment_nmi"],
            "fraction_rows_changed": row["mean_fraction_rows_changed"],
            "mean_assignment_entropy_start": row["mean_assignment_entropy_start"],
            "mean_assignment_entropy_end": row["mean_assignment_entropy_end"],
            "assignment_logit_grad_norm": row["mean_assignment_logit_grad_norm"],
            "prototype_param_delta_norm": row["mean_prototype_param_delta_norm"],
            "selection_score": row["mean_selection_score"],
            "selected_by_ari_nmi": False,
        }
        for row in rows
    ]


def _stage2a1_conclusion(rows: list[dict[str, object]], *, threshold_epsilon: float) -> str:
    if any(row.get("stage2a1_acceptance") == "strong_recovery" for row in rows):
        return "strong_recovery"
    if any(row.get("stage2a1_acceptance") == "partial_recovery" for row in rows):
        return "partial_recovery_not_strong"
    best_delta = min(
        (float(row["mean_delta_nll_known_orbit"]) for row in rows if row.get("mean_delta_nll_known_orbit") is not None),
        default=float("inf"),
    )
    best_ari = max((float(row.get("mean_ari") or 0.0) for row in rows), default=0.0)
    if best_delta <= float(threshold_epsilon) and best_ari < 0.80:
        return "likelihood_good_recovery_low_hardening_non_rescuing"
    return "hardening_inconclusive_or_failed"


def _assignment_movement_interpretation(rows: list[dict[str, object]]) -> str:
    keyed = {str(row["condition_id"]): row for row in rows}
    stable_local = [
        keyed[condition_id]
        for condition_id in ("B", "E", "G")
        if condition_id in keyed
        and _float_or_default(keyed[condition_id].get("init_final_assignment_nmi"), 0.0) >= 0.98
        and _float_or_default(keyed[condition_id].get("fraction_rows_changed"), 1.0) <= 0.02
    ]
    if len(stable_local) >= 2:
        return "local_logit_initialized_assignments_remain_at_disc10_ceiling"
    if any(_float_or_default(row.get("fraction_rows_changed"), 0.0) > 0.25 for row in rows):
        return "assignments_move_but_do_not_recover_hidden_quotient"
    return "assignments_movement_inconclusive"


def _load_prior_context(hardening_cfg: dict[str, object]) -> dict[str, object]:
    context: dict[str, object] = {
        "stage2a0_summary_path": str(hardening_cfg.get("stage2a0_summary_path", "")),
        "disc10_metrics_path": str(hardening_cfg.get("disc10_metrics_path", "")),
        "baseline_recovery_ari": 0.0,
        "baseline_recovery_nmi": 0.0,
        "K_minus_1": 0,
    }
    stage2a0_text = str(hardening_cfg.get("stage2a0_summary_path", ""))
    stage2a0_path = Path(stage2a0_text)
    if stage2a0_text and stage2a0_path.is_file():
        data = json.loads(stage2a0_path.read_text())
        main = data.get("main_matched_k_disc_hard") or {}
        context["stage2a0_result"] = data.get("stage2a0_result")
        context["stage2a0_ari"] = main.get("mean_ari")
        context["stage2a0_nmi"] = main.get("mean_nmi")
        if main.get("prototype_count_K") is not None:
            context["K_minus_1"] = int(main["prototype_count_K"]) - 1
    disc10_text = str(hardening_cfg.get("disc10_metrics_path", ""))
    disc10_path = Path(disc10_text)
    if disc10_text and disc10_path.is_file():
        data = json.loads(disc10_path.read_text())
        audit = data.get("disc10_audit") or {}
        seed_candidate = data.get("disc10_seed_candidate") or {}
        context["disc10_result"] = audit.get("passive_identifiability_result")
        context["disc10_ari"] = audit.get("ari")
        context["disc10_nmi"] = audit.get("nmi")
        context["disc10_best_visible_signature_family"] = audit.get("best_visible_signature_family")
        context["disc10_seed_candidate_family"] = seed_candidate.get("signature_family")
        if data.get("K") is not None:
            context["K_minus_1"] = int(data["K"]) - 1
    context["baseline_recovery_ari"] = max(
        _float_or_zero(context.get("stage2a0_ari")),
        _float_or_zero(context.get("disc10_ari")),
    )
    context["baseline_recovery_nmi"] = max(
        _float_or_zero(context.get("stage2a0_nmi")),
        _float_or_zero(context.get("disc10_nmi")),
    )
    return context


def _disc10_controlled_use(prior_context: dict[str, object], condition: dict[str, object]) -> dict[str, object]:
    return {
        "disc10_metrics_path": prior_context.get("disc10_metrics_path"),
        "disc10_result": prior_context.get("disc10_result"),
        "disc10_best_visible_signature_family": prior_context.get("disc10_best_visible_signature_family"),
        "condition_initializer": condition.get("initializer"),
        "uses_disc10_ari_nmi_for_selection": False,
        "uses_hidden_omega_for_initialization": False,
    }


def _acceptance_rule(threshold_epsilon: float) -> dict[str, object]:
    return {
        "strong_recovery": {
            "ari_min": 0.80,
            "nmi_min": 0.80,
            "delta_nll_known_orbit_max": float(threshold_epsilon),
            "active_clusters": ">= K - 1",
            "selection": "validation NLL / observable health, never ARI/NMI",
        },
        "partial_recovery": "ARI or NMI improves by at least 0.10 over Stage 2A.0/DISC10 but does not reach strong recovery.",
        "failure": "NLL remains good while ARI stays low, or recovery would require ARI/NMI-based selection.",
    }


def format_hardening_summary_markdown(result: dict[str, object]) -> str:
    lines = [
        "# Stage 2A.1 Hardening Summary",
        "",
        f"- Metrics: `{Path(result['output_dir']) / 'metrics.json'}`",
        f"- Conclusion: `{result['stage2a1_important_results']['stage2a1_conclusion']}`",
        f"- Movement interpretation: `{result['stage2a1_important_results']['assignment_movement_interpretation']}`",
        f"- Selection rule: `validation_nll_plus_observable_health`",
        f"- ARI/NMI used for selection: `false`",
        "",
        "| id | condition | ARI | NMI | dNLL known | active | result |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in result["stage2a1_important_results"]["condition_summary"]:
        lines.append(
            f"| {row['condition_id']} | {row['condition']} | {_fmt(row['mean_ari'])} | "
            f"{_fmt(row['mean_nmi'])} | {_fmt(row['mean_delta_nll_known_orbit'])} | "
            f"{_fmt(row['mean_active_prototypes'])} | {row['stage2a1_acceptance']} |"
        )
    lines.extend(
        [
            "",
            "## Assignment Movement Audit",
            "",
            "| id | init-final NMI | rows changed | entropy start | entropy end | grad norm | alpha delta | selected by ARI/NMI |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in result["stage2a1_important_results"]["assignment_movement_audit"]:
        lines.append(
            f"| {row['condition_id']} | {_fmt(row['init_final_assignment_nmi'])} | "
            f"{_fmt(row['fraction_rows_changed'])} | {_fmt(row['mean_assignment_entropy_start'])} | "
            f"{_fmt(row['mean_assignment_entropy_end'])} | {_fmt(row['assignment_logit_grad_norm'])} | "
            f"{_fmt(row['prototype_param_delta_norm'])} | {str(row['selected_by_ari_nmi']).lower()} |"
        )
    lines.extend(
        [
            "",
            "DISC10 is used only as a controlled visible-signature initializer context; ARI/NMI remain evaluator-only.",
            "",
        ]
    )
    return "\n".join(lines)


def format_hardening_terminal_summary(result: dict[str, object]) -> str:
    lines = [
        "Stage 2A.1 Hardening Summary",
        f"config: {result.get('config_path')}",
        f"output: {result.get('output_dir')}",
        f"metrics: {Path(str(result.get('output_dir'))) / 'metrics.json'}",
        f"conclusion: {result['stage2a1_important_results']['stage2a1_conclusion']}",
        f"movement: {result['stage2a1_important_results']['assignment_movement_interpretation']}",
        "selection: validation_nll_plus_observable_health | ARI/NMI evaluator-only",
        "",
        "id  condition                                      ARI     NMI     dNLL_known  active  result",
        "--  ---------------------------------------------  ------  ------  ----------  ------  -------------------------------",
    ]
    for row in result["stage2a1_important_results"]["condition_summary"]:
        lines.append(
            f"{row['condition_id']:<2}  {row['condition']:<45}  {_fmt(row['mean_ari']):>6}  "
            f"{_fmt(row['mean_nmi']):>6}  {_fmt(row['mean_delta_nll_known_orbit']):>10}  "
            f"{_fmt(row['mean_active_prototypes']):>6}  {row['stage2a1_acceptance']}"
        )
    return "\n".join(lines)


def _restart_seed(*, seed: int, prototype_count: int, restart_index: int) -> int:
    return int(seed) + 200_000 + 1_000 * int(prototype_count) + int(restart_index)


def _mean(records: list[dict[str, object]], key: str) -> float | None:
    values = [float(record[key]) for record in records if record.get(key) is not None]
    return float(sum(values) / len(values)) if values else None


def _min(records: list[dict[str, object]], key: str) -> float | None:
    values = [float(record[key]) for record in records if record.get(key) is not None]
    return float(min(values)) if values else None


def _delta(right: dict[str, object], left: dict[str, object], key: str) -> float | None:
    if right.get(key) is None or left.get(key) is None:
        return None
    return float(right[key]) - float(left[key])


def _float_or_zero(value: object) -> float:
    return _float_or_default(value, 0.0)


def _float_or_default(value: object, default: float) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float(default)
    return result if math.isfinite(result) else float(default)


def _fmt(value: object) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.4g}"
    except (TypeError, ValueError):
        return str(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Stage 2A.1 hardening ablation grid.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args(argv)
    run_hardening_experiment(args.config, output_dir=args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
