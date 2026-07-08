# Reading note: Lonigro & Chruściński, "On the classicality of quantum dephasing processes" (arXiv:2211.02014, 2022)

> **Provenance (2026-07-05): FULL-TEXT read (精读), §§1-2 + key theorems.** PDF → txt
> `outputs/papers/2211.02014.txt` (21 pages). Published in Frontiers in Quantum Science and Technology.
> Adjudication target: does this paper already solve the K-survival question for two-qubit
> collective dephasing? **Verdict: NO — it provides the exact SINGLE-QUBIT framework we need
> to generalize, and explicitly does NOT treat multi-qubit systems. This is the closest prior
> art and confirms our vacuum.**

## Metadata [paper]
- **Authors:** Davide Lonigro (Bari + INFN), Dariusz Chruściński (Toruń)
- **Venue / status:** arXiv:2211.02014v2 [quant-ph], Nov 2022. Frontiers in Quantum Science and Technology.
- **Type:** theory (mathematical analysis of Kolmogorov consistency for dephasing processes)
- **Follow-up by same group:** Lonigro, Sakuldee, Cywiński, Chruściński, Szańkowski, "Double or nothing:
  a Kolmogorov extension theorem for multitime (bi)probabilities" (Quantum 8, 1447, 2024)

## Executive summary [paper]
Analyzes the multitime statistics of **single-qubit pure dephasing** systems repeatedly probed
with sharp projective measurements, asking: for which (initial state, measurement basis, dephasing
model) combinations are the statistics Kolmogorov-consistent (classical)? Key results:
- **Markovian dephasing:** classicality at every order when measurement basis is either fully
  compatible with **or** fully incompatible with (MUBs to) the dephasing basis
- **Non-Markovian dephasing:** classicality only in the fully compatible case
- The dephasing matrix elements Tr[U^{j,ℓ}_{t,s}(ϱ_B)] = e^{-(iε_{jℓ}+γ_{jℓ}/2)(t-s)} control
  everything; factorization ⇒ Markovian; non-factorization ⇒ non-Markovian
- Defines N-classicality hierarchy: process is N-classical if KC holds up to order N

## Key formalism [paper]

### Dephasing Hamiltonian — Eq. (9)
H = Σ_j E_j ⊗ H_j, where {E_j} is a PVM on the system (the dephasing basis) and {H_j}
are bath Hamiltonians. The reduced dynamics:
Λ_{t,t₀}(ρ) = Σ_{j,ℓ} Tr[U^{j,ℓ}_{t,t₀}(ϱ_B)] E_j ρ E_ℓ

### Multitime statistics — Eq. (13)
For projective measurements in PVM {P_x}:
P_n(x_n,...,x_1) = Σ_{j_n,ℓ_n}...Σ_{j₁,ℓ₁} Tr[P_{x_n}E_{j_n,ℓ_n}...P_{x₁}E_{j₁,ℓ₁}(ρ)]
                    × Tr[U^{j_n,ℓ_n}_{t_n,t_{n-1}}...U^{j₁,ℓ₁}_{t₁,t₀}(ϱ_B)]

Factorizes into "system preparation-measurement" × "environment dephasing tensor."

### Markovianity condition — Eq. (14)
Regression formula holds iff the dephasing tensor factorizes:
Tr[U^{j_n,ℓ_n}...U^{j₁,ℓ₁}(ϱ_B)] = Π_k Tr[U^{j_k,ℓ_k}_{t_k,t_{k-1}}(ϱ_B)]

### Key classicality result (see Sections 3-4)
- Markovian + measurement basis = dephasing basis (compatible) → classical
- Markovian + measurement basis = MUB to dephasing basis → classical (!)
- Non-Markovian → only compatible case works

## Relevance to project [ours]
**This is the closest prior art and the explicit template for our generalization.**

The paper solves the single-qubit case completely. Our K-survival proposition asks the
**two-qubit collective dephasing** generalization — i.e., what happens when:
- H = Σ_{j,k} E_j ⊗ E_k ⊗ H_{jk} (two-qubit dephasing Hamiltonian)
- The measurement is joint-parity (a specific two-qubit PVM, not a product of single-qubit PVMs)
- The dephasing has a symmetry parameter r = g₁/g₀ controlling the common vs differential mix

Key mapping:
| Lonigro & Chruściński (single-qubit) | Our two-qubit generalization |
|---|---|
| Dephasing basis = {E_j} | Joint dephasing basis = {E_j ⊗ E_k} |
| Measurement PVM = {P_x} | Joint-parity PVM = {X_{d0}X_{d1} eigenstates} |
| MUB condition: P_x and E_j are MUBs | Does joint-parity act as MUB for the two-qubit dephasing basis? |
| Classicality when compatible OR MUB | **r=1: joint-parity IS compatible with common-mode dephasing → classical** |
| | **r≠1: joint-parity is NOT compatible → quantum** |

The explicit generalization to two qubits is NOT done in this paper. The 2024 follow-up
"Double or nothing" extends the mathematical foundation (Kolmogorov extension for
biprobabilities) but still does not treat the two-qubit collective case.

## The vacuum is CONFIRMED
No paper bridges the Lonigro-Chruściński single-qubit dephasing classicality framework
to two-qubit collective/differential dephasing with joint-parity measurements. This is
the EXACT gap our K-survival proposition fills.

## Limitations [paper]
- Single-qubit only (the dephasing basis {E_j} is on one qubit)
- The "MUB ⇒ classical" result assumes Markovian dephasing; our quantum bath is
  non-Markovian (pseudomode has memory)
- No measurement model for ancilla-mediated parity extraction
- No continuous parameter r for the common/differential mixing

## Tags
- `[paper]` single-qubit dephasing classicality: Kolmogorov consistency framework
- `[paper]` MUB condition: classicality when measurement basis ⊥ dephasing basis (Markovian)
- `[paper]` dephasing tensor factorization = Markovianity condition
- `[ours]` two-qubit generalization of this framework IS the K-survival proposition
- `[ours]` r=1: joint-parity compatible with common-mode dephasing → classical
- `[ours]` the dephasing TENSOR (not matrix) for two qubits encodes r
- `[gap]` NO paper extends this to two-qubit collective/differential dephasing
