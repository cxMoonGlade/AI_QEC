from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from error_coupling_simulator.frontend.ququart_transport import (
    index_from_ququart_string,
    load_ququart_transport_kraus,
    ququart_string_from_index,
    simulate_ququart_transport_smoke,
)

torch = pytest.importorskip("torch", reason="ququart transport backend requires torch")
requires_cuda = pytest.mark.skipif(not torch.cuda.is_available(), reason="QuquartDM transport backend is GPU-only")
TRANSPORT_KRAUS_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "outputs"
    / "teacher_prereg"
    / "qutip_cz_leakage_kraus.npz"
)
requires_transport_npz = pytest.mark.skipif(
    not TRANSPORT_KRAUS_FIXTURE.is_file(),
    reason="QuTiP-derived ququart transport Kraus artifact is missing",
)


def test_ququart_index_convention_is_engine_msf_order():
    assert index_from_ququart_string("00") == 0
    assert index_from_ququart_string("10") == 4
    assert index_from_ququart_string("01") == 1
    assert index_from_ququart_string("12") == 6
    assert index_from_ququart_string("30") == 12
    assert ququart_string_from_index(12, 2) == "30"


def test_ququart_transport_requires_explicit_external_kraus_path():
    with pytest.raises(TypeError, match="kraus_path"):
        simulate_ququart_transport_smoke(device="cpu")

    with pytest.raises(TypeError, match="kraus_path"):
        load_ququart_transport_kraus(device="cpu")


def test_ququart_transport_loader_reports_external_npz_contract(tmp_path):
    missing = tmp_path / "not-created.npz"
    with pytest.raises(
        FileNotFoundError,
        match=r"explicit external.*NPZ.*kraus_ququart.*\(rank, 16, 16\)",
    ):
        load_ququart_transport_kraus(missing, device="cpu")


def test_ququart_transport_loader_accepts_contract_fixture_on_cpu(tmp_path):
    path = tmp_path / "kraus.npz"
    np.savez(
        path,
        kraus_ququart=np.eye(16, dtype=np.complex128)[None, :, :],
        meta_note=np.asarray("unit fixture"),
    )

    kraus, meta = load_ququart_transport_kraus(path, device="cpu")

    assert tuple(kraus.shape) == (1, 16, 16)
    assert kraus.dtype == torch.complex128
    assert kraus.device.type == "cpu"
    assert meta == {
        "kraus_rank": 1,
        "cptp_residual": 0.0,
        "meta_note": "unit fixture",
    }


def test_ququart_transport_loader_rejects_missing_key_and_non_ranked_shape(tmp_path):
    missing_key = tmp_path / "missing-key.npz"
    np.savez(missing_key, other=np.eye(16, dtype=np.complex128))
    with pytest.raises(ValueError, match="required array 'kraus_ququart'"):
        load_ququart_transport_kraus(missing_key, device="cpu")

    wrong_shape = tmp_path / "wrong-shape.npz"
    np.savez(wrong_shape, kraus_ququart=np.eye(16, dtype=np.complex128))
    with pytest.raises(ValueError, match=r"exact shape \(rank, 16, 16\)"):
        load_ququart_transport_kraus(wrong_shape, device="cpu")


@requires_cuda
@requires_transport_npz
def test_ququart_transport_smoke_writes_exact_artifacts(tmp_path):
    result = simulate_ququart_transport_smoke(
        num_ququarts=2,
        initial_levels="12",
        shots=256,
        seed=11,
        kraus_path=TRANSPORT_KRAUS_FIXTURE,
        out_dir=tmp_path / "transport2",
    )

    assert result.artifacts is not None
    assert result.num_ququarts == 2
    assert (
        result.manifest["backend"]
        == "error_coupling_simulator.carrier.exact.qutrit_dm.QuquartDM"
    )
    assert result.manifest["representability"] == "exact_ququart_density_matrix_transport"
    assert result.manifest["mechanism"] == "qutip_cz_ququart_leakage_transport"
    assert result.manifest["decoder"] is None
    assert result.manifest["parameters"]["kraus_rank"] >= 2
    assert result.manifest["parameters"]["cptp_residual"] < 1e-9
    assert result.outcome_probability("30") > 0.05
    assert result.initial_state_probability < 0.95
    assert sum(result.counts.values()) == 256
    assert np.isclose(result.joint_probabilities.sum(), 1.0, atol=1e-12)
    assert result.density_matrix is not None
    assert np.isclose(np.trace(result.density_matrix).real, 1.0, atol=1e-12)
    assert all(
        np.isclose(row["p0"] + row["p1"] + row["p2"] + row["p3"], 1.0, atol=1e-12)
        for row in result.site_populations
    )

    assert result.artifacts.density_matrix is not None
    assert result.artifacts.density_matrix.exists()
    assert result.artifacts.joint_probabilities.exists()
    assert result.artifacts.site_populations.exists()
    assert result.artifacts.measurement_counts.exists()
    assert result.artifacts.theory_prediction.exists()
    assert result.artifacts.manifest.exists()
    forbidden_suffixes = {".stim", ".dem", ".b8"}
    assert not any(path.suffix in forbidden_suffixes for path in result.artifacts.out_dir.iterdir())
    assert not (result.artifacts.out_dir / "decoder_results.json").exists()

    manifest = json.loads(result.artifacts.manifest.read_text())
    assert manifest["artifacts"]["density_matrix"] == "density_matrix.npy"
    assert manifest["noise"]["type"] == "ququart_transport"
    assert manifest["noise"]["kraus_key"] == "kraus_ququart"
    assert manifest["noise"]["source"] == str(TRANSPORT_KRAUS_FIXTURE.resolve())
    assert manifest["noise"]["source_kind"] == "external_user_supplied_npz"
    assert manifest["noise"]["source_contract"] == {
        "format": "npz",
        "required_key": "kraus_ququart",
        "required_shape": ["rank", 16, 16],
        "schema": "error_coupling_simulator.external_ququart_kraus.v1",
    }
    assert np.load(result.artifacts.joint_probabilities).shape == (16,)
