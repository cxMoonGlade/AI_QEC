"""CPU gates for the fused-SV precision-purpose contract."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
import torch


def _marshalled(dtype: torch.dtype = torch.complex128):
    from error_coupling_simulator.carrier.within_cycle import WithinCycleMarshalled

    i32 = lambda values: torch.tensor(values, dtype=torch.int32)  # noqa: E731
    return WithinCycleMarshalled(
        n_data=1,
        n_stab=1,
        R=1,
        round_op_ptr=i32([0, 1, 1]),
        op_kind=i32([0]),
        op_uid=i32([0]),
        op_site=i32([0]),
        stab_supp=i32([[0]]),
        stab_supp_isx=i32([[0]]),
        stab_supp_len=i32([1]),
        log_supp=i32([0]),
        log_supp_isx=i32([0]),
        logical_kind=1,
        leak_kraus=torch.eye(3, dtype=dtype).unsqueeze(0),
        gate_unitaries=torch.eye(3, dtype=dtype).unsqueeze(0),
    )


@pytest.mark.parametrize(
    ("purpose", "dtype", "eligibility"),
    [
        ("optimization", "c64", "screening_only"),
        ("final", "c128", "c128_candidate"),
        ("certification", "c128", "c128_candidate"),
    ],
)
def test_run_purpose_has_one_precision_and_evidence_role(
    purpose: str, dtype: str, eligibility: str,
) -> None:
    from error_coupling_simulator.carrier.within_cycle import RunSpec

    spec = RunSpec(
        circuit_path="unused.stim", run_purpose=purpose, dtype=dtype)
    assert spec.run_purpose == purpose
    assert spec.dtype == dtype
    assert spec.evidence_eligibility == eligibility


def test_run_purpose_defaults_fail_safe_and_legacy_c64_is_screening() -> None:
    from error_coupling_simulator.carrier.within_cycle import RunSpec

    default = RunSpec(circuit_path="unused.stim")
    assert (default.run_purpose, default.dtype) == ("final", "c128")

    legacy_c64 = RunSpec(circuit_path="unused.stim", dtype="c64")
    assert legacy_c64.run_purpose == "optimization"
    assert legacy_c64.evidence_eligibility == "screening_only"


@pytest.mark.parametrize(
    ("purpose", "dtype"),
    [
        ("optimization", "c64"),
        ("final", "c128"),
        ("certification", "c128"),
    ],
)
def test_explicit_purpose_derives_dtype_without_a_second_precision_knob(
    purpose: str, dtype: str,
) -> None:
    from error_coupling_simulator.carrier.within_cycle import RunSpec

    spec = RunSpec(circuit_path="unused.stim", run_purpose=purpose)
    assert spec.dtype == dtype


@pytest.mark.parametrize(
    ("purpose", "dtype"),
    [
        ("optimization", "c128"),
        ("final", "c64"),
        ("certification", "c64"),
        ("unknown", "c128"),
    ],
)
def test_explicit_precision_purpose_mismatch_fails_closed(
    purpose: str, dtype: str,
) -> None:
    from error_coupling_simulator.carrier.within_cycle import RunSpec

    with pytest.raises(ValueError, match="run_purpose|precision policy"):
        RunSpec(circuit_path="unused.stim", run_purpose=purpose, dtype=dtype)


def test_precision_cast_changes_only_complex_tables() -> None:
    from error_coupling_simulator.carrier.within_cycle import (
        cast_within_cycle_precision,
    )

    original = _marshalled()
    screened = cast_within_cycle_precision(original, "c64")
    assert screened.leak_kraus.dtype == torch.complex64
    assert screened.gate_unitaries.dtype == torch.complex64
    for name in (
        "round_op_ptr", "op_kind", "op_uid", "op_site", "stab_supp",
        "stab_supp_isx", "stab_supp_len", "log_supp", "log_supp_isx",
    ):
        assert getattr(screened, name) is getattr(original, name)
        assert getattr(screened, name).dtype == torch.int32
    assert original.leak_kraus.dtype == torch.complex128
    assert original.gate_unitaries.dtype == torch.complex128


def test_header_rejects_false_precision_and_marks_screening() -> None:
    from error_coupling_simulator.carrier.within_cycle import (
        RunSpec,
        WithinCycleScheduleHost,
        cast_within_cycle_precision,
        require_c128_evidence_header,
    )

    host = WithinCycleScheduleHost("cpu")
    schedule = SimpleNamespace(logical_kind="Z")
    spec = RunSpec(
        circuit_path="unused.stim", run_purpose="optimization", dtype="c64")
    c128 = _marshalled()
    with pytest.raises(ValueError, match="header.*dtype|precision"):
        host.build_header(spec, c128, schedule)

    c64 = cast_within_cycle_precision(c128, spec.dtype)
    header = host.build_header(spec, c64, schedule)
    assert header["run_purpose"] == "optimization"
    assert header["dtype"] == "c64"
    assert header["evidence_eligibility"] == "screening_only"
    with pytest.raises(ValueError, match="c128.*evidence"):
        require_c128_evidence_header(header)


@pytest.mark.parametrize("purpose", ["final", "certification"])
def test_c128_header_is_evidence_candidate_not_an_automatic_pass(
    purpose: str,
) -> None:
    from error_coupling_simulator.carrier.within_cycle import (
        RunSpec,
        WithinCycleScheduleHost,
        require_c128_evidence_header,
    )

    spec = RunSpec(
        circuit_path="unused.stim", run_purpose=purpose, dtype="c128")
    header = WithinCycleScheduleHost("cpu").build_header(
        spec, _marshalled(), SimpleNamespace(logical_kind="Z"))
    require_c128_evidence_header(header)
    assert header["evidence_eligibility"] == "c128_candidate"
    assert header["build_identity"]["version"]
    assert len(header["build_identity"]["package_tree_sha256"]) == 64
    assert "passed" not in header


def test_c128_evidence_rejects_missing_or_stale_precision_policy() -> None:
    from error_coupling_simulator.carrier.within_cycle import (
        RunSpec,
        WithinCycleScheduleHost,
        require_c128_evidence_header,
    )

    spec = RunSpec(circuit_path="unused.stim", run_purpose="final", dtype="c128")
    header = WithinCycleScheduleHost("cpu").build_header(
        spec, _marshalled(), SimpleNamespace(logical_kind="Z"))
    header.pop("precision_policy")
    with pytest.raises(ValueError, match="precision_policy"):
        require_c128_evidence_header(header)


def test_c128_evidence_rejects_missing_installation_build_identity() -> None:
    from error_coupling_simulator.carrier.within_cycle import (
        RunSpec,
        WithinCycleScheduleHost,
        require_c128_evidence_header,
    )

    spec = RunSpec(circuit_path="unused.stim", run_purpose="final", dtype="c128")
    header = WithinCycleScheduleHost("cpu").build_header(
        spec, _marshalled(), SimpleNamespace(logical_kind="Z"))
    header.pop("build_identity")
    with pytest.raises(ValueError, match="build_identity"):
        require_c128_evidence_header(header)


def test_retained_mps_backend_rejects_c64_instead_of_mislabeling_header() -> None:
    from error_coupling_simulator.carrier.within_cycle import RunSpec
    from qec_twin.forward.scalable.mps_forward import MpsLeakageForward

    spec = RunSpec(
        circuit_path="unused.stim",
        run_purpose="optimization",
        dtype="c64",
    )
    backend = MpsLeakageForward("cpu")
    with pytest.raises(ValueError, match="complex128 only.*FusedWithinCycleSampler"):
        backend.sample(spec)


@pytest.mark.parametrize(
    ("purpose", "dtype", "eligibility"),
    [
        ("optimization", "c64", "screening_only"),
        ("final", "c128", "c128_candidate"),
        ("certification", "c128", "c128_candidate"),
    ],
)
def test_experiment_facade_derives_precision_and_binds_provenance(
    monkeypatch, purpose: str, dtype: str, eligibility: str,
) -> None:
    from error_coupling_simulator.frontend import experiments

    monkeypatch.setattr(
        experiments,
        "_dataset_files",
        lambda _root: {
            "r01_circ": Path("synthetic.stim"),
            "r01_meta": Path("synthetic.json"),
        },
    )
    spec = experiments.run_spec_from_preset(
        experiments.PRESET_LEAK_THETA_0P30,
        n_shots=2,
        n_rounds=3,
        seed=5,
        run_purpose=purpose,
    )
    assert (spec.run_purpose, spec.dtype) == (purpose, dtype)
    precision = spec.numerical_provenance["run_binding"]["precision"]
    assert precision == {
        "policy": "optimization_c64_final_certification_c128_v1",
        "run_purpose": purpose,
        "dtype": dtype,
        "evidence_eligibility": eligibility,
    }
