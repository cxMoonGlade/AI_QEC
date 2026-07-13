# Deep review — Bravyi, Englbrecht, König & Peard, Correcting Coherent Errors with Surface Codes

## Provenance

- **Pinned source:** arXiv:1710.02270v1, 18-page PDF, fetched 2026-07-13 from
  [arXiv](https://arxiv.org/abs/1710.02270); published as npj Quantum Information 4, 55
  (2018), [DOI 10.1038/s41534-018-0106-y](https://doi.org/10.1038/s41534-018-0106-y).
- **PDF SHA-256:** `d5f6c37036a03bd9dfe5a3e8ebb938de99efafab154b5ee1f9c9c7abf4f3852d`.
- **Reading method:** all 18 PDF pages traversed. The load-bearing model/equations and numerical
  claims were checked in extracted text; PDF pp. 3 and 11–14 were also rendered and visually
  inspected (Eqs. 3–6 and 52–57; Figs. 8–12; conclusion).
- **Status:** full-paper deep read. Exact algorithmic statements are separated below from Monte
  Carlo observations and the authors' explicit large-distance conjecture.

> Deep reading note (academic-paper-review format). Project relevance is bounded
> to the exact product-rotation reference slice and its conditional logical metric.

## Metadata
- **Authors.** Sergey Bravyi, Matthias Englbrecht, Robert König, Nolan Peard (IBM T.J. Watson; TU Munich; MIT).
- **Venue / status.** npj Quantum Information 4, 55 (2018); arXiv:1710.02270.
- **Domain / type.** QEC / fault tolerance; **theoretical + simulation** (exact classical simulation algorithms).

## Executive summary
The paper gives **`O(n²)` exact classical sampling/evaluation algorithms** for two restricted
surface-code protocols, by encoding each qubit into **4 Majorana modes** (a "C4-code") so the
protocol becomes a **fermionic-linear-optics (FLO)** circuit. The storage model is a product of
single-qubit `Z` rotations (translation invariant in the reported numerics); this is not a general
coherent-plus-stochastic circuit-noise simulator. The state-preparation algorithm accepts an
arbitrary product input of the form treated in the paper. Reported runs reach `n=2401` qubits
(`d=49`). Under translation-invariant storage noise `(e^{iθZ})^{⊗n}`, the syndrome distribution
`p(s)` is **independent of the logical state**, and the post-correction logical channel is a
**per-syndrome coherent rotation** `ρ↦e^{iθ_s Z_L}ρe^{-iθ_s Z_L}`. The logical error rate is
> **`P^L = 2Σ_s p(s)|sin θ_s|`** — the **average diamond-norm distance** between the conditional logical channel and the identity (Eq. 4).

Main numerical findings: an estimated **threshold `θ_0∈[0.08π,0.1π]`** for storage,
with `P^L` observed to decay exponentially in `d` below it; the estimated threshold agrees with
the Pauli-twirl comparison (dephasing `ε=sin²θ`, `ε_0≈0.11`), **but the Pauli twirl significantly
underestimates `P^L` sub-threshold**; and the simulated per-syndrome angles increasingly
concentrate near `{0, π/2}` (logical `{I, Z_L}`). The last trend motivates, but does not prove,
the authors' large-distance coherence-to-incoherence conjecture.

For this project it is a **published exact reference slice and a metric precedent**, not the
current production substrate: no FLO backend is present in `src/` as of the 2026-07-13 audit.
`P^L` is an exact average conditional diamond distance for this pure-rotation storage model, and
the physical-twirl comparison is a direct warning that matching the threshold does not validate
sub-threshold logical rates. Neither result certifies the project's leakage, repeated-record,
PEPS-truncation, or XZZX bridge.

## Contributions (claim → evidence → strength)
- **C1. `O(n²)` exact coherent surface-code simulation via Majorana/FLO (Secs. II–V).** *Evidence:* C4-code encoding (Eq. 7–8), `B_f=∏_{e∈∂f}L_e` (Lemma 1), FLO gate set + complexity; Table I (`d=49`, seconds). *Strength: strong — the enabling technical result.*
- **C2. `P^L`= average diamond-norm distance, exact for pure rotations (Eq. 3–4).** Per-syndrome logical rotation `θ_s`; `P^L=2Σ_s p(s)|sin θ_s|`. *Strength: exact and computable in the stated storage model.*
- **C3. Thresholds + twirl-underestimate (Eqs. 5–6; Figs. 8, 11–14).** Storage `θ_0∈[0.08π,0.1π]`; prep `θ_0(φ)∈[0.1π,0.15π]`; twirl approximately matches the reported threshold but strongly underestimates sub-threshold `P^L`. *Strength: direct numerical evidence in the stated model, not a threshold theorem.*
- **C4. Coherence-to-incoherence conversion at large `d` (Figs. 9–10; Sec. VII).** At the simulated distances, `θ_s` becomes increasingly concentrated near `{0,π/2}` and the coherence ratios approach one. The paper explicitly calls the asymptotic conversion a **conjecture** and asks whether it generalizes. *Strength: direct finite-size numerical evidence plus phenomenological extrapolation, not a theorem.*

## Method (deep)
- **C4-code.** 4 Majorana modes `c_1..c_4` per qubit, stabilizer `S=−c_1c_2c_3c_4`; logical `X̄=ic_1c_2`, `Z̄=ic_2c_3` (Eq. 7–8). Surface code on a planar graph `G=(V,E,F)`, `4n` modes; **link operators** `L_e=ic_p c_q` (Eq. 9) Hermitian, pairwise commuting.
- **Syndrome = product of links.** `B̄_f=∏_{e∈∂f}L_e` (Lemma 1, Fig. 4); measuring the syndrome reduces to measuring commuting link operators — a **Gaussian/FLO** operation. Logical ops `X̄_L,Z̄_L` are link products on the boundary (Eq. 12, Lemma 2).
- **FLO simulability.** Gates: init pairs, rotation `exp(γc_pc_q)`, projector `(I+ic_pc_q)/2`. Runtimes `O(n)` (init/rot), `O(n²)` (projector); exploiting locality → `O(n^{1/2})` active modes → total `O(n²)`. The link state `φ_link` is a fermionic Gaussian state; coherent `Z`-error preserves Gaussianity → simulable.
- **Algorithms.** A (storage): sample `p(s)`, compute `θ_s`, `P^L`. B (logical prep): syndrome projector `Π_s=∏_f ½(I+s_f B_f)` (Eq. 15), `p(s)=⟨ψ|Π_s|ψ⟩`, final `|φ_s⟩=C_sΠ_s|ψ⟩/√p(s)` (Eq. 18); Pauli correction `C_s` via constant-weight MWPM.

## Methodology assessment
| Criterion | 1–5 | Assessment |
|---|---|---|
| Soundness | **5** | Exact FLO simulation with proven lemmas; `P^L` rigorously a diamond-norm distance for pure rotations. |
| Novelty | **5** | First large-scale exact coherent surface-code simulation; the Majorana/FLO algorithm is the enabling, widely-reused tool. |
| Reproducibility | **5** | Algorithms + complexity + runtime table; self-contained encoding. |
| Experimental design | **4** | Storage + prep, multiple distances, twirl comparison; single-axis coherent only (the FLO constraint). |
| Statistical rigor | **4** | At least 50,000 syndrome samples per point (5,000 only in Fig. 12), threshold brackets, exponential-decay diagnostics, and explicitly conjectural finite-`d` extrapolation. |
| Scalability | **5** | `O(n²)` to `d=49` on a laptop — the headline. |

## Strengths
- **S1 — exact + scalable simulation on a restricted coherent slice (the FLO trick).** Encoding into Majorana modes makes the two stated surface-code protocols Gaussian-fermionic and exactly sampleable/evaluable per run; Monte Carlo is still used for reported averages.
- **S2 — a direct channel metric (`P^L`= avg conditional diamond-norm, Eq. 4/52).** This avoids replacing the coherent residual by a fidelity proxy, while remaining model-specific.
- **S3 — the twirl-underestimate finding (sub-threshold).** Showing the threshold matches the twirl but the sub-threshold `P^L` does **not** is the precise, honest statement of why coherence matters where it counts (the operating regime).

## Weaknesses / limitations
- **W1 — single-axis product `Z` rotations for storage.** General multi-axis, correlated, leakage, non-unital, measurement, and circuit-level noise are outside the demonstrated storage model.
- **W2 — `P^L`'s diamond-norm identity is exact only for *pure rotations*.** Once stochastic/non-unitary noise mixes in, `P^L=2Σp|sinθ|` is a proxy, not exactly the diamond norm — a caveat the twin's metric rule must carry.
- **W3 — translation-invariant, idealized.** Storage noise is uniform `(e^{iθZ})^{⊗n}`; no circuit-level/measurement noise (added by Márton–Asbóth 2303.04672).

## Relevance to the twin
This source supports only a bounded comparison surface for the current project:
1. **Independent reference candidate, not implemented backend.** A future FLO port could provide an exact large-`d` reference on the paper's product-`Z` slice. Until implemented and cross-validated, it is not a certified project teacher.
2. **Metric precedent.** `P^L` supplies an exact average conditional diamond distance only while the residual channels have the pure-rotation form in Lemma 4. A leakage/non-unitary extension needs a separately justified metric.
3. **Physical twirling can miss the operating-regime rate.** Fig. 11 directly supports this bounded warning. It does not prove that the project's moment-matched model fails, which requires an in-repo matched comparison.
4. **Large-`d` washout is restricted and conjectural.** The finite-size trend under ideal syndrome projection, Pauli recovery, and independent product rotations cannot be transferred to long-range correlated noise, leakage, noisy repeated rounds, a retained full record, or PEPS truncation.
5. **No long-range-truncation conclusion.** The paper contains no physical 2D PEPS tail, bond truncation, record-faithfulness bound, or rare-LER error certificate.

## How to use / trust + open questions
- **Trust:** high for the exact lemmas/algorithms and the reported finite-size observations in the stated model; medium for the large-distance phenomenology; **not evidence** for the project's leakage/record/truncation bridge.
- **Open questions for the project:** (i) decide whether a bounded FLO reference port is worth implementing; (ii) if so, reproduce Fig. 11 with a frozen decoder and metric convention before using it as a falsifier; (iii) define the correct channel metric once stochastic/non-unitary leakage is present; (iv) do not use the large-`d` washout trend to delete the finite-`d` coherent carrier without a target-model test.
