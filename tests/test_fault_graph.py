import torch

from scope_static.fault_graph import FaultGraph, combine_duplicate_probabilities, gf2_rank
from scope_static.stim_dem import build_surface_code_graph


def test_duplicate_mask_canonicalization_combines_probabilities():
    raw_masks = torch.tensor(
        [
            [1, 1, 0, 0],
            [0, 0, 1, 0],
        ],
        dtype=torch.bool,
    )
    raw_probabilities = torch.tensor([0.1, 0.2, 0.3, 0.4], dtype=torch.float64)
    graph = FaultGraph.from_raw_masks(
        raw_masks,
        num_detectors=2,
        num_observables=0,
        raw_probabilities=raw_probabilities,
        residual_rank=2,
    )
    assert graph.M == 2
    duplicate_effective_id = int(graph.raw_to_effective[0].item())
    assert graph.raw_to_effective.tolist().count(duplicate_effective_id) == 2
    expected = combine_duplicate_probabilities(raw_probabilities[:2])
    assert torch.isclose(graph.effective_probabilities[duplicate_effective_id], expected)
    assert len(graph.zero_mask_raw_indices) == 1
    audit = graph.audit_dict(
        exact_likelihood_trainable=True,
        dem_fault_logit_claim=True,
        cptp_gksl_claim=False,
    )
    assert audit["num_faults_raw_M"] == 4
    assert audit["num_faults_effective_M"] == 2
    assert audit["num_duplicate_mask_groups"] == 1
    assert audit["gf2_rank_A"] == gf2_rank(graph.A)


def test_stim_surface_code_graph_audit_uses_B_not_K():
    graph = build_surface_code_graph(
        distance=3,
        rounds=1,
        residual_rank=2,
        noise={
            "after_clifford_depolarization": 0.001,
            "after_reset_flip_probability": 0.001,
            "before_measure_flip_probability": 0.001,
            "before_round_data_depolarization": 0.001,
        },
    )
    audit = graph.audit_dict(
        exact_likelihood_trainable=True,
        dem_fault_logit_claim=True,
        cptp_gksl_claim=False,
    )
    assert audit["num_observation_bits_B"] == graph.num_detectors + graph.num_observables
    assert "num_observation_bits_K" not in audit
    assert audit["num_faults_raw_M"] >= audit["num_faults_effective_M"]
    assert audit["state_count_2_pow_B"] == 1 << graph.B


def test_soft_features_not_orbit_constant():
    raw_masks = torch.tensor(
        [
            [1, 0, 1, 0],
            [0, 1, 0, 1],
        ],
        dtype=torch.bool,
    )
    graph = FaultGraph.from_raw_masks(
        raw_masks,
        num_detectors=2,
        num_observables=0,
        residual_rank=4,
        canonicalize_duplicate_masks=False,
        orbit_ids=torch.tensor([0, 0, 1, 1]),
    )

    for omega in graph.orbit_ids.unique():
        idx = graph.orbit_ids == omega
        assert torch.allclose(
            graph.residual_features[idx].mean(dim=0),
            torch.zeros(graph.residual_rank, dtype=graph.residual_features.dtype),
        )

    audit = graph.residual_feature_audit_dict()
    assert audit["num_non_singleton_orbits"] == 2
    assert audit["num_orbits_with_nonzero_centered_feature_rank"] > 0
    assert audit["max_centered_feature_rank"] > 0
