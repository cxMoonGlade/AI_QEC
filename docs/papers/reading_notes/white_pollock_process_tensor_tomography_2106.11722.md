# 精读 — White, Pollock, Hollenberg, Modi, Hill, "Non-Markovian Quantum Process Tomography" (arXiv:2106.11722)

> **Provenance (2026-07-03): FULL-TEXT 精读 of the conceptual + method CORE.** PDF → txt
> `outputs/papers/2106.11722.txt` (PyMuPDF, 32 pages, arXiv v2 24 May 2022; published PRX Quantum 3,
> 020344, 2022). Read in depth: §I (intro + QCVV placement), §II (the tomography hierarchy QST→QPT→PTT,
> the process-tensor definition + the restricted-PT active/passive boundary + the non-Markovianity
> measure + SPAM), §III opening (MLE-PTT motivation). §III MLE algorithm internals, §IV Markov-order
> mechanics, §V control results, and the appendices are present in the txt for deeper reads (cited
> below at the level the reconstruction needs). Tags: **[paper]** stated; **[ours]** our inference.

## Metadata [paper]
- **Authors.** G. A. L. White, F. A. Pollock, L. C. L. Hollenberg, K. Modi, C. D. Hill (Melbourne / Monash).
- **Venue.** arXiv:2106.11722v2; **PRX Quantum 3, 020344 (2022).** THE foundational process-tensor
  tomography (PTT) paper (the active-observation characterization of non-Markovian noise).
- **Type.** Theory + method + real-hardware demonstration (IBM Quantum superconducting devices).

## Executive summary [paper]
Introduces **process tensor tomography (PTT)** — the direct generalization of quantum process tomography
(QPT) to **non-Markovian (multi-time) processes**. A CPTP map (QPT) captures only two-time correlations
and FAILS when composed across multi-time processes with memory. PTT instead reconstructs the **process
tensor** `Υ_{k:0}` (Choi form), a many-body state that captures **arbitrarily strong temporal
correlations** by mapping all temporal correlations onto SPATIAL correlations across a sequence of
(possibly correlated) CPTP maps. The reconstruction is by **applying an informationally-complete basis of
control operations `{B_μ}` at each timestep** and measuring — active/designed observation. Contributions:
(1) MLE-PTT (physical, causal, efficient — base 24→10 ops/step); (2) a **necessary AND sufficient**
non-Markovianity measure (distance to the closest Markov process tensor); (3) **Markov-order truncation**
turning O(N^k) → O(k·N^ℓ); (4) demonstrated **noise-aware control** using non-Markovian correlations as a
RESOURCE to raise multi-time circuit fidelity on real devices.

## Method (deep) — the exact objects [paper]
- **Tomography hierarchy (Table I).** QST reconstructs `ρ` (`p_i = Tr[Π_i ρ]`); QPT reconstructs a channel
  Choi `Ê` (`p_ij = Tr[(Π_i ⊗ ρ_j^T) Ê]`); **PTT reconstructs the process tensor `Υ_{k:0}`**:
  `p_{i,μ⃗} = Tr[(Π_i ⊗ B_{μ_{k-1}}^{T} ⊗ ⋯ ⊗ B_{μ_0}^{T}) Υ_{k:0}]` (the **spatiotemporal Born rule**).
  Positivity `Υ_{k:0} ⪰ 0`; the affine (causality) condition `Tr_{out}[Υ_{k:0}] = I_in ⊗ Υ_{k-1:0} ∀k`
  (future controls cannot affect past statistics). Info of each column ⊂ the next.
- **Controlled dynamics (Eq. 6–7).** A k-step process driven by a sequence of CP control operations
  `A_{k-1:0} = {A_0,…,A_{k-1}}` gives `ρ_k(A_{k-1:0}) = tr_E[U_{k:k-1} A_{k-1} ⋯ U_{1:0} A_0(ρ^{SE}_0)]`;
  the process tensor is the map `T_{k:0}[A_{k-1:0}] = ρ_k(A_{k-1:0})`.
- **Linear-inversion construction (Eq. 8–9).** Expand each time-local op in a basis `A_j = Σ_μ α_μ B_μ_j`;
  measure `ρ_k^μ⃗ := ρ_k(B_{k-1:0}^μ⃗)` for the full spatiotemporal basis; then with the dual set
  `{Δ_μ}` (`Tr[B_μ Δ_ν]=δ`), `Υ_{k:0} = Σ_μ⃗ ρ_k^μ⃗ ⊗ Δ_{k-1:0}^{μ⃗ T}` (Eq. 9). Choi form = a `2k+1`-partite
  state with alternating input/output legs; its marginals are `{Ê_{k:k-1},…,Ê_{1:0}, ρ_0}`.
- **Action / prediction (Eq. 10 — the spatiotemporal Born rule).**
  `ρ_k(A_{k-1:0}) = Tr_{ok̄}[Υ_{k:0} (I ⊗ A_{k-1} ⊗ ⋯ A_0)^T]` — predicts the output of ANY control
  sequence consistent with the process, inclusive of ALL intermediate SE dynamics + initial SE
  correlations. This is what makes the process tensor a control object.
- **Non-Markovianity measure (Eq. 11 — necessary AND sufficient).** Any CP-contractive quasi-distance
  between `Υ_{k:0}` and its closest Markov process tensor. Markov = a PRODUCT of CPTP marginals:
  `Υ^{Markov}_{k:0} = Tr_k̄[Υ]⊗Tr_{k-1}̄[Υ]⊗⋯⊗Tr_0̄[Υ]` (discard correlations). Strictly finer than the
  usual sufficient-only witnesses (CP-divisibility, BLP, RHP): here memory = literal correlation in the
  Choi state, measured on the same footing as any spatial correlation.
- **MLE-PTT + Markov-order (§III–IV).** MLE finds the physical (positive + causal) `Υ` maximizing data
  likelihood (a positive causal projection); Markov-order-ℓ truncation discards weak long-time memory →
  circuits scale `O(k·N^ℓ_{mle})` with `N_{mle}=10` (vs `N_{oc}=24` overcomplete). ℓ is itself a
  diagnostic of device-noise complexity.

## THE load-bearing result for us — the active/passive boundary, stated in the tomography foundation [paper]
- **The reconstruction observable IS active/designed observation:** you apply IC control operations `{B_μ}`
  (CP maps / unitaries, and ideally measure-and-prepare "causal breaks") BETWEEN timesteps. This is the
  active-`W` pole made operational.
- **RESTRICTED process tensor (§II C) = the passive/limited-control regime, and its exact cost.** On NISQ,
  intermediate ops are limited to UNITARIES + a terminal measurement (no fast projective mid-circuit
  control). Unitary control gives a *restricted* process tensor — "an **observational restriction**, not a
  model restriction." Key quotes: **unitaries are "fully orthogonal to the span of non-unital ... and
  trace-decreasing ... maps"** (their Choi are rank-1 projections onto max-entangled states; linear
  inversion **omits the local expectation values**); and decisively — **"in the absence of measurement
  causal breaks, correlations between past and future measurement statistics cannot be established ...
  the actual strength of the memory can only be inferred rather than directly measured."** Any measure
  needing a full eigendecomposition (e.g. quantum mutual information) is "similarly out of reach."
- **⇒ [ours] this is the passive/active boundary from the tomography side.** Passive/unitary-only records
  can *infer* but not *directly measure* the memory (and are blind to the non-unital/coherent local
  expectations) — the tomography-side twin of Prop IW-1's commutator-sector evenness. Designed control +
  causal breaks (active) directly measure it. Precisely the reconstruction's pivot, from the foundational
  reference.

## Findings + numbers [paper]
- Full LI-PTT needs `O(N_{oc}^k)` circuits (`N_{oc}=24` overcomplete for a qubit to beat shot-noise);
  MLE-PTT drops the base to `N_{mle}=10`; Markov-order-ℓ truncation → `O(k·N_{mle}^ℓ)` (linear in k).
- Single-qubit unitary basis needs `d^4−2d^2+2 = 10` ops/step; gate error `O(10^{-4})` (below the
  `1/√N_shots` sensitivity), so the input-op assumption is safe on clean devices.
- Demonstrated on IBM devices: characterize at Markov orders ℓ∈{1,2,3}; noise-aware control with HIGHER ℓ
  gives HIGHER multi-time circuit fidelity — improvement is *contingent* on including multi-time
  correlations (the necessity claim), a trade-off between characterization complexity and accuracy.

## Limitations [paper]
- Full generality scales exponentially in k (tempered only by Markov-order truncation / low-memory).
- Requires high-fidelity input control (SPAM broadened: initial state is a free marginal, so absorbed;
  gate-dependent coherent error needs GST or an overcomplete basis; strong SE coupling during a finite
  gate `O(1/τ_p)` breaks the model — expected rare).
- Restricted (unitary-only) PTT cannot directly measure memory strength / non-unital local expectations.
- Demonstrations are single-qubit, few-step; scalability tied to how fast memory decays.

## Relevance to the reconstruction [ours]
- **THE anchor for the active-observation spine** (`RECONSTRUCTION_active_observation`): non-Markovian
  noise IS characterized from a device by applying designed control operations between timesteps
  (spatiotemporal Born rule, Eq. 10) — refuting the retracted "passive record can't see non-Markovian"
  framing. The `qec_twin` `C_cal(r)` probe ladder (mid-evolution intervention/twirl probes) is the
  operational instance; `calibration/nll.py` is the MLE analogue.
- **The honest caveat is grounded here too:** unitary-only / passive characterization is a *restricted*
  process tensor — inferable but not directly measurable memory, blind to non-unital/coherent local
  expectations. So the reconstruction's active pivot must include **causal breaks** (measure-and-prepare)
  to *directly* measure the coherent memory, and must declare what a restricted (probe-limited) basis
  leaves un-fixed — the tomography-side of the gauge/identifiability honesty ("active ⇏ no gauge").
- **The non-Markovianity measure (Eq. 11)** — distance to the closest Markov process tensor — is the
  necessary+sufficient replacement for the retracted matched-marginal 2-point discriminator: memory is a
  literal correlation in `Υ`, measured directly, not a second-order residual.
- **Markov-order ℓ** is the process-tensor analogue of the twin's probe-richness `r` / the memory-depth
  the pseudomode carrier must reproduce (cf. Keeling PT-MPO bond `χ`).

## Related notes
[[keeling_process_tensor_2509.07661]] (PT-MPO memory measure), [[tn_decoders_process_tensor_nonmarkovian_2412.13739]]
(process-tensor decoders for QEC — same White/Modi lineage), [[montanalopez_nonmarkovian_learning_manybody_2511.16772]]
(active mid-`W` kernel learning), [[qec_learnable_logical_noise_2601.22286]] (Walsh-Hadamard syndrome learnability + gauge),
[[involuntary_w_check_2026-07-03]] (Prop IW-1, the passive obstruction this measures from the tomography side).
