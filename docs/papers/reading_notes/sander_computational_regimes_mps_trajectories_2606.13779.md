# Reading note (精读): Sander et al., "Computational regimes in matrix-product-state-based quantum trajectory simulations" (arXiv:2606.13779)

> **Provenance (2026-07-06): FULL-TEXT read (精读).** PDF → txt `outputs/papers/2606.13779.txt`
> (13 pages, PyMuPDF). All §/Eq refs from that text. Adjudication target: does this paper
> provide a framework for choosing the optimal MCWF unraveling for the JC shared-mode
> MPS simulations under the 65GB GPU memory constraint? **Verdict: YES — the (α,κ)
> framework and pilot-extraction protocol directly apply, and the central message ("lower
> bond dimension does NOT automatically mean lower total cost") is a concrete warning
> for our unraveling choices.**
>
> **Provenance (2026-07-06, second pass): FULL-TEXT re-read for a SECOND adjudication
> target** — should we add a parallel "TJM" trajectory backend next to the existing
> MCWF-on-MPS qutrit-leakage carrier (`src/qec_twin/forward/scalable/mps_forward.py`)?
> PDF now cached at `docs/papers/sander_computational_regimes_mps_trajectories_2606.13779.pdf`.
> **Verdict: this paper is NOT a new/faster simulation kernel — the TJM algorithm proper
> is its Ref. [28] (Sander et al., Nature Comm. 16, 11074 (2025) = arXiv:2501.17913, see
> `sander_tjm_tensor_jump_2501.17913.md`; circuit variant = cTJM,
> arXiv:2607.01323, see `froehlich_tensor_jump_method_2607.01323.md`). 2606.13779 is the
> COST-DECISION framework built ON the TJM: it proves no equivalence theorem of its own
> and claims no speedup of TJM over standard MCWF-on-MPS (TJM IS an MCWF-on-MPS method).
> What transfers to our carrier is the (α,κ) unraveling-comparison protocol + the warning
> that a lower-χ backend can lose on sampling. See "§TJM-backend adjudication" below.**

## Metadata [paper]
- **Authors:** Aaron Sander (TUM), Simon Cichy (FU Berlin), Martin Eigel (WIAS Berlin),
  Jens Eisert (FU Berlin / HZB), Maximilian Fröhlich (WIAS), Tom Peham (TUM),
  Robert Wille (TUM / MQSC / SCCH)
- **Venue / status:** arXiv:2606.13779v1 [quant-ph], 11 Jun 2026. Preprint.
- **Type:** theory + large-scale numerical benchmarks (TJM framework, MPS + TDVP)

## Executive summary [paper]
MPS-based quantum trajectory simulations have THREE independent cost channels:
**memory per trajectory** (∝ L·d·χ²), **runtime per trajectory** (∝ (T/δt)·L·d·χ³), and
**sampling cost** (number of trajectories N to reach target accuracy ε). Previous work
focused almost exclusively on minimizing trajectory entanglement (bond dimension χ).
This paper shows that **different stochastic unravelings of the SAME Lindblad dynamics
redistribute cost between these channels** — an unraveling with lower χ may require
many more trajectories (higher variance), offsetting the per-trajectory savings.

The framework introduces two dimensionless inflation factors:
- **α = χA/χB**: bond dimension inflation (relative per-trajectory complexity)
- **κ(ε) = NB/NA**: sampling inflation (relative number of trajectories for target accuracy ε)

The decision geometry: **κ = α³** (thread-limited boundary), **κ = α⁵** (memory-limited
boundary). If κ < α³: lower-χ unraveling wins despite more trajectories. If κ > α⁵:
higher-χ unraveling wins despite larger per-trajectory cost. The region α³ < κ < α⁵
is hardware-dependent.

## Key equations/findings [paper]

### Cost channels — Eqs. (8)-(10)
```
Memory:    mem(χ) ∝ L·d·χ²                    (8)
Runtime:   time(χ) ∝ (T/δt)·L·d·χ³            (9)
Sampling:  ΔO_U ≈ √(Var_U[O]/N)               (10)
           N_U(ε_target) = (σ_U / ε_target)²  (21)
```

### Inflation factors — Eq. (11)
```
α = χA / χB          (bond dimension inflation)
κ(ε) = NB(ε) / NA(ε) (sampling inflation)
```

### Decision boundaries — Eqs. (16)-(17)
```
Thread-limited:  TA/TB ∝ α³/κ     → unraveling B wins when κ < α³
Memory-limited:  TA/TB ∝ α⁵/κ     → unraveling B wins when κ < α⁵
```

### Hardware constraints — Eqs. (12)-(14)
```
m_j ∝ M / (L·d·χ²_j)              (max trajectories in memory)
P_j = min(p, N_j(ε), m_j)         (effective parallelism)
T_j ∝ (N_j/P_j) · (T/δt) · L·d·χ³_j  (total wall time)
```

### Benchmark results (Heisenberg chain, L=16, J=h=1, γ=0.1, δt=0.1, T=2, local ⟨Z⟩, ε_target=0.01, N_pilot=100 — §V.B)
| Noise channel | α | κ | Regime |
|---|---|---|---|
| Depolarizing (X,Y,Z) | 2.0 | 11 | Trade-off, hardware-dependent (α³=8 < κ=11 < α⁵=32; §V.B: "the crossover occurs near the onset of thread saturation, so modest changes in memory or worker count can reverse the preferred unraveling") |
| Dephasing (Z) | 1.5 | 3.8 | Trade-off (α³≈3.4 < κ=3.8 < α⁵≈7.6, hardware-dependent, crossover at lower memory) |
| Bit-flip (X) | 1.5 | 0.9 | **Strict dominance: B wins both channels (α>1 AND κ<1)** |

### Practical extraction protocol (§V.A)
1. Run N_pilot trajectories for each unraveling A, B under identical physical conditions
2. Extract maximum bond dimension χ_A, χ_B → α = χ_A/χ_B
3. Compute empirical trajectory-to-trajectory standard deviation σ_A, σ_B
4. For target accuracy ε_target: N_j ≈ (σ_j/ε_target)² → κ = N_B/N_A
5. Insert (α, κ) into hardware model to predict which unraveling is faster

**Key finding:** "The structure of κ does not mirror that of α: parameter regions
with reduced bond dimension can exhibit enhanced sampling requirements, and vice
versa. Sampling inflation therefore constitutes an independent cost channel that
cannot be inferred from trajectory entanglement alone."

**Key finding:** "Reduced trajectory bond dimension does not automatically imply
reduced total cost. ... an unraveling with lower per-trajectory complexity can
require more trajectories to reach the same statistical accuracy."

## Relevance to project [ours]
**Directly applicable to the JC shared-mode MPS simulations under the 65GB GPU
memory constraint.**

### 1. Which unraveling are we using?
The JC module uses MCWF (quantum jump unraveling) with MPS on quimb. The TJM
framework used in this paper is the same approach. The paper shows we should NOT
default to any single unraveling — we should pilot-test at least two different
unravelings (standard jump vs measurement-based/optimized jump) and extract (α, κ)
for our specific JC parameters (γ=0.15, g shared-mode coupling, 2 data qubits +
bosonic mode).

### 2. Our hardware maps to the thread-limited regime
65GB memory, GPU serialized (1 GPU task at a time, per the project CLAUDE.md
constraint). With L ~ 10-20 (2 data qubits + mode chain sites), d=2 (qubit) or
N_boson (truncated mode), and typical χ ~ 32-128:
- Memory per trajectory ≈ L·d·χ² · 16 bytes ≈ 20 · 2 · 128² · 16 ≈ 8.4 MB
- This is well within 65GB → m_j >> 1 → NOT memory-limited
- GPU serialized → p=1 effectively → thread-limited regime
- Decision boundary: κ = α³

**This means the higher-χ unraveling wins when κ > α³.** If reducing χ (say from
128 to 64, α=2) causes κ to increase to >8, the "cheaper" unraveling actually
costs MORE total wall time.

### 3. Pilot extraction for our JC model
The protocol is directly executable:
```python
# Pilot: N_pilot=100 trajectories, compare 2 unravelings at our JC parameters
# Unraveling A: standard quantum jump (MCWF)
# Unraveling B: measurement-based / optimized jump
# Extract: χ_A, χ_B, σ_A, σ_B at each γ
# Compute: α(γ), κ(γ), decision boundary κ = α³
```

Based on the paper's dephasing (similar to our σz sector: α=1.5, κ=3.8, κ<α³=3.375
→ B marginally faster) and bit-flip (similar structure to our σ−: α=1.5, κ=0.9,
κ<1 → B strictly dominates), the optimized unraveling is likely faster for our
amplitude-damping JC model.

### 4. The 65GB cap is NOT the bottleneck for trajectory MPS
At our system sizes (2 data qubits + ~20 mode sites), the memory per trajectory is
negligible (~8 MB). The constraint is GPU serialization (p=1 worker). This means
we are in the THREAD-LIMITED regime, where the decision is κ vs α³.

### 5. Warning: what the paper does NOT cover
- Non-Markovian (finite-memory) environments — the paper assumes Markovian Lindblad
  dynamics. Our JC model is non-Markovian (finite γ). The unraveling freedom for
  non-Markovian dynamics (process tensor, quantum combs) is richer and not addressed.
- Multi-time observables — the paper handles single-time expectation values only.
  Our syndrome records are multi-time joint probabilities. Variance scaling for
  multi-time estimators may differ.
- Bosonic modes — the paper benchmarks spin systems only. The JC bosonic mode
  introduces a continuous-variable element that changes χ scaling.

## §TJM-backend adjudication (2026-07-06 second pass): parallel TJM backend for the qutrit-leakage carrier

### 1. What the "TJM" in this paper actually is (algorithm, precise) [paper]

**This paper does not introduce the TJM; it uses it as the benchmarking platform.**
§I: "we employ the tensor jump method (TJM), a trajectory formulation of Lindblad
dynamics that evolves ensembles of MPS pure states and avoids the exponential overhead
of density-matrix simulation [28]." Ref. [28] = Sander, Fröhlich, Eigel, Eisert, Gelß,
Hintermüller, Milbradt, Wille, Mendl, Nature Comm. 16, 11074 (2025) — the TJM paper
proper (its circuit-level variant cTJM = arXiv:2607.01323, separate note).

The unraveling scheme, as this paper states it (§II.A, Eqs. (2)–(5)): standard MCWF.
Each trajectory evolves under the effective non-Hermitian Hamiltonian

> "H = H0 − (i/2) Σ_m γ_m L†_m L_m" (Eq. 2), with no-jump step
> "|Ψ(t + δt)⟩ = e^{−iHδt} |Ψ(t)⟩" (Eq. 3), total jump probability
> "δp(t) = Σ_m δt γ_m ⟨Ψ(t)|L†_m L_m|Ψ(t)⟩" (Eq. 4).
> "If a jump occurs, a jump operator Lm is applied with probability proportional to its
> contribution to δp(t), otherwise, the state vector is renormalized." (§II.A)

What is evolved and where jumps enter (§II.D): "the tensor jump method (TJM) [28],
which combines stochastic quantum trajectories with matrix product state representations
and time-dependent variational principle (TDVP) evolution [33–35]. Between stochastic
jump events, the state is propagated within the MPS manifold using TDVP, while quantum
jumps are implemented as local operator insertions followed by canonicalization and
controlled truncation."

dt/Trotter structure: first-order jump probability δp ∝ γδt per step (Eq. 6);
"Different choices of δt converge to the same physical dynamics in expectation, with
discretization error O(δt^p) for (p + 1)-order Trotterization" (§II.C). Convergence
order of TJM specifically (§IV.C): "we restrict to time steps δt ≤ 0.1, for which the
tensor jump method is provably convergent and achieves fixed-accuracy error scaling of
O(δt3) [28]" — the O(δt³) proof lives in Ref. [28], not here. [ours] The Strang-split
dissipative contraction giving that O(δt³) — e^{−iH_eff δt} = D[δt/2] U[δt] D[δt/2] +
O(δt³) — is spelled out in the cTJM note (2607.01323 §II.2).

Numerical controls (§IV.A): "No explicit maximum bond dimension is imposed, so unitary
evolution is performed using two-site TDVP without a hard cutoff on χ. Instead, bond
growth is controlled through a discarded-weight truncation criterion, i.e., after each
two-site update, singular values are truncated using a threshold of smax = 10−6."

**The paper's OWN algorithmic contribution** is not a dynamics kernel but the
cost-resolved decision layer: the three cost channels (Eqs. 8–10), the (α,κ) inflation
factors (Eq. 11), the hardware decision boundaries κ=α³ / κ=α⁵ (Eqs. 16–17), and the
pilot-extraction protocol (§V.A, Eq. 21).

### 2. Claimed gain — what it is and is NOT [paper]

**No speedup of TJM over "standard MCWF-on-MPS" is claimed anywhere** — TJM *is* an
MCWF-on-MPS method (§II.D); vs density-matrix integration it "avoids the exponential
overhead of density-matrix simulation" (§I). The quantified gains in THIS paper are
unraveling-choice gains between physically equivalent unravelings of the SAME Lindblad
generator:

- Bond-dimension inflation between the Pauli-jump (A) and measurement-based (B)
  unravelings: "Moderate inflation (α ∼ 1.2–1.5) appears at intermediate system sizes
  and noise strengths" (§IV.B); "Enhanced inflation, α ∼ 1.5–2.0, appears at
  intermediate noise strengths and fine time steps" (§IV.C). Means: μα = 1.46 (Fig. 2c),
  μα = 1.44 (Fig. 3c).
- Sampling inflation is independent and can be larger: μκ = 3.19, σκ = 2.21 (Fig. 5c);
  Heisenberg depolarizing κ = 11 at α = 2 (§V.B) — i.e. the lower-χ unraveling needs
  11× the trajectories there.
- Strict-dominance case exists: bit-flip (α,κ) = (1.5, 0.9) — the measurement-based
  unraveling wins BOTH channels (§V.B).
- Central negative result: "reduced trajectory bond dimension does not automatically
  imply reduced total cost" (§VI); and the finite-size caveat: "the noise-induced
  suppression of bond dimension becomes progressively less pronounced as L increases,
  and χ approaches a plateau-like regime" (§IV.B), with α narrowing toward unity at
  large L in their benchmark.

Benchmark scales (§I, §IV, §V): TFI chains up to L = 80 (Fig. 2), (γ,δt) maps at
L = 65 (Fig. 3), exact-reference sampling benchmark at 10 sites, T = 2, threshold
ε = 0.04 on ⟨X4X5⟩ (Fig. 5), Heisenberg L = 16 decision maps (Fig. 6). Hardware:
"a desktop equipped with an Intel Core i7-13600KF CPU with 20 threads and 64 GB of
RAM" (§IV.A). CPU-only, spin-1/2 only, N = 30 trajectories for the bond-dimension
maps (explicitly "insufficient for fully converged observables" but adequate for χ
trends, §IV.B).

**Open-source code** (§IV.A): "All benchmarks are performed using MQT-YAQS [37, 38],
our MPS-based framework for stochastic and time-dependent quantum simulation" —
Ref. [37]: github.com/munich-quantum-toolkit/yaqs (Python/Julia, MQT ecosystem).

### 3. Applicability to OUR carrier (mps_forward.py) [ours]

Our carrier (verified in source, `src/qec_twin/forward/scalable/mps_forward.py`):
9+ data qutrits as a quimb MPS, per-round within-cycle op stream (1-site qutrit H/X
unitaries; per-CZ Wood-Gambetta leak slice applied by **exact 1-site Kraus sampling**
of `exp(L/4)` — probabilities read from the 1-site reduced density matrix; "A 1-site
Kraus cannot grow the bond -> exact, no truncation"), then Born-sampled + projected
stabilizer parity measurements each round with a leaked-readout √E POVM, then a
transversal Y frame; discarded-weight truncation ledger. I.e., we are ALREADY an
MCWF-on-MPS trajectory method — but with an **exact channel-resolved Kraus unraveling
per slice**, not TJM's first-order no-jump/jump δt-splitting, and with **no TDVP**
(nothing to integrate: our within-cycle generator is a sum of 1-site terms already
exponentiated exactly; there is no multi-site Hamiltonian between gates).

Mapping, part by part:
- **Maps directly:** the (α,κ) pilot-extraction protocol (§V.A) — treat our existing
  exact-Kraus arm as "unraveling A(or B)" and any proposed TJM-style arm as the other;
  extract χ and trajectory-variance per arm under identical physical + numerical
  conditions; decide via κ vs α³ (thread-limited) / α⁵ (memory-limited). The paper
  explicitly acknowledges our unraveling class as a distinct point in this freedom:
  "Other trajectory constructions, including Kraus- or reset-based representations,
  may therefore produce qualitatively different finite-size behavior and can in some
  limits drive trajectories closer to product-state structure" (§IV.B) — named but
  NOT benchmarked.
- **Needs adaptation:** TJM's dynamics kernel (TDVP no-jump propagation under H_eff +
  first-order jump sampling) presumes a continuous-time Lindblad evolution with a
  nontrivial (generally multi-site) H0. Our within-cycle stream is a gate+channel
  CIRCUIT with purely 1-site dissipative slices — TDVP buys nothing (no multi-site H0
  to project onto the MPS manifold), and replacing our exact e^{L/4} Kraus slice by a
  first-order δt-split unraveling would ADD O(δt³)-class Trotter error where we
  currently have zero within-slice error. A TJM-style backend for us is therefore not
  "faster TDVP" but a DIFFERENT UNRAVELING of the same per-CZ slice (e.g. no-jump
  e^{−iH_eff δt} + jump splitting of the WG generator, or projector/measurement-based
  decompositions à la unraveling B) whose only possible win is trajectory-statistics /
  bond-growth redistribution at the STABILIZER-projection bottleneck — exactly what
  (α,κ) measures. The circuit-shaped variant of TJM is cTJM (2607.01323), which is the
  closer template for a gate-stream backend.
- **(a) Mid-evolution projective measurements / feedback: NOT treated.** No mid-circuit
  measurement of the simulated system, no syndrome records, no feedback anywhere in
  the paper. The "measurement-based unraveling (B)" uses projector jumps
  ("{|0⟩⟨0|, |1⟩⟨1|} for Z, …" §IV.A) as a stochastic REPRESENTATION of depolarizing
  noise, not as physical mid-circuit measurements. [ours] Structurally this shows
  projector insertions are perfectly at home in the trajectory formalism (our
  Born-sample+project step is the same operation type), but the paper's variance/κ
  analysis covers single-time expectation values only — nothing is proven about
  multi-time record statistics (our syndrome streams), and feedback is out of scope.
- **(b) Kraus channels vs continuous Lindblad:** the paper (and TJM) is continuous
  Lindblad with first-order jump probabilities; discrete Kraus-channel application is
  only mentioned as an alternative construction (§IV.B quote above), never benchmarked.
  Our exact per-slice Kraus sampling is OUTSIDE what the paper tests, INSIDE what its
  framework compares.
- **(c) Local dimension 3:** the cost model carries d explicitly — "mem(χ) ∝ L d χ2"
  (Eq. 8), "time(χ) ∝ (T/δt) L d χ3" (Eq. 9), m_j ∝ M/(L d χ²_j) (Eq. 12) — so
  qutrits enter trivially in the accounting; but ALL benchmarks are spin-1/2 (TFI,
  Heisenberg), and nothing dimension-specific about (α,κ) values at d=3 is measured.
  [ours] TJM/TDVP and jump sampling are dimension-agnostic; no obstruction to d=3,
  just no evidence either.

**Bottom line [ours]:** 2606.13779 does NOT itself justify a "TJM backend = faster"
expectation for our carrier; it justifies (and gives the protocol for) an
EXPERIMENTALLY DECIDED backend choice, and it warns that the decision must be made on
(α,κ) jointly, never on bond dimension alone. Any pre-registration for the parallel
backend should register the (α,κ) extraction as the primary measured outcome, with our
GPU-serialized workstation placing us at the thread-limited κ=α³ boundary.

### 4. Equivalence gate — what the paper proves/demonstrates, and what our gate should assert [paper unless tagged]

What the paper asserts about exactness:
- Unraveling equivalence (ensemble level): "While all valid unravelings reproduce the
  same mixed state dynamics upon ensemble averaging, they generally generate distinct
  trajectory ensembles." (§II.B); trajectory averaging is "a faithful estimator for the
  mixed quantum state at time t" (§II.A).
- Generator matching is an analytic PRECONDITION, not an output: "To ensure equivalence
  of the underlying master equation under this decomposition, the corresponding rates
  satisfy γB = 2γA =: 2γ." (§IV.A).
- Time-step convergence: O(δt^p) for (p+1)-order Trotterization (§II.C); TJM
  "provably convergent … fixed-accuracy error scaling of O(δt3)" for δt ≤ 0.1
  (§IV.C, proof in Ref. [28]).
- Sampling convergence: "ε ∝ 1/√N, indicating identical asymptotic scaling" for both
  unravelings, with unraveling-dependent pre-factors (§IV.D); N_U(ε) = (σ_U/ε)²
  (Eq. 21).
- Exact-oracle demonstration (small system): trajectory counts extracted as the N
  needed to reach "a fixed absolute deviation from exact reference evolution"
  (ε ≤ 0.04 on ⟨X4X5⟩, 10 sites, T = 2, Fig. 5) — for large systems only the standard
  error of the mean is available (§IV.A).

[ours] The equivalence GATE for a parallel TJM-style backend in our tree should
therefore assert, in this order:
1. **Channel matching (analytic, class (a)):** the backend's per-CZ slice unraveling
   must provably average to the SAME Wood-Gambetta `exp(L/4)` CPTP slice — exactly
   (Kraus-resolved) or to a declared O(δt³) with the Strang-split bound; the rate
   bookkeeping (the γB=2γA analog) is written down before any trajectory runs.
2. **vs the exact density-matrix oracle (small n, the existing `forward/exact` /
   certify seam):** ensemble means of the syndrome-record observables converge to the
   DM oracle at 1/√N with the registered σ, AND (for a δt-split backend) a δt-refinement
   sweep shows the O(δt³) slope toward the oracle — the paper's Fig.-5 protocol
   (absolute-deviation-vs-exact) lifted to our observables.
3. **vs the existing MCWF-on-MPS arm (same generator, two unravelings):** means agree
   within joint standard error at matched (δt, truncation threshold, ε_target); THEN
   extract (α,κ) per §V.A as the decision statistic. Disagreement beyond MC error =
   generator-matching bug, not a "regime effect".
4. **Truncation channel stays separately booked:** discarded-weight ledger per arm
   (the paper controls it at smax = 10⁻⁶ and assumes it subdominant, §IV.A/§IV.A
   fixed-accuracy paragraph) — our MpsTruncationLedger already does this per shot.
Caveat [ours]: the paper's single-time-observable equivalence is NECESSARY but not
sufficient for our multi-time syndrome records; the gate must score record-level
statistics (per-round marginals + the multi-time instruments we already use), since
nothing in the paper covers multi-time estimator variance across unravelings.

## Limitations
- Markovian Lindblad only — non-Markovian unraveling freedom (our finite-γ regime)
  is structurally richer and not analyzed here
- Single-time observables — multi-time syndrome statistics may have different
  variance scaling across unravelings
- Spin benchmarks only — bosonic mode truncation effects on (α,κ) not studied
- TJM-specific (TDVP evolution) — if we use TEBD or another integrator, the χ³
  scaling may differ (TEBD: χ³ → χ⁵ for some contractions)
- The protocol requires N_pilot trajectories that are "modest" — for our JC model
  at small d, pilot cost is negligible, but the projection to larger systems
  (d=5 surface code) requires extrapolation

## Tags
- `[paper]` (α,κ) framework: bond dimension inflation α + sampling inflation κ
- `[paper]` three cost channels: memory (χ²), runtime (χ³), sampling (σ²/ε²)
- `[paper]` decision boundaries: κ=α³ (thread-limited), κ=α⁵ (memory-limited)
- `[paper]` lower χ does NOT guarantee lower total cost — sampling overhead can dominate
- `[paper]` practical extraction protocol from N_pilot trajectories
- `[paper]` depolarizing (2.0,11), dephasing (1.5,3.8), bit-flip (1.5,0.9)
- `[ours]` our GPU-serialized constraint → thread-limited regime → κ vs α³
- `[ours]` at our system sizes (2 data qubits + mode), memory is NOT the bottleneck
- `[ours]` should pilot-test 2 unravelings on JC model at γ=0.15 and extract (α,κ)
- `[ours]` caveat: non-Markovian unraveling freedom, multi-time observables, bosonic mode
- `[paper]` TJM algorithm proper = Ref. [28] (Nat. Comm. 16, 11074 (2025)); this paper = the cost-decision layer on top; code = MQT-YAQS (github.com/munich-quantum-toolkit/yaqs)
- `[paper]` TJM = MCWF: H_eff no-jump (Eq. 2-3) + first-order δp=Σδtγ⟨L†L⟩ jumps (Eq. 4), two-site TDVP between jumps, discarded-weight smax=1e-6, O(δt³) fixed-accuracy for δt≤0.1 (via [28])
- `[paper]` no mid-circuit measurement/feedback/records; continuous-Lindblad only; Kraus-based representations named (§IV.B) but not benchmarked; spin-1/2 benchmarks only (d explicit in cost model)
- `[ours]` for OUR carrier a "TJM backend" = a different UNRAVELING of the same WG exp(L/4) slice (TDVP buys nothing at 1-site generators; first-order splitting would add error our exact Kraus doesn't have) — decide by (α,κ) pilot, not by assumption
- `[ours]` equivalence gate = channel matching (analytic) → DM-oracle 1/√N + O(δt³) refinement → two-arm agreement then (α,κ) → per-arm discarded-weight book; single-time equivalence necessary but NOT sufficient for multi-time syndrome records
