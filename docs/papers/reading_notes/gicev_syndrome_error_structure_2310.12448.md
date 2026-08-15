# Full-text review — Gicev, Hollenberg, Usman, "Quantum computer error structure probed by quantum error correction syndrome measurements" (arXiv:2310.12448)

> **Provenance (2026-07-02): FULL-TEXT read (精读).** PDF (arXiv 2310.12448v2, 25 Mar 2024) → txt
> `outputs/papers/2310.12448.txt` (35 pages, PyMuPDF via theory-first fetch_and_extract). All §/Eq/Fig/Table
> refs from that text. Figures not pixel-extracted — figure facts = captions + colorbar ranges stated in text.

## Metadata [paper]
- Authors / affiliation: Spiro Gicev, Lloyd C. L. Hollenberg, Muhammad Usman — Univ. of Melbourne (School of Physics); Usman also Data61, CSIRO. **(NOT Harper — verified from the PDF byline, PAGE 1.)**
- Venue / status: arXiv:2310.12448v2 [quant-ph], 25 Mar 2024; published Phys. Rev. Research 6, 043249 (2024).
- Type: **Experiment** (real IBM superconducting devices) + analytic/simulation modelling.

## Executive summary [paper]
They run heavy-hexagon-code stabilizer/gauge-operator syndrome-measurement circuits (up to 23 qubits, 16
repeated cycles) on IBM transmon devices (ibmq_montreal, ibmq_toronto, ibmq_mumbai, ibm_geneva) and test them
against the noise assumptions behind QEC threshold calculations. Data is **inconsistent with uniform
depolarizing noise**, favouring **biased (Z-biased) and inhomogeneous** noise models. Spatial-temporal
correlations of Z-stabilizer detection events (via the Chen-et-al./Google p_ij correlation matrix) show
**significant temporal correlation** in detection events plus additional off-structure correlations
attributed to leakage/cross-talk/asymmetric readout. Headline framing: real QEC-circuit noise has non-trivial
structure that simplified models miss — motivating noise-tailored codes/decoders.

## Method (deep) [paper]
Detection-event spatial-temporal correlation object (Eq. 5 in main text, Eq. C6 in appendix — identical):

```
p_ij = ( <x_i x_j> - <x_i><x_j> ) / ( (1 - 2<x_i>)(1 - 2<x_j>) ),   with p_ii := 0
```

- x_i, x_j are binary syndrome-bit **detection events** (values 0/1). Row/column index i = nS + c (n = #cycles,
  c = cycle, S = stabilizer). [paper, PAGE 10 / PAGE 20]
- Cited "[43]" for the formula = **Z. Chen et al., "Exponential suppression of bit or phase errors with cyclic
  error correction," Nature 595, 383 (2021)** — i.e. this is the standard Google/Fowler surface-code p_ij
  detection-correlation matrix, NOT a bespoke object. [paper, PAGE 12]
- The numerator is the plain **covariance** <x_i x_j> − <x_i><x_j>; the denominator is a normalization by the
  single-event "signal" factors (1 − 2<x_i>). The paper further gives
  `<x_i x_j> = ( <x_i> + <x_j> − <x_i ⊕ x_j> ) / 2` (Eq. C7) as the way to compute the joint rate. [PAGE 20]

Classes of structure the matrix is designed to expose (from simulation expectation): **Space-like (S)** =
simultaneous changes of operators sharing a qubit; **Time-like (T)** = subsequent changes of the same operator
(measurement error then correction); **Space-time-like (ST)** = shared-qubit operators across two subsequent
cycles; **C** = correlated multi-error entries (expected to vanish). Symbols S/T/ST/C annotate example matrix
entries in Fig. 6. [paper, PAGE 10]

## The MECHANISM (for implementation) [paper → ours]
Noise models fitted: uniform depolarizing (rejected), **Z-biased** depolarizing, and **inhomogeneous**
(per-qubit / per-gate) depolarizing sampled log-normally. The correlation matrix itself is a *diagnostic*, not
a channel: the "mechanism" they infer is inhomogeneous + biased Pauli noise plus unmodelled
leakage/cross-talk/asymmetric-readout contributions producing off-structure correlations. Our repo already has
the p_ij object family (Fowler correlation) in the detector-correlation / DEM tooling — this paper is a
grounding citation for the **signed** p_ij on real IBM heavy-hex data.

## The OBSERVABLE / metric [paper]
The observable IS Eq. 5 / C6 above — the Chen-et-al. detection-event correlation matrix p_ij. **Sign
structure (the decisive fact for us):**

- The numerator is a **covariance** and the denominator can be positive or negative, so **p_ij is a SIGNED
  quantity, not a probability**. It is NOT structurally ≥ 0. There is no coincidence-probability floor at 0.
- Every rendered correlation matrix in the paper uses a **symmetric diverging colorbar from −0.04 to +0.04
  centered at 0.00** (Fig. 6, Fig. 22, Fig. 23), i.e. the authors' own plotting convention explicitly admits
  and displays **both signs**. [paper, PAGE 10 caption / PAGE 34]
- They explicitly report an entry going the "wrong" (decorrelating) way: operator-4 shows *lower* correlations
  than simulation, interpreted as extra processes that "act to decorrelate detection events which are expected
  to be strongly correlated." [paper, PAGE 10]

## Findings + numbers [paper]
- Uniform depolarizing model rejected; **Z-biased + inhomogeneous** models fit better. [PAGE 10–11]
- **Significant temporal correlation** in Z detection events; all three structured classes (S, T, ST) present
  on ibmq_montreal, plus significant **additional off-structure correlations** (attributed to leakage,
  cross-talk, asymmetric readout). [PAGE 10]
- Correlation-matrix colorbar range ±0.04; entries with |p_ij| > 0.05 clipped (Fig. 6/22/23 captions). [PAGE 10, 33, 34]
- Full inhomogeneous 1q/2q depolarizing model is fully determined if all detection-event correlations are used;
  extractable to arbitrary precision for error rates below ~1% with enough shots. [PAGE 10]

## Limitations [paper]
- No dynamical decoupling used (flagged as an extension). [PAGE 11]
- Only ~2 effective cycles for some analyses ⇒ space-time-like correlations are the weakest / hardest to see. [PAGE 10]
- Interpretation of off-structure correlations (leakage/cross-talk/asymmetric readout) is **suggestive, not
  identified** — they do not isolate a single mechanism. [PAGE 10]
- Framing is entirely **classical noise-model discrimination** (depolarizing vs biased vs inhomogeneous vs
  correlated). **No** quantum-bath-vs-classical-bath discriminator, **no** sign-based quantum-vs-classical
  argument anywhere. Non-Markovianity is not invoked; "temporal correlation" is read as ordinary time-like
  measurement/error correlation, not CP-divisibility breaking.

## Relevance to AI_QEC / Bone-C premise [ours]
Decisive empirical test for our **Bone C** premise ("all documented QEC-hardware detection-event correlations
are POSITIVE/bunching; a negative short-lag conditional detection statistic would be a novel quantum-vs-classical
discriminator"). Verdict — **MIXED, and it forces a correction to the premise as literally stated:**

1. **Object is NOT ≥0 by construction.** [ours] Their p_ij (= Chen-et-al. Nature-595 formula) is a signed
   covariance-ratio, and the authors *plot* it on a ±0.04 diverging scale. So the claim "negative can't arise by
   construction" is FALSE for the field-standard object — negative p_ij is representable and the community
   already displays it that way. Any Bone-C novelty must be framed as *observing / interpreting* an anti-bunched
   value, NOT as "the object can't go negative elsewhere."
2. **They do NOT report a headline negative/anti-bunched detection correlation.** [paper] Their positive
   findings are all excess/positive structured correlations (S/T/ST) plus positive off-structure excess. The
   only "opposite-sign-ish" statement is *decorrelation* (operator-4 lower-than-expected), which is a
   *reduction of expected positive* correlation, not a reported negative/anti-bunched short-lag entry with a
   quoted negative value. So this paper does not itself furnish a counterexample to "documented correlations are
   positive/excess" — but it also doesn't affirmatively rule negatives out (colorbar admits them).
3. **They never propose a sign-based quantum-vs-classical discriminator.** [paper] Confirmed absent — their
   entire interpretive frame is classical noise-model selection (biased/inhomogeneous/correlated Pauli).

Net: our premise's *spirit* (no one has reported a negative short-lag detection correlation as a
quantum-vs-classical signature) survives here; but the *letter* ("negative cannot arise by construction / the
object is a probability ≥0") is **refuted** — the standard object is signed and routinely plotted with a
diverging ± colorbar. Reframe Bone C accordingly before it is load-bearing.

## How to use / trust + open questions [ours]
- Trust: full-text read; figure sign-ranges taken from captions/colorbar text, not pixel extraction — the
  ±0.04 diverging colorbar is stated in the caption text, so the "object is signed" conclusion is solid.
- Open: this paper is IBM heavy-hex, ≤2 informative cycles; it does not resolve whether any *individual* p_ij
  entry is measured NEGATIVE with significance. To close Bone C we still need a source that either (a) tabulates
  a negative p_ij entry, or (b) confirms all reported values are ≥0 — this paper leaves that specific point
  open (structured entries positive; off-structure "additional" entries sign unquoted; decorrelation reported
  qualitatively). GT-feasibility: the p_ij formula is directly computable from our detection-event records.
