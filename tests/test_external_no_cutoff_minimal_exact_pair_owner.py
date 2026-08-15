"""TDD contracts for the no-cutoff exact-pair micro-owner.

This qualification surface is deliberately smaller than the d=3/5 target
lowering.  A pass cannot authorize a solver or populate the historical census.
"""

from __future__ import annotations

from fractions import Fraction

import pytest


def test_exact_four_fraction_algebra_rejects_float_and_matches_sympy() -> None:
    from sympy import I, Rational, expand, sqrt

    from scripts.external_baselines.no_cutoff_minimal_exact_owners.model import (
        Qsqrt2i,
    )

    left = Qsqrt2i(Fraction(3, 5), Fraction(-2, 7), Fraction(11, 13), Fraction(1, 3))
    right = Qsqrt2i(Fraction(-4, 9), Fraction(5, 8), Fraction(2, 3), Fraction(-7, 10))
    product = left * right
    left_sym = Rational(3, 5) - Rational(2, 7) * sqrt(2) + I * (
        Rational(11, 13) + Rational(1, 3) * sqrt(2)
    )
    right_sym = -Rational(4, 9) + Rational(5, 8) * sqrt(2) + I * (
        Rational(2, 3) - Rational(7, 10) * sqrt(2)
    )
    product_sym = expand(left_sym * right_sym)
    rebuilt = (
        Rational(product.a.numerator, product.a.denominator)
        + Rational(product.b.numerator, product.b.denominator) * sqrt(2)
        + I
        * (
            Rational(product.c.numerator, product.c.denominator)
            + Rational(product.d.numerator, product.d.denominator) * sqrt(2)
        )
    )
    assert expand(product_sym - rebuilt) == 0

    with pytest.raises(TypeError, match="Fraction"):
        Qsqrt2i(0.0, Fraction(0), Fraction(0), Fraction(0))  # type: ignore[arg-type]


def test_pair_owner_tracer_bullet_preserves_the_frozen_tail() -> None:
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.model import (
        frozen_pair_add_program,
    )
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.pair import (
        run_pair_owner,
    )

    result = run_pair_owner(frozen_pair_add_program())

    assert result["scope"] == "MICRO_QUALIFICATION_ONLY"
    assert result["support_history"] == [2, 8, 2]
    assert result["n_pauli_pair_states_peak_micro"] == 8
    assert result["peak_event"] == "E1_BRANCH"
    assert len(result["checkpoints"][-1]["entries"]) == 2
    assert {
        tuple(tuple(rational) for rational in entry["coefficient"])
        for entry in result["checkpoints"][-1]["entries"]
    } == {
        ((0, 1), (1, 2**42), (0, 1), (0, 1)),
    }
    assert result["target_lowering"] == "UNAVAILABLE"
    assert result["solver_permission"] == "CODE_BLOCKED"


def test_pair_owner_rejects_a_left_right_codec_reordering() -> None:
    from dataclasses import replace

    from scripts.external_baselines.no_cutoff_minimal_exact_owners.model import (
        Codec,
        frozen_pair_add_program,
    )
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.pair import (
        run_pair_owner,
    )

    program = frozen_pair_add_program()
    swapped = Codec("A0-swapped", ("R.x", "L.z", "L.x", "R.z", "m", "frame"))
    corrupted = replace(program, codecs=(swapped, program.codecs[1], program.codecs[2]))

    with pytest.raises(ValueError, match="frozen codec"):
        run_pair_owner(corrupted)


def test_pair_relation_row_order_is_not_semantic() -> None:
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.model import (
        frozen_pair_add_program,
    )
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.pair import (
        run_pair_owner,
    )

    forward_program = frozen_pair_add_program()
    reverse_program = frozen_pair_add_program(reverse_rows=True)
    forward = run_pair_owner(forward_program)
    reverse = run_pair_owner(reverse_program)

    assert forward_program.sha256 == reverse_program.sha256
    assert forward["support_history"] == reverse["support_history"]
    assert [x["map_sha256"] for x in forward["checkpoints"]] == [
        x["map_sha256"] for x in reverse["checkpoints"]
    ]


def test_pair_codec_keeps_left_right_latent_frame_and_record_distinct() -> None:
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.model import (
        FROZEN_CODEC_0_FIELDS,
        Codec,
        PairKey,
    )

    codec0 = Codec("witness-0", FROZEN_CODEC_0_FIELDS)
    codec2 = Codec("witness-2", FROZEN_CODEC_0_FIELDS + ("d0",))
    base0 = PairKey(1, 0, 0, 0, -1, 0, ())
    left_only = PairKey(0, 0, 0, 0, -1, 0, ())
    right_only = PairKey(1, 0, 1, 0, -1, 0, ())
    latent_only = PairKey(1, 0, 0, 0, 1, 0, ())
    frame_only = PairKey(1, 0, 0, 0, -1, 1, ())
    assert codec0.encode(base0) != codec0.encode(left_only)
    assert codec0.encode(base0) != codec0.encode(right_only)
    assert codec0.encode(base0) != codec0.encode(latent_only)
    assert codec0.encode(base0) != codec0.encode(frame_only)

    base2 = PairKey(1, 0, 0, 0, -1, 0, (0,))
    assert codec2.encode(base2) != codec2.encode(PairKey(1, 0, 0, 0, -1, 0, (1,)))
    with pytest.raises(ValueError, match="unique"):
        Codec("duplicate-L", ("L.x", "L.x", "R.x", "R.z", "m", "frame"))
    with pytest.raises(ValueError, match="missing or unknown"):
        Codec("missing-frame", ("L.x", "L.z", "R.x", "R.z", "m"))


def test_pair_tail_and_deleted_zero_match_literal_sympy_algebra() -> None:
    from sympy import I, Rational, simplify, sqrt

    from scripts.external_baselines.no_cutoff_minimal_exact_owners.model import (
        frozen_pair_add_program,
    )
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.pair import (
        run_pair_owner,
    )

    delta = Rational(1, 2**40)
    tail = simplify(Rational(1, 2) + sqrt(2) / 4 * (-sqrt(2) + delta))
    deleted = simplify(I / 2 + (-I * sqrt(2) / 4) * sqrt(2))
    assert tail == sqrt(2) / 2**42
    assert 0 < tail**2 < Rational(1, 10**24)
    assert deleted == 0

    final_entries = run_pair_owner(frozen_pair_add_program())["checkpoints"][-1]["entries"]
    assert len(final_entries) == 2
    assert all(entry["coefficient"] == [[0, 1], [1, 2**42], [0, 1], [0, 1]] for entry in final_entries)


def test_pair_owner_rejects_a_changed_exact_transition_weight() -> None:
    from dataclasses import replace

    from scripts.external_baselines.no_cutoff_minimal_exact_owners.model import (
        ZERO,
        frozen_pair_add_program,
    )
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.pair import (
        run_pair_owner,
    )

    program = frozen_pair_add_program()
    first = program.events[0]
    changed_row = replace(first.rows[0], weight=ZERO)
    changed_event = replace(first, rows=(changed_row,) + first.rows[1:])
    changed = replace(program, events=(changed_event, program.events[1]))

    with pytest.raises(ValueError, match="fixture identity"):
        run_pair_owner(changed)
