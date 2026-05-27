from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import yaml

from scope_static.experiments.run_s2d_oracle_separability import run_s2d_oracle_separability
from scope_static.experiments.run_s2d_physical_teacher import run_s2d_physical_teacher
from scope_static.experiments.run_s2d_preflight import run_s2d_preflight
from scope_static.physical.preflight import audit_aer_backend
from scope_static.physical.teacher import build_default_oracle_mechanisms, resolve_aer_simulator_settings


def test_s2d_preflight_writes_backend_audit(tmp_path: Path) -> None:
    audit = run_s2d_preflight(output_dir=tmp_path / "S2D_PHYS0_preflight")

    assert audit["schema"] == "scope_static_s2d_backend_audit_v1"
    assert audit["backend_policy"]["priority"] == ["qiskit-aer-gpu", "qiskit-aer"]
    assert "qiskit-aer-gpu" in audit["packages"]
    assert "tiny_density_matrix_gpu_simulation" in audit
    if bool(audit["backend_usable"]):
        assert audit["tiny_density_matrix_gpu_simulation"]["passed"] is True
    assert (tmp_path / "S2D_PHYS0_preflight" / "backend_audit.json").exists()
    assert (tmp_path / "S2D_PHYS0_preflight" / "backend_audit.md").exists()


def test_default_oracle_mechanisms_include_required_labels() -> None:
    labels = [spec.mechanism_id for spec in build_default_oracle_mechanisms()]

    assert {"M0", "M1", "M2", "M3", "M4", "M13", "M14", "M15", "M16"} <= set(labels)


def test_aer_simulator_auto_uses_mps_tensor_network_for_phys15() -> None:
    small = resolve_aer_simulator_settings({"profile": "phys9_chain"})
    large = resolve_aer_simulator_settings({"profile": "phys15_chain"})
    larger = resolve_aer_simulator_settings({"profile": "phys20_chain"})

    assert small["method"] == "density_matrix"
    assert small["selection_reason"] == "auto_small_qubit_density_matrix"
    assert large["method"] == "matrix_product_state"
    assert large["device"] == "GPU"
    assert large["options"] == {"matrix_product_state_truncation_threshold": 0.0}
    assert large["selection_reason"] == "auto_large_qubit_tensor_network"
    assert larger["method"] == "matrix_product_state"
    assert larger["num_qubits"] == 20


def test_aer_simulator_allows_explicit_tensor_network_method() -> None:
    settings = resolve_aer_simulator_settings(
        {
            "profile": "phys15_chain",
            "aer_simulation_method": "tensor-network",
        }
    )

    assert settings["method"] == "tensor_network"
    assert settings["selection_reason"] == "explicit_aer_simulation_method"


def test_aer_simulator_options_do_not_duplicate_method_or_device() -> None:
    settings = resolve_aer_simulator_settings(
        {
            "profile": "phys15_chain",
            "aer_simulator_options": {
                "method": "tensor_network",
                "device": "GPU",
                "matrix_product_state_truncation_threshold": 0.0,
                "not_an_aer_option": 1,
            },
        }
    )

    assert settings["method"] == "tensor_network"
    assert settings["device"] == "GPU"
    assert settings["options"] == {"matrix_product_state_truncation_threshold": 0.0}


def test_s2d_teacher_generation_writes_noise_application_audit_when_gpu_available(tmp_path: Path) -> None:
    audit = audit_aer_backend(backend="qiskit_aer_gpu", require_gpu=True, allow_cpu_aer_fallback=False)
    if not bool(audit["backend_usable"]):
        pytest.skip(f"qiskit-aer-gpu preflight is not usable here: {audit.get('errors')}")
    config_path = tmp_path / "s2d_phys.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "s2d_physical": {
                    "shots": 32,
                    "num_qubits": 5,
                    "include_m5": True,
                    "backend": "qiskit_aer_gpu",
                    "require_gpu": True,
                    "allow_cpu_aer_fallback": False,
                }
            }
        )
    )
    result = run_s2d_physical_teacher(
        config_path,
        output_dir=tmp_path / "S2D_PHYS1_teacher",
        preflight_dir=tmp_path / "S2D_PHYS0_preflight",
    )

    assert {"M0", "M1", "M2", "M3", "M4", "M13", "M14", "M15", "M16"} <= set(result["mechanism_counts"])
    noise_audit = json.loads((tmp_path / "S2D_PHYS1_teacher" / "noise_application_audit.json").read_text())
    assert noise_audit["schema"] == "scope_static_s2d_noise_application_audit_v1"
    assert noise_audit["uses_oracle_labels_for_training"] is False
    assert noise_audit["uses_oracle_labels_for_selection"] is False
    assert {record["oracle_label"] for record in noise_audit["records"]} >= {"M0", "M1", "M2", "M3", "M4", "M13", "M14", "M15", "M16"}
    assert all(record["qiskit_application_api"] == "add_readout_error" for record in noise_audit["records"] if record["oracle_label"] in {"M13", "M14", "M15", "M16"})
    assert all(record["qiskit_application_api"] == "add_quantum_error" for record in noise_audit["records"] if record["oracle_label"] == "M4")
    non_clifford = json.loads((tmp_path / "S2D_PHYS1_teacher" / "non_clifford_audit.json").read_text())
    assert non_clifford["schema"] == "scope_static_s2d_non_clifford_audit_v1"
    assert non_clifford["non_clifford_teacher"] is True
    assert any(record["gate"] == "rzz" and record["source"] == "oracle_noise" for record in non_clifford["non_clifford_sources"])
    assert any(record["gate"] == "rzz" and record["source"] == "ideal_probe_circuit" for record in non_clifford["non_clifford_sources"])
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


def test_aer_gpu_execution_preflight_when_available() -> None:
    audit = audit_aer_backend(backend="qiskit_aer_gpu", require_gpu=True, allow_cpu_aer_fallback=False)
    if not bool(audit["backend_usable"]):
        pytest.skip(f"qiskit-aer-gpu preflight is not usable here: {audit.get('errors')}")
    assert audit["gpu_simulator_constructed"] is True
    assert audit["simulator_device"] == "GPU"
