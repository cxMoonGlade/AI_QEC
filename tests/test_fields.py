import torch

from scope_static.fields import (
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
