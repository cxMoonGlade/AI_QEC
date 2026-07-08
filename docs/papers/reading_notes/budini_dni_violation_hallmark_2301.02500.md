# Reading note (精读): Budini, "Violation of Diagonal Non-Invasiveness: A Hallmark of Non-Classical Memory Effects" (arXiv:2301.02500)

> **Provenance (2026-07-05): FULL-TEXT read (精读).** PDF → txt `outputs/papers/2301.02500.txt`
> (13 pages). All §/Eq refs from that text. This is the PREDECESSOR to Budini 2411.13471
> (Superclassical) — it introduces the DNI concept; the later paper characterizes the
> dynamics that SATISFY it.
> Adjudication target: does this paper provide the operational measurement scheme that
> we should use to define K on joint-parity records? **Verdict: YES — the three-measurement
> DNI protocol is the direct operational definition, and it's implementable.**

## Metadata [paper]
- **Author:** Adrián A. Budini (CONICET / UTN-FRC, Bariloche, Argentina)
- **Venue / status:** arXiv:2301.02500v4 [quant-ph], 9 Mar 2025 → Phys. Rev. A (published)
- **Type:** theory (operational definition + examples)

## Executive summary [paper]
Establishes the **Diagonal Non-Invasiveness (DNI)** operational scheme: three consecutive
projective measurements. The first and last are arbitrary; the intermediate one is performed
in the basis where the pre-measurement state is diagonal (i.e., commutes with it). In
Markovian dynamics, DNI always holds — the intermediate measurement is non-invasive. In
non-Markovian dynamics, violation of DNI = non-classical memory. The key finding:
**unitary system-environment coupling generically violates DNI**; non-unitary (Lindblad)
s-e coupling can satisfy DNI (superclassical). The quantifier I(t,τ) [Eq. (9)] directly
measures DNI violation and IS the operational definition of K (Kolmogorov violation).

## Key equations [paper]

### DNI violation measure — Eq. (9)
```
I(t,τ) = Σ_{zx} |P_3(z,x) − P_2(z,x)|
```
Where P_3(z,x) = Σ_y P_3(z,y,x) (marginal with intermediate measurement), P_2(z,x)
(joint without intermediate measurement). I = 0 ⇔ DNI holds. This is the direct
operational K analogue — the absolute distance between measurement-perturbed and
unperturbed distributions.

### CPF correlation — Eq. (11)
```
C_pf(t,τ) = Σ_{zx} zx [P_3(z,x|y) − P_3(z|y)P_2(x|y)]
```
C_pf ≠ 0 ⇔ non-Markovian (memory). I ≠ 0 AND C_pf ≠ 0 ⇔ non-classical memory.

### Unitary s-e coupling ⇒ DNI violation
For Hamiltonian H_se = (Ω/2) Σ_k σ_k ⊗ σ_k with maximally mixed environment:
I(t) = |cos(θ_Z−θ_X)| sin²(2tΩ). **Unitary coupling always violates DNI** for generic
measurement angles. Non-unitary (dissipative) coupling is required for DNI.

### Superclassical = memory without invasiveness
Non-Markovian dynamics with C_pf ≠ 0 but I = 0. Requires depolarizing s-e coupling
structure. **This is the condition our r=1 configuration approximately satisfies.**

## Relevance to project [ours]
**Dimension 5 (measurement invasiveness selectivity) — OPERATIONAL PROTOCOL DEFINED.**
This paper gives us the concrete measurement protocol for computing K on joint-parity
records:

1. **Three "measurements" in our setting:**
   - X-measurement (t=0): initial state preparation
   - Y-measurement (t): intermediate joint-parity extraction round (ancilla-mediated)
   - Z-measurement (t+τ): final joint-parity extraction round
   
2. **I(t,τ) = Σ |P_3(z,x) − P_2(z,x)|** — compute from Monte Carlo trajectories with and
   without the intermediate extraction round. This IS our K observable.

3. **The DNI condition for r=1:** at r=1, the coupling operator ∝ (σ_z¹ + σ_z²) is
   symmetric; the joint-parity measurement probes the symmetric X_{d0}X_{d1} observable.
   These commute (different Pauli axes), so the intermediate measurement should leave the
   pre-measurement state approximately invariant → DNI approximately satisfied → I ≈ 0.

4. **DNI violation for r≠1:** the coupling operator has an antisymmetric component;
   the intermediate measurement does NOT commute with the full system-bath coupling →
   DNI violated → I > 0.

## Limitations
- Single-qubit projective measurements; extension to ancilla-mediated parity readout
  requires mapping the parity extraction to an effective instrument on the data qubits
- The intermediate measurement must be in the pre-measurement eigenbasis — our
  joint-parity measurement is in a FIXED basis (X_{d0}X_{d1}), not adaptive
- No multi-round extension (only 3-time protocol)

## Tags
- `[paper]` DNI = operational definition of classicality for non-Markovian processes
- `[paper]` I(t,τ) [Eq. (9)] = direct K analogue (Kolmogorov violation measure)
- `[paper]` unitary s-e coupling ⇒ DNI violation (generic)
- `[paper]` C_pf ≠ 0 + I = 0 ⇒ superclassical (memory without invasiveness)
- `[ours]` this IS the protocol for computing K on joint-parity records
- `[ours]` r=1 ≈ superclassical (I ∼ 0 despite C_pf ≠ 0); r≠1 = DNI-violating
