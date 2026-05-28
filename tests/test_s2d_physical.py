from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import yaml

from scope_static.experiments.run_s2d_oracle_separability import run_s2d_oracle_separability
from scope_static.experiments.run_s2d_physical_teacher import run_s2d_physical_teacher
from scope_static.experiments.run_s2d_preflight import run_s2d_preflight
from scope_static.physical.preflight import audit_cudaq_backend
from scope_static.physical.teacher import (
    _counts_to_bit_matrix,
    build_default_oracle_mechanisms,
    build_probe_circuits,
)


def test_s2d_preflight_writes_cudaq_backend_audit(tmp_path: Path) -> None:
    audit = run_s2d_preflight(output_dir=tmp_path / "S2D_PHYS0_preflight")

    assert audit["schema"] == "scope_static_s2d_backend_audit_v2"
    assert audit["backend_policy"]["priority"] == ["cudaq"]
    assert "cudaq" in audit["packages"]
    assert "tiny_cudaq_sample" in audit
    if bool(audit["backend_usable"]):
        assert audit["tiny_cudaq_sample"]["passed"] is True
    assert (tmp_path / "S2D_PHYS0_preflight" / "backend_audit.json").exists()
    assert (tmp_path / "S2D_PHYS0_preflight" / "backend_audit.md").exists()


def test_default_oracle_mechanisms_include_required_labels() -> None:
    labels = [spec.mechanism_id for spec in build_default_oracle_mechanisms()]

    assert {"M0", "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9"} <= set(labels)


def test_probe_circuits_are_internal_visible_schedules() -> None:
    circuits, names = build_probe_circuits({"profile": "phys9_chain", "probe_set": "base", "depth": 3})

    assert names == ["z_basis", "x_measure", "y_measure"]
    assert circuits[0].count_ops()["rzz"] == 8 * 3
    assert circuits[0].count_ops()["measure"] == 9


def test_counts_to_bit_matrix_materializes_grouped_counts_with_numpy_repeat() -> None:
    rows = _counts_to_bit_matrix({"00": 2, "11": 1, "0x2": 2}, shots=5, num_bits=2)

    assert rows.dtype == np.uint8
    assert rows.shape == (5, 2)
    assert rows.tolist() == [[0, 0], [0, 0], [0, 1], [0, 1], [1, 1]]


def test_s2d_teacher_generation_writes_born_local_artifact_when_cuda_available(tmp_path: Path) -> None:
    audit = audit_cudaq_backend(backend="cudaq", require_gpu=True)
    if not bool(audit["backend_usable"]):
        pytest.skip(f"CUDA-Q preflight is not usable here: {audit.get('errors')}")
    torch = pytest.importorskip("torch")
    if not torch.cuda.is_available():
        pytest.skip("local sampled teacher requires torch CUDA")

    config_path = tmp_path / "s2d_phys.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "s2d_physical": {
                    "shots": 64,
                    "num_qubits": 5,
                    "mechanism_set": ["M1", "M2"],
                    "backend": "cudaq",
                    "require_gpu": True,
                    "local_observable_response_model": "born_local",
                    "balanced_min_instances_per_mechanism": 2,
                }
            }
        )
    )
    result = run_s2d_physical_teacher(
        config_path,
        output_dir=tmp_path / "S2D_PHYS1_teacher",
        preflight_dir=tmp_path / "S2D_PHYS0_preflight",
    )

    assert result["local_observable_response_model"] == "born_local"
    assert result["cudaq_backend"]["target"] is not None
    assert result["mechanism_counts"] == {"M1": 2, "M2": 2}
    assert (tmp_path / "S2D_PHYS1_teacher" / "sampling_audit.json").exists()
    observations = np.load(tmp_path / "S2D_PHYS1_teacher" / "observations.npz")
    assert observations["observations"].ndim == 3


def test_s2d_oracle_separability_writes_artifacts(tmp_path: Path) -> None:
    teacher = tmp_path / "S2D_PHYS1_teacher"
    teacher.mkdir()
    records = []
    specs = build_default_oracle_mechanisms({"include_m5": True, "num_qubits": 5})
    for idx, spec in enumerate(specs):
        records.append({"location_id": idx, **spec.audit_dict(), "oracle_label": spec.mechanism_id})
    (teacher / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}))

    out = tmp_path / "S2D_PHYS2_oracle_separability"
    result = run_s2d_oracle_separability(teacher_dir=teacher, output_dir=out)

    assert result["stage"] == "S2D_PHYS2_oracle_separability"
    assert result["ari_nmi_used_for_selection"] is False
    assert result["separability_gate"] in {"identifying", "limited_but_usable", "probe_set_insufficient"}
    assert result["fingerprint_families"]["probe_response"]["source"] == "oracle_channel_probe_responses"
    assert result["fingerprint_families"]["rzz_type_features"]["feature_names"] == [
        "rzz_type1_commuting_fixed_fraction",
        "rzz_type2_two_entry_rotation_fraction",
        "rzz_type3_nonclifford_rotation_strength",
        "rzz_type4_hard_residual_leakage",
    ]
    assert (out / "fingerprints.npy").exists()
    assert (out / "ptm_fingerprints.npy").exists()
    assert (out / "probe_fingerprints.npy").exists()
    assert (out / "rzz_type_features.npy").exists()
    assert np.load(out / "fingerprints.npy").ndim == 2
    assert (out / "metrics.json").exists()
    assert (out / "confusion_matrix.json").exists()
    assert (out / "summary.md").exists()


def test_cudaq_execution_preflight_when_available() -> None:
    audit = audit_cudaq_backend(backend="cudaq", require_gpu=True)
    if not bool(audit["backend_usable"]):
        pytest.skip(f"CUDA-Q preflight is not usable here: {audit.get('errors')}")
    assert audit["cudaq_import_ok"] is True
    assert int(audit["cudaq_gpu_count"]) >= 0
    assert audit["tiny_cudaq_sample"]["passed"] is True
