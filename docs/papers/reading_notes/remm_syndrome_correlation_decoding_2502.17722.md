# Full-text review — Remm, Lacroix, Bödeker, Genois, Hellings, Swiadek, Norris, Eichler, Blais, Müller, Krinner, Wallraff, "Experimentally Informed Decoding of Stabilizer Codes Based on Syndrome Correlations" (arXiv:2502.17722)

> **Provenance (2026-07-02): FULL-TEXT read (精读).** PDF (arXiv 2502.17722v1, 24 Feb 2025) → txt
> `outputs/papers/2502.17722.txt` (23 pages, PyMuPDF via theory-first fetch script). All §/Eq/Fig/Table refs
> from that text. Figures not pixel-extracted — figure facts = captions + numbers stated in text.

## Metadata [paper]
- Authors: A. Remm, N. Lacroix (ETH Zurich); L. Bödeker, M. Müller (FZ Jülich / RWTH Aachen); E. Genois,
  A. Blais (Sherbrooke); C. Hellings, F. Swiadek, G. J. Norris, C. Eichler, S. Krinner, A. Wallraff
  (ETH Zurich / ETH-PSI Hub). ETH Zurich–led.
- Venue / status: arXiv:2502.17722v1 (24 Feb 2025); published Phys. Rev. Research 8, 013044 (2026).
- Type: experiment (17-qubit superconducting d=3 surface code, device of Ref. 4 = Krinner et al.) + the
  supporting analytical estimator + a Clifford (PECOS) simulation baseline.

## Executive summary [paper]
Given raw syndrome data from running the QEC circuit itself, estimate the **probability of each independent
error event** (an error with a **unique syndrome signature**) directly from higher-order syndrome
correlations — no theoretical device error model, no separate calibration experiment. The headline is a
**generalized analytical inversion formula** (Eq. 10) that maps products of syndrome-correlation moments
`⟨σ̃_{j1}…σ̃_{jm}⟩` to the per-event probability `p_{i1,…,in}` of an error flipping the n syndrome elements
`{i1,…,in}` — a generalization of Spitz et al. [48] (which only handled ≤2-element signatures) to arbitrary
signature weight. Applied to the d=3 code it recovers weights for a (correlated) MWPM decoder without a
theory model, and diagnoses X vs Y asymmetry (crosstalk) and long multi-cycle correlated events (up to 8
cycles) attributed to data-qubit leakage.

## Method (deep) [paper]

**The estimated object.** Each independent error process is a **two-valued Bernoulli event** with a unique
signature. Abstract, Sec. IV, and Appendix E fix this:

===== PAGE 1 =====
> "we present an experimental approach guided by a novel analytical formula to characterize the probability
> of independent errors using correlations in the syndrome data"

===== PAGE 1 =====
> "We present an analytical method to calculate the probability of any independent error event that has a
> unique signature in the stabilizer measurement outcomes, based on the higher-order correlations in the
> experimental syndrome data."

**The general inversion formula (Eq. 10, PAGE 7).** For an error flipping n syndrome elements
`σ_{i1},…,σ_{in}`, with `σ̃_i = 1 − 2σ_i ∈ {+1,−1}`:

===== PAGE 7 =====
> "the probability pi1,...,in, that an error that flips n syndrome elements σi1, . . . , σin oc- curs, can be
> calculated as
>   pi1,...,in = 1/2 − 1/2 · [ PROD_{{j1,...,jm} ⊆ {i1,...,in}} ⟨σ̃j1 . . . σ̃jm⟩^{(−1)^{m−1} 2^{−(n−1)}} ]
>               · PROD_{{j1,...,jm} ⊃ {i1,...,in}} (1 − 2 p_{j1,...,jm})"

The numerator is a signed geometric product over all **subsets** of the signature (the moments actually
measured); the denominator product over **supersets** renormalizes for higher-weight events that also flip
this subset. The ≤2-element special case (Eq. E1a, PAGE 17) reproduces Spitz et al. [48]:
`p_ij = 1/2 − 1/2 · sqrt( ⟨σ̃_i⟩⟨σ̃_j⟩ / ⟨σ̃_i σ̃_j⟩ )`, and Eq. E2/E3 give the explicit ≤4- and ≤6-element forms.

**The covariance used as input (Eq. 9, PAGE 6):**
===== PAGE 6 =====
> "C(∆m)_{Ai,Aj} = ⟨ σ^{Ai}_m σ^{Aj}_{m+∆m} ⟩ − ⟨σ^{Ai}_m⟩⟨σ^{Aj}_{m+∆m}⟩"
This is the covariance of **binary (0/1) detector-difference syndrome elements** across auxiliary qubits and
cycle-separations — a discrete detector-moment, not a continuous field covariance.

**The independence assumption underpinning the inversion (Appendix E, PAGE 18):**
===== PAGE 18 =====
> "where Fi1,...,in = ±1 represents the underlying random variable that indicates whether the error that
> flips syndrome elements {i1, . . . , in} has happened (−1) or not (+1). ... We further assume that the error
> processes are independent, that is ⟨Fi1,...,inFj1,...,jm⟩ = ⟨Fi1,...,in⟩⟨Fj1,...,jm⟩ if {i1,...,in} ≠ {j1,...,jm},
> and that the probability of each error happening is given by pi1,...,in = (1 − ⟨Fi1,...,in⟩)/2."

So the generative model is: a set of **independent ±1 Bernoulli fault variables `F`, one per distinct
signature-set**, each with a Bernoulli probability `p = (1−⟨F⟩)/2`. Eq. 10 inverts the syndrome moments to
those Bernoulli probabilities. Validated numerically on artificial datasets with events triggering up to 12
syndromes (Fig. 12, PAGE 18).

## The MECHANISM (for implementation) [paper → ours]
Not a physical noise mechanism — an **estimator**. Input: binary syndrome-element tensor `σ^{Ai}_m` from N=16
cycles × (d²−1) stabilizers × 4 logical states, ~54k post-selected shots each (500k acquired, leakage/
non-ground-state runs discarded, PAGE 6). Output: per-cycle Bernoulli probability for each enumerated
signature (116 Pauli-derived + 4360 "C" highly-correlated leakage-class signatures, PAGE 7–8). These `p`
become MWPM edge weights via `w = −ln((1−A)^{-1} − 1)` (Eq. 4, PAGE 5). Enumeration required because the
`2^124` full signature space is infeasible (PAGE 7). To avoid negative-probability bias, all highly-correlated
super-signatures must be included in the denominator product (Appendix F, PAGE 18: a worked 3-node example
where omitting `p123` drives `p2, p3` negative).

## The OBSERVABLE / metric [paper]
The observable is the **discrete binary detector-difference syndrome element** `σ^{Ai}_m = (1 − s_{m−1}s_m)/2 ∈
{0,1}` and its n-point correlations `⟨σ̃_{j1}…σ̃_{jm}⟩`. Regime of informativeness: time-translation invariant
"bulk" cycles (first/last omitted, Eq. 5 + PAGE 6–7); errors assumed local (negligible covariance beyond
2 data qubits spatially, PAGE 7). Flagged INSUFFICIENT: the plain 2-point Spitz formula (Eq. E1) is
**biased** whenever higher-weight correlated processes exist — the paper's whole generalization exists to
correct that (Appendix F).

## Findings + numbers [paper]
- Per-cycle nonzero-syndrome rate ⟨σ⟩ = 0.165(17) (weight-4 stabs), 0.118(6) (weight-2) (PAGE 6).
- Error-class probabilities (Fig. 3b, PAGE 7) extracted vs Clifford-sim; T-class (aux dephasing + readout)
  dominant; correlated CZ bit-flips (M_XŶ) over-predicted by depolarizing sim vs experiment.
- Correlated MWPM (Y-aware, Appendix C): **no** significant d=3 improvement — "the logical error per cycle is
  not currently limited by Ŷ errors" (PAGE 5); expected to help at larger d.
- Long correlated events over up-to-**8 cycles** (C class, 4360 signatures), attributed to data-qubit leakage
  out of the computational subspace (PAGE 1, PAGE 8, Sec. V).
- X vs Y probability discrepancy used as a crosstalk/control-error diagnostic (simple T1/T2 models predict
  p_X = p_Y) (PAGE 2, PAGE 8–9).

## Limitations [paper]
- **Independent-events assumption** (Appendix E): distinct signature-sets are statistically independent
  Bernoulli variables; correlated/non-independent structure is not modeled beyond enumerating a bigger
  signature.
- Enumeration, not full inference: only pre-listed signatures (Pauli-derived + C class) are estimated; the
  full `2^124` space is infeasible (PAGE 7).
- Post-selection removes leakage/non-ground-state runs (PAGE 6).
- Time-translation-invariant bulk only; drift/edge cycles excluded (Eq. 5, Appendix I shows drift produces
  *apparent* correlations).
- Degenerate errors sharing a signature are **lumped** (see identifiability note below) — not separated.

## Identifiability / gauge — the load-bearing distinction for our Bone B [paper → ours]

The paper does **not** build an identifiability / blind-spot map. Where distinct physical errors share a
signature it **lumps them into one effective process** and estimates only the aggregate — a pragmatic
merge, not a functional-invisibility (gauge) theorem:

===== PAGE 5 =====
> "Physically, multiple distinct in- dependent errors can have the same syndrome signature. Since we infer
> probabilities directly from the syndrome data, these errors are indistinguishable and treated as a single
> process to construct the auxiliary-qubit graph."

===== PAGE 4 =====
> "the error prop- agating to three or four neighboring qubits is equivalent to errors on the complementary
> one or zero neighboring data qubits. Therefore, these errors are indistinguishable from phase flip errors
> on data qubits, which belong to the S_X̂|Ẑ class."

That is the full extent of "invisibility" here: degenerate-signature lumping (a stated modeling choice), plus
the earlier remark that a bit flip is *equivalent* to a phase flip before the Hadamard (a circuit-frame
equivalence, PAGE 3). There is **no** characterization of which functionals of a noise object are provably
invisible, no gauge subspace, no rank/identifiability analysis, no moment-order→visible-functional hierarchy.
The "moment order" that appears (Eq. 10, E1/E2/E3 for n ≤ 2, 4, 6) is a **signature-weight bookkeeping** — the
order equals the number of syndrome elements the *enumerated* event flips — not a hierarchy stating which
functional of an underlying continuous field first becomes visible at each order. Confirmed absent: no
"Gaussian", "continuous", "field", "hierarchy", or formal "identifiability" language anywhere in the text
(grep-confirmed over the 23-page txt).

## Relevance to our Bone B [ours]
This is the **direct competitor / highest-order passive detector-moment estimator** and pinning its object
protects our Bone-B sliver:

- **Their estimated object is a DISCRETE, INDEPENDENT Bernoulli error-event probability** `p_{i1,…,in}` per
  **unique signature-set** (Eq. 10 + the F = ±1 Bernoulli independence assumption, PAGE 18). It is **not** a
  continuous spacetime Gaussian covariance Σ, and **not** a field. Their `C(∆m)` (Eq. 9) is a covariance of
  *binary detector bits*, used only as an intermediate the inversion consumes to output Bernoulli `p`s.
- **They do NOT own an identifiability / gauge / blind-spot map.** Degenerate errors are lumped by fiat
  (PAGE 5), not analyzed for which functionals are invisible. No theorem states which functional of any
  underlying object is recoverable at which moment order. Their "order" = signature weight (bookkeeping),
  not a Σ-functional-visibility hierarchy.
- **Reuse for us:** Eq. 10 / E1–E3 as an exact discrete-event moment-inversion baseline; the negative-
  probability-bias lesson (Appendix F) — omitting super-signatures biases lower-weight estimates — is a real
  numerical trap for any moment estimator we build; the covariance-matrix `C(∆m)` construction (Eq. 9) as a
  detector-moment substrate. The X-vs-Y-signature crosstalk diagnostic is a concrete moment→physics readout.
- **Correction it does NOT force on us, but sharpens:** our Bone-B theorem must be explicitly stated over a
  **continuous Gaussian covariance Σ** with a **gauge/blind-spot subspace** and a **moment-order → Σ-functional
  visibility hierarchy** — all three of which are exactly what Remm et al. lack. Their scope stops at
  estimating discrete independent events with unique signatures; degenerate/invisible continuous structure is
  out of scope for them.

## How to use / trust + open questions [ours]
- Trust: full-text 精读 (figures not pixel-extracted; Fig-3/4/12 facts taken from captions + in-text numbers).
- GT feasibility: Eq. 10 is exact and closed-form; validated by the authors on artificial data to
  signature-weight 12 (Fig. 12) — cheap to reimplement as a discrete-event baseline oracle.
- Open question for us: whether their independent-Bernoulli-event model can even *represent* a continuous
  Gaussian-covariance source (it cannot represent non-independent latent structure except by enumerating an
  ever-larger signature) — this is precisely the wedge our continuous-Σ + gauge framing occupies.

## Bottom line [ours]
Remm et al. estimate **discrete, independent Bernoulli error-event probabilities** (one per unique syndrome
signature) by **inverting binary detector-syndrome correlation moments** (Eq. 10, generalizing Spitz to
arbitrary signature weight). They do **NOT** map the identifiability / gauge / blind-spot structure of a
**continuous spacetime Gaussian covariance** from a detector-moment hierarchy — degenerate errors are merely
lumped, "order" = signature weight, and no continuous-field or functional-visibility theorem appears. Our
Bone B (which Σ-functionals are visible at which detector-moment order, and which are provably gauge-invisible)
therefore **survives as an open, uncontested sliver**.
