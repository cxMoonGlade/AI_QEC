# Full-text review — P. Sierant, M. Schirò, M. Lewenstein & X. Turkeshi, "Measurement-induced phase transitions in (d+1)-dimensional stabilizer circuits" (arXiv:2210.11957, published version)

> **Provenance: FULL-TEXT read (精读).** Source: `docs/papers/sierant_dplus1_stabilizer_measurement_transitions_2210.11957.txt`
> (1942 lines, arXiv:2210.11957v1 [cond-mat.stat-mech], 21 Oct 2022 — includes main text Secs. I–IX,
> Table I, Figs. 1–13, Appendices A–B, and full reference list). Every quantitative claim below is taken
> directly from the body text / equations / table, with line and equation numbers cited. ID/title verified
> against the paper's own header line ("Measurement-induced phase transitions in (d+1)-dimensional
> stabilizer circuits", Sierant/Schirò/Lewenstein/Turkeshi).

## Metadata [paper]

- **Authors / affiliation:** Piotr Sierant (ICFO Barcelona), Marco Schirò (Collège de France / CNRS),
  Maciej Lewenstein (ICFO / ICREA), Xhek Turkeshi (Collège de France / CNRS).
- **Venue / status:** arXiv:2210.11957v1 [cond-mat.stat-mech], 21 Oct 2022. Large-scale numerical
  statistical-mechanics / quantum-information paper (condensed-matter / stat-mech methodology, not a
  QEC paper).
- **Type:** Numerical study (Clifford-simulability, Stim-based) of measurement-induced phase transitions
  (MIPT) in random hybrid stabilizer circuits, in (1+1)D, (2+1)D and (3+1)D — up to N = 32768 qubits.
- **Key relationship to our work:** This is the most rigorous, largest-scale published numerical
  characterization of the entanglement-vs-measurement-rate phase diagram in exactly the spatial
  dimensionalities relevant to a 2D (surface-code) or 3D (surface-code × time, if you count time as an
  extra dimension) syndrome-extraction geometry. It gives quantitative critical measurement rates `p_c`
  for several stabilizer-circuit architectures in d = 1, 2, 3 — directly informative for the question
  "is p ≈ 1 (near-maximal measurement) definitely deep in the bounded/area-law phase?" It is **not** a
  QEC or leakage paper: no code structure, no decoder, no non-Pauli/leakage physics anywhere in it.

## Executive summary [paper]

The paper studies (d+1)-dimensional hybrid stabilizer circuits (Clifford-random two-qubit gates
interleaved with local projective Z-measurements at a per-site rate `p`), simulated exactly via Stim's
Gottesman-Knill tableau formalism, for d = 1, 2, 3 spatial dimensions and lattice sizes up to L = 128
(2D, N = 16384) and L = 32 (3D, N = 32768). It finds a genuine measurement-induced phase transition
(MIPT) between a **volume-law entangled "QEC phase"** (p < p_c, entanglement entropy of a subregion
scales with its volume `|A|`) and an **area-law "quantum-Zeno (QZ) phase"** (p > p_c, entanglement
scales with the region's boundary `|∂A|`) for every d tested. The transition is located and characterized
via four independent observables — half-system entanglement entropy, tripartite quantum mutual
information (TQMI), purification dynamics of a maximally-mixed initial state, and participation entropy
of the wavefunction — all giving mutually consistent critical points and exponents. The critical exponents
for d = 2, 3 are compatible (within 1 error bar) with (d+1)-dimensional **classical percolation** theory,
and the transition point appears to be described by an emergent **conformal field theory** (verified via
torus entanglement entropy against the Extensive Mutual Information CFT model). Critically for our use
case: the **critical measurement rate `p_c` is strongly architecture/geometry-dependent** (ranging from
0.15 to 0.78 across the seven circuit architectures tested), while the **universality class (critical
exponents) is architecture-independent**.

## Method (deep) [paper]

**Model class (Sec. III):** Random hybrid stabilizer circuits on a d-dimensional hypercubic lattice Λ
(periodic BC unless noted), built from two ingredients:
1. **Measurement layer** (Eq. 20): every site `i` is stochastically measured in the Z basis with
   probability `p` per round (outcome ± with Born-rule probability, or left untouched — `M_i^0 = 1`
   — with probability `1-p`). This is a **uniform, spatially-random, per-site Bernoulli measurement
   process**, not a fixed deterministic pattern.
2. **Unitary layer:** two-qubit (or, in Appendix A, 4-body / 8-body) gates drawn **uniformly at random
   from the Clifford group**, arranged either (a) in a fully randomized fashion — random pairing of
   `|Λ|/4` neighbor pairs each round, Eq. 22 (the paper's main-text architecture for d ≥ 2) — or (b) in
   structured brick-wall / plaquette / cubic patterns (Appendix A, used only as a universality
   cross-check against prior literature, Refs. [91, 92]).

Because gates are Clifford and measurements are Pauli-string projections, the full many-body state stays
a stabilizer state at all times (Gottesman-Knill theorem, Sec. III A) and is exactly, polynomially
simulable via a tableau (Stim). This is a **classically-efficient toy model of monitored quantum
dynamics**, deliberately built to allow N up to 32768 — it is emphatically **not** a leakage/non-Clifford
model, and it is **not** a fixed deterministic syndrome-extraction circuit; it is a statistical ensemble
over random unitary + random measurement locations at a fixed overall rate `p`.

**Observables (Sec. II a–f, IV–VII):**
- Half-system / regional entanglement entropy `S_A` (Eq. 4/23-24), computed exactly via the F2-rank
  formula for stabilizer states.
- Tripartite quantum mutual information `I_3` (Eq. 5) on a quadripartition A,B,C,D — used to pinpoint
  `p_c` via a scale-invariant crossing point (`I_3 = O(1)` at criticality, Eq. 6), then finite-size
  scaling `I_3(p,L) ≈ F[(p-p_c)L^{1/ν}]` (Eq. 8) to extract `p_c`, `ν`.
- Purification entropy `S_pur` of an initially maximally-mixed state (Eq. 28), whose finite-size
  collapse in `t/L^z` gives the dynamical exponent `z`, and in `(p-p_c)L^{1/ν}` at fixed `t/L` gives an
  independent `(p_c, ν)` estimate (Eq. 9).
- Participation entropy `S_part` (Eq. 10-11) sub-leading fractal term `c` — a third independent probe
  of `(p_c, ν)` (Eq. 12).
- Ancilla-qubit purification / mutual-information exponents (`β, β_s, η, η_⊥, η_∥`, Sec. VII) — bulk and
  boundary critical exponents from coupling reference ancilla qubits to the bulk system.

**Control parameter:** the single scalar `p` (per-site, per-round measurement probability). This is the
entire "knob" of the model.

## Results + numbers [paper]

| Quantity | d = 1 (1+1D) | d = 2 (2+1D) | d = 3 (3+1D) |
|---|---|---|---|
| `p_c`, randomized architecture (main text) | 0.15995(10) (Sec. IV.a) | 0.1475(1)–(2) (Eq. 26) | 0.1937(1) (Eq. 27) |
| `p_c`, alternative structured architectures (Appendix A) | — | brick-wall 0.3116(1); plaquette 0.5517(1) | cubic (8-body gates) 0.7814(4) |
| `ν` (correlation length exponent, entanglement/TQMI) | 1.260–1.265(15) | 0.87–0.89(2) | 0.68–0.69(2) |
| Compare: classical percolation `ν` in (d+1) spatial dim | 2D: 1.333 (exact) | 3D: 0.8774(13) | 4D: 0.686(2) |
| Dynamical exponent `z` (purification) | 1.00(1) | 1.01(2) | 1.02(4) |
| `p_c` from purification | 0.15995 (shared with entanglement) | 0.1476(1) | 0.1937(5) |
| `p_c` from participation entropy | — | 0.1478(6) | 0.195(2) |
| Bulk order exponent `β` / boundary `β_s` | 0.129(8) / 0.46(2) | 0.44(1) / 0.86(2) | 0.60(3) / 1.14(9) |
| Max system size simulated | L = N = 10240 (TQMI) | L = 128, N = 16384 | L = 32, N = 32768 |
| Entanglement scaling below `p_c` (QEC phase) | `S_AB ∝ L` (volume-law) | `S_AB ∝ L^2` (volume-law) | `S_AB ∝ L^3` (volume-law) |
| Entanglement scaling above `p_c` (QZ phase) | `S_AB ∝ const` (area-law) | `S_AB ∝ L` (area-law) | `S_AB ∝ L^2` (area-law) |
| Critical-point entanglement scaling | `ceff·log L`, ceff=1.57(1) | linear in L (3D CFT-consistent) | scales as `L^2` (4D CFT-consistent) |
| Universality-class verdict | close to but **distinct** from 2D percolation (5 error bars, Sec. IV.a) | compatible with 3D percolation within **1** error bar | compatible with 4D percolation within **1** error bar |

**All `p_c` values found across every architecture/dimension tested lie strictly below 0.79** — the
largest is the most highly-connected (3+1)D 8-body-gate "cubic" circuit at `p_c = 0.7814(4)` (Appendix
A, Eq. A4-A5).

## The regime boundary [paper → the crux]

**What makes entanglement bounded (area-law/QZ) vs growing (volume-law/QEC), precisely:**

- The **sole control parameter in this model class is `p`**, the per-site per-round probability of a
  projective measurement (Eq. 20). Below a critical `p_c`, the scrambling unitary layer wins and the
  steady-state entanglement entropy of an extensive subregion grows **with the volume of the region**
  (`S_A ∝ |A|`, i.e., unboundedly with system size — this is exactly "volume-law growth"). Above `p_c`,
  local measurements disentangle faster than the unitary layer can scramble, and steady-state
  entanglement of an extensive region saturates to scale with **only its boundary** (`S_A ∝ |∂A|`) —
  bounded, area-law entanglement (Sec. II b, Eq. 6, confirmed numerically Figs. 2-4(a)). Since, for a
  stabilizer state, an area law on entanglement entropy across any cut directly bounds the Schmidt rank
  (hence tensor-network bond dimension) needed across that cut, **area-law ⟺ bounded bond dimension;
  volume-law ⟺ bond dimension growing exponentially with subsystem size.**

- **`p_c` is NOT universal — it is strongly geometry/architecture-dependent** (Table above): for fixed
  spatial dimension d, increasing the "scrambling power" of the unitary layer (2-body random gates →
  4-body plaquette/brick-wall → 8-body cubic gates) monotonically **raises** `p_c` (e.g., (2+1)D:
  0.1475 → 0.3116 → 0.5517; (3+1)D: 0.1937 → 0.7814). More powerful/dense entangling gates require a
  correspondingly higher measurement rate to reach the area-law phase. This is stated explicitly as the
  paper's own robustness check (Appendix A) — the transition's *existence*, *location*, and *universality
  class* are studied deliberately across multiple geometries to demonstrate the phenomenon is generic, but
  the **numeric value of `p_c` itself moves substantially with circuit structure.**

- **Critical exponents (the universality class), by contrast, are geometry-independent** within errors:
  for d = 2 and d = 3, every architecture tested (randomized, brick-wall, plaquette for d=2; randomized,
  cubic for d=3) gives `ν` compatible with the *same* percolation universality class in (d+1) spatial
  dimensions (Sec. VIII, Fig. 9). Sec. VIII's discussion (lines ~1246–1286) even raises — via a mapping
  to a large-local-Hilbert-space statistical mechanics model (Ref. [94]) — a theoretical expectation that
  qubit (q=2) circuits should show the *largest* deviations from pure percolation universality (since
  finite-q perturbations are theoretically expected to be most relevant at small q); the paper's own
  numerics find these deviations to be "very mild" for d ≥ 2 and leaves the mismatch between this
  expectation and the numerics as an **open question** (lines 1281–1286, "We leave this open dilemma
  for future investigations").

- **Where a near-maximal measurement-rate (p ≈ 1) circuit sits:** since every measured `p_c` across
  seven distinct architectures in d = 1, 2, 3 tops out at 0.7814, a circuit operating at `p ≈ 1` sits
  deep in the area-law/QZ phase for **every architecture this paper tested**, regardless of spatial
  dimension. The paper gives no example — even among its most strongly-scrambling 8-body-gate cubic
  circuit — where `p_c` approaches 1.

- **Caveats that could push toward growth / limit transfer to a real syndrome circuit (IMPORTANT — flag
  as analogy, not identity):**
  1. **Wrong model class.** This is a purely **Clifford, Haar-random-gate + random-location Pauli-basis
     projective measurement** ensemble. A real syndrome-extraction circuit is (a) fully **deterministic**
     (fixed CNOT/CZ schedule, fixed ancilla layout, no randomness in gate choice or measurement location),
     and (b) its "measurements" are not single-qubit Z-basis projections at a scalar rate `p` uniformly
     applied to every site — they are **weight-4 stabilizer parity checks** realized via ancilla-mediated
     multi-qubit circuits, with a strict **bipartite schedule**: ancilla qubits ARE measured every single
     round (`p=1` restricted to that sublattice) while data qubits are **never** directly measured
     (`p=0` on that sublattice). The paper's uniform scalar `p` does not literally represent this
     structure; "p ≈ 1" is an **analogy** (near-maximal fraction of qubits measured per round), not a
     rigorous identification of control parameters.
  2. Because `p_c` moved from 0.15 to 0.78 purely by changing gate connectivity/geometry within this
     paper's own tested architectures, the "regime boundary" is demonstrably sensitive to exactly the
     kind of structural detail (which sites are measured, how entangling the intervening unitary is) that
     differs between these toy circuits and a real stabilizer-code syndrome circuit. This paper cannot
     bound how a syndrome circuit's own (very different, low-scrambling, weight-4, ancilla-mediated)
     structure maps onto an effective `p_c`.
  3. **Zero non-Pauli/leakage physics.** The entire formalism is exact-stabilizer (Clifford); there is no
     leakage, no continuous-variable or qutrit dynamics, no non-Clifford coherent error anywhere in this
     paper. It cannot bound whether non-Pauli leakage (our actual physics) reintroduces
     entanglement/bond growth that a pure-Clifford measurement-rate argument would miss.
  4. The paper's entanglement-entropy observable is for **global bipartitions of an infinite/periodic
     bulk system in its late-time steady state** (t ≥ 10L), not the specific per-edge bond dimension of a
     finite, open-boundary, non-translation-invariant d=5 patch with logical structure evolving for a
     fixed ~40 rounds. The area-law argument is generic (bounded entanglement ⟹ bounded bond dimension),
     but the finite-size/open-boundary/short-time specifics of a real d5 patch are not directly modeled.
  5. Sec. IX's own listed limitation: detecting/verifying MIPT signatures experimentally for d > 1 suffers
     an exponential post-selection cost (this is about *experimental verification* of the transition, not
     about classical/tensor-network simulation, but it is a reminder that "p≈1 is deep in area-law" is a
     **numerical/theoretical** conclusion about this toy ensemble, not something independently verified
     on a real, structured, deterministic circuit at scale).

## Relevance to the d5 PEPS crux [ours]

**Verdict: SUPPORTS "bond should saturate" as the qualitative default expectation — but only as an
analogy-level prior, not a quantitative guarantee for our specific circuit.**

- This is the single most rigorous, largest-scale piece of evidence available that **near-saturating
  local measurement rates drive stabilizer-type circuits deep into a bounded, area-law entanglement
  phase**, and that this holds in exactly the spatial dimensionalities relevant to us (d = 2: a
  syndrome-extraction round applied across a 2D code patch; d = 3 if the time direction is counted as a
  third dimension for a fixed-depth trajectory). Across seven distinct circuit geometries (2-body,
  4-body, 8-body gates; randomized, brick-wall, plaquette, cubic patterns) spanning d = 1, 2, 3, **no
  architecture required `p` above 0.7814 to reach the area-law phase** — meaning a circuit that measures
  essentially all of its qubits every round (`p ≈ 1`) is, for every tested member of this large model
  class, safely and substantially inside the bounded regime, not near any observed boundary.
- This is consistent with — and strengthens the prior for — our working hypothesis that the pilot's
  observed bond growth (4 → 18 → >40 in 2 rounds) is an **instrument artifact** (the compiled weight-4
  √E_s POVM injecting spurious entanglement, and/or non-optimal truncation) rather than genuine
  volume-law physics: if anything, a real stabilizer syndrome circuit is a **much gentler, less
  scrambling** unitary than any of this paper's random-Clifford architectures (by design — a QEC code's
  whole purpose is to keep correlations *local* via weight-4 checks, not to scramble information across
  the lattice), so a syndrome circuit should sit even more comfortably inside the area-law phase than
  the `p ≈ 1` point already does in this paper's toy ensemble, *if* the qualitative "high measurement
  rate → area law" intuition transfers.
- **It does NOT, by itself, prove our specific carrier saturates**, for the reasons in the "regime
  boundary" section above: wrong model class (random Clifford vs. deterministic weight-4 ancilla-mediated
  stabilizer schedule), no literal scalar-`p` mapping to a syndrome circuit's bipartite
  ancilla-measured/data-unmeasured structure, zero leakage/non-Pauli content, and a demonstrated strong
  sensitivity of `p_c` itself to exactly the structural details (connectivity, gate power, geometry) that
  differ between this paper's toy circuits and ours. The paper's own open question (Sec. VIII, whether
  finite-local-dimension / structural perturbations could shift universality class) is a live reminder
  that "this generic mechanism favors area-law at p≈1" is not the same claim as "a d5 rotated-XZZX
  syndrome circuit with weight-4 checks and non-Pauli leakage provably has a bounded per-edge bond."
- **Net implication for the pilot:** the growth we saw is *not* what the broader measurement-induced
  transition literature would predict for a near-saturating-measurement-rate circuit of this general
  type — this raises the prior that it is an artifact of our specific compiled POVM/truncation scheme,
  worth debugging before concluding a genuine volume-law obstruction. It does not substitute for
  measuring our own carrier's bond-dimension trajectory directly and diagnosing the specific instrument.

## How to use / trust + open questions [ours]

- **Trust level:** FULL-TEXT 精读 (1942 lines, main text + two appendices + full reference list read).
  Peer-reviewed-grade large-scale numerics (N up to 32768, Stim-based exact stabilizer simulation);
  critical exponents cross-checked against three independent observables (entanglement/TQMI,
  purification, participation entropy) and, for d=2, against two independently published prior works
  (Refs. [91, 92]) whose discrepancies with each other the paper explicitly resolves via larger system
  sizes.
- **Independent re-orability:** the paper's core claim (area-law phase exists above a geometry-dependent
  `p_c` well below 1, for d=1,2,3 stabilizer circuits) is directly reproducible with Stim (already a
  project dependency, `external/baselines/`) — a cheap sanity check would be to reproduce Fig. 3
  (2+1D randomized circuit, `p_c ≈ 0.1475`) independently, both as a trust-building exercise and as a
  **calibration of our own entanglement/bond-dimension diagnostic tooling** (distinguishing a genuine
  transition/growth signal from a measurement or truncation artifact in our own pipeline).
- **Open questions for our d5 PEPS carrier:**
  1. Is there a way to define an effective scalar "measurement rate" for a real weight-4,
     ancilla-mediated, bipartite (ancilla-always-measured / data-never-measured) syndrome circuit that
     could be benchmarked against this paper's `p_c` values, rather than relying on the qualitative
     "p ≈ 1" analogy? (E.g., treating the ancilla sublattice alone as `p=1` might be closer to the
     paper's per-site convention than treating the full lattice as `p ≈ 0.5`.)
  2. Does the paper's `p_c` sensitivity to unitary-layer connectivity (0.15 → 0.78 as gates go from 2-body
     to 8-body) suggest that a d5 rotated-XZZX code's own weight-4 CNOT-mediated entangling structure
     (which is neither purely 2-body nor as scrambling as a random 8-body gate) could plausibly sit
     anywhere in that range if it were mapped onto this model class? If so, the "p≈1 is safe" conclusion
     is directionally reassuring but not quantitatively pinned down.
  3. Sec. VIII's open dilemma (large local-Hilbert-space arguments predict qubit circuits should show
     the *largest* deviation from percolation universality, yet numerics show "very mild" deviations) —
     does this generalize to our qutrit (leakage) local dimension? If leakage effectively increases local
     Hilbert-space dimension, could it push our carrier further from (or closer to) the percolation-like
     area-law-favoring regime? This paper offers no data on qutrit/leakage circuits and cannot answer this.
  4. The purification dynamical exponent `z ≈ 1` (all d) implies that, **at criticality**, the timescale
     to reach the steady-state (area-law) entanglement scales linearly with system size `L`; away from
     criticality in the QZ phase it is faster. For a d=5 patch (`L` on the order of the code distance),
     this suggests that IF our carrier is in the area-law phase, saturation should occur within at most
     ~O(L) rounds — consistent with expecting saturation well before our target ~40 rounds, and giving a
     concrete, checkable prediction (plot chi vs. round count; look for saturation within the first
     several rounds, not continued growth through round 40).
  5. **Immediate actionable check:** since this paper and its own random-circuit numerics show
     bond/entanglement growth then saturation is the expected SHAPE of the curve even inside the
     area-law phase (early transient growth, e.g., their own purification data plotted vs. `t/L^z` shows
     `S_pur` decreasing monotonically only after being sourced from a maximally mixed state — analogous
     early-round transients are normal), the 2-round pilot data (4→18→>40) is too short a window to
     distinguish "transient before saturation" from "genuine volume-law growth." The paper's own
     methodology (Sec. IV: evolve to `t = 10L` before calling the state "steady") argues for running our
     pilot to several times the natural length scale (rounds ≳ few × d) before drawing a bond-saturation
     conclusion either way.
- **Bottom-line verdict for our architecture:** this paper is the strongest available *generic* physics
  argument that near-saturating measurement rates favor bounded (area-law) entanglement across a wide
  range of stabilizer-circuit geometries in d = 1, 2, 3 — none of which needed `p` above ~0.78 to reach
  that phase. It raises the prior that our pilot's fast bond growth is an artifact rather than physics,
  and gives a concrete methodological lesson (evolve longer before judging saturation vs. growth). It
  does **not** constitute a proof for our specific, deterministic, weight-4, leakage-bearing syndrome
  circuit — the mapping from this paper's scalar random-Clifford `p` to our circuit's structure is an
  analogy, and the paper is entirely silent on the non-Pauli/leakage physics that is our carrier's actual
  distinguishing feature. Treat as a strong prior + methodological guide, not as ground truth for the d5
  PEPS bond-saturation question — that must still be measured directly, with the compiled-POVM/truncation
  instrument scrutinized first.
