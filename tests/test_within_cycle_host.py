"""CPU structural gates for the package-local within-cycle carrier host."""

from __future__ import annotations

import pytest
import torch


def _two_site_schedule():
    from error_coupling_simulator.frontend.xzzx_parser import (
        Stabilizer,
        WithinCycleStream,
        XZZXSchedule,
    )

    streams = (
        WithinCycleStream(
            pos=0,
            circuit_id=10,
            tokens=("H", "LEAK", "H", "X", "LEAK", "M", "Y"),
            n_cz=2,
            cz_layers=(1, 3),
            h_pattern=(1, 1, 0),
        ),
        WithinCycleStream(
            pos=1,
            circuit_id=11,
            tokens=("LEAK", "H", "X", "H", "LEAK", "M", "Y"),
            n_cz=2,
            cz_layers=(1, 4),
            h_pattern=(0, 1, 1),
        ),
    )
    return XZZXSchedule(
        n_data=2,
        data_indices=(10, 11),
        data_coords=((0.0, 0.0), (1.0, 0.0)),
        stabilizers=(
            Stabilizer(0, {0: "X", 1: "X"}, 20, (0.5, 0.0)),
            Stabilizer(1, {1: "Z"}, 21, (1.5, 0.0)),
        ),
        logical={1: "X"},
        logical_kind="X",
        data_init_x=frozenset(),
        surplus_dropped=(),
        rounds=2,
        within_cycle_streams=streams,
        source="synthetic-two-site",
    )


def test_within_cycle_quarter_slice_is_independently_pinned() -> None:
    from error_coupling_simulator.carrier.within_cycle import WC_LEAK_FRAC

    assert WC_LEAK_FRAC == 0.25


def test_within_cycle_physics_builder_rejects_cpu_device() -> None:
    from error_coupling_simulator.carrier.within_cycle import (
        RunSpec,
        WithinCycleScheduleHost,
    )

    host = WithinCycleScheduleHost(device="cpu")
    spec = RunSpec(circuit_path="unused.stim", N=1, theta=0.1)

    with pytest.raises(RuntimeError, match="GPU-only.*device.*cuda"):
        host.build_within_cycle_leak(spec)


def test_within_cycle_marshalling_matches_explicit_golden_layout() -> None:
    from error_coupling_simulator.carrier.within_cycle import (
        CDTYPE,
        SV_GATE_IDS,
        WithinCycleScheduleHost,
    )
    schedule = _two_site_schedule()
    leak = torch.eye(3, dtype=CDTYPE).unsqueeze(0)
    active = WithinCycleScheduleHost(device="cpu").marshal_within_cycle(
        schedule, leak, R=2)

    expected_kind = [
        0, 1, 0, 0, 1,
        1, 0, 0, 0, 1,
        0, 0,
        0, 1, 0, 0, 1,
        1, 0, 0, 0, 1,
    ]
    expected_uid = [
        SV_GATE_IDS["H"], 0, SV_GATE_IDS["H"], SV_GATE_IDS["X"], 0,
        0, SV_GATE_IDS["H"], SV_GATE_IDS["X"], SV_GATE_IDS["H"], 0,
        SV_GATE_IDS["Y"], SV_GATE_IDS["Y"],
        SV_GATE_IDS["H"], 0, SV_GATE_IDS["H"], SV_GATE_IDS["X"], 0,
        0, SV_GATE_IDS["H"], SV_GATE_IDS["X"], SV_GATE_IDS["H"], 0,
    ]
    expected_site = [
        0, 0, 0, 0, 0,
        1, 1, 1, 1, 1,
        0, 1,
        0, 0, 0, 0, 0,
        1, 1, 1, 1, 1,
    ]

    assert active.round_op_ptr.tolist() == [0, 10, 12, 22, 22]
    assert active.op_kind.tolist() == expected_kind
    assert active.op_uid.tolist() == expected_uid
    assert active.op_site.tolist() == expected_site
    assert active.stab_supp.tolist() == [[0, 1], [1, 0]]
    assert active.stab_supp_isx.tolist() == [[1, 1], [0, 0]]
    assert active.stab_supp_len.tolist() == [2, 1]
    assert active.log_supp.tolist() == [1]
    assert active.log_supp_isx.tolist() == [1]
    assert active.streams_by_pos == {
        0: ("H", "LEAK", "H", "X", "LEAK", "M", "Y"),
        1: ("LEAK", "H", "X", "H", "LEAK", "M", "Y"),
    }
    assert active.n_cz_by_pos == {0: 2, 1: 2}

    integer_tensor_fields = (
        "round_op_ptr", "op_kind", "op_uid", "op_site", "stab_supp",
        "stab_supp_isx", "stab_supp_len", "log_supp", "log_supp_isx",
    )
    for field in integer_tensor_fields:
        actual = getattr(active, field)
        assert actual.dtype == torch.int32
        assert actual.is_contiguous()
    assert active.leak_kraus.dtype == torch.complex128
    assert active.leak_kraus.is_contiguous()
    assert active.gate_unitaries.dtype == torch.complex128
    assert active.gate_unitaries.is_contiguous()


def test_peps_sampler_requires_frontend_compiled_schedule() -> None:
    from error_coupling_simulator.carrier.peps.trajectory import (
        PepsSampler,
        TruncationPolicy,
    )
    from error_coupling_simulator.carrier.within_cycle import RunSpec

    sampler = PepsSampler(device="cpu")
    spec = RunSpec(circuit_path="unused.stim", N=1)

    with pytest.raises(ValueError, match="explicit compiled schedule"):
        sampler.sample(spec, sched=None, policy=TruncationPolicy("lossless"))


def test_peps_sampler_rejects_c64_metadata_mismatch_before_execution() -> None:
    from error_coupling_simulator.carrier.peps.trajectory import (
        PepsSampler,
        TruncationPolicy,
    )
    from error_coupling_simulator.carrier.within_cycle import RunSpec

    sampler = PepsSampler(device="cpu")
    spec = RunSpec(circuit_path="unused.stim", N=1, dtype="c64")

    with pytest.raises(ValueError, match="complex128.*c128"):
        sampler.sample(
            spec,
            sched=_two_site_schedule(),
            policy=TruncationPolicy("lossless"),
        )


def test_peps_sampler_rejects_cpu_device_even_when_gpu_is_visible() -> None:
    from error_coupling_simulator.carrier.peps.trajectory import (
        PepsSampler,
        TruncationPolicy,
    )
    from error_coupling_simulator.carrier.within_cycle import RunSpec

    sampler = PepsSampler(device="cpu")
    spec = RunSpec(circuit_path="unused.stim", N=1, dtype="c128")

    with pytest.raises(RuntimeError, match="GPU-only.*device.*cuda"):
        sampler.sample(
            spec,
            sched=_two_site_schedule(),
            policy=TruncationPolicy("lossless"),
        )


def test_within_cycle_header_declares_current_packed_record_contract() -> None:
    from error_coupling_simulator.carrier.records import (
        PACKED_DETECTOR_INITIAL_PRIOR,
        PACKED_SHOT_SCHEMA,
        PACKED_SYNDROME_LAYOUT,
    )
    from error_coupling_simulator.carrier.within_cycle import (
        CDTYPE,
        RunSpec,
        WithinCycleScheduleHost,
    )
    schedule = _two_site_schedule()
    spec = RunSpec(
        circuit_path="synthetic.stim",
        metadata_path="synthetic.json",
        m=1,
        theta=0.2,
        g_seep=0.1,
        g_heat=0.01,
        arm="B1",
        b=0.75,
        readout_conv="half",
        N=7,
        base_seed=13,
        W=4,
        R=2,
    )
    leak = torch.eye(3, dtype=CDTYPE).unsqueeze(0)
    active_host = WithinCycleScheduleHost(device="cpu")
    marshalled = active_host.marshal_within_cycle(schedule, leak, R=2)

    active_header = active_host.build_header(spec, marshalled, schedule)
    build_identity = active_header["build_identity"]
    assert active_header["format"] == PACKED_SHOT_SCHEMA
    assert active_header["syndrome_layout"] == PACKED_SYNDROME_LAYOUT
    assert active_header["detector_initial_prior"] == PACKED_DETECTOR_INITIAL_PRIOR
    assert active_header["package_version"] == build_identity["version"]
    assert (
        active_header["package_tree_sha256"]
        == build_identity["package_tree_sha256"]
    )

    assert active_header["N"] == 7
    assert active_header["R"] == 2
    assert active_header["n_stab"] == 2
    assert active_header["syndrome_bits_per_shot"] == 4
    assert active_header["out_stride_bytes"] == 2
    assert active_header["N"] * active_header["out_stride_bytes"] == 14
