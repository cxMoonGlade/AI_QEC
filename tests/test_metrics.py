import torch

from scope_static.fault_graph import FaultGraph
from scope_static.metrics import (
    compression_audit,
    d_q_dem_distance,
    exact_observation_bit_rates,
    exact_observation_pair_joint_rates,
    observation_bit_rates_from_distribution,
    observation_pair_rates_from_distribution,
    shots_to_threshold,
)
from scope_static.likelihood import parity_distribution


def test_dq_dem_only_permits_identical_mask_permutations():
    masks = torch.tensor(
        [
            [1, 1, 0],
            [0, 0, 1],
        ],
        dtype=torch.bool,
    )
    graph = FaultGraph.from_raw_masks(
        masks,
        num_detectors=2,
        num_observables=0,
        residual_rank=0,
        canonicalize_duplicate_masks=False,
    )
    learned = torch.tensor([1.0, 2.0, 3.0])
    teacher = torch.tensor([2.0, 1.0, 3.0])
    assert d_q_dem_distance(graph, learned, teacher) == 0.0

    bad_teacher = torch.tensor([3.0, 1.0, 2.0])
    assert d_q_dem_distance(graph, learned, bad_teacher) > 0.0


def test_sparse_exact_moments_match_global_distribution():
    masks = torch.tensor(
        [
            [1, 0, 1],
            [0, 1, 1],
        ],
        dtype=torch.bool,
    )
    graph = FaultGraph.from_raw_masks(
        masks,
        num_detectors=2,
        num_observables=0,
        residual_rank=0,
        canonicalize_duplicate_masks=False,
    )
    logits = torch.tensor([-1.2, -2.0, -3.0], dtype=torch.float64)
    dist = parity_distribution(graph, logits)
    rates = exact_observation_bit_rates(graph, logits, bits=(0, 1))
    pair_rates = exact_observation_pair_joint_rates(graph, logits, pairs=[(0, 1)])
    assert torch.allclose(rates, observation_bit_rates_from_distribution(dist, graph.B))
    assert torch.allclose(pair_rates[0], observation_pair_rates_from_distribution(dist, graph.B)[0, 1])


def test_compression_audit_labels_soft_compression_truthfully():
    masks = torch.tensor(
        [
            [1, 0, 1, 0],
            [0, 1, 0, 1],
        ],
        dtype=torch.bool,
    )
    graph = FaultGraph.from_raw_masks(
        masks,
        num_detectors=2,
        num_observables=0,
        residual_rank=2,
        canonicalize_duplicate_masks=False,
        orbit_ids=torch.tensor([0, 0, 1, 1]),
    )
    audit = compression_audit(graph)
    assert audit["P_local"] == 4
    assert audit["P_hard"] == 2
    assert audit["P_soft"] == 6
    assert audit["hard_compressed"] is True
    assert audit["soft_compressed"] is False
    assert audit["rank_condition_satisfied"] is True

    rank_zero_graph = FaultGraph.from_raw_masks(
        masks,
        num_detectors=2,
        num_observables=0,
        residual_rank=0,
        canonicalize_duplicate_masks=False,
        orbit_ids=torch.tensor([0, 0, 1, 1]),
    )
    assert compression_audit(rank_zero_graph)["rank_condition_satisfied"] is False


def test_shots_to_threshold_uses_mean_across_seeds_by_default():
    records = [
        {"model": "hard_orbit", "teacher_mode": "exact_orbit", "epsilon_break": 0.0, "seed": 0, "shots": 512, "delta_nll_oracle": 0.01},
        {"model": "hard_orbit", "teacher_mode": "exact_orbit", "epsilon_break": 0.0, "seed": 1, "shots": 512, "delta_nll_oracle": 0.20},
        {"model": "hard_orbit", "teacher_mode": "exact_orbit", "epsilon_break": 0.0, "seed": 0, "shots": 2048, "delta_nll_oracle": 0.01},
        {"model": "hard_orbit", "teacher_mode": "exact_orbit", "epsilon_break": 0.0, "seed": 1, "shots": 2048, "delta_nll_oracle": 0.03},
    ]
    result = shots_to_threshold(records, threshold_epsilon=0.05)
    summary = result[("hard_orbit", "exact_orbit", 0.0, None)]
    assert summary["shots_to_threshold"] == 2048
    assert summary["threshold_seed_policy"] == "mean"
    assert summary["passing_summary"]["num_seeds"] == 2


def test_shots_to_threshold_can_require_all_seeds():
    records = [
        {"model": "soft_feature_orbit", "teacher_mode": "exact_orbit", "epsilon_break": 0.0, "seed": 0, "shots": 512, "delta_nll_oracle": 0.01},
        {"model": "soft_feature_orbit", "teacher_mode": "exact_orbit", "epsilon_break": 0.0, "seed": 1, "shots": 512, "delta_nll_oracle": 0.20},
        {"model": "soft_feature_orbit", "teacher_mode": "exact_orbit", "epsilon_break": 0.0, "seed": 0, "shots": 2048, "delta_nll_oracle": 0.01},
        {"model": "soft_feature_orbit", "teacher_mode": "exact_orbit", "epsilon_break": 0.0, "seed": 1, "shots": 2048, "delta_nll_oracle": 0.06},
    ]
    mean_result = shots_to_threshold(records, threshold_epsilon=0.05, seed_policy="mean")
    all_result = shots_to_threshold(records, threshold_epsilon=0.05, seed_policy="all")
    key = ("soft_feature_orbit", "exact_orbit", 0.0, None)
    assert mean_result[key]["shots_to_threshold"] == 2048
    assert all_result[key]["shots_to_threshold"] is None


def test_shots_to_threshold_groups_by_residual_rank():
    records = [
        {
            "model": "soft_feature_orbit",
            "teacher_mode": "in_family_soft_residual",
            "epsilon_break": 0.3,
            "residual_rank": 0,
            "seed": 0,
            "shots": 512,
            "delta_nll_oracle": 0.02,
        },
        {
            "model": "soft_feature_orbit",
            "teacher_mode": "in_family_soft_residual",
            "epsilon_break": 0.3,
            "residual_rank": 5,
            "seed": 0,
            "shots": 512,
            "delta_nll_oracle": 0.005,
        },
    ]
    result = shots_to_threshold(records, threshold_epsilon=0.01)
    assert result[("soft_feature_orbit", "in_family_soft_residual", 0.3, 0)]["shots_to_threshold"] is None
    assert result[("soft_feature_orbit", "in_family_soft_residual", 0.3, 5)]["shots_to_threshold"] == 512
