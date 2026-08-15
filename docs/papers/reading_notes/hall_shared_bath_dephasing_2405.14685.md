# Reading note: Hall et al., "Controlling dephasing of coupled qubits via shared-bath coherence" (arXiv:2405.14685)

> **Provenance (2026-07-05): Read abstract + intro + method.** PDF → txt `outputs/papers/2405.14685.txt`
> (17 pages). Published as Phys. Rev. B 112, 045303 (2025).
> Adjudication target: does this paper provide the **σz (pure dephasing) analogue** of Hatifi's
> distance-controlled dark/bright mode structure? **Verdict: YES — directly, for QD excitons
> coupled to shared acoustic phonon bath. Distance d controls dephasing rates via coherent
> bath interference.**

## Metadata [paper]
- **Authors:** L.M.J. Hall, L.S. Sirkina, A. Morreau, W. Langbein, E.A. Muljarov (Cardiff)
- **Venue / status:** arXiv:2405.14685v2 [cond-mat.mes-hall], Oct 2024 → Phys. Rev. B 112, 045303 (2025)
- **Type:** theory (Trotter decomposition + cumulant expansion for exact pure dephasing solution)

## Executive summary [paper]
Two semiconductor QD qubits at distance d, coupled to a **shared 3D acoustic phonon bath**
via independent boson (IB) model: H_IB = H_ph + d†₁d₁V₁ + d†₂d₂V₂, where Vⱼ = Σ_q λ_{q,j}(b_q + b†_{-q})
is the σz-type coupling (pure dephasing, exciton number-preserving). The matrix elements
satisfy λ_{q,2} = e^{iq·d} λ_{q,1} — the distance enters as a phase factor. Key result:
**dephasing rates show minima at specific distances d** due to coherent interference in the
shared bath. This is the pure-dephasing analogue of Hatifi's geometry-controlled dark/bright
modes. The effect is a **coherent property of the shared bath** — absent for independent baths.

## Key results [paper]

### Distance-dependent dephasing via shared bath
The phase factor e^{iq·d} in the coupling matrix elements means that the effective
coupling of collective qubit modes to the bath depends on d. At certain distances,
the dephasing rate of specific entangled states is minimized or eliminated.

### Mapping to Hatifi (σ⁺σ⁻ → σz)
| Feature | Hatifi (2508.07046) | Hall et al. (2405.14685) |
|---|---|---|
| Coupling type | σ⁺σ⁻ (energy exchange) | σz (pure dephasing) |
| Bath | 1D waveguide (Lorentzian) | 3D acoustic phonons |
| Distance control | cos(k₀d) and sin(k₀d) factors | e^{iq·d} phase factor |
| Dark mode | Symmetric at d=λ₀/4 | Depends on collective state symmetry |
| Mechanism | Interference in emission amplitudes | Interference in dephasing rates |

### DFS for σz collective dephasing (from existing literature)
For H_int = (g₁σz¹ + g₂σz²) ⊗ B:
- r = g₁/g₂ = 1 (common-mode): the {|01⟩, |10⟩} subspace is dark (DFS)
  - |S⟩ = (|01⟩−|10⟩)/√2 has zero coupling
- r = −1 (differential): the {|01⟩, |10⟩} subspace is FULLY bright
  - |01⟩ and |10⟩ acquire opposite phases → maximal dephasing
- r = 0 (single-qubit): intermediate

**This is the σz analogue of Hatifi's result, with the crucial difference that
the dark mode is the ANTISYMMETRIC (under qubit permutation) state for σz,
while it's the SYMMETRIC state for σ⁺σ⁻.**

## Relevance to project [ours]
**Directly grounds the K-survival prediction for r<0:**
1. At r=1: collective σz¹+σz² coupling → {|01⟩,|10⟩} is dark → bath cannot imprint
   memory on this subspace → K collapses (our observed ∼178×)
2. At r<0 (differential): σz¹−σz² coupling → {|01⟩,|10⟩} is maximally bright →
   bath fully imprints quantum memory → K should be **maximally large**, not suppressed
3. At r=0 (single-qubit): intermediate → K moderate

The K(r) prediction is now: **K should be asymmetric around r=1**, with r=1 as a
sharp minimum, r<0 giving maximal K, and r∈(0,1) giving intermediate values.

## Limitations
- Semiconductor QD specific (exciton-phonon coupling); mapping to superconducting
  qubit pseudomode requires adapting the bath model
- The IB model is exactly solvable (pure dephasing, no energy exchange) — the
  dark mode structure is exact, not approximate
- Markovian limit considered for long-time ZPL; non-Markovian short-time BB is
  also treated but less relevant for our steady-state K measurement

## Tags
- `[paper]` σz pure dephasing: distance-controlled dephasing via shared bath coherence
- `[paper]` phase factor λ_{q,2} = e^{iq·d} λ_{q,1} → interference in dephasing rates
- `[paper]` coherent bath effect absent for independent baths
- `[ours]` r=1 ↔ common-mode → {|01⟩,|10⟩} dark (DFS) → K ∼ 0
- `[ours]` r<0 ↔ differential → {|01⟩,|10⟩} maximally bright → K maximal
- `[ours]` K(r) prediction: asymmetric about r=1, sharp minimum at r=1, large at r<0
