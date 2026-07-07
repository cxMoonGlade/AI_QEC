# P2 — the conjunction @ d3: Θ→leakage per-round wiring (PRE-REGISTRATION, 2026-07-06)

**Goal (product spec P2):** one call = non-Markov latent (`source/process.py`) → shared-latent Θ fan-out
(`source/coupling.py`) → **qutrit leakage carrier** → `{det,obs}` + DEM, oracle-bounded on tiles. This is THE core
deliverable: the triple conjunction [leakage + non-Markov temporal + shared-latent] emitted as one faithful record.
User go-ahead 2026-07-06 ("都同意"). Grounding: the recon map (SV kernels take a STATIC leak-Kraus stack per run;
per-round modulation today exists ONLY on the DM caller loop) + the P0/P1 substrate.

## 0. The design decision (registered)
Per-round leakage modulation lands at THREE tiers, cheapest-referee-first:
- **T0 (exists): DM oracle arm** — the caller-driven `apply_within_cycle_round` loop takes a different leak slice per
  round today. The referee; no src change.
- **T1 (small src): MPS carrier arm** — `MpsLeakageForward._run_trajectory` applies leak ops from a list built once
  per run; change: accept a PER-ROUND leak-slice sequence (indexed by the round loop that already exists). ~1 s/shot
  ⇒ the certified mid-scale arm (certification + moderate-N coupled records), not production throughput.
- **T2 (kernel src, the production arm): `sv_traj_d3_wc` op_uid leak indexing** — the wc CSR already carries
  `op_uid` per op and DECLARES it UNUSED for `WC_OP_LEAK` (loader docstring): extend the kernel so `WC_OP_LEAK`'s
  `op_uid` indexes into a STACK of leak-Kraus sets `[n_sets, n_kraus, 3, 3]`, and `marshal_within_cycle` points each
  round's LEAK ops at that round's set. Backward-compatible (a single-set stack reproduces today's behavior
  bit-for-bit — the regression gate). CUDA change ⇒ highest cert burden, done LAST, after T1 is certified.

**Θ→leakage map (the physics seam):** extend `SourceCouplingConfig`/`CoupledMechanismParams` with leakage fields —
per-cycle `theta_wg(t)`, `g_seep(t)` modulated by the shared latent `z_t` (logit/linear form mirroring the existing
gamma_phi map). **Epistemic class (c) DECLARED map with a swept sensitivity bracket** — same discipline as the
existing gamma_phi fan-out (no literature-anchored TLS→leakage-rate transfer function is claimed; theory-first check
for one is part of P2-i, and absence ⇒ the bracket is the honest object). Θ(0) must collapse to today's static
physical cell exactly (the off-source identity).

## 1. Phases + registered gates
- **P2-i — Θ fan-out extension (src: `source/coupling.py`).** New fields + manifest + off-source identity.
  Gates (a): Θ(0) == the static cell exactly; closed-form map identities (the P1-b/test_source_coupling pattern);
  liveness: a non-constant z gives non-constant theta/g_seep (the C-9/R1 pattern).
- **P2-ii — T1 MPS per-round leak (src: `mps_forward.py`).** Gates: (a) single-set regression — per-round sequence
  of IDENTICAL slices reproduces today's arm byte-identically (same seeds); (b) record gate vs T0 — per-round-varied
  MPS records vs the per-round DM law: full-9q R=1 marginals against the **SEQUENTIAL-measurement null** (the P1-c
  lesson — never the isolated projection), z ≤ 4 at registered N; sub-register R∈{2,3} joint-history TV at the
  Gate-4 1/√N rate; (c) liveness control — varied-vs-constant arms differ beyond MC error where the modulation
  amplitude says they must (predict the effect size from the slice-channel derivative BEFORE the run); (d) per-arm
  truncation ledgers.
  API DESIGN PIN (2026-07-06, before code; grounded in the verified seams): `sample(...,
  leak_slices: Sequence[Tensor] | None = None)` — `None` = today's path (BYTE-identical, the gate-(a)
  object); else length-R sequence of `(n_kraus, 3, 3)` per-round slice tables, each CPTP-asserted at
  sample entry (`SvSampler.cptp_residual < CPTP_TOL` — the C1 discipline; the carrier never trusts
  caller tables). The CSR marshal is CONTENT-independent for leak (`_emit_leak` records `op_uid=0`;
  verified sv_sampler.py:958-959), so marshalling is UNCHANGED; `marsh.leak_kraus` is NOT consumed by
  the MPS arm (`_run_trajectory` takes its leak argument explicitly) — documented, not silently relied
  on. `_run_trajectory`'s leak parameter becomes per-round (`leak_by_round[r]`, the existing round
  loop); the POST-measure segment of round r uses round r's table (a registered convention — today's
  post segments contain only the transversal Y, no leak ops, so the convention is dormant but pinned).
  Building per-round tables FROM Θ (theta_wg(t)/g_seep(t) draws) is the CALLER's job (gate scripts,
  later the P2-iv teacher) — the carrier stays a data consumer (backend-agnostic seam). ShotSet header
  provenance: `leak_slices_mode` = `static`/`per_round` + a sha256 over the stacked per-round tables.
  T0 referee needs NO src change: the gate script hands `apply_within_cycle_round` a per-round marsh
  (CSR identical, only `leak_kraus` differs).
- **P2-iii — T2 kernel leak-stack (src: `.cu` + loader + marshal).** Gates: (a) single-set stack == today's kernel
  BIT-identical (same seeds, byte-compare packed shots); (b) varied-stack kernel vs the T1 MPS arm at matched
  model/seeds-independent statistics (two-implementation cross-check, the Gate-4 pattern); (c) throughput report
  (production claim needs ≥1e5 shot-rounds/min retained).
- **P2-iv — the one-call conjunction teacher (src: `teachers/`).** `CoupledLeakageTeacher` (or an extension seam on
  `CoupledCycleTeacher`) consuming (SourceProcess, SourceCouplingConfig, RunSpec-like cell) → emits `{det,obs}` via
  T1/T2 + the P0 interop exports (`records_to_dem` with the P1-a-bounded L0 rule incl. the last-round-delta
  refinement). Constraint-ledger + emit-surface projection mirroring C-1..C-12; truth evaluator-only; certified via
  the `certify` seam where feasible (note the dm_oracle DETECTOR_MARG semantics chip task_e194ccf4 — until fixed,
  record-level gates use the sequential-null pattern from the P1-c script directly).
- **P2-v — the conjunction record demo + faithfulness-table rows.** One committed run: the triple ON (non-Markov
  latent → Θ → per-round leakage) at d3, oracle-bounded on tiles + full-9q R=1 marginals; new table rows for the
  Θ→leakage map and the coupled-leakage record; feeds P3's killer-demo geometry choice.

## 2. Registered predictions (before any run)
- P2-1 (a): all off-source/single-set identities exact (bit/1e-12 tier).
- P2-2 (b): the varied-arm record effect size — per-round g_seep modulation at the gamma_phi-style ±30% bracket
  shifts per-round detector marginals by O(∂p/∂g_seep · Δg); the slice-channel derivative computed analytically
  BEFORE the run sets the liveness band. A sub-MC-floor effect at the registered N = a finding (records the
  coupling-visibility boundary for leakage, exactly the G0/S-4-style honest map).
- P2-3 (b): T1-vs-T0 record gates pass at the P1-c tier (z ≤ 4, sequential null).
- P2-4 (c): T2 throughput within 2× of today's wc kernel.
- Constants (c): fixture = real d3 XZZX cell (theta WG_L1=5e-3 calibrated, g_seep=0.09 base, b=0.9, arm A);
  modulation bracket ±30% logit/linear (swept, not pinned); N per gate registered in the phase scripts.

## 3. Disciplines
Src per phase needs user confirmation before commit (P2-i..iv are `src/` work); every run a committed script +
runner (aiqec-bin PATH for kernel JIT); GPU serial; CODE_MAP regen per src change; un-led review before每个 GPU
gate run (three-for-three catch rate this session); faithfulness protocol binds every new mechanism row
(declared + bounded vs T0, unbounded = STOP).
