from __future__ import annotations

"""CPU falsifiers for restricted-MPS probability and mutation-norm policy.

The scalar probability oracles are independent of the MPS implementation.  In
particular, the tiny decay probabilities are reconstructed with ``Decimal``
rather than the production exponential path, and the MCWF residual fixture is
the hand-written first-order one-site T1 formula.
"""

from decimal import Decimal, localcontext
from fractions import Fraction
from importlib import import_module
import math
from typing import Any

import pytest


_MIN_SUBNORMAL = math.nextafter(0.0, 1.0)


def _one_minus_exp_negative_decimal(value: float) -> float:
    """High-precision ``1 - exp(-value)`` from the exact binary64 input."""

    with localcontext() as context:
        context.prec = 120
        exact = Decimal.from_float(float(value))
        return float(Decimal(1) - (-exact).exp())


def _matrix_entry_mass(matrix: Any, row: int, column: int) -> float:
    entry = complex(matrix[int(row), int(column)].detach().cpu().item())
    return float(entry.real * entry.real + entry.imag * entry.imag)


def _one_site_product_mps(*, level: int):
    import quimb.tensor as qtn
    import torch

    vector = torch.zeros(2, dtype=torch.complex128, device="cpu")
    vector[int(level)] = 1.0
    return qtn.MPS_product_state([vector])


class _MutationState:
    """Minimum state seam needed to observe post-mutation normalization."""

    def __init__(self) -> None:
        self.gate_calls = 0
        self.multiply_factors: list[float] = []

    def copy(self) -> _MutationState:
        return _MutationState()

    def gate_(self, *_args: Any, **_kwargs: Any) -> _MutationState:
        self.gate_calls += 1
        return self

    def multiply_(self, factor: float, *, spread_over: int) -> _MutationState:
        assert spread_over == 1
        self.multiply_factors.append(float(factor))
        return self


@pytest.mark.parametrize(
    ("family", "entry", "expected_probability"),
    [
        pytest.param(
            "T1",
            (0, 1),
            _one_minus_exp_negative_decimal(2.0**-54),
            id="t1",
        ),
        pytest.param(
            "T2",
            (0, 0),
            0.5 * _one_minus_exp_negative_decimal(2.0**-55),
            id="t2",
        ),
    ],
)
def test_mps006_tiny_positive_t1_t2_probability_matches_decimal_oracle(
    family: str,
    entry: tuple[int, int],
    expected_probability: float,
) -> None:
    """A representable positive decay mass is never rounded to structural zero."""

    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        _collapse_kraus,
    )

    # coefficient**2 = 2**-54 exactly.  T1 uses that exponent directly;
    # T2 uses gamma=rate/2 and then half the phase-flip probability.
    coefficient = 2.0**-27
    operators = _collapse_kraus(
        {
            "operator_family": family,
            "coefficient": coefficient,
        },
        1.0,
        device="cpu",
    )

    observed = _matrix_entry_mass(operators[1], *entry)
    assert expected_probability > 0.0
    assert observed > 0.0
    assert observed == pytest.approx(expected_probability, rel=5.0e-15, abs=0.0)


@pytest.mark.parametrize(
    ("raw_norm", "expected_factor"),
    [
        pytest.param(0.0, None, id="exact-structural-zero"),
        pytest.param(
            _MIN_SUBNORMAL,
            1.0 / math.sqrt(_MIN_SUBNORMAL),
            id="smallest-positive-subnormal",
        ),
    ],
)
def test_mps006_qt_projection_distinguishes_zero_from_minimum_subnormal(
    monkeypatch: pytest.MonkeyPatch,
    raw_norm: float,
    expected_factor: float | None,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    monkeypatch.setattr(qt, "mps_norm_squared", lambda _state: raw_norm)
    projected, probability = qt._project_z_mps(
        _MutationState(),
        targets=[0],
        outcome_bits=[1],
        device="cpu",
    )

    assert probability == raw_norm
    if expected_factor is None:
        assert projected.multiply_factors == []
    else:
        assert projected.multiply_factors == [expected_factor]
        assert math.isfinite(projected.multiply_factors[0])


def test_mps011_raw_mass_snapshot_is_immutable_and_does_not_normalize() -> None:
    probability = import_module(
        "error_coupling_simulator.carrier.mps.probability"
    )
    raw_values = [0.2, 0.3]

    mass = probability.validate_raw_probability_mass(
        raw_values,
        name="law-neutral fixture",
    )

    assert raw_values == [0.2, 0.3]
    assert mass.values == (0.2, 0.3)
    assert mass.total == 0.5
    assert mass.residual_from_one == 0.5
    assert mass.positive_indices == (0, 1)
    with pytest.raises((AttributeError, TypeError)):
        mass.total = 1.0


def test_mps011_raw_mass_snapshot_keeps_zero_and_minimum_subnormal_distinct() -> None:
    probability = import_module(
        "error_coupling_simulator.carrier.mps.probability"
    )

    mass = probability.validate_raw_probability_mass(
        (0.0, _MIN_SUBNORMAL),
        name="representability fixture",
    )

    assert mass.values == (0.0, _MIN_SUBNORMAL)
    assert mass.total == _MIN_SUBNORMAL
    assert mass.residual_from_one == 1.0
    assert mass.positive_indices == (1,)


def test_mps011_raw_mass_snapshot_rejects_bool_negative_and_nonfinite() -> None:
    probability = import_module(
        "error_coupling_simulator.carrier.mps.probability"
    )
    validate = probability.validate_raw_probability_mass

    invalid = (
        ((), ValueError),
        ((True,), TypeError),
        (("0.5",), TypeError),
        ((-_MIN_SUBNORMAL,), ValueError),
        ((math.nan,), ValueError),
        ((math.inf,), ValueError),
        ((-math.inf,), ValueError),
    )
    for values, exception_type in invalid:
        with pytest.raises(exception_type):
            validate(values, name="invalid raw mass")


def test_mps011_raw_mass_rejects_bad_iterables_and_nonfinite_total(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    probability = import_module(
        "error_coupling_simulator.carrier.mps.probability"
    )
    validate = probability.validate_raw_probability_mass

    with pytest.raises(TypeError):
        validate("0.5", name="text raw mass")
    with pytest.raises(TypeError):
        validate(0.5, name="scalar raw mass")

    largest_finite = float.fromhex("0x1.fffffffffffffp+1023")
    with pytest.raises(ValueError):
        validate(
            (largest_finite, largest_finite),
            name="overflowed finite raw mass",
        )

    monkeypatch.setattr(probability.math, "fsum", lambda _values: math.inf)
    with pytest.raises(ValueError):
        validate((0.25, 0.75), name="corrupted nonfinite total")


def test_mps006_probability_product_distinguishes_structural_zero_from_underflow() -> None:
    probability = import_module(
        "error_coupling_simulator.carrier.mps.probability"
    )
    multiply = probability.multiply_probability_values

    assert multiply(0.0, _MIN_SUBNORMAL, name="structural zero") == 0.0
    assert multiply(_MIN_SUBNORMAL, 1.0, name="representable product") == _MIN_SUBNORMAL
    with pytest.raises(ValueError):
        multiply(_MIN_SUBNORMAL, 0.5, name="underflowed positive product")


def test_mps006_probability_helpers_bind_exact_stable_primitive_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    probability = import_module(
        "error_coupling_simulator.carrier.mps.probability"
    )
    product_calls: list[tuple[float, float, float]] = []
    expm1_calls: list[float] = []

    def fake_scaled_product_ratio(
        left: float,
        right: float,
        denominator: float,
        *,
        name: str,
    ) -> float:
        product_calls.append((left, right, denominator))
        return 0.125

    def fake_expm1(argument: float) -> float:
        expm1_calls.append(argument)
        return -0.125

    monkeypatch.setattr(
        probability,
        "scaled_product_ratio",
        fake_scaled_product_ratio,
    )
    monkeypatch.setattr(probability.math, "expm1", fake_expm1)

    assert probability.multiply_probability_values(
        0.0,
        0.5,
        name="structural-zero short circuit",
    ) == 0.0
    assert product_calls == []
    assert probability.multiply_probability_values(
        1.0,
        0.5,
        name="unit-factor product",
    ) == 0.125
    assert product_calls == [(1.0, 0.5, 1.0)]
    assert probability.multiply_probability_values(
        0.25,
        0.5,
        name="bound product",
    ) == 0.125
    assert product_calls == [(1.0, 0.5, 1.0), (0.25, 0.5, 1.0)]
    assert probability.one_minus_exp_neg_probability(
        0.25,
        name="bound exponential",
    ) == 0.125
    assert expm1_calls == [-0.25]


def test_mps006_one_minus_exp_negative_rejects_false_open_endpoint() -> None:
    probability = import_module(
        "error_coupling_simulator.carrier.mps.probability"
    )
    stable = probability.one_minus_exp_neg_probability

    assert stable(0.0, name="structural zero exponent") == 0.0
    assert stable(2.0**-54, name="tiny open probability") > 0.0
    with pytest.raises(ValueError):
        stable(1000.0, name="false unit endpoint")


def test_mps006_one_minus_exp_negative_rejects_corrupted_false_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    probability = import_module(
        "error_coupling_simulator.carrier.mps.probability"
    )
    monkeypatch.setattr(probability.math, "expm1", lambda _argument: -0.0)

    with pytest.raises(ValueError):
        probability.one_minus_exp_neg_probability(
            0.25,
            name="corrupted false zero",
        )


def test_mps011_raw_sampler_preserves_healthy_index_and_rng_state() -> None:
    probability = import_module(
        "error_coupling_simulator.carrier.mps.probability"
    )
    import torch

    mass = probability.validate_raw_probability_mass(
        (0.0, 0.3, 0.7),
        name="healthy raw sampler",
    )
    reference_generator = torch.Generator(device="cpu")
    candidate_generator = torch.Generator(device="cpu")
    reference_generator.manual_seed(41101)
    candidate_generator.manual_seed(41101)

    reference_weights = torch.tensor((0.3, 0.7), dtype=torch.float64)
    reference_weights = reference_weights / torch.sum(reference_weights)
    reference_local_index = int(
        torch.multinomial(
            reference_weights,
            1,
            generator=reference_generator,
        ).item()
    )
    expected_index = mass.positive_indices[reference_local_index]
    observed_index = probability.sample_raw_probability_mass(
        mass,
        device="cpu",
        generator=candidate_generator,
    )

    assert observed_index == expected_index
    assert torch.equal(reference_generator.get_state(), candidate_generator.get_state())
    assert mass.total == 1.0
    assert mass.values == (0.0, 0.3, 0.7)


def test_mps011_raw_sampler_binds_positive_subset_dtype_device_and_index_map(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import torch

    probability = import_module(
        "error_coupling_simulator.carrier.mps.probability"
    )
    real_tensor = torch.tensor
    tensor_calls: list[tuple[tuple[float, ...], object, object]] = []
    multinomial_calls: list[tuple[torch.Tensor, int, object]] = []
    generator = object()

    def capture_tensor(values, *, dtype, device):
        tensor_calls.append((tuple(values), dtype, device))
        return real_tensor(values, dtype=dtype, device=device)

    def select_second(weights, num_samples, *, generator):
        multinomial_calls.append((weights.detach().clone(), num_samples, generator))
        return real_tensor(1)

    monkeypatch.setattr(probability.torch, "tensor", capture_tensor)
    monkeypatch.setattr(probability.torch, "multinomial", select_second)
    mass = probability.validate_raw_probability_mass(
        (0.0, 2.0, 0.0, 6.0),
        name="sparse raw sampler",
    )

    observed = probability.sample_raw_probability_mass(
        mass,
        device="cpu",
        generator=generator,
    )

    assert observed == 3
    assert tensor_calls == [
        ((2.0, 6.0), torch.float64, "cpu"),
    ]
    assert len(multinomial_calls) == 1
    weights, num_samples, observed_generator = multinomial_calls[0]
    assert torch.equal(weights, real_tensor((0.25, 0.75), dtype=torch.float64))
    assert num_samples == 1
    assert observed_generator is generator


def test_mps011_raw_sampler_rejects_unvalidated_and_zero_mass_without_rng() -> None:
    probability = import_module(
        "error_coupling_simulator.carrier.mps.probability"
    )
    import torch

    generator = torch.Generator(device="cpu")
    generator.manual_seed(41102)
    initial_rng_state = generator.get_state().clone()

    with pytest.raises(TypeError):
        probability.sample_raw_probability_mass(
            (0.25, 0.75),
            device="cpu",
            generator=generator,
        )
    assert torch.equal(generator.get_state(), initial_rng_state)

    zero_mass = probability.validate_raw_probability_mass(
        (0.0, 0.0),
        name="all-zero raw sampler",
    )
    with pytest.raises(ValueError):
        probability.sample_raw_probability_mass(
            zero_mass,
            device="cpu",
            generator=generator,
        )
    assert torch.equal(generator.get_state(), initial_rng_state)


def test_mps011_raw_mass_constructor_rejects_forged_invariants_without_rng(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    probability = import_module(
        "error_coupling_simulator.carrier.mps.probability"
    )
    import torch

    generator = torch.Generator(device="cpu")
    generator.manual_seed(41103)
    initial_rng_state = generator.get_state().clone()

    forged_fields = (
        {
            "values": (0.25, 0.75),
            "total": 2.0,
            "residual_from_one": 1.0,
            "positive_indices": (0, 1),
        },
        {
            "values": (0.25, 0.75),
            "total": 1.0,
            "residual_from_one": 0.5,
            "positive_indices": (0, 1),
        },
        {
            "values": (0.0, 1.0),
            "total": 1.0,
            "residual_from_one": 0.0,
            "positive_indices": (0, 1),
        },
    )
    for fields in forged_fields:
        with pytest.raises(ValueError):
            probability.RawProbabilityMass(**fields)
        assert torch.equal(generator.get_state(), initial_rng_state)

    with pytest.raises(TypeError):
        probability.RawProbabilityMass(
            values=[0.25, 0.75],
            total=1.0,
            residual_from_one=0.0,
            positive_indices=(0, 1),
        )
    assert torch.equal(generator.get_state(), initial_rng_state)

    with pytest.raises(ValueError):
        probability.RawProbabilityMass(
            values=(),
            total=0.0,
            residual_from_one=1.0,
            positive_indices=(),
        )

    largest_finite = float.fromhex("0x1.fffffffffffffp+1023")
    with pytest.raises(ValueError):
        probability.RawProbabilityMass(
            values=(largest_finite, largest_finite),
            total=largest_finite,
            residual_from_one=largest_finite,
            positive_indices=(0, 1),
        )

    original_fsum = probability.math.fsum
    monkeypatch.setattr(probability.math, "fsum", lambda _values: math.inf)
    with pytest.raises(ValueError):
        probability.RawProbabilityMass(
            values=(1.0,),
            total=1.0,
            residual_from_one=0.0,
            positive_indices=(0,),
        )
    monkeypatch.setattr(probability.math, "fsum", original_fsum)

    for malformed_indices in ([0], (True,)):
        with pytest.raises(TypeError):
            probability.RawProbabilityMass(
                values=(1.0,),
                total=1.0,
                residual_from_one=0.0,
                positive_indices=malformed_indices,
            )
    assert torch.equal(generator.get_state(), initial_rng_state)

def test_mps011_qt_incomplete_kraus_mass_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt
    import torch

    incomplete = (
        math.sqrt(0.75)
        * torch.eye(2, dtype=torch.complex128, device="cpu"),
    )
    monkeypatch.setattr(
        qt,
        "_collapse_kraus",
        lambda _term, _dt_ns, *, device: incomplete,
    )
    generator = torch.Generator(device="cpu")
    generator.manual_seed(1101)
    state_before = generator.get_state().clone()

    with pytest.raises(ValueError):
        qt._sample_collapse_terms(
            _one_site_product_mps(level=0),
            {
                "dt_ns": 1.0,
                "terms": [
                    {
                        "kind": "collapse",
                        "operator_family": "T1",
                        "support": [0],
                        "coefficient": 1.0,
                    }
                ],
            },
            device="cpu",
            generator=generator,
        )
    assert torch.equal(generator.get_state(), state_before)


def test_mps011_qt_exact_incomplete_kraus_mass_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt
    import torch

    incomplete = (
        math.sqrt(0.75)
        * torch.eye(2, dtype=torch.complex128, device="cpu"),
    )
    monkeypatch.setattr(
        qt,
        "_collapse_kraus",
        lambda _term, _dt_ns, *, device: incomplete,
    )

    with pytest.raises(ValueError):
        qt._apply_collapse_terms_to_branches(
            [((), 1.0, _one_site_product_mps(level=0))],
            {
                "terms": [
                    {
                        "kind": "collapse",
                        "operator_family": "T1",
                        "support": [0],
                        "coefficient": 1.0,
                    }
                ]
            },
            device="cpu",
            max_branches=4,
            dt_ns=1.0,
        )


def test_mps006_qt_exact_singleton_partitions_do_not_accumulate_raw_norm_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    raw_masses = iter(
        (
            math.nextafter(1.0, 0.0),
            math.nextafter(1.0, math.inf),
            math.nextafter(1.0, math.inf),
            math.nextafter(1.0, math.inf),
        )
    )
    monkeypatch.setattr(
        qt,
        "_collapse_kraus",
        lambda _term, _dt_ns, *, device: (object(),),
    )
    monkeypatch.setattr(qt, "mps_norm_squared", lambda _state: next(raw_masses))

    result = qt._apply_collapse_terms_to_branches(
        [((), 1.0, _MutationState())],
        {
            "terms": [
                {
                    "kind": "collapse",
                    "operator_family": family,
                    "support": [0],
                    "coefficient": 1.0,
                }
                for family in ("T2", "T1", "T2", "T1")
            ]
        },
        device="cpu",
        max_branches=4,
        dt_ns=1.0,
    )

    assert len(result) == 1
    assert result[0][1] == 1.0


def test_mps006_qt_exact_branch_weight_conditions_on_raw_partition_total(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    raw = (
        math.nextafter(0.25, math.inf),
        math.nextafter(0.75, math.inf),
    )
    raw_total = math.fsum(raw)
    parent_weight = 0.5
    expected = tuple(
        float(
            Fraction.from_float(parent_weight)
            * Fraction.from_float(value)
            / Fraction.from_float(raw_total)
        )
        for value in raw
    )
    raw_masses = iter(raw)
    monkeypatch.setattr(
        qt,
        "_collapse_kraus",
        lambda _term, _dt_ns, *, device: (object(), object()),
    )
    monkeypatch.setattr(qt, "mps_norm_squared", lambda _state: next(raw_masses))

    result = qt._apply_collapse_terms_to_branches(
        [((), parent_weight, _MutationState())],
        {
            "terms": [
                {
                    "kind": "collapse",
                    "operator_family": "T1",
                    "support": [0],
                    "coefficient": 1.0,
                }
            ]
        },
        device="cpu",
        max_branches=4,
        dt_ns=1.0,
    )

    assert [weight for _bits, weight, _state in result] == list(expected)
    assert [
        state.multiply_factors for _bits, _weight, state in result
    ] == [[1.0 / (value**0.5)] for value in raw]


def _qt_exact_measurement_layout():
    from error_coupling_simulator.frontend.axis1_record_layout import (
        AXIS1_SCHEDULE_RECORD_LAYOUT_SCHEMA,
        Axis1MeasurementBoundaryLayout,
        Axis1ScheduleRecordLayout,
    )

    boundary = Axis1MeasurementBoundaryLayout(
        substep_id="measurement:0",
        substep_index=0,
        operations=(),
        keys=("m0",),
        targets=(0,),
        bases=("Z",),
        reset_after=(False,),
        global_slice=(0, 1),
    )
    return Axis1ScheduleRecordLayout(
        schema=AXIS1_SCHEDULE_RECORD_LAYOUT_SCHEMA,
        source_hash="phase4a-fixture",
        schedule_schema="phase4a-fixture",
        boundaries=(boundary,),
        measurement_keys=("m0",),
        measurement_targets=(0,),
        measurement_bases=("Z",),
        reset_after=(False,),
        detectors=(),
        observables=(),
    )


def test_mps006_qt_exact_measurement_conditions_on_raw_partition_total(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    raw = (
        math.nextafter(0.25, math.inf),
        math.nextafter(0.75, math.inf),
    )
    raw_total = math.fsum(raw)
    expected = [
        float(Fraction.from_float(value) / Fraction.from_float(raw_total))
        for value in raw
    ]
    raw_masses = iter(raw)

    def fake_project(state: Any, **_kwargs: Any) -> tuple[Any, float]:
        return state.copy(), next(raw_masses)

    monkeypatch.setattr(qt, "_project_z_mps", fake_project)

    result = qt._execute_program(
        {
            "program": {
                "num_qubits": 1,
                "substeps": [
                    {
                        "substep_id": "measurement:0",
                        "substep_kind": "measurement",
                        "route": "dense_local",
                        "route_reason": "phase4a_fixture",
                        "support": [0],
                        "operation_records": [
                            {"measurement_keys": ["m0"], "targets": [0]}
                        ],
                        "terms": [
                            {
                                "kind": "measurement_boundary",
                                "operator_family": "MEASURE",
                                "coefficient": None,
                            }
                        ],
                        "dt_ns": 1.0,
                    }
                ],
            }
        },
        record_layout=_qt_exact_measurement_layout(),
        device="cpu",
        max_bond=None,
        max_branches=4,
        microstep_count=1,
        finite_step_order="first_order",
    )

    assert result["record_probabilities"] == expected
    assert result["total_probability"] == 1.0


def test_mps006_qt_exact_reset_conditions_on_raw_partition_total(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    raw = (
        math.nextafter(0.25, math.inf),
        math.nextafter(0.75, math.inf),
    )
    raw_total = math.fsum(raw)
    expected = [
        float(Fraction.from_float(value) / Fraction.from_float(raw_total))
        for value in raw
    ]
    raw_masses = iter(raw)

    def fake_project(state: Any, **_kwargs: Any) -> tuple[Any, float]:
        return state.copy(), next(raw_masses)

    monkeypatch.setattr(qt, "_project_z_mps", fake_project)
    result = qt._reset_branches_for_operations(
        [((), 1.0, _MutationState())],
        {
            "operation_records": [
                {
                    "name": "R",
                    "targets": [0],
                }
            ]
        },
        device="cpu",
        max_branches=4,
    )

    assert [weight for _bits, weight, _state in result] == expected


@pytest.mark.parametrize(
    "invalid_conditioned_weight",
    [
        pytest.param(math.nan, id="nan"),
        pytest.param(math.inf, id="positive-inf"),
        pytest.param(-_MIN_SUBNORMAL, id="negative"),
        pytest.param(math.nextafter(1.0, math.inf), id="above-one"),
    ],
)
def test_mps006_qt_exact_conditioned_weight_guard_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    invalid_conditioned_weight: float,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    monkeypatch.setattr(
        qt,
        "scaled_product_ratio",
        lambda *_args, **_kwargs: invalid_conditioned_weight,
    )

    with pytest.raises(ValueError, match=r"finite and lie in \[0, 1\]"):
        qt._qt_exact_conditioned_branch_weight(
            1.0,
            1.0,
            1.0,
            name="QT exact guard fixture",
        )


def test_mps006_qt_exact_conditioned_weight_accepts_closed_endpoints() -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    assert qt._qt_exact_conditioned_branch_weight(
        1.0,
        0.0,
        1.0,
        name="QT exact structural-zero fixture",
    ) == 0.0
    assert qt._qt_exact_conditioned_branch_weight(
        0.0,
        _MIN_SUBNORMAL,
        1.0,
        name="QT exact zero-parent fixture",
    ) == 0.0
    assert qt._qt_exact_conditioned_branch_weight(
        1.0,
        1.0,
        1.0,
        name="QT exact unit fixture",
    ) == 1.0


def test_mps006_qt_exact_conditioned_weight_rejects_positive_underflow() -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    with pytest.raises(ValueError, match="representable as a finite float64"):
        qt._qt_exact_conditioned_branch_weight(
            _MIN_SUBNORMAL,
            0.5,
            1.0,
            name="QT exact positive-underflow fixture",
        )


def test_mps011_qt_incomplete_measurement_mass_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt
    import torch

    monkeypatch.setattr(
        qt,
        "_project_z_mps",
        lambda state, **_kwargs: (state.copy(), 0.25),
    )
    generator = torch.Generator(device="cpu")
    generator.manual_seed(1102)
    state_before = generator.get_state().clone()

    with pytest.raises(ValueError):
        qt._sample_z_measurement(
            _one_site_product_mps(level=0),
            targets=[0],
            device="cpu",
            generator=generator,
        )
    assert torch.equal(generator.get_state(), state_before)


def test_mps011_mcwf_incomplete_measurement_mass_fails_before_rng(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as mcwf
    import torch

    observed_norms = iter((0.6, 0.3))
    monkeypatch.setattr(
        mcwf,
        "mps_norm_squared",
        lambda _state: next(observed_norms),
    )
    generator = torch.Generator(device="cpu")
    generator.manual_seed(41102)
    state_before = generator.get_state().clone()

    with pytest.raises(ValueError):
        mcwf._sample_one_site_level(
            _MutationState(),
            site=0,
            local_dim=2,
            device="cpu",
            generator=generator,
        )
    assert torch.equal(generator.get_state(), state_before)


def test_mps011_mcwf_preserves_raw_first_order_total_and_residual() -> None:
    """MCWF records a nonunit first-order mass; it must not apply QT completeness."""

    import torch

    from error_coupling_simulator.frontend.axis1_mcwf_mps_execution import (
        _sample_joint_jump_or_nojump,
    )

    # For |1>, x=gamma*dt=1/2:
    # p_nojump=(1-x/2)^2=9/16, p_jump=x=1/2,
    # total=17/16, residual=1/16.  The residual is the declared first-order
    # approximation error, not permission to renormalize the reported total.
    generator = torch.Generator(device="cpu")
    generator.manual_seed(1103)
    selected, evidence = _sample_joint_jump_or_nojump(
        _one_site_product_mps(level=1),
        {
            "terms": [
                {
                    "kind": "collapse",
                    "operator_family": "T1",
                    "support": [0],
                    "coefficient": math.sqrt(0.5),
                }
            ]
        },
        dt_ns=1.0,
        device="cpu",
        generator=generator,
        local_dims=(2,),
    )

    assert evidence["candidate_count"] == 2
    assert evidence["probability_mass"] == pytest.approx(17.0 / 16.0, abs=1.0e-15)
    assert evidence["probability_mass_residual"] == pytest.approx(
        1.0 / 16.0,
        abs=1.0e-15,
    )
    dense = selected.to_dense().detach().cpu().numpy().reshape(-1)
    assert float((dense.conj() @ dense).real) == pytest.approx(1.0, abs=1.0e-15)


def _measurement_reset_boundary():
    from error_coupling_simulator.frontend.axis1_record_layout import (
        Axis1MeasurementBoundaryLayout,
    )

    return Axis1MeasurementBoundaryLayout(
        substep_id="measurement:0",
        substep_index=0,
        operations=(),
        keys=("m0",),
        targets=(0,),
        bases=("Z",),
        reset_after=(True,),
        global_slice=(0, 1),
    )


def _run_mcwf_reset_mutation(
    route: str,
    state: _MutationState,
    *,
    monkeypatch: pytest.MonkeyPatch,
) -> _MutationState:
    import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as mcwf
    import torch

    if route == "standalone-reset":
        monkeypatch.setattr(
            mcwf,
            "_sample_one_site_level",
            lambda candidate, **_kwargs: (0, candidate),
        )
        generator = torch.Generator(device="cpu")
        generator.manual_seed(7001)
        return mcwf._sample_reset_for_operations_multilevel(
            state,
            {
                "operation_records": [
                    {
                        "name": "R",
                        "targets": [0],
                    }
                ]
            },
            local_dims=(2,),
            device="cpu",
            generator=generator,
        )
    if route == "measurement-reset":
        return mcwf._apply_measurement_reset_if_requested_multilevel(
            state,
            _measurement_reset_boundary(),
            outcome_levels=(0,),
            local_dims=(2,),
            device="cpu",
        )
    raise AssertionError(f"unknown fixture route {route!r}")


@pytest.mark.parametrize("route", ["standalone-reset", "measurement-reset"])
@pytest.mark.parametrize(
    "invalid_norm",
    [
        pytest.param(0.0, id="zero"),
        pytest.param(-_MIN_SUBNORMAL, id="negative"),
        pytest.param(math.nan, id="nan"),
        pytest.param(math.inf, id="positive-inf"),
    ],
)
def test_mps007_mcwf_reset_mutation_rejects_invalid_post_operation_norm(
    monkeypatch: pytest.MonkeyPatch,
    route: str,
    invalid_norm: float,
) -> None:
    import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as mcwf

    state = _MutationState()
    monkeypatch.setattr(mcwf, "mps_norm_squared", lambda _state: invalid_norm)

    with pytest.raises(ValueError):
        _run_mcwf_reset_mutation(route, state, monkeypatch=monkeypatch)
    assert state.multiply_factors == []


@pytest.mark.parametrize("route", ["standalone-reset", "measurement-reset"])
def test_mps007_mcwf_reset_mutation_accepts_minimum_positive_subnormal_norm(
    monkeypatch: pytest.MonkeyPatch,
    route: str,
) -> None:
    import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as mcwf

    state = _MutationState()
    monkeypatch.setattr(
        mcwf,
        "mps_norm_squared",
        lambda _state: _MIN_SUBNORMAL,
    )

    returned = _run_mcwf_reset_mutation(route, state, monkeypatch=monkeypatch)

    assert returned is state
    assert state.multiply_factors == [1.0 / math.sqrt(_MIN_SUBNORMAL)]
    assert math.isfinite(state.multiply_factors[0])
