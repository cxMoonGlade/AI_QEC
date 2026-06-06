import torch

from qec_twin.decoder.fault_graph import FaultGraph, combine_duplicate_probabilities, gf2_rank, mask_states_from_matrix
from qec_twin.decoder.stim_dem import build_surface_code_graph


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
    assert audit["parity_storage"] == "sparse_supports_with_dense_A_compat"
    assert audit["num_sparse_support_entries"] == sum(len(support) for support in graph.supports_by_fault)


def test_sparse_support_views_match_dense_masks():
    raw_masks = torch.tensor(
        [
            [1, 0, 1],
            [0, 1, 1],
            [1, 0, 0],
        ],
        dtype=torch.bool,
    )
    graph = FaultGraph.from_raw_masks(
        raw_masks,
        num_detectors=3,
        num_observables=0,
        canonicalize_duplicate_masks=False,
    )
    assert graph.supports_by_fault == ((0, 2), (1,), (0, 1))
    assert graph.faults_by_observation_bit == ((0, 2), (1, 2), (0,))
    assert graph.packed_masks64 == ((5,), (2,), (3,))
    assert torch.equal(graph.mask_states, mask_states_from_matrix(graph.A))
    assert graph.dem_parity_map.num_observation_bits == graph.B
    assert torch.equal(graph.dem_parity_map.to_dense(), graph.A)
    fault_ids, local_masks = graph.project_window((0, 2))
    assert fault_ids.tolist() == [0, 2]
    assert local_masks.tolist() == [3, 1]
    faults = torch.tensor([[1, 0, 0], [1, 1, 1]], dtype=torch.bool)
    expected_observations = ((faults.to(torch.uint8) @ graph.A.T.to(torch.uint8)) % 2).to(dtype=torch.bool)
    assert torch.equal(graph.dem_parity_map.apply_faults(faults), expected_observations)


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
    assert audit["log2_state_count"] == graph.B
    assert audit["global_exact_state_count_materialized"] is True


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
