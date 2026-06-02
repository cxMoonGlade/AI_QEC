from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
from typing import Iterable, Mapping

import numpy as np
import yaml

from scope_static.google.s3_visible_common import _json_safe
from scope_static.google.s3_visible_surface_v2 import (
    DEFAULT_REGION_FAMILIES,
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


STAGE_NAME = "Stage4_0_synthetic_google_shaped_bridge_freeze"
DEFAULT_OUTPUT_DIR = "outputs/scope_static/S4_bridge/S4_0_synthetic_google_shaped_freeze/S3A_protocol_freeze"
DEFAULT_ASSIGNMENT_UNIT = "synthetic_google_shaped_mechanism_signature"
DEFAULT_ROUND_BANDS = ("all",)
DEFAULT_REGION_FAMILIES = ("full_patch",)
FORBIDDEN_LABEL_VISIBILITY = ("evaluator_only", "forbidden")


def write_stage4_synthetic_google_shaped_freeze(
    *,
    teacher_dir: str | Path,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    google_stage3a_dir: str | Path | None = None,
    round_bands: Iterable[str] = DEFAULT_ROUND_BANDS,
    region_families: Iterable[str] = DEFAULT_REGION_FAMILIES,
    split_policy: str = "leave_one_context_group_out",
    dataset_family: str = "synthetic_controlled_catalog",
    basis: str = "X",
    distance: int | None = None,
    rounds: int | None = None,
    shotblock_size: int = 16,
    max_source_shots_per_record: int | None = None,
    mirror_public_context_from_google_v2: bool = False,
    max_mirrored_public_contexts: int | None = None,
    emit_context_rows: bool = False,
    align_visible_feature_marginals_to_google_v2: bool = False,
    seed: int = 0,
) -> dict[str, object]:
    """Project controlled-catalog observations into a Google V2-shaped freeze."""

    teacher = Path(teacher_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    records = _load_mechanism_records(teacher / "oracle_mechanisms.json")
    observations, probe_names, shots = _load_observations(teacher / "observations.npz")
    if not records:
        raise ValueError("controlled catalog teacher must contain at least one mechanism record")
    if observations.ndim != 3:
        raise ValueError("observations.npz observations must have shape [num_probes, shots, num_qubits]")
    bands = _normalize_round_bands(tuple(round_bands))
    regions = _normalize_region_families(tuple(region_families))
    if int(shotblock_size) <= 0:
        raise ValueError("shotblock_size must be positive")
    max_source_shots = _optional_positive_int(max_source_shots_per_record)
    n_qubits = int(observations.shape[2])
    detector_count = n_qubits
    observable_count = 1
    context = _PublicSignatureContext(
        dataset_name="synthetic_controlled_catalog",
        dataset_family=str(dataset_family),
        basis=str(basis).upper() if str(basis).upper() in {"X", "Z"} else "X",
        distance=int(distance) if distance is not None else int(max(1, n_qubits)),
        rounds=int(rounds) if rounds is not None else int(max(1, len(probe_names))),
        patch_public_geometry_class="synthetic_line_patch",
    )
    coords = _synthetic_detector_coords(detector_count)
    boundary = {0, detector_count - 1} if detector_count > 1 else {0}
    context_specs = _public_context_specs(
        default_context=context,
        bands=bands,
        regions=regions,
        google_stage3a_dir=google_stage3a_dir,
        mirror_public_context_from_google_v2=bool(mirror_public_context_from_google_v2),
        max_mirrored_public_contexts=max_mirrored_public_contexts,
    )
    rows: list[np.ndarray] = []
    sampled_rows: list[np.ndarray] = []
    assignment_instances: list[dict[str, object]] = []
    signature_rows: list[dict[str, object]] = []
    evaluator_records: list[dict[str, object]] = []
    replicate_rows_by_unit: list[np.ndarray] = []
    detector_rate_means: list[float] = []
    logical_rate_means: list[float] = []

    for source_idx, record in enumerate(records):
        local_observations = _record_google_shaped_observations(
            record,
            observations,
            max_source_shots=max_source_shots,
        )
        logical_support = _record_logical_support(record, detector_count=detector_count)
        context_rows: list[tuple[np.ndarray, dict[str, float], dict[str, object]]] = []
        for spec in context_specs:
            round_band = str(spec["round_band"])
            region = str(spec["region_family"])
            row_context = spec["context"]
            if not isinstance(row_context, _PublicSignatureContext):
                raise TypeError("internal public context spec must carry _PublicSignatureContext")
            round_detectors = _detectors_for_round_band(coords, detector_count=detector_count, round_band=round_band)
            region_detectors = _detectors_for_region(
                region,
                detector_count=detector_count,
                boundary_detectors=boundary,
                logical_support_detectors=logical_support,
                coords=coords,
            )
            selected = sorted(set(round_detectors).intersection(region_detectors)) or sorted(range(detector_count))
            feature_row, support = _signature_feature_row(
                local_observations,
                context=row_context,
                coords=coords,
                boundary_detectors=boundary,
                logical_support_detectors=logical_support,
                selected_detectors=selected,
                detector_count=detector_count,
                observable_count=observable_count,
                round_band=round_band,
                region_family=region,
                shotblocks=_shotblocks(local_observations.shape[0], int(shotblock_size)),
            )
            feature_row = _override_mirrored_public_geometry(feature_row, spec)
            context_rows.append((feature_row, support, dict(spec["public_fields"])))
        label = str(record.get("oracle_label", record.get("mechanism_id", f"M{source_idx}")))
        quotient = str(record.get("quotient_label", label))
        if bool(emit_context_rows):
            for feature_row, support, public_fields in context_rows:
                _append_projected_row(
                    rows=rows,
                    sampled_rows=sampled_rows,
                    replicate_rows_by_unit=replicate_rows_by_unit,
                    detector_rate_means=detector_rate_means,
                    logical_rate_means=logical_rate_means,
                    assignment_instances=assignment_instances,
                    signature_rows=signature_rows,
                    evaluator_records=evaluator_records,
                    feature_row=feature_row,
                    replicate_rows=np.asarray([feature_row], dtype=np.float64),
                    support_values=[support],
                    public_fields=public_fields,
                    source_idx=source_idx,
                    record=record,
                    label=label,
                    quotient=quotient,
                    teacher=teacher,
                    observation_probe_count=int(observations.shape[0]),
                    local_observation_count=int(local_observations.shape[0]),
                )
        else:
            feature_rows = [row for row, _support, _public in context_rows]
            support_values = [support for _row, support, _public in context_rows]
            row = np.mean(np.asarray(feature_rows, dtype=np.float64), axis=0)
            public_fields = {
                "dataset_family": str(dataset_family),
                "basis": context.basis,
                "distance": context.distance,
                "rounds": context.rounds,
                "round_band": "mixed" if len({str(spec["round_band"]) for spec in context_specs}) > 1 else str(context_specs[0]["round_band"]),
                "region_family": "mixed" if len({str(spec["region_family"]) for spec in context_specs}) > 1 else str(context_specs[0]["region_family"]),
                "patch_public_geometry_class": context.patch_public_geometry_class,
            }
            _append_projected_row(
                rows=rows,
                sampled_rows=sampled_rows,
                replicate_rows_by_unit=replicate_rows_by_unit,
                detector_rate_means=detector_rate_means,
                logical_rate_means=logical_rate_means,
                assignment_instances=assignment_instances,
                signature_rows=signature_rows,
                evaluator_records=evaluator_records,
                feature_row=row,
                replicate_rows=np.asarray(feature_rows, dtype=np.float64),
                support_values=support_values,
                public_fields=public_fields,
                source_idx=source_idx,
                record=record,
                label=label,
                quotient=quotient,
                teacher=teacher,
                observation_probe_count=int(observations.shape[0]),
                local_observation_count=int(local_observations.shape[0]),
            )

    matrix = _finite(np.asarray(rows, dtype=np.float64))
    sampled = _finite(np.asarray(sampled_rows, dtype=np.float64))
    google_distribution_alignment = None
    if bool(align_visible_feature_marginals_to_google_v2) and google_stage3a_dir is not None:
        matrix, sampled, google_distribution_alignment = _align_visible_feature_marginals_to_google_v2(
            matrix=matrix,
            sampled=sampled,
            google_stage3a_dir=Path(google_stage3a_dir),
        )
    feature_schema = _feature_schema(list(FEATURE_NAMES))
    visible_feature_matrix = _visible_feature_matrix_manifest(matrix, sampled)
    split_manifest = _split_manifest(assignment_instances, split_policy=str(split_policy))
    forbidden = forbidden_feature_audit_google_v2(FEATURE_NAMES)
    adequacy = _adequacy_report(
        matrix,
        replicate_rows_by_unit=replicate_rows_by_unit,
        feature_names=list(FEATURE_NAMES),
        assignment_instances=assignment_instances,
        forbidden_audit=forbidden,
    )
    adequacy["surface_source"] = "synthetic_controlled_catalog_google_shaped_projection"
    acceptance = _acceptance_audit(
        forbidden_audit=forbidden,
        split_manifest=split_manifest,
        visible_feature_matrix=visible_feature_matrix,
        adequacy_report=adequacy,
    )
    source_label_manifest = _source_label_manifest()
    source_evaluator_labels = _source_evaluator_labels(evaluator_records)
    bridge_contract = _bridge_contract_audit(
        feature_schema=feature_schema,
        visible_feature_matrix=visible_feature_matrix,
        forbidden_feature_audit=forbidden,
        source_label_manifest=source_label_manifest,
    )
    schema_compatibility_with_google_v2 = None
    if google_stage3a_dir is not None:
        google_dir = Path(google_stage3a_dir)
        if google_dir.exists():
            schema_compatibility_with_google_v2 = _compare_stage4_bridge_contract_payloads(
                synthetic_dir=output,
                google_dir=google_dir,
                synthetic_schema=feature_schema,
                synthetic_manifest=visible_feature_matrix,
            )
        else:
            schema_compatibility_with_google_v2 = {
                "schema": "scope_static_stage4_bridge_contract_comparator_v1",
                "passed": False,
                "synthetic_dir": str(output),
                "google_dir": str(google_dir),
                "error": "google_stage3a_dir_missing",
            }
    comparator_passed = (
        schema_compatibility_with_google_v2 is None
        or bool(dict(schema_compatibility_with_google_v2).get("passed", False))
    )
    alignment_passed = google_distribution_alignment is None or bool(google_distribution_alignment.get("passed", False))
    result = {
        "schema": "scope_static_stage4_synthetic_google_shaped_freeze_v1",
        "stage": STAGE_NAME,
        "output_dir": str(output),
        "teacher_dir": str(teacher),
        "claim_boundary": {
            "synthetic_source_not_real_google_data": True,
            "uses_controlled_catalog_teacher_observations": True,
            "learner_visible_surface_kind": "synthetic Google-shaped public syndrome-response signatures",
            "contains_catalog_m_labels_as_learner_input": False,
            "contains_true_hidden_mechanism_labels": False,
            "contains_oracle_channel_ptm_kraus": False,
            "mechanism_survival_audit_required_before_neural_training": True,
        },
        "config": {
            "teacher_dir": str(teacher),
            "output_dir": str(output),
            "google_stage3a_dir": str(google_stage3a_dir) if google_stage3a_dir is not None else None,
            "round_bands": list(bands),
            "region_families": list(regions),
            "split_policy": str(split_policy),
            "dataset_family": str(dataset_family),
            "basis": context.basis,
            "distance": context.distance,
            "rounds": context.rounds,
            "shotblock_size": int(shotblock_size),
            "max_source_shots_per_record": max_source_shots,
            "mirror_public_context_from_google_v2": bool(mirror_public_context_from_google_v2),
            "max_mirrored_public_contexts": _optional_positive_int(max_mirrored_public_contexts),
            "emit_context_rows": bool(emit_context_rows),
            "emitted_public_context_count": int(len(context_specs)),
            "mirrors_google_public_geometry_numeric_features": bool(
                context_specs and isinstance(context_specs[0].get("meta_feature_values"), Mapping)
            ),
            "align_visible_feature_marginals_to_google_v2": bool(align_visible_feature_marginals_to_google_v2),
            "seed": int(seed),
        },
        "visible_feature_schema": feature_schema,
        "visible_feature_matrix": visible_feature_matrix,
        "split_manifest": split_manifest,
        "forbidden_feature_audit": forbidden,
        "adequacy_report": adequacy,
        "acceptance_audit": acceptance,
        "bridge_contract_audit": bridge_contract,
        "schema_compatibility_with_google_v2": schema_compatibility_with_google_v2,
        "google_distribution_alignment_audit": google_distribution_alignment,
        "probe_schedule_manifest": _probe_schedule_manifest(probe_names),
        "signature_schedule_manifest": _signature_schedule_manifest(signature_rows, bands=bands, regions=regions),
        "batch_context_schema": _batch_context_schema(len(assignment_instances)),
        "assignment_unit": _assignment_unit_manifest(len(assignment_instances), len(records)),
        "source_label_manifest_path": "source_label_manifest.json",
        "source_evaluator_labels_path": "source_evaluator_labels.json",
        "decision": "stage4_synthetic_bridge_freeze_passed"
        if acceptance["passed"] and bridge_contract["passed"] and comparator_passed and alignment_passed
        else "stage4_synthetic_bridge_freeze_failed",
    }
    _write_outputs(output, result, matrix, sampled, source_label_manifest, source_evaluator_labels)
    return result


def compare_stage4_bridge_contract(*, synthetic_dir: str | Path, google_dir: str | Path) -> dict[str, object]:
    synthetic = Path(synthetic_dir)
    google = Path(google_dir)
    syn_schema = _load_json(synthetic / "visible_feature_schema.json")
    syn_manifest = _load_json(synthetic / "visible_feature_matrix.json")
    return _compare_stage4_bridge_contract_payloads(
        synthetic_dir=synthetic,
        google_dir=google,
        synthetic_schema=syn_schema,
        synthetic_manifest=syn_manifest,
    )


def _compare_stage4_bridge_contract_payloads(
    *,
    synthetic_dir: str | Path,
    google_dir: str | Path,
    synthetic_schema: Mapping[str, object],
    synthetic_manifest: Mapping[str, object],
) -> dict[str, object]:
    synthetic = Path(synthetic_dir)
    google = Path(google_dir)
    goo_schema = _load_json(google / "visible_feature_schema.json")
    syn_names = _feature_names(synthetic_schema)
    goo_names = _feature_names(goo_schema)
    goo_manifest = _load_json(google / "visible_feature_matrix.json")
    checks = {
        "feature_names_match": syn_names == goo_names,
        "feature_count_match": int(synthetic_manifest.get("feature_count", -1)) == int(goo_manifest.get("feature_count", -2)),
        "block_order_match": list(_block_indices(syn_names).keys()) == list(_block_indices(goo_names).keys()),
        "dtype_policy_match": str(synthetic_manifest.get("dtype", "float64")) == str(goo_manifest.get("dtype", "float64")),
        "normalization_policy_match": str(synthetic_manifest.get("normalization_policy", "none")) == str(
            goo_manifest.get("normalization_policy", "none")
        ),
    }
    return {
        "schema": "scope_static_stage4_bridge_contract_comparator_v1",
        "passed": bool(all(checks.values())),
        "synthetic_dir": str(synthetic),
        "google_dir": str(google),
        "checks": checks,
        "synthetic_feature_count": int(len(syn_names)),
        "google_feature_count": int(len(goo_names)),
        "mismatch_count": int(sum(1 for left, right in zip(syn_names, goo_names) if left != right) + abs(len(syn_names) - len(goo_names))),
    }


def _write_outputs(
    output: Path,
    result: dict[str, object],
    visible_features: np.ndarray,
    sampled_visible_features: np.ndarray,
    source_label_manifest: dict[str, object],
    source_evaluator_labels: dict[str, object],
) -> None:
    artifacts = {
        "metrics.json": result,
        "visible_feature_schema.json": result["visible_feature_schema"],
        "visible_feature_matrix.json": result["visible_feature_matrix"],
        "forbidden_feature_audit.json": result["forbidden_feature_audit"],
        "split_manifest.json": result["split_manifest"],
        "probe_schedule_manifest.json": result["probe_schedule_manifest"],
        "signature_schedule_manifest.json": result["signature_schedule_manifest"],
        "batch_context_schema.json": result["batch_context_schema"],
        "assignment_unit.json": result["assignment_unit"],
        "adequacy_report.json": result["adequacy_report"],
        "acceptance_audit.json": result["acceptance_audit"],
        "bridge_contract_audit.json": result["bridge_contract_audit"],
        "schema_compatibility_with_google_v2.json": result["schema_compatibility_with_google_v2"],
        "google_distribution_alignment_audit.json": result["google_distribution_alignment_audit"],
        "source_label_manifest.json": source_label_manifest,
        "source_evaluator_labels.json": source_evaluator_labels,
    }
    for name, payload in artifacts.items():
        if payload is not None:
            (output / name).write_text(json.dumps(_json_safe(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    np.save(output / "visible_features.npy", np.asarray(visible_features, dtype=np.float64))
    np.save(output / "sampled_visible_features.npy", np.asarray(sampled_visible_features, dtype=np.float64))
    (output / "config.yaml").write_text(yaml.safe_dump({"stage4_synthetic_google_surface_v1": result["config"]}, sort_keys=False), encoding="utf-8")
    (output / "summary.md").write_text(format_stage4_synthetic_freeze_summary(result), encoding="utf-8")


def format_stage4_synthetic_freeze_summary(result: Mapping[str, object]) -> str:
    acceptance = dict(result.get("acceptance_audit", {}))
    matrix = dict(result.get("visible_feature_matrix", {}))
    return "\n".join(
        [
            "# S4.0 Synthetic Google-Shaped Bridge Freeze",
            "",
            f"- Decision: `{result.get('decision')}`",
            f"- Acceptance passed: `{str(bool(acceptance.get('passed', False))).lower()}`",
            f"- Rows: `{int(matrix.get('record_count', 0))}`",
            f"- Features: `{int(matrix.get('feature_count', 0))}`",
            "",
            "## Claim Boundary",
            "",
            "This artifact projects controlled-catalog sampled observations into a Google V2-shaped public syndrome-response surface. Mechanism labels and teacher objects are evaluator-only and are not learner-visible fields.",
            "",
        ]
    )


def _load_mechanism_records(path: Path) -> list[dict[str, object]]:
    data = _load_json(path)
    records = data.get("mechanisms")
    if not isinstance(records, list) or not records:
        raise ValueError(f"{path} does not contain non-empty mechanisms")
    return [dict(record) for record in records]


def _load_observations(path: Path) -> tuple[np.ndarray, list[str], int]:
    if not path.exists():
        raise FileNotFoundError(f"missing observations artifact: {path}")
    data = np.load(path, allow_pickle=True)
    observations = np.asarray(data["observations"])
    probe_names = [str(value) for value in data["probe_names"].tolist()] if "probe_names" in data.files else [f"probe_{idx}" for idx in range(observations.shape[0])]
    shots = int(data["shots"][0]) if "shots" in data.files else int(observations.shape[1])
    return observations, probe_names, shots


def _record_google_shaped_observations(record: Mapping[str, object], observations: np.ndarray, *, max_source_shots: int | None) -> np.ndarray:
    indices = _record_probe_indices(record, observations.shape[0])
    detector_bits = np.asarray(observations[indices]).reshape(-1, observations.shape[2])
    if max_source_shots is not None and detector_bits.shape[0] > max_source_shots:
        selected_rows = np.linspace(0, detector_bits.shape[0] - 1, int(max_source_shots), dtype=np.int64)
        detector_bits = detector_bits[selected_rows]
    qubits = [idx for idx in _record_qubits(record, observations.shape[2]) if 0 <= idx < observations.shape[2]]
    selected = detector_bits[:, qubits] if qubits else detector_bits
    logical = np.mod(np.sum(selected, axis=1), 2.0).reshape(-1, 1)
    return np.concatenate([detector_bits, logical], axis=1)


def _append_projected_row(
    *,
    rows: list[np.ndarray],
    sampled_rows: list[np.ndarray],
    replicate_rows_by_unit: list[np.ndarray],
    detector_rate_means: list[float],
    logical_rate_means: list[float],
    assignment_instances: list[dict[str, object]],
    signature_rows: list[dict[str, object]],
    evaluator_records: list[dict[str, object]],
    feature_row: np.ndarray,
    replicate_rows: np.ndarray,
    support_values: list[dict[str, float]],
    public_fields: dict[str, object],
    source_idx: int,
    record: Mapping[str, object],
    label: str,
    quotient: str,
    teacher: Path,
    observation_probe_count: int,
    local_observation_count: int,
) -> None:
    j = int(len(rows))
    row = np.asarray(feature_row, dtype=np.float64)
    rows.append(row)
    sampled_rows.append(row.copy())
    replicate_rows_by_unit.append(np.asarray(replicate_rows, dtype=np.float64))
    detector_rate_means.append(float(np.mean([value["detector_rate_mean"] for value in support_values])) if support_values else 0.0)
    logical_rate_means.append(float(np.mean([value["logical_rate_mean"] for value in support_values])) if support_values else 0.0)
    assignment_instances.append(
        {
            "j": j,
            "record_index": j,
            "visible_instance_id": f"s4srcj{j:06d}",
            "context_group": j,
            "assignment_unit": DEFAULT_ASSIGNMENT_UNIT,
            "unit_id_internal_only": f"synthetic_signature_unit_{j:06d}",
            "public_fields": public_fields,
            "source_probe_count": int(len(_record_probe_indices(record, observation_probe_count))),
            "source_shot_count_total": int(local_observation_count),
            "source_record_index_evaluator_only": int(source_idx),
        }
    )
    signature_rows.append({"j": j, "public_fields": public_fields, "source_shot_count_total": int(local_observation_count)})
    evaluator_records.append(
        {
            "j": j,
            "exact_mechanism_label": label,
            "quotient_label": quotient,
            "alias_label": quotient,
            "mechanism_family": str(record.get("name", record.get("mechanism_family", label))),
            "mechanism_set": str(record.get("mechanism_set", "controlled_catalog")),
            "teacher_config_hash": _file_digest(teacher / "teacher_config.json"),
            "source_record_index": int(source_idx),
        }
    )


def _public_context_specs(
    *,
    default_context: _PublicSignatureContext,
    bands: tuple[str, ...],
    regions: tuple[str, ...],
    google_stage3a_dir: str | Path | None,
    mirror_public_context_from_google_v2: bool,
    max_mirrored_public_contexts: int | None,
) -> list[dict[str, object]]:
    if mirror_public_context_from_google_v2 and google_stage3a_dir is not None:
        google_dir = Path(google_stage3a_dir)
        manifest_path = google_dir / "split_manifest.json"
        if manifest_path.exists():
            rows = _google_public_context_rows(google_dir)
            limit = _optional_positive_int(max_mirrored_public_contexts)
            if limit is not None and len(rows) > limit:
                indices = np.linspace(0, len(rows) - 1, int(limit), dtype=np.int64)
                rows = [rows[int(idx)] for idx in indices.tolist()]
            return rows
    out = []
    for band in bands:
        for region in regions:
            public_fields = {
                "dataset_family": default_context.dataset_family,
                "dataset_name": default_context.dataset_name,
                "basis": default_context.basis,
                "distance": default_context.distance,
                "rounds": default_context.rounds,
                "round_band": str(band),
                "region_family": str(region),
                "patch_public_geometry_class": default_context.patch_public_geometry_class,
            }
            out.append(
                {
                    "context": default_context,
                    "round_band": str(band),
                    "region_family": str(region),
                    "public_fields": public_fields,
                }
            )
    return out


def _override_mirrored_public_geometry(feature_row: np.ndarray, spec: Mapping[str, object]) -> np.ndarray:
    values = spec.get("meta_feature_values")
    if not isinstance(values, Mapping):
        return feature_row
    out = np.asarray(feature_row, dtype=np.float64).copy()
    name_to_idx = {name: idx for idx, name in enumerate(FEATURE_NAMES)}
    for name, value in values.items():
        idx = name_to_idx.get(str(name))
        if idx is not None:
            out[int(idx)] = float(value)
    return out


def _google_public_context_rows(google_dir: Path) -> list[dict[str, object]]:
    payload = _load_json(google_dir / "split_manifest.json")
    meta_values = _google_public_geometry_feature_values(google_dir)
    rows = payload.get("assignment_instances", [])
    if not isinstance(rows, list):
        return []
    seen: set[tuple[object, ...]] = set()
    out: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        public = dict(row.get("public_fields", {})) if isinstance(row.get("public_fields", {}), Mapping) else {}
        row_index = int(row.get("j", row.get("record_index", len(out))))
        key = (
            public.get("dataset_name"),
            public.get("dataset_family"),
            public.get("basis"),
            public.get("distance"),
            public.get("rounds"),
            public.get("round_band"),
            public.get("region_family"),
            public.get("patch_public_geometry_class"),
        )
        if key in seen:
            continue
        seen.add(key)
        basis = str(public.get("basis", "X")).upper()
        context = _PublicSignatureContext(
            dataset_name=str(public.get("dataset_name", "google_v2_public_context_mirror")),
            dataset_family=str(public.get("dataset_family", "surface")),
            basis=basis if basis in {"X", "Z"} else "X",
            distance=int(public.get("distance", 0) or 0),
            rounds=int(public.get("rounds", 0) or 0),
            patch_public_geometry_class=str(public.get("patch_public_geometry_class", "google_v2_public_context_mirror")),
        )
        out.append(
            {
                "context": context,
                "round_band": str(public.get("round_band", "all")),
                "region_family": str(public.get("region_family", "full_patch")),
                "public_fields": public,
                "meta_feature_values": meta_values.get(row_index, {}),
            }
        )
    return out


def _google_public_geometry_feature_values(google_dir: Path) -> dict[int, dict[str, float]]:
    schema_path = google_dir / "visible_feature_schema.json"
    matrix_path = google_dir / "visible_features.npy"
    if not schema_path.exists() or not matrix_path.exists():
        return {}
    schema = _load_json(schema_path)
    names = _feature_names(schema)
    meta_indices = [(idx, name) for idx, name in enumerate(names) if str(name).startswith("meta__public_geometry")]
    matrix = np.asarray(np.load(matrix_path), dtype=np.float64)
    out: dict[int, dict[str, float]] = {}
    for row_idx in range(int(matrix.shape[0])):
        out[row_idx] = {name: float(matrix[row_idx, idx]) for idx, name in meta_indices}
    return out


def _align_visible_feature_marginals_to_google_v2(
    *,
    matrix: np.ndarray,
    sampled: np.ndarray,
    google_stage3a_dir: Path,
) -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    google_path = google_stage3a_dir / "visible_features.npy"
    if not google_path.exists():
        return matrix, sampled, {
            "schema": "scope_static_stage4_google_distribution_alignment_audit_v1",
            "passed": False,
            "uses_google_labels": False,
            "error": "google_visible_features_missing",
            "google_stage3a_dir": str(google_stage3a_dir),
        }
    google = np.asarray(np.load(google_path), dtype=np.float64)
    if google.ndim != 2 or google.shape[1] != matrix.shape[1]:
        return matrix, sampled, {
            "schema": "scope_static_stage4_google_distribution_alignment_audit_v1",
            "passed": False,
            "uses_google_labels": False,
            "error": "google_visible_feature_shape_mismatch",
            "source_shape": [int(dim) for dim in matrix.shape],
            "google_shape": [int(dim) for dim in google.shape],
        }
    source_mean = np.mean(matrix, axis=0) if matrix.size else np.zeros(matrix.shape[1], dtype=np.float64)
    source_std = np.std(matrix, axis=0) if matrix.size else np.ones(matrix.shape[1], dtype=np.float64)
    google_mean = np.mean(google, axis=0) if google.size else np.zeros(google.shape[1], dtype=np.float64)
    google_std = np.std(google, axis=0) if google.size else np.ones(google.shape[1], dtype=np.float64)
    safe_source_std = np.where(source_std > 1.0e-12, source_std, 1.0)
    aligned = ((matrix - source_mean[None, :]) / safe_source_std[None, :]) * google_std[None, :] + google_mean[None, :]
    aligned_sampled = ((sampled - source_mean[None, :]) / safe_source_std[None, :]) * google_std[None, :] + google_mean[None, :]
    before_mean_abs = float(np.mean(np.abs(source_mean - google_mean))) if source_mean.size else 0.0
    before_std_abs = float(np.mean(np.abs(source_std - google_std))) if source_std.size else 0.0
    after_mean = np.mean(aligned, axis=0) if aligned.size else np.zeros_like(source_mean)
    after_std = np.std(aligned, axis=0) if aligned.size else np.ones_like(source_std)
    after_mean_abs = float(np.mean(np.abs(after_mean - google_mean))) if after_mean.size else 0.0
    after_std_abs = float(np.mean(np.abs(after_std - google_std))) if after_std.size else 0.0
    return _finite(aligned), _finite(aligned_sampled), {
        "schema": "scope_static_stage4_google_distribution_alignment_audit_v1",
        "passed": True,
        "method": "featurewise_affine_match_source_visible_marginals_to_google_v2_visible_marginals",
        "uses_google_labels": False,
        "uses_google_evaluator_only_fields": False,
        "uses_google_visible_features_only": True,
        "source_shape": [int(dim) for dim in matrix.shape],
        "google_shape": [int(dim) for dim in google.shape],
        "before_mean_abs_error": before_mean_abs,
        "before_std_abs_error": before_std_abs,
        "after_mean_abs_error": after_mean_abs,
        "after_std_abs_error": after_std_abs,
        "zero_source_scales_replaced_with_one": True,
    }


def _optional_positive_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    parsed = int(value)
    if parsed <= 0:
        raise ValueError("max_source_shots_per_record must be positive when provided")
    return parsed


def _record_probe_indices(record: Mapping[str, object], probe_count: int) -> list[int]:
    raw = record.get("probe_indices", [])
    if isinstance(raw, list) and raw:
        indices = [int(value) for value in raw]
    else:
        indices = list(range(int(probe_count)))
    return [idx for idx in indices if 0 <= idx < int(probe_count)] or list(range(int(probe_count)))


def _record_qubits(record: Mapping[str, object], detector_count: int) -> list[int]:
    raw = record.get("qubits", [])
    if isinstance(raw, list) and raw:
        return [int(value) for value in raw]
    return list(range(int(detector_count)))


def _record_logical_support(record: Mapping[str, object], *, detector_count: int) -> set[int]:
    support = {idx for idx in _record_qubits(record, detector_count) if 0 <= idx < int(detector_count)}
    return support or set(range(int(detector_count)))


def _synthetic_detector_coords(detector_count: int) -> dict[int, tuple[float, float, float]]:
    width = max(1, int(np.ceil(np.sqrt(max(1, detector_count)))))
    return {idx: (float(idx % width), float(idx // width), float(idx % 3)) for idx in range(int(detector_count))}


def _shotblocks(shot_count: int, size: int) -> tuple[tuple[int, int], ...]:
    n = int(shot_count)
    step = max(1, int(size))
    blocks = [(start, min(start + step, n)) for start in range(0, n, step)]
    return tuple(block for block in blocks if block[1] > block[0]) or ((0, n),)


def _visible_feature_matrix_manifest(matrix: np.ndarray, sampled: np.ndarray) -> dict[str, object]:
    names = list(FEATURE_NAMES)
    return {
        "schema": "scope_static_stage3a_visible_feature_matrix_v1",
        "training_matrix_path": "visible_features.npy",
        "training_matrix_kind": "synthetic_google_shaped_public_syndrome_response_signature_features",
        "sampled_matrix_path": "sampled_visible_features.npy",
        "sampled_matrix_kind": "same_synthetic_google_shaped_public_syndrome_response_signature_features",
        "feature_schema_path": "visible_feature_schema.json",
        "feature_count": int(matrix.shape[1]) if matrix.ndim == 2 else 0,
        "record_count": int(matrix.shape[0]) if matrix.ndim == 2 else 0,
        "shape": [int(dim) for dim in matrix.shape],
        "sampled_shape": [int(dim) for dim in sampled.shape],
        "dtype": "float64",
        "normalization_policy": "none",
        "sampling_mode": "synthetic_controlled_catalog_google_shaped_projection",
        "feature_names_sha256": _text_digest("\n".join(names)),
        "visible_features_sha256": _matrix_digest(matrix),
        "sampled_visible_features_sha256": _matrix_digest(sampled),
        "learner_training_source": "S4.0 synthetic Google-shaped frozen visible_features.npy",
        "contains_evaluator_labels": False,
        "contains_oracle_fields": False,
        "contains_context_path_sample_one_hot_features": False,
    }


def _split_manifest(assignment_instances: list[dict[str, object]], *, split_policy: str) -> dict[str, object]:
    groups = [int(row.get("context_group", idx)) for idx, row in enumerate(assignment_instances)]
    folds = []
    for fold_idx, test_group in enumerate(groups):
        validation_groups = [int(groups[(fold_idx + 1) % len(groups)])] if len(groups) >= 3 else []
        excluded = {int(test_group), *validation_groups}
        train_groups = [int(group) for group in groups if int(group) not in excluded]
        folds.append(
            {
                "fold": int(fold_idx),
                "train_groups": train_groups,
                "validation_groups": validation_groups,
                "test_groups": [int(test_group)],
                "train_indices": _indices_for_groups(assignment_instances, train_groups),
                "validation_indices": _indices_for_groups(assignment_instances, validation_groups),
                "test_indices": _indices_for_groups(assignment_instances, [int(test_group)]),
            }
        )
    non_empty = bool(groups and all(row["train_indices"] for row in folds) and all(row["validation_indices"] for row in folds) and all(row["test_indices"] for row in folds))
    return {
        "schema": "scope_static_stage3a_split_manifest_v1",
        "split_policy": str(split_policy),
        "split_policy_fixed_before_training": True,
        "group_key": "synthetic_google_shaped_signature_group",
        "assignment_unit": DEFAULT_ASSIGNMENT_UNIT,
        "record_count": int(len(assignment_instances)),
        "context_groups": groups,
        "fold_count": int(len(folds)),
        "folds": folds,
        "assignment_instances": assignment_instances,
        "contains_mechanism_labels_as_learner_fields": False,
        "validation_labels_available_to_model_selection": False,
        "test_labels_available_to_model_selection": False,
        "train_validation_test_splits_non_empty": non_empty,
    }


def _indices_for_groups(rows: list[dict[str, object]], groups: Iterable[int]) -> list[int]:
    selected = {int(group) for group in groups}
    return [idx for idx, row in enumerate(rows) if int(row.get("context_group", idx)) in selected]


def _source_label_manifest() -> dict[str, object]:
    fields = [
        ("exact_mechanism_label", "evaluator_only", "posthoc_eval", "Controlled-catalog M label; never learner-visible."),
        ("quotient_label", "evaluator_only", "posthoc_eval", "Observable quotient or alias class label for ceiling audits."),
        ("alias_label", "evaluator_only", "posthoc_eval", "Alias class used to report projection collapse."),
        ("mechanism_family", "evaluator_only", "posthoc_eval", "Mechanism taxonomy for audit summaries only."),
        ("mechanism_set", "evaluator_only", "posthoc_eval", "Catalog subset membership for audit summaries only."),
        ("teacher_config_hash", "evaluator_only", "posthoc_eval", "Reproducibility pointer, not model input."),
        ("source_record_index", "forbidden", "never", "Record index is an identity surrogate and cannot enter learner features."),
    ]
    return {
        "schema": "scope_static_stage4_source_label_manifest_v1",
        "fields": [
            {"field": field, "visibility": visibility, "allowed_use": allowed_use, "reason": reason}
            for field, visibility, allowed_use, reason in fields
        ],
        "learner_visible_label_fields": [],
        "evaluator_only_label_fields": [field for field, visibility, _allowed, _reason in fields if visibility == "evaluator_only"],
        "forbidden_label_fields": [field for field, visibility, _allowed, _reason in fields if visibility == "forbidden"],
    }


def _source_evaluator_labels(records: list[dict[str, object]]) -> dict[str, object]:
    exact = [str(row["exact_mechanism_label"]) for row in records]
    quotient = [str(row["quotient_label"]) for row in records]
    return {
        "schema": "scope_static_stage4_source_evaluator_labels_v1",
        "visibility": "evaluator_only",
        "used_for_training": False,
        "used_for_validation_selection": False,
        "records": records,
        "exact_mechanism_labels": exact,
        "quotient_labels": quotient,
        "exact_class_names": sorted(set(exact), key=_mechanism_sort_key),
        "quotient_class_names": sorted(set(quotient), key=_mechanism_sort_key),
    }


def _bridge_contract_audit(
    *,
    feature_schema: Mapping[str, object],
    visible_feature_matrix: Mapping[str, object],
    forbidden_feature_audit: Mapping[str, object],
    source_label_manifest: Mapping[str, object],
) -> dict[str, object]:
    fields = list(source_label_manifest.get("fields", [])) if isinstance(source_label_manifest.get("fields", []), list) else []
    checks = {
        "stage3a_visible_feature_matrix_schema": str(visible_feature_matrix.get("schema")) == "scope_static_stage3a_visible_feature_matrix_v1",
        "feature_schema_matches_google_v2_names": _feature_names(feature_schema) == list(FEATURE_NAMES),
        "forbidden_feature_audit_passed": bool(forbidden_feature_audit.get("passed", False)),
        "label_manifest_declares_no_training_labels": all(str(dict(row).get("allowed_use")) != "training" for row in fields),
        "label_manifest_marks_identity_fields_forbidden": any(
            str(dict(row).get("field")) == "source_record_index" and str(dict(row).get("visibility")) == "forbidden" for row in fields
        ),
    }
    return {
        "schema": "scope_static_stage4_bridge_contract_audit_v1",
        "passed": bool(all(checks.values())),
        "checks": checks,
    }


def _probe_schedule_manifest(probe_names: list[str]) -> dict[str, object]:
    return {
        "schema": "scope_static_stage4_synthetic_probe_schedule_manifest_v1",
        "source": "controlled catalog observations.npz probe_names",
        "probe_count": int(len(probe_names)),
        "examples": list(probe_names[:50]),
    }


def _signature_schedule_manifest(rows: list[dict[str, object]], *, bands: tuple[str, ...], regions: tuple[str, ...]) -> dict[str, object]:
    public_rows = [dict(row.get("public_fields", {})) for row in rows]
    return {
        "schema": "scope_static_stage4_synthetic_signature_schedule_manifest_v1",
        "assignment_unit": DEFAULT_ASSIGNMENT_UNIT,
        "round_bands": list(bands),
        "region_families": list(regions),
        "signature_unit_count": int(len(rows)),
        "round_band_counts": dict(sorted(Counter(str(row.get("round_band")) for row in public_rows).items())),
        "region_family_counts": dict(sorted(Counter(str(row.get("region_family")) for row in public_rows).items())),
        "selection_policy": [
            "project each controlled mechanism record to one synthetic Google-shaped public signature",
            "do not expose mechanism labels or teacher object fields as learner-visible features",
        ],
        "examples": rows[: min(50, len(rows))],
    }


def _batch_context_schema(row_count: int) -> dict[str, object]:
    return {
        "schema": "scope_static_stage3a_batch_context_schema_v1",
        "assignment_unit": DEFAULT_ASSIGNMENT_UNIT,
        "primary_protocol": {
            "mode": "synthetic_google_shaped_public_signature_batch",
            "context_group_key": "synthetic_google_shaped_signature_group",
            "context_group_count": int(row_count),
        },
        "learner_visible_fields": ["raw__*", "meta__public_geometry__*"],
        "protocol_only_fields": ["j", "fold", "train_validation_test_split", "public_fields", "unit_id_internal_only"],
        "evaluator_only_fields": ["exact_mechanism_label", "quotient_label", "alias_label", "mechanism_family"],
        "forbidden_learner_fields": ["source_record_index", "teacher_id", "path", "sample_id", "oracle_channel_ptm_kraus"],
    }


def _assignment_unit_manifest(row_count: int, source_record_count: int) -> dict[str, object]:
    return {
        "schema": "scope_static_stage3a_assignment_unit_v1",
        "assignment_matrix": "S[j,k] or Pi[j,k]",
        "j_definition": DEFAULT_ASSIGNMENT_UNIT,
        "j_description": "One synthetic Google-shaped public signature per controlled catalog mechanism record.",
        "single_shot_j_allowed_first_pass": False,
        "k_definition": "learned latent visible syndrome-response prototype",
        "record_count": int(row_count),
        "source_record_count": int(source_record_count),
        "catalog_cardinality_evaluator_only": int(source_record_count),
        "evaluator_mode": "controlled_catalog_evaluator_only",
    }


def _feature_names(schema: Mapping[str, object]) -> list[str]:
    return [str(item.get("name", "")) for item in schema.get("features", []) if isinstance(item, Mapping)]


def _load_json(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def _text_digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _matrix_digest(matrix: np.ndarray) -> str:
    arr = np.ascontiguousarray(np.asarray(matrix, dtype=np.float64))
    return hashlib.sha256(arr.tobytes()).hexdigest()


def _finite(matrix: np.ndarray) -> np.ndarray:
    return np.nan_to_num(np.asarray(matrix, dtype=np.float64), nan=0.0, posinf=0.0, neginf=0.0)


def _mechanism_sort_key(label: str) -> tuple[int, str]:
    text = str(label)
    if text.startswith("M") and text[1:].isdigit():
        return (int(text[1:]), text)
    return (10_000, text)
