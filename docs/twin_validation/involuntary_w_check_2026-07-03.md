# Involuntary-W check — does the schedule's own mid-circuit structure expose the commutator (Im-K) sector?

**Status: RESOLVED 2026-07-03 — v1 registered bet P2 falsified (§5, a finding), repaired
STRONGER by A-IW-1 (§5b evenness theorem + exact-classicality), all 16/16 v2 gates PASS
(§5c). Sections 0–4 are the original prereg, preserved verbatim; §3 M's mechanism reading
is superseded by A-IW-1.**
Queued 2026-07-03 by the 2511.16772 精读
(`docs/papers/reading_notes/montanalopez_nonmarkovian_learning_manybody_2511.16772.md`, Open (i));
resolves the tb-record duty "check the involuntary-W question before freezing 'invisible'
language" (`tb_ident_gauge_theorem_record.md`, COVERAGE GAP RESOLVED block).

## 0. The question

Montañà-López et al. (2511.16772) prove that in prepare–evolve–measure experiments (W = 1⊗N),
second-order-Dyson observables do not depend on the diagonal imaginary kernel data
Im[K^(m)_aa(0)]; inserting a mid-evolution single-qubit gate W restores access (their Table I).
Our T-B/tex claims say certain Σ-functionals are *invisible* to the fixed passive machine's
record. Duty: verify that the machine's OWN mid-circuit operations (the stabilizer parity
measurements — the only interleaved operations of the abstract machine) do not constitute an
"involuntary W" that voids any of our invisibility statements — and say precisely what they DO
expose at the model-class boundary.

## 1. Their mechanism, exactly (from the cached full text)

- Kernel symmetry K_ab(t) = K_ba(−t)* ⇒ diagonal K^(m)_aa(0) is real for even m, imaginary for
  odd m (txt p.11). The commutator (antisymmetric-in-time) sector of a coupling's
  autocorrelation = the odd-m diagonal Taylor data.
- Eq. (19b)/(20): at W = 1⊗N the coefficient superoperator of the diagonal Im data vanishes by
  the Pauli identity **[P, {P, ·}] = 0** — for pure dephasing this is the Z² = I global-phase
  cancellation. Off-diagonal odd-m components survive only as pair-sums (Eq. 20) — individually
  unresolvable.
- Table I: Case 2 (off-diagonal, odd m) is repaired by a mid PAULI W anticommuting with P_aP_b;
  Case 3 (diagonal Im, odd m) needs W = S·H (rotates Z → Y). **A mid Pauli does NOT repair
  Case 3** [derivation, class (a)]: conjugation by a Pauli only re-signs the coupling operator,
  and [Z, {Z, ·}] = 0 is sign-blind — check all three terms of their Eq. (19b) with W = X:
  X[Z,{Z,ρ}]X = 0; [Z,{Z, XρX}] = 0; [Z, X{Z,ρ}X] = [Z, {XZX, XρX}] = −[Z,{Z,ρ'}] = 0.
  So the operative property of W is *genuinely rotating* the coupling operator, not merely
  failing to commute with it.

## 2. In-class closure — no loophole inside the declared classical Gaussian class [(a)]

Two independent reasons, either sufficient:
1. **The component does not exist in-class.** For the declared classical Gaussian phase field,
   the kernel is real (Im K ≡ 0): a Gaussian family with vanishing commutators is a commuting
   operator family = a classical process; conversely our Σ parametrizes only the symmetric
   sector. The object their W recovers is structurally zero on our whole parameter space — no
   schedule, active or passive, can create dependence on a parameter that is identically zero.
2. **The proofs are machine-complete.** T1 (re-signing gauge, all orders), LA (probe calculus =
   the complete record law), C1 (order↔reach), R0 (window-Gram reduction) are theorems of the
   FULL machine — mid-circuit parity measurements and resets included. There is no "operation
   the proof forgot" for an involuntary W to hide in.

**Consequence for the draft:** every "invisible/conceals" claim keeps its three-part scope —
(model class: classical Gaussian Σ) × (access: this machine's passive record) × (moment order
where an order is stated). R0/T1 are all-order in-class statements; order-indexed claims stay
order-indexed. No claim retracts.

## 3. The class-boundary statement — the mid measurement IS a (partial) involuntary W [(a) + registered bets]

If the TRUE hardware noise is a quantum Gaussian dephasing environment (Im K ≠ 0), the
machine's own mid-circuit X-parity measurement partially plays the role of their Case-3 W:

- **N1 (no-mid-operation null, all orders).** With no interleaved operation (terminal-only
  measurement), the record is blind to Im K at ALL orders: within one uninterrupted leg the
  time-ordering commutator [Z⊗B(t), Z⊗B(t')] ∝ Z²⊗c-number = a global phase (Z² = I). The
  single-qubit pure-dephasing record depends on the kernel only through the symmetric part.
- **N2 (mid-outcome-discarded null at O(g²)).** Summing over the mid outcome m₁ replaces the
  measurement by the channel ρ ↦ (ρ + XρX)/2 — a mixture of identity and a Pauli conjugation.
  Each branch is Im-null at linear order (§1: Pauli W does not repair Case 3; the X-branch only
  re-signs the leg-2 coupling, flipping the sign of the whole cross-leg kernel), so the
  m₁-marginal record has NO linear (O(g²)) Im-K dependence; the leading allowed dependence is
  the mixed even term Re_c·Im_c = O(g⁴). Likewise E[m₁] (leg-1-only) is Im-blind at all orders
  by N1.
- **M (the mechanism).** The m₁-RESOLVED record keeps the projector cross terms
  m₁(Xρ + ρX)/4 — genuinely non-Pauli-conjugation superoperator terms sandwiched between the
  leg-1 and leg-2 coupling insertions. These break the L/R placement symmetry that kills the
  commutator contraction, so m₁-correlated cross-leg moments (E[m₁m₂]) generically acquire a
  LINEAR (O(g²)) dependence on the cross-leg commutator integral
  κ := −∫_{leg2}∫_{leg1} Im K(t₂−t₁) dt₁dt₂.
  This is the passive, partial counterpart of their Case-3 W: no design freedom is exercised —
  the schedule already contains the symmetry-breaking operation — but only the CROSS-window
  commutator content becomes visible, and only through outcome-resolved moments.

## 4. Minimal model + registered predictions (written BEFORE the run)

Machine: 1 qubit (stabilizer = X itself), R = 2 legs of duration τ, mid X-measurement (m₁),
terminal X-measurement (m₂), entry |+⟩. Quantum bath: one bosonic mode, thermal n̄,
H = ω a†a + (g/2) Z (a + a†); interaction-picture kernel
K(t) = (g²/4)[(2n̄+1)cos ωt − i sin ωt]. Leg displacement α₁ = −i(g/2)∫₀^τ e^{iωt}dt,
α₂ = e^{iωτ}α₁; cross-leg commutator integral κ = Im(α₂ᾱ₁) = |α₁|² sin ωτ.
**ω → −ω flips Im K (and κ) while leaving Re K unchanged exactly** — the ω-flip pair is the
Im-response probe with no matching procedure in the loop.
Classical-matched arm [(a) closed forms, from our own order-1/cosh law]: Gaussian phases with
Gram V_j = 4(2n̄+1)|α_j|², C = 4(2n̄+1)Re(α₂ᾱ₁):
E_cl[m₁] = e^{−V₁/2}, E_cl[m₂] = e^{−(V₁+V₂)/2}cosh C, E_cl[m₁m₂] = e^{−V₂/2}.
(A quantum Gaussian bath with Im K ≡ 0 is exactly a classical process, so the classical arm is
the Im→0 limit of the quantum machine at identical Re K.)

Two independent computation routes (adversarial-self-verification rule):
- Route A: dense joint evolution, qubit ⊗ truncated Fock (torch complex128, GPU), Schrödinger
  picture, projective Kraus mid-measurement.
- Route B: exact conditional-displacement path sum (16 sector paths, displacement algebra,
  thermal ⟨D(μ)⟩ = e^{−|μ|²(n̄+½)}) — no truncation, independent algebra.

Registered predictions (class (b) unless noted; thresholds (c); parameters ωτ = 1.7, τ = 1,
n̄ ∈ {0.3, 1.0}, g ∈ {0.4, 0.2, 0.1, 0.05, 0.025}, Fock N = 48 with N → 96 convergence gate):
- **P0 [exact-null control]:** ω-odd part of E_q[m₁] = 0 to ≤ 1e−13 (N1, leg-1-only).
- **P1:** ω-odd part of E_q[m₂] (mid-outcome-discarded) = o(g²): local log-log slope ≥ 3.5, or
  exact null ≤ 1e−13 (N2 allows O(g⁴)).
- **P2 [the headline]:** ω-odd part of E_q[m₁m₂] = Θ(g²): slope → 2.0 ± 0.15 at the small-g
  end, nonzero at every g, and sign flips with sin ωτ (mechanism M).
- **P3 [exact-null control]:** with the mid measurement REMOVED (terminal-only), the ω-odd part
  of ⟨X⟩(2τ) = 0 to ≤ 1e−13 at every order probed (N1 all-orders).
- **G-match [(b)]:** ω-symmetrized E_q[m₂] minus the classical cosh law = O(g⁴) (slope ≥ 3.5)
  — validates the Gram constants and exhibits our T2 cosh law as the O(g²) record of the
  quantum machine.
- **G-AB [(c) gate]:** |route A − route B| ≤ 1e−9 on every P(m₁,m₂) cell, every setting.
  **G-Fock [(c)]:** doubling N changes route A ≤ 1e−10.
- Falsification reading: P2 failing (slope ≠ 2 or zero response) kills the involuntary-W
  mechanism claim (§3 M); P0/P1/P3 failing kills the null derivations (N1/N2); G-AB/G-Fock
  failing = implementation, fix before interpreting.

## 5. v1 results (script `outputs/involuntary_w_check_v1.py` via `outputs/run_involuntary_w_check_v1.sh`, log `outputs/logs/involuntary_w_check_v1.log`, run 2026-07-03T01:02 PT)

**Registered bet P2 = MISS (a finding, never citable as fact).** All ω-odd parts are EXACT
ZEROS (printed +0.000e+00; both routes agree, G-AB ≤ 1.3e−13; G-Fock 9.4e−14): there is NO
linear commutator-sector response in ANY moment, outcome-resolved or not. P0/P1/P3 exact
nulls PASS. Meanwhile the run exposed two REAL structures the bets did not anticipate:
- E_q[m₂] equals the classical cosh law at MACHINE PRECISION at every g (G-match ≤ 1.2e−13
  even at g = 0.4 where other effects are 7e−3) — not merely O(g⁴)-close.
- E_q[m₁m₂] − E_cl[m₁m₂] ≠ 0 at O(g⁴): −6.94e−3 (n̄ = 0.3) / −6.36e−3 (n̄ = 1.0) at g = 0.4,
  ratio across g = 0.4→0.2 is 14.8 ≈ 2⁴ (slope ≈ 3.9): a real, two-route-confirmed
  quantum–classical record wedge, EVEN under the Im-flip.
Diagnosis of the miss: §3 M's cross-Kraus hand-wave ignored a realness constraint that
forces evenness — see A-IW-1. (The ω-flip probe is NOT vacuous: it flips Im K at fixed
Re K, so the exact null is an informative invariance measurement; it is the LINEAR-response
reading of §3 M that was wrong.)

## 5b. ADDENDUM A-IW-1 (registered 2026-07-03, before the v2 run) — the evenness theorem + corrected predictions

**Proposition IW-1 (record evenness in the commutator sector). [(a) proven]**
Hypotheses: (i) the machine's system-side objects (entry state, measurement/reset operators)
are REAL in the computational basis (X-parity projectors, |+⟩ entries, Z-basis resets all
are); (ii) the bath is zero-mean Gaussian with REAL quadratic H_b, REAL linear coupling
operators (a+a†-form), and a REAL, PARITY-EVEN state γ (thermal, real squeezed included);
(iii) passive record (no complex-valued designed gates). Then the record law is invariant
under the global commutator-sector flip Im K → −Im K at fixed Re K.
*Proof.* Let P = ⊗_modes parity. P H_b P = H_b would fail to flip — instead use
P [H_b + Σ_q Z_q⊗B_q] P = H_b − Σ Z_q⊗B_q and note H(−) := −P H P = −H_b + Σ Z_q⊗B_q, which
is exactly the machine with the bath free Hamiltonian reversed: B(t) → B(−t), i.e.
K(t) → K(−t) = K(t)* (Re fixed, Im flipped). So U_flip = P U† P with U = e^{−iHτ}. Insert
into the record functional: the P's cancel pairwise (P² = 1, P commutes with the system-side
real operators and Pγ P = γ). The resulting expression is the original one with U ↔ U†.
Now conjugate: every non-U factor is real, U* = U† (H real), and the record value is real —
so the U ↔ U† expression equals the original. ∎
Corollaries: (C1) the passive machine is LINEARLY blind to the commutator sector — the
quantum imprint can enter only through EVEN powers of the cross-window commutator integrals
κ (within-window Im is null at all orders by the leg-global-phase argument, N1). (C2) Their
Case-3 W = S·H is a COMPLEX matrix — precisely what escapes hypothesis (i); a mid Pauli or a
mid X-measurement keeps everything real and cannot escape. This is the exact structural
reason design freedom is needed for linear commutator access, now stated as a theorem on the
passive side.
**Exact-classicality of outcome-discarded moments. [(a) proven]** E[m₁] and E[m₂] equal the
classical closed forms EXACTLY (all orders in g): summing over m₁ replaces the mid
measurement by the branch mixture ½(ρ + XρX); in each branch the two coupling insertions
compose with Z² = 1 (identity or re-signed), so each branch is an uninterrupted (possibly
re-signed) dephasing = Re-only = classical; the branch average reproduces the T2 cosh law
with V_j, C = 4·(Re-K window Grams). The quantum–classical wedge of this machine therefore
lives EXCLUSIVELY in the outcome-resolved cross moment E[m₁m₂], with leading behavior
W₁₂ = a(n̄, ReGram)·κ² + O(κ⁴), κ = Im(α₂ᾱ₁) = |α₁|² sin ωτ.

Registered v2 predictions (before the v2 run; thresholds (c)):
- **G1:** |E_q[m₁] − e^{−V₁/2}| and |E_q[m₂] − e^{−(V₁+V₂)/2}cosh C| ≤ 5e−12 at ALL (g, n̄)
  (exact theorems; 1e−13 already seen at spot values).
- **G2:** wedge W₁₂ := E_q[m₁m₂] − e^{−V₂/2}: local slope 4.0 ± 0.2 at the smallest-g pair;
  coefficient a := W₁₂/κ² stable to ≤ 2% between g = 0.05 and 0.025; W₁₂(ωτ=4.0) has the
  SAME sign as W₁₂(ωτ=1.7) (evenness: sign set by a, not by sin ωτ).
- **G3:** single-mode full-flip odd parts of all three moments ≤ 1e−13 (Prop IW-1
  verification, rebadged from v1's P0/P1/P2 columns).
- **G4 (two-mode, ω₁τ=1.7, ω₂τ=4.0, g₂=0.8g₁, n̄=0.7):** (T1) full flip (−ω₁,−ω₂): E₁₂ odd
  part ≤ 1e−12 (IW-1); (T2'') |E₁₂(−ω₁,+ω₂) − E₁₂(+ω₁,−ω₂)| ≤ 1e−12 (evenness in the total
  κ = κ₁+κ₂); (T2) partial-flip response |E₁₂(+,+) − E₁₂(−,+)| > 1e−8 at g₁ = 0.3 with
  slope 4.0 ± 0.3 between g₁ = 0.3 and 0.15 (= the 4aκ₁κ₂ cross term — the parameter-free
  witness that the record depends on Im K only through the single scalar κ, evenly);
  (T3) two-mode E[m₁], E[m₂] classical-exact ≤ 5e−12 (kernels add: V, C sum over modes).
- **G5:** route A–B agreement ≤ 1e−9 everywhere incl. two-mode; two-mode Fock convergence
  (N 18→24) ≤ 1e−9.
Falsification reading: G1/G3/G4-T1/T2'' failing kills Prop IW-1 or the classicality theorem
(they are (a)-claims — a failure means a proof error, STOP); G2/G4-T2 failing kills the
κ²-leading-order reading of the wedge.

## 5c. v2 results — ALL 16/16 A-IW-1 GATES PASS (run 2026-07-03T01:11 PT, log `outputs/logs/involuntary_w_check_v2.log`)

Single-mode (n̄ ∈ {0.3, 1.0}, g ∈ {0.4…0.025}):
- **G1 PASS:** E_q[m₁], E_q[m₂] equal the classical closed forms to ≤ 1.3e−13 at every
  setting (exact-classicality theorem, machine-verified).
- **G3 PASS:** all Im-flip odd parts print EXACT 0.0e+00 (Prop IW-1, machine-verified).
- **G2 PASS:** wedge slope 3.998/3.997; coefficient stability 0.12%/0.22%; same sign at
  ωτ = 4.0. **Observation [(b)]:** a := W₁₂/κ² → −7.997/−7.994 at g = 0.025 for BOTH n̄ —
  consistent with an n̄-independent limit a(0) = −8 (closed-form derivation from the path
  sum = small open item; not load-bearing).
Two-mode (ω₁τ = 1.7, ω₂τ = 4.0, g₂ = 0.8g₁, n̄ = 0.7):
- **T1 PASS (exact 0.0):** full flip (−ω₁, −ω₂) leaves E₁₂ unchanged — IW-1 in two modes.
- **T2'' PASS (exact 0.0):** E₁₂(−ω₁,+ω₂) = E₁₂(+ω₁,−ω₂) — the record depends on the Im
  sector only through the single scalar κ_tot = κ₁+κ₂, evenly.
- **T2 PASS:** partial-flip response 1.1375e−3 at g₁ = 0.3, slope 3.892 (gate 4.0 ± 0.3) —
  the 4aκ₁κ₂ cross term is real and quadratic (consistency: 4·8·κ₁|κ₂| = 1.26e−3, 9% above
  the measured value at this not-yet-asymptotic g; slope confirms the order).
- **T3 PASS:** two-mode outcome-discarded moments classical-exact ≤ 1.1e−16 (checked on the
  exact route).
- **G5/G-Fock PASS** (routes ≤ 1e−9 after the N = 30 fix; N30→36 ≤ 4.9e−12).
Run-2 implementation notes (documented, not silent): the first two-mode attempt used
Fock N = 18 and failed G5 at 1.72e−7 = the thermal truncation tail q^N (n̄ = 0.7 ⇒
q^18 ≈ 1.2e−7) — raised to N = 30; the T3 exact-identity check was moved to the exact
(route-B) moments after the N = 30 run showed the dense-route floor (4.9e−12) grazing the
5e−12 threshold — an exact theorem is checked on the exact substrate.

## 6. Consequences (final)

1. **No retraction in-class; scope duty confirmed.** The tex "provably invisible/conceals"
   statements stand; make the three-part scope (model class: classical Gaussian Σ × access:
   this machine's passive record × moment order where stated) explicit at first use in
   sec:ident-gauge.
2. **The involuntary-W worry is CLOSED, stronger than hoped [(a) + machine-verified].** The
   schedule's own operations cannot even PARTIALLY mimic their Case-3 W at linear order:
   Prop IW-1 (realness/parity) forces the passive record to be EVEN in the commutator
   sector; within-window commutator content is null at all orders (N1); outcome-discarded
   moments are EXACTLY classical (cosh law); the only quantum imprint is quadratic —
   W₁₂ ≈ −8κ² in the minimal cell — confined to outcome-resolved cross moments. The
   "invisible" language survives its sharpest test: what looked like a potential loophole is
   a provable quadratic suppression.
3. **The active/passive boundary is now a matrix-realness statement.** Their Case 3 requires
   W = S·H — a COMPLEX gate; every operation our machine owns (X-parity measurements,
   resets, Pauli frames) is REAL, and IW-1 shows real machines cannot get linear commutator
   access. One remark in the draft: design freedom buys precisely the complex structure that
   linear commutator access requires (cite 2511.16772 Table I Case 3 as the active-pole
   construction; IW-1 as the passive-pole obstruction).
4. **Class-boundary honesty line for the draft:** if the true noise is a quantum Gaussian
   environment, the classical-Σ twin's record misspecification from the commutator sector is
   O(κ²) (quadratically suppressed cross-window commutator integrals), lives only in
   outcome-resolved cross moments, and vanishes identically from detector-averaged
   first-order statistics — the dephasing-sector counterpart (and mechanism-level
   explanation) of the smallness ordering seen in the quantum-bath branch (M2 D_matched,
   `quantum_bath_slot_prereg.md`).
5. **No new estimand claim:** we do not claim the quantum sector is learnable from real
   syndrome records; the check bounds what our "invisible" language may assert, and the a =
   −8 observation stays a numerical remark until derived.
