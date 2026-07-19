"""RED contract for Phase 7 sparse sampled QT/MPS Record support.

Sampled trajectories may emit only outcomes that were actually observed.  Exact
branch enumeration still owns the full binary Record support.  Comparisons must
therefore align probability maps by Record value, not by list position or by an
identical-support precondition.
"""

from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest


_OBSERVED_SUPPORT_POLICY = "observed_empirical_outcomes_only"
_FULL_SUPPORT_POLICY = "full_binary_record_support"
_UNION_ALIGNMENT_POLICY = "union_of_emitted_records_missing_probability_zero"


def _measurement_schedule(width: int = 6):
    from error_coupling_simulator.frontend import (
        CircuitBuilder,
        circuit_ir_to_substep_schedule,
    )

    builder = CircuitBuilder(num_qubits=width)
    builder.measure(
        tuple(range(width)),
        key=tuple(f"m{index}" for index in range(width)),
        duration_ns=1.0,
    )
    return circuit_ir_to_substep_schedule(builder.build())


def _record_layout(width: int):
    from error_coupling_simulator.frontend.axis1_record_layout import (
        AXIS1_SCHEDULE_RECORD_LAYOUT_SCHEMA,
        Axis1MeasurementBoundaryLayout,
        Axis1ScheduleRecordLayout,
    )

    keys = tuple(f"m{index}" for index in range(width))
    targets = tuple(range(width))
    boundary = Axis1MeasurementBoundaryLayout(
        substep_id="measurement-0",
        substep_index=0,
        operations=(),
        keys=keys,
        targets=targets,
        bases=("Z",) * width,
        reset_after=(False,) * width,
        global_slice=(0, width),
    )
    return Axis1ScheduleRecordLayout(
        schema=AXIS1_SCHEDULE_RECORD_LAYOUT_SCHEMA,
        source_hash="phase7-fixture",
        schedule_schema="phase7-fixture.v1",
        boundaries=(boundary,),
        measurement_keys=keys,
        measurement_targets=targets,
        measurement_bases=("Z",) * width,
        reset_after=(False,) * width,
        detectors=(),
        observables=(),
    )


def _sampled_run(
    records: list[list[int]],
    probabilities: list[float],
    *,
    seed: int,
) -> dict[str, Any]:
    return {
        "qt_mps_backend_executed": True,
        "carrier_program": {"requires_scalable_backend": False},
        "mps_execution": {
            "measurement_records": records,
            "record_probabilities": probabilities,
            "trajectory_sampling": {"rng_seed": seed},
        },
    }


def test_phase7_public_schemas_version_sparse_support_semantics() -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    assert qt.AXIS1_QT_MPS_RESTRICTED_EXECUTION_SCHEMA == (
        "error_coupling_simulator.frontend.qt_mps_restricted_execution.v6"
    )
    assert qt.AXIS1_QT_MPS_BOND_SWEEP_SCHEMA == (
        "error_coupling_simulator.frontend.qt_mps_bond_sweep.v4"
    )
    assert qt.AXIS1_QT_MPS_TRAJECTORY_SWEEP_SCHEMA == (
        "error_coupling_simulator.frontend.qt_mps_trajectory_seed_sweep.v4"
    )
    assert qt.AXIS1_QT_MPS_RESTRICTED_EVIDENCE_BUNDLE_SCHEMA == (
        "error_coupling_simulator.frontend.qt_mps_restricted_evidence_bundle.v4"
    )
    assert qt.AXIS1_QT_MPS_RESOURCE_PROBE_SCHEMA == (
        "error_coupling_simulator.frontend.qt_mps_resource_probe.v4"
    )
    assert qt._AXIS1_QT_MPS_RECORD_MATERIALIZATION_PREFLIGHT_SCHEMA == (
        "error_coupling_simulator.frontend."
        "qt_mps_record_materialization_preflight.v2"
    )


def test_sampled_preflight_caps_materialized_support_by_trajectory_count() -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    preflight = qt._record_materialization_preflight(
        SimpleNamespace(measurement_width=40, boundaries=(object(),)),
        max_record_materialization_outcomes=3,
        trajectory_count=3,
    )

    assert preflight["schema"].endswith("preflight.v2")
    assert preflight["record_support_policy"] == _OBSERVED_SUPPORT_POLICY
    assert preflight["trajectory_count"] == 3
    assert preflight["materialized_outcome_count_upper_bound"] == 3
    assert preflight["requires_full_binary_support_materialization"] is False
    assert "materialized_outcome_count" not in preflight
    assert preflight["checked_before_cuda"] is True
    assert preflight["checked_before_record_allocation"] is True


def test_sampled_preflight_remains_fail_closed_at_its_linear_bound() -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    with pytest.raises(ValueError):
        qt._record_materialization_preflight(
            SimpleNamespace(measurement_width=40, boundaries=(object(),)),
            max_record_materialization_outcomes=2,
            trajectory_count=3,
        )


def test_exact_preflight_still_requires_full_binary_support_budget() -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    exact = qt._record_materialization_preflight(
        SimpleNamespace(measurement_width=6, boundaries=(object(),)),
        max_record_materialization_outcomes=64,
        trajectory_count=None,
    )
    assert exact["record_support_policy"] == _FULL_SUPPORT_POLICY
    assert exact["trajectory_count"] is None
    assert exact["materialized_outcome_count_upper_bound"] == 64
    assert exact["requires_full_binary_support_materialization"] is True
    assert "materialized_outcome_count" not in exact

    with pytest.raises(ValueError):
        qt._record_materialization_preflight(
            SimpleNamespace(measurement_width=6, boundaries=(object(),)),
            max_record_materialization_outcomes=63,
            trajectory_count=None,
        )


@pytest.mark.parametrize(
    ("trajectory_count", "budget", "expected_cuda_calls"),
    [
        pytest.param(2, 1, 0, id="sampled-linear-bound-rejected"),
        pytest.param(2, 2, 1, id="sampled-linear-bound-accepted"),
        pytest.param(None, 63, 0, id="exact-full-support-still-rejected"),
        pytest.param(None, 64, 1, id="exact-full-support-accepted"),
    ],
)
def test_direct_manifest_applies_strategy_preflight_before_cuda(
    monkeypatch: pytest.MonkeyPatch,
    trajectory_count: int | None,
    budget: int,
    expected_cuda_calls: int,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    calls = {"cuda": 0, "record_allocation": 0, "exact": 0, "sampled": 0}

    def cuda_sentinel(_device: str) -> str:
        calls["cuda"] += 1
        raise RuntimeError("CUDA_SENTINEL")

    def record_allocation_sentinel(_width: int) -> list[list[int]]:
        calls["record_allocation"] += 1
        raise RuntimeError("RECORD_ALLOCATION_SENTINEL")

    def exact_sentinel(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        calls["exact"] += 1
        raise RuntimeError("EXACT_EXECUTION_SENTINEL")

    def sampled_sentinel(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        calls["sampled"] += 1
        raise RuntimeError("SAMPLED_EXECUTION_SENTINEL")

    monkeypatch.setattr(qt, "_require_cuda_device", cuda_sentinel)
    monkeypatch.setattr(qt, "_measurement_records", record_allocation_sentinel)
    monkeypatch.setattr(qt, "_execute_program", exact_sentinel)
    monkeypatch.setattr(qt, "_execute_sampled_program", sampled_sentinel)
    kwargs: dict[str, Any] = {
        "trajectory_count": trajectory_count,
        "max_record_materialization_outcomes": budget,
    }
    if trajectory_count is not None:
        kwargs["rng_seed"] = 7

    if expected_cuda_calls:
        with pytest.raises(RuntimeError):
            qt.axis1_qt_mps_restricted_execution_manifest(
                _measurement_schedule(),
                **kwargs,
            )
    else:
        with pytest.raises(ValueError):
            qt.axis1_qt_mps_restricted_execution_manifest(
                _measurement_schedule(),
                **kwargs,
            )
    assert calls == {
        "cuda": expected_cuda_calls,
        "record_allocation": 0,
        "exact": 0,
        "sampled": 0,
    }


def test_sampled_executor_emits_only_observed_records_without_full_support(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    width = 6
    outcomes = iter(
        [
            [0] * width,
            [1] * width,
            [0] * width,
        ]
    )

    class FakeMps:
        def apply_to_arrays(self, _callback: Any) -> None:
            return None

        def copy(self) -> "FakeMps":
            return FakeMps()

    class FakeGenerator:
        def manual_seed(self, _seed: int) -> "FakeGenerator":
            return self

    fake_quimb = ModuleType("quimb")
    fake_qtn = ModuleType("quimb.tensor")
    fake_qtn.MPS_product_state = (  # type: ignore[attr-defined]
        lambda _states: FakeMps()
    )
    fake_quimb.tensor = fake_qtn  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "quimb", fake_quimb)
    monkeypatch.setitem(sys.modules, "quimb.tensor", fake_qtn)
    monkeypatch.setattr(qt.torch, "Generator", lambda *, device: FakeGenerator())
    monkeypatch.setattr(qt, "axis1_carrier_substep_summary", lambda _step: {})
    monkeypatch.setattr(qt, "_substep_has_evolution_terms", lambda _step: False)
    monkeypatch.setattr(
        qt,
        "_sample_z_measurement",
        lambda state, **_kwargs: (next(outcomes), state),
    )
    monkeypatch.setattr(
        qt,
        "_apply_z_measurement_reset_if_requested",
        lambda state, *_args, **_kwargs: state,
    )
    monkeypatch.setattr(qt, "max_mps_bond", lambda _states: 1)
    monkeypatch.setattr(
        qt,
        "aggregate_sampled_truncation_events",
        lambda *_args, **_kwargs: {"context_complete": True},
    )
    monkeypatch.setattr(
        qt,
        "build_mps_truncation_ledger",
        lambda **_kwargs: {"discarded_weight_ledger_complete": True},
    )

    def forbidden_full_support(_width: int) -> list[list[int]]:
        raise AssertionError("sampled execution materialized full binary support")

    monkeypatch.setattr(qt, "_measurement_records", forbidden_full_support)
    execution = qt._execute_sampled_program(
        {
            "program": {
                "num_qubits": width,
                "substeps": [
                    {
                        "substep_kind": "measurement",
                        "substep_id": "measurement-0",
                    }
                ],
            }
        },
        record_layout=_record_layout(width),
        device="cuda",
        max_bond=None,
        microstep_count=1,
        finite_step_order="first_order",
        trajectory_count=3,
        rng_seed=11,
    )

    assert execution["measurement_records"] == [[0] * width, [1] * width]
    assert execution["record_counts"] == [2, 1]
    assert execution["record_probabilities"] == pytest.approx(
        [2.0 / 3.0, 1.0 / 3.0]
    )
    assert execution["record_count"] == 2
    assert execution["trajectory_sampling"]["record_support_policy"] == (
        _OBSERVED_SUPPORT_POLICY
    )
    assert execution["trajectory_sampling"]["zero_frequency_records_emitted"] is False


def test_measurement_sampler_conditions_one_binary_target_at_a_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    projector_calls: list[tuple[str, tuple[int, ...], tuple[int, ...]]] = []
    sampled_indices = iter((1, 0, 1))

    def forbidden_full_support(_width: int) -> list[list[int]]:
        raise AssertionError("conditional sampler requested full binary support")

    def project_sentinel(
        state: str,
        *,
        targets: list[int],
        outcome_bits: list[int],
        device: str,
    ) -> tuple[str, float]:
        assert device == "cuda"
        projector_calls.append((state, tuple(targets), tuple(outcome_bits)))
        bit = int(outcome_bits[0])
        target = int(targets[0])
        probability = 0.25 if bit == 0 else 0.75
        return f"{state}|q{target}={bit}", probability

    monkeypatch.setattr(qt, "_measurement_records", forbidden_full_support)
    monkeypatch.setattr(qt, "_project_z_mps", project_sentinel)
    monkeypatch.setattr(
        qt,
        "sample_raw_probability_mass",
        lambda _mass, **_kwargs: next(sampled_indices),
    )

    bits, final_state = qt._sample_z_measurement(
        "initial",
        targets=[2, 0, 3],
        device="cuda",
        generator=SimpleNamespace(),
    )

    assert bits == [1, 0, 1]
    assert final_state == "initial|q2=1|q0=0|q3=1"
    assert projector_calls == [
        ("initial", (2,), (0,)),
        ("initial", (2,), (1,)),
        ("initial|q2=1", (0,), (0,)),
        ("initial|q2=1", (0,), (1,)),
        ("initial|q2=1|q0=0", (3,), (0,)),
        ("initial|q2=1|q0=0", (3,), (1,)),
    ]


def test_seed_sweep_aligns_reordered_and_missing_sparse_support_by_union() -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    runs = [
        _sampled_run([[0], [1]], [0.25, 0.75], seed=1),
        _sampled_run([[1], [0]], [0.75, 0.25], seed=2),
        _sampled_run([[1]], [1.0], seed=3),
    ]
    comparison = qt._trajectory_seed_sweep_comparison(
        runs,
        seed_record_frequency_spread_gate=0.25,
    )

    assert comparison["record_support_alignment_policy"] == _UNION_ALIGNMENT_POLICY
    assert comparison["max_record_frequency_spread_across_seeds"] == pytest.approx(
        0.25
    )
    assert comparison["seed_spread_gate"]["passed"] is True
    assert "measurement_record_order_mismatch" not in comparison["seed_spread_gate"][
        "violations"
    ]


def test_seed_sweep_preserves_canonical_no_measurement_record_sentinel() -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    runs = [
        _sampled_run([[]], [1.0], seed=1),
        _sampled_run([[]], [1.0], seed=2),
    ]
    comparison = qt._trajectory_seed_sweep_comparison(
        runs,
        seed_record_frequency_spread_gate=0.0,
    )

    assert comparison["union_record_support_size"] == 1
    assert comparison["max_record_frequency_spread_across_seeds"] == 0.0
    assert comparison["seed_spread_gate"]["passed"] is True


def test_dense_calibration_aligns_sparse_sampled_support_with_missing_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt
    from test_mps_qt_aggregate_binding import _dense_record_oracle_payload

    schedule = _measurement_schedule(1)
    dense = _dense_record_oracle_payload(qt, schedule, device="cuda")
    dense["record_evidence"]["record_probabilities"] = [0.25, 0.75]
    dense["content_hash"] = qt._stable_payload_hash(dense)

    monkeypatch.setattr(
        qt,
        "axis1_measurement_record_evidence_manifest",
        lambda _schedule, *, device: dense,
    )
    runs = [
        _sampled_run([[1]], [1.0], seed=1),
        _sampled_run([[1], [0]], [0.75, 0.25], seed=2),
    ]
    calibration = qt._trajectory_seed_sweep_dense_calibration(
        schedule,
        runs,
        device="cuda",
        dense_record_frequency_gate=0.25,
    )

    assert calibration["record_support_alignment_policy"] == _UNION_ALIGNMENT_POLICY
    assert calibration["observed_max_abs_frequency_difference"] == pytest.approx(
        0.25
    )
    assert calibration["passed"] is True
    assert "measurement_record_order_mismatch" not in calibration["violations"]
