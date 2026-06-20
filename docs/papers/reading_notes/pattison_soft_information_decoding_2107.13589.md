# Deep review — Pattison, Beverland, da Silva & Delfosse, *Improved quantum error correction using soft information*

> Deep reading note (academic-paper-review format; full read of all four pages +
> Appendices A–D, every equation and both decoder algorithms). **This paper is the
> twin program's direct reference for the SOFT-READOUT (continuous / Gaussian-IQ)
> measurement model and for soft-information surface-code decoding.** It supplies
> (i) the exact Gaussian soft-measurement likelihood model we need for our SIM-ONLY
> non-Pauli teacher, and (ii) the exact soft-decoder edge-weight formulas (soft MWPM
> and soft Union-Find) we need to decode that continuous data — the non-Pauli signal
> that opens decoding headroom *above* Pauli (hard) decoders.

## Metadata
- **Title.** Improved quantum error correction using soft information.
- **Authors.** Christopher A. Pattison¹, Michael E. Beverland², Marcus P. da Silva²,
  Nicolas Delfosse². (¹ Caltech, Institute for Quantum Information and Matter,
  Pasadena, USA; ² Microsoft Quantum and Microsoft Research, Redmond, USA.)
- **Identifier / date.** arXiv:2107.13589v1 [quant-ph], 28 Jul 2021 (dated July 30, 2021).
- **Local path.** `docs/papers/pattison_soft_information_decoding_2107.13589.pdf`
  (4-page two-column body + Appendices A–D; the PDF ships owner-encrypted —
  text extracted with `pdftotext -layout`, no content lost).
- **Domain / type.** QEC / fault-tolerant decoding; **theory + Monte-Carlo simulation**
  (decoder construction, optimality proof, threshold + sub-threshold estimates). No
  hardware data.

## Executive summary
Standard QEC noise models flip a **binary** measurement outcome with some probability.
Real measurements are not binary — they output a continuous current/voltage (dispersive
superconducting readout), photon counts, etc. — and the hardware-to-binary discretization
**throws information away**. This paper shows how to (a) **model** that richer continuous
output and (b) **decode** with it, for the surface code, without ever reconstructing the
quantum state (the classical "measure all bits, compute parities in noiseless
post-processing" trick is forbidden because parities must be computed by *noisy* quantum
circuits that propagate errors).

The measurement model is deliberately generic (Fig. 2): an ideal projection produces a
**hidden** ideal bit `μ̄ ∈ {0,1}`; what is *observed* is a continuous **soft outcome** `μ`
drawn from a conditional density `f^(μ̄)(μ)`. The canonical instance is **Gaussian soft
noise**: `f^(0) = 𝒩(+1, σ²)`, `f^(1) = 𝒩(−1, σ²)`. A "hard" outcome `μ̂` is recovered by a
maximum-likelihood threshold (Eq. 1); discarding `μ` for `μ̂` is exactly the information
loss the paper recovers. The authors also derive a physically grounded **asymmetric**
model — Gaussian soft noise **with amplitude damping (T₁ decay)** — from a continuous
dispersive-readout signal (Appendix A), where measurement time `τ_M` trades resolution
against extra disturbance.

The decoders are modifications of MWPM and Union-Find that consume `μ` directly. The single
load-bearing object is a **per-vertex log-likelihood-ratio edge weight**: a "soft vertical
edge" connecting consecutive rounds gets weight `w(e) = −log L_{a,t}(μ_{a,t})` where
`L_{a,t}(μ) = f^(μ̂)(μ)/f^(μ̄̂)(μ)` is the likelihood ratio between the inferred hard outcome
and its complement (Eqs. 6–7). Ordinary (data-error) edges keep the usual `−log p/(1−p)`.
The authors **prove** the resulting soft MWPM returns a **most-likely fault set**
(Theorem 4.1, via a Bayes identity Lemma 4.3 that the conditional fault probability equals a
constant plus the sum of these weights, Eq. 10) and give a sufficient correction guarantee
`|x̃|_w < d_w/2` (Corollary 4.4); soft UF is an almost-linear-time approximation with a
matching guarantee under one extra topological condition (Theorem 4.5).

Headline numerics: under **soft phenomenological** noise, soft UF reaches threshold
**3.665(2)%** vs hard UF **2.637(1)%** — and critically **25% above the optimal hard-decoder
threshold 2.93(2)%** estimated by statistical-mechanics mapping (Wang–Harrington–Preskill,
ref. [21]). So the gain is not "soft UF beats hard UF" bookkeeping; **soft information beats
the information-theoretic ceiling of any decoder restricted to hard outcomes.** Under soft
circuit noise the gap shrinks (ancilla-circuit errors dominate) but persists (Table 1). The
amplitude-damping study shows logical performance is **violently sensitive to measurement
time**: for `d = 19`, a 5× longer `τ_M` (the time that naively minimizes per-measurement
soft-flip rate) raises the logical error rate per round **~1000×** — motivating joint
optimization of the physical and QEC layers.

**For the twin/program.** This is our **soft-readout model + soft-decoding reference**.
The non-Pauli axis the program has pivoted to (leakage / soft readout / T₁T₂, SIM-ONLY,
Bayes-floor-vs-Pauli-gap) needs exactly two ingredients this paper hands over: the
**Gaussian-IQ likelihood `f^(b)(μ)`** to *generate* continuous syndrome data in our teacher,
and the **soft edge-weight `w(e) = −log L`** to *decode* it. The "+25% above any hard
decoder" result is the cleanest published statement that **soft-readout information is real
decoding headroom above the best Pauli/hard decoder** — i.e. the gap the program proposes to
own. The amplitude-damping appendix is a ready-made asymmetric, time-parameterized readout
channel; one caveat — its amplitude damping is **measurement-induced T₁ relaxation acting on
the readout signal**, *not* leakage to a `|2⟩` level, so it covers our T₁/soft-readout teacher
but **not** the leakage axis (see Limitations).

## Contributions (claim → evidence → strength)
- **C1. A generic soft-measurement model decoupled from the physical encoding (Sec. 1.3, Fig. 2).**
  *Claim:* measurements are a perfect projection to a hidden ideal bit `μ̄` followed by a
  noisy channel emitting a continuous `μ ∼ f^(μ̄)(μ)`; only the conditional densities are
  needed, so the framework is hardware-agnostic. *Evidence:* hardening map Eq. 1; soft-flip
  probability Eq. 2; hard+soft composition Eq. 3; Gaussian instance `f^(0)=𝒩(+1,σ²),
  f^(1)=𝒩(−1,σ²)`. *Strength: strong (the modeling backbone; minimal assumptions).* 
- **C2. A graphical noise model unifying ideal/phenomenological/circuit noise WITH soft outcomes (Sec. 2, Def. 2.1).**
  *Claim:* a quadruple `(G_T, p, f, ε)` — fault hypergraph, per-edge fault probability,
  per-vertex soft-density pair `(f_{a,t}^{(0)}, f_{a,t}^{(1)})`, residual Pauli — captures
  correlated errors, repeated rounds, and soft readout as one object; the three standard
  models are special cases. *Evidence:* soft phenomenological (Sec. 2.3, Fig. 5), soft circuit
  (Sec. 2.4, Fig. 6) constructions; syndrome Eq. 5; fault-set probability Eq. 4.
  *Strength: strong (clean generalization; matches our DEM/hypergraph substrate).* 
- **C3. Soft MWPM and soft UF decoders via log-likelihood-ratio edge weights (Sec. 3, Algs. 1–2).**
  *Claim:* both decoders are the standard ones with a *data-dependent* weight on the new
  "soft vertical edges": `w(e) = −log L_{a,t}(μ)` (Eqs. 6–7); same asymptotic complexity as
  the hard decoders. *Evidence:* Algorithm 1 (distance graph, MWPM), Algorithm 2 (half-edge
  cluster growth Eq. 8 + peeling); complexity discussion (`O(d^{7.5})` MWPM with [36];
  `O(d³α(d))` UF). *Strength: strong (the directly reusable artifact).* 
- **C4. Optimality + correction guarantees (Sec. 4).**
  *Claim:* soft MWPM returns a most-likely fault set (Thm. 4.1); soft MWPM corrects any fault
  with `|x̃|_w < d_w/2` (Cor. 4.4); soft UF does the same under one topological condition
  (Thm. 4.5). *Evidence:* Bayes identity Lemma 4.3 (Eq. 10, with `P(m|x)` factorizing into
  the likelihood ratios, Eqs. 11–14); UF growth/diameter bounds Eqs. 15–20.
  *Strength: strong (the soft weights are *derived from Bayes*, not heuristic).* 
- **C5. Numerical thresholds: +25% over the optimal hard decoder (Sec. 5, Figs. 8–11, Table 1).**
  *Evidence:* phenomenological soft UF 3.665(2)% vs hard UF 2.637(1)% vs optimal-hard
  2.93(2)% [21]; circuit thresholds (Table 1); the `r = p_{M,soft}/p_{M,hardened}` sweep
  (Fig. 9). *Strength: strong (the headline empirical claim, with a stat-mech ceiling for
  reference).* 
- **C6. Measurement-time / logical-rate tradeoff under amplitude damping (Sec. 6, App. A, Fig. 12).**
  *Claim:* the `τ_M` minimizing per-measurement physical soft-flip rate is **not** the `τ_M`
  minimizing logical error; for `d = 19` the gap is ~1000× in logical rate for a 5× `τ_M`
  change. *Evidence:* parametric circuit model (`τ_G, τ_D, τ_A, τ_F`), Fig. 12.
  *Strength: strong (concrete co-design argument; physically parameterized).* 

## Method (deep)

### Soft-measurement model (Sec. 1.3, Fig. 2)
- **Ideal vs soft vs hard.** A perfect projection yields a hidden ideal bit `μ̄ ∈ {0,1}`.
  The observed **soft outcome** `μ` has density `f^(μ̄)(μ)` conditioned on `μ̄`. The framework
  handles continuous *or* discrete `μ`; the paper focuses on continuous.
- **Hardening map (maximum likelihood), Eq. 1:**
  `μ̂ = 0 if f^(0)(μ) ≥ f^(1)(μ); else 1.` A **soft flip** is `μ̂ ≠ μ̄`.
- **Soft-flip probability, Eq. 2:**
  `P(soft flip | μ̄) = ∫_{ f^(μ̄')(μ) > f^(μ̄)(μ) } f^(μ̄)(μ) dμ`, with `μ̄' = μ̄ + 1 (mod 2)`.
  In general this depends on `μ̄` (asymmetric measurements).
- **Symmetric measurement / Gaussian instance.** A measurement is *symmetric* if
  `P(soft flip|0) = P(soft flip|1) ≜ p_{M,soft}`. The canonical symmetric model is
  **Gaussian soft noise**: `f^(0) = 𝒩(+1, σ²)`, `f^(1) = 𝒩(−1, σ²)`. The mean separation is
  `2` and the spread `σ` (equivalently a signal-to-noise ratio) sets the overlap, hence
  `p_{M,soft}`.
- **Composition with a hard flip, Eq. 3.** If the *ideal* outcome is first flipped with hard
  probability `p_M` and then subject to symmetric soft noise, the overall after-hardening flip
  probability is `p_{M,hardened} = p_M + p_{M,soft} − p_M p_{M,soft}`. (This lets a soft model
  be tuned to a target hard flip rate — used throughout Sec. 5 to make the soft and hard
  models comparable at fixed `p_{M,hardened}`.)

### Amplitude-damping soft model (Sec. 1.4 + Appendix A) — the physical IQ-readout channel
- **Signal model, Eq. 25.** The continuous dispersive-readout output is
  `dS(τ) = v R(τ) dτ + σ dW(τ)`, where `v` is the signal amplitude, `R(τ) = +1` if the system
  is in `|0⟩` and `−1` if in `|1⟩` (instantaneous response), `σ` the noise amplitude, and
  `dW` a Wiener increment (white Gaussian noise, variance `dτ`). The qubit may spontaneously
  decay `|1⟩ → |0⟩` at any time (never `|0⟩ → |1⟩`); the decay time `K` is exponential with
  rate `1/τ_A` (the amplitude-damping / `T₁` time), so `P(|1⟩; τ) = e^{−τ/τ_A}`.
- **Integrated outcome, Eqs. 26–28.** Integrate for a measurement time `τ_M`:
  `S = ∫_0^{τ_M} dS(τ) = P + Q`, with the noise part `Q ∼ 𝒩(0, σ² τ_M)` independent of the
  state, and a deterministic-up-to-decay part `P`. Each realization of `S` is the soft
  outcome `μ` (after rescaling so the mean is `+1` for `μ̄ = 0`).
- **State-conditioned signal, Eqs. 29–36.** If the state is `|0⟩`: `P_0 = v τ_M`, so
  `S_0 ∼ 𝒩(v τ_M, σ² τ_M)`. If `|1⟩` and it decays at `K`:
  `P_{1|K} = −v(2K − τ_M)` for `K < τ_M`, else `−v τ_M` (Eq. 29). Marginalizing over the
  exponential `K` (Eqs. 30–36) and convolving with `Q` gives a closed-form `f_{S_1}` (Eq. 37,
  involving `erf`s). When `τ_M ≪ τ_A` decays are unlikely and `S_1 ≈ 𝒩(−v τ_M, σ² τ_M)`
  (i.e. back to symmetric Gaussian); as `τ_M → τ_A`, `f^(1)` is distorted and shifts toward
  `f^(0)`, driving `P(soft flip|1) → ½`.
- **Convenient parameterization, Eqs. 40–41 (means rescaled to ±1).** Define the
  **fluctuation time** `τ_F = 2σ²/v²`. Then the conditional densities depend only on the
  dimensionless ratios `τ_M/τ_F` and `τ_M/τ_A`:
  - `f^(0)(μ; τ_M, τ_A, τ_F) = √(τ_M/(2π τ_F)) · exp[ −(μ−1)² τ_M/(2 τ_F) ]` (a Gaussian of
    width `√(τ_F/τ_M)` centered at `+1`, Eq. 40).
  - `f^(1)(μ; τ_M, τ_A, τ_F)` is the asymmetric expression in Eq. 41 (a decay-broadened,
    `erf`-tailed density pushed toward `+1`).
  Physical reading: `τ_A` (set by materials/fabrication) bounds `τ_M` from above;
  `τ_F` (set by amplifier/coupling) bounds it from below. The "sweet spot" is
  `τ_F ≪ τ_M ≪ τ_A` — distinguishable Gaussians, few decays. The overlap decays
  exponentially in `τ_M/τ_F` for `τ_M ≪ τ_A`.
- **Soft-flip probabilities, Eqs. 42–43.** Integrating against a decision boundary `δ`:
  `P(soft flip|0) = ½[1 + erf(−δ/√2 · √(τ_M/τ_F))]` (Eq. 42), and an `erf`+`exp` expression
  for `P(soft flip|1)` (Eq. 43). The ML hardening map (Eq. 1) corresponds to a particular
  `δ(τ_M/τ_F, τ_M/τ_A)`; the paper varies `δ` and `τ_M` to optimize hard performance.

### Graphical model + sampling (Sec. 2)
- **Definition 2.1.** A graphical model for `T` rounds is `(G_T, p, f, ε)`: a fault
  hypergraph `G_T = (V_T, E_T)` with a spacetime vertex `(a,t)` per plaquette `a`, round `t`;
  per-edge fault probability `p_e`; per-vertex soft densities `(f_{a,t}^{(0)}, f_{a,t}^{(1)})`;
  a residual Pauli `ε_e` per edge. Boundary vertices `V_∂` correspond to perfect
  measurements.
- **Fault-set probability, Eq. 4:** `P(x) = ∏_{e∈x} p_e ∏_{e∉x} (1 − p_e)` (independent
  faults — correlations enter only through residual-error supports).
- **Syndrome, Eq. 5:** `ŝ_{a,t} = m̂_{a,t} + m̂_{a,t−1} (mod 2)` (consecutive-round
  difference of *hardened* outcomes, convention `m̂_{a,0}=0`). The soft outcome enters the
  decoder *through the weights*, not through the syndrome (the syndrome is computed from the
  hardened `m̂`).
- **Soft phenomenological (Sec. 2.3).** Stack `T+1` copies of `G_X`; horizontal edges =
  data X errors (prob `p_D`), vertical edges = ideal-outcome flips (prob `p_M`); each
  measurement vertex carries `(f^(0), f^(1)) = (𝒩(+1,σ²), 𝒩(−1,σ²))`. Hardening reproduces
  standard phenomenological noise exactly.
- **Soft circuit (Sec. 2.4, Fig. 6).** Each circuit fault location (idle-during-CNOT
  `p_{IG}/3`, idle-during-measure `p_{IM}/3`, CNOT `p_{CNOT}/15`, ideal-measurement-flip
  `p_M`) adds a hyperedge; measurement vertices additionally emit the continuous `μ ∼ f^(μ̄)`.
  Uses the *inclusive* (independent-fault) model for weights, *exclusive* for sampling (the
  two are equivalent, App. B / ref. [18]).

### Soft decoding graph and edge weights (Sec. 3.2) — the load-bearing formulas
- **Decoding graph `G̃_T`.** Take `G_T`, add a **soft vertical edge** `(a,t)–(a,t+1)` at each
  measurement vertex (so `G̃_T` may carry both a *hard* and a *soft* vertical edge between the
  same pair), and identify all boundary vertices to one **ghost vertex** `v_g`.
- **Likelihood ratio, Eq. 6.** For a measurement vertex `(a,t)` with soft outcome `μ` and
  hard outcome `μ̂` (`μ̄̂ = μ̂ + 1 mod 2`):
  `L_{a,t}(μ) = f_{a,t}^{(μ̄̂)}(μ) / f_{a,t}^{(μ̂)}(μ) ∈ [0,1]`
  (≤ 1 by definition of the ML hard outcome; it is the likelihood of the *less* likely class
  over the *more* likely class).
- **Edge weights, Eq. 7 (the formula to copy):**
  `w(e) = −log L_{a,t}(μ_{a,t})` if `e` is a **soft** vertical edge,
  `w(e) = −log[ p_e/(1 − p_e) ]` otherwise (data / hard edges).
  Both are **non-negative**. The decisive change from hard MWPM/UF: soft weights depend on the
  *observed continuous outcomes `m`*, so inter-vertex distances and geodesics **cannot be
  precomputed** — they are computed on the fly. With on-the-fly Dijkstra this leaves the
  asymptotic complexity unchanged (`O(d^{7.5})` MWPM with [36]; `O(d³α(d))` UF at 32-bit
  weight precision).
- **Gaussian closed form (the case we will use).** For symmetric Gaussian readout
  `f^(b) = 𝒩((−1)^b · 1, σ²)` (mean `+1` for `b=0`, `−1` for `b=1`), the log-likelihood-ratio
  weight reduces to an explicit function of `μ`. Writing the two log-densities and
  subtracting, `−log L_{a,t}(μ) = (2/σ²)·|μ|` for a soft edge (the quadratic `μ²/2σ²` terms
  cancel between numerator and denominator; the cross term `2μ/σ²` survives, and the magnitude
  follows because `μ̂ = sign`-thresholds at `0`). I.e. **the soft weight grows linearly with
  the confidence `|μ|` of the readout** — a confident measurement is an expensive edge to flip,
  a near-`0` (ambiguous) readout is cheap, exactly the desired behavior. (Derivable directly
  from Eqs. 6–7 with the Gaussian densities; the paper states the general Eq. 7 and leaves
  this Gaussian simplification implicit.)

### Soft MWPM (Algorithm 1) and the optimality proof (Sec. 4.2)
- **Algorithm 1.** (1) Compute soft-edge weights from `m` (Eq. 7); (2) compute the syndrome
  (Eq. 5) and its non-trivial vertices `v_1..v_k`; (3) build the complete **distance graph**
  `K(ŝ)` with weights `w_K({v_i,v_j}) = d_{G̃_T}(v_i,v_j)` (Dijkstra); (4) min-weight perfect
  matching `M`; (5–6) lift each matched pair to a geodesic in `G̃_T`, XOR the geodesics,
  restrict to `G_T`. If `k` is odd, add `v_g`.
- **Lemma 4.3 (Bayes identity, Eq. 10).** For a fault set `x` and soft outcomes `m`,
  `log P(x | m) = C + Σ_{e ∈ x̃} w(e)`, where `x̃ = x + x_soft` adds the soft-flip 1-chain and
  `C` is independent of `x`. *Proof sketch (Eqs. 11–14):* Bayes `P(x|m) ∝ P(m|x)P(x)`;
  `log P(x)` contributes the `−log p/(1−p)` (data) weights (Eq. 12); the continuous part
  `P(m|x)` factorizes over independent measurement vertices into the likelihood ratios
  `L_{a,t}` exactly where a soft flip occurred (Eq. 13), contributing the soft weights. Thus
  **minimizing total weight = maximizing the posterior fault probability**.
- **Theorem 4.1.** Under (C1) all edges rank-2 (graph, not hypergraph) and (C2) `p_e < 0.5`,
  soft MWPM returns a most-likely fault set. *Proof:* a contradiction argument — if some
  `x'` had higher posterior than the decoder's output, by Lemma 4.3 its weight would beat the
  matching, contradicting minimality.
- **Corollary 4.4.** Soft MWPM corrects every fault with `|x̃|_w < d_w/2`, where `d_w` is the
  weighted minimum distance (min `|x|_w` over logical faults) and `|a|_w = Σ_{e∈a} w(e)`.

### Soft Union-Find (Algorithm 2) and its guarantee (Sec. 3.4, 4.3)
- **Half-edge growth.** Work in the **split-edge graph** `H̃_T` (a vertex added at the middle
  of every edge; each `G̃_T` edge becomes two half-edges of weight `w(e)/2`). Initialize
  growth states `φ(e)=0`. While an odd cluster exists: pick the odd cluster of **minimum
  perimeter** (ties → least-recently-grown), grow all its boundary edges by
  `Δ_C = min_{e∈B(C)} (w_{H̃_T}(e) − φ(e))` (Eq. 8, the smallest increment that fully grows
  one boundary edge). Once all clusters are even, run the linear-time **peeling decoder** on
  the fully-grown sub-edges and restrict to `G_T`.
- **Differences from prior weighted UF [37]:** grows *half-edges* (in `H̃_T`) rather than full
  edges, and prioritizes the least-recently-grown cluster — both verified to slightly improve
  the hard-UF threshold too.
- **Theorem 4.5.** Under (C1), (C2) and **(C3)** "any trivial-syndrome `x̃` with
  `diam_w(x̃) < d_w` has `ε(x)` a stabilizer," soft UF corrects every fault with
  `|x̃|_w < d_w/2` (same sufficient condition as MWPM; proof via diameter/growth bounds
  Eqs. 15–20). Both soft phenomenological and soft circuit noise satisfy (C3).
- **Complexity.** With 32-bit weight precision, `O(d³ α(d))` (`α` inverse Ackermann) — far
  cheaper than soft MWPM, the practical choice and the one benchmarked in Sec. 5.

### Logical-rate estimation (Sec. 5.1 + App. C)
Per-round logical failure `p̄_d` is extracted from the protocol failure probability over `T`
rounds via the independent-per-round model `p̂^X_fail(T) = ½(1 − (1 − p̄)^T)` (Eq. 22),
inverted as `p̄_d(T) = 1 − (1 − 2 p^X_{d,fail}(T))^{1/T}`, `p̄_d = lim_{T→∞} p̄_d(T)`
(Eqs. 23–24; converges by `T ≈ 100`, Fig. 13). Thresholds are fit by the standard
universal-scaling quadratic in `x = (p − p*) d^{1/ν}` (App. D). Monte-Carlo success counts use
a Jeffreys-prior Beta posterior for honest credible intervals (App. D).

## Results (deep)
- **Soft phenomenological (Fig. 8, Table 1).** `p_D = p`, `p_M = 0`, `σ` chosen so
  `p_{M,hardened} = p`. Soft UF threshold **3.665(2)%** vs hard UF **2.637(1)%**. The optimal
  hard-decoder threshold (stat-mech mapping, Wang et al. [21]) is **2.93(2)%** — *still below*
  the soft UF threshold. **⇒ soft UF beats the optimal hard decoder by ≈ 25%.** This is the
  paper's headline and the cleanest statement that soft (continuous-readout) information is
  decoding capacity *unreachable* by any hard decoder.
- **Soft-to-hard ratio sweep (Fig. 9).** Fixing `p_{M,hardened} = p` and varying
  `r = p_{M,soft}/p_{M,hardened} ∈ [0,1]`: `r = 1` (all measurement noise is soft, no hard
  flip) is the Fig. 8 case (max soft benefit); `r = 0` (all hard flip) collapses to the hard
  threshold. The soft threshold rises monotonically with `r`, smoothly interpolating between
  the hard UF line and the +25% point. **Soft benefit scales with how much of the readout
  noise is genuinely soft (recoverable) vs an irreducible hard flip.**
- **Soft circuit (Figs. 10–11, Table 1).** `p_{IG}=p_{IM}=p_{CNOT}=p`, `p_M=0`, Gaussian
  readout. With `p_{M,hardened} = 10p` (readout 10× noisier than gates, realistic for many
  platforms): soft UF **0.5824(6)%** vs hard UF **0.4991(5)%**. With `p_{M,hardened} = p`
  (readout = gate error): soft UF **0.727(1)%** vs hard UF **0.702(1)%** — the gap **shrinks**
  because ancilla/circuit errors (not measurement) dominate. Sub-threshold `p̄_d` curves
  (Fig. 11, `d = 11/15/19`, `T = 1000`) show the soft decoder is better below threshold too,
  not only at the crossing.

  | Soft noise model | Soft UF threshold | Hard UF threshold |
  |---|---|---|
  | Phenomenological (`p_D=p, p_M=0`, `p_{M,hardened}=p`) | **3.665(2)%** | 2.637(1)% |
  | Circuit (`p_{IG}=p_{IM}=p_{CNOT}=p, p_M=0`, `p_{M,hardened}=p`) | 0.727(1)% | 0.702(1)% |
  | Circuit (same, `p_{M,hardened}=10p`) | **0.5824(6)%** | 0.4991(5)% |
  | — optimal *hard* decoder, phenomenological [21] | (ceiling) 2.93(2)% | — |

  *(Table 1 of the paper; the optimal-hard ceiling is the Wang–Harrington–Preskill stat-mech
  value cited in Sec. 5.2.)*
- **Measurement-time tradeoff (Fig. 12, Sec. 6).** Parametric circuit model with
  `τ_G = 10 ns`, `τ_D = 30 μs`, `τ_A = 15 μs`, `τ_F = 100 ns`, varying `τ_M`; fault
  probabilities derived from durations (`p_{IG}=1−e^{−τ_G/τ_D}`, etc.). The optimal `τ_M` for
  soft UF sits near `τ_M/τ_A ≈ 1×10⁻²` with `p̄_d ≈ 1×10⁻⁷` at `d=19`. If `τ_M` is instead
  chosen to minimize the **average per-measurement soft-flip probability**
  `½[P(soft flip|0) + P(soft flip|1)]` (the metric used in many experimental readout-fidelity
  demos), `τ_M` is ~5× longer and `p̄_d` jumps ~1000× to ≈ 1×10⁻⁴. Also the soft decoder's
  optimal `τ_M` is **shorter** than the hard decoder's — the right objective is not a function
  of soft-flip probabilities alone. **⇒ optimize measurement time against logical error, not
  against single-shot readout fidelity.**

## Methodology assessment
| Criterion | 1–5 | Assessment |
|---|---|---|
| Soundness | **5** | Soft weights are *derived from Bayes* (Lemma 4.3), not posited; optimality (Thm. 4.1) and correction guarantees (Cor. 4.4, Thm. 4.5) proven; amplitude-damping channel derived from a stochastic signal model (App. A). |
| Novelty | **4** | First *generic* (encoding-independent) soft-decoding framework for the surface code with MWPM **and** UF; prior soft-MWPM work was GKP-specific [11–14]. A real, useful step; the "+25% over optimal hard" framing is the standout. |
| Reproducibility | **4** | All weight formulas, both algorithms, the noise parameterizations, the per-round-rate model, and the Beta/Jeffreys statistics are explicit. No public code in v1; 32-bit weight precision stated. |
| Experimental design | **5** | Phenomenological + circuit, multiple `d` (up to 19), `r`-sweep, `p_{M,hardened}∈{p,10p}`, a physically parameterized `τ_M` study; soft compared to hard at matched `p_{M,hardened}` (fair). |
| Statistical rigor | **4** | Finite-size-scaling threshold fits with shaded uncertainty; Beta-posterior credible intervals; honest about the per-round model's asymptotic-`T` validity (Fig. 13). |
| Scalability | **4** | Soft UF keeps `O(d³α(d))`; soft MWPM `O(d^{7.5})` with [36]; the only cost is on-the-fly distances/geodesics (weights are data-dependent). |

## Strengths
- **S1 — the soft weight is the *Bayes-optimal* weight, with a one-line formula (Eqs. 6–7,
  Lemma 4.3).** `w(e) = −log L_{a,t}(μ)` is not a heuristic confidence score; Lemma 4.3 proves
  total weight = `−log P(x|m) + const`, so min-weight matching *is* maximum-likelihood
  decoding. This is the cleanest possible justification for the weight we will reuse.
- **S2 — encoding-independent modeling (Sec. 1.3).** The decoder needs *only* the conditional
  densities `f^(μ̄)(μ)` — nothing about the physical qubit. This is exactly the abstraction our
  SIM-ONLY teacher wants: pick any `f^(b)`, the rest of the pipeline is unchanged.
- **S3 — a physically derived asymmetric channel with a tunable time knob (App. A).** The
  amplitude-damping model gives closed-form `f^(0)`, `f^(1)` (Eqs. 40–41) parameterized by
  `(τ_M, τ_A, τ_F)`, capturing measurement-time-dependent `T₁` disturbance and the
  resolution/disturbance tradeoff — a ready-made, more realistic-than-Gaussian readout teacher.
- **S4 — the "+25% above any hard decoder" result (Sec. 5.2).** By referencing the stat-mech
  optimal-hard ceiling [21], the paper shows the soft gain is *above the information-theoretic
  limit of hard decoding* — the precise sense in which soft readout is genuine headroom.

## Weaknesses / limitations
- **W1 — amplitude damping here is NOT leakage.** The App. A channel is **measurement-induced
  `T₁` relaxation** (`|1⟩→|0⟩`) acting on the *readout signal*; it is the soft-readout/`T₁`
  axis, not the `|1⟩→|2⟩` **leakage + seepage** axis. Our program needs leakage separately —
  this paper does not supply it.
- **W2 — symmetric Gaussian is the workhorse; asymmetry handled but lightly studied.** The
  threshold numerics (Figs. 8–11, Table 1) all use symmetric `𝒩(±1, σ²)`. The asymmetric
  amplitude-damping channel is used only for the `τ_M` study (Sec. 6), and the decoder there
  still derives weights from the (possibly asymmetric) `f^(0)/f^(1)` ratio. Real IQ readout can
  have correlated-`I/Q`, non-Gaussian, or state-dependent-variance structure not covered.
- **W3 — phenomenological/circuit only; no hardware, no full state-of-the-art baseline.** No
  real-device data; the comparison is soft-vs-hard *UF/MWPM* (plus the stat-mech hard ceiling).
  It does **not** compare against neural decoders (AlphaQubit-style soft-input decoders) or
  TN-MLD; "+25%" is over hard *graph* decoders, not over all soft-capable decoders.
- **W4 — rank-2 / graph restriction (C1).** Decoders require `G_T` to be a genuine graph
  (all edges rank 2); general hyperedge faults (3-body and up) are explicitly excluded
  because the most-likely-fault problem becomes NP-hard. Correlated/hyperedge soft decoding
  is out of scope — relevant since our `hypergraph_dem` substrate is built for hyperedges.
- **W5 — last round assumed perfect; `T=d`-style protocol.** The success proofs and the
  protocol (Sec. 5.1) assume a final *perfect* measurement round to return to the code space;
  the per-round rate is an extrapolation (App. C) valid for large `T`.
- **W6 — UF guarantee is *sufficient*, not tight.** Theorem 4.5 gives `|x̃|_w < d_w/2` as a
  sufficient correction condition; soft UF is an *approximation* to the ML soft MWPM, so its
  actual performance (though empirically close) is not proven optimal.

## USEFUL FOR OUR PROJECT (the load-bearing section)

**Program context.** The twin's non-Pauli pivot (MEMORY: *Decoder gate + frontier caveat*,
2026-06-19) is to a **SIM-ONLY teacher** that generates **realistic non-Pauli** surface-code
syndrome data (leakage / soft readout / `T₁T₂`) and a soft/affine decoder (TN-affine GNN /
Transformer), de-risked by the **Bayes-floor-vs-Pauli gap on rich-noise sim**. This paper is
the **direct, citable reference for the SOFT-READOUT half**: how to *model* continuous
(Gaussian-IQ) measurement, and how to *decode* it with provably ML soft weights. The two
artifacts below are copy-ready.

### 1. Soft-readout (Gaussian-IQ) likelihood model for our teacher
Use the **encoding-independent conditional-density abstraction** (Sec. 1.3, Fig. 2): every
ancilla measurement in the teacher emits a **continuous** soft outcome `μ` instead of a bit.

- **Minimal model (start here): symmetric Gaussian readout.** Per measurement vertex, sample
  `μ ∼ 𝒩(+1, σ²)` if the ideal outcome is `0`, `μ ∼ 𝒩(−1, σ²)` if `1`
  (Sec. 1.3; used throughout Sec. 5). `σ` is the (inverse) readout SNR; tune it to a target
  hardened flip rate `p_{M,hardened}` via Eq. 3 (`p_{M,hardened} = p_M + p_{M,soft} −
  p_M p_{M,soft}`) so the soft teacher is comparable to our existing Pauli/hard models at fixed
  effective readout error. This is the **non-Pauli measurement signal** whose discretization
  loss is the headroom.
- **Realistic model (the `T₁`/measurement-time teacher): Gaussian soft noise with amplitude
  damping (App. A).** Sample the integrated dispersive signal `S = P + Q` with
  `Q ∼ 𝒩(0, σ²τ_M)` and the decay-conditioned `P` (Eqs. 26–37), or directly use the closed-form
  conditional densities `f^(0)(μ; τ_M, τ_A, τ_F)` (Eq. 40) and `f^(1)(μ; τ_M, τ_A, τ_F)`
  (Eq. 41), parameterized by measurement time `τ_M`, `T₁`-time `τ_A`, and fluctuation time
  `τ_F = 2σ²/v²`. This gives an **asymmetric, time-tunable** readout channel — the right teacher
  for studying the resolution/disturbance tradeoff and for generating data where the soft
  benefit and `T₁` couple. Representative experimentally-motivated values (Sec. 6):
  `τ_G=10 ns, τ_D=30 μs, τ_A=15 μs, τ_F=100 ns`, sweet spot `τ_F ≪ τ_M ≪ τ_A`.
- **Where it plugs in.** This is the measurement-emission layer of a graphical model
  `(G_T, p, f, ε)` (Def. 2.1) — identical in shape to our DEM/`hypergraph_dem` substrate; the
  data-error layer (`p_e`, residual Paulis) is unchanged, and only the per-vertex density pair
  `(f^{(0)}, f^{(1)})` is added. So the soft-readout teacher is an *additive* modification of
  the existing forward, not a rewrite.

### 2. Soft-decoder weight formulas for soft-readout decoding (decode the continuous data)
The single object to reuse is the **per-vertex log-likelihood-ratio soft edge weight**:

- **Likelihood ratio (Eq. 6):** `L_{a,t}(μ) = f^{(μ̄̂)}_{a,t}(μ) / f^{(μ̂)}_{a,t}(μ) ∈ [0,1]`,
  where `μ̂` is the ML-hardened bit (Eq. 1) and `μ̄̂` its complement.
- **Soft / hard edge weights (Eq. 7):**
  `w(soft vertical edge) = −log L_{a,t}(μ_{a,t})`,
  `w(data/hard edge) = −log[ p_e/(1−p_e) ]`. Both non-negative.
- **Gaussian closed form (the one we will implement):** with `f^{(b)} = 𝒩((−1)^b, σ²)`, the
  soft-edge weight is `−log L_{a,t}(μ) = (2/σ²)·|μ_{a,t}|` (the `μ²` terms cancel; the
  cross-term survives). **Confidence `|μ|` ↦ edge cost linearly**: a confident readout is an
  expensive edge to break, an ambiguous (`μ≈0`) readout is cheap — the entire point of soft
  decoding, and trivial to drop into a weighted matcher.
- **Decoder integration.** Build the decoding graph `G̃_T` (add one soft vertical edge per
  measurement vertex, identify the boundary to a ghost vertex), compute the syndrome from the
  *hardened* outcomes (Eq. 5), then run **standard MWPM or UF** with these weights — Algorithm 1
  (soft MWPM, provably ML, Thm. 4.1) or Algorithm 2 (soft UF, almost-linear, Thm. 4.5). The
  only implementation cost vs the hard case: weights/distances are data-dependent and computed
  on the fly. Practically, the soft weights can also feed a **TN-MLD or a learned (GNN/
  Transformer) decoder** as continuous inputs — which is exactly our planned "TN-affine GNN/
  Transformer" soft decoder; this paper provides the *graph-decoder* baseline and the exact
  Bayes-optimal weight those learned decoders must beat or match.

### 3. The headroom claim our de-risk needs
"+25% threshold over the optimal hard decoder" (Sec. 5.2: 3.665% soft UF vs 2.93% stat-mech
optimal-hard [21]) is the published, quantitative statement that **soft-readout information is
decoding capacity above any Pauli/hard decoder** — i.e. the *Bayes-floor-vs-Pauli gap* our
program proposes to own, demonstrated for measurement softness specifically. Use it as:
(i) the **existence proof** that the soft-readout gap is real and sizable (not a rounding
effect); (ii) the **direction** (gap grows with the soft fraction `r`, Fig. 9; and with
readout-vs-gate noise ratio, Table 1 — largest where readout dominates, `p_{M,hardened}=10p`);
(iii) a **sanity ceiling** — on *phenomenological* soft noise the achievable gain tops out
around +25%; richer circuit noise shrinks it (ancilla errors dilute the measurement-softness
benefit), so our sim-only headroom claim should expect a *smaller* number once full circuit
faults are included.

### 4. Co-design hook (secondary, but on-program)
The measurement-time result (Sec. 6, Fig. 12: ~1000× logical-rate swing for 5× `τ_M` at `d=19`;
the soft-optimal `τ_M` differs from the hard-optimal) is the concrete argument that the readout
parameter (`τ_M`) must be optimized against **logical** error, not single-shot fidelity. If the
twin's `manipulate`/`do()` axis ever touches a readout knob, this is the reference for "the
right objective is the QEC-layer LER," and the amplitude-damping channel (App. A) is the
differentiable, parameterized substrate to optimize over.

## What does NOT apply (carry as caveats)
- **Leakage is absent.** "Amplitude damping" here = measurement-time `T₁` relaxation on the
  readout signal (`|1⟩→|0⟩`), **not** `|1⟩→|2⟩` leakage + seepage (W1). For the leakage axis we
  need a separate reference/teacher; do not cite this paper for leakage.
- **Hyperedge/correlated soft decoding is out of scope.** (C1) forces a rank-2 graph (W4); the
  paper's optimality proofs do not extend to 3-body+ hyperedges (NP-hard). Our `hypergraph_dem`
  multi-body terms cannot use soft MWPM/UF directly — they need the TN/learned route.
- **Baseline is hard graph decoders, not the soft frontier.** "+25%" is over hard MWPM/UF and
  the stat-mech optimal *hard* decoder, **not** over soft-capable neural/TN decoders (W3). Our
  contribution bar remains "beat the *shipped soft frontier*" (e.g. AlphaQubit-style soft-input
  decoders), not "beat hard MWPM" — this paper sets the *floor*, not the frontier.
- **Symmetric Gaussian is idealized.** Real IQ blobs can be non-Gaussian, correlated across
  `I/Q`, or have state-dependent variance (W2); the closed-form weight `(2/σ²)|μ|` is the
  symmetric-Gaussian special case. Our teacher can use richer `f^{(b)}` (the Eq. 6–7 weight is
  general), but the clean linear weight is Gaussian-only.
- **Perfect final round / large-`T` extrapolation.** The success guarantees assume a perfect
  terminating measurement and the per-round rate is an asymptotic-`T` model (W5); our sim
  protocol should match this convention when comparing to the paper's numbers.

## How to use / trust + open questions
- **Trust:** high as the **soft-readout model + soft-decoder-weight reference**. The Gaussian-IQ
  likelihood (Sec. 1.3 / App. A) and the Bayes-optimal weight `w = −log L` (Eqs. 6–7,
  Lemma 4.3) are exact and directly reusable. Carry W1 (no leakage), W3 (floor not frontier),
  W4 (graph only).
- **Adopt now:** (i) the symmetric-Gaussian readout emitter `𝒩(±1, σ²)` and the
  amplitude-damping emitter (Eqs. 40–41) as the **soft-readout layer of our SIM-ONLY teacher**;
  (ii) the soft edge weight `−log L_{a,t}(μ)` (Gaussian form `(2/σ²)|μ|`) as the **soft-decoder
  baseline** and as the continuous-input feature for the planned TN-affine GNN/Transformer
  decoder; (iii) Eq. 3 to **tune `σ` to a target `p_{M,hardened}`** for fair soft-vs-hard
  comparison.
- **Open questions for the program:** (i) Quantify our **Bayes-floor-vs-Pauli gap on
  soft-readout sim** and compare to this paper's +25% (expect smaller under full circuit noise).
  (ii) Combine soft readout **with leakage and `T₁T₂`** in one teacher — this paper supplies the
  readout half; the leakage half is the missing reference. (iii) Extend soft weights to
  **hyperedges** (where soft MWPM/UF cannot go) via the TN/learned decoder — this is precisely
  the "non-Pauli signal SI1000 misses → TN/GNN" thread (MEMORY: decoding-floor program).
  (iv) Does the soft-optimal `τ_M` ≠ hard-optimal `τ_M` finding (Sec. 6) give a `do()`-knob
  prioritization (optimize readout time against LER) once the twin has a soft teacher?
