# Full-text review — Regev, Dilley, Delgado & Bennink, "Closed form logical error rate approximations for surface codes" (arXiv:2605.03054)

> **Provenance (2026-07-02): FULL-TEXT read (精读).** PDF fetched via
> `.claude/skills/theory-first/scripts/fetch_and_extract.py 2605.03054` → txt
> `outputs/papers/2605.03054.txt` (12 pages, PyMuPDF). All §/Eq/Fig/Table refs from that text.
> Figures not pixel-extracted — figure facts = captions + numbers stated in text.

## Metadata [paper]
- Authors / affiliation: Shaked Regev (Oak Ridge National Laboratory), Daniel Dilley (Argonne
  National Laboratory), Andrea Delgado (ORNL), Ryan Bennink (ORNL). `===== PAGE 1 =====`
- Venue / status: arXiv:2605.03054v1 [quant-ph], compiled May 6, 2026 (posted 4 May 2026). Not yet
  a journal paper. DARPA Quantum Benchmarking Initiative funding.
- Type: theory / combinatorics (path-counting algorithm + closed-form LER approximation; no hardware
  data, no decoder simulation beyond validating the count).

## Executive summary [paper]
A path-counting method for the **logical error rate (LER)** of unrotated and rotated surface codes.
The core assumption is **i.i.d. Pauli errors** (independent in space AND time). They enumerate the
minimum-length logical paths (MLLPs), count the number `C_{d_e}` of `d_e = (d+1)/2`-error
configurations that cause a logical error (independent of `p`), then plug in `p` to get
`L = Σ_k C_k p^k (1-p)^{d²-k}` (Eq. 1). They prove `L ≈ P_{d_e}` when `p d² ≪ 1`, recovering the
Fowler scaling law `L ≈ A (p/p_th)^{d_e}` (Eq. 4) with fitted `A ≈ 0.209`, `p_th ≈ 0.0733` (rotated).
Section 5 extends this to (5.1) a **single global correlated mode** (D-component Bernoulli mixture,
cosmic-ray/temperature style) and (5.2) different X/Z rates — NOT to arbitrary spatiotemporal
covariance.

## Method (deep) [paper]
Base LER (i.i.d.), `===== PAGE 4 =====`, Eq. (1):

```
L = Σ_{k=0}^{d²} C_k p^k (1-p)^{d²-k}  :=  Σ_{k=0}^{d²} P_k
```

`C_k` = number of distinct k-qubit physical error configurations that produce a logical error;
`C_k = 0` for all `k < d_e`. The whole apparatus is combinatorial path counting on the lattice
(Algorithm 1, `===== PAGE 8 =====` — a memoized recursive MLLP counter). The closed-form scaling is
`L ≈ A (p/p_th)^{d_e}` (Eq. 4, `===== PAGE 5 =====`), a **power law in `p/p_th`** — NOT a Fourier /
characteristic-function object.

Global-correlated extension (Section 5.1), `===== PAGE 10 =====`, Eqs. (9)–(10):

```
p_dep = Σ_{j=1}^{D} ρ_j p_j ,   Σ_j ρ_j = 1                                    (9)
L_dep = Σ_{k=d_e}^{N} C_k Σ_{j=1}^{D} ρ_j p_j^k (1-p_j)^{N-k}                  (10)
```

i.e. the physical error rate is drawn from **one of D Bernoulli distributions, each applied to ALL
qubits simultaneously** — a scalar mixture over a global environment state, not a covariance.

## The MECHANISM (for implementation) [paper → ours]
Not applicable as a mechanism we would implement — this is an evaluator-side LER estimator, not a
teacher channel. The relevant object for our comparison is the **noise model class** it covers:
i.i.d. Pauli (default) + a single global correlated mode (Section 5.1). No per-pair / per-lattice
correlation structure enters `C_k`; `C_k` is purely geometric and `p`-independent.

## The OBSERVABLE / metric [paper]
The logical error rate `L = f(p, d)` (Table 1, `===== PAGE 4 =====`). Also a measurement-error LER
`L_M` (Eq. 8, `===== PAGE 9 =====`) under i.i.d. measurement errors `p_m`. **No correlation-sensitivity
metric** of the form ∂(LER)/∂(correlation) or ∂(floor)/∂f is defined anywhere. The Section 5.1
"design implication" is a discrete/asymptotic-dominance argument (worst-case `p_1` dominates at large
`d`), not a derivative w.r.t. a correlation parameter.

## Findings + numbers [paper]
- Fitted rotated-code closed form: `A ≈ 2.09·10⁻¹`, `p_th ≈ 7.33·10⁻²` (`R² = 1 − 6.32·10⁻⁶`),
  Fig. 4 / `===== PAGE 7 =====`.
- Unrotated: `A ≈ 1.62`, `p_th ≈ 2.49·10⁻¹`, `===== PAGE 7 =====`.
- Upper/lower bounds on `C_{d_e}` (Eqs. 5–6), gap is large; `p d² ≪ 1` ⇒ `L ≈ P_{d_e}`
  (`===== PAGE 9 =====`, Eq. 7).
- Measurement: `M = d` repetitions suffice for rotated (not unrotated) codes (`===== PAGE 10 =====`).
- Global-correlated (5.1): at large enough `d`, the **worst-case component `p_1` dominates** the LER
  scaling, modulated by `ρ_j` (`===== PAGE 10-11 =====`).

## LOAD-BEARING VERBATIM QUOTES

Noise model — i.i.d., Markovian:

`===== PAGE 3 =====`
> "We assume that (i) our decoder is classical and perfect, (ii) unless stated otherwise, physical
> errors are independent (in space and time) and identically distributed (i.i.d) Pauli errors, i.e.
> they are Markovian, and (iii) measurement errors take a certain form (see Section 4)."

`===== PAGE 4 =====`
> "We consider a surface code with d2 data qubits, where each qubit experiences an independent and
> identically distributed (i.i.d.) error with probability p."

The correlated extension is a SINGLE GLOBAL mode (mixture over a global environment), NOT arbitrary
covariance:

`===== PAGE 10 =====`
> "5.1. Global correlated errors — We can extend the approximation of the logical error to a simple
> global correlated model. Suppose that instead of p being drawn from a Bernoulli distribution, it is
> drawn from one of D Bernoulli distributions, each occurring with a certain probability for all
> qubits simultaneously."

`===== PAGE 10 =====`
> "This type of distribution models errors occurring due to unfavorable environments such as those
> with fluctuating temperatures, manufacturing line defects, or in the presence of cosmic rays [8]."

Explicitly defers arbitrary space/time dependencies to FUTURE work (i.e. does NOT own it):

`===== PAGE 11 =====` (Section 6, Summary and future work)
> "Our method of counting configurations is only valid when the qubits are identical, but it is not
> necessary for them to be independent. Future work may consider more general qubit dependencies in
> space and time, along with more general measurement errors."

## The four adjudication questions [paper]

1. **Noise model — i.i.d. or correlated?** Default is **i.i.d. Pauli, independent in space AND time,
   Markovian** (PAGE 3, PAGE 4, verbatim above). Correlated noise appears ONLY in Section 5.1 as a
   **single global mode**: a scalar Bernoulli mixture `p_dep = Σ_j ρ_j p_j` applied to **all qubits
   simultaneously** (Eq. 9). This is exactly the cosmic-ray/temperature "global correlated" style —
   NOT an arbitrary spatiotemporal covariance. There is no per-qubit / per-pair correlation matrix.

2. **Interpolation parameter between independent and correlated?** **NO.** There is no continuous
   correlation-strength / covariance-indexed family. The Section 5.1 model has discrete environment
   components `{ρ_j, p_j}`; the takeaway is a dominance/worst-case argument (`p_1` dominates at large
   `d`), not an interpolation. No parameter continuously tunes independent → fully-common.

3. **Is the functional a finite Fourier sum of Gaussian characteristic functions of a covariance Σ?**
   **NO.** The closed form is a **combinatorial / power-law / union-bound** object:
   `L = Σ_k C_k p^k (1-p)^{d²-k}` (Eq. 1) with the geometric count `C_k`, giving `L ≈ A (p/p_th)^{d_e}`
   (Eq. 4). No characteristic functions, no Gaussian covariance, no Bochner/Fourier structure anywhere.

4. **Device sensitivity metric ∂(LER)/∂(correlation)?** **ABSENT.** No derivative of LER with respect
   to any correlation parameter is defined. The only "design metric" flavor is Section 5's discrete
   worst-case-dominance reasoning and the X/Z budget optimization (5.2) — neither is a
   ∂(floor)/∂(correlation) sensitivity.

## Limitations [paper]
- i.i.d. Pauli, perfect classical decoder, `p d² ≪ 1` regime (else only a lower bound).
- Only counts the LEADING `C_{d_e}` term exactly; higher `C_k` (k > d_e) deferred to future work.
- Correlation handled only as a single global scalar mode (Section 5.1); arbitrary space/time
  dependencies explicitly named as future work (Section 6, quote above).
- No hardware data; validated against the Fowler scaling law and its own path-count, not against
  independent decoder Monte Carlo beyond agreement fits.

## Relevance to our Bone #2 [ours]
Our Bone #2 = an **exact interpolating logical-failure functional for ARBITRARY spacetime Gaussian
covariance Σ** (a finite Fourier sum of Gaussian characteristic functions of Σ), generalizing Clader
et al.'s independent-vs-fully-common binary endpoints, PLUS a device metric ∂(floor)/∂f|₀.

This paper does **NOT** pre-empt any of that:
- Its object is combinatorial/power-law (`A (p/p_th)^{d_e}`), **not** a characteristic-function /
  covariance-indexed Fourier sum. (Q3)
- Its correlated model is a **single global mode** (cosmic-ray/temperature scalar mixture), **not**
  arbitrary spatiotemporal covariance Σ. (Q1)
- It has **no interpolation parameter** between independent and correlated. (Q2)
- It defines **no ∂(LER)/∂(correlation)** device-sensitivity metric. (Q4)
- It explicitly names "more general qubit dependencies in space and time" as **future work**
  (Section 6) — i.e. the arbitrary-covariance interpolant is an OPEN direction it does not claim.

**Bottom line: Bone #2's sliver survives intact.** The freshest 2026 closed-form competitor covers
i.i.d. + a single global correlated mode only, uses a combinatorial power-law form (not a
Gaussian-characteristic-function Fourier sum), has no independent↔correlated interpolant, and has no
∂(floor)/∂f metric.

## How to use / trust + open questions [ours]
- Trust: full-text read (12 pp), all quotes verbatim from the extracted txt; figures not pixel-extracted
  (figure facts = captions/text only, which is sufficient here — the noise-model and functional-form
  claims are all in prose/equations, not figures).
- Cite this note in the Bone #2 pre-registration as the prior-art adjudication for the 2026 closed-form
  competitor: covers i.i.d. + global-mode, NOT arbitrary-covariance interpolation, NOT a
  characteristic-function functional, NO sensitivity metric.
- Open question for us: their Eq. (1) `L = Σ_k C_k p^k (1-p)^{d²-k}` is the i.i.d. limit our
  interpolating functional must reduce to at Σ → diagonal — a useful consistency anchor, NOT a
  competing claim.
