from __future__ import annotations

r"""Pure uniform-to-outcome decision maps for the PEPS trajectory carrier.

These functions are the single source of the three decision rules used by
``trajectory`` and are independently exercised on CPU value stubs.

No torch / quimb / GPU dependency — plain-Python integer/float logic, callable
anywhere.
"""


def sbit_from_uniform(u: float, p0: float) -> int:
    """Stabilizer Born outcome from one uniform, matching
    ``mps_forward._measure_stabilizer``: ``sbit = 0 iff u < p0`` (strict ``<``), else 1 —
    ``p0 = 1/2 (1 + <P>)`` is the outcome-0 branch probability."""
    return 0 if float(u) < float(p0) else 1


def terminal_bit_from_uniform(u: float, p1: float) -> int:
    """Terminal per-qutrit readout bit from one uniform, matching
    ``mps_forward._terminal_readout``: ``bit = 1 iff u < p1``
    (STRICT ``<``), else 0 — ``p1 = <F1> / <psi|psi>``."""
    return 1 if float(u) < float(p1) else 0


def leak_branch_from_uniform(u: float, weights) -> int:
    """MCWF Kraus branch from one uniform: with
    ``tot = sum(weights)`` and ``target = u * tot``, select the FIRST ``k`` with
    ``target <= cumsum_k`` (NON-STRICT ``<=``); fallback ``K - 1`` if none
    (the ``u = 1`` / rounding tail). ``weights[k] = p_k = <psi| K_k^dag K_k
    |psi>`` (unnormalized branch masses — the caller reads them).

    Raises ``ValueError`` on nonpositive total mass (a collapsed state; the
    caller normally guards this first with the tighter numerical floor)."""
    ws = [float(w) for w in weights]
    if not ws:
        raise ValueError("leak_branch_from_uniform: empty weight list")
    tot = float(sum(ws))
    if not tot > 0.0:
        raise ValueError(f"leak_branch_from_uniform: nonpositive total mass {tot:.6e}")
    target = float(u) * tot
    cum = 0.0
    sel = len(ws) - 1  # fallback K-1
    for k, w in enumerate(ws):
        cum += w
        if target <= cum:  # non-strict tie break
            sel = k
            break
    return int(sel)


__all__ = [
    "sbit_from_uniform",
    "terminal_bit_from_uniform",
    "leak_branch_from_uniform",
]
