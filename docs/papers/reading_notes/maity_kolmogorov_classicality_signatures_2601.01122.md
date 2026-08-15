# Full-text review — Maity, Ghoshal, Onggadinata, Koh, "Non-Markovian and Thermodynamic Signatures in the Classicality Assessment via Kolmogorov Consistency" (arXiv:2601.01122)

> **Provenance (2026-07-02): FULL-TEXT read (精读).** PDF (arXiv:2601.01122) → txt
> `outputs/papers/2601.01122.txt` (21 pages, PyMuPDF via theory-first fetch_and_extract). All §/Eq/Fig
> refs from that text. Figures not pixel-extracted — figure facts = captions + numbers stated in text.

## Metadata [paper]
- Authors: Arghya Maity¹, Ahana Ghoshal², Kelvin Onggadinata¹, Teck Seng Koh¹.
  (¹ Nanyang Technological University, Singapore; ² Universität Siegen, Germany.) — authors/title
  in the prompt VERIFIED against page 1.
- Venue / status: arXiv:2601.01122, January 2026. Preprint (no journal stated).
- Type: theory (exact analytics on a single-qubit open-system model + supporting numerics).

## Executive summary [paper]
The paper defines a scalar Kolmogorov-consistency-condition (KCC) violation measure for a two-time
measurement record on a single dissipative qubit, derives it exactly, and links its magnitude to
non-Markovianity (RHP/BLP), quantum mutual information, the Fano factor, heat/entropy production, and
to Leggett–Garg + Kirkwood–Dirac negativity. The headline physical claim: KCC violation is a
competition between Markovian damping (positive decay rates → suppress) and non-Markovian backflow
(negative decay rates → enhance), all traced to a single coherence-decay factor. It is a
single-scalar classicality quantifier, not a structured additive decomposition.

## Method (deep) [paper]
- **KCC (general), Eq. (1)** — for outcomes x₁…xₙ at t′₁<…<t′ₙ, marginalizing over any subset must
  reproduce the correct joint of the rest.
  ===== PAGE 2 =====
  ```
  Specifically, for any k <= n,
    sum_{x_k} P(x_n,...,x_{k+1}, x_k, x_{k-1},...,x_1)
      = P(x_n,...,x_{k+1}, x_{k-1},...,x_1).   (1)
  ```
- **The KCC-violation MEASURE, Eq. (2)** — the two-time scalar, marginalizing over the EARLIER
  outcome (the nontrivial disturbance test):
  ===== PAGE 2 =====
  ```
  For simplicity, one can consider the two-time case (t'_1, t'_2), where the violation is quantified as
    viol_{x2}(t'_1, t'_2) = | sum_{x1} P(x2, x1) - P(x2) | .   (2)
  ```
  A nonzero value signals breakdown of a classical stochastic description. This is a single
  absolute-difference scalar per outcome — one number, not a two-term structure.
- **Model, Eqs. (7)–(10):** single qubit Hsys = (ℏ/2)ω₀σ_z coupled to a bosonic reservoir through
  HI ∝ ∫dω′ χ(ω′)(σ₊a + σ₋a†) — an amplitude-damping-type (σ±) coupling with a super-Ohmic spectral
  density J(ω)=α ω^s e^{−ω/ω_c}, s>1. Exact time-local master equation with dissipator
  D[ρ] = Σ Γ_ε L_{σ₋}[ρ] + γ̃_ε L_{σ₊}[ρ]; rates Γ_ε, γ̃_ε go temporarily negative in the
  non-Markovian regime.
- **Evaluated violation, Eqs. (13)–(14):** viol_{u1} = |p_{u1}(t2) − Π_{u1}(t2)| where Π is the
  classical mixture of conditional probabilities p_{u1}(t1)p_{u1}(t2|u1)+p_{u2}(t1)p_{u1}(t2|u2).
  Substitution gives viol = |P(t1,t2) + C(t1,t2)| with a **population term** P (∝cos θ) and a
  **coherence term** C (∝sin θ) — see "OBSERVABLE" below; this is the closest thing to a split.

## The MECHANISM (for implementation) [paper → ours]
Single dissipative qubit, σ± bosonic-bath coupling, super-Ohmic J(ω)=α ω^s e^{−ω/ω_c}, with
time-local decay rates from second-order weak-coupling (Eq. 6). Non-Markovianity enters as negative
Γ_ε/γ̃_ε intervals. This is a generic open-qubit / independent-boson-adjacent teacher — NOT a
stabilizer or QEC record model. [ours] Not directly reusable as a mechanism; relevant only as a
classicality-quantifier we must position Bone A against.

## The OBSERVABLE / metric [paper]
The metric is `viol` (Eq. 2). For the worked cases it collapses to a coherence-amplitude scalar:

===== PAGE 4 =====
```
For this case, the Kolmogorov-consistency violation for outcome |+> is
  viol_+(t1,t2) = (1/2) exp(-1/2 G(0,t2)) | sin(w0 t1) sin(w0 (t2 - t1)) |   (15)
  with G(t0,t) := int_{t0}^{t} lambda(s) ds, and lambda(s) := Gamma_eps(s) + gamma-tilde_eps(s).
```

The positive/negative-rate "factorized form" — a PRODUCT (multiplicative), not a sum:

===== PAGE 4 =====
```
Substituting into Eq. (16) yields the factorized form
  viol_+(t1,t2) = (1/2) e^{-1/2 M(t2)} | sin(w0 t1) sin(w0(t2 - t1)) | x e^{+1/2 N(t2)} .   (18)
```
where M(t2)=∫λ₊, N(t2)=∫λ₋. Text: "e^{−½M} accounts for the decay of coherence due to positive
decay rates, while … e^{+½N} quantifies the enhancement … from non-Markovian backflow." So the
structure is coherence-factor × unitary-oscillation × backflow-factor — a factorization of ONE
coherence scalar, not an additive floor+modulated pair.

And the direct coherence-proportionality (page 7):

===== PAGE 7 =====
```
viol_+(t1,t2) = |c(t2)| | sin(w0 t1) sin[w0(t2 - t1)] | .
Here, |c(t2)| = (1/2) e^{-1/2 G(0,t2)} (see Eq. (A5)). Thus, the KCC violation is directly
proportional to the coherence amplitude of the state for fixed w0, t1, and t2.
```

## Findings + numbers [paper]
- Exact viol for the dissipative qubit; suppressed at long times because integrated positive rate
  exceeds negative (numerics, two scenarios, §V/conclusion).
- viol places a quantitative LOWER BOUND on system–reservoir mutual information (Eq. 29 region).
- Linear two-sided bound of viol by the BLP non-Markovianity measure (Eq. 27): slopes between S/4
  and S with a common offset. Ties to RHP, Fano factor, heat, entropy production, LGI, KD-negativity.
- Grep audit: `stabilizer|error correct|surface code|syndrome|repetition code` → **0 occurrences**.
  `additive|floor|kill switch|measurement-independent|measurement-modulated` → **0 occurrences**.

## Limitations [paper]
- Single qubit, two-time (n=2) record; weak-coupling second-order rates; Born approximation for the
  mutual-information relation. No repeated/many-round record, no code, no stabilizer group.
- σ± amplitude-damping coupling is present in the model, but the paper NEVER isolates a
  non-unital/amplitude-damping "floor" as a separate additive term — viol is reported as a single
  coherence-proportional scalar (worked cases have viol=0 in the pointer basis; violation is
  MANUFACTURED by measuring off-basis, sin θ term).

## Relevance to Bone A [ours]
- **Does NOT pre-empt Bone A's additive decomposition.** Their measure (Eq. 2) is a single scalar
  `|Σ P(x2,x1) − P(x2)|`. The only structure they expose is (i) the P (population, cos θ) + C
  (coherence, sin θ) split of Eq. (13)-substitution — a trig/basis split, NOT a
  measurement-independent-floor + measurement-modulated split — and (ii) the MULTIPLICATIVE
  factorization Eq. (18) into damping × oscillation × backflow. Neither is our additive
  (non-unital floor + measurement-modulated part) with independent kill switches.
- **No measurement-INDEPENDENT part.** Their violation is engineered by choosing a
  measurement basis OFF the pointer basis; in the pointer basis viol vanishes. There is no
  measurement-independent non-unital floor that survives when the modulated part is switched off —
  the opposite regime from Bone A's floor kill switch.
- **No non-unital / γ/2 / g² floor object.** σ± coupling appears in the model but no
  amplitude-damping constant or bosonic-g² floor is separated out as a term. Absent — confirmed.
- **No QEC / stabilizer contact.** Zero mentions (grep-confirmed). Single-qubit, n=2 only.
- What we could cite it FOR: it is prior art that KCC-violation ↔ non-Markovianity ↔ coherence
  backflow, and the BLP/RHP + thermodynamic bracket. Bone A must acknowledge KCC-violation as an
  established scalar classicality quantifier and position our decomposition as the new object (the
  additive split + repeated-measurement/stabilizer record), not the quantifier itself.

## How to use / trust + open questions [ours]
- Trust: full-text 精读; figures not pixel-extracted (figure facts = captions/text). Equations
  transcribed verbatim from the txt with page anchors.
- Open questions: none blocking — the paper's object is clearly a single scalar. If Bone A wants to
  claim novelty of the additive split, cite Eq. (2) (single scalar) + Eq. (18) (multiplicative, not
  additive) as the contrast.
- GT-feasibility: their exact viol on a single qubit is trivially reproducible; irrelevant to our
  stabilizer-record GT.
