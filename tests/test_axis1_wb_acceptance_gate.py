"""Step-2 (W-B) regression + GPU cert — the MCWF acceptance gate is LIVE and NON-CIRCULAR.

The previous gate was INERT: ``accepted = residual_ok AND seed_explicit`` reduced to "a seed was
supplied" (``total_probability_residual ≡ 0`` by construction) and never compared the carrier to any
oracle. The fix (``axis1_mcwf_dense_certification``) gates acceptance on a dense certification of the
carrier's ACTUAL output vs the INDEPENDENT oracle ``forward.joint_lindbladian.assemble_substep_channel``
(channel ``1−F_e`` / record + level-population TV, with a Hoeffding finite-shot CI; gross/strict tiers).

THE CENTRAL, ANTI-CIRCULAR TEST (``test_gate_rejects_noop_carrier``): monkeypatch the carrier's
``_hamiltonian_group_gates`` to identity (a NO-OP Hamiltonian) while leaving the cert's oracle — which
is built from the per-term physics (``_hamiltonian_matrix_for_term``), NOT from the carrier's gates —
intact. A circular cert (oracle derived from the carrier's own gates via ``logm``) would build a
matching no-op oracle and FALSELY pass; the fixed, term-based oracle detects the carrier did nothing
while real dynamics were scheduled, so the gate REJECTS (``verdict == "fail"``). This is the test the
inert gate fails and the fix passes, and it certifies the oracle is genuinely independent (rule I).

GPU-only (memory rule; CPU is not a release basis) — collection FAILS without CUDA.

Run:  conda run -n aiqec python -m pytest -q tests/test_axis1_wb_acceptance_gate.py
"""
from __future__ import annotations

import math

import pytest
import torch

cuda_ok = torch.cuda.is_available()
if not cuda_ok:
    pytest.fail(
        "W-B acceptance-gate cert is GPU-gated; CUDA-MISSING is NOT A RELEASE BASIS",
        pytrace=False,
    )

import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as execmod  # noqa: E402
from error_coupling_simulator.frontend import (  # noqa: E402
    CircuitBuilder,
    Axis1LocalLindbladContextSpec,
    axis1_mcwf_mps_state_record_execution_manifest,
    circuit_ir_to_substep_schedule,
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


def test_correct_carrier_accepted():
    """The faithful carrier matches the oracle ⇒ gate ACCEPTS (verdict pass)."""
    manifest = _run(_ququart_transport_schedule())
    assert manifest["verdict"] == "pass"
    assert manifest["restricted_acceptance_policy"]["accepted_for_restricted_execution"] is True


def test_gate_rejects_noop_carrier(monkeypatch):
    """CENTRAL anti-circular test: a NO-OP Hamiltonian carrier (identity gates) is REJECTED,
    because the oracle is built from the per-term physics, not the carrier's gates. The inert
    gate accepted any seeded run; a circular cert would also pass (oracle from the same no-op
    gates). The fixed gate rejects."""
    schedule = _ququart_transport_schedule()
    # sanity: the faithful run is accepted (verdict pass) — established by the test above.
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


def test_cert_surfaces_real_metric():
    """A faithful run carries a real field-standard metric (TV / 1−F_e), comparison_outcome_is_metric True."""
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
