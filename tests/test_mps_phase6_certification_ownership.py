from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "src" / "error_coupling_simulator" / "frontend"
CERTIFY = ROOT / "src" / "error_coupling_simulator" / "certify"


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_mcwf_mps_certification_has_one_evaluator_side_owner() -> None:
    old_owner = FRONTEND / "axis1_mcwf_dense_certification.py"
    new_owner = CERTIFY / "axis1_mps.py"

    assert not old_owner.exists(), "Phase 6 is a hard cut; the frontend shim must not exist"
    assert new_owner.is_file()


def test_mps_certification_does_not_depend_on_qt_execution() -> None:
    modules = _imported_modules(CERTIFY / "axis1_mps.py")

    assert not any("axis1_qt_mps" in module for module in modules)


def test_mcwf_execution_consumes_certify_result_at_the_composition_seam() -> None:
    source = (FRONTEND / "axis1_mcwf_mps_execution.py").read_text(encoding="utf-8")

    assert "from ..certify.axis1_mps import (" in source
    assert "axis1_mcwf_dense_certification" not in source


def test_public_mps_surfaces_do_not_claim_that_the_backend_is_unimplemented() -> None:
    paths = (
        FRONTEND / "README.md",
        FRONTEND / "axis1_carrier_execution.py",
    )
    stale_markers = (
        "qt_mps_backend_not_implemented",
        "mcwf_mps_backend_not_implemented",
        "contract_only_backend_not_implemented",
    )

    for path in paths:
        source = path.read_text(encoding="utf-8")
        for marker in stale_markers:
            assert marker not in source, f"stale MPS backend status {marker!r} in {path}"


def test_contract_only_modules_and_compatibility_aliases_are_hard_cut() -> None:
    for filename in ("axis1_mcwf_mps_contract.py", "axis1_qt_mps_contract.py"):
        assert not (FRONTEND / filename).exists()

    frontend_init = (FRONTEND / "__init__.py").read_text(encoding="utf-8")
    retired_symbols = (
        "AXIS1_CARRIER_MCWF_MPS_CONTRACT_ONLY_BACKEND_CONTRACT",
        "AXIS1_CARRIER_MCWF_MPS_CONTRACT_ONLY_REPRESENTABILITY",
        "AXIS1_MCWF_MPS_CONTRACT_SCHEMA",
        "AXIS1_QT_MPS_CONTRACT_SCHEMA",
        "axis1_mcwf_mps_state_record_contract_manifest",
        "axis1_qt_mps_state_record_contract_manifest",
    )
    for symbol in retired_symbols:
        assert symbol not in frontend_init


def test_contract_only_modules_are_absent_from_machine_owners_and_coverage() -> None:
    retired_paths = (
        "src/error_coupling_simulator/frontend/axis1_mcwf_mps_contract.py",
        "src/error_coupling_simulator/frontend/axis1_qt_mps_contract.py",
    )
    paths = (
        ROOT / "docs" / "service_status.json",
        ROOT / "tests" / "_support" / "restricted_mps_coverage_targets.json",
    )
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        serialized = json.dumps(payload, sort_keys=True)
        for retired_path in retired_paths:
            assert retired_path not in serialized


def test_machine_catalog_does_not_register_mps_as_a_scientific_carrier() -> None:
    catalog = json.loads(
        (ROOT / "docs" / "service_status.json").read_text(encoding="utf-8")
    )
    service = next(
        item for item in catalog["services"]
        if item["id"] == "restricted_axis1_1d_mps"
    )
    assert service["kind"] == "restricted_verification"

    node = next(item for item in catalog["flow"]["nodes"] if item["id"] == "mps")
    assert node["group"] == "Restricted verification routes"


def test_mps_split_payload_names_bond_dimension_not_numerical_rank() -> None:
    paths = (
        ROOT / "src" / "error_coupling_simulator" / "carrier" / "mps" / "capped_two_site.py",
        ROOT / "scripts" / "mps_actual_split_diagnostic.py",
        ROOT / "scripts" / "mps_three_leg_comparator.py",
    )
    retired = ("actual_kept_rank", "kept_rank_cap", "pre_truncation_rank")
    for path in paths:
        source = path.read_text(encoding="utf-8")
        for field in retired:
            assert field not in source, f"ambiguous retired field {field!r} in {path}"

    production = paths[0].read_text(encoding="utf-8")
    assert "actual_kept_bond_dimension" in production
    diagnostic = paths[1].read_text(encoding="utf-8")
    assert "pre_truncation_numerical_rank" in diagnostic
    assert "numerical_rank_absolute_threshold" in diagnostic


def _literal_dict_keys(node: ast.Dict) -> set[str]:
    return {
        key.value
        for key in node.keys
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    }


def test_hidden_level_and_jump_family_data_are_evaluator_only() -> None:
    path = FRONTEND / "axis1_mcwf_mps_execution.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    dictionaries = [node for node in ast.walk(tree) if isinstance(node, ast.Dict)]

    execution_payloads = [
        node for node in dictionaries if "measurement_records" in _literal_dict_keys(node)
    ]
    assert execution_payloads
    for payload in execution_payloads:
        keys = _literal_dict_keys(payload)
        assert "evaluator_only_diagnostics" in keys
        assert not {
            "level_records",
            "level_record_counts",
            "level_record_probabilities",
            "jump_family_counts",
        } & keys

    evaluator_payloads = [
        node
        for node in dictionaries
        if {
            "level_records",
            "level_record_counts",
            "level_record_probabilities",
            "jump_family_counts",
        } <= _literal_dict_keys(node)
    ]
    assert len(evaluator_payloads) == 1
    assert "schema" in _literal_dict_keys(evaluator_payloads[0])
