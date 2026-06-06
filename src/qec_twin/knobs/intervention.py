from __future__ import annotations

"""B4: channel-level ``do()`` knobs, a frozen decoder, and the ``B_*`` scores.

Interventions are parameterization-independent transforms of a *channel* (a Kraus
stack), not edits to teacher parameters (ADR 0007 / the ``do()`` glossary):

  * Tier 0 -- ``do(E_i -> I)`` (remove a location's noise), unambiguous;
  * Tier 1 -- ``do(E_i -> (1-a) I + a E_i)``, a CPTP-safe weakening (convex mix
    with the identity stays CPTP for any ``a in [0, 1]``). Full generator-scaling
    ``exp(k Log E)`` with amplification waits for the GKSL PhysDec (ADR 0006 A).

The decoder ``D`` is predeclared and frozen: a single MWPM matching built from the
eval circuit's detector error model at a uniform nominal noise (so edge weights
are uniform -- a noise-agnostic minimum-distance decoder). The same ``D`` scores
teacher, twin, base, and every ``do()`` evaluation; no retuning happens inside the
score.

The counterfactual-validity scores compare the twin's *predicted* effect of an
intervention to the teacher's *true* effect, both exact-forwarded to a held-out
eval circuit:

  B_LER = | dLER_teacher - dLER_twin |          (decoder-relevant knob error)
  B_obs = TV( dp_teacher , dp_twin )            (observation-shift error)

with ``dLER = LER(do(E)) - LER(E)`` and ``dp = p_do(s,m) - p_base(s,m)``. Small
``B_*`` means the twin's knobs are trustworthy on that intervention. (On a Pauli
teacher with a Z-basis ladder the identifiable bit-flip action is what both the
joint fit and the ``do()`` depend on, so ``B_*`` is small; the coherent /
non-Clifford slice where the alias quotient makes ``B_*`` large is the B5 study.)
"""

import numpy as np
import torch

from qec_twin.calibration.nll import RepCodeTwin
from qec_twin.contexts.ladder import RepCodeContext, run_context
from qec_twin.knobs.reference import stim_rep_code_circuit
from qec_twin.forward.exact.rep_code import RepCodeForward


# --------------------------------------------------------------------------- #
# Channel-level do() transforms (act on a Kraus stack, return a Kraus stack)    #
# --------------------------------------------------------------------------- #
def do_remove(kraus: torch.Tensor) -> torch.Tensor:
    """``do(E -> I)`` -- replace the channel with the identity (Tier 0)."""
    d = kraus.shape[-1]
    return torch.eye(d, dtype=kraus.dtype, device=kraus.device).unsqueeze(0)


def do_weaken(kraus: torch.Tensor, alpha: float) -> torch.Tensor:
    """``do(E -> (1-a) I + a E)`` -- CPTP-safe weakening (Tier 1, ``a in [0,1]``).

    Kraus of the convex mixture: ``{sqrt(1-a) I} ∪ {sqrt(a) K_e}``.
    """
    a = float(alpha)
    d = kraus.shape[-1]
    eye = torch.eye(d, dtype=kraus.dtype, device=kraus.device).unsqueeze(0)
    return torch.cat([((1.0 - a) ** 0.5) * eye, (a ** 0.5) * kraus], dim=0)


def intervene_field(field, target_i: int, intervention):
    """Return a field with ``intervention`` applied at data location ``target_i``."""

    def new_field(t: int, i: int):
        kraus = field(t, i)
        if i == target_i and kraus is not None:
            return intervention(kraus)
        return kraus

    return new_field


# --------------------------------------------------------------------------- #
# Frozen decoder + exact logical error rate                                     #
# --------------------------------------------------------------------------- #
def build_frozen_decoder(context: RepCodeContext, *, nominal_p: float = 0.05):
    """Predeclared MWPM decoder for ``context`` (weight-uniform, noise-agnostic).

    Built once from the eval circuit's detector error model and reused unchanged
    across teacher / twin / base / ``do()`` -- ``D`` is frozen.
    """
    import pymatching

    circuit = stim_rep_code_circuit(
        context.distance, context.rounds, nominal_p, logical=context.logical
    )
    dem = circuit.detector_error_model(decompose_errors=True)
    return pymatching.Matching.from_detector_error_model(dem)


def decoder_error_indicator(
    forward: RepCodeForward, decoder, *, logical_reference: int = 0, floor: float = 1e-12
) -> torch.Tensor:
    """Per-branch ``[D(s_b) != actual_flip_b]`` as a fixed ``(B,)`` weight.

    The frozen decoder maps each branch's (structural, theta-independent) syndrome
    to a correction, so this indicator does not depend on the channel parameters
    -- only the branch probabilities do. It therefore turns the LER into the
    *differentiable* form ``sum_b err_b p_theta(b)`` (see ``differentiable_ler``),
    which is what makes the Tier-0/1 alias bands exact and cheap.

    Reachability: only branches with probability above ``floor`` at the current
    state are decoded (the rest are physically negligible and may carry
    non-matchable syndromes); their indicator is left 0. Evaluate at the
    calibration optimum so the reachable set is fixed for the local band.
    """
    probs = forward.probs.detach().cpu()
    reachable = (probs > floor).numpy()
    indicator = torch.zeros_like(forward.probs)
    if not reachable.any():
        return indicator
    detectors = forward.detector_events.round().to(torch.uint8).cpu().numpy()[reachable]
    predicted = decoder.decode_batch(detectors).reshape(-1).astype(np.int64)
    observable = forward.observable.round().to(torch.int64).cpu().numpy()[reachable]
    actual_flip = (observable + int(logical_reference)) % 2
    errors = torch.tensor((predicted != actual_flip).astype(float), dtype=forward.probs.dtype)
    indicator[torch.tensor(reachable)] = errors
    return indicator


def differentiable_ler(forward: RepCodeForward, error_indicator: torch.Tensor) -> torch.Tensor:
    """``LER(theta) = sum_b err_b p_theta(b)`` -- differentiable in the channel params.

    ``error_indicator`` is the frozen ``decoder_error_indicator`` (precomputed at
    the calibration optimum); only ``forward.probs`` carries the gradient.
    """
    return (error_indicator * forward.probs).sum()


def logical_error_rate(
    forward: RepCodeForward, decoder, *, logical_reference: int = 0
) -> float:
    """Exact LER under the frozen decoder: ``sum_b p(b) [D(s_b) != flip_b]``.

    The decoder predicts the observable flip from each branch's syndrome; a
    logical error is a disagreement with the actual flip (``observable`` XOR the
    noiseless ``logical_reference``). Exact because it sums over the enumerated
    joint, not samples.
    """
    with torch.no_grad():
        probs = forward.probs.detach().cpu()
        # The enumeration yields all 2**K records; unachievable ones (inconsistent
        # ancilla parities) carry exactly zero probability and can map to
        # non-matchable syndromes. Decode only the physically reachable branches;
        # the zero-probability remainder contributes nothing to the LER.
        reachable = (probs > 1e-12).numpy()
        if not reachable.any():
            return 0.0
        detectors = forward.detector_events.round().to(torch.uint8).cpu().numpy()[reachable]
        predicted = decoder.decode_batch(detectors).reshape(-1).astype(np.int64)
        observable = forward.observable.round().to(torch.int64).cpu().numpy()[reachable]
        actual_flip = (observable + int(logical_reference)) % 2
        error = torch.tensor((predicted != actual_flip).astype(np.float64))
        return float((probs[reachable] * error).sum())


# --------------------------------------------------------------------------- #
# Counterfactual-validity scores                                                #
# --------------------------------------------------------------------------- #
def _ler_and_forward(field, context, decoder):
    forward = run_context(context, channel_field=field)
    ler = logical_error_rate(forward, decoder, logical_reference=context.logical)
    return ler, forward


def field_counterfactual_scores(
    teacher_field,
    other_field,
    context: RepCodeContext,
    decoder,
    *,
    target_i: int,
    intervention,
) -> dict[str, float]:
    """Score one ``do()`` at location ``target_i`` for ``other_field`` vs the teacher.

    Applies the SAME channel-level intervention to the teacher-true field and to
    ``other_field`` (a calibrated twin field, or a negative-control field), exact-
    forwards both on the held-out ``context``, and returns the knob error ``B_LER``
    and observation-shift error ``B_obs`` plus the underlying base/do LERs.
    """
    with torch.no_grad():
        base_teacher_ler, base_teacher = _ler_and_forward(teacher_field, context, decoder)
        base_other_ler, base_other = _ler_and_forward(other_field, context, decoder)

        do_teacher_field = intervene_field(teacher_field, target_i, intervention)
        do_other_field = intervene_field(other_field, target_i, intervention)
        do_teacher_ler, do_teacher = _ler_and_forward(do_teacher_field, context, decoder)
        do_other_ler, do_other = _ler_and_forward(do_other_field, context, decoder)

        dler_teacher = do_teacher_ler - base_teacher_ler
        dler_other = do_other_ler - base_other_ler

        # dp over (s,m): base/do share the circuit structure, so branches align.
        dp_teacher = do_teacher.probs - base_teacher.probs
        dp_other = do_other.probs - base_other.probs
        b_obs = 0.5 * float((dp_teacher - dp_other).abs().sum())

    return {
        "B_LER": abs(dler_teacher - dler_other),
        "B_obs": b_obs,
        "dLER_teacher": dler_teacher,
        "dLER_twin": dler_other,
        "base_teacher_LER": base_teacher_ler,
        "base_twin_LER": base_other_ler,
        "do_teacher_LER": do_teacher_ler,
        "do_twin_LER": do_other_ler,
    }


def counterfactual_scores(
    teacher_field,
    twin: RepCodeTwin,
    context: RepCodeContext,
    decoder,
    *,
    target_i: int,
    intervention,
) -> dict[str, float]:
    """``field_counterfactual_scores`` for a calibrated ``twin`` (uses ``twin.field()``)."""
    return field_counterfactual_scores(
        teacher_field, twin.field(), context, decoder, target_i=target_i, intervention=intervention
    )
