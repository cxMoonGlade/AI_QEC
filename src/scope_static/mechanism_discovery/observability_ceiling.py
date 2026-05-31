from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import numpy as np
import yaml

from scope_static.protocols import LEARNER_VALIDATION_STAGE
from scope_static.learner import deterministic_visible_ceiling_audit
from .artifacts import load_json_object
from .artifacts import load_mechanism_records
from .artifacts import load_stage3_evaluator_labels
from .artifacts import load_stage3a_frozen_visible_features
from .artifacts import mechanism_sort_key
from .artifacts import resolve_teacher_dir
from .protocol_freeze import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A_DIR


STAGE_NAME = "Stage3A5_observability_alias_ceiling"
DEFAULT_OUTPUT_DIR = "outputs/scope_static/PHYC_STAGE3_discovery/S3A5_observability_alias_ceiling"
DEFAULT_DISTANCE_THRESHOLD = 1.0e-9
DEFAULT_SIGNATURE_DECIMALS = 10


def run_stage3a5_observability_alias_ceiling(
    *,
    stage3a_dir: str | Path = DEFAULT_STAGE3A_DIR,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    teacher_dir: str | Path | None = None,
    distance_threshold: float = DEFAULT_DISTANCE_THRESHOLD,
    signature_decimals: int = DEFAULT_SIGNATURE_DECIMALS,
) -> dict[str, object]:
    """Compute the Stage 3A.5 visible observability ceiling.

    This is an evaluator-only audit. It may inspect mechanism labels to define
    the maximum recoverable quotient, but it does not produce learner inputs and
    it does not train a discovery model.
    """

    s3a = Path(stage3a_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    s3a_metrics = load_json_object(s3a / "metrics.json")
    teacher = resolve_teacher_dir(s3a_metrics, teacher_dir)

    expected, feature_names, feature_matrix = load_stage3a_frozen_visible_features(s3a)
    evaluator = load_stage3_evaluator_labels(s3a, teacher)
    labels = evaluator.exact_labels
    if len(labels) != int(expected.shape[0]):
        raise ValueError(f"Stage 3A frozen feature row count {expected.shape[0]} does not match evaluator label count {len(labels)}")
    class_names = evaluator.exact_class_names
    feature_match = _feature_schema_matches_s3a(s3a, feature_names)

    pairwise = pairwise_visible_distance_matrix(labels, expected, threshold=float(distance_threshold))
    exact_ceiling = deterministic_visible_ceiling_audit(
        labels,
        expected,
        class_names,
        decimals=int(signature_decimals),
        feature_source="Stage 3A approved expected Z/X visible feature vector",
    )
    alias_artifact = oracle_alias_classes_from_ceiling(
        labels,
        exact_ceiling,
        pairwise,
        distance_threshold=float(distance_threshold),
    )
    quotient_labels = [str(alias_artifact["label_to_quotient"][label]) for label in labels]
    quotient_class_names = sorted(set(quotient_labels))
    quotient_ceiling = deterministic_visible_ceiling_audit(
        quotient_labels,
        expected,
        quotient_class_names,
        decimals=int(signature_decimals),
        feature_source="Stage 3A approved expected Z/X visible feature vector projected to quotient labels",
    )
    evaluator_metrics = evaluator_only_label_metrics(exact_ceiling, quotient_ceiling)
    acceptance = stage3a5_acceptance_audit(
        s3a_metrics=s3a_metrics,
        feature_match=feature_match,
        feature_matrix=feature_matrix,
        exact_ceiling=exact_ceiling,
        quotient_ceiling=quotient_ceiling,
        alias_artifact=alias_artifact,
    )
    exact_allowed = bool(exact_ceiling.get("perfect_mechanism_recovery_possible_from_visible_inputs", False))
    result = {
        "schema": "scope_static_stage3a5_observability_alias_ceiling_v1",
        "stage": STAGE_NAME,
        "public_layer": LEARNER_VALIDATION_STAGE.metadata(artifact_stage=STAGE_NAME, substage="observability_alias_ceiling"),
        "stage3a_dir": str(s3a),
        "teacher_dir": str(teacher),
        "output_dir": str(output),
        "claim_boundary": {
            "stage3a5_trains_model": False,
            "evaluator_only_labels_used_for_ceiling": True,
            "uses_stage3a_frozen_visible_features": True,
            "learner_inputs_written": False,
            "exact_label_recovery_claim_allowed": exact_allowed,
            "target_if_exact_not_visible": "quotient_recovery",
        },
        "config": {
            "stage3a_dir": str(s3a),
            "teacher_dir": str(teacher),
            "output_dir": str(output),
            "distance_threshold": float(distance_threshold),
            "signature_decimals": int(signature_decimals),
        },
        "visible_feature_matrix": feature_matrix,
        "feature_schema_match_audit": feature_match,
        "pairwise_visible_distance_matrix": pairwise,
        "observability_ceiling": exact_ceiling,
        "oracle_alias_classes": alias_artifact,
        "evaluator_only_label_metrics": evaluator_metrics,
        "quotient_metrics": {
            "schema": "scope_static_stage3a5_quotient_metrics_v1",
            "quotient_class_count": int(len(quotient_class_names)),
            "quotient_class_names": quotient_class_names,
            "quotient_ceiling": quotient_ceiling,
        },
        "acceptance_audit": acceptance,
        "decision": "stage3a5_observability_ceiling_passed" if acceptance["passed"] else "stage3a5_observability_ceiling_failed",
    }
    _write_outputs(output, result)
    return result


def pairwise_visible_distance_matrix(labels: list[str], features: np.ndarray, *, threshold: float) -> dict[str, object]:
    x = np.asarray(features, dtype=np.float64)
    class_names = sorted(set(labels), key=_mechanism_sort_key)
    means = {}
    for label in class_names:
        indices = [idx for idx, current in enumerate(labels) if current == label]
        means[label] = np.mean(x[np.asarray(indices, dtype=np.int64)], axis=0) if indices else np.zeros(x.shape[1], dtype=np.float64)
    stacked = np.vstack([means[label] for label in class_names]) if class_names else np.zeros((0, x.shape[1]), dtype=np.float64)
    scale = np.std(x, axis=0) if x.size else np.ones(x.shape[1], dtype=np.float64)
    scale = np.where(scale > 1.0e-12, scale, 1.0)
    raw_matrix = np.zeros((len(class_names), len(class_names)), dtype=np.float64)
    standardized_matrix = np.zeros_like(raw_matrix)
    pairs = []
    for i, left in enumerate(class_names):
        for j, right in enumerate(class_names):
            diff = stacked[i] - stacked[j]
            raw = float(np.linalg.norm(diff))
            standardized = float(np.linalg.norm(diff / scale))
            raw_matrix[i, j] = raw
            standardized_matrix[i, j] = standardized
            if i < j:
                pairs.append(
                    {
                        "left": left,
                        "right": right,
                        "raw_l2": raw,
                        "standardized_l2": standardized,
                        "below_threshold": bool(standardized <= float(threshold)),
                    }
                )
    return {
        "schema": "scope_static_stage3a5_pairwise_visible_distance_matrix_v1",
        "distance": "L2 between per-label mean expected visible feature vectors",
        "standardization": "feature-wise standard deviation over Stage 3A visible instances; zero scales set to 1",
        "distance_threshold": float(threshold),
        "labels": class_names,
        "raw_l2_matrix": raw_matrix.tolist(),
        "standardized_l2_matrix": standardized_matrix.tolist(),
        "pairs": pairs,
    }


def oracle_alias_classes_from_ceiling(
    labels: list[str],
    exact_ceiling: dict[str, object],
    pairwise: dict[str, object],
    *,
    distance_threshold: float,
) -> dict[str, object]:
    graph: dict[str, set[str]] = {label: set() for label in sorted(set(labels), key=_mechanism_sort_key)}
    for row in exact_ceiling.get("quotient_alias_classes", []):
        if not isinstance(row, list):
            continue
        local = [str(label) for label in row]
        for left in local:
            graph.setdefault(left, set()).update(right for right in local if right != left)
    for row in pairwise.get("pairs", []):
        if not isinstance(row, dict) or not bool(row.get("below_threshold", False)):
            continue
        left = str(row.get("left", ""))
        right = str(row.get("right", ""))
        if left and right:
            graph.setdefault(left, set()).add(right)
            graph.setdefault(right, set()).add(left)
    components = _connected_components(graph)
    label_to_quotient = {}
    classes = []
    for idx, component in enumerate(components):
        quotient_id = f"Q{idx:03d}"
        alias = len(component) > 1
        for label in component:
            label_to_quotient[label] = quotient_id
        classes.append(
            {
                "quotient_id": quotient_id,
                "mechanisms": component,
                "is_alias_class": bool(alias),
                "exact_hidden_label_recovery_required": not alias,
            }
        )
    alias_classes = [row for row in classes if bool(row["is_alias_class"])]
    return {
        "schema": "scope_static_stage3a5_oracle_alias_classes_v1",
        "definition": "m_a ~_obs m_b iff approved visible feature signatures/distances are indistinguishable under the declared threshold",
        "distance_threshold": float(distance_threshold),
        "alias_class_count": int(len(alias_classes)),
        "quotient_class_count": int(len(classes)),
        "classes": classes,
        "alias_classes": alias_classes,
        "label_to_quotient": label_to_quotient,
        "exact_label_recovery_claim_allowed": int(len(alias_classes)) == 0,
    }


def evaluator_only_label_metrics(exact_ceiling: dict[str, object], quotient_ceiling: dict[str, object]) -> dict[str, object]:
    exact = dict(exact_ceiling.get("deterministic_ceiling", {}))
    quotient = dict(quotient_ceiling.get("deterministic_ceiling", {}))
    return {
        "schema": "scope_static_stage3a5_evaluator_only_label_metrics_v1",
        "exact_label_ceiling": {
            "balanced_accuracy": float(exact.get("balanced_accuracy", 0.0)),
            "min_class_recall": float(exact.get("min_class_recall", 0.0)),
            "adjusted_rand_index": float(exact.get("adjusted_rand_index", 0.0)),
            "normalized_mutual_info": float(exact.get("normalized_mutual_info", 0.0)),
        },
        "quotient_label_ceiling": {
            "balanced_accuracy": float(quotient.get("balanced_accuracy", 0.0)),
            "min_class_recall": float(quotient.get("min_class_recall", 0.0)),
            "adjusted_rand_index": float(quotient.get("adjusted_rand_index", 0.0)),
            "normalized_mutual_info": float(quotient.get("normalized_mutual_info", 0.0)),
        },
    }


def stage3a5_acceptance_audit(
    *,
    s3a_metrics: dict[str, object],
    feature_match: dict[str, object],
    feature_matrix: dict[str, object],
    exact_ceiling: dict[str, object],
    quotient_ceiling: dict[str, object],
    alias_artifact: dict[str, object],
) -> dict[str, object]:
    exact_metrics = dict(exact_ceiling.get("deterministic_ceiling", {}))
    quotient_metrics = dict(quotient_ceiling.get("deterministic_ceiling", {}))
    exact_allowed = bool(alias_artifact.get("exact_label_recovery_claim_allowed", False))
    checks = {
        "stage3a_acceptance_passed": bool(dict(s3a_metrics.get("acceptance_audit", {})).get("passed", False)),
        "approved_feature_schema_matches_stage3a": bool(feature_match.get("passed", False)),
        "uses_stage3a_frozen_visible_features": bool(feature_matrix.get("loaded_from_stage3a_artifact", False)),
        "pairwise_distance_matrix_written": True,
        "oracle_alias_classes_written": True,
        "exact_label_claim_allowed_only_when_no_alias_classes": exact_allowed == (int(alias_artifact.get("alias_class_count", 0)) == 0),
        "quotient_ceiling_reported": bool(quotient_ceiling.get("deterministic_ceiling")),
        "quotient_ceiling_is_perfect": _is_one(quotient_metrics.get("balanced_accuracy")) and _is_one(quotient_metrics.get("normalized_mutual_info")),
        "evaluator_only_labels_not_learner_inputs": True,
        "learner_training_not_run_in_stage3a5": True,
    }
    checks["exact_ceiling_separates_mechanisms_if_claim_allowed"] = (not exact_allowed) or (
        _is_one(exact_metrics.get("balanced_accuracy"))
        and _is_one(exact_metrics.get("normalized_mutual_info"))
        and _is_one(exact_metrics.get("adjusted_rand_index"))
    )
    return {
        "schema": "scope_static_stage3a5_acceptance_audit_v1",
        "passed": bool(all(checks.values())),
        "checks": checks,
    }


def format_stage3a5_summary(result: dict[str, object]) -> str:
    acceptance = dict(result.get("acceptance_audit", {}))
    alias = dict(result.get("oracle_alias_classes", {}))
    metrics = dict(result.get("evaluator_only_label_metrics", {}))
    exact = dict(metrics.get("exact_label_ceiling", {}))
    quotient = dict(metrics.get("quotient_label_ceiling", {}))
    return "\n".join(
        [
            "# Stage 3A.5: Observability And Alias Ceiling",
            "",
            f"- Decision: `{result.get('decision')}`",
            f"- Acceptance passed: `{str(bool(acceptance.get('passed', False))).lower()}`",
            f"- Alias classes: `{int(alias.get('alias_class_count', 0))}`",
            f"- Exact-label claim allowed: `{str(bool(alias.get('exact_label_recovery_claim_allowed', False))).lower()}`",
            f"- Exact-label ceiling NMI: `{float(exact.get('normalized_mutual_info', 0.0)):.4f}`",
            f"- Quotient-label ceiling NMI: `{float(quotient.get('normalized_mutual_info', 0.0)):.4f}`",
            "",
            "## Claim Boundary",
            "",
            "Stage 3A.5 is an evaluator-only observability audit. It fixes the maximum recoverable quotient before discovery-model training. If exact labels are not visible, Stage 3B targets quotient recovery rather than forced exact mechanism recovery.",
            "",
        ]
    )


def _feature_schema_matches_s3a(stage3a_dir: Path, feature_names: list[str]) -> dict[str, object]:
    schema_path = stage3a_dir / "visible_feature_schema.json"
    if not schema_path.exists():
        return {
            "schema": "scope_static_stage3a5_feature_schema_match_audit_v1",
            "passed": False,
            "reason": f"missing {schema_path}",
        }
    schema = _load_json(schema_path)
    frozen_names = [str(item.get("name", "")) for item in schema.get("features", []) if isinstance(item, dict)]
    missing = [name for name in frozen_names if name not in set(feature_names)]
    extra = [name for name in feature_names if name not in set(frozen_names)]
    return {
        "schema": "scope_static_stage3a5_feature_schema_match_audit_v1",
        "passed": not missing and not extra and len(frozen_names) == len(feature_names),
        "frozen_feature_count": int(len(frozen_names)),
        "recomputed_feature_count": int(len(feature_names)),
        "missing_from_recomputed": missing[:50],
        "extra_in_recomputed": extra[:50],
    }


def _write_outputs(output: Path, result: dict[str, object]) -> None:
    artifacts = {
        "metrics.json": result,
        "observability_ceiling.json": result["observability_ceiling"],
        "oracle_alias_classes.json": result["oracle_alias_classes"],
        "pairwise_visible_distance_matrix.json": result["pairwise_visible_distance_matrix"],
        "evaluator_only_label_metrics.json": result["evaluator_only_label_metrics"],
        "quotient_metrics.json": result["quotient_metrics"],
        "acceptance_audit.json": result["acceptance_audit"],
        "feature_schema_match_audit.json": result["feature_schema_match_audit"],
        "visible_feature_matrix.json": result["visible_feature_matrix"],
    }
    for name, payload in artifacts.items():
        (output / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    (output / "config.yaml").write_text(yaml.safe_dump({"stage3a5_observability_alias_ceiling": result["config"]}, sort_keys=False))
    (output / "summary.md").write_text(format_stage3a5_summary(result))


def _load_json(path: Path) -> dict[str, object]:
    return load_json_object(path)


def _load_mechanism_records(path: Path) -> list[dict[str, object]]:
    return load_mechanism_records(path)


def _connected_components(graph: dict[str, set[str]]) -> list[list[str]]:
    seen: set[str] = set()
    components: list[list[str]] = []
    for label in sorted(graph, key=_mechanism_sort_key):
        if label in seen:
            continue
        stack = [label]
        component = []
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            component.append(current)
            stack.extend(sorted(graph.get(current, set()) - seen, key=_mechanism_sort_key, reverse=True))
        components.append(sorted(component, key=_mechanism_sort_key))
    return components


def _is_one(value: object, *, atol: float = 1.0e-12) -> bool:
    try:
        return abs(float(value) - 1.0) <= float(atol)
    except (TypeError, ValueError):
        return False


def _mechanism_sort_key(label: str) -> tuple[int, str]:
    return mechanism_sort_key(label)
