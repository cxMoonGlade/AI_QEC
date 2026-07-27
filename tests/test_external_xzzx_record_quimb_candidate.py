"""Focused contracts for the neutral XZZX Quimb PEPS candidate."""

from __future__ import annotations

import gc
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys


import numpy as np
import pytest
import stim


REPO = Path(__file__).resolve().parents[1]
WORKER_PATH = (
    REPO
    / "scripts"
    / "external_baselines"
    / "xzzx_record_quimb_candidate.py"
)
EMITTER_PATH = (
    REPO
    / "scripts"
    / "external_baselines"
    / "emit_xzzx_record_peps_fixture.py"
)
DENSE_PATH = (
    REPO
    / "scripts"
    / "external_baselines"
    / "xzzx_record_dense_reference.py"
)


def _load_worker():
    spec = importlib.util.spec_from_file_location(
        "xzzx_record_quimb_candidate_under_test",
        WORKER_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_emitter():
    spec = importlib.util.spec_from_file_location(
        "emit_xzzx_record_peps_fixture_for_quimb_test",
        EMITTER_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_dense():
    spec = importlib.util.spec_from_file_location(
        "xzzx_record_dense_reference_for_quimb_test",
        DENSE_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _v2_run_spec(emitter, fixture):
    distance = int(fixture["distance"])
    assert distance in (3, 5)
    return {
        "base_fixture_sha256": emitter.canonical_json_sha256(fixture),
        "distance": distance,
        "intervention": {
            "after_rounds": [0, 1],
            "angle_radians": 0.02,
            "gate": "RY",
            "placement": (
                "after_each_complete_syndrome_round_before_the_next_"
                "base_operation"
            ),
            "targets": "all_data_qubits_in_ascending_dense_id_order",
        },
        "reference_branch": {
            "sampler": "numpy_exact_data_projector",
            "selector": {
                "algorithm": "sha256_prefix_born_v1",
                "comparison": (
                    "bit_0_iff_h_times_den_lt_num_times_2_pow_256_for_"
                    "p0_as_integer_ratio"
                ),
                "domain_separator_ascii": (
                    "ECS-XZZX-DATA-ONLY-BRANCH-V2"
                ),
                "domain_separator_terminated_by_zero_byte": True,
                "hash_integer_encoding": (
                    "sha256_full_digest_unsigned_big_endian"
                ),
                "measurement_column_encoding": (
                    "uint32_big_endian_equal_to_prefix_length"
                ),
                "prefix_encoding": "one_byte_per_bit_0x00_or_0x01",
                "seed": 2026072600 + distance,
                "seed_encoding": "uint64_big_endian",
            },
            "shots": 1,
        },
        "reference_state": {
            "checkpoint": (
                "after_round_1_ry_before_terminal_data_measurements"
            ),
            "method": "numpy_exact_data_projector",
            "probability_floor": None,
            "truncation": None,
        },
        "rounds": 2,
        "schema": (
            "error_coupling_simulator.external_xzzx_record_peps."
            "run_spec.v2"
        ),
        "stim_circuit_sha256": fixture["stim_circuit_sha256"],
    }


def _require_arbitrary_graph_quimb() -> None:
    import quimb.tensor as qtn

    if not hasattr(qtn, "CircuitPEPSSimpleUpdate"):
        if os.environ.get("ECS_XZZX_REQUIRE_CUDA_CONTROLS") == "1":
            pytest.fail(
                "formal XZZX controls require arbitrary-graph Quimb PEPS"
            )
        pytest.skip(
            "requires the isolated ecs-baseline-quimb-peps environment"
        )


def _gauge_bytes(worker, trajectory) -> dict[object, tuple[str, tuple[int, ...], bytes]]:
    return {
        key: (
            np.asarray(worker._as_numpy(value)).dtype.str,
            tuple(np.asarray(worker._as_numpy(value)).shape),
            np.ascontiguousarray(worker._as_numpy(value)).tobytes(),
        )
        for key, value in trajectory.circuit.gauges.items()
    }


@pytest.mark.parametrize(
    ("distance", "expected_sha256"),
    [
        (
            3,
            "7dfa0a8ef9620712e6ea190aeda651c681295f9841963ce77686640255cc22a9",
        ),
        (
            5,
            "06151ea1244495475259d40bf6ca7ad16cbdaf5f8184ee61b344fb2e81b413a4",
        ),
    ],
)
def test_v2_run_spec_is_exact_hash_bound_to_numpy_reference_authority(
    distance: int,
    expected_sha256: str,
) -> None:
    worker = _load_worker()
    emitter = _load_emitter()
    _circuit, fixture = emitter.emit_fixture(
        stim,
        distance=distance,
        rounds=2,
    )
    run_spec = _v2_run_spec(emitter, fixture)

    observed, enumeration = worker.validate_run_spec(run_spec, fixture)

    assert observed == expected_sha256
    assert enumeration is False

    corrupt = json.loads(json.dumps(run_spec))
    corrupt["reference_branch"]["selector"]["seed"] += 1
    with pytest.raises(ValueError, match="canonical hash"):
        worker.validate_run_spec(corrupt, fixture)

    legacy = json.loads(json.dumps(run_spec))
    legacy["schema"] = (
        "error_coupling_simulator.external_xzzx_record_peps.run_spec.v1"
    )
    with pytest.raises(ValueError, match="schema"):
        worker.validate_run_spec(legacy, fixture)


def test_v2_candidate_configuration_rejects_unregistered_d5_d8() -> None:
    worker = _load_worker()

    worker.validate_candidate_configuration(
        distance=3,
        max_bond=8,
        rdm_radius="complete",
    )
    worker.validate_candidate_configuration(
        distance=5,
        max_bond=4,
        rdm_radius=3,
    )
    with pytest.raises(ValueError, match="d5 bond dimension"):
        worker.validate_candidate_configuration(
            distance=5,
            max_bond=8,
            rdm_radius=3,
        )


def test_public_gate_semantics_are_complex128_and_ordered() -> None:
    worker = _load_worker()

    h = worker.gate_matrix("H")
    ry = worker.gate_matrix("RY", angle_radians=0.02)
    cx = worker.gate_matrix("CX")

    assert h.dtype == ry.dtype == cx.dtype == np.complex128
    np.testing.assert_allclose(
        ry,
        [
            [np.cos(0.01), -np.sin(0.01)],
            [np.sin(0.01), np.cos(0.01)],
        ],
        atol=0.0,
        rtol=0.0,
    )
    np.testing.assert_array_equal(
        cx,
        [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 0],
        ],
    )


def test_born_pair_preserves_every_positive_probability_and_rejects_clipping() -> None:
    worker = _load_worker()
    tiny = float.fromhex("0x1.0000000000000p-100")

    probabilities, diagnostics = worker.validated_one_site_born_pair(
        np.asarray([[1.0, 0.0], [0.0, tiny]], dtype=np.complex128)
    )

    assert probabilities == (1.0, tiny)
    assert probabilities[1] > 0.0
    assert diagnostics["probability_sum_residual"] == 0.0
    assert worker.is_structural_zero_probability(0.0) is True
    assert worker.is_structural_zero_probability(tiny) is False

    for invalid in (
        np.asarray(
            [[1.0 + 1e-14, 0.0], [0.0, -1e-14]],
            dtype=np.complex128,
        ),
        np.asarray(
            [[1.0 + 1e-14, 0.0], [0.0, 0.0]],
            dtype=np.complex128,
        ),
    ):
        with pytest.raises(RuntimeError, match="Born probability"):
            worker.validated_one_site_born_pair(invalid)

    with pytest.raises(RuntimeError, match="positive-semidefinite"):
        worker.validated_one_site_born_pair(
            np.asarray([[0.5, 0.6], [0.6, 0.5]], dtype=np.complex128)
        )


def test_positive_branch_mass_never_underflows_to_structural_zero() -> None:
    worker = _load_worker()

    ordinary = worker.stable_positive_branch_mass([0.8, 0.3])
    assert ordinary == {
        "branch_mass": pytest.approx(0.24),
        "log_branch_mass": pytest.approx(np.log(0.8) + np.log(0.3)),
        "branch_mass_representable": True,
        "positive_mass_underflowed_to_zero": False,
    }

    tiny = float.fromhex("0x1.0000000000000p-600")
    underflow = worker.stable_positive_branch_mass([tiny, tiny])
    assert underflow["branch_mass"] is None
    assert np.isfinite(underflow["log_branch_mass"])
    assert underflow["branch_mass_representable"] is False
    assert underflow["positive_mass_underflowed_to_zero"] is False


def test_tracer_law_adapter_matches_dense_complete_bitstring_schema() -> None:
    worker = _load_worker()
    raw_rows = [
        {
            "bits": [0, 0],
            "probability": 0.1,
            "detector_bits": [0],
            "observable_bits": [0],
        },
        {
            "bits": [0, 1],
            "probability": 0.2,
            "detector_bits": [0],
            "observable_bits": [1],
        },
        {
            "bits": [1, 0],
            "probability": 0.3,
            "detector_bits": [1],
            "observable_bits": [0],
        },
        {
            "bits": [1, 1],
            "probability": 0.4,
            "detector_bits": [1],
            "observable_bits": [1],
        },
    ]
    folded_rows = [
        {
            "detector_bits": row["detector_bits"],
            "observable_bits": row["observable_bits"],
            "probability": row["probability"],
        }
        for row in raw_rows
    ]

    raw_law, record_law = worker.tracer_law_mappings(
        raw_rows=raw_rows,
        folded_rows=folded_rows,
        raw_width=2,
        detector_width=1,
        observable_width=1,
    )

    assert raw_law == {
        "00": 0.1,
        "01": 0.2,
        "10": 0.3,
        "11": 0.4,
    }
    assert record_law == raw_law

    duplicate = [dict(row) for row in raw_rows]
    duplicate[-1]["bits"] = [1, 0]
    with pytest.raises(ValueError, match="complete raw support"):
        worker.tracer_law_mappings(
            raw_rows=duplicate,
            folded_rows=folded_rows,
            raw_width=2,
            detector_width=1,
            observable_width=1,
        )


def test_environment_lock_rejects_schema_and_installed_source_drift() -> None:
    worker = _load_worker()
    lock = json.loads(
        worker.ENVIRONMENT_LOCK.read_text(encoding="utf-8")
    )
    clone = {
        "commit": worker.EXPECTED_QUIMB_COMMIT,
        "tree": worker.EXPECTED_QUIMB_TREE,
        "origin": "https://github.com/jcmgray/quimb.git",
    }
    locked_quimb = lock["selected_distribution_records"]["quimb"]
    installed = {
        "version": locked_quimb["version"],
        "direct_url": locked_quimb["direct_url"],
        "installed_source": lock["installed_quimb_source"],
    }

    wrong_schema = dict(lock)
    wrong_schema["schema"] = "wrong"
    with pytest.raises(RuntimeError, match="schema"):
        worker._verify_environment_lock(
            wrong_schema,
            clone=clone,
            installed_quimb=installed,
        )

    wrong_source = json.loads(json.dumps(installed))
    wrong_source["installed_source"]["python_source_file_count"] += 1
    with pytest.raises(RuntimeError, match="source bytes"):
        worker._verify_environment_lock(
            lock,
            clone=clone,
            installed_quimb=wrong_source,
        )


def test_formal_resource_gate_rejects_each_frozen_limit() -> None:
    worker = _load_worker()
    accepted = worker.validate_resource_limits(
        {
            "elapsed_seconds": 1.0,
            "python_peak_rss_bytes": 1024,
            "peak_device_allocated_bytes": 0,
        }
    )
    assert accepted["all_limits_passed"] is True

    for field, value in (
        ("elapsed_seconds", 1800.0 + 1e-9),
        ("python_peak_rss_bytes", 64 * 1024**3 + 1),
        ("peak_device_allocated_bytes", 28 * 1024**3 + 1),
    ):
        usage = {
            "elapsed_seconds": 1.0,
            "python_peak_rss_bytes": 1024,
            "peak_device_allocated_bytes": 0,
        }
        usage[field] = value
        with pytest.raises(RuntimeError, match="resource limit"):
            worker.validate_resource_limits(usage)


def test_output_preflight_rejects_aliases_and_existing_targets(
    tmp_path: Path,
) -> None:
    worker = _load_worker()
    summary = tmp_path / "summary.json"
    state = tmp_path / "state.npy"

    worker.preflight_output_paths(
        summary_path=summary,
        state_path=state,
    )
    with pytest.raises(ValueError, match="distinct"):
        worker.preflight_output_paths(
            summary_path=summary,
            state_path=summary,
        )

    summary.write_text("do not replace", encoding="utf-8")
    with pytest.raises(FileExistsError, match="existing output"):
        worker.preflight_output_paths(
            summary_path=summary,
            state_path=state,
        )
    assert not state.exists()


def test_atomic_publish_cannot_overwrite_a_racing_destination(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    worker = _load_worker()
    destination = tmp_path / "summary.json"
    real_link = os.link

    def racing_link(source: Path, target: Path) -> None:
        Path(target).write_text("racing writer", encoding="utf-8")
        real_link(source, target)

    monkeypatch.setattr(worker.os, "link", racing_link)
    with pytest.raises(FileExistsError, match="replace existing output"):
        worker._atomic_write_json(destination, {"status": "new"})
    assert destination.read_text(encoding="utf-8") == "racing writer"


def test_branch_contract_requires_bound_hashes_and_contiguous_bits() -> None:
    worker = _load_worker()
    branch = {
        "schema": worker.BRANCH_SCHEMA,
        "fixture_sha256": "a" * 64,
        "run_spec_sha256": "b" * 64,
        "branch_id": "primary",
        "distance": 3,
        "rounds": 2,
        "outcomes": [
            {"column": 0, "bit": 1},
            {"column": 1, "bit": 0},
        ],
    }

    assert worker.validate_branch(
        branch,
        fixture_sha256="a" * 64,
        spec_sha256="b" * 64,
        distance=3,
        rounds=2,
        measurement_count=2,
        enumeration=False,
    ) == [1, 0]

    branch["outcomes"][1]["column"] = 2
    with pytest.raises(ValueError, match="contiguous"):
        worker.validate_branch(
            branch,
            fixture_sha256="a" * 64,
            spec_sha256="b" * 64,
            distance=3,
            rounds=2,
            measurement_count=2,
            enumeration=False,
        )

    branch["outcomes"][1]["column"] = 1
    branch["fixture_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="fixture hash"):
        worker.validate_branch(
            branch,
            fixture_sha256="a" * 64,
            spec_sha256="b" * 64,
            distance=3,
            rounds=2,
            measurement_count=2,
            enumeration=False,
        )

    branch["fixture_sha256"] = "a" * 64
    branch["reference_probability_rows"] = []
    with pytest.raises(ValueError, match="exact neutral fields"):
        worker.validate_branch(
            branch,
            fixture_sha256="a" * 64,
            spec_sha256="b" * 64,
            distance=3,
            rounds=2,
            measurement_count=2,
            enumeration=False,
        )


def test_primary_branch_authority_is_hash_bound_and_kept_outside_branch() -> None:
    worker = _load_worker()
    emitter = _load_emitter()
    _circuit, fixture = emitter.emit_fixture(stim, distance=3, rounds=2)
    run_spec = _v2_run_spec(emitter, fixture)
    branch = {
        "schema": worker.BRANCH_SCHEMA,
        "fixture_sha256": emitter.canonical_json_sha256(fixture),
        "run_spec_sha256": emitter.canonical_json_sha256(run_spec),
        "branch_id": "exact-v2-primary",
        "distance": 3,
        "rounds": 2,
        "outcomes": [
            {"column": column, "bit": 0}
            for column in range(fixture["num_measurements"])
        ],
    }
    authority = {
        "schema": worker.BRANCH_AUTHORITY_SCHEMA,
        "role": "primary",
        "method": "sha256_prefix_born_v1",
        "branch_sha256": worker.canonical_json_sha256(branch),
        "selector": run_spec["reference_branch"]["selector"],
    }

    sanitized = worker.validate_branch_authority(
        authority,
        branch=branch,
        run_spec=run_spec,
        fixture=fixture,
    )

    assert sanitized == authority
    assert set(branch) == {
        "schema",
        "fixture_sha256",
        "run_spec_sha256",
        "branch_id",
        "distance",
        "rounds",
        "outcomes",
    }

    wrong_hash = dict(authority)
    wrong_hash["branch_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="branch SHA"):
        worker.validate_branch_authority(
            wrong_hash,
            branch=branch,
            run_spec=run_spec,
            fixture=fixture,
        )

    leaked = dict(authority)
    leaked["probability_rows"] = []
    with pytest.raises(ValueError, match="exact fields"):
        worker.validate_branch_authority(
            leaked,
            branch=branch,
            run_spec=run_spec,
            fixture=fixture,
        )


def test_exact_reference_summary_authorizes_only_its_bits_only_branch() -> None:
    worker = _load_worker()
    emitter = _load_emitter()
    _circuit, fixture = emitter.emit_fixture(stim, distance=3, rounds=2)
    run_spec = _v2_run_spec(emitter, fixture)
    branch = {
        "schema": worker.BRANCH_SCHEMA,
        "fixture_sha256": emitter.canonical_json_sha256(fixture),
        "run_spec_sha256": emitter.canonical_json_sha256(run_spec),
        "branch_id": "exact-v2-primary",
        "distance": 3,
        "rounds": 2,
        "outcomes": [
            {"column": column, "bit": 0}
            for column in range(fixture["num_measurements"])
        ],
    }
    authority = {
        "schema": worker.BRANCH_AUTHORITY_SCHEMA,
        "role": "primary",
        "method": "sha256_prefix_born_v1",
        "branch_sha256": worker.canonical_json_sha256(branch),
        "selector": run_spec["reference_branch"]["selector"],
    }
    exact_summary = {
        "schema": worker.EXACT_REFERENCE_RESULT_SCHEMA,
        "status": "completed",
        "branch": branch,
        "branch_authority": authority,
        "probability_rows": [{"must_not_be_consumed": True}],
        "state": {"must_not_be_consumed": True},
    }

    neutral = worker.validate_exact_reference_summary(
        exact_summary,
        summary_file_sha256="a" * 64,
        branch=branch,
        run_spec=run_spec,
        fixture=fixture,
    )

    assert neutral["authority"] == authority
    assert neutral["reference_probabilities_or_state_consumed"] is False
    assert "probability_rows" not in neutral
    assert "state" not in neutral

    other_branch = json.loads(json.dumps(branch))
    other_branch["branch_id"] = "substituted"
    with pytest.raises(ValueError, match="neutral branch"):
        worker.validate_exact_reference_summary(
            exact_summary,
            summary_file_sha256="a" * 64,
            branch=other_branch,
            run_spec=run_spec,
            fixture=fixture,
        )


def test_alternate_authority_binds_parent_hashes_and_mr_flip_column() -> None:
    worker = _load_worker()
    emitter = _load_emitter()
    _circuit, fixture = emitter.emit_fixture(stim, distance=3, rounds=2)
    run_spec = _v2_run_spec(emitter, fixture)
    branch = {
        "schema": worker.BRANCH_SCHEMA,
        "fixture_sha256": emitter.canonical_json_sha256(fixture),
        "run_spec_sha256": emitter.canonical_json_sha256(run_spec),
        "branch_id": "exact-v2-alternate",
        "distance": 3,
        "rounds": 2,
        "outcomes": [
            {"column": column, "bit": 0}
            for column in range(fixture["num_measurements"])
        ],
    }
    first_mr = next(
        row["column"]
        for row in fixture["measurement_order"]
        if row["reset"]
    )
    authority = {
        "schema": worker.BRANCH_AUTHORITY_SCHEMA,
        "role": "alternate",
        "method": (
            "first_mr_opposite_probability_at_least_1e-8_then_"
            "greedy_tie_zero"
        ),
        "branch_sha256": worker.canonical_json_sha256(branch),
        "parent": {
            "summary_schema": worker.EXACT_REFERENCE_RESULT_SCHEMA,
            "summary_file_sha256": "a" * 64,
            "branch_sha256": "b" * 64,
            "branch_id": "exact-v2-primary",
        },
        "flip_column": first_mr,
    }

    assert worker.validate_branch_authority(
        authority,
        branch=branch,
        run_spec=run_spec,
        fixture=fixture,
    ) == authority

    terminal = next(
        row["column"]
        for row in fixture["measurement_order"]
        if not row["reset"]
    )
    bad_flip = dict(authority)
    bad_flip["flip_column"] = terminal
    with pytest.raises(ValueError, match="identify an MR"):
        worker.validate_branch_authority(
            bad_flip,
            branch=branch,
            run_spec=run_spec,
            fixture=fixture,
        )


def test_selective_mr_uses_born_pair_and_resets_outcome_one() -> None:
    _require_arbitrary_graph_quimb()
    worker = _load_worker()
    trajectory = worker.QuimbTrajectory(
        qubit_count=2,
        edges=[(0, 1)],
        max_bond=2,
        rdm_radius="complete",
        device_name="cpu",
        optimize="greedy",
    )
    trajectory.apply_unitary(worker.gate_matrix("H"), [0])
    trajectory.apply_unitary(worker.gate_matrix("CX"), [0, 1])
    pre_reset_state, _ = trajectory.complete_state_vector([0, 1])
    pre_reset_gauges = _gauge_bytes(worker, trajectory)

    row, reset = trajectory.measure(
        column=0,
        site=0,
        bit=1,
        reset=True,
    )
    state, state_meta = trajectory.complete_state_vector([0, 1])
    post_reset_gauges = _gauge_bytes(worker, trajectory)

    np.testing.assert_allclose(
        [row["p0"], row["p1"], row["selected_probability"]],
        [0.5, 0.5, 0.5],
        atol=1e-12,
        rtol=0.0,
    )
    assert row["graph_coverage"]["complete"] is True
    assert row["graph_coverage"]["selected_tensor_ids"] == [0, 1]
    assert reset["physical_one_tensor_slice_exact_zero"] is True
    assert reset["physical_one_tensor_slice_max_abs"] == 0.0
    assert reset["rank_one_reset_slice_verified_exact"] is True
    assert reset["repair_projector_applied"] is False
    assert reset["trace_distance_to_zero"] <= 1e-12
    assert reset["reset_gauge_policy"]["strategy"] == (
        "preserve_pre_reset_simple_update_gauges_byte_for_byte"
    )
    assert reset["reset_gauge_policy"]["no_gauge_refresh"] is True
    assert reset["reset_gauge_policy"]["gauge_keys_unchanged"] is True
    assert reset["reset_gauge_policy"]["gauge_bytes_unchanged"] is True
    assert pre_reset_gauges == post_reset_gauges
    expected = np.zeros_like(pre_reset_state)
    expected[:2] = pre_reset_state[2:]
    expected /= np.linalg.norm(expected)
    np.testing.assert_allclose(state, expected, atol=1e-12, rtol=0.0)
    np.testing.assert_allclose(state, [0, 1, 0, 0], atol=1e-12, rtol=0.0)
    assert state_meta["qubit_order"] == [0, 1]
    assert state_meta["dtype"] == "complex128"


def test_projected_data_vector_fixes_reset_ancillas_and_preserves_axis_order() -> None:
    _require_arbitrary_graph_quimb()
    worker = _load_worker()
    trajectory = worker.QuimbTrajectory(
        qubit_count=3,
        edges=[(0, 1), (0, 2)],
        max_bond=2,
        rdm_radius="complete",
        device_name="cpu",
        optimize="greedy",
    )
    trajectory.apply_unitary(worker.gate_matrix("H"), [0])
    trajectory.apply_unitary(worker.gate_matrix("CX"), [0, 1])
    trajectory.apply_unitary(worker.gate_matrix("CX"), [0, 2])
    _row, reset = trajectory.measure(
        column=0,
        site=1,
        bit=1,
        reset=True,
    )

    vector, metadata = trajectory.projected_data_state_vector(
        data_qubits=[0, 2],
        reset_ancillas=[1],
    )

    assert reset["physical_one_tensor_slice_exact_zero"] is True
    np.testing.assert_allclose(vector, [0, 0, 0, 1], atol=1e-12, rtol=0.0)
    assert metadata["qubit_axis_order"] == [0, 2]
    assert metadata["q0_bit_significance"] == "most_significant"
    assert metadata["projected_ancillas"] == [1]
    assert metadata["shape"] == [4]


@pytest.mark.parametrize("device_name", ["cpu", "cuda"])
def test_copied_trajectory_applies_fresh_dynamic_gates(
    device_name: str,
) -> None:
    _require_arbitrary_graph_quimb()
    if device_name == "cuda":
        import torch

        if not torch.cuda.is_available():
            if os.environ.get("ECS_XZZX_REQUIRE_CUDA_CONTROLS") == "1":
                pytest.fail("formal XZZX controls require visible CUDA")
            pytest.skip("CUDA is unavailable")
    worker = _load_worker()
    root = worker.QuimbTrajectory(
        qubit_count=2,
        edges=[(0, 1)],
        max_bond=2,
        rdm_radius="complete",
        device_name=device_name,
        optimize="greedy",
    )
    root.apply_unitary(worker.gate_matrix("H"), [0])

    for index in range(20):
        angle = 0.07 * (index + 1)
        phase = np.exp(1.0j * angle)
        gate = np.asarray([[1.0, 0.0], [0.0, phase]], dtype=np.complex128)
        child = root.copy()
        child.apply_unitary(gate, [0])
        state, _metadata = child.complete_state_vector([0, 1])
        expected = np.asarray([1.0, 0.0, phase, 0.0], dtype=np.complex128)
        expected /= np.linalg.norm(expected)
        np.testing.assert_allclose(state, expected, atol=1e-12, rtol=0.0)
        del child, gate
        gc.collect()


def test_d2_neutral_fixture_executes_two_rounds_with_complete_graph_reset_checks() -> None:
    _require_arbitrary_graph_quimb()
    worker = _load_worker()
    emitter = _load_emitter()
    circuit, fixture = emitter.emit_fixture(stim, distance=2, rounds=2)
    run_spec = emitter.enumeration_spec(fixture)
    sampled = circuit.compile_sampler(seed=19).sample(shots=1)[0].astype(int)
    fixture_sha = emitter.canonical_json_sha256(fixture)
    spec_sha = emitter.canonical_json_sha256(run_spec)
    branch = {
        "schema": worker.BRANCH_SCHEMA,
        "fixture_sha256": fixture_sha,
        "enumeration_spec_sha256": spec_sha,
        "branch_id": "stim_viable_control",
        "distance": 2,
        "rounds": 2,
        "outcomes": [
            {"column": column, "bit": int(bit)}
            for column, bit in enumerate(sampled)
        ],
    }

    summary, state = worker.execute_candidate(
        fixture=fixture,
        run_spec=run_spec,
        branch=branch,
        max_bond=8,
        rdm_radius="complete",
        device_name="cpu",
        optimize="greedy",
        extract_state=True,
    )

    assert summary["schema"] == worker.RESULT_SCHEMA
    assert summary["status"] == "completed"
    assert summary["checkpoint"] == worker.PRETERMINAL_CHECKPOINT
    assert summary["intervention"]["applied_after_rounds"] == [0, 1]
    assert len(summary["probability_rows"]) == 10
    assert len(summary["reset_checks"]) == 6
    assert isinstance(summary["checkpoint_reset_slices"], list)
    assert [
        row["qubit"] for row in summary["checkpoint_reset_slices"]
    ] == [1, 4, 6]
    assert all(
        row["graph_coverage"]["complete"]
        for row in summary["probability_rows"]
    )
    assert all(
        row["physical_one_tensor_slice_exact_zero"]
        and row["trace_distance_to_zero"] <= 1e-10
        for row in summary["reset_checks"]
    )
    assert summary["record"]["raw_measurements"] == sampled.tolist()
    assert summary["record"]["detector_bits"] == [0, 0, 0, 0, 0]
    assert summary["record"]["observable_bits"] == [0]
    assert state is not None and state.shape == (1 << 7,)
    assert summary["branch"]["outcomes"] == branch["outcomes"]
    assert set(summary["branch"]) == set(branch)
    assert summary["forbidden_substitute_used"] is False
    assert summary["resource_usage"]["peak_device_allocated_bytes"] == 0
    assert summary["resource_usage"]["device"]["type"] == "cpu"
    assert summary["reset_gauge_policy"] == worker.RESET_GAUGE_POLICY
    assert summary["pretarget_deviation_evidence"] == (
        worker.PRETARGET_DEVIATION_EVIDENCE
    )
    assert summary["fixture"]["canonical_sha256"] == fixture_sha
    assert summary["run_spec"]["canonical_sha256"] == spec_sha
    assert summary["state"]["qubit_axis_order"] == list(range(7))
    assert summary["state"]["q0_bit_significance"] == "most_significant"
    assert summary["state"]["state_scope"] == "all_active_qubits"
    branch["outcomes"][0]["bit"] = 1 - branch["outcomes"][0]["bit"]
    assert summary["branch"]["outcomes"][0]["bit"] == int(sampled[0])


@pytest.mark.parametrize(
    ("distance", "minimum_fidelity", "maximum_probability_error"),
    [
        (2, 1.0 - 1e-10, 1e-10),
        (3, 0.99, 5e-3),
    ],
)
def test_reset_gauge_policy_survives_high_bond_evolution_and_dense_controls(
    distance: int,
    minimum_fidelity: float,
    maximum_probability_error: float,
) -> None:
    _require_arbitrary_graph_quimb()
    worker = _load_worker()
    emitter = _load_emitter()
    dense = _load_dense()
    _circuit, fixture = emitter.emit_fixture(
        stim,
        distance=distance,
        rounds=2,
    )
    spec = (
        emitter.enumeration_spec(fixture)
        if distance == 2
        else _v2_run_spec(emitter, fixture)
    )
    reference = dense.greedy_branch(
        fixture,
        branch_id=f"dense_greedy_d{distance}_reset_gauge_control",
    )
    fixture_sha = emitter.canonical_json_sha256(fixture)
    spec_sha = emitter.canonical_json_sha256(spec)
    branch = {
        "schema": worker.BRANCH_SCHEMA,
        "fixture_sha256": fixture_sha,
        (
            "enumeration_spec_sha256"
            if distance == 2
            else "run_spec_sha256"
        ): spec_sha,
        "branch_id": reference["branch_id"],
        "distance": distance,
        "rounds": 2,
        "outcomes": [
            {"column": column, "bit": int(bit)}
            for column, bit in enumerate(reference["raw_bits"])
        ],
    }

    summary, state = worker.execute_candidate(
        fixture=fixture,
        run_spec=spec,
        branch=branch,
        max_bond=8,
        rdm_radius="complete",
        device_name="cpu",
        optimize="greedy",
        extract_state=True,
    )

    assert summary["status"] == "completed"
    assert state is not None and np.isfinite(state).all()
    assert all(
        row["reset_gauge_policy"]["gauge_keys_unchanged"]
        and row["reset_gauge_policy"]["gauge_shapes_unchanged"]
        and row["reset_gauge_policy"]["gauge_dtypes_unchanged"]
        and row["reset_gauge_policy"]["gauge_bytes_unchanged"]
        and row["reset_gauge_policy"]["no_gauge_refresh"]
        and row["physical_one_tensor_slice_exact_zero"]
        for row in summary["reset_checks"]
    )
    reference_state = np.asarray(reference["preterminal_state"])
    fidelity = float(abs(np.vdot(reference_state, state)) ** 2)
    probability_error = max(
        abs(candidate["selected_probability"] - exact)
        for candidate, exact in zip(
            summary["probability_rows"],
            reference["conditional_probabilities"],
            strict=True,
        )
    )
    assert fidelity >= minimum_fidelity
    assert probability_error <= maximum_probability_error
    assert abs(
        summary["log_branch_mass"] - reference["log_branch_mass"]
    ) <= (1e-10 if distance == 2 else 1e-1)


def test_d2_full_enumeration_gate_is_hash_and_bond_bound_without_target_run() -> None:
    worker = _load_worker()
    emitter = _load_emitter()
    _circuit, fixture = emitter.emit_fixture(stim, distance=2, rounds=2)
    enumeration_spec = emitter.enumeration_spec(fixture)

    with pytest.raises(ValueError, match="requires D=8"):
        worker.enumerate_d2_laws(
            fixture=fixture,
            enumeration_spec=enumeration_spec,
            max_bond=4,
            device_name="cpu",
            optimize="greedy",
        )


def test_direct_rank_one_path_avoids_psi0_smudge_reset_contamination() -> None:
    _require_arbitrary_graph_quimb()
    worker = _load_worker()
    emitter = _load_emitter()
    _circuit, fixture = emitter.emit_fixture(stim, distance=2, rounds=2)

    control = worker.run_d2_reset_reconstruction_control(
        fixture=fixture,
        prefix=[0, 0, 0, 0, 1, 0],
        device_name="cpu",
        optimize="greedy",
    )

    assert control["prefix"] == [0, 0, 0, 0, 1, 0]
    assert control["direct_public_gate"]["trace_distance_to_zero"] <= 1e-12
    assert control["direct_public_gate"][
        "physical_one_tensor_slice_exact_zero"
    ] is True
    assert control["psi0_reconstruction"]["physical_one_weight"] > 1e-6
    assert control["psi0_reconstruction"]["hermiticity_residual"] > 1e-8
    assert control["repair_selected"] == (
        "direct_normalized_rank_one_no_reconstruction_no_repair_"
        "no_gauge_refresh"
    )


def test_cli_atomically_emits_neutral_summary_state_and_provenance(
    tmp_path: Path,
) -> None:
    _require_arbitrary_graph_quimb()
    worker = _load_worker()
    emitter = _load_emitter()
    circuit, fixture = emitter.emit_fixture(stim, distance=2, rounds=2)
    enumeration_spec = emitter.enumeration_spec(fixture)
    sampled = circuit.compile_sampler(seed=19).sample(shots=1)[0].astype(int)
    branch = {
        "schema": worker.BRANCH_SCHEMA,
        "fixture_sha256": emitter.canonical_json_sha256(fixture),
        "enumeration_spec_sha256": emitter.canonical_json_sha256(
            enumeration_spec
        ),
        "branch_id": "cli-smoke",
        "distance": 2,
        "rounds": 2,
        "outcomes": [
            {"column": column, "bit": int(bit)}
            for column, bit in enumerate(sampled)
        ],
    }
    fixture_path = tmp_path / "fixture.json"
    spec_path = tmp_path / "spec.json"
    branch_path = tmp_path / "branch.json"
    summary_path = tmp_path / "summary.json"
    state_path = tmp_path / "state.npy"
    fixture_path.write_bytes(emitter.canonical_json_bytes(fixture))
    spec_path.write_bytes(emitter.canonical_json_bytes(enumeration_spec))
    branch_path.write_bytes(emitter.canonical_json_bytes(branch))
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop("VIRTUAL_ENV", None)
    environment["PYTHONNOUSERSITE"] = "1"

    subprocess.run(
        [
            sys.executable,
            str(WORKER_PATH),
            "--fixture",
            str(fixture_path),
            "--run-spec",
            str(spec_path),
            "--branch",
            str(branch_path),
            "--D",
            "8",
            "--rdm-radius",
            "complete",
            "--device",
            "cpu",
            "--optimize",
            "greedy",
            "--pretarget-smoke",
            "--output-summary",
            str(summary_path),
            "--output-state",
            str(state_path),
        ],
        cwd=REPO,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    state = np.load(state_path, allow_pickle=False)
    assert summary["schema"] == worker.RESULT_SCHEMA
    assert summary["status"] == "pretarget_smoke"
    assert summary["formal_target_output"] is False
    assert summary["state"]["path"] == str(state_path.resolve())
    assert summary["state"]["file_sha256"] == worker._file_sha256(state_path)
    assert state.shape == (1 << 7,)
    assert summary["provenance"]["quimb_clone"]["commit"] == (
        worker.EXPECTED_QUIMB_COMMIT
    )
    assert summary["provenance"]["selective_update_adapter"]["selected"] == (
        "CircuitPEPSSimpleUpdate.copy with private backend cache + "
        "apply_gate(Gate.from_raw(A_b/sqrt(p_b))) + preserve pre-reset "
        "simple-update gauges byte-for-byte"
    )
    assert summary["provenance"]["environment_lock"][
        "authoritative_runtime_conformance_checked"
    ] is True
    assert summary["provenance"]["environment_lock"][
        "pip_distribution_records_exact"
    ] is True
    assert summary["provenance"]["environment_lock"][
        "installed_quimb_source_bytes_exact"
    ] is True
    assert summary["resource_usage"]["peak_device_allocated_bytes"] == 0
    assert summary["resource_limits"]["all_limits_passed"] is True
    assert summary["branch_authority"] is None
    assert summary["exact_reference_authority_source"] is None
    assert summary["provenance"]["repository_inputs"][
        "formal_target_commit_gate_required_for_this_run"
    ] is False
    assert summary["provenance"]["repository_inputs"][
        "frozen_v2_preregistration"
    ]["matches_freeze_commit"] is True
    assert summary["output"]["atomic_write"] is True
