from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = ROOT / "scripts" / "external_baselines"
PLAIN_PATH = SCRIPT_ROOT / "plain_quimb_d357_worker.py"
GCAPEPS_PATH = SCRIPT_ROOT / "gcapeps_d357_worker.py"
FIXTURE_PATH = (
    SCRIPT_ROOT / "emit_gcapeps_d357_unitary_prefix_fixture.py"
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def plain():
    return _load("_plain_quimb_d357_worker_test", PLAIN_PATH)


@pytest.fixture(scope="module")
def gcapeps():
    return _load("_gcapeps_d357_worker_test", GCAPEPS_PATH)


@pytest.fixture(scope="module")
def fixture_contract():
    return _load("_gcapeps_d357_fixture_test_for_workers", FIXTURE_PATH)


@pytest.mark.parametrize("distance", (3, 5, 7))
def test_both_workers_accept_each_exact_frozen_fixture(
    plain,
    gcapeps,
    fixture_contract,
    distance: int,
) -> None:
    stim = pytest.importorskip("stim")
    _, fixture = fixture_contract.emit_fixture(stim, distance=distance)
    canonical = fixture_contract.canonical_json_bytes(fixture)
    expected = fixture_contract.canonical_json_sha256(fixture)

    plain_frozen, plain_digest = plain._validate_fixture(
        fixture,
        canonical,
        fixture_contract,
    )
    gc_frozen, gc_digest = gcapeps._validate_fixture(
        fixture,
        canonical,
        fixture_contract,
    )

    assert plain_digest == expected
    assert gc_digest == expected
    assert plain_frozen == fixture
    assert gc_frozen == fixture
    assert plain.EXPECTED_PEPS_SETTINGS == fixture["peps_settings"]
    assert gcapeps.EXPECTED_SETTINGS == fixture["peps_settings"]


def test_plain_source_scan_rejects_hybrid_import(plain) -> None:
    source = PLAIN_PATH.read_text(encoding="utf-8")
    assert plain.scan_plain_worker_source(source) == {
        "passed": True,
        "prohibited_imports": [],
    }
    damaged = source + "\nimport quimb.experimental.gcapeps\n"
    report = plain.scan_plain_worker_source(damaged)
    assert report["passed"] is False
    assert report["prohibited_imports"] == [
        "quimb.experimental.gcapeps"
    ]


@pytest.mark.parametrize(
    "call",
    (
        "state_vector",
        "to_dense",
        "norm",
        "apply_coherent_pauli_sum",
    ),
)
def test_gcapeps_source_scan_rejects_forbidden_calls(
    gcapeps,
    call: str,
) -> None:
    source = GCAPEPS_PATH.read_text(encoding="utf-8")
    assert gcapeps.scan_gcapeps_worker_source(source)["passed"] is True
    damaged = f"def injected(candidate):\n    return candidate.{call}()\n"
    report = gcapeps.scan_gcapeps_worker_source(damaged)
    assert report["passed"] is False
    assert report["prohibited_calls"] == [call]


def test_plain_gate_matrices_and_rotation_remain_c128(plain) -> None:
    h = plain._matrix(np, "H")
    cx = plain._matrix(np, "CX")
    ry = plain._local_ry(np, 0.137)

    assert h.shape == (2, 2)
    assert cx.shape == (4, 4)
    assert ry.shape == (2, 2)
    for matrix in (h, cx, ry):
        assert matrix.dtype == np.dtype("complex128")
        assert matrix.dtype.str == "<c16"
        assert matrix.flags.c_contiguous
        np.testing.assert_allclose(
            matrix.conj().T @ matrix,
            np.eye(matrix.shape[0], dtype=np.complex128),
            atol=8 * np.finfo(np.float64).eps,
            rtol=0.0,
        )


def test_worker_cli_is_the_frozen_three_path_interface(
    plain,
    gcapeps,
) -> None:
    argv = [
        "--fixture",
        "/tmp/fixture.json",
        "--fork-checkout",
        "/tmp/quimb",
        "--output",
        "/tmp/result.json",
        "--cell-id",
        "d3-stress-corner",
    ]
    for worker in (plain, gcapeps):
        parsed = worker._parse_args(argv)
        assert parsed.fixture == Path("/tmp/fixture.json")
        assert parsed.fork_checkout == Path("/tmp/quimb")
        assert parsed.output == Path("/tmp/result.json")
        assert parsed.cell_id == "d3-stress-corner"


@pytest.mark.parametrize("worker_name", ("plain", "gcapeps"))
def test_atomic_publication_is_no_replace(
    request: pytest.FixtureRequest,
    tmp_path: Path,
    worker_name: str,
) -> None:
    worker = request.getfixturevalue(worker_name)
    tmp_path.chmod(0o700)
    output = tmp_path / f"{worker_name}.json"
    payload = b'{"status":"completed"}\n'

    digest = worker._atomic_publish_noreplace(output, payload)
    assert digest == hashlib.sha256(payload).hexdigest()
    assert output.read_bytes() == payload
    assert not list(tmp_path.glob(".*.stage-*"))
    with pytest.raises(FileExistsError):
        worker._atomic_publish_noreplace(output, payload)


def test_gcapeps_resource_caps_are_exact_per_distance(
    fixture_contract,
) -> None:
    stim = pytest.importorskip("stim")
    for distance, n_qubits in ((3, 17), (5, 49), (7, 97)):
        _, fixture = fixture_contract.emit_fixture(stim, distance=distance)
        assert fixture["gcapeps_multi_resource_limits"] == {
            "max_local_operator_elements": 64,
            "max_total_operator_elements": 64 * n_qubits,
            "max_local_candidate_tensor_elements": 4_194_304,
            "max_total_candidate_tensor_elements": 16_777_216,
            "max_predicted_bond_dimension": 64,
            "max_routed_rank_product": 64,
            "max_total_bond_growth_product": 64,
            "expected_refactor_factor_product": 1,
        }


def test_worker_sources_bind_required_native_batches() -> None:
    plain_source = PLAIN_PATH.read_text(encoding="utf-8")
    gc_source = GCAPEPS_PATH.read_text(encoding="utf-8")

    assert "circuit.apply_gates(raw_prefix_tuple)" in plain_source
    assert "circuit.apply_gates((raw_rotations[target],))" in plain_source
    assert "state.apply_clifford(prefix_circuit)" in gc_source
    assert "state.apply_pauli_rotation(" in gc_source
    assert "psi0=None" in plain_source
    assert "psi0=None" in gc_source



def _resource_snapshot(n_qubits: int, edge_count: int) -> dict[str, object]:
    return {
        "tensor_count": n_qubits,
        "edge_count": edge_count,
        "maximum_bond_dimension": 1,
        "bond_dimensions": [1] * edge_count,
        "total_tensor_elements": 2 * n_qubits,
        "maximum_site_tensor_elements": 2,
        "logical_tensor_bytes": 32 * n_qubits,
        "gauge_elements": 0,
        "logical_gauge_bytes": 0,
        "dtype": "complex128",
        "epistemic_class": "numerical_only_representation_resource",
    }


class _FakeGate:
    def __init__(self, qubits) -> None:
        self.qubits = tuple(qubits)

    @classmethod
    def from_raw(cls, _matrix, *, qubits):
        return cls(qubits)


class _FakePlainCircuit:
    instances: list["_FakePlainCircuit"] = []

    def __init__(self, *args, **kwargs) -> None:
        del args, kwargs
        self.num_gates = 0
        self.calls: list[tuple[_FakeGate, ...]] = []
        self.__class__.instances.append(self)

    def apply_gates(self, gates) -> None:
        batch = tuple(gates)
        self.calls.append(batch)
        self.num_gates += len(batch)


@dataclass
class _FakeRoutingEvent:
    column: int
    round_index: int
    operation: str
    frame_backend: str
    residual_backend: str
    frame_revision_before: int
    frame_revision_after: int
    physical_pauli: str | None
    pulled_back_pauli: str | None
    peps_gate_count_before: int
    peps_gate_count_after: int
    max_bond_before: int
    max_bond_after: int
    residual_update: object | None
    residual_revision_before: int
    residual_revision_after: int
    physical_terms: tuple[str, ...]
    pulled_back_terms: tuple[str, ...]


@dataclass
class _FakeResidualUpdate:
    support: tuple[int, ...]


class _FakeWord:
    def __init__(self, labels: str) -> None:
        self.labels = labels
        self.target = labels.index("Y")

    @classmethod
    def from_labels(cls, labels: str, *, phase: float):
        assert phase == 1.0
        return cls(labels)

    def __str__(self) -> str:
        return "+" + self.labels


def _install_fake_gcapeps_runtime(
    monkeypatch: pytest.MonkeyPatch,
    worker,
    fixture: dict,
    *,
    fail_attempt: int | None,
):
    stim = pytest.importorskip("stim")
    tracker = SimpleNamespace(
        circuit_count=0,
        state_count=0,
        prefix_calls=0,
        rotation_attempts=0,
        rotation_targets=[],
        validated_supports=[],
        tight_checks=[],
        state=None,
    )
    schedule = {
        (int(row["layer"]), int(row["location_rank"])): row
        for row in fixture["accumulated_frame_schedule"]["rows"]
    }
    rank_by_target = {
        int(row["target"]): int(row["location_rank"])
        for row in fixture["error_locations"]
    }

    class FakeResourceError(ValueError):
        def __init__(self) -> None:
            self.stage = "candidate_preflight"
            self.metric = "max_routed_rank_product"
            self.predicted = 128
            self.limit = 64
            super().__init__("fake guard: 128 > 64")

    class FakeFrame:
        def __init__(self, num_qubits: int) -> None:
            self.num_qubits = num_qubits
            self.revision = 0
            self.backend_name = "fake-stim-frame"

    class FakeCircuit:
        def __init__(self, *args, **kwargs) -> None:
            del args, kwargs
            tracker.circuit_count += 1

    class FakeLimits:
        def __init__(self, **kwargs) -> None:
            self.values = kwargs

    class FakeCarrier:
        def __init__(self, circuit, **kwargs) -> None:
            self.circuit = circuit
            self.kwargs = kwargs

    class FakeState:
        def __init__(self, frame, carrier) -> None:
            del carrier
            tracker.state_count += 1
            tracker.state = self
            self._frame = frame
            self._events: list[_FakeRoutingEvent] = []
            self.residual_revision = 0
            self.native_gate_count = 0
            self.max_bond = 1

        @property
        def events(self):
            return tuple(self._events)

        @property
        def frame(self):
            return self._frame

        def apply_clifford(self, _circuit):
            tracker.prefix_calls += 1
            before = self._frame.revision
            self._frame.revision += 1
            event = _FakeRoutingEvent(
                column=len(self._events),
                round_index=0,
                operation="clifford_frame_update",
                frame_backend=self._frame.backend_name,
                residual_backend="fake-carrier",
                frame_revision_before=before,
                frame_revision_after=self._frame.revision,
                physical_pauli=None,
                pulled_back_pauli=None,
                peps_gate_count_before=self.native_gate_count,
                peps_gate_count_after=self.native_gate_count,
                max_bond_before=self.max_bond,
                max_bond_after=self.max_bond,
                residual_update=None,
                residual_revision_before=self.residual_revision,
                residual_revision_after=self.residual_revision,
                physical_terms=(),
                pulled_back_terms=(),
            )
            self._events.append(event)
            return event

        def apply_pauli_rotation(self, word, _angle):
            tracker.rotation_attempts += 1
            tracker.rotation_targets.append(word.target)
            if fail_attempt == tracker.rotation_attempts:
                raise FakeResourceError()
            location_rank = rank_by_target[word.target]
            row = schedule[(self._frame.revision, location_rank)]
            support = tuple(int(q) for q in row["support"])
            increment = 1 if len(support) == 1 else 0
            update = _FakeResidualUpdate(support=support)
            event = _FakeRoutingEvent(
                column=len(self._events),
                round_index=0,
                operation="pulled_pauli_rotation",
                frame_backend=self._frame.backend_name,
                residual_backend="fake-carrier",
                frame_revision_before=self._frame.revision,
                frame_revision_after=self._frame.revision,
                physical_pauli=str(word),
                pulled_back_pauli=str(row["signed_pullback"]).replace("_", "I"),
                peps_gate_count_before=self.native_gate_count,
                peps_gate_count_after=self.native_gate_count + increment,
                max_bond_before=self.max_bond,
                max_bond_after=self.max_bond,
                residual_update=update,
                residual_revision_before=self.residual_revision,
                residual_revision_after=self.residual_revision + 1,
                physical_terms=(str(word),),
                pulled_back_terms=(str(row["signed_pullback"]),),
            )
            self.native_gate_count += increment
            self.residual_revision += 1
            self._events.append(event)
            return event

    fake_qtn = SimpleNamespace(CircuitPEPSSimpleUpdate=FakeCircuit)
    fake_gcapeps = SimpleNamespace(
        GCAPEPSResourceLimits=FakeLimits,
        QuimbPEPSCarrier=FakeCarrier,
        GCAPEPSState=FakeState,
        StimCliffordFrame=FakeFrame,
        QubitPauliWord=_FakeWord,
        PEPOResourceError=FakeResourceError,
    )
    monkeypatch.setattr(
        worker,
        "_runtime_imports",
        lambda _checkout: (np, fake_qtn, stim, fake_gcapeps, {"fake": True}),
    )

    def fake_validate(
        update,
        *,
        fixture,
        schedule_row,
        expected_limits,
        previous_representation,
        expected_revision_before,
        require_tight_first_ledger,
    ):
        del fixture, expected_limits, expected_revision_before
        assert update.support == tuple(schedule_row["support"])
        tracker.validated_supports.append(tuple(schedule_row["support"]))
        tracker.tight_checks.append(require_tight_first_ledger)
        return dict(previous_representation), {
            "stub_update": True,
            "tight_first_update_ledger_checked": require_tight_first_ledger,
        }

    monkeypatch.setattr(worker, "_validate_rotation_update", fake_validate)
    return tracker


def test_plain_executes_registered_l3_k4_on_one_persistent_circuit(
    monkeypatch: pytest.MonkeyPatch,
    plain,
    fixture_contract,
) -> None:
    stim = pytest.importorskip("stim")
    _, fixture = fixture_contract.emit_fixture(stim, distance=3)
    cell = plain._select_cell(fixture, "d3-stress-corner")
    _FakePlainCircuit.instances.clear()
    fake_qtn = SimpleNamespace(
        CircuitPEPSSimpleUpdate=_FakePlainCircuit,
        Gate=_FakeGate,
    )
    monkeypatch.setattr(
        plain,
        "_runtime_imports",
        lambda _checkout: (np, fake_qtn, {"fake": True}),
    )
    monkeypatch.setattr(
        plain,
        "_representation_snapshot",
        lambda _circuit, *, np, n_qubits, edges: _resource_snapshot(
            n_qubits,
            len(edges),
        ),
    )

    result = plain.compute_plain_candidate(
        fixture,
        cell=cell,
        fixture_sha256=fixture_contract.canonical_json_sha256(fixture),
        fork_checkout=Path("/fake/quimb"),
    )

    assert len(_FakePlainCircuit.instances) == 1
    circuit = _FakePlainCircuit.instances[0]
    assert [len(batch) for batch in circuit.calls] == [61, 1, 1, 1, 1] * 3
    rotation_targets = [
        batch[0].qubits[0] for batch in circuit.calls if len(batch) == 1
    ]
    assert rotation_targets == cell["selected_targets"] * 3
    assert result["progress"] == {
        "persistent_state_instances": 1,
        "prefix_batches_completed": 3,
        "completed_layers": 3,
        "completed_rotations": 12,
        "attempted_rotations": 12,
        "expected_layers": 3,
        "expected_rotations": 12,
    }


def test_gcapeps_executes_registered_l3_k4_with_live_frame_and_weight_one(
    monkeypatch: pytest.MonkeyPatch,
    gcapeps,
    fixture_contract,
) -> None:
    stim = pytest.importorskip("stim")
    _, fixture = fixture_contract.emit_fixture(stim, distance=3)
    cell = gcapeps._select_cell(fixture, "d3-stress-corner")
    tracker = _install_fake_gcapeps_runtime(
        monkeypatch,
        gcapeps,
        fixture,
        fail_attempt=None,
    )

    result = gcapeps.compute_gcapeps_candidate(
        fixture,
        cell=cell,
        fixture_sha256=fixture_contract.canonical_json_sha256(fixture),
        fork_checkout=Path("/fake/quimb"),
    )

    assert result["status"] == "completed"
    assert tracker.circuit_count == 1
    assert tracker.state_count == 1
    assert tracker.prefix_calls == 3
    assert tracker.rotation_attempts == 12
    assert tracker.rotation_targets == cell["selected_targets"] * 3
    assert any(len(support) == 1 for support in tracker.validated_supports)
    assert tracker.tight_checks == [True] + [False] * 11
    assert result["progress"]["completed_layers"] == 3
    assert result["progress"]["completed_rotations"] == 12
    assert result["progress"]["residual_native_gate_count"] == sum(
        len(support) == 1 for support in tracker.validated_supports
    )


def test_gcapeps_resource_guard_returns_serializable_partial_ledger(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    gcapeps,
    fixture_contract,
) -> None:
    stim = pytest.importorskip("stim")
    _, fixture = fixture_contract.emit_fixture(stim, distance=3)
    cell = gcapeps._select_cell(fixture, "d3-stress-corner")
    tracker = _install_fake_gcapeps_runtime(
        monkeypatch,
        gcapeps,
        fixture,
        fail_attempt=3,
    )

    result = gcapeps.compute_gcapeps_candidate(
        fixture,
        cell=cell,
        fixture_sha256=fixture_contract.canonical_json_sha256(fixture),
        fork_checkout=Path("/fake/quimb"),
    )

    assert result["status"] == "resource_guard_censored"
    assert result["censor"]["classification"] == "RESOURCE_GUARD_CENSORED"
    assert result["censor"]["failed_routing_event_not_committed"] is True
    assert result["progress"]["prefix_batches_completed"] == 1
    assert result["progress"]["completed_layers"] == 0
    assert result["progress"]["completed_rotations"] == 2
    assert result["progress"]["attempted_rotations"] == 3
    assert len(result["construction"]["updates"]) == 2
    assert len(tracker.state.events) == 3
    encoded = (json.dumps(result, allow_nan=False, sort_keys=True) + "\n").encode()
    tmp_path.chmod(0o700)
    output = tmp_path / "censored.json"
    gcapeps._atomic_publish_noreplace(output, encoded)
    assert json.loads(output.read_text())["status"] == "resource_guard_censored"


def test_one_site_update_validation_preserves_resource_shape(gcapeps) -> None:
    previous = _resource_snapshot(17, 24)
    update = SimpleNamespace(
        operation="pauli_rotation",
        strategy="one_site_coherent_dense",
        support=(6,),
        dependence_set=(6,),
        max_bond_before=1,
        max_bond_after=1,
        max_bond_limit=None,
        cutoff=1e-12,
        residual_revision_before=5,
        residual_revision_after=6,
        declared_term_count=2,
        active_term_count=2,
        truncation_applied=False,
        compression_applied=False,
        smudging_applied=False,
        approximate_contraction_applied=False,
        nonzero_validation="unitary_pauli_rotation",
        candidate_norm_squared=None,
        routing_root=None,
        routing_vertices=(),
        routing_tree_edges=(),
        edge_bonds=(),
        resource_ledger=None,
        dense_operator_action=None,
    )
    limits = {
        "max_local_operator_elements": 64,
        "max_total_operator_elements": 64 * 17,
        "max_local_candidate_tensor_elements": 4_194_304,
        "max_total_candidate_tensor_elements": 16_777_216,
        "max_predicted_bond_dimension": 64,
        "max_routed_rank_product": 64,
        "max_total_bond_growth_product": 64,
    }
    representation, evidence = gcapeps._validate_rotation_update(
        update,
        fixture={"n_qubits": 17},
        schedule_row={"support": [6]},
        expected_limits=limits,
        previous_representation=previous,
        expected_revision_before=5,
        require_tight_first_ledger=False,
    )
    assert representation == previous
    assert evidence["one_site_shape_and_bond_unchanged"] is True
    assert evidence["construction_resource_ledger"] is None
