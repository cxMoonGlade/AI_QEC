import torch

from scope_static.fields import (
    DiscoveryHardFaultLogitField,
    DiscoveryHardField,
    DiscoverySoftFeatureFaultLogitField,
    DiscoverySoftFeatureField,
    HardOrbitFaultLogitField,
    HardOrbitField,
    LocalFaultLogitField,
    LocalField,
    SoftFeatureOrbitFaultLogitField,
    SoftFeatureOrbitField,
)
from scope_static.stim_dem import build_surface_code_graph


def test_field_parameter_counts_are_compressed():
    graph = build_surface_code_graph(
        distance=3,
        rounds=1,
        residual_rank=3,
        noise={
            "after_clifford_depolarization": 0.001,
            "after_reset_flip_probability": 0.001,
            "before_measure_flip_probability": 0.001,
            "before_round_data_depolarization": 0.001,
        },
    )
    assert LocalField is LocalFaultLogitField
    assert HardOrbitField is HardOrbitFaultLogitField
    assert SoftFeatureOrbitField is SoftFeatureOrbitFaultLogitField
    assert DiscoveryHardField is DiscoveryHardFaultLogitField
    assert DiscoverySoftFeatureField is DiscoverySoftFeatureFaultLogitField
    local = LocalFaultLogitField.from_graph(graph)
    hard = HardOrbitFaultLogitField.from_graph(graph)
    soft = SoftFeatureOrbitFaultLogitField.from_graph(graph)
    assert local.parameter_count == graph.M
    assert hard.parameter_count == graph.O
    assert soft.parameter_count == graph.O * (1 + graph.residual_rank)
    assert soft.realized_logits().shape == (graph.M,)


def test_soft_collapses_to_hard_for_orbit_constant_features():
    orbit_ids = torch.tensor([0, 0, 1, 1, 1])
    phi = torch.tensor(
        [
            [1.0, 2.0],
            [1.0, 2.0],
            [0.5, -1.0],
            [0.5, -1.0],
            [0.5, -1.0],
        ],
        dtype=torch.float64,
    )
    field = SoftFeatureOrbitFaultLogitField(orbit_ids, phi, dtype=torch.float64)

    with torch.no_grad():
        field.alpha.copy_(torch.tensor([-3.0, -4.0], dtype=torch.float64))
        field.beta.copy_(torch.tensor([[0.25, -0.5], [1.5, 0.25]], dtype=torch.float64))

    prototype_logits = field.alpha + (field.beta * torch.stack([phi[0], phi[2]])).sum(dim=1)
    logits = field.realized_logits()

    assert torch.allclose(logits, prototype_logits[orbit_ids])
    for omega in orbit_ids.unique():
        idx = orbit_ids == omega
        assert torch.allclose(logits[idx], logits[idx][0].expand_as(logits[idx]))


def test_discovery_hard_assignment_is_row_stochastic_and_counts_free_logits():
    field = DiscoveryHardFaultLogitField(
        num_faults=5,
        num_prototypes=3,
        dtype=torch.float64,
        assignment_init_scale=0.0,
        alpha_init_scale=0.0,
    )
    S = field.assignment_probabilities()
    assert S.shape == (5, 3)
    assert torch.allclose(S.sum(dim=1), torch.ones(5, dtype=torch.float64))
    assert field.parameter_count == 3 + 5 * (3 - 1)


def test_discovery_entropy_regularization_penalizes_diffuse_assignments():
    field = DiscoveryHardFaultLogitField(
        num_faults=5,
        num_prototypes=3,
        dtype=torch.float64,
        assignment_init_scale=0.0,
        alpha_init_scale=0.0,
        assignment_entropy_weight=0.02,
    )
    diffuse_loss = field.regularization_loss()

    with torch.no_grad():
        field.assignment_logits.fill_(-80.0)
        field.assignment_logits[:, 1] = 80.0

    hard_loss = field.regularization_loss()
    assert diffuse_loss > 0.0
    assert hard_loss < diffuse_loss


def test_discovery_hard_can_match_hard_orbit_with_near_one_hot_assignments():
    orbit_ids = torch.tensor([0, 1, 0, 2])
    hard = HardOrbitFaultLogitField(orbit_ids, dtype=torch.float64)
    disc = DiscoveryHardFaultLogitField(
        num_faults=4,
        num_prototypes=3,
        dtype=torch.float64,
        assignment_init_scale=0.0,
        alpha_init_scale=0.0,
    )
    with torch.no_grad():
        hard.alpha.copy_(torch.tensor([-3.0, -4.0, -5.0], dtype=torch.float64))
        disc.alpha.copy_(hard.alpha)
        disc.assignment_logits.fill_(-80.0)
        for fault, prototype in enumerate(orbit_ids.tolist()):
            if prototype > 0:
                disc.assignment_logits[fault, prototype - 1] = 80.0

    assert torch.allclose(disc.hard_assignments(), orbit_ids)
    assert torch.allclose(disc.realized_logits(), hard.realized_logits(), atol=1e-12, rtol=0.0)


def test_disc_soft_uses_learner_visible_features_without_hidden_orbit_centering():
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
    field = DiscoverySoftFeatureFaultLogitField.from_graph(
        graph,
        num_prototypes=graph.O,
        dtype=torch.float64,
        assignment_init_scale=0.0,
        alpha_init_scale=0.0,
    )
    assert field.learner_feature_uses_hidden_orbit_centering is False
    assert field.learner_visible_feature_source == "fixed_fault_features_without_hidden_orbit_selection_or_centering"
    assert field.phi.shape == graph.phi.shape
    assert not torch.allclose(field.phi, graph.phi)
