# Full-text review — Pataki, Márton, Asbóth & Pályi, "Coherent errors in stabilizer codes caused by quasistatic phase damping" (arXiv:2401.04530v3; PRA 110, 012417 (2024))

> **Provenance (2026-07-02): FULL-TEXT read (精读).** Cached full text
> `outputs/papers/2401.04530.txt` (WSL path; also reachable as
> `\\wsl.localhost\ubuntu-f\home\cx\Document\AI_QEC\AI_QEC\outputs\papers\2401.04530.txt`),
> 15 pp, read end-to-end incl. Appendix A (Table I) and reference list. All §/Eq/Fig/Table refs are from
> that text; the plotted threshold/LER curves (Figs. 2, 4, 5, 6) are not pixel-extracted — the load-bearing
> NUMBERS quoted here are those stated in the running text + Table I. **Authored by opus subagent 2026-07-02;
> pending principal spot-verification.** Tags: **[paper]** = stated in the paper; **[twin]** = our
> application/inference for `qec_twin`, NOT the paper's claim.

## Metadata [paper]
- **Authors / affiliation.** Dávid Pataki, Áron Márton, János K. Asbóth, András Pályi (BME Budapest;
  HUN-REN Wigner RCP; HUN-REN–BME Quantum Dynamics & Correlations group). Same Márton–Asbóth line as the
  FLO coherent+readout paper [ref 18, Quantum 7, 1116 (2023)] whose simulator this work reuses.
- **Venue / status.** arXiv:2401.04530v3 [quant-ph], 18 Jul 2024; published PRA 110, 012417 (2024). 11 pp
  body + acknowledgments + Appendix A + refs.
- **Type.** Analytic derivation (rep code, general Pauli stabilizer codes) + classical **forward simulation**
  of the rotated surface code under a random-coherent-error model, using **Fermionic Linear Optics (FLO)**
  [refs 16–18] with **phenomenological readout errors** [ref 18] and 3-D MWPM/PyMatching decoding.

## Executive summary [paper]
Introduces **quasistatic phase damping (QPD)**: each data qubit suffers a coherent Z-rotation `e^{iθ_j Ẑ_j}`
with `θ_j` drawn i.i.d. Gaussian `N(0,σ²)`, **constant across all cycles within one shot, resampled shot to
shot** (the two senses of "quasistatic"). Physically motivates it as the 1/f-noise / Larmor-frequency-drift
error of idling spin qubits and dephasing-limited superconducting qubits. Main results:
- **Single cycle ⇒ QPD ≡ independent phase-flip.** For ONE cycle of detection (or correction), on ANY Pauli
  stabilizer code, the shot-averaged QPD channel is EXACTLY an independent per-qubit phase-flip channel with
  `p = ⟨sin²θ⟩ = ½(1−e^{−2σ²})` (Eqs. 12, 35–36). Proven, all code sizes.
- **Multiple cycles ⇒ distinct.** Because `θ_j` does NOT change between cycles, the shot-averaged multi-cycle
  channel is still Pauli-diagonal but is a **CORRELATED Pauli channel** — provably NOT reproducible by
  independent homogeneous phase flips at the same `p` (the 2-cycle rep code needs 4 distinct coefficients vs
  3 for the i.i.d. model; §III B, Eqs. 21 vs 22).
- **Logical-level decoherence is EXACT for all code sizes.** After correction, a coherent physical Z-error
  maps to a coherent LOGICAL Z-error `e^{iθ_L Ẑ_L}` (Eq. 49); averaging over the angle distribution
  decoheres the logical qubit into a Pauli-Z channel EXACTLY (not asymptotically) — sharper than the generic
  "stabilizer measurement asymptotically decoheres noise" of Beale et al. [ref 20].
- **Surface-code threshold** (QPD + readout, FLO sim, d up to 17): `p_th ≈ 2.85%` for `p=q`, essentially the
  same as the Pauli-phase-flip+readout threshold, but with a LOWER logical error rate AT threshold (`p_L≈7%`
  for QPD vs `≈8.5%` for Pauli) ⇒ QPD is *less harmful* than the matched i.i.d. phase-flip model for surface
  memory. Full (p,q) threshold phase diagram given (Fig. 5).
- **d=3 leading order** (look-up-table MWPM, `q=p`, 3 rounds): `p_L^{(d=3)} ≈ 118 p²` — *identical* to the
  independent-phase-flip+readout result at leading order. Break-even (`p_L<p`) needs `p ≲ 1%`, tolerating
  `q` up to ~6% (Fig. 6). Connected to spin-qubit hardware via `σ = √2 T_meas/T₂*`.

## Error model (§II, Eq 1) — the mechanism [paper]
`Û = ∏_{j=1}^n e^{iθ_j Ẑ_j}` (Eq. 1), `θ_j ~ N(0,σ²)` i.i.d. across qubits and shots, `−π<θ≤π`. Two defining
properties (**"quasistatic"**): (i) `θ_j` fixed for all cycles WITHIN a shot; (ii) resampled between shots.
Derivations only require the angle distribution be **symmetric with zero mean** (Eq. 29) — Gaussian is the
concrete choice. Coherent errors act on **data qubits only** (idle/dephasing error); readout is handled
separately and phenomenologically.

### ⚠ A9-load-bearing: "correlated is beyond scope" — the (b)-anchor verbatim [paper]
The paper is explicit and repeated that spatial/temporal CORRELATION of the angles is NOT modeled — the
angles are i.i.d. per qubit. This is the exact sentence our prereg A9 leans on to classify our correlated
result as `(a)/(b)` prior-vs-novel:
- **(§II, p.2, verbatim):** *"We also note that the simulation method we use to treat this error model in
  this work generalizes in a straightforward way to more complicated angle distributions, including
  spatially and temporally correlated ones; that extension is beyond the scope of this work."*
- **(§II, p.2–3, verbatim, the independence assumption):** *"A further assumption of our model is the
  statistical independence of the local random components of the Larmor frequencies, which is realistic if
  the Larmor frequency fluctuations are caused by local noise sources … We note that the numerical methods
  applied in this work are directly generalizable to variants of our noise model with more complex temporal
  and spatial correlations, which is in fact an interesting direction for future research."*
- Reinforced in the abstract/intro: angles are "statistically independent" for different qubits and shots
  (§II, Eq. 9 factorizes `f(θ_A,θ_B)=f(θ_A)f(θ_B)`).

⇒ **QPD is a purely PER-QUBIT, spatially/temporally UNcorrelated coherent model.** Every result below is
under that independence assumption.

## Single-cycle equivalence (§III A, §IV A) [paper]
- **Rep-code single cycle (Eqs. 10, 12–13):** trivial-syndrome (`s=+1`) post-measurement state under QPD is
  `ρ̂_{1,coh}(+1) = ⟨cos²θ⟩² ρ̂₀ + ⟨sin²θ⟩² Ẑ_L ρ̂₀ Ẑ_L`, IDENTICAL to the i.i.d. phase-flip result
  `ρ̂_{1,p}(+1)=(1−p)²ρ̂₀+p² Ẑ_L ρ̂₀ Ẑ_L` when `p = ⟨sin²θ⟩ = ½(1−e^{−2σ²})` (Eq. 12). Same for `s=−1`.
- **General Pauli stabilizer code, single cycle (Eqs. 30–37).** Write `Û=Σ_Ê A_θ(Ê)Ê` with
  `A_θ(Ê)=∏_j (cosθ_j)^{1−n_Ê(j)}(i sinθ_j)^{n_Ê(j)}` (Eq. 32). Averaging kills cross terms
  (`⟨A_θ(Ê)A*_θ(Ê')⟩ = δ_{Ê,Ê'} ⟨|A_θ(Ê)|²⟩ ≡ P(Ê)`, Eq. 33) because odd powers of `i sinθ_j` vanish
  under the symmetric distribution; the stabilizer commutation identity `Π̂_s Ê = Ê Π̂_0` for `Ê∈D_s`
  (Eq. 34) then gives `ρ̂₁(s)=Σ_{Ê∈D_s} P(Ê) Ê ρ̂₀ Ê` (Eq. 35) with
  `P(Ê)=∏_j ⟨cos²θ_j⟩^{1−n_Ê(j)} ⟨sin²θ_j⟩^{n_Ê(j)}` (Eq. 36) — **an independent per-qubit phase-flip
  channel, `p=⟨sin²θ_j⟩`, for every syndrome.** Holds for error correction too (Eq. 37).

## Multi-cycle correlated Pauli channel + the trivial-syndrome logical channel (§III B, §IV B) — the (b)-mechanism [paper]
- **Multi-cycle structure (Eqs. 38–44).** `t` cycles: `2^{tn}` cycle-resolved scenarios `E=(Ê₁,…,Ê_t)`,
  merged operator `Ê(E)=∏_r Ê_r`. The averaged state is Pauli-diagonal (Eq. 39) but the intermediate
  weights `P̃(E)` (Eq. 41) can be NEGATIVE (they are quasiprobabilities summing to 1) — real because
  odd-in-`i sinθ_j` terms cancel. Redistributing within each `(s,α)` class gives a genuine but **HIGHLY
  CORRELATED (nonlocal in space+time)** physical Pauli channel (Eqs. 44–48); whether a LOCAL-in-space-time
  correlated representation exists is left as *"an open question … beyond the scope of this work"* (§IV B).
- **The trivial-syndrome / syndrome-independent LOGICAL-Z channel — Eq. 44 (`Ẑ_α` term):** after `t`
  cycles the code state is
  `ρ̂_t(s) = Σ_α P̃_α(s) Ẑ_α Ê_s ρ̂₀ Ê_s Ẑ_α`, with `Ẑ_α=(Ẑ_1^L)^{α₁}…(Ẑ_k^L)^{α_k}` (Eqs. 44–46). The
  `Ẑ_α` factor is a residual LOGICAL phase-flip applied ON TOP of any syndrome-inferred correction `Ê_s` —
  i.e. an **undetectable, syndrome-outcome-independent logical-Z decoherence** (for the single-logical-qubit
  rep-code it is exactly the `c̃_s, d̃_s` split of Eq. 22, e.g. `c̃_{++}=P̃_0(++)`, `d̃_{++}=P̃_1(++)`).
  For the surface code this is made exact by Eq. 49 below.
  - **Note on wording:** the paper does not use the phrase *"acts independently of syndrome outcomes"*
    verbatim; the equivalent stated fact is that the logical rotation `θ_L=θ_L(s,θ)` and the residual
    `Ẑ_α` decoherence are functions of the syndrome+decoder but the resulting per-syndrome logical channel
    is a bona-fide Pauli-Z channel (`P̃_α(s)≥0`, Eq. 47) **for every syndrome including the trivial one** —
    the logical decoherence is not removable by decoding. [twin-flag: our A9 (b) paraphrases this as a
    "trivial-syndrome channel for INDEPENDENT noise"; that paraphrase is faithful to Eqs. 44–49, but the
    exact quoted string does not exist — cite Eq. 44 / Eq. 49, not a quotation.]
- **2-cycle rep-code closed forms (Eqs. 21 vs 22) — the counterexample.**
  i.i.d.: `c_{++}=(1−p)⁴+p⁴`, `d_{++}=c_{−+}=d_{−+}=2p²(1−p)²`,
  `c_{+−}=d_{+−}=c_{−−}=d_{−−}=p(1−p)³+p³(1−p)` (Eq. 21).
  QPD: `c̃_{++}=1/16(e^{−16σ²}+2e^{−8σ²}+8e^{−4σ²}+5)`, `d̃_{++}=d̃_{−+}=1/16(1−e^{−8σ²})²`,
  `c̃_{−+}=1/16(e^{−16σ²}+2e^{−8σ²}−8e^{−4σ²}+5)`, `c̃_{+−}=d̃_{+−}=c̃_{−−}=d̃_{−−}=1/16(1−e^{−16σ²})`
  (Eq. 22). Full 16-scenario `P(E)` vs `P̃(E)` table = Appendix A Table I.
- **Best i.i.d. Pauli approximation (§III B 3, Eqs. 23–25).** TVD `δ(p,σ)=max_s max(|c_s−c̃_s|,|d_s−d̃_s|)`;
  small-σ: `p_best(σ)≈σ²`, `δ(p_best,σ)≈6σ⁴` (Eq. 25); grows to ~10% at σ=0.5 (Fig. 2). So the i.i.d.
  approximation error is `O(σ⁴)` — small but nonzero, and the whole point that multi-cycle QPD ≠ i.i.d.

## The `p=⟨sin²θ⟩` calibration formula (Eq. 12) and OUR χ convention [twin]
**Their convention.** Angle SD is `σ`; per-cycle equivalent phase-flip probability is
`p = ⟨sin²θ⟩ = ½(1 − e^{−2σ²})` (Eq. 12), from `⟨sin²θ⟩=½(1−⟨cos2θ⟩)` and the Gaussian characteristic
function `⟨cos2θ⟩=e^{−2σ²}`. Small-angle: `p≈σ²` (and `p_best≈σ²`, Eq. 25). Threshold/LER plots use `p` (or
`σ`) as the physical-error axis; hardware link `σ(T_meas)=√2 T_meas/T₂*` (Eq. 58).

**Relation to our step-2 calibration (our χ convention).** Our teacher/carrier parametrizes a coherent
Z-dephasing by a rotation angle we call `χ` (per-cycle coherent Z half-angle, i.e. the analogue of `θ_j`).
The **exact map** between conventions, assuming a matched Gaussian coherent-Z model with our `χ` playing the
role of a single realization of `θ_j`:
- If our `χ` is a *fixed* per-cycle rotation (deterministic overrotation), the induced per-cycle Pauli-Z
  marginal is `p = sin²χ` (their Eq. 50 logical form / Eq. 32 amplitude, single-qubit case).
- If our `χ` is Gaussian with SD `σ_χ` (the QPD case), then `p = ½(1−e^{−2σ_χ²})` — our `σ_χ ≡ σ` and our
  calibration target `p` is **their Eq. 12 verbatim**. So our step-2 label-free calibration, which fits the
  per-(round,stabilizer) Pauli-Z marginal `p`, is fitting exactly `½(1−e^{−2σ²})`; recovering the coherent
  strength is `σ = √(−½ ln(1−2p))` (invert Eq. 12), valid for `p<½`.
- ⚠ **Identifiability caveat (matches our repo finding `project-coherence-not-identifiable-syndrome-only`).**
  Eq. 12 is a SINGLE-cycle identity; it says the marginal `p` alone cannot distinguish QPD from i.i.d.
  phase-flip in one cycle. The coherent SIGNATURE lives only in the MULTI-cycle correlated coefficients
  (Eqs. 22, 44) — i.e. exactly the part our binary-syndrome data is nearly blind to. Carry this: `p` fixes
  `σ` under the Gaussian-QPD *assumption*, but the assumption itself (coherent vs stochastic) is what the
  multi-cycle correlations, not `p`, would test.

## Surface-code numerical results (§V, §VI) [paper]
- **Method:** FLO simulator of Márton–Asbóth [refs 16–18] (Majorana-fermion representation; efficient for
  coherent Z + Clifford), + phenomenological readout `q` (Eq. 51), 3-D MWPM/PyMatching over `d` rounds with
  spacelike/timelike edge weights `w_s=log((1−p)/p)`, `w_t=log((1−q)/q)` (Eq. 54), last round readout-clean.
  LER = maximum infidelity `p_L(s,θ)=sin²θ_L` averaged over syndromes + angle distribution (Eqs. 50, 55–56).
- **Threshold (`p=q`, Fig. 4):** `p_th ≈ 2.85%` (d=7..17); close to toric-code Pauli-Z+readout `2.93±0.02%`
  [ref 12]. At threshold `p_L≈7%` (QPD) vs `≈8.5%` (Pauli phase-flip+readout) — QPD lower, difference
  sustained across the window. Sampling: `N_sample=10⁴·d·100` per point.
- **(p,q) phase diagram (Fig. 5):** at `p≈1%` the code is scalable even for `q≈8%`; at `q≈1%` it needs
  `p ≲ 4%`. Coherent errors are consistently MORE harmful than readout errors.
- **d=3 (§VI, Eq. 57):** `p_L^{(d=3)} ≈ 118 p²` (LUT-MWPM, `q=p`, 3 rounds) — **identical leading order for
  QPD and for independent phase-flip+readout**; break-even `p_L<p` needs `p≲1%`, tolerating `q` up to ~6%
  (Fig. 6). Spin-qubit hardware curve (Ref. 51 readout data, `T₂*=10 µs`, `q(T_meas)≈(τ/T_meas)⁵`,
  `τ=0.21µs`) lies inside break-even.

## What they do NOT do (scope boundaries) [paper]
1. **No CORRELATED angles.** Spatial or temporal correlation of `θ_j` is explicitly out of scope (§II,
   quoted above) — the whole paper is i.i.d.-per-qubit. (This is THE gap our correlated work occupies.)
2. **No moment ratios / no double-factorial enhancement.** They give exact 2-cycle coefficients but do not
   study how the correlated-vs-independent logical-error *ratio* scales with `d` (that is Clader et al.
   arXiv:2101.11631 / our A9 (a)). QPD being i.i.d., there is no common-mode `d!!` growth to report.
3. **No detection-event rate as an observable.** Detectors enter only through the decoder; they never report
   detection density, and certainly not a detection-rate *decrease* under correlation (our A9 (c) headline).
   No syndrome-silent-RUN rate is isolated.
4. **No non-Z / no leakage / no depolarizing.** X,Y and depolarizing are out of scope by FLO constraint
   (§VII: *"including random Pauli X and Y errors … is unfortunately beyond the scope of our approach, due
   to the constraints of the FLO simulation"*). Readout is phenomenological (perfect measurement, flipped
   outcome) — no soft/analog readout, no mid-circuit measurement-back-action model.
5. **No drift/estimation, no per-cycle rate variation.** `σ` is a fixed model parameter per run; there is no
   time-varying rate, no adaptive estimation (that axis = Bhardwaj 2511.09491 in our notes). "Quasistatic"
   here means *constant within a shot*, the opposite of drift.

## Limitations [paper]
- **L1 — FLO-restricted noise.** Only coherent Z-rotations + Clifford + phenomenological readout; no X/Y,
  no depolarizing, no leakage/relaxation (T₁ excluded — §VI notes transmons are T₁-limited, so QPD is the
  *wrong* model for standard transmons and the *right* one only for dephasing-limited qubits).
- **L2 — phenomenological readout.** Perfect projective measurement with classically flipped outcome (Eq.
  51); not a physical measurement channel.
- **L3 — i.i.d. angles only** (the scope quote); correlated variants deferred as "interesting future work".
- **L4 — d=3 analytic result uses a LUT decoder with equal space/time weights** (`w_s=w_t`), a special case
  of the general Eq. 54 weighting.
- **L5 — surface-code numbers are for `p=q` on the main threshold; the small-`p` (deep sub-threshold) regime
  is stated to be sampling-limited** ("could only provide accurate results by significantly increasing the
  number of samples which is not feasible", §VI).

## Relevance to the twin — the (b)-anchor for A9 (trivial-syndrome logical channel under INDEPENDENT noise) [twin]
1. **This is the `(b)` "folklore-unquantified" anchor cited verbatim in prereg A9** (`B_syndrome_shot_bridge_prereg.md`,
   line 214): *"collective flip = logical operator ⇒ zero syndrome (2401.04530 exhibits a trivial-syndrome
   channel for INDEPENDENT noise …)."* The mechanism is Eqs. 44 + 49: a **syndrome-outcome-independent,
   undetectable logical-Z decoherence `Ẑ_α`** that survives any correction — the "syndrome looks fine, the
   logical qubit has silently dephased" phenomenon. **Crucially the paper establishes this for i.i.d.
   per-qubit noise** (their whole model). ⇒ our contribution is NOT the existence of a syndrome-silent
   logical channel (Pataki et al. already exhibit it); it is the **CORRELATION AMPLIFICATION** of its rate
   (the ×15.9 moment law, Clader/A9 (a)) **and the detection-rate scissors** (A9 (c)), neither of which
   appears here.
2. **"logical-level decoherence is EXACT for all code sizes" — the condition.** Their sharper-than-generic
   claim (vs Beale et al. [20] asymptotic) holds under: (i) coherent Z-only physical noise; (ii) a symmetric,
   zero-mean angle distribution (Eq. 29) — Gaussian is sufficient but not necessary; (iii) the stabilizer
   commutation identity Eq. 34 (any Pauli stabilizer code). Under these, the shot-averaged logical channel is
   *exactly* Pauli-Z (Eq. 44, `P̃_α(s)≥0`), not merely asymptotically. Our carrier's coherent-Z teacher
   satisfies (i)–(iii), so this exactness transfers to our setting as a THEOREM-grade fact we may cite
   (epistemic class (a)).
3. **Calibration bridge (step-2).** Eq. 12 `p=½(1−e^{−2σ²})` is exactly our step-2 marginal-calibration
   target under a Gaussian coherent-Z model; the σ↔p↔χ map above is the convention-carry METRICS.md
   requires. But Eq. 12 is single-cycle: it is precisely the statement that the marginal cannot see coherence
   — consistent with `project-coherence-not-identifiable-syndrome-only`. Use it to *convert* a fitted `p` to
   `σ`, never to *claim* coherence was identified.
4. **Sharpens our claim discipline.** Their `p_L^{(d=3)}≈118p²` being IDENTICAL for QPD and i.i.d. phase-flip
   at leading order (Eq. 57), and their surface threshold being essentially unchanged, is a concrete warning:
   **at the LER/threshold level, single-qubit coherent-Z randomness is nearly indistinguishable from
   stochastic phase-flip.** Any headroom claim for coherence must come from the multi-cycle CORRELATED
   structure (Eqs. 22, 44) or from richer probes — never from LER alone. This is the same lesson as our
   decoder-gate/Bayes-floor program.
5. **A9 positioning is CONSISTENT — no contradiction found.** Prereg A9 already classifies this paper
   correctly as `(b)` (trivial-syndrome channel exhibited, for independent noise). Nothing in the full text
   contradicts that. Two precision notes to carry into the writeup: (i) the phrase *"acts independently of
   syndrome outcomes"* is a faithful paraphrase but NOT a verbatim quote — cite Eqs. 44/49; (ii) the paper's
   "correlated is beyond scope" (§II) is the clean verbatim justification for our `(a)/(b)` split and should
   be quoted directly. The A9 reading debt lists 2401.04530 as a "body-read"/精读 target — this note
   discharges the 精读.

## How to use / trust + open questions [twin]
- **Trust:** high. Analytic core (Eqs. 12, 22, 35–36, 44) is exact and self-contained (Table I gives the full
  2-cycle ledger); the surface-code numbers rest on the peer-reviewed FLO simulator [refs 16–18] and standard
  MWPM. Independent-oracle status: the single-cycle equivalence (Eq. 12) and the 2-cycle coefficients (Eqs.
  21–22) are closed-form and could be re-derived from scratch as a cross-check for our coherent-Z teacher
  (a good FAITHFULNESS_PROTOCOL independent-GT candidate at d=2, 2 cycles).
- **Open for us:** (i) our result must be framed as *correlated* QPD — the exact extension the authors flag as
  future work; the differentiator is spatial (Clader `d!!`) + circuit-level detection-rate behavior, not the
  syndrome-silent channel per se. (ii) The convention map σ↔p↔χ (item 3) should be committed alongside our
  step-2 numbers. (iii) Their negative-quasiprobability multi-cycle representation (Eqs. 41–48) is a useful
  formal template for how coherent multi-cycle correlations enter a Pauli-diagonal channel — relevant if we
  ever express our carrier's coherent teacher in a cycle-resolved Pauli-quasiprobability form.
