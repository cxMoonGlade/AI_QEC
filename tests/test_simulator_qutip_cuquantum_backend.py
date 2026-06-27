from __future__ import annotations

import pytest

pytest.importorskip(
    "qutip_cuquantum",
    reason="QUTIP-CUQUANTUM-MISSING (NOT A RELEASE BASIS for this optional backend probe)",
)

from qec_twin.simulator.qutip_cuquantum_backend import (
    MAX_QUTIP_CUQUANTUM_MCSOLVE_PROBE_QUTRITS,
    probe_qutip_cuquantum_local_mcwf,
    qutip_cuquantum_symbolic_collapse_summary,
)


def _cuda_available() -> bool:
    cp = pytest.importorskip(
        "cupy",
        reason="CUPY-MISSING (NOT A RELEASE BASIS for qutip-cuquantum GPU probe)",
    )
    try:
        return int(cp.cuda.runtime.getDeviceCount()) > 0
    except Exception:
        return False


def test_qutip_cuquantum_12q_collapse_product_stays_symbolic():
    summary = qutip_cuquantum_symbolic_collapse_summary(num_qutrits=12, site=0, rate=0.01)

    assert summary.collapse_shape == (3**12, 3**12)
    assert summary.collapse_data_type == "CuOperator"
    assert summary.collapse_terms == 1
    assert summary.collapse_hilbert_dims == (3,) * 12
    assert summary.cdc_shape == (3**12, 3**12)
    assert summary.cdc_data_type == "CuOperator"
    assert summary.cdc_terms == 1
    assert summary.cdc_hilbert_dims == (3,) * 12


def test_qutip_cuquantum_mcsolve_probe_refuses_12q_grover_carrier_role():
    with pytest.raises(ValueError, match="production 12-qutrit Grover uses DenseQutritMcwfBackend"):
        probe_qutip_cuquantum_local_mcwf(num_qutrits=12)


@pytest.mark.skipif(not _cuda_available(), reason="CUDA-MISSING (NOT A RELEASE BASIS for qutip-cuquantum probe)")
def test_qutip_cuquantum_small_local_mcwf_smoke():
    result = probe_qutip_cuquantum_local_mcwf(
        num_qutrits=2,
        ntraj=1,
        rate=0.01,
        t_final=1e-4,
    )

    assert result.num_qutrits == 2
    assert result.ntraj == 1
    assert "CuVern" in result.method
    assert result.end_condition == "ntraj reached"
    if result.final_state_data_type is not None:
        assert result.final_state_shape == (3**2, 1)


def test_qutip_cuquantum_probe_cap_is_intentional():
    assert MAX_QUTIP_CUQUANTUM_MCSOLVE_PROBE_QUTRITS == 4
