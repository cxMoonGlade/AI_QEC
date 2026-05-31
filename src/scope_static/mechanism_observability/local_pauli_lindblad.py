from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from scope_static.numerics import NUMERICAL_ZERO, positive_floor, probability_floor

from scope_static.backend.channels import correlated_relaxation_kraus, pauli_stochastic_kraus, rxx_unitary, ryy_unitary, rzz_unitary
from scope_static.backend.ptm import pauli_basis, ptm_from_kraus, ptm_from_unitary
from scope_static.backend.probe_catalog import (
    EDGE_ORIENTATION_RULE,
    RZZ_LOCAL_TOMOGRAPHY_PROBES,
    RZZ_TOMO_EDGE_PARITIES,
    RZZ_TOMO_MEAS_AXES,
    RZZ_TOMO_PREP_STATES,
    build_probe_basis_manifest,
)


PAULI_LABELS = tuple(label for label, _matrix in pauli_basis(2))
GENERATOR_COORDINATES = (
    "h_XX",
    "h_YY",
    "h_ZZ",
    "gamma_XX",
    "gamma_YY",
    "gamma_ZZ",
    "relaxation_pair",
    "affine_ZI",
    "affine_IZ",
    "affine_ZZ",
)
FORBIDDEN_FEATURE_TOKENS = ("oracle_label", "mechanism_id", "exact_ptm", "teacher_channel", "oracle_fingerprint")


@dataclass(frozen=True)
class LocalPauliLindbladBundle:
    generator_dictionary: dict[str, object]
    probe_observable_schema: dict[str, object]
    ptm_convention_audit: dict[str, object]
    response_jacobian: np.ndarray
    response_jacobian_json: dict[str, object]
    observability_rank_metrics: dict[str, object]
    ptm_block_reconstruction: dict[str, object]
    generator_coordinate_estimates: dict[str, object]
    generator_recovery_metrics: dict[str, object]
    feature_matrix: np.ndarray
    scrambled_feature_matrix: np.ndarray
    feature_names: list[str]
    scrambled_feature_names: list[str]
    leakage_guardrail_audit: dict[str, object]


def build_local_pauli_lindblad_observability(
    records: list[dict[str, object]],
    observations: np.ndarray,
    probe_names: Iterable[str],
    *,
    theta: float,
    ridge: float = 1e-8,
) -> LocalPauliLindbladBundle:
    obs = _validate_observations(observations)
    names = [str(name) for name in probe_names]
    num_qubits = int(obs.shape[2])
    probe_manifest = build_probe_basis_manifest(names, num_qubits=num_qubits)
    scrambled_manifest = _scrambled_tomography_manifest(probe_manifest)
    dictionary = generator_dictionary()
    jacobian = np.asarray(dictionary["jacobian"], dtype=np.float64)
    ideal_ptm = ptm_from_unitary(rzz_unitary(float(theta)))

    recon_records = []
    coord_rows = []
    scrambled_coord_rows = []
    for idx, record in enumerate(records):
        recon = reconstruct_record_local_ptm(record, obs, names, probe_manifest, theta=float(theta), ridge=float(ridge))
        scrambled = reconstruct_record_local_ptm(record, obs, names, scrambled_manifest, theta=float(theta), ridge=float(ridge))
        coords = fit_generator_coordinates(recon["R_error"], jacobian=jacobian, ridge=float(ridge))
        scrambled_coords = fit_generator_coordinates(scrambled["R_error"], jacobian=jacobian, ridge=float(ridge))
        coord_rows.append(_coordinate_feature_row(coords))
        scrambled_coord_rows.append(_coordinate_feature_row(scrambled_coords))
        recon_records.append(
            {
                "location_id": int(record.get("location_id", idx)),
                "oracle_label_evaluator_only": str(record.get("oracle_label", "")),
                "instruction": str(record.get("instruction", "")),
                "qubits": [int(value) for value in record.get("qubits", [])],
                "circuit_id": int(record.get("circuit_id", 0)),
                "local_edge_parity": recon["edge_parity"],
                "available": bool(recon["available"]),
                "num_probe_settings_used": int(recon["num_probe_settings_used"]),
                "R_est": _round_matrix(recon["R_est"]),
                "R_ideal": _round_matrix(ideal_ptm),
                "R_error": _round_matrix(recon["R_error"]),
                "Delta": _round_matrix(recon["Delta"]),
                "generator_coordinates": coords,
                "scrambled_generator_coordinates": scrambled_coords,
            }
        )

    feature_names = [*GENERATOR_COORDINATES, "nonunital_norm_proxy", "delta_norm", "logm_delta_norm"]
    scrambled_feature_names = [f"scrambled_{name}" for name in feature_names]
    features = _finite(np.asarray(coord_rows, dtype=np.float64))
    scrambled_features = _finite(np.asarray(scrambled_coord_rows, dtype=np.float64))
    rank_metrics = observability_rank_metrics(jacobian)
    leakage = leakage_guardrail_audit(feature_names, scrambled_feature_names)
    return LocalPauliLindbladBundle(
        generator_dictionary={key: value for key, value in dictionary.items() if key != "jacobian"},
        probe_observable_schema=probe_observable_schema(probe_manifest),
        ptm_convention_audit=ptm_convention_audit(),
        response_jacobian=jacobian,
        response_jacobian_json=response_jacobian_json(jacobian),
        observability_rank_metrics=rank_metrics,
        ptm_block_reconstruction={
            "schema": "scope_static_s2d9_ptm_block_reconstruction_v1",
            "pauli_labels": list(PAULI_LABELS),
            "records": recon_records,
        },
        generator_coordinate_estimates={
            "schema": "scope_static_s2d9_generator_coordinate_estimates_v1",
            "coordinate_names": feature_names,
            "records": [
                {
                    "location_id": int(record.get("location_id", idx)),
                    "oracle_label_evaluator_only": str(record.get("oracle_label", "")),
                    "circuit_id": int(record.get("circuit_id", 0)),
                    "features": {name: float(features[idx, col]) for col, name in enumerate(feature_names)},
                    "scrambled_features": {name: float(scrambled_features[idx, col]) for col, name in enumerate(feature_names)},
                }
                for idx, record in enumerate(records)
            ],
        },
        generator_recovery_metrics=generator_recovery_metrics(records, features, scrambled_features, feature_names),
        feature_matrix=features,
        scrambled_feature_matrix=scrambled_features,
        feature_names=feature_names,
        scrambled_feature_names=scrambled_feature_names,
        leakage_guardrail_audit=leakage,
    )


def reconstruct_record_local_ptm(
    record: dict[str, object],
    observations: np.ndarray,
    probe_names: list[str],
    probe_manifest: dict[str, object],
    *,
    theta: float,
    ridge: float = 1e-8,
) -> dict[str, object]:
    obs = _validate_observations(observations)
    qubits = _record_qubits(record)
    ideal = ptm_from_unitary(rzz_unitary(float(theta)))
    if len(qubits) < 2:
        return _empty_reconstruction(ideal)
    left, right = min(qubits), max(qubits)
    parity = "even" if left % 2 == 0 else "odd"
    prep_vectors = []
    output_vectors = []
    used = 0
    allowed = set(_record_probe_indices(record, len(probe_names)))
    by_setting = _tomography_probe_index(probe_manifest)
    for prep_left in RZZ_TOMO_PREP_STATES:
        for prep_right in RZZ_TOMO_PREP_STATES:
            prep_vectors.append(_prep_vector(prep_left, prep_right))
            estimates: dict[str, list[float]] = {label: [] for label in PAULI_LABELS}
            estimates["II"].append(1.0)
            for meas_left in RZZ_TOMO_MEAS_AXES:
                for meas_right in RZZ_TOMO_MEAS_AXES:
                    probe_indices = by_setting.get((prep_left, prep_right, meas_left, meas_right, parity), [])
                    for probe_idx in probe_indices:
                        if int(probe_idx) not in allowed:
                            continue
                        left_samples = _pm_one(obs[int(probe_idx), :, left])
                        right_samples = _pm_one(obs[int(probe_idx), :, right])
                        estimates[f"{meas_left}I"].append(float(np.mean(left_samples)))
                        estimates[f"I{meas_right}"].append(float(np.mean(right_samples)))
                        estimates[f"{meas_left}{meas_right}"].append(float(np.mean(left_samples * right_samples)))
                        used += 1
            output_vectors.append(np.asarray([float(np.mean(estimates[label])) if estimates[label] else 0.0 for label in PAULI_LABELS], dtype=np.float64))
    vin = np.stack(prep_vectors, axis=1)
    vout = np.stack(output_vectors, axis=1)
    if used == 0:
        return _empty_reconstruction(ideal)
    r_est = _finite(vout @ np.linalg.pinv(vin, rcond=max(NUMERICAL_ZERO, float(ridge))))
    r_error = local_error_ptm_from_observed(r_est, ideal, error_order="post_ideal")
    delta = _finite(r_error - np.eye(len(PAULI_LABELS), dtype=np.float64))
    return {
        "available": True,
        "edge_parity": parity,
        "num_probe_settings_used": int(used),
        "R_est": r_est,
        "R_ideal": ideal,
        "R_error": r_error,
        "Delta": delta,
    }


def local_error_ptm_from_observed(r_est: np.ndarray, r_ideal: np.ndarray, *, error_order: str = "post_ideal") -> np.ndarray:
    if error_order != "post_ideal":
        raise ValueError("S2D.9 v1 supports post_ideal error extraction only")
    return _finite(np.asarray(r_est, dtype=np.float64) @ np.linalg.pinv(np.asarray(r_ideal, dtype=np.float64)))


def fit_generator_coordinates(r_error: np.ndarray, *, jacobian: np.ndarray | None = None, ridge: float = 1e-8) -> dict[str, object]:
    j = generator_jacobian() if jacobian is None else np.asarray(jacobian, dtype=np.float64)
    delta = _finite(np.asarray(r_error, dtype=np.float64) - np.eye(len(PAULI_LABELS), dtype=np.float64))
    y = delta.reshape(-1)
    lhs = j.T @ j + float(ridge) * np.eye(j.shape[1], dtype=np.float64)
    rhs = j.T @ y
    coeff = _finite(np.linalg.solve(lhs, rhs))
    residual = y - j @ coeff
    log_info = _logm_safe(np.asarray(r_error, dtype=np.float64))
    coord = {name: float(coeff[idx]) for idx, name in enumerate(GENERATOR_COORDINATES)}
    diag_cov = np.diag(np.linalg.pinv(lhs))
    stderr = {name: float(np.sqrt(positive_floor(diag_cov[idx]))) for idx, name in enumerate(GENERATOR_COORDINATES)}
    return {
        "schema": "scope_static_s2d9_generator_coordinates_v1",
        "official_target": "R_error_minus_I",
        "coordinate_names": list(GENERATOR_COORDINATES),
        "coordinates": coord,
        "coordinate_stderr_proxy": stderr,
        "nonunital_norm_proxy": float(np.linalg.norm(np.asarray(r_error, dtype=np.float64)[1:, 0])),
        "delta_norm": float(np.linalg.norm(delta)),
        "residual_norm": float(np.linalg.norm(residual)),
        "logm_stable": bool(log_info["stable"]),
        "logm_delta_norm": log_info["log_delta_norm"],
    }


def generator_dictionary() -> dict[str, object]:
    jac = generator_jacobian()
    return {
        "schema": "scope_static_s2d9_generator_dictionary_v1",
        "pauli_labels": list(PAULI_LABELS),
        "coordinate_names": list(GENERATOR_COORDINATES),
        "coordinate_roles": {
            "h_XX": "Hamiltonian coherent XX generator",
            "h_YY": "Hamiltonian coherent YY generator",
            "h_ZZ": "Hamiltonian coherent ZZ generator",
            "gamma_XX": "stochastic Pauli-like XX generator",
            "gamma_YY": "stochastic Pauli-like YY generator",
            "gamma_ZZ": "stochastic Pauli-like ZZ generator",
            "relaxation_pair": "correlated two-qubit relaxation surrogate generator",
            "affine_ZI": "direct affine/non-unital ZI coordinate",
            "affine_IZ": "direct affine/non-unital IZ coordinate",
            "affine_ZZ": "direct affine/non-unital ZZ coordinate",
        },
        "official_generator_target": "R_error_minus_I",
        "jacobian": jac,
    }


def generator_jacobian(*, epsilon: float = 1e-6) -> np.ndarray:
    identity = np.eye(len(PAULI_LABELS), dtype=np.float64)
    columns = [
        ((ptm_from_unitary(rxx_unitary(float(epsilon))) - identity) / float(epsilon)).reshape(-1),
        ((ptm_from_unitary(ryy_unitary(float(epsilon))) - identity) / float(epsilon)).reshape(-1),
        ((ptm_from_unitary(rzz_unitary(float(epsilon))) - identity) / float(epsilon)).reshape(-1),
        ((ptm_from_kraus(_two_qubit_pauli_kraus("XX", float(epsilon))) - identity) / float(epsilon)).reshape(-1),
        ((ptm_from_kraus(_two_qubit_pauli_kraus("YY", float(epsilon))) - identity) / float(epsilon)).reshape(-1),
        ((ptm_from_kraus(_two_qubit_pauli_kraus("ZZ", float(epsilon))) - identity) / float(epsilon)).reshape(-1),
        ((ptm_from_kraus(correlated_relaxation_kraus(float(epsilon))) - identity) / float(epsilon)).reshape(-1),
        _affine_column("ZI").reshape(-1),
        _affine_column("IZ").reshape(-1),
        _affine_column("ZZ").reshape(-1),
    ]
    return _finite(np.stack(columns, axis=1))


def observability_rank_metrics(jacobian: np.ndarray) -> dict[str, object]:
    j = np.asarray(jacobian, dtype=np.float64)
    singular = np.linalg.svd(j, compute_uv=False)
    rank = int(np.linalg.matrix_rank(j, tol=1e-9))
    gram = j.T @ j
    angles = {}
    weakest = {"pair": None, "angle_degrees": None, "cosine_abs": None}
    for i, left in enumerate(GENERATOR_COORDINATES):
        for k, right in enumerate(GENERATOR_COORDINATES):
            if k <= i:
                continue
            a, b = j[:, i], j[:, k]
            denom = float(np.linalg.norm(a) * np.linalg.norm(b))
            cosine = NUMERICAL_ZERO if denom <= NUMERICAL_ZERO else float(np.dot(a, b) / denom)
            angle = float(np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0))))
            key = f"{left}/{right}"
            angles[key] = {"cosine": cosine, "abs_cosine": abs(cosine), "angle_degrees": angle}
            if weakest["cosine_abs"] is None or abs(cosine) > float(weakest["cosine_abs"]):
                weakest = {"pair": key, "angle_degrees": angle, "cosine_abs": abs(cosine)}
    return {
        "schema": "scope_static_s2d9_observability_rank_metrics_v1",
        "primary_object": "local_response_jacobian_generator_coordinate_identifiability",
        "rank": rank,
        "num_coordinates": int(j.shape[1]),
        "full_column_rank": bool(rank == int(j.shape[1])),
        "singular_values": [float(value) for value in singular.tolist()],
        "condition_number": float(singular[0] / singular[-1]) if singular.size and singular[-1] > NUMERICAL_ZERO else float("inf"),
        "pairwise_column_angles": angles,
        "weakest_pairwise_margin": weakest,
        "shot_weighted_gram_proxy": _round_matrix(gram),
    }


def generator_recovery_metrics(
    records: list[dict[str, object]],
    features: np.ndarray,
    scrambled_features: np.ndarray,
    feature_names: list[str],
) -> dict[str, object]:
    label_index = {name: idx for idx, name in enumerate(feature_names)}
    rows = []
    by_label: dict[str, list[int]] = {}
    for idx, record in enumerate(records):
        label = str(record.get("oracle_label", ""))
        by_label.setdefault(label, []).append(idx)
        row = features[idx]
        dominant = _dominant_coordinate(row, feature_names)
        rows.append(
            {
                "location_id": int(record.get("location_id", idx)),
                "oracle_label_evaluator_only": label,
                "circuit_id": int(record.get("circuit_id", 0)),
                "dominant_coordinate": dominant,
                "h_XX": float(row[label_index["h_XX"]]),
                "h_YY": float(row[label_index["h_YY"]]),
                "h_ZZ": float(row[label_index["h_ZZ"]]),
                "stochastic_norm": float(np.linalg.norm([row[label_index["gamma_XX"]], row[label_index["gamma_YY"]], row[label_index["gamma_ZZ"]]])),
                "nonunital_norm_proxy": float(row[label_index["nonunital_norm_proxy"]]),
            }
        )
    summary = {}
    for label, indices in sorted(by_label.items()):
        local = features[indices]
        scrambled = scrambled_features[indices]
        summary[label] = {
            "num_rows": int(len(indices)),
            "mean_coordinates": {name: float(np.mean(local[:, col])) for col, name in enumerate(feature_names)},
            "mean_abs_coordinates": {name: float(np.mean(np.abs(local[:, col]))) for col, name in enumerate(feature_names)},
            "real_minus_scrambled_norm": float(np.linalg.norm(np.mean(local, axis=0) - np.mean(scrambled, axis=0))),
        }
    return {
        "schema": "scope_static_s2d9_generator_recovery_metrics_v1",
        "role": "secondary_diagnostic_not_primary_verdict",
        "coordinate_names": list(feature_names),
        "records": rows,
        "by_oracle_label_audit_only": summary,
    }


def ptm_convention_audit() -> dict[str, object]:
    return {
        "schema": "scope_static_s2d9_ptm_convention_audit_v1",
        "ptm_definition": "R[row_out, col_in] = Tr(P_out E(P_in)) / d",
        "vector_convention": "column_vector",
        "evolution_rule": "v_out = R v_in",
        "error_order_assumption": "post_ideal",
        "post_ideal_extraction": "R_error = R_est @ pinv(R_ideal)",
        "phys3_uses_exact_teacher_ptm": False,
    }


def probe_observable_schema(probe_manifest: dict[str, object]) -> dict[str, object]:
    records = [
        record
        for record in probe_manifest.get("probe_records", [])
        if isinstance(record, dict) and str(record.get("base_probe_name", "")) in set(RZZ_LOCAL_TOMOGRAPHY_PROBES)
    ]
    return {
        "schema": "scope_static_s2d9_probe_observable_schema_v1",
        "probe_set": "rzz_local_tomography",
        "prep_states": list(RZZ_TOMO_PREP_STATES),
        "measurement_axes": list(RZZ_TOMO_MEAS_AXES),
        "edge_parities": list(RZZ_TOMO_EDGE_PARITIES),
        "pauli_observables": list(PAULI_LABELS),
        "edge_orientation_rule": EDGE_ORIENTATION_RULE,
        "learner_visible_inputs": ["shot_bits", "prep_metadata", "measurement_metadata", "edge_index", "visible_ideal_schedule"],
        "probe_records": records,
    }


def response_jacobian_json(jacobian: np.ndarray) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d9_response_jacobian_v1",
        "primary_object": "local_response_jacobian_generator_coordinate_identifiability",
        "row_order": [f"{row}_{col}" for row in PAULI_LABELS for col in PAULI_LABELS],
        "column_order": list(GENERATOR_COORDINATES),
        "matrix": _round_matrix(np.asarray(jacobian, dtype=np.float64)),
    }


def leakage_guardrail_audit(feature_names: list[str], scrambled_feature_names: list[str]) -> dict[str, object]:
    lower = [name.lower() for name in [*feature_names, *scrambled_feature_names]]
    checks = {
        "oracle_label_not_in_feature_columns": not any("oracle_label" in name for name in lower),
        "mechanism_id_not_in_feature_columns": not any("mechanism_id" in name for name in lower),
        "ptm_columns_absent": not any("exact_ptm" in name for name in lower),
        "teacher_channel_columns_absent": not any("teacher_channel" in name for name in lower),
        "oracle_fingerprint_columns_absent": not any("oracle_fingerprint" in name for name in lower),
        "phys3_features_learner_visible": True,
    }
    return {
        "schema": "scope_static_s2d9_leakage_guardrail_audit_v1",
        "passed": all(bool(value) for value in checks.values()),
        "checks": checks,
        "forbidden_feature_tokens": list(FORBIDDEN_FEATURE_TOKENS),
    }


def _tomography_probe_index(probe_manifest: dict[str, object]) -> dict[tuple[str, str, str, str, str], list[int]]:
    out: dict[tuple[str, str, str, str, str], list[int]] = {}
    for record in probe_manifest.get("probe_records", []):
        if not isinstance(record, dict):
            continue
        prep = record.get("rzz_tomography_prep", {})
        meas = record.get("rzz_tomography_measurement", {})
        if not isinstance(prep, dict) or not isinstance(meas, dict):
            continue
        key = (
            str(prep.get("left")),
            str(prep.get("right")),
            str(meas.get("left")),
            str(meas.get("right")),
            str(record.get("rzz_tomography_edge_parity")),
        )
        if "none" in key:
            continue
        out.setdefault(key, []).append(int(record["probe_index"]))
    return out


def _prep_vector(prep_left: str, prep_right: str) -> np.ndarray:
    left = _prep_bloch(prep_left)
    right = _prep_bloch(prep_right)
    values = []
    for label in PAULI_LABELS:
        values.append(_axis_value(label[0], left) * _axis_value(label[1], right))
    return np.asarray(values, dtype=np.float64)


def _prep_bloch(prep: str) -> dict[str, float]:
    if prep == "Zp":
        return {"X": 0.0, "Y": 0.0, "Z": 1.0}
    if prep == "Zm":
        return {"X": 0.0, "Y": 0.0, "Z": -1.0}
    if prep == "Xp":
        return {"X": 1.0, "Y": 0.0, "Z": 0.0}
    if prep == "Yp":
        return {"X": 0.0, "Y": 1.0, "Z": 0.0}
    raise ValueError(f"unknown tomography prep state {prep!r}")


def _axis_value(axis: str, bloch: dict[str, float]) -> float:
    return 1.0 if axis == "I" else float(bloch.get(axis, 0.0))


def _scrambled_tomography_manifest(probe_manifest: dict[str, object]) -> dict[str, object]:
    prep_mapping = {"Zp": "Xp", "Xp": "Yp", "Yp": "Zm", "Zm": "Zp"}
    meas_mapping = {"X": "Y", "Y": "Z", "Z": "X"}
    records = [dict(record) for record in probe_manifest.get("probe_records", [])]
    for record in records:
        prep = record.get("rzz_tomography_prep", {})
        meas = record.get("rzz_tomography_measurement", {})
        if isinstance(prep, dict) and prep.get("left") != "none":
            record["rzz_tomography_prep"] = {
                "left": prep_mapping.get(str(prep.get("left")), str(prep.get("left"))),
                "right": prep_mapping.get(str(prep.get("right")), str(prep.get("right"))),
            }
        if isinstance(meas, dict) and meas.get("left") != "none":
            record["rzz_tomography_measurement"] = {
                "left": meas_mapping.get(str(meas.get("left")), str(meas.get("left"))),
                "right": meas_mapping.get(str(meas.get("right")), str(meas.get("right"))),
            }
        if str(record.get("rzz_tomography_edge_parity")) == "even":
            record["rzz_tomography_edge_parity"] = "odd"
        elif str(record.get("rzz_tomography_edge_parity")) == "odd":
            record["rzz_tomography_edge_parity"] = "even"
    return {**probe_manifest, "schema": "scope_static_s2d9_scrambled_tomography_manifest_v1", "probe_records": records}


def _coordinate_feature_row(coords: dict[str, object]) -> list[float]:
    values = dict(coords.get("coordinates", {}))
    return [
        *[float(values.get(name, 0.0)) for name in GENERATOR_COORDINATES],
        float(coords.get("nonunital_norm_proxy", 0.0)),
        float(coords.get("delta_norm", 0.0)),
        float(coords.get("logm_delta_norm", 0.0) or 0.0),
    ]


def _dominant_coordinate(row: np.ndarray, feature_names: list[str]) -> str:
    candidate_indices = [idx for idx, name in enumerate(feature_names) if name in set(GENERATOR_COORDINATES)]
    if not candidate_indices:
        return "none"
    idx = max(candidate_indices, key=lambda item: abs(float(row[item])))
    return str(feature_names[idx])


def _two_qubit_pauli_kraus(label: str, probability: float) -> list[np.ndarray]:
    pauli = _two_qubit_pauli_matrix(label)
    p = probability_floor(float(probability))
    return [np.sqrt(positive_floor(1.0 - p)) * np.eye(4, dtype=np.complex128), np.sqrt(p) * pauli]


def _two_qubit_pauli_matrix(label: str) -> np.ndarray:
    one = {
        "I": np.eye(2, dtype=np.complex128),
        "X": np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128),
        "Y": np.array([[0.0, -1j], [1j, 0.0]], dtype=np.complex128),
        "Z": np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128),
    }
    return np.kron(one[label[0]], one[label[1]])


def _affine_column(label: str) -> np.ndarray:
    out = np.zeros((len(PAULI_LABELS), len(PAULI_LABELS)), dtype=np.float64)
    out[PAULI_LABELS.index(label), PAULI_LABELS.index("II")] = 1.0
    return out


def _logm_safe(matrix: np.ndarray) -> dict[str, object]:
    try:
        values, vectors = np.linalg.eig(np.asarray(matrix, dtype=np.float64))
        if np.any(np.abs(values) < NUMERICAL_ZERO):
            return {"stable": False, "log_delta_norm": None}
        log_diag = np.diag(np.log(values.astype(np.complex128)))
        logm = vectors @ log_diag @ np.linalg.inv(vectors)
        if np.max(np.abs(np.imag(logm))) > 1e-6:
            return {"stable": False, "log_delta_norm": None}
        return {"stable": True, "log_delta_norm": float(np.linalg.norm(np.real(logm)))}
    except Exception:
        return {"stable": False, "log_delta_norm": None}


def _record_qubits(record: dict[str, object]) -> list[int]:
    raw = record.get("qubits", [])
    return [int(value) for value in raw] if isinstance(raw, list) and raw else [0]


def _record_probe_indices(record: dict[str, object], num_probes: int) -> list[int]:
    raw = record.get("probe_indices", [])
    if isinstance(raw, list) and raw:
        return [int(value) for value in raw]
    return list(range(int(num_probes)))


def _empty_reconstruction(ideal: np.ndarray) -> dict[str, object]:
    identity = np.eye(len(PAULI_LABELS), dtype=np.float64)
    return {
        "available": False,
        "edge_parity": "none",
        "num_probe_settings_used": 0,
        "R_est": identity,
        "R_ideal": ideal,
        "R_error": identity,
        "Delta": np.zeros_like(identity),
    }


def _pm_one(bits: np.ndarray) -> np.ndarray:
    return 1.0 - 2.0 * np.asarray(bits, dtype=np.float64)


def _round_matrix(matrix: np.ndarray, *, decimals: int = 8) -> list[list[float]]:
    return np.round(_finite(np.asarray(matrix, dtype=np.float64)), decimals=int(decimals)).tolist()


def _validate_observations(observations: np.ndarray) -> np.ndarray:
    obs = np.asarray(observations)
    if obs.ndim != 3:
        raise ValueError("observations must have shape [num_probes, shots, num_qubits]")
    return obs


def _finite(values: np.ndarray) -> np.ndarray:
    return np.nan_to_num(np.asarray(values, dtype=np.float64), nan=NUMERICAL_ZERO, posinf=NUMERICAL_ZERO, neginf=-NUMERICAL_ZERO)
