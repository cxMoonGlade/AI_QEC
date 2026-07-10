# Full-text review — Kilda, Biella, Kshetrimayum, Weimer, Orus, "On the stability of the infinite Projected Entangled Pair Operator ansatz for driven-dissipative 2D lattices" (arXiv:2012.03095, SciPost Physics Submission)

> **Provenance (2026-07-09): FULL-TEXT 精读.** PDF (arXiv:2012.03095v2, 8 Feb 2021) ->
> `outputs/papers/pepo_survey/2012.03095.txt` (pdftotext, 21 pp / 1585 lines). All section/eq/figure
> references from that text. Figures not pixel-extracted — figure facts = captions + numbers stated
> in text.
>
> **CRITICAL for our iPEPO carrier plan.** This paper directly investigates the stability
> **failure modes of the SU-iPEPO algorithm** — the exact method we are considering for 2D open-system
> simulation. The findings are sobering: near dissipative critical points, increasing bond dimension
> can make the algorithm **less stable**, not more accurate.
>
> **Second full-text verification pass (2026-07-09, pre-engine-build):** re-read the original
> end-to-end. All load-bearing claims of this note confirmed verbatim (ε_Λ Eq. 3; D=3,4-pass/D=5,6-fail
> at J_y=1.5; D=12-pass/D=14,15-fail at J_y=1.2; κ≥5.2; J_y threshold 1.33/1.32; CTM-independence;
> "spurious steady states" p.8; >128 GB CTM at D=15; github.com/The-iPEPO-Project/iPEPO). Three
> details ADDED in this revision (previously missing): (i) the steady-state STOP RULE is per-bond —
> ε_Λ < ε required for EACH Λ ∈ {Λ[U,D,R,L]} (App. A.2, after Eq. 3); Fig. 2 plots the Λ[U] one;
> (ii) they GRADUALLY DECREASE δt during a run to shrink Trotter error at fixed cost (App. A.2);
> (iii) venue: later published as SciPost Phys. Core 4, 005 (2021) (this note reads the v2 submission
> text).

## Metadata [paper]
- **Authors / affiliation:** D. Kilda (Caltech, corresponding), A. Biella (Paris-Saclay / College de France),
  M. Schiro (Paris-Saclay / College de France), R. Fazio (ICTP Trieste / Napoli),
  J. Keeling (U. St Andrews).
- **Venue / status:** arXiv:2012.03095v2 [cond-mat.other], submitted to SciPost Physics (submission
  received 31 Dec 2020, revised 8 Feb 2021). NOT final-published (the arXiv submission status at the
  time of this note was "SciPost Physics Submission" — it is the pre-review submission manuscript).
- **Type:** Method critique / numerical stability analysis. NOT a new method paper — it examines the
  failure modes of the existing iPEPO algorithm from Kshetrimayum et al. (Nat. Commun. 8, 1291, 2017).
- **Code:** Fortran implementation available at https://github.com/The-iPEPO-Project/iPEPO [ref 36].

## Executive summary [paper]

The paper performs a systematic stability analysis of the **simple-update (SU) infinite Projected
Entangled Pair Operator (iPEPO)** algorithm for finding the nonequilibrium steady state (NESS) of
driven-dissipative 2D lattice systems. The testbed is the dissipative spin-1/2 XYZ model on an
infinite square lattice (Eqs. 1-2).

**Key result (sobering for our plans):** The SU-iPEPO algorithm is **not always stable** — it only
reaches a steady state in some parameter regimes, typically away from dissipative critical points.
Close to critical points (where correlation lengths diverge), the algorithm **fails to converge
regardless of bond dimension D, timestep size, or initial condition**. Worse, increasing D does not
monotonically improve accuracy: for some parameter regimes, **a steady state found at low D
destabilizes when D is increased** (Fig. 6, Jy=1.5: D=3,4 converge; D=5,6 do not). The instability
resides entirely in the **simple-update (SU) time evolution** — it is unaffected by the
corner-transfer-matrix (CTM) contraction accuracy.

## Method (deep) [paper]

### The iPEPO approach (restated from Appendix A)

The density matrix rho is represented as a **Projected Entangled Pair Operator (PEPO)**, then
reshaped (vectorized) into an infinite PEPS (iPEPS) by fusing bra/ket physical indices at each site
(Sec. A.2). The Liouvillian evolution replaces imaginary-time Hamiltonian evolution with real-time
Liouvillian propagation. The algorithm reuses the same simple-update (SU) machinery as ground-state
iPEPS:

1. **Trotter decomposition:** Split the Liouvillian into four bond directions L_U, L_D, L_R, L_L
   (Eq. 4-5).
2. **Vidal form:** The iPEPS is represented by two site tensors Gamma[A,B] and four diagonal bond
   matrices Lambda[U,R,D,L] (Fig. 7).
3. **The SU step (Sec. A.1.1):** absorb external Lambdas into Gammas, decompose into rank-3
   subtensors via SVD/QR (cost O(d^6 D^3)), apply the two-body propagator, re-SVD with truncation
   to D singular values, re-contract, divide out external Lambdas.
4. **CTM for observables (Sec. A.1.2):** Compute environment via corner transfer matrix renormalization
   with environmental bond dimension chi. Cost O(chi^3 D^6 + chi^2 D^8).

### The stability diagnostic (Eq. 3, central to the paper)

The stability metric monitors **singular value convergence**:
```
epsilon_Lambda = |Lambda_n - Lambda_{n-1}|_max / (delta_t * |Lambda_n|_max)
```
where Lambda_n are the diagonal bond matrices at timestep n. For a steady state, epsilon_Lambda
should approach zero (or machine precision). **Noisy oscillations that persist indefinitely** signal
failure to converge. **Precise stop rule (App. A.2, added 2026-07-09):** a steady state is declared
only when epsilon_Lambda < epsilon holds for EACH of the four bond matrices Lambda in
{Lambda[U], Lambda[D], Lambda[R], Lambda[L]} separately — a per-bond spectrum-stationarity
criterion (Fig. 2 shows the Lambda[U] trace). They also gradually DECREASE the timestep delta_t
during a run to reduce Trotter error while keeping cost low.

### The model (dissipative XYZ, Eqs. 1-2)

```
d/dt rho = -i[H_XYZ, rho] + kappa/2 * sum_j (2 sigma^-_j rho sigma^+_j - {sigma^+_j sigma^-_j, rho})
H_XYZ = sum_{<i,j>} (J_x sigma^x_i sigma^x_j + J_y sigma^y_i sigma^y_j + J_z sigma^z_i sigma^z_j)
```

with J_x=0.5, J_z=1 (in units of kappa=1), varying J_y.

## Findings + numbers [paper]

### 1. Instability regime (Sec. 2, Figs. 1-5)

| Observation | Details |
|---|---|
| **No steady state near dissipative critical points** | For J_y in ~1.2-1.32 (at J_x=0.5, J_z=1, kappa=1), the algorithm fails to converge for ALL timesteps delta_t={10^-1,10^-2,10^-3} (Fig. 2). The singular-value metric epsilon_Lambda shows noisy oscillations that never decay (Fig. 2a-c, blue lines). |
| **Stable regime exists** | For J_y=1.5, epsilon_Lambda decays cleanly to ~10^-6 (Fig. 2a-c, green lines). |
| **Threshold is sharp** | Adiabatic sweeping from J_y=1.4->1.2 reveals a clear threshold: steady states found for J_y >= 1.33, no steady state for J_y <= 1.32 (Figs. 4a-b). This is robust to timestep size and sweep step. |
| **Strong dissipation helps** | Sweeping from large kappa (kappa=8) to small (kappa=1) at fixed J_y=1.2: steady state for kappa >= 5.2, fails for kappa < 5.2 (Figs. 5a-b). Strong dissipation suppresses correlations (NESS becomes approximately factorizable), making iPEPO tractable. |
| **Initial conditions don't matter** | Testing four different initial conditions (random, all-down, all-up, mixed xyz) at J_y=1.2: ALL show persistent noisy oscillations (Figs. 3a-c). The instability is robust to initial state choice. |
| **The original 2017 results (Fig. 1b) are reproduced by stopping early** | Using a large timestep delta_t=10^-1 and stopping after N=1000 steps yields results similar to Kshetrimayum et al. [27] — but these are NOT steady states, just early-time snapshots with large Trotter error (Fig. 1b vs 1a). |

### 2. Bond dimension effects — THE critical finding (Sec. 2.2, Fig. 6)

**THIS IS THE MOST IMPORTANT RESULT FOR OUR USE CASE.**

| Observation | Details |
|---|---|
| **At J_y=1.2 (unstable regime), D=3-6 all fail** (Fig. 6a-c) | No steady state found at ANY tested bond dimension. No monotonic improvement with D. |
| **At J_y=1.5 (stable regime), HIGHER D DESTABILIZES** (Fig. 6d-f) | D=3,4 reach steady state; D=5,6 FAIL to reach steady state. **This is the counterintuitive and dangerous result**: increasing the variational自由度 makes the algorithm LESS stable. |
| **At J_y=1.2, D=12 transiently works; D=14,15 fail again** (Fig. 6g-i) | For D=12, epsilon_Lambda shows a decaying trend at delta_t=10^-2,10^-3. But D=14,15 drive noisy oscillations. Suggests that while SOME higher D may eventually work, the approach is not systematic — D must be "just right" and there is no a priori way to find the correct D. |
| **The instability is NOT a CTM issue** | The SU time evolution is completely unaffected by CTM contraction or environment bond dimension chi (explicitly stated, paragraph near Fig. 1). All results are CTM-independent. |
| **D=15 CTM is impractical** | CTM at D=15 would require >128 GB of RAM (p.8, paragraph after Fig. 6) — distributed memory and quantum symmetries needed to extract observables at D>=15. |

### 3. Interpretation (Sec. 3, Conclusion)

The authors state clearly: **"the SU iPEPO algorithm at low bond dimensions is not always stable,
reaching a steady state only in some parameter regimes, typically away from dissipative critical
points."** They believe there EXISTS a sufficiently high D that can faithfully represent the NESS
(when spatial correlations decay exponentially), but the study cannot determine what typical D
is needed for prototypical driven-dissipative models.

## Proposed mitigations (Sec. 3) [paper]

The paper discusses three alternative approaches, none implemented:

1. **Full Update (FU) iPEPS** (Sec. 3, paragraph 2): Adapt the variational two-site FU algorithm
   to Lindblad time evolution. **Problem:** non-Hermitian operators require a non-Hermitian
   alternating least-squares scheme, which doesn't exist robustly. Hubig & Cirac [39] found FU
   can be LESS stable than SU for closed-system time evolution. McKeever & Szymanska [43] showed
   that a **"full environment truncation"** variant (not full FU) can improve iPEPO stability —
   this is the most promising near-term mitigation.

2. **Global variational search for L|rho>>=0** (Sec. 3, paragraph 3): Solve for the null eigenstate
   of either the Liouvillian L or the positive-semidefinite L†L directly. **Appealing because**
   L†L enables reusing standard Hermitian optimization. **Problems:** (a) L†L of a
   nearest-neighbor Lindbladian produces highly non-local couplings (even when L = sum L_{l,l+1},
   L†L = sum_{l,r} L†_{l,l+1} L_{l+r,l+r+1}) — manageable in 1D but leads to unfeasibly large
   bond dimensions in 2D. (b) Contractions involve BOTH the iPEPS representing |rho>> AND the
   iPEPO representing L or L†L — expensive.

3. **Tangent-space / generalized eigenvalue iPEPS** (Sec. 3, paragraph 4): Extend the novel
   variational iPEPS techniques from Refs. [46,47] to Lindbladians. These optimize iPEPS tensors
   using tangent space methods or local generalized eigenvalue problems, avoiding explicit PEPO
   construction for the Hamiltonian/Liouvillian. **This could dramatically reduce costs** and
   potentially be more robust than two-body SU updates — but adapting to the non-Hermitian L or
   L†L is open research.

## Limitations [paper]

- **Single model testbed:** Only the dissipative XYZ model is studied in detail (with brief mention
  that similar issues arise for the 2D dissipative transverse-field Ising model). The universality
  of the instability across other driven-dissipative systems is asserted but not systematically
  tested.
- **No theoretical mechanism for instability:** The paper identifies WHEN instability occurs but
  provides no **theoretical explanation for WHY** increasing D destabilizes a previously stable
  fixed point. Is it a truncation artifact? A Trotter-error entanglement-seeding effect? A
  gauge-fixing pathology? The root cause is not identified.
- **No a priori stability criterion:** There is no diagnostic that predicts stability without
  running the simulation. The epsilon_Lambda metric is a posteriori (needs to run to see if it
  decays).
- **SU-only study:** The analysis is entirely within the simple-update framework. The FU,
  variational, and tangent-space mitigations are not implemented — they remain speculative.
  The "full environment truncation" variant [43] that showed improvement is cited but not tested
  here.
- **No CTM dependence studied:** The paper explicitly states the CTM contraction does not affect
  the SU instability, but this means the CTM environment approximation's own stability limits
  are NOT explored in relation to the SU failure.
- **D=15 compute wall:** Even finding D that works for the SU time evolution, CTM observables
  at D>=15 are infeasible (>128 GB RAM) without distributed memory and symmetries.
- **D=12 hint, not proof:** The transient stabilization at D=12 for J_y=1.2 is intriguing but
  not conclusive — the paper does not establish whether D=12 is genuinely sufficient or just
  appears to converge on the timescale studied.

## Relevance to qec_twin [ours]

**Verdict: HIGH-STAKES RELEVANCE. The paper documents a fundamental stability ceiling on the
SU-iPEPO algorithm that directly constrains any plan to use iPEPO as the 2D open-system carrier
for non-Markovian dynamics via pseudomode augmentation.**

### The core tension for our use case

Our plan (per `docs/plan3.md` and ADR 0008/0010) involves:
- Representing the system density matrix as an iPEPO on the 2D surface-code lattice.
- Augmenting with **pseudomodes** (ancillary bath modes) to capture non-Markovian shared-bath
  effects (1/f noise, TLS).
- The pseudomodes increase the **effective local Hilbert space dimension** at each site, which in
  an iPEPO representation **is equivalent to increasing the effective bond dimension** D (or
  requires mapping onto additional PEPS legs).

**This paper's findings mean that adding pseudomode degrees of freedom — which is isomorphic to
increasing the effective correlation length and entanglement in the density-matrix representation —
may actively DESTABILIZE the iPEPO evolution**, exactly in the parameter regimes we care about
(near-critical shared-bath-induced noise correlations).

### Specific constraints the paper imposes

1. **Increasing D does NOT systematically improve accuracy for iPEPO steady states.** This breaks
   the standard tensor-network assumption (MPS/PEPS converge monotonically with D for ground states).
   Our pseudomode augmentation strategy that increases effective D risks hitting the
   "D=5,6 destabilize while D=3,4 converge" regime (Fig. 6d-f) — we would not know whether
   augmentation helps or hurts without running it.

2. **The instability is worst near dissipative critical points** — but a shared-bath-induced
   dissipative phase transition (e.g., correlated dephasing driving a noise-induced transition)
   is exactly the interesting physics. The paper shows that these are the regions where iPEPO
   is least trustworthy.

3. **The instability is in the SU time evolution, not CTM contraction.** This means even cheap,
   low-chi environment contractions do not help — the problem is in the time-stepping itself.
   Any plan that relies on SU time evolution must contend with this.

4. **D=12 worked where D=3-6 failed (J_y=1.2, Fig. 6g-i), but D=14,15 failed again.** This
   non-monotonic behavior means even a careful D-sweep convergence test (standard practice in
   tensor-network methods) is unreliable — apparent convergence at D=12 could be a "spurious
   steady state" (their term, p.8) that changes at D=14.

5. **Strong dissipation (kappa >= 5.2) stabilizes iPEPO** (Figs. 5a-b). This suggests iPEPO
   IS usable for overdamped / high-dissipation regimes. For noise models where dissipation
   dominates over coherent coupling (e.g., pure dephasing with fast bath correlation times),
   iPEPO may be stable. Our pseudomode shared-bath simulations would need to check whether
   they fall in the "strong dissipation" (safe) or "near critical" (unsafe) regime.

6. **The full environment truncation variant** (McKeever & Szymanska [43], ref 43 in paper) is
   cited as improving stability. This is the most actionable mitigation: adopting FET instead of
   SU for the iPEPO time evolution may bypass the instability, at the cost of more expensive
   truncation.

### What the paper DOES NOT settle for our use case

- **Whether FET or FU iPEPO eliminates the instability** is cited but not tested here. The
  McKeever & Szymanska result (arXiv:2012.12233, their ref 43) is the natural follow-up to read.
- **Whether pseudomode augmentation necessarily increases effective iPEPO bond dimension** in a
  way that triggers the instability — this depends on how pseudomodes are coupled (as ancilla
  sites on the 2D lattice with their own physical dimension, which becomes local dimension d of
  the iPEPO, not the bond dim D). If pseudomodes add to the PHYSICAL dimension d rather than
  the bond dimension D, the instability documented here (which is D-specific) may not directly
  apply. **This distinction is crucial** — the paper's instability concerns the truncation of
  **bond indices** (entanglement between lattice sites), not the size of the **physical index**
  (local Hilbert space). Pseudomodes as auxiliary lattice sites with enlarged local dimension
  could bypass the bond-instability problem, at the cost of larger d² in the vectorized
  representation.
- **Whether iPEPO is stable for the surface-code stabilizer steady state** — our steady state
  is the code's steady-state density matrix under noisy gates, which is NOT the same as the
  NESS of a driven-dissipative spin model. The dissipative XYZ model has spontaneous symmetry
  breaking and true dissipative phase transitions; the surface-code steady state may have
  shorter correlation lengths and thus be more iPEPO-friendly.

### Concrete recommendations from this paper

1. **Before committing to SU-iPEPO as carrier, test stability on our target model.** Run the
   epsilon_Lambda diagnostic (Eq. 3) for a simplified surface-code iPEPO (even d=3, nearest-neighbor
   noise) and check for convergence at D=3,4,5,6. If the D=5,6 instability manifests
   (Fig. 6d-f pattern), abandon SU-iPEPO for the base carrier.

2. **Consider pseudomode-as-ancilla-site instead of pseudomode-as-bond-dimension.** Mapping
   pseudomodes to enlarged local dimension on appended ancilla lattice sites avoids the bond
   instability. Each pseudomode adds a physical Hilbert space dimension d_pseudo to the local
   site → the vectorized PEPS physical dimension becomes (d_system * d_pseudo)^2. This is a
   different cost scaling — larger local tensors but no increased bond cutoff.

3. **Read McKeever & Szymanska (arXiv:2012.12233) as the natural follow-up** — if full-environment
   truncation stabilizes iPEPO where SU fails, adopting FET could resolve the instability and
   unblock the 2D carrier.

4. **The adiabatic parameter sweep strategy (Sec. 2.1, Figs. 4-5) might help.** For regimes where
   iPEPO is unstable, slowly tuning from a stable parameter regime into the target regime can
   bypass highly entangled intermediate states. This could be used to initialize pseudomode
   couplings gradually.

5. **Do not rely on "convergence in D" as a certification strategy.** The non-monotonic D
   behavior (D=12 works, D=14 fails) means that D-sweep convergence checks (the standard
   tensor-network reliability test) are NOT sufficient to certify iPEPO steady states near
   critical points. Cross-validation with an independent method (small-system exact
   Liouvillian, cluster mean-field, process tensor) is necessary.

## How to use / trust + open questions [ours]

- **Trust level: HIGH for the negative result (SU-iPEPO fails near critical points), MODERATE
  for the mechanism claim (D-related instability).** The core stability analysis (Figs. 1-6) is
  well-executed: multiple timesteps, multiple initial conditions, multiple bond dimensions,
  adiabatic sweeps, systematic threshold identification. The claim that "the instability is in
  the SU not CTM" is experimentally verified (the paper states results are checked to be
  CTM-parameter independent). However, the paper does NOT explain the ROOT CAUSE of the
  instability — it documents what and when, not why. The failure at higher D (Fig. 6) is
  particularly important for us but is NOT theoretically explained: is it a Trotter error
  compound effect? A non-Hermitian SVD truncation pathology? A gauge-fixing artifact? Without
  a mechanism, we cannot predict when it will hit our model.

- **Critical open question:** Does the D-instability at J_y=1.5 (Fig. 6d-f) arise from Trotter
  error at finite delta_t, or is it intrinsic to the SU approximation? The paper does not
  delta_t->0 extrapolate to answer this. If Trotter-induced, then lower delta_t or higher-order
  Trotter could help. If intrinsic to SU truncation, only FU/FET can help.

- **Relation to our gauge/identifiability analysis:** The SU truncation is a local gauge
  choice (Vidal form assumes diagonal Lambda matrices in a specific basis). The paper does not
  discuss whether a gauge-optimized truncation (e.g., choosing different SVD bases for the bond
  truncation) could stabilize the evolution. This is a potential research direction connecting
  our gauge theory to iPEPO stability.

- **Margin-critical note:** The Spurious steady states phrase (p.8, "spurious... at small bond
  dimension which then change as the bond dimension increases further") is the paper's most
  important caution for our project: **if we find a steady state at low D, we must not trust
  it until checked against higher D, but higher D may destabilize rather than confirm**. This
  creates a catch-22 for validation.

- **Next steps:**
  1. Read McKeever & Szymanska (2012.12233) — the full-environment-truncation mitigation.
  2. Read Weimer, Kshetrimayum, Orus (1907.07079) — the review of simulation methods cited as
     ref [44], which discusses variational iPEPO approaches.
  3. Implement the epsilon_Lambda diagnostic (Eq. 3) in any iPEPO code we develop — it is the
     essential convergence check.
  4. Design a small-scale test: d=3 surface code with depolarizing noise on a 2x2 unit cell
     iPEPO, sweep D=2..8, check for the Fig. 6 pattern before scaling to larger d or adding
     pseudomodes.
