"""CPU/mock gates for the active fused within-cycle execution seam."""

from __future__ import annotations

from types import MethodType

import pytest
import torch


def _schedule():
    from error_coupling_simulator.frontend.xzzx_parser import (
        Stabilizer,
        WithinCycleStream,
        XZZXSchedule,
    )

    return XZZXSchedule(
        n_data=9,
        data_indices=tuple(range(9)),
        data_coords=tuple((float(site), 0.0) for site in range(9)),
        stabilizers=(Stabilizer(0, {0: "Z"}, 20, (0.0, 0.0)),),
        logical={0: "Z"},
        logical_kind="Z",
        data_init_x=frozenset(),
        surplus_dropped=(),
        rounds=1,
        within_cycle_streams=tuple(
            WithinCycleStream(
                pos=site,
                circuit_id=site,
                tokens=("M",),
                n_cz=0,
                cz_layers=(),
                h_pattern=(0, 0, 0),
            )
            for site in range(9)
        ),
        source="synthetic-nine-site",
    )


def _fake_physics(sampler) -> None:
    def build_leak(_self, _spec):
        return torch.eye(3, dtype=torch.complex128).unsqueeze(0), {
            "cptp_residual": 0.0,
            "compose_residual": 0.0,
            "construction_dtype": "c128",
        }

    def build_codestate(_self, _schedule, logical_m):
        state = torch.zeros(3 ** 9, dtype=torch.complex128)
        state[int(logical_m)] = 1.0
        return state, {
            "worst_S_residual": 0.0,
            "worst_L_residual": 0.0,
            "construction_dtype": "c128",
        }

    sampler.build_within_cycle_leak = MethodType(build_leak, sampler)
    sampler.build_codestate = MethodType(build_codestate, sampler)


@pytest.mark.parametrize(
    ("purpose", "dtype", "real_dtype", "eligibility"),
    [
        ("optimization", "c64", torch.float32, "screening_only"),
        ("final", "c128", torch.float64, "c128_candidate"),
        ("certification", "c128", torch.float64, "c128_candidate"),
    ],
)
def test_active_fused_sampler_executes_the_purpose_bound_precision(
    monkeypatch,
    purpose: str,
    dtype: str,
    real_dtype: torch.dtype,
    eligibility: str,
) -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader
    from error_coupling_simulator.carrier.within_cycle import (
        FusedWithinCycleSampler,
        RunSpec,
    )

    captured = {}

    def fake_kernel(**kwargs):
        captured.update(kwargs)
        n_shots = int(kwargs["N"])
        bits = int(kwargs["R"])
        return (
            torch.zeros((n_shots, (bits + 7) // 8 + 1), dtype=torch.uint8),
            torch.zeros(n_shots, dtype=real_dtype),
        )

    monkeypatch.setattr(sv_traj_d3_loader, "sv_traj_d3_wc", fake_kernel)
    sampler = FusedWithinCycleSampler("cpu")
    _fake_physics(sampler)
    spec = RunSpec(
        circuit_path="synthetic.stim",
        N=2,
        R=1,
        run_purpose=purpose,
        dtype=dtype,
    )
    urandom = torch.full((2, 3), 0.25, dtype=torch.float64)

    batch = sampler.sample(
        spec,
        schedule=_schedule(),
        urandom=urandom,
        urandom_stride=3,
    )

    expected_complex = (
        torch.complex64 if dtype == "c64" else torch.complex128)
    assert captured["dtype"] == dtype
    assert captured["codestate"].dtype == expected_complex
    assert captured["gate_unitaries"].dtype == expected_complex
    assert captured["leak_kraus"].dtype == expected_complex
    assert captured["urandom"].dtype == real_dtype
    assert batch.header["run_purpose"] == purpose
    assert batch.header["evidence_eligibility"] == eligibility
    assert batch.header["physics_construction_dtype"] == "c128"
    assert batch.header["kernel_entrypoint"] == "sv_traj_d3_wc"
    assert batch.provenance["precision_policy"].startswith("optimization_c64")
    assert batch.to_record_batch().det.shape == (2, 1)


def test_final_runner_calls_evidence_header_guard_before_kernel(monkeypatch) -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader
    from error_coupling_simulator.carrier.within_cycle import (
        FusedWithinCycleSampler,
        RunSpec,
    )

    class CorruptHeaderSampler(FusedWithinCycleSampler):
        def build_header(self, spec, marshalled, schedule):
            header = super().build_header(spec, marshalled, schedule)
            header.pop("precision_policy")
            return header

    called = False

    def fake_kernel(**_kwargs):
        nonlocal called
        called = True
        raise AssertionError("kernel must not run after a corrupt final header")

    monkeypatch.setattr(sv_traj_d3_loader, "sv_traj_d3_wc", fake_kernel)
    sampler = CorruptHeaderSampler("cpu")
    _fake_physics(sampler)
    spec = RunSpec(
        circuit_path="synthetic.stim",
        N=1,
        R=1,
        run_purpose="final",
        dtype="c128",
    )

    with pytest.raises(ValueError, match="precision_policy"):
        sampler.sample(spec, schedule=_schedule())
    assert called is False


def test_evidence_conversion_rejects_screening_and_purpose_mismatch(
    monkeypatch,
) -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader
    from error_coupling_simulator.carrier.within_cycle import (
        FusedWithinCycleSampler,
        RunSpec,
        c128_evidence_record_batch,
    )

    monkeypatch.setattr(
        sv_traj_d3_loader,
        "sv_traj_d3_wc",
        lambda **kwargs: (
            torch.zeros((int(kwargs["N"]), 2), dtype=torch.uint8),
            torch.zeros(int(kwargs["N"]), dtype=torch.float32),
        ),
    )
    sampler = FusedWithinCycleSampler("cpu")
    _fake_physics(sampler)
    screening = sampler.sample(
        RunSpec(
            circuit_path="synthetic.stim",
            N=1,
            R=1,
            run_purpose="optimization",
            dtype="c64",
        ),
        schedule=_schedule(),
    )
    assert screening.to_record_batch().n_shots == 1
    with pytest.raises(ValueError, match="c128 evidence"):
        c128_evidence_record_batch(
            screening, expected_purpose="certification")

    final_header = dict(screening.header)
    final_header.update({
        "run_purpose": "final",
        "dtype": "c128",
        "evidence_eligibility": "c128_candidate",
    })
    final = type(screening)(
        header=final_header,
        path=None,
        header_path=None,
        n_shots=screening.n_shots,
        syndrome_bits_per_shot=screening.syndrome_bits_per_shot,
        shots=screening.shots,
    )
    with pytest.raises(ValueError, match="run-purpose mismatch"):
        c128_evidence_record_batch(
            final, expected_purpose="certification")
    final_record = c128_evidence_record_batch(
        final, expected_purpose="final")
    assert final_record.n_shots == 1
    assert final_record.provenance["run_purpose"] == "final"
    assert final_record.provenance["dtype"] == "c128"
    assert final_record.provenance["precision_policy"].startswith(
        "optimization_c64")
    assert final_record.provenance["evidence_eligibility"] == "c128_candidate"


def test_execute_marshaled_rejects_precast_c64_as_a_certified_base() -> None:
    from error_coupling_simulator.carrier.within_cycle import (
        FusedWithinCycleSampler,
        RunSpec,
    )

    sampler = FusedWithinCycleSampler("cpu")
    leak = torch.eye(3, dtype=torch.complex64).unsqueeze(0)
    marshalled = sampler.marshal_within_cycle(_schedule(), leak, R=1)
    spec = RunSpec(
        circuit_path="synthetic.stim",
        N=1,
        R=1,
        run_purpose="optimization",
        dtype="c64",
    )
    state = torch.zeros(3 ** 9, dtype=torch.complex128)

    with pytest.raises(ValueError, match="certified base leak_kraus.*complex128"):
        sampler.execute_marshaled(
            spec,
            schedule=_schedule(),
            marshalled=marshalled,
            codestate=state,
        )


def test_fused_sampler_packed_output_shape_is_fail_closed(monkeypatch) -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader
    from error_coupling_simulator.carrier.within_cycle import (
        FusedWithinCycleSampler,
        RunSpec,
    )

    monkeypatch.setattr(
        sv_traj_d3_loader,
        "sv_traj_d3_wc",
        lambda **_kwargs: (
            torch.zeros((1, 99), dtype=torch.uint8),
            torch.zeros(1, dtype=torch.float32),
        ),
    )
    sampler = FusedWithinCycleSampler("cpu")
    _fake_physics(sampler)
    spec = RunSpec(
        circuit_path="synthetic.stim",
        N=1,
        R=1,
        run_purpose="optimization",
        dtype="c64",
    )

    with pytest.raises(ValueError, match="packed output shape mismatch"):
        sampler.sample(spec, schedule=_schedule())


def _frame_schedule(logical: dict[int, str], *, rounds: int):
    """Nine-site schedule whose every position carries a post-measure Y echo."""

    from error_coupling_simulator.frontend.xzzx_parser import (
        Stabilizer,
        WithinCycleStream,
        XZZXSchedule,
    )

    return XZZXSchedule(
        n_data=9,
        data_indices=tuple(range(9)),
        data_coords=tuple((float(site), 0.0) for site in range(9)),
        stabilizers=(Stabilizer(0, {0: "Z", 1: "Z"}, 20, (0.0, 0.0)),),
        logical=dict(logical),
        logical_kind="Z",
        data_init_x=frozenset(),
        surplus_dropped=(),
        rounds=rounds,
        within_cycle_streams=tuple(
            WithinCycleStream(
                pos=site,
                circuit_id=site,
                tokens=("M", "Y"),
                n_cz=0,
                cz_layers=(),
                h_pattern=(0, 0, 0),
            )
            for site in range(9)
        ),
        source="synthetic-nine-site-echo",
    )


@pytest.mark.parametrize(
    ("logical", "rounds", "expected"),
    [
        # Weight-3 logical: the transversal Y echo anticommutes on all three
        # support sites, so each non-terminal round contributes (-1)**3 = -1.
        ({0: "Z", 2: "Z", 5: "Z"}, 1, 0),
        ({0: "Z", 2: "Z", 5: "Z"}, 2, 1),
        ({0: "Z", 2: "Z", 5: "Z"}, 3, 0),
        ({0: "Z", 2: "Z", 5: "Z"}, 4, 1),
        # Even-weight logical: the echo is inert on the logical exactly as it is
        # inert on the even-weight stabilizers.
        ({0: "Z", 2: "Z"}, 2, 0),
        ({0: "Z", 2: "Z"}, 5, 0),
        # X support anticommutes with Y just as Z support does.
        ({0: "X", 2: "X", 5: "X"}, 2, 1),
    ],
)
def test_marshal_derives_transversal_echo_parity_on_the_logical(
    logical, rounds, expected
) -> None:
    # The per-round transversal Y echo is physically applied (it symmetrises the
    # asymmetric energy-relaxation error), so it cannot be removed -- but it
    # anticommutes with an odd-weight logical and must therefore be divided back
    # out of the emitted observable. Deriving the parity from the ops actually
    # emitted keeps this correct if the echo or the logical support ever changes.
    from error_coupling_simulator.carrier.within_cycle import (
        WithinCycleScheduleHost,
    )

    host = WithinCycleScheduleHost("cpu")
    plan = host.marshal_within_cycle(
        _frame_schedule(logical, rounds=rounds),
        torch.zeros((1, 3, 3), dtype=torch.complex128),
        R=rounds,
    )

    assert plan.frame_logical_parity == expected


@pytest.mark.parametrize("pauli", ["Y", "I", "z z", ""])
def test_marshal_rejects_a_logical_pauli_outside_the_measured_bases(pauli) -> None:
    # Measurement is X/Z only, so the logical operator is too. Before this check
    # an unrecognised Pauli fell through `== "X"` and reached the kernel marshalled
    # as Z -- a silent basis change, not an error. The stabilizer loop has always
    # rejected the same input; this closes the asymmetry.
    from error_coupling_simulator.carrier.within_cycle import (
        WithinCycleScheduleHost,
    )

    host = WithinCycleScheduleHost("cpu")

    with pytest.raises(ValueError, match="non-X/Z pauli"):
        host.marshal_within_cycle(
            _frame_schedule({0: "Z", 2: pauli, 5: "Z"}, rounds=2),
            torch.zeros((1, 3, 3), dtype=torch.complex128),
            R=2,
        )


def _real_d3_frame_inputs():
    """The real d3 patch, its noiseless codestate, and a marshalled plan, on CPU."""

    pytest.importorskip("numpy")
    from error_coupling_simulator.carrier.exact.qutrit_dm import QutritDM
    from error_coupling_simulator.carrier.within_cycle import (
        WithinCycleScheduleHost,
    )
    from error_coupling_simulator.frontend import experiments as experiments_mod

    try:
        schedule = experiments_mod.load_xzzx_d3(with_interior_streams=True)
    except (FileNotFoundError, OSError) as exc:
        pytest.skip(f"portable d3 dataset unavailable: {exc}")

    host = WithinCycleScheduleHost("cpu")
    marshalled = host.marshal_within_cycle(
        schedule, torch.zeros((1, 3, 3), dtype=torch.complex128), R=4
    )
    engine = QutritDM(int(schedule.n_data), device=torch.device("cpu"))
    engine.set_code(
        stabilizers=schedule.stab_paulis(),
        logical_z=dict(schedule.logical),
        logical_x=None,
    )
    codestate = engine._codestate_vector(0)
    codestate = codestate / torch.linalg.vector_norm(codestate)
    return host, schedule, marshalled, codestate.contiguous()


def test_frame_cross_check_agrees_with_the_noiseless_reference() -> None:
    host, schedule, marshalled, codestate = _real_d3_frame_inputs()

    report = host.verify_frame_logical_parity(
        schedule, codestate=codestate, marshalled=marshalled, logical_m=0
    )

    assert report["derived_parity"] == report["measured_parity"]
    assert report["frame_gates_applied"] == 3 * int(schedule.n_data)
    assert abs(abs(report["logical_expectation_framed"]) - 1.0) < 1e-9


def test_frame_cross_check_fires_on_a_derived_parity_that_is_wrong() -> None:
    # The combinatorial derivation is only sound while the frame is a clean sign
    # on a leakage-free reference. If it ever disagrees with what the frame
    # actually does, the run must stop rather than ship the constant.
    from dataclasses import replace as dataclass_replace

    host, schedule, marshalled, codestate = _real_d3_frame_inputs()
    tampered = dataclass_replace(
        marshalled,
        frame_logical_parity=1 - int(marshalled.frame_logical_parity),
    )

    with pytest.raises(RuntimeError, match="disagrees with the noiseless reference"):
        host.verify_frame_logical_parity(
            schedule, codestate=codestate, marshalled=tampered, logical_m=0
        )


def test_frame_cross_check_refuses_a_frame_that_is_not_a_deterministic_sign() -> None:
    # An echo that does not leave the logical in a deterministic sector cannot be
    # described by any parity bit. Swapping one Y for an H makes the frame map the
    # Z logical onto X, so <L> collapses to 0 -- the coherent analogue of what
    # leakage does, and the case the exact leg already refuses.
    from dataclasses import replace as dataclass_replace

    from error_coupling_simulator.carrier.within_cycle import SV_GATE_IDS

    host, schedule, marshalled, codestate = _real_d3_frame_inputs()
    op_uid = marshalled.op_uid.clone()
    first_post = int(marshalled.round_op_ptr[1])
    op_uid[first_post] = SV_GATE_IDS["H"]
    tampered = dataclass_replace(marshalled, op_uid=op_uid)

    with pytest.raises(RuntimeError, match="deterministic logical sector"):
        host.verify_frame_logical_parity(
            schedule, codestate=codestate, marshalled=tampered, logical_m=0
        )
