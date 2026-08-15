# Reading note (精读): Sakuldee, Taranto & Milz, "Connecting Commutativity and Classicality for Multi-Time Quantum Processes" (arXiv:2204.11698)

> **Provenance (2026-07-05): FULL-TEXT read (精读).** PDF → txt `outputs/papers/2204.11698.txt`
> (16 pages, Phys. Rev. A 106, 022416 (2022)). All §/Eq refs from that text.
> Adjudication target: does the multi-time Kolmogorov consistency condition reduce to a
> simple commutation relation that can guide our [coupling operator, measured observable]
> geometry analysis? **Verdict: NO — the multi-time condition is structurally richer than
> simple commutation, but the paper provides the formal tools to analyze it.**

## Metadata [paper]
- **Authors:** Fattah Sakuldee (Gdańsk), Philip Taranto (Vienna), Simon Milz (Vienna)
- **Venue / status:** Phys. Rev. A 106, 022416 (2022); arXiv:2204.11698
- **Type:** theory (formal analysis of commutativity ↔ classicality in process tensor framework)

## Executive summary [paper]
Extends Lüders' theorem (two-time classicality ⇔ commutativity of measured observables)
to the multi-time setting using the process tensor / quantum comb formalism. The key finding:
**in the multi-time case, Kolmogorov consistency does NOT simply reduce to operator
commutation.** Novel "absolute commutator" expressions are needed. The paper identifies the
relevant operators (process tensor objects like ρ̃₂(m₁), Q₂(m₃), and instrument elements
K₂^{(m₂)}) and shows that even for Markovian dynamics with projective measurements, no
simple commutation relation between these operators is guaranteed.

## Key results [paper]

### Two-time case (Lüders theorem generalization)
For a two-time process with instruments J₁, J₂, the joint probabilities are
Kolmogorov-consistent (classical) iff:
```
[J₁(·), J₂(·)] = 0   (commutation of instrument elements)
```
This is the familiar result: measuring A then B = measuring B then A if [A, B] = 0.

### Multi-time case — the "absolute commutator"
For n > 2 measurements, the condition becomes much richer. The process tensor T_{n:0}
introduces temporal correlations that make the classicality condition depend on:
1. The process tensor elements ρ̃_k (conditional states)
2. The instrument elements K_j^{(mⱼ)}
3. An "absolute commutator" expression involving these objects

The key structural insight: **temporal correlations in the process tensor can make
two commuting observables produce non-classical (Kolmogorov-inconsistent) statistics**
if the intermediate process tensor state has off-diagonal elements in the joint
eigenbasis.

### Classicality condition in process-tensor form
For process tensor T and instruments {J_k}, the joint probability distribution is
classical (Kolmogorov-consistent) iff certain marginalization conditions hold. These
reduce to commutation conditions on the Choi-state representation of the process
tensor, not on the observables alone.

## Relevance to project [ours]
**Dimension 5 (measurement invasiveness selectivity) — FORMAL STRUCTURE CLARIFIED.**
This paper tells us that the simple intuition "[coupling operator, measured observable] = 0
⇒ K = 0" is **too simple for the multi-time setting.** The joint-parity extraction produces
a multi-time record (multiple rounds), and the Kolmogorov consistency of that record depends
on the full process tensor structure, not just two-time commutativity.

Specifically for our K-survival proposition:
1. **The r=1 (common-mode) collapse IS a commutation effect at the single-round level:**
   when g₁ = g₂, the bath coupling operator Σ_j g_j σ_z^j ∝ (σ_z¹ + σ_z²) commutes with
   the measured X_{d0}X_{d1} parity (they act on different Pauli axes). But...
2. **Multi-round records introduce temporal correlations** that this paper shows can
   generate K > 0 even when single-round commutativity holds — the process tensor
   structure matters.
3. This means the r=1 collapse to K ∼ 0 is a **single-round effect** that may not
   survive to multi-round records — an important nuance for our experimental design.

## Limitations [paper]
- Formal mathematical analysis; no physical model instantiated
- No open-system dynamics (the process tensor is treated abstractly)
- No specific instrument model for stabilizer measurements or ancilla-mediated readout

## Tags
- `[paper]` multi-time classicality ≠ simple commutativity (richer structure)
- `[paper]` process tensor + instrument elements determine classicality
- `[paper]` temporal correlations can make commuting observables non-classical
- `[ours]` r=1 collapse may be single-round effect; multi-round records may revive K
- `[ours]` the full process tensor of joint-parity records is the right object
