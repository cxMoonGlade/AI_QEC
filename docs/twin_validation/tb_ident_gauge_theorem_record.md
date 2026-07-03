# T-B record — the identifiability/gauge theorem for passive detector moments (2026-07-02)

**Tracked record for the headline-#1 deliverable** (HANDOFF_math_spine §3 T-B). The full theorem
statements + proofs live in the (gitignored, local-only) paper draft
`docs/coupling_simulator_intro_draft.tex`, section `sec:ident-gauge` ("The identifiability–gauge
theorem: what passive detector moments reveal, and provably conceal, about a continuous noise
covariance"), inserted after `sec:structure-lemma`. The verification script is
`outputs/tb_ident_gauge_verify.py` (gitignored outputs/ per repo convention; script + log are the
local audit trail). This tracked doc records: the theorem inventory, the epistemic classes, the
registered (a)-exact verification bets (BEFORE the run), and the run results (appended after).

## Positioning (cite-don't-claim; adjudication B.1 [PROVISIONAL] no-owner)

Transport of the learnable-vs-gauge QUESTION AND PROGRAM (Chen 2206.06362 — 精读 note
`chen_learnability_pauli_noise_2206.06362.md`; Zheng 2601.22286) to a **continuous spacetime
Gaussian covariance Σ read by PASSIVE stabilizer detectors**. ⚠ PRECISION (penetration audit,
2026-07-03; supersedes "lift of the duality" shorthand): this is an ANALOGY, not an inheritance —
(1) noise classes are DISJOINT (Chen/Zheng = stochastic Pauli; coherent errors outside their
formalism by their own scope notes; ours = coherent-per-realization Gaussian dephasing);
(2) access classes differ (their all-experiments/active vs our one-fixed-passive-machine);
(3) completeness is ONE-SIDED here: gauge group proven + Lemma-A reduction proven; the full
learnable⊕gauge dichotomy is certified per finite instance only and is [O] open in general
(PAIR1 corank-6 Σ-dependent null). Remm 2502.17722 = a DIFFERENT OBJECT CLASS (discrete Bernoulli
error-event probabilities from syndrome correlations, no inversion correspondence to continuous
Σ); Paz-Silva 1609.01792 / von Lüpke 1912.04982 = continuous-Σ via ACTIVE control. The duality
concept is cited, never claimed; the continuous-Σ × passive-moment map is the contribution.
All ownership positioning [PROVISIONAL].

**✔ COVERAGE GAP RESOLVED (精读 completed 2026-07-03; verdicts STAND):**
arXiv:2511.16772 (Montañà-López, Elben, Choi, Trivedi, Nov 2025) was missed by the
adjudication's 6-axis search; the mandatory 精读 is done —
`docs/papers/reading_notes/montanalopez_nonmarkovian_learning_manybody_2511.16772.md`.
Text-grounded findings: access = ACTIVE designed experiments (chosen product ρ_S +
mid-evolution single-qubit-Clifford layer W + chosen product observables + short-time
time-traces, ONE terminal measurement per shot — no mid-circuit measurements); objects =
kernel Taylor data K^(m)_ab(0) (Prop 1) / quasistatic coefficient covariance Σ_ab incl.
all-to-all (Prop 2); estimators = unconstrained entrywise sup-norm (NO PSD/Bochner
constraint — 0 body hits); NO gauge/unlearnability content (0 hits); NO QEC content (all
syndrome/stabilizer/EC hits are bibliography lines). **B.1 no-owner verdict STANDS** —
they answer "what CAN designed experiments learn," never "what is provably invisible to
one fixed passive machine's record moments"; their own finding that Im[K_cc] is invisible
at W=1 and restored by inserting W is a published instance of
access-class-determines-visibility that CONCRETIZES our thesis. **#3.1 no-owner verdict
STANDS** — no PSD-constrained estimation, no QEC data; they join #3's baseline table as
the unconstrained many-body Gaussian-kernel comparator. Positioning duty: cite as the
third corner alongside Chen (discrete Pauli/active/duality) and Zheng (syndrome
N&S/Pauli): continuous Gaussian kernels/active/positive protocols — the continuous-Σ ×
passive-fixed-record × gauge-characterization conjunction remains NO OWNER. The queued
involuntary-W derivation check is **RESOLVED (2026-07-03,
`involuntary_w_check_2026-07-03.md`, 16/16 gates):** the schedule's own operations CANNOT
mimic their Case-3 W even partially at linear order — **Prop IW-1** (realness/parity
symmetry) forces the passive record to be EVEN in the commutator (Im-K) sector;
outcome-discarded moments are EXACTLY classical (cosh law, machine-verified ≤ 1.3e−13);
the only quantum imprint is quadratic (W₁₂ ≈ −8κ², cross-window commutator integrals,
outcome-resolved cross moments only). Their Case-3 W = S·H is COMPLEX — design freedom
buys exactly the complex structure linear commutator access requires; real passive
machines provably cannot. "Invisible" language survives with the class × access × order
scope made explicit; registered v1 bet P2 was falsified and repaired stronger (A-IW-1).

## Setting

The structure-lemma machine: n data qubits, X-type stabilizer group S (support group
V_S ≤ F₂^n), R rounds; per round: classical Gaussian Z-phases φ (joint covariance Σ over nR legs)
→ background Z (p_Z) → stabilizer parity measurement (assignment flip p_M) + reset; entry
|+⟩⟨+|^⊗n; exit = trace (syndrome-only) or transversal X readout (flip p_F). Access class =
PASSIVE: the fixed machine's record (m, x) only — no mid-circuit control, no design freedom.

## Theorem inventory (epistemic classes)

| # | Statement (tex paragraph) | Class |
|---|---|---|
| R0 | Continuum→Gram reduction: the record law depends on the continuum kernel only through the nR×nR window Gram matrix Σ; sub-window/out-of-band structure is concealed before any circuit algebra | (a) proven |
| LA | Probe calculus: every Walsh character W(u,χ) of the record = dressing × Σ over grade paths with DETERMINISTIC supports σ_r(u,χ) = χ ⊕ ⊕_{r'≥r} supp(g_{u_r'}), of nonneg machine coefficients × Gaussian CF evaluations e^{−½âᵀΣâ}. Passive analog of Chen App-D completeness | (a) proven |
| C1 | Window locality + order↔reach ladder: a moment sees only Σ-entries inside its windows; detector moments = closed bounded windows (exactly stationary/local); bare-m characters = entry-anchored (parity-walk nonstationarity, exact); rep-code spatial reach of order-j = qubit distance j | (a) proven |
| T1 | Universal sign gauge: Σ ↦ S_W Σ S_W (per-qubit re-signing, all legs) leaves the ENTIRE record invariant, all orders, both exits (X_W-conjugation symmetry). Identifiable sign content = loop products only (continuous analog of cycle space; per-qubit signs = cut-space analog). Broken by active control — the passive/active boundary | (a) proven |
| T2 | Order-1 law: E[(−1)^D] = (1−2p_M)²(1−2p_Z)^w · 2^{−w} Σ_{a∈{±1}^w} e^{−½aᵀΣ_win a} (hypercube-averaged CF; w=2 → cosh). Consequences: (a) sign blindness at order 1; (b) cosh ≥ 1 ⇒ detection rate DECREASES under within-window covariance of either sign — the quieter-scissors direction is analytic, and O(C²) explains the record-layer s²-dilution arithmetic | (a) proven |
| P3 | Order-2: lag-≥2 same-stabilizer pairs are cross-window sign-blind (coefficients factorize uniform); lag-1 contiguous pairs: relative-sign visibility is machine-specific — V_S restricted to the window support = {00,11} (single-stabilizer unit) preserves it (sinh visible), = all four patterns with uniform count (repetition-code interior) ERASES it exactly (measurement-induced erasure). Counting argument: #{h ∈ S: h flips pattern δ on the window} uniform ⇔ erasure | (a) proven (counting), [C] certified |
| P4 | Syndrome-only concealment: χ=0 windows live in V_S; logical-coset windows (the silent-floor functional) open only at readout. Whether syndrome-window closure determines the logical-window CF VALUE = machine-specific completeness (rank certificate; open in general) | (a) + [C] + [O] |
| RC | Finite-instance rank certificates on the tier-0 units (analytic Jacobian of all characters w.r.t. Sym(nR)) | [C] computed |

Honest deltas kept in the statement: (i) unlearnability is relative to the DECLARED passive
access class (Chen's quantifies over all experiments — active); (ii) gauge exhibits VALID
covariances (congruences preserve PSD); (iii) finite-R moment COUNT can bind before the form-span
does (rank ≤ #characters − 1) — ranks are reported, never assumed.

## Registered verification bets ((a)-exact; committed BEFORE the run; every invariance paired with an ALIVE control)

Script: `outputs/tb_ident_gauge_verify.py`. Machine side = brute-force record law (grade-path
enumeration over the tier-0 graded round pieces; entry/readout contracted; norm asserted = 1).
Theorem side = the closed forms above. Tolerances: equality 1e-12, invariance 1e-13, ALIVE > 1e-8.
Units: PAIR1 (1 stab / 2 qubits, R=3,4), PAIR2 (2 stabs / 3 qubits, R=2 dense; R=3 char-direct).
Constants p_M=0.011, p_F=0.007, p_Z=0.0034 all nonzero (dressing exercised).

- **V1** order-1 law exact: interior detector (window = leg 1 block) on PAIR1 + both PAIR2
  stabilizers × 3 random PSD Σ each; boundary detector (leg-0 window, single (1−2p_M) dressing).
- **V2** locality: outside-window perturbations (leg 2 cross + leg 0 diag) move the detector
  moment by exactly 0; inside-window perturbation moves it (ALIVE).
- **V3** sign gauge: full character table invariant under S_W Σ S_W for every nonempty qubit
  subset W (PAIR1 R=3, R=4; PAIR2 R=2); converse ALIVE: a single cross-entry sign flip (not a
  gauge element) moves some character.
- **V4** temporal-sign ladder: lag-2 same-stab pair (PAIR1 R=4, windows legs 1&3) invariant under
  cross-window block sign flip + magnitude-ALIVE; lag-1 contiguous pair (windows legs 1&2):
  PAIR1 moves under interior relative-sign flip; PAIR2 interior (R=3, char-direct) exactly
  erased + magnitude-ALIVE.
- **V5** rank certificates: registered (a)-parts only — (i) the syndrome-only Jacobian null space
  CONTAINS the per-leg (V_q − V_q′) diagonal directions (proven: all syndrome-only windows carry
  both support qubits, a² ≡ 1 on support); (ii) a-priori bound rank ≤ min(#chars−1, dim Sym).
  Ranks themselves are REPORTED (finite-character binding is real; no unproven rank is gated).
- **Route consistency**: dense record-law route vs memory-lean char-direct route agree on a
  PAIR2 character (two implementations, one number).

## Amendment A-TB-1 (2026-07-02, after run 1 — a registered sub-claim FALSIFIED by the machine;
theorem STRENGTHENED; documented before the rerun)

**Run-1 verdict: 1 FAILURE out of 30 checks — `V4 lag-1 relative sign VISIBLE (PAIR1)`: the
machine gives |dW| = 0.00e+00 exactly** (all other checks passed at 1e-16-scale; log
`outputs/logs/tb_ident_gauge_verify.log`). My Prop-3 sub-claim (single-stabilizer unit preserves
lag-1 relative signs, sinh-visible) was WRONG: the interior h-sum weights the aligned flips
±uniformly, so the lag-1 moment is cosh-factorized (even) too.

**Root cause + corrected theorem (rederived, then re-verified):** the true gauge group is LARGER
than the registered per-qubit (constant-pattern) group. **Theorem 1 (amended): any leg-wise sign
pattern ε with consecutive-leg increments in V̂_S = {(−1)^v : v ∈ V_S} (first leg arbitrary) is an
exact record gauge** — proof: insert X^v X^v = I at a round boundary and push one X^v through the
suffix (commutes with every X-type machine element, re-signs the suffix legs, dies at exit; the
global pattern dies at the |+⟩^n entry too). Consequences: (i) suffix flips erase temporal
relative signs at ANY lag — the run-1 "erasure" observations (lag-2 blindness, PAIR2 lag-1
erasure, AND the falsified PAIR1 lag-1 claim) are all instances; (ii) the surviving order-2
content is an exact even law (PAIR1 lag-1): W = (1−2p_M)²(1−2p_Z)⁴ · 2^{−2} Σ_a
e^{−½aᵀ(B₁+B₂)a} cosh(aᵀΣ_× a) — registered as a new (a)-exact bet; (iii) identifiable sign
content = ε-invariants only (within-window qubit-loop products; |·|-combinations across legs).
Tex Theorem-1/Prop-3 rewritten accordingly with an honesty note. Amended bets: V3b (general
gauge: admissible patterns invariant, non-admissible increments ALIVE), V4 flipped (lag-1 PAIR1
sign-blind + magnitude-ALIVE + the cosh-factorized law), nullspace diagnostic added for the
PAIR1-full rank-15/21 deficiency (conjecture: cross-block even-combination structure; diagnostic,
not gated).

## Results (final; logs `outputs/logs/tb_ident_gauge_verify.log` … `_v4.log`)

**ALL CHECKS PASS (38 checks — machine-precision equalities + 7 fired ALIVE controls + 5 rank
gates; count corrected per the review NOTE below, original "36" wording superseded).**

- **Route consistency:** dense record-law route vs char-direct route: |Δ| = 1.1e-16.
- **V1 order-1 hypercube law:** 12/12 exact (both units, both stabilizers, interior + boundary,
  3 random PSD Σ each, dressings exercised): max |W − pred| = 5.6e-16.
- **V2 locality:** outside-window |ΔW| = 0.0 exactly; inside-window ALIVE 3.3e-3.
- **V3 constant-pattern gauge:** all qubit subsets, PAIR1 R=3/R=4 + PAIR2 R=2: max |ΔW| ≤ 2.2e-16;
  converse ALIVE (single cross-entry flip): 5.5e-5.
- **V3b general re-signing gauge (A-TB-1):** suffix flips (v = 11; 011; 101), mid-block, composed
  global×suffix: all ≤ 2.2e-16; non-admissible increments (01 on PAIR1; 001 on PAIR2) ALIVE
  (8.4e-3 / 7.0e-5).
- **V4 temporal ladder (amended):** lag-2 and lag-1 cross-window sign flips both EXACTLY blind
  (0.0) with magnitude-ALIVE controls (6.9e-5 / 1.1e-4 / 3.1e-4); PAIR2 interior erasure exact
  (1.1e-16); **new order-2 cosh-factorized law exact (1.1e-16)**.
- **V5 rank certificates (analytic Jacobian, generic PSD Σ):**
  - PAIR1 R=3 full (readout): rank **15 / 21** (#chars 32; sv gap 2.6e12).
  - PAIR1 R=3 syndrome-only: rank **7 / 21** = #chars−1 (count-limited); per-leg (V_q−V_q′) null
    containment residual 9.5e-15 ((a)-predicted ✓).
  - PAIR2 R=2 full (readout): rank **21 / 21 = FULL** (sv gap ∞) — the dense unit with readout has
    NO linear blind spot at generic Σ; only the discrete re-signing quotient remains.
  - PAIR2 R=2 syndrome-only: rank **15 / 21** = #chars−1 (count-limited).
- **[O] OPEN item (diagnosed, falsified candidate, reported not gated):** the PAIR1-full corank-6
  null structure. Candidate "per-cross-block (A,B-only) differences" FALSIFIED (containment
  residual 0.98 despite the dimension coincidence 6). Second-Σ diagnostic: principal-angle cosines
  [0.969, 0.848, 0.700, 0.495, 0.438, 0.096] ⇒ the null space is **Σ-dependent** — a corank-6
  distribution, not a fixed linear gauge subspace; consistent with the record factoring through a
  locally 15-dimensional sufficient statistic. Closed form OPEN.

**Status:** T-B deliverable complete — theorem + proofs in tex `sec:ident-gauge`, (a)-exact
machine verification green, one registered sub-claim falsified and repaired via a documented
amendment (A-TB-1) that STRENGTHENED the gauge theorem. The [O] item (PAIR1 corank-6 structure)
stays open; [PROVISIONAL] positioning tags stand.

## Un-led review verdict (2026-07-02; fixes applied same day)

**Un-led adversarial review (independent agent; scratch trail `outputs/review_tb_t2_findings.md`):
(A) sec:ident-gauge = SOUND-WITH-FIXES.** All rederived items CONFIRMED: probe-map identity +
support determinism (incl. T(â) ≥ 0), re-signing gauge theorem (every commutation checked:
background channel, assignment noise, both exits, arbitrary first leg), order-1 law end-to-end
(incl. dressing powers; quieting generalizes to any w by Jensen), Prop-3 erasure mechanism
(coset symmetrization), locality/reach ladder, Prop 4 + rank certificates log-consistent and
honestly hedged.

**Findings + fixes applied:** (MAJOR, methodology) the tb script's "two independent routes"
claim was overstated — machine and theorem sides share the graded-CF algebra; the reviewer's
deliberate-bug run proved the class passes tb entirely and is caught only by the t2 MC anchor
(z ≈ 37–41). Fix: tb docstring independence-scope correction (points at t2 S6/S7 as the
independent anchor) + the new S7 dressed-MC anchor in t2 (see t2 record A-T2-2) closing the
p_Z/p_F dressing hole. (MINOR) Theorem-1 proof was terse at the boundary-absorption step — the
second X^v is absorbed because the post-measurement state lies in the recorded syndrome sector
where X^v acts as a scalar; sentence added to the tex (this is exactly why increments must be
V_S-valued at round boundaries). (NOTE) "36 checks" bookkeeping corrected to 38 (equalities +
7 ALIVE + 5 rank gates); norm assert documented as a coding tripwire only (Σ-weight-blind).
