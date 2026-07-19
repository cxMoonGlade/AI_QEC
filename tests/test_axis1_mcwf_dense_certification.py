"""Independent dense-reference certification of the restricted MCWF/MPS route.

The acceptance path compares the carrier output with
``carrier.joint_lindbladian.assemble_substep_channel`` using channel or record
metrics. Its corruption falsifiers replace either the carrier's Hamiltonian gates
or its X-basis rotation with identities while leaving the independent dense
reference unchanged, so shared-code agreement cannot produce a pass. This is a
GPU-only scientific acceptance file.

Run: conda run -n ecs python -m pytest -q tests/test_axis1_mcwf_dense_certification.py
"""
from __future__ import annotations

import copy
import hashlib
import math
from pathlib import Path

import pytest
import torch

cuda_ok = torch.cuda.is_available()
if not cuda_ok:
    pytest.fail(
        "MCWF dense-reference certification is GPU-gated; CUDA is required",
        pytrace=False,
    )

import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as execmod  # noqa: E402
import error_coupling_simulator.certify.axis1_mps as certmod  # noqa: E402
from error_coupling_simulator.frontend import (  # noqa: E402
    CircuitBuilder,
    Axis1LocalLindbladContextSpec,
    axis1_mcwf_mps_state_record_execution_manifest,
    circuit_ir_to_substep_schedule,
)
from error_coupling_simulator.certify.axis1_mps import (  # noqa: E402
    restricted_acceptance_policy,
)


class _AccessTrackingDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.accessed_keys = []

    def __getitem__(self, key):
        self.accessed_keys.append(key)
        return super().__getitem__(key)


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
    def _patched(substep, *, dt_ns, local_dims, device, term_records=None):
        groups = real_fn(
            substep,
            dt_ns=dt_ns,
            local_dims=local_dims,
            device=device,
            term_records=term_records,
        )
        out = []
        for g in groups:
            dim = int(g["gate"].shape[-1])
            out.append({**g, "gate": torch.eye(dim, dtype=torch.complex128, device=device)})
        return out
    return _patched


def _assert_dynamics_artifact_blocked(manifest, *, reason: str) -> None:
    assert manifest["verdict"] == "fail"
    assert manifest["passed"] is False
    assert manifest["execution_status"] == "blocked"
    assert manifest["mcwf_mps_backend_executed"] is False
    assert manifest["mps_execution"] is None
    assert manifest["blocked_reason"] == reason
    policy = manifest["restricted_acceptance_policy"]
    assert policy["accepted_for_restricted_execution"] is False
    assert policy["blocked_reason"] == reason


def test_restricted_carrier_matches_dense_reference():
    """The declared restricted carrier matches the independent dense reference."""
    manifest = _run(_ququart_transport_schedule())
    assert manifest["verdict"] == "pass"
    assert manifest["restricted_acceptance_policy"]["accepted_for_restricted_execution"] is True
    artifact = manifest["dynamics_artifact_reference_certification"]
    assert artifact["executed"] is True
    assert artifact["passed"] is True
    assert artifact["all_substeps_covered"] is True
    assert artifact["all_terms_covered"] is True
    assert artifact["all_groups_covered"] is True
    assert artifact["artifacts_bound_before_execution"] is True
    assert artifact["post_execution_integrity_verified"] is True
    assert artifact["structural_zero_policy"] == (
        "reference_declared_structural_zeros_must_be_exact_zero"
    )
    assert manifest["restricted_acceptance_policy"][
        "dynamics_artifact_reference_certification"
    ] == artifact
    execution = manifest["mps_execution"]
    diagnostics = execution["evaluator_only_diagnostics"]
    assert diagnostics["schema"] == (
        "error_coupling_simulator.frontend."
        "mcwf_mps_evaluator_only_diagnostics.v2"
    )
    assert diagnostics["visibility"] == (
        "evaluator_only_not_emitted_record_or_downstream_estimator_input"
    )
    assert diagnostics["level_record_semantics"] == (
        "schedule-ordered local measurement eigenlabel tuples: "
        "X columns use 0=|+>,1=|-> and preserve leaked level labels >=2; "
        "Z columns use computational local levels"
    )
    assert diagnostics["level_records"] == [[3, 0]]
    assert diagnostics["level_record_counts"] == [4]
    assert diagnostics["level_record_probabilities"] == [1.0]
    assert "jump_family_counts" in diagnostics
    assert not {
        "level_records",
        "level_record_counts",
        "level_record_probabilities",
    }.intersection(execution)
    assert "jump_family_counts" not in execution["jump_sampling"]


def test_dense_reference_rejects_noop_carrier(monkeypatch):
    """Identity carrier gates are rejected while the dense reference remains physical."""
    schedule = _ququart_transport_schedule()
    monkeypatch.setattr(
        execmod, "_hamiltonian_group_gates", _identity_group_gates(execmod._hamiltonian_group_gates)
    )
    manifest = _run(schedule)
    assert manifest["blocked_reason"].startswith(
        "mcwf_dynamics_artifact_group_mismatch:"
    )
    _assert_dynamics_artifact_blocked(
        manifest,
        reason=manifest["blocked_reason"],
    )


def test_dense_reference_rejects_corrupted_hamiltonian_term_builder(monkeypatch):
    """The oracle must not share the carrier's term-to-Hamiltonian builder."""

    real_builder = execmod._hamiltonian_matrix_for_term

    def _zero_hamiltonian(*args, **kwargs):
        return torch.zeros_like(real_builder(*args, **kwargs))

    monkeypatch.setattr(
        execmod,
        "_hamiltonian_matrix_for_term",
        _zero_hamiltonian,
    )
    corrupted = _run(_ququart_transport_schedule())

    _assert_dynamics_artifact_blocked(
        corrupted,
        reason=(
            "mcwf_dynamics_artifact_operator_mismatch:"
            "hamiltonian:CTRL_CZ"
        ),
    )


def test_dense_reference_rejects_corrupted_collapse_term_builder(monkeypatch):
    """The oracle must not share the carrier's term-to-collapse builder."""

    builder = CircuitBuilder(num_qubits=1)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.0,
            leak_seep_21_per_ns=1.0,
        )
    )
    builder.idle(0, duration_ns=2.0)
    builder.measure(0, key="mz", basis="Z")
    schedule = circuit_ir_to_substep_schedule(builder.build())
    real_builder = execmod._collapse_operator

    def _zero_collapse(*args, **kwargs):
        return torch.zeros_like(real_builder(*args, **kwargs))

    monkeypatch.setattr(execmod, "_collapse_operator", _zero_collapse)
    corrupted = axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        local_dims=[3],
        initial_levels=[2],
        microstep_count=20,
        trajectory_count=512,
        rng_seed=2903,
    )

    _assert_dynamics_artifact_blocked(
        corrupted,
        reason=(
            "mcwf_dynamics_artifact_operator_mismatch:collapse:LEAK_SEEP_21"
        ),
    )


def test_operator_guard_rejects_corrupted_phase_even_when_z_record_is_insensitive(
    monkeypatch,
):
    """A Z-eigenstate Record cannot hide a corrupted CTRL_Z operator."""

    builder = CircuitBuilder(num_qubits=1)
    builder.gate("Z", 0)
    builder.measure(0, key="mz", basis="Z")
    schedule = circuit_ir_to_substep_schedule(builder.build())
    real_builder = execmod._hamiltonian_matrix_for_term

    def _zero_hamiltonian(*args, **kwargs):
        return torch.zeros_like(real_builder(*args, **kwargs))

    monkeypatch.setattr(execmod, "_hamiltonian_matrix_for_term", _zero_hamiltonian)
    corrupted = axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        local_dims=[2],
        initial_levels=[0],
        trajectory_count=16,
        rng_seed=2297,
    )

    _assert_dynamics_artifact_blocked(
        corrupted,
        reason="mcwf_dynamics_artifact_operator_mismatch:hamiltonian:CTRL_Z",
    )


def test_operator_guard_rejects_corrupted_t2_on_dark_initial_state(monkeypatch):
    """A dark |0> trajectory cannot hide a corrupted nonzero T2 operator."""

    builder = CircuitBuilder(num_qubits=1)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.01,
            gamma_1_per_ns=0.0,
        )
    )
    builder.idle(0, duration_ns=1.0)
    builder.measure(0, key="mz", basis="Z")
    schedule = circuit_ir_to_substep_schedule(builder.build())
    real_builder = execmod._collapse_operator

    def _zero_collapse(*args, **kwargs):
        return torch.zeros_like(real_builder(*args, **kwargs))

    monkeypatch.setattr(execmod, "_collapse_operator", _zero_collapse)
    corrupted = axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        local_dims=[2],
        initial_levels=[0],
        trajectory_count=16,
        rng_seed=2299,
    )

    _assert_dynamics_artifact_blocked(
        corrupted,
        reason="mcwf_dynamics_artifact_operator_mismatch:collapse:T2",
    )


def test_operator_guard_rejects_subthreshold_structural_zero_pollution(monkeypatch):
    """Numerical tolerance must not turn leaked-sector structural zero into support."""

    builder = CircuitBuilder(num_qubits=1)
    builder.gate("Z", 0)
    builder.measure(0, key="mz", basis="Z")
    schedule = circuit_ir_to_substep_schedule(builder.build())
    real_builder = execmod._hamiltonian_matrix_for_term

    def _pollute_leaked_diagonal(*args, **kwargs):
        operator = real_builder(*args, **kwargs).clone()
        if str(args[0]["operator_family"]).upper() == "CTRL_Z":
            operator[2, 2] = 0.5 * 1.0e-12
        return operator

    monkeypatch.setattr(
        execmod,
        "_hamiltonian_matrix_for_term",
        _pollute_leaked_diagonal,
    )
    corrupted = axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        local_dims=[3],
        initial_levels=[0],
        trajectory_count=16,
        rng_seed=2301,
    )

    _assert_dynamics_artifact_blocked(
        corrupted,
        reason=(
            "mcwf_dynamics_artifact_structural_zero_mismatch:hamiltonian:CTRL_Z"
        ),
    )


def test_frozen_artifact_closes_stateful_builder_toctou(monkeypatch):
    """The validated tensor must be the exact one later consumed by trajectories."""

    builder = CircuitBuilder(num_qubits=1)
    builder.gate("Z", 0)
    builder.measure(0, key="mz", basis="Z")
    schedule = circuit_ir_to_substep_schedule(builder.build())
    real_builder = execmod._hamiltonian_matrix_for_term
    calls = 0

    def _stateful_builder(*args, **kwargs):
        nonlocal calls
        calls += 1
        honest = real_builder(*args, **kwargs)
        if calls <= 16:
            return torch.zeros_like(honest)
        return honest

    monkeypatch.setattr(
        execmod,
        "_hamiltonian_matrix_for_term",
        _stateful_builder,
    )
    corrupted = axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        local_dims=[2],
        initial_levels=[0],
        trajectory_count=16,
        rng_seed=2303,
    )

    assert calls == 1
    _assert_dynamics_artifact_blocked(
        corrupted,
        reason="mcwf_dynamics_artifact_operator_mismatch:hamiltonian:CTRL_Z",
    )


def test_frozen_artifact_rejects_state_insensitive_wrong_group_gate(monkeypatch):
    """A Z-eigenstate cannot hide an identity substituted after correct H construction."""

    builder = CircuitBuilder(num_qubits=1)
    builder.gate("Z", 0)
    builder.measure(0, key="mz", basis="Z")
    schedule = circuit_ir_to_substep_schedule(builder.build())
    real_grouping = execmod._hamiltonian_group_gates
    calls = 0

    def _identity_grouping(
        substep,
        *,
        dt_ns,
        local_dims,
        device,
        term_records=None,
    ):
        nonlocal calls
        calls += 1
        groups = real_grouping(
            substep,
            dt_ns=dt_ns,
            local_dims=local_dims,
            device=device,
            term_records=term_records,
        )
        return tuple(
            {
                **group,
                "gate": torch.eye(
                    int(group["gate"].shape[-1]),
                    dtype=torch.complex128,
                    device=device,
                ),
            }
            for group in groups
        )

    monkeypatch.setattr(execmod, "_hamiltonian_group_gates", _identity_grouping)
    corrupted = axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        local_dims=[2],
        initial_levels=[0],
        trajectory_count=16,
        rng_seed=2305,
    )

    assert calls == 1
    assert corrupted["blocked_reason"].startswith(
        "mcwf_dynamics_artifact_group_mismatch:"
    )
    _assert_dynamics_artifact_blocked(
        corrupted,
        reason=corrupted["blocked_reason"],
    )


def test_frozen_artifact_hash_seals_runtime_group_ledger_metadata(monkeypatch):
    """Post-cert mutation of runtime-consumed group metadata must fail closed."""

    builder = CircuitBuilder(num_qubits=1)
    builder.gate("Z", 0)
    builder.measure(0, key="mz", basis="Z")
    schedule = circuit_ir_to_substep_schedule(builder.build())
    real_execute = execmod._execute_sampled_mcwf_program

    def _mutate_after_reference_validation(*args, dynamics_artifacts, **kwargs):
        group = dynamics_artifacts[0]["hamiltonian_groups"][0]
        group["term"]["operator_family"] = "H_CLUSTER[FORGED]"
        return real_execute(
            *args,
            dynamics_artifacts=dynamics_artifacts,
            **kwargs,
        )

    monkeypatch.setattr(
        execmod,
        "_execute_sampled_mcwf_program",
        _mutate_after_reference_validation,
    )
    corrupted = axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        local_dims=[2],
        initial_levels=[0],
        trajectory_count=16,
        rng_seed=2306,
    )

    _assert_dynamics_artifact_blocked(
        corrupted,
        reason="mcwf_dynamics_artifact_integrity_mismatch:execution",
    )


def test_dense_reference_rejects_corrupted_x_basis_rotation(monkeypatch):
    """The NumPy X-projector oracle rejects an identity substituted for Torch H."""

    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key="mx", basis="X")
    schedule = circuit_ir_to_substep_schedule(builder.build())
    options = {
        "local_dims": [2],
        "initial_levels": [0],
        "trajectory_count": 128,
        "rng_seed": 2904,
    }

    honest = axis1_mcwf_mps_state_record_execution_manifest(schedule, **options)
    assert honest["verdict"] == "pass"

    monkeypatch.setattr(
        execmod,
        "_x_basis_rotation_local",
        lambda local_dim, *, device: torch.eye(
            int(local_dim),
            dtype=torch.complex128,
            device=device,
        ),
    )
    corrupted = axis1_mcwf_mps_state_record_execution_manifest(schedule, **options)

    assert corrupted["verdict"] == "fail"
    policy = corrupted["restricted_acceptance_policy"]
    certification = policy["dense_jointL_record_certification"]
    assert certification["comparison_object"] == (
        "measurement_basis_level_and_emitted_binary_record_populations"
    )
    assert certification["value"] == pytest.approx(0.5)
    assert certification["passed_gross"] is False
    assert policy["accepted_for_restricted_execution"] is False


def test_dense_reference_rejects_corrupted_public_level_to_bit_mapping(
    monkeypatch,
):
    """The label oracle must not hide a corrupted emitted binary Record."""

    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key="mz", basis="Z")
    schedule = circuit_ir_to_substep_schedule(builder.build())
    options = {
        "local_dims": [2],
        "initial_levels": [0],
        "trajectory_count": 32,
        "rng_seed": 2905,
    }

    monkeypatch.setattr(
        execmod,
        "_sample_level_bit",
        lambda *_args, **_kwargs: 1,
    )
    corrupted = axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        **options,
    )

    execution = corrupted["mps_execution"]
    diagnostics = execution["evaluator_only_diagnostics"]
    assert execution["measurement_records"] == [[1]]
    assert diagnostics["level_records"] == [[0]]
    assert corrupted["verdict"] == "fail"
    policy = corrupted["restricted_acceptance_policy"]
    certification = policy["dense_jointL_record_certification"]
    assert certification["comparison_object"] == (
        "measurement_basis_level_and_emitted_binary_record_populations"
    )
    assert certification["component_values"]["emitted_binary_record_tv"] == (
        pytest.approx(1.0)
    )
    assert certification["passed_gross"] is False
    assert policy["accepted_for_restricted_execution"] is False


@pytest.mark.parametrize("basis", ["X", "Z"])
def test_dense_reference_rejects_corrupted_multilevel_xz_readout_mapping(
    monkeypatch,
    basis,
):
    """Leaked X/Z labels must be checked against the emitted readout bit."""

    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key=f"m{basis.lower()}", basis=basis)
    schedule = circuit_ir_to_substep_schedule(builder.build())
    options = {
        "local_dims": [3],
        "initial_levels": [2],
        "leaked_readout_b": 0.0,
        "trajectory_count": 32,
        "rng_seed": 2906 if basis == "X" else 2907,
    }

    monkeypatch.setattr(
        execmod,
        "_sample_level_bit",
        lambda *_args, **_kwargs: 1,
    )
    corrupted = axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        **options,
    )

    execution = corrupted["mps_execution"]
    diagnostics = execution["evaluator_only_diagnostics"]
    assert execution["measurement_records"] == [[1]]
    assert diagnostics["level_records"] == [[2]]
    certification = corrupted["restricted_acceptance_policy"][
        "dense_jointL_record_certification"
    ]
    assert certification["component_values"] == {
        "declared_basis_eigenlabel_tv": pytest.approx(0.0),
        "emitted_binary_record_tv": pytest.approx(1.0),
    }
    assert certification["value"] == pytest.approx(1.0)
    assert certification["passed_gross"] is False
    assert corrupted["verdict"] == "fail"


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
    certification = _AccessTrackingDict(
        {
            "executed": True,
            "passed": True,
            "comparison_outcome_is_metric": True,
        }
    )
    with pytest.raises(KeyError):
        restricted_acceptance_policy(
            execution={
                "total_probability_residual": 0.0,
                "trajectory_sampling": {
                    "mode": "sampled_fixed_microstep_mcwf_trajectories",
                    "trajectory_count": 4,
                },
                "jump_sampling": {"probability_mass_residual_max": 0.0},
            },
            certification=certification,
            program={"requires_scalable_backend": False},
            rng_seed=904,
            trajectory_count=4,
            mass_residual_budget=0.1,
        )
    assert certification.accessed_keys[-1] == "passed_gross"
    assert certification.accessed_keys.count("passed_gross") == 1


def test_restricted_policy_requires_runtime_mass_residual_evidence():
    execution = _AccessTrackingDict(
        {
            "total_probability_residual": 0.0,
            "trajectory_sampling": {
                "mode": "sampled_fixed_microstep_mcwf_trajectories",
                "trajectory_count": 4,
            },
        }
    )
    with pytest.raises(KeyError):
        restricted_acceptance_policy(
            execution=execution,
            certification={
                "executed": True,
                "passed": True,
                "passed_gross": True,
                "comparison_outcome_is_metric": True,
            },
            program={"requires_scalable_backend": False},
            rng_seed=904,
            trajectory_count=4,
            mass_residual_budget=0.1,
        )
    assert execution.accessed_keys[-1] == "jump_sampling"
    assert execution.accessed_keys.count("jump_sampling") == 1


def _empty_hashed_program():
    return {
        "content_hash": "a" * 64,
        "requires_scalable_backend": False,
        "program": {"num_qubits": 1, "substeps": []},
    }


def _empty_artifact_hash(program):
    return certmod._mcwf_reference_dynamics_artifacts_content_hash(
        program,
        (),
        local_dims=(2,),
        microstep_count=1,
        finite_step_order="first_order",
    )


def _passing_empty_artifact_packet():
    program = _empty_hashed_program()
    packet = certmod.mcwf_dynamics_artifact_reference_certification(
        program,
        dynamics_artifacts=(),
        dynamics_artifact_content_hash=_empty_artifact_hash(program),
        local_dims=(2,),
        microstep_count=1,
        finite_step_order="first_order",
        post_execution_integrity_verified=True,
    )
    return program, packet


def _rehash_artifact_packet(packet):
    packet["content_hash"] = certmod._mcwf_reference_packet_content_hash(packet)


def test_public_artifact_packet_recomputes_instead_of_trusting_supplied_hash():
    program = _empty_hashed_program()
    wrong_hash = "0" * 64
    assert wrong_hash != _empty_artifact_hash(program)

    failed = certmod.mcwf_dynamics_artifact_reference_certification(
        program,
        dynamics_artifacts=(),
        dynamics_artifact_content_hash=wrong_hash,
        local_dims=(2,),
        microstep_count=1,
        finite_step_order="first_order",
        post_execution_integrity_verified=False,
    )
    assert failed["passed"] is False
    assert failed["reason"] == "mcwf_dynamics_artifact_content_hash_mismatch"
    assert failed["dynamics_artifact_content_hash"] == _empty_artifact_hash(
        program
    )

    with pytest.raises(
        ValueError,
        match="post-execution artifact integrity cannot pass",
    ):
        certmod.mcwf_dynamics_artifact_reference_certification(
            program,
            dynamics_artifacts=(),
            dynamics_artifact_content_hash=wrong_hash,
            local_dims=(2,),
            microstep_count=1,
            finite_step_order="first_order",
            post_execution_integrity_verified=True,
        )


def test_artifact_packet_builder_rejects_invalid_hash_states(monkeypatch):
    program = _empty_hashed_program()
    with pytest.raises(ValueError, match="requires a sha256 content hash"):
        certmod.mcwf_dynamics_artifact_reference_certification(
            program,
            dynamics_artifacts=(),
            dynamics_artifact_content_hash="not-a-hash",
            local_dims=(2,),
            microstep_count=1,
            finite_step_order="first_order",
            post_execution_integrity_verified=False,
        )
    with pytest.raises(ValueError, match="non-executed.*cannot carry"):
        certmod.mcwf_dynamics_artifact_reference_certification(
            program,
            dynamics_artifacts=None,
            dynamics_artifact_content_hash="0" * 64,
            local_dims=(2,),
            microstep_count=1,
            finite_step_order="first_order",
            post_execution_integrity_verified=False,
        )

    monkeypatch.setattr(
        certmod,
        "_mcwf_reference_dynamics_artifacts_content_hash",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    unavailable = certmod.mcwf_dynamics_artifact_reference_certification(
        program,
        dynamics_artifacts=(),
        dynamics_artifact_content_hash="0" * 64,
        local_dims=(2,),
        microstep_count=1,
        finite_step_order="first_order",
        post_execution_integrity_verified=False,
    )
    assert unavailable["passed"] is False
    assert unavailable["reason"] == (
        "mcwf_dynamics_artifact_content_hash_unavailable:RuntimeError"
    )


def test_artifact_packet_binds_transitive_control_and_selection_sources():
    package_root = Path(certmod.__file__).resolve().parents[1]
    expected_paths = {
        "reference_operator_source_sha256": (
            Path(certmod.__file__).with_name("mcwf_operator_reference.py")
        ),
        "reference_certification_source_sha256": Path(certmod.__file__),
        "carrier_operator_source_sha256": (
            package_root / "frontend" / "axis1_mcwf_mps_execution.py"
        ),
        "carrier_control_generator_source_sha256": (
            package_root / "frontend" / "axis1_ideal_controls.py"
        ),
        "carrier_selection_source_sha256": (
            package_root / "frontend" / "axis1_selection.py"
        ),
    }
    expected_hashes = {
        field: hashlib.sha256(path.read_bytes()).hexdigest()
        for field, path in expected_paths.items()
    }

    assert certmod._mcwf_reference_source_hashes() == expected_hashes


@pytest.mark.parametrize(
    "field",
    [
        "carrier_control_generator_source_sha256",
        "carrier_selection_source_sha256",
    ],
)
def test_artifact_packet_validator_rejects_transitive_source_drift(field):
    program, packet = _passing_empty_artifact_packet()
    packet[field] = "0" * 64
    _rehash_artifact_packet(packet)

    with pytest.raises(ValueError, match=f"{field} is not current"):
        certmod.validate_mcwf_dynamics_artifact_reference_certification(
            packet,
            program=program,
            local_dims=(2,),
            microstep_count=1,
            finite_step_order="first_order",
        )


def test_artifact_packet_validator_rejects_non_mapping_and_field_drift():
    program, packet = _passing_empty_artifact_packet()
    assert certmod.validate_mcwf_dynamics_artifact_reference_certification(
        packet,
        program=program,
        local_dims=(2,),
        microstep_count=1,
        finite_step_order="first_order",
    ) is True
    with pytest.raises(TypeError, match="must be a mapping"):
        certmod.validate_mcwf_dynamics_artifact_reference_certification(
            [],
            program=program,
            local_dims=(2,),
            microstep_count=1,
            finite_step_order="first_order",
        )
    missing = copy.deepcopy(packet)
    missing.pop("reason")
    with pytest.raises(ValueError, match="fields must be exact"):
        certmod.validate_mcwf_dynamics_artifact_reference_certification(
            missing,
            program=program,
            local_dims=(2,),
            microstep_count=1,
            finite_step_order="first_order",
        )
    stale_schema = copy.deepcopy(packet)
    stale_schema["schema"] = "stale"
    with pytest.raises(ValueError, match="schema is stale"):
        certmod.validate_mcwf_dynamics_artifact_reference_certification(
            stale_schema,
            program=program,
            local_dims=(2,),
            microstep_count=1,
            finite_step_order="first_order",
        )
    bad_hash = copy.deepcopy(packet)
    bad_hash["content_hash"] = "0" * 64
    with pytest.raises(ValueError, match="content hash is invalid"):
        certmod.validate_mcwf_dynamics_artifact_reference_certification(
            bad_hash,
            program=program,
            local_dims=(2,),
            microstep_count=1,
            finite_step_order="first_order",
        )


@pytest.mark.parametrize(
    ("case", "match"),
    [
        ("bool_type", "executed must be bool"),
        ("status", "status is inconsistent"),
        ("passing_reason", "passing artifact certification state"),
        ("missing_reason", "non-passing artifact certification requires"),
        ("artifact_hash", "executed artifact certification hash"),
        ("carrier_hash", "carrier program hash is stale"),
        ("local_dims", "local_dims are stale"),
        ("microstep_count", "microstep_count is stale"),
        ("finite_step_order", "finite_step_order is stale"),
        ("substep_count", "substep_count is stale"),
        ("hamiltonian_count", "hamiltonian_term_count is stale"),
        ("collapse_count", "collapse_term_count is stale"),
        ("group_count_type", "group count is invalid"),
        ("group_count_negative", "group count is invalid"),
        ("static_value", "epistemic_class is not current"),
    ],
)
def test_artifact_packet_validator_rejects_authenticated_state_drift(case, match):
    program, packet = _passing_empty_artifact_packet()
    if case == "bool_type":
        packet["executed"] = 1
    elif case == "status":
        packet["status"] = "failed"
    elif case == "passing_reason":
        packet["reason"] = "forged reason"
    elif case == "missing_reason":
        packet["passed"] = False
        packet["status"] = "failed"
        packet["reason"] = ""
    elif case == "artifact_hash":
        packet["dynamics_artifact_content_hash"] = "bad"
    elif case == "carrier_hash":
        packet["carrier_program_content_hash"] = "b" * 64
    elif case == "local_dims":
        packet["local_dims"] = [3]
    elif case == "microstep_count":
        packet["microstep_count"] = 2
    elif case == "finite_step_order":
        packet["finite_step_order"] = "strang_second_order"
    elif case == "substep_count":
        packet["substep_count"] = 1
    elif case == "hamiltonian_count":
        packet["hamiltonian_term_count"] = 1
    elif case == "collapse_count":
        packet["collapse_term_count"] = 1
    elif case == "group_count_type":
        packet["hamiltonian_group_count"] = 0.0
    elif case == "group_count_negative":
        packet["hamiltonian_group_count"] = -1
    elif case == "static_value":
        packet["epistemic_class"] = "stale"
    else:  # pragma: no cover - parametrization is exhaustive.
        raise AssertionError(case)
    _rehash_artifact_packet(packet)
    with pytest.raises((TypeError, ValueError), match=match):
        certmod.validate_mcwf_dynamics_artifact_reference_certification(
            packet,
            program=program,
            local_dims=(2,),
            microstep_count=1,
            finite_step_order="first_order",
        )


def test_artifact_packet_validator_rejects_invalid_program_and_failed_states():
    program, packet = _passing_empty_artifact_packet()
    invalid_program = copy.deepcopy(program)
    invalid_program["content_hash"] = "bad"
    with pytest.raises(ValueError, match="carrier program content hash must be sha256"):
        certmod.validate_mcwf_dynamics_artifact_reference_certification(
            packet,
            program=invalid_program,
            local_dims=(2,),
            microstep_count=1,
            finite_step_order="first_order",
        )

    not_executed = certmod.mcwf_dynamics_artifact_reference_certification(
        program,
        dynamics_artifacts=None,
        dynamics_artifact_content_hash=None,
        local_dims=(2,),
        microstep_count=1,
        finite_step_order="first_order",
        post_execution_integrity_verified=False,
        not_executed_reason="blocked",
    )
    invalid_nonexecuted_hash = copy.deepcopy(not_executed)
    invalid_nonexecuted_hash["dynamics_artifact_content_hash"] = "0" * 64
    _rehash_artifact_packet(invalid_nonexecuted_hash)
    with pytest.raises(ValueError, match="hash must be None"):
        certmod.validate_mcwf_dynamics_artifact_reference_certification(
            invalid_nonexecuted_hash,
            program=program,
            local_dims=(2,),
            microstep_count=1,
            finite_step_order="first_order",
        )

    invalid_post = copy.deepcopy(not_executed)
    invalid_post["post_execution_integrity_verified"] = True
    _rehash_artifact_packet(invalid_post)
    with pytest.raises(ValueError, match="post-execution integrity cannot pass"):
        certmod.validate_mcwf_dynamics_artifact_reference_certification(
            invalid_post,
            program=program,
            local_dims=(2,),
            microstep_count=1,
            finite_step_order="first_order",
        )


def test_direct_manifest_fail_closes_artifact_compile_and_preexecution_hash_drift(
    monkeypatch,
):
    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key="mz", basis="Z")
    schedule = circuit_ir_to_substep_schedule(builder.build())
    options = {
        "local_dims": [2],
        "initial_levels": [0],
        "trajectory_count": 4,
        "rng_seed": 3117,
    }

    monkeypatch.setattr(
        execmod,
        "_compile_mcwf_dynamics_artifacts",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    compile_blocked = axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        **options,
    )
    assert compile_blocked["blocked_reason"] == (
        "mcwf_dynamics_artifact_compile_unavailable:RuntimeError"
    )

    monkeypatch.undo()
    real_hash = execmod._mcwf_dynamics_artifacts_content_hash
    calls = 0

    def _drifting_hash(*args, **kwargs):
        nonlocal calls
        calls += 1
        honest = real_hash(*args, **kwargs)
        return honest if calls == 1 else ("0" * 64)

    monkeypatch.setattr(
        execmod,
        "_mcwf_dynamics_artifacts_content_hash",
        _drifting_hash,
    )
    hash_blocked = axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        **options,
    )
    assert hash_blocked["blocked_reason"] == (
        "mcwf_dynamics_artifact_integrity_mismatch:reference_validation"
    )
