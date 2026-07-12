# Full-text review — I. Sokolov, Y. Zhang, J. Dziarmaga, "Truncating loopy tensor networks by zero-mode gauge fixing" (arXiv:2508.00338)

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
- **Venue / status:** arXiv:2508.00338v2 [quant-ph], 4 Nov 2025. Preprint (not yet a journal ref in
  the PDF). Data openly available on RODBUK (Ref. 59).
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
cutting **both** legs of the bond (ket-index `i`, bra-index `j`), giving the more powerful
loop-cutting truncation (Eq. 12–17), with error `f = N/|E_D|²` (Eq. 19). Section V places ZMT against
**environment-assisted truncation (EAT)** [Ref. 31]: EAT approximates the metric by its **leading**
left–right product `g ≈ g_L λ1 g_R` (Eq. 20), which is exact only for a **non-loopy** bond; the
**loopiness** `l = λ2/λ1` (Eq. 21) measures the failure. **In the non-loopy case ZMT reduces exactly
to EAT / canonical-spectrum truncation; in the loopy case ZMT can cut a loop that EAT/SVD/Vidal-gauge
cannot** (Sec. V, last paragraph). The headline empirical claim: across all six examples ZMT gives
**better *initial* truncation errors** than EAT/SVD/TEBD, and in the hard **Z2 gauge** case the
initialization quality determines the *final* error after variational optimization (EAT "obliterates"
the plaquette gate; SVD is unconverged at D=10 while ZMT3 converges — Figs. 8–10).

**One-line relevance to us:** this is the FORK-A foundation. ZMT is a **deterministic,
pseudoinverse-free, loop-aware** replacement for the *initialization* step our FET-ALS gets wrong
(Sec. III is a two-line proof that the `pinv` solution keeps the redundant bond while the zero-mode
gauge choice cuts it). It confirms our independent derivation: **truncating "zero modes of the
cut-states metric" IS truncating the null space of the Gram** `ker(G)`. **But it is an initializer,
not a full variational solver, and it is physically blind — it cannot by itself distinguish a gauge
loop from weak leakage magic; the protection is a threshold `δ` (Sec. X), which must be set below the
leakage scale.**

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

### Determinism / monotonicity / role in the pipeline (load-bearing)
- **ZMT is a deterministic INITIALIZATION**, not a full solver: build the metric (one exact local
  environment contraction) → eigendecompose/SVD → gauge-fix `z=−1/E_D` → truncate the lowest-`f` mode,
  optionally one-by-one down to target. **No alternating least-squares sweep in the init.** The only
  iterative variant is the optional ZMT4 product ansatz.
- **Every example follows ZMT init with the usual variational (ALS-like) optimization.** So ZMT does
  **not eliminate** the variational sweep — it de-risks it. In the easy models (Ising Fig. 5, t-J
  Fig. 11) the *final* error is init-independent (any init converges). In the **hard loopy Z2 case**
  the *final* error **depends on the init** — EAT/SVD give a bad basin the ALS cannot escape, ZMT3
  gives a good one (Figs. 8–10). This is the regime we are in.
- **Monotone?** Not a global-optimality guarantee, but it is **deterministic and
  non-divergent**: it never pseudo-inverts a near-singular metric (Sec. III is the whole point); the
  greedy lowest-`f` elimination is a controlled descent on the initialization error with the exact
  bound Eq. 5 / Eq. 19 per step. Contrast our FET-ALS: non-monotone fidelity + pinv divergence.

## The MECHANISM (for implementation)
Per bond to truncate (finite d3/d5 patch, single-wire PEPS):
1. **Cut the bond.** Compact scheme: expose one leg → cut states `|ψj⟩`, `j=1..D`. General scheme:
   cut both legs → `|ψij⟩`, `i,j=1..D`.
2. **Build the metric (Gram) by contracting the LOCAL environment.** Compact: `g_ij = ⟨ψi|ψj⟩`
   (`D×D`, Eq. 1). General: `g_{ij,i'j'} = ⟨ψij|ψi'j'⟩` (`D²×D²`, Eq. 11). For a **finite** code patch
   this environment is contracted **exactly** (no infinite CTMRG) — cheap.
3. *(Recommended)* **Fix the EAT gauge** (Eq. 22–24) first: diagonalize `g_L,g_R`, SVD the overlap,
   insert Eq. 24. This makes `g_L,g_R` Hermitian/non-negative and puts you in the canonical (Schmidt)
   frame; the loopiness `l = λ2/λ1` (Eq. 21) is your **diagnostic** of how loopy the bond is.
4. **Eigendecompose the metric** (`U N U†`, compact) or **diagonalize the zero mode** `Z`
   (`Z_ij = S⁻¹ E_k S`, Eq. 13, general). Compute per-mode error `f = N/|Z_D|²` (Eq. 5) or
   `f = N/|E_D|²` (Eq. 19).
5. **Gauge-fix `z = −1/E_D` (largest-|E|) and truncate the resulting zero singular value** (Eq. 14–17).
   Eliminate the lowest-`f` mode; absorb the gauge factor into the two adjacent tensors.
6. **Two truncation MODES:**
   - **Fixed-χ mode:** cut one-by-one down to a target bond `D` regardless of error (Ising/t-J).
   - **Threshold-δ mode (SAFE for us):** keep cutting only while the incurred error Eq. 5 stays below
     `δ`; stop at whatever bond `χ' ≥ χ` first exceeds `δ` (TRG ZMT2, lines 1154–1160). **Accept the
     resulting bond; do not force it down.**
7. **Follow with the ordinary variational optimization** (the ALS sweep) from this initialization.
8. *(Optional)* App. C: perturb the chosen eigenmode `Z → Z + fε` (Eq. C4–C7) to lower `f` further —
   but the gain is only `O(f²)` and "may not justify the numerical overhead."

**Key correspondence to our independent derivation (asked explicitly):**
Yes. The paper's cut-states metric `g_ij = ⟨ψi|ψj⟩` **is** the Gram of the columns of `Ψ` (each column
= one cut state as a vector over the rest of the network). `g = Ψ†Ψ`, so **`ker(g)` = the set of
linear-dependence relations among cut states = `ker(Ψ†Ψ)`, which has the same rank/support as our
`ker(G)` with `G = ΨΨ†`** (the ket-bra Gram). Truncating "zero modes of the cut-states metric" =
projecting onto `range(ΨΨ†)` = removing exactly the redundant bond directions = our null-space
truncation. **Two precise caveats:**
- Our `ΨΨ†` lives on the *environment/physical* space; the paper's `g = Ψ†Ψ` lives on the *bond*
  space. Same nonzero spectrum, same rank; the *bond-space* form (paper's) is the one you truncate.
- Our `G` matches the paper's **compact Sec-II** metric if we cut **one** leg; it matches the
  **general Sec-IV** `D²×D²` metric if we cut **both** legs (ket and bra independently). The paper
  proves Sec. II is the diagonal restriction of Sec. IV — so both are the same object at different
  resolution, and our derivation is the compact one.

## Relevance to qec_twin [ours]

### FORK A foundation — replacing the FET-ALS initialization
Our failure (from the active line): single-edge FET-ALS on the d3/d5 single-wire PEPS grows the bond
(6→12→15…) with non-monotone fidelity and pinv divergence, while the true bipartition entropy `S_A`
is bounded (2 ebits d3 / 4 ebits d5). Root cause diagnosed as non-Hermitian/non-PSD metric +
unregularized pinv + over-parameterization on the **long-range (loop) bonds** (user steer:
"主要是修复长程关联"). This paper is a direct match:
- **The excess bond IS loop redundancy.** For the **leak-off** (pure-stabilizer) case, the extra bond
  above `S_A` is exactly the virtual-loop entanglement of Fig. 1 — decoupled from physical content.
  ZMT's **exact zero-mode elimination** (Eq. 4, `N_D=0`) removes it **losslessly and
  deterministically**, no variational sweep needed. This is the clean deterministic replacement the
  handoff wanted ("use the DETERMINISTIC gauge-fixed canonical-spectrum truncation as PRIMARY").
- **The loopiness `l = λ2/λ1` (Eq. 21) is the diagnostic spectrum** the handoff asked for ("the WTG
  spectrum DIAGNOSES solver-failure vs genuine long-range physics"). A bond with `l≈0` is non-loopy →
  EAT/canonical truncation suffices; a bond with `l>0` is loopy → the ALS *should* be expected to
  struggle and ZMT is required. This gives a per-bond, computable go/no-go for which bonds need the
  loop-aware cut.
- **It closes the Evenbly-2018 gap.** Ref. 32 (Evenbly, closed-loops gauge) is exactly the EAT-gauge
  Sec. V builds on; ZMT's Sec.-V theorem shows the canonical/Evenbly gauge truncation (EAT) is
  *insufficient for loops* and ZMT strictly extends it. So this paper is the reference the handoff
  named as "NOT yet read."

### Reliability vs our ALS (asked)
More reliable on exactly our failure bonds: (i) **no pinv of a singular metric** — Sec. III proves
pinv keeps the redundant bond; ZMT's gauge choice cuts it. (ii) **Hermitian/non-negative metric**
available via the EAT gauge (Eq. 22–24) — our non-Hermitian-metric crash mode is avoided. (iii)
**Deterministic** eigendecomposition, no alternating sweep in the init → no non-monotone-fidelity
oscillation. (iv) **Loop-aware** (Sec. V) — cuts loops EAT/SVD/Vidal cannot. **Honest caveat:** it is
an *initializer* the paper still follows with variational optimization; it de-risks the ALS rather
than deleting it. For pure loop redundancy the exact-zero-mode step alone suffices; for genuine
long-range physics it hands the ALS a good basin.

### Cost at d3/d5 on one RTX 5090 (asked)
Cheap. The dominant cost is the **local environment contraction** to build the metric — for a
**finite** d3/d5 patch this is an exact finite contraction we already perform (no infinite CTMRG). The
linear algebra is trivial at our scale: compact metric `D×D`; general metric `D²×D²` with
eigendecomposition `O(D^6)`. Our bonds are `D≈6–15`, so `D²×D² ≤ 225×225` — a sub-millisecond dense
eigendecomposition on GPU or even CPU. Contrast the paper's own cost worry (`O(D^8)` NTU-metric build,
`O(D^{10–12})` CTMRG) which is an **infinite-iPEPS, large-D** concern that **does not bind us**: our
patch is finite and small-D. Net: ZMT adds negligible cost relative to the trajectory loop.

### Leakage interaction — could it corrupt the physical `S_A`? (CRITICAL, asked)
**Yes, it *can*, and here is the precise condition and the safeguard.** ZMT's metric is **physically
blind**: it truncates directions with small metric eigenvalue `N`, whether that smallness comes from
(a) a genuine gauge/loop redundancy (an *exact* linear dependence, `N=0`, decoupled from physical
indices — truncating it changes the state by **exactly zero**, Eq. 4) or (b) a **weak but physical**
non-Clifford leakage direction (small `N>0`, but it *does* contribute to the physical state).
- The **discriminator the paper hands us is exactly right**: the per-mode error `f = N/|E_D|²`
  (Eq. 5/19) is the *actual norm-change* of truncating that mode. A true loop has `f→0`
  (provably lossless). A leakage magic direction has **strictly `f>0`** proportional to its physical
  weight. So the `f`-spectrum (equivalently the metric/`N` spectrum, and the loopiness `l`) **does
  diagnose gauge-artifact vs genuine physics** — which is precisely the leak-off vs leak-on question.
- **The protection is threshold-δ mode.** Run ZMT in the TRG-ZMT2 style (Sec. X, lines 1154–1160):
  truncate only while `f < δ`, and **set `δ` strictly below the leakage magnitude** (below the
  smallest physical Schmidt weight the weak non-Clifford leakage injects). Then ZMT removes only the
  `f≈0` loop redundancies and **cannot touch the leakage directions** → `S_A` (and the leakage magic
  above the GF(2) stabilizer entropy) is preserved.
- **The danger is fixed-χ mode.** If instead you force the bond down to a target `χ` regardless of
  error (the Ising/t-J "cut one-by-one down to D" mode), ZMT **will** truncate the smallest-`f` modes
  including weak leakage, corrupting the physical `S_A`. This is the tensor-network analog of the
  project's standing "Clifford-invariant ≠ leakage-invariant" trap (dropping a physically-applied
  direction on a gauge argument). **Mandate: for the leaky carrier, ZMT MUST run in threshold-δ mode,
  never fixed-χ mode.**
- **Untested for us:** the paper never treats leakage, projective measurement, or a finite patch. The
  above is an [ours] inference from the method's structure (the metric is built from the state tensors
  and is gate-agnostic, so weak non-Clifford content simply appears as small-but-nonzero `N`). It
  should be validated: on a leak-on d3 wire, confirm the `f`-spectrum shows a gap between the `f≈0`
  loop modes and the leakage modes, and that threshold-δ ZMT reproduces the exact `S_A` (2/4 ebits +
  leakage) against the independent GF(2) stabilizer-entropy oracle.

### Does it need a prior gauge fixing? (asked)
Recommended, not required. ZMT1/ZMT2 in the examples fix the **EAT gauge first**; ZMT3 in the Ising
case runs **without** it, while ZMT1/3 in the t-J case are EAT-gauge-initialized. The metric — and
hence the zero modes — **depend on the bond gauge** (Sec. V opening, lines 408–410), so a canonical
gauge (EAT/Schmidt) improves reliability and gives the loopiness diagnostic for free. For us: fix the
EAT gauge first (it also Hermitizes the metric, curing our non-Hermitian crash mode).

### The Z2 gauge example (Sec. VIII) = the stabilizer-flavored evidence we care about
The Z2 lattice gauge Hamiltonian `H = −Σ_p σz_{p1}σz_{p2}σz_{p3}σz_{p4} − g Σ_s σx_s` (Eq. 27) has
**four-body plaquette stabilizer terms** whose evolution operator is a **periodic MPO with a virtual
loop index `j` around the plaquette** (Eq. 29–30) — structurally the closest thing in the paper to a
**surface-code stabilizer**. Findings directly relevant to us: (i) **EAT fails** — it "obliterates the
effect of the pMPO gate" (lines 923–926), i.e. canonical/Evenbly truncation destroys stabilizer
content; (ii) plain **SVD is unconverged even at D=10** while **ZMT3 converges quickly with D**
(Fig. 10, `⟨σx⟩`); (iii) here the **final** error is init-dependent — the loop-aware initialization is
essential. This is strong support that on stabilizer-loop-carrying bonds (our surface-code case)
ZMT is the right tool and canonical/ALS-only truncation is not. **Caveat:** this is a *unitary,
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
- **[ours] Leakage corruption is a real risk in fixed-χ mode** — must run threshold-δ.
- **[ours] Companion 2605.09385 (Z2) unread** — the in-paper Sec. VIII already covers the
  stabilizer-flavored behavior, but the companion may add finite-size / measurement detail; flagged.

## Epistemic-status declaration
- **(a) exact:** The algebraic identities are exact — Eq. 4 (exact-zero-mode elimination is a lossless
  identity when `N_D=0`), Eq. 5 & 19 (`f = N/|Z_D|²`, `f = N/|E_D|²`, the leading-order truncation
  error), the Sec.-III pinv-vs-gauge toy (Eq. 6–9), and the Sec.-V statement that ZMT≡EAT in the
  non-loopy `g̃=Λ⊗Λ` case. The correspondence "cut-states metric zero modes = `ker` of the Gram = our
  `ker(G)`" is an **exact** linear-algebra identity (up to the bond-side/environment-side transpose).
- **(b) prediction band:** That ZMT (threshold-δ) will fix our d3/d5 bond growth to the true `S_A`
  while preserving weak leakage magic is a **registered falsifiable bet**, not yet run — a miss is a
  finding, not later citable as fact.
- **(c) heuristic gate:** The loopiness `l=λ2/λ1` threshold, the truncation threshold `δ` (set below
  the leakage scale), the greedy lowest-`f` selection rule, and "use threshold-δ not fixed-χ" are
  design/gating rules only — never a premise or derivation basis.
- **Provisional:** The whole "ZMT is the FORK-A fix" conclusion is PROVISIONAL until validated on a
  leak-on d3 wire against the independent GF(2) stabilizer-entropy oracle. Usable for go/no-go
  gating; nothing may be *built* on it (no further derivation) until that check passes.

## How to use / trust + open questions [ours]
- **Trust level:** FULL-TEXT 精读 of the 13-page v2. Equations transcribed and cross-checked from the
  PyMuPDF text. This is a **preprint** (2025) by the NTU author — high method credibility, but not yet
  peer-reviewed, so the empirical claims (Figs. 5–14) carry the usual preprint caveat.
- **Independent verification potential:** Data are on RODBUK (Ref. 59). The Sec.-III toy and the
  Sec.-V ZMT≡EAT theorem are checkable by hand. The Z2 `⟨σx⟩` convergence (Fig. 10) is the most
  reproducible target if we want to replicate the loop-cutting advantage before adopting it.
- **Concrete next actions for FORK A:**
  1. Implement ZMT init (steps 1–7 above) on the single-wire d3 PEPS bond; fix the EAT gauge (Eq.
     22–24) to Hermitize the metric.
  2. **Leak-off validation:** confirm exact-zero-mode elimination cuts the grown bond (6→12→15…) back
     to the true `S_A=2` ebits deterministically, matching the GF(2) stabilizer-entropy oracle, with
     **no** variational sweep. This is the direct test of "bond growth = gauge artifact."
  3. **Leak-on validation (the critical one):** run **threshold-δ** ZMT, `δ` below the leakage scale;
     confirm the `f`/loopiness spectrum shows a gap (loop modes `f≈0` vs leakage modes `f>0`) and that
     `S_A` (stabilizer + leakage magic) is preserved. Then re-probe WP1'.
  4. Compare against keeping the ALS as a *follow-up* optimizer from the ZMT init vs ZMT-alone.
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
- `|ψj⟩`, `|ψij⟩` — cut states (one leg / both legs open).
- `g_ij = ⟨ψi|ψj⟩` (Eq. 1) — compact `D×D` Gram; `g = ΨΨ†`/`Ψ†Ψ` in our notation.
- `Z_j = U_{jD}` (zero mode, Eq. 1–2); gauge `z=−1/Z_D` (Eq. 4); error `f = N_D/|Z_D|²` (Eq. 5).
- `g_{ij,i'j'} = ⟨ψij|ψi'j'⟩` (Eq. 11) — general `D²×D²` metric; zero mode `Z`, `Tr Z†Z=1`.
- `Z_ij = S⁻¹ E_k S` (Eq. 13); gauge `z=−1/E_D`; SVD `δ−Z/E_D = UλV*` with `λ_D=0` (Eq. 14);
  error `f = N/|E_D|²` (Eq. 19).
- EAT product `g ≈ g_L λ1 g_R` (Eq. 20); **loopiness `l = λ2/λ1`** (Eq. 21); EAT gauge (Eq. 22–24).
- Threshold `δ` (safe/leakage-preserving truncation mode, Sec. X).
- App. A/B: exact `f_min` beyond leading order. App. C: `O(f²)` eigenmode refinement.
- Refs: **31** = Sinha/Rams/Czarnik/Dziarmaga PRB 106, 195105 (2022) = EAT; **32** = Evenbly PRB 98,
  085155 (2018) = closed-loops gauge; **40** = Dziarmaga PRB 104, 094411 (2021) = NTU (our companion).
