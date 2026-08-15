"""Public contracts for exact retained-boundary target factor networks."""

from __future__ import annotations

import pytest


def test_d3_r1_tn_owns_exact_tables_sign_chain_and_record_boundary() -> None:
    from scripts.external_baselines.no_cutoff_target_lowering.neutral import (
        lower_frozen_declared_error_record,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.tn import (
        build_retained_boundary_factor_network,
    )

    neutral = lower_frozen_declared_error_record(distance=3, rounds=1)
    tn = build_retained_boundary_factor_network(neutral)
    data = tn.to_data()
    semantic = data["semantic"]

    assert data["_schema"] == (
        "error_coupling_simulator.external.retained_boundary_factor_network.v1"
    )
    assert semantic["neutral_sha256"] == neutral.sha256
    assert len(semantic["boundary"]) == 9
    keep_factors = [
        factor for factor in semantic["factors"] if factor["template_id"] == "KEEP"
    ]
    assert [factor["scope"][0] for factor in keep_factors] == semantic["boundary"]
    assert len(semantic["sign_occurrence_ledger"]) == 56
    assert len(
        [factor for factor in semantic["factors"] if factor["template_id"] == "SIGN_EQ"]
    ) == 56
    assert len(
        [
            factor
            for factor in semantic["factors"]
            if factor["template_id"] == "COHERENT_Z"
        ]
    ) == 56
    assert len(semantic["raw_consumer_ledger"]) == 17
    assert len(semantic["marker_ledger"]) == 24
    assert all(
        index["domain"] == (4 if index["kind"] == "DENSITY" else 2)
        for index in semantic["index_catalog"]
    )
    required_templates = {
        "INIT0",
        "TRACE",
        "H",
        "CX",
        "COHERENT_Z",
        "R",
        "M",
        "MR",
        "HALF",
        "SIGN_EQ",
        "ONE",
        "COPY",
        "ZERO",
        "XOR",
        "KEEP",
    }
    templates = {template["template_id"]: template for template in semantic["table_catalog"]}
    assert set(templates) == required_templates
    for template in templates.values():
        entries = 1
        for extent in template["shape"]:
            entries *= extent
        assert len(template["table"]) == entries
    assert "contraction_order" not in repr(data)
    assert "treewidth" not in repr(data)


def test_exact_tn_tables_match_independent_literal_reconstruction() -> None:
    from copy import deepcopy

    import pytest

    from scripts.external_baselines.no_cutoff_target_lowering.independent_tn_oracle import (
        reconstruct_table_catalog,
        validate_table_catalog,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.neutral import (
        lower_frozen_declared_error_record,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.tn import (
        build_retained_boundary_factor_network,
    )

    owner = build_retained_boundary_factor_network(
        lower_frozen_declared_error_record(distance=3, rounds=1)
    ).to_data()["semantic"]["table_catalog"]
    assert owner == reconstruct_table_catalog()
    validate_table_catalog(owner)

    corrupted = deepcopy(owner)
    coherent = next(row for row in corrupted if row["template_id"] == "COHERENT_Z")
    # Swap only the sign rows in each (q_in,q_out) block while keeping the
    # registered 0->-1,1->+1 codec: a symmetric prior cannot excuse this.
    for offset in range(0, len(coherent["table"]), 2):
        coherent["table"][offset], coherent["table"][offset + 1] = (
            coherent["table"][offset + 1],
            coherent["table"][offset],
        )
    with pytest.raises(ValueError, match="COHERENT_Z"):
        validate_table_catalog(corrupted)


def test_all_target_tn_incidence_matches_source_driven_independent_reconstruction() -> None:
    from scripts.external_baselines.no_cutoff_target_lowering.independent_tn_oracle import (
        reconstruct_network_incidence,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.neutral import (
        lower_frozen_declared_error_record,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.tn import (
        build_retained_boundary_factor_network,
    )

    incidence_keys = (
        "index_catalog",
        "factors",
        "boundary",
        "marker_ledger",
        "raw_consumer_ledger",
        "sign_occurrence_ledger",
    )
    for distance in (3, 5):
        for rounds in (1, 3, 5, 7):
            neutral = lower_frozen_declared_error_record(
                distance=distance, rounds=rounds
            )
            owner = build_retained_boundary_factor_network(neutral).to_data()[
                "semantic"
            ]
            independent = reconstruct_network_incidence(
                neutral.to_data()["semantic"]["source"]["source_text"]
            )
            assert {key: owner[key] for key in incidence_keys} == independent


def test_tiny_retained_tensors_match_direct_density_branching_exactly() -> None:
    from fractions import Fraction

    from scripts.external_baselines.no_cutoff_target_lowering.independent_tn_oracle import (
        reconstruct_tiny_retained_tensor,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.tn import (
        contract_tiny_retained_tensor,
    )

    for witness_id in ("T1", "T2", "T3", "T4"):
        assert contract_tiny_retained_tensor(witness_id) == (
            reconstruct_tiny_retained_tensor(witness_id)
        )

    persistent = contract_tiny_retained_tensor("T3")
    iid = contract_tiny_retained_tensor("T3", sign_process="iid")
    expected_delta = Fraction(2 * 9999 * 9999 * 200 * 200, 10001**4)
    assert [
        Fraction(row_p["value"][0][0], row_p["value"][0][1])
        - Fraction(row_i["value"][0][0], row_i["value"][0][1])
        for row_p, row_i in zip(persistent, iid, strict=True)
    ] == [expected_delta, Fraction(0), Fraction(0), -expected_delta]


def test_tn_typing_accepts_preregistered_terminal_and_record_wires() -> None:
    from scripts.external_baselines.no_cutoff_target_lowering.independent_tn_oracle import (
        validate_network_types,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.neutral import (
        lower_frozen_declared_error_record,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.tn import (
        build_retained_boundary_factor_network,
    )

    semantic = build_retained_boundary_factor_network(
        lower_frozen_declared_error_record(distance=3, rounds=1)
    ).to_data()["semantic"]
    validate_network_types(semantic)

    index_kinds = {
        row["index_id"]: row["kind"] for row in semantic["index_catalog"]
    }
    terminal_kinds = {
        factor["provenance"]["role"]: index_kinds[factor["scope"][0]]
        for factor in semantic["factors"]
        if factor["template_id"] == "ONE"
    }
    assert terminal_kinds["SIGN_TERMINAL"] == "SIGN"
    assert terminal_kinds["RAW_TERMINAL"] == "RAW"

    final_xors = [
        factor
        for factor in semantic["factors"]
        if factor["template_id"] == "XOR"
        and index_kinds[factor["scope"][2]] == "RECORD"
    ]
    assert len(final_xors) == len(semantic["boundary"])


@pytest.mark.parametrize("terminal_role", ("SIGN_TERMINAL", "RAW_TERMINAL"))
def test_tn_strict_reload_rejects_one_on_a_density_wire_as_a_type_error(
    terminal_role: str,
) -> None:
    from copy import deepcopy

    import pytest

    from scripts.external_baselines.no_cutoff_target_lowering.independent_tn_oracle import (
        validate_network_types,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.model import sha256_json
    from scripts.external_baselines.no_cutoff_target_lowering.neutral import (
        lower_frozen_declared_error_record,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.tn import (
        build_retained_boundary_factor_network,
        validate_retained_boundary_factor_network,
    )

    neutral = lower_frozen_declared_error_record(distance=3, rounds=1)
    candidate = deepcopy(build_retained_boundary_factor_network(neutral).to_data())
    density_index = next(
        row["index_id"]
        for row in candidate["semantic"]["index_catalog"]
        if row["kind"] == "DENSITY"
    )
    terminal = next(
        factor
        for factor in candidate["semantic"]["factors"]
        if factor["provenance"]["role"] == terminal_role
    )
    terminal["scope"] = [density_index]
    candidate["semantic_sha256"] = sha256_json(candidate["semantic"])

    with pytest.raises(ValueError, match="expects CLASSICAL, got DENSITY"):
        validate_network_types(candidate["semantic"])
    with pytest.raises(ValueError, match="expects CLASSICAL, got DENSITY"):
        validate_retained_boundary_factor_network(candidate, neutral=neutral)


def test_tn_type_checkers_reject_a_final_xor_into_a_raw_wire() -> None:
    from copy import deepcopy

    import pytest

    from scripts.external_baselines.no_cutoff_target_lowering.independent_tn_oracle import (
        validate_network_types,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.model import sha256_json
    from scripts.external_baselines.no_cutoff_target_lowering.neutral import (
        lower_frozen_declared_error_record,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.tn import (
        build_retained_boundary_factor_network,
        validate_retained_boundary_factor_network,
    )

    neutral = lower_frozen_declared_error_record(distance=3, rounds=1)
    candidate = deepcopy(build_retained_boundary_factor_network(neutral).to_data())
    index_rows = {
        row["index_id"]: row for row in candidate["semantic"]["index_catalog"]
    }
    final_xor = next(
        factor
        for factor in candidate["semantic"]["factors"]
        if factor["template_id"] == "XOR"
        and index_rows[factor["scope"][2]]["kind"] == "RECORD"
    )
    index_rows[final_xor["scope"][2]]["kind"] = "RAW"
    candidate["semantic_sha256"] = sha256_json(candidate["semantic"])

    with pytest.raises(ValueError, match="expects PARITY, got RAW"):
        validate_network_types(candidate["semantic"])
    with pytest.raises(ValueError, match="expects PARITY, got RAW"):
        validate_retained_boundary_factor_network(candidate, neutral=neutral)


def test_tn_type_checkers_reject_a_record_wire_as_xor_accumulator() -> None:
    from copy import deepcopy

    from scripts.external_baselines.no_cutoff_target_lowering.independent_tn_oracle import (
        validate_network_types,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.model import sha256_json
    from scripts.external_baselines.no_cutoff_target_lowering.neutral import (
        lower_frozen_declared_error_record,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.tn import (
        build_retained_boundary_factor_network,
        validate_retained_boundary_factor_network,
    )

    neutral = lower_frozen_declared_error_record(distance=3, rounds=1)
    candidate = deepcopy(build_retained_boundary_factor_network(neutral).to_data())
    index_kinds = {
        row["index_id"]: row["kind"]
        for row in candidate["semantic"]["index_catalog"]
    }
    final_xor = next(
        factor
        for factor in candidate["semantic"]["factors"]
        if factor["template_id"] == "XOR"
        and index_kinds[factor["scope"][2]] == "RECORD"
    )
    final_xor["scope"][0] = final_xor["scope"][2]
    candidate["semantic_sha256"] = sha256_json(candidate["semantic"])

    with pytest.raises(ValueError, match="slot 0 expects PARITY, got RECORD"):
        validate_network_types(candidate["semantic"])
    with pytest.raises(ValueError, match="slot 0 expects PARITY, got RECORD"):
        validate_retained_boundary_factor_network(candidate, neutral=neutral)


@pytest.mark.parametrize(
    ("index_kind", "wrong_domain"),
    (("DENSITY", 2), ("RECORD", 4)),
)
def test_tn_type_checkers_reject_wrong_index_domains(
    index_kind: str,
    wrong_domain: int,
) -> None:
    from copy import deepcopy

    from scripts.external_baselines.no_cutoff_target_lowering.independent_tn_oracle import (
        validate_network_types,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.model import sha256_json
    from scripts.external_baselines.no_cutoff_target_lowering.neutral import (
        lower_frozen_declared_error_record,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.tn import (
        build_retained_boundary_factor_network,
        validate_retained_boundary_factor_network,
    )

    neutral = lower_frozen_declared_error_record(distance=3, rounds=1)
    candidate = deepcopy(build_retained_boundary_factor_network(neutral).to_data())
    index = next(
        row
        for row in candidate["semantic"]["index_catalog"]
        if row["kind"] == index_kind
    )
    index["domain"] = wrong_domain
    candidate["semantic_sha256"] = sha256_json(candidate["semantic"])

    with pytest.raises(ValueError, match="TN index domain.*does not match"):
        validate_network_types(candidate["semantic"])
    with pytest.raises(ValueError, match="TN index domain.*does not match"):
        validate_retained_boundary_factor_network(candidate, neutral=neutral)


@pytest.mark.parametrize("forgery", ("process", "source", "event", "record"))
def test_tn_builder_authenticates_the_complete_upstream_neutral_program(
    forgery: str,
) -> None:
    from copy import deepcopy

    from scripts.external_baselines.no_cutoff_target_lowering.model import (
        NEUTRAL_SCHEMA,
        StaticArtifact,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.neutral import (
        lower_frozen_declared_error_record,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.tn import (
        build_retained_boundary_factor_network,
    )

    semantic = deepcopy(
        lower_frozen_declared_error_record(distance=3, rounds=1).to_data()[
            "semantic"
        ]
    )
    if forgery == "process":
        semantic["process"]["axis"] = "X"
    elif forgery == "source":
        semantic["source"]["generator"] = "forged_generator"
    elif forgery == "event":
        semantic["events"][0]["kernel_id"] = "FORGED_MARKER"
    elif forgery == "record":
        semantic["record_schema"]["record_width"] += 1
    else:  # pragma: no cover - parameter list is frozen above.
        raise AssertionError(f"unknown test forgery {forgery}")

    forged = StaticArtifact(NEUTRAL_SCHEMA, semantic)
    with pytest.raises(
        ValueError,
        match="frozen semantic identity|Record schema",
    ):
        build_retained_boundary_factor_network(forged)


def test_tn_factor_order_is_bound_and_reordering_rejects_on_reload() -> None:
    from copy import deepcopy

    from scripts.external_baselines.no_cutoff_target_lowering.model import sha256_json
    from scripts.external_baselines.no_cutoff_target_lowering.neutral import (
        lower_frozen_declared_error_record,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.tn import (
        build_retained_boundary_factor_network,
        validate_retained_boundary_factor_network,
    )

    neutral = lower_frozen_declared_error_record(distance=3, rounds=1)
    owner = build_retained_boundary_factor_network(neutral)
    reordered = deepcopy(owner.to_data())
    factors = reordered["semantic"]["factors"]
    factors[0], factors[1] = factors[1], factors[0]
    reordered["semantic_sha256"] = sha256_json(reordered["semantic"])

    assert reordered["semantic_sha256"] != owner.semantic_sha256
    with pytest.raises(ValueError, match="frozen semantic identity"):
        validate_retained_boundary_factor_network(reordered, neutral=neutral)


def test_raw_consumer_reversal_differs_from_source_driven_incidence_oracle() -> None:
    from copy import deepcopy

    from scripts.external_baselines.no_cutoff_target_lowering.independent_tn_oracle import (
        reconstruct_network_incidence,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.neutral import (
        lower_frozen_declared_error_record,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.tn import (
        build_retained_boundary_factor_network,
    )

    neutral = lower_frozen_declared_error_record(distance=3, rounds=1)
    owner = build_retained_boundary_factor_network(neutral).to_data()["semantic"]
    source_text = neutral.to_data()["semantic"]["source"]["source_text"]
    independent = reconstruct_network_incidence(source_text)
    incidence_keys = (
        "index_catalog",
        "factors",
        "boundary",
        "marker_ledger",
        "raw_consumer_ledger",
        "sign_occurrence_ledger",
    )
    assert {key: owner[key] for key in incidence_keys} == independent

    reversed_ledger = deepcopy(owner)
    row = next(
        item
        for item in reversed_ledger["raw_consumer_ledger"]
        if len(item["consumers"]) > 1
    )
    row["consumers"].reverse()
    assert {
        key: reversed_ledger[key] for key in incidence_keys
    } != independent
    assert reversed_ledger["raw_consumer_ledger"] != independent[
        "raw_consumer_ledger"
    ]


@pytest.mark.parametrize(
    ("control_id", "witness_id"),
    (
        ("tn_measurement_dephased", "T1"),
        ("tn_reset_trace_omitted", "T2"),
    ),
)
def test_tiny_table_corruptions_change_the_direct_density_record_tensor(
    control_id: str,
    witness_id: str,
) -> None:
    from scripts.external_baselines.no_cutoff_target_lowering.independent_tn_oracle import (
        reconstruct_tiny_retained_tensor,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.tn import (
        build_tiny_corrupted_table_catalog,
        contract_tiny_retained_tensor,
    )

    direct_density = reconstruct_tiny_retained_tensor(witness_id)
    corrupted_catalog = build_tiny_corrupted_table_catalog(control_id)
    corrupted_tensor = contract_tiny_retained_tensor(
        witness_id,
        table_catalog=corrupted_catalog,
    )

    assert corrupted_tensor != direct_density


@pytest.mark.parametrize(
    ("malformation", "error"),
    (
        ("partial", "complete catalog"),
        ("shape", "changes shape"),
        ("float", "four coordinates"),
    ),
)
def test_tiny_table_override_requires_a_complete_exact_catalog(
    malformation: str,
    error: str,
) -> None:
    from scripts.external_baselines.no_cutoff_target_lowering.tn import (
        build_tiny_corrupted_table_catalog,
        contract_tiny_retained_tensor,
    )

    catalog = build_tiny_corrupted_table_catalog("tn_measurement_dephased")
    if malformation == "partial":
        catalog.pop()
    elif malformation == "shape":
        catalog[0]["shape"] = [2]
    elif malformation == "float":
        catalog[0]["table"][0] = 0.5
    else:  # pragma: no cover - parameter list is frozen above.
        raise AssertionError(f"unknown table malformation {malformation}")

    with pytest.raises((TypeError, ValueError), match=error):
        contract_tiny_retained_tensor("T1", table_catalog=catalog)


def test_keep_omission_is_numerically_inert_but_structurally_rejected() -> None:
    from copy import deepcopy

    from scripts.external_baselines.no_cutoff_target_lowering.independent_tn_oracle import (
        reconstruct_network_incidence,
        validate_retained_boundary_keep_coverage,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.neutral import (
        lower_frozen_declared_error_record,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.tn import (
        build_retained_boundary_factor_network,
        contract_tiny_retained_tensor,
    )

    neutral = lower_frozen_declared_error_record(distance=3, rounds=1)
    clean = build_retained_boundary_factor_network(neutral).to_data()["semantic"]
    validate_retained_boundary_keep_coverage(clean)

    missing = deepcopy(clean)
    keep_index = next(
        index
        for index, factor in enumerate(missing["factors"])
        if factor["template_id"] == "KEEP"
    )
    missing["factors"].pop(keep_index)
    with pytest.raises(ValueError, match="retained boundary KEEP coverage"):
        validate_retained_boundary_keep_coverage(missing)

    source_text = neutral.to_data()["semantic"]["source"]["source_text"]
    incidence = reconstruct_network_incidence(source_text)
    assert missing["factors"] != incidence["factors"]

    clean_tensor = contract_tiny_retained_tensor("T1")
    keep_omitted_tensor = contract_tiny_retained_tensor(
        "T1",
        boundary_keep="omitted_control",
    )
    assert keep_omitted_tensor == clean_tensor
