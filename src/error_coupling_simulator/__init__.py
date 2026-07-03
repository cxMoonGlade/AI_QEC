"""error_coupling_simulator — the standalone coupling-error QEC teacher simulator.

A self-contained, independently-releasable package consolidating the coupling-error QEC simulator
that was previously scattered across ``qec_twin`` (tracked) and ``outputs/`` (gitignored scratch).

**Epistemic frame (binding):** this is a SIMULATOR — there is no physical ground truth. A teacher
here is a noise model whose parameters we SPECIFY; oracles (QuTiP, closed forms) are FORMAL
reference computations that catch implementation bugs, never a claim of correspondence to reality.
The product is LER (records -> decoder -> logical-error-rate); channel/record metrics are internal
instruments. See ``docs/error_coupling_simulator_MIGRATION.md``.

**Status: MIGRATION IN PROGRESS (Phase 1).** Only the homeless source/oracle primitives have been
re-homed so far. The public API is not yet frozen; import submodules directly.
"""

__version__ = "0.0.0.dev0"
