from __future__ import annotations

import json
from pathlib import Path

from scope_static.backend.mechanism_catalog import MECHANISM_NAMES
from scope_static.learner import (
    HEADS,
    build_batch_protocol,
    gaussian_parameter_schema,
    run_phyc3c_distributional_gaussian_likelihood_head,
)


def test_phyc3c_batch_protocol_distinguishes_single_and_multi_context_modes() -> None:
    labels = ["M6", "M13", "M27"] * 6
    groups = [group for group in range(6) for _ in range(3)]
    class_names = ["M6", "M13", "M27"]

    single = build_batch_protocol(labels, groups, class_names, mode="single_realization", batch_size=1)
    multi = build_batch_protocol(labels, groups, class_names, mode="multi_context_batch", batch_size=3)

    assert all(batch["num_contexts"] == 1 for batch in single)
    assert all(batch["num_contexts"] == 3 for batch in multi)
    assert sum(batch["label_evaluator_only"] == "M13" for batch in multi) == 2
    assert all(set(batch["test_groups"]).isdisjoint(set(batch["train_groups"])) for batch in multi)


def test_phyc3c_gaussian_schema_names_required_heads_without_forbidden_features() -> None:
    schema = gaussian_parameter_schema(["raw__single__prep_0__r_1__meas_Z__P0"], max_pca_components=4)

    assert schema["schema"] == "scope_static_phyc3c_gaussian_parameter_schema_v1"
    for head in HEADS:
        assert head in schema["heads"]
    assert "oracle" not in " ".join(schema["parameters"]).lower()
    assert "N logdet Sigma_m" in schema["likelihood"]


def test_phyc3c_run_writes_artifacts_and_reports_m13_batch_recovery(tmp_path: Path) -> None:
    teacher = tmp_path / "S2D_PHYC1_teacher"
    teacher.mkdir()
    records = []
    for group in range(8):
        records.append(_record("M6", group, epsilon=0.035))
        records.append(_record("M13", group, epsilon=0.023 + 0.018 * group / 7.0))
        records.append(_record("M27", group, epsilon=0.026))
    (teacher / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}))

    output = tmp_path / "PHYC3c"
    result = run_phyc3c_distributional_gaussian_likelihood_head(
        teacher_dir=teacher,
        output_dir=output,
        shots=1000,
        batch_size=4,
        max_pca_components=4,
    )

    assert result["stage"] == "PHYC3c_distributional_gaussian_likelihood_head"
    assert result["batch_protocol_audit"]["multi_context_batch_mode"]["m13_min_contexts"] == 4
    assert result["leakage_guardrail_audit"]["passed"] is True
    assert "m13_recall" in result["multi_context_batch_mode"]["head_results"]["PHYC3c_diagonal_gaussian"]
    assert result["m13_recovery_audit"]["schema"] == "scope_static_phyc3c_m13_recovery_audit_v1"
    for name in [
        "metrics.json",
        "summary.md",
        "gaussian_parameter_schema.json",
        "batch_protocol_audit.json",
        "distributional_ceiling_audit.json",
        "single_realization_metrics.json",
        "multi_context_batch_metrics.json",
        "head_comparison.json",
        "m13_recovery_audit.json",
        "leakage_guardrail_audit.json",
    ]:
        assert (output / name).exists()


def _record(label: str, group: int, *, epsilon: float) -> dict[str, object]:
    params = {"epsilon": float(epsilon)}
    if label == "M13":
        params = {"axis": "rx", "epsilon": float(epsilon), "epsilon_mean": 0.032, "epsilon_span": 0.018}
    return {
        "oracle_label": label,
        "mechanism_id": label,
        "name": MECHANISM_NAMES[label],
        "num_qubits": 1,
        "parameters": params,
        "instruction": "rx" if label in {"M6", "M13"} else "id",
        "qubits": [0],
        "circuit_id": int(group),
        "location_id": int(group),
        "probe_indices": [],
    }
