# Reading note (精读): Giarmatzi & Costa, "Witnessing quantum memory in non-Markovian processes" (arXiv:1811.03722)

> **Provenance (2026-07-05): FULL-TEXT read (精读).** PDF → txt `outputs/papers/1811.03722.txt`
> (17 pages + appendices). All §/Eq refs from that text. Published in Quantum 5, 440 (2021).
> Adjudication target: does this paper provide the operational test to distinguish classical
> memory from quantum memory in a non-Markovian process? **Verdict: YES — the process-matrix
> entanglement witness is precisely the tool needed for the Claim 3 quantum-vs-classical
> collectiveness adjudication.**

## Metadata [paper]
- **Authors:** Christina Giarmatzi & Fabio Costa (University of Queensland / Perimeter Institute)
- **Venue / status:** arXiv:1811.03722 [quant-ph], 5 Nov 2018 → Quantum 5, 440 (2021)
- **Type:** theory (witness framework + demonstrative examples)

## Executive summary [paper]
Establishes that **non-Markovian processes can carry either classical or quantum memory**,
and provides an operational witness to distinguish them via the **process matrix formalism**.
The key insight: a process is represented as a multipartite state (the process matrix W)
over temporal "cuts." Testing whether W is **separable across temporal cuts** maps to
testing whether the memory is classical (separable) or quantum (entangled). A process
has **classical memory** iff its process matrix can be decomposed as
W = Σ_i p_i W_i^A ⊗ W_i^B (separable in time). **Quantum memory** = W is entangled
across temporal cuts — no such decomposition exists. The paper provides explicit
entanglement witnesses tailored to process matrices and demonstrates on a simple
two-qubit system-environment model.

## Key equations [paper]

### Process matrix representation — Eq. (1)
```
W = Σ_{ij} W_{ij} σ_i ⊗ σ_j
```
where σ_i are Pauli operators. W must satisfy: (i) W ≥ 0 (positive semidefinite),
(ii) causal constraints (trace-preserving condition on certain subsystems).

### Classical memory condition — Eq. (4)
```
W = Σ_k p_k W_k^{A→A'} ⊗ W_k^{B→B'}
```
Separable across the temporal cut A→A' (earlier) and B→B' (later). The index k
runs over "memory states" that are classically correlated with the process.

### Quantum memory witness — Eq. (8)
A witness operator S such that:
```
Tr(S W) < 0 ⇒ quantum memory
```
while for all classical-memory processes, Tr(S W) ≥ 0. Constructed from entanglement
witnesses on the Choi-Jamiolkowski representation of the process.

### Witness construction recipe — §4
1. Take the process matrix W
2. Apply a temporal "swap" operation that exchanges the input/output spaces of
   the two time steps
3. Compute the expectation value of a suitable witness operator
4. Negative expectation = temporally entangled = quantum memory

### Two-qubit model — §5
Environment E is a single qubit (same dimension as system S). Hamiltonian:
```
H = ω (σ_z^S + σ_z^E) + g (σ_x^S σ_x^E + σ_y^S σ_y^E)
```
For weak coupling g, the process has classical memory only (separable W).
For strong coupling, W becomes entangled → quantum memory.

### Quantifier — Eq. (13)
The **quantum memory robustness**:
```
R_Q(W) = min{ t ≥ 0 | (W + t σ)/(1 + t) is separable }
```
where σ is a reference separable process. Larger R_Q = more robustly quantum memory.

## Relevance to project [ours]
**Claim 3 dimension ② (collectiveness) — OPERATIONAL TEST FOR QUANTUM VS CLASSICAL
COLLECTIVE MEMORY.** This paper directly provides the adjudication protocol for whether
the shared-mode JC model's collective decay signature is genuinely quantum or could be
simulated classically:

1. **Mapping to our setting:**
   - Two time steps: t₁ (initialization → first parity extraction) and t₂ (first → second
     parity extraction)
   - System S = two data qubits; environment E = shared bosonic mode
   - Process matrix W encodes the full system-environment dynamics across both steps

2. **Classical collectiveness scenario:** If the shared-mode interaction produces a
   process matrix that is **separable across the temporal cut**, then the collective
   decay is **classical memory** — a classical correlation between the two qubits
   mediated by the bath, reproducible by a classical hidden-variable model
   (e.g., independent AD with correlated classical noise).

3. **Quantum collectiveness scenario:** If W is **temporally entangled**, the collective
   decay is **genuinely quantum** — the shared mode induces system-bath entanglement
   that cannot be simulated classically. This is what the JC model with strong coupling
   predicts.

4. **Witness construction for our system:** The relevant witness S must be tailored
   to the JC Hamiltonian's symmetry (excitation-preserving, U(1) symmetry). The
   witness in §5 of the paper for a two-qubit environment is directly adaptable:
   replace the qubit environment with the truncated bosonic mode (truncation to
   d ≤ 4 Fock states).

5. **Prediction:** For the shared-mode JC model at r=1 (symmetric coupling), the
   process matrix should show **temporal entanglement** because the Jaynes-Cummings
   interaction creates qubit-mode entanglement at intermediate times. For independent
   AD per qubit (null model), W should be separable → testable via the witness.

6. **Control 2 grounding:** The separability criterion gives a **necessary condition**
   for classical simulation: if W is temporally entangled, no independent-bath model
   can reproduce the multi-time statistics, regardless of parameter tuning.

## Limitations
- Demonstrated only for a qubit environment (dimension 2); extension to truncated
  bosonic mode (dimension d > 2) requires constructing a higher-dimensional witness
- The witness construction is not unique — different witnesses detect different classes
  of temporal entanglement
- Requires full process tomography (exponential in system size) — practical only for
  small systems (≤4 qubits) or with compressed sensing
- The classical-vs-quantum distinction is defined relative to the temporal cut choice;
  a different cut could change the classification
- No experimental demonstration of the witness on real hardware (purely theoretical)

## Tags
- `[paper]` process matrix W = multipartite state over temporal cuts
- `[paper]` classical memory ⇔ W separable across temporal cuts
- `[paper]` quantum memory ⇔ W temporally entangled
- `[paper]` entanglement witness S: Tr(SW) < 0 ⇒ quantum memory
- `[paper]` two-qubit s-e model ≈ our shared-mode system
- `[ours]` operational test for quantum vs classical collectiveness
- `[ours]` directly grounds Control 2 (null model irreproducibility)
- `[ours]` temporal entanglement of JC process matrix = necessary condition for
  genuine quantum collectiveness
