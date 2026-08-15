#!/usr/bin/env python3
"""Run the preregistered F1/F2/F3 dense, QuTiP, and project comparison family."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any, Mapping, Sequence

from error_coupling_simulator.frontend import (
    AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT,
    axis1_carrier_execution_manifest,
    axis1_carrier_program_manifest,
    axis1_mcwf_mps_state_record_execution_manifest,
)
from error_coupling_simulator.numerics import NUMERICAL_ZERO

import qutip_mcwf_xz_protocol as protocol
import run_qutip_mcwf_xz_comparison as adapter


SCHEMA = (
    "error_coupling_simulator.external_baseline."
    "mcwf_xz_fixture_family_comparison.v1"
)
FIXTURE_REPORT_SCHEMA = (
    "error_coupling_simulator.external_baseline.mcwf_xz_fixture_comparison.v1"
)
QUTIP_WORKER_SCHEMA = (
    "error_coupling_simulator.external_baseline.qutip_mcwf_xz_record.v3"
)
DENSE_WORKER_SCHEMA = (
    "error_coupling_simulator.external_baseline.mcwf_xz_dense_record.v1"
)
WORKER_ENVELOPE_SCHEMA = (
    "error_coupling_simulator.external_baseline.mcwf_xz_worker_envelope.v1"
)
BASELINE_DIR = Path(__file__).resolve().parent
QUTIP_WORKER = BASELINE_DIR / "qutip_mcwf_xz_worker.py"
DENSE_WORKER = BASELINE_DIR / "mcwf_xz_dense_worker.py"
DEFAULT_REGISTRY = BASELINE_DIR / "fixtures" / "mcwf_xz_comparison_registry.json"
DEFAULT_FIXTURES = (
    BASELINE_DIR / "fixtures" / "qutip_mcwf_xz_two_qubit_t1.json",
    BASELINE_DIR / "fixtures" / "qutip_mcwf_xz_two_qubit_pure_dephasing.json",
    BASELINE_DIR / "fixtures" / "qutip_mcwf_xz_two_qubit_thermal.json",
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _law_from_worker_record(record: Mapping[str, Any]) -> dict[tuple[int, ...], float]:
    if "records" in record or "probabilities" in record:
        rows = record.get("records")
        probabilities = record.get("probabilities")
    else:
        rows = record.get("binary_records")
        probabilities = record.get("binary_probabilities")
    if (
        not isinstance(rows, list)
        or not isinstance(probabilities, list)
        or len(rows) != len(probabilities)
        or not rows
    ):
        raise RuntimeError("independent worker Record shape drifted")
    return {
        tuple(row): float(probability)
        for row, probability in zip(rows, probabilities, strict=True)
    }


def _worker_envelope(
    report: Mapping[str, Any],
    *,
    worker: Path,
    raw_json_bytes: bytes,
    stdout: str,
    stderr: str,
    returncode: int,
) -> dict[str, Any]:
    payload = copy.deepcopy(dict(report))
    canonical_bytes = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    parsed_raw = adapter._strict_json_loads(raw_json_bytes)
    if parsed_raw != payload or canonical_bytes != json.dumps(
        parsed_raw,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8"):
        raise RuntimeError("independent worker raw JSON does not match parsed payload")
    envelope: dict[str, Any] = {
        "schema": WORKER_ENVELOPE_SCHEMA,
        "worker_path": str(worker.relative_to(adapter.REPO)),
        "worker_sha256": _sha256_file(worker),
        "worker_report": payload,
        "worker_report_content_hash": payload.get("content_hash"),
        "worker_report_raw_json_sha256": hashlib.sha256(raw_json_bytes).hexdigest(),
        "worker_report_raw_json_size_bytes": len(raw_json_bytes),
        "fresh_process": {
            "stdout": stdout,
            "stderr": stderr,
            "returncode": returncode,
        },
    }
    envelope["content_hash"] = protocol.canonical_content_hash(envelope)
    return envelope


def _run_isolated_worker(
    worker: Path,
    fixture_path: Path,
    registry_path: Path,
) -> dict[str, Any]:
    conda = shutil.which("conda")
    if conda is None:
        raise RuntimeError("conda executable is required for isolated workers")
    baseline_python = adapter._resolve_named_conda_python(
        conda,
        environment_name="ecs-baseline-qutip",
    )
    with tempfile.TemporaryDirectory(prefix=f"{worker.stem}_") as temporary:
        temporary_root = Path(temporary)
        environment = adapter._worker_launch_environment(
            os.environ,
            baseline_python=baseline_python,
            cache_root=temporary_root / "private-runtime",
        )
        output = temporary_root / "report.json"
        command = [
            str(baseline_python),
            str(worker),
            "--fixture",
            str(Path(fixture_path).resolve()),
        ]
        if worker == QUTIP_WORKER:
            command.extend(["--registry", str(Path(registry_path).resolve())])
        command.extend(["--output", str(output)])
        process = subprocess.Popen(
            command,
            cwd=adapter.REPO,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = adapter._communicate_isolated_process(
            process,
            timeout_s=300.0,
        )
        if not output.is_file():
            raise RuntimeError(f"isolated {worker.name} published no artifact")
        raw_json_bytes = output.read_bytes()
        report = adapter._strict_json_loads(raw_json_bytes)
    envelope = _worker_envelope(
        report,
        worker=worker,
        raw_json_bytes=raw_json_bytes,
        stdout=stdout,
        stderr=stderr,
        returncode=int(process.returncode),
    )
    _validate_independent_worker_envelope(
        envelope,
        fixture_path=fixture_path,
        registry_path=registry_path,
        worker=worker,
    )
    return envelope


def _validate_independent_worker_envelope(
    envelope: Mapping[str, Any],
    *,
    fixture_path: Path,
    registry_path: Path,
    worker: Path,
) -> None:
    if envelope.get("schema") != WORKER_ENVELOPE_SCHEMA:
        raise RuntimeError("independent worker envelope schema drifted")
    if envelope.get("content_hash") != protocol.canonical_content_hash(envelope):
        raise RuntimeError("independent worker envelope content hash drifted")
    expected_worker_path = str(worker.relative_to(adapter.REPO))
    if (
        envelope.get("worker_path") != expected_worker_path
        or envelope.get("worker_sha256") != _sha256_file(worker)
    ):
        raise RuntimeError("independent worker source binding drifted")
    fresh_process = envelope.get("fresh_process")
    if (
        not isinstance(fresh_process, Mapping)
        or set(fresh_process) != {"stdout", "stderr", "returncode"}
        or fresh_process.get("returncode") != 0
        or not isinstance(fresh_process.get("stdout"), str)
        or not isinstance(fresh_process.get("stderr"), str)
    ):
        raise RuntimeError("independent worker fresh-process record drifted")
    report = envelope.get("worker_report")
    if not isinstance(report, Mapping):
        raise RuntimeError("independent worker report is unavailable")
    expected_schema = QUTIP_WORKER_SCHEMA if worker == QUTIP_WORKER else DENSE_WORKER_SCHEMA
    if report.get("schema") != expected_schema:
        raise RuntimeError("independent worker report schema drifted")
    if report.get("content_hash") != protocol.canonical_content_hash(report):
        raise RuntimeError("independent worker report content hash drifted")
    if report.get("all_checks_passed") is not True:
        raise RuntimeError("independent worker internal checks failed")
    fixture = protocol.load_fixture(fixture_path)
    fixture_record = report.get("fixture")
    if not isinstance(fixture_record, Mapping):
        raise RuntimeError("independent worker fixture binding is unavailable")
    if (
        fixture_record.get("schema") != fixture["schema"]
        or fixture_record.get("id") != fixture["fixture_id"]
        or fixture_record.get("sha256") != protocol.fixture_sha256(fixture_path)
    ):
        raise RuntimeError("independent worker fixture binding drifted")
    record = report.get("record")
    if not isinstance(record, Mapping):
        raise RuntimeError("independent worker Record is unavailable")
    law = _law_from_worker_record(record)
    if len(law) > 16 or any(
        len(row) != 4 or any(value not in (0, 1) for value in row) for row in law
    ):
        raise RuntimeError("independent worker Record domain drifted")
    if not math.isclose(math.fsum(law.values()), 1.0, rel_tol=0.0, abs_tol=1.0e-12):
        raise RuntimeError("independent worker Record mass drifted")
    runtime = report.get("runtime_provenance")
    if not isinstance(runtime, Mapping):
        raise RuntimeError("independent worker runtime provenance is unavailable")
    if worker == QUTIP_WORKER:
        registry = protocol.load_comparison_registry(registry_path)
        if fixture_record.get("comparison_registry_sha256") != registry["sha256"]:
            raise RuntimeError("QuTiP worker registry binding drifted")
        adapter._validate_isolated_qutip_report(
            dict(report),
            fixture=fixture,
            fixture_path=fixture_path,
        )
        if runtime.get("project_package_find_spec") is not None:
            raise RuntimeError("project package leaked into QuTiP worker")
        if report.get("solver", {}).get("collapse_operator_count") != len(
            fixture["collapse_terms"]
        ):
            raise RuntimeError("QuTiP collapse coverage drifted")
    else:
        if (
            runtime.get("project_program_consumed") is not False
            or runtime.get("project_implementation_imported") is not False
            or runtime.get("project_package_find_spec") is not None
            or runtime.get("project_isolation_required") is not True
        ):
            raise RuntimeError("dense worker independence contract drifted")
        if report.get("construction", {}).get("liouvillian_dimension") != 16:
            raise RuntimeError("dense worker Liouvillian dimension drifted")


def _expected_program_terms(fixture: Mapping[str, Any]) -> list[dict[str, Any]]:
    family_map = {
        "number_dephasing": "T2",
        "sigma_minus": "T1",
        "sigma_plus": "T1_UP",
    }
    return sorted(
        [
            {
                "operator_family": family_map[term["family"]],
                "support": [int(term["target"])],
                "generator_rate_per_ns": float(term["generator_rate_per_ns"]),
            }
            for term in fixture["collapse_terms"]
        ],
        key=lambda item: (item["operator_family"], item["support"]),
    )


def _project_program_binding(
    fixture: Mapping[str, Any],
    schedule: Any,
    program: Mapping[str, Any],
) -> dict[str, Any]:
    expected = _expected_program_terms(fixture)
    observed_layers: list[dict[str, Any]] = []
    substeps = program.get("program", {}).get("substeps", [])
    for substep in substeps:
        if substep.get("substep_kind") != "idle" or substep.get("dt_ns") != 10.0:
            continue
        active_terms = []
        for term in substep.get("terms", []):
            coefficient = term.get("coefficient")
            if (
                term.get("kind") != "collapse"
                or not isinstance(coefficient, (int, float))
                or isinstance(coefficient, bool)
                or float(coefficient) <= 0.0
            ):
                continue
            active_terms.append(
                {
                    "operator_family": term.get("operator_family"),
                    "support": term.get("support"),
                    "generator_rate_per_ns": float(coefficient) ** 2,
                }
            )
        active_terms.sort(key=lambda item: (item["operator_family"], item["support"]))
        observed_layers.append(
            {
                "substep_id": substep.get("substep_id"),
                "dt_ns": substep.get("dt_ns"),
                "active_terms": active_terms,
                "matches_fixture": (
                    len(active_terms) == len(expected)
                    and all(
                        observed["operator_family"] == target["operator_family"]
                        and observed["support"] == target["support"]
                        and abs(
                            observed["generator_rate_per_ns"]
                            - target["generator_rate_per_ns"]
                        )
                        <= NUMERICAL_ZERO
                        for observed, target in zip(active_terms, expected, strict=True)
                    )
                ),
            }
        )
    source_hash_match = program.get("source_hash") == schedule.source_hash
    passed = bool(
        len(observed_layers) == 2
        and all(layer["matches_fixture"] for layer in observed_layers)
        and source_hash_match
        and isinstance(program.get("content_hash"), str)
    )
    return {
        "fixture_terms": expected,
        "observed_evolution_layers": observed_layers,
        "schedule_source_hash": schedule.source_hash,
        "program_source_hash": program.get("source_hash"),
        "source_hash_match": source_hash_match,
        "program_content_hash": program.get("content_hash"),
        "passed": passed,
    }


def _score_registered_comparisons(
    *,
    fixture: Mapping[str, Any],
    registry: Mapping[str, Any],
    qutip_law: Mapping[Sequence[int], float],
    dense_law: Mapping[Sequence[int], float],
    project_law: Mapping[Sequence[int], float],
) -> dict[str, Any]:
    ntraj = int(fixture["trajectory_count"])
    alpha = float(registry["per_entry_alpha"])
    scored: dict[str, Any] = {}
    for entry in protocol.comparison_entries_for_fixture(
        registry, fixture["fixture_id"]
    ):
        left: Mapping[Sequence[int], float]
        right: Mapping[Sequence[int], float]
        kind = entry["comparison_kind"]
        if kind == "one_sample_qutip_dense":
            left, right = qutip_law, dense_law
        elif kind == "one_sample_project_dense":
            left, right = project_law, dense_law
        elif kind == "two_sample_qutip_project":
            left, right = qutip_law, project_law
        else:
            raise RuntimeError("comparison registry kind drifted")
        if entry["view"] == "marginal":
            column = fixture["measurement_keys"].index(entry["column_key"])
            left = protocol.binary_column_marginal(left, column=column)
            right = protocol.binary_column_marginal(right, column=column)
        if kind == "two_sample_qutip_project":
            result = protocol.two_sample_tv_comparison(
                left,
                right,
                left_sample_count=ntraj,
                right_sample_count=ntraj,
                alphabet_size=int(entry["alphabet_size"]),
                alpha=alpha,
            )
        else:
            result = protocol.one_sample_tv_comparison(
                left,
                right,
                sample_count=ntraj,
                alphabet_size=int(entry["alphabet_size"]),
                alpha=alpha,
            )
        scored[entry["statistic_id"]] = {
            "registry_entry": dict(entry),
            "result": result,
        }
    return {
        "registry_sha256": registry["sha256"],
        "registry_entry_count": registry["entry_count"],
        "per_entry_alpha": alpha,
        "statistics": scored,
        "all_checks_passed": all(
            item["result"]["passed"] for item in scored.values()
        ),
    }


def _build_project_candidate(fixture: Mapping[str, Any]) -> dict[str, Any]:
    schedule = adapter._schedule_from_fixture(dict(fixture))
    program = axis1_carrier_program_manifest(
        schedule,
        backend_contract=AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT,
    )
    binding = _project_program_binding(fixture, schedule, program)
    if not binding["passed"]:
        raise RuntimeError("project program does not bind the neutral fixture")
    options = {
        "device": "cuda",
        "local_dims": fixture["local_dims"],
        "initial_levels": fixture["initial_levels"],
        "microstep_count": int(fixture["microstep_count"]),
        "trajectory_count": int(fixture["trajectory_count"]),
        "rng_seed": int(fixture["project_rng_seed"]),
    }
    direct_manifest = axis1_mcwf_mps_state_record_execution_manifest(schedule, **options)
    if direct_manifest.get("verdict") != "pass":
        raise RuntimeError("public direct MCWF fixture failed")
    direct_execution = direct_manifest["mps_execution"]
    direct_record = adapter._validate_record_payload(
        direct_execution,
        dict(fixture),
        label_prefix="direct MCWF",
    )
    carrier_manifest = axis1_carrier_execution_manifest(
        schedule,
        device="cuda",
        execution_backend_contract=AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT,
        execution_backend_options={key: value for key, value in options.items() if key != "device"},
    )
    if carrier_manifest.get("passed") is not True:
        raise RuntimeError("public Carrier MCWF fixture failed")
    carrier_record = adapter._validate_record_payload(
        carrier_manifest["record_execution"],
        dict(fixture),
        label_prefix="Carrier MCWF",
    )
    direct_carrier_exact = direct_record == carrier_record
    if not direct_carrier_exact:
        raise RuntimeError("public direct and Carrier MCWF Records diverged")
    expected_semantics = (
        "measurement_bases and reset_after are schedule-ordered one-per-Record-column; "
        "X measurement rotates into Z, projects, then rotates back unless reset prepares |+>"
    )
    semantics_match = bool(
        direct_execution.get("measurement_basis_semantics") == expected_semantics
        and carrier_manifest["record_execution"].get("measurement_basis_semantics")
        == expected_semantics
    )
    return {
        "law": adapter._law(direct_record),
        "binding": binding,
        "direct": {
            "schema": direct_manifest["schema"],
            "content_hash": direct_manifest["content_hash"],
            "record": direct_record,
            "passed": True,
        },
        "carrier": {
            "schema": carrier_manifest["schema"],
            "content_hash": carrier_manifest["content_hash"],
            "record": carrier_record,
            "passed": True,
        },
        "direct_carrier_exact_record_match": direct_carrier_exact,
        "measurement_semantics_match": semantics_match,
        "array_backend": direct_execution["array_backend"],
        "carrier_array_backend": carrier_manifest["state_execution"]["array_backend"],
    }


def build_fixture_report(
    fixture_path: Path,
    registry_path: Path,
) -> dict[str, Any]:
    fixture = protocol.load_fixture(fixture_path)
    registry = protocol.load_comparison_registry(registry_path)
    if fixture["comparison_family_alpha"] != registry["comparison_family_alpha"]:
        raise RuntimeError("fixture comparison family alpha drifted")
    dense_envelope = _run_isolated_worker(DENSE_WORKER, fixture_path, registry_path)
    qutip_envelope = _run_isolated_worker(QUTIP_WORKER, fixture_path, registry_path)
    project = _build_project_candidate(fixture)
    dense_law = _law_from_worker_record(dense_envelope["worker_report"]["record"])
    qutip_record = qutip_envelope["worker_report"]["record"]
    qutip_law = {
        tuple(row): float(probability)
        for row, probability in zip(
            qutip_record["binary_records"],
            qutip_record["binary_probabilities"],
            strict=True,
        )
    }
    comparisons = _score_registered_comparisons(
        fixture=fixture,
        registry=registry,
        qutip_law=qutip_law,
        dense_law=dense_law,
        project_law=project["law"],
    )
    supplemental_f1 = None
    if fixture["fixture_id"] == "two_qubit_t1_ordered_xz_reset":
        recurrence = protocol.finite_step_convergence_evidence(fixture)
        public_gate = protocol.finite_step_public_sample_evidence(
            fixture, project["law"]
        )
        supplemental_f1 = {
            "deterministic_recurrence": recurrence,
            "public_m40_sample_gate": public_gate,
            "all_checks_passed": bool(
                recurrence["all_checks_passed"] and public_gate["passed"]
            ),
        }
    all_checks_passed = bool(
        dense_envelope["worker_report"]["all_checks_passed"]
        and qutip_envelope["worker_report"]["all_checks_passed"]
        and project["binding"]["passed"]
        and project["direct_carrier_exact_record_match"]
        and project["measurement_semantics_match"]
        and comparisons["all_checks_passed"]
        and (
            supplemental_f1 is None
            or supplemental_f1["all_checks_passed"]
        )
    )
    report: dict[str, Any] = {
        "schema": FIXTURE_REPORT_SCHEMA,
        "claim_boundary": fixture["claim_boundary"],
        "fixture": {
            "schema": fixture["schema"],
            "id": fixture["fixture_id"],
            "path": str(Path(fixture_path).resolve()),
            "sha256": protocol.fixture_sha256(fixture_path),
            "trajectory_count": fixture["trajectory_count"],
        },
        "dense": dense_envelope,
        "qutip": qutip_envelope,
        "project": {key: value for key, value in project.items() if key != "law"},
        "comparisons": comparisons,
        "supplemental_f1_convergence": supplemental_f1,
        "corruption_contract": {
            "test_path": "tests/test_external_mcwf_xz_fixture_family.py",
            "required_mutations": [
                "f1_sigma_minus_to_sigma_plus",
                "f2_missing_sqrt_two",
                "f3_remove_sigma_plus",
                "f3_swap_sigma_plus_sigma_minus",
                "f3_double_excitation_generator_rate",
                "f3_move_target1_pair_to_target0",
            ],
            "gauge_invariance_control": "unit_modulus_collapse_phase_must_remain_inert",
        },
        "all_checks_passed": all_checks_passed,
    }
    report["content_hash"] = protocol.canonical_content_hash(report)
    return report


def build_report(
    fixture_paths: Sequence[Path],
    registry_path: Path,
) -> dict[str, Any]:
    registry = protocol.load_comparison_registry(registry_path)
    resolved_paths = tuple(Path(path).resolve() for path in fixture_paths)
    fixtures = [protocol.load_fixture(path) for path in resolved_paths]
    if tuple(sorted(fixture["fixture_id"] for fixture in fixtures)) != (
        protocol.EXPECTED_FIXTURE_IDS
    ):
        raise RuntimeError("family run must contain each F1/F2/F3 fixture exactly once")
    project_runtime = adapter._project_runtime_provenance()
    fixture_reports = [
        build_fixture_report(path, registry_path)
        for path in sorted(
            resolved_paths,
            key=lambda item: protocol.load_fixture(item)["fixture_id"],
        )
    ]
    if adapter._project_source_provenance() != project_runtime["source_provenance"]:
        raise RuntimeError("project evidence sources changed during family run")
    if (
        adapter._environment_lock_provenance()
        != project_runtime["environment_lock_provenance"]
    ):
        raise RuntimeError("project environment locks changed during family run")
    report: dict[str, Any] = {
        "schema": SCHEMA,
        "claim_boundary": (
            "three frozen two-qubit Markovian neutral fixtures only; no complete QEC "
            "Record, finite-bond, calibration, scalability, or release claim"
        ),
        "registry": registry,
        "project_runtime_provenance": project_runtime,
        "fixtures": fixture_reports,
        "registered_statistic_count": sum(
            len(item["comparisons"]["statistics"]) for item in fixture_reports
        ),
        "all_checks_passed": all(
            item["all_checks_passed"] for item in fixture_reports
        ),
    }
    if report["registered_statistic_count"] != registry["entry_count"]:
        raise RuntimeError("family report statistic count drifted from registry")
    report["content_hash"] = protocol.canonical_content_hash(report)
    return report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, action="append", dest="fixtures")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    fixture_paths = DEFAULT_FIXTURES if args.fixtures is None else tuple(args.fixtures)
    adapter._prepare_output_path(args.output)
    report = build_report(fixture_paths, args.registry)
    adapter._atomic_write_json(args.output, report)
    print(f"registered_statistic_count={report['registered_statistic_count']}")
    print(f"all_checks_passed={report['all_checks_passed']}")
    print(f"content_hash={report['content_hash']}")
    return 0 if report["all_checks_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
