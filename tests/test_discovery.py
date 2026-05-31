import math

import torch

from scope_static.dem.discovery import (
    add_known_orbit_deltas,
    discovery_assignment_metrics,
    discovery_parameter_audit,
)
from scope_static.dem.fault_graph import FaultGraph


def test_discovery_assignment_metrics_are_permutation_invariant_and_audit_entropy():
    hidden = torch.tensor([0, 0, 1, 1, 2, 2])
    S = torch.tensor(
        [
            [0.0, 1.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 1.0],
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
        ],
        dtype=torch.float64,
    )
    metrics = discovery_assignment_metrics(S, hidden, active_mass_threshold=1.0)
    assert metrics["ari"] == 1.0
    assert metrics["nmi"] == 1.0
    assert metrics["assignment_entropy_mean"] == 0.0
    assert metrics["assignment_entropy_normalized"] == 0.0
    assert metrics["num_active_prototypes"] == 3
    assert metrics["assignment_collapse"] is False

    diffuse = torch.full((6, 3), 1 / 3, dtype=torch.float64)
    diffuse_metrics = discovery_assignment_metrics(diffuse, hidden, active_mass_threshold=1.0)
    assert math.isclose(diffuse_metrics["assignment_entropy_normalized"], 1.0)
    assert diffuse_metrics["assignment_collapse"] is True


def test_discovery_parameter_audit_marks_free_assignment_as_not_compressed_claim():
    graph = FaultGraph.from_raw_masks(
        torch.tensor([[1, 0, 1, 0], [0, 1, 0, 1]], dtype=torch.bool),
        num_detectors=2,
        num_observables=0,
        residual_rank=1,
        canonicalize_duplicate_masks=False,
        orbit_ids=torch.tensor([0, 0, 1, 1]),
    )
    audit = discovery_parameter_audit(graph, model_name="disc_soft", prototype_count=3, residual_rank=1)
    assert audit["P_local"] == 4
    assert audit["P_known_hard_orbit"] == 2
    assert audit["P_discovery_prototypes"] == 6
    assert audit["P_discovery_assignment"] == 8
    assert audit["P_discovery_total"] == 14
    assert audit["assignment_parameterization"] == "free"
    assert audit["compressed_claim_allowed"] is False


def test_known_orbit_delta_uses_matched_oracle_record():
    records = [
        {
            "seed": 0,
            "teacher_mode": "exact_orbit",
            "epsilon_break": 0.0,
            "shots": 64,
            "residual_rank": 0,
            "model": "known_hard_orbit",
            "heldout_exact_nll": 1.2,
            "heldout_local_window_nll": 1.3,
        },
        {
            "seed": 0,
            "teacher_mode": "exact_orbit",
            "epsilon_break": 0.0,
            "shots": 64,
            "residual_rank": 0,
            "model": "disc_hard",
            "heldout_exact_nll": 1.25,
            "heldout_local_window_nll": 1.35,
        },
    ]
    add_known_orbit_deltas(records)
    assert records[1]["known_orbit_oracle_model"] == "known_hard_orbit"
    assert records[1]["known_orbit_oracle_available"] is True
    assert math.isclose(records[1]["delta_nll_known_orbit"], 0.05)
    assert records[1]["delta_nll_known_orbit_source"] == "global_exact"
