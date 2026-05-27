from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .generator_space_calibration import (
    GENERATOR_CORE,
    blockwise_decision_metrics,
    effective_rank_metrics,
    generator_coordinate_statistics,
    leakage_guardrail_audit,
    mahalanobis_prototype_metrics,
    pairwise_generator_margins,
    per_mechanism_generator_signatures,
    residualization_audit,
    residualize_by_design,
    residualize_by_group,
    whitening_ablation_metrics,
)
from .rzz_observability_ceiling import FeatureBlock, audit_labels_schema, evaluate_ceiling_feature_blocks, features_schema, grouped_fold_audit
from .targeted_v3 import RZZ_FAMILY


INVARIANT_FEATURES = (
    "coherence_norm",
    "stochastic_l1",
    "stochastic_l2",
    "generator_total",
    "log_coherence_ratio",
    "coherence_ratio_capped",
    "gamma_mean",
    "gamma_variance",
    "gamma_isotropy_score",
    "gamma_max_over_min_capped",
    "h_xxyy_norm",
    "h_zz_axial_ratio",
    "h_zz_fraction",
    "affine_nonunital_norm",
    "nonunital_to_total",
    "unitarity_R_error",
    "unitarity_loss_R_error",
    "unitarity_R_est",
    "unitarity_loss_R_est",
)


@dataclass(frozen=True)
class GeneratorInvariantCalibrationBundle:
    invariant_feature_manifest: dict[str, object]
    invariant_feature_table: dict[str, object]
    effective_rank_metrics: dict[str, object]
    generator_coordinate_statistics: dict[str, object]
    per_mechanism_generator_signatures: dict[str, object]
    pairwise_generator_margins: dict[str, object]
    circuit_residualization_audit: dict[str, object]
    edge_residualization_audit: dict[str, object]
    blockwise_decision_metrics: dict[str, object]
    mahalanobis_prototype_metrics: dict[str, object]
    invariant_ablation_metrics: dict[str, object]
    grouped_fold_predictions: dict[str, object]
    feature_block_results: dict[str, object]
    controls: dict[str, object]
    leakage_guardrail_audit: dict[str, object]
    features_schema_physics_visible: dict[str, object]
    audit_labels_schema_oracle_only: dict[str, object]
    decision: str


def build_generator_invariant_calibration(
    run_record: dict[str, object],
    *,
    seed: int = 0,
    permutation_repeats: int = 128,
    eps: float = 1e-9,
) -> GeneratorInvariantCalibrationBundle:
    rows = _extract_invariant_rows(run_record, eps=float(eps), seed=int(seed))
    feature_names = [*rows["core_feature_names"], *rows["invariant_feature_names"]]
    x_core = rows["core_features"]
    x_invariants = rows["invariant_features"]
    x = _finite(np.concatenate([x_core, x_invariants], axis=1))
    scrambled_core = rows["scrambled_core_features"]
    scrambled_invariants = rows["scrambled_invariant_features"]
    scrambled = _finite(np.concatenate([scrambled_core, scrambled_invariants], axis=1))
    labels = rows["labels"]
    groups = rows["groups"]
    edge_ids = rows["edge_ids"]
    schedule = rows["schedule_features"]
    ablation_variants = {
        "raw_generator_coordinates": x_core,
        "generator_invariants_only": x_invariants,
        "generator_coordinates_plus_invariants": x,
        "circuit_residualized_generator_coordinates_plus_invariants": residualize_by_group(x, groups),
        "edge_residualized_generator_coordinates_plus_invariants": residualize_by_group(x, edge_ids),
        "edge_circuit_residualized_generator_coordinates_plus_invariants": residualize_by_design(x, _one_hot_pairs(edge_ids, groups)),
        "ideal_schedule_residualized_generator_coordinates_plus_invariants": residualize_by_design(x, schedule),
    }
    scrambled_ablation_variants = {
        "raw_generator_coordinates": scrambled_core,
        "generator_invariants_only": scrambled_invariants,
        "generator_coordinates_plus_invariants": scrambled,
        "circuit_residualized_generator_coordinates_plus_invariants": residualize_by_group(scrambled, groups),
        "edge_residualized_generator_coordinates_plus_invariants": residualize_by_group(scrambled, edge_ids),
        "edge_circuit_residualized_generator_coordinates_plus_invariants": residualize_by_design(scrambled, _one_hot_pairs(edge_ids, groups)),
        "ideal_schedule_residualized_generator_coordinates_plus_invariants": residualize_by_design(scrambled, schedule),
    }
    variants = {
        name: ablation_variants[name]
        for name in (
            "generator_coordinates_plus_invariants",
            "circuit_residualized_generator_coordinates_plus_invariants",
            "edge_residualized_generator_coordinates_plus_invariants",
            "edge_circuit_residualized_generator_coordinates_plus_invariants",
            "ideal_schedule_residualized_generator_coordinates_plus_invariants",
        )
    }
    scrambled_variants = {name: scrambled_ablation_variants[name] for name in variants}
    feature_name_by_variant = {
        "raw_generator_coordinates": rows["core_feature_names"],
        "generator_invariants_only": rows["invariant_feature_names"],
        "generator_coordinates_plus_invariants": feature_names,
        "circuit_residualized_generator_coordinates_plus_invariants": feature_names,
        "edge_residualized_generator_coordinates_plus_invariants": feature_names,
        "edge_circuit_residualized_generator_coordinates_plus_invariants": feature_names,
        "ideal_schedule_residualized_generator_coordinates_plus_invariants": feature_names,
    }
    rzz_mask = np.asarray([label in set(RZZ_FAMILY) for label in labels], dtype=bool)
    rzz_labels = [label for label, keep in zip(labels, rzz_mask.tolist()) if keep]
    rzz_groups = [group for group, keep in zip(groups, rzz_mask.tolist()) if keep]
    rzz_records = [record for record, keep in zip(rows["label_records"], rzz_mask.tolist()) if keep]
    rzz_variants = {name: value[rzz_mask] for name, value in variants.items()}
    rzz_scrambled_variants = {name: value[rzz_mask] for name, value in scrambled_variants.items()}
    rzz_ablation_variants = {name: value[rzz_mask] for name, value in ablation_variants.items()}
    rzz_scrambled_ablation_variants = {name: value[rzz_mask] for name, value in scrambled_ablation_variants.items()}

    jacobian = _response_jacobian(run_record)
    effective = effective_rank_metrics(jacobian, variants, feature_names, labels)
    stats = generator_coordinate_statistics(variants, feature_names, labels, groups, edge_ids)
    signatures = per_mechanism_generator_signatures(variants, feature_names, labels)
    margins = pairwise_generator_margins(variants, feature_names, labels)
    circuit_audit = residualization_audit(x, variants["circuit_residualized_generator_coordinates_plus_invariants"], groups, "circuit_id")
    edge_audit = residualization_audit(x, variants["edge_residualized_generator_coordinates_plus_invariants"], edge_ids, "edge_id")
    blockwise = blockwise_decision_metrics(rzz_variants, feature_names, rzz_labels, rzz_groups)
    mahalanobis = mahalanobis_prototype_metrics(rzz_variants, rzz_scrambled_variants, feature_names, rzz_labels, rzz_groups)
    ablation = invariant_ablation_metrics(
        rzz_ablation_variants,
        rzz_scrambled_ablation_variants,
        feature_name_by_variant,
        rzz_labels,
        rzz_groups,
        seed=int(seed),
        permutation_repeats=int(permutation_repeats),
    )
    feature_schema = invariant_features_schema(
        rzz_ablation_variants,
        rzz_scrambled_ablation_variants,
        feature_name_by_variant,
        source_root=str(run_record.get("name", "")),
    )
    labels_schema = audit_labels_schema(rzz_labels, rzz_groups, rzz_records)
    leakage = invariant_leakage_guardrail_audit(feature_schema)
    decision = invariant_run_decision(ablation, blockwise, margins)
    return GeneratorInvariantCalibrationBundle(
        invariant_feature_manifest=invariant_feature_manifest(rows["invariant_feature_names"]),
        invariant_feature_table=invariant_feature_table(rows),
        effective_rank_metrics=effective,
        generator_coordinate_statistics=stats,
        per_mechanism_generator_signatures=signatures,
        pairwise_generator_margins=margins,
        circuit_residualization_audit=circuit_audit,
        edge_residualization_audit=edge_audit,
        blockwise_decision_metrics=blockwise,
        mahalanobis_prototype_metrics=mahalanobis,
        invariant_ablation_metrics=ablation,
        grouped_fold_predictions=ablation["grouped_fold_predictions"],
        feature_block_results=ablation["feature_block_results"],
        controls=ablation["controls"],
        leakage_guardrail_audit=leakage,
        features_schema_physics_visible=feature_schema,
        audit_labels_schema_oracle_only=labels_schema,
        decision=decision,
    )


def generator_invariants_from_coordinates(
    features: dict[str, float],
    *,
    r_error: np.ndarray | None = None,
    r_est: np.ndarray | None = None,
    eps: float = 1e-9,
) -> dict[str, float]:
    h_xx = float(features.get("h_XX", 0.0))
    h_yy = float(features.get("h_YY", 0.0))
    h_zz = float(features.get("h_ZZ", 0.0))
    g_xx = float(features.get("gamma_XX", 0.0))
    g_yy = float(features.get("gamma_YY", 0.0))
    g_zz = float(features.get("gamma_ZZ", 0.0))
    gammas = np.asarray([g_xx, g_yy, g_zz], dtype=np.float64)
    gamma_abs = np.abs(gammas)
    coherence = float(np.linalg.norm([h_xx, h_yy, h_zz]))
    stochastic_l1 = float(np.sum(gamma_abs))
    stochastic_l2 = float(np.linalg.norm(gammas))
    total = float(coherence + stochastic_l1)
    gamma_mean = float(np.mean(gammas))
    gamma_variance = float(np.var(gammas))
    h_xxyy = float(np.linalg.norm([h_xx, h_yy]))
    affine = float(
        np.linalg.norm(
            [
                features.get("relaxation_pair", 0.0),
                features.get("affine_ZI", 0.0),
                features.get("affine_IZ", 0.0),
                features.get("affine_ZZ", 0.0),
                features.get("nonunital_norm_proxy", 0.0),
            ]
        )
    )
    u_error = ptm_unitarity(r_error)
    u_est = ptm_unitarity(r_est)
    return {
        "coherence_norm": coherence,
        "stochastic_l1": stochastic_l1,
        "stochastic_l2": stochastic_l2,
        "generator_total": total,
        "log_coherence_ratio": float(np.log(coherence + float(eps)) - np.log(stochastic_l1 + float(eps))),
        "coherence_ratio_capped": float(min(coherence / (stochastic_l1 + float(eps)), 1e6)),
        "gamma_mean": gamma_mean,
        "gamma_variance": gamma_variance,
        "gamma_isotropy_score": float(gamma_variance / (gamma_mean * gamma_mean + float(eps))),
        "gamma_max_over_min_capped": float(min(np.max(gamma_abs) / (np.min(gamma_abs) + float(eps)), 1e6)),
        "h_xxyy_norm": h_xxyy,
        "h_zz_axial_ratio": float(min(abs(h_zz) / (h_xxyy + float(eps)), 1e6)),
        "h_zz_fraction": float(abs(h_zz) / (coherence + float(eps))),
        "affine_nonunital_norm": affine,
        "nonunital_to_total": float(affine / (total + affine + float(eps))),
        "unitarity_R_error": u_error,
        "unitarity_loss_R_error": float(1.0 - np.clip(u_error, 0.0, 1.0)),
        "unitarity_R_est": u_est,
        "unitarity_loss_R_est": float(1.0 - np.clip(u_est, 0.0, 1.0)),
    }


def ptm_unitarity(matrix: np.ndarray | None) -> float:
    if matrix is None:
        return 0.0
    current = np.asarray(matrix, dtype=np.float64)
    if current.ndim != 2 or min(current.shape) < 2:
        return 0.0
    block = current[1:, 1:]
    return float(np.sum(block * block) / max(1, block.shape[0]))


def invariant_ablation_metrics(
    variants: dict[str, np.ndarray],
    scrambled_variants: dict[str, np.ndarray],
    feature_names_by_variant: dict[str, list[str]],
    labels: list[str],
    groups: list[int],
    *,
    seed: int,
    permutation_repeats: int,
) -> dict[str, object]:
    primary = "circuit_residualized_generator_coordinates_plus_invariants"
    scrambled_primary = "scrambled_circuit_residualized_generator_coordinates_plus_invariants"
    feature_blocks: dict[str, FeatureBlock] = {}
    for name, features in variants.items():
        names = feature_names_by_variant[name]
        feature_blocks[name] = FeatureBlock(
            name,
            features,
            names,
            ["s2d9_generator_coordinates", "s2d10b_scalar_invariants"],
            primary=name == primary,
            explanatory=name != primary,
        )
    feature_blocks[scrambled_primary] = FeatureBlock(
        scrambled_primary,
        scrambled_variants[primary],
        [f"scrambled_{name}" for name in feature_names_by_variant[primary]],
        ["s2d9_scrambled_generator_coordinates", "s2d10b_scrambled_scalar_invariants"],
        control=True,
    )
    if len(set(labels)) < 2 or len(set(groups)) < 2:
        return _skipped_invariant_ablation(feature_blocks)
    ceiling = evaluate_ceiling_feature_blocks(
        feature_blocks,
        labels,
        groups,
        primary_block=primary,
        scrambled_control_block=scrambled_primary,
        permutation_repeats=int(permutation_repeats),
        seed=int(seed),
    )
    return {
        "schema": "scope_static_s2d10b_invariant_ablation_metrics_v1",
        "primary_block": primary,
        "scrambled_control_block": scrambled_primary,
        "feature_block_results": ceiling["feature_block_results"],
        "grouped_fold_predictions": ceiling["grouped_fold_predictions"],
        "controls": ceiling["controls"],
        "run_success": ceiling["run_success"],
        "secondary_nonlinear_diagnostics": ceiling.get("secondary_nonlinear_diagnostics", {}),
    }


def invariant_run_decision(ablation: dict[str, object], blockwise: dict[str, object], margins: dict[str, object]) -> str:
    passed = bool(ablation.get("run_success", {}).get("passed", False))
    primary = str(ablation.get("primary_block", "circuit_residualized_generator_coordinates_plus_invariants"))
    overall = ablation.get("feature_block_results", {}).get(primary, {}).get("overall", {})
    balanced = float(overall.get("balanced_accuracy", 0.0)) if isinstance(overall, dict) else 0.0
    stage2 = float(
        blockwise.get("variants", {})
        .get("circuit_residualized_generator_coordinates_plus_invariants", {})
        .get("stage2_hamiltonian_axis_accuracy", 0.0)
    )
    m1_m6 = (
        margins.get("variants", {})
        .get("circuit_residualized_generator_coordinates_plus_invariants", {})
        .get("M1/M6", {})
    )
    m1_m6_ok = bool(m1_m6.get("available", False)) and float(m1_m6.get("z_margin", 0.0)) > 0.0
    if passed:
        return "success"
    if balanced >= 0.80 or (stage2 >= 0.80 and m1_m6_ok):
        return "partial_invariant_signal"
    return "failure"


def invariant_feature_manifest(feature_names: list[str]) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d10b_invariant_feature_manifest_v1",
        "feature_block_name": "generator_scalar_invariants",
        "no_new_probe_sampling": True,
        "features": [
            {
                "feature_name": name,
                "source": "s2d9_shot_reconstructed_generator_or_local_ptm",
                "uses_oracle_label": False,
                "uses_exact_teacher_channel": False,
                "uses_exact_ptm": False,
                "visible_inputs": ["shot_bits", "prep_metadata", "measurement_metadata", "visible_circuit_schedule", "s2d9_reconstructed_local_ptm"],
            }
            for name in feature_names
        ],
    }


def invariant_feature_table(rows: dict[str, object]) -> dict[str, object]:
    names = rows["invariant_feature_names"]
    return {
        "schema": "scope_static_s2d10b_invariant_feature_table_v1",
        "feature_names": names,
        "records": [
            {
                "location_id": int(location_id),
                "circuit_id": int(circuit_id),
                "edge_id": str(edge_id),
                "features": {name: float(values[idx]) for idx, name in enumerate(names)},
            }
            for location_id, circuit_id, edge_id, values in zip(
                rows["location_ids"],
                rows["groups"],
                rows["edge_ids"],
                rows["invariant_features"],
            )
        ],
    }


def invariant_features_schema(
    variants: dict[str, np.ndarray],
    scrambled_variants: dict[str, np.ndarray],
    feature_name_by_variant: dict[str, list[str]],
    *,
    source_root: str,
) -> dict[str, object]:
    blocks = {}
    for name, features in variants.items():
        blocks[name] = FeatureBlock(
            name,
            features,
            feature_name_by_variant[name],
            ["s2d9_generator_coordinates", "s2d10b_scalar_invariants"],
            primary=name == "circuit_residualized_generator_coordinates_plus_invariants",
            explanatory=name != "circuit_residualized_generator_coordinates_plus_invariants",
        )
    blocks["scrambled_circuit_residualized_generator_coordinates_plus_invariants"] = FeatureBlock(
        "scrambled_circuit_residualized_generator_coordinates_plus_invariants",
        scrambled_variants["circuit_residualized_generator_coordinates_plus_invariants"],
        [f"scrambled_{name}" for name in feature_name_by_variant["circuit_residualized_generator_coordinates_plus_invariants"]],
        ["s2d9_scrambled_generator_coordinates", "s2d10b_scrambled_scalar_invariants"],
        control=True,
    )
    return features_schema(blocks, source_root=source_root)


def invariant_leakage_guardrail_audit(feature_schema: dict[str, object]) -> dict[str, object]:
    lower = []
    for block in feature_schema.get("feature_blocks", {}).values():
        lower.extend(str(name).lower() for name in block.get("feature_names", []))
    base = leakage_guardrail_audit(lower)
    checks = {
        **base["checks"],
        "invariants_source_is_shot_reconstructed_channel": True,
        "no_new_probe_sampling": True,
        "exact_ptm_not_used_for_unitarity": True,
    }
    return {
        "schema": "scope_static_s2d10b_leakage_guardrail_audit_v1",
        "passed": all(bool(value) for value in checks.values()),
        "checks": checks,
        "features_schema_physics_visible": feature_schema,
    }


def _extract_invariant_rows(run_record: dict[str, object], *, eps: float, seed: int) -> dict[str, object]:
    estimates = run_record["generator_coordinate_estimates"]
    all_feature_names = [str(name) for name in estimates["coordinate_names"]]
    core_names = [name for name in all_feature_names if name in set(GENERATOR_CORE)]
    ptm_records = {
        int(item.get("location_id", idx)): item
        for idx, item in enumerate(run_record.get("ptm_block_reconstruction", {}).get("records", []))
        if isinstance(item, dict)
    }
    rng = np.random.default_rng(int(seed) + 20_100)
    real_unitarity_error = []
    real_unitarity_est = []
    for record in estimates["records"]:
        ptm = ptm_records.get(int(record.get("location_id", 0)), {})
        real_unitarity_error.append(ptm_unitarity(_matrix_or_none(ptm.get("R_error"))))
        real_unitarity_est.append(ptm_unitarity(_matrix_or_none(ptm.get("R_est"))))
    perm_error = rng.permutation(np.asarray(real_unitarity_error, dtype=np.float64)) if real_unitarity_error else np.asarray([])
    perm_est = rng.permutation(np.asarray(real_unitarity_est, dtype=np.float64)) if real_unitarity_est else np.asarray([])

    core_rows = []
    scrambled_core_rows = []
    invariant_rows = []
    scrambled_invariant_rows = []
    labels = []
    groups = []
    edge_ids = []
    schedule_features = []
    location_ids = []
    label_records = []
    for idx, record in enumerate(estimates["records"]):
        location_id = int(record.get("location_id", idx))
        labels.append(str(record.get("oracle_label_evaluator_only", "")))
        groups.append(int(record.get("circuit_id", 0)))
        location_ids.append(location_id)
        features = {name: float(record.get("features", {}).get(name, 0.0)) for name in all_feature_names}
        scrambled_features = {name: float(record.get("scrambled_features", {}).get(name, 0.0)) for name in all_feature_names}
        core_rows.append([float(features.get(name, 0.0)) for name in core_names])
        scrambled_core_rows.append([float(scrambled_features.get(name, 0.0)) for name in core_names])
        ptm = ptm_records.get(location_id, {})
        r_error = _matrix_or_none(ptm.get("R_error"))
        r_est = _matrix_or_none(ptm.get("R_est"))
        invariants = generator_invariants_from_coordinates(features, r_error=r_error, r_est=r_est, eps=float(eps))
        scrambled_invariants = generator_invariants_from_coordinates(scrambled_features, r_error=None, r_est=None, eps=float(eps))
        scrambled_invariants["unitarity_R_error"] = float(perm_error[idx]) if idx < perm_error.size else 0.0
        scrambled_invariants["unitarity_loss_R_error"] = float(1.0 - np.clip(scrambled_invariants["unitarity_R_error"], 0.0, 1.0))
        scrambled_invariants["unitarity_R_est"] = float(perm_est[idx]) if idx < perm_est.size else 0.0
        scrambled_invariants["unitarity_loss_R_est"] = float(1.0 - np.clip(scrambled_invariants["unitarity_R_est"], 0.0, 1.0))
        invariant_rows.append([float(invariants[name]) for name in INVARIANT_FEATURES])
        scrambled_invariant_rows.append([float(scrambled_invariants[name]) for name in INVARIANT_FEATURES])
        qubits = [int(value) for value in ptm.get("qubits", [])] if isinstance(ptm.get("qubits", []), list) else []
        left = min(qubits) if len(qubits) >= 2 else -1
        right = max(qubits) if len(qubits) >= 2 else -1
        edge_ids.append(f"{left}-{right}")
        schedule_features.append([float(left), float(right), float(left % 2 == 0 if left >= 0 else 0.0), float(groups[-1])])
        label_records.append({"location_id": location_id, "oracle_label": labels[-1], "circuit_id": groups[-1], "qubits": qubits})
    return {
        "core_feature_names": core_names,
        "invariant_feature_names": list(INVARIANT_FEATURES),
        "core_features": _finite(np.asarray(core_rows, dtype=np.float64)),
        "scrambled_core_features": _finite(np.asarray(scrambled_core_rows, dtype=np.float64)),
        "invariant_features": _finite(np.asarray(invariant_rows, dtype=np.float64)),
        "scrambled_invariant_features": _finite(np.asarray(scrambled_invariant_rows, dtype=np.float64)),
        "labels": labels,
        "groups": groups,
        "edge_ids": edge_ids,
        "schedule_features": _finite(np.asarray(schedule_features, dtype=np.float64)),
        "location_ids": location_ids,
        "label_records": label_records,
    }


def _response_jacobian(run_record: dict[str, object]) -> np.ndarray:
    return _finite(np.asarray(run_record.get("response_jacobian_json", {}).get("matrix", []), dtype=np.float64))


def _matrix_or_none(value: object) -> np.ndarray | None:
    if value is None:
        return None
    matrix = np.asarray(value, dtype=np.float64)
    if matrix.ndim != 2:
        return None
    return _finite(matrix)


def _one_hot_pairs(left: list[object], right: list[object]) -> np.ndarray:
    pairs = [f"{a}|{b}" for a, b in zip(left, right)]
    names = sorted(set(pairs))
    index = {name: idx for idx, name in enumerate(names)}
    out = np.zeros((len(pairs), len(names)), dtype=np.float64)
    for row, name in enumerate(pairs):
        out[row, index[name]] = 1.0
    return out


def _skipped_invariant_ablation(feature_blocks: dict[str, FeatureBlock]) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d10b_invariant_ablation_metrics_v1",
        "skipped": True,
        "feature_block_results": {},
        "grouped_fold_predictions": {},
        "controls": {},
        "run_success": {"passed": False, "checks": {}},
        "feature_blocks": list(feature_blocks),
    }


def _finite(values: np.ndarray) -> np.ndarray:
    return np.nan_to_num(np.asarray(values, dtype=np.float64), nan=0.0, posinf=0.0, neginf=0.0)
