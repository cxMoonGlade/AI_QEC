from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pytest
import torch

import error_coupling_simulator.certify.axis1_mps as certification
import error_coupling_simulator.certify.mcwf_operator_reference as reference
import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as execution
from error_coupling_simulator.numerics import NUMERICAL_ZERO


pytestmark = pytest.mark.skipif(
    not torch.cuda.is_available(),
    reason="MCWF operator certification is GPU-only",
)

DEVICE = "cuda"
COEFFICIENT = 0.137

ONE_QUBIT_CONTROLS = (
    "C_XYZ",
    "C_ZYX",
    "H",
    "H_XY",
    "H_XZ",
    "S",
    "S_DAG",
    "SQRT_X",
    "SQRT_X_DAG",
    "SQRT_Y",
    "SQRT_Y_DAG",
    "SQRT_Z",
    "SQRT_Z_DAG",
    "X",
    "Y",
    "Z",
)
TWO_QUBIT_CONTROLS = (
    "CX",
    "CY",
    "CZ",
    "ISWAP",
    "ISWAP_DAG",
    "SQRT_XX",
    "SQRT_XX_DAG",
    "SQRT_YY",
    "SQRT_YY_DAG",
    "SQRT_ZZ",
    "SQRT_ZZ_DAG",
    "SWAP",
    "XCX",
    "XCY",
    "XCZ",
    "YCX",
    "YCY",
    "YCZ",
)
OTHER_HAMILTONIANS = (
    ("ZZ", (3, 4), (0, 1)),
    ("FSIM_PHASE", (3, 4), (0, 1)),
    ("LEAK_EXCHANGE_12", (4,), (0,)),
    ("LEAK_EXCHANGE_11_02", (4, 4), (0, 1)),
    ("LEAK_MOBILITY_12_21", (4, 4), (0, 1)),
    ("LEAK_TRANSPORT_30_12", (4, 4), (0, 1)),
    ("LEAK_TRANSPORT_31_22", (4, 4), (0, 1)),
    ("LEAK_COND_PHASE_LEFT2_RIGHTZ", (4, 4), (0, 1)),
    ("LEAK_COND_PHASE_LEFTZ_RIGHT2", (4, 4), (0, 1)),
    ("COH_RX", (4,), (0,)),
    ("COH_RY", (4,), (0,)),
    ("COH_RZ", (4,), (0,)),
    ("COH_XX", (3, 4), (0, 1)),
    ("COH_YY", (3, 4), (0, 1)),
    ("COH_ZX", (3, 4), (0, 1)),
    ("COH_XX_YY", (3, 4), (0, 1)),
    ("COH_CROSSTALK_ZZ", (3, 4), (0, 1)),
)
COLLAPSE_FAMILIES = (
    ("T1", (4,), (0,)),
    ("T1_UP", (4,), (0,)),
    ("T2", (4,), (0,)),
    ("RD", (4,), (0,)),
    ("LEAK_SEEP_21", (4,), (0,)),
    ("LEAK_HEAT_12", (4,), (0,)),
    ("CORR_RELAX", (3, 4), (0, 1)),
)


def _hamiltonian_term(family: str) -> dict:
    return {
        "kind": "hamiltonian",
        "operator_family": family,
        "coefficient": COEFFICIENT,
    }


def _collapse_term(family: str) -> dict:
    return {
        "kind": "collapse",
        "operator_family": family,
        "coefficient": COEFFICIENT,
    }


def _assert_same_operator(actual: torch.Tensor, expected: np.ndarray) -> None:
    actual_numpy = actual.detach().cpu().numpy()
    assert actual_numpy.shape == expected.shape
    assert np.all(np.isfinite(actual_numpy))
    assert np.all(np.isfinite(expected))
    assert float(np.max(np.abs(actual_numpy - expected))) <= NUMERICAL_ZERO


@pytest.mark.parametrize("gate", ONE_QUBIT_CONTROLS)
def test_all_one_qubit_controls_match_certifier_local_reference(gate: str):
    term = _hamiltonian_term(f"CTRL_{gate}")
    dims = (4,)
    support = (0,)
    actual = execution._hamiltonian_matrix_for_term(
        term,
        support=support,
        local_dims=dims,
        device=DEVICE,
    )
    expected = reference.reference_hamiltonian_matrix_for_term(
        term,
        support=support,
        local_dims=dims,
    )
    _assert_same_operator(actual, expected)
    assert torch.count_nonzero(actual[2:, :]).item() == 0
    assert torch.count_nonzero(actual[:, 2:]).item() == 0
    assert np.count_nonzero(expected[2:, :]) == 0
    assert np.count_nonzero(expected[:, 2:]) == 0


@pytest.mark.parametrize("gate", TWO_QUBIT_CONTROLS)
def test_all_two_qubit_controls_match_certifier_local_reference(gate: str):
    term = _hamiltonian_term(f"CTRL_{gate}")
    dims = (3, 4)
    support = (0, 1)
    actual = execution._hamiltonian_matrix_for_term(
        term,
        support=support,
        local_dims=dims,
        device=DEVICE,
    )
    expected = reference.reference_hamiltonian_matrix_for_term(
        term,
        support=support,
        local_dims=dims,
    )
    _assert_same_operator(actual, expected)
    computational = {left * dims[1] + right for left in (0, 1) for right in (0, 1)}
    leaked = sorted(set(range(dims[0] * dims[1])) - computational)
    assert torch.count_nonzero(actual[leaked, :]).item() == 0
    assert torch.count_nonzero(actual[:, leaked]).item() == 0
    assert np.count_nonzero(expected[leaked, :]) == 0
    assert np.count_nonzero(expected[:, leaked]) == 0


@pytest.mark.parametrize("family,dims,support", OTHER_HAMILTONIANS)
def test_all_noncontrol_hamiltonians_match_certifier_local_reference(
    family: str,
    dims: tuple[int, ...],
    support: tuple[int, ...],
):
    term = _hamiltonian_term(family)
    actual = execution._hamiltonian_matrix_for_term(
        term,
        support=support,
        local_dims=dims,
        device=DEVICE,
    )
    expected = reference.reference_hamiltonian_matrix_for_term(
        term,
        support=support,
        local_dims=dims,
    )
    _assert_same_operator(actual, expected)
    assert float(torch.max(torch.abs(actual - actual.conj().T)).item()) <= NUMERICAL_ZERO


@pytest.mark.parametrize("family,dims,support", COLLAPSE_FAMILIES)
def test_all_collapse_operators_match_certifier_local_reference(
    family: str,
    dims: tuple[int, ...],
    support: tuple[int, ...],
):
    term = _collapse_term(family)
    if len(support) == 1:
        actual = execution._collapse_operator(
            term,
            local_dim=dims[support[0]],
            device=DEVICE,
        )
    else:
        actual = execution._joint_collapse_operator(
            term,
            support,
            local_dims=dims,
            device=DEVICE,
        )
    expected = reference.reference_collapse_operator_for_term(
        term,
        support=support,
        local_dims=dims,
    )
    _assert_same_operator(actual, expected)


def test_reference_inventory_covers_every_registered_mcwf_operator_family():
    fixture_hamiltonian_families = {
        *(f"CTRL_{gate}" for gate in ONE_QUBIT_CONTROLS),
        *(f"CTRL_{gate}" for gate in TWO_QUBIT_CONTROLS),
        *(family for family, _dims, _support in OTHER_HAMILTONIANS),
    }
    fixture_collapse_families = {
        family for family, _dims, _support in COLLAPSE_FAMILIES
    }
    production_hamiltonian_families = {
        *(f"CTRL_{gate}" for gate in execution.AXIS1_FRONTEND_ONE_QUBIT_CONTROL_GATES),
        *(f"CTRL_{gate}" for gate in execution.AXIS1_FRONTEND_TWO_QUBIT_CONTROL_GATES),
        "ZZ",
        "FSIM_PHASE",
        *execution._ONE_SITE_LEAKAGE_HAMILTONIAN_FAMILIES,
        *execution._TWO_SITE_LEAKAGE_HAMILTONIAN_LEVELS,
        *execution._TWO_SITE_CONDITIONAL_PHASE_FAMILIES,
        *execution.COHERENT_PAULI_FAMILIES,
    }
    reference_hamiltonian_families = {
        *(f"CTRL_{gate}" for gate in reference._ONE_QUBIT_CONTROLS),
        *(f"CTRL_{gate}" for gate in reference._TWO_QUBIT_CONTROLS),
        "ZZ",
        "FSIM_PHASE",
        "LEAK_EXCHANGE_12",
        *reference._TWO_SITE_LEAKAGE_LEVELS,
        "LEAK_COND_PHASE_LEFT2_RIGHTZ",
        "LEAK_COND_PHASE_LEFTZ_RIGHT2",
        *reference._ONE_SITE_COHERENT,
        *reference._TWO_SITE_COHERENT,
    }
    production_collapse_families = {
        *execution._ONE_SITE_COLLAPSE_FAMILIES,
        *execution.TWO_SITE_COLLAPSE_FAMILIES,
    }
    reference_collapse_families = {
        *reference._ONE_SITE_COLLAPSE,
        "CORR_RELAX",
    }
    assert fixture_hamiltonian_families == production_hamiltonian_families
    assert reference_hamiltonian_families == production_hamiltonian_families
    assert fixture_collapse_families == production_collapse_families
    assert reference_collapse_families == production_collapse_families
    assert len(production_hamiltonian_families) == 51
    assert len(production_collapse_families) == 7


@pytest.mark.mutation_trampoline_incompatible
def test_reference_module_has_only_absolute_stdlib_and_numpy_imports():
    source_path = Path(reference.__file__)
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imports.add(node.module or "")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id != "__import__"
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr != "import_module"
    allowed_roots = {"__future__", "math", "numbers", "typing", "numpy"}
    assert {name.split(".", 1)[0] for name in imports} <= allowed_roots
    assert not any(name.startswith("error_coupling_simulator") for name in imports)


def test_reference_structural_zero_masks_distinguish_padding_and_sparse_zeros():
    control = _hamiltonian_term("CTRL_Z")
    control_mask = reference.reference_structural_zero_mask_for_term(
        control,
        support=(0,),
        local_dims=(3,),
    )
    assert control_mask.shape == (3, 3)
    assert np.count_nonzero(control_mask[:2, :2]) == 0
    assert np.all(control_mask[2, :])
    assert np.all(control_mask[:, 2])

    two_site_control = _hamiltonian_term("CTRL_CZ")
    two_site_mask = reference.reference_structural_zero_mask_for_term(
        two_site_control,
        support=(0, 1),
        local_dims=(3, 4),
    )
    computational = {left * 4 + right for left in (0, 1) for right in (0, 1)}
    leaked = sorted(set(range(12)) - computational)
    assert two_site_mask.shape == (12, 12)
    assert (
        np.count_nonzero(
            two_site_mask[np.ix_(sorted(computational), sorted(computational))]
        )
        == 0
    )
    assert np.all(two_site_mask[leaked, :])
    assert np.all(two_site_mask[:, leaked])

    sparse = _hamiltonian_term("LEAK_EXCHANGE_12")
    sparse_reference = reference.reference_hamiltonian_matrix_for_term(
        sparse,
        support=(0,),
        local_dims=(3,),
    )
    sparse_mask = reference.reference_structural_zero_mask_for_term(
        sparse,
        support=(0,),
        local_dims=(3,),
    )
    assert np.array_equal(sparse_mask, sparse_reference == 0.0)

    zero = _collapse_term("T1")
    zero["coefficient"] = 0.0
    zero_mask = reference.reference_structural_zero_mask_for_term(
        zero,
        support=(0,),
        local_dims=(4,),
    )
    assert np.all(zero_mask)


@pytest.mark.parametrize(
    "builder,term,support,dims",
    (
        (
            reference.reference_hamiltonian_matrix_for_term,
            _hamiltonian_term("CTRL_NOT_REGISTERED"),
            (0,),
            (2,),
        ),
        (
            reference.reference_hamiltonian_matrix_for_term,
            _hamiltonian_term("COH_RX"),
            (0, 1),
            (2, 2),
        ),
        (
            reference.reference_collapse_operator_for_term,
            _collapse_term("T1"),
            (0, 1),
            (2, 2),
        ),
        (
            reference.reference_collapse_operator_for_term,
            _collapse_term("CORR_RELAX"),
            (0,),
            (2,),
        ),
    ),
)
def test_reference_fails_closed_on_unknown_family_or_wrong_arity(
    builder,
    term: dict,
    support: tuple[int, ...],
    dims: tuple[int, ...],
):
    with pytest.raises(ValueError):
        builder(term, support=support, local_dims=dims)


def test_hamiltonian_reference_rejects_non_hamiltonian_kind():
    term = _hamiltonian_term("ZZ")
    term["kind"] = "collapse"

    with pytest.raises(ValueError, match="requires kind='hamiltonian'"):
        reference.reference_hamiltonian_matrix_for_term(
            term,
            support=(0, 1),
            local_dims=(2, 2),
        )


@pytest.mark.parametrize("family", ("", None))
def test_hamiltonian_reference_rejects_empty_or_nontext_family(family):
    term = _hamiltonian_term("ZZ")
    term["operator_family"] = family

    with pytest.raises(TypeError, match="family must be nonempty text"):
        reference.reference_hamiltonian_matrix_for_term(
            term,
            support=(0, 1),
            local_dims=(2, 2),
        )


@pytest.mark.parametrize(
    "family,support,dims,error",
    (
        (
            "LEAK_EXCHANGE_12",
            (0,),
            (2,),
            "requires local_dim >= 3",
        ),
        (
            "LEAK_TRANSPORT_30_12",
            (0, 1),
            (3, 3),
            "levels are outside local_dims",
        ),
        (
            "LEAK_COND_PHASE_LEFT2_RIGHTZ",
            (0, 1),
            (2, 3),
            "requires left local_dim >= 3",
        ),
        (
            "LEAK_COND_PHASE_LEFTZ_RIGHT2",
            (0, 1),
            (3, 2),
            "requires right local_dim >= 3",
        ),
    ),
)
def test_hamiltonian_reference_rejects_insufficient_declared_levels(
    family: str,
    support: tuple[int, ...],
    dims: tuple[int, ...],
    error: str,
):
    with pytest.raises(ValueError, match=error):
        reference.reference_hamiltonian_matrix_for_term(
            _hamiltonian_term(family),
            support=support,
            local_dims=dims,
        )


def test_hamiltonian_reference_rejects_unknown_noncontrol_family():
    with pytest.raises(
        ValueError,
        match="unsupported certifier-local Hamiltonian family",
    ):
        reference.reference_hamiltonian_matrix_for_term(
            _hamiltonian_term("NOT_A_HAMILTONIAN"),
            support=(0,),
            local_dims=(2,),
        )


def test_collapse_reference_rejects_noncollapse_kind():
    term = _collapse_term("T1")
    term["kind"] = "hamiltonian"

    with pytest.raises(ValueError, match="requires kind='collapse'"):
        reference.reference_collapse_operator_for_term(
            term,
            support=(0,),
            local_dims=(2,),
        )


@pytest.mark.parametrize("family", ("", None))
def test_collapse_reference_rejects_empty_or_nontext_family(family):
    term = _collapse_term("T1")
    term["operator_family"] = family

    with pytest.raises(TypeError, match="family must be nonempty text"):
        reference.reference_collapse_operator_for_term(
            term,
            support=(0,),
            local_dims=(2,),
        )


@pytest.mark.parametrize(
    "family,error",
    (
        ("LEAK_SEEP_21", "requires local_dim >= 3"),
        ("LEAK_HEAT_12", "requires local_dim >= 3"),
    ),
)
def test_collapse_reference_rejects_insufficient_declared_levels(
    family: str,
    error: str,
):
    with pytest.raises(ValueError, match=error):
        reference.reference_collapse_operator_for_term(
            _collapse_term(family),
            support=(0,),
            local_dims=(2,),
        )


def test_collapse_reference_rejects_unknown_family():
    with pytest.raises(
        ValueError,
        match="unsupported certifier-local collapse family",
    ):
        reference.reference_collapse_operator_for_term(
            _collapse_term("NOT_A_COLLAPSE"),
            support=(0,),
            local_dims=(2,),
        )


@pytest.mark.parametrize("family", ("", None))
def test_structural_zero_mask_rejects_empty_or_nontext_family(family):
    term = _hamiltonian_term("ZZ")
    term["operator_family"] = family

    with pytest.raises(TypeError, match="family must be nonempty text"):
        reference.reference_structural_zero_mask_for_term(
            term,
            support=(0, 1),
            local_dims=(2, 2),
        )


def test_structural_zero_mask_rejects_nonoperator_kind():
    term = _collapse_term("T1")
    term["kind"] = "measurement"

    with pytest.raises(ValueError, match="requires Hamiltonian or collapse kind"):
        reference.reference_structural_zero_mask_for_term(
            term,
            support=(0,),
            local_dims=(2,),
        )


def test_structural_zero_mask_defensively_rejects_wrong_computational_arity(
    monkeypatch: pytest.MonkeyPatch,
):
    term = _hamiltonian_term("CTRL_Z")
    monkeypatch.setattr(
        reference,
        "reference_hamiltonian_matrix_for_term",
        lambda *_args, **_kwargs: np.zeros((8, 8), dtype=np.complex128),
    )

    with pytest.raises(ValueError, match="requires one- or two-site support"):
        reference.reference_structural_zero_mask_for_term(
            term,
            support=(0, 1, 2),
            local_dims=(2, 2, 2),
        )


def test_corr_relax_dense_oracle_uses_two_site_operator():
    term = _collapse_term("CORR_RELAX")
    term["support"] = [0, 1]
    substep = {
        "substep_id": "corr_relax_operator_route",
        "substep_kind": "idle",
        "dt_ns": 0.01,
        "terms": [term],
    }
    dims = (3, 4)
    window = (0, 1)
    dim = dims[0] * dims[1]
    lift = certification._make_lift_fn(window, dims, dim)

    hamiltonians, collapses = certification._window_oracle_operators(
        substep,
        window,
        dims,
        substep["dt_ns"],
        lift,
        device=DEVICE,
    )
    assert hamiltonians == []
    assert len(collapses) == 1
    expected = reference.reference_collapse_operator_for_term(
        term,
        support=window,
        local_dims=dims,
    )
    _assert_same_operator(collapses[0], expected)


@pytest.mark.parametrize("family", ("T1", "T1_UP", "T2", "RD"))
def test_mcwf_preflight_rejects_two_site_support_for_one_site_collapse(
    family: str,
):
    program = {
        "program": {
            "substeps": [
                {
                    "substep_id": "wrong_one_site_collapse_support",
                    "substep_kind": "idle",
                    "dt_ns": 1.0,
                    "terms": [
                        {
                            **_collapse_term(family),
                            "support": [0, 1],
                        }
                    ],
                }
            ]
        }
    }
    blockers = execution._unsupported_substeps(program, local_dims=(2, 2))
    assert blockers == [
        {
            "substep_id": "wrong_one_site_collapse_support",
            "substep_kind": "idle",
            "reason": f"one_site_collapse_requires_one_site_support:{family}",
        }
    ]
