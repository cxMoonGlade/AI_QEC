# 精读 — Kattemölle, Gulácsi, Burkard, "Non-Markovianity induced by Pauli-twirling" (arXiv:2602.08464)

> **Provenance (2026-07-03): FULL-TEXT 精读 of the core** (abstract, intro, preliminaries: divisibility /
> GKSL / channel-semigroup-Markovianity, the PL-channel characterization, Fig. 1 map). PDF → txt
> `outputs/papers/2602.08464.txt` (PyMuPDF, 9 pages, arXiv v1 9 Feb 2026). Two worked examples (§§ later) +
> feasibility in the txt. Secondary/support paper. Tags **[paper]**/**[ours]**.

## Metadata [paper]
- Kattemölle, Gulácsi, Burkard (Konstanz / Jülich / RWTH Aachen). arXiv:2602.08464v1 (Feb 2026). Theory.

## Executive summary [paper]
Pauli twirling / randomized compiling turns arbitrary noise into a Pauli channel and underpins
Pauli-Lindblad (PL) noise models (`E = e^L`, `L(ρ) = Σ_a λ_a(P_a ρ P_a − ρ)`), which are usually assumed to
have **nonnegative** parameters `λ_a ≥ 0` "on grounds of physicality." The paper proves: a general Pauli
channel is **non-Markovian (channel-semigroup sense) IFF at least one PL parameter `λ_a` is negative**. Using
this, it shows **Markovian channels OFTEN become non-Markovian AFTER Pauli twirling** — so a correct
description requires NEGATIVE PL parameters. Concrete example: the standard `√X`-gate implementation under
Markovian dephasing + relaxation becomes non-Markovian after twirling (plausibly already present in current
hardware, especially dephasing-biased). Direct implications for error mitigation (PL models with
nonnegative-only params are qualitatively wrong).

## Method (deep) [paper]
- **Markovianity by divisibility** (GKSL, Eq. 2–3): `dρ/dt = −i[H(t),ρ] + Σ_k γ_k(t)(L_k ρ L_k† − ½{L_k†L_k,ρ})`,
  divisible ⟺ `γ_k(t) ≥ 0 ∀t` (the RHP/BLP CP-divisibility condition).
- **Channel semigroup Markovianity (CSM):** a single channel `E` is Markovian iff ∃ generator `L` in Lindblad
  form with `E = e^L` — testable by `log E` → check Lindblad form.
- **Generalized PL channels** (`λ_a ∈ ℂ`/allow negative): any Pauli channel is a PL channel once the
  nonnegativity restriction is lifted; **the physical PL channels with ≥1 negative `λ_a` are EXACTLY the
  non-Markovian Pauli channels** (Fig. 1 map: CSM = nonnegative-λ region; the rest is non-Markovian).
- **Twirling breaks Markovianity:** twirling a Markovian channel yields a Pauli channel whose PL
  parameterization generically has a negative `λ_a` ⇒ non-Markovian.

## Findings [paper]
- The negative-PL-parameter is the measurable non-Markovian signature (in the Pauli/stochastic sector).
- Effect estimated observable under realistic settings; the `√X` gate is a standing example.

## Relevance to the reconstruction [ours]
- **Sharpens the retraction of the matched-marginal / twirled observable.** The retracted framing leaned on
  Pauli-twirled (matched-marginal) statistics as an implicit Markov null. This paper shows twirling is NOT a
  clean Markovianizer: it both measurement-twirls the coherence (Prop IW-1
  [[involuntary_w_check_2026-07-03]]) AND can INDUCE non-Markovianity (negative PL params). So a twirled/Pauli
  baseline is doubly unsound as "the Markov reference."
- **Gives a concrete, measurable NM observable in the STOCHASTIC/Pauli sector: the sign of the PL parameters
  `λ_a`** — CSM/CP-divisibility applied to the (Zheng-learnable) Pauli channel. This complements the
  process-tensor observable (White) with a Pauli-Lindblad-side witness that is efficiently estimable from the
  same syndrome/gate data, and it is the discrete-Pauli image of the RHP `I = −2∫_{γ<0}γ` measure the
  reconstruction already uses ([[rhp_nonmarkovianity_measure_0911.4270]]).
- Reinforces that the correct Markov null is CP-divisibility (γ_k ≥ 0 / λ_a ≥ 0), NOT a twirled-marginal match.

## Related notes
[[qec_learnable_logical_noise_2601.22286]] (Pauli learnability), [[rhp_nonmarkovianity_measure_0911.4270]],
[[blp_nonmarkovianity_measure_0908.0238]], [[involuntary_w_check_2026-07-03]] (twirling ⇒ coherence-blind),
[[white_pollock_process_tensor_tomography_2106.11722]].
