from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import torch

from error_coupling_simulator.carrier.exact.qutrit_dm import QutritDM
from error_coupling_simulator.certify.anchors.dm_oracle import DMOracleAnchor
from error_coupling_simulator.certify.types import Regime, Statistic


def _basis_state(level: int) -> torch.Tensor:
    vector = torch.zeros(3, dtype=torch.complex128)
    vector[level] = 1.0
    return torch.outer(vector, vector.conj())


def test_sequential_marginals_include_prior_nonselective_backaction() -> None:
    eng = QutritDM(1, device="cpu")
    eng.rho = _basis_state(0)
    stabs = [{0: "X"}, {0: "Z"}]

    isolated = []
    rho_pre = eng.rho.clone()
    for stab in stabs:
        eng.rho = rho_pre.clone()
        isolated.append(eng.project_stabilizer(stab, 1, 0.5, "A"))

    eng.rho = rho_pre
    joint = eng.syndrome_distribution(stabs, 0.5, "A")
    eng.rho = rho_pre
    sequential = eng.sequential_stabilizer_marginals(stabs, 0.5, "A")

    np.testing.assert_allclose(isolated, [0.5, 0.0], atol=1e-14)
    np.testing.assert_allclose(sequential, [0.5, 0.5], atol=1e-14)
    np.testing.assert_allclose(
        sequential,
        [
            sum(prob for outcome, prob in joint.items() if outcome[0] == 1),
            sum(prob for outcome, prob in joint.items() if outcome[1] == 1),
        ],
        atol=1e-14,
    )
    assert abs(eng.trace() - 1.0) < 1e-14


def test_logical_distribution_supports_biased_leaked_terminal_readout() -> None:
    eng = QutritDM(1, device="cpu")
    eng.set_code(stabilizers=None, logical_z={0: "Z"})
    eng.rho = _basis_state(2)

    np.testing.assert_allclose(eng.logical_distribution(), (0.5, 0.5), atol=1e-14)
    np.testing.assert_allclose(eng.logical_distribution(0.9), (0.1, 0.9), atol=1e-14)


def test_multisite_logical_readout_uses_product_povm_parity() -> None:
    eng = QutritDM(2, device="cpu")
    eng.set_code(stabilizers=None, logical_z={0: "Z", 1: "Z"})
    eng.rho = torch.zeros((9, 9), dtype=torch.complex128)
    eng.rho[8, 8] = 1.0  # |22>

    # Two independently classified leaked sites have odd parity with
    # probability b(1-b) + (1-b)b, not a hard-bit or blanket 1/2 split.
    np.testing.assert_allclose(eng.logical_distribution(0.9), (0.82, 0.18), atol=1e-14)


def test_dm_anchor_routes_detector_marginals_through_sequential_primitive(monkeypatch) -> None:
    import error_coupling_simulator.carrier.exact.qutrit_dm as qdm_module

    calls: dict[str, object] = {}

    class FakeDM:
        def __init__(self, n_data, *, device):
            calls["init"] = (n_data, str(device))

        def set_code(self, **kwargs):
            calls["code"] = kwargs

        def init_logical(self, m):
            calls["m"] = m

        def sequential_stabilizer_marginals(self, stabs, b, arm):
            calls["sequential"] = (stabs, b, arm)
            return (0.2, 0.3)

        def logical_distribution(self, readout_bias=0.5):
            calls["readout_bias"] = readout_bias
            return (0.6, 0.4)

    monkeypatch.setattr(qdm_module, "QutritDM", FakeDM)
    sched = SimpleNamespace(
        n_data=1,
        logical_kind="Z",
        logical={0: "Z"},
        stab_paulis=lambda: [{0: "X"}, {0: "Z"}],
    )

    class Teacher:
        def __init__(self):
            self.sched = sched

        def dm_round_callbacks(self, device):
            return (lambda eng, r: None), (lambda eng, r: None)

    regime = Regime(R=1, n_active=1, n_stab=2, b=0.9, arm="A")
    answer = DMOracleAnchor(device="cpu", card_bytes=1).answer(
        Teacher(), Statistic.DETECTOR_MARG, regime
    )

    np.testing.assert_allclose(answer.value, [0.2, 0.3, 0.4])
    assert calls["readout_bias"] == 0.9
    assert answer.provenance["measurement_semantics"] == "sequential_nonselective_lueders"
    assert answer.provenance["terminal_readout"] == "biased_b_product_povm"
