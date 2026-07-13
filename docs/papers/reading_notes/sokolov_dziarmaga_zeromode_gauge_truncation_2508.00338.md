# Full-text review — I. Sokolov, Y. Zhang, J. Dziarmaga, "Truncating loopy tensor networks by zero-mode gauge fixing" (arXiv:2508.00338; PRE 2025)

> **Provenance (2026-07-12): FULL-TEXT read (精读).** PDF (arXiv:2508.00338**v2**, dated
> "4 Nov 2025" on the arXiv line / front matter "Dated: July 28, 2025") downloaded via curl →
> `outputs/papers/peps_foundation/2508.00338.pdf` → PyMuPDF text
> `outputs/papers/peps_foundation/2508.00338.txt` (**13 pages / 1567 lines**). Every §/Eq/Fig/Ref
> below transcribed from that text (not from any summary). Read the ORIGINAL end-to-end; the
> project has been burned by inheriting a note's blind spot, so all load-bearing equations
> (Eq. 1–5, 11–24, App. A/B/C) were transcribed verbatim from the extracted text and cross-checked.
>
> **Verbatim-passage confirmations (front matter + load-bearing claims):**
> - Title line 1: *"Truncating loopy tensor networks by zero-mode gauge fixing"*.
> - Authors (lines 2–6): *"Ihor Sokolov, Yintai Zhang, and Jacek Dziarmaga"* — all Jagiellonian
>   University, Kraków (Institute of Theoretical Physics / Mark Kac Center / Doctoral School).
> - Abstract (lines 8–15): *"By cutting the bond, we define a set of states whose linear dependence
>   can be used to truncate the bond dimension. The linear dependence is eliminated with zero modes
>   of the states' metric tensor."*
> - Eq. (1) `gij ≡ ⟨ψi|ψj⟩ = Σk Uik Nk U*jk`; Eq. (5) `f = ND/|ZD|²`; Eq. (11) general metric
>   `gij,i'j' = ⟨ψij|ψi'j'⟩`; Eq. (19) `f = N/|ED|²`; Eq. (20)–(21) EAT product + loopiness `l=λ2/λ1`.
>
> **ID/title verified.** arXiv:2508.00338 IS this paper. Companion Z2-gauge id 2605.09385 was NOT
> downloaded — the Z2 lattice-gauge / stabilizer-flavored behavior we care about is developed
> IN THIS paper (Sec. VIII, Figs. 7–10), so the core question is answered here; the companion is
> flagged as unread in "Open questions."

## Metadata [paper]
- **Authors / affiliation:** Ihor Sokolov, Yintai Zhang, Jacek Dziarmaga — Jagiellonian University,
  Kraków, Poland. (Dziarmaga is the NTU author of arXiv:2107.06635, our companion note.)
- **Venue / status:** arXiv:2508.00338v2 [quant-ph], 4 Nov 2025. **Physical Review E 112,
  055307 (2025), DOI `10.1103/4lgp-ld2s`.** The arXiv record now carries the journal reference and
  related DOI; the v2 PDF predates that metadata. Data openly available on RODBUK (Ref. 59).
- **Type:** Method paper (a tensor-network bond-truncation *initialization* scheme) + a series of six
  numerical illustrations (iPEPS real-/imaginary-time evolution: quantum Ising, Heisenberg thermal,
  **Z2 gauge field**, t-J; plus TRG for the classical Ising model).

## Executive summary [paper]
The paper introduces **zero-mode truncation (ZMT)**, a deterministic *initialization* for compressing
a bond in a **loopy** tensor network (PEPS/pMPS), where virtual loop entanglement parasitically
inflates bond dimension (the cartoon of Fig. 1: a plaquette loop index `j` decoupled from all
physical indices yet consuming bond dimension). The core idea (Sec. II): **cut the bond**, obtaining
a set of "cut states" `|ψj⟩` whose sum is the TN state, `|ψ⟩ = Σj |ψj⟩`. Their **metric (Gram)
matrix** `gij = ⟨ψi|ψj⟩` (Eq. 1) is diagonalized; a **zero eigenvalue** `N_D = 0` signals **linear
dependence** of the cut states (Eq. 2), i.e. redundant bond directions. The associated **zero mode**
`Z_j = U_{jD}` generates a **gauge freedom** `Σj|ψj⟩ = Σj(1 + zZ_j)|ψj⟩` (Eq. 3); fixing `z = −1/Z_D`
**exactly eliminates** one cut state and truncates the bond `D → D−1` *without changing the physical
state* (Eq. 4). For a small-but-nonzero eigenvalue the incurred error is the closed form
`f = N_D/|Z_D|²` (Eq. 5), and one greedily eliminates the mode of **lowest f** (not lowest `N`).
Section IV generalizes this to the full `D²×D²` metric `g_{ij,i'j'} = ⟨ψij|ψi'j'⟩` (Eq. 11) by
retaining the two virtual endpoint labels `i,j` of the cut bond (the primed labels belong to
the bra in the Gram), giving the more powerful
loop-cutting truncation (Eq. 12–17), with error `f = N/|E_D|²` (Eq. 19). Section V places ZMT against
**environment-assisted truncation (EAT)** [Ref. 31]: EAT approximates the metric by its **leading**
left–right product `g ≈ g_L λ1 g_R` (Eq. 20), which is exact only for a **non-loopy** bond; the
**loopiness** `l = λ2/λ1` (Eq. 21) measures the failure. **In the non-loopy case ZMT reduces exactly
to EAT / canonical-spectrum truncation; in the loopy case ZMT can cut a loop that EAT/SVD/Vidal-gauge
cannot** (Sec. V, last paragraph). The headline empirical claim: across all six examples ZMT gives
**better *initial* truncation errors** than EAT/SVD/TEBD, and in the hard **Z2 gauge** case the
initialization quality determines the *final* error after variational optimization (EAT "obliterates"
the plaquette gate; SVD is unconverged at D=10 while ZMT3 converges — Figs. 8–10).

**One-line relevance to us:** this is a candidate FORK-A initializer, not a closed fix. ZMT is a **deterministic,
pseudoinverse-free, loop-aware** replacement for the *initialization* step our FET-ALS gets wrong
(Sec. III is a two-line proof that the `pinv` solution keeps the redundant bond while the zero-mode
gauge choice cuts it). It confirms the bond-side statement **`ker(g)=ker(Ψ)` for
`g=Ψ†Ψ`**, where the columns of `Ψ` are cut states. It does not identify this with the generally
different environment-side kernel of `ΨΨ†`. **ZMT is an initializer, not a full variational solver,
and it is physically blind — it cannot by itself distinguish a gauge loop from weak leakage magic.
The threshold `δ` (Sec. X) selects the ZMT1-to-ZMT2/3 construction while compression continues to
the same target rank; it is not an acceptance, physical-content, or record-faithfulness threshold.**

## Method (deep) [paper]

### II. Elimination of linear dependence — the compact `D×D` scheme (this becomes "ZMT1")
- Black-box TN state (Fig. 2a): expose one bond index `j=1..D`; each value defines a cut state
  `|ψj⟩`; the TN state is `|ψ⟩ = Σ_{j=1}^D |ψj⟩` (line 136).
- **Metric = Gram of the cut states:** `gij ≡ ⟨ψi|ψj⟩ = Σ_k U_ik N_k U*_jk` (Eq. 1), with
  `N_1 ≥ … ≥ N_D ≥ 0`.
- **Zero mode = null vector of the Gram:** if `N_D = 0`, the eigenvector `Z_j ≡ U_{jD}` satisfies
  `Σ_j Z_j |ψj⟩ = 0` (Eq. 2) — an exact **linear dependence**.
- **Zero-mode gauge freedom:** because `Σ_j Z_j|ψj⟩ = 0`, `Σj|ψj⟩ = Σj (1 + zZ_j)|ψj⟩` for any `z`
  (Eq. 3). Choosing `z = −1/Z_D` gives `Σj|ψj⟩ = Σ_{j=1}^{D−1}(1 − Z_j/Z_D)|ψj⟩` (Eq. 4): the
  factor `1 − Z_j/Z_D` is **absorbed into the adjacent tensors**, and `|ψD⟩` is gone — bond `D→D−1`,
  **state unchanged**. Permute indices so `|Z_D|` is maximal (numerical stability, line 169).
- **Imperfect zero mode:** if `N_D > 0` small, truncating anyway changes the state by
  `−Σ_j (Z_j/Z_D)|ψj⟩` whose norm² is `f = (Σ Z*_i g_ij Z_j)/|Z_D|² = N_D/|Z_D|²` (Eq. 5).
  **Greedy rule: eliminate the mode with the lowest `f`, not the lowest eigenvalue `N_D`** — both the
  eigenvalue and the gauge weight `|Z_D|` matter (lines 218–222). Degeneracies/multiplets of the
  lowest `N_k` may matter (a known SVD-truncation subtlety, Ref. 29, lines 223–227).

### III. Zero-mode gauge fixing **versus** the pseudoinverse (the money section for us)
A minimal toy (lines 231–267): target `½ Σ_{j=1}^2 |ψj⟩` with `|ψ1⟩ = |ψ2⟩`. The Gram is
`g = 1 + σ_x`, **singular**, with zero mode `(1,−1)^T`. Minimizing `f = c†gc − (1,1)c − c†(1,1)^T + 1`
(Eq. 6) requires `g c = (1,1)^T` (Eq. 7).
- **Pseudoinverse (the standard/ALS move):** `c = pinv(g)(1,1)^T = ½(1,1)^T` (Eq. 8) → a valid
  minimizer but it **keeps bond dimension 2** (`|ψ⟩ = ½Σ|ψj⟩`). *The pinv does not truncate.*
- **Zero-mode gauge:** the general `f=0` solution is `c = ½(1,1)^T + z(1,−1)^T` (Eq. 9); set `z=½`
  → `|ψ⟩ = |ψ1⟩`, **bond dimension 1**. *The gauge freedom truncates.*

This is exactly our FET-ALS pathology: an unregularized/pinv least-squares solve lands on the
non-truncating minimizer of a singular metric (and, with our non-Hermitian metric, diverges), instead
of exploiting the null-space gauge freedom to actually cut the bond.

### IV. General bond zero modes — the `D²×D²` scheme (this becomes "ZMT3")
- Cut **both** bond legs (Fig. 2b): states `|ψij⟩`, with `|ψ⟩ = Σ_{ij} δij |ψij⟩` (Eq. 10).
- **General metric** `g_{ij,i'j'} = ⟨ψij|ψi'j'⟩` (Eq. 11) — the `D²×D²` Gram.
- Zero mode `Z` with `g_{ij,i'j'} Z_{i'j'} = 0`, normalized `Tr Z†Z = 1`. Gauge freedom
  `|ψ⟩ = Σ_{ij}(δij + z Z_ij)|ψij⟩` (Eq. 12).
- Diagonalize the **matrix** `Z_ij = Σ_k S⁻¹_{ik} E_k S_{kj}` (Eq. 13), eigenvalues
  `|E_1| ≤ … ≤ |E_D|`. Choosing `z = −1/E_D` makes `δij + z Z_ij` singular; its SVD
  `δij − Z_ij/E_D = Σ_k U_ik λ_k V*_jk` (Eq. 14) has `λ_D = 0`. Truncating `λ_D` and absorbing `U,V`
  into the two local tensors (Fig. 2d, Eq. 16–17) compresses `D → D−1`.
- **Sec. II is the special case** of restricting the metric to the diagonal subspace `i=j, i'=j'`
  with `Z_ij = δij Z_j` (lines 354–360). When `Z` is diagonalizable, a **conventional gauge**
  `1 = S⁻¹S` inserted in the bond (Eq. 18, Fig. 2e) rotates the general zero mode to a diagonal one
  `Z^S_ij = δij E_j`. The paper also uses **restricted subspaces**: Hermitian `Z_ij = Z*_ji` (complex
  TN) or real-symmetric `Z_ij = Z_ji` (real TN) — these are the ZMT2 variants.
- **Imperfect general zero mode:** error `f = N/|E_D|²` (Eq. 19; App. B gives the exact
  `f_min` beyond leading order). Again pick the lowest-`f` eigenmode. Switching from the cheap
  `D×D` (Sec. II) to the big `D²×D²` (Sec. IV) is decided by comparing Eq. 5 vs Eq. 19 (lines 396–400).

### V. Loopy vs non-loopy metric — the EAT / canonical-gauge positioning
- **EAT [Ref. 31]** approximates the metric by its leading left–right SVD product
  `g_{ij,i'j'} ≈ g^{ii'}_L λ1 g^{jj'}_R` (Eq. 20), `g_{L,R}` made Hermitian & non-negative (Fig. 3).
  **Exact iff the bond is the only connection between the left and right halves** — i.e. non-loopy.
- **Loopiness** `l = λ2/λ1` (Eq. 21): the relative weight of the second SVD value. `l=0` ⇒ non-loopy.
- **EAT gauge** (Eq. 22–24): diagonalize `g_L, g_R`, SVD `N_L^{1/2} U_L^T U_R N_R^{1/2} = W_L Λ W_R`,
  insert the gauge (Eq. 24). When Eq. 20 is exact this is the **Schmidt decomposition** with
  entanglement spectrum `Λ`; EAT = truncating the smallest `Λ` = **canonical-spectrum truncation**.
- **The central theorem-in-words (lines 498–508):** in the non-loopy case `g̃ = Λ⊗Λ`, the lowest
  eigenmode of `g̃` is `|Z⟩ = |D⟩|D⟩` with `N = Λ_D`, so **ZMT ≡ EAT** (both truncate the smallest
  Schmidt value). *"However, for a general loopy bond metric tensor the zero-mode gauge fixing is
  capable of truncating a loop while EAT is not."* This is the precise statement of ZMT's advantage
  over canonical/Vidal-gauge/EAT truncation — and it is the "close the Evenbly-2018 gap" result
  (Ref. 32 = Evenbly PRB 98, 085155 (2018), the closed-loops gauge in our handoff): EAT's gauge is
  Evenbly-flavored; ZMT strictly extends it to loops.

### Variant naming used in the examples
- **ZMT1** = compact `D×D` scheme (Sec. II), `Z_ij = δij Z_j`, cut one-by-one, usually in the EAT gauge.
- **ZMT2** = general scheme with `Z` restricted to Hermitian/real-symmetric subspace (real `E_k`,
  orthonormal `S`); often the **best** (TRG Fig. 14; Heisenberg Fig. 6).
- **ZMT3** = fully general `Z` (Sec. IV), no restriction, `E_D` = largest-magnitude (or largest real)
  eigenvalue; best on the loopy Z2 gauge case (Fig. 8) but *worse* than symmetric ZMT2 in TRG.
- **ZMT4** (Z2 example only) = **product ansatz** `Z_ij = R_i L_j`, `R†R=L†L=1`, optimized iteratively
  `→L→R→` to converge Eq. 19 (`N = Z†gZ`, `E_D = Σ_j L_j R_j`) — the one iterative variant.

### Construction / role in the pipeline (load-bearing)
- **ZMT is an INITIALIZATION**, not a full solver: obtain the metric from a supplied environment →
  eigendecompose/SVD → gauge-fix `z=−1/E_D` → truncate the selected mode, optionally one-by-one down
  to target. **No alternating least-squares sweep appears in ZMT1–3 initialization.** ZMT4 optimizes
  a product ansatz iteratively. Environment approximation, degeneracies, and mode-selection choices
  are outside any determinism or convergence guarantee in the paper.
- **Every example follows ZMT init with the usual variational (ALS-like) optimization.** So ZMT does
  **not eliminate** the variational sweep — it de-risks it. In the easy models (Ising Fig. 5, t-J
  Fig. 11) the *final* error is init-independent (any init converges). In the **hard loopy Z2 case**
  the *final* error **depends on the init** — EAT/SVD give a bad basin the ALS cannot escape, ZMT3
  gives a good one (Figs. 8–10). Whether the project's measured bonds are in an analogous regime is
  an open transfer hypothesis.
- **No monotonicity/global-convergence theorem.** The construction avoids the particular pseudoinverse
  pathology illustrated in Sec. III, and Eqs. 5/19 quantify the paper's selected-mode objective at the
  stated order. They do not prove a monotone multi-cut descent, non-divergence under an approximate
  environment, or convergence to a global optimum.

## The MECHANISM (for implementation)
Per bond to truncate (finite d3/d5 patch, single-wire PEPS):
1. **Cut the bond.** Compact scheme: retain one bond label → cut states `|ψj⟩`, `j=1..D`.
   General scheme: expose the two endpoint bond labels → `|ψij⟩`, `i,j=1..D`. These are the
   two virtual indices at the cut, not independent ket/bra copies.
2. **Build the metric (Gram) from the relevant environment.** Compact: `g_ij = ⟨ψi|ψj⟩`
   (`D×D`, Eq. 1). General: `g_{ij,i'j'} = ⟨ψij|ψi'j'⟩` (`D²×D²`, Eq. 11). A finite project patch can
   be contracted exactly in principle, but the paper does not prove that route cheap or numerically
   benign; the actual contraction cost and approximation must be measured.
3. *(Recommended)* **Fix the EAT gauge** (Eq. 22–24) first: diagonalize `g_L,g_R`, SVD the overlap,
   insert Eq. 24. This makes `g_L,g_R` Hermitian/non-negative and puts you in the canonical (Schmidt)
   frame; the loopiness `l = λ2/λ1` (Eq. 21) is your **diagnostic** of how loopy the bond is.
4. **Eigendecompose the metric** (`U N U†`, compact) or **diagonalize the zero mode** `Z`
   (`Z_ij = S⁻¹ E_k S`, Eq. 13, general). Compute per-mode error `f = N/|Z_D|²` (Eq. 5) or
   `f = N/|E_D|²` (Eq. 19).
5. **Gauge-fix `z = −1/E_D` (largest-|E|) and truncate the resulting zero singular value** (Eq. 14–17).
   Eliminate the lowest-`f` mode; absorb the gauge factor into the two adjacent tensors.
6. **Target-rank variants:** ZMT1 applies the compact elimination one-by-one to the target `χ`.
   In the TRG ZMT2/3 variants, compact ZMT1 is used until Eq. 5 first exceeds `δ` at `χ' > χ`;
   the algorithm then **switches to the general Sec.-IV mode and continues to the same target `χ`**
   (paper lines 1150–1163). Thus `δ` selects the compact-to-general transition; it is not a stop/
   accept threshold and does not certify physical content.
7. **Follow with the ordinary variational optimization** (the ALS sweep) from this initialization.
8. *(Optional)* App. C: perturb the chosen eigenmode `Z → Z + fε` (Eq. C4–C7) to lower `f` further —
   but the gain is only `O(f²)` and "may not justify the numerical overhead."

**Key correspondence to our independent derivation (asked explicitly):**
Partly. The paper's cut-states metric `g_ij = ⟨ψi|ψj⟩` is the Gram of the columns of `Ψ` (each
column is one cut state), so `g = Ψ†Ψ` and **`ker(g)=ker(Ψ)`** is exactly the space of bond-label
linear-dependence relations. The environment-side operator `G=ΨΨ†` has the same nonzero spectrum
and rank, but it acts in a different space and generally has a different kernel dimension/support.
Therefore a null-space derivation written for `G` is not literally the paper's bond-space truncation;
it must be transported through the SVD/range maps before claiming equivalence. **Two precise caveats:**
- `G=ΨΨ†` lives on the environment/physical space; `g=Ψ†Ψ` lives on the bond-label space. Only
  nonzero spectra and rank agree automatically; the bond-space form `g` is the object ZMT truncates.
- Our `G` matches the paper's **compact Sec-II** metric when one bond label is retained; it matches the
  **general Sec-IV** `D²×D²` metric when both endpoint labels are retained. The paper
  proves Sec. II is the diagonal restriction of Sec. IV — so both are the same object at different
  resolution, and our derivation is the compact one.

## Relevance to qec_twin [ours]

### FORK A candidate — replacing only the FET-ALS initialization
Our failure (from the active line): single-edge FET-ALS on the d3/d5 single-wire PEPS grows the bond
(6→12→15…) with non-monotone fidelity and pinv divergence, while the measured bipartition entropy
`S_A` is bounded. This paper is structurally relevant, but the mapping is conditional:

- **Exact-zero implication.** If the project's cut-state Gram has an **exact** zero mode, ZMT's Eq. 4
  removes that linear dependence without changing the represented state. Bounded `S_A` alone does
  not prove that the excess virtual bond is exactly such a zero mode; that remains a project
  hypothesis.
- **Loopiness is not a physical classifier.** `l=λ2/λ1` (Eq. 21) measures the failure of EAT's
  rank-one environment factorization. `l≈0` recovers the non-loopy EAT/Schmidt limit; `l>0` says the
  bond is loopy, but does not distinguish removable virtual redundancy from genuine long-range
  physical correlation and does not prove that ALS must fail.
- **ZMT extends EAT as an initializer.** The paper shows that zero-mode gauge fixing can truncate a
  loopy metric where EAT cannot, but every numerical example still follows the initialization with
  variational optimization. It does not license replacing the full solver by a canonical spectrum.

### Reliability vs our ALS [ours]
ZMT can be safer as an initializer because it avoids using a pseudoinverse to choose one arbitrary
solution in a singular metric and explicitly exploits exact linear dependence. The cut-state Gram is
Hermitian PSD **by definition**; EAT gauge fixing does not excuse or automatically repair a
non-Hermitian implementation. ZMT is deterministic before the optional variational refinement, but
the paper gives no global-optimum guarantee for nonzero modes. Exact-zero removal is lossless;
approximate-mode removal is an approximation.

### Cost at d3/d5 [ours]
The dense linear algebra is `D×D` for the compact scheme and `D²×D²` for the general scheme. The
dominant cost can instead be the environment contraction that constructs the Gram. A finite patch
makes the contraction exact in principle, not automatically cheap. The prior “sub-millisecond /
negligible” estimate was not benchmarked and is retracted; cost must be measured on the actual path.

### Leakage interaction — could it corrupt physical content? [ours]
**Yes.** ZMT is physically blind: a small metric direction can be an approximate virtual redundancy
or weak but genuine leakage physics.

- `f = N/|E_D|²` (Eqs. 5/19) measures the state-norm cost assigned by the construction. `f=0`
  certifies an exact linear dependence and lossless removal. **Small positive `f` does not identify
  why it is small.** Neither the `f` spectrum nor loopiness `l` is an ontology test.
- The paper's `δ` switches from compact ZMT1 to general ZMT2/3; it does not stop compression or
  protect leakage. No published lower bound on the smallest physical leakage direction is supplied.
- Any fixed-target compression can delete weak physical modes. Neither the selected-mode objective nor
  the ZMT1→ZMT2/3 switch certifies the complete QEC record.
- Validation must therefore compare the exact and truncated **joint `(detectors, obs)` record law**
  at d3 using TV/KL and a frozen-decoder LER, while logging `f`, state overlap, and `S_A` only as
  internal diagnostics.

### Does it need a prior gauge fixing? (asked)
Recommended, not required. ZMT1/ZMT2 in the examples fix the **EAT gauge first**; ZMT3 in the Ising
case runs **without** it, while ZMT1/3 in the t-J case are EAT-gauge-initialized. The metric — and
hence the zero modes — **depend on the bond gauge** (Sec. V opening, lines 408–410), so a canonical
gauge (EAT/Schmidt) may improve conditioning and gives the loopiness diagnostic. For us: fix the EAT
gauge first if its assumptions hold, but reject any non-Hermitian Gram as an implementation bug rather
than relying on gauge fixing to cure it.

### The Z2 gauge example (Sec. VIII) = the stabilizer-flavored evidence we care about
The Z2 lattice gauge Hamiltonian `H = −Σ_p σz_{p1}σz_{p2}σz_{p3}σz_{p4} − g Σ_s σx_s` (Eq. 27) has
**four-body plaquette stabilizer terms** whose evolution operator is a **periodic MPO with a virtual
loop index `j` around the plaquette** (Eq. 29–30) — structurally the closest thing in the paper to a
**surface-code stabilizer**. Findings directly relevant to us: (i) **EAT fails** — it "obliterates the
effect of the pMPO gate" (lines 923–926), i.e. canonical/Evenbly truncation destroys stabilizer
content; (ii) plain **SVD is unconverged even at D=10** while **ZMT3 converges quickly with D**
(Fig. 10, `⟨σx⟩`); (iii) here the **final** error is init-dependent — the loop-aware initialization is
essential. This is useful structural evidence that loop-aware initialization can matter; transferring
it to a surface-code PEPS is still an [ours] hypothesis. **Caveat:** this is a *unitary,
translationally-invariant, unmeasured, non-leaky* Z2 model — not our finite/measured/leaky code.

## Limitations [paper] + [ours]
- **[paper] ZMT is an initialization, not a solver.** Every example runs variational optimization
  afterward. The claim is "better *initial* truncation," and only in the hard Z2 case does init
  determine the final answer.
- **[paper] Gauge-dependent.** The metric and zero modes depend on the bond gauge (Sec. V); results
  differ across ZMT1/2/3 and across gauge choices; no single variant is universally best (ZMT3 best
  for Z2, ZMT2 best for TRG/Heisenberg).
- **[paper] No error guarantee for approximate modes beyond the `f = N/|E_D|²` leading order** (App.
  A/B give the next order `f_min`; App. C's eigenmode improvement is only `O(f²)`).
- **[paper] Demonstrated only on infinite iPEPS (real/imag-time, ground/thermal) and TRG-pMPS**, all
  unitary or imaginary-time, translationally invariant, **pure Clifford-free spin/fermion models —
  no measurement, no leakage, no finite code patch.**
- **[ours] Direct applicability to our setting is PARTIAL** (see structured output). The *method* is
  bond-local and state-agnostic, so it transfers; but nothing in the paper tests finite + projectively
  measured + leaky, so the transfer is an [ours] inference to be validated.
- **[ours] Leakage corruption is a real risk in every fixed-target variant.** The `δ` switch changes
  which ZMT construction is used; it does not identify physical content or certify a multi-time record.
- **[ours] Companion 2605.09385 (Z2) unread** — the in-paper Sec. VIII already covers the
  stabilizer-flavored behavior, but the companion may add finite-size / measurement detail; flagged.

## Epistemic-status declaration
- **(a) exact:** The algebraic identities are exact — Eq. 4 (exact-zero-mode elimination is a lossless
  identity when `N_D=0`), Eq. 5 & 19 (`f = N/|Z_D|²`, `f = N/|E_D|²`, the leading-order truncation
  error), the Sec.-III pinv-vs-gauge toy (Eq. 6–9), and the Sec.-V statement that ZMT≡EAT in the
  non-loopy `g̃=Λ⊗Λ` case. The exact correspondence is `ker(Ψ†Ψ)=ker(Ψ)` on the bond-label
  space. `ΨΨ†` acts in a different space; only its nonzero spectrum and rank agree automatically.
- **(b) prediction band:** That ZMT initialization will improve the failing d3/d5 optimization while
  preserving the full record is a **registered falsifiable bet**, not yet run.
- **(c) heuristic gate:** Loopiness thresholds, positive-`f` cutoffs, the greedy lowest-`f` rule, and
  threshold-vs-fixed-rank choices are design gates only — never physical classifiers or conclusion
  premises.
- **Provisional:** “ZMT is the FORK-A fix” remains unlicensed until an exact d3 **record-law** oracle
  passes. GF(2) entropy and `S_A` are useful controls but are insufficient acceptance targets.

## How to use / trust + open questions [ours]
- **Trust level:** FULL-TEXT 精读 of the 13-page v2. Equations transcribed and cross-checked from the
  PyMuPDF text. The work is now published as **Physical Review E 112, 055307 (2025)**; the PDF itself
  predates the journal metadata.
- **Independent verification potential:** Data are on RODBUK (Ref. 59). The Sec.-III toy and the
  Sec.-V ZMT≡EAT theorem are checkable by hand. The Z2 `⟨σx⟩` convergence (Fig. 10) is the most
  reproducible target if we want to replicate the loop-cutting advantage before adopting it.
- **Concrete next actions for FORK A:**
  1. Before implementation, test whether the actual cut-state Gram is Hermitian PSD and has exact
     zero modes; do not infer this from bounded `S_A`.
  2. **Leak-off validation:** compare exact-zero removal, ZMT+variational refinement, and the current
     solver; use state equality and GF(2)/`S_A` only as internal controls.
  3. **Leak-on validation (critical):** sweep the positive-`f` threshold without labeling small modes
     “gauge”; compare the full d3 joint record to the exact qutrit instrument using TV/KL and frozen
     decoder LER.
  4. Compare ZMT-initialized variational optimization against ZMT-alone; the paper supports the former.
- **Open questions:**
  1. **Measurement.** After a projective stabilizer measurement (rank-1 projector on a physical index)
     the bond-truncation problem is still a local Gram — does anything break? (Expected: no, the
     method is gate/measurement-agnostic, but untested.)
  2. **Finite-patch environment.** Our exact finite-patch metric replaces the paper's CTMRG/NTU
     infinite environment. Is the finite Gram still well-conditioned enough for the EAT-gauge SVD
     (Eq. 23) near a boundary? (Watch for near-degenerate `Λ` at open boundaries.)
  3. **Leakage gap robustness.** Does the `f`-gap between loop and leakage modes survive as leakage
     strength → 0 (motional-narrowing-like)? If it closes, threshold-δ ZMT and genuine leakage become
     indistinguishable — the honest failure boundary of FORK A, and the argument for FORK B
     (stabilizer-frame carrier tracking only magic).
  4. **Companion 2605.09385** — read if finite-size/measurement Z2 detail is needed.

## Key equations / quantities (implementation reference)
- `|ψj⟩`, `|ψij⟩` — cut states (one retained bond label / two endpoint labels).
- `g_ij = ⟨ψi|ψj⟩` (Eq. 1) — compact `D×D` bond-label Gram, `g=Ψ†Ψ` when cut states are columns of `Ψ`.
- `Z_j = U_{jD}` (zero mode, Eq. 1–2); gauge `z=−1/Z_D` (Eq. 4); error `f = N_D/|Z_D|²` (Eq. 5).
- `g_{ij,i'j'} = ⟨ψij|ψi'j'⟩` (Eq. 11) — general `D²×D²` metric; zero mode `Z`, `Tr Z†Z=1`.
- `Z_ij = S⁻¹ E_k S` (Eq. 13); gauge `z=−1/E_D`; SVD `δ−Z/E_D = UλV*` with `λ_D=0` (Eq. 14);
  error `f = N/|E_D|²` (Eq. 19).
- EAT product `g ≈ g_L λ1 g_R` (Eq. 20); **loopiness `l = λ2/λ1`** (Eq. 21); EAT gauge (Eq. 22–24).
- Threshold `δ` (ZMT1-to-ZMT2/3 switch during compression to target `χ`, not a stop rule or
  leakage/record certificate, Sec. X).
- App. A/B: exact `f_min` beyond leading order. App. C: `O(f²)` eigenmode refinement.
- Refs: **31** = Sinha/Rams/Czarnik/Dziarmaga PRB 106, 195105 (2022) = EAT; **32** = Evenbly PRB 98,
  085155 (2018) = closed-loops gauge; **40** = Dziarmaga PRB 104, 094411 (2021) = NTU (our companion).
