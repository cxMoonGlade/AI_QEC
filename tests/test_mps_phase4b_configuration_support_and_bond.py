from __future__ import annotations

"""CPU RED falsifiers for MPS-008, MPS-009, and MPS-010.

The tests deliberately trap the first CUDA or nested-child call.  Invalid
public controls must be rejected by their owning interface before that trap.
The exact-bond reference is a hand-written cut-product oracle and does not
reuse either frontend implementation.
"""

import ast
from itertools import product
import math
from typing import Any

import pytest


def _one_site_measurement_schedule():
    from error_coupling_simulator.frontend import (
        CircuitBuilder,
        circuit_ir_to_substep_schedule,
    )

    builder = CircuitBuilder(num_qubits=1)
    builder.measure((0,), key=("m0",), duration_ns=1.0)
    return circuit_ir_to_substep_schedule(builder.build())


@pytest.fixture(scope="module")
def schedule():
    return _one_site_measurement_schedule()


def _unexpected_cuda_or_child(*_args: Any, **_kwargs: Any) -> Any:
    raise AssertionError("invalid public control reached CUDA or a nested child")


_QT_DIRECT_INVALID_CONTROLS = (
    ("max_branches", True),
    ("microstep_count", 1.5),
    ("finite_step_order", 1),
    ("rng_seed", "7"),
    ("dense_oracle_certification", 1),
)
@pytest.mark.parametrize(
    ("control", "invalid"),
    _QT_DIRECT_INVALID_CONTROLS,
    ids=lambda value: repr(value),
)
def test_mps008_qt_direct_rejects_invalid_control_before_cuda(
    monkeypatch: pytest.MonkeyPatch,
    schedule: Any,
    control: str,
    invalid: Any,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    monkeypatch.setattr(qt, "_require_cuda_device", _unexpected_cuda_or_child)
    with pytest.raises(TypeError):
        qt.axis1_qt_mps_restricted_execution_manifest(
            schedule,
            **{control: invalid},
        )


_MCWF_DIRECT_INVALID_CONTROLS = (
    ("local_dims", [2.0]),
    ("microstep_count", "2"),
    ("finite_step_order", b"first_order"),
    ("trajectory_count", 2.5),
    ("rng_seed", True),
    ("initial_levels", [False]),
    ("leaked_readout_b", "0.5"),
)
@pytest.mark.parametrize(
    ("control", "invalid"),
    _MCWF_DIRECT_INVALID_CONTROLS,
    ids=lambda value: repr(value),
)
def test_mps008_mcwf_direct_rejects_invalid_control_before_cuda(
    monkeypatch: pytest.MonkeyPatch,
    schedule: Any,
    control: str,
    invalid: Any,
) -> None:
    import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as mcwf

    monkeypatch.setattr(mcwf, "_require_cuda_device", _unexpected_cuda_or_child)
    with pytest.raises(TypeError):
        mcwf.axis1_mcwf_mps_state_record_execution_manifest(
            schedule,
            **{control: invalid},
        )


@pytest.mark.parametrize("control", ("microstep_count", "trajectory_count"))
def test_mps008_mcwf_direct_rejects_nonpositive_count_before_cuda(
    monkeypatch: pytest.MonkeyPatch,
    schedule: Any,
    control: str,
) -> None:
    import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as mcwf

    monkeypatch.setattr(mcwf, "_require_cuda_device", _unexpected_cuda_or_child)
    with pytest.raises(ValueError):
        mcwf.axis1_mcwf_mps_state_record_execution_manifest(
            schedule,
            **{control: 0},
        )


_QT_AGGREGATE_INVALID_CONTROLS = (
    ("bond", "max_branches", True),
    ("trajectory", "rng_seeds", (1, 2.5)),
    ("bundle", "trajectory_count", True),
)
@pytest.mark.parametrize(
    ("route", "control", "invalid"),
    _QT_AGGREGATE_INVALID_CONTROLS,
    ids=lambda value: repr(value),
)
def test_mps008_qt_aggregate_rejects_invalid_control_before_child(
    monkeypatch: pytest.MonkeyPatch,
    schedule: Any,
    route: str,
    control: str,
    invalid: Any,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    common = {
        "bond": {
            "bond_values": (1, 2),
        },
        "trajectory": {
            "trajectory_count": 2,
            "rng_seeds": (1, 2),
        },
        "bundle": {
            "bond_values": (1, 2),
            "trajectory_count": 2,
            "rng_seeds": (1, 2),
        },
    }[route]
    kwargs = {**common, control: invalid}
    if route == "bond":
        target = qt.axis1_qt_mps_bond_sweep_manifest
        monkeypatch.setattr(
            qt,
            "axis1_qt_mps_restricted_execution_manifest",
            _unexpected_cuda_or_child,
        )
    elif route == "trajectory":
        target = qt.axis1_qt_mps_trajectory_seed_sweep_manifest
        monkeypatch.setattr(
            qt,
            "axis1_qt_mps_restricted_execution_manifest",
            _unexpected_cuda_or_child,
        )
    else:
        target = qt.axis1_qt_mps_restricted_evidence_bundle_manifest
        monkeypatch.setattr(
            qt,
            "axis1_qt_mps_bond_sweep_manifest",
            _unexpected_cuda_or_child,
        )
    with pytest.raises(TypeError):
        target(schedule, **kwargs)


_QT_RESOURCE_INVALID_CONTROLS = (
    ("microstep_count", "1"),
)
@pytest.mark.parametrize(
    ("control", "invalid"),
    _QT_RESOURCE_INVALID_CONTROLS,
    ids=lambda value: repr(value),
)
def test_mps008_qt_resource_probe_rejects_invalid_control_before_cuda(
    monkeypatch: pytest.MonkeyPatch,
    schedule: Any,
    control: str,
    invalid: Any,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    monkeypatch.setattr(qt, "_require_cuda_device", _unexpected_cuda_or_child)
    kwargs = {
        "bond_values": (1, 2),
        "trajectory_count": 2,
        "rng_seeds": (1, 2),
        control: invalid,
    }
    with pytest.raises(TypeError):
        qt.axis1_qt_mps_resource_probe_manifest(schedule, **kwargs)


_QT_CARRIER_INVALID_CONTROLS = (
    ("max_branches", "2"),
)
@pytest.mark.parametrize(
    ("control", "invalid"),
    _QT_CARRIER_INVALID_CONTROLS,
    ids=lambda value: repr(value),
)
def test_mps008_qt_carrier_rejects_invalid_passthrough_before_child(
    monkeypatch: pytest.MonkeyPatch,
    schedule: Any,
    control: str,
    invalid: Any,
) -> None:
    import error_coupling_simulator.frontend.axis1_carrier_execution as carrier
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_restricted_execution_manifest",
        _unexpected_cuda_or_child,
    )
    with pytest.raises(TypeError):
        carrier.axis1_carrier_execution_manifest(
            schedule,
            execution_backend_contract=(
                carrier.AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT
            ),
            execution_backend_options={control: invalid},
        )


_MCWF_CARRIER_INVALID_CONTROLS = (
    ("local_dims", [True]),
)
@pytest.mark.parametrize(
    ("control", "invalid"),
    _MCWF_CARRIER_INVALID_CONTROLS,
    ids=lambda value: repr(value),
)
def test_mps008_mcwf_carrier_rejects_invalid_passthrough_before_cuda(
    monkeypatch: pytest.MonkeyPatch,
    schedule: Any,
    control: str,
    invalid: Any,
) -> None:
    import error_coupling_simulator.frontend.axis1_carrier_execution as carrier

    monkeypatch.setattr(carrier, "_require_cuda_device", _unexpected_cuda_or_child)
    with pytest.raises(TypeError):
        carrier.axis1_carrier_execution_manifest(
            schedule,
            execution_backend_contract=(
                carrier.AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
            ),
            execution_backend_options={control: invalid},
        )


class _IndexOnly:
    def __init__(self, value: int) -> None:
        self.value = value

    def __index__(self) -> int:
        return self.value

    def __int__(self) -> int:
        raise AssertionError("lossy int coercion must not be used")


_QT_HOSTILE_PUBLIC_CONTROLS = (
    ("direct", "device", 7, TypeError),
    ("direct", "device", "", ValueError),
    ("direct", "max_bond", 2.0, TypeError),
    ("direct", "max_branches", True, TypeError),
    ("direct", "max_record_materialization_outcomes", "8", TypeError),
    ("direct", "microstep_count", 1.5, TypeError),
    ("direct", "finite_step_order", b"first_order", TypeError),
    ("direct", "worst_cut_discarded_weight_gate", math.nan, ValueError),
    ("direct", "total_discarded_weight_gate", "0.1", TypeError),
    ("direct", "trajectory_count", True, TypeError),
    ("direct", "rng_seed", "7", TypeError),
    ("direct", "dense_oracle_certification", 1, TypeError),
    ("bond", "bond_values", (1, 2.5), TypeError),
    ("bond", "bond_values", (2, 2), ValueError),
    ("bond", "device", b"cuda", TypeError),
    ("bond", "max_branches", "4", TypeError),
    ("bond", "max_record_materialization_outcomes", True, TypeError),
    ("bond", "microstep_count", 1.5, TypeError),
    ("bond", "finite_step_order", 1, TypeError),
    ("bond", "convergence_record_probability_gate", math.nan, ValueError),
    ("bond", "worst_cut_discarded_weight_gate", True, TypeError),
    ("bond", "total_discarded_weight_gate", math.inf, ValueError),
    ("bond", "dense_oracle_certification", 1, TypeError),
    ("trajectory", "trajectory_count", True, TypeError),
    ("trajectory", "rng_seeds", (1, "2"), TypeError),
    ("trajectory", "rng_seeds", (1, 1), ValueError),
    ("trajectory", "device", 3, TypeError),
    ("trajectory", "max_bond", "2", TypeError),
    ("trajectory", "max_record_materialization_outcomes", 8.0, TypeError),
    ("trajectory", "microstep_count", "1", TypeError),
    ("trajectory", "finite_step_order", False, TypeError),
    ("trajectory", "worst_cut_discarded_weight_gate", math.nan, ValueError),
    ("trajectory", "total_discarded_weight_gate", "0", TypeError),
    ("trajectory", "seed_record_frequency_spread_gate", math.inf, ValueError),
    ("trajectory", "dense_record_frequency_gate", -math.inf, ValueError),
    ("bundle", "bond_values", (1, True), TypeError),
    ("bundle", "trajectory_count", 2.5, TypeError),
    ("bundle", "rng_seeds", (1, "2"), TypeError),
    ("bundle", "device", b"cuda", TypeError),
    ("bundle", "max_branches", True, TypeError),
    ("bundle", "max_record_materialization_outcomes", "8", TypeError),
    ("bundle", "microstep_count", 1.5, TypeError),
    ("bundle", "finite_step_order", 1, TypeError),
    ("bundle", "convergence_record_probability_gate", math.nan, ValueError),
    ("bundle", "seed_record_frequency_spread_gate", "0.1", TypeError),
    ("bundle", "dense_record_frequency_gate", math.inf, ValueError),
    ("bundle", "worst_cut_discarded_weight_gate", True, TypeError),
    ("bundle", "total_discarded_weight_gate", -math.inf, ValueError),
    ("resource", "bond_values", (1, 2.0), TypeError),
    ("resource", "trajectory_count", True, TypeError),
    ("resource", "rng_seeds", (1, "2"), TypeError),
    ("resource", "device", 4, TypeError),
    ("resource", "max_branches", 1.5, TypeError),
    ("resource", "max_record_materialization_outcomes", "8", TypeError),
    ("resource", "microstep_count", True, TypeError),
    ("resource", "finite_step_order", 1, TypeError),
    ("resource", "convergence_record_probability_gate", math.nan, ValueError),
    ("resource", "seed_record_frequency_spread_gate", "0.1", TypeError),
    ("resource", "dense_record_frequency_gate", math.inf, ValueError),
    ("resource", "worst_cut_discarded_weight_gate", True, TypeError),
    ("resource", "total_discarded_weight_gate", -math.inf, ValueError),
    ("resource", "min_peak_allocated_gib", math.nan, ValueError),
    ("resource", "min_peak_reserved_gib", "1", TypeError),
)


@pytest.mark.parametrize(
    ("route", "control", "invalid", "error_type"),
    _QT_HOSTILE_PUBLIC_CONTROLS,
)
def test_mps008_all_qt_public_controls_reject_before_cuda_or_child(
    monkeypatch: pytest.MonkeyPatch,
    schedule: Any,
    route: str,
    control: str,
    invalid: Any,
    error_type: type[Exception],
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    base_kwargs = {
        "direct": {},
        "bond": {"bond_values": (1, 2)},
        "trajectory": {"trajectory_count": 2, "rng_seeds": (1, 2)},
        "bundle": {
            "bond_values": (1, 2),
            "trajectory_count": 2,
            "rng_seeds": (1, 2),
        },
        "resource": {
            "bond_values": (1, 2),
            "trajectory_count": 2,
            "rng_seeds": (1, 2),
        },
    }
    targets = {
        "direct": qt.axis1_qt_mps_restricted_execution_manifest,
        "bond": qt.axis1_qt_mps_bond_sweep_manifest,
        "trajectory": qt.axis1_qt_mps_trajectory_seed_sweep_manifest,
        "bundle": qt.axis1_qt_mps_restricted_evidence_bundle_manifest,
        "resource": qt.axis1_qt_mps_resource_probe_manifest,
    }
    if route in {"direct", "resource"}:
        monkeypatch.setattr(qt, "_require_cuda_device", _unexpected_cuda_or_child)
    elif route in {"bond", "trajectory"}:
        monkeypatch.setattr(
            qt,
            "axis1_qt_mps_restricted_execution_manifest",
            _unexpected_cuda_or_child,
        )
    else:
        monkeypatch.setattr(
            qt,
            "axis1_qt_mps_bond_sweep_manifest",
            _unexpected_cuda_or_child,
        )
    kwargs = {**base_kwargs[route], control: invalid}

    with pytest.raises(error_type):
        targets[route](schedule, **kwargs)


_MCWF_HOSTILE_PUBLIC_CONTROLS = (
    ("device", 7, TypeError),
    ("local_dims", [2.0], TypeError),
    ("max_bond", "2", TypeError),
    ("worst_cut_discarded_weight_gate", math.nan, ValueError),
    ("total_discarded_weight_gate", True, TypeError),
    ("microstep_count", "1", TypeError),
    ("finite_step_order", b"first_order", TypeError),
    ("trajectory_count", 2.5, TypeError),
    ("rng_seed", True, TypeError),
    ("initial_levels", [0.0], TypeError),
    ("leaked_readout_b", "0.5", TypeError),
    ("mass_residual_budget", math.inf, ValueError),
)


@pytest.mark.parametrize(
    ("control", "invalid", "error_type"),
    _MCWF_HOSTILE_PUBLIC_CONTROLS,
)
def test_mps008_mcwf_direct_controls_reject_before_cuda(
    monkeypatch: pytest.MonkeyPatch,
    schedule: Any,
    control: str,
    invalid: Any,
    error_type: type[Exception],
) -> None:
    import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as mcwf

    monkeypatch.setattr(mcwf, "_require_cuda_device", _unexpected_cuda_or_child)

    with pytest.raises(error_type):
        mcwf.axis1_mcwf_mps_state_record_execution_manifest(
            schedule,
            **{control: invalid},
        )


_CARRIER_HOSTILE_PUBLIC_CONTROLS = (
    ("qt", "device", 7, TypeError),
    ("qt", "max_bond", 2.0, TypeError),
    ("qt", "max_branches", "2", TypeError),
    ("qt", "max_record_materialization_outcomes", True, TypeError),
    ("qt", "microstep_count", 1.5, TypeError),
    ("qt", "finite_step_order", 1, TypeError),
    ("qt", "worst_cut_discarded_weight_gate", math.nan, ValueError),
    ("qt", "total_discarded_weight_gate", "0.1", TypeError),
    ("qt", "trajectory_count", 2.5, TypeError),
    ("qt", "rng_seed", True, TypeError),
    ("qt", "dense_oracle_certification", 1, TypeError),
    ("mcwf", "device", b"cuda", TypeError),
    ("mcwf", "local_dims", [2.0], TypeError),
    ("mcwf", "initial_levels", [False], TypeError),
    ("mcwf", "leaked_readout_b", "0.5", TypeError),
    ("mcwf", "max_bond", 2.0, TypeError),
    ("mcwf", "microstep_count", "1", TypeError),
    ("mcwf", "finite_step_order", b"first_order", TypeError),
    ("mcwf", "trajectory_count", 2.5, TypeError),
    ("mcwf", "rng_seed", True, TypeError),
    ("mcwf", "worst_cut_discarded_weight_gate", math.nan, ValueError),
    ("mcwf", "total_discarded_weight_gate", "0.1", TypeError),
    ("mcwf", "mass_residual_budget", math.inf, ValueError),
)


@pytest.mark.parametrize(
    ("route", "control", "invalid", "error_type"),
    _CARRIER_HOSTILE_PUBLIC_CONTROLS,
)
def test_mps008_carrier_rejects_all_route_controls_before_boundary(
    monkeypatch: pytest.MonkeyPatch,
    schedule: Any,
    route: str,
    control: str,
    invalid: Any,
    error_type: type[Exception],
) -> None:
    import error_coupling_simulator.frontend.axis1_carrier_execution as carrier
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    if route == "qt":
        backend = carrier.AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT
        monkeypatch.setattr(
            qt,
            "axis1_qt_mps_restricted_execution_manifest",
            _unexpected_cuda_or_child,
        )
    else:
        backend = carrier.AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
        monkeypatch.setattr(
            carrier,
            "_require_cuda_device",
            _unexpected_cuda_or_child,
        )
    device = invalid if control == "device" else "cuda"
    options = {} if control == "device" else {control: invalid}

    with pytest.raises(error_type):
        carrier.axis1_carrier_execution_manifest(
            schedule,
            device=device,
            execution_backend_contract=backend,
            execution_backend_options=options,
        )


def test_mps008_operator_index_controls_remain_legal() -> None:
    from error_coupling_simulator.carrier.mps.controls import (
        normalize_mps_index,
        normalize_mps_index_sequence,
    )
    from error_coupling_simulator.carrier.mps.controls import (
        normalize_mps_max_bond,
    )

    assert normalize_mps_index(
        _IndexOnly(3), name="index_counter", minimum=1
    ) == 3
    assert normalize_mps_index_sequence(
        [_IndexOnly(2), _IndexOnly(4)], name="sequence_counter", minimum=1
    ) == (2, 4)
    assert normalize_mps_max_bond(_IndexOnly(5)) == 5


def test_mps008_index_sequence_rejects_noniterable_and_required_empty() -> None:
    from error_coupling_simulator.carrier.mps.controls import (
        normalize_mps_index_sequence,
    )

    for invalid in (7, "7", b"7", bytearray(b"7")):
        with pytest.raises(TypeError):
            normalize_mps_index_sequence(invalid, name="scalar sequence")
    with pytest.raises(ValueError):
        normalize_mps_index_sequence(
            (),
            name="required sequence",
            require_nonempty=True,
        )


@pytest.mark.parametrize(
    ("value", "bounds"),
    [
        pytest.param(-0.25, {"minimum": 0.0}, id="below-minimum"),
        pytest.param(1.25, {"maximum": 1.0}, id="above-maximum"),
    ],
)
def test_mps008_finite_real_rejects_out_of_bounds(
    value: float,
    bounds: dict[str, float],
) -> None:
    from error_coupling_simulator.carrier.mps.controls import (
        normalize_mps_finite_real,
    )

    with pytest.raises(ValueError):
        normalize_mps_finite_real(value, name="bounded real", **bounds)


def test_mps008_route_neutral_controls_pin_direct_boundary_semantics() -> None:
    from error_coupling_simulator.carrier.mps import controls

    assert controls.normalize_mps_bool(True, name="flag") is True
    assert controls.normalize_mps_bool(False, name="flag") is False
    for invalid_bool in (0, 1, "", None):
        with pytest.raises(TypeError):
            controls.normalize_mps_bool(invalid_bool, name="flag")

    for device in ("cpu", "cuda", "cuda:3"):
        assert controls.normalize_mps_device(device) == device
    for invalid_device in (None, 0, False):
        with pytest.raises(TypeError):
            controls.normalize_mps_device(invalid_device)
    with pytest.raises(ValueError):
        controls.normalize_mps_device("")

    assert controls.normalize_mps_index(0, name="index") == 0
    assert controls.normalize_mps_index(-3, name="index") == -3
    assert controls.normalize_mps_index(3, name="index", minimum=3) == 3
    with pytest.raises(ValueError):
        controls.normalize_mps_index(2, name="index", minimum=3)
    for invalid_index in (True, False, 3.0, "3", None):
        with pytest.raises(TypeError):
            controls.normalize_mps_index(invalid_index, name="index")

    assert controls.normalize_optional_mps_index(None, name="optional") is None
    assert controls.normalize_optional_mps_index(
        _IndexOnly(4),
        name="optional",
        minimum=1,
    ) == 4
    with pytest.raises(ValueError):
        controls.normalize_optional_mps_index(
            _IndexOnly(0),
            name="optional",
            minimum=1,
        )
    assert controls.normalize_mps_max_bond(None) is None
    assert controls.normalize_mps_max_bond(1) == 1
    with pytest.raises(TypeError):
        controls.normalize_mps_max_bond(None, allow_none=False)
    for invalid_bond, error_type in ((0, ValueError), (True, TypeError), (1.0, TypeError)):
        with pytest.raises(error_type):
            controls.normalize_mps_max_bond(invalid_bond)

    one_shot = (value for value in (_IndexOnly(2), 3))
    assert controls.normalize_mps_index_sequence(
        one_shot,
        name="sites",
        minimum=1,
        require_nonempty=True,
    ) == (2, 3)
    assert controls.normalize_mps_index_sequence(
        (),
        name="sites",
        require_nonempty=False,
    ) == ()
    assert controls.normalize_mps_index_sequence((), name="sites") == ()
    with pytest.raises(ValueError):
        controls.normalize_mps_index_sequence(
            (1, 0),
            name="sites",
            minimum=1,
        )

    assert controls.normalize_mps_choice(
        "exact",
        name="mode",
        choices=("exact", "sampled"),
    ) == "exact"
    with pytest.raises(TypeError):
        controls.normalize_mps_choice(
            1,
            name="mode",
            choices=("exact", "sampled"),
        )
    with pytest.raises(ValueError):
        controls.normalize_mps_choice(
            "other",
            name="mode",
            choices=("exact", "sampled"),
        )

    assert controls.normalize_mps_finite_real(
        0,
        name="bounded",
        minimum=0.0,
        maximum=1.0,
    ) == 0.0
    assert controls.normalize_mps_finite_real(
        1,
        name="bounded",
        minimum=0.0,
        maximum=1.0,
    ) == 1.0
    for invalid_real, error_type in (
        (True, TypeError),
        ("0.5", TypeError),
        (math.nan, ValueError),
        (math.inf, ValueError),
        (-math.inf, ValueError),
    ):
        with pytest.raises(error_type):
            controls.normalize_mps_finite_real(
                invalid_real,
                name="bounded",
            )
    assert controls.normalize_optional_mps_nonnegative_real(
        None,
        name="optional real",
    ) is None
    assert controls.normalize_optional_mps_nonnegative_real(
        0.0,
        name="optional real",
    ) == 0.0
    with pytest.raises(ValueError):
        controls.normalize_optional_mps_nonnegative_real(
            -math.ulp(0.0),
            name="optional real",
        )


def test_mps008_qt_public_entry_accepts_operator_index_controls(
    monkeypatch: pytest.MonkeyPatch,
    schedule: Any,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    program = _coherent_program("COH_RX", (0,))
    monkeypatch.setattr(qt, "axis1_carrier_program_manifest", lambda *_a, **_k: program)
    monkeypatch.setattr(qt, "_require_cuda_device", lambda _device: "cpu")
    manifest = qt.axis1_qt_mps_restricted_execution_manifest(
        schedule,
        max_bond=_IndexOnly(2),
        max_branches=_IndexOnly(4),
        max_record_materialization_outcomes=_IndexOnly(8),
        microstep_count=_IndexOnly(1),
        trajectory_count=_IndexOnly(2),
        rng_seed=_IndexOnly(7),
    )

    assert manifest["max_bond"] == 2
    assert manifest["max_branches"] == 4
    assert manifest["max_record_materialization_outcomes"] == 8
    assert manifest["microstep_count"] == 1
    assert manifest["trajectory_count"] == 2
    assert manifest["rng_seed"] == 7
    assert manifest["execution_status"] == "blocked"


def test_mps008_mcwf_direct_accepts_operator_index_local_dims(
    monkeypatch: pytest.MonkeyPatch,
    schedule: Any,
) -> None:
    import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as mcwf

    monkeypatch.setattr(mcwf, "_require_cuda_device", lambda device: device)
    manifest = mcwf.axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        local_dims=[_IndexOnly(3)],
        device="cpu",
        max_bond=_IndexOnly(1),
    )

    assert manifest["local_hilbert_space"]["local_dims"] == [3]
    assert manifest["execution_status"] == "blocked"
    assert manifest["blocked_reason"] == (
        "mcwf_mps_multilevel_finite_bond_ledger_not_implemented"
    )


def test_mps008_mcwf_manifest_preserves_discarded_weight_gate_fields(
    monkeypatch: pytest.MonkeyPatch,
    schedule: Any,
) -> None:
    import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as mcwf

    monkeypatch.setattr(mcwf, "_require_cuda_device", lambda device: device)
    manifest = mcwf.axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        local_dims=(3,),
        device="cpu",
        max_bond=1,
        worst_cut_discarded_weight_gate=0.25,
        total_discarded_weight_gate=0.5,
    )

    assert manifest["worst_cut_discarded_weight_gate"] == 0.25
    assert manifest["total_discarded_weight_gate"] == 0.5
    assert {
        key for key in manifest if "execution_status" in key.casefold()
    } == {"execution_status"}


@pytest.mark.parametrize(
    ("invalid_device", "error_type"),
    [
        (7, TypeError),
        (b"cuda", TypeError),
        ("", ValueError),
    ],
)
def test_mps008_qt_direct_rejects_device_before_cuda(
    monkeypatch: pytest.MonkeyPatch,
    schedule: Any,
    invalid_device: Any,
    error_type: type[Exception],
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    monkeypatch.setattr(qt, "_require_cuda_device", _unexpected_cuda_or_child)

    with pytest.raises(error_type):
        qt.axis1_qt_mps_restricted_execution_manifest(
            schedule,
            device=invalid_device,
        )


_DENSE_CERTIFICATION_HOSTILE_CONTROLS = (
    ("device", 7, TypeError),
    ("device", b"cuda", TypeError),
    ("device", "", ValueError),
    ("dense_channel_max_dim", True, TypeError),
    ("dense_channel_max_dim", 2.5, TypeError),
    ("dense_channel_max_dim", "16", TypeError),
    ("dense_channel_max_dim", 0, ValueError),
)


@pytest.mark.parametrize("route", ["overcap", "channel"])
@pytest.mark.parametrize(
    ("control", "invalid", "error_type"),
    _DENSE_CERTIFICATION_HOSTILE_CONTROLS,
)
def test_mps008_dense_certification_rejects_controls_before_route_or_overcap_return(
    monkeypatch: pytest.MonkeyPatch,
    route: str,
    control: str,
    invalid: Any,
    error_type: type[Exception],
) -> None:
    import error_coupling_simulator.certify.axis1_mps as dense

    monkeypatch.setattr(dense, "_certify_channel_path", _unexpected_cuda_or_child)
    execution = {
        "trajectory_sampling": {
            "mode": "exact_branch_enumeration",
            "rng_seed_was_explicit": True,
            "trajectory_count": 1,
        }
    }
    program = {"requires_scalable_backend": route == "overcap"}
    kwargs = {control: invalid}

    with pytest.raises(error_type):
        dense.dense_jointL_record_certification(
            object(),
            execution,
            program,
            **kwargs,
        )


@pytest.mark.parametrize(
    ("device", "options", "control", "error_type"),
    [
        (7, {}, "device", TypeError),
        (b"cuda", {}, "device", TypeError),
        ("cuda", {"local_dims": [2.5]}, "local_dims", TypeError),
    ],
)
def test_mps008_carrier_auto_route_rejects_controls_before_cuda_or_vram_routing(
    monkeypatch: pytest.MonkeyPatch,
    schedule: Any,
    device: Any,
    options: dict[str, Any],
    control: str,
    error_type: type[Exception],
) -> None:
    import error_coupling_simulator.frontend.axis1_carrier_execution as carrier

    monkeypatch.setattr(carrier, "_require_cuda_device", _unexpected_cuda_or_child)
    monkeypatch.setattr(carrier, "_select_dense_or_mcwf", _unexpected_cuda_or_child)

    with pytest.raises(error_type):
        carrier.axis1_carrier_execution_manifest(
            schedule,
            device=device,
            execution_backend_contract=carrier.AXIS1_CARRIER_AUTO_BACKEND_CONTRACT,
            execution_backend_options=options,
        )



@pytest.mark.mutation_trampoline_incompatible
def test_mps009_mcwf_does_not_import_qt_private_support_predicate() -> None:
    import inspect
    import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as mcwf

    tree = ast.parse(inspect.getsource(mcwf))
    imported_support_predicates = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and str(node.module).endswith("axis1_qt_mps_execution")
        for alias in node.names
        if "hamiltonian" in alias.name and "supported" in alias.name
    }

    assert imported_support_predicates == set()


_COHERENT_FAMILIES = (
    ("COH_RX", (0,)),
    ("COH_RY", (0,)),
    ("COH_RZ", (0,)),
    ("COH_XX_YY", (0, 1)),
    ("COH_XX", (0, 1)),
    ("COH_YY", (0, 1)),
    ("COH_ZX", (0, 1)),
    ("COH_CROSSTALK_ZZ", (0, 1)),
)


def _coherent_program(family: str, support: tuple[int, ...]) -> dict[str, Any]:
    kind = "one_qubit_gate" if len(support) == 1 else "two_qubit_gate"
    return {
        "schema": "hand_written_coherent_support_fixture.v1",
        "content_hash": "a" * 64,
        "backend_contract": "hand_written_preflight_fixture",
        "requires_scalable_backend": False,
        "program": {
            "substeps": [
                {
                    "substep_id": "coh-0",
                    "substep_kind": kind,
                    "route": "hand_written_preflight_fixture",
                    "dt_ns": 1.0,
                    "terms": [
                        {
                            "kind": "hamiltonian",
                            "operator_family": family,
                            "support": list(support),
                            "coefficient": 0.125,
                        }
                    ],
                    "operation_records": [],
                }
            ]
        },
    }


@pytest.mark.parametrize(("family", "support"), _COHERENT_FAMILIES)
def test_mps009_qt_preflight_structurally_blocks_coherent_family(
    family: str,
    support: tuple[int, ...],
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    blocked = qt._unsupported_substeps(_coherent_program(family, support))

    assert blocked == [
        {
            "substep_id": "coh-0",
            "substep_kind": (
                "one_qubit_gate" if len(support) == 1 else "two_qubit_gate"
            ),
            "reason": f"unsupported_hamiltonian_family:{family}",
        }
    ]


def test_mps009_mcwf_preflight_retains_all_coherent_families() -> None:
    import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as mcwf

    for family, support in _COHERENT_FAMILIES:
        dims = tuple(2 for _ in range(max(support) + 1))
        assert mcwf._unsupported_substeps(
            _coherent_program(family, support),
            local_dims=dims,
        ) == []


def test_mps009_mcwf_preflight_retains_fsim_phase() -> None:
    import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as mcwf

    assert mcwf._unsupported_substeps(
        _coherent_program("FSIM_PHASE", (0, 1)),
        local_dims=(2, 2),
    ) == []


@pytest.mark.parametrize(
    "family",
    [
        pytest.param("BOGUS", id="unknown-non-control-family"),
        pytest.param("CTRL_NOT_REGISTERED", id="unknown-two-site-control-gate"),
    ],
)
def test_mps009_mcwf_preflight_blocks_unknown_hamiltonian_family(
    family: str,
) -> None:
    import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as mcwf

    blocked = mcwf._unsupported_substeps(
        _coherent_program(family, (0, 1)),
        local_dims=(2, 2),
    )

    assert blocked == [
        {
            "substep_id": "coh-0",
            "substep_kind": "two_qubit_gate",
            "reason": f"unsupported_mcwf_hamiltonian_family:{family}",
        }
    ]


def test_mps009_qt_public_manifest_returns_structured_coherent_blocker(
    monkeypatch: pytest.MonkeyPatch,
    schedule: Any,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    program = _coherent_program("COH_RX", (0,))
    monkeypatch.setattr(qt, "axis1_carrier_program_manifest", lambda *_a, **_k: program)
    monkeypatch.setattr(qt, "_require_cuda_device", lambda _device: "cpu")
    monkeypatch.setattr(qt, "_execute_program", _unexpected_cuda_or_child)

    manifest = qt.axis1_qt_mps_restricted_execution_manifest(schedule)

    assert manifest["execution_status"] == "blocked"
    assert manifest["blocked_reason"] == "unsupported_hamiltonian_family:COH_RX"
    assert manifest["qt_mps_backend_executed"] is False
    assert manifest["passed"] is False


def _independent_exact_bond_oracle(local_dims: tuple[int, ...]) -> int:
    """Maximum possible Schmidt rank over every open-chain cut."""

    if len(local_dims) <= 1:
        return 1
    return max(
        min(math.prod(local_dims[:cut]), math.prod(local_dims[cut:]))
        for cut in range(1, len(local_dims))
    )


@pytest.mark.parametrize("num_sites", range(1, 9))
def test_mps010_qubit_exact_bond_matches_independent_cut_product_oracle(
    num_sites: int,
) -> None:
    from error_coupling_simulator.carrier.mps.state import (
        exact_mps_bond_dimension,
    )

    expected = _independent_exact_bond_oracle((2,) * num_sites)
    assert exact_mps_bond_dimension((2,) * num_sites) == expected


def test_mps010_reference_oracle_detects_retired_ceil_formula() -> None:
    mismatched = {
        num_sites
        for num_sites in range(1, 9)
        if _independent_exact_bond_oracle((2,) * num_sites)
        != 2 ** math.ceil(num_sites / 2)
    }

    assert mismatched == {1, 3, 5, 7}


def test_mps010_mixed_dims_match_exhaustive_cut_product_oracle() -> None:
    from error_coupling_simulator.carrier.mps.state import (
        exact_mps_bond_dimension,
    )

    fixtures = [
        dims
        for width in range(1, 6)
        for dims in product(range(2, 5), repeat=width)
    ]
    observed = [exact_mps_bond_dimension(dims) for dims in fixtures]
    expected = [_independent_exact_bond_oracle(dims) for dims in fixtures]

    assert observed == expected


def test_mps010_qt_three_site_cap_two_is_exact_bond_sufficient() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_exact_branch_truncation_events,
        build_mps_truncation_ledger,
    )

    ledger = build_mps_truncation_ledger(
        max_bond=2,
        local_dims=(2, 2, 2),
        max_observed_bond=2,
        truncation_events=[],
        aggregation=aggregate_exact_branch_truncation_events(
            [], expected_gate_occurrences=[]
        ),
    )

    assert ledger["exact_bond_dimension_sufficient"] == 2
    assert ledger["exact_bond_policy"] == (
        "finite_cap_at_or_above_conservative_exact_sufficient_bond"
    )
    assert ledger["accepted_as_exact_bond_representation"] is True
