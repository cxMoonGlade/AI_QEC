# CP-divisibility check — derivation + predictions (predict-before-measure, 2026-07-04)

> **OBJECT-MISMATCH CORRECTION, 2026-07-13.** C1 was evaluated with a Gaussian second-cumulant
> coherence surrogate parameterized by the production source's amplitudes/rates. The production
> `OneOverFDriftSource` is instead an explicit sum of eight finite RTNs, including default modes
> outside the weak-RTN limit. The committed `RHP=BLP=0` result therefore applies to the surrogate,
> **not** to the implemented source. A 2026-07-13 preregistered gate subsequently found BLP
> backflow for two declared finite-RTN free-induction lifts, but production uses a different
> `z -> Theta` fan-out; a stochastic source alone has no CP-divisibility status and the production
> QEC map remains open. C2–C3 remain
> algebraic statements about their declared models. C4 deliberately uses a rate-record model that
> excludes between-round coherence carry; absence there is by construction and cannot prove that a
> physical QEC instrument universally twirls omitted coherence. See
> [`notion123_taxonomy_literature_closure_2026-07-13.md`](notion123_taxonomy_literature_closure_2026-07-13.md).

**Status: HISTORICAL DERIVATION; C1 object and C4 interpretation corrected 2026-07-13.** Committed
script: `outputs/twin_validation/cpdiv_passive_record_check.py`. It supplies model-conditional
bug-catching numbers; it does not settle the production source's notion-1 status or physical
passive-record reachability.
Anchors: RHP 0911.4270 (Eq 4), BLP 0908.0238, Anderson–Kubo single-RTN dephasing.

## The exact objects

Dephasing coherence factor `λ(t) = |ρ_01(t)|/|ρ_01(0)|`. RHP/BLP for pure dephasing (a-exact):
- **RHP rate** `γ(t) = −½ d/dt ln λ(t)`; `γ(t)<0 ⇔ λ increasing ⇔ revival`. **RHP measure** `I = −2∫_{γ<0} γ dt`
  (0911.4270 Eq 4). CP-divisible ⇔ `I=0`.
- **BLP measure** (σx-eigenstate pair, `D(t)=λ(t)`): `N = Σ_i [λ(b_i)−λ(a_i)]` over increasing intervals
  (0908.0238 Eq 12). Non-Markovian ⇔ `N>0`.

Three distinct objects must not be conflated:
- **Gaussian** (sum of many weak RTNs, CLT): `λ(t)=e^{−χ(t)}`, `χ(t)=∫₀ᵗ(t−τ)C(τ)dτ`,
  `C(τ)=Σ_k v_k² e^{−2γ_k|τ|} ≥ 0`. Then `γ(t)=½∫₀ᵗ C(τ)dτ ≥ 0`.
- **Single RTN EXACT** (Anderson–Kubo, non-Gaussian): coupling `v`, switching rate `γ_sw`,
  `λ(t)=e^{−γ_sw t}[cosh(κt)+(γ_sw/κ)sinh(κt)]`, `κ=√(γ_sw²−v²)`. For `v>γ_sw`, `κ=iΩ`, `Ω=√(v²−γ_sw²)`, so
  `λ(t)=e^{−γ_sw t}[cos(Ωt)+(γ_sw/Ω)sin(Ωt)]` — **oscillates → revivals.**
- **Production `OneOverFDriftSource`:** an explicit sampled sum of eight finite RTNs. With the
  defaults, `v_k=1e-4/sqrt(8)≈3.54e-5 rad/ns` and the slowest
  `γ_k=0.005/1000=5e-6/ns`, so `v_k/γ_k≈7.07`. It is not uniformly in the weak/CLT limit.
  Its exact coherence is a product of finite-RTN coherences and must be evaluated as that object.

## PREDICTIONS (predict-before-measure)

- **C1 (a-exact for the surrogate only) — the positive-exponential-covariance Gaussian surrogate
  is CP-DIVISIBLE.** `C≥0 ⇒ γ(t)≥0 ⇒ RHP I=0`, `λ` monotone `⇒ BLP N=0`. This does
  not determine the explicit finite-RTN production source.
- **C2 (a-exact) — a single RTN at the GAUSSIAN level is ALSO CP-divisible.** `C=v²e^{−2γ_sw τ}≥0 ⇒ I=0, N=0`.
  ⇒ the Gaussian/autocorrelation approximation CANNOT produce CP-div breaking; **non-Gaussianity is essential.**
- **C3 (a-exact) — a single EXACT RTN breaks CP-divisibility iff `v>γ_sw`.** For `v>γ_sw`: `λ` oscillates ⇒
  `RHP I>0`, `BLP N>0`. Sweep `v/γ_sw`: transition exactly at `v/γ_sw=1` (`I=N=0` for `v≤γ_sw`, `>0` above).
  The repo `RTNSource` defaults (`v=amplitude=1e-4/ns`, `γ_sw=gamma_per_cycle/cycle_time=5e-5/ns` ⇒ `v/γ_sw=2`)
  are already mildly-breaking but heavily damped (`Ω≈γ_sw`); a clear demonstration uses `v≫γ_sw`
  (e.g. `v=1e-3/ns`, `γ_sw=5e-6/ns`, `v/γ_sw=200`, `Ω≈v`, many revivals within `1/γ_sw`).
- **C4 (model control, not a physical reachability finding) — the declared rate-only record contains
  no coherence revival because it has no coherence-carry state.** Under the projective-measurement
  RATE record model — per-round `e_r ~ Bernoulli(p_r)`, `p_r = clip(p0(1+κ·ξ_r), 0, 1)` (the elevated-RATE
  model the coupled teacher uses via `γφ`-modulation; the ancilla is measured every cycle ⇒ NO between-round
  coherence carry) — the record is a **classical rate process by construction**. Consequences:
  **(i) notion-2 SURVIVES** —
  `Cov(e_r,e_{r+ℓ}) = p0²κ²⟨ξ_r ξ_{r+ℓ}⟩ > 0`, positive-monotone, tracking the latent autocov; **(ii) notion-1
  is STRUCTURALLY ABSENT** — there is no coherence-carry term for the revival frequency `Ω` to enter, so the
  CP-div-BREAKING strong RTN's record looks identical-in-shape to the Gaussian-surrogate 1/f-like arm (classical rate
  memory), indistinguishable-by-revival. Falsifier: a coherence-carry record model that DID surface `Ω` —
  but deciding whether it is faithful requires the missing channel-to-instrument bridge. (⚠ the symmetric-RTN `½(1−cos φ)`
  phase model is DEGENERATE — `|φ|` is sign-independent so it washes out ALL latent memory; the rate model is
  the chosen comparator.)

## Epistemic classes + declared model

- **(a) exact:** C1 only for the Gaussian surrogate; C2 and C3 for their declared reduced
  dephasing models. No exact class is assigned to production-source CP-divisibility.
- **Model-conditional control:** C4 shows what the rate-only record generator can encode. It is not a
  physical twirling result or a bounded simplification.
- **Declared record model (bounded simplification):** per-round Z-error `e_r ~ Bernoulli(p_r)`,
  `p_r = clip(p0(1+κ·ξ_r), 0, 1)` (elevated-RATE model = the coupled teacher's `γφ`-modulation), `ξ_r` the
  RTN/1f latent, independent projective syndrome measurement each round (NO between-round coherence carry).
  It EXCLUDES coherence carry (the thing whose survival is in question), so it cannot adjudicate
  whether the exclusion is faithful. (The `½(1−cos φ)` phase model is
  degenerate for a symmetric RTN — `|φ|` sign-independent — so the rate model is used.)

## RESULTS (post-run 2026-07-04; object/interpretation corrected above)

Committed: `outputs/twin_validation/cpdiv_passive_record_check.py` (`python-exit=0`, artifact
`cpdiv_passive_record_check.json`, `content_hash=5bc63d4d4888ce539dffde3ff809e37c093a0a30582a266ad9d7cabca3b19f68`,
`GATE_RESULT ... GROUNDING_CONFIRMED`).

| # | prediction | result | verdict |
|---|---|---|---|
| C1 | positive-covariance Gaussian surrogate CP-divisible | BLP N=0, monotone | **CONFIRMED for surrogate; superseded as a proxy for finite RTNs** |
| C2 | single RTN at Gaussian level CP-divisible (even v/γ_sw=200) | BLP N=0, monotone | **CONFIRMED — non-Gaussianity essential** |
| C3 | exact RTN breaks iff v>γ_sw | v/γ_sw ≤1: N=0; =1.1: N=1.06e-3; =2: N=0.195; =10: N=2.69; =200: N=62.9 — **sharp transition at 1.0** | **CONFIRMED (a-exact)** |
| C4 | rate-only record cannot carry revival | strong-RTN free coherence has BLP N=62.9 while the separately defined rate record has positive-monotone covariance and no revival variable | **BY-CONSTRUCTION CONTROL; no physical twirl verdict** |

**Corrected conclusion:** the registered Gaussian surrogate is CP-divisible and the exact single-RTN
control breaks CP-divisibility for `v>γ_sw`. The later exact gate confirms BLP backflow for both
declared free-induction lifts of the eight-finite-RTN defaults; see
[`finite_rtn_exact_cpdiv_result_2026-07-13.md`](finite_rtn_exact_cpdiv_result_2026-07-13.md). Those
lifts are not the production fan-out/QEC channel. Separately, the rate-only record generator can carry notion-2 multi-time
memory but cannot carry a coherence revival it never represents. Whether a physical QEC instrument
suppresses or exposes such coherence is channel- and schedule-dependent and remains open here. No
finite-lag diagnostic in this run proves that every finite-order Markov/HMM representation is
excluded.
