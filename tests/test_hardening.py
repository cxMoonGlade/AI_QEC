import json

import torch
import yaml

from scope_static.experiments.run_static_hardening import run_hardening_experiment
from scope_static.fields import DiscoveryHardFaultLogitField
from scope_static.hardening import (
    apply_assignment_initialization,
    local_logit_assignment_initialization,
)


def test_straight_through_assignment_forward_uses_hard_labels():
    field = DiscoveryHardFaultLogitField(
        num_faults=3,
        num_prototypes=2,
        dtype=torch.float64,
        assignment_mode="straight_through",
        assignment_init_scale=0.0,
        alpha_init_scale=0.0,
    )
    with torch.no_grad():
        field.alpha.copy_(torch.tensor([-3.0, -5.0], dtype=torch.float64))
        field.assignment_logits[:, 0].copy_(torch.tensor([-10.0, 10.0, 10.0], dtype=torch.float64))

    assert torch.equal(field.hard_assignments(), torch.tensor([0, 1, 1]))
    assert torch.allclose(field.realized_logits(), torch.tensor([-3.0, -5.0, -5.0], dtype=torch.float64))


def test_local_logit_initializer_is_visible_and_sets_near_hard_assignments():
    local_logits = torch.tensor([-7.0, -7.1, -4.0, -4.2], dtype=torch.float64)
    init = local_logit_assignment_initialization(local_logits, num_prototypes=2)
    field = DiscoveryHardFaultLogitField(
        num_faults=4,
        num_prototypes=2,
        dtype=torch.float64,
        assignment_init_scale=0.0,
        alpha_init_scale=0.0,
    )
    apply_assignment_initialization(field, init, confidence=8.0)

    assert init.uses_hidden_omega is False
    assert init.source == "DISC10_local_logit_signature"
    assert torch.allclose(field.assignment_probabilities().sum(dim=1), torch.ones(4, dtype=torch.float64))
    assert torch.equal(field.hard_assignments(), init.labels)


def test_stage2a1_hardening_smoke_writes_schema_and_uses_validation_selection(tmp_path):
    config = {
        "run": {"name": "hardening_smoke", "output_dir": str(tmp_path / "out"), "device": "cpu", "dtype": "float64"},
        "circuit": {
            "family": "surface_code:rotated_memory_x",
            "distance": 3,
            "rounds": 1,
            "noise": {
                "after_clifford_depolarization": 0.001,
                "after_reset_flip_probability": 0.001,
                "before_measure_flip_probability": 0.001,
                "before_round_data_depolarization": 0.001,
            },
        },
        "graph": {"canonicalize_duplicate_masks": True, "residual_rank": 0},
        "windows": {"enabled": False},
        "experiment": {
            "seeds": [0],
            "teacher_cases": [{"mode": "exact_orbit_separated", "epsilon_break": 0.0}],
            "shot_budgets": [32],
            "heldout_shots": 64,
            "threshold_epsilon": 0.1,
        },
        "training": {
            "models": ["local", "known_hard_orbit", "disc_hard"],
            "steps": 1,
            "lr": 0.05,
            "aggregate_unique": True,
            "exact_likelihood_trainable": True,
            "dem_fault_logit_claim": True,
            "cptp_gksl_claim": False,
        },
        "evaluation": {"global_exact_max_bits": 20},
        "hardening": {
            "restarts": 1,
            "validation_shots": 32,
            "conditions": [
                {"id": "A", "name": "free_random_init", "assignment_mode": "soft", "initializer": "random"},
                {
                    "id": "D",
                    "name": "hard_st_local_logit_init",
                    "assignment_mode": "straight_through",
                    "initializer": "local_logit",
                },
            ],
        },
    }
    config_path = tmp_path / "hardening.yaml"
    config_path.write_text(yaml.safe_dump(config))
    result = run_hardening_experiment(config_path)

    assert result["stage"] == "stage2A.1"
    assert result["schema"] == "scope_static_stage2a1_hardening_v1"
    assert result["stage2a1_important_results"]["condition_summary"]
    hardening_records = [record for record in result["records"] if record.get("stage2a1_condition_id")]
    assert hardening_records
    assert all(record["ari_nmi_used_for_selection"] is False for record in hardening_records)
    assert all(record["selected_by_ari_nmi"] is False for record in hardening_records)
    assert all(record["selection_rule"] == "validation_nll_plus_observable_health" for record in hardening_records)
    assert any(record["assignment_initializer"] == "DISC10_local_logit_signature" for record in hardening_records)
    assert any(record["known_orbit_oracle_model"] == "known_hard_orbit" for record in hardening_records)
    for key in [
        "init_final_assignment_nmi",
        "fraction_rows_changed",
        "mean_assignment_entropy_start",
        "mean_assignment_entropy_end",
        "assignment_logit_grad_norm",
        "prototype_param_delta_norm",
        "cluster_mass_start",
        "cluster_mass_end",
    ]:
        assert key in hardening_records[0]

    metrics = json.loads((tmp_path / "out" / "metrics.json").read_text())
    assert metrics["hardening_restart_records"][0]["selection_rule"] == "validation_nll_plus_observable_health"
    assert metrics["stage2a1_important_results"]["assignment_movement_audit"]
    assert "stage2a1_conclusion" in metrics["stage2a1_important_results"]
    assert "assignment_movement_interpretation" in metrics["stage2a1_important_results"]
    assert (tmp_path / "out" / "stage2a1_summary.md").exists()
    assert "Assignment Movement Audit" in (tmp_path / "out" / "stage2a1_summary.md").read_text()
