# CP-divisibility check — derivation + predictions (predict-before-measure, 2026-07-04)

**Status: DERIVATION written BEFORE the run.** Committed script:
`outputs/twin_validation/cpdiv_passive_record_check.py`. Grounds
`theory_first_grounding_nonmarkovian_legitimacy_2026-07-04.md` §0/§1 with committed numbers, and settles
notion-1 (CP-divisibility breaking) reachability + passive-record survival before the notion-2 gate build.
Anchors: RHP 0911.4270 (Eq 4), BLP 0908.0238, Anderson–Kubo single-RTN dephasing.

## The exact objects

Dephasing coherence factor `λ(t) = |ρ_01(t)|/|ρ_01(0)|`. RHP/BLP for pure dephasing (a-exact):
- **RHP rate** `γ(t) = −½ d/dt ln λ(t)`; `γ(t)<0 ⇔ λ increasing ⇔ revival`. **RHP measure** `I = −2∫_{γ<0} γ dt`
  (0911.4270 Eq 4). CP-divisible ⇔ `I=0`.
- **BLP measure** (σx-eigenstate pair, `D(t)=λ(t)`): `N = Σ_i [λ(b_i)−λ(a_i)]` over increasing intervals
  (0908.0238 Eq 12). Non-Markovian ⇔ `N>0`.

Two coherence models:
- **Gaussian** (sum of many weak RTNs, CLT): `λ(t)=e^{−χ(t)}`, `χ(t)=∫₀ᵗ(t−τ)C(τ)dτ`,
  `C(τ)=Σ_k v_k² e^{−2γ_k|τ|} ≥ 0`. Then `γ(t)=½∫₀ᵗ C(τ)dτ ≥ 0`.
- **Single RTN EXACT** (Anderson–Kubo, non-Gaussian): coupling `v`, switching rate `γ_sw`,
  `λ(t)=e^{−γ_sw t}[cosh(κt)+(γ_sw/κ)sinh(κt)]`, `κ=√(γ_sw²−v²)`. For `v>γ_sw`, `κ=iΩ`, `Ω=√(v²−γ_sw²)`, so
  `λ(t)=e^{−γ_sw t}[cos(Ωt)+(γ_sw/Ω)sin(Ωt)]` — **oscillates → revivals.**

## PREDICTIONS (predict-before-measure)

- **C1 (a-exact) — `OneOverFDriftSource` (Gaussian, 8 weak RTNs) is CP-DIVISIBLE.** `C≥0 ⇒ γ(t)≥0 ⇒ RHP I=0`,
  `λ` monotone `⇒ BLP N=0`. Its non-Markovianity is notion-2 (classical memory), invisible to RHP/BLP.
- **C2 (a-exact) — a single RTN at the GAUSSIAN level is ALSO CP-divisible.** `C=v²e^{−2γ_sw τ}≥0 ⇒ I=0, N=0`.
  ⇒ the Gaussian/autocorrelation approximation CANNOT produce CP-div breaking; **non-Gaussianity is essential.**
- **C3 (a-exact) — a single EXACT RTN breaks CP-divisibility iff `v>γ_sw`.** For `v>γ_sw`: `λ` oscillates ⇒
  `RHP I>0`, `BLP N>0`. Sweep `v/γ_sw`: transition exactly at `v/γ_sw=1` (`I=N=0` for `v≤γ_sw`, `>0` above).
  The repo `RTNSource` defaults (`v=amplitude=1e-4/ns`, `γ_sw=gamma_per_cycle/cycle_time=5e-5/ns` ⇒ `v/γ_sw=2`)
  are already mildly-breaking but heavily damped (`Ω≈γ_sw`); a clear demonstration uses `v≫γ_sw`
  (e.g. `v=1e-3/ns`, `γ_sw=5e-6/ns`, `v/γ_sw=200`, `Ω≈v`, many revivals within `1/γ_sw`).
- **C4 (b — the passive-record survival, the novel finding) — coherence revival is TWIRLED OUT of the passive
  syndrome record; only classical latent memory (notion-2) survives.** Under the FAITHFUL projective-measurement
  RATE record model — per-round `e_r ~ Bernoulli(p_r)`, `p_r = clip(p0(1+κ·ξ_r), 0, 1)` (the elevated-RATE
  model the coupled teacher uses via `γφ`-modulation; the ancilla is measured every cycle ⇒ NO between-round
  coherence carry) — the record is a **classical rate process** (Watkins-Quiroz 2501.06619: ensemble-avg
  syndrome is block-diagonal / classical). Consequences: **(i) notion-2 SURVIVES** —
  `Cov(e_r,e_{r+ℓ}) = p0²κ²⟨ξ_r ξ_{r+ℓ}⟩ > 0`, positive-monotone, tracking the latent autocov; **(ii) notion-1
  is STRUCTURALLY ABSENT** — there is no coherence-carry term for the revival frequency `Ω` to enter, so the
  CP-div-BREAKING strong RTN's record looks identical-in-shape to the CP-divisible 1/f's (classical rate
  memory), indistinguishable-by-revival. Falsifier: a coherence-carry record model that DID surface `Ω` —
  but that would be UNfaithful to projective per-round QEC measurement. (⚠ the symmetric-RTN `½(1−cos φ)`
  phase model is DEGENERATE — `|φ|` is sign-independent so it washes out ALL latent memory; the rate model is
  the faithful choice.)

## Epistemic classes + declared model

- **(a) exact:** C1, C2, C3 (RHP/BLP of the reduced dephasing map from closed-form coherences).
- **(b) band/finding:** C4 (passive-record survival) — under the **declared record model** (§ below), class (b).
- **Declared record model (bounded simplification):** per-round Z-error `e_r ~ Bernoulli(p_r)`,
  `p_r = clip(p0(1+κ·ξ_r), 0, 1)` (elevated-RATE model = the coupled teacher's `γφ`-modulation), `ξ_r` the
  RTN/1f latent, independent projective syndrome measurement each round (NO between-round coherence carry).
  This is the faithful passive-syndrome map; it EXCLUDES coherence carry (the thing whose survival is in
  question) — so C4 tests whether the revival can appear WITHOUT assuming it. (The `½(1−cos φ)` phase model is
  degenerate for a symmetric RTN — `|φ|` sign-independent — so the rate model is used.)

## RESULTS (post-run 2026-07-04; predictions above INTACT)

Committed: `outputs/twin_validation/cpdiv_passive_record_check.py` (`python-exit=0`, artifact
`cpdiv_passive_record_check.json`, `content_hash=5bc63d4d4888ce539dffde3ff809e37c093a0a30582a266ad9d7cabca3b19f68`,
`GATE_RESULT ... GROUNDING_CONFIRMED`).

| # | prediction | result | verdict |
|---|---|---|---|
| C1 | OneOverF Gaussian CP-divisible | BLP N=0, monotone | **CONFIRMED (a-exact)** |
| C2 | single RTN at Gaussian level CP-divisible (even v/γ_sw=200) | BLP N=0, monotone | **CONFIRMED — non-Gaussianity essential** |
| C3 | exact RTN breaks iff v>γ_sw | v/γ_sw ≤1: N=0; =1.1: N=1.06e-3; =2: N=0.195; =10: N=2.69; =200: N=62.9 — **sharp transition at 1.0** | **CONFIRMED (a-exact)** |
| C4 | revival twirled; notion-2 survives | strong RTN free coherence BLP N=62.9 (45842 revivals) yet record err-cov positive-monotone (2.5e-3→2.2e-3) tracking ξ, **identical-in-shape to CP-divisible 1/f** (2.0e-3→1.0e-3) — no revival trace | **CONFIRMED (b)** |

**Grounded conclusion:** our `OneOverFDriftSource` is **CP-divisible (RHP=BLP=0)** — anchoring legitimacy on
CP-div breaking would score it zero. CP-div breaking is reachable only via a strong non-Gaussian RTN (`v>γ_sw`),
and **its coherence revival is twirled out of the passive syndrome record** (projective per-round measurement ⇒
classical rate process; consistent with the standing [[project-nonmarkovian-wedge-must-be-coherence]]: revival
is coherence-probe-only, NOT Z-syndrome-visible). ⇒ **the simulator's passive-record legitimacy signal is
notion-2 (classical multi-time memory)** — and, since notion-2 at finite Markov order is forgeable by Markov-k
(that note's Probe A/B), the non-forgeable core is the **1/f power-law / multi-timescale tail** that no
finite-order Markov reproduces (Level-3, `h2 §2b` `E(k)` residual), measured **multi-time / differentiable
syndrome NLL** (never 2-point), sited **Class-1/2** (Kam decode-consequential).
