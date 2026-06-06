from __future__ import annotations

"""Exact multi-round repetition-code forward model (B1 of the CPTP-twin build).

Extends the differentiable density-matrix core
(:mod:`qec_twin.forward.exact.circuit_sim`) to a full QEC *memory*
experiment: mid-circuit ancilla measurement with reset across ``rounds`` rounds,
and the exact trajectory-enumerated joint distribution ``p(s, m)`` over detector
events ``s`` and the logical observable ``m``, computed under arbitrary local
CPTP noise (stochastic Pauli, non-Pauli, and coherent / non-Clifford alike).

This is the smallest real QEC code that is exactly density-matrix simulable
(distance 3 -> 5 qubits) and is the controlled toy for the B feasibility step
(ADR 0006 / 0007 and project memory ``qec-digital-twin-goal``): label-free
calibration via exact observation-NLL, channel-level ``do()`` knobs, and
counterfactual-validity scoring against controlled-teacher ground truth all run
on this forward model.

Convention (bit-flip / Z-basis repetition code, logical ``|0_L>``)
------------------------------------------------------------------
``distance`` data qubits ``0..d-1`` and ``d-1`` ancillas ``d..2d-2``; check
``j`` couples data ``j`` and ``j+1`` through ancilla ``d+j``. Each round applies
the optional local data-noise channel, the CX parity ladder, then measures and
resets the ancillas. After ``rounds`` rounds every data qubit is measured.
Detectors: round-0 ancilla measurements are absolute (compared to the
deterministic ``0`` of the ``|0_L>`` reset), later rounds compare to the previous
round, and a final data-derived syndrome compares to the last ancilla round. The
logical observable is data qubit ``0``. Noiselessly all detectors and the
observable are ``0``, so "no detections, zero logical error" is the exact
no-noise limit.

The detector/observable wiring matches a hand-built stim reference circuit (same
qubits, CX order, noise placement, ``MR``/``M`` order, and ``rec`` offsets), so
the pure-Pauli slice is validated against a stim sampler; non-Pauli and coherent
noise -- which stim cannot represent -- evaluate on the same exact substrate.
"""

from dataclasses import dataclass

import torch

from qec_twin.forward.exact.circuit_sim import (
    apply_channel_local,
    apply_unitary,
    cx,
    measure_parity_enumerate,
    measure_qubit_enumerate,
    pauli_x,
    ry,
    zero_state,
)
from qec_twin.forward.cptp_channel import RDTYPE


def rep_code_qubits(distance: int) -> tuple[list[int], list[int], int]:
    """Physical qubit indices: ``(data, ancilla, n)`` for distance ``d``."""
    d = int(distance)
    data = list(range(d))
    anc = list(range(d, 2 * d - 1))
    return data, anc, 2 * d - 1


@dataclass
class RepCodeForward:
    """Exact enumerated joint distribution of a rep-code memory experiment.

    ``measurement_record`` is ``(B, K)`` recorded bits over the ``B = 2**K``
    trajectories; ``probs`` is the exact ``(B,)`` probability of each trajectory
    (sums to 1). ``detector_events`` is ``(B, num_detectors)`` and ``observable``
    is ``(B,)``, both deterministic functions of the record. Together
    ``(detector_events, observable, probs)`` *is* the joint ``p(s, m)`` (group by
    matching rows to collapse trajectories with the same ``(s, m)``).
    """

    distance: int
    rounds: int
    measurement_record: torch.Tensor
    probs: torch.Tensor
    detector_events: torch.Tensor
    observable: torch.Tensor

    @property
    def num_detectors(self) -> int:
        return self.detector_events.shape[1]

    def total_probability(self) -> torch.Tensor:
        return self.probs.sum()

    def detector_marginals(self) -> torch.Tensor:
        """``P(detector d == 1)`` for each detector ``d`` (shape ``(num_detectors,)``)."""
        return (self.probs[:, None] * self.detector_events).sum(0)

    def observable_marginal(self) -> torch.Tensor:
        """``P(observable == 1)`` -- the raw (pre-decoding) logical-readout rate."""
        return (self.probs * self.observable).sum()

    def no_detection_probability(self) -> torch.Tensor:
        """``P(all detectors == 0)`` -- the exact quiet-syndrome probability."""
        fired = self.detector_events.sum(1)
        return self.probs[fired == 0].sum()


def _detectors_and_observable(
    outcomes: torch.Tensor, distance: int, rounds: int
) -> tuple[torch.Tensor, torch.Tensor]:
    """Map the ``(B, K)`` measurement record to detector events and observable.

    Record layout (time order): ancilla round ``t`` check ``j`` at column
    ``t * (d-1) + j`` for ``t = 0..rounds-1``; final data qubit ``i`` at column
    ``rounds * (d-1) + i``. Detectors are emitted in syndrome-round-major order
    (``t = 0..rounds``, then check ``j``), matching the stim reference.
    """
    d = int(distance)
    nchecks = d - 1
    r = int(rounds)

    def anc(t: int, j: int) -> torch.Tensor:
        return outcomes[:, t * nchecks + j]

    def data(i: int) -> torch.Tensor:
        return outcomes[:, r * nchecks + i]

    dets: list[torch.Tensor] = []
    for t in range(r + 1):
        for j in range(nchecks):
            if t == 0:
                det = anc(0, j)
            elif t < r:
                det = (anc(t, j) + anc(t - 1, j)) % 2
            else:  # final data-derived syndrome vs the last ancilla round
                data_parity = (data(j) + data(j + 1)) % 2
                det = (data_parity + anc(r - 1, j)) % 2
            dets.append(det)
    detector_events = torch.stack(dets, dim=1)
    observable = data(0)
    return detector_events, observable


def _simulate_ancilla(
    distance: int,
    rounds: int,
    *,
    channel_field,
    initial_flips: list[int] | None,
    repeats: int,
    pre_rotation: float,
    device: str | torch.device,
) -> RepCodeForward:
    """Core exact forward (ancilla backend: full ``2**(2d-1)`` data+ancilla register).

    ``channel_field`` is ``None`` or a callable
    ``(round_t, data_index_i) -> (k, 2, 2) Kraus stack | None`` applied to data
    qubit ``i`` at the start of round ``t`` (the per-location storage mechanism;
    a constant callable recovers a shared channel, a learnable one is the B3
    calibration target). ``initial_flips`` applies ``X`` to the listed data-qubit
    indices before round 0 (logical prep / wiring checks).

    Two probe knobs expose coherence (B5): ``repeats`` applies the storage channel
    that many times per round so a coherent rotation accumulates (``RX(k theta)``)
    while a stochastic flip merely compounds -- the scaling discriminates them;
    ``pre_rotation`` applies ``RY(pre_rotation)`` to every data qubit at prep so the
    channel acts on a superposition input, making its coherent (off-diagonal)
    action visible in the Z-basis syndrome. Both preserve the measurement
    structure, so the record -> (s, m) bijection and calibration machinery are
    unchanged."""
    data, anc, n = rep_code_qubits(distance)
    nchecks = int(distance) - 1

    rho = zero_state(n, device=device).unsqueeze(0)  # (1, dim, dim)
    outcomes = torch.zeros((1, 0), dtype=RDTYPE, device=device)

    if initial_flips:
        for q in initial_flips:
            rho = apply_unitary(rho, pauli_x(), [data[q]], n)
    if pre_rotation:
        gate = ry(pre_rotation)
        for q in data:
            rho = apply_unitary(rho, gate, [q], n)

    for t in range(int(rounds)):
        if channel_field is not None:
            for i in range(int(distance)):
                kraus = channel_field(t, i)
                if kraus is not None:
                    for _ in range(int(repeats)):
                        rho = apply_channel_local(rho, kraus, [data[i]], n)
        for j in range(nchecks):
            rho = apply_unitary(rho, cx(), [data[j], anc[j]], n)
            rho = apply_unitary(rho, cx(), [data[j + 1], anc[j]], n)
        for j in range(nchecks):
            rho, outcomes = measure_qubit_enumerate(rho, outcomes, anc[j], n, reset=True)

    for i in range(int(distance)):
        rho, outcomes = measure_qubit_enumerate(rho, outcomes, data[i], n, reset=False)

    probs = torch.diagonal(rho, dim1=-2, dim2=-1).real.sum(-1)  # (B,)
    detector_events, observable = _detectors_and_observable(outcomes, distance, rounds)
    return RepCodeForward(
        distance=int(distance),
        rounds=int(rounds),
        measurement_record=outcomes,
        probs=probs,
        detector_events=detector_events,
        observable=observable,
    )


def _simulate_parity(
    distance: int,
    rounds: int,
    *,
    channel_field,
    initial_flips: list[int] | None,
    repeats: int,
    pre_rotation: float,
    device: str | torch.device,
) -> RepCodeForward:
    """Core exact forward (parity backend: data-only ``2**d`` register, no ancilla).

    Each stabilizer is measured as a direct ``Z_j Z_{j+1}`` parity projection on the
    data register (exact when syndrome extraction is noiseless, i.e. for data-only
    storage / coherent / correlated mechanisms). Produces the identical record
    layout to :func:`_simulate_ancilla`, so detectors, observable, and the whole
    downstream stack are unchanged -- but the register is ``2**d`` instead of
    ``2**(2d-1)``, which is what makes ``d=5`` (and beyond) tractable.
    """
    n = int(distance)
    nchecks = n - 1

    rho = zero_state(n, device=device).unsqueeze(0)  # (1, 2**d, 2**d)
    outcomes = torch.zeros((1, 0), dtype=RDTYPE, device=device)

    if initial_flips:
        for q in initial_flips:
            rho = apply_unitary(rho, pauli_x(), [q], n)
    if pre_rotation:
        gate = ry(pre_rotation)
        for q in range(n):
            rho = apply_unitary(rho, gate, [q], n)

    for t in range(int(rounds)):
        if channel_field is not None:
            for i in range(n):
                kraus = channel_field(t, i)
                if kraus is not None:
                    for _ in range(int(repeats)):
                        rho = apply_channel_local(rho, kraus, [i], n)
        for j in range(nchecks):
            rho, outcomes = measure_parity_enumerate(rho, outcomes, j, j + 1, n)

    for i in range(n):
        rho, outcomes = measure_qubit_enumerate(rho, outcomes, i, n, reset=False)

    probs = torch.diagonal(rho, dim1=-2, dim2=-1).real.sum(-1)  # (B,)
    detector_events, observable = _detectors_and_observable(outcomes, distance, rounds)
    return RepCodeForward(
        distance=int(distance),
        rounds=int(rounds),
        measurement_record=outcomes,
        probs=probs,
        detector_events=detector_events,
        observable=observable,
    )


def _simulate(distance, rounds, *, backend, **kwargs) -> RepCodeForward:
    """Dispatch to the ancilla or parity backend.

    ``backend="auto"`` keeps the validated ancilla register for ``d <= 3`` (the
    frozen small-scale path) and switches to the data-only parity register for
    ``d >= 4`` (where the ancilla register would be intractable). The two are
    exactly equivalent for noiseless syndrome extraction (checked on ``d=3``).
    """
    if backend == "auto":
        backend = "ancilla" if int(distance) <= 3 else "parity"
    if backend == "ancilla":
        return _simulate_ancilla(distance, rounds, **kwargs)
    if backend == "parity":
        return _simulate_parity(distance, rounds, **kwargs)
    raise ValueError(f"unknown backend {backend!r} (expected 'auto', 'ancilla', or 'parity')")


def simulate_rep_code_memory(
    distance: int,
    rounds: int,
    *,
    data_channel: torch.Tensor | None = None,
    channel_field=None,
    initial_flips: list[int] | None = None,
    repeats: int = 1,
    pre_rotation: float = 0.0,
    backend: str = "auto",
    device: str | torch.device = "cpu",
) -> RepCodeForward:
    """Exact-forward a distance-``d`` repetition-code memory experiment.

    Pass exactly one noise spec (or neither for the noiseless limit):
    ``data_channel`` is a single ``(k, 2, 2)`` Kraus stack shared across every
    data qubit and round; ``channel_field`` is a callable
    ``(round_t, data_index_i) -> (k, 2, 2) | None`` for per-location / per-round
    channels (the B3 calibration target). Either may be Pauli, non-Pauli, or
    coherent and may carry leaf parameters for gradients. ``initial_flips``
    deterministically applies ``X`` to the listed data-qubit indices before
    round 0 (``|1_L>`` prep / wiring checks). ``repeats`` and ``pre_rotation`` are
    the B5 coherence-exposing probe knobs (see ``_simulate``). Returns the full
    enumerated joint distribution; cost is ``2**K`` branches with
    ``K = rounds*(d-1) + d`` measurements, so keep ``d`` and ``rounds`` small.
    """
    if data_channel is not None and channel_field is not None:
        raise ValueError("pass data_channel or channel_field, not both")
    field = channel_field
    if data_channel is not None:
        field = lambda t, i: data_channel  # noqa: E731 -- shared-channel shortcut
    return _simulate(
        distance,
        rounds,
        backend=backend,
        channel_field=field,
        initial_flips=initial_flips,
        repeats=repeats,
        pre_rotation=pre_rotation,
        device=device,
    )
