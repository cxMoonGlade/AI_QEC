"""Axis-2 classical memory sources and their mechanism-parameter fan-out.

``process`` owns replayable cross-cycle timelines, including the finite-RTN
``OneOverFDriftSource`` construction and matched-marginal controls. ``coupling``
owns the explicit ``Theta(z_t)`` map from one source draw to the same-cycle
Axis-1 mechanism parameters. The complete emitted-record service is
``error_coupling_simulator.noise_processes.CoupledCycleNoiseProcess``.

Quantum-bath divisibility witnesses are a separate research surface; they are
not silently used to label this classical stochastic construction.
"""

from .coupling import *  # noqa: F403 - the submodule's explicit __all__ is the contract
from .coupling import __all__ as _coupling_all
from .process import *  # noqa: F403 - the submodule's explicit __all__ is the contract
from .process import __all__ as _process_all

__all__ = sorted(set(_process_all) | set(_coupling_all))

del _coupling_all, _process_all
