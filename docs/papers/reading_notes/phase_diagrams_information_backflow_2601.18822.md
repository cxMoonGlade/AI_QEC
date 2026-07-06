精读 provenance: FULL-TEXT read via ar5iv HTML (https://ar5iv.labs.arxiv.org/abs/2601.18822). Date: 2026-07-06.
Source: arXiv:2601.18822 (Jan 2026). Some sub-equation constants transcribed from the HTML render; where a
symbol was ambiguous in the render it is flagged inline. No equations fabricated — only what was read.

## Metadata [paper]

- Title: "Phase Diagrams of Information Backflow: Unifying Entanglement Revivals and Entropy Overshoots in
  Minimal Non-Markovian Models"
- Author: Koichi Nakagawa (Hoshi University, Tokyo, Japan)
- arXiv: 2601.18822 (Jan 2026)
- Class: open-system non-Markovianity / information backflow; minimal quantum vs. classical models with a
  shared fractional (long-memory) kernel.

## Executive summary [paper]

The paper builds a MINIMAL pair of models — a quantum two-state dissipative relaxation model and a classical
three-state stochastic model — driven by the SAME memory kernel (a Caputo fractional derivative of order
α∈(0,1], whose solution is the Mittag–Leffler function E_α). It defines a single backflow functional N_I that
integrates the positive-slope portions of an "information-like observable" I(t): for the quantum model I(t) is
an entanglement-revival component; for the classical model I(t) is Shannon entropy (or KL divergence). It then
draws a phase diagram in the (α, ω/λ) plane and finds a sharp boundary near α ≃ 1/2 separating weak- and
strong-revival regimes — and CRUCIALLY the SAME α ≃ 1/2 boundary appears on BOTH the quantum and the classical
side once the same kernel is imposed. The paper's own conclusion: the boundary "originates from the kernel's
mathematical structure rather than from quantumness per se." This is the decisive certificate that
revival/backflow witnesses MEMORY (the kernel), not quantumness.

## Key equations/criteria [paper] (verbatim / near-verbatim from HTML render)

- Backflow functional (integral form):
    N_I ≡ ∫₀^∞ Θ(İ(t)) İ(t) dt
  where I(t) is "an information-like observable derived from the observed state," Θ is the Heaviside step, and
  İ = dI/dt. (Only the intervals where the observable is INCREASING contribute — this is the "backflow.")

- Backflow functional (discrete/interval form):
    N_I = Σ_k [ I(t_k^end) − I(t_k^start) ]
  summed over "maximal intervals with İ > 0."  [i.e. the total upward variation of I across all revival windows]

- Memory kernel / α:
    "The Markovian limit α=1 reproduces an exponential kernel with a single timescale, while 0<α<1 yields
     long-tailed memory encoded by the Mittag–Leffler function E_α(·)."
  So α is a FRACTIONAL (Caputo) memory-kernel exponent; α=1 ⇒ Markovian exponential kernel; α<1 ⇒ long-tailed
  power-law memory.

- Quantum observable I(t) (entanglement-revival component):
    b_qe^(α)(t) = (1/4) [ E_α(−λ^α t^α) ]² sin²(ω t)
  [transcription note: HTML rendered as "1/4[Eα(−λαtα)]²sin²(ωt)"; the E_α(−λ^α t^α) envelope × oscillatory
   sin²(ωt) is the load-bearing structure — an oscillation under a Mittag–Leffler decay envelope.]

- Classical observable I(t):
    H(t) = − Σ_{i=1}^{3} p_i(t) ln p_i(t)   (Shannon entropy of the 3-state model; KL divergence also used)

- Phase boundary:
    "a sharp boundary near α ≃ 1/2 in the (α, ω/λ) plane" separating "weak- and strong-revival regimes";
    classically, "marked change of behavior around α ≃ 1/2."

## Relevance to project [ours]

- [paper] The SAME backflow functional N_I, driven by the SAME Mittag–Leffler / Caputo-α memory kernel,
  produces revival phases on BOTH the quantum-entanglement side AND the classical-entropy side, with the
  SAME α ≃ 1/2 phase boundary. [paper] Verdict: "the boundary originates from the kernel's mathematical
  structure rather than from quantumness per se."
- [ours] This is THE citation for Flag 0's settled result: entanglement/negativity REVIVAL (backflow) of a
  reduced-channel Choi = RHP non-CP-divisibility = non-Markovianity, and it is FORGEABLE by classical
  non-Markovian noise. Nakagawa demonstrates the forgeability CONSTRUCTIVELY at the level of the backflow
  functional itself: a purely classical 3-state stochastic process with the same long-memory kernel exhibits
  an entropy overshoot on the identical N_I functional, crossing the identical α≃1/2 boundary. A bare revival
  therefore CANNOT distinguish quantum memory from classical memory.
- [ours] This directly supports our in-house Control 0b (classical RTN dephasing FIRES a bare
  negativity-revival witness while genuine Bäcker C#(t1)<C(t2) stays SILENT): our empirical forgery is exactly
  the phenomenon Nakagawa proves is kernel-driven and quantum/classical-symmetric.
- [ours] CONSEQUENCE for the CORRECT tool: because bare backflow N_I is quantum/classical-degenerate, a
  genuine quantum-memory claim needs a functional that EXCEEDS a classical-memory bound — i.e. Bäcker's
  E#[χ1] < E[χ2] (entanglement-of-assistance '#' form, 2310.01205 Thm 1), NOT a bare revival. Our dropped-'#'
  "Control 3b" witnessed memory/non-Markovianity, not quantum memory — precisely the failure mode Nakagawa's
  quantum/classical equivalence predicts.
- [ours] LIMITATION re Flag #1 (does quantum memory live on the PASSIVE syndrome record, or only in the
  active single-time channel-tomography object?): Nakagawa is a CHANNEL-object / single-observable-trajectory
  statement (I(t) is a function of the instantaneous observed state along a decay trajectory). It does NOT
  address a multi-time PASSIVE record witness. So this paper closes "revival ≠ quantum" but does NOT supply
  the passive-record quantum-memory witness — that gap must be filled by a process-tensor / multi-time source.

## Decisive verbatim quotes [paper]

- "Memory effects in non-Markovian dynamics are often diagnosed either via quantum-correlation revivals or
  via non-monotonic classical information measures, yet a unified minimal framework comparing their 'backflow
  phases' is still lacking." (Abstract)
- "The two signatures—quantum entanglement revival and classical entropy overshoot—are unified by the
  backflow functional."
- "...indicating that the boundary originates from the kernel's mathematical structure rather than from
  quantumness per se."
- "This observation closes the 'comparison symmetry' gap by showing that the α≃1/2 boundary is a kernel-driven
  feature that appears on both the quantum and classical sides once the same memory kernel is imposed."
- "The Markovian limit α=1 reproduces an exponential kernel with a single timescale, while 0<α<1 yields
  long-tailed memory encoded by the Mittag–Leffler function E_α(·)."
