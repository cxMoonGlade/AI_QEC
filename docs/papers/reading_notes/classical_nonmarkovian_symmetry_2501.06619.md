# Full-text review — Watkins & Quiroz, "Classical Non-Markovian Noise in Symmetry-Preserving Quantum Dynamics" (arXiv:2501.06619v2; PRL 135, 140401 (2025))

> **Provenance (2026-07-03): FULL-TEXT read (精读).** Cached full text
> `outputs/papers/2501.06619.txt` (WSL path; also reachable as
> `\\wsl.localhost\ubuntu-f\home\cx\Document\AI_QEC\AI_QEC\outputs\papers\2501.06619.txt`),
> 8 pp (6 pp main text + refs), read end-to-end incl. reference list. All §/Eq/Fig refs are from
> that text; the plotted density matrices (Figs. 1, 2) are not pixel-extracted — the load-bearing
> NUMBERS quoted here are those stated in the running text. **Authored by opus subagent 2026-07-03;
> pending principal spot-verification.** Tags: **[paper]** = stated in the paper; **[twin]** = our
> application/inference for `qec_twin`, NOT the paper's claim. **Supplemental Material [ref 59] NOT
> downloaded or read** (linked at `http://link.aps.org/supplemental/10.1103/t78h-c9s3`); this note covers
> the 6-page main text + reference list only.

## Metadata [paper]
- **Authors / affiliation.** William M. Watkins, Gregory Quiroz (William H. Miller III Department of Physics
  & Astronomy, Johns Hopkins University; Johns Hopkins University Applied Physics Laboratory).
- **Venue / status.** arXiv:2501.06619v2 [quant-ph], 3 Sep 2025; published PRL 135, 140401 (2025). 6 pp
  main text + acknowledgments + references. **Supplemental Material** at
  `http://link.aps.org/supplemental/10.1103/t78h-c9s3` (includes the su(4) root space decomposition
  worked example, further FFF details, and Refs. [81–88]) — NOT read.
- **Type.** **Analytic framework** (representation theory + filter function formalism) with two
  **numerical demonstrations** (TFIM, [[4,2,2]] QED code) under classical temporally correlated
  (non-Markovian) noise. NOT a standalone simulator, NOT an experimental paper.

## Executive summary [paper]
Develops a formalism to quantify the impact of **classical non-Markovian noise** on quantum dynamics with
**dynamical symmetries**. Prior work on symmetries in open quantum systems (Albert & Jiang, Lostaglio et
al.) was restricted to **Markovian** Lindblad dynamics. This paper extends the analysis to temporally
correlated (colored) noise by combining **root space decompositions** of the Lie algebra su(N) with the
**filter function formalism (FFF)**. Main results:

- **q-basis block diagonalization (Eq. 7):** The control matrix `R^i_mu(t)` (representing the frame-transformed
  noise Hamiltonian) is block diagonal **iff** computed in a generator basis derived from the symmetry
  eigenspace decomposition. This identifies a large set of identically-zero filter functions, reducing the
  number of FFs needed from `O(N^4)` to `O(N_q^4)` where `N_q = dim Z(q)` and typically `N_q << N`.
- **Symmetry-preserving noise (Eq. 8):** When noise operators commute with the symmetry subalgebra, the
  noise-averaged density operator remains confined to the symmetry-preserving subspace (SPS) — decoherence
  but no leakage.
- **Symmetry-breaking noise (Eqs. 9–10):** Noise operators that do not commute with the symmetries induce
  transitions out of the SPS, but the averaged state is **block diagonal in the symmetry representation**
  — coherence between distinct symmetry eigenspaces is fully killed by ensemble averaging.
- **Weak-noise bound (Eq. 11):** The trace distance `D = 1/2 ||(U_E - U_0)[rho(0)]||_1` decouples into
  a symmetric-noise sum over `h(q) + g(q)` and a nonsymmetric-noise sum over `g(q -> q')`, making the
  leakage contribution explicitly additive.

## Technical method — the three-layer structure [paper]

### Layer 1: Symmetry-informed operator basis (Eqs. 1–5)
Given a set of commuting symmetries `{Q_i}` with `[Q_i, H_0(t)] = 0` (Eq. 1), the Hilbert space
decomposes as `H_S = \bigoplus_{vec{q}} V(vec{q})` (Eq. 3). The Lie algebra `g = su(N)` is decomposed
via Cartan subalgebra `h` constructed to contain `q = span[{Q_i}]`, yielding:

```
g = bigoplus_{vec{q}} [h(vec{q}) ⊕ g(vec{q})]  ⊕  bigoplus_{vec{q},vec{q}'} g(vec{q} -> vec{q}')
```
(Eq. 5). The subspaces: `h(vec{q})` projects the Cartan into the `vec{q}` eigenspace, `g(vec{q})` are
ladder operators preserving the eigenvalues (symmetry-preserving), and `g(vec{q} -> vec{q}')` are ladder
operators transitioning between eigenspaces (symmetry-breaking). This is the **generalization of the
total-spin `|j,m><j',m'|` operator indexing** to any abelian set — a key unifying insight.

### Layer 2: Filter function formalism (Eqs. 6–7)
The noisy dynamics are isolated via the reverse interaction picture: `U(T,0) = \tilde{U}_E(T,0) ∘ U_0(T,0)`.
Under a **weak-noise assumption** (`||H_E|| T << 1`), the cumulant expansion is truncated at second order:

```
C(T) = Σ_{ij} (χ^{(1)}_{ij}(T) A_{ij} + χ^{(2)}_{ij}(T) B_{ij})
```
(Eq. 6), where `A_{ij} = [x_i, [x_j, ·]]` (dissipative) and `B_{ij} = [[x_i, x_j], ·]` (coherent,
uniquely from noise correlations). The coefficients `χ^{(1)}_{ij}, χ^{(2)}_{ij}` are **spectral overlaps**
integrating the noise PSD `S_{μν}(ω)` against filter functions `F^{μν}_{ij}(ω,T), G^{μν}_{ij}(ω,T)`.

The control matrix `R^i_μ(t) = Tr[U_0(T,t)[x_i] x_μ]` (the frame-transformed noise generator expansion)
is the computational bottleneck. The paper's key structural result (Eq. 7):
```
R^i_μ(t) = 0  if  x_i ∈ h(vec{q}_1)⊕g(vec{q}_1), x_μ ∈ h(vec{q}_2)⊕g(vec{q}_2), vec{q}_1 ≠ vec{q}_2
```
— the control matrix is **block diagonal in the q-basis**. This follows because the rotating-frame
operator `U_0(T,t)[x_i]` preserves the root projection `α(vec{q})` of `x_i`.

### Layer 3: Error channel characterization (Eqs. 8–11)
- **Symmetry-preserving noise** (`N_μ ∈ Z(q)` the centralizer): `C(T)[h(vec{q})⊕g(vec{q})] ⊆ h(vec{q})⊕g(vec{q})`
  → the noisy state stays in the SPS (Eq. 8).
- **Symmetry-breaking noise** (uncorrelated with symmetric components): `C(T)[h(vec{q})⊕g(vec{q})] ⊆
  \bigoplus_{vec{q}'} [h(vec{q}')⊕g(vec{q}')]` → block diagonal in symmetry representation, no inter-block
  coherence (Eqs. 9–10).
- **Weak-noise bound** (Eq. 11): `D ≤ Σ_{sym} ψ^{μν}_{ij}(T) + Σ_{nonsym} ψ^{μν}_{ij}(T)`, where
  `ψ^{μν}_{ij}(T)` integrates the PSD times the **magnitude** of FFs (not the signed spectral overlaps).
  The second sum runs over **all** target eigenspaces, so leakage increases the bound substantially.

## Numerical examples (Figs. 1–2) — the demonstration [paper]

### Example 1: TFIM with total-spin symmetry (Fig. 1)
- **System:** Transverse-field Ising model `H_0 = Σ_{ij} J_{ij} σ^z_i σ^z_j + h Σ_i σ^x_i` with
  all-to-all uniform `J_{ij} = J`. Symmetry: **total angular momentum `J^2`** (n eigenvalues, not just
  Z_2). Initial state: `|+>^{⊗n}` (symmetric subspace, `j = n/2`). `n = 4` due to computational
  constraints (same qualitative behavior for larger n stated but not shown).
- **Noise:** Pink noise `S(ω) ~ 1/ω` with IR and UV cutoffs. Two variants:
  - **Global dephasing** `β_i(t) = β(t)` ∀i → `H_E(t) = n β(t) J_z` commutes with `J^2` → **symmetry-preserving**.
    Fig. 1(a): density matrix block diagonal in the symmetry sectors `j = {0, 1, 2}`, all weight in the
    symmetric (`j = 2`) subspace. Decoherence within SPS only.
  - **Local dephasing** (independent noise per site) → breaks `J^2` → **symmetry-breaking**. Fig. 1(b):
    transitions out of SPS into `j = 0, 1` sectors. The averaged state is block diagonal — no coherence
    between different `j` sectors.
- **Statistics:** Ensemble of 20,000 noise trajectories; simulation time `T ≈ 2τ` where `τ` is the noise
  correlation length (exponential fit to autocorrelation).

### Example 2: [[4,2,2]] quantum error-detecting code (Fig. 2)
- **System:** The [[4,2,2]] code encodes 2 logical qubits into 4 physical qubits with stabilizers `{X^{⊗4},
  Z^{⊗4}}`. The encoded Hamiltonian commutes with both stabilizers; the logical states span the eigenspace
  `vec{q}_L = (+1, +1)`. The symmetry subalgebra is **two-dimensional**: `q = span[{X^{⊗4}, Z^{⊗4}}]`.
- **Noise:** Pink noise, no spatial correlations (`S_{ij}(ω) = 0` for `i ≠ j`). Two variants:
  - **Single-axis X noise** `H_E(t) = Σ_i β^x_i(t) σ^x_i` → breaks `Z^{⊗4}` symmetry but preserves `X^{⊗4}`.
    Fig. 2(a): leakage from `(+1,+1)` into the subspace with flipped `Z^{⊗4}` parity (`−1`).
  - **Multiaxis noise** `H_E(t) = Σ_i (β^x_i(t) σ^x_i + β^z_i(t) σ^z_i)` → breaks **both** symmetries.
    Fig. 2(b): leakage into all three other eigenspaces `{(+1,−1), (−1,+1), (−1,−1)}`.
- **Key claim:** The state is block diagonal in the symmetry basis; the logical filter functions and errors
  are characterized by `e^{C(T)}[ρ_0(T)] ∈ h(vec{q}_L) ⊕ g(vec{q}_L)`. The framework identifies the
  **subalgebra causing temporally correlated logical errors**, informing error characterization, recovery,
  and logical gate design.

## Limitations [paper]

- **L1 — Classical noise only.** The formalism is restricted to **classical stochastic processes**
  (wide-sense stationary Gaussian). The paper flags generalization to stochastic quantum baths as "future
  study" (Conclusions). This means the framework does not cover quantum (non-commuting) noise correlations,
  which limits direct application to the quantum-bath asymmetry we track through Bones A–C.
- **L2 — Weak-noise / second-order truncation.** The cumulant expansion is truncated at second order
  under `||H_E|| T << 1`. This excludes strong-coupling or long-time regimes where higher cumulants
  contribute — the noise PSD is integrated only through quadratic spectral overlaps.
- **L3 — Numerical scope is limited.** n=4 TFIM only (qualitative scaling stated but not shown); [[4,2,2]]
  QED code at 4 qubits. No large-system numerics, no threshold calculation, no decoder analysis.
- **L4 — No QEC decoding or error correction analysis.** The [[4,2,2]] example is **error-detection only**
  (pre-post-selection, no feedback/decoding). The paper never computes logical error rates or detection
  event rates under a real decoder — it characterizes the state dynamics before any correction step.
- **L5 — Noise PSD specifics don't affect algebraic structure.** Pink noise `S(ω) ~ 1/ω` is the concrete
  choice, but the algebraic results (Eqs. 5–11) are PSD-agnostic. The quoted "block diagonal in the
  q-basis" holds for any classical stationary noise.
- **L6 — No gauge/identifiability analysis.** The paper does not discuss the observational alias,
  parameter identifiability, or gauge degrees of freedom that are central to our twin's `recover`
  capability and our identifiability program (ADR 0005).
- **L7 — No closed-form detector statistics or moment ratios.** No detection-event rates, no
  detector-moment calculations, no double-factorial or `d!!` scaling. No overlap with our
  syndrome-silent-floor or coherent-wedge characterization claims.

## Strengths [twin assessment]

- **S1 — Clean algebraic framework that bridges two toolsets.** Combining Cartan/root space decomposition
  (from Lie theory / quantum control) with the filter function formalism (from noise spectroscopy)
  is a genuinely novel synthesis. The q-basis block diagonalization (Eq. 7) is a precise, general
  structural result that identifies an exponential savings in FF computation. This is directly usable as a
  **theorem-grade** (epistemic class (a)) statement: for any classical stationary noise and any set of
  commuting symmetries, the control matrix of the frame-transformed noise is block diagonal in the symmetry
  eigenspace basis — independent of noise PSD specifics.
- **S2 — Non-Markovian gap filled.** Prior work (Albert & Jiang 2014, Lostaglio 2017, Albert 2019) on
  symmetries in open quantum dynamics was Lindblad/Markovian only. This paper extends to finite-memory
  (colored) classical noise, which is the relevant model for 1/f flux noise, charge noise, and TLF
  environments in solid-state qubits.
- **S3 — Clean statement of when symmetry helps or hurts.** Symmetry-preserving noise = decoherence
  within SPS, no leakage. Symmetry-breaking noise = leakage + block diagonal (no cross-sector coherence).
  The weak-noise bound makes the additive contribution of leakage explicit. This provides a precise
  language for discussing **secular/non-secular** noise structure in qubit registers.

## Weaknesses [twin assessment]

- **W1 — No bridge to QEC observables.** Despite the [[4,2,2]] example, the paper gives no
  decoder-integrated quantities: no logical error rate, no detection-event rate, no threshold. The
  block-diagonal density matrix is a **state-level** statement, not a **record-level** (syndrome/decoder)
  statement. This leaves a gap between their algebraic decomposition and any observable a QEC
  experiment would report.
- **W2 — PSD integrals left abstract.** The spectral overlaps `χ^{(1)},\ χ^{(2)}` are expressed as
  integrals over `S_{μν}(ω)` times filter functions, but **no closed-form evaluation** is given for any
  concrete noise PSD. The pink noise example is numerical only. For our coherent-wedge characterization,
  we would need explicit formulas linking PSD parameters to decoherence rates — the paper provides the
  framework but does not carry it through to closed-form rates.
- **W3 — No explicit connection to our coherent↔incoherent split.** The cumulant expansion's `A_{ij}`
  (dissipative) vs `B_{ij}` (coherent, from noise correlations) terms (below Eq. 6) are mentioned but
  **not developed** into a practical decomposition of the noise channel into coherent and incoherent
  components. The paper cites the Liouvillian FFF (Cerfontaine et al. 2021, Hangleiter et al. 2021)
  for this, but does not itself exploit the split for any QEC conclusion. Our Girsanov split (Kaufmann
  2307.08741, Ivashkov 2603.05492) remains the primary tool for that decomposition.
- **W4 — No analysis of spatially correlated noise.** The two examples are global vs local (TFIM) or
  single-axis vs multiaxis (QED code) — but none uses **spatially correlated** (common-mode) noise
  across all qubits with spatial coupling structure. The pink noise is temporally correlated but
  spatially independent (`S_{ij}(ω) = 0` for `i ≠ j` in the local noise case). So the paper does not
  touch the **common-fluctuator / collective-dephasing / spatially-correlated** regime (Layden
  1903.01046, Clader 2101.11631) that drives our A9 syndrome-silent-floor program.

## Relevance to the twin [twin]

1. ***The** reference for symmetry-informed filter-function analysis of non-Markovian noise.* For our
   `recover` capability, when we analyze detector records under temporally correlated noise, the
   q-basis block diagonalization (Eq. 7) provides a **theorem-grade framework** for reducing the
   control matrix to its non-vanishing symmetry blocks. This is directly applicable to our stabilizer-code
   twin: the stabilizer group `G` plus logical operators `L` form the symmetry subalgebra `q`, and
   noise operators that commute with `G` stay in the code space (SPS analog), while non-commuting noise
   operators produce block-diagonal leakage in the `(stabilizer, logical)` eigenvalue representation.

2. **Connects but does not compress our coherent-wedge observables.** The paper's framework is
   **adjacent to, but does not preempt** our coherent-wedge characterization because (W1) the paper
   does not compute any detector-level observable, (W2) does not develop the coherent/incoherent
   split into a practical decomposition, and (W4) does not address spatially correlated common-mode
   noise. The paper's structural results (Eqs. 5–11) are (a)-class (exact, algebra-derived) and can be
   cited as theorem-grade statements about how classical non-Markovian noise distributes across symmetry
   sectors — but they do not produce any QEC record-level prediction that would duplicate our
   syndrome-silent-floor or detection-rate results.

3. **Direct analog to our detector-layer symmetry analysis.** The [[4,2,2]] example's symmetry subalgebra
   `q = span[{X^{⊗4}, Z^{⊗4}}]` is structurally identical to a stabilizer group acting as the symmetry
   generator — the paper's statement "no coherence between eigenspaces after ensemble averaging"
   translates directly to the statement that **ensemble-averaged syndrome outcomes are classical
   probability distributions over stabilizer eigenvalues, with no inter-sector coherence**. This is
   already assumed (implicitly or explicitly) in all DEM / Pauli-frame approaches, but the paper provides
   a clean algebraic justification for when and why it holds: it holds for **any** classical stationary
   noise, regardless of noise color, under second-order cumulant truncation.

4. **Potential use in our filter-function-based characterization of non-Markovian coherent noise.** If
   our `understand` capability develops a filter-function analyzer for syndrome records under
   temporally correlated coherent Z noise, the paper's framework gives the correct symmetry-adapted
   generator basis. In particular, the **control matrix block diagonalization** (Eq. 7) tells us exactly
   which filter functions are identically zero for a given symmetry structure — potentially reducing the
   computational burden of a syndrome-FFF analysis by the same `O(N^4) → O(N_q^4)` factor the paper
   reports.

5. **No overlap with our A9 syndrome-silent-floor claims.** The paper does not compute:
   (i) any detection-event rate,
   (ii) logical error rate at fixed detector marginals,
   (iii) double-factorial moment ratios (Clader 2101.11631),
   (iv) detection-rate decrease at fixed marginals (our A9(c) candidate).
   So it does not compress any of our A9 claims to (a). It remains a **framing/structural reference**
   (the algebraic analysis of symmetry-block-diagonal noise) that informs but does not preempt.

## Classification in our reading-note corpus

| Category | Fit |
|---|---|
| **Noise source / bath-spectrum anchor** | Weak — pink noise chosen illustratively, no concrete PSD-to-rate closed forms |
| **Simulator engine landscape** | No — analytical framework only, no standalone simulator |
| **Surface-code / coherent-error / harden-frontier** | Tangential — the [[4,2,2]] QED code is error-detection only, not surface-code |
| **Non-Markovian noise learning & engine landscape** | Adjacent — the FFF framework is the shared language, but the paper is analytic rather than estimation/learning |
| **Quantum-noise / record-classicality probes** | No — no record-level analysis |
| **Correlated-noise QEC / spectroscopy anchors** | Adjacent — provides the algebraic structure for symmetry-resolved noise analysis, but no QEC observables |

## Decisive verbatim quotes [paper]

- **Symmetry-preserving noise maintains the SPS:** "`U_E(T)[ρ_0(T)] = e^{C(T)}[ρ_0(T)] ∈ h(vec{q}) ⊕ g(vec{q})`" (Eq. 8).
- **Symmetry-breaking noise is block diagonal:** "`U_E(T)[ρ_0(T)] ∈ \bigoplus_{vec{q}'∈λ({Q_i})} [h(vec{q}') ⊕ g(vec{q}')]`"
  (Eq. 10) — "the noise perturbation and noise-averaged density operator are block diagonal in the symmetry
  representation" (p3).
- **FF count reduction:** "Normally, one needs `O(N^4)` FFs, but with this construction, one only needs
  `O(N^4_q)` elements to characterize classical non-Markovian noise, where `N_q = dim Z(q)` and usually
  `N_q << N`." (p3)
- **Control matrix block diagonalization:** "A key result of our study is that `R^i_μ(t)` is block diagonal
  if and only if calculated in the eigenspace decomposition with respect to `q`." (p3, Eq. 7)
- **Classical-noise-only scope:** "While we focus exclusively on classical stochastic processes in this
  study, the algebraic structure and framework should generalize to stochastic quantum baths. We leave that
  for a future study." (Conclusions)
- **Weak-noise assumption:** "We enforce a weak noise assumption, `||H_E(t)|| T << 1`, and truncate the
  expansion to second order." (p2)

## How to use / trust + open questions [twin]
- **Trust:** High for the algebraic core (Eqs. 1–11). The root space decomposition, Cartan subalgebra
  construction, and block diagonalization argument (Eq. 7) are standard Lie theory; the cumulant expansion
  and FFF are standard quantum control. The structural claims are theorem-grade (epistemic class (a)) given
  the stated assumptions (classical, stationary, weak noise). The numerics (Figs. 1–2) are illustrative
  (n=4, ensemble of 20k trajectories) but consistent with the algebra.
- **Open for us:** (i) Extend the block diagonalization to **quantum** noise (non-commuting, asymmetry
  spectrum) — the paper flags this but does not attempt it. (ii) Translate the `O(N^4) → O(N_q^4)` FF
  savings into a practical estimator for syndrome records — the paper stops at the structural result.
  (iii) Connect the `Aij`/`Bij` (dissipative/coherent) split in the cumulant expansion to our Girsanov
  split (coherent↔incoherent decomposition of the channel) — the paper notes the split but does not develop
  it. (iv) Evaluate the spectral overlaps `χ^{(1)}, χ^{(2)}` in closed form for the 1/f noise and
  low-frequency (`S(ω) ~ 1/ω`) PSD that drives dephasing-limited qubit noise, producing explicit
  decoherence rates per symmetry sector.
