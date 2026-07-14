from __future__ import annotations

import json

import numpy as np
import pytest

from qec_twin.simulator.qutrit_leakage import (
    index_from_qutrit_string,
    qutrit_string_from_index,
    simulate_qutrit_wg_leakage,
)

torch = pytest.importorskip("torch", reason="qutrit leakage backend requires torch")
requires_cuda = pytest.mark.skipif(not torch.cuda.is_available(), reason="QutritDM leakage backend is GPU-only")


def test_qutrit_index_convention_is_engine_msf_order():
    assert index_from_qutrit_string("000") == 0
    assert index_from_qutrit_string("100") == 9
    assert index_from_qutrit_string("010") == 3
    assert index_from_qutrit_string("001") == 1
    assert index_from_qutrit_string("212") == 23
    assert qutrit_string_from_index(23, 3) == "212"


@requires_cuda
def test_qutrit_wg_leakage_default_writes_exact_artifacts(tmp_path):
    result = simulate_qutrit_wg_leakage(
        num_qutrits=3,
        initial_levels="111",
        cycles=1,
        shots=256,
        seed=5,
        out_dir=tmp_path / "leakage3",
    )

    assert result.artifacts is not None
    assert result.num_qutrits == 3
    assert result.manifest["backend"] == (
        "error_coupling_simulator.carrier.exact.qutrit_dm.QutritDM"
    )
    assert result.manifest["representability"] == "exact_qutrit_density_matrix_leakage"
    assert result.manifest["mechanism"] == "wood_gambetta_qutrit_leakage"
    assert result.manifest["decoder"] is None
    assert result.manifest["parameters"]["WG_L1"] > 0.0
    assert result.manifest["parameters"]["C_L"] > 0.0
    assert result.total_leaked_population > 0.005
    assert result.initial_state_probability < 1.0
    assert sum(result.counts.values()) == 256
    assert np.isclose(result.joint_probabilities.sum(), 1.0, atol=1e-12)
    assert result.density_matrix is not None
    assert np.isclose(np.trace(result.density_matrix).real, 1.0, atol=1e-12)
    assert all(np.isclose(row["p0"] + row["p1"] + row["p2"], 1.0, atol=1e-12) for row in result.site_populations)

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
    assert manifest["noise"]["type"] == "qutrit_leakage"
    assert np.load(result.artifacts.joint_probabilities).shape == (27,)


@requires_cuda
def test_qutrit_zero_channel_control_has_no_leakage():
    result = simulate_qutrit_wg_leakage(
        num_qutrits=2,
        initial_levels="11",
        cycles=3,
        shots=0,
        theta=0.0,
        g_seep=0.0,
        g_heat=0.0,
    )

    assert result.counts == {}
    assert result.total_leaked_population == pytest.approx(0.0, abs=1e-12)
    assert result.joint_probabilities[index_from_qutrit_string("11")] == pytest.approx(1.0, abs=1e-12)
    assert result.manifest["parameters"]["C_L"] == pytest.approx(0.0, abs=1e-12)
