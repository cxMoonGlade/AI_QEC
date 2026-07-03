from __future__ import annotations

"""``certify_teacher`` — the one-call facade (the common-caller spine, ③).

``certify_teacher(teacher, level=...) -> CertReport`` auto-builds the independent anchors (the exact
DM + the stim Clifford-slice wiring), routes each over its FEASIBLE cells (OOM-as-data — an anchor
that would OOM at a regime is simply skipped, never allocated), runs the negative controls (ON by
default), over the ``level``'s (statistic, R) grid, and merges ONE epistemic ledger. It collapses the
hand-rolled per-script cross-check (the ~950-line ``twin_xzzx_teacher_fullmix.main()`` / the L1–L6
ledger of ``twin_dm_record_oracle_check``) to a call.

The DM and stim anchors certify DIFFERENT teacher VIEWS (the full mechanism vs the Clifford slice), so
both run — they don't compete; the OOM routing is per-anchor (the DM skips R≥2 full-9q; the carrier /
closed-form carry the scale, opt-in). Statistical (stim) rows give PASS_PROVISIONAL, never PASS.
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


def certify_teacher(teacher, *, level: str = "standard", anchors=None, controls=None,
                    device: str = "cuda", N: int | None = None, seed: int = 0, cells=None) -> CertReport:
    """Certify a controlled teacher against the auto-routed independent ground-truth anchors → one
    epistemic ledger + a single verdict.

    ``level`` ∈ {smoke, standard, deep} selects the (statistic, R) grid + the shot budget. ``anchors``
    defaults to ``[DMOracleAnchor, StimCliffordAnchor]`` (the closed-form sidecar is opt-in — it needs
    a non-degenerate non-unital Markov pair). ``controls`` defaults to the corrupt-stabilizer control.
    ``cells`` overrides the level grid (for tests / bespoke plans)."""
    if level not in _LEVELS:
        raise ValueError(f"unknown level {level!r}; choose from {sorted(_LEVELS)}")
    plan = _LEVELS[level]
    n_eff = int(N or plan["N"])
    if anchors is None:
        anchors = [DMOracleAnchor(device=device), StimCliffordAnchor()]
    if controls is None:
        controls = [CorruptStabControl(stab=1)]
    check_list = cells if cells is not None else [(s, _regime(teacher, R)) for (s, R) in plan["checks"]]

    all_rows, all_controls, routing = [], [], {}
    for anchor in anchors:
        feasible = [(s, r) for (s, r) in check_list
                    if s in anchor.answers() and anchor.capability(s, r).feasible]
        if not feasible:
            continue
        rep = certify_cells(teacher, feasible, [anchor], controls, N=n_eff, seed=seed)
        all_rows.extend(rep.rows)
        all_controls.extend(rep.controls)
        routing.update({f"{anchor.name}:{k}": v for k, v in rep.routing.items()})
    if not all_rows:
        raise ValueError("certify_teacher: no anchor could feasibly answer any cell (check the level / "
                         "the teacher geometry)")
    return CertReport(_rollup(all_rows, all_controls), tuple(all_rows), tuple(all_controls),
                      routing, dict(teacher.truth), {"level": level, "N": n_eff, "seed": seed})


def _regime(teacher, R: int) -> Regime:
    sched = teacher.sched
    return Regime(R=R, register="full", n_active=int(sched.n_data),
                  n_stab=len(sched.stabilizers), arm="A", b=1.0)
