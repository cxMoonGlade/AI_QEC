# Reading note (精读): Budini, "Superclassical non-Markovian open quantum dynamics" (arXiv:2411.13471)

> **Provenance (2026-07-05): FULL-TEXT read (精读).** PDF → txt `outputs/papers/2411.13471.txt`
> (12 pages, PyMuPDF). All §/Eq refs from that text. Published as Phys. Rev. A 111, 052202 (2025).
> Adjudication target: does this paper ground the claim that measurement invasiveness (and thus K)
> depends on the commutation relation between the coupling operator and the measured observable?
> **Verdict: PARTIALLY — it defines the DNI framework and the superclassicality condition that ARE
> the formal structure for that dependence, but it treats single-qubit projective measurements, not
> multi-qubit stabilizer-parity extraction.**

## Metadata [paper]
- **Author:** Adrián A. Budini (CONICET / UTN-FRC, Bariloche, Argentina)
- **Venue / status:** arXiv:2411.13471v2 [quant-ph], 9 Mar 2025 → Phys. Rev. A 111, 052202 (2025)
- **Type:** theory (operational definition + characterization of superclassical non-Markovian dynamics)
- **Predecessor:** Budini, "Violation of Diagonal Non-Invasiveness" (arXiv:2301.02500) — the DNI
  concept is introduced there; this paper characterizes the dynamics that SATISFY it.

## Executive summary [paper]
Budini defines **superclassical** non-Markovian dynamics: processes that, despite having memory
(non-Markovianity), satisfy **Diagonal Non-Invasiveness (DNI)** — a projective measurement whose
observable commutes with the pre-measurement state does NOT alter subsequent statistics, for
arbitrary previous and posterior measurement choices. This guarantees that Kolmogorov consistency
conditions hold. The paper characterizes which bipartite system-environment Lindblad evolutions
satisfy this strong condition, finding that:
1. **Without discord generation:** depolarizing collisional dynamics where a depolarizing map is
   applied whenever the environment undergoes a transition [Eq. (26)]
2. **With discord generation:** more constrained; requires extra propagator conditions [Eqs. (29)-(30)]
The unifying structure: the system dynamics must be depolarizing [Eq. (13)], and the
system-environment coupling must be non-unitary (unitary coupling generically violates DNI).

## Key definitions (exact) [paper]

### DNI (Diagonal Non-Invasiveness) — Eq. (5)
```
△_Z ∘ G_{t+τ,t} ∘ △_Y^t ∘ G_{t,0} ∘ △_X = △_Z ∘ G_{t+τ,t} ∘ G_{t,0} ∘ △_X
```
- △_X, △_Z: **arbitrary** dephasing maps (arbitrary measurement bases for first and last measurement)
- △_Y^t: the dephasing map that **leaves invariant** the pre-measurement state ρ_{t|X}
  [Eq. (7): △_Y^t[ρ_{t|X}] = ρ_{t|X}] — i.e., the intermediate measurement commutes with the
  pre-measurement state
- G: bipartite system-environment propagator (semigroup), ρ_{t+τ}^{se} = G_{t+τ,t}[ρ_t^{se}]
- Compare with Milz et al. operational classicality [Eq. (4)]: there, △ is FIXED (same basis for
  all measurements); here, △_X and △_Z are ARBITRARY — a much stronger condition

### Kolmogorov consistency condition — Eq. (10)
```
I(t,τ) = Σ_{zx} |P_3(z,x) − P_2(z,x)| = 0
```
Where P_3(z,x) = Σ_y P_3(z,y,x) is the marginal with intermediate measurement performed,
P_2(z,x) is the joint without intermediate measurement. I(t,τ) = 0 ⇔ DNI holds ⇔ the
process is "superclassical" (memory without measurement invasiveness).

### CPF (Conditional Past-Future) correlation — Eq. (11)
```
C_pf(t,τ) = Σ_{zx} zx [P_3(z,x|y) − P_3(z|y) P_2(x|y)]
```
C_pf ≠ 0 ⇒ non-Markovian. C_pf = 0 ⇒ Markovian. Superclassical = C_pf ≠ 0 AND I = 0
simultaneously.

### Superclassical system dynamics must be depolarizing — Eq. (13)
```
ρ_t = U_t [λ_t ρ_0 + (1−λ_t) I_s/d] U_t^†
```
Master equation form [Eq. (14)]: dρ_t/dt = −i[H_s, ρ_t] + γ_t (D_I[ρ_t] − ρ_t) where
D_I[ρ] = I_s/d. Note: γ_t can be negative (non-Markovian) while the dynamics remains
superclassical.

## Key results for the K-survival proposition [paper → ours]

### 1. Unitary system-environment coupling VIOLATES DNI
Section IV B 2: For Hamiltonian H_se = (Ω/2) Σ_k σ_k ⊗ σ_k with maximally mixed environment
initial state, I(t) = |cos(θ_Z−θ_X)| sin²(2tΩ) ≠ 0. **Unitary s-e coupling generically
produces measurement invasiveness** — the intermediate measurement disturbs the statistics even
when it commutes with the pre-measurement state.

**→ This directly supports the K-survival mechanism picture:** the quantum bath's unitary
coupling to data qubits creates irreducible measurement invasiveness that the joint-parity
extraction may or may not "see," depending on the geometric alignment.

### 2. The DNI condition is basis-sensitive
Eq. (38): I(t,τ) = (1/3)(4−e^{−γ(t+τ)}) |sin(θ_Z−θ_Y) sin(θ_Y−θ_X)|. DNI holds ONLY when
θ_Y = θ_X (intermediate measurement aligned with pre-measurement basis). For any other
alignment, I ≠ 0.

**→ This is the formal structure for the coupling-observable commutation dependence:**
K (Kolmogorov violation) = f([coupling operator, measured observable]). When they align,
the measurement is non-invasive (DNI); when they don't, invasiveness survives.

### 3. Discord generation does NOT guarantee DNI violation
Section IV A 2: Superclassical dynamics WITH discord generation is possible [Eq. (40)].
The system dynamics is depolarizing, I(t,τ) = 0, C_pf ≠ 0 — memory without invasiveness,
despite quantum discord in the s-e state.

**→ Important nuance for the K-survival proposition:** K > 0 requires BOTH memory AND
invasiveness. Discord alone is not sufficient; the measurement must be geometrically
misaligned with the coupling to detect it.

### 4. Non-unitary s-e coupling is necessary for DNI
Superclassicality requires non-unitary s-e coupling [Eq. (26) or (31)]. Pure unitary
coupling always violates DNI. The physical bath (pseudomode with σ_z coupling) is unitary
at the microscopic level → DNI should be violated → K should be detectable UNLESS the
measurement geometry twirls it out.

## Relevance to project [ours]
**Dimension 5 (measurement invasiveness selectivity) — FRAMEWORK GROUNDED.** Budini provides the
formal operational definition of when a measurement is invasive (I ≠ 0) and how that depends on
the alignment between the measurement basis and the pre-measurement state. The key mapping to our
K-survival proposition:

| Budini concept | Our setting |
|---|---|
| Single-qubit projective measurement in basis {|m⟩} | Joint-parity extraction via ancilla (CX → Born → reset) |
| DNI condition: △_Y^t commutes with ρ_{t\|X} | K-survival: does the joint-parity measurement commute with the bath-coupled observable? |
| I(t,τ) = 0 ⇔ superclassical (memory without invasiveness) | K(r) ∼ 0 at r=1 (common-mode): the measurement IS aligned → invasiveness twirled out |
| I(t,τ) ≠ 0 for unitary s-e coupling | K(r) > 0 for r ≠ 1: the measurement is MISALIGNED → invasiveness survives |
| Arbitrariness of △_X, △_Z matters | Our single fixed measurement scheme (X_{d0}X_{d1} parity) is only ONE choice of △ |

**The gap Budini does NOT fill:** our joint-parity extraction is a **coarse-grained,
ancilla-mediated, multi-qubit** measurement — not a single-qubit projective measurement.
Extending DNI/K to this setting requires understanding how the ancilla-mediated parity
readout maps to an effective dephasing map △ on the data-qubit subspace, and whether the
commutation condition [coupling operator, measured observable] generalizes naturally.

## Limitations [paper]
- Single qubit only; all examples are two-level systems
- Assumes semigroup property G_{t+τ,0} = G_{t+τ,t} G_{t,0} (time-independent generator between
  measurements). Our quantum bath with pseudomode is time-dependent in the toggling frame.
- No multi-qubit extension; the "arbitrary measurement" condition is defined per-qubit, not
  for joint/collective measurements
- Markovian Lindblad form between measurements (though the REDUCED system dynamics can be
  non-Markovian via γ_t < 0)
- The depolarizing constraint on the system dynamics is a consequence of demanding DNI for
  ALL measurement bases; our fixed measurement scheme may relax this

## Tags
- `[paper]` DNI/Kolmogorov framework for measurement invasiveness in non-Markovian systems
- `[paper]` unitary s-e coupling ⇒ DNI violation (measurement invasiveness is generic)
- `[paper]` superclassicality = memory without invasiveness (requires non-unitary s-e coupling)
- `[ours]` joint-parity extraction maps to an effective △ on data qubits; DNI depends on
  [coupling operator, measured observable] commutation
- `[ours]` the r=1 collapse (K ∼ 178× smaller) = DNI is approximately satisfied
  (common-mode coupling aligned with symmetric parity measurement)
- `[ours]` the r≠1 survival = DNI violated (generic coupling not aligned)
