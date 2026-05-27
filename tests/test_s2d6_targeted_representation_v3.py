from __future__ import annotations

import numpy as np
import torch

from scope_static.physical.targeted_v3 import evaluate_targeted_v3_methods, typed_feature_manifest
from scope_static.physical.teacher import build_default_oracle_mechanisms


def test_targeted_v3_typed_features_are_learner_visible_and_fix_readout_split() -> None:
    specs = build_default_oracle_mechanisms({"profile": "phys9_multicircuit_setB_balanced"})
    records = [{"location_id": idx, **spec.audit_dict(), "oracle_label": spec.mechanism_id} for idx, spec in enumerate(specs)]
    label_names = sorted({str(record["oracle_label"]) for record in records})
    label_index = {name: idx for idx, name in enumerate(label_names)}
    hidden = torch.tensor([label_index[str(record["oracle_label"])] for record in records], dtype=torch.long)
    observations = _observations(num_probes=9, shots=64, num_qubits=9)
    probe_names = np.asarray([f"c{circuit}:{probe}" for circuit in range(3) for probe in ("z_basis", "x_measure", "y_measure")])
    split_readout_labels = [idx % len(label_names) for idx in range(len(records))]

    result = evaluate_targeted_v3_methods(
        records,
        observations,
        probe_names,
        hidden,
        label_names,
        comparison_labels={
            "physical_local_inverse_probability": split_readout_labels,
            "physical_local_inverse_probability_v2": split_readout_labels,
            "direct_S_alpha_assignment": split_readout_labels,
        },
    )

    manifest = result["feature_manifest"]
    assert manifest["method"] == "physical_local_inverse_probability_v3_typed"
    assert manifest["uses_oracle_labels"] is False
    assert "v3c_physical_local_inverse_probability_v3_typed" in result["labels_by_method"]
    readout = result["readout_split_audit"]["methods"]["v3c_physical_local_inverse_probability_v3_typed"]
    assert readout["M5_split_fixed"] is True
    assert readout["readout_split_count"] == 4
    assert result["type_budgets"]["readout"] == 4
    assert result["type_budgets"]["rzz_edge"] == 4


def test_targeted_v3_manifest_names_expected_blocks() -> None:
    manifest = typed_feature_manifest()

    assert "RZZ locations" in manifest["feature_blocks"]
    assert "readout locations" in manifest["feature_blocks"]
    assert manifest["feature_roles"]["physical_local_inverse_probability_v3_typed"] == "learner_visible"


def _observations(*, num_probes: int, shots: int, num_qubits: int) -> np.ndarray:
    base = np.linspace(0.05, 0.65, int(num_qubits), dtype=np.float64)
    rates = np.stack([(base + 0.03 * idx) % 0.8 for idx in range(int(num_probes))], axis=0)
    rng = np.random.default_rng(23)
    return (rng.random((int(num_probes), int(shots), int(num_qubits))) < rates[:, None, :]).astype(np.uint8)
