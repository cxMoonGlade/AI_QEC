import torch

from scope_static.dem.stim_dem import build_surface_code_graph
from scope_static.dem.teacher_logits import make_teacher_logits


def test_separated_teacher_has_clear_orbit_logit_gaps():
    graph = build_surface_code_graph(
        distance=3,
        rounds=1,
        residual_rank=0,
        noise={
            "after_clifford_depolarization": 0.001,
            "after_reset_flip_probability": 0.001,
            "before_measure_flip_probability": 0.001,
            "before_round_data_depolarization": 0.001,
        },
    )

    logits = make_teacher_logits(graph, mode="exact_orbit_separated", seed=0, dtype=torch.float64)
    orbit_logits = torch.stack(
        [logits[torch.nonzero(graph.orbit_ids == orbit, as_tuple=False).flatten()[0]] for orbit in range(graph.O)]
    )

    assert torch.all(torch.diff(torch.sort(orbit_logits).values) >= 0.3)
    for orbit in range(graph.O):
        idx = torch.nonzero(graph.orbit_ids == orbit, as_tuple=False).flatten()
        assert torch.allclose(logits[idx], logits[idx][0].expand_as(logits[idx]))


def test_separated_suffix_preserves_residual_teacher_modes():
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

    exact = make_teacher_logits(graph, mode="exact_orbit_separated", seed=0, dtype=torch.float64)
    residual = make_teacher_logits(
        graph,
        mode="in_family_soft_residual_separated",
        epsilon_break=0.3,
        seed=0,
        dtype=torch.float64,
    )

    assert exact.shape == residual.shape == (graph.M,)
    assert not torch.allclose(exact, residual)
