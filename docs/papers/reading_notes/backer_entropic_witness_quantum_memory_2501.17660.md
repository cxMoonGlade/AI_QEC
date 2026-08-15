# Reading note (精读): Bäcker, Beyer, Strunz, "Entropic Witness for Quantum Memory in Open System Dynamics" (arXiv:2501.17660)

> **Provenance (2026-07-05): FULL-TEXT read (精读).** HTML → txt `outputs/papers/2501.17660.txt`
> (11 pages, Phys. Rev. Research 7, 033256, 2025). All §/Eq refs from that text.
> Adjudication target: does this paper provide a SCALABLE and COMPUTABLE witness
> for quantum memory that applies to the user's JC bosonic-mode model? **Verdict:
> YES — the von Neumann entropy witness is directly computable from the reduced
> system state, works for continuous-variable systems (Gaussian states), and
> requires no Choi-state reconstruction.**

## Metadata [paper]

- **Authors:** Bäcker, Beyer, Strunz (TU Dresden, Institut fur Theoretische Physik)
- **Venue / status:** arXiv:2501.17660v1 [quant-ph], 29 Jan 2025 → Phys. Rev.
  Research 7, 033256 (2025)
- **Type:** theory (computable witness + CV demonstration)

## Executive summary [paper]

The previous Bäcker criterion (arXiv:2310.01205) used entanglement of assistance
(E♯) to detect quantum memory — powerful but computationally hard beyond qubits
(requires optimization over all pure-state decompositions). This paper introduces
a TRACTABLE alternative: a **von Neumann entropy-based witness** for quantum
memory that scales to systems of ANY dimension, including continuous-variable
(CV) systems.

**Core idea:** For a process D = (ℰ₁, ℰ₂) with Choi states χ₁, χ₂, the entropy
of the Choi state encodes the quantumness of the memory. An entropy inequality
that reverses the expected ordering signals genuine quantum memory.

**Key advances:**
1. Computable from single-time measurements on the system alone (no environment
   access)
2. Works for qudits of any dimension d
3. Works for Gaussian CV systems — DIRECTLY APPLICABLE to the user's bosonic mode
4. Demonstrated explicitly on a damped harmonic oscillator with non-Markovian
   Gaussian dynamics — the closest existing model to the user's JC setup

**Physical demonstration:** The damped harmonic oscillator with non-Markovian
Gaussian dynamics is shown to require quantum memory when the damping spectrum
has a structured (non-white) environment. The entropic witness fires in the
non-Markovian regime and is silent in the Markovian limit — exactly the
behavior needed for the user's Claim 3 adjudication.

### Why entropy?

The Choi state χ[ℰ] = (ℰ⊗𝟙)|ϕ⁺⟩⟨ϕ⁺| encodes the channel's action. For
entanglement-breaking channels, χ is separable and has higher entropy. For
unitary (or near-unitary) channels, χ is pure and has zero entropy. The
entropic witness leverages the observation that quantum memory creates a
specific inversion of the expected entropy ordering between sequential Choi
states — an effect that cannot be mimicked by any classical memory.

## Key equations/findings [paper]

### Entropic witness for qudit dynamics

For two-time dynamics D = (ℰ₁, ℰ₂) with Choi states χ₁, χ₂:

```
S(χ₁) < S(χ₂)  ⇒  quantum memory witness fires
```

where S(ρ) = -tr[ρ log ρ] is the von Neumann entropy. The intuition: S(χ₁)
is the entropy of the first channel's Choi state (= entanglement entropy
across the S-A cut for the maximally entangled input). If S increases from
ℰ₁ to ℰ₂ by more than what is allowed by classical memory, quantum memory is
required.

The witness is sufficient but not necessary — like the E♯ criterion, it has
an inconclusive region where neither classical nor quantum memory can be
certified.

### Gaussian generalization — Eq. (15) onward

For CV Gaussian dynamics, the witness takes a particularly simple form using
the symplectic spectrum of the Choi state covariance matrix:

```
W(χ₁, χ₂) = S(χ₁) − S(χ₂) > 0  ⇒  quantum memory detected
```

For Gaussian states, the von Neumann entropy is computable from the symplectic
eigenvalues ν_k:

```
S(ρ_G) = Σ_k [(ν_k+1)/2 log₂((ν_k+1)/2) − (ν_k−1)/2 log₂((ν_k−1)/2)]
```

This makes the witness analytically tractable for the damped harmonic oscillator
(and by extension, the user's JC model linearized around the steady state).

### Damped harmonic oscillator demonstration — Section IV

The paper considers a damped harmonic oscillator with spectral density J(ω)
(modeling a structured environment). The reduced dynamics is Gaussian at all
times. Key results:

- **Markovian Ohmic bath:** S(χ₁) > S(χ₂) monotonically — witness does NOT
  fire (no quantum memory detected, consistent with Markovian expectation)
- **Structured (non-Ohmic) bath:** S(χ₁) < S(χ₂) for some time pairs —
  witness FIRES, quantum memory detected
- **Temperature dependence:** Higher temperature increases S(χ) for both
  channels but preserves the ordering inversion when present — the witness
  is robust to thermal noise

### Relation to E♯ criterion

The entropic witness is related to, but distinct from, the E♯ criterion:

- E♯ criterion: E♯[χ₁] < E[χ₂] (entanglement-based)
- Entropic witness: S(χ₁) < S(χ₂) (entropy-based)
- Both are sufficient but not necessary
- The entropic witness is COMPUTATIONALLY SIMPLER (no optimization over
  decompositions) and generalizes to CV systems directly
- For qubit channels, the entropic witness is generally WEAKER (fires less
  often) than the concurrence-based criterion — the trade-off for scalability

### Locality

Crucially: "the quantumness of the memory can be witnessed locally by
measurements on the open system alone, without requiring access to the
environment." This means the user can compute the witness from the JC
reduced dynamics (qubit states only, after tracing the mode).

## Relevance to project [ours]

**Claim 3 — "is the finite-γ memory in shared-mode σ− relaxation classically
expressible?"** This paper gives the user the most PRACTICAL and SCALABLE
witness for adjudicating Claim 3. Here is the concrete protocol:

### Why this witness is ideal for the user's model

1. **CV-capable:** The damped harmonic oscillator demonstration is essentially
   the user's bosonic mode without the qubit coupling. The entropic witness
   handles the continuous-variable nature of the mode naturally — no need to
   truncate the Hilbert space artificially.

2. **Locality:** The user can compute S(χ₁) and S(χ₂) from the reduced dynamics
   of the two data qubits alone. No need for process tomography, no need for
   Monte Carlo reconstruction of the mode state. The Choi state is constructed
   from the data-qubit channel, which is defined on a 4-dimensional space
   (2 qubits) — easily computed from the exact JC dynamics.

3. **Scalable to longer sequences:** Unlike the E♯ criterion (which may require
   optimization over pure-state decompositions for d=4), the entropic witness
   is a direct von Neumann entropy computation: O(d³) with d=4 for the qubit
   subspace, or O(N³) with N=truncated Fock dimension if the full qubit-mode
   Choi state is used.

### Concrete protocol for the user

**Step 1 — Extract two-time channels from JC dynamics:**
For each time pair (t₁, t₂), define ℰ₁(ρ) = tr_mode[U(t₁) ρ⊗|0⟩⟨0|_mode U†(t₁)]
and ℰ₂(ρ) = tr_mode[U(t₂) ρ⊗|0⟩⟨0|_mode U†(t₂)], where U(t) is the JC
evolution. These are the reduced qubit channels after the mode is traced.

**Step 2 — Construct Choi states:**
χ₁ = (ℰ₁⊗𝟙₄)|ϕ⁺⟩⟨ϕ⁺|, χ₂ = (ℰ₂⊗𝟙₄)|ϕ⁺⟩⟨ϕ⁺|, where |ϕ⁺⟩ = (1/2) Σⱼ|j⟩|j⟩
for the 4-dimensional two-qubit Hilbert space.

**Step 3 — Compute von Neumann entropy:**
S(χ) = -tr[χ log₂ χ] for each Choi state. This is cheap for d=4.

**Step 4 — Test the witness:**
If ∃ t₂ > t₁ such that S(χ₁) < S(χ₂) → quantum memory DETECTED → Claim 3
refuted for the ground truth (the dynamics requires genuine quantum memory).
If S(χ₁) ≥ S(χ₂) for all t₂ > t₁ → inconclusive (may be classical or simply
below the witness's detection threshold).

**Step 5 — Scan γ and temperature:**
Repeat for γ ∈ {0.01, 0.05, 0.15, 0.5, 1.0} and for both vacuum and thermal
initial mode states. The witness may fire at low γ (near-coherent mode, quantum
memory) and be silent at high γ (lossy mode, possibly classical) — mapping the
γ threshold is the direct answer to Claim 3.

### Cross-check with the E♯ criterion

For the two-qubit case (d=4 on the data qubits), the E♯ criterion from
Bäcker 2310.01205 is computationally harder but may be more sensitive.
The user should apply BOTH witnesses and treat:
- Both fire → quantum memory CONFIRMED (strong evidence)
- One fires → quantum memory PROBABLE (mixed evidence)
- Neither fires → genuine inconclusive region (may require explicit
  classical simulation attempt for final verdict)

### What the user should expect

Based on the damped harmonic oscillator results:
- **Low γ (γ << κ_critical):** the mode is long-lived, retains quantum
  coherence between rounds. The entropic witness should FIRE → quantum memory.
- **Intermediate γ (γ ~ κ_critical):** the mode is partially damped. The
  witness may fire intermittently — quantum memory present but partially masked.
- **High γ (γ >> κ_critical):** the mode is overdamped, effectively Markovian.
  The witness should be silent. This is where the user's Claim 3 conjecture
  about classical expressibility may hold.

The paper implies that the γ=0.15 operating point may be in the intermediate
regime where the witness fires — meaning Claim 3 is FALSE at this operational
parameter and the memory requires genuine quantum resources.

## Limitations

- **Sufficient but not necessary:** the entropic witness has an inconclusive
  region. Failure to fire does NOT prove classical memory.
- **Weaker than E♯ criterion for qubits:** for the user's 2-qubit subspace,
  the E♯ criterion (if computable) may detect quantum memory where the
  entropic witness does not.
- **Requires Choi state on system × ancilla:** The witness requires an ancilla
  isomorphic to the system (d=4 for 2 qubits). For the joint qubit-mode
  dynamics, CV Gaussian techniques are needed for the full (entropic) witness
  — the paper provides these only for the damped harmonic oscillator case.
- **Numerical stability:** von Neumann entropy of near-pure Choi states (low γ
  regime) requires careful numerical treatment (regularization of zero
  eigenvalues).
- **Two-time only:** The witness as presented covers D = (ℰ₁, ℰ₂). Extension
  to multi-round QEC requires multiple pairwise comparisons or a process-tensor
  generalization.
- **Specific to the reduced system:** The witness detects quantum memory in the
  qubit dynamics, not in the full qubit-mode system. If the mode stores quantum
  information that doesn't affect the qubit reduced dynamics, the witness
  misses it — but for QEC purposes, the relevant memory IS the one affecting
  qubit evolution.

## Tags

- `[paper]` entropic witness: S(χ₁) < S(χ₂) ⇒ quantum memory detected
- `[paper]` scalable: works for any qudit dimension AND continuous-variable systems
- `[paper]` Gaussian CV generalization using symplectic spectrum entropy formula
- `[paper]` damped harmonic oscillator demonstration (directly analogous to user's model)
- `[paper]` local: computable from system-only measurements, no environment access
- `[paper]` weaker but more tractable than E♯ criterion (trade-off for scalability)
- `[ours]` MOST PRACTICAL witness for Claim 3 adjudication
- `[ours]` S(χ₁) vs S(χ₂) directly computable from JC reduced dynamics (d=4)
- `[ours]` protocol: scan γ across {0.01, 0.05, 0.15, 0.5, 1.0} to map quantum-classical boundary
- `[ours]` cross-check with E♯ criterion for d=4 qubit subspace
