from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from qec_twin.simulator.ququart_transport import (
    DEFAULT_TRANSPORT_KRAUS_PATH,
    index_from_ququart_string,
    ququart_string_from_index,
    simulate_ququart_transport_smoke,
)

torch = pytest.importorskip("torch", reason="ququart transport backend requires torch")
requires_cuda = pytest.mark.skipif(not torch.cuda.is_available(), reason="QuquartDM transport backend is GPU-only")
requires_transport_npz = pytest.mark.skipif(
    not Path(DEFAULT_TRANSPORT_KRAUS_PATH).is_file(),
    reason="QuTiP-derived ququart transport Kraus artifact is missing",
)


def test_ququart_index_convention_is_engine_msf_order():
    assert index_from_ququart_string("00") == 0
    assert index_from_ququart_string("10") == 4
    assert index_from_ququart_string("01") == 1
    assert index_from_ququart_string("12") == 6
    assert index_from_ququart_string("30") == 12
    assert ququart_string_from_index(12, 2) == "30"


@requires_cuda
@requires_transport_npz
def test_ququart_transport_smoke_writes_exact_artifacts(tmp_path):
    result = simulate_ququart_transport_smoke(
        num_ququarts=2,
        initial_levels="12",
        shots=256,
        seed=11,
        out_dir=tmp_path / "transport2",
    )

    assert result.artifacts is not None
    assert result.num_ququarts == 2
    assert result.manifest["backend"] == "qec_twin.forward.exact.qutrit_dm.QuquartDM"
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
    assert np.load(result.artifacts.joint_probabilities).shape == (16,)
