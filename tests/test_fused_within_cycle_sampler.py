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
