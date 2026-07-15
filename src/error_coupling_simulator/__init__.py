"""Standalone specified-noise simulator for QEC error mechanisms.

The package applies declared coupling, leakage, and memoryful noise processes to a QEC circuit and
emits a multi-time syndrome record. It consolidates the simulator implementation behind an
independently releasable package boundary.

There is no physical ground truth implied by a specified noise process. QuTiP, closed-form, and
exact-density-matrix references are formal implementation checks, not evidence of correspondence to
hardware. The emitted record is the product; LER and channel/record metrics are instruments on that
record. Evaluator-only process truth is isolated from emitted artifacts.

The public API and separate-distribution boundary are not yet frozen. The binding object and claim
contract is ``docs/SIMULATOR.md``; current migration status is recorded in ``CLAUDE.md``.
"""

from importlib.metadata import PackageNotFoundError, version


try:
    __version__ = version("error-coupling-simulator")
except PackageNotFoundError:  # source tree before installation
    __version__ = "0+uninstalled"
