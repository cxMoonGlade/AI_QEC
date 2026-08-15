"""Focused contracts for the neutral XZZX d=7 external-runtime fixture."""

from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
import stim


REPO = Path(__file__).resolve().parents[1]
EMITTER = (
    REPO
    / "scripts"
    / "external_baselines"
    / "emit_xzzx_d7_capability_fixture.py"
)
CUDA_WORKER = (
    REPO
    / "scripts"
    / "external_baselines"
    / "cudaq_xzzx_d7_capability_worker.py"
)
PECOS_WORKER = (
    REPO
    / "scripts"
    / "external_baselines"
    / "pecos_xzzx_d7_capability_worker.py"
)
LOCK_BUILDER = (
    REPO
    / "scripts"
    / "external_baselines"
    / "build_xzzx_capability_environment_locks.py"
)
CUDA_LOCK = REPO / "baseline-environment-cudaq-qec-linux-64.lock.json"
PECOS_LOCK = REPO / "baseline-environment-pecos-linux-64.lock.json"
EXPECTED = {
    2: {
        "shape": (97, 145, 96, 1),
        "detector_arities": {1: 24, 2: 48, 3: 6, 5: 18},
        "sha256": (
            "193d56d199b45016d91e8d5742f52fdc4e8e3b74d571891c78e28f7ec4eca6bd"
        ),
    },
    7: {
        "shape": (97, 385, 336, 1),
        "detector_arities": {1: 24, 2: 288, 3: 6, 5: 18},
        "sha256": (
            "20a32d1cd1293d4d4d6e74d8af04fe7b1300ddb82dbf734f558fb764ad27c4d7"
        ),
    },
}


def _load_script(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(
        name,
        path,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_emitter():
    return _load_script(
        EMITTER,
        "emit_xzzx_d7_capability_fixture_under_test",
    )


def _fixture(rounds: int):
    emitter = _load_emitter()
    circuit, frame = emitter.dense_xzzx_memory(
        stim,
        distance=7,
        rounds=rounds,
    )
    return emitter, circuit, emitter.neutral_fixture(circuit, frame, rounds=rounds)


def _fold(rows: list[list[int]], measurements: np.ndarray) -> np.ndarray:
    folded = np.zeros((measurements.shape[0], len(rows)), dtype=np.uint8)
    for column, row in enumerate(rows):
        folded[:, column] = np.bitwise_xor.reduce(
            measurements[:, row],
            axis=1,
        )
    return folded


def _copy_with_first_post_cx_h_removed(circuit: stim.Circuit) -> stim.Circuit:
    """Remove the first conjugating H following a selected-data CX."""

    instructions = list(circuit)
    changed_index = None
    changed_targets = None
    for index in range(1, len(instructions) - 1):
        instruction = instructions[index]
        if instruction.name != "CX" or len(instruction.targets_copy()) != 2:
            continue
        endpoints = {target.value for target in instruction.targets_copy()}
        previous = instructions[index - 1]
        following = instructions[index + 1]
        if previous.name != "H" or following.name != "H":
            continue
        previous_qubits = {target.value for target in previous.targets_copy()}
        following_targets = following.targets_copy()
        conjugated = endpoints & previous_qubits & {
            target.value for target in following_targets
        }
        if not conjugated:
            continue
        removed = next(iter(conjugated))
        changed_index = index + 1
        changed_targets = [
            target for target in following_targets if target.value != removed
        ]
        break

    assert changed_index is not None
    assert changed_targets is not None
    corrupted = stim.Circuit()
    for index, instruction in enumerate(instructions):
        targets = (
            changed_targets
            if index == changed_index
            else instruction.targets_copy()
        )
        if targets:
            corrupted.append(
                instruction.name,
                targets,
                instruction.gate_args_copy(),
            )
    return corrupted


def _copy_without_mid_circuit_resets(circuit: stim.Circuit) -> stim.Circuit:
    corrupted = stim.Circuit()
    for instruction in circuit:
        name = "M" if instruction.name == "MR" else instruction.name
        corrupted.append(
            name,
            instruction.targets_copy(),
            instruction.gate_args_copy(),
        )
    return corrupted


@pytest.mark.parametrize("rounds", [2, 7])
def test_fixture_fingerprint_shape_and_detector_arity_are_pinned(rounds: int) -> None:
    emitter, circuit, fixture = _fixture(rounds)
    expected = EXPECTED[rounds]

    assert fixture["schema"] == emitter.FIXTURE_SCHEMA
    assert (
        fixture["num_qubits"],
        fixture["num_measurements"],
        fixture["num_detectors"],
        fixture["num_observables"],
    ) == expected["shape"]
    assert fixture["stim_circuit_sha256"] == expected["sha256"]
    assert hashlib.sha256(str(circuit).encode("utf-8")).hexdigest() == expected[
        "sha256"
    ]
    assert Counter(map(len, fixture["detector_rows"])) == expected[
        "detector_arities"
    ]
    assert list(map(len, fixture["observable_rows"])) == [7]

    frame = fixture["frame"]
    assert frame["source_sparse_num_qubits"] == 118
    assert len(frame["active_sparse_qubit_ids"]) == 97
    assert len(frame["data_qubits"]) == 49
    assert len(frame["hadamard_frame_data_qubits"]) == 25
    assert sorted(frame["dense_qubit_map"].values()) == list(range(97))

    measurement_order = fixture["measurement_order"]
    assert [entry["column"] for entry in measurement_order] == list(
        range(expected["shape"][1])
    )
    assert sum(entry["reset"] for entry in measurement_order) == rounds * 48
    assert all(entry["reset"] for entry in measurement_order[: rounds * 48])
    assert not any(entry["reset"] for entry in measurement_order[rounds * 48 :])


@pytest.mark.parametrize("rounds", [2, 7])
def test_noiseless_raw_measurements_fold_to_zero_record(rounds: int) -> None:
    _emitter, circuit, fixture = _fixture(rounds)
    measurements = circuit.compile_sampler(seed=123).sample(shots=256)

    assert measurements.shape == (256, fixture["num_measurements"])
    assert np.any(measurements), "raw projected syndromes must not be assumed zero"
    detectors = _fold(fixture["detector_rows"], measurements)
    observables = _fold(fixture["observable_rows"], measurements)
    assert detectors.shape == (256, fixture["num_detectors"])
    assert observables.shape == (256, 1)
    assert not np.any(detectors)
    assert not np.any(observables)


def test_structural_reset_and_rec_offset_corruptions_break_noiseless_record() -> None:
    emitter, circuit, fixture = _fixture(rounds=2)

    missing_h = _copy_with_first_post_cx_h_removed(circuit)
    with pytest.raises(RuntimeError, match="fingerprint drift"):
        emitter.neutral_fixture(missing_h, fixture["frame"], rounds=2)
    missing_h_measurements = missing_h.compile_sampler(seed=3).sample(shots=256)
    assert np.any(_fold(fixture["detector_rows"], missing_h_measurements))

    missing_resets = _copy_without_mid_circuit_resets(circuit)
    missing_reset_measurements = missing_resets.compile_sampler(seed=3).sample(
        shots=256
    )
    assert np.any(_fold(fixture["detector_rows"], missing_reset_measurements))

    clean_measurements = circuit.compile_sampler(seed=3).sample(shots=256)
    corrupted_rows = [row.copy() for row in fixture["detector_rows"]]
    temporal_row = next(
        index for index, row in enumerate(corrupted_rows) if len(row) == 2
    )
    corrupted_rows[temporal_row] = corrupted_rows[temporal_row][:-1]
    assert np.any(_fold(corrupted_rows, clean_measurements))


def test_cuda_worker_rejects_unfrozen_sha_and_measurement_ledger_mutation(
    tmp_path: Path,
) -> None:
    cuda_worker = _load_script(
        CUDA_WORKER,
        "cudaq_xzzx_d7_capability_worker_under_test",
    )
    _emitter, _circuit, fixture = _fixture(rounds=2)
    fixture_path = tmp_path / "fixture.json"

    fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
    assert cuda_worker._read_fixture(fixture_path)["rounds"] == 2

    wrong_fingerprint = copy.deepcopy(fixture)
    wrong_fingerprint["stim_circuit_sha256"] = "0" * 64
    fixture_path.write_text(json.dumps(wrong_fingerprint), encoding="utf-8")
    with pytest.raises(ValueError, match="fingerprint"):
        cuda_worker._read_fixture(fixture_path)

    wrong_ledger = copy.deepcopy(fixture)
    wrong_ledger["measurement_order"][0]["basis"] = "Y"
    fixture_path.write_text(json.dumps(wrong_ledger), encoding="utf-8")
    with pytest.raises(ValueError, match="measurement order"):
        cuda_worker._read_fixture(fixture_path)


def test_zero_strength_non_pauli_controls_are_explicitly_inactive() -> None:
    cuda_worker = _load_script(
        CUDA_WORKER,
        "cudaq_xzzx_d7_zero_strength_under_test",
    )
    pecos_worker = _load_script(
        PECOS_WORKER,
        "pecos_xzzx_d7_zero_strength_under_test",
    )

    assert cuda_worker._is_non_pauli_active(0.0) is False
    assert cuda_worker._is_non_pauli_active(0.01) is True
    assert pecos_worker._is_non_pauli_active(0.0) is False
    assert pecos_worker._is_non_pauli_active(0.02) is True
    assert '"is_non_pauli_active"' in CUDA_WORKER.read_text(encoding="utf-8")
    assert '"is_non_pauli_active"' in PECOS_WORKER.read_text(encoding="utf-8")


def test_cuda_record_fold_keeps_explicit_measurement_string_order() -> None:
    cuda_worker = _load_script(
        CUDA_WORKER,
        "cudaq_xzzx_d7_record_order_under_test",
    )
    synthetic_fixture = {
        "num_measurements": 5,
        "detector_rows": [[0], [4], [0, 2, 4]],
        "observable_rows": [[0, 1, 3, 4]],
    }

    records = cuda_worker._counts_to_records(
        {"10110": 3},
        synthetic_fixture,
    )

    assert records == [
        {
            "frequency": 3,
            "raw_measurements": [1, 0, 1, 1, 0],
            "detector_bits": [1, 0, 0],
            "observable_bits": [0],
        }
    ]


def test_cuda_kraus_placement_is_once_per_complete_syndrome_round() -> None:
    cuda_worker = _load_script(
        CUDA_WORKER,
        "cudaq_xzzx_d7_noise_placement_under_test",
    )
    _emitter, _circuit, fixture = _fixture(rounds=2)

    class FakeKernel:
        def __init__(self) -> None:
            self.events: list[tuple[object, ...]] = []

        def qalloc(self, count: int) -> list[int]:
            return list(range(count))

        def reset(self, qubit: int) -> None:
            self.events.append(("reset", qubit))

        def h(self, qubit: int) -> None:
            self.events.append(("h", qubit))

        def cx(self, control: int, target: int) -> None:
            self.events.append(("cx", control, target))

        def mz(self, qubit: int) -> None:
            self.events.append(("mz", qubit))

        def apply_noise(self, channel: object, qubit: int) -> None:
            self.events.append(("apply_noise", qubit, channel))

    class FakeCudaq:
        class KrausOperator:
            def __init__(self, matrix: np.ndarray) -> None:
                self.matrix = matrix

        class KrausChannel:
            def __init__(self, operators: list[object]) -> None:
                self.operators = operators

        class NoiseModel:
            pass

        def __init__(self) -> None:
            self.kernel = FakeKernel()

        def make_kernel(self) -> FakeKernel:
            return self.kernel

    fake_cudaq = FakeCudaq()
    kernel, noise_model, applications = cuda_worker._build_kernel(
        fake_cudaq,
        fixture,
        0.01,
    )

    assert noise_model is not None
    assert applications == 2 * 49
    noise_indices = [
        index
        for index, event in enumerate(kernel.events)
        if event[0] == "apply_noise"
    ]
    assert len(noise_indices) == 98
    assert noise_indices == list(
        range(noise_indices[0], noise_indices[0] + 49)
    ) + list(range(noise_indices[49], noise_indices[49] + 49))
    for start in (noise_indices[0], noise_indices[49]):
        assert [event[1] for event in kernel.events[start : start + 49]] == fixture[
            "frame"
        ]["data_qubits"]
    assert sum(
        event[0] == "mz" for event in kernel.events[: noise_indices[0]]
    ) == 48
    assert sum(
        event[0] == "mz" for event in kernel.events[: noise_indices[49]]
    ) == 96


@pytest.mark.parametrize("rounds", [2, 7])
def test_pecos_native_round_semantics_disclose_initial_partial_layer(
    rounds: int,
) -> None:
    pecos_worker = _load_script(
        PECOS_WORKER,
        "pecos_xzzx_d7_round_semantics_under_test",
    )
    semantics = pecos_worker._native_round_semantics(rounds)

    assert semantics == {
        "pecos_complete_rounds": rounds,
        "initial_partial_measurement_count": 24,
        "complete_round_measurement_count": 48,
        "syndrome_measurement_layer_count": rounds + 1,
        "expected_num_measurements": 24 + rounds * 48 + 49,
        "expected_num_detectors": 24 + rounds * 48,
        "expected_non_pauli_layers": rounds,
    }
    source = PECOS_WORKER.read_text(encoding="utf-8")
    for field in semantics:
        assert f'"{field}"' in source


@pytest.mark.parametrize(
    ("worker_path", "module_name", "lock_path", "critical_versions"),
    [
        (
            CUDA_WORKER,
            "cudaq_xzzx_d7_environment_binding_under_test",
            CUDA_LOCK,
            {
                "cudaq": "0.14.2",
                "cuda-quantum-cu13": "0.14.2",
                "cudaq-qec": "0.6.0",
                "cudaq-qec-cu13": "0.6.0",
                "cutensornet-cu13": "2.12.2",
                "cupy-cuda13x": "13.6.0",
            },
        ),
        (
            PECOS_WORKER,
            "pecos_xzzx_d7_environment_binding_under_test",
            PECOS_LOCK,
            {
                "quantum-pecos": "0.9.0.dev2",
                "pecos-rslib": "0.9.0.dev2",
                "pytket-cutensornet": "0.12.1",
                "cutensornet-cu13": "2.13.0",
                "cupy-cuda13x": "14.1.1",
            },
        ),
    ],
)
def test_workers_bind_root_lock_and_fail_closed_on_runtime_versions(
    worker_path: Path,
    module_name: str,
    lock_path: Path,
    critical_versions: dict[str, str],
) -> None:
    worker = _load_script(worker_path, module_name)

    assert worker.ENVIRONMENT_LOCK == lock_path
    assert worker.EXPECTED_RUNTIME_DISTRIBUTIONS == critical_versions
    worker._validate_runtime_versions(critical_versions)

    wrong = dict(critical_versions)
    first = next(iter(wrong))
    wrong[first] = "0.invalid"
    with pytest.raises(RuntimeError, match=first):
        worker._validate_runtime_versions(wrong)

    missing = dict(critical_versions)
    missing.pop(first)
    with pytest.raises(RuntimeError, match=first):
        worker._validate_runtime_versions(missing)

    source = worker_path.read_text(encoding="utf-8")
    assert lock_path.name in source
    assert '"environment_lock"' in source
    if worker_path == PECOS_WORKER:
        assert "LD_LIBRARY_PATH" in source
        assert '"python_executable"' in source
        assert '"python_prefix"' in source


@pytest.mark.parametrize("lock_path", [CUDA_LOCK, PECOS_LOCK])
def test_environment_locks_claim_installed_state_only(lock_path: Path) -> None:
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    scope = lock["provenance_scope"]

    assert scope["installed_state_only"] is True
    assert scope["fully_reproducible"] is False
    assert scope["wheel_bytes_attested"] is False
    claim = lock["claim_boundary"].lower()
    assert "installed-state" in claim
    assert "not fully reproducible" in claim
    assert "does not attest wheel bytes" in claim
    for locked_url in lock["conda_explicit_sha256_urls"]:
        _url, separator, digest = locked_url.rpartition("#")
        assert separator == "#"
        assert len(digest) == 64
        int(digest, 16)

    builder_source = LOCK_BUILDER.read_text(encoding="utf-8")
    for field in (
        '"installed_state_only"',
        '"fully_reproducible"',
        '"wheel_bytes_attested"',
    ):
        assert field in builder_source
    assert '"--sha256"' in builder_source
    assert '"--md5"' not in builder_source
    assert "must be a released wheel" not in builder_source
