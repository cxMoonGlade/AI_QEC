from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
from typing import Iterable, Mapping

import numpy as np
import yaml

from scope_static.dem.baselines import baseline_metadata
from scope_static.dem.metrics import normalized_mutual_info
from scope_static.google.s3_visible_common import _json_safe
from scope_static.google.s3_visible_surface_v2 import (
    FEATURE_NAMES,
    _PublicSignatureContext,
    _adequacy_report,
    _acceptance_audit,
    _block_indices,
    _detectors_for_region,
    _detectors_for_round_band,
    _feature_schema,
    _normalize_region_families,
    _normalize_round_bands,
    _signature_feature_row,
    forbidden_feature_audit_google_v2,
)
from scope_static.google.s4_bridge_surface import (
    _compare_stage4_bridge_contract_payloads,
    _file_digest,
    _load_mechanism_records,
    _load_observations,
    _matrix_digest,
    _record_google_shaped_observations,
    _record_logical_support,
    _shotblocks,
    _synthetic_detector_coords,
    _text_digest,
)

from .artifacts import load_json_object, load_stage3a_frozen_visible_features
from .google_transfer import _assign_to_source_centers
from .source_pretrain import _fit_attention_vq, _replay_metrics
from .stage4_artifacts import load_stage4_visible_matrix


STAGE_NAME = "Stage4_6_google_unit_controlled_source_expansion"
DEFAULT_OUTPUT_DIR = "outputs/scope_static/S4_bridge/S4_6_google_unit_source_expansion"
FREEZE_DIR_NAME = "S3A_protocol_freeze"
ASSIGNMENT_UNIT = "synthetic_public_syndrome_response_signature"

CONTROL_NAMES = (
    "control_public_context_only",
    "control_random_mixture_same_context",
    "control_shuffled_google_native_mode",
    "control_family_bucket_shuffled",
    "control_no_visible_transform",
    "control_target_mean_std_only",
)

BASELINE_NAMES = (
    "dmle_qec_visible_marginal_mle",
)

FAMILY_BUCKETS = (
    "readout_spam",
    "prep_reset",
    "spatial_two_qubit_crosstalk",
    "temporal_stability_drift",
    "logical_tail_high_impact",
)


def run_stage4_google_unit_source_expansion(
    *,
    teacher_dir: str | Path,
    google_stage3a_dir: str | Path,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    assignment_geometry_dir: str | Path | None = None,
    source_pretrain_dir: str | Path | None = None,
    seed: int = 0,
    k: int = 32,
    shotblock_size: int = 16,
    max_source_shots_per_record: int | None = None,
    mixture_component_count: int = 3,
    design_fraction: float = 0.50,
    validation_fraction: float = 0.25,
    min_missing_mode_mass: float = 0.02,
) -> dict[str, object]:
    """Build a Google-unit synthetic source freeze plus split-clean S4.6 audits."""

    teacher = Path(teacher_dir)
    google_dir = Path(google_stage3a_dir)
    output = Path(output_dir)
    freeze = output / FREEZE_DIR_NAME
    output.mkdir(parents=True, exist_ok=True)
    freeze.mkdir(parents=True, exist_ok=True)

    records = _load_mechanism_records(teacher / "oracle_mechanisms.json")
    observations, probe_names, _shots = _load_observations(teacher / "observations.npz")
    google_raw, google_feature_names, google_manifest = load_stage3a_frozen_visible_features(google_dir)
    if list(google_feature_names) != list(FEATURE_NAMES):
        raise ValueError("Google V2 feature schema must match the public S3A V2 feature names")
    if observations.ndim != 3:
        raise ValueError("observations.npz observations must have shape [num_probes, shots, num_qubits]")
    if google_raw.ndim != 2 or google_raw.shape[0] <= 0:
        raise ValueError("Google Stage3A freeze must contain a non-empty visible feature matrix")

    split = _mode_design_split_manifest(
        row_count=int(google_raw.shape[0]),
        seed=int(seed),
        design_fraction=float(design_fraction),
        validation_fraction=float(validation_fraction),
    )
    google_public_rows = _google_public_signature_rows(google_dir, google_raw=google_raw, row_count=int(google_raw.shape[0]))
    source_codebook = _load_optional_source_codebook(source_pretrain_dir, feature_names=google_feature_names)
    assignment_baseline = _load_assignment_baseline(assignment_geometry_dir)
    mode_design = _design_google_unit_modes(
        google_raw=google_raw,
        design_indices=[int(idx) for idx in split["design"]],
        feature_names=google_feature_names,
        source_codebook=source_codebook,
        assignment_baseline=assignment_baseline,
        seed=int(seed),
        k=int(k),
        min_missing_mode_mass=float(min_missing_mode_mass),
    )
    bucket_records = _records_by_family_bucket(records)
    build = _build_google_unit_matrix(
        records=records,
        observations=observations,
        google_public_rows=google_public_rows,
        split=split,
        mode_design=mode_design,
        bucket_records=bucket_records,
        teacher=teacher,
        seed=int(seed),
        shotblock_size=int(shotblock_size),
        max_source_shots_per_record=_optional_positive_int(max_source_shots_per_record),
        mixture_component_count=max(1, int(mixture_component_count)),
        apply_surrogate_transforms=True,
    )
    no_transform = _build_google_unit_matrix(
        records=records,
        observations=observations,
        google_public_rows=google_public_rows,
        split=split,
        mode_design=mode_design,
        bucket_records=bucket_records,
        teacher=teacher,
        seed=int(seed),
        shotblock_size=int(shotblock_size),
        max_source_shots_per_record=_optional_positive_int(max_source_shots_per_record),
        mixture_component_count=max(1, int(mixture_component_count)),
        apply_surrogate_transforms=False,
    )

    matrix, source_visible_calibration = _calibrate_source_visible_surface_to_design_split(
        source_matrix=build.matrix,
        google_raw=google_raw,
        split=split,
        evaluator_records=build.evaluator_records,
        feature_names=google_feature_names,
    )
    sampled = matrix.copy()
    feature_schema = _stage4_google_unit_feature_schema()
    visible_feature_matrix = _visible_feature_matrix_manifest(matrix, sampled)
    split_manifest = _source_split_manifest(build.assignment_instances, split=split)
    forbidden = forbidden_feature_audit_google_v2(FEATURE_NAMES)
    adequacy = _adequacy_report(
        matrix,
        replicate_rows_by_unit=[row[None, :] for row in matrix],
        feature_names=list(FEATURE_NAMES),
        assignment_instances=build.assignment_instances,
        forbidden_audit=forbidden,
    )
    adequacy["surface_source"] = "synthetic_google_unit_controlled_source_mixture"
    adequacy["assignment_unit"] = ASSIGNMENT_UNIT
    freeze_acceptance = _acceptance_audit(
        forbidden_audit=forbidden,
        split_manifest=split_manifest,
        visible_feature_matrix=visible_feature_matrix,
        adequacy_report=adequacy,
    )
    source_public_signature_manifest = _source_public_signature_manifest(build.public_signature_records)
    source_mixture_label_manifest = _source_mixture_label_manifest()
    source_mixture_evaluator_labels = _source_mixture_evaluator_labels(build.evaluator_records)
    source_label_manifest = _source_label_manifest()
    source_evaluator_labels = _source_evaluator_labels_compat(build.evaluator_records)
    claim_boundary = _claim_boundary()
    schema_compatibility = _compare_stage4_bridge_contract_payloads(
        synthetic_dir=freeze,
        google_dir=google_dir,
        synthetic_schema=feature_schema,
        synthetic_manifest=visible_feature_matrix,
    )

    freeze_result = {
        "schema": "scope_static_stage4_google_unit_source_freeze_v1",
        "stage": STAGE_NAME,
        "output_dir": str(freeze),
        "teacher_dir": str(teacher),
        "google_stage3a_dir": str(google_dir),
        "assignment_unit": ASSIGNMENT_UNIT,
        "visible_feature_schema": feature_schema,
        "visible_feature_matrix": visible_feature_matrix,
        "split_manifest": split_manifest,
        "forbidden_feature_audit": forbidden,
        "adequacy_report": adequacy,
        "acceptance_audit": freeze_acceptance,
        "schema_compatibility_with_google_v2": schema_compatibility,
        "source_public_signature_manifest": source_public_signature_manifest,
        "source_mixture_label_manifest": source_mixture_label_manifest,
        "source_mixture_evaluator_labels": source_mixture_evaluator_labels,
        "source_label_manifest": source_label_manifest,
        "source_evaluator_labels": source_evaluator_labels,
        "claim_boundary": claim_boundary,
        "probe_schedule_manifest": _probe_schedule_manifest(probe_names),
        "signature_schedule_manifest": _signature_schedule_manifest(build.public_signature_records),
        "batch_context_schema": _batch_context_schema(row_count=int(matrix.shape[0])),
        "assignment_unit_manifest": _assignment_unit_manifest(row_count=int(matrix.shape[0]), source_record_count=len(records)),
        "config": {
            "teacher_dir": str(teacher),
            "google_stage3a_dir": str(google_dir),
            "assignment_geometry_dir": str(assignment_geometry_dir) if assignment_geometry_dir is not None else None,
            "source_pretrain_dir": str(source_pretrain_dir) if source_pretrain_dir is not None else None,
            "seed": int(seed),
            "k": int(k),
            "shotblock_size": int(shotblock_size),
            "max_source_shots_per_record": _optional_positive_int(max_source_shots_per_record),
            "mixture_component_count": int(max(1, mixture_component_count)),
            "design_fraction": float(design_fraction),
            "validation_fraction": float(validation_fraction),
            "min_missing_mode_mass": float(min_missing_mode_mass),
        },
        "decision": "stage4_google_unit_source_freeze_passed"
        if bool(freeze_acceptance.get("passed", False)) and bool(schema_compatibility.get("passed", False))
        else "stage4_google_unit_source_freeze_failed",
    }
    _write_freeze_outputs(freeze, freeze_result, matrix, sampled)

    controls = _control_matrices(
        main_matrix=matrix,
        no_transform_matrix=no_transform.matrix,
        google_raw=google_raw,
        split=split,
        build=build,
        seed=int(seed),
    )
    mode_design_audit = _mode_design_audit(split=split, mode_design=mode_design, source_codebook=source_codebook)
    surrogate_audit = _visible_surrogate_transform_audit(build.transform_counts, rows=int(matrix.shape[0]))
    surrogate_audit["source_visible_calibration"] = source_visible_calibration
    survival = _mixture_mode_survival_report(build.evaluator_records, mode_design=mode_design, split=split)
    coverage = _google_native_mode_coverage(
        source_matrix=matrix,
        google_raw=google_raw,
        split=split,
        mode_design=mode_design,
    )
    distance = _source_google_mode_distance(
        source_matrix=matrix,
        google_raw=google_raw,
        split=split,
        assignment_baseline=assignment_baseline,
    )
    transfer = _expanded_transfer_report(
        source_matrix=matrix,
        control_matrices=controls,
        google_raw=google_raw,
        split=split,
        feature_names=google_feature_names,
        seed=int(seed),
        k=int(k),
        assignment_baseline=assignment_baseline,
    )
    acceptance = _s4_6_acceptance(
        freeze_result=freeze_result,
        split=split,
        surrogate_audit=surrogate_audit,
        coverage=coverage,
        distance=distance,
        transfer=transfer,
        output_dir=output,
    )
    result = {
        "schema": "scope_static_stage4_google_unit_source_expansion_v1",
        "stage": STAGE_NAME,
        "output_dir": str(output),
        "freeze_dir": str(freeze),
        "teacher_dir": str(teacher),
        "google_stage3a_dir": str(google_dir),
        "assignment_geometry_dir": str(assignment_geometry_dir) if assignment_geometry_dir is not None else None,
        "source_pretrain_dir": str(source_pretrain_dir) if source_pretrain_dir is not None else None,
        "config": dict(freeze_result["config"]),
        "claim_boundary": claim_boundary,
        "mode_design_split_manifest": split,
        "mode_design_audit": mode_design_audit,
        "visible_surrogate_transform_audit": surrogate_audit,
        "source_visible_calibration_audit": source_visible_calibration,
        "mixture_mode_survival_report": survival,
        "google_native_mode_coverage": coverage,
        "source_google_mode_distance": distance,
        "expanded_transfer_report": transfer,
        "controls": _control_report(controls, transfer),
        "acceptance_audit": acceptance,
        "decision": "stage4_google_unit_source_expansion_passed" if acceptance["passed"] else "stage4_google_unit_source_expansion_failed",
    }
    _write_parent_outputs(output, result)
    return result


class _GoogleUnitBuild:
    def __init__(
        self,
        *,
        matrix: np.ndarray,
        assignment_instances: list[dict[str, object]],
        public_signature_records: list[dict[str, object]],
        evaluator_records: list[dict[str, object]],
        transform_counts: dict[str, int],
    ) -> None:
        self.matrix = matrix
        self.assignment_instances = assignment_instances
        self.public_signature_records = public_signature_records
        self.evaluator_records = evaluator_records
        self.transform_counts = transform_counts


def _build_google_unit_matrix(
    *,
    records: list[dict[str, object]],
    observations: np.ndarray,
    google_public_rows: list[dict[str, object]],
    split: Mapping[str, object],
    mode_design: Mapping[str, object],
    bucket_records: Mapping[str, list[int]],
    teacher: Path,
    seed: int,
    shotblock_size: int,
    max_source_shots_per_record: int | None,
    mixture_component_count: int,
    apply_surrogate_transforms: bool,
) -> _GoogleUnitBuild:
    detector_count = int(observations.shape[2])
    observable_count = 1
    coords = _synthetic_detector_coords(detector_count)
    boundary = {0, detector_count - 1} if detector_count > 1 else {0}
    rows: list[np.ndarray] = []
    assignment_instances: list[dict[str, object]] = []
    public_signature_records: list[dict[str, object]] = []
    evaluator_records: list[dict[str, object]] = []
    transform_counts: dict[str, int] = defaultdict(int)
    mode_specs = list(mode_design.get("mode_specs", []))
    design_mode_by_row = {
        int(row["google_row_index"]): dict(row)
        for row in mode_design.get("design_row_assignments", [])
        if isinstance(row, Mapping)
    }
    for row_index, public_row in enumerate(google_public_rows):
        public_fields = dict(public_row.get("public_fields", {})) if isinstance(public_row.get("public_fields", {}), Mapping) else {}
        split_name = str(_split_name_for_index(row_index, split))
        mode_spec = _mode_spec_for_row(
            row_index=row_index,
            split_name=split_name,
            public_fields=public_fields,
            mode_specs=mode_specs,
            design_mode_by_row=design_mode_by_row,
            seed=int(seed),
        )
        label_weights = _mixture_label_weights(
            records=records,
            bucket_records=bucket_records,
            bucket_weights=dict(mode_spec.get("bucket_weights", {})),
        )
        mixed = _mixed_observations_for_weights(
            records=records,
            observations=observations,
            label_weights=label_weights,
            seed=_stable_int({"row": row_index, "seed": seed, "mode": mode_spec.get("mode_id")}),
            max_source_shots=max_source_shots_per_record,
            component_count=int(mixture_component_count),
        )
        transform_kind = str(mode_spec.get("visible_transform", "none"))
        if apply_surrogate_transforms and transform_kind != "none":
            mixed = _apply_visible_surrogate_transform(
                mixed,
                transform_kind=transform_kind,
                seed=_stable_int({"row": row_index, "transform": transform_kind, "seed": seed}),
            )
            transform_counts[transform_kind] += 1
        else:
            transform_counts["none"] += 1
        logical_support = _mixture_logical_support(records, label_weights, detector_count=detector_count)
        row = _feature_row_for_public_signature(
            mixed,
            public_fields=public_fields,
            coords=coords,
            boundary_detectors=boundary,
            logical_support_detectors=logical_support,
            detector_count=detector_count,
            observable_count=observable_count,
            shotblock_size=int(shotblock_size),
        )
        google_visible_row = public_row.get("google_visible_features")
        if google_visible_row is not None:
            row = _override_public_geometry_from_google_visible(row, np.asarray(google_visible_row, dtype=np.float64))
        rows.append(row)
        row_payload = {
            "j": int(row_index),
            "record_index": int(row_index),
            "visible_instance_id": f"s4gunit{row_index:06d}",
            "context_group": int(row_index),
            "assignment_unit": ASSIGNMENT_UNIT,
            "unit_id_internal_only": f"synthetic_public_signature_unit_{row_index:06d}",
            "mode_design_split": split_name,
            "public_fields": public_fields,
            "source_assignment_unit": ASSIGNMENT_UNIT,
            "source_mixture_component_count": int(sum(1 for value in label_weights.values() if float(value) > 0.0)),
        }
        assignment_instances.append(row_payload)
        public_signature_records.append(
            {
                "row_id": int(row_index),
                "j": int(row_index),
                "assignment_unit": ASSIGNMENT_UNIT,
                "mode_design_split": split_name,
                "public_fields": public_fields,
            }
        )
        dominant_family = _dominant_family_from_bucket_weights(dict(mode_spec.get("bucket_weights", {})))
        evaluator_records.append(
            {
                "row_id": int(row_index),
                "j": int(row_index),
                "assignment_unit": ASSIGNMENT_UNIT,
                "google_row_index": int(row_index),
                "mode_design_split": split_name,
                "exact_mechanism_label": f"mixture:{dominant_family}",
                "quotient_label": str(mode_spec.get("visible_mode_tag", dominant_family)),
                "alias_label": str(mode_spec.get("alias_label", mode_spec.get("visible_mode_tag", dominant_family))),
                "dominant_family": dominant_family,
                "visible_mode_tag": str(mode_spec.get("visible_mode_tag", dominant_family)),
                "mixture_weights_by_mechanism_label": {key: float(value) for key, value in sorted(label_weights.items())},
                "mixture_weights_by_family_bucket": {
                    key: float(value) for key, value in sorted(dict(mode_spec.get("bucket_weights", {})).items())
                },
                "missing_mode_spec_id": str(mode_spec.get("mode_id", "mode_unspecified")),
                "uses_google_visible_data_to_design_source_modes": True,
                "used_for_training": False,
                "used_for_validation_selection": False,
                "teacher_config_hash": _file_digest(teacher / "teacher_config.json"),
            }
        )
    return _GoogleUnitBuild(
        matrix=np.asarray(rows, dtype=np.float64),
        assignment_instances=assignment_instances,
        public_signature_records=public_signature_records,
        evaluator_records=evaluator_records,
        transform_counts=dict(transform_counts),
    )


def _design_google_unit_modes(
    *,
    google_raw: np.ndarray,
    design_indices: list[int],
    feature_names: list[str],
    source_codebook: Mapping[str, object] | None,
    assignment_baseline: Mapping[str, object],
    seed: int,
    k: int,
    min_missing_mode_mass: float,
) -> dict[str, object]:
    design = np.asarray(google_raw[design_indices], dtype=np.float64)
    native_k = max(1, min(int(k), int(design.shape[0])))
    native = _fit_attention_vq(design, k=native_k, max_iter=25, code_dim=min(native_k, design.shape[1]))
    assignments = np.asarray(native["assignments"], dtype=np.int64)
    centers = np.asarray(native["centers"], dtype=np.float64)
    block_indices = _block_indices(feature_names)
    source_radius = _source_radius_from_baseline(assignment_baseline)
    source_distance_by_mode = _nearest_source_distance_by_mode(centers, source_codebook)
    mode_specs = []
    design_row_assignments = []
    counts = Counter(int(value) for value in assignments.tolist())
    for mode_id in range(native_k):
        mask = assignments == mode_id
        count = int(np.sum(mask))
        mass = float(count / max(1, int(assignments.size)))
        block_scores = _mode_block_scores(design, centers[int(mode_id)], block_indices=block_indices, mask=mask)
        dominant_block = max(block_scores.items(), key=lambda item: float(item[1]))[0] if block_scores else "raw__marginal"
        bucket = _bucket_for_visible_block(dominant_block)
        nearest = float(source_distance_by_mode.get(int(mode_id), np.inf))
        missing = bool(mass >= float(min_missing_mode_mass) and (not np.isfinite(nearest) or nearest > source_radius))
        spec = {
            "mode_id": f"GUM{mode_id:03d}",
            "google_native_mode": f"G{mode_id:03d}",
            "design_split_mass": mass,
            "design_row_count": count,
            "dominant_visible_block": dominant_block,
            "dominant_family_bucket": bucket,
            "bucket_weights": _bucket_weights_for_mode(bucket, missing=missing),
            "visible_transform": _visible_transform_for_bucket(bucket) if missing else "none",
            "visible_mode_tag": f"{bucket}_{'missing' if missing else 'covered'}",
            "alias_label": f"{bucket}_{'missing' if missing else 'covered'}",
            "nearest_source_code_distance": None if not np.isfinite(nearest) else nearest,
            "source_radius_threshold": source_radius,
            "selected_as_missing_mode": missing,
            "block_scores": {key: float(value) for key, value in sorted(block_scores.items())},
        }
        mode_specs.append(spec)
    if not mode_specs:
        mode_specs.append(_fallback_mode_spec())
    for local_idx, google_idx in enumerate(design_indices):
        mode = int(assignments[local_idx]) if assignments.size else 0
        design_row_assignments.append(
            {
                "google_row_index": int(google_idx),
                "design_local_index": int(local_idx),
                "mode_id": mode_specs[min(mode, len(mode_specs) - 1)]["mode_id"],
                "google_native_mode": f"G{mode:03d}",
            }
        )
    return {
        "schema": "scope_static_stage4_6_google_unit_mode_design_v1",
        "uses_google_visible_rows": "design_split_only",
        "uses_google_heldout_eval_rows": False,
        "design_indices": [int(idx) for idx in design_indices],
        "native_mode_count": int(native_k),
        "min_missing_mode_mass": float(min_missing_mode_mass),
        "mode_specs": mode_specs,
        "design_row_assignments": design_row_assignments,
        "native_centers": centers.tolist(),
        "source_radius_threshold": source_radius,
    }


def _mode_design_split_manifest(*, row_count: int, seed: int, design_fraction: float, validation_fraction: float) -> dict[str, object]:
    n = int(row_count)
    if n <= 0:
        raise ValueError("row_count must be positive")
    rng = np.random.default_rng(int(seed))
    order = np.arange(n, dtype=np.int64)
    rng.shuffle(order)
    if n >= 3:
        design_count = max(1, min(n - 2, int(round(float(design_fraction) * n))))
        validation_count = max(1, min(n - design_count - 1, int(round(float(validation_fraction) * n))))
    elif n == 2:
        design_count = 1
        validation_count = 1
    else:
        design_count = 1
        validation_count = 0
    design = sorted(int(idx) for idx in order[:design_count].tolist())
    validation = sorted(int(idx) for idx in order[design_count : design_count + validation_count].tolist())
    heldout = sorted(int(idx) for idx in order[design_count + validation_count :].tolist())
    checks = {
        "splits_are_disjoint": not (set(design) & set(validation) or set(design) & set(heldout) or set(validation) & set(heldout)),
        "design_non_empty": bool(design),
        "validation_non_empty": bool(validation),
        "heldout_eval_non_empty": bool(heldout),
        "missing_mode_selection_reads_design_only": True,
        "source_expansion_config_uses_design_plus_source_only": True,
        "final_transfer_reports_heldout_eval_only": True,
    }
    return {
        "schema": "scope_static_stage4_6_mode_design_split_manifest_v1",
        "split_policy": "deterministic_google_visible_design_validation_heldout_eval",
        "seed": int(seed),
        "row_count": n,
        "google_mode_design_split": design,
        "google_calibration_split": validation,
        "google_eval_split": heldout,
        "design": design,
        "validation": validation,
        "heldout_eval": heldout,
        "google_visible_indices_used_for_missing_mode_selection": design,
        "google_heldout_indices_used_for_missing_mode_selection": [],
        "checks": checks,
        "passed": bool(all(checks.values())) if n >= 3 else bool(checks["design_non_empty"]),
    }


def _google_public_signature_rows(google_dir: Path, *, google_raw: np.ndarray, row_count: int) -> list[dict[str, object]]:
    path = google_dir / "split_manifest.json"
    if path.exists():
        payload = load_json_object(path)
        rows = payload.get("assignment_instances", [])
        if isinstance(rows, list) and rows:
            out = []
            for idx in range(int(row_count)):
                row = dict(rows[idx]) if idx < len(rows) and isinstance(rows[idx], Mapping) else {}
                public = dict(row.get("public_fields", {})) if isinstance(row.get("public_fields", {}), Mapping) else {}
                out.append(
                    {
                        "google_row_index": idx,
                        "public_fields": _defaulted_public_fields(public),
                        "google_visible_features": np.asarray(google_raw[idx], dtype=np.float64),
                    }
                )
            return out
    return [
        {
            "google_row_index": idx,
            "public_fields": _defaulted_public_fields({}),
            "google_visible_features": np.asarray(google_raw[idx], dtype=np.float64),
        }
        for idx in range(int(row_count))
    ]


def _override_public_geometry_from_google_visible(row: np.ndarray, google_row: np.ndarray) -> np.ndarray:
    out = np.asarray(row, dtype=np.float64).copy()
    meta_indices = [idx for idx, name in enumerate(FEATURE_NAMES) if str(name).startswith("meta__public_geometry")]
    for idx in meta_indices:
        if idx < google_row.shape[0]:
            out[idx] = float(google_row[idx])
    return out


def _feature_row_for_public_signature(
    observations: np.ndarray,
    *,
    public_fields: Mapping[str, object],
    coords: dict[int, tuple[float, ...]],
    boundary_detectors: set[int],
    logical_support_detectors: set[int],
    detector_count: int,
    observable_count: int,
    shotblock_size: int,
) -> np.ndarray:
    context = _context_from_public_fields(public_fields)
    round_band = _safe_round_band(public_fields.get("round_band", "all"))
    region = _safe_region_family(public_fields.get("region_family", "full_patch"))
    round_detectors = _detectors_for_round_band(coords, detector_count=detector_count, round_band=round_band)
    region_detectors = _detectors_for_region(
        region,
        detector_count=detector_count,
        boundary_detectors=boundary_detectors,
        logical_support_detectors=logical_support_detectors,
        coords=coords,
    )
    selected = sorted(set(round_detectors).intersection(region_detectors)) or sorted(range(detector_count))
    row, _support = _signature_feature_row(
        observations,
        context=context,
        coords=coords,
        boundary_detectors=boundary_detectors,
        logical_support_detectors=logical_support_detectors,
        selected_detectors=selected,
        detector_count=detector_count,
        observable_count=observable_count,
        round_band=round_band,
        region_family=region,
        shotblocks=_shotblocks(observations.shape[0], max(1, int(shotblock_size))),
    )
    return np.asarray(row, dtype=np.float64)


def _mixed_observations_for_weights(
    *,
    records: list[dict[str, object]],
    observations: np.ndarray,
    label_weights: Mapping[str, float],
    seed: int,
    max_source_shots: int | None,
    component_count: int,
) -> np.ndarray:
    rng = np.random.default_rng(int(seed))
    label_to_record = {
        str(record.get("oracle_label", record.get("mechanism_id", f"M{idx}"))): idx for idx, record in enumerate(records)
    }
    selected = sorted(label_weights.items(), key=lambda item: float(item[1]), reverse=True)[: max(1, int(component_count))]
    total_weight = sum(float(weight) for _label, weight in selected) or 1.0
    components = []
    target_shots = max(8, min(256, int(observations.shape[1]) * max(1, int(len(selected)))))
    for label, weight in selected:
        record_idx = label_to_record.get(str(label), 0)
        local = _record_google_shaped_observations(records[record_idx], observations, max_source_shots=max_source_shots)
        take = max(1, int(round(target_shots * float(weight) / total_weight)))
        indices = rng.integers(0, max(1, local.shape[0]), size=take)
        components.append(local[indices])
    mixed = np.vstack(components) if components else _record_google_shaped_observations(records[0], observations, max_source_shots=max_source_shots)
    rng.shuffle(mixed, axis=0)
    return np.asarray(mixed, dtype=np.float64)


def _apply_visible_surrogate_transform(observations: np.ndarray, *, transform_kind: str, seed: int) -> np.ndarray:
    rng = np.random.default_rng(int(seed))
    out = np.asarray(observations, dtype=np.float64).copy()
    if out.ndim != 2 or out.shape[1] <= 1:
        return out
    detector_cols = out.shape[1] - 1
    detectors = out[:, :detector_cols]
    logical = out[:, detector_cols:]
    if transform_kind == "marginal_rate_add_drop":
        mask = rng.random(detectors.shape) < 0.08
        detectors[:, :] = np.mod(detectors + mask.astype(np.float64), 2.0)
    elif transform_kind == "correlated_pair_flip":
        if detector_cols >= 2:
            for col in range(detector_cols - 1):
                mask = rng.random(detectors.shape[0]) < 0.10
                detectors[mask, col] = 1.0 - detectors[mask, col]
                detectors[mask, col + 1] = 1.0 - detectors[mask, col + 1]
    elif transform_kind == "shotblock_rate_drift":
        half = max(1, detectors.shape[0] // 2)
        mask = rng.random(detectors[half:].shape) < 0.12
        detectors[half:, :] = np.mod(detectors[half:, :] + mask.astype(np.float64), 2.0)
    elif transform_kind == "logical_conditioned_detector_shape":
        if logical.size:
            conditioned = np.asarray(logical[:, 0] > 0.5, dtype=bool)
            detectors[conditioned, ::2] = 1.0 - detectors[conditioned, ::2]
    out[:, :detector_cols] = detectors
    return out


def _control_matrices(
    *,
    main_matrix: np.ndarray,
    no_transform_matrix: np.ndarray,
    google_raw: np.ndarray,
    split: Mapping[str, object],
    build: _GoogleUnitBuild,
    seed: int,
) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(int(seed))
    names = list(FEATURE_NAMES)
    meta_mask = np.asarray([name.startswith("meta__public_geometry") for name in names], dtype=bool)
    raw_mask = ~meta_mask
    controls: dict[str, np.ndarray] = {}
    public_only = np.asarray(main_matrix, dtype=np.float64).copy()
    raw_mean = np.mean(main_matrix[:, raw_mask], axis=0, keepdims=True) if np.any(raw_mask) else np.zeros((1, 0))
    public_only[:, raw_mask] = raw_mean
    controls["control_public_context_only"] = public_only
    random_mixture = np.asarray(main_matrix, dtype=np.float64).copy()
    perm = rng.permutation(random_mixture.shape[0])
    random_mixture[:, raw_mask] = random_mixture[perm][:, raw_mask]
    controls["control_random_mixture_same_context"] = random_mixture
    shuffled_mode = np.asarray(main_matrix, dtype=np.float64).copy()
    perm = rng.permutation(shuffled_mode.shape[0])
    shuffled_mode[:, raw_mask] = shuffled_mode[perm][:, raw_mask]
    controls["control_shuffled_google_native_mode"] = shuffled_mode
    family_shuffled = np.asarray(main_matrix, dtype=np.float64).copy()
    families = [str(row.get("dominant_family", "")) for row in build.evaluator_records]
    for family in sorted(set(families)):
        idx = [i for i, value in enumerate(families) if value == family]
        if len(idx) >= 2:
            shuffled = np.asarray(idx, dtype=np.int64)
            rng.shuffle(shuffled)
            row_idx = np.asarray(idx, dtype=np.int64)
            raw_cols = np.where(raw_mask)[0]
            family_shuffled[np.ix_(row_idx, raw_cols)] = family_shuffled[np.ix_(shuffled, raw_cols)]
    controls["control_family_bucket_shuffled"] = family_shuffled
    controls["control_no_visible_transform"] = np.asarray(no_transform_matrix, dtype=np.float64)
    controls["control_target_mean_std_only"] = _target_mean_std_only_control_matrix(
        google_raw=google_raw,
        split=split,
        row_count=int(main_matrix.shape[0]),
        seed=int(seed) + 1009,
    )
    return controls


def _target_mean_std_only_control_matrix(
    *,
    google_raw: np.ndarray,
    split: Mapping[str, object],
    row_count: int,
    seed: int,
) -> np.ndarray:
    """Build a moment-only control without preserving source row geometry."""

    target = np.asarray(google_raw, dtype=np.float64)
    design = [int(idx) for idx in split.get("design", [])]
    design_matrix = target[design] if design else target
    feature_count = int(target.shape[1]) if target.ndim == 2 else 0
    if int(row_count) <= 0 or feature_count <= 0:
        return np.zeros((max(0, int(row_count)), max(0, feature_count)), dtype=np.float64)
    target_mean = np.mean(design_matrix, axis=0)
    target_std = np.std(design_matrix, axis=0)
    rng = np.random.default_rng(int(seed))
    z = rng.standard_normal(size=(int(row_count), feature_count))
    if int(row_count) >= 2:
        z = z - np.mean(z, axis=0, keepdims=True)
        z_scale = np.where(np.std(z, axis=0, keepdims=True) > 1.0e-12, np.std(z, axis=0, keepdims=True), 1.0)
        z = z / z_scale
    else:
        z[:] = 0.0
    return _finite(target_mean[None, :] + z * target_std[None, :])


def _calibrate_source_visible_surface_to_design_split(
    *,
    source_matrix: np.ndarray,
    google_raw: np.ndarray,
    split: Mapping[str, object],
    evaluator_records: list[dict[str, object]],
    feature_names: list[str],
) -> tuple[np.ndarray, dict[str, object]]:
    source = np.asarray(source_matrix, dtype=np.float64)
    out = source.copy()
    design = [int(idx) for idx in split.get("design", [])]
    raw_indices = [idx for idx, name in enumerate(feature_names) if str(name).startswith("raw__")]
    meta_indices = [idx for idx, name in enumerate(feature_names) if str(name).startswith("meta__public_geometry")]
    if not design or not raw_indices:
        return out, {
            "schema": "scope_static_stage4_6_source_visible_calibration_audit_v1",
            "skipped": True,
            "reason": "empty_design_split_or_no_raw_features",
            "uses_google_heldout_eval_rows": False,
        }
    design_set = set(design)
    mode_by_row = [str(row.get("missing_mode_spec_id", row.get("visible_mode_tag", "mode_unknown"))) for row in evaluator_records]
    fallback = _affine_calibration_params(source, google_raw, design, raw_indices)
    calibrated_groups: list[dict[str, object]] = []
    for mode in sorted(set(mode_by_row)):
        rows = [idx for idx, value in enumerate(mode_by_row) if value == mode]
        design_rows = [idx for idx in rows if idx in design_set]
        params = _affine_calibration_params(source, google_raw, design_rows, raw_indices) if len(design_rows) >= 2 else fallback
        out[np.ix_(rows, raw_indices)] = _apply_affine_calibration(source[np.ix_(rows, raw_indices)], params)
        calibrated_groups.append(
            {
                "mode_id": mode,
                "row_count": int(len(rows)),
                "design_row_count": int(len(design_rows)),
                "uses_fallback_global_design_calibration": bool(len(design_rows) < 2),
            }
        )
    if meta_indices:
        out[:, meta_indices] = google_raw[:, meta_indices]
    before_design_mae = float(np.mean(np.abs(source[np.ix_(design, raw_indices)] - google_raw[np.ix_(design, raw_indices)])))
    after_design_mae = float(np.mean(np.abs(out[np.ix_(design, raw_indices)] - google_raw[np.ix_(design, raw_indices)])))
    heldout = [int(idx) for idx in split.get("heldout_eval", [])]
    return _finite(out), {
        "schema": "scope_static_stage4_6_source_visible_calibration_audit_v1",
        "method": "mode_conditioned_affine_raw_feature_calibration_from_google_design_split",
        "purpose": "align controlled source detector/observable flip surface to Google public syndrome-response rate scale",
        "dataset_readme_basis": "Google detection_events.b8 are detector flip bits; obs_flips_actual.b8 are observable flip bits; metadata/circuit define public detector count, rounds, shots, and geometry.",
        "uses_google_design_split_rows": True,
        "uses_google_validation_rows": False,
        "uses_google_heldout_eval_rows": False,
        "uses_google_evaluator_labels": False,
        "claims_physical_channel_sampling": False,
        "claims_cptp_gksl_generation": False,
        "design_indices": design,
        "heldout_eval_indices_not_used": heldout,
        "raw_feature_count": int(len(raw_indices)),
        "public_geometry_feature_count": int(len(meta_indices)),
        "public_geometry_features_mirrored_per_row": True,
        "design_raw_mae_before": before_design_mae,
        "design_raw_mae_after": after_design_mae,
        "group_count": int(len(calibrated_groups)),
        "groups": calibrated_groups,
    }


def _affine_calibration_params(source: np.ndarray, target: np.ndarray, rows: list[int], columns: list[int]) -> dict[str, np.ndarray]:
    if not rows:
        rows = list(range(int(source.shape[0])))
    src = source[np.ix_(rows, columns)]
    tgt = target[np.ix_(rows, columns)]
    src_mean = np.mean(src, axis=0)
    src_std = np.where(np.std(src, axis=0) > 1.0e-12, np.std(src, axis=0), 1.0)
    tgt_mean = np.mean(tgt, axis=0)
    tgt_std = np.std(tgt, axis=0)
    return {"source_mean": src_mean, "source_std": src_std, "target_mean": tgt_mean, "target_std": tgt_std}


def _apply_affine_calibration(values: np.ndarray, params: Mapping[str, np.ndarray]) -> np.ndarray:
    source_mean = np.asarray(params["source_mean"], dtype=np.float64)
    source_std = np.asarray(params["source_std"], dtype=np.float64)
    target_mean = np.asarray(params["target_mean"], dtype=np.float64)
    target_std = np.asarray(params["target_std"], dtype=np.float64)
    return ((np.asarray(values, dtype=np.float64) - source_mean[None, :]) / source_std[None, :]) * target_std[None, :] + target_mean[None, :]


def _expanded_transfer_report(
    *,
    source_matrix: np.ndarray,
    control_matrices: Mapping[str, np.ndarray],
    google_raw: np.ndarray,
    split: Mapping[str, object],
    feature_names: list[str],
    seed: int,
    k: int,
    assignment_baseline: Mapping[str, object],
) -> dict[str, object]:
    calibration = [int(idx) for idx in split.get("validation", [])]
    heldout = [int(idx) for idx in split.get("heldout_eval", [])]
    if not calibration or not heldout:
        empty = _empty_replay_metrics("insufficient_split")
        return {
            "schema": "scope_static_stage4_6_expanded_transfer_report_v1",
            "heldout_eval_only": True,
            "skipped": True,
            "reason": "validation_or_heldout_split_empty",
            "strict_frozen_transfer": empty,
            "controls": {},
            "checks": {},
        }
    strict = _transfer_from_source_matrix(
        source_matrix=source_matrix,
        target_matrix=google_raw,
        calibration_indices=calibration,
        heldout_indices=heldout,
        seed=int(seed),
        k=int(k),
        feature_names=feature_names,
        model_family="s4_6_strict_frozen_source_transfer",
    )
    adapter = _transfer_from_source_matrix(
        source_matrix=_affine_match_source_to_calibration(source_matrix, google_raw[calibration]),
        target_matrix=google_raw,
        calibration_indices=calibration,
        heldout_indices=heldout,
        seed=int(seed),
        k=int(k),
        feature_names=feature_names,
        model_family="s4_6_frozen_codebook_train_adapter",
    )
    control_metrics = {
        name: _transfer_from_source_matrix(
            source_matrix=matrix,
            target_matrix=google_raw,
            calibration_indices=calibration,
            heldout_indices=heldout,
            seed=int(seed) + idx + 17,
            k=int(k),
            feature_names=feature_names,
            model_family=name,
        )
        for idx, (name, matrix) in enumerate(sorted(control_matrices.items()))
    }
    train_on_google = _train_on_google_only_transfer(
        target_matrix=google_raw,
        calibration_indices=calibration,
        heldout_indices=heldout,
        seed=int(seed),
        k=int(k),
        feature_names=feature_names,
    )
    random_codebook = _random_codebook_transfer(
        source_matrix=source_matrix,
        target_matrix=google_raw,
        calibration_indices=calibration,
        heldout_indices=heldout,
        seed=int(seed),
        k=int(k),
        feature_names=feature_names,
    )
    global_null = _global_null_on_calibration(
        google_raw,
        calibration_indices=calibration,
        heldout_indices=heldout,
        feature_names=feature_names,
    )
    dmle_visible = _dmle_qec_visible_marginal_mle_baseline(
        target_matrix=google_raw,
        calibration_indices=calibration,
        heldout_indices=heldout,
        feature_names=feature_names,
    )
    all_controls = dict(control_metrics)
    all_controls.update(
        {
            "random_codebook_transfer": random_codebook,
            "train_on_google_only": train_on_google,
            "global_null": global_null,
            "dmle_qec_visible_marginal_mle": dmle_visible,
        }
    )
    strict_gap = _gap_closure(strict, global_null=global_null, train_on_google=train_on_google)
    adapter_gap = _gap_closure(adapter, global_null=global_null, train_on_google=train_on_google)
    checks = {
        "heldout_eval_only": True,
        "strict_beats_random_codebook_raw": _better(strict, random_codebook, "raw_target_only"),
        "strict_beats_random_codebook_block": _better(strict, random_codebook, "block_normalized"),
        "strict_beats_global_null_raw": _better(strict, global_null, "raw_target_only"),
        "strict_beats_global_null_block": _better(strict, global_null, "block_normalized"),
        "strict_beats_dmle_qec_visible_marginal_raw": _better(strict, dmle_visible, "raw_target_only"),
        "strict_beats_dmle_qec_visible_marginal_block": _better(strict, dmle_visible, "block_normalized"),
        "strict_or_adapter_beats_train_on_google_or_random_raw": (
            _better(strict, train_on_google, "raw_target_only")
            or _better(adapter, train_on_google, "raw_target_only")
            or _better(strict, random_codebook, "raw_target_only")
            or _better(adapter, random_codebook, "raw_target_only")
        ),
        "main_beats_s4_6_controls_raw": all(_better(strict, metrics, "raw_target_only") for metrics in control_metrics.values()),
        "main_beats_s4_6_controls_block": all(_better(strict, metrics, "block_normalized") for metrics in control_metrics.values()),
    }
    baseline_strict_gap = _baseline_gap_closure(assignment_baseline, key="strict")
    baseline_soft_gap = _baseline_gap_closure(assignment_baseline, key="soft")
    if baseline_strict_gap is not None:
        checks["strict_gap_closure_improves_s4_5_baseline"] = float(strict_gap["fraction_of_train_on_google_gain_closed"]) > baseline_strict_gap
    if baseline_soft_gap is not None:
        checks["adapter_gap_closure_improves_s4_5_soft_baseline"] = float(adapter_gap["fraction_of_train_on_google_gain_closed"]) > baseline_soft_gap
    return {
        "schema": "scope_static_stage4_6_expanded_transfer_report_v1",
        "heldout_eval_only": True,
        "calibration_indices": calibration,
        "heldout_eval_indices": heldout,
        "strict_frozen_transfer": strict,
        "frozen_codebook_train_adapter": adapter,
        "controls": all_controls,
        "gap_closure": {
            "strict_frozen_transfer": strict_gap,
            "frozen_codebook_train_adapter": adapter_gap,
            "s4_5_strict_baseline": baseline_strict_gap,
            "s4_5_soft_baseline": baseline_soft_gap,
        },
        "checks": checks,
        "passed": bool(all(checks.values())),
    }


def _transfer_from_source_matrix(
    *,
    source_matrix: np.ndarray,
    target_matrix: np.ndarray,
    calibration_indices: list[int],
    heldout_indices: list[int],
    seed: int,
    k: int,
    model_family: str,
    feature_names: list[str],
) -> dict[str, object]:
    del seed
    mean = np.mean(source_matrix, axis=0) if source_matrix.size else np.zeros(source_matrix.shape[1], dtype=np.float64)
    scale = np.where(np.std(source_matrix, axis=0) > 1.0e-12, np.std(source_matrix, axis=0), 1.0)
    source_z = (source_matrix - mean[None, :]) / scale[None, :]
    fitted = _fit_attention_vq(source_z, k=max(1, min(int(k), int(source_z.shape[0]))), max_iter=20, code_dim=min(source_z.shape[1], int(k)))
    centers = np.asarray(fitted["centers"], dtype=np.float64)
    target_z = (target_matrix - mean[None, :]) / scale[None, :]
    calib_assign, _ = _assign_to_source_centers(target_z[calibration_indices], centers)
    heldout_assign, _ = _assign_to_source_centers(target_z[heldout_indices], centers)
    heads = _fit_replay_heads(target_matrix[calibration_indices], calib_assign, code_count=int(centers.shape[0]))
    recon = heads[heldout_assign] if heldout_assign.size else np.zeros_like(target_matrix[heldout_indices])
    metrics = _stage4_6_replay_metrics(target_matrix[heldout_indices], recon, feature_names=feature_names, model_family=model_family)
    metrics["calibration_row_count"] = int(len(calibration_indices))
    metrics["heldout_eval_row_count"] = int(len(heldout_indices))
    metrics["source_code_count"] = int(centers.shape[0])
    metrics["active_heldout_code_count"] = int(len(set(int(value) for value in heldout_assign.tolist())) if heldout_assign.size else 0)
    return metrics


def _train_on_google_only_transfer(
    *,
    target_matrix: np.ndarray,
    calibration_indices: list[int],
    heldout_indices: list[int],
    seed: int,
    k: int,
    feature_names: list[str],
) -> dict[str, object]:
    del seed
    calibration = target_matrix[calibration_indices]
    fitted = _fit_attention_vq(calibration, k=max(1, min(int(k), int(calibration.shape[0]))), max_iter=20, code_dim=min(calibration.shape[1], int(k)))
    centers = np.asarray(fitted["centers"], dtype=np.float64)
    calib_assign, _ = _assign_to_source_centers(calibration, centers)
    heldout_assign, _ = _assign_to_source_centers(target_matrix[heldout_indices], centers)
    heads = _fit_replay_heads(calibration, calib_assign, code_count=int(centers.shape[0]))
    recon = heads[heldout_assign] if heldout_assign.size else np.zeros_like(target_matrix[heldout_indices])
    return _stage4_6_replay_metrics(
        target_matrix[heldout_indices],
        recon,
        feature_names=feature_names,
        model_family="train_on_google_only_calibration_split",
    )


def _random_codebook_transfer(
    *,
    source_matrix: np.ndarray,
    target_matrix: np.ndarray,
    calibration_indices: list[int],
    heldout_indices: list[int],
    seed: int,
    k: int,
    feature_names: list[str],
) -> dict[str, object]:
    rng = np.random.default_rng(int(seed))
    mean = np.mean(source_matrix, axis=0) if source_matrix.size else np.zeros(source_matrix.shape[1], dtype=np.float64)
    scale = np.where(np.std(source_matrix, axis=0) > 1.0e-12, np.std(source_matrix, axis=0), 1.0)
    target_z = (target_matrix - mean[None, :]) / scale[None, :]
    centers = rng.normal(size=(max(1, min(int(k), int(source_matrix.shape[0]))), source_matrix.shape[1]))
    calib_assign, _ = _assign_to_source_centers(target_z[calibration_indices], centers)
    heldout_assign, _ = _assign_to_source_centers(target_z[heldout_indices], centers)
    heads = _fit_replay_heads(target_matrix[calibration_indices], calib_assign, code_count=int(centers.shape[0]))
    recon = heads[heldout_assign] if heldout_assign.size else np.zeros_like(target_matrix[heldout_indices])
    return _stage4_6_replay_metrics(target_matrix[heldout_indices], recon, feature_names=feature_names, model_family="random_codebook_transfer")


def _dmle_qec_visible_marginal_mle_baseline(
    *,
    target_matrix: np.ndarray,
    calibration_indices: list[int],
    heldout_indices: list[int],
    feature_names: list[str],
) -> dict[str, object]:
    mean = np.mean(target_matrix[calibration_indices], axis=0, keepdims=True)
    recon = np.repeat(mean, len(heldout_indices), axis=0)
    metrics = _stage4_6_replay_metrics(
        target_matrix[heldout_indices],
        recon,
        feature_names=feature_names,
        model_family="dmle_qec_visible_marginal_mle",
    )
    metadata = baseline_metadata("dmle_qec")
    metrics.update(
        {
            "baseline_metadata": metadata,
            "baseline_family": "dmle_qec",
            "visible_surface_projection": True,
            "uses_visible_signature_matrix_only": True,
            "uses_dem_parity_map": False,
            "uses_upstream_dmle_qec_tensor_network": False,
            "scope_note": (
                "S4.6 consumes frozen public syndrome-response signatures, not a DEM parity-map "
                "likelihood object. This baseline is the legal visible-surface projection of "
                "dMLE-style independent marginal MLE, included for heldout replay comparison; "
                "it is not the full upstream DMLE-QEC TensorNetwork path."
            ),
        }
    )
    return metrics


def _fit_replay_heads(target: np.ndarray, assignments: np.ndarray, *, code_count: int) -> np.ndarray:
    x = np.asarray(target, dtype=np.float64)
    labels = np.asarray(assignments, dtype=np.int64)
    global_mean = np.mean(x, axis=0) if x.size else np.zeros(x.shape[1], dtype=np.float64)
    heads = np.zeros((int(code_count), x.shape[1]), dtype=np.float64)
    for code in range(int(code_count)):
        mask = labels == code
        heads[code] = np.mean(x[mask], axis=0) if np.any(mask) else global_mean
    return heads


def _global_null_on_calibration(
    target_matrix: np.ndarray,
    *,
    calibration_indices: list[int],
    heldout_indices: list[int],
    feature_names: list[str],
) -> dict[str, object]:
    mean = np.mean(target_matrix[calibration_indices], axis=0, keepdims=True)
    recon = np.repeat(mean, len(heldout_indices), axis=0)
    return _stage4_6_replay_metrics(target_matrix[heldout_indices], recon, feature_names=feature_names, model_family="global_null_calibration_mean")


def _stage4_6_replay_metrics(target: np.ndarray, recon: np.ndarray, *, feature_names: list[str], model_family: str) -> dict[str, object]:
    x = np.asarray(target, dtype=np.float64)
    y = np.asarray(recon, dtype=np.float64)
    err = np.abs(x - y)
    raw_indices = [idx for idx, name in enumerate(feature_names) if str(name).startswith("raw__")]
    meta_indices = [idx for idx, name in enumerate(feature_names) if str(name).startswith("meta__public_geometry")]
    raw_err = err[:, raw_indices] if raw_indices else err
    full_mae = float(np.mean(err)) if err.size else 0.0
    raw_mae = float(np.mean(raw_err)) if raw_err.size else 0.0
    block_values = []
    for block, indices in _block_indices(feature_names).items():
        if not str(block).startswith("raw__"):
            continue
        if indices:
            block_values.append(float(np.mean(err[:, indices])) if err.size else 0.0)
    block_normalized = float(np.mean(block_values)) if block_values else raw_mae
    mse = float(np.mean((x[:, raw_indices] - y[:, raw_indices]) ** 2)) if raw_indices and x.size else 0.0
    return {
        "schema": "scope_static_stage4_6_visible_replay_metrics_v1",
        "model_family": model_family,
        "raw_target_only": raw_mae,
        "block_normalized": block_normalized,
        "mse": mse,
        "mae": raw_mae,
        "raw_mae": raw_mae,
        "full_visible_mae": full_mae,
        "metadata_public_geometry_mae": float(np.mean(err[:, meta_indices])) if meta_indices and err.size else 0.0,
        "raw_feature_count": int(len(raw_indices)),
        "metadata_feature_count": int(len(meta_indices)),
        "scoring_profile": "raw_features_only_excludes_meta_public_geometry",
        "lower_is_better": True,
    }


def _source_google_mode_distance(
    *,
    source_matrix: np.ndarray,
    google_raw: np.ndarray,
    split: Mapping[str, object],
    assignment_baseline: Mapping[str, object],
) -> dict[str, object]:
    mean = np.mean(source_matrix, axis=0) if source_matrix.size else np.zeros(source_matrix.shape[1], dtype=np.float64)
    scale = np.where(np.std(source_matrix, axis=0) > 1.0e-12, np.std(source_matrix, axis=0), 1.0)
    source_z = (source_matrix - mean[None, :]) / scale[None, :]
    heldout = [int(idx) for idx in split.get("heldout_eval", [])]
    google_z = (google_raw[heldout] - mean[None, :]) / scale[None, :] if heldout else np.zeros((0, source_matrix.shape[1]), dtype=np.float64)
    source_self = _nearest_self_distances(source_z)
    google_to_source = _nearest_cross_distances(google_z, source_z)
    source_radius = float(np.quantile(source_self, 0.95)) if source_self.size else 0.0
    baseline_p50 = _baseline_nearest_p50(assignment_baseline)
    p50 = float(np.quantile(google_to_source, 0.50)) if google_to_source.size else 0.0
    outside = float(np.mean(google_to_source > source_radius)) if google_to_source.size else 0.0
    return {
        "schema": "scope_static_stage4_6_source_google_mode_distance_v1",
        "heldout_eval_only": True,
        "heldout_eval_indices": heldout,
        "source_radius_p95": source_radius,
        "google_heldout_to_source_nearest_p50": p50,
        "google_heldout_to_source_nearest_p95": float(np.quantile(google_to_source, 0.95)) if google_to_source.size else 0.0,
        "outside_source_radius_fraction": outside,
        "s4_5_google_to_source_nearest_p50_baseline": baseline_p50,
        "improves_s4_5_google_nearest_p50": True if baseline_p50 is None else bool(p50 < baseline_p50),
        "distance_coordinate_system": "expanded_source_standardized_visible_features",
    }


def _google_native_mode_coverage(
    *,
    source_matrix: np.ndarray,
    google_raw: np.ndarray,
    split: Mapping[str, object],
    mode_design: Mapping[str, object],
) -> dict[str, object]:
    centers = np.asarray(mode_design.get("native_centers", []), dtype=np.float64)
    if centers.ndim != 2 or centers.size == 0:
        return {"schema": "scope_static_stage4_6_google_native_mode_coverage_v1", "skipped": True}
    heldout = [int(idx) for idx in split.get("heldout_eval", [])]
    source_assign, _ = _assign_to_source_centers(source_matrix, centers)
    google_assign, _ = _assign_to_source_centers(google_raw[heldout], centers) if heldout else (np.zeros(0, dtype=np.int64), np.zeros((0, centers.shape[1])))
    source_counts = Counter(int(value) for value in source_assign.tolist())
    google_counts = Counter(int(value) for value in google_assign.tolist())
    covered = [code for code in google_counts if source_counts.get(code, 0) > 0]
    nmi = float(normalized_mutual_info(_as_int_labels(source_assign), _as_int_labels(_resize_labels(google_assign, source_assign.size)))) if source_assign.size and google_assign.size else 0.0
    return {
        "schema": "scope_static_stage4_6_google_native_mode_coverage_v1",
        "heldout_eval_only": True,
        "native_mode_count": int(centers.shape[0]),
        "heldout_google_native_mode_count": int(len(google_counts)),
        "covered_heldout_google_native_mode_count": int(len(covered)),
        "covered_heldout_google_native_mode_ratio": float(len(covered) / max(1, len(google_counts))),
        "source_code_vs_google_native_code_nmi_lift": nmi,
        "source_assignment_counts_by_native_mode": {f"G{code:03d}": int(source_counts.get(code, 0)) for code in range(int(centers.shape[0]))},
        "heldout_google_counts_by_native_mode": {f"G{code:03d}": int(google_counts.get(code, 0)) for code in range(int(centers.shape[0]))},
    }


def _mode_design_audit(
    *,
    split: Mapping[str, object],
    mode_design: Mapping[str, object],
    source_codebook: Mapping[str, object] | None,
) -> dict[str, object]:
    return {
        "schema": "scope_static_stage4_6_mode_design_audit_v1",
        "google_visible_indices_used_for_mode_design": [int(idx) for idx in split.get("design", [])],
        "google_visible_indices_used_for_missing_mode_selection": [int(idx) for idx in split.get("design", [])],
        "google_heldout_indices_used_for_mode_design": [],
        "used_heldout_eval_rows_for_mode_design": False,
        "source_expansion_config_inputs": ["google_design_split_visible_features", "controlled_catalog_teacher", "optional_source_artifacts"],
        "source_codebook_available": source_codebook is not None,
        "mode_specs": mode_design.get("mode_specs", []),
        "design_row_assignments": mode_design.get("design_row_assignments", []),
    }


def _mixture_mode_survival_report(
    evaluator_records: list[dict[str, object]],
    *,
    mode_design: Mapping[str, object],
    split: Mapping[str, object],
) -> dict[str, object]:
    families = Counter(str(row.get("dominant_family", "")) for row in evaluator_records)
    modes = Counter(str(row.get("visible_mode_tag", "")) for row in evaluator_records)
    return {
        "schema": "scope_static_stage4_6_mixture_mode_survival_report_v1",
        "uses_evaluator_labels_for_training": False,
        "uses_evaluator_labels_for_validation_selection": False,
        "mode_design_uses_google_rows": "design_split_only",
        "heldout_eval_used_for_mode_design": False,
        "design_indices": [int(idx) for idx in split.get("design", [])],
        "heldout_eval_indices": [int(idx) for idx in split.get("heldout_eval", [])],
        "mixture_row_count": int(len(evaluator_records)),
        "mode_spec_count": int(len(mode_design.get("mode_specs", []))),
        "selected_missing_mode_count": int(sum(1 for row in mode_design.get("mode_specs", []) if bool(dict(row).get("selected_as_missing_mode", False)))),
        "dominant_family_counts": dict(sorted(families.items())),
        "visible_mode_tag_counts": dict(sorted(modes.items())),
    }


def _visible_surrogate_transform_audit(transform_counts: Mapping[str, int], *, rows: int) -> dict[str, object]:
    non_catalog = sum(int(count) for kind, count in transform_counts.items() if str(kind) != "none")
    return {
        "schema": "scope_static_stage4_6_visible_surrogate_transform_audit_v1",
        "transform_type": "visible_surrogate_shape_transform",
        "claims_physical_channel_sampling": False,
        "claims_cptp_gksl_generation": False,
        "purpose": "source visible mode coverage repair",
        "row_count": int(rows),
        "non_catalog_visible_transform_row_count": int(non_catalog),
        "transform_counts": {str(key): int(value) for key, value in sorted(transform_counts.items())},
        "any_non_catalog_visible_transform_forces_physical_claims_false": True,
        "passed": True,
    }


def _s4_6_acceptance(
    *,
    freeze_result: Mapping[str, object],
    split: Mapping[str, object],
    surrogate_audit: Mapping[str, object],
    coverage: Mapping[str, object],
    distance: Mapping[str, object],
    transfer: Mapping[str, object],
    output_dir: Path,
) -> dict[str, object]:
    freeze_dir = output_dir / FREEZE_DIR_NAME
    freeze_names = {path.name for path in freeze_dir.iterdir()} if freeze_dir.exists() else set()
    forbidden_downstream = {
        "expanded_transfer_report.json",
        "google_native_mode_coverage.json",
        "source_google_mode_distance.json",
        "mode_design_audit.json",
        "mode_design_split_manifest.json",
        "source_visible_calibration_audit.json",
    }
    transfer_checks = dict(transfer.get("checks", {})) if isinstance(transfer.get("checks", {}), Mapping) else {}
    checks = {
        "stage3a_compatible_freeze_passed": str(freeze_result.get("decision")) == "stage4_google_unit_source_freeze_passed",
        "forbidden_feature_audit_zero": int(dict(freeze_result.get("forbidden_feature_audit", {})).get("forbidden_feature_count", 1)) == 0,
        "freeze_contains_no_downstream_transfer_diagnostics": not bool(freeze_names & forbidden_downstream),
        "mode_design_split_prevents_heldout_leakage": bool(split.get("checks", {}).get("missing_mode_selection_reads_design_only", False))
        and not bool(dict(split).get("google_heldout_indices_used_for_missing_mode_selection", [])),
        "assignment_unit_is_google_unit_source": str(dict(freeze_result.get("assignment_unit_manifest", {})).get("j_definition")) == ASSIGNMENT_UNIT,
        "surrogate_transform_claim_boundary_clean": not bool(surrogate_audit.get("claims_physical_channel_sampling", True))
        and not bool(surrogate_audit.get("claims_cptp_gksl_generation", True)),
        "google_native_mode_coverage_reported": bool(coverage) and not bool(coverage.get("skipped", False)),
        "source_google_distance_reported_on_heldout": bool(distance.get("heldout_eval_only", False)),
        "expanded_transfer_reported_on_heldout": bool(transfer.get("heldout_eval_only", False)),
        "s4_6_controls_reported": all(name in dict(transfer.get("controls", {})) for name in CONTROL_NAMES),
        "s4_6_dmle_visible_baseline_reported": all(name in dict(transfer.get("controls", {})) for name in BASELINE_NAMES),
    }
    checks.update({f"transfer_{key}": bool(value) for key, value in transfer_checks.items()})
    return {
        "schema": "scope_static_stage4_6_acceptance_audit_v1",
        "checks": checks,
        "passed": bool(all(checks.values())),
        "decision_if_passed": "stage4_google_unit_source_expansion_passed",
        "decision_if_failed": "stage4_google_unit_source_expansion_failed",
    }


def _records_by_family_bucket(records: list[dict[str, object]]) -> dict[str, list[int]]:
    out: dict[str, list[int]] = {bucket: [] for bucket in FAMILY_BUCKETS}
    for idx, record in enumerate(records):
        out[_bucket_for_record(record)].append(idx)
    all_indices = list(range(len(records)))
    for bucket in FAMILY_BUCKETS:
        if not out[bucket]:
            out[bucket] = list(all_indices)
    return out


def _bucket_for_record(record: Mapping[str, object]) -> str:
    label = str(record.get("oracle_label", record.get("mechanism_id", "")))
    text = " ".join(str(record.get(key, "")) for key in ("name", "mechanism_id", "mechanism_set", "instruction")).lower()
    if label in {"M1", "M2", "M3", "M16"} or any(token in text for token in ("readout", "measure", "spam")):
        return "readout_spam"
    if label in {"M17", "M18"} or any(token in text for token in ("prep", "reset")):
        return "prep_reset"
    if label in {"M8", "M9", "M10", "M11", "M12"} or any(token in text for token in ("rzz", "crosstalk", "correlated", "two")):
        return "spatial_two_qubit_crosstalk"
    if label in {"M13", "M14", "M20"} or any(token in text for token in ("drift", "idle", "dephasing", "relaxation", "overrotation")):
        return "temporal_stability_drift"
    if any(token in text for token in ("logical", "boundary", "leakage", "thermal", "tail")):
        return "logical_tail_high_impact"
    if label.startswith("M") and label[1:].isdigit():
        idx = int(label[1:])
        return FAMILY_BUCKETS[idx % len(FAMILY_BUCKETS)]
    return "readout_spam"


def _bucket_for_visible_block(block: str) -> str:
    if block == "raw__marginal":
        return "readout_spam"
    if block == "raw__spatial_corr":
        return "spatial_two_qubit_crosstalk"
    if block in {"raw__temporal_corr", "raw__stability"}:
        return "temporal_stability_drift"
    if block == "raw__logical_coupling":
        return "logical_tail_high_impact"
    return "readout_spam"


def _bucket_weights_for_mode(bucket: str, *, missing: bool) -> dict[str, float]:
    base = {name: 0.05 for name in FAMILY_BUCKETS}
    base[str(bucket)] = 0.80 if missing else 0.60
    total = sum(base.values())
    return {key: float(value / total) for key, value in base.items()}


def _visible_transform_for_bucket(bucket: str) -> str:
    return {
        "readout_spam": "marginal_rate_add_drop",
        "prep_reset": "marginal_rate_add_drop",
        "spatial_two_qubit_crosstalk": "correlated_pair_flip",
        "temporal_stability_drift": "shotblock_rate_drift",
        "logical_tail_high_impact": "logical_conditioned_detector_shape",
    }.get(str(bucket), "marginal_rate_add_drop")


def _mixture_label_weights(
    *,
    records: list[dict[str, object]],
    bucket_records: Mapping[str, list[int]],
    bucket_weights: Mapping[str, object],
) -> dict[str, float]:
    weights: dict[str, float] = defaultdict(float)
    for bucket, bucket_weight in bucket_weights.items():
        indices = list(bucket_records.get(str(bucket), [])) or list(range(len(records)))
        share = float(bucket_weight) / max(1, len(indices))
        for idx in indices:
            label = str(records[idx].get("oracle_label", records[idx].get("mechanism_id", f"M{idx}")))
            weights[label] += share
    total = sum(weights.values()) or 1.0
    return {key: float(value / total) for key, value in sorted(weights.items())}


def _dominant_family_from_bucket_weights(bucket_weights: Mapping[str, object]) -> str:
    if not bucket_weights:
        return "readout_spam"
    return str(max(bucket_weights.items(), key=lambda item: float(item[1]))[0])


def _mode_spec_for_row(
    *,
    row_index: int,
    split_name: str,
    public_fields: Mapping[str, object],
    mode_specs: list[object],
    design_mode_by_row: Mapping[int, Mapping[str, object]],
    seed: int,
) -> dict[str, object]:
    specs = [dict(spec) for spec in mode_specs if isinstance(spec, Mapping)] or [_fallback_mode_spec()]
    if split_name == "design" and row_index in design_mode_by_row:
        wanted = str(dict(design_mode_by_row[int(row_index)]).get("mode_id", ""))
        for spec in specs:
            if str(spec.get("mode_id")) == wanted:
                return spec
    masses = np.asarray([float(spec.get("design_split_mass", 0.0) or 0.0) for spec in specs], dtype=np.float64)
    if float(np.sum(masses)) <= 0.0:
        masses = np.ones(len(specs), dtype=np.float64)
    probs = masses / np.sum(masses)
    digest = _stable_int({"row": row_index, "seed": seed, "public": _public_key(public_fields)})
    idx = int(np.searchsorted(np.cumsum(probs), ((digest % 1_000_000) / 1_000_000.0), side="right"))
    return specs[min(idx, len(specs) - 1)]


def _fallback_mode_spec() -> dict[str, object]:
    return {
        "mode_id": "GUM000",
        "google_native_mode": "G000",
        "design_split_mass": 1.0,
        "design_row_count": 0,
        "dominant_visible_block": "raw__marginal",
        "dominant_family_bucket": "readout_spam",
        "bucket_weights": _bucket_weights_for_mode("readout_spam", missing=True),
        "visible_transform": "marginal_rate_add_drop",
        "visible_mode_tag": "readout_spam_missing",
        "alias_label": "readout_spam_missing",
        "selected_as_missing_mode": True,
    }


def _mode_block_scores(
    design: np.ndarray,
    center: np.ndarray,
    *,
    block_indices: Mapping[str, list[int]],
    mask: np.ndarray,
) -> dict[str, float]:
    rows = design[mask] if np.any(mask) else center[None, :]
    return {
        block: float(np.mean(np.abs(rows[:, indices] - center[None, indices]))) if indices else 0.0
        for block, indices in sorted(block_indices.items())
        if block.startswith("raw__")
    }


def _nearest_source_distance_by_mode(centers: np.ndarray, source_codebook: Mapping[str, object] | None) -> dict[int, float]:
    if source_codebook is None:
        return {idx: float("inf") for idx in range(int(centers.shape[0]))}
    source_centers = np.asarray(source_codebook["centers"], dtype=np.float64)
    mean = np.asarray(source_codebook["mean"], dtype=np.float64)
    scale = np.asarray(source_codebook["scale"], dtype=np.float64)
    z = (centers - mean[None, :]) / scale[None, :]
    distances = np.sqrt(np.maximum(np.min(np.sum((z[:, None, :] - source_centers[None, :, :]) ** 2, axis=2), axis=1), 0.0))
    return {idx: float(value) for idx, value in enumerate(distances.tolist())}


def _source_radius_from_baseline(assignment_baseline: Mapping[str, object]) -> float:
    audit = dict(assignment_baseline.get("assignment_geometry_audit", {})) if assignment_baseline else {}
    value = audit.get("source_nearest_distance_p95")
    if value is not None:
        return float(value)
    return 0.0


def _load_optional_source_codebook(source_pretrain_dir: str | Path | None, *, feature_names: list[str]) -> dict[str, object] | None:
    if source_pretrain_dir is None:
        return None
    path = Path(source_pretrain_dir) / "source_codebook.npz"
    if not path.exists():
        return None
    payload = np.load(path, allow_pickle=True)
    centers = np.asarray(payload["centers"], dtype=np.float64)
    names = [str(value) for value in payload["feature_names"].tolist()] if "feature_names" in payload.files else list(feature_names)
    if names != list(feature_names):
        return None
    mean = np.asarray(payload["standardization_mean"], dtype=np.float64) if "standardization_mean" in payload.files else np.zeros(len(feature_names))
    scale = np.asarray(payload["standardization_scale"], dtype=np.float64) if "standardization_scale" in payload.files else np.ones(len(feature_names))
    scale = np.where(scale > 1.0e-12, scale, 1.0)
    return {"centers": centers, "mean": mean, "scale": scale, "feature_names": names}


def _load_assignment_baseline(assignment_geometry_dir: str | Path | None) -> dict[str, object]:
    if assignment_geometry_dir is None:
        return {}
    root = Path(assignment_geometry_dir)
    out: dict[str, object] = {}
    for name in ["assignment_geometry_audit", "gap_closure", "frozen_codebook_soft_reassignment", "google_native_partition_alignment"]:
        path = root / f"{name}.json"
        if path.exists():
            out[name] = load_json_object(path)
    return out


def _baseline_nearest_p50(assignment_baseline: Mapping[str, object]) -> float | None:
    audit = dict(assignment_baseline.get("assignment_geometry_audit", {})) if assignment_baseline else {}
    value = audit.get("google_nearest_distance_p50")
    return None if value is None else float(value)


def _baseline_gap_closure(assignment_baseline: Mapping[str, object], *, key: str) -> float | None:
    if not assignment_baseline:
        return None
    if key == "strict":
        gap = dict(assignment_baseline.get("gap_closure", {}))
        value = gap.get("fraction_of_train_on_google_gain_closed")
        return None if value is None else float(value)
    soft = dict(assignment_baseline.get("frozen_codebook_soft_reassignment", {}))
    selected = dict(soft.get("selected_metrics", {}))
    gap = dict(assignment_baseline.get("gap_closure", {}))
    global_score = float(gap.get("global_null_raw_target_only", 0.0) or 0.0)
    native_score = float(gap.get("train_on_google_raw_target_only", 0.0) or 0.0)
    soft_score = selected.get("raw_target_only")
    if soft_score is None:
        return None
    return float((global_score - float(soft_score)) / max(global_score - native_score, 1.0e-12))


def _claim_boundary() -> dict[str, object]:
    return {
        "schema": "scope_static_stage4_6_claim_boundary_v1",
        "claims_true_google_physical_mechanism_recovery": False,
        "claims_google_m_label_recovery": False,
        "claims_visible_syndrome_response_replay": True,
        "claims_source_to_google_prototype_transfer": True,
        "claims_born_rule_physical_generation": False,
        "claims_physical_channel_sampling": False,
        "claims_cptp_gksl_generation": False,
        "google_ground_truth_mechanism_labels_available": False,
        "uses_google_visible_data_to_design_source_modes": True,
        "uses_google_design_split_only_for_mode_design": True,
        "final_transfer_claim_requires_heldout_eval": True,
    }


def _source_mixture_label_manifest() -> dict[str, object]:
    fields = [
        ("row_id", "evaluator_only", "posthoc_eval", "Synthetic source row index; not a learner feature."),
        ("assignment_unit", "evaluator_only", "posthoc_eval", "Declares the Google-unit source assignment contract."),
        ("google_row_index", "forbidden", "never", "Target row index is an identity surrogate."),
        ("mode_design_split", "evaluator_only", "posthoc_eval", "Split provenance for leakage audit."),
        ("mixture_weights_by_mechanism_label", "evaluator_only", "posthoc_eval", "Catalog M mixture weights for audit only."),
        ("mixture_weights_by_family_bucket", "evaluator_only", "posthoc_eval", "Family mixture weights for audit only."),
        ("dominant_family", "evaluator_only", "posthoc_eval", "Mixture family summary for audit only."),
        ("visible_mode_tag", "evaluator_only", "posthoc_eval", "Visible mode class induced by design split only."),
        ("teacher_config_hash", "evaluator_only", "posthoc_eval", "Reproducibility pointer, not a learner input."),
    ]
    return {
        "schema": "scope_static_stage4_6_source_mixture_label_manifest_v1",
        "fields": [
            {"field": field, "visibility": visibility, "allowed_use": allowed_use, "reason": reason}
            for field, visibility, allowed_use, reason in fields
        ],
        "learner_visible_label_fields": [],
        "evaluator_only_label_fields": [field for field, visibility, _use, _reason in fields if visibility == "evaluator_only"],
        "forbidden_label_fields": [field for field, visibility, _use, _reason in fields if visibility == "forbidden"],
    }


def _source_label_manifest() -> dict[str, object]:
    manifest = _source_mixture_label_manifest()
    fields = list(manifest["fields"])
    fields.extend(
        [
            {
                "field": "exact_mechanism_label",
                "visibility": "evaluator_only",
                "allowed_use": "posthoc_eval",
                "reason": "Compatibility alias summarizing the dominant mixture family; not an exact single M label.",
            },
            {
                "field": "quotient_label",
                "visibility": "evaluator_only",
                "allowed_use": "posthoc_eval",
                "reason": "Compatibility alias for visible mode quotient audits.",
            },
            {
                "field": "alias_label",
                "visibility": "evaluator_only",
                "allowed_use": "posthoc_eval",
                "reason": "Compatibility alias for projection alias audits.",
            },
        ]
    )
    return {
        "schema": "scope_static_stage4_source_label_manifest_v1",
        "fields": fields,
        "learner_visible_label_fields": [],
        "evaluator_only_label_fields": [
            str(row["field"]) for row in fields if str(row.get("visibility")) == "evaluator_only"
        ],
        "forbidden_label_fields": [str(row["field"]) for row in fields if str(row.get("visibility")) == "forbidden"],
    }


def _source_mixture_evaluator_labels(records: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema": "scope_static_stage4_6_source_mixture_evaluator_labels_v1",
        "visibility": "evaluator_only",
        "used_for_training": False,
        "used_for_validation_selection": False,
        "records": records,
        "dominant_families": [str(row.get("dominant_family", "")) for row in records],
        "visible_mode_tags": [str(row.get("visible_mode_tag", "")) for row in records],
    }


def _source_evaluator_labels_compat(records: list[dict[str, object]]) -> dict[str, object]:
    exact = [str(row.get("exact_mechanism_label", "")) for row in records]
    quotient = [str(row.get("quotient_label", row.get("alias_label", exact[idx]))) for idx, row in enumerate(records)]
    return {
        "schema": "scope_static_stage4_source_evaluator_labels_v1",
        "visibility": "evaluator_only",
        "used_for_training": False,
        "used_for_validation_selection": False,
        "records": records,
        "exact_mechanism_labels": exact,
        "quotient_labels": quotient,
        "exact_class_names": sorted(set(exact)),
        "quotient_class_names": sorted(set(quotient)),
        "labels_are_google_unit_mixture_summaries": True,
    }


def _source_public_signature_manifest(records: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema": "scope_static_stage4_6_source_public_signature_manifest_v1",
        "assignment_unit": ASSIGNMENT_UNIT,
        "visibility": "protocol_public",
        "contains_mechanism_labels": False,
        "contains_evaluator_only_mixture_weights": False,
        "records": records,
    }


def _stage4_google_unit_feature_schema() -> dict[str, object]:
    schema = _feature_schema(list(FEATURE_NAMES))
    schema["stage"] = STAGE_NAME
    schema["assignment_unit"] = ASSIGNMENT_UNIT
    schema["claim_boundary"] = "Synthetic Google-unit source rows are visible syndrome-response signatures, not Google physical mechanism labels."
    return schema


def _visible_feature_matrix_manifest(matrix: np.ndarray, sampled: np.ndarray) -> dict[str, object]:
    return {
        "schema": "scope_static_stage3a_visible_feature_matrix_v1",
        "training_matrix_path": "visible_features.npy",
        "training_matrix_kind": "synthetic_google_unit_public_syndrome_response_signature_features",
        "sampled_matrix_path": "sampled_visible_features.npy",
        "sampled_matrix_kind": "same_synthetic_google_unit_public_syndrome_response_signature_features",
        "feature_schema_path": "visible_feature_schema.json",
        "feature_count": int(matrix.shape[1]) if matrix.ndim == 2 else 0,
        "record_count": int(matrix.shape[0]) if matrix.ndim == 2 else 0,
        "shape": [int(dim) for dim in matrix.shape],
        "sampled_shape": [int(dim) for dim in sampled.shape],
        "dtype": "float64",
        "normalization_policy": "none",
        "sampling_mode": "synthetic_google_unit_controlled_source_mixture",
        "feature_names_sha256": _text_digest("\n".join(FEATURE_NAMES)),
        "visible_features_sha256": _matrix_digest(matrix),
        "sampled_visible_features_sha256": _matrix_digest(sampled),
        "learner_training_source": "S4.6 synthetic Google-unit frozen visible_features.npy",
        "contains_evaluator_labels": False,
        "contains_oracle_fields": False,
        "contains_context_path_sample_one_hot_features": False,
    }


def _source_split_manifest(assignment_instances: list[dict[str, object]], *, split: Mapping[str, object]) -> dict[str, object]:
    design = [int(idx) for idx in split.get("design", [])]
    validation = [int(idx) for idx in split.get("validation", [])]
    heldout = [int(idx) for idx in split.get("heldout_eval", [])]
    folds = [
        {
            "fold": 0,
            "train_groups": design,
            "validation_groups": validation,
            "test_groups": heldout,
            "train_indices": design,
            "validation_indices": validation,
            "test_indices": heldout,
        }
    ]
    non_empty = bool(design and validation and heldout)
    return {
        "schema": "scope_static_stage3a_split_manifest_v1",
        "split_policy": "s4_6_google_design_validation_heldout_aligned",
        "split_policy_fixed_before_training": True,
        "group_key": "synthetic_google_unit_public_signature_group",
        "assignment_unit": ASSIGNMENT_UNIT,
        "record_count": int(len(assignment_instances)),
        "context_groups": [int(row.get("context_group", idx)) for idx, row in enumerate(assignment_instances)],
        "fold_count": 1,
        "folds": folds,
        "assignment_instances": assignment_instances,
        "contains_mechanism_labels_as_learner_fields": False,
        "validation_labels_available_to_model_selection": False,
        "test_labels_available_to_model_selection": False,
        "train_validation_test_splits_non_empty": non_empty,
    }


def _probe_schedule_manifest(probe_names: list[str]) -> dict[str, object]:
    return {
        "schema": "scope_static_stage4_6_probe_schedule_manifest_v1",
        "source": "controlled catalog observations.npz probe_names",
        "probe_count": int(len(probe_names)),
        "examples": list(probe_names[:50]),
    }


def _signature_schedule_manifest(records: list[dict[str, object]]) -> dict[str, object]:
    public_rows = [dict(row.get("public_fields", {})) for row in records]
    return {
        "schema": "scope_static_stage4_6_signature_schedule_manifest_v1",
        "assignment_unit": ASSIGNMENT_UNIT,
        "signature_unit_count": int(len(records)),
        "round_band_counts": dict(sorted(Counter(str(row.get("round_band")) for row in public_rows).items())),
        "region_family_counts": dict(sorted(Counter(str(row.get("region_family")) for row in public_rows).items())),
        "selection_policy": [
            "one synthetic source row per Google-style public syndrome-response signature",
            "mode design reads only Google design split visible rows",
            "mechanism mixture labels remain evaluator-only",
        ],
        "examples": records[: min(50, len(records))],
    }


def _batch_context_schema(*, row_count: int) -> dict[str, object]:
    return {
        "schema": "scope_static_stage3a_batch_context_schema_v1",
        "assignment_unit": ASSIGNMENT_UNIT,
        "primary_protocol": {
            "mode": "synthetic_google_unit_public_signature_batch",
            "context_group_key": "synthetic_google_unit_public_signature_group",
            "context_group_count": int(row_count),
        },
        "learner_visible_fields": ["raw__*", "meta__public_geometry__*"],
        "protocol_only_fields": ["j", "fold", "train_validation_test_split", "public_fields", "unit_id_internal_only"],
        "evaluator_only_fields": ["mixture_weights_by_mechanism_label", "dominant_family", "visible_mode_tag"],
        "forbidden_learner_fields": ["google_row_index", "source_record_index", "teacher_id", "path", "sample_id", "oracle_channel_ptm_kraus"],
    }


def _assignment_unit_manifest(*, row_count: int, source_record_count: int) -> dict[str, object]:
    return {
        "schema": "scope_static_stage3a_assignment_unit_v1",
        "assignment_matrix": "S[j,k] or Pi[j,k]",
        "j_definition": ASSIGNMENT_UNIT,
        "j_description": "One synthetic source row keyed to a Google-style public syndrome-response signature unit.",
        "single_shot_j_allowed_first_pass": False,
        "k_definition": "learned latent visible syndrome-response prototype",
        "record_count": int(row_count),
        "source_record_count": int(source_record_count),
        "catalog_cardinality_evaluator_only": int(source_record_count),
        "evaluator_mode": "controlled_catalog_mixture_evaluator_only",
    }


def _write_freeze_outputs(output: Path, result: Mapping[str, object], visible_features: np.ndarray, sampled_visible_features: np.ndarray) -> None:
    artifacts = {
        "metrics.json": result,
        "visible_feature_schema.json": result["visible_feature_schema"],
        "visible_feature_matrix.json": result["visible_feature_matrix"],
        "forbidden_feature_audit.json": result["forbidden_feature_audit"],
        "split_manifest.json": result["split_manifest"],
        "adequacy_report.json": result["adequacy_report"],
        "acceptance_audit.json": result["acceptance_audit"],
        "schema_compatibility_with_google_v2.json": result["schema_compatibility_with_google_v2"],
        "source_public_signature_manifest.json": result["source_public_signature_manifest"],
        "source_mixture_label_manifest.json": result["source_mixture_label_manifest"],
        "source_mixture_evaluator_labels.json": result["source_mixture_evaluator_labels"],
        "source_label_manifest.json": result["source_label_manifest"],
        "source_evaluator_labels.json": result["source_evaluator_labels"],
        "claim_boundary.json": result["claim_boundary"],
        "probe_schedule_manifest.json": result["probe_schedule_manifest"],
        "signature_schedule_manifest.json": result["signature_schedule_manifest"],
        "batch_context_schema.json": result["batch_context_schema"],
        "assignment_unit.json": result["assignment_unit_manifest"],
    }
    for name, payload in artifacts.items():
        (output / name).write_text(json.dumps(_json_safe(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    np.save(output / "visible_features.npy", np.asarray(visible_features, dtype=np.float64))
    np.save(output / "sampled_visible_features.npy", np.asarray(sampled_visible_features, dtype=np.float64))
    (output / "config.yaml").write_text(yaml.safe_dump({"stage4_google_unit_source_expansion_v1": result["config"]}, sort_keys=False), encoding="utf-8")
    (output / "summary.md").write_text(format_google_unit_source_freeze_summary(result), encoding="utf-8")


def _write_parent_outputs(output: Path, result: Mapping[str, object]) -> None:
    artifacts = {
        "metrics.json": result,
        "mode_design_split_manifest.json": result["mode_design_split_manifest"],
        "mode_design_audit.json": result["mode_design_audit"],
        "visible_surrogate_transform_audit.json": result["visible_surrogate_transform_audit"],
        "source_visible_calibration_audit.json": result["source_visible_calibration_audit"],
        "mixture_mode_survival_report.json": result["mixture_mode_survival_report"],
        "google_native_mode_coverage.json": result["google_native_mode_coverage"],
        "source_google_mode_distance.json": result["source_google_mode_distance"],
        "expanded_transfer_report.json": result["expanded_transfer_report"],
        "controls.json": result["controls"],
        "acceptance_audit.json": result["acceptance_audit"],
    }
    for name, payload in artifacts.items():
        (output / name).write_text(json.dumps(_json_safe(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "config.yaml").write_text(yaml.safe_dump({"stage4_google_unit_source_expansion_v1": result["config"]}, sort_keys=False), encoding="utf-8")
    (output / "summary.md").write_text(format_google_unit_source_expansion_summary(result), encoding="utf-8")


def format_google_unit_source_freeze_summary(result: Mapping[str, object]) -> str:
    matrix = dict(result.get("visible_feature_matrix", {}))
    return "\n".join(
        [
            "# S4.6 Google-Unit Source Freeze",
            "",
            f"- Decision: `{result.get('decision')}`",
            f"- Rows: `{int(matrix.get('record_count', 0))}`",
            f"- Features: `{int(matrix.get('feature_count', 0))}`",
            f"- Assignment unit: `{ASSIGNMENT_UNIT}`",
            "",
        ]
    )


def format_google_unit_source_expansion_summary(result: Mapping[str, object]) -> str:
    transfer = dict(result.get("expanded_transfer_report", {}))
    strict = dict(transfer.get("strict_frozen_transfer", {}))
    return "\n".join(
        [
            "# S4.6 Google-Unit Source Expansion",
            "",
            f"- Decision: `{result.get('decision')}`",
            f"- Freeze dir: `{result.get('freeze_dir')}`",
            f"- Heldout strict raw replay: `{float(strict.get('raw_target_only', 0.0)):.6f}`",
            "",
        ]
    )


def _defaulted_public_fields(public: Mapping[str, object]) -> dict[str, object]:
    return {
        "dataset_name": str(public.get("dataset_name", "google_v2_public_signature")),
        "dataset_family": str(public.get("dataset_family", "surface")),
        "basis": str(public.get("basis", "X")).upper() if str(public.get("basis", "X")).upper() in {"X", "Z"} else "X",
        "distance": int(public.get("distance", 3) or 3),
        "rounds": int(public.get("rounds", 3) or 3),
        "round_band": _safe_round_band(public.get("round_band", "all")),
        "region_family": _safe_region_family(public.get("region_family", "full_patch")),
        "patch_public_geometry_class": str(public.get("patch_public_geometry_class", "synthetic_google_unit_patch")),
    }


def _context_from_public_fields(public: Mapping[str, object]) -> _PublicSignatureContext:
    fields = _defaulted_public_fields(public)
    return _PublicSignatureContext(
        dataset_name=str(fields["dataset_name"]),
        dataset_family=str(fields["dataset_family"]),
        basis=str(fields["basis"]),
        distance=int(fields["distance"]),
        rounds=int(fields["rounds"]),
        patch_public_geometry_class=str(fields["patch_public_geometry_class"]),
    )


def _safe_round_band(value: object) -> str:
    parsed = str(value or "all")
    return _normalize_round_bands((parsed,))[0] if parsed in {"early", "mid", "late", "all"} else "all"


def _safe_region_family(value: object) -> str:
    parsed = str(value or "full_patch")
    allowed = {
        "boundary_adjacent",
        "bulk",
        "logical_support_neighborhood",
        "interior_chain",
        "full_patch",
    }
    return _normalize_region_families((parsed,))[0] if parsed in allowed else "full_patch"


def _split_name_for_index(idx: int, split: Mapping[str, object]) -> str:
    if int(idx) in {int(value) for value in split.get("design", [])}:
        return "design"
    if int(idx) in {int(value) for value in split.get("validation", [])}:
        return "validation"
    if int(idx) in {int(value) for value in split.get("heldout_eval", [])}:
        return "heldout_eval"
    return "unassigned"


def _mixture_logical_support(records: list[dict[str, object]], label_weights: Mapping[str, float], *, detector_count: int) -> set[int]:
    label_to_record = {
        str(record.get("oracle_label", record.get("mechanism_id", f"M{idx}"))): record for idx, record in enumerate(records)
    }
    support: set[int] = set()
    for label, weight in label_weights.items():
        if float(weight) <= 0.0:
            continue
        record = label_to_record.get(str(label))
        if record is not None:
            support.update(_record_logical_support(record, detector_count=detector_count))
    return support or set(range(int(detector_count)))


def _control_report(controls: Mapping[str, np.ndarray], transfer: Mapping[str, object]) -> dict[str, object]:
    metrics = dict(transfer.get("controls", {})) if isinstance(transfer.get("controls", {}), Mapping) else {}
    return {
        "schema": "scope_static_stage4_6_controls_v1",
        "control_names": list(CONTROL_NAMES),
        "baseline_names": list(BASELINE_NAMES),
        "matrix_shapes": {name: [int(dim) for dim in np.asarray(matrix).shape] for name, matrix in sorted(controls.items())},
        "heldout_transfer_metrics": {name: metrics.get(name, {}) for name in CONTROL_NAMES},
        "heldout_baseline_metrics": {name: metrics.get(name, {}) for name in BASELINE_NAMES},
        "control_construction": {
            "control_target_mean_std_only": {
                "uses_google_design_split_rows": True,
                "uses_google_validation_rows": False,
                "uses_google_heldout_eval_rows": False,
                "uses_source_row_geometry": False,
                "preserves_source_standardized_geometry": False,
                "construction": "independent deterministic Gaussian moment match from Google design mean/std only",
                "purpose": "pure marginal/statistical alignment control without source codebook geometry",
            },
            "dmle_qec_visible_marginal_mle": {
                "baseline_family": "dmle_qec",
                "visible_surface_projection": True,
                "uses_dem_parity_map": False,
                "uses_upstream_dmle_qec_tensor_network": False,
            },
        },
        "used_for_model_selection": False,
    }


def _gap_closure(frozen: Mapping[str, object], *, global_null: Mapping[str, object], train_on_google: Mapping[str, object]) -> dict[str, object]:
    global_score = float(global_null.get("raw_target_only", 0.0) or 0.0)
    frozen_score = float(frozen.get("raw_target_only", 0.0) or 0.0)
    native_score = float(train_on_google.get("raw_target_only", 0.0) or 0.0)
    denom = max(global_score - native_score, 1.0e-12)
    return {
        "schema": "scope_static_stage4_6_gap_closure_v1",
        "fraction_of_train_on_google_gain_closed": float((global_score - frozen_score) / denom),
        "global_null_raw_target_only": global_score,
        "frozen_source_raw_target_only": frozen_score,
        "train_on_google_raw_target_only": native_score,
    }


def _affine_match_source_to_calibration(source_matrix: np.ndarray, calibration: np.ndarray) -> np.ndarray:
    s_mean = np.mean(source_matrix, axis=0, keepdims=True)
    s_std = np.where(np.std(source_matrix, axis=0, keepdims=True) > 1.0e-12, np.std(source_matrix, axis=0, keepdims=True), 1.0)
    t_mean = np.mean(calibration, axis=0, keepdims=True)
    t_std = np.std(calibration, axis=0, keepdims=True)
    return _finite(((source_matrix - s_mean) / s_std) * t_std + t_mean)


def _better(left: Mapping[str, object], right: Mapping[str, object], key: str) -> bool:
    return float(left.get(key, 0.0) or 0.0) < float(right.get(key, 0.0) or 0.0) - 1.0e-12


def _empty_replay_metrics(model_family: str) -> dict[str, object]:
    return {
        "schema": "scope_static_stage4_visible_replay_metrics_v1",
        "model_family": model_family,
        "raw_target_only": 0.0,
        "block_normalized": 0.0,
        "mse": 0.0,
        "mae": 0.0,
        "lower_is_better": True,
    }


def _nearest_self_distances(x: np.ndarray) -> np.ndarray:
    if x.shape[0] <= 1:
        return np.zeros(0, dtype=np.float64)
    distances = _nearest_cross_distances(x, x, exclude_self=True)
    return distances


def _nearest_cross_distances(left: np.ndarray, right: np.ndarray, *, exclude_self: bool = False) -> np.ndarray:
    if left.size == 0 or right.size == 0:
        return np.zeros(0, dtype=np.float64)
    out = np.zeros(left.shape[0], dtype=np.float64)
    chunk = 512
    for start in range(0, left.shape[0], chunk):
        stop = min(start + chunk, left.shape[0])
        dist = np.sqrt(np.maximum(np.sum((left[start:stop, None, :] - right[None, :, :]) ** 2, axis=2), 0.0))
        if exclude_self and left.shape[0] == right.shape[0]:
            for row in range(start, stop):
                dist[row - start, row] = np.inf
        out[start:stop] = np.min(dist, axis=1)
    return out


def _as_int_labels(values: Iterable[object]) -> list[int]:
    mapping: dict[str, int] = {}
    out = []
    for value in values:
        key = str(value)
        if key not in mapping:
            mapping[key] = len(mapping)
        out.append(mapping[key])
    return out


def _resize_labels(values: np.ndarray, size: int) -> list[int]:
    if values.size == 0:
        return [0 for _ in range(int(size))]
    return [int(values[idx % values.size]) for idx in range(int(size))]


def _optional_positive_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    parsed = int(value)
    if parsed <= 0:
        raise ValueError("positive integer expected when provided")
    return parsed


def _public_key(public_fields: Mapping[str, object]) -> dict[str, object]:
    keys = ["dataset_name", "dataset_family", "basis", "distance", "rounds", "round_band", "region_family", "patch_public_geometry_class"]
    return {key: public_fields.get(key) for key in keys}


def _stable_int(payload: object) -> int:
    text = json.dumps(_json_safe(payload), sort_keys=True)
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16) % (2**31 - 1)


def _finite(matrix: np.ndarray) -> np.ndarray:
    return np.nan_to_num(np.asarray(matrix, dtype=np.float64), nan=0.0, posinf=0.0, neginf=0.0)
