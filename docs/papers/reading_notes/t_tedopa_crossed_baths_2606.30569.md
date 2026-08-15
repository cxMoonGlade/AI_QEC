# Full-text review — Le Dé, Mangaud, Chin & Desouter-Lecomte, "Revisiting crossed-correlated baths in open quantum systems simulated by HEOM or T-TEDOPA" (arXiv:2606.30569)

> **Provenance (2026-06-30): FULL-TEXT read (精读), incl. Supplementary Material.** PDF
> `outputs/papers/2606.30569.txt` (source `arxiv.org/pdf/2606.30569`, 30 pp, 80650 chars, pdftotext-layout
> via `fetch_and_extract.py`). All §/Eq/Fig/Table refs from that text. Figures not pixel-extracted —
> figure facts = captions + numbers stated in text. Two equation numbering streams: **main text** Eqs.(1)–(41)
> and **SI** Eqs.(1)–(18); SI eqs flagged "[SI Eq]" below.

## Metadata [paper]
- **Authors / affiliation:** Brieuc Le Dé (Sorbonne / UC Merced), Etienne Mangaud (Univ. Gustave Eiffel),
  Alex W. Chin (Sorbonne — the Chin TEDOPA group), Michèle Desouter-Lecomte (Univ. Paris-Saclay, corresponding).
- **Venue / status:** arXiv:2606.30569v1 [quant-ph], 29 Jun 2026. Manuscript styled for J. Chem. Phys.
- **Type:** Theory + simulation (methodology comparison, one molecular illustration). NOT experiment.
- **Code:** all T-TEDOPA runs done with the **MPSDynamics.jl** package (github.com/shareloqs/MPSDynamics, ref 83/61).

## Executive summary [paper]
The paper tackles ONE problem: two (or more) system operators coupled to a **shared vibrational environment**
produce **cross-correlated baths** — the bath collective modes `B_l`, `B_m` have a nonzero cross two-time
correlation `C_lm(t-τ) = <B_l(t) B_m(τ)>` even though each `B_n` is built from independent normal modes. This
is encoded in an **off-diagonal spectral-density matrix** `J_lm(ω)`. The question is how to simulate it, and
whether the correlated baths can be **de-correlated** by a transformation that diagonalizes `J(ω)`. Key result:
the diagonalizing transform `U(ω)` is in general **frequency-dependent**, and **HEOM cannot use a
frequency-dependent transform** (its bath operators would become ω-dependent mixtures, incompatible with the
exponential-mode ADO machinery) — so HEOM must either (a) simulate the full correlated hierarchy (N²_bath
correlation functions → ADO count explodes) or (b) approximate with an *optimal frequency-INdependent* `U_opt`.
**T-TEDOPA CAN use the exact frequency-dependent transform**, at the price of **long-range couplings in the
tensor chain**. When the spectral-density matrix is (nearly) **rank-1 / dyadic** at each frequency (dominant
eigenvalue `Λ_1(ω) ≫ Λ_2(ω)`), the correlated pair compresses to a **single shared bath** — a chain whose
coupling to each system operator `S_n` is `c_n(ω)=√(Λ_1(ω)) U_{n1}(ω)`. Illustrated on a conical-intersection
LVC model of the m22 PPE dimer at 298 K; correlated-HEOM and AD-factorized T-TEDOPA agree; **neglecting the
correlation badly overpredicts decoherence** (Fig.10).

## Method (deep) [paper]

### System–bath model (star model / LVC)
Generic partition `H = H_S + H_B + H_SB` (Eq.1). Bath = harmonic oscillators (Caldeira–Leggett star model).
Cross-correlation enters through the **collective bath modes**, each a linear combination of the SAME
underlying normal modes `q_j`:
- `B_n = Σ_j κ^(n)_j q_j` (Eq.3), coupled to the system by projector `S_n = |n><n|`, `H_SB = Σ_n S_n B_n` (Eq.2).
- Even with independent `q_j`, `B_l` and `B_m` are correlated **whenever they share common modes** (Eq.4 text,
  p.3): "not distinct physical environments, but different projections of the same vibrational environment onto
  different electronic states." **This is exactly the shared-bath mechanism.** [paper → ours: this IS our
  shared-1/f/TLS bath imprinting correlated dephasing across qubits.]

### The cross-correlation object (EXACT, verbatim)
Two-time correlation **matrix** (Eq.4):
```
C_lm(t-τ) = <B_l(t) B_m(τ)>,   l,m ∈ [1,2]  (avg over equilibrated baths at T, Eq.5 ρ^eq_B)
```
Linked to the **temperature-dependent spectral-density matrix** by Fourier transform (Eq.6):
```
C_lm(t-τ) = (ℏ/π) ∫_{-∞}^{∞} dω J^β_lm(ω) e^{-iω(t-τ)}       (Eq.6)
J^β_lm(ω)  = J_lm(ω) n_β(ω)                                   (Eq.7)   n_β = Bose function
J_lm(ω)    = (π/2) Σ_j g^(l)_j g^(m)_j δ(ω-ω_j)               (Eq.8)   g^(l)_j = κ^(l)_j ω_j^{-1/2}
```
The **off-diagonal `J_12(ω)` is nonzero because the two states couple to overlapping subsets of modes** (p.4).
KMS / statistical relation (Eq.20): `C_ml(τ,t) = C_lm(t - iℏβ, τ) = C*_lm(t,τ)` (derived in full in SI Eqs.5–6).

### The frequency-dependent diagonalization (the crux)
At each frequency, `J^β(ω)` is a symmetric matrix diagonalizable by an **orthogonal `U(ω)`** (Eq.9 / Eq.37):
```
J^β(ω) = U(ω) Λ(ω) U^T(ω)                                     (Eq.37)
```
- **Discrete LVC:** `J(ω_j) = g_j ⊗ g_j` is a **rank-1 dyadic** (Eq.25) → exactly ONE nonzero eigenvalue
  `Λ_1(ω_j)`, all others zero (Eq.26). A rank-1 matrix at every frequency ⇒ a **single shared bath** carries
  everything, the orthogonal complement decouples.
- **Continuous (after Lorentzian broadening, Eq.41 / SI Eq.2, Γ=80 cm⁻¹):** positive/negative mode
  contributions can cancel → `J_12(ω)` shrinks; dyadic structure can be broken → possibly `Λ_2(ω) ≠ 0`.
- **Fully (anti)correlated special case (Sec.II):** `g^(1)_j = ± g^(2)_j ∀j` ⇒ `U` is frequency-INDEPENDENT,
  shared bath `B_± = (B_1 ± B_2)/√2` (Eq.10), transformed operator `S_± = (S_1 ± S_2)/√2` (Eq.11). The standard
  **spin-boson σ_z model = fully anti-correlated case** (p.5, key remark).

### HEOM formulation & why it fails for frequency-dependent U
- Second-order cumulant is EXACT for Gaussian (harmonic) baths (Wick, Eq.14). Master equation (Eq.19) rigorously
  carries the **full correlation matrix `C_lm`**, including off-diagonal, even though `H_SB` looks like a sum of
  independent terms.
- HEOM expands each `C_lm(t)` in decaying exponentials (Eqs.21–22): `C_lm(t,τ)=Σ_k α^(lm)_k e^{iγ^(lm)_k(t-τ)}`.
  Auxiliary density operators (ADOs) indexed by occupation vector `m` over ALL modes of ALL diagonal AND
  cross correlation functions (Eq.23). Coupled EOM Eq.24.
- **Cost:** cross-correlation adds the `J_lm`, `J_ml` baths ⇒ scales as **N²_bath** correlation functions.
  ADO count `N_ADO = (L+K)!/(L!K!)` (p.13). Concrete blow-up in the m22 example (below).
- **Why frequency-dependent `U(ω)` is incompatible with HEOM (Sec.V, p.7):** if `U` varies with ω, "the bath
  operators become frequency-dependent mixtures of the original operators … the transformed baths cannot
  generally be represented by a simple set of independent harmonic environments compatible with the standard
  HEOM formulation." HEOM needs each bath to have a single fixed system operator + a fixed exponential-mode
  correlation function; an ω-dependent mixing destroys that. **Hence HEOM's only decorrelation route is a
  frequency-INdependent `U_opt`.** Four `U_opt` recipes (p.8): (a) `U_η` at a representative (dominant-peak)
  frequency assuming constant coupling ratio `g^(2)=±√η g^(1)`; (b) `U_aver` = average of eigenvectors of
  `J^β(ω)`; (c) `U_C(0)` = eigenvectors of the initial correlation matrix `C(t=0)` (= integral of `J^β`); (d)
  `U_PCA` = principal SVD vector of the `N_bath×N_bath×N_ω` tensor. Quality metric = integrated off-diagonal
  Frobenius residual `ε(U_opt)=∫dω Σ_{i≠j}([U^T J^β U]_{ij})²` (Eq.28).

### T-TEDOPA formulation & how it KEEPS cross-correlation (Sec.VI — the core for us)
T-TEDOPA (Tamascelli et al., ref 59) replaces the thermal mixed state by a **pure 0 K state on an
extended (positive+negative) frequency axis**; initial state `ρ(0)=ρ_S(0)⊗|0…0><0…0|` (Eq.29). Each bath is
**chain-mapped**: sample `J^β(ω)dω` → build orthogonal polynomials → the system couples ONLY to the first chain
mode; nearest-neighbour chain hoppings from the 3-term recurrence (refs 60,72,73). Fock dimension `d` per mode,
bond dimension `r` — an MPS of `d`-dimensional cores.

**Cross-correlation is kept via a factorization `J^β(ω)=A(ω)A^T(ω)` (Eq.31)**, `A` transforms operators
`s̄_A(ω)=A(ω)s` and modes. Two factorization families:

1. **`A(ω)` factorization (Dunnett/Zuehlsdorff, refs 28,29,64)** — Eq.32, explicit 2×2 with entries `√G_1`,
   `√C G_2`, `√C G_1`, `√G_2`, `G_1=(J^β_12)²/[2J^β_22(1-R)]`, `G_2=(J^β_12)²/[2J^β_11(1-R)]`,
   `C=(2J^β_11 J^β_22/(J^β_12)²)(1-R)-1`, `R=[1-(J^β_12)²/(J^β_11 J^β_22)]^{1/2}` (Eqs.33–35). Gives **two
   independent chains, EACH coupled to BOTH states** (Eq.36): `H_SB = ∫dω (A_11 S_1 + A_12 S_2)√B_{A1} +
   ∫dω (A_21 S_1 + A_22 S_2)√B_{A2}`. The "other-state" coupling to a chain built for one state ⇒
   **interactions become long-ranged** in the chain (p.10). Some *dynamical* correlation remains but chains
   can be cheaper.

2. **`A_D(ω) = U(ω)√Λ(ω)` — the EXACT spectral factorization (Eq.38, the paper's recommended route).**
   `s̄_{A_D}(ω)=A_D(ω)s`. In the **dyadic/rank-1 favorable case** `Λ_1(ω)≫Λ_2(ω)` this collapses to a
   **SINGLE shared chain** (Eq.39):
   ```
   H_SB = ∫dω ( c_1(ω) S_1 + c_2(ω) S_2 ) √B_{A_D1}(ω) ,   c_n(ω) = √(Λ_1(ω)) U_{n1}(ω),  n=1,2   (Eq.39)
   ```
   **This is the operative equation for us.** One physical shared bath (chain), coupled to the two system
   operators with frequency-dependent weights `c_n(ω)` — the eigenvalue sits IN the system operator (contrast:
   in HEOM it sits in the correlation function). If `Λ_2` is non-negligible, add a second term/chain.

**Why long-range couplings, not factored away (p.10, p.15–16):** the ω-dependent `U(ω)`/`c_n(ω)` means the
weight of `S_2` relative to `S_1` on the shared chain varies along the chain; the transform is NOT a single
static rotation, so the second-state coupling reaches multiple chain sites → **explicit long-range hoppings in
the MPS**, which TEDOPA's long-range-interaction machinery (Lacroix/Chin, refs 53,54) handles. "T-TEDOPA
procedure allows to account for the FULL frequency dependence of the transformation `U(ω)` at the cost of the
long-range interactions." (p.10) The cross-correlation is **preserved as chain topology**, not diagonalized
into independent factorized baths. **Slowly-varying `c_n(ω)` ⇒ shorter chains** (p.10, practical lever).

## The MECHANISM (for implementation) [paper → ours]
**Shared-bath → cross-correlated dephasing on multiple system operators**, exactly represented (given a
harmonic/Gaussian bath) by:
1. a **spectral-density MATRIX `J^β_lm(ω)`** with nonzero **off-diagonal cross term `J_12(ω)`** (Eqs.6–8);
2. mapped to dynamics either by **correlated HEOM** (Eq.24, exact, `N²_bath` cost) or by
   **T-TEDOPA with `A_D(ω)=U(ω)√Λ(ω)`** (Eq.38) → single shared chain Eq.39 when rank-1.

For OUR twin the system operators are `S_n = |1><1|_n` (dephasing projector on qubit n, i.e. the `σ_z`-type
coupling — the paper explicitly notes σ_z spin-boson = fully anti-correlated shared bath, p.5). A shared 1/f
or TLS bath seen by qubits n and m gives a **cross spectral density `J_nm(ω)`** = the spatial correlation of
their dephasing. Chain-map `J^β(ω)` (extended frequency axis, 0 K pure state) → MPS with per-qubit coupling
weights `c_n(ω)=√Λ_1 U_{n1}`. Grounded knobs the paper hands us: Lorentzian broadening `Γ=80 cm⁻¹`;
Tannor–Meier fit form (SI Eq.3) `J_TM(ω)=Σ_l p_l ω /{ℏ³[(ω+Ω_l)²+Γ_l²][(ω-Ω_l)²+Γ_l²]}`; analytic bath-correlation
expansion with `α_1, α_2` from Lorentzian poles ±Ω±iΓ (SI Eqs.11–12) + Matsubara poles `γ_m=i2πm/ℏβ`,
`α_m=2iJ(γ_m)/β` (SI Eqs.13–14). **Repo:** we have NO chain-mapping / TEDOPA carrier — this is external
(MPSDynamics.jl). Our MPS carrier (`src/qec_twin/simulator/axis1_*_mps_execution.py`, `forward/scalable/`) is a
qutrit-MCWF-on-system-MPS, a *different* tensor object (system chain, not bath chain).

## The OBSERVABLE / metric [paper]
- **Populations** `P_2(t)` (Fig.9) and **modulus of electronic coherence** `|ρ_12(t)|` (Fig.10) — the
  discriminating observable. **Coherence decay is the sensitive probe of bath correlation**: correlated baths
  give MUCH SLOWER decoherence; the uncorrelated approximation "predicts a too fast decay" (p.16). Populations
  are comparatively INSENSITIVE to the correlation ("little impact on the population but … decay of the
  coherence is completely different", SI p.8). **[paper: correlation lives in the coherence, not the
  populations — mirrors our repo memory that coherence, not syndrome populations, is the correlation signature.]**
- **Approximation-quality metrics:** integrated off-diagonal Frobenius residual `ε(U_opt)` (Eq.28); and a
  suggested (not implemented) a-priori error bound generalizing Mascherpa et al. (ref 70) — error from the
  residual correlation matrix `J^β(ω) - J̄^β_{U_opt}(ω)`, expected to **grow exponentially in time**.

## Findings + numbers [paper]
- **HEOM cost blow-up (m22, correlated, L=7):** 5 correlation functions (4 for the two correlated tuning baths
  `K^(11),K^(22),K^(12),K^(21)` + 1 coupling bath `K^(33)`), 6 decay modes each ⇒ K=30 total modes ⇒
  **N_ADO = 10,295,472**. Approximate single shared bath (2 correlation functions): **N_ADO = 50,388**
  (×~200 reduction); +Matsubara (8 modes/bath): N_ADO = 116,280.
- **T-TEDOPA storage (m22):** `r=8`, `d=10`, 100 modes coupling bath + 90 modes tuning bath. AD (single shared
  tuning bath): `N = (100+90)×10×8² = 121,600` complex elements. A-factorization (two tuning baths):
  `(100+180)×10×8² = 179,200`. T-TEDOPA "always more efficient in computational time" than HEOM here.
- **`U_opt` accuracy (Eq.28 residual):** 5.07×10⁻⁵ (`U_aver`), 3.28×10⁻⁵ (`U_C(0)`), 4.51×10⁻⁵ (`U_PCA`) —
  all tiny; the example is nearly perfectly rank-1 (`Λ_2` negligible). `U_{η=1}` coeffs 0.707106 vs `U_C(0)`
  0.70707/0.70714 — essentially the symmetric/antisymmetric effective-mode transform (κ_± = (κ^(1)±κ^(2))/2).
- **Physics result:** for this *sloped* conical intersection (gradients same sign → positive correlation),
  correlation **slows decoherence** (long-term nuclear-wavepacket overlap). Correlated-HEOM ≈ AD-T-TEDOPA;
  `U_{η=1}` acceptable for first ~50 fs; **uncorrelated = qualitatively wrong** (Fig.10).

## Limitations [paper]
- **Gaussian/harmonic bath ONLY.** The whole exactness (2nd-order cumulant truncation, Wick, Eq.14) rests on
  linear coupling to harmonic oscillators. Non-Gaussian baths are out of scope.
- **Two-level / few-level, few-bath demonstration.** Illustration is a 3-electronic-state (1 ground + 2 excited)
  LVC with 3 baths. **No scaling study in N_sites**; N²_bath is called out only as the reason HEOM becomes
  "prohibitive." No lattice / many-qubit demonstration.
- **A_D single-shared-bath collapse requires a (near-)rank-1 `J(ω)`** ("favorable case", "dyadic structure
  preserved"). General multi-site cross-correlation ⇒ multiple non-zero eigenvalues ⇒ multiple chains + more
  long-range couplings; no bound given on how bad that gets.
- **Error control is convergence-only, not a-priori.** `ε(U_opt)` (Eq.28) measures only the residual of the
  *frequency-independent approximation*; the exact `A_D` T-TEDOPA has NO stated a-priori accuracy bound — only
  agreement-with-HEOM. The rigorous bound (ref 70 generalization) is proposed as *future* work; error "expected
  to grow exponentially with time." Convergence in `r,d`, chain length also only checked empirically.
- **HEOM run here dropped Matsubara terms in the correlated case** (only the approximate/shared runs kept them),
  so even the "exact" HEOM baseline carries a stated approximation.

## Relevance to qec_twin [ours]
**Verdict: ORACLE (small-scale, per-mechanism), NOT a carrier for the full 2D surface code. Faithfulness
trade-off: gains the EXACT shared-bath cross-correlation + non-Markovianity we currently cannot represent;
loses at surface-code scale (N² baths, growing bond, no a-priori error bound).**

- **What it gives us that we lack:** an INDEPENDENT, method-distinct **exact oracle for correlated dephasing
  from a shared 1/f/TLS bath**. Our carrier is qutrit-MCWF-on-a-system-MPS; T-TEDOPA/HEOM is a
  *bath-side, memory-kernel-exact* method. Cross-checking our teacher's correlated-dephasing channel against a
  T-TEDOPA (or correlated-HEOM) run on the SAME `J^β_lm(ω)` = a genuinely independent ground truth (satisfies
  Faithfulness Protocol rule I — the check is against a method that does NOT share our carrier's blind spots),
  provided we restrict to a small qubit patch (2–4 qubits, few rounds) where TEDOPA/HEOM is tractable.
- **The one equation to reuse:** Eq.39 — shared bath, per-qubit coupling `c_n(ω)=√(Λ_1(ω)) U_{n1}(ω)`. Our
  "shared bath imprints correlated dephasing" is EXACTLY the σ_z-projector shared-bath case the paper flags
  (p.5). The spatial cross-correlation of qubit n,m dephasing = `J_nm(ω)`; positive `J_nm` = correlated
  (in-phase) dephasing.
- **CORRECTION this forces on us:** the naive "diagonalize the correlation matrix and simulate independent
  baths" shortcut is **frequency-dependent in general and cannot be factored away without either (i) accepting
  long-range chain couplings (T-TEDOPA) or (ii) a controlled frequency-independent approximation whose error
  grows exponentially in time (HEOM `U_opt`).** If our teacher ever "de-correlates for tractability," that is a
  **declared, error-bounded simplification** (Faithfulness rule III), not a free move — and the paper shows the
  discriminating observable (coherence, Fig.10) is precisely where the error shows up. Also: **the σ_z
  spin-boson standard already IS a fully-anti-correlated shared bath** — a caution that "independent per-qubit
  dephasing baths" is itself a modeling choice, not the neutral default.
- **What it CANNOT do for us:** it is NOT a full-2D-surface-code multi-round carrier. N²_bath correlation
  functions (HEOM) and growing bond + long-range chains (T-TEDOPA) at d5/d7 × many rounds are unaddressed;
  Gaussian-bath-only excludes leakage / non-Pauli. So: **oracle for the correlated-dephasing sub-mechanism at
  small patch, feeding/validating our carrier — not a replacement carrier.**

## How to use / trust + open questions [ours]
- **Trust:** FULL text + SI read; equations transcribed verbatim (main Eqs.6–8, 24, 37–39; SI Eqs.3, 11–14).
  Figures not pixel-extracted — all figure *facts* used here (N_ADO counts, storage counts, ε residuals,
  coherence-vs-population sensitivity) are stated numerically in the text, so figure non-extraction is not
  load-bearing.
- **GT-feasibility (the actionable path):** to certify our correlated-dephasing teacher, (1) build `J^β_nm(ω)`
  for a small qubit patch from our shared-bath spectral model (Tannor–Meier fit form SI Eq.3 available), (2) run
  **correlated-HEOM (QuTiP HEOMSolver supports cross-bath) OR T-TEDOPA (MPSDynamics.jl, Eq.38/39)** on 2–4
  qubits, few rounds, (3) compare **`|ρ_nm(t)|` coherence decay** (the sensitive observable) against our
  carrier. Two independent methods (HEOM and T-TEDOPA) that already cross-validate here (Fig.9/10) → a strong
  external oracle.
- **Open questions:** (a) at what patch size does HEOM's N²_bath / T-TEDOPA's chain length become infeasible for
  our qubit counts and round depth? (b) is our shared bath actually (near-)rank-1 in `J_nm(ω)` (⇒ single shared
  chain, Eq.39) or multi-eigenvalue (⇒ multiple chains)? (c) can we obtain the a-priori time-dependent error
  bound (ref 70 generalization) the paper leaves open, so a declared de-correlation simplification is *bounded*
  per Faithfulness rule III, not just convergence-checked? (d) MPSDynamics.jl is Julia — integration cost vs
  QuTiP-HEOM (Python, already in our stack) for the oracle role.
