# notion-3 vs coupling geometry (common ↔ differential) — Pre-Registration (theory-first, LITERATURE-GROUNDED)

> **HISTORICAL / INTERPRETATION SUPERSEDED, 2026-07-13.** Preserve the registered geometry sweep,
> symmetry controls, and run facts; do not reuse `K` as a model-free notion-3/quantum-memory certificate.
> It is a measure-all-versus-omit protocol comparison, and the paper-to-project bridge for the claimed
> DFS cause was not a direct theorem about this QEC instrument. Current authority:
> [`notion123_taxonomy_literature_closure_2026-07-13.md`](notion123_taxonomy_literature_closure_2026-07-13.md).

Status: PRE-REGISTRATION, 2026-07-05. Predictions written BEFORE the run; a miss is a finding, not a re-fit.

> **⚠ CORRECTED 2026-07-05 (BEFORE running) — the central experiment below is a MIRROR TAUTOLOGY; DO NOT run
> the φ∈[−45°,+45°] sweep on the |++> carrier.** A certified, a-exact control
> ([[project-jointparity-K-sign-blind-sx1]], `outputs/twin_validation/notion3_sign_symmetry_control.py`, GATE
> `SIGN_SYMMETRY_CONFIRMED`, sha `f4610a33`) proves **σx₁ L(r) σx₁ = L(−r)** exactly ⇒ on the σx₁-invariant
> |++> carrier the record is byte-identical under r→−r (5.6e-17) ⇒ **K(r)=K(−r), sign-blind, K=f(|r|).** So
> r=+1 (common) and r=−1 (differential) are σx₁ MIRRORS — K collapses at BOTH; §3 Outcome A (K enhanced at
> r=−1) is **FALSIFIED**. The §0 reading-note `[ours]` inferences CONFLATED the dephasing RATE (genuinely
> asymmetric in ±r — wang/hatifi/szankowski are right about the RATE) with **K (σx₁-even; the RATE papers do
> NOT govern K).** **What STANDS:** the DFS/dark-mode mechanism as the explanation of the **|r|=1** collapse,
> the Budini SUPERCLASSICAL framing (K≡DNI; r=1 = memory without invasiveness), and K=f(|r|) peaking at
> intermediate |r|. **What's DEAD:** anything predicting a differential/sign asymmetry of K on |++>. To test a
> genuine correlated-vs-anticorrelated SIGN effect you MUST BREAK σx₁ — a Bell/computational data init (the
> certified positive control: Bell init → 47% asymmetry, sign becomes visible), a σx₁-non-invariant observable,
> or a coupling not realized by a g₁ sign-flip. The corrected experiment is registered in §8 below; §1–§7 are
> retained as the (partly-superseded) RATE-vs-K grounding, read under this correction.

**Motivating data (already measured, `notion3_ancilla_mediated_prereg.md` §10):** on the faithful
ancilla-mediated joint-parity carrier with a shared bath coupling BOTH data qubits, the quantum
non-classicality K is NON-MONOTONE in r=g₁/g₀ — rises ~1.3× at r=0.25 then COLLAPSES ~178× at r=1 (symmetric),
while the record memory (M_mem/CMI) GROWS. **Question:** is the r=1 collapse a decoherence-free-subspace
(dark-mode) effect specific to the SYMMETRIC point — so a DIFFERENTIAL (r<0) coupling makes K survive/grow — or
is it a general blind-spot of the coarse joint-parity measurement (symmetry-independent)? This run answers it,
now with a quantitative, literature-grounded set of predicted outcomes. Scope: SIMULATOR record-char
faithfulness (does the quantum signature survive the real measurement, and how does it depend on coupling
geometry), NOT twin recovery.

## 0. Grounding ledger — the complete literature basis (all 精读, 2026-07-05)

| role | paper | what it grounds |
|---|---|---|
| **mechanism: DFS/interference** | wang 1409.0172 | `J_eff = J₁+J₂−2√(J₁J₂) = J₁(1−\|r\|)²`; r=1⇒0 (DFS), r=−1⇒4J₁ (bright). The quantitative K(r) form. |
| **mechanism: dark/bright modes** | hatifi 2508.07046 | geometry ⇒ symmetric mode dark at DFS node; joint-parity aligned with dark mode at r=1; `T_df∝(δd)⁻²` ⇒ QUADRATIC near r=1. |
| **mechanism: DFS only at \|g₀\|=\|g₁\|** | layden 1903.01046 | common-mode generator `H_E=Σg_jZ_j`; DFS "only in the degenerate limit \|g₁\|=\|g₂\|, in practice rare" ⇒ r=1 is special. |
| **mechanism: metastable DFS** | botzung 2506.19631 | {\|01⟩,\|10⟩} = metastable DFS under collective coupling; **differential dephasing → NO protection**; "metastable" ⇒ even r=1 imperfect (finite-lifetime residual). |
| **r-observable** | szankowski 1507.03897 | cross-dephasing `χ₁₂ ∝ g₁g₂ = r·g₀²`; r<0 ⇒ χ₁₂<0 ⇒ sign reversal ENHANCES {\|01⟩,\|10⟩} decoherence. Competing (linear) K(r) form. |
| **K = DNI (operational)** | budini 2301.02500 | **our K ≡ DNI violation `I(t,τ)=Σ\|P₃(z,x)−P₂(z,x)\|`** (identical to Milz); unitary s-e coupling generically violates DNI. |
| **superclassical** | budini 2411.13471 | **memory (C_pf≠0) WITHOUT invasiveness (I=K≈0) = "superclassical"**; K>0 needs BOTH memory AND misalignment; discord alone ≠ K>0. DNI basis-sensitive `∝\|sin(θ_Y−θ_X)\|`. |
| **classicality of dephasing** | lonigro 2211.02014 | single-qubit: classical when measurement ⊥/∥ dephasing basis (Markovian); **r=1 ⇒ joint-parity COMPATIBLE with common-mode ⇒ classical**; two-qubit collective+joint-parity = UNDONE (our gap). |
| **multi-time ≠ commutativity** | sakuldee 2204.11698 | multi-time classicality is richer than single-round commutativity ⇒ **r=1 residual K can be a genuine multi-round effect** (the observed 3.3e-4). |
| **instrument-dependence** | gherardini 2101.11662 | memory = quantum-SE + classical-outcome-feedback; **invasive measurement REDUCES memory** (⇒ the 178× collapse); TT separates the two K sources. |
| **positioning (closest prior)** | shen/QMCtwin 2606.19848 | syndrome blind-spots for correlated/coherent noise at scale (d=7), geometry-dependent — but does NOT compute K (non-classicality), NOR common-vs-differential, NOR multi-round. **Our exact gap.** |

**Novelty (multiply-confirmed vacuum):** no paper computes the QUANTUM non-classicality (K/DNI) of a
correlated bath on MULTI-ROUND stabilizer records as a function of coupling COMMUTATION GEOMETRY (common ↔
differential). lonigro (single-qubit classicality), budini (single-qubit DNI), QMCtwin (beyond-Pauli syndrome
statistics, not K), wang/hatifi (spectral DFS, no measurement/record) each own a piece; the conjunction is empty.

## 1. Mechanism (anchored) — why r=1 collapses K, five independent ways

At r=1 the coupling `∝(σz^{d0}+σz^{d1})` is the SYMMETRIC (common) mode. Five groundings agree it is special:
(i) destructive interference `J_eff=J₁(1−|r|)²→0` (wang); (ii) the symmetric mode is the DARK mode of the
system–bath coupling and the joint-parity measurement is aligned with it (hatifi); (iii) DFS exists only at
`|g₀|=|g₁|` (layden); (iv) {|01⟩,|10⟩} is the metastable DFS, broken by differential coupling (botzung); (v) the
joint-parity measurement is COMPATIBLE with the common-mode dephasing basis ⇒ DNI satisfied ⇒ classical
(lonigro/budini). ⇒ at r=1 the bath cannot invasively imprint on the measured mode ⇒ K collapses. For a
DIFFERENTIAL coupling `∝(σz^{d0}−σz^{d1})` (antisymmetric/bright mode) the alignment is broken ⇒ K should survive.

## 2. The experiment (fixed total coupling power, angle sweep — isolates geometry from strength)

Reuse the v2 faithful carrier (2 data + 1 ancilla + pseudomode, X_{d0}X_{d1} joint-parity via ancilla). Couple
the shared bath with `S(φ) = g_tot·(cos φ · σz^{d0} + sin φ · σz^{d1})`, sweep **φ ∈ [−45°, +45°]**:
- φ=0 ⇒ proxy (only d0); **φ=+45° ⇒ common** (r=+1, σz₀+σz₁); **φ=−45° ⇒ differential** (r=−1, σz₀−σz₁).
- **Fixed total power:** `Tr[S(φ)²] = 4 g_tot²` is φ-INDEPENDENT (since Tr[σz₀σz₁]=0) ⇒ K(φ) differences come
  ONLY from geometry, NOT total coupling strength (fixes the v2 confound where g₁ grew with r). Builder MUST
  assert Tr[S²] fixed across φ.

**Observables per φ (all on the ancilla joint-parity record):**
- **K** (Milz/budini-DNI: `Σ|P₃(z,x)−P₂(z,x)|`) — notion-3 invasiveness/non-classicality;
- **C_pf** (budini conditional past-future, Eq 11) — the memory axis of the DNI framework (independent of M_mem/CMI);
- **M_mem, CMI** — the classical-order memory (reused);
- N_detect for K and for the memory (feasibility).

## 3. The several possible OUTCOMES (predict-before-measure; each falsifiable, each a real finding)

Registered BEFORE the run. The run selects among A–F; more than one interpretive outcome (C/D/F) can co-hold.

- **Outcome A — DFS/interference, QUADRATIC (wang/hatifi).** `K(φ) ∝ (1−|tan φ|)²`-shaped: K MINIMUM at
  φ=+45° (r=+1, DFS), ENHANCED ~4× at φ=−45° (r=−1, bright), quadratic recovery near +45°. ⇒ the r=1 collapse
  is symmetry-specific; **notion-3 is RECOVERABLE by differential coupling.** [The DFS hypothesis; the user's bet.]
- **Outcome B — cross-dephasing, LINEAR (szankowski).** `K(φ) ∝ |χ₁₂| ∝ |tan φ|`-shaped (or the coherence-decay
  form): still min at +45°, enhanced at −45°, but the SHAPE is linear-ish, not quadratic. (A and B AGREE on
  survival/enhancement at differential; they DISAGREE on the functional form near the DFS point — the fit
  discriminates.)
- **Outcome C — SUPERCLASSICAL at φ=+45° (budini).** At the common point, `C_pf > 0` (memory present) while
  `K = I ≈ 0` (no invasiveness) ⇒ φ=+45° is genuinely Budini-superclassical (memory WITHOUT non-classicality),
  not a loss of memory. Predicted to hold regardless of A vs B; directly explains the v2 "memory grows as K
  collapses." Discriminator: report BOTH K and C_pf at every φ.
- **Outcome D — MULTI-ROUND RESIDUAL (sakuldee/botzung).** K(φ=+45°) does NOT vanish (residual, cf. the
  converged 3.3e-4) because multi-time correlations generate K even at the single-round-DNI/DFS point and/or the
  metastable DFS has finite lifetime. **Test: K(φ=+45°) GROWS with round count R** (a single-round check gives
  ~0; multi-round gives the residual). ⇒ the DFS collapse is not to exactly zero.
- **Outcome E — GENERAL BLIND-SPOT (FALSIFIES A/B, the user's hypothesis).** If K stays small / detection-
  INFEASIBLE across ALL φ including differential (φ=−45°), the collapse is a general coarse-joint-parity
  blind-spot (gherardini: invasive measurement suppresses memory), symmetry-INDEPENDENT ⇒ differential does NOT
  rescue notion-3; the joint-parity syndrome is broadly blind to the quantum signature. [The grounded competing
  hypothesis.] Signature: K(−45°) ≲ K(+45°)-order and N_detect(K) > 1e6 at all φ.
- **Outcome F — CLASSICAL-FEEDBACK artifact control (gherardini).** Any K>0 must be from quantum S-E
  correlations, NOT classical ancilla-reset feedback. The classical shared-bath arm (K=0) is re-run at EVERY φ;
  if classical-K stays ~0 across φ while quantum-K varies, F is excluded (the signal is genuinely quantum).

**Decision map:** A or B (with survival at φ=−45°, N_detect feasible) ⇒ notion-3 recoverable via geometry, and
distinguishes quadratic vs linear. E ⇒ notion-3 broadly blind on the faithful carrier (the stronger, more
sobering finding). C and D are interpretive layers (superclassical framing + multi-round residual) reported
alongside. F is the anti-artifact gate.

## 4. Independent ground truth (non-circular)

- **build_L2 GT (reuse):** the 2-qubit shared-bath reduced coherences vs the collective-dephasing closed form
  `0.25 e^{−(Δs)² Γ_unit}`, `Δs = g₀((-1)^a−(-1)^{a'}) + g₁((-1)^b−(-1)^{b'})` (v2, 6.8e-10) — re-assert per φ.
- **DFS analytic anchor (NEW, a-exact):** at φ=+45° the reduced coherence of the DIFFERENTIAL subspace
  {|01⟩,|10⟩} must be PROTECTED (Δs=0 for that sector ⇒ no decay) while at φ=−45° it decays fastest — a
  closed-form check of the dark/bright structure (wang/szankowski), independent of K.
- **classical-K null per φ** (Outcome F): classical shared-bath arm K<1e-8 at every φ.
- **no-bath sanity, extraction-GT, factorization-GT, Fock convergence, non-degeneracy** (record(φ≠0)≠proxy) — reuse v2.
- **budini cross-witness:** K (Milz) and I (budini-DNI) are the SAME statistic (Eq 9 ≡ our K_stat) — assert
  they agree numerically (a self-consistency, not an independent oracle); C_pf is the independent memory axis.

## 5. Bounded simplifications (declared; unbounded ⇒ STOP)

- **(c) 2 data + 1 ancilla single X-stabilizer** (not full d=3); Fock nmax convergence within the feasible dim
  bound (dim 8·nmax; v2 converged nmax=18) + OOM guard.
- **(c) pure σz-dephasing coupling** — the wang/hatifi DFS results are Markovian/RWA and (hatifi) energy-exchange
  (T1-type); our σz non-Markovian pseudomode may shift the EXPONENT (A vs B) — that is exactly what the run tests;
  the DFS/superclassical MECHANISM (r=1 special) is robust across the groundings.
- **(c) 3-round K** for the main sweep; the R-dependence (Outcome D) is a separate small ladder.
- **(c) CPU exact-DM**; no GPU, no concurrency.

## 6. Epistemic status (METRICS-ladder)

- **(a) exact:** Tr[S(φ)²]=4g_tot² fixed; K≡DNI `I(t,τ)` (budini Eq 9 = Milz); the DFS analytic anchor
  (differential-subspace protection at φ=+45°); classical-K null; build_L2 GT.
- **(b) bands:** which outcome (A quadratic / B linear / E blind-spot); the K(φ=−45°)/K_proxy enhancement
  (predicted ~4× if A); the superclassical C_pf(+45°)>0∧K(+45°)≈0 (C); the R-growth of the +45° residual (D).
- **(c) gates:** N_detect ≤ 1e6 feasibility; non-degeneracy; Fock convergence; classical-K<1e-8 per φ.
- **Provisional:** the Markovian/RWA groundings predict the FORM; our non-Markovian σz result is the honest one.
  Nothing built on it yet.

## 7. Build org (scouts light — reuse v2 — + builder + un-led reviewer)

Reuse `notion3_ancilla_mediated_run.py` v2 verbatim (build_L2, joint-parity extraction, K/M_mem/CMI, controls,
Fock convergence). Builder: (1) reparameterize the coupling to `g_tot(cos φ σz₀ + sin φ σz₁)` + assert
Tr[S²] fixed; (2) sweep φ∈[−45°,+45°]; (3) ADD C_pf (budini Eq 11) and assert K≡DNI-I numerically; (4) ADD the
DFS analytic anchor (differential-subspace protection at +45°); (5) the R-dependence mini-ladder for Outcome D;
(6) classical-K per φ (Outcome F). Fit K(φ) to BOTH `(1−|tanφ|)²` (A) and `|tanφ|` (B); report which. Un-led
reviewer: confirm non-degeneracy at φ=−45°, the fixed-power invariant, that K is genuine DNI not error-A, and
that the outcome assignment is honestly supported. Then serial CPU run.
