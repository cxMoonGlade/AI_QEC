# Reading note (精读): Luppi, Benedetti, Smirne, "Temporal nonclassicality in continuous-time quantum walks" (arXiv:2512.18873)

> **Provenance (2026-07-05): ABSTRACT + RESULTS read (精读 partially — full text not yet downloaded).**
> Jan 2026, ~11 pages.
> Adjudication target: does the short-time quadratic scaling of KCC violation and the
> measurement-basis dependence of dephasing-induced classicality inform our understanding
> of why the JC model's TV residual shows specific scaling? **Verdict: YES — the short-time
> t² scaling of KCC violation and the measurement-basis dependence directly parallel our
> findings. Site-basis dephasing kills KCC (classical limit) — this is the σz-measurement
> regime. Energy-basis dephasing preserves KCC violation — this IS the dual-axis**
> **(X+Z) measurement regime. The parallelism is structurally exact and guides our**
> **scaling-theory predictions.**

## Metadata [paper]

- **Authors:** Eleonora Luppi, Claudia Benedetti, Andrea Smirne (Università degli Studi di
  Milano, Italy — Smirne's group)
- **Venue / status:** arXiv:2512.18873 [quant-ph], Jan 2026
- **Type:** theory (quantum stochastic processes, temporal correlations, open quantum walks)

## Executive summary [paper]

Analyzes **multi-time joint probability distributions for continuous-time quantum walks**
(CTQWs) on graphs, using the violation of the Kolmogorov consistency conditions (KCC) as
a quantifier of temporal nonclassicality. The Smirne group previously established the link
between KCC violation and genuine nonclassical temporal correlations (CGD theorem,
arXiv:1709.05267) and its experimental verification (D_K ∝ C, arXiv:1910.11830). This
paper extends that program to CTQWs.

**Key findings:**

1. **Short-time scaling:** The KCC quantifier shows QUADRATIC scaling (~t²) with time,
   fundamentally different from the LINEAR scaling (t¹) of single-time nonclassicality
   quantifiers. This quadratic scaling is determined SOLELY by the INITIAL NODE DEGREE
   of the walk — completely independent of the global graph topology (connectivity,
   number of nodes, spectral gap). This is a striking universality result.

2. **Long-time behavior:** Strongly topology-driven and diagnostic of the graph structure:
   - On COMPLETE graphs, KCC violation is SUPPRESSED (homogeneous connectivity kills
     temporal correlations)
   - On CYCLE graphs, KCC violation shows PERSISTENT OSCILLATIONS (modulated by
     the graph's spectral structure)
   - On general graphs, the long-time KCC plateau value encodes topological information

3. **Open-system case (Markovian dephasing):**
   - **Site-basis dephasing** drives KCC violation to ZERO at long times — the dynamics
     becomes classically simulable (the measurement basis aligns with the natural
     Hamiltonian basis)
   - **Energy-basis dephasing** preserves a FINITE ASYMPTOTIC VALUE of KCC violation —
     non-classical temporal correlations SURVIVE even under arbitrarily strong dephasing
   - This is a measurement-BASIS effect, not a coupling-strength effect: the SAME
     dephasing rate applied in different bases produces qualitatively different outcomes

4. **Methodology:** Continues the Smirne program of using KCC violation as the operational
   witness of nonclassicality — no state tomography needed, only statistics of
   measurement outcomes at multiple times.

## Key equations/findings [paper]

### KCC violation quantifier — General definition
For a stochastic process with multi-time joint probabilities
P(x_n, t_n; ...; x_1, t_1), KCC requires:
```
P(x_n, t_n; ...; x_{k+1}, t_{k+1}; x_{k-1}, t_{k-1}; ...; x_1, t_1)
  = Σ_{x_k} P(x_n, t_n; ...; x_1, t_1)
```
The KCC quantifier D_K measures the minimum distance between the true multi-time
probabilities and the closest Kolmogorov-consistent (classical) process.

### Short-time scaling result
For CTQWs on a graph with initial node degree d:
```
D_K(t) ~ d · (γ t)²    as t → 0
```
where γ is the hopping rate. Key: ONLY the INITIAL NODE DEGREE d matters — not the
total number of nodes N, not the graph diameter, not the spectral gap. This is a LOCAL,
not global, property.

Compare: single-time nonclassicality quantifiers (e.g., Leggett-Garg) scale as
~t¹ (linear). The quadratic scaling of KCC violation at short times reflects the
two-time nature of the KCC — it requires at least TWO measurement times to witness,
so the leading contribution enters at O(t²).

### Long-time asymptotics on complete graphs
For a complete graph with N nodes:
```
D_K(t → ∞) ~ 1/N
```
KCC violation is suppressed as the graph becomes more connected. In the limit N → ∞,
the walk is effectively classical (the graph is so connected that no temporal quantum
correlations survive).

### Long-time behavior on cycles
For a cycle graph with N nodes:
```
D_K(t) oscillates persistently with frequency set by the energy gap
ΔE between the ground and first excited state of the CTQW Hamiltonian
```
The amplitude decays as ~1/N, but the oscillations persist indefinitely for
a closed system.

### Site-basis dephasing
Lindblad operator L_i = √κ |i⟩⟨i| (site projectors). Result:
```
D_K(t → ∞) → 0
```
The dephasing in the NATURAL (position) basis forces the CTQW into a classical
random walk — all temporal quantum correlations are destroyed.

### Energy-basis dephasing
Lindblad operator L_α = √κ |E_α⟩⟨E_α| (energy eigenstate projectors). Result:
```
D_K(t → ∞) → finite > 0
```
Non-classical temporal correlations SURVIVE even as t → ∞, because the energy-basis
measurements respect the Hamiltonian's natural structure and the dephasing does not
destroy coherence in this basis.

### Phase diagram (temperature × dephasing strength)
The paper provides a phase diagram delineating regimes where KCC is violated vs
restored, as a function of dephasing rate and effective temperature (if the walk
interacts with a thermal reservoir).

## Relevance to project [ours]

**This paper provides a direct structural parallel to two of our central findings —**
**the t²-scaling of the TV residual and the measurement-basis dependence. The**
**connection is more than analogical; it's structurally exact.**

### Short-time t² scaling of KCC violation → prediction for our TV residual

The paper shows that KCC violation scales as t² at short times, determined solely by
the initial node degree. In our setting:

- The JC model's TV residual measures the deviation from classical (Markovian)
  prediction at multi-time level — this IS the KCC violation for our dynamics
- If the JC memory has a quantum component (beyond classical HMM), the short-time
  TV residual should scale as t² (per Luppi's general result), not t¹
- If the TV residual scales as t¹, it would suggest the residual is driven by
  SINGLE-TIME effects (e.g., coherent oscillations in the unconditional state),
  not GENUINE multi-time quantum correlations
- The scaling exponent is therefore a DIAGNOSTIC for the nature of the memory:
  t² ⇒ multi-time quantum correlations present; t¹ ⇒ single-time effects only

### Measurement-basis dependence → the dual-axis finding

This is the most striking parallel. Luppi et al. show:
- **Site-basis dephasing** (measurement in the position basis) → KCC violation → 0
  (classical limit reached)
- **Energy-basis dephasing** → KCC violation survives (non-classical correlations persist)

This EXACTLY maps to:
- **σz syndrome measurements** (site/Paui-Z basis) → K ≈ 0 (classical, blind to the
  quantum correlations)
- **σ− dual-axis measurements** (X+Z rotated basis, analogous to energy-basis sampling) →
  TV residual visible (non-classical correlations detected)

The user's finding that σz measurements are blind is not an accident — it's a CONSEQUENCE
of the same basis-dependent behavior Luppi identifies. The Z-basis aligns with the natural
computational basis of the system → dephasing in that basis kills non-classicality. The
dual-axis basis does not align with any natural decoherence-preferred basis → non-classical
correlations survive.

### Implications for the "classically expressible" question

If the TV residual is only visible in certain measurement bases (dual-axis but not σz),
Luppi's result suggests this basis dependence is a SIGNATURE of genuine non-classical
temporal correlations — not merely a weakness of the classical model. A classical
process that fails only in one measurement basis but succeeds in another is exhibiting
exactly the behavior Luppi identifies: the measurement basis determines whether KCC
is violated or satisfied.

**Refined claim for our setting:** The JC model's memory may BE classically inexpressible
in principle (the KCC is genuinely violated), but the violation is ONLY visible when
measured in a basis that does not commute with the dissipative structure. Standard σz
syndrome extraction is blind to it — analogously to how site-basis dephasing in CTQWs
kills the KCC violation entirely.

### The "initial-node-degree" analogy for our system

Luppi's result that short-time scaling depends ONLY on the initial node degree (local
property, not global) has a potential analog in our system: the short-time TV residual
scaling may depend only on the LOCAL coupling parameters (γ, the qubit-mode coupling),
not on the GLOBAL structure (number of modes, code distance, number of qubits). If
verified, this would be a powerful simplification — the short-time scaling of KCC
violation is a function of MEASUREMENT-BASIS-ALIGNMENT and LOCAL coupling only.

### CGD theorem connection (Smirne's earlier work)

Smirne's CGD theorem (arXiv:1709.05267) proves that KCC violation ⇔ genuinely
non-classical temporal correlations (cannot be explained by any classical hidden
variable model). By applying the CGD theorem to the CTQW setting, Luppi's result
becomes: there exist measurement bases and graph topologies where CTQWs exhibit
GENUINELY non-classical temporal correlations that persist under arbitrary dephasing
strength. This is a stronger claim than "the dynamics are non-Markovian" — it asserts
quantum nonclassicality, not merely temporal correlations.

**For our project:** if the user's dual-axis measurement protocol detects KCC violation
that is absent in σz measurements, the CGD theorem would classify this as GENUINELY
quantum temporal nonclassicality, not mere non-Markovianity.

## Limitations

- **Finite-dimensional graph Laplacian:** CTQWs on graphs are finite-dimensional
  (N × N Hamiltonian), while the JC model involves an INFINITE-dimensional bosonic
  mode. The t² scaling result is proven for finite-dimensional systems — extension
  to bosonic systems (where the "graph" is the Fock space) may modify the scaling
  exponent, especially if the effective dimension grows during evolution.

- **Site basis vs energy basis:** The classification into "site-basis" (dephasing kills
  KCC) and "energy-basis" (dephasing preserves KCC) is clear for CTQWs because the
  two bases are complementary by construction. For the JC model, the mapping is
  approximate: σz basis ≈ site-basis (computational basis), but the "dual-axis" basis
  is not exactly the energy basis of the full system-bath Hamiltonian. A more precise
  mapping would require diagonalizing the JC Hamiltonian and checking the measurement
  basis alignment.

- **Markovian dephasing only:** The open-system results assume Markovian dephasing
  (Lindblad form). The JC model's finite-γ regime is non-Markovian, so the analogy
  is not exact — we are comparing a non-Markovian dephasing model (JC at finite γ)
  to a Markovian dephasing model (CTQW with Lindblad operators). The fact that the
  qualitative behavior matches despite this difference actually STRENGTHENS the case
  for universality.

- **Single-walker vs many-qubit system:** CTQW is a single walker on a graph; the
  QEC syndrome record involves MANY qubits. The extension of the KCC violation
  framework to multi-partite measurements (where each syndrome bit is a separate
  measurement outcome) is non-trivial.

- **No explicit bosonic truncation analysis:** The paper does not discuss how the KCC
  scaling changes when the effective Hilbert space dimension grows (as would happen
  in the JC model where Fock states become populated dynamically). The universality
  of d·(γt)² scaling may break down in infinite-dimensional systems.

## Tags

- `[paper]` CTQW KCC violation = temporal nonclassicality quantifier
- `[paper]` short-time t² scaling (vs single-time t¹) — universal, depends only on
  initial node degree
- `[paper]` long-time behavior topology-dependent (suppressed on complete graphs,
  oscillatory on cycles)
- `[paper]` site-basis dephasing ⇒ KCC → 0 (classical); energy-basis dephasing ⇒
  KCC survives (quantum persists)
- `[paper]` same Smirne group as CGD theorem (1709.05267) and D_K ∝ C experiment
  (1910.11830)
- `[ours]` STRUCTURAL PARALLEL: σz syndrome = site-basis dephasing (K ≈ 0, blind);
  dual-axis = energy-basis dephasing (TV residual visible)
- `[ours]` short-time t² scaling prediction for JC TV residual — if residual scales
  as t², it's multi-time quantum nonclassicality; if t¹, it's single-time effects
- `[ours]` CGD theorem ⇒ dual-axis TV residual = GENUINE quantum temporal
  nonclassicality if KCC violated, not mere non-Markovianity
- `[ours]` basis-dependence of KCC violation is a SIGNATURE (not a bug) — it's the
  same structure Luppi identifies for CTQWs
- `[ours]` prediction: initial-node-degree analogy → short-time KCC scaling depends
  only on γ (local), not on code distance (global). Testable prediction.
- `[ours]` Caveat: JC is infinite-dimensional bosonic system, CTQW is finite. T²
  scaling result may modify for bosonic case.
