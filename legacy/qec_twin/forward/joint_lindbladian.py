"""SHIM — moved to ``error_coupling_simulator.carrier.joint_lindbladian`` (MIGRATION P2, 2026-07-03).

The Axis-1 within-substep joint-Lindbladian assembler (the G2 HEADLINE substrate) now lives in the
standalone ``error_coupling_simulator`` package. This module is a thin, bulletproof re-export so every
existing importer of ``qec_twin.forward.joint_lindbladian`` — src modules, ~14 tests, the G2 gate —
keeps working UNCHANGED until call sites are migrated to the package path (de-shim phase, P7). Do not
add logic here; edit the canonical module in the package.

See ``docs/error_coupling_simulator_MIGRATION.md``.
"""
from error_coupling_simulator.carrier import joint_lindbladian as _m

# Mirror the moved module's ENTIRE namespace (public + underscore helpers like `_composed_superop`,
# `_superop_expm` that the G2 gate imports), excluding dunders. So `from
# qec_twin.forward.joint_lindbladian import <anything>` resolves exactly as before.
globals().update({_k: _v for _k, _v in vars(_m).items() if not _k.startswith("__")})
del _m
