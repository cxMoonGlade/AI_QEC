"""Independent dense-reference certification of the restricted MCWF/MPS route.

The acceptance path compares the carrier output with
``carrier.joint_lindbladian.assemble_substep_channel`` using channel or record
metrics. Its corruption falsifier replaces the carrier's Hamiltonian gates with
identities while leaving the per-term dense reference unchanged, so shared-code
agreement cannot produce a pass. This is a GPU-only scientific acceptance file.

Run: conda run -n ecs python -m pytest -q tests/test_axis1_mcwf_dense_certification.py
"""
from __future__ import annotations

import math

import pytest
import torch

cuda_ok = torch.cuda.is_available()
if not cuda_ok:
    pytest.fail(
        "MCWF dense-reference certification is GPU-gated; CUDA is required",
        pytrace=False,
    )

import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as execmod  # noqa: E402
from error_coupling_simulator.frontend import (  # noqa: E402
    CircuitBuilder,
    Axis1LocalLindbladContextSpec,
    axis1_mcwf_mps_state_record_execution_manifest,
    circuit_ir_to_substep_schedule,
)
from error_coupling_simulator.frontend.axis1_mcwf_dense_certification import (  # noqa: E402
    restricted_acceptance_policy,
)


def _ququart_transport_schedule():
    """A coherent ququart leakage-transport gate (|1,2> -> |3,0>) + measure — deterministic
    level records, so correct=[[3,0]] while a no-op carrier stays at [[1,2]] (TV = 1)."""
    builder = CircuitBuilder(num_qubits=2)
    builder.cz((0, 1))
    dt_ns = _dt_ns_of(builder)
    builder = CircuitBuilder(num_qubits=2)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            leak_transport_30_12_rad_per_ns=math.pi / (2.0 * dt_ns),
        )
    )
    builder.cz((0, 1))
    builder.measure((0, 1), key=("m0", "m1"))
    return circuit_ir_to_substep_schedule(builder.build())


def _dt_ns_of(builder) -> float:
    schedule = circuit_ir_to_substep_schedule(builder.build())
    for substep in schedule.substeps if hasattr(schedule, "substeps") else []:
        dt = float(getattr(substep, "dt_ns", 0.0) or 0.0)
        if dt > 0.0:
            return dt
    return 25.0


def _run(schedule, **kw):
    return axis1_mcwf_mps_state_record_execution_manifest(
        schedule, local_dims=[4, 3], initial_levels=[1, 2], leaked_readout_b=1.0,
        trajectory_count=4, rng_seed=904, **kw
    )


def _identity_group_gates(real_fn):
    """Wrap _hamiltonian_group_gates to return identity gates on the same supports (a NO-OP
    Hamiltonian carrier) — the cert's term-based oracle is unaffected, so the mismatch is caught."""
    def _patched(substep, *, dt_ns, local_dims, device):
        groups = real_fn(substep, dt_ns=dt_ns, local_dims=local_dims, device=device)
        out = []
        for g in groups:
            dim = int(g["gate"].shape[-1])
            out.append({**g, "gate": torch.eye(dim, dtype=torch.complex128, device=device)})
        return out
    return _patched


def test_restricted_carrier_matches_dense_reference():
    """The declared restricted carrier matches the independent dense reference."""
    manifest = _run(_ququart_transport_schedule())
    assert manifest["verdict"] == "pass"
    assert manifest["restricted_acceptance_policy"]["accepted_for_restricted_execution"] is True


def test_dense_reference_rejects_noop_carrier(monkeypatch):
    """Identity carrier gates are rejected while the dense reference remains physical."""
    schedule = _ququart_transport_schedule()
    monkeypatch.setattr(
        execmod, "_hamiltonian_group_gates", _identity_group_gates(execmod._hamiltonian_group_gates)
    )
    manifest = _run(schedule)
    assert manifest["verdict"] == "fail"
    acceptance = manifest["restricted_acceptance_policy"]
    assert acceptance["accepted_for_restricted_execution"] is False
    cert = acceptance["dense_jointL_record_certification"]
    assert cert["executed"] is True              # the cert ran (did not silently skip)
    assert cert["passed"] is False               # and it FAILED (no-op != oracle)
    assert cert["comparison_outcome_is_metric"] is True  # via a real metric, not a policy flag


def test_certification_surfaces_declared_metric():
    """A matching run reports TV or process infidelity, not a policy-only flag."""
    manifest = _run(_ququart_transport_schedule())
    cert = manifest["restricted_acceptance_policy"]["dense_jointL_record_certification"]
    assert cert["executed"] is True
    assert cert["comparison_outcome_is_metric"] is True
    assert cert.get("metric") in {
        "total_variation_distance",
        "process_infidelity_one_minus_Fe",
        "level_record_total_variation_distance",
    } or "variation" in str(cert.get("metric", "")) or "Fe" in str(cert.get("metric", ""))
    assert isinstance(cert.get("value"), float)


def test_missing_seed_not_accepted_as_sampled_evidence(monkeypatch):
    """A sampled run with no rng seed is not reproducible ⇒ not accepted as sampled evidence."""
    schedule = _ququart_transport_schedule()
    manifest = axis1_mcwf_mps_state_record_execution_manifest(
        schedule, local_dims=[4, 3], initial_levels=[1, 2], leaked_readout_b=1.0,
        trajectory_count=4, rng_seed=None,
    )
    acceptance = manifest["restricted_acceptance_policy"]
    assert acceptance["accepted_for_sampled_execution_evidence"] is False


def test_restricted_policy_requires_explicit_gross_verdict():
    """A certification row missing the current gross verdict fails loudly."""
    with pytest.raises(KeyError, match="passed_gross"):
        restricted_acceptance_policy(
            execution={
                "total_probability_residual": 0.0,
                "trajectory_sampling": {
                    "mode": "sampled_fixed_microstep_mcwf_trajectories"
                },
            },
            certification={
                "executed": True,
                "passed": True,
                "comparison_outcome_is_metric": True,
            },
            program={"requires_scalable_backend": False},
            rng_seed=904,
            trajectory_count=4,
        )
