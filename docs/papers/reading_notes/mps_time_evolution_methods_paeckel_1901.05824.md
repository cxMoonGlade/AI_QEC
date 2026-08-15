# Full-text review (targeted 精读) — Paeckel, Köhler, Swoboda, Manmana, Schollwöck, Hubig, "Time-evolution methods for matrix-product states" (arXiv:1901.05824, Ann. Phys. 411 (2019) 167998)

> **Provenance (2026-07-01): targeted 精读** of the method-selection + W^II + TDVP sections (the review is
> 82 pp / 7927 lines; `outputs/papers/1901.05824.txt`). Read: §1–3 overview/comparison (l.301–336,
> 1465–1512), §4 MPO W^I/W^II construction (l.2035–2130+, Eq. 68–70), §5/6 Krylov/TDVP intro. This is the
> **method/integrator** reference for the MPS carrier — the mechanism (coupled-pseudomode Lindbladian) is
> already grounded in `[2506.10308]`.

## Why this note exists [ours]
The MPS-carrier prereg (`mps_tdvp_carrier_prereg.md` v0) proposed **superoperator-Trotter (TEBD)**. That is
WRONG for our problem: the shared-bath pseudomode couples to a COLLECTIVE operator ⇒ the vectorized
Lindbladian is **long-range**, and TEBD is a nearest-neighbour method (long-range ⇒ swap gates, awkward).
`[2506.10308 SM §S4]` (primary, re-read): the paper propagates the **vectorized ρ via TDVP** (TD-DMRG,
ITensors.jl), site order by dissipation magnitude, cutoff ε=1e-12, **renorm tr ρ=1 each step**, observables
`⟨⟨I|Oρ⟩⟩` with `|I⟩⟩` = vectorized identity as an MPS. Correct method = TDVP or an equivalent handling
long-range + non-Hermitian.

## The five methods + their scope [paper §2–3]
| Method | Long-range? | Unitary? | Time-step err | Notes |
|---|---|---|---|---|
| **TEBD** (1/2/4) | NN only (swaps for long-range) | yes | larger | our-original-WRONG choice for the shared bath |
| **MPO W^I / W^II** (Zaletel 2015, ref [40]) | **YES, directly; smaller MPOs than TEBD** | **NO (natural for a Lindbladian!)** | larger (O(δ²) for W^II) | builds `Û(δ)` as an MPO from Ĥ's block-triangular MPO |
| **global Krylov** (§5) | via MPO | yes | very small | Krylov vectors highly entangled ⇒ expensive |
| **local Krylov** (§6.1) | arbitrary Ĥ | yes | uncontrolled projection err | "treats arbitrary Ĥ" (unlike TEBD/W^II) |
| **TDVP 1-/2-site** (§6.2, refs [36,37]) | arbitrary Ĥ (the paper's method) | yes | 2TDVP: **NO projection err for NN**; 1TDVP larger but constant bond | needs tangent-space / MovingEnvironment machinery |

**Decisive [paper l.1470–1473, 1492]:** "The MPO W^I,II method … can directly deal with **long-range
interactions** and generally generates **smaller MPOs than TEBD**. Its primary downside is that the evolution
is not exactly unitary." ⇒ for a **Lindbladian (inherently non-unitary)** the W^II "downside" is a NON-issue.

## The chosen method — MPO W^II [paper §4, Eq. 68–70]
`Û^II(δ) = 1 − iδ Σ_j Ĥ_j − (δ²/2) Σ''_{j,k} Ĥ_j Ĥ_k + …` (Eq. 68), the double-primed sum excluding terms
overlapping on **>1 site** (arbitrary powers of single-site terms exact; error O(δ²)). Construction (Eq. 69):
the time-evolution MPO has the SAME block-triangular structure as the Hamiltonian MPO,
`W^II_j = [[W^II_Dj, W^II_Cj],[W^II_Bj, W^II_Aj]]`, blocks built from the Hamiltonian-MPO blocks
`{A_j,B_j,C_j,D_j}` via operator-valued exponentials (Eq. 70):
`Φ_j = exp( ĉ†ā† A_j + √δ(ĉ† B_j + ā† C_j) + δ D_j )`, W^II entries = hard-core-boson transition amplitudes
`⟨0,0̄| ĉ ā Φ_j |0,0̄⟩` etc. (Zaletel formalism). ⇒ **build the Lindbladian as a block-triangular MPO, apply
Eq. 70 per site to get the W^II MPO, apply W^II to the vec-ρ MPS + compress each step.** For a Lindbladian
L̂ (replacing −iĤ): D carries the on-site dissipator superops, B/C the coupling superops; the shared-mode
long-range coupling lives in the MPO's off-diagonal blocks with small bond — W^II handles it exactly.

## Can I OPERATE it? [ours]
YES: (1) vec-ρ as an MPS (sites = qubits + modes, local dim phys²); (2) Lindbladian as a block-triangular
MPO (on-site H_A/dissipator superops in D; qubit–mode coupling superops in B/C — long-range shared-mode
term = off-diagonal MPO block, small bond); (3) W^II MPO via Eq. 70; (4) apply + compress (χ-truncation) +
renorm tr ρ=1 (`⟨⟨I|ρ⟩⟩`); reduced ρ_S via `⟨⟨I_modes|`. **Implementation (don't reinvent):** TeNPy has
`ExpMPOEvolution` (W^I/W^II) **and** `TDVPEngine` built-in + tested — NOT installed here (cf. cvxpy).
quimb (installed, used by `mps_forward.py`) has MPO-apply + compress but NOT W^II/TDVP ⇒ either install
TeNPy (numpy dep) or implement the W^II block construction on quimb. **Prereg DECISION:** method = **W^II
MPO** (grounded here), via TeNPy (preferred, tested) or a quimb W^II build; NOT TEBD/hand-Trotter.

## Limitations / caveats [paper + ours]
- W^II time-step error O(δ²), larger than Krylov/TDVP ⇒ smaller δ + a convergence check (prereg C4).
- Non-unitarity is fine for a Lindbladian but **renorm tr ρ=1 each step REQUIRED** (matches `[2506.10308 SM
  §S4]` + our fp32 renorm-guard decision).
- 2TDVP has no projection error for NN, but our coupling is long-range ⇒ 2TDVP would still project; W^II
  avoids the projection-error issue entirely (MPO-application, not tangent projection).
- The FEASIBILITY question (bond χ bounded for the pseudomode-enlarged dephasing) is orthogonal to the
  integrator — the prereg §3b bet, decided empirically.

## Provenance line
Downloaded 2026-07-01 (arXiv:1901.05824 → PyMuPDF txt, 82 pp). Targeted 精读 of method-selection + W^II
(§4) + TDVP (§6.2). Ann. Phys. 411 (2019) 167998. The MPS-time-evolution methods reference.
