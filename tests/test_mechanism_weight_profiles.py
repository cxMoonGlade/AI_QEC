from __future__ import annotations

from scope_static.primitives.mechanism_catalog import IMPLEMENTED_MECHANISM_IDS, MECHANISM_NAMES
from scope_static.primitives.mechanism_profiles import resolve_mechanism_weight_profile
from scope_static.primitives.probe_catalog import _merged_config
from scope_static.data_preparation.full_circuit_cudaq import _build_full_circuit_oracle_mechanisms


def test_weighted_realistic_profile_covers_current_catalog_without_legacy_semantic_drift() -> None:
    profile = resolve_mechanism_weight_profile("weighted_realistic_v1")

    assert profile["not_hardware_calibrated"] is True
    assert tuple(profile["mechanism_set"]) == IMPLEMENTED_MECHANISM_IDS
    assert set(profile["mechanism_instance_counts"]) == set(IMPLEMENTED_MECHANISM_IDS)
    assert set(profile["mechanisms"]) == set(IMPLEMENTED_MECHANISM_IDS)

    entries = profile["entries"]
    for mechanism_id in IMPLEMENTED_MECHANISM_IDS:
        assert entries[mechanism_id]["name"] == MECHANISM_NAMES[mechanism_id]

    parameters = profile["mechanisms"]
    assert "epsilon" not in parameters["M1"]
    assert "p0_to_1" in parameters["M1"]
    assert "p" not in parameters["M13"]
    assert "epsilon_mean" in parameters["M13"]
    assert "gamma_up" in parameters["M24"]


def test_weighted_discovery_floor_profile_keeps_rare_mechanisms_visible() -> None:
    realistic = resolve_mechanism_weight_profile("weighted_realistic_v1")
    floor = resolve_mechanism_weight_profile("weighted_discovery_floor_v1")

    assert min(floor["mechanism_instance_counts"].values()) >= 4
    assert floor["mechanism_instance_counts"]["M34"] >= realistic["mechanism_instance_counts"]["M34"]
    assert floor["mechanism_instance_counts"]["M15"] >= realistic["mechanism_instance_counts"]["M15"]


def test_weight_profile_expands_teacher_config_from_catalog_source_of_truth() -> None:
    cfg = _merged_config(
        {
            "num_qubits": 10,
            "probe_set": "base",
            "mechanism_weight_profile": "weighted_realistic_v1",
            "balanced_min_instances_per_mechanism": 2,
        }
    )

    assert cfg["mechanism_set"] == list(IMPLEMENTED_MECHANISM_IDS)
    assert set(cfg["mechanism_instance_counts"]) == set(IMPLEMENTED_MECHANISM_IDS)
    assert cfg["mechanism_instance_counts"]["M1"] == 12
    assert cfg["mechanisms"]["M1"]["p0_to_1"] == 0.028
    assert cfg["mechanisms"]["M13"]["epsilon_mean"] == 0.030
    assert cfg["mechanism_weight_profile_manifest"]["profile_name"] == "weighted_realistic_v1"

    mechanisms, repetitions, sampling_contract = _build_full_circuit_oracle_mechanisms(cfg)
    counts: dict[str, int] = {}
    for spec in mechanisms:
        counts[spec.mechanism_id] = counts.get(spec.mechanism_id, 0) + 1

    assert sampling_contract == "weighted"
    assert repetitions == 12
    assert counts["M1"] == 12
    assert counts["M15"] == 3
    assert counts["M34"] == 4
