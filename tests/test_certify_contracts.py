"""Focused public-contract regressions for ``error_coupling_simulator.certify``."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from error_coupling_simulator.certify import certify_noise_process
from error_coupling_simulator.certify.anchors.dm_oracle import DMOracleAnchor
from error_coupling_simulator.certify.core import certify_cells
from error_coupling_simulator.certify.types import (
    AnchorValue,
    Capability,
    Exactness,
    Regime,
    Statistic,
)


def _record_signature(regime: Regime) -> int:
    return sum(regime.sites or ()) % 2


class _RecordingProcess:
    def __init__(self) -> None:
        self.emitted_regimes: list[Regime] = []

    @property
    def truth(self) -> dict:
        return {}

    def emit(self, regime: Regime, *, m: int, N: int, seed: int) -> dict:
        self.emitted_regimes.append(regime)
        width = int(regime.R) * int(regime.n_stab or 0)
        return {
            "det": np.full((N, width), _record_signature(regime), dtype=np.uint8),
            "obs": np.zeros(N, dtype=np.uint8),
        }


class _ExactMarginalAnchor:
    name = "exact_marginal"
    independence = "test-only exact construction"

    def answers(self) -> frozenset[Statistic]:
        return frozenset({Statistic.DETECTOR_MARG})

    def capability(self, statistic: Statistic, regime: Regime) -> Capability:
        return Capability(statistic, Exactness.EXACT, True)

    def answer(
        self,
        process,
        statistic: Statistic,
        regime: Regime,
        *,
        N: int | None = None,
        generator=None,
        corrupt=None,
    ) -> AnchorValue:
        width = int(regime.R) * int(regime.n_stab or 0)
        value = np.concatenate(
            [np.full(width, _record_signature(regime), dtype=float), np.zeros(1)]
        )
        return AnchorValue(statistic, regime, value, Exactness.EXACT, 0.0, "a")


@pytest.mark.parametrize(
    "second",
    [
        Regime(R=1, register="subregister", n_active=2, n_stab=2, sites=(0,)),
        Regime(R=1, register="subregister", n_active=2, n_stab=1, sites=(1,)),
    ],
    ids=["n_stab-is-part-of-regime", "sites-are-part-of-regime"],
)
def test_certification_does_not_share_emit_cache_across_distinct_regimes(second: Regime):
    first = Regime(R=1, register="subregister", n_active=2, n_stab=1, sites=(0,))
    process = _RecordingProcess()

    report = certify_cells(
        process,
        [(Statistic.DETECTOR_MARG, first), (Statistic.DETECTOR_MARG, second)],
        [_ExactMarginalAnchor()],
        [],
        N=8,
    )

    assert process.emitted_regimes == [first, second]
    assert len(report.routing) == 2


class _BaseProcessWithoutDefaultAnchorExtensions:
    def __init__(self) -> None:
        self.emit_calls = 0
        stabilizer = SimpleNamespace(paulis={0: "Z"})
        self._sched = SimpleNamespace(
            n_data=1,
            stabilizers=[stabilizer],
            logical={0: "Z"},
            logical_kind="Z",
            stab_paulis=lambda: [{0: "Z"}],
        )

    @property
    def sched(self):
        return self._sched

    @property
    def truth(self) -> dict:
        return {}

    def emit(self, regime: Regime, *, m: int, N: int, seed: int) -> dict:
        self.emit_calls += 1
        return {
            "det": np.zeros((N, int(regime.R) * int(regime.n_stab or 0)), dtype=np.uint8),
            "obs": np.zeros(N, dtype=np.uint8),
        }

    def channels(self):
        return ()


def test_default_facade_rejects_missing_anchor_capabilities_at_its_boundary():
    process = _BaseProcessWithoutDefaultAnchorExtensions()

    with pytest.raises(TypeError) as exc_info:
        certify_noise_process(process, level="smoke", device="cpu", N=8)

    assert str(exc_info.value) == (
        "certify_noise_process capability error: default anchors require callable process "
        "extensions; missing: dm_round_callbacks, emit_clifford_slice"
    )
    assert process.emit_calls == 0


@pytest.mark.parametrize(
    "statistic",
    [Statistic.FULL_JOINT, Statistic.SYNDROME_DIST],
)
def test_dm_anchor_fails_closed_for_r2_joint_distributions(statistic: Statistic):
    anchor = DMOracleAnchor(device="cpu", card_bytes=10**15, safety=1.0)
    regime = Regime(R=2, register="subregister", n_active=1, n_stab=1)

    capability = anchor.capability(statistic, regime)

    assert capability.feasible is False
    assert capability.reason == (
        "R>=2 QutritDM.record_oracle returns moments only; it cannot provide the full joint "
        "required by FULL_JOINT or SYNDROME_DIST"
    )
    assert capability.mem_bytes_estimate is None


@pytest.mark.parametrize(
    "statistic",
    [Statistic.FULL_JOINT, Statistic.SYNDROME_DIST],
)
def test_dm_anchor_rejects_direct_r2_joint_answer_with_contract_error(statistic: Statistic):
    anchor = DMOracleAnchor(device="cpu", card_bytes=10**15, safety=1.0)
    regime = Regime(R=2, register="subregister", n_active=1, n_stab=1)

    with pytest.raises(ValueError) as exc_info:
        anchor.answer(object(), statistic, regime)

    assert str(exc_info.value) == (
        "DMOracleAnchor contract error: R>=2 QutritDM.record_oracle returns moments only; "
        "it cannot provide the full joint required by FULL_JOINT or SYNDROME_DIST"
    )
