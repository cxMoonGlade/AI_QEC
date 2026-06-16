# Full-text review — Harper, Nakhl, Sevior & Usman, "Non-Clifford Crosstalk Noise in Surface Codes Using Hybrid Stabilizer–Tensor Network Methods" (arXiv:2605.29514v1)

> **Provenance (2026-06-15): FULL-TEXT read.** The owner-encrypted PDF (user-downloaded,
> `docs/papers/Non-Clifford_..._2605.29514v1.pdf`) was decrypted with an empty user password
> (`outputs/decrypt_pdf.py`, pikepdf) and the text extracted to `outputs/harper_2605.29514.txt`
> (`outputs/extract_pdf_text.py`, pypdf). All §/Eq/Table/Figure references below are from that text.
> The **6 figures' plotted curves are not pixel-extracted** — figure-level facts here are the captions
> + the numbers stated in the running text (threshold, χ_max, θ, J_ZZ/t_g are all in the text). This
> supersedes the earlier digest-tier note. Epistemic tags: **[paper]** = stated in the paper;
> **[twin]** = our application/inference for `qec_twin` (not the paper's claim).

## Metadata [paper]
- **Authors / affiliation.** Ben Harper, Azar C. Nakhl, Martin Sevior, Muhammad Usman (Univ. Melbourne; Data61/CSIRO; Monash).
- **Venue / status.** arXiv:2605.29514v1 [quant-ph], 28 May 2026; 8 pp, 6 figs; no journal yet.
- **Type.** Classical **forward simulation** (hybrid stabilizer–tensor-network) of the rotated surface code under coherent non-Clifford crosstalk during syndrome extraction.
- **Predecessor.** Incoherent (Pauli-twirled) crosstalk study Zhou–Ji–Ding arXiv:2503.04642 [ref 13].
- **Simulator.** GCAMPS library [ref 21, Harper et al., SC/HPCAsia '26]; stabilizer-TN lineage: Nakhl et al. PRL 134, 190602 (2025) [ref 22, magic-state injection], Masot-Llima & Garcia-Saez PRL 133, 230601 (2024) [ref 23].

## Executive summary [paper]
Standard QEC simulation stays Clifford (Stim) by assuming incoherent (Pauli) noise or noise-free
syndrome extraction; the full density matrix (`4^n`) is infeasible at scale; tensor networks alone
choke on the surface code's high entanglement. This paper uses a **hybrid stabilizer–tensor-network**
(the Clifford bulk in a stabilizer/Clifford operator, the few non-Clifford coherent insertions in an
MPS) to simulate **coherent ZZ crosstalk during syndrome extraction**. Findings: coherence **raises
logical error rates below threshold** (the threshold itself ≈ unchanged vs the Pauli-twirl
approximation, ~0.8%), and **the coherent distribution matters** — two noise models with identical
Pauli-twirl approximations give different sub-threshold LER (constructive vs destructive interference).

## Method (from §IV, verbatim structure) [paper]
**Representation (Eq 7):** an arbitrary state is `|ψ⟩ = C |MPS⟩`, with `C` a Clifford operator and
`|MPS⟩` a matrix product state.
- **Clifford gate** `G`: updates `C` directly (`G C|MPS⟩ = C'|MPS⟩`) — the Gottesman–Knill tableau path (what Stim does), `poly(n)`.
- **Non-Clifford op** `U`: decomposed into a sum of Paulis, commuted through `C`, then applied to the MPS: `U|ψ⟩ = Σ_i P_i C|MPS⟩ = C Σ_i P̃_i|MPS⟩ = C|MPS'⟩`. A physically **local** Pauli string, commuted through `C`, can become **higher-weight** (non-local) on the TN — `C` turns local ops into non-local ones on the network.
- **Measurement:** a sum of Paulis is commuted through `C` and applied to the MPS; the non-Clifford error in the MPS **collapses to a Pauli error in the Clifford tableau** at measurement.
- **QEC interpretation (key):** `C` is the **ideal Clifford operator implementing the code**; non-Clifford errors do **not** change `C`; the **MPS carries the error that perturbs the ideal Clifford state**.
- They deliberately do **NOT** use the usual stabilizer-TN optimisations — **no magic-state injection** (too many non-Clifford gates → too many magic ancillas) and **no Clifford optimisation** (cost outweighed the bond-dimension benefit).

**Truncation (§IV.B, Eq 8):** SVD across the central MPS cut, `|ψ⟩ = Σ_{i<χ} λ_i |i_L⟩|i_R⟩`; bond
dimension capped at `χ_max ≤ 2^{N/2}`, discarding the smallest singular values.
- **Schmidt values decay exponentially** (Fig 2, d = 3,5,7,9) → large truncation is safe.
- **`χ_max = 32` for all results** (Fig 3, d = 9, converged).
- The largest MPS component is the **zero state (no crosstalk)**; noise is the low-probability tail. Over-truncation **lowers** the measured LER ⇒ the reported LERs are a **lower bound**.

## Noise model (§III) [paper]
- **Baseline depolarizing** inserted after each gate: single-qubit `ε₁` (Eq 2) at `p₁`, two-qubit `ε₂` (Eq 3) at `p₂`. **Table I rates:** `p₁ = 0.1p`, `p₂ = p`, reset `p_R = 2p`, measurement `p_M = 5p`; `p` is swept for the threshold.
- **Crosstalk = coherent ZZ rotation between nearest neighbours when a 2-qubit gate is applied** (gate-based NN; Eq 4): `ε(ρ) = e^{iθ Z₁⊗Z₂} ρ e^{−iθ Z₁⊗Z₂}`, with `θ = J_ZZ · t_g` (Eq 5), `J_ZZ ≈ 100–150 kHz`, `t_g ≈ 100–150 ns` → **`θ ≈ 10⁻³` (fixed)**. Implemented as `RZ(θ/2)` + CNOT gates; occurs **after the entangling gates** (Fig 1 dashed lines). They note gate-era vs always-on ZZ are qualitatively similar in QEC circuits (almost always interacting).
- **Pauli-Twirl Approximation (PTA, Eq 6):** `ε_twirl(ρ) = (1−sin²θ)ρ + sin²θ (Z⊗Z)ρ(Z⊗Z)` — **mathematically the projection of the channel's Pauli-transfer matrix onto its diagonal** (drops the off-diagonal/coherence).
- **Logical error metric (Eq 1):** `P_L = (1/N) Σ_i |sin(θ_i/2)|` over logical rotation angles `θ_i` from sampled syndromes — the **average diamond-norm distance** between the logical error channel and identity (Bravyi et al. [11]); reduces to standard LER for Pauli errors (`θ_i ∈ {0,π}`).

## Decoder (§III.D) [paper]
MWPM via **PyMatching** [ref 27]. **PyMatching only supports Pauli error models, so the decoding error
model is generated from the PTA** — i.e. the simulation carries coherence but the **decoder is
Pauli/coherence-blind**.

## Results (§V) [paper]
- `J_ZZ = 150 kHz`, `t_g = 150 ns`; `10⁵` samples per data point.
- **Crosstalk lowers the threshold from ~1% to ~0.8%** (Fig 4). Adding **coherence raises sub-threshold LER further** but does **not** significantly move the threshold.
- **Distribution matters (§V.B):** a random-sign angle `θ_i ∈ {θ, −θ}` (Eq 9) has the **same PTA** as the fixed-angle model (`sin²θ = sin²(−θ)`), but **destructive** interference gives a **lower sub-threshold LER** than the fixed (constructive) model (Figs 5, 6, d = 9). So the Pauli-twirl is not a sufficient statistic for sub-threshold LER.

## Strengths / limitations
- **[paper] S1.** Simulates the regime Stim/Pauli cannot (coherent + noisy syndrome extraction) without the full `4^n` density matrix — the selling point.
- **[paper] S2.** Coherence-preserving **and** scalable at once (Clifford bulk in `C`, sparse coherent magic in the MPS); χ_max = 32 suffices to d = 9 by the Schmidt decay.
- **[paper] L1.** **Forward simulation only — noise is assumed known** (`θ = 10⁻³` fixed); **no inference/calibration/learning**.
- **[paper] L2.** **Decoder is Pauli (PTA)** — shows coherence's cost, does not exploit it.
- **[paper] L3.** Truncation makes LER a **lower bound**; no temporal drift / non-Markovianity (listed as future work, with amplitude damping, leakage, PEPS/TTN layouts, qLDPC).

## Relevance to the twin (ADR 0008 carrier study) [twin — our application, not the paper's claim]
1. **This is the carrier that dissolves our dense-register wall.** Our step-2/3 dead end was a
   dense density-matrix frame (9q instrument falsified; faithful d3 = 17q = 275 GB infeasible; the
   interleaved data gates + 8 simultaneously-live ancillas forced `4^{17}`). In `|ψ⟩ = C|MPS⟩` the
   **entire Clifford backbone** (the interleaved Y/H/X data gates, 4 CZ layers, reset, measure — all
   Clifford) sits in `C` at `O(n²)`; only the **coherent noise** enters the MPS (χ_max ~ 32). The
   register-size question (9q/13q/17q) disappears. d3 (9 data + 8 ancilla) is smaller than their d = 9.
2. **The `C = ideal code / MPS = error` split IS the white-box structure.** `C` = the fixed ideal d3
   Clifford syndrome extraction; the **MPS carries the θ-parameterised coherent mechanisms we recover**;
   held-out syndrome NLL comes from the MPS measurement. This maps the twin's "recover the coherent
   window channel from real syndromes" directly onto their representation.
3. **The gap = exactly our novelty.** Harper is **forward-only with a PTA decoder**. The twin needs
   the **inverse**: a **differentiable** stabilizer-TN whose MPS depends on θ (the `e^{−iθP}`
   Pauli-sum coefficients cos/sin are smooth in θ → MPS amplitudes differentiable → autograd-fit θ to
   real held-out syndrome NLL). Differentiating **through the SVD truncation** needs care (the
   discard is non-smooth; fixed-χ or soft truncation). So Harper is a **carrier-engine REFERENCE
   (scalable + coherence-preserving forward), not a carrier** — it does not learn from data.
4. **Decoder-blindness does not bind our validation.** Their Pauli decoder is a *cost-measurement*
   choice; the twin's recover validation is **held-out syndrome NLL (decoder-independent)**, so the
   PTA-decoder limitation (L2) does not constrain our white-box fit/validate loop. (Their L3 LER
   lower-bound caution applies only if we later score %ΔLER under a frozen decoder.)
5. **Our dense work is the oracle, not waste.** The dense `WindowChannel` is feasible at the d7
   interior window (13q, < 15q backend wall) and bit-exact; it is the **correctness oracle** to
   validate a differentiable stabilizer-TN at small scale via standard metrics (trace distance / Choi
   / NLL) before scaling.
6. **Physics backing for the coherent wedge.** "Coherence raises sub-threshold LER" and "distribution
   matters (same PTA, different LER)" are the strongest external statement that the off-diagonal /
   coherent structure the twin preserves is operationally consequential — aligns with our located
   bunching/heterogeneity (M3 per-window R̂; `metric_results.md`).

## Open questions / how to use [twin]
- (i) Is **GCAMPS [21] / the Nakhl stabilizer-TN [22]** open-source and reusable as the forward
  engine, or do we implement a differentiable stabilizer-TN ourselves (Clifford tableau via Stim,
  MPS in torch)?
- (ii) Differentiating through SVD truncation at fixed χ — gradient stability + the θ→MPS path.
- (iii) χ vs accuracy envelope for our `(θ ≈ 10⁻³, p ≈ 0.01, d = 3)` regime (likely χ ≪ 32; theirs
  was d = 9).
- (iv) Pixel-extract the 6 figures (exact LER curves / threshold crossings) only if we need their
  quantitative numbers for comparison — the qualitative results + the text numbers are captured above.
- **Trust:** high for the method, model, and stated numbers (full text read); figure curves not
  pixel-level.

## Related-work cluster [paper refs]
Bravyi–Englbrecht–König–Peard, coherent errors + surface codes, npj QI 4, 55 (2018) [11]
(`correcting_coherent_errors_surface_1710.02270.md`); Darmawan–Poulin, TN surface under realistic
noise, PRL 119, 040502 (2017) [12]; Zhou–Ji–Ding, crosstalk (incoherent), arXiv:2503.04642 [13];
Behrends–Béri, surface code beyond Pauli, PRX Quantum 6, 040350 (2025) [15]; Katabarwa–Geller, LER in
the PTA, Sci. Rep. 5, 14670 (2015) [14]. Overview hub:
`2026-06-14_coherent_noise_and_neural_decoders.md`.
