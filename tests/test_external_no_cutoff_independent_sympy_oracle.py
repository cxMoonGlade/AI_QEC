"""Independent SymPy-oracle contracts for the pair/ADD microfixture."""

from __future__ import annotations

import ast
import inspect
from itertools import product


def test_independent_sympy_oracle_tracer_and_exhaustive_receipts() -> None:
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.independent_sympy_oracle import (
        run_independent_sympy_pair_add_oracle,
    )

    result = run_independent_sympy_pair_add_oracle()

    assert result["oracle"] == "INDEPENDENT_SYMPY_PAIR_ADD_LITERAL_ORACLE"
    assert result["scope"] == "MICRO_QUALIFICATION_ONLY"
    assert result["target_lowering"] == "UNAVAILABLE"
    assert result["solver_permission"] == "CODE_BLOCKED"
    assert result["support_history"] == [2, 8, 2]
    assert [receipt["roundtrip_assignment_count"] for receipt in result["codecs"]] == [
        64,
        64,
        128,
    ]
    assert [
        receipt["exhaustive_assignment_count"]
        for receipt in result["checkpoint_literal_maps"]
    ] == [64, 64, 128]
    assert [
        receipt["exhaustive_assignment_count"] for receipt in result["relations"]
    ] == [2**12, 2**13]
    assert [receipt["nonzero_count"] for receipt in result["relations"]] == [8, 8]

    tail = result["interference_evidence"]
    assert tail["tail"] == [[0, 1], [1, 2**42], [0, 1], [0, 1]]
    assert tail["tail_is_strictly_positive"] is True
    assert tail["tail_squared_is_below_1e_minus_24"] is True
    assert tail["deleted_zero"] == [[0, 1], [0, 1], [0, 1], [0, 1]]
    assert tail["deleted_zero_is_exact"] is True
    assert all(len(value) == 64 for key, value in result.items() if key.endswith("sha256"))


def test_independent_sympy_oracle_has_no_owner_or_fixture_import() -> None:
    from scripts.external_baselines.no_cutoff_minimal_exact_owners import (
        independent_sympy_oracle,
    )

    source = inspect.getsource(independent_sympy_oracle)
    tree = ast.parse(source)
    imports: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend((0, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append((node.level, node.module or ""))
    assert all(level == 0 for level, _module in imports)
    assert {module.split(".", 1)[0] for _level, module in imports} <= {
        "__future__",
        "dataclasses",
        "hashlib",
        "itertools",
        "json",
        "sympy",
    }

    forbidden_owner_symbols = {
        "PairKey",
        "Qsqrt2i",
        "Codec",
        "TransitionRow",
        "PairAddProgram",
        "frozen_pair_add_program",
        "canonical_json_bytes",
        "sha256_json",
        "run_pair_owner",
        "run_dynamic_add_owner",
    }
    observed = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
    } | {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
    }
    assert forbidden_owner_symbols.isdisjoint(observed)


def test_independent_literal_codecs_roundtrip_every_code() -> None:
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.independent_sympy_oracle import (
        CHECKPOINT_FIELDS,
        decode_literal_bits,
        encode_literal_key,
    )

    for fields in CHECKPOINT_FIELDS:
        for bits in product((0, 1), repeat=len(fields)):
            assert encode_literal_key(decode_literal_bits(bits, fields), fields) == bits


def test_independent_sympy_maps_match_pair_and_add_only_at_test_boundary() -> None:
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.add import (
        advance,
        build_total_function_from_fixture_clauses,
        compile_transition_relation,
    )
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.independent_sympy_oracle import (
        run_independent_sympy_pair_add_oracle,
    )
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.model import (
        ZERO,
        frozen_pair_add_program,
    )
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.pair import (
        run_pair_owner,
    )

    oracle = run_independent_sympy_pair_add_oracle()
    program = frozen_pair_add_program()
    pair = run_pair_owner(program)

    clauses = tuple(
        (program.codecs[0].encode(key), coefficient) for key, coefficient in program.initial
    )
    state = build_total_function_from_fixture_clauses(program.codecs[0], clauses)
    states = [state]
    relations = []
    for index, event in enumerate(program.events):
        relation = compile_transition_relation(
            event, program.codecs[index], program.codecs[index + 1]
        )
        relations.append(relation)
        state = advance(state, program.codecs[index], program.codecs[index + 1], relation)
        states.append(state)

    assert oracle["support_history"] == pair["support_history"]
    for oracle_checkpoint, pair_checkpoint, add_state in zip(
        oracle["checkpoint_literal_maps"], pair["checkpoints"], states, strict=True
    ):
        oracle_entries = {
            tuple(entry["bits"]): (entry["coefficient"], entry["key"])
            for entry in oracle_checkpoint["nonzero_witnesses"]
        }
        pair_entries = {
            tuple(entry["bits"]): (entry["coefficient"], entry["key"])
            for entry in pair_checkpoint["entries"]
        }
        assert oracle_entries == pair_entries
        for bits in product((0, 1), repeat=add_state.width):
            expected = oracle_entries.get(bits, (ZERO.to_data(), None))[0]
            assert add_state.evaluate(bits).to_data() == expected

    for oracle_relation, owner_relation in zip(
        oracle["relations"], relations, strict=True
    ):
        expected = {
            tuple(entry["combined_bits"]): entry["coefficient"]
            for entry in oracle_relation["nonzero_witnesses"]
        }
        for bits in product((0, 1), repeat=owner_relation.state.width):
            assert owner_relation.state.evaluate(bits).to_data() == expected.get(
                bits, ZERO.to_data()
            )
