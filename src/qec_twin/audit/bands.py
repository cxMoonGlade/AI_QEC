from __future__ import annotations

"""D3 Tier 0 (ADR 0008): the closed-form Laplace ellipsoid alias/uncertainty band.

This is the band *method* for the D3 phase: a single first-order, closed-form
expression that is simultaneously the slack-coupling formula AND the D5a audit AND
the warm-start/lower-bound for the higher tiers (TRS / warm-started extremization /
boundary sampling).

Setup. At the calibration optimum ``theta*`` the exact-NLL is locally quadratic
with Hessian ``H`` (the Fisher information per unit data; ``sum``-over-``N``-shots
NLL has Hessian ``N H``), and the knob ``dLER`` is locally linear with gradient
``g = d dLER / d theta``. Over the calibration-consistent ellipsoid
``{delta : 1/2 delta^T (N H) delta <= s}`` the range of the linear knob is
``dLER* +/- sqrt(2 s / N) sqrt(g^T H^+ g)``. Writing it per-shot:

    statistical half-width = (z / sqrt(N)) * sqrt(g^T H^+ g)        (z = sqrt(chi2_1))

is the **a<->b coupling in one line**: the finite-shot scale ``N`` (the D3b axis)
enters as ``1/sqrt(N)``; the model-set (D3a) geometry is ``g^T H^+ g``.

D5a audit, for free. Eigendecompose ``H``. Gauge + aliased directions are its
near-null space; a *physical* knob is gauge-invariant, so ``g`` has zero weight on
gauge directions but **non-zero weight on a genuinely aliased direction** -- there
``g^T H^+ g`` diverges, i.e. the knob has an unbounded *epistemic* (alias) band
that no amount of data shrinks. So the eigenspectrum splits the two uncertainties
the ADR demands be reported separately: large-eigenvalue weight -> statistical
band (``~1/sqrt(N)``); near-null weight of ``g`` -> epistemic alias band (the
D5a learnable-DOF deficiency, surfaced on the knob). Tier 0 reports both; the true
*bounded* epistemic magnitude (CPTP-constrained, non-monotone) needs Tier 1+ and
is warm-started from here.
"""

import torch

from qec_twin.calibration.nll import RepCodeTwin, joint_cross_entropy
from qec_twin.contexts.ladder import RepCodeContext, run_context
from qec_twin.knobs.intervention import (
    decoder_error_indicator,
    differentiable_ler,
    intervene_field,
)
from qec_twin.forward.cptp_channel import CDTYPE, RDTYPE


def _kraus_from_generator(real, imag, dim, num_kraus):
    m = real.to(CDTYPE) + 1j * imag.to(CDTYPE)
    hermitian = m + m.conj().transpose(-1, -2)
    isometry = torch.matrix_exp(1j * hermitian)[:, :dim]
    return isometry.reshape(num_kraus, dim, dim)


def flatten_twin(twin: RepCodeTwin) -> torch.Tensor:
    """Concatenate the twin's per-location (real, imag) generators into ``theta``."""
    parts = [p.reshape(-1) for ch in twin.channels for p in (ch.real, ch.imag)]
    return torch.cat(parts).detach()


def field_from_flat(theta: torch.Tensor, twin: RepCodeTwin):
    """Rebuild the per-location channel field from a flat ``theta`` (differentiable)."""
    kraus_list = []
    idx = 0
    for ch in twin.channels:
        size = ch.real.numel()
        real = theta[idx : idx + size].reshape(ch.real.shape)
        idx += size
        imag = theta[idx : idx + size].reshape(ch.imag.shape)
        idx += size
        kraus_list.append(_kraus_from_generator(real, imag, ch.dim, ch.num_kraus))
    return lambda t, i: kraus_list[i]


def _make_nll_fn(twin, contexts, teacher_forwards):
    def nll(theta: torch.Tensor) -> torch.Tensor:
        field = field_from_flat(theta, twin)
        loss = torch.zeros((), dtype=RDTYPE)
        for context, teacher in zip(contexts, teacher_forwards):
            loss = loss + joint_cross_entropy(teacher, run_context(context, channel_field=field))
        return loss

    return nll


def tier0_alias_band(
    twin: RepCodeTwin,
    contexts: list[RepCodeContext],
    teacher_forwards,
    *,
    eval_context: RepCodeContext,
    decoder,
    target_i: int,
    intervention,
    shots: int,
    z: float = 1.0,
    tol: float = 1e-7,
) -> dict[str, object]:
    """Tier-0 band on the ``do()`` knob ``dLER`` at the calibration optimum.

    Returns the knob value, the statistical half-width at ``shots`` (``z=1`` is
    1-sigma), the eigenspectrum split, and the epistemic alias weight of ``g`` in
    ``H``'s near-null space (non-zero -> a non-identifiable knob direction, the
    D5a deficiency surfaced).
    """
    theta = flatten_twin(twin).requires_grad_(True)

    field = field_from_flat(theta, twin)
    base = run_context(eval_context, channel_field=field)
    do_field = intervene_field(field, target_i, intervention)
    intervened = run_context(eval_context, channel_field=do_field)

    err_base = decoder_error_indicator(base, decoder, logical_reference=eval_context.logical)
    err_do = decoder_error_indicator(intervened, decoder, logical_reference=eval_context.logical)
    knob = differentiable_ler(intervened, err_do) - differentiable_ler(base, err_base)
    (g,) = torch.autograd.grad(knob, theta)

    hessian = torch.autograd.functional.hessian(_make_nll_fn(twin, contexts, teacher_forwards), theta.detach())
    hessian = 0.5 * (hessian + hessian.transpose(-1, -2))
    eigenvalues, eigenvectors = torch.linalg.eigh(hessian)
    g_proj = eigenvectors.transpose(-1, -2) @ g.detach()

    well = eigenvalues > tol
    inv_quad = float(((g_proj[well] ** 2) / eigenvalues[well]).sum())  # g^T H^+ g
    statistical_band = float(z * (inv_quad / float(shots)) ** 0.5)
    alias_weight = float((g_proj[~well] ** 2).sum() ** 0.5)

    return {
        "knob_value": float(knob.detach()),
        "statistical_band": statistical_band,
        "inv_quad": inv_quad,
        "alias_weight": alias_weight,
        "num_aliased_with_signal": int(((~well) & (g_proj.abs() > tol)).sum()),
        "eig_min": float(eigenvalues.min()),
        "eig_max": float(eigenvalues.max()),
        "grad_norm": float(g.detach().norm()),
    }
