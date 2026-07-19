"""Transitive semantic firewall for QT/MPS aggregate evidence."""

from __future__ import annotations

import copy
from typing import Any

import pytest


def _measurement_schedule():
    from error_coupling_simulator.frontend import (
        CircuitBuilder,
        circuit_ir_to_substep_schedule,
    )

    builder = CircuitBuilder(num_qubits=2)
    builder.measure((0, 1), key=("m0", "m1"), duration_ns=1.0)
    return circuit_ir_to_substep_schedule(builder.build())


def _unsupported_measurement_schedule():
    from error_coupling_simulator.frontend import (
        CircuitBuilder,
        circuit_ir_to_substep_schedule,
    )

    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key="mx", basis="X")
    return circuit_ir_to_substep_schedule(builder.build())


def _rehash(qt: Any, payload: dict[str, Any]) -> dict[str, Any]:
    payload["content_hash"] = qt._stable_payload_hash(payload)
    return payload


def _accepted_sweeps(monkeypatch: pytest.MonkeyPatch, qt: Any):
    from test_mps_qt_aggregate_binding import (
        _direct_child,
        _install_dense_record_oracle,
    )

    schedule = _measurement_schedule()
    _install_dense_record_oracle(monkeypatch, qt)
    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_restricted_execution_manifest",
        lambda schedule_arg, **kwargs: _direct_child(
            qt,
            schedule_arg,
            **kwargs,
        ),
    )
    bond = qt.axis1_qt_mps_bond_sweep_manifest(
        schedule,
        bond_values=(1, 2),
        convergence_record_probability_gate=0.0,
    )
    seed = qt.axis1_qt_mps_trajectory_seed_sweep_manifest(
        schedule,
        trajectory_count=5,
        rng_seeds=(3, 7),
        max_bond=2,
        seed_record_frequency_spread_gate=0.0,
        dense_record_frequency_gate=0.0,
    )
    return schedule, bond, seed


def _install_sweeps(
    monkeypatch: pytest.MonkeyPatch,
    qt: Any,
    *,
    bond: dict[str, Any],
    seed: dict[str, Any],
) -> None:
    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_bond_sweep_manifest",
        lambda *_args, **_kwargs: bond,
    )
    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_trajectory_seed_sweep_manifest",
        lambda *_args, **_kwargs: seed,
    )


def _bundle_request(qt: Any, schedule: Any) -> dict[str, Any]:
    return qt.axis1_qt_mps_restricted_evidence_bundle_manifest(
        schedule,
        bond_values=(1, 2),
        trajectory_count=5,
        rng_seeds=(3, 7),
        convergence_record_probability_gate=0.0,
        seed_record_frequency_spread_gate=0.0,
        dense_record_frequency_gate=0.0,
    )


def _install_fake_cuda(monkeypatch: pytest.MonkeyPatch, qt: Any) -> None:
    monkeypatch.setattr(qt, "_require_cuda_device", lambda _device: "cuda")
    monkeypatch.setattr(qt.torch.cuda, "empty_cache", lambda: None)
    monkeypatch.setattr(
        qt.torch.cuda,
        "reset_peak_memory_stats",
        lambda _device: None,
    )
    monkeypatch.setattr(qt.torch.cuda, "synchronize", lambda _device: None)
    monkeypatch.setattr(qt.torch.cuda, "max_memory_allocated", lambda _device: 1)
    monkeypatch.setattr(qt.torch.cuda, "max_memory_reserved", lambda _device: 1)


def _accepted_bundle(monkeypatch: pytest.MonkeyPatch, qt: Any):
    schedule, bond, seed = _accepted_sweeps(monkeypatch, qt)
    _install_sweeps(monkeypatch, qt, bond=bond, seed=seed)
    return schedule, _bundle_request(qt, schedule)


def _resource_request(qt: Any, schedule: Any) -> dict[str, Any]:
    return qt.axis1_qt_mps_resource_probe_manifest(
        schedule,
        bond_values=(1, 2),
        trajectory_count=5,
        rng_seeds=(3, 7),
        convergence_record_probability_gate=0.0,
        seed_record_frequency_spread_gate=0.0,
        dense_record_frequency_gate=0.0,
    )


def test_bundle_rejects_rehashed_bond_representability_forgery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule, bond, seed = _accepted_sweeps(monkeypatch, qt)
    forged = copy.deepcopy(bond)
    forged["representability"] = "forged_qt_aggregate"
    _rehash(qt, forged)
    _install_sweeps(monkeypatch, qt, bond=forged, seed=seed)

    with pytest.raises(ValueError):
        _bundle_request(qt, schedule)


def test_bundle_rejects_rehashed_seed_representability_forgery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule, bond, seed = _accepted_sweeps(monkeypatch, qt)
    forged = copy.deepcopy(seed)
    forged["representability"] = "forged_qt_aggregate"
    _rehash(qt, forged)
    _install_sweeps(monkeypatch, qt, bond=bond, seed=forged)

    with pytest.raises(ValueError):
        _bundle_request(qt, schedule)


def test_bundle_rejects_rehashed_false_bond_convergence_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule, bond, seed = _accepted_sweeps(monkeypatch, qt)
    forged = copy.deepcopy(bond)
    forged["convergence_policy"]["convergence_gate"]["passed"] = False
    _rehash(qt, forged)
    _install_sweeps(monkeypatch, qt, bond=forged, seed=seed)

    with pytest.raises(ValueError):
        _bundle_request(qt, schedule)


def test_bundle_rejects_rehashed_bond_gate_with_contradictory_numerics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule, bond, seed = _accepted_sweeps(monkeypatch, qt)
    forged = copy.deepcopy(bond)
    gate = forged["convergence_policy"]["convergence_gate"]
    gate["observed_max_abs_probability_difference"] = 1.0
    gate["passed"] = True
    gate["violations"] = ["record_probability_difference_exceeds_gate"]
    _rehash(qt, forged)
    _install_sweeps(monkeypatch, qt, bond=forged, seed=seed)

    with pytest.raises(ValueError):
        _bundle_request(qt, schedule)


def test_bundle_rejects_rehashed_failed_bond_run_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule, bond, seed = _accepted_sweeps(monkeypatch, qt)
    forged = copy.deepcopy(bond)
    forged["run_summaries"][0]["passed"] = False
    forged["run_summaries"][0]["verdict"] = "fail"
    _rehash(qt, forged)
    _install_sweeps(monkeypatch, qt, bond=forged, seed=seed)

    with pytest.raises(ValueError):
        _bundle_request(qt, schedule)


def test_bundle_rejects_rehashed_false_seed_spread_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule, bond, seed = _accepted_sweeps(monkeypatch, qt)
    forged = copy.deepcopy(seed)
    forged["seed_sweep_policy"]["seed_spread_gate"]["passed"] = False
    _rehash(qt, forged)
    _install_sweeps(monkeypatch, qt, bond=bond, seed=forged)

    with pytest.raises(ValueError):
        _bundle_request(qt, schedule)


def test_bundle_rejects_rehashed_seed_gate_with_contradictory_numerics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule, bond, seed = _accepted_sweeps(monkeypatch, qt)
    forged = copy.deepcopy(seed)
    gate = forged["seed_sweep_policy"]["seed_spread_gate"]
    gate["observed_max_record_frequency_spread"] = 1.0
    gate["passed"] = True
    gate["violations"] = ["seed_record_frequency_spread_exceeds_gate"]
    _rehash(qt, forged)
    _install_sweeps(monkeypatch, qt, bond=bond, seed=forged)

    with pytest.raises(ValueError):
        _bundle_request(qt, schedule)


def test_bundle_rejects_rehashed_failed_seed_run_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule, bond, seed = _accepted_sweeps(monkeypatch, qt)
    forged = copy.deepcopy(seed)
    forged["run_summaries"][0]["passed"] = False
    forged["run_summaries"][0]["verdict"] = "fail"
    _rehash(qt, forged)
    _install_sweeps(monkeypatch, qt, bond=bond, seed=forged)

    with pytest.raises(ValueError):
        _bundle_request(qt, schedule)


def test_resource_rejects_rehashed_false_bundle_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule, bundle = _accepted_bundle(monkeypatch, qt)
    forged = copy.deepcopy(bundle)
    forged["bundle_policy"]["accepted_as_restricted_bundle_evidence"] = False
    _rehash(qt, forged)
    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_restricted_evidence_bundle_manifest",
        lambda *_args, **_kwargs: forged,
    )
    _install_fake_cuda(monkeypatch, qt)

    with pytest.raises(ValueError):
        _resource_request(qt, schedule)


def test_resource_rejects_rehashed_nested_bond_gate_contradiction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule, bond, seed = _accepted_sweeps(monkeypatch, qt)
    _install_sweeps(monkeypatch, qt, bond=bond, seed=seed)
    bundle = _bundle_request(qt, schedule)
    forged = copy.deepcopy(bundle)
    forged["bond_sweep"] = copy.deepcopy(bond)
    gate = forged["bond_sweep"]["convergence_policy"]["convergence_gate"]
    gate["observed_max_abs_probability_difference"] = 1.0
    gate["passed"] = True
    gate["violations"] = ["record_probability_difference_exceeds_gate"]
    _rehash(qt, forged["bond_sweep"])
    _rehash(qt, forged)
    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_restricted_evidence_bundle_manifest",
        lambda *_args, **_kwargs: forged,
    )
    _install_fake_cuda(monkeypatch, qt)

    with pytest.raises(ValueError):
        _resource_request(qt, schedule)


def test_resource_rejects_rehashed_bundle_representability_forgery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule, bundle = _accepted_bundle(monkeypatch, qt)
    forged = copy.deepcopy(bundle)
    forged["representability"] = "forged_qt_bundle"
    _rehash(qt, forged)
    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_restricted_evidence_bundle_manifest",
        lambda *_args, **_kwargs: forged,
    )
    _install_fake_cuda(monkeypatch, qt)

    with pytest.raises(ValueError):
        _resource_request(qt, schedule)


@pytest.mark.parametrize("nested_name", ["bond_sweep", "trajectory_seed_sweep"])
def test_resource_rejects_rehashed_failed_nested_sweep(
    monkeypatch: pytest.MonkeyPatch,
    nested_name: str,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule, bundle = _accepted_bundle(monkeypatch, qt)
    forged = copy.deepcopy(bundle)
    forged[nested_name]["passed"] = False
    forged[nested_name]["verdict"] = "fail"
    _rehash(qt, forged[nested_name])
    _rehash(qt, forged)
    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_restricted_evidence_bundle_manifest",
        lambda *_args, **_kwargs: forged,
    )
    _install_fake_cuda(monkeypatch, qt)

    with pytest.raises(ValueError):
        _resource_request(qt, schedule)


@pytest.mark.parametrize("nested_name", ["bond_sweep", "trajectory_seed_sweep"])
def test_resource_rejects_rehashed_nested_representability_forgery(
    monkeypatch: pytest.MonkeyPatch,
    nested_name: str,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule, bundle = _accepted_bundle(monkeypatch, qt)
    forged = copy.deepcopy(bundle)
    forged[nested_name]["representability"] = "forged_nested_sweep"
    _rehash(qt, forged[nested_name])
    _rehash(qt, forged)
    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_restricted_evidence_bundle_manifest",
        lambda *_args, **_kwargs: forged,
    )
    _install_fake_cuda(monkeypatch, qt)

    with pytest.raises(ValueError):
        _resource_request(qt, schedule)


def test_resource_rejects_rehashed_blocked_bundle_promotion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule = _unsupported_measurement_schedule()
    blocked = qt.axis1_qt_mps_restricted_evidence_bundle_manifest(
        schedule,
        bond_values=(1, 2),
        trajectory_count=5,
        rng_seeds=(3, 7),
    )
    assert blocked["passed"] is False
    forged = copy.deepcopy(blocked)
    forged["passed"] = True
    forged["verdict"] = "pass"
    forged["bundle_policy"]["accepted_as_restricted_bundle_evidence"] = True
    forged["claims_qt_mps_backend_execution"] = True
    for nested_name in ("bond_sweep", "trajectory_seed_sweep"):
        forged[nested_name]["claims_qt_mps_backend_execution"] = True
        _rehash(qt, forged[nested_name])
    _rehash(qt, forged)
    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_restricted_evidence_bundle_manifest",
        lambda *_args, **_kwargs: forged,
    )
    _install_fake_cuda(monkeypatch, qt)

    with pytest.raises(ValueError):
        qt.axis1_qt_mps_resource_probe_manifest(
            schedule,
            bond_values=(1, 2),
            trajectory_count=5,
            rng_seeds=(3, 7),
        )
