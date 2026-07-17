"""RED falsifiers for restricted-MPS Phase 1B numerical and resource gates."""

from __future__ import annotations

import inspect
import sys
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest


def _six_bit_measurement_schedule():
    from error_coupling_simulator.frontend import (
        CircuitBuilder,
        circuit_ir_to_substep_schedule,
    )

    builder = CircuitBuilder(num_qubits=6)
    builder.measure(
        tuple(range(6)),
        key=tuple(f"m{i}" for i in range(6)),
        duration_ns=1.0,
    )
    return circuit_ir_to_substep_schedule(builder.build())


def _two_boundary_six_bit_measurement_schedule():
    from error_coupling_simulator.frontend import (
        CircuitBuilder,
        circuit_ir_to_substep_schedule,
    )

    builder = CircuitBuilder(num_qubits=3)
    builder.measure(
        tuple(range(3)),
        key=tuple(f"first_m{i}" for i in range(3)),
        duration_ns=1.0,
    )
    builder.tick()
    builder.measure(
        tuple(range(3)),
        key=tuple(f"second_m{i}" for i in range(3)),
        duration_ns=1.0,
    )
    return circuit_ir_to_substep_schedule(builder.build())


def _ledger(*, explicit_truncation: bool = False) -> dict[str, Any]:
    return {
        "explicit_truncation_requested": explicit_truncation,
        "exact_bond_dimension_sufficient": 4,
        "exact_bond_policy": (
            "finite_cap_below_conservative_exact_sufficient_bond"
            if explicit_truncation
            else "unbounded_no_requested_truncation"
        ),
        "accepted_as_exact_bond_representation": not explicit_truncation,
        "discarded_weight_ledger_complete": True,
        "discarded_weight_sum": 0.0,
        "worst_cut_discarded_weight": 0.0,
        "n_truncating_ops": 0,
        "epistemic_class": "c",
    }


def _qt_policy(
    *,
    residual: Any = 0.0,
    certification: dict[str, Any] | None = None,
    sampling: dict[str, Any] | None = None,
    ledger: dict[str, Any] | None = None,
    requires_scalable_backend: bool = False,
) -> dict[str, Any]:
    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        _restricted_acceptance_policy,
    )

    selected_ledger = _ledger() if ledger is None else ledger
    return _restricted_acceptance_policy(
        program={"requires_scalable_backend": requires_scalable_backend},
        execution={
            "total_probability_residual": residual,
            "trajectory_sampling": sampling
            or {
                "mode": "exact_branch_enumeration",
                "trajectory_count": None,
                "rng_seed": None,
                "rng_seed_was_explicit": False,
            },
            "finite_step_policy": {"microstep_count": 1},
            "mps_truncation_ledger": selected_ledger,
        },
        certification=certification
        or {
            "executed": True,
            "passed": True,
            "comparison_outcome_is_metric": True,
        },
        finite_step_order="first_order",
        finite_step_policy="operator_family_product_formula_v1",
        max_bond=1 if selected_ledger["explicit_truncation_requested"] else None,
        worst_cut_discarded_weight_gate=None,
        total_discarded_weight_gate=None,
    )


def _mcwf_policy(
    *,
    normalization_residual: Any = 0.0,
    certification: dict[str, Any] | None = None,
    rng_seed: Any = 17,
    ledger: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from error_coupling_simulator.frontend.axis1_mcwf_dense_certification import (
        restricted_acceptance_policy,
    )

    return restricted_acceptance_policy(
        execution={
            "total_probability_residual": normalization_residual,
            "trajectory_sampling": {
                "mode": "sampled_fixed_microstep_mcwf_trajectories"
            },
            "jump_sampling": {"probability_mass_residual_max": 0.0},
            "mps_truncation_ledger": _ledger() if ledger is None else ledger,
        },
        certification=certification
        or {
            "executed": True,
            "passed": True,
            "passed_gross": True,
            "comparison_outcome_is_metric": True,
        },
        program={"requires_scalable_backend": False},
        rng_seed=rng_seed,
        trajectory_count=2,
        mass_residual_budget=0.1,
    )


@pytest.mark.parametrize(
    "invalid_residual",
    [float("nan"), float("inf"), float("-inf"), -1.0, False, True],
)
def test_qt_probability_residual_must_be_finite_nonnegative_real(
    invalid_residual: Any,
) -> None:
    policy = _qt_policy(residual=invalid_residual)

    assert policy["accepted_for_restricted_execution"] is False
    assert "invalid_total_probability_residual" in policy["production_blockers"]


def test_qt_true_overcap_without_independent_oracle_is_diagnostic_only() -> None:
    policy = _qt_policy(
        requires_scalable_backend=True,
        certification={
            "executed": False,
            "reason": "schedule_contains_scalable_required_rows",
            "comparison_outcome_is_metric": False,
        },
    )

    assert policy["accepted_for_restricted_execution"] is False
    assert policy["certification_status"] == "unavailable"
    assert policy["diagnostic_only"] is True
    assert policy["blocked_reason"] == (
        "overcap_independent_record_oracle_unavailable"
    )
    assert policy["overcap"][
        "accepted_as_restricted_overcap_execution"
    ] is False


@pytest.mark.parametrize(
    "invalid_residual",
    [float("nan"), float("inf"), float("-inf"), -1.0, False, True],
)
def test_mcwf_normalization_residual_must_be_finite_nonnegative_real(
    invalid_residual: Any,
) -> None:
    policy = _mcwf_policy(normalization_residual=invalid_residual)

    assert policy["accepted_for_restricted_execution"] is False
    assert policy["certification_status"] == "rejected"
    assert policy["probability"][
        "normalization_invariant_is_finite_nonnegative_real"
    ] is False
    assert policy["blocked_reason"] == "normalization_invariant_invalid"


@pytest.mark.parametrize("invalid_flag", [float("nan"), float("inf"), 1, "false"])
@pytest.mark.parametrize(
    ("route", "field"),
    [
        ("qt", "executed"),
        ("qt", "passed"),
        ("mcwf", "executed"),
        ("mcwf", "passed_gross"),
    ],
)
def test_dense_certification_flags_require_actual_booleans(
    route: str,
    field: str,
    invalid_flag: Any,
) -> None:
    certification = {
        "executed": True,
        "passed": True,
        "passed_gross": True,
        "comparison_outcome_is_metric": True,
    }
    certification[field] = invalid_flag

    with pytest.raises(TypeError, match=field):
        if route == "qt":
            _qt_policy(certification=certification)
        else:
            _mcwf_policy(certification=certification)


def test_qt_seed_evidence_flag_rejects_truthy_nonboolean() -> None:
    with pytest.raises(TypeError, match="rng_seed_was_explicit"):
        _qt_policy(
            sampling={
                "mode": "sampled_product_channel_trajectories",
                "trajectory_count": 2,
                "rng_seed": 17,
                "rng_seed_was_explicit": float("nan"),
            },
            certification={
                "executed": False,
                "reason": (
                    "sampled_trajectory_empirical_probabilities_not_exact_dense_certified"
                ),
                "comparison_outcome_is_metric": False,
            },
        )


def test_mcwf_explicit_seed_rejects_bool_as_integer() -> None:
    with pytest.raises(TypeError, match="rng_seed"):
        _mcwf_policy(rng_seed=True)


@pytest.mark.parametrize(
    "missing_key",
    [
        "discarded_weight_ledger_complete",
        "discarded_weight_sum",
        "worst_cut_discarded_weight",
    ],
)
def test_truncation_gate_requires_every_mandatory_ledger_value(
    missing_key: str,
) -> None:
    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        _truncation_gate_result,
    )

    ledger = _ledger(explicit_truncation=True)
    ledger.pop(missing_key)
    with pytest.raises(KeyError, match=missing_key):
        _truncation_gate_result(
            ledger,
            worst_cut_discarded_weight_gate=1.0,
            total_discarded_weight_gate=1.0,
        )


def test_truncation_ledger_complete_flag_requires_actual_boolean() -> None:
    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        _truncation_gate_result,
    )

    ledger = _ledger(explicit_truncation=True)
    ledger["discarded_weight_ledger_complete"] = float("nan")
    with pytest.raises(TypeError, match="discarded_weight_ledger_complete"):
        _truncation_gate_result(
            ledger,
            worst_cut_discarded_weight_gate=1.0,
            total_discarded_weight_gate=1.0,
        )


@pytest.mark.parametrize("route", ["qt", "mcwf"])
def test_lossless_finite_bond_claim_requires_truncating_operation_count(
    route: str,
) -> None:
    ledger = _ledger(explicit_truncation=True)
    ledger.pop("n_truncating_ops")

    with pytest.raises(KeyError, match="n_truncating_ops"):
        if route == "qt":
            _qt_policy(ledger=ledger)
        else:
            _mcwf_policy(ledger=ledger)


def test_probability_and_truncation_gates_include_the_equality_boundary() -> None:
    import error_coupling_simulator.frontend.axis1_mcwf_dense_certification as mcwf
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    assert _qt_policy(residual=qt._TOTAL_PROBABILITY_RESIDUAL_GATE)[
        "accepted_for_restricted_execution"
    ] is True
    assert _mcwf_policy(normalization_residual=mcwf._NORMALIZATION_INVARIANT_GATE)[
        "accepted_for_restricted_execution"
    ] is True
    gate = qt._truncation_gate_result(
        {
            "discarded_weight_ledger_complete": True,
            "discarded_weight_sum": 0.2,
            "worst_cut_discarded_weight": 0.1,
        },
        worst_cut_discarded_weight_gate=0.1,
        total_discarded_weight_gate=0.2,
    )
    assert gate["passed"] is True


@pytest.mark.parametrize(
    "invalid_free_vram",
    [float("nan"), float("inf"), float("-inf"), -1.0, 0.0],
)
def test_auto_router_fails_toward_mcwf_on_invalid_free_vram(
    monkeypatch: pytest.MonkeyPatch,
    invalid_free_vram: float,
) -> None:
    import error_coupling_simulator.frontend.axis1_carrier_execution as carrier

    schedule = SimpleNamespace(num_qubits=2, substeps=())
    monkeypatch.setattr(
        carrier,
        "_available_vram_bytes",
        lambda _device: invalid_free_vram,
    )
    chosen, decision = carrier._select_dense_or_mcwf(
        schedule,
        "cuda",
        {"requires_scalable_backend": False},
    )

    assert chosen == carrier.AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
    assert decision["use_dense"] is False
    assert "invalid_available_vram_bytes" in decision["route_reasons"]


_INVALID_OPTIONAL_GATES = [
    pytest.param(False, TypeError, id="false"),
    pytest.param(True, TypeError, id="true"),
    pytest.param(-1.0, ValueError, id="negative"),
    pytest.param(float("nan"), ValueError, id="nan"),
    pytest.param(float("inf"), ValueError, id="posinf"),
    pytest.param(float("-inf"), ValueError, id="neginf"),
]


@pytest.mark.parametrize(
    ("gate_name", "surface"),
    [
        ("convergence_record_probability_gate", "bond"),
        ("seed_record_frequency_spread_gate", "seed"),
        ("dense_record_frequency_gate", "seed"),
        ("min_peak_allocated_gib", "resource"),
        ("min_peak_reserved_gib", "resource"),
    ],
)
@pytest.mark.parametrize(("invalid_gate", "error_type"), _INVALID_OPTIONAL_GATES)
def test_qt_mps_optional_gates_reject_invalid_values_before_delegate(
    monkeypatch: pytest.MonkeyPatch,
    gate_name: str,
    surface: str,
    invalid_gate: Any,
    error_type: type[Exception],
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    delegate_calls = 0

    def delegate_sentinel(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        nonlocal delegate_calls
        delegate_calls += 1
        raise RuntimeError("DELEGATE_SENTINEL")

    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_restricted_execution_manifest",
        delegate_sentinel,
    )
    monkeypatch.setattr(qt, "_require_cuda_device", delegate_sentinel)
    schedule = _six_bit_measurement_schedule()
    with pytest.raises(error_type, match=gate_name):
        if surface == "bond":
            qt.axis1_qt_mps_bond_sweep_manifest(
                schedule,
                bond_values=(1, 2),
                **{gate_name: invalid_gate},
            )
        elif surface == "seed":
            qt.axis1_qt_mps_trajectory_seed_sweep_manifest(
                schedule,
                trajectory_count=1,
                rng_seeds=(0, 1),
                **{gate_name: invalid_gate},
            )
        else:
            qt.axis1_qt_mps_resource_probe_manifest(
                schedule,
                bond_values=(1, 2),
                trajectory_count=1,
                rng_seeds=(0, 1),
                **{gate_name: invalid_gate},
            )

    assert delegate_calls == 0


@pytest.mark.parametrize(
    "nested_gate_name",
    [
        "convergence_record_probability_gate",
        "seed_record_frequency_spread_gate",
        "dense_record_frequency_gate",
    ],
)
def test_resource_probe_validates_nested_gates_before_cuda(
    monkeypatch: pytest.MonkeyPatch,
    nested_gate_name: str,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    cuda_calls = 0

    def cuda_sentinel(*_args: Any, **_kwargs: Any) -> str:
        nonlocal cuda_calls
        cuda_calls += 1
        raise RuntimeError("CUDA_SENTINEL")

    monkeypatch.setattr(qt, "_require_cuda_device", cuda_sentinel)
    with pytest.raises(ValueError, match=nested_gate_name):
        qt.axis1_qt_mps_resource_probe_manifest(
            _six_bit_measurement_schedule(),
            bond_values=(1, 2),
            trajectory_count=1,
            rng_seeds=(0, 1),
            **{nested_gate_name: float("nan")},
        )

    assert cuda_calls == 0


def _qt_record_run(
    probabilities: list[float],
    *,
    max_bond: int,
    rng_seed: int,
) -> dict[str, Any]:
    return {
        "max_bond": max_bond,
        "qt_mps_backend_executed": True,
        "carrier_program": {"requires_scalable_backend": False},
        "mps_execution": {
            "measurement_records": [[0], [1]],
            "record_probabilities": probabilities,
            "trajectory_sampling": {"rng_seed": rng_seed},
        },
    }


def test_maximum_probability_gates_keep_inclusive_boundaries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from math import inf, nextafter

    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    delta = 0.125
    below_delta = nextafter(delta, -inf)
    runs = [
        _qt_record_run([0.375, 0.625], max_bond=1, rng_seed=0),
        _qt_record_run([0.5, 0.5], max_bond=2, rng_seed=1),
    ]

    bond_equal = qt._bond_sweep_comparison(
        runs,
        convergence_record_probability_gate=delta,
    )
    bond_below = qt._bond_sweep_comparison(
        runs,
        convergence_record_probability_gate=below_delta,
    )
    assert bond_equal["convergence_gate"]["passed"] is True
    assert bond_below["convergence_gate"]["passed"] is False

    seed_equal = qt._trajectory_seed_sweep_comparison(
        runs,
        seed_record_frequency_spread_gate=delta,
    )
    seed_below = qt._trajectory_seed_sweep_comparison(
        runs,
        seed_record_frequency_spread_gate=below_delta,
    )
    assert seed_equal["seed_spread_gate"]["passed"] is True
    assert seed_below["seed_spread_gate"]["passed"] is False

    monkeypatch.setattr(
        qt,
        "axis1_measurement_record_evidence_manifest",
        lambda _schedule, *, device: {
            "schema": "independent_dense_record_fixture.v1",
            "content_hash": "fixture",
            "record_evidence": {
                "measurement_records": [[0], [1]],
                "record_probabilities": [0.5, 0.5],
            },
        },
    )
    dense_equal = qt._trajectory_seed_sweep_dense_calibration(
        SimpleNamespace(),
        runs,
        device="cuda",
        dense_record_frequency_gate=delta,
    )
    dense_below = qt._trajectory_seed_sweep_dense_calibration(
        SimpleNamespace(),
        runs,
        device="cuda",
        dense_record_frequency_gate=below_delta,
    )
    assert dense_equal["passed"] is True
    assert dense_below["passed"] is False


@pytest.mark.parametrize(
    "gate_name",
    ["min_peak_allocated_gib", "min_peak_reserved_gib"],
)
def test_minimum_resource_gates_keep_inclusive_boundaries(
    gate_name: str,
) -> None:
    from math import inf, nextafter

    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    equal_kwargs = {
        "min_peak_allocated_gib": 1.0,
        "min_peak_reserved_gib": 1.0,
    }
    equal = qt._resource_probe_policy(
        peak_allocated_bytes=1024**3,
        peak_reserved_bytes=1024**3,
        **equal_kwargs,
    )
    assert equal["gate_passed"] is True

    failing_kwargs = dict(equal_kwargs)
    failing_kwargs[gate_name] = nextafter(1.0, inf)
    above = qt._resource_probe_policy(
        peak_allocated_bytes=1024**3,
        peak_reserved_bytes=1024**3,
        **failing_kwargs,
    )
    assert above["gate_passed"] is False


@pytest.mark.parametrize(
    "invalid_observation",
    [False, True, -1.0, float("nan"), float("inf"), float("-inf")],
)
@pytest.mark.parametrize(
    "field",
    ["discarded_weight_sum", "worst_cut_discarded_weight"],
)
def test_invalid_truncation_observation_fails_without_declared_gate(
    field: str,
    invalid_observation: Any,
) -> None:
    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        _truncation_gate_result,
    )

    ledger = _ledger(explicit_truncation=True)
    ledger[field] = invalid_observation
    gate = _truncation_gate_result(
        ledger,
        worst_cut_discarded_weight_gate=None,
        total_discarded_weight_gate=None,
    )

    assert gate["evaluated"] is True
    assert gate["passed"] is False
    assert f"invalid_{field}" in gate["violations"]


def test_truncation_gate_rejects_the_next_float_above_the_inclusive_boundary() -> None:
    from math import inf, nextafter

    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        _truncation_gate_result,
    )

    gate = _truncation_gate_result(
        {
            "discarded_weight_ledger_complete": True,
            "discarded_weight_sum": nextafter(0.2, inf),
            "worst_cut_discarded_weight": nextafter(0.1, inf),
        },
        worst_cut_discarded_weight_gate=0.1,
        total_discarded_weight_gate=0.2,
    )

    assert gate["evaluated"] is True
    assert gate["passed"] is False


class _IndexSixtyFour:
    def __index__(self) -> int:
        return 64


def test_record_materialization_budget_accepts_index_integers() -> None:
    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        _normalize_max_record_materialization_outcomes,
    )

    assert _normalize_max_record_materialization_outcomes(64) == 64
    assert _normalize_max_record_materialization_outcomes(_IndexSixtyFour()) == 64


@pytest.mark.parametrize(
    "invalid_budget",
    [
        None,
        False,
        True,
        64.0,
        "64",
        Decimal("64"),
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_record_materialization_budget_rejects_nonintegers(
    invalid_budget: Any,
) -> None:
    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        _normalize_max_record_materialization_outcomes,
    )

    with pytest.raises(TypeError, match="max_record_materialization_outcomes"):
        _normalize_max_record_materialization_outcomes(invalid_budget)


@pytest.mark.parametrize("invalid_budget", [0, -1, sys.maxsize + 1])
def test_record_materialization_budget_rejects_out_of_domain_integers(
    invalid_budget: int,
) -> None:
    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        _normalize_max_record_materialization_outcomes,
    )

    with pytest.raises(ValueError, match="max_record_materialization_outcomes"):
        _normalize_max_record_materialization_outcomes(invalid_budget)


def test_all_qt_mps_resource_surfaces_declare_the_same_record_budget() -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    for name in (
        "axis1_qt_mps_restricted_execution_manifest",
        "axis1_qt_mps_bond_sweep_manifest",
        "axis1_qt_mps_trajectory_seed_sweep_manifest",
        "axis1_qt_mps_restricted_evidence_bundle_manifest",
        "axis1_qt_mps_resource_probe_manifest",
    ):
        parameter = inspect.signature(getattr(qt, name)).parameters[
            "max_record_materialization_outcomes"
        ]
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
        assert parameter.default == 4096


def _install_qt_no_execution_sentinels(
    monkeypatch: pytest.MonkeyPatch,
    qt: Any,
) -> dict[str, int]:
    calls = {"cuda": 0, "records": 0, "exact": 0, "sampled": 0}

    def cuda_sentinel(_device: str) -> str:
        calls["cuda"] += 1
        raise RuntimeError("CUDA_SENTINEL")

    def records_sentinel(_width: int) -> list[list[int]]:
        calls["records"] += 1
        raise RuntimeError("RECORD_ALLOCATION_SENTINEL")

    def exact_sentinel(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        calls["exact"] += 1
        raise RuntimeError("EXACT_EXECUTION_SENTINEL")

    def sampled_sentinel(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        calls["sampled"] += 1
        raise RuntimeError("SAMPLED_EXECUTION_SENTINEL")

    monkeypatch.setattr(qt, "_require_cuda_device", cuda_sentinel)
    monkeypatch.setattr(qt, "_measurement_records", records_sentinel)
    monkeypatch.setattr(qt, "_execute_program", exact_sentinel)
    monkeypatch.setattr(qt, "_execute_sampled_program", sampled_sentinel)
    return calls


@pytest.mark.parametrize("trajectory_count", [None, 1])
def test_record_budget_rejects_exact_and_sampled_before_cuda_or_allocation(
    monkeypatch: pytest.MonkeyPatch,
    trajectory_count: int | None,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    calls = _install_qt_no_execution_sentinels(monkeypatch, qt)
    kwargs: dict[str, Any] = {
        "max_record_materialization_outcomes": 63,
        "trajectory_count": trajectory_count,
    }
    if trajectory_count is not None:
        kwargs["rng_seed"] = 0

    with pytest.raises(
        ValueError,
        match="record materialization outcome budget exceeded",
    ):
        qt.axis1_qt_mps_restricted_execution_manifest(
            _six_bit_measurement_schedule(),
            **kwargs,
        )

    assert calls == {"cuda": 0, "records": 0, "exact": 0, "sampled": 0}


def test_record_budget_counts_total_width_across_measurement_boundaries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    calls = _install_qt_no_execution_sentinels(monkeypatch, qt)
    with pytest.raises(
        ValueError,
        match="record materialization outcome budget exceeded",
    ):
        qt.axis1_qt_mps_restricted_execution_manifest(
            _two_boundary_six_bit_measurement_schedule(),
            max_record_materialization_outcomes=63,
        )

    assert calls == {"cuda": 0, "records": 0, "exact": 0, "sampled": 0}


@pytest.mark.parametrize("budget", [64, 65])
@pytest.mark.parametrize("trajectory_count", [None, 1])
def test_record_budget_equality_and_above_reach_cuda_only_after_preflight(
    monkeypatch: pytest.MonkeyPatch,
    budget: int,
    trajectory_count: int | None,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    calls = _install_qt_no_execution_sentinels(monkeypatch, qt)
    kwargs: dict[str, Any] = {
        "max_record_materialization_outcomes": budget,
        "trajectory_count": trajectory_count,
    }
    if trajectory_count is not None:
        kwargs["rng_seed"] = 0

    with pytest.raises(RuntimeError, match="CUDA_SENTINEL"):
        qt.axis1_qt_mps_restricted_execution_manifest(
            _six_bit_measurement_schedule(),
            **kwargs,
        )

    assert calls == {"cuda": 1, "records": 0, "exact": 0, "sampled": 0}


def test_carrier_record_budget_blocks_before_either_cuda_seam(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_carrier_execution as carrier
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    carrier_cuda_calls = 0

    def carrier_cuda_sentinel(_device: str) -> str:
        nonlocal carrier_cuda_calls
        carrier_cuda_calls += 1
        raise RuntimeError("CARRIER_CUDA_SENTINEL")

    monkeypatch.setattr(carrier, "_require_cuda_device", carrier_cuda_sentinel)
    qt_calls = _install_qt_no_execution_sentinels(monkeypatch, qt)

    with pytest.raises(
        ValueError,
        match="record materialization outcome budget exceeded",
    ):
        carrier.axis1_carrier_execution_manifest(
            _six_bit_measurement_schedule(),
            execution_backend_contract=(
                carrier.AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT
            ),
            execution_backend_options={
                "max_record_materialization_outcomes": 63,
            },
        )

    assert carrier_cuda_calls == 0
    assert qt_calls == {"cuda": 0, "records": 0, "exact": 0, "sampled": 0}


def test_resource_probe_record_budget_blocks_before_cuda_accounting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    calls = _install_qt_no_execution_sentinels(monkeypatch, qt)
    cuda_accounting_calls = {
        "empty_cache": 0,
        "reset_peak_memory_stats": 0,
        "synchronize": 0,
    }

    def accounting_sentinel(name: str):
        def sentinel(*_args: Any, **_kwargs: Any) -> None:
            cuda_accounting_calls[name] += 1
            raise RuntimeError(f"{name.upper()}_SENTINEL")

        return sentinel

    for name in cuda_accounting_calls:
        monkeypatch.setattr(qt.torch.cuda, name, accounting_sentinel(name))

    with pytest.raises(
        ValueError,
        match="record materialization outcome budget exceeded",
    ):
        qt.axis1_qt_mps_resource_probe_manifest(
            _six_bit_measurement_schedule(),
            bond_values=(1, 2),
            trajectory_count=1,
            rng_seeds=(0, 1),
            max_record_materialization_outcomes=63,
        )

    assert calls == {"cuda": 0, "records": 0, "exact": 0, "sampled": 0}
    assert cuda_accounting_calls == {
        "empty_cache": 0,
        "reset_peak_memory_stats": 0,
        "synchronize": 0,
    }
