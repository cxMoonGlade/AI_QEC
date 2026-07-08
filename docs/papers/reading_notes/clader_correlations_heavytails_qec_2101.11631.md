# Full-text review — Clader, Trout, Barnes, Schultz, Quiroz & Titum, "Impact of correlations and heavy-tails on quantum error correction" (arXiv:2101.11631v2, PRA 103, 052428, 2021)

> **Provenance (2026-07-02): FULL-TEXT read (精读).** Cached text
> `outputs/papers/2101.11631.txt` (10 pp incl. refs; arXiv:2101.11631v2 [quant-ph],
> dated 25 May 2021; published as Phys. Rev. A **103**, 052428 (2021)). All §/Eq/Fig
> refs are from that text; the 5 figures' plotted curves are NOT pixel-extracted — the
> analytic formulae, Table I entries, and the running-text numbers are captured verbatim
> here. **Note authored by opus subagent (2026-07-02); load-bearing claims pending
> principal spot-verification.** Tags: **[paper]** = stated in the paper; **[ours]** =
> our application/inference for `qec_twin`, NOT the paper's claim.

## Metadata [paper]
- **Authors / affiliation.** B.D. Clader, Colin J. Trout, Jeff P. Barnes, Kevin Schultz,
  Gregory Quiroz, Paraj Titum — all **Johns Hopkins University Applied Physics Laboratory**
  (JHU/APL), Laurel MD. Corresponding: dave.clader@jhuapl.edu.
- **Venue / status.** PRA 103, 052428 (2021); arXiv:2101.11631v2, 25 May 2021. 8 pp body
  + refs (no appendices; the analytics are all in the main text §II).
- **Type.** Analytic **code-capacity** derivation (§II) + **state-vector circuit-level
  numerics** on a d=3 rotated surface code (§III). Noise = **coherent single-qubit
  rotation errors** with random angles from Gaussian / Student-t / Lévy α-stable
  distributions; the lever is **heavy tails × correlation** (spatial in the analytics,
  temporal in the numerics). Decoding is by perfect-code assumption (analytics) or an
  unspecified surface-code decoder + perfect correction (numerics). Prior companion:
  Barnes, Trout, Lucarelli, Clader, PRA 95, 062338 (2017) [ref 76] (same sim framework).

## Executive summary [paper]
The single result: **spatially- or temporally-correlated *coherent* single-qubit
rotation errors, when the rotation angle is drawn from a heavy-tailed distribution,
generate high-weight errors that reduce the effective code distance — down to d_eff=1
(no protection at all) for correlated Cauchy noise.** The mechanism is weight-one
*generators* producing high-weight *errors* through correlation, and the severity is set
by the **tail index**, not by any spatial/temporal coupling range. Structure of the argument:
- **Gaussian (light tail) correlated noise is benign for the distance** — LER still
  scales as σ^{2(w+1)} = σ^{d+1} (Eq 7 region), i.e. the code behaves as its nominal
  distance; correlation only inflates the *leading coefficient*, and that inflation grows
  as **d!! (double factorial)** with distance (Fig 1: 3, 15, 105, 945, 10 395, 135 135,
  2 027 025 for d=3…15). So Gaussian correlations are a coefficient penalty, never a
  distance loss.
- **Cauchy (ν=1 Student-t / α=1 Lévy) correlated noise kills the code** — effective
  distance → 1 for every code distance considered (conjectured for all d); logical
  infidelity ∝ physical infidelity (slope 1), no suppression.
- **Student-t interpolates by the odd integer ν=2r−1**: the code recovers its full
  distance only once **d ≤ 2r−3** (equivalently the distance loss sets in for **d > 2r−3**),
  and the max σ-exponent for correlated noise is **2r−1** (Table I).
- **Lévy α-stable interpolates continuously via α∈(0,2]**: for **any α<2** the correlated
  LER has a term ∝ σ^α ∝ P_ph (no protection, all d); **only exactly α=2 (Gaussian)**
  restores σ^{2α} suppression (Fig 2).
- **Time-correlation numerics (SchWARMA, d=3 surface code)** reproduce the same story:
  DC (infinite-time-correlation) heavy-tailed noise → slope-1 logical/physical infidelity;
  white (uncorrelated-in-time) heavy-tailed noise → protected; intermediate correlation
  (EMA half-life T_h) interpolates, with the slope degrading as T_h approaches the
  syndrome-cycle length (Figs 3–5).

## The noise model — EXACT form (§II, Eqs 1–2) [paper]
**Code-capacity coherent-rotation model (§II, Eq 1).** Start from a perfectly encoded
n-qubit logical state |ψ_L⟩. Apply a single-qubit rotation about an **arbitrary but common
axis** v̂ to **all data qubits**:

  |ψ_L⟩ → Π_{j=1}^n [ cos(θ_j/2) Î − i sin(θ_j/2) v̂·σ̂^(j) ] |ψ_L⟩   (Eq 1)

with v̂ a fixed real unit 3-vector (rotation direction, **same for all qubits**), σ̂^(j)
the Pauli 3-vector on qubit j, θ_j the per-qubit rotation angle.

- **This is a COHERENT unitary rotation, NOT classical dephasing.** Each qubit gets a
  genuine SU(2) rotation exp(−i (θ_j/2) v̂·σ) with a *random* angle. It is the
  "semiclassical system-bath" model — the bath is a classical random variable inside the
  Hamiltonian (p. 1, "The errors are modeled as classical random variables within the
  Hamiltonian… semi-classical system bath model"). Assumptions stated (p. 2): bath in
  thermal equilibrium, no back-action, infinite temperature (equal-population long-time
  decay) — "These assumptions apply directly to classical noise from the classical control
  system." So it is coherent rotation with a **stochastic (classically-random) angle**;
  averaging over the angle distribution produces the decoherence.
- **Independent (uncorrelated) case:** each θ_j is drawn **independently** from the
  distribution — n i.i.d. random variables. Physically = local/independent errors.
- **Correlated case (EXACT wording, p. 2):** *"we assume that a single angle is drawn
  from the same probability distribution and applied to each qubit."* i.e. **θ_j ≡ θ, one
  common random draw, identical on every qubit** — perfect (rank-1, fully collinear)
  correlation, the maximally-correlated limit. This is a **common-mode coherent rotation**
  (all qubits rotate by the same random angle about the same axis). Physically = a
  spatially-correlated error (common bath / shared control line).
- **Axis note.** The analytic axis v̂ is arbitrary; the numerics (§III) fix it to **Y**
  (U = exp(−iθ σ_y), a Y-rotation — a coherent X↔Z mixing, not a pure Z-dephasing).

**Logical-error probabilities (Eq 2), perfect-code assumption.** The code corrects all
Pauli errors up to weight w=(d−1)/2. Averaging the surviving weight over the angle
distribution ⟨·⟩:

  P_unc = 1 − Σ_{k=0}^{w} C(n,k) ⟨cos²(θ/2)⟩^{n−k} ⟨sin²(θ/2)⟩^{k}          (Eq 2a)
  P_cor = 1 − Σ_{k=0}^{w} C(n,k) ⟨cos^{2(n−k)}(θ/2) sin^{2k}(θ/2)⟩          (Eq 2b)

— **the ONLY difference is where the ensemble average sits**: Eq 2a averages each qubit's
cos²/sin² *independently* (product of averages, because the angles are independent),
Eq 2b averages the *whole product jointly* (one shared angle θ). That single
independent-vs-joint-average distinction is the entire correlation effect.

**Characteristic-function forms (Eq 3).** After algebra (assuming distributions symmetric
about 0, f(t)=f(−t)):

  P_unc = 1 − (1/2^n) Σ_{k=0}^{w} Σ_{l=0}^{n−k} Σ_{m=0}^{k} C(n,k)C(n−k,l)C(k,m) (−1)^{m−k} f(t=1)^{n−l−m}   (Eq 3a)
  P_cor = 1 − (1/2^{2n}) Σ_{k=0}^{w} Σ_{l=0}^{2(n−k)} Σ_{m=0}^{2k} C(n,k)C(2(n−k),l)C(2k,m) (−1)^{m−k} f(t = n−l−m)   (Eq 3b)

where **f(t) is the characteristic function** of the angle distribution. Key structural
point: Eq 3a only ever needs f(t=1); Eq 3b needs f evaluated at integer arguments up to
t=n — so the correlated LER probes the **high-t (small-scale / tail) behavior** of f,
which is exactly where heavy tails differ.

**Physical (single-qubit) failure prob.** P = sin²(θ/2) (Eq 4); ⟨P⟩ ≡ P_ph = ½[1 − f(t=1)]
(Eq 5). **Convention:** "failure" = getting a bit-flip OR phase-flip on measurement.
**Qubit count convention:** n set to the Knill–Laflamme bound **n = 4w+1** (minimum
perfect-code size) throughout unless stated (p. 3, p. 4 Table I caption).

## Findings + numbers — VERBATIM (§II.A–C, Table I, Figs 1–2) [paper]

### Gaussian (§II.A, Eq 6–7, Fig 1)
- Characteristic function f(t;σ) = exp(−½ σ² t²)   (Eq 6).
- Both P_unc and P_cor scale as **σ^{2(w+1)}** (w = correctable weight, d=2w+1) — Gaussian
  correlated noise does **NOT** reduce code distance; it only changes the series coefficient
  (p. 3).
- **d=3 leading terms (σ≪1), Eq 7 — verbatim:**
  - **P_ph ≈ σ²/4**
  - **P_unc ≈ 5σ⁴/8**
  - **P_cor ≈ 15σ⁴/8**
  ⇒ the correlated pre-factor is **3× the uncorrelated** at d=3 (15/8 ÷ 5/8 = 3), both
  still σ⁴ (quadratic-in-P suppression, as a d=3 code should).
- **Fig 1 — the d!! ratio series.** Fig 1 plots **P_cor/P_unc of the leading-order term in
  σ** for correlated vs uncorrelated Gaussian noise (σ≪1), vs distance d = 3,5,7,9,11,13,15.
  The plotted/labelled ratio values are:

    d :   3     5      7       9        11         13          15
    P_cor/P_unc : 3,   15,   105,    945,    10 395,   135 135,   2 027 025

  Caption: *"As the code distance increases, the ratio increases as d!!"* — i.e. the ratio
  is the **double factorial d!!** (3=3!!, 15=5!!, 105=7!!, 945=9!!, 10395=11!!, 135135=13!!,
  2027025=15!!). So for correlated Gaussian noise the LER leading coefficient is inflated by
  d!! relative to uncorrelated, but the σ-*power* (distance) is unchanged.
  - **Caveat stated (p. 3–4):** the σ→0 expansion of Eq 2 "must be done with care" — valid
    only for **σ ≪ (1/d!!)^{2/(d+1)}** because the binomial term count grows with d. Agrees
    with prior work [ref 14] that a *threshold* does not exist, but a **pseudo-threshold**
    exists per distance.

### Student-t (§II.B, Eq 8–9, Table I)
- PDF_t(θ;ν,σ) = (νσ²)^{ν/2} Γ((ν+1)/2) / [√π Γ(ν/2)] · 1/(νσ²+θ²)^{(ν+1)/2}   (Eq 8);
  ν≥1 integer = degrees of freedom (tail heaviness). **ν=1 = exactly the Cauchy
  distribution**; ν→∞ = Gaussian. Analytics restricted to **odd ν, written ν=2r−1, r≥1**.
- Characteristic function f(t;σ,ν) = [σ^{ν/2} ν^{ν/4} |t|^{ν/2} / (2^{ν/2−1} Γ(ν/2))]
  K_{ν/2}(σ√ν |t|)   (Eq 9), K_n = modified Bessel of the 2nd kind.
- **Correlated Cauchy (r=1, ν=1): NO error suppression — effective code distance reduced
  to 1 for ALL code distances considered; conjectured to hold for arbitrary d** (p. 4).
  ⇒ correlated single-qubit rotations with Cauchy angles produce **at least weight
  (d+1)/2 errors**.
- **The distance-loss rule (verbatim, p. 4 + Table I caption):** *"when the distance is
  d ≤ 2r−3 … the effective distance of the QEC is equivalent for the correlated and
  uncorrelated cases. However, once d > 2r−3 the effective distance begins to be reduced
  for correlated noise, with the maximum exponent on σ appearing to be 2r−1 for correlated
  noise."* Worked example (caption): **d=3 at r=3 → effective distances are equal** for
  unc/cor (3 ≤ 2·3−3 = 3).
- **Table I** (leading σ≪1 term of the failure probability; n=4w+1) tabulates Physical +
  Unc/Cor for d=3,5,7,9 across r=1…6. Representative verbatim entries:
  - **r=1 (Cauchy):** Physical = **σ/2**; d=3 Unc = (5/2)σ², Cor = (35/64)σ; d=5 Unc =
    (21/2)σ³, Cor = (9009/16384)σ; d=7 Unc = (715/16)σ⁴, Cor = (1154725/2097152)σ; d=9 Unc =
    (1547/8)σ⁵, Cor = (591534125/1073741824)σ. **⇒ every correlated column is ∝ σ¹**
    (d_eff=1) regardless of d, while the uncorrelated column scales as σ^{(d+1)/2}.
  - **r=2 (ν=3):** Physical = (3/4)σ²; d=3 Unc = (45/8)σ⁴, Cor = (175√3/64)σ³; correlated
    max exponent 2r−1 = 3.
  - **r=3 (ν=5):** Physical = (12)σ²… ; d=3 Unc = (125/72)σ⁴, **Cor = (125/8)σ⁴** — first
    row where d=3 correlated is back to σ⁴ (d_eff restored, matching d ≤ 2r−3 = 3).
  - Pattern across the table: as r grows the correlated column's σ-power climbs toward the
    nominal σ^{(d+1)/2}, distance-by-distance, exactly at the d = 2r−3 boundary.

### Lévy α-stable (§II.C, Eq 10–11, Fig 2)
- Characteristic function (skew=loc=0): f(t;σ,α) = exp(−|σ t|^α)   (Eq 10); α∈(0,2];
  **α=2 = Gaussian, α=1 = Cauchy**; continuous interpolation. (Stable ⇒ usable for the
  time-correlation numerics via SchWARMA.)
- **d=3 leading terms (σ≪1), Eq 11 — verbatim:**
  - **P_ph ≈ σ^α / 2**
  - **P_unc ≈ 5 σ^{2α} / 2**
  - **P_cor ≈ (1/128)[5·2^{α+2} − 5·3^α − 5·4^α − 5^α + 70] σ^α
             + (1/256)[5·(−4^{α+1} + 9^α + 16^α − 14) + 25^α] σ^{2α}**
  ⇒ correlated LER has a **σ^α term ∝ P_ph** for any α<2; the σ^α coefficient vanishes
  **only at exactly α=2**, restoring σ^{2α} (Gaussian) suppression.
- **Fig 2** plots the coefficient of the σ^α term of P_cor for d=3,5,7,9,11 vs α∈[0,2];
  dashed line = first-order P_ph = 0.5. **Code distance barely matters (curves nearly
  coincide)**; for all d, any α<2 gives correlated LER ∝ P_ph → **no protection regardless
  of code size**, except the single point α=2 (Gaussian).

## Numerical simulations — EXACT object (§III, Eqs 12–15, Figs 3–5) [paper]
- **Code:** a **single distance-3 rotated surface code** (state-vector sim ⇒ limited to
  low distance; "we limit ourselves to just simulations of a distance-3 rotated surface
  code," p. 5). No distance *sequence* in the numerics (the distance sweep lives only in
  the analytics / Fig 1–2). Same framework/circuits as ref 76 (Barnes 2017).
- **Error insertion:** random unitary **U_k^(ℓ)(θ_k^(ℓ)) = exp(−i θ_k^(ℓ) σ_y^(ℓ))** —
  a **Y-rotation** by random angle, **inserted after EVERY single gate**, on **BOTH data
  and ancilla qubits**, at every circuit location (a genuine **circuit-level noise model**),
  p. 6. Angles drawn from Gaussian / Cauchy / Student-t / Lévy.
- **Rounds / SPAM:** **three rounds of faulty syndrome extraction** with errors after every
  gate location, then **decoding + perfect correction**, closed by **one round of perfect
  error correction** to clean trailing errors (p. 6). So measurement/SPAM errors ARE present
  during the 3 faulty rounds (errors after every gate incl. the extraction circuitry), but
  the final correction is idealized. **The decoder itself is unnamed** — the text says only
  "decoding and perfect correction"; no MWPM/DEM specification, no correlation-aware vs
  correlation-blind decoder discussion.
- **Metric = FIDELITY, not decoded LER.** Random initial state |ψ_0⟩ = cosα|0⟩ + e^{iβ}sinα|1⟩,
  α,β ~ U[0,2π) (Eq 12; explicitly NOT a Haar average). Fidelity F² = (1/(2π)²)∬dαdβ ∫dθ
  p(θ) |⟨ψ_0|e^{−iθσ_y}|ψ_0⟩|² (Eq 13). **Physical fidelity F² = 5/8 + (3/8) f(t=2)** (Eq
  14), f(t=2) the characteristic function. The plotted quantity is **logical INFIDELITY vs
  physical INFIDELITY** (1−F²), estimated by MC over initial states + error terms; **10^7
  independent trials per point**, 95% CIs by bootstrap (10³ resamples). So the reported
  "logical error rate" is a **post-decode logical INFIDELITY (1 − fidelity to the encoded
  input)**, NOT a syndrome/detection-event rate.
- **Time correlations via SchWARMA [ref 77, arXiv:2010.04580].** Angle at circuit time k =
  ARMA model θ_k^(ℓ) = Σ_i a_i θ_{k−i} (AR) + Σ_j b_j x_{k−j} (MA)   (Eq 15). ARMA needs
  *summing* random variates ⇒ **restricted to stable distributions** (Gaussian, Lévy); the
  **Student-t is NOT stable**, so for Student-t they use only two limits: **white noise**
  (uncorrelated, p=0,q=0) and **DC noise** (a single angle drawn once at circuit start,
  reused at all times — p=0, q→∞). The DC limit = the analytics' "same angle applied
  everywhere" (perfect correlation), now in *time*. For stable distributions they
  interpolate with **exponential moving averages (EMA)**: b_j = N exp(−ln2·j/T_h), N
  normalizes Σb_j=1, **T_h = half-life** of the MA; p=0 (no AR); q=10⌈T_h⌉ terms; one gate
  = one time unit. **Syndrome-extraction cycles take 2–6 ticks** (2–4 CNOTs + 2 X-syndrome
  rotation gates).
- **Results (Figs 3–5):**
  - **Gaussian (Fig 3):** DC and white are indistinguishable; below pseudo-threshold LER is
    quadratically suppressed (slope-2, matching Eq 7). Time-correlation is **benign** for
    Gaussian — all EMA T_h curves overlap. ⇒ confirms analytics.
  - **Student-t (Fig 4):** **white noise** → protected, ~immune to ν (curves overlap);
    **DC noise** → slope depends on ν. **ν=1 (fattest) → logical ∝ physical (slope 1, no
    protection)**; **ν={2,3} → partial protection**; **ν≥4 → full protection (slope-2,
    quadratic)**. (Analytics only covered odd ν, predicting full protection from ν≥5; the
    numerics push it to ν≥4.)
  - **Lévy α-stable, α=1.5 (Fig 5):** white → pseudo-threshold (protected); **DC → no
    protection (slope 1)**; EMA T_h∈{2,4,8,16,32} interpolate — **slope degrades as T_h
    approaches the syndrome-cycle length** (the noise "begins to generate weight-two errors
    across syndrome boundaries," p. 7). ⇒ correlation *time* directly sets the slope loss.

## What they do NOT do — for the A9 novelty defense [paper / verbatim-absence]
Each item below is either an explicit paper statement or a whole-paper absence (I read all
8 body pages + refs; the numerics section §III is the only empirical part and is fully
transcribed above). These back our A9 positioning that **the "all-silent-run sub-channel
rate at fixed marginals + detection-density-vs-correlation" object is not in the prior art.**

1. **(i) NO isolation of an "all-silent run" sub-channel (logical flip ∧ zero detection
   events).** The paper's only logical observable is a **fidelity/infidelity** (Eq 13–14)
   marginalized over all error realizations and initial states. There is **no conditioning
   on the detection-event pattern at all**, hence no "silent" (zero-detector) subclass, and
   no rate for "logical error occurred while the syndrome record was blank." The concept is
   absent from §II (perfect-code counting — no detectors exist in that model) and §III
   (fidelity MC — detectors are never inspected). **This is the sharpest gap: our v2b
   object (silent-run floor) has no analogue here.**

2. **(ii) NO reported detection-event rate / syndrome density, and NO
   density-vs-correlation curve (esp. a *decrease*).** Detection events / syndrome density
   are never computed or plotted. The analytic model (§II) is code-capacity (data-qubit
   errors only, no syndrome extraction, so **no detectors exist**); the numerics report
   only logical vs physical *infidelity* (Figs 3–5), never the raw detector statistics. So
   there is **no statement about how syndrome/detection density moves with correlation
   strength**, and certainly no observation that it can *drop* under correlation (the
   Kam-style "quiet correlated run" effect). Absent.

3. **(iii) NO common↔local interpolation parameter (spatial).** The spatial-correlation
   axis (§II) is **binary**: fully independent (Eq 2a, n i.i.d. angles) vs perfectly
   correlated (Eq 2b, one shared angle on all qubits). There is **no tunable spatial
   correlation length / shared-fraction knob** — no interpolation between local and common.
   (The *only* interpolation they build is in **time** — EMA half-life T_h and the α-stable
   α — never a spatial common↔local slider.) The heaviness knob (ν, α) tunes the *tail*,
   not the *spatial coupling range*. Absent.

4. **(iv) NO circuit-level per-round detection-event stream — everything is folded into a
   post-decode scalar.** The analytics give a closed-form logical *probability* (Eq 2–3);
   the numerics give a Monte-Carlo logical *infidelity* (Eq 13). Neither ever emits or
   analyzes a **round-resolved detection-event record**. There is no shot-level syndrome
   stream, no per-round detector time series, no detector-graph / DEM object. The temporal
   structure enters only through the *input* angle correlations (SchWARMA), never through an
   *observed* detector-stream statistic. Absent.

5. **(v) Marginal-fixing is NOT an explicit methodology — the comparison does NOT hold the
   marginal fixed.** This is a **contrast** with Kam (2410.23779), and important to state
   precisely: Clader et al. compare correlated vs uncorrelated as a function of a **shared
   width parameter σ (or physical infidelity)** — the *pseudo-threshold plot* is
   logical-infidelity **vs physical-infidelity**, so they compare at matched **P_ph**, not
   at a matched per-location Pauli marginal after twirling. Their correlated and
   uncorrelated models share the *distribution family and σ*, and the physical-fidelity
   formula (Eq 14, F²=5/8+(3/8)f(t=2)) is the **same** for both — so P_ph *is* held fixed
   between the two by construction of the x-axis. But there is **no marginalization
   construction** (no C_E reparametrization, no "make the independent model reproduce the
   correlated per-(round,stab) marginal" step à la Kam Appendix A). The fixed quantity is a
   *coherent* single-qubit physical infidelity, not a *twirled Pauli marginal*. So: matched
   P_ph = **yes, implicitly, via the plot axis**; explicit fixed-Pauli-marginal methodology
   = **no**. (For A9: our fixed-marginal construction is closer to Kam's; Clader's "fixed
   marginal" is only the coherent physical infidelity.)

## Limitations [paper]
- **L1 (coherent-only, semiclassical bath).** Errors are *coherent* Y-rotations with a
  classically-random angle; a true open-quantum-system bath (back-action, finite-T,
  non-trivial phase evolution) is explicitly **out of scope** (p. 1–2, deferred to future
  work). So this is NOT an incoherent-Pauli-correlation study — it is a **coherent
  rotation-angle-distribution** study. The heavy tail lives in the *angle*, not in a Pauli
  error probability.
- **L2 (spatial correlation = perfect/binary).** The analytic spatial model has only the
  two extremes (fully independent / fully common); no partial spatial correlation.
- **L3 (d=3 numerics only; state-vector-limited).** The circuit-level numerics are a single
  d=3 rotated surface code (state-vector ⇒ can't scale). The distance dependence (Fig 1,2,
  Table I) is **analytic code-capacity only** (perfect-code counting, which the text notes
  can *under*-count what real surface codes correct — "certain codes, such as surface codes,
  can correct certain types of high-weight errors that will break this assumption," p. 2).
- **L4 (decoder unspecified).** The numeric decoder is described only as "decoding and
  perfect correction" — no algorithm named, no correlation-aware vs blind comparison. So
  there is **no misspecification/decoder-mismatch axis** (unlike Kam's marginalized-DEM
  study). The degradation is a *physics* effect (high-weight errors exceed d_eff), not a
  decoder-blindness effect.
- **L5 (characterization gap = their motivation).** Their headline open problem: standard
  noise-spectroscopy expands into **moments/cumulants**, which are *undefined/infinite* for
  heavy-tailed distributions (p. 2) — so existing characterization can't detect this noise;
  they call for new characterization methods. (This is the "need a new tomography" pitch,
  not a twin/decoder result.)

## Relevance to project — A9 novelty anchor [ours]
This paper is the **spatial/temporal heavy-tail coherent-correlation** prior-art anchor for
prereg A9. The precise positioning:

1. **[paper] object = post-decode logical INFIDELITY (or code-capacity logical
   probability) vs a heavy-tail angle distribution; [ours] object = a
   detection-event-conditioned sub-channel (all-silent-run rate) + detection density, both
   at fixed marginals.** These are **different observables on different subspaces**. Clader
   never conditions on the syndrome record; we condition ON it (silent = zero detectors).
   Their "logical error rate" is 1 − fidelity to the encoded input, marginalized over every
   error realization — the coarsest possible scalar. This is the load-bearing distinction
   for A9: **the silent-run sub-channel and the detection-density-vs-correlation curve are
   not measured, plotted, or defined anywhere in Clader et al.** (see NOT-done items i, ii,
   iv).

2. **[paper] 3× (d=3 correlated/uncorrelated coefficient, Gaussian) vs [ours] 15.9×
   (silent-run floor at fixed k=3 marginal) — the two "3×-ish factors are NOT the same
   object.** Be explicit in the A9 writeup:
   - **Clader's 3×** (Eq 7: P_cor/P_unc = (15σ⁴/8)/(5σ⁴/8) = 3 at d=3) is the ratio of the
     **leading σ⁴ coefficients** of the **marginal post-decode logical error probability**
     for **perfectly-correlated vs fully-independent coherent Gaussian rotations** in a
     code-capacity d=3 perfect code. It is a **coefficient inflation at fixed distance**
     (same σ-power) — a spatial-correlation effect, decoder-idealized, **no detector
     conditioning, no fixed-Pauli-marginal**. It grows as **d!!** with distance (Fig 1),
     but stays a coefficient (never a distance loss) for Gaussian.
   - **Our 15.9×** is the **silent-run floor ratio** (logical flip ∧ zero detection events)
     at a **fixed per-(round,stab) Pauli marginal, k=3 syndrome match**, accompanied by a
     **detection-density DECREASE** — a *conditioned sub-channel* quantity our v2b measures,
     on a *fixed-marginal* comparison, from the *detection-event stream*.
   - ⇒ Different numerator (silent sub-channel vs full logical prob), different control
     (fixed twirled marginal vs fixed σ/P_ph), different data (detector-conditioned stream
     vs marginal fidelity), different mechanism (correlated-quiet-run vs high-weight-from-
     heavy-tail). **The near-coincidence of "≈3–16×" magnitudes is not a collision of
     claims.** No contradiction with A9 — if anything Clader's absence of the silent-run /
     detection-density object *supports* A9 novelty.

3. **[paper] correlation-severity lever = TAIL INDEX (heavy tails); [ours] lever =
   correlation STRUCTURE at fixed marginal.** Clader's whole effect vanishes for light
   (Gaussian) tails — the distance loss (d_eff→1) is a **heavy-tail** phenomenon (Cauchy /
   ν small / α<2). Our silent-run effect is a **structure-at-fixed-marginal** phenomenon
   (Kam-family), independent of tail heaviness. So the two papers occupy **orthogonal axes**
   (heavy-tail coherent-angle vs fixed-marginal correlation-structure) — cite Clader for the
   heavy-tail axis, Kam for the fixed-marginal structure axis; **our object sits in
   neither** (detection-conditioned sub-channel at fixed marginal).

4. **[ours] What Clader DOES pin down that we should cite as settled:** (a) coherent
   common-mode rotations with heavy-tailed angles reduce d_eff (down to 1 for Cauchy) —
   a real, distribution-dependent QEC breakdown; (b) the **d!!** coefficient growth for
   Gaussian correlated noise (Fig 1) is a clean closed-form fact; (c) the **d ≤ 2r−3**
   Student-t recovery boundary and the **α=2-only** Lévy protection point are exact
   analytic thresholds; (d) time-correlation degrades the slope as the correlation half-life
   T_h approaches the syndrome-cycle length (Fig 5) — a temporal analogue of our
   "correlation across the decoding boundary" intuition, but again measured as
   infidelity-slope, not detector statistics.

5. **[ours] Caveats for citing this paper.** (i) It is **coherent-rotation**, not
   incoherent-Pauli-correlated — do not conflate its "correlated noise" with our
   Pauli-DEM-correlation axis; the heavy tail is in the *angle*. (ii) The distance sweep is
   **code-capacity analytic** (perfect-code counting), which the authors themselves flag as
   *under*-counting real surface-code correction (p. 2) — so Fig 1's d!! and Table I's
   distance boundaries are perfect-code idealizations, not surface-code numerics (the only
   surface-code numerics are d=3, §III). (iii) **No decoder is specified** and **no
   detection-event data exists** — so there is nothing here to compare against our
   frozen-MWPM-DEM / detection-density machinery except by re-deriving. (iv) Marginal is
   held fixed only as *coherent physical infidelity* (Eq 14), not as a *twirled Pauli
   marginal* (contrast Kam Appendix A).

## How to use / trust + open questions [ours]
- **Trust:** high for the analytics (closed-form Eq 2–11 + Table I, self-contained,
  re-derivable) and the qualitative numerics (standard state-vector d=3, ref-76 framework).
  **Medium** on any quantitative surface-code distance claim: Fig 1 / Table I are
  *code-capacity perfect-code* numbers, and the only genuine surface-code simulation is a
  single d=3. Carry L4 (decoder unspecified) whenever contrasting with decoder-mismatch
  papers.
- **For A9:** the three NOT-done items that most directly back our novelty are **(i) no
  silent-run / zero-detector sub-channel, (ii) no detection-density-vs-correlation curve,
  (iv) no round-resolved detection-event stream** — all confirmed absent by full-text read.
  The **3× vs 15.9×** distinction (item 2 above) is the precise sentence to put in the A9
  positioning: same-magnitude numbers, categorically different objects. **No finding in
  this paper contradicts the A9 positioning.**
- **Open (for the principal):** spot-verify (a) Eq 7 coefficients (5/8, 15/8 → ratio 3);
  (b) that Fig 1's labelled series is literally d!! (3,15,105,945,10395,135135,2027025 for
  d=3…15 — matches double-factorial exactly); (c) the Table I r=1 Cauchy correlated columns
  are all σ¹ (d_eff=1); (d) the §III metric is infidelity (Eq 13), NOT a detection-event
  rate — the "logical error rate" wording in the text refers to 1−fidelity.
