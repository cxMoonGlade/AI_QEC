from __future__ import annotations

import numpy as np

from qec_twin.forward.channels import (
    M13_DEFAULT_DRIFT_VISIBILITY_SCALE,
    MechanismSpec,
    amplitude_damping_kraus,
    mechanism_channel,
    pauli_stochastic_kraus,
    readout_bias_matrix,
    rx_unitary,
    rz_unitary,
    rzz_unitary,
)
from qec_twin.forward.cptp_guardrail import audit_mechanism_physicality, build_cptp_guardrail_audit
from qec_twin.forward.exact.density_sim import apply_kraus, measurement_probabilities_z
from qec_twin.mechanisms.catalog import IMPLEMENTED_MECHANISM_IDS, MECHANISM_NAMES, READOUT_MECHANISM_IDS, RZZ_FAMILY_IDS
from qec_twin.mechanisms.catalog import CURRENT_VISIBLE_SURFACE_FLAT_EXACT_CLAIM_TARGET_IDS
from qec_twin.mechanisms.catalog import MECHANISM_LEAF_EXACT_IDS, NON_FLAT_PRIMARY_TARGET_IDS, PRIMARY_FLAT_CLUSTER_TARGET_IDS
from qec_twin.mechanisms.catalog import NON_FLAT_PUBLIC_LABELS, PRIMARY_FLAT_PUBLIC_LABELS
from qec_twin.mechanisms.catalog import PUBLIC_LABEL_TO_LEGACY_MECHANISM_ID
from qec_twin.mechanisms.catalog import SURFACE_CONDITIONAL_DIMENSION_TARGET_IDS
from qec_twin.mechanisms.catalog import legacy_mechanism_id, mechanism_label_namespace, mechanism_public_label
from qec_twin.mechanisms.catalog import mechanism_contract, mechanism_taxonomy_contract_audit
from qec_twin.forward.ptm import channel_fingerprint, ptm_from_kraus, ptm_from_unitary, rzz_ptm_block_audit
from qec_twin.forward.ptm import probe_response_fingerprint, rzz_type_feature_names, rzz_type_feature_vector
from qec_twin.contexts.probe_catalog import build_default_oracle_mechanisms


def test_amplitude_damping_preserves_trace_and_probabilities_normalize() -> None:
    rho = np.array([[0.2, 0.1], [0.1, 0.8]], dtype=np.complex128)
    out = apply_kraus(rho, amplitude_damping_kraus(0.25))
    probs = measurement_probabilities_z(out, num_qubits=1)

    assert np.isclose(np.trace(out), 1.0)
    assert np.isclose(probs.sum(), 1.0)
    assert np.all(probs >= 0.0)


def test_stochastic_pauli_ptm_is_diagonal() -> None:
    kraus = pauli_stochastic_kraus({"X": 0.01, "Y": 0.02, "Z": 0.03})
    ptm = ptm_from_kraus(kraus)

    assert ptm.shape == (4, 4)
    assert np.allclose(ptm, np.diag(np.diag(ptm)), atol=1e-12)
    assert np.isclose(ptm[0, 0], 1.0)


def test_rzz_ptm_has_fixed_and_two_entry_blocks() -> None:
    ptm = ptm_from_unitary(rzz_unitary(0.2))
    audit = rzz_ptm_block_audit(ptm)

    assert ptm.shape == (16, 16)
    assert audit["max_column_support"] <= 2
    assert audit["num_fixed_columns"] > 0
    assert audit["num_two_entry_columns"] > 0


def test_readout_and_mechanism_fingerprints_are_finite() -> None:
    matrix = readout_bias_matrix(p0_to_1=0.02, p1_to_0=0.01)
    assert np.allclose(matrix.sum(axis=1), 1.0)

    specs = [
        MechanismSpec("M0", "pauli", 1, {"p_x": 0.001, "p_y": 0.002, "p_z": 0.003}),
        MechanismSpec("M8", "rzz", 2, {"epsilon": 0.04}),
        MechanismSpec("M6", "rx", 1, {"axis": "rx", "epsilon": 0.03}),
        MechanismSpec("M7", "rz", 1, {"epsilon": 0.04}),
        MechanismSpec("M4", "amp", 1, {"gamma": 0.02}),
        MechanismSpec("M15", "custom", 1, {"eta": 0.02}),
        MechanismSpec("M9", "depolarizing", 2, {"p": 0.006}),
        MechanismSpec("M1", "readout", 1, {"p": 0.02}),
    ]
    for spec in specs:
        channel = mechanism_channel(spec)
        features = channel_fingerprint(spec, paper_informed=True)
        probe = probe_response_fingerprint(spec)
        assert channel["kind"] in {"kraus", "unitary", "readout"}
        assert features.ndim == 1
        assert np.isfinite(features).all()
        assert probe.shape == (32,)
        assert np.isfinite(probe).all()


def test_rzz_type_features_are_named_and_rzz_specific() -> None:
    rzz = MechanismSpec("M8", "rzz", 2, {"epsilon": 0.04})
    pauli = MechanismSpec("M0", "pauli", 1, {"p_x": 0.001, "p_y": 0.002, "p_z": 0.003})

    assert rzz_type_feature_names() == [
        "rzz_type1_commuting_fixed_fraction",
        "rzz_type2_two_entry_rotation_fraction",
        "rzz_type3_nonclifford_rotation_strength",
        "rzz_type4_hard_residual_leakage",
    ]
    assert rzz_type_feature_vector(rzz).shape == (4,)
    assert np.isfinite(rzz_type_feature_vector(rzz)).all()
    assert np.allclose(rzz_type_feature_vector(pauli), 0.0)


def test_m13_m14_contracts_are_mathematically_separated() -> None:
    m13 = MechanismSpec(
        "M13",
        MECHANISM_NAMES["M13"],
        1,
        {"operation_axis": "rx", "epsilon": 0.031},
        instruction="rx",
        qubits=(0,),
    )
    m14 = MechanismSpec(
        "M14",
        MECHANISM_NAMES["M14"],
        1,
        {"operation_axis": "rx", "error_axis": "rz", "epsilon": 0.028},
        instruction="rx",
        qubits=(0,),
    )

    m13_channel = mechanism_channel(m13)
    m14_channel = mechanism_channel(m14)

    assert m13_channel["definition_contract"]["context_dependent"] is True
    assert m13_channel["definition_contract"]["drift_overlay_payload_present"] is True
    assert m13_channel["definition_contract"]["channel_representation"] == "random_unitary_kraus_mixture"
    assert m13_channel["kind"] == "kraus"
    assert m14_channel["definition_contract"]["operation_dependent"] is True
    assert m14_channel["definition_contract"]["distinct_from_axis_overrotation"] is True
    assert np.allclose(m14_channel["unitary"], rz_unitary(0.028))
    assert m13_channel["definition_contract"]["channel_axis"] != m14_channel["definition_contract"]["channel_axis"]


def test_m13_drift_overlay_channel_is_not_plain_rx_at_row_level() -> None:
    m13 = MechanismSpec(
        "M13",
        MECHANISM_NAMES["M13"],
        1,
        {
            "operation_axis": "rx",
            "epsilon": 0.035,
            "epsilon_mean": 0.035,
            "epsilon_span": 0.018,
        },
        instruction="rx",
        qubits=(0,),
    )

    channel = mechanism_channel(m13)
    kraus = [np.asarray(item, dtype=np.complex128) for item in channel["kraus"]]
    effect = sum(op.conj().T @ op for op in kraus)
    drift_ptm = ptm_from_kraus(kraus)
    plain_ptm = ptm_from_unitary(rx_unitary(0.035))

    assert channel["kind"] == "kraus"
    assert len(kraus) == 3
    assert np.allclose(effect, np.eye(2), atol=1e-12)
    assert float(np.linalg.norm(drift_ptm - plain_ptm)) > 1.0e-4
    assert channel["definition_contract"]["drift_overlay_payload_present"] is True
    assert channel["definition_contract"]["single_context_exact_recovery_required"] is False


def test_balanced_m13_records_serialize_drift_overlay_payload() -> None:
    specs = build_default_oracle_mechanisms(
        {
            "num_qubits": 20,
            "mechanism_set": ["M13"],
            "balanced_min_instances_per_mechanism": 3,
            "multicircuit_teacher_batch": True,
            "balanced_strength_variants": True,
            "balanced_strength_variant_strategy": "decorrelated_latin",
        }
    )

    assert len(specs) == 3
    for spec in specs:
        record = spec.audit_dict()

        assert spec.parameters["drift_visibility_scale"] == M13_DEFAULT_DRIFT_VISIBILITY_SCALE
        assert record["parameters"]["drift_visibility_scale"] == M13_DEFAULT_DRIFT_VISIBILITY_SCALE
        assert record["drift_overlay_present"] is True
        assert record["drift_overlay"]["drift_visibility_scale"] == M13_DEFAULT_DRIFT_VISIBILITY_SCALE
        assert record["claims_standalone_flat_mechanism"] is False


def test_implemented_catalog_mechanisms_have_distinct_channel_fingerprints() -> None:
    fingerprints = {}
    for mechanism_id in IMPLEMENTED_MECHANISM_IDS:
        num_qubits = 2 if mechanism_id in RZZ_FAMILY_IDS else 1
        instruction = "rzz" if num_qubits == 2 else ("measure" if mechanism_id in READOUT_MECHANISM_IDS else "id")
        spec = MechanismSpec(
            mechanism_id,
            MECHANISM_NAMES[mechanism_id],
            num_qubits,
            {},
            instruction=instruction,
            qubits=tuple(range(num_qubits)),
        )
        channel = mechanism_channel(spec)
        fingerprint = np.concatenate([channel_fingerprint(spec, paper_informed=True), probe_response_fingerprint(spec)])

        assert channel["kind"] in {"kraus", "unitary", "readout"}
        assert np.isfinite(fingerprint).all()
        fingerprints[mechanism_id] = fingerprint

    assert set(fingerprints) == set(IMPLEMENTED_MECHANISM_IDS)
    for left_idx, left in enumerate(IMPLEMENTED_MECHANISM_IDS):
        for right in IMPLEMENTED_MECHANISM_IDS[left_idx + 1 :]:
            assert float(np.linalg.norm(fingerprints[left] - fingerprints[right])) > 1e-6


def test_mechanism_taxonomy_contract_marks_composite_targets_explicitly() -> None:
    audit = mechanism_taxonomy_contract_audit()

    assert audit["passed"] is True
    assert audit["schema"] == "qec_twin_mechanism_taxonomy_contract_audit_v2"
    assert audit["label_scheme"] == "flat_F_nonflat_M_v1"
    assert set(audit["contracts"]) == set(IMPLEMENTED_MECHANISM_IDS)
    assert "M11" not in MECHANISM_LEAF_EXACT_IDS
    assert "M11" in NON_FLAT_PRIMARY_TARGET_IDS
    assert set(PRIMARY_FLAT_CLUSTER_TARGET_IDS) < set(IMPLEMENTED_MECHANISM_IDS)
    assert set(PRIMARY_FLAT_CLUSTER_TARGET_IDS) <= set(MECHANISM_LEAF_EXACT_IDS)
    assert {"M6", "M22", "M23"} <= set(SURFACE_CONDITIONAL_DIMENSION_TARGET_IDS)
    assert not {"M6", "M22", "M23"} & set(CURRENT_VISIBLE_SURFACE_FLAT_EXACT_CLAIM_TARGET_IDS)
    assert set(audit["surface_conditional_dimension_target_ids"]) == set(SURFACE_CONDITIONAL_DIMENSION_TARGET_IDS)
    assert set(audit["current_visible_surface_flat_exact_claim_target_ids"]) == set(CURRENT_VISIBLE_SURFACE_FLAT_EXACT_CLAIM_TARGET_IDS)
    assert list(PRIMARY_FLAT_PUBLIC_LABELS) == [f"F{idx}" for idx in range(len(PRIMARY_FLAT_CLUSTER_TARGET_IDS))]
    assert list(NON_FLAT_PUBLIC_LABELS) == [f"M{idx}" for idx in range(len(NON_FLAT_PRIMARY_TARGET_IDS))]
    assert len(PUBLIC_LABEL_TO_LEGACY_MECHANISM_ID) == len(IMPLEMENTED_MECHANISM_IDS)
    assert len(set(PUBLIC_LABEL_TO_LEGACY_MECHANISM_ID)) == len(IMPLEMENTED_MECHANISM_IDS)
    for mechanism_id in PRIMARY_FLAT_CLUSTER_TARGET_IDS:
        public_label = mechanism_public_label(mechanism_id)
        assert public_label.startswith("F")
        assert mechanism_label_namespace(mechanism_id) == "flat"
        assert legacy_mechanism_id(public_label) == mechanism_id
        assert mechanism_contract(mechanism_id)["public_label"] == public_label
        assert mechanism_contract(mechanism_id)["legacy_catalog_id"] == mechanism_id
    for mechanism_id in NON_FLAT_PRIMARY_TARGET_IDS:
        public_label = mechanism_public_label(mechanism_id)
        assert public_label.startswith("M")
        assert mechanism_label_namespace(mechanism_id) == "non_flat"
        assert legacy_mechanism_id(public_label) == mechanism_id
        assert mechanism_contract(mechanism_id)["public_label"] == public_label
    for mechanism_id in ["M0", "M1", "M2", "M3", "M9", "M10", "M13", "M14", "M15", "M16", "M18", "M19", "M27", "M34"]:
        assert mechanism_id in NON_FLAT_PRIMARY_TARGET_IDS
        assert mechanism_contract(mechanism_id)["primary_flat_cluster_target"] is False
    assert mechanism_contract("M11")["contract_role"] == "overlay_family"
    assert mechanism_contract("M11")["leaf_exact_effect_supported"] is False
    assert mechanism_contract("M11")["public_label"].startswith("M")
    assert mechanism_contract("M13")["contract_role"] == "context_conditioned_family"
    assert mechanism_contract("M16")["base_family"] == "readout_spam"
    assert mechanism_contract("M6")["primary_flat_cluster_target"] is True
    assert mechanism_contract("M6")["current_visible_surface_flat_exact_claim_allowed"] is False
    assert "paired_observability_group" not in mechanism_contract("M6")
    assert len(mechanism_contract("M6")["targeted_observability_group"]) >= 3
    assert mechanism_contract("M22")["current_visible_surface_claim_target"] == "parasitic_axis_dimension_recovery"
    assert "paired_observability_group" not in mechanism_contract("M22")
    assert mechanism_contract("M22")["targeted_observability_group"] == ["M6", "M13", "M22", "M23"]
    assert mechanism_contract("M23")["targeted_observability_group"] == ["M6", "M13", "M22", "M23"]


def test_mechanism_spec_audit_dict_exposes_public_label_and_legacy_id() -> None:
    flat = MechanismSpec("M8", MECHANISM_NAMES["M8"], 2, {"epsilon": 0.04}, instruction="rzz", qubits=(0, 1))
    non_flat = MechanismSpec(
        "M11",
        MECHANISM_NAMES["M11"],
        2,
        {
            "epsilon": 0.02,
            "spectator_overlay_present": True,
            "base_mechanism": "M8",
            "victim_relative_location": "edge",
            "aggressor_relative_location": "adjacent_gate",
            "coupling_axis": "ZZ",
            "timing_context": "same_cycle",
            "spectator_strength": 0.02,
            "victim_qubit": 1,
            "aggressor_qubit": 2,
            "claims_standalone_flat_mechanism": False,
        },
        instruction="rzz",
        qubits=(1, 2),
    )

    flat_audit = flat.audit_dict()
    non_flat_audit = non_flat.audit_dict()

    assert flat_audit["legacy_catalog_id"] == "M8"
    assert flat_audit["mechanism_id"] == "M8"
    assert flat_audit["public_label"].startswith("F")
    assert flat_audit["label_namespace"] == "flat"
    assert non_flat_audit["legacy_catalog_id"] == "M11"
    assert non_flat_audit["mechanism_id"] == "M11"
    assert non_flat_audit["public_label"].startswith("M")
    assert non_flat_audit["label_namespace"] == "non_flat"
    assert non_flat_audit["contract_role"] == "overlay_family"
    assert non_flat_audit["public_effect_family"] == "spectator_overlay"
    assert str(non_flat_audit["public_overlay_class"]).endswith("_overlay")
    assert str(non_flat_audit["nonflat_public_label"]).startswith("spectator_overlay_")
    assert non_flat_audit["spectator_overlay_present"] is True
    assert non_flat_audit["base_mechanism"] == "M8"
    assert non_flat_audit["victim_relative_location"] == "edge"
    assert non_flat_audit["aggressor_relative_location"] == "adjacent_gate"
    assert non_flat_audit["coupling_axis"] == "ZZ"
    assert non_flat_audit["timing_context"] == "same_cycle"
    assert non_flat_audit["spectator_strength"] == 0.02
    assert non_flat_audit["spectator_overlay"]["present"] is True
    assert non_flat_audit["spectator_overlay"]["base_mechanism"] == "M8"


def test_carrier_surrogate_claim_boundary() -> None:
    m11 = MechanismSpec("M11", MECHANISM_NAMES["M11"], 2, {"epsilon": 0.02}, instruction="rzz", qubits=(1, 2))

    channel = mechanism_channel(m11)
    contract = channel["definition_contract"]

    assert channel["kind"] == "unitary"
    assert np.allclose(channel["unitary"], rzz_unitary(0.02))
    assert contract["contract_role"] == "overlay_family"
    assert contract["sampling_surrogate"]["carrier_channel"] == "rzz_unitary"
    assert contract["sampling_surrogate"]["claims_exact_physical_overlay_channel"] is False
    assert contract["sampling_surrogate"]["claims_standalone_flat_mechanism"] is False
    assert contract["leaf_exact_effect_supported"] is False
    assert contract["primary_flat_cluster_target"] is False


def test_cptp_guardrail_accepts_implemented_catalog_mechanisms() -> None:
    specs = []
    for mechanism_id in IMPLEMENTED_MECHANISM_IDS:
        num_qubits = 2 if mechanism_id in RZZ_FAMILY_IDS else 1
        instruction = "rzz" if num_qubits == 2 else ("measure" if mechanism_id in READOUT_MECHANISM_IDS else "id")
        specs.append(
            MechanismSpec(
                mechanism_id,
                MECHANISM_NAMES[mechanism_id],
                num_qubits,
                {},
                instruction=instruction,
                qubits=tuple(range(num_qubits)),
            )
        )

    audit = build_cptp_guardrail_audit(specs)

    assert audit["schema"] == "qec_twin_layer1_cptp_guardrail_audit_v1"
    assert audit["passed"] is True
    assert audit["num_failed_records"] == 0
    assert audit["num_mechanism_records"] == len(IMPLEMENTED_MECHANISM_IDS)


def test_cptp_guardrail_checks_unitary_kraus_and_readout_representations() -> None:
    unitary = audit_mechanism_physicality(MechanismSpec("M8", "rzz", 2, {"epsilon": 0.04}, instruction="rzz", qubits=(0, 1)))
    kraus = audit_mechanism_physicality(MechanismSpec("M4", "amp", 1, {"gamma": 0.02}, instruction="id", qubits=(0,)))
    readout = audit_mechanism_physicality(MechanismSpec("M1", "readout", 1, {"p": 0.02}, instruction="measure", qubits=(0,)))

    assert unitary["kind"] == "unitary"
    assert unitary["passed"] is True
    assert unitary["complete_positivity_source"] == "unitary_representation"
    assert unitary["complete_positivity_passed"] is True
    assert float(unitary["unitary_residual_max_abs"]) <= 1.0e-9
    assert kraus["kind"] == "kraus"
    assert kraus["passed"] is True
    assert kraus["complete_positivity_source"] == "kraus_representation"
    assert kraus["complete_positivity_passed"] is True
    assert float(kraus["kraus_tp_residual_max_abs"]) <= 1.0e-9
    assert readout["kind"] == "readout"
    assert readout["passed"] is True
    assert readout["complete_positivity_source"] == "classical_stochastic_readout_matrix"
    assert readout["complete_positivity_passed"] is True
    assert float(readout["readout_row_sum_residual_max_abs"]) <= 1.0e-9


def test_cptp_guardrail_rejects_invalid_probability_parameters_before_flooring() -> None:
    audit = audit_mechanism_physicality(MechanismSpec("M4", "amp", 1, {"gamma": -0.1}, instruction="id", qubits=(0,)))

    assert audit["kind"] == "kraus"
    assert audit["passed"] is False
    assert audit["parameter_validity_passed"] is False
    invalid = audit["parameter_validity"]["invalid_parameters"]  # type: ignore[index]
    assert invalid[0]["parameter"] == "gamma"


def test_cptp_guardrail_rejects_wrong_declared_channel_dimension() -> None:
    audit = audit_mechanism_physicality(MechanismSpec("M8", "rzz", 1, {"epsilon": 0.04}, instruction="rzz", qubits=(0,)))

    assert audit["kind"] == "unitary"
    assert audit["passed"] is False
    assert audit["channel_dimension_expected"] == 2
    assert audit["channel_dimension_actual"] == [4, 4]
    assert audit["channel_dimension_passed"] is False
