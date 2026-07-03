# T-L2 — the non-unital classical rate imitator (L2): definition, matching theorems, and the
channel-floor → record-CGF transfer question (2026-07-02, zero-compute derivations)

**Deliverable of HANDOFF_math_spine §3 T-L2** — the derivations every M3 instrument depends on
(state-confirmation §5 item 3). Inputs: Q1 (M2's imitator class is UNITAL-only — L2 inherits
nothing from M2's prescription except matching/χ-pinning + the rate-gate instrument), Q2 (P3's
power law measured on the TOTAL wedge; "c₂ pinned by γ/2" not well-posed without a transfer map),
Q3 (additivity needs the L2 instrument), the D1 correction (NO comb/record lower bounds from
channel theorems), and the A-P1-READ D3 observable owners. Epistemic classes per METRICS.md.

## 1. Definition (the L2 class)

**L2 = the pointer-basis classical rate imitator.** A piecewise-deterministic classical Markov
jump process on the qubit pointer basis, plus the classically-allowed dressing:

- **State:** a classical bit z(t) ∈ {e, g} (+ optionally a latent classical memory Y(t), see L2b).
- **Dynamics:** jump rates γ↓(t) (e→g) and γ↑(t) (g→e). **Matching prescription (the analog of
  M2's matched-BCF discipline): γ↓/γ↑ are matched to the quantum unit's direction-resolved
  TCL2 rate functions** (the same objects the M2/G-Q3-rate crash gate measures; direction-SUMMED
  intensity for the gate, directional ratio (N̄+1)/(N̄+½) is physics — inherited rule).
- **Record:** at each protocol measurement time, the record bit = z(t) ⊕ assignment noise (same
  p_M as the quantum arm). Post-measurement: no back-action on z beyond what the reading is
  (classical states are measurement-transparent).
- **Variants:** **L2a** — memoryless: (γ↓, γ↑) constants (the τ_m-window-integrated rates of the
  quantum unit's Markov point). **L2b** — latent-modulated: rates driven by a hidden classical
  process Y(t) (OU/telegraph; the Cox/doubly-stochastic class that captured the composed-code
  records in A7). Deterministic control and an additive classical Gaussian dephasing field (the
  L1 ingredients) may be composed on top; for the Z-record protocol they are inert (Thm L2-2).
- **Channel-language footprint (why "non-unital"):** the induced map on the qubit at time τ is
  the stochastic matrix T(τ) = exp(τQ), Q = [[−γ↑, γ↓],[γ↑, −γ↓]] on the diagonal sector, fixed
  point π = (γ↓+γ↑)^{-1}(γ↑, γ↓) ≠ I/2 — exactly the non-unital affine term L1 cannot produce
  (Landau–Streater via Crow–Joynt for the qualitative obstruction; A-M1-1 attributions apply).

(c)-choice declared: jumps go to the poles (full reset). This is what makes the population
process exactly Markov-telegraph; partial-jump classical models trade population matching for
coherence matching and are outside L2 (they belong to L3's bounded-memory HMM class).

## 2. Matching theorems (what L2 can and cannot match)

**Theorem L2-1 (exact record equivalence at the Markov point). (a)**
*For the Z-pointer-basis record protocol (projective qubit measurements every τ_m, no coherent
probing between measurements), the FULL record law — all orders, all conditional statistics — of
the memoryless quantum unit (GKSL amplitude-damping/absorption channel at rates γ↓, γ↑; the
mode-reset-per-round construction) is IDENTICAL to L2a's telegraph record law with per-window
transition matrix T(τ_m).*
*Derivation.* Post-measurement states are pointer states (diagonal). Between measurements, a GKSL
generator with only σ± dissipators evolves the diagonal sector autonomously by the rate equations
(coherences never feed populations for diagonal inputs), i.e., by T(τ_m); the measurement reads
the diagonal and re-prepares a pointer state. The record is therefore a Markov chain on {e,g}
with kernel T(τ_m) ⊕ assignment noise — which is precisely L2a. ∎
**Corollaries.** (i) **The quantum unit's declared memoryless null ≡ L2a at the record layer**
(one construction serves both; the structure lemma does not cover the quantum unit — this is its
declared replacement, with the (c)-bound that "memoryless" means mode-reset-per-round).
(ii) **Any nonzero record wedge vs matched L2 is attributable to MEMORY (mode-mediated), never to
non-unitality** — the rates already carry the non-unital fixed point.
(iii) **The L2-differencing instrument is theorem-grounded:** Δ(q vs L1) − Δ(q vs L2) isolates
the non-unitality component (present in the L1 comparison, absent in the L2 comparison);
Δ(q vs L2) isolates the beyond-classical-rate memory component. This replaces the ill-posed
c₂-pin (see §3). Endpoint calibration: at the motional-narrowing/Markov operating point,
Δ(q vs L2a) = 0 identically — a built-in null the M3 prereg must register as a crash gate
(the analog of D_comb(R=1) ≡ 0).

**Theorem L2-2 (coherence sector: inert for this record; the honest scope line). (a)**
*The Z-record protocol never prepares or reads qubit coherence (pointer-state re-preparation each
window); therefore NO record statistic of this protocol can distinguish models that differ only
in the coherence sector.* Consequences: (i) the PDMP's factor-2 coherence mismatch — a classical
jump process at population rates Γ = γ↓+γ↑ destroys coherence at rate Γ (survival = no-jump
probability e^{−Γt}) while the quantum channel decays it at Γ/2 — is REAL at the channel level
(it is the coherence-sector face of the γ/2 floor) but INVISIBLE to this record. Scrutinize-
vacuous-checks discipline: the M3 prereg must NOT register a coherence-based kill criterion for
L2 on this protocol (it could never fire); coherence-sector claims need a different instrument
(process tomography / Ramsey insertions = active control, outside the passive record).

**Proposition L2-3 (the P4 sign is NOT an L2 discriminator). (a)-direction**
The measured P4 companion (conditional flip excess after an observed ↓ flip: quantum −4.06e-2 vs
L1-classical +3.30e-3) does not separate q from L2: the telegraph reproduces the negative sign.
*Derivation.* After an observed e→g flip the L2 state is g; the conditional next-window flip
probability is [T(τ_m)]_{g→e} = (γ↑/Γ)(1−e^{−Γτ_m}), while the stationary unconditional flip
probability mixes the larger e→g channel: π_e[T]_{e→g} + π_g[T]_{g→e}. At N̄ → 0 (γ↑ → 0) the
conditional-post-↓ probability → 0 while the unconditional stays O(γ↓π_e) — a NEGATIVE
conditional excess of the same sign as the quantum unit's emission anti-bunching. ∎
**M3 consequence (prereg de-risk):** register P4 as an L1-only discriminator (its sign kills the
Gaussian-field imitator, not the rate imitator); the anti-bunching physics is owned
(Plenio–Knight — cite) and its record shadow is classically-rate-forgeable. Any P4-based
"quantum" language must be conditioned on the imitator class named.

**What survives against L2b (the honest wedge). (b)-direction, registered language**
The quantum record law is a quantum hidden-Markov model (qubit⊗mode jointly Markov, mode
unobserved). L2b is the classical hidden-Markov/Cox class at matched rate functions. The wedge
Δ(q vs L2b) is therefore a quantum-vs-classical HMM expressiveness gap at matched local
statistics — expected-positive (b), NEVER theorem-guaranteed at the record layer (D1 correction:
contractivity gives no lower bound; fold attenuation measured ~O(10²)). Expected ordering, to be
registered as a (b)-band: Δ(q vs L1) > Δ(q vs L2a) > Δ(q vs L2b) ≥ 0 at the non-Markov operating
point, with Δ(q vs L2a) → 0 at the Markov point (Thm L2-1 null).

## 3. The channel-floor → record-CGF transfer question (Q2 closed by declaration + instrument)

**(i) No-go (direction of theorems). (a)** Data processing/contractivity runs the WRONG way for
the needed bound: composing both arms with the identical record machine can only SHRINK trace
distance, so the γ/2 CHANNEL floor implies NO lower bound on any record-CGF distance — at any
resolution (the D1 correction, now standing). Upper bounds exist (D_rec ≤ D_comb ≤ per-window
channel distances by chaining) but are the uninteresting direction for a floor.

**(ii) Declaration (the registered resolution).** The c₂ coefficient of the record-wedge
expansion **FLOATS** — no pin from the γ/2 value is claimed. The registered consistency check
replacing it: **γ/2-scaling** — the L1-attributed floor component (measured via the
L2-differencing instrument of Thm L2-1(iii)) must scale linearly with the channel non-unitality
(1−e^{−γτ})/2 ≈ γτ/2 as γ is varied at fixed protocol (a (b)-band on the SLOPE direction/
linearity, not on the constant).

**(iii) The instrument that replaces the pin.** c₂-content is MEASURED, not derived:
Δ(q vs L1) − Δ(q vs L2) across the g-ladder = the non-unitality (floor) component's record
footprint; its γ-scaling is the consistency check; its additivity with the memory component is
Q3's check, landing free in the same runs (same record protocol, one extra arm per point).

## 4. Register-ready consequences for the M3 prereg (checklist deltas)

1. L2 defined as §1 (L2a + L2b); matching = TCL2 rate functions + rate crash gate (direction-
   summed; directional ratio = physics); jumps-to-poles declared (c).
2. Crash-gate null: Δ(q vs L2a) = 0 at the Markov operating point (Thm L2-1) — the record-layer
   analog of D_comb(R=1) ≡ 0.
3. L2-differencing = the primary component separator (theorem-grounded attribution); g-ladder =
   corroboration; c₂ floats with the γ/2-scaling (b)-check (§3.ii).
4. P4 = L1-only discriminator (Prop L2-3); no coherence-sector kill criteria on the Z-record
   (Thm L2-2; vacuous-check discipline).
5. The quantum memoryless null = mode-reset-per-round ≡ L2a record law (one construction, both
   roles; declared bound: "memoryless" = per-round reset).
6. Expected-positive (b) ordering Δ(L1) > Δ(L2a) > Δ(L2b) ≥ 0 registered as bands, never as
   premises; all wedge claims carry the imitator-class name.

*Zero-compute deliverable; no runs. All (a) items are short derivations reproduced above; (b)/(c)
items are declared for M3 registration.*

## Amendment A-L2-1 (2026-07-03, after the un-led Fable review — 4 MAJOR findings accepted in
full; supersedes the flagged statements above; reviewer evidence `outputs/review2_l2_findings.md`
+ probe `outputs/review2_l2_p3_check.py`)

1. **Matching prescription REDEFINED (kills the O(g⁴) confound).** L2 matching = **exact
   per-window kernel matching**: a = P(e→g), b = P(g→e) over one τ_m window matched to the
   quantum unit's true window kernel (measurable/computable; realizable as exp(τQ) whenever
   a+b < 1). TCL2 rates are downgraded to interpretation. Reason (reviewer, verified): the
   mode-reset JC record IS exactly a 2-state Markov chain at any (g, κ), but its kernel equals
   exp(τ_m Q_TCL2) only to O(g²) — TCL2-matching leaves an O(g⁴) mismatch, the SAME order as the
   memory signal. Under kernel matching, Thm L2-1's Cor. (i)/(ii) and the Markov-point crash-gate
   null become true identities; under TCL2 matching they are approximations and the null can fire
   spuriously. M3 registers the null on the kernel-matched arm.
2. **Differencing attribution DEMOTED.** Cor. (iii)/§3(iii): theorems ground CONTAINMENT only
   (L2 carries the non-unital fixed point; L1 cannot). The subtraction Δ(q,L1) − Δ(q,L2)
   isolates the non-unitality component only under additivity — which is Q3's MEASURED check,
   not a theorem (and L1/L2 differ additionally in temporal class: Gaussian field vs telegraph).
   Register as "theorem-grounded containment + measured additivity".
3. **Prop L2-3 REGIME-CONDITIONED (and partially reversed — good news for M3).** The derivation
   above computes the TRUE-flip statistic (sign correct universally, excess = b(b−a)/(a+b) < 0).
   The P4 companion conditions on an OBSERVED flip: with assignment noise the observed-flip
   excess flips POSITIVE in the sticky regime (a,b ≪ p_M: excess → (1−2p_M)(π_e − p_M);
   reviewer-verified exactly), and at the probe's N̄ = 0 point the matched L2a is degenerate
   (p_M = 0 ⇒ conditioning event has probability 0; p_M > 0 ⇒ excess = p_M(2p_M−1) < 0 with
   magnitude ≤ p_M) ⇒ **the measured quantum −4.06e-2 is unreachable by matched L2a unless
   p_M ≥ 4.4e-2 — P4 RETAINS magnitude-level q-vs-L2a discriminating power at N̄ = 0.**
   *[Errata per review round 3 (R6), registered in A-T3-1 addendum 3 item 8: exact threshold
   = 4.4574e-2 (the 4.4e-2 was an under-converged iterate; conclusion strengthened); the
   sticky-regime POSITIVE sign additionally requires π_e > p_M (the limit formula itself is
   exact); Q/π in the column-stochastic convention; the lift list read as RATES (Γ, Γ/2, ∞).]*
   "P4 = L1-only discriminator" is replaced by: P4 sign kills L1; P4 magnitude vs L2a is a live
   (b)-band instrument in the flip-dominated/N̄=0 regimes, dead in the sticky regime. (The
   N̄→0 "→0 while stays" contrast in the old derivation was broken — both vanish at Θ(γ↑),
   ratio → Γ/2γ↓; negativity follows from b < a alone.)
4. **Hypotheses STATED.** Thm L2-1/L2-2 require **[H, Π_z] = 0** (pointer-diagonal Hamiltonian —
   Lamb/Stark σ_z fine; any transverse drive breaks diagonal-sector autonomy and the theorems)
   and **classification-only measurement noise** (i.i.d. record flips, no back-action,
   post-state = true-outcome pointer state). The JC-elimination setting satisfies both; M3
   inherits them as declared preconditions. Ancilla-mediated partial-collapse readout is outside
   the theorem (declarable separately if needed).
5. **Minor corrections:** §1 Q/π ordering fixed — in the (e,g) ordering Q = [[−γ↓, γ↑],[γ↓, −γ↑]],
   π = (γ↑, γ↓)/Γ; §3(i) chaining reads D_rec ≤ D_comb ≤ Σ_r (per-window channel distances);
   the "factor-2 coherence mismatch" of Thm L2-2(i) is LIFT-DEPENDENT (no-jump-branch lift
   e^{−Γt}; GKSL jump-operator lift Γ/2; incoherent embedding ∞) — tag (c), cite M2's exact
   theorem for the channel-level statement; "directional ratio (N̄+1)/(N̄+½)" = γ↓/(Γ/2)
   (not detailed balance) — named explicitly.
6. **Upgrade (reviewer positive finding):** the §3(i) no-go is SELF-WITNESSED — Thm L2-2's own
   construction exhibits model pairs with channel distance ≥ the γ/2 floor and record distance
   exactly 0, so "no record lower bound from channel floors" is a theorem with an explicit
   witness, not a direction observation.

Checklist §4 items 2, 3, 4(first clause), 5 are superseded accordingly. Reviewer verdict:
all four results CORRECT(-WITH-HYPOTHESIS-GAP) in their intended domain; document
SOUND-WITH-FIXES; fixes = this amendment.
