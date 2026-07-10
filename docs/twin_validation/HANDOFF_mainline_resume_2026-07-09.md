# Mainline Handoff — Resume the P0→P4 Simulator Build (2026-07-09)

**Scope of this handoff:** how to proceed on the **mainline** (the error-coupling SIMULATOR, the
P0→P4 plan) after pausing the P4-side unit-test program. It deliberately does **not** cover the
test-coverage work (that state lives in the full-coverage program notes + `tests/CODEBOOK.md`).
Everything below is the science/build spine.

---

## 0. One-paragraph orientation (read first — do not re-derive)

**Goal (do NOT re-frame):** express the coupled / leakage error content **as CORRECTLY and as FAST
as possible, ORACLE-BOUNDED**. The value is a faithful/fast/bounded simulator **plus the P3
"Stim-can't-produce-this" demo** — *not* novelty or quantum advantage. Proving quantum,
classically-irreproducible expressive power on the syndrome is IMPOSSIBLE (proven protocol boundary)
and is NOT the goal.

**notion hierarchy (the why):** the passive QEC syndrome record — the simulator's PRODUCT — carries
only **notion-2** (classical multi-time record memory; Markov-order > 1). **notion-3** (quantum /
Kolmogorov-violation) is **CLOSED as a protocol boundary** and **parked**. Consequence for scope:
the **quantum GKSL bath / "Branch B" is PARKED** (trigger-gated, not deleted); the live frontier is
the **notion-2 faithful correlated simulator** — the classical / CP-divisible source (`source/*`,
already built) → Θ fan-out → qutrit-leakage carrier → {det,obs}+DEM. `quantum_bath/` stays in the
tree as (a) the evidence trail for the notion-3 closure and (b) reusable **matched nulls** for the
record-characterization validity chain; no further quantum-bath science is on the critical path.

Authoritative framing: `project-simulator-p0p4-plan-framing` (memory) ·
`docs/twin_validation/notion3_protocol_boundary_closure.md` ·
`docs/twin_validation/conjunction_tool_product_spec_2026-07-06.md`.

---

## 1. Where the mainline stands (verified 2026-07-09 against the preregs)

| stage | content | status |
|---|---|---|
| **P0** | interop spike: emit → Stim/DEM → PyMatching decode | ✅ **DONE** (record round-trips the standard stack; z=18) |
| **P1** | faithfulness table: mechanism × independent oracle × error bound × usable d | **9/15 bounded · 5 partially bounded (rows 1,4,6,10,15) · 1 UNBOUNDED-but-fenced (row 9 PhaseBurst)**. "Partially" ≠ unbounded — see §3.3 |
| **P2** | conjunction @ d3: non-Markov latent → Θ fan-out → qutrit-leakage carrier → {det,obs}+DEM, bounded vs qutrit-DM oracle on a tile | **IN PROGRESS.** residual-② precondition MEASURED; **P2-i DONE**; **P2-ii gate (a) DONE + committed** (per-round `leak_slices` seam, `p2ii_gate_a_run.sh` 5/5); **P2-ii (b)+(c) = the LIVE FRONTIER** |
| **P3** | killer demo: an oracle-bounded coupled/leakage record Stim CANNOT produce; decoder/threshold differs from Stim-Pauli | **PARKED** behind P2 — needs a record-ALIVE, X-check-bearing geometry. **The evidence for the whole value prop.** |
| **P4** | d5-thin + API/docs + first user; the unit-test program is P4-side quality hardening | **PAUSED** (this handoff pauses it); runs in parallel, does NOT advance P1–P3 |

**Scaling line (parallel engineering, not a P-stage):** OPT2-1 (batched-MPS op core, quimb-free)
COMMITTED (gates 22/22). **OPT2-2** (batched trajectory driver @ d3-exact grade, RunSpec→ShotSet,
≥10–100× throughput) is the next scaling item. Detail: `project-dualline-build-state` (memory).

---

## 2. The next-action queue (in dependency order)

**Pipeline dependency (from `p2_conjunction_wiring_prereg.md` §1):**
P0 ✅ → **P1 is a STOP-gate on P2** (unbounded ⇒ STOP) → P2-i ✅ → **P2-ii T1 (a✅ → b,c)** →
P2-iii T2 (LAST, highest CUDA cert burden) → P2-iv teacher (emits via T1/T2) → P2-v demo →
**P2-v feeds P3's geometry choice** → P3.

### 2.1 IMMEDIATE — P2-ii (b) + (c) [the live frontier]

Referee tier order is cheapest-first: T0 (the caller-driven `apply_within_cycle_round` DM loop, the
referee — exists) → **T1 (MPS) certified here** → T2 (kernel) later. Gate (a) [byte-identity
regression] already landed 5/5; (b) and (c) are the next phase.

- **(b) — per-round-varied MPS records vs the per-round DM law, under the SEQUENTIAL null.**
  Run: full-9q **R=1 varied-arm** `MpsLeakageForward` records vs the per-round DM oracle (T0 handed a
  per-round `marsh` with identical CSR, only `leak_kraus` differing — **no src change**); plus
  sub-register **R∈{2,3}** joint-history comparisons.
  **Pass (prereg wording):** full-9q R=1 marginals **z ≤ 4 at registered N** against the
  **sequential-measurement null**; sub-register R∈{2,3} joint-history **TV at the 1/√N rate**.
  ⚠ **Load-bearing constraint:** compute the null the way `p1c_full9q_record_bound.py` does — the
  **sequential** null — **NOT** the isolated `dm_oracle.py` DETECTOR_MARG answer (that isolated
  marginal differs by up to 2.1e-4 and would false-fail ≥3 detectors at 4.7–6.6σ; chip
  `task_e194ccf4` is the open blocker for using the certify seam directly).
  Deliverable: a committed P2-ii gate-(b) run script (the gate-(a) analogue was `p2ii_gate_a_run.sh`).

- **(c) — liveness control (predict-before-measure).**
  **Derive first (before any run):** the effect size from the slice-channel derivative
  `∂p/∂g_seep · Δg`, analytically, to set the liveness band. Then run varied-arm vs constant-arm
  records under the ±30% `g_seep` bracket.
  **Pass (prereg wording):** varied-vs-constant arms differ **beyond MC error where the modulation
  amplitude says they must**. A **sub-MC-floor** effect at the registered N is a **finding, not a
  fail** — it records the leakage coupling-visibility boundary (the honest G0/S-4-style map).
  Deliverable: the committed effect-size derivation (lands BEFORE the run) + the liveness
  discriminator in the same gate bundle.

Pointer: `docs/twin_validation/p2_conjunction_wiring_prereg.md` §1 (P2-ii), §2 (predictions P2-2/P2-3),
§"PHASE-1 OUTCOMES".

### 2.2 THEN — P2-iii → P2-iv → P2-v

- **P2-iii — T2 kernel leak-stack** (production arm; src `.cu` + loader + marshal). Make
  `sv_traj_d3_wc`'s `WC_OP_LEAK` use its currently-unused `op_uid` to index a **stack** of leak-Kraus
  sets `[n_sets,n_kraus,3,3]`; `marshal_within_cycle` points each round at its set.
  **Pass:** (a) single-set == today's kernel **BIT-identical** (same seeds — regression gate); (b)
  varied-stack kernel vs the T1 MPS arm (two-implementation cross-check); (c) **throughput ≥ 1e5
  shot-rounds/min** (within 2× of today's wc kernel). **Do LAST** — highest CUDA cert burden, only
  after T1 is certified.

- **P2-iv — `CoupledLeakageTeacher`** (new `src/teachers/` work → **needs user confirmation before
  commit**). Consumes `(SourceProcess, SourceCouplingConfig, RunSpec-like cell)` → emits `{det,obs}`
  via T1/T2 + the P0 interop exports (`records_to_dem`, the P1-a-bounded L0 rule incl. the
  last-round-delta refinement). **Pass:** constraint-ledger + emit-surface projection (mirror
  C-1..C-12); truth evaluator-only; certified via the `certify` seam where feasible — until the
  `dm_oracle` DETECTOR_MARG chip is fixed, record-level gates reuse the **P1-c sequential-null
  pattern directly**. Depends on P2-ii (T1) certified, optionally P2-iii (T2).

- **P2-v — conjunction record demo** (the P2 core deliverable's proof). One committed run with the
  **triple ON** (non-Markov latent → Θ → per-round leakage) at d3. **Pass:** oracle-bounded on tiles
  + full-9q R=1 marginals; add new faithfulness-table rows (Θ→leakage map; coupled-leakage record),
  each bounded. **This run feeds P3's killer-demo geometry choice.**

Pointer: `docs/twin_validation/p2_conjunction_wiring_prereg.md` §1 (P2-iii/iv/v), §2 (P2-4).

### 2.3 PARALLEL — close the 5 open P1 rows

P1 is the STOP-gate on P2, but **P2 is not currently blocked**: 9/15 are bounded, the 5 below are
**partially** bounded (not unbounded), and the only genuinely UNBOUNDED row (9, PhaseBurst) is
correctly **fenced off the shared arm** by the teacher whitelist (`MEMORYFUL_SHARED_SOURCES`) and
unparks only with its own oracle. Close the 5 opportunistically; two of them (rows 1, 15) are
naturally closed BY the P2 wiring.

| # | mechanism | independent oracle | to bound it |
|---|---|---|---|
| **1** | Mechanism catalog M0–M34 | operator refs + analytic Kraus | bound the **deployed-register composition** (currently only 1–2q object-level). **Waits for P2's wiring** (same register plumbing). |
| **4** | MCWF/MPS leakage carrier | dense joint-L (independent expm) + no-op control | d3-full is GROSS tier (TV≤0.2); **tile-decompose to STRICT windows** or shrink the GROSS tier. Standalone eng item. |
| **6** | B5 teachers (overrot / damped-rot / ZZ / corr-dephasing) | analytic Kraus + Stim cross-check | **tighten the Stim cross-check tier or declare it structural-only** (planned: declare structural-only — a doc edit). |
| **10** | TemporalStormSPPSource (2-state HMM) | exact 2-state Markov closed forms | has stationary/corr-length bound; needs a **record-level liveness** once wired to a fixture. |
| **15** | `CoupledCycleTeacher` end-to-end {det,obs} | joint-L + C-10 rates + off-source identity | has component bounds; needs **one end-to-end record-law bound vs independent enumeration at small R**. Closed largely BY P2-iv/P2-v. |

Pointer: `docs/twin_validation/p1_faithfulness_table.md` (table + execution plan + aggregate picture).

### 2.4 THEN — P3 (the payoff, parked)

**Blocker:** P0's demo fixture (`default_coupled_code_spec_d3_repz`, an all-Z rep code) is
**coupling-blind** — its Z-diagonal source-coupled mechanisms are **record-dead** (γφ/ζ Z-diagonal
twirled out of the projective record; γ₁ inert on |0…0⟩). So P0 exercises interop + decode on
**instrument noise only** and makes no coupling-visibility claim.

**Next-step:** pick/build a d3 fixture that **bears an X-check** (an X-type stabilizer), so a
Θ-coupled γφ-style (Z-diagonal dephasing) mechanism produces actual **detection events**
(record-ALIVE) **and** changes MWPM's logical prediction vs the Stim-Pauli DEM (decode-relevant). The
P0 pipeline (export → `records_to_dem` → PyMatching) is reusable as-is.

**Seed:** the **5q x0 chain** — `build_axis1_codespec_frontend_spec` (3 data + 2 ancilla; **x0 =
X on data-0 read by ancilla-3** + z1; logical `logical_z2`; M(R)=2R+3). The **x0 X-check** is the
element that makes a Z-diagonal coupled mechanism record-alive. (A 4q variant "3 data + 1 X-check
ancilla, ZZ edge (0,3)" is also registered.) **P2-v's committed conjunction run picks the geometry.**

Pointer: `docs/twin_validation/p0_interop_spike_notes.md` §Next/§caveats ·
`docs/twin_validation/coupled_teacher_round_gates_prereg.md` §1.1.

### 2.5 SCALING — OPT2-2 (parallel eng, any time)

Batched trajectory driver @ d3-exact grade (RunSpec→ShotSet seam, ≥10–100× throughput). Not a
P-stage; unblocks larger-N gates. Detail: `project-dualline-build-state` (memory).

---

## 3. Carry-over constraints — do NOT relearn these

1. **Sequential-measurement null EVERYWHERE.** Every record-level gate (P2-ii b, P2-iv, P2-v) uses
   the sequential null (the `p1c_full9q_record_bound.py` pattern), **never** the isolated
   `dm_oracle.py` DETECTOR_MARG marginal. The DETECTOR_MARG isolation bug (chip `task_e194ccf4`) is
   the open blocker for using the `certify` seam directly for record gates.
2. **FAITHFULNESS_PROTOCOL is the live STOP.** Every load-bearing model claim: verified vs an
   INDEPENDENT oracle + a constraint ledger + every simplification declared & BOUNDED. **Unbounded ⇒
   STOP.** (`docs/FAITHFULNESS_PROTOCOL.md`.)
3. **G0-v2 is VOID — not a live gate.** The G0-v2 "FAIL/STOP" verdict + `g0_v2_effectsize.json` are
   RETRACTED (wrong observable: 2-point TV / shared-minus-Markovian). The machinery is kept, the
   conclusion is void, and the notion-2 legitimacy question it gated is DEMOTED to an optional
   value-map flag. **Do NOT treat G0-v2 as a STOP over P2-iv.** (`HANDOFF_static_simulator_notion2_2026-07-06.md` §3.)
4. **Theory-first / predict-before-measure** for every gate: derive the predicted direction/scaling/
   band BEFORE the run; a miss is a finding, never rationalized away.
5. **`src/` changes need explicit user confirmation** (P2-iii `.cu`, P2-iv teacher). `docs/` +
   `outputs/` are normal flow.
6. **notion-3 / Branch-B / quantum GKSL bath = PARKED** (trigger-gated, not dropped). `quantum_bath/`
   stays as evidence + reusable matched-nulls. Do not open near-resonant / A′ corner work.
7. **GPU serialized.** The workstation is the user's live desktop — no concurrent GPU jobs; fan-out
   is read-only.

---

## 4. Authoritative documents (pointers)

- `project-simulator-p0p4-plan-framing` (memory) — the big direction (P0→P4 + notion hierarchy).
- `docs/twin_validation/conjunction_tool_product_spec_2026-07-06.md` — the P0→P4 product spec.
- `docs/twin_validation/p2_conjunction_wiring_prereg.md` — P2-i…v wiring + predictions + phase-1 outcomes.
- `docs/twin_validation/p1_faithfulness_table.md` — the P1 faithfulness table (the STOP-gate).
- `docs/twin_validation/residual2_d3_conjunction_cost_prereg.md` — the P2 residual-② cost precondition.
- `docs/twin_validation/notion3_protocol_boundary_closure.md` — the notion-3 closure (why Branch B is parked).
- `docs/twin_validation/coupled_teacher_round_gates_prereg.md` — the 5q x0 fixture + teacher round gates.
- `docs/twin_validation/HANDOFF_static_simulator_notion2_2026-07-06.md` — operative substrate + the RETRACTED/VOID list (incl. G0-v2).
- `docs/plan3.md` · `docs/FAITHFULNESS_PROTOCOL.md` · `docs/METRICS.md` — roadmap / anti-toy protocol / metric ladder.
