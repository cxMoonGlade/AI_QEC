from __future__ import annotations

import base64
import copy
import hashlib
import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT
    / "scripts"
    / "external_baselines"
    / "compare_gcapeps_finite_memory_bond32.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("gcapeps_fm_comparator", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _encoded(array):
    raw = array.tobytes(order="C")
    return {
        "encoding": "ndarray-v1",
        "dtype": array.dtype.str,
        "shape": list(array.shape),
        "order": "C",
        "nbytes": len(raw),
        "data_sha256": hashlib.sha256(raw).hexdigest(),
        "data_base64": base64.b64encode(raw).decode("ascii"),
    }


def test_ndarray_v1_round_trip_preserves_exact_bits_and_rejects_corruption():
    comparator = _load_module()
    array = np.asarray([complex(-0.0, 1.25), 2.0 - 3.0j], dtype="<c16")
    payload = _encoded(array)
    decoded = comparator.decode_ndarray_v1(
        payload,
        dtype="<c16",
        shape=(2,),
    )
    assert decoded.tobytes(order="C") == array.tobytes(order="C")

    bad = copy.deepcopy(payload)
    bad["data_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="hash mismatch"):
        comparator.decode_ndarray_v1(bad, dtype="<c16", shape=(2,))

    bad = copy.deepcopy(payload)
    bad["data_base64"] = bad["data_base64"].rstrip("=")
    with pytest.raises(ValueError):
        comparator.decode_ndarray_v1(bad, dtype="<c16", shape=(2,))


def test_comparator_array_sampler_deduplicates_roots_and_samples_release_peak():
    comparator = _load_module()
    sampler = comparator.ComparatorArraySampler()
    root = np.arange(64, dtype=np.uint8)
    alias = root.reshape((8, 8))
    other = np.zeros(3, dtype="<c16")

    assert sampler.materialized(root, alias) == root.nbytes
    assert sampler.materialized(other) == root.nbytes + other.nbytes
    assert sampler.maximum_bytes == root.nbytes + other.nbytes

    assert sampler.release(root) == root.nbytes + other.nbytes
    assert sampler.release(alias) == other.nbytes
    assert sampler.release(other) == 0
    assert sampler.maximum_bytes == root.nbytes + other.nbytes
    with pytest.raises(ValueError, match="unowned"):
        sampler.release(other)


def test_ndarray_decode_enters_and_leaves_comparator_array_ownership():
    comparator = _load_module()
    sampler = comparator.ComparatorArraySampler()
    array = np.asarray([1.0 + 2.0j, 3.0 - 4.0j], dtype="<c16")

    decoded = comparator.decode_ndarray_v1(
        _encoded(array),
        dtype="<c16",
        shape=(2,),
        sampler=sampler,
    )
    assert sampler.current_bytes == array.nbytes
    assert sampler.maximum_bytes == array.nbytes
    assert sampler.release(decoded) == 0


def test_metric_array_sampler_covers_auxiliaries_and_releases_to_inputs():
    comparator = _load_module()
    sampler = comparator.ComparatorArraySampler()
    reference = np.asarray([1.0, 0.0, 0.0, 0.0], dtype="<c16")
    candidate = np.asarray([0.8, 0.0, 0.6, 0.0], dtype="<c16")
    sampler.materialized(reference, candidate)
    input_bytes = reference.nbytes + candidate.nbytes

    comparator.whole_state_metrics(
        reference,
        candidate,
        width=1,
        sampler=sampler,
    )

    assert sampler.current_bytes == input_bytes
    assert sampler.maximum_bytes > input_bytes
    assert sampler.release(reference, candidate) == 0


def test_whole_state_known_answers_include_raw_and_normalized_metrics():
    comparator = _load_module()
    reference = np.asarray([1.0, 0.0, 0.0, 0.0], dtype="<c16")
    candidate = np.asarray([0.8, 0.0, 0.6, 0.0], dtype="<c16")
    metrics = comparator.whole_state_metrics(
        reference,
        candidate,
        width=1,
    )
    assert metrics["fidelity"] == pytest.approx(0.64)
    assert metrics["pure_state_trace_distance"] == pytest.approx(0.6)
    assert metrics["d2_raw"] == pytest.approx((0.2**2 + 0.6**2) ** 0.5)
    assert metrics["dinf_raw"] == pytest.approx(0.6)
    assert metrics["reference_raw_norm"] == pytest.approx(1.0)
    assert metrics["candidate_raw_norm"] == pytest.approx(1.0)
    assert metrics["signed_raw_norm_error"] == pytest.approx(0.0)
    assert metrics["relative_norm_distance"] == pytest.approx(0.0)
    assert metrics["entropy_von_neumann_error"] == pytest.approx(0.0)


def test_metrics_do_not_phase_fit():
    comparator = _load_module()
    reference = np.asarray([1.0, 1.0, 0.0, 0.0], dtype="<c16")
    candidate = np.asarray([1.0j, 1.0j, 0.0, 0.0], dtype="<c16")
    metrics = comparator.whole_state_metrics(reference, candidate, width=1)
    assert metrics["fidelity"] == pytest.approx(1.0)
    assert metrics["d2_raw"] == pytest.approx(2.0)
    assert metrics["d2_normalized"] == pytest.approx(2.0**0.5)


def test_q0_msb_reduction_and_pair_trace_distance():
    comparator = _load_module()
    zero = np.asarray([1.0, 0.0, 0.0, 0.0], dtype="<c16")
    system_one = np.asarray([0.0, 0.0, 1.0, 0.0], dtype="<c16")
    memory_one = np.asarray([0.0, 1.0, 0.0, 0.0], dtype="<c16")
    assert comparator.fixed_pair_checkpoint_error(
        zero,
        system_one,
        zero,
        system_one,
        width=1,
    )["dense_fixed_pair_trace_distance"] == pytest.approx(1.0)
    assert comparator.fixed_pair_checkpoint_error(
        zero,
        memory_one,
        zero,
        memory_one,
        width=1,
    )["dense_fixed_pair_trace_distance"] == pytest.approx(0.0)


def test_vector_gate_fails_before_metrics_on_dtype_shape_norm_and_nonfinite():
    comparator = _load_module()
    with pytest.raises(TypeError, match="dtype"):
        comparator.vector_gate(np.ones(4, dtype=np.complex64), width=1)
    with pytest.raises(ValueError, match="shape"):
        comparator.vector_gate(np.ones(2, dtype="<c16"), width=1)
    with pytest.raises(ValueError, match="strictly positive"):
        comparator.vector_gate(np.zeros(4, dtype="<c16"), width=1)
    bad = np.ones(4, dtype="<c16")
    bad[0] = np.nan
    with pytest.raises(ValueError, match="non-finite"):
        comparator.vector_gate(bad, width=1)


def test_stress_delta_f_reports_both_directions_and_tie():
    comparator = _load_module()
    assert comparator.stress_delta_f(
        plain_fidelities={"input1": 0.8, "input2": 0.9},
        gcapeps_fidelities={"input1": 0.85, "input2": 0.95},
    )["direction"] == "gcapeps_higher"
    assert comparator.stress_delta_f(
        plain_fidelities={"input1": 0.9, "input2": 0.95},
        gcapeps_fidelities={"input1": 0.8, "input2": 0.85},
    )["direction"] == "plain_higher"
    assert comparator.stress_delta_f(
        plain_fidelities={"input1": 0.9, "input2": 0.8},
        gcapeps_fidelities={"input1": 0.8, "input2": 0.9},
    )["direction"] == "tie"


def test_comparator_source_has_no_forbidden_imports():
    source = MODULE_PATH.read_text(encoding="utf-8")
    for forbidden in (
        "import quimb",
        "from quimb",
        "import stim",
        "from stim",
        "import sdim",
        "from sdim",
        "import error_coupling_simulator",
        "from error_coupling_simulator",
    ):
        assert forbidden not in source


def _load_sibling(filename: str, module_name: str):
    path = ROOT / "scripts" / "external_baselines" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _rehash(core, comparator):
    core["result_projection_sha256"] = comparator.projection_sha256(core)


def _pre_metric(vector):
    raw = vector.tobytes(order="C")
    z = np.vdot(vector, vector)
    return {
        "raw_vector_sha256": hashlib.sha256(raw).hexdigest(),
        "raw_norm_squared_real": float(z.real),
        "raw_norm_squared_imag_abs": abs(float(z.imag)),
        "stored_vector_normalized_before_metric": False,
        "metric_local_normalized_copy": True,
        "phase_fit": False,
        "coordinate_permutation": False,
        "dtype_cast": False,
    }


def _fixture_operations(fixture):
    return [
        operation
        for round_row in fixture["carrier_path"]["round_ledger"]
        for operation in round_row["operations"]
    ]


def _bind_split(*, comparator, lane, row):
    row.pop("spectrum_producer_binding_sha256", None)
    projection = {
        "schema": (
            "error_coupling_simulator.external.gcapeps_finite_memory."
            "split_spectrum_producer.v1"
        ),
        "lane": lane,
        "split_row": row,
    }
    row["spectrum_producer_binding_sha256"] = hashlib.sha256(
        comparator.canonical_json_bytes(projection)
    ).hexdigest()
    return row


def _positive_split(*, comparator, lane, operation, split_index=None, edge=None):
    scale = 1.0 + 0.01 * operation["operation_index"]
    full = np.ascontiguousarray(
        np.linspace(2.0, 1.0, 33, dtype="<f8") * scale,
        dtype="<f8",
    )
    kept = full[:32].copy(order="C")
    pre_weight = float(np.sum(np.square(full)))
    discarded = float(np.sum(np.square(full[32:])))
    state_hash = hashlib.sha256(
        f"{lane}:{operation['operation_index']}:{split_index}".encode("ascii")
    ).hexdigest()
    row = {
        "operation_index": operation["operation_index"],
        "round_index": operation["round_index"],
        "collision_ordinal": operation.get("collision_ordinal"),
        "pre_split_state_sha256": state_hash,
        "shadow_pre_split_state_sha256": state_hash,
        "configured_max_bond": 32,
        "configured_cutoff": 0.0,
        "configured_cutoff_mode": "rel",
        "configured_method": "svd",
        "configured_renorm": False,
        "configured_absorb": None,
        "configured_power": 1.0,
        "configured_smudge": 1.0e-12,
        "full_singular_values": _encoded(full),
        "kept_singular_values": _encoded(kept),
        "full_bond_dimension": 33,
        "kept_bond_dimension": 32,
        "discarded_squared_weight": discarded,
        "discarded_fraction": discarded / pre_weight,
        "cause": "max_bond",
        "positive_discarded_weight": True,
        "positive_discarded_weight_threshold": 1.0e-12,
    }
    if lane == "plain":
        row.update(
            {
                "pre_split_weight": pre_weight,
                "ordered_sites": operation["targets"],
                "eligible_edges": [operation["targets"]],
                "materialized_zero_gauge_edges": [],
                "smudge_actually_used": False,
            }
        )
    else:
        assert split_index is not None and edge is not None
        row.update(
            {
                "split_index": split_index,
                "edge": edge,
                "bond_index_before": f"before-{operation['operation_index']}",
                "bond_index_after": f"after-{operation['operation_index']}",
                "exact_precompression_bond": 33,
                "low_level_contract": "reduce-split",
                "identity_matrix_sha256": "e" * 64,
                "stripped_high_level_keys": [],
                "selected_gauges": [],
                "smudge_actually_used": False,
                "shadow_evidence_enabled": True,
                "dimension_reduced": True,
                "physical_gate_count_before": 0,
                "physical_gate_count_after": 0,
                "info_mapping_was_fresh_and_empty": True,
                "not_a_global_error_bound": True,
            }
        )
    return _bind_split(comparator=comparator, lane=lane, row=row)


def _algorithm_ledger(fixture):
    rows = []
    collision_epoch = 0
    for operation in _fixture_operations(fixture):
        common = {
            "column": operation["operation_index"],
            "round_index": operation["round_index"],
            "operation": (
                "clifford_frame_update"
                if operation["operation_class"] == "clifford"
                else "pulled_pauli_rotation"
            ),
            "frame_revision_before": operation["operation_index"],
            "frame_revision_after": operation["operation_index"] + 1,
            "residual_revision_before": collision_epoch,
            "residual_revision_after": collision_epoch,
        }
        if operation["operation_class"] == "clifford":
            rows.append(common)
            continue
        edge = copy.deepcopy(operation["targets"])
        compression = {
            "compression_revision": "test-tree-compression-v1",
            "construction_epoch_before": collision_epoch,
            "construction_epoch_after": collision_epoch + 1,
            "routed_edge_order": [edge],
            "configured_max_bond": 32,
            "configured_cutoff": 0.0,
            "configured_cutoff_mode": "rel",
            "configured_method": "svd",
            "configured_renorm": False,
            "configured_absorb": None,
            "configured_smudge": 1.0e-12,
            "configured_power": 1.0,
            "low_level_contract": "reduce-split",
            "routed_split_count": 1,
            "physical_gate_count_before": 0,
            "physical_gate_count_after": 0,
            "product_maps_reset_to_one_on_commit": True,
            "counterfactual_lifetime_product_only": True,
            "not_a_global_error_bound": True,
        }
        rows.append(
            {
                **common,
                "physical_pauli": operation["physical_pauli_body"],
                "pulled_back_pauli": operation["physical_pauli_body"],
                "strategy": "exact_tree_then_native_identity_compress",
                "support": operation["targets"],
                "dependence_set": operation["targets"],
                "routing_root": operation["targets"][0],
                "routing_vertices": operation["targets"],
                "routing_tree_edges": [edge],
                "max_bond_before": 32,
                "max_bond_after": 32,
                "construction_epoch_before": collision_epoch,
                "construction_epoch_after": collision_epoch + 1,
                "edge_bonds": [],
                "resource_ledger": {},
                "compression": compression,
            }
        )
        rows[-1]["residual_revision_after"] = collision_epoch + 1
        collision_epoch += 1
    return rows


def _memory_sample(*, label, tensor_role, scale=1, evidence=False):
    if tensor_role == "none":
        carrier = gauges = frame = ledger = 0
    else:
        carrier = 100 * scale
        gauges = 10 * scale
        frame = 0 if tensor_role == "plain_physical" else 7 * scale
        ledger = 20 * scale
    auxiliary_arrays = 1000 * scale if evidence else 0
    auxiliary_ledger = 100 * scale if evidence else 0
    total = carrier + gauges + frame + ledger
    return {
        "label": label,
        "tensor_role": tensor_role,
        "carrier_tensor_bytes": carrier,
        "gauge_spectrum_bytes": gauges,
        "frame_bytes": frame,
        "ledger_bytes": ledger,
        "total_owned_logical_bytes": total,
        "evidence_auxiliary_array_bytes": auxiliary_arrays,
        "evidence_auxiliary_ledger_bytes": auxiliary_ledger,
        "evidence_owned_logical_bytes": (
            total + auxiliary_arrays + auxiliary_ledger
        ),
    }


def _logical_memory_reports(*, comparator, lane):
    tensor_role = "plain_physical" if lane == "plain" else "gc_residual"
    final_sample = _memory_sample(
        label="final_committed",
        tensor_role=tensor_role,
        scale=1,
    )
    max_committed_sample = _memory_sample(
        label="max_committed",
        tensor_role=tensor_role,
        scale=2,
    )
    max_algorithm_sample = _memory_sample(
        label="max_algorithm",
        tensor_role=tensor_role,
        scale=3,
    )
    base = {
        "schema": comparator.LOGICAL_MEMORY_SCHEMA,
        "tensor_role": tensor_role,
        "sample_count": 3,
        "final_committed_owned_logical_bytes": final_sample[
            "total_owned_logical_bytes"
        ],
        "max_committed_owned_logical_bytes": max_committed_sample[
            "total_owned_logical_bytes"
        ],
        "max_sampled_algorithm_owned_logical_bytes": max_algorithm_sample[
            "total_owned_logical_bytes"
        ],
        "final_committed_sample": final_sample,
        "max_committed_sample": max_committed_sample,
        "max_sampled_algorithm_sample": max_algorithm_sample,
    }
    evidence_sample = _memory_sample(
        label="instrumented_shadow",
        tensor_role="none",
        scale=4,
        evidence=True,
    )
    evidence_report = copy.deepcopy(base)
    evidence_report.update(
        {
            "sample_count": 7,
            "max_sampled_evidence_owned_logical_bytes": evidence_sample[
                "evidence_owned_logical_bytes"
            ],
            "max_sampled_evidence_sample": evidence_sample,
        }
    )
    return base, evidence_report


def _candidate_core(
    *, comparator, dense_core, fixture, lane, input_id, signed_rows
):
    dense_path = dense_core["fixed_paths"][input_id - 1]
    dense_by_round = {
        checkpoint["round_index"]: checkpoint
        for checkpoint in dense_path["checkpoints"]
    }
    checkpoints = []
    for round_index in fixture["checkpoints"]:
        vector = comparator.decode_ndarray_v1(
            dense_by_round[round_index]["vector"],
            dtype="<c16",
            shape=(2 ** fixture["geometry"]["n_qubits"],),
        )
        checkpoints.append(
            {
                "round_index": round_index,
                "source_branch": "instrumented_replay",
                "pre_metric": _pre_metric(vector),
                "vector": _encoded(vector),
            }
        )
    operations = _fixture_operations(fixture)
    operation_count = len(operations)
    final_carrier_hash = {
        "sha256": hashlib.sha256(
            f"{lane}:{input_id}".encode("ascii")
        ).hexdigest()
    }
    prior_end = hashlib.sha256(
        f"{lane}:{input_id}:initial".encode("ascii")
    ).hexdigest()
    continuity = []
    for round_index in range(1, fixture["parameters"]["rounds"] + 1):
        round_end = (
            final_carrier_hash["sha256"]
            if round_index == fixture["parameters"]["rounds"]
            else hashlib.sha256(
                f"{lane}:{input_id}:round:{round_index}".encode("ascii")
            ).hexdigest()
        )
        continuity.append(
            {
                "round_index": round_index,
                "prior_round_end_state_sha256": prior_end,
                "round_start_state_sha256": prior_end,
                "round_end_state_sha256": round_end,
                "starts_from_prior_round_end": True,
                "candidate_restarted_between_rounds": False,
                "memory_reset_between_rounds": False,
            }
        )
        prior_end = round_end
    algorithm_ledger = _algorithm_ledger(fixture)
    if lane == "plain":
        split_records = [
            _positive_split(
                comparator=comparator,
                lane=lane,
                operation=operation,
            )
            for operation in operations
            if len(operation["targets"]) == 2
        ]
    else:
        collision_rows = {
            row["column"]: row
            for row in algorithm_ledger
            if "compression" in row
        }
        split_records = []
        for operation in operations:
            if operation["operation_class"] != "collision_rotation":
                continue
            for split_index, edge in enumerate(
                collision_rows[operation["operation_index"]]["compression"][
                    "routed_edge_order"
                ]
            ):
                split_records.append(
                    _positive_split(
                        comparator=comparator,
                        lane=lane,
                        operation=operation,
                        split_index=split_index,
                        edge=edge,
                    )
                )
    no_shadow_memory, evidence_memory = _logical_memory_reports(
        comparator=comparator,
        lane=lane,
    )
    no_shadow = {
        "operation_count": operation_count,
        "max_committed_bond": 32,
        "final_committed_bond": 32,
        "final_carrier_hash": final_carrier_hash,
        "logical_memory": no_shadow_memory,
        "round_continuity_ledger": copy.deepcopy(continuity),
    }
    if lane == "gcapeps":
        no_shadow.update(
            {
                "max_exact_precompression_bond": 33,
                "algorithm_ledger": copy.deepcopy(algorithm_ledger),
            }
        )
    core = {
        "schema": (
            comparator.PLAIN_EVIDENCE_SCHEMA
            if lane == "plain"
            else comparator.GCAPEPS_EVIDENCE_SCHEMA
        ),
        "lane": lane,
        "role": "evidence",
        "case_id": fixture["case_id"],
        "input_id": input_id,
        "fixture_projection_sha256": fixture["result_projection_sha256"],
        "no_shadow": no_shadow,
        "instrumented_final_carrier_hash": final_carrier_hash,
        "operation_count": operation_count,
        "max_exact_precompression_bond": None if lane == "plain" else 33,
        "max_committed_bond": 32,
        "final_committed_bond": 32,
        "positive_cap_event_count": len(split_records),
        "split_records": split_records,
        "round_continuity_ledger": continuity,
        "checkpoints": checkpoints,
        "logical_memory": evidence_memory,
        "contains_cross_artifact_metric": False,
        "result_projection_sha256": "",
    }
    if lane == "gcapeps":
        core["signed_pullback_rows"] = signed_rows
        core["instrumented_algorithm_ledger"] = copy.deepcopy(
            algorithm_ledger
        )
    _rehash(core, comparator)
    return core


def _signed_artifacts(*, comparator, fixture):
    n_qubits = fixture["geometry"]["n_qubits"]
    requests = copy.deepcopy(fixture["sdim_pullback_requests"])
    sdim_rows = [
        {**row, "sdim_sign": 1, "sdim_body": "I" * n_qubits}
        for row in requests
    ]
    stim_rows = [
        {**row, "stim_sign": 1, "stim_body": "I" * n_qubits}
        for row in requests
    ]
    joined_rows = [
        {
            **row,
            "sdim_sign": 1,
            "sdim_body": "I" * n_qubits,
            "stim_sign": 1,
            "stim_body": "I" * n_qubits,
            "sdim_equals_stim": True,
        }
        for row in requests
    ]
    gc_rows = {
        input_id: [
            {
                **row,
                "physical_sign": 1,
                "physical_body": row["physical_pauli_body"],
                "pulled_back_sign": 1,
                "pulled_back_body": "I" * n_qubits,
            }
            for row in requests
            if row["input_id"] == input_id
        ]
        for input_id in (1, 2)
    }
    count = len(requests)
    sdim_core = {
        "schema": comparator.SDIM_SCHEMA,
        "role": "sdim_stim_qubit_frame_corroboration",
        "fixture_identity": {
            "schema": fixture["schema"],
            "fixture_projection_sha256": fixture[
                "result_projection_sha256"
            ],
            "run_partition": fixture["run_partition"],
            "case_id": fixture["case_id"],
            "width": fixture["geometry"]["width"],
            "n_qubits": n_qubits,
            "request_count": count,
        },
        "inventory_binding": {
            "schema": "test.inventory.v1",
            "inventory_state_sha256": "a" * 64,
            "inventory_result_projection_sha256": "b" * 64,
        },
        "scope": {"qubit_only": True},
        "expected_key_sequence": requests,
        "sdim_rows": sdim_rows,
        "stim_rows": stim_rows,
        "pullback_rows": joined_rows,
        "coverage": {
            "expected_count": count,
            "sdim_count": count,
            "stim_count": count,
            "joined_count": count,
            "expected_sdim_stim_exact_ordered_sequence": True,
            "duplicates_rejected_before_join": True,
            "empty_sequence_legal_only_if_fixture_empty": True,
        },
        "sdim_equals_stim": True,
        "result_projection_sha256": "",
    }
    _rehash(sdim_core, comparator)
    return sdim_core, gc_rows


@pytest.fixture()
def artifact_bundle():
    comparator = _load_module()
    fixture_owner = _load_sibling(
        "emit_gcapeps_finite_memory_fixture.py",
        "_gcapeps_comparator_fixture_owner",
    )
    dense_owner = _load_sibling(
        "gcapeps_finite_memory_dense_reference.py",
        "_gcapeps_comparator_dense_owner",
    )
    fixture = fixture_owner.build_fixture(
        run_partition="HELDOUT",
        width=3,
        rounds=1,
        axis_family=3,
        p_event_numerator=4,
        seed=fixture_owner.HELDOUT_SEED,
        gamma_index=0,
        run_blpensemble=False,
    )
    dense_core = dense_owner.build_core_payload(fixture)
    sdim_core, gc_rows = _signed_artifacts(
        comparator=comparator, fixture=fixture
    )
    bundle = {
        "fixture": fixture,
        "dense_core": dense_core,
        "plain_input1_core": _candidate_core(
            comparator=comparator,
            dense_core=dense_core,
            fixture=fixture,
            lane="plain",
            input_id=1,
            signed_rows=None,
        ),
        "plain_input2_core": _candidate_core(
            comparator=comparator,
            dense_core=dense_core,
            fixture=fixture,
            lane="plain",
            input_id=2,
            signed_rows=None,
        ),
        "gcapeps_input1_core": _candidate_core(
            comparator=comparator,
            dense_core=dense_core,
            fixture=fixture,
            lane="gcapeps",
            input_id=1,
            signed_rows=gc_rows[1],
        ),
        "gcapeps_input2_core": _candidate_core(
            comparator=comparator,
            dense_core=dense_core,
            fixture=fixture,
            lane="gcapeps",
            input_id=2,
            signed_rows=gc_rows[2],
        ),
        "sdim_core": sdim_core,
    }
    return comparator, bundle


def _build(comparator, bundle):
    return comparator.build_comparator_core(**bundle)


def test_terminal_artifact_join_computes_metrics_and_four_path_gate(
    artifact_bundle,
):
    comparator, bundle = artifact_bundle
    core = _build(comparator, bundle)
    assert core["pullback_join"][
        "exact_unique_ordered_E_equals_S_equals_T_equals_G"
    ]
    assert core["pullback_join"]["signed_values_equal_after_coverage"]
    assert core["positive_bond32_gate"]["all_four_paths_positive"]
    assert len(core["positive_bond32_gate"]["paths"]) == 4
    assert [row["round_index"] for row in core["checkpoint_metrics"]] == [0, 1]
    for checkpoint in core["checkpoint_metrics"]:
        for lane in ("plain", "gcapeps"):
            assert checkpoint[lane]["input1"]["fidelity"] == pytest.approx(1.0)
            assert checkpoint[lane]["input2"]["fidelity"] == pytest.approx(1.0)
            assert checkpoint[lane]["fixed_pair_checkpoint_error"][
                "absolute_trace_distance_error"
            ] == pytest.approx(0.0)
    final = core["final_bond32_faithfulness"]
    assert final["delta_f"]["delta_fidelity"] == pytest.approx(0.0)
    assert "verdict" not in final
    assert final[
        "h_f_applicability_deferred_to_amendment_bound_stress_cell"
    ] is True
    assert final[
        "conditional_h_f_verdict_if_amendment_bound_stress_cell"
    ] == "tie/inconclusive"
    retained_vector_floor = sum(
        checkpoint["vector"]["nbytes"]
        for path in bundle["dense_core"]["fixed_paths"]
        for checkpoint in path["checkpoints"]
    ) + sum(
        checkpoint["vector"]["nbytes"]
        for key, candidate_core in bundle.items()
        if key.startswith(("plain_input", "gcapeps_input"))
        for checkpoint in candidate_core["checkpoints"]
    )
    assert core["max_sampled_comparator_array_bytes"] > retained_vector_floor
    assert core["result_projection_sha256"] == comparator.projection_sha256(core)


@pytest.mark.parametrize("corruption", [False, 0, -1, 1.5])
def test_comparator_peak_array_bytes_rejects_corruption(
    artifact_bundle,
    corruption,
):
    comparator, bundle = artifact_bundle
    core = _build(comparator, bundle)
    core["max_sampled_comparator_array_bytes"] = corruption
    _rehash(core, comparator)
    with pytest.raises(ValueError, match="max_sampled_comparator_array_bytes"):
        comparator.validate_comparator_core(core)

@pytest.mark.parametrize(
    "mutation",
    (
        "artifact_binding",
        "pullback_join",
        "positive_gate",
        "locator_duplicate",
        "locator_round",
        "locator_cause",
        "candidate_bond",
        "gc_exact_bond",
        "checkpoint_metric",
        "final_faithfulness",
        "claim_boundary",
    ),
)
def test_public_comparator_validator_rechecks_every_derived_section(
    artifact_bundle,
    mutation,
):
    comparator, bundle = artifact_bundle
    core = _build(comparator, bundle)
    if mutation == "artifact_binding":
        core["artifact_bindings"]["dense"] = "not-a-sha256"
    elif mutation == "pullback_join":
        core["pullback_join"]["signed_values_equal_after_coverage"] = False
    elif mutation == "positive_gate":
        core["positive_bond32_gate"]["paths"][0][
            "qualifying_event_locators"
        ][0] = {}
    elif mutation == "locator_duplicate":
        locators = core["positive_bond32_gate"]["paths"][0][
            "qualifying_event_locators"
        ]
        locators[1] = copy.deepcopy(locators[0])
    elif mutation == "locator_round":
        core["positive_bond32_gate"]["paths"][0][
            "qualifying_event_locators"
        ][0]["round_index"] = 0
    elif mutation == "locator_cause":
        core["positive_bond32_gate"]["paths"][0][
            "qualifying_event_locators"
        ][0]["cause"] = "none"
    elif mutation == "candidate_bond":
        core["candidate_bonds"]["plain"]["input1"][
            "final_committed_bond"
        ] = 33
    elif mutation == "gc_exact_bond":
        core["candidate_bonds"]["gcapeps"]["input1"][
            "max_exact_precompression_bond"
        ] = 1
    elif mutation == "checkpoint_metric":
        core["checkpoint_metrics"][-1]["plain"]["input1"][
            "pure_state_trace_distance"
        ] += 0.1
    elif mutation == "final_faithfulness":
        core["final_bond32_faithfulness"]["delta_f"][
            "delta_fidelity"
        ] += 0.1
    else:
        core["claim_boundary"] += "; widened"
    _rehash(core, comparator)
    with pytest.raises(ValueError):
        comparator.validate_comparator_core(core)



@pytest.mark.parametrize(
    "mutation",
    (
        "base_projection_drift",
        "missing_evidence_peak",
        "nonextended_sample_count",
        "evidence_in_no_shadow",
    ),
)
def test_terminal_join_rejects_logical_memory_branch_evasion(
    artifact_bundle,
    mutation,
):
    comparator, original = artifact_bundle
    bundle = copy.deepcopy(original)
    candidate = bundle["plain_input1_core"]
    base = candidate["no_shadow"]["logical_memory"]
    evidence = candidate["logical_memory"]
    if mutation == "base_projection_drift":
        evidence["max_committed_sample"]["label"] = "drifted"
    elif mutation == "missing_evidence_peak":
        evidence.pop("max_sampled_evidence_owned_logical_bytes")
        evidence.pop("max_sampled_evidence_sample")
    elif mutation == "nonextended_sample_count":
        evidence["sample_count"] = base["sample_count"]
    else:
        base.update(
            {
                "max_sampled_evidence_owned_logical_bytes": 1,
                "max_sampled_evidence_sample": _memory_sample(
                    label="forbidden",
                    tensor_role="none",
                    evidence=True,
                ),
            }
        )
    _rehash(candidate, comparator)
    with pytest.raises(ValueError, match="memory|no-shadow"):
        _build(comparator, bundle)


@pytest.mark.parametrize("mutation", ["missing", "extra"])
def test_terminal_join_rejects_missing_and_extra_G_rows(
    artifact_bundle, mutation
):
    comparator, original = artifact_bundle
    bundle = copy.deepcopy(original)
    rows = bundle["gcapeps_input2_core"]["signed_pullback_rows"]
    if mutation == "missing":
        rows.pop()
    else:
        extra = copy.deepcopy(rows[-1])
        extra["collision_ordinal"] += 1000
        rows.append(extra)
    _rehash(bundle["gcapeps_input2_core"], comparator)
    with pytest.raises(ValueError, match="coverage gate"):
        _build(comparator, bundle)


def test_terminal_join_rejects_local_and_cross_artifact_duplicates(
    artifact_bundle,
):
    comparator, original = artifact_bundle

    local = copy.deepcopy(original)
    rows = local["sdim_core"]["sdim_rows"]
    rows.insert(1, copy.deepcopy(rows[0]))
    _rehash(local["sdim_core"], comparator)
    with pytest.raises(ValueError, match="duplicate request key"):
        _build(comparator, local)

    cross = copy.deepcopy(original)
    duplicate = copy.deepcopy(
        cross["gcapeps_input1_core"]["signed_pullback_rows"][0]
    )
    cross["gcapeps_input2_core"]["signed_pullback_rows"].insert(0, duplicate)
    _rehash(cross["gcapeps_input2_core"], comparator)
    with pytest.raises(ValueError, match="duplicate key across artifacts"):
        _build(comparator, cross)


def test_terminal_join_rejects_reordered_rows_before_signed_values(
    artifact_bundle,
):
    comparator, original = artifact_bundle
    bundle = copy.deepcopy(original)
    bundle["sdim_core"]["stim_rows"].reverse()
    _rehash(bundle["sdim_core"], comparator)
    with pytest.raises(ValueError, match="exact lexicographic order"):
        _build(comparator, bundle)


def test_terminal_join_rejects_signed_value_corruption_after_coverage(
    artifact_bundle,
):
    comparator, original = artifact_bundle
    bundle = copy.deepcopy(original)
    row = bundle["gcapeps_input1_core"]["signed_pullback_rows"][0]
    row["pulled_back_sign"] *= -1
    _rehash(bundle["gcapeps_input1_core"], comparator)
    with pytest.raises(ValueError, match="signed pullback value mismatch"):
        _build(comparator, bundle)


def test_terminal_join_rejects_candidate_vector_corruption_via_raw_gate(
    artifact_bundle,
):
    comparator, original = artifact_bundle
    bundle = copy.deepcopy(original)
    checkpoint = bundle["plain_input1_core"]["checkpoints"][-1]
    vector = comparator.decode_ndarray_v1(
        checkpoint["vector"], dtype="<c16", shape=(64,)
    )
    vector[0] += 0.125j
    checkpoint["vector"] = _encoded(vector)
    _rehash(bundle["plain_input1_core"], comparator)
    with pytest.raises(ValueError, match="disagrees with the transported raw vector"):
        _build(comparator, bundle)


def test_terminal_join_rejects_positive_flag_forgery_from_spectrum(
    artifact_bundle,
):
    comparator, original = artifact_bundle
    bundle = copy.deepcopy(original)
    core = bundle["gcapeps_input2_core"]
    core["split_records"][0]["positive_discarded_weight"] = False
    core["positive_cap_event_count"] = 0
    _bind_split(
        comparator=comparator,
        lane="gcapeps",
        row=core["split_records"][0],
    )
    _rehash(core, comparator)
    with pytest.raises(ValueError, match="positive flag disagrees"):
        _build(comparator, bundle)


@pytest.mark.parametrize("lane", ["plain", "gcapeps"])
@pytest.mark.parametrize("mutation", ["missing", "extra"])
def test_terminal_join_rejects_nonexact_split_schema(
    artifact_bundle,
    lane,
    mutation,
):
    comparator, original = artifact_bundle
    bundle = copy.deepcopy(original)
    core = bundle[f"{lane}_input1_core"]
    row = core["split_records"][0]
    if mutation == "missing":
        row.pop("pre_split_state_sha256")
    else:
        row["unregistered_split_field"] = True
    _rehash(core, comparator)
    with pytest.raises(ValueError, match="key mismatch"):
        _build(comparator, bundle)


@pytest.mark.parametrize("lane", ["plain", "gcapeps"])
@pytest.mark.parametrize("mutation", ["evidence", "whole_row"])
def test_terminal_join_rejects_cross_producer_split_transplant(
    artifact_bundle,
    lane,
    mutation,
):
    comparator, original = artifact_bundle
    bundle = copy.deepcopy(original)
    core = bundle[f"{lane}_input1_core"]
    source, target = core["split_records"][:2]
    if mutation == "whole_row":
        core["split_records"][1] = copy.deepcopy(source)
        expected = "fixture operation|split index sequence"
    else:
        for field in (
            "pre_split_state_sha256",
            "shadow_pre_split_state_sha256",
            "full_singular_values",
            "kept_singular_values",
            "full_bond_dimension",
            "kept_bond_dimension",
            "discarded_squared_weight",
            "discarded_fraction",
            "spectrum_producer_binding_sha256",
        ):
            target[field] = copy.deepcopy(source[field])
        expected = "producer binding"
    _rehash(core, comparator)
    with pytest.raises(ValueError, match=expected):
        _build(comparator, bundle)


def test_terminal_join_rejects_gc_algorithm_epoch_corruption(
    artifact_bundle,
):
    comparator, original = artifact_bundle
    bundle = copy.deepcopy(original)
    core = bundle["gcapeps_input1_core"]
    row = next(
        item
        for item in core["instrumented_algorithm_ledger"]
        if "compression" in item
    )
    row["construction_epoch_before"] = 999
    row["compression"]["construction_epoch_before"] = 999
    _rehash(core, comparator)
    with pytest.raises(ValueError, match="epoch|route ledger"):
        _build(comparator, bundle)


@pytest.mark.parametrize(
    "mutation",
    ["candidate_restart", "memory_reset", "broken_chain", "terminal_hash"],
)
def test_terminal_join_rejects_round_restart_or_memory_reset(
    artifact_bundle,
    mutation,
):
    comparator, original = artifact_bundle
    bundle = copy.deepcopy(original)
    core = bundle["plain_input1_core"]
    row = core["round_continuity_ledger"][0]
    if mutation == "candidate_restart":
        row["candidate_restarted_between_rounds"] = True
    elif mutation == "memory_reset":
        row["memory_reset_between_rounds"] = True
    elif mutation == "broken_chain":
        row["round_start_state_sha256"] = "f" * 64
    else:
        row["round_end_state_sha256"] = "f" * 64
        core["no_shadow"]["round_continuity_ledger"][0][
            "round_end_state_sha256"
        ] = "f" * 64
    _rehash(core, comparator)
    with pytest.raises(ValueError, match="continuity|identity mismatch"):
        _build(comparator, bundle)


def test_terminal_join_rejects_projection_corruption_before_metrics(
    artifact_bundle,
):
    comparator, original = artifact_bundle
    bundle = copy.deepcopy(original)
    bundle["plain_input1_core"]["case_id"] = "corrupt-without-rehash"
    with pytest.raises(ValueError, match="projection hash mismatch"):
        _build(comparator, bundle)


def test_comparator_worker_emits_standard_two_frame_transport(artifact_bundle):
    comparator, bundle = artifact_bundle
    timing = _load_sibling(
        "gcapeps_finite_memory_timing.py",
        "_gcapeps_comparator_timing_owner",
    )
    result = comparator.run_comparator_worker(
        **bundle,
        timing_module=timing,
    )
    core_bytes, trailer_bytes = timing.decode_two_frames(
        result["framed_bytes"],
        core_max=len(result["core_bytes"]),
        trailer_max=len(result["trailer_bytes"]),
    )
    assert core_bytes == result["core_bytes"]
    assert trailer_bytes == result["trailer_bytes"]
    assert core_bytes == comparator.canonical_json_bytes(result["core"])
    assert result["core"]["schema"] == comparator.COMPARATOR_SCHEMA
    trailer = timing.json.loads(trailer_bytes.decode("ascii"))
    assert trailer["core_sha256"] == hashlib.sha256(core_bytes).hexdigest()
