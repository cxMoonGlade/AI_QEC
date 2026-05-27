from __future__ import annotations

import numpy as np

from scope_static.physical.rzz_observability_ceiling import (
    FeatureBlock,
    audit_labels_schema,
    evaluate_ceiling_feature_blocks,
    features_schema,
    grouped_fold_audit,
    leakage_guardrail_audit,
)


def test_grouped_logistic_ceiling_detects_transferable_signal() -> None:
    labels, groups, blocks = _separable_blocks()

    result = evaluate_ceiling_feature_blocks(
        blocks,
        labels,
        groups,
        permutation_repeats=8,
        seed=7,
    )

    primary = result["feature_block_results"]["v3c_plus_active_all"]["overall"]
    controls = result["controls"]
    assert primary["macro_F1"] >= 0.80
    assert primary["balanced_accuracy"] >= 0.80
    assert controls["real_minus_scrambled_balanced_accuracy"] >= 0.25
    assert controls["real_minus_permutation_balanced_accuracy"] >= 0.25
    assert result["run_success"]["passed"] is True
    assert result["secondary_nonlinear_diagnostics"]["role"] == "secondary_diagnostic_not_used_for_pass_fail"


def test_grouped_fold_audit_uses_leave_one_circuit_id_out() -> None:
    audit = grouped_fold_audit([0, 0, 1, 1, 2, 2])

    assert audit["splitter"] == "LeaveOneGroupOut"
    assert audit["group_key"] == "circuit_id"
    assert audit["num_folds"] == 3
    assert audit["all_test_groups_disjoint_from_train"] is True


def test_leakage_guardrail_rejects_oracle_feature_columns() -> None:
    labels, groups, blocks = _separable_blocks()
    bad = dict(blocks)
    bad["bad"] = FeatureBlock(
        "bad",
        np.zeros((len(labels), 1), dtype=np.float64),
        ["oracle_label_encoded"],
        ["bad_source"],
    )
    schema = audit_labels_schema(labels, groups, _records(labels, groups))
    fold_audit = grouped_fold_audit(groups)
    guard = leakage_guardrail_audit(bad, schema, fold_audit)

    assert guard["passed"] is False
    assert guard["checks"]["oracle_label_not_in_feature_columns"] is False


def test_feature_and_label_schemas_are_separate() -> None:
    labels, groups, blocks = _separable_blocks()
    feature_schema = features_schema(blocks, source_root="/tmp/source")
    label_schema = audit_labels_schema(labels, groups, _records(labels, groups))

    assert feature_schema["no_new_teacher_sampling"] is True
    assert feature_schema["feature_blocks"]["v3c_plus_active_all"]["uses_oracle_label"] is False
    assert label_schema["labels_role"] == "audit_only_supervised_targets"
    assert label_schema["forbidden_as_phys3_features"] is True


def _separable_blocks() -> tuple[list[str], list[int], dict[str, FeatureBlock]]:
    class_order = ["M1", "M7", "M8"]
    labels = class_order * 3
    groups = [0, 0, 0, 1, 1, 1, 2, 2, 2]
    y = np.asarray([class_order.index(label) for label in labels], dtype=np.int64)
    v3c = np.zeros((len(labels), 2), dtype=np.float64)
    active = np.eye(3, dtype=np.float64)[y]
    scrambled = np.zeros_like(active)
    blocks = {
        "baseline_v3c_visible": FeatureBlock("baseline_v3c_visible", v3c, ["v3c_0", "v3c_1"], ["base"], explanatory=True),
        "active_all": FeatureBlock("active_all", active, ["active_0", "active_1", "active_2"], ["active"], explanatory=True),
        "scrambled_active_all": FeatureBlock("scrambled_active_all", scrambled, ["scr_0", "scr_1", "scr_2"], ["scrambled"], control=True),
        "v3c_plus_active_all": FeatureBlock(
            "v3c_plus_active_all",
            np.concatenate([v3c, active], axis=1),
            ["v3c_0", "v3c_1", "active_0", "active_1", "active_2"],
            ["base", "active"],
            primary=True,
        ),
        "v3c_plus_scrambled_active_all": FeatureBlock(
            "v3c_plus_scrambled_active_all",
            np.concatenate([v3c, scrambled], axis=1),
            ["v3c_0", "v3c_1", "scr_0", "scr_1", "scr_2"],
            ["base", "scrambled"],
            control=True,
        ),
        "active_residualized_against_v3c": FeatureBlock(
            "active_residualized_against_v3c",
            active,
            ["active_0", "active_1", "active_2"],
            ["active"],
            residualize_against=v3c,
            explanatory=True,
        ),
        "scrambled_active_residualized_against_v3c": FeatureBlock(
            "scrambled_active_residualized_against_v3c",
            scrambled,
            ["scr_0", "scr_1", "scr_2"],
            ["scrambled"],
            residualize_against=v3c,
            control=True,
        ),
    }
    return labels, groups, blocks


def _records(labels: list[str], groups: list[int]) -> list[dict[str, object]]:
    return [
        {
            "location_id": idx,
            "oracle_label": label,
            "circuit_id": group,
            "qubits": [idx % 4, idx % 4 + 1],
        }
        for idx, (label, group) in enumerate(zip(labels, groups))
    ]
