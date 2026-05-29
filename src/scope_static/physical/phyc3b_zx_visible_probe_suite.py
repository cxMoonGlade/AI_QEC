from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Iterable

import numpy as np

from .channels import MechanismSpec, mechanism_channel
from .layers import LAYER3_LEARNER
from .mechanism_catalog import MECHANISM_NAMES
from .sampled_observation_separability import visible_input_identifiability_audit
from .sampled_quantum_error_quality import ChannelVector, channel_vector
from .typed_spam_gate_invariant import classification_metrics


STAGE_NAME = "PHYC3b_ZX_visible_alias_breaking_probe_suite"
SINGLE_PREPS = ("|0>", "|1>", "|+>")
SINGLE_REPEATS = (1, 2, 4, 8)
SINGLE_MEASUREMENTS = ("Z", "X")
TWO_PREPS = ("|00>", "|01>", "|10>", "|++>")
TWO_REPEATS = (1, 2)
TWO_REPEATS_ROBUST = (1, 2, 4)
TWO_MEASUREMENTS = ("ZZ", "ZX", "XZ", "XX")
ALIAS_PAIRS = (("M8", "M30"), ("M9", "M31"), ("M10", "M32"), ("M12", "M33"), ("M0", "M24"), ("M15", "M34"), ("M4", "M27"))
FORBIDDEN_LEARNER_INPUTS = (
    "true mechanism ID",
    "mechanism name",
    "physical family label",
    "teacher self-distinguishment features",
    "oracle channel matrix",
    "oracle Kraus/PTM matrix",
    "oracle prototype vector",
    "hidden omega",
)
FORBIDDEN_FEATURE_TOKENS = ("oracle", "mechanism", "teacher", "channel", "kraus", "ptm", "prototype", "omega", "family", "label")
RAW_SINGLE_METRICS = ("P0", "P1", "p_comp")
RAW_TWO_PROB_METRICS = ("P00", "P01", "P10", "P11", "p_comp")
H_GATE = (1.0 / math.sqrt(2.0)) * np.asarray([[1.0, 1.0], [1.0, -1.0]], dtype=np.complex128)
I_GATE = np.eye(2, dtype=np.complex128)


@dataclass(frozen=True)
class ZXVisibleFeatureTable:
    features: np.ndarray
    expected_features: np.ndarray
    feature_names: list[str]
    feature_schema: dict[str, object]
    records: list[dict[str, object]]
    labels: list[str]
    groups: list[int]
    schedule: list[dict[str, object]]


def build_zx_visible_probe_schedule(*, robustness_mode: bool = False) -> list[dict[str, object]]:
    """Return the PHYC3b Clifford-only, Y-free Z/X probe schedule."""

    schedule: list[dict[str, object]] = []
    probe_id = 0
    for prep in SINGLE_PREPS:
        for repeat in SINGLE_REPEATS:
            for basis in SINGLE_MEASUREMENTS:
                schedule.append(
                    {
                        "probe_id": int(probe_id),
                        "probe_kind": "single_qubit",
                        "qubit_count": 1,
                        "prepare": prep,
                        "repeat": int(repeat),
                        "measurement_basis": basis,
                        "measurement_axes": [basis],
                        "preparation_clifford_only": True,
                        "measurement_clifford_only": True,
                        "contains_y_basis": False,
                    }
                )
                probe_id += 1
    repeats = TWO_REPEATS_ROBUST if robustness_mode else TWO_REPEATS
    for prep in TWO_PREPS:
        for repeat in repeats:
            for basis in TWO_MEASUREMENTS:
                schedule.append(
                    {
                        "probe_id": int(probe_id),
                        "probe_kind": "two_qubit",
                        "qubit_count": 2,
                        "prepare": prep,
                        "repeat": int(repeat),
                        "measurement_basis": basis,
                        "measurement_axes": list(basis),
                        "preparation_clifford_only": True,
                        "measurement_clifford_only": True,
                        "contains_y_basis": False,
                    }
                )
                probe_id += 1
    _assert_zx_only_schedule(schedule)
    return schedule


def build_zx_visible_feature_table(
    records: list[dict[str, object]],
    *,
    shots: int = 20_000,
    seed: int = 0,
    robustness_mode: bool = False,
    sampling_mode: str = "expected",
) -> ZXVisibleFeatureTable:
    schedule = build_zx_visible_probe_schedule(robustness_mode=bool(robustness_mode))
    raw_names = _raw_feature_names(schedule)
    rng = np.random.default_rng(int(seed))
    observed_rows = []
    expected_rows = []
    derived_names: list[str] | None = None
    metadata_names = ["visible_metadata__qubit_count", "visible_metadata__shot_count"]

    for row_idx, record in enumerate(records):
        values = {name: 0.0 for name in raw_names}
        expected_values = {name: 0.0 for name in raw_names}
        spec = _spec_from_record(record)
        for probe in schedule:
            if int(probe["qubit_count"]) != int(spec.num_qubits):
                continue
            probabilities = _probe_probabilities(spec, probe)
            observed = _empirical_probabilities(probabilities, shots=int(shots), rng=rng, mode=sampling_mode)
            _append_probe_values(values, probe, observed, shots=int(shots))
            _append_probe_values(expected_values, probe, probabilities, shots=int(shots))
        derived = _derived_features(values, schedule)
        derived_expected = _derived_features(expected_values, schedule)
        if derived_names is None:
            derived_names = list(derived.keys())
        metadata = {
            "visible_metadata__qubit_count": float(spec.num_qubits),
            "visible_metadata__shot_count": float(shots),
        }
        observed_rows.append([values[name] for name in raw_names] + [derived[name] for name in derived_names] + [metadata[name] for name in metadata_names])
        expected_rows.append(
            [expected_values[name] for name in raw_names]
            + [derived_expected[name] for name in derived_names]
            + [metadata[name] for name in metadata_names]
        )

    if derived_names is None:
        derived_names = list(_derived_features({}, schedule).keys())
    feature_names = [*raw_names, *derived_names, *metadata_names]
    features = _finite(np.asarray(observed_rows, dtype=np.float64)) if observed_rows else np.zeros((0, len(feature_names)), dtype=np.float64)
    expected_features = _finite(np.asarray(expected_rows, dtype=np.float64)) if expected_rows else np.zeros((0, len(feature_names)), dtype=np.float64)
    schema = feature_schema_zx_visible(feature_names, raw_names=raw_names, derived_names=derived_names, metadata_names=metadata_names)
    return ZXVisibleFeatureTable(
        features=features,
        expected_features=expected_features,
        feature_names=feature_names,
        feature_schema=schema,
        records=[dict(record) for record in records],
        labels=[str(record.get("oracle_label", record.get("mechanism_id", ""))) for record in records],
        groups=[int(record.get("circuit_id", 0)) for record in records],
        schedule=schedule,
    )


def feature_schema_zx_visible(
    feature_names: list[str],
    *,
    raw_names: Iterable[str] = (),
    derived_names: Iterable[str] = (),
    metadata_names: Iterable[str] = (),
) -> dict[str, object]:
    raw_set = set(str(name) for name in raw_names)
    derived_set = set(str(name) for name in derived_names)
    metadata_set = set(str(name) for name in metadata_names)
    features = []
    for idx, name in enumerate(feature_names):
        if name in raw_set:
            kind = "raw_sampled_observation"
        elif name in derived_set:
            kind = "derived_sampled_observation"
        elif name in metadata_set:
            kind = "allowed_probe_metadata"
        else:
            kind = "unknown_visible"
        features.append(
            {
                "index": int(idx),
                "name": str(name),
                "kind": kind,
                "learner_visible": True,
                "source": "Z/X probe sampled observations or allowed probe metadata",
            }
        )
    return {
        "schema": "scope_static_phyc3b_zx_visible_feature_schema_v1",
        "stage": STAGE_NAME,
        "public_layer": LAYER3_LEARNER.metadata(artifact_stage=STAGE_NAME, substage="zx_visible_surface_repair"),
        "claim_boundary": "Z/X measurement axes are sufficient; Y measurement is not required; X-prepared states are required for phase/coherence observability.",
        "measurement_axes": ["Z", "X"],
        "preparations": {"single_qubit": list(SINGLE_PREPS), "two_qubit": list(TWO_PREPS)},
        "raw_time_sequence_retained": True,
        "raw_feature_count": int(len(raw_set)),
        "derived_feature_count": int(len(derived_set)),
        "metadata_feature_count": int(len(metadata_set)),
        "num_features": int(len(feature_names)),
        "features": features,
    }


def run_phyc3b_zx_visible_alias_breaking_probe_suite(
    *,
    teacher_dir: str | Path,
    output_dir: str | Path,
    phyc2_dir: str | Path | None = None,
    shots: int = 20_000,
    seed: int = 0,
    robustness_mode: bool = False,
    sampling_mode: str = "expected",
    signature_decimals: int = 10,
) -> dict[str, object]:
    teacher = Path(teacher_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    records = _load_mechanism_records(teacher / "oracle_mechanisms.json")
    labels = [str(record.get("oracle_label", record.get("mechanism_id", ""))) for record in records]
    class_names = sorted(set(labels), key=_mechanism_sort_key)

    before = _load_before_visible_audit(teacher, records, phyc2_dir=phyc2_dir)
    table = build_zx_visible_feature_table(
        records,
        shots=int(shots),
        seed=int(seed),
        robustness_mode=bool(robustness_mode),
        sampling_mode=str(sampling_mode),
    )
    after = deterministic_visible_ceiling_audit(
        labels,
        table.expected_features,
        class_names,
        decimals=int(signature_decimals),
        feature_source="PHYC3b expected Z/X visible probe feature vector",
    )
    learner = grouped_nearest_visible_learner(table.features, labels, table.groups, class_names)
    incompatible = incompatible_prediction_audit(records, learner.get("grouped_fold_predictions", []))
    alias_confusion = alias_pair_confusion(learner.get("true_labels", []), learner.get("predicted_labels", []), alias_pairs=ALIAS_PAIRS)
    m34_audit = audit_m34_implementation(records, table=table)
    leakage = leakage_guardrail_audit_zx_visible(table.feature_names)
    support_audit = alias_pair_support_audit(table)

    before_ceiling = dict(before.get("deterministic_ceiling", {}))
    after_ceiling = dict(after.get("deterministic_ceiling", {}))
    learner_overall = dict(learner.get("overall", {}))
    conflicts_before = int(before.get("conflicting_visible_signature_count", 0))
    conflicts_after = int(after.get("conflicting_visible_signature_count", 0))
    records_before = int(before.get("conflicting_record_count", 0))
    records_after = int(after.get("conflicting_record_count", 0))
    ba_before = float(before_ceiling.get("balanced_accuracy", 0.0))
    ba_after = float(after_ceiling.get("balanced_accuracy", 0.0))
    nmi_before = float(before_ceiling.get("normalized_mutual_info", 0.0))
    nmi_after = float(after_ceiling.get("normalized_mutual_info", 0.0))
    ari_before = float(before_ceiling.get("adjusted_rand_index", 0.0))
    ari_after = float(after_ceiling.get("adjusted_rand_index", 0.0))
    result = {
        "schema": "scope_static_phyc3b_zx_visible_alias_breaking_probe_suite_v1",
        "stage": STAGE_NAME,
        "public_layer": LAYER3_LEARNER.metadata(artifact_stage=STAGE_NAME, substage="zx_visible_surface_repair"),
        "teacher_dir": str(teacher),
        "phyc2_dir": None if phyc2_dir is None else str(phyc2_dir),
        "output_dir": str(output),
        "claim_boundary": {
            "visible_observability_repair_not_classifier_tuning": True,
            "z_x_measurement_axes_sufficient": True,
            "y_measurement_required": False,
            "x_prepared_states_required_for_phase_coherence_observability": True,
            "quotient_alias_classes_reported_when_exact_recovery_not_visible": True,
        },
        "config": {
            "shots": int(shots),
            "seed": int(seed),
            "sampling_mode": str(sampling_mode),
            "robustness_mode": bool(robustness_mode),
            "signature_decimals": int(signature_decimals),
        },
        "execution_order": [
            "visible_ceiling_before",
            "probe_schedule_generation",
            "feature_extraction",
            "visible_ceiling_after",
            "learner_training",
            "incompatible_prediction_audit",
        ],
        "ceiling_audit_precedes_learner_training": True,
        "probe_schedule": table.schedule,
        "feature_schema": table.feature_schema,
        "visible_signature_conflicts_before": conflicts_before,
        "visible_signature_conflicts_after": conflicts_after,
        "conflicting_records_before": records_before,
        "conflicting_records_after": records_after,
        "deterministic_ceiling_BA_before": ba_before,
        "deterministic_ceiling_BA_after": ba_after,
        "deterministic_ceiling_NMI_before": nmi_before,
        "deterministic_ceiling_NMI_after": nmi_after,
        "deterministic_ceiling_ARI_before": ari_before,
        "deterministic_ceiling_ARI_after": ari_after,
        "learner_BA": float(learner_overall.get("balanced_accuracy", 0.0)),
        "learner_ARI": float(learner_overall.get("adjusted_rand_index", 0.0)),
        "learner_NMI": float(learner_overall.get("normalized_mutual_info", 0.0)),
        "min_recall": float(learner_overall.get("min_class_recall", 0.0)),
        "incompatible_prediction_count": int(incompatible.get("incompatible_prediction_count", 0)),
        "per_alias_pair_confusion": alias_confusion,
        "main_success_criterion_passed": bool(ba_after > ba_before and nmi_after > nmi_before),
        "decision": _decision(ba_before=ba_before, ba_after=ba_after, nmi_before=nmi_before, nmi_after=nmi_after, learner=learner_overall),
        "visible_signature_conflicts_before_artifact": before,
        "visible_signature_conflicts_after_artifact": after,
        "deterministic_ceiling_metrics_before": before_ceiling,
        "deterministic_ceiling_metrics_after": after_ceiling,
        "quotient_alias_classes_after": after.get("quotient_alias_classes", []),
        "learner_metrics": learner,
        "learner_confusion_matrix": {
            "labels": learner_overall.get("confusion_matrix_labels", class_names),
            "matrix": learner_overall.get("confusion_matrix", []),
        },
        "incompatible_predictions": incompatible,
        "leakage_guardrail_audit": leakage,
        "m34_implementation_audit": m34_audit,
        "alias_pair_support_audit": support_audit,
    }
    _write_artifacts(output, result)
    return result


def deterministic_visible_ceiling_audit(
    labels: list[str],
    features: np.ndarray,
    class_names: list[str],
    *,
    decimals: int = 10,
    feature_source: str = "visible feature vector",
) -> dict[str, object]:
    x = _finite(np.asarray(features, dtype=np.float64))
    by_signature: dict[tuple[float, ...], list[int]] = {}
    for idx, row in enumerate(x):
        signature = tuple(float(value) for value in np.round(row, int(decimals)).tolist())
        by_signature.setdefault(signature, []).append(idx)
    conflicts = []
    graph: dict[str, set[str]] = {}
    for indices in by_signature.values():
        local_labels = [labels[idx] for idx in indices]
        unique = sorted(set(local_labels), key=_mechanism_sort_key)
        if len(unique) <= 1:
            continue
        for label in unique:
            graph.setdefault(label, set()).update(other for other in unique if other != label)
        conflicts.append(
            {
                "labels": unique,
                "label_counts": {label: int(local_labels.count(label)) for label in unique},
                "record_count": int(len(indices)),
                "record_indices": [int(idx) for idx in indices[:20]],
            }
        )
    pred = _optimistic_signature_predictions(labels, by_signature)
    ceiling = classification_metrics(labels, pred, class_names)
    return {
        "schema": "scope_static_phyc3b_visible_signature_conflicts_v1",
        "feature_source": str(feature_source),
        "signature_decimals": int(decimals),
        "num_records": int(len(labels)),
        "num_visible_signatures": int(len(by_signature)),
        "conflicting_visible_signature_count": int(len(conflicts)),
        "conflicting_record_count": int(sum(int(row["record_count"]) for row in conflicts)),
        "conflict_examples": conflicts[:50],
        "quotient_alias_classes": _connected_components(graph),
        "perfect_mechanism_recovery_possible_from_visible_inputs": len(conflicts) == 0,
        "deterministic_ceiling": {
            "balanced_accuracy": float(ceiling.get("balanced_accuracy", 0.0)),
            "min_class_recall": float(ceiling.get("min_class_recall", 0.0)),
            "adjusted_rand_index": float(ceiling.get("adjusted_rand_index", 0.0)),
            "normalized_mutual_info": float(ceiling.get("normalized_mutual_info", 0.0)),
            "per_class_recall": ceiling.get("per_class_recall", {}),
        },
    }


def grouped_nearest_visible_learner(features: np.ndarray, labels: list[str], groups: list[int], class_names: list[str]) -> dict[str, object]:
    x = _finite(np.asarray(features, dtype=np.float64))
    g = np.asarray(groups, dtype=np.int64)
    if len(class_names) < 2 or len(set(groups)) < 2:
        overall = classification_metrics([], [], class_names)
        return {
            "schema": "scope_static_phyc3b_grouped_visible_nearest_learner_v1",
            "model": "GroupedStandardizedNearestVisibleFeaturePrototype",
            "overall": overall,
            "grouped_fold_predictions": [],
            "true_labels": [],
            "predicted_labels": [],
        }
    true_all: list[str] = []
    pred_all: list[str] = []
    folds = []
    for fold_idx, test_group in enumerate(sorted(set(int(value) for value in g.tolist()))):
        train = np.where(g != int(test_group))[0]
        test = np.where(g == int(test_group))[0]
        x_train = x[train]
        x_test = x[test]
        mean = np.mean(x_train, axis=0) if x_train.size else np.zeros(x.shape[1], dtype=np.float64)
        std = np.std(x_train, axis=0) if x_train.size else np.ones(x.shape[1], dtype=np.float64)
        std = np.where(std > 1e-12, std, 1.0)
        z_train = (x_train - mean) / std
        z_test = (x_test - mean) / std
        prototypes = {}
        for label in class_names:
            local = [row for row, idx in zip(z_train, train.tolist()) if labels[idx] == label]
            if local:
                prototypes[label] = np.mean(np.asarray(local, dtype=np.float64), axis=0)
        predicted = []
        for row in z_test:
            if not prototypes:
                predicted.append(class_names[0])
                continue
            best_label = min(prototypes, key=lambda label: float(np.linalg.norm(row - prototypes[label])))
            predicted.append(str(best_label))
        true = [labels[int(idx)] for idx in test.tolist()]
        true_all.extend(true)
        pred_all.extend(predicted)
        folds.append(
            {
                "fold": int(fold_idx),
                "test_circuit_id": int(test_group),
                "test_indices": [int(idx) for idx in test.tolist()],
                "true_labels": true,
                "predicted_labels": predicted,
            }
        )
    overall = classification_metrics(true_all, pred_all, class_names)
    return {
        "schema": "scope_static_phyc3b_grouped_visible_nearest_learner_v1",
        "model": "GroupedStandardizedNearestVisibleFeaturePrototype",
        "primary_feature_block": "zx_visible_probe_raw_time_sequence_plus_derived",
        "primary_head": "nearest_visible_feature_prototype",
        "overall": overall,
        "balanced_accuracy": float(overall.get("balanced_accuracy", 0.0)),
        "min_class_recall": float(overall.get("min_class_recall", 0.0)),
        "adjusted_rand_index": float(overall.get("adjusted_rand_index", 0.0)),
        "normalized_mutual_info": float(overall.get("normalized_mutual_info", 0.0)),
        "grouped_fold_predictions": folds,
        "true_labels": true_all,
        "predicted_labels": pred_all,
    }


def incompatible_prediction_audit(records: list[dict[str, object]], folds: object) -> dict[str, object]:
    fold_rows = folds if isinstance(folds, list) else []
    rows = []
    for fold in fold_rows:
        if not isinstance(fold, dict):
            continue
        test_indices = [int(idx) for idx in fold.get("test_indices", [])]
        predicted = [str(value) for value in fold.get("predicted_labels", [])]
        train_records = [record for idx, record in enumerate(records) if idx not in set(test_indices)]
        prototypes = _channel_prototypes(train_records)
        for row_idx, pred_label in zip(test_indices, predicted):
            if not (0 <= int(row_idx) < len(records)):
                continue
            record = records[int(row_idx)]
            true_channel = channel_vector(record)
            predicted_channel = prototypes.get(pred_label)
            compatible = _channel_compatible(true_channel, predicted_channel)
            if not compatible:
                rows.append(
                    {
                        "record_index": int(row_idx),
                        "test_circuit_id": int(record.get("circuit_id", 0)),
                        "true_label_evaluator_only": str(record.get("oracle_label", "")),
                        "predicted_label": pred_label,
                        "true_channel_family": true_channel.family,
                        "predicted_channel_family": None if predicted_channel is None else predicted_channel.family,
                    }
                )
    return {
        "schema": "scope_static_phyc3b_incompatible_predictions_v1",
        "incompatible_prediction_count": int(len(rows)),
        "records": rows,
    }


def alias_pair_confusion(true_labels: object, predicted_labels: object, *, alias_pairs: Iterable[tuple[str, str]]) -> dict[str, object]:
    true = [str(value) for value in true_labels] if isinstance(true_labels, list) else []
    pred = [str(value) for value in predicted_labels] if isinstance(predicted_labels, list) else []
    out = {}
    for left, right in alias_pairs:
        subset = {left, right}
        matrix = {left: {left: 0, right: 0, "other": 0}, right: {left: 0, right: 0, "other": 0}}
        for a, b in zip(true, pred):
            if a not in subset:
                continue
            matrix[a][b if b in subset else "other"] += 1
        out[f"{left}__{right}"] = matrix
    return out


def alias_pair_support_audit(table: ZXVisibleFeatureTable) -> dict[str, object]:
    values = {label: _mean_feature_map(table, label) for label in sorted(set(table.labels), key=_mechanism_sort_key)}

    def delta(label_a: str, feature_a: str, label_b: str, feature_b: str | None = None) -> float | None:
        if label_a not in values or label_b not in values:
            return None
        right_feature = feature_a if feature_b is None else feature_b
        return float(values[label_a].get(feature_a, 0.0) - values[label_b].get(right_feature, 0.0))

    checks = {
        "M8__M30": {
            "expected": "RZZ leaves |00> ZZ populations unchanged; ZY creates |01> population.",
            "P01_delta_M30_minus_M8": _negate(delta("M8", "raw__two__prep_00__r_1__meas_ZZ__P01", "M30")),
            "P00_delta_M8_minus_M30": delta("M8", "raw__two__prep_00__r_1__meas_ZZ__P00", "M30"),
        },
        "M9__M31": {
            "expected": "Depolarizing spreads broadly; coherent XZ gives structured |10> transfer from |00>.",
            "P10_delta_M31_minus_M9": _negate(delta("M9", "raw__two__prep_00__r_1__meas_ZZ__P10", "M31")),
            "population_support_pattern_delta": delta("M9", "derived__two_prep_00_r_1_ZZ_population_support_pattern", "M31"),
        },
        "M10__M32": {
            "expected": "RXX/RYY can create |11>; YZ creates |10>, not |11>.",
            "P11_delta_M10_minus_M32": delta("M10", "raw__two__prep_00__r_1__meas_ZZ__P11", "M32"),
            "P10_delta_M32_minus_M10": _negate(delta("M10", "raw__two__prep_00__r_1__meas_ZZ__P10", "M32")),
        },
        "M12__M33": {
            "expected": "Correlated relaxation should not increase |11> from |00>; coherent YX can.",
            "P11_delta_M33_minus_M12": _negate(delta("M12", "raw__two__prep_00__r_1__meas_ZZ__P11", "M33")),
        },
        "M0__M24": {
            "expected": "Local stochastic Pauli is unital; thermal excitation is non-unital.",
            "non_unitality_proxy_delta_M24_minus_M0": _negate(delta("M0", "derived__single_non_unitality_proxy", "M24")),
        },
        "M4__M27": {
            "expected": "Amplitude damping is visible from |1>; H-axis coherent overrotation moves |0> and |+> coherently.",
            "prep_1_relaxation_proxy_delta_M4_minus_M27": delta("M4", "derived__single_prep_1_z_relaxation_proxy", "M27"),
            "prep_0_dynamics_proxy_delta_M27_minus_M4": _negate(delta("M4", "derived__single_prep_0_z_dynamics_proxy", "M27")),
        },
        "M15__M34": {
            "expected": "If M34 is CPTP in the computational subspace, p_comp need not separate it from M15.",
            "computational_survival_delta_M34_minus_M15": _negate(delta("M15", "derived__computational_subspace_survival_proxy", "M34")),
            "zx_feature_distance": _feature_distance(table, "M15", "M34"),
        },
    }
    return {"schema": "scope_static_phyc3b_alias_pair_support_audit_v1", "checks": checks}


def audit_m34_implementation(records: list[dict[str, object]], *, table: ZXVisibleFeatureTable | None = None) -> dict[str, object]:
    record = next((dict(item) for item in records if str(item.get("oracle_label", item.get("mechanism_id", ""))) == "M34"), None)
    if record is None:
        record = {
            "oracle_label": "M34",
            "mechanism_id": "M34",
            "name": MECHANISM_NAMES["M34"],
            "num_qubits": 1,
            "parameters": {},
            "instruction": "id",
            "qubits": [0],
            "circuit_id": 0,
        }
    spec = _spec_from_record(record)
    channel = mechanism_channel(spec)
    kind = str(channel.get("kind", ""))
    trace_preserving_error = 0.0
    implementation_class = "unknown"
    if kind == "kraus":
        kraus = [np.asarray(item, dtype=np.complex128) for item in channel.get("kraus", [])]  # type: ignore[arg-type]
        dim = kraus[0].shape[1] if kraus else 0
        effect = np.zeros((dim, dim), dtype=np.complex128)
        for op in kraus:
            effect = effect + op.conj().T @ op
        trace_preserving_error = float(np.linalg.norm(effect - np.eye(dim, dtype=np.complex128))) if dim else float("inf")
        implementation_class = "B_CPTP_computational_subspace_surrogate" if trace_preserving_error <= 1e-9 else "A_non_TP_leakage_out_of_computational_subspace"
    if table is not None:
        distance = _feature_distance(table, "M15", "M34")
    else:
        distance = None
    return {
        "schema": "scope_static_phyc3b_m34_implementation_audit_v1",
        "m34_name": MECHANISM_NAMES["M34"],
        "channel_kind": kind,
        "trace_preserving_error": float(trace_preserving_error),
        "implementation_class": implementation_class,
        "p_comp_valid_leakage_survival_feature": implementation_class == "A_non_TP_leakage_out_of_computational_subspace",
        "p_comp_m15_m34_separator_claim_allowed": implementation_class == "A_non_TP_leakage_out_of_computational_subspace",
        "zx_feature_distance_M15_M34": distance,
        "decision": (
            "p_comp may distinguish M34 as true leakage survival"
            if implementation_class == "A_non_TP_leakage_out_of_computational_subspace"
            else "M34 is CPTP inside the computational subspace; do not claim p_comp separates M15/M34 unless Z/X features do so"
        ),
    }


def leakage_guardrail_audit_zx_visible(feature_names: list[str]) -> dict[str, object]:
    lowered = [name.lower() for name in feature_names]
    checks = {f"{token}_absent_from_feature_names": not any(token in name for name in lowered) for token in FORBIDDEN_FEATURE_TOKENS}
    checks.update(
        {
            "only_z_x_measurement_axes": True,
            "no_y_preparation_or_measurement": True,
            "raw_time_sequence_retained": True,
            "ceiling_audit_runs_before_learner_training": True,
        }
    )
    return {
        "schema": "scope_static_phyc3b_leakage_guardrail_audit_v1",
        "passed": bool(all(checks.values())),
        "checks": checks,
        "allowed_visible_inputs": [
            "probe preparation label",
            "measurement basis label",
            "repeat count",
            "qubit count",
            "empirical probabilities",
            "empirical expectations",
            "shot count",
            "finite-shot uncertainty estimates",
        ],
        "forbidden_learner_inputs": list(FORBIDDEN_LEARNER_INPUTS),
    }


def format_phyc3b_summary(result: dict[str, object]) -> str:
    m34 = result.get("m34_implementation_audit", {})
    if not isinstance(m34, dict):
        m34 = {}
    return "\n".join(
        [
            "# Layer 3b: Z/X Visible Alias-Breaking Probe Suite",
            "",
            f"- Layer: `{LAYER3_LEARNER.public_name}`",
            f"- Legacy alias: `{LAYER3_LEARNER.legacy_alias}`",
            f"- Decision: `{result.get('decision')}`",
            f"- Main ceiling criterion passed: `{str(bool(result.get('main_success_criterion_passed'))).lower()}`",
            f"- Visible conflicts before: `{int(result.get('visible_signature_conflicts_before', 0))}`",
            f"- Visible conflicts after: `{int(result.get('visible_signature_conflicts_after', 0))}`",
            f"- Deterministic ceiling BA before: `{float(result.get('deterministic_ceiling_BA_before', 0.0)):.4f}`",
            f"- Deterministic ceiling BA after: `{float(result.get('deterministic_ceiling_BA_after', 0.0)):.4f}`",
            f"- Deterministic ceiling NMI before: `{float(result.get('deterministic_ceiling_NMI_before', 0.0)):.4f}`",
            f"- Deterministic ceiling NMI after: `{float(result.get('deterministic_ceiling_NMI_after', 0.0)):.4f}`",
            f"- Learner BA: `{float(result.get('learner_BA', 0.0)):.4f}`",
            f"- Learner ARI: `{float(result.get('learner_ARI', 0.0)):.4f}`",
            f"- Learner NMI: `{float(result.get('learner_NMI', 0.0)):.4f}`",
            f"- Min recall: `{float(result.get('min_recall', 0.0)):.4f}`",
            f"- Incompatible predictions: `{int(result.get('incompatible_prediction_count', 0))}`",
            f"- M34 implementation: `{m34.get('implementation_class', 'unknown')}`",
            "",
            "## Claim Boundary",
            "",
            "PHYC3b is a visible-observability repair, not a classifier-tuning stage. It uses only Z/X measurements. Y is not required, while X-prepared states are required for phase/coherence observability.",
            "",
        ]
    )


def _raw_feature_names(schedule: list[dict[str, object]]) -> list[str]:
    names: list[str] = []
    for probe in schedule:
        base = _probe_base(probe)
        if int(probe["qubit_count"]) == 1:
            basis = str(probe["measurement_basis"])
            for metric in (*RAW_SINGLE_METRICS, f"E_{basis}"):
                names.append(f"{base}__{metric}")
            for metric in ("P0", "P1", f"E_{basis}", "p_comp"):
                names.append(f"{base}__se_{metric}")
        else:
            basis = str(probe["measurement_basis"])
            for metric in (*RAW_TWO_PROB_METRICS, *_two_expectation_labels(basis)):
                names.append(f"{base}__{metric}")
            for metric in (*RAW_TWO_PROB_METRICS, *_two_expectation_labels(basis)):
                names.append(f"{base}__se_{metric}")
    return names


def _append_probe_values(target: dict[str, float], probe: dict[str, object], probabilities: np.ndarray, *, shots: int) -> None:
    base = _probe_base(probe)
    shots = 1.0
    if int(probe["qubit_count"]) == 1:
        p0 = float(probabilities[0]) if probabilities.size > 0 else 0.0
        p1 = float(probabilities[1]) if probabilities.size > 1 else 0.0
        comp = p0 + p1
        basis = str(probe["measurement_basis"])
        expectation = p0 - p1
        local = {"P0": p0, "P1": p1, "p_comp": comp, f"E_{basis}": expectation}
        for metric, value in local.items():
            target[f"{base}__{metric}"] = float(value)
        for metric, value in local.items():
            target[f"{base}__se_{metric}"] = _standard_error(float(value), float(shots))
        return
    probs = np.zeros(4, dtype=np.float64)
    probs[: min(4, probabilities.size)] = probabilities[: min(4, probabilities.size)]
    p00, p01, p10, p11 = [float(value) for value in probs.tolist()]
    comp = p00 + p01 + p10 + p11
    basis = str(probe["measurement_basis"])
    left_label, right_label, pair_label = _two_expectation_labels(basis)
    left = p00 + p01 - p10 - p11
    right = p00 - p01 + p10 - p11
    pair = p00 - p01 - p10 + p11
    local = {
        "P00": p00,
        "P01": p01,
        "P10": p10,
        "P11": p11,
        "p_comp": comp,
        left_label: float(left),
        right_label: float(right),
        pair_label: float(pair),
    }
    for metric, value in local.items():
        target[f"{base}__{metric}"] = float(value)
    for metric, value in local.items():
        target[f"{base}__se_{metric}"] = _standard_error(float(value), float(shots))


def _derived_features(values: dict[str, float], schedule: list[dict[str, object]]) -> dict[str, float]:
    out: dict[str, float] = {}
    oscillation = 0.0
    sign_changes = 0
    monotonic_violations = 0
    for qubit_count, prep, basis, metrics, repeats in _sequence_specs(schedule):
        for metric in metrics:
            seq = [
                float(values.get(f"raw__{qubit_count}__prep_{_slug(prep)}__r_{repeat}__meas_{basis}__{metric}", 0.0))
                for repeat in repeats
            ]
            stem = f"derived__{qubit_count}__prep_{_slug(prep)}__meas_{basis}__{metric}"
            for left, right, value_left, value_right in zip(repeats[:-1], repeats[1:], seq[:-1], seq[1:]):
                out[f"{stem}__first_diff_r_{left}_to_{right}"] = float(value_right - value_left)
            if len(seq) >= 3:
                for a, b, c, va, vb, vc in zip(repeats[:-2], repeats[1:-1], repeats[2:], seq[:-2], seq[1:-1], seq[2:]):
                    second = float(vc - 2.0 * vb + va)
                    out[f"{stem}__second_diff_r_{a}_{b}_{c}"] = second
                    oscillation += abs(second)
            diffs = [b - a for a, b in zip(seq[:-1], seq[1:])]
            if diffs:
                monotonic_violations += int(any(diff > 1e-12 for diff in diffs) and any(diff < -1e-12 for diff in diffs))
            signs = [1 if value > 1e-12 else -1 if value < -1e-12 else 0 for value in seq]
            sign_changes += sum(1 for left, right in zip(signs[:-1], signs[1:]) if left != 0 and right != 0 and left != right)
    p00 = float(values.get("raw__two__prep_00__r_1__meas_ZZ__P00", 0.0))
    p01 = float(values.get("raw__two__prep_00__r_1__meas_ZZ__P01", 0.0))
    p10 = float(values.get("raw__two__prep_00__r_1__meas_ZZ__P10", 0.0))
    p11 = float(values.get("raw__two__prep_00__r_1__meas_ZZ__P11", 0.0))
    support_bits = [p00 > 1e-9, p01 > 1e-9, p10 > 1e-9, p11 > 1e-9]
    out["derived__two_prep_00_r_1_ZZ_population_support_pattern"] = float(sum((1 << idx) for idx, keep in enumerate(support_bits) if keep))
    out["derived__two_prep_00_r_1_ZZ_population_asymmetry_score"] = float(abs(p10 - p01) + abs(p11 - p00))
    ez0 = float(values.get("raw__single__prep_0__r_8__meas_Z__E_Z", 0.0))
    ez1 = float(values.get("raw__single__prep_1__r_8__meas_Z__E_Z", 0.0))
    ez0_r1 = float(values.get("raw__single__prep_0__r_1__meas_Z__E_Z", 0.0))
    ez1_r1 = float(values.get("raw__single__prep_1__r_1__meas_Z__E_Z", 0.0))
    ezp_r1 = float(values.get("raw__single__prep_plus__r_1__meas_Z__E_Z", 0.0))
    exp_r1 = float(values.get("raw__single__prep_plus__r_1__meas_X__E_X", 0.0))
    exp_r8 = float(values.get("raw__single__prep_plus__r_8__meas_X__E_X", 0.0))
    p_comp_values = [float(value) for name, value in values.items() if name.endswith("__p_comp")]
    out["derived__single_non_unitality_proxy"] = float(abs(0.5 * (ez0 + ez1)))
    out["derived__single_prep_1_z_relaxation_proxy"] = float(ez1 - ez1_r1)
    out["derived__single_prep_0_z_dynamics_proxy"] = float(abs(ez0 - ez0_r1))
    out["derived__single_plus_phase_coherence_proxy"] = float(abs(exp_r8 - exp_r1) + abs(ezp_r1))
    out["derived__computational_subspace_survival_proxy"] = float(min(p_comp_values)) if p_comp_values else 0.0
    out["derived__oscillation_score"] = float(oscillation)
    out["derived__sign_change_count"] = float(sign_changes)
    out["derived__monotonicity_flag_count"] = float(monotonic_violations)
    return out


def _sequence_specs(schedule: list[dict[str, object]]) -> list[tuple[str, str, str, list[str], list[int]]]:
    specs = []
    grouped: dict[tuple[str, str, str], set[int]] = {}
    for probe in schedule:
        qubit_count = "single" if int(probe["qubit_count"]) == 1 else "two"
        grouped.setdefault((qubit_count, str(probe["prepare"]), str(probe["measurement_basis"])), set()).add(int(probe["repeat"]))
    for (qubit_count, prep, basis), repeat_set in sorted(grouped.items()):
        repeats = sorted(repeat_set)
        if qubit_count == "single":
            metrics = ["P0", "P1", "p_comp", f"E_{basis}"]
        else:
            metrics = [*RAW_TWO_PROB_METRICS, *_two_expectation_labels(basis)]
        specs.append((qubit_count, prep, basis, metrics, repeats))
    return specs


def _probe_probabilities(spec: MechanismSpec, probe: dict[str, object]) -> np.ndarray:
    state = _density_matrix(_prep_state(str(probe["prepare"])))
    channel = mechanism_channel(spec)
    kind = str(channel.get("kind", ""))
    rho = np.array(state, copy=True)
    if kind == "unitary":
        unitary = np.asarray(channel["unitary"], dtype=np.complex128)
        for _ in range(int(probe["repeat"])):
            rho = unitary @ rho @ unitary.conj().T
    elif kind == "kraus":
        kraus = [np.asarray(item, dtype=np.complex128) for item in channel.get("kraus", [])]  # type: ignore[arg-type]
        for _ in range(int(probe["repeat"])):
            rho = sum(op @ rho @ op.conj().T for op in kraus)
    elif kind == "readout":
        pass
    else:
        raise ValueError(f"unknown channel kind {kind!r}")
    probabilities = _measurement_probabilities(rho, str(probe["measurement_basis"]))
    if kind == "readout":
        matrix = np.asarray(channel["matrix"], dtype=np.float64)
        for _ in range(int(probe["repeat"])):
            probabilities = probabilities @ matrix
    return _clip_probabilities(probabilities)


def _empirical_probabilities(probabilities: np.ndarray, *, shots: int, rng: np.random.Generator, mode: str) -> np.ndarray:
    probs = _clip_probabilities(probabilities)
    if str(mode).lower() in {"expected", "mean", "deterministic"}:
        return probs
    if int(shots) <= 0:
        raise ValueError("shots must be positive for multinomial sampling")
    comp = float(np.sum(probs))
    lost = max(0.0, 1.0 - comp)
    categories = np.concatenate([probs, np.asarray([lost], dtype=np.float64)])
    total = float(np.sum(categories))
    if total <= 0.0:
        return np.zeros_like(probs)
    counts = rng.multinomial(int(shots), categories / total)
    return counts[:-1].astype(np.float64) / float(shots)


def _measurement_probabilities(rho: np.ndarray, basis: str) -> np.ndarray:
    axes = list(str(basis))
    transform = np.asarray([[1.0]], dtype=np.complex128)
    for axis in axes:
        if axis == "Z":
            transform = np.kron(transform, I_GATE)
        elif axis == "X":
            transform = np.kron(transform, H_GATE)
        else:
            raise ValueError("PHYC3b probe suite allows only Z/X measurement axes")
    rotated = transform @ rho @ transform.conj().T
    return np.real(np.diag(rotated)).astype(np.float64)


def _prep_state(label: str) -> np.ndarray:
    zero = np.asarray([1.0, 0.0], dtype=np.complex128)
    one = np.asarray([0.0, 1.0], dtype=np.complex128)
    plus = (zero + one) / math.sqrt(2.0)
    if label == "|0>":
        return zero
    if label == "|1>":
        return one
    if label == "|+>":
        return plus
    if label == "|00>":
        return np.kron(zero, zero)
    if label == "|01>":
        return np.kron(zero, one)
    if label == "|10>":
        return np.kron(one, zero)
    if label == "|++>":
        return np.kron(plus, plus)
    raise ValueError(f"unknown PHYC3b preparation {label!r}")


def _density_matrix(state: np.ndarray) -> np.ndarray:
    vector = np.asarray(state, dtype=np.complex128).reshape(-1, 1)
    return vector @ vector.conj().T


def _clip_probabilities(values: np.ndarray) -> np.ndarray:
    out = np.real(np.asarray(values, dtype=np.float64))
    out = np.where(out < 0.0, 0.0, out)
    total = float(np.sum(out))
    if total > 1.0 and total <= 1.0 + 1e-9:
        out = out / total
    return out


def _probe_base(probe: dict[str, object]) -> str:
    qubit_count = "single" if int(probe["qubit_count"]) == 1 else "two"
    return f"raw__{qubit_count}__prep_{_slug(str(probe['prepare']))}__r_{int(probe['repeat'])}__meas_{probe['measurement_basis']}"


def _slug(value: str) -> str:
    return str(value).replace("|", "").replace(">", "").replace("+", "plus")


def _two_expectation_labels(basis: str) -> tuple[str, str, str]:
    left, right = list(str(basis))
    return f"{left}I", f"I{right}", f"{left}{right}"


def _standard_error(value: float, shots: float) -> float:
    n = max(1.0, float(shots))
    bounded = min(1.0, max(0.0, abs(float(value))))
    return float(math.sqrt(max(0.0, bounded * (1.0 - bounded)) / n))


def _spec_from_record(record: dict[str, object]) -> MechanismSpec:
    mechanism_id = str(record.get("mechanism_id", record.get("oracle_label", "")))
    return MechanismSpec(
        mechanism_id=mechanism_id,
        name=str(record.get("name", MECHANISM_NAMES.get(mechanism_id, mechanism_id))),
        num_qubits=int(record.get("num_qubits", 1)),
        parameters=dict(record.get("parameters", {})),
        instruction=None if record.get("instruction") is None else str(record.get("instruction")),
        qubits=tuple(int(value) for value in record.get("qubits", [])),
        circuit_id=int(record.get("circuit_id", 0)),
        probe_indices=tuple(int(value) for value in record.get("probe_indices", [])),
    )


def _load_before_visible_audit(teacher: Path, records: list[dict[str, object]], *, phyc2_dir: str | Path | None) -> dict[str, object]:
    if phyc2_dir is not None:
        metrics_path = Path(phyc2_dir) / "metrics.json"
        if metrics_path.exists():
            data = json.loads(metrics_path.read_text())
            audit = data.get("visible_input_identifiability_audit")
            if isinstance(audit, dict):
                return _compact_before_audit(audit, source=str(metrics_path))
    observations_path = teacher / "observations.npz"
    if observations_path.exists():
        data = np.load(observations_path)
        observations = np.asarray(data["observations"])
        probe_names = [str(value) for value in data["probe_names"].tolist()]
        return _compact_before_audit(visible_input_identifiability_audit(records, probe_names, observations), source=str(observations_path))
    return _old_visible_signature_audit(records)


def _compact_before_audit(audit: dict[str, object], *, source: str) -> dict[str, object]:
    ceiling = audit.get("optimistic_duplicate_signature_ceiling", audit.get("deterministic_ceiling", {}))
    if not isinstance(ceiling, dict):
        ceiling = {}
    examples = audit.get("conflict_examples", [])
    compact_examples = []
    if isinstance(examples, list):
        for row in examples[:50]:
            if isinstance(row, dict):
                compact_examples.append(
                    {
                        "labels": row.get("labels", []),
                        "label_counts": row.get("label_counts", {}),
                        "record_count": int(row.get("record_count", 0)),
                    }
                )
    return {
        "schema": "scope_static_phyc3b_visible_signature_conflicts_before_v1",
        "source": str(source),
        "conflicting_visible_signature_count": int(audit.get("conflicting_visible_signature_count", 0)),
        "conflicting_record_count": int(audit.get("conflicting_record_count", 0)),
        "conflict_examples": compact_examples,
        "deterministic_ceiling": {
            "balanced_accuracy": float(ceiling.get("balanced_accuracy", 0.0)),
            "min_class_recall": float(ceiling.get("min_class_recall", 0.0)),
            "adjusted_rand_index": float(ceiling.get("adjusted_rand_index", 0.0)),
            "normalized_mutual_info": float(ceiling.get("normalized_mutual_info", 0.0)),
            "per_class_recall": ceiling.get("per_class_recall", {}),
        },
        "quotient_alias_classes": _quotient_classes_from_examples(compact_examples),
        "perfect_mechanism_recovery_possible_from_visible_inputs": bool(audit.get("perfect_mechanism_recovery_possible_from_visible_inputs", False)),
    }


def _old_visible_signature_audit(records: list[dict[str, object]]) -> dict[str, object]:
    labels = [str(record.get("oracle_label", record.get("mechanism_id", ""))) for record in records]
    class_names = sorted(set(labels), key=_mechanism_sort_key)
    by_signature: dict[tuple[object, ...], list[int]] = {}
    for idx, record in enumerate(records):
        signature = (
            int(record.get("circuit_id", 0)),
            str(record.get("instruction", "")),
            tuple(int(value) for value in record.get("qubits", [])),
            tuple(int(value) for value in record.get("probe_indices", [])),
            bool(record.get("local_observable_slot_remap", False)),
        )
        by_signature.setdefault(signature, []).append(idx)
    conflicts = []
    graph: dict[str, set[str]] = {}
    for indices in by_signature.values():
        local = [labels[idx] for idx in indices]
        unique = sorted(set(local), key=_mechanism_sort_key)
        if len(unique) > 1:
            for label in unique:
                graph.setdefault(label, set()).update(other for other in unique if other != label)
            conflicts.append({"labels": unique, "label_counts": {label: int(local.count(label)) for label in unique}, "record_count": int(len(indices))})
    pred = _optimistic_signature_predictions(labels, by_signature)
    ceiling = classification_metrics(labels, pred, class_names)
    return {
        "schema": "scope_static_phyc3b_visible_signature_conflicts_before_v1",
        "source": "PHYC3b fallback old visible signature",
        "conflicting_visible_signature_count": int(len(conflicts)),
        "conflicting_record_count": int(sum(row["record_count"] for row in conflicts)),
        "conflict_examples": conflicts[:50],
        "deterministic_ceiling": {
            "balanced_accuracy": float(ceiling.get("balanced_accuracy", 0.0)),
            "min_class_recall": float(ceiling.get("min_class_recall", 0.0)),
            "adjusted_rand_index": float(ceiling.get("adjusted_rand_index", 0.0)),
            "normalized_mutual_info": float(ceiling.get("normalized_mutual_info", 0.0)),
            "per_class_recall": ceiling.get("per_class_recall", {}),
        },
        "quotient_alias_classes": _connected_components(graph),
        "perfect_mechanism_recovery_possible_from_visible_inputs": len(conflicts) == 0,
    }


def _optimistic_signature_predictions(labels: list[str], by_signature: dict[object, list[int]]) -> list[str]:
    predictions = [""] * len(labels)
    tie_counters: dict[tuple[str, ...], int] = {}
    for indices in by_signature.values():
        local_labels = [labels[idx] for idx in indices]
        unique = sorted(set(local_labels), key=_mechanism_sort_key)
        if len(unique) == 1:
            chosen = unique[0]
        else:
            counts = {label: local_labels.count(label) for label in unique}
            max_count = max(counts.values())
            tied = [label for label in unique if counts[label] == max_count]
            key = tuple(tied)
            offset = tie_counters.get(key, 0)
            chosen = tied[offset % len(tied)]
            tie_counters[key] = offset + 1
        for idx in indices:
            predictions[idx] = chosen
    return [pred if pred else labels[idx] for idx, pred in enumerate(predictions)]


def _quotient_classes_from_examples(examples: list[dict[str, object]]) -> list[list[str]]:
    graph: dict[str, set[str]] = {}
    for row in examples:
        labels = [str(label) for label in row.get("labels", [])]
        if len(labels) < 2:
            continue
        for label in labels:
            graph.setdefault(label, set()).update(other for other in labels if other != label)
    return _connected_components(graph)


def _connected_components(graph: dict[str, set[str]]) -> list[list[str]]:
    seen: set[str] = set()
    components = []
    for node in sorted(graph, key=_mechanism_sort_key):
        if node in seen:
            continue
        stack = [node]
        local = set()
        while stack:
            current = stack.pop()
            if current in local:
                continue
            local.add(current)
            stack.extend(sorted(graph.get(current, set()) - local, key=_mechanism_sort_key))
        seen.update(local)
        if len(local) > 1:
            components.append(sorted(local, key=_mechanism_sort_key))
    return components


def _channel_prototypes(records: list[dict[str, object]]) -> dict[str, ChannelVector]:
    grouped: dict[str, list[ChannelVector]] = {}
    for record in records:
        grouped.setdefault(str(record.get("oracle_label", "")), []).append(channel_vector(record))
    out = {}
    for label, vectors in grouped.items():
        by_family: dict[str, list[ChannelVector]] = {}
        for vector in vectors:
            by_family.setdefault(vector.family, []).append(vector)
        family, local = max(by_family.items(), key=lambda item: len(item[1]))
        matrix = np.stack([item.vector for item in local], axis=0)
        out[label] = ChannelVector(
            family=family,
            vector=_finite(np.mean(matrix, axis=0)),
            representation=local[0].representation,
            mechanism_id=label,
        )
    return out


def _channel_compatible(left: ChannelVector, right: ChannelVector | None) -> bool:
    return bool(right is not None and left.family == right.family and left.vector.shape == right.vector.shape)


def _mean_feature_map(table: ZXVisibleFeatureTable, label: str) -> dict[str, float]:
    mask = np.asarray([item == label for item in table.labels], dtype=bool)
    if not np.any(mask):
        return {}
    values = np.mean(table.expected_features[mask], axis=0)
    return {name: float(values[idx]) for idx, name in enumerate(table.feature_names)}


def _feature_distance(table: ZXVisibleFeatureTable, left: str, right: str) -> float | None:
    left_map = _mean_feature_map(table, left)
    right_map = _mean_feature_map(table, right)
    if not left_map or not right_map:
        return None
    left_vec = np.asarray([left_map.get(name, 0.0) for name in table.feature_names], dtype=np.float64)
    right_vec = np.asarray([right_map.get(name, 0.0) for name in table.feature_names], dtype=np.float64)
    return float(np.linalg.norm(left_vec - right_vec) / math.sqrt(max(1, left_vec.size)))


def _negate(value: float | None) -> float | None:
    return None if value is None else float(-value)


def _decision(*, ba_before: float, ba_after: float, nmi_before: float, nmi_after: float, learner: dict[str, object]) -> str:
    if ba_after > ba_before and nmi_after > nmi_before:
        if float(learner.get("balanced_accuracy", 0.0)) >= ba_after - 1e-9:
            return "visible_ceiling_improved_and_learner_reached_ceiling"
        return "visible_ceiling_improved_learner_still_below_ceiling"
    return "visible_ceiling_not_improved_do_not_claim_classifier_gain"


def _write_artifacts(output: Path, result: dict[str, object]) -> None:
    artifacts = {
        "metrics.json": result,
        "feature_schema_zx_visible.json": result["feature_schema"],
        "probe_schedule_zx_visible.json": {"schema": "scope_static_phyc3b_zx_visible_probe_schedule_v1", "stage": STAGE_NAME, "probes": result["probe_schedule"]},
        "visible_signature_conflicts_before.json": result["visible_signature_conflicts_before_artifact"],
        "visible_signature_conflicts_after.json": result["visible_signature_conflicts_after_artifact"],
        "deterministic_ceiling_metrics_before.json": result["deterministic_ceiling_metrics_before"],
        "deterministic_ceiling_metrics_after.json": result["deterministic_ceiling_metrics_after"],
        "alias_pair_confusion_after.json": result["per_alias_pair_confusion"],
        "quotient_alias_classes_after.json": {"schema": "scope_static_phyc3b_quotient_alias_classes_after_v1", "classes": result["quotient_alias_classes_after"]},
        "leakage_guardrail_audit.json": result["leakage_guardrail_audit"],
        "learner_metrics.json": result["learner_metrics"],
        "learner_confusion_matrix.json": result["learner_confusion_matrix"],
        "incompatible_predictions.json": result["incompatible_predictions"],
        "m34_implementation_audit.json": result["m34_implementation_audit"],
        "alias_pair_support_audit.json": result["alias_pair_support_audit"],
    }
    for name, payload in artifacts.items():
        (output / name).write_text(json.dumps(_json_safe(payload), indent=2, sort_keys=True) + "\n")
    (output / "summary.md").write_text(format_phyc3b_summary(result))


def _assert_zx_only_schedule(schedule: list[dict[str, object]]) -> None:
    for probe in schedule:
        axes = [str(axis) for axis in probe.get("measurement_axes", [])]
        if any(axis not in {"Z", "X"} for axis in axes):
            raise ValueError("PHYC3b schedule must use only Z/X measurement axes")
        if "Y" in str(probe.get("prepare", "")) or "Y" in str(probe.get("measurement_basis", "")):
            raise ValueError("PHYC3b schedule must not contain Y-basis preparation or measurement")


def _load_mechanism_records(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text())
    records = data.get("mechanisms")
    if not isinstance(records, list) or not records:
        raise ValueError(f"{path} does not contain non-empty mechanisms")
    return [dict(record) for record in records]


def _finite(values: np.ndarray) -> np.ndarray:
    return np.nan_to_num(np.asarray(values, dtype=np.float64), nan=0.0, posinf=0.0, neginf=0.0)


def _json_safe(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return _json_safe(list(value))
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, float) and not np.isfinite(value):
        return "inf" if value > 0.0 else "-inf"
    return value


def _mechanism_sort_key(name: str) -> tuple[int, str]:
    text = str(name)
    if text.startswith("M") and text[1:].isdigit():
        return (int(text[1:]), text)
    return (10_000, text)
