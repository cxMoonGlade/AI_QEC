# Reading note (精读): Smirne, Egloff, Díaz, Plenio, Huelga, "Coherence and non-classicality of quantum Markov processes" (arXiv:1709.05267)

> **Provenance (2026-07-05): FULL-TEXT read (精读).** arxiv HTML → txt `outputs/papers/1709.05267.txt`
> (11 pages, 4 figures). All §/Eq refs from that text. Published as Quantum Sci. Technol. 4, 01LT01 (2019).
> Adjudication target: does this paper provide the theorem linking coherence generation to
> classical simulability (Markovian case), and does the non-Markovian breakdown inform our
> finite-γ decomposition? **Verdict: YES — Theorem 2 (CGD ⇔ non-classicality under Markovianity)
> is foundational for Claim 3, but the non-Markovian breakdown is the key physics: the
> CGD→classicality connection fails exactly where our finite-γ system lives.**

## Metadata [paper]
- **Author:** Smirne, Egloff, Díaz, Plenio, Huelga (Ulm University / Imperial College London / Universidad Nacional de Colombia)
- **Venue / status:** arXiv:1709.05267v3 [quant-ph] → Quantum Sci. Technol. 4, 01LT01 (2019) (Letters)
- **Type:** theory (theorems + examples)

## Executive summary [paper]

Establishes the **equivalence between non-classicality of multi-time statistics and
Coherence-Generating-and-Detecting (CGD) dynamics for Markovian quantum processes**.
The central result is Theorem 2: for a Markovian quantum process, non-classical correlations
in the multi-time statistics exist ⇔ the dynamics generates coherences that are subsequently
detected as populations. The "detecting" clause is critical — generating coherence is not
enough; the coherence must be rotated into a population basis at a later measurement for
non-classical statistics to appear.

The paper formalizes this via the CGD condition [Eq. 5]: Δ ∘ Λ(t) ∘ Δ ∘ Λ(τ) ∘ Δ ≠
Δ ∘ Λ(t+τ) ∘ Δ, where Δ is the dephasing (completely decohering) map. CGD dynamics mean
that on intermediate timescales, the dynamics generates off-diagonal elements (coherences)
that a later evolution can turn into populations. The complementary condition, NCGD
(Non-Coherence-Generating-and-Detecting), is equivalent to the Chapman-Kolmogorov property
for the conditional probabilities [Proposition 1, Eq. 6], meaning the process is classically
Markovian.

**CRITICAL FOR CLAIM 3:** The paper explicitly states that this equivalence holds ONLY
under Markovianity. In the Non-Markovian case, coherence generation and non-classicality
can decouple — one can have CGD dynamics without Leggett-Garg inequality violation, and
vice versa. This is stated in the text surrounding Theorem 1 and Fig. 3. Our finite-γ JC
model is manifestly non-Markovian (the bath correlation time ∼ 1/γ is finite), which means
the CGD→classicality connection that would make σ− sector "obviously non-classical" does
NOT directly apply. The gap between CGD and non-classicality IS the space our decomposition
must quantify.

## Key equations/findings [paper]

### CGD (Coherence-Generating-and-Detecting) condition — Eq. (5)
```
Δ ∘ Λ(t) ∘ Δ ∘ Λ(τ) ∘ Δ ≠ Δ ∘ Λ(t+τ) ∘ Δ
```
The left side: dephase → evolve τ → dephase → evolve t → dephase (three dephasings).
The right side: dephase → evolve t+τ → dephase (two dephasings). Inequality means
dephasing a subset of evolutions changes the measurement statistics — i.e., coherences
are both generated and rotated into populations.

### NCGD ⇔ Classical Markov property — Proposition 1, Eq. (6)
```
NCGD ⇔ p(x₃,t₃|x₂,t₂; x₁,t₁) = p(x₃,t₃|x₂,t₂)   [∀ t₃ > t₂ > t₁]
```
When dynamics is NCGD, the multi-time conditional probabilities satisfy the classical
Markov property — the future depends on the past only through the immediate preceding
outcome. This IS the K = 0 condition (Kolmogorov zero) in our setting. NCGD is the
dynamical condition for fully classical multi-time statistics.

### Theorem 2 — CGD ⇔ Non-classicality (Markovian case)
For a **Markovian** quantum process (divisible dynamical map, QRT holds):
```
CGD dynamics ⇔ non-classical multi-time correlations
```
This is the central theorem. "Non-classical" means the multi-time statistics cannot be
reproduced by a classical hidden-variable model. Under Markovianity, detecting a CGD
process is sufficient to conclude non-classicality.

### Theorem 1 — Leggett-Garg violation ⇒ CGD (for Lindblad)
```
LG(t₁,t₂,t₃) violation ⇒ CGD dynamics
```
But the converse does NOT hold: CGD does not imply LGI violation. LGI is a witness, not a
characterization. CGD is the full characterization of the relevant dynamical property.

### Non-Markovian breakdown — Fig. 3 and surrounding text
In the non-Markovian regime, the equivalence chain breaks:
- Non-CGD dynamics can produce LGI violations (non-classical statistics from apparently
  "non-CGD" dynamics)
- CGD dynamics can be compatible with a classical hidden-variable model (classical
  statistics from apparently "CGD" dynamics)
The breakdown occurs because the QRT fails — multi-time statistics are no longer determined
by the reduced map alone, and environmental correlations can either simulate or destroy
non-classical features.

## Relevance to project [ours]

**This paper is the FOUNDATIONAL theorem for Claim 3's "coherence sector" decomposition
— but the non-Markovian breakdown is the operative physics for our finite-γ system.**

1. **σz sector (pure dephasing) = NCGD, classically simulable:** Under pure dephasing,
   the dynamics never generates coherences (the evolution preserves the σz eigenbasis).
   Theorem 2 tells us that, under Markovianity, σz-sector dynamics are NCGD and therefore
   classically simulable. For our JC model at r=1 (σz-coupling only), this explains why
   the incoherent null model fits well — the TV residual is small because the dynamics
   is approximately NCGD.

2. **σ− sector (T₁ decay) = CGD, the coherence-active channel:** Amplitude damping
   generates coherences (off-diagonal in σz basis) that evolve into populations at later
   times. Theorem 2 says this sector is CGD and therefore non-classical — which maps
   onto our larger TV residual for the JC model at r≠1 (where the σ− component in the
   coupling creates coherence).

3. **BUT — the Markovian assumption fails for finite γ:** Our JC model has finite bath
   correlation time (γ not infinite, T₂* not ≪ 1/γ). The non-Markovian breakdown means
   the CGD→non-classicality equivalence does NOT hold where our system operates. The
   gap between CGD and non-classicality in the non-Markovian regime IS what our TV
   residual decomposition must measure — this gap is exactly the finite-γ contribution
   that cannot be reduced to coherence generation alone.

4. **Decomposition implication:** Claim 3's decomposition must separate the TV residual
   into three components:
   - (a) **CGD-induced (Markovian-analogue) part:** the portion attributable to coherence
     generation in the σ− sector, as if the process were Markovian — this is the
     theorem-backed "baseline" non-classicality
   - (b) **Non-Markovian enhancement (or suppression):** the deviation from (a) due to
     finite-γ environmental memory — the gap CGD→non-classicality opens
   - (c) **Collective part:** the portion from multi-qubit correlations, not captured by
     single-qubit CGD (this paper is single-qubit only)

## Limitations
- Single-qubit only (Theorem 2-3 proven for single-qubit dephasing and depolarizing;
  multi-qubit CGD is not characterized)
- Markovian assumption is essential for the central equivalence (Theorem 2) — the
  non-Markovian breakdown is stated qualitatively, not quantified
- No explicit connection to bath spectral density or finite correlation times — the
  breakdown is "non-Markovian = QRT fails" without a continuous parameter quantifying
  the gap
- Dephasing channel (Δ) as CGD detector is specific: other dephasing choices would
  change the classification

## Tags
- `[paper]` Theorem 2: CGD ⇔ non-classical multi-time statistics (Markovian case)
- `[paper]` NCGD ⇔ classical Markov property (K = 0) — Proposition 1
- `[paper]` CGD condition: Δ ∘ Λ(t) ∘ Δ ∘ Λ(τ) ∘ Δ ≠ Δ ∘ Λ(t+τ) ∘ Δ
- `[paper]` Leggett-Garg violation ⇒ CGD (but CGD ⇏ LGI violation)
- `[paper]` NON-MARKOVIAN: CGD ↔ classicality equivalence breaks (our finite-γ regime)
- `[ours]` σz sector (r=1) = NCGD ≈ classically simulable (explains small TV residual)
- `[ours]` σ− sector (r≠1) = CGD, but non-Markovian gap means NOT automatically
  non-classical
- `[ours]` Claim 3 must decompose: baseline CGD part + non-Markovian deviation + collective
