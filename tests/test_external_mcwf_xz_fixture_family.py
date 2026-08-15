"""F2/F3 neutral fixture, independent dense-oracle, and registry contracts."""

from __future__ import annotations

import ast
import copy
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import sys

import pytest


REPO = Path(__file__).resolve().parents[1]
BASELINE = REPO / "scripts" / "external_baselines"
FIXTURES = BASELINE / "fixtures"
PROTOCOL = BASELINE / "qutip_mcwf_xz_protocol.py"
DENSE_WORKER = BASELINE / "mcwf_xz_dense_worker.py"
PROJECT_ADAPTER = BASELINE / "run_qutip_mcwf_xz_comparison.py"
FAMILY_COMPARATOR = BASELINE / "run_mcwf_xz_fixture_family_comparison.py"
REGISTRY = FIXTURES / "mcwf_xz_comparison_registry.json"
FIXTURE_PATHS = {
    "f1": FIXTURES / "qutip_mcwf_xz_two_qubit_t1.json",
    "f2": FIXTURES / "qutip_mcwf_xz_two_qubit_pure_dephasing.json",
    "f3": FIXTURES / "qutip_mcwf_xz_two_qubit_thermal.json",
}


def _load_protocol():
    spec = importlib.util.spec_from_file_location("qutip_mcwf_xz_protocol", PROTOCOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_dense(monkeypatch):
    protocol = _load_protocol()
    monkeypatch.setitem(sys.modules, "qutip_mcwf_xz_protocol", protocol)
    spec = importlib.util.spec_from_file_location(
        "mcwf_xz_dense_worker_under_test", DENSE_WORKER
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return protocol, module


def _load_family_comparator(monkeypatch):
    protocol = _load_protocol()
    monkeypatch.setitem(sys.modules, "qutip_mcwf_xz_protocol", protocol)
    adapter_spec = importlib.util.spec_from_file_location(
        "run_qutip_mcwf_xz_comparison", PROJECT_ADAPTER
    )
    assert adapter_spec is not None and adapter_spec.loader is not None
    adapter = importlib.util.module_from_spec(adapter_spec)
    adapter_spec.loader.exec_module(adapter)
    monkeypatch.setitem(
        sys.modules, "run_qutip_mcwf_xz_comparison", adapter
    )
    family_spec = importlib.util.spec_from_file_location(
        "run_mcwf_xz_fixture_family_comparison_under_test", FAMILY_COMPARATOR
    )
    assert family_spec is not None and family_spec.loader is not None
    family = importlib.util.module_from_spec(family_spec)
    family_spec.loader.exec_module(family)
    return protocol, family


def _marginal(protocol, law, key, fixture):
    column = fixture["measurement_keys"].index(key)
    return protocol.binary_column_marginal(law, column=column)


def test_fixture_family_is_byte_pinned_and_matches_preregistered_exact_laws():
    protocol = _load_protocol()
    expected = {
        "f1": (0.5, 0.25, 0.75, 0.0),
        "f2": (0.5, 1.0, 0.625, 0.0),
        "f3": (0.5, 0.4, 0.75, 0.15),
    }

    for short_id, path in FIXTURE_PATHS.items():
        fixture = protocol.load_fixture(path)
        assert fixture["schema"] == (
            "error_coupling_simulator.neutral.mcwf_xz_fixture.v2"
        )
        assert protocol.fixture_sha256(path) == (
            protocol.EXPECTED_FIXTURE_SHA256_BY_ID[fixture["fixture_id"]]
        )
        law = protocol.analytic_binary_distribution(fixture)
        assert len(law) == 16
        assert math.fsum(law.values()) == pytest.approx(1.0, abs=1.0e-15)
        observed = tuple(
            _marginal(protocol, law, key, fixture)[(value,)]
            for key, value in (
                ("mx_before", 0),
                ("mz_before", 1),
                ("mx_after", 0),
                ("mz_after", 1),
            )
        )
        assert observed == pytest.approx(expected[short_id], abs=1.0e-15)


def test_registry_binds_five_statistics_per_fixture_and_family_alpha():
    protocol = _load_protocol()
    registry = protocol.load_comparison_registry(REGISTRY)

    assert registry["entry_count"] == 15
    assert registry["comparison_family_alpha"] == 0.01
    assert registry["per_entry_alpha"] == pytest.approx(0.01 / 15.0)
    assert protocol.multinomial_tv_radius(
        sample_count=2048,
        alphabet_size=16,
        alpha=registry["per_entry_alpha"],
    ) == pytest.approx(0.0670302388436366, abs=1.0e-15)
    assert 2.0 * protocol.multinomial_tv_radius(
        sample_count=2048,
        alphabet_size=16,
        alpha=registry["per_entry_alpha"] / 2.0,
    ) == pytest.approx(0.1365617560712202, abs=1.0e-15)
    assert protocol.multinomial_tv_radius(
        sample_count=2048,
        alphabet_size=2,
        alpha=registry["per_entry_alpha"],
    ) == pytest.approx(0.04421175841273293, abs=1.0e-15)

    for fixture_id in protocol.EXPECTED_FIXTURE_IDS:
        entries = protocol.comparison_entries_for_fixture(registry, fixture_id)
        assert len(entries) == 5
        assert sum(entry["view"] == "marginal" for entry in entries) == 2


def test_dense_worker_is_project_independent_and_uses_hand_typed_matrix_route():
    tree = ast.parse(DENSE_WORKER.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])

    assert "error_coupling_simulator" not in imported_roots
    assert imported_roots <= {
        "__future__",
        "argparse",
        "hashlib",
        "importlib",
        "json",
        "math",
        "numpy",
        "os",
        "pathlib",
        "platform",
        "qutip_mcwf_xz_protocol",
        "scipy",
        "sys",
        "tempfile",
        "typing",
    }
    source = DENSE_WORKER.read_text(encoding="utf-8")
    for forbidden in (
        "axis1_primitives",
        "compiled_program",
        "CircuitBuilder",
        "assemble_substep_channel",
    ):
        assert forbidden not in source
    assert "np.kron(collapse.conj(), collapse)" in source
    assert "expm(duration * generator)" in source


def test_family_comparator_uses_public_project_interfaces_and_registry_count():
    tree = ast.parse(FAMILY_COMPARATOR.read_text(encoding="utf-8"))
    project_imports = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module
        and node.module.startswith("error_coupling_simulator")
    }

    assert project_imports == {
        "error_coupling_simulator.frontend",
        "error_coupling_simulator.numerics",
    }
    source = FAMILY_COMPARATOR.read_text(encoding="utf-8")
    for forbidden in (
        "_collapse_operator",
        "_hamiltonian_matrix_for_term",
        "_measure_site_declared_basis",
    ):
        assert forbidden not in source
    assert '"registered_statistic_count"' in source


def test_family_comparator_reads_dense_and_qutip_record_shapes(monkeypatch):
    _protocol, family = _load_family_comparator(monkeypatch)
    expected = {(0, 1, 0, 0): 0.75, (1, 0, 1, 0): 0.25}

    assert family._law_from_worker_record(
        {
            "records": [[0, 1, 0, 0], [1, 0, 1, 0]],
            "probabilities": [0.75, 0.25],
        }
    ) == expected
    assert family._law_from_worker_record(
        {
            "binary_records": [[0, 1, 0, 0], [1, 0, 1, 0]],
            "binary_probabilities": [0.75, 0.25],
        }
    ) == expected


@pytest.mark.parametrize("fixture_name", ["f1", "f2", "f3"])
def test_dense_worker_matches_closed_form_and_preserves_structural_zeros(
    monkeypatch,
    fixture_name,
):
    protocol, dense = _load_dense(monkeypatch)
    report = dense.build_report(FIXTURE_PATHS[fixture_name])

    assert report["schema"] == dense.SCHEMA
    assert report["all_checks_passed"] is True
    assert report["construction"]["density_matrix_dimension"] == 4
    assert report["construction"]["liouvillian_dimension"] == 16
    assert report["closed_form_crosscheck"]["maximum_cell_difference"] <= 1.0e-9
    assert report["closed_form_crosscheck"]["structural_zeros_preserved"] is True
    assert report["runtime_provenance"]["project_program_consumed"] is False
    assert report["content_hash"] == protocol.canonical_content_hash(report)


def test_preregistered_corruptions_trip_directed_dense_laws(monkeypatch):
    protocol, dense = _load_dense(monkeypatch)
    marginal_radius = 0.04421175841273293

    f1 = protocol.load_fixture(FIXTURE_PATHS["f1"])
    f1_clean, _ = dense._record_distribution(f1)
    f1_wrong, _ = dense._record_distribution(
        f1,
        term_transform=lambda term: {**term, "family": "sigma_plus"},
    )
    assert protocol.total_variation(
        _marginal(protocol, f1_clean, "mz_before", f1),
        _marginal(protocol, f1_wrong, "mz_before", f1),
    ) == pytest.approx(0.75, abs=1.0e-12)

    f2 = protocol.load_fixture(FIXTURE_PATHS["f2"])
    f2_clean, _ = dense._record_distribution(f2)
    f2_wrong, _ = dense._record_distribution(
        f2,
        term_transform=lambda term: {
            **term,
            "generator_rate_per_ns": term["generator_rate_per_ns"] / 2.0,
        },
    )
    f2_separation = protocol.total_variation(
        _marginal(protocol, f2_clean, "mx_after", f2),
        _marginal(protocol, f2_wrong, "mx_after", f2),
    )
    assert f2_separation == pytest.approx(0.125, abs=1.0e-12)
    assert f2_separation > marginal_radius

    f3 = protocol.load_fixture(FIXTURE_PATHS["f3"])
    f3_clean, _ = dense._record_distribution(f3)
    removed_up, _ = dense._record_distribution(
        f3,
        term_transform=lambda term: None
        if term["family"] == "sigma_plus"
        else term,
    )
    assert protocol.total_variation(
        _marginal(protocol, f3_clean, "mz_after", f3),
        _marginal(protocol, removed_up, "mz_after", f3),
    ) == pytest.approx(0.15, abs=1.0e-12)


def test_project_program_binding_matches_fixture_families_rates_and_supports(
    monkeypatch,
):
    protocol, family = _load_family_comparator(monkeypatch)

    for path in FIXTURE_PATHS.values():
        fixture = protocol.load_fixture(path)
        schedule = family.adapter._schedule_from_fixture(fixture)
        program = family.axis1_carrier_program_manifest(
            schedule,
            backend_contract=(
                family.AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
            ),
        )
        binding = family._project_program_binding(fixture, schedule, program)
        assert binding["passed"] is True
        assert binding["source_hash_match"] is True
        assert len(binding["observed_evolution_layers"]) == 2
        assert all(
            layer["matches_fixture"]
            for layer in binding["observed_evolution_layers"]
        )


def test_registry_scoring_rejects_f2_and_f3_candidate_corruptions(monkeypatch):
    protocol, dense = _load_dense(monkeypatch)
    _protocol_again, family = _load_family_comparator(monkeypatch)
    registry = protocol.load_comparison_registry(REGISTRY)
    marginal_radius = 0.04421175841273293

    f2 = protocol.load_fixture(FIXTURE_PATHS["f2"])
    f2_clean, _ = dense._record_distribution(f2)
    f2_wrong, _ = dense._record_distribution(
        f2,
        term_transform=lambda term: {
            **term,
            "generator_rate_per_ns": term["generator_rate_per_ns"] / 2.0,
        },
    )
    f2_score = family._score_registered_comparisons(
        fixture=f2,
        registry=registry,
        qutip_law=f2_clean,
        dense_law=f2_clean,
        project_law=f2_wrong,
    )
    assert f2_score["all_checks_passed"] is False
    assert f2_score["statistics"]["f2.project_dense_mx_after"]["result"][
        "passed"
    ] is False

    f3 = protocol.load_fixture(FIXTURE_PATHS["f3"])
    f3_clean, _ = dense._record_distribution(f3)
    f3_wrong, _ = dense._record_distribution(
        f3,
        term_transform=lambda term: None
        if term["family"] == "sigma_plus"
        else term,
    )
    f3_score = family._score_registered_comparisons(
        fixture=f3,
        registry=registry,
        qutip_law=f3_clean,
        dense_law=f3_clean,
        project_law=f3_wrong,
    )
    assert f3_score["all_checks_passed"] is False
    assert f3_score["statistics"]["f3.project_dense_mz_after"]["result"][
        "passed"
    ] is False

    swapped, _ = dense._record_distribution(
        f3,
        term_transform=lambda term: {
            **term,
            "family": (
                "sigma_plus" if term["family"] == "sigma_minus" else "sigma_minus"
            ),
        },
    )
    for key in ("mz_before", "mz_after"):
        assert protocol.total_variation(
            _marginal(protocol, f3_clean, key, f3),
            _marginal(protocol, swapped, key, f3),
        ) == pytest.approx(0.45, abs=1.0e-12)

    doubled_up, _ = dense._record_distribution(
        f3,
        term_transform=lambda term: {
            **term,
            "generator_rate_per_ns": (
                2.0 * term["generator_rate_per_ns"]
                if term["family"] == "sigma_plus"
                else term["generator_rate_per_ns"]
            ),
        },
    )
    doubled_separation = protocol.total_variation(
        _marginal(protocol, f3_clean, "mz_after", f3),
        _marginal(protocol, doubled_up, "mz_after", f3),
    )
    assert doubled_separation == pytest.approx(
        0.12017847639540005, abs=1.0e-12
    )
    assert doubled_separation > marginal_radius

    wrong_target, _ = dense._record_distribution(
        f3,
        term_transform=lambda term: {
            **term,
            "target": 0 if term["target"] == 1 else term["target"],
        },
    )
    assert protocol.total_variation(
        _marginal(protocol, f3_clean, "mz_before", f3),
        _marginal(protocol, wrong_target, "mz_before", f3),
    ) == pytest.approx(0.6, abs=1.0e-12)
    assert protocol.total_variation(
        _marginal(protocol, f3_clean, "mz_after", f3),
        _marginal(protocol, wrong_target, "mz_after", f3),
    ) == pytest.approx(0.15, abs=1.0e-12)


@pytest.mark.parametrize("fixture_name", ["f1", "f2", "f3"])
def test_collapse_global_phase_is_an_inert_control(monkeypatch, fixture_name):
    protocol, dense = _load_dense(monkeypatch)
    fixture = protocol.load_fixture(FIXTURE_PATHS[fixture_name])
    clean, _ = dense._record_distribution(fixture)
    phases = {term["term_id"]: -1.0 for term in fixture["collapse_terms"]}
    phased, _ = dense._record_distribution(fixture, phases=phases)

    assert protocol.total_variation(clean, phased) == pytest.approx(0.0, abs=1.0e-15)


def test_fixture_tampering_and_registry_cardinality_drift_fail_closed(tmp_path: Path):
    protocol = _load_protocol()
    corrupted_fixture = copy.deepcopy(
        json.loads(FIXTURE_PATHS["f2"].read_text(encoding="utf-8"))
    )
    corrupted_fixture["collapse_terms"][0]["generator_rate_per_ns"] /= 2.0
    fixture_path = tmp_path / FIXTURE_PATHS["f2"].name
    fixture_path.write_text(json.dumps(corrupted_fixture), encoding="utf-8")
    with pytest.raises(ValueError, match="fixture SHA-256 mismatch"):
        protocol.load_fixture(fixture_path)

    corrupted_registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    corrupted_registry["entries"].pop()
    registry_path = tmp_path / REGISTRY.name
    registry_path.write_text(json.dumps(corrupted_registry), encoding="utf-8")
    with pytest.raises(ValueError, match="registry SHA-256 mismatch"):
        protocol.load_comparison_registry(registry_path)


@pytest.mark.skipif(
    os.environ.get("ECS_RUN_MCWF_XZ_FIXTURE_FAMILY_COMPARISON") != "1",
    reason=(
        "set ECS_RUN_MCWF_XZ_FIXTURE_FAMILY_COMPARISON=1 for the full "
        "GPU/dense/QuTiP family"
    ),
)
def test_optional_full_fixture_family_comparison(tmp_path: Path):
    from harness import proc

    conda = shutil.which("conda")
    assert conda is not None
    output = tmp_path / "mcwf_xz_fixture_family_comparison.json"
    log = tmp_path / "mcwf_xz_fixture_family_comparison.log"
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment["PYTHONNOUSERSITE"] = "1"
    visible_device = environment.get("CUDA_VISIBLE_DEVICES")
    assert visible_device not in (None, "")
    leased_slot = environment.get("ECS_GPU_SLOT")
    if leased_slot is not None:
        assert visible_device == leased_slot
    ran = proc.run(
        [
            conda,
            "run",
            "--no-capture-output",
            "-n",
            "ecs",
            "python",
            str(FAMILY_COMPARATOR),
            "--output",
            str(output),
        ],
        cwd=str(REPO),
        env=environment,
        timeout=1800.0,
        log_path=str(log),
    )

    assert ran.ok, log.read_text(encoding="utf-8", errors="replace")
    assert ran.group_cleanup_verified is True
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["schema"] == (
        "error_coupling_simulator.external_baseline."
        "mcwf_xz_fixture_family_comparison.v1"
    )
    assert report["all_checks_passed"] is True
    assert report["registered_statistic_count"] == 15
    assert report["registry"]["entry_count"] == 15
    assert report["registry"]["sha256"] == (
        "3cd654e798a4c45d3bbebf51665ecffbc109f89ccb3a9eb776904236b5525d62"
    )
    assert [item["fixture"]["id"] for item in report["fixtures"]] == [
        "two_qubit_pure_dephasing_ordered_xz_reset",
        "two_qubit_t1_ordered_xz_reset",
        "two_qubit_thermal_ordered_xz_reset",
    ]
    assert all(item["comparisons"]["all_checks_passed"] for item in report["fixtures"])
