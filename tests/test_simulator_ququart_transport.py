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
_CURRENT_KRAUS_SCHEMA = "error_coupling_simulator.frontend.ququart_transport_kraus.v2"
_TRANSPORT_PROBABILITY = 0.25


def _handwritten_transport_kraus() -> np.ndarray:
    """Two-Kraus random-unitary channel with explicit ``|12> <-> |30>`` transport.

    The two-ququart basis uses ``4*q0 + q1``. Hence ``|12>`` and ``|30>``
    have indices 6 and 12. The construction is independent of the package's
    channel builders and satisfies ``sum_k K_k^dag K_k = I`` by inspection.
    """

    identity = np.eye(16, dtype=np.complex128)
    transport = identity.copy()
    transport[6, 6] = 0.0
    transport[12, 12] = 0.0
    transport[12, 6] = 1.0
    transport[6, 12] = 1.0
    return np.stack(
        (
            np.sqrt(1.0 - _TRANSPORT_PROBABILITY) * identity,
            np.sqrt(_TRANSPORT_PROBABILITY) * transport,
        )
    )


@pytest.fixture
def handwritten_transport_npz(tmp_path) -> Path:
    path = tmp_path / "ququart_transport_kraus_v2.npz"
    np.savez(
        path,
        kraus_ququart=_handwritten_transport_kraus(),
        meta_schema=np.asarray(_CURRENT_KRAUS_SCHEMA),
        meta_fixture=np.asarray("handwritten_random_unitary_12_to_30"),
        meta_transport_probability=np.asarray(_TRANSPORT_PROBABILITY),
    )
    return path


def test_ququart_index_convention_is_engine_msf_order():
    assert index_from_ququart_string("00") == 0
    assert index_from_ququart_string("10") == 4
    assert index_from_ququart_string("01") == 1
    assert index_from_ququart_string("12") == 6
    assert index_from_ququart_string("30") == 12
    assert ququart_string_from_index(12, 2) == "30"


def test_ququart_transport_requires_exactly_one_explicit_channel_source():
    with pytest.raises(TypeError, match="exactly one.*cz_params.*channel.*kraus_path"):
        simulate_ququart_transport_smoke(device="cpu")

    identity = np.eye(16, dtype=np.complex128)[None, :, :]
    with pytest.raises(TypeError, match="exactly one"):
        simulate_ququart_transport_smoke(
            device="cpu", channel=identity, kraus_path="also-set.npz"
        )

    with pytest.raises(TypeError, match="kraus_path"):
        load_ququart_transport_kraus(device="cpu")


def test_ququart_transport_loader_reports_explicit_npz_contract(tmp_path):
    missing = tmp_path / "not-created.npz"
    with pytest.raises(
        FileNotFoundError,
        match=r"explicit.*NPZ.*kraus_ququart.*\(rank, 16, 16\)",
    ):
        load_ququart_transport_kraus(missing, device="cpu")


def test_ququart_transport_loader_accepts_current_schema_fixture_on_cpu(
    handwritten_transport_npz,
):
    kraus, meta = load_ququart_transport_kraus(
        handwritten_transport_npz, device="cpu")

    assert tuple(kraus.shape) == (2, 16, 16)
    assert kraus.dtype == torch.complex128
    assert kraus.device.type == "cpu"
    assert meta["kraus_rank"] == 2
    assert meta["cptp_residual"] < 1e-15
    assert meta["meta_schema"] == _CURRENT_KRAUS_SCHEMA
    assert meta["meta_fixture"] == "handwritten_random_unitary_12_to_30"
    assert meta["meta_transport_probability"] == _TRANSPORT_PROBABILITY


def test_ququart_transport_loader_rejects_missing_key_and_non_ranked_shape(tmp_path):
    missing_key = tmp_path / "missing-key.npz"
    np.savez(missing_key, other=np.eye(16, dtype=np.complex128))
    with pytest.raises(ValueError, match="required array 'kraus_ququart'"):
        load_ququart_transport_kraus(missing_key, device="cpu")

    wrong_shape = tmp_path / "wrong-shape.npz"
    np.savez(wrong_shape, kraus_ququart=np.eye(16, dtype=np.complex128))
    with pytest.raises(ValueError, match=r"exact shape \(rank, 16, 16\)"):
        load_ququart_transport_kraus(wrong_shape, device="cpu")


def test_ququart_transport_runs_from_in_memory_channel_without_external_data():
    identity = np.eye(16, dtype=np.complex128)[None, :, :]
    result = simulate_ququart_transport_smoke(
        num_ququarts=2,
        initial_levels="12",
        shots=8,
        seed=4,
        channel=identity,
        device="cpu",
    )

    assert result.initial_state_probability == pytest.approx(1.0)
    assert result.manifest["noise"]["source_kind"] == "in_memory_kraus_injection"
    assert result.manifest["parameters"]["kraus_rank"] == 1


def test_ququart_transport_derives_channel_from_declared_params(monkeypatch):
    from error_coupling_simulator.mechanisms import cz_leakage

    params = cz_leakage.CZParams()
    seen = {}

    def fake_build(got, *, track_dim):
        seen.update(params=got, track_dim=track_dim)
        return cz_leakage.LeakageChannel(
            arm="ququart",
            track_dim=4,
            kraus=[np.eye(16, dtype=np.complex128)],
            cptp_residual=0.0,
            leaked_population=0.0,
            params=got,
            note="unit identity",
            leaked_from_comp=0.0,
            leaked_from_leaked_max=0.0,
            pop_ge4_max=0.0,
        )

    monkeypatch.setattr(cz_leakage, "build_cz_channel", fake_build)
    result = simulate_ququart_transport_smoke(
        cz_params=params,
        device="cpu",
        shots=0,
    )

    assert seen == {"params": params, "track_dim": 4}
    assert result.manifest["noise"]["source_kind"] == (
        "derived_in_process_from_declared_cz_params"
    )
    assert result.manifest["parameters"]["declared_cz_params"]["t_gate"] == 25.0


@requires_cuda
def test_ququart_transport_smoke_writes_exact_artifacts(
    tmp_path, handwritten_transport_npz,
):
    result = simulate_ququart_transport_smoke(
        num_ququarts=2,
        initial_levels="12",
        shots=256,
        seed=11,
        kraus_path=handwritten_transport_npz,
        device="cuda",
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
    assert result.manifest["parameters"]["kraus_rank"] == 2
    assert result.manifest["parameters"]["cptp_residual"] < 1e-9
    assert result.manifest["parameters"]["meta_schema"] == _CURRENT_KRAUS_SCHEMA
    assert result.outcome_probability("30") == pytest.approx(
        _TRANSPORT_PROBABILITY, abs=1e-12)
    assert result.initial_state_probability == pytest.approx(
        1.0 - _TRANSPORT_PROBABILITY, abs=1e-12)
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
    assert manifest["noise"]["source"] == str(handwritten_transport_npz.resolve())
    assert manifest["noise"]["source_kind"] == "serialized_channel_cache_or_user_injection"
    assert manifest["noise"]["source_contract"] == {
        "format": "npz",
        "required_key": "kraus_ququart",
        "required_shape": ["rank", 16, 16],
        "schema": _CURRENT_KRAUS_SCHEMA,
    }
    assert np.load(result.artifacts.joint_probabilities).shape == (16,)
