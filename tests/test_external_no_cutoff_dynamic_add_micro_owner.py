"""TDD contracts for the direct dynamic exact-ADD micro-owner."""

from __future__ import annotations

from itertools import product

import ast
import inspect
import pytest


def test_dynamic_add_matches_independent_sparse_truth_at_every_code(monkeypatch) -> None:
    from scripts.external_baselines.no_cutoff_minimal_exact_owners import pair
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.add import (
        advance,
        build_total_function_from_fixture_clauses,
        compile_transition_relation,
    )
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.model import (
        ZERO,
        frozen_pair_add_program,
    )

    program = frozen_pair_add_program()
    sparse = pair.run_pair_owner(program)
    monkeypatch.setattr(
        pair,
        "run_pair_owner",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("frontier poisoned")),
    )

    clauses = tuple(
        (program.codecs[0].encode(key), coefficient) for key, coefficient in program.initial
    )
    state = build_total_function_from_fixture_clauses(program.codecs[0], clauses)
    states = [state]
    for index, event in enumerate(program.events):
        relation = compile_transition_relation(
            event, program.codecs[index], program.codecs[index + 1]
        )
        state = advance(state, program.codecs[index], program.codecs[index + 1], relation)
        states.append(state)

    for state, checkpoint in zip(states, sparse["checkpoints"], strict=True):
        expected = {
            tuple(entry["bits"]): entry["coefficient"] for entry in checkpoint["entries"]
        }
        for bits in product((0, 1), repeat=state.width):
            assert state.evaluate(bits).to_data() == expected.get(bits, ZERO.to_data())


def test_dynamic_advance_has_no_sparse_or_exhaustive_backdoor(monkeypatch) -> None:
    from scripts.external_baselines.no_cutoff_minimal_exact_owners import add
    from scripts.external_baselines.no_cutoff_minimal_exact_owners import pair
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.model import (
        frozen_pair_add_program,
    )

    tree = ast.parse(inspect.getsource(add))
    definitions: dict[str, list[ast.FunctionDef | ast.AsyncFunctionDef]] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            definitions.setdefault(node.name, []).append(node)
    reachable = {"run_dynamic_add_owner"}
    changed = True
    while changed:
        changed = False
        for name in tuple(reachable):
            for function in definitions[name]:
                for node in ast.walk(function):
                    called = None
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                        called = node.func.id
                    elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                        called = node.func.attr
                    if called in definitions and called not in reachable:
                        reachable.add(called)
                        changed = True
    assert {
        "_apply",
        "_build_clause_function",
        "_copy_reachable",
        "_rename_output_root",
        "_snapshot",
        "advance",
        "compile_transition_relation",
        "multiply",
        "run_dynamic_add_owner",
        "sum_abstract_level",
    } <= reachable

    forbidden_tokens = {
        "frontier",
        "iter_nonzero",
        "nonzero_assignments",
        "to_sparse",
        "truth_table",
        "evaluate_all",
        "pair_map",
    }
    observed: set[str] = set()
    for name in reachable:
        for function in definitions[name]:
            for node in ast.walk(function):
                if isinstance(node, ast.Name):
                    observed.add(node.id)
                elif isinstance(node, ast.Attribute):
                    observed.add(node.attr)
    assert forbidden_tokens.isdisjoint(observed)

    advance_source = inspect.getsource(add.advance)
    assert ".multiply(" in advance_source
    assert ".sum_abstract_level(" in advance_source
    assert "_rename_output_root(" in advance_source
    relation_parameters = tuple(inspect.signature(add.compile_transition_relation).parameters)
    assert relation_parameters == ("event", "input_codec", "output_codec")

    compile_calls: list[tuple[str, int, int]] = []
    build_widths: list[int] = []
    original_compile = add.compile_transition_relation
    original_build = add._build_clause_function

    def compile_spy(event, input_codec, output_codec):
        compile_calls.append((event.name, input_codec.width, output_codec.width))
        return original_compile(event, input_codec, output_codec)

    def build_spy(*, width, codec_sha256, clauses):
        build_widths.append(width)
        return original_build(
            width=width, codec_sha256=codec_sha256, clauses=clauses
        )

    monkeypatch.setattr(add, "compile_transition_relation", compile_spy)
    monkeypatch.setattr(add, "_build_clause_function", build_spy)
    monkeypatch.setattr(
        pair,
        "run_pair_owner",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("pair frontier poisoned")
        ),
    )
    result = add.run_dynamic_add_owner(frozen_pair_add_program())
    assert compile_calls == [
        ("E1_BRANCH", 6, 6),
        ("E2_INTERFERE_AND_EMIT", 6, 7),
    ]
    assert build_widths == [12, 13, 6]
    assert result["n_exact_pair_add_nodes_history_micro"] == [7, 20, 11]


def test_dynamic_add_relation_order_and_row_permutation_are_hash_bound() -> None:
    from dataclasses import replace

    from scripts.external_baselines.no_cutoff_minimal_exact_owners.add import (
        advance,
        build_total_function_from_fixture_clauses,
        compile_transition_relation,
        run_dynamic_add_owner,
    )
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.model import (
        frozen_pair_add_program,
    )

    forward = run_dynamic_add_owner(frozen_pair_add_program())
    reverse = run_dynamic_add_owner(frozen_pair_add_program(reverse_rows=True))
    assert forward["n_exact_pair_add_nodes_history_micro"] == reverse[
        "n_exact_pair_add_nodes_history_micro"
    ]
    assert [x["node_table_sha256"] for x in forward["checkpoints"]] == [
        x["node_table_sha256"] for x in reverse["checkpoints"]
    ]
    assert forward["relation_receipts"] == reverse["relation_receipts"]
    assert forward["relation_receipts"][0]["combined_order"] == [
        "in:L.x",
        "in:L.z",
        "in:R.x",
        "in:R.z",
        "in:m",
        "in:frame",
        "out:L.x",
        "out:L.z",
        "out:R.x",
        "out:R.z",
        "out:m",
        "out:frame",
    ]
    assert len(forward["relation_receipts"][1]["combined_order"]) == 13

    program = frozen_pair_add_program()
    initial = build_total_function_from_fixture_clauses(
        program.codecs[0],
        tuple(
            (program.codecs[0].encode(key), coefficient)
            for key, coefficient in program.initial
        ),
    )
    relation = compile_transition_relation(
        program.events[0], program.codecs[0], program.codecs[1]
    )
    with pytest.raises(ValueError, match="combined order"):
        advance(
            initial,
            program.codecs[0],
            program.codecs[1],
            replace(relation, combined_order=tuple(reversed(relation.combined_order))),
        )
    with pytest.raises(ValueError, match="state width"):
        advance(
            initial,
            program.codecs[0],
            program.codecs[1],
            replace(
                relation,
                state=replace(relation.state, width=relation.state.width + 1),
            ),
        )


def test_dynamic_add_rejects_the_smaller_wrong_variable_order() -> None:
    from fractions import Fraction

    from scripts.external_baselines.no_cutoff_minimal_exact_owners.add import (
        build_total_function_from_fixture_clauses,
        snapshot_add_state,
    )
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.model import (
        Codec,
        Qsqrt2i,
        frozen_fixture_keys,
    )

    codec = Codec("wrong-order", ("L.x", "R.x", "L.z", "R.z", "m", "frame"))
    keys = frozen_fixture_keys()
    values = {
        "a": Qsqrt2i.rational(1, 2),
        "b": Qsqrt2i.sqrt2(Fraction(1, 4)),
        "c": Qsqrt2i.imag(Fraction(1, 2)),
        "d": Qsqrt2i(Fraction(0), Fraction(0), Fraction(0), Fraction(-1, 4)),
    }
    clauses = tuple(
        (codec.encode(key), values[label])
        for label in ("a", "b", "c", "d")
        for key in keys[label]
    )
    snapshot = snapshot_add_state(
        "WRONG_ORDER", build_total_function_from_fixture_clauses(codec, clauses)
    )
    assert snapshot["internal_count"] == 13
    assert snapshot["terminal_count"] == 5
    assert snapshot["reachable_node_count"] == 18


def test_dynamic_add_gc_keeps_tiny_terminal_and_discards_cancelled_dead_nodes() -> None:
    from fractions import Fraction

    from scripts.external_baselines.no_cutoff_minimal_exact_owners.add import (
        build_total_function_from_fixture_clauses,
        snapshot_add_state,
    )
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.model import (
        Codec,
        ONE,
        Qsqrt2i,
    )

    codec = Codec("tiny-gc", ("L.x", "L.z", "R.x", "R.z", "m", "frame"))
    # All unspecified bits are fixed too; duplicate clauses cancel before GC.
    zero_bits = (0, 0, 0, 0, 0, 0)
    one_bits = (1, 0, 0, 0, 0, 0)
    epsilon = Qsqrt2i.sqrt2(Fraction(1, 2**42))
    state = build_total_function_from_fixture_clauses(
        codec,
        ((zero_bits, ONE), (zero_bits, -ONE), (one_bits, epsilon)),
    )
    snapshot = snapshot_add_state("TINY_GC", state)

    assert snapshot["terminal_count"] == 2
    assert snapshot["reachable_node_count"] == 8
    assert snapshot["allocated_node_count"] == 8
    assert [
        node["value"] for node in snapshot["node_table"] if node["kind"] == "terminal"
    ] == [
        [[0, 1], [0, 1], [0, 1], [0, 1]],
        [[0, 1], [1, 2**42], [0, 1], [0, 1]],
    ]


def test_dynamic_add_tracer_bullet_owns_the_live_peak_not_the_final_pmf() -> None:
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.add import (
        run_dynamic_add_owner,
    )
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.model import (
        frozen_pair_add_program,
    )

    result = run_dynamic_add_owner(frozen_pair_add_program())

    assert result["scope"] == "MICRO_QUALIFICATION_ONLY"
    assert result["n_exact_pair_add_nodes_history_micro"] == [7, 20, 11]
    assert result["n_exact_pair_add_nodes_peak_micro"] == 20
    assert result["peak_event"] == "E1_BRANCH"
    assert result["checkpoints"][-1]["internal_count"] == 9
    assert result["checkpoints"][-1]["terminal_count"] == 2
    assert result["checkpoints"][-1]["reachable_node_count"] == 11
    assert result["checkpoints"][-1]["allocated_node_count"] == 11
    assert result["headline_semantics"] == "DYNAMIC_PAIR_MAP_NOT_FINAL_RECORD_PMF"
    assert result["target_lowering"] == "UNAVAILABLE"
    assert result["solver_permission"] == "CODE_BLOCKED"
