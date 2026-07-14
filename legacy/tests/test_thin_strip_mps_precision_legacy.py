"""Explicit legacy-only gate for the retired thin-strip MPS carrier.

This is intentionally outside pytest's active ``tests/`` collection. The current
simulator precision contract belongs to ``error_coupling_simulator.carrier.within_cycle``;
the old ``MpsLeakageForward`` remains runnable only in the retained legacy environment.
"""

from __future__ import annotations

import pytest


def test_retained_mps_backend_rejects_c64_instead_of_mislabeling_header() -> None:
    from error_coupling_simulator.carrier.within_cycle import RunSpec
    from qec_twin.forward.scalable.mps_forward import MpsLeakageForward

    spec = RunSpec(
        circuit_path="unused.stim",
        run_purpose="optimization",
        dtype="c64",
    )
    backend = MpsLeakageForward("cpu")
    with pytest.raises(ValueError, match="complex128 only.*FusedWithinCycleSampler"):
        backend.sample(spec)
