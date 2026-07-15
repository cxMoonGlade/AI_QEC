from __future__ import annotations

"""One-call certification facade for a controlled noise process.

``certify_noise_process`` auto-builds the independent anchors (the exact
DM + the stim Clifford-slice wiring), routes each over its FEASIBLE cells (OOM-as-data — an anchor
that would OOM at a regime is simply skipped, never allocated), runs the negative controls (ON by
default), over the ``level``'s (statistic, R) grid, and merges ONE epistemic ledger.

The DM and stim anchors certify different process views (the full mechanism vs the Clifford slice), so
both run — they don't compete; the OOM routing is per-anchor. Statistical (stim) rows give
PASS_PROVISIONAL, never PASS.

MEMORY ACCOUNTING CORRECTED 2026-07-06 (residual-②): the DM anchor's DETECTOR_MARG cell now declares
its TRUE live set (4 conservative copies ≈ 24.8 GB at full-9q — the old 2-copy ~12.4 GB claim would
have OOMed). Consequence on a 32 GB card at the default ``safety=0.5``: EVERY full-register grid cell
is DM-infeasible, so the ledger is stim-only and the verdict caps at PASS_PROVISIONAL — an HONEST gap,
loudly different from the previous silently-false "exact" rows. The measured lean peak (~3.3 copies
≈ 20 GB) does fit a dedicated 32 GB card: pass ``dm_safety=0.78`` (or your own anchor) to enable the
full-9q exact leg DELIBERATELY; sub-register cells via ``cells=`` remain the conservative route.
"""

from .anchors import CorruptStabControl, DMOracleAnchor, StimCliffordAnchor
from .core import _rollup, certify_cells
from .types import CertReport, Regime, Statistic

#: The ``level`` grids — (statistic, R) checks + the shot budget. SMOKE for CI, STANDARD the default,
#: DEEP for the orchestrator's high-N run.
_LEVELS = {
    "smoke": {"checks": [(Statistic.DETECTOR_MARG, 1)], "N": 30_000},
    "standard": {"checks": [(Statistic.DETECTOR_MARG, 1), (Statistic.DETECTOR_MARG, 2)], "N": 200_000},
    "deep": {"checks": [(Statistic.DETECTOR_MARG, 1), (Statistic.DETECTOR_MARG, 2),
                        (Statistic.DETECTOR_MARG, 3)], "N": 2_000_000},
}


def certify_noise_process(process, *, level: str = "standard", anchors=None, controls=None,
                          device: str = "cuda", N: int | None = None, seed: int = 0,
                          cells=None, dm_safety: float | None = None) -> CertReport:
    """Certify a controlled noise process against independent formal anchors → one
    epistemic ledger + a single verdict.

    ``level`` ∈ {smoke, standard, deep} selects the (statistic, R) grid + the shot budget. ``anchors``
    defaults to ``[DMOracleAnchor, StimCliffordAnchor]`` (the closed-form sidecar is opt-in — it needs
    a non-degenerate non-unital Markov pair). ``controls`` defaults to the corrupt-stabilizer control.
    ``cells`` overrides the level grid (for tests / bespoke plans). ``dm_safety`` overrides the DM
    anchor's card-budget fraction (default 0.5) — the DELIBERATE opt-in for the full-9q exact leg on a
    32 GB card (see the module docstring; ignored when ``anchors`` is supplied explicitly)."""
    if level not in _LEVELS:
        raise ValueError(f"unknown level {level!r}; choose from {sorted(_LEVELS)}")
    plan = _LEVELS[level]
    n_eff = int(N or plan["N"])
    if anchors is None:
        required_extensions = ("dm_round_callbacks", "emit_clifford_slice")
        missing = [
            name for name in required_extensions
            if not callable(getattr(process, name, None))
        ]
        if missing:
            raise TypeError(
                "certify_noise_process capability error: default anchors require callable process "
                f"extensions; missing: {', '.join(missing)}"
            )
        dm_kwargs = {} if dm_safety is None else {"safety": float(dm_safety)}
        anchors = [DMOracleAnchor(device=device, **dm_kwargs), StimCliffordAnchor()]
    if controls is None:
        controls = [CorruptStabControl(stab=1)]
    check_list = cells if cells is not None else [
        (s, _regime(process, R)) for (s, R) in plan["checks"]
    ]

    all_rows, all_controls, routing = [], [], {}
    for anchor in anchors:
        feasible = [(s, r) for (s, r) in check_list
                    if s in anchor.answers() and anchor.capability(s, r).feasible]
        if not feasible:
            continue
        rep = certify_cells(process, feasible, [anchor], controls, N=n_eff, seed=seed)
        all_rows.extend(rep.rows)
        all_controls.extend(rep.controls)
        routing.update({f"{anchor.name}:{k}": v for k, v in rep.routing.items()})
    if not all_rows:
        raise ValueError(
            "certify_noise_process: no anchor could feasibly answer any cell "
            "(check the level / process geometry)"
        )
    return CertReport(_rollup(all_rows, all_controls), tuple(all_rows), tuple(all_controls),
                      routing, dict(process.truth), {"level": level, "N": n_eff, "seed": seed})


def _regime(process, R: int) -> Regime:
    sched = process.sched
    return Regime(R=R, register="full", n_active=int(sched.n_data),
                  n_stab=len(sched.stabilizers), arm="A", b=1.0)
