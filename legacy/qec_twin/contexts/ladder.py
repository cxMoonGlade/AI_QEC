from __future__ import annotations

"""B2: the probe-richness ladder ``C_cal(r)`` and held-out eval on the rep-code toy.

A *context* ``c`` is a runnable calibration/eval circuit -- here parameterized by
(distance, rounds, logical-prep basis); richer levels (basis-rotated /
coherent-sensitive probes) extend it later. ADR 0003 fixes the ladder structure
``r = 0..4`` (the same local channel slot reused across contexts so context
diversity breaks the observational alias quotient); this module instantiates it
for the repetition code and provides a held-out eval context disjoint from the
calibration set, so counterfactual knobs are always validated cross-context.

Current build: ``r = 0`` (single ``|0_L>`` memory) and ``r = 1`` (multiple rounds
+ both logical bases), all Z-basis. Per the chosen sequencing, the loop is closed
end-to-end (B3 calibration, B4 ``do()``) on ``r = 0, 1`` before the richer
``r = 2..4`` probes are built; :data:`MAX_BUILT_RICHNESS` guards the boundary.
"""

import math
from dataclasses import dataclass

from qec_twin.forward.exact.rep_code import RepCodeForward, simulate_rep_code_memory

MAX_BUILT_RICHNESS = 4

_HALF_PI = math.pi / 2


@dataclass(frozen=True)
class RepCodeContext:
    """A single runnable rep-code context (one entry of ``C_cal(r)``).

    ``logical`` selects the prepared logical state (``0`` -> ``|0_L>``, ``1`` ->
    ``|1_L>``). ``repeats`` applies the storage channel that many times per round
    and ``pre_rotation`` applies ``RY(pre_rotation)`` to the data at prep -- the two
    coherence-exposing probe knobs (default ``1`` / ``0.0`` is a plain memory).
    ``richness`` is the ladder level; ``label`` a stable tag. ``key`` identifies
    the circuit (de-duplication and held-out disjointness).
    """

    distance: int
    rounds: int
    logical: int
    richness: int
    label: str
    repeats: int = 1
    pre_rotation: float = 0.0

    @property
    def key(self) -> tuple[int, int, int, int, float]:
        return (self.distance, self.rounds, self.logical, self.repeats, round(self.pre_rotation, 9))

    def initial_flips(self) -> list[int] | None:
        """``X`` on every data qubit prepares ``|1_L>``; ``None`` keeps ``|0_L>``."""
        return list(range(self.distance)) if self.logical else None


def run_context(
    context: RepCodeContext,
    *,
    data_channel=None,
    channel_field=None,
    edge_field=None,
    device: str | object = "cpu",
) -> RepCodeForward:
    """Exact-forward a context under a shared ``data_channel`` or a per-location
    ``channel_field`` (the B3 calibration target), optionally with a non-factorized
    ``edge_field`` (H2 coupling slot). Returns the joint ``p(s, m)``."""
    return simulate_rep_code_memory(
        context.distance,
        context.rounds,
        data_channel=data_channel,
        channel_field=channel_field,
        edge_field=edge_field,
        initial_flips=context.initial_flips(),
        repeats=context.repeats,
        pre_rotation=context.pre_rotation,
        device=device,
    )


def _ctx(
    distance: int,
    rounds: int,
    logical: int,
    richness: int,
    *,
    repeats: int = 1,
    pre_rotation: float = 0.0,
    tag: str = "",
) -> RepCodeContext:
    label = f"r{richness}:R{rounds}-L{logical}" + (f"-{tag}" if tag else "")
    return RepCodeContext(distance, rounds, logical, richness, label, repeats, pre_rotation)


def _level_contexts(richness: int, distance: int) -> list[RepCodeContext]:
    """The *new* contexts introduced at ladder level ``richness`` (cumulative).

    The ladder climbs from Z-basis memory (blind to coherence) to coherence-
    stressing and basis-rotated probes (ADR 0003 ``r=0..4``):
      r0  single ``|0_L>`` memory;
      r1  more rounds + both logical bases (still Z-basis);
      r2  repeated-storage probes (``RX(k theta)`` accumulation -- coherence stress);
      r3  basis-rotated probes (``RY(pi/2)`` prep -- channel acts on a superposition);
      r4  combined stress + rotation (maximally coherence-sensitive).
    """
    if richness == 0:
        return [_ctx(distance, 2, 0, 0)]
    if richness == 1:
        return [
            _ctx(distance, 1, 0, 1),
            _ctx(distance, 3, 0, 1),
            _ctx(distance, 1, 1, 1),
            _ctx(distance, 2, 1, 1),
            _ctx(distance, 3, 1, 1),
        ]
    if richness == 2:  # repeated-storage coherence stress (Z-basis)
        return [
            _ctx(distance, 2, 0, 2, repeats=2, tag="k2"),
            _ctx(distance, 3, 0, 2, repeats=2, tag="k2"),
        ]
    if richness == 3:  # basis-rotated probes: channel acts on a superposition
        return [
            _ctx(distance, 1, 0, 3, pre_rotation=_HALF_PI, tag="ry"),
            _ctx(distance, 2, 0, 3, pre_rotation=_HALF_PI, tag="ry"),
        ]
    if richness == 4:  # combined stress + rotation
        return [
            _ctx(distance, 2, 0, 4, repeats=2, pre_rotation=_HALF_PI, tag="k2ry"),
            _ctx(distance, 2, 0, 4, repeats=3, tag="k3"),
        ]
    raise NotImplementedError(
        f"probe richness r={richness} not built yet (max r={MAX_BUILT_RICHNESS})"
    )


def calibration_contexts(richness: int, *, distance: int = 3) -> list[RepCodeContext]:
    """Cumulative calibration set ``C_cal(r)`` -- levels ``0..richness``.

    The ladder grows monotonically (``C_cal(r-1) ⊂ C_cal(r)``): richer levels add
    more diverse probes without dropping earlier ones.
    """
    if richness > MAX_BUILT_RICHNESS:
        raise NotImplementedError(
            f"probe richness r={richness} not built yet (max r={MAX_BUILT_RICHNESS})"
        )
    contexts: list[RepCodeContext] = []
    for level in range(int(richness) + 1):
        contexts.extend(_level_contexts(level, distance))
    return contexts


def held_out_eval_context(*, distance: int = 3) -> RepCodeContext:
    """A memory context disjoint from every calibration level (cross-context eval).

    Uses a round count (``4``) absent from the calibration ladder so the knob
    validation in B4 always extrapolates beyond the calibrated circuits.
    """
    return RepCodeContext(distance, 4, 0, -1, "eval:R4-L0")


def held_out_sandwich_context(*, distance: int = 3) -> RepCodeContext:
    """The held-out repeated-storage "sandwich" memory eval (H2).

    Same disjoint round count (``4``) as :func:`held_out_eval_context` but with
    ``repeats=2``, so a per-round edge coupling sits INSIDE a storage sandwich
    (visibility = drift x backdrop-coherence between extractions) instead of being
    absorbed by the next extraction (the repeats=1 phi-blind theorem). NOT a new
    calibration rung -- the crosstalk probes are the existing r=2/r=4 levels; the
    phase-sensitive (signed) edge evals are :func:`held_out_exotic_contexts`.
    """
    return RepCodeContext(distance, 4, 0, -1, "eval:R4-k2", repeats=2)


def held_out_exotic_contexts(*, distance: int = 3) -> list[RepCodeContext]:
    """The held-out coherent / phase-sensitive "exotics" for the D2 protocol.

    The finance "exotic" priced from low-`r` "vanilla" calibration: basis-rotated
    (``RY(pi/2)`` prep) and coherence-stressed (``repeats``) probes at a round
    count (``4``) absent from the calibration ladder, so every level
    ``C_cal(k)`` must *extrapolate* to them. Their observable distribution is
    maximally sensitive to the coherent drift a Z-basis fit may Pauli-shadow, so
    a low-`k` twin's worst-case prediction error over this set is where
    Pauli-shadowing shows up out of basis (the D2 headline).
    """
    return [
        RepCodeContext(distance, 4, 0, -1, "exotic:R4-ry", 1, _HALF_PI),
        RepCodeContext(distance, 4, 0, -1, "exotic:R4-ry-k2", 2, _HALF_PI),
        RepCodeContext(distance, 3, 0, -1, "exotic:R3-ry-k2", 2, _HALF_PI),
    ]
