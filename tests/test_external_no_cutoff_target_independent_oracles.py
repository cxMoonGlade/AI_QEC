"""Independence and strict-reload contracts for target-lowering oracles."""

from __future__ import annotations

import pytest


from scripts.external_baselines.no_cutoff_target_lowering.report import (
    CORRUPTION_CONTROL_IDS,
)


def test_independent_oracles_do_not_import_target_owners_or_micro_owners() -> None:
    import ast
    import importlib.util
    import inspect

    from scripts.external_baselines.no_cutoff_target_lowering import (
        independent_pair_oracle,
        independent_source_oracle,
        independent_target_oracle,
        independent_tn_oracle,
    )

    forbidden_modules = {
        "scripts.external_baselines.no_cutoff_minimal_exact_owners",
        "scripts.external_baselines.no_cutoff_target_lowering.add_relations",
        "scripts.external_baselines.no_cutoff_target_lowering.model",
        "scripts.external_baselines.no_cutoff_target_lowering.neutral",
        "scripts.external_baselines.no_cutoff_target_lowering.pair",
        "scripts.external_baselines.no_cutoff_target_lowering.tn",
    }
    def imported_modules(source: str, *, package: str) -> set[str]:
        tree = ast.parse(source)
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                relative = "." * node.level + (node.module or "")
                imports.add(
                    importlib.util.resolve_name(relative, package)
                    if node.level
                    else relative
                )
        return imports

    package = "scripts.external_baselines.no_cutoff_target_lowering"
    # Regression guard: AST's raw ``node.module`` for ``from .pair`` is only
    # ``pair``.  Resolve the relative level before comparing absolute names.
    assert (
        "scripts.external_baselines.no_cutoff_target_lowering.pair"
        in imported_modules("from .pair import owner", package=package)
    )

    for module in (
        independent_pair_oracle,
        independent_source_oracle,
        independent_target_oracle,
        independent_tn_oracle,
    ):
        imports = imported_modules(
            inspect.getsource(module), package=module.__package__
        )
        assert forbidden_modules.isdisjoint(imports)


def test_pair_add_and_tn_strict_reload_reproduce_frozen_identity() -> None:
    from copy import deepcopy

    import pytest

    from scripts.external_baselines.no_cutoff_target_lowering.add_relations import (
        build_dynamic_add_relation_program,
        validate_dynamic_add_relation_program,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.model import sha256_json
    from scripts.external_baselines.no_cutoff_target_lowering.neutral import (
        lower_frozen_declared_error_record,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.pair import (
        build_exact_pair_transition_program,
        validate_exact_pair_transition_program,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.tn import (
        build_retained_boundary_factor_network,
        validate_retained_boundary_factor_network,
    )

    neutral = lower_frozen_declared_error_record(distance=3, rounds=1)
    pair = build_exact_pair_transition_program(neutral)
    add = build_dynamic_add_relation_program(pair, neutral=neutral)
    tn = build_retained_boundary_factor_network(neutral)

    assert validate_exact_pair_transition_program(
        pair.to_data(), neutral=neutral
    ).sha256 == pair.sha256
    assert validate_dynamic_add_relation_program(
        add.to_data(), pair=pair, neutral=neutral
    ).sha256 == add.sha256
    assert validate_retained_boundary_factor_network(
        tn.to_data(), neutral=neutral
    ).sha256 == tn.sha256

    changed_pair = deepcopy(pair.to_data())
    coherent = next(
        kernel
        for kernel in changed_pair["semantic"]["kernels"]
        if kernel["kind"] == "COHERENT_Z"
    )
    coherent["component_rows"][0]["multiplier_by_latent"][0]["coefficient"] = [
        [0, 1],
        [0, 1],
        [0, 1],
        [0, 1],
    ]
    kernel_body = {key: value for key, value in coherent.items() if key != "semantic_sha256"}
    coherent["semantic_sha256"] = sha256_json(kernel_body)
    changed_pair["semantic_sha256"] = sha256_json(changed_pair["semantic"])
    with pytest.raises(ValueError, match="frozen semantic identity"):
        validate_exact_pair_transition_program(changed_pair, neutral=neutral)

    changed_add = deepcopy(add.to_data())
    changed_add["semantic"]["current_root"] = 0
    changed_add["semantic_sha256"] = sha256_json(changed_add["semantic"])
    with pytest.raises(ValueError, match="semantic schema"):
        validate_dynamic_add_relation_program(
            changed_add, pair=pair, neutral=neutral
        )

    changed_tn = deepcopy(tn.to_data())
    zero = next(
        template
        for template in changed_tn["semantic"]["table_catalog"]
        if template["template_id"] == "ZERO"
    )
    zero["table"].pop()
    changed_tn["semantic_sha256"] = sha256_json(changed_tn["semantic"])
    with pytest.raises(ValueError, match="frozen semantic identity"):
        validate_retained_boundary_factor_network(changed_tn, neutral=neutral)

    changed_float = deepcopy(pair.to_data())
    changed_float["semantic"]["initial_terms"][0]["coefficient"][0] = 0.5
    changed_float["semantic_sha256"] = sha256_json(changed_float["semantic"])
    with pytest.raises(TypeError, match="floating value"):
        validate_exact_pair_transition_program(changed_float, neutral=neutral)


def test_c1_c4_coset_products_and_idempotence_match_independently() -> None:
    from scripts.external_baselines.no_cutoff_target_lowering.independent_target_oracle import (
        reconstruct_coset_witness_rows,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.pair import (
        build_coset_witness_rows,
    )

    expected_counts = {"C1": 8, "C2": 8, "C3": 64, "C4": 512}
    for witness_id, row_count in expected_counts.items():
        for side in ("ket", "bra"):
            owner = build_coset_witness_rows(witness_id, side=side)
            independent = reconstruct_coset_witness_rows(witness_id, side=side)
            assert owner == independent
            assert len(owner) == row_count
            assert all(row["first_reduction"] == row["second_reduction"] for row in owner)


def test_persistent_sign_audit_binds_neutral_pair_and_tn_occurrences() -> None:
    from scripts.external_baselines.no_cutoff_target_lowering.independent_target_oracle import (
        audit_persistent_sign_lowering,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.neutral import (
        lower_frozen_declared_error_record,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.pair import (
        build_exact_pair_transition_program,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.tn import (
        build_retained_boundary_factor_network,
    )

    neutral = lower_frozen_declared_error_record(distance=3, rounds=1)
    pair = build_exact_pair_transition_program(neutral)
    tn = build_retained_boundary_factor_network(neutral)

    receipt = audit_persistent_sign_lowering(
        neutral.to_data()["semantic"],
        pair.to_data()["semantic"],
        tn.to_data()["semantic"],
    )

    assert receipt["status"] == "PASS"
    assert receipt["coherent_occurrence_count"] == 56
    assert len(receipt["occurrences"]) == 56
    assert receipt["occurrences"][0]["previous_sign"] == "sign:z:0"
    assert receipt["occurrences"][-1]["next_sign"] == "sign:z:56"
    assert receipt["receipt_sha256"]


def test_persistent_sign_audit_rejects_resampled_neutral_declaration() -> None:
    from copy import deepcopy

    from scripts.external_baselines.no_cutoff_target_lowering.independent_target_oracle import (
        audit_persistent_sign_lowering,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.neutral import (
        lower_frozen_declared_error_record,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.pair import (
        build_exact_pair_transition_program,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.tn import (
        build_retained_boundary_factor_network,
    )

    neutral = lower_frozen_declared_error_record(distance=3, rounds=1)
    pair = build_exact_pair_transition_program(neutral)
    tn = build_retained_boundary_factor_network(neutral)
    changed = deepcopy(neutral.to_data()["semantic"])
    changed["process"]["latent"]["transition"] = (
        "resample_independently_at_each_occurrence"
    )

    with pytest.raises(
        ValueError, match="persistent neutral latent declaration"
    ) as caught:
        audit_persistent_sign_lowering(
            changed,
            pair.to_data()["semantic"],
            tn.to_data()["semantic"],
        )
    assert caught.value.subchecks == {
        "neutral_process": "FAIL",
        "pair_latent": "PASS",
        "tn_sign_chain": "PASS",
    }


def test_persistent_sign_audit_rejects_iid_half_per_coherent_occurrence() -> None:
    from copy import deepcopy

    from scripts.external_baselines.no_cutoff_target_lowering.independent_target_oracle import (
        audit_persistent_sign_lowering,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.neutral import (
        lower_frozen_declared_error_record,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.pair import (
        build_exact_pair_transition_program,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.tn import (
        build_retained_boundary_factor_network,
    )

    neutral = lower_frozen_declared_error_record(distance=3, rounds=1)
    pair = build_exact_pair_transition_program(neutral)
    changed = deepcopy(
        build_retained_boundary_factor_network(neutral).to_data()["semantic"]
    )
    for factor in changed["factors"]:
        if factor["template_id"] == "SIGN_EQ":
            factor["template_id"] = "HALF"
            factor["shape"] = [2]
            factor["scope"] = [factor["scope"][1]]

    with pytest.raises(ValueError, match="exactly one HALF prior") as caught:
        audit_persistent_sign_lowering(
            neutral.to_data()["semantic"],
            pair.to_data()["semantic"],
            changed,
        )
    assert caught.value.subchecks == {
        "neutral_process": "PASS",
        "pair_latent": "PASS",
        "tn_sign_chain": "FAIL",
    }


@pytest.mark.parametrize("surface", ("initial", "kernel", "codec"))
def test_persistent_sign_audit_rejects_missing_pair_latent_binding(
    surface: str,
) -> None:
    from copy import deepcopy

    from scripts.external_baselines.no_cutoff_target_lowering.independent_target_oracle import (
        audit_persistent_sign_lowering,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.neutral import (
        lower_frozen_declared_error_record,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.pair import (
        build_exact_pair_transition_program,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.tn import (
        build_retained_boundary_factor_network,
    )

    neutral = lower_frozen_declared_error_record(distance=3, rounds=1)
    changed = deepcopy(
        build_exact_pair_transition_program(neutral).to_data()["semantic"]
    )
    tn = build_retained_boundary_factor_network(neutral)
    if surface == "initial":
        changed["initial_terms"][0].pop("latent_m")
    elif surface == "kernel":
        changed["kernels"][0]["component_rows"][0][
            "multiplier_by_latent"
        ][0].pop("latent_m")
    else:
        changed["checkpoints"][0]["codec_fields"].remove("latent_m")

    with pytest.raises(ValueError, match="pair_latent") as caught:
        audit_persistent_sign_lowering(
            neutral.to_data()["semantic"],
            changed,
            tn.to_data()["semantic"],
        )
    assert caught.value.subchecks["neutral_process"] == "PASS"
    assert caught.value.subchecks["pair_latent"] == "FAIL"


@pytest.mark.parametrize("control_id", CORRUPTION_CONTROL_IDS, ids=CORRUPTION_CONTROL_IDS)
def test_registered_corruption_control_trips(control_id: str) -> None:
    from scripts.external_baselines.no_cutoff_target_lowering.report import (
        run_corruption_control,
    )

    receipt = run_corruption_control(control_id)
    assert receipt["control_id"] == control_id
    assert receipt["status"] == "TRIPPED"
    assert receipt["expected_exception"] == receipt["observed_exception"]
    assert receipt["receipt_sha256"]
