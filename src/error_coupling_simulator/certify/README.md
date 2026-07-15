# certify — compare a controlled noise process with independent formal anchors

**Evaluator-side boundary.** Scores a controlled noise process's emitted records (or the
scalable carrier that produces them) against **independent, exact-or-declared-reduction ground-truth
anchors**, and returns an epistemic ledger + a single verdict.

**Design (locked).** A common-caller spine over an
`Anchor` capability-descriptor **port**. The core is BLIND to whether a DM oracle, a stim Clifford
slice, or a closed-form identity answered; the port carries a *capability descriptor* so OOM-routing
is **data**: an anchor that would OOM reports `feasible=False`, the core routes to the carrier-MCWF for
scale and never allocates the infeasible density matrix. Closed-form identities ride as an analytic
**sidecar** (the `SCALAR_FUNC` statistic), not as peers in the distributional comparison.

- `types.py` — the interface: `Regime`, the `Anchor` / `Control` /
  `ControlledNoiseProcess` ports, and the
  epistemic ledger (`CertReport` / `LedgerRow` / `Verdict`). Pure value types; no GPU.
- `core.py` — the implemented route → controls-first → score → ledger engine.
- `anchors/` — the implemented DM / Stim / closed-form adapters plus corrupt-stabilizer and
  record-shuffle negative controls (each **wraps** an existing package/wheel route, never
  reimplements physics).
- `facade.py` — the implemented `certify_noise_process` entry point.

**Invariants.** Negative controls are first-class + non-optional (an inert control forces FAIL);
feasibility is data (cannot OOM); every row carries its epistemic class (a)/(b)/(c) (METRICS.md);
anchors must be INDEPENDENT of the carrier's implementation (anti-circular).
For the fused within-cycle SV-MC carrier, certification accepts only a c128
`c128_candidate` header; callers must use `carrier.c128_evidence_record_batch(...)` before reducing
the self-describing packed batch to a `RecordBatch`. A c64 optimization artifact is permanently `screening_only`; replaying
the frozen run in c128 creates a separate candidate artifact and does not promote the c64 artifact.

**Boundary.** Certification may read evaluator-only process truth to score the declared process, but
that truth never enters emitted records. Anchors wrap package-owned exact-DM, Stim, and closed-form
references; no physics is reimplemented here. Downstream decoder-headroom analysis is not a
simulator certification rung.
The facade requires a caller process that implements its declared capability protocols. It is not
an automatic `RecordBatch -> certificate` transform: the current `CoupledCycleNoiseProcess` has no
DM replay callback and its Clifford-slice method is still an explicit open bridge.
