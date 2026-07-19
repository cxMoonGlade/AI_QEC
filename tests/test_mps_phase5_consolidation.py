from __future__ import annotations

"""Architecture gates for the restricted-MPS mechanics consolidation."""

import ast
import importlib
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "error_coupling_simulator"
FRONTEND = SRC / "frontend"
MPS = SRC / "carrier" / "mps"
CERTIFY = SRC / "certify"


def _imports(path: Path) -> list[ast.Import | ast.ImportFrom]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]


def _imported_module(node: ast.Import | ast.ImportFrom) -> tuple[str, ...]:
    if isinstance(node, ast.Import):
        return tuple(alias.name for alias in node.names)
    return (() if node.module is None else (node.module,))


@pytest.mark.mutation_trampoline_incompatible
def test_phase5_capped_two_site_module_is_a_hard_cut_without_frontend_shim() -> None:
    assert not (FRONTEND / "_mps_actual_split.py").exists()
    assert (MPS / "capped_two_site.py").is_file()

    module = importlib.import_module(
        "error_coupling_simulator.carrier.mps.capped_two_site"
    )
    assert module.apply_capped_two_site_unitary.__module__ == module.__name__
    controls = importlib.import_module(
        "error_coupling_simulator.carrier.mps.controls"
    )
    assert controls.normalize_mps_max_bond.__module__ == controls.__name__
    state = importlib.import_module(
        "error_coupling_simulator.carrier.mps.state"
    )
    for name in (
        "commit_mps_candidate_",
        "exact_mps_bond_dimension",
        "max_mps_bond",
        "mps_norm_squared",
    ):
        assert getattr(state, name).__module__ == state.__name__

    for path in (
        FRONTEND / "axis1_qt_mps_execution.py",
        FRONTEND / "axis1_mcwf_mps_execution.py",
        FRONTEND / "axis1_carrier_execution.py",
    ):
        assert "_mps_actual_split" not in path.read_text(encoding="utf-8")


@pytest.mark.mutation_trampoline_incompatible
def test_phase5_qt_and_mcwf_adapters_do_not_import_each_other() -> None:
    paths = {
        "qt": FRONTEND / "axis1_qt_mps_execution.py",
        "mcwf": FRONTEND / "axis1_mcwf_mps_execution.py",
    }
    forbidden = {
        "qt": "axis1_mcwf_mps_execution",
        "mcwf": "axis1_qt_mps_execution",
    }
    for route, path in paths.items():
        imported = {
            module
            for node in _imports(path)
            for module in _imported_module(node)
        }
        assert not any(forbidden[route] in module for module in imported)


def test_phase5_neutral_carrier_program_helpers_preserve_adapter_semantics() -> None:
    module = importlib.import_module(
        "error_coupling_simulator.frontend.axis1_carrier_program"
    )
    assert {
        name: module.axis1_reset_basis(name)
        for name in ("R", "RZ", "RX", "RY", "H")
    } == {"R": "Z", "RZ": "Z", "RX": "X", "RY": "Y", "H": None}

    summary = module.axis1_carrier_substep_summary(
        {
            "substep_id": "s0",
            "substep_kind": "idle",
            "route": "dense_local",
            "route_reason": "fixture",
            "support": [0, 1],
            "dt_ns": 4.0,
            "terms": [
                {
                    "kind": "hamiltonian",
                    "operator_family": "ZZ",
                    "coefficient": 0.25,
                },
                {
                    "kind": "collapse",
                    "operator_family": "T1",
                    "coefficient": 0.0,
                },
                {
                    "kind": "collapse",
                    "operator_family": "T2",
                    "coefficient": 0.5,
                },
                {
                    "kind": "measurement_boundary",
                    "operator_family": "MEASURE",
                    "coefficient": None,
                },
            ],
        }
    )
    assert summary == {
        "substep_id": "s0",
        "substep_kind": "idle",
        "route": "dense_local",
        "route_reason": "fixture",
        "support": [0, 1],
        "dt_ns": 4.0,
        "hamiltonian_operator_families": ["ZZ"],
        "hamiltonian_term_count": 1,
        "nonzero_collapse_operator_families": ["T2"],
        "nonzero_collapse_term_count": 1,
        "measurement_boundary_count": 1,
    }


def test_phase5_carrier_mps_modules_do_not_depend_on_frontend_or_certification() -> None:
    for path in sorted(MPS.glob("*.py")):
        imported = {
            module
            for node in _imports(path)
            for module in _imported_module(node)
        }
        assert not any(
            "frontend" in module or "certif" in module
            for module in imported
        ), path


@pytest.mark.mutation_trampoline_incompatible
def test_phase5_dense_reference_does_not_import_executor_reset_policy() -> None:
    path = CERTIFY / "axis1_mps.py"
    for node in _imports(path):
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.module.endswith("axis1_mcwf_mps_execution"):
            imported_names = {alias.name for alias in node.names}
            assert "_reset_basis" not in imported_names
        if node.module.endswith("axis1_qt_mps_execution"):
            raise AssertionError(
                "dense MCWF certification must not import QT executor policy"
            )


def test_phase5_exact_bond_documentation_uses_cut_product_not_ceil() -> None:
    text = (FRONTEND / "README.md").read_text(encoding="utf-8")
    assert "2**ceil(n_sites/2)" not in text
    assert "cut-product" in text


def test_phase5_three_authoritative_docs_pin_non_scientific_carrier_role() -> None:
    paths = (
        MPS / "README.md",
        ROOT / "docs" / "ARCHITECTURE.md",
        ROOT / "docs" / "SIMULATOR.md",
    )
    required = (
        "execution-mechanics library",
        "no state-, Record-, or LER-faithfulness claim",
        "not a registered scientific Carrier",
        "PEPS remains the trajectory-carrier frontier",
        "PEPO remains the retained research Carrier",
    )
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for phrase in required:
            assert phrase in text, f"{path}: missing {phrase!r}"


def test_phase5_registry_keeps_mechanics_inside_existing_restricted_route() -> None:
    registry = json.loads(
        (ROOT / "docs" / "service_status.json").read_text(encoding="utf-8")
    )
    owners = [
        service
        for service in registry["services"]
        if any(
            str(owner).startswith("src/error_coupling_simulator/carrier/mps/")
            for owner in service.get("owners", ())
        )
    ]
    assert [service["id"] for service in owners] == ["restricted_axis1_1d_mps"]
    service = owners[0]
    assert any(
        str(owner).startswith("src/error_coupling_simulator/frontend/")
        for owner in service["owners"]
    )
    assert "not a registered scientific carrier" in service["note"].lower()


def test_phase5_carrier_execution_rejects_unknown_backend_before_cuda(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from error_coupling_simulator.frontend import (
        CircuitBuilder,
        circuit_ir_to_substep_schedule,
    )

    carrier = importlib.import_module(
        "error_coupling_simulator.frontend.axis1_carrier_execution"
    )
    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key="m0")
    schedule = circuit_ir_to_substep_schedule(builder.build())
    cuda_calls = []

    def unexpected_cuda(_device: str) -> str:
        cuda_calls.append(_device)
        raise AssertionError("unknown backend reached CUDA")

    monkeypatch.setattr(carrier, "_require_cuda_device", unexpected_cuda)

    with pytest.raises(ValueError):
        carrier.axis1_carrier_execution_manifest(
            schedule,
            execution_backend_contract="unknown_backend",
        )
    assert cuda_calls == []


def test_phase5_dense_probe_returns_authenticated_qubit_cap_block_without_gpu(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from error_coupling_simulator.frontend import (
        CircuitBuilder,
        circuit_ir_to_substep_schedule,
    )

    carrier = importlib.import_module(
        "error_coupling_simulator.frontend.axis1_carrier_execution"
    )
    builder = CircuitBuilder(num_qubits=carrier.AXIS1_STATE_MAX_EXACT_QUBITS + 1)
    builder.tick()
    schedule = circuit_ir_to_substep_schedule(builder.build())

    monkeypatch.setattr(carrier, "_require_cuda_device", lambda _device: "cuda")

    def fail_if_dense_execution_starts(*_args, **_kwargs):
        raise AssertionError("qubit-cap block must precede dense GPU execution")

    monkeypatch.setattr(
        carrier,
        "axis1_state_evolution_evidence_manifest",
        fail_if_dense_execution_starts,
    )
    monkeypatch.setattr(
        carrier,
        "axis1_measurement_record_evidence_manifest",
        fail_if_dense_execution_starts,
    )

    manifest = carrier.axis1_carrier_execution_manifest(schedule)

    assert manifest["verdict"] == "fail"
    assert manifest["passed"] is False
    assert manifest["blocked_reason"] == "dense_jointL_probe_qubit_cap_exceeded"
    assert manifest["dense_probe_executed"] is False
    assert manifest["state_execution"] is None
    assert manifest["record_execution"] is None
    assert manifest["carrier_program"]["requires_scalable_backend"] is False
    assert manifest["content_hash"] == carrier._stable_payload_hash(manifest)


@pytest.mark.parametrize(
    "override",
    [
        {"kind": "unknown"},
        {"support": (-1,)},
        {"coefficient": float("nan")},
    ],
)
def test_phase5_carrier_term_rejects_invalid_public_values(
    override: dict[str, object],
) -> None:
    carrier_program = importlib.import_module(
        "error_coupling_simulator.frontend.axis1_carrier_program"
    )
    kwargs = {
        "kind": "hamiltonian",
        "support": (0,),
        "operator_family": "z",
        "coefficient": 1.0,
        "coefficient_source": "fixture",
        "provenance": {},
    }
    kwargs.update(override)

    with pytest.raises(ValueError):
        carrier_program.Axis1CarrierTerm(**kwargs)


@pytest.mark.parametrize(
    "override",
    [
        {"backend_contract": "unknown_backend"},
        {"schema": "error_coupling_simulator.frontend.carrier_program.v0"},
    ],
)
def test_phase5_carrier_program_rejects_unknown_backend_or_schema(
    override: dict[str, object],
) -> None:
    carrier_program = importlib.import_module(
        "error_coupling_simulator.frontend.axis1_carrier_program"
    )
    kwargs = {
        "source_kind": "fixture",
        "source_hash": "fixture-hash",
        "num_qubits": 1,
        "site_order": (0,),
        "substeps": (),
    }
    kwargs.update(override)

    with pytest.raises(ValueError):
        carrier_program.Axis1CarrierProgram(**kwargs)


def test_phase5_qt_two_qubit_tableau_cache_is_cpu_only_and_copy_safe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import stim
    import torch

    qt = importlib.import_module(
        "error_coupling_simulator.frontend.axis1_qt_mps_execution"
    )
    qt._cached_two_qubit_gate_matrix_numpy.cache_clear()
    original_circuit = stim.Circuit
    constructions: list[str] = []

    def counted_circuit(text: str):
        constructions.append(text)
        return original_circuit(text)

    monkeypatch.setattr(stim, "Circuit", counted_circuit)
    try:
        first = qt._two_qubit_gate_matrix("CZ", device="cpu")
        second = qt._two_qubit_gate_matrix("cz", device="cpu")

        assert constructions == ["CZ 0 1"]
        assert first.device.type == second.device.type == "cpu"
        assert first.dtype == second.dtype == torch.complex128
        assert first.data_ptr() != second.data_ptr()
        torch.testing.assert_close(first, second, rtol=0.0, atol=0.0)

        first.zero_()
        assert torch.count_nonzero(second).item() > 0
    finally:
        qt._cached_two_qubit_gate_matrix_numpy.cache_clear()
