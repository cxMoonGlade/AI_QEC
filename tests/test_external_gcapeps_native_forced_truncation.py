"""Non-formal contracts for the GCAPEPS bridge truncation supervisor.

Every numerical fixture in this file is the preregistration-excluded API
pilot or a synthetic ledger. This test module must never execute the held-out
formal target.
"""

from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest


REPO = Path(__file__).resolve().parents[1]
RUNNER_PATH = (
    REPO / "scripts" / "external_baselines" / "run_gcapeps_native_forced_truncation.py"
)
ANCHOR_PATH = (
    REPO
    / "scripts"
    / "external_baselines"
    / "gcapeps_forced_truncation_dense_anchor.py"
)
PILOT_A = 4.0 / 5.0
PILOT_B = 3.0 / 5.0
PILOT_THETA = np.pi / 3.0


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


runner = _load(RUNNER_PATH, "_gcapeps_forced_truncation_runner_test")
anchor = _load(ANCHOR_PATH, "_gcapeps_forced_truncation_anchor_test")


def _pilot_anchor():
    return anchor.build_anchor_payload(
        a=PILOT_A,
        b=PILOT_B,
        theta=PILOT_THETA,
    )


def _pilot_cap_row(*, cause: str = "max_bond"):
    max_bond = 1 if cause == "max_bond" else None
    cutoff = 0.0 if cause == "max_bond" else 0.8
    return SimpleNamespace(
        step_index=0,
        gate_role="parity_compute_cnot",
        edge=(0, 1),
        ordered_sites=(0, 1),
        configured_max_bond=max_bond,
        configured_cutoff=cutoff,
        configured_cutoff_mode="rel",
        full_singular_values=(PILOT_A, PILOT_B),
        kept_singular_values=(PILOT_A,),
        full_bond_dimension=2,
        kept_bond_dimension=1,
        pre_split_weight=1.0,
        discarded_squared_weight=PILOT_B**2,
        discarded_fraction=PILOT_B**2,
        keep_by_cutoff=2 if cause == "max_bond" else 1,
        keep_by_cap=1 if cause == "max_bond" else 2,
        actual_keep=1,
        cause=cause,
        dimension_reduced=True,
        positive_discarded_weight=True,
        positive_discarded_weight_threshold=1.0e-12,
        not_a_global_error_bound=True,
    )


def _pilot_no_loss_row():
    return SimpleNamespace(
        step_index=2,
        gate_role="parity_uncompute_cnot",
        edge=(0, 1),
        ordered_sites=(0, 1),
        configured_max_bond=1,
        configured_cutoff=0.0,
        configured_cutoff_mode="rel",
        full_singular_values=(1.0,),
        kept_singular_values=(1.0,),
        full_bond_dimension=1,
        kept_bond_dimension=1,
        pre_split_weight=1.0,
        discarded_squared_weight=0.0,
        discarded_fraction=0.0,
        keep_by_cutoff=1,
        keep_by_cap=1,
        actual_keep=1,
        cause="none",
        dimension_reduced=False,
        positive_discarded_weight=False,
        positive_discarded_weight_threshold=1.0e-12,
        not_a_global_error_bound=True,
    )


def _pilot_ledger(rows, *, plan_digest="c" * 64):
    if not isinstance(rows, tuple):
        rows = (rows,)
    return SimpleNamespace(
        compiler_revision="gcapeps_native_pauli_rotation.v1",
        plan_digest_sha256=plan_digest,
        plan_step_count=3,
        two_site_step_count=len(rows),
        split_records=rows,
        positive_discarded_event_count=sum(
            row.positive_discarded_weight for row in rows
        ),
        dimension_reduction_event_count=sum(
            row.dimension_reduced for row in rows
        ),
        total_discarded_squared_weight_diagnostic_only=sum(
            row.discarded_squared_weight for row in rows
        ),
        any_smudging_applied=False,
        not_a_global_error_bound=True,
    )


def test_test_source_cannot_execute_the_formal_target() -> None:
    """AST guard: all anchor builds are explicit pilots; no target entry runs."""

    tree = ast.parse(
        Path(__file__).read_text(encoding="utf-8"),
        filename=__file__,
    )
    forbidden_calls = {
        "build_formal_report",
        "run_formal_experiment",
        "main",
    }
    observed_forbidden = []
    anchor_calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            called = node.func.id
        elif isinstance(node.func, ast.Attribute):
            called = node.func.attr
        else:
            called = None
        if called in forbidden_calls:
            observed_forbidden.append(called)
        if called == "build_anchor_payload":
            anchor_calls.append({keyword.arg for keyword in node.keywords})
    assert observed_forbidden == []
    assert anchor_calls
    assert all({"a", "b", "theta"} <= keywords for keywords in anchor_calls)


def test_runner_and_anchor_do_not_statically_import_quimb() -> None:
    result = runner.scan_anchor_imports(ANCHOR_PATH)
    assert result["passed"] is True
    assert result["forbidden_imports"] == []

    runner_tree = ast.parse(
        RUNNER_PATH.read_text(encoding="utf-8"),
        filename=str(RUNNER_PATH),
    )
    static_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(runner_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    static_roots.update(
        node.module.split(".", 1)[0]
        for node in ast.walk(runner_tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )
    assert "quimb" not in static_roots


def test_pilot_complete_vector_metrics_are_standard_and_untransformed() -> None:
    payload = _pilot_anchor()
    exact = anchor.decode_complex_array(payload["arrays"]["exact_vector"])
    capped = anchor.decode_complex_array(payload["arrays"]["cap_only_lossy_vector"])
    metrics = anchor.evaluate_metrics(exact, capped)

    assert runner._validate_metric_payload(metrics) is True
    assert runner._metrics_match(
        metrics,
        payload["exact_predictions"]["cap_only"],
    )
    assert metrics["d_2"] == pytest.approx(PILOT_B, abs=1.0e-12)
    assert metrics["d_inf"] == pytest.approx(PILOT_B, abs=1.0e-12)
    assert metrics["fidelity"] == pytest.approx(PILOT_A**2, abs=1.0e-12)
    assert metrics["phase_fit_performed"] is False
    assert metrics["normalization_performed"] is False
    assert metrics["dtype_cast_performed"] is False


@pytest.mark.parametrize("cause", ("max_bond", "cutoff"))
def test_pilot_split_serializer_recomputes_distinct_causes(cause) -> None:
    row = runner.serialize_split_record(_pilot_cap_row(cause=cause))

    assert runner.validate_serialized_split_record(row) is True
    assert row["cause"] == cause
    assert row["positive_discarded_weight"] is True
    assert row["discarded_squared_weight"] == pytest.approx(
        PILOT_B**2,
        abs=1.0e-12,
    )
    if cause == "max_bond":
        assert row["configured_max_bond"] == 1
        assert row["configured_cutoff"] == 0.0
    else:
        assert row["configured_max_bond"] is None
        assert row["configured_cutoff"] == 0.8


def test_no_positive_loss_allows_later_structural_zero_cutoff_cause() -> None:
    structural = SimpleNamespace(
        step_index=2,
        gate_role="pilot_second_cnot",
        edge=(0, 1),
        ordered_sites=(0, 1),
        configured_max_bond=None,
        configured_cutoff=0.4,
        configured_cutoff_mode="rel",
        full_singular_values=(1.0, 0.0),
        kept_singular_values=(1.0,),
        full_bond_dimension=2,
        kept_bond_dimension=1,
        pre_split_weight=1.0,
        discarded_squared_weight=0.0,
        discarded_fraction=0.0,
        keep_by_cutoff=1,
        keep_by_cap=2,
        actual_keep=1,
        cause="cutoff",
        dimension_reduced=True,
        positive_discarded_weight=False,
        positive_discarded_weight_threshold=1.0e-12,
        not_a_global_error_bound=True,
    )
    ledger = SimpleNamespace(
        compiler_revision="gcapeps_native_pauli_rotation.v1",
        plan_digest_sha256="c" * 64,
        plan_step_count=3,
        two_site_step_count=1,
        split_records=(structural,),
        positive_discarded_event_count=0,
        dimension_reduction_event_count=1,
        total_discarded_squared_weight_diagnostic_only=0.0,
        any_smudging_applied=False,
        not_a_global_error_bound=True,
    )
    serialized = runner.serialize_native_ledger(ledger)

    assert runner._validate_expected_cause(
        serialized,
        expected_cause=None,
        expected_positive=False,
    )
    assert serialized["split_records"][0]["cause"] == "cutoff"
    assert serialized["split_records"][0]["positive_discarded_weight"] is False


def test_pilot_ledger_serializer_rejects_cause_and_spectrum_corruption() -> None:
    serialized = runner.serialize_native_ledger(_pilot_ledger(_pilot_cap_row()))
    assert runner.validate_serialized_ledger(serialized) is True

    wrong_cause = json.loads(json.dumps(serialized))
    wrong_cause["split_records"][0]["cause"] = "cutoff"
    with pytest.raises(ValueError, match="cause"):
        runner.validate_serialized_ledger(wrong_cause)

    wrong_spectrum = json.loads(json.dumps(serialized))
    wrong_spectrum["split_records"][0]["full_singular_values"][1] *= 0.9
    with pytest.raises(ValueError, match="inconsistent"):
        runner.validate_serialized_ledger(wrong_spectrum)


def test_native_plan_serialization_is_explicit_and_canonical() -> None:
    steps = (
        SimpleNamespace(
            step_index=0,
            role="parity_compute_cnot",
            gate_kind="CX",
            qubits=(0, 1),
            sites=(0, 1),
            angle_radians=None,
            matrix_sha256="a" * 64,
            is_two_site=True,
        ),
        SimpleNamespace(
            step_index=1,
            role="root_rotation",
            gate_kind="RZ",
            qubits=(1,),
            sites=(1,),
            angle_radians=float(PILOT_THETA),
            matrix_sha256="b" * 64,
            is_two_site=False,
        ),
        SimpleNamespace(
            step_index=2,
            role="parity_uncompute_cnot",
            gate_kind="CX",
            qubits=(0, 1),
            sites=(0, 1),
            angle_radians=None,
            matrix_sha256="a" * 64,
            is_two_site=True,
        ),
    )
    word = SimpleNamespace(
        num_qubits=2,
        codes=(3, 3),
        is_hermitian=True,
    )
    plan = SimpleNamespace(
        compiler_revision="gcapeps_native_pauli_rotation.v1",
        pauli_word=word,
        pauli_phase=1.0 + 0.0j,
        site_order=(0, 1),
        graph_edges=((0, 1),),
        angle_radians=float(PILOT_THETA),
        signed_angle_radians=float(PILOT_THETA),
        support=(0, 1),
        support_sites=(0, 1),
        routing_root=1,
        routing_vertices=(0, 1),
        routing_tree_edges=((0, 1),),
        steps=steps,
        canonical_transcript="pending",
        plan_digest_sha256="0" * 64,
        precision_dtype="complex128",
    )
    transcript = runner._rebuild_native_plan_transcript(plan)
    plan.canonical_transcript = transcript
    plan.plan_digest_sha256 = runner.hashlib.sha256(
        transcript.encode("utf-8")
    ).hexdigest()
    plan_digest = plan.plan_digest_sha256

    serialized = runner.serialize_native_plan(plan)
    canonical = runner._canonical_json_bytes(serialized)

    assert serialized["precision_dtype"] == "complex128"
    assert [step["gate_kind"] for step in serialized["steps"]] == [
        "CX",
        "RZ",
        "CX",
    ]
    assert json.loads(canonical) == serialized
    assert serialized["site_order"] == [0, 1]
    assert serialized["graph_edges"] == [[0, 1]]
    assert serialized["canonical_transcript"] == transcript
    assert serialized["plan_digest_sha256"] == plan_digest

    matching_ledger = _pilot_ledger(
        (_pilot_cap_row(), _pilot_no_loss_row()),
        plan_digest=plan_digest,
    )
    result = SimpleNamespace(
        circuit=SimpleNamespace(num_gates=3),
        plan=plan,
        ledger=matching_ledger,
        plan_digest_sha256=plan_digest,
    )
    result_payload = runner.serialize_native_execution_result(result)
    assert result_payload["plan_digest_sha256"] == plan_digest
    assert runner.validate_native_plan_ledger_binding(
        result_payload["plan"],
        result_payload["ledger"],
    )
    assert result_payload["circuit"]["tensor_elements_serialized"] is False

    wrong_result = SimpleNamespace(
        circuit=result.circuit,
        plan=plan,
        ledger=result.ledger,
        plan_digest_sha256="d" * 64,
    )
    with pytest.raises(ValueError, match="digests disagree"):
        runner.serialize_native_execution_result(wrong_result)

    forged_transcript = SimpleNamespace(**vars(plan))
    forged_transcript.canonical_transcript = json.dumps(
        {"schema": "forged.native_plan.v1"},
        sort_keys=True,
        separators=(",", ":"),
    )
    forged_transcript.plan_digest_sha256 = runner.hashlib.sha256(
        forged_transcript.canonical_transcript.encode("utf-8")
    ).hexdigest()
    with pytest.raises(ValueError, match="disagrees with plan fields"):
        runner.serialize_native_plan(forged_transcript)

    two_step_plan = json.loads(json.dumps(result_payload["plan"]))
    two_step_plan["steps"] = two_step_plan["steps"][:2]
    with pytest.raises(ValueError, match="plan_step_count"):
        runner.validate_native_plan_ledger_binding(
            two_step_plan,
            result_payload["ledger"],
        )

    corruptions = (
        ("compiler_revision", None, "forged.revision", "revisions"),
        ("plan_step_count", None, 2, "plan_step_count"),
        ("two_site_step_count", None, 1, "two-site count"),
        ("step_index", 0, 1, "step_index"),
        ("gate_role", 0, "wrong_role", "gate_role"),
        ("ordered_sites", 0, [1, 0], "ordered_sites"),
    )
    for field, row_index, value, match in corruptions:
        corrupted = json.loads(json.dumps(result_payload["ledger"]))
        if row_index is None:
            corrupted[field] = value
        else:
            corrupted["split_records"][row_index][field] = value
        with pytest.raises(ValueError, match=match):
            runner.validate_native_plan_ledger_binding(
                result_payload["plan"],
                corrupted,
            )


def test_output_requires_fresh_absolute_tmp_path_and_is_atomic(tmp_path) -> None:
    target = tmp_path / "pilot.json"
    payload = {
        "schema": "pilot.synthetic.v1",
        "formal_target_executed": False,
    }
    runner._atomic_write_new(target, payload)

    raw = target.read_bytes()
    assert raw == runner._canonical_json_bytes(payload)
    with pytest.raises(FileExistsError):
        runner._atomic_write_new(target, payload)
    with pytest.raises(ValueError, match="absolute"):
        runner._validate_output_path(Path("relative.json"))


def test_atomic_publish_preserves_a_concurrent_target(
    tmp_path,
    monkeypatch,
) -> None:
    target = tmp_path / "race.json"
    concurrent_bytes = b"concurrent-owner"

    def collide(_stage, destination):
        Path(destination).write_bytes(concurrent_bytes)
        raise FileExistsError("simulated concurrent publication")

    monkeypatch.setattr(runner.os, "link", collide)
    with pytest.raises(FileExistsError, match="concurrent"):
        runner._atomic_write_new(
            target,
            {"schema": "pilot.synthetic.race.v1"},
        )

    assert target.read_bytes() == concurrent_bytes
    assert list(tmp_path.glob("*.stage")) == []
    assert list(tmp_path.glob(".*.stage")) == []


def test_ignored_runtime_inventory_is_recorded_but_not_called_dirt(
    tmp_path,
    monkeypatch,
) -> None:
    commit = "1" * 40
    tree = "2" * 40

    def fake_git_scalar(repo, *arguments):
        if arguments == ("rev-parse", "--show-toplevel"):
            return str(repo)
        if arguments == ("rev-parse", "--verify", "HEAD^{commit}"):
            return commit
        if arguments == ("rev-parse", "--verify", "HEAD^{tree}"):
            return tree
        raise AssertionError(arguments)

    ignored_lines = [
        *(f"!! .pixi/cache-{index}" for index in range(15)),
        *(f"!! .pytest_cache/item-{index}" for index in range(7)),
    ]

    def fake_git_status(_repo, *, include_ignored):
        return "\n".join(ignored_lines) + "\n" if include_ignored else ""

    monkeypatch.setattr(runner, "_git_scalar", fake_git_scalar)
    monkeypatch.setattr(runner, "_git_status", fake_git_status)

    result = runner._validate_repo(
        tmp_path,
        expected_commit=commit,
        expected_tree=tree,
        include_ignored=True,
        label="pilot fork",
    )

    assert result["clean"] is True
    assert result["ignored_inventory_recorded"] is True
    assert result["ignored_entry_count"] == 22
    assert len(result["ignored_status_sha256"]) == 64
    summary = result["ignored_inventory_summary"]
    assert summary["entry_count"] == 22
    assert summary["counts_by_first_path_component"] == {
        ".pixi": 15,
        ".pytest_cache": 7,
    }
    assert len(summary["first_entries"]) == 10
    assert len(summary["last_entries"]) == 10
    assert summary["first_entries"][0] == ".pixi/cache-0"
    assert summary["last_entries"][-1] == ".pytest_cache/item-6"
    assert summary["full_entry_list_emitted"] is False
    assert "ignored_entries" not in result
    assert "ignored_inclusive_clean" not in result


def test_post_execution_revalidation_rejects_claim_bearing_drift(
    tmp_path,
    monkeypatch,
) -> None:
    def repositories(*, ignored_count):
        return {
            "parent": {
                "path": str(tmp_path),
                "commit": "1" * 40,
                "tree": "2" * 40,
                "clean": True,
                "tracked_claim_paths": ["runner.py"],
                "ignored_entry_count": ignored_count,
            },
            "fork": {
                "path": str(tmp_path),
                "commit": "3" * 40,
                "tree": "4" * 40,
                "clean": True,
                "tracked_claim_paths": ["native.py"],
                "frozen_base_commit": runner.BASE_FORK_COMMIT,
                "descends_from_frozen_base": True,
                "ignored_entry_count": ignored_count,
            },
        }

    pre_repositories = repositories(ignored_count=10)
    post_repositories = repositories(ignored_count=99)
    source_sha = {
        "parent": {"runner.py": "a" * 64},
        "fork": {"native.py": "b" * 64},
    }
    import_identity = {
        "quimb": {
            "origin": str(tmp_path / "quimb.py"),
            "source_sha256": "c" * 64,
        }
    }
    monkeypatch.setattr(
        runner,
        "_source_identity",
        lambda _parent, _fork: json.loads(json.dumps(source_sha)),
    )
    monkeypatch.setattr(
        runner,
        "_validate_parent_and_fork",
        lambda **_kwargs: json.loads(json.dumps(post_repositories)),
    )
    monkeypatch.setattr(
        runner,
        "_load_runtime",
        lambda _fork: SimpleNamespace(
            import_identity=json.loads(json.dumps(import_identity))
        ),
    )
    common = {
        "parent": tmp_path,
        "fork": tmp_path,
        "expected_parent_commit": "1" * 40,
        "expected_parent_tree": "2" * 40,
        "expected_fork_commit": "3" * 40,
        "expected_fork_tree": "4" * 40,
        "pre_repositories": pre_repositories,
        "pre_source_sha256": source_sha,
        "pre_import_identity": import_identity,
    }

    passed = runner._post_execution_revalidate(**common)
    assert passed["claim_bearing_repository_identity_equal"] is True
    assert passed["source_sha256_equal"] is True
    assert passed["import_identity_equal"] is True
    assert passed["ignored_inventory_equality_required"] is False
    assert (
        passed["post_repositories"]["fork"]["ignored_entry_count"]
        != pre_repositories["fork"]["ignored_entry_count"]
    )

    monkeypatch.setattr(
        runner,
        "_source_identity",
        lambda _parent, _fork: {
            "parent": {"runner.py": "d" * 64},
            "fork": {"native.py": "b" * 64},
        },
    )
    with pytest.raises(RuntimeError, match="source hashes changed"):
        runner._post_execution_revalidate(**common)

    monkeypatch.setattr(
        runner,
        "_source_identity",
        lambda _parent, _fork: json.loads(json.dumps(source_sha)),
    )
    changed_repositories = repositories(ignored_count=99)
    changed_repositories["fork"]["tree"] = "5" * 40
    monkeypatch.setattr(
        runner,
        "_validate_parent_and_fork",
        lambda **_kwargs: changed_repositories,
    )
    with pytest.raises(RuntimeError, match="repository identity changed"):
        runner._post_execution_revalidate(**common)

    monkeypatch.setattr(
        runner,
        "_validate_parent_and_fork",
        lambda **_kwargs: json.loads(json.dumps(post_repositories)),
    )
    monkeypatch.setattr(
        runner,
        "_load_runtime",
        lambda _fork: SimpleNamespace(
            import_identity={
                "quimb": {
                    "origin": str(tmp_path / "other.py"),
                    "source_sha256": "c" * 64,
                }
            }
        ),
    )
    with pytest.raises(RuntimeError, match="import identity changed"):
        runner._post_execution_revalidate(**common)


def test_cli_requires_all_four_caller_bound_git_identities(tmp_path) -> None:
    common = [
        "--output",
        str(tmp_path / "unused.json"),
        "--parent-repo",
        str(REPO),
        "--fork-repo",
        str(REPO / "external" / "forks" / "quimb-gcapeps"),
    ]
    with pytest.raises(SystemExit):
        runner._parse_args(common)

    parsed = runner._parse_args(
        [
            *common,
            "--expected-parent-commit",
            "1" * 40,
            "--expected-parent-tree",
            "2" * 40,
            "--expected-fork-commit",
            "3" * 40,
            "--expected-fork-tree",
            "4" * 40,
        ]
    )
    assert parsed.expected_parent_commit == "1" * 40
    assert parsed.expected_fork_tree == "4" * 40


def test_formal_entrypoint_is_guarded() -> None:
    tree = ast.parse(
        RUNNER_PATH.read_text(encoding="utf-8"),
        filename=str(RUNNER_PATH),
    )
    guards = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Name)
        and node.test.left.id == "__name__"
    ]
    assert guards
