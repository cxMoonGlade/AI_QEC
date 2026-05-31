from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import torch
import yaml

from scope_static.experiments.static.plan import ExperimentPlan
from scope_static.dem.metrics import exact_dem_nll
from scope_static.dem.multi_env import (
    MultiEnvIndependentAssignmentField,
    MultiEnvKnownOrbitField,
    MultiEnvLocalField,
    MultiEnvSharedAssignmentField,
    assignment_recovery_metrics,
    independent_assignment_recovery_metrics,
    initialize_shared_from_local_logits,
    make_multi_env_teacher,
)
from scope_static.dem.objectives import build_likelihood_objective
from scope_static.dem.stim_dem import sample_observations_from_logits


DISC12_AUDIT = {
    "stage": "stage2A.2",
    "experiment": "DISC12_multi_env_shared_assignment",
    "uses_hidden_omega_for_training": False,
    "uses_hidden_omega_for_initialization": False,
    "uses_hidden_omega_for_checkpoint_selection": False,
    "uses_hidden_omega_for_final_evaluation": True,
    "ari_nmi_used_for_selection": False,
}


def run_multi_env_discovery(
    config_path: str | Path,
    *,
    output_dir: str | Path | None = None,
) -> dict[str, object]:
    plan = ExperimentPlan.from_path(config_path, output_dir=output_dir)
    cfg = dict(plan.config.get("multi_env", {}))
    output = plan.output_dir
    output.mkdir(parents=True, exist_ok=True)
    (output / "config_snapshot.yaml").write_text(yaml.safe_dump(plan.config, sort_keys=False))

    graph = plan.build_graph(plan.teacher_residual_rank)
    teacher = make_multi_env_teacher(
        graph,
        seed=int(cfg.get("teacher_seed", 0)),
        dtype=plan.dtype,
        contrast_strength=float(cfg.get("contrast_strength", 1.0)),
        design=str(cfg.get("environment_design", "default")),
    )
    train_env_ids = tuple(int(env) for env in cfg.get("train_env_ids", [0, 1, 2, 3]))
    heldout_env_ids = tuple(int(env) for env in cfg.get("heldout_env_ids", [4]))
    shot_budget = int(plan.shot_budgets[0])
    validation_shots = int(cfg.get("validation_shots", shot_budget))
    heldout_shots = int(plan.heldout_shots)
    adaptation_shots = int(cfg.get("heldout_env_adaptation_shots", shot_budget))
    restarts = int(cfg.get("restarts", 4))
    active_mass_threshold = float(cfg.get("active_mass_threshold", 1.0))
    stage2a1_ceiling = dict(cfg.get("stage2a1_ceiling", {"ari": 0.2748, "nmi": 0.7097}))

    observations = _sample_env_observations(
        graph,
        teacher.logits_by_env,
        shots=shot_budget,
        seed_base=10_000,
        env_ids=teacher.env_ids,
    )
    validation_observations = _sample_env_observations(
        graph,
        teacher.logits_by_env,
        shots=validation_shots,
        seed_base=20_000,
        env_ids=teacher.env_ids,
    )
    heldout_observations = _sample_env_observations(
        graph,
        teacher.logits_by_env,
        shots=heldout_shots,
        seed_base=30_000,
        env_ids=teacher.env_ids,
    )
    heldout_adaptation_observations = _sample_env_observations(
        graph,
        teacher.logits_by_env,
        shots=adaptation_shots,
        seed_base=40_000,
        env_ids=teacher.env_ids,
    )

    local_logits_by_train_env, local_record = _fit_local_full_per_env(
        plan,
        graph,
        train_env_ids=train_env_ids,
        train_observations=observations,
        validation_observations=validation_observations,
        heldout_observations=heldout_observations,
        teacher_logits=teacher.logits_by_env,
        active_mass_threshold=active_mass_threshold,
    )
    records = [local_record]
    restart_records: list[dict[str, object]] = []

    condition_specs = _condition_specs(cfg)
    for spec in condition_specs:
        if spec["model"] == "known_orbit_oracle_shared_S":
            record = _fit_known_orbit_oracle(
                plan,
                graph,
                train_env_ids=train_env_ids,
                heldout_env_ids=heldout_env_ids,
                train_observations=observations,
                validation_observations=validation_observations,
                heldout_observations=heldout_observations,
                heldout_adaptation_observations=heldout_adaptation_observations,
                teacher_logits=teacher.logits_by_env,
                active_mass_threshold=active_mass_threshold,
            )
            records.append(record)
            continue
        selected, outcomes = _fit_condition_restarts(
            plan,
            graph,
            spec=spec,
            train_env_ids=train_env_ids if bool(spec.get("multi_env", True)) else (train_env_ids[0],),
            heldout_env_ids=heldout_env_ids,
            train_observations=observations,
            validation_observations=validation_observations,
            heldout_observations=heldout_observations,
            heldout_adaptation_observations=heldout_adaptation_observations,
            teacher_logits=teacher.logits_by_env,
            local_logits_by_train_env=local_logits_by_train_env,
            restarts=restarts,
            active_mass_threshold=active_mass_threshold,
        )
        records.append(selected)
        restart_records.extend(outcomes)

    _add_known_orbit_deltas(records)
    important = _disc12_important_results(
        records,
        threshold_epsilon=plan.threshold_epsilon,
        stage2a1_ceiling=stage2a1_ceiling,
        num_prototypes=graph.O,
    )
    sweep = _run_contrast_sweep(
        plan,
        graph,
        cfg=cfg,
        stage2a1_ceiling=stage2a1_ceiling,
        output=output,
    )
    result = {
        **graph.audit_dict(
            exact_likelihood_trainable=bool(plan.training_cfg.get("exact_likelihood_trainable", False)),
            dem_fault_logit_claim=bool(plan.training_cfg.get("dem_fault_logit_claim", False)),
            cptp_gksl_claim=bool(plan.training_cfg.get("cptp_gksl_claim", False)),
        ),
        **plan.output_audit_dict(),
        **DISC12_AUDIT,
        "schema": "scope_static_stage2a2_disc12_v1",
        "train_env_ids": list(train_env_ids),
        "heldout_env_ids": list(heldout_env_ids),
        "env_names": list(teacher.env_names),
        "shot_budget": shot_budget,
        "validation_shots": validation_shots,
        "heldout_shots": heldout_shots,
        "heldout_env_adaptation_protocol": "freeze_shared_S_fit_env_alpha_only",
        "stage2a1_ceiling": stage2a1_ceiling,
        "environment_contrast_audit": _environment_contrast_audit(teacher.alpha_by_env, teacher.logits_by_env),
        "disc12a_stage_label": "multi_env_predictive_only_weak_recovery_gain_observable_contrast_likely_insufficient",
        "contrast_sweep": sweep,
        "records": records,
        "restart_records": restart_records,
        "disc12_important_results": important,
    }
    _write_artifacts(output, result, records, restart_records)
    print(format_disc12_terminal_summary(result))
    return result


def _fit_condition_restarts(
    plan: ExperimentPlan,
    graph,
    *,
    spec: dict[str, object],
    train_env_ids: tuple[int, ...],
    heldout_env_ids: tuple[int, ...],
    train_observations: dict[int, torch.Tensor],
    validation_observations: dict[int, torch.Tensor],
    heldout_observations: dict[int, torch.Tensor],
    heldout_adaptation_observations: dict[int, torch.Tensor],
    teacher_logits: torch.Tensor,
    local_logits_by_train_env: dict[int, torch.Tensor],
    restarts: int,
    active_mass_threshold: float,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    selected: dict[str, object] | None = None
    outcomes: list[dict[str, object]] = []
    best_score = float("inf")
    for restart_index in range(max(1, int(restarts))):
        seed = 300_000 + 1_000 * len(train_env_ids) + 17 * restart_index
        field = _make_field_for_spec(plan, graph, spec, num_environments=len(train_env_ids), seed=seed)
        init_audit = _apply_initializer(
            field,
            spec=spec,
            local_logits=local_logits_by_train_env[train_env_ids[0]],
        )
        fit = _fit_multi_env_field(
            plan,
            graph,
            field,
            train_env_ids=train_env_ids,
            observations=train_observations,
        )
        field = fit["field"]
        validation_nll = _mean_env_nll(
            graph,
            [field.realized_logits_for_env(slot) for slot in range(len(train_env_ids))],
            [validation_observations[env] for env in train_env_ids],
            backend=plan.likelihood_backend,
            aggregate_unique=plan.aggregate_unique,
        )
        health = _field_recovery_metrics(field, graph, active_mass_threshold=active_mass_threshold)
        penalty = _observable_health_penalty(health, num_prototypes=graph.O)
        score = float(validation_nll + penalty)
        movement = _assignment_movement_audit(init_audit.get("init_labels"), _field_labels(field))
        outcome = {
            **DISC12_AUDIT,
            "model": spec["model"],
            "condition": spec["name"],
            "restart_index": restart_index,
            "restart_seed": seed,
            "selected": False,
            "validation_nll": validation_nll,
            "observable_health_penalty": penalty,
            "selection_score": score,
            "selection_rule": "validation_nll_plus_observable_health",
            **health,
            **movement,
            **{k: v for k, v in init_audit.items() if k != "init_labels"},
        }
        outcomes.append(outcome)
        if score < best_score:
            best_score = score
            selected = {
                "field": field,
                "fit": fit,
                "outcome": outcome,
                "init_audit": init_audit,
                "movement": movement,
            }
    assert selected is not None
    for outcome in outcomes:
        outcome["selected"] = outcome["restart_index"] == selected["outcome"]["restart_index"]

    field = selected["field"]
    record = _evaluate_multi_env_model(
        plan,
        graph,
        field,
        spec=spec,
        train_env_ids=train_env_ids,
        heldout_env_ids=heldout_env_ids,
        heldout_observations=heldout_observations,
        heldout_adaptation_observations=heldout_adaptation_observations,
        teacher_logits=teacher_logits,
        active_mass_threshold=active_mass_threshold,
    )
    record.update(
        {
            "train_final_nll": selected["fit"]["history"][-1] if selected["fit"]["history"] else None,
            "validation_nll": selected["outcome"]["validation_nll"],
            "selection_score": selected["outcome"]["selection_score"],
            "selection_rule": "validation_nll_plus_observable_health",
            "restart_selection_audit": outcomes,
            **selected["movement"],
            **{k: v for k, v in selected["init_audit"].items() if k != "init_labels"},
        }
    )
    return record, outcomes


def _fit_known_orbit_oracle(
    plan: ExperimentPlan,
    graph,
    *,
    train_env_ids: tuple[int, ...],
    heldout_env_ids: tuple[int, ...],
    train_observations: dict[int, torch.Tensor],
    validation_observations: dict[int, torch.Tensor],
    heldout_observations: dict[int, torch.Tensor],
    heldout_adaptation_observations: dict[int, torch.Tensor],
    teacher_logits: torch.Tensor,
    active_mass_threshold: float,
) -> dict[str, object]:
    field = MultiEnvKnownOrbitField(graph.orbit_ids, len(train_env_ids), dtype=plan.dtype)
    fit = _fit_multi_env_field(plan, graph, field, train_env_ids=train_env_ids, observations=train_observations)
    return _evaluate_multi_env_model(
        plan,
        graph,
        fit["field"],
        spec={
            "model": "known_orbit_oracle_shared_S",
            "name": "known_orbit_oracle_shared_S",
            "shared_assignment": True,
            "oracle": True,
        },
        train_env_ids=train_env_ids,
        heldout_env_ids=heldout_env_ids,
        heldout_observations=heldout_observations,
        heldout_adaptation_observations=heldout_adaptation_observations,
        teacher_logits=teacher_logits,
        active_mass_threshold=active_mass_threshold,
        extra={
            "train_final_nll": fit["history"][-1] if fit["history"] else None,
            "validation_nll": _mean_env_nll(
                graph,
                [fit["field"].realized_logits_for_env(slot) for slot in range(len(train_env_ids))],
                [validation_observations[env] for env in train_env_ids],
                backend=plan.likelihood_backend,
                aggregate_unique=plan.aggregate_unique,
            ),
        },
    )


def _fit_local_full_per_env(
    plan: ExperimentPlan,
    graph,
    *,
    train_env_ids: tuple[int, ...],
    train_observations: dict[int, torch.Tensor],
    validation_observations: dict[int, torch.Tensor],
    heldout_observations: dict[int, torch.Tensor],
    teacher_logits: torch.Tensor,
    active_mass_threshold: float,
) -> tuple[dict[int, torch.Tensor], dict[str, object]]:
    field = MultiEnvLocalField(graph.M, len(train_env_ids), dtype=plan.dtype)
    fit = _fit_multi_env_field(plan, graph, field, train_env_ids=train_env_ids, observations=train_observations)
    fitted = fit["field"]
    local_logits = {
        env: fitted.realized_logits_for_env(slot).detach().cpu().to(dtype=torch.float64)
        for slot, env in enumerate(train_env_ids)
    }
    train_eval = _eval_envs(
        graph,
        [fitted.realized_logits_for_env(slot) for slot in range(len(train_env_ids))],
        train_env_ids,
        heldout_observations,
        teacher_logits,
        backend=plan.likelihood_backend,
        aggregate_unique=plan.aggregate_unique,
    )
    record = {
        **DISC12_AUDIT,
        "model": "local_full_per_fault_per_env",
        "condition": "local_full_per_fault_per_env",
        "shared_assignment": False,
        "parameter_count": int(fitted.parameter_count),
        "env_alpha_train": {
            str(env): [float(value) for value in logits.flatten().tolist()]
            for env, logits in local_logits.items()
        },
        "train_final_nll": fit["history"][-1] if fit["history"] else None,
        "validation_nll": _mean_env_nll(
            graph,
            [fitted.realized_logits_for_env(slot) for slot in range(len(train_env_ids))],
            [validation_observations[env] for env in train_env_ids],
            backend=plan.likelihood_backend,
            aggregate_unique=plan.aggregate_unique,
        ),
        "ari": None,
        "nmi": None,
        "num_active_prototypes": None,
        "assignment_entropy_normalized": None,
        **train_eval,
    }
    return local_logits, record


def _fit_multi_env_field(plan: ExperimentPlan, graph, field, *, train_env_ids: tuple[int, ...], observations: dict[int, torch.Tensor]):
    field = field.to(device=plan.device)
    objectives = [
        build_likelihood_objective(
            graph,
            observations[env],
            likelihood_objective=plan.likelihood_objective,
            observation_mode="full",
            aggregate_unique=plan.aggregate_unique,
            backend=plan.likelihood_backend,
            device=plan.device,
        )
        for env in train_env_ids
    ]
    optimizer = torch.optim.Adam(field.parameters(), lr=float(plan.training_cfg.get("lr", 0.05)))
    history = []
    for _ in range(int(plan.training_cfg.get("steps", 200))):
        optimizer.zero_grad(set_to_none=True)
        losses = [objective.loss(field.realized_logits_for_env(slot)) for slot, objective in enumerate(objectives)]
        nll = torch.stack(losses).mean()
        reg = field.regularization_loss()
        loss = nll + reg
        loss.backward()
        optimizer.step()
        history.append(float(nll.detach().cpu()))
    return {"field": field, "history": history}


def _evaluate_multi_env_model(
    plan: ExperimentPlan,
    graph,
    field,
    *,
    spec: dict[str, object],
    train_env_ids: tuple[int, ...],
    heldout_env_ids: tuple[int, ...],
    heldout_observations: dict[int, torch.Tensor],
    heldout_adaptation_observations: dict[int, torch.Tensor],
    teacher_logits: torch.Tensor,
    active_mass_threshold: float,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    train_logits = [field.realized_logits_for_env(slot) for slot in range(len(train_env_ids))]
    train_eval = _eval_envs(
        graph,
        train_logits,
        train_env_ids,
        heldout_observations,
        teacher_logits,
        backend=plan.likelihood_backend,
        aggregate_unique=plan.aggregate_unique,
    )
    recovery = _field_recovery_metrics(field, graph, active_mass_threshold=active_mass_threshold)
    heldout_transfer = {}
    if bool(spec.get("shared_assignment", True)) and hasattr(field, "assignment_probabilities"):
        S = field.assignment_probabilities().detach()
        heldout_transfer = _fit_heldout_alpha_transfer(
            plan,
            graph,
            S,
            heldout_env_ids=heldout_env_ids,
            adaptation_observations=heldout_adaptation_observations,
            heldout_observations=heldout_observations,
            teacher_logits=teacher_logits,
        )
    record = {
        **DISC12_AUDIT,
        "model": spec["model"],
        "condition": spec["name"],
        "shared_assignment": bool(spec.get("shared_assignment", True)),
        "synthetic_oracle_baseline": bool(spec.get("oracle", False)),
        "uses_hidden_omega_for_training": bool(spec.get("oracle", False)),
        "uses_hidden_omega_for_initialization": bool(spec.get("oracle", False)),
        "parameter_count": int(field.parameter_count),
        "env_alpha_train": _extract_env_alpha(field, train_env_ids),
        **recovery,
        **train_eval,
        **heldout_transfer,
        **(extra or {}),
    }
    return record


def _fit_heldout_alpha_transfer(
    plan: ExperimentPlan,
    graph,
    S: torch.Tensor,
    *,
    heldout_env_ids: tuple[int, ...],
    adaptation_observations: dict[int, torch.Tensor],
    heldout_observations: dict[int, torch.Tensor],
    teacher_logits: torch.Tensor,
) -> dict[str, object]:
    S = S.to(device=plan.device, dtype=plan.dtype)
    nlls = []
    deltas = []
    alphas = {}
    for env in heldout_env_ids:
        alpha = torch.nn.Parameter(torch.full((S.shape[1],), -5.5, dtype=plan.dtype, device=plan.device))
        objective = build_likelihood_objective(
            graph,
            adaptation_observations[env],
            likelihood_objective=plan.likelihood_objective,
            observation_mode="full",
            aggregate_unique=plan.aggregate_unique,
            backend=plan.likelihood_backend,
            device=plan.device,
        )
        optimizer = torch.optim.Adam([alpha], lr=float(plan.training_cfg.get("lr", 0.05)))
        for _ in range(int(plan.training_cfg.get("steps", 200))):
            optimizer.zero_grad(set_to_none=True)
            loss = objective.loss(S @ alpha)
            loss.backward()
            optimizer.step()
        logits = S @ alpha
        model_nll = exact_dem_nll(
            graph,
            logits,
            heldout_observations[env],
            aggregate_unique=plan.aggregate_unique,
            backend=plan.likelihood_backend,
        )
        oracle_nll = exact_dem_nll(
            graph,
            teacher_logits[:, env].to(device=logits.device, dtype=logits.dtype),
            heldout_observations[env],
            aggregate_unique=plan.aggregate_unique,
            backend=plan.likelihood_backend,
        )
        nlls.append(float(model_nll.detach().cpu()))
        deltas.append(float((model_nll - oracle_nll).detach().cpu()))
        alphas[str(env)] = [float(value) for value in alpha.detach().cpu().tolist()]
    return {
        "env_holdout_nll": _mean(nlls),
        "env_holdout_dNLL": _mean(deltas),
        "env_holdout_alpha": alphas,
        "env_holdout_transfer_protocol": "freeze_assignment_fit_alpha_only",
    }


def _eval_envs(
    graph,
    logits_by_slot: list[torch.Tensor],
    env_ids: tuple[int, ...],
    heldout_observations: dict[int, torch.Tensor],
    teacher_logits: torch.Tensor,
    *,
    backend: str,
    aggregate_unique: bool,
) -> dict[str, object]:
    nlls = []
    deltas = []
    per_env = {}
    for slot, env in enumerate(env_ids):
        logits = logits_by_slot[slot]
        obs = heldout_observations[env]
        model_nll = exact_dem_nll(graph, logits, obs, aggregate_unique=aggregate_unique, backend=backend)
        oracle_nll = exact_dem_nll(
            graph,
            teacher_logits[:, env].to(device=logits.device, dtype=logits.dtype),
            obs,
            aggregate_unique=aggregate_unique,
            backend=backend,
        )
        nll = float(model_nll.detach().cpu())
        delta = float((model_nll - oracle_nll).detach().cpu())
        nlls.append(nll)
        deltas.append(delta)
        per_env[str(env)] = {"heldout_nll": nll, "delta_nll_oracle": delta}
    return {
        "eval_env_ids": [int(env) for env in env_ids],
        "train_env_heldout_nll_mean": _mean(nlls),
        "train_env_delta_nll_oracle_mean": _mean(deltas),
        "heldout_mean_nll": _mean(nlls),
        "per_env_eval": per_env,
    }


def _mean_env_nll(graph, logits_by_slot: list[torch.Tensor], observations: list[torch.Tensor], *, backend: str, aggregate_unique: bool) -> float:
    values = [
        float(exact_dem_nll(graph, logits, obs, aggregate_unique=aggregate_unique, backend=backend).detach().cpu())
        for logits, obs in zip(logits_by_slot, observations)
    ]
    return _mean(values)


def _make_field_for_spec(plan: ExperimentPlan, graph, spec: dict[str, object], *, num_environments: int, seed: int):
    model = spec["model"]
    if model in {"single_env_free_assignment", "single_env_local_logit_init", "multi_env_shared_S_random_init", "multi_env_shared_S_DISC10_init"}:
        return MultiEnvSharedAssignmentField(
            graph.M,
            graph.O,
            num_environments,
            dtype=plan.dtype,
            seed=seed,
            assignment_entropy_weight=float(spec.get("assignment_entropy_weight", 0.0)),
            assignment_balance_weight=float(spec.get("assignment_balance_weight", 0.0)),
        )
    if model == "multi_env_independent_S_per_env":
        return MultiEnvIndependentAssignmentField(graph.M, graph.O, num_environments, dtype=plan.dtype, seed=seed)
    raise ValueError(f"unsupported DISC12 model {model!r}")


def _apply_initializer(field, *, spec: dict[str, object], local_logits: torch.Tensor) -> dict[str, object]:
    if not isinstance(field, MultiEnvSharedAssignmentField):
        return {
            "assignment_initializer": "random_parameter_init",
            "uses_hidden_omega_for_initialization": False,
            "init_labels": None,
        }
    if str(spec.get("initializer", "random")) == "DISC10_local_logit":
        init = initialize_shared_from_local_logits(field, local_logits, confidence=float(spec.get("initializer_confidence", 6.0)))
        return {
            "assignment_initializer": "DISC10_local_logit",
            "assignment_initializer_feature_family": "local_logit",
            "uses_hidden_omega_for_initialization": False,
            "init_labels": [int(value) for value in init.labels.tolist()],
        }
    return {
        "assignment_initializer": "random_parameter_init",
        "assignment_initializer_feature_family": None,
        "uses_hidden_omega_for_initialization": False,
        "init_labels": None,
    }


def _field_recovery_metrics(field, graph, *, active_mass_threshold: float) -> dict[str, object]:
    if isinstance(field, MultiEnvIndependentAssignmentField):
        return independent_assignment_recovery_metrics(
            field.assignment_probabilities(),
            graph.orbit_ids,
            active_mass_threshold=active_mass_threshold,
        )
    if hasattr(field, "assignment_probabilities"):
        return assignment_recovery_metrics(
            field.assignment_probabilities(),
            graph.orbit_ids,
            active_mass_threshold=active_mass_threshold,
        )
    return {"ari": None, "nmi": None, "num_active_prototypes": None, "assignment_entropy_normalized": None}


def _field_labels(field) -> list[int] | None:
    if isinstance(field, MultiEnvIndependentAssignmentField):
        labels = torch.argmax(field.assignment_probabilities()[0].detach().cpu(), dim=1)
        return [int(value) for value in labels.tolist()]
    if hasattr(field, "assignment_probabilities"):
        labels = torch.argmax(field.assignment_probabilities().detach().cpu(), dim=1)
        return [int(value) for value in labels.tolist()]
    return None


def _extract_env_alpha(field, env_ids: tuple[int, ...]) -> dict[str, list[float]] | None:
    alpha = getattr(field, "alpha", None)
    if alpha is None:
        gamma = getattr(field, "gamma", None)
        if gamma is None:
            return None
        values = gamma.detach().cpu()
    else:
        values = alpha.detach().cpu()
    return {
        str(env): [float(value) for value in values[slot].flatten().tolist()]
        for slot, env in enumerate(env_ids)
    }


def _assignment_movement_audit(init_labels: object, final_labels: object) -> dict[str, object]:
    if init_labels is None or final_labels is None:
        return {
            "assignment_movement_from_init": None,
            "init_final_assignment_nmi": None,
            "fraction_rows_changed": None,
        }
    left = torch.as_tensor(init_labels, dtype=torch.long)
    right = torch.as_tensor(final_labels, dtype=torch.long)
    changed = left != right
    return {
        "assignment_movement_from_init": float(changed.to(dtype=torch.float64).mean().item()),
        "init_final_assignment_nmi": assignment_nmi(left, right),
        "fraction_rows_changed": float(changed.to(dtype=torch.float64).mean().item()),
    }


def assignment_nmi(left: torch.Tensor, right: torch.Tensor) -> float:
    from scope_static.dem.metrics import normalized_mutual_info

    return normalized_mutual_info(left, right)


def _observable_health_penalty(metrics: dict[str, object], *, num_prototypes: int) -> float:
    active = int(metrics.get("num_active_prototypes") or 0)
    entropy = float(metrics.get("assignment_entropy_normalized") or 0.0)
    penalty = 0.05 * max(0, int(num_prototypes) - 1 - active)
    if entropy > 0.95:
        penalty += 0.02 * (entropy - 0.95)
    if bool(metrics.get("assignment_collapse", False)):
        penalty += 1.0
    return float(penalty)


def _environment_contrast_audit(alpha_by_env: torch.Tensor, logits_by_env: torch.Tensor) -> dict[str, object]:
    alpha = alpha_by_env.to(dtype=torch.float64)
    rates = torch.sigmoid(logits_by_env.to(dtype=torch.float64))
    prototype_std = alpha.std(dim=0, unbiased=False)
    return {
        "alpha_variation_norm": float((alpha - alpha.mean(dim=0, keepdim=True)).norm().item()),
        "between_env_rate_contrast": float((rates - rates.mean(dim=1, keepdim=True)).abs().mean().item()),
        "per_prototype_alpha_separation": [float(value) for value in prototype_std.tolist()],
        "mean_per_prototype_alpha_separation": float(prototype_std.mean().item()),
    }


def _sample_env_observations(graph, logits_by_env: torch.Tensor, *, shots: int, seed_base: int, env_ids: tuple[int, ...]) -> dict[int, torch.Tensor]:
    return {
        int(env): sample_observations_from_logits(
            graph,
            logits_by_env[:, int(env)],
            shots=int(shots),
            seed=int(seed_base) + int(env),
        )
        for env in env_ids
    }


def _condition_specs(cfg: dict[str, object]) -> list[dict[str, object]]:
    default = [
        {"model": "single_env_free_assignment", "name": "single_env_free_assignment", "multi_env": False, "initializer": "random"},
        {
            "model": "single_env_local_logit_init",
            "name": "single_env_local_logit_init",
            "multi_env": False,
            "initializer": "DISC10_local_logit",
        },
        {
            "model": "multi_env_independent_S_per_env",
            "name": "multi_env_independent_S_per_env",
            "multi_env": True,
            "initializer": "random",
            "shared_assignment": False,
        },
        {"model": "multi_env_shared_S_random_init", "name": "multi_env_shared_S_random_init", "multi_env": True, "initializer": "random"},
        {
            "model": "multi_env_shared_S_DISC10_init",
            "name": "multi_env_shared_S_DISC10_init",
            "multi_env": True,
            "initializer": "DISC10_local_logit",
        },
        {"model": "known_orbit_oracle_shared_S", "name": "known_orbit_oracle_shared_S", "oracle": True},
    ]
    raw = cfg.get("conditions", default)
    return [dict(item) for item in raw]


def _run_contrast_sweep(
    plan: ExperimentPlan,
    graph,
    *,
    cfg: dict[str, object],
    stage2a1_ceiling: dict[str, object],
    output: Path,
) -> dict[str, object]:
    sweep_cfg = dict(cfg.get("contrast_sweep", {}))
    if not bool(sweep_cfg.get("enabled", False)):
        return {"enabled": False, "rows": []}
    strengths = [float(value) for value in sweep_cfg.get("strengths", [1.0, 2.0, 4.0, 8.0, 16.0])]
    design = str(sweep_cfg.get("environment_design", "codebook"))
    train_env_ids = tuple(int(env) for env in cfg.get("train_env_ids", [0, 1, 2, 3]))
    heldout_env_ids = tuple(int(env) for env in cfg.get("heldout_env_ids", [4]))
    shot_budget = int(sweep_cfg.get("shot_budget", plan.shot_budgets[0]))
    validation_shots = int(sweep_cfg.get("validation_shots", shot_budget))
    heldout_shots = int(sweep_cfg.get("heldout_shots", plan.heldout_shots))
    adaptation_shots = int(sweep_cfg.get("heldout_env_adaptation_shots", shot_budget))
    restarts = int(sweep_cfg.get("restarts", cfg.get("restarts", 2)))
    active_mass_threshold = float(cfg.get("active_mass_threshold", 1.0))
    rows = []
    for strength in strengths:
        teacher = make_multi_env_teacher(
            graph,
            seed=int(cfg.get("teacher_seed", 0)),
            dtype=plan.dtype,
            contrast_strength=float(strength),
            design=design,
        )
        observations = _sample_env_observations(
            graph,
            teacher.logits_by_env,
            shots=shot_budget,
            seed_base=110_000 + int(100 * strength),
            env_ids=teacher.env_ids,
        )
        validation_observations = _sample_env_observations(
            graph,
            teacher.logits_by_env,
            shots=validation_shots,
            seed_base=120_000 + int(100 * strength),
            env_ids=teacher.env_ids,
        )
        heldout_observations = _sample_env_observations(
            graph,
            teacher.logits_by_env,
            shots=heldout_shots,
            seed_base=130_000 + int(100 * strength),
            env_ids=teacher.env_ids,
        )
        adaptation_observations = _sample_env_observations(
            graph,
            teacher.logits_by_env,
            shots=adaptation_shots,
            seed_base=140_000 + int(100 * strength),
            env_ids=teacher.env_ids,
        )
        local_logits, _local_record = _fit_local_full_per_env(
            plan,
            graph,
            train_env_ids=train_env_ids,
            train_observations=observations,
            validation_observations=validation_observations,
            heldout_observations=heldout_observations,
            teacher_logits=teacher.logits_by_env,
            active_mass_threshold=active_mass_threshold,
        )
        oracle = _fit_known_orbit_oracle(
            plan,
            graph,
            train_env_ids=train_env_ids,
            heldout_env_ids=heldout_env_ids,
            train_observations=observations,
            validation_observations=validation_observations,
            heldout_observations=heldout_observations,
            heldout_adaptation_observations=adaptation_observations,
            teacher_logits=teacher.logits_by_env,
            active_mass_threshold=active_mass_threshold,
        )
        selected, _outcomes = _fit_condition_restarts(
            plan,
            graph,
            spec={
                "model": "multi_env_shared_S_DISC10_init",
                "name": "contrast_sweep_shared_S_DISC10_init",
                "multi_env": True,
                "initializer": "DISC10_local_logit",
            },
            train_env_ids=train_env_ids,
            heldout_env_ids=heldout_env_ids,
            train_observations=observations,
            validation_observations=validation_observations,
            heldout_observations=heldout_observations,
            heldout_adaptation_observations=adaptation_observations,
            teacher_logits=teacher.logits_by_env,
            local_logits_by_train_env=local_logits,
            restarts=restarts,
            active_mass_threshold=active_mass_threshold,
        )
        _add_known_orbit_deltas([selected, oracle])
        contrast = _environment_contrast_audit(teacher.alpha_by_env, teacher.logits_by_env)
        rate_singular_values = _rate_singular_values(teacher.logits_by_env)
        row = {
            "experiment": "DISC12b_multi_env_contrast_sweep",
            "environment_design": design,
            "contrast_strength": float(strength),
            "between_env_rate_contrast": contrast["between_env_rate_contrast"],
            "mean_per_prototype_alpha_separation": contrast["mean_per_prototype_alpha_separation"],
            "alpha_variation_norm": contrast["alpha_variation_norm"],
            "rate_singular_values": rate_singular_values,
            "ari": selected.get("ari"),
            "nmi": selected.get("nmi"),
            "delta_nll_known_orbit": selected.get("delta_nll_known_orbit"),
            "env_holdout_dNLL": selected.get("env_holdout_dNLL"),
            "num_active_prototypes": selected.get("num_active_prototypes"),
            "assignment_movement_from_init": selected.get("assignment_movement_from_init"),
            "disc12b_result": _classify_disc12(
                {
                    "ari": selected.get("ari"),
                    "nmi": selected.get("nmi"),
                    "delta_nll_known_orbit": selected.get("delta_nll_known_orbit"),
                    "num_active_prototypes": selected.get("num_active_prototypes"),
                },
                threshold_epsilon=plan.threshold_epsilon,
                stage2a1_ceiling=stage2a1_ceiling,
                num_prototypes=graph.O,
            ),
        }
        rows.append(row)
    result = {
        "enabled": True,
        "experiment": "DISC12b_multi_env_contrast_sweep",
        "question": "Does quotient recovery improve monotonically when environment-induced observable contrast increases?",
        "environment_design": design,
        "rows": rows,
        "decision": _contrast_sweep_decision(rows),
        "calibration_warning": _contrast_sweep_calibration_warning(rows),
    }
    (output / "contrast_sweep.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def _rate_singular_values(logits_by_env: torch.Tensor) -> list[float]:
    rates = torch.sigmoid(logits_by_env.to(dtype=torch.float64))
    centered = rates - rates.mean(dim=1, keepdim=True)
    try:
        values = torch.linalg.svdvals(centered)
    except RuntimeError:
        values = torch.empty((0,), dtype=torch.float64)
    return [float(value) for value in values.tolist()]


def _contrast_sweep_decision(rows: list[dict[str, object]]) -> str:
    if not rows:
        return "not_run"
    contrasts = [_float_or_none(row.get("between_env_rate_contrast")) or 0.0 for row in rows]
    aris = [_float_or_none(row.get("ari")) or 0.0 for row in rows]
    nmis = [_float_or_none(row.get("nmi")) or 0.0 for row in rows]
    contrast_increases = contrasts[-1] > contrasts[0] * 1.5 if contrasts[0] > 0 else contrasts[-1] > contrasts[0]
    recovery_increases = max(aris) > aris[0] + 0.10 or max(nmis) > nmis[0] + 0.10
    high_contrast = max(contrasts) > 0.01
    if contrast_increases and recovery_increases:
        return "recovery_increases_with_observable_contrast"
    if contrast_increases and not recovery_increases and high_contrast:
        return "high_observable_contrast_but_recovery_still_low"
    if not contrast_increases:
        return "environment_generator_failed_to_increase_observable_contrast"
    return "contrast_increases_but_recovery_gain_is_weak"


def _contrast_sweep_calibration_warning(rows: list[dict[str, object]]) -> str | None:
    if any((_float_or_none(row.get("env_holdout_dNLL")) or 0.0) > 0.05 for row in rows):
        return "high_contrast_rows_degrade_heldout_environment_transfer"
    if any((_float_or_none(row.get("delta_nll_known_orbit")) or 0.0) < -0.05 for row in rows):
        return "high_contrast_rows_show_unstable_oracle_delta_estimates_check_sampling_and_calibration"
    return None


def _add_known_orbit_deltas(records: list[dict[str, object]]) -> None:
    oracle = next((record for record in records if record.get("model") == "known_orbit_oracle_shared_S"), None)
    oracle_by_env = {} if oracle is None else dict(oracle.get("per_env_eval", {}))
    for record in records:
        eval_env_ids = [str(env) for env in record.get("eval_env_ids", [])]
        oracle_values = [
            float(oracle_by_env[env]["heldout_nll"])
            for env in eval_env_ids
            if env in oracle_by_env and oracle_by_env[env].get("heldout_nll") is not None
        ]
        oracle_nll = _mean(oracle_values) if oracle_values else None
        record["known_orbit_oracle_model"] = "known_orbit_oracle_shared_S"
        record["known_orbit_oracle_heldout_nll"] = oracle_nll
        record["known_orbit_oracle_available"] = oracle_nll is not None
        record["delta_nll_known_orbit"] = (
            None if oracle_nll is None or record.get("heldout_mean_nll") is None else float(record["heldout_mean_nll"] - oracle_nll)
        )


def _disc12_important_results(records: list[dict[str, object]], *, threshold_epsilon: float, stage2a1_ceiling: dict[str, object], num_prototypes: int) -> dict[str, object]:
    rows = []
    for record in records:
        row = {
            "model": record.get("model"),
            "condition": record.get("condition"),
            "ari": record.get("ari"),
            "nmi": record.get("nmi"),
            "num_active_prototypes": record.get("num_active_prototypes"),
            "assignment_entropy_normalized": record.get("assignment_entropy_normalized"),
            "delta_nll_known_orbit": record.get("delta_nll_known_orbit"),
            "env_holdout_dNLL": record.get("env_holdout_dNLL"),
            "selection_score": record.get("selection_score"),
            "ari_nmi_used_for_selection": False,
        }
        row["disc12_result"] = _classify_disc12(
            row,
            threshold_epsilon=threshold_epsilon,
            stage2a1_ceiling=stage2a1_ceiling,
            num_prototypes=num_prototypes,
        )
        rows.append(row)
    return {
        "schema": "scope_static_stage2a2_disc12_important_results_v1",
        "acceptance_categories": {
            "strong_recovery": "ARI/NMI >= 0.80, active >= K - 1, dNLL_known small, no ARI/NMI selection",
            "partial_recovery": "ARI/NMI clearly improve over Stage 2A.1 ceiling but miss strong threshold",
            "predictive_only": "NLL improves while ARI remains low",
            "failure": "no meaningful recovery or likelihood benefit",
        },
        "stage2a1_ceiling": stage2a1_ceiling,
        "model_summary": rows,
    }


def _classify_disc12(row: dict[str, object], *, threshold_epsilon: float, stage2a1_ceiling: dict[str, object], num_prototypes: int) -> str:
    ari = _float_or_none(row.get("ari"))
    nmi = _float_or_none(row.get("nmi"))
    delta = _float_or_none(row.get("delta_nll_known_orbit"))
    active = _float_or_none(row.get("num_active_prototypes"))
    if ari is not None and nmi is not None and ari >= 0.80 and nmi >= 0.80 and active is not None and active >= num_prototypes - 1 and delta is not None and delta <= threshold_epsilon:
        return "strong_recovery"
    if ari is not None and nmi is not None:
        if ari >= float(stage2a1_ceiling.get("ari", 0.0)) + 0.10 or nmi >= float(stage2a1_ceiling.get("nmi", 0.0)) + 0.10:
            return "partial_recovery"
    if delta is not None and delta <= threshold_epsilon:
        return "predictive_only"
    return "failure"


def _write_artifacts(output: Path, result: dict[str, object], records: list[dict[str, object]], restarts: list[dict[str, object]]) -> None:
    (output / "metrics.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (output / "disc12_summary.md").write_text(format_disc12_summary_markdown(result))
    if result.get("contrast_sweep", {}).get("enabled"):
        (output / "contrast_sweep.json").write_text(json.dumps(result["contrast_sweep"], indent=2, sort_keys=True) + "\n")
    shared = {
        record["model"]: {
            "hard_assignment_labels": record.get("hard_assignment_labels"),
            "prototype_masses": record.get("prototype_masses"),
            "ari": record.get("ari"),
            "nmi": record.get("nmi"),
        }
        for record in records
        if record.get("hard_assignment_labels") is not None
    }
    (output / "shared_assignment.json").write_text(json.dumps(shared, indent=2, sort_keys=True) + "\n")
    env_alpha = {
        record["model"]: {
            "train": record.get("env_alpha_train"),
            "heldout_transfer": record.get("env_holdout_alpha"),
        }
        for record in records
        if record.get("env_holdout_alpha") is not None or record.get("env_alpha_train") is not None
    }
    (output / "env_alpha.json").write_text(json.dumps(env_alpha, indent=2, sort_keys=True) + "\n")
    (output / "run_selection_audit.json").write_text(json.dumps({"restart_records": restarts}, indent=2, sort_keys=True) + "\n")


def format_disc12_summary_markdown(result: dict[str, object]) -> str:
    lines = [
        "# DISC12 Multi-Environment Shared Assignment",
        "",
        f"- Metrics: `{Path(result['output_dir']) / 'metrics.json'}`",
        f"- Train envs: `{result['train_env_ids']}`",
        f"- Heldout envs: `{result['heldout_env_ids']}`",
        f"- Stage label: `{result.get('disc12a_stage_label')}`",
        f"- ARI/NMI used for selection: `{str(result['ari_nmi_used_for_selection']).lower()}`",
        "",
        "| model | ARI | NMI | active | dNLL known | env holdout dNLL | result |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in result["disc12_important_results"]["model_summary"]:
        lines.append(
            f"| {row['model']} | {_fmt(row['ari'])} | {_fmt(row['nmi'])} | {_fmt(row['num_active_prototypes'])} | "
            f"{_fmt(row['delta_nll_known_orbit'])} | {_fmt(row['env_holdout_dNLL'])} | {row['disc12_result']} |"
        )
    lines.extend(["", "## Environment Contrast Audit", "", "```json", json.dumps(result["environment_contrast_audit"], indent=2), "```", ""])
    sweep = result.get("contrast_sweep", {})
    if isinstance(sweep, dict) and sweep.get("enabled"):
        lines.extend(
            [
                "",
                "## DISC12b Contrast Sweep",
                "",
                f"- Decision: `{sweep.get('decision')}`",
                f"- Calibration warning: `{sweep.get('calibration_warning')}`",
                "",
                "| strength | rate contrast | alpha sep | ARI | NMI | dNLL known | env dNLL | result |",
                "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for row in sweep.get("rows", []):
            lines.append(
                f"| {_fmt(row.get('contrast_strength'))} | {_fmt(row.get('between_env_rate_contrast'))} | "
                f"{_fmt(row.get('mean_per_prototype_alpha_separation'))} | {_fmt(row.get('ari'))} | "
                f"{_fmt(row.get('nmi'))} | {_fmt(row.get('delta_nll_known_orbit'))} | "
                f"{_fmt(row.get('env_holdout_dNLL'))} | {row.get('disc12b_result')} |"
            )
        lines.append("")
    return "\n".join(lines)


def format_disc12_terminal_summary(result: dict[str, object]) -> str:
    lines = [
        "Stage 2A.2 DISC12 Multi-Environment Summary",
        f"config: {result.get('config_path')}",
        f"output: {result.get('output_dir')}",
        f"metrics: {Path(str(result.get('output_dir'))) / 'metrics.json'}",
        "selection: validation_nll_plus_observable_health | ARI/NMI evaluator-only",
        "",
        "model                               ARI     NMI     active  dNLL_known  env_dNLL  result",
        "----------------------------------  ------  ------  ------  ----------  --------  ----------------",
    ]
    for row in result["disc12_important_results"]["model_summary"]:
        lines.append(
            f"{str(row['model']):<34}  {_fmt(row['ari']):>6}  {_fmt(row['nmi']):>6}  "
            f"{_fmt(row['num_active_prototypes']):>6}  {_fmt(row['delta_nll_known_orbit']):>10}  "
            f"{_fmt(row['env_holdout_dNLL']):>8}  {row['disc12_result']}"
        )
    return "\n".join(lines)


def _mean(values: list[object]) -> float:
    floats = [float(value) for value in values if value is not None]
    return float(sum(floats) / len(floats)) if floats else 0.0


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _fmt(value: object) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.4g}"
    except (TypeError, ValueError):
        return str(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Stage 2A.2 DISC12 multi-environment shared assignment.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args(argv)
    run_multi_env_discovery(args.config, output_dir=args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
