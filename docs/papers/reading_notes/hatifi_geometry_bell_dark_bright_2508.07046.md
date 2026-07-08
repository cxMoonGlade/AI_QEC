# Reading note (精读): Hatifi, "Geometry-Controlled Freezing and Revival of Bell Nonlocality through Environmental Memory" (arXiv:2508.07046)

> **Provenance (2026-07-05): FULL-TEXT read (精读).** PDF → txt `outputs/papers/2508.07046.txt`
> (10 pages, PyMuPDF). All §/Eq refs from that text.
> Adjudication target: does this paper ground the claim that dark/bright mode structure
> (common-mode vs differential coupling) controls what quantum correlations survive
> environmental coupling? **Verdict: YES — directly, with analytic closed-form results
> for two qubits in a structured bath.**

## Metadata [paper]
- **Author:** Mohamed Hatifi (Institut Fresnel, Marseille)
- **Venue / status:** arXiv:2508.07046v2 [quant-ph], 11 Jan 2026. Preprint.
- **Type:** theory + numerics (exact analytic solution in single-excitation sector + continuum limit)

## Executive summary [paper]
Two qubits separated by distance d, coupled to a structured bosonic reservoir (Lorentzian
spectral density with linewidth λ). The **distance d acts as a single geometric control** that
determines which collective mode (symmetric |S⟩ or antisymmetric |A⟩) is bright (coupled to
bath) vs dark (decoupled = DFS). Key results:
1. At d = λ₀/4: symmetric state is dark (DFS), antisymmetric is bright
2. At d = nλ₀/2: antisymmetric is dark, symmetric is bright
3. Subwavelength displacements from DFS node → quadratic change in dark/bright decay rates
4. Bell nonlocality (CHSH) can be **stored, revived, or quenched** purely by geometry
5. Non-Markovian backflow regions map directly to Bell revival regions

## Key equations (exact) [paper]

### System-bath coupling in collective basis — Eq. (3)
```
H_SB = Σ_k √(2)g_k [cos(k₀d) σ⁺_S + i sin(k₀d) σ⁺_A] b_k + H.c.
```
where σ⁺_S = (σ⁺_1 + σ⁺_2)/√2, σ⁺_A = (σ⁺_1 − σ⁺_2)/√2. The coupling amplitudes are
**g_S ∝ cos(k₀d)** and **g_A ∝ sin(k₀d)**. At k₀d = π/2 (d = λ₀/4): cos = 0, sin = 1 →
|S⟩ is dark, |A⟩ is bright. This is the **exact common-mode (symmetric) vs differential-mode
(antisymmetric)** structure.

### Lorentzian spectral density — Eq. (4)
J_L(ω) = γλ²/[(ω−ω₀)² + λ²]. Memory time τ_M ∼ 1/λ. Non-Markovian when τ_M ∼ 1/γ.

### Dark-state lifetime scaling — Eq. (10)
T_df ∝ (δd)^{−2} for |k₀δd| ≪ 1, where δd is displacement from the DFS node. Quadratic
sensitivity → subwavelength displacements dramatically change protection.

### BLP-analogue for Bell — integrated backflow
N_B = ∫_{Ḃ>0} Ḃ(t) dt where B(t) is the CHSH parameter. Peaks at Poincaré times t = nT_P
where T_P = 2L/v (round-trip time in mirror-terminated guide).

## Key findings for K-survival proposition [paper → ours]

### 1. Geometry controls coupling symmetry
The factor cos(k₀d) vs sin(k₀d) is the **physical realization of our r = g₁/g₀ knob**.
When d = λ₀/4 (our r=1 common-mode), the symmetric combination |S⟩ = (|eg⟩+|ge⟩)/√2 is
completely dark — it does not couple to the bath at all. This is the mechanism behind
r=1 "twirling out": the joint-parity measurement probes the symmetric mode, which at
r=1 is the dark mode → the bath's quantum memory is invisible.

### 2. Dark/bright = common/differential
|S⟩ is the common-mode excitation (both qubits excited in phase), |A⟩ is the differential
mode (out of phase). The mapping to our setting: the X_{d0}X_{d1} parity measurement
couples to the symmetric data-qubit observable → when r=1 (symmetric coupling to bath),
the measurement is aligned with the dark mode → K collapses. When r≠1, the coupling
has an antisymmetric component → the measurement "sees" the bright mode → K survives.

### 3. Quadratic sensitivity near DFS node
T_df ∝ (δd)^{−2} near the DFS node means that even SMALL deviations from r=1 produce
measurable changes in the dark-state lifetime → the K collapse at r=1 should be sharp
(factor ~178×), with a quadratic recovery as r moves away from 1. This is consistent
with the observed r=0.5 giving K ∼ 1.16–1.33× r=0 baseline.

### 4. Non-Markovianity = Bell revival
The paper shows that regions of (d, λ) with information backflow (BLP N > 0) exactly
overlap with regions of Bell revival. This connects directly: our K (Kolmogorov
violation) is the operational multi-time analogue of Bell violation; the same geometric
control that revives Bell nonlocality should revive K.

## Relevance to project [ours]
**Dimensions 3 & mechanism grounding — DIRECTLY SUPPORTS the common-mode collapse mechanism.**
The dark/bright mode structure at the single-excitation level provides the cleanest
physical picture of why K collapses at r=1: the joint-parity measurement couples to the
symmetric (common-mode) data observable, which at r=1 is the dark mode of the system-bath
coupling. The bath cannot imprint quantum memory on a mode it doesn't couple to.

The key mapping:
| Hatifi concept | Our K-survival setting |
|---|---|
| Two qubits, distance d | Two data qubits, coupling ratio r = g₁/g₀ |
| cos(k₀d) = 0 → dark |S⟩ | r=1 → joint-parity measurement aligned with dark mode |
| sin(k₀d) = 1 → bright |A⟩ | r≠1 → antisymmetric component couples to bath |
| DFS node at d = λ₀/4 | K-minimum at r=1 |
| T_df ∝ (δd)^{−2} near node | K(r) should show quadratic recovery near r=1 |

## Limitations [paper]
- Single-excitation sector only (weak-driving limit)
- Rotating-wave approximation (no counter-rotating terms → pure σ⁺σ⁻ coupling, not σ_z
  coupling like our pseudomode)
- The model is energy-exchange (T₁-type), not pure dephasing (T_ϕ-type). Our pseudomode
  has σ_z coupling (pure dephasing) — the dark/bright structure generalizes but the
  mapping is not one-to-one
- Discrete bath with mirror boundary condition — our quantum bath is a single pseudomode
  (nontrivial generalization needed)

## Tags
- `[paper]` geometric control of dark/bright modes = distance d → coupling symmetry
- `[paper]` DFS node at d = λ₀/4: symmetric mode dark, antisymmetric bright
- `[paper]` quadratic sensitivity near DFS node: T_df ∝ (δd)^{−2}
- `[paper]` Bell revival ↔ non-Markovian backflow (same (d,λ) regions)
- `[ours]` r=1 ↔ d=λ₀/4: joint-parity measurement aligned with dark mode → K collapses
- `[ours]` r≠1 ↔ d≠λ₀/4: measurement sees bright mode → K survives
- `[ours]` the K(r) shape near r=1 should be quadratic (from DFS-node sensitivity scaling)
