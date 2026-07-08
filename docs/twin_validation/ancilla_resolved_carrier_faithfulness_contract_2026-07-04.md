# Faithfulness contract — per-round ancilla-SPAM extension of the dense Axis-1 carrier (2026-07-04)

**Status: CONTRACT for un-led review, 2026-07-04. NO `src/**` code until this is un-led-reviewed +
user-approved (user point 0; [[feedback-anti-toy-ground-truth-protocol]] rule II).** This is the first
deliverable of the ancilla-resolved-carrier build. It is a **contract**, not code: the physical theorems the
extension must satisfy + a falsifying test each (§3), the independent-GT plan (§4), the regression anchor
(§5), the bounded simplifications (§6), and the predict-before-measure gates (§7).

## 0. What is being built (and what is NOT) — scope

**Object:** make the dense Axis-1 carrier's **existing** ancilla SPAM **per-round source-modulated** (it is
currently held at the trajectory MEAN, S-1), and **wire the deferred `cz_depol_p`** (Class-2) into the CZ
gate — so the shared source imprints **Class-1 (ancilla SPAM)** and **Class-2 (CZ)** errors per round. Then
run the **notion-2 gate** (classical multi-time memory, the passive-record legitimacy signal for the classical
source) on it.

**Dual-purpose (evidence-backed, `quantum_backaction_c4analog.py` v2):** the passive-record twirling
condition is **incoherence** — the classical 1/f source → **notion-2 ceiling**; a **quantum/coherent bath**
survives via its complementary stabilizer on the **same** carrier. So this plumbing (per-round SPAM +
ancilla-aware exact-DM oracle) is the plumbing the quantum-dephasing headline (source-swap to a
pseudomode/GKSL bath) needs too — NOT wasted.

**Architecture decision (3-agent read-only map, 2026-07-04):** build on the **dense Axis-1 carrier**
(`CoupledCycleTeacher` + `axis1_record_evidence.py`), which ALREADY has explicit ancilla + real projective
`measure_qubit_enumerate` + real reset + `Axis1ReadoutResetInstrumentSpec` SPAM. **NOT** the MCWF/MPS carrier
(implicit parity projection, NO ancilla → Class-1 infeasible, bond 243→20000). No carrier rebuild.

**Minimal-faithful scope (user point 2):** d3, **data + ancilla, qubit-level**. Class-1 (ancilla SPAM,
Kam's main-catastrophic) PRIMARY; Class-2 (CZ depol, `cz_depol_sensitivity` already in config) SECONDARY.
**DEFERRED (declared, NOT in this build):** leakage / qutrit (ADR 0010 axis); d5/d7; the quantum-bath source
swap (the headline follow-on); the notion-2 gate's own internals (a separate contract). Over-build is the
project's repeated trap — this contract is the plumbing only.

## 1. The constraint ledger — physical theorems + a falsifying test each (rule II)

Each row: the theorem the extension MUST satisfy, and the committed test that would FALSIFY it. Written
BEFORE the code. "PASS" = the falsifying test does not fire on the built extension.

| # | Physical theorem (MUST hold) | Falsifying test (committed) |
|---|---|---|
| **T1** | **Projective ancilla measurement is Born-rule exact.** The per-round ancilla readout is a genuine projective measurement (`measure_qubit_enumerate`, branch enumeration), NOT a marginal/effective flip. | Feed a known 1-ancilla fixture; assert the enumerated branch probabilities equal the analytic Born probabilities `tr(P_s ρ)` to 1e-12; a wrong (marginal) measurement diverges. |
| **T2** | **Reset is a real CPTP reset channel** on the ancilla (prepare-basis flip after ideal reset), not a deterministic re-prep that discards the SPAM. | Set `reset_flip_p=0.3`; assert the post-reset ancilla density matrix = `(1−p)|0><0| + p|1><1|` (a real mixed reset), exact; `reset_flip_p=0` → pure `|0>`. |
| **T3** | **Per-round SPAM is a genuine per-round source modulation**: `readout_flip_p(r)`, `reset_flip_p(r)`, `cz_depol_p(r)` each vary with the round `r` via the shared source `Θ(z_r)` — NOT a per-trajectory constant. | Emit with a source whose `z_r` has a known per-round pattern; assert the effective per-round SPAM tracks `Θ(z_r)` round-by-round (not the trajectory mean); a mean-only path gives a flat series (FAIL). |
| **T4** | **The composed per-round channel is CPTP** (each substep + the assembled cycle). | Choi-matrix eigenvalue check `≥ −1e-12` + trace-preservation `tr_out = I` to 1e-12, on every substep and the full cycle, at random source draws. |
| **T5** | **Information–disturbance / no-signalling from the future:** a round-`r` measurement outcome cannot depend on a round-`r'>r` operation (causality). | The DM-replay `round_pre(eng,r)` applied in place must give round-`r` detector marginals independent of any later-round parameter; permuting a future round's SPAM leaves round-`r` marginals invariant to 1e-12. |
| **T6** | **Clifford/detector-invariant ≠ dynamics-invariant:** a Clifford frame change (or a detector-fold relabel) that leaves the syndrome geometry invariant must NOT be used to drop a physically-applied SPAM/CZ channel. | The corrupt-stabilizer control (X↔Z flip of stab j) MUST make the ground-truth mismatch FIRE (a dropped channel would leave it inert = FAIL). |
| **T7** | **Detector-fold / round-map is derived, not assumed:** `D_{c,r} = m_{c,r−1} ⊕ m_{c,r}` with the first-round-raw + interior-XOR fold, bit-for-bit; no stale `round_index` field. | Reproduce the fold from the raw ancilla measurement stream in a from-scratch numpy reconstruction; assert bit-identical to the carrier's `det` cube. |
| **T8** | **Class-2 CZ depol acts on the data–ancilla PAIR at the CZ**, not folded into a data marginal. | `cz_depol_p=0.1` must change the RR_CORR / detector marginals in the way an exact 2-qubit-depol-after-CZ does (matched to the exact-DM oracle); a data-only marginal fold diverges. |

## 2. Numerical-trap pre-embedding (user point 6, [[feedback-carrier-transition-numerical-traps]])

Each is a committed falsifying test in the ledger BEFORE running, not a run-time discovery:
- **N1 detector-fold / round-map** — T7 (the dead-`round_index` trap): from-scratch fold reconstruction.
- **N2 Kraus norm-bleed** — assert `Σ_k K_k† K_k = I` to 1e-12 for every applied Kraus set (SPAM, CZ depol,
  reset) at random draws (norm-bleed from an unnormalized Kraus set is a silent CPTP break → caught by T4 + this).
- **N3 measurement branch-count** — the enumerated branch tree is `2^(#measured ancilla)`; assert the branch
  count + total probability = 1 exactly (a mis-folded projector loses/duplicates mass).
- **N4 LPDO/positivity** — not applicable to the dense DM path (exact DM, no LPDO); if any reduced-DM is
  formed, assert Hermitian + eigenvalues `≥ −1e-12`.
- **N5 (MCWF √N)** — N/A here (dense DM, no MCWF); flagged only because the quantum-bath source-swap follow-on
  would use it — declared out of THIS build.

## 3. Independent ground truth (rule I) — reuse, do not rebuild (§4 of the oracle map)

The extension is certified against ground truth INDEPENDENT of the carrier's own code:
- **Ancilla-aware exact-DM oracle** (`AncillaAwareDMOracleAnchor`, ~180 LOC, NEW; mirrors `dm_oracle.py`):
  dual-register `(n_data, n_ancilla)` exact DM. **Feasibility (declared):** 1 ancilla `3^10≈27 GB` @ R=1
  feasible; 2 ancilla `3^11≈81 GB` OOM ⇒ **sub-register / ≤1-ancilla exact-DM** (rule-III bound, §6). This is
  the DM-replay GT for T1–T8.
- **Stim Clifford slice** (`StimCliffordAnchor`, REUSE): the Pauli part of Class-1 (ancilla-SPAM bit-flip) +
  the XZZX wiring/seam-fold check — an INDEPENDENT executable (separate simulator).
- **Closed-form** (`closed_form.py` `E[d_r d_{r+1}]=p01 p10`, REUSE / extend to a 4-state data⊗ancilla chain):
  analytic RR_CORR cross-check.
- **QuTiP `mcsolve`** (continuous part; OPTIONAL, for the Class-2 CZ continuous check) — deferred unless T8
  needs it.
- **Controls-first anti-vacuity** (`certify_cells`, REUSE): inert control ⇒ FAIL; zero-firing ⇒ FINDING.
  NEW control `CorruptAncillaControl` (~45 LOC): flip ancilla-readout bit `j` in the GT ⇒ MUST fire (T6).
- **From-scratch record oracle** (numpy embedding/projectors/reset-Kraus/XOR) for T7 — shares NO code with
  the carrier.

**Anti-circularity:** the DM oracle is a DIFFERENT code path (branch-tree DM, not the record-evidence
emitter); the Stim slice is a DIFFERENT executable; the from-scratch fold shares no code. No check is against
the carrier's own emitter.

## 4. The regression anchor (user point 3) — a HARD gate

**In the Class-0-only limit — SPAM/CZ source-modulation OFF (readout/reset at the committed trajectory-mean,
`cz_depol_p=0`) — the extended carrier MUST reproduce the CURRENT dense carrier bit-for-bit** (byte-identical
`det`/`obs` cubes at a fixed seed) OR to a declared bounded regression (if a refactor reorders floating ops).
This guarantees the extension does not move the **G2-certified Class-0 behavior**. Committed test: emit the
5q fixture at a fixed seed on old vs new; assert identical (or bounded) — a HARD gate, blocks merge on failure.

## 5. Bounded simplifications (rule III) — declared + error-bounded; unbounded ⇒ STOP

- **S-1 → per-round (the extension itself):** the OLD carrier holds SPAM at the trajectory mean; the new one
  makes it per-round. The trajectory-mean limit is recovered exactly (the regression anchor §4). No unbounded
  approximation — this is a REFINEMENT, not a simplification.
- **Class-1 exact-DM scale bound (HARD):** ancilla-aware exact-DM is feasible only at **small fixtures / ≤1–2
  ancilla** (3^10 feasible, 3^11 OOM; full-d3 9+8=17 qutrits ≈ 10^32 GB dead; MCWF/MPS has NO ancilla). ⇒
  **Class-1 is a small-fixture, exact-DM-certified claim; it does NOT scale via the current carriers.** Class-2
  (CZ) scales on both. Declared, not hidden.
- **Multi-qubit stabilizer twirl (for the quantum-headline follow-on, NOT this build):** the C4-analog toy
  measured a single qubit in σx; the multi-qubit ancilla-mediated stabilizer measurement is a stronger twirl —
  survival of the quantum signature there is the deepen check, out of THIS contract.
- **Leakage / qutrit + d5/d7:** DEFERRED (ADR 0010 axis; over-build guard).

## 6. Predict-before-measure gates (the extension's own acceptance)

Registered BEFORE building; each is (a) exact / (b) band / (c) gate:
- **G-T1..T8 (a-exact):** every ledger falsifying test does NOT fire (T1–T8 hold). BLOCKING.
- **G-REG (a-exact):** the Class-0 regression anchor (§4) is bit-identical / bounded. BLOCKING.
- **G-CTRL (c):** `CorruptStabControl` + `CorruptAncillaControl` FIRE (controls-first anti-vacuity).
- **G-PLANT (c, positive control, user point 7):** a PLANTED notion-2 memory (a known per-round source
  correlation) injected via the extension MUST be detected by the notion-2 gate — built in from the start,
  not bolted on.
- **G-CLASS12 (b):** Class-1 (per-round ancilla SPAM) and Class-2 (CZ depol) each move the record statistics
  in the direction the exact-DM oracle predicts (matched, within the DM feasibility band).

## 7. Build organization (user point 8) — for AFTER this contract is approved

≥3 disjoint-ownership builders + un-led reviewer ([[feedback-heavy-tasks-multi-agent]]); reviewer gets
problem+goal+artifact only ([[feedback-reviewer-no-leading]]). Disjoint ownership (revised for the
no-rebuild reality):
- **(A) per-round SPAM plumbing:** `Axis1ReadoutResetInstrumentSpec` → per-substep callable; `Θ(z_r)` →
  per-round readout/reset; wire `cz_depol_p` into the CZ.
- **(B) ancilla-aware oracle + controls:** `AncillaAwareDMOracleAnchor` + `CorruptAncillaControl` + protocol
  field `n_ancilla`.
- **(C) notion-2 gate integration + the planted positive control + the regression/ledger test harness.**
Scripted-execution ([[feedback-scripted-execution]]); GPU serial, offload heavy to `ssh spark`; H6 (every
`src/**`+`tests/**` change user-confirmed BEFORE commit); regenerate CODE_MAP after any src change; pytest
scoped to `tests/`.

## 8. What the reviewer should attack

- Is any ledger theorem (T1–T8) a **tautology** (true by construction, cannot fail)? Propose the strongest
  non-vacuous form.
- Is the ancilla-aware DM oracle genuinely INDEPENDENT of the carrier's emitter, or does it share a blind
  spot (rule I)?
- Is the Class-0 regression anchor (§4) actually bit-identical-testable, or will floating-point reordering
  make it vacuous?
- Is the Class-1 small-fixture scale bound honestly stated, or does it get quietly relaxed?
- Does the planted positive control (G-PLANT) exercise the REAL notion-2 statistic, or a strawman?
