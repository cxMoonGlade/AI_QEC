from __future__ import annotations

"""Public noise API for the simulator frontend.

This module is the user-facing entrypoint for Stim-representable frontend noise.
It deliberately exposes only Pauli/depolarizing projections that can be carried
by `.stim` / `.dem` artifacts. Leakage, analog joint-Lindbladian coupling, and
shared-source non-Markovian truth are separate backend/sidecar concerns, not
Stim noise rules.
"""

from .noise_spec import (
    FrontendNoiseSpec,
    NoiseBuilder,
    StimNoiseRule,
    StimPauliNoiseSpec,
    TargetedStimNoiseSpec,
    apply_stim_pauli_noise,
)


def no_noise() -> None:
    """Return the sentinel for no simulator-added frontend noise."""

    return None


def depolarizing_noise(
    *,
    after_1q: float = 0.0,
    after_2q: float = 0.0,
    before_measure_flip: float = 0.0,
) -> StimPauliNoiseSpec:
    """Build global Stim Pauli/depolarizing frontend noise.

    This is a convenience wrapper around :class:`StimPauliNoiseSpec` using short
    user-facing names. It inserts `DEPOLARIZE1`, `DEPOLARIZE2`, and Z-basis
    measurement `X_ERROR` only.
    """

    return StimPauliNoiseSpec(
        after_1q_depolarization=after_1q,
        after_2q_depolarization=after_2q,
        before_measure_flip=before_measure_flip,
    )


def targeted_noise() -> NoiseBuilder:
    """Start an ordered targeted Stim/Pauli noise builder."""

    return NoiseBuilder()


class Noise:
    """Namespace-style facade for common frontend noise construction.

    Example:

    ```python
    noise = (
        Noise.targeted()
        .after_gate_type("CZ", "DEPOLARIZE", 0.01)
        .during_idle("DEPOLARIZE", 0.001, targets=range(12))
        .before_measurement("X_ERROR", 0.02)
        .build()
    )
    ```
    """

    none = staticmethod(no_noise)
    depolarizing = staticmethod(depolarizing_noise)
    pauli = staticmethod(depolarizing_noise)
    targeted = staticmethod(targeted_noise)


__all__ = [
    "FrontendNoiseSpec",
    "Noise",
    "NoiseBuilder",
    "StimNoiseRule",
    "StimPauliNoiseSpec",
    "TargetedStimNoiseSpec",
    "apply_stim_pauli_noise",
    "depolarizing_noise",
    "no_noise",
    "targeted_noise",
]
