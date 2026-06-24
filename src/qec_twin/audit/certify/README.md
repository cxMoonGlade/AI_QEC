# audit/certify — certify a controlled teacher against independent ground-truth anchors

**Evaluator-side (the `audit` boundary).** Scores a **controlled teacher**'s emitted records (or the
scalable carrier that produces them) against **independent, exact-or-declared-reduction ground-truth
anchors**, and returns an epistemic ledger + a single verdict. Graduates into one deep module the
carrier↔DM↔closed-form cross-checks that were re-wired ad hoc across `outputs/teacher_prereg/` (the
de-facto `p7e_carrier_cert_common` + the stim slice in `twin_xzzx_teacher` + the closed-form anchors
in `mechanisms`/`hardware`).

**Design (locked).** A common-caller spine `certify_teacher(teacher, level=...) -> CertReport` over an
`Anchor` capability-descriptor **port** — the same Protocol shape as
`audit.floor_backend.PathJointEvaluator`. The core is BLIND to whether a DM oracle, a stim Clifford
slice, or a closed-form identity answered; the port carries a *capability descriptor* so OOM-routing
is **data**: an anchor that would OOM reports `feasible=False`, the core routes to the carrier-MCWF for
scale and never allocates the infeasible density matrix. Closed-form identities ride as an analytic
**sidecar** (the `SCALAR_FUNC` statistic), not as peers in the distributional comparison.

- `types.py` — the interface: `Regime`, the `Anchor` / `Control` / `ControlledTeacher` ports, and the
  epistemic ledger (`CertReport` / `LedgerRow` / `Verdict`). Pure value types; no GPU.
- *(later steps)* `core.py` — the route → controls-first → score → ledger engine; `anchors/` — the DM
  / stim / closed-form adapters (each **wraps** an existing wheel, never reimplements physics); the
  `certify_teacher` facade.

**Invariants.** Negative controls are first-class + non-optional (an inert control forces FAIL);
feasibility is data (cannot OOM); every row carries its epistemic class (a)/(b)/(c) (METRICS.md);
anchors must be INDEPENDENT of the carrier's implementation (anti-circular).

**Boundary.** Evaluator-only: reads the teacher's known truth to SCORE; never feeds a learner. Anchors
WRAP the validated wheels (`forward/exact/qutrit_dm`, the stim slice, `mechanisms/seam_teachers` +
`hardware/dem_compose` closed forms, `audit/bayes_floor`) — no physics is reimplemented here.
